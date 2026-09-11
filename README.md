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

ShuETL 0.1.0 is [published on PyPI](https://pypi.org/project/shuetl/0.1.0/).
This release is the 0.1 boundary-proof implementation phase: the package is
intentionally inert while the published ETLantic 0.51.0 composition seam is
verified; the usable `ShuETL` facade begins in 0.2.

The complete design pack is in [`docs/plans/`](docs/plans/README.md).

The implementation contract and release gate are in
[`docs/plans/PHASE_0_1_EXECUTION.md`](docs/plans/PHASE_0_1_EXECUTION.md).

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
