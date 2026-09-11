"""Executable blocker verification for the approved Phase 0.3 contract."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from etlantic.control_plane.memory import MemoryAuthorizer
from etlantic_fastapi.auth import principal_from_header, static_context_factory
from pydantic import ValidationError

import shuetl
from shuetl import (
    CapabilityError,
    LocalProviderBundle,
    ShuETLSettings,
    compatibility,
    providers,
)
from shuetl.cli import main
from shuetl.diagnostics import DoctorReport, _inspect_sqlite_schema

REQUIRED_SETTINGS = {
    "profile": "local",
    "role": "gateway",
    "provider": "memory",
    "identity": "host",
}


def _settings(**overrides: Any) -> ShuETLSettings:
    return ShuETLSettings(**(REQUIRED_SETTINGS | overrides))  # type: ignore[arg-type]


def _context_factory():
    return static_context_factory(tenant_id="tenant-a", workspace_id="workspace-a")


def test_sol_001_security_sensitive_settings_are_required() -> None:
    with pytest.raises(ValidationError):
        ShuETLSettings()  # type: ignore[call-arg]


def test_sol_001_lowercase_environment_names_are_not_consumed(monkeypatch) -> None:
    monkeypatch.setenv("shuetl_api_prefix", "/lowercase")
    assert _settings().api_prefix == "/etl"


def test_sol_001_database_value_is_absent_from_validation_errors() -> None:
    sentinel = "review-sentinel"
    with pytest.raises(ValidationError) as captured:
        _settings(
            provider="sqlite",
            database_url=f"sqlite:///database.db?token={sentinel}",
        )
    assert sentinel not in str(captured.value)


def test_sol_001_qualified_pysqlite_file_url_is_supported(tmp_path: Path) -> None:
    settings = _settings(
        provider="sqlite",
        database_url=f"sqlite+pysqlite:///{tmp_path / 'database.db'}",
    )
    assert settings.database_driver == "sqlite"


def test_sol_002_sqlite_inventory_includes_qualified_sqlalchemy(monkeypatch) -> None:
    sqlalchemy = SimpleNamespace(
        metadata={"Name": "sqlalchemy"},
        version="2.0.52",
    )
    monkeypatch.setattr(compatibility, "distributions", lambda: [sqlalchemy])
    versions = compatibility.installed_versions()
    assert versions["sqlalchemy"] == "2.0.52"


def test_sol_002_capability_errors_are_not_wrapped(monkeypatch) -> None:
    expected = 'pip install "shuetl[sqlite]==0.3.0"'
    monkeypatch.setattr(providers, "validate_core", lambda: {})

    def unavailable() -> None:
        raise CapabilityError(expected)

    monkeypatch.setattr(providers, "validate_sqlite", unavailable)
    with pytest.raises(CapabilityError, match="pip install"):
        LocalProviderBundle.create(
            _settings(provider="sqlite", database_url="sqlite:///missing.db"),
            authorizer=MemoryAuthorizer(),
            context_factory=_context_factory(),
            principal_dependency=principal_from_header,
        )


def test_sol_002_qualified_sqlite_bundle_constructs(tmp_path: Path) -> None:
    sqlmodel = pytest.importorskip("etlantic_sqlmodel")
    database = tmp_path / "qualified.db"
    database_url = f"sqlite:///{database}"
    engine = sqlmodel.create_sqlite_engine(database_url)
    try:
        sqlmodel.apply_migrations(engine)
    finally:
        engine.dispose()

    bundle = LocalProviderBundle.create(
        _settings(provider="sqlite", database_url=database_url),
        authorizer=MemoryAuthorizer(),
        context_factory=_context_factory(),
        principal_dependency=principal_from_header,
    )
    try:
        assert isinstance(bundle.definitions, sqlmodel.SQLModelDefinitionRepository)
        assert isinstance(bundle.submissions, sqlmodel.SQLModelSubmissionStore)
        assert isinstance(bundle.events, sqlmodel.SqlModelEventStore)
    finally:
        bundle.close()


def test_sol_003_doctor_schema_inspection_is_read_only(tmp_path: Path) -> None:
    pytest.importorskip("etlantic_sqlmodel")
    database = tmp_path / "empty.db"
    database.touch()
    settings = _settings(
        provider="sqlite",
        database_url=f"sqlite:///{database}",
    )

    _inspect_sqlite_schema(settings)

    with sqlite3.connect(database) as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    assert tables == []


def test_sol_003_bundle_schema_inspection_is_read_only(
    tmp_path: Path, monkeypatch
) -> None:
    pytest.importorskip("etlantic_sqlmodel")
    monkeypatch.setattr(providers, "validate_core", lambda: {})
    monkeypatch.setattr(providers, "validate_sqlite", lambda: {})
    database = tmp_path / "empty-bundle.db"
    database.touch()

    with pytest.raises(shuetl.ProviderReadinessError):
        LocalProviderBundle.create(
            _settings(
                provider="sqlite",
                database_url=f"sqlite:///{database}",
            ),
            authorizer=MemoryAuthorizer(),
            context_factory=_context_factory(),
            principal_dependency=principal_from_header,
        )

    with sqlite3.connect(database) as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    assert tables == []


@pytest.mark.parametrize(
    ("overrides", "argument"),
    [
        ({"authorizer": lambda: None}, "authorizer"),
        ({"context_factory": lambda: None}, "context_factory"),
        ({"principal_dependency": lambda: None}, "principal_dependency"),
    ],
)
def test_sol_004_wrong_adapter_shapes_fail_before_construction(
    overrides: dict[str, Any], argument: str
) -> None:
    arguments = {
        "authorizer": MemoryAuthorizer(),
        "context_factory": _context_factory(),
        "principal_dependency": principal_from_header,
    } | overrides
    with pytest.raises(TypeError, match=argument):
        LocalProviderBundle.create(_settings(), **arguments)  # type: ignore[arg-type]


def test_sol_004_settings_must_be_the_exact_public_type() -> None:
    with pytest.raises(TypeError, match="settings"):
        LocalProviderBundle.create(
            object(),  # type: ignore[arg-type]
            authorizer=MemoryAuthorizer(),
            context_factory=_context_factory(),
            principal_dependency=principal_from_header,
        )


def test_sol_005_public_export_order_matches_contract() -> None:
    assert shuetl.__all__ == (
        "ShuETL",
        "ShuETLSettings",
        "LocalProviderBundle",
        "DoctorReport",
        "DiagnosticCheck",
        "ShuETLError",
        "InvalidPrefixError",
        "MountConflictError",
        "CompatibilityError",
        "CapabilityError",
        "ProviderReadinessError",
    )


def test_sol_005_version_output_matches_contract(capsys) -> None:
    assert main(["--version"]) == 0
    assert capsys.readouterr().out == "shuetl 0.3.0\n"


def test_sol_005_doctor_text_contains_every_json_fact() -> None:
    report = DoctorReport.inspect(_settings())
    text = report.render_text()
    for fact in (
        "role: gateway",
        "identity: host",
        "api_prefix: /etl",
        "route_preset: complete",
        "database_configured: false",
        "database_driver: none",
        "etlantic: 0.51.0",
        "provider.memory",
        "Use a separately operated provider for production workloads.",
    ):
        assert fact in text


def test_sol_005_cli_redacts_unexpected_internal_errors(monkeypatch, capsys) -> None:
    sentinel = "review-internal-sentinel"

    def fail(cls):
        raise RuntimeError(sentinel)

    monkeypatch.setattr(DoctorReport, "inspect", classmethod(fail))
    assert main(["doctor"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert sentinel not in captured.err


def test_sol_006_release_verification_covers_phase_0_3_and_sqlite() -> None:
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/checks.yml").read_text(encoding="utf-8")
    clean_wheel = (root / "scripts/check_clean_wheel.py").read_text(encoding="utf-8")
    assert "Phase 0.2" not in workflow
    assert "shuetl-0.2-artifacts" not in workflow
    assert "docs/evidence/0.2" not in workflow
    assert "--extra sqlite" in workflow
    assert "phase_0_3_quickstart.py" in clean_wheel
    assert "[sqlite]" in clean_wheel


def test_sol_006_required_sqlite_example_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "examples/phase_0_3_sqlite.py").is_file()


def test_sol_007_readme_documents_the_complete_settings_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    readme = (root / "README.md").read_text(encoding="utf-8")
    for setting in (
        "SHUETL_PROFILE",
        "SHUETL_ROLE",
        "SHUETL_PROVIDER",
        "SHUETL_IDENTITY",
        "SHUETL_API_PREFIX",
        "SHUETL_ROUTE_PRESET",
        "SHUETL_DATABASE_URL",
        "SHUETL_PROVIDER_CONNECT_TIMEOUT_SECONDS",
    ):
        assert setting in readme
