# ShuETL API Composition

## Principle

ShuETL mounts and configures ETLantic's authoritative FastAPI surface. It does
not maintain parallel endpoint implementations or duplicate request/response
models.

`etlantic-fastapi` owns the normative:

- route paths and operation IDs;
- HTTP methods and status codes;
- request, response, and problem-detail schemas;
- durable-accept semantics;
- authorization ordering and non-enumeration behavior;
- idempotency and optimistic-concurrency headers;
- SSE formatting, cursors, replay, and retention-gap behavior.

ShuETL owns how that router is composed into a host application.

## Public composition surfaces

ShuETL should provide two integration styles.

### Mount into an existing application

```python
app = FastAPI(lifespan=integration.lifespan)
integration.mount(app, prefix="/etl")
```

Mounting must:

- preserve ETLantic operation IDs and schema identities;
- support a configurable path prefix without rewriting route meaning;
- compose with, rather than replace, host middleware and lifespan behavior;
- require explicit principal and context dependencies for protected profiles;
- install or document required exception handlers;
- avoid duplicate route registration.

### Create an application

```python
app = integration.create_app()
```

The factory is a convenience for dedicated deployments. It should produce the
same ETLantic API contract as mounting into an existing host.

## Exposed ETLantic capabilities

Depending on configured providers, the mounted API may expose ETLantic
operations for:

- definitions and registry revisions;
- validation and planning;
- durable run submission and cancellation requests;
- submission/run status, attempts, and recovery information;
- schedules and firing history;
- events and resumable SSE;
- reports, diagnostics, and artifact metadata;
- readiness and liveness;
- policy, approval, audit, or other optional control-plane surfaces.

This list is capability-oriented, not a promise that ShuETL implements each
operation. An endpoint is exposed only when the required ETLantic contract and
provider are present and supported by the selected ShuETL compatibility profile.

## No parallel convenience API

ShuETL must not add aliases such as `/pipelines/{id}/runs` when ETLantic's
authoritative route uses a different resource vocabulary. Convenience belongs in
Python configuration or a generated client, not a second HTTP contract.

Pipeline-specific generated routes are out of scope unless ETLantic defines a
canonical route-generation contract.

## Durable submission

ShuETL preserves upstream submission behavior:

- the API returns `202 Accepted` only after durable acceptance;
- callers use the upstream idempotency mechanism;
- retries of the same accepted request do not create a second logical
  submission;
- a client disconnect does not own execution lifetime;
- the response is an ETLantic submission/run record, not a ShuETL wrapper.

## Authorization

The host-authenticated principal is adapted into ETLantic's control-plane
context. The authoritative ETLantic authorizer and route/service checks decide
access.

ShuETL must preserve:

- authorization before existence-sensitive lookup;
- resource-scoped actions;
- tenant/workspace/environment scope where configured;
- consistent `403` versus opaque `404` behavior;
- authorization of list filters, pagination, event streams, and artifact
  metadata;
- fail-closed behavior when required policy services are unavailable.

## OpenAPI

The generated OpenAPI document must come from the mounted
`etlantic-fastapi` routes and models.

ShuETL tests:

- prefix-safe route generation;
- stable operation IDs;
- normal and error responses;
- security requirements;
- `202 Accepted` submission;
- SSE media types and documented resume inputs;
- absence of ShuETL shadow schemas for ETLantic records.

ShuETL-specific configuration models do not need to become public HTTP schemas.

## Streaming

When ETLantic SSE support is configured, ShuETL exposes it unchanged.

ShuETL is responsible for deployment guidance covering proxy buffering,
keep-alives, connection limits, graceful shutdown, and authentication lifetime.
It does not define another event envelope or cursor.

## Health and readiness

Use the authoritative adapter's liveness and readiness surfaces where available.
ShuETL contributes provider checks and deployment diagnostics through supported
extension hooks rather than creating conflicting health endpoints.

Readiness should fail when a required provider, schema revision, execution role,
or compatibility constraint is unavailable. Liveness must not claim that runs
can be accepted.

## API compatibility

ShuETL publishes:

- the ETLantic and `etlantic-fastapi` release range it supports;
- any mounted-route selection profile;
- a checked OpenAPI snapshot for each supported release train;
- upgrade notes for intentional upstream API changes.

ShuETL does not promise stability beyond the upstream contract it pins and
tests.
