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
from .providers import LocalProviderBundle
from .settings import ShuETLSettings

__all__ = (
    "ShuETL",
    "ShuETLSettings",
    "LocalProviderBundle",
    "DoctorReport",
    "DiagnosticCheck",
    "ShuETLError",
    "InvalidPrefixError",
    "MountConflictError",
    "CompatibilityError",
    "CapabilityError",
    "ProviderReadinessError",
)
