# Phase 0.6 public composition contract

This record describes the ShuETL role graph implemented for the Phase 0.6
branch. API shape and source inspection do not qualify live PostgreSQL,
provider, process, or failure behavior. See the per-criterion status in
[`README.md`](README.md) and [`qualification.md`](qualification.md).

## Selected package train

| Package | Selected version |
| --- | --- |
| Python | `>=3.11,<3.14` |
| `shuetl` | `0.6.0` development target |
| `etlantic` | `0.56.0` |
| `etlantic-fastapi` | `0.56.0` |
| `etlantic-sqlmodel` | `0.56.0` |
| `etlantic-sql` extra | `0.56.0` |
| `etlantic-foundry` extra | `0.56.0` |
| FastAPI / Pydantic / SQLAlchemy / Psycopg / Uvicorn | `0.141.1` / `2.13.5` / `2.0.52` / `3.3.5` / `0.54.0` |
| PostgreSQL preview server | `18.6` |
| SQLModel migration head | `014_cp1_complete_principal_idempotency_0_56` |

The exact ETLantic 0.56.0 wheel hashes and upstream audit limits are recorded
in [`ETLANTIC_0_56_WHEEL_AUDIT.md`](../../plans/ETLANTIC_0_56_WHEEL_AUDIT.md).
Upstream's 44/44 acceptance result is not counted as a ShuETL process-role
result.

## Production plugin allowlist

ETLantic SQL 0.56.0 exposes a SQL plugin reporting version `0.56.0` and a
transform compiler reporting version `0.50.0` under the same
`etlantic-sql` plugin identity. ETLantic core also exposes the built-in
`etlantic-local` compiler as version `0.50.0`; it has no separate distribution.
The integration profile therefore allows `etlantic-sql` with
`>=0.50.0,<0.57.0` and `etlantic-local` with `==0.50.0`. ShuETL checks the
specifier against an installed package distribution when one exists, while
ETLantic checks each discovered plugin's own identity and version. ShuETL's
package compatibility gate still requires the installed ETLantic SQL
distribution to be exactly `0.56.0`.

## ShuETL bindings

`shuetl.runtime.HostRuntimeBindings` contains the host's public ETLantic
authorizer; an optional gateway `HostIdentityAdapter`; an optional scoped
service `ControlPlaneContext`; an optional `PlanningContext` factory; optional
independently installed action handlers; an optional worker-side
`SecretAliasAuthorizer`; an optional gateway app factory; and an optional
host-resource close callback.

`shuetl serve --role gateway|scheduler|worker --factory package.module:callable`
requires a matching `SHUETL_ROLE`. Workers additionally accept `--kind runs`
or `--kind actions`. ShuETL validates preview settings and package versions,
performs read-only PostgreSQL server/schema inspection, then loads trusted host
bindings and creates the ETLantic managed backend. The current migration head
is required before role construction.

## Upstream construction calls

The role graph uses these public ETLantic 0.56.0 surfaces:

```text
etlantic_fastapi.ManagedBackendConfig
etlantic_fastapi.managed.create_managed_backend
etlantic.runtime.scheduler_service.SchedulerService
ManagedBackend.create_execution_host
ManagedBackend.create_action_execution_host
ManagedApplicationService.submit_scheduled_run
```

Gateway and runtime roles construct the same database, store ID, profile,
authorizer, and planning bridge. Gateway identity dependencies come from the
guarded host adapter. Scheduler and worker API identity dependencies reject
HTTP requests; their public service calls use the configured service context.
The scheduler receives the bound
`backend.api.managed_service.submit_scheduled_run` method so ETLantic discovers
its occurrence preparation and recovery methods.

ETLantic 0.56.0's `create_managed_backend` constructs the durable-work store but
leaves `api.schedule_store` unset. ShuETL supplies the public
`etlantic_sqlmodel.control_plane.SQLModelScheduleStore` on the backend's same
engine and configured store ID before building the scheduler. This makes the
scheduler use the same persisted control-plane database; the integration is
covered by the scheduler role unit proof and PostgreSQL CI.

The run worker invokes `tick(context, limit=1)` on an ETLantic execution host.
The action worker invokes the action host's public tick. ShuETL owns role
startup, loopback probes, provider readiness checks, signal handling, and
resource close ordering. ETLantic owns scheduling, durable admission, claims,
leases, attempts, execution, reports, cancellation, and recovery.

## Upstream import limitation

The public `etlantic_fastapi` package import loads
`etlantic.runtime.execute` and `etlantic.runtime.action_execution_host` into
`sys.modules` in a fresh process. ShuETL avoids its own eager imports of those
modules, but the gateway imports `etlantic_fastapi` for its public context and
managed-backend API. This means the current upstream package cannot meet the
Phase 0.6 gateway criterion that forbids importing the runner. AC-005 remains
open until ETLantic provides a package boundary that lets gateway code use its
public FastAPI APIs without importing runtime execution modules, or an
equivalent upstream fix is qualified.

Reproduction command:

```sh
uv run python -c 'import sys; import etlantic_fastapi; print([n for n in sys.modules if n.startswith("etlantic.runtime.") and ("execution_host" in n or n.endswith(".execute"))])'
```

Observed result contains `etlantic.runtime.execute` and
`etlantic.runtime.action_execution_host`.

## Probe and schema boundary

Runtime processes bind `/live` and `/ready` to loopback and return only role,
lifecycle state, booleans, and a bounded reason code. A recent read-only schema
inspection gates new ticks. The gateway retains its upstream `/health`
handler; requests are held at 503 until the local provider check is ready.

Readiness and doctor call ShuETL's read-only inspector. Backend construction
uses the ETLantic constructor. ETLantic 0.56.0's `migrations.current_version`
unconditionally issues `CREATE TABLE IF NOT EXISTS
etlantic_sqlmodel_schema_version`, even after its caller verifies that the
table exists. PostgreSQL still requires schema `CREATE` for that statement, so
backend construction fails for the intended runtime role without schema
`CREATE`. The hosted fixture now grants schema `CREATE` to exercise the rest of
the runtime graph and compares schema snapshots before and after construction;
this does not satisfy AC-008's least-privilege requirement. AC-008 remains
open pending an upstream read-only version check or an accepted change to the
runtime grant contract.
