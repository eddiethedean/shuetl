# Phase 0.6 source/runtime implementation checks

Recorded: 2026-10-09 for source commit `40402b6c4f2788605ecfebfe5e25144ddd04a57c`.
These checks cover the implementation source and an isolated Python 3.13 wheel.
They do not close the 33 release criteria or the release gates.

| Check | Command | Result | Scope |
| --- | --- | --- | --- |
| Formatting | `ruff format --check .` | PASS | Local workspace |
| Lint | `ruff check .` | PASS | Source, scripts and tests |
| Types | `uv run --group dev pyright` | PASS, 0 errors | Python 3.13.9 |
| Regression | `uv run pytest -q --junitxml=docs/evidence/0.6/regression.xml` | 255 passed, 8 skipped | Seven PostgreSQL tests require the dedicated service job; final-hash test is release-gated |
| PostgreSQL regression | `uv run pytest tests/integration/test_postgresql.py -q --junitxml=docs/evidence/0.6/postgresql-regression.xml` | 7 passed, 0 skipped | Disposable PostgreSQL 18.6; includes TCP-fault-proxy outage and readiness recovery |
| Boundary | `uv run python scripts/check_boundaries.py` | PASS | Local workspace |
| Build/artifacts | `uv build`; `uv run python scripts/check_artifact.py` | PASS | Wheel and source distribution built locally |
| OpenAPI | `uv run python scripts/capture_openapi.py --check` | PASS | Existing approved baseline |
| Clean wheel | `uv run python scripts/check_clean_wheel.py` | PASS | Isolated core, SQLite, PostgreSQL and server extras on Python 3.13.9; runtime import isolation checked |

The new unit checks cover role-setting rejection, public bindings, loopback probe
responses/freshness, headless import boundaries and cleanup order. PostgreSQL
process checks cover scheduler drain and provider connectivity recovery, but not
all worker roles, forced termination, or competing process recovery. The release
evidence checker remains red while AC-001–033 and Gates A–C are open.
