"""Validate the committed Phase 0.1 evidence index and redaction rules."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "evidence" / "0.1"
REDACTION_PATTERNS = (
    r"/Users/",
    r"/Volumes/",
    r"/home/",
    r"/var/folders/",
    r"-----BEGIN [A-Z ]+PRIVATE KEY-----",
)


def check() -> list[str]:
    errors: list[str] = []
    index = EVIDENCE / "README.md"
    contracts = EVIDENCE / "contracts.md"
    ownership = EVIDENCE / "ownership.md"
    for path in (index, contracts, ownership):
        if not path.exists():
            errors.append(f"missing evidence file: {path.relative_to(ROOT)}")
    if errors:
        return errors
    text = index.read_text(encoding="utf-8")
    for number in range(1, 23):
        criterion = f"AC-{number:03d}"
        if criterion not in text:
            errors.append(f"evidence index does not mention {criterion}")
    if (
        text.count("proceed-to-0.2")
        + text.count("blocked-on-upstream")
        + text.count("merge-into-etlantic-fastapi")
        != 1
    ):
        errors.append("evidence index must record exactly one boundary outcome")
    if "| PASS |" not in text:
        errors.append("evidence index must contain PASS results before release")
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in (index, contracts, ownership)
    )
    for pattern in REDACTION_PATTERNS:
        if re.search(pattern, combined):
            errors.append(
                f"evidence contains a forbidden sensitive/path pattern: {pattern}"
            )
    return errors


def main() -> int:
    errors = check()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("evidence consistency checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
