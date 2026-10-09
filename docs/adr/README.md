# Architecture Decision Records

These ADRs record implementation constraints. Accepted decisions govern
implementation; proposed decisions identify concrete designs awaiting their
stated acceptance evidence.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-package-boundary-and-merge-trigger.md) | Package boundary and merge trigger | Accepted; FastAPI-only criterion superseded by 0015 |
| [0002](0002-initial-compatibility-policy.md) | Initial compatibility policy | Accepted |
| [0003](0003-dependency-boundaries.md) | Dependency boundaries | Accepted |
| [0004](0004-facade-input-policy.md) | 0.2 facade input policy | Accepted |
| [0005](0005-host-lifespan-and-problem-handlers.md) | Host lifecycle and handlers | Accepted |
| [0006](0006-route-selection.md) | Route selection | Accepted |
| [0007](0007-settings-sources-and-precedence.md) | Settings sources and precedence | Accepted |
| [0008](0008-local-provider-bundles.md) | Local provider bundles | Accepted |
| [0009](0009-doctor-report-contract.md) | Doctor report contract | Accepted |
| [0010](0010-postgresql-pilot-and-migration-boundary.md) | PostgreSQL pilot and migration boundary | Accepted |
| [0011](0011-host-identity-composition-and-production-guards.md) | Host identity composition and production guards | Accepted and implemented for 0.5; published 0.55.0 prerequisites qualified |
| [0012](0012-one-way-host-integration.md) | One-way host integration and headless composition | Accepted |
| [0013](0013-specifications-and-backend-ownership.md) | Application specifications and complete backend ownership | Accepted; ownership clarified by 0015 |
| [0014](0014-role-separated-managed-runtime.md) | Revised role factories, bindings, probes, stop and fresh-store boundary | Proposed; Gate U/0 pass, ShuETL API freeze pending |
| [0015](0015-backend-and-deployment-ownership.md) | Canonical upstream backend and ShuETL deployment ownership | Accepted planning boundary; implementation unqualified |

Any change to an accepted decision requires updating its governing execution
contract and acceptance/verification mapping.
