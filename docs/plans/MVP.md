# ShuETL MVP

## MVP objective

Ship the smallest useful system that lets a developer deploy ETLantic pipelines as a persistent, schedulable FastAPI service.

## Required capabilities

### Pipeline registration

A trusted application can register an ETLantic pipeline.

```python
shuetl.register(
    name="customers",
    pipeline=customer_pipeline,
)
```

Registration persists a versioned definition or authoritative reference.

### Pipeline versioning

- immutable versions;
- one active version;
- historical runs retain their exact version.

### FastAPI integration

Provide a router or application factory.

```python
app.include_router(shuetl.router)
```

### Manual runs

```http
POST /pipelines/{id}/runs
```

creates a durable `PENDING` run and returns `202`.

### Scheduled runs

Support cron and interval schedules stored in the database.

### Scheduler

A single scheduler instance creates due runs.

### Local executor

Execute pending runs within the ShuETL deployment.

### Run history

Expose:

```http
GET /runs
GET /runs/{id}
```

with status and bounded ETLantic reports.

### Result registry

Persist small bounded outputs inline and external result/artifact references.

### SQLite and PostgreSQL

SQLite is the developer default. PostgreSQL is the production reference backend.

## MVP acceptance criteria

- [ ] ShuETL can be mounted into a normal FastAPI app.
- [ ] A trusted code-defined ETLantic pipeline can be registered and persisted.
- [ ] Updating a pipeline creates a new immutable version.
- [ ] A manual HTTP trigger returns a durable run ID before execution completes.
- [ ] The local executor can claim and execute a pending run.
- [ ] Cron and interval schedules survive application restarts.
- [ ] Duplicate scheduled runs are prevented for the same schedule occurrence.
- [ ] Run status survives application restart.
- [ ] Historical runs preserve the pipeline version used.
- [ ] ETLantic run reports can be persisted in bounded form.
- [ ] Large pipeline outputs are represented by artifact references rather than forced into the control DB.
- [ ] SQLite works locally.
- [ ] PostgreSQL is covered by integration tests.
- [ ] OpenAPI documents all public endpoints/models.
- [ ] No arbitrary Python source can be uploaded and executed through the API.

## External identity compatibility requirement

- [ ] Stable authorization, service-account, credential-resolution, and audit protocols exist.
- [ ] ShuETL can run without AuthMate in explicitly configured local/development mode.
- [ ] AuthMate plugs in without ShuETL importing AuthMate internals.
- [ ] Manual runs preserve the triggering principal when supplied.
- [ ] Scheduled runs execute as an explicit service account when identity integration is enabled.
- [ ] Credential references are persisted; resolved secrets are never stored in pipeline definitions.
- [ ] Loss of service-account/credential authorization blocks a run before unsafe external I/O.
- [ ] A reference integration test covers FastAPI + Hedron + AuthMate + ShuETL + ETLantic.

## Dependency requirements

- [ ] APScheduler 3.11.x provides trigger/timing mechanics.
- [ ] ShuETL's database remains authoritative for Schedule/Run state.
- [ ] Tenacity handles bounded retry/backoff mechanics.
- [ ] Distributed execution is not required for MVP.
- [ ] Artifact filesystem support is optional behind fsspec/UPath.

## Pydantic requirements

- [ ] Schedule triggers use discriminated Pydantic unions.
- [ ] Run/executor/artifact configuration uses typed Pydantic contracts.
- [ ] Run parameters are validated through Pydantic-compatible schemas.
- [ ] `pydantic-settings` owns operational configuration.
- [ ] Public API models never expose SQLAlchemy/APScheduler/backend-specific types.
- [ ] Generated JSON Schema/OpenAPI derives from the same public contracts.

## SQLModel requirements

- [ ] Core persisted control-plane entities use SQLModel where appropriate.
- [ ] Run-claiming and scheduler-lock semantics may use direct SQLAlchemy.
- [ ] Public API/config models remain separate when persistence fields should not be exposed.

## FastAPI requirements

- [ ] FastAPI lifespan starts/stops scheduler/local executor resources.
- [ ] DI composes sessions, identity, credentials, executor, artifact, and publisher services.
- [ ] Manual run creation returns `202 Accepted`.
- [ ] `BackgroundTasks` is not used for pipeline execution.
- [ ] Typed SSE run-event streaming is supported or explicitly scheduled for the first operational release.
- [ ] Outbound webhook contracts are documented through OpenAPI where enabled.
- [ ] Stable custom exception handlers/error envelopes exist.
- [ ] Dependency overrides support full integration tests.

## SQL-only infrastructure acceptance

- [ ] ShuETL core production functionality requires only FastAPI + relational SQL.
- [ ] SQLite supports local development.
- [ ] PostgreSQL is the production reference backend.
- [ ] Scheduler runs in-process.
- [ ] LocalExecutor runs without Redis/RabbitMQ/Celery/Dramatiq.
- [ ] SQL is authoritative for schedules, runs, coordination, and history.
- [ ] Object storage is not required.
- [ ] Distributed workers/brokers remain optional scale-out adapters.
