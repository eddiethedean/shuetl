# Phase 0.6 qualification record

Status: partial development qualification. This record covers installed
baseline transfer and role startup only. It is not a PASS record for the 33
acceptance criteria or Gates A–C.

## Exact hosted artifacts

The current hosted qualification used source commit
`b03e4468a622a4ac9af4080a0e8ae9534f21a742` and PostgreSQL 18.6. CI built and
installed ShuETL and the reference wheels outside the checkout.

| Artifact | SHA-256 | Purpose |
| --- | --- | --- |
| `shuetl-0.6.0-py3-none-any.whl` | `d1944eb7def4c707787b2b958dafb71db0bb7d4020bf83103b763be443ef98a1` | Installed role/runtime under qualification |
| `shuetl_phase06_reference-0.0.1-py3-none-any.whl` | `d1bde3822e756e5c6bdebcf78b8eb0c187e6cea1359d7b72405b7fac65b2b3bc` | Separately installed workload and example transformation |
| CLI reference-host wheel | `1c3773dd72daa9c34080d7249aba9bf759866167ad5062737399acb176f64769` | Separately installed role CLI bindings |

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
[`hosted-gate0/`](hosted-gate0/). CLI role startup/readiness/SIGTERM records are
in [`hosted-cli/`](hosted-cli/). The corresponding [hosted run](https://github.com/eddiethedean/shuetl/actions/runs/37986479448)
passed.

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
on Python 3.11–3.13. It does not qualify active run execution, forced
termination, or multiple competing processes.

A supervisor regression injects an `unreachable` provider inspection followed
by a healthy result. It verifies the role reports `provider_unavailable`, keeps
liveness healthy, then restores readiness and usable upstream prerequisites.
This covers status mapping. A separate PostgreSQL integration test now interrupts
all runtime database connections through a local TCP fault proxy, observes
`/ready` fail with `provider_unavailable` while `/live` remains healthy, restores
connectivity, and observes readiness recover before SIGTERM shutdown. The new
case passed locally on PostgreSQL 18.6 and in hosted CI on Python 3.11–3.13
with no skips. It does not cover force termination or competing process
recovery.

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
