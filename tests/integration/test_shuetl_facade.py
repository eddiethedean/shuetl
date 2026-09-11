"""Behavioral checks for embedded and dedicated ShuETL applications."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from spikes.phase_0_1_memory_mount import build_graph

from shuetl import ShuETL


def test_embedded_routes_and_openapi_use_the_requested_prefix() -> None:
    graph = build_graph()
    integration = ShuETL(api=graph.api)
    app = FastAPI(title="host")
    integration.mount(app, prefix="/internal/etl")
    with TestClient(app) as client:
        response = client.get("/internal/etl/health")
    assert response.status_code == 200
    schema = app.openapi()
    assert "/internal/etl/health" in schema["paths"]
    assert "/etl/health" not in schema["paths"]


def test_dedicated_route_contract_matches_direct_upstream() -> None:
    graph = build_graph()
    integration = ShuETL(api=graph.api)
    app = integration.create_app()
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 200
    operation_ids = {
        operation["operationId"]
        for item in app.openapi()["paths"].values()
        for method, operation in item.items()
        if not method.startswith("x-")
    }
    assert "cp_health" in operation_ids
    assert "cp_submit_run" in operation_ids
