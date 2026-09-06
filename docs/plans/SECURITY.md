# ShuETL Security

## Security posture

ShuETL is a control plane capable of triggering data movement and therefore must be secure by default.

## Authentication

MVP should support pluggable FastAPI authentication rather than embedding one identity provider. Auth may be explicitly disabled for local development, but production documentation should strongly discourage unauthenticated deployment.

## Authorization

Define resource-oriented permissions for pipelines, schedules, runs, artifacts, and admin operations. Internal permission checks should support fine-grained RBAC even if MVP begins with coarse viewer/operator/admin roles.

## Pipeline-definition security

If pipeline definitions can contain executable Python references, arbitrary remote creation becomes code-execution territory. MVP should prefer trusted code-registered pipelines or declarative ETLantic definitions known to be safe to deserialize. Do not accept arbitrary Python source uploads through the API.

## Secrets

Database records contain secret references, not plaintext resolved secrets. The persistence model must never require embedding resolved credentials in pipeline definitions.

## Result security

Artifact metadata should support classification, owner, expiration, and access-policy metadata where appropriate.

## Auditability

Audit pipeline version creation/activation, schedule changes, manual triggers, cancellations, retries, and artifact access where appropriate.

## Network exposure

Follow FastAPI deployment best practices: HTTPS termination, restrictive CORS, configurable docs endpoints, and explicitly trusted proxy headers.

## Denial-of-service controls

Bound request sizes, inline results, stored reports, schedule frequency, concurrent run creation, and pagination.

## Multi-tenancy

True tenant isolation is out of scope for MVP, but the data model should leave a clean future path to workspace/tenant scoping.

## External identity integration

ShuETL exposes a provider-neutral security integration surface. AuthMate is the reference implementation, not a required dependency.

### Authorization

Protected operations use generic ShuETL resource/action names such as `shuetl.pipeline`, `shuetl.schedule`, `shuetl.run`, `shuetl.artifact`, and actions like `shuetl.pipeline.run`, `shuetl.schedule.manage`, `shuetl.run.cancel`, and `shuetl.artifact.read`.

### Service-account execution

Scheduled/background runs execute as an explicit service account instead of inheriting credentials from the human who created a schedule. Disabled/revoked execution identities must block runs before unsafe I/O.

### Credential resolution

Pipeline definitions persist credential references only. At runtime the service account is authorized, the credential resolver obtains temporary secret material, and ETLantic receives it only for the duration needed.

ShuETL never silently falls back to application-global credentials if an explicit binding fails.

### UI versus server enforcement

Hedron or another UI may hide/disable controls based on authorization, but ShuETL APIs/services independently enforce the permission. Presentation state is never an authorization boundary.
