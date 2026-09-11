# Scheduling and Runtime Composition

## Principle

ETLantic owns scheduling and runtime semantics. ShuETL configures and operates
ETLantic scheduler, worker, and external-runtime interfaces through a FastAPI
deployment.

ShuETL does not define:

- another schedule or firing model;
- trigger calculation;
- overlap or misfire semantics;
- a run state machine;
- claim, lease, fencing, retry, cancellation, or recovery behavior;
- an executor protocol competing with ETLantic's runtime contracts.

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
- explicit timezone, DST, overlap, misfire, and catch-up behavior.

If a requirement is absent, scheduling is unavailable. ShuETL must not fall back
to process-local timing in a production profile.

## Runtime roles

### Gateway

The gateway hosts FastAPI and accepts authorized control-plane requests. It
commits durable submissions but does not execute pipeline work in the request or
with FastAPI `BackgroundTasks`.

### Scheduler

The scheduler runs ETLantic's scheduler service against the configured schedule
and durable-work stores. ShuETL may provide a configuration wrapper or process
entry point, but not a separate scheduling loop.

### Worker

The worker runs ETLantic's worker/execution service. It resolves the immutable
definition/plan/profile revision and executes through ETLantic's runtime.

### External execution host

An external host implements a supported ETLantic submission/poll/cancel/report
contract. ShuETL only configures the adapter.

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
- mixed-version rolling deployment where supported.

Exactly-once external effects must never be inferred from exactly-once firing or
submission identity. Sink idempotency and reconciliation remain explicit
ETLantic/runtime concerns.

## Retries and cancellation

ShuETL exposes ETLantic retry, cancellation, replay, and repair capabilities as
provided. It does not wrap them in a second policy model.

If an upstream execution mode cannot interrupt work safely, ShuETL must expose
that limitation rather than reporting cancellation as completed.

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
