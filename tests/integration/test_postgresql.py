"""Executable PostgreSQL pilot qualification for the Phase 0.4 provider."""

from __future__ import annotations

import os
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor

import pytest
from etlantic.control_plane import (
    ControlPlaneContext,
    EnvironmentRef,
    MemoryAuthorizer,
    Principal,
    ScheduleSpec,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic_sqlmodel.migrations import upgrade
from sqlalchemy import text

from shuetl import PostgreSQLProviderBundle, ShuETL, ShuETLSettings
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


def _context() -> ControlPlaneContext:
    return ControlPlaneContext(
        principal=Principal("phase-0-4"),
        tenant=TenantRef("tenant-0-4"),
        workspace=WorkspaceRef("tenant-0-4", "workspace-0-4"),
        environment=EnvironmentRef("production"),
        security_domain=SecurityDomain("default"),
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
        context_factory=lambda principal, request: _context(),
        principal_dependency=lambda request: Principal("phase-0-4"),
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
        context_factory=lambda principal, request: _context(),
        principal_dependency=lambda request: Principal("phase-0-4"),
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
        revision_id="revision-1",
        nominal_fire_time="2026-09-13T00:00:00Z",
        owner_id="owner-1",
        fencing_token=1,
        plan_fingerprint="fingerprint-1",
        require_leader_lease=False,
    )
    duplicate_firing, duplicate = bundle.schedules.claim_firing(
        ctx,
        schedule_id=schedule.schedule_id,
        revision_id="revision-1",
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
        context_factory=lambda principal, request: _context(),
        principal_dependency=lambda request: Principal("phase-0-4"),
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
