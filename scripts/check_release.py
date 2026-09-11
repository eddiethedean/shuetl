"""Run the complete local Phase 0.3 release gate."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
RELEASE_SERIES = ".".join(str(PROJECT["project"]["version"]).split(".")[:2])


def run_step(label: str, command: list[str]) -> None:
    print(f"== {label} ==")
    subprocess.run(command, cwd=ROOT, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    uv = shutil.which("uv")
    if uv is None:
        print("uv is required for the release gate", file=sys.stderr)
        return 1
    uv_run = [uv, "run"]
    run_step("lock", [uv, "lock", "--check"])
    run_step(
        "sync",
        [uv, "sync", "--locked", "--all-groups", "--extra", "test"],
    )
    run_step("format", [*uv_run, "ruff", "format", "--check", "."])
    run_step("lint", [*uv_run, "ruff", "check", "."])
    run_step("typing", [*uv_run, "pyright"])
    run_step(
        "boundary",
        [
            *uv_run,
            "python",
            "scripts/check_boundaries.py",
            "--openapi",
            f"docs/evidence/{RELEASE_SERIES}/openapi.normalized.json",
        ],
    )
    run_step("tests", [*uv_run, "pytest", "-q"])
    run_step("build", [uv, "build"])
    run_step("artifact", [*uv_run, "python", "scripts/check_artifact.py"])
    run_step(
        "openapi",
        [*uv_run, "python", "scripts/capture_openapi.py", "--check"],
    )
    run_step("clean-wheel", [*uv_run, "python", "scripts/check_clean_wheel.py"])
    run_step(
        "evidence",
        [
            *uv_run,
            "python",
            "scripts/check_evidence.py",
            "--evidence",
            f"docs/evidence/{RELEASE_SERIES}",
        ],
    )
    print(f"Phase {RELEASE_SERIES} release gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
