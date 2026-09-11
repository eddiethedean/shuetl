"""Minimal ShuETL 0.3 memory bundle example."""

from etlantic.control_plane import (
    ControlPlaneContext,
    EnvironmentRef,
    MemoryAuthorizer,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic_fastapi import membership_context_factory, principal_from_header
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shuetl import LocalProviderBundle, ShuETL, ShuETLSettings

context = ControlPlaneContext(
    principal=Principal(subject="alice"),
    tenant=TenantRef(tenant_id="tenant-a"),
    workspace=WorkspaceRef(tenant_id="tenant-a", workspace_id="ws-1"),
    environment=EnvironmentRef(name="development"),
    security_domain=SecurityDomain(domain_id="default"),
)
authorizer = MemoryAuthorizer()
for action in ("definition.list", "definition.read", "run.submit"):
    authorizer.grant(context, action)

settings = ShuETLSettings(
    profile="local", role="gateway", provider="memory", identity="host"
)
bundle = LocalProviderBundle.create(
    settings,
    authorizer=authorizer,
    context_factory=membership_context_factory(
        {"alice": ("tenant-a", "ws-1", "development", "default")}
    ),
    principal_dependency=principal_from_header,
)
integration = ShuETL(api=bundle.api)
app = FastAPI(lifespan=integration.lifespan)
integration.mount(app, prefix=settings.api_prefix)

if __name__ == "__main__":
    try:
        with TestClient(app) as client:
            response = client.get("/etl/health")
            response.raise_for_status()
        print(f"mounted {len(app.routes)} routes; provider={bundle.provider}")
    finally:
        bundle.close()
