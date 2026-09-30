# Phase 0.5 feature ownership

| Boundary | Owner | ShuETL 0.5 responsibility |
| --- | --- | --- |
| Credential/session verification and membership | Host application | Provide an authenticated upstream `Principal` through a native FastAPI dependency and a trusted context factory. |
| Principal, scope context, policies, scoped stores, list decisions, run disclosure, events, and execution semantics | ETLantic | Consume public upstream contracts and qualify behavior from the installed 0.55.0 release. |
| HTTP routes, schemas, OpenAPI operation IDs, SSE, validation route and problem errors | `etlantic-fastapi` | Mount its API and preserve the published adapter behavior. |
| PostgreSQL/SQLite schemas, stores and migrations | `etlantic-sqlmodel` | Select exact provider packages, report compatibility and require explicit provisioning. |
| Settings, provider graph, identity guard composition, app lifecycle, doctor, compatibility and operator documentation | ShuETL | Validate composition and fail closed without adding a competing control plane. |
| OIDC, sessions, bearer/cookie handling, CSRF, secret providers and execution credentials | Host / ETLantic runtime | Document integration requirements; ShuETL does not implement them. |
