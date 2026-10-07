"""Standard ETLantic 0.56 managed role construction."""

from __future__ import annotations

import importlib
import inspect
import math
import uuid
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from etlantic.control_plane import (
    Authorizer,
    ControlPlaneContext,
    ControlPlaneError,
    Principal,
)
from etlantic.profile import Profile, resolve_profile
from etlantic.registry import PlanningContext
from etlantic.secrets.provider import SecretAliasAuthorizer
from etlantic_fastapi import ContextFactory
from fastapi import FastAPI
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from .compatibility import installed_versions, validate_postgresql
from .errors import CapabilityError, CompatibilityError, ProviderReadinessError
from .identity import HostIdentityAdapter, validate_authorizer
from .integration import ShuETL
from .postgresql import (
    POSTGRESQL_HEAD,
    create_postgresql_engine,
    inspect_postgresql_engine,
)
from .settings import ShuETLSettings

if TYPE_CHECKING:
    from etlantic.runtime import ActionHandler


_UPSTREAM_BUILTIN_PLUGIN_IDENTITIES = frozenset({"etlantic-local"})


@dataclass(frozen=True, slots=True)
class HostRuntimeBindings:
    """Trusted host identity and resource bindings for one process role.

    Provider action handlers must come from independently installed provider
    packages. This object contains references only; it never implements ETL
    execution or owns the managed database engine.
    """

    authorizer: Authorizer = field(repr=False)
    identity_adapter: HostIdentityAdapter | None = None
    service_context: ControlPlaneContext | None = field(default=None, repr=False)
    planning_context_factory: Callable[[Any, Any], PlanningContext] | None = field(
        default=None, repr=False
    )
    action_handlers: Mapping[str, ActionHandler] = field(
        default_factory=dict, repr=False
    )
    secret_alias_authorizer: SecretAliasAuthorizer | None = field(
        default=None, repr=False
    )
    gateway_app_factory: Callable[[ShuETL], FastAPI] | None = field(
        default=None, repr=False
    )
    close: Callable[[], None] | None = field(default=None, repr=False)


@dataclass(slots=True)
class ManagedRuntime:
    """One role's public upstream graph and its owned host bindings."""

    settings: ShuETLSettings
    bindings: HostRuntimeBindings
    backend: Any = field(repr=False)
    service: Any = field(default=None, repr=False)
    context: ControlPlaneContext | None = field(default=None, repr=False)
    integration: ShuETL | None = field(default=None, repr=False)
    app: FastAPI | None = field(default=None, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    def close(self) -> None:
        """Close the backend and host resources once, in ownership order."""

        if self._closed:
            return
        failure: Exception | None = None
        try:
            self.backend.close()
        except Exception as exc:  # pragma: no cover - defensive adapter boundary
            failure = exc
        try:
            if self.bindings.close is not None:
                self.bindings.close()
        except Exception as exc:  # pragma: no cover - defensive adapter boundary
            failure = failure or exc
        self._closed = True
        if failure is not None:
            raise ProviderReadinessError("runtime resource cleanup failed") from None


def build_managed_runtime(settings: ShuETLSettings) -> ManagedRuntime:
    """Preflight PostgreSQL, load trusted bindings, and construct one role."""

    if type(settings) is not ShuETLSettings:
        raise TypeError("settings must be a ShuETLSettings instance")
    if settings.profile != "postgresql-preview":
        raise ProviderReadinessError("managed runtime requires postgresql-preview")

    try:
        validate_postgresql()
    except CapabilityError:
        raise
    except CompatibilityError:
        raise CompatibilityError(
            "ETLantic 0.56 PostgreSQL dependencies are required"
        ) from None

    profile = resolve_profile(
        _required(settings.execution_profile, "execution_profile"),
        allow_adhoc_profile=False,
    )
    _validate_execution_profile(profile)

    engine = create_postgresql_engine(settings)
    try:
        schema = inspect_postgresql_engine(engine)
    finally:
        engine.dispose()
    if schema.state != "head" or schema.version != POSTGRESQL_HEAD:
        raise ProviderReadinessError(
            f"PostgreSQL preview schema is not ready ({schema.state})"
        )

    bindings = _load_bindings(settings)
    try:
        _validate_bindings(settings, bindings)
        adapter = _scoped_identity_adapter(settings, bindings)
        context_factory, principal_dependency = _api_identity(adapter)
        from etlantic_fastapi.managed import (
            ManagedBackendConfig,
            create_managed_backend,
        )

        database_url = settings.database_url
        if database_url is None:
            raise ProviderReadinessError("PostgreSQL database configuration is missing")
        engine_options: dict[str, Any] = {
            "connect_args": {
                "connect_timeout": math.ceil(settings.provider_connect_timeout_seconds),
                "sslmode": settings.postgresql_sslmode,
            },
            "pool_pre_ping": True,
        }
        config = ManagedBackendConfig(
            database_url=database_url.get_secret_value(),
            store_id=_required(settings.store_id, "store_id"),
            profile=profile,
            engine_options=engine_options,
            title="ShuETL 0.6 Control Plane",
            version="0.6.0",
            action_handlers=dict(bindings.action_handlers),
            artifact_root=settings.artifact_root,
        )
        backend = create_managed_backend(
            config,
            authorizer=bindings.authorizer,
            context_factory=context_factory,
            principal_dependency=principal_dependency,
            planning_context_factory=bindings.planning_context_factory,
        )
        try:
            if backend.api.schedule_store is None:
                from etlantic_sqlmodel.control_plane import SQLModelScheduleStore

                backend.api.schedule_store = SQLModelScheduleStore(
                    backend.engine, store_id=config.store_id
                )
            if backend.api.managed_service is None:
                raise ProviderReadinessError(
                    "ETLantic managed submission service is unavailable"
                )
            _verify_constructed_backend(backend)
            return _make_role_runtime(settings, bindings, backend)
        except Exception:
            backend.close()
            raise
    except Exception:
        if bindings.close is not None:
            with suppress(Exception):
                bindings.close()
        raise


def _required(value: str | None, name: str) -> str:
    if value is None:
        raise ProviderReadinessError(f"{name} is required")
    return value


def _validate_execution_profile(profile: Profile) -> None:
    """Fail before database or host code when a trusted profile is incomplete."""

    allowlist = dict(profile.plugin_allowlist or {})
    production = profile.security_mode == "production"
    if production and not allowlist:
        raise ProviderReadinessError(
            "production execution profile requires a pinned plugin allowlist"
        )
    versions = installed_versions()
    for package, pin in allowlist.items():
        if not str(package).startswith("etlantic"):
            continue
        installed = versions.get(str(package))
        if installed is None:
            if package in _UPSTREAM_BUILTIN_PLUGIN_IDENTITIES:
                # ETLantic exposes this built-in plugin identity from its core
                # distribution; plugin trust validates its own reported version.
                continue
            raise CompatibilityError(
                f"execution profile requires missing package {package}"
            )
        expected = str(pin).removeprefix("==") if pin is not None else None
        if production and not expected:
            raise ProviderReadinessError(
                f"production execution profile must pin package {package}"
            )
        if expected is not None:
            specifier = expected
            if not specifier.startswith(("<", ">", "=", "!", "~")):
                specifier = f"=={specifier}"
            try:
                matches = Version(installed) in SpecifierSet(specifier)
            except (InvalidSpecifier, InvalidVersion):
                matches = False
            if not matches:
                raise CompatibilityError(
                    "execution profile package pin does not match "
                    f"{package}={installed}"
                )


def _load_bindings(settings: ShuETLSettings) -> HostRuntimeBindings:
    reference = _required(settings.factory, "factory")
    module_name, attribute = reference.split(":", 1)
    try:
        module = importlib.import_module(module_name)
        factory = getattr(module, attribute)
        if not callable(factory):
            raise TypeError
        inspect.signature(factory).bind(settings)
        bindings = factory(settings)
    except Exception:
        raise ProviderReadinessError(
            "trusted runtime factory could not be loaded"
        ) from None
    if type(bindings) is not HostRuntimeBindings:
        raise ProviderReadinessError(
            "trusted runtime factory must return HostRuntimeBindings"
        )
    return bindings


def _validate_bindings(settings: ShuETLSettings, bindings: HostRuntimeBindings) -> None:
    validate_authorizer(bindings.authorizer)
    if settings.role == "gateway":
        adapter = bindings.identity_adapter
        if adapter is None or adapter.development_only:
            raise ProviderReadinessError(
                "gateway role requires a host-mode HostIdentityAdapter"
            )
        if bindings.service_context is not None:
            raise ProviderReadinessError(
                "gateway bindings cannot contain a runtime service context"
            )
        if bindings.action_handlers:
            raise ProviderReadinessError(
                "gateway bindings cannot load provider action handlers"
            )
        if bindings.secret_alias_authorizer is not None:
            raise ProviderReadinessError(
                "gateway bindings cannot load worker secret authorization"
            )
    else:
        if bindings.identity_adapter is not None:
            raise ProviderReadinessError(
                "runtime roles cannot load gateway request identity"
            )
        if bindings.gateway_app_factory is not None:
            raise ProviderReadinessError(
                "runtime roles cannot load a gateway application factory"
            )
        context = bindings.service_context
        if not isinstance(context, ControlPlaneContext):
            raise ProviderReadinessError(
                "runtime role requires an ETLantic service context"
            )
        if context.principal.kind not in {"service", "workload"}:
            raise ProviderReadinessError(
                "runtime context must use a service or workload principal"
            )
        if not _matches_configured_scope(settings, context):
            raise ProviderReadinessError(
                "runtime service context does not match the configured scope"
            )
        if settings.role == "scheduler" and bindings.action_handlers:
            raise ProviderReadinessError(
                "scheduler bindings cannot load provider action handlers"
            )
        if (
            settings.role == "scheduler"
            and bindings.secret_alias_authorizer is not None
        ):
            raise ProviderReadinessError(
                "scheduler bindings cannot load worker secret authorization"
            )
        if settings.role == "worker" and settings.worker_kind == "actions":
            if not bindings.action_handlers:
                raise ProviderReadinessError(
                    "action worker requires independently installed provider handlers"
                )
        elif bindings.action_handlers:
            raise ProviderReadinessError(
                "run workers cannot load provider action handlers"
            )


def _matches_configured_scope(
    settings: ShuETLSettings, context: ControlPlaneContext
) -> bool:
    return (
        context.tenant.tenant_id == settings.tenant_id
        and context.workspace.tenant_id == settings.tenant_id
        and context.workspace.workspace_id == settings.workspace_id
    )


def _scoped_identity_adapter(
    settings: ShuETLSettings, bindings: HostRuntimeBindings
) -> HostIdentityAdapter | None:
    original = bindings.identity_adapter
    if settings.role != "gateway" or original is None:
        return None

    def context_factory(principal: Principal, request: Any) -> ControlPlaneContext:
        context = original.context_factory(principal, request)
        if not _matches_configured_scope(settings, context):
            raise ControlPlaneError.unauthorized(
                "Request is outside the configured preview scope."
            )
        return context

    return HostIdentityAdapter.create(
        principal_dependency=original.principal_dependency,
        context_factory=context_factory,
    )


def _api_identity(
    adapter: HostIdentityAdapter | None,
) -> tuple[ContextFactory, Any]:
    if adapter is not None:
        return adapter.context_factory, adapter.principal_dependency

    def deny_context(_principal: Principal, _request: Any) -> ControlPlaneContext:
        raise ControlPlaneError.unauthorized("This runtime role has no HTTP identity.")

    async def deny_principal() -> Principal:
        raise ControlPlaneError.unauthorized("This runtime role has no HTTP identity.")

    return deny_context, deny_principal


def _verify_constructed_backend(backend: Any) -> None:
    api = backend.api
    if api.durable_work is None or api.schedule_store is None:
        raise ProviderReadinessError(
            "ETLantic managed backend lacks durable or schedule stores"
        )
    status = inspect_postgresql_engine(backend.engine)
    if status.state != "head" or status.version != POSTGRESQL_HEAD:
        raise ProviderReadinessError(
            f"PostgreSQL schema changed during backend construction ({status.state})"
        )


def _make_role_runtime(
    settings: ShuETLSettings,
    bindings: HostRuntimeBindings,
    backend: Any,
) -> ManagedRuntime:
    runtime = ManagedRuntime(settings, bindings, backend)
    if settings.role == "gateway":
        integration = ShuETL(api=backend.api)
        if bindings.gateway_app_factory is None:
            app = integration.create_app(prefix=settings.api_prefix)
        else:
            try:
                app = bindings.gateway_app_factory(integration)
            except Exception:
                raise ProviderReadinessError(
                    "gateway application composition failed"
                ) from None
        if not isinstance(app, FastAPI):
            raise ProviderReadinessError(
                "gateway application factory must return FastAPI"
            )
        if getattr(app.state, "etlantic_api", None) is not backend.api or getattr(
            getattr(app.state, "shuetl", None), "integration_id", None
        ) != id(integration):
            raise ProviderReadinessError(
                "gateway factory must mount the supplied ShuETL integration"
            )
        runtime.integration = integration
        runtime.app = app
        return runtime

    context = bindings.service_context
    assert context is not None
    owner_suffix = settings.owner_id or "process"
    owner_id = f"{settings.role}-{owner_suffix}-{uuid.uuid4().hex}"
    if settings.role == "scheduler":
        from etlantic.runtime.scheduler_service import SchedulerService

        runtime.service = SchedulerService(
            backend.api.schedule_store,
            durable=backend.api.durable_work,
            owner_id=owner_id,
            ttl_seconds=settings.lease_ttl_seconds,
            run_submitter=backend.api.managed_service.submit_scheduled_run,
            profile=backend.execution_profile,
        )
    else:
        if settings.worker_kind == "actions":
            runtime.service = backend.create_action_execution_host(worker_id=owner_id)
        else:
            execution_host = backend.create_execution_host(
                owner_id=owner_id,
                ttl_seconds=settings.lease_ttl_seconds,
            )
            if bindings.secret_alias_authorizer is not None:
                runner = getattr(execution_host, "runner", None)
                if runner is None or not hasattr(runner, "secret_alias_authorizer"):
                    raise ProviderReadinessError(
                        "ETLantic execution host does not expose secret authorization"
                    )
                runner.secret_alias_authorizer = bindings.secret_alias_authorizer
            runtime.service = execution_host
    runtime.context = context
    return runtime


__all__ = [
    "HostRuntimeBindings",
    "ManagedRuntime",
    "build_managed_runtime",
]
