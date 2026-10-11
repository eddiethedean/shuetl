"""Installed-wheel crash qualification, called inside the disposable Gate 0 fixture.

Barriers wrap public provider methods in the independent reference test wheel.
The parent sends SIGKILL only after observing a named boundary. Recovery uses
published factories and public queries; no fixture edits leases or terminal rows.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import text


def qualify(*, start_role, gateway, action, worker, operator, schedule_id, evidence):
    gateway.call("schedule-command", method="pause", schedule_id=schedule_id)
    records = evidence.setdefault("cases", [])

    def sink_state():
        with operator.connect() as connection:
            return {
                "rows": [
                    list(r)
                    for r in connection.execute(
                        text(
                            "SELECT id,payload,quantity FROM sink.upsert_target "
                            "ORDER BY id"
                        )
                    )
                ],
                "effects": connection.execute(
                    text("SELECT count(*) FROM sink.effects")
                ).scalar_one(),
            }

    def pause(role, target, method, when, op, **values):
        role.call("fault-arm", target=target, method=method, when=when)
        deadline = time.monotonic() + 20
        while True:
            role.process.stdin.write(json.dumps({"op": op, **values}) + "\n")
            role.process.stdin.flush()
            observed = role.read()
            if observed == {"barrier": method, "when": when}:
                break
            # A prior scheduler can retain its real-time leader lease after
            # cooperative close. Poll public standby state until this process
            # reaches the armed boundary; never kill an unobserved transaction.
            if (
                observed.get("ok", {}).get("status", {}).get("activity") == "standby"
                and time.monotonic() < deadline
            ):
                time.sleep(0.1)
                continue
            break
        assert observed == {"barrier": method, "when": when}, (
            observed,
            role.stderr_tail(),
        )
        return observed

    def crash(role, target, method, when, op, **values):
        observed = pause(role, target, method, when, op, **values)
        role.process.kill()
        assert role.process.wait(timeout=10) != 0
        return observed

    def accepted(key):
        prep = gateway.call(
            "preparation",
            key=key,
            request={
                "retry": {"max_attempts": 3},
                "explicit_settings": ["retry.max_attempts"],
            },
        )
        assert action.call("tick")["count"] == 1
        result = gateway.call("preparation-get", operation_id=prep["operation_id"])
        assert result["status"] == "succeeded", result
        receipt = result["result"]
        return prep, receipt

    def resume(role):
        role.process.stdin.write('{"op":"release"}\n')
        role.process.stdin.flush()
        response = role.read()
        if "error" in response:
            assert response["type"] == "ControlPlaneError", response
            return {"type": response["type"], "error": response["error"]}
        return response["ok"]

    for when in ("before", "after"):
        key = "fault-gateway-" + when
        doomed = start_role("gateway")
        boundary = crash(
            doomed, "durable", "accept_action_job", when, "preparation", key=key
        )
        recovered = gateway.call("preparation", key=key)
        repeated = gateway.call("preparation", key=key)
        assert recovered["operation_id"] == repeated["operation_id"]
        assert action.call("tick")["count"] == 1
        assert worker.call("tick")["count"] == 1
        records.append(
            {
                "case": key,
                "boundary": boundary,
                "same_operation": True,
                "result": "PASS",
            }
        )

    # Action preparation crosses separately committed CP1 acceptance and durable
    # submission publication. Restart must reconcile both by the same command key.
    for target, method, when in (
        ("durable", "claim_action_job", "after"),
        ("submissions", "accept", "after"),
        ("durable", "accept", "after"),
    ):
        key = "fault-action-" + target + "-" + method
        prep = gateway.call("preparation", key=key, deadline_seconds=10)
        doomed = start_role("action-worker")
        boundary = crash(doomed, target, method, when, "tick")
        replacement = start_role("action-worker")
        deadline = time.monotonic() + 20
        ticks = []
        while time.monotonic() < deadline:
            ticks.append(replacement.call("tick")["count"])
            result = gateway.call("preparation-get", operation_id=prep["operation_id"])
            if result["status"] in {"succeeded", "failed", "timed_out", "cancelled"}:
                break
            time.sleep(0.1)
        else:
            raise AssertionError("action did not reach a terminal status")
        repeat = gateway.call("preparation", key=key, deadline_seconds=10)
        assert repeat["operation_id"] == prep["operation_id"]
        accepted_key = "preparation-" + prep["operation_id"]
        cp1 = gateway.call("lookup-cp1", key=accepted_key)
        durable = gateway.call("lookup-submission", key=accepted_key)
        count = worker.call("tick")["count"]
        passed = (result["status"] == "succeeded" and count == 1) or (
            method == "claim_action_job"
            and result["status"] == "timed_out"
            and cp1 is None
            and durable is None
            and count == 0
        )
        records.append(
            {
                "case": key,
                "boundary": boundary,
                "recovery_ticks": ticks,
                "operation": result,
                "repeat": repeat,
                "cp1_receipt": cp1,
                "durable_submission": durable,
                "run_worker_count": count,
                "result": "PASS" if passed else "FAIL",
            }
        )
        replacement.close()
    # A still-alive process resumes with its old fence after another worker
    # has authoritatively completed the run. Only public lease expiry/recovery
    # changes ownership; the fixture never edits storage or supplies fake results.
    _, receipt = accepted("fault-stale-worker")
    stale = start_role("run-worker")
    boundary = pause(stale, "durable", "acquire_lease", "after", "tick")
    replacement = start_role("run-worker")
    deadline = time.monotonic() + 20
    while True:
        replacement.call("tick")
        authoritative = gateway.call(
            "submission-detail", submission_id=receipt["submission_id"]
        )
        if authoritative["submission"]["status"] == "completed":
            break
        assert time.monotonic() < deadline, authoritative
        time.sleep(0.1)
    sink_before_resume = sink_state()
    stale_response = resume(stale)
    assert stale_response.get("error") == "Stale or invalid execution lease", (
        stale_response
    )
    after_resume = gateway.call(
        "submission-detail", submission_id=receipt["submission_id"]
    )
    assert authoritative == after_resume
    assert sink_state() == sink_before_resume
    records.append(
        {
            "case": "fault-stale-worker",
            "boundary": boundary,
            "authoritative": authoritative,
            "stale_tick": stale_response,
            "state_unchanged": True,
            "sink_unchanged": True,
            "result": "PASS",
        }
    )
    stale.close()
    replacement.close()

    for stage, method, target, when in (
        ("accepted", None, None, None),
        ("leased", "acquire_lease", "durable", "after"),
        ("running", "start_attempt", "durable", "after"),
        ("effect-committed", "put", "reports", "before"),
    ):
        _, receipt = accepted("fault-cancel-" + stage)
        before = sink_state()
        active = start_role("run-worker")
        boundary = None
        if method:
            boundary = pause(active, target, method, when, "tick")
        at_cancel = sink_state()
        request = gateway.call(
            "cancel-submission", submission_id=receipt["submission_id"]
        )
        assert request["status"] == "cancel_requested"
        response = resume(active) if method else active.call("tick")
        deadline = time.monotonic() + 20
        while True:
            detail = gateway.call(
                "submission-detail", submission_id=receipt["submission_id"]
            )
            if detail["submission"]["status"] == "cancelled":
                break
            assert time.monotonic() < deadline, detail
            active.call("tick")
            time.sleep(0.1)
        after = sink_state()
        if stage in {"accepted", "leased"}:
            assert after == before
        assert all(a["status"] != "completed" for a in detail["attempts"]), detail
        records.append(
            {
                "case": "fault-cancel-" + stage,
                "boundary": boundary,
                "cancel_request": request,
                "tick": response,
                "terminal": detail,
                "before": before,
                "at_cancel": at_cancel,
                "after": after,
                "report": gateway.call(
                    "report-or-error", run_id=receipt["resource_id"]
                ),
                "result": "PASS",
            }
        )
        active.close()

    for method, when in (
        ("acquire_lease", "before"),
        ("acquire_lease", "after"),
        ("start_attempt", "after"),
        ("put", "before"),
        ("put", "after"),
        ("finish_attempt", "after"),
        ("mark_published", "before"),
    ):
        key = "fault-run-" + method + "-" + when
        _, receipt = accepted(key)
        before = sink_state()
        doomed = start_role("run-worker")
        boundary = crash(
            doomed, "reports" if method == "put" else "durable", method, when, "tick"
        )
        at_crash = sink_state()
        replacement = start_role("run-worker")
        # A durable result/terminal state can be reconciled without starting a
        # second ETL attempt, so completion is observed through the public record.
        deadline = time.monotonic() + 20
        ticks = []
        while time.monotonic() < deadline:
            ticks.append(replacement.call("tick")["count"])
            detail = gateway.call(
                "submission-detail", submission_id=receipt["submission_id"]
            )
            if detail["submission"]["status"] in {"completed", "failed", "cancelled"}:
                break
            time.sleep(0.1)
        else:
            raise AssertionError("run remained nonterminal after real lease expiry")
        after = sink_state()
        assert after["rows"] == [[10, "ok", 10]], after
        assert after["effects"] - before["effects"] <= 2, (before, at_crash, after)
        status = detail["submission"]["status"]
        must_complete = (
            method in {"put", "finish_attempt", "mark_published"} and when == "after"
        ) or method == "acquire_lease"
        uncertain = (
            method in {"start_attempt", "put"}
            and not (method == "put" and when == "after")
            and status == "failed"
            and (detail.get("effect") or {}).get("status") == "unknown"
            and after == at_crash
        )
        passed = (
            status == "completed"
            if must_complete
            else uncertain or status == "completed"
        )
        records.append(
            {
                "case": key,
                "boundary": boundary,
                "recovery_ticks": ticks,
                "submission_status": status,
                "attempts": detail["attempts"],
                "effect": detail["effect"],
                "before": before,
                "at_crash": at_crash,
                "after": after,
                "report": gateway.call(
                    "report-or-error", run_id=receipt["resource_id"]
                ),
                "result": "PASS" if passed else "FAIL",
            }
        )
        replacement.close()

    # The fake clock selects schedule due times only. Leader, run and action
    # leases expire on the real provider clock; never edit their stored timestamps.
    for index, (target, method, when) in enumerate(
        (
            ("schedule", "claim_firing", "before"),
            ("schedule", "claim_firing", "after"),
            ("durable", "accept", "after"),
            ("schedule", "link_firing_submission", "before"),
            ("schedule", "link_firing_submission", "after"),
        )
    ):
        instant = (
            datetime(2026, 10, 10, tzinfo=UTC) + timedelta(minutes=index)
        ).isoformat()
        identifier = "fault-schedule-" + str(index)
        created = gateway.call("schedule-create", instant=instant)
        identifier = created["schedule_id"]
        doomed = start_role("scheduler")
        boundary = crash(doomed, target, method, when, "tick", instant=instant)
        replacement = start_role("scheduler")
        recovery = (datetime.fromisoformat(instant) + timedelta(seconds=5)).isoformat()
        deadline = time.monotonic() + 20
        ticks = []
        while time.monotonic() < deadline:
            ticks.append(replacement.call("tick", instant=recovery)["count"])
            firings = gateway.call("firings", schedule_id=identifier)
            if len(firings) == 1 and firings[0]["submission_id"]:
                break
            time.sleep(0.1)
        else:
            raise AssertionError(
                f"scheduler did not recover after lease expiry: {firings}"
            )
        gateway.call("schedule-command", method="pause", schedule_id=identifier)
        assert worker.call("tick")["count"] == 1
        submission = gateway.call(
            "submission", submission_id=firings[0]["submission_id"]
        )
        assert (
            gateway.call("report", run_id=submission["run_id"])["status"] == "succeeded"
        )
        records.append(
            {
                "case": "fault-schedule-" + str(index),
                "boundary": boundary,
                "firings": firings,
                "recovery_ticks": ticks,
                "result": "PASS",
            }
        )
        replacement.close()
    evidence.update(
        {
            "schema": "shuetl.phase06.crashes/1",
            "result": "PASS" if all(r["result"] == "PASS" for r in records) else "FAIL",
            "cases": records,
            "limits": (
                "Test-only public-call barriers and published recovery; active CLI "
                "drain and force termination use a separate qualification."
            ),
        }
    )
    assert evidence["result"] == "PASS", (
        "canonical crash recovery failed; see crash evidence"
    )
    return evidence
