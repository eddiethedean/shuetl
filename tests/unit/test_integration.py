"""Unit tests for the ShuETL composition contract."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, cast

import pytest
from etlantic.control_plane import ControlPlaneError
from etlantic_fastapi import control_plane_error_handler
from fastapi import FastAPI
from fastapi.responses import Response
from spikes.phase_0_1_memory_mount import build_graph

from shuetl import InvalidPrefixError, MountConflictError, ShuETL


@pytest.fixture
def integration() -> ShuETL:
    return ShuETL(api=build_graph().api)


@pytest.mark.parametrize(
    "prefix",
    [
        "/",
        "etl",
        "/etl/",
        "/etl//v1",
        "/etl/{id}",
        "/etl?a",
        "/etl#a",
        "/é",
        "/.",
        "/etl/../v1",
    ],
)
def test_invalid_prefix_is_rejected_without_mutation(
    integration: ShuETL, prefix: str
) -> None:
    app = FastAPI()
    before_routes = list(app.routes)
    before_handlers = dict(app.exception_handlers)
    with pytest.raises(InvalidPrefixError):
        integration.mount(app, prefix=prefix)
    assert app.routes == before_routes
    assert app.exception_handlers == before_handlers
    assert app.state._state == {}


def test_mount_preserves_api_and_installs_upstream_handler(integration: ShuETL) -> None:
    app = FastAPI()
    assert integration.mount(app) is None
    assert app.state.etlantic_api is integration.api
    assert app.state.shuetl.prefix == "/etl"
    assert app.exception_handlers[ControlPlaneError] is control_plane_error_handler


def test_reserved_state_and_custom_handler_conflicts_are_atomic(
    integration: ShuETL,
) -> None:
    app = FastAPI()
    sentinel = object()
    app.state.shuetl = sentinel
    before_routes = list(app.routes)
    with pytest.raises(MountConflictError):
        integration.mount(app)
    assert app.state.shuetl is sentinel
    assert app.routes == before_routes

    app = FastAPI()

    def custom(*_args: object) -> Response:
        return Response(status_code=500)

    app.add_exception_handler(ControlPlaneError, custom)
    before_handlers = dict(app.exception_handlers)
    with pytest.raises(MountConflictError):
        integration.mount(app)
    assert app.exception_handlers == before_handlers
    assert app.state._state == {}


def test_repeated_mount_and_prefix_subtree_collision(integration: ShuETL) -> None:
    app = FastAPI()
    integration.mount(app)
    route_count = len(app.routes)
    with pytest.raises(MountConflictError):
        integration.mount(app)
    assert len(app.routes) == route_count

    occupied = FastAPI()

    @occupied.get("/etl/custom")
    def custom() -> dict[str, str]:
        return {"ok": "yes"}

    with pytest.raises(MountConflictError):
        integration.mount(occupied)


def test_upstream_operation_ids_must_be_present_and_unique(integration: ShuETL) -> None:
    first = cast(Any, integration.api.router.routes[0])
    second = cast(Any, integration.api.router.routes[1])
    first_state = (first.operation_id, first.unique_id)
    second_state = (second.operation_id, second.unique_id)
    try:
        first.operation_id = None
        first.unique_id = None
        with pytest.raises(MountConflictError):
            integration.mount(FastAPI())

        first.operation_id = "duplicate-operation"
        first.unique_id = "duplicate-operation"
        second.operation_id = "duplicate-operation"
        second.unique_id = "duplicate-operation"
        with pytest.raises(MountConflictError):
            integration.mount(FastAPI())
    finally:
        first.operation_id, first.unique_id = first_state
        second.operation_id, second.unique_id = second_state


def test_segment_adjacent_prefix_does_not_conflict(integration: ShuETL) -> None:
    app = FastAPI()

    @app.get("/etlantic")
    def adjacent() -> dict[str, str]:
        return {"ok": "yes"}

    integration.mount(app)
    assert any(getattr(route, "path", None) == "/etlantic" for route in app.routes)


def test_dedicated_apps_are_new_and_have_lifespan(integration: ShuETL) -> None:
    first = integration.create_app()
    second = integration.create_app()
    assert first is not second
    assert first.title == integration.api.title
    assert first.version == integration.api.version
    assert first.router.lifespan_context is not second.router.lifespan_context


def test_composed_lifespan_is_host_first_and_reverse_on_exit(
    integration: ShuETL,
) -> None:
    events: list[str] = []

    @asynccontextmanager
    async def host(_app: FastAPI):
        events.append("host-enter")
        try:
            yield
        finally:
            events.append("host-exit")

    app = FastAPI(lifespan=integration.compose_lifespan(host))
    integration.mount(app)

    async def run() -> None:
        async with integration.compose_lifespan(host)(app):
            events.append("body")

    asyncio.run(run())
    assert events == ["host-enter", "body", "host-exit"]
    assert app.state.shuetl.active is False
