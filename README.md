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

ShuETL 0.3.0 is the current development release. It provides a typed FastAPI facade for local development and
automated tests. It accepts a prebuilt
`etlantic_fastapi.ETLanticAPI`; the 0.3 local bundle additionally wires exact
upstream memory providers and an opt-in, pre-provisioned SQLite profile.
Both profiles are development-only and are not a production durability claim.

The complete design pack is in [`docs/plans/`](docs/plans/README.md).

The implementation contracts are in
[`docs/plans/PHASE_0_1_EXECUTION.md`](docs/plans/PHASE_0_1_EXECUTION.md) and
[`docs/plans/PHASE_0_2_EXECUTION.md`](docs/plans/PHASE_0_2_EXECUTION.md), with
the Phase 0.3 contract in
[`docs/plans/PHASE_0_3_EXECUTION.md`](docs/plans/PHASE_0_3_EXECUTION.md).

## Install

```bash
python -m pip install "shuetl==0.3.0"
# Optional pre-provisioned SQLite provider
python -m pip install "shuetl[sqlite]==0.3.0"
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

Phase 0.3 adds immutable `ShuETLSettings`, `LocalProviderBundle`, and the
redacted `shuetl doctor` preflight CLI. Settings use `SHUETL_*` environment
variables; constructor values override the environment. SQLite files must be
provisioned and migrated by upstream tooling before the bundle is created.
ShuETL never migrates, creates tables, executes pipelines, or accepts anonymous
identity. The host supplies the authorizer, context factory, principal
dependency, and closes the bundle.

### Settings contract

The supported settings are:

| Environment variable | Meaning | Default |
| --- | --- | --- |
| `SHUETL_PROFILE` | Deployment profile; currently `local` | required |
| `SHUETL_ROLE` | Runtime role; currently `gateway` | required |
| `SHUETL_PROVIDER` | `memory` or `sqlite` | required |
| `SHUETL_IDENTITY` | Host-supplied identity mode; currently `host` | required |
| `SHUETL_API_PREFIX` | Mount prefix | `/etl` |
| `SHUETL_ROUTE_PRESET` | Route set; currently `complete` | `complete` |
| `SHUETL_DATABASE_URL` | Existing local SQLite file URL | none |
| `SHUETL_PROVIDER_CONNECT_TIMEOUT_SECONDS` | SQLite connection timeout | `2.0` |

The four required values fail closed when omitted. Constructor arguments take
precedence over environment variables. Names are case-sensitive and only the
listed `SHUETL_*` environment variables are read; dotenv files, secret files,
and structured configuration sources are not consulted. Database URLs are
redacted from representations and diagnostics. The host owns bundle cleanup
and must call `close()` during application shutdown.

SQLite is local-only: use an absolute or relative file URL with the `sqlite` or
`sqlite+pysqlite` driver, and provision the file to migration head
`004_schedules_0_47` with ETLantic's upstream tooling before startup. ShuETL
does not create tables or run migrations. The local memory and SQLite profiles
are development-only; production durability, authentication, scheduling, and
worker operation remain outside this package.

```bash
shuetl doctor
shuetl doctor --format json
shuetl --version
```

To run the local evidence gate:

```bash
uv sync --locked --all-groups --extra test
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
