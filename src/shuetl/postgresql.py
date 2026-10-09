"""Qualified PostgreSQL engine and provider-migration helpers.

The module keeps optional SQLAlchemy/Psycopg imports lazy so a core or SQLite
installation can still import ShuETL without the PostgreSQL extra.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal

from ._secrets import _database_url_value
from .compatibility import validate_postgresql
from .errors import ProviderReadinessError
from .settings import ShuETLSettings

# The selected provider contract, not a downstream migration implementation.
POSTGRESQL_HEAD = "014_cp1_complete_principal_idempotency_0_56"
POSTGRESQL_MIGRATION_VERSIONS: tuple[str, ...]
POSTGRESQL_REQUIRED_TABLES: frozenset[str]


def __getattr__(name: str) -> Any:
    """Keep legacy inventories available through optional provider metadata."""
    if name == "POSTGRESQL_MIGRATION_VERSIONS":
        from etlantic_sqlmodel.migrations import VERSIONS

        return tuple(VERSIONS)
    if name == "POSTGRESQL_REQUIRED_TABLES":
        from etlantic_sqlmodel import schema_requirements

        return frozenset(item.name for item in schema_requirements().objects)
    raise AttributeError(name)


SchemaState = Literal[
    "fresh",
    "behind",
    "head",
    "ahead_or_unknown",
    "corrupt",
    "wrong-server",
    "unreachable",
]


@dataclass(frozen=True, slots=True)
class PostgreSQLSchemaStatus:
    """Bounded, redacted result of a PostgreSQL compatibility inspection."""

    state: SchemaState
    version: str | None
    server_version: str | None
    missing_tables: tuple[str, ...] = ()


def create_postgresql_engine(settings: ShuETLSettings) -> Any:
    """Create the qualified synchronous SQLAlchemy engine for one pilot DB."""

    if settings.provider != "postgresql":
        raise ProviderReadinessError("PostgreSQL settings are required")
    raw_url = _database_url_value(settings.database_url)
    if raw_url is None:
        raise ProviderReadinessError("PostgreSQL database configuration is missing")
    try:
        from sqlalchemy import create_engine

        return create_engine(
            raw_url,
            connect_args={
                "connect_timeout": math.ceil(settings.provider_connect_timeout_seconds),
                "sslmode": settings.postgresql_sslmode,
            },
            pool_pre_ping=True,
        )
    except Exception as exc:
        raise ProviderReadinessError("PostgreSQL engine initialization failed") from exc


def inspect_postgresql_engine(
    engine: Any,
    *,
    expected_server: str = "18.6",
) -> PostgreSQLSchemaStatus:
    """Inspect server and migration state without issuing any DDL or commit."""

    try:
        from etlantic_sqlmodel import inspect_schema

        with engine.connect() as connection:
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            raw_server = str(connection.exec_driver_sql("SHOW server_version").scalar())
            server_version = raw_server.split(maxsplit=1)[0]
            if server_version != expected_server:
                return PostgreSQLSchemaStatus("wrong-server", None, server_version)

        status = inspect_schema(engine)
        states: dict[str, SchemaState] = {
            "fresh": "fresh",
            "behind": "behind",
            "compatible": "head",
            "unknown_or_ahead": "ahead_or_unknown",
            "partial_or_corrupt": "corrupt",
            "unreachable": "unreachable",
        }
        return PostgreSQLSchemaStatus(
            states[status.compatibility.value],
            status.observed_version,
            server_version,
            status.missing_objects,
        )
    except Exception:
        return PostgreSQLSchemaStatus("unreachable", None, None)


def inspect_postgresql(settings: ShuETLSettings) -> PostgreSQLSchemaStatus:
    """Inspect one configured PostgreSQL database and always dispose its engine."""

    engine = None
    try:
        engine = create_postgresql_engine(settings)
        return inspect_postgresql_engine(engine)
    finally:
        if engine is not None:
            engine.dispose()


def upgrade_postgresql(settings: ShuETLSettings) -> str:
    """Run the pinned provider migration chain and verify its resulting head."""

    if settings.profile != "postgresql-pilot" or settings.provider != "postgresql":
        raise ProviderReadinessError(
            "database upgrade requires the postgresql-pilot PostgreSQL profile"
        )
    try:
        validate_postgresql()
    except Exception as exc:
        raise ProviderReadinessError(
            "PostgreSQL provider dependencies are not qualified"
        ) from exc
    engine = None
    try:
        engine = create_postgresql_engine(settings)
        before = inspect_postgresql_engine(engine)
        if before.state in {
            "wrong-server",
            "ahead_or_unknown",
            "corrupt",
            "unreachable",
        }:
            raise ProviderReadinessError(
                f"PostgreSQL schema cannot be upgraded from {before.state} state"
            )
        from etlantic_sqlmodel.migrations import upgrade

        result = upgrade(engine)
        after = inspect_postgresql_engine(engine)
        if result != POSTGRESQL_HEAD or after.state != "head":
            raise ProviderReadinessError(
                "PostgreSQL migration did not reach the required head"
            )
        return POSTGRESQL_HEAD
    except ProviderReadinessError:
        raise
    except Exception as exc:
        raise ProviderReadinessError("PostgreSQL migration failed") from exc
    finally:
        if engine is not None:
            engine.dispose()


__all__ = [
    "POSTGRESQL_HEAD",
    "POSTGRESQL_MIGRATION_VERSIONS",
    "POSTGRESQL_REQUIRED_TABLES",
    "PostgreSQLSchemaStatus",
]
