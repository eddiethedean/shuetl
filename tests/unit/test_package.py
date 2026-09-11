"""Tests for the Phase 0.3 package contract."""

from __future__ import annotations

from importlib import metadata

import shuetl


def test_package_metadata_and_minimal_surface() -> None:
    assert metadata.version("shuetl") == "0.3.0"
    assert shuetl.__all__ == (
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
    assert shuetl.ShuETL
    assert shuetl.ShuETLError
    assert shuetl.InvalidPrefixError
    assert shuetl.MountConflictError
    for provisional_name in ("ProviderBundle", "create_app", "mount"):
        assert not hasattr(shuetl, provisional_name)
