"""SOL-010 verification: an existing unrelated test is not current AC proof."""

from __future__ import annotations

import shutil
from pathlib import Path

from scripts import check_evidence


def test_sol_010_evidence_rejects_package_metadata_as_concurrent_submission_proof(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "0.4"
    shutil.copytree(check_evidence.EVIDENCE, evidence)
    index = evidence / "README.md"
    rows = index.read_text().splitlines()
    for position, row in enumerate(rows):
        if row.startswith("| AC-021 |"):
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            cells[2] = "`uv run pytest tests/unit/test_package.py -q`"
            cells[3] = "`tests/unit/test_package.py`"
            rows[position] = "| " + " | ".join(cells) + " |"
            break
    else:
        raise AssertionError("Current evidence has no AC-021 row")
    index.write_text("\n".join(rows) + "\n")

    errors = check_evidence.check(evidence)
    assert any("AC-021" in error for error in errors), (
        "Package metadata verification cannot establish concurrent submissions; "
        "the current task label must not make an unrelated proof pass"
    )
