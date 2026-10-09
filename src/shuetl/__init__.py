"""Typed ShuETL boundary over ETLantic.

Exports load lazily so headless worker processes do not import FastAPI or the
host identity layer as a side effect of importing the package.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .bindings import GatewayBindings as GatewayBindings
    from .bindings import HostBindings as HostBindings
    from .bindings import RuntimeBindings as RuntimeBindings
    from .diagnostics import DiagnosticCheck as DiagnosticCheck
    from .diagnostics import DoctorReport as DoctorReport
    from .errors import (
        CapabilityError as CapabilityError,
    )
    from .errors import (
        CompatibilityError as CompatibilityError,
    )
    from .errors import (
        InvalidPrefixError as InvalidPrefixError,
    )
    from .errors import (
        MountConflictError as MountConflictError,
    )
    from .errors import (
        ProviderReadinessError as ProviderReadinessError,
    )
    from .errors import (
        ShuETLError as ShuETLError,
    )
    from .identity import HostIdentityAdapter as HostIdentityAdapter
    from .integration import ShuETL as ShuETL
    from .providers import LocalProviderBundle as LocalProviderBundle
    from .providers import PostgreSQLProviderBundle as PostgreSQLProviderBundle
    from .settings import ShuETLSettings as ShuETLSettings

_EXPORTS = {
    "HostBindings": (".bindings", "HostBindings"),
    "GatewayBindings": (".bindings", "GatewayBindings"),
    "RuntimeBindings": (".bindings", "RuntimeBindings"),
    "ShuETL": (".integration", "ShuETL"),
    "ShuETLSettings": (".settings", "ShuETLSettings"),
    "LocalProviderBundle": (".providers", "LocalProviderBundle"),
    "PostgreSQLProviderBundle": (".providers", "PostgreSQLProviderBundle"),
    "DoctorReport": (".diagnostics", "DoctorReport"),
    "DiagnosticCheck": (".diagnostics", "DiagnosticCheck"),
    "ShuETLError": (".errors", "ShuETLError"),
    "InvalidPrefixError": (".errors", "InvalidPrefixError"),
    "MountConflictError": (".errors", "MountConflictError"),
    "CompatibilityError": (".errors", "CompatibilityError"),
    "CapabilityError": (".errors", "CapabilityError"),
    "ProviderReadinessError": (".errors", "ProviderReadinessError"),
    "HostIdentityAdapter": (".identity", "HostIdentityAdapter"),
}
__all__ = (
    "ShuETL",
    "ShuETLSettings",
    "LocalProviderBundle",
    "PostgreSQLProviderBundle",
    "DoctorReport",
    "DiagnosticCheck",
    "ShuETLError",
    "InvalidPrefixError",
    "MountConflictError",
    "CompatibilityError",
    "CapabilityError",
    "ProviderReadinessError",
    "HostIdentityAdapter",
    "HostBindings",
    "GatewayBindings",
    "RuntimeBindings",
)


def __getattr__(name: str) -> Any:
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module = import_module(target[0], __name__)
    value = getattr(module, target[1])
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
