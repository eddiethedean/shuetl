# ShuETL Roadmap

## Phase 0 — Architecture and contracts

Freeze terminology, pipeline/version/run/schedule models, FastAPI integration contract, database schema, serialization strategy, scheduler semantics, run state machine, and security boundary.

## Phase 1 — MVP control plane

Deliver FastAPI router/app integration, persistence/migrations, pipeline registry, immutable versions, manual run creation, local executor, cron/interval schedules, run history, result artifact registry, and SQLite/PostgreSQL support.

## Phase 2 — Operational usability

Add pagination/filtering, diagnostics, retry policies, cancellation requests, schedule misfire/concurrency policy, basic RBAC integration, CLI, and health endpoints.

## Phase 3 — ETLantic intelligence integration

Integrate ETLantic capabilities as they stabilize: pipeline inference authoring, contract/schema drift, preflight/readiness, field lineage, remediation suggestions, pipeline health, and contract explorer. ETLantic remains authoritative.

## Phase 4 — Distributed execution

Introduce a stable execution abstraction:

```text
LocalExecutor
QueueExecutor
ExternalExecutor
```

Potential optional backends include database queue, Dramatiq, Celery, Temporal, Kubernetes Job, and cloud batch services. Public run semantics do not change.

## Phase 5 — Artifact backends

Add optional filesystem, S3, Azure Blob, GCS, and database/table reference adapters.

## Phase 6 — Event-driven triggers

Support webhook, file/object arrival, database notification, message queue event, and external callback triggers. All create normal ShuETL runs.

## Phase 7 — Web operations console

Potential UI surfaces include Pipelines, Versions, Schedules, Runs, Results, Health, Drift, Lineage, and Contract Explorer.

## Phase 8 — Platform capabilities

Potential workspaces, multi-tenancy, audit log, approvals/promotion, environment promotion, secrets integrations, organization policy, notifications, and pipeline templates.

## Identity and credential integration track

Define provider-neutral protocols for current principal references, authorization, service accounts, credential resolution, and audit events. Add an AuthMate reference adapter and later expose execution identity, credential-binding health, revoked/expired credential diagnostics, service-account status, permission-aware controls, and audit correlation.

## Long-term positioning

ShuETL should remain **the lightweight FastAPI-native control plane for ETLantic**, not a general-purpose workflow orchestrator.
