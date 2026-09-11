"""Runtime compatibility checks for the qualified ShuETL package train."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, distributions, version

from .errors import CapabilityError, CompatibilityError

CORE_REQUIREMENTS = {
    "shuetl": "0.3.0",
    "etlantic": "0.51.0",
    "etlantic-fastapi": "0.51.0",
    "fastapi": "0.141.1",
    "pydantic": "2.13.5",
    "pydantic-settings": "2.15.0",
}
SQLITE_REQUIREMENTS = {
    "etlantic-sqlmodel": "0.51.0",
    "sqlalchemy": "2.0.52",
}


def _installed(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def installed_versions() -> dict[str, str | None]:
    """Return the stable core and optional package inventory."""

    values = {
        name: _installed(name) for name in (*CORE_REQUIREMENTS, *SQLITE_REQUIREMENTS)
    }
    for dist in distributions():
        name = str(dist.metadata["Name"] or "").lower()
        if name.startswith("etlantic-") or name in SQLITE_REQUIREMENTS:
            values[name] = dist.version
    return dict(sorted(values.items()))


def validate_core() -> dict[str, str | None]:
    """Validate the core runtime train before provider imports."""

    versions = installed_versions()
    mismatches = [
        f"{name}={versions.get(name) or 'missing'} (requires {required})"
        for name, required in CORE_REQUIREMENTS.items()
        if versions.get(name) != required
    ]
    for name, installed in versions.items():
        if (
            name.startswith("etlantic-")
            and installed is not None
            and installed.split(".")[:2] != ["0", "51"]
        ):
            mismatches.append(f"{name}={installed} (requires the ETLantic 0.51 train)")
    if mismatches:
        raise CompatibilityError(
            "incompatible ShuETL runtime packages: " + "; ".join(sorted(mismatches))
        )
    return versions


def validate_sqlite() -> dict[str, str | None]:
    """Validate the optional SQLite provider train without importing it."""

    versions = validate_core()
    missing = [
        f"{name} (requires {required})"
        for name, required in SQLITE_REQUIREMENTS.items()
        if versions.get(name) != required
    ]
    if missing:
        raise CapabilityError(
            "SQLite capability is unavailable; install "
            '`pip install "shuetl[sqlite]==0.3.0"`: ' + ", ".join(missing)
        )
    return versions
