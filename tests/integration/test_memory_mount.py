"""Executable Phase 0.1 proof against the public ETLantic FastAPI seam."""

from __future__ import annotations

import json
from pathlib import Path

from spikes.phase_0_1_memory_mount import (
    assert_openapi_parity,
    build_direct_app,
    build_embedded_app,
    build_graph,
    run,
)


def test_memory_provider_mount_and_submission_contract() -> None:
    run()


def test_normalized_openapi_matches_committed_evidence() -> None:
    graph = build_graph()
    contract = assert_openapi_parity(build_embedded_app(graph), build_direct_app())
    evidence_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "evidence"
        / "0.1"
        / "openapi.normalized.json"
    )
    expected = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert contract == expected
