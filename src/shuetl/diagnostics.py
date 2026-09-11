"""Deterministic, redacted local runtime diagnostics."""

# Stable golden summary lines intentionally retain their contract wording.
# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .compatibility import (
    CORE_REQUIREMENTS,
    SQLITE_REQUIREMENTS,
    installed_versions,
    validate_core,
)
from .providers import SQLITE_HEAD, LocalProviderBundle
from .settings import ShuETLSettings

CheckStatus = Literal["pass", "warn", "fail", "skip"]


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
        bundle: LocalProviderBundle | None = None,
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
                )

        versions = installed_versions()
        checks: list[DiagnosticCheck] = []
        checks.append(
            DiagnosticCheck(
                id="configuration.valid",
                status="fail" if configuration_error else "pass",
                summary=configuration_error or "Configuration is valid.",
                remediation=(
                    "Set supported SHUETL_* values." if configuration_error else None
                ),
            )
        )
        try:
            validate_core()
            core_status: CheckStatus = "pass"
            core_summary = "Core package versions are compatible."
            core_remediation = None
        except Exception:
            core_status = "fail"
            core_summary = "Core package versions are incompatible."
            core_remediation = "Install the qualified ShuETL 0.3 package set."
        checks.append(
            DiagnosticCheck(
                id="compatibility.core",
                status=core_status,
                summary=core_summary,
                remediation=core_remediation,
            )
        )
        train_ok = all(
            value is None or value.split(".")[:2] == ["0", "51"]
            for name, value in versions.items()
            if name.startswith("etlantic-")
        )
        checks.append(
            DiagnosticCheck(
                id="compatibility.etlantic_train",
                status="pass" if train_ok else "fail",
                summary=(
                    "Installed ETLantic extensions share the 0.51 train."
                    if train_ok
                    else "An ETLantic extension is outside the 0.51 train."
                ),
                remediation=(
                    None
                    if train_ok
                    else "Align every installed etlantic-* package to 0.51."
                ),
            )
        )

        provider = settings.provider
        configured = [
            "control-plane.definitions",
            "control-plane.events",
            "control-plane.submissions",
        ]
        provider_available = provider == "memory" or all(
            versions.get(name) == required
            for name, required in SQLITE_REQUIREMENTS.items()
        )
        if provider == "memory":
            available = ["provider.memory"]
        elif provider == "sqlite" and provider_available:
            available = ["provider.sqlite"]
        else:
            available = []
        checks.append(
            DiagnosticCheck(
                id="provider.available",
                status="pass" if provider_available else "fail",
                summary=(
                    "Configured provider dependencies are installed."
                    if provider_available
                    else "Configured provider dependencies are unavailable."
                ),
                remediation=(
                    None if provider_available else "Install `shuetl[sqlite]==0.3.0`."
                ),
            )
        )
        ready = "pass"
        ready_summary = "Configured provider is ready for local use."
        ready_remediation = None
        schema_status: CheckStatus = "skip"
        schema_summary = "SQLite schema inspection is not applicable to memory."
        schema_remediation = None
        if configuration_error:
            ready = "fail"
            ready_summary = "Provider readiness cannot be evaluated."
            ready_remediation = "Fix configuration before selecting a provider."
        if provider == "sqlite":
            if not provider_available:
                ready = "fail"
                ready_summary = "SQLite provider dependencies are unavailable."
                ready_remediation = "Install `shuetl[sqlite]==0.3.0`."
                schema_status = "fail"
                schema_summary = (
                    "SQLite schema cannot be inspected without the optional provider."
                )
                schema_remediation = "Install the optional SQLite extra."
            elif bundle is not None and bundle.settings != settings:
                ready = "fail"
                ready_summary = (
                    "The supplied provider bundle does not match configuration."
                )
                ready_remediation = "Inspect a bundle created from the same settings."
                schema_status = "fail"
                schema_summary = (
                    "SQLite schema was not inspected because configuration differed."
                )
            else:
                schema_status, schema_summary, schema_remediation = (
                    _inspect_sqlite_schema(settings)
                )
                if schema_status == "fail":
                    ready = "fail"
                    ready_summary = "SQLite provider is not ready."
                    ready_remediation = schema_remediation
        checks.append(
            DiagnosticCheck(
                id="provider.ready",
                status=ready,
                summary=ready_summary,
                remediation=ready_remediation,
            )
        )
        checks.append(
            DiagnosticCheck(
                id="provider.schema",
                status=schema_status,
                summary=schema_summary,
                remediation=schema_remediation,
            )
        )
        checks.extend(
            [
                DiagnosticCheck(
                    id="identity.explicit",
                    status="pass" if settings.identity == "host" else "fail",
                    summary="Host identity is explicit."
                    if settings.identity == "host"
                    else "Identity mode is unsupported.",
                    remediation=None
                    if settings.identity == "host"
                    else "Use SHUETL_IDENTITY=host.",
                ),
                DiagnosticCheck(
                    id="role.supported",
                    status="pass" if settings.role == "gateway" else "fail",
                    summary="Gateway role is supported."
                    if settings.role == "gateway"
                    else "Role is unsupported.",
                    remediation=None
                    if settings.role == "gateway"
                    else "Use SHUETL_ROLE=gateway.",
                ),
                DiagnosticCheck(
                    id="routes.supported",
                    status="pass" if settings.route_preset == "complete" else "fail",
                    summary="Complete route preset is supported."
                    if settings.route_preset == "complete"
                    else "Route preset is unsupported.",
                    remediation=None
                    if settings.route_preset == "complete"
                    else "Use SHUETL_ROUTE_PRESET=complete.",
                ),
                DiagnosticCheck(
                    id="topology.development_only",
                    status="warn",
                    summary="Local providers are development-only.",
                    remediation="Use a separately operated provider for production workloads.",
                ),
            ]
        )
        return cls(
            schema="shuetl.doctor/1",
            status="fail"
            if any(check.status == "fail" for check in checks)
            else "pass",
            profile=settings.profile,
            role=settings.role,
            provider=settings.provider,
            identity=settings.identity,
            api_prefix=settings.api_prefix,
            route_preset=settings.route_preset,
            development_only=True,
            database_configured=settings.database_url is not None,
            database_driver=settings.database_driver,
            versions={name: versions.get(name) for name in CORE_REQUIREMENTS}
            | {
                name: value
                for name, value in versions.items()
                if name.startswith("etlantic-") and name not in CORE_REQUIREMENTS
            },
            configured_capabilities=sorted(configured),
            available_capabilities=sorted(available),
            checks=checks,
        )

    def render_text(self) -> str:
        lines = [
            f"status: {self.status}",
            f"provider: {self.provider or 'unknown'}",
            f"profile: {self.profile or 'unknown'}",
            f"development_only: {str(self.development_only).lower()}",
        ]
        lines.extend(
            f"{check.id}: {check.status} — {check.summary}" for check in self.checks
        )
        return "\n".join(lines)


def _inspect_sqlite_schema(
    settings: ShuETLSettings,
) -> tuple[CheckStatus, str, str | None]:
    """Inspect an existing SQLite file through the optional public APIs."""

    database_url = settings.database_url
    if database_url is None:
        return (
            "fail",
            "SQLite database file is not configured.",
            "Set SHUETL_DATABASE_URL.",
        )
    parsed = urlsplit(database_url.get_secret_value())
    raw_path = parsed.path
    path = (
        Path("/" + raw_path.lstrip("/"))
        if raw_path.startswith("//")
        else Path(raw_path.lstrip("/"))
    )
    if not path.is_file():
        return (
            "fail",
            "SQLite database file is not ready.",
            "Provision the SQLite file before startup.",
        )
    engine = None
    try:
        from etlantic_sqlmodel import (  # type: ignore[import-not-found]
            create_sqlite_engine,
            current_version,
        )

        engine = create_sqlite_engine(
            database_url.get_secret_value(),
            connect_args={"timeout": settings.provider_connect_timeout_seconds},
        )
        version = current_version(engine)
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


__all__ = ["DiagnosticCheck", "DoctorReport"]
