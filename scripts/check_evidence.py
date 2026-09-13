"""Validate a committed ShuETL evidence index and redaction rules."""

from __future__ import annotations

import argparse
import hashlib
import json
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


def proof_registry(evidence_dir: Path, errors: list[str]) -> dict[str, dict[str, str]]:
    """Load reviewed proof bindings, not keywords inferred from task labels.

    The registry and qualification record are an auditable review contract.
    This checks reference integrity; it cannot replace human review of whether
    a test or recorded observation establishes the approved requirement.
    """
    registry = evidence_dir / "proofs.json"
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"cannot read current proof registry: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append("current proof registry must be an AC-keyed object")
        return {}
    result: dict[str, dict[str, str]] = {}
    plan = (ROOT / "docs/plans/PHASE_0_4_EXECUTION.md").read_text(encoding="utf-8")
    approved = plan.split("## Acceptance criteria", 1)[1].split(
        "## Verification matrix", 1
    )[0]
    for criterion, proof in data.items():
        fields = ("command", "artifact", "requirement", "provenance", "limitation")
        if not isinstance(proof, dict) or not all(
            isinstance(proof.get(field), str) and proof[field] for field in fields
        ):
            errors.append(f"malformed current proof binding: {criterion}")
            continue
        result[criterion] = proof
        # The verification matrix repeats IDs: bind to the observable AC table,
        # not the matrix's preferred verification type.
        required_row = next(
            (
                line
                for line in approved.splitlines()
                if line.startswith(f"| {criterion} |")
            ),
            "",
        )
        requirement = required_row.strip("|").split("|")
        if len(requirement) != 2 or proof["requirement"] != requirement[1].strip():
            errors.append(
                f"proof requirement differs from approved contract: {criterion}"
            )
        for field in ("artifact", "provenance"):
            reference = proof[field]
            path_ref, _, anchor = reference.partition("#")
            path = evidence_dir / path_ref if "/" not in path_ref else ROOT / path_ref
            if not path.is_file():
                errors.append(f"missing {field} for {criterion}: {reference}")
                continue
            contents = path.read_text(encoding="utf-8")
            headings = {
                re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")
                for heading in re.findall(r"^#+ (.+)$", contents, re.MULTILINE)
            }
            if anchor and anchor not in headings:
                errors.append(f"missing {field} anchor for {criterion}: {reference}")
            if field == "artifact":
                section = contents.split(f"## {criterion}\n", 1)
                record = section[1].split("\n## ", 1)[0] if len(section) == 2 else ""
                if not all(
                    value in record
                    for value in (
                        proof["command"],
                        proof["requirement"],
                        proof["provenance"],
                        proof["limitation"],
                        "Result: PASS",
                    )
                ):
                    errors.append(f"incomplete qualification record for {criterion}")
    return result


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
    registry = (
        proof_registry(evidence_dir, errors) if evidence_dir.name == "0.4" else {}
    )
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
        header = next(
            (
                line.lower()
                for line in section.splitlines()
                if line.startswith("| Criterion |")
            ),
            "",
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
        criterion_counts = {"0.2": 36, "0.3": 42, "0.4": 38}
        expected = {
            f"AC-{number:03d}"
            for number in range(1, criterion_counts.get(evidence_dir.name, 43) + 1)
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
            if evidence_dir.name == "0.4":
                command, artifact = cells[2], cells[3]
                if not command:
                    errors.append(
                        f"acceptance evidence has no verification command: {criterion}"
                    )
                if not artifact:
                    errors.append(
                        f"acceptance evidence has no result artifact: {criterion}"
                    )
                else:
                    artifact_ref = artifact.strip().strip("`")
                    artifact_path = artifact_ref.split("#", 1)[0].split("::", 1)[0]
                    candidate_paths = [ROOT / artifact_path]
                    if "/" not in artifact_path:
                        candidate_paths.insert(0, evidence_dir / artifact_path)
                    if not any(path.exists() for path in candidate_paths):
                        errors.append(
                            "acceptance evidence artifact does not exist: "
                            f"{criterion} ({artifact_path})"
                        )
                binding = registry.get(criterion)
                if binding is None or (
                    command.strip("`") != binding["command"]
                    or artifact.strip("`") != binding["artifact"]
                    or len(cells) < 6
                    or cells[5] != binding["limitation"]
                ):
                    errors.append(
                        f"acceptance evidence does not match audited proof: {criterion}"
                    )
        missing = sorted(expected - seen.keys())
        if missing:
            errors.append(f"acceptance evidence omits criteria: {missing}")
        if evidence_dir.name == "0.4" and registry.keys() != expected:
            errors.append("current proof registry must cover exactly AC-001–AC-038")
        proof_terms = PHASE_0_3_PROOF_TERMS if evidence_dir.name == "0.3" else {}
        if proof_terms:
            for criterion, terms in proof_terms.items():
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
    artifact_prefix = f"shuetl-{PROJECT_VERSION}"
    for kind, pattern in (
        ("wheel", f"{artifact_prefix}*.whl"),
        ("sdist", f"{artifact_prefix}*.tar.gz"),
    ):
        artifacts = sorted(DIST.glob(pattern))
        if len(artifacts) != 1:
            errors.append(f"expected one {kind} artifact in {DIST}")
            continue
        digest = hashlib.sha256(artifacts[0].read_bytes()).hexdigest()
        if recorded_hashes.get(kind) != digest:
            errors.append(f"recorded {kind} SHA-256 does not match built artifact")
    max_criterion = {"0.2": 36, "0.3": 42, "0.4": 38}.get(evidence_dir.name, 42)
    for number in range(1, max_criterion + 1):
        criterion = f"AC-{number:03d}"
        if criterion not in text:
            errors.append(f"evidence index does not mention {criterion}")
    outcomes = (
        ("proceed-to-0.2", "blocked-on-upstream", "merge-into-etlantic-fastapi")
        if evidence_dir.name != "0.4"
        else ("proceed-to-0.4", "blocked-on-upstream", "merge-into-etlantic-fastapi")
    )
    if sum(text.count(outcome) for outcome in outcomes) != 1:
        errors.append("evidence index must record exactly one boundary outcome")
    if "| PASS |" not in text:
        errors.append("evidence index must contain PASS results before release")
    boundary_answers = (
        "integration burden",
        "public composition hooks",
        "copied route",
        "materially easier",
        "contributed to `etlantic-fastapi`",
    )
    if evidence_dir.name == "0.4":
        boundary_answers = (
            "integration burden",
            "public composition hooks",
            "copied route",
        )
    for answer in boundary_answers:
        if answer not in text:
            errors.append(f"boundary review omits answer: {answer}")
    redaction_files = [index, contracts, ownership]
    if evidence_dir.name == "0.4":
        redaction_files.extend(
            path
            for path in (
                evidence_dir / "proofs.json",
                evidence_dir / "qualification.md",
                evidence_dir / "ci.md",
            )
            if path.is_file()
        )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in redaction_files)
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
