"""Command-line diagnostics and managed role lifecycle."""

from __future__ import annotations

import argparse
import importlib.metadata
import sys
from collections.abc import Sequence


def _parser() -> argparse.ArgumentParser:
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
    serve.add_argument("--kind", choices=("runs", "actions"))
    serve.add_argument("--factory")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"shuetl {importlib.metadata.version('shuetl')}")
        return 0
    if args.command == "doctor":
        from .diagnostics import DoctorReport

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
        from .postgresql import upgrade_postgresql
        from .settings import ShuETLSettings

        try:
            head = upgrade_postgresql(ShuETLSettings())
            print(f"PostgreSQL schema is at {head}.")
            return 0
        except Exception:
            print("shuetl database upgrade failed", file=sys.stderr)
            return 1
    if args.command == "serve":
        from pydantic import ValidationError

        from .settings import ShuETLSettings

        try:
            settings = ShuETLSettings()
            if settings.role != args.role:
                raise ValueError("--role must match SHUETL_ROLE")
            if args.kind is not None and (
                settings.role != "worker" or settings.worker_kind != args.kind
            ):
                raise ValueError("--kind must match worker SHUETL_WORKER_KIND")
        except (ValidationError, ValueError) as exc:
            print(f"shuetl serve configuration failed: {exc}", file=sys.stderr)
            return 2
        try:
            from .compatibility import validate_core, validate_postgresql

            validate_core()
            validate_postgresql()
            from .runtime import serve

            return serve(
                settings, factory_path=args.factory, host=args.host, port=args.port
            )
        except Exception:
            print("shuetl serve failed before startup", file=sys.stderr)
            return 1
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
