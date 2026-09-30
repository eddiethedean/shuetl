"""Explicit fixed identity for local development and tests only."""

from __future__ import annotations

from etlantic.control_plane import (
    ControlPlaneContext,
    EnvironmentRef,
    MemoryAuthorizer,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from fastapi.testclient import TestClient

from shuetl import (
    HostIdentityAdapter,
    LocalProviderBundle,
    ShuETL,
    ShuETLSettings,
)


def main() -> None:
    settings = ShuETLSettings(
        profile="local",
        role="gateway",
        provider="memory",
        identity="development-static",
    )
    adapter = HostIdentityAdapter.development_static(
        principal=Principal("local-example", issuer="local-development", kind="human"),
        tenant_id="local-tenant",
        workspace_id="local-workspace",
    )
    fixed_context = ControlPlaneContext(
        principal=Principal("local-example", issuer="local-development", kind="human"),
        tenant=TenantRef(tenant_id="local-tenant"),
        workspace=WorkspaceRef(
            tenant_id="local-tenant", workspace_id="local-workspace"
        ),
        environment=EnvironmentRef(name="development"),
        security_domain=SecurityDomain(domain_id="default"),
    )
    authorizer = MemoryAuthorizer()
    authorizer.grant(fixed_context, "definition.list")
    bundle = LocalProviderBundle.create(
        settings,
        authorizer=authorizer,
        identity_adapter=adapter,
    )
    try:
        app = ShuETL(api=bundle.api).create_app()
        with TestClient(app) as client:
            response = client.get(
                "/v1/definitions", headers={"X-Principal": "forged-user"}
            )
        assert response.status_code == 200
        assert response.json() == {"items": []}
    finally:
        bundle.close()
    print("development-static identity smoke checks passed")


if __name__ == "__main__":
    main()
