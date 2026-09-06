# Scheduling and Runtime

## Scheduling model

Schedules create runs. They do not own execution.

```text
Scheduler
   ↓
Find due schedule
   ↓
Create durable Run(PENDING)
   ↓
Advance next_run_at transactionally
   ↓
Executor claims run
```

This avoids duplicate execution and keeps the scheduler lightweight.

## Trigger types

MVP should support cron, interval, and one-time/date triggers.

## Timezones

Every schedule must have an explicit timezone. Do not infer server-local time as persistent schedule semantics.

## Scheduler implementation

APScheduler is the MVP timing dependency, but ShuETL keeps its persistent schedule model independent of APScheduler objects. The database remains authoritative.

## Duplicate prevention

A transaction or lease must guarantee multiple service replicas cannot create duplicate runs for the same schedule occurrence. Prefer PostgreSQL row locking, advisory locks, unique `(schedule_id, scheduled_for)` constraints, or a scheduler leader lease over process-local flags.

## Concurrency policies

Support a small explicit set such as `ALLOW`, `FORBID`, `REPLACE`, and `QUEUE`, with MVP likely beginning with `ALLOW` and `FORBID`.

## Misfire policy

Support explicit `SKIP`, `RUN_ONCE`, and later `CATCH_UP` behavior. Unbounded catch-up is never the default.

## Run execution

The executor claims runs through durable state transitions:

```text
PENDING → CLAIMED → RUNNING → SUCCEEDED / FAILED
```

A heartbeat supports stale-run detection in multi-worker deployments.

## Retry policy

Retries use explicit policy: max attempts, backoff strategy, initial/max delay, and retryable error codes. Retry history is auditable.

## Cancellation

MVP can cancel `PENDING` runs immediately and mark `RUNNING` runs as cancellation requested. Forceful interruption may be deferred.

## Execution isolation

Initial execution may use internal asyncio tasks, executor pools, or dedicated threads/processes. CPU-heavy/failure-prone work can later move to isolated workers without changing public run semantics.

## Long-running HTTP request rule

Never execute the pipeline directly inside the trigger request. `POST` creates a durable run and returns `202 Accepted`; clients poll or subscribe to status.

## Scheduled execution identity

Schedules do not own credentials. A scheduled run resolves the pipeline version's explicit service account, checks credential grants, resolves secrets just in time, and only then invokes ETLantic.

Authorization/credential failures must block before unsafe external I/O.

## Scheduler library strategy

Use APScheduler 3.11.x for timing mechanics while keeping ShuETL's database model authoritative. Use Tenacity or backend-native retry primitives rather than custom backoff loops.

`LocalExecutor` remains core; Dramatiq is the preferred first optional distributed adapter, with Celery as a later compatibility backend.

## FastAPI lifespan ownership

Scheduler and local executor startup/shutdown belong in FastAPI lifespan.

## BackgroundTasks prohibition

Do not run ETLantic pipelines with FastAPI `BackgroundTasks`. It is limited to small, non-durable post-response work.

## SQL-backed execution baseline

The baseline requires no broker or external scheduler:

```text
APScheduler in application process
        ↓
SQL Schedule state
        ↓
SQL Run(PENDING)
        ↓
LocalExecutor claims run
        ↓
RUNNING
        ↓
SUCCEEDED / FAILED
```

For PostgreSQL multi-process deployments, prefer row locks, `FOR UPDATE`, `SKIP LOCKED`, advisory locks, leases, and unique constraints before introducing a required broker.

Dramatiq/Celery/Redis/RabbitMQ remain optional scale-out backends.
