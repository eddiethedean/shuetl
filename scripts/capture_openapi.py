"""Capture or verify normalized OpenAPI evidence."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from spikes.phase_0_1_memory_mount import (  # noqa: E402
    build_direct_app,
    build_graph,
    normalized_openapi,
)

from shuetl import ShuETL  # noqa: E402

VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
    "project"
]["version"]
DEFAULT_OUTPUT = (
    ROOT
    / "docs"
    / "evidence"
    / ".".join(str(VERSION).split(".")[:2])
    / "openapi.normalized.json"
)


def capture() -> dict[str, Any]:
    """Build both apps and return the normalized upstream contract."""

    graph = build_graph()
    embedded = FastAPI()
    ShuETL(api=graph.api).mount(embedded, prefix="/etl")
    direct = build_direct_app()
    contract = normalized_openapi(embedded.openapi(), prefix="/etl")
    if contract != normalized_openapi(direct.openapi()):
        raise AssertionError("ShuETL OpenAPI differs from direct upstream OpenAPI")
    return contract


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare with the committed artifact instead of writing it",
    )
    args = parser.parse_args(argv)
    actual = capture()
    encoded = json.dumps(actual, indent=2, sort_keys=True) + "\n"
    if args.check:
        expected = args.output.read_text(encoding="utf-8")
        if expected != encoded:
            raise SystemExit(f"OpenAPI evidence differs: {args.output}")
        print(f"OpenAPI evidence verified: {args.output}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded, encoding="utf-8")
    print(f"OpenAPI evidence written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
