# Phase 0.4 production re-review

Date: 2026-09-13. Verdict: NEEDS FIXES.

The approved authority remains `docs/plans/PHASE_0_4_EXECUTION.md`, ADR-0010,
and AC-001–AC-038. The previous review is `PHASE_0_4_REVIEW.md`; the Luna
resolution report is in the conversation immediately preceding this review.
The same PostgreSQL pilot, migration, identity, lifecycle, diagnostics,
compatibility, operations and evidence boundary applies. No production code,
documentation, configuration, or prior verification artifact was changed in
this re-review. New files are verification artifacts for the open SOL-010
contract and this report. Backup automation remains excluded; runnable restore
guidance and recorded qualification remain required.

## Previous blockers

| Finding | Status | Verification and root-cause audit |
|---|---|---|
| SOL-010 | PARTIALLY FIXED | Original topic test passes; 38 labels now match the plan. New missing-proof-reference test fails: the checker accepts a PASS with empty command and artifact. Critical index rows still name unspecified probes. |
| SOL-011 | VERIFIED FIXED | Protected identity test passes. Direct native ETLanticAPI construction retains the exact bundle repository and registry, with the same production profile and caller/provider objects. Real PostgreSQL graph test passes. |
| SOL-012 | VERIFIED FIXED | Both protected tests pass. Configured capabilities now depend on configuration, availability remains exact-version-gated, and TLS mode appears in ordinary success, missing-extra and failed-readiness summaries without new doctor fields/check IDs. |
| SOL-013 | PARTIALLY FIXED | Protected topic test passes; manual execution of the new command fails because pg_dump does not accept the required ShuETL SQLAlchemy URL scheme. |
| SOL-014 | VERIFIED FIXED | Protected cancellation test passes. Cleanup disposes the engine on BaseException and re-raises cancellation unchanged; normal exceptions retain bounded readiness wrapping. |

SOL-001–SOL-009 remain resolved in their original phase 0.3 scope. Their
existing verification was rerun as part of the release gate and the phase 0.3
review suite. No previous test was weakened or removed.

## Acceptance criteria

For unchanged behavior, evidence includes the previous independently executed
PostgreSQL qualification recorded in the original review, current code
inspection, and the fresh release gate. This is not a claim that every prior
manual probe or another Python version was re-executed. Fresh PostgreSQL
integration ran with the exact 18.6 service and installed locked distributions.

| AC | Status | Evidence / limitation |
|---|---|---|
| AC-001 | VERIFIED | Metadata, lock, fresh build and wheel gate |
| AC-002 | VERIFIED | Exact 18.6 claim, live integration version assertion and recorded reference server |
| AC-003 | VERIFIED | Export contract and isolated wheel imports |
| AC-004 | VERIFIED | Explicit settings matrix inspection and existing compatibility tests |
| AC-005 | VERIFIED | Structural URL/secret validation and TLS enum/default retained |
| AC-006 | VERIFIED | Exact metadata validation precedes optional imports/engine construction |
| AC-007 | VERIFIED | Exact settings and explicit adapter requirements retained |
| AC-008 | VERIFIED | SOL-011 identity fix, shared engine/native providers, live graph construction |
| AC-009 | VERIFIED | Native production API retains caller and provider objects |
| AC-010 | VERIFIED | Unchanged bounded state classifier; prior real state probes and current inspection |
| AC-011 | VERIFIED | Exact head and inventory checks; live schema test |
| AC-012 | VERIFIED | Unchanged read-only inspection and facade paths; prior fresh catalog probe |
| AC-013 | VERIFIED | SOL-014 test plus unchanged locked, explicit idempotent close |
| AC-014 | VERIFIED | Unchanged CLI output/errors and public migration delegation |
| AC-015 | VERIFIED | Fresh live integration migration/inventory and provider constraint inspection |
| AC-016 | VERIFIED | Prior independently seeded upgrade at all four earlier heads; path unchanged |
| AC-017 | VERIFIED | Prior head no-op/unknown preservation probes; rejection path unchanged |
| AC-018 | VERIFIED | Prior two-revision close/reopen probe; canonical repository retained |
| AC-019 | VERIFIED | Prior canonical receipt restart comparison; store unchanged |
| AC-020 | VERIFIED | Prior same-payload restart/changed-payload 409 probe; store unchanged |
| AC-021 | VERIFIED | Prior eight-party barrier with independent engines and one acceptance; store unchanged |
| AC-022 | VERIFIED | Prior full event equality from persisted cursor after restart; store unchanged |
| AC-023 | VERIFIED | Prior independent barrier probe and fresh integration sequence test |
| AC-024 | VERIFIED | Fresh schedule/firing persistence integration and prior durable-backed restart probe |
| AC-025 | VERIFIED | Prior durable-backed duplicate claim and native atomic/early-return path unchanged |
| AC-026 | VERIFIED | Native API/facade route ownership preserved; current compatibility/OpenAPI gates |
| AC-027 | VERIFIED | SOL-012 capability facts and exact versions; live doctor test |
| AC-028 | VERIFIED | Protected doctor tests and bounded same-summary rendering; read-only path retained |
| AC-029 | VERIFIED | Prior full canonical-table dump/restore equality and readiness using native PostgreSQL connection inputs; current published instructions have the separate SOL-013 defect |
| AC-030 | VERIFIED | Fresh release and original compatibility suites |
| AC-031 | VERIFIED | Fresh boundary gate and change inspection |
| AC-032 | VERIFIED | Fresh isolated core/SQLite/PostgreSQL wheel installation/import gate |
| AC-033 | PARTIALLY SATISFIED | Exact matrix/service configured; no current-change live Actions execution is recorded. Evidence repair must distinguish configuration from execution (SOL-010). |
| AC-034 | PARTIALLY SATISFIED | Baseline release gate passes, but new open-blocker verification fails |
| AC-035 | PARTIALLY SATISFIED | Restore/admission topics added, but documented native-tool command fails (SOL-013) |
| AC-036 | PARTIALLY SATISFIED | Current meanings fixed; actual proof references remain missing and checker accepts no proof (SOL-010) |
| AC-037 | VERIFIED | Exact published provider and prior migration qualification retained |
| AC-038 | VERIFIED | Exact provider allocator and prior independent barrier qualification retained |

## Open findings

### SOL-010 — Current evidence gate accepts a PASS without verification references

Severity: High.

Disposition: BLOCKER.

Related AC: AC-036, AC-033.

Location: `docs/evidence/0.4/README.md:44` and its restart/concurrency/recovery
rows; `scripts/check_evidence.py:164` through proof validation.

Problem: the labels now match the approved contract, but the actual command
and artifact columns still say things such as "PostgreSQL barrier probe" and
"independent same-key submission outcome". They identify no executable file,
test selector, linked recorded procedure, or results artifact. The checker
combines the task label with the proof columns, so the label alone satisfies
the keyword check even if both proof columns are empty.

Evidence: copying the current index and clearing only AC-021's command and
artifact produces `check_evidence.check(...) == []`. The new verification
fails for the expected reason. Searches show no repository barrier probe or
prior-head probe matching those index descriptions. The old review records
that independent probes passed, but the index does not reference it or record
instructions to reproduce those probes.

Relationship to current change: this is the unresolved verification-reference
portion of the original SOL-010, whose resolution explicitly required actual
executable or recorded manual proof beyond keyword edits. It retains that ID.

Why it matters: a release reviewer cannot establish what command/result proves
each current requirement, and the gate can certify no verification at all.

Why this blocks the current change: AC-036 requires an actual AC-to-passing-proof
mapping. Current-topic labels alone do not meet it. A configured CI matrix is
also not evidence that AC-033's executions occurred.

Required behavior: identify actual commands/test selectors and concrete results
or linked manual procedures for the current ACs, record executed environments
and limitations, and reject PASS entries that lack verification references.
Existing independent evidence may be referenced; this does not require another
equivalent set of probes if the recorded proof is adequate. Do not claim
unexecuted environments or CI runs.

Acceptance criteria: every required proof can be located and assessed from the
index; empty command/artifact cannot pass merely because the task label matches;
the unchanged 0.3 proof contract remains valid.

Verification artifact: `test_phase_0_4_evidence_contract.py`,
`test_sol_010_evidence_rejects_a_pass_without_command_or_artifact`.

Verification status: EXPECTED BLOCKER VERIFICATION — confirmed failing before
handoff. Original SOL-010 topic test passes and remains protected. The new test
is a necessary lower bound; filling columns with arbitrary text is insufficient.

### SOL-013 — The published backup command cannot use ShuETL's required URL

Severity: Medium.

Disposition: BLOCKER.

Related AC: AC-035.

Location: `README.md:203` through the restore command block.

Problem: the newly added `pg_dump` command passes `$SHUETL_DATABASE_URL`
directly to the native PostgreSQL tool. ShuETL requires
`postgresql+psycopg://...`; libpq tools recognize native PostgreSQL connection
strings such as `postgresql://...`. They interpret the ShuETL-only scheme as
a database name instead. The restore variable also has to serve both native
pg_restore and ShuETL doctor, whose accepted schemes differ. In addition, the
commands do not explicitly carry the configured ShuETL TLS mode into native
tools, so equivalent connection trust settings need documentation.

Evidence / executed manual verification artifact:

```text
docker exec shuetl-sol04-review pg_dump -U shuetl --schema-only \
  'postgresql+psycopg://shuetl@localhost/shuetl'
```

On PostgreSQL/pg_dump 18.6 this exits 1 with database
`postgresql+psycopg://shuetl@localhost/shuetl` not existing. With the same
connection represented as `postgresql://shuetl@localhost/shuetl`, a schema-only
dump succeeds. Running the README command without forcing a username tries
the default local role instead; its failure is also reproducible. These are
disposable local test connection values, not operator credentials.

Relationship to current change: remediation added the missing operator
procedure, but it was not verified with the required configuration format.
The original SOL-013 required verification of the documented procedure, so
this is PARTIALLY FIXED under the same ID, not a new finding.

Why it matters: following the published procedure cannot produce the promised
backup and restore from a valid pilot configuration. Keyword-only topic
verification passes despite the operational failure.

Why this blocks the current change: the required AC-035 operator procedure is
not executable as documented, and the previous finding explicitly required
its real-server verification before closure.

Required behavior: document native libpq-compatible backup/restore connection
inputs and their relationship to ShuETL's SQLAlchemy URLs, with explicit TLS
and trust handling. Restore into an appropriate isolated target and run doctor
using a valid ShuETL URL before traffic. Keep credentials/trust material out
of results and evidence.

Acceptance criteria: execute the documented dump/restore procedure on 18.6
using valid pilot settings, preserve canonical rows/identities, and obtain
passing readiness before admission; publish a concrete proof reference.

Verification artifact: the manual command/reproducer above and the existing
protected documentation test. Verification status: manual native-tool
reproducer fails as expected; original topic test passes but does not prove
command compatibility. No data-loss defect in the provider is alleged.

## Quality gates

| Gate | Executed | Result / classification |
|---|---|---|
| Original Sol 0.4 and 0.3 focused suites | Yes | 34 passed |
| Full release gate before new review artifacts | Yes | PASS: 103 passed, 3 PostgreSQL skips without URL, all lock/format/lint/type/boundary/build/artifact/OpenAPI/clean-wheel/evidence steps |
| Real PostgreSQL integration on 18.6 | Yes | 3 passed |
| Published native backup command probe | Yes | FAIL — unresolved SOL-013; native-URI control succeeded |
| Missing-proof-reference regression test | Yes | FAIL — expected SOL-010 blocker verification |
| Ruff format/lint and Pyright after additions | Yes | PASS |
| Full pytest suite after additions | Yes | 102 passed, 3 skipped, 2 failed: expected SOL-010 regression test and review-induced sdist hash change; wheel hash unchanged |
| Diff whitespace check | Yes | PASS |
| Current-change live Actions matrix | No | Workflow inspected, execution not claimed |

Adding verification files changes the sdist input, so the recorded source
artifact hash will need the normal refresh during remediation. This is not a
new production defect and no hash check was bypassed in this review.

## Follow-ups, observations, convergence

No new unrelated follow-up defect was discovered. Open issues #1 (Actions
runtime deprecation) and #2 (historical TestClient transport) remain existing
follow-ups and are not remediation requirements. The non-failing AnyIO
BlockingPortal warning remains an observation.

Three of five previous blockers are verified fixed; two are partially fixed.
There are no new finding IDs or separate remediation-caused blockers. The
operational defect is within the existing SOL-013 resolution contract. The
loop is converging; the next remediation must finish the recorded-proof and
executable-runbook requirements rather than add unrelated behavior. Only one
phase 0.4 remediation attempt is recorded, so repeated-attempt escalation is
not yet warranted. Hand back only SOL-010 and SOL-013.

NEEDS FIXES
