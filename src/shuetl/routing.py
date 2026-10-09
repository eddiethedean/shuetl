"""Small routing validation shared without importing the ASGI adapter."""

from __future__ import annotations

from re import fullmatch
from typing import Final

from .errors import InvalidPrefixError

_PREFIX_SEGMENT: Final = r"[A-Za-z0-9._~-]+"
_PREFIX_PATTERN: Final = rf"/(?:{_PREFIX_SEGMENT})(?:/(?:{_PREFIX_SEGMENT}))*"


def validate_prefix(prefix: str) -> str:
    if not isinstance(prefix, str):
        raise InvalidPrefixError(
            f"invalid mount prefix: expected str, got {type(prefix).__name__}"
        )
    if prefix == "":
        return prefix
    if not fullmatch(_PREFIX_PATTERN, prefix):
        raise InvalidPrefixError(
            f"invalid mount prefix {prefix!r}: use '' or slash-prefixed "
            "ASCII URL-unreserved path segments without a trailing slash"
        )
    if any(segment in {".", ".."} for segment in prefix.split("/")[1:]):
        raise InvalidPrefixError(
            f"invalid mount prefix {prefix!r}: dot path segments are not allowed"
        )
    return prefix
