"""Adversarial verification for open Phase 0.1 review blockers."""

from __future__ import annotations

import ast
import re
import tomllib
from importlib import metadata
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SUPPORTED_PYTHONS = ("3.11", "3.12", "3.13")


def _job_block(workflow: Path, job_name: str) -> str:
    text = workflow.read_text(encoding="utf-8")
    match = re.search(
        rf"^  {re.escape(job_name)}:\n(?P<body>.*?)(?=^  [a-zA-Z0-9_-]+:\n|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"missing workflow job: {job_name}"
    return match.group("body")


def test_release_gate_runs_on_every_supported_python() -> None:
    release_gate = _job_block(
        ROOT / ".github" / "workflows" / "checks.yml", "release-gate"
    )
    assert "strategy:" in release_gate and "matrix:" in release_gate
    for version in SUPPORTED_PYTHONS:
        assert f'"{version}"' in release_gate
    assert "python-version: ${{ matrix.python-version }}" in release_gate


def test_clean_wheel_is_not_pinned_to_one_supported_minor() -> None:
    source = (ROOT / "scripts" / "check_clean_wheel.py").read_text(encoding="utf-8")
    for version in SUPPORTED_PYTHONS:
        assert f'"--python", "{version}"' not in source


def test_inventory_names_every_consumed_upstream_symbol() -> None:
    spike = ROOT / "spikes" / "phase_0_1_memory_mount.py"
    tree = ast.parse(spike.read_text(encoding="utf-8"), filename=str(spike))
    consumed = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.split(".", 1)[0] in {"etlantic", "etlantic_fastapi"}
        for alias in node.names
    }
    inventory = (ROOT / "docs" / "evidence" / "0.1" / "contracts.md").read_text(
        encoding="utf-8"
    )
    listed = set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", inventory))
    assert consumed <= listed, f"unlisted consumed symbols: {sorted(consumed - listed)}"


def test_inventory_has_every_required_reserved_capability() -> None:
    inventory = (ROOT / "docs" / "evidence" / "0.1" / "contracts.md").read_text(
        encoding="utf-8"
    )
    table = "\n".join(
        line.lower() for line in inventory.splitlines() if line.startswith("|")
    )
    required = (
        "durable work",
        "registry",
        "history",
        "health",
        "readiness",
        "problem details",
        "sse",
    )
    missing = [capability for capability in required if capability not in table]
    assert not missing, f"required inventory rows missing: {missing}"


def test_ownership_matrix_covers_deployment_profiles() -> None:
    ownership = (ROOT / "docs" / "evidence" / "0.1" / "ownership.md").read_text(
        encoding="utf-8"
    )
    table = "\n".join(
        line.lower() for line in ownership.splitlines() if line.startswith("|")
    )
    assert "deployment profile" in table


def test_every_adr_records_alternatives_and_evidence_links() -> None:
    required_sections = (
        "## Context",
        "## Decision",
        "## Alternatives",
        "## Consequences",
        "## Validation",
        "## Revisit trigger",
    )
    for adr in sorted((ROOT / "docs" / "adr").glob("[0-9][0-9][0-9][0-9]-*.md")):
        text = adr.read_text(encoding="utf-8")
        missing = [section for section in required_sections if section not in text]
        assert not missing, f"{adr.name} missing sections: {missing}"
        assert "contracts.md" in text, f"{adr.name} does not link contract evidence"
        assert "ownership.md" in text, f"{adr.name} does not link ownership evidence"


def test_evidence_index_contains_required_reproducibility_record() -> None:
    index = (ROOT / "docs" / "evidence" / "0.1" / "README.md").read_text(
        encoding="utf-8"
    )
    required = (
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
    missing = [item for item in required if item not in index]
    assert not missing, f"evidence record missing required fields: {missing}"

    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked_versions = {
        package["name"]: package["version"] for package in lock["package"]
    }
    for distribution in ("fastapi", "pydantic", "httpx"):
        version = locked_versions[distribution]
        assert version in index, f"evidence omits locked {distribution}=={version}"

    acceptance = index.split("## Acceptance results", 1)[1].split("## Gap register", 1)[
        0
    ]
    header = acceptance.splitlines()[2].lower()
    for field in (
        "criterion",
        "task",
        "command",
        "artifact",
        "limitation",
        "reviewer",
        "date",
    ):
        assert field in header, f"acceptance evidence has no {field!r} column"


def test_boundary_review_answers_all_stop_questions() -> None:
    index = (ROOT / "docs" / "evidence" / "0.1" / "README.md").read_text(
        encoding="utf-8"
    )
    required_answers = (
        "integration burden",
        "public composition hooks",
        "copied route",
        "materially easier",
        "contributed to `etlantic-fastapi`",
    )
    missing = [answer for answer in required_answers if answer not in index]
    assert not missing, f"boundary-review answers missing: {missing}"


def test_spike_output_records_versions_and_memory_profile(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from spikes.phase_0_1_memory_mount import run

    run()
    captured = capsys.readouterr()
    assert "process-local" in captured.out.lower()
    for distribution in (
        "shuetl",
        "etlantic",
        "etlantic-fastapi",
        "fastapi",
        "pydantic",
        "httpx",
    ):
        expected = f"{distribution}={metadata.version(distribution)}"
        assert expected in captured.out.lower()


def test_contract_accounts_for_authorized_release_automation() -> None:
    release_workflow = ROOT / ".github" / "workflows" / "release.yml"
    if not release_workflow.exists():
        return
    contract = (ROOT / "docs" / "plans" / "PHASE_0_1_EXECUTION.md").read_text(
        encoding="utf-8"
    )
    touched_surface = contract.split("### Touched Surface", 1)[1].split(
        "## Public Contract", 1
    )[0]
    non_scope = contract.split("## Explicit Non-Scope", 1)[1].split(
        "## Known Follow-Up Candidates", 1
    )[0]
    assert ".github/workflows/release.yml" in touched_surface
    assert "publication automation" not in non_scope
