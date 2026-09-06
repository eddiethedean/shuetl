# FastAPI Strategy

## Principle

ShuETL should use FastAPI for API composition, DI, lifecycle, OpenAPI, event streaming, and testing while keeping durable pipeline execution outside request/background-task lifetimes.

## Required FastAPI features

### APIRouter
Expose pipeline, schedule, run, artifact, and operational routers as composable modules.

### Dependency injection
Use `Depends`/`Annotated` for:

- SQLModel/SQLAlchemy sessions;
- identity/authorization provider;
- credential resolver;
- executor;
- artifact store;
- metadata publisher;
- settings and request-scoped services.

FastAPI dependency injection is the preferred runtime composition mechanism.

### Security()
Use FastAPI `Security()` where scopes map cleanly to permissions such as `shuetl.pipeline.run`, while preserving service-level resource authorization.

### Router-level dependencies
Use broad router dependencies for authenticated/operator/admin surfaces.

### yield dependencies
Use `yield` dependencies for request-scoped sessions and short-lived external resources.

### Lifespan
FastAPI lifespan owns startup/shutdown of:

- APScheduler timing engine;
- local run-claim/executor loops;
- long-lived provider clients;
- optional worker/backend coordination resources.

Do not use legacy startup-event patterns as the primary design.

### SSE
Provide first-class Server-Sent Events for run updates, e.g.:

```http
GET /runs/{run_id}/events
```

Events may include:

```text
run.claimed
run.started
preflight.completed
drift.detected
artifact.registered
run.succeeded
run.failed
```

Use Pydantic event models and FastAPI's SSE response support.

### OpenAPI webhooks
Use FastAPI OpenAPI webhook declarations to document outbound notifications such as:

```text
run.completed
run.failed
drift.detected
pipeline.health.changed
```

Delivery remains a ShuETL concern; FastAPI documents the contract.

### BackgroundTasks
`BackgroundTasks` may be used only for small post-response work such as notifications, audit writes, or cache invalidation.

It must **not** execute ETLantic pipelines or own durable run execution.

### Exception handling
Use a stable ShuETL error envelope and custom exception handlers.

### OpenAPI
Fully describe normal and error responses, `202 Accepted` run creation, security requirements, SSE endpoints, and webhook contracts.

### Testing
Use dependency overrides for fake executors, identity providers, credential resolvers, artifact stores, publishers, and sessions.

## Do not misuse

- No pipeline execution inside `BackgroundTasks`.
- No request lifetime owns a long-running pipeline.
- Prefer SSE over WebSockets for one-way run-status streams.
- Do not let APScheduler/backend-specific objects leak into API models.
