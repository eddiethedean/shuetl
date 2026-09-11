"""Local provider composition for the Phase 0.3 runtime."""

from __future__ import annotations

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

from .compatibility import validate_core, validate_sqlite
from .errors import ProviderReadinessError
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

        if not callable(authorizer) and not hasattr(authorizer, "authorize"):
            raise TypeError("authorizer must implement authorize")
        if not callable(context_factory) or not callable(principal_dependency):
            raise TypeError("context_factory and principal_dependency must be callable")

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
                raw_url = database_url.get_secret_value()
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
        except ProviderReadinessError:
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
    if value.startswith("sqlite:////"):
        return Path("/" + raw_path.lstrip("/"))
    return Path(raw_path.lstrip("/"))


__all__ = ["LocalProviderBundle", "SQLITE_HEAD"]
