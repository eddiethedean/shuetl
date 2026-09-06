# ShuETL API Design

## Principles

- REST-first;
- FastAPI/OpenAPI-native;
- asynchronous job semantics for pipeline execution;
- stable IDs and slugs;
- no long-running execution tied to a single HTTP request;
- structured error models;
- bounded result payloads.

## Pipelines

```http
POST   /pipelines
GET    /pipelines
GET    /pipelines/{pipeline_id}
PATCH  /pipelines/{pipeline_id}
DELETE /pipelines/{pipeline_id}
```

Deletion should normally archive/disable rather than destroy historical records.

## Pipeline versions

```http
POST /pipelines/{pipeline_id}/versions
GET  /pipelines/{pipeline_id}/versions
GET  /pipelines/{pipeline_id}/versions/{version_id}

POST /pipelines/{pipeline_id}/versions/{version_id}/activate
```

Creation from #119 inference can later be surfaced as an authoring endpoint, but MVP may require explicit registered pipeline definitions.

## Runs

```http
POST /pipelines/{pipeline_id}/runs
GET  /pipelines/{pipeline_id}/runs
GET  /runs/{run_id}
POST /runs/{run_id}/cancel
POST /runs/{run_id}/retry
```

Trigger response:

```json
{
  "id": "run_01...",
  "pipeline_id": "pipe_01...",
  "pipeline_version_id": "pv_01...",
  "status": "PENDING"
}
```

HTTP `202 Accepted` is appropriate when execution is queued.

## Schedules

```http
POST   /pipelines/{pipeline_id}/schedules
GET    /pipelines/{pipeline_id}/schedules
GET    /schedules/{schedule_id}
PATCH  /schedules/{schedule_id}
DELETE /schedules/{schedule_id}

POST /schedules/{schedule_id}/enable
POST /schedules/{schedule_id}/disable
```

## Results

```http
GET /runs/{run_id}/artifacts
GET /runs/{run_id}/artifacts/{artifact_id}
```

Large artifacts should return metadata/reference information rather than stream arbitrary datasets by default.

## ETLantic operational surfaces

As ETLantic exposes these capabilities publicly, ShuETL can project them:

```http
POST /pipelines/{pipeline_id}/preflight
GET  /pipelines/{pipeline_id}/health
GET  /pipelines/{pipeline_id}/drift
GET  /pipelines/{pipeline_id}/lineage
GET  /pipelines/{pipeline_id}/contract
```

ShuETL must consume ETLantic's authoritative records rather than implement parallel analysis.

## API-triggered parameters

A run may accept bounded parameter values:

```json
{
  "parameters": {
    "business_date": "2026-09-06"
  }
}
```

Only parameters declared by the pipeline/version may be accepted.

Unknown parameter names should fail validation.

## Generated pipeline-specific endpoints

Potential later capability:

```http
POST /p/customers/run
GET  /p/customers/status
```

This should be generated from registered pipeline metadata, not hand-authored duplication.

## OpenAPI

FastAPI's generated OpenAPI is a core ShuETL feature.

Pipeline schemas, schedule payloads, run states, and structured error responses should be represented with Pydantic models and automatically documented.

## Identity-aware API behavior

When an external identity provider is installed, ShuETL endpoints should resolve the current principal through provider/FastAPI dependencies and enforce permissions at the service boundary.

Examples:

```text
POST /pipelines/{id}/runs
  requires: shuetl.pipeline.run

PATCH /schedules/{id}
  requires: shuetl.schedule.manage

POST /runs/{id}/cancel
  requires: shuetl.run.cancel
```

The exact authentication mechanism remains external to ShuETL.

Run records should preserve:

```text
triggering_principal_id
execution_service_account_id
```

when those concepts are available.

Neither principal objects nor authorization decisions should be serialized into ETLantic pipeline definitions.

## Pydantic-driven API contracts

FastAPI request/response schemas should be defined once as Pydantic models and reused by Python service/client surfaces where practical.

Run-parameter schemas should be Pydantic/JSON-Schema compatible so invalid parameters fail before durable execution begins.

## Live run events

Add a first-class SSE endpoint:

```http
GET /runs/{run_id}/events
```

using typed Pydantic `RunEvent` records.

## Outbound webhook contracts

Use FastAPI OpenAPI webhooks to describe optional outbound callbacks for run completion/failure and other operational events.

## Response semantics

Manual/API-triggered run creation returns `202 Accepted` with a typed durable run record rather than waiting for execution.
