# ADR-0001: Package Boundary and Merge Trigger

- Status: Accepted
- Date: 2026-09-11

## Context

ETLantic and `etlantic-fastapi` already own pipeline semantics and ETLantic
HTTP behavior. ShuETL is currently documentation-only, so the first proof must
show value beyond a shorter import alias.

## Decision

Keep ShuETL separate while it owns material host composition, compatibility
validation, readiness diagnostics, deployment-profile guidance, and operator
documentation. ETLantic remains the semantic owner and `etlantic-fastapi`
remains the HTTP owner. Merge ShuETL into `etlantic-fastapi` if the required
composition hooks are not public or if the only remaining ShuETL value is an
alias for `include_router()`.

## Consequences

Phase 0.1 proves the upstream seam and does not create a facade. Every later
feature must be expressible as configuring or exposing ETLantic capability
through FastAPI.

## Validation

The memory spike, ownership matrix, OpenAPI comparison, and boundary checker
provide the evidence. See AC-006 through AC-018.

## Revisit trigger

Revisit at the E11 boundary review or if a required upstream composition hook
cannot be used through a documented public API.
