"""Typed FastAPI composition facade for ETLantic."""

from .diagnostics import DiagnosticCheck, DoctorReport
from .errors import (
    CapabilityError,
    CompatibilityError,
    InvalidPrefixError,
    MountConflictError,
    ProviderReadinessError,
    ShuETLError,
)
from .identity import HostIdentityAdapter
from .integration import ShuETL
from .providers import LocalProviderBundle, PostgreSQLProviderBundle
from .runtime import HostRuntimeBindings
from .settings import ShuETLSettings

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
    "HostRuntimeBindings",
)
