# Phase 0.6 qualification record

Status: partial development qualification. This record covers installed
baseline transfer, multi-process coordination, CLI cleanup ordering, and
source-level PostgreSQL outage recovery. It is not a PASS record for the 33
acceptance criteria or Gates A–C.

## Exact hosted artifacts

The current hosted qualification used source commit
`c064aa9ead7b78d9f6451895d6799e088ab8682f` and PostgreSQL 18.6. CI built and
installed ShuETL and the reference wheels outside the checkout.

| Artifact | SHA-256 | Purpose |
| --- | --- | --- |
| `shuetl-0.6.0-py3-none-any.whl` | `3921b62c7d8c27b6a7d5be69e3a4e36ae1a3030ba9020a1db8dcbfbb73060d24` | Installed role/runtime under qualification |
| `shuetl_phase06_reference-0.0.1-py3-none-any.whl` | `5668ffa6f89724feba2b5b36d0fcfede08661676a602202818e7d8319226a714` | Separately installed workload and example transformation |
| CLI reference-host wheel | `1bc27163c3c30487a386fd019210594f807253fc50a443ef289754cbf9c5621a` | Separately installed role CLI bindings |

ETLantic core, FastAPI adapter, SQLModel provider and SQL connector are pinned
to 0.57.0; the published local implementation plugin is pinned separately to
0.50.0. ShuETL's exact declared runtime pins are unchanged by this fixture.

## Observed installed behavior

The Gate 0 harness passed on Python 3.11, 3.12 and 3.13 against PostgreSQL
18.6. It ran three installed transfer cases through public ETLantic plan,
preparation, action-worker and run-worker contracts:

- CSV landing snapshot to PostgreSQL append sinks, including manual execution,
  native scheduled execution and duplicate-trigger identity.
- PostgreSQL repeatable snapshot to separate PostgreSQL append sinks, including
  manual execution and select-only access to the input schema.
- PostgreSQL repeatable snapshot to a PostgreSQL sink keyed by declared primary
  key `id`. Two separate submissions, with a source update between them, leave
  one target row containing the updated value; both runs have distinct run IDs.

All three cases verify typed normalization, filtering, quality
acceptance/rejection, exact destination rows and provider effect receipts. The
full per-interpreter records, grants, run reports and plans are in
[`hosted-gate0/`](hosted-gate0/). CLI role startup/readiness/SIGTERM and cleanup
records are in [`hosted-cli/`](hosted-cli/). The corresponding [hosted run](https://github.com/eddiethedean/shuetl/actions/runs/37989243217)
passed on Python 3.11–3.13.

The independent reference host also runs a portable plan through the installed
ETLantic local compiler. Selection, drop, rename, lowercase, filtering, output
schema and required/range/set/uniqueness quality outcomes pass. The same plan's
canonical sort action is ignored before keyed deduplication: reversing two
same-key inputs changes the retained row from quantity 4 to 3. This blocks
deterministic deduplication qualification and is tracked in
[ETLantic #283](https://github.com/eddiethedean/etlantic/issues/283); it is not
claimed as a supported ShuETL capability.

The repository's active-worker signal regression passes locally and in the
quality matrix using a deterministic SQLite barrier. A separate PostgreSQL
integration test blocks the scheduler's leader-lease acquisition, sends SIGTERM,
and verifies readiness remains false and the backend stays open after grace
expiry until the lease call returns. That test passed locally and in hosted CI
on Python 3.11–3.13. It does not qualify active run execution or forced
termination.

A supervisor regression injects an `unreachable` provider inspection followed
by a healthy result. It verifies the role reports `provider_unavailable`, keeps
liveness healthy, then restores readiness and usable upstream prerequisites.
This covers status mapping. A PostgreSQL integration test interrupts all runtime
database connections through a local TCP fault proxy, observes `/ready` fail
with `provider_unavailable` while `/live` remains healthy, restores connectivity,
and observes readiness recover before SIGTERM shutdown. The test now covers
scheduler, run-worker and action-worker roles. The full dedicated PostgreSQL
18.6 integration file passed locally (9 passed, 0 skipped). Hosted run
37984396221 qualifies the earlier scheduler-only case; hosted qualification of
the two worker-role cases awaits CI for the current source. These tests do not
cover force termination or competing process recovery.

## Limitations and release status

The ETLantic SQL provider describes live PostgreSQL connectors as Experimental.
Only the three rows in [`providers.md`](providers.md) are observed in the ShuETL
installed workload. PostgreSQL write modes beyond append and the one declared
primary-key upsert case, aliases/alternate upsert keys, schema drift, effective
overrides, disabled-writer behavior, input-resource retention/expiry, retries
versus new runs, and provider action deadlines remain unqualified.

This record does not qualify final artifact hashes, migration/rollback,
PostgreSQL process failure injection, or acceptance criteria AC-001–AC-033.
Those requirements remain open in the [evidence index](README.md); release
approval is withheld.
