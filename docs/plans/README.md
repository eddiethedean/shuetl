# ShuETL Planning Pack

**ShuETL** *(pronounced “shuttle”)* is a FastAPI-native control plane for building, persisting, scheduling, running, and observing ETLantic pipelines.

ShuETL is intentionally separate from ETLantic core.

- **ETLantic** owns pipeline semantics, contracts, validation, planning, execution, and runtime reports.
- **ShuETL** owns deployment, persistence, scheduling, API exposure, run orchestration, history, result references, and operator-facing control surfaces.

## Planning documents

- [VISION.md](VISION.md) — product purpose, principles, scope, and positioning
- [ARCHITECTURE.md](ARCHITECTURE.md) — system boundaries and component architecture
- [DATA_MODEL.md](DATA_MODEL.md) — persistent entities and versioning model
- [API_DESIGN.md](API_DESIGN.md) — REST API and generated FastAPI surface
- [SCHEDULING_AND_RUNTIME.md](SCHEDULING_AND_RUNTIME.md) — scheduling, jobs, workers, retries, concurrency
- [RESULTS_AND_ARTIFACTS.md](RESULTS_AND_ARTIFACTS.md) — output/result storage strategy
- [SECURITY.md](SECURITY.md) — authentication, authorization, secrets, and isolation
- [MVP.md](MVP.md) — first shippable scope and acceptance criteria
- [ROADMAP.md](ROADMAP.md) — staged delivery plan beyond MVP
- [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) — initial architectural decisions and open ADRs

## Core product statement

> **ShuETL deploys and operates ETLantic pipelines as durable, schedulable FastAPI services.**

The initial deployment model should remain intentionally simple:

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

The architecture must nevertheless preserve a clean path to separating the API, scheduler, and execution workers later without changing the public pipeline/run model.

## Identity and credential integration

ShuETL must support external FastAPI-native identity systems through stable public protocols rather than embedding its own authentication framework.

The reference composition is:

```text
FastAPI
├── Hedron
├── AuthMate
├── ShuETL
└── ETLantic
```

AuthMate is the reference identity/credential implementation, but ShuETL core must remain usable with another compatible provider or without identity integration in explicitly configured local/development scenarios.

See `IDENTITY_INTEGRATION.md`.

## Dependency philosophy

> **Own the contracts; reuse the mechanics.**

ShuETL should use mature libraries for scheduling, retries, persistence, filesystem abstraction, and optional worker execution behind ShuETL-owned models and protocols.

See `DEPENDENCY_STRATEGY.md`.

## Pydantic-first contracts

Pydantic is a first-class architectural dependency, not merely FastAPI request validation.

Public domain models, configuration, discriminated unions, validation, serialization boundaries, and generated JSON Schema should use Pydantic wherever appropriate.

See `PYDANTIC_STRATEGY.md`.

## FastAPI-native architecture

FastAPI is a first-class integration substrate, not merely the HTTP server.

The package should fully use FastAPI routing, dependency injection, security primitives, lifespan, OpenAPI, exception handling, and testing overrides while preserving clear domain boundaries.

See `FASTAPI_STRATEGY.md`.

## SQL-only infrastructure baseline

> **SQL-only infrastructure baseline.**

Core production capability must require only the FastAPI application process and a relational SQL database.

No Redis, RabbitMQ, Kafka, Elasticsearch/OpenSearch, object store, Vault, external scheduler, separate worker service, or other infrastructure may be required for the default production deployment.

Additional services may only extend scale, interoperability, or specialized functionality.

For local development, SQLite should remain sufficient wherever practical.
