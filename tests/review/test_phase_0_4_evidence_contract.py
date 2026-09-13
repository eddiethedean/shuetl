"""Additional verification of the unresolved SOL-010 proof-reference contract."""

from __future__ import annotations

import shutil
from pathlib import Path

from scripts import check_evidence


def test_sol_010_evidence_rejects_a_pass_without_command_or_artifact(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "0.4"
    evidence.mkdir()
    for name in ("README.md", "contracts.md", "ownership.md"):
        shutil.copy2(check_evidence.EVIDENCE / name, evidence / name)
    index = evidence / "README.md"
    rows = index.read_text().splitlines()
    for position, row in enumerate(rows):
        if row.startswith("| AC-021 |"):
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            cells[2] = ""
            cells[3] = ""
            rows[position] = "| " + " | ".join(cells) + " |"
            break
    else:
        raise AssertionError("Current evidence has no AC-021 row")
    index.write_text("\n".join(rows) + "\n")

    errors = check_evidence.check(evidence)
    assert any("AC-021" in error for error in errors), (
        "A PASS task label without a verification command or artifact "
        "cannot establish AC-021; the evidence gate accepted it"
    )
