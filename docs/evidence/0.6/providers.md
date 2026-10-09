# Phase 0.6 provider and capability matrix

Status: frozen 0.6 candidate matrix; qualification inventory, not a final
support promise. The ETLantic SQL provider is marked **Experimental** in
version 0.57.0. The candidate scope is exactly the three executed rows below:
CSV landing snapshot to PostgreSQL append, PostgreSQL snapshot to PostgreSQL
append, and PostgreSQL snapshot to the single declared-primary-key upsert case.
The table freezes each row's observed control path. No other pairing, mode or
control path is in the candidate claim. CSV append, PostgreSQL snapshot append,
and the primary-key upsert passed the hosted installed-artifact matrix on
Python 3.11–3.13, but release support remains conditional on the outstanding
AC-028–033 evidence, including file-resource immutability and expiry.

## Ownership boundary

ShuETL selects pinned packages, creates role processes, supplies trusted
contexts and opaque resource bindings, exposes the upstream control plane, and
qualifies installed combinations. It does not implement connector reads/writes,
transform semantics, quality rules, scheduling, retries, or effect recovery.

ETLantic owns canonical pipeline/specification models, planning and run
coordination. The independently installed ETLantic provider packages own file
and PostgreSQL connector behavior, write-mode semantics, schema inspection,
resource identity, and effect reconciliation. The reference workload package
owns only its example transformation implementation and quality specification.
The adopting host owns identity/resource enrollment and any application policy.

## Executed transfer combinations

The first row's native-scheduled behavior applies to the CSV-to-PostgreSQL
append case. The two PostgreSQL-source rows are qualified only for the manual
control paths shown; do not infer scheduled, retry, override, alternate-key,
or other write-mode support from these observations.

| Source | Sink | Mode | Control path | Observed result | Qualification state |
| --- | --- | --- | --- | --- | --- |
| `local-files` CSV landing snapshot | PostgreSQL `sink.target` and `sink.rejected` | PostgreSQL append | Manual HTTP preparation, native scheduler, duplicate trigger | Exact accepted/rejected rows and six independent sink effect receipts; hosted Python 3.11–3.13 records in [Gate 0](hosted-gate0/) | Installed baseline passes; does not qualify immutable-resource ownership or all provider options |
| PostgreSQL `input.source_rows` repeatable snapshot | PostgreSQL `sink.postgres_target` and `sink.postgres_rejected` | PostgreSQL append | Manual HTTP preparation through action worker; run worker executes accepted receipt | Hosted PostgreSQL 18.6 records on Python 3.11–3.13 produced `[[10, "ok", 4]]` and `[[11, "no", 120]]`; input was read-only for the runtime principal | Installed baseline passes; does not qualify all provider options |
| Same PostgreSQL repeatable snapshot | PostgreSQL `sink.upsert_target` keyed by primary key `id`; rejected rows append | PostgreSQL upsert | Two distinct manual submissions with a source-row update between runs | Hosted Python 3.11–3.13 runs changed key `10` from `[[10, "ok", 4]]` to `[[10, "ok", 10]]`, kept one target row, and observed two distinct run IDs per interpreter | Installed case passes; only this declared primary-key case is observed |

Both paths execute a transformation implementation packaged outside ShuETL,
then ETLantic quality acceptance/rejection, and publish through ETLantic's
PostgreSQL connector. The workload projects away an unused input field, casts
integers, lowercases text, multiplies the quantity, filters invalid input, and
checks not-null, range, and membership rules. These are fixture observations,
not a general transform/operator support claim.

The separate portable-plan conformance command builds and executes a
`dtcs.transform-plan/2` plan with the installed ETLantic local compiler
(`etlantic-local` 0.50.0). It observes select/drop/rename, lowercase, filter,
output schema, and not-null, range, membership, and uniqueness quality
outcomes. The plan declares sort before keyed deduplication, but reversing two
duplicate-key inputs changes the chosen row: the local compiler accepts the
canonical sort action but ignores its field-reference expression. This fails
the deterministic-deduplication requirement and is tracked in
[ETLantic #283](https://github.com/eddiethedean/etlantic/issues/283). Its exact
input, both order-dependent outputs, accepted and rejected rows, plan actions,
and compiler identity are retained in `postgresql-gate0.json`. The three live
PostgreSQL connector runs still execute the separately packaged native
reference transformation and do not establish portable-plan pushdown.

The PostgreSQL-source fixture gave its runtime role `USAGE` on `input` and
`SELECT` on `input.source_rows`, with no `INSERT`, `UPDATE`, or `DELETE` rights
there. Sink permissions are separate. The harness independently queried both
destination tables and the provider effect ledger after worker execution.

## Explicitly unqualified

| Capability | Current decision |
| --- | --- |
| PostgreSQL source modes other than `snapshot` | Not supported by the ETLantic 0.57 SQL connector contract |
| PostgreSQL sink `overwrite`, `replace`, `merge`, aliases, or alternate key selection | Not qualified for the ShuETL 0.6 candidate; one primary-key upsert case is observed |
| PostgreSQL-to-PostgreSQL alias/resource overlap rejection and schema drift | Not observed in the ShuETL installed workload |
| Canonical local sort followed by keyed deduplication | Unqualified: ETLantic 0.57.0 ignores the plan's sort field expression, so the retained duplicate changes with input order; see [ETLantic #283](https://github.com/eddiethedean/etlantic/issues/283) |
| Immutable input-resource ownership, checksum mismatch, expiry, retention, and cleanup | Not observed; the CSV fixture uses a temporary landing file |
| Effective overrides, disabled-writer policy, retry versus deliberate new-run identity | Not observed in this matrix |
| Provider action handlers for connection/catalog/schema/preflight, rotation, revocation, and deadlines | Not qualified by the role startup/transfer fixture |
| SQL/PySpark execution, preview, and destination provisioning | Not included in the baseline qualification |

These entries remain open against AC-028–033 where required. A provider's
public API or its own conformance suite does not substitute for ShuETL's
installed-process observation. Do not advertise these combinations as
qualified until the corresponding upstream evidence and ShuETL sink/control
observations are attached.

## Reproduction

The expanded installed harness is [phase_0_6_gate_0.py](../../../spikes/phase_0_6_gate_0.py);
the separate workload package is [tests/reference_phase06](../../../tests/reference_phase06/pyproject.toml).
The local PostgreSQL 18.6 run used Python 3.13.9, source commit
`b03e4468a622a4ac9af4080a0e8ae9534f21a742`, ShuETL wheel SHA-256
`d1944eb7def4c707787b2b958dafb71db0bb7d4020bf83103b763be443ef98a1`, and
reference workload wheel SHA-256
`d1bde3822e756e5c6bdebcf78b8eb0c187e6cea1359d7b72405b7fac65b2b3bc`. The
current hosted records for all three rows are from [CI run 37989243217](https://github.com/eddiethedean/shuetl/actions/runs/37989243217),
source commit `c064aa9ead7b78d9f6451895d6799e088ab8682f`; hosted evidence is
stored per interpreter under [hosted-gate0/](hosted-gate0/).
