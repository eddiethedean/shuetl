# ADR-0005: Host Lifespan and Problem Handlers

- Status: Accepted
- Date: 2026-09-11

## Context

`include_router()` intentionally does not install exception handlers or lifespan
hooks and writes `app.state.etlantic_api`. A host application may already own
handlers, lifecycle resources, or state with those names.

## Decision

The 0.1 spike explicitly installs the upstream `ControlPlaneError` handler and
uses no integration lifespan. The 0.2 facade must compose host lifecycle and
handlers, detect state/handler conflicts, and never replace unrelated host
behavior silently. The observed upstream state key is recorded as a seam, not
changed by ShuETL 0.1.

## Consequences

## Alternatives

- Replace host handlers or lifespan silently; rejected because composition must
  preserve host behavior and surface conflicts.
- Add lifespan behavior to the 0.1 spike; rejected because it would turn proof
  tooling into production runtime code.

The spike proves the upstream behavior while avoiding an accidental lifecycle
API. Collision resolution is a required 0.2 implementation concern.

## Validation

See the [contract inventory](../evidence/0.1/contracts.md) and [ownership matrix](../evidence/0.1/ownership.md).

Embedded error responses and the host route are asserted in the spike; the
upstream no-handler behavior is recorded in the contract inventory. See AC-009,
AC-013, and AC-014.

## Revisit trigger

Revisit when the 0.2 mount/factory implementation is designed.
