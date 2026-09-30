"""Fail a required pytest gate when it skips tests or executes no tests."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def counts(path: Path) -> tuple[int, int]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    tests = sum(int(suite.get("tests", "0")) for suite in suites)
    skipped = sum(int(suite.get("skipped", "0")) for suite in suites)
    return tests, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("junit", type=Path)
    args = parser.parse_args(argv)
    try:
        tests, skipped = counts(args.junit)
    except (OSError, ET.ParseError, ValueError) as exc:
        print(f"cannot inspect required pytest results: {exc}", file=sys.stderr)
        return 1
    if tests == 0 or skipped:
        print(
            f"required pytest gate executed {tests} tests and skipped {skipped}; "
            "a live PostgreSQL run must execute every selected test",
            file=sys.stderr,
        )
        return 1
    print(f"required pytest gate executed {tests} tests with no skips")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
