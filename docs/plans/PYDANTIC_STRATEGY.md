# Pydantic Strategy

## Principle

ShuETL should use Pydantic as the canonical public contract layer for pipeline-control metadata and API boundaries.

> **Pydantic is the contract layer; SQLAlchemy is the persistence layer; ETLantic owns pipeline semantics.**

## Use Pydantic for

- Pipeline records exposed by ShuETL;
- PipelineVersion metadata;
- Schedule definitions;
- trigger configurations;
- Run and RunAttempt records;
- artifact metadata;
- executor configuration;
- retry/concurrency/misfire policies;
- identity-provider references;
- API requests/responses;
- event payloads;
- application settings;
- JSON Schema/OpenAPI generation.

## Discriminated unions

Use tagged unions for extensible configuration:

```python
ScheduleTrigger = CronTrigger | IntervalTrigger | DateTrigger
ExecutorConfig = LocalExecutorConfig | DramatiqExecutorConfig | CeleryExecutorConfig
ArtifactLocation = InlineArtifact | FileArtifact | ExternalArtifact
```

Each union should use stable discriminator fields.

## Validation

Use Pydantic validators for cron/trigger payload structure, mutually exclusive fields, version-policy invariants, retry limits, concurrency policy, artifact bounds, parameter schemas, and service-account/credential reference shape.

Do not scatter these checks across route handlers.

## Pipeline parameters

Allow pipeline/run parameters to be described by Pydantic models or JSON Schema-compatible contracts.

ShuETL should validate run parameters before creating/executing a run.

## Settings

Use `pydantic-settings` for database URLs, scheduler configuration, executor settings, artifact backends, API prefixes, and operational limits.

## Serialization

Persist structured snapshots using stable Pydantic serialization where appropriate, while avoiding coupling database schema design to raw serialized model blobs when relational structure is needed.

## TypeAdapter

Use `TypeAdapter` for validating plugin/provider payloads and adapter results without unnecessary wrapper models.

## JSON Schema

Expose Pydantic-generated JSON Schema for schedule configuration, run parameters, executor configuration, and artifact metadata where useful to UIs/clients.

## Boundary with ETLantic

ShuETL must not duplicate ETLantic's Pydantic contract semantics. Where ETLantic already provides authoritative Pydantic-compatible records, ShuETL should consume or wrap them rather than re-implement validation.

## SQLModel relationship

Where a ShuETL entity is both a typed domain record and a relational row, SQLModel should be the first choice.

Do not merge persistence and API models when doing so would leak internal scheduler/executor fields or make versioned public contracts harder to evolve.
