"""Guard the host-owned identity boundary without owning authentication."""

from __future__ import annotations

import inspect
from contextlib import suppress
from dataclasses import dataclass, field
from functools import partial
from typing import Any
from weakref import WeakKeyDictionary

from etlantic.control_plane import (
    Authorizer,
    ControlPlaneContext,
    ControlPlaneError,
    CorrelationKey,
    EnvironmentRef,
    IdempotencyKey,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic_fastapi import (
    ContextFactory,
    make_principal_from_header,
    principal_from_header,
    static_context_factory,
)
from fastapi import Depends, Request

from ._contracts import is_async_or_generator_callable

_DEMO_DEPENDENCY_CODE = make_principal_from_header().__code__
_GUARDED_CALLABLES: WeakKeyDictionary[Any, tuple[object, str]] = WeakKeyDictionary()


def _nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(str.strip(value))


def _principal_is_valid(value: object) -> bool:
    try:
        return (
            isinstance(value, Principal)
            and _nonblank(value.subject)
            and (value.issuer is None or _nonblank(value.issuer))
            and isinstance(value.kind, str)
            and value.kind in {"human", "workload", "service"}
        )
    except Exception:
        return False


def _authenticated_principal(value: object) -> Principal:
    if not _principal_is_valid(value):
        raise ControlPlaneError.unauthorized("Authenticated principal is required.")
    return value  # type: ignore[return-value]


def _identity_context_is_valid(
    value: object,
    principal: Principal,
) -> bool:
    if not isinstance(value, ControlPlaneContext):
        return False
    if value.principal is not principal:
        return False
    if not isinstance(value.tenant, TenantRef) or not _nonblank(value.tenant.tenant_id):
        return False
    if not isinstance(value.workspace, WorkspaceRef):
        return False
    if (
        not _nonblank(value.workspace.tenant_id)
        or not _nonblank(value.workspace.workspace_id)
        or value.workspace.tenant_id != value.tenant.tenant_id
    ):
        return False
    if not isinstance(value.environment, EnvironmentRef) or not _nonblank(
        value.environment.name
    ):
        return False
    if not isinstance(value.security_domain, SecurityDomain) or not _nonblank(
        value.security_domain.domain_id
    ):
        return False
    if value.correlation_key is not None and (
        not isinstance(value.correlation_key, CorrelationKey)
        or not _nonblank(value.correlation_key.value)
    ):
        return False
    if value.idempotency_key is not None and (
        not isinstance(value.idempotency_key, IdempotencyKey)
        or not _nonblank(value.idempotency_key.value)
    ):
        return False
    return value.request_id is None or _nonblank(value.request_id)


def _context_unavailable() -> ControlPlaneError:
    return ControlPlaneError(
        "Host identity context is unavailable.",
        code="PMCP503",
        status=503,
        type="etlantic.control_plane/error",
        title="Service Unavailable",
    )


def _is_upstream_header_demo(value: object) -> bool:
    while isinstance(value, partial):
        value = value.func
    if value is principal_from_header or value is make_principal_from_header:
        return True
    return (
        inspect.isfunction(value)
        and getattr(value, "__code__", None) is _DEMO_DEPENDENCY_CODE
    )


def _context_factory_shape_is_valid(value: object) -> bool:
    if not callable(value):
        return False
    if is_async_or_generator_callable(value):
        return False
    try:
        inspect.signature(value).bind(object(), object())
    except (TypeError, ValueError):
        return False
    return True


def validate_authorizer(authorizer: object) -> Authorizer:
    """Validate the synchronous upstream authorizer seam without calling it."""

    if not isinstance(authorizer, Authorizer):
        raise TypeError("authorizer must implement the ETLantic Authorizer protocol")
    method = getattr(authorizer, "authorize", None)
    if not callable(method) or is_async_or_generator_callable(method):
        raise TypeError("authorizer.authorize must be a synchronous callable")
    try:
        inspect.signature(method).bind(object(), "action", "resource")
    except (TypeError, ValueError):
        raise TypeError(
            "authorizer.authorize must accept context, action, and resource"
        ) from None
    return authorizer


def _register_guarded_pair(
    adapter: HostIdentityAdapter,
    token: object,
) -> None:
    mode = "development-static" if adapter.development_only else "host"
    _GUARDED_CALLABLES[adapter.principal_dependency] = (token, mode)
    _GUARDED_CALLABLES[adapter.context_factory] = (token, mode)


def is_host_guard_pair(
    principal_dependency: object,
    context_factory: object,
) -> bool:
    """Return whether callables are the same adapter's production-safe guards."""

    try:
        principal = _GUARDED_CALLABLES.get(principal_dependency)
        context = _GUARDED_CALLABLES.get(context_factory)
    except TypeError:
        # FastAPI accepts callable dependency objects that are not hashable or
        # weak-referenceable. They cannot be a registered adapter guard, so
        # treat them as an ordinary non-matching pair during preflight.
        return False
    return (
        principal is not None
        and context is not None
        and principal[0] is context[0]
        and principal[1] == context[1] == "host"
    )


@dataclass(frozen=True, slots=True, init=False, eq=False, repr=False)
class HostIdentityAdapter:
    """Stable FastAPI dependency guards around host-authenticated identity.

    The host authenticates credentials and establishes membership. This object
    accepts an upstream Principal and checks only its type and composition into
    an upstream ControlPlaneContext.
    """

    _principal_dependency: Any = field(repr=False)
    _context_factory: Any = field(repr=False)
    _development_only: bool

    @classmethod
    def create(
        cls,
        *,
        principal_dependency: Any,
        context_factory: ContextFactory,
    ) -> HostIdentityAdapter:
        """Wrap a native FastAPI principal dependency and host context factory."""

        if not callable(principal_dependency) or _is_upstream_header_demo(
            principal_dependency
        ):
            raise TypeError(
                "principal_dependency must be a host-authenticated dependency"
            )
        try:
            inspect.signature(principal_dependency)
        except (TypeError, ValueError):
            raise TypeError(
                "principal_dependency must be FastAPI-inspectable"
            ) from None
        if not _context_factory_shape_is_valid(context_factory):
            raise TypeError(
                "context_factory must be synchronous and accept principal and request"
            )

        token = object()

        async def guarded_principal(
            principal: Any = Depends(principal_dependency),  # noqa: B008
        ) -> Principal:
            return _authenticated_principal(principal)

        def guarded_context_factory(
            principal: Principal,
            request: Request,
        ) -> ControlPlaneContext:
            authenticated = _authenticated_principal(principal)
            try:
                context = context_factory(authenticated, request)
            except ControlPlaneError:
                raise
            except Exception:
                raise _context_unavailable() from None

            if inspect.iscoroutine(context):
                with suppress(Exception):
                    context.close()
                raise _context_unavailable()
            if inspect.isawaitable(context):
                raise _context_unavailable()
            try:
                valid = _identity_context_is_valid(context, authenticated)
            except Exception:
                valid = False
            if not valid:
                raise _context_unavailable()
            return context  # type: ignore[return-value]

        adapter = cls._from_callables(
            guarded_principal,
            guarded_context_factory,
            development_only=False,
        )
        _register_guarded_pair(adapter, token)
        return adapter

    @classmethod
    def development_static(
        cls,
        *,
        principal: Principal,
        tenant_id: str,
        workspace_id: str,
        environment: str = "development",
        security_domain: str = "default",
    ) -> HostIdentityAdapter:
        """Create an explicit local-only fixed identity adapter."""

        _authenticated_principal(principal)
        for name, value in (
            ("tenant_id", tenant_id),
            ("workspace_id", workspace_id),
            ("environment", environment),
            ("security_domain", security_domain),
        ):
            if not _nonblank(value):
                raise ValueError(f"{name} must be a non-blank string")

        def static_principal_dependency() -> Principal:
            return principal

        raw_context_factory = static_context_factory(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            environment=environment,
            security_domain=security_domain,
        )
        token = object()

        async def guarded_principal() -> Principal:
            return _authenticated_principal(static_principal_dependency())

        def guarded_context_factory(
            authenticated: Principal,
            request: Request,
        ) -> ControlPlaneContext:
            valid_principal = _authenticated_principal(authenticated)
            try:
                context = raw_context_factory(valid_principal, request)
            except ControlPlaneError:
                raise
            except Exception:
                raise _context_unavailable() from None
            if inspect.iscoroutine(context):
                with suppress(Exception):
                    context.close()
                raise _context_unavailable()
            if inspect.isawaitable(context):
                raise _context_unavailable()
            try:
                valid = _identity_context_is_valid(context, valid_principal)
            except Exception:
                valid = False
            if not valid:
                raise _context_unavailable()
            return context  # type: ignore[return-value]

        adapter = cls._from_callables(
            guarded_principal,
            guarded_context_factory,
            development_only=True,
        )
        _register_guarded_pair(adapter, token)
        return adapter

    @classmethod
    def _from_callables(
        cls,
        principal_dependency: Any,
        context_factory: Any,
        *,
        development_only: bool,
    ) -> HostIdentityAdapter:
        instance = object.__new__(cls)
        object.__setattr__(instance, "_principal_dependency", principal_dependency)
        object.__setattr__(instance, "_context_factory", context_factory)
        object.__setattr__(instance, "_development_only", development_only)
        return instance

    @property
    def principal_dependency(self) -> Any:
        """Return the stable guarded dependency for the upstream API."""

        return self._principal_dependency

    @property
    def context_factory(self) -> ContextFactory:
        """Return the stable guarded synchronous context factory."""

        return self._context_factory

    @property
    def development_only(self) -> bool:
        """Whether this adapter supplies explicit fixed development identity."""

        return self._development_only

    def __repr__(self) -> str:
        mode = "development-static" if self.development_only else "host"
        return f"HostIdentityAdapter(mode={mode!r})"


__all__ = ["HostIdentityAdapter", "is_host_guard_pair", "validate_authorizer"]
