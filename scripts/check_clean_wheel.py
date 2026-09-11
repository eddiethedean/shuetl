"""Verify the Phase 0.1 spike from an isolated wheel installation."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "0.1.0"
ROOT = Path(__file__).resolve().parents[1]


def _python(venv_dir: Path) -> Path:
    executable = "python.exe" if os.name == "nt" else "python"
    return venv_dir / ("Scripts" if os.name == "nt" else "bin") / executable


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def find_wheel(dist: Path) -> Path:
    wheels = sorted(dist.glob(f"shuetl-{VERSION}-*.whl"))
    if len(wheels) != 1:
        raise ValueError(f"expected one ShuETL wheel in {dist}, found {wheels}")
    return wheels[0].resolve()


def verify(wheel: Path) -> None:
    wheel = wheel.resolve()
    spike = ROOT / "spikes" / "phase_0_1_memory_mount.py"
    if not spike.exists():
        raise FileNotFoundError(spike)
    with tempfile.TemporaryDirectory(prefix="shuetl-0.1-wheel-") as temp:
        temp_root = Path(temp)
        venv_dir = temp_root / "venv"
        work_dir = temp_root / "work"
        work_dir.mkdir()
        uv = shutil.which("uv")
        if uv is None:
            raise RuntimeError("uv is required for clean-wheel verification")
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        _run(
            [uv, "venv", "--python", python_version, "--seed", str(venv_dir)],
            cwd=work_dir,
            env=os.environ.copy(),
        )
        python = _python(venv_dir)
        _run(
            [str(python), "-m", "pip", "install", f"{wheel}[test]"],
            cwd=work_dir,
            env={**os.environ, "PYTHONPATH": "", "PYTHONNOUSERSITE": "1"},
        )
        isolated_spike = work_dir / spike.name
        shutil.copy2(spike, isolated_spike)
        env = {
            **os.environ,
            "PYTHONPATH": "",
            "PYTHONNOUSERSITE": "1",
            "SHUETL_EXPECT_INSTALLED": "1",
        }
        _run([str(python), str(isolated_spike)], cwd=work_dir, env=env)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    args = parser.parse_args(argv)
    wheel = args.wheel.resolve() if args.wheel else find_wheel(args.dist.resolve())
    verify(wheel)
    print(f"clean-wheel verification passed: {wheel.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
