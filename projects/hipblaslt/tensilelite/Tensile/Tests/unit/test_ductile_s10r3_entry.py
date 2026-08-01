# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Offline, synthetic, label-blind tests for the S10R3 entry implementation."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import tempfile
import types
import struct
import subprocess
import sys
from dataclasses import replace as dataclass_replace
from pathlib import Path

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[6]
PROTOCOL_ROOT = (
    ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1"
)
if str(PROTOCOL_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOCOL_ROOT))

import s10r3.contract as contract_module  # noqa: E402

from s10r3.conformance import (  # noqa: E402
    ConformanceError,
    EARLY_TERMINATE,
    GUARD_ORDER,
    compare_native_transcript,
    expected_native_transcript,
    fixture_document,
    independent_oracle,
    validate_fixture,
    validate_pinned_guard_source,
)
from s10r3.contract import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    EXPECTED_CONTRACT_ID,
    EXPECTED_CONTRACT_SCHEMA_VERSION,
    EXPECTED_CONTRACT_CANONICAL_SHA256,
    EXPECTED_CONTRACT_RAW_SHA256,
    EXPECTED_ORACLE_PROJECTION_SHA256,
    EXPECTED_PLAN_A_FREEZE_SHA256,
    EXPECTED_PLAN_A_PATH,
    EXPECTED_PLAN_A_REVISION,
    EXPECTED_PLAN_A_SHA256,
    EXPECTED_PLAN_A_SIZE_BYTES,
    EXPECTED_PLAN_B_FREEZE_SHA256,
    EXPECTED_PLAN_B_PATH,
    EXPECTED_PLAN_B_REVISION,
    EXPECTED_PLAN_B_SHA256,
    IMPLEMENTATION_PATHS,
    PLAN_A_FREEZE_ID,
    PLAN_B_FREEZE_ID,
    PREDECESSOR_COMPONENT_IDS,
    PRELABEL_ROOTS,
    PRODUCTION_ADMISSION_LOCK_PATH,
    PRODUCTION_ADMISSION_RESOLVED_PATH,
    PRODUCTION_SINGLE_FILE_LOGICAL_BASENAMES,
    PRODUCTION_TRANSITION_PATHS,
    SUCCESSOR_FORMAL_SCOPES,
    SUCCESSOR_OUTCOME_PATHS,
    SUCCESSOR_AUDIT_CHECKS,
    ContractError,
    _authorized_transition_path,
    _governance_binding,
    _load_freeze,
    _load_current_plan_b_freeze,
    admission_lock_identity,
    canonical_sha256,
    component_inventory,
    create_stable_admission_lock,
    load_contract,
    new_transition_journal,
    oracle_projection,
    rename_noreplace,
    sha256_file,
    stable_admission_lock,
    strict_load_json,
    strict_load_yaml,
    transition_recovery_action,
    validate_transition_journal,
    append_transition_event,
    acquire_manifest_repair_locks,
    build_capsule_manifest,
    build_lineage_seal,
    classify_one_time_manifest_repair,
    build_resource_lineage_binding,
    manifest_repair_binding,
    repair_staging_manifest_once,
    successor_manifest_repair_binding,
    write_transition_journal,
    validate_capsule_manifest,
    validate_resource_lineage_binding,
    validate_lineage_seal,
    validate_embedded_contract_schemas,
    validate_document,
    validate_successor_audit_checks,
    G2_LINEAGE_SELECTOR,
    G2ComponentSpec,
    append_g2_transition_event,
    build_g2_capsule_manifest,
    execute_g2_transition,
    g2_lineage_spec,
    new_g2_transition_journal,
    validate_g2_capsule_manifest,
    validate_g2_lineage_seal,
    validate_g2_transition_journal,
    validate_mapping_failure_batch,
    validate_mapping_failure_signature,
    validate_mapping_worker_completion,
)
from s10r3.correctness import (  # noqa: E402
    CorrectnessError,
    anchor_hashes,
    validate_noise_cells,
    verify_correctness_cells,
)
from s10r3.ledger import LedgerError, RunLedger  # noqa: E402
from s10r3.mapping import (  # noqa: E402
    FORMOCAST_FIELDS,
    MAPPING_FAILURE_MARKER,
    MAPPING_FAILURE_RETURN_CODE,
    MappingError,
    mapping_worker_code,
    mapping_row,
    run_mapping_batch,
    size_registry_document,
    verify_mapping_parity,
)
from s10r3.native_adapter import (  # noqa: E402
    NativeAdapterError,
    NativeBinding,
    PinnedNativeFormocastRuntimeAdapter,
)
from s10r3.selector import (  # noqa: E402
    Witness,
    deterministic_greedy_bounded_cover,
    mandatory_mapping_atoms,
)
from s10r3.state_machine import (  # noqa: E402
    Stage,
    TransitionError,
    assert_transition,
    require_complete_unit,
    transition_path_is_valid,
)
from s10r3.support import (  # noqa: E402
    CHUNK_SIZE,
    CONDITIONAL_CHUNKS,
    GLOBAL_CHUNKS,
    MAX_CONDITIONAL_TARGETS,
    MAX_TOTAL_CHUNKS,
    MAX_TOTAL_DRAWS,
    AtomRegistry,
    AxisSpec,
    SupportState,
    activate_conditional_targets,
    axis_specs_from_registry,
    categorical_index,
    deterministic_seed,
    generate_discovery_chunk,
    guidance_eligible_axes,
    uniform_masses,
    weighted_masses,
)


def _float32(values):
    packed = b"".join(struct.pack("=f", value) for value in values)
    return (
        tuple(
            struct.unpack("=f", packed[index : index + 4])[0]
            for index in range(0, len(packed), 4)
        ),
        hashlib.sha256(packed).hexdigest(),
    )


def _registry(*, axis_zero_count: int = 3, weighted_axis: int | None = None):
    axes = []
    for axis_index in range(30):
        values = (
            tuple(range(axis_zero_count))
            if axis_index == 0
            else (False, True)
        )
        weighted = axis_index == weighted_axis
        if weighted:
            probabilities, digest = _float32(
                [0.25, 0.75] if len(values) == 2 else [1 / len(values)] * len(values)
            )
        else:
            probabilities, digest = (), None
        axes.append(
            AxisSpec(
                axis_index=axis_index,
                axis_name=f"axis{axis_index}",
                values=values,
                grouped=False,
                frozen_free=True,
                currently_weighted=weighted,
                yaml_pointer=f"/axes/{axis_index}",
                probabilities=probabilities,
                probabilities_raw_sha256=digest,
            )
        )
    return AtomRegistry(axes)


def _config(registry: AtomRegistry, index: int):
    return {
        axis.axis_name: axis.values[index % len(axis.values)]
        for axis in registry.axes
    }


def _witness(
    registry: AtomRegistry,
    index: int,
    atoms,
    *,
    occurrence: int | None = None,
):
    config = _config(registry, index)
    config["synthetic_nonce"] = index
    return Witness(
        config=config,
        config_hash=canonical_sha256(config),
        atom_ids=frozenset(atoms),
        stream_rank=0,
        conditional_priority_rank=0,
        chunk_index=0,
        draw_index=index if occurrence is None else occurrence,
    )


def test_phase1_contract_exact_identities():
    contract = load_contract()
    assert contract["schema_version"] == EXPECTED_CONTRACT_SCHEMA_VERSION == 10
    assert contract["contract_id"] == EXPECTED_CONTRACT_ID
    assert sha256_file(DEFAULT_CONTRACT_PATH) == EXPECTED_CONTRACT_RAW_SHA256
    assert canonical_sha256(contract) == EXPECTED_CONTRACT_CANONICAL_SHA256
    assert canonical_sha256(oracle_projection(contract)) == EXPECTED_ORACLE_PROJECTION_SHA256
    assert tuple(contract["write_boundaries"]["implementation"]) == IMPLEMENTATION_PATHS


def test_contract_workflow_and_scientific_drift_rejected():
    contract = load_contract()
    drift = copy.deepcopy(contract)
    drift["bounded_cover_selector"]["k_maximum"] = 21
    assert canonical_sha256(drift) != EXPECTED_CONTRACT_CANONICAL_SHA256
    drift = copy.deepcopy(contract)
    drift["workflow_authority_manifest"]["entries"][0]["sha256"] = "0" * 64
    assert canonical_sha256(drift) != EXPECTED_CONTRACT_CANONICAL_SHA256


@pytest.mark.parametrize(
    ("plan_id", "revision"),
    [
        (PLAN_A_FREEZE_ID, EXPECTED_PLAN_A_REVISION),
        (PLAN_B_FREEZE_ID, EXPECTED_PLAN_B_REVISION),
    ],
)
def test_exact_current_freeze_plan_ids_and_rejects_other_ids(
    tmp_path, monkeypatch, plan_id, revision
):
    monkeypatch.setattr(contract_module, "REPOSITORY_ROOT", tmp_path)
    relative_plan = Path("plans") / f"{plan_id.lower()}.md"
    plan = tmp_path / relative_plan
    plan.parent.mkdir()
    plan.write_bytes(f"frozen {plan_id} bytes\n".encode())
    freeze = {
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "plan_id": plan_id,
        "revision": revision,
        "path": relative_plan.as_posix(),
        "sha256": sha256_file(plan),
        "size_bytes": plan.stat().st_size,
        "mode": "0664",
        "regular_file": True,
        "symlink": False,
        "frozen": True,
        "mutable": False,
        "implementation_allowed": False,
    }
    freeze_path = tmp_path / f"{plan_id.lower()}.freeze.json"
    freeze_path.write_text(json.dumps(freeze))
    assert _load_freeze(freeze_path, plan_id=plan_id) == freeze

    wrong = dict(freeze)
    wrong["plan_id"] = f"{plan_id}-OTHER"
    freeze_path.write_text(json.dumps(wrong))
    with pytest.raises(ContractError, match=f"{plan_id} freeze identity mismatch"):
        _load_freeze(freeze_path, plan_id=plan_id)


def test_current_plan_a_revision_nineteen_identity_is_frozen():
    freeze_path = (
        ROOT
        / "agent_run/260730-ductile-factorized-guidance-s10r3-restart/"
        "gates/s10r3/plan_a.freeze.json"
    )
    freeze = contract_module._load_current_plan_a_freeze(freeze_path)
    assert sha256_file(freeze_path) == EXPECTED_PLAN_A_FREEZE_SHA256
    assert {
        "path": freeze["path"],
        "sha256": freeze["sha256"],
        "size_bytes": freeze["size_bytes"],
        "revision": freeze["revision"],
    } == {
        "path": EXPECTED_PLAN_A_PATH,
        "sha256": EXPECTED_PLAN_A_SHA256,
        "size_bytes": EXPECTED_PLAN_A_SIZE_BYTES,
        "revision": EXPECTED_PLAN_A_REVISION,
    }


def _synthetic_current_plan_b_freeze(tmp_path, monkeypatch):
    monkeypatch.setattr(contract_module, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(
        contract_module,
        "DEFAULT_CONTRACT_PATH",
        tmp_path
        / "study_docs/research/ductile-origami-warmstart/protocol/v1/"
        "s10r3-stage1-bounded-cover-entry-contract.yaml",
    )
    plan = tmp_path / EXPECTED_PLAN_B_PATH
    plan.parent.mkdir(parents=True)
    synthetic_size = 257
    plan.write_bytes(b"P" * synthetic_size)
    plan.chmod(0o664)
    record = {
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "plan_id": PLAN_B_FREEZE_ID,
        "revision": EXPECTED_PLAN_B_REVISION,
        "plan_kind": "goal_oracle",
        "path": EXPECTED_PLAN_B_PATH,
        "sha256": EXPECTED_PLAN_B_SHA256,
        "size_bytes": synthetic_size,
        "mode": "0664",
        "authored_by": "/root",
        "phase1_seal_commit": contract_module.PHASE1_SEAL_COMMIT,
        "frozen_contract_raw_sha256": EXPECTED_CONTRACT_RAW_SHA256,
        "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
        "phase1_post_commit_verdict": "AUDIT_PASS_POSTCOMMIT_A46_5",
        "repair_count_is_stop_gate": False,
        "frozen": True,
        "mutable": False,
        "visible_to": ["main", "adversarial_auditor", "fresh_verifier"],
        "forbidden_to": ["fresh_implementer"],
    }
    freeze_path = tmp_path / "synthetic-plan-b.freeze.json"
    freeze_path.write_text(json.dumps(record))
    real_sha256_file = contract_module.sha256_file

    def exact_current_hash(path):
        candidate = Path(path)
        if candidate == plan:
            if candidate.read_bytes() == b"P" * synthetic_size:
                return EXPECTED_PLAN_B_SHA256
            return real_sha256_file(path)
        if candidate == freeze_path:
            return EXPECTED_PLAN_B_FREEZE_SHA256
        return real_sha256_file(path)

    monkeypatch.setattr(contract_module, "sha256_file", exact_current_hash)
    return freeze_path, plan, record


def test_current_plan_b_revision_nine_exact_freeze_is_accepted(tmp_path, monkeypatch):
    freeze_path, _, record = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    accepted = _load_current_plan_b_freeze(freeze_path)
    assert accepted == record
    assert accepted["visible_to"] == [
        "main",
        "adversarial_auditor",
        "fresh_verifier",
    ]
    assert accepted["forbidden_to"] == ["fresh_implementer"]
    assert "role_visibility" not in accepted


@pytest.mark.parametrize(
    "wrong_id",
    ["S10R3-PLAN-B-V2", "S10R3-PLAN-B-V3", "S10R3-PLAN-B-OTHER"],
)
def test_current_plan_b_rejects_every_non_current_id(tmp_path, monkeypatch, wrong_id):
    freeze_path, _, record = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    record["plan_id"] = wrong_id
    freeze_path.write_text(json.dumps(record))
    with pytest.raises(ContractError, match="Plan-B top-level freeze binding mismatch"):
        _load_current_plan_b_freeze(freeze_path)


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    [
        ("revision", 3),
        ("path", "plans/not-the-current-plan-b.md"),
        ("sha256", "0" * 64),
        ("size_bytes", 258),
    ],
)
def test_current_plan_b_rejects_changed_plan_binding(
    tmp_path, monkeypatch, field, wrong_value
):
    freeze_path, _, record = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    record[field] = wrong_value
    freeze_path.write_text(json.dumps(record))
    with pytest.raises(ContractError):
        _load_current_plan_b_freeze(freeze_path)


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    [
        ("schema_version", 2),
        ("schema_version", True),
        ("checkpoint_id", "S10R2"),
        ("plan_kind", "implementation"),
        ("mode", "0644"),
        ("authored_by", "/root/other"),
        ("frozen", False),
        ("frozen", 1),
        ("mutable", True),
        ("mutable", 0),
        ("repair_count_is_stop_gate", 0),
    ],
)
def test_current_plan_b_rejects_changed_exact_shape_field(
    tmp_path, monkeypatch, field, wrong_value
):
    freeze_path, _, record = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    record[field] = wrong_value
    freeze_path.write_text(json.dumps(record))
    with pytest.raises(ContractError, match="Plan-B top-level freeze binding mismatch"):
        _load_current_plan_b_freeze(freeze_path)


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    [
        ("phase1_seal_commit", "0" * 40),
        ("frozen_contract_raw_sha256", "0" * 64),
        ("scientific_oracle_projection_sha256", "0" * 64),
        ("phase1_post_commit_verdict", "AUDIT_FAIL"),
        ("repair_count_is_stop_gate", True),
    ],
)
def test_current_plan_b_rejects_mutated_top_level_a46_2_seal_field(
    tmp_path, monkeypatch, field, wrong_value
):
    freeze_path, _, record = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    record[field] = wrong_value
    freeze_path.write_text(json.dumps(record))
    with pytest.raises(ContractError, match="Plan-B top-level freeze binding mismatch"):
        _load_current_plan_b_freeze(freeze_path)


@pytest.mark.parametrize(
    "field",
    [
        "phase1_seal_commit",
        "frozen_contract_raw_sha256",
        "scientific_oracle_projection_sha256",
        "phase1_post_commit_verdict",
        "repair_count_is_stop_gate",
    ],
)
def test_current_plan_b_rejects_omitted_top_level_a46_2_seal_field(
    tmp_path, monkeypatch, field
):
    freeze_path, _, record = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    record.pop(field)
    freeze_path.write_text(json.dumps(record))
    with pytest.raises(ContractError, match="Plan-B top-level freeze binding mismatch"):
        _load_current_plan_b_freeze(freeze_path)


def test_current_plan_b_rejects_predecessor_nested_only_phase1_shape(
    tmp_path, monkeypatch
):
    freeze_path, _, record = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    for field in (
        "phase1_seal_commit",
        "frozen_contract_raw_sha256",
        "scientific_oracle_projection_sha256",
        "phase1_post_commit_verdict",
        "repair_count_is_stop_gate",
    ):
        record.pop(field)
    record["phase1_seal"] = contract_module._current_phase1_plan_binding()
    freeze_path.write_text(json.dumps(record))
    with pytest.raises(ContractError, match="Plan-B top-level freeze binding mismatch"):
        _load_current_plan_b_freeze(freeze_path)


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    [
        (
            "visible_to",
            ["adversarial_auditor", "main", "fresh_verifier"],
        ),
        (
            "visible_to",
            [
                "main",
                "adversarial_auditor",
                "fresh_verifier",
                "fresh_implementer",
            ],
        ),
        ("visible_to", ["main", "adversarial_auditor"]),
        ("visible_to", "main,adversarial_auditor,fresh_verifier"),
        ("forbidden_to", []),
        ("forbidden_to", ["fresh_verifier"]),
        ("forbidden_to", ["fresh_implementer", "main"]),
        ("forbidden_to", "fresh_implementer"),
    ],
)
def test_current_plan_b_rejects_changed_top_level_role_visibility(
    tmp_path, monkeypatch, field, wrong_value
):
    freeze_path, _, record = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    record[field] = wrong_value
    freeze_path.write_text(json.dumps(record))
    with pytest.raises(ContractError, match="Plan-B role visibility mismatch"):
        _load_current_plan_b_freeze(freeze_path)


@pytest.mark.parametrize("field", ["visible_to", "forbidden_to"])
def test_current_plan_b_rejects_omitted_top_level_role_visibility(
    tmp_path, monkeypatch, field
):
    freeze_path, _, record = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    record.pop(field)
    freeze_path.write_text(json.dumps(record))
    with pytest.raises(ContractError, match="Plan-B role visibility mismatch"):
        _load_current_plan_b_freeze(freeze_path)


def test_current_plan_b_rejects_visibility_moved_under_wrapper(tmp_path, monkeypatch):
    freeze_path, _, record = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    record["role_visibility"] = {
        "visible_to": record.pop("visible_to"),
        "forbidden_to": record.pop("forbidden_to"),
    }
    freeze_path.write_text(json.dumps(record))
    with pytest.raises(ContractError, match="Plan-B role visibility mismatch"):
        _load_current_plan_b_freeze(freeze_path)


def test_current_plan_b_rejects_visibility_wrapper_even_with_top_level_fields(
    tmp_path, monkeypatch
):
    freeze_path, _, record = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    record["role_visibility"] = {
        "visible_to": list(record["visible_to"]),
        "forbidden_to": list(record["forbidden_to"]),
    }
    freeze_path.write_text(json.dumps(record))
    with pytest.raises(ContractError, match="Plan-B role visibility mismatch"):
        _load_current_plan_b_freeze(freeze_path)


def test_current_plan_b_rejects_changed_bound_plan_bytes(tmp_path, monkeypatch):
    freeze_path, plan, _ = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    plan.write_bytes(b"Q" * 257)
    with pytest.raises(ContractError, match="Plan-B frozen plan bytes mismatch"):
        _load_current_plan_b_freeze(freeze_path)


def test_current_plan_b_rejects_changed_bound_plan_mode(tmp_path, monkeypatch):
    freeze_path, plan, _ = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    plan.chmod(0o644)
    with pytest.raises(ContractError, match="Plan-B frozen plan bytes mismatch"):
        _load_current_plan_b_freeze(freeze_path)


def test_current_plan_b_rejects_changed_freeze_record_identity(tmp_path, monkeypatch):
    freeze_path, _, _ = _synthetic_current_plan_b_freeze(tmp_path, monkeypatch)
    accepted_hash = contract_module.sha256_file

    def changed_freeze_hash(path):
        if Path(path) == freeze_path:
            return "0" * 64
        return accepted_hash(path)

    monkeypatch.setattr(contract_module, "sha256_file", changed_freeze_hash)
    with pytest.raises(ContractError, match="Plan-B freeze-record SHA-256 mismatch"):
        _load_current_plan_b_freeze(freeze_path)


def test_successor_builder_is_production_admitted_and_binds_a46_5_fields():
    source = Path(contract_module.__file__).read_text(encoding="utf-8")
    assert "@_production_admitted\ndef build_effective_lock(" in source
    builder = source[source.index("def build_effective_lock(") :]
    assert '"schema_version": 2' in builder
    assert '"lock_id": SUCCESSOR_LOCK_ID' in builder
    assert '"generation_id": SUCCESSOR_GENERATION_ID' in builder
    assert '"predecessor_lineage_binding": predecessor_binding' in builder
    assert '"resource_lineage_binding": build_resource_lineage_binding(' in builder
    assert '"successor_entry_preconditions": _successor_entry_preconditions()' in builder
    assert '"audit_checks": list(SUCCESSOR_AUDIT_CHECKS)' in builder


def test_a46_5_authority_parent_and_g2_predecessor_lock_commit_are_exact():
    contract = load_contract()
    predecessor = contract["g2_predecessor_capsule_lineage"][
        "seal_json_schema"
    ]["properties"]["predecessor_lock"]["const"]
    assert contract_module.PHASE1_SEAL_PARENT == (
        "d9e52829d39268b52a30dea9ad1ad985731fdbb3"
    )
    assert contract_module.PREDECESSOR_EFFECTIVE_LOCK_COMMIT == predecessor["commit"]
    assert predecessor["commit"] == "d9e52829d39268b52a30dea9ad1ad985731fdbb3"


def test_prelabel_absence_does_not_inspect_main_owned_lock(monkeypatch):
    class PoisonLockPath:
        def exists(self):
            raise AssertionError("implementer touched the Main-owned lock path")

    runner = _load_runner_module()
    monkeypatch.setattr(runner, "DEFAULT_LOCK_PATH", PoisonLockPath())
    runner._assert_prelabel_absence()


@pytest.mark.parametrize("invalid", [True, 8, 0, -1, 9.0, "15", None])
def test_repair_provenance_floor_and_type_fail_closed(invalid):
    with pytest.raises(ContractError, match="integer at least 9"):
        _governance_binding(invalid)


@pytest.mark.parametrize("used", [9, 15, 1000])
def test_repair_provenance_is_uncapped_and_not_a_stop_gate(used):
    governance = _governance_binding(used)
    assert governance["repair_rounds_used"] == used
    assert governance["repair_rounds_stop_cap"] is None
    assert governance["repair_count_is_stop_gate"] is False
    assert "repair_rounds_maximum" not in governance


def test_effective_lock_schema_rejects_old_repair_cap_shape():
    schema = load_contract()["implementation_binding_schema"][
        "effective_lock_json_schema"
    ]["properties"]["governance_binding"]
    validator = jsonschema.Draft7Validator(schema)
    assert not list(validator.iter_errors(_governance_binding(9)))
    assert not list(validator.iter_errors(_governance_binding(1000)))
    for mutator in (
        lambda value: value.update({"repair_rounds_used": 8}),
        lambda value: value.update({"repair_rounds_stop_cap": 15}),
        lambda value: value.update({"repair_count_is_stop_gate": True}),
        lambda value: value.update({"repair_rounds_maximum": 15}),
    ):
        invalid = _governance_binding(15)
        mutator(invalid)
        assert list(validator.iter_errors(invalid))


def _emitted_worker_plain():
    tree = ast.parse(mapping_worker_code())
    selected = [
        node
        for node in tree.body
        if (
            isinstance(node, ast.Import)
            and any(alias.name in ("inspect", "math") for alias in node.names)
        )
        or isinstance(node, ast.FunctionDef)
        and node.name == "plain"
    ]
    namespace = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "<worker-plain>", "exec"), namespace)
    return namespace["plain"]


def _emitted_worker_failure_emitter():
    tree = ast.parse(mapping_worker_code())
    selected = [
        node
        for node in tree.body
        if (
            isinstance(node, ast.Import)
            and any(alias.name in {"hashlib", "json", "sys"} for alias in node.names)
        )
        or isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id in {"FAILURE_MARKER", "FAILURE_RETURN_CODE"}
            for target in node.targets
        )
        or isinstance(node, ast.FunctionDef)
        and node.name in {"canonical_digest", "emit_codegen_failure"}
    ]
    namespace = {}
    exec(
        compile(
            ast.Module(body=selected, type_ignores=[]),
            "<worker-failure-emitter>",
            "exec",
        ),
        namespace,
    )
    return namespace["emit_codegen_failure"]


def test_emitted_worker_plain_normalizes_actual_pinned_state_methods():
    from Tensile.Activation import ActivationType
    from Tensile.Common.DataType import DataType

    plain = _emitted_worker_plain()
    problem_type = {
        "ProblemType": {
            "DataType": DataType(0),
            "ActivationType": ActivationType("none"),
        }
    }
    assert plain(problem_type) == {
        "ProblemType": {"ActivationType": "None", "DataType": "Float"}
    }


def test_emitted_worker_failure_marker_matches_runner_parser(capsys):
    config = {"synthetic": True}
    kernel_failures = [
        {
            "kernel_index": 0,
            "kernel_name": "synthetic-kernel",
            "result_error_code": -2,
            "overflowed_resources": 5,
        }
    ]
    with pytest.raises(SystemExit) as stopped:
        _emitted_worker_failure_emitter()(0, config, kernel_failures)
    assert stopped.value.code == MAPPING_FAILURE_RETURN_CODE
    runner = _load_runner_module()
    failure = runner._parse_mapping_failure_marker(
        capsys.readouterr().out.encode("utf-8"), [config]
    )
    assert failure["category"] == "code_generation_nonzero"
    assert failure["error_class"] == "KernelWriterAssembly_overflowedResources"
    assert failure["error_code"] == 5
    assert failure["kernel_failures"] == kernel_failures


@pytest.mark.parametrize(
    ("result_error_code", "overflowed_resources"), [(-1, 5), (-2, 4)]
)
def test_emitted_worker_rejects_nonallowlisted_nested_failures(
    result_error_code, overflowed_resources
):
    with pytest.raises(RuntimeError, match="nonallowlisted"):
        _emitted_worker_failure_emitter()(
            0,
            {"synthetic": True},
            [
                {
                    "kernel_index": 0,
                    "kernel_name": "synthetic-kernel",
                    "result_error_code": result_error_code,
                    "overflowed_resources": overflowed_resources,
                }
            ],
        )


def test_emitted_worker_plain_preserves_noncallable_state_and_primitives():
    plain = _emitted_worker_plain()

    class PropertyState:
        state = {"finite": 1.25, "tuple": (True, None)}

    assert plain(PropertyState()) == {"finite": 1.25, "tuple": [True, None]}


@pytest.mark.parametrize(
    "factory",
    [
        lambda: type("GenericCallable", (), {"state": lambda: "bad"})(),
        lambda: type("RequiredArgument", (), {"state": lambda self, value: value})(),
        lambda: type(
            "RaisingState",
            (),
            {"state": lambda self: (_ for _ in ()).throw(RuntimeError("boom"))},
        )(),
        lambda: type("UnsupportedReturn", (), {"state": lambda self: object()})(),
        lambda: type("NonFiniteReturn", (), {"state": lambda self: float("inf")})(),
    ],
)
def test_emitted_worker_plain_fails_closed_on_adversarial_state(factory):
    with pytest.raises((TypeError, RuntimeError)):
        _emitted_worker_plain()(factory())


def test_emitted_worker_plain_rejects_wrong_foreign_class_and_static_bindings():
    plain = _emitted_worker_plain()

    class Other:
        def state(self):
            return "foreign"

        def wrong(self):
            return "wrong"

    other = Other()

    class Foreign:
        state = other.state

    class WrongName:
        state = other.wrong

    class ClassBound:
        @classmethod
        def state(cls):
            return "class"

    class StaticBound:
        @staticmethod
        def state():
            return "static"

    for value in (Foreign(), WrongName(), ClassBound(), StaticBound()):
        with pytest.raises(TypeError):
            plain(value)


def test_mapping_implementation_drift_is_checked_before_worker_creation():
    runner = _load_runner_module()
    source = (PROTOCOL_ROOT / "run_s10r3_entry.py").read_text(encoding="utf-8")
    command = source[
        source.index("def mapping_command") : source.index("def _native_fixture_input")
    ]
    assert command.index("_require_formal(") < command.index("_run_mapping_worker(")
    assert any(path.endswith("/mapping.py") for path in IMPLEMENTATION_PATHS)
    assert runner._run_mapping_worker.__name__ == "_run_mapping_worker"


def test_nonzero_mapping_worker_creates_no_result_or_later_transition(
    a46_3_synthetic_root, monkeypatch
):
    runner = _load_runner_module()
    output = _synthetic_mapping_pass_root(
        runner, a46_3_synthetic_root / "nonzero-worker", monkeypatch
    )
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: types.SimpleNamespace(
            returncode=17, stdout=b"", stderr=b"synthetic failure"
        ),
    )
    with pytest.raises(runner.RunnerError, match="failed closed"):
        runner._run_mapping_worker("A", [{"synthetic": True}], output)
    assert sorted(path.name for path in output.iterdir()) == [
        "attempt-01",
        "request.json",
    ]
    assert sorted(path.name for path in (output / "attempt-01").iterdir()) == [
        "completion.json",
        "worker.stderr",
        "worker.stdout",
    ]
    forbidden = (
        "mapping-pass.json",
        "s10r3-mapping-corpus.json",
        "s10r3-sentinel-conformance.json",
        "s10r3-smoke-correctness.json",
        "s10r3-noise-pilot.json",
        "s10r3-decision.json",
    )
    assert all(not (output / name).exists() for name in forbidden)


def _mapping_failure_stdout(config, *, kernel_name="synthetic-kernel"):
    body = {
        "failure_kind": "required_mapping_code_generation",
        "category": "code_generation_nonzero",
        "error_class": "KernelWriterAssembly_overflowedResources",
        "error_code": 5,
        "slot": 0,
        "config_hash": canonical_sha256(config),
        "kernel_failures": [
            {
                "kernel_index": 0,
                "kernel_name": kernel_name,
                "result_error_code": -2,
                "overflowed_resources": 5,
            }
        ],
    }
    failure = {**body, "failure_signature": canonical_sha256(body)}
    return (
        MAPPING_FAILURE_MARKER
        + json.dumps(
            failure,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _synthetic_mapping_pass_root(runner, root, monkeypatch):
    synthetic_repository = root / "synthetic-repository"
    monkeypatch.setattr(runner, "ROOT", synthetic_repository)
    build_root = synthetic_repository / (
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/"
        "artifacts/prelabel-build"
    )
    monkeypatch.setattr(runner, "PRELABEL_BUILD_ROOT", build_root)
    formal_mapping_root = synthetic_repository / (
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/"
        "artifacts/formal-mapping"
    )
    monkeypatch.setattr(runner, "FORMAL_MAPPING_ROOT", formal_mapping_root)
    provenance = build_root / (
        "pinned-source/projects/hipblaslt/tensilelite/Tensile/Contractions.py"
    )
    provenance.parent.mkdir(parents=True)
    provenance.write_bytes(b"synthetic pinned provenance\n")
    return formal_mapping_root / "pass-a"


def test_reproducible_mapping_worker_failure_is_exactly_two_isolated_attempts(
    a46_3_synthetic_root, monkeypatch
):
    runner = _load_runner_module()
    output = _synthetic_mapping_pass_root(
        runner, a46_3_synthetic_root / "reproducible-mapping-failure", monkeypatch
    )
    configs = [{"synthetic": index} for index in range(10)]
    config = configs[0]
    calls = []
    real_subprocess_run = subprocess.run

    def fail_codegen(*args, **kwargs):
        if args and args[0] and args[0][0] == "git":
            return real_subprocess_run(*args, **kwargs)
        cwd = Path(kwargs["cwd"])
        calls.append(cwd)
        (cwd / "a.out").write_bytes(f"attempt-{len(calls)}".encode("ascii"))
        return types.SimpleNamespace(
            returncode=MAPPING_FAILURE_RETURN_CODE,
            stdout=_mapping_failure_stdout(config),
            stderr=b"",
        )

    monkeypatch.setattr(runner.subprocess, "run", fail_codegen)
    monkeypatch.setattr(
        runner.resource,
        "getrusage",
        lambda *args: types.SimpleNamespace(
            ru_utime=1.0,
            ru_stime=1.0,
            ru_maxrss=-1,
        ),
    )
    document = runner._run_mapping_worker("A", configs, output)
    assert document["document_kind"] == "mapping_failure_batch"
    assert document["payload"]["complete"] is True
    assert document["payload"]["reproducible"] is True
    assert document["payload"]["attempt_count"] == 2
    assert calls == [output / "attempt-01", output / "attempt-02"]
    assert (output / "attempt-01/a.out").read_bytes() == b"attempt-1"
    assert (output / "attempt-02/a.out").read_bytes() == b"attempt-2"
    for attempt in (1, 2):
        completion = runner.strict_load_json(
            output / f"attempt-{attempt:02d}/completion.json"
        )
        assert completion["payload"]["maximum_child_rss_kib"] == 0
    assert not (output / "attempt-03").exists()

    def reject_third_attempt(*args, **kwargs):
        if args and args[0] and args[0][0] == "git":
            return real_subprocess_run(*args, **kwargs)
        raise AssertionError("a third mapping attempt was started")

    monkeypatch.setattr(runner.subprocess, "run", reject_third_attempt)
    assert runner._run_mapping_worker("A", configs, output) == document
    assert not (output / "attempt-03").exists()


def test_mapping_worker_failure_signature_mismatch_stops_without_third_attempt(
    a46_3_synthetic_root, monkeypatch
):
    runner = _load_runner_module()
    output = _synthetic_mapping_pass_root(
        runner, a46_3_synthetic_root / "mismatched-mapping-failure", monkeypatch
    )
    configs = [{"synthetic": index} for index in range(10)]
    config = configs[0]
    calls = 0

    def fail_differently(*args, **kwargs):
        nonlocal calls
        del args, kwargs
        calls += 1
        return types.SimpleNamespace(
            returncode=MAPPING_FAILURE_RETURN_CODE,
            stdout=_mapping_failure_stdout(
                config, kernel_name=f"synthetic-kernel-{calls}"
            ),
            stderr=b"",
        )

    monkeypatch.setattr(runner.subprocess, "run", fail_differently)
    with pytest.raises(runner.RunnerError, match="not reproducible"):
        runner._run_mapping_worker("A", configs, output)
    assert calls == 2
    assert not (output / "attempt-03").exists()
    assert not (output / "mapping-failure.json").exists()


def test_mapping_worker_failure_then_success_is_not_a_replacement(
    a46_3_synthetic_root, monkeypatch
):
    runner = _load_runner_module()
    output = _synthetic_mapping_pass_root(
        runner, a46_3_synthetic_root / "failure-then-success", monkeypatch
    )
    configs = [{"synthetic": index} for index in range(10)]
    config = configs[0]
    calls = 0

    def fail_then_succeed(*args, **kwargs):
        nonlocal calls
        del args, kwargs
        calls += 1
        if calls == 1:
            return types.SimpleNamespace(
                returncode=MAPPING_FAILURE_RETURN_CODE,
                stdout=_mapping_failure_stdout(config),
                stderr=b"",
            )
        if calls == 2:
            return types.SimpleNamespace(returncode=0, stdout=b"", stderr=b"")
        raise AssertionError("a third mapping attempt was started")

    monkeypatch.setattr(runner.subprocess, "run", fail_then_succeed)
    with pytest.raises(runner.RunnerError, match="outcomes are not reproducible"):
        runner._run_mapping_worker("A", configs, output)
    assert calls == 2
    assert not (output / "attempt-03").exists()
    assert not (output / "mapping-pass.json").exists()
    assert not (output / "mapping-failure.json").exists()


@pytest.mark.parametrize(
    "tamper",
    [
        "category",
        "error_class",
        "error_code",
        "config_hash",
        "result_error_code",
        "overflowed_resources",
        "unknown",
        "signature",
    ],
)
def test_mapping_worker_failure_marker_tampering_fails_closed(tamper):
    runner = _load_runner_module()
    config = {"synthetic": True}
    marker = _mapping_failure_stdout(config).decode("utf-8").strip()
    failure = json.loads(marker[len(MAPPING_FAILURE_MARKER) :])
    if tamper == "category":
        failure["category"] = "api_exception"
    elif tamper == "error_class":
        failure["error_class"] = "Other"
    elif tamper == "error_code":
        failure["error_code"] = 4
    elif tamper == "config_hash":
        failure["config_hash"] = "0" * 64
    elif tamper in {"result_error_code", "overflowed_resources"}:
        failure["kernel_failures"][0][tamper] = 0
    elif tamper == "unknown":
        failure["unknown"] = True
    else:
        failure["failure_signature"] = "0" * 64
    stdout = (
        MAPPING_FAILURE_MARKER
        + json.dumps(failure, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    with pytest.raises(runner.RunnerError):
        runner._parse_mapping_failure_marker(stdout, [config])


def test_mapping_command_terminalizes_complete_reproducible_failure(
    a46_3_synthetic_root, monkeypatch
):
    runner = _load_runner_module()
    formal_mapping = a46_3_synthetic_root / "formal-mapping"
    mapping_path = a46_3_synthetic_root / "mapping-corpus.json"
    configs = [{"synthetic": index} for index in range(10)]
    selection = {
        "document_digest": "1" * 64,
        "payload": {
            "status": "selected",
            "k": 10,
            "final_witnesses": [{"config": config} for config in configs],
        },
    }
    failure_batch = {
        "document_kind": "mapping_failure_batch",
        "document_digest": "2" * 64,
        "payload": {
            "complete": True,
            "reproducible": True,
            "attempt_count": 2,
        },
    }
    lock = {"runtime_binding": {"toolchain": [{"id": "python"}]}}
    written = {}
    decision_calls = []

    monkeypatch.setattr(runner, "FORMAL_MAPPING_ROOT", formal_mapping)
    monkeypatch.setattr(runner, "MAPPING_PATH", mapping_path)
    monkeypatch.setattr(runner, "_require_formal", lambda path: lock)
    monkeypatch.setattr(runner, "_assert_no_terminal", lambda: None)
    monkeypatch.setattr(runner, "_selection_document", lambda: selection)
    monkeypatch.setattr(
        runner,
        "_run_mapping_worker",
        lambda pass_id, selected, output: failure_batch,
    )

    def formal_document(**kwargs):
        document = {
            "document_kind": kwargs["kind"],
            "payload": dict(kwargs["payload"]),
        }
        return {**document, "document_digest": canonical_sha256(document)}

    monkeypatch.setattr(runner, "_formal_document", formal_document)
    monkeypatch.setattr(
        runner,
        "_write_or_match_json",
        lambda path, document: written.setdefault(Path(path), document),
    )

    def terminal_decision(**kwargs):
        decision_calls.append(kwargs)
        return {"document_digest": "3" * 64}

    monkeypatch.setattr(runner, "_terminal_decision", terminal_decision)
    result = runner.mapping_command.__wrapped__("A", a46_3_synthetic_root / "lock")
    assert result == {
        "checkpoint_id": "S10R3",
        "status": "TERMINAL_NEGATIVE_MAPPING",
        "decision_digest": "3" * 64,
    }
    corpus = written[mapping_path]
    assert corpus["payload"]["status"] == "FT-BLOCKED-MAPPING"
    assert corpus["payload"]["failed_pass"] == "A"
    assert corpus["payload"]["pass_b_activated"] is False
    assert corpus["payload"]["toolchain_binding"] == lock["runtime_binding"][
        "toolchain"
    ]
    assert decision_calls[0]["scientific_outcome"] == "negative"
    assert decision_calls[0]["criterion"] == "S1_ENTRY_BLOCKED"
    assert decision_calls[0]["failure_id"] == "FT-BLOCKED-MAPPING"
    assert decision_calls[0]["edge"] is None
    assert not (formal_mapping / "pass-b").exists()


def test_reproduction_reconstructs_two_raw_mapping_failure_attempts(
    a46_3_synthetic_root, monkeypatch
):
    runner = _load_runner_module()
    pass_root = _synthetic_mapping_pass_root(
        runner, a46_3_synthetic_root / "raw-reproduction", monkeypatch
    )
    formal_mapping = pass_root.parent
    pass_root.mkdir(parents=True)
    configs = [{"synthetic": index} for index in range(10)]
    config_hashes = [canonical_sha256(config) for config in configs]
    stdout = _mapping_failure_stdout(configs[0])
    failure = runner._parse_mapping_failure_marker(stdout, configs)
    attempts = []
    completions = []
    for attempt_number in (1, 2):
        attempt_root = pass_root / f"attempt-{attempt_number:02d}"
        attempt_root.mkdir()
        stdout_path = attempt_root / "worker.stdout"
        stderr_path = attempt_root / "worker.stderr"
        artifact_path = attempt_root / "a.out"
        stdout_path.write_bytes(stdout)
        stderr_path.write_bytes(b"")
        artifact_path.write_bytes(f"artifact-{attempt_number}".encode("ascii"))
        completion_payload = {
            "attempt": attempt_number,
            "returncode": MAPPING_FAILURE_RETURN_CODE,
            "cwd_path": str(attempt_root.relative_to(runner.ROOT)),
            "stdout_path": str(stdout_path.relative_to(runner.ROOT)),
            "stdout_sha256": sha256_file(stdout_path),
            "stderr_path": str(stderr_path.relative_to(runner.ROOT)),
            "stderr_sha256": sha256_file(stderr_path),
            "worker_artifacts": [runner._mapping_file_record(artifact_path)],
            "wall_s": 1.0,
            "cpu_s": 1.0,
            "maximum_child_rss_kib": 1,
        }
        completion = runner._raw_document(
            "mapping_worker_completion", completion_payload
        )
        completions.append(completion)
        (attempt_root / "completion.json").write_text(
            json.dumps(completion, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        attempts.append(
            {
                "completion_digest": completion["document_digest"],
                **{
                    key: completion_payload[key]
                    for key in (
                        "attempt",
                        "returncode",
                        "cwd_path",
                        "stdout_path",
                        "stdout_sha256",
                        "stderr_path",
                        "stderr_sha256",
                        "worker_artifacts",
                    )
                },
            }
        )
    provenance_path = (
        runner.PRELABEL_BUILD_ROOT
        / "pinned-source/projects/hipblaslt/tensilelite/Tensile/Contractions.py"
    )
    request = {
        "schema_version": 1,
        "pass_id": "A",
        "yaml_path": str(runner.ACTUAL_YAML),
        "yaml_sha256": sha256_file(runner.ACTUAL_YAML),
        "compiler": "/opt/rocm/bin/amdclang++",
        "configs": configs,
        "config_hashes": config_hashes,
        "provenance_source_path": str(provenance_path),
        "provenance_record_path": str(provenance_path.relative_to(runner.ROOT)),
        "provenance_source_sha256": sha256_file(provenance_path),
        "worker_source_sha256": hashlib.sha256(
            mapping_worker_code().encode("utf-8")
        ).hexdigest(),
    }
    request_path = pass_root / "request.json"
    request_path.write_text(
        json.dumps(request, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    worker_binding = {
        key: request[key]
        for key in (
            "worker_source_sha256",
            "yaml_path",
            "yaml_sha256",
            "provenance_source_path",
            "provenance_source_sha256",
            "compiler",
        )
    }
    batch = {
        "status": "FT-BLOCKED-MAPPING",
        "pass_id": "A",
        "k": 10,
        "complete": True,
        "reproducible": True,
        "attempt_count": 2,
        "request_path": str(request_path.relative_to(runner.ROOT)),
        "request_sha256": sha256_file(request_path),
        "config_hashes": config_hashes,
        "failure": failure,
        "attempts": attempts,
        "worker_binding": worker_binding,
    }
    failure_document = runner._raw_document("mapping_failure_batch", batch)
    validate_mapping_failure_signature(failure, config_hashes=config_hashes)
    for completion in completions:
        validate_mapping_worker_completion(
            completion, repository_root=runner.ROOT, require_files=True
        )
    validate_mapping_failure_batch(
        failure_document,
        request=request,
        completions=completions,
        repository_root=runner.ROOT,
        require_files=True,
    )
    (pass_root / "mapping-failure.json").write_text(
        json.dumps(failure_document, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    toolchain = [
        {"id": "python", "path": "/opt/venv/bin/python3", "sha256": "1" * 64},
        {"id": "pytest", "path": "/opt/venv/bin/pytest", "sha256": "2" * 64},
        {
            "id": "cxx_compiler",
            "path": "/opt/rocm/bin/amdclang++",
            "sha256": "3" * 64,
        },
        {
            "id": "rocm_toolchain",
            "path": "/opt/rocm/bin/hipcc",
            "sha256": "4" * 64,
        },
    ]
    mapping = {
        "document_kind": "mapping_corpus",
        "document_digest": "5" * 64,
        "upstream_identities": {
            "mapping_failure_batch": failure_document["document_digest"]
        },
        "payload": {
            "status": "FT-BLOCKED-MAPPING",
            "failure": "reproducible_required_mapping_code_generation",
            "k": 10,
            "selection": {
                "k": 10,
                "final_witnesses": [{"config": config} for config in configs],
            },
            "failed_pass": "A",
            "failure_batch": batch,
            "toolchain_binding": toolchain,
            "pass_b_activated": False,
        },
    }
    decision = {
        "document_digest": "6" * 64,
        "payload": {
            "scientific_outcome": "negative",
            "criterion": "S1_ENTRY_BLOCKED",
            "failure_id": "FT-BLOCKED-MAPPING",
            "edge": None,
        },
    }
    lock = {"runtime_binding": {"toolchain": toolchain}}

    def load_formal(path, *, kind, lock_path, lock):
        del path, lock_path, lock
        return decision if kind == "decision" else mapping

    monkeypatch.setattr(runner, "FORMAL_MAPPING_ROOT", formal_mapping)
    monkeypatch.setattr(runner, "_load_formal_document", load_formal)
    reconstructed = runner._reconstruct_reached_outcome(
        a46_3_synthetic_root / "lock", lock
    )
    required_raw_paths = set(reconstructed.pop("_required_raw_child_paths"))
    assert batch["request_path"] in required_raw_paths
    assert str((pass_root / "mapping-failure.json").relative_to(runner.ROOT)) in required_raw_paths
    for attempt in attempts:
        assert attempt["stdout_path"] in required_raw_paths
        assert attempt["stderr_path"] in required_raw_paths
        assert attempt["worker_artifacts"][0]["path"] in required_raw_paths
    assert reconstructed["scientific_outcome"] == "negative"
    assert reconstructed["failure_id"] == "FT-BLOCKED-MAPPING"
    assert reconstructed["edge"] is None


@pytest.mark.parametrize(
    "counterfeit",
    [None, "traversal", "absolute", "hash", "symlink_parent", "stdout_symlink"],
)
def test_mapping_completion_worker_artifact_is_strictly_contained_and_raw_bound(
    a46_3_synthetic_root, monkeypatch, counterfeit
):
    runner = _load_runner_module()
    pass_root = _synthetic_mapping_pass_root(
        runner,
        a46_3_synthetic_root / f"artifact-containment-{counterfeit}",
        monkeypatch,
    )
    attempt_root = pass_root / "attempt-01"
    attempt_root.mkdir(parents=True)
    stdout_path = attempt_root / "worker.stdout"
    stderr_path = attempt_root / "worker.stderr"
    artifact_path = attempt_root / "worker.bin"
    stdout_path.write_bytes(b"stdout")
    stderr_path.write_bytes(b"stderr")
    artifact_path.write_bytes(b"non-empty-worker-artifact")
    record = runner._mapping_file_record(artifact_path)
    if counterfeit == "traversal":
        record["path"] = (
            f"{attempt_root.relative_to(runner.ROOT).as_posix()}/../../escape.bin"
        )
    elif counterfeit == "absolute":
        record["path"] = artifact_path.as_posix()
    elif counterfeit == "hash":
        record["sha256"] = "0" * 64
    elif counterfeit == "symlink_parent":
        target = attempt_root / "target"
        target.mkdir()
        (target / "worker.bin").write_bytes(b"non-empty-worker-artifact")
        linked_parent = attempt_root / "linked"
        linked_parent.symlink_to(target, target_is_directory=True)
        record = runner._mapping_file_record(target / "worker.bin")
        record["path"] = (
            f"{attempt_root.relative_to(runner.ROOT).as_posix()}/linked/worker.bin"
        )
    elif counterfeit == "stdout_symlink":
        stdout_target = attempt_root / "stdout-target"
        stdout_target.write_bytes(stdout_path.read_bytes())
        stdout_path.unlink()
        stdout_path.symlink_to(stdout_target)
    payload = {
        "attempt": 1,
        "returncode": MAPPING_FAILURE_RETURN_CODE,
        "cwd_path": attempt_root.relative_to(runner.ROOT).as_posix(),
        "stdout_path": stdout_path.relative_to(runner.ROOT).as_posix(),
        "stdout_sha256": sha256_file(stdout_path),
        "stderr_path": stderr_path.relative_to(runner.ROOT).as_posix(),
        "stderr_sha256": sha256_file(stderr_path),
        "worker_artifacts": [record],
        "wall_s": 1.0,
        "cpu_s": 1.0,
        "maximum_child_rss_kib": 1,
    }
    completion = runner._raw_document("mapping_worker_completion", payload)
    if counterfeit is None:
        validate_mapping_worker_completion(
            completion, repository_root=runner.ROOT, require_files=True
        )
    else:
        with pytest.raises(ContractError):
            validate_mapping_worker_completion(
                completion, repository_root=runner.ROOT, require_files=True
            )


@pytest.mark.parametrize(
    "symlink_kind", ["pass_root", "attempt_root", "request", "completion"]
)
def test_mapping_worker_rejects_symlink_state_roots_before_subprocess(
    a46_3_synthetic_root, monkeypatch, symlink_kind
):
    runner = _load_runner_module()
    pass_root = _synthetic_mapping_pass_root(
        runner,
        a46_3_synthetic_root / f"mapping-{symlink_kind}",
        monkeypatch,
    )
    pass_root.parent.mkdir(parents=True)
    if symlink_kind == "pass_root":
        target = pass_root.parent / "pass-target"
        target.mkdir()
        pass_root.symlink_to(target, target_is_directory=True)
    else:
        pass_root.mkdir()
        if symlink_kind == "attempt_root":
            target = pass_root.parent / "attempt-target"
            target.mkdir()
            (pass_root / "attempt-01").symlink_to(
                target, target_is_directory=True
            )
        elif symlink_kind == "request":
            target = pass_root.parent / "request-target.json"
            target.write_text("{}\n", encoding="utf-8")
            (pass_root / "request.json").symlink_to(target)
        else:
            attempt_root = pass_root / "attempt-01"
            attempt_root.mkdir()
            target = pass_root.parent / "completion-target.json"
            target.write_text("{}\n", encoding="utf-8")
            (attempt_root / "completion.json").symlink_to(target)
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("mapping subprocess started after symlink counterfeit")
        ),
    )
    with pytest.raises(runner.RunnerError, match="symlink"):
        runner._run_mapping_worker("A", [{"synthetic": True}], pass_root)


def test_raw_mapping_document_adoption_rejects_symlink(tmp_path):
    runner = _load_runner_module()
    target = tmp_path / "target.json"
    target.write_text("{}\n", encoding="utf-8")
    linked = tmp_path / "mapping-failure.json"
    linked.symlink_to(target)
    with pytest.raises(runner.RunnerError, match="symlink"):
        runner._load_raw_document(linked, "mapping_failure_batch")
    with pytest.raises(runner.RunnerError, match="symlink"):
        runner._write_or_match_json(linked, {})


@pytest.fixture
def a46_3_synthetic_root():
    parent = ROOT / PRELABEL_ROOTS[2]
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="a46-3-", dir=parent) as directory:
        yield Path(directory)


def test_stable_admission_lock_is_exclusive_empty_and_same_inode(
    a46_3_synthetic_root,
):
    path = a46_3_synthetic_root / "admission.lock"
    created = create_stable_admission_lock(path)
    assert created["resolved_path"] == path.resolve().as_posix()
    assert created["mode"] == "0600"
    assert created["size_bytes"] == 0
    assert created["nlink"] == 1
    with pytest.raises(ContractError, match="exclusive admission lock creation failed"):
        create_stable_admission_lock(path)
    with stable_admission_lock(path, expected_identity=created) as (_, observed):
        assert observed == created


def test_production_admission_identity_is_canonical_across_runtime_aliases(
    a46_3_synthetic_root, monkeypatch
):
    synthetic_path = a46_3_synthetic_root / "production-admission.lock"
    create_stable_admission_lock(synthetic_path)
    container_alias = ROOT / PRODUCTION_ADMISSION_LOCK_PATH
    host_alias = Path(PRODUCTION_ADMISSION_RESOLVED_PATH)
    observed = []

    def redirect(path, *, allow_production=False):
        observed.append((Path(path), allow_production))
        return synthetic_path, PRODUCTION_ADMISSION_LOCK_PATH

    monkeypatch.setattr(contract_module, "_authorized_transition_path", redirect)
    descriptor = os.open(
        synthetic_path, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        container_identity = admission_lock_identity(
            container_alias, descriptor, allow_production=True
        )
        host_identity = admission_lock_identity(
            host_alias, descriptor, allow_production=True
        )
        assert container_identity == host_identity
        assert (
            container_identity["resolved_path"]
            == PRODUCTION_ADMISSION_RESOLVED_PATH
        )
        assert container_identity["identity_digest"] == contract_module._identity_digest(
            container_identity
        )
        assert observed == [(container_alias, True), (host_alias, True)]

        validate_transition_journal(
            new_transition_journal(container_identity), production_identity=True
        )

        wrong_identity = copy.deepcopy(container_identity)
        wrong_identity["resolved_path"] = container_alias.as_posix()
        wrong_identity["identity_digest"] = contract_module._identity_digest(
            wrong_identity
        )
        with pytest.raises(ContractError, match="stable admission lock identity changed"):
            admission_lock_identity(
                container_alias,
                descriptor,
                allow_production=True,
                expected_identity=wrong_identity,
            )

        wrong_journal = new_transition_journal(container_identity)
        wrong_journal["admission_lock_identity"] = wrong_identity
        wrong_journal["events"][0]["admission_lock_identity_digest"] = wrong_identity[
            "identity_digest"
        ]
        wrong_journal["events"][0]["event_digest"] = contract_module._event_digest(
            wrong_journal["events"][0]
        )
        wrong_journal["document_digest"] = contract_module._self_digest(
            wrong_journal, "document_digest"
        )
        with pytest.raises(ContractError, match="transition journal schema failed"):
            validate_transition_journal(wrong_journal, production_identity=True)

        def redirect_wrong_production_path(path, *, allow_production=False):
            return synthetic_path, PRODUCTION_TRANSITION_PATHS[1]

        monkeypatch.setattr(
            contract_module,
            "_authorized_transition_path",
            redirect_wrong_production_path,
        )
        with pytest.raises(ContractError, match="production admission identity path mismatch"):
            admission_lock_identity(
                container_alias, descriptor, allow_production=True
            )
    finally:
        os.close(descriptor)


def test_stable_admission_lock_detects_replaced_inode(a46_3_synthetic_root):
    path = a46_3_synthetic_root / "admission.lock"
    create_stable_admission_lock(path)
    replacement = a46_3_synthetic_root / "replacement.lock"
    replacement.touch(mode=0o600)
    replacement.chmod(0o600)
    with pytest.raises(ContractError, match="inode identity mismatch"):
        with stable_admission_lock(path):
            os.replace(replacement, path)


def test_formal_entrypoints_acquire_admission_before_scope_and_recheck():
    source = (PROTOCOL_ROOT / "run_s10r3_entry.py").read_text(encoding="utf-8")
    serialized = source[
        source.index("def _serialized_formal") : source.index("def _assert_no_terminal")
    ]
    assert serialized.index("stable_admission_lock(") < serialized.index(
        "_require_formal("
    )
    assert serialized.index("_require_formal(") < serialized.index("_FormalWriter(")
    assert serialized.index("_FormalWriter(") < serialized.index(
        "admission_lock_identity("
    )
    for command in (
        "support_discovery_command",
        "support_classification_command",
        "select_bounded_cover_command",
        "mapping_command",
        "native_conformance_command",
        "gpu_environment_command",
        "correctness_command",
        "noise_command",
        "decision_command",
        "reproduction_command",
    ):
        assert "@_serialized_formal(" in source[: source.index(f"def {command}")]
    verifier = source[
        source.index("def verify_effective_lock_command") : source.index("def _parser")
    ]
    assert verifier.index("stable_admission_lock(") < verifier.index(
        "strict_load_json("
    )


def test_transition_api_refuses_paths_outside_prelabel_roots():
    forbidden_path = DEFAULT_CONTRACT_PATH / "forbidden.lock"
    with pytest.raises(ContractError, match="outside prelabel roots"):
        create_stable_admission_lock(forbidden_path)


def test_production_transition_authorization_is_exact_and_filesystem_free(
    monkeypatch,
):
    expected = (
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/gates/"
        "s10r3/execution-transition.lock",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/gates/"
        "s10r3/execution-transition-journal.json",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/gates/"
        "s10r3/execution-transition-journal.json.tmp",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
        "formal-cpu",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
        "formal-mapping",
        "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/"
        "s10r3-support-classification.json",
        "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/"
        "s10r3-stage1-bounded-cover-entry-lock.json",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
        "retired-predecessors/.staging-S10R3-A46.3-G1/formal-cpu",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
        "retired-predecessors/.staging-S10R3-A46.3-G1/formal-mapping",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
        "retired-predecessors/.staging-S10R3-A46.3-G1/"
        "s10r3-support-classification.json",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
        "retired-predecessors/.staging-S10R3-A46.3-G1/effective-lock.json",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
        "retired-predecessors/.staging-S10R3-A46.3-G1",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
        "retired-predecessors/.staging-S10R3-A46.3-G1/"
        "predecessor-manifest.json",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
        "retired-predecessors/.staging-S10R3-A46.3-G1/"
        ".predecessor-manifest.a46-4.tmp",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
        "retired-predecessors/"
        "lock-1cd089d3abe79d4918d965a2afa868421ec8d810644b8c7ede00f0ef05960301",
        "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/"
        "lineage/s10r3-predecessor-lock-1cd089d3.json",
    )
    assert PRODUCTION_TRANSITION_PATHS == expected
    assert len(set(PRODUCTION_TRANSITION_PATHS)) == 16

    def filesystem_access_forbidden(*_args, **_kwargs):
        raise AssertionError("production authorization performed filesystem access")

    for method in ("resolve", "stat", "lstat", "exists", "mkdir", "open"):
        monkeypatch.setattr(Path, method, filesystem_access_forbidden)

    for lexical in expected:
        assert _authorized_transition_path(
            lexical, allow_production=True
        ) == (ROOT / lexical, lexical)
        assert _authorized_transition_path(
            ROOT / lexical, allow_production=True
        ) == (ROOT / lexical, lexical)
        with pytest.raises(ContractError, match="Main-only"):
            _authorized_transition_path(lexical)

    derived = (
        expected[0] + ".bak",
        expected[1] + ".typo",
        expected[2] + "/child",
        expected[3] + "/child",
        expected[7] + "/child",
        expected[11] + "-typo",
        expected[12] + ".bak",
        expected[13] + ".bak",
        expected[14] + "/formal-cpu",
        expected[15] + ".bak",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/"
        "artifacts/retired-predecessors",
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/gates/"
        "s10r3/../s10r3/execution-transition.lock",
    )
    for lexical in derived:
        with pytest.raises(ContractError, match="exact production transition allowlist"):
            _authorized_transition_path(lexical, allow_production=True)


def test_production_noreplace_path_pair_can_be_safely_redirected(
    a46_3_synthetic_root, monkeypatch
):
    production_source = PRODUCTION_TRANSITION_PATHS[3]
    production_destination = PRODUCTION_TRANSITION_PATHS[7]
    synthetic_source = a46_3_synthetic_root / "source"
    synthetic_destination = a46_3_synthetic_root / "staging" / "formal-cpu"
    synthetic_destination.parent.mkdir()
    synthetic_source.write_bytes(b"payload")
    observed = []

    def redirect(path, *, allow_production=False):
        observed.append((Path(path), allow_production))
        redirected = {
            Path(production_source): synthetic_source,
            Path(production_destination): synthetic_destination,
        }
        return redirected[Path(path)], Path(path).as_posix()

    monkeypatch.setattr(contract_module, "_authorized_transition_path", redirect)
    rename_noreplace(
        production_source, production_destination, allow_production=True
    )
    assert observed == [
        (Path(production_source), True),
        (Path(production_destination), True),
    ]
    assert not synthetic_source.exists()
    assert synthetic_destination.read_bytes() == b"payload"


def test_true_noreplace_move_and_destination_collision(a46_3_synthetic_root):
    source = a46_3_synthetic_root / "source"
    destination = a46_3_synthetic_root / "destination"
    source.write_bytes(b"payload")
    rename_noreplace(source, destination)
    assert not source.exists() and destination.read_bytes() == b"payload"
    source.write_bytes(b"second")
    with pytest.raises(ContractError, match="destination already exists"):
        rename_noreplace(source, destination)
    assert source.read_bytes() == b"second"
    assert destination.read_bytes() == b"payload"


def test_noreplace_has_no_fallback_when_primitive_is_unavailable(
    a46_3_synthetic_root, monkeypatch
):
    source = a46_3_synthetic_root / "source"
    destination = a46_3_synthetic_root / "destination"
    source.write_bytes(b"payload")
    monkeypatch.setattr(
        contract_module,
        "_renameat2_noreplace",
        lambda *_: (_ for _ in ()).throw(ContractError("unavailable")),
    )
    with pytest.raises(ContractError, match="unavailable"):
        rename_noreplace(source, destination)
    assert source.exists() and not destination.exists()


def test_component_inventory_is_root_excluded_utf8_sorted_and_canonical(
    a46_3_synthetic_root,
):
    component = a46_3_synthetic_root / "component"
    (component / "z-dir").mkdir(parents=True)
    (component / "z-dir" / "x").write_bytes(b"xyz")
    (component / "a").write_bytes(b"a")
    (component / "é").write_bytes(b"utf8")
    inventory = component_inventory(component, "formal_cpu")
    logical = [item["logical_path"] for item in inventory["entries"]]
    assert logical == sorted(logical, key=lambda value: value.encode("utf-8"))
    assert "component/" not in logical
    assert inventory["entry_count"] == 4
    assert inventory["regular_file_count"] == 3
    assert inventory["directory_count"] == 1
    assert inventory["total_bytes"] == 8
    assert inventory["inventory_sha256"] == canonical_sha256(inventory["entries"])


def test_single_file_inventory_canonical_basename_survives_rename(
    a46_3_synthetic_root,
):
    source_basename = PRODUCTION_SINGLE_FILE_LOGICAL_BASENAMES["effective_lock"]
    source = a46_3_synthetic_root / source_basename
    renamed = a46_3_synthetic_root / "effective-lock.json"
    source.write_bytes(b"same frozen bytes")
    renamed.write_bytes(source.read_bytes())
    source.chmod(0o644)
    renamed.chmod(0o644)

    source_inventory = component_inventory(source, "effective_lock")
    renamed_default = component_inventory(renamed, "effective_lock")
    renamed_canonical = component_inventory(
        renamed,
        "effective_lock",
        single_file_logical_basename=source_basename,
    )
    assert renamed_canonical == source_inventory
    assert renamed_default != source_inventory
    assert renamed_default["entries"][0]["logical_path"] == "effective-lock.json"
    assert renamed_default["inventory_sha256"] != source_inventory[
        "inventory_sha256"
    ]


def test_single_file_inventory_canonical_basename_rejects_misuse(
    a46_3_synthetic_root,
):
    expected = PRODUCTION_SINGLE_FILE_LOGICAL_BASENAMES["effective_lock"]
    component = a46_3_synthetic_root / "effective-lock.json"
    component.write_bytes(b"payload")
    for invalid in ("", ".", "..", "nested/name", "nested\\name", "bad\x00name", False):
        with pytest.raises(ContractError, match="logical basename is unsafe"):
            component_inventory(
                component,
                "generic",
                single_file_logical_basename=invalid,
            )
    with pytest.raises(ContractError, match="does not match frozen component"):
        component_inventory(
            component,
            "effective_lock",
            single_file_logical_basename="effective-lock.json",
        )

    for file_count in (1, 2):
        directory = a46_3_synthetic_root / f"directory-{file_count}"
        directory.mkdir()
        for index in range(file_count):
            (directory / f"file-{index}").write_bytes(b"x")
        with pytest.raises(ContractError, match="regular-file component"):
            component_inventory(
                directory,
                "effective_lock",
                single_file_logical_basename=expected,
            )


def test_component_inventory_rejects_symlink_hardlink_and_nonregular(
    a46_3_synthetic_root,
):
    for kind in ("symlink", "hardlink", "fifo"):
        component = a46_3_synthetic_root / kind
        component.mkdir()
        original = component / "original"
        original.write_bytes(b"x")
        if kind == "symlink":
            (component / "bad").symlink_to(original)
        elif kind == "hardlink":
            os.link(original, component / "bad")
        else:
            os.mkfifo(component / "bad")
        with pytest.raises(ContractError):
            component_inventory(component, kind)


def test_capsule_manifest_recomputes_inventory_paths_summary_and_self_digest(
    a46_3_synthetic_root,
):
    roots = []
    for component_id in ("one", "two"):
        root = a46_3_synthetic_root / component_id
        root.mkdir()
        (root / "payload").write_text(component_id)
        roots.append(component_inventory(root, component_id))
    paths = {
        item["component_id"]: (
            f"synthetic/source/{item['component_id']}",
            f"synthetic/final/{item['component_id']}",
        )
        for item in roots
    }
    manifest = build_capsule_manifest(
        roots,
        paths,
        predecessor={"status": "CHANGES_REQUIRED"},
        inventory_algorithm={"root_entry_included": False},
        later_evidence_absence={"all_successor_evidence": True},
    )
    validate_capsule_manifest(manifest, require_frozen=False)
    assert manifest["diagnostic_only"] is True
    assert manifest["admissible_for_successor"] is False
    invalid = copy.deepcopy(manifest)
    invalid["entries"][0]["source_path"] = "../escape"
    with pytest.raises(ContractError):
        validate_capsule_manifest(invalid, require_frozen=False)
    invalid = copy.deepcopy(manifest)
    invalid["document_digest"] = "0" * 64
    with pytest.raises(ContractError, match="document digest"):
        validate_capsule_manifest(invalid, require_frozen=False)


def test_capsule_manifest_fresh_single_file_uses_source_logical_basename(
    a46_3_synthetic_root,
):
    source_basename = PRODUCTION_SINGLE_FILE_LOGICAL_BASENAMES["effective_lock"]
    source = a46_3_synthetic_root / "source" / source_basename
    final = a46_3_synthetic_root / "final" / "effective-lock.json"
    source.parent.mkdir()
    final.parent.mkdir()
    source.write_bytes(b"same frozen bytes")
    final.write_bytes(source.read_bytes())
    source.chmod(0o644)
    final.chmod(0o644)
    component_paths = {
        "effective_lock": (
            f"synthetic/source/{source_basename}",
            "synthetic/final/effective-lock.json",
        )
    }
    common = {
        "predecessor": {"status": "CHANGES_REQUIRED"},
        "inventory_algorithm": {"root_entry_included": False},
        "later_evidence_absence": {"all_successor_evidence": True},
    }

    canonical_manifest = build_capsule_manifest(
        [component_inventory(source, "effective_lock")],
        component_paths,
        **common,
    )
    assert canonical_manifest["entries"][0]["logical_path"] == source_basename
    validate_capsule_manifest(
        canonical_manifest,
        require_frozen=False,
        component_roots={"effective_lock": final},
    )

    physical_manifest = build_capsule_manifest(
        [component_inventory(final, "effective_lock")],
        component_paths,
        **common,
    )
    assert physical_manifest["entries"][0]["logical_path"] == "effective-lock.json"
    with pytest.raises(ContractError, match="does not match frozen identity"):
        validate_capsule_manifest(
            physical_manifest,
            require_frozen=False,
            component_roots={"effective_lock": final},
        )

    wrong_source = copy.deepcopy(canonical_manifest)
    wrong_source["component_inventory"][0]["source_root"] = (
        "synthetic/source/wrong.json"
    )
    wrong_source["entries"][0]["source_path"] = "synthetic/source/wrong.json"
    wrong_source["document_digest"] = contract_module._self_digest(
        wrong_source, "document_digest"
    )
    with pytest.raises(ContractError, match="does not match frozen component"):
        validate_capsule_manifest(
            wrong_source,
            require_frozen=False,
            component_roots={"effective_lock": final},
        )


def test_frozen_manifest_schema_has_exact_four_component_auxiliary_shape():
    frozen_components = load_contract()["predecessor_capsule_lineage"][
        "manifest_json_schema"
    ]["properties"]["component_inventory"]["const"]
    core_fields = {
        "component_id",
        "source_root",
        "final_root",
        "entry_count",
        "regular_file_count",
        "directory_count",
        "total_bytes",
        "inventory_sha256",
    }

    assert [item["component_id"] for item in frozen_components] == list(
        PREDECESSOR_COMPONENT_IDS
    )
    assert [set(item) - core_fields for item in frozen_components] == [
        set(),
        set(),
        {"raw_sha256", "document_digest"},
        {"raw_sha256", "canonical_self_sha256"},
    ]


def _synthetic_frozen_capsule_builder_inputs(root, monkeypatch):
    source = root / "frozen-source"
    final = root / "frozen-final"
    source.mkdir()
    final.mkdir()

    for component_id in PREDECESSOR_COMPONENT_IDS[:2]:
        source_component = source / component_id
        final_component = final / component_id
        (source_component / "nested").mkdir(parents=True)
        (final_component / "nested").mkdir(parents=True)
        payload = f"{component_id}-payload".encode()
        (source_component / "nested" / "payload.bin").write_bytes(payload)
        (final_component / "nested" / "payload.bin").write_bytes(payload)

    support_basename = PRODUCTION_SINGLE_FILE_LOGICAL_BASENAMES[
        "support_classification"
    ]
    lock_basename = PRODUCTION_SINGLE_FILE_LOGICAL_BASENAMES["effective_lock"]
    support_source = source / support_basename
    support_final = final / support_basename
    lock_source = source / lock_basename
    lock_final = final / "effective-lock.json"
    support_source.write_bytes(b'{"kind":"support"}\n')
    support_final.write_bytes(support_source.read_bytes())
    lock_source.write_bytes(b'{"kind":"lock"}\n')
    lock_final.write_bytes(lock_source.read_bytes())

    source_roots = {
        "formal_cpu": source / "formal_cpu",
        "formal_mapping": source / "formal_mapping",
        "support_classification": support_source,
        "effective_lock": lock_source,
    }
    final_roots = {
        "formal_cpu": final / "formal_cpu",
        "formal_mapping": final / "formal_mapping",
        "support_classification": support_final,
        "effective_lock": lock_final,
    }
    inventories = [
        component_inventory(source_roots[component_id], component_id)
        for component_id in PREDECESSOR_COMPONENT_IDS
    ]
    component_paths = {
        "formal_cpu": (
            "synthetic/source/formal-cpu",
            "synthetic/final/formal-cpu",
        ),
        "formal_mapping": (
            "synthetic/source/formal-mapping",
            "synthetic/final/formal-mapping",
        ),
        "support_classification": (
            f"synthetic/source/{support_basename}",
            f"synthetic/final/{support_basename}",
        ),
        "effective_lock": (
            f"synthetic/source/{lock_basename}",
            "synthetic/final/effective-lock.json",
        ),
    }
    common = {
        "predecessor": {"status": "CHANGES_REQUIRED"},
        "inventory_algorithm": {"root_entry_included": False},
        "later_evidence_absence": {"all_successor_evidence": True},
    }
    synthetic = build_capsule_manifest(
        inventories,
        component_paths,
        **common,
    )
    frozen_components = copy.deepcopy(synthetic["component_inventory"])
    frozen_components[2].update(
        {
            "raw_sha256": sha256_file(support_source),
            "document_digest": canonical_sha256({"kind": "support"}),
        }
    )
    frozen_components[3].update(
        {
            "raw_sha256": sha256_file(lock_source),
            "canonical_self_sha256": canonical_sha256({"kind": "lock"}),
        }
    )
    manifest_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["component_inventory"],
        "properties": {
            "component_inventory": {"const": frozen_components},
        },
    }
    monkeypatch.setattr(
        contract_module,
        "load_contract",
        lambda: {
            "predecessor_capsule_lineage": {
                "manifest_json_schema": manifest_schema,
            }
        },
    )
    return inventories, component_paths, common, frozen_components, final_roots


def test_capsule_manifest_frozen_builder_embeds_exact_auxiliary_projection(
    a46_3_synthetic_root, monkeypatch
):
    inventories, paths, common, frozen_components, final_roots = (
        _synthetic_frozen_capsule_builder_inputs(
            a46_3_synthetic_root,
            monkeypatch,
        )
    )
    manifest = build_capsule_manifest(
        inventories,
        paths,
        frozen_components=frozen_components,
        **common,
    )

    assert [item["component_id"] for item in manifest["component_inventory"]] == list(
        PREDECESSOR_COMPONENT_IDS
    )
    auxiliary_fields = {
        "raw_sha256",
        "document_digest",
        "canonical_self_sha256",
    }
    assert [
        {key: value for key, value in item.items() if key in auxiliary_fields}
        for item in manifest["component_inventory"]
    ] == [
        {},
        {},
        {
            "raw_sha256": frozen_components[2]["raw_sha256"],
            "document_digest": frozen_components[2]["document_digest"],
        },
        {
            "raw_sha256": frozen_components[3]["raw_sha256"],
            "canonical_self_sha256": frozen_components[3][
                "canonical_self_sha256"
            ],
        },
    ]
    validate_capsule_manifest(
        manifest,
        require_frozen=True,
        component_roots=final_roots,
    )


def test_capsule_manifest_frozen_builder_rejects_metadata_and_core_drift(
    a46_3_synthetic_root, monkeypatch
):
    inventories, paths, common, frozen_components, _ = (
        _synthetic_frozen_capsule_builder_inputs(
            a46_3_synthetic_root,
            monkeypatch,
        )
    )

    invalid_frozen = []
    changed = copy.deepcopy(frozen_components)
    changed[0]["unknown"] = "caller metadata"
    invalid_frozen.append(changed)
    changed = copy.deepcopy(frozen_components)
    changed[2].pop("document_digest")
    invalid_frozen.append(changed)
    changed = copy.deepcopy(frozen_components)
    changed[2]["raw_sha256"] = "0" * 64
    invalid_frozen.append(changed)
    invalid_frozen.append(copy.deepcopy(frozen_components[:-1]))
    changed = copy.deepcopy(frozen_components)
    changed.append(copy.deepcopy(changed[-1]))
    invalid_frozen.append(changed)
    changed = copy.deepcopy(frozen_components)
    changed[0]["component_id"] = "unknown"
    invalid_frozen.append(changed)
    invalid_frozen.append(list(reversed(copy.deepcopy(frozen_components))))
    for changed in invalid_frozen:
        with pytest.raises(ContractError, match="contract schema const"):
            build_capsule_manifest(
                inventories,
                paths,
                frozen_components=changed,
                **common,
            )
    for changed in (tuple(frozen_components), False):
        with pytest.raises(ContractError, match="contract schema const"):
            build_capsule_manifest(
                inventories,
                paths,
                frozen_components=changed,
                **common,
            )

    changed_inventories = copy.deepcopy(inventories)
    changed_inventories[0]["caller_metadata"] = "forbidden"
    with pytest.raises(ContractError, match="unknown or missing field"):
        build_capsule_manifest(
            changed_inventories,
            paths,
            frozen_components=frozen_components,
            **common,
        )
    changed_inventories = copy.deepcopy(inventories)
    changed_inventories[0].pop("entries")
    with pytest.raises(ContractError, match="unknown or missing field"):
        build_capsule_manifest(
            changed_inventories,
            paths,
            frozen_components=frozen_components,
            **common,
        )

    for changed_inventories in (
        list(reversed(copy.deepcopy(inventories))),
        copy.deepcopy(inventories[:-1]),
        copy.deepcopy(inventories) + [copy.deepcopy(inventories[-1])],
    ):
        with pytest.raises(ContractError, match="core/order drift"):
            build_capsule_manifest(
                changed_inventories,
                paths,
                frozen_components=frozen_components,
                **common,
            )
    changed_inventories = copy.deepcopy(inventories)
    changed_inventories[0]["entry_count"] += 1
    with pytest.raises(ContractError, match="core/order drift"):
        build_capsule_manifest(
            changed_inventories,
            paths,
            frozen_components=frozen_components,
            **common,
        )
    changed_inventories = copy.deepcopy(inventories)
    changed_inventories[0]["component_id"] = "unknown"
    with pytest.raises(ContractError, match="path mapping is missing"):
        build_capsule_manifest(
            changed_inventories,
            paths,
            frozen_components=frozen_components,
            **common,
        )

    for changed_paths in (
        {key: value for key, value in paths.items() if key != "effective_lock"},
        {**paths, "unknown": ("synthetic/source/x", "synthetic/final/x")},
    ):
        with pytest.raises(ContractError, match="path set mismatch"):
            build_capsule_manifest(
                inventories,
                changed_paths,
                frozen_components=frozen_components,
                **common,
            )
    changed_paths = copy.deepcopy(paths)
    changed_paths["formal_cpu"] = (
        "synthetic/source/drifted",
        changed_paths["formal_cpu"][1],
    )
    with pytest.raises(ContractError, match="core/order drift"):
        build_capsule_manifest(
            inventories,
            changed_paths,
            frozen_components=frozen_components,
            **common,
        )


def _resource_record(generation, lineage_id):
    unknown = {
        "status": "UNKNOWN",
        "reason": "no authoritative measurement",
        "measurement_boundary": f"{generation}:handoff",
    }
    return {
        "lineage_id": lineage_id,
        "generation_id": generation,
        "wall_time": copy.deepcopy(unknown),
        "cpu_time": copy.deepcopy(unknown),
        "gpu_time": copy.deepcopy(unknown),
        "persistent_storage": {
            "status": "KNOWN",
            "value": 1,
            "unit": "bytes",
            "measurement_boundary": f"{generation}:handoff",
            "source": "synthetic-test",
        },
        "transient_storage": copy.deepcopy(unknown),
    }


def test_resource_lineage_is_append_only_and_preserves_explicit_unknown():
    records = [
        _resource_record("S10R3-A46.2-G1", "g1-predecessor"),
        _resource_record("S10R3-A46.3-G2", "g2-attempt-01"),
        _resource_record("S10R3-A46.3-G2", "g2-attempt-02"),
        _resource_record("S10R3-A46.5-G3", "g3-successor"),
    ]
    binding = build_resource_lineage_binding(records)
    validate_resource_lineage_binding(binding)
    assert binding["canonical_sha256"] == canonical_sha256(records)
    assert binding["reset"] is False
    for mutator in (
        lambda value: value["records"].pop(0),
        lambda value: value.update({"reset": True}),
        lambda value: value["records"][0]["gpu_time"].update(
            {"status": "KNOWN", "value": 0}
        ),
        lambda value: value.update({"canonical_sha256": "0" * 64}),
    ):
        invalid = copy.deepcopy(binding)
        mutator(invalid)
        with pytest.raises(ContractError):
            validate_resource_lineage_binding(invalid)


def test_successor_audit_checks_reject_seven_ten_and_reordered():
    checks = list(SUCCESSOR_AUDIT_CHECKS)
    validate_successor_audit_checks(checks)
    for invalid in (checks[:7], [*checks, "tenth"], [checks[1], checks[0], *checks[2:]]):
        with pytest.raises(ContractError, match="exact ordered nine"):
            validate_successor_audit_checks(invalid)


def test_lineage_seal_cross_binds_manifest_journal_and_admission(
    a46_3_synthetic_root,
):
    authority = load_contract()
    authority_record = {
        "path": DEFAULT_CONTRACT_PATH.relative_to(ROOT).as_posix(),
        "commit": contract_module.G1_PHASE1_SEAL_COMMIT,
        "raw_sha256": contract_module.G1_CONTRACT_RAW_SHA256,
        "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
    }
    component = a46_3_synthetic_root / "sealed-component"
    component.mkdir()
    (component / "payload").write_bytes(b"sealed")
    inventory = component_inventory(component, "one")
    manifest = build_capsule_manifest(
        [inventory],
        {"one": ("synthetic/source/one", "synthetic/final/one")},
        predecessor={"status": "CHANGES_REQUIRED"},
        inventory_algorithm={"root_entry_included": False},
        later_evidence_absence={"all_successor_evidence": True},
    )
    journal = _complete_transition_journal(
        _synthetic_admission_identity(a46_3_synthetic_root)
    )
    seal = build_lineage_seal(
        authority_contract=authority_record,
        final_capsule_root="synthetic/final",
        predecessor_lock={"raw_sha256": "b" * 64},
        manifest_path="synthetic/final/predecessor-manifest.json",
        manifest=manifest,
        journal_path="synthetic/journal.json",
        journal=journal,
        contract=authority,
    )
    validate_lineage_seal(
        seal,
        manifest=manifest,
        journal=journal,
        require_frozen=False,
        contract=authority,
    )
    for field in ("sha256", "document_digest"):
        invalid = copy.deepcopy(seal)
        invalid["capsule_manifest"][field] = "0" * 64
        invalid["document_digest"] = contract_module._self_digest(
            invalid, "document_digest"
        )
        with pytest.raises(ContractError, match="manifest binding"):
            validate_lineage_seal(
                invalid,
                manifest=manifest,
                journal=journal,
                require_frozen=False,
                contract=authority,
            )
    invalid = copy.deepcopy(seal)
    invalid["admission_lock_identity"]["st_ino"] += 1
    invalid["admission_lock_identity"]["identity_digest"] = (
        contract_module._identity_digest(invalid["admission_lock_identity"])
    )
    invalid["document_digest"] = contract_module._self_digest(
        invalid, "document_digest"
    )
    with pytest.raises(ContractError, match="journal binding"):
        validate_lineage_seal(
            invalid,
            manifest=manifest,
            journal=journal,
            require_frozen=False,
            contract=authority,
        )
    for mutation in (
        lambda value: value.pop("manifest_repair"),
        lambda value: value["manifest_repair"].update({"replacement_count": 2}),
        lambda value: value["manifest_repair"].update({"quarantine": True}),
    ):
        invalid = copy.deepcopy(seal)
        mutation(invalid)
        invalid["document_digest"] = contract_module._self_digest(
            invalid, "document_digest"
        )
        with pytest.raises(ContractError, match="manifest-repair binding"):
            validate_lineage_seal(
                invalid,
                manifest=manifest,
                journal=journal,
                require_frozen=False,
                contract=authority,
            )


def _synthetic_admission_identity(a46_3_synthetic_root):
    path = a46_3_synthetic_root / "journal-admission.lock"
    return create_stable_admission_lock(path)


def _complete_transition_journal(identity):
    journal = new_transition_journal(identity)
    for component in PREDECESSOR_COMPONENT_IDS:
        journal = append_transition_event(
            journal, action="component_relocated", component_id=component
        )
    journal = append_transition_event(journal, action="staging_verified")
    return append_transition_event(journal, action="finalized")


def _five_event_transition_journal(identity):
    journal = new_transition_journal(identity)
    for component_id in PREDECESSOR_COMPONENT_IDS:
        journal = append_transition_event(
            journal, action="component_relocated", component_id=component_id
        )
    return journal


def _synthetic_manifest_repair_classifier_state(a46_3_synthetic_root):
    authority = copy.deepcopy(load_contract())
    admission_path = a46_3_synthetic_root / "repair-classifier-admission.lock"
    identity = create_stable_admission_lock(admission_path)
    journal = _five_event_transition_journal(identity)
    journal_bytes = contract_module.canonical_json_bytes(journal) + b"\n"
    repair = authority["predecessor_capsule_lineage"][
        "one_time_manifest_repair"
    ]
    repair["pre_repair_journal_identity"] = {
        "raw_sha256": hashlib.sha256(journal_bytes).hexdigest(),
        "document_digest": journal["document_digest"],
        "state": "MOVING",
        "event_count": 5,
        "last_action": "component_relocated",
        "relocated_components": list(PREDECESSOR_COMPONENT_IDS),
        "admission_lock_identity_digest": identity["identity_digest"],
    }
    transitions = authority["write_boundaries"]["execution_artifacts"][
        "scoped_artifact_policy"
    ][
        "a46_3_closed_transition_exception"
    ]["components"]
    frozen = authority["predecessor_capsule_lineage"][
        "frozen_predecessor_inventory"
    ]["components"]
    component_state = [
        {
            "component_id": component_id,
            "source_path": str(paths["source"]).rstrip("/"),
            "staging_path": str(paths["staging_destination"]).rstrip("/"),
            "inventory_sha256": expected["inventory_sha256"],
            "source_absent": True,
            "staging_present": True,
        }
        for component_id, paths, expected in zip(
            PREDECESSOR_COMPONENT_IDS, transitions, frozen
        )
    ]
    return {
        "target_path": repair["target_path"],
        "temp_path": repair["fixed_temp_path"],
        "target_identity": copy.deepcopy(repair["old_manifest_identity"]),
        "target_document": {"synthetic": "old"},
        "journal_path": authority["predecessor_capsule_lineage"]["paths"][
            "journal"
        ],
        "journal_raw_sha256": repair["pre_repair_journal_identity"][
            "raw_sha256"
        ],
        "journal": journal,
        "admission_lock_identity_value": identity,
        "scope_lock_projection": [
            {"scope_id": component_id} for component_id in PREDECESSOR_COMPONENT_IDS
        ],
        "component_state": component_state,
        "final_capsule_absent": True,
        "lineage_seal_absent": True,
        "temp_absent": True,
        "contract": authority,
    }


def test_a46_4_classifier_accepts_only_exact_old_and_corrected_branches(
    a46_3_synthetic_root, monkeypatch
):
    state = _synthetic_manifest_repair_classifier_state(a46_3_synthetic_root)
    observed_profiles = []
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda document, *, branch, contract: observed_profiles.append(branch),
    )
    assert classify_one_time_manifest_repair(**state) == "replace_once"
    corrected = state["contract"]["predecessor_capsule_lineage"][
        "one_time_manifest_repair"
    ]["corrected_manifest_identity"]
    state["target_identity"] = copy.deepcopy(corrected)
    state["target_document"] = {"synthetic": "corrected"}
    assert classify_one_time_manifest_repair(**state) == "verify_staging"
    assert observed_profiles == ["old", "corrected"]


@pytest.mark.parametrize(
    "branch,field",
    [
        *(('old', field) for field in (
            "entry_type", "mode", "nlink", "st_dev", "st_ino", "size_bytes",
            "raw_sha256", "document_digest", "mtime_utc", "ctime_utc",
        )),
        *(('corrected', field) for field in (
            "entry_type", "mode", "nlink", "st_dev", "size_bytes",
            "raw_sha256", "document_digest",
        )),
    ],
)
def test_a46_4_classifier_rejects_every_manifest_identity_mutation(
    a46_3_synthetic_root, monkeypatch, branch, field
):
    state = _synthetic_manifest_repair_classifier_state(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    expected = state["contract"]["predecessor_capsule_lineage"][
        "one_time_manifest_repair"
    ][f"{branch}_manifest_identity"]
    state["target_identity"] = copy.deepcopy(expected)
    value = state["target_identity"][field]
    state["target_identity"][field] = value + 1 if type(value) is int else f"drift-{value}"
    with pytest.raises(ContractError, match="BLOCKED_TRANSITION"):
        classify_one_time_manifest_repair(**state)


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda value: value.update({"temp_absent": False}), "absence drift"),
        (lambda value: value.update({"final_capsule_absent": False}), "absence drift"),
        (lambda value: value.update({"lineage_seal_absent": False}), "absence drift"),
        (lambda value: value["scope_lock_projection"].pop(), "scope-lock"),
        (lambda value: value["scope_lock_projection"].reverse(), "scope-lock"),
        (lambda value: value["component_state"][0].update({"source_absent": False}), "component/source"),
        (lambda value: value["component_state"][0].update({"inventory_sha256": "0" * 64}), "component/source"),
        (lambda value: value.update({"target_path": "wrong"}), "target/temp"),
        (lambda value: value.update({"temp_path": "wrong"}), "target/temp"),
    ],
)
def test_a46_4_classifier_rejects_boundary_lock_and_component_drift(
    a46_3_synthetic_root, monkeypatch, mutation, match
):
    state = _synthetic_manifest_repair_classifier_state(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    mutation(state)
    with pytest.raises(ContractError, match=match):
        classify_one_time_manifest_repair(**state)


@pytest.mark.parametrize("late_action", ["staging_verified", "finalized", "blocked"])
def test_a46_4_classifier_rejects_late_or_blocked_journal(
    a46_3_synthetic_root, monkeypatch, late_action
):
    state = _synthetic_manifest_repair_classifier_state(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    if late_action == "staging_verified":
        state["journal"] = append_transition_event(
            state["journal"], action="staging_verified"
        )
    elif late_action == "finalized":
        staged = append_transition_event(state["journal"], action="staging_verified")
        state["journal"] = append_transition_event(staged, action="finalized")
    else:
        state["journal"] = append_transition_event(state["journal"], action="blocked")
    with pytest.raises(ContractError, match="five-event prefix"):
        classify_one_time_manifest_repair(**state)


def _a46_4_atomic_repair_fixture(root):
    authority = copy.deepcopy(load_contract())
    relative = lambda path: path.relative_to(ROOT).as_posix()
    staging_root = root / "staging"
    staging_root.mkdir()
    target = staging_root / "predecessor-manifest.json"
    temporary = staging_root / ".predecessor-manifest.a46-4.tmp"
    journal_path = root / "transition-journal.json"
    final_capsule = root / "final-capsule"
    seal_path = root / "lineage-seal.json"
    admission_path = root / "admission.lock"
    admission_identity = create_stable_admission_lock(admission_path)
    journal = _five_event_transition_journal(admission_identity)
    journal_path.write_bytes(contract_module.canonical_json_bytes(journal) + b"\n")
    journal_path.chmod(0o600)

    transitions = []
    frozen = []
    for component_id in PREDECESSOR_COMPONENT_IDS:
        single_file = component_id in ("support_classification", "effective_lock")
        if single_file:
            basename = PRODUCTION_SINGLE_FILE_LOGICAL_BASENAMES[component_id]
            source = root / "source" / basename
            staging = staging_root / basename
            staging.write_text(component_id)
            inventory = component_inventory(
                staging,
                component_id,
                single_file_logical_basename=basename,
            )
        else:
            source = root / "source" / component_id
            staging = staging_root / component_id
            (staging / "nested").mkdir(parents=True)
            (staging / "nested" / "payload").write_text(component_id)
            inventory = component_inventory(staging, component_id)
        transitions.append(
            {
                "source": relative(source),
                "staging_destination": relative(staging),
                "final_destination": relative(final_capsule / component_id),
            }
        )
        frozen.append(
            {
                "component_id": component_id,
                "source_root": relative(source),
                "final_root": relative(final_capsule / component_id),
                "entry_count": inventory["entry_count"],
                "regular_file_count": inventory["regular_file_count"],
                "directory_count": inventory["directory_count"],
                "total_bytes": inventory["total_bytes"],
                "inventory_sha256": inventory["inventory_sha256"],
            }
        )

    lineage = authority["predecessor_capsule_lineage"]
    legacy = [
        {
            field: item[field]
            for field in contract_module._MANIFEST_COMPONENT_CORE_FIELDS
        }
        for item in frozen
    ]
    old_document = {
        "component_inventory": legacy,
        "document_digest": "a" * 64,
        "synthetic": "old",
    }
    corrected_document = copy.deepcopy(old_document)
    corrected_document["component_inventory"] = copy.deepcopy(frozen)
    corrected_document["document_digest"] = contract_module._self_digest(
        corrected_document, "document_digest"
    )
    target.write_bytes(contract_module.canonical_json_bytes(old_document) + b"\n")
    target.chmod(0o600)
    old_identity, _ = contract_module._manifest_snapshot(target)
    corrected_bytes = contract_module.canonical_json_bytes(corrected_document) + b"\n"
    lineage["manifest_json_schema"] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["component_inventory", "document_digest", "synthetic"],
        "properties": {
            "component_inventory": {"const": copy.deepcopy(frozen)},
            "document_digest": {"type": "string"},
            "synthetic": {"const": "old"},
        },
        "additionalProperties": False,
    }
    lineage["paths"].update(
        {
            "final_capsule": relative(final_capsule),
            "admission_lock": relative(admission_path),
            "journal": relative(journal_path),
            "durable_lineage_seal": relative(seal_path),
        }
    )
    lineage["frozen_predecessor_inventory"]["components"] = frozen
    authority["write_boundaries"]["execution_artifacts"][
        "scoped_artifact_policy"
    ][
        "a46_3_closed_transition_exception"
    ]["components"] = transitions
    repair = lineage["one_time_manifest_repair"]
    repair["target_path"] = relative(target)
    repair["fixed_temp_path"] = relative(temporary)
    repair["old_manifest_identity"] = {
        **old_identity,
        "generic_validation": "PASS",
        "frozen_validation": "FAIL_KNOWN_AUXILIARY_OMISSION_ONLY",
        "entry_count": 4129,
        "component_core_and_order_equal_frozen": True,
    }
    repair["corrected_manifest_identity"] = {
        "entry_type": "regular_file",
        "mode": "0600",
        "nlink": 1,
        "st_dev": staging_root.stat().st_dev,
        "size_bytes": len(corrected_bytes),
        "raw_sha256": hashlib.sha256(corrected_bytes).hexdigest(),
        "document_digest": corrected_document["document_digest"],
        "generic_validation": "PASS",
        "frozen_validation": "PASS",
        "entry_count": 4129,
        "component_core_auxiliary_and_order_equal_frozen": True,
    }
    repair["pre_repair_journal_identity"] = {
        "raw_sha256": hashlib.sha256(journal_path.read_bytes()).hexdigest(),
        "document_digest": journal["document_digest"],
        "state": "MOVING",
        "event_count": 5,
        "last_action": "component_relocated",
        "relocated_components": list(PREDECESSOR_COMPONENT_IDS),
        "admission_lock_identity_digest": admission_identity["identity_digest"],
    }

    return {
        "contract": authority,
        "admission_path": admission_path,
        "admission_identity": admission_identity,
        "scope_paths": [
            ROOT / item["staging_destination"] for item in transitions
        ],
        "target": target,
        "temporary": temporary,
        "journal_path": journal_path,
        "old_bytes": target.read_bytes(),
        "corrected_document": corrected_document,
        "corrected_bytes": corrected_bytes,
    }


def _close_scope_descriptors(fixture):
    assert "scope_descriptors" not in fixture


def _invoke_a46_4_atomic_repair(fixture, builder):
    with acquire_manifest_repair_locks(
        expected_admission_identity=fixture["admission_identity"],
        contract=fixture["contract"],
    ) as lock_context:
        return repair_staging_manifest_once(
            corrected_builder=builder,
            lock_context=lock_context,
            contract=fixture["contract"],
        )


def _a46_4_repair_mutation_snapshot(fixture):
    frozen = fixture["contract"]["predecessor_capsule_lineage"][
        "frozen_predecessor_inventory"
    ]["components"]
    component_digests = []
    for component_id, path, expected in zip(
        PREDECESSOR_COMPONENT_IDS, fixture["scope_paths"], frozen
    ):
        logical_basename = (
            Path(expected["source_root"]).name
            if expected["directory_count"] == 0
            else None
        )
        component_digests.append(
            component_inventory(
                path,
                component_id,
                single_file_logical_basename=logical_basename,
            )["inventory_sha256"]
        )
    return {
        "target": fixture["target"].read_bytes(),
        "temporary_exists": os.path.lexists(fixture["temporary"]),
        "temporary_bytes": (
            fixture["temporary"].read_bytes()
            if fixture["temporary"].is_file()
            and not fixture["temporary"].is_symlink()
            else None
        ),
        "journal": fixture["journal_path"].read_bytes(),
        "component_digests": component_digests,
    }


def test_a46_4_never_locked_raw_fd_and_bare_proofs_cannot_replace(
    a46_3_synthetic_root, monkeypatch
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    before = _a46_4_repair_mutation_snapshot(fixture)
    descriptor = os.open(fixture["admission_path"], os.O_RDWR)
    arbitrary = a46_3_synthetic_root / "arbitrary-scope.lock"
    arbitrary.touch(mode=0o600)
    scope_descriptor = os.open(arbitrary, os.O_RDWR)
    try:
        info = os.fstat(scope_descriptor)
        with pytest.raises(ContractError, match="bare idle-writer/lock"):
            repair_staging_manifest_once(
                corrected_builder=lambda: copy.deepcopy(
                    fixture["corrected_document"]
                ),
                admission_lock_path=fixture["admission_path"],
                admission_descriptor=descriptor,
                expected_admission_identity=fixture["admission_identity"],
                admission_exclusive=True,
                scope_lock_proofs=[
                    {
                        "scope_id": PREDECESSOR_COMPONENT_IDS[0],
                        "path": arbitrary,
                        "descriptor": scope_descriptor,
                        "identity": {
                            "st_dev": info.st_dev,
                            "st_ino": info.st_ino,
                        },
                        "exclusive": True,
                    }
                ],
                contract=fixture["contract"],
            )
    finally:
        os.close(scope_descriptor)
        os.close(descriptor)
    assert _a46_4_repair_mutation_snapshot(fixture) == before


@pytest.mark.parametrize("lock_slot", ["admission", 0, 1, 2, 3])
def test_a46_4_active_context_rejects_each_unlocked_descriptor_without_mutation(
    a46_3_synthetic_root, monkeypatch, lock_slot
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    before = _a46_4_repair_mutation_snapshot(fixture)
    with acquire_manifest_repair_locks(
        expected_admission_identity=fixture["admission_identity"],
        contract=fixture["contract"],
    ) as lock_context:
        record = contract_module._ACTIVE_MANIFEST_REPAIR_LOCK_CONTEXTS[
            lock_context
        ]
        descriptor = (
            record["admission_descriptor"]
            if lock_slot == "admission"
            else record["scopes"][lock_slot]["descriptor"]
        )
        contract_module.fcntl.flock(descriptor, contract_module.fcntl.LOCK_UN)
        with pytest.raises(ContractError, match="not exclusively flocked"):
            repair_staging_manifest_once(
                corrected_builder=lambda: copy.deepcopy(
                    fixture["corrected_document"]
                ),
                lock_context=lock_context,
                contract=fixture["contract"],
            )
    assert _a46_4_repair_mutation_snapshot(fixture) == before


def _a46_4_context_descriptor_and_path(record, lock_slot):
    if lock_slot == "admission":
        return record["admission_descriptor"], record["admission_path"]
    scope = record["scopes"][lock_slot]
    return scope["descriptor"], scope["path"]


@pytest.mark.parametrize("lock_slot", ["admission", 0, 1, 2, 3])
def test_a46_4_same_process_takeover_cannot_impersonate_registered_descriptor(
    a46_3_synthetic_root, monkeypatch, lock_slot
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    before = _a46_4_repair_mutation_snapshot(fixture)
    with acquire_manifest_repair_locks(
        expected_admission_identity=fixture["admission_identity"],
        contract=fixture["contract"],
    ) as lock_context:
        record = contract_module._ACTIVE_MANIFEST_REPAIR_LOCK_CONTEXTS[
            lock_context
        ]
        descriptor, path = _a46_4_context_descriptor_and_path(record, lock_slot)
        contract_module.fcntl.flock(descriptor, contract_module.fcntl.LOCK_UN)
        competitor = contract_module._open_scope_lock(path)
        contract_module.fcntl.flock(
            competitor,
            contract_module.fcntl.LOCK_EX | contract_module.fcntl.LOCK_NB,
        )
        try:
            with pytest.raises(ContractError, match="registered descriptor does not own"):
                repair_staging_manifest_once(
                    corrected_builder=lambda: copy.deepcopy(
                        fixture["corrected_document"]
                    ),
                    lock_context=lock_context,
                    contract=fixture["contract"],
                )
        finally:
            contract_module.fcntl.flock(
                competitor, contract_module.fcntl.LOCK_UN
            )
            os.close(competitor)
    assert _a46_4_repair_mutation_snapshot(fixture) == before


@pytest.mark.parametrize("lock_slot", ["admission", 0, 1, 2, 3])
def test_a46_4_child_process_takeover_cannot_impersonate_registered_descriptor(
    a46_3_synthetic_root, monkeypatch, lock_slot
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    before = _a46_4_repair_mutation_snapshot(fixture)
    child_code = "\n".join(
        [
            "import fcntl, os, stat, sys",
            "path = sys.argv[1]",
            "mode = os.lstat(path).st_mode",
            "flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)",
            "flags |= os.O_DIRECTORY if stat.S_ISDIR(mode) else 0",
            "descriptor = os.open(path, flags)",
            "fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)",
            "print('LOCKED', flush=True)",
            "sys.stdin.readline()",
            "fcntl.flock(descriptor, fcntl.LOCK_UN)",
            "os.close(descriptor)",
        ]
    )
    with acquire_manifest_repair_locks(
        expected_admission_identity=fixture["admission_identity"],
        contract=fixture["contract"],
    ) as lock_context:
        record = contract_module._ACTIVE_MANIFEST_REPAIR_LOCK_CONTEXTS[
            lock_context
        ]
        descriptor, path = _a46_4_context_descriptor_and_path(record, lock_slot)
        contract_module.fcntl.flock(descriptor, contract_module.fcntl.LOCK_UN)
        child = subprocess.Popen(
            [sys.executable, "-c", child_code, str(path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert child.stdout is not None
        assert child.stdout.readline() == "LOCKED\n"
        try:
            with pytest.raises(ContractError, match="registered descriptor does not own"):
                repair_staging_manifest_once(
                    corrected_builder=lambda: copy.deepcopy(
                        fixture["corrected_document"]
                    ),
                    lock_context=lock_context,
                    contract=fixture["contract"],
                )
        finally:
            stdout, stderr = child.communicate("\n", timeout=10)
        assert child.returncode == 0, (stdout, stderr)
    assert _a46_4_repair_mutation_snapshot(fixture) == before


def test_a46_4_context_rejects_checkpoint_release_before_temp_creation(
    a46_3_synthetic_root, monkeypatch
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    before = _a46_4_repair_mutation_snapshot(fixture)
    with acquire_manifest_repair_locks(
        expected_admission_identity=fixture["admission_identity"],
        contract=fixture["contract"],
    ) as lock_context:
        record = contract_module._ACTIVE_MANIFEST_REPAIR_LOCK_CONTEXTS[
            lock_context
        ]
        calls = 0

        def unlock_during_builder():
            nonlocal calls
            calls += 1
            if calls == 1:
                contract_module.fcntl.flock(
                    record["scopes"][2]["descriptor"],
                    contract_module.fcntl.LOCK_UN,
                )
            return copy.deepcopy(fixture["corrected_document"])

        with pytest.raises(ContractError, match="not exclusively flocked"):
            repair_staging_manifest_once(
                corrected_builder=unlock_during_builder,
                lock_context=lock_context,
                contract=fixture["contract"],
            )
    assert _a46_4_repair_mutation_snapshot(fixture) == before


@pytest.mark.parametrize("holder_slot", ["admission", 0, 1, 2, 3])
def test_a46_4_context_acquisition_rejects_competing_holder_without_mutation(
    a46_3_synthetic_root, holder_slot
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    before = _a46_4_repair_mutation_snapshot(fixture)
    if holder_slot == "admission":
        descriptor = os.open(fixture["admission_path"], os.O_RDWR)
    else:
        descriptor = contract_module._open_scope_lock(
            fixture["scope_paths"][holder_slot]
        )
    contract_module.fcntl.flock(
        descriptor,
        contract_module.fcntl.LOCK_EX | contract_module.fcntl.LOCK_NB,
    )
    try:
        with pytest.raises(ContractError, match="lock acquisition failed"):
            with acquire_manifest_repair_locks(
                expected_admission_identity=fixture["admission_identity"],
                contract=fixture["contract"],
            ):
                raise AssertionError("competing lock was not rejected")
    finally:
        contract_module.fcntl.flock(descriptor, contract_module.fcntl.LOCK_UN)
        os.close(descriptor)
    assert _a46_4_repair_mutation_snapshot(fixture) == before


def test_a46_4_forged_stale_and_cross_context_capabilities_fail_closed(
    a46_3_synthetic_root, monkeypatch
):
    root_a = a46_3_synthetic_root / "lease-a"
    root_b = a46_3_synthetic_root / "lease-b"
    root_a.mkdir()
    root_b.mkdir()
    fixture_a = _a46_4_atomic_repair_fixture(root_a)
    fixture_b = _a46_4_atomic_repair_fixture(root_b)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    before_a = _a46_4_repair_mutation_snapshot(fixture_a)
    before_b = _a46_4_repair_mutation_snapshot(fixture_b)
    with pytest.raises(ContractError, match="cannot be caller-constructed"):
        contract_module.ManifestRepairLockContext()
    for forged in ({"exclusive": True}, object()):
        with pytest.raises(ContractError, match="active acquired"):
            repair_staging_manifest_once(
                corrected_builder=lambda: copy.deepcopy(
                    fixture_a["corrected_document"]
                ),
                lock_context=forged,
                contract=fixture_a["contract"],
            )
    stale = None
    with acquire_manifest_repair_locks(
        expected_admission_identity=fixture_a["admission_identity"],
        contract=fixture_a["contract"],
    ) as stale:
        pass
    with pytest.raises(ContractError, match="stale or foreign"):
        repair_staging_manifest_once(
            corrected_builder=lambda: copy.deepcopy(
                fixture_a["corrected_document"]
            ),
            lock_context=stale,
            contract=fixture_a["contract"],
        )
    with acquire_manifest_repair_locks(
        expected_admission_identity=fixture_a["admission_identity"],
        contract=fixture_a["contract"],
    ) as foreign:
        with pytest.raises(ContractError, match="authority mismatch"):
            repair_staging_manifest_once(
                corrected_builder=lambda: copy.deepcopy(
                    fixture_b["corrected_document"]
                ),
                lock_context=foreign,
                contract=fixture_b["contract"],
            )
    assert _a46_4_repair_mutation_snapshot(fixture_a) == before_a
    assert _a46_4_repair_mutation_snapshot(fixture_b) == before_b


def test_a46_4_context_releases_scopes_reverse_then_admission_and_closes_fds(
    a46_3_synthetic_root, monkeypatch
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    real_flock = contract_module.fcntl.flock
    released = []
    descriptors = []
    labels = {}
    with acquire_manifest_repair_locks(
        expected_admission_identity=fixture["admission_identity"],
        contract=fixture["contract"],
    ) as lock_context:
        record = contract_module._ACTIVE_MANIFEST_REPAIR_LOCK_CONTEXTS[
            lock_context
        ]
        descriptors = [record["admission_descriptor"]] + [
            item["descriptor"] for item in record["scopes"]
        ]
        labels = {
            record["admission_descriptor"]: "admission",
            **{
                item["descriptor"]: item["scope_id"] for item in record["scopes"]
            },
        }

        def tracked_flock(descriptor, operation):
            if operation == contract_module.fcntl.LOCK_UN and descriptor in labels:
                released.append(labels[descriptor])
            return real_flock(descriptor, operation)

        monkeypatch.setattr(contract_module.fcntl, "flock", tracked_flock)
    assert released == [*reversed(PREDECESSOR_COMPONENT_IDS), "admission"]
    assert lock_context not in contract_module._ACTIVE_MANIFEST_REPAIR_LOCK_CONTEXTS
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)


def test_a46_4_atomic_repair_replaces_once_and_crash_resume_is_zero_replace(
    a46_3_synthetic_root, monkeypatch
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    real_replace = contract_module.os.replace
    replacements = []

    def counted_replace(source, destination):
        replacements.append((Path(source), Path(destination)))
        return real_replace(source, destination)

    monkeypatch.setattr(contract_module.os, "replace", counted_replace)
    try:
        journal_before = fixture["journal_path"].read_bytes()
        assert _invoke_a46_4_atomic_repair(
            fixture, lambda: copy.deepcopy(fixture["corrected_document"])
        ) == "verify_staging"
        assert fixture["target"].read_bytes() == fixture["corrected_bytes"]
        assert not fixture["temporary"].exists()
        assert fixture["journal_path"].read_bytes() == journal_before
        assert len(replacements) == 1
        assert _invoke_a46_4_atomic_repair(
            fixture,
            lambda: (_ for _ in ()).throw(AssertionError("second build forbidden")),
        ) == "verify_staging"
        assert len(replacements) == 1
    finally:
        _close_scope_descriptors(fixture)


@pytest.mark.parametrize("fault", ["different_builds", "wrong_builder", "temp_exists", "temp_symlink"])
def test_a46_4_atomic_repair_rejects_builder_and_temp_faults(
    a46_3_synthetic_root, monkeypatch, fault
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    calls = 0

    def builder():
        nonlocal calls
        calls += 1
        if fault == "different_builds" and calls == 2:
            return {"document_digest": "c" * 64, "synthetic": "drift"}
        if fault == "wrong_builder":
            return {"document_digest": "c" * 64, "synthetic": "wrong"}
        return copy.deepcopy(fixture["corrected_document"])

    if fault == "temp_exists":
        fixture["temporary"].write_text("occupied")
    elif fault == "temp_symlink":
        fixture["temporary"].symlink_to(fixture["target"])
    try:
        with pytest.raises(ContractError):
            _invoke_a46_4_atomic_repair(fixture, builder)
        assert fixture["target"].read_bytes() == fixture["old_bytes"]
        assert fixture["journal_path"].read_bytes()
    finally:
        _close_scope_descriptors(fixture)


def test_a46_4_atomic_repair_handles_partial_writes_without_truncation(
    a46_3_synthetic_root, monkeypatch
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    real_write = contract_module.os.write

    def partial_write(descriptor, payload):
        return real_write(descriptor, payload[: max(1, len(payload) // 2)])

    monkeypatch.setattr(contract_module.os, "write", partial_write)
    try:
        assert _invoke_a46_4_atomic_repair(
            fixture, lambda: copy.deepcopy(fixture["corrected_document"])
        ) == "verify_staging"
        assert fixture["target"].read_bytes() == fixture["corrected_bytes"]
    finally:
        _close_scope_descriptors(fixture)


@pytest.mark.parametrize("fault", ["zero_write", "file_fsync", "replace"])
def test_a46_4_atomic_repair_pre_replace_fault_leaves_old_target_and_journal(
    a46_3_synthetic_root, monkeypatch, fault
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    journal_before = fixture["journal_path"].read_bytes()
    if fault == "zero_write":
        monkeypatch.setattr(contract_module.os, "write", lambda *args: 0)
    elif fault == "file_fsync":
        monkeypatch.setattr(
            contract_module.os,
            "fsync",
            lambda descriptor: (_ for _ in ()).throw(OSError("fsync fault")),
        )
    else:
        monkeypatch.setattr(
            contract_module.os,
            "replace",
            lambda *args: (_ for _ in ()).throw(OSError("replace fault")),
        )
    try:
        with pytest.raises((ContractError, OSError)):
            _invoke_a46_4_atomic_repair(
                fixture, lambda: copy.deepcopy(fixture["corrected_document"])
            )
        assert fixture["target"].read_bytes() == fixture["old_bytes"]
        assert fixture["journal_path"].read_bytes() == journal_before
    finally:
        _close_scope_descriptors(fixture)


def test_a46_4_atomic_repair_failed_directory_fsync_resumes_without_replacement(
    a46_3_synthetic_root, monkeypatch
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    real_fsync = contract_module.os.fsync
    calls = 0

    def fail_second_fsync(descriptor):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("directory fsync fault")
        return real_fsync(descriptor)

    monkeypatch.setattr(contract_module.os, "fsync", fail_second_fsync)
    try:
        with pytest.raises(OSError, match="directory fsync fault"):
            _invoke_a46_4_atomic_repair(
                fixture, lambda: copy.deepcopy(fixture["corrected_document"])
            )
        assert fixture["target"].read_bytes() == fixture["corrected_bytes"]
        monkeypatch.setattr(contract_module.os, "fsync", real_fsync)
        assert _invoke_a46_4_atomic_repair(
            fixture,
            lambda: (_ for _ in ()).throw(AssertionError("resume rebuilt")),
        ) == "verify_staging"
    finally:
        _close_scope_descriptors(fixture)


def test_a46_4_atomic_repair_blocks_pre_replace_race_without_replacement(
    a46_3_synthetic_root, monkeypatch
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    real_capture = contract_module._capture_manifest_repair_state
    captures = 0

    def raced_capture(**kwargs):
        nonlocal captures
        captures += 1
        state = real_capture(**kwargs)
        if captures == 2:
            state["journal_raw_sha256"] = "0" * 64
        return state

    monkeypatch.setattr(
        contract_module, "_capture_manifest_repair_state", raced_capture
    )
    try:
        with pytest.raises(ContractError, match="pre-replace race"):
            _invoke_a46_4_atomic_repair(
                fixture, lambda: copy.deepcopy(fixture["corrected_document"])
            )
        assert fixture["target"].read_bytes() == fixture["old_bytes"]
        assert fixture["temporary"].exists()
    finally:
        _close_scope_descriptors(fixture)


def test_a46_4_atomic_repair_rejects_missing_or_reordered_scope_locks(
    a46_3_synthetic_root, monkeypatch
):
    fixture = _a46_4_atomic_repair_fixture(a46_3_synthetic_root)
    monkeypatch.setattr(
        contract_module,
        "_validate_repair_manifest_profile",
        lambda *args, **kwargs: None,
    )
    before = _a46_4_repair_mutation_snapshot(fixture)
    with acquire_manifest_repair_locks(
        expected_admission_identity=fixture["admission_identity"],
        contract=fixture["contract"],
    ) as lock_context:
        record = contract_module._ACTIVE_MANIFEST_REPAIR_LOCK_CONTEXTS[
            lock_context
        ]
        original = record["scopes"]
        for scopes in (original[:-1], list(reversed(original))):
            record["scopes"] = scopes
            with pytest.raises(ContractError, match="missing or out of frozen order"):
                repair_staging_manifest_once(
                    corrected_builder=lambda: copy.deepcopy(
                        fixture["corrected_document"]
                    ),
                    lock_context=lock_context,
                    contract=fixture["contract"],
                )
        record["scopes"] = original
    assert _a46_4_repair_mutation_snapshot(fixture) == before


@pytest.mark.parametrize("no_live_writer", [False, True, 1, "asserted"])
def test_a46_4_caller_idle_writer_boolean_is_non_authoritative(no_live_writer):
    with pytest.raises(ContractError, match="bare idle-writer/lock"):
        repair_staging_manifest_once(
            no_live_s10r3_writer=no_live_writer,
            corrected_builder=lambda: {},
        )


def test_a46_4_atomic_repair_default_denies_real_production_path_without_read():
    with pytest.raises(ContractError, match="Main-only"):
        with acquire_manifest_repair_locks(
            expected_admission_identity={},
        ):
            raise AssertionError("production lock context unexpectedly acquired")
    with pytest.raises(ContractError, match="must load the committed contract"):
        with acquire_manifest_repair_locks(
            expected_admission_identity={},
            allow_production=True,
            contract={},
        ):
            raise AssertionError("injected production contract unexpectedly accepted")


def test_a46_4_atomic_repair_uses_only_single_replace_and_no_journal_or_relocation():
    source = Path(contract_module.__file__).read_text(encoding="utf-8")
    body = source[
        source.index("def repair_staging_manifest_once(") : source.index(
            "def validate_lineage_seal("
        )
    ]
    assert body.count("os.replace(temporary, target)") == 1
    assert "append_transition_event(" not in body
    assert "rename_noreplace(" not in body
    assert "unlink(" not in body
    assert "quarantine" not in body
    assert "rollback" not in body


def test_transition_journal_exact_seven_event_chain_and_durable_write(
    a46_3_synthetic_root,
):
    journal = _complete_transition_journal(
        _synthetic_admission_identity(a46_3_synthetic_root)
    )
    validate_transition_journal(journal, production_identity=False)
    assert journal["state"] == "FINALIZED"
    assert [item["action"] for item in journal["events"]] == [
        "prepared",
        "component_relocated",
        "component_relocated",
        "component_relocated",
        "component_relocated",
        "staging_verified",
        "finalized",
    ]
    path = a46_3_synthetic_root / "journal.json"
    write_transition_journal(path, journal)
    assert strict_load_json(path) == journal
    assert not Path(f"{path}.tmp").exists()


def test_production_journal_path_can_be_safely_redirected(
    a46_3_synthetic_root, monkeypatch
):
    journal = _complete_transition_journal(
        _synthetic_admission_identity(a46_3_synthetic_root)
    )
    production_target = PRODUCTION_TRANSITION_PATHS[1]
    synthetic_target = a46_3_synthetic_root / "production-journal.json"
    synthetic_temporary = Path(f"{synthetic_target}.tmp")
    observed = []
    actual_validate = contract_module.validate_transition_journal

    def redirect(path, *, allow_production=False):
        observed.append((Path(path), allow_production))
        if Path(path) == Path(production_target):
            return synthetic_target, production_target
        if Path(path) == synthetic_temporary:
            return synthetic_temporary, synthetic_temporary.as_posix()
        raise AssertionError(f"unexpected journal path: {path}")

    def validate_as_synthetic(document, *, production_identity=True):
        assert production_identity is True
        actual_validate(document, production_identity=False)

    monkeypatch.setattr(contract_module, "_authorized_transition_path", redirect)
    monkeypatch.setattr(
        contract_module, "validate_transition_journal", validate_as_synthetic
    )
    write_transition_journal(production_target, journal, allow_production=True)
    assert observed == [
        (Path(production_target), True),
        (synthetic_temporary, True),
    ]
    assert strict_load_json(synthetic_target) == journal
    assert not synthetic_temporary.exists()


@pytest.mark.parametrize("mutation", ["reorder", "duplicate", "fake_final", "wrong_state"])
def test_transition_journal_rejects_illegal_chains(a46_3_synthetic_root, mutation):
    journal = _complete_transition_journal(
        _synthetic_admission_identity(a46_3_synthetic_root)
    )
    if mutation == "reorder":
        journal["events"][1], journal["events"][2] = (
            journal["events"][2],
            journal["events"][1],
        )
    elif mutation == "duplicate":
        journal["events"].insert(5, copy.deepcopy(journal["events"][5]))
    elif mutation == "fake_final":
        journal["events"] = [journal["events"][-1]]
    else:
        journal["events"][5]["state"] = "STAGING_VERIFIED"
    with pytest.raises(ContractError):
        validate_transition_journal(journal, production_identity=False)


def test_transition_recovery_covers_each_forward_boundary(a46_3_synthetic_root):
    identity = _synthetic_admission_identity(a46_3_synthetic_root)
    journal = new_transition_journal(identity)
    locations = {component: "source" for component in PREDECESSOR_COMPONENT_IDS}
    for index, component in enumerate(PREDECESSOR_COMPONENT_IDS):
        assert transition_recovery_action(journal, locations) == {
            "action": "relocate_component",
            "component_id": component,
        }
        locations[component] = "staging"
        assert transition_recovery_action(journal, locations) == {
            "action": "record_component_relocated",
            "component_id": component,
        }
        journal = append_transition_event(
            journal, action="component_relocated", component_id=component
        )
        assert len(journal["relocated_components"]) == index + 1
    assert transition_recovery_action(journal, locations)["action"] == "verify_staging"
    journal = append_transition_event(journal, action="staging_verified")
    assert transition_recovery_action(journal, locations)["action"] == "finalize_staging"
    locations = {component: "final" for component in PREDECESSOR_COMPONENT_IDS}
    assert transition_recovery_action(journal, locations)["action"] == "record_finalized"
    journal = append_transition_event(journal, action="finalized")
    assert transition_recovery_action(journal, locations)["action"] == "complete"


def test_transition_recovery_rejects_ambiguous_multiplicity(a46_3_synthetic_root):
    journal = new_transition_journal(
        _synthetic_admission_identity(a46_3_synthetic_root)
    )
    locations = {component: "source" for component in PREDECESSOR_COMPONENT_IDS}
    locations[PREDECESSOR_COMPONENT_IDS[1]] = "staging"
    with pytest.raises(ContractError, match="legal forward prefix"):
        transition_recovery_action(journal, locations)


def _synthetic_g2_spec(root):
    exact = g2_lineage_spec(selector=G2_LINEAGE_SELECTOR)
    transition_root = root / "g2-transition"
    transition_root.mkdir(parents=True)
    admission_path = transition_root / "admission.lock"
    identity = create_stable_admission_lock(admission_path)
    staging_root = transition_root / "staging"
    final_root = transition_root / "final"
    sources = {
        "formal_cpu": transition_root / "formal-cpu",
        "formal_mapping": transition_root / "formal-mapping",
        "support_classification": transition_root
        / "s10r3-support-classification.json",
        "effective_lock": transition_root
        / "s10r3-stage1-bounded-cover-entry-lock.json",
    }
    sources["formal_cpu"].mkdir()
    (sources["formal_cpu"] / "cpu.bin").write_bytes(b"cpu")
    sources["formal_mapping"].mkdir()
    (sources["formal_mapping"] / "mapping.bin").write_bytes(b"mapping")
    sources["support_classification"].write_bytes(b"support")
    sources["effective_lock"].write_bytes(b"lock")
    names = {
        "formal_cpu": "formal-cpu",
        "formal_mapping": "formal-mapping",
        "support_classification": "s10r3-support-classification.json",
        "effective_lock": "effective-lock.json",
    }
    basenames = {
        "formal_cpu": None,
        "formal_mapping": None,
        "support_classification": sources["support_classification"].name,
        "effective_lock": sources["effective_lock"].name,
    }
    components = []
    for component_id in PREDECESSOR_COMPONENT_IDS:
        inventory = component_inventory(
            sources[component_id],
            component_id,
            single_file_logical_basename=basenames[component_id],
        )
        components.append(
            G2ComponentSpec(
                component_id=component_id,
                source_root=sources[component_id].relative_to(ROOT).as_posix(),
                staging_root=(staging_root / names[component_id])
                .relative_to(ROOT)
                .as_posix(),
                final_root=(final_root / names[component_id])
                .relative_to(ROOT)
                .as_posix(),
                entry_count=inventory["entry_count"],
                regular_file_count=inventory["regular_file_count"],
                directory_count=inventory["directory_count"],
                total_bytes=inventory["total_bytes"],
                inventory_sha256=inventory["inventory_sha256"],
                single_file_logical_basename=basenames[component_id],
            )
        )
    spec = dataclass_replace(
        exact,
        admission_lock=admission_path.relative_to(ROOT).as_posix(),
        admission_identity_digest=identity["identity_digest"],
        journal=(transition_root / "journal.json").relative_to(ROOT).as_posix(),
        journal_temp=(transition_root / "journal.json.tmp")
        .relative_to(ROOT)
        .as_posix(),
        staging_capsule=staging_root.relative_to(ROOT).as_posix(),
        final_capsule=final_root.relative_to(ROOT).as_posix(),
        manifest_path=(final_root / "predecessor-manifest.json")
        .relative_to(ROOT)
        .as_posix(),
        seal_path=(transition_root / "lineage-seal.json")
        .relative_to(ROOT)
        .as_posix(),
        components=tuple(components),
    )
    return spec, identity


def test_g2_selector_is_explicit_and_historical_g1_kind_is_distinct():
    with pytest.raises(ContractError, match="explicit"):
        g2_lineage_spec(selector="predecessor_capsule_lineage")
    selected = g2_lineage_spec(selector=G2_LINEAGE_SELECTOR)
    assert selected.transition_id == "S10R3-A46.5-G2-RETIREMENT"
    assert selected.predecessor_generation_id == "S10R3-A46.3-G2"
    assert selected.successor_generation_id == "S10R3-A46.5-G3"
    assert selected.successor_lock_id == "S10R3-A46-5-EFFECTIVE-LOCK-G3"
    assert load_contract()["predecessor_capsule_lineage"]["transition"][
        "transition_id"
    ] == "S10R3-A46.3-G1-RETIREMENT"


def test_g2_cli_maps_illegal_topology_to_exact_blocked_lifecycle(
    monkeypatch, capsys
):
    runner = _load_runner_module()
    monkeypatch.setattr(
        runner,
        "execute_g2_transition",
        lambda **kwargs: (_ for _ in ()).throw(
            ContractError("synthetic illegal G2 topology")
        ),
    )
    assert runner.main(["g2-retirement", "--production"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "checkpoint_id": "S10R3",
        "action": "blocked",
        "state": "BLOCKED_TRANSITION",
        "execution_status": "CHANGES_REQUIRED",
        "scientific_outcome": "not_evaluated",
        "edge": None,
        "formal_evidence_started": False,
        "error": "synthetic illegal G2 topology",
    }


def test_g2_synthetic_forward_executor_is_idempotent_and_writes_exact_seal(
    a46_3_synthetic_root,
):
    spec, _ = _synthetic_g2_spec(a46_3_synthetic_root / "g2-success")
    first = execute_g2_transition(
        selector=G2_LINEAGE_SELECTOR,
        allow_production=False,
        durable_seal_path=spec.seal_path,
        spec=spec,
        require_frozen=False,
    )
    second = execute_g2_transition(
        selector=G2_LINEAGE_SELECTOR,
        allow_production=False,
        durable_seal_path=spec.seal_path,
        spec=spec,
        require_frozen=False,
    )
    assert first == second
    assert first["state"] == "FINALIZED"
    assert first["scientific_outcome"] == "not_evaluated"
    assert first["edge"] is None
    journal = strict_load_json(ROOT / spec.journal)
    validate_g2_transition_journal(
        journal,
        selector=G2_LINEAGE_SELECTOR,
        spec=spec,
        require_frozen=False,
    )
    assert [event["event_type"] for event in journal["events"]] == [
        "prepared",
        "component_relocated",
        "component_relocated",
        "component_relocated",
        "component_relocated",
        "staging_verified",
        "finalized",
    ]
    manifest = strict_load_json(ROOT / spec.manifest_path)
    final_roots = {
        item.component_id: ROOT / item.final_root for item in spec.components
    }
    validate_g2_capsule_manifest(
        manifest,
        selector=G2_LINEAGE_SELECTOR,
        spec=spec,
        require_frozen=False,
        component_roots=final_roots,
    )
    inventories = [
        component_inventory(
            final_roots[item.component_id],
            item.component_id,
            single_file_logical_basename=item.single_file_logical_basename,
        )
        for item in spec.components
    ]
    assert build_g2_capsule_manifest(
        inventories,
        selector=G2_LINEAGE_SELECTOR,
        spec=spec,
        require_frozen=False,
    ) == manifest
    seal = strict_load_json(ROOT / spec.seal_path)
    validate_g2_lineage_seal(
        seal,
        selector=G2_LINEAGE_SELECTOR,
        spec=spec,
        manifest=manifest,
        journal=journal,
        component_roots=final_roots,
        require_frozen=False,
    )


def test_g2_manifest_and_seal_semantic_counterfeits_fail_closed(
    a46_3_synthetic_root,
):
    spec, _ = _synthetic_g2_spec(a46_3_synthetic_root / "g2-counterfeits")
    execute_g2_transition(
        selector=G2_LINEAGE_SELECTOR,
        allow_production=False,
        durable_seal_path=spec.seal_path,
        spec=spec,
        require_frozen=False,
    )
    manifest = strict_load_json(ROOT / spec.manifest_path)
    journal = strict_load_json(ROOT / spec.journal)
    seal = strict_load_json(ROOT / spec.seal_path)
    final_roots = {
        item.component_id: ROOT / item.final_root for item in spec.components
    }

    manifest_mutations = []
    duplicate_component = copy.deepcopy(manifest)
    duplicate_component["component_inventory"][1] = copy.deepcopy(
        duplicate_component["component_inventory"][0]
    )
    manifest_mutations.append(duplicate_component)
    duplicate_entry = copy.deepcopy(manifest)
    duplicate_entry["entries"].append(copy.deepcopy(duplicate_entry["entries"][0]))
    manifest_mutations.append(duplicate_entry)
    wrong_final_path = copy.deepcopy(manifest)
    wrong_final_path["entries"][0]["final_path"] += ".counterfeit"
    manifest_mutations.append(wrong_final_path)
    for counterfeit in manifest_mutations:
        counterfeit["document_digest"] = contract_module._self_digest(
            counterfeit, "document_digest"
        )
        with pytest.raises(ContractError):
            validate_g2_capsule_manifest(
                counterfeit,
                selector=G2_LINEAGE_SELECTOR,
                spec=spec,
                require_frozen=False,
                component_roots=final_roots,
            )

    seal_mutations = []
    wrong_manifest_path = copy.deepcopy(seal)
    wrong_manifest_path["capsule_manifest"]["path"] += ".counterfeit"
    seal_mutations.append(wrong_manifest_path)
    arbitrary_journal_digest = copy.deepcopy(seal)
    arbitrary_journal_digest["terminal_journal"]["document_digest"] = "0" * 64
    seal_mutations.append(arbitrary_journal_digest)
    wrong_lifecycle = copy.deepcopy(seal)
    wrong_lifecycle["lifecycle"]["scientific_outcome"] = "positive"
    seal_mutations.append(wrong_lifecycle)
    for counterfeit in seal_mutations:
        counterfeit["document_digest"] = contract_module._self_digest(
            counterfeit, "document_digest"
        )
        with pytest.raises(ContractError):
            validate_g2_lineage_seal(
                counterfeit,
                selector=G2_LINEAGE_SELECTOR,
                spec=spec,
                manifest=manifest,
                journal=journal,
                component_roots=final_roots,
                require_frozen=False,
            )


@pytest.mark.parametrize("crash_after_rename", range(1, 6))
def test_g2_crash_resume_after_each_noreplace_boundary(
    a46_3_synthetic_root, monkeypatch, crash_after_rename
):
    spec, _ = _synthetic_g2_spec(
        a46_3_synthetic_root / f"g2-rename-crash-{crash_after_rename}"
    )
    real_rename = contract_module.rename_noreplace
    calls = 0

    def crash_once(source, destination, *, allow_production=False):
        nonlocal calls
        real_rename(source, destination, allow_production=allow_production)
        calls += 1
        if calls == crash_after_rename:
            raise OSError("synthetic crash after no-replace rename")

    monkeypatch.setattr(contract_module, "rename_noreplace", crash_once)
    with pytest.raises(OSError, match="synthetic crash"):
        execute_g2_transition(
            selector=G2_LINEAGE_SELECTOR,
            allow_production=False,
            spec=spec,
            require_frozen=False,
        )
    monkeypatch.setattr(contract_module, "rename_noreplace", real_rename)
    resumed = execute_g2_transition(
        selector=G2_LINEAGE_SELECTOR,
        allow_production=False,
        spec=spec,
        require_frozen=False,
    )
    assert resumed["state"] == "FINALIZED"
    assert calls == crash_after_rename


@pytest.mark.parametrize("crash_after_write", range(1, 8))
def test_g2_crash_resume_after_each_durable_journal_boundary(
    a46_3_synthetic_root, monkeypatch, crash_after_write
):
    spec, _ = _synthetic_g2_spec(
        a46_3_synthetic_root / f"g2-journal-crash-{crash_after_write}"
    )
    real_write = contract_module.write_g2_transition_journal
    calls = 0

    def crash_once(path, journal, **kwargs):
        nonlocal calls
        real_write(path, journal, **kwargs)
        calls += 1
        if calls == crash_after_write:
            raise OSError("synthetic crash after durable journal write")

    monkeypatch.setattr(contract_module, "write_g2_transition_journal", crash_once)
    with pytest.raises(OSError, match="synthetic crash"):
        execute_g2_transition(
            selector=G2_LINEAGE_SELECTOR,
            allow_production=False,
            spec=spec,
            require_frozen=False,
        )
    monkeypatch.setattr(contract_module, "write_g2_transition_journal", real_write)
    resumed = execute_g2_transition(
        selector=G2_LINEAGE_SELECTOR,
        allow_production=False,
        spec=spec,
        require_frozen=False,
    )
    assert resumed["state"] == "FINALIZED"
    assert calls == crash_after_write


def test_g2_relocation_fsyncs_both_parents_before_each_journal_event(
    a46_3_synthetic_root, monkeypatch
):
    spec, _ = _synthetic_g2_spec(a46_3_synthetic_root / "g2-fsync-order")
    real_rename = contract_module.rename_noreplace
    real_fsync_directory = contract_module._fsync_directory
    real_write = contract_module.write_g2_transition_journal
    observations = []

    def traced_rename(source, destination, *, allow_production=False):
        component_id = next(
            (
                item.component_id
                for item in spec.components
                if Path(source).as_posix() == item.source_root
            ),
            "final_capsule",
        )
        observations.append(("rename", component_id))
        return real_rename(
            source, destination, allow_production=allow_production
        )

    def traced_fsync_directory(path):
        observations.append(("fsync", Path(path).resolve()))
        return real_fsync_directory(path)

    def traced_write(path, journal, **kwargs):
        event = journal["events"][-1]
        observations.append(
            ("journal", event["event_type"], event["component_id"])
        )
        return real_write(path, journal, **kwargs)

    monkeypatch.setattr(contract_module, "rename_noreplace", traced_rename)
    monkeypatch.setattr(contract_module, "_fsync_directory", traced_fsync_directory)
    monkeypatch.setattr(
        contract_module, "write_g2_transition_journal", traced_write
    )
    execute_g2_transition(
        selector=G2_LINEAGE_SELECTOR,
        allow_production=False,
        spec=spec,
        require_frozen=False,
    )

    for component in spec.components:
        rename_index = observations.index(("rename", component.component_id))
        journal_index = observations.index(
            ("journal", "component_relocated", component.component_id)
        )
        fsyncs = [
            item[1]
            for item in observations[rename_index + 1 : journal_index]
            if item[0] == "fsync"
        ]
        assert fsyncs == [
            (ROOT / component.source_root).parent.resolve(),
            (ROOT / component.staging_root).parent.resolve(),
            (ROOT / component.source_root).parent.resolve(),
            (ROOT / component.staging_root).parent.resolve(),
        ]
    final_rename = observations.index(("rename", "final_capsule"))
    finalized = observations.index(("journal", "finalized", None))
    assert [
        item[1]
        for item in observations[final_rename + 1 : finalized]
        if item[0] == "fsync"
    ] == [(ROOT / spec.staging_capsule).parent.resolve()]


@pytest.mark.parametrize("fault_parent", ["source", "destination"])
def test_g2_parent_fsync_fault_cannot_precede_relocation_journal_and_resumes(
    a46_3_synthetic_root, monkeypatch, fault_parent
):
    spec, _ = _synthetic_g2_spec(
        a46_3_synthetic_root / f"g2-{fault_parent}-parent-fsync-fault"
    )
    component = spec.components[0]
    source_parent = (ROOT / component.source_root).parent.resolve()
    destination_parent = (ROOT / component.staging_root).parent.resolve()
    fault_path = source_parent if fault_parent == "source" else destination_parent
    real_rename = contract_module.rename_noreplace
    real_fsync_directory = contract_module._fsync_directory
    renamed = False
    faulted = False

    def traced_rename(source, destination, *, allow_production=False):
        nonlocal renamed
        result = real_rename(
            source, destination, allow_production=allow_production
        )
        if Path(source).as_posix() == component.source_root:
            renamed = True
        return result

    def fail_selected_parent(path):
        nonlocal faulted
        if renamed and not faulted and Path(path).resolve() == fault_path:
            faulted = True
            raise OSError(f"synthetic {fault_parent} parent fsync fault")
        return real_fsync_directory(path)

    monkeypatch.setattr(contract_module, "rename_noreplace", traced_rename)
    monkeypatch.setattr(contract_module, "_fsync_directory", fail_selected_parent)
    with pytest.raises(OSError, match=f"{fault_parent} parent fsync fault"):
        execute_g2_transition(
            selector=G2_LINEAGE_SELECTOR,
            allow_production=False,
            spec=spec,
            require_frozen=False,
        )
    journal = strict_load_json(ROOT / spec.journal)
    assert [event["event_type"] for event in journal["events"]] == ["prepared"]
    assert not (ROOT / component.source_root).exists()
    assert (ROOT / component.staging_root).exists()

    resume_order = []

    def resumed_fsync(path):
        resume_order.append(("fsync", Path(path).resolve()))
        return real_fsync_directory(path)

    monkeypatch.setattr(contract_module, "rename_noreplace", real_rename)
    monkeypatch.setattr(contract_module, "_fsync_directory", resumed_fsync)
    original_write = contract_module.write_g2_transition_journal

    def write_without_recursion(path, candidate, **kwargs):
        event = candidate["events"][-1]
        resume_order.append(
            ("journal", event["event_type"], event["component_id"])
        )
        return original_write(path, candidate, **kwargs)

    monkeypatch.setattr(
        contract_module, "write_g2_transition_journal", write_without_recursion
    )
    resumed = execute_g2_transition(
        selector=G2_LINEAGE_SELECTOR,
        allow_production=False,
        spec=spec,
        require_frozen=False,
    )
    relocated = resume_order.index(
        ("journal", "component_relocated", component.component_id)
    )
    assert [
        item[1]
        for item in resume_order[:relocated]
        if item[0] == "fsync"
    ][:2] == [source_parent, destination_parent]
    assert resumed["state"] == "FINALIZED"


def test_g2_post_rename_inventory_drift_cannot_advance_journal(
    a46_3_synthetic_root, monkeypatch
):
    spec, _ = _synthetic_g2_spec(
        a46_3_synthetic_root / "g2-post-rename-inventory-drift"
    )
    component = spec.components[0]
    real_fsync_parents = contract_module._fsync_rename_parents
    mutated = False

    def mutate_after_durable_rename(source, destination, **kwargs):
        nonlocal mutated
        result = real_fsync_parents(source, destination, **kwargs)
        if not mutated and Path(source).as_posix() == component.source_root:
            (ROOT / component.staging_root / "cpu.bin").write_bytes(b"drift")
            mutated = True
        return result

    monkeypatch.setattr(
        contract_module, "_fsync_rename_parents", mutate_after_durable_rename
    )
    with pytest.raises(ContractError):
        execute_g2_transition(
            selector=G2_LINEAGE_SELECTOR,
            allow_production=False,
            spec=spec,
            require_frozen=False,
        )

    journal = strict_load_json(ROOT / spec.journal)
    assert [event["event_type"] for event in journal["events"]] == ["prepared"]
    next_component = spec.components[1]
    assert (ROOT / next_component.source_root).exists()
    assert not (ROOT / next_component.staging_root).exists()


def test_g2_scope_inode_swap_cannot_relocate_next_component(
    a46_3_synthetic_root, monkeypatch
):
    spec, _ = _synthetic_g2_spec(
        a46_3_synthetic_root / "g2-scope-inode-swap"
    )
    first_component = spec.components[0]
    next_component = spec.components[1]
    next_source = ROOT / next_component.source_root
    swapped_source = next_source.with_name(f"{next_source.name}-swapped")
    real_write = contract_module.write_g2_transition_journal
    swapped = False

    def swap_after_first_relocation(path, journal, **kwargs):
        nonlocal swapped
        result = real_write(path, journal, **kwargs)
        event = journal["events"][-1]
        if (
            not swapped
            and event["event_type"] == "component_relocated"
            and event["component_id"] == first_component.component_id
        ):
            next_source.rename(swapped_source)
            next_source.mkdir()
            (next_source / "mapping.bin").write_bytes(b"mapping")
            swapped = True
        return result

    monkeypatch.setattr(
        contract_module, "write_g2_transition_journal", swap_after_first_relocation
    )
    with pytest.raises(ContractError, match="scope lock identity changed"):
        execute_g2_transition(
            selector=G2_LINEAGE_SELECTOR,
            allow_production=False,
            spec=spec,
            require_frozen=False,
        )

    journal = strict_load_json(ROOT / spec.journal)
    assert [
        (event["event_type"], event["component_id"])
        for event in journal["events"]
    ] == [
        ("prepared", None),
        ("component_relocated", first_component.component_id),
    ]
    assert next_source.exists()
    assert not (ROOT / next_component.staging_root).exists()


def test_g2_noreplace_fsync_and_unexpected_temp_faults_do_not_fallback(
    a46_3_synthetic_root, monkeypatch
):
    no_replace_spec, _ = _synthetic_g2_spec(
        a46_3_synthetic_root / "g2-no-replace-fault"
    )
    real_rename = contract_module.rename_noreplace
    monkeypatch.setattr(
        contract_module,
        "rename_noreplace",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ContractError("synthetic no-replace failure")
        ),
    )
    with pytest.raises(ContractError, match="no-replace failure"):
        execute_g2_transition(
            selector=G2_LINEAGE_SELECTOR,
            allow_production=False,
            spec=no_replace_spec,
            require_frozen=False,
        )
    assert all((ROOT / item.source_root).exists() for item in no_replace_spec.components)

    monkeypatch.setattr(contract_module, "rename_noreplace", real_rename)
    fsync_spec, _ = _synthetic_g2_spec(
        a46_3_synthetic_root / "g2-fsync-fault"
    )
    real_fsync_directory = contract_module._fsync_directory
    monkeypatch.setattr(
        contract_module,
        "_fsync_directory",
        lambda path: (_ for _ in ()).throw(OSError("synthetic directory fsync fault")),
    )
    with pytest.raises(OSError, match="directory fsync fault"):
        execute_g2_transition(
            selector=G2_LINEAGE_SELECTOR,
            allow_production=False,
            spec=fsync_spec,
            require_frozen=False,
        )
    assert all((ROOT / item.source_root).exists() for item in fsync_spec.components)

    monkeypatch.setattr(contract_module, "_fsync_directory", real_fsync_directory)
    temp_spec, _ = _synthetic_g2_spec(
        a46_3_synthetic_root / "g2-unexpected-temp"
    )
    temp_path = ROOT / temp_spec.journal_temp
    temp_path.write_bytes(b"unexpected")
    with pytest.raises(ContractError, match="unexpected G2 journal temp"):
        execute_g2_transition(
            selector=G2_LINEAGE_SELECTOR,
            allow_production=False,
            spec=temp_spec,
            require_frozen=False,
        )
    assert all((ROOT / item.source_root).exists() for item in temp_spec.components)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["events"][0].update({"event_type": "finalized"}),
        lambda value: value["events"][1].update({"component_id": "formal_mapping"}),
        lambda value: value["events"][1].update({"previous_event_digest": "0" * 64}),
        lambda value: value.update({"admission_lock_identity_digest": "0" * 64}),
        lambda value: value.update({"state": "FINALIZED"}),
    ],
)
def test_g2_semantically_illegal_journal_fails_closed(
    a46_3_synthetic_root, mutation
):
    spec, identity = _synthetic_g2_spec(
        a46_3_synthetic_root / f"g2-journal-{id(mutation)}"
    )
    journal = new_g2_transition_journal(
        identity["identity_digest"], selector=G2_LINEAGE_SELECTOR, spec=spec
    )
    journal = append_g2_transition_event(
        journal,
        event_type="component_relocated",
        component_id="formal_cpu",
        selector=G2_LINEAGE_SELECTOR,
        spec=spec,
    )
    mutation(journal)
    journal["document_digest"] = contract_module._self_digest(
        journal, "document_digest"
    )
    with pytest.raises(ContractError):
        validate_g2_transition_journal(
            journal,
            selector=G2_LINEAGE_SELECTOR,
            spec=spec,
            require_frozen=False,
        )


@pytest.mark.parametrize(
    "payload",
    [
        '{"x":1,"x":2}',
        '{"x":NaN}',
        '{"x":Infinity}',
        "[]",
    ],
)
def test_strict_json_rejects_duplicate_nonfinite_and_nonobject(tmp_path, payload):
    path = tmp_path / "bad.json"
    path.write_text(payload)
    with pytest.raises(ContractError):
        strict_load_json(path)


@pytest.mark.parametrize(
    "payload",
    [
        "x: 1\nx: 2\n",
        "? [a, b]\n: value\n",
        "!!python/object/apply:os.system ['false']\n",
        "- not\n- object\n",
    ],
)
def test_strict_yaml_rejects_duplicate_nonstring_unsafe_and_nonobject(tmp_path, payload):
    path = tmp_path / "bad.yaml"
    path.write_text(payload)
    with pytest.raises(ContractError):
        strict_load_yaml(path)


def test_all_twelve_embedded_schemas_are_draft7_and_strict():
    contract = load_contract()
    validate_embedded_contract_schemas(contract)
    schemas = [
        contract_module._dotted_value(contract, path)
        for path in contract_module.EMBEDDED_SCHEMA_PATHS
    ]
    assert len(schemas) == 12
    for schema in schemas:
        jsonschema.Draft7Validator.check_schema(schema)
        assert schema["additionalProperties"] is False
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft7Validator(schema).validate({"unknown": True})


@pytest.mark.parametrize("schema_index", range(12))
def test_each_embedded_schema_envelope_counterfeit_fails(schema_index):
    contract = load_contract()
    parts = contract_module.EMBEDDED_SCHEMA_PATHS[schema_index].split(".")
    schema = contract
    for part in parts:
        schema = schema[part]
    schema["additionalProperties"] = True
    with pytest.raises(ContractError, match="schema envelope drift"):
        validate_embedded_contract_schemas(contract)


@pytest.mark.parametrize(
    "kind",
    [
        "effective_lock",
        "external_phase2_audit",
        "s10r3_predecessor_capsule_manifest",
        "s10r3_predecessor_transition_journal",
        "s10r3_predecessor_lineage_seal",
        "operational_blocker",
        "mapping_worker_completion",
        "mapping_failure_batch",
    ],
)
def test_external_embedded_schema_dispatches_reject_counterfeit(kind):
    with pytest.raises(ContractError):
        validate_document({"unknown": True}, kind)


def test_historical_manifest_repair_binding_remains_read_only_in_g1_seal():
    contract = load_contract()
    binding = manifest_repair_binding(contract)
    assert binding["authority_amendment"] == "A46.4"
    assert binding["replacement_count"] == 1
    assert binding["quarantine"] is False
    assert binding["diagnostic_only"] is True
    assert binding["admissible_for_successor"] is False
    successor = successor_manifest_repair_binding(contract)
    assert successor["old_manifest_raw_sha256"] == binding["old_manifest"]["raw_sha256"]
    assert successor["corrected_manifest_raw_sha256"] == binding[
        "corrected_manifest"
    ]["raw_sha256"]
    assert successor["replacement_count"] == 1
    assert successor["lineage_seal_bound"] is True
    invalid = copy.deepcopy(contract)
    invalid["predecessor_capsule_lineage"]["seal_json_schema"]["properties"][
        "manifest_repair"
    ]["const"].update({"replacement_count": 2})
    with pytest.raises(ContractError, match="repair projection drift"):
        validate_embedded_contract_schemas(invalid)


def _a46_4_const_manifest_profile_fixture(monkeypatch):
    authority = copy.deepcopy(load_contract())
    frozen = authority["predecessor_capsule_lineage"][
        "frozen_predecessor_inventory"
    ]["components"]
    core = [
        {
            field: item[field]
            for field in contract_module._MANIFEST_COMPONENT_CORE_FIELDS
        }
        for item in frozen
    ]
    authority["predecessor_capsule_lineage"]["manifest_json_schema"] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["component_inventory", "entries", "document_digest"],
        "properties": {
            "component_inventory": {"const": copy.deepcopy(frozen)},
            "entries": {"type": "array"},
            "document_digest": {"type": "string"},
        },
    }
    monkeypatch.setattr(
        contract_module,
        "validate_capsule_manifest",
        lambda *args, **kwargs: None,
    )
    old = {
        "component_inventory": core,
        "entries": [None] * 4129,
        "document_digest": "a" * 64,
        "semantic": {"must_remain": "unchanged"},
    }
    corrected = copy.deepcopy(old)
    corrected["component_inventory"] = copy.deepcopy(frozen)
    corrected["document_digest"] = contract_module._self_digest(
        corrected, "document_digest"
    )
    corrected_bytes = contract_module.canonical_json_bytes(corrected) + b"\n"
    authority["predecessor_capsule_lineage"]["one_time_manifest_repair"][
        "corrected_manifest_identity"
    ].update(
        {
            "size_bytes": len(corrected_bytes),
            "raw_sha256": hashlib.sha256(corrected_bytes).hexdigest(),
            "document_digest": corrected["document_digest"],
        }
    )
    return authority, old, corrected, frozen


def test_a46_4_manifest_profiles_accept_exact_top_level_const_repair(
    monkeypatch,
):
    authority, old, corrected, frozen = _a46_4_const_manifest_profile_fixture(
        monkeypatch
    )
    contract_module._validate_repair_manifest_profile(
        old, branch="old", contract=authority
    )
    contract_module._validate_repair_manifest_profile(
        corrected, branch="corrected", contract=authority
    )
    mechanical = contract_module._mechanically_corrected_manifest(old, authority)
    assert mechanical == corrected
    assert mechanical["component_inventory"] == frozen
    assert {
        key: value
        for key, value in mechanical.items()
        if key not in {"component_inventory", "document_digest"}
    } == {
        key: value
        for key, value in old.items()
        if key not in {"component_inventory", "document_digest"}
    }


@pytest.mark.parametrize(
    "schema_mutation",
    [
        lambda schema, frozen: schema["properties"].update(
            {"component_inventory": {"minItems": len(frozen) + 1}}
        ),
        lambda schema, frozen: schema.update(
            {
                "properties": {"entries": {"type": "array"}},
                "allOf": [
                    {
                        "properties": {
                            "component_inventory": {
                                "const": copy.deepcopy(frozen)
                            }
                        }
                    }
                ],
            }
        ),
        lambda schema, frozen: schema["properties"].update(
            {"entries": {"const": []}}
        ),
        lambda schema, frozen: schema["properties"].update(
            {
                "component_inventory": {
                    "const": [
                        {**frozen[0], "component_id": "counterfeit"},
                        *copy.deepcopy(frozen[1:]),
                    ]
                }
            }
        ),
    ],
    ids=[
        "wrong-validator",
        "wrong-schema-path",
        "multiple-errors",
        "validator-value-drift",
    ],
)
def test_a46_4_old_manifest_profile_rejects_const_error_counterfeits(
    monkeypatch, schema_mutation
):
    authority, old, _, frozen = _a46_4_const_manifest_profile_fixture(monkeypatch)
    schema = authority["predecessor_capsule_lineage"]["manifest_json_schema"]
    schema_mutation(schema, frozen)
    with pytest.raises(
        ContractError,
        match="frozen-schema error|exact known const mismatch",
    ):
        contract_module._validate_repair_manifest_profile(
            old, branch="old", contract=authority
        )


@pytest.mark.parametrize("branch,mutation", [
    (
        "old",
        lambda document: document["component_inventory"][0].update(
            {"component_id": "counterfeit"}
        ),
    ),
    (
        "old",
        lambda document: document["semantic"].update({"must_remain": "drift"}),
    ),
    (
        "corrected",
        lambda document: document["semantic"].update({"must_remain": "drift"}),
    ),
])
def test_a46_4_manifest_profiles_reject_non_auxiliary_drift(
    monkeypatch, branch, mutation
):
    authority, old, corrected, _ = _a46_4_const_manifest_profile_fixture(
        monkeypatch
    )
    candidate = copy.deepcopy(old if branch == "old" else corrected)
    mutation(candidate)
    with pytest.raises(ContractError):
        contract_module._validate_repair_manifest_profile(
            candidate, branch=branch, contract=authority
        )


def test_registry_round_trip_typed_values_and_priority():
    registry = _registry()
    document = registry.document()
    assert document["axis_count"] == 30
    assert len(document["axis_order"]) == 30
    assert any(type(row["typed_value"]) is bool for row in document["rows"])
    assert all(
        row["source_symbol_and_blob"]["git_blob"]
        == "4968b29b5eacddc56b20c42cb4b2c1e3d8d6f406"
        for row in document["rows"]
    )
    rebuilt = AtomRegistry(axis_specs_from_registry(document))
    assert rebuilt.document() == document
    assert sorted(
        (tuple(row["deterministic_priority"]), row["atom_id"])
        for row in document["rows"]
    )


def test_registry_exact_role_flags_and_s10r3_identity():
    registry = _registry()
    assert registry.document()["checkpoint_id"] == "S10R3"
    assert registry.prelocked_atoms()
    assert registry.diagnostic_atoms() >= registry.prelocked_atoms()
    assert all(
        row["nominal_role_flags"]["prelocked_candidate"]
        for row in registry.rows
        if not row["grouped"]
        and not row["currently_weighted"]
        and row["candidate_count"] > 1
    )


def test_seed_namespace_domain_separation_and_determinism():
    seed = deterministic_seed("global", None, 0, 0)
    assert seed == deterministic_seed("global", None, 0, 0)
    assert seed != deterministic_seed("conditional", None, 0, 0)
    assert seed != deterministic_seed("global", "atom", 0, 0)
    assert seed != deterministic_seed("global", None, 1, 0)
    assert seed != deterministic_seed("global", None, 0, 1)


def test_uniform_integer_partition_boundaries():
    masses = uniform_masses(3)
    assert sum(masses) == 2**64
    axis = _registry().axes[0]
    assert categorical_index(axis, 0) == 0
    assert categorical_index(axis, masses[0] - 1) == 0
    assert categorical_index(axis, masses[0]) == 1
    assert categorical_index(axis, 2**64 - 1) == 2


def test_weighted_largest_remainder_partition_and_boundaries():
    probabilities, digest = _float32([0.25, 0.75])
    masses = weighted_masses(probabilities)
    assert masses == (2**62, 3 * 2**62)
    registry = _registry(weighted_axis=1)
    axis = registry.axes[1]
    assert axis.probabilities_raw_sha256 == digest
    assert categorical_index(axis, 2**62 - 1) == 0
    assert categorical_index(axis, 2**62) == 1


def test_conditional_chunk_has_exact_fixed_atom_and_draw_count():
    registry = _registry()
    target = sorted(registry.diagnostic_atoms())[0]
    row = registry.row_by_atom()[target]
    draws = generate_discovery_chunk(
        registry,
        stream_id="conditional/0",
        conditional_atom_id=target,
        chunk_index=0,
    )
    assert len(draws) == CHUNK_SIZE == 512
    assert all(
        draw[row["axis_name"]] == row["typed_value"]
        and type(draw[row["axis_name"]]) is type(row["typed_value"])
        for draw in draws
    )


def test_fixed_schedule_constants_and_target_cap():
    assert (GLOBAL_CHUNKS, CONDITIONAL_CHUNKS, MAX_CONDITIONAL_TARGETS) == (32, 32, 15)
    assert (MAX_TOTAL_CHUNKS, MAX_TOTAL_DRAWS) == (512, 262144)
    registry = _registry()
    state = {row["atom_id"]: SupportState.SUPPORT_UNOBSERVED for row in registry.rows}
    targets = activate_conditional_targets(registry, state)
    assert len(targets) == min(15, len(registry.diagnostic_atoms()))
    assert targets == tuple(
        row["atom_id"]
        for row in sorted(
            [
                row
                for row in registry.rows
                if row["conditional_eligibility"]
            ],
            key=lambda row: tuple(row["deterministic_priority"]),
        )[:15]
    )


def test_support_three_states_and_stochastic_zero_not_absence():
    from s10r3.support import classify_support

    registry = _registry()
    ids = [row["atom_id"] for row in registry.rows]
    classification = classify_support(
        registry,
        {ids[0]},
        {
            ids[1]: {
                "proof_kind": "finite_exhaustive",
                "proof_sha256": "a" * 64,
                "complete": True,
                "independently_validated": True,
            }
        },
    )
    assert classification[ids[0]] is SupportState.SUPPORTED_WITNESSED
    assert classification[ids[1]] is SupportState.SUPPORT_PROVEN_ABSENT
    assert classification[ids[2]] is SupportState.SUPPORT_UNOBSERVED


def test_guidance_eligibility_is_axis_local():
    registry = _registry()
    state = {row["atom_id"]: SupportState.SUPPORTED_WITNESSED for row in registry.rows}
    first = registry.rows[0]
    state[first["atom_id"]] = SupportState.SUPPORT_UNOBSERVED
    eligible = guidance_eligible_axes(registry, state)
    assert first["axis_name"] not in eligible
    assert "axis1" in eligible


def test_mandatory_atoms_are_exact_intersection():
    registry = _registry()
    state = {row["atom_id"]: SupportState.SUPPORT_UNOBSERVED for row in registry.rows}
    selected = next(iter(registry.prelocked_atoms()))
    state[selected] = SupportState.SUPPORTED_WITNESSED
    assert mandatory_mapping_atoms(registry, state) == {selected}


def test_greedy_exact_k_padding_and_sorted_final_hashes():
    registry = _registry(axis_zero_count=2)
    state = {row["atom_id"]: SupportState.SUPPORT_PROVEN_ABSENT for row in registry.rows}
    mandatory = sorted(registry.prelocked_atoms())[:3]
    for atom in mandatory:
        state[atom] = SupportState.SUPPORTED_WITNESSED
    witnesses = [
        _witness(registry, index, mandatory if index == 0 else ())
        for index in range(10)
    ]
    result = deterministic_greedy_bounded_cover(registry, state, witnesses)
    assert result.status == "selected"
    assert result.c_greedy == 1
    assert result.k == 10
    assert result.final_config_hashes == tuple(sorted(result.final_config_hashes))


def test_greedy_first_occurrence_tie_and_coverage_union():
    registry = _registry(axis_zero_count=2)
    state = {row["atom_id"]: SupportState.SUPPORT_PROVEN_ABSENT for row in registry.rows}
    atom = sorted(registry.prelocked_atoms())[0]
    state[atom] = SupportState.SUPPORTED_WITNESSED
    first = _witness(registry, 0, (), occurrence=0)
    same_config_later = Witness(
        config=first.config,
        config_hash=first.config_hash,
        atom_ids=frozenset({atom}),
        stream_rank=0,
        conditional_priority_rank=0,
        chunk_index=0,
        draw_index=99,
    )
    others = [_witness(registry, index, (), occurrence=index) for index in range(1, 10)]
    result = deterministic_greedy_bounded_cover(
        registry, state, [first, same_config_later, *others]
    )
    assert result.greedy_steps[0].config_hash == first.config_hash
    assert result.greedy_steps[0].gain == 1


def test_greedy_fewer_than_ten_is_inconclusive():
    registry = _registry()
    state = {row["atom_id"]: SupportState.SUPPORT_PROVEN_ABSENT for row in registry.rows}
    result = deterministic_greedy_bounded_cover(
        registry, state, [_witness(registry, index, ()) for index in range(9)]
    )
    assert result.failure_reason == "fresh_distinct_valid_witnesses_less_than_10"


def test_greedy_over_20_and_l_axis_disclosure():
    registry = _registry(axis_zero_count=21)
    state = {row["atom_id"]: SupportState.SUPPORT_PROVEN_ABSENT for row in registry.rows}
    axis_atoms = [
        row["atom_id"]
        for row in registry.rows
        if row["axis_index"] == 0
    ]
    for atom in axis_atoms:
        state[atom] = SupportState.SUPPORTED_WITNESSED
    witnesses = [
        _witness(registry, index, {atom})
        for index, atom in enumerate(axis_atoms)
    ]
    result = deterministic_greedy_bounded_cover(registry, state, witnesses)
    assert result.c_greedy == 21
    assert result.failure_reason == "c_greedy_greater_than_20"
    assert result.l_axis == 21


def test_ledger_append_chain_index_and_replay(tmp_path):
    lock = "a" * 64
    with RunLedger(tmp_path / "ledger", lock) as ledger:
        first = ledger.append(
            stage=Stage.GLOBAL_DISCOVERY,
            stream_id="global",
            atom_id=None,
            chunk_index=0,
            payload={"chunk": 0},
            timestamp_utc="2026-07-30T00:00:00Z",
        )
        second = ledger.append(
            stage=Stage.GLOBAL_DISCOVERY,
            stream_id="global",
            atom_id=None,
            chunk_index=1,
            payload={"chunk": 1},
            timestamp_utc="2026-07-30T00:00:01Z",
        )
        state = ledger.load_and_verify()
    assert second["previous_event_digest"] == first["event_digest"]
    assert state["index"]["event_count"] == 2
    assert state["index"]["per_stream_next_chunk"] == {"global": 2}


def test_ledger_exclusive_writer_and_chunk_boundary(tmp_path):
    root = tmp_path / "ledger"
    with RunLedger(root, "a" * 64) as first:
        with pytest.raises(LedgerError):
            with RunLedger(root, "a" * 64):
                pass
        with pytest.raises(LedgerError):
            first.append(
                stage=Stage.GLOBAL_DISCOVERY,
                stream_id="global",
                atom_id=None,
                chunk_index=1,
                payload={},
            )


@pytest.mark.parametrize("fault", ["corrupt", "reorder", "lock-drift", "tmp-alias"])
def test_ledger_faults_fail_closed(tmp_path, fault):
    root = tmp_path / "ledger"
    with RunLedger(root, "a" * 64) as ledger:
        ledger.append(
            stage=Stage.GLOBAL_DISCOVERY,
            stream_id="global",
            atom_id=None,
            chunk_index=0,
            payload={"ok": True},
            timestamp_utc="2026-07-30T00:00:00Z",
        )
    event = root / "events/000000000000.json"
    if fault == "corrupt":
        event.write_text(event.read_text().replace('"event_index":0', '"event_index":1'))
    elif fault == "reorder":
        event.rename(root / "events/000000000001.json")
    elif fault == "lock-drift":
        with pytest.raises(LedgerError):
            RunLedger(root, "b" * 64).load_and_verify()
        return
    else:
        (root / "events/000000000000.json.tmp").write_text("{}")
    with pytest.raises((LedgerError, ContractError)):
        RunLedger(root, "a" * 64).load_and_verify()


def _mapping_result(config, size):
    formocast = {field: 1 for field in FORMOCAST_FIELDS}
    formocast["macroTile"] = [64, 64, 1]
    formocast["matrixInstruction"] = [16, 16, 16, 1]
    formocast["waveGroup"] = [2, 2]
    provenance = {
        field: {
            "source": "resolved_solution",
            "source_path": f"/{field}",
            "source_sha256": "a" * 64,
        }
        for field in FORMOCAST_FIELDS
    }
    return {
        "resolved_solution": {"config": dict(config), "size": size["value"]},
        "size_mapping": dict(formocast),
        "formocast_input": formocast,
        "required_field_provenance": provenance,
    }


def test_mapping_exact_3k_ab_and_provenance_parity():
    registry = _registry()
    configs = [_config(registry, index) | {"nonce": index} for index in range(10)]
    rows_a = run_mapping_batch(pass_id="A", configs=configs, resolver=_mapping_result)
    rows_b = run_mapping_batch(pass_id="B", configs=configs, resolver=_mapping_result)
    corpus = verify_mapping_parity(rows_a, rows_b, k=10)
    assert len(rows_a) == len(rows_b) == 30
    assert corpus["parity"] is True


@pytest.mark.parametrize(
    "fault",
    ["missing-field", "guessed-provenance", "replacement", "partial", "parity"],
)
def test_mapping_forbidden_fallbacks(fault):
    registry = _registry()
    configs = [_config(registry, index) | {"nonce": index} for index in range(10)]
    if fault in {"missing-field", "guessed-provenance"}:
        result = _mapping_result(configs[0], {"size_id": "small", "value": [8, 8, 1, 128]})
        if fault == "missing-field":
            result["formocast_input"].pop(FORMOCAST_FIELDS[0])
        else:
            result["required_field_provenance"][FORMOCAST_FIELDS[0]]["source"] = ""
        with pytest.raises(MappingError):
            mapping_row(pass_id="A", config=configs[0], size_id="small", **result)
        return
    rows_a = run_mapping_batch(pass_id="A", configs=configs, resolver=_mapping_result)
    rows_b = run_mapping_batch(pass_id="B", configs=configs, resolver=_mapping_result)
    if fault == "replacement":
        rows_b[0] = {**rows_b[0], "config_hash": "b" * 64}
    elif fault == "partial":
        rows_b.pop()
    else:
        rows_b[0] = copy.deepcopy(rows_b[0])
        rows_b[0]["formocast_input"][FORMOCAST_FIELDS[0]] = 2
        body = dict(rows_b[0])
        body.pop("row_digest")
        rows_b[0]["row_digest"] = canonical_sha256(body)
    with pytest.raises(MappingError):
        verify_mapping_parity(rows_a, rows_b, k=10)


def test_size_registry_exact_panel():
    document = size_registry_document()
    assert [item["value"] for item in document["sizes"]] == [
        [8, 8, 1, 128],
        [256, 256, 1, 1024],
        [2304, 1024, 1, 214336],
    ]


def _pinned_formocast_source():
    commit = "5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39"
    path = "shared/origami/src/simulator/tensilelite/formocast_simulator.cpp"
    source = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT}", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout
    blob = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT}",
            "rev-parse",
            f"{commit}:{path}",
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    return source, blob


def test_fixture_oracle_ties_thresholds_queue_and_guard():
    fixture = fixture_document()
    validate_fixture(fixture)
    assert independent_oracle(fixture) == fixture["expected_queues"]
    assert fixture["expected_queues"]["0.0"]["queue_prefix"] == [0]
    assert fixture["expected_queues"]["0.0"]["queue_prefix"] != [0, 2]
    assert fixture["expected_queues"]["0.5"]["queue_prefix"] == [0, 2]
    assert fixture["expected_queues"]["1.0"]["queue_prefix"] == [0, 2, 3]
    assert fixture["expected_queues"]["2.0"]["queue_prefix"] == [0, 1, 2, 3]
    assert fixture["expected_queues"]["2.0"]["prediction_disabled"] is True
    assert fixture["guard_order"] == list(GUARD_ORDER)
    assert fixture["early_terminate"] == EARLY_TERMINATE
    source, blob = _pinned_formocast_source()
    validate_pinned_guard_source(source, source_blob=blob, fixture=fixture)


@pytest.mark.parametrize("guard_index", range(7))
def test_guard_deletion_faults(guard_index):
    source, blob = _pinned_formocast_source()
    fixture = fixture_document()
    anchors = [
        "if (GlobalSplitU == 0)",
        "if ((M < 128 && MT0 - M >= 16) || (N < 128 && MT1 - N >= 16))",
        "if ((M >= 128 && MT0 - M >= 32) || (N >= 128 && MT1 - N >= 32))",
        "if(problem.dataType == data_type_t::BFloat16 || problem.dataType == data_type_t::Half)",
        "if(DirectToLdsA && M < MT0)",
        "if(DirectToLdsB && N < MT1)",
        "if (PLR == 0)",
    ]
    mutated = source.replace(anchors[guard_index], "if(false)", 1)
    with pytest.raises(ConformanceError):
        validate_pinned_guard_source(mutated, source_blob=blob, fixture=fixture)


@pytest.mark.parametrize("pair_index", range(6))
def test_each_adjacent_guard_swap_rejected(pair_index):
    fixture = fixture_document()
    order = list(fixture["guard_order"])
    order[pair_index], order[pair_index + 1] = order[pair_index + 1], order[pair_index]
    fixture["guard_order"] = order
    source, blob = _pinned_formocast_source()
    with pytest.raises(ConformanceError):
        validate_pinned_guard_source(source, source_blob=blob, fixture=fixture)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda fixture: fixture["expected_guard_trace"].update({"first_true_wins": False}),
        lambda fixture: fixture["early_terminate"].update({"microSeconds": 1.0}),
        lambda fixture: fixture["early_terminate"].update({"hitRate": 1.0}),
        lambda fixture: fixture["expected_guard_trace"]["ordered_predicates"][0].update(
            {"predicate": "false"}
        ),
    ],
)
def test_guard_oracle_mutations_fail(mutator):
    fixture = fixture_document()
    mutator(fixture)
    source, blob = _pinned_formocast_source()
    with pytest.raises(ConformanceError):
        validate_pinned_guard_source(source, source_blob=blob, fixture=fixture)


def test_guard_duplicate_assignment_and_blob_faults_fail():
    source, blob = _pinned_formocast_source()
    fixture = fixture_document()
    duplicated = source.replace(
        "if (GlobalSplitU == 0)",
        "if (GlobalSplitU == 0) {}\nif (GlobalSplitU == 0)",
        1,
    )
    with pytest.raises(ConformanceError):
        validate_pinned_guard_source(duplicated, source_blob=blob, fixture=fixture)
    moved = source.replace(
        "pp.hitRate = 0;\n            return pp;",
        "return pp;\n            pp.hitRate = 0;",
        1,
    )
    with pytest.raises(ConformanceError):
        validate_pinned_guard_source(moved, source_blob=blob, fixture=fixture)
    with pytest.raises(ConformanceError):
        validate_pinned_guard_source(source, source_blob="0" * 40, fixture=fixture)


def test_native_transcript_exact_and_four_substitution_classes():
    fixture = fixture_document()
    transcript = expected_native_transcript(fixture)
    compare_native_transcript(fixture, transcript)
    for field in (
        "symbol",
        "guard_order",
        "runtime_check_solution_called",
        "queues",
    ):
        fault = copy.deepcopy(transcript)
        if field == "symbol":
            fault[field] = "proxy"
        elif field == "guard_order":
            fault[field] = list(reversed(fault[field]))
        elif field == "runtime_check_solution_called":
            fault[field] = False
        else:
            fault[field]["0.0"]["queue_prefix"] = []
        with pytest.raises(ConformanceError):
            compare_native_transcript(fixture, fault)


def test_real_native_adapter_refuses_before_locked_ready(tmp_path):
    binding = NativeBinding(
        binary_path="missing",
        binary_sha256="a" * 64,
        cpp_source_path="missing",
        cpp_source_sha256="a" * 64,
        host_adapter_path="missing",
        host_adapter_sha256="a" * 64,
        formocast_source_blob="a" * 40,
        formocast_header_blob="a" * 40,
        runtime_source_blob="a" * 40,
        runtime_header_blob="a" * 40,
    )
    adapter = PinnedNativeFormocastRuntimeAdapter(binding, repository_root=ROOT)
    with pytest.raises(NativeAdapterError, match="before LOCKED_READY"):
        adapter.invoke(
            lock={},
            fixture=fixture_document(),
            input_path=tmp_path / "input",
            output_path=tmp_path / "output",
            locked_ready=False,
        )
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    ("k", "expected"),
    [(10, (0, 4, 9)), (18, (0, 8, 17)), (20, (0, 9, 19))],
)
def test_dynamic_anchor_indices(k, expected):
    hashes = [f"{index:064x}" for index in range(k)]
    assert anchor_hashes(hashes) == tuple(hashes[index] for index in expected)


def test_exact_nine_correctness_cells():
    hashes = [f"{index:064x}" for index in range(10)]
    cells = [
        {
            "config_hash": anchor,
            "size_id": size,
            "generate": True,
            "compile": True,
            "smoke": True,
            "nonzero_correctness": True,
        }
        for anchor in anchor_hashes(hashes)
        for size in ("small", "medium", "large")
    ]
    summary = verify_correctness_cells(hashes, cells)
    assert summary["cell_count"] == 9
    with pytest.raises(CorrectnessError):
        verify_correctness_cells(hashes, cells[:-1])


def test_exact_63_noise_cv_p95_and_parent_delta_noise():
    hashes = [f"{index:064x}" for index in range(10)]
    observations = [
        {
            "config_hash": anchor,
            "size_id": size,
            "repeat": repeat,
            "quantity": 100.0 + repeat * 0.01,
        }
        for anchor in anchor_hashes(hashes)
        for size in ("small", "medium", "large")
        for repeat in range(7)
    ]
    summary = validate_noise_cells(hashes, observations)
    assert summary["observation_count"] == 63
    assert summary["stable"] is True
    assert summary["cv_p95"] <= 0.005
    assert summary["delta_noise"] >= 0
    with pytest.raises(CorrectnessError):
        validate_noise_cells(hashes, observations[:-1])


def test_state_machine_full_positive_and_terminal_separation():
    path = [
        Stage.PREIMPLEMENTATION,
        Stage.IMPLEMENTATION_READY,
        Stage.LOCKED_READY,
        Stage.GLOBAL_DISCOVERY,
        Stage.CONDITIONAL_ACTIVATION,
        Stage.SUPPORT_CLASSIFICATION_SEALED,
        Stage.BOUNDED_K_SELECTED,
        Stage.MAPPING_A,
        Stage.MAPPING_B,
        Stage.NATIVE_CONFORMANCE,
        Stage.GPU_ENVIRONMENT,
        Stage.CORRECTNESS,
        Stage.NOISE,
        Stage.DECISION_READY,
        Stage.TERMINAL_POSITIVE,
        Stage.VERIFIED_PENDING_CLOSEOUT,
    ]
    assert transition_path_is_valid(path)
    assert not transition_path_is_valid(path + [Stage.LOCKED_READY])


def test_state_machine_terminal_negative_branches_and_partial_rejection():
    assert assert_transition(Stage.MAPPING_A, Stage.TERMINAL_NEGATIVE_MAPPING)
    assert assert_transition(
        Stage.CORRECTNESS, Stage.TERMINAL_NEGATIVE_CORRECTNESS
    )
    with pytest.raises(TransitionError):
        assert_transition(Stage.TERMINAL_NEGATIVE_MAPPING, Stage.NATIVE_CONFORMANCE)
    with pytest.raises(TransitionError):
        assert_transition(Stage.TERMINAL_NEGATIVE_CORRECTNESS, Stage.NOISE)
    with pytest.raises(TransitionError):
        require_complete_unit(
            complete=False, failure_kind="mapping", current=Stage.MAPPING_A
        )


def test_harness_defect_uses_changes_required_side_exit():
    assert (
        assert_transition(Stage.MAPPING_A, Stage.CHANGES_REQUIRED)
        is Stage.CHANGES_REQUIRED
    )
    assert (
        assert_transition(Stage.CORRECTNESS, Stage.CHANGES_REQUIRED)
        is Stage.CHANGES_REQUIRED
    )


def test_cli_prelabel_validation_does_not_enter_formal_admission():
    runner = PROTOCOL_ROOT / "run_s10r3_entry.py"
    validate = subprocess.run(
        [sys.executable, str(runner), "validate-contract"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert validate.returncode == 0
    assert json.loads(validate.stdout)["status"] == "PHASE1_CONTRACT_VALID"


def test_exact_write_boundary_and_forbidden_scopes_absent():
    assert len(IMPLEMENTATION_PATHS) == 14
    assert len(set(IMPLEMENTATION_PATHS)) == 14
    assert all((ROOT / path).is_file() for path in IMPLEMENTATION_PATHS)
    assert all(not (ROOT / path).exists() for path in SUCCESSOR_OUTCOME_PATHS)
    assert all(not (ROOT / path).exists() for path in SUCCESSOR_FORMAL_SCOPES)


def test_no_retired_module_imports_or_downstream_writes():
    implementation = [
        ROOT / path
        for path in IMPLEMENTATION_PATHS
        if path.endswith((".py", ".cpp")) and "test_ductile" not in path
    ]
    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in implementation)
    assert "s10r1" not in source
    assert "s10r2" not in source
    assert "run_s11" not in source
    assert "s11-stage1-model-only-factorization-report" not in source


def test_schema_rejects_unknown_dispatch_and_unknown_registry_property():
    schema = strict_load_json(PROTOCOL_ROOT / "schemas/s10r3-entry.schema.json")
    assert "external_phase2_audit" in schema["properties"]["document_kind"]["enum"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(schema).validate(
            {"document_kind": "foreign", "document": {}}
        )
    document = _registry().document()
    document["pinned_identity_digests"] = {
        "ordered_axes_and_candidate_order": "a" * 64,
        "expanded_groups": "b" * 64,
        "search_space_map": "c" * 64,
        "baseline_weights": "d" * 64,
    }
    body = dict(document)
    body.pop("registry_digest")
    document["registry_digest"] = canonical_sha256(body)
    document["unknown"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(schema).validate(
            {"document_kind": "candidate_registry", "document": document}
        )


def _load_runner_module():
    path = PROTOCOL_ROOT / "run_s10r3_entry.py"
    spec = importlib.util.spec_from_file_location("s10r3_offline_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_formal_dispatch_routes_every_declared_handler(monkeypatch, capsys):
    runner = _load_runner_module()
    calls = []

    def bind(name):
        def handler(*arguments):
            calls.append((name, arguments))
            return {"checkpoint_id": "S10R3", "status": name}

        return handler

    commands = {
        "support-discovery": "support_discovery_command",
        "support-classification": "support_classification_command",
        "select-bounded-cover": "select_bounded_cover_command",
        "native-conformance": "native_conformance_command",
        "gpu-environment": "gpu_environment_command",
        "correctness": "correctness_command",
        "noise": "noise_command",
        "decision": "decision_command",
    }
    for cli_name, function_name in commands.items():
        monkeypatch.setattr(runner, function_name, bind(cli_name))
        assert runner.main([cli_name, "--lock", "LOCK"]) == 0
        assert json.loads(capsys.readouterr().out)["status"] == cli_name
    monkeypatch.setattr(runner, "mapping_command", bind("mapping"))
    assert runner.main(["mapping", "--pass-id", "A", "--lock", "LOCK"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "mapping"
    monkeypatch.setattr(runner, "reproduction_command", bind("reproduction"))
    assert (
        runner.main(
            [
                "reproduction",
                "--lock",
                "LOCK",
                "--output",
                "REPRODUCTION",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "reproduction"
    assert len(calls) == 10


def test_formal_stage_projection_enforces_order_and_terminal_separation():
    runner = _load_runner_module()
    present = set()
    assert runner.formal_stage_projection(present) == "LOCKED_READY"
    expected = [
        ("support", "SUPPORT_CLASSIFICATION_SEALED"),
        ("selection", "BOUNDED_K_SELECTED"),
        ("mapping_a", "MAPPING_A"),
        ("mapping_b", "MAPPING_B_PENDING_PARITY"),
        ("mapping", "MAPPING_B"),
        ("native", "NATIVE_CONFORMANCE"),
        ("gpu_environment", "GPU_ENVIRONMENT"),
        ("correctness", "CORRECTNESS"),
        ("noise", "NOISE"),
    ]
    for artifact, stage in expected:
        present.add(artifact)
        assert runner.formal_stage_projection(present) == stage
    present.add("decision")
    assert runner.formal_stage_projection(present) == "TERMINAL"
    present.add("reproduction")
    assert runner.formal_stage_projection(present) == "VERIFIED_PENDING_CLOSEOUT"
    with pytest.raises(runner.RunnerError):
        runner.formal_stage_projection({"mapping_b"})
    with pytest.raises(runner.RunnerError):
        runner.formal_stage_projection({"foreign"})


def test_atomic_orphan_adoption_and_mismatch_rejection(tmp_path):
    runner = _load_runner_module()
    path = tmp_path / "artifact.json"
    document = runner._raw_document("synthetic", {"value": 1})
    assert runner._write_or_match_json(path, document) is False
    assert runner._write_or_match_json(path, document) is True
    with pytest.raises(runner.RunnerError):
        runner._write_or_match_json(
            path, runner._raw_document("synthetic", {"value": 2})
        )
    assert runner._load_raw_document(path, "synthetic") == document


def test_formal_schema_rejects_unknown_top_level_and_accepts_strict_identity():
    schema = strict_load_json(PROTOCOL_ROOT / "schemas/s10r3-entry.schema.json")
    document = {
        "document_kind": "decision",
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "contract_raw_sha256": "a" * 64,
        "effective_lock_raw_sha256": "b" * 64,
        "effective_lock_self_sha256": "c" * 64,
        "source_registry_fixture_digests": {
            "candidate_registry": "d" * 64,
            "size_registry": "e" * 64,
            "sentinel_fixture": "f" * 64,
        },
        "raw_children": [],
        "upstream_identities": {"noise": "1" * 64},
        "payload": {
            "scientific_outcome": "positive",
            "edge": "S11",
            "terminal": True,
        },
        "document_digest": "2" * 64,
    }
    validator = jsonschema.Draft7Validator(schema)
    validator.validate({"document_kind": "decision", "document": document})
    document["unknown"] = True
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({"document_kind": "decision", "document": document})


@pytest.mark.parametrize(
    ("outcome", "criterion", "failure_id", "edge"),
    [
        ("positive", "S1_ENTRY_GO", None, "S11"),
        ("negative", "S1_ENTRY_BLOCKED", "FT-BLOCKED-MAPPING", None),
        ("negative", "S1_ENTRY_BLOCKED", "FT-BLOCKED-CORRECTNESS", None),
        ("inconclusive", "FT-INCONCLUSIVE", "noise_instability", None),
    ],
)
def test_terminal_report_projection_covers_all_frozen_branches(
    outcome, criterion, failure_id, edge
):
    runner = _load_runner_module()
    decision = {
        "document_digest": "a" * 64,
        "payload": {
            "scientific_outcome": outcome,
            "criterion": criterion,
            "failure_id": failure_id,
            "edge": edge,
        },
    }
    report = runner._formal_report_bytes(decision).decode()
    assert outcome in report
    assert criterion in report
    assert "does not claim checkpoint completion" in report


def test_native_fixture_input_is_exact_and_score_blind():
    runner = _load_runner_module()
    fixture = fixture_document()
    payload = runner._native_fixture_input(fixture)
    lines = payload.decode("ascii").splitlines()
    assert lines[0] == "4 4"
    assert lines[1:5] == ["0.0 0.0", "0.5 0.5", "1.0 1.0", "2.0 2.0"]
    assert len(lines) == 9
    assert all(len(line.split()) == 40 for line in lines[5:])
    assert b"oracle_microseconds" not in payload


def test_formal_runner_has_no_fail_closed_placeholder_dispatch():
    source = (PROTOCOL_ROOT / "run_s10r3_entry.py").read_text(encoding="utf-8")
    assert "_formal_not_started" not in source
    assert "requires its complete prior-phase durable projection" not in source
    for symbol in (
        "support_discovery_command",
        "support_classification_command",
        "select_bounded_cover_command",
        "mapping_command",
        "native_conformance_command",
        "gpu_environment_command",
        "correctness_command",
        "noise_command",
        "decision_command",
        "reproduction_command",
    ):
        assert f"def {symbol}" in source
