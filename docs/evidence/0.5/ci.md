# Phase 0.5 verification runs

The implementation baseline was verified locally on macOS 26.5.2 arm64 with Python 3.11.15, 3.12.13 and 3.13.11 and uv 0.11.3. The configured CI workflow is `.github/workflows/checks.yml`, with quality, live PostgreSQL 18.6, and release-gate jobs for Python 3.11–3.13. Hosted run [36654931532](https://github.com/eddiethedean/shuetl/actions/runs/36654931532) passed all nine jobs for qualification baseline commit `6e69b578d45983e2426c900253c7768a0ab1da5b`. The follow-up AC-017 configured-provider proof passed locally on Python 3.12.13 after that run; it is not part of the hosted result.

| Verification | Local result | Scope / limitation |
| --- | --- | --- |
| Quality gate | PASS — 183 passed, 5 skipped on Python 3.11.15, 3.12.13 and 3.13.11 | Ruff format/lint, Pyright, boundary and full pytest. The five skips per runtime are the PostgreSQL cases, executed separately below. Each run reported the upstream Starlette/AnyIO deprecation warning. |
| PostgreSQL integration | PASS — 5 passed, 0 skipped on Python 3.11.15, 3.12.13 and 3.13.11 | PostgreSQL 18.6; every JUnit result was checked for tests and zero skips. Each run reported the upstream Starlette/AnyIO deprecation warning. |
| Release gate | PASS — Python 3.12.13 | `scripts/check_release.py`: lock/sync, Ruff, Pyright, boundary, full pytest, deterministic build, artifact contents, OpenAPI, clean core/SQLite/PostgreSQL wheel environments and examples, and evidence consistency. |
| Hosted CI baseline | PASS — run 36654931532 | Quality, live PostgreSQL 18.6, and Phase 0.5 release-gate jobs passed on Python 3.11, 3.12 and 3.13 for commit `6e69b57`. |
| AC-017 review remediation | PASS — 14 passed on Python 3.12.13 | Local targeted proof for existing foreign registry and schedule records in direct and mounted apps; one upstream Starlette/AnyIO deprecation warning. Added after hosted baseline run 36654931532, so this follow-up was not run in hosted CI. |

The local PostgreSQL service is a disposable `postgres:18.6-bookworm` container on loopback port 55432. It is not a production deployment. The CI workflow rejects a missing `SHUETL_DATABASE_URL` and rejects skipped tests in its dedicated PostgreSQL JUnit result.
