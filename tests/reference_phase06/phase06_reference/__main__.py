"""One independently launched role, driven through a bounded JSON pipe."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import traceback
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from importlib import metadata
from pathlib import Path
from typing import Any

from etlantic import Data, Extract, Input, Load, Output, Pipeline, Transformation
from etlantic.authoring import definition_from_pipeline
from etlantic.authoring.serialize import pipeline_to_dict
from etlantic.control_plane import (
    ControlPlaneContext,
    ControlPlaneError,
    EnvironmentRef,
    FakeScheduleClock,
    MemoryAuthorizer,
    Principal,
    ScheduleSpec,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic.control_plane.input_resources import InputResourceReference
from etlantic.profile import Profile
from etlantic.quality import (
    QualityRuleset,
    make_quality_gate,
    rule_membership,
    rule_not_null,
    rule_range,
    rule_uniqueness,
    split_by_quality,
)
from etlantic.registry import BindingDescriptor, PlanningContext
from etlantic.transform import functions as F
from etlantic.transform.compiler import (
    TransformCompileContext,
    TransformExecutionContext,
)
from etlantic.transform.local_compiler import LocalTransformCompiler
from etlantic_sqlmodel import SQLModelBackendConfig, create_managed_backend
from sqlalchemy import create_engine, event


class Row(Data):
    id: str
    payload: str
    quantity: str


class NormalizedRow(Data):
    id: int
    payload: str
    quantity: int


class PortableRawRow(Data):
    id: int
    payload: str | None
    quantity: int
    discarded: str


class PortableNormalizedRow(Data):
    id: int
    payload: str | None
    quantity: int


class NormalizeRows(Transformation):
    rows: Input[Row]
    result: Output[NormalizedRow]


def normalize_rows(rows):
    normalized = []
    for row in rows:
        identifier = int(row["id"])
        quantity = int(row["quantity"])
        if identifier > 0 and quantity > 0:
            normalized.append(
                {
                    "id": identifier,
                    "payload": str(row["payload"]).lower(),
                    "quantity": quantity * 2,
                }
            )
    return normalized


NormalizeRows.implementation("local")(normalize_rows)


class PortableNormalizeRows(Transformation):
    rows: Input[PortableRawRow]
    result: Output[PortableNormalizedRow]


@PortableNormalizeRows.portable
def portable_normalize_rows(rows):
    selected = rows.drop("discarded").select("id", "payload", "quantity")
    renamed = selected.rename({"id": "source_id"})
    normalized = renamed.select(
        F.col("source_id").alias("id"),
        F.lower(F.col("payload")).alias("payload"),
        F.col("quantity").alias("quantity"),
    )
    return (
        normalized.filter((F.col("id") > 0) & (F.col("quantity") > 0))
        .sort(F.col("id").asc(), F.col("quantity").asc())
        .dropDuplicates("id")
    )


PORTABLE_QUALITY = QualityRuleset(
    name="Phase06PortableQuality",
    rules=(
        rule_not_null("id"),
        rule_not_null("payload"),
        rule_range("quantity", min_value=1, max_value=100),
        rule_membership("payload", ["ok"]),
        rule_uniqueness("id"),
    ),
)


def portable_conformance():
    """Execute a canonical portable plan with ETLantic's installed local compiler."""
    plan = PortableNormalizeRows.to_transform_plan()
    actions = [
        str(action["kind"]["action"])
        for action in plan.get("actions", [])
        if isinstance(action, dict) and isinstance(action.get("kind"), dict)
    ]
    compiler = LocalTransformCompiler()
    compiled = compiler.compile(
        plan,
        context=TransformCompileContext(
            pipeline_id="phase06-portable-conformance",
            plan_id="phase06-portable-plan",
            step_name="normalize",
            profile_name="gate0",
            engine="local",
        ),
    )
    source_rows = [
        {"id": 1, "payload": "OK", "quantity": 4, "discarded": "drop-me"},
        {"id": 1, "payload": "OK", "quantity": 3, "discarded": "drop-me"},
        {"id": 2, "payload": "NO", "quantity": 60, "discarded": "drop-me"},
        {"id": 3, "payload": None, "quantity": 4, "discarded": "drop-me"},
        {"id": 4, "payload": "ok", "quantity": 120, "discarded": "drop-me"},
        {"id": 0, "payload": "ok", "quantity": 9, "discarded": "drop-me"},
    ]

    async def execute(rows, run_id):
        return await compiler.execute(
            compiled,
            inputs={"rows": rows},
            parameters={},
            context=TransformExecutionContext(
                run_id=run_id,
                pipeline_id="phase06-portable-conformance",
                plan_id="phase06-portable-plan",
                step_name="normalize",
                engine="local",
            ),
        )

    bundle = asyncio.run(execute(source_rows, "phase06-portable-forward-run"))
    normalized = [
        PortableNormalizedRow.model_validate(row).model_dump()
        for row in bundle.valid["result"]
    ]
    reversed_rows = [source_rows[1], source_rows[0], *source_rows[2:]]
    reverse_bundle = asyncio.run(
        execute(reversed_rows, "phase06-portable-reversed-run")
    )
    reverse_normalized = [
        PortableNormalizedRow.model_validate(row).model_dump()
        for row in reverse_bundle.valid["result"]
    ]
    accepted, rejected, _diagnostics = split_by_quality(normalized, PORTABLE_QUALITY)
    duplicate_quality_rows = [
        {"id": 8, "payload": "ok", "quantity": 8},
        {"id": 8, "payload": "ok", "quantity": 9},
    ]
    _unique_rows, duplicate_rejections, _unique_diagnostics = split_by_quality(
        duplicate_quality_rows, PORTABLE_QUALITY
    )
    expected_actions = [
        "dtcs:drop_fields",
        "dtcs:project",
        "dtcs:rename_fields",
        "dtcs:project",
        "dtcs:filter",
        "dtcs:sort",
        "dtcs:deduplicate",
    ]
    capability_results = {
        "portable_plan_select": "dtcs:project" in actions,
        "portable_plan_drop": "dtcs:drop_fields" in actions,
        "portable_plan_rename": "dtcs:rename_fields" in actions,
        "portable_plan_filter": "dtcs:filter" in actions,
        "portable_plan_scalar_lowercase": "dtcs:lower"
        in json.dumps(plan, sort_keys=True),
        "portable_plan_contains_sort_before_deduplicate": (
            "dtcs:sort" in actions
            and actions.index("dtcs:sort") < actions.index("dtcs:deduplicate")
        ),
        "portable_output_schema": all(
            set(row) == {"id", "payload", "quantity"} for row in normalized
        ),
        "portable_quality_required_value": [row["id"] for row in rejected] == [2, 3, 4]
        and rejected[1]["payload"] is None,
        "portable_quality_range": any(row["id"] == 4 for row in rejected),
        "portable_quality_set_membership": any(row["id"] == 2 for row in rejected),
        "portable_quality_uniqueness": len(duplicate_rejections) == 1,
        "portable_quality_keeps_rejections_separate": [row["id"] for row in accepted]
        == [1]
        and [row["id"] for row in rejected] == [2, 3, 4],
    }
    order_sensitive = {
        "deterministic": (
            next(row["quantity"] for row in normalized if row["id"] == 1)
            == next(row["quantity"] for row in reverse_normalized if row["id"] == 1)
        ),
        "forward_key_quantity": next(
            row["quantity"] for row in normalized if row["id"] == 1
        ),
        "reversed_key_quantity": next(
            row["quantity"] for row in reverse_normalized if row["id"] == 1
        ),
    }
    if (
        actions != expected_actions
        or not all(capability_results.values())
        or order_sensitive
        != {
            "deterministic": True,
            "forward_key_quantity": 3,
            "reversed_key_quantity": 3,
        }
    ):
        raise AssertionError(
            {
                "actions": actions,
                "expected_actions": expected_actions,
                "capability_results": capability_results,
                "sort_deduplicate_order_observation": order_sensitive,
            }
        )
    return {
        "plan_identity": plan.get("planIdentity"),
        "actions": actions,
        "compiler": compiler.info.to_dict(),
        "normalized_rows": normalized,
        "reversed_rows": reverse_normalized,
        "accepted_rows": accepted,
        "rejected_rows": rejected,
        "duplicate_quality_rejections": duplicate_rejections,
        "sort_deduplicate_order_observation": order_sensitive,
        "unqualified_capabilities": [],
        "capability_results": capability_results,
    }


Quality = make_quality_gate(
    NormalizedRow,
    QualityRuleset(
        rules=(
            rule_not_null("id"),
            rule_not_null("payload"),
            rule_range("quantity", min_value=1, max_value=100),
            rule_membership("payload", ["ok"]),
            rule_uniqueness("id"),
        )
    ),
    name="ReferenceQualityGate",
)


class Transfer(Pipeline):
    source: Extract[Row] = Extract(asset="source")
    normalized = NormalizeRows.step(rows=source)
    quality = Quality.step(rows=normalized.result)
    sink: Load[NormalizedRow] = Load(input=quality.result, asset="sink")
    rejected: Load[NormalizedRow] = Load(input=quality.rejected, asset="rejected")


class PostgreSQLTransfer(Pipeline):
    source: Extract[Row] = Extract(asset="pg-source")
    normalized = NormalizeRows.step(rows=source)
    quality = Quality.step(rows=normalized.result)
    sink: Load[NormalizedRow] = Load(input=quality.result, asset="pg-sink")
    rejected: Load[NormalizedRow] = Load(input=quality.rejected, asset="pg-rejected")


class PostgreSQLUpsertTransfer(Pipeline):
    source: Extract[Row] = Extract(asset="pg-source")
    normalized = NormalizeRows.step(rows=source)
    quality = Quality.step(rows=normalized.result)
    sink: Load[NormalizedRow] = Load(input=quality.result, asset="upsert-sink")
    rejected: Load[NormalizedRow] = Load(
        input=quality.rejected, asset="upsert-rejected"
    )


class UploadedTransfer(Pipeline):
    source: Extract[Row] = Extract(asset="uploaded-source")
    normalized = NormalizeRows.step(rows=source)
    quality = Quality.step(rows=normalized.result)
    sink: Load[NormalizedRow] = Load(input=quality.result, asset="sink")
    rejected: Load[NormalizedRow] = Load(input=quality.rejected, asset="rejected")


def main():
    requested_role = sys.argv[1]
    role, _, _instance = requested_role.partition("@")
    root = Path(os.environ["PHASE06_ROOT"])
    ctx = ControlPlaneContext(
        principal=Principal("gate0-workload", issuer="reference-host", kind="service"),
        tenant=TenantRef("gate0"),
        workspace=WorkspaceRef("gate0", "qualification"),
        environment=EnvironmentRef("test"),
        security_domain=SecurityDomain("gate0"),
        resource_owner_id="gate0-workload",
    )
    auth = MemoryAuthorizer()
    for action in (
        "definition.write",
        "definition.plan",
        "run.submit",
        "run.read",
        "run.report",
        "run.retry",
        "run.rerun",
        "run.actions",
        "run.lineage",
        "run.artifacts",
        "run.artifact.content",
        "input.read",
        "schedule.write",
        "schedule.read",
        "action.execute",
    ):
        auth.grant(ctx, action)
    profile = Profile(
        name="gate0",
        security_mode="production",
        portable_transform_policy="native",
        plugin_allowlist={
            "etlantic": "0.57.2",
            "etlantic-local": "0.50.0",
            "etlantic-sql": "0.57.2",
            "postgresql": "0.57.2",
            "local-files": "0.57.2",
        },
        safe_io={"approved_roots": [str(root / "landing")]},
    )

    def planning_factory(_ctx, effective_profile):
        planning = PlanningContext.create(profile=effective_profile)
        uploaded_path = root / "uploaded-input.json"
        if uploaded_path.exists():
            reference = InputResourceReference.from_dict(
                json.loads(uploaded_path.read_text())
            )
            planning.registry.register_binding(
                BindingDescriptor(
                    binding="uploaded-source",
                    provider="local-files",
                    kind="source",
                    config={"format": "csv", "input_resource": reference.to_dict()},
                )
            )
        planning.registry.register_binding(
            BindingDescriptor(
                binding="source",
                provider="local-files",
                kind="source",
                config={
                    "format": "csv",
                    "mode": "snapshot",
                    "root": ".",
                    "root_ref": "gate0-input",
                    "glob": "*.csv",
                },
            )
        )
        planning.registry.register_binding(
            BindingDescriptor(
                binding="sink",
                provider="postgresql",
                kind="sink",
                location="target",
                config={
                    "schema": "sink",
                    "mode": "append",
                    "effect_table": "sink.effects",
                },
            )
        )
        planning.registry.register_binding(
            BindingDescriptor(
                binding="rejected",
                provider="postgresql",
                kind="sink",
                location="rejected",
                config={
                    "schema": "sink",
                    "mode": "append",
                    "effect_table": "sink.effects",
                },
            )
        )
        planning.registry.register_binding(
            BindingDescriptor(
                binding="pg-source",
                provider="postgresql",
                kind="source",
                location="source_rows",
                config={"schema": "input", "mode": "snapshot"},
            )
        )
        for binding, location in (
            ("pg-sink", "postgres_target"),
            ("pg-rejected", "postgres_rejected"),
            ("upsert-rejected", "upsert_rejected"),
        ):
            planning.registry.register_binding(
                BindingDescriptor(
                    binding=binding,
                    provider="postgresql",
                    kind="sink",
                    location=location,
                    config={
                        "schema": "sink",
                        "mode": "append",
                        "effect_table": "sink.effects",
                    },
                )
            )
        for binding in ("upsert-sink", "upsert-sink-alias"):
            planning.registry.register_binding(
                BindingDescriptor(
                    binding=binding,
                    provider="postgresql",
                    kind="sink",
                    location="upsert_target",
                    config={
                        "schema": "sink",
                        "mode": "upsert",
                        "key_columns": ["id"],
                        "effect_table": "sink.effects",
                    },
                )
            )
        return planning

    clock = FakeScheduleClock(datetime(2026, 10, 9, tzinfo=UTC))
    engine = create_engine(os.environ["PHASE06_RUNTIME_URL"], pool_pre_ping=True)
    statements = []
    commits = []
    event.listen(
        engine,
        "before_cursor_execute",
        lambda _c, _cu, sql, _p, _ctx, _many: statements.append(
            sql.strip().split()[0].upper()
        ),
    )
    event.listen(engine, "commit", lambda _c: commits.append(True))
    backend = create_managed_backend(
        SQLModelBackendConfig(
            store_id="gate0",
            profile=profile,
            artifact_root=str(root / "artifacts"),
            schedule_clock=clock,
            action_job_lease_seconds=int(
                os.environ.get("PHASE06_ACTION_LEASE_SECONDS", "330")
            ),
            run_artifact_retention_seconds=(
                int(os.environ["PHASE06_ARTIFACT_RETENTION"])
                if "PHASE06_ARTIFACT_RETENTION" in os.environ
                else None
            ),
            run_artifact_cleanup_batch_size=1,
        ),
        authorizer=auth,
        engine=engine,
        planning_context_factory=planning_factory,
    )
    assert not commits
    assert not set(statements) & {
        "CREATE",
        "ALTER",
        "DROP",
        "INSERT",
        "UPDATE",
        "DELETE",
    }
    startup_sql = list(statements)
    worker = None
    client = None
    owner_id = None
    if role == "gateway":
        from etlantic_fastapi import adapt_managed_backend
        from fastapi.testclient import TestClient

        from shuetl import HostIdentityAdapter, ShuETL

        identity = HostIdentityAdapter.create(
            principal_dependency=lambda: ctx.principal,
            context_factory=lambda _p, _r: ctx,
        )
        adapter = adapt_managed_backend(
            backend,
            context_factory=identity.context_factory,
            principal_dependency=identity.principal_dependency,
        )
        client = TestClient(ShuETL(api=adapter.api).create_app(prefix="/etl"))
        client.__enter__()
    elif role == "scheduler":
        owner_id = f"scheduler-{os.getpid()}"
        worker = backend.create_scheduler(
            owner_id=owner_id,
            clock=clock,
            ttl_seconds=int(os.environ.get("PHASE06_LEASE_SECONDS", "30")),
        )
    elif role == "run-worker":
        owner_id = f"run-{os.getpid()}"
        worker = backend.create_execution_host(
            owner_id=owner_id,
            ttl_seconds=int(os.environ.get("PHASE06_LEASE_SECONDS", "30")),
        )
    elif role == "action-worker":
        owner_id = f"action-{os.getpid()}"
        service_type = type(backend.managed_service)
        execute_preparation = service_type.execute_run_preparation

        def observe_preparation_failure(service, *args, **kwargs):
            try:
                return execute_preparation(service, *args, **kwargs)
            except Exception as exc:
                message = str(exc).replace(
                    os.environ["PHASE06_RUNTIME_URL"], "<redacted-database-url>"
                )
                report = getattr(exc, "report", None)
                (root / "preparation-error.json").write_text(
                    json.dumps(
                        {
                            "type": type(exc).__name__,
                            "message": message,
                            "report": (
                                {
                                    "phases": list(report.phases),
                                    "diagnostics": [
                                        item.to_dict() for item in report.diagnostics
                                    ],
                                }
                                if report is not None and hasattr(report, "diagnostics")
                                else None
                            ),
                        }
                    )
                )
                raise

        service_type.execute_run_preparation = observe_preparation_failure
        worker = backend.create_action_execution_host(worker_id=owner_id)
    else:
        raise ValueError(role)
    import etlantic_sqlmodel

    print(
        json.dumps(
            {
                "started": requested_role,
                "pid": os.getpid(),
                "owner_id": owner_id,
                "startup_sql": startup_sql,
                "origin": etlantic_sqlmodel.__file__,
                "reference_origin": __file__,
                "versions": {
                    n: metadata.version(n)
                    for n in ("etlantic", "etlantic-sqlmodel", "etlantic-sql")
                },
                "http_imported": "fastapi" in sys.modules,
                "execution_imported": "etlantic.runtime.execution_host" in sys.modules,
            }
        ),
        flush=True,
    )
    try:
        for line in sys.stdin:
            command = json.loads(line)
            try:
                op = command["op"]
                if op == "fault-arm":
                    # Test-wheel barriers around public calls. No production hooks,
                    # storage repair, or replacement semantics are involved.
                    target = {
                        "durable": backend.durable_work,
                        "schedule": backend.schedule_store,
                        "submissions": backend.submissions,
                        "reports": type(backend.report_store_factory(ctx)),
                    }[command["target"]]
                    method = command["method"]
                    if method not in {
                        "accept",
                        "accept_action_job",
                        "claim_action_job",
                        "acquire_lease",
                        "start_attempt",
                        "finish_attempt",
                        "record_result_publication",
                        "mark_published",
                        "claim_firing",
                        "link_firing_submission",
                        "put",
                    }:
                        raise ValueError("unsupported test barrier")
                    original = getattr(target, method)
                    when = command["when"]
                    if when not in {"before", "after"}:
                        raise ValueError("unsupported barrier position")

                    def paused_call(
                        *args,
                        _target=target,
                        _method=method,
                        _original=original,
                        _when=when,
                        **kwargs,
                    ):
                        def pause():
                            print(
                                json.dumps({"barrier": _method, "when": _when}),
                                flush=True,
                            )
                            assert json.loads(sys.stdin.readline()) == {"op": "release"}

                        setattr(_target, _method, _original)
                        if _when == "before":
                            pause()
                        value = _original(*args, **kwargs)
                        if _when == "after":
                            pause()
                        return value

                    setattr(target, method, paused_call)
                    result = {"armed": method, "when": when}
                elif op == "preparation":
                    result = backend.managed_service.start_run_preparation(
                        ctx,
                        command.get("definition_id", "postgres-upsert-transfer"),
                        idempotency_key=command["key"],
                        deadline_seconds=command.get("deadline_seconds", 300),
                        request=command.get("request"),
                    )
                elif op == "preparation-get":
                    result = backend.managed_service.get_run_preparation(
                        ctx, command["operation_id"]
                    )
                elif op == "action-job":
                    record = backend.durable_work.get_action_job(
                        ctx, command["action_id"]
                    )
                    result = asdict(record)
                elif op == "preparation-error":
                    error_path = root / "preparation-error.json"
                    result = (
                        json.loads(error_path.read_text())
                        if error_path.exists()
                        else None
                    )
                elif op == "lookup-submission":
                    record = backend.durable_work.get_submission_by_idempotency(
                        ctx, idempotency_key=command["key"], operation="run.submit"
                    )
                    result = (
                        None
                        if record is None
                        else {
                            "submission_id": record.submission_id,
                            "status": record.status,
                            "run_id": record.run_id,
                        }
                    )
                elif op == "lookup-cp1":
                    receipt = backend.submissions.lookup_idempotency(
                        ctx, command["key"], operation="run.submit"
                    )
                    result = None if receipt is None else receipt.to_dict()
                elif op == "submission-detail":
                    record = backend.durable_work.get_submission(
                        ctx, command["submission_id"]
                    )
                    result = {
                        "submission": asdict(record),
                        "attempts": [
                            asdict(a)
                            for a in backend.durable_work.list_attempts(
                                ctx, record.submission_id
                            )
                        ],
                    }
                    try:
                        result["effect"] = asdict(
                            backend.durable_work.get_effect(
                                ctx, record.submission_id + ":execution"
                            )
                        )
                    except ControlPlaneError:
                        result["effect"] = None
                elif op == "cancel-submission":
                    result = asdict(
                        backend.durable_work.cancel_submission(
                            ctx, command["submission_id"]
                        )
                    )
                elif op == "run-command":
                    methods = {
                        "retry": "retry_run",
                        "rerun": "rerun_run",
                        "actions": "get_run_actions",
                        "lineage": "get_run_lineage",
                        "artifacts": "list_run_artifacts",
                        "artifact-content": "get_run_artifact_content",
                    }
                    arguments = dict(command.get("arguments", {}))
                    run_context = ctx
                    if command.get("foreign_owner"):
                        run_context = replace(
                            ctx,
                            principal=Principal(
                                "foreign", issuer="reference", kind="service"
                            ),
                        )
                    if command.get("foreign_scope"):
                        run_context = replace(
                            ctx, workspace=WorkspaceRef(ctx.tenant.tenant_id, "foreign")
                        )
                    try:
                        value = getattr(
                            backend.managed_service, methods[command["method"]]
                        )(run_context, command["run_id"], **arguments)
                        if command["method"] == "artifact-content":
                            content, media_type = value
                            value = {
                                "sha256": hashlib.sha256(content).hexdigest(),
                                "byte_length": len(content),
                                "media_type": media_type,
                            }
                        result = {
                            "status": 200,
                            "value": value.to_dict()
                            if hasattr(value, "to_dict")
                            else value,
                        }
                    except ControlPlaneError as exc:
                        result = {
                            "status": exc.status,
                            "code": exc.code,
                            "detail": str(exc),
                            "diagnostics": exc.extensions,
                        }
                elif op == "execution-options":
                    from etlantic.control_plane.execution_envelope import (
                        ExecutionEnvelope,
                    )
                    from etlantic.runtime.request import RunRequest

                    submission = backend.durable_work.get_submission(
                        ctx, command["submission_id"]
                    )
                    envelope = ExecutionEnvelope.from_json(submission.input_snapshot)
                    requested = RunRequest.from_dict(envelope.run_request).to_dict()
                    effective = RunRequest.from_dict(
                        envelope.effective_request
                    ).to_dict()
                    assert RunRequest.from_dict(requested).to_dict() == requested
                    assert RunRequest.from_dict(effective).to_dict() == effective
                    result = {
                        "requested": requested,
                        "effective": effective,
                        "roundtrip": True,
                    }
                elif op == "artifact-cleanup":
                    assert worker is not None and role == "run-worker"
                    result = worker.runner.cleanup_expired_run_artifacts(
                        ctx,
                        now=datetime.fromisoformat(command["now"]),
                        limit=command["limit"],
                    ).to_dict()
                elif op == "input-resource":
                    resource_context = ctx
                    if command.get("foreign_owner"):
                        resource_context = replace(
                            ctx,
                            principal=Principal(
                                "foreign", issuer="reference", kind="service"
                            ),
                            resource_owner_id="foreign",
                        )
                    if command.get("foreign_scope"):
                        resource_context = replace(
                            ctx, workspace=WorkspaceRef(ctx.tenant.tenant_id, "foreign")
                        )
                    arguments = dict(command.get("arguments", {}))
                    for name in ("expires_at", "now", "retain_until"):
                        if name in arguments:
                            arguments[name] = datetime.fromisoformat(arguments[name])
                    if "reference" in arguments:
                        arguments["reference"] = InputResourceReference.from_dict(
                            arguments["reference"]
                        )
                    if "content" in arguments:
                        arguments["content"] = arguments["content"].encode()
                    try:
                        value = getattr(backend.input_resources, command["method"])(
                            resource_context, **arguments
                        )
                        result = {
                            "status": 200,
                            "value": (
                                {
                                    "sha256": hashlib.sha256(value).hexdigest(),
                                    "byte_length": len(value),
                                }
                                if isinstance(value, bytes)
                                else asdict(value)
                                if hasattr(value, "__dataclass_fields__")
                                else value
                            ),
                        }
                    except ControlPlaneError as exc:
                        result = {
                            "status": exc.status,
                            "code": exc.code,
                            "detail": str(exc),
                        }
                elif op == "schedule-create":
                    clock.set(
                        datetime.fromisoformat(command["instant"])
                        - timedelta(seconds=60)
                    )
                    result = backend.schedule_service.create(
                        ctx,
                        definition_id="postgres-upsert-transfer",
                        profile_name="gate0",
                        spec=ScheduleSpec(kind="interval", interval_seconds=60),
                    ).to_dict()
                elif op == "definition":
                    result = backend.managed_service.register_definition(
                        ctx,
                        "transfer",
                        pipeline_to_dict(definition_from_pipeline(Transfer)),
                    )
                    result = {"registered": True}
                elif op == "definition-document":
                    result = pipeline_to_dict(definition_from_pipeline(Transfer))
                elif op == "host-code-digest":
                    result = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
                elif op == "register-definition-document":
                    backend.managed_service.register_definition(
                        ctx, command["definition_id"], command["document"]
                    )
                    result = {"registered": True}
                elif op == "definition-pg":
                    result = backend.managed_service.register_definition(
                        ctx,
                        "postgres-transfer",
                        pipeline_to_dict(definition_from_pipeline(PostgreSQLTransfer)),
                    )
                    result = {"registered": True}
                elif op == "plan":
                    result = backend.managed_service.plan_definition(ctx, "transfer")
                elif op == "plan-pg":
                    result = backend.managed_service.plan_definition(
                        ctx, "postgres-transfer"
                    )
                elif op == "definition-upsert":
                    result = backend.managed_service.register_definition(
                        ctx,
                        "postgres-upsert-transfer",
                        pipeline_to_dict(
                            definition_from_pipeline(PostgreSQLUpsertTransfer)
                        ),
                    )
                    result = {"registered": True}
                elif op == "definition-input":
                    reference = InputResourceReference.from_dict(command["reference"])
                    (root / "uploaded-input.json").write_text(
                        json.dumps(reference.to_dict())
                    )
                    backend.managed_service.register_definition(
                        ctx,
                        "uploaded-transfer",
                        pipeline_to_dict(definition_from_pipeline(UploadedTransfer)),
                    )
                    result = {"registered": True}
                elif op == "portable-conformance":
                    if role != "gateway":
                        raise ValueError(
                            "portable conformance runs in the reference host"
                        )
                    result = portable_conformance()
                elif op == "plan-upsert":
                    result = backend.managed_service.plan_definition(
                        ctx, "postgres-upsert-transfer"
                    )
                elif op == "http":
                    assert client is not None
                    response = client.request(
                        command["method"],
                        "/etl" + command["path"],
                        json=command.get("body"),
                        headers=command.get("headers", {}),
                    )
                    result = {"status": response.status_code, "body": response.json()}
                elif op == "schedule-get":
                    result = backend.schedule_service.get(
                        ctx, command["schedule_id"]
                    ).to_dict()
                elif op == "firings":
                    result = [
                        f.to_dict()
                        for f in backend.schedule_service.list_firings(
                            ctx, command["schedule_id"]
                        )
                    ]
                elif op == "submission":
                    result = {
                        "run_id": backend.durable_work.get_submission(
                            ctx, command["submission_id"]
                        ).run_id
                    }
                elif op == "schedule-command":
                    scope = (
                        replace(ctx, workspace=WorkspaceRef("gate0", "denied"))
                        if command.get("denied")
                        else ctx
                    )
                    method = command["method"]
                    identifier = command.get("schedule_id")
                    service = backend.schedule_service
                    try:
                        value: Any
                        if method == "amend":
                            value = service.amend(
                                scope,
                                identifier,
                                expected_revision_id=command["revision_id"],
                                spec=ScheduleSpec(kind="interval", interval_seconds=60),
                            )
                        elif method in ("pause", "resume", "get", "preview"):
                            value = getattr(service, method)(scope, identifier)
                        elif method == "list":
                            value = [
                                s.to_dict()
                                for s in service.list_definition(scope, "transfer")
                            ]
                        elif method == "trigger":
                            value, _ = service.trigger(
                                scope,
                                identifier,
                                nominal_fire_time=datetime.fromisoformat(
                                    command["instant"]
                                ),
                            )
                        else:
                            raise ValueError(method)
                        result = value.to_dict() if hasattr(value, "to_dict") else value
                    except ControlPlaneError as exc:
                        result = {"denial_status": exc.status}
                elif op in {"report", "report-or-error"}:
                    try:
                        result = backend.managed_service.get_run_report(
                            ctx, command["run_id"]
                        )
                    except ControlPlaneError as exc:
                        if op == "report":
                            raise
                        result = {
                            "status": exc.status,
                            "code": exc.code,
                            "detail": str(exc),
                        }
                elif op == "tick":
                    assert worker is not None
                    if "instant" in command:
                        clock.set(datetime.fromisoformat(command["instant"]))
                    result = {
                        "count": worker.tick(ctx),
                        "status": asdict(worker.status()),
                    }
                elif op == "close":
                    if worker is not None:
                        worker.request_drain()
                        assert worker.tick(ctx) == 0
                    result = {"closed": True}
                else:
                    raise ValueError(op)
                print(json.dumps({"ok": result}, default=str), flush=True)
                if op == "close":
                    break
            except Exception as exc:
                print(
                    json.dumps(
                        {
                            "error": str(exc),
                            "type": type(exc).__name__,
                            "traceback": traceback.format_exc(),
                            "diagnostics": getattr(exc, "extensions", {}),
                        }
                    ),
                    flush=True,
                )
    finally:
        if client is not None:
            client.__exit__(None, None, None)
        if worker is not None:
            worker.request_drain()
        backend.close()
        with engine.connect() as connection:
            from sqlalchemy import text

            assert connection.execute(text("SELECT 1")).scalar_one() == 1
        engine.dispose()


if __name__ == "__main__":
    main()
