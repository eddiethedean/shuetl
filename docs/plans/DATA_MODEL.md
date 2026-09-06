# ShuETL Data Model

## Design goals

The persistent model must support:

- immutable pipeline versions;
- recurring schedules;
- durable execution history;
- retries and concurrency;
- ETLantic report persistence;
- artifact/result references;
- future multi-worker execution.

## Pipeline

Represents a logical named pipeline.

```text
Pipeline
- id
- name
- slug
- description
- enabled
- active_version_id
- created_at
- updated_at
```

`slug` should be unique and suitable for URLs.

Example:

```text
customers-daily
```

## PipelineVersion

Represents an immutable pipeline definition.

```text
PipelineVersion
- id
- pipeline_id
- version
- definition_format
- definition_payload
- definition_fingerprint
- etlantic_version
- created_at
- created_by
- status
```

Possible status:

```text
DRAFT
ACTIVE
SUPERSEDED
ARCHIVED
```

Once a version has been executed, its semantic definition must not be edited in place.

## Schedule

```text
Schedule
- id
- pipeline_id
- name
- enabled
- trigger_type
- trigger_definition
- timezone
- version_policy
- pinned_version_id
- concurrency_policy
- misfire_policy
- parameters
- next_run_at
- last_run_at
- created_at
- updated_at
```

`trigger_definition` may be structured JSON rather than a raw cron string so multiple trigger types remain possible.

## Run

```text
Run
- id
- pipeline_id
- pipeline_version_id
- schedule_id
- trigger_type
- status
- attempt
- parameters
- created_at
- queued_at
- claimed_at
- started_at
- completed_at
- heartbeat_at
- executor_id
- error_code
- error_summary
- run_report
```

Trigger types:

```text
MANUAL
SCHEDULED
API
RETRY
SYSTEM
```

## RunAttempt

Optional separate table if retry history needs first-class persistence.

```text
RunAttempt
- id
- run_id
- attempt_number
- status
- executor_id
- started_at
- completed_at
- error_code
- error_summary
- execution_report
```

For MVP, attempt fields may initially live on `Run` if retries are simple.

## ResultArtifact

```text
ResultArtifact
- id
- run_id
- name
- kind
- storage_type
- uri
- media_type
- inline_payload
- size_bytes
- checksum
- metadata
- created_at
```

`inline_payload` must be bounded.

Storage types may include:

```text
INLINE
FILE
OBJECT_STORE
DATABASE
TABLE
EXTERNAL_URI
```

## RunEvent

Optional but useful for event-style history.

```text
RunEvent
- id
- run_id
- sequence
- event_type
- payload
- created_at
```

Examples:

```text
run.created
run.claimed
run.started
preflight.completed
drift.detected
artifact.registered
run.succeeded
run.failed
```

## Concurrency lease

A durable lease can support scheduler and worker coordination.

```text
Lease
- key
- owner_id
- acquired_at
- expires_at
- heartbeat_at
```

Potential keys:

```text
scheduler-leader
pipeline:{pipeline_id}:exclusive-run
run:{run_id}:claim
```

PostgreSQL advisory locks may be used instead for some production paths.

## Versioning invariant

Every run must point to one immutable `PipelineVersion`.

Never resolve a historical run through the pipeline's current active version.

## Identity and credential references

The data model should support provider-neutral references without owning identity tables.

### PipelineVersion additions

Potential fields:

```text
execution_service_account_id
credential_bindings
```

`credential_bindings` should reference credential IDs or logical bindings, never resolved secret values.

### Run additions

Potential fields:

```text
triggering_principal_id
execution_service_account_id
security_context_version
```

These are references/audit metadata, not foreign keys that require AuthMate tables to be present.

This preserves the ability to use AuthMate, another provider, or a remote identity service.

## Pydantic representation

Every externally visible persistent entity should have an explicit Pydantic representation separate from its SQLAlchemy persistence model.

This includes Pipeline, PipelineVersion, Schedule, Run, RunAttempt, ResultArtifact, and security-reference records.

Use discriminated Pydantic unions for schedule triggers, artifact locations, and executor configuration.

## SQLModel persistence

Prefer SQLModel for ordinary persisted ShuETL entities:

```text
Pipeline
PipelineVersion
Schedule
Run
RunAttempt
ResultArtifact
RunEvent
```

Use separate Pydantic-only models where the public API/configuration shape differs materially from the persistence shape.

Use direct SQLAlchemy for:

- durable run claiming;
- row locking / `SKIP LOCKED`;
- advisory locks;
- scheduler leader election;
- bulk state transitions;
- optimized history queries.
