# Phase 0.2 — Architecture and Implementation Plan

## Plan status

- Status: Ready for implementation
- Target release: `0.2.0`
- Baseline release: `v0.1.0`
- Baseline source commit: `1a9c06b4cfa5743bfd258386cc895219ee2dc491`
- Planning date: 2026-09-11
- Supported Python: 3.11, 3.12, and 3.13
- Supported upstream train: `etlantic==0.51.0` and
  `etlantic-fastapi==0.51.0`

This document is the implementation contract for Phase 0.2. It resolves the
public behavior and change boundary needed for implementation. It does not
authorize work deferred to later roadmap phases.

## Architecture summary

Phase 0.2 turns the Phase 0.1 composition proof into the first usable ShuETL
facade for local development and automated tests.

```text
Host FastAPI application
        |
        v
ShuETL facade
  prefix validation
  collision preflight
  handler and lifespan composition
        |
        v
etlantic-fastapi public APIs
  ETLanticAPI
  include_router()
  install_exception_handlers()
        |
        v
Caller-owned ETLantic providers and contracts
```

ShuETL owns only host composition. ETLantic remains the semantic owner and
`etlantic-fastapi` remains the HTTP owner. The facade accepts a prebuilt
`ETLanticAPI`; it does not construct providers, add routes, translate models,
or own execution.

The implementation uses these accepted Phase 0.1 decisions without reopening
them:

| Decision | Phase 0.2 constraint |
|---|---|
| ADR-0001 | ShuETL stays separate only while it provides material host composition value. |
| ADR-0002 | Support remains Python 3.11–3.13 on the exact ETLantic 0.51.0 train. |
| ADR-0003 | Runtime dependencies are limited to directly consumed composition contracts and compatibility constraints. |
| ADR-0004 | The facade accepts only a prebuilt `ETLanticAPI`. |
| ADR-0005 | Host state, exception handlers, and lifespan behavior are never silently replaced. |
| ADR-0006 | The complete upstream router is mounted; no aliases, copies, or route presets are added. |

## Repository ground truth

The plan is based on the published `v0.1.0` repository and installed 0.51.0
distributions.

| Concern | Verified baseline |
|---|---|
| Importable ShuETL surface | Inert typed package with an empty `__all__` |
| Upstream graph | `etlantic_fastapi.ETLanticAPI` |
| Embedded hook | `etlantic_fastapi.include_router(app, api, prefix=...)` |
| Dedicated hook | `etlantic_fastapi.create_app(api, ...)` |
| Error hook | `etlantic_fastapi.install_exception_handlers(app)` |
| Upstream embedding behavior | Writes `app.state.etlantic_api`; installs no handlers, middleware, or lifespan |
| Upstream handler behavior | Registers `control_plane_error_handler` for `ControlPlaneError`, replacing a same-key handler if called blindly |
| Upstream dedicated lifespan | Writes upstream state/readiness fields; starts no execution and exposes no provider-lifecycle protocol |
| Router ownership | Upstream routes, operation IDs, models, status codes, authorization, and SSE |
| Existing proof | Prefixed memory-provider host, durable `202`, idempotent replay, error handling, and normalized OpenAPI parity |
| Release gate | Lock, sync, Ruff, Pyright, boundary checks, tests, build, artifact, OpenAPI, clean-wheel, and evidence checks |
| CI matrix | Python 3.11, 3.12, and 3.13 |

The Phase 0.1 evidence outcome is `proceed-to-0.2`. No blocking upstream hook is
missing for this phase.

## Change boundary

### Problem

Applications can mount `etlantic-fastapi` today, but each host must manually
choose a safe prefix, check state and route collisions, install problem-detail
handlers, coordinate lifespan behavior, and keep dedicated-app behavior aligned
with embedded behavior. Calling the upstream helpers directly can silently
replace `app.state.etlantic_api` or a host `ControlPlaneError` handler.

### Desired outcome

A FastAPI developer can use one narrow, typed facade to embed a caller-owned
ETLantic API graph or create a dedicated application. Both modes expose the
same upstream HTTP contract, reject unsafe composition before known mutations,
and work from the installed wheel.

### In scope

- A public `ShuETL` facade accepting one prebuilt `ETLanticAPI`.
- Mounting the complete upstream router into an existing `FastAPI` app.
- A dedicated FastAPI application factory on the facade.
- Strict, non-normalizing prefix validation.
- Duplicate-mount, prefix-namespace, path/method, operation-ID, state, and
  exception-handler collision detection.
- Installation of the authoritative upstream `ControlPlaneError` handler when
  no conflicting handler exists.
- A ShuETL-owned application-state namespace.
- An integration lifespan and a host-lifespan composition helper.
- Preservation of caller ownership over the prebuilt API and all providers.
- OpenAPI and runtime parity between embedded, dedicated, and direct upstream
  applications.
- Dependency-override documentation and tests.
- Runtime dependency declarations for the supported upstream train.
- A `0.2.0` version bump, package-artifact updates, 0.2 evidence, and
  version-neutral release tooling.
- An installed-wheel quickstart for local/test use.

### Explicitly out of scope

- Environment-driven settings or `ShuETLSettings`.
- Provider graph construction, discovery, factories, or global registries.
- Memory, SQLite, PostgreSQL, or other deployment-profile selection.
- Compatibility/readiness diagnostics or a `shuetl doctor` command.
- Runtime support for an ETLantic train other than exactly 0.51.0.
- Host identity adaptation, AuthMate integration, or a new authorization model.
- Production database claims, migrations, schema checks, or persistence code.
- Scheduler, worker, executor, retry, or in-process pipeline execution code.
- Route filtering, aliases, presets, or ShuETL-authored HTTP endpoints.
- ShuETL request, response, problem-detail, event, report, or artifact models.
- SSE protocol changes, buffering middleware, or proxy configuration.
- A production deployment profile or claim that memory providers are durable.
- Changes tracked by GitHub issues #1 and #2 unless separately authorized.

### Touched surface

Implementation is expected to touch only:

- `src/shuetl/__init__.py`
- `src/shuetl/integration.py`
- `src/shuetl/errors.py`
- `pyproject.toml` and `uv.lock`
- `tests/unit/`, `tests/integration/`, `tests/contract/`, and test support code
- one installed-wheel example under `examples/`
- `scripts/check_artifact.py`
- `scripts/check_clean_wheel.py`
- `scripts/capture_openapi.py`
- `scripts/check_evidence.py`
- `scripts/check_release.py`
- `.github/workflows/checks.yml`
- Phase 0.2 user documentation and `docs/evidence/0.2/`
- `README.md`, `CHANGELOG.md`, and the planning index where needed

No provider, migration, CLI, application server, or ShuETL HTTP-route module is
part of the expected change.

## Public contract

### Public exports

`shuetl.__all__` must contain exactly these Phase 0.2 names:

```python
from shuetl import (
    InvalidPrefixError,
    MountConflictError,
    ShuETL,
    ShuETLError,
)
```

The implementation modules may contain private helpers, but no additional
public constructor, top-level `mount()`, top-level `create_app()`, settings
class, provider bundle, or domain type is introduced.

### Exceptions

```python
class ShuETLError(Exception): ...


class InvalidPrefixError(ShuETLError, ValueError): ...


class MountConflictError(ShuETLError, RuntimeError): ...
```

- `InvalidPrefixError` reports the rejected prefix and the violated rule.
- `MountConflictError` identifies the collision category and the conflicting
  state key, exception type, operation ID, prefix, or route as applicable.
- Errors must not include provider representations, secrets, request bodies,
  headers, or arbitrary application-state values.
- Recognized validation and collision failures occur before router, state, or
  handler mutation.

### Facade construction

```python
class ShuETL:
    def __init__(self, *, api: ETLanticAPI) -> None: ...

    @property
    def api(self) -> ETLanticAPI: ...
```

Required behavior:

- `api` is keyword-only and must be an `etlantic_fastapi.ETLanticAPI` from the
  supported distribution train.
- `None` and arbitrary duck-typed objects raise `TypeError` at construction.
- Construction retains the exact object identity. It does not copy, wrap, or
  mutate the API or its providers.
- One `ShuETL` instance may be used to create or mount multiple distinct apps.
  Mount state is per app, not global to the facade.

Recommended implementation:

- Store the API on a private slot and expose a read-only property.
- Keep collision and route-inspection helpers private in `integration.py`.

### Prefix contract

`mount()` and `create_app()` use the same validator.

Accepted values are:

- the empty string `""`, meaning the upstream router is mounted at root; or
- one or more literal slash-prefixed path segments, such as `/etl`,
  `/internal/etl`, or `/etl-v1`.

Every non-empty prefix must:

- be a `str`;
- begin with exactly one `/`;
- not end with `/`;
- contain no empty segment, `.` segment, or `..` segment;
- contain no route parameters (`{` or `}`), query marker, fragment marker,
  percent escape, backslash, control character, or whitespace;
- use only ASCII URL-unreserved characters within each segment:
  letters, digits, `.`, `_`, `~`, and `-`.

The facade never strips, adds, decodes, case-folds, or otherwise normalizes a
prefix. Invalid values raise `InvalidPrefixError` before app mutation. `/` is
invalid; callers wanting root use `""`.

### Existing-app mounting

```python
def mount(self, app: FastAPI, *, prefix: str = "/etl") -> None: ...
```

Required behavior:

1. Validate `app` and `prefix` without mutation.
2. Inspect all collisions described below without mutation.
3. Install the exact upstream problem-detail handler only when no handler is
   registered for `ControlPlaneError`.
4. Call the public `etlantic_fastapi.include_router()` once with the exact API
   and prefix.
5. Store one private mount record at `app.state.shuetl` after successful mount.
6. Clear `app.openapi_schema` after successful route inclusion so an OpenAPI
   document generated before mounting cannot remain stale.
7. Return `None`.

Mounting must not replace or reorder host middleware, change host metadata,
replace the host lifespan, or modify unrelated application state or exception
handlers.

#### State collision rules

Preflight fails with `MountConflictError` if either condition is true:

- `app.state.shuetl` already exists, regardless of its value; or
- `app.state.etlantic_api` already exists, regardless of whether it references
  the same API.

This deliberately rejects duplicate ShuETL mounts and apps previously mounted
through the upstream helper. The facade must not guess ownership from object
identity. After a successful mount:

- `app.state.etlantic_api is integration.api` is preserved as upstream state;
- `app.state.shuetl` is an opaque ShuETL-owned mount record containing only
  integration identity, API identity, prefix, and private lifecycle state;
- no other pre-existing `app.state` value changes.

The contents of `app.state.shuetl` are internal and not a public model.

#### Exception-handler collision rules

- If `ControlPlaneError` has no registered handler, install the upstream
  handler through `install_exception_handlers()`.
- If the registered handler is the exact exported
  `control_plane_error_handler` object, accept it and do not register it again.
- If any other handler is registered for `ControlPlaneError`, raise
  `MountConflictError` before any mutation.
- Handlers for all other exception types are left byte-for-byte/object-identical
  and in place.

There is no `replace_handlers`, `force`, or silent fallback option in 0.2.

#### Route and operation collision rules

Before mounting, derive the full upstream paths using the validated prefix and
inspect public FastAPI route metadata.

- The upstream router must itself contain unique, non-empty operation IDs.
- Any upstream operation ID already used by a host `APIRoute` is a conflict.
- For a non-empty prefix, any existing host HTTP, WebSocket, or mounted-ASGI
  route at the prefix or below its path-segment subtree is a prefix-namespace
  conflict, even if methods differ.
- For an empty prefix, an existing route conflicts when its concrete path and
  any HTTP method overlap an upstream path/method. Built-in documentation routes
  remain allowed when they do not overlap.
- A path such as `/etlantic` does not occupy `/etl`; segment boundaries matter.
- All recognized collisions raise `MountConflictError` before mutation.

This preflight reserves a non-empty ShuETL prefix as one coherent upstream API
namespace and prevents future upstream route additions from silently colliding
with host endpoints.

### Dedicated application

```python
def create_app(self, *, prefix: str = "") -> FastAPI: ...
```

Required behavior:

- Return a new `FastAPI` instance on every call.
- Use `integration.api.title` and `integration.api.version` as application
  metadata.
- Use `integration.lifespan` as the application lifespan.
- Mount through `integration.mount()` so validation, state, handlers, OpenAPI
  invalidation, and collision behavior are shared with embedded mode.
- Default to root mounting. A caller may pass a validated non-empty prefix.
- Expose the same normalized upstream paths, operation IDs, component schemas,
  status codes, errors, security requirements, and SSE metadata as embedded
  mode and the direct upstream app.

The factory accepts no provider arguments, arbitrary FastAPI keyword arguments,
settings, middleware, or route-selection options. Applications needing host
customization use existing-app mode.

### Lifespan contract

```python
@asynccontextmanager
async def lifespan(self, app: FastAPI) -> AsyncIterator[None]: ...


def compose_lifespan(
    self,
    host_lifespan: Callable[[FastAPI], AsyncContextManager[None]],
) -> Callable[[FastAPI], AsyncContextManager[None]]: ...
```

Required behavior:

- `integration.lifespan` is directly usable as `FastAPI(lifespan=...)`.
- At entry it verifies that `app.state.shuetl` belongs to this integration and
  that `app.state.etlantic_api is integration.api`; otherwise it raises
  `MountConflictError`.
- It marks only the private ShuETL mount record active for the duration of the
  context and always clears that marker on exit.
- Re-entering the same app concurrently raises `MountConflictError`.
- It does not start, stop, close, or mutate caller-owned providers. Phase 0.2
  has no public upstream provider-lifecycle protocol to invoke.
- `compose_lifespan(host_lifespan)` enters the host lifespan first, then the
  ShuETL lifespan. Cleanup occurs in reverse order.
- Each context is entered and exited exactly once.
- If host entry fails, ShuETL is not entered. If app execution or ShuETL entry
  fails after host entry, host cleanup still runs. Original exceptions are not
  translated.
- `mount()` never replaces `app.router.lifespan_context`; callers select the
  helper when constructing the host app.

Supported embedded usage without another lifespan:

```python
integration = ShuETL(api=etlantic_api)
app = FastAPI(lifespan=integration.lifespan)
integration.mount(app, prefix="/etl")
```

Supported host composition:

```python
integration = ShuETL(api=etlantic_api)
app = FastAPI(lifespan=integration.compose_lifespan(host_lifespan))
integration.mount(app, prefix="/etl")
```

The host remains responsible for initializing and closing the providers it
passed into `ETLanticAPI`. Host-first entry lets those providers become ready
before ShuETL validates its mount; reverse cleanup removes ShuETL activity
before provider shutdown.

### FastAPI dependency overrides

ShuETL adds no dependency layer. The same upstream dependency callables remain
override keys in both modes.

Documentation must include an executable example equivalent to:

```python
app.dependency_overrides[integration.api.principal_dependency] = override_principal
app.dependency_overrides[integration.api.context_dependency] = override_context
```

Tests must prove that an override changes the upstream route behavior in both
embedded and dedicated applications and can be removed through ordinary
FastAPI APIs.

### Packaging and compatibility

Phase 0.2 changes the project version to `0.2.0` and makes its imported
dependencies unconditional runtime dependencies.

Required dependency policy:

- `etlantic==0.51.0`
- `etlantic-fastapi==0.51.0`
- FastAPI and Pydantic constrained to the exact versions qualified by the 0.2
  lock/evidence run; the initial target is FastAPI 0.141.1 and Pydantic 2.13.5
- HTTPX remains test-only and is constrained to the qualified version
- Python remains `>=3.11,<3.14`

Exact FastAPI/Pydantic pins are intentionally conservative for this
experimental release. Expanding them requires a separate compatibility matrix,
not a permissive metadata edit.

The wheel includes only the typed `shuetl` package and distribution metadata.
Tests, examples, evidence, and spikes may be in the sdist but not the wheel.

## Required invariants

1. ETLantic owns every domain record and semantic transition.
2. `etlantic-fastapi` owns every ETLantic HTTP route and schema.
3. ShuETL defines no route decorator and no ETLantic shadow model.
4. The exact caller-provided `ETLanticAPI` reaches upstream routes.
5. Known composition conflicts fail before known mutation.
6. Host state and handlers are never silently replaced.
7. The complete upstream router is exposed exactly once per host app.
8. Prefixing changes only paths, never operation IDs or schemas.
9. Authorization dependencies and their ordering remain upstream behavior.
10. `202 Accepted` and idempotency remain upstream store behavior.
11. SSE media type, cursor inputs, and event envelope remain upstream behavior.
12. Provider lifecycle remains caller-owned.
13. No request handler or `BackgroundTasks` object executes pipeline work.
14. Dedicated and embedded modes have normalized OpenAPI parity.
15. Package behavior is proven from an installed wheel on every supported
    Python version.

## Edge cases and failure modes

| Case | Required result |
|---|---|
| `api=None` or a duck-typed object | `TypeError`; no facade created |
| Non-FastAPI `app` | `TypeError`; no mutation |
| Empty prefix | Root mount |
| `/etl` or nested literal prefix | Exact prefix preserved |
| Slash-only, trailing slash, double slash, dot segment, parameterized, escaped, whitespace, or non-ASCII prefix | `InvalidPrefixError`; no mutation |
| Existing `app.state.shuetl` | `MountConflictError`; original value preserved |
| Existing `app.state.etlantic_api` | `MountConflictError`; original value preserved |
| Repeated mount | `MountConflictError`; route count unchanged |
| Existing non-empty prefix subtree | `MountConflictError`; existing routes preserved |
| Root path/method collision | `MountConflictError`; existing routes preserved |
| Operation-ID collision on another path | `MountConflictError` |
| Duplicate IDs inside upstream router | `MountConflictError` |
| Existing exact upstream problem handler | Accepted without re-registration |
| Existing custom `ControlPlaneError` handler | `MountConflictError`; handler preserved |
| Unrelated host handlers | Preserved by object identity |
| OpenAPI generated before mount | Cache invalidated; next schema includes ShuETL routes once |
| Host lifespan entry failure | Exception propagates; ShuETL not active |
| Request failure inside composed lifespan | Both cleanups run once; exception propagates |
| Concurrent lifespan entry for one app | `MountConflictError` |
| One integration used by separate apps | Supported; independent state |
| Dependency override added then removed | Ordinary FastAPI behavior in both modes |
| Provider raises from upstream route | Existing upstream error/status behavior preserved |
| Client disconnect or SSE cancellation | Delegated unchanged to upstream adapter |

Mounting after an application has begun serving is unsupported. Documentation
must state that all mounting and dependency overrides intended as defaults occur
before startup. The facade does not inspect private FastAPI server state.

## Security and reliability requirements

- The facade accepts Python objects only. It accepts no import path, package
  name, source text, file path, URL, credential, or provider configuration.
- The host-supplied principal dependency, context factory, and authorizer remain
  authoritative. ShuETL introduces no anonymous fallback.
- Collision errors expose identifiers needed for remediation but never reprs of
  providers, state values, principals, headers, payloads, or secrets.
- Mount preflight runs before known mutations so an invalid integration cannot
  leave a partly registered route set.
- Host middleware order and exception handlers unrelated to
  `ControlPlaneError` remain unchanged.
- Lifespan cleanup uses `try/finally` or nested async context managers so cleanup
  occurs during normal shutdown, exceptions, and cancellation.
- The facade neither calls provider `close()` methods nor guesses async context
  manager support.
- No production module imports `BackgroundTasks`, scheduler, worker, retry,
  SQLModel, Alembic, or execution libraries.
- Existing upstream authorization-before-lookup and non-enumeration tests must
  pass through ShuETL without weakened assertions.

## Compatibility requirements

- Python 3.11, 3.12, and 3.13 remain supported in CI and package classifiers.
- The runtime train is exactly ETLantic 0.51.0 and `etlantic-fastapi` 0.51.0.
- FastAPI and Pydantic match the versions recorded in the 0.2 lock and evidence.
- Phase 0.1 evidence remains immutable historical evidence; new proof is stored
  under `docs/evidence/0.2/`.
- Existing `v0.1.0` artifacts and tag are not modified or republished.
- The new facade is experimental. Exact names may change before the 0.9 public
  contract freeze, but 0.2 patch releases must preserve this documented shape.
- Upstream request/response models, serialized fields, status codes, problem
  details, operation IDs, security requirements, and SSE metadata are unchanged.
- FastAPI dependency overrides continue to target upstream callables.

## Acceptance criteria

| ID | Observable acceptance criterion |
|---|---|
| AC-001 | The project reports version `0.2.0`, supports Python 3.11–3.13, and declares the qualified ETLantic/FastAPI/Pydantic runtime constraints. |
| AC-002 | `shuetl.__all__` exposes exactly `ShuETL`, `ShuETLError`, `InvalidPrefixError`, and `MountConflictError`. |
| AC-003 | `ShuETL(api=api).api is api`; missing, `None`, and non-`ETLanticAPI` inputs fail with `TypeError`. |
| AC-004 | `mount(app)` mounts the complete upstream router exactly once at `/etl` and returns `None`. |
| AC-005 | `create_app()` returns a new dedicated FastAPI app with root-mounted upstream routes and API-derived title/version. |
| AC-006 | Every accepted prefix is preserved exactly in routing and OpenAPI. |
| AC-007 | Every prohibited prefix class raises `InvalidPrefixError` before route, handler, state, or OpenAPI-cache mutation. |
| AC-008 | Embedded, dedicated, and direct-upstream OpenAPI documents are equal after documented prefix normalization. |
| AC-009 | Upstream operation IDs are complete and unique, and no ShuETL domain schema appears in OpenAPI. |
| AC-010 | Mounting installs the authoritative upstream `ControlPlaneError` handler when it is absent. |
| AC-011 | An already-installed exact upstream handler is preserved without duplicate registration. |
| AC-012 | A different existing `ControlPlaneError` handler causes `MountConflictError` before mutation; unrelated handlers remain object-identical. |
| AC-013 | Successful mounting stores the exact API at `app.state.etlantic_api`, one opaque record at `app.state.shuetl`, and changes no unrelated state. |
| AC-014 | Any pre-existing `shuetl` or `etlantic_api` state key causes `MountConflictError` and remains unchanged. |
| AC-015 | Repeated mounting fails with `MountConflictError` and does not add routes or handlers. |
| AC-016 | An occupied non-empty prefix subtree causes `MountConflictError`; segment-adjacent paths such as `/etlantic` do not conflict with `/etl`. |
| AC-017 | Root path/method collisions and cross-path operation-ID collisions fail before mutation. |
| AC-018 | Duplicate or missing upstream operation IDs fail before mounting. |
| AC-019 | A previously generated OpenAPI cache is invalidated after successful mount and regenerates with each upstream operation exactly once. |
| AC-020 | Host routes, middleware order, metadata, lifespan selection, and unrelated handlers remain unchanged after mount. |
| AC-021 | `integration.lifespan` validates mount ownership, enters/exits once, rejects concurrent re-entry, and clears private active state on normal and exceptional exit. |
| AC-022 | `compose_lifespan()` enters host then ShuETL and exits ShuETL then host exactly once, including exception and cancellation paths. |
| AC-023 | Neither mounting nor either lifespan API starts, stops, closes, or mutates caller-owned providers. |
| AC-024 | Principal and context dependency overrides work and can be removed through standard FastAPI APIs in both modes. |
| AC-025 | Definition reads and validation/planning responses preserve upstream status codes, bodies, models, and authorization behavior in both modes. |
| AC-026 | Submission returns upstream `202`; identical idempotent replay returns one canonical acceptance; conflicting replay preserves upstream `409` problem details. |
| AC-027 | Health, readiness, run observation, report, artifact, lineage, and schema/reliability routes preserve the qualified upstream behavior. |
| AC-028 | SSE paths preserve upstream media type, cursor inputs, event formatting, authorization, and cancellation behavior. |
| AC-029 | Authorization remains before existence-sensitive lookup and no facade fallback principal or authorizer is introduced. |
| AC-030 | Static and runtime checks find no ShuETL-authored ETLantic route, shadow domain model, pipeline execution, or `BackgroundTasks` execution path. |
| AC-031 | One facade instance can serve multiple distinct apps without shared mount/lifecycle state; `create_app()` can be called repeatedly. |
| AC-032 | The documented quickstart runs from an isolated installation of the built wheel with no source-checkout imports. |
| AC-033 | Wheel and sdist contents are allowlisted, include `py.typed`, and declare the expected runtime/test dependencies. |
| AC-034 | Ruff, Pyright, boundary checks, all tests, build, artifact checks, OpenAPI checks, clean-wheel checks, and evidence checks pass on Python 3.11, 3.12, and 3.13. |
| AC-035 | Phase 0.2 documentation states local/test support, provider ownership, lifespan ordering, prefix rules, dependency overrides, collision errors, and explicit non-scope. |
| AC-036 | The 0.2 evidence index maps every AC exactly once to a passing proof and contains no secret or machine-specific path. |

## Verification matrix

| AC | Preferred proof | Required assertion/artifact |
|---|---|---|
| AC-001 | Packaging + compatibility | Metadata inspection, lock check, Python CI matrix |
| AC-002 | Unit + artifact | Exact exports in source and installed wheel |
| AC-003 | Unit + typing | Identity retention and rejected constructor inputs |
| AC-004 | Integration | Default embedded routes and route-count delta |
| AC-005 | Integration | Repeated dedicated factory construction and metadata |
| AC-006 | Parameterized integration | Accepted prefix table against routing and OpenAPI |
| AC-007 | Parameterized unit/integration | Invalid prefix table plus before/after app snapshot |
| AC-008 | Contract | Normalized three-way OpenAPI equality |
| AC-009 | Contract + static gate | Operation-ID inventory and component-schema ownership |
| AC-010 | Integration | Upstream handler identity after mount |
| AC-011 | Integration | Existing exact handler identity and handler-map cardinality |
| AC-012 | Adversarial integration | Custom same-type handler and unrelated handler snapshots |
| AC-013 | Integration | Application-state before/after snapshot and identity checks |
| AC-014 | Adversarial integration | Both reserved state keys with sentinel values |
| AC-015 | Adversarial integration | Second mount and unchanged route/handler counts |
| AC-016 | Parameterized integration | Prefix subtree collision and segment-adjacent success |
| AC-017 | Adversarial integration | Path/method and operation-ID fixtures |
| AC-018 | Unit/contract fixture | Synthetic router with missing/duplicate operation IDs |
| AC-019 | Integration | Generate schema, mount, regenerate, compare operations |
| AC-020 | Integration | Host object snapshots by identity/order/value |
| AC-021 | Async unit/integration | Entry, exit, exception, cancellation, and re-entry counters |
| AC-022 | Async unit/integration | Ordered event log for composed contexts |
| AC-023 | Spy-provider integration | No lifecycle or mutation calls from ShuETL |
| AC-024 | Integration | Override behavior and removal in both app modes |
| AC-025 | Contract | Shared HTTP contract suite parameterized by app mode |
| AC-026 | Contract | `202`, stable identity, and conflicting replay `409` |
| AC-027 | Contract | Qualified route behavior matrix |
| AC-028 | Contract | SSE headers/body/cursor/auth/cancellation assertions |
| AC-029 | Security integration | Denied/missing/existing resource behavior and call order |
| AC-030 | Static gate + runtime spy | Boundary scanner and no-execution assertions |
| AC-031 | Integration | Two apps active independently from one facade |
| AC-032 | Clean-wheel end-to-end | Copy and execute quickstart outside checkout |
| AC-033 | Artifact | Wheel/sdist allowlists and METADATA requirements |
| AC-034 | CI/static gate | Full release command on every supported Python |
| AC-035 | Documentation review | Required topics and executable snippets |
| AC-036 | Evidence gate | AC completeness, PASS status, hashes, and redaction scan |

No AC may be marked complete only because a source string exists. Behavioral
criteria require the production facade path, not a mock facade or copied test
implementation.

## Implementation phases

### E01 — Freeze contract fixtures

Goal: turn the public contract into failing tests before production behavior is
added.

Relevant surface:

- `tests/unit/test_integration.py`
- `tests/integration/test_mount.py`
- `tests/integration/test_lifespan.py`
- `tests/contract/test_http_contract.py`
- shared memory-graph and app-mode fixtures

Required work:

- Replace direct spike-only fixtures with reusable test support that still
  constructs the graph exclusively through public upstream APIs.
- Parameterize runtime HTTP assertions over embedded and dedicated modes.
- Add immutable before/after snapshots for routes, state, handlers, middleware,
  metadata, lifespan, and OpenAPI cache.
- Add invalid-prefix and every collision fixture before implementation.

Dependencies: accepted ADRs and the 0.1 public-contract inventory.

Exit: tests describe AC-003 through AC-031 and fail only because the facade is
not implemented.

### E02 — Update packaging and compatibility

Goal: make the intended runtime boundary explicit.

Relevant surface:

- `pyproject.toml`
- `uv.lock`
- package metadata/artifact tests

Required work:

- Set project version to `0.2.0`.
- Move the supported ETLantic train and qualified FastAPI/Pydantic versions into
  unconditional runtime constraints.
- Keep HTTPX test-only.
- Preserve Python 3.11–3.13 classifiers and `py.typed`.
- Update artifact allowlists without admitting tests or examples to the wheel.

Dependencies: none beyond E01 fixture expectations.

Exit: AC-001 and the metadata portion of AC-033 pass.

### E03 — Implement facade types and prefix validation

Goal: add the smallest importable public surface.

Relevant surface:

- `src/shuetl/errors.py`
- `src/shuetl/integration.py`
- `src/shuetl/__init__.py`

Required work:

- Implement the three exception types and exact exports.
- Implement keyword-only construction and the read-only API property.
- Implement strict prefix validation as a pure private helper.
- Do not add any route, provider, settings, or domain abstraction.

Dependencies: E02 dependency declarations.

Exit: AC-002, AC-003, AC-006, and AC-007 unit proofs pass.

### E04 — Implement atomic mount preflight and composition

Goal: safely mount the authoritative router.

Relevant surface:

- `src/shuetl/integration.py`
- mount and collision integration tests

Required work:

- Inspect state, handler, route namespace, path/method, and operation IDs.
- Accumulate or deterministically report the first conflict without mutation.
- Accept only the exact existing upstream handler.
- Install handlers and invoke the upstream public `include_router()` once.
- Write the private mount record only after success.
- Invalidate the OpenAPI cache after successful inclusion.

Dependencies: E03.

Exit: AC-004 and AC-010 through AC-020 pass.

### E05 — Implement lifespan and dedicated-app composition

Goal: make embedded and dedicated hosting deterministic.

Relevant surface:

- `src/shuetl/integration.py`
- lifespan and app-factory tests

Required work:

- Implement the bound async lifespan with per-app active state.
- Implement host-first nested lifespan composition.
- Ensure cleanup on exceptions and cancellation.
- Implement `create_app()` through the same mount path.
- Prove that no provider lifecycle method is inferred or invoked.

Dependencies: E04.

Exit: AC-005, AC-021, AC-022, AC-023, and AC-031 pass.

### E06 — Prove upstream contract preservation

Goal: demonstrate that the facade is composition, not a second HTTP layer.

Relevant surface:

- shared integration fixtures
- `tests/contract/test_http_contract.py`
- OpenAPI capture tooling

Required work:

- Run the same behavior suite against both ShuETL modes.
- Compare both modes to direct upstream normalized OpenAPI.
- Assert problem details, authorization order, durable acceptance, idempotent
  replay, conflict behavior, SSE, reports, artifacts, and operability routes.
- Add spies proving no request/background execution path.
- Test dependency overrides through the exact upstream callables.

Dependencies: E05.

Exit: AC-008, AC-009, and AC-024 through AC-030 pass.

### E07 — Add installed-wheel quickstart and user documentation

Goal: provide a truthful local/test integration path.

Relevant surface:

- `examples/phase_0_2_quickstart.py`
- `README.md`
- `CHANGELOG.md`
- a focused Phase 0.2 integration guide

Required work:

- Show caller-owned memory providers, `ShuETL(api=...)`, host mount, dedicated
  app creation, dependency overrides, and lifespan composition.
- Label memory providers process-local and the release experimental.
- Document all prefix and collision rules and exact remediation.
- Execute the example from an installed wheel outside the checkout.

Dependencies: E06.

Exit: AC-032 and AC-035 pass.

### E08 — Generalize release tooling and assemble 0.2 evidence

Goal: make the existing one-command gate prove Phase 0.2 without rewriting
Phase 0.1 history.

Relevant surface:

- `scripts/check_artifact.py`
- `scripts/check_clean_wheel.py`
- `scripts/capture_openapi.py`
- `scripts/check_evidence.py`
- `scripts/check_release.py`
- `docs/evidence/0.2/`
- `.github/workflows/checks.yml`

Required work:

- Derive the project version from package metadata or `pyproject.toml`; remove
  hardcoded 0.1 artifact names.
- Point current OpenAPI and evidence checks at the 0.2 artifacts while retaining
  0.1 evidence unchanged.
- Validate the exact AC-001–AC-036 set, artifact hashes, environment versions,
  import origins, redaction, and gate results.
- Rename CI display/artifact names that incorrectly say Phase 0.1.
- Keep the release workflow tag/version check and Trusted Publishing chain.
- Keep the release command self-bootstrapping from a clean clone.

Dependencies: E07.

Exit: AC-033, AC-034, and AC-036 pass locally.

### E09 — Final compatibility and scope gate

Goal: establish a reviewable 0.2 release candidate.

Required work:

1. Run `uv run python scripts/check_release.py` from the working repository.
2. Clone the exact candidate commit into a fresh directory and run only the
   same command.
3. Install the wheel without the source checkout and run the quickstart.
4. Run CI on Python 3.11, 3.12, and 3.13.
5. Verify the normalized OpenAPI and artifact hashes from CI outputs.
6. Audit every file against the touched surface and explicit non-scope.
7. Obtain normal production review before any `v0.2.0` tag.

Dependencies: E08.

Exit: every AC is linked to passing evidence and no release blocker remains.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Upstream handler installation silently replaces a host handler | Host error semantics change | Inspect the exact exception key and accept only the exact upstream handler before calling the installer |
| `include_router()` overwrites upstream state | Host integration is corrupted | Reserve and preflight both state keys before invoking upstream |
| A non-empty prefix already contains host routes | Ambiguous ownership and future collisions | Reserve the whole path-segment subtree |
| FastAPI already cached OpenAPI | Published docs omit mounted routes | Invalidate only `app.openapi_schema` after successful mount and test regeneration |
| Route inspection relies on framework internals | Compatibility fragility | Use public `app.routes`, route `path`/`methods`/`operation_id`, and pin the qualified framework versions |
| Provider lifecycle is guessed | Double close, leaked resources, or ownership inversion | Call no provider lifecycle methods; require host ownership and document entry order |
| Facade becomes an alias with no durable value | Package boundary is unjustified | Collision safety, lifecycle composition, parity proof, and installed-wheel DX are release requirements |
| Test fixtures duplicate upstream behavior | False confidence | Exercise real upstream router/services and parameterize the production facade path |
| 0.2 expands into settings or deployment work | Review boundary becomes unbounded | Enforce explicit non-scope through review tests and defer to roadmap phases |
| Exact dependency train becomes stale | Upgrade pressure | Keep 0.2 conservative; expand only with a new compatibility decision and evidence |

## Known pre-existing problems and follow-up candidates

These do not block Phase 0.2 unless their current behavior changes materially:

- [GitHub issue #1](https://github.com/eddiethedean/shuetl/issues/1): upgrade
  GitHub Actions away from deprecated Node.js 20 runtimes.
- [GitHub issue #2](https://github.com/eddiethedean/shuetl/issues/2): migrate
  HTTP tests from the deprecated TestClient transport. Phase 0.2 may use the
  existing test path, but it must not weaken assertions to suppress warnings.
- [ETLantic issue #130](https://github.com/eddiethedean/etlantic/issues/130):
  upstream docstring drift recorded during Phase 0.1.
- Phase 0.3: settings, explicit local provider construction, profiles, and
  compatibility/readiness diagnostics.
- Phase 0.4 and later: relational persistence, provider migrations, identity,
  and separated runtime roles.

No additional planning-time issue is required. The known state/handler/OpenAPI
hazards are in-scope Phase 0.2 behavior with acceptance coverage.

## Definition of done

Phase 0.2 is complete only when:

- every AC-001 through AC-036 criterion is satisfied by the production facade;
- all required compatibility and ownership invariants remain true;
- recognized conflicts are proven mutation-free;
- embedded and dedicated modes pass the same upstream contract suite;
- lifecycle order, cleanup, and caller provider ownership are proven;
- the installed-wheel quickstart succeeds outside the checkout;
- the complete self-bootstrapping release gate passes from a fresh clone;
- CI passes on Python 3.11, 3.12, and 3.13;
- 0.2 documentation and evidence match implemented behavior;
- no follow-up work was silently pulled into scope;
- no blocker attributable to Phase 0.2 remains.

The repository does not need to be globally defect-free. Pre-existing and
explicitly deferred problems remain follow-up work unless they prevent an
in-scope acceptance criterion from being verified or safely delivered.

## Final planning decision

The 0.51.0 public composition hooks are sufficient, the Phase 0.1 boundary
review explicitly permits work to proceed, and this contract leaves no required
public-shape or collision-policy decision to the implementer.

**READY FOR IMPLEMENTATION**
