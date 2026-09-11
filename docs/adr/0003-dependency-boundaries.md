# ADR-0003: Dependency Boundaries

- Status: Accepted
- Date: 2026-09-11

## Context

The 0.1 importable package contains no runtime behavior. ETLantic providers
already own persistence, scheduling, retry, worker, and migration mechanics.

## Decision

The 0.1 package has no unconditional runtime dependencies. Its `test` extra
contains the exact ETLantic/FastAPI evidence dependencies. ShuETL core must not
import or directly depend on SQLModel, Alembic, APScheduler, Tenacity, Celery,
Dramatiq, or artifact backends.

## Consequences

## Alternatives

- Add ETLantic as a runtime dependency; rejected because the 0.1 package is
  intentionally inert.
- Vendor provider implementations; rejected because ETLantic owns persistence
  and execution semantics.

The wheel is inert but proves that a future facade can be added without hidden
dependency coupling. The 0.2 facade adds direct dependencies only when its
importable source consumes them.

## Validation

See the [contract inventory](../evidence/0.1/contracts.md) and [ownership matrix](../evidence/0.1/ownership.md).

Wheel metadata inspection, clean-wheel installation, and AST boundary fixtures
prove the rule. See AC-001 through AC-004 and AC-017 through AC-019.

## Revisit trigger

Revisit when importable ShuETL code first uses an upstream package or an
optional integration is proposed.
