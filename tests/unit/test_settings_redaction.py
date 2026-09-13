"""Regression coverage for settings validation-error redaction."""

import pytest
from pydantic import ValidationError

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
