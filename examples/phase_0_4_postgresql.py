"""Build the Phase 0.4 PostgreSQL gateway after explicit provisioning.

Set the documented ``SHUETL_*`` variables, run ``shuetl database upgrade``
with a migration-capable role, then execute this example with the gateway role.
The example only constructs the graph and FastAPI application; the host owns
the server lifecycle and calls ``close`` during shutdown.
"""

from etlantic.control_plane.memory import MemoryAuthorizer
from etlantic_fastapi.auth import principal_from_header, static_context_factory

from shuetl import PostgreSQLProviderBundle, ShuETL, ShuETLSettings


def main() -> None:
    settings = ShuETLSettings()
    bundle = PostgreSQLProviderBundle.create(
        settings,
        authorizer=MemoryAuthorizer(),
        context_factory=static_context_factory(
            tenant_id="example-tenant", workspace_id="example-workspace"
        ),
        principal_dependency=principal_from_header,
    )
    try:
        app = ShuETL(api=bundle.api).create_app(prefix=settings.api_prefix)
        print(f"created PostgreSQL gateway with {len(app.routes)} routes")
    finally:
        bundle.close()


if __name__ == "__main__":
    main()
