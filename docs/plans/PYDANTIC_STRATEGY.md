# Pydantic Strategy

## Principle

Pydantic models follow semantic ownership.

> **ETLantic models describe ETLantic; ShuETL models describe ShuETL
> composition.**

## Reuse ETLantic models

ShuETL uses the public Pydantic-compatible contracts supplied by ETLantic and
`etlantic-fastapi` for:

- definitions and revisions;
- validation and plans;
- submissions, runs, attempts, and recovery;
- schedules and firings;
- reports, events, diagnostics, and artifacts;
- control-plane identity and authorization context;
- executor/provider configuration where publicly exposed upstream.

ShuETL must not subclass or copy these models solely to rename fields, add a
`shuetl` schema name, or make them easier to serialize.

## ShuETL models

ShuETL may use Pydantic for:

- `ShuETLSettings`;
- deployment-profile and role selection;
- provider configuration references;
- FastAPI mount options;
- compatibility reports;
- capability and readiness diagnostics;
- optional adapter settings.

These models should be small, versioned when externally persisted, and free of
resolved credentials.

## Configuration

`pydantic-settings` may load environment, file, or explicitly supplied
configuration for ShuETL integration concerns.

Configuration must:

- distinguish missing values from deliberate local defaults;
- reject development-only settings in production profiles;
- avoid logging database credentials or secret values;
- validate mutually exclusive provider choices;
- leave ETLantic profile, plan, retry, schedule, and runtime validation to
  ETLantic.

## Validation boundary

ShuETL validates composition facts, including:

- compatible package versions;
- required provider presence;
- deployment-role consistency;
- identity/authorizer requirements;
- database/provider configuration shape;
- route-prefix and mounting conflicts.

It does not repeat validation already performed by ETLantic. Upstream validation
errors and diagnostics pass through without translation into new error codes.

## Serialization

ShuETL configuration and diagnostic serialization must be deterministic and
redacted.

ETLantic records use their upstream serializers and schema identifiers. Avoid
`model_dump()` followed by validation into a look-alike ShuETL class; that
creates an unnecessary compatibility boundary.

## OpenAPI

OpenAPI schemas for ETLantic routes are generated from
`etlantic-fastapi` models.

ShuETL should add no shadow schemas. A compatibility test compares the mounted
OpenAPI surface with the authoritative adapter, allowing only documented prefix,
tag, and host-level additions.

## Persistence

Pydantic models are not a reason for ShuETL to own persistence tables.
ETLantic's selected provider controls persistence mapping and migrations.

## Compatibility testing

Tests should prove:

- ETLantic objects retain their schema identifiers through ShuETL;
- no field is lost or reinterpreted;
- invalid upstream records fail in the upstream layer;
- ShuETL settings errors are clearly distinguished from ETLantic domain
  diagnostics;
- serialized diagnostics never expose secrets.
