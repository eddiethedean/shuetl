"""Validate a committed ShuETL evidence index and redaction rules."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
PROJECT_VERSION = str(PROJECT["project"]["version"])
RELEASE_SERIES = ".".join(PROJECT_VERSION.split(".")[:2])
EVIDENCE = ROOT / "docs" / "evidence" / RELEASE_SERIES
DIST = ROOT / "dist"
REDACTION_PATTERNS = (
    r"/Users/",
    r"/Volumes/",
    r"/home/",
    r"/var/folders/",
    r"-----BEGIN [A-Z ]+PRIVATE KEY-----",
)
PHASE_0_3_PROOF_TERMS = {
    "AC-001": ("metadata", "packag"),
    "AC-002": ("export", "public"),
    "AC-003": ("settings schema",),
    "AC-004": ("required", "fail-closed", "omission"),
    "AC-005": ("precedence",),
    "AC-006": ("source", "dotenv"),
    "AC-007": ("prefix", "route preset"),
    "AC-008": ("cross-field", "combination"),
    "AC-009": ("timeout",),
    "AC-010": ("secret", "redaction"),
    "AC-011": ("core", "compatibility"),
    "AC-012": ("train",),
    "AC-013": ("extra", "capability"),
    "AC-014": ("input", "injection", "adapter"),
    "AC-015": ("memory", "store"),
    "AC-016": ("identity", "profile"),
    "AC-017": ("optional", "provider"),
    "AC-018": ("isolation", "independent"),
    "AC-019": ("sqlite", "file"),
    "AC-020": ("sqlmodel", "engine"),
    "AC-021": ("schema", "migration"),
    "AC-022": ("cleanup", "disposal", "close"),
    "AC-023": ("0.2", "facade"),
    "AC-024": ("parity", "http"),
    "AC-025": ("doctor", "diagnostic"),
    "AC-026": ("doctor", "diagnostic"),
    "AC-027": ("version",),
    "AC-028": ("capabil",),
    "AC-029": ("preflight", "side effect"),
    "AC-030": ("schema",),
    "AC-031": ("check", "order"),
    "AC-032": ("text", "json", "redaction"),
    "AC-033": ("cli", "doctor"),
    "AC-034": ("version", "cli"),
    "AC-035": ("quickstart",),
    "AC-036": ("sqlite example",),
    "AC-037": ("boundar",),
    "AC-038": ("openapi",),
    "AC-039": ("artifact", "clean"),
    "AC-040": ("gate", "matrix"),
    "AC-041": ("doc",),
    "AC-042": ("evidence",),
}


def check(evidence: Path | None = None) -> list[str]:
    errors: list[str] = []
    evidence_dir = evidence or EVIDENCE
    index = evidence_dir / "README.md"
    contracts = evidence_dir / "contracts.md"
    ownership = evidence_dir / "ownership.md"
    for path in (index, contracts, ownership):
        if not path.exists():
            errors.append(f"missing evidence file: {path.relative_to(ROOT)}")
    if errors:
        return errors
    text = index.read_text(encoding="utf-8")
    required_fields = (
        "OS and architecture",
        "Python version",
        "uv version",
        "ETLantic source revision",
        "SHA-256",
        "Gate A",
        "Gate B",
        "Gate C",
        "ShuETL import origin",
        "ETLantic import origin",
        "etlantic-fastapi import origin",
        "FastAPI import origin",
        "Pydantic import origin",
        "HTTPX import origin",
    )
    for field in required_fields:
        if field not in text:
            errors.append(f"evidence index omits required field: {field}")
    acceptance = text.split("## Acceptance results", 1)
    if len(acceptance) == 2:
        section = acceptance[1].split("## Gap register", 1)[0]
        header = (
            section.splitlines()[2].lower() if len(section.splitlines()) > 2 else ""
        )
        for field in (
            "criterion",
            "task",
            "command",
            "artifact",
            "limitation",
            "reviewer",
            "date",
        ):
            if field not in header:
                errors.append(f"acceptance evidence has no {field!r} column")
        rows = [line for line in section.splitlines() if line.startswith("| AC-")]
        expected = {
            f"AC-{number:03d}"
            for number in range(1, (37 if evidence_dir.name == "0.2" else 43))
        }
        seen: dict[str, str] = {}
        proofs: dict[str, str] = {}
        for row in rows:
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            if len(cells) < 5:
                errors.append(f"malformed acceptance row: {row}")
                continue
            criterion, status = cells[0], cells[4]
            if criterion in seen:
                errors.append(f"duplicate acceptance result: {criterion}")
            seen[criterion] = status
            proofs[criterion] = " ".join(cells[1:4]).lower()
            if status != "PASS":
                errors.append(f"acceptance criterion is not PASS: {criterion}")
        missing = sorted(expected - seen.keys())
        if missing:
            errors.append(f"acceptance evidence omits criteria: {missing}")
        if evidence_dir.name == "0.3":
            for criterion, terms in PHASE_0_3_PROOF_TERMS.items():
                proof = proofs.get(criterion, "")
                if proof and not any(term in proof for term in terms):
                    errors.append(
                        f"acceptance evidence does not map {criterion} to its proof"
                    )
    else:
        errors.append("evidence index is missing the acceptance results section")
    for gate in ("Gate A", "Gate B", "Gate C"):
        gate_rows = [
            line for line in text.splitlines() if line.startswith(f"| {gate} |")
        ]
        if not gate_rows:
            errors.append(f"evidence index does not record {gate}")
        elif gate_rows[0].strip("|").split("|")[-1].strip() != "PASS":
            errors.append(f"{gate} is not PASS")
    if evidence_dir.name == "0.3" and not re.search(
        r"\| uv version \| \d+\.\d+\.\d+", text
    ):
        errors.append("evidence index does not record a concrete uv version")
    recorded_hashes = dict(
        re.findall(r"\| SHA-256 (wheel|sdist) \| `([0-9a-f]{64})` \|", text)
    )
    for kind, pattern in (("wheel", "*.whl"), ("sdist", "*.tar.gz")):
        artifacts = sorted(DIST.glob(pattern))
        if len(artifacts) != 1:
            errors.append(f"expected one {kind} artifact in {DIST}")
            continue
        digest = hashlib.sha256(artifacts[0].read_bytes()).hexdigest()
        if recorded_hashes.get(kind) != digest:
            errors.append(f"recorded {kind} SHA-256 does not match built artifact")
    max_criterion = 36 if evidence_dir.name == "0.2" else 42
    for number in range(1, max_criterion + 1):
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
    for answer in (
        "integration burden",
        "public composition hooks",
        "copied route",
        "materially easier",
        "contributed to `etlantic-fastapi`",
    ):
        if answer not in text:
            errors.append(f"boundary review omits answer: {answer}")
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    errors = check(args.evidence)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("evidence consistency checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
