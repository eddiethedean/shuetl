"""FastAPI composition facade for the ETLantic control-plane adapter."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass
from re import fullmatch
from typing import Any, Final

from etlantic.control_plane import ControlPlaneError
from etlantic_fastapi import (
    ETLanticAPI,
    control_plane_error_handler,
    include_router,
    install_exception_handlers,
)
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.routing import Mount, Route, WebSocketRoute

from .errors import InvalidPrefixError, MountConflictError

_PREFIX_SEGMENT: Final = r"[A-Za-z0-9._~-]+"
_PREFIX_PATTERN: Final = rf"/(?:{_PREFIX_SEGMENT})(?:/(?:{_PREFIX_SEGMENT}))*"


@dataclass(slots=True)
class _MountRecord:
    """Opaque state kept on an application mounted by one integration."""

    integration_id: int
    api_id: int
    prefix: str
    active: bool = False


def _state_contains(app: FastAPI, key: str) -> bool:
    return key in app.state._state


def _validate_prefix(prefix: str) -> str:
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


def _route_operation_id(route: Any) -> str | None:
    value = getattr(route, "operation_id", None)
    if value is None:
        value = getattr(route, "unique_id", None)
    if not isinstance(value, str) or not value:
        return None
    return value


def _route_path(route: Any) -> str | None:
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else None


def _route_methods(route: Any) -> set[str]:
    methods = getattr(route, "methods", None)
    if methods is None:
        return set()
    return {str(method).upper() for method in methods}


def _path_segments(path: str) -> tuple[str, ...]:
    return tuple(segment for segment in path.split("/") if segment)


def _path_templates_overlap(left: str, right: str) -> bool:
    """Return whether two FastAPI path templates can address the same path."""

    left_segments = _path_segments(left)
    right_segments = _path_segments(right)
    left_catch_all = bool(left_segments and left_segments[-1] == "{path:path}")
    right_catch_all = bool(right_segments and right_segments[-1] == "{path:path}")
    if (
        not left_catch_all
        and not right_catch_all
        and len(left_segments) != len(right_segments)
    ):
        return False
    comparable = min(len(left_segments), len(right_segments))
    for left_segment, right_segment in zip(
        left_segments[:comparable], right_segments[:comparable], strict=True
    ):
        if left_segment == "{path:path}" or right_segment == "{path:path}":
            return True
        if left_segment.startswith("{") or right_segment.startswith("{"):
            continue
        if left_segment != right_segment:
            return False
    return (
        left_catch_all or right_catch_all or len(left_segments) == len(right_segments)
    )


def _full_path(prefix: str, route_path: str) -> str:
    if not prefix:
        return route_path or "/"
    if not route_path or route_path == "/":
        return prefix
    return f"{prefix}{route_path if route_path.startswith('/') else '/' + route_path}"


@dataclass(frozen=True, slots=True)
class _HostRoute:
    route: Any
    path: str


def _join_route_path(prefix: str, path: str) -> str:
    if not path or path == "/":
        return prefix or "/"
    normalized_path = path if path.startswith("/") else f"/{path}"
    if not prefix:
        return normalized_path
    return f"{prefix.rstrip('/')}{normalized_path}"


def _included_router_parts(route: Any) -> tuple[list[Any], str] | None:
    """Read FastAPI's included-router container without importing private APIs."""

    original_router = getattr(route, "original_router", None)
    include_context = getattr(route, "include_context", None)
    routes = getattr(original_router, "routes", None)
    include_prefix = getattr(include_context, "prefix", None)
    if not isinstance(routes, list) or not isinstance(include_prefix, str):
        return None
    return routes, include_prefix


def _host_routes(app: FastAPI) -> list[_HostRoute]:
    routes: list[_HostRoute] = []

    def visit(route_list: list[Any], prefix: str = "") -> None:
        for route in route_list:
            included = _included_router_parts(route)
            if included is not None:
                included_routes, included_prefix = included
                visit(included_routes, _join_route_path(prefix, included_prefix))
                continue

            route_path = _route_path(route)
            if route_path is None:
                continue
            effective_path = _join_route_path(prefix, route_path)
            routes.append(_HostRoute(route=route, path=effective_path))
            child_routes = getattr(route, "routes", None)
            if isinstance(child_routes, list):
                visit(child_routes, effective_path)

    visit(list(app.routes))
    return routes


def _is_prefix_subtree(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(f"{prefix}/")


def _conflict(message: str) -> MountConflictError:
    return MountConflictError(message)


class ShuETL:
    """Compose a caller-owned ETLantic API into FastAPI applications."""

    __slots__ = ("_api",)

    def __init__(self, *, api: ETLanticAPI) -> None:
        if not isinstance(api, ETLanticAPI):
            raise TypeError("api must be an etlantic_fastapi.ETLanticAPI instance")
        self._api = api

    @property
    def api(self) -> ETLanticAPI:
        """Return the exact caller-provided API object."""

        return self._api

    def _preflight(self, app: FastAPI, prefix: str) -> None:
        if not isinstance(app, FastAPI):
            raise TypeError("app must be a FastAPI instance")
        if _state_contains(app, "shuetl"):
            raise _conflict("mount conflict: app.state.shuetl is already present")
        if _state_contains(app, "etlantic_api"):
            raise _conflict("mount conflict: app.state.etlantic_api is already present")

        existing_handler = app.exception_handlers.get(ControlPlaneError)
        if (
            existing_handler is not None
            and existing_handler is not control_plane_error_handler
        ):
            raise _conflict(
                "mount conflict: a non-upstream ControlPlaneError handler is registered"
            )

        upstream_routes = list(self.api.router.routes)
        operation_ids: set[str] = set()
        for route in upstream_routes:
            operation_id = _route_operation_id(route)
            if operation_id is None:
                raise _conflict("mount conflict: upstream route has no operation ID")
            if operation_id in operation_ids:
                raise _conflict(
                    f"mount conflict: duplicate upstream operation ID {operation_id!r}"
                )
            operation_ids.add(operation_id)

        host_routes = _host_routes(app)
        host_operation_ids = {
            operation_id
            for host_route in host_routes
            if isinstance(host_route.route, APIRoute)
            for route in [host_route.route]
            for operation_id in [_route_operation_id(route)]
            if operation_id is not None
        }
        overlap = sorted(operation_ids & host_operation_ids)
        if overlap:
            raise _conflict(
                "mount conflict: operation ID already used by host route "
                f"{overlap[0]!r}"
            )

        for upstream_route in upstream_routes:
            route_path = _route_path(upstream_route)
            if route_path is None:
                raise _conflict("mount conflict: upstream route has no path")
            target_path = _full_path(prefix, route_path)
            target_methods = _route_methods(upstream_route)
            for host_route in host_routes:
                host_path = host_route.path
                route = host_route.route
                if prefix and (
                    _is_prefix_subtree(host_path, prefix)
                    or (
                        isinstance(route, Mount)
                        and _is_prefix_subtree(prefix, host_path)
                    )
                    or _path_templates_overlap(host_path, target_path)
                ):
                    raise _conflict(
                        f"mount conflict: host route occupies prefix {prefix!r}"
                    )
                if not prefix and isinstance(route, (WebSocketRoute, Mount)):
                    continue
                if not prefix and isinstance(route, (APIRoute, Route)):
                    host_methods = _route_methods(route)
                    if target_methods & host_methods and _path_templates_overlap(
                        target_path, host_path
                    ):
                        raise _conflict(
                            f"mount conflict: host route overlaps {target_path!r}"
                        )

    def mount(self, app: FastAPI, *, prefix: str = "/etl") -> None:
        """Mount the complete upstream router into an existing FastAPI app."""

        validated_prefix = _validate_prefix(prefix)
        self._preflight(app, validated_prefix)
        if ControlPlaneError not in app.exception_handlers:
            install_exception_handlers(app)
        host_lifespan = app.router.lifespan_context
        try:
            include_router(app, self.api, prefix=validated_prefix)
        finally:
            # The upstream helper merges router lifespans as a side effect.
            # ShuETL must leave lifespan selection to the host/factory caller.
            app.router.lifespan_context = host_lifespan
        app.state.shuetl = _MountRecord(
            integration_id=id(self), api_id=id(self.api), prefix=validated_prefix
        )
        app.openapi_schema = None

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncIterator[None]:
        """Track ShuETL activity without taking ownership of providers."""

        if not isinstance(app, FastAPI):
            raise TypeError("app must be a FastAPI instance")
        if not _state_contains(app, "shuetl") or not _state_contains(
            app, "etlantic_api"
        ):
            raise _conflict("lifespan requires an app mounted by this integration")
        record = app.state.shuetl
        if not isinstance(record, _MountRecord) or record.integration_id != id(self):
            raise _conflict("lifespan mount belongs to a different ShuETL integration")
        if app.state.etlantic_api is not self.api or record.api_id != id(self.api):
            raise _conflict("lifespan API does not belong to this ShuETL integration")
        if record.active:
            raise _conflict("lifespan cannot be entered concurrently for one app")
        record.active = True
        try:
            yield
        finally:
            record.active = False

    def compose_lifespan(
        self,
        host_lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]],
    ) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
        """Compose a host lifespan around ShuETL's lifecycle bookkeeping."""

        if not callable(host_lifespan):
            raise TypeError("host_lifespan must be callable")

        @asynccontextmanager
        async def composed(app: FastAPI) -> AsyncIterator[None]:
            async with host_lifespan(app), self.lifespan(app):
                yield

        return composed

    def create_app(self, *, prefix: str = "") -> FastAPI:
        """Create a dedicated FastAPI app for the caller-owned API graph."""

        app = FastAPI(
            title=self.api.title,
            version=self.api.version,
            lifespan=self.lifespan,
        )
        self.mount(app, prefix=prefix)
        return app


__all__ = ["ShuETL"]
