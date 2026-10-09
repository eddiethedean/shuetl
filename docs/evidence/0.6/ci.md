# Phase 0.6 hosted CI record

| Run | Source commit | Result | Coverage |
| --- | --- | --- | --- |
| [37986479448](https://github.com/eddiethedean/shuetl/actions/runs/37986479448) | `b03e4468a622a4ac9af4080a0e8ae9534f21a742` | PASS | Quality, seven no-skip PostgreSQL integration cases, installed CLI roles and installed Gate 0 on Python 3.11–3.13; portable-plan observations record the ETLantic sort/dedup limitation |
| [37984396221](https://github.com/eddiethedean/shuetl/actions/runs/37984396221) | `40402b6c4f2788605ecfebfe5e25144ddd04a57c` | PASS | Quality, seven no-skip PostgreSQL integration cases including TCP-level outage/recovery, installed CLI roles and installed Gate 0 on Python 3.11–3.13 |
| [37982842772](https://github.com/eddiethedean/shuetl/actions/runs/37982842772) | `0595029938c8917b904470a19c4ccf3d277e7e28` | PASS | Quality, PostgreSQL integration, installed CLI roles, installed Gate 0 including keyed PostgreSQL upsert on Python 3.11–3.13 |
| [37981202502](https://github.com/eddiethedean/shuetl/actions/runs/37981202502) | `32a8ecab6e8fdf4d920d7f9b2b39d87cc83e83a0` | PASS | Quality, PostgreSQL integration, installed CLI roles, installed Gate 0 on Python 3.11–3.13 |
| [37980372245](https://github.com/eddiethedean/shuetl/actions/runs/37980372245) | `edfa8693f667d05791e44d39a6e91fb861b3413f` | PASS | Evidence/docs commit CI; same package-source behavior |
| [37980178783](https://github.com/eddiethedean/shuetl/actions/runs/37980178783) | `5baafe1b488352ccddad3c3a56a58e93929505e5` | PASS | Active worker drain regression, PostgreSQL integration, installed CLI and original Gate 0 matrix |

Run 37986479448 built and installed the ShuETL, reference workload and CLI host
wheels outside the source checkout. All three Gate 0 versions observed CSV
append, PostgreSQL snapshot append and primary-key upsert behavior recorded in
[`hosted-gate0/`](hosted-gate0/). All three installed CLI rows are in
[`hosted-cli/`](hosted-cli/). The PostgreSQL integration jobs ran against the
configured PostgreSQL 18.6 service, passed all seven cases on each interpreter,
and rejected skipped tests. The installed reference host also captures
order-dependent output from canonical sort followed by deduplication, keeping
that ETLantic local capability unqualified (see [ETLantic #283](https://github.com/eddiethedean/etlantic/issues/283)).

The release-gate job is tag-only and was skipped on these `main` branch runs.
The final-artifact evidence gate therefore remains unqualified. Main-branch CI
success is not a release approval: AC-001–AC-033 and Gates A–C remain open.
