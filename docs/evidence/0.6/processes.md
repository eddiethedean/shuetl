# Phase 0.6 process observations

The reference process layout is one gateway, scheduler, run worker, and
optional action worker per role instance. Each role owns an ETLantic managed
backend engine and connects to the same PostgreSQL database/store. Scheduler
and worker owners are generated anew for each process start. Operational probes
bind only to `127.0.0.1`.

The code has unit coverage for settings, context scope, bound scheduler
submission callback, upstream action-host selection, provider-gated ticks,
probe state, gateway request gating, and once-only close behavior. A live
PostgreSQL integration fixture now submits one manual run through the gateway,
one scheduled occurrence through the scheduler, executes both in a real
ETLantic worker, and checks a PostgreSQL sink and effect ledger. Hosted jobs
provision a separate runtime database role with data access but without schema
`CREATE`, then compare public schema objects and migration version before and
after the three managed backends are constructed. ETLantic 0.56.2's current-
version check is read-only. No separate-process failure or recovery results
are claimed in this ledger.

No run of that integration fixture on PostgreSQL 18.6 is captured yet. There
are no ShuETL separate-process barrier tests for commit boundaries, duplicate
gateways/schedulers/workers, lease fencing, cancellation, forced worker death,
database outage/reconnect, active-tick drain, or restart reconciliation. No
canonical firing, submission, lease, attempt, report, or external-effect IDs
are claimed as observed in this ledger.

The expected operations sequence is: read-only preflight; construct the
backend; start role probe and supervision; gate new work on fresh provider
inspection; on signal, mark draining and stop dispatch; call upstream drain
where available; await in-flight work; close backend and host bindings once.
If the platform grace expires, keep resources alive while the external
supervisor decides when to terminate the process. The behavior under kill and
restart remains open.
