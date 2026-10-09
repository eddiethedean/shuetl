# Development ownership evidence

ETLantic owns neutral backend/service/role assembly, identity validity,
authorization decisions, planning, preparation/admission, scheduling, claims,
leases, fencing, reports and effects. SQLModel owns persistence requirements,
inspection and migration semantics. FastAPI adapts those same service handles.

ShuETL owns package selection, deployment settings, host identity guards,
server/TLS qualification policy, future process supervision and probes.
The Gate 0 harness owns disposable infrastructure and process orchestration;
it calls public contracts without replacement runtime factories or callbacks.

The reference host supplies exact plugin trust and canonical binding metadata.
It owns its borrowed engine and disposes it after cooperative drain/backend close;
backend close itself preserves the borrowed engine. Both owned and borrowed
resource contracts are independently exercised in coverage acceptance.

See [ADR-0015](../../adr/0015-backend-and-deployment-ownership.md).
Supported ShuETL role bindings remain a future API freeze and implementation.
