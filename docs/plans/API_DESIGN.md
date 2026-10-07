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

ShuETL's target has three consumption styles. Mounting and application creation
exist in 0.4; headless composition is governed by the planned
[0.5 execution contract](PHASE_0_5_EXECUTION.md).

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

### Headless host application

A host may embed ShuETL as an ETL backend without exposing ETLantic's HTTP API
and without making requests back to its own server. ShuETL must make the
configured public ETLantic application services available to the host using
supported upstream contracts. The HTTP API remains optional in this mode.

The standard headless surface accepts canonical specifications/parameters and
backend commands and returns canonical results. ShuETL supplies the supported
backend profile; apps do not construct its runtime provider graph or sequence
preparation calls. Existing provider injection remains an advanced interface.
Ergonomic Python delegation to public ETLantic commands is permitted without
new ShuETL domain models, fingerprints or state semantics. Required missing
public services must be added upstream before support is claimed.

Each headless invocation supplies its own trusted upstream context and passes
the same service-level authorization as HTTP. Exposing a raw store or router
closure does not meet this contract. Public service names and lifecycle are
frozen after installed-package qualification; headless use must not construct
a synthetic HTTP request or share mutable identity between concurrent calls.

The [specification contract](SPECIFICATION_CONTRACT.md) defines the required
canonical authoring schema, application-controlled choices and backend-owned
outputs. Schema/capability discovery must support typed editor binding and
diagnostics without duplicating an ETL rule engine in the app.

## Complete developer control

[DEVELOPER_CONTROL.md](DEVELOPER_CONTROL.md) requires full public control of
each qualified profile. Convenience methods must preserve a typed canonical
specification and documented service access path for provider-specific settings,
programmatic authoring, advanced queries and commands absent from presets.
An upstream Python service need not have an HTTP route to be available headlessly.

Expose permitted per-run overrides and their effective configuration without
mutating saved definitions. Preserve engine/provider choices, execution hints,
run action discovery, command preconditions, attempt/new-run lineage and
explicit unavailable-action reasons. Apps may invoke optional staged planning,
preflight and approval using qualified immutable references; the backend still
owns every admission check. Direct submission remains complete by itself.

External triggers and business workflows may issue the same commands and
consume canonical outcomes. Private backend extensions reuse public upstream
contracts without changes to ShuETL routes/models or a mandatory core release.

## Exposed ETLantic capabilities

Depending on configured providers, the mounted API may expose ETLantic
operations for:

- definitions and registry revisions;
- validation and planning;
- durable run submission and cancellation requests;
- complete qualified run controls, including failed-work retry, deliberate
  rerun, and supported replay/backfill/pause/resume/repair commands;
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

Host-specific HTTP endpoints, HTML forms, and presentation summaries remain in
the host. They call public ETLantic services through the headless integration
surface and project upstream records without becoming a second ETL control
plane.

## Durable submission

The application makes one logical submission request with a canonical
specification or revision reference, parameters, trusted context and an
idempotency token. The public backend service owns normalization/fingerprinting,
revision binding, planning, required preflight, admission and acceptance.
Optional prior validation or preview does not satisfy or bypass those checks.
Long preparation may expose an upstream operation identity for observation;
the host does not coordinate or persist the preparation sequence.

ShuETL preserves upstream submission behavior:

- the API returns `202 Accepted` only after durable acceptance;
- callers use the upstream idempotency mechanism;
- retries of the same accepted request do not create a second logical
  submission;
- a client disconnect does not own execution lifetime;
- the response is an ETLantic submission/run record, not a ShuETL wrapper.

For an in-process host, the HTTP response is optional; the durable-accept,
scope, idempotency, and canonical-identity rules still apply unchanged.

After authorization, an accepted-key lookup precedes repeated live preflight.
An identical request returns its existing record after response loss; a changed
fingerprint conflicts. New work binds preflight and acceptance to an immutable
revision/resource selection. Failed preflight creates no pipeline submission;
upstream provider-action evidence may still be recorded. Preflight is not a
reservation of remote state, so execution rechecks time-sensitive conditions.

Catalog/test/preflight and sample preview have explicit authorized action
contracts and deadlines outside the gateway. Provisioning a destination is a
separate mutation and must never occur as a side effect of validation or
read-only preflight. See [HOST_INTEGRATION.md](HOST_INTEGRATION.md).

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

Headless conformance separately proves a host can exercise the supported
validation/planning, preflight, submission, cancellation, and result-read
contracts without an HTTP listener or HTTP loopback.
The coverage inventory also compares every qualified caller-facing field,
command and query with ShuETL exposure, including provider-specific settings,
per-run overrides and direct public service access beyond convenience methods.

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
