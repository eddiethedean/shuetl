# ADR-0011: Host Identity Composition and Production Guards

- Status: Accepted and implemented for Phase 0.5.
- Date: 2026-09-29.
- Governing contract: [Phase 0.5](../plans/PHASE_0_5_EXECUTION.md).

## Context

The released 0.4 bundles accept explicit host callbacks but enforce positional
principal signatures, do not validate principal/context outputs, and allow demo
header callbacks in the PostgreSQL pilot. Native FastAPI host authentication
uses dependency graphs, async/yield functions and security declarations that a
direct callable wrapper must not flatten. ETLantic remains the owner of domain
identity and authorization; ShuETL must not create principal or policy models.

## Decision

Add `HostIdentityAdapter` as a frozen composition object exposing stable guarded
principal/context callables and development-mode metadata. FastAPI executes the
original host principal dependency through native injection. A guarded
synchronous host context factory returns the upstream `ControlPlaneContext`
with the exact authenticated principal and matching typed scope refs.

The host validates credentials and authoritative membership. ShuETL guards
composition/output shape, rejects qualified upstream demo principal helpers in
host mode, and never verifies tokens or implements permission decisions.
Explicit `development-static` settings and an adapter factory are limited to
local profiles; static identity cannot construct or mount production APIs.

Retain genuine legacy PostgreSQL callback syntax through adapter normalization
and preserve the old local callback form as development compatibility. Prebuilt
production/unknown-profile APIs must be assembled with a matching host guard
pair before ShuETL accepts/mounts the exact caller API. The facade does not
rewrite callbacks, copy routers, or own providers. Security classification
does not resolve profile filenames merely to decide whether guards are required.

Keep the existing doctor schema/check order and distinguish configured mode
from inspected runtime adapter facts. No IdP/policy authentication probe belongs
in doctor and no identity-related persistence migration is introduced.

## Alternatives

- General identity/authorization models or middleware: rejected because the host
  and ETLantic already own those semantics.
- Directly invoking host dependencies: rejected because it bypasses FastAPI's
  execution, caching, security metadata and teardown rules.
- Async context bridges: deferred; the qualified upstream context seam is
  synchronous and host subdependencies can perform async membership lookup.
- Replacing caller API callbacks during mount: rejected because it violates
  facade ownership and can leave stale cached dependency graphs.
- Compensating for upstream list/HTTP-error defects in ShuETL: rejected;
  the requirements from [ETLantic #143](https://github.com/eddiethedean/etlantic/issues/143)
  and [#144](https://github.com/eddiethedean/etlantic/issues/144) are supplied
  by published 0.55.0 artifacts and remain upstream-owned.

## Consequences

Production demo callbacks and unguarded prebuilt production APIs require an
explicit upgrade. Trusted host code remains responsible for real credential
verification, issuer-aware membership, safe error/log behavior, session/CSRF
policy and connection lifetime. Same-process hostile code and multi-issuer
canonical-key isolation are not guaranteed.

Phase 0.5 AC-003 through AC-015 and AC-027 verify composition; AC-016 through
AC-026 and AC-033/034 verify preservation of upstream security behavior. The
published 0.55.0 correction and the public validation route are qualified in the
execution plan and release evidence.

## Validation

The upstream 0.55.0 artifacts and their direct/mounted behavior were inspected
and exercised on 2026-09-29. ShuETL's focused identity dependency and bundle
tests cover the adapter and profile guards. See the Phase 0.5 evidence ledger
for the executed commands and limits: [contract mapping](../evidence/0.5/contracts.md),
[ownership mapping](../evidence/0.5/ownership.md),
[qualification](../evidence/0.5/qualification.md), and the
[evidence index](../evidence/0.5/README.md).

## Revisit trigger

Revisit if upstream publishes async context injection, guarded host composition,
new principal/protocol semantics, or a broader qualified production profile.
