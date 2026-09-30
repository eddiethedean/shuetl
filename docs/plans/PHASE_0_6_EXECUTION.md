# Phase 0.6 — Role-Separated Production Preview: Execution Contract

## Planning status

- Target release: `0.6.0`.
- Released baseline: [`v0.5.0`](https://github.com/eddiethedean/shuetl/tree/v0.5.0)
  at `d846c3dd15b517def5c736e831202a603ca0e080`; the
  [release workflow](https://github.com/eddiethedean/shuetl/actions/runs/36659686930)
  passed and published to PyPI.
- Baseline compatibility train: ETLantic core, FastAPI, and SQLModel `0.55.0`;
  PostgreSQL `18.6`; Python 3.11–3.13. A later upstream train needs fresh
  artifact and behavior qualification before it can become the 0.6 pin.
- Status: **planning contract; production role integration is not yet
  qualified**. Gate 0 below must pass before a 0.6 production-preview claim.

This plan refines the [roadmap boundary](ROADMAP.md#06--role-separated-production-preview).
The [0.5 contract](PHASE_0_5_EXECUTION.md) remains authoritative for host
identity, authorization, redaction, and the PostgreSQL gateway graph. The
[runtime design](SCHEDULING_AND_RUNTIME.md) assigns scheduling, leases,
execution, retries, and recovery to ETLantic. Phase 0.6 adds process
composition and evidence for those upstream behaviors; it does not implement
their semantics in ShuETL.

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

```text
same pinned application artifact
├── gateway × 2: trusted host FastAPI app + ShuETL + etlantic-fastapi
├── scheduler × 2: upstream timer leadership + schedule/durable stores
├── worker × 2: upstream execution host + real host runner
└── PostgreSQL 18.6: provider-owned registry, submission, event,
    schedule, firing, and durable-work state
```

## Gate 0 — Qualify the upstream role contract

Inspection of the exact installed `0.55.0` packages establishes the starting
gap, not a 0.6 production qualification:

| Surface in the 0.55.0 installation | Observed behavior | 0.6 consequence |
| --- | --- | --- |
| `ShuETLSettings` and `PostgreSQLProviderBundle` | Only the `gateway` role and `postgresql-pilot` profile are accepted; the bundle exposes the exact upstream schedule and durable stores. | Add an explicit preview role/profile contract without changing the 0.5 pilot behavior. |
| `etlantic scheduler serve --help` and `etlantic worker serve --help` | The CLI commands take shared JSON file paths and load memory stores. | Do not wrap these commands for the PostgreSQL preview. |
| `etlantic.runtime.scheduler_service.SchedulerService` | A `tick` accepts `ScheduleStore` and optional `DurableWorkStore`; the service exposes `drain` and `ready`. | Qualify a supported process loop and shared SQLModel stores before use. |
| `etlantic.runtime.execution_host.ExecutionHost` | A `tick` accepts `DurableWorkStore` and an optional runner; its default runner returns without pipeline work. | A missing real runner must fail startup, never complete work successfully. |
| `SQLModelScheduleStore` and `SQLModelDurableWorkStore` | They accept one SQLAlchemy engine; firing claim can share a commit with durable acceptance when paired on that engine. | Prove the exact published provider's cross-process behavior with real PostgreSQL. |

Before implementation can claim production-preview readiness, select and
record a **published** ETLantic package train that supplies or explicitly
supports all of the following:

1. A PostgreSQL-backed scheduler and worker composition through public APIs.
   A public service/tick API is acceptable only if an ADR limits ShuETL to
   generic process supervision; ETLantic still owns timing, claim, lease,
   retry, cancellation, and recovery decisions.
2. A real worker runner that resolves the canonical immutable
   definition/revision/profile for admitted work and invokes ETLantic execution.
   A caller-supplied runner is acceptable if its public contract, input
   resolution, credential boundary, and result reporting are qualified.
3. Explicit owner identity, heartbeat, drain, readiness, and shutdown behavior
   suitable for multiple scheduler and worker processes. Termination must not
   turn an unknown external effect into a fabricated successful result.
4. A documented scoped service context for each role. It must use ETLantic's
   `Principal` and `ControlPlaneContext`, with explicit tenant/workspace scope
   and no request-credential reuse.
5. A compatible provider migration head and same-engine firing/durable
   acceptance guarantee. Startup and health inspection must be read-only.

Record public import paths, signatures, package hashes, migration head,
failure semantics, and a small installed-wheel PostgreSQL spike. If the
required behavior is absent, track the gap in ETLantic and keep the 0.6
preview claim blocked. Do not supply a ShuETL substitute for missing runtime
semantics or point production processes at the JSON-file CLI.

## Process and configuration contract

The user-facing command is `shuetl serve --role gateway|scheduler|worker`.
`SHUETL_ROLE` remains required, and the command argument must match it; neither
source silently overrides the other. A new explicit `postgresql-preview`
profile accepts only the PostgreSQL provider and one of the three roles.
The released `postgresql-pilot` profile stays gateway-only, while memory,
SQLite, and `development-static` remain local-only. Missing or unsupported
configuration fails before host module loading or database access.

The gateway consumes an explicitly selected trusted ASGI application factory
that supplies the existing `HostIdentityAdapter`, ETLantic authorizer, and
`PostgreSQLProviderBundle`. Scheduler and worker factories supply their own
trusted scoped service context and upstream role dependencies; they do not
construct or mount a FastAPI app. No configuration field may import an arbitrary
provider implementation. The exact factory signature and import mechanism need
an accepted role-composition ADR before implementation; examples must use an
installed host package rather than a sibling source checkout.

The existing `SHUETL_IDENTITY=host` mode describes gateway request identity,
not scheduler or worker identity. The role-composition ADR must define how a
trusted host supplies service principals and scope for runtime roles, validate
that selection independently of request credentials, and preserve the 0.5
gateway settings contract. `development-static` is never a runtime-role
shortcut.

| Role | May construct | Must reject or omit |
| --- | --- | --- |
| Gateway | Guarded host FastAPI app, upstream API router, PostgreSQL control-plane stores. | Scheduler or worker loop, pipeline runner, runtime secret resolution, local provider fallback. |
| Scheduler | Upstream scheduler with schedule and durable stores on the same engine, explicit scoped service context, unique process owner. | Host ASGI app, request credentials, pipeline execution, file-backed CLI stores. |
| Worker | Upstream execution host with durable store, explicit scoped service context, real runner, unique process owner. | Host ASGI app, no-op runner, scheduler timer calculation, file-backed CLI stores. |

Each role validates the exact installed package train, database TLS setting,
server version, schema head, and required tables before becoming ready.
Migrations remain a separate `shuetl database upgrade` operator step with
separate privileges. Provider construction, startup, readiness, and shutdown
must not create tables or migrate a schema. Keep gateway request identity,
service identity, and ETLantic execution credentials distinct in configuration,
diagnostics, logs, and durable payloads.

## Health and shutdown contract

- Liveness means the supervised process is running and its loop is responsive.
  Readiness means its own validated provider graph and upstream role are able
  to accept the work assigned to that role. A healthy gateway alone never
  proves that a scheduler or worker is ready.
- The gateway retains the authoritative upstream `/health` and `/ready`
  behavior for the mounted API. Scheduler and worker need an explicit local
  readiness probe from the qualified upstream role or the role-composition
  ADR. Phase 0.6 does not claim the cross-role readiness planned for 0.7.
- On termination, stop new acceptance or claims, invoke the upstream drain
  contract, and close the role's own engine once. If a worker cannot safely
  interrupt an active effect, report that limit; do not claim forced
  termination or exactly-once effects.
- Preserve the `shuetl.doctor/1` fields and redaction behavior for the 0.5
  pilot. A breaking doctor shape needs a new schema identifier and its own
  compatibility tests. Process probes must not expose URLs, credentials,
  principal values, or raw provider exceptions.

## Acceptance criteria

| ID | Required result |
| --- | --- |
| AC-001 | Source, wheel, lock, and clean-wheel metadata identify `0.6.0`, supported Python versions, one exact qualified ETLantic train, the PostgreSQL extra, and its provider migration head. |
| AC-002 | An installed-artifact Gate 0 probe executes one real scheduled and one manual submission through the selected PostgreSQL-backed upstream roles; the worker produces an observable ETLantic report rather than no-op completion. |
| AC-003 | A single built application artifact starts each of the three roles; wrong/missing role, mismatched `--role` and `SHUETL_ROLE`, local provider, demo identity, missing runner, or incompatible package fails before serving or claiming work. |
| AC-004 | The 0.5 `postgresql-pilot` gateway and local profiles retain their existing behavior; no implicit `postgresql-preview` upgrade occurs. |
| AC-005 | Gateway construction and request handling never start scheduler/worker ticks, import the runner, resolve pipeline secrets, or execute a pipeline. |
| AC-006 | Scheduler and worker construct no FastAPI app or host credential verifier; each receives a trusted, scope-bound ETLantic service context and a unique owner ID. |
| AC-007 | Scheduler and worker use the same PostgreSQL provider schema and store identity as the gateway; schedule/firing/durable acceptance uses the qualified same-engine transaction boundary. |
| AC-008 | Every role checks compatibility, PostgreSQL connectivity, and the provider-owned schema head without DDL; migration is possible only through the explicit operator command. |
| AC-009 | Role-local liveness/readiness report startup, running, draining, provider outage, and schema mismatch without false success or secret-bearing output. |
| AC-010 | SIGTERM prevents new gateway acceptance and new scheduler/worker claims before shutdown; repeated shutdown closes resources once and retains upstream lease/effect limits. |
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

## Verification and implementation order

1. **Qualify upstream artifacts.** Capture the exact public runtime and
   provider contracts, package hashes, migration head, and installed-wheel
   PostgreSQL spike. Resolve Gate 0 or record a blocking upstream issue.
2. **Decide process composition.** Accept an ADR for the trusted host factory,
   role supervisor versus upstream launcher, service-context source, and
   scheduler/worker probe transport. Keep the 0.5 settings precedence and
   security boundary explicit.
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
   order, restart behavior, and at-least-once effect guidance.
7. **Release gate.** Build clean artifacts, run all required CI jobs, record
   evidence for the exact commit, review security and durability findings, and
   publish only after every criterion and Gate 0 passes.

## Explicit non-goals and stop conditions

- No ShuETL schedule calculator, worker engine, lease/fencing implementation,
  retry policy, migration, or ETLantic HTTP route copy.
- No anonymous or development-static production role, host token reuse by
  workers, implicit runner, memory/file fallback, or successful no-op execution.
- No multi-region, disaster recovery, unbounded capacity, formal SLA, forced
  process termination, or exactly-once external-effect claim. Backup/restore,
  rolling upgrades, broad role-to-role diagnostics, and capacity qualification
  remain Phase 0.7 work.
- Stop the 0.6 release if a published upstream train cannot provide a real
  runner, cross-process PostgreSQL coordination, safe drain/fencing, or a
  reproducible installed-artifact reference topology. A green unit suite or
  configured workflow alone does not satisfy this contract.
