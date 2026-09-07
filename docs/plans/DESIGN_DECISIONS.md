# ShuETL Initial Design Decisions

This document records initial decisions that should later become formal ADRs.

## D1 — Separate project from ETLantic
ShuETL is a separate package because deployment, scheduling, persistence, APIs, and operational state are control-plane concerns.

## D2 — FastAPI is foundational
ShuETL is FastAPI-native and uses its API, OpenAPI, Pydantic integration, lifecycle, DI, and streaming primitives.

## D3 — Database is authoritative for operational state
Schedules, runs, versions, and result metadata live durably in relational SQL.

## D4 — SQLModel/SQLAlchemy persistence
Prefer SQLModel for normal persisted entities while retaining SQLAlchemy for advanced coordination/query behavior.

## D5 — SQLite local, PostgreSQL production reference
Support both for zero-friction development and reliable production coordination.

## D6 — Pipeline versions are immutable
A run always targets one immutable version for reproducibility and auditability.

## D7 — Scheduling creates runs
The scheduler creates durable Run records; executors execute them.

## D8 — HTTP is asynchronous relative to execution
Run-trigger endpoints return durable run identity rather than waiting for completion.

## D9 — Output data is external by default
The control DB primarily stores bounded results and result metadata/references rather than arbitrary datasets.

## D10 — No arbitrary remote Python execution
MVP does not permit unrestricted uploaded Python execution.

## D11 — ETLantic owns pipeline intelligence
Inference, drift, lineage, health, validation, and execution semantics remain ETLantic responsibilities.

## D12 — Local executor first
Local execution is the baseline; the Executor contract permits optional scale-out implementations.

## D13 — Identity is external and protocol-driven
AuthMate is the reference identity/credential implementation, not a required dependency.

## D14 — Triggering and execution principals are distinct
Scheduled/background work uses explicit service identity rather than implicitly inheriting human credentials.

## D15 — Credentials are references
Pipeline versions store credential references/bindings; secrets resolve just in time.

## D16 — Full-stack compatibility is a release target
CI includes Hedron + AuthMate + ShuETL + ETLantic composition while packages remain independent.

## D18 — Reuse mature operational mechanics
Use maintained libraries such as APScheduler, Tenacity, fastapi-pagination, optional fsspec/UPath, Dramatiq, and Celery behind ShuETL contracts.

## D19 — Pydantic is the ShuETL contract layer
Public control-plane models, configuration, extension payloads, validation, unions, serialization, and JSON Schema are Pydantic-first.

## D20 — Prefer SQLModel for control-plane persistence
SQLModel is default for ordinary entities; SQLAlchemy remains available for locking, coordination, bulk, and advanced queries.

## D21 — Use FastAPI lifecycle and event primitives directly
Use lifespan, SSE, OpenAPI webhooks, DI, and dependency overrides. `BackgroundTasks` never owns durable pipeline execution.

## D22 — SQL-only infrastructure baseline
Default production requires only FastAPI + relational SQL. Brokers, external schedulers, object stores, and worker fleets remain optional.

## D23 — Useful defaults, extensible by contract

**Decision:** major ShuETL control-plane capabilities expose stable typed extension surfaces where practical: selected persistence metadata, run parameters, triggers, executors, artifact providers/types, metadata publishers, policies, events, and lifecycle hooks.

**Constraint:** extensions may not silently bypass durable Run creation/state transitions, immutable version binding, authorization context, idempotency/concurrency policy, or secret-reference semantics.

## D24 — Managed Alembic migrations for supported model extensions

**Decision:** supported SQLModel extensions use ShuETL-managed programmatic Alembic migrations. Safe additive changes may be automatically applied under `auto_migrate="safe"`; destructive/ambiguous changes are blocked for explicit action.

**Constraint:** ShuETL maintains its own migration namespace even in a shared ecosystem database.

## D25 — Extension protocols remain domain-boundary aware

**Decision:** ShuETL extension points cover control-plane behavior only. Pipeline-semantic/inference/execution extension mechanisms belong to ETLantic and should be consumed rather than duplicated.

## Open ADRs

- pipeline serialization;
- run claim/lease semantics;
- exact concurrency/cancellation behavior;
- report retention;
- pipeline activation/version-selection policy;
- exact supported set of extensible SQLModel entities;
- managed migration revision/version strategy;
- safe-vs-unsafe DDL classifier;
- hook ordering/transaction/failure semantics;
- event extension registry/versioning;
- executor and trigger conformance contracts.
