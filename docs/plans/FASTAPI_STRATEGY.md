# FastAPI Strategy

## Principle

FastAPI is one of ShuETL's application integration substrates.
`etlantic-fastapi` remains the authoritative implementation of ETLantic HTTP
semantics. Headless host composition is also supported and uses public
ETLantic application services without requiring an HTTP listener.

## Composition, not route duplication

ShuETL uses the supported `etlantic-fastapi` application/router APIs. It does
not copy route functions or build alternate Pydantic request/response models.

ShuETL may:

- mount the router under a configurable prefix;
- select a documented upstream route preset;
- inject supported provider instances;
- connect host principal/context dependencies;
- install or document required exception handlers;
- compose readiness checks and lifespan resources.

## Existing application mode

```python
app = FastAPI(lifespan=integration.lifespan)
integration.mount(app)
```

Requirements:

- do not replace an existing host lifespan silently;
- do not install duplicate middleware or exception handlers;
- preserve host application state outside the ShuETL namespace;
- detect conflicting prefixes or operation IDs;
- support FastAPI dependency overrides in tests.

The implementation should offer a documented lifespan-composition helper rather
than requiring applications to copy internal startup logic.

## Dedicated application mode

```python
app = integration.create_app()
```

The factory owns the whole FastAPI application and may install recommended
handlers and lifespan behavior. Its ETLantic routes and OpenAPI models must match
existing-application mode.

## Dependency injection

FastAPI dependencies connect:

- host-authenticated principal to ETLantic control-plane context;
- ETLantic authorizer and stores to `etlantic-fastapi`;
- request-scoped database sessions where required by the selected provider;
- host logging/correlation context to supported upstream hooks.

ShuETL dependencies must not become pipeline runtime resources or pass
request-scoped sessions into ETLantic transformations.

## Lifespan

ShuETL lifespan may:

- initialize and close provider clients;
- validate package and schema compatibility;
- publish readiness state;
- start explicitly selected local-development roles;
- compose upstream lifespan behavior.

Production gateway lifespan must not start pipeline execution work unless an
upstream provider explicitly qualifies that topology. The reference production
profile runs scheduler and worker roles separately.

## Background tasks

FastAPI `BackgroundTasks` never owns ETLantic pipeline execution or durable
dispatch. Small host-level response follow-up work may use it only when failure
does not affect durable control-plane truth.

## OpenAPI

ShuETL preserves upstream:

- operation IDs;
- request/response schemas;
- problem details;
- security requirements;
- `202 Accepted` semantics;
- SSE media types and resume inputs.

Tests compare the mounted schema with the supported
`etlantic-fastapi` contract.

## Headless host mode

A non-HTTP host uses canonical specifications and commands through ShuETL's
standard backend profile. It does not construct runtime providers, mount routes,
create an HTTP client or call back into its own process. FastAPI dependency
injection remains the mechanism for HTTP requests; headless commands receive
the equivalent trusted principal/context through public upstream contracts.
The backend owns construction of the configured service graph.

This is a composition mode, not a second ETL application API. ShuETL must not
copy ETLantic domain models or call private ETLantic modules to supply a missing
service operation. Required service-level contracts are upstream work.

Expose complete qualified caller-facing control through canonical contracts or
documented public service access, including provider settings and run actions
outside convenience presets. Headless services do not require matching HTTP
routes; any upstream transport limitation is explicit. Apps may implement their
own product endpoints and workflows over these services. See
[DEVELOPER_CONTROL.md](DEVELOPER_CONTROL.md).

The standard submission command delegates the complete preparation/admission
workflow to the public backend service. The host's UI may request separate
validation/explanation/preview, but cannot be responsible for sequencing those
stages correctly to make submission safe.

## Streaming

ShuETL exposes upstream SSE behavior and documents:

- proxy buffering configuration;
- keep-alives and timeouts;
- connection limits;
- graceful gateway shutdown;
- authentication expiry and reauthorization;
- cursor retention gaps.

ShuETL does not implement a second event stream protocol.

## Health and readiness

Use upstream health/readiness routes when available. ShuETL contributes provider
and compatibility signals through supported hooks.

Liveness means the gateway process is running. Readiness means the configured
profile can safely accept the operations it advertises.

## Testing

The FastAPI suite covers:

- mounting and dedicated application modes;
- prefixed deployment and reverse-proxy behavior;
- lifespan composition and cleanup;
- dependency overrides;
- principal/context propagation;
- authorization and non-enumeration;
- OpenAPI parity;
- SSE resume behavior;
- missing/incompatible provider readiness;
- confirmation that no execution runs in request or background-task lifetimes.

The host-integration suite also proves the standard specification and command
surface works without a listening server, with identities and outcomes matching
the mounted HTTP mode. Its reference app supplies neither a provider graph nor
submission preparation logic; the backend owns both in either consumption mode.
