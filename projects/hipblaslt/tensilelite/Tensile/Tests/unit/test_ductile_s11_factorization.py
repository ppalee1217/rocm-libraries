# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Deterministic synthetic and authority tests for the S11 pre-evidence machinery."""

from __future__ import annotations

from dataclasses import replace
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[6]
PROTOCOL = ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1"
sys.path.insert(0, str(PROTOCOL))

from s11.canonical import atomic_write_json, canonical_json_bytes, canonical_sha256, sha256_file
from s11.contract import (
    APPROVED_IMPLEMENTATION_PARENT_COMMIT,
    BASE_SHA256,
    DEFAULT_CONTRACT_PATH,
    DEFAULT_LOCK_PATH,
    DEFAULT_PREIMPLEMENTATION_LOCK_PATH,
    DEFAULT_REVISION_PATH,
    DEFAULT_SCHEMA_PATH,
    EXPECTED_IMPLEMENTATION_WHITELIST,
    FORMAL_COMMANDS,
    REVISION_SHA256,
    TOOLCHAIN_KEYS,
    ContractError,
    _git_commit_hash,
    _validate_toolchain,
    admit_formal_command,
    expected_qualification_fingerprint,
    load_contract,
    materialize_pinned_integration,
    preflight,
    validate_implementation_commit_topology,
    validate_lock_commit_topology,
    validate_contract,
)
from s11.decision import DecisionError, branch_artifact_policy, decide, decide_from_artifacts
from s11.guidance import (
    GuidanceError,
    construct_gene_probabilities,
    deterministic_nonidentity_shuffle,
    float32_inverse_cost_roundtrip,
    guidance_bundle_identity,
    normalized_entropy,
    select_global_lambda,
)
from s11.ledger import ChunkLedger, LedgerError
from s11.native_adapter import (
    NativeAdapterError,
    NativeFormocastAdapter,
    SCALAR_MAPPING_FIELDS,
    build_native_formocast_helper,
    derive_sealed_execution_argv,
)
from s11.populations import build_populations, global_mean, value_cell
from s11.qualification import (
    PinnedQualificationWorker,
    QualificationAttempt,
    QualificationError,
    evaluate_attempts,
    value_preservation_state,
)
from s11.registry import RegistryError, extract_registry, verify_structural_registry
from s11.sampling import (
    PERSISTENT_VALIDATOR_PROTOCOL,
    PinnedValidatorAdapter,
    SamplingError,
    StreamSpec,
    canonical_prefix,
    derive_persistent_validator_argv,
    expand_compact_chunk,
    sample_chunk,
    sample_complete_stream,
    stream_terminal_state,
    _axis_choice_widths,
)
from s11.statistics import (
    DECISION_LOSS_MARGIN,
    DECISION_LOSS_SENSITIVITY_MIN,
    HALF_CATEGORICAL_PROJECTION_FIELDS,
    HALF_TUPLE_FIELDS,
    StatisticsError,
    alpha0_shrinkage_sensitivity,
    arm_sensitivity_theta,
    bootstrap_stability,
    decision_loss_panel,
    emitted_prior_reconstruction,
    gene_marginals,
    joint_permutation_test,
    midrank_latency_benefits,
    per_size_latency_margin,
    query_terminal_global_ecdf,
    run_decision_loss_simulation,
    semantic_half_stability,
    size_direction,
    survivorship_yield,
    type7_quantile,
)
from s11.workflow import (
    SyntheticInterruption,
    WorkflowError,
    _allowed_output,
    _firewall,
    _projection_marker,
    _remote_delivery_snapshot,
    _render_projection_document,
    _validate_projection_hunk,
    _require_workspace_descendant,
    _validate_raw_stream,
    build_analysis_and_guidance,
    build_artifact_reproduction,
    run_resumable_stream,
    seal_stage_artifact,
    verify_closeout,
)
from s11.workload_envelope import build_workload_envelope


ACTUAL_YAML = PROTOCOL / "inputs/s10-generated.yaml"
STRUCTURAL = PROTOCOL / "manifests/s11-structural-registry.json"
LOCK_ID = "a" * 64


def tiny_registry() -> dict:
    candidates = [
        {"type": "int", "value": "0"},
        {"type": "int", "value": "1"},
    ]
    ids = [canonical_sha256({"index": index}) for index in range(2)]
    return {
        "eligible_genes": [
            {
                "gene": "G",
                "candidates": candidates,
                "candidate_ids": ids,
                "baseline_probabilities": [0.5, 0.5],
            }
        ]
    }


def decision_inputs(**updates: object) -> dict:
    result = {
        "integrity_failure": False,
        "label_leakage": False,
        "qualification_discordant_or_partial": False,
        "blocked_mapping_exact_allowlisted": False,
        "bounded_family_complete": True,
        "material_stochastic_shortage": False,
        "global_uexec_count": 256,
        "stable_guided_gene_count": 1,
        "positive_global_lambda": True,
        "all_positive_gates_pass": True,
    }
    result.update(updates)
    return result


def attempt(role: str, root: str, **updates: object) -> QualificationAttempt:
    values = {
        "role": role,
        "workspace_root_id": root,
        "complete": True,
        "result": "accepted",
        "semantic_identity": "b" * 64,
        "qualification_fingerprint": "c" * 64,
        "reason_code": "complete_normal_generation_and_compile",
        "no_guess": True,
        "solution_sha256": "1" * 64,
        "size_mapping_sha256": "2" * 64,
        "kernel_association_sha256": "3" * 64,
        "occurrence_ids_sha256": "4" * 64,
        "alias_fanout_sha256": "5" * 64,
        "transcript_sha256": "6" * 64,
    }
    values.update(updates)
    return QualificationAttempt(**values)


def population_row(
    occurrence: str,
    *,
    frame: str = "global",
    candidate: str = "v0",
    identity: str = "id0",
    executable: bool = True,
    scored: bool = True,
    credit: bool = True,
    benefit: float = 0.5,
) -> dict:
    return {
        "occurrence_id": occurrence,
        "frame": frame,
        "candidate_ids": {"G": candidate},
        "raw_valid": True,
        "canonical_credit": credit,
        "qualification_state": "executable" if executable else "execution_attrition",
        "semantic_identity": identity,
        "scores_complete_finite": scored,
        "benefit": benefit,
    }


def statistical_rows() -> tuple[list[dict], dict[str, list[dict]], dict[str, dict[str, float]]]:
    global_rows = [
        {"semantic_identity": "g0", "candidate_ids": {"G": "a"}, "latencies": [1.0, 1.0, 1.0]},
        {"semantic_identity": "g1", "candidate_ids": {"G": "a"}, "latencies": [2.0, 2.0, 2.0]},
        {"semantic_identity": "g2", "candidate_ids": {"G": "b"}, "latencies": [3.0, 3.0, 3.0]},
        {"semantic_identity": "g3", "candidate_ids": {"G": "b"}, "latencies": [4.0, 4.0, 4.0]},
    ]
    conditional = {
        "a": [
            {"semantic_identity": "ca0", "latencies": [1.2, 1.2, 1.2]},
            {"semantic_identity": "ca1", "latencies": [1.8, 1.8, 1.8]},
        ],
        "b": [
            {"semantic_identity": "cb0", "latencies": [3.2, 3.2, 3.2]},
            {"semantic_identity": "cb1", "latencies": [3.8, 3.8, 3.8]},
        ],
    }
    global_scored = query_terminal_global_ecdf(global_rows, global_rows)
    conditional_scored = {
        candidate_id: query_terminal_global_ecdf(global_rows, rows)
        for candidate_id, rows in conditional.items()
    }
    global_mean_value = sum(row["benefit"] for row in global_scored) / len(global_scored)
    cells = {"a": [], "b": []}
    for source, scored in zip(global_rows, global_scored):
        cells[source["candidate_ids"]["G"]].append(scored["benefit"])
    for candidate_id in cells:
        cells[candidate_id].extend(row["benefit"] for row in conditional_scored[candidate_id])
    observed = {"G": gene_marginals(cells, global_mean=global_mean_value)}
    return global_rows, conditional, observed


def ledger_metadata(index: int, accepted: int = 1) -> dict:
    return {
        "nominal_slots": 2, "accepted_count": accepted,
        "disposition_counts": {
            "accepted": accepted, "validator_rejected": 2 - accepted,
            "validator_exception": 0, "malformed_validator_result": 0,
        },
        "chunk_relative_path": f"chunks/{index:012d}.json",
        "chunk_byte_length": 123,
        "chunk_file_sha256": canonical_sha256({"file": index}),
        "chunk_semantic_sha256": canonical_sha256({"semantic": index}),
    }


def test_contract_resolves_strict_ordered_base_plus_r2() -> None:
    assert sha256_file(DEFAULT_CONTRACT_PATH) == BASE_SHA256
    assert sha256_file(DEFAULT_REVISION_PATH) == REVISION_SHA256
    contract = load_contract()
    assert contract["_active_contract"]["ordered_raw_sha256"] == [BASE_SHA256, REVISION_SHA256]
    assert contract["statistics"]["half_stability"]["exact_tuple"][-2:] == [
        "per_size_and_aggregate_direction", "each_model_test_result"
    ]
    assert contract["fixed_frame_analysis"]["semantic_half_tuple"][-2:] == [
        "per_size_and_aggregate_direction", "each_model_test_result"
    ]


def test_contract_duplicate_key_and_unknown_field_fail_closed(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.yaml"
    duplicate.write_text("document_kind: x\ndocument_kind: y\n", encoding="utf-8")
    with pytest.raises(ContractError, match="duplicate YAML key"):
        load_contract(duplicate, verify_hashes=False)
    unknown = tmp_path / "unknown.yaml"
    unknown.write_text(DEFAULT_CONTRACT_PATH.read_text(encoding="utf-8") + "unknown_s11_field: true\n", encoding="utf-8")
    with pytest.raises(ContractError, match="schema failure"):
        validate_contract(unknown, DEFAULT_SCHEMA_PATH, verify_hashes=False, verify_base_authorities=False)


def test_revision_patch_order_value_and_duplicate_fail_closed(tmp_path: Path) -> None:
    changed = tmp_path / "revision.yaml"
    changed.write_text(
        DEFAULT_REVISION_PATH.read_text(encoding="utf-8").replace(
            "values: [per_size_and_aggregate_direction, each_model_test_result]",
            "values: [each_model_test_result, per_size_and_aggregate_direction]",
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ContractError, match="patch order"):
        load_contract(revision_path=changed, verify_hashes=False)
    duplicate_base = tmp_path / "base.yaml"
    duplicate_base.write_text(
        DEFAULT_CONTRACT_PATH.read_text(encoding="utf-8").replace(
            "      - trust_states", "      - per_size_and_aggregate_direction\n      - trust_states", 1
        ),
        encoding="utf-8",
    )
    with pytest.raises(ContractError, match="duplicates tuple"):
        load_contract(duplicate_base, verify_hashes=False)


def test_prelock_unknown_field_and_hash_drift_fail_closed(tmp_path: Path) -> None:
    prelock = json.loads(DEFAULT_PREIMPLEMENTATION_LOCK_PATH.read_text(encoding="utf-8"))
    prelock["unknown"] = True
    changed = tmp_path / "prelock.json"
    changed.write_bytes(canonical_json_bytes(prelock) + b"\n")
    with pytest.raises(ContractError, match="schema changed"):
        load_contract(preimplementation_lock_path=changed, verify_hashes=False)
    copied = tmp_path / "contract.yaml"
    copied.write_bytes(DEFAULT_CONTRACT_PATH.read_bytes() + b"\n")
    with pytest.raises(ContractError, match="raw SHA-256"):
        load_contract(copied)


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=repo, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.decode("utf-8").strip()


def _topology_repository(
    root: Path, *, extra: bool = False, missing: bool = False,
) -> tuple[str, str, list[dict[str, str]], str]:
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "s11@example.invalid")
    _git(root, "config", "user.name", "S11 Test")
    _git(root, "config", "commit.gpgsign", "false")
    (root / "base.txt").write_text("P0b\n", encoding="utf-8")
    _git(root, "add", "base.txt")
    _git(root, "commit", "-q", "-m", "P0b")
    parent = _git(root, "rev-parse", "HEAD")
    bindings = []
    paths = list(EXPECTED_IMPLEMENTATION_WHITELIST)
    if missing:
        paths.pop()
    for index, relative in enumerate(paths):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"implementation {index}\n", encoding="utf-8")
        bindings.append({"path": relative, "sha256": sha256_file(path)})
    manifest_relative = (
        "study_docs/research/ductile-origami-warmstart/protocol/v1/"
        "manifests/s11-implementation.json"
    )
    manifest = root / manifest_relative
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("manifest\n", encoding="utf-8")
    if extra:
        (root / "extra.txt").write_text("extra\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "P1")
    implementation = _git(root, "rev-parse", "HEAD")
    return parent, implementation, bindings, manifest_relative


def test_commit_topology_exact_p1_p2_clone_and_terminal_descendant(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    parent, implementation, bindings, manifest_relative = _topology_repository(repo)
    validate_implementation_commit_topology(
        repo, implementation_commit=implementation,
        implementation_parent_commit=parent, manifest_relative_path=manifest_relative,
        implementation_bindings=bindings, require_clean_head=True,
        approved_parent_commit=parent,
    )
    lock_relative = (
        "study_docs/research/ductile-origami-warmstart/protocol/v1/"
        "locks/s11-stage1-model-only-factorization-lock.json"
    )
    lock = repo / lock_relative
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("lock\n", encoding="utf-8")
    _git(repo, "add", lock_relative)
    _git(repo, "commit", "-q", "-m", "P2 lock only")
    p2 = _git(repo, "rev-parse", "HEAD")
    assert validate_lock_commit_topology(
        repo, implementation_commit=implementation,
        lock_relative_path=lock_relative,
    ) == p2
    (repo / "terminal.txt").write_text("terminal\n", encoding="utf-8")
    _git(repo, "add", "terminal.txt")
    _git(repo, "commit", "-q", "-m", "terminal")
    assert validate_lock_commit_topology(
        repo, implementation_commit=implementation,
        lock_relative_path=lock_relative,
    ) == p2
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "-q", str(repo), str(clone)], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    validate_implementation_commit_topology(
        clone, implementation_commit=implementation,
        implementation_parent_commit=parent, manifest_relative_path=manifest_relative,
        implementation_bindings=bindings, approved_parent_commit=parent,
    )
    assert validate_lock_commit_topology(
        clone, implementation_commit=implementation,
        lock_relative_path=lock_relative,
    ) == p2


def test_commit_topology_wrong_parent_extra_missing_blob_dirty_unreachable_and_merge(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "valid"
    parent, implementation, bindings, manifest_relative = _topology_repository(repo)
    with pytest.raises(ContractError, match="approved P0b"):
        validate_implementation_commit_topology(
            repo, implementation_commit=implementation,
            implementation_parent_commit="0" * 40,
            manifest_relative_path=manifest_relative,
            approved_parent_commit=parent,
        )
    wrong_blob = copy.deepcopy(bindings)
    wrong_blob[0]["sha256"] = "0" * 64
    with pytest.raises(ContractError, match="blob"):
        validate_implementation_commit_topology(
            repo, implementation_commit=implementation,
            implementation_parent_commit=parent,
            manifest_relative_path=manifest_relative,
            implementation_bindings=wrong_blob, approved_parent_commit=parent,
        )
    (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(ContractError, match="clean"):
        validate_implementation_commit_topology(
            repo, implementation_commit=implementation,
            implementation_parent_commit=parent,
            manifest_relative_path=manifest_relative,
            require_clean_head=True, approved_parent_commit=parent,
        )
    (repo / "dirty.txt").unlink()
    _git(repo, "checkout", "-q", parent)
    with pytest.raises(ContractError, match="reachable"):
        validate_implementation_commit_topology(
            repo, implementation_commit=implementation,
            implementation_parent_commit=parent,
            manifest_relative_path=manifest_relative,
            approved_parent_commit=parent,
        )

    for label, options in (("extra", {"extra": True}), ("missing", {"missing": True})):
        bad = tmp_path / label
        bad_parent, bad_impl, _, bad_manifest = _topology_repository(bad, **options)
        with pytest.raises(ContractError, match="19-plus-manifest"):
            validate_implementation_commit_topology(
                bad, implementation_commit=bad_impl,
                implementation_parent_commit=bad_parent,
                manifest_relative_path=bad_manifest,
                approved_parent_commit=bad_parent,
            )

    merge_repo = tmp_path / "merge"
    merge_parent, merge_impl, _, merge_manifest = _topology_repository(merge_repo)
    _git(merge_repo, "checkout", "-q", "-b", "side", merge_parent)
    (merge_repo / "side.txt").write_text("side\n", encoding="utf-8")
    _git(merge_repo, "add", "side.txt")
    _git(merge_repo, "commit", "-q", "-m", "side")
    _git(merge_repo, "checkout", "-q", merge_impl)
    _git(merge_repo, "merge", "-q", "--no-ff", "side", "-m", "merge")
    merge_commit = _git(merge_repo, "rev-parse", "HEAD")
    with pytest.raises(ContractError, match="exactly the sealed parent"):
        validate_implementation_commit_topology(
            merge_repo, implementation_commit=merge_commit,
            implementation_parent_commit=merge_impl,
            manifest_relative_path=merge_manifest,
            approved_parent_commit=merge_impl,
        )


def test_fixed_implementation_parent_authority() -> None:
    assert APPROVED_IMPLEMENTATION_PARENT_COMMIT == (
        "e7b2c33d91a127e498e3f2c2440769b188efedfd"
    )


def test_git_commit_hash_accepts_only_lowercase_sha1_shape() -> None:
    assert _git_commit_hash(APPROVED_IMPLEMENTATION_PARENT_COMMIT)
    for malformed in (
        "",
        "a" * 64,
        "a" * 39,
        "a" * 41,
        APPROVED_IMPLEMENTATION_PARENT_COMMIT.upper(),
        0,
    ):
        assert not _git_commit_hash(malformed)


def test_schema_contract_and_preflight_are_current() -> None:
    contract = validate_contract()
    assert contract["schedule"]["global"]["complete_chunks"] == 65536
    result = preflight()
    assert result["effective_lock_absent"] is True
    assert result["formal_admission_enabled"] is False
    assert result["structural_registry_verified"] is True


@pytest.mark.parametrize("command", FORMAL_COMMANDS)
def test_every_formal_command_is_denied_without_effective_lock(command: str) -> None:
    with pytest.raises(ContractError, match="effective lock is absent"):
        admit_formal_command(command)


def test_exact_reproduce_and_verify_closeout_cli_shapes_parse_without_request(tmp_path: Path) -> None:
    runner = PROTOCOL / "run_s11_factorization.py"
    reproduction_output = tmp_path / "SHOULD-NOT-EXIST-reproduction.json"
    reproduce = subprocess.run(
        [sys.executable, str(runner), "reproduce", "--output", str(reproduction_output)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert reproduce.returncode != 0
    assert b"effective lock is absent" in reproduce.stderr
    assert b"--request" not in reproduce.stderr
    assert not reproduction_output.exists()

    closeout_output = tmp_path / "SHOULD-NOT-EXIST-closeout.json"
    closeout = subprocess.run(
        [
            sys.executable, str(runner), "verify-closeout", "--commit", "HEAD",
            "--output", str(closeout_output),
        ],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert closeout.returncode != 2
    assert b"unrecognized arguments" not in closeout.stderr
    assert b"--request" not in closeout.stderr
    assert not closeout_output.exists()


def test_structural_registry_replays_original_s10_only() -> None:
    structural = verify_structural_registry(repository_root=ROOT)
    assert structural["problem_sizes"] == [[8, 8, 1, 128], [256, 256, 1, 1024], [2304, 1024, 1, 214336]]
    assert structural["extraction"]["source_raw_row_count"] == 17
    assert structural["extraction"]["source_distinct_count"] == 16
    assert structural["extraction"]["selection_indices"] == [0, 7, 15]
    assert structural["fixed_runtime"] == {
        "actual_reducer": "max", "soo": False, "weight_beta": 0.25,
        "weight_beta_origin": "pinned Ductile config default; actual YAML omits the field",
    }


def test_residual_registry_order_counts_alias_ids_and_protected_hashes() -> None:
    registry = extract_registry(ACTUAL_YAML)
    assert registry["registry_sha256"] == "e767e2eb5f9ead55b1a38fb174349dc2fdbb2fdf744919b8f99db499c727b848"
    assert len(registry["eligible_genes"]) == 27
    assert len(registry["conditional_streams"]) == 101
    assert registry["eligible_genes"][0]["gene"] == "DepthU"
    assert registry["protected_groups_sha256"] == "0526a9b3c1d8a1bbe1db2cb03616bfda6e5a1f2dfad3826c0747d8dcb3ab9140"
    assert registry["protected_weights_sha256"] == "56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f"
    assert registry["actual_reducer"] == "max"


def test_production_source_contains_no_retired_runtime_dependency() -> None:
    source_paths = [
        path for path in (PROTOCOL / "s11").glob("*.py")
        if path.name not in {"workflow.py"}
    ] + [PROTOCOL / "run_s11_factorization.py"]
    joined = "\n".join(path.read_text(encoding="utf-8") for path in source_paths).lower()
    for token in ("s10r4-size-registry", "s10r4/", "b01/", "b02/", "b03/", "b04/", "b05/", "b06/"):
        assert token not in joined


def test_sampling_one_worker_many_worker_and_resume_parity() -> None:
    spec = StreamSpec("global", target_accepted=4, hard_cap_chunks=4, nominal_slots_per_chunk=8)
    one = sample_complete_stream(tiny_registry(), spec, master_nonce="1" * 64, validator=lambda _: True, workers=1)
    many = sample_complete_stream(tiny_registry(), spec, master_nonce="1" * 64, validator=lambda _: True, workers=3)
    assert one == many
    assert sample_complete_stream(
        tiny_registry(), spec, master_nonce="1" * 64, validator=lambda _: True,
        workers=2, first_missing_chunk=2,
    ) == one[2:]
    assert len(one) == spec.hard_cap_chunks


def test_sampling_fixed_cap_never_target_stops_and_prefix_zero_credit() -> None:
    spec = StreamSpec("global", target_accepted=2, hard_cap_chunks=2, nominal_slots_per_chunk=4)
    chunks = sample_complete_stream(tiny_registry(), spec, master_nonce="2" * 64, validator=lambda _: True)
    prefix = canonical_prefix(
        chunks, 2, registry=tiny_registry(), spec=spec,
        master_nonce="2" * 64, expected_lock_sha256="0" * 64,
    )
    assert prefix["accepted_observed"] == 8
    assert prefix["accepted_credited"] == 2
    assert prefix["zero_credit_occurrence_count"] == 6
    assert len(prefix["acceptance_ledger"]) == 2
    assert all(row["canonical_credit"] for row in prefix["acceptance_ledger"])
    accepted_ids = [
        occurrence_id
        for chunk in chunks
        for occurrence_id in expand_compact_chunk(
            chunk, registry=tiny_registry(), spec=spec, master_nonce="2" * 64,
            expected_lock_sha256="0" * 64,
        )["accepted_occurrence_ids"]
    ]
    materialized_ledger = [
        {
            "acceptance_index": index,
            "occurrence_id": occurrence_id,
            "canonical_credit": index < 2,
            "downstream_credit": "full" if index < 2 else "zero_diagnostic_only",
        }
        for index, occurrence_id in enumerate(accepted_ids)
    ]
    assert prefix["acceptance_ledger_sha256"] == canonical_sha256(materialized_ledger)
    assert prefix["zero_credit_acceptance_ledger_sha256"] == canonical_sha256(
        materialized_ledger[2:]
    )
    assert stream_terminal_state(
        stream_kind="global", accepted_credited=2, chunks_committed=1,
        target_accepted=2, hard_cap_chunks=2,
    ) == "CANONICAL_PREFIX_COMPLETE_CONTINUE_FIXED_CAP"
    assert stream_terminal_state(
        stream_kind="global", accepted_credited=2, chunks_committed=2,
        target_accepted=2, hard_cap_chunks=2,
    ) == "CAP_COMPLETE_CANONICAL"


def test_sampling_chunk_index_and_test_cap_cannot_enter_formal_admission() -> None:
    spec = StreamSpec("global", target_accepted=1, hard_cap_chunks=1, nominal_slots_per_chunk=1)
    with pytest.raises(SamplingError, match="outside"):
        sample_chunk(tiny_registry(), spec, master_nonce="3" * 64, chunk_index=1, validator=lambda _: True)
    with pytest.raises(ContractError):
        admit_formal_command("global-discovery", lock_path=DEFAULT_LOCK_PATH.with_name("absent-test-lock.json"))


def test_sampling_uint16_codec_covers_candidate_indices_above_uint8() -> None:
    candidates = [{"type": "int", "value": str(index)} for index in range(300)]
    candidate_ids = [canonical_sha256({"index": index}) for index in range(300)]
    registry = {
        "eligible_genes": [{
            "gene": "wide", "candidates": candidates,
            "candidate_ids": candidate_ids,
            "baseline_probabilities": [1.0 / 300] * 300,
        }]
    }
    spec = StreamSpec(
        "conditional/wide/299", target_accepted=1, hard_cap_chunks=1,
        nominal_slots_per_chunk=1, fixed_gene="wide",
        fixed_candidate_id=candidate_ids[299],
    )
    chunk = sample_chunk(
        registry, spec, master_nonce="9" * 64, chunk_index=0,
        validator=lambda _: True,
    )
    assert chunk["choice_codec"] == "axis-uint8-or-uint16-be-slot-major-base64-v1"
    assert chunk["axis_choice_width_bytes"] == [2]
    expanded = expand_compact_chunk(
        chunk, registry=registry, spec=spec, master_nonce="9" * 64,
        expected_lock_sha256="0" * 64,
    )
    assert expanded["slots"][0]["raw_configuration"]["wide"] == 299
    changed_width = copy.deepcopy(chunk)
    changed_width["axis_choice_width_bytes"] = [1]
    changed_width_body = dict(changed_width)
    changed_width_body.pop("chunk_sha256")
    changed_width["chunk_sha256"] = canonical_sha256(changed_width_body)
    with pytest.raises(SamplingError, match="axis candidate width"):
        expand_compact_chunk(
            changed_width, registry=registry, spec=spec,
            master_nonce="9" * 64, expected_lock_sha256="0" * 64,
        )
    with pytest.raises(SamplingError, match="cardinality"):
        _axis_choice_widths([{"candidate_ids": [None] * 65537}])


def _fake_persistent_validator(
    tmp_path: Path, worker_count: int, provenance_variant: str = "valid"
) -> PinnedValidatorAdapter:
    worker = tmp_path / f"validator-{worker_count}-{provenance_variant}.py"
    worker.write_text(
        """import hashlib, json, sys
provenance = {
    "executable_sha256": sys.argv[1],
    "validator_source_sha256": sys.argv[2],
    "normal_valid_fn_path": True,
    "valid_fn": "Tensile.backends.ductile_backend._validate_solution",
    "proxy_or_substitution": False,
    "session_protocol": "s11_validator_session_v2",
}
variant = sys.argv[3]
if variant == "old_key":
    provenance.pop("normal_valid_fn_path")
    provenance.pop("valid_fn")
    provenance["normal_individualset_path"] = True
elif variant == "both_keys":
    provenance["normal_individualset_path"] = True
elif variant == "false":
    provenance["normal_valid_fn_path"] = False
elif variant == "substitution":
    provenance["valid_fn"] = "substitute.validator"
for line in sys.stdin.buffer:
    request = json.loads(line)
    if request["raw_configuration"].get("bad"):
        sys.stdout.buffer.write(b"{malformed}\\n")
        sys.stdout.buffer.flush()
        continue
    canonical = json.dumps(
        request, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    response = {
        "protocol": request["protocol"],
        "request_sha256": hashlib.sha256(canonical).hexdigest(),
        "accepted": True,
        "provenance": provenance,
    }
    sys.stdout.write(
        json.dumps(response, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\\n"
    )
    sys.stdout.flush()
""",
        encoding="utf-8",
    )
    executable = Path(sys.executable).resolve()
    executable_sha256 = sha256_file(executable)
    source_sha256 = sha256_file(worker)
    return PinnedValidatorAdapter(
        executable, executable_sha256=executable_sha256,
        validator_source_path=worker, validator_source_sha256=source_sha256,
        timeout_seconds=2, protocol=PERSISTENT_VALIDATOR_PROTOCOL,
        worker_count=worker_count,
        argv=[
            str(executable), str(worker), executable_sha256, source_sha256,
            provenance_variant,
        ],
        cwd=tmp_path,
    )


def test_persistent_validator_worker_count_parity_and_request_context(tmp_path: Path) -> None:
    spec = StreamSpec("global", target_accepted=1, hard_cap_chunks=1, nominal_slots_per_chunk=8)
    fd_before = len(os.listdir("/proc/self/fd"))
    with _fake_persistent_validator(tmp_path, 1) as one:
        one_chunk = sample_chunk(
            tiny_registry(), spec, master_nonce="a" * 64, chunk_index=0,
            validator=one,
        )
    with _fake_persistent_validator(tmp_path, 3) as many:
        many_chunk = sample_chunk(
            tiny_registry(), spec, master_nonce="a" * 64, chunk_index=0,
            validator=many,
        )
        assert many.spawn_count == 3
        worker_pids = [session.process.pid for session in many._sessions if session.process]
    assert all(session.process is None for session in many._sessions)
    assert all(not Path(f"/proc/{pid}").exists() for pid in worker_pids)
    assert len(os.listdir("/proc/self/fd")) <= fd_before + 1
    assert one_chunk == many_chunk
    expand_compact_chunk(
        one_chunk, registry=tiny_registry(), spec=spec, master_nonce="a" * 64,
        expected_lock_sha256="0" * 64,
    )


def test_persistent_validator_malformed_response_digest_and_session_restart(
    tmp_path: Path,
) -> None:
    malformed = b"{malformed}\n"
    with _fake_persistent_validator(tmp_path, 1) as validator:
        results = validator.validate_many(
            [{"bad": True}, {"bad": False}],
            [
                {"stream_id": "global", "chunk_index": 7, "slot_index": 0},
                {"stream_id": "global", "chunk_index": 7, "slot_index": 1},
            ],
        )
        assert validator.spawn_count == 2
    assert results[0]["raw_response_sha256"] == hashlib.sha256(malformed).hexdigest()
    assert results[0]["raw_response_truncated"] is False
    assert results[1]["raw_response_sha256"] is None


def test_actual_registry_compact_chunk_storage_forecast_and_bounded_spawns(
    tmp_path: Path,
) -> None:
    registry = extract_registry(ACTUAL_YAML)
    spec = StreamSpec(
        "global", target_accepted=8192, hard_cap_chunks=65536,
        nominal_slots_per_chunk=512,
    )
    with _fake_persistent_validator(tmp_path, 4) as validator:
        chunk = sample_chunk(
            registry, spec, master_nonce="b" * 64, chunk_index=0,
            validator=validator, lock_sha256=LOCK_ID,
        )
        assert validator.spawn_count == 4
    compact_chunk_bytes = len(canonical_json_bytes(chunk)) + 1
    producer_chunk_count = 65536 + 101 * 512
    producer_worst_case_bytes = compact_chunk_bytes * producer_chunk_count
    assert producer_chunk_count == 117248
    assert compact_chunk_bytes < 45000
    assert producer_worst_case_bytes < 5 * 1024**3


@pytest.mark.parametrize(
    "variant", ["old_key", "both_keys", "false", "substitution"]
)
def test_persistent_validator_provenance_substitution_fails_closed(
    tmp_path: Path, variant: str,
) -> None:
    with _fake_persistent_validator(tmp_path, 1, variant) as validator:
        result = validator.validate_many(
            [{"G": 1}],
            [{"stream_id": "global", "chunk_index": 0, "slot_index": 0}],
        )[0]
    assert result["code"] == 6
    assert result["raw_response_sha256"] is not None


def test_ledger_full_replay_cursor_and_metadata_only_event(tmp_path: Path) -> None:
    with ChunkLedger(tmp_path / "ledger", LOCK_ID) as ledger:
        for index in range(3):
            ledger.append_chunk(
                stage="global_discovery", stream_id="global", chunk_index=index,
                **ledger_metadata(index),
            )
        replay = ledger.full_verify()
    assert replay["event_count"] == 3
    assert replay["per_stream_next_chunk"] == {"global": 3}


def test_ledger_rejects_cursor_index_chain_and_payload_corruption(tmp_path: Path) -> None:
    root = tmp_path / "ledger"
    with ChunkLedger(root, LOCK_ID) as ledger:
        ledger.append_chunk(
            stage="global_discovery", stream_id="global", chunk_index=0,
            **ledger_metadata(0),
        )
        with pytest.raises(LedgerError, match="first missing"):
            ledger.append_chunk(
                stage="global_discovery", stream_id="global", chunk_index=2,
                **ledger_metadata(2),
            )
    event_path = root / "events/000000000000.json"
    event = json.loads(event_path.read_text(encoding="utf-8"))
    event["disposition_counts"]["accepted"] = 0
    atomic_write_json(event_path, event)
    with pytest.raises(LedgerError):
        with ChunkLedger(root, LOCK_ID):
            pass


def test_ledger_recovers_one_complete_published_tail(tmp_path: Path) -> None:
    root = tmp_path / "ledger"
    with ChunkLedger(root, LOCK_ID) as ledger:
        empty_index = json.loads((root / "ledger-index.json").read_text(encoding="utf-8"))
        ledger.append_chunk(
            stage="global_discovery", stream_id="global", chunk_index=0,
            **ledger_metadata(0),
        )
    atomic_write_json(root / "ledger-index.json", empty_index)
    with ChunkLedger(root, LOCK_ID) as recovered:
        assert recovered.full_verify()["event_count"] == 1


def test_resumable_stream_end_to_end_interruption_replay_and_zero_credit(tmp_path: Path) -> None:
    spec = StreamSpec(
        "global", target_accepted=3, hard_cap_chunks=3, nominal_slots_per_chunk=4
    )
    root = tmp_path / "resumable-stream"
    with pytest.raises(SyntheticInterruption):
        run_resumable_stream(
            tiny_registry(), spec, master_nonce="8" * 64,
            validator=lambda _: True, scratch_root=root, lock_sha256=LOCK_ID,
            stage="global_discovery", synthetic=True,
            interrupt_after_publication=1,
        )
    resumed = run_resumable_stream(
        tiny_registry(), spec, master_nonce="8" * 64,
        validator=lambda _: True, scratch_root=root, lock_sha256=LOCK_ID,
        stage="global_discovery", synthetic=True,
    )
    clean = run_resumable_stream(
        tiny_registry(), spec, master_nonce="8" * 64,
        validator=lambda _: True, scratch_root=tmp_path / "clean",
        lock_sha256=LOCK_ID, stage="global_discovery", synthetic=True,
    )
    assert resumed == clean
    assert resumed["cap_complete"] is True
    assert resumed["prefix"]["accepted_credited"] == 3
    assert len(resumed["credited_rows"]) == 3
    assert resumed["prefix"]["overshoot_diagnostic"] == 9
    assert resumed["ledger_replay"]["event_count"] == 3
    rebuilt, attestation = _validate_raw_stream(
        stream=resumed, spec=spec, stream_root=root, registry=tiny_registry(),
        master_nonce="8" * 64, lock_sha256=LOCK_ID,
        stage="global_discovery", repository_root=tmp_path,
    )
    assert rebuilt == resumed
    assert attestation["raw_file_count"] == 7  # index + 3 chunks + 3 events
    assert len(attestation["raw_files_sha256"]) == 64
    with pytest.raises(WorkflowError, match="root is absent"):
        _validate_raw_stream(
            stream=resumed, spec=spec, stream_root=tmp_path / "no-ledger",
            registry=tiny_registry(), master_nonce="8" * 64,
            lock_sha256=LOCK_ID, stage="global_discovery", repository_root=tmp_path,
        )
    longer_spec = StreamSpec(
        "global", target_accepted=3, hard_cap_chunks=4, nominal_slots_per_chunk=4
    )
    short_summary = {**resumed, "hard_cap_chunks": 4, "complete_nominal_draws": 16}
    with pytest.raises(WorkflowError, match="full production cap"):
        _validate_raw_stream(
            stream=short_summary, spec=longer_spec, stream_root=root,
            registry=tiny_registry(), master_nonce="8" * 64,
            lock_sha256=LOCK_ID, stage="global_discovery", repository_root=tmp_path,
        )
    with pytest.raises(WorkflowError, match="not formally reachable"):
        run_resumable_stream(
            tiny_registry(), spec, master_nonce="8" * 64,
            validator=lambda _: True, scratch_root=tmp_path / "formal-hook",
            lock_sha256=LOCK_ID, stage="global_discovery",
            interrupt_after_publication=0,
        )


def test_populations_preserve_alias_multiplicity_and_exclude_overshoot() -> None:
    rows = [
        population_row("o0", identity="same"),
        population_row("o1", identity="same"),
        population_row("o2", identity="later", credit=False),
        population_row("o3", frame="conditional/G/v0", identity="conditional"),
    ]
    populations = build_populations(rows)
    assert len(populations["Fraw_global"]) == 2
    assert populations["Uexec_global"] == ["same"]
    assert populations["aliases_by_identity"]["same"] == ["o0", "o1"]
    assert [row["occurrence_id"] for row in populations["zero_credit_diagnostics"]] == ["o2"]
    assert global_mean(populations) == 0.5
    cell = value_cell(populations, gene="G", candidate_id="v0")
    assert len(cell["Graw"]) == 2 and cell["support_gv"] == 1


def test_value_cell_zero_denominator_and_global_conditional_isolation() -> None:
    rows = [
        population_row("g", executable=False, scored=False),
        population_row("c", frame="conditional/G/v0", executable=False, scored=False),
    ]
    populations = build_populations(rows)
    cell = value_cell(populations, gene="G", candidate_id="v0")
    assert cell["Cscore_occ_gv"] is None
    assert populations["Y_exec_global"] == 0.0
    assert populations["Uexec_global"] == []


def test_alpha0_sensitivity_reports_attenuation_displacement_and_flip() -> None:
    cells = {
        "a": {"Dscore": [{}], "sum_b_gv": 0.9},
        "b": {"Dscore": [{}, {}], "sum_b_gv": 0.2},
        "c": {"Dscore": [], "sum_b_gv": 0.0},
    }
    marginals = {"a": 0.4, "b": 0.6, "c": 0.5}
    flipped = alpha0_shrinkage_sensitivity(
        marginals_alpha32=marginals,
        cells=cells,
        global_mean=0.5,
        best="b",
        worst="a",
    )
    assert flipped["attenuation"]["a"] == pytest.approx(1.0 / 33.0)
    assert flipped["mu_unshrunk"]["a"] == pytest.approx(0.9)
    assert flipped["displacement"]["a"] == pytest.approx(0.4 - 0.9)
    assert flipped["alpha0_best"] == "a" and flipped["alpha0_worst"] == "b"
    assert flipped["alpha0_bestworst_flip"] is True
    assert flipped["mu_unshrunk"]["c"] is None
    assert flipped["mu_unshrunk_reason"]["c"] == "n_gv_zero"

    stable = alpha0_shrinkage_sensitivity(
        marginals_alpha32=marginals,
        cells=cells,
        global_mean=0.5,
        best="a",
        worst="b",
    )
    assert stable["alpha0_bestworst_flip"] is False


def test_survivorship_yield_and_divzero_guard() -> None:
    report = survivorship_yield(
        cell={
            "Draw": [{}, {}, {}, {}],
            "Dexec": [{}, {}, {}],
            "Dscore": [{}, {}],
            "Cscore_occ_gv": 2.0 / 3.0,
        }
    )
    assert report["Y_exec_gv"] == pytest.approx(3.0 / 4.0)
    assert report["Cscore_occ_gv"] == pytest.approx(2.0 / 3.0)
    assert report["exec_attrition_share"] == pytest.approx(1.0 / 4.0)
    assert report["score_attrition_share"] == pytest.approx(1.0 / 3.0)

    empty = survivorship_yield(
        cell={"Draw": [], "Dexec": [], "Dscore": [], "Cscore_occ_gv": None}
    )
    assert empty["Y_exec_gv"] is None
    assert empty["Y_exec_reason"] == "draw_empty"
    assert empty["exec_attrition_share"] is None
    assert empty["score_attrition_share"] is None


def test_arm_sensitivity_theta_and_not_estimable_on_poor_overlap() -> None:
    cells = {
        "a": {
            "Dscore": [
                {"candidate_ids": {"G": "a", "H": "x"}, "benefit": 0.8},
                {"candidate_ids": {"G": "a", "H": "y"}, "benefit": 0.2},
            ]
        },
        "b": {
            "Dscore": [
                {"candidate_ids": {"G": "b", "H": "x"}, "benefit": 0.3},
                {"candidate_ids": {"G": "b", "H": "y"}, "benefit": 0.7},
            ]
        },
    }
    well_overlapped = {
        "G": {"H": {"x": 0.5, "y": 0.5}},
        "F": {"H": {"x": 0.75, "y": 0.25}},
        "S": {"H": {"x": 0.25, "y": 0.75}},
    }
    report = arm_sensitivity_theta(
        gene="G",
        trusted=["a", "b"],
        cells=cells,
        arm_distributions=well_overlapped,
    )
    assert math.isfinite(report["a"]["theta"]["F"])
    assert report["a"]["ess"]["F"] > 0.0
    assert report["a"]["not_estimable"]["F"] is False
    assert type(report["ordering_change_F"]) is bool

    poor_overlap = {
        **well_overlapped,
        "F": {"H": {"z": 1.0}},
    }
    poor = arm_sensitivity_theta(
        gene="G",
        trusted=["a", "b"],
        cells=cells,
        arm_distributions=poor_overlap,
    )
    assert poor["a"]["not_estimable"]["F"] is True
    assert poor["a"]["theta"]["F"] is None
    assert poor["a"]["ess"]["F"] is None
    assert poor["ordering_estimable"] is False
    assert poor["ordering_change_F"] is None

    sparse_cells = {
        candidate_id: {
            "Dscore": [
                {
                    "candidate_ids": {"G": candidate_id, "H": "x"},
                    "benefit": benefit,
                }
            ]
            + [
                {
                    "candidate_ids": {"G": candidate_id, "H": "y"},
                    "benefit": benefit,
                }
                for _ in range(99)
            ]
        }
        for candidate_id, benefit in (("a", 0.8), ("b", 0.2))
    }
    sparse = arm_sensitivity_theta(
        gene="G",
        trusted=["a", "b"],
        cells=sparse_cells,
        arm_distributions={
            "G": {"H": {"x": 0.5, "y": 0.5}},
            "F": {"H": {"x": 1.0, "y": 0.0}},
            "S": {"H": {"x": 0.5, "y": 0.5}},
        },
    )
    assert sparse["ess_min_fraction"] == 0.05
    assert sparse["a"]["ess_fraction"]["F"] == pytest.approx(0.01)
    assert sparse["a"]["not_estimable"]["F"] is True
    assert sparse["a"]["theta"]["F"] is None


def test_per_size_latency_margin_contrasts_and_ratios() -> None:
    report = per_size_latency_margin(
        arm_cell_rows={
            "G": [(1.0, {"latencies": [4.0, {"predicted_latency": 9.0}]})],
            "F": [(1.0, {"latencies": [1.0, {"predicted_latency": 3.0}]})],
            "S": [],
        }
    )
    assert report["contrast_G_minus_F"] == pytest.approx(
        [math.log(4.0), math.log(3.0)]
    )
    assert report["ratio_G_over_F"] == pytest.approx([4.0, 3.0])
    assert report["E_logL"]["S"] == [None, None]
    assert report["contrast_S_minus_F"] == [None, None]
    assert report["ratio_S_over_F"] == [None, None]
    assert report["note"] == (
        "formocast_model_margin_terminal_frame_relative_not_real_speedup"
    )


def test_exactly_two_qualification_accept_reject_and_pending() -> None:
    producer = attempt("producer", "producer")
    verifier = attempt("fresh_verifier", "verifier")
    assert evaluate_attempts([producer], blocked_mapping_allowlist=[])["state"] == "pending_second_attempt"
    assert evaluate_attempts([producer, verifier], blocked_mapping_allowlist=[])["state"] == "executable"
    reject_a = replace(producer, result="normal_reject", semantic_identity=None, reason_code="normal_reject")
    reject_b = replace(verifier, result="normal_reject", semantic_identity=None, reason_code="normal_reject")
    assert evaluate_attempts([reject_a, reject_b], blocked_mapping_allowlist=[])["state"] == "execution_attrition"


@pytest.mark.parametrize(
    "producer,verifier,reason",
    [
        (attempt("producer", "same"), attempt("fresh_verifier", "same"), "fresh_verifier_root_not_separate"),
        (attempt("producer", "p"), attempt("fresh_verifier", "v", complete=False), "partial_attempt"),
        (attempt("producer", "p"), attempt("fresh_verifier", "v", no_guess=False), "guessed_field"),
        (attempt("producer", "p"), attempt("fresh_verifier", "v", qualification_fingerprint="d" * 64), "ambient_or_toolchain_drift"),
        (attempt("producer", "p"), attempt("fresh_verifier", "v", result="normal_reject", semantic_identity=None), "discordant_result"),
        (attempt("producer", "p"), attempt("fresh_verifier", "v", semantic_identity="e" * 64), "semantic_identity_discordance"),
        (attempt("producer", "p"), attempt("fresh_verifier", "v", solution_sha256="7" * 64), "solution_association_discordance"),
        (attempt("producer", "p"), attempt("fresh_verifier", "v", size_mapping_sha256="7" * 64), "size_mapping_association_discordance"),
        (attempt("producer", "p"), attempt("fresh_verifier", "v", kernel_association_sha256="7" * 64), "kernel_association_discordance"),
        (attempt("producer", "p"), attempt("fresh_verifier", "v", occurrence_ids_sha256="7" * 64), "occurrence_binding_discordance"),
        (attempt("producer", "p"), attempt("fresh_verifier", "v", alias_fanout_sha256="7" * 64), "alias_fanout_discordance"),
    ],
)
def test_qualification_discordance_guess_association_and_partial_are_changes_required(
    producer: QualificationAttempt, verifier: QualificationAttempt, reason: str
) -> None:
    projection = evaluate_attempts([producer, verifier], blocked_mapping_allowlist=[])
    assert projection["state"] == "changes_required_not_evaluated"
    assert projection["reason"] == reason


def test_mapping_outcome_cannot_be_manufactured_with_empty_allowlist() -> None:
    producer = attempt("producer", "p", result="mapping_impossible", semantic_identity=None, reason_code="x")
    verifier = attempt("fresh_verifier", "v", result="mapping_impossible", semantic_identity=None, reason_code="x")
    assert evaluate_attempts([producer, verifier], blocked_mapping_allowlist=[])["state"] == "changes_required_not_evaluated"
    with pytest.raises(DecisionError, match="unreachable"):
        decide(decision_inputs(blocked_mapping_exact_allowlisted=True))


def test_value_preservation_is_separate_from_executable_membership() -> None:
    aliases = [{"gene": "G", "candidate_id": "v", "semantic_identity": "id", "relation": "value_preserving"}]
    assert value_preservation_state(aliases, gene="G", candidate_id="v")["trusted"] is True
    aliases.append({"gene": "G", "candidate_id": "v", "semantic_identity": "other", "relation": "value_preserving"})
    assert value_preservation_state(aliases, gene="G", candidate_id="v")["trusted"] is False


def test_occurrence_weighted_mid_ecdf_ties_and_conditional_query_isolation() -> None:
    global_rows = [
        {"semantic_identity": "a", "latencies": [1.0, 1.0, 1.0]},
        {"semantic_identity": "b", "latencies": [1.0, 2.0, 2.0]},
        {"semantic_identity": "c", "latencies": [3.0, 4.0, 4.0]},
    ]
    benefits = midrank_latency_benefits(global_rows, reducer="max")
    assert benefits[0]["size_latency_percentile"][0] == pytest.approx(1.0 / 3.0)
    assert benefits[0]["benefit"] == pytest.approx(5.0 / 6.0)
    assert benefits[2]["benefit"] == pytest.approx(1.0 / 6.0)
    conditional = query_terminal_global_ecdf(
        global_rows, [{"semantic_identity": "q", "latencies": [2.0, 2.0, 2.0]}]
    )
    assert conditional[0]["size_latency_percentile"] == pytest.approx([2.0 / 3.0, 0.5, 0.5])
    assert conditional[0]["benefit"] == pytest.approx(0.5)
    assert [row["semantic_identity"] for row in global_rows] == ["a", "b", "c"]


def test_bootstrap_rebuilds_all_statistics_deterministic_golden() -> None:
    global_rows, conditional, _ = statistical_rows()
    result = bootstrap_stability(
        global_rows=global_rows,
        conditional_cells=conditional,
        observed_best="a",
        observed_worst="b",
        master_nonce="6" * 64,
        gene="G",
        candidate_order=["a", "b"],
    )
    assert result["replicates"] == 2000
    assert result["rebuilds_ecdf_benefit_global_mean_mu_and_S"] is True
    assert result["fixed_pair"] == ["a", "b"]
    assert result["differences_sha256"] == "30b0fc0000ba6f1bb9037cd5998d165ba76d90c7550627e020adbd5b5442cb7a"


def test_joint_permutation_rebuilds_all_statistics_deterministic_golden() -> None:
    global_rows, conditional, observed = statistical_rows()
    result = joint_permutation_test(
        global_rows=global_rows,
        conditional_cells={"G": conditional},
        trusted_values={"G": ["a", "b"]},
        observed_marginals=observed,
        master_nonce="7" * 64,
    )
    assert result["replicates"] == 2000
    assert result["shared_global_permutation"] is True
    assert result["conditional_domain_separation"] is True
    assert result["max_null_sha256"] == "9f9197b545107165af8e54d8e66b45f86c4bce56c998735a979ca9d2932b439b"


def test_type7_size_direction_and_three_size_requirement() -> None:
    assert type7_quantile(list(range(1, 2001)), 0.95) == pytest.approx(1900.05)
    with pytest.raises(StatisticsError, match="three locked"):
        midrank_latency_benefits(
            [{"semantic_identity": "a", "latencies": [1.0]}, {"semantic_identity": "b", "latencies": [2.0]}],
            reducer="max",
        )
    cells = {
        "best": [{"size_benefits": [0.9, 0.8, 0.1]}],
        "worst": [{"size_benefits": [0.1, 0.2, 0.2]}],
    }
    assert size_direction(cells, best="best", worst="worst")["pass"] is True


def test_semantic_half_stability_gates_categorical_projection_and_reports_numeric_drift() -> None:
    half = {field: {"value": field} for field in HALF_TUPLE_FIELDS}
    identical = semantic_half_stability(half, dict(half))
    assert identical["stable"] is True
    changed = dict(half)
    changed["each_model_test_result"] = {"value": "changed"}
    result = semantic_half_stability(half, changed)
    assert result["stable"] is False

    drifted = dict(half)
    drifted["per_value_mu"] = {"value": "drifted"}
    result = semantic_half_stability(half, drifted)
    assert result["stable"] is True
    assert result["numeric_drift"]["gating"] is False
    assert result["numeric_drift"]["reported"] is True
    assert "per_value_mu" in result["numeric_drift"]["fields"]
    assert result["categorical_projection_fields"] == list(HALF_CATEGORICAL_PROJECTION_FIELDS)
    assert identical["left_categorical_sha256"] == canonical_sha256(
        {field: half[field] for field in HALF_CATEGORICAL_PROJECTION_FIELDS}
    )
    quarter_lambda = {field: {"value": field} for field in HALF_TUPLE_FIELDS}
    quarter_lambda["same_positive_global_lambda"] = 0.25

    half_lambda = dict(quarter_lambda)
    half_lambda["same_positive_global_lambda"] = 0.50
    assert semantic_half_stability(quarter_lambda, half_lambda)["stable"] is False

    zero_lambda = dict(quarter_lambda)
    zero_lambda["same_positive_global_lambda"] = 0.0
    assert semantic_half_stability(zero_lambda, quarter_lambda)["stable"] is False

    numeric_drift = dict(quarter_lambda)
    numeric_drift["per_value_mu"] = {"value": "drifted"}
    result = semantic_half_stability(quarter_lambda, numeric_drift)
    assert result["stable"] is True
    assert result["numeric_drift"]["gating"] is False
    assert result["numeric_drift"]["reported"] is True
    assert result["numeric_drift"]["fields"] == ["per_value_mu"]
    assert result["continuation"] == "NO_EXTENSION_PERMITTED"
    with pytest.raises(StatisticsError, match="incomplete"):
        semantic_half_stability({}, {})


def test_guidance_p0_q_p1_entropy_and_global_positive_lambda() -> None:
    order = ["a", "b", "c"]
    inputs = {
        "candidate_order": order,
        "baseline": {"a": 0.2, "b": 0.3, "c": 0.5},
        "marginals": {"a": 0.2, "b": 0.4},
        "trusted": ["a", "b"],
    }
    bundle = construct_gene_probabilities(**inputs, lambda_value=1.0)
    assert bundle["p1"][2] == 0.20 * 0.5
    assert sum(bundle["p1"]) == pytest.approx(1.0)
    selected = select_global_lambda({"G": inputs})
    assert selected["global_lambda"] > 0.0
    assert selected["genes"]["G"]["normalized_entropy"] >= 0.80


def test_guidance_shuffle_order_roundtrip_and_tamper_faults() -> None:
    order = ["a", "b", "c"]
    q = [0.4, 0.6, 0.0]
    shuffled = deterministic_nonidentity_shuffle(
        candidate_order=order, trusted=["a", "b"], q=q, master_nonce="4" * 64, gene="G"
    )
    assert shuffled["nonidentity"] and shuffled["multiset_preserved"]
    assert shuffled["q_shuffled"][2] == 0.0
    roundtrip = float32_inverse_cost_roundtrip([0.2, 0.3, 0.5], weight_beta=0.25)
    assert roundtrip["pass"] is True
    assert guidance_bundle_identity(roundtrip) == canonical_sha256(roundtrip)
    with pytest.raises(GuidanceError):
        construct_gene_probabilities(
            candidate_order=order,
            baseline={"b": 0.3, "a": 0.2, "c": 0.5},
            marginals={"a": 0.2, "b": 0.4}, trusted=["a", "b"], lambda_value=1.0,
        )


def synthetic_scientific_artifacts(
    *,
    conditional_count: int = 128,
    candidate_latencies: tuple[float, float] = (1.0, 10.0),
) -> tuple[dict, dict, dict, dict, dict]:
    registry_payload = tiny_registry()
    registry = seal_stage_artifact(
        "s11_registry", lock_sha256=LOCK_ID, dependencies={}, payload=registry_payload
    )
    ids = registry_payload["eligible_genes"][0]["candidate_ids"]
    raws = [{"G": 0}, {"G": 1}]

    def occurrence(frame: str, index: int, candidate_index: int) -> dict:
        raw = raws[candidate_index]
        occurrence_id = canonical_sha256(
            {"frame": frame, "index": index, "raw_configuration": raw}
        )
        return {
            "occurrence_id": occurrence_id,
            "frame": frame,
            "candidate_ids": {"G": ids[candidate_index]},
            "raw_configuration": raw,
            "canonical_credit": True,
        }

    global_rows = [occurrence("global", index, index % 2) for index in range(4)]
    conditional_streams = []
    all_rows = list(global_rows)
    for candidate_index, candidate_id in enumerate(ids):
        frame = f"conditional/G/{candidate_id[:16]}"
        rows = [
            occurrence(frame, index, candidate_index)
            for index in range(conditional_count)
        ]
        all_rows.extend(rows)
        conditional_streams.append(
            {
                "stream_id": frame, "fixed_gene": "G",
                "fixed_candidate_id": candidate_id, "cap_complete": True,
                "prefix": {
                    "complete": True, "accepted_credited": conditional_count,
                    "credited_occurrence_ids": [row["occurrence_id"] for row in rows],
                },
                "credited_rows": rows,
            }
        )
    global_prefix = seal_stage_artifact(
        "s11_global_prefix", lock_sha256=LOCK_ID,
        dependencies={"registry": registry["artifact_sha256"]},
        payload={
            "stream": {
                "stream_id": "global", "cap_complete": True,
                "prefix": {
                    "complete": True, "accepted_credited": 4,
                    "credited_occurrence_ids": [row["occurrence_id"] for row in global_rows],
                },
                "credited_rows": global_rows,
            }
        },
    )
    conditional = seal_stage_artifact(
        "s11_conditional_prefixes", lock_sha256=LOCK_ID,
        dependencies={
            "registry": registry["artifact_sha256"],
            "global_prefix": global_prefix["artifact_sha256"],
        },
        payload={"activation_complete": True, "streams": conditional_streams},
    )
    qualification_records = []
    score_records = []
    for candidate_index, raw in enumerate(raws):
        raw_sha = canonical_sha256(raw)
        occurrence_ids = [
            row["occurrence_id"]
            for row in all_rows
            if canonical_sha256(row["raw_configuration"]) == raw_sha
        ]
        semantic_id = canonical_sha256({"synthetic_semantic": candidate_index})
        qualification_records.append(
            {
                "raw_configuration_sha256": raw_sha,
                "occurrence_ids": occurrence_ids,
                "alias_fanout_sha256": canonical_sha256({raw_sha: occurrence_ids}),
                "attempt_count": 2,
                "projection": {"state": "executable", "semantic_identity": semantic_id},
            }
        )
        latency = candidate_latencies[candidate_index]
        score_records.append(
            {
                "semantic_identity": semantic_id,
                "native_result": {"latencies": [latency, latency, latency]},
                "occurrence_ids": occurrence_ids,
            }
        )
    qualifications = seal_stage_artifact(
        "s11_qualifications", lock_sha256=LOCK_ID,
        dependencies={
            "global_prefix": global_prefix["artifact_sha256"],
            "conditional_prefixes": conditional["artifact_sha256"],
        },
        payload={
            "qualification_records": qualification_records,
            "exactly_two_complete_attempts_enforced": True,
            "producer_and_fresh_verifier_roots_separate": True,
        },
    )
    scores = seal_stage_artifact(
        "s11_native_scores", lock_sha256=LOCK_ID,
        dependencies={"qualifications": qualifications["artifact_sha256"]},
        payload={"score_records": score_records, "all_locked_sizes_required": True},
    )
    return registry, global_prefix, conditional, qualifications, scores


def multi_gene_scientific_artifacts(
    *, validity_frame: bool = False
) -> tuple[dict, dict, dict, dict, dict]:
    genes = []
    candidate_ids = {}
    for gene, baseline in (("G", [0.7, 0.3]), ("H", [0.6, 0.4])):
        ids = [canonical_sha256({"gene": gene, "index": index}) for index in range(2)]
        candidate_ids[gene] = ids
        genes.append(
            {
                "gene": gene,
                "candidates": [
                    {"type": "int", "value": "0"},
                    {"type": "int", "value": "1"},
                ],
                "candidate_ids": ids,
                "baseline_probabilities": baseline,
            }
        )
    registry = seal_stage_artifact(
        "s11_registry",
        lock_sha256=LOCK_ID,
        dependencies={},
        payload={"eligible_genes": genes},
    )
    raws = [
        {"G": g_index, "H": h_index}
        for g_index in range(2)
        for h_index in range(2)
    ]
    if validity_frame:
        global_raws = raws * 2
    else:
        global_raws = raws

    def occurrence(frame: str, index: int, raw: dict) -> dict:
        return {
            "occurrence_id": canonical_sha256(
                {"frame": frame, "index": index, "raw_configuration": raw}
            ),
            "frame": frame,
            "candidate_ids": {
                gene: candidate_ids[gene][raw[gene]] for gene in ("G", "H")
            },
            "raw_configuration": raw,
            "canonical_credit": True,
        }

    global_rows = [
        occurrence("global", index, raw) for index, raw in enumerate(global_raws)
    ]
    conditional_streams = []
    all_rows = list(global_rows)
    for gene in ("G", "H"):
        other_gene = "H" if gene == "G" else "G"
        for candidate_index, candidate_id in enumerate(candidate_ids[gene]):
            frame = f"conditional/{gene}/{candidate_id[:16]}"
            rows = []
            for index in range(128):
                if validity_frame:
                    other_index = 0
                elif gene == "G":
                    other_index = index % 2
                else:
                    low_count = 70 if candidate_index == 0 else 58
                    other_index = 0 if index < low_count else 1
                raw = {gene: candidate_index, other_gene: other_index}
                if validity_frame:
                    raw["validity_cell"] = gene
                rows.append(occurrence(frame, index, raw))
            all_rows.extend(rows)
            conditional_streams.append(
                {
                    "stream_id": frame,
                    "fixed_gene": gene,
                    "fixed_candidate_id": candidate_id,
                    "cap_complete": True,
                    "prefix": {
                        "complete": True,
                        "accepted_credited": 128,
                        "credited_occurrence_ids": [
                            row["occurrence_id"] for row in rows
                        ],
                    },
                    "credited_rows": rows,
                }
            )
    global_prefix = seal_stage_artifact(
        "s11_global_prefix",
        lock_sha256=LOCK_ID,
        dependencies={"registry": registry["artifact_sha256"]},
        payload={
            "stream": {
                "stream_id": "global",
                "cap_complete": True,
                "prefix": {
                    "complete": True,
                    "accepted_credited": len(global_rows),
                    "credited_occurrence_ids": [
                        row["occurrence_id"] for row in global_rows
                    ],
                },
                "credited_rows": global_rows,
            }
        },
    )
    conditional = seal_stage_artifact(
        "s11_conditional_prefixes",
        lock_sha256=LOCK_ID,
        dependencies={
            "registry": registry["artifact_sha256"],
            "global_prefix": global_prefix["artifact_sha256"],
        },
        payload={"activation_complete": True, "streams": conditional_streams},
    )
    qualification_records = []
    score_records = []
    configurations_by_sha = {}
    for row in all_rows:
        configurations_by_sha.setdefault(
            canonical_sha256(row["raw_configuration"]),
            row["raw_configuration"],
        )
    for raw in configurations_by_sha.values():
        raw_sha = canonical_sha256(raw)
        occurrence_ids = [
            row["occurrence_id"]
            for row in all_rows
            if canonical_sha256(row["raw_configuration"]) == raw_sha
        ]
        semantic_id = canonical_sha256({"synthetic_semantic": raw})
        qualification_records.append(
            {
                "raw_configuration_sha256": raw_sha,
                "occurrence_ids": occurrence_ids,
                "alias_fanout_sha256": canonical_sha256({raw_sha: occurrence_ids}),
                "attempt_count": 2,
                "projection": {
                    "state": "executable",
                    "semantic_identity": semantic_id,
                },
            }
        )
        validity_cell = raw.get("validity_cell")
        if validity_cell == "G":
            base_latency = 0.25 if raw["G"] == 0 else 8.0
        elif validity_cell == "H":
            base_latency = 0.50 if raw["H"] == 0 else 9.0
        elif validity_frame:
            base_latency = 1.0 + 4.0 * raw["G"] + 2.0 * raw["H"]
        else:
            base_latency = 10.0 if raw["G"] else 1.0
        score_records.append(
            {
                "semantic_identity": semantic_id,
                "native_result": {
                    "latencies": [
                        base_latency,
                        2.0 * base_latency,
                        4.0 * base_latency,
                    ]
                },
                "occurrence_ids": occurrence_ids,
            }
        )
    qualifications = seal_stage_artifact(
        "s11_qualifications",
        lock_sha256=LOCK_ID,
        dependencies={
            "global_prefix": global_prefix["artifact_sha256"],
            "conditional_prefixes": conditional["artifact_sha256"],
        },
        payload={
            "qualification_records": qualification_records,
            "exactly_two_complete_attempts_enforced": True,
            "producer_and_fresh_verifier_roots_separate": True,
        },
    )
    scores = seal_stage_artifact(
        "s11_native_scores",
        lock_sha256=LOCK_ID,
        dependencies={"qualifications": qualifications["artifact_sha256"]},
        payload={"score_records": score_records, "all_locked_sizes_required": True},
    )
    return registry, global_prefix, conditional, qualifications, scores


def _edge_decision_from_analysis(analysis: dict, guidance: dict) -> dict:
    return decide(
        decision_inputs(
            material_stochastic_shortage=bool(analysis["material_shortages"]),
            stable_guided_gene_count=analysis["stable_guided_gene_count"],
            positive_global_lambda=guidance["positive_global_lambda"],
            all_positive_gates_pass=(
                analysis["all_model_gates_pass"]
                and guidance["all_guidance_gates_pass"]
                and analysis["semantic_half_stability"]["stable"]
            ),
        )
    )


def _guided_decision_projection(
    analysis: dict, guidance: dict, contract: dict
) -> dict:
    decision = _edge_decision_from_analysis(analysis, guidance)
    return {
        "thresholds": contract["statistics"],
        "gene_results": analysis["gene_results"],
        "stable_guided_gene_count": analysis["stable_guided_gene_count"],
        "all_model_gates_pass": analysis["all_model_gates_pass"],
        "semantic_half_stability": analysis["semantic_half_stability"],
        "guidance": guidance,
        "decision": decision,
        "edge": branch_artifact_policy(decision)["edge"],
    }


def _build_option_c_analysis(
    monkeypatch: pytest.MonkeyPatch,
    gene_states: dict[str, tuple[bool, bool]],
) -> tuple[dict, dict, tuple[dict, dict, dict, dict, dict]]:
    import s11.workflow as workflow_module

    artifacts = synthetic_scientific_artifacts()
    candidate_ids = {gene: f"{gene}-candidate" for gene in gene_states}

    def frame_analysis(**_: object) -> dict:
        guided = [
            gene for gene, (is_guided, _) in gene_states.items() if is_guided
        ]
        return {
            "population_summary": {"global_uexec_count": 256},
            "trust_states": {
                gene: {
                    candidate_ids[gene]: True,
                    f"{gene}-candidate-2": True,
                }
                for gene in gene_states
            },
            "trust_reasons": {
                gene: {
                    candidate_ids[gene]: "trusted",
                    f"{gene}-candidate-2": "trusted",
                }
                for gene in gene_states
            },
            "trusted_sets": {
                gene: [candidate_ids[gene], f"{gene}-candidate-2"]
                for gene in gene_states
            },
            "gene_results": {
                gene: {
                    "guided": is_guided,
                    "model_test_results": {"alpha32_primary_gate": is_guided},
                }
                for gene, (is_guided, _) in gene_states.items()
            },
            "permutation": {},
            "guidance": {
                "global_lambda": 1.0 if guided else 0.0,
                "positive_global_lambda": bool(guided),
                "genes": {
                    gene: {
                        "normalized_entropy": 1.0,
                        "consumer_roundtrip": {"pass": True},
                        "shuffle": {
                            "nonidentity": True,
                            "multiset_preserved": True,
                        },
                    }
                    for gene in guided
                },
                "canonical_guidance_hash": canonical_sha256(guided),
            },
            "bias_diagnostics": {
                "genes": {
                    gene: {
                        "alpha0_sensitivity": {
                            "alpha0_decision_flip": alpha0_flip,
                        }
                    }
                    for gene, (_, alpha0_flip) in gene_states.items()
                },
                "alpha0_projection": {
                    "decision_flip": any(
                        alpha0_flip for _, alpha0_flip in gene_states.values()
                    ),
                    "reported_only": True,
                },
            },
            "validity_inputs": {
                "marginals": {
                    gene: {candidate_ids[gene]: 0.5} for gene in gene_states
                },
                "emitted_arm_laws": {},
                "baseline": {},
                "global_scored_rows": [
                    {"candidate_ids": dict(candidate_ids)}
                ],
            },
            "half_tuple": {},
        }

    monkeypatch.setattr(workflow_module, "_frame_analysis", frame_analysis)
    monkeypatch.setattr(
        workflow_module,
        "semantic_half_stability",
        lambda _left, _right: {"stable": True},
    )
    monkeypatch.setattr(
        workflow_module,
        "additive_rank_faithfulness",
        lambda **_kwargs: {"reported_only": True},
    )
    monkeypatch.setattr(
        workflow_module,
        "emitted_prior_reconstruction",
        lambda **_kwargs: {"reported_only": True},
    )
    registry, global_prefix, conditional, qualifications, scores = artifacts
    analysis, guidance = build_analysis_and_guidance(
        registry=registry,
        global_prefix=global_prefix,
        conditional_prefixes=conditional,
        qualifications=qualifications,
        native_scores=scores,
        contract=load_contract(),
        lock_sha256=LOCK_ID,
    )
    return analysis, guidance, artifacts


def _reseal_formal_decision_sources(
    analysis: dict,
    guidance: dict,
    artifacts: tuple[dict, dict, dict, dict, dict],
) -> tuple[dict, dict, dict, dict, dict, dict, dict, dict]:
    metadata = {
        "document_kind",
        "schema_version",
        "checkpoint_id",
        "lock_sha256",
        "dependencies",
        "artifact_sha256",
    }

    def payload(document: dict) -> dict:
        return {key: copy.deepcopy(value) for key, value in document.items() if key not in metadata}

    old_registry, old_global, old_conditional, old_qualifications, old_scores = artifacts
    registry_payload = payload(old_registry)
    registry_payload["conditional_streams"] = [
        {"stream_id": stream["stream_id"]}
        for stream in old_conditional["streams"]
    ]
    registry = seal_stage_artifact(
        "s11_registry", lock_sha256=LOCK_ID, dependencies={},
        payload=registry_payload,
    )
    global_payload = payload(old_global)
    global_payload["stream"]["ledger_replay"] = {"stream": "global"}
    global_payload["stream"]["chunk_hashes_sha256"] = canonical_sha256(
        {"stream": "global", "chunks": []}
    )
    global_prefix = seal_stage_artifact(
        "s11_global_prefix", lock_sha256=LOCK_ID,
        dependencies={"registry": registry["artifact_sha256"]},
        payload=global_payload,
    )
    conditional_payload = payload(old_conditional)
    for stream in conditional_payload["streams"]:
        stream["ledger_replay"] = {"stream": stream["stream_id"]}
        stream["chunk_hashes_sha256"] = canonical_sha256(
            {"stream": stream["stream_id"], "chunks": []}
        )
    conditional = seal_stage_artifact(
        "s11_conditional_prefixes", lock_sha256=LOCK_ID,
        dependencies={
            "registry": registry["artifact_sha256"],
            "global_prefix": global_prefix["artifact_sha256"],
        },
        payload=conditional_payload,
    )
    qualifications = seal_stage_artifact(
        "s11_qualifications", lock_sha256=LOCK_ID,
        dependencies={
            "global_prefix": global_prefix["artifact_sha256"],
            "conditional_prefixes": conditional["artifact_sha256"],
        },
        payload=payload(old_qualifications),
    )
    scores = seal_stage_artifact(
        "s11_native_scores", lock_sha256=LOCK_ID,
        dependencies={"qualifications": qualifications["artifact_sha256"]},
        payload=payload(old_scores),
    )
    resealed_analysis = seal_stage_artifact(
        "s11_analysis", lock_sha256=LOCK_ID,
        dependencies={
            "registry": registry["artifact_sha256"],
            "global_prefix": global_prefix["artifact_sha256"],
            "conditional_prefixes": conditional["artifact_sha256"],
            "qualifications": qualifications["artifact_sha256"],
            "native_scores": scores["artifact_sha256"],
        },
        payload=payload(analysis),
    )
    resealed_guidance = seal_stage_artifact(
        "s11_guidance", lock_sha256=LOCK_ID,
        dependencies={"analysis": resealed_analysis["artifact_sha256"]},
        payload=payload(guidance),
    )
    source_artifact_sha256 = {
        "registry": registry["artifact_sha256"],
        "global_prefix": global_prefix["artifact_sha256"],
        "conditional_prefixes": conditional["artifact_sha256"],
        "qualifications": qualifications["artifact_sha256"],
        "native_scores": scores["artifact_sha256"],
        "analysis": resealed_analysis["artifact_sha256"],
        "guidance": resealed_guidance["artifact_sha256"],
    }
    streams = [global_prefix["stream"], *conditional["streams"]]
    formal_evidence_body = {
        "document_kind": "s11_formal_evidence_attestation",
        "schema_version": 1,
        "checkpoint_id": "S11",
        "lock_sha256": LOCK_ID,
        "production_schedule": {
            "chunk_nominal_draws": 512,
            "global_target_accepted": 8192,
            "global_complete_chunks": 65536,
            "conditional_target_accepted": 256,
            "conditional_complete_chunks": 512,
            "conditional_stream_ids": [
                stream["stream_id"] for stream in conditional["streams"]
            ],
        },
        "source_artifact_sha256": source_artifact_sha256,
        "streams": [
            {
                "stream_id": stream["stream_id"],
                "target_accepted": 8192 if index == 0 else 256,
                "hard_cap_chunks": 65536 if index == 0 else 512,
                "nominal_slots_per_chunk": 512,
                "ledger_replay_sha256": canonical_sha256(stream["ledger_replay"]),
                "credited_rows_sha256": canonical_sha256(stream["credited_rows"]),
                "chunk_hashes_sha256": stream["chunk_hashes_sha256"],
                "raw_files": [
                    {"path": f"synthetic/{index}.json", "sha256": f"{index + 1:064x}"}
                ],
            }
            for index, stream in enumerate(streams)
        ],
        "dependency_chain_verified": True,
        "synthetic": False,
    }
    formal_evidence = {
        **formal_evidence_body,
        "evidence_sha256": canonical_sha256(formal_evidence_body),
    }
    return (
        registry,
        global_prefix,
        conditional,
        qualifications,
        scores,
        resealed_analysis,
        resealed_guidance,
        formal_evidence,
    )


def test_alpha0_flip_is_reported_but_does_not_change_decision() -> None:
    registry, global_prefix, conditional, qualifications, scores = (
        synthetic_scientific_artifacts()
    )
    contract = load_contract()
    analysis, guidance = build_analysis_and_guidance(
        registry=registry,
        global_prefix=global_prefix,
        conditional_prefixes=conditional,
        qualifications=qualifications,
        native_scores=scores,
        contract=contract,
        lock_sha256=LOCK_ID,
    )
    guided_gene = next(iter(guidance["genes"]))
    alpha0 = analysis["bias_diagnostics"]["genes"][guided_gene][
        "alpha0_sensitivity"
    ]
    assert alpha0["guided_status_flip_evaluated"] is True
    assert alpha0["alpha0_decision_flip"] is True
    assert alpha0["alpha0_decision_flip"] == (
        alpha0["guided_status_flip"]
        or alpha0["alpha0_bestworst_flip"]
        or alpha0["discrete_lambda_flip"]
    )
    assert alpha0["alpha0_global_lambda"] == analysis["bias_diagnostics"][
        "alpha0_projection"
    ]["global_lambda"]
    assert all(
        "alpha0" not in gate
        for result in analysis["gene_results"].values()
        for gate in result["model_test_results"]
    )
    without_diagnostics = copy.deepcopy(analysis)
    del without_diagnostics["bias_diagnostics"]
    assert canonical_json_bytes(
        _guided_decision_projection(analysis, guidance, contract)
    ) == canonical_json_bytes(
        _guided_decision_projection(without_diagnostics, guidance, contract)
    )
    reported_decision = _edge_decision_from_analysis(analysis, guidance)
    changed_report = copy.deepcopy(analysis)
    changed_report["bias_diagnostics"]["genes"][guided_gene][
        "alpha0_sensitivity"
    ]["alpha0_decision_flip"] = False
    changed_report["bias_diagnostics"]["alpha0_projection"][
        "decision_flip"
    ] = False
    assert canonical_json_bytes(reported_decision) == canonical_json_bytes(
        _edge_decision_from_analysis(changed_report, guidance)
    )
    assert reported_decision["terminal_code"] == "FT-INCONCLUSIVE"
    assert branch_artifact_policy(reported_decision)["edge"] is None


def test_alpha0_no_flip_is_reported_and_real_edge_is_unchanged() -> None:
    registry, global_prefix, conditional, qualifications, scores = (
        synthetic_scientific_artifacts(conditional_count=512)
    )
    contract = load_contract()
    analysis, guidance = build_analysis_and_guidance(
        registry=registry,
        global_prefix=global_prefix,
        conditional_prefixes=conditional,
        qualifications=qualifications,
        native_scores=scores,
        contract=contract,
        lock_sha256=LOCK_ID,
    )
    guided_gene = next(iter(guidance["genes"]))
    alpha0 = analysis["bias_diagnostics"]["genes"][guided_gene][
        "alpha0_sensitivity"
    ]
    assert alpha0["guided_status_flip_evaluated"] is True
    assert alpha0["guided_status_flip"] is False
    assert alpha0["alpha0_bestworst_flip"] is False
    assert alpha0["discrete_lambda_flip"] is False
    assert alpha0["alpha0_decision_flip"] is False

    without_diagnostics = copy.deepcopy(analysis)
    del without_diagnostics["bias_diagnostics"]
    assert canonical_json_bytes(
        _guided_decision_projection(analysis, guidance, contract)
    ) == canonical_json_bytes(
        _guided_decision_projection(without_diagnostics, guidance, contract)
    )
    actual_decision = _edge_decision_from_analysis(analysis, guidance)
    changed_report = copy.deepcopy(analysis)
    changed_report["bias_diagnostics"]["genes"][guided_gene][
        "alpha0_sensitivity"
    ]["alpha0_decision_flip"] = True
    changed_report["bias_diagnostics"]["alpha0_projection"][
        "decision_flip"
    ] = True
    assert canonical_json_bytes(actual_decision) == canonical_json_bytes(
        _edge_decision_from_analysis(changed_report, guidance)
    )
    assert actual_decision["terminal_code"] == "S1_GUIDANCE_LOCKED"
    assert branch_artifact_policy(actual_decision)["edge"] == "S12"


def test_option_c_only_guided_gene_flips_is_inconclusive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis, guidance, _ = _build_option_c_analysis(
        monkeypatch, {"G": (True, True)}
    )
    gate = analysis["option_c_shrinkage_gate"]
    assert analysis["gene_results"]["G"]["guided"] is True
    assert analysis["all_model_gates_pass"] is True
    assert gate == {
        "active": True,
        "policy": "alpha0_decision_flip_disqualifies_guided_gene",
        "guided_genes_alpha32": ["G"],
        "alpha0_disqualified_genes": ["G"],
        "robust_guided_gene_count": 0,
        "shrinkage_robustness_shortage": True,
    }
    assert analysis["stable_guided_gene_count"] == 0
    assert "shrinkage_robustness_shortage" in analysis["material_shortages"]
    decision = _edge_decision_from_analysis(analysis, guidance)
    assert decision["terminal_code"] == "FT-INCONCLUSIVE"
    assert decision["terminal_code"] not in {
        "S1_GUIDANCE_LOCKED",
        "COMPLETE_DETERMINISTIC_NO_GUIDANCE",
    }


def test_option_c_non_flipping_guided_gene_stays_positive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis, guidance, _ = _build_option_c_analysis(
        monkeypatch, {"G": (True, False)}
    )
    gate = analysis["option_c_shrinkage_gate"]
    assert gate["guided_genes_alpha32"] == ["G"]
    assert gate["alpha0_disqualified_genes"] == []
    assert gate["robust_guided_gene_count"] == 1
    assert gate["shrinkage_robustness_shortage"] is False
    assert analysis["stable_guided_gene_count"] == 1
    assert "shrinkage_robustness_shortage" not in analysis["material_shortages"]
    decision = _edge_decision_from_analysis(analysis, guidance)
    assert decision["terminal_code"] == "S1_GUIDANCE_LOCKED"
    assert branch_artifact_policy(decision)["edge"] == "S12"


def test_option_c_mixed_guided_genes_drops_only_flipper_and_stays_positive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis, guidance, _ = _build_option_c_analysis(
        monkeypatch, {"G": (True, True), "H": (True, False)}
    )
    gate = analysis["option_c_shrinkage_gate"]
    assert gate["guided_genes_alpha32"] == ["G", "H"]
    assert gate["alpha0_disqualified_genes"] == ["G"]
    assert gate["robust_guided_gene_count"] == 1
    assert gate["shrinkage_robustness_shortage"] is False
    assert analysis["stable_guided_gene_count"] == 1
    assert _edge_decision_from_analysis(analysis, guidance)[
        "terminal_code"
    ] == "S1_GUIDANCE_LOCKED"


def test_option_c_decision_records_gate_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis, guidance, artifacts = _build_option_c_analysis(
        monkeypatch, {"G": (True, True)}
    )
    (
        registry,
        global_prefix,
        conditional,
        qualifications,
        scores,
        analysis,
        guidance,
        formal_evidence,
    ) = _reseal_formal_decision_sources(analysis, guidance, artifacts)
    decision = decide_from_artifacts(
        registry=registry,
        global_prefix=global_prefix,
        conditional_prefixes=conditional,
        qualifications=qualifications,
        native_scores=scores,
        analysis=analysis,
        guidance=guidance,
        formal_evidence=formal_evidence,
    )
    assert decision["option_c_shrinkage_gate"] == analysis[
        "option_c_shrinkage_gate"
    ]
    assert decision["option_c_shrinkage_gate"]["active"] is True
    assert decision["option_c_shrinkage_gate"][
        "alpha0_disqualified_genes"
    ] == ["G"]
    body = dict(decision)
    recorded_sha256 = body.pop("decision_sha256")
    assert recorded_sha256 == canonical_sha256(body)


def test_option_c_zero_guided_is_no_guidance_and_preserves_primary_semantics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis, guidance, _ = _build_option_c_analysis(
        monkeypatch, {"G": (False, True)}
    )
    gate = analysis["option_c_shrinkage_gate"]
    assert gate["guided_genes_alpha32"] == []
    assert gate["alpha0_disqualified_genes"] == []
    assert gate["shrinkage_robustness_shortage"] is False
    assert "shrinkage_robustness_shortage" not in analysis["material_shortages"]
    assert _edge_decision_from_analysis(analysis, guidance)[
        "terminal_code"
    ] == "COMPLETE_DETERMINISTIC_NO_GUIDANCE"

    contract = load_contract()
    assert contract["statistics"]["alpha"] == 32
    assert contract["statistics"]["sensitivity_min"] == 0.05
    assert contract["statistics"]["score_coverage_min"] == 0.95
    assert contract["statistics"]["ci_half_width_max"] == 0.025
    assert contract["statistics"]["best_worst_recurrence_min"] == 0.90
    assert contract["statistics"]["normalized_entropy_min"] == 0.80
    assert contract["statistics"]["lambda_grid"] == {
        "start": 0.0,
        "stop": 8.0,
        "step": 0.25,
    }
    assert HALF_CATEGORICAL_PROJECTION_FIELDS == (
        "trust_states",
        "trust_reasons",
        "trusted_sets",
        "guided_states",
        "guided_reasons",
        "best_worst",
        "per_size_directions",
        "own_null_pass",
        "familywise_null_pass",
        "same_positive_global_lambda",
        "shuffle_mapping",
        "per_size_and_aggregate_direction",
        "each_model_test_result",
    )
    assert analysis["bias_diagnostics"]["alpha0_projection"][
        "reported_only"
    ] is True
    assert analysis["bias_diagnostics"]["genes"]["G"]["alpha0_sensitivity"][
        "alpha0_decision_flip"
    ] is True
    assert set(analysis["gene_results"]["G"]["model_test_results"]) == {
        "alpha32_primary_gate"
    }


def _decision_loss_surface(surface_id: str) -> dict:
    return next(
        surface
        for surface in decision_loss_panel()
        if surface["surface_id"] == surface_id
    )


@pytest.fixture(scope="module")
def decision_loss_masks_runs() -> tuple[dict, dict]:
    surface = _decision_loss_surface("shrinkage_masks_realgap")
    return (
        run_decision_loss_simulation(panel=[surface]),
        run_decision_loss_simulation(panel=[surface]),
    )


def test_decision_loss_shrinkage_helps_recommends_option_b() -> None:
    surface = _decision_loss_surface("shrinkage_helps_lowsupport")
    assert len(set(surface["n_gv"].values())) == 2
    result = run_decision_loss_simulation(panel=[surface])
    regime = result["per_regime"][0]
    assert regime["truth"]["truth_source"] == (
        "noise_free_true_means_via_real_alpha0_projection"
    )
    assert regime["truth"]["sensitivity"] == pytest.approx(
        max(surface["true_mean_hint"].values())
        - min(surface["true_mean_hint"].values())
    )
    assert regime["truth"]["sensitivity"] < DECISION_LOSS_SENSITIVITY_MIN
    assert regime["loss_alpha32"] < regime["loss_alpha0"]
    assert result["recommended_option"] == "OPTION_B_REPORT_ONLY"
    assert result["aggregate"]["paired_delta"] <= 0.0


def test_decision_loss_shrinkage_masks_gap_recommends_option_c(
    decision_loss_masks_runs: tuple[dict, dict],
) -> None:
    result = decision_loss_masks_runs[0]
    regime = result["per_regime"][0]
    assert min(regime["n_gv"].values()) >= 24
    assert regime["truth"]["truth_source"] == (
        "noise_free_true_means_via_real_alpha0_projection"
    )
    surface = _decision_loss_surface("shrinkage_masks_realgap")
    assert regime["truth"]["sensitivity"] == pytest.approx(
        max(surface["true_mean_hint"].values())
        - min(surface["true_mean_hint"].values())
    )
    assert regime["truth"]["sensitivity"] > DECISION_LOSS_SENSITIVITY_MIN
    assert regime["loss_alpha32"] > regime["loss_alpha0"]
    assert result["recommended_option"] == "OPTION_C_GATE_FLIP"
    assert (
        result["aggregate"]["weighted_paired_delta"] > DECISION_LOSS_MARGIN
    )


def test_decision_loss_unequal_support_flips_best_worst_detected(
    decision_loss_masks_runs: tuple[dict, dict],
) -> None:
    surface = _decision_loss_surface("shrinkage_masks_realgap")
    assert len(set(surface["n_gv"].values())) == 2
    regime = decision_loss_masks_runs[0]["per_regime"][0]
    assert regime["bestworst_flip_detected"] is True
    assert regime["discrete_lambda"]["alpha32"]
    assert regime["discrete_lambda"]["alpha0"]


def test_decision_loss_invokes_real_selection_functions(monkeypatch) -> None:
    import s11.workflow as workflow_module

    original = workflow_module.joint_permutation_test
    calls = 0

    def counted_joint_permutation_test(*args: object, **kwargs: object) -> dict:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        workflow_module, "joint_permutation_test", counted_joint_permutation_test
    )
    surface = _decision_loss_surface("tiny_n_1to8_additive")
    result = run_decision_loss_simulation(panel=[surface])
    assert calls > 0
    assert result["gate_replicates"] == 2000
    assert result["selection_path"] == (
        "workflow.build_analysis_and_guidance/_frame_analysis"
    )


def test_decision_loss_deterministic_reproducibility(
    decision_loss_masks_runs: tuple[dict, dict],
) -> None:
    first, second = decision_loss_masks_runs
    assert first["result_sha256"] == second["result_sha256"]
    assert first["panel_spec_hash"] == second["panel_spec_hash"]
    assert first["recommended_option"] == second["recommended_option"]


def test_decision_loss_sim_does_not_change_normal_analysis(
    guided_analysis_bundle: tuple[dict, dict, tuple[dict, dict, dict, dict, dict]],
) -> None:
    analysis, guidance, artifacts = guided_analysis_bundle
    registry, global_prefix, conditional, qualifications, scores = artifacts
    contract = load_contract()
    before = canonical_json_bytes(
        _guided_decision_projection(analysis, guidance, contract)
    )
    simulation = run_decision_loss_simulation(
        panel=[_decision_loss_surface("tiny_n_1to8_additive")]
    )
    assert simulation["gating"] is False
    assert simulation["wires_alpha0_into_gate"] is False
    rebuilt_analysis, rebuilt_guidance = build_analysis_and_guidance(
        registry=registry,
        global_prefix=global_prefix,
        conditional_prefixes=conditional,
        qualifications=qualifications,
        native_scores=scores,
        contract=contract,
        lock_sha256=LOCK_ID,
    )
    after = canonical_json_bytes(
        _guided_decision_projection(rebuilt_analysis, rebuilt_guidance, contract)
    )
    assert before == after


@pytest.fixture(scope="module")
def guided_analysis_bundle() -> tuple[
    dict, dict, tuple[dict, dict, dict, dict, dict]
]:
    registry, global_prefix, conditional, qualifications, scores = (
        synthetic_scientific_artifacts()
    )
    analysis, guidance = build_analysis_and_guidance(
        registry=registry, global_prefix=global_prefix,
        conditional_prefixes=conditional, qualifications=qualifications,
        native_scores=scores, contract=load_contract(), lock_sha256=LOCK_ID,
    )
    return analysis, guidance, (
        registry, global_prefix, conditional, qualifications, scores
    )


def test_artifact_derived_population_analysis_guidance_and_decision_end_to_end(
    guided_analysis_bundle: tuple[dict, dict, tuple[dict, dict, dict, dict, dict]],
) -> None:
    analysis, guidance, artifacts = guided_analysis_bundle
    registry, global_prefix, conditional, qualifications, scores = artifacts
    assert analysis["population_summary"]["global_fraw_count"] == 4
    assert analysis["population_summary"]["conditional_fraw_count"] == 256
    assert analysis["permutation"]["replicates"] == 2000
    assert all(
        result["bootstrap"]["replicates"] == 2000
        for result in analysis["gene_results"].values()
    )
    assert analysis["read_audit"]["conditional_entered_global_ecdf"] is False
    assert analysis["semantic_half_stability"]["stable"] is True
    assert guidance["positive_global_lambda"] is True
    guided_gene = next(iter(guidance["genes"]))
    assert set(analysis["bias_diagnostics"]["genes"][guided_gene]) == {
        "survivorship",
        "alpha0_sensitivity",
        "arm_sensitivity",
    }
    assert "validity_diagnostics" in analysis["bias_diagnostics"]
    assert analysis["bias_diagnostics"]["per_size_margin"]["reweighted_genes"] == [
        guided_gene
    ]
    assert analysis["bias_diagnostics"]["per_size_margin"]["note"] == (
        "formocast_model_margin_terminal_frame_relative_not_real_speedup"
    )
    # Synthetic summaries exercise population/statistics mechanics only.  They
    # are deliberately inadmissible to the formal decision without production
    # raw chunk/ledger evidence.
    with pytest.raises(DecisionError, match="ledger-derived evidence"):
        decide_from_artifacts(
            global_prefix=global_prefix, conditional_prefixes=conditional,
            qualifications=qualifications, analysis=analysis, guidance=guidance,
        )
    tampered = copy.deepcopy(analysis)
    tampered["population_summary"]["global_uexec_count"] = 256
    with pytest.raises(DecisionError, match="self-hash"):
        decide_from_artifacts(
            registry=registry,
            global_prefix=global_prefix, conditional_prefixes=conditional,
            qualifications=qualifications, native_scores=scores,
            analysis=tampered, guidance=guidance, formal_evidence={},
        )


@pytest.fixture(scope="module")
def multi_gene_analysis_bundle() -> tuple[dict, dict, dict, dict]:
    registry, global_prefix, conditional, qualifications, scores = (
        multi_gene_scientific_artifacts()
    )
    analysis, guidance = build_analysis_and_guidance(
        registry=registry,
        global_prefix=global_prefix,
        conditional_prefixes=conditional,
        qualifications=qualifications,
        native_scores=scores,
        contract=load_contract(),
        lock_sha256=LOCK_ID,
    )
    return analysis, guidance, registry, global_prefix


@pytest.fixture(scope="module")
def validity_multi_gene_analysis_bundle() -> tuple[dict, dict, dict, dict]:
    registry, global_prefix, conditional, qualifications, scores = (
        multi_gene_scientific_artifacts(validity_frame=True)
    )
    analysis, guidance = build_analysis_and_guidance(
        registry=registry,
        global_prefix=global_prefix,
        conditional_prefixes=conditional,
        qualifications=qualifications,
        native_scores=scores,
        contract=load_contract(),
        lock_sha256=LOCK_ID,
    )
    return analysis, guidance, registry, global_prefix


def test_multi_gene_emitted_arm_theta_and_global_per_size_margin(
    multi_gene_analysis_bundle: tuple[dict, dict, dict, dict],
) -> None:
    analysis, guidance, registry, _ = multi_gene_analysis_bundle
    assert set(guidance["genes"]) == {"G"}
    bias = analysis["bias_diagnostics"]
    assert set(bias["genes"]) == {"G", "H"}
    assert analysis["gene_results"]["H"]["guided"] is False
    for gene in ("G", "H"):
        assert "arm_sensitivity" in bias["genes"][gene]
    bundle = guidance["genes"]["G"]
    for index, candidate_id in enumerate(bundle["candidate_order"]):
        assert bias["arm_laws"]["F"]["G"][candidate_id] == pytest.approx(
            bundle["p1"][index]
        )
        assert bias["arm_laws"]["S"]["G"][candidate_id] == pytest.approx(
            0.20 * bundle["p0"][index]
            + 0.80 * bundle["shuffle"]["q_shuffled"][index]
        )
    assert bias["arm_laws"]["sources"]["H"] == "unguided_baseline_all_arms"
    assert bias["arm_laws"]["F"]["H"] == bias["arm_laws"]["G"]["H"]
    assert bias["arm_laws"]["S"]["H"] == bias["arm_laws"]["G"]["H"]

    gene_ids = {
        row["gene"]: row["candidate_ids"] for row in registry["eligible_genes"]
    }
    target = gene_ids["H"][0]
    arm_report = bias["genes"]["H"]["arm_sensitivity"]
    assert arm_report["ess_min_fraction"] == 0.05
    assert arm_report[target]["theta"]["G"] == pytest.approx(
        (71.0 * 0.75 + 59.0 * 0.25) / 130.0
    )
    g_baseline = bias["arm_laws"]["G"]["G"]
    g_f = bias["arm_laws"]["F"]["G"]
    g_s = bias["arm_laws"]["S"]["G"]
    g_ids = gene_ids["G"]

    def tilted_theta(law: dict) -> float:
        weights = [
            law[candidate_id] / g_baseline[candidate_id]
            for candidate_id in g_ids
        ]
        return (71.0 * weights[0] * 0.75 + 59.0 * weights[1] * 0.25) / (
            71.0 * weights[0] + 59.0 * weights[1]
        )

    assert arm_report[target]["theta"]["F"] == pytest.approx(tilted_theta(g_f))
    assert arm_report[target]["theta"]["S"] == pytest.approx(tilted_theta(g_s))
    assert type(arm_report["ordering_change_F"]) is bool
    assert type(arm_report["bestworst_change_S"]) is bool

    margin = bias["per_size_margin"]
    assert margin["survivor_occurrence_count"] == 516
    assert margin["reweighted_genes"] == ["G", "H"]
    base_latencies = {
        (0, 0): [1.0, 2.0, 4.0],
        (0, 1): [1.0, 2.0, 4.0],
        (1, 0): [10.0, 20.0, 40.0],
        (1, 1): [10.0, 20.0, 40.0],
    }
    occurrence_counts = {(0, 0): 135, (0, 1): 123, (1, 0): 123, (1, 1): 135}

    def expected_log(arm: str, size_index: int) -> float:
        weighted = []
        for (g_index, h_index), latencies in base_latencies.items():
            g_id = gene_ids["G"][g_index]
            h_id = gene_ids["H"][h_index]
            weight = (
                bias["arm_laws"][arm]["G"][g_id]
                / bias["arm_laws"]["G"]["G"][g_id]
                * bias["arm_laws"][arm]["H"][h_id]
                / bias["arm_laws"]["G"]["H"][h_id]
                * occurrence_counts[(g_index, h_index)]
            )
            weighted.append((weight, math.log(latencies[size_index])))
        return sum(weight * value for weight, value in weighted) / sum(
            weight for weight, _ in weighted
        )

    expected_g_minus_f = [
        expected_log("G", size_index) - expected_log("F", size_index)
        for size_index in range(3)
    ]
    expected_s_minus_f = [
        expected_log("S", size_index) - expected_log("F", size_index)
        for size_index in range(3)
    ]
    assert margin["contrast_G_minus_F"] == pytest.approx(expected_g_minus_f)
    assert margin["contrast_S_minus_F"] == pytest.approx(expected_s_minus_f)
    assert margin["ratio_G_over_F"] == pytest.approx(
        [math.exp(value) for value in expected_g_minus_f]
    )
    assert margin["ratio_S_over_F"] == pytest.approx(
        [math.exp(value) for value in expected_s_minus_f]
    )
    assert all(abs(value) > 0.0 for value in margin["contrast_G_minus_F"])
    assert all(abs(value) > 0.0 for value in margin["contrast_S_minus_F"])
    assert all(value != pytest.approx(1.0) for value in margin["ratio_G_over_F"])
    assert margin["note"] == (
        "formocast_model_margin_terminal_frame_relative_not_real_speedup"
    )


def test_validity_A_h_both_directions(
    validity_multi_gene_analysis_bundle: tuple[dict, dict, dict, dict],
) -> None:
    analysis, _, _, _ = validity_multi_gene_analysis_bundle
    validity = analysis["bias_diagnostics"]["validity_diagnostics"]
    reports = validity["additive_rank_faithfulness"]
    directions = {"left_train_right_eval", "right_train_left_eval"}
    assert set(reports) == directions
    for report in reports.values():
        assert type(report["rho"]) is float
        assert report["rho"] > 0.90
        assert report["not_estimable"] is False
        assert report["center_rule"] == (
            "train_half_occurrence_weighted_mean_marginal"
        )
        interpretation = report["interpretation"]
        assert "additive-faithfulness localization diagnostic" in interpretation
        assert (
            "not an orthogonal interaction-variance/Sobol decomposition"
            in interpretation
        )
        assert "not proof of epistasis" in interpretation
        assert "factorization/additive layer" in interpretation
        assert report["reported_only"] is True
        assert report["gating"] is False
        assert report["non_independent_shared_conditional_corpus"] is True
        assert "share the sealed conditional corpus" in report[
            "non_independent_replication_note"
        ]
        assert report["n_eval"] == 4
    assert reports["left_train_right_eval"] is not reports["right_train_left_eval"]
    assert validity["metadata"] == {
        "non_independent_shared_conditional_corpus": True,
        "non_independent_replication_note": (
            "cross-fit halves share the sealed conditional corpus and are not "
            "independent replication"
        ),
        "reported_only": True,
        "gating": False,
        "center_rule": "train_half_occurrence_weighted_mean_marginal",
        "ess_min_fraction": 0.05,
        "arm_law_mix": 0.20,
        "cross_fit": "both_directions_train_one_half_eval_opposite",
    }


def test_validity_emitted_prior_V_contrasts_and_ess(
    validity_multi_gene_analysis_bundle: tuple[dict, dict, dict, dict],
) -> None:
    analysis, _, registry, global_prefix = validity_multi_gene_analysis_bundle
    reports = analysis["bias_diagnostics"]["validity_diagnostics"][
        "emitted_prior_reconstruction"
    ]
    for report in reports.values():
        assert report["not_applicable"] is False
        assert report["not_estimable"] is False
        assert set(report["V"]) == {"G", "F", "S"}
        assert type(report["V_F_minus_G"]) is float
        assert type(report["V_F_minus_S"]) is float
        assert set(report["ess"]) == {"G", "F", "S"}
        assert set(report["ess_fraction"]) == {"G", "F", "S"}
        assert all(report["ess"][arm] >= 1.0 for arm in ("G", "F", "S"))
        assert all(
            report["ess_fraction"][arm] >= report["ess_min_fraction"]
            for arm in ("G", "F", "S")
        )
        assert report["ess_min_fraction"] == 0.05
        assert report["V"]["G"] == pytest.approx(0.5)
        assert report["replicates"] == 2000
        assert report["block"] == "occurrence"
        assert report["bootstrap_reason"] is None
        assert report["interpretation"] == (
            "incremental-density-tilt held-out benefit reconstruction; "
            "label-blind Formocast model quantity, not real performance"
        )
        assert "share the sealed conditional corpus" in report[
            "non_independent_replication_note"
        ]
        for interval_key in ("ci_V_F_minus_G", "ci_V_F_minus_S"):
            interval = report[interval_key]
            assert type(interval) is list and len(interval) == 2
            assert all(
                type(value) is float and math.isfinite(value)
                for value in interval
            )
            assert interval[0] <= interval[1]

    gene_rows = {row["gene"]: row for row in registry["eligible_genes"]}
    left_probabilities = analysis["fixed_halves"]["left_tuple"][
        "per_gene_guidance_probabilities"
    ]
    assert set(left_probabilities) == {"G", "H"}
    baseline = {
        gene: dict(zip(row["candidate_ids"], row["baseline_probabilities"]))
        for gene, row in gene_rows.items()
    }
    left_f = {
        gene: dict(zip(gene_rows[gene]["candidate_ids"], probabilities))
        for gene, probabilities in left_probabilities.items()
    }
    eval_rows = global_prefix["stream"]["credited_rows"][4:]
    benefit_by_assignment = {
        (0, 0): 0.875,
        (0, 1): 0.625,
        (1, 0): 0.375,
        (1, 1): 0.125,
    }
    eval_benefits = [
        benefit_by_assignment[
            (row["raw_configuration"]["G"], row["raw_configuration"]["H"])
        ]
        for row in eval_rows
    ]
    weights = []
    for row in eval_rows:
        weight = 1.0
        for gene in ("G", "H"):
            candidate_id = row["candidate_ids"][gene]
            weight *= left_f[gene][candidate_id] / baseline[gene][candidate_id]
        weights.append(weight)
    expected_v_f = sum(
        weight * benefit for weight, benefit in zip(weights, eval_benefits)
    ) / sum(weights)
    assert reports["left_train_right_eval"]["V"]["F"] == pytest.approx(
        expected_v_f
    )


def test_validity_not_applicable_when_no_guided_gene() -> None:
    registry, global_prefix, conditional, qualifications, scores = (
        synthetic_scientific_artifacts(conditional_count=1)
    )
    analysis, guidance = build_analysis_and_guidance(
        registry=registry,
        global_prefix=global_prefix,
        conditional_prefixes=conditional,
        qualifications=qualifications,
        native_scores=scores,
        contract=load_contract(),
        lock_sha256=LOCK_ID,
    )
    assert guidance["genes"] == {}
    validity = analysis["bias_diagnostics"]["validity_diagnostics"]
    for report in validity["emitted_prior_reconstruction"].values():
        assert report["not_applicable"] is True
        assert report["reason"] == "no_emitted_prior_no_guided_gene"
        assert "label-blind Formocast model quantity" in report["interpretation"]
        assert "V" not in report
    for report in validity["additive_rank_faithfulness"].values():
        assert report["n_eval"] >= 1
        assert report["reported_only"] is True


def test_validity_not_estimable_on_poor_overlap() -> None:
    eval_rows = [
        {"candidate_ids": {"G": "x"}, "benefit": 1.0}
    ] + [
        {"candidate_ids": {"G": "y"}, "benefit": 0.0}
        for _ in range(99)
    ]
    report = emitted_prior_reconstruction(
        arm_laws_train={
            "G": {"G": {"x": 0.5, "y": 0.5}},
            "F": {"G": {"x": 1.0, "y": 0.0}},
            "S": {"G": {"x": 0.5, "y": 0.5}},
        },
        baseline_train={"G": {"x": 0.5, "y": 0.5}},
        eval_rows=eval_rows,
        master_nonce="1" * 64,
        direction_tag="poor_overlap_test",
    )
    assert report["not_applicable"] is False
    assert report["not_estimable"] is True
    assert report["ess_min_fraction"] == 0.05
    assert report["ess"]["F"] == pytest.approx(1.0)
    assert report["ess_fraction"]["F"] == pytest.approx(0.01)
    assert report["V"]["F"] is None
    assert report["V_F_minus_G"] is None
    assert report["V_F_minus_S"] is None
    assert report["ci_V_F_minus_G"] is None
    assert report["reason"] == "poor_overlap"


def test_validity_diagnostics_are_non_gating_byte_identical(
    guided_analysis_bundle: tuple[dict, dict, tuple[dict, dict, dict, dict, dict]],
) -> None:
    analysis, guidance, _ = guided_analysis_bundle
    guidance_snapshot = copy.deepcopy(guidance)
    without = copy.deepcopy(analysis)
    del without["bias_diagnostics"]["validity_diagnostics"]
    contract = load_contract()
    assert canonical_json_bytes(
        _guided_decision_projection(analysis, guidance, contract)
    ) == canonical_json_bytes(
        _guided_decision_projection(without, guidance, contract)
    )
    for field in (
        "gene_results",
        "stable_guided_gene_count",
        "all_model_gates_pass",
        "semantic_half_stability",
    ):
        assert canonical_json_bytes(analysis[field]) == canonical_json_bytes(
            without[field]
        )
    assert canonical_json_bytes(guidance) == canonical_json_bytes(guidance_snapshot)
    assert guidance["canonical_guidance_hash"] == guidance_snapshot[
        "canonical_guidance_hash"
    ]
    decision = _edge_decision_from_analysis(analysis, guidance)
    decision_without = _edge_decision_from_analysis(without, guidance)
    assert canonical_json_bytes(decision) == canonical_json_bytes(decision_without)
    assert decision["terminal_code"] == "FT-INCONCLUSIVE"
    assert branch_artifact_policy(decision)["edge"] is None


@pytest.mark.parametrize(
    "updates,code",
    [
        ({"label_leakage": True, "integrity_failure": True}, "EVIDENCE_INVALID"),
        ({"integrity_failure": True}, "CHANGES_REQUIRED"),
        ({"material_stochastic_shortage": True}, "FT-INCONCLUSIVE"),
        ({}, "S1_GUIDANCE_LOCKED"),
        ({"stable_guided_gene_count": 0}, "COMPLETE_DETERMINISTIC_NO_GUIDANCE"),
    ],
)
def test_terminal_first_match_branches_and_artifact_edge_exclusivity(updates: dict, code: str) -> None:
    result = decide(decision_inputs(**updates))
    assert result["terminal_code"] == code
    policy = branch_artifact_policy(result)
    if code == "S1_GUIDANCE_LOCKED":
        assert policy == {"scientific_report": "forbidden", "compact_gate_record": "required", "edge": "S12"}
    elif code in ("FT-INCONCLUSIVE", "COMPLETE_DETERMINISTIC_NO_GUIDANCE"):
        assert policy["scientific_report"] == "required" and policy["edge"] is None
    else:
        assert policy["scientific_report"] == "forbidden" and policy["edge"] is None


def test_formal_firewall_and_output_path_symlink_escape(tmp_path: Path) -> None:
    with pytest.raises(WorkflowError):
        _firewall({"metric": "real_GFLOPS"})
    repository = tmp_path / "repository"
    repository.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (repository / "safe").symlink_to(outside, target_is_directory=True)
    contract = {"write_boundaries": {"execution_whitelist_exact": ["safe/result.json"]}}
    with pytest.raises(WorkflowError, match="symlink"):
        _allowed_output(contract, repository / "safe/result.json", repository)


@pytest.mark.parametrize(
    "decision_updates,expected_branch",
    [
        ({}, "positive"),
        ({"stable_guided_gene_count": 0}, "negative_or_inconclusive"),
        ({"material_stochastic_shortage": True}, "negative_or_inconclusive"),
    ],
)
def test_closeout_end_to_end_derives_git_branch_paths_hashes_ack_and_push(
    tmp_path: Path, decision_updates: dict, expected_branch: str
) -> None:
    repository = tmp_path / "closeout-repository"
    repository.mkdir()
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "S11 Test",
        "GIT_AUTHOR_EMAIL": "s11@example.invalid",
        "GIT_COMMITTER_NAME": "S11 Test",
        "GIT_COMMITTER_EMAIL": "s11@example.invalid",
    }

    def git(*arguments: str) -> bytes:
        return subprocess.run(
            ["git", "-c", "commit.gpgsign=false", *arguments],
            cwd=repository, env=git_env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout

    git("init", "-q")
    (repository / "initial.txt").write_text("initial\n", encoding="ascii")
    projection_paths = [
        Path("study_docs/research/ductile-origami-warmstart-experiment-plan.md"),
        Path("study_docs/research/ductile-origami-warmstart/README.md"),
        Path("study_docs/research/ductile-origami-warmstart/s11-stage1-model-only-factorization-design.md"),
    ]
    for path in projection_paths:
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    git("add", "initial.txt", *(str(path) for path in projection_paths))
    git("commit", "-q", "-m", "initial")

    decision_path = Path(
        "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s11-decision.json"
    )
    reproduction_path = Path(
        "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s11-reproduction.json"
    )
    decision = decide(decision_inputs(**decision_updates))
    decision_target = repository / decision_path
    decision_target.parent.mkdir(parents=True)
    decision_target.write_bytes(canonical_json_bytes(decision) + b"\n")
    projection = {
        field: decision[field]
        for field in (
            "terminal_code", "operational_status", "scientific_outcome",
            "criterion", "edge", "required_action",
        )
    }
    reproduction_body = {
        "document_kind": "s11_reproduction", "schema_version": 1,
        "checkpoint_id": "S11", "decision_sha256": decision["decision_sha256"],
        "decision_projection": projection, "fresh_whole_bundle_replay": True,
        "exact_parity": True,
    }
    reproduction = {
        **reproduction_body,
        "reproduction_sha256": canonical_sha256(reproduction_body),
    }
    reproduction_target = repository / reproduction_path
    reproduction_target.write_bytes(canonical_json_bytes(reproduction) + b"\n")
    manifest_paths = [
        Path("study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-registry.json"),
        Path("study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-global-prefix.json"),
        Path("study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-conditional-prefixes.json"),
        Path("study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-qualifications.json"),
        Path("study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-native-scores.json"),
        Path("study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-analysis.json"),
        Path("study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-guidance.json"),
    ]
    gate_path = Path(
        "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/"
        "gate-records/s11-s1-guidance-locked.json"
    )
    report_path = Path(
        "study_docs/research/ductile-origami-warmstart/reports/staged/"
        "s11-stage1-model-only-factorization-report.md"
    )
    branch_path = gate_path if expected_branch == "positive" else report_path
    for path in [*manifest_paths, branch_path]:
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("sealed S11 result\n", encoding="utf-8")
    for path in projection_paths:
        parent_raw = git("show", f"HEAD:{path}")
        (repository / path).write_bytes(
            _render_projection_document(
                parent_raw=parent_raw, path=str(path), decision=decision,
                reproduction=reproduction,
            )
        )
    expected_paths = [
        str(decision_path), str(reproduction_path),
        *(str(path) for path in manifest_paths), str(branch_path),
        *(str(path) for path in projection_paths),
    ]
    git("add", *expected_paths)
    git("commit", "-q", "-m", "S11 synthetic closeout\n\nClosure-Unit: CU-S1-MECHANISM")
    commit = git("rev-parse", "HEAD").decode("ascii").strip()
    observed = [
        item for item in git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", commit
        ).decode("utf-8").splitlines() if item
    ]
    bindings = []
    for path in observed:
        fields = git("ls-tree", commit, "--", path).decode("utf-8").strip().split(None, 3)
        bindings.append({
            "path": path, "git_blob_oid": fields[2],
            "sha256": sha256_file(repository / path),
        })
    paths = {row["path"]: row["sha256"] for row in bindings}
    parent = git("show", "-s", "--format=%P", commit).decode("ascii").strip()
    tree = git("show", "-s", "--format=%T", commit).decode("ascii").strip()
    ack_body = {
        "document_kind": "s11_closeout_ack", "schema_version": 1,
        "checkpoint_id": "S11", "ack": "CLOSEOUT_ACK", "branch": expected_branch,
        "technical_verdict": "PASS", "closeout_verdict": "PASS",
        "proposed_parent_head": parent, "staged_tree": tree,
        "staged_blob_hashes": bindings,
        "delivery_manifest_sha256": canonical_sha256(bindings),
        "terminal_tuple": projection, "projection_parity": True,
        "formal_reproduction": {
            "decision_sha256": decision["decision_sha256"],
            "reproduction_sha256": reproduction["reproduction_sha256"],
            "fresh_whole_bundle_replay": True, "exact_parity": True,
        },
        "precommit_remote_state": _remote_delivery_snapshot(repository),
        "push_performed": False,
    }
    ack = {**ack_body, "ack_sha256": canonical_sha256(ack_body)}
    ack_target = repository / (
        "agent_run/260803-ductile-factorized-guidance-s11/s11-execution-v2/"
        "formal/verifier/closeout-ack.json"
    )
    ack_target.parent.mkdir(parents=True)
    ack_target.write_bytes(canonical_json_bytes(ack) + b"\n")
    output = repository / (
        "agent_run/260803-ductile-factorized-guidance-s11/s11-execution-v2/"
        "build/tests/closeout-audit.json"
    )
    contract = {
        "formal_outcome_paths": [
            str(decision_path), str(reproduction_path),
            *(str(path) for path in manifest_paths), str(report_path),
        ],
        "branch_delivery": {
            "positive": {
                "requires": [
                    str(gate_path), str(decision_path), str(reproduction_path),
                    *(str(path) for path in projection_paths),
                ],
                "forbids": [str(report_path)],
            },
            "negative_or_inconclusive": {
                "requires": [
                    str(decision_path), str(reproduction_path), str(report_path),
                    *(str(path) for path in projection_paths),
                ],
                "forbids": [str(gate_path)],
            },
        },
    }
    audit = verify_closeout(
        commit, output=output, repository_root=repository, contract=contract
    )
    assert audit["commit"] == commit
    assert audit["branch"] == expected_branch
    assert audit["paths"] == paths
    assert audit["push_performed"] is False
    assert audit["terminal_remote_tracking_reachable"] is False

    missing_result_contract = copy.deepcopy(contract)
    missing_result_contract["formal_outcome_paths"].append("missing-result.json")
    with pytest.raises(WorkflowError, match="exact branch commit path set"):
        verify_closeout(
            commit, output=output.with_name("closeout-audit-missing.json"),
            repository_root=repository, contract=missing_result_contract,
        )
    extra_result_contract = copy.deepcopy(contract)
    extra_result_contract["formal_outcome_paths"].remove(str(manifest_paths[0]))
    with pytest.raises(WorkflowError, match="exact branch commit path set"):
        verify_closeout(
            commit, output=output.with_name("closeout-audit-extra.json"),
            repository_root=repository, contract=extra_result_contract,
        )
    parent_projection = git("show", f"{parent}:{projection_paths[0]}")
    marker = _projection_marker(decision, reproduction)
    with pytest.raises(WorkflowError, match="exact status/criterion/outcome/edge"):
        _validate_projection_hunk(
            root=repository, parent=parent, commit=commit,
            path=str(projection_paths[0]),
            raw=parent_projection + marker.encode("utf-8") + b"\n",
            decision=decision, reproduction=reproduction,
        )
    valid_projection = _render_projection_document(
        parent_raw=parent_projection, path=str(projection_paths[0]),
        decision=decision, reproduction=reproduction,
    )
    with pytest.raises(WorkflowError, match="exact status/criterion/outcome/edge"):
        _validate_projection_hunk(
            root=repository, parent=parent, commit=commit,
            path=str(projection_paths[0]),
            raw=valid_projection + b"ALTERED PROCEDURE\n",
            decision=decision, reproduction=reproduction,
        )
    wrong_decision = {**decision, "criterion": "WRONG-TERMINAL-TUPLE"}
    with pytest.raises(WorkflowError, match="exact status/criterion/outcome/edge"):
        _validate_projection_hunk(
            root=repository, parent=parent, commit=commit,
            path=str(projection_paths[0]), raw=valid_projection,
            decision=wrong_decision, reproduction=reproduction,
        )
    with pytest.raises(WorkflowError, match="exact status/criterion/outcome/edge"):
        _validate_projection_hunk(
            root=repository, parent=parent, commit=commit,
            path=str(projection_paths[0]),
            raw=valid_projection.replace(
                b"> **S11 terminal projection:**", b"> **S11 projection omitted:**"
            ),
            decision=decision, reproduction=reproduction,
        )

    for key in ("technical_verdict", "closeout_verdict", "proposed_parent_head",
                "staged_tree", "terminal_tuple", "projection_parity",
                "formal_reproduction", "precommit_remote_state"):
        absent_body = copy.deepcopy(ack_body)
        absent_body.pop(key)
        absent = {**absent_body, "ack_sha256": canonical_sha256(absent_body)}
        ack_target.write_bytes(canonical_json_bytes(absent) + b"\n")
        with pytest.raises(WorkflowError, match="ACK schema"):
            verify_closeout(
                commit, output=output.with_name(f"closeout-audit-absent-{key}.json"),
                repository_root=repository, contract=contract,
            )
    for key in ("proposed_parent_head", "staged_tree"):
        wrong_binding_body = copy.deepcopy(ack_body)
        wrong_binding_body[key] = "0" * 40
        wrong_binding = {
            **wrong_binding_body,
            "ack_sha256": canonical_sha256(wrong_binding_body),
        }
        ack_target.write_bytes(canonical_json_bytes(wrong_binding) + b"\n")
        with pytest.raises(WorkflowError, match="ACK identity"):
            verify_closeout(
                commit, output=output.with_name(f"closeout-audit-wrong-{key}.json"),
                repository_root=repository, contract=contract,
            )

    bad_body = dict(ack_body)
    bad_body["push_performed"] = True
    bad_ack = {**bad_body, "ack_sha256": canonical_sha256(bad_body)}
    ack_target.write_bytes(canonical_json_bytes(bad_ack) + b"\n")
    with pytest.raises(WorkflowError, match="ACK identity"):
        verify_closeout(
            commit,
            output=output.with_name("closeout-audit-bad.json"),
            repository_root=repository,
            contract=contract,
        )

    ack_target.write_bytes(canonical_json_bytes(ack) + b"\n")
    git("update-ref", "refs/remotes/origin/changed-after-ack", parent)
    with pytest.raises(WorkflowError, match="state changed after closeout ACK"):
        verify_closeout(
            commit, output=output.with_name("closeout-audit-remote-changed.json"),
            repository_root=repository, contract=contract,
        )
    git("update-ref", "-d", "refs/remotes/origin/changed-after-ack")

    git("update-ref", "refs/remotes/origin/published", commit)
    reachable_ack_body = {
        **ack_body,
        "precommit_remote_state": _remote_delivery_snapshot(repository),
    }
    reachable_ack = {
        **reachable_ack_body,
        "ack_sha256": canonical_sha256(reachable_ack_body),
    }
    ack_target.write_bytes(canonical_json_bytes(reachable_ack) + b"\n")
    with pytest.raises(WorkflowError, match="reachable from a remote-tracking ref"):
        verify_closeout(
            commit, output=output.with_name("closeout-audit-remote-reachable.json"),
            repository_root=repository, contract=contract,
        )
    git("update-ref", "-d", "refs/remotes/origin/published")

    wrong_projection_body = copy.deepcopy(ack_body)
    wrong_projection_body["terminal_tuple"] = {
        **projection, "scientific_outcome": "tampered"
    }
    wrong_projection = {
        **wrong_projection_body,
        "ack_sha256": canonical_sha256(wrong_projection_body),
    }
    ack_target.write_bytes(canonical_json_bytes(wrong_projection) + b"\n")
    with pytest.raises(WorkflowError, match="ACK identity"):
        verify_closeout(
            commit, output=output.with_name("closeout-audit-projection.json"),
            repository_root=repository, contract=contract,
        )

    wrong_hash_body = copy.deepcopy(ack_body)
    wrong_hash_body["staged_blob_hashes"][0]["sha256"] = "0" * 64
    wrong_hash_body["delivery_manifest_sha256"] = canonical_sha256(
        wrong_hash_body["staged_blob_hashes"]
    )
    wrong_hash = {**wrong_hash_body, "ack_sha256": canonical_sha256(wrong_hash_body)}
    ack_target.write_bytes(canonical_json_bytes(wrong_hash) + b"\n")
    with pytest.raises(WorkflowError, match="blob OID/SHA"):
        verify_closeout(
            commit, output=output.with_name("closeout-audit-hash.json"),
            repository_root=repository, contract=contract,
        )

    (repository / "nonclosure.txt").write_text("nonclosure\n", encoding="ascii")
    git("add", "nonclosure.txt")
    git("commit", "-q", "-m", "not a closure commit")
    nonclosure = git("rev-parse", "HEAD").decode("ascii").strip()
    with pytest.raises(WorkflowError, match="closure-unit trailer"):
        verify_closeout(
            nonclosure, output=output.with_name("closeout-audit-nonclosure.json"),
            repository_root=repository, contract=contract,
        )


def test_qualification_role_workspace_descendant_and_escape(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    root = repository / "formal/producer/build"
    root.mkdir(parents=True)
    allowed = _require_workspace_descendant(root / "identity", root, repository)
    assert allowed == root / "identity"
    with pytest.raises(WorkflowError, match="escapes"):
        _require_workspace_descendant(repository / "formal/verifier/build/identity", root, repository)


def make_native_script(path: Path, *, mode: str = "valid") -> None:
    latency = "float('nan')" if mode == "nan" else "float(index + 1)"
    omit = "sizes = sizes[:-1]" if mode == "partial" else ""
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "header=sys.stdin.readline().split(); count=int(header[3]); sizes=[list(map(int,sys.stdin.readline().split())) for _ in range(count)]\n"
        "sys.stdin.readline()\n"
        f"{omit}\n"
        "rows=[]\n"
        f"for index,size in enumerate(sizes): rows.append({{'problem_size':size,'predicted_latency':{latency}}})\n"
        "print(json.dumps({'protocol':'s11_native_formocast_v1','request_sha256':header[1],'semantic_identity':header[2],'latencies':rows,'native_path_called':True},sort_keys=True,separators=(',',':'),allow_nan=True))\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def native_mapping() -> dict:
    mapping = {field: 1 for field in SCALAR_MAPPING_FIELDS}
    for field in (
        "globalSplitUCoalesced", "globalSplitUWorkGroupMappingRoundRobin", "DirectToVgprA",
        "DirectToVgprB", "DirectToLdsA", "DirectToLdsB",
    ):
        mapping[field] = False
    mapping.update({"macroTile": [16, 16, 1], "matrixInstruction": [16, 16, 16, 1], "waveGroup": [1, 1]})
    return mapping


def pinned_valid_qualification_fixture() -> dict:
    return {
        "1LDSBuffer": 1, "AdaptiveGemm": 0, "ClusterLocalRead": 1, "DepthU": 32,
        "DirectToLds": 0, "DirectToVgprA": False, "DtlPlusLdsBuf": 1,
        "ExtraMiLatencyLeft": 0, "GlobalReadVectorWidthA": 4,
        "GlobalReadVectorWidthB": 4, "GlobalSplitU": 2,
        "GlobalSplitUAlgorithm": "MultipleBuffer", "LDSTrInst": False,
        "MIArchVgpr": False, "MatrixInstruction": [16, 16, 16, 1, 1, 28, 2, 1, 4],
        "NonTemporalA": 0, "NonTemporalB": 0, "NonTemporalC": 4, "NonTemporalD": 4,
        "NumElementsPerBatchStore": 4, "PrefetchGlobalRead": 1, "PrefetchLocalRead": 1,
        "ScheduleGROverBarrier": 0, "SourceSwap": False, "StaggerU": 0,
        "StaggerUStride": 128, "StorePriorityOpt": False, "StoreSyncOpt": 1,
        "TailloopInNll": False, "TransposeLDS": 2,
        "UnrollLoopSwapGlobalReadOrder": 0, "UseSgprForGRO": 0,
        "WaveSeparateGlobalReadA": 0, "WaveSeparateGlobalReadB": 0,
        "WorkGroupMapping": 8, "WorkGroupMappingXCC": 1,
    }


def test_pinned_integration_real_native_smoke_and_closed_toolchain(tmp_path: Path) -> None:
    contract = load_contract()
    pinned = materialize_pinned_integration(tmp_path / "pinned", contract)
    source_root = Path(pinned["source_root"])
    pinned_defaults = source_root / "projects/hipblaslt/tensilelite/Tensile/ductile/config/defaults.yaml"
    current_defaults = ROOT / "projects/hipblaslt/tensilelite/Tensile/ductile/config/defaults.yaml"
    assert sha256_file(pinned_defaults) == contract["source_pins"]["ductile_files"][0]["sha256"]
    assert sha256_file(pinned_defaults) != sha256_file(current_defaults)
    compiler = Path("/opt/rocm/bin/amdclang++")
    compiler_bound = compiler.resolve()
    compiler_version = subprocess.run(
        [str(compiler), "--version"], stdout=subprocess.PIPE, check=True
    ).stdout.decode("utf-8").splitlines()[0]
    native_source = (PROTOCOL / "s11/native_formocast_runtime_adapter.cpp").resolve()
    built = build_native_formocast_helper(
        contract=contract,
        pinned_materialization_root=tmp_path / "pinned",
        build_root=tmp_path / "native-build",
        compiler_path=compiler,
        compiler_sha256=sha256_file(compiler_bound),
        compiler_version=compiler_version,
        adapter_source_path=native_source,
        adapter_source_sha256=sha256_file(native_source),
    )
    adapter = NativeFormocastAdapter(
        built["helper_path"], executable_sha256=built["helper_sha256"],
        native_source_path=native_source, native_source_sha256=sha256_file(native_source),
        ductile_commit=contract["source_pins"]["ductile_commit"], timeout_seconds=20,
        compiler_path=compiler, compiler_sha256=sha256_file(compiler_bound),
        compiler_version=compiler_version, build_provenance=built["build"],
    )
    scored = adapter.score(
        semantic_identity="f" * 64,
        operational_solution=native_mapping(),
        problem_sizes=contract["native_scoring"]["problem_sizes"],
        soo=False,
        weight_beta=0.25,
    )
    assert len(scored["latencies"]) == 3
    assert all(row["predicted_latency"] > 0 for row in scored["latencies"])
    smoke_boundary = {
        "fixture": "deterministic_synthetic_nonformal_SizeMapping",
        "formal_sample_or_decision_read": False,
        "scientific_credit": 0,
        "admitted_to_populations_statistics_guidance_or_outcome": False,
    }
    assert smoke_boundary == {
        "fixture": "deterministic_synthetic_nonformal_SizeMapping",
        "formal_sample_or_decision_read": False,
        "scientific_credit": 0,
        "admitted_to_populations_statistics_guidance_or_outcome": False,
    }

    worker_relative = contract["toolchain_bindings"]["qualification_worker_source_path"]
    python_launcher = Path("/opt/venv/bin/python3")
    validator_runtime = tmp_path / "validator-runtime"
    validator_cwd = validator_runtime / "cwd"
    validator_tmpdir = validator_runtime / "tmp"
    validator_pycache = validator_runtime / "pycache"
    validator_cwd.mkdir(parents=True)
    validator_tmpdir.mkdir()
    validator_pycache.mkdir()
    tools = {
        "validator_adapter_path": str(python_launcher),
        "validator_adapter_sha256": sha256_file(python_launcher.resolve()),
        "validator_source_path": worker_relative,
        "validator_source_sha256": sha256_file(ROOT / worker_relative),
        "validator_protocol": PERSISTENT_VALIDATOR_PROTOCOL,
        "validator_worker_count": 1,
        "validator_argv": derive_persistent_validator_argv(
            executable=python_launcher, worker_source_path=ROOT / worker_relative,
            pinned_source_root=source_root, actual_yaml_path=ACTUAL_YAML,
            compiler_path=compiler,
        ),
        "validator_working_directory": str(validator_cwd.resolve()),
        "validator_tmpdir": str(validator_tmpdir.resolve()),
        "validator_pythonpycacheprefix": str(validator_pycache.resolve()),
        "validator_timeout_seconds": 120,
        "compiler_path": str(compiler),
        "compiler_sha256": sha256_file(compiler_bound),
        "compiler_version": compiler_version,
        "qualification_python_path": str(python_launcher),
        "qualification_python_sha256": sha256_file(python_launcher.resolve()),
        "qualification_worker_source_path": worker_relative,
        "qualification_worker_source_sha256": sha256_file(ROOT / worker_relative),
        "native_helper_path": built["helper_path"],
        "native_helper_sha256": built["helper_sha256"],
        "native_helper_source_path": contract["toolchain_bindings"]["native_helper_source_path"],
        "native_helper_source_sha256": sha256_file(native_source),
        "native_build_argv": built["build"],
        "qualification_argv": [],
        "resolver_source_sha256": sha256_file(
            source_root / "projects/hipblaslt/tensilelite/Tensile/backends/ductile_backend.py"
        ),
        "kernelwriter_source_sha256": sha256_file(
            source_root / "projects/hipblaslt/tensilelite/Tensile/KernelWriterAssembly.py"
        ),
        "semantic_identity_schema": "s11_consumer_semantic_identity_v1",
        "qualification_fingerprint_sha256": "0" * 64,
        "qualification_timeout_seconds": 120,
        "native_timeout_seconds": 20,
    }
    rocm_root = next(
        parent for parent in compiler_bound.parents
        if (parent / "include/hip/hip_runtime.h").is_file()
    )
    tools["qualification_argv"] = derive_sealed_execution_argv(
        compiler_path=tools["compiler_path"], pinned_source_root=source_root,
        rocm_root=rocm_root,
        linked_sources=[row["path"] for row in built["build"]["linked_sources"]],
        linked_objects=[row["path"] for row in built["build"]["linked_objects"]],
        generated_header=built["build"]["generated_headers"][0]["path"],
        helper_path=built["helper_path"],
        qualification_python_path=tools["qualification_python_path"],
        qualification_worker_source_path=(ROOT / worker_relative).resolve(),
        qualification_yaml_path=ACTUAL_YAML.resolve(),
    )["qualification_argv"]
    assert set(tools) == set(TOOLCHAIN_KEYS)
    tools["qualification_fingerprint_sha256"] = expected_qualification_fingerprint(tools)
    _validate_toolchain(tools, contract)

    # The launcher must remain the venv symlink in argv; resolving it would
    # select system Python and lose the pinned worker dependencies.
    assert tools["validator_argv"][0] == str(python_launcher)
    def actual_validator(worker_count: int) -> PinnedValidatorAdapter:
        return PinnedValidatorAdapter(
            python_launcher,
            executable_sha256=sha256_file(python_launcher.resolve()),
            validator_source_path=ROOT / worker_relative,
            validator_source_sha256=sha256_file(ROOT / worker_relative),
            timeout_seconds=120, protocol=PERSISTENT_VALIDATOR_PROTOCOL,
            worker_count=worker_count, argv=tools["validator_argv"],
            cwd=tools["validator_working_directory"],
            tmpdir=tools["validator_tmpdir"],
            pythonpycacheprefix=tools["validator_pythonpycacheprefix"],
        )

    base_raw = pinned_valid_qualification_fixture()
    raw_mapping = copy.deepcopy(base_raw); raw_mapping["WorkGroupMapping"] = 1
    raw_stagger = copy.deepcopy(base_raw); raw_stagger["StaggerU"] = 32
    raw_corpus = [base_raw, raw_mapping, raw_stagger]
    contexts = [
        {"stream_id": "launcher-smoke", "chunk_index": 0, "slot_index": index}
        for index in range(len(raw_corpus))
    ]
    one_shot_codes = []
    for raw, context in zip(raw_corpus, contexts):
        with actual_validator(1) as fresh:
            one_shot_codes.append(fresh.validate_many([raw], [context])[0]["code"])
            assert fresh.spawn_count == 1
    with actual_validator(1) as reused:
        reused_codes = [row["code"] for row in reused.validate_many(raw_corpus, contexts)]
        assert reused.spawn_count == 1
        reverse_codes = [
            row["code"]
            for row in reused.validate_many(
                list(reversed(raw_corpus)), list(reversed(contexts))
            )
        ]
        assert reused.spawn_count == 1
    with actual_validator(3) as parallel:
        parallel_codes = [
            row["code"] for row in parallel.validate_many(raw_corpus, contexts)
        ]
        assert parallel.spawn_count == 3
    assert one_shot_codes == reused_codes == parallel_codes
    assert reverse_codes == list(reversed(reused_codes))
    assert all(code in (0, 1) for code in reused_codes)

    raw = pinned_valid_qualification_fixture()
    occurrence_id = canonical_sha256({"fixture": "fresh_pinned_normal_qualification", "raw": raw})
    alias_fanout = {canonical_sha256(raw): [occurrence_id]}
    worker = PinnedQualificationWorker(
        python_path=python_launcher,
        python_sha256=sha256_file(python_launcher.resolve()),
        worker_source_path=ROOT / worker_relative,
        worker_source_sha256=sha256_file(ROOT / worker_relative),
        compiler_path=compiler,
        compiler_sha256=sha256_file(compiler_bound),
        resolver_source_sha256=tools["resolver_source_sha256"],
        kernelwriter_source_sha256=tools["kernelwriter_source_sha256"],
        semantic_identity_schema=tools["semantic_identity_schema"],
        qualification_fingerprint_sha256=tools["qualification_fingerprint_sha256"],
        qualification_argv=tools["qualification_argv"],
        timeout_seconds=120,
        repository_root=source_root,
        actual_yaml_path=ACTUAL_YAML,
    )
    producer, producer_transcript = worker.run(
        role="producer", workspace_root=tmp_path / "qualification-producer",
        workspace_root_id="synthetic-producer", raw_configuration=raw,
        occurrence_ids=[occurrence_id], alias_fanout=alias_fanout,
    )
    verifier, verifier_transcript = worker.run(
        role="fresh_verifier", workspace_root=tmp_path / "qualification-verifier",
        workspace_root_id="synthetic-verifier", raw_configuration=raw,
        occurrence_ids=[occurrence_id], alias_fanout=alias_fanout,
    )
    projection = evaluate_attempts([producer, verifier], blocked_mapping_allowlist=[])
    assert projection["state"] == "executable"
    assert projection["association_parity"] and projection["occurrence_alias_parity"]
    assert producer_transcript["provenance"] == verifier_transcript["provenance"]
    faults = []
    missing = copy.deepcopy(tools); missing.pop("native_timeout_seconds"); faults.append(missing)
    extra = copy.deepcopy(tools); extra["unknown"] = True; faults.append(extra)
    pending = copy.deepcopy(tools); pending["native_build_argv"]["link_argv"].append("required_pending"); faults.append(pending)
    wrong_version = copy.deepcopy(tools); wrong_version["compiler_version"] = "wrong"; faults.append(wrong_version)
    wrong_argv = copy.deepcopy(tools); wrong_argv["native_build_argv"]["compile_argv"][0][-1] = "wrong.o"; faults.append(wrong_argv)
    extra_qualification = copy.deepcopy(tools); extra_qualification["qualification_argv"].append("--unexecuted"); faults.append(extra_qualification)
    wrong_timeout = copy.deepcopy(tools); wrong_timeout["native_timeout_seconds"] = 0; faults.append(wrong_timeout)
    wrong_hash = copy.deepcopy(tools); wrong_hash["resolver_source_sha256"] = "0" * 64; faults.append(wrong_hash)
    for fault in faults:
        with pytest.raises(ContractError):
            _validate_toolchain(fault, contract)

    # Re-seal the two hashes after each mutation so rejection proves exact argv
    # sequence enforcement rather than merely detecting a stale self-hash.
    def reseal(fault: dict) -> dict:
        build_body = dict(fault["native_build_argv"])
        build_body.pop("build_sha256")
        fault["native_build_argv"]["build_sha256"] = canonical_sha256(build_body)
        fault["qualification_fingerprint_sha256"] = expected_qualification_fingerprint(fault)
        return fault

    exact_argv_faults = []
    fault = copy.deepcopy(tools)
    fault["native_build_argv"]["compile_argv"][0].insert(1, "-DUNEXECUTED=1")
    exact_argv_faults.append(reseal(fault))
    fault = copy.deepcopy(tools)
    fault["native_build_argv"]["compile_argv"][0][1:3] = reversed(
        fault["native_build_argv"]["compile_argv"][0][1:3]
    )
    exact_argv_faults.append(reseal(fault))
    fault = copy.deepcopy(tools)
    fault["native_build_argv"]["link_argv"].insert(1, "-Wl,--build-id=none")
    exact_argv_faults.append(reseal(fault))
    fault = copy.deepcopy(tools)
    fault["native_build_argv"]["link_argv"].pop(1)
    exact_argv_faults.append(reseal(fault))
    fault = copy.deepcopy(tools)
    fault["qualification_argv"].append("--unexecuted")
    fault["qualification_fingerprint_sha256"] = expected_qualification_fingerprint(fault)
    exact_argv_faults.append(fault)
    import s11.contract as contract_module

    original_verify = contract_module.verify_pinned_integration
    contract_module.verify_pinned_integration = lambda destination, selected: {
        "source_root": str(source_root),
        "manifest_file_sha256": built["build"]["pinned_source_manifest_sha256"],
    }
    try:
        for fault in exact_argv_faults:
            with pytest.raises(ContractError, match="argv"):
                _validate_toolchain(fault, contract)
    finally:
        contract_module.verify_pinned_integration = original_verify


def synthetic_native_build_binding(tmp_path: Path, executable: Path, source: Path) -> dict:
    compiler = Path(sys.executable).resolve()
    version = subprocess.run(
        [str(compiler), "--version"], stdout=subprocess.PIPE, check=True
    ).stdout.decode("utf-8").splitlines()[0]
    generated = tmp_path / "generated.hpp"
    object_path = tmp_path / "linked.o"
    pinned_manifest = tmp_path / "pinned-manifest.json"
    generated.write_text("synthetic only\n", encoding="utf-8")
    object_path.write_bytes(b"synthetic-object")
    pinned_manifest.write_text("synthetic manifest\n", encoding="utf-8")
    build_body = {
        "document_kind": "s11_native_build_execution", "schema_version": 1,
        "checkpoint_id": "S11",
        "compile_argv": [[str(compiler), "-c", str(source), "-o", str(object_path)]],
        "link_argv": [str(compiler), str(object_path), "-o", str(executable)],
        "pinned_source_root": str(tmp_path),
        "pinned_source_manifest_sha256": sha256_file(pinned_manifest),
        "generated_headers": [{"path": str(generated), "sha256": sha256_file(generated)}],
        "linked_objects": [{"path": str(object_path), "sha256": sha256_file(object_path)}],
        "linked_sources": [{"path": str(source), "sha256": sha256_file(source)}],
    }
    build = {**build_body, "build_sha256": canonical_sha256(build_body)}
    return {
        "compiler_path": compiler,
        "compiler_sha256": sha256_file(compiler),
        "compiler_version": version,
        "build_provenance": build,
    }


def test_native_adapter_all_size_finite_and_source_executable_binding(tmp_path: Path) -> None:
    executable = tmp_path / "helper"
    source = tmp_path / "helper.cpp"
    make_native_script(executable)
    source.write_text("ProblemInfo SizeMapping predictedPerformance\n", encoding="utf-8")
    adapter = NativeFormocastAdapter(
        executable, executable_sha256=sha256_file(executable), native_source_path=source,
        native_source_sha256=sha256_file(source), ductile_commit="5" * 40, timeout_seconds=5,
        **synthetic_native_build_binding(tmp_path, executable, source),
    )
    sizes = [[8, 8, 1, 128], [256, 256, 1, 1024], [2304, 1024, 1, 214336]]
    result = adapter.score(
        semantic_identity="f" * 64, operational_solution=native_mapping(),
        problem_sizes=sizes, soo=False, weight_beta=0.25,
    )
    assert result["problem_sizes"] == sizes
    assert result["provenance"]["proxy_or_substitution"] is False
    with pytest.raises(NativeAdapterError, match="source hash"):
        NativeFormocastAdapter(
            executable, executable_sha256=sha256_file(executable), native_source_path=source,
            native_source_sha256="0" * 64, ductile_commit="5" * 40, timeout_seconds=5,
            **synthetic_native_build_binding(tmp_path, executable, source),
        )


@pytest.mark.parametrize("mode,match", [("partial", "partial"), ("nan", "strict JSON")])
def test_native_adapter_partial_and_nonfinite_fail_closed(tmp_path: Path, mode: str, match: str) -> None:
    executable = tmp_path / "helper"
    source = tmp_path / "helper.cpp"
    make_native_script(executable, mode=mode)
    source.write_text("native source\n", encoding="utf-8")
    adapter = NativeFormocastAdapter(
        executable, executable_sha256=sha256_file(executable), native_source_path=source,
        native_source_sha256=sha256_file(source), ductile_commit="5" * 40, timeout_seconds=5,
        **synthetic_native_build_binding(tmp_path, executable, source),
    )
    with pytest.raises(NativeAdapterError, match=match):
        adapter.score(
            semantic_identity="f" * 64, operational_solution=native_mapping(),
            problem_sizes=[[8, 8, 1, 128], [256, 256, 1, 1024], [2304, 1024, 1, 214336]],
            soo=False, weight_beta=0.25,
        )


def test_workload_envelope_family_matches_real_extractor() -> None:
    envelope = build_workload_envelope(repository_root=ROOT)
    registry = extract_registry(ACTUAL_YAML)
    assert envelope["family"]["activated_value_count"] == len(
        registry["conditional_streams"]
    ) == 101
    assert envelope["family"]["eligible_gene_count"] == len(
        registry["eligible_genes"]
    ) == 27
    assert envelope["family"]["registry_sha256"] == registry["registry_sha256"]


def test_workload_envelope_totals_equal_schedule_arithmetic() -> None:
    envelope = build_workload_envelope(repository_root=ROOT)
    contract = load_contract()
    schedule = contract["schedule"]
    global_schedule = schedule["global"]
    conditional_schedule = schedule["conditional"]
    registry = extract_registry(ACTUAL_YAML)
    activated_values = len(registry["conditional_streams"])
    attempts = contract["qualification"]["complete_attempts_total"]
    locked_sizes = len(contract["native_scoring"]["problem_sizes"])
    totals = envelope["totals"]

    assert totals["global_nominal_draws"] == global_schedule["complete_nominal_draws"]
    assert totals["conditional_nominal_draws"] == (
        activated_values
        * conditional_schedule["complete_nominal_draws_per_activated_value"]
    )
    assert totals["producer_chunk_count"] == (
        global_schedule["complete_chunks"]
        + activated_values
        * conditional_schedule["complete_chunks_per_activated_value"]
    ) == 117248
    assert totals["total_nominal_draws"] == 60030976
    assert totals["credited_accepted_occurrence_upper_bound"] == (
        global_schedule["canonical_prefix_accepted"]
        + activated_values * conditional_schedule["canonical_prefix_accepted"]
    )
    qualification_attempts_upper_bound = (
        attempts * totals["credited_accepted_occurrence_upper_bound"]
    )
    assert totals["attempts_per_semantic_identity"] == attempts == 2
    assert totals["qualification_attempts_upper_bound"] == (
        qualification_attempts_upper_bound
    )
    assert totals["unique_identity_qualification_attempt_upper_bound"] == (
        qualification_attempts_upper_bound
    )
    per_size_bounds = totals["formocast_score_call_upper_bound_by_locked_size"]
    assert envelope["schedule_source"]["locked_problem_sizes"] == registry[
        "problem_sizes"
    ]
    assert per_size_bounds == {
        canonical_json_bytes(problem_size).decode("utf-8"): totals[
            "credited_accepted_occurrence_upper_bound"
        ]
        for problem_size in registry["problem_sizes"]
    }
    assert len(per_size_bounds) == locked_sizes == 3
    assert set(per_size_bounds.values()) == {34048}
    assert totals["formocast_score_call_upper_bound_total"] == sum(
        per_size_bounds.values()
    )
    assert totals["formocast_score_call_upper_bound_total"] == (
        totals["formocast_score_call_upper_bound_per_locked_size"] * locked_sizes
    )
    assert totals["global_nominal_draws"] == 33554432
    assert totals["conditional_nominal_draws"] == 101 * 262144
    assert totals["credited_accepted_occurrence_upper_bound"] == 8192 + 101 * 256
    assert totals["qualification_attempts_upper_bound"] == 68096
    assert totals["unique_identity_qualification_attempt_upper_bound"] == 68096
    assert totals["formocast_score_call_upper_bound_total"] == (
        totals["formocast_score_call_upper_bound_per_locked_size"] * 3
    )


def test_workload_envelope_estimates_are_record_and_notify_only() -> None:
    envelope = build_workload_envelope(repository_root=ROOT)
    assert envelope["authority"] == "record_and_notify_only"
    assert envelope["status"] == "planning_only"
    for estimate in envelope["planning_estimates"].values():
        assert estimate["authority"] == "record_and_notify_only"
        assert estimate["layer"] == "C"
        assert estimate["may_stop_or_downgrade"] is False
        assert estimate["basis"] == "synthetic_planning_calibration"
    forecast = envelope["planning_estimates"]["runtime"]["resource_forecast"]
    assert forecast["authority"] == "notify_only"
    assert forecast["may_stop_or_downgrade"] is False
    storage = envelope["planning_estimates"]["storage"]
    assert storage["worst_case_bytes"] == (
        storage["synthetic_bytes_per_chunk"] * storage["producer_chunk_count"]
    )


def test_workload_envelope_branch_reachability_lists_all_terminals() -> None:
    envelope = build_workload_envelope(repository_root=ROOT)
    contract = load_contract()
    branches = {
        branch["terminal_code"]: branch
        for branch in envelope["terminal_branch_reachability"]
    }
    assert set(branches) == set(contract["outcomes"]["ordering"])
    assert list(branches) == contract["outcomes"]["ordering"]
    assert branches["FT-BLOCKED-MAPPING"]["reachable"] is False
    assert all(
        branch["reachable"] is True
        for code, branch in branches.items()
        if code != "FT-BLOCKED-MAPPING"
    )
    global_minimum = contract["outcomes"]["positive"]["requirements"][
        "global_Uexec_min"
    ]
    assert branches["FT-INCONCLUSIVE"]["sub_reasons"] == [
        f"global_uexec_count<{global_minimum}",
        "material_stochastic_shortage",
        "not bounded_family_complete",
    ]


def test_workload_envelope_manifest_is_committed_and_reproducible() -> None:
    envelope = build_workload_envelope(repository_root=ROOT)
    regenerated = canonical_json_bytes(envelope) + b"\n"
    manifest_path = PROTOCOL / "manifests/s11-workload-envelope.json"
    committed = manifest_path.read_bytes()
    assert regenerated == committed
    committed_manifest = json.loads(committed)
    envelope_sha256 = committed_manifest.pop("envelope_sha256")
    assert envelope_sha256 == canonical_sha256(committed_manifest)
    assert envelope_sha256 == envelope["envelope_sha256"]


def test_workload_envelope_no_lock_materialized() -> None:
    assert not DEFAULT_LOCK_PATH.exists()
