"""Unit contracts for ShuETL's host identity composition boundary."""

from __future__ import annotations

import warnings
from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from etlantic.control_plane import (
    ControlPlaneContext,
    ControlPlaneError,
    EnvironmentRef,
    MemoryAuthorizer,
    MemoryDefinitionRepository,
    MemoryEventStore,
    MemorySubmissionStore,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic_fastapi import (
    ETLanticAPI,
    make_principal_from_header,
    principal_from_header,
)
from fastapi import Request
from fastapi.testclient import TestClient

from shuetl import HostIdentityAdapter, ProviderReadinessError, ShuETL


def _context(principal: Principal) -> ControlPlaneContext:
    return ControlPlaneContext(
        principal=principal,
        tenant=TenantRef(tenant_id="tenant-a"),
        workspace=WorkspaceRef(tenant_id="tenant-a", workspace_id="workspace-a"),
        environment=EnvironmentRef(name="development"),
        security_domain=SecurityDomain(domain_id="default"),
    )


def _app_for_adapter(
    adapter: HostIdentityAdapter,
    authorizer: Any | None = None,
) -> Any:
    api = ETLanticAPI(
        authorizer=authorizer or MemoryAuthorizer(),
        definitions=MemoryDefinitionRepository(),
        submissions=MemorySubmissionStore(),
        events=MemoryEventStore(),
        context_factory=adapter.context_factory,
        principal_dependency=adapter.principal_dependency,
        profile="development",
    )
    return ShuETL(api=api).create_app()


def test_adapter_properties_are_stable_immutable_and_redacted() -> None:
    principal = Principal(subject="credential-sentinel")

    def principal_dependency() -> Principal:
        return principal

    adapter = HostIdentityAdapter.create(
        principal_dependency=principal_dependency,
        context_factory=lambda p, _r: _context(p),
    )

    assert adapter.principal_dependency is adapter.principal_dependency
    assert adapter.context_factory is adapter.context_factory
    assert adapter.development_only is False
    assert "credential-sentinel" not in repr(adapter)
    assert "principal_dependency" not in repr(adapter)
    with pytest.raises(FrozenInstanceError):
        adapter._development_only = True  # type: ignore[misc]


@pytest.mark.parametrize(
    "dependency",
    [principal_from_header, make_principal_from_header()],
)
def test_adapter_rejects_upstream_header_demo_dependencies(dependency: Any) -> None:
    with pytest.raises(TypeError, match="host-authenticated"):
        HostIdentityAdapter.create(
            principal_dependency=dependency,
            context_factory=lambda p, _r: _context(p),
        )


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(
            lambda p, _r: _context(p),
            id="synchronous",
        ),
    ],
)
def test_adapter_accepts_a_synchronous_context_factory(factory: Any) -> None:
    adapter = HostIdentityAdapter.create(
        principal_dependency=lambda: Principal(subject="alice"),
        context_factory=factory,
    )
    assert callable(adapter.context_factory)


def test_adapter_rejects_async_generator_and_incompatible_context_factories() -> None:
    async def async_factory(
        principal: Principal, request: Request
    ) -> ControlPlaneContext:
        del request
        return _context(principal)

    def generator_factory(principal: Principal, _request: Request):
        yield _context(principal)

    def keyword_only_factory(*, principal: Principal, request: Request):
        del request
        return _context(principal)

    for factory in (async_factory, generator_factory, keyword_only_factory, object()):
        with pytest.raises(TypeError, match="context_factory"):
            HostIdentityAdapter.create(
                principal_dependency=lambda: Principal(subject="alice"),
                context_factory=factory,  # type: ignore[arg-type]
            )


@pytest.mark.parametrize(
    "principal",
    [
        None,
        {"subject": "alice"},
        Principal(subject=" "),
        Principal(subject="alice", issuer="  "),
        Principal(subject="alice", kind="admin"),  # type: ignore[arg-type]
    ],
)
def test_invalid_resolved_principal_is_401_before_context_or_authorization(
    principal: object,
) -> None:
    context_calls: list[object] = []
    authorizer = MemoryAuthorizer()

    def principal_dependency() -> object:
        return principal

    def context_factory(
        authenticated: Principal, request: Request
    ) -> ControlPlaneContext:
        del request
        context_calls.append(authenticated)
        return _context(authenticated)

    adapter = HostIdentityAdapter.create(
        principal_dependency=principal_dependency,
        context_factory=context_factory,
    )
    with TestClient(_app_for_adapter(adapter, authorizer)) as client:
        response = client.get("/v1/definitions")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authenticated principal is required."
    assert context_calls == []
    assert authorizer.grants == set()


def test_invalid_context_is_a_constant_503_without_exception_details() -> None:
    principal = Principal(subject="alice")

    def principal_dependency() -> Principal:
        return principal

    def failing_context_factory(
        _principal: Principal, _request: Request
    ) -> ControlPlaneContext:
        raise RuntimeError("context-sentinel")

    adapter = HostIdentityAdapter.create(
        principal_dependency=principal_dependency,
        context_factory=failing_context_factory,
    )
    with TestClient(_app_for_adapter(adapter)) as client:
        response = client.get("/v1/definitions")

    assert response.status_code == 503
    assert response.json() == {
        "schema": "etlantic.control_plane.error/1",
        "type": "etlantic.control_plane/error",
        "title": "Service Unavailable",
        "status": 503,
        "detail": "Host identity context is unavailable.",
        "code": "PMCP503",
    }
    assert "context-sentinel" not in response.text


def test_context_must_preserve_the_authenticated_principal_object() -> None:
    principal = Principal(subject="alice")
    substituted = Principal(subject="another-user")

    def principal_dependency() -> Principal:
        return principal

    adapter = HostIdentityAdapter.create(
        principal_dependency=principal_dependency,
        context_factory=lambda _principal, _request: _context(substituted),
    )
    with TestClient(_app_for_adapter(adapter)) as client:
        response = client.get("/v1/definitions")

    assert response.status_code == 503
    assert response.json()["detail"] == "Host identity context is unavailable."


def test_unexpected_coroutine_is_closed_and_returns_503() -> None:
    principal = Principal(subject="alice")
    coroutine_closed: list[bool] = []

    async def coroutine_factory(
        _principal: Principal, _request: Request
    ) -> ControlPlaneContext:
        coroutine_closed.append(True)
        return _context(principal)

    def returns_coroutine(_principal: Principal, _request: Request) -> Any:
        return coroutine_factory(principal, _request)

    adapter = HostIdentityAdapter.create(
        principal_dependency=lambda: principal,
        context_factory=returns_coroutine,  # type: ignore[arg-type]
    )
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        with TestClient(_app_for_adapter(adapter)) as client:
            response = client.get("/v1/definitions")

    assert response.status_code == 503
    assert coroutine_closed == []
    assert not any(issubclass(item.category, RuntimeWarning) for item in captured)


def test_host_control_plane_errors_keep_the_upstream_error() -> None:
    principal = Principal(subject="alice")

    def principal_dependency() -> Principal:
        return principal

    def membership_failure(
        _principal: Principal, _request: Request
    ) -> ControlPlaneContext:
        raise ControlPlaneError.unauthorized("Membership is unavailable.")

    adapter = HostIdentityAdapter.create(
        principal_dependency=principal_dependency,
        context_factory=membership_failure,
    )
    with TestClient(_app_for_adapter(adapter)) as client:
        response = client.get("/v1/definitions")

    assert response.status_code == 401
    assert response.json()["detail"] == "Membership is unavailable."


def test_development_static_adapter_uses_fixed_identity_and_scope() -> None:
    principal = Principal(subject="local-user", issuer="local-issuer", kind="human")
    adapter = HostIdentityAdapter.development_static(
        principal=principal,
        tenant_id="fixed-tenant",
        workspace_id="fixed-workspace",
    )
    assert adapter.development_only is True
    assert "local-user" not in repr(adapter)
    context = adapter.context_factory(
        principal,
        Request({"type": "http", "headers": [], "method": "GET", "path": "/"}),
    )
    assert context.principal is principal
    assert context.tenant.tenant_id == "fixed-tenant"
    assert context.workspace.workspace_id == "fixed-workspace"


def test_production_api_requires_adapter_before_router_materialization() -> None:
    raw_api = ETLanticAPI(
        authorizer=MemoryAuthorizer(),
        definitions=MemoryDefinitionRepository(),
        submissions=MemorySubmissionStore(),
        events=MemoryEventStore(),
        context_factory=lambda p, _r: _context(p),
        principal_dependency=principal_from_header,
        profile="production",
    )
    with pytest.raises(ProviderReadinessError, match="matching host identity adapter"):
        ShuETL(api=raw_api)
    assert raw_api._router is None
