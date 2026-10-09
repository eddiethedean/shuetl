# ADR-0015: Backend Correctness and Deployment Ownership

- Status: Accepted as the Phase 0.6 planning boundary; implementation unqualified.
- Date: 2026-10-08.
- Governing contract: [Phase 0.6](../plans/PHASE_0_6_EXECUTION.md).
- Supersedes ADR-0001's FastAPI-only feature test and clarifies ADR-0013's
  “supported backend experience.” Revises ADR-0014's proposed composition;
  preserves the 0.5 facade/bundle API and historical release evidence.

## Context

The [responsibility review](../reviews/PHASE_0_6_RESPONSIBILITY_REVIEW.md) found
HTTP-coupled headless construction, schedule commands inside HTTP handlers,
callback-identity-dependent recovery wiring and provider-schema knowledge in
ShuETL. Installed 0.56.2 fixes the earlier DDL version-reader defect, but does
not close the broader backend/service/provider boundary requirements.

2026-10-09 follow-up: the [0.57.0 candidate audit](../reviews/ETLANTIC_0_57_CANDIDATE_AUDIT.md)
records those published contract surfaces and initial checks. This ownership
decision is unchanged; formal acceptance and ShuETL deployment evidence remain
required.

## Decision

ETLantic owns canonical ETL meaning and correctness: models, authorized services,
normalization/planning, idempotency, scheduling, execution and recovery. Providers
own connectors, resources, persistence, schema compatibility and migrations.
The standard backend and complete role factories belong upstream and must be
usable independently of ShuETL and its HTTP adapter. The SQLModel-specific graph
belongs in the provider or another explicit optional upstream composition package.

`etlantic-fastapi` translates public services to HTTP. It must not be the sole
owner of schedule command orchestration or a prerequisite for headless roles.

ShuETL owns deployment configuration, selection of qualified upstream factories,
FastAPI/host integration, lifecycle ownership, process supervision, operational
probes, exact compatibility pins, support matrices and runbooks. It does not
assemble collaborators whose omission changes preparation or recovery, implement
schema recognition over internal tables, or maintain a canonical feature catalog.
Its factory selectors and composition handles may reuse upstream public types.

Hosts own authentication, account membership, resource/credential enrollment and
business workflows. Canonical context validation and per-operation authorization
remain enforced upstream for HTTP, headless and runtime callers. Keep ShuETL's
native FastAPI identity adapter and deployment scope guards. External supervisors
own process scaling, restarts and forced termination.

The feature test is: “Configure, expose or operate an upstream ETLantic capability
for a host or deployment.” A change to ETL identity, authorization, durability,
effect meaning or recovery belongs upstream. HTTP mounting is optional. Advanced
caller-owned provider injection remains supported; the standard path requires
no host ETL implementation and invokes upstream-complete factories.

Gate U tracks [#278](https://github.com/eddiethedean/etlantic/issues/278),
[#279](https://github.com/eddiethedean/etlantic/issues/279),
[#280](https://github.com/eddiethedean/etlantic/issues/280),
[#281](https://github.com/eddiethedean/etlantic/issues/281), and
[#282](https://github.com/eddiethedean/etlantic/issues/282). Select exact published
artifacts only after contract evidence is available. The old 0.56.0-as-is selection
and constructor-DDL exception no longer govern 0.6. This decision creates no new
runtime capability and does not change current package pins.

## Alternatives

- Keep assembling the published 0.56.0 graph in ShuETL: rejected because the
  standard path would depend on HTTP-only services and fragile recovery wiring.
- Move all deployment behavior into ETLantic: rejected because host composition,
  supervisor policy and deployment qualification are a distinct ShuETL purpose.
- Move the managed ETL service into ShuETL: rejected because all consumers need
  one canonical service and ETLantic must remain independently usable.
- Merge ShuETL into the HTTP adapter now: rejected while material host/deployment
  value remains; the merge trigger still applies if that value disappears.

## Consequences

Upstream changes and a new artifact qualification gate precede standard-path
implementation. Missing semantics block delivery instead of authorizing local
fallback. Keep engine conformance upstream and repeat relevant outcomes through
ShuETL's installed deployments. Support qualification can restrict a deployment
claim but cannot silently alter canonical options or command semantics.

## Validation

[Gate U, Gate 0 and AC-001–033](../plans/PHASE_0_6_EXECUTION.md) plus the
[verification plan](../plans/PHASE_0_6_VERIFICATION.md) require dependency-layer,
HTTP/headless parity, schema inspection, lifecycle and failure proofs. The
[0.5 contract evidence](../evidence/0.5/contracts.md) and
[ownership baseline](../evidence/0.5/ownership.md) remain regression inputs,
not proof of these unimplemented changes. The future 0.6 evidence ledger must
record actual artifacts and results without placeholder PASS entries.

## Revisit trigger

Revisit if upstream public contracts cannot provide the complete backend without
HTTP/host coupling, a proposed ShuETL feature changes ETL semantics, or the package
loses material integration/deployment value.
