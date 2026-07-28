# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""S10R2 contract canonicalization, parity, and effective-lock validation."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from Tensile.ductile.evidence import (
    canonical_json_bytes,
    canonical_sha256,
    plain_value,
    sha256_file,
    strict_load_json,
    strict_load_yaml,
    validate_schema_document,
)

from .calibration import (
    Allocation,
    CalibrationError,
    parse_utc_timestamp,
    validate_allocation,
)


class ContractError(ValueError):
    """Contract, parity, source binding, or lock-seal failure."""


PACKAGE_ROOT = Path(__file__).resolve().parent
PROTOCOL_ROOT = PACKAGE_ROOT.parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[5]
DEFAULT_CONTRACT_PATH = (
    PROTOCOL_ROOT / "s10r2-stage1-support-aware-entry-contract.yaml"
)
DEFAULT_SCHEMA_PATH = PROTOCOL_ROOT / "schemas/s10r2-entry.schema.json"

EXPECTED_IMPLEMENTATION_WHITELIST = [
    "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r2_entry.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r2/__init__.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r2/contract.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r2/calibration.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r2/ledger.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r2/support.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r2/mapping.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r2/native_adapter.py",
    (
        "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r2/"
        "native_formocast_runtime_adapter.cpp"
    ),
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r2/conformance.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r2/correctness.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r2/state_machine.py",
    (
        "study_docs/research/ductile-origami-warmstart/protocol/v1/"
        "s10r2-stage1-support-aware-entry-contract.yaml"
    ),
    (
        "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/"
        "s10r2-entry.schema.json"
    ),
    (
        "projects/hipblaslt/tensilelite/Tensile/Tests/unit/"
        "test_ductile_s10r2_entry.py"
    ),
]

EXPECTED_BOUND_ARTIFACTS = {
    "allocation_record",
    "calibration_metrics_record",
    "candidate_atom_registry",
    "client_binary",
    "client_build_record",
    "native_build_manifest",
    "native_helper_binary",
    "pinned_materialization_manifest",
    "resource_calibration_fixture",
    "size_registry",
}


def _repository_relative(path: Path | str) -> str:
    candidate = Path(path).resolve()
    try:
        return candidate.relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError as error:
        raise ContractError(f"path escapes repository: {path}") from error


def _mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{field} must be an object")
    return value


def _allocation_from_fixture(
    fixture: Mapping[str, Any],
) -> Allocation:
    raw = _mapping(fixture.get("allocation"), field="allocation fixture allocation")
    fields = {
        "allocation_id",
        "container_name",
        "device_arch",
        "partition_mode",
        "numa_mode",
        "available_wall_s",
        "available_cpu_s",
        "available_gpu_s",
        "valid_from_utc",
        "valid_until_utc",
        "confirmed",
    }
    if set(raw) != fields:
        raise ContractError("allocation fixture fields differ from frozen interface")
    return _allocation_from_record(raw)


def _allocation_from_record(record: Mapping[str, Any]) -> Allocation:
    fields = {
        "allocation_id",
        "container_name",
        "device_arch",
        "partition_mode",
        "numa_mode",
        "available_wall_s",
        "available_cpu_s",
        "available_gpu_s",
        "valid_from_utc",
        "valid_until_utc",
        "confirmed",
    }
    missing = fields.difference(record)
    if missing:
        raise ContractError(
            f"allocation record omits frozen fields: {sorted(missing)}"
        )
    try:
        return Allocation(**{field: record[field] for field in fields})
    except (TypeError, ValueError) as error:
        raise ContractError(f"invalid allocation record: {error}") from error


def _allocation_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "allocation_id",
        "container_name",
        "device_arch",
        "partition_mode",
        "numa_mode",
        "available_wall_s",
        "available_cpu_s",
        "available_gpu_s",
        "valid_from_utc",
        "valid_until_utc",
        "confirmed",
    )
    missing = set(fields).difference(record)
    if missing:
        raise ContractError(
            f"allocation record omits frozen fields: {sorted(missing)}"
        )
    return {field: record[field] for field in fields}


def _verify_frozen_registry_bindings(
    contract: Mapping[str, Any],
    bindings: Mapping[str, Mapping[str, Any]],
    *,
    candidate_digest: str,
) -> None:
    expected = {
        "candidate_atom_registry": {
            "path": _mapping(contract.get("support"), field="support").get(
                "candidate_registry_path"
            ),
            "document_digest_field": "registry_digest",
            "document_digest": _mapping(
                contract.get("support"), field="support"
            ).get("candidate_registry_digest"),
        },
        "size_registry": {
            "path": _mapping(contract.get("correctness"), field="correctness").get(
                "size_registry_path"
            ),
            "document_digest_field": "size_registry_digest",
            "document_digest": _mapping(
                contract.get("correctness"), field="correctness"
            ).get("size_registry_digest"),
        },
    }
    if candidate_digest != expected["candidate_atom_registry"]["document_digest"]:
        raise ContractError("candidate registry digest differs from frozen contract")
    for name, identity in expected.items():
        binding = _mapping(bindings.get(name), field=f"artifact binding {name}")
        if any(binding.get(field) != value for field, value in identity.items()):
            raise ContractError(
                f"{name} path/document digest differs from frozen contract"
            )


def _verify_frozen_allocation_binding(
    contract: Mapping[str, Any],
    bindings: Mapping[str, Mapping[str, Any]],
    *,
    fixture_allocation: Allocation,
    repository_root: Path | str,
) -> None:
    binding = _mapping(
        bindings.get("allocation_record"),
        field="artifact binding allocation_record",
    )
    expected_path = _mapping(
        contract.get("formal_execution"), field="formal_execution"
    ).get("allocation_record")
    if (
        binding.get("path") != expected_path
        or binding.get("document_digest_field") is not None
        or binding.get("document_digest") is not None
    ):
        raise ContractError("allocation record path differs from frozen contract")
    candidate = (Path(repository_root).resolve() / str(expected_path)).resolve()
    document = strict_load_json(candidate)
    if not isinstance(document, Mapping):
        raise ContractError("allocation record is not an object")
    runtime_projection = _allocation_projection(document)
    fixture_projection = _allocation_projection(asdict(fixture_allocation))
    if canonical_json_bytes(runtime_projection) != canonical_json_bytes(
        fixture_projection
    ):
        raise ContractError("allocation record differs from calibrated fixture")


def canonicalize_contract(document: Mapping[str, Any]) -> dict[str, Any]:
    plain = plain_value(document)
    if not isinstance(plain, Mapping):
        raise ContractError("contract must be an object")
    # Round-trip through canonical JSON to reject representation-dependent
    # dict/list subclasses and establish the machine projection.
    import json

    return json.loads(canonical_json_bytes(plain).decode("utf-8"))


def load_contract(
    path: Path | str = DEFAULT_CONTRACT_PATH,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    document = strict_load_yaml(path)
    schema = strict_load_json(schema_path)
    if not isinstance(document, Mapping) or not isinstance(schema, Mapping):
        raise ContractError("contract and schema must be objects")
    validate_schema_document(document, schema, context="S10R2 contract")
    canonical = canonicalize_contract(document)
    _semantic_contract_checks(canonical)
    return canonical


def _semantic_contract_checks(contract: Mapping[str, Any]) -> None:
    if contract.get("checkpoint_id") != "S10R2":
        raise ContractError("contract checkpoint_id must be S10R2")
    authority = _mapping(contract.get("authority"), field="authority")
    if (
        authority.get("repair_budget_amendment_commit")
        != "bfe700ca76a17bd65509f3afff70abaf0ad125f4"
    ):
        raise ContractError("S10R2 repair budget amendment authority mismatch")
    schedule = _mapping(contract.get("schedule"), field="schedule")
    exact = {
        "chunk_size": 512,
        "global_chunks": 32,
        "conditional_chunks_each": 32,
        "maximum_conditional_targets": 15,
        "maximum_total_chunks": 512,
        "maximum_total_draws": 262_144,
        "first_resource_reforecast_chunk": 6,
        "first_resource_reforecast_draws": 3_072,
        "early_stop": False,
        "extension": False,
    }
    mismatches = {
        key: (schedule.get(key), value)
        for key, value in exact.items()
        if schedule.get(key) != value
    }
    if mismatches:
        raise ContractError(f"frozen S10R2 schedule mismatch: {mismatches}")
    support = _mapping(contract.get("support"), field="support")
    if support.get("states") != [
        "supported_witnessed",
        "support_unobserved",
        "support_proven_absent",
    ]:
        raise ContractError("support tri-state differs from authority")
    if support.get("stochastic_zero_implies_absence") is not False:
        raise ContractError("stochastic zero must not imply absence")
    if (
        support.get("candidate_registry_rows") != 10_024
        or support.get("prelocked_candidate_atom_count") != 101
        or support.get("conditional_diagnostic_atom_count") != 107
    ):
        raise ContractError("candidate registry count contract mismatch")
    mapping = _mapping(contract.get("mapping"), field="mapping")
    if (
        mapping.get("corpus_size") != 10
        or mapping.get("sizes") != 3
        or mapping.get("rows_per_pass") != 30
        or mapping.get("passes") != ["A", "B"]
        or mapping.get("replacement") is not False
    ):
        raise ContractError("exact-ten mapping contract mismatch")
    resource = _mapping(contract.get("resource"), field="resource")
    history = _mapping(
        resource.get("historical_carry_over"),
        field="resource.historical_carry_over",
    )
    if (
        history.get("completed_selection_chunks") != 3151
        or history.get("fresh_role_threads_lower_bound") != 10
        or history.get("repair_rounds_lower_bound") != 11
        or history.get("reset_by_s10r2") is not False
    ):
        raise ContractError("historical resource carry-over differs from A34")
    for field in (
        "wall_s",
        "cpu_s",
        "gpu_s",
        "preemp_engineering_s",
        "historical_peak_storage_bytes",
        "bytes_written",
    ):
        if history.get(field) != "UNKNOWN":
            raise ContractError(f"historical UNKNOWN was rewritten: {field}")
    prospective = _mapping(
        resource.get("prospective_limits"),
        field="resource.prospective_limits",
    )
    if prospective != {
        "fresh_role_threads": 5,
        "repair_rounds": 6,
        "shared_hands_on_s": 604800,
        "preemp_engineering_s": 120960,
        "transient_storage_bytes": 5368709120,
    }:
        raise ContractError("prospective A34/A35 limits mismatch")
    calibration = _mapping(
        resource.get("calibration_protocol"),
        field="resource.calibration_protocol",
    )
    if calibration.get("status") != "complete":
        raise ContractError("outcome-blind calibration protocol is incomplete")
    for name in (
        "selection_chunk",
        "native_build",
        "client_build",
        "mapping_row",
        "correctness_build_cell",
        "gpu_fixed_cost",
        "storage",
    ):
        item = _mapping(calibration.get(name), field=f"calibration_protocol.{name}")
        if name not in {"selection_chunk", "native_build"} and item.get("status") != "complete":
            raise ContractError(f"calibration component is incomplete: {name}")
    numeric = _mapping(
        resource.get("numeric_relock"),
        field="resource.numeric_relock",
    )
    contract_status = contract.get("status")
    numeric_status = numeric.get("status")
    numeric_fields = (
        "caps",
        "calibration_fixture_digest",
        "calibration_input_contract_digest",
        "initial_resource_counter",
        "unbuffered_projection",
        "reservations",
        "preemp_engineering",
    )
    if contract_status == "draft_numeric_caps_pending":
        if numeric_status != "pending" or any(numeric.get(field) is not None for field in numeric_fields):
            raise ContractError("draft contract must keep numeric relock pending")
    elif contract_status in {"frozen_pre_evidence", "effective"}:
        if numeric_status != "approved" or any(numeric.get(field) is None for field in numeric_fields):
            raise ContractError("frozen contract requires complete numeric relock")
        caps = _mapping(numeric.get("caps"), field="resource.numeric_relock.caps")
        initial = _mapping(
            numeric.get("initial_resource_counter"),
            field="resource.numeric_relock.initial_resource_counter",
        )
        projection = _mapping(
            numeric.get("unbuffered_projection"),
            field="resource.numeric_relock.unbuffered_projection",
        )
        reservations = _mapping(
            numeric.get("reservations"),
            field="resource.numeric_relock.reservations",
        )
        preemp = _mapping(
            numeric.get("preemp_engineering"),
            field="resource.numeric_relock.preemp_engineering",
        )
        if (
            preemp.get("cap_s") != prospective["preemp_engineering_s"]
            or preemp.get("measurement_basis") != "elapsed_UTC_upper_bound"
            or preemp.get("exact_through_lock_recorded_in_lock") is not True
            or preemp.get("charged_before_formal_s")
            != preemp.get("measured_through_fixture_s", 0)
            + preemp.get("audit_and_seal_reservation_s", 0)
            or preemp.get("charged_before_formal_s", 0) > preemp.get("cap_s", 0)
        ):
            raise ContractError("pre-empirical engineering charge mismatch")
        if caps.get("transient_storage_bytes", 0) > prospective["transient_storage_bytes"]:
            raise ContractError("numeric storage cap exceeds A34 ceiling")
        for label, values in (
            ("caps", caps),
            ("initial_resource_counter", initial),
            ("unbuffered_projection", projection),
        ):
            for field in ("wall_s", "cpu_s", "gpu_s", "transient_storage_bytes"):
                value = values.get(field)
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or value < 0
                    or (label == "caps" and value <= 0)
                ):
                    raise ContractError(f"invalid numeric resource {label}.{field}")
        required_reservations = {
            "selection_chunk",
            "mapping_ab",
            "native_conformance",
            "gpu_environment",
            "correctness_anchor",
            "noise_anchor_repeat",
            "decision",
        }
        if set(reservations) != required_reservations:
            raise ContractError("formal resource reservation set mismatch")
        for name, values in reservations.items():
            counter = _mapping(values, field=f"resource reservation {name}")
            for field in ("wall_s", "cpu_s", "gpu_s", "transient_storage_bytes"):
                value = counter.get(field)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                    raise ContractError(f"invalid resource reservation {name}.{field}")
    else:
        raise ContractError("unsupported contract status")
    correctness = _mapping(contract.get("correctness"), field="correctness")
    if (
        correctness.get("anchor_indices") != [0, 4, 9]
        or correctness.get("cells") != 9
        or correctness.get("validation_elements") != 128
        or correctness.get("atomic_unit") != "one_anchor_all_three_sizes"
    ):
        raise ContractError("correctness anchor contract mismatch")
    noise = _mapping(contract.get("noise"), field="noise")
    if (
        noise.get("anchors") != 3
        or noise.get("sizes") != 3
        or noise.get("repeats") != 7
        or noise.get("cells") != 63
        or noise.get("cv_p95_threshold") != 0.005
        or noise.get("reduce_fn") != "max"
        or noise.get("schedule_order") != "sorted_anchor_hash_then_repeat_0_to_6"
        or noise.get("atomic_unit") != "one_anchor_repeat_all_three_sizes"
    ):
        raise ContractError("noise contract mismatch")
    native = _mapping(contract.get("native_conformance"), field="native_conformance")
    binding = _mapping(native.get("binding"), field="native_conformance.binding")
    helper_source = REPOSITORY_ROOT / str(native.get("helper_source"))
    host_adapter = REPOSITORY_ROOT / str(native.get("host_adapter"))
    if binding.get("helper_source_sha256") != sha256_file(helper_source):
        raise ContractError("native helper source binding mismatch")
    if binding.get("host_adapter_sha256") != sha256_file(host_adapter):
        raise ContractError("native host adapter binding mismatch")
    from .conformance import materialize_native_fixture

    materialized = materialize_native_fixture(
        _mapping(
            native.get("synthetic_fixture"),
            field="native_conformance.synthetic_fixture",
        ),
        native.get("thresholds", []),
    )
    if (
        native.get("synthetic_fixture_digest") != materialized["fixture_digest"]
        or native.get("synthetic_fixture_input_sha256")
        != materialized["input_sha256"]
    ):
        raise ContractError("native synthetic fixture identity mismatch")
    decision = _mapping(contract.get("decision"), field="decision")
    if decision.get("only_positive_edge") != "S10R2:S1_ENTRY_GO -> S11":
        raise ContractError("unexpected outgoing edge")
    formal = _mapping(contract.get("formal_execution"), field="formal_execution")
    if (
        formal.get("required_container_name") != "perlee"
        or formal.get("required_container_env") != "S10R2_CONTAINER_NAME"
        or formal.get("process_version") != "s10r2/v1"
        or formal.get("physical_device_selection")
        != (
            "lowest_visible_zero_use_zero_vram_no_foreign_pid_"
            "gfx942_SPX_NPS1"
        )
        or formal.get("logical_device_index") != 0
        or formal.get("gpu_time_accounting") != "elapsed_wall_upper_bound"
    ):
        raise ContractError("formal execution boundary mismatch")
    for field in (
        "run_root",
        "lineage_root",
        "pinned_integration_root",
        "pinned_materialization_manifest",
        "native_build_manifest",
        "client_build_record",
        "allocation_record",
        "calibration_metrics_record",
        "resource_calibration_fixture",
    ):
        value = str(formal.get(field, ""))
        if not value.startswith("agent_run/") or "s10r1" in value.lower():
            raise ContractError(f"formal execution path is outside S10R2 run root: {field}")
    implementation = contract.get("implementation_whitelist")
    if implementation != EXPECTED_IMPLEMENTATION_WHITELIST:
        raise ContractError("implementation whitelist differs from frozen exact paths")
    delivery = contract.get("delivery_whitelist")
    if not isinstance(delivery, Sequence) or isinstance(delivery, (str, bytes)):
        raise ContractError("delivery_whitelist must be an array")
    if not set(EXPECTED_IMPLEMENTATION_WHITELIST).issubset(delivery):
        raise ContractError("delivery whitelist omits implementation paths")
    forbidden = contract.get("forbidden_evidence_reuse")
    if not isinstance(forbidden, Sequence) or isinstance(forbidden, (str, bytes)):
        raise ContractError("forbidden_evidence_reuse must be an array")
    if not any("S10R1" in str(item) for item in forbidden):
        raise ContractError("S10R1 evidence non-reuse must be explicit")
    for path in contract.get("implementation_whitelist", []):
        if "s10r1" in str(path).lower():
            raise ContractError("S10R1 path is forbidden in implementation whitelist")


def verify_human_machine_parity(
    human_contract: Mapping[str, Any],
    machine_projection: Mapping[str, Any],
) -> str:
    human = canonicalize_contract(human_contract)
    machine = canonicalize_contract(machine_projection)
    if human != machine:
        keys = sorted(set(human).union(machine))
        differing = [key for key in keys if human.get(key) != machine.get(key)]
        raise ContractError(f"human/machine contract parity mismatch: {differing}")
    return canonical_sha256(human)


def implementation_hashes(
    whitelist: Sequence[str],
    *,
    repository_root: Path | str = REPOSITORY_ROOT,
) -> dict[str, str]:
    root = Path(repository_root).resolve()
    result: dict[str, str] = {}
    for relative in whitelist:
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ContractError(f"implementation path escapes repository: {relative}") from error
        if not candidate.is_file():
            raise ContractError(f"implementation whitelist path absent: {relative}")
        result[str(relative)] = sha256_file(candidate)
    return result


def lock_body(
    *,
    contract: Mapping[str, Any],
    contract_path: Path | str = DEFAULT_CONTRACT_PATH,
    schema_path: Path | str,
    audit: Mapping[str, Any],
    allocation_fixture: Mapping[str, Any],
    implementation: Mapping[str, str],
    registry_digest: str,
    artifact_bindings: Mapping[str, Mapping[str, Any]],
    prelock_elapsed_s: float,
    sealed_at_utc: str | None = None,
) -> dict[str, Any]:
    if (
        audit.get("verdict") != "AUDIT_PASS"
        or audit.get("checkpoint_id") != "S10R2"
        or audit.get("fresh") is not True
        or audit.get("role") != "adversarial_oracle_authority_auditor"
        or not audit.get("thread_id")
        or audit.get("contract_digest") != canonical_sha256(contract)
    ):
        raise ContractError("effective lock requires fresh AUDIT_PASS")
    resource = _mapping(contract.get("resource"), field="resource")
    numeric = _mapping(resource.get("numeric_relock"), field="resource.numeric_relock")
    if numeric.get("status") != "approved":
        raise ContractError("effective lock requires approved numeric relock")
    contract_relative = _repository_relative(contract_path)
    expected_contract_relative = _repository_relative(DEFAULT_CONTRACT_PATH)
    if contract_relative != expected_contract_relative:
        raise ContractError("effective lock contract path differs from canonical path")
    if Path(schema_path).resolve() != DEFAULT_SCHEMA_PATH.resolve():
        raise ContractError("effective lock schema path differs from canonical path")
    caps = _mapping(numeric.get("caps"), field="resource.numeric_relock.caps")
    for field in ("wall_s", "cpu_s", "gpu_s", "transient_storage_bytes"):
        value = caps.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise ContractError(f"numeric resource cap {field} is not positive")
    if allocation_fixture.get("status") != "CALIBRATION_COMPLETE":
        raise ContractError("allocation fixture is not complete")
    fixture_digest = allocation_fixture.get("fixture_digest")
    fixture_body = dict(allocation_fixture)
    fixture_body.pop("fixture_digest", None)
    if fixture_digest != canonical_sha256(fixture_body):
        raise ContractError("allocation fixture digest mismatch")
    if numeric.get("calibration_fixture_digest") != fixture_digest:
        raise ContractError("numeric relock/calibration fixture digest mismatch")
    if numeric.get("calibration_input_contract_digest") != allocation_fixture.get(
        "contract_digest"
    ):
        raise ContractError("calibration input contract digest mismatch")
    if allocation_fixture.get("proposed_caps") != caps:
        raise ContractError("numeric relock caps differ from calibrated proposal")
    if sealed_at_utc is None:
        raise ContractError("effective lock requires an exact seal timestamp")
    try:
        seal_time = parse_utc_timestamp(sealed_at_utc, field="sealed_at_utc")
        allocation = _allocation_from_fixture(allocation_fixture)
        validate_allocation(
            allocation,
            at_utc=seal_time,
            required_duration_s=float(caps["wall_s"]),
        )
    except CalibrationError as error:
        raise ContractError(f"allocation window cannot authorize lock: {error}") from error
    preemp = _mapping(
        numeric.get("preemp_engineering"),
        field="resource.numeric_relock.preemp_engineering",
    )
    if (
        isinstance(prelock_elapsed_s, bool)
        or not isinstance(prelock_elapsed_s, (int, float))
        or prelock_elapsed_s < preemp.get("measured_through_fixture_s", 0)
        or prelock_elapsed_s > preemp.get("charged_before_formal_s", 0)
    ):
        raise ContractError("pre-lock engineering elapsed time exceeds frozen reservation")
    if set(artifact_bindings) != EXPECTED_BOUND_ARTIFACTS:
        raise ContractError("effective lock artifact binding set mismatch")
    _verify_artifact_bindings(
        artifact_bindings,
        repository_root=REPOSITORY_ROOT,
    )
    _verify_frozen_registry_bindings(
        contract,
        artifact_bindings,
        candidate_digest=registry_digest,
    )
    _verify_frozen_allocation_binding(
        contract,
        artifact_bindings,
        fixture_allocation=allocation,
        repository_root=REPOSITORY_ROOT,
    )
    return {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "status": "effective",
        "contract_path": contract_relative,
        "contract_digest": canonical_sha256(contract),
        "schema_sha256": sha256_file(schema_path),
        "audit_identity": dict(audit),
        "allocation_fixture_digest": fixture_digest,
        "sealed_at_utc": sealed_at_utc,
        "allocation_window": {
            "allocation_id": allocation.allocation_id,
            "valid_from_utc": allocation.valid_from_utc,
            "valid_until_utc": allocation.valid_until_utc,
            "full_panel_wall_s": caps["wall_s"],
        },
        "resource_caps": dict(caps),
        "initial_resource_counter": dict(numeric["initial_resource_counter"]),
        "resource_reservations": dict(numeric["reservations"]),
        "preemp_engineering": {
            **dict(preemp),
            "exact_through_lock_s": prelock_elapsed_s,
        },
        "implementation_hashes": dict(sorted(implementation.items())),
        "implementation_whitelist": list(contract["implementation_whitelist"]),
        "delivery_whitelist": list(contract["delivery_whitelist"]),
        "source_identity": contract["source_identity"],
        "candidate_atom_registry_digest": registry_digest,
        "artifact_bindings": {
            name: dict(artifact_bindings[name]) for name in sorted(artifact_bindings)
        },
        "outcome_artifacts_absent_at_seal": True,
        "only_positive_edge": "S10R2:S1_ENTRY_GO -> S11",
    }


def _verify_artifact_bindings(
    bindings: Mapping[str, Mapping[str, Any]],
    *,
    repository_root: Path | str,
) -> None:
    root = Path(repository_root).resolve()
    if set(bindings) != EXPECTED_BOUND_ARTIFACTS:
        raise ContractError("locked artifact binding set mismatch")
    for name, raw in bindings.items():
        if not isinstance(raw, Mapping):
            raise ContractError(f"artifact binding is not an object: {name}")
        if set(raw) != {
            "path",
            "sha256",
            "document_digest_field",
            "document_digest",
        }:
            raise ContractError(f"artifact binding fields mismatch: {name}")
        relative = str(raw["path"])
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ContractError(f"artifact binding escapes repository: {name}") from error
        if not candidate.is_file() or sha256_file(candidate) != raw["sha256"]:
            raise ContractError(f"artifact binding file/hash mismatch: {name}")
        digest_field = raw["document_digest_field"]
        digest_value = raw["document_digest"]
        if digest_field is None:
            if digest_value is not None:
                raise ContractError(f"binary binding has document digest: {name}")
            continue
        document = strict_load_json(candidate)
        if not isinstance(document, Mapping):
            raise ContractError(f"bound document is not an object: {name}")
        body = dict(document)
        recorded = body.pop(str(digest_field), None)
        if recorded != digest_value or recorded != canonical_sha256(body):
            raise ContractError(f"bound document digest mismatch: {name}")


def seal_lock_document(body: Mapping[str, Any]) -> dict[str, Any]:
    if "lock_digest" in body:
        raise ContractError("unsealed lock body must not contain lock_digest")
    return {**dict(body), "lock_digest": canonical_sha256(body)}


def verify_lock_seal(
    lock: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
    repository_root: Path | str = REPOSITORY_ROOT,
) -> str:
    body = dict(lock)
    recorded_digest = body.pop("lock_digest", None)
    if recorded_digest != canonical_sha256(body):
        raise ContractError("effective lock digest mismatch")
    if body.get("status") != "effective" or body.get("checkpoint_id") != "S10R2":
        raise ContractError("lock is not an effective S10R2 lock")
    if body.get("contract_path") != _repository_relative(DEFAULT_CONTRACT_PATH):
        raise ContractError("lock contract path mismatch")
    if body.get("contract_digest") != canonical_sha256(contract):
        raise ContractError("lock/contract digest mismatch")
    if body.get("schema_sha256") != sha256_file(schema_path):
        raise ContractError("lock/schema digest mismatch")
    if body.get("audit_identity", {}).get("verdict") != "AUDIT_PASS":
        raise ContractError("lock lacks fresh AUDIT_PASS")
    if body.get("implementation_whitelist") != contract.get("implementation_whitelist"):
        raise ContractError("lock implementation whitelist mismatch")
    if body.get("delivery_whitelist") != contract.get("delivery_whitelist"):
        raise ContractError("lock delivery whitelist mismatch")
    current_hashes = implementation_hashes(
        contract["implementation_whitelist"], repository_root=repository_root
    )
    if body.get("implementation_hashes") != current_hashes:
        raise ContractError("locked implementation hash mismatch")
    if body.get("source_identity") != contract.get("source_identity"):
        raise ContractError("locked source identity mismatch")
    numeric = _mapping(
        _mapping(contract.get("resource"), field="resource").get("numeric_relock"),
        field="resource.numeric_relock",
    )
    if body.get("resource_caps") != numeric.get("caps"):
        raise ContractError("locked resource caps mismatch")
    if body.get("initial_resource_counter") != numeric.get("initial_resource_counter"):
        raise ContractError("locked initial resource counter mismatch")
    if body.get("resource_reservations") != numeric.get("reservations"):
        raise ContractError("locked resource reservations mismatch")
    preemp = body.get("preemp_engineering")
    if not isinstance(preemp, Mapping):
        raise ContractError("lock lacks pre-empirical engineering record")
    expected_preemp = numeric.get("preemp_engineering")
    if (
        {key: preemp.get(key) for key in expected_preemp} != expected_preemp
        or not isinstance(preemp.get("exact_through_lock_s"), (int, float))
        or isinstance(preemp.get("exact_through_lock_s"), bool)
        or preemp["exact_through_lock_s"]
        < expected_preemp["measured_through_fixture_s"]
        or preemp["exact_through_lock_s"] > expected_preemp["charged_before_formal_s"]
    ):
        raise ContractError("locked pre-empirical engineering record mismatch")
    if body.get("allocation_fixture_digest") != numeric.get(
        "calibration_fixture_digest"
    ):
        raise ContractError("locked calibration fixture mismatch")
    bindings = body.get("artifact_bindings")
    if not isinstance(bindings, Mapping):
        raise ContractError("lock lacks artifact bindings")
    _verify_artifact_bindings(bindings, repository_root=repository_root)
    candidate_digest = body.get("candidate_atom_registry_digest")
    if not isinstance(candidate_digest, str):
        raise ContractError("lock lacks candidate registry digest")
    _verify_frozen_registry_bindings(
        contract,
        bindings,
        candidate_digest=candidate_digest,
    )
    fixture_binding = _mapping(
        bindings.get("resource_calibration_fixture"),
        field="resource calibration fixture binding",
    )
    fixture_path = (
        Path(repository_root).resolve() / str(fixture_binding.get("path"))
    ).resolve()
    fixture = strict_load_json(fixture_path)
    if not isinstance(fixture, Mapping):
        raise ContractError("resource calibration fixture is not an object")
    allocation = _allocation_from_fixture(fixture)
    _verify_frozen_allocation_binding(
        contract,
        bindings,
        fixture_allocation=allocation,
        repository_root=repository_root,
    )
    sealed_at_utc = body.get("sealed_at_utc")
    try:
        seal_time = parse_utc_timestamp(sealed_at_utc, field="sealed_at_utc")
        validate_allocation(
            allocation,
            at_utc=seal_time,
            required_duration_s=float(numeric["caps"]["wall_s"]),
        )
    except CalibrationError as error:
        raise ContractError(f"locked allocation window mismatch: {error}") from error
    expected_window = {
        "allocation_id": allocation.allocation_id,
        "valid_from_utc": allocation.valid_from_utc,
        "valid_until_utc": allocation.valid_until_utc,
        "full_panel_wall_s": numeric["caps"]["wall_s"],
    }
    if body.get("allocation_window") != expected_window:
        raise ContractError("locked allocation window identity mismatch")
    if body.get("outcome_artifacts_absent_at_seal") is not True:
        raise ContractError("lock did not attest pre-outcome absence")
    if body.get("only_positive_edge") != "S10R2:S1_ENTRY_GO -> S11":
        raise ContractError("lock outgoing edge mismatch")
    return str(recorded_digest)
