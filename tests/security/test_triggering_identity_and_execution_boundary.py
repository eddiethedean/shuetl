"""Trigger identity persistence and no secret/executor side effects in ShuETL."""

from __future__ import annotations

import json
from typing import Any

import pytest
from etlantic.control_plane import (
    ControlPlaneContext,
    EnvironmentRef,
    MemoryEventStore,
    MemoryScheduleStore,
    MemorySubmissionStore,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic.control_plane.durable_memory import MemoryDurableWorkStore
from etlantic.control_plane.memory import MemoryAuthorizer, MemoryDefinitionRepository
from etlantic_fastapi import ETLanticAPI
from fastapi import Request
from fastapi.testclient import TestClient

from shuetl import HostIdentityAdapter, ShuETL

BEARER_SENTINEL = "synthetic-bearer-credential-sentinel"
COOKIE_SENTINEL = "synthetic-session-cookie-sentinel"


def _context(principal: Principal) -> ControlPlaneContext:
    return ControlPlaneContext(
        principal=principal,
        tenant=TenantRef(tenant_id="trigger-tenant"),
        workspace=WorkspaceRef(
            tenant_id="trigger-tenant", workspace_id="trigger-workspace"
        ),
        environment=EnvironmentRef(name="production"),
        security_domain=SecurityDomain(domain_id="default"),
    )


def _api_and_context(
    adapter: HostIdentityAdapter,
    durable: Any = None,
    schedule_store: MemoryScheduleStore | None = None,
) -> ETLanticAPI:
    principal = Principal(
        subject="verified-user-42",
        issuer="https://issuer.example",
        kind="human",
    )
    ctx = _context(principal)
    authorizer = MemoryAuthorizer()
    authorizer.grant(ctx, "definition.list")
    authorizer.grant(ctx, "definition.read")
    authorizer.grant(ctx, "definition.validate")
    authorizer.grant(ctx, "definition.plan")
    authorizer.grant(ctx, "run.submit")
    authorizer.grant(ctx, "schedule.write")
    definitions = MemoryDefinitionRepository()
    definitions.put(
        ctx,
        "identity-definition",
        {"fingerprint": "safe-fingerprint", "name": "identity probe"},
    )
    return ETLanticAPI(
        authorizer=authorizer,
        definitions=definitions,
        submissions=MemorySubmissionStore(),
        events=MemoryEventStore(),
        durable_work=durable,
        schedule_store=schedule_store,
        context_factory=adapter.context_factory,
        principal_dependency=adapter.principal_dependency,
        profile="production",
    )


def test_durable_submission_persists_only_trigger_identity_and_no_credentials() -> None:
    def authenticated_host_dependency(_request: Request) -> Principal:
        return Principal(
            subject="verified-user-42",
            issuer="https://issuer.example",
            kind="human",
        )

    adapter = HostIdentityAdapter.create(
        principal_dependency=authenticated_host_dependency,
        context_factory=lambda principal, _request: _context(principal),
    )
    durable = MemoryDurableWorkStore()
    api = _api_and_context(adapter, durable)
    app = ShuETL(api=api).create_app(prefix="/etl")
    with TestClient(app) as client:
        rejected = client.post(
            "/etl/v1/definitions/identity-definition/runs",
            headers={"Idempotency-Key": "forged-snapshot"},
            json={"payload": {"input_snapshot": "caller-created-snapshot"}},
        )
        assert rejected.status_code == 400
        assert durable.dump()["submissions"] == {}
        response = client.post(
            "/etl/v1/definitions/identity-definition/runs",
            headers={
                "Authorization": f"Bearer {BEARER_SENTINEL}",
                "Cookie": f"session={COOKIE_SENTINEL}",
                "Idempotency-Key": "identity-persistence-key",
            },
            json={"payload": {}},
        )

    assert response.status_code == 202
    submission_id = response.json()["submission_id"]
    stored = durable.dump()
    rows = [
        value
        for value in stored["submissions"].values()
        if value["submission_id"] == submission_id
    ]
    assert len(rows) == 1
    assert rows[0]["principal_subject"] == "verified-user-42"
    assert rows[0]["principal_issuer"] == "https://issuer.example"
    assert rows[0]["principal_kind"] == "human"
    serialized = json.dumps(stored, sort_keys=True)
    assert BEARER_SENTINEL not in serialized
    assert COOKIE_SENTINEL not in serialized
    assert BEARER_SENTINEL not in response.text
    assert COOKIE_SENTINEL not in response.text


def test_validate_plan_and_submit_never_resolve_secrets_or_execute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import etlantic.runtime.execute as execute
    from etlantic.authoring import pipeline_definition, pipeline_to_dict
    from etlantic.secrets import (
        EnvSecretProvider,
        MountedFileSecretProvider,
        SecretCache,
    )
    from etlantic.secrets.value import SecretValue

    calls: list[str] = []

    def forbidden(name: str):
        def fail(*_args: Any, **_kwargs: Any) -> Any:
            calls.append(name)
            raise AssertionError(f"gateway invoked {name}")

        return fail

    monkeypatch.setattr(SecretCache, "get", forbidden("secret-cache.get"))
    monkeypatch.setattr(EnvSecretProvider, "resolve", forbidden("env-secret.resolve"))
    monkeypatch.setattr(
        MountedFileSecretProvider,
        "resolve",
        forbidden("file-secret.resolve"),
    )
    monkeypatch.setattr(
        SecretValue,
        "get_secret_value",
        forbidden("secret-value.read"),
    )
    monkeypatch.setattr(execute, "run_pipeline", forbidden("pipeline.run"))
    monkeypatch.setattr(execute, "arun_pipeline", forbidden("pipeline.arun"))

    principal = Principal(
        subject="verified-user-42",
        issuer="https://issuer.example",
        kind="human",
    )
    ctx = _context(principal)
    adapter = HostIdentityAdapter.create(
        principal_dependency=lambda: principal,
        context_factory=lambda authenticated, _request: _context(authenticated),
    )
    schedules = MemoryScheduleStore()
    document = pipeline_to_dict(
        pipeline_definition("canonical-security-probe", "Canonical Security Probe")
    )
    api = _api_and_context(adapter, schedule_store=schedules)
    api.definitions.put(ctx, "canonical-security-probe", document)
    app = ShuETL(api=api).create_app()

    with TestClient(app) as client:
        validated = client.post("/v1/definitions/canonical-security-probe/validate")
        planned = client.post("/v1/definitions/canonical-security-probe/plan")
        submitted = client.post(
            "/v1/definitions/identity-definition/runs",
            headers={
                "Idempotency-Key": "no-execution-key",
                "Authorization": f"Bearer {BEARER_SENTINEL}",
                "Cookie": f"session={COOKIE_SENTINEL}",
            },
            json={"payload": {}},
        )
        scheduled = client.post(
            "/v1/definitions/identity-definition/schedules",
            headers={
                "Authorization": f"Bearer {BEARER_SENTINEL}",
                "Cookie": f"session={COOKIE_SENTINEL}",
            },
            json={
                "spec": {"kind": "interval", "interval_seconds": 60},
                "parameter_refs": {"source": "configured-parameter-reference"},
            },
        )

    assert validated.status_code == planned.status_code == 200
    assert submitted.status_code == 202
    assert scheduled.status_code == 201
    stored_schedules = json.dumps(
        [record.to_dict() for record in schedules.list_schedules(ctx)], sort_keys=True
    )
    assert BEARER_SENTINEL not in stored_schedules
    assert COOKIE_SENTINEL not in stored_schedules
    assert not calls
