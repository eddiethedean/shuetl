# Phase 0.5 — Secure Host Integration: Architecture and Implementation Contract

## Plan status

- Target release: `0.5.0`.
- Baseline release: `v0.4.0`, release commit
  `69f140f6f7343cc6e2bdbb97c34dba3d4eb324e0`.
- Baseline checkout: `ebe42ad6bfb47a9632941deff62a758dec050232`; implementation
  and documentation are committed on `main`.
- Implementation date: 2026-09-29.
- Status: **RELEASED as ShuETL 0.5.0 on 2026-09-30 UTC**.
  Published upstream prerequisites, local supported-Python matrix, live
  PostgreSQL suite, release artifact gates, and hosted CI are qualified. Tag
  [`v0.5.0`](https://github.com/eddiethedean/shuetl/tree/v0.5.0) resolves to
  release commit `d846c3dd15b517def5c736e831202a603ca0e080`. Pre-tag run
  [36659423353](https://github.com/eddiethedean/shuetl/actions/runs/36659423353)
  and tag-triggered release run
  [36659686930](https://github.com/eddiethedean/shuetl/actions/runs/36659686930)
  passed on Python 3.11–3.13; Trusted Publishing completed. The final hosted
  checks include the AC-017 configured-provider foreign-record proof.

This contract implements the [0.5 roadmap boundary](ROADMAP.md#05--secure-host-integration).
It replaces speculative identity examples in the general design pack for this
release. The [0.4 contract](PHASE_0_4_EXECUTION.md) remains authoritative for the
PostgreSQL pilot's persistence and migration behavior. AC IDs below belong to
Phase 0.5; identical IDs in older releases retain their older meanings.

The composition decisions below are fixed. ShuETL does not implement ETLantic
routes, authorizers, stores, authentication, or validation-error semantics.
Published ETLantic 0.55.0 supplies the corrected list filtering and public
redacted-validation route seam; its exact artifacts and behavior are recorded
in the Phase 0.5 evidence.

## Architecture summary

Add one small, explicit identity-composition object, `HostIdentityAdapter`,
which consumes an already authenticated upstream `Principal` through native
FastAPI dependency injection and guards the host's synchronous context factory.
The object stores callables and a development-mode flag; it is not a principal,
membership record, policy engine, credential store, or authentication provider.

```text
Host credential validation / session lookup
        |
        v
native FastAPI dependency -> ETLantic Principal
        |
        v
HostIdentityAdapter principal guard
        |
        v
trusted host ContextFactory -> ETLantic ControlPlaneContext
        |
        v
HostIdentityAdapter context guard
        |
        v
etlantic-fastapi route -> ETLantic Authorizer -> scoped upstream store
        |
        v
canonical ETLantic records / redacted upstream HTTP errors / SSE
```

The host validates credentials and chooses authoritative membership. ETLantic
owns action/resource decisions, scope isolation, list visibility, non-enumeration,
events, execution identities, and redaction. ShuETL validates and wires the
composition and proves that mounting preserves the qualified upstream behavior.
There is no new middleware authentication layer, permission namespace, token
parser, route implementation, persistent state, or execution role.

### Repository ground truth

| Concern | Inspected reality and implication |
|---|---|
| Request/specification | The user's architecture-only request and `ROADMAP.md` 0.5 deliverables; no existing 0.5 execution plan or ShuETL feature issue was found. |
| Governing design | `IDENTITY_INTEGRATION.md`, `SECURITY.md`, `API_DESIGN.md`, `FASTAPI_STRATEGY.md`, `RESULTS_AND_ARTIFACTS.md`, `PYDANTIC_STRATEGY.md`, `ARCHITECTURE.md`, `EXTENSIBILITY.md`, and ADRs 0004–0010. General design examples describe future APIs and are not evidence of implemented exports. |
| Local instructions | No applicable repository/ancestor `AGENTS.md` was found. |
| Facade | `src/shuetl/integration.py`: `ShuETL(api=...)` retains the exact caller API; mount preflights conflicts, preserves upstream routing/handlers, clears OpenAPI cache, and leaves provider lifecycle to the caller. |
| Existing identity interface | `providers.py` requires an authorizer and two raw callbacks. `_accepts_positional` binds a principal dependency with one positional request and a context factory with two arguments. This rejects valid native keyword-only/subdependency shapes and does not validate returned identities. |
| Settings | `settings.py`: immutable, extra-forbidden; explicit profile/role/provider/identity, identity currently only `host`; constructor overrides case-sensitive uppercase environment; no file/dotenv secret source. |
| Diagnostics | `diagnostics.py`: `shuetl.doctor/1`; `identity.explicit` currently verifies the configured string, not an actual adapter or authentication service. |
| Upstream principal/context | Published `etlantic==0.55.0`: frozen dataclasses `Principal(subject, issuer=None, kind="human")` and `ControlPlaneContext`; ShuETL additionally validates identity/scope values at its host composition boundary. |
| Upstream dependency seam | Published `etlantic-fastapi==0.55.0`: native `Depends(api.principal_dependency)`; `ContextFactory` is synchronous `(Principal, Request) -> ControlPlaneContext`. ShuETL supplies stable guards while leaving native FastAPI dependency resolution intact. |
| Host auth helpers | `principal_from_header` and `make_principal_from_header` are explicitly demo/test-only. `oauth2_oidc_principal_hook` maps claims and does not verify credentials. `membership_context_factory` keys membership only by subject; it does not prove issuer trust. |
| Authorization ordering | Public upstream helpers authorize first. `require_authorized_run` may subsequently probe existence only in the caller's scoped run store to distinguish in-scope 403 from opaque 404. A requirement of zero reads after every denial would contradict this supported behavior. |
| Lists/pagination | ETLantic 0.55.0 `visible_items` and `visible_limited_items` apply collection and per-item decisions before existing limits/results. Most exposed lists have no pagination; durable outbox and audit expose a `limit`. ShuETL adds no pagination API. |
| SSE | Connection/run authorization precedes cursor validation; unknown or foreign-scope cursors return upstream 410. Follow defaults cap at 100 polls/60 seconds; the implementation does not continuously reauthenticate. |
| Artifacts | The exposed artifact route is run-authorized acceptance-receipt metadata. The built-in graph has no full artifact download, signing, preview, or artifact provider. Those capabilities cannot be promised in 0.5. |
| HTTP errors | Upstream `ControlPlaneError` handler serializes redacted ETLantic problem details. `RedactedValidationRoute` is exported by `etlantic_fastapi`, selected by the upstream router builder, and preserves a fixed safe 422 response for control-plane routes. |
| Persistence/migrations | No ShuETL-owned tables. PostgreSQL 18.6, head `005_cp1_reference`, 17 required tables, explicit upstream upgrade command, and read-only startup/doctor remain the 0.4 boundary. |
| Dependencies/runtime | Python `>=3.11,<3.14`; exact ETLantic core/FastAPI/SQLModel `0.55.0`, FastAPI `0.141.1`, Pydantic `2.13.5`, pydantic-settings `2.15.0`, SQLAlchemy `2.0.52`, Psycopg/binary `3.3.5`; test extra `httpx2==2.12.0`; Hatchling packaging and `py.typed`. |
| Existing tests | 0.2 HTTP/dependency-override/auth-before-lookup tests; 0.3 settings, callback-shape, redaction and diagnostics tests; 0.4 native graph, cleanup, evidence and real PostgreSQL restart/concurrency tests. Existing production fixtures use synthetic static callbacks and require adaptation for the new guarded context identity invariant. |
| CI/gates | `.github/workflows/checks.yml`: quality, real PostgreSQL, and release-gate jobs on Python 3.11/3.12/3.13; release workflow depends on checks. Gates cover lock/sync, Ruff, Pyright, boundaries, pytest, build, artifacts, OpenAPI, separate clean-wheel extras, and evidence. |
| Release infrastructure | `check_release.py` derives the release series, but `check_evidence.py` still binds proof validation to the 0.4 plan/count. Artifact metadata checks and workflow labels also name 0.4. Focused 0.5 updates are required. |

### Upstream 0.55.0 qualification

On 2026-09-29, the published core, FastAPI, and SQLModel 0.55.0 wheels were
downloaded and inspected. Direct installed-artifact probes confirmed that an
explicit `definition:hidden` list denial filters a collection-granted list and
that a malformed control-plane request with a nested password sentinel returns
the fixed redacted 422 body without the input. The same validation route is
used by `ETLanticAPI` in direct and ShuETL-mounted apps; an unrelated host route
keeps FastAPI's own ordinary validation response. ETLantic issues #143 and #144
remain open in the project tracker, but their published package requirements
were verified against the artifacts rather than inferred from issue status.

The upstream SQLModel version chain and head are unchanged at
`005_cp1_reference`. Exact non-ETLantic pins remain unchanged. The exact commands,
versions, observed response fragments and limits belong in
`docs/evidence/0.5/upstream-artifact-qualification.md`.

### Implementation verification

The initial release adjustments updated stale 0.4 evidence fixtures, CI labels,
and PostgreSQL identity fixtures to use a genuine guarded host dependency. The
current verification run records 183 passed tests and five environment-gated
PostgreSQL skips per supported Python runtime; the dedicated PostgreSQL 18.6
job executes all five integration cases without skips. Exact commands,
artifacts, warnings, and the distinction between local and hosted CI runs are
recorded in [the Phase 0.5 evidence](../evidence/0.5/README.md).

## Change boundary

### Problem

The gateway has durable providers and explicit host callbacks, but lacks a
qualified interface for native authenticated FastAPI dependencies, runtime
identity/context validation, enforceable development-mode separation, and
comprehensive security-contract verification. The pinned upstream adapter also
does not meet the required concrete list-denial and validation-redaction rules.

### Desired outcome

A host can supply its authenticated principal dependency, authoritative context
factory, and conforming ETLantic authorizer to a controlled single-tenant
gateway. Native dependency graphs and cleanup work normally; malformed identity
or context cannot reach protected services; development static identity cannot
construct or mount a production profile. Mounted endpoints preserve the
qualified upstream authorization, scope, error, SSE, and redaction contracts.

### In scope

- `HostIdentityAdapter` and its host/static-development factories.
- Native FastAPI principal dependencies, including sync, async, nested
  `Depends`/`Security`, keyword-only parameters, and yield cleanup.
- Guarded, synchronous upstream context construction and principal/scope checks.
- Adapter injection into the existing local and PostgreSQL bundles; explicit
  compatibility handling for raw callback callers.
- Production security preflight for bundle construction and prebuilt API
  mounting, without changing caller API/store ownership.
- One explicit `development-static` identity settings value limited to local
  profiles; safe, bounded diagnostic summaries in the existing schema.
- Complete mounted-route authorization inventory, all-mutation denial coverage,
  direct/list/bounded-list/SSE/artifact-metadata cross-scope probes, and outages.
- Qualification of upstream fixes for PB-001/PB-002 and their public seams;
  implementation of those semantics remains upstream work.
- Host OIDC and session integration recipes using already validated identity;
  executable local smoke harnesses with synthetic host authentication.
- Secret-resolution absence and redaction checks at the gateway boundary.
- Exact 0.5 packaging, clean-wheel, CI, documentation, and evidence updates.

### Touched surface

Expected downstream production edits are limited to a new
`src/shuetl/identity.py`, `providers.py`, `integration.py`, `settings.py`,
`diagnostics.py`, `compatibility.py`, and `__init__.py`. Existing error classes
suffice. `_secrets.py`, `postgresql.py`, and `cli.py` need only version/remediation
or direct compatibility changes justified by qualification; their database
behavior must not be redesigned.

Expected supporting edits: `pyproject.toml`, `uv.lock`, focused identity/security
unit and integration tests, production-auth fixture updates in existing tests,
artifact/clean-wheel/evidence scripts, the current workflow labels/test commands,
`examples/phase_0_5_*`, the 0.4 PostgreSQL example's authentication recipe,
README, changelog, ADR-0011, planning index, and `docs/evidence/0.5/`.

Do not add runtime provider imports, schemas, migrations, routes, or services in
the ShuETL tree to compensate for PB-001/PB-002. A reviewer finding an unrelated
defect does not expand this boundary. A security defect in a qualified route
that invalidates a listed AC is an upstream release prerequisite, not permission
to fork its implementation.

## Public contract

### Required behavior — exports and identity composition

All 0.4 top-level exports remain in their current order. Append exactly one new
name, `HostIdentityAdapter`, to the existing `__all__`; add no ShuETL principal,
context, membership, authorization-decision, or token model.

The public construction surface is:

```python
HostIdentityAdapter.create(
    *,
    principal_dependency: Callable[..., Any],
    context_factory: ContextFactory,
) -> HostIdentityAdapter

HostIdentityAdapter.development_static(
    *,
    principal: Principal,
    tenant_id: str,
    workspace_id: str,
    environment: str = "development",
    security_domain: str = "default",
) -> HostIdentityAdapter
```

`ContextFactory` and `Principal` are the upstream types. `Callable[..., Any]`
intentionally describes native FastAPI dependency forms; the resolved output
must be an upstream `Principal`. The adapter exposes stable callable properties
`principal_dependency`, `context_factory`, and `development_only: bool`.
Repeated property access returns the same callable objects. Metadata is
immutable; callable, principal, membership, request, and credential contents
are excluded from adapter repr. The adapter has no persistence/JSON format and
no authentication or policy-health method.

`create` accepts a FastAPI-inspectable callable without invoking it at startup.
Do not require that a request can be bound positionally. FastAPI executes the
host dependency and its subdependencies; ShuETL must not call it directly, use
`asyncio.run`, solve dependencies itself, or copy its credential inputs. The
guard participates as a dependency on the exact host callable. Native caching,
security-scheme discovery, overrides targeting the original callable, and yield
teardown follow FastAPI's supported dependency behavior.

The host context factory must be inspectable, synchronous, callable with
`(principal, request)`, and return a context directly. Async context factories,
async callable objects, and generator context factories are rejected at
construction with a constant `TypeError`. Async membership lookup belongs in
host principal subdependencies; the synchronous factory can read trusted
request state populated by those dependencies. General async context support
requires an upstream extension and is outside 0.5.

Known upstream demo dependencies `principal_from_header` and the closures
returned by `make_principal_from_header` must be rejected by the host factory
and production preflight. Match the qualified upstream helpers explicitly;
do not classify arbitrary host callables by their names, source text, globals,
or whether they use a fixed scope. A server-fixed scope is legitimate after
host authentication. Detection is a misuse guard, not a proof that arbitrary
trusted host code authenticates correctly.

`development_static` validates the upstream principal and scope inputs eagerly,
then produces a constant principal dependency and upstream context factory.
It reads no identity/scope headers and generates no credentials; its
`development_only` is `True`. It may use upstream static-context/key helpers to
preserve correlation and idempotency behavior. No allow-all authorizer is
created; the caller must still supply a conforming authorizer.

### Required behavior — identity and context validation

On each protected request, before context construction, validate the resolved
principal without coercing, serializing, stripping, or logging its input:

- It is an instance of the upstream `Principal` with a non-blank string subject.
- Issuer is `None` or a non-blank string; kind is exactly `human`, `workload`, or
  `service`.
- `None`, dictionaries, ORM objects, tokens, arbitrary objects, malformed
  dataclass fields, and wrong dependency output types fail with upstream
  `ControlPlaneError.unauthorized("Authenticated principal is required.")`.
- Valid subject/issuer/kind values are preserved exactly. The same principal
  object reaches the host context factory.

Validate the factory result before ETLantic route/service use:

- It is an upstream `ControlPlaneContext`; its principal is the exact guarded
  principal object, not a replaced user or execution identity.
- Tenant/workspace/environment/security-domain refs are the corresponding
  upstream classes with non-blank string IDs/names.
- Workspace tenant equals the context tenant.
- Optional correlation/idempotency keys are `None` or their upstream key
  classes with non-blank string values; request ID is `None` or a non-blank
  string. Preserve accepted objects and values without injecting defaults in
  host mode.
- Wrong output, mismatched principal/scope, an unexpected awaitable, or an
  unexpected factory exception yields a constant upstream error: code
  `PMCP503`, HTTP 503, title `Service Unavailable`, type
  `etlantic.control_plane/error`, detail `Host identity context is unavailable.`
  Do not render the factory exception/input or chain it into a public/logged
  credential payload. No partial context is returned.
- If a synchronous factory unexpectedly returns a Python coroutine, close it
  without running it before rejecting the output; do not leave an unawaited
  coroutine warning or introduce an async bridge. Catch ordinary `Exception`
  only; cancellation, `KeyboardInterrupt`, and `SystemExit` propagate normally.
- Explicit host `ControlPlaneError` authentication/membership decisions remain
  upstream errors and are serialized by the qualified upstream handler.
  They do not trigger fallback scope or a static principal.

Host-dependency errors occur during FastAPI subdependency execution, before the
principal guard runs. The host owns their safe error mapping: sanitized 401 for
missing/invalid/expired credentials and sanitized 503 for membership/IdP outage.
ShuETL must not claim it can catch such errors inside the output guard. Unexpected
errors remain unsuccessful framework responses with production debug disabled;
they never become anonymous or successful requests.

### Required behavior — bundle and facade integration

Extend both existing bundle factories with optional `identity_adapter` while
retaining the names of the raw callbacks:

```python
Bundle.create(
    settings,
    *,
    authorizer: Authorizer,
    identity_adapter: HostIdentityAdapter | None = None,
    context_factory: ContextFactory | None = None,
    principal_dependency: Callable[..., Any] | None = None,
) -> Bundle
```

Here `Bundle` means `LocalProviderBundle` or `PostgreSQLProviderBundle`.
Exactly one complete input form is accepted: an adapter, or both raw callbacks.
Missing pairs and mixed forms raise constant `TypeError` before engine creation.
`authorizer` remains required. Validate its runtime upstream protocol, callable
synchronous `authorize`, and ability to bind `(context, action, resource)`
without calling it or inventing a test decision. Policy-return semantics remain
the upstream authorizer contract; no ShuETL policy wrapper is added.

With `identity="host"`, a supplied adapter must be host-mode. In PostgreSQL,
legacy genuine host callbacks normalize through `HostIdentityAdapter.create`
and receive the same request guards. Legacy known header-demo callbacks are
rejected. Local legacy callback mode with `identity="host"` retains its 0.4
behavior, including the old callback shape checks; it is explicitly unqualified
development compatibility behavior. New local users should select the adapter
form to obtain native dependency support and guards.

With `identity="development-static"`, a local bundle requires the adapter form
and a development-static adapter. No raw callback shortcuts or implicit static
principal are allowed. PostgreSQL rejects development-static settings/adapters
before driver imports, connection, or store construction.

Expose `identity_adapter: HostIdentityAdapter | None` on bundles: the supplied
or normalized actual adapter, or `None` for the legacy local form. Construct the
upstream API with its stable guarded callables and the exact caller authorizer.
Store/API types and shared-engine identities remain the 0.4 contract; the only
intentional graph difference is the principal/context guard callables. Preserve
explicit `close`, closed-state behavior, cleanup on cancellation, and upstream
development/production profile selection.

`ShuETL(api=...)` retains its constructor and exact `.api` object. For
production/unknown-profile APIs, construction and mount/app-factory preflight
require the principal/context callables to be a matching pair from one host-mode
adapter and the authorizer to conform. A prebuilt production API is assembled
with `adapter.principal_dependency` and `adapter.context_factory` before being
given to ShuETL; ShuETL does not replace callbacks, copy the API, materialize its
router early, or close caller resources.

Classify `None` and exact upstream development aliases `development`, `local`,
`test`, `dev` as development; `production`/`prod` as production; an upstream
`Profile` by public `is_production_profile(profile)`. Any other string/object
requires the host guard conservatively. Do not resolve filenames or load profile
JSON merely to decide whether security preflight applies. This avoids filesystem
configuration determining whether a guard is required. Existing upstream profile
validation/planning still owns whether the profile itself is usable.

Preflight rechecks the guard pair and authorizer before host app mutation. It
rejects a development adapter, a mismatched pair, or a caller API whose callbacks
were reassigned after composition with `ProviderReadinessError` using constant
messages. FastAPI/router graphs must not be mutated after construction/startup;
trusted code that changes dependency internals or installs bypass overrides is
outside the supported production trust boundary. No attempt is made to defend
against mutually untrusted Python in the same process.

### Required behavior — settings and diagnostics

- Extend only `identity` to `Literal["host", "development-static"]`; it remains
  required and is loaded through `SHUETL_IDENTITY` with existing precedence.
- The new value is valid only for `local` with memory/pre-provisioned SQLite,
  `gateway`, and `complete`. Every other profile/provider/default stays as 0.4.
- Static subject, memberships, issuer allowlists, JWT secrets, provider import
  paths, and token fields are not settings fields or environment sources.
- Keep `shuetl.doctor/1`, JSON fields, check IDs/order, CLI exits, and redaction.
  Local static identity yields an `identity.explicit` warning and a bounded
  development-only summary; the overall report still passes absent failures.
- Without a supplied bundle, host-mode doctor states that the mode is configured
  and the runtime adapter was not inspected; it must not claim authentication
  was verified. Do not call host dependencies, authorizers, IdPs, or secret
  providers from doctor.
- With a supplied bundle, report the actual adapter mode and fail identity
  preflight if it conflicts with settings/profile. Keep the existing
  settings/bundle mismatch failure. Legacy local bundles remain visibly
  development-only; diagnostic contents include no principal or scope IDs.

### Required behavior — authorization and HTTP qualification

Use the existing complete upstream router. Record all routes from `routes.py`,
`schedule_routes.py`, and `ai_routes.py`, including optional-provider routes.
The final route inventory binds method/path/operation ID to each upstream
action/resource and its allow/deny/missing-provider proof. Inventory equality
must fail if a new mutation appears without a test binding.

For every mounted POST/PUT/PATCH/DELETE, test a well-formed denied request with
an explicit conforming authorizer. Confirm exact action/resource and context,
authorization before business lookup, and no state mutation. Optional providers
remain absent in the built-in graph: denial must precede unavailability, and an
authorized request preserves upstream 501 when applicable. Qualifying denial
on an optional route does not qualify its full governance/execution behavior.

Normative examples of retained action/resource contracts:

| Route family | Existing upstream contract |
|---|---|
| Definition list/read/validate/plan | `definition.list` on `definition:*`; `definition.read/validate/plan` on `definition:{id}`. |
| Submit/cancel | `run.submit` on `definition:{id}`; `run.cancel` on `run:{id}`. |
| Run read/events/report/artifacts/lineage | `run.read/events/report/artifacts/lineage` on `run:{id}`. |
| Registry tenant/workspace/revision/alias/promotion | Existing `registry.*` actions on upstream `registry:*` resources; retain tenant/workspace isolation even for collection rights. |
| Durable host routes | Existing `durable.*` actions on outbox/submission/attempt/checkpoint/etc. resources. These routes do not cause ShuETL to own a worker. |
| Schedules | `schedule.write` or `schedule.read` on definition/schedule/firing resources; upstream scheduler/worker-health actions remain protected. |
| Optional governance/AI routes | Existing policy/approval/quota/erasure/audit/attestation/objective and AI actions; include their actual inventory, not only CP1 routes. |
| `/health`, `/ready` | Existing public bounded operational responses; no new authentication requirement or readiness endpoint. `/ready` checks injection, not live IdP/policy health. |

Preserve explicit upstream 403/404 disclosure decisions. Cross-scope denies
must not disclose protected existence/content; after authorization denial, only
the documented caller-scoped run-existence probe is permissible. Do not require
byte-identical messages for every upstream missing and denied resource. No
foreign-scope lookup or protected mutation occurs before authorization.

For list visibility, retain collection authorization before lookup and apply
concrete resource decisions before serialization and any existing limit.
Definition visibility uses `definition.list` on `definition:{id}`; workspace
visibility uses `registry.workspace.list` on `registry:workspace:{id}`. Read
permission is independent of list permission. Denied items do not occupy result
slots or appear in totals/cursors. No new list/pagination API is introduced.
The qualified 0.55.0 route behavior and concrete resource contracts are recorded
in the route inventory and release evidence.

SSE run/connection authorization precedes replay/cursor access. Cross-scope run
access uses opaque upstream denial; a foreign/unknown cursor in an otherwise
authorized stream uses upstream 410. Retain query-cursor versus Last-Event-ID
precedence, envelope/sequence behavior, existing follow caps, and teardown on
disconnect. No continuous token refresh or policy reauthorization is invented;
hosts must bound connection lifetimes and require fresh authentication on
reconnect. Midstream failures terminate without successful/fabricated frames;
an HTTP error status cannot be substituted after headers have been sent.

Artifacts are limited to the existing acceptance-receipt metadata route and its
`run.artifacts` checks. Do not add artifact storage, download, filesystem access,
preview, signed URLs, or retention logic.

Expected host/policy outages are upstream sanitized 503 errors. Required
provider errors fail the operation rather than falling back to memory,
unauthenticated identity, partial lists, empty-success results, or fabricated
acceptance. Unexpected exceptions may remain generic HTTP 500; no new global
exception-to-503 translation is required. Preserve upstream transactions and
already-committed-state semantics; do not promise rollback across every store
when a later event operation fails.

HTTP paths, models, normal statuses, operation IDs, schema references and native
security-scheme discovery remain upstream/FastAPI-owned. Host security schemes
may appear in OpenAPI through the dependency graph; do not add fake OAuth scopes
or require a scheme for cookie/middleware-based identity that does not expose one.

### Required behavior — redaction and execution identity

The adapter receives `Principal`, not claims, authorization headers, cookies,
credential objects, raw JWTs, or resolved pipeline secrets. The host maps only
identity fields after credential validation and derives scope only from approved
issuer-aware membership or server-fixed deployment routing. Caller path/query/
body/headers cannot replace tenant/workspace/environment/security-domain authority.
Correlation/idempotency keys are metadata, not membership grants.

Use a single host-approved identity namespace in the first supported deployment.
The upstream submission key currently includes principal subject, not issuer.
Do not claim multi-issuer collision isolation. Hosts accepting multiple issuers
must use distinct canonical subject namespaces and issuer-aware membership;
subject-only upstream membership helpers are not production authentication.

No pipeline secret/resource provider or executor is installed or invoked by the
identity object, doctor, bundle startup, or mounted gateway flows. Instrument
upstream secret-resolution/execution seams for validate/plan/submit/schedule
probes; any resolution discovered in a required gateway path is an upstream
blocker. Triggering subject/issuer/kind remain canonical submission metadata;
do not reinterpret them as workload credentials or propagate host tokens into
durable payloads/schedules. Scheduled work does not inherit a session/token.

Redaction proof covers ShuETL settings validation, upstream problem details,
HTTP request validation, gateway-emitted logs/events/SSE, readiness/doctor, and
OpenAPI examples. Use recognized credential-bearing keys/URLs and synthetic
sentinels; inspect adapter-owned repr/errors without invoking arbitrary input
repr/str. There is no promise to recognize every secret hidden under an arbitrary
ordinary string, sanitize host-owned application logs, or remove secrets that
trusted host code deliberately embeds in identity IDs. Do not install blanket
log filters or sanitize all unrelated host routes.

ETLantic 0.55.0 supplies upstream-safe HTTP 422 output through the exported
`RedactedValidationRoute` used by its router builder. Retain validation
rejection; unsafe original `input` and validation context must not be exposed.
ShuETL preserves that upstream route class in direct and mounted apps and keeps
unrelated host validation behavior unchanged.

### Required behavior — dependencies and serialization compatibility

Target Python remains 3.11/3.12/3.13; PostgreSQL remains 18.6, Psycopg/binary
3.3.5, SQLAlchemy 2.0.52, and migration head `005_cp1_reference`. No auth/IdP/JWT
client, AuthMate, session ORM, or cryptographic library is added to core or a
ShuETL extra. Host examples consume verified identity through callbacks.

Retain the existing exact non-ETLantic pins. ETLantic core/FastAPI/SQLModel are
pinned to the published 0.55.0 train and qualified against its installed
artifacts. The SQLModel migration head and provider protocol are unchanged. If
a future upstream release requires a new schema head, protocol, or additional
dependency, amend this contract rather than widening compatibility silently.

No ShuETL persistence or data migration is required for identity composition.
All domain serialization retains upstream formats. Document the intentional
security tightenings: production raw header demos rejected, production prebuilt
APIs require guarded callbacks, malformed contexts rejected, and qualified
upstream list/422 behavior corrected. Genuine legacy PostgreSQL host callback
syntax remains supported via normalization. Existing local raw callbacks,
mount prefixes, provider ownership, database upgrade/doctor CLI, and healthy
database behavior remain compatible.

### Recommended implementation

- Keep adapter guards/callable metadata in `identity.py`; use closures with a
  private ownership marker to recognize matching guarded principal/context
  pairs. Markers are composition evidence within trusted Python, not an
  authentication credential or a new global registry.
- Implement the output guard as a native `Depends(original_host_dependency)`
  callable with a concrete runtime signature. Test postponed annotations and
  security-scheme discovery rather than solving dependencies manually.
- Reuse upstream refs, keys, error constructors, and the static-context helper.
  Avoid Pydantic look-alike models and generic object-to-dict conversion.
- Share security preflight between bundle creation and facade construction/mount;
  run it before the existing optional import/engine/router mutation seams.
- Bind test inventories to operation IDs and normalized source-derived actions;
  parameterize route denial cases with valid body/path fixtures and recording
  authorizer/store doubles.

Required observable behavior takes precedence over these internal recommendations.

## Invariants, edge cases, security and reliability

1. Host credential verification is mandatory in host mode and cannot be inferred
   from a `Principal`'s existence. No omitted value selects static identity.
2. A valid guarded principal remains the exact principal in its upstream context;
   no cross-request identity/context cache exists in ShuETL.
3. Context membership is host-authoritative; caller-selected routing data confers
   no authority. Workspace and tenant refs always agree.
4. Authentication/context failure prevents all protected service/store use.
   Authorization occurs before business lookup; denied operations never mutate.
5. Collection permission does not override a concrete item list denial.
6. Dependency/policy/provider outage never activates development or memory fallback.
7. Native FastAPI owns principal dependency execution, caching, and resource cleanup.
   Cancellation propagates; no `BaseException` suppression or orphan background task.
8. The facade retains its exact caller API and does not acquire provider ownership.
9. No gateway secret resolution, credential persistence, or execution takes place.
10. Upstream records, schema/error identity, transaction boundaries, and migration
    ownership are preserved; changes to list/422 semantics require published fixes.

| Relevant case/failure | Required result |
|---|---|
| Adapter/raw callbacks omitted or mixed | Constant construction `TypeError`, before engine/app mutation. |
| Native async/yield/keyword-only principal dependency | FastAPI executes and cleans up normally; resolved Principal is guarded. |
| Async/generator context factory | Rejected before construction; no coroutine execution or bridge. |
| Invalid/blank principal, invalid kind/issuer, dict/ORM/token output | Constant upstream 401, no context/service/store use or rendering input. |
| Context substitutes principal or malformed/mismatched refs | Constant upstream 503; no protected use and no fallback. |
| Missing/unapproved membership | Host sanitized upstream authentication/authorization failure; no default workspace. |
| Forged X-Principal/issuer/scope headers alongside valid host identity | Host identity and server membership remain authoritative. |
| Explicit development-static under PostgreSQL or production prebuilt API | Rejected before connection/mount; no production bypass. |
| Legacy local demo callbacks | Existing behavior retained and labeled development-only. |
| API guard pair reassigned/mismatched before mount | Readiness failure before host state/routes/handlers/cache mutation. |
| Parallel requests by different principals/scopes | Each authorizer/store receives the corresponding context; no identity bleed. |
| Collection wildcard allow plus concrete denial | Denied item omitted before existing bounds; PB-001 prerequisite. |
| Same-tenant foreign workspace or foreign tenant | No protected records/metadata/events disclosed despite collection rights. |
| Foreign run or cursor, absent run, unauthorized artifact metadata | Preserve upstream opaque run denial and cursor 410 where authorized. |
| SSE disconnect or failure after headers | Native teardown/termination, no new success frames or remapped HTTP status. |
| Host/policy outage before authorization | Sanitized failure; no lookup/mutation; no fallback. |
| Provider outage after authorization | Failed operation; upstream committed-state/transaction semantics remain authoritative. |
| Invalid credential-bearing HTTP input | Rejected with safe upstream 422; PB-002 prerequisite. |
| Repeated adapter access/bundle close | Stable dependency callable identity; existing close remains idempotent. |
| Existing migrated database/restart/upgrade | Same 0.4 canonical state and migration contract; no identity migration. |

Host deployments must keep FastAPI debug disabled, validate bearer credentials
for the correct issuer/audience/use/expiry, and reject failed verification. OIDC
ID-token validation belongs to the host's OIDC flow; an ID token is not treated
as an arbitrary gateway bearer access token. Session hosts own cookie security,
expiry/revocation, CSRF protections for mutations, proxy trust, and TLS. Examples
must state which host controls are assumed rather than claim a built-in IdP.
These references inform the host recipes, not new core features:
[FastAPI security dependencies](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
and [OIDC Core validation](https://openid.net/specs/openid-connect-core-1_0-18.html#IDTokenValidation).

## Acceptance criteria

| ID | Observable acceptance criterion |
|---|---|
| AC-001 | 0.5 source/wheel metadata and exact lock identify Python 3.11–3.13, the recorded corrected ETLantic train, unchanged qualified database pins, and no core/extra authentication client dependency. |
| AC-002 | All 0.4 top-level exports remain in order and only `HostIdentityAdapter` is appended; no principal/context/token/policy shadow schema appears. |
| AC-003 | Host adapter accepts native sync/async/keyword-only/nested Security/Depends/yield principal dependencies without executing them at construction; FastAPI owns their execution and teardown. |
| AC-004 | Adapter properties retain stable callable identity, immutable mode metadata, and bounded repr without principal/callable/credential contents. |
| AC-005 | Missing/wrong/malformed Principal output returns the specified upstream 401 and invokes no context factory or protected service/store. |
| AC-006 | Valid subject/issuer/kind and Principal object identity reach the context factory and canonical context unchanged. |
| AC-007 | Async/generator/nonconforming context factories fail at construction; malformed/mismatched context output or unexpected factory failure returns the specified constant 503 before protected use. |
| AC-008 | Guarded context preserves all accepted upstream scope/key objects and never substitutes caller-provided tenant/workspace/environment/security-domain authority. |
| AC-009 | Bundle factories accept exactly adapter or a complete raw callback pair and reject missing/mixed forms or a nonconforming authorizer before engine/app mutation. |
| AC-010 | Genuine legacy PostgreSQL host callbacks normalize through host guards; known upstream header-demo dependencies and development adapters are rejected in production. |
| AC-011 | `development_static` supplies only its validated fixed Principal/scope, still requires an authorizer, and is usable only with explicit local `development-static` settings. |
| AC-012 | Existing settings/default/source/URL/TLS behavior remains; `development-static` is the sole added identity value, required explicitly and rejected outside local profiles. |
| AC-013 | Production/unknown-profile prebuilt APIs require a matching host guard pair and conforming authorizer at construction/mount; failure leaves host routes/state/handlers/lifespan/OpenAPI unchanged. |
| AC-014 | The facade retains the exact API; bundles retain native store/caller-authorizer objects, one shared engine, explicit lifecycle ownership, and existing failure/cancellation/idempotent-close behavior. |
| AC-015 | Dependency overrides can target the original host callable and guarded upstream dependencies, can be removed normally, and preserve native security-scheme discovery/OpenAPI parity. |
| AC-016 | Every mounted POST/PUT/PATCH/DELETE has a route-inventory-bound well-formed denial proof recording exact upstream action/resource/context before business lookup and demonstrating zero mutation; missing optional providers do not bypass denial. |
| AC-017 | Direct definition/run/registry/schedule/report/lineage/artifact-metadata probes preserve upstream 403/404 disclosure and reveal no protected cross-scope existence/content; only the documented caller-scoped run probe may follow denial. |
| AC-018 | Collection denial prevents lookup, and wildcard collection allowance does not expose concrete list-denied definitions/workspaces or foreign-scope protected items. |
| AC-019 | Applicable item filtering occurs before existing limit/result-bound operations, so denied items occupy no result slots or reported totals/cursors; no new pagination API appears. |
| AC-020 | Concurrent requests with different host principals/scopes deliver their own Principal/context to authorization/stores without request-state leakage or ShuETL global identity caching. |
| AC-021 | SSE authorizes before cursor/event access, preserves foreign-run denial and authorized unknown/foreign-cursor 410, existing resume precedence/envelopes/follow caps, and dependency teardown on disconnect. |
| AC-022 | Existing acceptance-receipt artifact metadata is protected by `run.artifacts` before lookup; no artifact download/signing/storage implementation is added. |
| AC-023 | Host/membership/policy outages and required-provider failures yield unsuccessful sanitized responses and no identity/provider fallback, unauthorized mutation, fabricated acceptance, or partial-success list/stream. |
| AC-024 | Guarded triggering subject/issuer/kind persists in upstream durable submission metadata when that path is used; host tokens/cookies do not enter payloads/schedules and are not used as execution credentials. |
| AC-025 | Instrumented gateway validate/plan/submit/schedule, composition/startup and doctor flows invoke no pipeline-secret resolution or pipeline executor. |
| AC-026 | Recognized credential-bearing inputs/sentinels are absent from the specified validation/problem/HTTP-422/log/event/SSE/readiness/doctor/OpenAPI/repr surfaces; invalid input still fails validation. |
| AC-027 | Doctor keeps its schema/shape/check order/exits and safely distinguishes configured host mode, inspected adapter mode and explicit local static development mode without authenticating or exposing identity/scope values. |
| AC-028 | OIDC and session recipes consume already validated host identity through native dependencies, state host verification/CSRF/expiry requirements, reject invalid/outage cases in synthetic smoke harnesses, and add no credential validator to ShuETL. |
| AC-029 | Existing local raw-callback, PostgreSQL persistence/restart/migration/idempotency/concurrency, CLI, mount/lifecycle/handler and OpenAPI contract assertions pass, except the explicitly documented production-security and corrected upstream list/422 changes. |
| AC-030 | Core/SQLite/PostgreSQL clean-wheel environments resolve exports from the wheel and execute a 0.5 identity smoke example without undeclared auth packages or repository-source imports. |
| AC-031 | Ruff, Pyright, lock, boundary, unit/security/integration, build, artifact, OpenAPI and release/evidence gates pass; real PostgreSQL and 0.5 security tests execute on Python 3.11/3.12/3.13 in CI without required-test skips. |
| AC-032 | A 0.5 evidence index maps each AC exactly once to its actual proof and limitations, binds the approved route/AC inventory and corrected train, rejects copied/unrelated/missing proofs, and contains no secrets or machine-specific paths. |
| AC-033 | Published upstream artifacts fix PB-001 with concrete collection-resource contracts, and installed-package tests demonstrate AC-018/019 through direct and ShuETL-mounted graphs. |
| AC-034 | Published upstream artifacts fix PB-002 through a documented public seam, preserving safe HTTP-422 validation and unrelated host validation behavior in direct and embedded apps. |

## Verification matrix

Preferred proofs below define eventual release evidence; they are not claims
that the implementation or tests exist now. Security tests use synthetic
credentials and recording providers and run in both root and prefixed mount
modes. Real-database cases use disposable isolated databases only.

| AC | Preferred proof and required demonstration |
|---|---|
| AC-001 | Static Gate / Compatibility — source, lock, installed distribution and wheel dependency metadata. |
| AC-002 | Contract / Static Gate — exact exports, wheel import assertions and absence of shadow schemas. |
| AC-003 | Unit / Integration — native dependency-shape table, startup invocation counter, async/yield enter/exit and nested Security/Depends cases. |
| AC-004 | Unit — frozen metadata/property identity and credential/callable/principal repr sentinels. |
| AC-005 | Unit / Integration — malformed upstream dataclass and foreign output matrix, exact 401, zero factory/store calls. |
| AC-006 | Contract — identity/issuer/kind equality and `is` assertions at factory/authorizer boundaries. |
| AC-007 | Unit / Integration — synchronous-shape rejection plus wrong-output/mismatched-principal/ref and exception injection; exact constant 503. |
| AC-008 | Contract / Property — scope/ref/key round trips and forged path/query/body/header authority variations. |
| AC-009 | Unit — adapter/raw combination matrix, authorizer callability/signature checks and engine/mutation spies. |
| AC-010 | Compatibility / Security Integration — genuine raw host path, both qualified upstream demo helper forms, static adapter rejection before driver/engine use. |
| AC-011 | Unit / Integration — fixed principal/scope despite forged headers, local static app and authorizer requirement. |
| AC-012 | Unit / Compatibility — identity/profile/provider matrix plus existing immutable settings/precedence/redaction suite. |
| AC-013 | Unit / Integration — production/Profile/unknown-profile classifier table, mismatched/reassigned guards and before/after host snapshots. |
| AC-014 | Contract / Compatibility — native graph/object/engine identities, unchanged facade API, failure/cancellation disposal and repeated/concurrent close counters. |
| AC-015 | Contract / Integration — override/remove original and guard callables; compare direct and mounted OpenAPI for identical security dependency graphs. |
| AC-016 | Integration / Static Gate — generated route-set equality and per-mutation valid-request deny cases, recorded actions/resources/order and unchanged state. Include AI/schedule/optional routes. |
| AC-017 | Integration — existing/missing/foreign tenant and same-tenant foreign workspace matrix with scoped read spies; preserve upstream disclosure distinctions. |
| AC-018 | Upstream Contract / Integration — native memory and relational lists with collection denial, wildcard allowance and explicit item list denials. |
| AC-019 | Contract / Integration — permitted/denied candidates around existing limit boundaries; applicable list contract fixtures prove filtering occurs first. Non-paginated routes remain non-paginated. |
| AC-020 | Integration / Concurrency — synchronized ASGI requests with separate contexts and authorizer/store observations; include async host dependencies. |
| AC-021 | Integration — unauthorized stream/cursor lookup counters; foreign cursor 410, valid replay, bounded follow and real ASGI disconnect/teardown. Buffered TestClient alone is insufficient for disconnect proof. |
| AC-022 | Contract / Integration — run.artifacts action/lookup ordering, absent/foreign run and exact acceptance-receipt metadata schema. |
| AC-023 | Integration / Failure injection — safe host/membership/policy 503 and store failure cases, before/after state, no fallback; streaming failure after headers terminates safely. |
| AC-024 | PostgreSQL Integration / Contract — canonical submission subject/issuer/kind readback after restart plus schedule/durable payload scans with synthetic bearer/cookie sentinels. |
| AC-025 | Static Gate / Integration — spies on installed public secret-resolution/execution seams, actual canonical pipeline validation/planning fixtures and startup/doctor flows; stubs alone are insufficient. |
| AC-026 | Unit / Upstream Contract / Integration — sentinel scans of valid/error/malformed body/query/header responses, captured gateway logs, upstream events/SSE, OpenAPI and diagnostic/repr output. |
| AC-027 | Unit / Contract — host config-only/bundle/static/mismatch golden reports, unchanged fields/check order and no auth/policy/secret invocation spies. |
| AC-028 | Integration / Manual — executable verified-identity host smoke examples, missing/invalid/expired/outage fixtures, recipe review against linked host-auth standards. No live IdP claim. |
| AC-029 | Compatibility / Migration — preserve prior contract assertions; rerun full suite and real PostgreSQL 0.4 restart/migration/concurrency qualification on the corrected train. |
| AC-030 | Integration / Artifact — isolated wheel extras, copied smoke harness, empty PYTHONPATH and installed-origin/dependency checks. |
| AC-031 | Static Gate / CI Integration — prescribed one-command release gate and executed current-change CI matrix; configured YAML alone is insufficient. |
| AC-032 | Static Gate / Contract / Manual audit — 34 AC bindings, semantic proof review, exact route coverage, negative missing/unrelated/recycled-proof fixtures and sanitized artifacts. |
| AC-033 | Upstream Contract / Compatibility — inspect exact published correction and run installed-wheel list-denial/bound-order probes through direct and mounted adapters. |
| AC-034 | Upstream Contract / Integration — inspect exported validation composition seam and exercise safe 422 plus unrelated host route/custom-handler behavior. |

## Implementation phases

### Phase 0 — Resolve and qualify upstream prerequisites (complete)

- Goal: obtain a published train that satisfies the planned security boundary.
- Modules: upstream work tracked by PB-001/PB-002, not ShuETL route/store code.
- Required behavior: fix concrete list-denial/bound ordering and safe validation
  output; document collection-resource contracts and public validation seam.
- Tests: installed-artifact reproductions in direct/mounted modes; rerun 0.4
  real PostgreSQL migration/restart/concurrency and redaction qualification.
- Documentation/configuration: planning owner records exact versions, exports,
  public 422 representation, and fixture requirements here. Do not bump ShuETL
  dependencies to an unreleased checkout or advertise readiness yet.
- Dependencies: none. Published artifacts qualified on 2026-09-29; issues
  #143/#144 remain open, but issue status was not used as a substitute for
  artifact inspection and behavior probes.

### Phase 1 — Identity adapter and runtime guards (implemented)

- Goal: implement the one composition object and stable native dependency guards.
- Modules: `identity.py`, `__init__.py`, focused `tests/unit/test_identity.py` and
  `tests/integration/test_identity_dependencies.py`.
- Required behavior: AC-002–008; host/static factories; no auth implementation.
- Tests: principal/context boundaries, native async/yield/nested dependency
  lifecycle, stable callable identity, factory failure, and repr redaction.
- Documentation/configuration: API reference and the fixed ADR-0011 decision;
  no database migration or new dependency.
- Dependencies: Phase 0's recorded upstream interfaces.

### Phase 2 — Bundle/profile/facade security preflight (implemented)

- Goal: enforce production guards and explicit local static separation.
- Modules: `providers.py`, `integration.py`, `settings.py`, `diagnostics.py`;
  production identity fixtures and focused preflight/doctor tests.
- Required behavior: AC-009–015 and AC-027; normalize genuine legacy PostgreSQL
  callbacks, preserve legacy local form, never mutate a caller API or host app
  on rejection. Compose PB-002's exact public seam if registration is required.
- Tests: settings/input/profile matrix, authorizer shapes, known demo rejection,
  mismatched guards, graph identity, cleanup, overrides and OpenAPI parity.
- Documentation/configuration: raw-to-adapter upgrade examples, production
  security tightenings, doctor's config-only limits; no identity/data migration.
- Dependencies: Phase 1 and the Phase 0 validation seam.

### Phase 3 — Authorization inventory and adversarial qualification (implemented)

- Goal: prove every mounted mutation and the relevant enumeration boundaries.
- Modules: `tests/security/` or narrowly organized integration security modules;
  route/fixture/proof inventory under 0.5 evidence.
- Required behavior: AC-016–023, AC-033/034; preserve upstream semantics rather
  than adding downstream permissions/filtering/errors.
- Tests: all-mutation denial, both tenant/workspace attacks, direct/list/bounded
  list, SSE cursor/disconnect, artifact metadata, and safe host/policy/provider
  outage matrices. Optional providers need denial/unavailable proofs only.
- Documentation/configuration: complete operation/action/resource inventory and
  explicit optional capability/SSE lifetime limitations. No new production model.
- Dependencies: Phases 0–2.

### Phase 4 — Triggering identity and secret boundary (implemented)

- Goal: prove identity propagation without gateway credentials or execution.
- Modules: canonical pipeline/security fixtures and PostgreSQL security tests;
  existing upstream secret/execution seams are instrumented only in tests.
- Required behavior: AC-024–026; no host token persistence or secret resolution.
- Tests: actual canonical validate/plan/submit/schedule requests, no-resolution
  spies, durable subject/issuer/kind restart readback, malformed credential
  inputs, logs/events/SSE/readiness/OpenAPI sentinel scans.
- Documentation/configuration: triggering versus execution identity and approved
  single identity namespace; do not add secret/provider settings or migrations.
- Dependencies: Phase 3 and real PostgreSQL fixtures.

### Phase 5 — Host recipes and upgrade documentation (implemented)

- Goal: publish runnable composition recipes without implementing an IdP.
- Modules: `examples/phase_0_5_oidc_host.py`,
  `examples/phase_0_5_session_host.py`, explicit local static example, README,
  the PostgreSQL auth example, changelog and security/identity design links.
- Required behavior: AC-028 and AC-029 documentation portions. Recipes receive
  verified host principals; synthetic test harnesses are prominently local/test
  fixtures. No unverified claim decoder or demo header becomes production auth.
- Tests: copied wheel examples with success/missing/invalid/expired/outage cases.
- Documentation/configuration: host issuer/audience/use/expiry/session/CSRF/TLS
  assumptions, dependency overrides as trusted test/admin code, and production
  callback/context upgrade notes. No live provider/network setup is required.
- Dependencies: Phases 1–4.

### Phase 6 — Release packaging, CI, evidence and regression (implemented locally)

- Goal: qualify a reproducible 0.5 artifact against the bounded contract.
- Modules: `pyproject.toml`, lock, `compatibility.py`, scripts, existing workflows,
  `docs/evidence/0.5/`; focused release/evidence checker tests.
- Required behavior: AC-001, AC-029–032. Set ShuETL 0.5.0 only during implementation;
  update install remediations. Evidence validator explicitly selects the 0.5
  plan and 34 ACs, applies the proof registry's semantic integrity rules and
  recognizes 0.5 qualification decisions; retain older evidence validation.
- Tests: full quality/release gates, exact wheel contents including `identity.py`,
  native dependency smoke in all wheel extras, real database regression and
  security tests in the executed Python 3.11/3.12/3.13 CI matrix. Required live
  jobs must fail for a missing database/test skip instead of silently passing.
- Documentation/configuration: exact artifact hashes/import origins, actual
  server/version/CI run, limitations and every AC-to-proof binding. No proof is
  marked PASS because a previous release used the same AC number.
- Dependencies: Phases 0–5. Publishing/tagging is separate release work.

## Risks

| Risk | Mitigation / release rule |
|---|---|
| Upstream issue status remains open after correction artifacts publish | Qualify the exact installed 0.55.0 wheels and direct/mounted behavior; issue closure is informational, not the artifact gate. |
| Future upstream fix introduces new API/schema/dependency decisions | Planning owner amends the exact compatibility/public-seam section before Luna proceeds; no silent scope expansion. |
| A callable is mistaken for proof of credential validation | Explicit host trust contract, demo misuse rejection and verified-identity recipes; no claim against malicious same-process code. |
| Native dependency graph is flattened by a direct-call wrapper | Depends on the original callable; async/yield/keyword-only/Security/override proofs. |
| ContextFactory is treated as async despite upstream synchronous execution | Reject async/generator factories; perform asynchronous host membership lookup upstream in FastAPI dependencies. |
| Issuer collisions through subject-only membership/idempotency | Single approved namespace; host issuer-aware mapping and namespaced subjects; no multi-issuer isolation claim. |
| List filtering consumes an already truncated candidate set | Upstream bound-order proof is mandatory; no downstream post-pagination filter. |
| Non-enumeration tests demand behavior upstream never promised | Preserve disclosure contract and caller-scoped run probes; verify absence of protected foreign-scope content rather than all-string equality. |
| SSE authorization is assumed to refresh continuously | Document connect/reconnect authorization and bounded host connection lifetime; no token-refresh/revocation guarantee midstream. |
| Generic exceptions or host logs disclose credentials | Adapter guards use constants/no input logging; host dependencies own safe failures/logging; upstream 422/redaction proof required. |
| Production security tightening breaks demo fixtures/users | Explicit upgrade notes; keep genuine raw PostgreSQL syntax and local legacy behavior; adapt identity fixtures while preserving substantive assertions. |
| New evidence recycles older IDs or only verifies configured CI | Release-specific plan/proof/route binding, negative evidence tests and executed current-change CI evidence. |

## Explicit non-scope

- User databases, login/logout routes/UI, token issuers/validators, OIDC discovery,
  JWT decoding/cryptography, session storage, role/permission engines or secret
  managers; AuthMate/Hedron/client-library dependencies and extras.
- Unauthenticated or header-demo production access, caller-selected membership,
  automatic anonymous fallback, or allow-all policy creation.
- ShuETL authorizer/store wrappers, new permission names, concrete list filtering,
  HTTP error schemas, ETLantic routes, or fixes copied from upstream source.
- General async ContextFactory support or manual FastAPI dependency solving.
- General pagination, new route presets, rate limiting, request-size middleware,
  continuous SSE token refresh/reauthorization, a log-scrubbing platform or
  unrelated host-route security redesign.
- Artifact downloads/previews/signing/storage, full report/governance/AI semantic
  qualification, worker/scheduler supervision, pipeline execution or execution
  secret resolution. Denial coverage of mounted optional routes remains in scope.
- Multi-tenant/HA/performance qualification, mutually untrusted in-process code,
  multi-issuer canonical-key redesign, database/table/migration changes, new
  PostgreSQL/driver versions, exactly-once external effects, or disaster-recovery
  automation.
- Broad cleanup of the repository/design pack or existing warning/action-runtime
  follow-ups unrelated to this release boundary.

## Known pre-existing problems and follow-up candidates

### Qualified upstream prerequisites

**PB-001 — Concrete list denial is ignored.**
Tracked as [ETLantic #143](https://github.com/eddiethedean/etlantic/issues/143).
The 0.52.1 reproducer showed that collection grants exposed an explicitly
list-denied definition. Published ETLantic 0.55.0 now calls `visible_items` and
`visible_limited_items` to apply concrete item decisions before returning
results and before consuming existing limits. Direct wheel probes confirm the
hidden definition is absent from a collection-granted list. The issue remains
open; 0.55.0 artifact behavior is the qualification evidence for AC-018/019/033.
Most lists remain unpaginated; this does not authorize a new pagination API.

**PB-002 — HTTP validation echoes credential-bearing original input.**
Tracked as [ETLantic #144](https://github.com/eddiethedean/etlantic/issues/144).
The 0.52.1 reproducer showed the original nested body in a default validation
detail. The published 0.55.0 `RedactedValidationRoute` is exported by
`etlantic_fastapi`, selected by `build_control_plane_router`, and responds with
a fixed 422 detail that omits the original input. Direct and mounted app probes
confirm the password sentinel is absent while an unrelated host route retains
its ordinary FastAPI 422. The issue remains open; artifact behavior is the
qualification evidence for AC-026/034.

### Follow-up only

- [ShuETL #1](https://github.com/eddiethedean/shuetl/issues/1): deprecated Node.js
  action runtimes. Existing workflows still use older action tags; 0.5 workflow
  label/test edits do not require solving this independent warning.
- [ShuETL #2](https://github.com/eddiethedean/shuetl/issues/2): test transport /
  BlockingPortal deprecations. `httpx2` is already the active test dependency;
  the AnyIO alias warning remains in the local passing baseline. Separate issue
  triage may narrow its remaining scope.
- [ETLantic #130](https://github.com/eddiethedean/etlantic/issues/130): stale
  upstream package docstring version; documentation-only and unrelated.
- Future upstream async context, issuer-qualified idempotency, continuous stream
  reauthorization, general pagination, and full artifact access qualification
  need separate contracts when those capabilities are first claimed. They are
  deferred enhancements, not required repairs for the bounded single-namespace
  0.5 profile.

Do not manufacture issues for speculative future enhancements. Existing open
issues above satisfy duplicate/reference triage for confirmed unrelated findings.

## Definition of done and implementation decision

This change is done when every AC-001 through AC-034 is demonstrated, required
0.4 compatibility remains, documentation matches the actual guarded/qualified
behavior, current-change required gates pass on supported runtimes, and no
substantive regression or attributable release blocker remains. Independently
confirmed pre-existing warnings/failures outside the boundary are recorded and
do not demand unrelated repairs. The repository need not be globally defect-free.

The 0.55.0 upstream artifacts satisfy both previously blocking prerequisites.
The 34 criteria have qualification evidence, including a three-version Python
matrix, real PostgreSQL 18.6 integration, and hosted run
[36654931532](https://github.com/eddiethedean/shuetl/actions/runs/36654931532)
for the initial baseline. AC-017 was added afterward and passed locally, then
passed in the final pre-tag and tag-triggered release runs. ShuETL 0.5.0 was
published through Trusted Publishing; artifact hashes and workflow records are
in [the Phase 0.5 evidence index](../evidence/0.5/README.md).
