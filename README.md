# ShuETL

[![PyPI version](https://img.shields.io/pypi/v/shuetl.svg)](https://pypi.org/project/shuetl/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/shuetl.svg)](https://pypi.org/project/shuetl/)
[![CI](https://github.com/eddiethedean/shuetl/actions/workflows/ci.yml/badge.svg)](https://github.com/eddiethedean/shuetl/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/shuetl.svg)](https://github.com/eddiethedean/shuetl/blob/main/LICENSE)

**ShuETL** *(pronounced “shuttle”)* is the opinionated FastAPI integration and
deployment package for ETLantic.

> **ShuETL composes ETLantic into a durable, schedulable FastAPI service.**

ShuETL does not reimplement ETLantic's pipeline or control-plane semantics.
Instead, it assembles ETLantic's public packages, contracts, stores, and runtime
roles into a coherent application-facing experience.

- **ETLantic** owns canonical pipeline definitions and revisions, planning,
  execution semantics, durable submission, run and attempt state, scheduling,
  reports, events, artifacts, idempotency, recovery, and provider protocols.
- **`etlantic-fastapi`** is ETLantic's low-level HTTP adapter and authoritative
  source of ETLantic request, response, route, SSE, and error semantics.
- **ShuETL** owns opinionated composition: configuration, provider wiring,
  FastAPI mounting, lifecycle integration, deployment profiles, compatibility
  pins, optional ecosystem adapters, and operator-focused documentation.

If a required semantic capability is absent from ETLantic, the default response
is to add it to ETLantic or one of its provider packages. ShuETL must not create
a competing `Pipeline`, `Run`, `Schedule`, `Artifact`, or executor model.

## Architecture principles

- **Integrate; do not reinterpret.**
- **One ETLantic contract at every boundary.**
- **Useful defaults, replaceable providers.**
- **FastAPI-native composition and lifecycle.**
- **Development convenience must not become a false production guarantee.**
- **SQL-only infrastructure baseline where the selected ETLantic providers
  support it.**

The reference ecosystem can compose in one FastAPI application:

```text
FastAPI host
├── Hedron presentation (optional)
├── AuthMate identity adapter (optional)
└── ShuETL
    ├── etlantic-fastapi
    ├── ETLantic control-plane/runtime contracts
    └── ETLantic persistence and execution providers
```

Hedron and AuthMate remain optional peer packages. ShuETL integrates with them
through public contracts and FastAPI dependencies.

## Status

ShuETL [0.4.0](https://pypi.org/project/shuetl/0.4.0/) was published on
2026-09-13 from the [`v0.4.0` tag](https://github.com/eddiethedean/shuetl/tree/v0.4.0).
The [release workflow](https://github.com/eddiethedean/shuetl/actions/runs/34778081760)
passed all checks and published the wheel and source distribution to PyPI.
It provides a typed FastAPI facade for local development and a
controlled single-tenant PostgreSQL pilot. It accepts a prebuilt
`etlantic_fastapi.ETLanticAPI`; the 0.3 local bundle additionally wires exact
upstream memory providers and an opt-in, pre-provisioned SQLite profile. The
0.4 PostgreSQL bundle wires ETLantic 0.52.1 registry, submission, event,
durable-work, and schedule stores. It does not provide a multi-tenant, HA, or
exactly-once external-effect guarantee.

The complete design pack is in [`docs/plans/`](docs/plans/README.md).

The implementation contracts are in
[`docs/plans/PHASE_0_1_EXECUTION.md`](docs/plans/PHASE_0_1_EXECUTION.md) and
[`docs/plans/PHASE_0_2_EXECUTION.md`](docs/plans/PHASE_0_2_EXECUTION.md), with
the Phase 0.3 contract in
[`docs/plans/PHASE_0_3_EXECUTION.md`](docs/plans/PHASE_0_3_EXECUTION.md).
The Phase 0.4 PostgreSQL contract is in
[`docs/plans/PHASE_0_4_EXECUTION.md`](docs/plans/PHASE_0_4_EXECUTION.md).

## Install

```bash
python -m pip install "shuetl==0.4.0"
# Optional pre-provisioned SQLite provider
python -m pip install "shuetl[sqlite]==0.4.0"
# Controlled PostgreSQL pilot provider
python -m pip install "shuetl[postgresql]==0.4.0"
```

## Quickstart

```python
from fastapi import FastAPI
from shuetl import ShuETL

integration = ShuETL(api=prebuilt_etlantic_api)
app = FastAPI(lifespan=integration.lifespan)
integration.mount(app, prefix="/etl")
```

Use `integration.create_app()` for a dedicated root-mounted application. Prefixes
are literal slash-prefixed segments (`/etl`, `/internal/etl`); use `""` for the
root. Mounting rejects occupied state keys, route namespaces, operation IDs, and
custom `ControlPlaneError` handlers before mutating the host. Dependency
overrides target the original ETLantic callables through ordinary FastAPI APIs.

For tests, override the exact upstream dependencies and remove them normally:

```python
app.dependency_overrides[integration.api.principal_dependency] = override_principal
app.dependency_overrides[integration.api.context_dependency] = override_context
# ...test...
app.dependency_overrides.pop(integration.api.principal_dependency, None)
app.dependency_overrides.pop(integration.api.context_dependency, None)
```

Mount the integration before startup. ShuETL does not start, stop,
close, or mutate caller-owned providers; the host remains responsible for their
lifecycle. When a host lifespan is present, compose it explicitly: the host
enters first and ShuETL exits before the host. The host first initializes
providers, then ShuETL records its active mount:

```python
from contextlib import asynccontextmanager


@asynccontextmanager
async def host_lifespan(app):
    # Initialize caller-owned ETLantic providers here.
    yield
    # Close caller-owned providers here.


app = FastAPI(lifespan=integration.compose_lifespan(host_lifespan))
integration.mount(app, prefix="/etl")
```

Prefixes are literal path segments: use `""` for the root, or a slash-prefixed
sequence of ASCII letters, digits, `.`, `_`, `~`, and `-` segments. A prefix may
not have a trailing slash or contain empty, dot, or dot-dot segments, route
parameters, query or fragment markers, percent escapes, backslashes, whitespace,
or control characters. `InvalidPrefixError` reports invalid prefixes. Mounting
raises `MountConflictError` before mutation when reserved state, handlers, route
namespaces, or operation IDs collide; resolve the host conflict before retrying.

Phase 0.4 adds immutable `ShuETLSettings`, `LocalProviderBundle`,
`PostgreSQLProviderBundle`, and the redacted `shuetl doctor` preflight CLI.
Settings use `SHUETL_*` environment variables; constructor values override the
environment. SQLite files must be provisioned and migrated by upstream tooling
before the bundle is created. PostgreSQL is provisioned explicitly with
`shuetl database upgrade`; application startup and doctor never migrate or
create tables. ShuETL never executes pipelines or accepts anonymous identity.
The host supplies the authorizer, context factory, principal dependency, TLS
trust configuration, database credentials, and closes the bundle.

### Settings contract

The supported settings are:

| Environment variable | Meaning | Default |
| --- | --- | --- |
| `SHUETL_PROFILE` | `local` or `postgresql-pilot` | required |
| `SHUETL_ROLE` | Runtime role; currently `gateway` | required |
| `SHUETL_PROVIDER` | `memory`, `sqlite`, or `postgresql` | required |
| `SHUETL_IDENTITY` | Host-supplied identity mode; currently `host` | required |
| `SHUETL_API_PREFIX` | Mount prefix | `/etl` |
| `SHUETL_ROUTE_PRESET` | Route set; currently `complete` | `complete` |
| `SHUETL_DATABASE_URL` | Existing SQLite file or `postgresql+psycopg` URL | none |
| `SHUETL_PROVIDER_CONNECT_TIMEOUT_SECONDS` | Provider connection timeout | `2.0` |
| `SHUETL_POSTGRESQL_SSLMODE` | `verify-full`, `verify-ca`, `require`, or explicit CI-only `disable` | `verify-full` |

The four required values fail closed when omitted. Constructor arguments take
precedence over environment variables. Names are case-sensitive and only the
listed `SHUETL_*` environment variables are read; dotenv files, secret files,
and structured configuration sources are not consulted. Database URLs are
redacted from representations and diagnostics. The host owns bundle cleanup
and must call `close()` during application shutdown.

SQLite is local-only: use an absolute or relative file URL with the `sqlite` or
`sqlite+pysqlite` driver, and provision the file to migration head
`005_cp1_reference` with ETLantic's upstream tooling before startup. ShuETL
does not create tables or run SQLite migrations.

The PostgreSQL pilot requires the exact `postgresql+psycopg` URL scheme, a
username, host, and database, and PostgreSQL 18.6. The secure default is
`verify-full`; use `disable` only for an isolated local/CI service with an
explicit environment setting. Provision the database with:

```bash
shuetl database upgrade
shuetl doctor --format json
python examples/phase_0_4_postgresql.py
```

The database migration command is the only ShuETL schema-changing operation.
Run it with a migration-capable role, then run the gateway with a role that
does not need schema-change privileges. Backups must include all ETLantic-owned
tables and `etlantic_sqlmodel_schema_version`; credentials, TLS keys, external
artifacts, and pipeline side effects are separate operator inputs.

### PostgreSQL backup and restore verification

Use a transactionally consistent custom-format dump of the provider-owned
database. Native `pg_dump` and `pg_restore` use libpq connection strings
(`postgresql://`), while ShuETL uses its SQLAlchemy URL
(`postgresql+psycopg://`). Keep those inputs separate, and configure the same
TLS policy for both tools. For the isolated local/CI service, set
`PGSSLMODE=disable`; for a verified deployment use `PGSSLMODE=verify-full`
and provide `PGSSLROOTCERT` as required by the server certificate:

```bash
export PGSSLMODE="${PGSSLMODE:-disable}"
export PG_DUMP_DATABASE_URL="postgresql://<user>:<password>@<host>:<port>/<database>"
export PG_RESTORE_DATABASE_URL="postgresql://<user>:<password>@<host>:<port>/<isolated_restore_database>"
export SHUETL_RESTORE_DATABASE_URL="postgresql+psycopg://<user>:<password>@<host>:<port>/<isolated_restore_database>"

pg_dump --format=custom --file=shuetl-0.4.backup "$PG_DUMP_DATABASE_URL"
pg_restore --exit-on-error --dbname="$PG_RESTORE_DATABASE_URL" shuetl-0.4.backup
SHUETL_DATABASE_URL="$SHUETL_RESTORE_DATABASE_URL" shuetl doctor --format json
```

Restore into an isolated database first. Do not admit gateway traffic until
`doctor` reports the qualified server, migration head, required tables, and
provider capabilities, then repeat the restart/idempotency/event probes used
for the pilot. A failed readiness check keeps the restored database out of
traffic; it does not run migrations or repair the restored schema. The dump
must contain the canonical ETLantic tables and
`etlantic_sqlmodel_schema_version`; backups do not contain external artifacts,
credentials, TLS keys, or external side effects.

The memory and SQLite profiles remain development-only. The PostgreSQL profile
is a controlled single-tenant pilot; it is not a multi-tenant, high-availability,
or exactly-once external-effect claim.

```bash
shuetl doctor
shuetl doctor --format json
shuetl --version
```

Doctor checks report `pass`, `warn`, `fail`, or `skip`. The overall report is
`pass` when no required check fails; each failed check includes a safe
remediation message. Exit `0` indicates a passing report, exit `1` indicates a
failed required check, and exit `2` indicates command-line usage or unexpected internal
errors. Text and JSON formats contain the same redacted facts.

To run the local evidence gate:

```bash
uv sync --locked --all-groups --extra test --extra sqlite
uv run python scripts/capture_openapi.py
uv run python scripts/check_release.py
```

## Planned ShuETL capabilities

- mount a curated ETLantic API into an existing FastAPI application;
- create a complete FastAPI application from explicit ETLantic providers;
- validate provider compatibility and production readiness at startup;
- configure ETLantic definition, submission, event, schedule, and persistence
  providers without exposing their implementation details to application code;
- offer safe local-development defaults;
- document and test separate gateway, scheduler, and worker roles for production;
- integrate host authentication/authorization with ETLantic's control-plane
  context and authorizer contracts;
- publish a tested compatibility matrix across FastAPI and ETLantic packages;
- provide optional Hedron and AuthMate composition adapters when those packages
  are available.

## Deployment goal

Local development may use one process and SQLite or in-memory providers.

The production reference uses one installable application/image with separate
supervised roles:

```text
FastAPI gateway
+
ETLantic scheduler/worker process or supported external execution host
+
PostgreSQL
```

The baseline should not require Redis, RabbitMQ, Kafka, an object store, or an
external scheduler. “No required broker” does not imply that long-running ETL
work executes inside the FastAPI gateway process.
