"""Rehearse fresh-store enrollment and retained 0.5 application rollback.

Requires two isolated installed environments. Each child completes before the
next authority starts. Only uniquely named disposable databases are removed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path


def child(mode):
    import importlib.metadata as metadata

    from etlantic.control_plane import (
        ControlPlaneContext,
        EnvironmentRef,
        MemoryAuthorizer,
        Principal,
        SecurityDomain,
        TenantRef,
        WorkspaceRef,
    )
    from etlantic_sqlmodel.migrations import upgrade
    from sqlalchemy import create_engine, event

    from shuetl.postgresql import inspect_postgresql_engine

    url = os.environ["TRANSITION_DATABASE_URL"]
    engine = create_engine(url)
    trace = []
    event.listen(
        engine,
        "before_cursor_execute",
        lambda _c, _cu, statement, _p, _cx, _m: trace.append(
            statement.strip().split()[0].upper()
        ),
    )
    ctx = ControlPlaneContext(
        principal=Principal(
            "transition-service", issuer="reference-host", kind="service"
        ),
        tenant=TenantRef("phase06"),
        workspace=WorkspaceRef("phase06", "transition"),
        environment=EnvironmentRef("test"),
        security_domain=SecurityDomain("phase06"),
    )
    result = {
        "pid": os.getpid(),
        "mode": mode,
        "versions": {
            name: metadata.version(name)
            for name in ("shuetl", "etlantic", "etlantic-fastapi", "etlantic-sqlmodel")
        },
    }
    if mode == "reject-old":
        from shuetl import PostgreSQLProviderBundle
        from shuetl.settings import ShuETLSettings

        settings = ShuETLSettings(
            profile="postgresql-pilot",
            role="gateway",
            provider="postgresql",
            identity="host",
            database_url=url,
            postgresql_sslmode="disable",
        )
        status = inspect_postgresql_engine(engine)
        assert status.state == "behind", status
        try:
            PostgreSQLProviderBundle.create(
                settings,
                authorizer=MemoryAuthorizer(),
                context_factory=lambda _p, _r: ctx,
                principal_dependency=lambda: ctx.principal,
            )
        except Exception as exc:
            assert type(exc).__name__ == "ProviderReadinessError", type(exc)
            result["rejection"] = type(exc).__name__
        else:
            raise AssertionError("0.6 accepted the retained 0.55 store")
        assert not set(trace) & {
            "CREATE",
            "ALTER",
            "DROP",
            "INSERT",
            "UPDATE",
            "DELETE",
        }, trace
        result["read_only_rejection"] = True
    elif mode == "fresh-enroll":
        from phase06_host import bindings

        from shuetl.backend import create_backend_runtime
        from shuetl.settings import ShuETLSettings

        upgrade(engine)
        settings = ShuETLSettings(
            profile="postgresql-preview",
            role="gateway",
            provider="postgresql",
            identity="host",
            database_url=url,
            postgresql_sslmode="disable",
            tenant_id="phase06",
            workspace_id="transition",
            environment="test",
            security_domain="phase06",
            store_id="transition",
            bindings_factory="phase06_host.bindings:create",
        )
        runtime = create_backend_runtime(settings, bindings.create(settings))
        scope = bindings._context(settings)
        try:
            assert (
                runtime.backend.submissions.lookup_idempotency(
                    scope, "retained-uncertain"
                )
                is None
            )
            assert list(runtime.backend.definitions.list(scope)) == []
            definition = json.loads(os.environ["TRANSITION_DEFINITION"])
            runtime.backend.managed_service.register_definition(
                scope, "retained-transfer", definition
            )
            assert list(runtime.backend.definitions.list(scope)) == [
                "retained-transfer"
            ]
            assert (
                runtime.backend.submissions.lookup_idempotency(
                    scope, "retained-uncertain"
                )
                is None
            )
            result.update(
                {
                    "old_acceptance_absent": True,
                    "definitions_reenrolled": ["retained-transfer"],
                    "no_automatic_replay": True,
                    "schema": inspect_postgresql_engine(engine).version,
                }
            )
        finally:
            runtime.close()
    else:
        from etlantic import Data, Extract, Load, Pipeline
        from etlantic.authoring import definition_from_pipeline
        from etlantic.authoring.serialize import pipeline_to_dict

        from shuetl import PostgreSQLProviderBundle, ShuETL, ShuETLSettings

        if mode == "retained-seed":
            upgrade(engine)
        auth = MemoryAuthorizer()
        for action in ("definition.list", "definition.read", "run.read"):
            auth.grant(ctx, action)
        settings = ShuETLSettings(
            profile="postgresql-pilot",
            role="gateway",
            provider="postgresql",
            identity="host",
            database_url=url,
            postgresql_sslmode="disable",
        )
        bundle = PostgreSQLProviderBundle.create(
            settings,
            authorizer=auth,
            context_factory=lambda _p, _r: ctx,
            principal_dependency=lambda: ctx.principal,
        )
        try:
            if mode == "retained-seed":

                class Row(Data):
                    id: str
                    payload: str

                class Transfer(Pipeline):
                    source: Extract[Row] = Extract(asset="source")
                    sink: Load[Row] = Load(input=source.result, asset="sink")

                definition = pipeline_to_dict(definition_from_pipeline(Transfer))
                bundle.definitions.put(ctx, "retained-transfer", definition)
                accepted = bundle.submissions.accept(
                    ctx,
                    idempotency_key="retained-uncertain",
                    payload={
                        "definition_id": "retained-transfer",
                        "transition_fixture": "requires-operator-reconciliation",
                    },
                )
                result["receipt"] = accepted.receipt.to_dict()
                result["definition"] = definition
            else:
                result["receipt"] = bundle.submissions.lookup_idempotency(
                    ctx, "retained-uncertain"
                ).to_dict()
                assert list(bundle.definitions.list(ctx)) == ["retained-transfer"]
            app = ShuETL(api=bundle.api).create_app(prefix="/etl")
            assert "/etl/v1/definitions" in app.openapi()["paths"]
            result["retained_application_mounted"] = True
            result["schema"] = inspect_postgresql_engine(engine).version
        finally:
            bundle.close()
    engine.dispose()
    print(json.dumps(result, default=str))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--child", choices=("retained-seed", "reject-old", "fresh-enroll", "rollback")
    )
    parser.add_argument("--disposable-admin-url")
    parser.add_argument("--retained-python")
    parser.add_argument("--candidate-python")
    parser.add_argument("--source-commit")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.child:
        child(args.child)
        return
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    token = uuid.uuid4().hex[:12]
    databases = {"old": f"phase06_old_{token}", "new": f"phase06_new_{token}"}
    url = make_url(args.disposable_admin_url)
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    evidence = {
        "schema": "shuetl.phase06.transition/1",
        "result": "FAIL",
        "source_commit": args.source_commit,
        "steps": [],
        "limits": (
            "Rehearses store incompatibility, definition re-enrollment "
            "and retained application mounting. The retained acceptance is "
            "a seeded reconciliation case, not proof of an interrupted 0.55 ETL "
            "effect. No production systemd supervisor or traffic switch is exercised."
        ),
    }
    try:
        with admin.connect() as connection:
            for database in databases.values():
                connection.execute(text(f'CREATE DATABASE "{database}"'))
        with tempfile.TemporaryDirectory(prefix="shuetl-transition-") as folder:
            root = Path(folder).resolve()
            (root / "landing").mkdir()
            definition = None
            for mode, python, store in (
                ("retained-seed", args.retained_python, "old"),
                ("reject-old", args.candidate_python, "old"),
                ("fresh-enroll", args.candidate_python, "new"),
                ("rollback", args.retained_python, "old"),
            ):
                env = {
                    key: value
                    for key, value in os.environ.items()
                    if not key.startswith(("SHUETL_", "ETLANTIC_", "PYTHONPATH"))
                }
                env.update(
                    TRANSITION_DATABASE_URL=url.set(
                        database=databases[store]
                    ).render_as_string(hide_password=False),
                    PHASE06_ROOT=str(root),
                )
                if definition:
                    env["TRANSITION_DEFINITION"] = json.dumps(definition)
                run = subprocess.run(
                    [python, "-I", str(Path(__file__).resolve()), "--child", mode],
                    env=env,
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                assert run.returncode == 0, (mode, run.stderr[-3000:])
                observed = json.loads(run.stdout)
                evidence["steps"].append(observed)
                if mode == "retained-seed":
                    definition = observed.pop("definition")
            assert evidence["steps"][0]["receipt"] == evidence["steps"][-1]["receipt"]
            assert evidence["steps"][0]["schema"] == evidence["steps"][-1]["schema"]
            evidence.update(
                result="PASS",
                one_application_authority_at_a_time=True,
                retained_identity_unchanged=True,
            )
    finally:
        with admin.connect() as connection:
            for database in databases.values():
                connection.execute(
                    text(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)')
                )
        admin.dispose()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2) + "\n")


if __name__ == "__main__":
    main()
