# ETLantic 0.57.0 coverage acceptance

Decision: U01–U05 accepted on 2026-10-09. This accepts public upstream
contracts for ShuETL development; it does not close PostgreSQL Gate 0, any of
the 33 phase acceptance criteria, hosted checks, transition rehearsal or release.

The [published-artifact audit](../../reviews/ETLANTIC_0_57_CANDIDATE_AUDIT.md)
binds PyPI SHA-256 values, source/tag provenance, upstream CI's 160 passing
cases and independent installations outside both checkouts. Acceptance adds
the following consumer assertions against those installed distributions:

| Contract | Independent coverage | Decision |
| --- | --- | --- |
| U01 backend ownership | Headless installation without FastAPI; shared gateway services; borrowed engine remains usable; owned engine disposes exactly once; failed construction cleans owned resources | PASS |
| U02 schedule commands | HTTP/Python create, amend, pause, resume, preview, trigger, get, list and firing results; stale revision conflicts; workspace denial; workload binding denial; interrupted firing link retries one canonical submission | PASS |
| U03 scheduler factory | Complete public factory; accepted-firing recovery; standby after lease contention; PostgreSQL scheduler restart in independent processes | PASS |
| U04 schema inspection | Public requirements; compatible/fresh/partial inspection; no DDL, write or commit during inspection/construction; published state/grant matrix; actual PostgreSQL runtime grants without schema CREATE | PASS |
| U05 lifecycle | All three roles tested during blocked provider work; repeated drain stops later admissions; in-flight count persists until work finishes; backend refuses active close; outage makes readiness unusable and recovery restores it; invalid trusted context rejected before I/O | PASS |

Consumer command (Python 3.13.9, exact candidate requirements from the audit):

```sh
/tmp/shuetl-057-audit.CjjECZ/gateway/bin/python -m pytest \
  tests/integration/test_upstream_contracts.py -q \
  --junitxml=docs/evidence/0.6/gate-u.xml
```

[Consumer XML](gate-u.xml): **12 passed**, no failures/errors/skips.
The installed environment uses SQLAlchemy 2.0.52, FastAPI 0.141.1 and Pydantic
2.13.5, matching ShuETL's retained non-ETLantic pins.

The tagged upstream `test_managed_schema_inspection_0_57.py`,
`test_managed_runtime_schema_privileges_0_57.py` and
`test_managed_scheduler_postgresql_0_57.py` were also run against the installed
0.57.0 wheels with `ETLANTIC_SQLMODEL_TEST_URL` pointing to a disposable
PostgreSQL **18.6** container. [Provider XML](gate-u-provider.xml): **10 passed**,
no failures/errors/skips. Three unknown-mark warnings come from running the
upstream tests under ShuETL's pytest configuration.

Docker image: `postgres:18.6`, digest
`sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336`.
The restricted-grant fixture and its SQL assertions belong to the provider's
tagged tests, not a ShuETL implementation of persistence semantics.

Lifecycle barriers prove the active public operations and drain/close boundary.
They do not prove signal handling, process grace periods or interrupted live
connector effects; those remain ShuETL process/release qualification work.
Issue closure remains the ETLantic maintainers' responsibility. No missing
upstream contract was found in this coverage review.
