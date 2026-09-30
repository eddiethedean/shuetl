"""OIDC composition recipe with a synthetic, test-only token verifier.

Production hosts must pass a maintained verifier that validates signature,
issuer, audience, expiry, token use, and revocation requirements before returning
claims. ShuETL receives only the already verified ETLantic Principal.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
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
from fastapi import Security
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.testclient import TestClient

from shuetl import HostIdentityAdapter, ShuETL

ISSUER = "https://issuer.example"


async def _synthetic_test_verifier(token: str) -> Mapping[str, Any]:
    """Replace this smoke fixture with the host's verified OIDC access-token API."""
    if token == "synthetic-outage-token":
        raise ControlPlaneError(
            "Host identity service is unavailable.",
            code="PMCP503",
            status=503,
            title="Service Unavailable",
        )
    if token == "synthetic-valid-access-token":
        return {"sub": "oidc-user-42", "iss": ISSUER, "token_use": "access"}
    raise ControlPlaneError.unauthorized("A verified host identity is required.")


def create_app(
    verify_access_token: Callable[[str], Awaitable[Mapping[str, Any]]] = (
        _synthetic_test_verifier
    ),
):
    """Create a composed app; production callers supply their host OIDC verifier."""
    oauth = OAuth2AuthorizationCodeBearer(
        authorizationUrl="https://issuer.example/authorize",
        tokenUrl="https://issuer.example/token",
        scopes={"etl.read": "Read ETLantic control-plane definitions"},
    )

    async def authenticated_principal(
        token: str = Security(oauth, scopes=["etl.read"]),
    ) -> Principal:
        claims = await verify_access_token(token)
        subject = claims.get("sub")
        issuer = claims.get("iss")
        token_use = claims.get("token_use")
        if (
            not isinstance(subject, str)
            or not subject.strip()
            or issuer != ISSUER
            or token_use != "access"
        ):
            raise ControlPlaneError.unauthorized(
                "A verified host identity is required."
            )
        return Principal(subject=subject, issuer=issuer, kind="human")

    def host_membership_context(
        principal: Principal, _request: Any
    ) -> ControlPlaneContext:
        if (principal.issuer, principal.subject) != (ISSUER, "oidc-user-42"):
            raise ControlPlaneError.unauthorized("Host membership is unavailable.")
        return ControlPlaneContext(
            principal=principal,
            tenant=TenantRef(tenant_id="tenant-oidc-example"),
            workspace=WorkspaceRef(
                tenant_id="tenant-oidc-example", workspace_id="workspace-oidc-example"
            ),
            environment=EnvironmentRef(name="production"),
            security_domain=SecurityDomain(domain_id="default"),
        )

    adapter = HostIdentityAdapter.create(
        principal_dependency=authenticated_principal,
        context_factory=host_membership_context,
    )
    seed_principal = Principal("oidc-user-42", issuer=ISSUER, kind="human")
    seed_context = host_membership_context(seed_principal, None)
    authorizer = MemoryAuthorizer()
    authorizer.grant(seed_context, "definition.list")
    api = ETLanticAPI(
        authorizer=authorizer,
        definitions=MemoryDefinitionRepository(),
        submissions=MemorySubmissionStore(),
        events=MemoryEventStore(),
        context_factory=adapter.context_factory,
        principal_dependency=adapter.principal_dependency,
        profile="production",
    )
    return ShuETL(api=api).create_app(prefix="/etl")


def main() -> None:
    app = create_app()
    with TestClient(app) as client:
        cases = (
            (None, 401),
            ("synthetic-invalid-access-token", 401),
            ("synthetic-expired-access-token", 401),
            ("synthetic-outage-token", 503),
            ("synthetic-valid-access-token", 200),
        )
        for token, expected in cases:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            response = client.get("/etl/v1/definitions", headers=headers)
            assert response.status_code == expected
            if token and expected != 200:
                assert token not in response.text
    print("OIDC host composition smoke checks passed")


if __name__ == "__main__":
    main()
