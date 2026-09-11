"""Local provider composition for the Phase 0.3 runtime."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlsplit

from etlantic.control_plane import Authorizer
from etlantic.control_plane.memory import (
    MemoryDefinitionRepository,
    MemoryEventStore,
    MemorySubmissionStore,
)
from etlantic_fastapi import ETLanticAPI
from etlantic_fastapi.auth import ContextFactory, PrincipalDependency

from ._secrets import _database_url_value
from .compatibility import validate_core, validate_sqlite
from .errors import CapabilityError, CompatibilityError, ProviderReadinessError
from .settings import ShuETLSettings

SQLITE_HEAD = "004_schedules_0_47"


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
    definitions: Any
    submissions: Any
    events: Any
    provider: str
    development_only: bool
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
            else:
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
                    current_version,
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
                if current_version(engine) != SQLITE_HEAD:
                    raise ProviderReadinessError(
                        "SQLite schema is not at the required head"
                    )
                definitions = SQLModelDefinitionRepository(engine)
                submissions = SQLModelSubmissionStore(engine)
                events = SqlModelEventStore(engine)

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


__all__ = ["LocalProviderBundle", "SQLITE_HEAD"]
