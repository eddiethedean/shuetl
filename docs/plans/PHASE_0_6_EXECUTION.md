# Phase 0.6 — Role-Separated Production Preview: Execution Contract

## Planning status

- Target release: `0.6.0`; released baseline: ShuETL `0.5.0` at
  `d846c3dd15b517def5c736e831202a603ca0e080`, using ETLantic `0.55.0`.
- Revised ownership decision: [ADR-0015](../adr/0015-backend-and-deployment-ownership.md),
  accepted 2026-10-08. [ADR-0014](../adr/0014-role-separated-managed-runtime.md)
  defines the revised process composition requirements; upstream APIs and the
  ShuETL binding/API freeze are recorded; installed-runtime qualification remains open.
- **Upstream selection accepted:** exact published `0.57.0` core, HTTP adapter
  and SQLModel artifacts now appear in development metadata/lock. The previous
  0.56.0 selection and constructor-DDL exception are superseded.
  [Coverage acceptance](../evidence/0.6/coverage-acceptance.md) records U01–U05 PASS;
  [PostgreSQL evidence](../evidence/0.6/README.md) records Gate 0 feasibility.
  Gates A–C and all 33 release criteria remain OPEN.
- PostgreSQL `18.6` and Python 3.11–3.13 remain the target qualification matrix.
  Select exact published core, HTTP adapter, persistence and enabled provider
  artifacts after Gate U. Preserve their declared compatibility; pin every
  enabled package and record hashes. No source-wheel patches or floating pins.
- Status as of 2026-10-09: **U01–U05 accepted; exact 0.57.0 pins adopted;
  installed-artifact PostgreSQL role feasibility PASS on Python 3.11–3.13;
  role binding/CLI/probe/drain source implementation present**. Final-wheel,
  lifecycle, failure, capability, transition and release gates remain OPEN.


The [verification plan](PHASE_0_6_VERIFICATION.md) maps Gate U, Gate 0 and all
33 acceptance criteria. Planned verification steps do not count as passing
evidence. The
[responsibility review](../reviews/PHASE_0_6_RESPONSIBILITY_REVIEW.md) explains the
change; the [dependency register](ETLANTIC_0_56_DEPENDENCIES.md) records issue status.
The [implementation and release plan](PHASE_0_6_IMPLEMENTATION.md) turns this
contract into ordered work packages, ownership, dependencies and exit checks.

## Responsibility boundary

ETLantic owns canonical models, authorized application and schedule commands,
planning, admission, idempotency, execution, leases, cancellation and recovery.
Its providers own connector implementations, persistence, resource access,
schema requirements and migrations. The standard backend and complete role
factories are upstream, independent of the HTTP adapter.

`etlantic-fastapi` adapts those services into canonical HTTP routes, wire schemas,
errors and SSE. ShuETL selects/configures qualified backend factories, composes
host identity and lifespans, and operates role entry points, process supervision,
probes, compatibility diagnostics and deployment runbooks. It owns the tested
operating envelope, not the ETL algorithms or canonical capability catalog.
Hosts own authentication, membership, credential enrollment, product UI and
business workflows. External supervisors own scaling, restarts and forced exit.

Keep the 0.5 facade and caller-owned bundles compatible. The new standard path
must not require a caller-built graph or put correctness-sensitive service
assembly in ShuETL. An upstream gap blocks that path; it never licenses a
ShuETL semantic replacement. Canonical services remain usable independently of
ShuETL, and FastAPI mounting is optional for headless use.

## Supported preview boundary

The reference uses one pinned `shuetl[postgresql,server]` application artifact, one
qualified PostgreSQL store, and separately supervised gateway, scheduler,
run-worker and action-worker processes. One explicitly configured tenant and
workspace is the initial supported scope. Additional scopes require separate
configured role instances or an upstream-qualified partitioning contract.

Exercise two instances of every role kind for coordination. This does not imply
general HA, multi-tenant, multi-region, capacity or exactly-once external-effect
support. A SQL-only deployment is valid only when the upstream stores supply
coordination without a broker. HTTP admission never executes ETL or resolves
runtime credentials; runtime roles receive trusted service contexts.

The minimum live fixture uses immutable CSV and PostgreSQL sources with a
PostgreSQL sink, bounded canonical transforms and quality rules. Each advertised
pairing/write mode needs both upstream conformance and ShuETL integration evidence.
Foundry and other optional providers remain unavailable in the supported profile
until their rows pass. Qualified canonical controls remain accessible even when
the reference fixture does not exercise them. Provision shared immutable input
and report volumes explicitly where advertised; SQL metadata alone is insufficient.

```text
same pinned application artifact
├── gateway × 2: host identity + ShuETL + etlantic-fastapi service adapter
├── scheduler × 2: upstream-complete managed scheduler
├── worker --kind runs × 2: upstream managed execution host
├── worker --kind actions × 2: upstream provider-action host
└── PostgreSQL + qualified shared resources: upstream-owned state and artifacts
```

## Gate U — Upstream contracts before standard-path implementation

All five surfaces are published in 0.57.0 and accepted in the coverage record.
The candidate audit binds hashes, signatures, upstream conformance and focused
isolated checks. The ETLantic GitHub issues remain administratively open; that
state is separate from ShuETL acceptance and deployment proof.
Different module names are acceptable if
the ownership and behavioral contracts below hold.

| Gate | Required upstream contract | Tracking | ShuETL boundary |
| --- | --- | --- | --- |
| U01 | Transport-independent backend/services and provider-owned SQL graph, explicit ownership/cleanup, canonical context validation, separate HTTP adapter | [ETLantic #278](https://github.com/eddiethedean/etlantic/issues/278) | Configure factories; runtime bindings have no HTTP dependencies. |
| U02 | Authorized schedule create/amend/pause/resume/preview/trigger/read/list/firing services shared by HTTP and headless callers | [ETLantic #279](https://github.com/eddiethedean/etlantic/issues/279) | Delegate canonical commands; no direct store or handler invocation. |
| U03 | Complete managed scheduler factory with schedule store and explicit preparation/submission/recovery integration | [ETLantic #280](https://github.com/eddiethedean/etlantic/issues/280) | Supply scope/owner/configuration; no callback-identity-dependent semantic wiring. |
| U04 | Provider-owned read-only schema compatibility/status, including partial/corrupt schema and required objects, reused by construction | [ETLantic #281](https://github.com/eddiethedean/etlantic/issues/281) | Render public status and apply deployment/server policy; no internal-table SQL or inventory duplication. |
| U05 | Public role-specific runtime status and cooperative-stop guarantees for scheduler, run worker and action worker | [ETLantic #282](https://github.com/eddiethedean/etlantic/issues/282) | Own dispatch, signals, process probes, freshness and cleanup; never leases or run transitions. |

The 0.56.0 wheel audit and focused 0.56.2 findings remain historical evidence.
The 0.57.0 candidate removes the headless HTTP dependency, supplies schedule
commands/store/factory, uses explicit occurrence collaborators and exposes role
status/drain. U04 now has a public provider inspection API beyond the #273 fix.
Do not carry the old constructor exception forward.

Upstream capability schemas, action-handler loading, plugin trust and semantic
conformance remain upstream responsibilities across these gates. ShuETL's support
matrix records qualified deployment combinations separately. Do not move the
exhaustive ETL engine test suite into ShuETL or treat upstream PASS as deployment
qualification. Independent process/sink observations remain mandatory below.

## Gate 0 — Qualify composition on the selected artifacts

After Gate U, freeze exact versions/imports/signatures, canonical context sources,
resource ownership and role lifecycle contracts in ADR-0014's qualification record.
Use a disposable installed-wheel harness before the public CLI exists. On
PostgreSQL 18.6 under actual runtime grants, construct the upstream backend and
roles, run one manual and one native-scheduled submission through separate
processes, and observe canonical reports plus sink effects. Include headless
schedule-command/HTTP parity and read-only inspection/construction traces.

Upstream owns occurrence preparation, claim, acceptance, linking and recovery.
Qualify the selected implementation's commit boundaries; a shared engine does
not establish atomicity. ShuETL must not compute firing keys, fingerprints,
repair links, or depend on a specific callable's `__self__`. Tests can observe
public boundaries without putting reconciliation code in the shipped supervisor.
Gate 0 does not replace any of AC-001–033 or the final-artifact failure matrix.

### Fresh-store transition and startup boundary

Provision a fresh separate store using the selected provider's explicit migration
API through `shuetl database upgrade`. Gate U/W01 records its exact schema head;
`014_cp1_complete_principal_idempotency_0_56` is also the inspected 0.57.0 head, not an
assumption about a future selected release. Retain the 0.5 application and 0.55
store for rollback. Disable old admissions/native scheduling before enabling the
new deployment, re-enroll through canonical APIs, and reconcile unfinished work
and external effects explicitly. No automatic cross-store replay, converter or
rolling-upgrade claim is introduced.

Use public provider inspection before admission and construction. Reject fresh,
behind, partial, unknown and corrupt schemas with safe diagnostics. Neither
inspection nor normal construction may issue DDL or explicit commits. Any temporary
inspection resources have an explicit owner and are closed on success/failure.
Runtime grants allow required DML but exclude schema CREATE, table ownership,
superuser and inherited migration privileges. Prove this on actual runtime
connections, not only a session-switched read-only constructor. Capture SQL and
schema snapshots; normal runtime writes are separate from read-only inspection.

## Process and configuration contract

`shuetl serve --role gateway|scheduler|worker` must match required `SHUETL_ROLE`.
The new `postgresql-preview` profile supports these roles with PostgreSQL only.
The existing `postgresql-pilot` remains gateway-only; memory, SQLite and
`development-static` remain local-only. Missing/unsupported configuration fails
before host module loading or database access. Constructor values continue to
override environment settings except that a conflicting explicit CLI role is
an error, not a silent override.

An explicit trusted `--factory package.module:callable` receives validated settings
and returns typed host identity/authorization/resource bindings. Gateway bindings
contain `HostIdentityAdapter`, its guarded HTTP context/principal pair, and an
optional ASGI composition hook. Runtime bindings contain a trusted canonical
service context and applicable resource/policy bridges, with no Request, HTTP
context factory, principal dependency, or gateway hook. The upstream headless
package must be independently installable without the HTTP adapter even though
ShuETL retains FastAPI for its existing gateway interface.

ShuETL passes bindings/configuration into upstream backend and role factories;
these own the complete graph and semantic collaborator assembly. The standard
host supplies no stores, row callbacks, connectors, scheduler or runner. Advanced
caller-owned injection remains available. Host bindings own only their integration
resources; upstream backend handles own their engines. Cleanup proceeds after
active work finishes, backend first and bindings second, once per owned resource.

Workers select `--kind runs|actions`, default `runs`, matching configured
`worker_kind`. Use dedicated upstream action hosts and independently packaged
handlers for connection/catalog/schema/preflight work. Preserve upstream loading,
trust, resource and deadline rules. Preview is separately qualified read-only
execution; provisioning is a separately authorized mutation. No gateway fallback.

ADR-0014 defines configuration ownership and binding requirements. Freeze exact
public types after Gate U. Validate import syntax/settings/version/role before
calling trusted factory code, and use provider preflight before role admission.
Explicit trusted factory loading is not a sandbox; redact import/provider errors.
`identity=host` describes gateway identity; runtime identity is a trusted scoped
service/workload Principal, never a copied request token or local demo identity.
Canonical context validity and per-command authorization are enforced upstream;
ShuETL additionally rejects deployment scope mismatches.

## Health and shutdown contract

- ShuETL owns process states `starting`, `running`, `draining`, `stopped`, `failed`.
  These never replace canonical ETL run/attempt states. External supervisors own
  restarts, scaling and forced termination.
- Readiness combines upstream role/provider facts, validated scope/configuration,
  a responsive supervisor, fresh inspection evidence and no drain state. Standby
  leadership is not failure; a zero-result tick is not a health proof. A healthy
  gateway does not prove that another role is running or ready.
- The gateway retains upstream HTTP `/health` and `/ready`. Runtime roles expose
  loopback `/live` and `/ready` on distinct configured ports, returning only role,
  process state and bounded reasons, with 200/503 status. These operational probes
  are the sole scoped exception to ShuETL's no-domain-route boundary. `doctor`
  checks configuration/provider facts, never a different process's health.
- Use public non-mutating provider/runtime inspection without claiming work,
  renewing leases or resolving runtime credentials. A worker supervisor/probe
  remains responsive during active upstream execution; long work alone does not
  establish a stall. Tick dispatch and upstream lifecycle signatures are frozen
  only after U05; the initial deployment uses one execution thread per worker.
- Signals fail readiness and stop new dispatch/requests, then invoke each role's
  upstream cooperative-stop contract. An already dispatched operation may still
  claim/accept/finish work; document that window. Await active work before backend
  and binding cleanup. Grace expiry remains draining/non-ready and is reported
  as incomplete; leave termination to the external supervisor. Never dispose an
  active engine, mutate lease/run state or fabricate a terminal outcome.
- Preserve `shuetl.doctor/1` compatibility and redaction for the pilot. A breaking
  report shape needs a new schema and compatibility tests. Public probes/logs
  exclude credentials, URLs, principal values and raw provider exceptions.

## Acceptance criteria


| ID | Required result |
| --- | --- |
| AC-001 | Source, wheel, lock, and clean-wheel metadata identify ShuETL `0.6.0`, Python 3.11–3.13, the exact published ETLantic/provider versions and provider schema contract selected after Gate U, and all enabled optional packages. No floating versions, patched wheels, or assumed 0.56.0 compatibility. |
| AC-002 | After Gate U, an installed-artifact Gate 0 probe executes one real scheduled and one manual submission through upstream-complete PostgreSQL backend/role factories; canonical reports and independent sink effects are observed. |
| AC-003 | A single built application artifact starts each of the three roles; wrong/missing role, mismatched `--role` and `SHUETL_ROLE`, local provider, demo identity, missing runner, or incompatible package fails before serving or claiming work. |
| AC-004 | Existing gateway/local settings, facade, identity, HTTP/SSE and doctor contracts are requalified on the selected upstream artifacts with fresh stores; `postgresql-pilot` stays gateway-only and no implicit preview or 0.55-store upgrade occurs. |
| AC-005 | Gateway construction and request handling never start scheduler/worker ticks, import the runner, resolve pipeline secrets, or execute a pipeline. |
| AC-006 | Scheduler and workers require no FastAPI app, Request, HTTP context factory, principal dependency or host credential verifier. Each receives a trusted scope-bound canonical service context and a unique process owner; upstream headless installation works without the HTTP adapter. |
| AC-007 | All roles use the same provider schema/store identity. The upstream managed scheduler factory supplies its schedule store and explicit preparation/submission/recovery collaborators. Standard consumers cannot disable recovery by wrapping a callback. Crash/retry proofs cover each canonical commit boundary without assuming atomic acceptance/linking. |
| AC-008 | All roles consume public provider-owned read-only connectivity/schema compatibility inspection. Inspection and normal backend construction issue no DDL or explicit commits; missing, partial, behind, unknown or corrupt schema fails before admission. Real runtime grants exclude schema creation/ownership; only the explicit operator migration command changes schema. |
| AC-009 | Role-local liveness/readiness combine upstream runtime/provider facts with process state and evidence freshness; startup, standby, active execution, draining, outage and mismatch produce truthful redacted responses. |
| AC-010 | SIGTERM/SIGINT fail readiness, stop new request/tick dispatch, invoke the upstream role-specific cooperative-stop contract and await in-flight work before one-time cleanup. Evidence distinguishes dispatched claim windows and grace expiry; ShuETL never changes lease/run state or disposes an engine beneath active execution. |
| AC-011 | Two gateway processes given the same scope and idempotency key yield one canonical accepted submission after concurrent requests and retry. |
| AC-012 | Killing a gateway before versus after durable acceptance produces the documented ambiguous-client/committed-store outcomes; retry with the same idempotency key recovers the canonical identity. |
| AC-013 | Two scheduler processes scanning one due schedule create exactly one canonical firing and linked durable submission for the logical key. |
| AC-014 | A scheduler crash around firing claim and durable acceptance recovers without an orphaned success claim or a second logical firing. |
| AC-015 | Two workers contending for one item honor upstream leases; one authoritative attempt result is recorded while duplicate external effects remain subject to the documented at-least-once contract. |
| AC-016 | Worker death before and after lease acquisition and on lease expiry leads to the exact upstream recovery state; no work is reported completed by an absent or no-op runner. |
| AC-017 | A stale worker cannot commit an authoritative terminal result after lease ownership or fencing token changes. |
| AC-018 | Cancellation in accepted, leased, and running states maps to upstream outcomes; inability to interrupt an external effect is reported without fabricated completion. |
| AC-019 | Database disconnect and reconnect fail readiness and work admission/claim safely, then recover through upstream state without memory or file fallback. |
| AC-020 | A representative real ETL fixture performs an observable, idempotency-keyed sink effect in a worker while both gateways remain responsive. |
| AC-021 | Request credentials and resolved secrets are absent from durable payloads, reports, events, errors, logs, doctor, and health output; execution credentials are resolved only inside the worker boundary. |
| AC-022 | Container and ordinary supervisor examples use the same digest-pinned artifact, separate processes, one PostgreSQL service, and no broker; startup and shutdown commands are reproducible. |
| AC-023 | The release gate and hosted Python 3.11–3.13 matrix run real PostgreSQL, subprocess failure injection, clean-wheel role smoke checks, artifact/OpenAPI/boundary checks, and reject skipped required cases. |
| AC-024 | A Phase 0.6 evidence ledger maps every AC to an exact command, observed result, source commit, upstream version, environment, artifact, and limitation. |
| AC-025 | The reference deployment provisions a fresh store for the selected upstream schema, rejects use of the 0.55 store, documents re-enrollment/reconciliation, and demonstrates rollback to the retained 0.5 application/store without concurrent trigger authority or automatic replay of uncertain effects. |
| AC-026 | The trusted factory returns role-specific host bindings. Gateway bindings alone contain HTTP identity/context and ASGI hooks; runtime bindings contain canonical service identity and resource/policy bridges. ShuETL configures upstream backend/role factories without constructing semantic collaborator graphs. Malformed bindings, wrong scope, demo identity and role-field mismatches fail with redacted diagnostics. |
| AC-027 | An independently installed reference host changes canonical source/destination/transform/quality/schedule specifications and executes manual/scheduled ETL without stores, connectors or runtime callbacks. HTTP and headless schedule create/amend/pause/resume/preview/trigger/read/list/firing services preserve authorization, revisions and identities without synthetic requests or direct store access. |
| AC-028 | Every advertised provider pairing/write mode has live source/sink evidence, enabled-writer policy, alias/upsert-key and schema-drift cases. The minimum CSV/PostgreSQL-to-PostgreSQL fixture proves select/drop/rename, casts, filters, scalar expressions, deterministic deduplication and schema/required/range/set quality rules, including failing quality without a falsely successful publication. |
| AC-029 | Canonical upstream schema/control discovery, complete option round trips and effective per-run configuration agree with live behavior. ETLantic owns authorization, capability and policy decisions; ShuETL reports deployment support separately and preserves qualified options without a competing catalog or policy model. |
| AC-030 | Live failed-work retry and deliberate new-run commands preserve upstream attempt/run/lineage identities and admission policy. An independently packaged example extension executes without host ETL code or ShuETL core changes. |
| AC-031 | Advertised file-input/report-artifact support proves immutable checksums, owner/version access, changed/missing/expired input, retry retention, cross-worker availability and bounded cleanup; gateway artifact delivery does not expose runtime credentials or arbitrary filesystem paths. |
| AC-032 | Runtime probes remain accurate during execution, idle/standby, outage, recovery and drain by combining public upstream status with process state. Stale evidence fails readiness; zero-result ticks do not prove health. Probe output, upstream logs and error handling pass seeded-secret redaction checks without hiding failure. |
| AC-033 | Dedicated action workers perform live connection/catalog/schema/preflight operations through public upstream jobs without gateway secret resolution. Scope, resource rotation/revocation, deadline, outage and stale-preflight cases preserve canonical action results. Advertised sample preview is bounded/read-only with cleanup; provisioning requires separate explicit mutation authorization and qualification. |


## Verification matrix

The [verification plan](PHASE_0_6_VERIFICATION.md) maps every criterion to fixtures
and evidence owners. All 33 criteria and Gates U/0 remain unqualified. Existing
upstream 0.56 evidence and SQLite probes do not establish PostgreSQL/process
acceptance. Required cases must run from the final selected artifacts without skips.

## Required failure-injection evidence

Use separate OS processes against a real PostgreSQL server; threads or memory
stores do not establish role coordination. Capture the canonical submission,
firing, lease, attempt, and report identities before and after each fault.
Fault controls must distinguish a process killed before a commit from one killed
after a commit but before its client received the outcome.

| Fault | Acceptance IDs | Observation to retain |
| --- | --- | --- |
| Gateway loss around durable accept | AC-011, AC-012 | HTTP outcome, idempotency key, one canonical submission, retry result. |
| Scheduler loss around firing acceptance; duplicate schedulers | AC-013, AC-014 | One logical firing and linked durable submission after restart. |
| Worker loss around lease and effect; duplicate workers | AC-015, AC-016 | Lease owner/token, attempt history, effect marker, recovery state. |
| Stale worker completion after ownership change | AC-017 | Rejected stale terminal update and unchanged authoritative result. |
| Cancellation in three durable states | AC-018 | Upstream state and whether an effect could still finish. |
| PostgreSQL outage and restoration | AC-019 | Readiness transition, no fallback state, resumed upstream processing. |
| Gateway isolation during representative execution | AC-005, AC-020, AC-021 | Worker-only execution/secret access and bounded gateway response. |
| Drain during an active tick; deadline expiry | AC-010, AC-032 | Probe transitions, tick-dispatch boundary, effect marker, cleanup count and upstream recovery after supervisor termination. |
| Input change/expiry; worker replaced before artifact read | AC-031 | Immutable version/checksum, denied ownership access, retained resource/report identity and cleanup result. |

## Verification and implementation order

1. **Close Gate U.** Qualify published upstream contracts U01–U05 and record their
   evidence, exact artifact versions and public signatures. No ShuETL workaround
   closes a missing semantic/provider contract.
2. **Select artifacts and close Gate 0.** Update pins/lock and compatibility records,
   then prove standard role construction under real runtime grants with manual,
   scheduled and headless-command parity fixtures. Preserve the 0.5 regression
   baseline and separately provisioned store transition.
3. **Implement deployment configuration and lifecycle.** Add role-specific host
   bindings, upstream factory selection, process entry points, supervisor/probes,
   cleanup and redacted diagnostics. Preserve advanced facade/bundle interfaces.
4. **Prove live behavior and failures.** Exercise the support matrix and separate
   process faults with independent sink observations on PostgreSQL 18.6. Upstream
   owns semantic conformance; ShuETL owns installed deployment integration.
5. **Package and release only qualified artifacts.** Record container/supervisor
   recipes, fresh-store rollback, hashes, CI results and all acceptance evidence.
   Gates U, 0 and A–C plus AC-001–033 must pass with no unresolved required defect.

### Implementation work packages

| Package | Depends on | Concrete output and completion evidence |
| --- | --- | --- |
| W00 — upstream contract gate | U01–U05 issues and published artifacts | Public backend, schedule services/factory, provider inspection and lifecycle evidence; isolated installations prove Gate U; no ShuETL semantic substitutes. |
| W01 — compatibility and schema | W00 | Exact metadata/pins/lock and provider-owned schema requirements/status, regression/OpenAPI inventory; AC-001/004/008. |
| W02 — contract and Gate 0 | W01 | Freeze ADR-0014 signatures; installed-wheel PostgreSQL 18.6 harness with runtime grants, complete scheduler, manual/scheduled effects and headless parity; AC-002/006/007/026/027. |
| W03 — settings and standard construction | W02 | Role-specific bindings and upstream factory selection, deployment scope/compatibility checks and public inspection; no graph algorithms, handler copies or schema SQL; AC-003/005/006/026/027. |
| W04 — supervisor and probes | W03, U05 | CLI, owner IDs, dispatch/signals, fresh operational probes and one-time cleanup around upstream role contracts; AC-009/010/019/021/032. |
| W05 — live capability qualification | W03/W04 | Independent host and extension fixtures, upstream conformance references plus installed pairing/mode/resource/command/action-worker proofs; AC-020/027–031/033. |
| W06 — process failure matrix | W04/W05 | Separate-process contention and commit-boundary faults, canonical recovery/fencing/cancellation observations; AC-011–019 and AC-007/010/021/031/032. |
| W07 — deployment and transition | W05/W06 | Same-artifact recipes, grants/resources, fresh-store handoff and rollback; AC-022/025. |
| W08 — evidence and release | W00–W07 | Gate U/0 and 33-criterion ledger, final-wheel hosted matrix, no skipped required cases; AC-023/024 and every release row. |

Update the evidence checker series map, Gate U bindings, expected criterion count
(33), approved requirement text and release script together during implementation.
Do not create placeholder PASS records or rewrite historical release evidence.

## Explicit non-goals and stop conditions

- No ShuETL schedule calculator, semantic graph factory, lease/fencing/retry engine,
  run state machine, schema inspector over provider tables, migration implementation,
  canonical capability catalog or ETLantic domain route copy.
- No HTTP request/context factory in runtime bindings, demo production identity,
  copied host tokens, implicit runner, memory/file fallback or successful no-op work.
- No broader HA, multi-region, disaster recovery, capacity/SLA, forced-stop or
  exactly-once external-effect claim. Broader operational qualification stays in 0.7.
- Stop standard-path implementation at an unmet Gate U contract. Stop release if
  Gate 0, any required acceptance row or final-artifact gate fails. Upstream issue
  closure, green unit tests or configured CI alone are insufficient.
