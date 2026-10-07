# Phase 0.6 store transition

The preview starts with a fresh database at
`014_cp1_complete_principal_idempotency_0_56`. The runtime does not attempt to
open or upgrade a 0.55 store, and it does not convert durable submissions,
reports, schedules, or artifacts between stores. Keep the released 0.5
application and database available until the new system's admissions and
scheduling authority are deliberately enabled.

## Operator sequence

1. Provision a fresh PostgreSQL 18.6 database, runtime principal, migration
   principal, and any shared artifact/resource volume.
2. Run `shuetl database upgrade` using the migration credential and explicit
   `postgresql-pilot` migration settings.
3. Verify schema head 014 and runtime grants. Start no preview role until the
   read-only 18.6/schema preflight passes.
4. Disable new admissions and native scheduling on the retained 0.5 system.
   Inventory pending submissions, accepted firings, leases, retries, and
   external effects.
5. Re-enroll definitions, connections, and schedules through the public
   control-plane APIs. Reconcile uncertain external effects before deciding
   whether to submit corresponding work in the new store.
6. Start the gateway and supervised scheduler/workers from one digest-pinned
   application image. Verify each role's own readiness before enabling
   traffic or schedule creation.
7. For rollback, stop new 0.6 admissions and scheduling, reconcile new-store
   work, then restore the old service and its original store as the sole
   trigger authority.

## Qualification status

The repository includes this handoff procedure and the Compose template. It
does not include a rehearsed database cutover, a 0.55 workload inventory,
provider grant capture, interrupted-work reconciliation, rollback transcript,
or a tested image digest. No migration or rollback rehearsal is claimed.
