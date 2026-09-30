"""Generated inventory-bound denial checks for every mounted mutation route."""

from __future__ import annotations

import json
import re
import types
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

from etlantic.control_plane import AuthzDecision, ControlPlaneContext
from etlantic_fastapi import ETLanticAPI
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pydantic import BaseModel
from spikes.phase_0_1_memory_mount import build_graph

from shuetl import ShuETL

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "docs/evidence/0.5/route_inventory.json"
MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_PATH_PARAMETER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


class DenyAllAuthorizer:
    def __init__(self) -> None:
        self.decisions: list[tuple[str, str]] = []

    def authorize(
        self, ctx: ControlPlaneContext, action: str, resource: str
    ) -> AuthzDecision:
        del ctx
        self.decisions.append((action, resource))
        return AuthzDecision(
            allowed=False,
            reason="synthetic security proof denial",
            disclosure="forbidden",
        )


class StoreCallProbe:
    """Record all provider method calls while preserving the wrapped store."""

    def __init__(self, inner: object, name: str, calls: list[str]) -> None:
        self._inner = inner
        self._name = name
        self._calls = calls

    def __getattr__(self, attribute: str) -> Any:
        target = getattr(self._inner, attribute)
        if not callable(target):
            self._calls.append(f"{self._name}.{attribute}")
            return target

        def invoke(*args: Any, **kwargs: Any) -> Any:
            self._calls.append(f"{self._name}.{attribute}")
            return target(*args, **kwargs)

        return invoke


def _sample_value(annotation: Any) -> Any:
    origin = get_origin(annotation)
    arguments = get_args(annotation)
    if origin is Literal:
        return arguments[0]
    if origin is types.UnionType or origin is Union:
        non_none = [value for value in arguments if value is not type(None)]
        return _sample_value(non_none[0]) if non_none else None
    if origin is not None and str(origin).endswith("Annotated"):
        return _sample_value(arguments[0])
    if annotation is Any or annotation is object:
        return {}
    if annotation is str:
        return "phase05-security-probe"
    if annotation is int:
        return 1
    if annotation is float:
        return 1.0
    if annotation is bool:
        return False
    if origin is dict or annotation is dict:
        return {}
    if origin is list or annotation is list:
        return []
    if origin is tuple or annotation is tuple:
        return []
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return next(iter(annotation)).value
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        values: dict[str, Any] = {}
        for name, field in annotation.model_fields.items():
            if field.is_required():
                values[name] = _sample_value(field.annotation)
            elif field.default_factory is not None:
                values[name] = field.get_default(call_default_factory=True)
            elif field.default is not None:
                values[name] = field.default
        return annotation(**values).model_dump(mode="json")
    if isinstance(annotation, type) and issubclass(annotation, str):
        return "phase05-security-probe"
    return "phase05-security-probe"


def _route_path(path: str) -> tuple[str, dict[str, str]]:
    names: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        marker = f"route-{name}"
        names[name] = marker
        return marker

    return _PATH_PARAMETER.sub(replace, path), names


def _normalized_resource(resource: str, names: dict[str, str]) -> str:
    for name, marker in names.items():
        resource = resource.replace(marker, "{" + name + "}")
    return resource


def _request_body(route: APIRoute) -> tuple[bool, Any]:
    hints = get_type_hints(route.endpoint)
    if "body" not in hints:
        return False, None
    annotation = hints["body"]
    if get_origin(annotation) in (types.UnionType, Union) and type(None) in get_args(
        annotation
    ):
        return True, _sample_value(annotation)
    return True, _sample_value(annotation)


def _mutation_routes(api: ETLanticAPI) -> list[APIRoute]:
    router = api.router
    return sorted(
        (
            route
            for route in router.routes
            if isinstance(route, APIRoute)
            and route.methods is not None
            and route.methods & MUTATION_METHODS
        ),
        key=lambda route: (route.path, route.operation_id or ""),
    )


def collect_inventory() -> list[dict[str, Any]]:
    graph = build_graph()
    authorizer = DenyAllAuthorizer()
    graph.api.authorizer = authorizer
    store_calls: list[str] = []
    for name in (
        "definitions",
        "submissions",
        "events",
        "history_store",
        "registry",
        "durable_work",
        "schedule_store",
        "policy",
        "approvals",
        "quotas",
        "erasure",
        "audit",
        "attestations",
        "objectives",
    ):
        provider = getattr(graph.api, name, None)
        if provider is not None:
            setattr(graph.api, name, StoreCallProbe(provider, name, store_calls))

    app = FastAPI()
    ShuETL(api=graph.api).mount(app, prefix="/guarded")
    observed: list[dict[str, Any]] = []
    with TestClient(app) as client:
        for route in _mutation_routes(graph.api):
            if route.methods is None:
                raise AssertionError(f"mutation route has no methods: {route.path}")
            path, names = _route_path(route.path)
            method = sorted(route.methods & MUTATION_METHODS)[0]
            include_body, body = _request_body(route)
            authorizer.decisions.clear()
            store_calls.clear()
            request: dict[str, Any] = {
                "headers": {"X-Principal": "alice"},
            }
            if include_body:
                request["json"] = body
            response = client.request(method, f"/guarded{path}", **request)

            assert response.status_code == 403, (
                route.operation_id,
                response.status_code,
                response.text,
            )
            assert authorizer.decisions, route.operation_id
            assert store_calls == [], (route.operation_id, store_calls)
            observed.append(
                {
                    "method": method,
                    "path": route.path,
                    "operation_id": route.operation_id,
                    "authorizations": [
                        {
                            "action": action,
                            "resource": _normalized_resource(resource, names),
                        }
                        for action, resource in authorizer.decisions
                    ],
                    "denial_status": response.status_code,
                    "provider_calls": [],
                }
            )

    return observed


def test_every_mounted_mutation_denies_before_provider_lookup() -> None:
    observed = collect_inventory()
    expected = json.loads(INVENTORY.read_text(encoding="utf-8"))
    assert observed == expected
    assert len(observed) >= 40
