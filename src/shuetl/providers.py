"""Local provider composition for the Phase 0.3 runtime."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Literal
from urllib.parse import urlsplit

from etlantic.control_plane import (
    Authorizer,
    DefinitionRepository,
    DurableWorkStore,
    EventStore,
    RegistryProvider,
    ScheduleStore,
    SubmissionStore,
)
from etlantic.control_plane.memory import (
    MemoryDefinitionRepository,
    MemoryEventStore,
    MemorySubmissionStore,
)
from etlantic_fastapi import ETLanticAPI
from etlantic_fastapi.auth import ContextFactory, PrincipalDependency

from ._secrets import _database_url_value
from .compatibility import validate_core, validate_postgresql, validate_sqlite
from .errors import CapabilityError, CompatibilityError, ProviderReadinessError
from .postgresql import (
    POSTGRESQL_HEAD,
    create_postgresql_engine,
    inspect_postgresql_engine,
)
from .settings import ShuETLSettings

SQLITE_HEAD = "005_cp1_reference"


@dataclass
class _BundleState:
    closed: bool = False
    lock: Lock = field(default_factory=Lock)


@dataclass(frozen=True, slots=True)
class LocalProviderBundle:
    """The exact provider objects used by one local ETLantic API."""

    settings: ShuETLSettings
    api: ETLanticAPI
    authorizer: Authorizer
    definitions: DefinitionRepository
    submissions: SubmissionStore
    events: EventStore
    provider: Literal["memory", "sqlite"]
    development_only: Literal[True]
    _engine: Any = field(default=None, repr=False, compare=False)
    _state: _BundleState = field(
        default_factory=_BundleState, repr=False, compare=False
    )

    @classmethod
    def create(
        cls,
        settings: ShuETLSettings,
        *,
        authorizer: Authorizer,
        context_factory: ContextFactory,
        principal_dependency: PrincipalDependency,
    ) -> LocalProviderBundle:
        """Build a local API using caller-provided identity and authorization."""

        if not isinstance(authorizer, Authorizer):
            raise TypeError("authorizer must implement authorize")
        if not _accepts_positional(context_factory, 2):
            raise TypeError("context_factory must accept principal and request")
        if not _accepts_positional(principal_dependency, 1):
            raise TypeError("principal_dependency must accept request")
        if type(settings) is not ShuETLSettings:
            raise TypeError("settings must be a ShuETLSettings instance")

        engine: Any = None
        try:
            validate_core()
            if settings.provider == "memory":
                definitions = MemoryDefinitionRepository()
                submissions = MemorySubmissionStore()
                events = MemoryEventStore()
            elif settings.provider == "sqlite":
                validate_sqlite()
                database_url = settings.database_url
                if database_url is None:
                    raise ProviderReadinessError(
                        "SQLite database configuration is missing"
                    )
                raw_url = _database_url_value(database_url)
                assert raw_url is not None
                database_path = _sqlite_path(raw_url)
                if not database_path.exists() or not database_path.is_file():
                    raise ProviderReadinessError("SQLite database file is not ready")
                from etlantic_sqlmodel import (  # type: ignore[import-not-found]
                    SQLModelDefinitionRepository,
                    SqlModelEventStore,
                    SQLModelSubmissionStore,
                    create_sqlite_engine,
                )

                engine = create_sqlite_engine(
                    raw_url,
                    connect_args={"timeout": settings.provider_connect_timeout_seconds},
                )
                from sqlalchemy import inspect as inspect_engine

                if (
                    "etlantic_sqlmodel_schema_version"
                    not in inspect_engine(engine).get_table_names()
                ):
                    raise ProviderReadinessError(
                        "SQLite schema is not provisioned at the required head"
                    )
                if _read_sqlite_version(engine) != SQLITE_HEAD:
                    raise ProviderReadinessError(
                        "SQLite schema is not at the required head"
                    )
                definitions = SQLModelDefinitionRepository(engine)
                submissions = SQLModelSubmissionStore(engine)
                events = SqlModelEventStore(engine)
            else:
                raise ProviderReadinessError(
                    "PostgreSQL providers require PostgreSQLProviderBundle"
                )

            api = ETLanticAPI(
                authorizer=authorizer,
                definitions=definitions,
                submissions=submissions,
                events=events,
                context_factory=context_factory,
                principal_dependency=principal_dependency,
                profile="development",
            )
            return cls(
                settings=settings,
                api=api,
                authorizer=authorizer,
                definitions=definitions,
                submissions=submissions,
                events=events,
                provider=settings.provider,
                development_only=True,
                _engine=engine,
            )
        except (ProviderReadinessError, CompatibilityError, CapabilityError):
            if engine is not None:
                engine.dispose()
            raise
        except Exception as exc:
            if engine is not None:
                engine.dispose()
            raise ProviderReadinessError(
                "local provider initialization failed"
            ) from exc

    @property
    def closed(self) -> bool:
        return self._state.closed

    def close(self) -> None:
        """Dispose resources; repeated calls are intentionally harmless."""

        with self._state.lock:
            if self._state.closed:
                return
            if self._engine is not None:
                self._engine.dispose()
            self._state.closed = True


@dataclass(frozen=True, slots=True)
class PostgreSQLProviderBundle:
    """Qualified ETLantic PostgreSQL providers sharing one SQLAlchemy engine."""

    settings: ShuETLSettings
    api: ETLanticAPI
    authorizer: Authorizer
    registry: RegistryProvider
    definitions: DefinitionRepository
    submissions: SubmissionStore
    events: EventStore
    durable_work: DurableWorkStore
    schedules: ScheduleStore
    provider: Literal["postgresql"]
    development_only: Literal[False]
    _engine: Any = field(default=None, repr=False, compare=False)
    _state: _BundleState = field(
        default_factory=_BundleState, repr=False, compare=False
    )

    @classmethod
    def create(
        cls,
        settings: ShuETLSettings,
        *,
        authorizer: Authorizer,
        context_factory: ContextFactory,
        principal_dependency: PrincipalDependency,
    ) -> PostgreSQLProviderBundle:
        """Build the qualified production-profile provider graph."""

        if not isinstance(authorizer, Authorizer):
            raise TypeError("authorizer must implement authorize")
        if not _accepts_positional(context_factory, 2):
            raise TypeError("context_factory must accept principal and request")
        if not _accepts_positional(principal_dependency, 1):
            raise TypeError("principal_dependency must accept request")
        if type(settings) is not ShuETLSettings:
            raise TypeError("settings must be a ShuETLSettings instance")
        if settings.profile != "postgresql-pilot" or settings.provider != "postgresql":
            raise ProviderReadinessError(
                "PostgreSQLProviderBundle requires the postgresql-pilot "
                "PostgreSQL profile"
            )

        engine: Any = None
        try:
            validate_postgresql()
            engine = create_postgresql_engine(settings)
            status = inspect_postgresql_engine(engine)
            if status.state != "head":
                raise ProviderReadinessError(
                    _postgresql_status_message(status.state, status.missing_tables)
                )
            from etlantic.control_plane import RegistryDefinitionRepository
            from etlantic_sqlmodel.control_plane import (  # type: ignore[import-not-found]
                SQLModelDurableWorkStore,
                SqlModelEventStore,
                SqlModelRegistryProvider,
                SQLModelScheduleStore,
                SQLModelSubmissionStore,
            )

            registry: Any = SqlModelRegistryProvider(engine)
            definitions = RegistryDefinitionRepository(registry)
            submissions = SQLModelSubmissionStore(engine)
            events = SqlModelEventStore(engine)
            durable_work = SQLModelDurableWorkStore(engine)
            schedules = SQLModelScheduleStore(engine)
            # The convenience factory creates a second definition repository.
            # Keep the bundle and API on the exact same canonical object.
            api = ETLanticAPI(
                authorizer=authorizer,
                definitions=definitions,
                registry=registry,
                submissions=submissions,
                events=events,
                context_factory=context_factory,
                principal_dependency=principal_dependency,
                profile="production",
                durable_work=durable_work,
                schedule_store=schedules,
            )
            return cls(
                settings=settings,
                api=api,
                authorizer=authorizer,
                registry=registry,
                definitions=definitions,
                submissions=submissions,
                events=events,
                durable_work=durable_work,
                schedules=schedules,
                provider="postgresql",
                development_only=False,
                _engine=engine,
            )
        except (ProviderReadinessError, CompatibilityError, CapabilityError):
            if engine is not None:
                engine.dispose()
            raise
        except BaseException as exc:
            if engine is not None:
                engine.dispose()
            if isinstance(exc, Exception):
                raise ProviderReadinessError(
                    "PostgreSQL provider initialization failed"
                ) from exc
            raise

    @property
    def closed(self) -> bool:
        return self._state.closed

    def close(self) -> None:
        """Dispose the engine exactly once; repeated calls are harmless."""

        with self._state.lock:
            if self._state.closed:
                return
            if self._engine is not None:
                self._engine.dispose()
            self._state.closed = True


def _postgresql_status_message(state: str, missing_tables: tuple[str, ...]) -> str:
    if missing_tables:
        return "PostgreSQL schema is missing required provider tables"
    if state == "fresh":
        return f"PostgreSQL schema is not provisioned at {POSTGRESQL_HEAD}"
    if state == "behind":
        return f"PostgreSQL schema is not at the required head {POSTGRESQL_HEAD}"
    if state == "wrong-server":
        return "PostgreSQL server version is not qualified"
    if state == "unreachable":
        return "PostgreSQL database is unreachable"
    return "PostgreSQL schema is unknown or corrupt"


def _read_sqlite_version(engine: Any) -> str | None:
    with engine.connect() as connection:
        row = connection.exec_driver_sql(
            "SELECT version FROM etlantic_sqlmodel_schema_version WHERE id = 1"
        ).fetchone()
    return None if row is None else str(row[0])


def _sqlite_path(value: str) -> Path:
    parsed = urlsplit(value)
    raw_path = parsed.path
    if raw_path.startswith("//"):
        return Path("/" + raw_path.lstrip("/"))
    return Path(raw_path.lstrip("/"))


def _accepts_positional(value: Any, count: int) -> bool:
    if not callable(value):
        return False
    try:
        inspect.signature(value).bind(*([object()] * count))
    except (TypeError, ValueError):
        return False
    return True


__all__ = [
    "LocalProviderBundle",
    "PostgreSQLProviderBundle",
    "SQLITE_HEAD",
    "POSTGRESQL_HEAD",
]
