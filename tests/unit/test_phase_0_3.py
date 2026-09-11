"""Focused tests for the Phase 0.3 public surfaces."""

from __future__ import annotations

import json

from etlantic.control_plane.memory import MemoryAuthorizer
from etlantic_fastapi.auth import principal_from_header, static_context_factory

from shuetl import (
    DoctorReport,
    LocalProviderBundle,
    ShuETLSettings,
)
from shuetl.cli import main


def test_settings_constructor_overrides_environment(monkeypatch) -> None:
    monkeypatch.setenv("SHUETL_API_PREFIX", "/from-env")
    settings = ShuETLSettings(api_prefix="/from-init")  # type: ignore[call-arg]
    assert settings.api_prefix == "/from-init"
    assert settings.model_dump() == {
        "profile": "local",
        "role": "gateway",
        "provider": "memory",
        "identity": "host",
        "api_prefix": "/from-init",
        "route_preset": "complete",
        "provider_connect_timeout_seconds": 2.0,
    }


def test_memory_bundle_uses_exact_upstream_stores_and_closes() -> None:
    bundle = LocalProviderBundle.create(
        ShuETLSettings(),  # type: ignore[call-arg]
        authorizer=MemoryAuthorizer(),
        context_factory=static_context_factory,  # type: ignore[arg-type]
        principal_dependency=principal_from_header,
    )
    try:
        assert bundle.provider == "memory"
        assert bundle.development_only is True
        assert bundle.api.definitions is bundle.definitions
        assert bundle.api.submissions is bundle.submissions
        assert bundle.api.events is bundle.events
        assert bundle.closed is False
    finally:
        bundle.close()
    bundle.close()
    assert bundle.closed is True


def test_doctor_json_is_stable_and_redacted() -> None:
    report = DoctorReport.inspect(
        ShuETLSettings(database_url=None),  # type: ignore[call-arg]
    )
    payload = json.loads(report.model_dump_json(by_alias=True))
    assert payload["schema"] == "shuetl.doctor/1"
    assert [check["id"] for check in payload["checks"]] == [
        "configuration.valid",
        "compatibility.core",
        "compatibility.etlantic_train",
        "provider.available",
        "provider.ready",
        "provider.schema",
        "identity.explicit",
        "role.supported",
        "routes.supported",
        "topology.development_only",
    ]
    assert "database_url" not in json.dumps(payload)


def test_cli_version_and_json(capsys) -> None:
    assert main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == "0.3.0"
    assert main(["doctor", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["schema"] == "shuetl.doctor/1"
