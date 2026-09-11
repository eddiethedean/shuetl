# ADR-0007: Settings Sources and Precedence

- Status: Accepted
- Date: 2026-09-11

## Context

Phase 0.3 introduces environment-driven configuration. A missing value must not
silently select a development-only topology, and common `BaseSettings` sources
such as dotenv files or a secrets directory would add undeclared precedence and
filesystem trust.

## Decision

`ShuETLSettings` uses `pydantic-settings` with the exact `SHUETL_` environment
prefix. Precedence is constructor arguments, then environment variables, then
defaults. Dotenv, file-secret, CLI, and custom settings sources are disabled.

Deployment profile, process role, provider, and identity mode have no defaults.
Phase 0.3 accepts only the explicit local/gateway combinations defined by its
execution contract. Unknown fields and unsupported combinations fail validation.

Database configuration is secret-bearing. Its value is excluded from normal
serialization and may be resolved only inside provider construction or a bounded
readiness check. Diagnostics, errors, logs, and representations report only that
a database reference is configured and its validated driver family.

## Consequences

Local development takes a few explicit values, but missing configuration cannot
activate memory storage or demo identity by accident. Tests can reproduce every
source and precedence case without reading user files.

## Alternatives

- Default to a local memory profile; rejected because omission would select
  development-only behavior.
- Load `.env` automatically; rejected because working-directory files would
  become an implicit configuration and secret source.
- Accept arbitrary provider import paths; rejected because configuration must
  not become plugin discovery or code execution.

## Validation

The released baseline is recorded in the 0.2
[contract inventory](../evidence/0.2/contracts.md) and
[ownership matrix](../evidence/0.2/ownership.md).

See AC-003 through AC-010 in
[`PHASE_0_3_EXECUTION.md`](../plans/PHASE_0_3_EXECUTION.md).

## Revisit trigger

Revisit when a named production profile needs an approved secret-reference or
configuration-file source. Adding a source requires an ADR and an explicit
precedence update.
