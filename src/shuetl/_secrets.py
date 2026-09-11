"""Private secret access helpers shared by ShuETL internals."""

from __future__ import annotations

from pydantic import SecretStr


def _database_url_value(value: SecretStr | None) -> str | None:
    """Read the database URL only inside an internal, non-public helper."""

    return value.get_secret_value() if value is not None else None
