# Changelog

## Unreleased — Phase 0.6 development

- Target ShuETL 0.6.0 at the published ETLantic, `etlantic-fastapi`, and
  `etlantic-sqlmodel` 0.56.0 train; pin optional SQL and Foundry provider
  packages to 0.56.0.
- Add a `postgresql-preview` settings profile and `shuetl serve` entry point
  for separately supervised gateway, scheduler, run-worker, and provider-action
  worker processes.
- Construct ETLantic's managed backend after read-only PostgreSQL 18.6/schema
  preflight; use its scheduler, durable stores, execution host, and action
  execution host without adding ShuETL-owned execution semantics.
- Add loopback runtime probes, provider-gated dispatch, signal handling, and
  drain-before-cleanup supervision.
- Add the Phase 0.6 evidence ledger, installed-wheel metadata checks, and
  Python/PostgreSQL qualification workflow. Production-preview qualification
  remains open; see `docs/evidence/0.6/README.md`.

## 0.5.0 — Secure host integration (2026-09-30)

- Published to [PyPI](https://pypi.org/project/shuetl/0.5.0/) through Trusted
  Publishing from the [`v0.5.0` tag](https://github.com/eddiethedean/shuetl/tree/v0.5.0)
  at commit `d846c3dd15b517def5c736e831202a603ca0e080`. The tag-triggered
  [release workflow](https://github.com/eddiethedean/shuetl/actions/runs/36659686930)
  passed its checks, build, and publication steps.
- Pin the published ETLantic, `etlantic-fastapi`, and `etlantic-sqlmodel` 0.55.0
  train; retain the qualified FastAPI, Pydantic, PostgreSQL, SQLAlchemy, and
  Psycopg pins.
- Add `HostIdentityAdapter` for native FastAPI principal dependencies and
  guarded ETLantic context construction; require matching host guards for
  production-profile bundles and prebuilt APIs.
- Add explicit local-only `development-static` identity and safe doctor facts
  for configured and inspected identity mode.
- Qualify mutation authorization, scope/list visibility, SSE cursor access,
  trigger-identity persistence, credential redaction, and the gateway's
  no-execution boundary against ETLantic 0.55.0.
- Add synthetic OIDC and session host recipes, clean-wheel smoke checks, and
  current Phase 0.5 acceptance evidence.

## 0.4.0 — Durable PostgreSQL pilot (2026-09-13)

- Published to [PyPI](https://pypi.org/project/shuetl/0.4.0/) through Trusted
  Publishing from the `v0.4.0` tag at `69f140f6f7343cc6e2bdbb97c34dba3d4eb324e0`.
  All nine CI jobs and the
  [release workflow](https://github.com/eddiethedean/shuetl/actions/runs/34778081760)
  passed.
- Added the exact ETLantic 0.52.1 compatibility train and a `shuetl[postgresql]`
  extra with SQLModel, SQLAlchemy, and Psycopg 3.3.5 binary support.
- Added validated `postgresql-pilot` settings and the public
  `PostgreSQLProviderBundle` for registry-backed definitions, submissions,
  events, durable work, schedules, and firings.
- Added read-only PostgreSQL connectivity/schema-head checks to `shuetl doctor`
  and the explicit `shuetl database upgrade` provider-migration command.
- Qualified fresh/prior-head migrations, restart identity persistence,
  idempotency, schedule/firing claims, event replay, and concurrent PostgreSQL
  appends against PostgreSQL 18.6.
- Protected byte-valued database URLs from text/JSON validation-error disclosure
  and rejected invalid UTF-8 without exposing credentials.
- Qualified the upstream workspace-scoped firing fix in ETLantic 0.52.1,
  including canonical durable-submission identities across restart.

## 0.3.0 — Local provider bundle and diagnostics (2026-09-11)

- Added immutable `ShuETLSettings` with strict `SHUETL_*` configuration and
  local SQLite URL validation.
- Added `LocalProviderBundle` for exact ETLantic memory or pre-provisioned
  SQLite stores with explicit host identity and idempotent cleanup.
- Added deterministic, redacted `shuetl doctor` text/JSON diagnostics and the
  `shuetl --version` command.
- Added an optional `shuetl[sqlite]` dependency set pinned to the ETLantic
  0.51 provider train.

## 0.2.0 — FastAPI composition facade (2026-09-11)

- Added the typed `ShuETL` facade for embedding or creating ETLantic FastAPI
  applications from a caller-owned `ETLanticAPI`.
- Added strict prefix validation, atomic collision checks, upstream handler
  composition, OpenAPI cache invalidation, and host-lifespan composition.
- Qualified runtime dependencies against ETLantic 0.51.0, FastAPI 0.141.1,
  and Pydantic 2.13.5.
- Added local/test quickstart documentation and facade contract tests.
- Published to PyPI through Trusted Publishing from the `v0.2.0` tag.

## 0.1.0 — Boundary proof

- Added the typed ShuETL package foundation.
- Added the disposable ETLantic 0.51.0 memory-provider FastAPI integration
  spike and normalized OpenAPI evidence.
- Added package-boundary, artifact, clean-wheel, and release-gate checks.
- Published to PyPI through Trusted Publishing from the `v0.1.0` tag.

This release is an architecture and integration spike. It does not provide a
stable ShuETL facade or a production deployment profile.
