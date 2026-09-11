# ShuETL Planning Pack

**ShuETL** *(pronounced “shuttle”)* is the opinionated FastAPI integration and
deployment package for ETLantic.

> **ShuETL composes ETLantic into a durable, schedulable FastAPI service without
> creating a second ETLantic control plane.**

## Product boundary

ShuETL is a composition layer, not the semantic owner of the features it
exposes.

| Concern | Authoritative owner | ShuETL responsibility |
|---|---|---|
| Pipeline definitions, revisions, plans, and fingerprints | ETLantic | Registration and application configuration |
| Durable submissions, runs, attempts, retries, and recovery | ETLantic | Provider wiring and FastAPI exposure |
| Schedules, firings, overlap, and misfire semantics | ETLantic | API selection, configuration, and role startup |
| Reports, events, artifacts, and diagnostics | ETLantic | HTTP/SSE projection and operator documentation |
| HTTP schemas and ETLantic route semantics | `etlantic-fastapi` | Curated mounting and host integration |
| Relational reference stores and migrations | `etlantic-sqlmodel` or another ETLantic provider | Database configuration and readiness checks |
| Authentication and credential implementation | Host application or optional identity provider | Adapt authenticated identity into ETLantic authorization context |
| Presentation | Host application or optional Hedron adapter | Optional operator-facing composition |

ShuETL must use ETLantic public models and protocols directly. It must not fork,
shadow, or translate them into ShuETL-owned equivalents without an explicit,
documented interoperability requirement.

## Core principles

> **Integrate; do not reinterpret.**

> **One ETLantic contract at every boundary.**

> **Useful defaults, replaceable providers.**

> **Development convenience must not become a false production guarantee.**

## Relationship to `etlantic-fastapi`

`etlantic-fastapi` remains the low-level authoritative FastAPI adapter for
ETLantic operations. ShuETL builds on it rather than defining parallel routes or
schemas.

ShuETL adds the application-level experience that a low-level adapter should not
own:

- one configuration and composition facade;
- explicit local and production deployment profiles;
- provider selection and compatibility validation;
- host FastAPI integration and lifecycle coordination;
- optional AuthMate and Hedron adapters;
- operator runbooks and supported deployment recipes;
- cross-package compatibility and failure-injection tests.

If this distinction cannot be maintained in implementation, ShuETL should be
merged into or replaced by `etlantic-fastapi` rather than duplicate it.

## Planning documents

- [VISION.md](VISION.md) — product purpose, users, scope, and success criteria
- [ARCHITECTURE.md](ARCHITECTURE.md) — integration boundaries and deployment roles
- [DATA_MODEL.md](DATA_MODEL.md) — authoritative model sourcing and persistence rules
- [API_DESIGN.md](API_DESIGN.md) — API composition rather than parallel route design
- [SCHEDULING_AND_RUNTIME.md](SCHEDULING_AND_RUNTIME.md) — ETLantic runtime delegation and process topology
- [RESULTS_AND_ARTIFACTS.md](RESULTS_AND_ARTIFACTS.md) — projection of ETLantic results and artifacts
- [SECURITY.md](SECURITY.md) — host identity adaptation and boundary enforcement
- [IDENTITY_INTEGRATION.md](IDENTITY_INTEGRATION.md) — provider-neutral identity integration
- [EXTENSIBILITY.md](EXTENSIBILITY.md) — composition-level extension points
- [DEPENDENCY_STRATEGY.md](DEPENDENCY_STRATEGY.md) — direct versus transitive dependencies
- [PYDANTIC_STRATEGY.md](PYDANTIC_STRATEGY.md) — reuse of ETLantic models
- [FASTAPI_STRATEGY.md](FASTAPI_STRATEGY.md) — router, DI, lifespan, and application factory behavior
- [MVP.md](MVP.md) — first shippable integration scope and acceptance criteria
- [ROADMAP.md](ROADMAP.md) — staged delivery after the integration boundary is proven
- [PHASE_0_1.md](PHASE_0_1.md) — executable boundary-proof plan and release gate
- [PHASE_0_1_EXECUTION.md](PHASE_0_1_EXECUTION.md) — concrete 0.1 tasks, files, commands, and gates
- [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) — decisions and blocking ADRs

## Infrastructure baseline

Local development may compose the API, scheduler, and worker in one process.
Production documentation must use separate supervised gateway and execution
roles unless the selected ETLantic provider explicitly certifies another
topology.

PostgreSQL is the production reference store. SQLite or memory providers are
local-development conveniences. Brokers, object stores, and external schedulers
remain optional when ETLantic's selected providers do not require them.
