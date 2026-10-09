"""Failure-path regressions for trusted bindings and owned resources."""

from __future__ import annotations

import sys
from dataclasses import replace
from types import ModuleType

import pytest
from etlantic.control_plane import (
    ControlPlaneContext,
    EnvironmentRef,
    MemoryAuthorizer,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic.profile import Profile
from tests.unit.test_runtime_contract import _preview_settings

from shuetl import cli
from shuetl import runtime as runtime_module
from shuetl.backend import BackendRuntime
from shuetl.bindings import GatewayBindings, RuntimeBindings
from shuetl.errors import ProviderReadinessError
from shuetl.factory import load_bindings
from shuetl.identity import HostIdentityAdapter


def bindings(**overrides):
    return RuntimeBindings(
        authorizer=MemoryAuthorizer(),
        profile=Profile(
            "test", security_mode="production", plugin_allowlist={"etlantic": "0.57.0"}
        ),
        planning_context_factory=lambda ctx, profile: None,  # type: ignore[arg-type]
        context=ControlPlaneContext(
            Principal("worker", kind="service"),
            TenantRef("tenant-a"),
            WorkspaceRef("tenant-a", "workspace-a"),
            EnvironmentRef("production"),
            SecurityDomain("domain-a"),
        ),
        **overrides,
    )


def install_factory(monkeypatch, factory):
    module = ModuleType("review_host")
    module.create = factory  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, module.__name__, module)
    return _preview_settings(bindings_factory="review_host:create")


@pytest.mark.parametrize("role", ["gateway", "worker"])
def test_wrong_role_binding_closes_host_resources(monkeypatch, role):
    calls = []
    value = bindings(close=lambda: calls.append("closed"))
    if role == "worker":
        value = GatewayBindings(
            authorizer=value.authorizer,
            profile=value.profile,
            planning_context_factory=value.planning_context_factory,
            identity_adapter=None,
            close=value.close,
        )
    settings = install_factory(monkeypatch, lambda settings: value)
    with pytest.raises(ProviderReadinessError, match="requires"):
        load_bindings(
            "review_host:create",
            _preview_settings(bindings_factory=settings.bindings_factory, role=role),
        )
    assert calls == ["closed"]


def test_malformed_context_also_closes_host_resources(monkeypatch):
    calls = []
    value = bindings(close=lambda: calls.append("closed"))
    value = replace(value, context=replace(value.context, security_domain=None))
    settings = install_factory(monkeypatch, lambda settings: value)
    with pytest.raises(ProviderReadinessError, match="context"):
        load_bindings("review_host:create", settings)
    assert calls == ["closed"]


def test_gateway_rejects_development_identity_adapter(monkeypatch):
    calls = []
    value = bindings()
    gateway = GatewayBindings(
        authorizer=value.authorizer,
        profile=value.profile,
        planning_context_factory=value.planning_context_factory,
        identity_adapter=HostIdentityAdapter.development_static(
            principal=Principal("local-user", issuer="local-issuer", kind="human"),
            tenant_id="tenant-a",
            workspace_id="workspace-a",
        ),
        close=lambda: calls.append("closed"),
    )
    settings = install_factory(monkeypatch, lambda settings: gateway)
    with pytest.raises(ProviderReadinessError, match="production host-mode"):
        load_bindings(
            "review_host:create",
            _preview_settings(
                bindings_factory=settings.bindings_factory, role="gateway"
            ),
        )
    assert calls == ["closed"]


def test_gateway_rejects_invalid_planning_factory_signature(monkeypatch):
    calls = []
    value = bindings()
    gateway = GatewayBindings(
        authorizer=value.authorizer,
        profile=value.profile,
        planning_context_factory=lambda ctx: None,  # type: ignore[call-arg]
        identity_adapter=HostIdentityAdapter.create(
            principal_dependency=lambda: Principal("alice"),
            context_factory=lambda principal, request: value.context,
        ),
        close=lambda: calls.append("closed"),
    )
    settings = install_factory(monkeypatch, lambda settings: gateway)
    settings = _preview_settings(
        bindings_factory=settings.bindings_factory, role="gateway"
    )

    with pytest.raises(
        ProviderReadinessError, match="planning context factory must accept"
    ):
        load_bindings("review_host:create", settings)

    assert calls == ["closed"]


def test_bindings_reject_close_callback_that_requires_arguments(monkeypatch):
    calls = []

    def close(required):
        calls.append(required)

    settings = install_factory(monkeypatch, lambda settings: bindings(close=close))

    with pytest.raises(
        ProviderReadinessError, match="binding close callback must accept no arguments"
    ):
        load_bindings("review_host:create", settings)

    assert calls == []


@pytest.mark.parametrize("source", ["factory", "import", "serve"])
def test_cli_redacts_host_failures(monkeypatch, capsys, source):
    sentinel = "REVIEW_SECRET_SENTINEL"

    def fail(*args, **kwargs):
        raise ValueError(sentinel)

    settings = install_factory(monkeypatch, fail)
    monkeypatch.setattr("shuetl.settings.ShuETLSettings", lambda: settings)
    if source == "import":
        monkeypatch.setattr("shuetl.factory.importlib.import_module", fail)
    elif source == "serve":
        monkeypatch.setattr("shuetl.runtime.serve", fail)
    assert cli.main(["serve", "--role", "worker"]) == 1
    captured = capsys.readouterr()
    assert sentinel not in captured.out + captured.err
    assert captured.err


def test_failed_close_preserves_resources_and_can_be_retried():
    calls = []

    class Backend:
        active = True

        def close(self):
            if self.active:
                raise RuntimeError("roles are active")
            calls.append("backend")

    backend = Backend()
    runtime = BackendRuntime(
        settings=_preview_settings(),
        bindings=bindings(close=lambda: calls.append("host")),
        backend=backend,
        role_handle=None,
        context=None,
    )
    with pytest.raises(RuntimeError):
        runtime.close()
    assert not runtime.closed
    assert calls == []
    backend.active = False
    runtime.close()
    runtime.close()
    assert runtime.closed
    assert calls == ["backend", "host"]


def test_serve_returns_failure_when_runtime_cleanup_fails(monkeypatch):
    host_bindings = bindings()

    class Backend:
        def close(self):
            raise RuntimeError("active role")

    settings = _preview_settings(bindings_factory="review_host:create")
    runtime = BackendRuntime(
        settings=settings,
        bindings=host_bindings,
        backend=Backend(),
        role_handle=None,
        context=None,
    )
    monkeypatch.setattr(
        runtime_module, "load_bindings", lambda _path, _settings: host_bindings
    )
    monkeypatch.setattr(
        runtime_module, "create_backend_runtime", lambda _settings, _bindings: runtime
    )
    monkeypatch.setattr(runtime_module, "_serve_worker", lambda _runtime: 0)
    monkeypatch.setattr("shuetl.compatibility.validate_core", lambda: {})
    monkeypatch.setattr("shuetl.compatibility.validate_postgresql", lambda: {})

    assert runtime_module.serve(settings) == 1


def test_action_handler_mapping_is_frozen_at_factory_boundary(monkeypatch):
    async def handler(ctx, request):
        return {"connected": True}

    handlers = {"connector.test": handler}
    settings = install_factory(
        monkeypatch, lambda settings: bindings(action_handlers=handlers)
    )
    result = load_bindings("review_host:create", settings)
    handlers.clear()
    assert isinstance(result, RuntimeBindings)
    assert result.action_handlers == {"connector.test": handler}
    with pytest.raises(TypeError):
        result.action_handlers["connector.test"] = handler  # type: ignore[index]


def test_invalid_handler_configuration_closes_host_resources(monkeypatch):
    calls = []
    settings = install_factory(
        monkeypatch,
        lambda settings: bindings(
            action_handlers=None, close=lambda: calls.append("host")
        ),
    )
    with pytest.raises(ProviderReadinessError, match="mapping"):
        load_bindings("review_host:create", settings)
    assert calls == ["host"]
