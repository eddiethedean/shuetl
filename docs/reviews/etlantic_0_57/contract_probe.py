"""Focused installed-wheel checks; not ShuETL PostgreSQL release qualification."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import inspect
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

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
from etlantic_sqlmodel import (
    SQLModelBackendConfig,
    apply_migrations,
    create_managed_backend,
    create_sqlite_engine,
    inspect_schema,
    schema_requirements,
)
from sqlalchemy import event
from sqlalchemy.pool import StaticPool


class ProbeRow(Data):
    id: int


class ProbePipeline(Pipeline):
    source: Extract[ProbeRow] = Extract(asset="source")
    result: Load[ProbeRow] = Load(input=source, asset="result")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("headless", "gateway"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "headless":
        assert importlib.util.find_spec("fastapi") is None
        assert importlib.util.find_spec("etlantic_fastapi") is None
    ctx = ControlPlaneContext(
        principal=Principal(subject="contract-probe", issuer="shuetl-review"),
        tenant=TenantRef(tenant_id="probe-tenant"),
        workspace=WorkspaceRef(
            tenant_id="probe-tenant", workspace_id="probe-workspace"
        ),
        environment=EnvironmentRef(name="test"),
        security_domain=SecurityDomain(domain_id="probe"),
    )
    authorizer = MemoryAuthorizer()
    for action in ("definition.write", "run.submit", "schedule.write", "schedule.read"):
        authorizer.grant(ctx, action)
    engine = create_sqlite_engine("sqlite://", poolclass=StaticPool)
    commands, commits = [], []

    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        commands.append(statement.lstrip().split(None, 1)[0].upper())

    def commit(_connection):
        commits.append(True)

    event.listen(engine, "before_cursor_execute", capture)
    event.listen(engine, "commit", commit)
    fresh = inspect_schema(engine).to_dict()
    assert fresh["compatibility"] == "fresh"
    assert not commits and not set(commands) & {
        "CREATE",
        "ALTER",
        "INSERT",
        "UPDATE",
        "DELETE",
    }
    event.remove(engine, "before_cursor_execute", capture)
    event.remove(engine, "commit", commit)
    apply_migrations(engine)
    commands.clear()
    event.listen(engine, "before_cursor_execute", capture)
    event.listen(engine, "commit", commit)
    compatible = inspect_schema(engine).to_dict()
    backend = create_managed_backend(
        SQLModelBackendConfig(store_id="probe"), authorizer=authorizer, engine=engine
    )
    assert compatible["compatible"]
    assert backend.engine is engine and not backend.owns_engine
    assert not commits and not set(commands) & {
        "CREATE",
        "ALTER",
        "INSERT",
        "UPDATE",
        "DELETE",
    }
    event.remove(engine, "before_cursor_execute", capture)
    event.remove(engine, "commit", commit)
    assert not hasattr(backend, "api")
    assert "context_factory" not in inspect.signature(create_managed_backend).parameters
    assert backend.schedule_service.schedule_store is backend.schedule_store
    assert backend.schedule_service.managed_service is backend.managed_service
    backend.managed_service.register_definition(
        ctx, "probe-pipeline", pipeline_to_dict(definition_from_pipeline(ProbePipeline))
    )
    service = backend.schedule_service
    schedule = service.create(
        ctx, "probe-pipeline", spec=ScheduleSpec(kind="interval", interval_seconds=60)
    )
    assert service.get(ctx, schedule.schedule_id) == schedule
    assert service.list_definition(ctx, "probe-pipeline") == (schedule,)
    assert service.preview(ctx, schedule.schedule_id)
    service.pause(ctx, schedule.schedule_id)
    service.resume(ctx, schedule.schedule_id)
    denied_ctx = ControlPlaneContext(
        principal=Principal(subject="denied", issuer="shuetl-review"),
        tenant=ctx.tenant,
        workspace=WorkspaceRef(
            tenant_id="probe-tenant", workspace_id="denied-workspace"
        ),
        environment=ctx.environment,
        security_domain=ctx.security_domain,
    )
    try:
        service.get(denied_ctx, schedule.schedule_id)
    except ControlPlaneError:
        pass
    else:
        raise AssertionError("unauthorized schedule read succeeded")
    observations = {
        "fastapi_installed": importlib.util.find_spec("fastapi") is not None,
        "fresh_schema": fresh,
        "compatible_schema": compatible,
        "inspection_and_construction_no_writes_or_commits": True,
        "neutral_backend": True,
        "shared_authorized_schedule_commands": True,
        "borrowed_engine_preserved": True,
    }
    signatures = {
        "create_managed_backend": str(inspect.signature(create_managed_backend)),
        "create_scheduler": str(inspect.signature(backend.create_scheduler)),
        "create_execution_host": str(inspect.signature(backend.create_execution_host)),
        "create_action_execution_host": str(
            inspect.signature(backend.create_action_execution_host)
        ),
    }
    if args.mode == "headless":
        roles = {
            "scheduler": backend.create_scheduler(owner_id="probe-scheduler"),
            "run_worker": backend.create_execution_host(owner_id="probe-run-worker"),
            "action_worker": backend.create_action_execution_host(
                worker_id="probe-action-worker"
            ),
        }
        initial = {name: role.status().to_dict() for name, role in roles.items()}
        assert all(status["prerequisites"] == "unknown" for status in initial.values())
        for role in roles.values():
            role.tick(ctx)
        after = {name: role.status().to_dict() for name, role in roles.items()}
        for role in roles.values():
            role.request_drain()
            role.request_drain()
            assert role.status().admission in {"draining", "stopped"}
            assert not role.status().ready
        observations["initial_role_statuses"] = initial
        observations["after_empty_ticks"] = after
        observations["repeated_drain_all_roles"] = True
    else:
        from etlantic_fastapi import adapt_managed_backend
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        def context_factory(_request, _principal):
            return ctx

        def principal_dependency():
            return ctx.principal

        adapter = adapt_managed_backend(
            backend,
            context_factory=context_factory,
            principal_dependency=principal_dependency,
        )
        assert adapter.api.managed_service is backend.managed_service
        assert adapter.api.get_schedule_service() is backend.schedule_service
        app = FastAPI()
        app.include_router(adapter.api.router)
        assert "etlantic.runtime.execution_host" not in sys.modules
        assert "etlantic.runtime.action_execution_host" not in sys.modules
        with TestClient(app) as client:
            response = client.get(f"/v1/schedules/{schedule.schedule_id}")
            assert response.status_code == 200, response.text
            assert response.json() == service.get(ctx, schedule.schedule_id).to_dict()
            response = client.post(
                "/v1/definitions/probe-pipeline/schedules",
                json={"spec": {"kind": "interval", "interval_seconds": 120}},
            )
            assert response.status_code == 201, response.text
            created = response.json()
            assert service.get(ctx, created["schedule_id"]).to_dict() == created
        observations["http_headless_shared_records"] = True
        observations["gateway_execution_imports_absent"] = True
        signatures["adapt_managed_backend"] = str(
            inspect.signature(adapt_managed_backend)
        )
    backend.close()
    backend.close()
    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT 1")
    # Destructive fixture operation uses only this disposable in-memory database
    # and an object name obtained from public provider requirements.
    required = schema_requirements()
    object_name = required.objects[0].name
    with engine.begin() as connection:
        connection.exec_driver_sql(f'DROP TABLE "{object_name}"')
    partial = inspect_schema(engine).to_dict()
    assert partial["compatibility"] == "partial_or_corrupt"
    observations["partial_schema"] = partial
    engine.dispose()
    packages = ("etlantic", "etlantic-sqlmodel") + (
        ("etlantic-fastapi", "fastapi", "pydantic", "sqlalchemy")
        if args.mode == "gateway"
        else ()
    )
    result = {
        "schema": "shuetl.etlantic_0_57.contract_probe/1",
        "status": "passed",
        "observed_at": datetime.now(UTC).isoformat(),
        "mode": args.mode,
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {name: importlib.metadata.version(name) for name in packages},
        "module_origins": {
            name: str(importlib.util.find_spec(name).origin)
            for name in ("etlantic", "etlantic_sqlmodel")
        },
        "observations": observations,
        "signatures": signatures,
        "limitations": [
            "SQLite in-process checks only",
            "No real ETL effects, active drain, crash recovery "
            "or PostgreSQL grants qualification",
            "Not a ShuETL Gate 0 or release PASS",
        ],
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"mode": args.mode, "status": "passed"}))


if __name__ == "__main__":
    main()
