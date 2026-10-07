"""Executable PostgreSQL pilot qualification for the Phase 0.4 provider."""

from __future__ import annotations

import json
import os
import sys
import types
import uuid
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

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
    HostRuntimeBindings,
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
from shuetl.runtime import build_managed_runtime


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


def _public_schema_snapshot(connection: Any) -> tuple[tuple[tuple[Any, ...], ...], ...]:
    """Capture public schema objects without relying on a migration helper."""

    queries = (
        """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name, table_type
        """,
        """
        SELECT table_name, column_name, ordinal_position, data_type, udt_name,
               is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
        """,
        """
        SELECT relation.relname, constraint_row.conname, constraint_row.contype,
               pg_get_constraintdef(constraint_row.oid)
        FROM pg_constraint AS constraint_row
        JOIN pg_class AS relation ON relation.oid = constraint_row.conrelid
        JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        WHERE namespace.nspname = 'public'
        ORDER BY relation.relname, constraint_row.conname
        """,
        """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY indexname
        """,
        """
        SELECT sequence_name, data_type, numeric_precision, numeric_scale
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
        ORDER BY sequence_name
        """,
        """
        SELECT event_object_table, trigger_name, event_manipulation,
               action_timing, action_statement
        FROM information_schema.triggers
        WHERE trigger_schema = 'public'
        ORDER BY event_object_table, trigger_name, event_manipulation
        """,
    )
    return tuple(
        tuple(tuple(row) for row in connection.execute(text(query)).all())
        for query in queries
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
        if os.environ.get("SHUETL_RUNTIME_DATABASE_URL"):
            with engine.begin() as connection:
                connection.execute(
                    text("GRANT USAGE ON SCHEMA public TO shuetl_runtime")
                )
                # ETLantic 0.56.0 migrations.current_version unconditionally
                # executes CREATE TABLE IF NOT EXISTS, which requires CREATE
                # on the schema in PostgreSQL even when the table already exists.
                connection.execute(
                    text("GRANT CREATE ON SCHEMA public TO shuetl_runtime")
                )
                connection.execute(
                    text(
                        "GRANT SELECT, INSERT, UPDATE, DELETE "
                        "ON ALL TABLES IN SCHEMA public TO shuetl_runtime"
                    )
                )
                connection.execute(
                    text(
                        "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public "
                        "TO shuetl_runtime"
                    )
                )
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
    from etlantic import Data, Extract, Load, Pipeline, Profile
    from etlantic.authoring import definition_from_pipeline
    from etlantic.authoring.serialize import pipeline_to_dict

    class IdentityRow(Data):
        value: str

    class IdentityPipeline(Pipeline):
        source: Extract[IdentityRow] = Extract(asset="source")
        result: Load[IdentityRow] = Load(input=source, asset="result")

    ctx = _context()
    authorizer = cast(MemoryAuthorizer, bundle.authorizer)
    for action in (
        "definition.write",
        "definition.read",
        "run.submit",
        "run.read",
        "run.report",
        "run.artifacts",
        "run.artifact.content",
        "input.read",
    ):
        authorizer.grant(ctx, action)
    bundle.api.profile = Profile(name="phase06-identity-test", security_mode="test")
    bundle.api.enable_managed_execution()
    service = bundle.api.managed_service
    assert service is not None
    service.register_definition(
        ctx,
        "identity-definition",
        pipeline_to_dict(definition_from_pipeline(IdentityPipeline)),
    )
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
            json={},
        )
    assert response.status_code == 202, response.text
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
        provider: PostgreSQLProviderBundle,
        ctx: ControlPlaneContext,
        revision_id: str,
    ) -> tuple[FiringRecord, bool]:
        lease = provider.schedules.acquire_leader_lease(
            ctx, owner_id="scope-scheduler", ttl_seconds=60
        )
        return provider.schedules.claim_firing(
            ctx,
            schedule_id="workspace-shared-schedule",
            revision_id=revision_id,
            nominal_fire_time="2026-09-13T00:00:00Z",
            owner_id="scope-scheduler",
            fencing_token=lease.fencing_token,
            plan_fingerprint="workspace-shared-plan",
            durable=provider.durable_work,
        )

    firings = []
    for ctx in contexts:
        schedule = bundle.schedules.create(
            ctx,
            definition_id="workspace-shared-definition",
            profile_name="production",
            spec=ScheduleSpec(kind="interval", interval_seconds=60),
            schedule_id="workspace-shared-schedule",
        )
        firing, created = claim(bundle, ctx, schedule.revision_id)
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
            replay, created = claim(reopened, ctx, original.revision_id)
            assert not created
            assert replay == original
            assert reopened.schedules.list_firings(
                ctx, "workspace-shared-schedule"
            ) == (original,)
            assert len(reopened.durable_work.pending_outbox(ctx)) == 1
    finally:
        reopened.close()


def test_preview_runtime_executes_manual_and_scheduled_postgresql_work(
    settings: ShuETLSettings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise the standard gateway, scheduler, worker and SQL connector."""
    pytest.importorskip("etlantic_sql")

    from etlantic import Data, Extract, Load, Pipeline, Profile
    from etlantic.authoring import definition_from_pipeline
    from etlantic.authoring.serialize import pipeline_to_dict
    from etlantic.registry import BindingDescriptor, PlanningContext
    from etlantic.secrets import SecretRef
    from etlantic.secrets.provider import SecretResolutionContext
    from sqlalchemy.exc import ProgrammingError

    class TransferRow(Data):
        id: str
        payload: str

    class TransferPipeline(Pipeline):
        source: Extract[TransferRow] = Extract(asset="source")
        result: Load[TransferRow] = Load(input=source, asset="result")

    assert settings.database_url is not None
    runtime_database_url = os.environ.get("SHUETL_RUNTIME_DATABASE_URL")
    if not runtime_database_url:
        pytest.fail("SHUETL_RUNTIME_DATABASE_URL is required for the preview fixture")
    suffix = uuid.uuid4().hex[:12]
    source_table = f"phase06_source_{suffix}"
    target_table = f"phase06_target_{suffix}"
    effect_table = f"phase06_effect_{suffix}"
    test_engine = create_postgresql_engine(settings)
    try:
        with test_engine.begin() as connection:
            connection.execute(
                text(
                    f'CREATE TABLE public."{source_table}" '
                    "(id text PRIMARY KEY, payload text NOT NULL)"
                )
            )
            connection.execute(
                text(
                    f'INSERT INTO public."{source_table}" VALUES '
                    "('one', 'manual-and-scheduled')"
                )
            )
            connection.execute(
                text(
                    f'CREATE TABLE public."{target_table}" '
                    "(id text PRIMARY KEY, payload text NOT NULL)"
                )
            )
            connection.execute(
                text(
                    f'CREATE TABLE public."{effect_table}" ('
                    "effect_id text PRIMARY KEY, intent_fingerprint text NOT NULL, "
                    "publication_id text NOT NULL UNIQUE, row_count bigint NOT NULL, "
                    "committed_at timestamptz NOT NULL DEFAULT now())"
                )
            )
    finally:
        test_engine.dispose()

    profile = Profile(
        name=f"phase06-{suffix}",
        security_mode="production",
        sql_engine="sql",
        plugin_allowlist={
            "etlantic-sql": ">=0.50.0,<0.57.0",
            "etlantic-local": "==0.50.0",
        },
    )
    profile_path = tmp_path / f"{profile.name}.json"
    profile_path.write_text(json.dumps(profile.to_dict()), encoding="utf-8")
    service_ctx = ControlPlaneContext(
        principal=Principal("phase06-runtime", kind="service"),
        tenant=TenantRef("phase06-runtime"),
        workspace=WorkspaceRef("phase06-runtime", "qualification"),
        environment=EnvironmentRef("test"),
        security_domain=SecurityDomain("phase06-runtime"),
    )
    human = Principal("phase06-user", issuer="https://identity.example")
    gateway_ctx = replace(service_ctx, principal=human)
    authorizer = MemoryAuthorizer()
    for ctx in (service_ctx, gateway_ctx):
        for action in (
            "definition.write",
            "definition.read",
            "run.submit",
            "run.read",
            "run.report",
            "run.artifacts",
            "run.artifact.content",
            "run.retry",
            "run.rerun",
            "input.read",
        ):
            authorizer.grant(ctx, action)

    def context_factory(principal: Principal, _request: Request) -> ControlPlaneContext:
        return replace(gateway_ctx, principal=principal)

    class AllowTestSecret:
        async def authorize_late_binding(
            self, reference: SecretRef, context: SecretResolutionContext
        ) -> bool:
            return (
                reference.name == "SHUETL_PHASE06_SQL_URL"
                and context.trusted_scope is not None
            )

    secret_authorizer = AllowTestSecret()

    def planning_context_factory(
        _ctx: ControlPlaneContext, effective_profile: Profile
    ) -> PlanningContext:
        planning = PlanningContext.create(profile=effective_profile)
        for binding, kind, table, config in (
            ("source", "source", source_table, {"schema": "public"}),
            (
                "result",
                "sink",
                target_table,
                {
                    "schema": "public",
                    "mode": "upsert",
                    "key_columns": ["id"],
                    "effect_table": f"public.{effect_table}",
                },
            ),
        ):
            planning.registry.register_binding(
                BindingDescriptor(
                    binding=binding,
                    provider="postgresql",
                    kind=kind,
                    location=table,
                    secret_ref=SecretRef(
                        provider="env",
                        name="SHUETL_PHASE06_SQL_URL",
                        key="value",
                    ),
                    config=config,
                )
            )
        return planning

    def factory(preview_settings: ShuETLSettings) -> HostRuntimeBindings:
        if preview_settings.role == "gateway":
            identity = HostIdentityAdapter.create(
                principal_dependency=lambda: human,
                context_factory=context_factory,
            )
            return HostRuntimeBindings(
                authorizer=authorizer,
                identity_adapter=identity,
                planning_context_factory=planning_context_factory,
            )
        return HostRuntimeBindings(
            authorizer=authorizer,
            service_context=service_ctx,
            planning_context_factory=planning_context_factory,
            secret_alias_authorizer=(
                secret_authorizer if preview_settings.role == "worker" else None
            ),
        )

    factory_module = types.ModuleType("phase_0_6_test_host")
    factory_module.__dict__["build"] = factory
    monkeypatch.setitem(sys.modules, factory_module.__name__, factory_module)
    monkeypatch.setenv("SHUETL_PHASE06_SQL_URL", runtime_database_url)

    def role_settings(role: str, probe_port: int) -> ShuETLSettings:
        return ShuETLSettings(
            profile="postgresql-preview",
            role=role,
            provider="postgresql",
            identity="host",
            database_url=runtime_database_url,
            postgresql_sslmode=settings.postgresql_sslmode,
            factory="phase_0_6_test_host:build",
            store_id=f"phase06-{suffix}",
            tenant_id=service_ctx.tenant.tenant_id,
            workspace_id=service_ctx.workspace.workspace_id,
            execution_profile=str(profile_path),
            worker_kind="runs" if role == "worker" else None,
            probe_port=probe_port,
            gateway_port=probe_port + 1,
            artifact_root=str(tmp_path / "artifacts"),
        )

    gateway = None
    scheduler = None
    worker = None
    try:
        admin_engine = create_postgresql_engine(settings)
        try:
            with admin_engine.begin() as connection:
                connection.execute(
                    text("REVOKE CREATE ON SCHEMA public FROM shuetl_runtime")
                )
        finally:
            admin_engine.dispose()
        with pytest.raises(ProgrammingError, match="permission denied for schema"):
            build_managed_runtime(role_settings("worker", 19006))
        admin_engine = create_postgresql_engine(settings)
        try:
            with admin_engine.begin() as connection:
                connection.execute(
                    text("GRANT CREATE ON SCHEMA public TO shuetl_runtime")
                )
        finally:
            admin_engine.dispose()

        runtime_settings = role_settings("worker", 19004)
        inspection_engine = create_postgresql_engine(runtime_settings)
        try:
            with inspection_engine.connect() as connection:
                assert (
                    connection.exec_driver_sql("SELECT current_user").scalar_one()
                    == "shuetl_runtime"
                )
                assert connection.exec_driver_sql(
                    "SELECT has_schema_privilege(current_user, 'public', 'CREATE')"
                ).scalar_one()
        finally:
            inspection_engine.dispose()

        admin_engine = create_postgresql_engine(settings)
        try:
            with admin_engine.connect() as connection:
                schema_at_start = _public_schema_snapshot(connection)
                version_at_start = connection.exec_driver_sql(
                    "SELECT version FROM etlantic_sqlmodel_schema_version WHERE id = 1"
                ).scalar_one()
        finally:
            admin_engine.dispose()

        gateway = build_managed_runtime(role_settings("gateway", 19000))
        scheduler = build_managed_runtime(role_settings("scheduler", 19002))
        worker = build_managed_runtime(role_settings("worker", 19004))
        admin_engine = create_postgresql_engine(settings)
        try:
            with admin_engine.connect() as connection:
                schema_after_construction = _public_schema_snapshot(connection)
                version_after_construction = connection.exec_driver_sql(
                    "SELECT version FROM etlantic_sqlmodel_schema_version WHERE id = 1"
                ).scalar_one()
        finally:
            admin_engine.dispose()
        assert schema_after_construction == schema_at_start
        assert version_after_construction == version_at_start

        assert gateway.app is not None
        service = gateway.backend.api.managed_service
        assert service is not None
        definition_id = f"phase06-pipe-{suffix}"
        service.register_definition(
            service_ctx,
            definition_id,
            pipeline_to_dict(definition_from_pipeline(TransferPipeline)),
        )
        definition_revision, profile_name = service.pin_schedule_definition_revision(
            service_ctx, definition_id
        )

        with TestClient(gateway.app) as client:
            manual_response = client.post(
                f"/etl/v1/definitions/{definition_id}/runs",
                headers={"Idempotency-Key": f"manual-{suffix}"},
                json={"payload": {}},
            )
        assert manual_response.status_code == 202, manual_response.text
        manual_receipt = gateway.backend.api.durable_work.get_submission(
            gateway_ctx, manual_response.json()["submission_id"]
        )
        assert manual_receipt is not None and manual_receipt.run_id is not None
        assert worker.service is not None and worker.context is not None
        worker_errors: list[str] = []
        worker_outcomes: list[str] = []
        original_runner = worker.service.runner

        def observe_runner(ctx: Any, **kwargs: Any) -> Any:
            try:
                outcome = original_runner(ctx, **kwargs)
                status = getattr(outcome, "status", None)
                diagnostics = getattr(outcome, "diagnostics", ())
                diagnostic_details = [
                    (
                        f"{getattr(item, 'code', 'unknown')}: "
                        f"{getattr(item, 'message', '')}".replace(
                            runtime_database_url, "[redacted]"
                        )
                    )
                    for item in diagnostics
                ]
                worker_outcomes.append(
                    f"status={status}; diagnostics={diagnostic_details!r}"
                )
                return outcome
            except Exception as exc:
                message = str(exc).replace(runtime_database_url, "[redacted]")
                causes: list[str] = []
                cause = exc.__cause__
                while cause is not None:
                    cause_message = str(cause).replace(
                        runtime_database_url, "[redacted]"
                    )
                    causes.append(f"{type(cause).__name__}: {cause_message}")
                    cause = cause.__cause__
                detail = f"; caused by {' <- '.join(causes)}" if causes else ""
                worker_errors.append(f"{type(exc).__name__}: {message}{detail}")
                raise

        worker.service.runner = observe_runner
        assert worker.service.tick(worker.context, limit=1) == 1
        manual_publication = (
            gateway.backend.api.durable_work.get_latest_result_publication(
                service_ctx, manual_receipt.submission_id
            )
        )
        durable_work = gateway.backend.api.durable_work
        submission_after_tick = durable_work.get_submission(
            service_ctx, manual_receipt.submission_id
        )
        attempts_after_tick = durable_work.list_attempts(
            service_ctx, manual_receipt.submission_id
        )
        assert manual_publication is not None, (
            "Worker did not publish a durable run result; "
            f"submission_status={submission_after_tick.status}; "
            f"attempts={attempts_after_tick!r}; "
            f"runner_errors={worker_errors!r}; outcomes={worker_outcomes!r}"
        )
        manual_report = service.get_run_report(service_ctx, manual_receipt.run_id)
        assert manual_report["status"] == "succeeded", manual_report

        assert scheduler.context is not None and scheduler.service is not None
        scheduler.backend.api.schedule_store.create(
            scheduler.context,
            definition_id=definition_id,
            definition_revision_id=definition_revision,
            profile_name=profile_name,
            spec=ScheduleSpec(kind="interval", interval_seconds=60),
            schedule_id=f"schedule-{suffix}",
            next_fire_at=(datetime.now(UTC) - timedelta(seconds=120))
            .isoformat()
            .replace("+00:00", "Z"),
        )
        assert scheduler.service.tick(scheduler.context) == 1
        assert worker.service.tick(worker.context, limit=1) == 1
        firings = scheduler.backend.api.schedule_store.list_firings(
            scheduler.context, f"schedule-{suffix}"
        )
        assert len(firings) == 1 and firings[0].submission_id is not None
        scheduled_submission = scheduler.backend.api.durable_work.get_submission(
            service_ctx, firings[0].submission_id
        )
        assert scheduled_submission is not None
        assert scheduled_submission.run_id is not None
        scheduled_report = service.get_run_report(
            service_ctx, scheduled_submission.run_id
        )
        assert scheduled_report["status"] == "succeeded", scheduled_report

        check_engine = create_postgresql_engine(settings)
        try:
            with check_engine.connect() as connection:
                rows = connection.execute(
                    text(f'SELECT id, payload FROM public."{target_table}"')
                ).all()
                effects = connection.execute(
                    text(f'SELECT effect_id FROM public."{effect_table}"')
                ).all()
            assert rows == [("one", "manual-and-scheduled")]
            assert len(effects) == 2
        finally:
            check_engine.dispose()
    finally:
        if worker is not None:
            worker.close()
        if scheduler is not None:
            scheduler.close()
        if gateway is not None:
            gateway.close()
        cleanup_engine = create_postgresql_engine(settings)
        try:
            with cleanup_engine.begin() as connection:
                connection.execute(
                    text(f'DROP TABLE IF EXISTS public."{source_table}"')
                )
                connection.execute(
                    text(f'DROP TABLE IF EXISTS public."{target_table}"')
                )
                connection.execute(
                    text(f'DROP TABLE IF EXISTS public."{effect_table}"')
                )
        finally:
            cleanup_engine.dispose()
