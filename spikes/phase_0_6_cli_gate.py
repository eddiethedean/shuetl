"""Exercise the installed ShuETL role CLI against disposable PostgreSQL 18.6.

Build/install ShuETL and the reference host outside the checkout first. The
administrator URL must point to a disposable server; this program creates and
drops only uniquely named databases and roles of its own.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

CONTAINER_PROBES: dict[int, str] = {}


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _settings_env(
    *,
    role: str,
    url: str,
    factory: str,
    root: Path,
    probe_port: int,
    worker_kind: str | None = None,
) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("SHUETL_", "ETLANTIC_", "PYTHONPATH"))
    }
    env.update(
        {
            "SHUETL_PROFILE": "postgresql-preview",
            "SHUETL_ROLE": role,
            "SHUETL_PROVIDER": "postgresql",
            "SHUETL_IDENTITY": "host",
            "SHUETL_DATABASE_URL": url,
            "SHUETL_POSTGRESQL_SSLMODE": "disable",
            "SHUETL_BINDINGS_FACTORY": factory,
            "SHUETL_TENANT_ID": "phase06",
            "SHUETL_WORKSPACE_ID": "cli-qualification",
            "SHUETL_ENVIRONMENT": "test",
            "SHUETL_SECURITY_DOMAIN": "phase06",
            "SHUETL_STORE_ID": "phase06-cli",
            "SHUETL_PROBE_PORT": str(probe_port),
            "SHUETL_SHUTDOWN_GRACE_SECONDS": "5",
            "SHUETL_DISPATCH_INTERVAL_SECONDS": "0.2",
            "PHASE06_ROOT": str(root),
            "PYTHONNOUSERSITE": "1",
        }
    )
    if worker_kind is not None:
        env["SHUETL_WORKER_KIND"] = worker_kind
        env["ETLANTIC_SQL_URL"] = url
    return env


def _probe(port: int, endpoint: str) -> tuple[int, dict[str, Any]]:
    if port in CONTAINER_PROBES:
        code = (
            "import json,urllib.request,urllib.error; "
            f"url='http://127.0.0.1:{port}/{endpoint}'\n"
            "try: response=urllib.request.urlopen(url,timeout=1)\n"
            "except urllib.error.HTTPError as error: response=error\n"
            "print(json.dumps([response.code,json.loads(response.read())]))"
        )
        result = subprocess.run(
            ["docker", "exec", CONTAINER_PROBES[port], "python", "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode:
            raise OSError("container probe unavailable")
        status, payload = json.loads(result.stdout)
        return status, payload
    request = urllib.request.Request(f"http://127.0.0.1:{port}/{endpoint}")
    try:
        with urllib.request.urlopen(request, timeout=1) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as response:
        return response.code, json.loads(response.read())


def _wait_ready(
    process: subprocess.Popen[str],
    port: int,
    log_path: Path,
    redactions: tuple[str, ...],
) -> dict[str, Any]:
    deadline = time.monotonic() + 40
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        if process.poll() is not None:
            log_tail = "\n".join(
                log_path.read_text(encoding="utf-8", errors="replace").splitlines()[
                    -20:
                ]
            )
            for secret in redactions:
                log_tail = log_tail.replace(secret, "<redacted>")
            raise RuntimeError(
                f"role process exited during startup: {process.returncode}; "
                f"redacted log tail: {log_tail}"
            )
        try:
            status, last = _probe(port, "ready")
            if status == 200 and last.get("ready") is True:
                return last
        except (OSError, TimeoutError, ValueError):
            pass
        time.sleep(0.1)
    raise TimeoutError(f"role did not become ready; observed state={last}")


def _run_migrations(python: str, env: dict[str, str], work: Path) -> None:
    result = subprocess.run(
        [python, "-m", "shuetl.cli", "database", "upgrade"],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError("explicit provider migration command failed")


def _assert_runtime_grants(engine: Any, runtime: str, migrator: str) -> dict[str, Any]:
    with engine.connect() as connection:
        grants = connection.execute(
            text(
                "SELECT has_schema_privilege(:role, 'public', 'CREATE'), "
                "has_schema_privilege(:role, 'sink', 'CREATE'), "
                "pg_has_role(:role, :owner, 'MEMBER')"
            ),
            {"role": runtime, "owner": migrator},
        ).one()
        owners = connection.execute(
            text(
                "SELECT count(*) FROM pg_class c JOIN pg_roles r "
                "ON r.oid = c.relowner WHERE r.rolname = :role"
            ),
            {"role": runtime},
        ).scalar_one()
    assert tuple(grants) == (False, False, False), tuple(grants)
    assert owners == 0, owners
    return {
        "public_schema_create": bool(grants[0]),
        "sink_schema_create": bool(grants[1]),
        "migration_role_membership": bool(grants[2]),
        "owned_objects": owners,
    }


def _active_drain(
    *,
    root,
    children,
    settings,
    host_module,
    evidence,
    operator,
    execution_url,
    python,
    gateway_port,
    force,
):
    """Exercise actual CLI dispatch with public provider barriers in a test wheel."""
    from phase06_host.workload import specification

    from shuetl.backend import create_backend_runtime

    controller = create_backend_runtime(settings, host_module.create(settings))
    backend = controller.backend
    ctx = host_module._context(settings)
    service = backend.managed_service
    try:
        service.register_definition(ctx, "cli-transfer", specification())
        _action_checks(root=root, backend=backend, ctx=ctx, evidence=evidence)
        for role in ("scheduler", "worker-actions", "worker-runs"):
            (root / f"arm-{role}").touch()
        first = service.start_run_preparation(
            ctx, "cli-transfer", idempotency_key="cli-drain-first"
        )
        second = service.start_run_preparation(
            ctx, "cli-transfer", idempotency_key="cli-drain-second"
        )
        records = evidence.setdefault("active_drain", [])
        gateway_probe = next(row[2] for row in children if row[0] == "gateway")
        request_code = (
            "import json,urllib.request; "
            f"response=urllib.request.urlopen('http://127.0.0.1:{gateway_port}"
            "/qualification/active-request',timeout=80); "
            "print(json.dumps({'status':response.status,'body':json.loads(response.read())}))"
        )
        request_command = (
            [
                "docker",
                "exec",
                CONTAINER_PROBES[gateway_probe],
                "python",
                "-c",
                request_code,
            ]
            if gateway_probe in CONTAINER_PROBES
            else [python, "-c", request_code]
        )
        request_pool = ThreadPoolExecutor(max_workers=1)
        request_future = request_pool.submit(
            subprocess.run, request_command, capture_output=True, text=True, timeout=85
        )
        for name, host_role in (
            ("scheduler", "scheduler"),
            ("action_worker", "worker-actions"),
            ("run_worker", "worker-runs"),
            ("gateway", "gateway"),
        ):
            _, process, port, _ = next(row for row in children if row[0] == name)
            reached = root / f"reached-{host_role}"
            deadline = time.monotonic() + 40
            while not reached.exists():
                assert process.poll() is None, name
                assert time.monotonic() < deadline, (
                    f"{name} did not reach public barrier"
                )
                time.sleep(0.05)
            process.send_signal(signal.SIGTERM)
            process.send_signal(signal.SIGINT)
            deadline = time.monotonic() + 10
            while True:
                status, readiness = _probe(port, "ready")
                if status == 503 and readiness.get("reason_code") == "grace_expired":
                    break
                assert time.monotonic() < deadline, readiness
                time.sleep(0.05)
            live_status, live = _probe(port, "live")
            assert live_status == 200 and live["live"] is True
            assert process.poll() is None
            lifecycle = root / (
                f"lifecycle-{name}-1.jsonl"
                if port in CONTAINER_PROBES
                else f"lifecycle-{process.pid}.jsonl"
            )
            assert not lifecycle.exists(), "cleanup beneath active provider call"
            (root / f"release-{host_role}").touch()
            assert process.wait(timeout=30) == 0
            records.append(
                {
                    "role": name,
                    "boundary": reached.read_text(),
                    "signals": ["SIGTERM", "SIGINT"],
                    "ready_after_grace": readiness,
                    "live_after_grace": live,
                    "cleanup_before_release": False,
                    "exit_code": 0,
                }
            )
        request_result = request_future.result(timeout=10)
        request_pool.shutdown(wait=True)
        assert request_result.returncode == 0, request_result.stderr
        response = json.loads(request_result.stdout)
        assert response == {"status": 200, "body": {"completed": True}}, response
        evidence["gateway_active_request"] = response
        first_result = service.get_run_preparation(ctx, first["operation_id"])
        second_result = service.get_run_preparation(ctx, second["operation_id"])
        assert first_result["status"] == "succeeded", first_result
        assert second_result["status"] == "queued", second_result
        report = service.get_run_report(ctx, first_result["result"]["resource_id"])
        assert report["status"] == "succeeded", report
        with operator.connect() as connection:
            rows = [
                list(row)
                for row in connection.execute(
                    text("SELECT id,payload FROM sink.target ORDER BY id")
                )
            ]
            effects = connection.execute(
                text("SELECT count(*) FROM sink.effects")
            ).scalar_one()
        assert rows == [["001", "phase06-cli"]] and effects == 1, (rows, effects)
        # Replacement roles recover queued work through canonical factories.
        action = backend.create_action_execution_host(
            worker_id="cli-replacement-actions"
        )
        run = backend.create_execution_host(owner_id="cli-replacement-runs")
        assert action.tick(ctx) == 1
        previous_url = os.environ.get("ETLANTIC_SQL_URL")
        os.environ["ETLANTIC_SQL_URL"] = execution_url
        try:
            assert run.tick(ctx) == 1
        finally:
            if previous_url is None:
                os.environ.pop("ETLANTIC_SQL_URL", None)
            else:
                os.environ["ETLANTIC_SQL_URL"] = previous_url
        action.request_drain()
        run.request_drain()
        assert action.tick(ctx) == run.tick(ctx) == 0
        recovered = service.get_run_preparation(ctx, second["operation_id"])
        assert recovered["status"] == "succeeded"
        assert (
            service.get_run_report(ctx, recovered["result"]["resource_id"])["status"]
            == "succeeded"
        )
        evidence["active_execution"] = {
            "first": first_result,
            "queued_at_shutdown": second_result,
            "replacement": recovered,
            "rows_before_replacement": rows,
            "effects_before_replacement": effects,
            "result": "PASS",
        }
        if force:
            _force_roles(
                root=root,
                settings=settings,
                backend=backend,
                ctx=ctx,
                python=python,
                execution_url=execution_url,
                evidence=evidence,
            )
    finally:
        controller.close()


def _action_checks(*, root, backend, ctx, evidence):
    """Published SQL handlers execute in the installed CLI action worker."""
    from dataclasses import replace

    from etlantic.control_plane import ControlPlaneError, Principal

    service = backend.managed_service
    records = evidence.setdefault("connector_actions", [])

    def execute(key, action, request, expected="succeeded", deadline_seconds=10):
        job = service.submit_connector_action(
            ctx, action, request, idempotency_key=key, deadline_seconds=deadline_seconds
        )
        deadline = time.monotonic() + 20
        while True:
            result = service.get_connector_action(ctx, job["action_id"])
            if result["status"] in {"succeeded", "failed", "timed_out", "cancelled"}:
                break
            assert time.monotonic() < deadline, result
            time.sleep(0.05)
        assert result["status"] == expected, result
        records.append({"case": key, "receipt": result, "result": "PASS"})
        return job, result

    request = {"provider": "postgresql", "connection_id": "saved-connection"}
    job, connection = execute("cli-connection-test", "connector.test", request)
    assert connection["result"]["ok"] is True
    _, schema = execute(
        "cli-schema-inspect", "connector.schema.inspect", {**request, "max_fields": 2}
    )
    assert len(schema["result"]["fields"]) == 2 and schema["result"]["has_more"] is True
    foreign = replace(
        ctx,
        principal=Principal("foreign", issuer="reference-host", kind="service"),
        resource_owner_id="foreign",
    )
    try:
        service.get_connector_action(foreign, job["action_id"])
    except ControlPlaneError as exc:
        assert exc.status in {403, 404}
    else:
        raise AssertionError("another action owner read the receipt")
    (root / "connection-version").write_text("2")
    execute("cli-resource-rotation", "connector.test", request)
    (root / "revoke-connection").touch()
    try:
        execute("cli-resource-revocation", "connector.test", request, "failed")
    finally:
        (root / "revoke-connection").unlink()
    execute(
        "cli-resource-deadline",
        "connector.test",
        {**request, "connection_id": "slow-connection"},
        "timed_out",
        deadline_seconds=2,
    )
    (root / "unavailable-port").write_text(str(_free_port()))
    execute(
        "cli-connector-outage",
        "connector.test",
        {**request, "connection_id": "unavailable-connection"},
        "failed",
    )
    execute("cli-resource-recovery", "connector.test", request)
    _, preflight = execute(
        "cli-static-preflight", "connector.preflight", {"definition_id": "cli-transfer"}
    )
    assert preflight["result"]["metadata"]["mode"] == "read_only_plan"
    evidence["action_limits"] = (
        "Published worker-isolated connection/schema actions; test host rotates "
        "a resource version and rejects revoked references. Preflight is explicitly "
        "static; live pipeline readiness remains ETLantic #121."
    )


def _force_roles(*, root, settings, backend, ctx, python, execution_url, evidence):
    """An external supervisor kills blocked native CLI processes after grace."""
    from dataclasses import asdict

    records = evidence.setdefault("forced_termination", [])
    for role, kind, host_role in (
        ("scheduler", None, "scheduler"),
        ("worker", "actions", "worker-actions"),
        ("worker", "runs", "worker-runs"),
    ):
        for prefix in ("arm", "reached", "release"):
            (root / f"{prefix}-{host_role}").unlink(missing_ok=True)
        port = _free_port()
        env = _settings_env(
            role=role,
            url=execution_url,
            factory="phase06_host.bindings:create",
            root=root,
            probe_port=port,
            worker_kind=kind,
        )
        path = root / f"force-{host_role}.log"
        with path.open("w") as log:
            command = [python, "-m", "shuetl.cli", "serve", "--role", role]
            if kind:
                command.extend(("--kind", kind))
            process = subprocess.Popen(
                command,
                env=env,
                cwd=root,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
            try:
                _wait_ready(process, port, path, (execution_url,))
                (root / f"arm-{host_role}").touch()
                operation = None
                if kind:
                    operation = backend.managed_service.start_run_preparation(
                        ctx,
                        "cli-transfer",
                        idempotency_key="cli-force-" + kind,
                        deadline_seconds=10,
                    )
                if kind == "runs":
                    action = backend.create_action_execution_host(
                        worker_id="force-prepare-runs"
                    )
                    assert action.tick(ctx) == 1
                    action.request_drain()
                    operation = backend.managed_service.get_run_preparation(
                        ctx, operation["operation_id"]
                    )
                    assert operation["status"] == "succeeded"
                deadline = time.monotonic() + 45
                while not (root / f"reached-{host_role}").exists():
                    assert time.monotonic() < deadline, host_role
                    assert process.poll() is None
                    time.sleep(0.05)

                def snapshot(kind=kind, operation=operation):
                    if kind == "runs":
                        return asdict(
                            backend.durable_work.get_submission(
                                ctx, operation["result"]["submission_id"]
                            )
                        )
                    if kind == "actions":
                        return asdict(
                            backend.durable_work.get_action_job(
                                ctx, operation["operation_id"]
                            )
                        )
                    return None

                before = snapshot()
                process.send_signal(signal.SIGTERM)
                deadline = time.monotonic() + 10
                while True:
                    status, readiness = _probe(port, "ready")
                    if (
                        status == 503
                        and readiness.get("reason_code") == "grace_expired"
                    ):
                        break
                    assert time.monotonic() < deadline, readiness
                    time.sleep(0.05)
                lifecycle = root / f"lifecycle-{process.pid}.jsonl"
                assert not lifecycle.exists()
                process.kill()
                assert process.wait(timeout=10) == -signal.SIGKILL
                assert not lifecycle.exists()
                after = snapshot()
                assert before == after, (before, after)
                records.append(
                    {
                        "role": host_role,
                        "pid": process.pid,
                        "signals": ["SIGTERM", "SIGKILL"],
                        "ready_after_grace": readiness,
                        "before": before,
                        "after": after,
                        "cleanup_events": [],
                        "result": "PASS",
                    }
                )
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)
    evidence["force_limits"] = (
        "Native CLI processes killed after committed claims. Published "
        "lease/deadline recovery is qualified separately by the installed "
        "fault matrix; SIGKILL cannot run cleanup."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disposable-admin-url", required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shuetl-wheel", type=Path, required=True)
    parser.add_argument("--reference-wheel", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument(
        "--active",
        action="store_true",
        help="Qualify in-flight role drain and real effects",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Also kill active native CLI processes after grace",
    )
    parser.add_argument(
        "--container-image",
        help="Exact local Docker image ID for the same candidate wheels",
    )
    args = parser.parse_args(argv)
    if args.force and (not args.active or args.container_image):
        parser.error("force requires active qualification in native processes")
    if args.container_image is not None and (
        not args.container_image.startswith("sha256:")
        or len(args.container_image) != 71
    ):
        parser.error("container-image must be an exact sha256 Docker image ID")
    import importlib.metadata as metadata

    if metadata.version("shuetl") != "0.6.0":
        raise RuntimeError("the selected interpreter must have the 0.6.0 wheel")
    host_module = __import__("phase06_host.bindings", fromlist=["create"])
    host_path = Path(host_module.__file__).resolve()
    if "site-packages" not in str(host_path):
        raise RuntimeError("the reference host must be installed outside the checkout")
    shuetl_module = __import__("shuetl")
    shuetl_path = Path(shuetl_module.__file__).resolve()
    if "site-packages" not in str(shuetl_path):
        raise RuntimeError("the qualification must exercise the installed ShuETL wheel")

    token = uuid.uuid4().hex[:12]
    database = f"phase06_cli_{token}"
    migrator = f"phase06_mig_{token}"
    runtime = f"phase06_run_{token}"
    migration_password = secrets.token_urlsafe(24)
    runtime_password = secrets.token_urlsafe(24)
    admin_url = make_url(args.disposable_admin_url)
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    children: list[tuple[str, subprocess.Popen[str], int, Path]] = []
    evidence: dict[str, Any] = {
        "schema": "shuetl.phase06.cli-gate/1",
        "result": "FAIL",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "shuetl_version": metadata.version("shuetl"),
        "shuetl_origin": str(shuetl_path),
        "reference_host_origin": str(host_path),
        "etlantic_sql_version": metadata.version("etlantic-sql"),
        "etlantic_version": metadata.version("etlantic"),
        "etlantic_sqlmodel_version": metadata.version("etlantic-sqlmodel"),
        "source_commit": args.source_commit,
        "shuetl_wheel_sha256": hashlib.sha256(
            args.shuetl_wheel.read_bytes()
        ).hexdigest(),
        "reference_wheel_sha256": hashlib.sha256(
            args.reference_wheel.read_bytes()
        ).hexdigest(),
        "roles": [],
    }
    cleanup_errors: list[str] = []
    try:
        with admin.connect() as connection:
            server = str(connection.execute(text("SHOW server_version")).scalar_one())
            assert server.split()[0] == "18.6", server
            evidence["postgresql_version"] = server
            for name, password in (
                (migrator, migration_password),
                (runtime, runtime_password),
            ):
                literal = connection.execute(
                    text("SELECT quote_literal(:value)"), {"value": password}
                ).scalar_one()
                connection.execute(
                    text(
                        f'CREATE ROLE "{name}" LOGIN NOSUPERUSER NOCREATEDB '
                        f"NOCREATEROLE NOINHERIT PASSWORD {literal}"
                    )
                )
            connection.execute(text(f'CREATE DATABASE "{database}" OWNER "{migrator}"'))

        migration_url = admin_url.set(
            database=database, username=migrator, password=migration_password
        )
        runtime_url = migration_url.set(username=runtime, password=runtime_password)
        migration_dsn = migration_url.render_as_string(hide_password=False)
        runtime_dsn = runtime_url.render_as_string(hide_password=False)
        operator = create_engine(migration_url)
        try:
            with operator.begin() as connection:
                connection.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
                connection.execute(text("CREATE SCHEMA sink"))
                connection.execute(
                    text(
                        "CREATE TABLE sink.target (id text NOT NULL, "
                        "payload text NOT NULL)"
                    )
                )
                connection.execute(
                    text(
                        "CREATE TABLE sink.effects (effect_id text PRIMARY KEY, "
                        "intent_fingerprint text NOT NULL, publication_id text "
                        "NOT NULL UNIQUE, row_count bigint NOT NULL, "
                        "committed_at timestamptz NOT NULL DEFAULT now())"
                    )
                )
                for schema in ("public", "sink"):
                    connection.execute(
                        text(f'GRANT USAGE ON SCHEMA {schema} TO "{runtime}"')
                    )
                    connection.execute(
                        text(
                            f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES "
                            f'IN SCHEMA {schema} TO "{runtime}"'
                        )
                    )
                    connection.execute(
                        text(
                            f"GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN "
                            f'SCHEMA {schema} TO "{runtime}"'
                        )
                    )
        finally:
            operator.dispose()

        evidence["runtime_grants"] = _assert_runtime_grants(
            operator := create_engine(migration_url), runtime, migrator
        )
        operator.dispose()

        with tempfile.TemporaryDirectory(prefix="shuetl-phase06-cli-") as temp_root:
            root = Path(temp_root).resolve()
            if args.container_image:
                root.chmod(0o777)  # Disposable fixture shared with container UID 10001.
                evidence["schema"] = "shuetl.phase06.container/1"
                evidence["container_image_id"] = args.container_image
                evidence["platform"] = "linux/amd64"
            (root / "landing").mkdir()
            (root / "landing" / "input.csv").write_text(
                "id,payload\n001,phase06-cli\n", encoding="utf-8"
            )
            factory_path = "phase06_host.bindings:create"
            from shuetl.backend import create_backend_runtime
            from shuetl.settings import ShuETLSettings

            preflight_settings = ShuETLSettings(
                profile="postgresql-preview",
                role="gateway",
                provider="postgresql",
                identity="host",
                database_url=runtime_dsn,
                bindings_factory=factory_path,
                tenant_id="phase06",
                workspace_id="cli-qualification",
                environment="test",
                security_domain="phase06",
                store_id="phase06-cli",
                postgresql_sslmode="disable",
            )
            os.environ["PHASE06_ROOT"] = str(root)
            migration_env = _settings_env(
                role="gateway",
                url=migration_dsn,
                factory=factory_path,
                root=root,
                probe_port=_free_port(),
            )
            migration_env["SHUETL_PROFILE"] = "postgresql-pilot"
            migration_env.pop("SHUETL_BINDINGS_FACTORY", None)
            for scope_field in (
                "SHUETL_TENANT_ID",
                "SHUETL_WORKSPACE_ID",
                "SHUETL_ENVIRONMENT",
                "SHUETL_SECURITY_DOMAIN",
            ):
                migration_env.pop(scope_field, None)
            _run_migrations(args.python, migration_env, root)

            # Provider migration objects do not exist when the initial target
            # schema grants are applied. Grant the runtime role its explicit
            # DML surface after migrations, without granting schema ownership.
            migration_operator = create_engine(migration_url)
            try:
                with migration_operator.begin() as connection:
                    connection.execute(
                        text(
                            f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES "
                            f'IN SCHEMA public TO "{runtime}"'
                        )
                    )
                    connection.execute(
                        text(
                            f"GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN "
                            f'SCHEMA public TO "{runtime}"'
                        )
                    )
            finally:
                migration_operator.dispose()

            try:
                preflight = create_backend_runtime(
                    preflight_settings, host_module.create(preflight_settings)
                )
                preflight.close()
                evidence["construction_preflight"] = "PASS"
            except Exception as exc:
                safe_message = str(exc)
                for secret in (
                    migration_dsn,
                    runtime_dsn,
                    migration_password,
                    runtime_password,
                ):
                    safe_message = safe_message.replace(secret, "<redacted>")
                evidence["construction_preflight"] = (
                    f"{type(exc).__name__}: {safe_message}"
                )
                raise

            gateway_port = _free_port()
            roles_to_start = (
                ("gateway", "gateway", None),
                ("scheduler", "scheduler", None),
                ("run_worker", "worker", "runs"),
                ("action_worker", "worker", "actions"),
            )
            for role_name, cli_role, kind in roles_to_start:
                probe_port = _free_port()
                env = _settings_env(
                    role=cli_role,
                    url=runtime_dsn,
                    factory=factory_path,
                    root=root,
                    probe_port=probe_port,
                    worker_kind=kind,
                )
                command = [
                    args.python,
                    "-m",
                    "shuetl.cli",
                    "serve",
                    "--role",
                    cli_role,
                    "--factory",
                    factory_path,
                ]
                if kind is not None:
                    command.extend(("--kind", kind))
                if cli_role == "gateway":
                    env["SHUETL_PROBE_PORT"] = str(_free_port())
                    probe_port = int(env["SHUETL_PROBE_PORT"])
                    command.extend(("--host", "127.0.0.1", "--port", str(gateway_port)))
                if args.container_image:
                    container_name = f"shuetl-qualification-{token}-{role_name}"
                    CONTAINER_PROBES[probe_port] = container_name
                    container_env = {
                        key: value
                        for key, value in env.items()
                        if key.startswith(("SHUETL_", "ETLANTIC_", "PHASE06_"))
                    }
                    container_env.update(
                        SHUETL_DATABASE_URL=runtime_url.set(
                            host="host.docker.internal"
                        ).render_as_string(hide_password=False),
                        PHASE06_ROOT="/qualification",
                        PHASE06_PROCESS_TOKEN=role_name,
                    )
                    if kind is not None:
                        container_env["ETLANTIC_SQL_URL"] = runtime_url.set(
                            host="host.docker.internal"
                        ).render_as_string(hide_password=False)
                    env_path = root / f"{role_name}.env"
                    env_path.write_text(
                        "".join(
                            f"{key}={value}\n" for key, value in container_env.items()
                        ),
                        encoding="utf-8",
                    )
                    env_path.chmod(0o600)
                    command = [
                        "docker",
                        "run",
                        "--rm",
                        "--name",
                        container_name,
                        "--platform",
                        "linux/amd64",
                        "--env-file",
                        str(env_path),
                        "--volume",
                        f"{root}:/qualification",
                        args.container_image,
                        *command[3:],
                    ]
                    if sys.platform.startswith("linux"):
                        command[2:2] = [
                            "--add-host",
                            "host.docker.internal:host-gateway",
                        ]
                log_path = root / f"{role_name}.log"
                log = log_path.open("w", encoding="utf-8")
                process = subprocess.Popen(
                    command,
                    cwd=root,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                children.append((role_name, process, probe_port, log_path))
                ready = _wait_ready(
                    process,
                    probe_port,
                    log_path,
                    (migration_dsn, runtime_dsn, migration_password, runtime_password),
                )
                live_status, live = _probe(probe_port, "live")
                assert live_status == 200 and live.get("live") is True, live
                container_metadata = None
                if args.container_image:
                    result = subprocess.run(
                        [
                            "docker",
                            "exec",
                            container_name,
                            "python",
                            "-c",
                            "import json,sys,pathlib,importlib.metadata as m; "
                            "print(json.dumps({'python':sys.version.split()[0],"
                            "'versions':{n:m.version(n) for n in ('shuetl','etlantic',"
                            "'etlantic-fastapi','etlantic-sqlmodel','etlantic-sql')},"
                            "'wheels':json.loads(pathlib.Path('/usr/local/share/shuetl-wheels.json').read_text())}))",
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=10,
                    )
                    container_metadata = json.loads(result.stdout)
                    assert (
                        container_metadata["wheels"][args.shuetl_wheel.name]
                        == evidence["shuetl_wheel_sha256"]
                    )
                    assert (
                        container_metadata["wheels"][args.reference_wheel.name]
                        == evidence["reference_wheel_sha256"]
                    )
                    assert container_metadata["versions"] == {
                        "shuetl": "0.6.0",
                        "etlantic": "0.57.2",
                        "etlantic-fastapi": "0.57.2",
                        "etlantic-sqlmodel": "0.57.2",
                        "etlantic-sql": "0.57.2",
                    }
                evidence["roles"].append(
                    {
                        "role": role_name,
                        "pid": process.pid,
                        "ready": ready,
                        "live": live,
                        **(
                            {"container_metadata": container_metadata}
                            if container_metadata
                            else {}
                        ),
                        "probe_host": "127.0.0.1",
                        "gateway_port": (
                            gateway_port if role_name == "gateway" else None
                        ),
                    }
                )

            assert len({row["pid"] for row in evidence["roles"]}) == 4
            evidence["role_imports"] = []
            expected_import_roles = {
                "gateway": "gateway",
                "scheduler": "scheduler",
                "run_worker": "worker-runs",
                "action_worker": "worker-actions",
            }
            for role_name, process, _port, _log_path in children:
                import_role = expected_import_roles[role_name]
                import_path = root / f"imports-{import_role}.json"
                imports = json.loads(import_path.read_text(encoding="utf-8"))
                assert imports["pid"] == (1 if args.container_image else process.pid), (
                    imports
                )
                if args.container_image:
                    imports["container_name"] = CONTAINER_PROBES[_port]
                assert imports["role"] == import_role, imports
                should_import_http = role_name == "gateway"
                assert imports["fastapi_imported"] is should_import_http, imports
                assert imports["etlantic_fastapi_imported"] is should_import_http, (
                    imports
                )
                evidence["role_imports"].append(imports)
            if args.active:
                operator = create_engine(migration_url)
                try:
                    _active_drain(
                        root=root,
                        children=children,
                        settings=preflight_settings,
                        host_module=host_module,
                        evidence=evidence,
                        operator=operator,
                        execution_url=runtime_dsn,
                        python=args.python,
                        gateway_port=gateway_port,
                        force=args.force,
                    )
                finally:
                    operator.dispose()
            evidence["shutdown"] = []
            for role_name, process, probe_port, _log_path in reversed(children):
                if process.poll() is None:
                    process.send_signal(signal.SIGTERM)
                exit_code = process.wait(timeout=15)
                assert exit_code == 0, (role_name, exit_code)
                lifecycle_path = root / (
                    f"lifecycle-{role_name}-1.jsonl"
                    if args.container_image
                    else f"lifecycle-{process.pid}.jsonl"
                )
                lifecycle_events = [
                    json.loads(line)["event"]
                    for line in lifecycle_path.read_text(encoding="utf-8").splitlines()
                ]
                assert lifecycle_events == [
                    "backend.engine_disposed",
                    "bindings.close",
                ], (role_name, lifecycle_events)
                evidence["shutdown"].append(
                    {
                        "role": role_name,
                        "signal": "SIGTERM",
                        "exit_code": exit_code,
                        "cleanup_events": lifecycle_events,
                    }
                )
                if role_name == "action_worker" and args.active:
                    resource_token = (
                        role_name if args.container_image else str(process.pid)
                    )
                    calls = [
                        json.loads(line)
                        for line in (root / f"resource-calls-{resource_token}.jsonl")
                        .read_text()
                        .splitlines()
                    ]
                    cleanup = json.loads(
                        (root / f"resource-cleanup-{resource_token}.json").read_text()
                    )
                    assert {call["version"] for call in calls} == {
                        "1",
                        "2",
                        "unavailable",
                    }
                    assert all(
                        call["pid"] == (1 if args.container_image else process.pid)
                        and call["authority_matches"] is True
                        and 0 < call["timeout_seconds"] <= 10
                        for call in calls
                    )
                    assert cleanup == {"engines_disposed": 3}, cleanup
                    evidence["resource_bridge"] = {
                        "calls": calls,
                        "cleanup": cleanup,
                        "worker_only": True,
                    }
                try:
                    status, payload = _probe(probe_port, "live")
                    assert status == 503 and payload.get("live") is False
                except OSError:
                    pass
            children.clear()

            logs = "\n".join(
                path.read_text(encoding="utf-8") for path in root.glob("*.log")
            )
            assert migration_password not in logs
            assert runtime_password not in logs
            evidence["credential_sentinels_absent"] = True
            evidence["result"] = "PASS"

    finally:
        for role_name, process, _port, _log_path in children:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                    cleanup_errors.append(f"force-terminated {role_name}")
        for container_name in CONTAINER_PROBES.values():
            subprocess.run(
                ["docker", "rm", "--force", container_name],
                capture_output=True,
                timeout=15,
            )
        CONTAINER_PROBES.clear()
        with admin.connect() as connection:
            connection.execute(
                text(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)')
            )
            connection.execute(text(f'DROP ROLE IF EXISTS "{runtime}"'))
            connection.execute(text(f'DROP ROLE IF EXISTS "{migrator}"'))
        admin.dispose()
        evidence["cleanup_errors"] = cleanup_errors
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return 0 if evidence["result"] == "PASS" and not cleanup_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
