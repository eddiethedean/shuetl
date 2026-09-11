"""Executable blocker verification for the approved Phase 0.3 contract."""

from __future__ import annotations

import re
import runpy
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal, get_type_hints

import pytest
from etlantic.control_plane import DefinitionRepository, EventStore, SubmissionStore
from etlantic.control_plane.memory import MemoryAuthorizer, MemoryDefinitionRepository
from etlantic_fastapi.auth import principal_from_header, static_context_factory
from fastapi.testclient import TestClient
from pydantic import ValidationError
from scripts import check_clean_wheel

import shuetl
from shuetl import (
    CapabilityError,
    LocalProviderBundle,
    ShuETLSettings,
    compatibility,
    diagnostics,
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


def test_sol_005_sqlite_doctor_reports_sqlalchemy_version(
    tmp_path: Path, monkeypatch
) -> None:
    versions = {
        "shuetl": "0.3.0",
        "etlantic": "0.51.0",
        "etlantic-fastapi": "0.51.0",
        "etlantic-sqlmodel": "0.51.0",
        "fastapi": "0.141.1",
        "pydantic": "2.13.5",
        "pydantic-settings": "2.15.0",
        "sqlalchemy": "2.0.52",
    }
    monkeypatch.setattr(diagnostics, "installed_versions", lambda: versions)
    monkeypatch.setattr(diagnostics, "validate_core", lambda: versions)
    report = DoctorReport.inspect(
        _settings(
            provider="sqlite",
            database_url=f"sqlite:///{tmp_path / 'missing.db'}",
        )
    )
    assert report.versions["etlantic-sqlmodel"] == "0.51.0"
    assert report.versions["sqlalchemy"] == "2.0.52"


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


def test_sol_006_memory_quickstart_uses_owned_definition_and_host_identity(
    monkeypatch,
) -> None:
    root = Path(__file__).resolve().parents[2]
    definitions: list[str] = []
    requests: list[tuple[str, dict[str, str]]] = []
    original_put = MemoryDefinitionRepository.put
    original_get = TestClient.get

    def record_put(
        self,
        ctx,
        definition_id: str,
        document: dict[str, Any],
    ) -> None:
        definitions.append(definition_id)
        original_put(self, ctx, definition_id, document)

    def record_get(self, url: str, **kwargs: Any):
        requests.append((url, kwargs.get("headers", {})))
        return original_get(self, url, **kwargs)

    monkeypatch.setattr(MemoryDefinitionRepository, "put", record_put)
    monkeypatch.setattr(TestClient, "get", record_get)
    runpy.run_path(str(root / "examples/phase_0_3_quickstart.py"), run_name="__main__")

    assert definitions
    assert any(
        url.startswith("/etl/v1/") and headers.get("X-Principal") == "alice"
        for url, headers in requests
    )


def test_sol_006_sqlite_example_leaves_file_creation_to_upstream(
    monkeypatch,
) -> None:
    root = Path(__file__).resolve().parents[2]

    def reject_direct_touch(self, *args: Any, **kwargs: Any) -> None:
        raise AssertionError("SQLite example directly creates the database file")

    monkeypatch.setattr(Path, "touch", reject_direct_touch)
    runpy.run_path(str(root / "examples/phase_0_3_sqlite.py"), run_name="__main__")


def test_sol_006_clean_wheel_uses_separate_core_and_sqlite_environments(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[list[str]] = []

    def record(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
        del cwd, env
        calls.append(command)

    monkeypatch.setattr(check_clean_wheel.shutil, "which", lambda name: "/usr/bin/uv")
    monkeypatch.setattr(check_clean_wheel, "_run", record)
    check_clean_wheel.verify(tmp_path / "shuetl-0.3.0-py3-none-any.whl")

    venv_commands = [command for command in calls if command[1:2] == ["venv"]]
    memory_run = next(
        command for command in calls if command[-1].endswith("phase_0_3_quickstart.py")
    )
    sqlite_run = next(
        command for command in calls if command[-1].endswith("phase_0_3_sqlite.py")
    )
    assert len(venv_commands) == 2
    assert memory_run[0] != sqlite_run[0]


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


def test_sol_007_readme_documents_doctor_status_and_exit_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    readme = (root / "README.md").read_text(encoding="utf-8").lower()
    for fact in ("pass", "warn", "fail", "skip", "remediation"):
        assert fact in readme
    for code in (0, 1, 2):
        assert re.search(rf"exit(?: code)?\s+`?{code}`?", readme)


def test_sol_008_bundle_public_annotations_match_the_typed_contract() -> None:
    hints = get_type_hints(LocalProviderBundle)
    assert hints["definitions"] is DefinitionRepository
    assert hints["submissions"] is SubmissionStore
    assert hints["events"] is EventStore
    assert hints["provider"] == Literal["memory", "sqlite"]
    assert hints["development_only"] == Literal[True]
