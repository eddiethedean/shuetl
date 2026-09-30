# Host identity integration

ShuETL accepts an ETLantic `Principal` from the host's authenticated FastAPI
dependency and an ETLantic `ControlPlaneContext` from the host's trusted
membership lookup. `HostIdentityAdapter` guards that composition while FastAPI
continues to execute the original dependency graph, security declarations,
dependency overrides, and yield cleanup.

ShuETL does not validate passwords, decode or verify tokens, resolve sessions,
choose tenant membership, or decide permissions. The host performs credential
verification and authoritative membership lookup; ETLantic's `Authorizer`
decides actions and resources.

## Compose a host dependency

The principal dependency may be synchronous or asynchronous, nested through
`Depends` or `Security`, keyword-only, or a yield dependency. Do not call it
directly. Provide the callable to the adapter so FastAPI retains its native
execution and cleanup behavior:

```python
from etlantic.control_plane import ControlPlaneContext, Principal
from fastapi import FastAPI, Request, Security

from shuetl import HostIdentityAdapter, ShuETL


async def verified_principal(token: str = Security(host_oauth_scheme)) -> Principal:
    # The host's maintained verifier validates the credential and returns an
    # upstream Principal only after authentication succeeds.
    return await host_authenticate_and_build_principal(token)


def member_context(principal: Principal, request: Request) -> ControlPlaneContext:
    # Resolve issuer-aware membership using trusted server-side policy.
    return load_authorized_membership(principal, request)


identity = HostIdentityAdapter.create(
    principal_dependency=verified_principal,
    context_factory=member_context,
)
api = build_etlantic_api(
    principal_dependency=identity.principal_dependency,
    context_factory=identity.context_factory,
    authorizer=host_etlantic_authorizer,
)
integration = ShuETL(api=api)
app = FastAPI()
integration.mount(app, prefix="/etl")
```

For the supported PostgreSQL profile, pass `identity_adapter=identity` and an
explicit ETLantic authorizer to `PostgreSQLProviderBundle.create(...)`. The
bundle validates the guard pair before constructing its engine. For an API
created elsewhere, pass its guarded callables into the ETLantic API before
`ShuETL(api=...)`; ShuETL rejects an unguarded production API before router
materialization or host-app mutation.

The host context factory is synchronous because that is the upstream
`etlantic-fastapi` contract. Perform asynchronous authentication and membership
lookups in the native FastAPI dependency graph before the context factory. The
factory must return the upstream `ControlPlaneContext`, preserve the exact
authenticated `Principal` object, and use matching typed tenant/workspace
references. ShuETL returns a constant 503 for malformed or unexpected context
failures and does not include host exception details.

For ordinary tests, override the original host callable using FastAPI's normal
`app.dependency_overrides` mapping. The adapter guard remains in the dependency
graph and verifies the replacement output. Remove overrides with the original
callable key after each test.

## OIDC host recipe

See [the OIDC example](../examples/phase_0_5_oidc_host.py). Its verifier is a
synthetic smoke fixture; it is not an OIDC implementation. A production host
must use a maintained provider library or trusted verification service and
validate at least the signature and allowed algorithm, exact issuer, intended
audience, expiration and not-before times, token use, and required revocation
policy before returning a `Principal`. The host must map a verified subject into
an issuer-aware ETLantic identity namespace; do not use an unverified claim or
subject alone as a membership key.

Do not place access tokens, refresh tokens, or ID tokens in pipeline payloads,
schedule configuration, idempotency keys, logs, event metadata, or ETLantic
execution credentials. The gateway's identity is the triggering identity for
authorization and durable acceptance. Pipeline execution uses the configured
ETLantic runtime and secret-provider boundary, not the gateway's host credential.

## Session host recipe

See [the session example](../examples/phase_0_5_session_host.py). Its in-memory
middleware is a test harness only. A production host owns server-side session
lookup and expiry/revocation, signed and rotated cookies, `Secure`, `HttpOnly`,
and appropriate `SameSite` attributes, TLS, trusted-proxy configuration, and
CSRF protection for every state-changing route. Session and CSRF middleware
must run before ShuETL routes. A yield dependency can keep request-scoped host
resources alive until a streaming response disconnects; SSE authorization is
performed when the stream connects and is not continuously reauthenticated.

## Local static identity

For local development only, select `identity="development-static"` with a
`profile="local"` settings object and create a matching
`HostIdentityAdapter.development_static(...)`. This adapter always supplies one
fixed Principal and scope; request headers cannot change them. It is not
authentication and must not be used for PostgreSQL or any production-profile
API. `shuetl doctor` reports the configured mode and, when a bundle is
available, the inspected adapter mode; it does not authenticate a user or probe
the host's identity service.

Run the [local static example](../examples/phase_0_5_development_static.py) for
the complete in-memory setup.

## Upstream security behavior

ShuETL preserves the authorization checks and response semantics provided by
ETLantic 0.55.0. Concrete item denials are applied before list results and
existing list limits. Control-plane validation errors use the upstream
`RedactedValidationRoute`; ShuETL does not copy routes, rewrite schemas, or add
another permission layer. The release evidence records direct and mounted
probes for these upstream contracts.

The scope guarantee depends on the host's membership mapping and the configured
ETLantic authorizer. This release does not claim isolation from malicious code
running in the same process, multi-issuer key redesign, continuous SSE token
refresh, or multi-tenant/HA operation.
