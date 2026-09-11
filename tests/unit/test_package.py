"""Tests for the intentionally minimal 0.1 package contract."""

from __future__ import annotations

from importlib import metadata

import shuetl


def test_package_metadata_and_minimal_surface() -> None:
    assert metadata.version("shuetl") == "0.1.0"
    assert shuetl.__all__ == ()
    for provisional_name in (
        "ShuETL",
        "ShuETLSettings",
        "ProviderBundle",
        "create_app",
        "mount",
    ):
        assert not hasattr(shuetl, provisional_name)
