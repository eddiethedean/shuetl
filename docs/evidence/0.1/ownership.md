# Phase 0.1 Ownership Matrix

| Capability | Semantic owner | HTTP owner | ShuETL role | Prohibited ShuETL work | Verification | First release |
|---|---|---|---|---|---|---|
| Definitions, revisions, fingerprints | ETLantic | etlantic-fastapi | expose/configure | shadow model or registry | upstream contract | 0.2 |
| Plans and validation | ETLantic | etlantic-fastapi | expose/configure | reimplement planner | upstream contract | 0.2 |
| Submissions, runs, attempts | ETLantic | etlantic-fastapi | provider wiring | second state machine | idempotent spike | 0.1 proof |
| Retries, cancellation, recovery | ETLantic | etlantic-fastapi | document | retry/lease implementation | ownership review | 0.6 |
| Schedules and firings | ETLantic | etlantic-fastapi | later role configuration | scheduler loop | reserved inventory | 0.6 |
| Events and SSE | ETLantic | etlantic-fastapi | mount/document | second event protocol | OpenAPI inventory | 0.2 |
| Reports and artifacts | ETLantic | etlantic-fastapi | expose/document | wrapper schema or store | ownership review | 0.2 |
| Authorization context | ETLantic contracts + host identity | etlantic-fastapi | adapt later | tenant authority from request path | auth failure spike | 0.5 |
| Control-plane persistence | ETLantic provider | etlantic-fastapi | select later | ShuETL ORM/table | provider inventory | 0.4 |
| Migrations | provider package | n/a | invoke/document later | inferred DDL or revisions | reserved inventory | 0.4 |
| HTTP routes and errors | etlantic-fastapi | etlantic-fastapi | mount | copied route/schema/operation ID | OpenAPI parity | 0.2 |
| OpenAPI | upstream adapter | upstream adapter | compare evidence | shadow component schemas | normalized comparator | 0.1 proof |
| Settings and provider selection | ShuETL | n/a | deferred | domain configuration copy | scope gate | 0.3 |
| Host lifespan and handlers | host + ShuETL composition | upstream handler | document seam, implement later | silent replacement | ADR-0005 | 0.2 |
| Capability/readiness diagnostics | ShuETL composition | later adapter surface | deferred | implicit fallback capability | scope gate | 0.3 |
| Gateway/scheduler/worker roles | ETLantic runtime + supervisor | n/a | configure later | ShuETL executor/scheduler | reserved inventory | 0.6 |
| Optional AuthMate/Hedron adapters | peer package public APIs | peer/upstream | deferred | core dependency or authority fork | scope gate | 0.8 |

The authoritative semantic owner is unique in every row. “ShuETL supports” a
capability means selecting, mounting, validating, or documenting the upstream
capability; it does not transfer semantic ownership.
