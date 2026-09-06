# ShuETL Initial Design Decisions

This document records initial decisions that should later become formal ADRs.

## D1 — Separate project from ETLantic

**Decision:** ShuETL is a separate package.

**Reason:** Deployment, scheduling, persistence, APIs, and operational state are control-plane concerns, not core pipeline semantics.

## D2 — FastAPI is foundational

**Decision:** ShuETL is built as a FastAPI-native package rather than a generic server abstraction.

**Reason:** FastAPI provides the API surface, OpenAPI, Pydantic integration, lifecycle hooks, and a familiar deployment model.

## D3 — Database is authoritative for operational state

**Decision:** schedules, runs, versions, and result metadata live durably in a relational database.

**Reason:** process-local schedulers and in-memory run state do not survive restart or scale safely.

## D4 — SQLAlchemy 2.x

**Decision:** use SQLAlchemy 2.x for persistence.

**Reason:** robust SQLite/PostgreSQL support, mature migrations/tooling, and broad deployment compatibility.

## D5 — SQLite local, PostgreSQL production reference

**Decision:** support both.

**Reason:** zero-friction development plus reliable multi-process production coordination.

## D6 — Pipeline versions are immutable

**Decision:** a run always targets one immutable version.

**Reason:** reproducibility, auditability, safe schedule behavior, and drift reconciliation.

## D7 — Scheduling creates runs

**Decision:** scheduler creates durable `Run` records; executor executes them.

**Reason:** separates timing from execution and enables future distributed workers.

## D8 — HTTP is asynchronous relative to execution

**Decision:** run-trigger endpoints return a run ID rather than waiting for completion.

**Reason:** ETL jobs may be long-running and must survive client disconnects.

## D9 — Output data is external by default

**Decision:** the control DB primarily stores result metadata/references, not arbitrary datasets.

**Reason:** pipeline outputs can be too large or belong in destination systems/object stores.

## D10 — No arbitrary remote Python execution

**Decision:** MVP does not allow API clients to upload arbitrary Python code as pipelines.

**Reason:** pipeline authoring can become remote code execution if not constrained.

## D11 — ETLantic owns pipeline intelligence

**Decision:** ShuETL consumes ETLantic inference, drift, lineage, health, and preflight APIs.

**Reason:** prevent duplicated semantic engines and divergent behavior.

## D12 — Local executor first, abstraction later

**Decision:** MVP uses local execution but models runs independently of executor implementation.

**Reason:** keep deployment simple while preserving a path to distributed execution.

## Open ADRs

The following require explicit design decisions before implementation:

1. **Pipeline serialization**
   - declarative ETLantic plan;
   - importable Python reference;
   - packaged artifact;
   - combination.
2. **Scheduler implementation** — APScheduler-backed polling, database due-run loop, or hybrid.
3. **Run claim semantics** — row lock, `SKIP LOCKED`, lease table, or advisory lock.
4. **Concurrency policy** — exact MVP behavior for duplicate/overlapping runs.
5. **Cancellation semantics** — cooperative only vs process isolation.
6. **Authentication integration** — dependency hook, built-in JWT option, or both.
7. **Report retention** — DB JSON size limits and external report artifact option.
8. **Pipeline activation** — immediate, transactional, or optional preflight gate.
9. **Schedule version policy** — active, pinned, or both.
10. **Package/API naming** — `ShuETL`, import `shuetl`, CLI `shuetl`.

## D13 — Identity is external and protocol-driven

**Decision:** ShuETL does not implement a general-purpose authentication/user-management system.

**Reason:** identity, authorization, service accounts, and credential management are independently reusable FastAPI concerns.

AuthMate is the reference implementation, not a core dependency.

## D14 — Triggering principal and execution principal are distinct

**Decision:** ShuETL distinguishes the human/service principal that requests a run from the service account that executes the pipeline.

**Reason:** scheduled/background workloads require stable machine identity and must not implicitly inherit human credentials.

## D15 — Credentials are references

**Decision:** pipeline versions store credential references/bindings only.

**Reason:** resolved secrets belong to the external credential provider and should be resolved just in time.

## D16 — Full-stack compatibility is a release target

**Decision:** CI must include a reference composition of Hedron + AuthMate + ShuETL + ETLantic in one FastAPI app.

**Reason:** the combined stack is a supported product surface even though the packages remain independently deployable.

## D18 — Reuse mature operational mechanics

**Decision:** ShuETL delegates commodity scheduling/retry/filesystem/worker mechanics to maintained libraries behind ShuETL-owned contracts.

Initial choices: APScheduler 3.11.x, Tenacity, optional fsspec + universal-pathlib, optional Dramatiq, and optional Celery.

## D19 — Pydantic is the ShuETL contract layer

**Decision:** ShuETL uses Pydantic for public control-plane models, configuration, validation, discriminated unions, serialization boundaries, and JSON Schema generation.

**Reason:** This maximizes reuse of FastAPI's native modeling system and avoids duplicate validation across HTTP, scheduler, and Python APIs.

## D20 — Prefer SQLModel for control-plane persistence

**Decision:** ShuETL uses SQLModel as the default persistence modeling layer for normal entities while retaining direct SQLAlchemy for concurrency/locking/advanced queries.

**Reason:** This reduces duplicate Pydantic and ORM models without sacrificing the lower-level database controls required by a durable scheduler/executor.

## D21 — Use FastAPI lifecycle and event primitives directly

**Decision:** ShuETL uses FastAPI lifespan for service lifecycle, SSE for one-way run-event streaming, OpenAPI webhooks for callback contracts, and dependency overrides for testing.

**Decision:** FastAPI `BackgroundTasks` is never the durable pipeline execution mechanism.

**Reason:** FastAPI already provides these application primitives, while ShuETL's Run model must remain durable and independent of request lifetime.

## D22 — SQL-only infrastructure baseline

**Decision:** ShuETL's default production deployment requires only the FastAPI application process and a relational SQL database.

**Reason:** scheduling and durable execution should remain operationally lightweight. Brokers, external schedulers, object stores, and worker fleets are optional scalability features, not baseline requirements.
