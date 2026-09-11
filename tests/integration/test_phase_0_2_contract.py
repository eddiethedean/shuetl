"""Facade-path contract coverage for Phase 0.2 evidence."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import pytest
from etlantic.control_plane import ControlPlaneContext, ControlPlaneError, Principal
from etlantic_fastapi import control_plane_error_handler
from fastapi import FastAPI
from fastapi.testclient import TestClient
from spikes.phase_0_1_memory_mount import (
    Graph,
    assert_openapi_parity,
    build_direct_app,
    build_graph,
    normalized_openapi,
)

from shuetl import MountConflictError, ShuETL


@dataclass
class AppCase:
    graph: Graph
    integration: ShuETL
    app: FastAPI
    prefix: str


@pytest.fixture(params=["embedded", "dedicated"])
def app_case(request: pytest.FixtureRequest) -> Iterator[AppCase]:
    graph = build_graph()
    integration = ShuETL(api=graph.api)
    if request.param == "embedded":
        app = FastAPI()
        integration.mount(app, prefix="/etl")
        prefix = "/etl"
    else:
        app = integration.create_app()
        prefix = ""
    yield AppCase(graph=graph, integration=integration, app=app, prefix=prefix)


def _path(case: AppCase, suffix: str) -> str:
    return f"{case.prefix}{suffix}"


def test_three_way_openapi_contract_matches_direct_upstream() -> None:
    graph = build_graph()
    integration = ShuETL(api=graph.api)
    embedded = FastAPI()
    integration.mount(embedded, prefix="/etl")
    dedicated = integration.create_app()
    direct = build_direct_app()

    assert normalized_openapi(embedded.openapi(), prefix="/etl") == normalized_openapi(
        direct.openapi()
    )
    assert normalized_openapi(dedicated.openapi()) == normalized_openapi(
        direct.openapi()
    )
    assert_openapi_parity(embedded, direct)


def test_openapi_cache_is_invalidated_after_mount() -> None:
    graph = build_graph()
    app = FastAPI()
    app.openapi()
    assert app.openapi_schema is not None

    ShuETL(api=graph.api).mount(app, prefix="/etl")

    assert app.openapi_schema is None
    assert "/etl/health" in app.openapi()["paths"]


def test_existing_upstream_handler_is_preserved_without_duplicate_registration() -> (
    None
):
    graph = build_graph()
    app = FastAPI()
    app.exception_handlers[ControlPlaneError] = control_plane_error_handler
    before = dict(app.exception_handlers)

    ShuETL(api=graph.api).mount(app, prefix="/etl")

    assert app.exception_handlers == before
    assert app.exception_handlers[ControlPlaneError] is control_plane_error_handler


def test_mount_preserves_host_routes_metadata_lifespan_and_state() -> None:
    graph = build_graph()
    app = FastAPI(title="host")

    @app.get("/host-health", operation_id="host_health")
    def host_health() -> dict[str, str]:
        return {"status": "ok"}

    sentinel = object()
    app.state.host_sentinel = sentinel
    before_routes = list(app.routes)
    before_handlers = dict(app.exception_handlers)
    before_lifespan = app.router.lifespan_context

    ShuETL(api=graph.api).mount(app, prefix="/etl")

    assert app.title == "host"
    assert app.state.host_sentinel is sentinel
    assert app.exception_handlers == before_handlers | {
        ControlPlaneError: control_plane_error_handler
    }
    assert app.router.lifespan_context is before_lifespan
    assert app.routes[: len(before_routes)] == before_routes


@pytest.mark.parametrize("mode", ["embedded", "dedicated"])
def test_dependency_overrides_work_and_can_be_removed(mode: str) -> None:
    graph = build_graph()
    integration = ShuETL(api=graph.api)
    if mode == "embedded":
        app = FastAPI()
        integration.mount(app, prefix="/etl")
        prefix = "/etl"
    else:
        app = integration.create_app()
        prefix = ""

    def override_principal() -> Principal:
        return graph.context.principal

    def override_context() -> ControlPlaneContext:
        return graph.context

    app.dependency_overrides[graph.api.principal_dependency] = override_principal
    app.dependency_overrides[graph.api.context_dependency] = override_context
    with TestClient(app) as client:
        overridden = client.get(f"{prefix}/v1/definitions")
        assert overridden.status_code == 200

        app.dependency_overrides.clear()
        restored = client.get(f"{prefix}/v1/definitions")
        assert restored.status_code == 401


def test_submission_contract_is_preserved_in_both_modes(app_case: AppCase) -> None:
    case = app_case
    case.graph.definitions.put(
        case.graph.context,
        "pipe-1",
        {"name": "demo", "fingerprint": "fp1"},
    )
    headers = {"X-Principal": "alice", "Idempotency-Key": "phase-0-2-idem"}
    body = {"payload": {"mode": "full"}}

    with TestClient(case.app) as client:
        first = client.post(
            _path(case, "/v1/definitions/pipe-1/runs"),
            headers=headers,
            json=body,
        )
        replay = client.post(
            _path(case, "/v1/definitions/pipe-1/runs"),
            headers=headers,
            json=body,
        )
        conflict = client.post(
            _path(case, "/v1/definitions/pipe-1/runs"),
            headers=headers,
            json={"payload": {"mode": "incremental"}},
        )

    assert first.status_code == 202
    assert replay.status_code == 202
    assert replay.json()["acceptance_id"] == first.json()["acceptance_id"]
    assert replay.json()["submission_id"] == first.json()["submission_id"]
    assert conflict.status_code == 409
    assert conflict.headers["content-type"].startswith("application/problem+json")


def test_authorization_precedes_existence_lookup_in_both_modes(
    app_case: AppCase,
) -> None:
    case = app_case
    with TestClient(case.app) as client:
        response = client.get(_path(case, "/v1/definitions/missing"))
    assert response.status_code == 401


def test_sse_contract_is_preserved_in_both_modes(app_case: AppCase) -> None:
    case = app_case
    case.graph.authorizer.grant(case.graph.context, "run.events")
    case.graph.definitions.put(case.graph.context, "pipe-1", {"name": "demo"})
    headers = {"X-Principal": "alice", "Idempotency-Key": "sse-idem"}

    with TestClient(case.app) as client:
        accepted = client.post(
            _path(case, "/v1/definitions/pipe-1/runs"),
            headers=headers,
            json={"payload": {"mode": "full"}},
        )
        events = client.get(
            _path(case, f"/v1/runs/{accepted.json()['submission_id']}/events"),
            headers={"X-Principal": "alice"},
        )

    assert accepted.status_code == 202
    assert events.status_code == 200
    assert events.headers["content-type"].startswith("text/event-stream")
    assert "event: run.accepted" in events.text


def test_lifespan_reentry_and_exception_cleanup_are_atomic() -> None:
    graph = build_graph()
    integration = ShuETL(api=graph.api)
    app = integration.create_app()

    async def exercise() -> None:
        async with integration.lifespan(app):
            assert app.state.shuetl.active is True
            with pytest.raises(MountConflictError):
                async with integration.lifespan(app):
                    pass
        assert app.state.shuetl.active is False

        with pytest.raises(RuntimeError):
            async with integration.lifespan(app):
                raise RuntimeError("body failure")
        assert app.state.shuetl.active is False

    asyncio.run(exercise())


def test_composed_lifespan_skips_shuetl_when_host_entry_fails() -> None:
    graph = build_graph()
    integration = ShuETL(api=graph.api)
    app = integration.create_app()
    events: list[str] = []

    @asynccontextmanager
    async def failing_host(_app: FastAPI):
        events.append("host-enter")
        raise RuntimeError("host failed")
        yield

    async def exercise() -> None:
        with pytest.raises(RuntimeError):
            async with integration.compose_lifespan(failing_host)(app):
                pass

    asyncio.run(exercise())
    assert events == ["host-enter"]
    assert app.state.shuetl.active is False


def test_operation_ids_are_unique_and_no_shuetl_schemas_are_published() -> None:
    app = ShuETL(api=build_graph().api).create_app()
    operations = [
        operation
        for item in app.openapi()["paths"].values()
        for method, operation in item.items()
        if not method.startswith("x-")
    ]
    operation_ids = [operation["operationId"] for operation in operations]
    assert len(operation_ids) == len(set(operation_ids))
    assert not any(
        name.startswith("ShuETL") for name in app.openapi()["components"]["schemas"]
    )
