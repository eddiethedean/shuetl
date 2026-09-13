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
from .integration import ShuETL
from .providers import LocalProviderBundle, PostgreSQLProviderBundle
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
)
