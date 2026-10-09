"""Reject incomplete or substituted Phase 0.6 release evidence."""

from __future__ import annotations

import hashlib
import json
import re
import shutil

import pytest
from scripts import check_evidence


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    evidence = tmp_path / "0.6"
    shutil.copytree(check_evidence.ROOT / "docs/evidence/0.6", evidence)
    index = evidence / "README.md"
    text = index.read_text()
    dist = tmp_path / "dist"
    dist.mkdir()
    monkeypatch.setattr(check_evidence, "DIST", dist)
    wheel_digest = ""
    for kind, suffix in (("wheel", "-py3-none-any.whl"), ("sdist", ".tar.gz")):
        payload = f"synthetic {kind} fixture".encode()
        (dist / f"shuetl-{check_evidence.PROJECT_VERSION}{suffix}").write_bytes(payload)
        if kind == "wheel":
            wheel_digest = hashlib.sha256(payload).hexdigest()
        text = re.sub(
            rf"(\| SHA-256 {kind} \| `)[0-9a-f]{{64}}(` \|)",
            rf"\g<1>{hashlib.sha256(payload).hexdigest()}\g<2>",
            text,
        )
    plan = check_evidence.PLAN_BY_SERIES["0.6"].read_text()
    requirements = {
        row.split("|")[1].strip(): row.split("|")[2].strip()
        for row in plan.splitlines()
        if re.match(r"\| AC-\d{3} \|", row)
    }
    proofs = {}
    records = []
    for number in range(1, 34):
        criterion = f"AC-{number:03d}"
        proof = {
            "command": f"python synthetic-check.py --criterion {criterion}",
            "artifact": f"qualification.md#{criterion.lower()}",
            "requirement": requirements[criterion],
            "provenance": f"source.md#{criterion.lower()}",
            "limitation": "Synthetic fixture only.",
        }
        proofs[criterion] = proof
        row = (
            f"| {criterion} | fixture | `{proof['command']}` | `{proof['artifact']}` "
            f"| PASS | {proof['limitation']} | fixture-reviewer | 2026-10-09 |"
        )
        text = re.sub(
            rf"^\| {criterion} \|.*$", lambda match, row=row: row, text, flags=re.M
        )
        records.append(
            f"## {criterion}\n"
            + "\n".join(
                proof[field]
                for field in ("command", "requirement", "provenance", "limitation")
            )
            + "\nResult: PASS\n"
        )
    text = re.sub(r"^(\| Gate [ABC].*)OPEN( \|)$", r"\1PASS\2", text, flags=re.M)
    source_commit = "a" * 40
    text = re.sub(
        r"^\| ShuETL source commit \|.*\|$",
        f"| ShuETL source commit | {source_commit} |",
        text,
        flags=re.M,
    )
    index.write_text(text)
    (evidence / "proofs.json").write_text(json.dumps(proofs))
    gate0_path = evidence / "postgresql-gate0.json"
    gate0 = json.loads(gate0_path.read_text())
    reference_digest = hashlib.sha256(b"synthetic reference wheel fixture").hexdigest()
    gate0.update(
        source_commit=source_commit,
        shuetl_wheel_sha256=wheel_digest,
        reference_wheel_sha256=reference_digest,
        sink_rows=[[1, "ok", 6]] * 3,
        rejected_rows=[[2, "no", 120]] * 3,
        sink_effects=[
            [f"effect-{index}", f"publication-{index}", 1] for index in range(6)
        ],
        capability_results={
            "canonical_transform": True,
            "integer_cast": True,
            "lowercase": True,
            "scalar_expression": True,
            "filter": True,
            "projection_drops_unselected_fields": True,
            "quality_not_null": True,
            "quality_range_accept_and_reject": True,
            "quality_membership_accept_and_reject": True,
            "accepted_and_rejected_outputs_independently_observed": True,
        },
    )
    gate0_path.write_text(json.dumps(gate0))
    cli_path = evidence / "cli-postgresql.json"
    cli = json.loads(cli_path.read_text())
    cli.update(
        etlantic_version="0.57.0",
        etlantic_sql_version="0.57.0",
        etlantic_sqlmodel_version="0.57.0",
        source_commit=source_commit,
        shuetl_wheel_sha256=wheel_digest,
        reference_wheel_sha256=hashlib.sha256(
            b"synthetic reference host wheel"
        ).hexdigest(),
        role_imports=[
            {
                "role": role,
                "pid": process["pid"],
                "fastapi_imported": role == "gateway",
                "etlantic_fastapi_imported": role == "gateway",
            }
            for role, process in (
                (
                    "gateway",
                    next(row for row in cli["roles"] if row["role"] == "gateway"),
                ),
                (
                    "scheduler",
                    next(row for row in cli["roles"] if row["role"] == "scheduler"),
                ),
                (
                    "worker-runs",
                    next(row for row in cli["roles"] if row["role"] == "run_worker"),
                ),
                (
                    "worker-actions",
                    next(row for row in cli["roles"] if row["role"] == "action_worker"),
                ),
            )
        ],
    )
    cli_path.write_text(json.dumps(cli))
    (evidence / "qualification.md").write_text("\n".join(records))
    (evidence / "source.md").write_text(
        "# Fixture\n"
        + "\n".join(f"## {criterion}\nSynthetic provenance." for criterion in proofs)
    )
    (evidence / "ci.md").write_text("# Fixture\nSynthetic hosted record.\n")
    assert check_evidence.check(evidence) == []
    return evidence


def test_audited_phase06_ledger_accepts_complete_fixture(ledger):
    assert check_evidence.check(ledger) == []


def test_pass_labels_cannot_replace_missing_proofs(ledger):
    (ledger / "proofs.json").unlink()
    errors = check_evidence.check(ledger)
    assert any("proof registry" in error for error in errors)
    assert any("audited proof: AC-001" in error for error in errors)


@pytest.mark.parametrize("gate", ["Gate U", "Gate 0"])
def test_upstream_and_postgresql_gate_failures_are_required(ledger, gate):
    index = ledger / "README.md"
    index.write_text(
        re.sub(
            rf"^(\| {gate}[^\n]*)PASS( \|)$", r"\1FAIL\2", index.read_text(), flags=re.M
        )
    )
    assert any(f"{gate} is FAIL" in error for error in check_evidence.check(ledger))


@pytest.mark.parametrize("field", ["command", "artifact", "requirement", "provenance"])
def test_phase06_proof_substitution_is_rejected(ledger, field):
    path = ledger / "proofs.json"
    proofs = json.loads(path.read_text())
    proofs["AC-033"][field] = proofs["AC-001"][field]
    path.write_text(json.dumps(proofs))
    assert any("AC-033" in error for error in check_evidence.check(ledger))


def test_required_upstream_results_cannot_skip_cases(ledger):
    (ledger / "gate-u.xml").write_text(
        '<testsuite tests="1" skipped="0">'
        '<testcase name="fixture"><skipped/></testcase></testsuite>'
    )
    assert any("gate-u.xml" in error for error in check_evidence.check(ledger))


def test_missing_postgresql_evidence_is_rejected(ledger):
    (ledger / "postgresql-gate0.json").unlink()
    assert any("Gate 0 evidence" in error for error in check_evidence.check(ledger))


def test_failed_postgresql_evidence_is_rejected(ledger):
    path = ledger / "postgresql-gate0.json"
    data = json.loads(path.read_text())
    data["result"] = "FAIL"
    path.write_text(json.dumps(data))
    assert any("Gate 0 evidence" in error for error in check_evidence.check(ledger))


def test_phase06_gate0_requires_live_transform_and_quality_observations(ledger):
    path = ledger / "postgresql-gate0.json"
    data = json.loads(path.read_text())
    data["capability_results"]["quality_range_accept_and_reject"] = False
    path.write_text(json.dumps(data))
    assert any("Gate 0 evidence" in error for error in check_evidence.check(ledger))


def test_failed_upstream_contract_is_rejected(ledger):
    path = ledger / "coverage-acceptance.md"
    path.write_text(
        re.sub(r"^(\| U05[^\n]*)PASS( \|)$", r"\1FAIL\2", path.read_text(), flags=re.M)
    )
    assert any("U01–U05" in error for error in check_evidence.check(ledger))


@pytest.mark.parametrize("cell", [1, 2, 3, 5, 6, 7])
def test_acceptance_placeholders_are_rejected(ledger, cell):
    path = ledger / "README.md"
    text = path.read_text()
    row = next(row for row in text.splitlines() if row.startswith("| AC-001 |"))
    cells = [value.strip() for value in row.strip("|").split("|")]
    cells[cell] = "pending"
    path.write_text(text.replace(row, "| " + " | ".join(cells) + " |"))
    assert any("AC-001" in error for error in check_evidence.check(ledger))


def test_extra_acceptance_criteria_are_rejected(ledger):
    path = ledger / "README.md"
    text = path.read_text()
    row = next(row for row in text.splitlines() if row.startswith("| AC-001 |"))
    path.write_text(text.replace(row, row + "\n" + row.replace("AC-001", "AC-034")))
    assert any(
        "exactly AC-001–AC-033" in error for error in check_evidence.check(ledger)
    )
