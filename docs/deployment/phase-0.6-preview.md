# Phase 0.6 PostgreSQL preview deployment

This guide describes the reference topology for the in-progress ShuETL 0.6.0
package. The role graph is implemented, but the [acceptance ledger](../evidence/0.6/README.md)
is still open. Treat this configuration as a qualification fixture until the
ledger records the hosted PostgreSQL 18.6 results.

## Topology

Build one application image containing the exact ShuETL wheel, the trusted host
integration package, its ETLantic provider packages, and the approved profile.
Deploy that image by immutable digest for all roles. Run two gateways, two
schedulers, and two `runs` workers against one fresh PostgreSQL 18.6 database.
Add `actions` workers only when their provider handlers and resource policy are
qualified. No message broker is required by this graph.

The [Compose file](../../deploy/phase-0.6/compose.yml) is a single-host
qualification template. It expects the host integration image, secrets, and
profile to be supplied by the operator. It does not contain credentials or a
placeholder digest that could be mistaken for a deployable release.

For a host-managed process supervisor, install the same host image by digest
and use the [systemd unit](../../deploy/phase-0.6/systemd/shuetl-preview@.service)
with the [Podman launcher](../../deploy/phase-0.6/systemd/shuetl-preview-container).
The launcher rejects mutable image tags and runs each role from the configured
digest. It uses host networking so loopback probes remain host-local; set the
database URL for the host's PostgreSQL service and restrict gateway access at
the host firewall or reverse proxy. Configure a distinct probe port per unit.
Install both files at the paths in the unit, provision
`/etc/shuetl/phase-0.6.env` and the shared resource directories, then enable
`shuetl-preview@gateway`, `shuetl-preview@scheduler`, and
`shuetl-preview@worker`. Start `shuetl-preview@action-worker` only after its
provider handler package and resource policy are qualified.

The PostgreSQL 18.6 Compose service mounts its data at
`/var/lib/postgresql`, the official PostgreSQL 18 image volume location. The
image uses `/var/lib/postgresql/18/docker` as `PGDATA`.

The host package exports the trusted factory named by
`SHUETL_FACTORY` and the matching `--factory` CLI argument. For gateway starts,
it returns a production `HostIdentityAdapter` and authorizer. For scheduler and
worker starts, it returns an ETLantic service context with an explicit tenant,
workspace, service/workload principal, authorizer, and any worker-only secret
authorization or independently packaged action handlers. A factory must not
return a runner, store, scheduler, request credential, or ETL implementation.

## Fresh store and startup

Provision a new database for ETLantic 0.56.0. Keep the 0.5 application and its
database separate for rollback. Use a migration credential for the explicit
upgrade command and a separate runtime credential. ETLantic 0.56.0 currently
requires the runtime credential to have `CREATE` on its schema during managed
backend construction, because its migration-version helper runs
`CREATE TABLE IF NOT EXISTS` even when the version table already exists. This
does not meet the planned least-privilege boundary; treat the deployment as a
qualification fixture and do not claim production-preview support until this
upstream behavior or the accepted grant contract changes.

Configure the migration command with `SHUETL_PROFILE=postgresql-pilot`,
`SHUETL_ROLE=gateway`, `SHUETL_PROVIDER=postgresql`,
`SHUETL_IDENTITY=host`, the migration database URL, and the explicit
`SHUETL_POSTGRESQL_SSLMODE`. Run:

```sh
docker compose --profile operations run --rm migrate
```

The command must reach migration head
`014_cp1_complete_principal_idempotency_0_56`. Runtime roles perform a
read-only preflight and fail if the server is not PostgreSQL 18.6 or the schema
is fresh, behind, unknown, or corrupt. Do not start them against the 0.55
database. ShuETL does not convert prior durable work.

Before enabling the new gateway or scheduler, stop admissions and scheduling
in the retained 0.5 deployment. Re-enroll definitions, connections, and
schedules through the public APIs. Reconcile unfinished work and uncertain
external effects explicitly; do not copy or replay pending work across stores.
Rollback disables the 0.6 gateway and scheduler first, then restores authority
to the retained application and its original database.

## Runtime settings

Every role uses the same database URL, store ID, execution profile, tenant, and
workspace. The host supplies the runtime database URL through its secret
manager; do not place credentials in Compose source control.

| Variable | Preview value or rule |
| --- | --- |
| `SHUETL_PROFILE` | `postgresql-preview` |
| `SHUETL_ROLE` | `gateway`, `scheduler`, or `worker`; must match `--role` |
| `SHUETL_PROVIDER` | `postgresql` |
| `SHUETL_IDENTITY` | `host`; gateway requests use the host adapter, runtime roles use a separate service context |
| `SHUETL_FACTORY` | Installed trusted `package.module:callable`, equal to `--factory` |
| `SHUETL_STORE_ID` | One explicit ID shared by all roles |
| `SHUETL_TENANT_ID`, `SHUETL_WORKSPACE_ID` | One explicitly configured scope |
| `SHUETL_EXECUTION_PROFILE` | Installed upstream profile name or an operator-managed JSON profile path |
| `SHUETL_PROBE_PORT` | Loopback-only role probe port; distinct from the gateway HTTP port |
| `SHUETL_WORKER_KIND` | `runs` or `actions`, only on workers |
| `SHUETL_ARTIFACT_ROOT` | Same shared path on every role when reports/artifacts use files |
| `SHUETL_POSTGRESQL_SSLMODE` | `verify-full` for verified deployments; `disable` only for an isolated test database |

The supervisor assigns a new unique owner ID each time a scheduler or worker
starts. Set a `runs` worker's lease TTL longer than three times its poll
interval. `/live` and `/ready` on the runtime probe report only bounded role,
lifecycle, and reason values; they bind to `127.0.0.1` inside each container.
The gateway retains ETLantic's `/health` route and gates other requests on
fresh provider readiness.

## Operating and stopping

Scale the gateway, scheduler, and run worker with the Compose service names.
The `worker` and `scheduler` services can be scaled because each process
generates its own owner ID. A reverse proxy must balance gateway requests and
preserve the host application's authentication boundary.

Send SIGTERM or SIGINT to stop dispatch, mark readiness false, invoke upstream
drain where available, and wait for an active tick before closing its backend.
The grace interval reports an incomplete drain; the supervisor must terminate
the process if its platform deadline expires. An in-flight claim or external
effect can outlive request admission, and external effects remain subject to
ETLantic/provider idempotency and recovery contracts.

The deployment remains a bounded single-database preview. It does not claim
multi-region failover, capacity limits, exactly-once external effects, or
automatic migration of 0.5 durable work.
