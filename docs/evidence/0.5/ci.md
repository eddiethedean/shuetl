# Phase 0.5 verification and release runs

## Published release

ShuETL 0.5.0 was published to [PyPI](https://pypi.org/project/shuetl/0.5.0/)
on 2026-09-30 UTC from annotated tag [`v0.5.0`](https://github.com/eddiethedean/shuetl/tree/v0.5.0),
which resolves to commit `d846c3dd15b517def5c736e831202a603ca0e080`. PyPI records
the wheel upload at 02:27:06 UTC and the source distribution at 02:27:08 UTC.

- Pre-tag [CI run 36659423353](https://github.com/eddiethedean/shuetl/actions/runs/36659423353)
  passed all nine quality, PostgreSQL, and Phase 0.5 release-gate jobs on Python
  3.11, 3.12, and 3.13 for the final commit. This includes the AC-017
  configured-provider denial proof.
- Tag-triggered [Release run 36659686930](https://github.com/eddiethedean/shuetl/actions/runs/36659686930)
  passed all nine checks, verified the tag against the package version, built
  and uploaded both distributions, and completed Trusted Publishing to PyPI.
- PyPI lists `shuetl-0.5.0-py3-none-any.whl` with SHA-256
  `cfa560e22d9ab6b4d956408a7062e9cc04752798e5c8b17c394877a292ad84b6` and
  `shuetl-0.5.0.tar.gz` with SHA-256
  `f4d9dacdc650879d14c7bba302ababd5597d4db5c7e2e999323bdf7caaa10924`.

## Implementation qualification

The implementation baseline was verified locally on macOS 26.5.2 arm64 with Python 3.11.15, 3.12.13 and 3.13.11 and uv 0.11.3. The configured CI workflow is `.github/workflows/checks.yml`, with quality, live PostgreSQL 18.6, and release-gate jobs for Python 3.11–3.13. Hosted run [36654931532](https://github.com/eddiethedean/shuetl/actions/runs/36654931532) passed all nine jobs for qualification baseline commit `6e69b578d45983e2426c900253c7768a0ab1da5b`. The AC-017 configured-provider proof was added afterward, passed locally, and is included in the final-commit pre-tag and release runs above.

| Verification | Local result | Scope / limitation |
| --- | --- | --- |
| Quality gate | PASS — 183 passed, 5 skipped on Python 3.11.15, 3.12.13 and 3.13.11 | Ruff format/lint, Pyright, boundary and full pytest. The five skips per runtime are the PostgreSQL cases, executed separately below. Each run reported the upstream Starlette/AnyIO deprecation warning. |
| PostgreSQL integration | PASS — 5 passed, 0 skipped on Python 3.11.15, 3.12.13 and 3.13.11 | PostgreSQL 18.6; every JUnit result was checked for tests and zero skips. Each run reported the upstream Starlette/AnyIO deprecation warning. |
| Release gate | PASS — Python 3.12.13 | `scripts/check_release.py`: lock/sync, Ruff, Pyright, boundary, full pytest, deterministic build, artifact contents, OpenAPI, clean core/SQLite/PostgreSQL wheel environments and examples, and evidence consistency. |
| Hosted CI baseline | PASS — run 36654931532 | Initial quality, live PostgreSQL 18.6, and Phase 0.5 release-gate jobs passed on Python 3.11, 3.12 and 3.13 for commit `6e69b57`. |
| AC-017 review remediation | PASS — 14 local targeted cases; final hosted run passed | Direct and mounted denial checks cover configured foreign registry and schedule records. Added after initial baseline run 36654931532; included in pre-tag run 36659423353 and release run 36659686930 for commit `d846c3d`. |

The local PostgreSQL service is a disposable `postgres:18.6-bookworm` container on loopback port 55432. It is not a production deployment. The CI workflow rejects a missing `SHUETL_DATABASE_URL` and rejects skipped tests in its dedicated PostgreSQL JUnit result.
