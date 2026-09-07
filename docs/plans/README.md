# ShuETL Planning Pack

**ShuETL** *(pronounced “shuttle”)* is a FastAPI-native control plane for building, persisting, scheduling, running, and observing ETLantic pipelines.

ShuETL is intentionally separate from ETLantic core.

- **ETLantic** owns pipeline semantics, contracts, validation, planning, execution, and runtime reports.
- **ShuETL** owns deployment, persistence, scheduling, API exposure, run orchestration, history, result references, and operator-facing control surfaces.

## Core principles

> **Independent by default, composable by contract.**

> **Own the contracts; reuse the mechanics.**

> **Useful defaults, extensible by contract.**

> **Extensions must not weaken durable execution invariants implicitly.**

ShuETL should adapt to host-application operational/domain needs without forks or monkey-patching while retaining authority over durable Run/Schedule correctness.

## Planning documents

- [VISION.md](VISION.md) — product purpose, principles, scope, and positioning
- [ARCHITECTURE.md](ARCHITECTURE.md) — system boundaries and component architecture
- [DATA_MODEL.md](DATA_MODEL.md) — persistent entities and versioning model
- [EXTENSIBILITY.md](EXTENSIBILITY.md) — model, provider, policy, event, and lifecycle extension contracts
- [API_DESIGN.md](API_DESIGN.md) — REST API and generated FastAPI surface
- [SCHEDULING_AND_RUNTIME.md](SCHEDULING_AND_RUNTIME.md) — scheduling, jobs, workers, retries, concurrency
- [RESULTS_AND_ARTIFACTS.md](RESULTS_AND_ARTIFACTS.md) — output/result storage strategy
- [SECURITY.md](SECURITY.md) — authentication, authorization, secrets, and isolation
- [MVP.md](MVP.md) — first shippable scope and acceptance criteria
- [ROADMAP.md](ROADMAP.md) — staged delivery plan beyond MVP
- [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) — initial architectural decisions and open ADRs

## Core product statement

> **ShuETL deploys and operates ETLantic pipelines as durable, schedulable FastAPI services.**

The initial deployment model remains intentionally simple:

```text
FastAPI
  +
ShuETL control plane
  +
ETLantic runtime
  +
Scheduler
  +
PostgreSQL / SQLite
```

## Identity and credential integration

ShuETL supports external FastAPI-native identity systems through stable public protocols rather than embedding its own authentication framework.

The reference composition is Hedron + AuthMate + ShuETL + ETLantic, but AuthMate remains a reference implementation rather than a core dependency.

See `IDENTITY_INTEGRATION.md`.

## Dependency philosophy

ShuETL uses mature libraries for scheduling, pagination, retries, persistence, filesystem abstraction, and optional worker execution behind ShuETL-owned models and protocols.

See `DEPENDENCY_STRATEGY.md`.

## Pydantic-first contracts

Pydantic is a first-class architectural dependency for public domain models, configuration, extension payloads, discriminated unions, validation, serialization boundaries, and JSON Schema.

See `PYDANTIC_STRATEGY.md`.

## FastAPI-native architecture

FastAPI is the integration substrate: routing, DI, security, lifespan, OpenAPI, exception handling, streaming, and testing overrides.

See `FASTAPI_STRATEGY.md`.

## SQL-only infrastructure baseline

Core production capability requires only the FastAPI application process and a relational SQL database. Redis, brokers, search services, object stores, external schedulers, and separate workers remain optional extensions.

SQLite should remain sufficient for local development wherever practical.

## Extensibility

ShuETL supports controlled extension of selected SQLModel metadata, run parameter models, schedule triggers, executors, artifacts, metadata publishers, policies, typed events, and lifecycle behavior.

Supported persistence extensions pair with ShuETL-managed Alembic migrations so safe additive schema evolution does not require normal Alembic CLI use.

See `EXTENSIBILITY.md`.
