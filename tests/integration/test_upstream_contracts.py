"""Consumer acceptance of the published ETLantic 0.57 public contracts."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from threading import Event
from typing import Any

import pytest
from etlantic import Data, Extract, Load, Pipeline
from etlantic.authoring import definition_from_pipeline
from etlantic.authoring.serialize import pipeline_to_dict
from etlantic.control_plane import (
    ControlPlaneContext,
    ControlPlaneError,
    EnvironmentRef,
    MemoryAuthorizer,
    Principal,
    ScheduleSpec,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic_fastapi import adapt_managed_backend, create_app
from etlantic_sqlmodel import (
    SQLModelBackendConfig,
    create_managed_backend,
    create_sqlite_engine,
    inspect_schema,
    schema_requirements,
)
from etlantic_sqlmodel.migrations import upgrade
from fastapi.testclient import TestClient
from sqlalchemy import event


class ContractRow(Data):
    id: int


class ContractPipeline(Pipeline):
    source: Extract[ContractRow] = Extract(asset="source")
    result: Load[ContractRow] = Load(input=source, asset="result")


@pytest.fixture
def graph(tmp_path):
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'contract.db'}")
    upgrade(engine)
    ctx = ControlPlaneContext(
        principal=Principal("contract-check", issuer="shuetl-test"),
        tenant=TenantRef("tenant"),
        workspace=WorkspaceRef("tenant", "workspace"),
        environment=EnvironmentRef("test"),
        security_domain=SecurityDomain("test"),
    )
    authorizer = MemoryAuthorizer()
    for action in (
        "definition.write",
        "run.submit",
        "schedule.write",
        "schedule.read",
    ):
        authorizer.grant(ctx, action)
    backend = create_managed_backend(
        SQLModelBackendConfig(store_id="contract"), authorizer=authorizer, engine=engine
    )
    backend.managed_service.register_definition(
        ctx, "pipeline", pipeline_to_dict(definition_from_pipeline(ContractPipeline))
    )
    try:
        yield backend, ctx
    finally:
        backend.close()
        engine.dispose()


def test_schedule_http_headless_parity_and_revision_conflicts(graph):
    backend, ctx = graph
    adapter = adapt_managed_backend(
        backend,
        context_factory=lambda _principal, _request: ctx,
        principal_dependency=lambda: ctx.principal,
    )
    assert adapter.api.get_schedule_service() is backend.schedule_service
    app = create_app(adapter.api)
    commands = backend.schedule_service
    with TestClient(app) as client:
        response = client.post(
            "/v1/definitions/pipeline/schedules",
            json={"spec": {"kind": "interval", "interval_seconds": 60}},
        )
        assert response.status_code == 201, response.text
        created = response.json()
        identifier = created["schedule_id"]
        record = commands.get(ctx, identifier)
        assert record.to_dict() == created
        assert client.get(f"/v1/schedules/{identifier}").json() == record.to_dict()
        assert client.get("/v1/definitions/pipeline/schedules").json() == {
            "schedules": [
                item.to_dict() for item in commands.list_definition(ctx, "pipeline")
            ]
        }
        changed = commands.amend(
            ctx,
            identifier,
            expected_revision_id=record.revision_id,
            spec=ScheduleSpec(kind="interval", interval_seconds=120),
        )
        assert changed.revision_id != record.revision_id
        response = client.post(
            f"/v1/schedules/{identifier}/amend",
            json={
                "expected_revision_id": record.revision_id,
                "spec": {"kind": "interval", "interval_seconds": 180},
            },
        )
        assert response.status_code == 409
        with pytest.raises(ControlPlaneError) as rejected:
            commands.amend(
                ctx,
                identifier,
                expected_revision_id=record.revision_id,
                spec=ScheduleSpec(kind="interval", interval_seconds=180),
            )
        assert rejected.value.status == 409
        paused = commands.pause(ctx, identifier)
        assert client.get(f"/v1/schedules/{identifier}").json() == paused.to_dict()
        resumed = client.post(f"/v1/schedules/{identifier}/resume")
        assert resumed.status_code == 200
        assert resumed.json() == commands.get(ctx, identifier).to_dict()
        assert (
            client.get(f"/v1/schedules/{identifier}/preview").json()["schedule_id"]
            == commands.preview(ctx, identifier)["schedule_id"]
        )
        nominal = datetime(2026, 10, 9, 12, tzinfo=UTC)
        first, _created = commands.trigger(ctx, identifier, nominal_fire_time=nominal)
        duplicate = client.post(
            f"/v1/schedules/{identifier}/trigger",
            json={"nominal_fire_time": nominal.isoformat()},
        )
        assert duplicate.status_code == 200, duplicate.text
        assert duplicate.json()["firing_id"] == first.firing_id
        assert duplicate.json()["submission_id"] == first.submission_id
        assert len(commands.list_firings(ctx, identifier)) == 1


def test_schedule_denial_scope_and_workload_binding(graph):
    backend, ctx = graph
    commands = backend.schedule_service
    denied = replace(ctx, workspace=WorkspaceRef("tenant", "denied"))
    with pytest.raises(ControlPlaneError):
        commands.create(
            denied, "pipeline", spec=ScheduleSpec(kind="interval", interval_seconds=60)
        )
    with pytest.raises(ControlPlaneError):
        commands.create(
            ctx,
            "pipeline",
            spec=ScheduleSpec(kind="interval", interval_seconds=60),
            workload_identity=Principal(
                "unapproved-worker", issuer="test", kind="service"
            ),
        )
    assert commands.list_definition(ctx, "pipeline") == ()


def test_interrupted_schedule_link_recovers_one_submission(graph, monkeypatch):
    backend, ctx = graph
    commands = backend.schedule_service
    schedule = commands.create(
        ctx, "pipeline", spec=ScheduleSpec(kind="interval", interval_seconds=60)
    )
    nominal = datetime(2026, 10, 9, 12, tzinfo=UTC)
    original = backend.schedule_store.link_firing_submission

    def unavailable(*args, **kwargs):
        raise OSError("interrupted before firing link")

    monkeypatch.setattr(backend.schedule_store, "link_firing_submission", unavailable)
    with pytest.raises(OSError):
        commands.trigger(ctx, schedule.schedule_id, nominal_fire_time=nominal)
    pending = backend.durable_work.pending_outbox(ctx)
    assert len(pending) == 1
    firing = commands.list_firings(ctx, schedule.schedule_id)[0]
    assert firing.submission_id is None
    monkeypatch.setattr(backend.schedule_store, "link_firing_submission", original)
    recovered, created = commands.trigger(
        ctx, schedule.schedule_id, nominal_fire_time=nominal
    )
    assert not created
    assert recovered.firing_id == firing.firing_id
    assert recovered.submission_id == pending[0].submission_id
    assert len(backend.durable_work.pending_outbox(ctx)) == 1


def _role(backend: Any, kind: str):
    if kind == "scheduler":
        return (
            backend.create_scheduler(owner_id="scheduler"),
            backend.schedule_store,
            "acquire_leader_lease",
        )
    if kind == "runs":
        return (
            backend.create_execution_host(owner_id="worker"),
            backend.durable_work,
            "pending_outbox",
        )
    return (
        backend.create_action_execution_host(worker_id="actions"),
        backend.durable_work,
        "claim_action_job",
    )


@pytest.mark.parametrize("kind", ["scheduler", "runs", "actions"])
def test_active_role_drain_does_not_close_engine_or_dispatch_later(
    graph, monkeypatch, kind
):
    backend, ctx = graph
    role, store, operation = _role(backend, kind)
    entered, release = Event(), Event()
    original = getattr(store, operation)
    calls = []

    def blocked(*args, **kwargs):
        calls.append(True)
        entered.set()
        assert release.wait(10), "fixture barrier timed out"
        return original(*args, **kwargs)

    monkeypatch.setattr(store, operation, blocked)
    disposed = []
    event.listen(
        backend.engine, "engine_disposed", lambda _engine: disposed.append(True)
    )
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(role.tick, ctx)
        try:
            assert entered.wait(10), "role did not reach provider boundary"
            role.request_drain()
            role.request_drain()
            status = role.status()
            assert status.activity == "active" and status.in_flight > 0
            assert not status.ready
            with pytest.raises(RuntimeError, match="still active"):
                backend.close()
            assert not disposed
        finally:
            release.set()
        assert future.result(timeout=10) == 0
    count = len(calls)
    assert role.tick(ctx) == 0
    assert len(calls) == count
    backend.close()
    backend.close()
    assert not disposed  # borrowed engine remains caller-owned
    with backend.engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT 1").scalar_one() == 1


@pytest.mark.parametrize("kind", ["scheduler", "runs", "actions"])
def test_role_provider_outage_recovery_and_invalid_context(graph, monkeypatch, kind):
    backend, ctx = graph
    role, store, operation = _role(backend, kind)
    invalid = replace(ctx, principal=Principal(" "))
    with pytest.raises(ControlPlaneError):
        role.tick(invalid)
    assert role.status().prerequisites == "unknown"
    original = getattr(store, operation)

    def unavailable(*args, **kwargs):
        raise OSError("credential-sentinel")

    monkeypatch.setattr(store, operation, unavailable)
    if kind == "scheduler":
        assert role.tick(ctx) == 0
    else:
        with pytest.raises(OSError):
            role.tick(ctx)
    assert role.status().prerequisites == "unusable"
    assert "credential-sentinel" not in str(role.status().to_dict())
    monkeypatch.setattr(store, operation, original)
    assert role.tick(ctx) == 0
    assert role.status().prerequisites == "usable"


def test_scheduler_standby_is_usable(graph):
    backend, ctx = graph
    leader = backend.create_scheduler(owner_id="leader")
    standby = backend.create_scheduler(owner_id="standby")
    assert leader.tick(ctx) == 0
    assert standby.tick(ctx) == 0
    assert standby.status().activity == "standby"
    assert standby.status().ready


def test_owned_engine_close_once_and_partial_failure_cleanup(tmp_path, monkeypatch):
    import etlantic_sqlmodel.managed as provider
    from sqlalchemy import create_engine

    url = f"sqlite:///{tmp_path / 'owned.db'}"
    engine = create_engine(url)
    upgrade(engine)
    engine.dispose()
    created, disposed = [], []

    def create(*args, **kwargs):
        value = create_engine(*args, **kwargs)
        created.append(value)
        event.listen(value, "engine_disposed", lambda _engine: disposed.append(value))
        return value

    monkeypatch.setattr(provider, "create_engine", create, raising=False)
    # The provider imports SQLAlchemy's public constructor at call time.
    monkeypatch.setattr("sqlalchemy.create_engine", create)
    backend = create_managed_backend(
        SQLModelBackendConfig(database_url=url), authorizer=MemoryAuthorizer()
    )
    assert backend.owns_engine
    backend.close()
    backend.close()
    assert disposed == [created[0]]
    with pytest.raises(RuntimeError):
        create_managed_backend(
            SQLModelBackendConfig(database_url=f"sqlite:///{tmp_path / 'fresh.db'}"),
            authorizer=MemoryAuthorizer(),
        )
    assert disposed == created


def test_public_schema_inspection_is_read_only_and_detects_corruption(graph):
    backend, _ctx = graph
    writes, commits = [], []

    def capture(_conn, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().split(None, 1)[0].upper() in {
            "CREATE",
            "ALTER",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
        }:
            writes.append(statement)

    event.listen(backend.engine, "before_cursor_execute", capture)
    event.listen(backend.engine, "commit", lambda _conn: commits.append(True))
    assert inspect_schema(backend.engine).compatible
    assert not writes and not commits
    event.remove(backend.engine, "before_cursor_execute", capture)
    required = schema_requirements().objects[0].name
    with backend.engine.begin() as connection:
        connection.exec_driver_sql(f'DROP TABLE "{required}"')
    inspected = inspect_schema(backend.engine)
    assert inspected.compatibility.value == "partial_or_corrupt"
    assert required in inspected.missing_objects
