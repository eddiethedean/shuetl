"""Public immutable-input qualification across independently installed workers."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta


def qualify(*, gateway, worker, replica, evidence):
    records = evidence.setdefault("cases", [])
    now = datetime.now(UTC)
    expiry = now + timedelta(seconds=30)
    later = expiry + timedelta(seconds=1)
    retained = later + timedelta(minutes=1)

    def call(role, method, expected=200, **arguments):
        result = role.call("input-resource", method=method, arguments=arguments)
        assert result["status"] == expected, (method, result)
        return result.get("value")

    content = "id,payload\n001,immutable-input-sentinel\n"
    digest = hashlib.sha256(content.encode()).hexdigest()
    upload = call(
        gateway,
        "stage",
        content=content,
        media_type="text/csv",
        format="csv",
        expires_at=expiry.isoformat(),
    )
    call(
        gateway,
        "finalize",
        409,
        upload_id=upload["upload_id"],
        expected_sha256="0" * 64,
        expected_byte_length=len(content.encode()),
    )
    reference = call(
        gateway,
        "finalize",
        upload_id=upload["upload_id"],
        expected_sha256=digest,
        expected_byte_length=len(content.encode()),
    )
    assert reference["version"] == "sha256:" + digest
    repeated = call(
        gateway,
        "finalize",
        upload_id=upload["upload_id"],
        expected_sha256=digest,
        expected_byte_length=len(content.encode()),
    )
    assert reference == repeated
    call(
        gateway,
        "finalize",
        409,
        upload_id=upload["upload_id"],
        expected_sha256="1" * 64,
        expected_byte_length=len(content.encode()),
    )
    for role in (worker, replica):
        assert call(role, "read", reference=reference)["sha256"] == digest
    for selector in ("foreign_owner", "foreign_scope"):
        denied = replica.call(
            "input-resource",
            method="read",
            arguments={"reference": reference},
            **{selector: True},
        )
        assert denied["status"] == 404, denied
    altered = {**reference, "sha256": "1" * 64, "version": "sha256:" + "1" * 64}
    call(worker, "read", 409, reference=altered)
    missing = {**reference, "resource_id": "0" * 32}
    call(worker, "read", 404, reference=missing)
    records.append(
        {
            "case": "checksum-version-owner-scope-cross-worker",
            "reference": reference,
            "result": "PASS",
        }
    )
    call(worker, "read", 410, reference=reference, now=later.isoformat())
    call(
        gateway,
        "acquire_lease",
        reference=reference,
        lease_id="retry-retention",
        retain_until=retained.isoformat(),
    )
    assert (
        call(
            replica,
            "read_leased",
            reference=reference,
            lease_id="retry-retention",
            now=later.isoformat(),
        )["sha256"]
        == digest
    )
    kept = call(gateway, "cleanup", now=later.isoformat(), limit=1)
    assert kept["deleted_upload_ids"] == [] and kept["remaining_candidates"] == 0
    call(gateway, "release_lease", lease_id="retry-retention")
    call(
        replica,
        "read_leased",
        410,
        reference=reference,
        lease_id="retry-retention",
        now=later.isoformat(),
    )
    extra = call(
        gateway,
        "stage",
        content=content,
        media_type="text/csv",
        format="csv",
        expires_at=expiry.isoformat(),
    )
    removed = call(gateway, "cleanup", now=later.isoformat(), limit=1)
    assert (
        len(removed["deleted_upload_ids"]) == 1 and removed["remaining_candidates"] == 1
    ), removed
    rest = call(gateway, "cleanup", now=later.isoformat(), limit=1)
    assert len(rest["deleted_upload_ids"]) == 1 and rest["remaining_candidates"] == 0
    assert set(removed["deleted_upload_ids"] + rest["deleted_upload_ids"]) == {
        reference["resource_id"],
        extra["upload_id"],
    }
    call(replica, "read", 404, reference=reference)
    records.append(
        {
            "case": "expiry-retry-retention-bounded-cleanup",
            "first_cleanup": removed,
            "second_cleanup": rest,
            "result": "PASS",
        }
    )
    evidence.update(
        {
            "schema": "shuetl.phase06.inputs/1",
            "result": "PASS",
            "limits": (
                "Public input-store API across OS workers; supplied future "
                "observation clocks test expiry without changing stored timestamps. "
                "Does not establish report-artifact delivery "
                "or actual run retry retention."
            ),
        }
    )
