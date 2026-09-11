"""Provision and run the Phase 0.3 pre-migrated SQLite profile."""

from __future__ import annotations

import tempfile
from pathlib import Path

from etlantic.control_plane import MemoryAuthorizer
from etlantic_fastapi import membership_context_factory, principal_from_header
from etlantic_sqlmodel import apply_migrations, create_sqlite_engine
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shuetl import LocalProviderBundle, ShuETL, ShuETLSettings


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="shuetl-0.3-sqlite-") as directory:
        database = Path(directory) / "shuetl.db"
        database_url = f"sqlite+pysqlite:///{database}"

        # Provisioning is an explicit operator step, outside bundle startup.
        engine = create_sqlite_engine(database_url)
        try:
            apply_migrations(engine)
        finally:
            engine.dispose()

        settings = ShuETLSettings(
            profile="local",
            role="gateway",
            provider="sqlite",
            identity="host",
            database_url=database_url,
        )
        authorizer = MemoryAuthorizer()
        bundle = LocalProviderBundle.create(
            settings,
            authorizer=authorizer,
            context_factory=membership_context_factory(
                {"alice": ("tenant-a", "workspace-a", "development", "default")}
            ),
            principal_dependency=principal_from_header,
        )
        try:
            integration = ShuETL(api=bundle.api)
            app = FastAPI(lifespan=integration.lifespan)
            integration.mount(app, prefix=settings.api_prefix)
            with TestClient(app) as client:
                response = client.get("/etl/health")
                response.raise_for_status()
            print(f"sqlite provider ready at {database}; provider={bundle.provider}")
        finally:
            bundle.close()


if __name__ == "__main__":
    main()
