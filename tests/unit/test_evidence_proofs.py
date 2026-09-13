"""Implementation-side integrity checks for the audited Phase 0.4 proofs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from scripts import check_evidence


def _copy(tmp_path: Path) -> Path:
    evidence = tmp_path / "0.4"
    shutil.copytree(check_evidence.EVIDENCE, evidence)
    return evidence


@pytest.mark.parametrize("criterion", ["AC-012", "AC-016", "AC-018", "AC-025"])
def test_another_acs_passing_proof_cannot_replace_recorded_proof(
    tmp_path: Path, criterion: str
) -> None:
    evidence = _copy(tmp_path)
    index = evidence / "README.md"
    rows = index.read_text().splitlines()
    other = next(row for row in rows if row.startswith("| AC-001 |"))
    replacement = [cell.strip() for cell in other.strip("|").split("|")]
    for position, row in enumerate(rows):
        if row.startswith(f"| {criterion} |"):
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            cells[2:4] = replacement[2:4]
            rows[position] = "| " + " | ".join(cells) + " |"
    index.write_text("\n".join(rows) + "\n")
    assert any(criterion in error for error in check_evidence.check(evidence))


def test_registry_cannot_redefine_the_approved_requirement(tmp_path: Path) -> None:
    evidence = _copy(tmp_path)
    registry = evidence / "proofs.json"
    proofs = json.loads(registry.read_text())
    proofs["AC-021"]["requirement"] = "Package metadata is valid."
    registry.write_text(json.dumps(proofs))
    assert any(
        "approved contract: AC-021" in error for error in check_evidence.check(evidence)
    )


def test_manual_proof_requires_its_locatable_result_section(tmp_path: Path) -> None:
    evidence = _copy(tmp_path)
    record = evidence / "qualification.md"
    record.write_text(record.read_text().replace("## AC-021\n", "## Removed\n"))
    assert any("AC-021" in error for error in check_evidence.check(evidence))


def test_valid_registry_and_ledger_have_no_proof_errors(tmp_path: Path) -> None:
    errors = check_evidence.check(_copy(tmp_path))
    assert not [error for error in errors if "SHA-256" not in error]
