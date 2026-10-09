"""Import and validate explicitly trusted host binding factories."""

from __future__ import annotations

import importlib
import inspect
import threading
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import replace
from types import MappingProxyType
from typing import Any, cast

from etlantic.control_plane import (
    ControlPlaneContext,
    EnvironmentRef,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic.profile import Profile

from ._contracts import authorizer_is_valid
from .bindings import GatewayBindings, HostBindings, RuntimeBindings
from .errors import ProviderReadinessError
from .settings import ShuETLSettings


def load_bindings(path: str, settings: ShuETLSettings) -> HostBindings:
    """Load one trusted factory only after validated settings and pins."""
    if not settings.bindings_factory or path != settings.bindings_factory:
        raise ProviderReadinessError(
            "binding factory does not match validated settings"
        )
    module_name, separator, attribute = path.partition(":")
    if not separator or not module_name or not attribute:
        raise ProviderReadinessError("binding factory path is invalid")
    try:
        module = importlib.import_module(module_name)
    except Exception:
        raise ProviderReadinessError("binding factory module is unavailable") from None
    factory = getattr(module, attribute, None)
    if not callable(factory):
        raise ProviderReadinessError("binding factory is unavailable")
    try:
        inspect.signature(factory).bind(settings)
    except (TypeError, ValueError):
        raise ProviderReadinessError(
            "binding factory must accept validated ShuETL settings"
        ) from None
    try:
        result = factory(settings)
    except Exception:
        raise ProviderReadinessError("binding factory failed") from None
    try:
        _validate_bindings(result, settings)
        result = _with_close_once(cast(HostBindings, result))
        if isinstance(result, RuntimeBindings):
            result = replace(
                result, action_handlers=MappingProxyType(dict(result.action_handlers))
            )
        return cast(HostBindings, result)
    except BaseException:
        _close_invalid(result)
        raise


def _validate_bindings(result: Any, settings: ShuETLSettings) -> None:
    if not isinstance(result, (GatewayBindings, RuntimeBindings)) or type(
        result
    ) not in {GatewayBindings, RuntimeBindings}:
        raise ProviderReadinessError(
            "binding factory returned an unsupported binding type"
        )
    if settings.role == "gateway" and not isinstance(result, GatewayBindings):
        raise ProviderReadinessError("gateway role requires GatewayBindings")
    if settings.role != "gateway" and not isinstance(result, RuntimeBindings):
        raise ProviderReadinessError("runtime role requires RuntimeBindings")
    if (
        not isinstance(result.profile, Profile)
        or result.profile.security_mode != "production"
        or not result.profile.plugin_allowlist
    ):
        raise ProviderReadinessError(
            "preview bindings require a production profile and explicit "
            "plugin allowlist"
        )
    if not is_authorizer(result.authorizer):
        raise ProviderReadinessError("binding authorizer is invalid")
    if not callable(result.planning_context_factory) or not callable(result.close):
        raise ProviderReadinessError("binding resource lifecycle is invalid")
    try:
        inspect.signature(result.planning_context_factory).bind(
            ControlPlaneContext, result.profile
        )
    except (TypeError, ValueError):
        raise ProviderReadinessError(
            "planning context factory must accept context and profile"
        ) from None
    try:
        inspect.signature(result.close).bind()
    except (TypeError, ValueError):
        raise ProviderReadinessError(
            "binding close callback must accept no arguments"
        ) from None
    if not isinstance(result.require_attestations, bool):
        raise ProviderReadinessError("attestation requirement must be boolean")
    if result.artifact_root is not None and (
        not isinstance(result.artifact_root, str) or not result.artifact_root.strip()
    ):
        raise ProviderReadinessError("artifact root must be a non-empty path")
    if isinstance(result, GatewayBindings):
        from .identity import HostIdentityAdapter

        if (
            not isinstance(result.identity_adapter, HostIdentityAdapter)
            or result.identity_adapter.development_only
        ):
            raise ProviderReadinessError(
                "gateway requires a production host-mode identity adapter"
            )
        if result.asgi_hook is not None and not callable(result.asgi_hook):
            raise ProviderReadinessError("gateway ASGI hook is invalid")
    if isinstance(result, RuntimeBindings):
        if not _valid_context(result.context):
            raise ProviderReadinessError("runtime service context is invalid")
        if not isinstance(result.action_handlers, Mapping):
            raise ProviderReadinessError("runtime action handlers must be a mapping")
        _check_scope(result.context, settings)


class _CloseOnce:
    def __init__(self, callback: Any) -> None:
        self._callback = callback
        self._lock = threading.Lock()
        self._closed = False

    def __call__(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._callback()


def _with_close_once(binding: HostBindings) -> HostBindings:
    return replace(binding, close=_CloseOnce(binding.close))


def is_authorizer(value: Any) -> bool:
    return authorizer_is_valid(value)


def validate_context_scope(ctx: ControlPlaneContext, settings: ShuETLSettings) -> None:
    _check_scope(ctx, settings)


def _valid_context(ctx: Any) -> bool:
    try:
        return (
            isinstance(ctx, ControlPlaneContext)
            and isinstance(ctx.principal, Principal)
            and ctx.principal.kind in {"service", "workload"}
            and isinstance(ctx.tenant, TenantRef)
            and bool(ctx.tenant.tenant_id.strip())
            and isinstance(ctx.workspace, WorkspaceRef)
            and ctx.workspace.tenant_id == ctx.tenant.tenant_id
            and bool(ctx.workspace.workspace_id.strip())
            and isinstance(ctx.environment, EnvironmentRef)
            and bool(ctx.environment.name.strip())
            and isinstance(ctx.security_domain, SecurityDomain)
            and bool(ctx.security_domain.domain_id.strip())
            and bool(ctx.principal.subject.strip())
            and bool(ctx.tenant.tenant_id.strip())
            and bool(ctx.workspace.workspace_id.strip())
            and bool(ctx.environment.name.strip())
            and bool(ctx.security_domain.domain_id.strip())
        )
    except (AttributeError, TypeError):
        return False


def _check_scope(
    ctx: ControlPlaneContext,
    settings: ShuETLSettings,
) -> None:
    pairs = (
        (ctx.tenant.tenant_id, settings.tenant_id),
        (ctx.workspace.workspace_id, settings.workspace_id),
        (ctx.environment.name, settings.environment),
        (ctx.security_domain.domain_id, settings.security_domain),
    )
    if any(expected is not None and actual != expected for actual, expected in pairs):
        raise ProviderReadinessError(
            "binding context differs from configured deployment scope"
        )


def _close_invalid(value: Any) -> None:
    with suppress(Exception):
        value.close()
