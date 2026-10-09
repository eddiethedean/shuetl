# Phase 0.6 hosted CI record

| Run | Source commit | Result | Coverage |
| --- | --- | --- | --- |
| [37989243217](https://github.com/eddiethedean/shuetl/actions/runs/37989243217) | `c064aa9ead7b78d9f6451895d6799e088ab8682f` | PASS | Quality, nine no-skip PostgreSQL integration cases, installed CLI roles with exact cleanup order, and installed Gate 0 transfer plus two-process coordination on Python 3.11–3.13 |
| [37988671712](https://github.com/eddiethedean/shuetl/actions/runs/37988671712) | `5dc71c078d1527c3cd0aa58ec460a86e6ca47259` | PASS | Quality, installed CLI cleanup-order qualification and installed Gate 0 coordination on Python 3.11–3.13 |
| [37988337495](https://github.com/eddiethedean/shuetl/actions/runs/37988337495) | `87a9549dcc148bf5317b4b747d90a6bdcdbee6c2` | PASS | Expanded two-process Gate 0 coordination on Python 3.11–3.13 |
| [37986479448](https://github.com/eddiethedean/shuetl/actions/runs/37986479448) | `b03e4468a622a4ac9af4080a0e8ae9534f21a742` | PASS | Quality, installed CLI roles, installed Gate 0 and portable-plan observations on Python 3.11–3.13 |
| [37984396221](https://github.com/eddiethedean/shuetl/actions/runs/37984396221) | `40402b6c4f2788605ecfebfe5e25144ddd04a57c` | PASS | Scheduler TCP-level PostgreSQL outage/recovery plus installed role and transfer matrices on Python 3.11–3.13 |
| [37982842772](https://github.com/eddiethedean/shuetl/actions/runs/37982842772) | `0595029938c8917b904470a19c4ccf3d277e7e28` | PASS | Installed Gate 0 including keyed PostgreSQL upsert on Python 3.11–3.13 |

Run 37989243217 built and installed the ShuETL wheel and separate CLI and Gate 0
reference wheels outside the source checkout. The PostgreSQL integration job
passed all nine cases, with zero skips, against PostgreSQL 18.6 on Python
3.11–3.13. The outage test severed runtime database connections and verified
readiness loss, continued liveness and recovery for scheduler, run-worker and
action-worker processes. The installed CLI matrix verifies startup, probes,
SIGTERM exit and one owned-engine disposal followed by one host-binding close
for each of the four roles. The installed Gate 0 matrix verifies its three
transfer fixtures and same-store two-process coordination, including one
canonical result for each concurrent preparation, scheduler tick and worker
claim. Exact per-interpreter records and artifact hashes are checked into this
directory.

The installed reference workload continues to observe ETLantic's order-
dependent output for canonical sort followed by keyed deduplication. This
capability remains unqualified and is tracked in
[ETLantic #283](https://github.com/eddiethedean/etlantic/issues).

The Phase 0.6 release-gate job is tag-only and was skipped on this main-branch
run. The final-artifact evidence gate therefore remains unqualified. Green
main-branch CI is not release approval: AC-001–AC-033 and Gates A–C remain open.
