# ShuETL Vision

## Purpose

ShuETL makes ETLantic pipelines easy to deploy and operate without requiring a separate orchestration platform.

A user should be able to create/register an ETLantic pipeline, persist/version it, expose it through FastAPI, schedule recurring runs, trigger runs through an API, inspect status/history/results, surface ETLantic health/drift/lineage/preflight information, and deploy the system as a single application for small and medium workloads.

## Product boundary

ETLantic owns pipeline semantics, contracts, validation, inference authoring, drift classification, planning, execution, and run reports.

ShuETL owns persistence, versioning, scheduling, REST APIs, run orchestration, result references, operational history, identity integration, and deployment.

ShuETL consumes ETLantic public APIs/records instead of duplicating them.

## Product principles

### Single-service first

A useful production deployment requires only ShuETL, ETLantic, FastAPI, and a relational database. Distributed infrastructure remains optional.

### Durable state over in-memory state

Pipelines, versions, schedules, and runs are durably represented in SQL and survive application restarts.

### Pipelines are versioned artifacts

Historical runs retain the exact immutable version that produced them.

### HTTP requests do not own long-running execution

Run triggers create durable run records and return quickly; execution continues independently of the request.

### Results are not synonymous with database rows

ShuETL stores run metadata/reports, small bounded outputs where appropriate, and references to large external artifacts rather than assuming all output belongs in the control database.

### FastAPI is the service surface

FastAPI provides routing, OpenAPI, dependency injection, security integration, lifecycle hooks, and extension points.

### ETLantic remains authoritative

ShuETL schedules and operates pipelines but does not reinterpret ETLantic pipeline semantics at runtime.

### Progressive operational complexity

The same public model should support an MVP of FastAPI + scheduler + local executor, later SQL-backed/multi-worker operation, and optional external execution backends without changing public run semantics.

## Primary users

Developers create/register pipelines, operators schedule/monitor/investigate them, and application integrators trigger and consume pipelines through HTTP.

## Non-goals for MVP

- competing with Airflow/Prefect/Temporal feature-for-feature;
- visual DAG authoring;
- large distributed task execution;
- arbitrary user-code upload;
- storing all transformed datasets in the control database;
- automatic semantic mutation during scheduled runs.
