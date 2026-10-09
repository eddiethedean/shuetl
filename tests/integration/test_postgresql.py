"""Executable PostgreSQL pilot qualification for the Phase 0.4 provider."""

from __future__ import annotations

import json
import os
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
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

from shuetl import (
    HostIdentityAdapter,
    PostgreSQLProviderBundle,
    ShuETL,
    ShuETLSettings,
)
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
