"""Deterministic, redacted ShuETL runtime diagnostics."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ._secrets import _database_url_value
from .compatibility import (
    CORE_REQUIREMENTS,
    POSTGRESQL_REQUIREMENTS,
    SQLITE_REQUIREMENTS,
    installed_versions,
    validate_core,
)
from .postgresql import POSTGRESQL_HEAD, inspect_postgresql
from .providers import (
    SQLITE_HEAD,
    LocalProviderBundle,
    PostgreSQLProviderBundle,
    _read_sqlite_version,
    _sqlite_path,
)
from .settings import ShuETLSettings

CheckStatus = Literal["pass", "warn", "fail", "skip"]


def _identity_check(
    identity: str | None,
    bundle: LocalProviderBundle | PostgreSQLProviderBundle | None,
) -> DiagnosticCheck:
    if identity == "development-static":
        if bundle is not None and (
            bundle.identity_adapter is None
            or not bundle.identity_adapter.development_only
        ):
            return DiagnosticCheck(
                id="identity.explicit",
                status="fail",
                summary=(
                    "Configured development-static mode does not match "
                    "the bundle adapter."
                ),
                remediation="Use a local development-static identity adapter.",
            )
        return DiagnosticCheck(
            id="identity.explicit",
            status="warn",
            summary=(
                "Development-static identity is local-only and is not "
                "suitable for production."
                if bundle is not None
                else "Development-static identity is configured; the runtime "
                "adapter was not inspected."
            ),
            remediation="Use SHUETL_IDENTITY=host for authenticated host deployments.",
        )
    if identity == "host":
        if bundle is None:
            return DiagnosticCheck(
                id="identity.explicit",
                status="warn",
                summary=(
                    "Host identity is configured; the runtime adapter was not "
                    "inspected."
                ),
                remediation=(
                    "Pass the provider bundle to inspect its composition; "
                    "doctor does not authenticate."
                ),
            )
        adapter = bundle.identity_adapter
        if adapter is None and isinstance(bundle, LocalProviderBundle):
            return DiagnosticCheck(
                id="identity.explicit",
                status="warn",
                summary=(
                    "Legacy local host callbacks are unguarded development "
                    "compatibility mode."
                ),
                remediation=(
                    "Use HostIdentityAdapter for guarded host identity composition."
                ),
            )
        if adapter is None or adapter.development_only:
            return DiagnosticCheck(
                id="identity.explicit",
                status="fail",
                summary="Host identity settings do not match the runtime adapter.",
                remediation="Use a host-mode HostIdentityAdapter.",
            )
        return DiagnosticCheck(
            id="identity.explicit",
            status="pass",
            summary=(
                "Host identity adapter is composed; authentication was not inspected."
            ),
        )
    return DiagnosticCheck(
        id="identity.explicit",
        status="fail",
        summary="Identity mode is unsupported.",
        remediation="Use SHUETL_IDENTITY=host or development-static.",
    )


class DiagnosticCheck(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    status: CheckStatus
    summary: str
    remediation: str | None = None


class DoctorReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    schema_: str = Field("shuetl.doctor/1", alias="schema")
    status: Literal["pass", "fail"]
    profile: str | None
    role: str | None
    provider: str | None
    identity: str | None
    api_prefix: str | None
    route_preset: str | None
    development_only: bool
    database_configured: bool
    database_driver: str | None
    versions: dict[str, str | None]
    configured_capabilities: list[str]
    available_capabilities: list[str]
    checks: list[DiagnosticCheck]

    @classmethod
    def inspect(
        cls,
        settings: ShuETLSettings | None = None,
        bundle: LocalProviderBundle | PostgreSQLProviderBundle | None = None,
    ) -> DoctorReport:
        configuration_error: str | None = None
        if settings is None:
            try:
                settings = ShuETLSettings()  # type: ignore[call-arg]
            except ValidationError:
                configuration_error = "Configuration is invalid."
                settings = ShuETLSettings.model_construct(  # type: ignore[call-arg]
                    profile=None,
                    role=None,
                    provider=None,
                    identity=None,
                    api_prefix=None,
                    route_preset=None,
                    database_url=None,
                    provider_connect_timeout_seconds=2.0,
                    postgresql_sslmode="verify-full",
                )

        versions = installed_versions()
        checks: list[DiagnosticCheck] = [
            DiagnosticCheck(
                id="configuration.valid",
                status="fail" if configuration_error else "pass",
                summary=configuration_error or "Configuration is valid.",
                remediation=(
                    "Set supported SHUETL_* values." if configuration_error else None
                ),
            )
        ]
        try:
            validate_core()
            core_status: CheckStatus = "pass"
            core_summary = "Core package versions are compatible."
            core_remediation = None
        except Exception:
            core_status = "fail"
            core_summary = "Core package versions are incompatible."
            core_remediation = "Install the qualified ShuETL 0.6 package set."
        checks.append(
            DiagnosticCheck(
                id="compatibility.core",
                status=core_status,
                summary=core_summary,
                remediation=core_remediation,
            )
        )
        train_ok = all(
            value is None or value == "0.56.2"
            for name, value in versions.items()
            if name.startswith("etlantic-")
        )
        checks.append(
            DiagnosticCheck(
                id="compatibility.etlantic_train",
                status="pass" if train_ok else "fail",
                summary=(
                    "Installed ETLantic extensions match 0.56.2."
                    if train_ok
                    else "An ETLantic extension is outside the 0.56.2 train."
                ),
                remediation=(
                    None
                    if train_ok
                    else "Align every installed etlantic-* package to 0.56.2."
                ),
            )
        )

        provider = settings.provider
        configured = [
            "control-plane.definitions",
            "control-plane.events",
            "control-plane.submissions",
        ]
        if provider == "postgresql":
            configured.extend(
                [
                    "control-plane.registry",
                    "control-plane.revisions",
                    "control-plane.durable-work",
                    "control-plane.schedules",
                    "control-plane.firings",
                    "control-plane.run-reports",
                    "control-plane.input-resources",
                    "control-plane.action-jobs",
                    "control-plane.managed-execution",
                ]
            )
        if provider == "memory":
            provider_available = True
        elif provider == "sqlite":
            provider_available = all(
                versions.get(name) == required
                for name, required in SQLITE_REQUIREMENTS.items()
            )
        else:
            provider_available = all(
                versions.get(name) == required
                for name, required in POSTGRESQL_REQUIREMENTS.items()
            )

        if provider == "memory":
            available = ["provider.memory"]
        elif provider == "sqlite" and provider_available:
            available = ["provider.sqlite"]
        elif provider == "postgresql" and provider_available:
            available = ["provider.postgresql"]
        else:
            available = []

        provider_remediation = None
        if not provider_available:
            provider_remediation = (
                "Install `shuetl[sqlite]==0.6.0`."
                if provider == "sqlite"
                else "Install `shuetl[postgresql]==0.6.0`."
            )
        checks.append(
            DiagnosticCheck(
                id="provider.available",
                status="pass" if provider_available else "fail",
                summary=(
                    "Configured provider dependencies are installed."
                    if provider_available
                    else "Configured provider dependencies are unavailable."
                ),
                remediation=provider_remediation,
            )
        )

        ready: CheckStatus = "pass"
        ready_summary = "Configured provider is ready for local use."
        ready_remediation: str | None = None
        schema_status: CheckStatus = "skip"
        schema_summary = "Relational schema inspection is not applicable to memory."
        schema_remediation: str | None = None
        server_version: str | None = None

        if configuration_error:
            ready = "fail"
            ready_summary = "Provider readiness cannot be evaluated."
            ready_remediation = "Fix configuration before selecting a provider."
        elif bundle is not None and bundle.settings != settings:
            ready = "fail"
            ready_summary = "The supplied provider bundle does not match configuration."
            ready_remediation = "Inspect a bundle created from the same settings."
            if provider in {"sqlite", "postgresql"}:
                schema_status = "fail"
                schema_summary = (
                    "Relational schema was not inspected because configuration "
                    "differed."
                )
        elif provider == "sqlite":
            if not provider_available:
                ready = "fail"
                ready_summary = "SQLite provider dependencies are unavailable."
                ready_remediation = "Install `shuetl[sqlite]==0.6.0`."
                schema_status = "fail"
                schema_summary = (
                    "SQLite schema cannot be inspected without the optional provider."
                )
                schema_remediation = "Install the optional SQLite extra."
            else:
                schema_status, schema_summary, schema_remediation = (
                    _inspect_sqlite_schema(settings)
                )
                if schema_status == "fail":
                    ready = "fail"
                    ready_summary = "SQLite provider is not ready."
                    ready_remediation = schema_remediation
        elif provider == "postgresql":
            ready_summary = (
                "PostgreSQL provider is ready for the controlled pilot; "
                f"TLS mode is {settings.postgresql_sslmode}."
            )
            if not provider_available:
                ready = "fail"
                ready_summary = (
                    "PostgreSQL provider dependencies are unavailable; "
                    f"TLS mode is {settings.postgresql_sslmode}."
                )
                ready_remediation = "Install `shuetl[postgresql]==0.6.0`."
                schema_status = "fail"
                schema_summary = (
                    "PostgreSQL schema cannot be inspected without the optional "
                    "provider."
                )
                schema_remediation = "Install the optional PostgreSQL extra."
            else:
                status = inspect_postgresql(settings)
                server_version = status.server_version
                if status.state == "head":
                    schema_status = "pass"
                    schema_summary = (
                        "PostgreSQL schema is at the required migration head "
                        f"{POSTGRESQL_HEAD}."
                    )
                else:
                    ready = "fail"
                    ready_summary = (
                        "PostgreSQL provider is not ready; "
                        f"TLS mode is {settings.postgresql_sslmode}."
                    )
                    ready_remediation = _postgresql_schema_remediation(status.state)
                    schema_status = "fail"
                    schema_summary = "PostgreSQL schema is not ready."
                    schema_remediation = ready_remediation

        checks.extend(
            [
                DiagnosticCheck(
                    id="provider.ready",
                    status=ready,
                    summary=ready_summary,
                    remediation=ready_remediation,
                ),
                DiagnosticCheck(
                    id="provider.schema",
                    status=schema_status,
                    summary=schema_summary,
                    remediation=schema_remediation,
                ),
                _identity_check(settings.identity, bundle),
                DiagnosticCheck(
                    id="role.supported",
                    status="pass"
                    if settings.role in {"gateway", "scheduler", "worker"}
                    else "fail",
                    summary=(
                        f"Configured {settings.role} role is recognized."
                        if settings.role in {"gateway", "scheduler", "worker"}
                        else "Role is unsupported."
                    ),
                    remediation=(
                        None
                        if settings.role in {"gateway", "scheduler", "worker"}
                        else "Use a supported ShuETL role."
                    ),
                ),
                DiagnosticCheck(
                    id="routes.supported",
                    status="pass" if settings.route_preset == "complete" else "fail",
                    summary=(
                        "Complete route preset is supported."
                        if settings.route_preset == "complete"
                        else "Route preset is unsupported."
                    ),
                    remediation=(
                        None
                        if settings.route_preset == "complete"
                        else "Use SHUETL_ROUTE_PRESET=complete."
                    ),
                ),
                DiagnosticCheck(
                    id="topology.development_only",
                    status="pass" if provider == "postgresql" else "warn",
                    summary=(
                        "PostgreSQL runtime is not development-only."
                        if provider == "postgresql"
                        else "Local providers are development-only."
                    ),
                    remediation=(
                        None
                        if provider == "postgresql"
                        else (
                            "Use a separately operated provider for production "
                            "workloads."
                        )
                    ),
                ),
            ]
        )

        reported_versions = {name: versions.get(name) for name in CORE_REQUIREMENTS}
        reported_versions.update(
            {
                name: value
                for name, value in versions.items()
                if (name.startswith("etlantic-") and name not in CORE_REQUIREMENTS)
                or (provider == "sqlite" and name in SQLITE_REQUIREMENTS)
                or (provider == "postgresql" and name in POSTGRESQL_REQUIREMENTS)
            }
        )
        if provider == "postgresql":
            reported_versions["postgresql-server"] = server_version

        return cls(
            schema="shuetl.doctor/1",
            status=(
                "fail" if any(check.status == "fail" for check in checks) else "pass"
            ),
            profile=settings.profile,
            role=settings.role,
            provider=settings.provider,
            identity=settings.identity,
            api_prefix=settings.api_prefix,
            route_preset=settings.route_preset,
            development_only=provider != "postgresql",
            database_configured=settings.database_url is not None,
            database_driver=settings.database_driver,
            versions=reported_versions,
            configured_capabilities=sorted(configured),
            available_capabilities=sorted(available),
            checks=checks,
        )

    def render_text(self) -> str:
        lines = [
            f"schema: {self.schema_}",
            f"status: {self.status}",
            f"profile: {self.profile or 'unknown'}",
            f"role: {self.role or 'unknown'}",
            f"provider: {self.provider or 'unknown'}",
            f"identity: {self.identity or 'unknown'}",
            f"api_prefix: {self.api_prefix or 'unknown'}",
            f"route_preset: {self.route_preset or 'unknown'}",
            f"development_only: {str(self.development_only).lower()}",
            f"database_configured: {str(self.database_configured).lower()}",
            f"database_driver: {self.database_driver or 'none'}",
            "versions:",
        ]
        lines.extend(
            f"  {name}: {value or 'missing'}" for name, value in self.versions.items()
        )
        lines.append(
            "configured_capabilities: " + ", ".join(self.configured_capabilities)
        )
        lines.append(
            "available_capabilities: " + ", ".join(self.available_capabilities)
        )
        for check in self.checks:
            lines.append(f"{check.id}: {check.status} — {check.summary}")
            if check.remediation:
                lines.append(f"{check.id}.remediation: {check.remediation}")
        return "\n".join(lines)


def _inspect_sqlite_schema(
    settings: ShuETLSettings,
) -> tuple[CheckStatus, str, str | None]:
    """Inspect an existing SQLite file without invoking mutating APIs."""

    database_url = settings.database_url
    if database_url is None:
        return (
            "fail",
            "SQLite database file is not configured.",
            "Set SHUETL_DATABASE_URL.",
        )
    raw_url = _database_url_value(database_url)
    assert raw_url is not None
    path = _sqlite_path(raw_url)
    if not path.is_file():
        return (
            "fail",
            "SQLite database file is not ready.",
            "Provision the SQLite file before startup.",
        )
    engine = None
    try:
        from etlantic_sqlmodel import (
            create_sqlite_engine,  # type: ignore[import-not-found]
        )
        from sqlalchemy import inspect as inspect_engine

        engine = create_sqlite_engine(
            raw_url,
            connect_args={"timeout": settings.provider_connect_timeout_seconds},
        )
        if (
            "etlantic_sqlmodel_schema_version"
            not in inspect_engine(engine).get_table_names()
        ):
            return (
                "fail",
                "SQLite schema is not provisioned.",
                f"Provision the database at {SQLITE_HEAD}.",
            )
        version = _read_sqlite_version(engine)
    except Exception:
        return (
            "fail",
            "SQLite schema could not be inspected.",
            f"Provision the database at {SQLITE_HEAD}.",
        )
    finally:
        if engine is not None:
            engine.dispose()
    if version != SQLITE_HEAD:
        return (
            "fail",
            "SQLite schema is not at the required migration head.",
            f"Provision the database at {SQLITE_HEAD}.",
        )
    return "pass", "SQLite schema is at the required migration head.", None


def _postgresql_schema_remediation(state: str) -> str:
    if state == "fresh":
        return f"Run `shuetl database upgrade` to provision {POSTGRESQL_HEAD}."
    if state == "behind":
        return f"Run `shuetl database upgrade` to reach {POSTGRESQL_HEAD}."
    if state == "wrong-server":
        return "Use the qualified PostgreSQL 18.6 server."
    if state == "unreachable":
        return "Verify PostgreSQL connectivity, credentials, and TLS settings."
    if state == "corrupt":
        return "Restore a provider-owned schema and rerun `shuetl doctor`."
    return "Use a recognized provider migration head."


__all__ = ["DiagnosticCheck", "DoctorReport"]
