"""Transport-neutral callable checks shared by identity and runtime loading."""

from __future__ import annotations

import inspect
from functools import partial

from etlantic.control_plane import Authorizer


def is_async_or_generator_callable(value: object) -> bool:
    candidate = value
    while isinstance(candidate, partial):
        candidate = candidate.func
    functions = (candidate, type(candidate).__call__)
    return any(
        inspect.iscoroutinefunction(function)
        or inspect.isasyncgenfunction(function)
        or inspect.isgeneratorfunction(function)
        for function in functions
        if function is not None
    )


def authorizer_is_valid(value: object) -> bool:
    if not isinstance(value, Authorizer):
        return False
    method = getattr(value, "authorize", None)
    if not callable(method) or is_async_or_generator_callable(method):
        return False
    try:
        inspect.signature(method).bind(object(), "action", "resource")
    except (TypeError, ValueError):
        return False
    return True
