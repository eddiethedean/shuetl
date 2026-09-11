# Changelog

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
