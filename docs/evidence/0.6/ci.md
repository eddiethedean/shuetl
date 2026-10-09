# Phase 0.6 hosted CI record

| Run | Source commit | Result | Coverage |
| --- | --- | --- | --- |
| [37981721063](https://github.com/eddiethedean/shuetl/actions/runs/37981721063) | `0e6673b96bee3a5a603d2b55662f4f9ba5c54c6b` | PASS | Quality, PostgreSQL integration, installed CLI roles, installed Gate 0 including keyed PostgreSQL upsert on Python 3.11–3.13 |
| [37981202502](https://github.com/eddiethedean/shuetl/actions/runs/37981202502) | `32a8ecab6e8fdf4d920d7f9b2b39d87cc83e83a0` | PASS | Quality, PostgreSQL integration, installed CLI roles, installed Gate 0 on Python 3.11–3.13 |
| [37980372245](https://github.com/eddiethedean/shuetl/actions/runs/37980372245) | `edfa8693f667d05791e44d39a6e91fb861b3413f` | PASS | Evidence/docs commit CI; same package-source behavior |
| [37980178783](https://github.com/eddiethedean/shuetl/actions/runs/37980178783) | `5baafe1b488352ccddad3c3a56a58e93929505e5` | PASS | Active worker drain regression, PostgreSQL integration, installed CLI and original Gate 0 matrix |

Run 37981721063 built and installed the ShuETL, reference workload and CLI host
wheels outside the source checkout. All three Gate 0 versions observed CSV
append, PostgreSQL snapshot append and primary-key upsert behavior recorded in
[`hosted-gate0/`](hosted-gate0/). All three installed CLI rows are in
[`hosted-cli/`](hosted-cli/). The PostgreSQL integration jobs ran against the
configured PostgreSQL service and rejected skipped tests.

The release-gate job is tag-only and was skipped on these `main` branch runs.
The final-artifact evidence gate therefore remains unqualified. Main-branch CI
success is not a release approval: AC-001–AC-033 and Gates A–C remain open.
