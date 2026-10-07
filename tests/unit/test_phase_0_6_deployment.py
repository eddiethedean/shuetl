"""Contract checks for the Phase 0.6 process deployment launcher."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "deploy" / "phase-0.6" / "systemd" / "shuetl-preview-container"


def test_systemd_launcher_accepts_only_digest_pinned_application_images() -> None:
    valid = subprocess.run(
        ["sh", str(LAUNCHER), "--check"],
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "SHUETL_IMAGE": f"registry.example/shuetl-host@sha256:{'a' * 64}",
            "SHUETL_FACTORY": "trusted_host:build",
        },
    )
    assert valid.returncode == 0, valid.stderr

    mutable = subprocess.run(
        ["sh", str(LAUNCHER), "--check"],
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "SHUETL_IMAGE": "registry.example/shuetl-host:latest",
            "SHUETL_FACTORY": "trusted_host:build",
        },
    )
    assert mutable.returncode == 2
    assert "sha256 digest" in mutable.stderr


def test_systemd_launcher_rejects_invalid_digest_characters() -> None:
    result = subprocess.run(
        ["sh", str(LAUNCHER), "--check"],
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "SHUETL_IMAGE": f"registry.example/shuetl-host@sha256:{'g' * 64}",
            "SHUETL_FACTORY": "trusted_host:build",
        },
    )
    assert result.returncode == 2
    assert "invalid sha256 digest" in result.stderr
