# ADR-0004: 0.2 Facade Input Policy

- Status: Accepted
- Date: 2026-09-11

## Context

ETLantic already provides a fully constructed `ETLanticAPI` graph. Constructing
providers from environment values would add configuration and trust decisions
before the boundary is proven.

## Decision

The 0.2 `ShuETL` facade accepts a prebuilt, supported `ETLanticAPI`. Provider
graph construction and typed settings begin in 0.3 after compatibility and
readiness requirements are implemented.

## Consequences

Applications retain explicit provider ownership in 0.2. ShuETL cannot silently
select or discover caller-controlled providers.

## Validation

The 0.1 spike constructs the upstream graph directly and exports no provisional
facade. See AC-003, AC-004, and AC-022.

## Revisit trigger

Revisit when 0.3 settings work begins or when upstream exposes a supported
provider-bundle construction contract.
