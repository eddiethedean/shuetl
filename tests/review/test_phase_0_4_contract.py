"""Sol blocker verification for the approved Phase 0.4 contract."""

from __future__ import annotations

import re
from asyncio import CancelledError
from pathlib import Path
from unittest.mock import Mock

import pytest
from etlantic.control_plane import Principal
from etlantic.control_plane.memory import MemoryAuthorizer
from etlantic_fastapi.auth import static_context_factory
from fastapi import Request

from shuetl import (
    HostIdentityAdapter,
    PostgreSQLProviderBundle,
    ShuETLSettings,
    diagnostics,
    providers,
)
from shuetl.compatibility import CORE_REQUIREMENTS, POSTGRESQL_REQUIREMENTS
from shuetl.diagnostics import DoctorReport
from shuetl.postgresql import POSTGRESQL_HEAD, PostgreSQLSchemaStatus

ROOT = Path(__file__).resolve().parents[2]


def _review_principal(_request: Request) -> Principal:
    return Principal(subject="review", issuer="https://review.example")


def _review_identity() -> HostIdentityAdapter:
    return HostIdentityAdapter.create(
        principal_dependency=_review_principal,
        context_factory=static_context_factory(
            tenant_id="review", workspace_id="review"
        ),
    )


def _settings() -> ShuETLSettings:
    return ShuETLSettings(
        profile="postgresql-pilot",
        role="gateway",
        provider="postgresql",
        identity="host",
        database_url="postgresql+psycopg://review:sentinel@invalid.example/pilot",
        postgresql_sslmode="disable",
    )


def test_phase_0_5_evidence_matches_current_ac_meanings() -> None:
    """A recycled PASS ledger is not proof of the current acceptance contract."""
    index = (ROOT / "docs/evidence/0.5/README.md").read_text()
    rows = re.findall(r"^\| (AC-\d{3}) \| (.+)$", index, re.MULTILINE)
    assert len(rows) == 34
    assert len(dict(rows)) == 34
    # Distinct identity, route, upstream, and release proof obligations.
    required_proof_topics = {
        "AC-001": ("metadata", "lock"),
        "AC-016": ("mutation", "route"),
        "AC-020": ("concurrent", "principal"),
        "AC-021": ("sse", "cursor"),
        "AC-024": ("trigger", "identity"),
        "AC-028": ("host", "recipe"),
        "AC-031": ("release", "matrix"),
        "AC-032": ("evidence", "proof"),
        "AC-033": ("list", "denial"),
        "AC-034": ("validation", "redaction"),
    }
    proofs = {
        criterion: " ".join(cells.split("|")[:3]).lower() for criterion, cells in rows
    }
    mismatches = [
        criterion
        for criterion, topics in required_proof_topics.items()
        if not all(topic in proofs[criterion] for topic in topics)
    ]
    assert not mismatches, f"Evidence maps unrelated proof to {mismatches}"


def test_sol_011_bundle_definitions_are_the_api_definitions(monkeypatch) -> None:
    """Isolate graph wiring; database readiness is a separate contract."""
    sqlalchemy = pytest.importorskip("sqlalchemy")
    pytest.importorskip("etlantic_sqlmodel")
    engine = sqlalchemy.create_engine("sqlite://")
    monkeypatch.setattr(providers, "create_postgresql_engine", lambda _: engine)
    monkeypatch.setattr(
        providers,
        "inspect_postgresql_engine",
        lambda _: PostgreSQLSchemaStatus("head", POSTGRESQL_HEAD, "18.6"),
    )
    bundle = PostgreSQLProviderBundle.create(
        _settings(),
        authorizer=MemoryAuthorizer(),
        identity_adapter=_review_identity(),
    )
    try:
        assert bundle.api.definitions is bundle.definitions
    finally:
        bundle.close()


def test_sol_012_explicit_insecure_tls_mode_is_visible_in_both_formats(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        diagnostics,
        "inspect_postgresql",
        lambda _: PostgreSQLSchemaStatus("head", POSTGRESQL_HEAD, "18.6"),
    )
    report = DoctorReport.inspect(_settings())
    # Keep doctor/1 fields and check IDs: the mode can be a bounded check fact.
    assert "disable" in report.model_dump_json(by_alias=True)
    assert "disable" in report.render_text()
    assert "sentinel" not in report.model_dump_json(by_alias=True)


def test_sol_012_configured_capabilities_do_not_depend_on_installed_extras(
    monkeypatch,
) -> None:
    versions: dict[str, str | None] = dict(CORE_REQUIREMENTS)
    versions.update(dict.fromkeys(POSTGRESQL_REQUIREMENTS))
    monkeypatch.setattr(diagnostics, "installed_versions", lambda: versions)

    def forbidden_connection(_):
        pytest.fail("Missing-extra diagnostics must not connect")

    monkeypatch.setattr(diagnostics, "inspect_postgresql", forbidden_connection)
    report = DoctorReport.inspect(_settings())
    assert report.status == "fail"
    assert "provider.postgresql" not in report.available_capabilities
    assert {
        "control-plane.registry",
        "control-plane.revisions",
        "control-plane.durable-work",
        "control-plane.schedules",
        "control-plane.firings",
    } <= set(report.configured_capabilities)


def test_sol_013_operator_documentation_explains_restore_admission() -> None:
    """An implementation plan is not an operator restore runbook (AC-035)."""
    operator_docs = [ROOT / "README.md"]
    operator_docs.extend(
        path
        for path in (ROOT / "docs").rglob("*.md")
        if not {"plans", "evidence", "reviews"}.intersection(path.parts)
    )
    text = "\n".join(path.read_text() for path in operator_docs).lower()
    assert "restore" in text, "No operator-facing PostgreSQL restore procedure"
    assert "readiness" in text or "doctor" in text
    assert "traffic" in text, "Restore must be checked before admitting traffic"


def test_sol_014_cancelled_construction_disposes_engine_once(monkeypatch) -> None:
    engine = Mock()
    monkeypatch.setattr(providers, "create_postgresql_engine", lambda _: engine)

    def cancelled(_):
        raise CancelledError()

    monkeypatch.setattr(providers, "inspect_postgresql_engine", cancelled)
    with pytest.raises(CancelledError):
        PostgreSQLProviderBundle.create(
            _settings(),
            authorizer=MemoryAuthorizer(),
            identity_adapter=_review_identity(),
        )
    engine.dispose.assert_called_once_with()
