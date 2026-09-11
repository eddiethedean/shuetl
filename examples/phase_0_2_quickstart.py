"""Minimal ShuETL 0.2 local/test integration example.

Run this file from an installed wheel with the ETLantic test dependencies
available. The memory providers are process-local and are not a production
persistence profile.
"""

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
    membership_context_factory,
    principal_from_header,
)
from fastapi import FastAPI

from shuetl import ShuETL

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
api = ETLanticAPI(
    authorizer=authorizer,
    definitions=MemoryDefinitionRepository(),
    submissions=MemorySubmissionStore(),
    events=MemoryEventStore(),
    context_factory=membership_context_factory(
        {"alice": ("tenant-a", "ws-1", "development", "default")}
    ),
    principal_dependency=principal_from_header,
)
integration = ShuETL(api=api)  # Providers remain owned by the host application.

# Embedded mode: choose the facade lifespan when constructing the host app.
app = FastAPI(lifespan=integration.lifespan)
integration.mount(app, prefix="/etl")

# Dedicated mode uses the same upstream API and routes at the root.
dedicated_app = integration.create_app()


if __name__ == "__main__":
    print(f"mounted {len(app.routes)} routes; dedicated={dedicated_app.title}")
