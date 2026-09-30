"""FastAPI-native dependency behavior through the ShuETL facade."""

from __future__ import annotations

from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock

from etlantic.control_plane import (
    AuthzDecision,
    ControlPlaneContext,
    EnvironmentRef,
    MemoryDefinitionRepository,
    MemoryEventStore,
    MemorySubmissionStore,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic.control_plane.memory import MemoryAuthorizer
from etlantic_fastapi import ETLanticAPI, create_app
from fastapi import FastAPI, Request, Security
from fastapi.security import OAuth2PasswordBearer
from fastapi.testclient import TestClient
from pydantic import BaseModel

from shuetl import HostIdentityAdapter, ShuETL


class _RecordingAllowAuthorizer:
    def __init__(self) -> None:
        self.calls: list[tuple[ControlPlaneContext, str, str]] = []

    def authorize(
        self,
        ctx: ControlPlaneContext,
        action: str,
        resource: str,
    ) -> AuthzDecision:
        self.calls.append((ctx, action, resource))
        return AuthzDecision(allowed=True, reason="test grant")


def _api(adapter: HostIdentityAdapter, authorizer: object) -> ETLanticAPI:
    return ETLanticAPI(
        authorizer=authorizer,  # type: ignore[arg-type]
        definitions=MemoryDefinitionRepository(),
        submissions=MemorySubmissionStore(),
        events=MemoryEventStore(),
        context_factory=adapter.context_factory,
        principal_dependency=adapter.principal_dependency,
        profile="development",
    )


def test_nested_security_keyword_only_and_yield_dependencies_remain_native() -> None:
    oauth = OAuth2PasswordBearer(tokenUrl="/token")
    yielded: list[str] = []
    principals: list[Principal] = []
    contexts: list[ControlPlaneContext] = []

    async def authenticate(
        *, token: str = Security(oauth, scopes=["etl.read"])
    ) -> AsyncIterator[Principal]:
        principal = Principal(subject=token, issuer="https://issuer.example")
        principals.append(principal)
        try:
            yield principal
        finally:
            yielded.append(token)

    def make_context(principal: Principal, request: Request) -> ControlPlaneContext:
        del request
        context = ControlPlaneContext(
            principal=principal,
            tenant=TenantRef(tenant_id="tenant-a"),
            workspace=WorkspaceRef(tenant_id="tenant-a", workspace_id="workspace-a"),
            environment=EnvironmentRef(name="production"),
            security_domain=SecurityDomain(domain_id="default"),
        )
        contexts.append(context)
        return context

    adapter = HostIdentityAdapter.create(
        principal_dependency=authenticate,
        context_factory=make_context,
    )
    authorizer = _RecordingAllowAuthorizer()
    api = _api(adapter, authorizer)
    assert principals == []
    integration = ShuETL(api=api)
    app = integration.create_app(prefix="/private/etl")

    with TestClient(app) as client:
        response = client.get(
            "/private/etl/v1/definitions",
            headers={"Authorization": "Bearer alice"},
        )
        assert response.status_code == 200
        assert response.json() == {"items": []}
        assert yielded == ["alice"]
        assert contexts[-1].principal is principals[-1]
        assert authorizer.calls[-1][0] is contexts[-1]

        def overridden_principal() -> Principal:
            principal = Principal(subject="override-user")
            principals.append(principal)
            return principal

        app.dependency_overrides[authenticate] = overridden_principal
        overridden = client.get(
            "/private/etl/v1/definitions",
            headers={"Authorization": "Bearer ignored"},
        )
        app.dependency_overrides.pop(authenticate)

    assert overridden.status_code == 200
    assert contexts[-1].principal is principals[-1]
    assert contexts[-1].principal.subject == "override-user"
    assert "OAuth2PasswordBearer" in app.openapi()["components"]["securitySchemes"]
    operation = app.openapi()["paths"]["/private/etl/v1/definitions"]["get"]
    assert {"OAuth2PasswordBearer": ["etl.read"]} in operation["security"]


def test_upstream_validation_errors_are_redacted_without_changing_host_routes() -> None:
    adapter = HostIdentityAdapter.development_static(
        principal=Principal(subject="local-user"),
        tenant_id="tenant-a",
        workspace_id="workspace-a",
    )
    api = _api(adapter, MemoryAuthorizer())
    direct = create_app(api)
    host = FastAPI()

    class HostInput(BaseModel):
        count: int

    @host.post("/host-validation")
    def host_validation(body: HostInput) -> dict[str, int]:
        return {"count": body.count}

    ShuETL(api=api).mount(host, prefix="/etl")

    payload = {"idempotency_key": {"password": "secret-sentinel-422"}}
    with TestClient(direct) as direct_client, TestClient(host) as host_client:
        direct_response = direct_client.post(
            "/v1/definitions/example/runs", json=payload
        )
        mounted_response = host_client.post(
            "/etl/v1/definitions/example/runs", json=payload
        )
        invalid_query = host_client.get(
            "/etl/v1/durable/outbox?limit=query-sentinel-422"
        )
        unrelated_host_response = host_client.post(
            "/host-validation", json={"count": "host-sentinel-422"}
        )

    safe_body = {
        "detail": [{"type": "request_validation", "loc": [], "msg": "Invalid request"}]
    }
    assert direct_response.status_code == mounted_response.status_code == 422
    assert direct_response.json() == mounted_response.json() == safe_body
    assert invalid_query.status_code == 422
    assert invalid_query.json() == safe_body
    assert "secret-sentinel-422" not in direct_response.text
    assert "secret-sentinel-422" not in mounted_response.text
    assert "query-sentinel-422" not in invalid_query.text
    assert unrelated_host_response.status_code == 422


def test_mount_rechecks_production_guard_before_mutating_the_host() -> None:
    def principal_dependency() -> Principal:
        return Principal(subject="alice")

    def make_context(principal: Principal, _request: Request) -> ControlPlaneContext:
        return ControlPlaneContext(
            principal=principal,
            tenant=TenantRef(tenant_id="tenant-a"),
            workspace=WorkspaceRef(tenant_id="tenant-a", workspace_id="workspace-a"),
            environment=EnvironmentRef(name="production"),
            security_domain=SecurityDomain(domain_id="default"),
        )

    adapter = HostIdentityAdapter.create(
        principal_dependency=principal_dependency,
        context_factory=make_context,
    )
    api = _api(adapter, _RecordingAllowAuthorizer())
    api.profile = "production"
    integration = ShuETL(api=api)
    api.principal_dependency = lambda: Principal(subject="reassigned")

    app = FastAPI()
    routes_before = list(app.routes)
    handlers_before = dict(app.exception_handlers)
    lifespan_before = app.router.lifespan_context
    openapi_before = app.openapi_schema

    try:
        integration.mount(app)
    except Exception as exc:
        assert "matching host identity adapter" in str(exc)
    else:
        raise AssertionError("mount accepted a reassigned production dependency")

    assert app.routes == routes_before
    assert app.exception_handlers == handlers_before
    assert app.router.lifespan_context is lifespan_before
    assert app.openapi_schema is openapi_before
    assert app.state._state == {}


def test_concurrent_principals_keep_independent_scopes() -> None:
    rendezvous = Barrier(2)
    contexts_seen: list[ControlPlaneContext] = []
    lock = Lock()

    async def authenticate(request: Request) -> Principal:
        subject = request.headers["X-Principal"]
        return Principal(subject=subject, issuer="https://issuer.example")

    def make_context(principal: Principal, _request: Request) -> ControlPlaneContext:
        rendezvous.wait(timeout=5)
        return ControlPlaneContext(
            principal=principal,
            tenant=TenantRef(tenant_id=f"tenant-{principal.subject}"),
            workspace=WorkspaceRef(
                tenant_id=f"tenant-{principal.subject}",
                workspace_id=f"workspace-{principal.subject}",
            ),
            environment=EnvironmentRef(name="production"),
            security_domain=SecurityDomain(domain_id="default"),
        )

    class ConcurrentAuthorizer:
        def authorize(
            self,
            ctx: ControlPlaneContext,
            _action: str,
            _resource: str,
        ) -> AuthzDecision:
            with lock:
                contexts_seen.append(ctx)
            return AuthzDecision(allowed=True, reason="synthetic concurrent grant")

    adapter = HostIdentityAdapter.create(
        principal_dependency=authenticate,
        context_factory=make_context,
    )
    api = _api(adapter, ConcurrentAuthorizer())
    api.definitions.put(
        ControlPlaneContext(
            principal=Principal("alice", issuer="https://issuer.example"),
            tenant=TenantRef(tenant_id="tenant-alice"),
            workspace=WorkspaceRef(
                tenant_id="tenant-alice", workspace_id="workspace-alice"
            ),
            environment=EnvironmentRef(name="production"),
            security_domain=SecurityDomain(domain_id="default"),
        ),
        "alice-only",
        {"name": "alice"},
    )
    api.definitions.put(
        ControlPlaneContext(
            principal=Principal("bob", issuer="https://issuer.example"),
            tenant=TenantRef(tenant_id="tenant-bob"),
            workspace=WorkspaceRef(
                tenant_id="tenant-bob", workspace_id="workspace-bob"
            ),
            environment=EnvironmentRef(name="production"),
            security_domain=SecurityDomain(domain_id="default"),
        ),
        "bob-only",
        {"name": "bob"},
    )
    app = ShuETL(api=api).create_app()
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=2) as pool:
        alice = pool.submit(
            client.get, "/v1/definitions", headers={"X-Principal": "alice"}
        )
        bob = pool.submit(client.get, "/v1/definitions", headers={"X-Principal": "bob"})
        alice_response = alice.result(timeout=10)
        bob_response = bob.result(timeout=10)

    assert alice_response.status_code == bob_response.status_code == 200
    assert alice_response.json() == {"items": [{"definition_id": "alice-only"}]}
    assert bob_response.json() == {"items": [{"definition_id": "bob-only"}]}
    assert {
        (ctx.principal.subject, ctx.tenant.tenant_id, ctx.workspace.workspace_id)
        for ctx in contexts_seen
    } == {
        ("alice", "tenant-alice", "workspace-alice"),
        ("bob", "tenant-bob", "workspace-bob"),
    }
