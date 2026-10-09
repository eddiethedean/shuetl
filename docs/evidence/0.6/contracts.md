# Development contract inventory

Upstream public imports and ownership are bound by the
[0.57.0 published audit](../../reviews/ETLANTIC_0_57_CANDIDATE_AUDIT.md),
[coverage acceptance](coverage-acceptance.md) and
[Gate 0 reference host](../../../tests/reference_phase06/phase06_reference/__main__.py).

Consumed interfaces: `SQLModelBackendConfig`, `create_managed_backend`,
`schema_requirements`, `inspect_schema`, `ManagedBackend.managed_service`,
`schedule_service`, `create_scheduler`, `create_execution_host`,
`create_action_execution_host`, `RuntimeRoleStatus`, `status`, `request_drain`,
`close`, `adapt_managed_backend`; canonical contexts, specifications, profiles,
planning registries, receipts and reports remain upstream types.

ShuETL's frozen host-binding exports are `HostBindings`, `GatewayBindings` and
`RuntimeBindings`; settings and lifecycle entry points are implemented in
`shuetl.settings`, `shuetl.cli` and `shuetl.runtime`. The reference package
remains a Gate 0 qualification fixture, not a release-proof artifact. This
inventory is not a final release proof registry.

Runtime bindings additionally accept an optional keyword-only `action_handlers`
mapping of public upstream connector action names to asynchronous handlers from
trusted backend packages. ShuETL snapshots the mapping and forwards it to
`SQLModelBackendConfig`; upstream validates and executes it. Gateway bindings
omit this worker configuration. Startup, recovery and cleanup corrections require
fresh installed-artifact qualification before any release gate closes.
