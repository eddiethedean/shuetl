# Phase 0.4 final-blocker remediation

Scope: FINAL-001 and FINAL-002 only. The authorized dependency correction is
ETLantic 0.52.1; ShuETL continues to expose the exact upstream provider objects.
This implementation report is not independent release approval.

## FINAL-001 — Byte-valued database URLs disclose secrets in validation errors

Status: FIXED

Related AC: AC-005

Root cause: The pre-validation redaction boundary wrapped strings but left byte
inputs in Pydantic's retained error input.

Production changes: `src/shuetl/settings.py` normalizes both database URL aliases
to `SecretStr` before validation. Valid UTF-8 bytes retain their accepted value;
invalid UTF-8 becomes a redacted invalid URL and is rejected.

Before-fix verification: A byte URL with a missing required role exposed its
password and hostname through `ValidationError.json()`.

After-fix verification: `tests/unit/test_settings_redaction.py` checks both aliases,
missing-field failures, invalid schemes, invalid UTF-8 and valid byte input.
Together with the protected SOL-001 verification, all eight cases passed before
the dependency-train update.

Related regression tests: Protected Phase 0.4 settings validation verification.

Additional tests: Seven cases distinguish error serialization from string
rendering and preserve valid byte-input compatibility.

Resolution: Secrets are wrapped before Pydantic can retain either alias in an
error, including errors unrelated to the URL field.

### Subsequent final-check structured-input remediation

The final check reopened FINAL-001 under AC-005: unsupported mapping inputs
were returned unchanged by the redaction helper and retained in Pydantic's
type-error input. The original byte fix remains intact, but was insufficient
for that input class.

`_redact_database_url_input` now preserves None and accepted secret/string/byte
inputs while replacing every unsupported type with an empty mapping. This
contains no original input, invokes no user repr/str, and remains invalid for
the field, including in the nullable memory profile. It does not coerce invalid
configuration into an accepted value.

Before-fix verification: all six
`test_final_001_structured_url_errors_are_redacted` cases failed for disclosed
sentinel coordinates through both aliases and constructor/model/JSON paths.
After-fix verification: all 15 tests in `test_settings_redaction.py` passed;
the focused redaction and protected Phase 0.3/0.4 suites returned 49 passed.
Additional tests protect unsupported list/object rejection without rendering
and valid SecretStr/explicit None compatibility. Existing review artifacts and
quality-gate configuration are unchanged. No follow-up work was included.

## FINAL-002 — Firing deduplication collides across workspaces

Status: FIXED

Related AC: AC-024, AC-025

Root cause: `MemoryScheduleStore` indexed firings by a scope-free logical key.
The SQLModel snapshot adapter inherited that index, returning another workspace's
canonical firing and durable submission for the same nominal occurrence.

Production changes: Upstream ETLantic commit `f0e31bab` scopes the internal index
by tenant, workspace and logical key. Snapshot loading reconstructs that index
from canonical records, preserving legacy firing IDs. Public logical keys and
the durable store's existing scoped idempotency contract remain unchanged.
ShuETL pins the corrected 0.52.1 core and companion packages, without a wrapper,
monkey patch or copied provider implementation.

Before-fix verification: The original 0.52.0 memory, SQLite and PostgreSQL paths
returned `created=False` for the second workspace; the legacy-snapshot case
failed the same invariant.

After-fix verification: Upstream `tests/schedule/test_firing_scope.py` passed all
four cases, including PostgreSQL 18.6, with real leader leases. A built-wheel
probe through ShuETL's complete PostgreSQL bundle also passed restart identity.
These initial probes used a local upstream wheel and are not publication proof.

Related regression tests: Upstream schedule and SQLModel suites passed;
ShuETL's existing PostgreSQL persistence suite passed against the original train.

Additional tests: ShuETL's
`test_workspace_firing_and_durable_identity_survive_restart` exercises two
workspaces through the real bundle, canonical durable IDs, one outbox record
per scope and close/reopen duplicate identity.

Resolution: The underlying provider index enforces caller scope, including
snapshot reload, without changing public APIs or migration heads.

## Follow-ups and protected verification

Existing follow-ups (Actions runtime and historical test transport) are unchanged.
No new unrelated follow-up candidates were discovered. Protected assertions,
test discovery and gates remain intact. Phase 0.3 version-specific compatibility
fixtures were updated from 0.52.0 to the authorized 0.52.1 runtime requirement;
their compatibility assertions were not weakened.

## Published-train qualification and gates

ETLantic's replacement `v0.52.1` tag targets
`2d21df409e007d840963fc7141d45bd7ca2f1998`. All 37 upstream check jobs passed in
[run 34775693083](https://github.com/eddiethedean/etlantic/actions/runs/34775693083)
before publishing. The first unpublished tag was replaced with explicit user
authorization after version-bound companion evidence failed; no checks were
bypassed. Medallantic goldens differ only because facade-version provenance
participates in fingerprints; DuckDB manifest evidence and the SQLModel
compatibility matrix were regenerated. Their assertions remain intact.

The exact core, FastAPI and SQLModel 0.52.1 packages were resolved from PyPI into
`uv.lock` and forcibly reinstalled with the locked sync. All three installed
distributions report version 0.52.1 and no local-wheel `direct_url.json`.

- Published-train PostgreSQL suite: 4 passed, no skips, PostgreSQL 18.6.
- Earlier-head migration probe: all four heads passed; canonical logical and
  revision records were seeded through public registry APIs, compared unchanged
  after public `upgrade`, and every required provider table was present.
- Settings verification: 8 passed (seven new cases plus protected SOL-001).
- Local lint, formatting and type checking: passed.

The migration probe used a disposable database, separately recreated for each
prior head. It used no copied DDL, local upstream implementation or patched
installed package. The PostgreSQL suite exercises persistent restart identity,
concurrent event ordering and the actual upstream bundle.

The complete locked local release gate passed. ShuETL
[CI run 34776217942](https://github.com/eddiethedean/shuetl/actions/runs/34776217942)
passed all nine jobs on source `b28bf9aedbcf3f9cbb212ffa5012dae15c43a1eb` after
rerunning an initial Python 3.12 clean-wheel publication/index timing failure.
No source or gate changed for the rerun. Detailed primary provenance and the
historical original-train record are retained in `docs/evidence/0.4/ci.md`.

## Quality gate report

| Gate | Executed | Result | Notes |
| --- | --- | --- | --- |
| Locked sync / lock check | Yes | PASS | Published PyPI 0.52.1 train |
| Ruff format / lint | Yes | PASS | No exclusions added |
| Pyright | Yes | PASS | Zero errors |
| Boundary / OpenAPI | Yes | PASS | Exact upstream composition retained |
| Default suite | Yes | PASS | 120 passed; 4 PostgreSQL skips |
| Live PostgreSQL suite | Yes | PASS | 4 passed, no skips; actual 18.6 |
| Earlier-head upgrade probe | Yes | PASS | Four prior heads preserve canonical records |
| Build / artifact / fresh archive hashes | Yes | PASS | Deterministic build |
| Core / SQLite / PostgreSQL clean wheels | Yes | PASS | Three isolated installations |
| Evidence / redaction checks | Yes | PASS | Approved AC requirements retained |
| Upstream release checks | Yes | PASS | All 37 jobs before publication |
| ShuETL CI matrix | Yes | PASS | Nine jobs, Python 3.11/3.12/3.13; attempt 2 |

The initial Python 3.12 CI failure is environmental publication/index timing,
not a weakened gate. Local source/wheel probes above are distinguished from
fresh published-package evidence. Subsequent evidence edits are not claimed as
tested by the recorded source run.

## Remediation summary

Blockers received: 2
Blockers fixed: 2
Blockers remaining: 0
Verification conflicts: 0
Escalations: 0
New follow-up candidates: 0

READY FOR SOL RE-REVIEW
