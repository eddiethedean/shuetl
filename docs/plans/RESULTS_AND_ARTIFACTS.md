# Results and Artifacts

## Principle

ETLantic owns result, report, event, diagnostic, and artifact semantics. ShuETL
exposes those records through the configured ETLantic FastAPI adapter and
documents their operation in the selected deployment profile.

## Canonical records

ShuETL must preserve upstream:

- `PipelineRunReport` schema and status;
- submission, run, and attempt identities;
- diagnostic codes and redaction;
- event envelope, ordering, and cursor semantics;
- artifact identity, type, ownership, classification, and location;
- checksum, size, retention, and external-effect evidence where available.

ShuETL does not create a generic `ResultArtifact` table or serialize ETLantic
reports into a less expressive local model.

## HTTP projection

The mounted `etlantic-fastapi` routes remain authoritative for report, event,
and artifact metadata responses.

ShuETL may:

- choose which optional routes are enabled;
- configure providers and response bounds;
- mount them under a host prefix;
- supply proxy, caching, and streaming deployment guidance;
- provide presentation adapters that consume the canonical responses.

It may not silently omit fields that change ETLantic semantics.

## Bounded responses

ShuETL settings should configure only bounds supported by the upstream adapter
and providers.

- Generic API responses contain metadata and bounded previews, not arbitrary
  datasets.
- Oversized reports or previews produce the upstream truncation/reference
  behavior.
- List and event endpoints use upstream pagination/cursor contracts.
- Presentation summaries identify truncation and their source record.

## Artifact data

Large data remains in its ETLantic-selected storage or destination system.
ShuETL exposes metadata and authorized access mechanisms supplied by the
artifact provider.

ShuETL must not:

- turn arbitrary artifact URIs into an unrestricted proxy;
- dereference caller-selected local paths or network locations;
- generate persistent signed URLs;
- persist resolved credentials;
- delete externally owned data merely because control-plane metadata is
  removed.

## Provider selection

Local development may use ETLantic memory or local-file providers within their
documented security boundary.

Production uses an explicitly configured ETLantic artifact/report/event
provider. Object storage is optional when pipelines already publish to stable
external locations and the provider can store safe references.

## Security and authorization

Artifact and report access uses ETLantic authorization context and provider
rules. Authorization occurs before existence-sensitive lookup, signing,
preview, download, or deletion.

ShuETL presentation integrations must not treat UI visibility as authorization.

## Retention

Retention semantics remain provider-owned. ShuETL configures supported policies
and documents operational procedures without inventing an independent cleanup
state machine.

Readiness or diagnostics should identify missing retention configuration for a
production profile when the selected provider requires it.

## Observability integration

Publishers such as OpenLineage or telemetry exporters should use ETLantic event,
report, and metadata provider contracts. ShuETL may package configuration
adapters, but it does not define another event model.
