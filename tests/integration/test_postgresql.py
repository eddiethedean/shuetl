"""Executable PostgreSQL pilot qualification for the Phase 0.4 provider."""

from __future__ import annotations

import json
import os
import select
import socket
import threading
import time
import uuid
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import replace
from typing import cast

import pytest
from etlantic.control_plane import (
    ControlPlaneContext,
    EnvironmentRef,
    FiringRecord,
    MemoryAuthorizer,
    Principal,
    ScheduleSpec,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic_sqlmodel.migrations import upgrade
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import text
from tests.unit.test_runtime_contract import _preview_settings
from tests.unit.test_runtime_failures import bindings as runtime_bindings

from shuetl import (
    HostIdentityAdapter,
    PostgreSQLProviderBundle,
    ShuETL,
    ShuETLSettings,
)
from shuetl import runtime as runtime_module
from shuetl.backend import create_backend_runtime
from shuetl.diagnostics import DoctorReport
from shuetl.postgresql import (
    POSTGRESQL_HEAD,
    POSTGRESQL_REQUIRED_TABLES,
    create_postgresql_engine,
    inspect_postgresql,
)


def _settings() -> ShuETLSettings:
    url = os.environ.get("SHUETL_DATABASE_URL")
    if not url:
        pytest.skip("SHUETL_DATABASE_URL is not configured")
    return ShuETLSettings(
        profile="postgresql-pilot",
        role="gateway",
        provider="postgresql",
        identity="host",
        database_url=url,
        postgresql_sslmode=os.environ.get("SHUETL_POSTGRESQL_SSLMODE", "disable"),
    )


def _context(principal: Principal | None = None) -> ControlPlaneContext:
    return ControlPlaneContext(
        principal=principal or Principal("phase-0-4", issuer="https://test.example"),
        tenant=TenantRef("tenant-0-4"),
        workspace=WorkspaceRef("tenant-0-4", "workspace-0-4"),
        environment=EnvironmentRef("production"),
        security_domain=SecurityDomain("default"),
    )


def _identity_adapter() -> HostIdentityAdapter:
    def principal_dependency(_request: Request) -> Principal:
        return Principal("phase-0-4", issuer="https://test.example")

    def context_factory(principal: Principal, _request: Request) -> ControlPlaneContext:
        return _context(principal)

    return HostIdentityAdapter.create(
        principal_dependency=principal_dependency,
        context_factory=context_factory,
    )


class _PostgreSQLFaultProxy:
    """A disposable TCP gate that can sever a runtime's PostgreSQL connections."""

    def __init__(self, host: str, port: int) -> None:
        self.upstream = (host, port)
        self._available = threading.Event()
        self._available.set()
        self._stopped = threading.Event()
        self._lock = threading.Lock()
        self._connections: set[tuple[socket.socket, socket.socket]] = set()
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen()
        self._listener.settimeout(0.1)
        self.port = self._listener.getsockname()[1]
        self._accept_thread = threading.Thread(target=self._accept, daemon=True)
        self._accept_thread.start()

    def __enter__(self) -> _PostgreSQLFaultProxy:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def interrupt(self) -> None:
        self._available.clear()
        with self._lock:
            connections = tuple(self._connections)
        for pair in connections:
            self._close_pair(pair)

    def recover(self) -> None:
        self._available.set()

    def close(self) -> None:
        self._stopped.set()
        self.interrupt()
        self._listener.close()
        self._accept_thread.join(timeout=2)

    def _accept(self) -> None:
        while not self._stopped.is_set():
            try:
                client, _address = self._listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            if not self._available.is_set():
                client.close()
                continue
            try:
                upstream = socket.create_connection(self.upstream, timeout=2)
            except OSError:
                client.close()
                continue
            pair = (client, upstream)
            with self._lock:
                self._connections.add(pair)
            threading.Thread(target=self._relay, args=(pair,), daemon=True).start()

    def _relay(self, pair: tuple[socket.socket, socket.socket]) -> None:
        client, upstream = pair
        try:
            while not self._stopped.is_set():
                readable, _writable, _errors = select.select(pair, (), (), 0.25)
                for source in readable:
                    data = source.recv(65536)
                    if not data:
                        return
                    destination = upstream if source is client else client
                    destination.sendall(data)
        except (OSError, ValueError):
            pass
        finally:
            with self._lock:
                self._connections.discard(pair)
            self._close_pair(pair)

    @staticmethod
    def _close_pair(pair: tuple[socket.socket, socket.socket]) -> None:
        for connection in pair:
            with suppress(OSError):
                connection.shutdown(socket.SHUT_RDWR)
            connection.close()


@pytest.fixture(scope="module")
def settings() -> ShuETLSettings:
    configured = _settings()
    engine = create_postgresql_engine(configured)
    try:
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
        assert upgrade(engine) == POSTGRESQL_HEAD
    finally:
        engine.dispose()
    return configured


@pytest.fixture
def bundle(settings: ShuETLSettings) -> Generator[PostgreSQLProviderBundle, None, None]:
    result = PostgreSQLProviderBundle.create(
        settings,
        authorizer=MemoryAuthorizer(),
        identity_adapter=_identity_adapter(),
    )
    try:
        yield result
    finally:
        result.close()


def test_schema_head_graph_and_doctor(settings: ShuETLSettings) -> None:
    status = inspect_postgresql(settings)
    assert status.state == "head"
    assert status.version == POSTGRESQL_HEAD
    assert status.server_version == "18.6"
    engine = create_postgresql_engine(settings)
    try:
        from sqlalchemy import inspect

        assert set(inspect(engine).get_table_names()) >= POSTGRESQL_REQUIRED_TABLES
    finally:
        engine.dispose()

    bundle = PostgreSQLProviderBundle.create(
        settings,
        authorizer=MemoryAuthorizer(),
        identity_adapter=_identity_adapter(),
    )
    try:
        assert bundle.provider == "postgresql"
        assert bundle.development_only is False
        assert ShuETL(api=bundle.api).create_app(prefix="/etl").openapi()["paths"]
        report = DoctorReport.inspect(settings=settings, bundle=bundle)
        assert report.status == "pass"
        assert report.database_driver == "psycopg"
        assert "provider.postgresql" in report.available_capabilities
        assert report.versions["postgresql-server"] == "18.6"
    finally:
        bundle.close()


def test_restart_idempotency_events_schedules_and_firings(
    settings: ShuETLSettings, bundle: PostgreSQLProviderBundle
) -> None:
    ctx = _context()
    first = bundle.submissions.accept(
        ctx, idempotency_key="submission-1", payload={"value": 1}
    )
    second = bundle.submissions.accept(
        ctx, idempotency_key="submission-1", payload={"value": 1}
    )
    assert first.receipt.submission_id == second.receipt.submission_id
    assert first.created is True
    assert second.created is False

    event = bundle.events.append(ctx, kind="phase-0-4", payload={"value": 1})
    assert (
        bundle.events.list_after_cursor(ctx, None, limit=10)[0].event_id
        == event.event_id
    )

    bundle.definitions.put(ctx, "definition-1", {"name": "definition-1"})
    schedule = bundle.schedules.create(
        ctx,
        definition_id="definition-1",
        profile_name="production",
        spec=ScheduleSpec(kind="interval", interval_seconds=60),
        schedule_id="schedule-1",
    )
    first_firing, created = bundle.schedules.claim_firing(
        ctx,
        schedule_id=schedule.schedule_id,
        revision_id=schedule.revision_id,
        nominal_fire_time="2026-09-13T00:00:00Z",
        owner_id="owner-1",
        fencing_token=1,
        plan_fingerprint="fingerprint-1",
        require_leader_lease=False,
    )
    duplicate_firing, duplicate = bundle.schedules.claim_firing(
        ctx,
        schedule_id=schedule.schedule_id,
        revision_id=schedule.revision_id,
        nominal_fire_time="2026-09-13T00:00:00Z",
        owner_id="owner-1",
        fencing_token=1,
        plan_fingerprint="fingerprint-1",
        require_leader_lease=False,
    )
    assert created is True
    assert duplicate is False
    assert duplicate_firing.firing_id == first_firing.firing_id

    reopened = PostgreSQLProviderBundle.create(
        settings,
        authorizer=MemoryAuthorizer(),
        identity_adapter=_identity_adapter(),
    )
    try:
        assert reopened.schedules.get(ctx, "schedule-1").schedule_id == "schedule-1"
        assert reopened.submissions.lookup_idempotency(ctx, "submission-1") is not None
        assert reopened.schedules.list_firings(ctx, "schedule-1")[0].firing_id == (
            first_firing.firing_id
        )
    finally:
        reopened.close()


def test_concurrent_event_appends_have_unique_sequences(
    bundle: PostgreSQLProviderBundle,
) -> None:
    ctx = _context()

    def append(index: int) -> str:
        return bundle.events.append(
            ctx, kind="concurrent", payload={"index": index}
        ).event_id

    with ThreadPoolExecutor(max_workers=10) as executor:
        event_ids = list(executor.map(append, range(20)))
    assert len(set(event_ids)) == 20
    events = bundle.events.list_after_cursor(ctx, None, limit=100)
    sequences = [event.sequence for event in events if event.event_id in event_ids]
    assert len(sequences) == 20
    assert len(set(sequences)) == 20


def test_triggering_identity_is_persisted_without_host_credentials(
    settings: ShuETLSettings,
    bundle: PostgreSQLProviderBundle,
) -> None:
    ctx = _context()
    cast(MemoryAuthorizer, bundle.authorizer).grant(ctx, "run.submit")
    bundle.definitions.put(ctx, "identity-definition", {"fingerprint": "safe-fp"})
    app = ShuETL(api=bundle.api).create_app(prefix="/etl")
    bearer = "bearer-credential-sentinel"
    cookie = "session-cookie-sentinel"

    with TestClient(app) as client:
        response = client.post(
            "/etl/v1/definitions/identity-definition/runs",
            headers={
                "Authorization": f"Bearer {bearer}",
                "Cookie": f"session={cookie}",
                "Idempotency-Key": "phase-0-5-trigger-identity",
            },
            json={"payload": {}},
        )
    assert response.status_code == 202
    submission_id = response.json()["submission_id"]
    query = text(
        "SELECT payload_json FROM cp_durable_submission_entity "
        "WHERE store_id = 'default' AND submission_id = :submission_id"
    )
    with bundle._engine.connect() as connection:
        row = connection.execute(query, {"submission_id": submission_id}).scalar_one()
    persisted = json.loads(row)
    assert persisted["principal_subject"] == "phase-0-4"
    assert persisted["principal_issuer"] == "https://test.example"
    assert persisted["principal_kind"] == "human"
    assert bearer not in row
    assert cookie not in row

    bundle.close()
    reopened = PostgreSQLProviderBundle.create(
        settings,
        authorizer=MemoryAuthorizer(),
        identity_adapter=_identity_adapter(),
    )
    try:
        with reopened._engine.connect() as connection:
            replayed = connection.execute(
                query, {"submission_id": submission_id}
            ).scalar_one()
        assert json.loads(replayed) == persisted
        assert bearer not in replayed
        assert cookie not in replayed
    finally:
        reopened.close()


def test_workspace_firing_and_durable_identity_survive_restart(
    settings: ShuETLSettings, bundle: PostgreSQLProviderBundle
) -> None:
    base = _context()
    contexts = tuple(
        replace(base, workspace=WorkspaceRef(base.tenant.tenant_id, workspace))
        for workspace in ("firing-workspace-a", "firing-workspace-b")
    )

    def claim(
        provider: PostgreSQLProviderBundle, ctx: ControlPlaneContext
    ) -> tuple[FiringRecord, bool]:
        lease = provider.schedules.acquire_leader_lease(
            ctx, owner_id="scope-scheduler", ttl_seconds=60
        )
        return provider.schedules.claim_firing(
            ctx,
            schedule_id="workspace-shared-schedule",
            revision_id=provider.schedules.get(
                ctx, "workspace-shared-schedule"
            ).revision_id,
            nominal_fire_time="2026-09-13T00:00:00Z",
            owner_id="scope-scheduler",
            fencing_token=lease.fencing_token,
            plan_fingerprint="workspace-shared-plan",
            durable=provider.durable_work,
        )

    firings = []
    for ctx in contexts:
        bundle.schedules.create(
            ctx,
            definition_id="workspace-shared-definition",
            profile_name="production",
            spec=ScheduleSpec(kind="interval", interval_seconds=60),
            schedule_id="workspace-shared-schedule",
        )
        firing, created = claim(bundle, ctx)
        assert created
        assert firing.workspace_id == ctx.workspace.workspace_id
        assert len(bundle.durable_work.pending_outbox(ctx)) == 1
        firings.append(firing)
    assert firings[0].firing_id != firings[1].firing_id
    assert firings[0].submission_id != firings[1].submission_id
    bundle.close()

    reopened = PostgreSQLProviderBundle.create(
        settings,
        authorizer=MemoryAuthorizer(),
        context_factory=lambda principal, request: _context(),
        principal_dependency=lambda request: Principal("phase-0-4"),
    )
    try:
        for ctx, original in zip(contexts, firings, strict=True):
            replay, created = claim(reopened, ctx)
            assert not created
            assert replay == original
            assert reopened.schedules.list_firings(
                ctx, "workspace-shared-schedule"
            ) == (original,)
            assert len(reopened.durable_work.pending_outbox(ctx)) == 1
    finally:
        reopened.close()


def test_postgresql_scheduler_signal_drains_active_claim(
    settings: ShuETLSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep PostgreSQL-backed resources open until an active scheduler claim drains."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        probe_port = listener.getsockname()[1]
    runtime = create_backend_runtime(
        _preview_settings(
            role="scheduler",
            store_id=f"pg-drain-{uuid.uuid4().hex[:10]}",
            database_url=settings.database_url,
            probe_port=probe_port,
            shutdown_grace_seconds=0.1,
            dispatch_interval_seconds=0.05,
        ),
        runtime_bindings(),
    )
    states = []
    handlers = []
    real_probe = runtime_module.serve_probes

    def capture_probe(state, port):
        states.append(state)
        return real_probe(state, port)

    monkeypatch.setattr(runtime_module, "serve_probes", capture_probe)
    monkeypatch.setattr(
        runtime_module,
        "_install_signals",
        lambda callback: handlers.append(callback) or {},
    )
    monkeypatch.setattr(runtime_module, "_restore_signals", lambda previous: None)

    entered = threading.Event()
    release = threading.Event()
    store = runtime.backend.schedule_store
    original = store.acquire_leader_lease

    def blocked_claim(*args, **kwargs):
        entered.set()
        assert release.wait(8), "active PostgreSQL claim was not released"
        return original(*args, **kwargs)

    store.acquire_leader_lease = blocked_claim
    outcomes = []

    def serve_and_cleanup():
        result = runtime_module._serve_worker(runtime)
        return result if runtime_module._close_when_drained(runtime) else 1

    def invoke():
        try:
            outcomes.append(serve_and_cleanup())
        except BaseException as exc:
            outcomes.append(exc)

    thread = threading.Thread(target=invoke, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and (not handlers or not states):
            time.sleep(0.01)
        assert handlers and states, "PostgreSQL scheduler supervisor did not start"
        assert entered.wait(8), "scheduler did not begin a PostgreSQL claim"
        assert runtime.role_handle.status().in_flight > 0

        handlers[0](15, None)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            status, payload = states[0].payload(False)
            if status == 503 and payload["reason_code"] == "grace_expired":
                break
            time.sleep(0.01)
        assert states[0].payload(False)[0] == 503
        assert runtime.role_handle.status().in_flight > 0
        assert not runtime.closed
        assert not outcomes

        release.set()
        thread.join(timeout=8)
        assert not thread.is_alive(), "scheduler did not finish after claim release"
        assert outcomes == [0]
        assert runtime.closed
        assert runtime.role_handle.status().in_flight == 0
    finally:
        release.set()
        if handlers and thread.is_alive():
            handlers[0](15, None)
        thread.join(timeout=8)
        if not runtime.closed:
            runtime.close()


def test_postgresql_scheduler_provider_outage_recovers(
    settings: ShuETLSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = create_postgresql_engine(settings)
    try:
        database_url = engine.url
    finally:
        engine.dispose()
    upstream_host = database_url.host or "127.0.0.1"
    upstream_port = database_url.port or 5432

    with _PostgreSQLFaultProxy(upstream_host, upstream_port) as proxy:
        with socket.socket() as probe_listener:
            probe_listener.bind(("127.0.0.1", 0))
            probe_port = probe_listener.getsockname()[1]
        runtime = create_backend_runtime(
            _preview_settings(
                role="scheduler",
                store_id=f"pg-outage-{uuid.uuid4().hex[:10]}",
                database_url=database_url.set(
                    host="127.0.0.1", port=proxy.port
                ).render_as_string(hide_password=False),
                probe_port=probe_port,
                shutdown_grace_seconds=0.5,
                dispatch_interval_seconds=0.05,
            ),
            runtime_bindings(),
        )
        states = []
        handlers = []
        real_probe = runtime_module.serve_probes

        def capture_probe(state, port):
            states.append(state)
            return real_probe(state, port)

        monkeypatch.setattr(runtime_module, "serve_probes", capture_probe)
        monkeypatch.setattr(
            runtime_module,
            "_install_signals",
            lambda callback: handlers.append(callback) or {},
        )
        monkeypatch.setattr(runtime_module, "_restore_signals", lambda previous: None)
        outcomes = []

        def serve_and_cleanup():
            result = runtime_module._serve_worker(runtime)
            return result if runtime_module._close_when_drained(runtime) else 1

        def invoke():
            try:
                outcomes.append(serve_and_cleanup())
            except BaseException as exc:
                outcomes.append(exc)

        thread = threading.Thread(target=invoke, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline and (not handlers or not states):
                time.sleep(0.01)
            assert handlers and states, "PostgreSQL scheduler supervisor did not start"
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline and states[0].payload(False)[0] != 200:
                time.sleep(0.01)
            assert states[0].payload(False)[0] == 200

            proxy.interrupt()
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                status, payload = states[0].payload(False)
                if status == 503 and payload["reason_code"] == "provider_unavailable":
                    break
                time.sleep(0.01)
            assert states[0].payload(False)[0] == 503
            assert states[0].payload(False)[1]["reason_code"] == "provider_unavailable"
            assert states[0].payload(True)[0] == 200
            assert not runtime.closed

            proxy.recover()
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline and states[0].payload(False)[0] != 200:
                time.sleep(0.01)
            assert states[0].payload(False)[0] == 200
            handlers[0](15, None)
            thread.join(timeout=8)
            assert not thread.is_alive(), "scheduler did not stop after recovery"
            assert outcomes == [0]
            assert runtime.closed
        finally:
            if thread.is_alive() and handlers:
                handlers[0](15, None)
            thread.join(timeout=8)
            assert not thread.is_alive(), "scheduler did not stop during cleanup"
            if not runtime.closed:
                runtime.close()
