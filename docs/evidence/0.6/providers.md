# Phase 0.6 provider and capability matrix

Status: qualification inventory, not a final support promise. The ETLantic SQL
provider is marked **Experimental** in version 0.57.0. The rows below record
observed combinations and keep untested modes out of the release claim until
the full AC-028–033 review is complete. CSV append, PostgreSQL snapshot append,
and one primary-key upsert case passed the hosted installed-artifact matrix on
Python 3.11–3.13.

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
The local PostgreSQL 18.6 run used Python 3.13.9, the installed ShuETL wheel
SHA-256 `b39057130779cab9975b9820e0fe565581375007f2854525fa42fa6b4a9c8b15`,
and updated reference workload wheel SHA-256
`5eeb1756e0dce0b1f022adad94953a4680e01806f35b15df2679266be16062e2`. Hosted
records for all three rows are from [CI run 37982842772](https://github.com/eddiethedean/shuetl/actions/runs/37982842772),
source commit `0595029938c8917b904470a19c4ccf3d277e7e28`; hosted evidence is
stored per interpreter under [hosted-gate0/](hosted-gate0/).
