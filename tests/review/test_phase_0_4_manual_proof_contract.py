"""SOL-010: recorded verification must identify real qualified upgrade inputs."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_sol_010_recorded_upgrade_identifiers_are_real() -> None:
    """Check facts explicitly named in proof, not a preferred private layout."""
    migrations = pytest.importorskip("etlantic_sqlmodel.migrations")
    record = (ROOT / "docs/evidence/0.4/qualification.md").read_text()
    upgrade_record = record.split("## AC-016\n", 1)[1].split("\n## ", 1)[0]
    named_heads = set(re.findall(r"\b00[1-5]_[a-z0-9_]+\b", upgrade_record))
    unknown_heads = sorted(named_heads - set(migrations.VERSIONS))

    cli_record = record.split("## AC-014\n", 1)[1].split("\n## ", 1)[0]
    source_symbols = {
        node.name
        for path in (ROOT / "src/shuetl").glob("*.py")
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    named_symbols = {
        step.strip()
        for trace in re.findall(r"Trace ([^;]+);", cli_record)
        for step in trace.split("->")
        if step.strip().isidentifier()
    }
    unknown_symbols = sorted(named_symbols - source_symbols)
    assert not (unknown_heads or unknown_symbols), (
        "AC-036 recorded upgrade proof names nonexistent qualified inputs: "
        f"heads={unknown_heads}, CLI symbols={unknown_symbols}"
    )
