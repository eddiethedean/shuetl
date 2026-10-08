# Phase 0.6 — Role-Separated Production Preview: Execution Contract

## Planning status

- Target release: `0.6.0`.
- Released baseline: [`v0.5.0`](https://github.com/eddiethedean/shuetl/tree/v0.5.0)
  at `d846c3dd15b517def5c736e831202a603ca0e080`; the
  [release workflow](https://github.com/eddiethedean/shuetl/actions/runs/36659686930)
  passed and published to PyPI.
- Selected 0.6 compatibility train: published ETLantic core, FastAPI, and
  SQLModel `0.56.2`, used as published; PostgreSQL `18.6`; Python 3.11–3.13.
  SQL and Foundry provider packages, when enabled, also use exact `0.56.2`
  pins. The released ShuETL 0.5.0 baseline uses ETLantic `0.55.0`.
- Dependency selection is complete. Implementation updates the package pins,
  lock, compatibility checks, and provider metadata to this train. Upstream
  release-document cleanup or a later ETLantic release is not a prerequisite.
- Status: **planning contract; production role integration is not yet
  qualified**. Gate 0 below must pass before a 0.6 production-preview claim.

The [role-composition ADR](../adr/0014-role-separated-managed-runtime.md)
records the proposed concrete wiring and lifecycle decisions. The
[verification plan](PHASE_0_6_VERIFICATION.md) maps all acceptance criteria to
fixtures, checks and evidence. These are planning documents; their proposed
commands and paths are not claims of implemented or passing checks.

This plan refines the [roadmap boundary](ROADMAP.md#06--role-separated-production-preview).
The [0.5 contract](PHASE_0_5_EXECUTION.md) remains authoritative for host
identity, authorization, redaction, and the PostgreSQL gateway graph. The
[runtime design](SCHEDULING_AND_RUNTIME.md) assigns scheduling, leases,
execution, retries, and recovery to ETLantic. Phase 0.6 adds process
composition and evidence for those upstream behaviors; it does not implement
their semantics in ShuETL.
The standard-consumer and developer-control requirements in
[ADR-0013](../adr/0013-specifications-and-backend-ownership.md) and
[CAPABILITY_DELIVERY.md](CAPABILITY_DELIVERY.md) also apply. Existing 0.5
evidence is the regression baseline; it does not qualify newly composed 0.56
services or prove the broader host capability plans are already implemented.

## Supported preview boundary

The reference deployment uses one version-pinned `shuetl[postgresql]` artifact,
one qualified PostgreSQL database, and separate supervised gateway, scheduler,
and worker processes. Its first acceptance fixture uses one explicitly
configured tenant and workspace. Additional scopes need separate explicit role
instances or a qualified upstream enumeration and partitioning contract.

Two instances of each role must be exercised to prove coordination, but this
does not imply a general HA, multi-tenant, multi-region, or capacity claim.
The gateway accepts authenticated control-plane requests and never executes
pipeline work. Scheduler and worker processes use trusted service contexts;
they never reuse a caller's host token or session credential. A SQL-only
deployment is supported only if the selected upstream stores coordinate
through PostgreSQL without a broker.

The minimum live fixture uses immutable CSV and PostgreSQL sources with a
PostgreSQL sink, bounded declarative transforms and quality checks. It proves
the standard application path with independently installed backend packages.
Record every advertised source/destination/write-mode combination in a support
matrix. Foundry and other providers can be enabled only after their ShuETL
integration rows pass; upstream's provider matrix is input evidence. Additional
qualified canonical controls remain accessible even when the reference fixture
does not exercise them. HTTP/control-plane metadata may use PostgreSQL while
file inputs and report artifacts use a separately configured shared resource
volume; the deployment guide must provision and qualify both.

```text
same pinned application artifact
├── gateway × 2: trusted host FastAPI app + ShuETL + etlantic-fastapi
├── scheduler × 2: upstream timer leadership + schedule/durable stores
├── worker × 2: upstream execution host + ManagedExecutionAdapter
├── worker --kind actions × 2: upstream provider-action execution host
└── PostgreSQL 18.6: provider-owned registry, submission, event,
    schedule, firing, and durable-work state
```

## Gate 0 — Qualify ShuETL composition on ETLantic 0.56.2

The published ETLantic 0.56.2 wheel audit is recorded in
[ETLANTIC_0_56_2_WHEEL_AUDIT.md](ETLANTIC_0_56_2_WHEEL_AUDIT.md). It verifies
the published package hashes and confirms fixes for gateway import isolation
and read-only migration-version inspection. ShuETL process-role and target
PostgreSQL evidence remains required before Gate 0 closes.

The published wheel hashes match the upstream qualification manifest, whose
release evidence records 44/44 upstream acceptance criteria passed. This
settles artifact selection; ShuETL's own role integration remains unqualified.
The stale upstream candidate/support wording is retained as an audit finding
and does not block implementation against the published release.

| Surface in the 0.56.2 installation | Selected 0.6 composition | Required ShuETL evidence |
| --- | --- | --- |
| `ManagedBackendConfig`, `create_managed_backend`, and `ManagedApplicationService` | Construct the standard SQLModel service graph per process; gateway HTTP and headless submission use the same upstream service contracts. | Exact public imports, scoped authorization, shared database/store identity, and resource ownership. |
| `etlantic.runtime.scheduler_service.SchedulerService` | Supervise public `tick`, `ready`, and `drain`; pass the bound `managed_service.submit_scheduled_run` method as `run_submitter`. | Preserve upstream discovery of occurrence preparation/recovery; prove manual/scheduled admission parity, occurrence identity, restart and duplicate-scheduler behavior. |
| `ManagedBackend.create_execution_host()` | Use the supplied `ManagedExecutionAdapter` and real ETLantic runtime. | Observable sink effect, canonical report, leases/fencing, cancellation and recovery. |
| `ExecutionHost` lifecycle | Provide ShuETL process readiness and signal handling around public tick/drain behavior; no upstream `ready()` method is assumed. | Provider/loop/adapter readiness, outage handling, safe drain and one-time cleanup. |
| `ManagedBackend.create_action_execution_host()` | Dedicated worker processes with `--kind actions` execute upstream action-job ticks and independently packaged provider handlers. | Isolated live connection/catalog/preflight actions, scoped resource access and bounded failures without gateway execution. |
| SQLModel stores and migrations | Use one engine per process and migration head `014_cp1_complete_principal_idempotency_0_56`. | PostgreSQL 18.6 coordination, managed firing/submission/link recovery and the startup boundary below. |
| Upstream scheduler/worker CLI | Use the Python services; the published CLI uses JSON-file stores. | Installed ShuETL commands construct the PostgreSQL graph directly. |

Gate 0 closes when the role-composition ADR records the public imports,
signatures, service contexts, lifecycle and resource ownership, and an
installed-wheel PostgreSQL 18.6 spike executes one manual and one scheduled
real ETL submission through separate gateway/scheduler/worker processes.
The ADR confines ShuETL to wiring, supervision and diagnostics; ETLantic owns
timing, claims, leases, retries, cancellation and recovery. The remaining
failure matrix is mandatory for the 0.6 release gate.

The managed schedule path is not one firing-and-submission transaction. In
0.56 it prepares an occurrence, claims its firing with admission deferred,
submits through the managed service, then links the firing to the durable
submission. Restart reconciles unlinked accepted firings through upstream
recovery. Same-engine stores remain required, but qualification must observe
each commit boundary and canonical identity instead of assuming atomicity.
Pass the bound submission method directly: a lambda wrapper loses the
scheduler's automatic discovery of its preparer and recoverer. No ShuETL
fingerprint, firing-key calculation, replay or repair loop is permitted.

### Fresh-store transition and startup boundary

The 0.6 reference starts with a fresh, separately provisioned 0.56 database.
An operator runs `shuetl database upgrade` with migration privileges to reach
head `014_cp1_complete_principal_idempotency_0_56` before starting any role.
Do not point 0.56 processes at the 0.55 store or promise resumption of its
durable work. Retain the 0.5 application and its separate store for rollback;
stop new admissions and native scheduling in the old deployment before
enabling the new deployment. Re-enroll definitions, connections and schedules
through public APIs, and reconcile unfinished work and external effects
explicitly before resubmission. A general data converter and rolling upgrade
remain outside this preview.

ShuETL performs read-only schema preflight before managed-backend construction
and rejects a fresh, behind, unknown or corrupt schema. Dispose the temporary
preflight engine before the standard backend creates its own shared engine.
Runtime database roles have required data privileges but no
schema-creation/migration privileges, ownership of provider tables, superuser
or inherited migration role. Qualification uses an actual connection under
these grants and executes a real submission and worker write, not only a
constructor under a session-switched read-only role.
ETLantic 0.56.2's version inspector checks for the version table and reads the
version without DDL. Managed backend construction must succeed under the
runtime role's ordinary data grants, with no schema `CREATE`, table ownership,
or migration privileges. Readiness and doctor use ShuETL's own read-only
inspection path and never reconstruct the backend. Capture database grants,
schema state and executed statements in the acceptance evidence.

## Process and configuration contract

The user-facing command is `shuetl serve --role gateway|scheduler|worker`.
`SHUETL_ROLE` remains required, and the command argument must match it; neither
source silently overrides the other. A new explicit `postgresql-preview`
profile accepts only the PostgreSQL provider and one of the three roles.
The released `postgresql-pilot` profile stays gateway-only, while memory,
SQLite, and `development-static` remain local-only. Missing or unsupported
configuration fails before host module loading or database access.

The standard CLI takes an explicit `--factory package.module:callable` from an
installed trusted integration package. The factory receives validated settings
and returns typed identity/authorization/resource bindings, not a provider
graph or runner. ShuETL constructs the standard managed backend and selected
role. Gateway bindings include `HostIdentityAdapter` and an optional host-app
composition hook; runtime bindings include an upstream scoped service context.
Scheduler and worker bindings do not load the gateway hook or construct a
FastAPI app. Adopters supply identity, membership and resource bridges;
ShuETL supplies submission wiring and runtime construction. Existing explicit
facade/provider injection remains available as an advanced API.

Worker commands additionally select `--kind runs|actions` (default `runs`),
matched to their configured worker kind. Action workers use the same trusted
bindings, schema, probes and unique ownership rules, but call the upstream
action execution host instead of a pipeline runner. Required provider actions
have dedicated processes so a long ETL tick cannot starve their queue. Their
handlers come from independently installed backend packages. A host does not
supply connector-action algorithms. Preview or provisioning is exposed only
when separately qualified; provisioning is never a preflight side effect.

The proposed factory result and role configuration are specified in ADR-0014.
Freeze their public signatures and acceptance mapping before implementation.
Parse and validate the import reference, settings, role and package versions
before invoking trusted factory code; perform schema preflight before runtime
construction. Importing explicitly selected trusted code is an operator trust
decision, not a plugin sandbox. Import/provider errors are redacted at the CLI.

The existing `SHUETL_IDENTITY=host` mode describes gateway request identity,
not scheduler or worker identity. The role-composition ADR must define how a
trusted host supplies service principals and scope for runtime roles, validate
that selection independently of request credentials, and preserve the 0.5
gateway settings contract. Use ETLantic `Principal` and `ControlPlaneContext`
with explicit tenant/workspace scope. `development-static` is never a runtime-role
shortcut.

| Role | May construct | Must reject or omit |
| --- | --- | --- |
| Gateway | Guarded host FastAPI app, upstream API router, PostgreSQL control-plane stores. | Scheduler or worker loop, pipeline runner, runtime secret resolution, local provider fallback. |
| Scheduler | Upstream scheduler with schedule and durable stores on the same engine, bound managed submit method, explicit scoped service context, unique process owner. | Host ASGI app, request credentials, pipeline execution, file-backed CLI stores. |
| Worker | Upstream execution host with durable store, explicit scoped service context, real runner, unique process owner. | Host ASGI app, no-op runner, scheduler timer calculation, file-backed CLI stores. |

Each role validates the exact installed package train, database TLS setting,
server version, schema head, and required tables before becoming ready.
Migrations remain a separate `shuetl database upgrade` operator step with
separate privileges. Provider construction, startup, readiness, and shutdown
must not change schema state; construction permits only the version-table
statement documented above, while health inspection remains free of DDL.
Keep gateway request identity, service identity, and ETLantic execution
credentials distinct in configuration, diagnostics, logs, and durable payloads.

`postgresql-pilot` remains a gateway-only configuration/API profile under the
new package train; this does not promise compatibility with a 0.55 database.
Requalify existing settings, identity guards, routes, errors, SSE and local
bundle behavior on 0.56 and use separately provisioned stores. The old 0.5
binary continues to own its original store. No dual train is loaded in one
interpreter and no migration command silently converts old durable work.

## Health and shutdown contract

- Liveness means the supervised process is running and its loop is responsive.
  Readiness means its own validated provider graph and upstream role are able
  to accept the work assigned to that role. A healthy gateway alone never
  proves that a scheduler or worker is ready.
- The gateway retains the authoritative upstream `/health` and `/ready`
  behavior for the mounted API. Runtime roles expose loopback-only `/live`
  and `/ready` operational probes on an explicit per-process port; these
  contain only role, lifecycle state and bounded reason codes. Probes return
  200 when satisfied and 503 otherwise. `doctor` inspects configuration and
  schema, never claims that a different running process is healthy.
- Runtime readiness requires validated scope/adapter, a running supervisor,
  fresh read-only provider inspection and no drain state. Scheduler `ready()`
  is only its drain flag, so it cannot substitute for a database probe. A
  scheduler waiting for another owner's leader lease can remain ready. A
  zero-result tick proves neither successful admission nor provider health.
- A worker's supervisor/probe remains responsive during a synchronous upstream
  tick. One execution thread invokes `tick(ctx, limit=1)`; ETLantic owns its
  heartbeat/cancellation monitor. Probe checks never claim work or mutate
  durable state. Long active work is not a stalled process solely because
  no new tick has completed.
- SIGTERM/SIGINT mark the process draining, fail readiness, stop dispatching
  new ticks/requests and invoke upstream drain. An already dispatched tick may
  still claim or finish work; record this window instead of promising immediate
  revocation. Await that tick before closing the backend once. An exceeded
  grace period reports an incomplete drain and leaves termination to the
  supervisor; never dispose an engine under active execution or fabricate a
  terminal result. Restart follows upstream lease/effect recovery.
- Preserve the `shuetl.doctor/1` fields and redaction behavior for the 0.5
  pilot. A breaking doctor shape needs a new schema identifier and its own
  compatibility tests. Process probes must not expose URLs, credentials,
  principal values, or raw provider exceptions.

## Acceptance criteria

| ID | Required result |
| --- | --- |
| AC-001 | Source, wheel, lock, and clean-wheel metadata identify ShuETL `0.6.0`, Python 3.11–3.13, exact ETLantic core/FastAPI/SQLModel `0.56.2` pins (and SQL/Foundry `0.56.2` when enabled), the PostgreSQL extra, and migration head `014_cp1_complete_principal_idempotency_0_56`. |
| AC-002 | An installed-artifact Gate 0 probe executes one real scheduled and one manual submission through the selected PostgreSQL-backed upstream roles; the worker produces an observable ETLantic report rather than no-op completion. |
| AC-003 | A single built application artifact starts each of the three roles; wrong/missing role, mismatched `--role` and `SHUETL_ROLE`, local provider, demo identity, missing runner, or incompatible package fails before serving or claiming work. |
| AC-004 | Existing gateway/local settings, facade, identity, HTTP/SSE and doctor contracts are requalified on 0.56 with fresh stores; `postgresql-pilot` stays gateway-only and no implicit preview or 0.55-store upgrade occurs. |
| AC-005 | Gateway construction and request handling never start scheduler/worker ticks, import the runner, resolve pipeline secrets, or execute a pipeline. |
| AC-006 | Scheduler and worker construct no FastAPI app or host credential verifier; each receives a trusted, scope-bound ETLantic service context and a unique owner ID. |
| AC-007 | All roles use the same provider schema/store identity. Scheduler passes the bound `submit_scheduled_run` method; crash/retry proofs cover occurrence preparation, firing claim, managed acceptance and linking on same-engine stores without assuming one atomic commit. |
| AC-008 | Every role performs read-only compatibility/connectivity/schema preflight and health inspection. Backend construction under a runtime role without schema-creation privileges performs no DDL; missing/incorrect schema fails before construction. Migration is possible only through the explicit operator command. |
| AC-009 | Role-local liveness/readiness report startup, running, draining, provider outage, and schema mismatch without false success or secret-bearing output. |
| AC-010 | SIGTERM/SIGINT fail readiness, stop new request/tick dispatch, invoke drain and await in-flight work before one-time cleanup. Evidence distinguishes in-flight acceptance/claim windows and grace-period expiry; no concurrent engine disposal or fabricated terminal result occurs. |
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
| AC-025 | The reference deployment provisions a fresh 0.56 store, rejects use of the 0.55 store, documents re-enrollment and reconciliation of unfinished work, and demonstrates rollback to the retained 0.5 application/store without concurrent trigger authority or automatic replay of uncertain effects. |
| AC-026 | The trusted factory receives validated settings and returns only typed host bindings. ShuETL constructs the managed graph, scheduler callback and execution host; malformed bindings, wrong scope, demo identity and invalid role-specific fields fail with redacted diagnostics. |
| AC-027 | An independently installed reference host changes canonical source/destination/transform/quality/schedule specifications and executes real manual/scheduled ETL without constructing stores, implementing connectors or supplying runtime callbacks. Headless and HTTP paths preserve canonical identities and outcomes. |
| AC-028 | Every advertised provider pairing/write mode has live source/sink evidence, enabled-writer policy, alias/upsert-key and schema-drift cases. The minimum CSV/PostgreSQL-to-PostgreSQL fixture proves select/drop/rename, casts, filters, scalar expressions, deterministic deduplication and schema/required/range/set quality rules, including failing quality without a falsely successful publication. |
| AC-029 | Canonical schema/control discovery, complete option round trips and per-run effective configuration agree with live behavior. Missing provider/policy/authorization/state requirements produce upstream diagnostics; supported controls are accessible without a ShuETL-only restriction. |
| AC-030 | Live failed-work retry and deliberate new-run commands preserve upstream attempt/run/lineage identities and admission policy. An independently packaged example extension executes without host ETL code or ShuETL core changes. |
| AC-031 | Advertised file-input/report-artifact support proves immutable checksums, owner/version access, changed/missing/expired input, retry retention, cross-worker availability and bounded cleanup; gateway artifact delivery does not expose runtime credentials or arbitrary filesystem paths. |
| AC-032 | Runtime probe state remains accurate during active execution, idle/standby, outage, recovery and drain; stale inspection fails readiness. Probe output, upstream runtime logs and exception handling pass seeded-secret redaction checks without hiding process failure. |
| AC-033 | Dedicated action workers perform live connection/catalog/schema/preflight operations through public upstream jobs without gateway secret resolution. Scope, resource rotation/revocation, deadline, outage and stale-preflight cases preserve canonical action results. Advertised sample preview is bounded/read-only with cleanup; provisioning requires separate explicit mutation authorization and qualification. |

## Verification matrix

The [verification plan](PHASE_0_6_VERIFICATION.md) assigns AC-001–AC-033 to
planned files, deterministic fixtures and evidence outputs. Every criterion
requires an executed proof from the final artifact. All 33 remain unqualified
for ShuETL 0.6; upstream 44/44 evidence and local PostgreSQL 14 constructor
smokes do not mark any of these rows passed.

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

1. **Adopt the selected artifacts.** Pin core/FastAPI/SQLModel to `0.56.2`
   and enabled SQL/Foundry providers to the same version. Update the lock,
   compatibility inventory, migration head and required-table metadata using
   the wheel audit. Preserve its distinction between upstream evidence and
   ShuETL qualification.
2. **Freeze process composition.** Finalize ADR-0014 for the trusted host factory,
   generic supervisor of upstream service ticks, service-context source, and
   scheduler/worker probe transport, managed-service callback wiring and the
   narrow construction exception. Keep the 0.5 settings precedence and
   security boundary explicit. Gate 0 uses a disposable installed-wheel harness
   before the public CLI exists, so it does not depend on step 3.
3. **Implement configuration and role graphs.** Add the preview profile,
   role-specific validation, entry points, and separate provider ownership.
   Extend compatibility, doctor, artifact, and boundary checks without adding
   a ShuETL domain model or provider schema.
4. **Implement role lifecycle.** Wire upstream startup, readiness, drain,
   signals, and cleanup; keep the gateway ASGI path separate from runtime
   process imports and secrets.
5. **Prove cross-process outcomes.** Run the acceptance and fault matrix on
   disposable PostgreSQL 18.6 (or a newly qualified version), with actual
   ETL execution and an instrumented sink effect.
6. **Package the reference deployment.** Supply container and process
   supervisor recipes, version/digest pinning, configuration and migration
   order, fresh-store transition/rollback, restart behavior, and at-least-once
   effect guidance.
7. **Release gate.** Build clean artifacts, run all required CI jobs, record
   evidence for the exact commit, review security and durability findings, and
   publish only after every criterion and Gate 0 passes.

### Implementation work packages

| Package | Depends on | Concrete output and completion evidence |
| --- | --- | --- |
| W01 — compatibility and schema | Selected published artifacts | Update `pyproject.toml`, `uv.lock`, compatibility diagnostics, PostgreSQL and SQLite inventories, installed metadata and normalized upstream OpenAPI; AC-001/004/008. |
| W02 — contract and Gate 0 | W01 | Finalize ADR-0014 and public signatures; disposable PostgreSQL 18.6 installed-wheel role harness with actual runtime grants, manual/scheduled effects, bound-method recovery and scoped contexts; AC-002/007/026. |
| W03 — settings and standard construction | W02 | Preview settings and trusted binding loader; standard managed graph plus role factories owned by ShuETL, negative configuration/security matrix; AC-003/005/006/026/027. |
| W04 — supervisor and probes | W03 | Serve entry points, unique owner IDs, loopback operational probes, one-item worker ticks, signals/drain/cleanup and redacted error paths; AC-009/010/019/021/032. |
| W05 — live capability qualification | W03/W04 | Independent reference host, provider support matrix, immutable resources, transform/quality/effective-settings/run-actions/extension fixtures and dedicated provider-action workers; AC-020/027–031/033. |
| W06 — process failure matrix | W04/W05 | Deterministic separate-process contention and commit-boundary faults, replay identities, stale fencing and cancellation effects; AC-011–019 plus AC-007/010/021/031/032. |
| W07 — deployment and transition | W05/W06 | One-artifact container/supervisor recipes, resource-volume/credential/grant setup, fresh-store handoff and rollback rehearsal; AC-022/025. |
| W08 — evidence and release | W01–W07 | Extend evidence/release/clean-wheel scripts and CI for 33 criteria, final wheel subprocess runs on Python 3.11–3.13/PostgreSQL 18.6, reviewed hashes/limitations and no skipped required cases; AC-023/024 and every release row. |

Update the evidence checker series map and expected criterion count together;
its current 0.5 mappings do not validate 0.6. Do not create placeholder PASS
records while implementing these packages.

## Explicit non-goals and stop conditions

- No ShuETL schedule calculator, worker engine, lease/fencing implementation,
  retry policy, migration, or ETLantic HTTP route copy.
- No anonymous or development-static production role, host token reuse by
  workers, implicit runner, memory/file fallback, or successful no-op execution.
- No multi-region, disaster recovery, unbounded capacity, formal SLA, forced
  process termination, or exactly-once external-effect claim. Backup/restore,
  rolling upgrades, broad role-to-role diagnostics, and capacity qualification
  remain Phase 0.7 work.
- Stop the 0.6 release if the selected published `0.56.2` train cannot provide
  a real runner, cross-process PostgreSQL coordination, safe drain/fencing, or a
  reproducible installed-artifact reference topology. A green unit suite or
  configured workflow alone does not satisfy this contract.
