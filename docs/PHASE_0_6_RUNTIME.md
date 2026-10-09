# Phase 0.6 role runtime

**Implementation guide; deployment qualification remains open.** Use the same
exact ShuETL 0.6.0 candidate and ETLantic 0.57.0 train for every process. This
guide describes the implemented interfaces; it does not certify a final wheel,
real deployment, process-failure behavior or transition from a 0.5 store.

## Host binding factory

The host installs a trusted module that exports a synchronous `create(settings)`
factory and configures its import path as `SHUETL_BINDINGS_FACTORY`. The module
creates host-owned identity and resource bridges, then returns:

- `GatewayBindings` for the gateway, with the host's `Authorizer`, production
  `Profile`, planning-context factory and `HostIdentityAdapter`;
- `RuntimeBindings` for scheduler/run/action processes, with the same profile,
  authorizer and planning bridge plus a canonical, service-principal
  `ControlPlaneContext` for the configured deployment scope. The optional
  keyword-only `action_handlers=` mapping supplies asynchronous connector
  handlers from trusted backend packages. ShuETL forwards this mapping to
  upstream `SQLModelBackendConfig`; upstream validates action names, handler
  contracts, authorization, leases and results. Gateway bindings do not contain
  these handlers or resolve their secrets.

The factory may set `close=` to release host-owned resources. ShuETL owns and
closes the backend it constructs; ETLantic/providers own service semantics,
stores and execution behavior. The runtime binding has no HTTP request, host
principal dependency, or ASGI hook. Do not provide execution callbacks or
construct a second backend graph in this module.

## Shared configuration

Supply these settings to all four process kinds. Keep the database URL in a
permission-restricted secret source. Runtime credentials must have the provider's
required DML and sequence grants, without schema creation, object ownership, or
membership in the migration role.

```sh
SHUETL_PROFILE=postgresql-preview
SHUETL_PROVIDER=postgresql
SHUETL_IDENTITY=host
SHUETL_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@DB/STORE
SHUETL_POSTGRESQL_SSLMODE=verify-full
SHUETL_BINDINGS_FACTORY=host_application.shuetl_bindings:create
SHUETL_TENANT_ID=tenant-a
SHUETL_WORKSPACE_ID=workspace-a
SHUETL_ENVIRONMENT=production
SHUETL_SECURITY_DOMAIN=domain-a
SHUETL_STORE_ID=production
SHUETL_PROBE_PORT=8090
SHUETL_SHUTDOWN_GRACE_SECONDS=30
SHUETL_DISPATCH_INTERVAL_SECONDS=1
```

`SHUETL_PROBE_PORT` must be unique for each process on a shared host. `/live`
and `/ready` bind to loopback on this port; the gateway HTTP listener is
configured separately. Gateway readiness requires completed ASGI lifespan
startup, a bound listener and fresh public provider health. Startup or unexpected
server failure exits unsuccessfully. Runtime readiness requires healthy, fresh
provider and role prerequisites. ETLantic ticks recheck prerequisites and control
admission, so ShuETL permits bootstrap and recovery ticks after a fresh provider
check even while role readiness is false. Temporary failures remain non-ready
until upstream prerequisites recover; no tick runs while provider health is
unavailable or stale.

## Start and stop

Apply the selected provider migrations once with the operator's migration
identity before starting runtime processes. Keep that identity out of the
gateway, scheduler and worker environments. Start one gateway, one scheduler,
one run worker and one action worker as separate supervised processes:

```sh
shuetl serve --role gateway --factory host_application.shuetl_bindings:create \
  --host 0.0.0.0 --port 8000

SHUETL_ROLE=scheduler \
  shuetl serve --role scheduler \
  --factory host_application.shuetl_bindings:create

SHUETL_ROLE=worker SHUETL_WORKER_KIND=runs \
  shuetl serve --role worker --kind runs \
  --factory host_application.shuetl_bindings:create

SHUETL_ROLE=worker SHUETL_WORKER_KIND=actions \
  shuetl serve --role worker --kind actions \
  --factory host_application.shuetl_bindings:create
```

Send SIGTERM for cooperative shutdown. Processes fail readiness, stop admission
or tick dispatch, ask the upstream role to drain, and keep owned resources open
while active work remains. If the configured grace interval expires, the
process remains non-ready and draining until work completes or the external
supervisor terminates it. ShuETL does not promise to interrupt external effects.

## Store transition

Use a separately provisioned store at the selected provider schema head. Keep
the 0.5/0.55 deployment available for rollback with only one scheduler authority
active at a time. Reconcile unfinished work and uncertain external effects
before directing traffic or schedules to the new store. There is no implicit
conversion, rolling upgrade, or replay between stores. These steps require a
deployment rehearsal before 0.6 release qualification.
