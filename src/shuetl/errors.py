"""Public ShuETL integration errors."""

from __future__ import annotations


class ShuETLError(Exception):
    """Base class for errors raised by the ShuETL integration facade."""


class InvalidPrefixError(ShuETLError, ValueError):
    """Raised when a mount prefix violates the literal-prefix contract."""


class MountConflictError(ShuETLError, RuntimeError):
    """Raised when mounting would collide with existing application state."""


class CompatibilityError(ShuETLError, RuntimeError):
    """Raised when installed packages are outside the qualified train."""


class CapabilityError(ShuETLError, RuntimeError):
    """Raised when a selected optional capability is unavailable."""


class ProviderReadinessError(ShuETLError, RuntimeError):
    """Raised when a selected local provider cannot safely serve requests."""
