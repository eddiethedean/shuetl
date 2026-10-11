"""Live no-write, failed-work retry, fresh rerun and lineage qualification."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from sqlalchemy import text


def qualify(
    *, gateway, action, worker, replica, operator, schedule_id, runtime_role, evidence
):
    gateway.call("schedule-command", method="pause", schedule_id=schedule_id)
    cases = evidence.setdefault("cases", [])

    def effects():
        with operator.connect() as connection:
            return connection.execute(
                text("SELECT count(*) FROM sink.effects")
            ).scalar_one()

    def execute(key, **request):
        operation = gateway.call("preparation", key=key, request=request)
        assert action.call("tick")["count"] == 1
        prepared = gateway.call(
            "preparation-get", operation_id=operation["operation_id"]
        )
        assert prepared["status"] == "succeeded", prepared
        receipt = prepared["result"]
        assert worker.call("tick")["count"] == 1
        report = gateway.call("report", run_id=receipt["resource_id"])
        return receipt, report

    def command(method, run_id, expected=200, **arguments):
        result = gateway.call(
            "run-command", method=method, run_id=run_id, arguments=arguments
        )
        assert result["status"] == expected, result
        return result.get("value", result)

    before = effects()
    receipt, report = execute(
        "controls-no-write",
        no_write=True,
        materialization="durable",
        retry={"max_attempts": 3},
        timeout={"run_seconds": 15, "step_seconds": 5},
        explicit_settings=[
            "retry.max_attempts",
            "timeout.run_seconds",
            "timeout.step_seconds",
        ],
    )
    assert report["status"] == "succeeded", report
    assert effects() == before
    options = gateway.call("execution-options", submission_id=receipt["submission_id"])
    assert options["roundtrip"] is True
    assert options["effective"]["no_write"] is True
    assert options["effective"]["retry"]["max_attempts"] == 3
    assert options["effective"]["timeout"] == {"run_seconds": 15, "step_seconds": 5}
    artifacts = command("artifacts", receipt["resource_id"])
    assert artifacts and all(a["content_available"] for a in artifacts), artifacts
    contents = []
    for artifact in artifacts:
        arguments = {"artifact_id": artifact["artifact_id"]}
        original = command("artifact-content", receipt["resource_id"], **arguments)
        from_worker = replica.call(
            "run-command",
            method="artifact-content",
            run_id=receipt["resource_id"],
            arguments=arguments,
        )
        assert from_worker == {"status": 200, "value": original}
        denied = replica.call(
            "run-command",
            method="artifact-content",
            run_id=receipt["resource_id"],
            arguments=arguments,
            foreign_scope=True,
        )
        assert denied["status"] == 404, denied
        response = gateway.call(
            "http",
            method="GET",
            path=f"/v1/runs/{receipt['resource_id']}/artifacts/content?"
            + urlencode(arguments),
        )
        assert response["status"] == 200, response
        contents.append(
            {
                "artifact": artifact,
                "content": original,
                "cross_worker_same": True,
                "foreign_scope_status": denied["status"],
                "http_status": response["status"],
            }
        )
    command(
        "artifact-content",
        receipt["resource_id"],
        expected=404,
        artifact_id="../../outside",
    )
    cases.append(
        {
            "case": "no-write-effective-execution",
            "receipt": receipt,
            "report": report,
            "artifacts": artifacts,
            "artifact_delivery": contents,
            "effects_unchanged": True,
            "canonical_options": options,
            "result": "PASS",
        }
    )
    # The operator changes only its fixture source, never execution metadata.
    with operator.begin() as connection:
        changed = connection.execute(
            text(
                "UPDATE input.source_rows SET quantity='not-an-integer' WHERE id='010'"
            )
        )
        assert changed.rowcount == 1
    receipt, failed = execute("controls-failed-work")
    assert failed["status"] in {"failed", "partial"}, failed
    detail = gateway.call("submission-detail", submission_id=receipt["submission_id"])
    assert detail["submission"]["status"] == "failed", detail
    assert effects() == before
    with operator.begin() as connection:
        changed = connection.execute(
            text("UPDATE input.source_rows SET quantity='5' WHERE id='010'")
        )
        assert changed.rowcount == 1
    blocked = command(
        "retry",
        receipt["resource_id"],
        expected=409,
        idempotency_key="controls-partial-retry",
    )
    blocked_rerun = command(
        "rerun",
        receipt["resource_id"],
        expected=409,
        idempotency_key="controls-partial-rerun",
    )
    cases.append(
        {
            "case": "uncertain-partial-effect-replay-denied",
            "report": failed,
            "effect": detail["effect"],
            "retry": blocked,
            "rerun": blocked_rerun,
            "result": "PASS",
        }
    )
    with operator.begin() as connection:
        connection.execute(
            text(f'REVOKE SELECT ON input.source_rows FROM "{runtime_role}"')
        )
    try:
        receipt, failed = execute("controls-source-read-denied")
        assert failed["status"] == "failed", failed
        assert effects() == before
    finally:
        with operator.begin() as connection:
            connection.execute(
                text(f'GRANT SELECT ON input.source_rows TO "{runtime_role}"')
            )
    retry = command("retry", receipt["resource_id"], idempotency_key="controls-retry")
    repeated = command(
        "retry", receipt["resource_id"], idempotency_key="controls-retry"
    )
    assert retry == repeated
    assert retry["resource_id"] != receipt["resource_id"]
    assert worker.call("tick")["count"] == 1
    retry_report = gateway.call("report", run_id=retry["resource_id"])
    assert retry_report["status"] == "succeeded", retry_report
    lineage = command("lineage", retry["resource_id"])
    assert receipt["resource_id"] in json.dumps(lineage), lineage
    command(
        "retry",
        retry["resource_id"],
        expected=409,
        idempotency_key="controls-retry-completed",
    )
    rerun = command(
        "rerun", retry["resource_id"], idempotency_key="controls-deliberate-rerun"
    )
    assert rerun["resource_id"] not in {receipt["resource_id"], retry["resource_id"]}
    assert worker.call("tick")["count"] == 1
    rerun_report = gateway.call("report", run_id=rerun["resource_id"])
    assert rerun_report["status"] == "succeeded", rerun_report
    rerun_lineage = command("lineage", rerun["resource_id"])
    assert retry["resource_id"] in json.dumps(rerun_lineage), rerun_lineage
    assert effects() == before + 4  # accepted and rejected publications per run.
    cases.append(
        {
            "case": "failed-retry-versus-deliberate-rerun",
            "failed": failed,
            "retry": retry,
            "retry_report": retry_report,
            "retry_lineage": lineage,
            "rerun": rerun,
            "rerun_report": rerun_report,
            "rerun_lineage": rerun_lineage,
            "result": "PASS",
        }
    )
    alias, alias_report = execute(
        "controls-asset-alias", asset_overrides={"upsert-sink": "upsert-sink-alias"}
    )
    assert alias_report["status"] == "succeeded", alias_report
    alias_options = gateway.call(
        "execution-options", submission_id=alias["submission_id"]
    )
    assert alias_options["effective"]["asset_overrides"] == {
        "upsert-sink": "upsert-sink-alias"
    }
    with operator.connect() as connection:
        rows = [
            list(row)
            for row in connection.execute(
                text("SELECT id,payload,quantity FROM sink.upsert_target ORDER BY id")
            )
        ]
    assert rows == [[10, "ok", 10]], rows
    assert effects() == before + 6
    cases.append(
        {
            "case": "asset-alias-upsert-key",
            "receipt": alias,
            "report": alias_report,
            "options": alias_options,
            "rows": rows,
            "result": "PASS",
        }
    )
    with operator.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE sink.upsert_target RENAME COLUMN quantity "
                "TO quantity_before_drift"
            )
        )
    try:
        drift, drift_report = execute("controls-target-schema-drift")
        assert drift_report["status"] in {"partial", "failed"}, drift_report
        drift_detail = gateway.call(
            "submission-detail", submission_id=drift["submission_id"]
        )
        assert drift_detail["submission"]["status"] == "failed"
        assert any(
            step["step_name"] == "sink" and step["status"] == "failed"
            for step in drift_report["steps"]
        )
        assert effects() - before in {6, 7}
    finally:
        with operator.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE sink.upsert_target RENAME COLUMN "
                    "quantity_before_drift TO quantity"
                )
            )
    with operator.connect() as connection:
        after_drift = [
            list(row)
            for row in connection.execute(
                text("SELECT id,payload,quantity FROM sink.upsert_target ORDER BY id")
            )
        ]
    assert after_drift == rows
    cases.append(
        {
            "case": "target-schema-drift-no-false-completion",
            "receipt": drift,
            "report": drift_report,
            "terminal": drift_detail,
            "accepted_sink_unchanged": True,
            "result": "PASS",
        }
    )
    # Accepted uploaded inputs acquire a managed retention lease. Force the
    # first attempt to fail before its source read, then prove retry succeeds
    # after expires_at and the worker's read access has been restored.
    uploaded_content = "id,payload,quantity\n777,OK,7\n"
    expiry = datetime.now(UTC) + timedelta(seconds=15)
    upload = gateway.call(
        "input-resource",
        method="stage",
        arguments={
            "content": uploaded_content,
            "media_type": "text/csv",
            "format": "csv",
            "expires_at": expiry.isoformat(),
        },
    )
    assert upload["status"] == 200, upload
    reference_result = gateway.call(
        "input-resource",
        method="finalize",
        arguments={
            "upload_id": upload["value"]["upload_id"],
            "expected_sha256": hashlib.sha256(uploaded_content.encode()).hexdigest(),
            "expected_byte_length": len(uploaded_content.encode()),
        },
    )
    assert reference_result["status"] == 200, reference_result
    reference = reference_result["value"]
    assert uploaded_content not in json.dumps(reference)
    assert gateway.call("definition-input", reference=reference)["registered"]
    preparation = gateway.call(
        "preparation",
        definition_id="uploaded-transfer",
        key="controls-uploaded-input-after-expiry",
        deadline_seconds=60,
    )
    assert action.call("tick")["count"] == 1
    prepared = gateway.call("preparation-get", operation_id=preparation["operation_id"])
    assert prepared["status"] == "succeeded", {
        "preparation": prepared,
        "action_job": gateway.call("action-job", action_id=preparation["action_id"]),
        "action_worker_stderr": action.stderr_tail(),
        "preparation_error": gateway.call("preparation-error"),
    }
    receipt = prepared["result"]
    delay = (expiry - datetime.now(UTC)).total_seconds() + 0.25
    if delay > 0:
        time.sleep(delay)
    assert datetime.now(UTC) > expiry
    effects_before_retry = effects()
    with operator.begin() as connection:
        connection.execute(
            text(f'REVOKE SELECT ON public.cp_input_uploads FROM "{runtime_role}"')
        )
    try:
        assert worker.call("tick")["count"] == 1
    finally:
        with operator.begin() as connection:
            connection.execute(
                text(f'GRANT SELECT ON public.cp_input_uploads TO "{runtime_role}"')
            )
    failed_report = gateway.call("report", run_id=receipt["resource_id"])
    assert failed_report["status"] in {"failed", "partial"}, failed_report
    assert effects() == effects_before_retry
    retained_retry = command(
        "retry",
        receipt["resource_id"],
        idempotency_key="controls-uploaded-input-retained-retry",
    )
    assert worker.call("tick")["count"] == 1
    retry_report = gateway.call("report", run_id=retained_retry["resource_id"])
    assert retry_report["status"] == "succeeded", retry_report
    with operator.connect() as connection:
        uploaded_rows = [
            list(row)
            for row in connection.execute(
                text("SELECT id,payload,quantity FROM sink.target ORDER BY id")
            )
        ]
    assert [row for row in uploaded_rows if row[0] == 777] == [[777, "ok", 14]], {
        "rows": uploaded_rows,
        "steps": retry_report["steps"],
    }
    detail = gateway.call(
        "submission-detail", submission_id=retained_retry["submission_id"]
    )
    assert uploaded_content not in detail["submission"]["input_snapshot"]
    cases.append(
        {
            "case": "uploaded-input-retry-after-expiry-from-retained-store",
            "reference": reference,
            "expires_at": expiry.isoformat(),
            "first_run": receipt,
            "first_report": failed_report,
            "retry": retained_retry,
            "retry_report": retry_report,
            "target_rows": uploaded_rows,
            "payload_absent_from_durable_snapshot": True,
            "failed_attempt_had_no_publication": True,
            "result": "PASS",
        }
    )
    evidence.update(
        {
            "schema": "shuetl.phase06.controls/1",
            "result": "PASS",
            "limits": (
                "Real transform failure and target schema drift, uploaded input "
                "retention and rerun, retry/rerun admission, artifact delivery, "
                "and selected execution controls. Does not establish full schema "
                "control discovery or the complete public option catalog."
            ),
        }
    )
