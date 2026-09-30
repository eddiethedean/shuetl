"""Session-host composition recipe with a clearly test-only session harness.

A production host must supply its session resolver and middleware, including
cookie signing, expiry/revocation, Secure/HttpOnly/SameSite, CSRF checks for every
mutation, trusted proxy handling, and TLS. ShuETL receives only the host's
already validated Principal through native FastAPI dependency injection.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from etlantic.control_plane import (
    ControlPlaneContext,
    ControlPlaneError,
    EnvironmentRef,
    MemoryEventStore,
    MemorySubmissionStore,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic.control_plane.memory import MemoryAuthorizer, MemoryDefinitionRepository
from etlantic_fastapi import ETLanticAPI
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from shuetl import HostIdentityAdapter, ShuETL


def create_app() -> FastAPI:
    """Create a local smoke app; replace test middleware with the real host."""

    async def principal_from_host_session(request: Request) -> AsyncIterator[Principal]:
        principal = getattr(request.state, "host_principal", None)
        if not isinstance(principal, Principal):
            raise ControlPlaneError.unauthorized(
                "A validated host session is required."
            )
        yield principal

    def host_membership_context(
        principal: Principal, _request: Request
    ) -> ControlPlaneContext:
        if principal.subject != "session-user-42":
            raise ControlPlaneError.unauthorized("Host membership is unavailable.")
        return ControlPlaneContext(
            principal=principal,
            tenant=TenantRef(tenant_id="tenant-session-example"),
            workspace=WorkspaceRef(
                tenant_id="tenant-session-example",
                workspace_id="workspace-session-example",
            ),
            environment=EnvironmentRef(name="production"),
            security_domain=SecurityDomain(domain_id="default"),
        )

    adapter = HostIdentityAdapter.create(
        principal_dependency=principal_from_host_session,
        context_factory=host_membership_context,
    )
    seed = Principal("session-user-42", issuer="https://host.example", kind="human")
    context = host_membership_context(seed, Request({"type": "http", "headers": []}))
    authorizer = MemoryAuthorizer()
    authorizer.grant(context, "definition.list")
    api = ETLanticAPI(
        authorizer=authorizer,
        definitions=MemoryDefinitionRepository(),
        submissions=MemorySubmissionStore(),
        events=MemoryEventStore(),
        context_factory=adapter.context_factory,
        principal_dependency=adapter.principal_dependency,
        profile="production",
    )
    host = FastAPI()

    @host.middleware("http")
    async def _test_only_session_and_csrf(request: Request, call_next: Any):
        session = request.cookies.get("session")
        if session == "synthetic-session-outage":
            return JSONResponse(
                {"detail": "Host session service unavailable"}, status_code=503
            )
        if session != "synthetic-valid-session":
            return JSONResponse(
                {"detail": "A validated host session is required"}, status_code=401
            )
        if (
            request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and request.headers.get("X-CSRF-Token") != "synthetic-csrf-token"
        ):
            return JSONResponse({"detail": "CSRF validation failed"}, status_code=403)
        request.state.host_principal = seed
        return await call_next(request)

    @host.post("/host-mutation")
    async def host_mutation() -> dict[str, bool]:
        return {"ok": True}

    ShuETL(api=api).mount(host, prefix="/etl")
    return host


def main() -> None:
    app = create_app()
    with TestClient(app) as client:
        assert client.get("/etl/v1/definitions").status_code == 401
        assert (
            client.get(
                "/etl/v1/definitions", cookies={"session": "synthetic-expired-session"}
            ).status_code
            == 401
        )
        assert (
            client.get(
                "/etl/v1/definitions", cookies={"session": "synthetic-session-outage"}
            ).status_code
            == 503
        )
        valid = {"session": "synthetic-valid-session"}
        assert client.get("/etl/v1/definitions", cookies=valid).status_code == 200
        assert client.post("/host-mutation", cookies=valid).status_code == 403
        assert (
            client.post(
                "/host-mutation",
                cookies=valid,
                headers={"X-CSRF-Token": "synthetic-csrf-token"},
            ).status_code
            == 200
        )
    print("session host composition smoke checks passed")


if __name__ == "__main__":
    main()
