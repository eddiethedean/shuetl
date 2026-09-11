"""Disposable Phase 0.1 proof against the published ETLantic 0.51.0 train.

This module is repository evidence, not a ShuETL runtime API. It deliberately
uses the upstream ETLantic FastAPI adapter directly so the boundary remains
visible and testable.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

import etlantic
import etlantic_fastapi
from etlantic.control_plane import (
    ControlPlaneContext,
    EnvironmentRef,
    MemoryAuthorizer,
    MemoryDefinitionRepository,
    MemoryEventStore,
    MemorySubmissionStore,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic_fastapi import (
    ETLanticAPI,
    create_app,
    include_router,
    install_exception_handlers,
    membership_context_factory,
    principal_from_header,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient

import shuetl

REQUIRED_OPERATION_IDS = {
    "cp_health",
    "cp_ready",
    "cp_list_definitions",
    "cp_get_definition",
    "cp_validate_definition",
    "cp_plan_definition",
    "cp_submit_run",
    "cp_get_run",
    "cp_cancel_run",
    "cp_stream_run_events",
    "cp_get_run_report",
    "cp_list_run_artifacts",
    "cp_get_run_lineage",
    "cp_list_schema_observations",
    "cp_ack_schema_observation",
    "cp_list_reliability",
}


@dataclass
class Graph:
    """The public memory graph required by :class:`ETLanticAPI`."""

    api: ETLanticAPI
    context: ControlPlaneContext
    authorizer: MemoryAuthorizer
    definitions: MemoryDefinitionRepository
    submissions: MemorySubmissionStore


def make_context() -> ControlPlaneContext:
    return ControlPlaneContext(
        principal=Principal(subject="alice"),
        tenant=TenantRef(tenant_id="tenant-a"),
        workspace=WorkspaceRef(tenant_id="tenant-a", workspace_id="ws-1"),
        environment=EnvironmentRef(name="development"),
        security_domain=SecurityDomain(domain_id="default"),
    )


def build_graph() -> Graph:
    """Construct only the public ETLantic memory-provider graph."""

    authorizer = MemoryAuthorizer()
    definitions = MemoryDefinitionRepository()
    submissions = MemorySubmissionStore()
    context = make_context()
    for action in ("definition.list", "definition.read", "run.submit"):
        authorizer.grant(context, action)
    api = ETLanticAPI(
        authorizer=authorizer,
        definitions=definitions,
        submissions=submissions,
        events=MemoryEventStore(),
        context_factory=membership_context_factory(
            {"alice": ("tenant-a", "ws-1", "development", "default")}
        ),
        principal_dependency=principal_from_header,
    )
    return Graph(
        api=api,
        context=context,
        authorizer=authorizer,
        definitions=definitions,
        submissions=submissions,
    )


def build_embedded_app(graph: Graph) -> FastAPI:
    """Mount upstream routes into an otherwise ordinary host application."""

    app = FastAPI(title="Phase 0.1 host")

    @app.get("/host-health", operation_id="host_health")
    def host_health() -> dict[str, str]:
        return {"status": "host-ok"}

    # include_router intentionally does not install this handler itself.
    install_exception_handlers(app)
    include_router(app, graph.api, prefix="/etl")
    return app


def build_direct_app() -> FastAPI:
    """Build the equivalent upstream dedicated app for contract comparison."""

    return create_app(build_graph().api)


def _prefixed_paths(schema: dict[str, Any], prefix: str) -> dict[str, Any]:
    paths = schema.get("paths", {})
    selected: dict[str, Any] = {}
    for path, item in paths.items():
        if prefix:
            if path != prefix and not path.startswith(f"{prefix}/"):
                continue
            normalized_path = path[len(prefix) :] or "/"
        else:
            normalized_path = path
        selected[normalized_path] = item
    return selected


def normalized_openapi(schema: dict[str, Any], *, prefix: str = "") -> dict[str, Any]:
    """Keep stable upstream contract evidence and normalize a mount prefix."""

    selected_paths = _prefixed_paths(schema, prefix)
    selected_operations: list[dict[str, Any]] = []
    for item in selected_paths.values():
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if not method.startswith("x-") and isinstance(operation, dict):
                selected_operations.append(operation)
    operation_ids = sorted(
        str(operation["operationId"])
        for operation in selected_operations
        if "operationId" in operation
    )
    return {
        "openapi": schema.get("openapi"),
        "paths": json.loads(json.dumps(selected_paths, sort_keys=True)),
        "operationIds": operation_ids,
        "components": json.loads(
            json.dumps(schema.get("components", {}), sort_keys=True)
        ),
    }


def assert_openapi_parity(embedded: FastAPI, direct: FastAPI) -> dict[str, Any]:
    embedded_schema = embedded.openapi()
    direct_schema = direct.openapi()
    embedded_contract = normalized_openapi(embedded_schema, prefix="/etl")
    direct_contract = normalized_openapi(direct_schema)
    if embedded_contract != direct_contract:
        raise AssertionError("embedded OpenAPI differs from direct upstream OpenAPI")
    operation_ids = embedded_contract["operationIds"]
    if len(operation_ids) != len(set(operation_ids)):
        raise AssertionError("embedded OpenAPI contains duplicate operation IDs")
    missing = REQUIRED_OPERATION_IDS - set(operation_ids)
    if missing:
        raise AssertionError(
            f"required upstream operation IDs missing: {sorted(missing)}"
        )
    component_names = set(embedded_contract["components"].get("schemas", {}))
    shadowed = sorted(name for name in component_names if name.startswith("ShuETL"))
    if shadowed:
        raise AssertionError(f"ShuETL shadow schemas found: {shadowed}")
    return embedded_contract


def _assert_clean_origin(module: Any, name: str) -> None:
    origin_raw = getattr(module, "__file__", None)
    if not origin_raw:
        raise AssertionError(f"{name} has no import origin")
    origin = Path(origin_raw).resolve()
    print(f"{name.upper()}_ORIGIN={origin}")
    if os.environ.get("SHUETL_EXPECT_INSTALLED") == "1":
        prefix = Path(sys.prefix).resolve()
        if prefix not in origin.parents:
            raise AssertionError(f"{name} did not load from the isolated environment")


def run() -> None:
    """Run the complete Phase 0.1 behavior proof."""

    _assert_clean_origin(shuetl, "shuetl")
    _assert_clean_origin(etlantic, "etlantic")
    _assert_clean_origin(etlantic_fastapi, "etlantic_fastapi")
    for distribution in (
        "shuetl",
        "etlantic",
        "etlantic-fastapi",
        "fastapi",
        "pydantic",
        "httpx",
    ):
        version = metadata.version(distribution)
        print(f"{distribution}={version}")
    assert metadata.version("etlantic") == "0.51.0"
    assert metadata.version("etlantic-fastapi") == "0.51.0"

    graph = build_graph()
    app = build_embedded_app(graph)
    client = TestClient(app)
    alice = {"X-Principal": "alice"}

    host = client.get("/host-health")
    assert host.status_code == 200
    assert host.json() == {"status": "host-ok"}

    empty = client.get("/etl/v1/definitions", headers=alice)
    assert empty.status_code == 200
    assert empty.json() == {"items": []}

    graph.definitions.put(
        graph.context,
        "pipe-1",
        {"name": "demo", "fingerprint": "fp1"},
    )
    listed = client.get("/etl/v1/definitions", headers=alice)
    assert listed.status_code == 200
    assert listed.json()["items"] == [{"definition_id": "pipe-1"}]
    fetched = client.get("/etl/v1/definitions/pipe-1", headers=alice)
    assert fetched.status_code == 200
    assert fetched.json() == {
        "definition_id": "pipe-1",
        "document": {"name": "demo", "fingerprint": "fp1"},
    }

    headers = {**alice, "Idempotency-Key": "phase-0-1-idem"}
    body = {"payload": {"mode": "full"}}
    first = client.post("/etl/v1/definitions/pipe-1/runs", headers=headers, json=body)
    assert first.status_code == 202
    first_payload = first.json()
    assert first_payload["status"] == "accepted"
    assert first_payload["acceptance_id"]
    assert first_payload["submission_id"]

    replay = client.post("/etl/v1/definitions/pipe-1/runs", headers=headers, json=body)
    assert replay.status_code == 202
    assert replay.json()["acceptance_id"] == first_payload["acceptance_id"]
    assert replay.json()["submission_id"] == first_payload["submission_id"]

    changed = client.post(
        "/etl/v1/definitions/pipe-1/runs",
        headers=headers,
        json={"payload": {"mode": "incremental"}},
    )
    assert changed.status_code == 409
    assert changed.headers["content-type"].startswith("application/problem+json")
    assert changed.json()["code"] == "PMCP409"
    assert len(graph.submissions.poll_accepted(graph.context, limit=10)) == 1

    missing_principal = client.get("/etl/v1/definitions/pipe-1")
    assert missing_principal.status_code == 401
    assert missing_principal.headers["content-type"].startswith(
        "application/problem+json"
    )
    assert missing_principal.json()["code"] == "PMCP401"

    unmapped = client.get(
        "/etl/v1/definitions/pipe-1",
        headers={"X-Principal": "bob"},
    )
    assert unmapped.status_code == 401
    assert unmapped.json()["code"] == "PMCP401"

    missing_idempotency = client.post(
        "/etl/v1/definitions/pipe-1/runs",
        headers=alice,
        json={},
    )
    assert missing_idempotency.status_code == 400
    assert missing_idempotency.json()["code"] == "PMCP400"

    unknown = client.get("/etl/v1/definitions/missing", headers=alice)
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "PMCP404"

    contract = assert_openapi_parity(app, build_direct_app())
    print(f"OPENAPI_OPERATION_COUNT={len(contract['operationIds'])}")
    print("MEMORY_PROFILE=process-local; no restart durability")
    print("PHASE_0_1_SPIKE=PASS")


if __name__ == "__main__":
    run()
