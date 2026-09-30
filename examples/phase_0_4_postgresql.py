"""Compose a PostgreSQL bundle into an authenticated host application.

Provision with ``shuetl database upgrade`` before calling this helper. The host
supplies its credential-verified identity adapter and ETLantic authorizer; this
example deliberately supplies neither a header-based principal nor a default
allow policy.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from etlantic.control_plane import Authorizer
from fastapi import FastAPI

from shuetl import HostIdentityAdapter, PostgreSQLProviderBundle, ShuETL, ShuETLSettings


def create_postgresql_host(
    settings: ShuETLSettings,
    *,
    authorizer: Authorizer,
    identity_adapter: HostIdentityAdapter,
    host_app: FastAPI | None = None,
) -> tuple[FastAPI, PostgreSQLProviderBundle]:
    """Build the host graph with caller-owned policy and native auth dependency."""
    bundle = PostgreSQLProviderBundle.create(
        settings,
        authorizer=authorizer,
        identity_adapter=identity_adapter,
    )
    try:
        integration = ShuETL(api=bundle.api)

        if host_app is None:
            host_app = FastAPI()
        host_lifespan = host_app.router.lifespan_context
        integration.mount(host_app, prefix=settings.api_prefix)
        composed_lifespan = integration.compose_lifespan(host_lifespan)

        @asynccontextmanager
        async def close_bundle(app: FastAPI):
            try:
                async with composed_lifespan(app):
                    yield
            finally:
                bundle.close()

        host_app.router.lifespan_context = close_bundle
    except BaseException:
        bundle.close()
        raise
    return host_app, bundle


def main() -> None:
    raise SystemExit(
        "Import create_postgresql_host from the host application and pass its "
        "ETLantic authorizer plus HostIdentityAdapter."
    )


if __name__ == "__main__":
    main()
