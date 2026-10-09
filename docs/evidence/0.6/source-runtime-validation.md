# Phase 0.6 source/runtime implementation checks

Recorded: 2026-10-09. These checks cover the current implementation source and
an isolated Python 3.13 wheel. They do not close any of the 33 release criteria
or qualify gateway/worker lifecycle against PostgreSQL.

| Check | Command | Result | Scope |
| --- | --- | --- | --- |
| Formatting | `ruff format --check .` | PASS | Local workspace |
| Lint | `ruff check .` | PASS | Source, scripts and tests |
| Types | `uv run --group dev pyright` | PASS, 0 errors | Python 3.13.9 |
| Regression | `uv run --group dev pytest -q` | 207 passed, 6 skipped | Five existing PostgreSQL tests lacked `SHUETL_DATABASE_URL`; final-hash test intentionally skips while Gates A–C are open |
| Boundary | `uv run python scripts/check_boundaries.py` | PASS | Local workspace |
| Build/artifacts | `uv build`; `uv run python scripts/check_artifact.py` | PASS | Wheel and source distribution built locally |
| OpenAPI | `uv run python scripts/capture_openapi.py --check` | PASS | Existing approved baseline |
| Clean wheel | `uv run python scripts/check_clean_wheel.py` | PASS | Isolated core, SQLite, PostgreSQL and server extras on Python 3.13.9; runtime import isolation checked |

The new unit checks cover role-setting rejection, public bindings, loopback probe
responses/freshness, headless import boundaries and cleanup order. This is source
and wheel smoke evidence, not role-process acceptance. The release evidence
checker remains red while AC-001–033 and Gates A–C are open and final candidate
hashes do not match the currently recorded values.
