"""One independently launched role, driven through a bounded JSON pipe."""

from __future__ import annotations

import json
import os
import sys
import traceback
from dataclasses import asdict, replace
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

from etlantic import Data, Extract, Load, Pipeline
from etlantic.authoring import definition_from_pipeline
from etlantic.authoring.serialize import pipeline_to_dict
from etlantic.control_plane import (
    ControlPlaneContext,
    ControlPlaneError,
    EnvironmentRef,
    FakeScheduleClock,
    MemoryAuthorizer,
    Principal,
    ScheduleSpec,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic.profile import Profile
from etlantic.registry import BindingDescriptor, PlanningContext
from etlantic_sqlmodel import SQLModelBackendConfig, create_managed_backend
from sqlalchemy import create_engine, event


class Row(Data):
    id: str
    payload: str


class Transfer(Pipeline):
    source: Extract[Row] = Extract(asset="source")
    sink: Load[Row] = Load(input=source, asset="sink")


def main():
    role = sys.argv[1]
    root = Path(os.environ["PHASE06_ROOT"])
    ctx = ControlPlaneContext(
        principal=Principal("gate0-workload", issuer="reference-host", kind="service"),
        tenant=TenantRef("gate0"),
        workspace=WorkspaceRef("gate0", "qualification"),
        environment=EnvironmentRef("test"),
        security_domain=SecurityDomain("gate0"),
    )
    auth = MemoryAuthorizer()
    for action in (
        "definition.write",
        "run.submit",
        "run.read",
        "run.report",
        "input.read",
        "schedule.write",
        "schedule.read",
        "action.execute",
    ):
        auth.grant(ctx, action)
    profile = Profile(
        name="gate0",
        security_mode="production",
        plugin_allowlist={
            "etlantic": "0.57.0",
            "etlantic-local": "0.50.0",
            "etlantic-sql": "0.57.0",
            "postgresql": "0.57.0",
            "local-files": "0.57.0",
        },
        safe_io={"approved_roots": [str(root / "landing")]},
    )

    def planning_factory(_ctx, effective_profile):
        planning = PlanningContext.create(profile=effective_profile)
        planning.registry.register_binding(
            BindingDescriptor(
                binding="source",
                provider="local-files",
                kind="source",
                config={
                    "format": "csv",
                    "mode": "snapshot",
                    "root": ".",
                    "root_ref": "gate0-input",
                    "glob": "*.csv",
                },
            )
        )
        planning.registry.register_binding(
            BindingDescriptor(
                binding="sink",
                provider="postgresql",
                kind="sink",
                location="target",
                config={
                    "schema": "sink",
                    "mode": "append",
                    "effect_table": "sink.effects",
                },
            )
        )
        return planning

    clock = FakeScheduleClock(datetime(2026, 10, 9, tzinfo=UTC))
    engine = create_engine(os.environ["PHASE06_RUNTIME_URL"], pool_pre_ping=True)
    statements = []
    commits = []
    event.listen(
        engine,
        "before_cursor_execute",
        lambda _c, _cu, sql, _p, _ctx, _many: statements.append(
            sql.strip().split()[0].upper()
        ),
    )
    event.listen(engine, "commit", lambda _c: commits.append(True))
    backend = create_managed_backend(
        SQLModelBackendConfig(
            store_id="gate0",
            profile=profile,
            artifact_root=str(root / "artifacts"),
            schedule_clock=clock,
        ),
        authorizer=auth,
        engine=engine,
        planning_context_factory=planning_factory,
    )
    assert not commits
    assert not set(statements) & {
        "CREATE",
        "ALTER",
        "DROP",
        "INSERT",
        "UPDATE",
        "DELETE",
    }
    startup_sql = list(statements)
    worker = None
    client = None
    if role == "gateway":
        from etlantic_fastapi import adapt_managed_backend
        from fastapi.testclient import TestClient

        from shuetl import HostIdentityAdapter, ShuETL

        identity = HostIdentityAdapter.create(
            principal_dependency=lambda: ctx.principal,
            context_factory=lambda _p, _r: ctx,
        )
        adapter = adapt_managed_backend(
            backend,
            context_factory=identity.context_factory,
            principal_dependency=identity.principal_dependency,
        )
        client = TestClient(ShuETL(api=adapter.api).create_app(prefix="/etl"))
        client.__enter__()
    elif role == "scheduler":
        worker = backend.create_scheduler(
            owner_id=f"scheduler-{os.getpid()}", clock=clock
        )
    elif role == "run-worker":
        worker = backend.create_execution_host(owner_id=f"run-{os.getpid()}")
    elif role == "action-worker":
        worker = backend.create_action_execution_host(worker_id=f"action-{os.getpid()}")
    else:
        raise ValueError(role)
    import etlantic_sqlmodel

    print(
        json.dumps(
            {
                "started": role,
                "pid": os.getpid(),
                "startup_sql": startup_sql,
                "origin": etlantic_sqlmodel.__file__,
                "reference_origin": __file__,
                "versions": {
                    n: metadata.version(n)
                    for n in ("etlantic", "etlantic-sqlmodel", "etlantic-sql")
                },
                "http_imported": "fastapi" in sys.modules,
                "execution_imported": "etlantic.runtime.execution_host" in sys.modules,
            }
        ),
        flush=True,
    )
    try:
        for line in sys.stdin:
            command = json.loads(line)
            try:
                op = command["op"]
                if op == "definition":
                    result = backend.managed_service.register_definition(
                        ctx,
                        "transfer",
                        pipeline_to_dict(definition_from_pipeline(Transfer)),
                    )
                    result = {"registered": True}
                elif op == "http":
                    assert client is not None
                    response = client.request(
                        command["method"],
                        "/etl" + command["path"],
                        json=command.get("body"),
                        headers=command.get("headers", {}),
                    )
                    result = {"status": response.status_code, "body": response.json()}
                elif op == "schedule-get":
                    result = backend.schedule_service.get(
                        ctx, command["schedule_id"]
                    ).to_dict()
                elif op == "firings":
                    result = [
                        f.to_dict()
                        for f in backend.schedule_service.list_firings(
                            ctx, command["schedule_id"]
                        )
                    ]
                elif op == "submission":
                    result = {
                        "run_id": backend.durable_work.get_submission(
                            ctx, command["submission_id"]
                        ).run_id
                    }
                elif op == "schedule-command":
                    scope = (
                        replace(ctx, workspace=WorkspaceRef("gate0", "denied"))
                        if command.get("denied")
                        else ctx
                    )
                    method = command["method"]
                    identifier = command.get("schedule_id")
                    service = backend.schedule_service
                    try:
                        value: Any
                        if method == "amend":
                            value = service.amend(
                                scope,
                                identifier,
                                expected_revision_id=command["revision_id"],
                                spec=ScheduleSpec(kind="interval", interval_seconds=60),
                            )
                        elif method in ("pause", "resume", "get", "preview"):
                            value = getattr(service, method)(scope, identifier)
                        elif method == "list":
                            value = [
                                s.to_dict()
                                for s in service.list_definition(scope, "transfer")
                            ]
                        elif method == "trigger":
                            value, _ = service.trigger(
                                scope,
                                identifier,
                                nominal_fire_time=datetime.fromisoformat(
                                    command["instant"]
                                ),
                            )
                        else:
                            raise ValueError(method)
                        result = value.to_dict() if hasattr(value, "to_dict") else value
                    except ControlPlaneError as exc:
                        result = {"denial_status": exc.status}
                elif op == "report":
                    result = backend.managed_service.get_run_report(
                        ctx, command["run_id"]
                    )
                elif op == "tick":
                    assert worker is not None
                    if "instant" in command:
                        clock.set(datetime.fromisoformat(command["instant"]))
                    result = {
                        "count": worker.tick(ctx),
                        "status": asdict(worker.status()),
                    }
                elif op == "close":
                    if worker is not None:
                        worker.request_drain()
                        assert worker.tick(ctx) == 0
                    result = {"closed": True}
                else:
                    raise ValueError(op)
                print(json.dumps({"ok": result}, default=str), flush=True)
                if op == "close":
                    break
            except Exception as exc:
                print(
                    json.dumps(
                        {
                            "error": str(exc),
                            "type": type(exc).__name__,
                            "traceback": traceback.format_exc(),
                            "diagnostics": getattr(exc, "extensions", {}),
                        }
                    ),
                    flush=True,
                )
    finally:
        if client is not None:
            client.__exit__(None, None, None)
        if worker is not None:
            worker.request_drain()
        backend.close()
        with engine.connect() as connection:
            from sqlalchemy import text

            assert connection.execute(text("SELECT 1")).scalar_one() == 1
        engine.dispose()


if __name__ == "__main__":
    main()
