# Phase 0.2 contract evidence

The Phase 0.2 contract is implemented by `shuetl.ShuETL` and delegates HTTP
semantics to `etlantic-fastapi==0.51.0`. No ShuETL route, domain model, provider
factory, scheduler, worker, or execution path is introduced.

| Capability | Owner | Proof |
|---|---|---|
| Complete control-plane router and schemas | `etlantic-fastapi` | `tests/integration/test_shuetl_facade.py` |
| Public composition hooks | ShuETL facade | `tests/unit/test_integration.py` |
| Problem details | `etlantic-fastapi` | upstream handler identity test |
| Durable work and idempotency | ETLantic providers | Phase 0.1 contract suite |
| Registry and history | ETLantic providers | Phase 0.1 inventory |
| Health and readiness | `etlantic-fastapi` | dedicated app test |
| SSE | `etlantic-fastapi` | upstream contract inventory |
| Authentication and authorization | host dependencies and ETLantic | dependency override contract |

The facade provides integration value through prefix validation, collision
preflight, handler composition, lifecycle ordering, and OpenAPI cache handling.
That integration burden is materially easier for hosts than repeating the
public composition hooks manually, while ShuETL never adds a copied route.
