"""Executable verification for open Phase 0.2 production-review blockers."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import cast

import pytest
from fastapi import APIRouter, FastAPI
from scripts import check_evidence
from spikes.phase_0_1_memory_mount import build_graph

from shuetl import InvalidPrefixError, MountConflictError, ShuETL

ROOT = Path(__file__).resolve().parents[2]


def _integration() -> ShuETL:
    return ShuETL(api=build_graph().api)


def test_root_mount_rejects_existing_path_method_before_mutation() -> None:
    app = FastAPI()

    @app.get("/health", operation_id="host_health")
    def host_health() -> dict[str, str]:
        return {"status": "host"}

    routes = list(app.routes)
    handlers = dict(app.exception_handlers)
    state = dict(app.state._state)
    with pytest.raises(MountConflictError):
        _integration().mount(app, prefix="")
    assert app.routes == routes
    assert app.exception_handlers == handlers
    assert app.state._state == state


def test_prefixed_mount_rejects_included_router_namespace() -> None:
    app = FastAPI()
    router = APIRouter()

    @router.get("/etl/host", operation_id="host_included")
    def host_included() -> dict[str, str]:
        return {"status": "host"}

    app.include_router(router)
    with pytest.raises(MountConflictError):
        _integration().mount(app, prefix="/etl")


def test_prefixed_mount_rejects_earlier_catch_all_route() -> None:
    app = FastAPI()

    @app.get("/{path:path}", operation_id="host_catch_all")
    def host_catch_all(path: str) -> dict[str, str]:
        return {"path": path}

    with pytest.raises(MountConflictError):
        _integration().mount(app, prefix="/etl")


class _SensitiveRepr:
    def __repr__(self) -> str:
        return "<provider password=review-secret>"


class _ExplodingRepr:
    def __repr__(self) -> str:
        raise RuntimeError("repr must not run")


@pytest.mark.parametrize("value", [_SensitiveRepr(), _ExplodingRepr()])
def test_non_string_prefix_is_rejected_without_evaluating_repr(value: object) -> None:
    with pytest.raises(InvalidPrefixError) as raised:
        _integration().mount(FastAPI(), prefix=cast(str, value))
    assert "review-secret" not in str(raised.value)


def test_evidence_checker_defaults_to_the_current_release_series() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    release_series = ".".join(project["project"]["version"].split(".")[:2])
    assert check_evidence.EVIDENCE.name == release_series


def test_user_documentation_covers_required_integration_safety_contract() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    required_concepts = {
        "lifespan composition API": ("compose_lifespan(",),
        "host-first lifespan ordering": ("host first", "host-first"),
        "mount timing": ("before startup", "prior to startup"),
        "invalid-prefix error": ("invalidprefixerror",),
        "mount-conflict error": ("mountconflicterror",),
        "provider non-ownership": ("does not start", "never starts", "will not start"),
    }
    missing = [
        concept
        for concept, alternatives in required_concepts.items()
        if not any(alternative in readme for alternative in alternatives)
    ]
    assert not missing, f"README omits Phase 0.2 safety guidance: {missing}"
