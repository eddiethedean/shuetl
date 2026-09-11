"""Verify Phase 0.3 memory and SQLite examples from an isolated wheel."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]


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
    example = ROOT / "examples" / "phase_0_3_quickstart.py"
    sqlite_example = ROOT / "examples" / "phase_0_3_sqlite.py"
    if not example.exists():
        raise FileNotFoundError(example)
    if not sqlite_example.exists():
        raise FileNotFoundError(sqlite_example)
    with tempfile.TemporaryDirectory(prefix=f"shuetl-{VERSION}-wheel-") as temp:
        temp_root = Path(temp)
        work_dir = temp_root / "work"
        work_dir.mkdir()
        uv = shutil.which("uv")
        if uv is None:
            raise RuntimeError("uv is required for clean-wheel verification")
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        isolated_example = work_dir / example.name
        isolated_sqlite_example = work_dir / sqlite_example.name
        shutil.copy2(example, isolated_example)
        shutil.copy2(sqlite_example, isolated_sqlite_example)
        env = {
            **os.environ,
            "PYTHONPATH": "",
            "PYTHONNOUSERSITE": "1",
            "SHUETL_EXPECT_INSTALLED": "1",
        }

        def verify_environment(name: str, example_path: Path, sqlite: bool) -> None:
            venv_dir = temp_root / f"venv-{name}"
            _run(
                [uv, "venv", "--python", python_version, "--seed", str(venv_dir)],
                cwd=work_dir,
                env=os.environ.copy(),
            )
            python = _python(venv_dir)
            _run(
                [str(python), "-m", "pip", "install", f"{wheel}[test]"],
                cwd=work_dir,
                env=env,
            )
            if sqlite:
                _run(
                    [str(python), "-m", "pip", "install", f"{wheel}[sqlite]"],
                    cwd=work_dir,
                    env=env,
                )
            _run([str(python), str(example_path)], cwd=work_dir, env=env)

        verify_environment("core", isolated_example, sqlite=False)
        verify_environment("sqlite", isolated_sqlite_example, sqlite=True)


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
