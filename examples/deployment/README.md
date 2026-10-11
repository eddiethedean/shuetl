# Four process deployment examples

These templates use the 0.6.0 candidate and published ETLantic 0.57.2.
Full deployment/transition qualification remains open. See the
[release ledger](../../docs/evidence/0.6/README.md). Install your independently
packaged host binding factory; the qualification host is a test fixture.

## Prepare the artifact and store

Build the frozen wheel and retain its SHA-256 with the host wheel and lock.
Install the same artifacts into every process environment. The container base
is pinned by digest; record the resulting application image digest as well.
The host wheel must include its qualified connector dependencies and configure
the shared artifact root, authorizer, profile and canonical scope.

Provision a **new** PostgreSQL 18.6 store. Run `shuetl database upgrade` once
with a separate migration identity and the gateway `postgresql-pilot` profile.
Grant runtime DML/sequence rights required by the provider, without schema
CREATE, object ownership or membership in the migration role. Runtime processes
use `postgresql-preview`. Never run the new migrations against the retained
0.5/0.55 rollback store.

Use the shared configuration in the [runtime guide](../../docs/PHASE_0_6_RUNTIME.md).
Protect environment files with mode 0600 and keep migration credentials out of
runtime files. Configure `verify-full` TLS and the server CA in production.
Set `SHUETL_BINDINGS_FACTORY=your_host.shuetl_bindings:create` and the same
tenant/workspace/environment/security-domain/store IDs in all runtime roles.
Use worker-only resource credentials for execution connectors. Supply shared
immutable inputs and reports through the upstream resource bridge and
`artifact_root`; a local path alone does not establish immutable ownership.

## Ordinary Linux supervisor

Install `shuetl@.service` into `/etc/systemd/system/`. Install the candidate and
host wheels under `/opt/shuetl/venv`. Put common settings in
`/etc/shuetl/common.env`, and these role settings in separate files:

| File | Role settings | Loopback probe |
| --- | --- | --- |
| `gateway.env` | `SHUETL_ROLE=gateway` | `SHUETL_PROBE_PORT=8090` |
| `scheduler.env` | `SHUETL_ROLE=scheduler` | `SHUETL_PROBE_PORT=8091` |
| `runs.env` | `SHUETL_ROLE=worker`, `SHUETL_WORKER_KIND=runs` | `SHUETL_PROBE_PORT=8092` |
| `actions.env` | `SHUETL_ROLE=worker`, `SHUETL_WORKER_KIND=actions` | `SHUETL_PROBE_PORT=8093` |

Create the `shuetl` system account and `/var/lib/shuetl`, owned by that account.
Start only after migration and public read-only provider checks succeed:

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now shuetl@gateway shuetl@scheduler shuetl@runs shuetl@actions
curl --fail http://127.0.0.1:8090/ready
curl --fail http://127.0.0.1:8091/ready
curl --fail http://127.0.0.1:8092/ready
curl --fail http://127.0.0.1:8093/ready
```

The gateway defaults to loopback port 8000. Put an authenticated TLS reverse
proxy in front of it. Stop with `systemctl stop`; the supervisor waits at most
120 seconds before terminating the process group. Choose that deadline for
your workload and reconcile any uncertain effects after forcible termination.

## Container

Place the exact ShuETL wheel and your host wheel under `wheels/` and build once:

```sh
docker build --platform linux/amd64 -t shuetl-candidate .
export SHUETL_IMAGE="$(docker image inspect shuetl-candidate --format '{{.Id}}')"
printf '%s\n' "$SHUETL_IMAGE"
```

The executed build target is Linux amd64. Linux arm64 currently requires
additional native build tooling for the `dpcs` dependency and is unqualified.
Use that single image ID in all four launches. Each environment file contains
common and role settings from the table above. The host factory uses
`/resources` as its shared artifact root. Prepare that volume for UID 10001.

```sh
docker run -d --name shuetl-gateway --stop-timeout 120 \
  --env-file gateway.env --mount source=shuetl-resources,target=/resources \
  -p 127.0.0.1:8000:8000 "$SHUETL_IMAGE" \
  serve --role gateway --host 0.0.0.0 --port 8000
docker run -d --name shuetl-scheduler --stop-timeout 120 \
  --env-file scheduler.env --mount source=shuetl-resources,target=/resources \
  "$SHUETL_IMAGE" serve --role scheduler
docker run -d --name shuetl-runs --stop-timeout 120 \
  --env-file runs.env --mount source=shuetl-resources,target=/resources \
  "$SHUETL_IMAGE" serve --role worker --kind runs
docker run -d --name shuetl-actions --stop-timeout 120 \
  --env-file actions.env --mount source=shuetl-resources,target=/resources \
  "$SHUETL_IMAGE" serve --role worker --kind actions
```

Probes bind to each container's loopback. Query them from inside that container,
for example `docker exec shuetl-runs python -c
'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8092/ready").read().decode())'`.
Publishing a probe port does not expose a loopback-only listener. Readiness loss
removes a gateway from traffic; it is not a command to forcibly restart active
workers. No broker is required by this PostgreSQL topology.

## Transition and rollback

Disable old admissions and scheduling before handoff. Inventory every unfinished
run and reconcile actual destination effects; retain uncertainty explicitly.
Provision the separate new store, re-enroll canonical definitions/resources and
recreate schedules through public APIs. Enable one scheduler authority and
switch traffic only after readiness and qualification succeed. There is no
automatic durable-state conversion or cross-store replay.

For rollback, stop new admissions/scheduling, drain or reconcile new work, then
restore traffic and the sole scheduler authority to the retained 0.5.0/0.55.0
deployment. Keep both stores and evidence until reconciliation is complete.
These instructions still require the release's executed transition rehearsal.
