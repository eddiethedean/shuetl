"""Public ShuETL integration errors."""

from __future__ import annotations


class ShuETLError(Exception):
    """Base class for errors raised by the ShuETL integration facade."""


class InvalidPrefixError(ShuETLError, ValueError):
    """Raised when a mount prefix violates the literal-prefix contract."""


class MountConflictError(ShuETLError, RuntimeError):
    """Raised when mounting would collide with existing application state."""
