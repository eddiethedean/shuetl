"""Tests for the Phase 0.3 package contract."""

from __future__ import annotations

from importlib import metadata

import shuetl


def test_package_metadata_and_minimal_surface() -> None:
    assert metadata.version("shuetl") == "0.6.0"
    assert shuetl.__all__ == (
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
    assert shuetl.ShuETL
    assert shuetl.ShuETLError
    assert shuetl.InvalidPrefixError
    assert shuetl.MountConflictError
    assert shuetl.HostIdentityAdapter
    assert shuetl.HostBindings
    assert shuetl.GatewayBindings
    assert shuetl.RuntimeBindings
    for provisional_name in ("ProviderBundle", "create_app", "mount"):
        assert not hasattr(shuetl, provisional_name)
