"""Reproduce required action and deterministic dedup gaps on published wheels."""

import asyncio
import json
from importlib.metadata import version

from etlantic import Data, Input, Output, Transformation
from etlantic.control_plane import (
    ControlPlaneContext,
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
from etlantic_sql import create_action_handlers
from etlantic_sqlmodel import SQLModelBackendConfig, create_managed_backend
from etlantic_sqlmodel.migrations import apply_migrations
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool


class Row(Data):
    id: int
    quantity: int


class Deduplicate(Transformation):
    rows: Input[Row]
    result: Output[Row]


@Deduplicate.portable
def deduplicate(rows):
    return rows.sort(F.col("id").asc(), F.col("quantity").asc()).dropDuplicates("id")


def main():
    packages = {
        name: version(name)
        for name in ("etlantic", "etlantic-sql", "etlantic-sqlmodel")
    }
    assert set(packages.values()) == {"0.57.1"}, packages
    compiler = LocalTransformCompiler()
    plan = Deduplicate.to_transform_plan()
    compiled = compiler.compile(
        plan,
        context=TransformCompileContext(
            pipeline_id="requirements",
            plan_id="dedup",
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
                pipeline_id="requirements",
                plan_id="dedup",
                step_name="dedup",
                engine="local",
            ),
        )
        return list(bundle.valid["result"])

    rows = [{"id": 1, "quantity": 4}, {"id": 1, "quantity": 3}]
    forward = asyncio.run(execute(rows))
    reversed_rows = asyncio.run(execute(list(reversed(rows))))

    ctx = ControlPlaneContext(
        principal=Principal(
            "requirements-probe", issuer="shuetl-review", kind="service"
        ),
        tenant=TenantRef("probe"),
        workspace=WorkspaceRef("probe", "probe"),
        environment=EnvironmentRef("test"),
        security_domain=SecurityDomain("probe"),
    )
    authorizer = MemoryAuthorizer()
    actions = {
        "connector.test": {
            "provider": "postgresql",
            "connection_id": "saved-connection",
        },
        "connector.schema.inspect": {
            "provider": "postgresql",
            "connection_id": "saved-connection",
        },
        "connector.preflight": {"definition_id": "saved-definition"},
    }
    for action in (*actions, "connector.action.read"):
        authorizer.grant(ctx, action)
    resolver_calls = []

    def resolve_engine(context, connection_id):
        resolver_calls.append(connection_id)
        raise AssertionError("Missing handlers must not resolve the connection")

    handlers = create_action_handlers(resolve_engine)
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    apply_migrations(engine)
    backend = create_managed_backend(
        SQLModelBackendConfig(store_id="probe", action_handlers=handlers),
        authorizer=authorizer,
        engine=engine,
    )
    try:
        host = backend.create_action_execution_host(worker_id="probe-worker")
        jobs = {
            action: backend.managed_service.submit_connector_action(
                ctx,
                action,
                request,
                idempotency_key=action,
            )
            for action, request in actions.items()
        }
        assert host.tick(ctx) == len(jobs)
        results = {}
        for action, job in jobs.items():
            result = backend.managed_service.get_connector_action(ctx, job["action_id"])
            results[action] = {
                key: result.get(key) for key in ("status", "error_code", "result")
            }
        print(
            json.dumps(
                {
                    "packages": packages,
                    "local_compiler": compiler.info.to_dict(),
                    "sort_dedup": {
                        "forward": forward,
                        "reversed": reversed_rows,
                        "deterministic": forward == reversed_rows,
                    },
                    "sql_handler_names": sorted(handlers),
                    "worker_handler_names": sorted(host.handlers),
                    "action_results": results,
                    "resolver_calls": resolver_calls,
                },
                indent=2,
            )
        )
    finally:
        backend.close()
        engine.dispose()


if __name__ == "__main__":
    main()
