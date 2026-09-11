"""Check that built artifacts contain only the Phase 0.1 package surface."""

from __future__ import annotations

import argparse
import csv
import io
import zipfile
from pathlib import Path

VERSION = "0.1.0"
ALLOWED_WHEEL_FILES = {
    f"shuetl-{VERSION}.dist-info/METADATA",
    f"shuetl-{VERSION}.dist-info/RECORD",
    f"shuetl-{VERSION}.dist-info/WHEEL",
    f"shuetl-{VERSION}.dist-info/licenses/LICENSE",
    "shuetl/__init__.py",
    "shuetl/py.typed",
}


def _wheel_path(dist: Path) -> Path:
    wheels = sorted(dist.glob(f"shuetl-{VERSION}-*.whl"))
    if len(wheels) != 1:
        raise ValueError(
            f"expected one ShuETL {VERSION} wheel in {dist}, found {wheels}"
        )
    return wheels[0]


def check_wheel(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        unexpected = sorted(names - ALLOWED_WHEEL_FILES)
        missing = sorted(ALLOWED_WHEEL_FILES - names)
        if unexpected or missing:
            raise ValueError(
                f"wheel contents unexpected={unexpected} missing={missing}"
            )
        metadata_name = f"shuetl-{VERSION}.dist-info/METADATA"
        metadata = archive.read(metadata_name).decode("utf-8")
        requires_dist = [
            line for line in metadata.splitlines() if line.startswith("Requires-Dist:")
        ]
        unconditional = [line for line in requires_dist if "extra ==" not in line]
        if unconditional:
            raise ValueError(
                f"unconditional runtime dependencies found: {unconditional}"
            )
        if not any(
            "extra == 'test'" in line or 'extra == "test"' in line
            for line in requires_dist
        ):
            raise ValueError("test extra is missing from wheel metadata")
        record = archive.read(f"shuetl-{VERSION}.dist-info/RECORD").decode("utf-8")
        csv.reader(io.StringIO(record))


def check_sdist(path: Path) -> None:
    if path.suffix != ".gz" or path.name != f"shuetl-{VERSION}.tar.gz":
        raise ValueError(f"unexpected sdist path: {path}")
    import tarfile

    with tarfile.open(path, "r:gz") as archive:
        names = {member.name for member in archive.getmembers()}
        if not any(name.endswith("/pyproject.toml") for name in names):
            raise ValueError("sdist does not contain pyproject.toml")
        if not any(name.endswith("/src/shuetl/py.typed") for name in names):
            raise ValueError("sdist does not contain py.typed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    args = parser.parse_args(argv)
    wheel = _wheel_path(args.dist)
    check_wheel(wheel)
    sdist = args.dist / f"shuetl-{VERSION}.tar.gz"
    check_sdist(sdist)
    print(f"artifact contents verified: {wheel.name}, {sdist.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
