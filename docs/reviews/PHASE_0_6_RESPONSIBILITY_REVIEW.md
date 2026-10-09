# Phase 0.6 responsibility review

Follow-up, 2026-10-09: ETLantic 0.57.0 publishes all five requested contract
surfaces. The [candidate audit](ETLANTIC_0_57_CANDIDATE_AUDIT.md) records artifacts,
upstream conformance and independent headless/gateway checks. [Coverage acceptance](../evidence/0.6/coverage-acceptance.md) closes Gate U;
exact pins and PostgreSQL role feasibility pass. Role implementation/release
qualification remain open. The findings below are
historical evidence, not current 0.57.0 API-gap claims.

Follow-up, 2026-10-08: the ownership recommendations are adopted in
[ADR-0015](../adr/0015-backend-and-deployment-ownership.md) and the revised 0.6
plan. A subsequent isolated 0.56.2 probe confirmed the version-inspection DDL
fix from [#273](https://github.com/eddiethedean/etlantic/issues/273). Remaining
upstream changes are filed as [#278–282](../plans/ETLANTIC_0_56_DEPENDENCIES.md).
The findings below retain their original 0.56.0 scope; final upstream selection
and all deployment qualification remain pending.


Date: 2026-10-08
Status: Recommendations for review; does not amend an accepted ADR or release contract.

## Recommendation

Keep ShuETL as the opinionated application-integration and deployment product.
Keep ETLantic and its providers independently usable as a complete ETL backend.
Reduce the amount of ETL correctness that depends on ShuETL assembling the right
objects and callbacks. Move transport-independent backend construction out of
`etlantic-fastapi`, schedule command orchestration into ETLantic services, and
schema inspection into the persistence provider.

ShuETL has a distinct purpose: turn a qualified ETLantic backend into a configured,
authenticated, supervised deployment with explicit lifecycle ownership and a
tested operating envelope. It need not own pipeline semantics or be the only way
to run ETLantic to justify a separate package.

The useful dividing question is: **Would getting this code wrong change the
meaning, authorization, identity, durability, or recovery of an ETL operation?**
If so, its authoritative implementation belongs in ETLantic or its provider.
Deployment choices and host integration belong in ShuETL. Deployment still
requires safety tests, but should consume explicit upstream guarantees.

## Scope and evidence

- ShuETL checkout: `d07fa10ead8ad2ec3fd6da381aa0c034cdbc1b7f`, version 0.5.0,
  including the proposed 0.6 execution contract and ADR-0014.
- Both adjacent ETLantic checkouts still identify as 0.55.0; they are not evidence
  of the selected 0.56 implementation.
- Inspected installed `etlantic`, `etlantic-fastapi`, and `etlantic-sqlmodel`
  distributions at exact version 0.56.0 in an isolated Python 3.13 environment.
- Ran focused public-API probes against a newly created temporary SQLite store
  migrated to `014_cp1_complete_principal_idempotency_0_56`. No existing database
  or application data was used. These probes establish API and construction
  behavior, not PostgreSQL or multiprocess qualification.

Upstream references below identify files inside those installed distributions:

| Evidence | File and relevant location |
| --- | --- |
| U1 | `etlantic_fastapi/managed.py`: `ManagedBackendConfig` at 51, `ManagedBackend` at 184, `create_managed_backend` at 340 |
| U2 | `etlantic_fastapi/api.py`: `enable_managed_execution`, which constructs `ManagedApplicationService` |
| U3 | `etlantic_fastapi/schedule_routes.py`: `create_schedule` at 52, amendment/preview handlers, `trigger_schedule` and its prepare/claim/submit/link sequence |
| U4 | `etlantic/runtime/scheduler_service.py`: constructor at 43, callback-owner discovery at 83–115, `ready` at 122 |
| U5 | `etlantic/runtime/execution_host.py`: `drain` at 251 and `tick` at 267; `etlantic/runtime/action_execution_host.py`: class at 74 and `tick` at 133 |
| U6 | `etlantic_sqlmodel/migrations/__init__.py`: `current_version` issues `CREATE TABLE IF NOT EXISTS`, commits, then selects the version |
| U7 | `etlantic/service/managed.py`: existing canonical definition, preparation, submission, lifecycle, report, artifact, and scheduled-occurrence services |

Observed probe results:

```json
{
  "managed_backend_schedule_store": "NoneType",
  "managed_backend_scheduler_factory": false,
  "backend_requires_http_context_factory": true,
  "bound_method_discovers_preparer": true,
  "bound_method_discovers_recoverer": true,
  "wrapped_method_discovers_preparer": false,
  "wrapped_method_discovers_recoverer": false,
  "current_version_issues_ddl": true,
  "execution_host_has_ready": false,
  "action_host_has_drain": false
}
```

The callback probe constructed schedulers with a test object's bound submission
method and a lambda forwarding to the same method. It invoked no ticks or ETL.
The DDL probe recorded statements from `current_version` on the disposable store.
Construction used `create_managed_backend`, `ManagedBackendConfig`,
`MemoryAuthorizer`, and `static_context_factory`; the latter two were local test
inputs, not a proposed production configuration.

## Findings and recommended shifts

### R1 — Put the standard backend below the HTTP adapter

**Priority: resolve before freezing the new 0.6 public API.**

U1's headless backend owns an `ETLanticAPI`, requires a FastAPI context factory,
and reaches application services through `backend.api.managed_service`. Its
configuration mixes database, artifact, retention, action-handler, and HTTP
title/version settings. The API object itself constructs the application service
(U2). ADR-0014 consequently requires runtime bindings to supply `context_factory`
even though scheduler and worker roles have no HTTP request.

Move the transport-independent backend handle and role contracts into ETLantic's
service/runtime layer. Put the concrete SQLModel graph and engine construction
in `etlantic-sqlmodel` (or a deliberately separate upstream composition package).
This preserves optional SQL dependencies. Expose the service and stores without
an intervening HTTP object. Keep an API/app adapter in `etlantic-fastapi` that
accepts the already constructed backend plus HTTP identity dependencies.

ShuETL selects the qualified backend, passes deployment configuration, mounts the
adapter, and owns resources it creates. It should not reconstruct the upstream
graph store by store. Keep old upstream factory imports as delegating compatibility
entry points where practical; do not maintain two graph implementations.

**Proof:** construct headless services, scheduler, and workers without a Request,
HTTP context factory, principal dependency, or FastAPI application. Ideally the
upstream headless installation does not require `etlantic-fastapi` at all.
ShuETL itself may retain its FastAPI dependency for backward compatibility.

### R2 — Move schedule commands from HTTP handlers into public ETLantic services

**Priority: required before claiming complete HTTP/headless schedule parity.**

U3 does more than HTTP adaptation. Schedule creation resolves revision policy,
authorizes workload binding, computes a policy fingerprint and initial firing
time, and writes the store. The trigger route coordinates preparation, firing
claim, submission, and linking. Amendment also computes the next firing time.
U7 has important scheduled-occurrence helpers, but its managed service does not
provide the complete create/amend/pause/resume/preview/trigger command surface.

Move this command orchestration and its authorization into a public ETLantic
schedule service, or extend the existing application service. HTTP retains
request parsing, response serialization, status codes, headers, and error
translation. ShuETL must not fill the headless gap by invoking route functions,
accessing stores directly, or copying these algorithms.

**Proof:** the same command through Python and HTTP produces the same authorization
decisions, revision/firing/submission identities, conflicts, and recovery behavior.
Calling the store directly is not evidence of an authorized headless service.

### R3 — Make managed scheduler construction an upstream responsibility

**Priority: required before releasing the standard scheduled deployment.**

The 0.56 factory leaves `backend.api.schedule_store` unset and has no scheduler
factory (U1 and executable probe). ADR-0014 assumes a backend schedule store and
requires ShuETL to pass exactly the bound `submit_scheduled_run` method. U4
discovers preparation and recovery by inspecting the callback's `__self__`.
A forwarding lambda preserves invocation but loses both discoveries.

Add upstream construction for the complete managed scheduler, including the
provider's schedule store on the shared engine/store identity, profile, and
submission/preparation/recovery integration. Replace implicit callback-owner
discovery on the standard path with an explicit upstream contract, or encapsulate
it inside the upstream factory until it can be replaced. A missing recovery
participant must fail construction, not silently weaken semantics.

ShuETL supplies the chosen role, scoped service context, unique process owner,
and deployment timing configuration, then invokes the completed role. It can
still instantiate providers through public APIs for advanced integrations;
the standard path must not depend on such correctness-sensitive assembly.

**Proof:** standard factory construction includes schedules, and callers cannot
accidentally disable managed preparation/recovery by decorating a callback.
Keep duplicate-scheduler and crash/link recovery tests upstream and repeat
representative cases through ShuETL's installed processes.

### R4 — Move schema knowledge and read-only inspection into the provider

**Priority: fix before expanding the workaround in 0.6.**

[ShuETL's PostgreSQL module](../../src/shuetl/postgresql.py) duplicates the provider's
migration list, version-table layout and required table inventory, and queries
that private schema directly. SQLite inspection repeats related knowledge in
`providers.py` and `diagnostics.py`. U6 explains why: the upstream version reader
performs DDL. The 0.6 plan extends the duplication and accepts a special constructor
DDL exception.

Add a public, genuinely read-only schema/connectivity inspection API to
`etlantic-sqlmodel`, with provider-owned compatibility requirements and structured
safe results. Make standard construction use it. Keep version-table creation
inside explicit migrations. ShuETL consumes the result, applies its qualified
server/version policy, and renders operator remediation. The `shuetl database
upgrade` command may remain as a thin delegation to provider migration APIs.

This is a reason to revise the selected upstream baseline, not to add ShuETL
migrations or a richer SQL schema inspector. ShuETL may pin a required upstream
schema contract; it should not own the algorithm that recognizes it.

**Proof:** inspection and normal construction issue no DDL or commits and work
under real runtime grants; missing, partial, unknown, and incompatible schemas
fail before admission. Migration tests remain provider-owned.

### R5 — Split runtime lifecycle facts from process supervision

**Priority: freeze the contract before implementing W04.**

U4's scheduler `ready()` reports only its drain flag. The execution host has
`drain()` but no readiness method; the action host has neither. These facts do
not prove that a generic ShuETL supervisor is wrong. They do mean it cannot
derive runtime health or safe-stop guarantees from method names or a zero tick.

ETLantic should define observable admission/drain state, in-flight work behavior,
runtime prerequisites, lease monitoring and outcome/recovery guarantees. Add
documented capability/status and cooperative stop contracts where needed; do
not force an artificial identical implementation onto all roles.

ShuETL should retain process startup, signal handling, tick dispatch, polling
cadence, thread/process ownership, probe transport, evidence freshness, grace
budgets, and one-time resource cleanup. It combines upstream runtime/provider
facts with process state to decide deployment readiness. The external process
manager owns restarts, scaling, and forced termination.

A hard shutdown deadline never authorizes ShuETL to revoke a lease itself,
rewrite a run, declare cancellation complete, or close an engine under active
execution. Keep the current plan's explicit in-flight dispatch window.

**Proof:** every role documents and tests idle, active, standby, outage, drain,
grace-expiry and restart behavior. ShuETL observes these outcomes without
implementing another worker state machine.

### R6 — Separate canonical capabilities from deployment qualification

**Priority: clarify in the 0.6 acceptance plan.**

The broad phrase “ShuETL owns the supported backend experience” in ADR-0013 and
the capability-delivery documents can be read as ownership of every connector,
transform, quality rule, resource policy and run command. Those implementations,
schemas, plugin trust decisions, authorized discovery, and conformance suites
belong in ETLantic/provider packages. Much already lives there and should stay.

ShuETL owns the matrix of combinations it has tested and promises to support.
It may reject an unsupported deployment configuration with a clear diagnostic.
It should not introduce a competing connector catalog, action registry, ETL
profile, fingerprint, retention algorithm, or per-run policy model. Deployment
settings may carry canonical upstream objects and add stricter operating limits,
but must not silently discard supported upstream controls.

Keep live end-to-end tests for every advertised combination in ShuETL. Put
exhaustive transform, quality, connector, lease and recovery conformance upstream.
Distinguish *implementation evidence* from *deployment qualification evidence*;
neither replaces the other. AC-028–033 should identify both owners explicitly.

## Target ownership table

| Concern | Authoritative owner | ShuETL role |
| --- | --- | --- |
| Definitions, plans, fingerprints, canonical commands/results | ETLantic services/models | Expose the same objects and services |
| Manual/native-schedule preparation, admission, idempotency | ETLantic application/schedule services | Configure and invoke; no command sequencing |
| Claims, leases, fencing, retries, cancellation, recovery | ETLantic runtime/providers | Supervise and observe |
| Standard backend graph and correctness-preserving role factories | Transport-independent upstream backend; SQLModel graph in provider | Select/configure factory and own its lifecycle |
| Connectors, action handlers, transforms, quality, resource resolution | ETLantic/independent provider packages | Install/select qualified packages; test integration |
| Provider tables, schema compatibility and migrations | Persistence provider | Read public status; delegate explicit upgrade |
| HTTP routes, wire schemas, errors and SSE | `etlantic-fastapi` | Mount safely and compose host dependencies |
| Authentication and account/membership policy | Host/identity provider | Adapt authenticated identity; enforce composition guards |
| Canonical principal/context validity and operation authorization | ETLantic services | Reuse checks; do not rely on gateway-only validation |
| Role CLI, environment settings, process probes, shutdown orchestration | ShuETL | Implement and qualify |
| Supported topology, exact dependency pins, runbooks and compatibility matrix | ShuETL | Own the deployment promise |
| Business UI, credential enrollment and product workflows | Host | Provide integration contracts; no host coupling |
| Infrastructure provisioning, scaling and forced process termination | Operator/process manager | Supply recipes and process status |

Retain `HostIdentityAdapter` in ShuETL. Its FastAPI dependency composition and
local-only guard policy are useful integration behavior. Where structural
principal/context checks are needed by headless and runtime callers too, expose
and reuse canonical ETLantic validation rather than maintaining separate rules.
This is a boundary-hardening recommendation, not a finding that the existing
adapter authenticates tokens or that upstream authorization is absent.

## Proposed changes to the 0.6 plan

1. **Add an upstream contract gate before W01/W02.** Require the neutral backend,
   public schedule commands, complete managed scheduler construction, read-only
   provider inspection, and documented runtime lifecycle contracts. Proposed
   API names in this review are requirements, not claims of existing exports.
2. **Reconsider “0.56.0 as-is.”** The current exact-artifact decision and DDL
   exception are explicit. These recommendations would amend them. Use a newly
   published compatible ETLantic/provider release when the changes are available,
   then pin and requalify its exact artifacts. Do not patch installed wheels,
   silently float versions, or ship the missing semantic behavior in ShuETL.
3. **Revise ADR-0014 and W03.** ShuETL selects upstream role factories; it does
   not own their semantic assembly. Split gateway bindings from runtime bindings.
   Only gateway bindings contain a principal dependency, HTTP context factory
   and ASGI hook; runtime bindings contain trusted scoped service identity and
   applicable resource/policy bridges.
4. **Rewrite AC-007/026 around outcomes and upstream contracts.** Replace the
   bound-method instruction with complete managed scheduling and recovery
   requirements. Add the missing schedule-store construction proof.
5. **Revise AC-008.** Consume provider-owned inspection and remove constructor
   DDL once the upstream fix is selected. Preserve explicit migration privileges,
   fresh-store transition, and failure on incompatible schema.
6. **Strengthen AC-027/029.** Test headless schedule commands as well as manual
   submissions. Require service authorization without synthetic HTTP requests or
   direct store access. Keep caller control over qualified canonical options.
7. **Clarify AC-009/010/032 and W04.** Record separate provider/runtime facts,
   process readiness and freshness. Keep ShuETL's process supervisor small and
   domain-agnostic; preserve truthful drain and uncertain-effect limitations.
8. **Assign AC-028–033 and W05/W06 evidence ownership.** Upstream conformance plus
   ShuETL installed-artifact integration; keep every advertised capability tested.
9. **Replace conflicting historical ownership language.** ADR-0001's “every
   feature through FastAPI” criterion conflicts with accepted headless scope.
   Architecture and capability docs mix implemented and planned releases. Add a
   superseding ownership ADR and align the current planning documents; preserve
   historical release evidence rather than rewriting it as current capability.
10. **Expand boundary enforcement.** The current checker catches selected import
    roots, exact class names and route decorators, but misses raw provider-schema
    SQL and domain logic inside generically named helpers. Add import-layer and
    behavior checks for the standard path. Permit tightly scoped ShuETL process
    probe endpoints without allowing copies of ETLantic domain routes.

Keep existing 0.5 facade/bundle interfaces compatible while directing the new
standard path through the upstream backend. Deprecate duplicate construction
only with a documented migration path. Backend decoupling does not make 0.55
durable records compatible with a new store; retain the planned fresh-store and
rollback boundary unless upstream supplies and qualifies a conversion.

## Suggested implementation order and release decision

First implement and qualify the upstream backend/service/provider contracts.
Then revise the ShuETL ADR and 0.6 execution/verification plan against their exact
public signatures. Finally implement ShuETL's configuration, host adapters,
supervisor, probes and installed-artifact acceptance suite.

Keep 0.6 unreleased until the standard manual and scheduled paths use those
contracts and the revised deployment gates pass. If upstream work is deferred,
explicitly narrow the release claim; do not preserve “complete backend” or
headless schedule parity by moving the missing logic into ShuETL.

No production source, dependency pins, accepted ADRs or release gates were changed
by this review. The earlier checkout-wide test run reported 187 passed, 2 failed
(ADR evidence-link and source-distribution hash checks), and 5 PostgreSQL skips.
This review adds focused 0.56 construction probes, not a new claim of production
readiness or a completed 0.6 acceptance run.
