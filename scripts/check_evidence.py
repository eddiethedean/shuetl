"""Validate a committed ShuETL evidence index and redaction rules."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
PROJECT_VERSION = str(PROJECT["project"]["version"])
RELEASE_SERIES = ".".join(PROJECT_VERSION.split(".")[:2])
EVIDENCE = ROOT / "docs" / "evidence" / RELEASE_SERIES
DIST = ROOT / "dist"
PLAN_BY_SERIES = {
    "0.2": ROOT / "docs/plans/PHASE_0_2_EXECUTION.md",
    "0.3": ROOT / "docs/plans/PHASE_0_3_EXECUTION.md",
    "0.4": ROOT / "docs/plans/PHASE_0_4_EXECUTION.md",
    "0.5": ROOT / "docs/plans/PHASE_0_5_EXECUTION.md",
    "0.6": ROOT / "docs/plans/PHASE_0_6_EXECUTION.md",
}
CRITERION_COUNTS = {"0.2": 36, "0.3": 42, "0.4": 38, "0.5": 34, "0.6": 33}
AUDITED_SERIES = {"0.4", "0.5", "0.6"}
PLACEHOLDERS = {"pending", "open", "tbd", "todo", "unknown", "-"}
REDACTION_PATTERNS = (
    r"/Users/",
    r"/Volumes/",
    r"/home/",
    r"/var/folders/",
    r"-----BEGIN [A-Z ]+PRIVATE KEY-----",
)
PHASE_0_5_MUTATION_CONTEXT = {
    "principal_subject": "alice",
    "principal_issuer": None,
    "principal_kind": "human",
    "tenant_id": "tenant-a",
    "workspace_tenant_id": "tenant-a",
    "workspace_id": "ws-1",
    "environment": "development",
    "security_domain": "default",
    "correlation_key": "phase05-correlation-probe",
    "idempotency_key": "phase05-idempotency-probe",
    "request_id": "phase05-request-probe",
}
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
    plan_path = PLAN_BY_SERIES.get(evidence_dir.name)
    if plan_path is None:
        errors.append(f"no approved execution plan for {evidence_dir.name}")
        return result
    plan = plan_path.read_text(encoding="utf-8")
    approved = plan.split("## Acceptance criteria", 1)[1].split(
        "## Verification matrix", 1
    )[0]
    for criterion, proof in data.items():
        fields = ("command", "artifact", "requirement", "provenance", "limitation")
        if not isinstance(proof, dict) or not all(
            isinstance(proof.get(field), str)
            and proof[field].strip()
            and proof[field].strip().lower() not in PLACEHOLDERS
            for field in fields
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


def phase06_prerequisites(evidence_dir: Path, errors: list[str]) -> None:
    """Require executed upstream acceptance and PostgreSQL role evidence."""
    coverage = evidence_dir / "coverage-acceptance.md"
    if not coverage.is_file():
        errors.append("missing Phase 0.6 upstream coverage acceptance")
    else:
        decisions = [
            [cell.strip() for cell in line.strip("|").split("|")]
            for line in coverage.read_text(encoding="utf-8").splitlines()
            if re.match(r"\| U\d\d\b", line)
        ]
        identifiers = [row[0].split()[0] for row in decisions]
        if (
            set(identifiers) != {f"U{number:02d}" for number in range(1, 6)}
            or len(identifiers) != 5
            or any(row[-1] != "PASS" for row in decisions)
        ):
            errors.append("Phase 0.6 requires exactly five PASS decisions U01–U05")
    for name in ("gate-u.xml", "gate-u-provider.xml"):
        try:
            root = ET.parse(evidence_dir / name).getroot()
            cases = list(root.iter("testcase"))
            suites = list(root.iter("testsuite"))
            if (
                not cases
                or any(
                    case.find(tag) is not None
                    for case in cases
                    for tag in ("failure", "error", "skipped")
                )
                or any(
                    int(suite.get(field, "0")) != 0
                    for suite in suites
                    for field in ("failures", "errors", "skipped")
                )
            ):
                errors.append(f"required Phase 0.6 results are incomplete: {name}")
        except (OSError, ET.ParseError, ValueError):
            errors.append(f"cannot read required Phase 0.6 results: {name}")
    try:
        gate0 = json.loads(
            (evidence_dir / "postgresql-gate0.json").read_text(encoding="utf-8")
        )
        roles = gate0.get("roles", []) if isinstance(gate0, dict) else []
        role_rows = roles if isinstance(roles, list) else []
        role_map = {
            role.get("started"): role
            for role in role_rows
            if isinstance(role, dict) and isinstance(role.get("started"), str)
        }
        expected_roles = {"gateway", "scheduler", "run-worker", "action-worker"}
        expected_capabilities = {
            "canonical_transform",
            "integer_cast",
            "lowercase",
            "scalar_expression",
            "filter",
            "projection_drops_unselected_fields",
            "quality_not_null",
            "quality_range_accept_and_reject",
            "quality_membership_accept_and_reject",
            "accepted_and_rejected_outputs_independently_observed",
            "postgresql_snapshot_source",
        }
        capabilities = (
            gate0.get("capability_results", {}) if isinstance(gate0, dict) else {}
        )
        gate0_good = isinstance(gate0, dict) and (
            gate0.get("schema") == "shuetl.phase06.gate0/1"
            and gate0.get("result") == "PASS"
            and len(role_rows) == 4
            and set(role_map) == expected_roles
            and str(gate0.get("postgresql_version", "")).startswith("18.6")
            and gate0.get("schema_head")
            == "014_cp1_complete_principal_idempotency_0_56"
            and gate0.get("grants")
            == {
                "schema_create": False,
                "migration_membership": False,
                "owned_objects": 0,
            }
            and isinstance(capabilities, dict)
            and set(capabilities) == expected_capabilities
            and all(value is True for value in capabilities.values())
            and gate0.get("sink_rows") == [[1, "ok", 6]] * 3
            and gate0.get("rejected_rows") == [[2, "no", 120]] * 3
            and gate0.get("postgresql_source_rows") == [[10, "ok", 4]]
            and gate0.get("postgresql_rejected_rows") == [[11, "no", 120]]
            and gate0.get("connector_grants")
            == {
                "input_select": True,
                "input_insert": False,
                "input_update": False,
                "input_delete": False,
            }
            and isinstance(gate0.get("sink_effects"), list)
            and len(gate0["sink_effects"]) == 8
            and all(
                isinstance(effect, list) and len(effect) == 3 and effect[2] == 1
                for effect in gate0["sink_effects"]
            )
            and re.fullmatch(r"[0-9a-f]{64}", str(gate0.get("shuetl_wheel_sha256", "")))
            and re.fullmatch(
                r"[0-9a-f]{64}", str(gate0.get("reference_wheel_sha256", ""))
            )
            and bool(re.fullmatch(r"[0-9a-f]{40}", str(gate0.get("source_commit", ""))))
        )
        if not gate0_good:
            errors.append("Phase 0.6 PostgreSQL Gate 0 evidence is not qualified")
        else:
            pids = [row.get("pid") for row in role_rows]
            if any(not isinstance(pid, int) for pid in pids) or len(set(pids)) != 4:
                errors.append(
                    "Phase 0.6 Gate 0 roles must have four distinct process IDs"
                )
            for name, role in role_map.items():
                versions = role.get("versions")
                if (
                    role.get("http_imported") is not (name == "gateway")
                    or role.get("execution_imported") is not (name == "run-worker")
                    or not isinstance(versions, dict)
                    or versions
                    != {
                        "etlantic": "0.57.0",
                        "etlantic-sqlmodel": "0.57.0",
                        "etlantic-sql": "0.57.0",
                    }
                    or "site-packages" not in role.get("origin", "")
                    or "site-packages" not in role.get("reference_origin", "")
                ):
                    errors.append(
                        f"Phase 0.6 Gate 0 role provenance/isolation is invalid: {name}"
                    )
    except (OSError, ValueError):
        errors.append("cannot read Phase 0.6 PostgreSQL Gate 0 evidence")
    try:
        cli = json.loads(
            (evidence_dir / "cli-postgresql.json").read_text(encoding="utf-8")
        )
        expected_roles = {"gateway", "scheduler", "run_worker", "action_worker"}
        cli_roles = cli.get("roles", []) if isinstance(cli, dict) else []
        role_imports = cli.get("role_imports", []) if isinstance(cli, dict) else []
        cli_shutdown = cli.get("shutdown", []) if isinstance(cli, dict) else []
        source_commit = cli.get("source_commit") if isinstance(cli, dict) else None
        source_record = re.search(
            r"\| ShuETL source commit \| `?([0-9a-f]{40})`? \|",
            (evidence_dir / "README.md").read_text(encoding="utf-8"),
        )
        wheel = next(iter(sorted(DIST.glob(f"shuetl-{PROJECT_VERSION}-*.whl"))), None)
        wheel_digest = hashlib.sha256(wheel.read_bytes()).hexdigest() if wheel else None
        cli_pids = [row.get("pid") for row in cli_roles if isinstance(row, dict)]
        import_pids = [
            item.get("pid") for item in role_imports if isinstance(item, dict)
        ]
        gate0 = json.loads(
            (evidence_dir / "postgresql-gate0.json").read_text(encoding="utf-8")
        )
        if (
            not isinstance(cli, dict)
            or cli.get("schema") != "shuetl.phase06.cli-gate/1"
            or cli.get("result") != "PASS"
            or not str(cli.get("postgresql_version", "")).startswith("18.6")
            or cli.get("shuetl_version") != PROJECT_VERSION
            or cli.get("etlantic_version") != "0.57.0"
            or cli.get("etlantic_sql_version") != "0.57.0"
            or cli.get("etlantic_sqlmodel_version") != "0.57.0"
            or len(cli_roles) != 4
            or len(role_imports) != 4
            or any(not isinstance(pid, int) for pid in import_pids)
            or set(import_pids) != set(cli_pids)
            or {item.get("role") for item in role_imports if isinstance(item, dict)}
            != {"gateway", "scheduler", "worker-runs", "worker-actions"}
            or any(
                item.get("fastapi_imported") is not (item.get("role") == "gateway")
                or item.get("etlantic_fastapi_imported")
                is not (item.get("role") == "gateway")
                for item in role_imports
                if isinstance(item, dict)
            )
            or {row.get("role") for row in cli_roles if isinstance(row, dict)}
            != expected_roles
            or any(not isinstance(pid, int) for pid in cli_pids)
            or len(set(cli_pids)) != 4
            or any(
                row.get("ready", {}).get("ready") is not True
                or row.get("live", {}).get("live") is not True
                or row.get("ready", {}).get("process_state") != "running"
                for row in cli_roles
                if isinstance(row, dict)
            )
            or len(cli_shutdown) != 4
            or any(
                not isinstance(row, dict) or row.get("exit_code") != 0
                for row in cli_shutdown
            )
            or "site-packages" not in cli.get("shuetl_origin", "")
            or "site-packages" not in cli.get("reference_host_origin", "")
            or cli.get("shuetl_wheel_sha256") != wheel_digest
            or cli.get("shuetl_wheel_sha256") != gate0.get("shuetl_wheel_sha256")
            or source_commit != gate0.get("source_commit")
            or not re.fullmatch(r"[0-9a-f]{64}", cli.get("reference_wheel_sha256", ""))
            or not source_record
            or source_commit != source_record.group(1)
        ):
            errors.append(
                "Phase 0.6 installed CLI/PostgreSQL evidence is not artifact-qualified"
            )
    except (OSError, ValueError, AttributeError, TypeError):
        errors.append("cannot read Phase 0.6 installed CLI/PostgreSQL evidence")


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
        proof_registry(evidence_dir, errors)
        if evidence_dir.name in AUDITED_SERIES
        else {}
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
    if evidence_dir.name == "0.6":
        required_fields += ("ShuETL source commit",)
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
        expected = {
            f"AC-{number:03d}"
            for number in range(1, CRITERION_COUNTS.get(evidence_dir.name, 43) + 1)
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
            if evidence_dir.name in AUDITED_SERIES:
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
            if evidence_dir.name == "0.6":
                if len(cells) != 8 or any(
                    not cell.strip("`").strip()
                    or cell.strip("`").strip().lower() in PLACEHOLDERS
                    for cell in cells[1:]
                ):
                    errors.append(f"incomplete Phase 0.6 acceptance row: {criterion}")
                else:
                    try:
                        date.fromisoformat(cells[-1])
                    except ValueError:
                        errors.append(f"invalid acceptance review date: {criterion}")
        missing = sorted(expected - seen.keys())
        if missing:
            errors.append(f"acceptance evidence omits criteria: {missing}")
        if evidence_dir.name == "0.6" and seen.keys() != expected:
            errors.append("Phase 0.6 acceptance must cover exactly AC-001–AC-033")
        if evidence_dir.name in AUDITED_SERIES and registry.keys() != expected:
            errors.append(
                "current proof registry must cover exactly "
                f"AC-001–AC-{CRITERION_COUNTS[evidence_dir.name]:03d}"
            )
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
    gates = ("Gate A", "Gate B", "Gate C")
    if evidence_dir.name == "0.6":
        gates = ("Gate U", "Gate 0", *gates)
        phase06_prerequisites(evidence_dir, errors)
    for gate in gates:
        gate_rows = [line for line in text.splitlines() if line.startswith(f"| {gate}")]
        if not gate_rows:
            errors.append(f"evidence index does not record {gate}")
        elif len(gate_rows) != 1:
            errors.append(f"evidence index must record exactly one {gate}")
        elif gate_rows[0].strip("|").split("|")[-1].strip() != "PASS":
            status = gate_rows[0].strip("|").split("|")[-1].strip()
            errors.append(f"{gate} is {status}; release requires PASS")
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
    max_criterion = CRITERION_COUNTS.get(evidence_dir.name, 42)
    for number in range(1, max_criterion + 1):
        criterion = f"AC-{number:03d}"
        if criterion not in text:
            errors.append(f"evidence index does not mention {criterion}")
    outcome = {
        "0.2": "proceed-to-0.2",
        "0.3": "proceed-to-0.3",
        "0.4": "proceed-to-0.4",
        "0.5": "proceed-to-0.5",
    }.get(evidence_dir.name)
    outcomes = (
        (outcome, "blocked-on-upstream", "merge-into-etlantic-fastapi")
        if outcome
        else ()
    )
    if outcomes and sum(text.count(outcome) for outcome in outcomes) != 1:
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
    if evidence_dir.name in {"0.4", "0.5"}:
        boundary_answers = (
            "integration burden",
            "public composition hooks",
            "copied route",
        )
    if evidence_dir.name == "0.5":
        boundary_answers = (
            "integration burden",
            "public composition hooks",
            "copied route",
            "contributed to `etlantic-fastapi`",
            "materially easier",
        )
    if evidence_dir.name in {"0.2", "0.3", "0.4", "0.5"}:
        for answer in boundary_answers:
            if answer not in text:
                errors.append(f"boundary review omits answer: {answer}")
    if evidence_dir.name == "0.5":
        inventory = evidence_dir / "route_inventory.json"
        try:
            routes = json.loads(inventory.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"cannot read mutation route inventory: {exc}")
            routes = []
        if not isinstance(routes, list) or not routes:
            errors.append("mutation route inventory must be a non-empty array")
        else:
            route_keys: set[tuple[str, str, str]] = set()
            for route in routes:
                if not isinstance(route, dict):
                    errors.append("mutation route inventory contains a non-object")
                    continue
                method = route.get("method")
                path = route.get("path")
                operation_id = route.get("operation_id")
                if (
                    not isinstance(method, str)
                    or not method
                    or not isinstance(path, str)
                    or not path
                    or not isinstance(operation_id, str)
                    or not operation_id
                ):
                    errors.append(
                        "mutation route inventory has an incomplete route key"
                    )
                    continue
                key = (method, path, operation_id)
                if key in route_keys:
                    errors.append(f"duplicate mutation route inventory entry: {key}")
                route_keys.add(key)
                authorizations = route.get("authorizations")
                if (
                    not isinstance(authorizations, list)
                    or not authorizations
                    or any(
                        not isinstance(item, dict)
                        or not isinstance(item.get("action"), str)
                        or not item["action"]
                        or not isinstance(item.get("resource"), str)
                        or not item["resource"]
                        or item.get("context") != PHASE_0_5_MUTATION_CONTEXT
                        for item in authorizations
                    )
                    or route.get("denial_status") != 403
                    or route.get("provider_calls") != []
                ):
                    errors.append(
                        "mutation route inventory must record authorization, "
                        f"403 denial, and zero provider calls: {key}"
                    )
    if evidence_dir.name in {"0.5", "0.6"}:
        for name in (
            "proofs.json",
            "qualification.md",
            "ci.md",
            "route_inventory.json",
        ):
            path = evidence_dir / name
            if not path.is_file():
                errors.append(
                    f"missing Phase {evidence_dir.name} evidence artifact: {name}"
                )
    redaction_files = [index, contracts, ownership]
    if evidence_dir.name in AUDITED_SERIES:
        redaction_files.extend(
            path
            for path in (
                evidence_dir / "proofs.json",
                evidence_dir / "qualification.md",
                evidence_dir / "ci.md",
                evidence_dir / "route_inventory.json",
                evidence_dir / "upstream-artifact-qualification.md",
                evidence_dir / "coverage-acceptance.md",
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
