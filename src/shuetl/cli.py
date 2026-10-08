"""Command-line diagnostics for ShuETL."""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import sys

from pydantic import ValidationError

from .diagnostics import DoctorReport
from .errors import CompatibilityError, ProviderReadinessError
from .postgresql import upgrade_postgresql
from .runtime import build_managed_runtime
from .settings import ShuETLSettings
from .supervisor import serve_gateway, serve_runtime_role


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shuetl")
    parser.add_argument("--version", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--format", choices=("text", "json"), default="text")
    database = subparsers.add_parser("database")
    database_subparsers = database.add_subparsers(dest="database_command")
    database_subparsers.add_parser("upgrade")
    serve = subparsers.add_parser("serve")
    serve.add_argument(
        "--role", choices=("gateway", "scheduler", "worker"), required=True
    )
    serve.add_argument("--factory", required=True)
    serve.add_argument("--kind", choices=("runs", "actions"))
    args = parser.parse_args(argv)
    if args.version:
        print(f"shuetl {importlib.metadata.version('shuetl')}")
        return 0
    if args.command == "doctor":
        try:
            report = DoctorReport.inspect()
            if args.format == "json":
                print(report.model_dump_json(by_alias=True, indent=2))
            else:
                print(report.render_text())
            return 1 if report.status == "fail" else 0
        except Exception:
            print("shuetl doctor failed", file=sys.stderr)
            return 2
    if args.command == "database" and args.database_command == "upgrade":
        try:
            head = upgrade_postgresql(ShuETLSettings())
            print(f"PostgreSQL schema is at {head}.")
            return 0
        except Exception:
            print("shuetl database upgrade failed", file=sys.stderr)
            return 1
    if args.command == "serve":
        configured_role = os.environ.get("SHUETL_ROLE")
        if configured_role is None or configured_role != args.role:
            print("shuetl serve failed: --role must match SHUETL_ROLE", file=sys.stderr)
            return 2
        configured_factory = os.environ.get("SHUETL_FACTORY")
        if configured_factory is not None and configured_factory != args.factory:
            print(
                "shuetl serve failed: --factory must match SHUETL_FACTORY",
                file=sys.stderr,
            )
            return 2
        try:
            overrides: dict[str, object] = {"role": args.role, "factory": args.factory}
            configured_kind = os.environ.get("SHUETL_WORKER_KIND")
            if args.kind is not None:
                if configured_kind is not None and configured_kind != args.kind:
                    raise ValueError("--kind must match SHUETL_WORKER_KIND")
                overrides["worker_kind"] = args.kind
            settings = ShuETLSettings(**overrides)
            runtime = build_managed_runtime(settings)
            if settings.role == "gateway":
                return serve_gateway(runtime)
            return serve_runtime_role(runtime)
        except (
            ValidationError,
            CompatibilityError,
            ProviderReadinessError,
            ValueError,
        ):
            print(
                "shuetl serve failed; check configuration, package compatibility, "
                "and provider readiness",
                file=sys.stderr,
            )
            return 2
        except Exception:
            print("shuetl serve failed", file=sys.stderr)
            return 2
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
