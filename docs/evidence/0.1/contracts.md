# Phase 0.1 Public-Contract Inventory

Evidence train: `etlantic==0.51.0`, `etlantic-fastapi==0.51.0`.
Import paths below are public paths documented/exported by the upstream
packages; private implementation modules are excluded.

| Capability | Public symbol | Import path | Distribution | Version | Upstream maturity | First ShuETL consumer | Evidence | Disposition |
|---|---|---|---|---|---|---|---|---|
| Control-plane graph | `ETLanticAPI` | `etlantic_fastapi.ETLanticAPI` | etlantic-fastapi | 0.51.0 | CP1 control plane | 0.1 spike | upstream adapter README/API | consumed |
| Embedded router | `include_router` | `etlantic_fastapi.include_router` | etlantic-fastapi | 0.51.0 | CP1 control plane | 0.1 spike | upstream API and mount test | consumed |
| Dedicated app | `create_app` | `etlantic_fastapi.create_app` | etlantic-fastapi | 0.51.0 | CP1 control plane | OpenAPI comparator | upstream API and factory test | consumed for comparison |
| Problem handler | `install_exception_handlers` | `etlantic_fastapi.install_exception_handlers` | etlantic-fastapi | 0.51.0 | CP1 control plane | 0.1 spike | embedded handler test | consumed |
| Principal adapter | `principal_from_header` | `etlantic_fastapi.principal_from_header` | etlantic-fastapi | 0.51.0 | demo/test adapter | 0.1 spike | upstream auth module | consumed |
| Context adapter | `membership_context_factory` | `etlantic_fastapi.membership_context_factory` | etlantic-fastapi | 0.51.0 | public host adapter | 0.1 spike | upstream auth module | consumed |
| Authorization | `Authorizer` | `etlantic.control_plane.Authorizer` | etlantic | 0.51.0 | public protocol | 0.1 spike graph | upstream control-plane exports | consumed |
| Definition store | `DefinitionRepository` | `etlantic.control_plane.DefinitionRepository` | etlantic | 0.51.0 | public protocol | 0.1 spike graph | upstream control-plane exports | consumed |
| Submission store | `SubmissionStore` | `etlantic.control_plane.SubmissionStore` | etlantic | 0.51.0 | public protocol | 0.1 spike graph | upstream control-plane exports | consumed |
| Event store | `EventStore` | `etlantic.control_plane.EventStore` | etlantic | 0.51.0 | public protocol | 0.1 spike graph | upstream control-plane exports | consumed |
| Memory authorization | `MemoryAuthorizer` | `etlantic.control_plane.MemoryAuthorizer` | etlantic | 0.51.0 | test/local provider | 0.1 spike graph | upstream memory implementation | consumed |
| Memory definitions | `MemoryDefinitionRepository` | `etlantic.control_plane.MemoryDefinitionRepository` | etlantic | 0.51.0 | test/local provider | 0.1 spike graph | upstream memory implementation | consumed |
| Memory submissions | `MemorySubmissionStore` | `etlantic.control_plane.MemorySubmissionStore` | etlantic | 0.51.0 | process-local acceptance | 0.1 spike graph | upstream memory implementation | consumed |
| Memory events | `MemoryEventStore` | `etlantic.control_plane.MemoryEventStore` | etlantic | 0.51.0 | test/local provider | 0.1 spike graph | upstream memory implementation | consumed |
| Identity context | `ControlPlaneContext`, refs, `Principal` | `etlantic.control_plane` | etlantic | 0.51.0 | public models | 0.1 spike setup | upstream control-plane exports | consumed |
| Identity references | `TenantRef`, `WorkspaceRef`, `EnvironmentRef`, `SecurityDomain` | `etlantic.control_plane` | etlantic | 0.51.0 | public models | 0.1 spike setup | upstream control-plane exports | consumed |
| Durable work | `DurableWorkStore`, `MemoryDurableWorkStore` | `etlantic.control_plane` | etlantic | 0.51.0 | reserved provider seam | 0.4 | upstream control-plane exports | reserved |
| Registry | `RegistryProvider`, `RevisionRegistry` | `etlantic.control_plane` | etlantic | 0.51.0 | reserved provider seam | 0.4 | upstream control-plane exports | reserved |
| History | `HistoryStore`, `MemoryHistoryStore` | `etlantic.control_plane` | etlantic | 0.51.0 | reserved provider seam | 0.4 | upstream control-plane exports | reserved |
| Health | `HealthResponse` | `etlantic_fastapi` | etlantic-fastapi | 0.51.0 | public response | 0.2 | upstream adapter exports | reserved |
| Readiness | `ReadyResponse` | `etlantic_fastapi` | etlantic-fastapi | 0.51.0 | public response | 0.2 | upstream adapter exports | reserved |
| Problem Details | `ProblemDetails` | `etlantic.control_plane` | etlantic | 0.51.0 | public error model | 0.2 | upstream control-plane exports | reserved |
| SSE | `sse_streaming_response` | `etlantic_fastapi` | etlantic-fastapi | 0.51.0 | public response helper | 0.2 | upstream adapter exports | reserved |
| HTTP host | `FastAPI`, `TestClient` | `fastapi`, `fastapi.testclient` | fastapi | lock-resolved | framework API | 0.1 spike | FastAPI contract tests | test-only |
| HTTP test transport | `httpx` | `httpx` | httpx | lock-resolved | test dependency | 0.1 tests | adapter test extra | test-only |
| Relational providers | `etlantic-sqlmodel` public package | `etlantic_sqlmodel` | etlantic-sqlmodel | 0.51.0 | provider-owned persistence | 0.4 | provider README/migrations | reserved |
| Provider migrations | `current_version`, `upgrade`, `downgrade` | `etlantic_sqlmodel.migrations` | etlantic-sqlmodel | 0.51.0 | provider-owned migration API | 0.4 | migration package | reserved |
| Scheduler role | `etlantic scheduler` | ETLantic CLI | etlantic | 0.51.0 | upstream runtime role | 0.6 | upstream CLI guidance | reserved |
| Worker role | `etlantic worker` | ETLantic CLI | etlantic | 0.51.0 | upstream runtime role | 0.6 | upstream CLI guidance | reserved |

## Observed upstream behavior

- `include_router()` does not install exception handlers, middleware, or
  lifespan behavior and writes `app.state.etlantic_api`.
- `create_app()` owns a dedicated app, optional problem handlers, and a
  readiness-only lifespan; it does not execute pipeline work.
- CP1 operation IDs include `cp_health`, `cp_ready`, definition operations,
  `cp_submit_run`, run observation, SSE, report, artifact, lineage, schema, and
  reliability operations.
- A valid submission returns `202` only after the memory acceptance store commit.
- Reusing the same scoped idempotency key returns the original acceptance;
  changing its payload returns `409`/`PMCP409`.

These observations are 0.1 evidence, not a promise that later upstream minor
trains retain identical internals.
