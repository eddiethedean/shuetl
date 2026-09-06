# ShuETL

**ShuETL** *(pronounced “shuttle”)* is a FastAPI-native control plane for deploying and operating ETLantic pipelines.

> **ShuETL deploys and operates ETLantic pipelines as durable, schedulable FastAPI services.**

ShuETL is intentionally separate from ETLantic core:

- **ETLantic** owns pipeline semantics, contracts, validation, planning, execution, inference, drift, lineage, and runtime reports.
- **ShuETL** owns persistence, versioning, scheduling, API exposure, durable runs, operational history, result references, and deployment concerns.

## Architecture principles

- **Independent by default, composable by contract.**
- **Own the contracts; reuse the mechanics.**
- **Pydantic-first public contracts.**
- **SQLModel where it cleanly fits; SQLAlchemy for advanced persistence mechanics.**
- **FastAPI-native composition and lifecycle.**
- **SQL-only infrastructure baseline** — core production functionality requires only the FastAPI application process and a relational SQL database.

The reference ecosystem can compose as one FastAPI application:

```text
FastAPI
├── Hedron
├── AuthMate
├── ShuETL
└── ETLantic
```

without making Hedron or AuthMate core dependencies of ShuETL.

## Status

ShuETL is currently in the architecture and planning phase.

The complete design pack is in [`docs/plans/`](docs/plans/README.md).

## Planned capabilities

- register and version ETLantic pipelines;
- expose pipeline operations through FastAPI;
- create durable manual/API runs;
- persist schedules in SQL;
- run an in-process scheduler and local executor by default;
- preserve exact pipeline versions for historical runs;
- expose run history, results, artifacts, health, drift, lineage, and preflight information;
- integrate with external identity/credential providers through stable protocols;
- provide SSE run-event streams and OpenAPI webhook contracts;
- scale later to optional distributed execution without changing the public run model.

## Default deployment goal

```text
FastAPI application
+
PostgreSQL
```

SQLite should remain sufficient for local development.

No Redis, RabbitMQ, Kafka, external scheduler, object store, or separate worker service is required for core functionality.
