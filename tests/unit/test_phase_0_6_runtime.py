"""Contract coverage for the ETLantic 0.56 role runtime."""

from __future__ import annotations

import json
import socket
import threading
import time
import types
from collections.abc import Mapping
from dataclasses import replace
from typing import Any, Literal, cast
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest
from etlantic.control_plane import (
    ControlPlaneContext,
    EnvironmentRef,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic.control_plane.memory import MemoryAuthorizer
from etlantic.profile import Profile
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from shuetl import HostIdentityAdapter, ShuETLSettings, supervisor
from shuetl import runtime as runtime_module
from shuetl.errors import ProviderReadinessError
from shuetl.postgresql import POSTGRESQL_HEAD, PostgreSQLSchemaStatus
from shuetl.runtime import (
    HostRuntimeBindings,
    ManagedRuntime,
    _matches_configured_scope,
    _scoped_identity_adapter,
    _validate_bindings,
    build_managed_runtime,
)

DATABASE_URL = "postgresql+psycopg://shuetl:sentinel-secret@db.example/control"


def _context(
    *,
    kind: Literal["human", "service", "workload"] = "service",
    tenant_id: str = "tenant-a",
    workspace_id: str = "workspace-a",
) -> ControlPlaneContext:
    return ControlPlaneContext(
        principal=Principal(subject="phase06-runtime", kind=kind),
        tenant=TenantRef(tenant_id=tenant_id),
        workspace=WorkspaceRef(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        ),
        environment=EnvironmentRef(name="production"),
        security_domain=SecurityDomain(domain_id="default"),
    )


def _settings(role: str = "gateway", **overrides: Any) -> ShuETLSettings:
    values = {
        "profile": "postgresql-preview",
        "role": role,
        "provider": "postgresql",
        "identity": "host",
        "database_url": DATABASE_URL,
        "factory": "phase06_test_host:build",
        "store_id": "shared-control-store",
        "tenant_id": "tenant-a",
        "workspace_id": "workspace-a",
        "execution_profile": "production",
        "probe_port": 9131 if role != "gateway" else 9130,
    }
    values.update(overrides)
    return ShuETLSettings(**values)


def _host_identity(context: ControlPlaneContext | None = None) -> HostIdentityAdapter:
    principal = Principal(subject="verified-user", issuer="https://id.example")
    return HostIdentityAdapter.create(
        principal_dependency=lambda: principal,
        context_factory=lambda authenticated, _request: replace(
            context or _context(kind="human"), principal=authenticated
        ),
    )


def test_preview_settings_are_role_scoped_and_keep_secrets_out_of_repr() -> None:
    gateway = _settings()
    assert gateway.profile == "postgresql-preview"
    assert gateway.role == "gateway"
    assert DATABASE_URL not in repr(gateway)

    scheduler = _settings("scheduler")
    assert scheduler.probe_port == 9131

    worker = _settings("worker", worker_kind="actions")
    assert worker.worker_kind == "actions"

    with pytest.raises(ValidationError, match="gateway-only"):
        ShuETLSettings(
            profile="postgresql-pilot",
            role="worker",
            provider="postgresql",
            identity="host",
            database_url=DATABASE_URL,
        )

    with pytest.raises(ValidationError, match="probe_port and gateway_port"):
        _settings(probe_port=8000, gateway_port=8000)

    with pytest.raises(ValidationError, match="factory"):
        _settings(factory="not-a-callable")


def test_preview_context_is_service_scoped_and_rejects_gateway_bindings() -> None:
    scheduler = _settings("scheduler")
    bindings = HostRuntimeBindings(
        authorizer=MemoryAuthorizer(),
        service_context=_context(),
    )
    _validate_bindings(scheduler, bindings)
    assert bindings.service_context is not None
    assert _matches_configured_scope(scheduler, bindings.service_context)

    wrong_scope = HostRuntimeBindings(
        authorizer=MemoryAuthorizer(),
        service_context=_context(tenant_id="tenant-other"),
    )
    with pytest.raises(ProviderReadinessError, match="configured scope"):
        _validate_bindings(scheduler, wrong_scope)

    gateway_with_service = HostRuntimeBindings(
        authorizer=MemoryAuthorizer(),
        identity_adapter=_host_identity(),
        service_context=_context(),
    )
    with pytest.raises(ProviderReadinessError, match="cannot contain"):
        _validate_bindings(_settings(), gateway_with_service)


def test_gateway_identity_is_constrained_to_one_configured_scope() -> None:
    settings = _settings()
    adapter = _scoped_identity_adapter(
        settings,
        HostRuntimeBindings(
            authorizer=MemoryAuthorizer(),
            identity_adapter=_host_identity(_context(kind="human")),
        ),
    )
    assert adapter is not None
    principal = Principal(subject="verified-user", issuer="https://id.example")
    assert (
        adapter.context_factory(principal, cast(Any, object())).tenant.tenant_id
        == "tenant-a"
    )

    outside = _scoped_identity_adapter(
        settings,
        HostRuntimeBindings(
            authorizer=MemoryAuthorizer(),
            identity_adapter=_host_identity(
                _context(kind="human", tenant_id="tenant-other")
            ),
        ),
    )
    assert outside is not None
    with pytest.raises(Exception, match="configured preview scope"):
        outside.context_factory(principal, cast(Any, object()))


class _FakeEngine:
    def __init__(self) -> None:
        self.dispose_count = 0

    def dispose(self) -> None:
        self.dispose_count += 1


class _FakeBackend:
    def __init__(self, api: Any, execution_profile: str) -> None:
        self.api = api
        self.engine = _FakeEngine()
        self.execution_profile = execution_profile
        self.close_count = 0

    def close(self) -> None:
        self.close_count += 1

    def create_execution_host(self, **kwargs: Any) -> object:
        self.execution_host_kwargs = kwargs
        return object()

    def create_action_execution_host(self, **kwargs: Any) -> object:
        self.action_host_kwargs = kwargs
        return object()


class _FakeManagedService:
    def submit_scheduled_run(self, *_args: Any) -> tuple[str, str]:
        return "submission", "run"


def _patch_backend(
    monkeypatch: pytest.MonkeyPatch,
    api: Any,
    *,
    backend: _FakeBackend,
) -> dict[str, Any]:
    monkeypatch.setattr(runtime_module, "validate_postgresql", lambda: {})
    monkeypatch.setattr(
        runtime_module,
        "resolve_profile",
        lambda _profile, **_kwargs: Profile(
            name="phase06-test", security_mode="development"
        ),
    )
    monkeypatch.setattr(
        runtime_module, "create_postgresql_engine", lambda _s: _FakeEngine()
    )
    monkeypatch.setattr(
        runtime_module,
        "inspect_postgresql_engine",
        lambda _engine: PostgreSQLSchemaStatus("head", POSTGRESQL_HEAD, "18.6"),
    )
    monkeypatch.setattr(
        runtime_module, "_load_bindings", lambda _settings: api.bindings
    )

    config_seen: dict[str, Any] = {}

    def create(config: Any, **kwargs: Any) -> _FakeBackend:
        config_seen["config"] = config
        config_seen.update(kwargs)
        return backend

    import importlib

    managed_module = importlib.import_module("etlantic_fastapi.managed")
    monkeypatch.setattr(managed_module, "create_managed_backend", create)
    return config_seen


def test_role_builder_uses_shared_headless_backend_and_bound_scheduler_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scheduler_service_calls: dict[str, Any] = {}

    class SchedulerServiceProbe:
        def __init__(self, schedule_store: Any, **kwargs: Any) -> None:
            scheduler_service_calls["schedule_store"] = schedule_store
            scheduler_service_calls.update(kwargs)

    service = _FakeManagedService()
    api = types.SimpleNamespace(
        managed_service=service,
        schedule_store=object(),
        durable_work=object(),
    )
    bindings = HostRuntimeBindings(
        authorizer=MemoryAuthorizer(),
        service_context=_context(),
    )
    api.bindings = bindings
    backend = _FakeBackend(api, "phase06-test")
    config_seen = _patch_backend(monkeypatch, api, backend=backend)
    from etlantic.runtime import scheduler_service as scheduler_module

    monkeypatch.setattr(scheduler_module, "SchedulerService", SchedulerServiceProbe)

    runtime = build_managed_runtime(_settings("scheduler"))
    try:
        callback = scheduler_service_calls["run_submitter"]
        assert callback == service.submit_scheduled_run
        assert getattr(callback, "__self__", None) is service
        assert scheduler_service_calls["schedule_store"] is api.schedule_store
        assert scheduler_service_calls["durable"] is api.durable_work
        assert scheduler_service_calls["profile"] == "phase06-test"
        config = config_seen["config"]
        assert config.store_id == "shared-control-store"
        assert config.profile.name == "phase06-test"
        assert config.database_url == DATABASE_URL
    finally:
        runtime.close()
        runtime.close()
    assert backend.close_count == 1


def test_action_worker_requires_external_handlers_and_uses_upstream_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def action_handler(
        _context: ControlPlaneContext, payload: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        return {"accepted": bool(payload)}

    handlers = {"connector.test": action_handler}
    bindings = HostRuntimeBindings(
        authorizer=MemoryAuthorizer(),
        service_context=_context(),
        action_handlers=handlers,
    )
    with pytest.raises(ProviderReadinessError, match="provider handlers"):
        _validate_bindings(
            _settings("worker", worker_kind="actions"),
            HostRuntimeBindings(
                authorizer=MemoryAuthorizer(), service_context=_context()
            ),
        )

    api = types.SimpleNamespace(
        managed_service=_FakeManagedService(),
        schedule_store=object(),
        durable_work=object(),
    )
    api.bindings = bindings
    backend = _FakeBackend(api, "production")
    config_seen = _patch_backend(monkeypatch, api, backend=backend)
    runtime = build_managed_runtime(_settings("worker", worker_kind="actions"))
    try:
        assert runtime.service is not None
        assert backend.action_host_kwargs["worker_id"].startswith("worker-process-")
        assert config_seen["config"].action_handlers == handlers
    finally:
        runtime.close()


def test_probe_lifecycle_reports_outage_drain_and_stale_state_without_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [100.0]
    monkeypatch.setattr(supervisor.time, "monotonic", lambda: now[0])
    state = supervisor._ProbeState("worker", stale_after=4.0)

    status, body = state.snapshot("/ready")
    assert status == 503
    assert json.loads(body)["state"] == "starting"

    state.provider_result(True, "ready")
    state.mark_running()
    assert state.snapshot("/live")[0] == 200
    assert state.snapshot("/ready")[0] == 200

    state.provider_result(False, "schema_corrupt")
    status, body = state.snapshot("/ready")
    assert status == 503
    assert json.loads(body)["reason"] == "schema_corrupt"
    assert b"sentinel-secret" not in body

    state.provider_result(True, "ready")
    now[0] += 5.0
    status, body = state.snapshot("/ready")
    assert status == 503
    assert json.loads(body)["reason"] == "supervisor_stale"

    state.mark_draining()
    assert state.snapshot("/live")[0] == 503
    state.mark_failed("runtime_tick_failed")
    assert state.snapshot("/live")[0] == 503


def test_runtime_ticks_wait_for_provider_and_classifies_database_errors() -> None:
    calls: list[str] = []
    stop = threading.Event()
    failed = threading.Event()
    settings = _settings("scheduler", runtime_poll_interval_seconds=0.1)

    class Service:
        def tick(self, _context: ControlPlaneContext) -> None:
            calls.append("tick")
            stop.set()

    runtime = ManagedRuntime(
        settings=settings,
        bindings=HostRuntimeBindings(
            authorizer=MemoryAuthorizer(),
            service_context=_context(),
        ),
        backend=object(),
        service=Service(),
        context=_context(),
    )
    state = supervisor._ProbeState("scheduler", stale_after=1.0)
    state.mark_running()
    thread = threading.Thread(
        target=supervisor._run_ticks,
        args=(runtime, state, stop, failed),
    )
    thread.start()
    time.sleep(0.04)
    assert calls == []
    state.provider_result(True, "ready")
    thread.join(timeout=1)
    assert not thread.is_alive()
    assert calls == ["tick"]
    assert not failed.is_set()

    from sqlalchemy.exc import OperationalError

    assert supervisor._is_database_error(OperationalError("query", {}, Exception()))
    assert not supervisor._is_database_error(RuntimeError("secret-free failure"))


def test_gateway_gates_requests_until_provider_recovers_and_serves_local_probes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        probe_port = listener.getsockname()[1]

    settings = _settings(
        probe_port=probe_port,
        probe_refresh_seconds=0.1,
        probe_stale_after_seconds=1.0,
    )
    app = FastAPI()

    @app.get("/protected")
    def protected() -> dict[str, str]:
        return {"ok": "yes"}

    @app.get("/etl/health")
    def upstream_health() -> dict[str, str]:
        return {"status": "ok"}

    backend = _FakeBackend(types.SimpleNamespace(), "production")
    closed: list[bool] = []
    bindings = HostRuntimeBindings(
        authorizer=MemoryAuthorizer(),
        close=lambda: closed.append(True),
    )
    runtime = ManagedRuntime(settings, bindings, backend, app=app)
    status = [
        PostgreSQLSchemaStatus("unreachable", None, None),
        PostgreSQLSchemaStatus("head", POSTGRESQL_HEAD, "18.6"),
    ]
    inspections = 0

    def inspect(_engine: Any) -> PostgreSQLSchemaStatus:
        nonlocal inspections
        value = status[min(inspections, len(status) - 1)]
        inspections += 1
        return value

    monkeypatch.setattr(supervisor, "inspect_postgresql_engine", inspect)

    class FakeConfig:
        def __init__(self, application: FastAPI, **_kwargs: Any) -> None:
            self.app = application

    class FakeServer:
        def __init__(self, config: FakeConfig) -> None:
            self.config = config
            self.started = False

        def run(self) -> None:
            self.started = True
            with TestClient(self.config.app) as client:
                assert client.get("/etl/health").json() == {"status": "ok"}
                deadline = time.monotonic() + 2.0
                saw_not_ready = False
                while time.monotonic() < deadline:
                    response = client.get("/protected")
                    if response.status_code == 503:
                        saw_not_ready = True
                    if response.status_code == 200:
                        assert saw_not_ready
                        assert response.json() == {"ok": "yes"}
                        break
                    time.sleep(0.01)
                else:
                    raise AssertionError("gateway did not become ready")

            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                try:
                    with urlopen(
                        f"http://127.0.0.1:{probe_port}/ready", timeout=0.2
                    ) as response:
                        if response.status == 200:
                            return
                except HTTPError as exc:
                    if exc.code != 503:
                        raise
                time.sleep(0.01)
            raise AssertionError("gateway readiness probe did not recover")

        def handle_exit(self, _sig: int, _frame: Any) -> None:
            return None

    import uvicorn

    monkeypatch.setattr(uvicorn, "Config", FakeConfig)
    monkeypatch.setattr(uvicorn, "Server", FakeServer)

    assert supervisor.serve_gateway(runtime) == 0
    assert inspections >= 2
    assert backend.close_count == 1
    assert closed == [True]
