# Scheduling and Runtime Composition

## Principle

ETLantic owns scheduling and runtime semantics. ShuETL configures and operates
ETLantic scheduler, worker, and external-runtime interfaces for FastAPI and
headless host deployments. The released 0.5 identity/gateway boundary remains
the security baseline; live role/executor qualification in 0.6 uses published
ETLantic `0.56.0` under the [execution contract](PHASE_0_6_EXECUTION.md).

ShuETL does not define:

- another schedule or firing model;
- trigger calculation;
- overlap or misfire semantics;
- a run state machine;
- claim, lease, fencing, retry, cancellation, or recovery behavior;
- an executor protocol competing with ETLantic's runtime contracts.

An embedded host also leaves canonical ETL state and execution with the backend.
The host may call public ETLantic services in-process for authoring and run
control, but accepted work is executed by the configured ETLantic worker or supported
external execution host. The host's request lifecycle and UI background tasks
do not own durable execution.

## Scheduling flow

```text
ETLantic ScheduleRecord
        ↓
ETLantic scheduler evaluates due time
        ↓
ETLantic FiringRecord with canonical logical key
        ↓
ETLantic durable submission
        ↓
ETLantic worker or supported external execution host
```

ShuETL supplies settings, provider instances, process entry points, health
checks, and deployment documentation for this flow.

## Capability requirements

Before enabling schedule routes or a scheduler role, ShuETL verifies that the
selected ETLantic package set provides:

- the expected schedule and firing schema versions;
- a persistent ScheduleStore suitable for the deployment profile;
- durable submission and idempotency support;
- an execution role capable of consuming accepted work;
- compatible migration state;
- explicit timezone, DST, overlap, misfire, and catch-up behavior;
- stable next-occurrence preview and a policy for whether a schedule follows
  the latest approved definition revision or pins a specific revision;
- one durable idempotency identity per occurrence, with pause/delete affecting
  only future occurrences.

Manual and scheduled work share authorization, admission, preflight policy and
durable-submission contracts. Scope is part of the canonical firing identity.
Resolve a latest-approved definition once at firing creation and preserve that
selected revision through retries; never re-read mutable definitions mid-run.

The backend submission service owns the complete preparation sequence for both
paths. For native schedules, the app supplies a schedule specification and
reads canonical outcomes; it does not calculate canonical firings, compute
request fingerprints or coordinate required preflight before scheduling a run.

Apps may alternatively submit work from external events, schedulers or workflow
tools, with one declared trigger authority and scoped idempotency/correlation
identity. They may decide when to request an authorized retry or deliberate new
run; ETLantic owns attempt/effect semantics and the transition itself. Business
workflow state stays in the app without becoming a second ETL run state machine.

If a requirement is absent, scheduling is unavailable. ShuETL must not fall back
to process-local timing in a production profile.

## Runtime roles

### Gateway

The gateway hosts FastAPI and accepts authorized control-plane requests. It
commits durable submissions but does not execute pipeline work in the request or
with FastAPI `BackgroundTasks`.

### Scheduler

The scheduler runs ETLantic's scheduler service against the configured schedule
and durable-work stores. For 0.56.0, ShuETL supervises public `SchedulerService`
ticks and wires its `run_submitter` callback to the managed submission service
with a trusted scoped context. The generic process loop invokes upstream
timing and claim decisions; it does not calculate schedules or firing identity.
Pass the bound `ManagedApplicationService.submit_scheduled_run` method so
upstream discovers occurrence preparation and recovery. Managed firing claim,
submission and linking span recoverable commits; same-engine storage does not
make this path one atomic transaction. Phase 0.6 proves every interruption
boundary through separate processes.

### Worker

The worker runs ETLantic's worker/execution service. It resolves the immutable
definition/plan/profile revision and executes through ETLantic's runtime.
For 0.56.0, construct it with `ManagedBackend.create_execution_host()` and its
`ManagedExecutionAdapter`. ShuETL supplies process readiness and shutdown
coordination around public lifecycle methods; the host has no `ready()`
method. The PostgreSQL preview does not launch the JSON-file worker CLI.
The supervisor remains responsive while one execution thread calls
`tick(ctx, limit=1)`. Drain stops future tick dispatch, then waits for the
in-flight tick before closing resources. A dispatched tick may still acquire
a lease after a signal; termination and external-effect limits are explicit
in [ADR-0014](../adr/0014-role-separated-managed-runtime.md).

### External execution host

An external host implements a supported ETLantic submission/poll/cancel/report
contract. ShuETL only configures the adapter.

### Provider actions and previews

Connection tests, catalogs and preflight may occur before a pipeline submission
exists. They use separately authorized upstream actions executed outside the
gateway with bounded resource references, deadlines and redacted results.
Pipeline submission failure does not forbid retaining provider-action audit
evidence. Destination provisioning is an explicit mutation, never preflight.

Sample preview also executes in an isolated role with no destination writes,
bounded data and temporary-storage cleanup. Its execution identity may be
durable; it must not be tied to a host request lifetime. These roles may share
an upstream worker process when supported. ShuETL does not invent an action
queue or authorize gateway secret resolution to bridge an upstream gap.

### Embedded application host

A host application may provide its own UI and use the standard specification
and command surface without exposing ETLantic HTTP routes. ShuETL configures
the backend graph; the backend owns submission preparation, execution and
recovery. Submission, worker, schedule and result semantics remain canonical.
Host-specific control tables remain projections or mappings keyed by canonical
ETLantic identities.

## Local-development profile

A development-only convenience mode may start ETLantic's in-process scheduler
and worker alongside FastAPI.

Requirements:

- it is explicitly labeled local/development;
- one-process limitations are visible in readiness/capability output;
- shutdown is graceful where upstream permits;
- it never becomes an implicit production fallback;
- tests do not confuse in-memory acceptance with durable production acceptance.

## Production reference profile

Run gateway, scheduler, and worker as separate supervised processes, even when
they use the same Python environment or container image.

The default reference may remain SQL-only if ETLantic's selected providers
support coordination through PostgreSQL. A message broker is optional, but
process isolation is not equivalent to adding an external orchestration
platform.

## Crash and recovery guarantees

ShuETL documents and tests the guarantees made by the selected ETLantic
providers. It must not strengthen those claims in marketing or API
documentation.

Production qualification should exercise:

- gateway failure before and after durable acceptance;
- scheduler restart around firing creation;
- worker loss before and after external side effects;
- lease expiry and stale-worker fencing;
- cancellation during queued, leased, and running states;
- idempotent resubmission;
- report/event publication failure;
- database disconnect and recovery;
- mixed-version rolling deployment where supported;
- an independent host process that submits and reads outcomes through the
  public headless composition contract;
- owner-scoped credential resolution and redaction inside worker execution;
- connector timeout/commit ambiguity and truthful reconciliation outcomes;
- bounded data-plane memory, batch size, concurrency, egress, and spool use for
  every named reference workload.

Exactly-once external effects must never be inferred from exactly-once firing or
submission identity. Sink idempotency and reconciliation remain explicit
ETLantic/runtime concerns.

## Retries and cancellation

ShuETL exposes ETLantic retry, cancellation, replay, and repair capabilities as
provided. It does not wrap them in a second policy model.

If an upstream execution mode cannot interrupt work safely, ShuETL must expose
that limitation rather than reporting cancellation as completed.

The [developer-control contract](DEVELOPER_CONTROL.md) adds discoverable actions
by caller/state/provider, per-run overrides, engine/resource preferences and
explicit retry-versus-rerun identities. Preserve every qualified public action,
including backfill, selective replay, pause/resume and live amendments when
available. Backend-owned recovery does not remove the app's choice of supported
policies or its ability to request those operations.

The 0.6 reference qualifies live cancel, safe failed-work retry and deliberate
new execution from a chosen specification. Additional lifecycle profiles are
0.8 expansion work; expose already-qualified contracts earlier. An action
unavailable in a given state must include a reason and cannot be simulated by
rewriting execution state or silently mapping to a different command.

## Dependencies

Scheduling and retry libraries are implementation details of ETLantic or its
providers. ShuETL should not depend directly on APScheduler, Tenacity, Dramatiq,
Celery, or equivalent libraries unless ShuETL introduces a narrowly scoped
integration that ETLantic does not own and an ADR approves it.

## Operational commands

ShuETL may offer ergonomic commands such as:

```text
shuetl serve --role gateway
shuetl serve --role scheduler
shuetl serve --role worker
shuetl doctor
```

These commands configure and invoke ETLantic roles. They do not implement
parallel runtime engines.
