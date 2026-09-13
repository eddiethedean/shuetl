"""Command-line diagnostics for ShuETL."""

from __future__ import annotations

import argparse
import importlib.metadata
import sys

from .diagnostics import DoctorReport
from .postgresql import upgrade_postgresql
from .settings import ShuETLSettings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shuetl")
    parser.add_argument("--version", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--format", choices=("text", "json"), default="text")
    database = subparsers.add_parser("database")
    database_subparsers = database.add_subparsers(dest="database_command")
    database_subparsers.add_parser("upgrade")
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
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
