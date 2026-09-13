# Phase 0.4 production re-review — second remediation audit

Date: 2026-09-13. Verdict: NEEDS FIXES.

Authority remains `docs/plans/PHASE_0_4_EXECUTION.md`, ADR-0010, and
AC-001–AC-038. Previous reviews are `PHASE_0_4_REVIEW.md` and
`PHASE_0_4_RE_REVIEW.md`; the latest Luna resolution report is in the preceding
conversation. No application code, operator documentation, configuration,
package metadata, evidence ledger, or prior Sol verification was modified.
This review adds this report and one verification test for unresolved SOL-010.

## Acceptance criteria

Unchanged technical behavior retains the independently executed qualification
recorded in the original review, supplemented by current code inspection and
fresh gates. Those prior probes were not all re-executed in this review.
Python 3.12.13 and PostgreSQL 18.6 were executed locally; current-change Actions
execution and Python 3.11/3.13 execution are not claimed.

| AC | Status | Evidence |
|---|---|---|
| AC-001 | VERIFIED | Metadata, lock, artifact and isolated wheel gates |
| AC-002 | VERIFIED | Fresh real-server integration asserts 18.6 |
| AC-003 | VERIFIED | Export tests and isolated installed-wheel checks |
| AC-004 | VERIFIED | Settings matrix inspection and compatibility tests |
| AC-005 | VERIFIED | Structural URL validation, TLS enum/default and redaction inspection |
| AC-006 | VERIFIED | Metadata qualification before optional imports; existing tests |
| AC-007 | VERIFIED | Adapter validation and exact settings type; existing tests |
| AC-008 | VERIFIED | Protected SOL-011 test, native graph inspection and live construction |
| AC-009 | VERIFIED | Direct API composition retains exposed/caller objects |
| AC-010 | VERIFIED | Prior real state probes and unchanged bounded classification |
| AC-011 | VERIFIED | Fresh migration/inventory test and unchanged head checks |
| AC-012 | VERIFIED | Prior PostgreSQL catalog probe and unchanged read-only execution |
| AC-013 | VERIFIED | Protected cancellation test and lock/idempotent disposal inspection |
| AC-014 | VERIFIED | CLI/migration flow inspection and previous independent migration probes |
| AC-015 | VERIFIED | Fresh live migration/inventory and provider constraint inspection |
| AC-016 | VERIFIED | Original independent seeded upgrade at all four earlier heads |
| AC-017 | VERIFIED | Original no-op/unknown-state probes and unchanged rejection path |
| AC-018 | VERIFIED | Original independently closed/reopened two-revision comparison |
| AC-019 | VERIFIED | Original full CP1 receipt comparison across restart |
| AC-020 | VERIFIED | Original same-key restart and changed-payload conflict probe |
| AC-021 | VERIFIED | Original eight-party barrier with independent engines/stores |
| AC-022 | VERIFIED | Original full replay equality and persisted-cursor restart probe |
| AC-023 | VERIFIED | Original independent barrier plus fresh concurrent-event test |
| AC-024 | VERIFIED | Original durable-backed restart and fresh firing persistence test |
| AC-025 | VERIFIED | Original durable-backed duplicate claim and native atomic path |
| AC-026 | VERIFIED | Unchanged facade/router ownership and HTTP/OpenAPI gates |
| AC-027 | VERIFIED | Protected doctor tests and fresh live doctor output |
| AC-028 | VERIFIED | Protected redaction/TLS tests and unchanged read-only rendering |
| AC-029 | VERIFIED | Fresh native dump/restore: 17 tables, 26 rows equal; restored doctor passes; prior wider identity qualification retained |
| AC-030 | VERIFIED | Full compatibility suite and fresh PostgreSQL integration |
| AC-031 | VERIFIED | Boundary gate and native ownership inspection |
| AC-032 | VERIFIED | Separate installed core/SQLite/PostgreSQL wheel environments |
| AC-033 | PARTIALLY SATISFIED | Required matrix configured; current-change live CI execution unrecorded |
| AC-034 | PARTIALLY SATISFIED | Baseline full gate passes; added SOL-010 verification fails as intended |
| AC-035 | VERIFIED | Corrected libpq/ShuETL URL separation, TLS/operations topics and successful populated restore/readiness |
| AC-036 | NOT SATISFIED | Existing command/file references still map several ACs to unrelated or incomplete verification |
| AC-037 | VERIFIED | Fresh published-provider migration and original earlier-head qualification |
| AC-038 | VERIFIED | Native PostgreSQL allocator, original independent barrier and fresh integration |

The underlying behavior of AC-018, for example, retains prior independent
proof. The new ledger's chosen test still does not prove AC-018. This is an
evidence-mapping defect under AC-036, not a new allegation that revision
persistence is broken.

## Previous blockers

| Finding | Status | Verification |
|---|---|---|
| SOL-010 | PARTIALLY FIXED | Topic and empty-reference tests pass; new unrelated-proof test fails; actual ledger mappings remain inaccurate |
| SOL-011 | VERIFIED FIXED | Protected object-identity test passes; direct native API composition retained |
| SOL-012 | VERIFIED FIXED | Both protected tests pass; live doctor shows TLS mode and truthful capabilities |
| SOL-013 | VERIFIED FIXED | Protected doc test passes; corrected native dump/restore on populated 18.6 succeeds, exact rows match, restored doctor exits 0 |
| SOL-014 | VERIFIED FIXED | Protected cancellation/disposal test passes; BaseException cleanup retained |

SOL-001–SOL-009 remain verified fixed in their original Phase 0.3 scope; their
protected verification was rerun. None was weakened or removed.

## Open finding

### SOL-010 — Locatable but unrelated verification is still accepted as proof

Severity: High.

Disposition: BLOCKER.

Related AC: AC-036; AC-033 remains an explicit execution-evidence limitation.

Location: `docs/evidence/0.4/README.md:40` through the restart/concurrency rows;
`docs/evidence/0.4/qualification.md:23`; `scripts/check_evidence.py` proof
validation.

Problem: the syntax/empty-reference portion is fixed, but the authoritative
AC-to-passing-proof mapping is not. The checker combines the correct task
label with its proof and then accepts any existing artifact and command with
recognized syntax. An unrelated metadata test can certify concurrent
submissions while the required test/procedure remains absent from that proof.

Evidence: both the original topic test and the missing-reference test pass.
The new test keeps AC-021's correct task label and changes only its proof to
the real, passing package-metadata test. The checker accepts it; verification
fails at the expected AC-021 assertion. This checks semantic relevance rather
than another empty-field permutation.

The actual committed mappings also contain concrete mismatches:

| AC | Referenced proof | Missing required behavior |
|---|---|---|
| AC-012 | Phase 0.3 SQLite read-only test | PostgreSQL catalog/no-DDL proof |
| AC-014 | Phase 0.3 review suite | New database-upgrade CLI behavior; suite does not invoke that command |
| AC-016 | Three-test PostgreSQL suite | Fixture initializes fresh schema; no earlier-head seeded upgrades |
| AC-018 | Restart/idempotency/schedule test | No comparison of two immutable revisions across closed/reopened engines |
| AC-020 | Same restart test | No changed-payload conflict or post-restart repeat acceptance |
| AC-021 | Three-test PostgreSQL suite | No concurrent submission acceptance or independent barrier |
| AC-022 | Same restart test | Event asserted before reopen; no replay from persisted cursor after restart |
| AC-025 | Same restart test | Duplicate firing checked without proving canonical durable submission identity |

The qualification paragraph asserts prior manual probes passed, but supplies
the same unrelated three-test command instead of their actual procedure or
specific recorded verification provenance. Several affected rows point only
to the insufficient test file. Topic words and file existence do not resolve
the original review's explicit demand for relevant verification references.

Relationship to current change: this is the unresolved semantic proof-mapping
root cause of SOL-010. No new finding ID or functionality expansion applies.

Why it matters: an assessor following the release ledger cannot reproduce or
locate the proof of the requirements that its chosen command does not test.

Why this blocks the current change: AC-036 explicitly requires each current
AC to map to passing proof; accepted unrelated proof violates that boundary
even though independently reviewed runtime behavior and ordinary gates pass.

Required behavior: map each AC to relevant executable tests or specific
recorded manual verification with an assessable procedure/result. The existing
original independent qualification can be referenced where adequate; do not
require equivalent probes to be rerun solely for test count. Correct the
command/provenance column rather than substitute an unrelated passing suite.
Semantic validation must not be satisfied by the task label alone. Preserve
the previous 0.3 proof contract and truthful environment/CI limitations.

Acceptance criteria: every row's chosen proof actually constrains its required
behavior; recorded manual proof is identifiable; package metadata cannot be
accepted as concurrent-submission proof merely because the task says so.

Verification artifact:
`test_phase_0_4_evidence_semantics.py::test_sol_010_evidence_rejects_package_metadata_as_concurrent_submission_proof`.

Verification status: EXPECTED BLOCKER VERIFICATION — confirmed failing for the
expected assertion before handoff. Manual audit of the actual mappings also
fails as listed above; a special case for the regression's exact file name
would not resolve the finding.

ESCALATION RECOMMENDED: SOL-010 has now survived two remediation attempts.
Use a stronger implementation/reasoning model for the AC-to-proof audit. The
specification is explicit and no architecture redesign is indicated; both
attempts repaired labels or syntax without establishing the required proof
relationships.

## Restore verification

Fresh disposable server: `postgres:18.6-bookworm`. After the existing real
PostgreSQL suite seeded canonical state, native commands were executed using
libpq URLs and explicit `PGSSLMODE=disable` against the isolated test service:

```text
pg_dump --format=custom --file=/tmp/shuetl-0.4.backup <native-source-URL>
createdb <isolated-restore-database>
pg_restore --exit-on-error --dbname=<native-restore-URL> /tmp/shuetl-0.4.backup
SHUETL_DATABASE_URL=<ShuETL-restore-URL> shuetl doctor --format json
```

All exited 0. Doctor reported status pass, server 18.6, required head and
capabilities. A separately executed full-row snapshot comparison (all public
tables, sorted JSON row mappings) established exact equality across 17 tables
and 26 rows. The disposable service was stopped afterward. This closes the
native URL compatibility and populated restore/readiness portion of SOL-013.

## Quality gates

| Gate | Executed | Result / classification |
|---|---|---|
| Full release gate before new review artifacts | Yes | PASS: 104 passed, 3 PostgreSQL skips; all lock/sync/format/lint/type/boundary/build/artifact/OpenAPI/clean-wheel/evidence stages |
| Protected Phase 0.3/0.4 suites | Yes | 35 passed |
| Real PostgreSQL integration on 18.6 | Yes | 3 passed |
| Corrected populated native backup/restore | Yes | PASS; exact rows and restored readiness |
| New semantic evidence verification | Yes | FAIL — EXPECTED BLOCKER VERIFICATION, SOL-010 |
| Format, lint, Pyright and diff whitespace after additions | Yes | PASS |
| Full test suite after additions | Yes | 103 passed, 3 skipped, 2 failed: expected SOL-010 assertion and review-induced stale sdist hash; wheel hash unchanged |
| Current-change Actions matrix | No | Workflow inspected; execution not claimed |

New review artifacts change sdist inputs, so hashes require normal remediation
refresh. This review does not alter the ledger or bypass its hash gate.

## Follow-ups, observations and convergence

Open GitHub issues were searched. Existing low-severity follow-ups #1 (Actions
runtime deprecation) and #2 (historical TestClient transport) remain separate.
No new unrelated follow-up issue was found or created. The existing non-failing
AnyIO BlockingPortal deprecation warning remains an observation.

Four of five original Phase 0.4 blockers are verified fixed. One remains under
its stable SOL-010 ID; no new blocker attributable to runtime remediation was
found. The loop has narrowed, but evidence remediation has stalled across two
attempts. Hand back only SOL-010 with the escalation above.

NEEDS FIXES
