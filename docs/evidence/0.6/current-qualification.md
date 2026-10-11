# Phase 0.6 current development qualification

**Observed 2026-10-11.** This record follows the ETLantic 0.57.2 selection and
supersedes older development snapshots for the checks listed here. It records
local qualification of installed artifacts, not hosted release approval. The
source tree was based on `a0b3a1258cf199e755e045cd9b6e9e8b4c218511` with local
changes; rebuild and rerun the affected gates after committing or changing the
candidate.

## Candidate artifact identities

| Artifact | SHA-256 | Scope |
| --- | --- | --- |
| ShuETL 0.6.0 wheel | `7a22a8b51f65af9150481fbc897a9858e2ff8d249f86db703926bdcc3808b826` | Installed app used by Gate 0, native CLI and container roles |
| Gate 0 reference workload wheel | `80e55db32d07124dcbd6a80177aed7be1383c3fec6bf1626fb15ed110367e1d1` | Independently installed ETL workload |
| CLI/container host wheel | `2585ce1ab66bbfea536cbd81d725b63ff0efdf970082ae77f6da16ee17e1a2ef` | Independently installed role bindings, including the HTTP client used by the reference gateway |
| ETLantic core, FastAPI, SQLModel and SQL provider | `0.57.2` | Published artifacts; no source patch |

## Executed local qualification

| Check | Result | Boundary |
| --- | --- | --- |
| Installed Gate 0 with controls, immutable resources, retry retention and bounded artifact cleanup | PASS on Python 3.11.15, 3.12.13 and 3.13.16 against PostgreSQL 18.6 | [3.11](local-2026-10-11/gate0-python-3.11.json), [3.12](local-2026-10-11/gate0-python-3.12.json), [3.13](local-2026-10-11/gate0-python-3.13.json) |
| Native four-role CLI with active work, cooperative signals and forced termination | PASS on Python 3.12.13 | [CLI result](local-2026-10-11/cli-postgresql.json) |
| Linux/amd64 container with all four roles and active-work shutdown | PASS on Python 3.12.13; image `sha256:fbbd469cbe53aed77a1c9a2efaf0ea3dd5c0e22a670db5cc51305894b477d1b7` | [Container result](local-2026-10-11/container-postgresql.json) |
| 0.5.0/0.55.0 retained store to fresh 0.6.0/0.57.2 enrollment and rollback | PASS for seeded old acceptance and re-enrollment rehearsal | [Transition result](local-2026-10-11/transition.json) |
| Installed crash matrix | 20 of 22 cases pass; two accepted-preparation recovery cases fail | [Crash result](local-2026-10-11/crash-matrix.json), upstream [#299](https://github.com/eddiethedean/etlantic/issues/299) |

Gate 0 controls cover no-write effective execution, refusal to replay uncertain
partial effects, failed-work retry versus deliberate rerun, alias/upsert-key
behavior, schema drift without false completion, and successful retry of an
immutable uploaded input after expiry using retained bytes. Resource checks cover
checksum/version/owner/scope, access from a replacement worker, expiry, retry
retention, and bounded report/artifact cleanup. The expired-input case forces a
first source-read failure before any sink effect, then retries the canonical run
after access to the retained input is restored.

The fault matrix passes gateway acceptance, scheduler recovery, run-worker
lease/effect recovery, stale-worker fencing and cancellation boundaries. Its
only failures are the two windows documented in #299: action-worker death after
CP1 acceptance before durable submission, and death after durable submission
before reporting the preparation result. These failures remain blocking and are
not skipped or treated as expected passes.

The transition rehearsal verifies store incompatibility, re-enrollment of a
definition into a fresh store, no automatic replay, and mounting the retained
0.5 application/store for rollback. Its accepted run is a seeded reconciliation
record; it does not reproduce an interrupted external effect. It also does not
exercise production traffic or a systemd supervisor.

## Remaining release blockers

- [ETLantic #299](https://github.com/eddiethedean/etlantic/issues/299): accepted
  run preparation does not reconcile across action-worker death and reporting
  deadline expiry.
- [ETLantic #121](https://github.com/eddiethedean/etlantic/issues/121): the
  published default preflight is a static `read_only_plan`, not authorized,
  bounded live provider readiness.
- Hosted qualification and review of the frozen final source/wheel remain
  pending. The evidence above is local and based on an uncommitted candidate.

The earlier deterministic sort/deduplication finding (#283) and SQL action
handler implementation finding (#286) are fixed in 0.57.2. Their published
wheel evidence is in the [0.57.2 upstream audit](../../reviews/ETLANTIC_0_57_2_REQUIREMENTS_AUDIT.md).
No Phase 0.6 release criteria are closed by this development record alone.

## Reproduction

Use a disposable PostgreSQL 18.6 server and exact built wheels. The Gate 0
command below was run with Python 3.11.15, 3.12.13 and 3.13.16; the role
environment contained the ShuETL wheel with its `postgresql`, `server`, and
`test` extras plus the separately built host and workload wheels.

```sh
python spikes/phase_0_6_gate_0.py \
  --disposable-admin-url "$DISPOSABLE_POSTGRES_ADMIN_URL" \
  --python "$INSTALLED_WHEEL_PYTHON" \
  --shuetl-wheel "$SHUETL_WHEEL" \
  --reference-wheel "$REFERENCE_WORKLOAD_WHEEL" \
  --source-commit "$QUALIFIED_SOURCE_COMMIT" \
  --controls --resources --retention \
  --output "$GATE0_EVIDENCE_JSON"
```

The native CLI and container commands are captured by
[`phase_0_6_cli_gate.py`](../../../spikes/phase_0_6_cli_gate.py); the transition
and failure reproductions are captured by
[`phase_0_6_transition.py`](../../../spikes/phase_0_6_transition.py) and
[`phase_0_6_faults.py`](../../../spikes/phase_0_6_faults.py). The serialized
observations linked above preserve actual per-run evidence and exact wheel
hashes.
