"""Validated, immutable ShuETL runtime settings."""

from __future__ import annotations

from typing import Any, Literal, cast
from urllib.parse import unquote, urlsplit

from pydantic import (
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from ._secrets import _database_url_value
from .integration import _validate_prefix


def _redact_database_url_input(value: Any) -> Any:
    """Protect URL credentials before Pydantic constructs validation errors.

    Pydantic accepts byte strings for ``SecretStr`` fields, but validation
    errors serialize the original input value.  Normalize byte-like values
    before model validation so credentials cannot be echoed in an error
    payload. Invalid UTF-8 becomes an empty secret URL, which provider URL
    validation rejects without retaining the original bytes in error context.
    """

    if isinstance(value, SecretStr):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            return SecretStr(bytes(value).decode("utf-8"))
        except UnicodeDecodeError:
            return SecretStr("")
    if isinstance(value, str):
        return SecretStr(value)
    return value


class ShuETLSettings(BaseSettings):
    """Configuration for the local ShuETL composition boundary."""

    model_config = SettingsConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        case_sensitive=True,
        env_prefix="SHUETL_",
        env_file=None,
        secrets_dir=None,
    )

    profile: Literal["local", "postgresql-pilot"] = Field(
        validation_alias="SHUETL_PROFILE"
    )
    role: Literal["gateway"] = Field(validation_alias="SHUETL_ROLE")
    provider: Literal["memory", "sqlite", "postgresql"] = Field(
        validation_alias="SHUETL_PROVIDER"
    )
    identity: Literal["host"] = Field(validation_alias="SHUETL_IDENTITY")
    api_prefix: str = Field("/etl", validation_alias="SHUETL_API_PREFIX")
    route_preset: Literal["complete"] = Field(
        "complete", validation_alias="SHUETL_ROUTE_PRESET"
    )
    database_url: SecretStr | None = Field(
        None, validation_alias="SHUETL_DATABASE_URL", exclude=True
    )
    provider_connect_timeout_seconds: float = Field(
        2.0,
        ge=0.1,
        le=30.0,
        validation_alias="SHUETL_PROVIDER_CONNECT_TIMEOUT_SECONDS",
    )
    postgresql_sslmode: Literal["verify-full", "verify-ca", "require", "disable"] = (
        Field("verify-full", validation_alias="SHUETL_POSTGRESQL_SSLMODE")
    )

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        return _validate_prefix(value)

    @model_validator(mode="after")
    def validate_provider_url(self) -> ShuETLSettings:
        if self.provider == "memory" and self.database_url is not None:
            raise ValueError("database_url is only valid for sqlite or postgresql")
        if self.provider == "sqlite":
            if self.database_url is None:
                raise ValueError("sqlite provider requires database_url")
            raw_url = _database_url_value(self.database_url)
            assert raw_url is not None
            _validate_sqlite_url(raw_url)
            if self.profile != "local":
                raise ValueError("sqlite provider requires the local profile")
            if self.postgresql_sslmode != "verify-full":
                raise ValueError("postgresql_sslmode is only valid for postgresql")
        elif self.provider == "postgresql":
            if self.profile != "postgresql-pilot":
                raise ValueError(
                    "postgresql provider requires the postgresql-pilot profile"
                )
            if self.database_url is None:
                raise ValueError("postgresql provider requires database_url")
            raw_url = _database_url_value(self.database_url)
            assert raw_url is not None
            _validate_postgresql_url(raw_url)
        else:
            if self.profile != "local":
                raise ValueError("memory provider requires the local profile")
            if self.postgresql_sslmode != "verify-full":
                raise ValueError("postgresql_sslmode is only valid for postgresql")
        return self

    def __init__(self, **data: Any) -> None:
        """Convert explicitly supplied secrets before Pydantic builds errors."""

        for key in ("database_url", "SHUETL_DATABASE_URL"):
            if key in data:
                data[key] = _redact_database_url_input(data[key])
        super().__init__(**data)

    @property
    def database_driver(self) -> Literal["sqlite", "psycopg"] | None:
        if self.provider == "sqlite":
            return "sqlite"
        if self.provider == "postgresql":
            return "psycopg"
        return None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        del settings_cls, dotenv_settings, file_secret_settings

        def redacted_env_settings() -> dict[str, Any]:
            values = env_settings()
            for key in ("database_url", "SHUETL_DATABASE_URL"):
                if key in values:
                    values[key] = _redact_database_url_input(values[key])
            return values

        return init_settings, cast(PydanticBaseSettingsSource, redacted_env_settings)


def _validate_sqlite_url(value: str) -> None:
    """Reject network, credentialed, URI, and in-memory SQLite URLs."""

    if not isinstance(value, str) or not value.startswith("sqlite"):
        raise ValueError("database_url must be a local sqlite URL")
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"sqlite", "sqlite+pysqlite"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("database_url must not contain query or fragment components")
    if parsed.username or parsed.password or parsed.hostname:
        raise ValueError("database_url must not contain credentials or a host")
    if value in {"sqlite://", "sqlite:///:memory:"}:
        raise ValueError("in-memory sqlite databases are not supported")
    if not parsed.path or parsed.path in {"/", ":memory:"}:
        raise ValueError("database_url must identify a local database file")
    if ":memory:" in parsed.path.lower():
        raise ValueError("in-memory sqlite databases are not supported")


def _validate_postgresql_url(value: str) -> None:
    """Reject ambiguous PostgreSQL URLs while keeping credentials secret."""

    if not isinstance(value, str):
        raise ValueError("database_url must be a PostgreSQL URL")
    parsed = urlsplit(value)
    if parsed.scheme != "postgresql+psycopg":
        raise ValueError("database_url must use the postgresql+psycopg scheme")
    if parsed.query or parsed.fragment:
        raise ValueError("database_url must not contain query or fragment components")
    if not parsed.username or not parsed.hostname:
        raise ValueError("database_url must include a PostgreSQL username and host")
    database = unquote(parsed.path.lstrip("/"))
    if not database or "/" in database:
        raise ValueError("database_url must identify one PostgreSQL database")


__all__ = ["ShuETLSettings"]
