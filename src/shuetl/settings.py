"""Validated, immutable ShuETL runtime settings."""

from __future__ import annotations

from typing import Any, Literal, cast
from urllib.parse import urlsplit

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

    profile: Literal["local"] = Field(validation_alias="SHUETL_PROFILE")
    role: Literal["gateway"] = Field(validation_alias="SHUETL_ROLE")
    provider: Literal["memory", "sqlite"] = Field(validation_alias="SHUETL_PROVIDER")
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

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        return _validate_prefix(value)

    @model_validator(mode="after")
    def validate_provider_url(self) -> ShuETLSettings:
        if self.provider == "memory" and self.database_url is not None:
            raise ValueError("database_url is only valid for the sqlite provider")
        if self.provider == "sqlite":
            if self.database_url is None:
                raise ValueError("sqlite provider requires database_url")
            raw_url = _database_url_value(self.database_url)
            assert raw_url is not None
            _validate_sqlite_url(raw_url)
        return self

    def __init__(self, **data: Any) -> None:
        """Convert explicitly supplied secrets before Pydantic builds errors."""

        for key in ("database_url", "SHUETL_DATABASE_URL"):
            value = data.get(key)
            if isinstance(value, str):
                data[key] = SecretStr(value)
        super().__init__(**data)

    @property
    def database_driver(self) -> Literal["sqlite"] | None:
        return "sqlite" if self.provider == "sqlite" else None

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
                value = values.get(key)
                if isinstance(value, str):
                    values[key] = SecretStr(value)
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


__all__ = ["ShuETLSettings"]
