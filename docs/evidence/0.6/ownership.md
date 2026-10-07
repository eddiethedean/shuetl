# Phase 0.6 responsibility and resource ownership

## Component boundaries

| Owner | Responsibilities |
| --- | --- |
| Host application/integration package | Authentication, membership, service-principal creation, configured scope, authorization policy, secret-reference policy, profile/provider allowlist, independent provider packages, and shared file/artifact volume policy. |
| ShuETL | Strict preview settings, compatibility checks, read-only PostgreSQL preflight, managed backend construction, gateway identity guard, role selection, bound scheduler callback, runtime service context wiring, loopback probes, request/tick readiness gates, signal handling, and once-only cleanup. |
| ETLantic and provider packages | Canonical specifications/revisions, planning, run admission, durable stores, schedule semantics, firing and submission identity/recovery, worker leases/fencing, attempts/retries/cancellation, connector execution, reports, artifacts, and action jobs. |
| Database operator | Fresh 0.56 database, migration role, migration execution, runtime grants, backups, TLS, and database availability. |
| Deployment supervisor | Replicas, reverse proxy, secret injection, health checks, process deadlines, image digest, log routing, and final termination after an exceeded grace window. |

## Resource ownership

Each process creates and closes its own ETLantic managed backend and SQLAlchemy
engine. The short-lived preflight engine is disposed before backend creation.
The engine and provider stores are not returned through `HostRuntimeBindings`.
The host factory owns its callback resources and may return a `close()` hook;
ShuETL closes the backend before invoking that hook, once per process.

All roles use the configured store ID and database URL. The host configuration
must keep tenant and workspace identifiers identical across the gateway,
scheduler, and workers. Each scheduler/run worker receives a fresh unique owner
ID per start. An `actions` worker receives a fresh upstream worker ID.

For file-based inputs or reports, the host provisions one shared resource
location and configures the same artifact root in every process. A path is not
a resource authorization token. Resource ownership, checksum validation,
cross-worker access, retention, and cleanup still require the open qualification
cases.

## Security boundaries

The gateway may authenticate requests and authorize control-plane operations.
It does not create a scheduler or execution host, run connector code, or resolve
pipeline secrets. Scheduler and worker processes do not import a gateway app
factory or request credential verifier. Workers receive an explicit service
context; run workers may also receive a host-owned late-binding authorizer.
Action handlers must be supplied by independent provider packages and are
loaded only by action workers.

The factory reference is an operator-selected code import, not a sandbox.
Factory errors and provider inspection failures are reduced to bounded safe
diagnostics at the CLI and probes. A worker deployment is not considered
qualified merely because the gateway starts.
