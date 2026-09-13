# Phase 0.4 CI execution record

## Qualified runtime matrix

Observed on 2026-09-13 from the completed GitHub Actions job API and logs.

- Run: [34776217942](https://github.com/eddiethedean/shuetl/actions/runs/34776217942), attempt 2.
- Tested source commit: `b28bf9aedbcf3f9cbb212ffa5012dae15c43a1eb` on `main`.
- Trigger: push; workflow: CI calling `.github/workflows/checks.yml`.
- Completed conclusion: `success`; all nine required jobs passed.
- Locked train: ETLantic / FastAPI adapter / SQLModel adapter 0.52.1,
  SQLAlchemy 2.0.52, Psycopg / psycopg-binary 3.3.5.
- Server: `postgres:18.6-bookworm`; actual server version asserted as 18.6.
- Runner: Ubuntu x86_64; uv 0.11.3; Python 3.11, 3.12 and 3.13.

```console
gh run view 34776217942 --json headSha,status,conclusion,jobs
```

| Job | Python | Result | GitHub job |
| --- | --- | --- | --- |
| Quality | 3.11 | PASS | [103775185773](https://github.com/eddiethedean/shuetl/actions/runs/34776217942/job/103775185773) |
| Quality | 3.12 | PASS | [103775186491](https://github.com/eddiethedean/shuetl/actions/runs/34776217942/job/103775186491) |
| Quality | 3.13 | PASS | [103775164900](https://github.com/eddiethedean/shuetl/actions/runs/34776217942/job/103775164900) |
| PostgreSQL integration | 3.11 | PASS — 4 passed, no skips | [103775164567](https://github.com/eddiethedean/shuetl/actions/runs/34776217942/job/103775164567) |
| PostgreSQL integration | 3.12 | PASS — 4 passed, no skips | [103775179168](https://github.com/eddiethedean/shuetl/actions/runs/34776217942/job/103775179168) |
| PostgreSQL integration | 3.13 | PASS — 4 passed, no skips | [103775180264](https://github.com/eddiethedean/shuetl/actions/runs/34776217942/job/103775180264) |
| Phase 0.4 release gate | 3.11 | PASS | [103775164933](https://github.com/eddiethedean/shuetl/actions/runs/34776217942/job/103775164933) |
| Phase 0.4 release gate | 3.12 | PASS | [103775164533](https://github.com/eddiethedean/shuetl/actions/runs/34776217942/job/103775164533) |
| Phase 0.4 release gate | 3.13 | PASS | [103775165157](https://github.com/eddiethedean/shuetl/actions/runs/34776217942/job/103775165157) |

The live suite includes two-workspace canonical firing/durable identity after
restart. Default release-suite logs record 120 passed and 4 skipped; the three
live jobs independently execute all four PostgreSQL tests. The 3.12 release log
ends with clean-wheel verification, evidence consistency and
`Phase 0.4 release gate passed`.

Attempt 1 had eight passing jobs and one clean-wheel failure: its pip index
response did not yet list etlantic-sqlmodel 0.52.1. The other interpreters and
local clean installs resolved that published package. The failed workflow was
rerun without changing source, dependencies, gates or assertions. Attempt 2
completed successfully. This publication/index timing failure is preserved in
the run history rather than presented as an implementation fix.

Limitation: qualifies recorded source revision; see ci.md for tested commit.
The record is committed after its tested source revision. It does not claim
the recorded run tested subsequent evidence-document edits. CI success is not
independent Sol approval.

## Original 0.52.0 runtime matrix

Observed on 2026-09-13 using the GitHub Actions run/job API and completed logs.
This is newly executed CI evidence, not a reconstruction of a previous review.

- Run: [34771524213](https://github.com/eddiethedean/shuetl/actions/runs/34771524213).
- Tested source commit: `114da1ab264088e487e7f216e7d1f14ee778f6aa` on `main`.
- Trigger: push; workflow: CI calling `.github/workflows/checks.yml`.
- Run status: `completed`; conclusion: `success`.
- Runner: Ubuntu 24.04.5 x86_64; uv 0.11.3.
- PostgreSQL integration interpreters: CPython 3.11.15, 3.12.3 and 3.13.12.

Verification command:

```console
gh run view 34771524213 --json headSha,status,conclusion,jobs
```

Every job below completed successfully, including its required steps.
Job links provide the primary execution provenance.

| Job | Python | Result | GitHub job |
| --- | --- | --- | --- |
| Quality | 3.11 | PASS | [103761874395](https://github.com/eddiethedean/shuetl/actions/runs/34771524213/job/103761874395) |
| Quality | 3.12 | PASS | [103761874431](https://github.com/eddiethedean/shuetl/actions/runs/34771524213/job/103761874431) |
| Quality | 3.13 | PASS | [103761874476](https://github.com/eddiethedean/shuetl/actions/runs/34771524213/job/103761874476) |
| PostgreSQL integration | 3.11 | PASS — 3 passed, no skips | [103761874408](https://github.com/eddiethedean/shuetl/actions/runs/34771524213/job/103761874408) |
| PostgreSQL integration | 3.12 | PASS — 3 passed, no skips | [103761874299](https://github.com/eddiethedean/shuetl/actions/runs/34771524213/job/103761874299) |
| PostgreSQL integration | 3.13 | PASS — 3 passed, no skips | [103761874470](https://github.com/eddiethedean/shuetl/actions/runs/34771524213/job/103761874470) |
| Phase 0.4 release gate | 3.11 | PASS | [103762025483](https://github.com/eddiethedean/shuetl/actions/runs/34771524213/job/103762025483) |
| Phase 0.4 release gate | 3.12 | PASS | [103762025491](https://github.com/eddiethedean/shuetl/actions/runs/34771524213/job/103762025491) |
| Phase 0.4 release gate | 3.13 | PASS | [103762025510](https://github.com/eddiethedean/shuetl/actions/runs/34771524213/job/103762025510) |

All jobs sync the committed `uv.lock` with
`uv sync --locked --all-groups --extra test --extra sqlite --extra postgresql`.
The provider train is ETLantic, etlantic-fastapi and etlantic-sqlmodel 0.52.0,
SQLAlchemy 2.0.52, and Psycopg / psycopg-binary 3.3.5. The PostgreSQL jobs start
the `postgres:18.6-bookworm` service and run
`uv run pytest tests/integration/test_postgresql.py -q` against that live server.
The schema/doctor test asserts actual server version `18.6`; the remaining
tests exercise persistent restart/idempotency/schedules/firings and concurrent
event sequencing. No connection credential is copied into this record.

Quality jobs run format, lint, Pyright, boundary and the default test suite.
Release jobs run `uv run python scripts/check_release.py`, including lock/sync,
format/lint/types, boundary, tests, deterministic build, artifact inspection,
OpenAPI comparison, three isolated wheel installs and evidence consistency.
The default suite's three PostgreSQL skips do not establish integration proof;
the separate live jobs above do. The 3.12 release log records 113 passed and
3 skipped, followed by `Phase 0.4 release gate passed`.

The first 0.4 run, 34771360202, failed because an implementation-side ledger
unit test assumed pre-existing `dist` artifacts. The tested commit above makes
that unit self-contained with isolated hash fixtures and a full no-error
assertion. Real archive/fresh-build verification and all required gates remain
enabled; protected Sol verification is unchanged.

Limitation: qualifies recorded source revision; see ci.md for tested commit.
This record is committed after the run it describes, so the recorded run does
not claim to have tested these subsequent evidence-document edits. Historical
manual probes remain attributed to their original independent reviews. CI
success is engineering evidence, not independent Sol approval or a release tag.
The existing Node.js action-runtime warning remains follow-up issue #1.
