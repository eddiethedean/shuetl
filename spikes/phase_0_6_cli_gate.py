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
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


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
            "ETLANTIC_SQL_URL": url,
            "PYTHONNOUSERSITE": "1",
        }
    )
    if worker_kind is not None:
        env["SHUETL_WORKER_KIND"] = worker_kind
    return env


def _probe(port: int, endpoint: str) -> tuple[int, dict[str, Any]]:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disposable-admin-url", required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shuetl-wheel", type=Path, required=True)
    parser.add_argument("--reference-wheel", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args(argv)
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
            root = Path(temp_root)
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
                evidence["roles"].append(
                    {
                        "role": role_name,
                        "pid": process.pid,
                        "ready": ready,
                        "live": live,
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
                assert imports["pid"] == process.pid, imports
                assert imports["role"] == import_role, imports
                should_import_http = role_name == "gateway"
                assert imports["fastapi_imported"] is should_import_http, imports
                assert imports["etlantic_fastapi_imported"] is should_import_http, (
                    imports
                )
                evidence["role_imports"].append(imports)
            evidence["shutdown"] = []
            for role_name, process, probe_port, _log_path in reversed(children):
                process.send_signal(signal.SIGTERM)
                exit_code = process.wait(timeout=15)
                assert exit_code == 0, (role_name, exit_code)
                lifecycle_path = root / f"lifecycle-{process.pid}.jsonl"
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
