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

POSTGRESQL_HEAD = "005_cp1_reference"
POSTGRESQL_MIGRATION_VERSIONS = (
    "001_registry_cp2",
    "002_durable_cp3",
    "003_cp4_governance",
    "004_schedules_0_47",
    POSTGRESQL_HEAD,
)

POSTGRESQL_REQUIRED_TABLES = frozenset(
    {
        "etlantic_sqlmodel_schema_version",
        "cp_cp4_governance_snapshot",
        "cp_definitions",
        "cp_durable_outbox_entity",
        "cp_durable_snapshot",
        "cp_durable_submission_entity",
        "cp_events",
        "cp_registry_aliases",
        "cp_registry_environments",
        "cp_registry_logical",
        "cp_registry_promotions",
        "cp_registry_revisions",
        "cp_registry_security_domains",
        "cp_registry_tenants",
        "cp_registry_workspaces",
        "cp_schedule_snapshot",
        "cp_submissions",
    }
)

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
        from sqlalchemy import inspect as sqlalchemy_inspect

        with engine.connect() as connection:
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            raw_server = str(connection.exec_driver_sql("SHOW server_version").scalar())
            server_version = raw_server.split(maxsplit=1)[0]
            if server_version != expected_server:
                return PostgreSQLSchemaStatus("wrong-server", None, server_version)

            tables = set(sqlalchemy_inspect(connection).get_table_names())
            version_table = "etlantic_sqlmodel_schema_version"
            if version_table not in tables:
                return PostgreSQLSchemaStatus("fresh", None, server_version)

            rows = connection.exec_driver_sql(
                "SELECT id, version FROM etlantic_sqlmodel_schema_version ORDER BY id"
            ).fetchall()
            if len(rows) != 1 or rows[0][0] != 1 or not rows[0][1]:
                return PostgreSQLSchemaStatus("corrupt", None, server_version)
            version = str(rows[0][1])
            if version not in POSTGRESQL_MIGRATION_VERSIONS:
                return PostgreSQLSchemaStatus(
                    "ahead_or_unknown", version, server_version
                )
            if version != POSTGRESQL_HEAD:
                return PostgreSQLSchemaStatus("behind", version, server_version)
            missing = tuple(sorted(POSTGRESQL_REQUIRED_TABLES - tables))
            if missing:
                return PostgreSQLSchemaStatus(
                    "corrupt", version, server_version, missing
                )
            return PostgreSQLSchemaStatus("head", version, server_version)
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
