"""Verify the published fixes using disposable PostgreSQL and a separate worker."""

import argparse
import asyncio
import json
import os
import secrets
import selectors
import subprocess
import sys
import time
import uuid
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path

from etlantic import Data, Extract, Input, Load, Output, Pipeline, Transformation
from etlantic.authoring import definition_from_pipeline
from etlantic.authoring.serialize import pipeline_to_dict
from etlantic.control_plane import (
    ControlPlaneContext,
    ControlPlaneError,
    EnvironmentRef,
    MemoryAuthorizer,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic.transform import functions as F
from etlantic.transform.compiler import (
    TransformCompileContext,
    TransformExecutionContext,
)
from etlantic.transform.local_compiler import LocalTransformCompiler
from etlantic_sqlmodel import (
    SQLModelBackendConfig,
    apply_migrations,
    create_managed_backend,
)
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ACTIONS = (
    "definition.write",
    "connector.test",
    "connector.schema.inspect",
    "connector.preflight",
    "connector.action.read",
)
ROW_SENTINEL = "phase06-source-row-must-not-be-disclosed"


class Row(Data):
    id: int
    quantity: int


class Deduplicate(Transformation):
    rows: Input[Row]
    result: Output[Row]


@Deduplicate.portable
def deduplicate(rows):
    return rows.sort(F.col("id").asc(), F.col("quantity").asc()).dropDuplicates("id")


class SavedPipeline(Pipeline):
    source: Extract[Row] = Extract(asset="source")
    result: Load[Row] = Load(input=source, asset="result")


class RevisedPipeline(Pipeline):
    source: Extract[Row] = Extract(asset="revised-source")
    result: Load[Row] = Load(input=source, asset="revised-result")


def context():
    return ControlPlaneContext(
        principal=Principal("probe", issuer="shuetl-review", kind="service"),
        tenant=TenantRef("probe"),
        workspace=WorkspaceRef("probe", "probe"),
        environment=EnvironmentRef("test"),
        security_domain=SecurityDomain("probe"),
        resource_owner_id="probe",
    )


def authorizer():
    auth = MemoryAuthorizer()
    for action in ACTIONS:
        auth.grant(context(), action)
    return auth


def verify_sort():
    compiler = LocalTransformCompiler()
    compiled = compiler.compile(
        Deduplicate.to_transform_plan(),
        context=TransformCompileContext(
            pipeline_id="probe",
            plan_id="sort",
            step_name="dedup",
            profile_name="development",
            engine="local",
        ),
    )

    async def execute(rows):
        bundle = await compiler.execute(
            compiled,
            inputs={"rows": rows},
            parameters={},
            context=TransformExecutionContext(
                run_id="probe",
                pipeline_id="probe",
                plan_id="sort",
                step_name="dedup",
                engine="local",
            ),
        )
        return list(bundle.valid["result"])

    rows = [{"id": 1, "quantity": 4}, {"id": 1, "quantity": 3}]
    forward = asyncio.run(execute(rows))
    reverse = asyncio.run(execute(list(reversed(rows))))
    assert forward == reverse == [{"id": 1, "quantity": 3}]
    return {"forward": forward, "reversed": reverse, "deterministic": True}


def worker():
    from etlantic_sql import create_action_handlers

    engine = create_engine(
        os.environ["PROBE_RUNTIME_URL"],
        connect_args={"connect_timeout": 2, "options": "-c search_path=data"},
    )
    calls = []

    def resolve_engine(ctx, connection_id, *, timeout_seconds):
        assert ctx == context() and 0 < timeout_seconds <= 30
        calls.append(
            {
                "connection_id": connection_id,
                "pid": os.getpid(),
                "timeout_seconds": timeout_seconds,
            }
        )
        if connection_id == "slow-connection":
            time.sleep(min(timeout_seconds + 0.2, 3))
            raise TimeoutError(ROW_SENTINEL)
        if connection_id != "saved-connection":
            raise ValueError(ROW_SENTINEL)
        return engine

    handlers = create_action_handlers(resolve_engine)
    backend = create_managed_backend(
        SQLModelBackendConfig(
            database_url=os.environ["PROBE_RUNTIME_URL"],
            store_id="probe",
            action_handlers=handlers,
        ),
        authorizer=authorizer(),
    )
    try:
        host = backend.create_action_execution_host(worker_id="published-action-probe")
        print(json.dumps({"ready": True, "pid": os.getpid()}), flush=True)
        assert sys.stdin.readline().strip() == "execute"
        count = host.tick(context())
        assert "fastapi" not in sys.modules and "etlantic_fastapi" not in sys.modules
        print(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "count": count,
                    "resolver_calls": calls,
                    "handler_names": sorted(host.handlers),
                    "http_imports_absent": True,
                }
            )
        )
    finally:
        backend.close()
        engine.dispose()


def snapshot(engine):
    with engine.connect() as conn:
        columns = list(
            conn.execute(
                text(
                    "SELECT table_name, column_name, data_type "
                    "FROM information_schema.columns WHERE table_schema='data' "
                    "ORDER BY table_name, ordinal_position"
                )
            )
        )
        rows = list(conn.execute(text("SELECT * FROM data.sample")))
        return columns, rows


def verify_actions(admin_url):
    # Own only a uniquely named database and role on an explicitly disposable server.
    token = uuid.uuid4().hex[:12]
    database, runtime_role = f"probe0572_{token}", f"probe0572_user_{token}"
    password = secrets.token_urlsafe(24)
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    operator = backend = None
    try:
        with admin.connect() as conn:
            server = str(conn.execute(text("SHOW server_version")).scalar_one())
            assert server.split()[0] == "18.6", server
            literal = conn.execute(
                text("SELECT quote_literal(:password)"), {"password": password}
            ).scalar_one()
            conn.execute(
                text(
                    f'CREATE ROLE "{runtime_role}" LOGIN NOSUPERUSER NOCREATEDB '
                    f"NOCREATEROLE NOINHERIT PASSWORD {literal}"
                )
            )
            conn.execute(text(f'CREATE DATABASE "{database}"'))
        url = make_url(admin_url).set(database=database)
        runtime_url = url.set(
            username=runtime_role, password=password
        ).render_as_string(hide_password=False)
        operator = create_engine(url)
        apply_migrations(operator)
        with operator.begin() as conn:
            conn.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
            conn.execute(text("CREATE SCHEMA data"))
            conn.execute(
                text(
                    "CREATE TABLE data.sample (id integer PRIMARY KEY, "
                    "quantity integer, payload text, extra text)"
                )
            )
            conn.execute(
                text("INSERT INTO data.sample VALUES (1, 3, :sentinel, 'extra')"),
                {"sentinel": ROW_SENTINEL},
            )
            conn.execute(
                text(f'GRANT USAGE ON SCHEMA public, data TO "{runtime_role}"')
            )
            conn.execute(
                text(
                    "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES "
                    f'IN SCHEMA public TO "{runtime_role}"'
                )
            )
            conn.execute(
                text(
                    "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES "
                    f'IN SCHEMA public TO "{runtime_role}"'
                )
            )
            conn.execute(
                text(f'GRANT SELECT ON ALL TABLES IN SCHEMA data TO "{runtime_role}"')
            )
        before = snapshot(operator)
        auth = authorizer()
        backend = create_managed_backend(
            SQLModelBackendConfig(database_url=runtime_url, store_id="probe"),
            authorizer=auth,
        )
        service, ctx = backend.managed_service, context()
        first = service.register_definition(
            ctx,
            "saved-pipeline",
            pipeline_to_dict(definition_from_pipeline(SavedPipeline)),
        )
        requests = {
            "connector.test": {
                "provider": "postgresql",
                "connection_id": "saved-connection",
            },
            "connector.schema.inspect": {
                "provider": "postgresql",
                "connection_id": "saved-connection",
                "max_fields": 2,
            },
            "connector.preflight": {"definition_id": "saved-pipeline"},
        }
        jobs = {
            action: service.submit_connector_action(
                ctx, action, request, idempotency_key=action
            )
            for action, request in requests.items()
        }
        second = service.register_definition(
            ctx,
            "saved-pipeline",
            pipeline_to_dict(definition_from_pipeline(RevisedPipeline)),
        )
        assert second["revision_id"] != first["revision_id"]
        retried = service.submit_connector_action(
            ctx,
            "connector.preflight",
            requests["connector.preflight"],
            idempotency_key="connector.preflight",
        )
        assert retried["action_id"] == jobs["connector.preflight"]["action_id"]
        jobs["revoked"] = service.submit_connector_action(
            ctx,
            "connector.test",
            {"provider": "postgresql", "connection_id": "revoked-connection"},
            idempotency_key="revoked",
        )
        proc = subprocess.Popen(
            [sys.executable, "-I", str(Path(__file__).resolve()), "--worker"],
            env={**os.environ, "PROBE_RUNTIME_URL": runtime_url},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            assert proc.stdout is not None
            with selectors.DefaultSelector() as selector:
                selector.register(proc.stdout, selectors.EVENT_READ)
                assert selector.select(30), "action worker startup exceeded 30 seconds"
            ready = json.loads(proc.stdout.readline())
            assert ready["ready"] is True
            # Start the deadline after worker initialization, not interpreter startup.
            jobs["deadline"] = service.submit_connector_action(
                ctx,
                "connector.test",
                {"provider": "postgresql", "connection_id": "slow-connection"},
                idempotency_key="deadline",
                deadline_seconds=2,
            )
            output, _stderr = proc.communicate("execute\n", timeout=45)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate(timeout=10)
        assert proc.returncode == 0, "isolated action worker failed"
        observed = json.loads(output)
        assert observed["pid"] != os.getpid() and observed["count"] == len(jobs)
        receipts = {
            name: service.get_connector_action(ctx, job["action_id"])
            for name, job in jobs.items()
        }
        for action in requests:
            assert receipts[action]["status"] == "succeeded", receipts[action]
        assert receipts["connector.test"]["result"]["ok"] is True
        schema = receipts["connector.schema.inspect"]["result"]
        assert len(schema["fields"]) == 2 and schema["has_more"] is True
        assert [field["name"] for field in schema["fields"]] == ["id", "quantity"]
        preflight = receipts["connector.preflight"]["result"]
        assert (
            preflight["ok"] is True and preflight["revision_id"] == first["revision_id"]
        )
        assert preflight["metadata"]["mode"] == "read_only_plan"
        assert receipts["revoked"]["status"] == "failed"
        assert receipts["deadline"]["status"] == "timed_out"
        assert receipts["deadline"]["error_code"] == "deadline_exceeded"
        assert snapshot(operator) == before
        foreign = replace(
            ctx,
            principal=Principal("foreign", issuer="shuetl-review", kind="service"),
            resource_owner_id="foreign",
        )
        auth.grant(foreign, "connector.action.read")
        try:
            service.get_connector_action(foreign, jobs["connector.test"]["action_id"])
        except ControlPlaneError as exc:
            assert exc.status in (403, 404)
        else:
            raise AssertionError("cross-owner action was visible")
        encoded = json.dumps(receipts)
        assert password not in encoded and ROW_SENTINEL not in encoded
        return {
            "postgresql_version": server,
            "gateway_pid": os.getpid(),
            "worker": observed,
            "results": {
                name: {
                    key: receipt.get(key) for key in ("status", "error_code", "result")
                }
                for name, receipt in receipts.items()
            },
            "revision_pin_preserved": True,
            "cross_owner_hidden": True,
            "data_schema_and_rows_unchanged": True,
            "sentinels_absent": True,
        }
    finally:
        if backend is not None:
            backend.close()
        if operator is not None:
            operator.dispose()
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)'))
            conn.execute(text(f'DROP ROLE IF EXISTS "{runtime_role}"'))
        admin.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--disposable-admin-url")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    packages = {
        name: version(name)
        for name in ("etlantic", "etlantic-sql", "etlantic-sqlmodel")
    }
    assert set(packages.values()) == {"0.57.2"}, packages
    if args.worker:
        worker()
        return
    if not args.disposable_admin_url or args.output is None:
        parser.error("require --disposable-admin-url and --output")
    result = {
        "packages": packages,
        "python": sys.version,
        "sort_dedup": verify_sort(),
        "actions": verify_actions(args.disposable_admin_url),
        "status": "passed",
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": "passed", "output": str(args.output)}))


if __name__ == "__main__":
    main()
