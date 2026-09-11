"""Command-line diagnostics for ShuETL."""

from __future__ import annotations

import argparse
import importlib.metadata
import sys

from .diagnostics import DoctorReport


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shuetl")
    parser.add_argument("--version", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    if args.version:
        print(importlib.metadata.version("shuetl"))
        return 0
    if args.command == "doctor":
        report = DoctorReport.inspect()
        if args.format == "json":
            print(report.model_dump_json(by_alias=True, indent=2))
        else:
            print(report.render_text())
        return 1 if report.status == "fail" else 0
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
