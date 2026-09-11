# ADR-0006: Route Selection

- Status: Accepted
- Date: 2026-09-11

## Context

`etlantic-fastapi` publishes stable operation IDs and a capability-oriented
router. ShuETL must not create a competing HTTP vocabulary.

## Decision

The 0.2 facade exposes the complete upstream router under one validated prefix
and adds no aliases, copied routes, or independent route presets. Provider
capability differences remain upstream behavior and are reported in later
readiness work.

## Consequences

## Alternatives

- Expose selected route aliases; rejected because it would create a second
  public vocabulary and drift from upstream OpenAPI.
- Copy upstream handlers and schemas; rejected because ETLantic remains the
  semantic and HTTP owner.

OpenAPI parity can be compared directly after stripping the mount prefix.
Route filtering, if ever needed, must be added upstream or through a separately
accepted ADR.

## Validation

See the [contract inventory](../evidence/0.1/contracts.md) and [ownership matrix](../evidence/0.1/ownership.md).

The normalized direct-versus-embedded OpenAPI comparison and operation-ID
uniqueness checks prove this decision. See AC-015 and AC-016.

## Revisit trigger

Revisit only if upstream publishes a supported route-selection contract.
