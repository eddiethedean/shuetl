"""Compose pinned ETLantic backend and role factories from trusted bindings."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, cast

from etlantic_sqlmodel import SQLModelBackendConfig, create_managed_backend

from ._secrets import _database_url_value
from .bindings import GatewayBindings, HostBindings, RuntimeBindings
from .errors import ProviderReadinessError
from .factory import validate_context_scope
from .settings import ShuETLSettings


@dataclass(slots=True)
class BackendRuntime:
    settings: ShuETLSettings
    bindings: HostBindings
    backend: Any
    role_handle: Any
    context: Any
    app: Any = None
    closed: bool = False

    def close(self) -> None:
        if self.closed:
            return
        # Upstream may refuse closure while a role is active. Preserve host
        # resources and allow a later retry in that case.
        self.backend.close()
        try:
            self.bindings.close()
        finally:
            self.closed = True


def create_backend_runtime(
    settings: ShuETLSettings, bindings: HostBindings
) -> BackendRuntime:
    """Construct provider-owned storage and the selected upstream role."""
    if settings.database_url is None:
        raise ProviderReadinessError("PostgreSQL database configuration is missing")
    raw_url = _database_url_value(settings.database_url)
    if raw_url is None:
        raise ProviderReadinessError("PostgreSQL database configuration is missing")
    if settings.role != "gateway" and not isinstance(bindings, RuntimeBindings):
        raise ProviderReadinessError("runtime role requires RuntimeBindings")
    if settings.role == "gateway" and not isinstance(bindings, GatewayBindings):
        raise ProviderReadinessError("gateway role requires GatewayBindings")
    try:
        backend = create_managed_backend(
            SQLModelBackendConfig(
                database_url=raw_url,
                store_id=settings.store_id,
                profile=bindings.profile,
                action_handlers=(
                    bindings.action_handlers
                    if isinstance(bindings, RuntimeBindings)
                    else {}
                ),
                policy=bindings.policy,
                approvals=bindings.approvals,
                quotas=bindings.quotas,
                audit=bindings.audit,
                attestations=bindings.attestations,
                require_attestations=bindings.require_attestations,
                schedule_parameter_resolver=bindings.schedule_parameter_resolver,
                artifact_root=bindings.artifact_root,
                engine_options={
                    "pool_pre_ping": True,
                    "pool_timeout": settings.provider_connect_timeout_seconds,
                    "connect_args": {
                        "connect_timeout": max(
                            1, ceil(settings.provider_connect_timeout_seconds)
                        ),
                        "sslmode": settings.postgresql_sslmode,
                    },
                },
            ),
            authorizer=bindings.authorizer,
            planning_context_factory=bindings.planning_context_factory,
        )
    except BaseException:
        bindings.close()
        raise
    try:
        if isinstance(bindings, RuntimeBindings):
            validate_context_scope(bindings.context, settings)
            if settings.role == "scheduler":
                role = backend.create_scheduler(
                    owner_id=f"scheduler-{settings.store_id}-{_owner_token()}",
                    ttl_seconds=30,
                )
            elif settings.worker_kind == "actions":
                role = backend.create_action_execution_host(
                    worker_id=f"actions-{settings.store_id}-{_owner_token()}"
                )
            else:
                role = backend.create_execution_host(
                    owner_id=f"runs-{settings.store_id}-{_owner_token()}"
                )
            context = bindings.context
        else:
            from etlantic_fastapi import adapt_managed_backend

            from .identity import HostIdentityAdapter

            gateway_bindings = cast(GatewayBindings, bindings)
            original = gateway_bindings.identity_adapter
            if (
                not isinstance(original, HostIdentityAdapter)
                or original.development_only
            ):
                raise ProviderReadinessError(
                    "gateway requires a production host-mode identity adapter"
                )

            def scoped_context(principal: Any, request: Any) -> Any:
                ctx = original.context_factory(principal, request)
                validate_context_scope(ctx, settings)
                return ctx

            identity = HostIdentityAdapter.create(
                principal_dependency=original.principal_dependency,
                context_factory=scoped_context,
            )
            adapter = adapt_managed_backend(
                backend,
                context_factory=identity.context_factory,
                principal_dependency=identity.principal_dependency,
            )
            from .integration import ShuETL

            integration = ShuETL(api=adapter.api)
            app = integration.create_app(prefix=settings.api_prefix)
            if gateway_bindings.asgi_hook is not None:
                gateway_bindings.asgi_hook(app)
            role = None
            context = None
            return BackendRuntime(settings, bindings, backend, role, context, app)
        return BackendRuntime(settings, bindings, backend, role, context)
    except BaseException:
        backend.close()
        bindings.close()
        raise


def _owner_token() -> str:
    import secrets

    return secrets.token_hex(8)
