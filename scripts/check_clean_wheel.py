"""Verify local and optional provider imports from an isolated wheel."""

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
POSTGRESQL_SETTINGS_ENV = (
    "SHUETL_PROFILE",
    "SHUETL_ROLE",
    "SHUETL_PROVIDER",
    "SHUETL_IDENTITY",
    "SHUETL_DATABASE_URL",
    "SHUETL_RUNTIME_DATABASE_URL",
    "SHUETL_POSTGRESQL_SSLMODE",
)


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
    examples = {
        "core": [
            ROOT / "examples" / "phase_0_3_quickstart.py",
            ROOT / "examples" / "phase_0_5_oidc_host.py",
            ROOT / "examples" / "phase_0_5_session_host.py",
            ROOT / "examples" / "phase_0_5_development_static.py",
        ],
        "sqlite": [ROOT / "examples" / "phase_0_3_sqlite.py"],
        "postgresql": [],
        "foundry": [],
    }
    for example in (path for paths in examples.values() for path in paths):
        if not example.exists():
            raise FileNotFoundError(example)
    with tempfile.TemporaryDirectory(prefix=f"shuetl-{VERSION}-wheel-") as temp:
        temp_root = Path(temp)
        work_dir = temp_root / "work"
        work_dir.mkdir()
        uv = shutil.which("uv")
        if uv is None:
            raise RuntimeError("uv is required for clean-wheel verification")
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        isolated_examples: dict[str, list[Path]] = {key: [] for key in examples}
        for extra, paths in examples.items():
            for example in paths:
                destination = work_dir / example.name
                shutil.copy2(example, destination)
                isolated_examples[extra].append(destination)
        env = {
            **os.environ,
            "PYTHONPATH": "",
            "PYTHONNOUSERSITE": "1",
            "SHUETL_EXPECT_INSTALLED": "1",
        }

        def verify_environment(
            name: str, example_paths: list[Path], extra: str
        ) -> None:
            venv_dir = temp_root / f"venv-{name}"
            _run(
                [uv, "venv", "--python", python_version, "--seed", str(venv_dir)],
                cwd=work_dir,
                env=os.environ.copy(),
            )
            python = _python(venv_dir)
            _run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    f"{wheel}[test{',' + extra if extra else ''}]",
                ],
                cwd=work_dir,
                env=env,
            )
            _run(
                [
                    str(python),
                    "-c",
                    f"""
import importlib.metadata as metadata
import importlib.util
import pathlib
import sysconfig

purelib = pathlib.Path(sysconfig.get_paths()["purelib"]).resolve()
modules = (
    "shuetl",
    "etlantic",
    "etlantic_fastapi",
    "fastapi",
    "pydantic",
    "httpx2",
)
origins = {{}}
for name in modules:
    spec = importlib.util.find_spec(name)
    assert spec is not None and spec.origin is not None, name
    origins[name] = pathlib.Path(spec.origin).resolve()
assert all(path.is_relative_to(purelib) for path in origins.values()), origins
assert metadata.version("shuetl") == "{VERSION}"
assert metadata.version("etlantic") == "0.56.0"
assert metadata.version("etlantic-fastapi") == "0.56.0"
assert metadata.version("sqlalchemy") == "2.0.52"
print(origins)
""",
                ],
                cwd=work_dir,
                env=env,
            )
            example_env = env
            if name != "postgresql":
                example_env = env.copy()
                for setting in POSTGRESQL_SETTINGS_ENV:
                    example_env.pop(setting, None)
            for example_path in example_paths:
                _run(
                    [str(python), str(example_path)],
                    cwd=work_dir,
                    env=example_env,
                )
            if name == "postgresql":
                _run(
                    [
                        str(python),
                        "-c",
                        (
                            "import psycopg, shuetl; "
                            "from shuetl import PostgreSQLProviderBundle"
                        ),
                    ],
                    cwd=work_dir,
                    env=env,
                )
                if env.get("SHUETL_DATABASE_URL"):
                    if not env.get("SHUETL_RUNTIME_DATABASE_URL"):
                        raise RuntimeError(
                            "SHUETL_RUNTIME_DATABASE_URL is required when "
                            "SHUETL_DATABASE_URL is configured"
                        )
                    integration_test = work_dir / "test_postgresql.py"
                    shutil.copy2(
                        ROOT / "tests" / "integration" / "test_postgresql.py",
                        integration_test,
                    )
                    junit_report = temp_root / "installed-postgresql-tests.xml"
                    _run(
                        [
                            str(python),
                            "-m",
                            "pytest",
                            str(integration_test),
                            "-q",
                            f"--junitxml={junit_report}",
                        ],
                        cwd=work_dir,
                        env=env,
                    )
                    _run(
                        [
                            str(python),
                            str(ROOT / "scripts" / "check_pytest_no_skips.py"),
                            str(junit_report),
                        ],
                        cwd=work_dir,
                        env=env,
                    )
                else:
                    print(
                        "installed PostgreSQL integration not run: "
                        "SHUETL_DATABASE_URL is not configured"
                    )
                _run(
                    [
                        str(python),
                        "-c",
                        (
                            "import importlib.metadata as metadata; "
                            "assert metadata.version('etlantic-sqlmodel') == '0.56.0'; "
                            "assert metadata.version('etlantic-sql') == '0.56.0'; "
                            "import etlantic_sql"
                        ),
                    ],
                    cwd=work_dir,
                    env=env,
                )
            if name == "foundry":
                _run(
                    [
                        str(python),
                        "-c",
                        (
                            "import importlib.metadata as metadata; "
                            "assert metadata.version('etlantic-foundry') == '0.56.0'; "
                            "import etlantic_foundry"
                        ),
                    ],
                    cwd=work_dir,
                    env=env,
                )

        def verify_cli_rejects_mismatched_role(python: Path) -> None:
            executable = python.parent / ("shuetl.exe" if os.name == "nt" else "shuetl")
            secret = (
                "postgresql+psycopg://operator:role-smoke-secret@db.example/control"
            )
            result = subprocess.run(
                [
                    str(executable),
                    "serve",
                    "--role",
                    "gateway",
                    "--factory",
                    "trusted_host:build",
                ],
                cwd=work_dir,
                env={
                    **env,
                    "SHUETL_ROLE": "scheduler",
                    "SHUETL_DATABASE_URL": secret,
                },
                check=False,
                capture_output=True,
                text=True,
            )
            output = result.stdout + result.stderr
            if result.returncode != 2 or "must match SHUETL_ROLE" not in output:
                raise AssertionError("installed CLI did not reject mismatched role")
            if secret in output:
                raise AssertionError("installed CLI exposed the database URL")

        verify_environment("core", isolated_examples["core"], "")
        verify_cli_rejects_mismatched_role(_python(temp_root / "venv-core"))
        verify_environment("sqlite", isolated_examples["sqlite"], "sqlite")
        verify_environment("postgresql", [], "postgresql")
        verify_environment("foundry", [], "foundry")


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
