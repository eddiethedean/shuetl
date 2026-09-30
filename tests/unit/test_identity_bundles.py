"""Bundle, settings, authorizer, and doctor identity contracts."""

from __future__ import annotations

from typing import Any

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
from etlantic_fastapi import make_principal_from_header, principal_from_header
from fastapi import Request

from shuetl import (
    DoctorReport,
    HostIdentityAdapter,
    LocalProviderBundle,
    PostgreSQLProviderBundle,
    ShuETLSettings,
)
from shuetl.identity import is_host_guard_pair, validate_authorizer


def _settings(identity: str = "host") -> ShuETLSettings:
    return ShuETLSettings(
        profile="local",
        role="gateway",
        provider="memory",
        identity=identity,  # type: ignore[arg-type]
    )


def _make_context(
    principal: Principal,
    _request: Request,
) -> ControlPlaneContext:
    return ControlPlaneContext(
        principal=principal,
        tenant=TenantRef(tenant_id="tenant-a"),
        workspace=WorkspaceRef(tenant_id="tenant-a", workspace_id="workspace-a"),
        environment=EnvironmentRef(name="development"),
        security_domain=SecurityDomain(domain_id="default"),
    )


def _host_adapter() -> HostIdentityAdapter:
    return HostIdentityAdapter.create(
        principal_dependency=lambda: Principal(subject="alice"),
        context_factory=_make_context,
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"context_factory": _make_context},
        {"principal_dependency": principal_from_header},
    ],
)
def test_local_bundle_requires_one_complete_identity_form(
    kwargs: dict[str, Any],
) -> None:
    with pytest.raises(TypeError, match="identity_adapter or both raw callbacks"):
        LocalProviderBundle.create(_settings(), authorizer=MemoryAuthorizer(), **kwargs)


def test_local_bundle_keeps_legacy_raw_callbacks_as_development_compatibility() -> None:
    raw_principal = principal_from_header
    raw_context = _make_context
    bundle = LocalProviderBundle.create(
        _settings(),
        authorizer=MemoryAuthorizer(),
        context_factory=raw_context,
        principal_dependency=raw_principal,
    )
    try:
        assert bundle.identity_adapter is None
        assert bundle.api.context_factory is raw_context
        assert bundle.api.principal_dependency is raw_principal
        assert bundle.development_only is True
    finally:
        bundle.close()


def test_local_bundle_uses_adapter_callables_and_exact_authorizer() -> None:
    adapter = _host_adapter()
    authorizer = MemoryAuthorizer()
    bundle = LocalProviderBundle.create(
        _settings(), authorizer=authorizer, identity_adapter=adapter
    )
    try:
        assert bundle.identity_adapter is adapter
        assert bundle.api.principal_dependency is adapter.principal_dependency
        assert bundle.api.context_factory is adapter.context_factory
        assert bundle.api.authorizer is authorizer
    finally:
        bundle.close()


def test_bundle_rejects_mixed_forms_and_adapter_mode_mismatch() -> None:
    adapter = _host_adapter()
    with pytest.raises(TypeError, match="not both"):
        LocalProviderBundle.create(
            _settings(),
            authorizer=MemoryAuthorizer(),
            identity_adapter=adapter,
            context_factory=_make_context,
            principal_dependency=lambda: Principal(subject="alice"),
        )

    static_adapter = HostIdentityAdapter.development_static(
        principal=Principal(subject="local"),
        tenant_id="tenant-a",
        workspace_id="workspace-a",
    )
    with pytest.raises(TypeError, match="host settings"):
        LocalProviderBundle.create(
            _settings("host"),
            authorizer=MemoryAuthorizer(),
            identity_adapter=static_adapter,
        )


def test_development_static_settings_require_an_explicit_static_adapter() -> None:
    settings = _settings("development-static")
    with pytest.raises(TypeError, match="requires identity_adapter"):
        LocalProviderBundle.create(settings, authorizer=MemoryAuthorizer())
    with pytest.raises(TypeError, match="development-static identity requires"):
        LocalProviderBundle.create(
            settings,
            authorizer=MemoryAuthorizer(),
            context_factory=_make_context,
            principal_dependency=lambda: Principal(subject="alice"),
        )

    adapter = HostIdentityAdapter.development_static(
        principal=Principal(subject="local"),
        tenant_id="tenant-a",
        workspace_id="workspace-a",
    )
    bundle = LocalProviderBundle.create(
        settings, authorizer=MemoryAuthorizer(), identity_adapter=adapter
    )
    try:
        assert bundle.identity_adapter is adapter
        assert adapter.development_only is True
    finally:
        bundle.close()


def test_development_static_is_rejected_outside_local_profiles() -> None:
    with pytest.raises(ValueError, match="requires the local profile"):
        ShuETLSettings(
            profile="postgresql-pilot",
            role="gateway",
            provider="postgresql",
            identity="development-static",
            database_url="postgresql+psycopg://user:pass@localhost/db",
        )


@pytest.mark.parametrize(
    "dependency", [principal_from_header, make_principal_from_header()]
)
def test_postgresql_bundle_rejects_known_header_helpers_before_engine_creation(
    dependency: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from shuetl import providers

    engine_calls: list[bool] = []
    monkeypatch.setattr(
        providers,
        "create_postgresql_engine",
        lambda _settings: engine_calls.append(True),
    )
    settings = ShuETLSettings(
        profile="postgresql-pilot",
        role="gateway",
        provider="postgresql",
        identity="host",
        database_url="postgresql+psycopg://user:pass@localhost/db",
    )
    with pytest.raises(TypeError, match="host-authenticated"):
        PostgreSQLProviderBundle.create(
            settings,
            authorizer=MemoryAuthorizer(),
            context_factory=_make_context,
            principal_dependency=dependency,
        )
    assert engine_calls == []


def test_production_raw_callbacks_are_normalized_to_a_guard_pair() -> None:
    from shuetl.providers import _resolve_bundle_identity

    settings = ShuETLSettings(
        profile="postgresql-pilot",
        role="gateway",
        provider="postgresql",
        identity="host",
        database_url="postgresql+psycopg://user:pass@localhost/db",
    )
    adapter, context_factory, principal_dependency = _resolve_bundle_identity(
        settings,
        authorizer=MemoryAuthorizer(),
        identity_adapter=None,
        context_factory=_make_context,
        principal_dependency=lambda: Principal(subject="alice"),
        production=True,
    )
    assert adapter is not None
    assert is_host_guard_pair(principal_dependency, context_factory)
    assert principal_dependency is adapter.principal_dependency
    assert context_factory is adapter.context_factory


def test_authorizer_must_be_synchronous_and_bind_the_upstream_signature() -> None:
    class WrongArity:
        def authorize(self, ctx: object) -> object:
            del ctx
            return object()

    class AsyncAuthorizer:
        async def authorize(
            self,
            ctx: ControlPlaneContext,
            action: str,
            resource: str,
        ) -> object:
            del ctx, action, resource
            return object()

    for authorizer in (WrongArity(), AsyncAuthorizer(), object()):
        with pytest.raises(TypeError):
            validate_authorizer(authorizer)

    assert validate_authorizer(MemoryAuthorizer()) is not None


def test_doctor_reports_configured_and_inspected_identity_without_authenticating() -> (
    None
):
    host_settings = _settings("host")
    uninspected = DoctorReport.inspect(host_settings)
    host_check = next(
        check for check in uninspected.checks if check.id == "identity.explicit"
    )
    assert host_check.status == "warn"
    assert "not inspected" in host_check.summary
    assert "not suitable" not in host_check.summary

    adapter = _host_adapter()
    host_bundle = LocalProviderBundle.create(
        host_settings,
        authorizer=MemoryAuthorizer(),
        identity_adapter=adapter,
    )
    try:
        inspected = DoctorReport.inspect(host_settings, host_bundle)
        assert (
            next(
                check for check in inspected.checks if check.id == "identity.explicit"
            ).status
            == "pass"
        )
    finally:
        host_bundle.close()

    static_settings = _settings("development-static")
    static_adapter = HostIdentityAdapter.development_static(
        principal=Principal(subject="local-principal-sentinel"),
        tenant_id="tenant-a",
        workspace_id="workspace-a",
    )
    static_bundle = LocalProviderBundle.create(
        static_settings,
        authorizer=MemoryAuthorizer(),
        identity_adapter=static_adapter,
    )
    try:
        report = DoctorReport.inspect(static_settings, static_bundle)
        static_check = next(
            check for check in report.checks if check.id == "identity.explicit"
        )
        assert report.status == "pass"
        assert report.development_only is True
        assert static_check.status == "warn"
        assert "local-only" in static_check.summary
        encoded = report.model_dump_json(by_alias=True)
        assert "tenant-a" not in encoded
        assert "local-principal-sentinel" not in encoded
    finally:
        static_bundle.close()
