# Phase 0.6 CI and release gate

The workflow defines Python 3.11, 3.12, and 3.13 jobs. The quality matrix
installs all extras without a PostgreSQL service. PostgreSQL qualification and
the release-gate test environment install only the extras used by the SQL
preview profile; the clean-wheel gate separately verifies each optional extra
in its own environment. This keeps the Foundry plugin outside the SQL profile's
allowlist while still checking its packaged pin. CI provisions a separate
runtime PostgreSQL role, uses a PostgreSQL 18.6 service, and builds/checks wheel
and source artifacts. The fixture grants the runtime role schema `CREATE`:
ETLantic 0.56.0's `current_version` helper runs
`CREATE TABLE IF NOT EXISTS` unconditionally, and PostgreSQL requires schema
`CREATE` even when the table exists. This exercises the rest of the managed
role graph but leaves AC-008's planned no-`CREATE` startup boundary open. The
release gate runs the PostgreSQL role fixture from an isolated installed wheel.
`check_pytest_no_skips.py` rejects skips in required PostgreSQL integration
tests. The release gate clears the PostgreSQL profile environment for the
general test suite, then retains it for the installed-wheel PostgreSQL check;
the clean-wheel gate also clears those settings for core and SQLite examples
while retaining them for PostgreSQL qualification. The installed `test` extra
provides pytest for that isolated fixture. The dedicated integration job runs
its PostgreSQL tests with the PostgreSQL environment. PRs run the implementation
gate with open acceptance rows allowed; tag runs use strict evidence mode.

| Gate | Workflow job | Current evidence |
| --- | --- | --- |
| A — static and regression | `quality` | [Run 37664305784](https://github.com/eddiethedean/shuetl/actions/runs/37664305784) passed on Python 3.11–3.13. |
| B — PostgreSQL | `postgresql-integration` | Run 37664305784 passed on PostgreSQL 18.6 and Python 3.11–3.13; the no-`CREATE` grant remains unqualified. |
| C — clean artifact | `release-gate` | Run 37664305784 passed the build, metadata, isolated extras, installed-wheel PostgreSQL fixture, OpenAPI, boundary, and full check script on Python 3.11–3.13. PR mode used `--allow-open`. |

`scripts/check_release.py --allow-open` runs lock, sync, Ruff, Pyright,
boundary, test, build, artifact, OpenAPI, clean-wheel, and evidence consistency
checks without authorizing release. The default command adds
`check_evidence.py --release`, which rejects open criteria or gates. A release
tag cannot publish until all AC rows and Gate A–C are PASS and the evidence
outcome is `proceed-to-0.6-preview`.

Run 37664305784 validated implementation source commit
`625a7b3f38e35fef2124accdfd0eba3dc0d6c847`. The PR gate used `--allow-open`;
it does not authorize preview while acceptance rows remain open.
