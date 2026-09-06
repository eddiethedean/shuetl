# Results and Artifacts

## Problem

Pipeline output can range from a small JSON result or validation summary to Parquet files, millions of rows, database tables, or object-store locations. The control-plane database should not assume all outputs are small or relational.

## Result model

ShuETL should distinguish Run report, Result metadata, Result artifact, and Result data.

### Run report

Always persisted when bounded and safe. Examples include run status, ETLantic execution reports, validation summaries, drift summaries, warnings, and timings.

### Result artifact

Represents where output lives, for example:

```text
s3://bucket/path/output.parquet
file:///data/output.csv
postgres://warehouse/table
table:analytics.customers
```

## Inline results

Inline result payloads are useful for row counts, scalar outputs, small JSON dictionaries, and tiny previews. They must have strict configurable size limits.

## External artifacts

Large results should be represented by URI, media type, size, checksum, and metadata. ShuETL should not proxy large artifact contents through its database by default.

## Artifact adapters

Potential interface:

```python
class ArtifactStore:
    def put(...)
    def get_reference(...)
    def delete(...)
```

Potential implementations include local filesystem, S3-compatible storage, Azure Blob, and database/table references.

## Retention

Retention policy should apply separately to run metadata, execution reports, inline results, and externally managed artifacts. Deleting ShuETL metadata must not automatically delete externally owned datasets unless the artifact store explicitly owns them.

## Security

Artifact records must never persist resolved credentials, signed URLs with long-lived secrets, or unredacted connection strings. Persist stable logical references and generate temporary access paths when needed.

## Filesystem dependency strategy

Use `fsspec` plus `universal-pathlib` for general filesystem/object-store mechanics when the artifacts extra is installed.

ShuETL still owns artifact identity, metadata, retention, security/redaction, and run relationships.

## SQL-only artifact baseline

ShuETL must not require object storage.

Baseline behavior:

- small bounded results may be stored inline in SQL;
- large outputs remain where the pipeline writes them;
- ShuETL stores stable metadata/references to external output locations.

S3/Azure/GCS/fsspec-based artifact stores remain optional capabilities rather than required infrastructure.
