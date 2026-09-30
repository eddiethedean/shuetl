# ETLantic 0.55.0 artifact qualification

On 2026-09-29 the published 0.55.0 core, FastAPI, and SQLModel wheels were downloaded from PyPI, inspected, and exercised in an isolated Python 3.12 environment. The project pins the same exact package versions.

| Distribution | Wheel | SHA-256 |
| --- | --- | --- |
| etlantic | `etlantic-0.55.0-py3-none-any.whl` | `5dc7a6bbf202f038dcddfd8100eb9e35239e77a6944b80804c8d97fe47d1e350` |
| etlantic-fastapi | `etlantic_fastapi-0.55.0-py3-none-any.whl` | `df6f6056d3559cd805e7ffb5034a84e5760f468cdab8820175f99de28a989821` |
| etlantic-sqlmodel | `etlantic_sqlmodel-0.55.0-py3-none-any.whl` | `e3197890af8c0a1c68e5c711f7036c144c32bb2c27e6d31df6d93b03a2750e64` |

## PB-001 — concrete item denial and bounded visibility

The installed `etlantic_fastapi.collections.visible_items` and `visible_limited_items` apply per-item authorization before returning visible results and before consuming an existing result limit. With a collection grant and an explicit denial for `definition:hidden`, the direct upstream API list omitted that definition. The same upstream API runs under ShuETL's direct factory and prefixed mount, where the security tests preserve item denial and a denied first 100 outbox candidates do not consume a two-visible-item limit. A dedicated registry proof also denies a caller before the workspace provider is queried when collection authorization fails, then filters a concrete denied workspace while returning only its permitted workspace in both graphs. ShuETL adds no post-pagination filter.

## PB-002 — safe validation route

`etlantic_fastapi.errors.RedactedValidationRoute` is exported and selected by `build_control_plane_router`. A malformed control-plane request with a nested password sentinel returned the fixed 422 detail `[{"type":"request_validation","loc":[],"msg":"Invalid request"}]` without echoing the input in direct and ShuETL-mounted apps. An unrelated host FastAPI route retained its own ordinary validation error. The executable installed-package check is `tests/integration/test_identity_dependencies.py::test_upstream_validation_errors_are_redacted_without_changing_host_routes`.

The upstream repository issues [#143](https://github.com/eddiethedean/etlantic/issues/143) and [#144](https://github.com/eddiethedean/etlantic/issues/144) remained open at qualification time; the published artifacts, exports, and behavior were checked directly. The SQLModel schema head remains `005_cp1_reference`; no identity migration was added.
