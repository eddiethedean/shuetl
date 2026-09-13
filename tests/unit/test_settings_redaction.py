"""Regression coverage for settings validation-error redaction."""

import json

import pytest
from pydantic import SecretStr, ValidationError

from shuetl.settings import ShuETLSettings


@pytest.mark.parametrize("field", ["database_url", "SHUETL_DATABASE_URL"])
def test_byte_database_url_is_redacted_from_missing_field_errors(field: str) -> None:
    secret_url = b"postgresql+psycopg://etl_user:byte-password@db.example/etl"

    with pytest.raises(ValidationError) as captured:
        ShuETLSettings(
            profile="postgresql-pilot",
            provider="postgresql",
            identity="host",
            **{field: secret_url},
        )

    for error in (str(captured.value), captured.value.json()):
        assert "byte-password" not in error
        assert "db.example" not in error


@pytest.mark.parametrize("field", ["database_url", "SHUETL_DATABASE_URL"])
@pytest.mark.parametrize(
    "secret_url",
    [
        b"not-a-url://etl_user:byte-password@db.example/etl",
        b"postgresql+psycopg://etl_user:byte-password\xff@db.example/etl",
    ],
)
def test_invalid_byte_database_url_is_redacted_from_validation_errors(
    field: str, secret_url: bytes
) -> None:

    with pytest.raises(ValidationError) as captured:
        ShuETLSettings(
            profile="postgresql-pilot",
            role="gateway",
            provider="postgresql",
            identity="host",
            **{field: secret_url},
        )

    for error in (str(captured.value), captured.value.json()):
        assert "byte-password" not in error
        assert "db.example" not in error


def test_valid_byte_database_url_preserves_accepted_value() -> None:
    url = "postgresql+psycopg://etl_user:byte-password@db.example/etl"
    settings = ShuETLSettings(
        profile="postgresql-pilot",
        role="gateway",
        provider="postgresql",
        identity="host",
        database_url=url.encode("utf-8"),
    )
    assert settings.database_url is not None
    assert settings.database_url.get_secret_value() == url


@pytest.mark.parametrize("field", ["database_url", "SHUETL_DATABASE_URL"])
@pytest.mark.parametrize("path", ["constructor", "model", "json"])
def test_final_001_structured_url_errors_are_redacted(field: str, path: str) -> None:
    url = "postgresql+psycopg://sentinel-user:sentinel-password@sentinel-host/db"
    data = {
        "profile": "postgresql-pilot",
        "role": "gateway",
        "provider": "postgresql",
        "identity": "host",
        field: {"value": url},
    }
    with pytest.raises(ValidationError) as captured:
        if path == "constructor":
            ShuETLSettings(**data)  # type: ignore[arg-type]
        elif path == "model":
            ShuETLSettings.model_validate(data)
        else:
            ShuETLSettings.model_validate_json(json.dumps(data))

    assert captured.value.errors()[0]["type"] == "string_type"
    for error in (str(captured.value), captured.value.json()):
        assert "sentinel-password" not in error
        assert "sentinel-host" not in error
        assert "sentinel-user" not in error


def test_unsupported_url_inputs_are_not_rendered_or_coerced() -> None:
    class UnrenderableInput:
        def __str__(self) -> str:
            raise AssertionError("URL input must not be coerced to a string")

        def __repr__(self) -> str:
            raise AssertionError("URL input must not be rendered")

    for value in (["sentinel-password"], UnrenderableInput()):
        with pytest.raises(ValidationError) as captured:
            ShuETLSettings(
                profile="local",
                role="gateway",
                provider="memory",
                identity="host",
                database_url=value,  # type: ignore[arg-type]
            )
        assert captured.value.errors()[0]["type"] == "string_type"
        assert "sentinel-password" not in str(captured.value)
        assert "sentinel-password" not in captured.value.json()


def test_secret_url_and_explicit_none_remain_supported() -> None:
    secret = SecretStr("postgresql+psycopg://user:password@host/db")
    configured = ShuETLSettings(
        profile="postgresql-pilot",
        role="gateway",
        provider="postgresql",
        identity="host",
        database_url=secret,
    )
    assert configured.database_url is secret
    local = ShuETLSettings(
        profile="local",
        role="gateway",
        provider="memory",
        identity="host",
        database_url=None,
    )
    assert local.database_url is None
