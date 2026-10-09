"""Qualify installed PostgreSQL role composition before implementing the CLI.

Requires an explicitly disposable administrator URL and an isolated Python with
built ShuETL/reference wheels installed. Owns only fixtures and subprocesses;
all application behavior goes through published upstream public contracts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import selectors
import subprocess
import tempfile
import uuid
from pathlib import Path

from etlantic_sqlmodel.migrations import upgrade
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


class Role:
    def __init__(self, python, role, env, cwd):
        with (Path(cwd) / f"{role}.stderr").open("w") as log:
            self.process = subprocess.Popen(
                [python, "-I", "-m", "phase06_reference", role],
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log,
                text=True,
                bufsize=1,
            )
        try:
            self.startup = self.read()
            assert self.startup["started"] == role, self.startup
        except BaseException:
            self.process.kill()
            self.process.wait(timeout=10)
            raise

    def read(self):
        assert self.process.stdout is not None
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            assert selector.select(30), "role response exceeded 30 seconds"
        line = self.process.stdout.readline()
        assert line, f"role exited {self.process.poll()}"
        return json.loads(line)

    def call(self, op, **values):
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps({"op": op, **values}) + "\n")
        self.process.stdin.flush()
        response = self.read()
        assert "error" not in response, response
        return response["ok"]

    def close(self):
        if self.process.poll() is None:
            try:
                self.call("close")
                assert self.process.wait(timeout=10) == 0
            finally:
                if self.process.poll() is None:
                    self.process.kill()
                    self.process.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disposable-admin-url", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shuetl-wheel", type=Path, required=True)
    parser.add_argument("--reference-wheel", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    token = uuid.uuid4().hex[:12]
    database, migrator, runtime = [
        f"gate0_{name}_{token}" for name in ("db", "migration", "runtime")
    ]
    migration_password = secrets.token_urlsafe(24)
    runtime_password = secrets.token_urlsafe(24)
    admin = create_engine(args.disposable_admin_url, isolation_level="AUTOCOMMIT")
    roles = []
    evidence = {
        "schema": "shuetl.phase06.gate0/1",
        "result": "FAIL",
        "source_commit": args.source_commit,
        "shuetl_wheel_sha256": hashlib.sha256(
            args.shuetl_wheel.read_bytes()
        ).hexdigest(),
        "reference_wheel_sha256": hashlib.sha256(
            args.reference_wheel.read_bytes()
        ).hexdigest(),
        "roles": [],
    }
    try:
        with admin.connect() as conn:
            server = str(conn.execute(text("SHOW server_version")).scalar_one())
            assert server.split()[0] == "18.6", server
            evidence["postgresql_version"] = server
            for name, password in (
                (migrator, migration_password),
                (runtime, runtime_password),
            ):
                literal = conn.execute(
                    text("SELECT quote_literal(:value)"), {"value": password}
                ).scalar_one()
                conn.execute(
                    text(
                        f'CREATE ROLE "{name}" LOGIN NOSUPERUSER '
                        "NOCREATEDB NOCREATEROLE "
                        f"NOINHERIT PASSWORD {literal}"
                    )
                )
            conn.execute(text(f'CREATE DATABASE "{database}" OWNER "{migrator}"'))
        migration_url = make_url(args.disposable_admin_url).set(
            database=database, username=migrator, password=migration_password
        )
        runtime_url = migration_url.set(username=runtime, password=runtime_password)
        operator = create_engine(migration_url)
        try:
            evidence["schema_head"] = upgrade(operator)
            with operator.begin() as conn:
                conn.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
                conn.execute(text("CREATE SCHEMA sink"))
                conn.execute(
                    text(
                        "CREATE TABLE sink.target (id text NOT NULL, payload text NOT "
                        "NULL)"
                    )
                )
                conn.execute(
                    text(
                        "CREATE TABLE sink.effects (effect_id text PRIMARY KEY, "
                        "intent_fingerprint text NOT NULL, "
                        "publication_id text NOT NULL "
                        "UNIQUE, row_count bigint NOT NULL, "
                        "committed_at timestamptz NOT "
                        "NULL DEFAULT now())"
                    )
                )
                conn.execute(
                    text(f'GRANT CONNECT ON DATABASE "{database}" TO "{runtime}"')
                )
                for schema in ("public", "sink"):
                    conn.execute(text(f'GRANT USAGE ON SCHEMA {schema} TO "{runtime}"'))
                    conn.execute(
                        text(
                            "GRANT SELECT, INSERT, UPDATE, DELETE "
                            "ON ALL TABLES IN SCHEMA "
                            f'{schema} TO "{runtime}"'
                        )
                    )
                    conn.execute(
                        text(
                            "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES "
                            f"IN SCHEMA {schema} "
                            f'TO "{runtime}"'
                        )
                    )
            with operator.connect() as conn:
                grants = conn.execute(
                    text(
                        "SELECT has_schema_privilege(:role, 'public', 'CREATE'), "
                        "has_schema_privilege(:role, 'sink', 'CREATE'), "
                        "pg_has_role(:role, "
                        ":owner, 'MEMBER')"
                    ),
                    {"role": runtime, "owner": migrator},
                ).one()
                assert tuple(grants) == (False, False, False)
                owners = conn.execute(
                    text(
                        "SELECT count(*) FROM pg_class c JOIN pg_roles r ON "
                        "r.oid=c.relowner WHERE r.rolname=:role"
                    ),
                    {"role": runtime},
                ).scalar_one()
                assert owners == 0
                evidence["grants"] = {
                    "schema_create": False,
                    "migration_membership": False,
                    "owned_objects": owners,
                }
            with tempfile.TemporaryDirectory(prefix="shuetl-gate0-") as scratch:
                root = Path(scratch)
                (root / "landing").mkdir()
                content = "id,payload\n001,gate0-value\n"
                (root / "landing/input.csv").write_text(content)
                evidence["input_sha256"] = hashlib.sha256(content.encode()).hexdigest()
                env = {
                    k: v
                    for k, v in os.environ.items()
                    if not k.startswith(("SHUETL_", "ETLANTIC_", "PYTHONPATH"))
                }
                env.update(
                    PHASE06_ROOT=scratch,
                    PHASE06_RUNTIME_URL=runtime_url.render_as_string(
                        hide_password=False
                    ),
                )
                for name in ("gateway", "scheduler", "run-worker", "action-worker"):
                    role_env = dict(env)
                    if name in ("run-worker", "action-worker"):
                        role_env["ETLANTIC_SQL_URL"] = runtime_url.render_as_string(
                            hide_password=False
                        )
                    role = Role(args.python, name, role_env, scratch)
                    roles.append(role)
                    evidence["roles"].append(role.startup)
                gateway, scheduler, worker, action = roles
                assert len({r.startup["pid"] for r in roles}) == 4
                assert all(not r.startup["http_imported"] for r in roles[1:])
                assert not gateway.startup["execution_imported"]
                gateway.call("definition")
                prep = gateway.call(
                    "http",
                    method="POST",
                    path="/v1/definitions/transfer/preparations",
                    body={"payload": {}},
                    headers={"Idempotency-Key": "gate0-manual"},
                )
                assert prep["status"] == 202, prep
                evidence["action_tick"] = action.call("tick")
                operation = gateway.call(
                    "http",
                    method="GET",
                    path="/v1/preparations/" + prep["body"]["operation_id"],
                )
                evidence["manual_preparation"] = operation
                assert operation["body"]["status"] == "succeeded", operation
                evidence["manual_tick"] = worker.call("tick")
                # The preparation result is the upstream accept receipt.
                receipt = operation["body"]["result"]
                manual_run = receipt.get("resource_id") or receipt.get(
                    "receipt", {}
                ).get("resource_id")
                assert manual_run, receipt
                report = gateway.call("report", run_id=manual_run)
                assert report["status"] == "succeeded", report
                evidence["manual_report"] = report
                created = gateway.call(
                    "http",
                    method="POST",
                    path="/v1/definitions/transfer/schedules",
                    body={"spec": {"kind": "interval", "interval_seconds": 60}},
                )
                assert created["status"] == 201, created
                schedule_id = created["body"]["schedule_id"]
                assert (
                    scheduler.call("schedule-get", schedule_id=schedule_id)
                    == created["body"]
                )
                original_revision = created["body"]["revision_id"]
                changed = scheduler.call(
                    "schedule-command",
                    method="amend",
                    schedule_id=schedule_id,
                    revision_id=original_revision,
                )
                assert changed["revision_id"] != original_revision
                conflict = gateway.call(
                    "http",
                    method="POST",
                    path=f"/v1/schedules/{schedule_id}/amend",
                    body={
                        "expected_revision_id": original_revision,
                        "spec": {"kind": "interval", "interval_seconds": 60},
                    },
                )
                assert conflict["status"] == 409
                assert scheduler.call(
                    "schedule-command",
                    method="amend",
                    schedule_id=schedule_id,
                    revision_id=original_revision,
                ) == {"denial_status": 409}
                assert scheduler.call(
                    "schedule-command",
                    method="get",
                    schedule_id=schedule_id,
                    denied=True,
                )["denial_status"] in (403, 404)
                paused = scheduler.call(
                    "schedule-command", method="pause", schedule_id=schedule_id
                )
                assert (
                    gateway.call(
                        "http", method="GET", path=f"/v1/schedules/{schedule_id}"
                    )["body"]
                    == paused
                )
                resumed = gateway.call(
                    "http", method="POST", path=f"/v1/schedules/{schedule_id}/resume"
                )
                assert resumed["body"] == scheduler.call(
                    "schedule-get", schedule_id=schedule_id
                )
                assert gateway.call(
                    "http", method="GET", path="/v1/definitions/transfer/schedules"
                )["body"]["schedules"] == scheduler.call(
                    "schedule-command", method="list"
                )
                assert gateway.call(
                    "http", method="GET", path=f"/v1/schedules/{schedule_id}/preview"
                )["body"] == scheduler.call(
                    "schedule-command", method="preview", schedule_id=schedule_id
                )
                evidence["schedule_parity"] = {
                    "create": True,
                    "amend": True,
                    "conflict": True,
                    "pause": True,
                    "resume": True,
                    "get": True,
                    "list": True,
                    "preview": True,
                    "scope_denial": True,
                }
                evidence["scheduler_tick"] = scheduler.call(
                    "tick", instant="2026-10-09T00:01:00+00:00"
                )
                firings = gateway.call("firings", schedule_id=schedule_id)
                evidence["firings"] = firings
                assert len(firings) == 1 and firings[0]["submission_id"], firings
                evidence["scheduled_tick"] = worker.call("tick")
                # Resolve the run through the public firing receipt.
                firing_http = gateway.call(
                    "http", method="GET", path=f"/v1/schedules/{schedule_id}/firings"
                )
                evidence["http_firings"] = firing_http
                evidence["scheduled_submission_id"] = firings[0]["submission_id"]
                scheduled_run = gateway.call(
                    "submission", submission_id=firings[0]["submission_id"]
                )["run_id"]
                scheduled_report = gateway.call("report", run_id=scheduled_run)
                assert scheduled_report["status"] == "succeeded", scheduled_report
                evidence["scheduled_report"] = scheduled_report
                assert firing_http["body"]["firings"] == firings
                first = scheduler.call(
                    "schedule-command",
                    method="trigger",
                    schedule_id=schedule_id,
                    instant="2026-10-09T00:02:00+00:00",
                )
                duplicate = gateway.call(
                    "http",
                    method="POST",
                    path=f"/v1/schedules/{schedule_id}/trigger",
                    body={"nominal_fire_time": "2026-10-09T00:02:00+00:00"},
                )
                assert (
                    duplicate["status"] == 200
                    and duplicate["body"]["firing_id"] == first["firing_id"]
                )
                assert duplicate["body"]["submission_id"] == first["submission_id"]
                evidence["schedule_parity"].update(
                    trigger=True, duplicate_trigger=True, firings=True
                )
                assert worker.call("tick")["count"] == 1
                with operator.connect() as conn:
                    rows = [
                        list(row)
                        for row in conn.execute(
                            text("SELECT id,payload FROM sink.target ORDER BY id")
                        )
                    ]
                    effects = [
                        list(row)
                        for row in conn.execute(
                            text(
                                "SELECT effect_id,publication_id,row_count "
                                "FROM sink.effects ORDER "
                                "BY effect_id"
                            )
                        )
                    ]
                assert rows == [["001", "gate0-value"]] * 3, rows
                assert len(effects) == 3 and all(row[2] == 1 for row in effects), (
                    effects
                )
                evidence["sink_rows"] = rows
                evidence["sink_effects"] = effects
                for role in reversed(roles):
                    role.close()
                evidence["result"] = "PASS"
        finally:
            operator.dispose()
    finally:
        for role in reversed(roles):
            role.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
        )
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)'))
            for name in (runtime, migrator):
                conn.execute(text(f'DROP ROLE IF EXISTS "{name}"'))
        admin.dispose()
    print(f"Gate 0 {evidence['result']}: {args.output}")


if __name__ == "__main__":
    main()
