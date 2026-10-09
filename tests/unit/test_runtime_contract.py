from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from shuetl import GatewayBindings, HostBindings, RuntimeBindings
from shuetl.backend import BackendRuntime
from shuetl.compatibility import CORE_REQUIREMENTS, POSTGRESQL_REQUIREMENTS
from shuetl.diagnostics import DoctorReport
from shuetl.probes import ProbeState, serve_probes
from shuetl.runtime import _close_when_drained
from shuetl.settings import ShuETLSettings


def _preview_settings(**overrides: object) -> ShuETLSettings:
    values: dict[str, object] = {
        "profile": "postgresql-preview",
        "role": "worker",
        "provider": "postgresql",
        "identity": "host",
        "database_url": "postgresql+psycopg://runtime:secret@db.example/shuetl",
        "bindings_factory": "host_bindings:create",
        "tenant_id": "tenant-a",
        "workspace_id": "workspace-a",
        "environment": "production",
        "security_domain": "domain-a",
    }
    values.update(overrides)
    return ShuETLSettings(**values)  # type: ignore[arg-type]


def test_preview_runtime_settings_require_host_scope_and_postgresql() -> None:
    assert _preview_settings().role == "worker"
    with pytest.raises(ValidationError, match="host-trusted bindings"):
        _preview_settings(identity="development-static")
    with pytest.raises(ValidationError, match="SHUETL_SECURITY_DOMAIN"):
        _preview_settings(security_domain=" ")
    with pytest.raises(ValidationError, match="SHUETL_WORKER_KIND"):
        _preview_settings(role="scheduler", worker_kind="actions")
    with pytest.raises(ValidationError, match="require the postgresql-preview"):
        _preview_settings(profile="local", provider="memory", database_url=None)


@pytest.mark.parametrize("role", ["gateway", "scheduler", "worker"])
def test_doctor_accepts_roles_supported_by_postgresql_preview(
    monkeypatch, role
) -> None:
    import shuetl.diagnostics as diagnostics

    versions = {**CORE_REQUIREMENTS, **POSTGRESQL_REQUIREMENTS}
    monkeypatch.setattr(diagnostics, "installed_versions", lambda: versions)
    monkeypatch.setattr(diagnostics, "validate_core", lambda: versions)
    monkeypatch.setattr(
        diagnostics,
        "inspect_postgresql",
        lambda _settings: SimpleNamespace(state="head", server_version="18.6"),
    )

    report = DoctorReport.inspect(_preview_settings(role=role))
    role_check = next(check for check in report.checks if check.id == "role.supported")
    assert role_check.status == "pass"
    assert report.status == "pass"


def test_binding_contracts_are_public_and_typed() -> None:
    assert HostBindings.__name__ == "HostBindings"
    assert GatewayBindings.__name__ == "GatewayBindings"
    assert RuntimeBindings.__name__ == "RuntimeBindings"
    assert "GatewayBindings" in __import__("shuetl").__all__


def test_probe_readiness_is_fresh_and_response_has_no_provider_details() -> None:
    state = ProbeState("run_worker")
    assert state.payload(False)[0] == 503
    state.update(
        state="running",
        provider_ready=True,
        runtime_ready=True,
        checked_at=time.monotonic(),
        reason=None,
    )
    status, response = state.payload(False)
    assert status == 200
    assert response == {
        "role": "run_worker",
        "process_state": "running",
        "reason_code": None,
        "ready": True,
    }
    state.max_age_seconds = 0
    assert state.payload(False)[0] == 503
    assert "database" not in str(state.payload(False)).lower()


def test_initial_role_tick_requires_fresh_provider_check_not_full_readiness() -> None:
    state = ProbeState("scheduler")
    assert not state.provider_available()
    state.update(
        state="running",
        provider_ready=True,
        runtime_ready=False,
        checked_at=time.monotonic(),
        reason="prerequisites_unavailable",
    )
    assert state.payload(False)[0] == 503
    assert state.provider_available()
    state.max_age_seconds = 0
    assert not state.provider_available()


def test_probe_listener_binds_loopback_and_serves_health() -> None:
    state = ProbeState("gateway")
    server = serve_probes(state, 0)
    try:
        assert server.server_address[0] == "127.0.0.1"
        ready_url = f"http://127.0.0.1:{server.server_port}/ready"
        with pytest.raises(urllib.error.HTTPError) as response:
            urllib.request.urlopen(ready_url, timeout=2)
        assert response.value.code == 503
        state.update(
            state="running",
            provider_ready=True,
            runtime_ready=True,
            checked_at=time.monotonic(),
            reason=None,
        )
        with urllib.request.urlopen(ready_url, timeout=2) as response:
            assert response.status == 200
        with pytest.raises(urllib.error.HTTPError) as response:
            urllib.request.urlopen(
                f"http://127.0.0.1:{server.server_port}/unexpected", timeout=2
            )
        assert response.value.code == 404
    finally:
        server.shutdown()
        server.server_close()


def test_package_import_does_not_load_gateway_or_provider_stack() -> None:
    root = Path(__file__).resolve().parents[2]
    output = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "import sys, shuetl; "
            "assert 'fastapi' not in sys.modules; "
            "assert 'etlantic_fastapi' not in sys.modules; "
            "assert 'etlantic_sqlmodel' not in sys.modules",
        ],
        cwd=root,
        text=True,
    )
    assert output == ""


def test_backend_cleanup_waits_for_drain_and_closes_once() -> None:
    calls: list[str] = []

    class Role:
        remaining = 1

        def request_drain(self) -> None:
            calls.append("drain")
            self.remaining = 0

        def status(self) -> SimpleNamespace:
            return SimpleNamespace(in_flight=self.remaining)

    class Backend:
        def close(self) -> None:
            calls.append("backend")

    class Bindings:
        def close(self) -> None:
            calls.append("bindings")

    runtime = BackendRuntime(
        settings=_preview_settings(),
        bindings=Bindings(),  # type: ignore[arg-type]
        backend=Backend(),
        role_handle=Role(),
        context=object(),
    )
    _close_when_drained(runtime)
    runtime.close()
    assert calls == ["drain", "backend", "bindings"]
