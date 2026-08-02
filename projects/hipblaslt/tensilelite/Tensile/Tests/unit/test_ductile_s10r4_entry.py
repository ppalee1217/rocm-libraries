# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Outcome-blind, offline checks for the sealed S10R4 entry implementation."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import math
import os
import shutil
import stat
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest
import jsonschema


REPO_ROOT = Path(__file__).resolve().parents[6]
PROTOCOL_ROOT = REPO_ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1"
sys.path.insert(0, str(PROTOCOL_ROOT))

import s10r4.contract as contract_module

from s10r4.census import (
    census_request,
    classify_native_membership,
    execute_census_worker,
    git_blob_oid,
    reconcile_native_artifacts,
    stable_classify,
)
from s10r4.conformance import (
    FIXTURE_PAYLOAD_SHA256,
    build_native_fixture,
    exact_binary64,
    exact_tree,
    expected_transcript,
    fixture_ascii_bytes,
    ordered_field_digest,
    validate_fault_substitutions,
    validate_native_fixture,
    validate_native_transcript,
)
from s10r4.contract import (
    COMMAND_PLACEHOLDERS,
    COMMAND_TEMPLATES,
    CONTRACT_RAW_SHA256,
    FIXED_ENVIRONMENT,
    S10R4Error,
    atomic_write_json,
    canonical_json,
    canonical_self_hash,
    canonical_sha256,
    load_contract,
    load_base_contract,
    load_contract_supplement,
    load_json,
    materialize_command_template,
    llvm_executable_closure,
    ordinary_file_records,
    raw_sha256,
    safe_relative_path,
    seal_digest,
    strict_json_bytes,
    strict_yaml_bytes,
    validate_audit_ledger,
    validate_command_template,
    validate_document_schema,
    validate_effective_lock,
    validate_environment,
)
from s10r4.correctness import (
    CorrectnessAttempt,
    aggregate_noise,
    anchor_indices,
    correctness_build_request,
    decide_client_result,
    decide_correctness_attempts,
    execute_correctness_build_worker,
    nearest_rank,
    parse_allocation_snapshot,
    parse_process_snapshot,
    parse_single_result_csv,
    rewrite_results_file,
    select_gpu,
    validate_client_parameters,
    verify_gpu_continuity,
)
from s10r4.ledger import (
    completion_digest,
    finalize_child,
    finalize_process_completion,
    scan_exact_children,
)
from s10r4.mapping import (
    MappingAttempt,
    REQUIRED_MAPPING_FIELDS,
    _actual_mapping_backend,
    build_size_registry,
    compare_mapping_passes,
    decide_mapping_attempts,
    execute_mapping_worker,
    mapping_request,
    validate_mapping_batch,
    validate_size_registry,
)
from s10r4.selector import Witness, deterministic_select
from s10r4.state_machine import (
    Lifecycle,
    StageProjection,
    decide_outcome,
    project_formal_stage,
    validate_document_policy,
)


def raises(callable_, *args, **kwargs):
    with pytest.raises(S10R4Error):
        callable_(*args, **kwargs)


def test_contract_identity_and_fixture_hash():
    contract = load_contract()
    supplement = load_contract_supplement()
    base = load_base_contract()
    assert base["contract_id"] == "S10R4-A47-EXACT-FRAME-OPERATIONAL-ENTRY-V1"
    assert contract["contract_id"] == "S10R4-A48-EXACT-FRAME-BINDING-02"
    assert supplement["binding_id"] == "binding-02"
    assert contract["identity"]["execution_tranche"] == "T-S10R4-B02"
    assert contract["identity"]["authority_amendment"] == "A48"
    assert contract["identity"]["effective_lock_path"].endswith(
        "s10r4-stage1-exact-frame-entry-binding-02-lock.json"
    )
    operational = contract["binding_02_operational_inputs"]
    assert set(operational) == {"supplement_and_recovery", "prebinding_recovery"}
    assert operational["prebinding_recovery"]["amendment_record"]["commit_oid"] == (
        contract_module.AMENDMENT_COMMIT_OID
    )
    assert operational["prebinding_recovery"]["retired_prebinding_attempt"][
        "seal_authority"
    ] is False
    encoded = canonical_json(contract).decode("utf-8")
    assert contract_module.FORBIDDEN_BINDING_01_RUN_PREFIX not in encoded
    assert len(CONTRACT_RAW_SHA256) == 64
    fixture = build_native_fixture(contract)
    assert fixture["fixture_digest"] == FIXTURE_PAYLOAD_SHA256
    validate_native_fixture(fixture, contract)


def test_prebinding_recovery_exact_bindings_and_retired_ledger_rejected():
    amendment = contract_module.load_prebinding_recovery_amendment()
    recovery = contract_module._prebinding_recovery_lock_inputs(amendment)
    assert recovery["amendment_record"] == {
        "path": "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4-stage1-exact-frame-entry-binding-02-prebinding-recovery-contract.yaml",
        "git_mode": "100644",
        "blob_oid": "c229f627fab19551f8302f4637812020ea3e4ebd",
        "size_bytes": 10403,
        "raw_sha256": contract_module.AMENDMENT_RAW_SHA256,
        "canonical_sha256": contract_module.AMENDMENT_CANONICAL_SHA256,
        "commit_oid": contract_module.AMENDMENT_COMMIT_OID,
    }
    assert [record["raw_sha256"] for record in recovery["precommit_verdict_records"]] == [
        "fc222c2cbc53cab14d0d02cf291a41d5f367bf9f61607c0452b41e254d030d1d",
        "db1dc835eaebc878fcd5f3d8e5c5cfbbb8e30885808b1e9e10d26cf4f86b8df4",
    ]
    assert recovery["postcommit_audit_record"]["raw_sha256"] == (
        "ed92bc2f8690ba75cf5cebabac5a41a176b5bb702bbc09a19d11b22e9a146e74"
    )
    retired = recovery["retired_prebinding_attempt"]
    assert retired["state"] == "retired_prebinding_diagnostic"
    assert retired["seal_authority"] is False
    assert len(retired["event_digests"]) == 4
    assert recovery["successor_prebinding_ledger"]["path"].endswith(
        "/audit-verdict-r2.json"
    )
    raises(
        contract_module.load_prebinding_audit_ledger,
        contract_module.RETIRED_PREBINDING_LEDGER_PATH,
    )


def test_plan_a_revision_16_append_only_chain_is_exact():
    selected = contract_module._selected_revision_record()
    assert selected["revision"] == 16
    assert selected["plan_a_raw_sha256"] == contract_module.PLAN_A_RAW_SHA256
    assert selected["plan_a_size_bytes"] == 51130
    assert selected["previous_revision"] == 15
    assert selected["previous_raw_sha256"] == contract_module.PLAN_A_PREDECESSOR["raw_sha256"]


def test_actual_report_resources_project_exact_eight_keys_to_closed_six():
    report = load_json(contract_module.IMPLEMENTER_REPORT_PATHS[1])
    resources = report["resources"]
    projection = contract_module.project_report_resources(resources)
    assert set(resources) == contract_module.REPORT_RESOURCE_KEYS
    assert set(resources["peak_and_transient"]) == contract_module.PEAK_TRANSIENT_RESOURCE_KEYS
    assert resources["historical_carried"] == (
        load_contract_supplement()["resources"]["carry_from_binding_01"]
    )
    assert set(projection) == contract_module.LOCK_REPORTED_RESOURCE_KEYS
    assert "historical_carried" not in projection
    assert "peak_and_transient" not in projection
    schema = load_json(PROTOCOL_ROOT / "schemas/s10r4-entry.schema.json")
    jsonschema.Draft7Validator(schema["definitions"]["lockReportedResources"]).validate(
        projection
    )
    widened = copy.deepcopy(projection)
    widened["peak_and_transient"] = resources["peak_and_transient"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(
            schema["definitions"]["lockReportedResources"]
        ).validate(widened)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.pop("peak_and_transient"),
        lambda value: value.__setitem__("unknown_resource", 0),
        lambda value: value["historical_carried"].__setitem__(
            "storage_bytes_before_final_reports", 0
        ),
        lambda value: value["peak_and_transient"].pop("repair_archive_bytes"),
        lambda value: value["peak_and_transient"].__setitem__(
            "repair_archive_present", 0
        ),
        lambda value: value["peak_and_transient"].__setitem__(
            "current_prelabel_build_bytes", -1
        ),
        lambda value: value["storage_bytes_before_reports"].__setitem__("total", 0),
        lambda value: value.__setitem__("whole_role_cpu_seconds", "unknown"),
        lambda value: value.__setitem__("observed_activity_lower_bound_seconds", math.inf),
    ],
)
def test_report_resource_projection_rejects_missing_extra_malformed_or_divergent(
    mutation,
):
    resources = copy.deepcopy(
        load_json(contract_module.IMPLEMENTER_REPORT_PATHS[1])["resources"]
    )
    mutation(resources)
    raises(contract_module.project_report_resources, resources)


@pytest.mark.parametrize(
    "payload",
    [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b'[]', b'\xff'],
)
def test_strict_json_rejects_ambiguous_or_invalid(payload):
    raises(strict_json_bytes, payload)


@pytest.mark.parametrize("payload", [b"a: 1\na: 2\n", b".nan: value\n", b"- 1\n"])
def test_strict_yaml_rejects_ambiguous_or_nonobject(payload):
    raises(strict_yaml_bytes, payload)


def test_canonical_json_and_hash_are_stable():
    left = {"b": [2, 1], "a": "x"}
    right = {"a": "x", "b": [2, 1]}
    assert canonical_json(left) == b'{"a":"x","b":[2,1]}'
    assert canonical_sha256(left) == canonical_sha256(right)


def test_atomic_write_is_no_overwrite(tmp_path):
    path = tmp_path / "record.json"
    atomic_write_json(path, {"a": 1})
    atomic_write_json(path, {"a": 1})
    raises(atomic_write_json, path, {"a": 2})
    assert load_json(path) == {"a": 1}


@pytest.mark.parametrize("value", ["/absolute", "../escape", "a/../b", "."])
def test_safe_relative_path_rejects_escape(value):
    with pytest.raises(S10R4Error):
        safe_relative_path(value)


def test_inventory_records_ordinary_files(tmp_path):
    (tmp_path / "b").write_bytes(b"two")
    (tmp_path / "a").write_bytes(b"one")
    records, total = ordinary_file_records(tmp_path)
    assert [row["relative_path"] for row in records] == ["a", "b"]
    assert total == 6


def test_inventory_rejects_symlink(tmp_path):
    (tmp_path / "target").write_bytes(b"x")
    os.symlink("target", tmp_path / "link")
    raises(ordinary_file_records, tmp_path)


def test_run_git_uses_literal_root_safe_argv_and_preserves_process_controls(
    tmp_path, monkeypatch
):
    observed = {}

    def fake_run(argv, **kwargs):
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, 0, b"ok\n", b"")

    monkeypatch.setattr(contract_module.subprocess, "run", fake_run)
    completed = contract_module._run_git(
        ["status", "--porcelain=v1"], repo_root=tmp_path, check=False
    )

    assert observed["argv"] == [
        "/usr/bin/git",
        "-c",
        "safe.directory=/src/rocm-libraries",
        "status",
        "--porcelain=v1",
    ]
    assert observed["kwargs"] == {
        "cwd": tmp_path,
        "env": {"LC_ALL": "C", "PATH": "/usr/bin:/bin"},
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "timeout": 60,
        "check": False,
    }
    assert completed.returncode == 0


def test_run_git_actual_root_repo_is_safe_fail_closed_and_nonmutating(monkeypatch):
    assert os.geteuid() == 0
    assert REPO_ROOT == Path("/src/rocm-libraries")
    assert REPO_ROOT.stat().st_uid != 0

    predecessor_root = REPO_ROOT / (
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/"
        "artifacts/formal-cpu"
    )
    assert predecessor_root.is_dir()

    def path_state(path):
        try:
            info = path.lstat()
        except FileNotFoundError:
            return {"present": False}
        result = {
            "present": True,
            "file_type": stat.S_IFMT(info.st_mode),
            "mode": stat.S_IMODE(info.st_mode),
            "uid": info.st_uid,
            "gid": info.st_gid,
            "nlink": info.st_nlink,
            "size_bytes": info.st_size,
            "mtime_ns": info.st_mtime_ns,
            "ctime_ns": info.st_ctime_ns,
        }
        if stat.S_ISREG(info.st_mode):
            result["raw_sha256"] = raw_sha256(path)
        return result

    def tree_metadata(root):
        records = []
        for current, directory_names, file_names in os.walk(root):
            directory_names.sort()
            file_names.sort()
            current_path = Path(current)
            for path in [current_path, *(current_path / name for name in file_names)]:
                info = path.lstat()
                records.append(
                    {
                        "relative_path": "."
                        if path == root
                        else path.relative_to(root).as_posix(),
                        "file_type": stat.S_IFMT(info.st_mode),
                        "mode": stat.S_IMODE(info.st_mode),
                        "uid": info.st_uid,
                        "gid": info.st_gid,
                        "nlink": info.st_nlink,
                        "size_bytes": info.st_size,
                        "mtime_ns": info.st_mtime_ns,
                        "ctime_ns": info.st_ctime_ns,
                    }
                )
        return records

    git_config_paths = (
        Path("/root/.gitconfig"),
        Path("/root/.config/git/config"),
        Path("/etc/gitconfig"),
        REPO_ROOT / ".git/config",
    )

    config_before = {path.as_posix(): path_state(path) for path in git_config_paths}
    metadata_before = tree_metadata(predecessor_root)
    inventory_before, inventory_bytes_before = ordinary_file_records(predecessor_root)
    ledger_before = [
        row for row in inventory_before if row["relative_path"].startswith("ledger/")
    ]
    assert ledger_before
    assert sum(
        row["file_type"] == stat.S_IFREG
        and row["mode"] == 0o600
        and row["uid"] == 0
        and row["gid"] == 0
        for row in metadata_before
    ) == 2562

    completed = contract_module._run_git(["rev-parse", "--show-toplevel"])
    assert completed.returncode == 0
    assert completed.stdout == b"/src/rocm-libraries\n"

    real_run = subprocess.run
    required_prefix = [
        "/usr/bin/git",
        "-c",
        "safe.directory=/src/rocm-libraries",
    ]
    fault_prefixes = {
        "option": [
            "/usr/bin/git",
            "--no-pager",
            "safe.directory=/src/rocm-libraries",
        ],
        "path": [
            "/usr/bin/git",
            "-c",
            "safe.directory=/src/not-rocm-libraries",
        ],
        "removal": ["/usr/bin/git"],
    }
    for fault_prefix in fault_prefixes.values():
        with monkeypatch.context() as fault_patch:
            def faulted_run(argv, **kwargs):
                assert argv[:3] == required_prefix
                return real_run([*fault_prefix, *argv[3:]], **kwargs)

            fault_patch.setattr(contract_module.subprocess, "run", faulted_run)
            raises(contract_module._run_git, ["rev-parse", "--show-toplevel"])

    config_after = {path.as_posix(): path_state(path) for path in git_config_paths}
    metadata_after = tree_metadata(predecessor_root)
    inventory_after, inventory_bytes_after = ordinary_file_records(predecessor_root)
    ledger_after = [
        row for row in inventory_after if row["relative_path"].startswith("ledger/")
    ]
    assert config_after == config_before
    assert metadata_after == metadata_before
    assert inventory_after == inventory_before
    assert inventory_bytes_after == inventory_bytes_before
    assert ledger_after == ledger_before


def test_size_registry_schema_and_digest():
    registry = build_size_registry()
    validate_document_schema(registry)
    validate_size_registry(registry)
    assert [row["size_id"] for row in registry["sizes"]] == ["size-00", "size-01", "size-02"]


def test_schema_rejects_unknown_kind_and_unknown_field():
    raises(validate_document_schema, {"document_kind": "unknown"})
    registry = build_size_registry()
    registry["unknown"] = True
    raises(validate_document_schema, registry)


@pytest.mark.parametrize(
    "group",
    [
        {"GlobalSplitU": 1},
        {"MatrixInstruction": [16, 16, 16, 1, 1, 1, 1, 1, 1]},
        {"GlobalSplitU": 1, "MatrixInstruction": [16, 16, 16, 1, 1, 1, 1, 1, 1]},
        {"MatrixInstruction": [16, 16, 16, 1, 1, 1, 1, 1, 1], "MIArchVgpr": False},
    ],
)
def test_group0_exact_legal_variants(group):
    schema = load_json(PROTOCOL_ROOT / "schemas/s10r4-entry.schema.json")
    jsonschema.Draft7Validator(schema["definitions"]["group0"]).validate(group)


def test_group0_rejects_empty_and_unknown_variants():
    schema = load_json(PROTOCOL_ROOT / "schemas/s10r4-entry.schema.json")
    validator = jsonschema.Draft7Validator(schema["definitions"]["group0"])
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({})
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({"MatrixInstruction": [16] * 9, "unknown": 1})


def test_fixture_ascii_is_exact_and_guard_mutation_fails():
    contract = load_contract()
    fixture = build_native_fixture(contract)
    encoded = fixture_ascii_bytes(fixture)
    assert encoded.startswith(b"4 4\n0.0 0.0\n0.5 0.5\n1.0 1.0\n2.0 2.0\n")
    assert encoded.endswith(b"\n") and b"\r" not in encoded
    assert all(len(line.split()) == 40 for line in encoded.splitlines()[5:])
    assert len(ordered_field_digest()) == 64
    changed = copy.deepcopy(fixture)
    changed["guard_order"][0] = "mutated"
    raises(validate_native_fixture, changed, contract)


def test_exact_binary64_and_tree_are_strict():
    exact_binary64(1.5, 1.5, where="x")
    raises(exact_binary64, 0.0, -0.0, where="x")
    raises(exact_binary64, 1.0, 1.0000000000000002, where="x")
    exact_tree({"a": [True, 2, 3.5]}, {"a": [True, 2, 3.5]})
    raises(exact_tree, {"a": 1}, {"a": True})


def test_all_four_native_substitutions_fail_closed():
    faults = {
        key: {"accepted": False, "criterion": "CHANGES_REQUIRED"}
        for key in (
            "native_helper_binary_or_path",
            "source_blob_or_guard_order",
            "host_adapter",
            "runtime_queue_semantics",
        )
    }
    validate_fault_substitutions(faults)
    faults["host_adapter"]["accepted"] = True
    raises(validate_fault_substitutions, faults)


def test_native_transcript_faults_and_actual_runtime_symbols_are_bound():
    fixture = build_native_fixture(load_contract())
    transcript = expected_transcript(fixture)
    validate_native_transcript(fixture, transcript)
    mutations = []
    changed = copy.deepcopy(transcript)
    changed["rows"][0]["checkSolution"] = False
    mutations.append(changed)
    changed = copy.deepcopy(transcript)
    changed["rows"][0]["microSeconds"] += 1.0
    mutations.append(changed)
    changed = copy.deepcopy(transcript)
    changed["queues"][1]["queue_prefix"] = [2, 0]
    mutations.append(changed)
    changed = copy.deepcopy(transcript)
    changed["rows"][0]["problem_constants"]["compute_type"] = "Half"
    mutations.append(changed)
    for changed in mutations:
        raises(validate_native_transcript, fixture, changed)
    source = (PROTOCOL_ROOT / "s10r4/native_formocast_runtime_adapter.cpp").read_text(encoding="utf-8")
    assert "checker.checkActual" in source
    assert "AllSolutionsIterator iterator" in source
    assert "actualQueue(1.0" in source
    assert "std::stable_sort(performance" not in source


def witness(index, atoms):
    return Witness(f"h{index:02d}", frozenset(atoms), (0, index, 0, 0, f"h{index:02d}"))


def test_selector_greedy_tie_padding_and_bounds():
    witnesses = [witness(0, {"a", "b"}), witness(1, {"a", "c"})]
    witnesses.extend(witness(index, {f"padding-{index}"}) for index in range(2, 10))
    selected = deterministic_select(witnesses, {"a", "b", "c"})
    assert selected.c_greedy == 2
    assert selected.k == 10 and len(selected.selected_hashes) == 10
    assert selected.greedy_steps[0].config_hash == "h00"
    raises(deterministic_select, witnesses, {"a"}, minimum_k=9)
    raises(deterministic_select, witnesses[:9], {"a"})


def test_selector_rejects_duplicate_hash_and_cover_over_twenty():
    duplicate = [witness(index, {str(index)}) for index in range(10)] + [witness(0, {"x"})]
    raises(deterministic_select, duplicate, {"0"})
    wide = [witness(index, {str(index)}) for index in range(21)]
    raises(deterministic_select, wide, {str(index) for index in range(21)})


def mapping_object():
    fixture = build_native_fixture(load_contract())
    return copy.deepcopy(fixture["base_size_mapping"])


def provenance():
    return {name: {"source_path": f"solution.{name}", "guessed": False} for name in REQUIRED_MAPPING_FIELDS}


def mapping_rows(pass_id="A", hashes=("h0",)):
    rows = []
    sizes = {
        row["size_id"]: row["value"]
        for row in build_size_registry()["sizes"]
    }
    for config_hash in hashes:
        for size_id in ("size-00", "size-01", "size-02"):
            size = sizes[size_id]
            size_mapping = mapping_object()
            rows.append(
                {
                    "pass_id": pass_id,
                    "sorted_slot": len(rows),
                    "size_id": size_id,
                    "size": size,
                    "raw_config": {"x": 1},
                    "resolved_solution": {"x": 1},
                    "canonical_config_hash": config_hash,
                    "size_mapping": size_mapping,
                    "formocast_input": {
                        "problem": dict(zip(("M", "N", "NumBatches", "K"), size)),
                        "size_mapping": size_mapping,
                    },
                    "required_field_provenance": provenance(),
                }
            )
    return rows


def test_mapping_exact_3k_order_and_parity():
    rows_a = mapping_rows("A", ("h0", "h1"))
    rows_b = mapping_rows("B", ("h0", "h1"))
    validate_mapping_batch(rows_a, ("h0", "h1"), "A")
    validate_mapping_batch(rows_b, ("h0", "h1"), "B")
    compare_mapping_passes(rows_a, rows_b)
    rows_b[0]["size_mapping"]["depthU"] += 1
    raises(compare_mapping_passes, rows_a, rows_b)
    for mutate in (
        lambda row: row.pop("size"),
        lambda row: row.__setitem__("size", [1, 2, 3, 4]),
        lambda row: row["formocast_input"]["problem"].__setitem__("M", row["size"][0] + 1),
        lambda row: row["formocast_input"].__setitem__("extra", 1),
    ):
        forged = copy.deepcopy(rows_a)
        mutate(forged[0])
        raises(validate_mapping_batch, forged, ("h0", "h1"), "A")


def mapping_failure_attempt(**changes):
    values = {
        "status": "allowlisted_failure",
        "signature_id": "required_field_unresolved",
        "failing_pass_id": "A",
        "first_failing_config_hash": "1" * 64,
        "first_failing_sorted_slot": 0,
        "exact_signature_fields": {
            "failure_stage": "required_field_resolution",
            "resolver_result": None,
            "guessed_value_used": False,
            "input_source_and_mapping_identity_complete": True,
        },
        "complete_request_digest": "2" * 64,
        "source_toolchain_harness_identity": "3" * 64,
    }
    values.update(changes)
    return MappingAttempt(**values)


def test_mapping_attempt_table():
    assert decide_mapping_attempts([MappingAttempt("success")]) == "mapping_pass_PASS"
    failed = mapping_failure_attempt()
    assert "FT_BLOCKED_MAPPING" in decide_mapping_attempts([failed, failed])
    raises(decide_mapping_attempts, [failed])


@pytest.mark.parametrize(
    "field,value",
    [
        ("failing_pass_id", "B"),
        ("first_failing_config_hash", "4" * 64),
        ("first_failing_sorted_slot", 3),
        ("complete_request_digest", "5" * 64),
        ("source_toolchain_harness_identity", "6" * 64),
    ],
)
def test_mapping_failure_reproduction_rejects_each_site_identity_mutation(field, value):
    raises(decide_mapping_attempts, [mapping_failure_attempt(), mapping_failure_attempt(**{field: value})])


def test_mapping_failure_rejects_signature_and_exact_field_mutations_before_negative():
    raises(mapping_failure_attempt, signature_id="unknown")
    changed = copy.deepcopy(mapping_failure_attempt().exact_signature_fields)
    changed["guessed_value_used"] = True
    raises(mapping_failure_attempt, exact_signature_fields=changed)


def _test_artifact_record(relative_path, payload):
    return {
        "relative_path": relative_path,
        "mode": 0o644,
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def census_result(success=True, config_hash="c" * 64):
    assembly_payload = b".text\nK:\n"
    helper_source = b"void H() {}\n"
    helper_header = b"void H();\n"
    helper_identity = canonical_sha256(
        {"input_config_hash": config_hash, "kernel_kind": "helper", "kernel_name": "H"}
    )
    assembly_record = _test_artifact_record(
        "build_tmp/ARTIFACTS/assembly/K.s", assembly_payload
    )
    helper_source_record = _test_artifact_record("Kernels.cpp", helper_source)
    helper_header_record = _test_artifact_record("Kernels.h", helper_header)
    helper_component_source = _test_artifact_record(
        f"required_helpers/{helper_identity}.cpp", helper_source
    )
    helper_component_header = _test_artifact_record(
        f"required_helpers/{helper_identity}.h", helper_header
    )
    inventory = sorted(
        [
            assembly_record,
            helper_source_record,
            helper_header_record,
            helper_component_source,
            helper_component_header,
        ],
        key=lambda row: row["relative_path"].encode("utf-8"),
    )
    process_code = 0 if success else -2
    overflow_code = 0 if success else 5
    result = {
        "input_config_hash": config_hash,
        "required_assembly_kernels": [
            {
                "name": "K",
                "canonical_identity": canonical_sha256(
                    {"input_config_hash": config_hash, "kernel_kind": "assembly", "kernel_name": "K"}
                ),
                "terminal_native_result": True,
                "err": not success,
                "processKernelSource_result_code": process_code,
                "overflowed_resources": overflow_code,
                "expected_artifact": assembly_record,
            }
        ],
        "required_helper_kernels": [
            {
                "name": "H",
                "canonical_identity": helper_identity,
                "source_sha256": hashlib.sha256(helper_source).hexdigest(),
                "source_size_bytes": len(helper_source),
                "source_artifact": helper_component_source,
                "header_sha256": hashlib.sha256(helper_header).hexdigest(),
                "header_size_bytes": len(helper_header),
                "header_artifact": helper_component_header,
            }
        ],
        "required_helper_declared_artifacts": [helper_source_record, helper_header_record],
        "reconciled_artifact_inventory": inventory,
        "process_returncode": 0 if success else 23,
        "post_filter_solution_present": success,
        "required_assembly_kernel_set_digest": canonical_sha256(
            {"input_config_hash": config_hash, "kernel_kind": "assembly", "sorted_kernel_names": ["K"]}
        ),
        "required_helper_kernel_set_digest": canonical_sha256(
            {"input_config_hash": config_hash, "kernel_kind": "helper", "sorted_kernel_names": ["H"]}
        ),
        "post_filter_solution_identity": "s",
        "classification_kind": "success" if success else "attrition",
        "ordered_failed_kernel_names": [] if success else ["K"],
        "ordered_native_result_error_codes": [overflow_code],
        "ordered_processKernelSource_result_codes": [process_code],
        "post_filter_solution_membership": success,
    }
    return result


def write_census_artifacts(root, result):
    helper_identity = result["required_helper_kernels"][0]["canonical_identity"]
    payloads = {
        "build_tmp/ARTIFACTS/assembly/K.s": b".text\nK:\n",
        "Kernels.cpp": b"void H() {}\n",
        "Kernels.h": b"void H();\n",
        f"required_helpers/{helper_identity}.cpp": b"void H() {}\n",
        f"required_helpers/{helper_identity}.h": b"void H();\n",
    }
    for relative, payload in payloads.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    inventory = ordinary_file_records(root)[0]
    result["reconciled_artifact_inventory"] = inventory
    return inventory


def test_native_membership_and_stable_classification():
    assert classify_native_membership(census_result()) == "native_membership_success"
    assert stable_classify(census_result(), census_result()) == "operational_codegen_witnessed"
    assert stable_classify(census_result(False), census_result(False)) == "stable_operational_attrition"
    raises(stable_classify, census_result(), census_result(False))


def test_native_membership_separates_helpers_from_assembly():
    result = census_result()
    result["required_helper_kernels"][0].pop("header_sha256")
    raises(classify_native_membership, result)
    result = census_result()
    result["required_assembly_kernels"].append(copy.deepcopy(result["required_assembly_kernels"][0]))
    raises(classify_native_membership, result)


@pytest.mark.parametrize(
    "fault",
    ["omission", "substitution", "duplicate", "unrelated_only", "path", "digest"],
)
def test_native_membership_inventory_association_faults_fail_closed(fault):
    result = census_result()
    inventory = copy.deepcopy(result["reconciled_artifact_inventory"])
    if fault == "omission":
        inventory.pop(0)
    elif fault == "substitution":
        inventory[0]["sha256"] = "0" * 64
    elif fault == "duplicate":
        inventory.append(copy.deepcopy(inventory[0]))
    elif fault == "unrelated_only":
        inventory = [_test_artifact_record("unrelated.bin", b"unrelated")]
    elif fault == "path":
        inventory[0]["relative_path"] = "substituted/" + inventory[0]["relative_path"]
    elif fault == "digest":
        result["required_assembly_kernels"][0]["expected_artifact"]["sha256"] = "f" * 64
    result["reconciled_artifact_inventory"] = inventory
    raises(classify_native_membership, result)


def test_native_membership_config_bound_identities_and_generic_nonzero_attrition():
    attrition = census_result(False)
    attrition["required_assembly_kernels"][0]["processKernelSource_result_code"] = -9
    attrition["required_assembly_kernels"][0]["overflowed_resources"] = 7
    attrition["ordered_processKernelSource_result_codes"] = [-9]
    attrition["ordered_native_result_error_codes"] = [7]
    assert classify_native_membership(attrition) == "ordinary_all_solutions_removed_attrition"
    changed = census_result()
    changed["required_assembly_kernels"][0]["canonical_identity"] = "0" * 64
    raises(classify_native_membership, changed)
    changed = census_result()
    changed["required_helper_kernel_set_digest"] = "0" * 64
    raises(classify_native_membership, changed)


def _mapping_request_fixture(tmp_path):
    selected = []
    for index in range(10):
        raw_config = {"DepthU": 32, "SyntheticOrdinal": index}
        selected.append({"config_hash": canonical_sha256(raw_config), "raw_config": raw_config})
    root = tmp_path / "mapping-native"
    root.mkdir()
    return mapping_request(
        "A", 1, selected, root, {**FIXED_ENVIRONMENT, "PYTHONPATH": "pinned"}, "a" * 64
    )


def test_mapping_overflow_signature_uses_two_separate_native_observables(tmp_path, monkeypatch):
    request = _mapping_request_fixture(tmp_path)

    def backend(child_request):
        result = census_result(False, child_request["config_hash"])
        artifact_root = Path(child_request["artifact_root"])
        artifact_root.mkdir(parents=True)
        write_census_artifacts(artifact_root, result)
        return result

    monkeypatch.setattr("s10r4.census._actual_census_backend", backend)
    output = _actual_mapping_backend(request)
    assert output["signature_id"] == "codegen_resource_overflow"
    assert output["exact_signature_fields"] == {
        "failure_stage": "kernel_source_generation",
        "native_error_class": "KernelWriterAssembly_overflowedResources",
        "native_error_code": 5,
        "processKernelSource_result_code": -2,
        "worker_returncode": 23,
        "post_filter_solution_present": False,
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("overflowed_resources", 4),
        ("processKernelSource_result_code", -1),
        ("overflowed_resources", 0),
    ],
)
def test_mapping_overflow_signature_rejects_native_field_substitution(
    tmp_path, monkeypatch, field, value
):
    request = _mapping_request_fixture(tmp_path)

    def backend(child_request):
        result = census_result(False, child_request["config_hash"])
        result["required_assembly_kernels"][0][field] = value
        artifact_root = Path(child_request["artifact_root"])
        artifact_root.mkdir(parents=True)
        write_census_artifacts(artifact_root, result)
        return result

    monkeypatch.setattr("s10r4.census._actual_census_backend", backend)
    raises(_actual_mapping_backend, request)


def test_mapping_overflow_signature_rejects_missing_or_unknown_native_fields(tmp_path, monkeypatch):
    request = _mapping_request_fixture(tmp_path)

    def backend(child_request):
        result = census_result(False, child_request["config_hash"])
        result["required_assembly_kernels"][0].pop("overflowed_resources")
        result["required_assembly_kernels"][0]["stdout_signature"] = "overflowedResources=5"
        artifact_root = Path(child_request["artifact_root"])
        artifact_root.mkdir(parents=True)
        write_census_artifacts(artifact_root, result)
        return result

    monkeypatch.setattr("s10r4.census._actual_census_backend", backend)
    raises(_actual_mapping_backend, request)


def gpu(index, use="0", memory="0"):
    return {
        "physical_visible_index": index,
        "unique_id": f"u{index}",
        "serial_number": f"s{index}",
        "gfx_version": "gfx942",
        "compute_partition": "SPX",
        "memory_partition": "NPS1",
        "gpu_use_percent": use,
        "vram_allocated_percent": memory,
    }


def test_gpu_selection_and_continuity():
    selected = select_gpu([gpu(2), gpu(1)], {1: [], 2: []})
    assert selected["physical_visible_index"] == 1
    verify_gpu_continuity(selected, copy.deepcopy(selected), [])
    busy = copy.deepcopy(selected)
    busy["gpu_use_percent"] = "1"
    raises(verify_gpu_continuity, selected, busy, [])
    raises(select_gpu, [gpu(0, use="1")], {0: []})


@pytest.mark.parametrize("k,expected", [(10, (0, 4, 9)), (11, (0, 5, 10)), (20, (0, 9, 19))])
def test_dynamic_anchors(k, expected):
    assert anchor_indices(k) == expected


def test_correctness_attempt_table():
    assert decide_correctness_attempts([CorrectnessAttempt("PASS", None, {})]) == "correctness_cell_PASS"
    failed = CorrectnessAttempt("FAIL", "compile", {"code": 7})
    assert "FT_BLOCKED_CORRECTNESS" in decide_correctness_attempts([failed, failed])
    raises(decide_correctness_attempts, [CorrectnessAttempt("FAIL", "unknown", {}), CorrectnessAttempt("FAIL", "unknown", {})])


def test_nearest_rank_noise_and_321_schedule():
    assert nearest_rank(list(range(1, 64)), 0.95) == 60
    groups = {f"g{index}": [100.0] * 7 for index in range(9)}
    result = aggregate_noise(groups)
    assert result["repeat_count"] == 63
    assert result["delta_noise_rank"] == 60 and result["delta_noise"] == 0.0
    assert result["schedule"] == {"NumWarmups": 321, "EnqueuesPerSync": 321, "MaxEnqueuesPerSync": 321}


def test_client_parameter_schedule_exact_once():
    good = "num-warmups=321\nnum-enqueues-per-sync=321\nmax-enqueues-per-sync=321\n"
    validate_client_parameters(good)
    raises(validate_client_parameters, good + "num-warmups=321\n")
    raises(validate_client_parameters, good.replace("321", "320", 1))


def test_lifecycle_order_and_edges():
    lifecycle = Lifecycle().bind_effective_lock()
    lifecycle = lifecycle.enter_stage("verify_effective_lock_and_prelabel_absence")
    raises(lifecycle.enter_stage, "seal_codegen_classification")
    positive = {"scientific_outcome": "positive", "criterion": "S1_ENTRY_GO_EXACT_FRAME"}
    complete = lifecycle.technical_pass(positive)
    assert complete.edge == "S10R4:S1_ENTRY_GO_EXACT_FRAME"
    assert complete.post_commit_audit().edge.endswith("->S11")


@pytest.mark.parametrize(
    "facts,criterion",
    [
        ({"changes_required": True, "operational_blocked": True}, "CHANGES_REQUIRED"),
        ({"operational_blocked": True}, "BLOCKED"),
        ({"negative_mapping": True}, "S1_ENTRY_BLOCKED"),
        ({"negative_correctness": True}, "S1_ENTRY_BLOCKED"),
        ({"inconclusive_noise": True}, None),
    ],
)
def test_outcome_priority(facts, criterion):
    assert decide_outcome(facts)["criterion"] == criterion


def test_positive_outcome_and_document_policy():
    facts = {
        field: True
        for field in (
            "exact_frame_integrity_pass",
            "all_228_codegen_children_stably_classified",
            "stable_survivor_count_at_least_10",
            "full_mandatory_cover",
            "k_at_most_20",
            "mapping_a_b_pass",
            "native_conformance_pass",
            "all_9_correctness_cells_pass",
            "all_63_noise_cells_complete_and_pass",
        )
    }
    facts.update(
        {
            "changes_required": False,
            "operational_blocked": False,
            "negative_mapping": False,
            "negative_correctness": False,
            "inconclusive_noise": False,
        }
    )
    outcome = decide_outcome(facts)
    assert outcome["edge"] == "S10R4:S1_ENTRY_GO_EXACT_FRAME"
    raises(validate_document_policy, {"criterion": "BLOCKED", "scientific_outcome": "not_evaluated"}, set())


def test_environment_and_command_binding():
    validate_environment(FIXED_ENVIRONMENT)
    raises(validate_environment, {**FIXED_ENVIRONMENT, "EXTRA": "x"})
    validate_command_template(
        "validate_contract",
        [
            "/opt/venv/bin/python3",
            "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
            "validate-contract",
        ],
    )
    raises(validate_command_template, "validate_contract", ["python", "validate-contract"])


def test_single_argv_materializer_covers_every_template_and_fault():
    substitutions = {
        "pass_id": "A",
        "child_root": "/tmp/child",
        "attempt_root": "/tmp/attempt",
        "binary_path": "/tmp/native",
        "input_path": "/tmp/input",
        "output_path": "/tmp/output",
        "client_path": "/tmp/client",
        "config_path": "/tmp/config",
    }
    for command_id in sorted(COMMAND_TEMPLATES):
        values = {name: substitutions[name] for name in COMMAND_PLACEHOLDERS[command_id]}
        argv = materialize_command_template(command_id, values)
        assert argv and all(isinstance(value, str) for value in argv)
        residual = [value for value in argv if "{" in value or "}" in value]
        assert residual == (["d32abacfd13579d1f523f035b7a10b0734c4ac47^{commit}"] if command_id == "resolve_geko_commit" else [])
        validate_command_template(command_id, argv, values)
        if COMMAND_PLACEHOLDERS[command_id] == {"pass_id"}:
            values_b = {"pass_id": "B"}
            validate_command_template(command_id, materialize_command_template(command_id, values_b), values_b)
    raises(materialize_command_template, "census", {})
    raises(materialize_command_template, "census", {"pass_id": "C"})
    raises(materialize_command_template, "census", {"pass_id": "A", "unknown": "x"})
    raises(materialize_command_template, "census", {"pass_id": "{still-unresolved}"})
    exact = materialize_command_template("validate_contract")
    raises(validate_command_template, "validate_contract", [*exact, "--extra"])
    raises(validate_command_template, "validate_contract", list(reversed(exact)))


def _stage_state(**updates):
    state = {
        "census_a_count": 0,
        "census_b_count": 0,
        "resource_reforecast": False,
        "classification": False,
        "selection_status": None,
        "mapping_a_status": None,
        "mapping_b_status": None,
        "mapping_corpus_status": None,
        "native_conformance": False,
        "gpu_environment": False,
        "blocker_producer": None,
        "correctness_count": 0,
        "correctness_status": None,
        "noise_count": 0,
        "noise_status": None,
        "decision": False,
        "reproduction": False,
    }
    state.update(updates)
    return state


def test_artifact_derived_stage_projector_full_sequence_and_faults():
    sequence = [
        (_stage_state(), ("census", "A")),
        (_stage_state(census_a_count=114, resource_reforecast=True), ("census", "B")),
        (_stage_state(census_a_count=114, census_b_count=114, resource_reforecast=True), ("classify-select", None)),
        (_stage_state(census_a_count=114, census_b_count=114, resource_reforecast=True, classification=True, selection_status="PASS"), ("mapping", "A")),
        (_stage_state(census_a_count=114, census_b_count=114, resource_reforecast=True, classification=True, selection_status="PASS", mapping_a_status="PASS"), ("mapping", "B")),
        (_stage_state(census_a_count=114, census_b_count=114, resource_reforecast=True, classification=True, selection_status="PASS", mapping_a_status="PASS", mapping_b_status="PASS", mapping_corpus_status="PASS"), ("native-conformance", None)),
        (_stage_state(census_a_count=114, census_b_count=114, resource_reforecast=True, classification=True, selection_status="PASS", mapping_a_status="PASS", mapping_b_status="PASS", mapping_corpus_status="PASS", native_conformance=True), ("gpu-environment", None)),
        (_stage_state(census_a_count=114, census_b_count=114, resource_reforecast=True, classification=True, selection_status="PASS", mapping_a_status="PASS", mapping_b_status="PASS", mapping_corpus_status="PASS", native_conformance=True, gpu_environment=True), ("correctness", None)),
        (_stage_state(census_a_count=114, census_b_count=114, resource_reforecast=True, classification=True, selection_status="PASS", mapping_a_status="PASS", mapping_b_status="PASS", mapping_corpus_status="PASS", native_conformance=True, gpu_environment=True, correctness_count=9, correctness_status="PASS"), ("noise", None)),
        (_stage_state(census_a_count=114, census_b_count=114, resource_reforecast=True, classification=True, selection_status="PASS", mapping_a_status="PASS", mapping_b_status="PASS", mapping_corpus_status="PASS", native_conformance=True, gpu_environment=True, correctness_count=9, correctness_status="PASS", noise_count=63, noise_status="PASS"), ("decision", None)),
    ]
    for state, identity in sequence:
        projection = project_formal_stage(state)
        assert (projection.command_id, projection.pass_id) == identity
    decided = {**sequence[-1][0], "decision": True}
    assert project_formal_stage(decided).command_id == "reproduction"
    assert project_formal_stage({**decided, "reproduction": True}).command_id is None
    gpu_boundary = _stage_state(
        census_a_count=114,
        census_b_count=114,
        resource_reforecast=True,
        classification=True,
        selection_status="PASS",
        mapping_a_status="PASS",
        mapping_b_status="PASS",
        mapping_corpus_status="PASS",
        native_conformance=True,
        blocker_producer="gpu-environment",
    )
    assert project_formal_stage(gpu_boundary).terminal_branch == "BLOCKED"
    assert project_formal_stage(_stage_state(census_a_count=114, census_b_count=114, resource_reforecast=True, classification=True, selection_status="NEGATIVE_MAPPING")).command_id == "decision"
    for forged in (
        _stage_state(census_a_count=1, census_b_count=1),
        _stage_state(census_a_count=114, census_b_count=1, resource_reforecast=False),
        _stage_state(census_a_count=114, census_b_count=114, resource_reforecast=True, selection_status="PASS"),
        {**sequence[-1][0], "correctness_count": 8},
        {**sequence[-1][0], "noise_count": 62},
        _stage_state(reproduction=True),
        _stage_state(blocker_producer="gpu-environment", decision=True),
    ):
        raises(project_formal_stage, forged)


@pytest.mark.parametrize(
    "terminal_state,branch",
    [
        (
            _stage_state(
                census_a_count=114, census_b_count=114, resource_reforecast=True,
                classification=True, selection_status="NEGATIVE_MAPPING",
            ),
            "NEGATIVE_MAPPING",
        ),
        (
            _stage_state(
                census_a_count=114, census_b_count=114, resource_reforecast=True,
                classification=True, selection_status="PASS", mapping_a_status="PASS",
                mapping_b_status="PASS", mapping_corpus_status="PASS",
                native_conformance=True, gpu_environment=True, correctness_count=1,
                correctness_status="NEGATIVE_CORRECTNESS",
            ),
            "NEGATIVE_CORRECTNESS",
        ),
        (
            _stage_state(
                census_a_count=114, census_b_count=114, resource_reforecast=True,
                classification=True, selection_status="PASS", mapping_a_status="PASS",
                mapping_b_status="PASS", mapping_corpus_status="PASS",
                native_conformance=True, gpu_environment=True, correctness_count=9,
                correctness_status="PASS", noise_count=63,
                noise_status="INCONCLUSIVE_NOISE",
            ),
            "INCONCLUSIVE_NOISE",
        ),
        (
            _stage_state(
                census_a_count=114, census_b_count=114, resource_reforecast=True,
                classification=True, selection_status="PASS", mapping_a_status="PASS",
                mapping_b_status="PASS", mapping_corpus_status="PASS",
                native_conformance=True, gpu_environment=True, correctness_count=9,
                correctness_status="PASS", noise_count=63, noise_status="PASS",
            ),
            "POSITIVE",
        ),
    ],
)
def test_base_first_terminal_overlays_require_complete_branch(terminal_state, branch):
    base = project_formal_stage(terminal_state)
    assert base.command_id == "decision" and base.terminal_branch == branch
    decided = {**terminal_state, "decision": True}
    assert project_formal_stage(decided) == StageProjection(
        "independent_reproduction", "reproduction", terminal_branch=branch,
        resume_command_id="decision",
    )
    assert project_formal_stage({**decided, "reproduction": True}) == StageProjection(
        "terminal_after_reproduction", None, terminal_branch=branch,
        resume_command_id="reproduction",
    )


def test_base_first_rejects_incomplete_blocker_decision_and_reproduction_overlays():
    partial_mapping_terminal = _stage_state(
        census_a_count=114, census_b_count=114, resource_reforecast=True,
        classification=True, selection_status="PASS", mapping_a_status="NEGATIVE_MAPPING",
    )
    assert project_formal_stage(partial_mapping_terminal).command_id == "mapping"
    assert project_formal_stage(
        {**partial_mapping_terminal, "blocker_producer": "mapping"}
    ).terminal_branch == "BLOCKED"
    for forged in (
        {**_stage_state(), "blocker_producer": "decision"},
        {**partial_mapping_terminal, "decision": True},
        {**partial_mapping_terminal, "reproduction": True},
        {**partial_mapping_terminal, "decision": True, "reproduction": True},
        {
            **partial_mapping_terminal,
            "mapping_corpus_status": "NEGATIVE_MAPPING",
            "blocker_producer": "mapping",
        },
    ):
        raises(project_formal_stage, forged)


def test_cumulative_audit_ledgers_require_exact_chains_and_inputs():
    def ledger(kind, phases):
        events = []
        previous = None
        for ordinal, (phase, verdict, input_fields) in enumerate(phases):
            event = {
                "ordinal": ordinal, "phase": phase, "verdict": verdict,
                "auditor_task_id": f"/root/auditor-{ordinal}", "fresh": True,
                "implementation_participation": False, "created_utc": "2026-08-02T00:00:00Z",
                "inputs": {field: None for field in input_fields}, "findings": [],
                "previous_event_digest": previous, "event_digest": "0" * 64,
            }
            event["event_digest"] = canonical_sha256({key: value for key, value in event.items() if key != "event_digest"})
            previous = event["event_digest"]
            events.append(event)
        document = {"schema_version": 1, "checkpoint_id": "S10R4", "document_kind": kind, "events": events, "ledger_digest": "0" * 64}
        document["ledger_digest"] = canonical_sha256({key: value for key, value in document.items() if key != "ledger_digest"})
        return document

    import s10r4.contract as contract_module

    pre = ledger(
        "prebinding_audit_ledger",
        [
            (phase, verdict, contract_module.AUDIT_INPUT_FIELDS[phase])
            for phase, verdict in contract_module.PREBINDING_PHASES
        ],
    )
    assert len(validate_audit_ledger(pre, kind="prebinding_audit_ledger", require_count=4)) == 4
    for mutation in (
        lambda value: value["events"][1].__setitem__("previous_event_digest", "0" * 64),
        lambda value: value["events"][2].__setitem__("findings", ["x"]),
        lambda value: value["events"][3]["inputs"].__setitem__("unknown", None),
    ):
        forged = copy.deepcopy(pre)
        mutation(forged)
        raises(validate_audit_ledger, forged, kind="prebinding_audit_ledger", require_count=4)
    post = ledger(
        "post_commit_audit_ledger",
        [
            (phase, verdict, contract_module.AUDIT_INPUT_FIELDS[phase])
            for phase, verdict in contract_module.POST_COMMIT_PHASES
        ],
    )
    assert len(validate_audit_ledger(post, kind="post_commit_audit_ledger")) == 2


def test_post_binding_activation_checks_exact_nineteen_path_git_commit(tmp_path, monkeypatch):
    import s10r4.contract as contract_module

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "s10r4@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "S10R4 Test"], cwd=repo, check=True)
    prebinding_path = repo / "audit/prebinding.json"
    prebinding_path.parent.mkdir(parents=True)
    prebinding_path.write_text('{"ledger":"prebinding"}\n', encoding="utf-8")
    subprocess.run(["git", "add", "audit/prebinding.json"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "parent"], cwd=repo, check=True)
    parent = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    implementation_paths = [f"implementation/p{index:02d}.txt" for index in range(15)]
    prelabel_paths = [f"prelabel/r{index}.json" for index in range(3)]
    lock_relative = "lock/effective.json"
    phase2_paths = [*implementation_paths, *prelabel_paths, lock_relative]
    for relative in [*implementation_paths, *prelabel_paths]:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            canonical_json({"path": relative}, newline=True).decode("utf-8")
            if path.suffix == ".json" else f"{relative}\n",
            encoding="utf-8",
        )

    def binding(path):
        info = path.stat()
        value = strict_json_bytes(path.read_bytes()) if path.suffix == ".json" else None
        return {
            "path": path.relative_to(repo).as_posix(), "mode": stat.S_IMODE(info.st_mode),
            "size_bytes": info.st_size, "raw_sha256": raw_sha256(path),
            "canonical_sha256": None if value is None else canonical_sha256(value),
        }

    implementation_records = [binding(repo / relative) for relative in implementation_paths]
    registry_records = [binding(repo / relative) for relative in prelabel_paths]
    unrelated = {"status_lines": [], "status_projection_sha256": "b" * 64, "attribution": "UNKNOWN_EXTERNAL_PRESERVED", "staged_phase2_paths": []}
    source = {"native_build_manifest": {"path": "unused.json"}}
    lock = {
        "implementation": {"files": implementation_records},
        "predecessor_and_registries": {
            "exact_frame_registry": registry_records[0], "size_registry": registry_records[1],
            "native_fixture": registry_records[2],
        },
        "source_realization": source,
        "governance_and_boundary": {
            "base": {"unrelated_worktree_observation": unrelated},
            "prebinding_audit": {},
        },
        "self_identity": {"canonical_self_sha256": "c" * 64},
    }
    lock_path = repo / lock_relative
    lock_path.parent.mkdir(parents=True)
    lock_path.write_bytes(canonical_json(lock, newline=True))
    subprocess.run(["git", "add", *phase2_paths], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "phase2"], cwd=repo, check=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    monkeypatch.setattr(contract_module, "REPO_ROOT", repo)
    monkeypatch.setattr(contract_module, "PREBINDING_LEDGER_PATH", prebinding_path)
    contract = {
        "identity": {"effective_lock_path": lock_relative},
        "seal_protocol": {"phase2": {"exact_commit_paths": phase2_paths}},
        "prelabel_absence": {"durable_paths": [], "raw_scopes": []},
        "predecessor_frame": {"committed_inputs": []},
    }
    monkeypatch.setattr(contract_module, "load_contract", lambda: contract)
    monkeypatch.setattr(contract_module, "validate_effective_lock", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(contract_module, "_source_realization", lambda *_args, **_kwargs: source)
    absence_projection = {
        "durable": [], "raw_scopes": [],
        "lock": {"path": lock_relative, "absent": False},
    }
    absence = {
        **absence_projection,
        "projection_sha256": canonical_sha256(absence_projection),
    }
    monkeypatch.setattr(
        contract_module,
        "_absence_observation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("historical activation validation must not remeasure live absence")
        ),
    )
    prebinding = {"ledger_digest": "e" * 64}
    monkeypatch.setattr(contract_module, "load_prebinding_audit_ledger", lambda: (prebinding, []))
    path_records = [contract_module._committed_path_record(commit, relative) for relative in phase2_paths]
    inputs = {
        "phase2_commit_oid": commit, "phase2_parent_oid": parent, "commit_is_ancestor_of_head": True,
        "changed_paths": phase2_paths, "path_records": path_records,
        "lock_record": contract_module._binding_record(lock_path), "lock_self_sha256": "c" * 64,
        "prebinding_ledger_record": {**contract_module._binding_record(prebinding_path), "ledger_digest": "e" * 64},
        "formal_absence": absence, "auditor_task_id": "/root/fresh-post-binding", "fresh": True,
        "unrelated_worktree_observation": unrelated, "exact_commit_projection_sha256": "0" * 64,
    }
    inputs["exact_commit_projection_sha256"] = canonical_sha256({key: value for key, value in inputs.items() if key != "exact_commit_projection_sha256"})
    event = {"auditor_task_id": "/root/fresh-post-binding", "event_digest": "f" * 64, "inputs": inputs}
    post_events = []
    post = {"events": post_events}

    def load_postbinding_fixture():
        if not post_events:
            raise S10R4Error("post-commit audit ledger lacks Phase-2 activation event")
        return post, list(post_events)

    monkeypatch.setattr(
        contract_module,
        "load_post_commit_audit_ledger",
        load_postbinding_fixture,
    )
    raises(contract_module.verify_committed_effective_lock, lock_path)
    # Compose that same actual temporary-Git activation path with the literal
    # formal admission and reached-stage projector.  Only lower raw-boundary
    # readers and the worker launch are synthetic.
    module = load_runner("s10r4_runner_actual_postbinding_admission")
    state_root = tmp_path / "actual-admission-stage"
    install_synthetic_projector_state(module, monkeypatch, state_root, _stage_state())
    monkeypatch.setattr(module, "LOCK_PATH", lock_path)
    monkeypatch.setattr(module, "validate_effective_lock", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(module, "verify_prelabel", lambda **_kwargs: {"status": "PASS"})
    monkeypatch.setattr(module, "_print", lambda _value: None)
    frame_path = state_root / "full-frame.json"
    frame_rows = []
    for index in range(1):
        raw_config = {"DepthU": 32, "SyntheticOrdinal": index}
        frame_rows.append(
            {
                "registry_index": index,
                "config_hash": canonical_sha256(raw_config),
                "raw_config": raw_config,
            }
        )
    atomic_write_json(frame_path, {"rows": frame_rows})
    monkeypatch.setattr(module, "FRAME_PATH", frame_path)
    reforecast_path = module.CODEGEN_ROOT / "resource-reforecast.json"

    def seal_reforecast(*_args, **_kwargs):
        atomic_write_json(reforecast_path, {"synthetic_boundary": True})

    monkeypatch.setattr(module, "_seal_resource_reforecast", seal_reforecast)
    argv = materialize_command_template("census", {"pass_id": "A"})
    monkeypatch.setattr(module.sys, "executable", argv[0])
    monkeypatch.setattr(module.sys, "argv", argv[1:])
    arguments = SimpleNamespace(command="census", lock=lock_path.as_posix(), pass_id="A")
    launches = []

    def worker_spy(child_argv, cwd, _environment, stdout, stderr, _timeout):
        request = load_json(cwd / "request.json")
        native = census_result(True, request["config_hash"])
        artifact_root = Path(request["artifact_root"])
        artifact_root.mkdir()
        inventory = write_census_artifacts(artifact_root, native)
        native["stable_input_classification"] = "native_membership_success"
        document = {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": "census_child",
            "pass_id": request["pass_id"],
            "registry_index": request["registry_index"],
            "config_hash": request["config_hash"],
            "input_digest": request["input_digest"],
            "cwd": request["cwd"],
            "argv": child_argv,
            "environment": request["environment"],
            "effective_lock_digest": request["effective_lock_digest"],
            "outputs": native,
            "artifact_inventory": inventory,
        }
        finalize_child(
            cwd / "result.json",
            document,
            {
                "document_kind": "census_child",
                "pass_id": request["pass_id"],
                "registry_index": request["registry_index"],
                "config_hash": request["config_hash"],
            },
        )
        stdout.write_bytes(b"stdout\n")
        stderr.write_bytes(b"")
        launches.append(request["registry_index"])
        return 0, {
            "wall_seconds": 1.0,
            "child_cpu_seconds": 0.5,
            "new_child_tree_bytes": 1,
            "measurement_semantics": "parent_monotonic_wall_rusage_children_and_child_tree_bytes",
        }

    monkeypatch.setattr(module, "_run_logged_observed", worker_spy)
    raises(module.command_census, arguments)
    assert launches == []
    post_events.append(event)
    assert contract_module.verify_committed_effective_lock(lock_path) == lock
    module.command_census(arguments)
    assert launches == [0]
    # A second top-level admission sees the now-live complete raw prefix, still
    # authenticates the immutable historical ordinal-0 absence, and resumes
    # through the artifact-derived state machine without remeasuring absence.
    module.command_census(arguments)
    assert launches == [0]
    (repo / implementation_paths[0]).write_text("drift\n", encoding="utf-8")
    raises(contract_module.verify_committed_effective_lock, lock_path)


def test_forged_activation_preactivation_raw_foreign_binding_01_path_and_partial_binding_02_child_fail_closed(
    tmp_path, monkeypatch
):
    synthetic_contract = {
        "identity": {"effective_lock_path": "locks/binding-02.json"},
        "prelabel_absence": {
            "durable_paths": ["durable/result.json"],
            "raw_scopes": ["raw/formal"],
        },
    }
    projection = {
        "durable": [{"path": "durable/result.json", "absent": True}],
        "raw_scopes": [{"path": "raw/formal", "absent": True}],
        "lock": {"path": "locks/binding-02.json", "absent": False},
    }
    authentic = {**projection, "projection_sha256": canonical_sha256(projection)}
    contract_module._validate_historical_activation_absence(
        authentic, synthetic_contract
    )
    mutations = [
        lambda value: value["raw_scopes"][0].__setitem__("absent", False),
        lambda value: value["raw_scopes"][0].__setitem__(
            "path", "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame/artifacts/formal-codegen"
        ),
        lambda value: value["lock"].__setitem__("path", "locks/foreign.json"),
        lambda value: value.__setitem__("projection_sha256", "0" * 64),
        lambda value: value.__setitem__("forged_live_observation", True),
    ]
    for mutation in mutations:
        forged = copy.deepcopy(authentic)
        mutation(forged)
        raises(
            contract_module._validate_historical_activation_absence,
            forged,
            synthetic_contract,
        )

    module = load_runner("s10r4_runner_partial_binding02_child")
    frame_path = tmp_path / "frame.json"
    raw_config = {"DepthU": 32}
    rows = [{
        "registry_index": 0,
        "config_hash": canonical_sha256(raw_config),
        "raw_config": raw_config,
    }]
    atomic_write_json(frame_path, {"rows": rows})
    monkeypatch.setattr(module, "FRAME_PATH", frame_path)
    monkeypatch.setattr(module, "CODEGEN_ROOT", tmp_path / "formal-codegen")
    expected = module.census_expectations(module.CODEGEN_ROOT, "A", rows)
    child_root = expected[0][0].parent
    child_root.mkdir(parents=True)
    atomic_write_json(child_root / "request.json", {"partial": True})
    raises(module._exact_census_prefix, "A")


def test_actual_constructor_attaches_non_circular_four_event_governance(
    tmp_path, monkeypatch
):
    """Exercise the real constructor in a temporary repository, never production."""
    import s10r4.contract as contract_module

    source_root = REPO_ROOT
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "s10r4@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "S10R4 Test"], cwd=repo, check=True)
    (repo / "setup.txt").write_text("temporary constructor fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "setup.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "setup"], cwd=repo, check=True)

    contract = load_contract()
    supplement = load_contract_supplement()
    supplement_inputs = contract_module._supplement_lock_inputs(supplement)
    recovery_inputs = contract_module._prebinding_recovery_lock_inputs(
        contract_module.load_prebinding_recovery_amendment()
    )

    def copy_relative(relative):
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_root / relative, destination)
        return destination

    implementation_paths = list(contract["write_boundaries"]["implementation_exact_paths"])
    prelabel_paths = list(contract["write_boundaries"]["prelabel_durable_exact_paths"][:-1])
    for relative in [*implementation_paths, *prelabel_paths]:
        copy_relative(relative)
    for row in contract["authority"]["committed_projection"]:
        if not (repo / row["path"]).exists():
            copy_relative(row["path"])

    contract_path = copy_relative(contract["identity"]["contract_path"])
    plan_a_relative = "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/gates/s10r4/plan_a.md"
    plan_a_path = copy_relative(plan_a_relative)
    revision_path = copy_relative(
        "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/gates/s10r4/plan_a-revisions.jsonl"
    )
    baseline_path = copy_relative(
        "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/baseline.md"
    )
    report_md = repo / "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/gates/s10r4/implementer-report.md"
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("# Synthetic implementer report\n", encoding="utf-8")
    report_json = report_md.with_suffix(".json")
    reported_resources = copy.deepcopy(
        load_json(contract_module.IMPLEMENTER_REPORT_PATHS[1])["resources"]
    )
    atomic_write_json(report_json, {"resources": reported_resources})
    assert set(reported_resources) == {
        "whole_role_cpu_seconds", "whole_role_wall_seconds",
        "observed_activity_lower_bound_seconds", "observed_activity_start_utc",
        "observed_activity_end_utc", "storage_bytes_before_reports",
        "historical_carried", "peak_and_transient",
    }
    assert set(reported_resources["storage_bytes_before_reports"]) == {
        "implementation", "prelabel_durable", "prelabel_build", "prelabel_fixtures",
        "prelabel_tests_and_repair_archive", "total",
    }
    plan_b_path = repo / "synthetic/hidden-plan-not-read.md"
    plan_b_path.parent.mkdir(parents=True)
    plan_b_path.write_text("synthetic opaque plan binding\n", encoding="utf-8")
    plan_b_freeze_path = repo / "synthetic/plan-b-freeze.json"
    atomic_write_json(plan_b_freeze_path, {"opaque": True})
    native_manifest = repo / "synthetic/native-build.json"
    atomic_write_json(native_manifest, {"native_executed": False, "products": []})
    summary_path = repo / "synthetic/prelabel-summary.json"
    atomic_write_json(summary_path, {"synthetic": True})
    product_path = repo / "synthetic/native-product.bin"
    product_path.write_bytes(b"product")

    monkeypatch.setattr(contract_module, "REPO_ROOT", repo)
    monkeypatch.setattr(contract_module, "CONTRACT_PATH", contract_path)
    monkeypatch.setattr(contract_module, "PLAN_A_REVISION_LEDGER_PATH", revision_path)
    monkeypatch.setattr(contract_module, "BASELINE_PATH", baseline_path)
    monkeypatch.setattr(contract_module, "IMPLEMENTER_REPORT_PATHS", (report_md, report_json))
    ledger_path = repo / "audit/prebinding.json"
    monkeypatch.setattr(contract_module, "PREBINDING_LEDGER_PATH", ledger_path)
    monkeypatch.setattr(
        contract_module, "POST_COMMIT_LEDGER_PATH", repo / "closure/post-commit-audit.json"
    )
    monkeypatch.setattr(contract_module, "load_contract", lambda: contract)
    monkeypatch.setattr(contract_module, "load_contract_supplement", lambda: supplement)
    monkeypatch.setattr(
        contract_module, "_supplement_lock_inputs", lambda _supplement: supplement_inputs
    )
    monkeypatch.setattr(
        contract_module, "_prebinding_recovery_lock_inputs", lambda _amendment: recovery_inputs
    )
    monkeypatch.setattr(
        contract_module, "load_prebinding_recovery_amendment", lambda: {"synthetic": True}
    )
    monkeypatch.setattr(contract_module, "validate_phase1", lambda: contract)

    pinned_root = repo / "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/artifacts/prelabel-build/pinned-source"
    pinned_records = []
    for declared in contract_module.pinned_source_declarations(contract):
        materialized = pinned_root / declared["repository_path"]
        pinned_records.append(
            {
                **declared,
                "materialized_path": materialized.as_posix(),
                "mode": 0o644,
                "link_count": 1,
                "size_bytes": 1,
                "raw_sha256": "1" * 64,
            }
        )
    summary_path.write_bytes(
        canonical_json({"source_identity": {"files": pinned_records}}, newline=True)
    )
    tools = []
    for tool_id, requested, argv, allowed, first_line, _stderr in contract_module.TOOL_VERSION_SPECS:
        tools.append(
            {
                "tool_id": tool_id, "requested_path": requested, "resolved_path": requested,
                "mode": 0o755, "size_bytes": 1, "binary_sha256": "2" * 64,
                "version_argv": argv, "allowed_returncodes": list(allowed), "returncode": 0,
                "stdout_sha256": "3" * 64, "stderr_sha256": "4" * 64,
                "first_line": first_line,
            }
        )
    commit_resolution = {
        "commit": "5" * 40, "argv": ["/usr/bin/git", "rev-parse"], "returncode": 0,
        "stdout_sha256": "6" * 64, "stderr_sha256": "7" * 64,
    }
    source_realization = {
        "ductile_commit_resolution": commit_resolution,
        "geko_commit_resolution": {**commit_resolution, "commit": "8" * 40},
        "pinned_source_records": pinned_records,
        "actual_yaml": {
            "path": contract["source_and_input_identity"]["actual_yaml"]["path"],
            "git_blob_oid": "9" * 40, "mode": 0o644, "size_bytes": 1,
            "raw_sha256": contract["source_and_input_identity"]["actual_yaml"]["sha256"],
        },
        "tool_records": tools,
        "llvm_executable_closure": [
            {"requested_path": f"/opt/rocm-7.2.4/lib/llvm/bin/{name}", "present": False}
            for name in ("clang++", "clang", "ld.lld", "llvm-mc", "llvm-objcopy", "clang-offload-bundler")
        ],
        "native_build_manifest": contract_module._binding_record(native_manifest),
        "native_build_products": [
            {
                "path": product_path.relative_to(repo).as_posix(), "mode": 0o644,
                "size_bytes": product_path.stat().st_size, "sha256": raw_sha256(product_path),
            }
        ],
        "prelabel_summary": contract_module._binding_record(summary_path),
        "container_realization": {
            "container_name": "perlee", "host_path": "/data1/perlee",
            "container_path": "/src", "mode": "rw",
            "mount_observation": {
                "mount_point": "/src", "mount_options": ["rw"],
                "filesystem_type": "bind", "source": "/data1/perlee",
                "record_sha256": "a" * 64,
            },
            "device_surface": [
                {"path": path, "present": False, "type": None, "mode": None, "major": None, "minor": None}
                for path in ("/dev/kfd", "/dev/dri")
            ],
        },
        "gpu_selection_predicate": {
            "projection": contract["gpu_correctness_and_noise"]["card_selection"]["eligible_predicate"],
            "projection_sha256": canonical_sha256(
                contract["gpu_correctness_and_noise"]["card_selection"]["eligible_predicate"]
            ),
        },
        "in_process_boundaries": ["strict_parsing_schema_hashing"],
    }
    monkeypatch.setattr(contract_module, "_source_realization", lambda *_args, **_kwargs: source_realization)

    def committed_record(_commit, relative):
        payload = (repo / relative).read_bytes()
        return {
            "path": relative, "git_mode": "100644", "blob_oid": "b" * 40,
            "size_bytes": len(payload), "raw_sha256": raw_sha256(repo / relative),
        }

    monkeypatch.setattr(contract_module, "_committed_path_record", committed_record)
    monkeypatch.setattr(
        contract_module, "_validate_prebinding_ledger_inputs", lambda *_args, **_kwargs: None
    )

    phases = list(contract_module.PREBINDING_PHASES)

    def make_events(count):
        events = []
        previous = None
        for ordinal, (phase, verdict) in enumerate(phases[:count]):
            inputs = {field: None for field in contract_module.AUDIT_INPUT_FIELDS[phase]}
            event = {
                "ordinal": ordinal, "phase": phase, "verdict": verdict,
                "auditor_task_id": f"/root/fresh-constructor-{ordinal}", "fresh": True,
                "implementation_participation": False,
                "created_utc": "2026-08-02T00:00:00Z", "inputs": inputs,
                "findings": [], "previous_event_digest": previous, "event_digest": "0" * 64,
            }
            event["event_digest"] = canonical_sha256(
                {key: value for key, value in event.items() if key != "event_digest"}
            )
            previous = event["event_digest"]
            events.append(event)
        return events

    phase2_paths = list(contract["seal_protocol"]["phase2"]["exact_commit_paths"])
    governance_base = contract_module._governance_base(
        contract, "/root/fresh-constructor-3", phase2_paths
    )
    events = make_events(4)
    events[3]["inputs"]["role_resource_boundary_realization"] = governance_base
    events[3]["inputs"]["source_realization"] = source_realization
    events[3]["inputs"]["tool_realization"] = source_realization["tool_records"]
    events[3]["inputs"]["container_device_realization"] = source_realization["container_realization"]
    events[3]["inputs"]["lock_input_projection_hashes"] = {
        key: "c" * 64
        for key in (
            "phase1", "plans", "implementation", "predecessor_and_registries",
            "source_realization", "governance_base", "binding_02_inputs",
            "prebinding_recovery_inputs",
        )
    }
    events[3]["event_digest"] = canonical_sha256(
        {key: value for key, value in events[3].items() if key != "event_digest"}
    )
    ledger = {
        "schema_version": 1, "checkpoint_id": "S10R4",
        "document_kind": "prebinding_audit_ledger", "events": events,
        "ledger_digest": "0" * 64,
    }
    ledger["ledger_digest"] = canonical_sha256(
        {key: value for key, value in ledger.items() if key != "ledger_digest"}
    )

    output = repo / contract["identity"]["effective_lock_path"]
    preflight_lock = contract_module.construct_effective_lock(
        output=output,
        plan_a_path=plan_a_path,
        plan_b_path=plan_b_path,
        plan_b_freeze_path=plan_b_freeze_path,
        audit_verdict_path=ledger_path,
        native_build_manifest=native_manifest,
        prebinding_ledger=ledger,
        write=False,
    )
    assert preflight_lock["prebinding_recovery_inputs"] == recovery_inputs
    assert not ledger_path.exists() and not output.exists()
    atomic_write_json(ledger_path, ledger)
    dry_run_lock = contract_module.construct_effective_lock(
        output=output,
        plan_a_path=plan_a_path,
        plan_b_path=plan_b_path,
        plan_b_freeze_path=plan_b_freeze_path,
        audit_verdict_path=ledger_path,
        native_build_manifest=native_manifest,
        write=False,
    )
    assert dry_run_lock == preflight_lock
    assert not output.exists()
    lock = contract_module.construct_effective_lock(
        output=output,
        plan_a_path=plan_a_path,
        plan_b_path=plan_b_path,
        plan_b_freeze_path=plan_b_freeze_path,
        audit_verdict_path=ledger_path,
        native_build_manifest=native_manifest,
    )
    assert output.is_file()
    assert lock["lock_id"] == "S10R4-A49-EXACT-FRAME-BINDING-02-EFFECTIVE-LOCK-V2"
    assert lock["plans"]["plan_a"]["revision"] == 16
    assert lock["plans"]["plan_a"]["raw_sha256"] == contract_module.PLAN_A_RAW_SHA256
    assert lock["plans"]["predecessor_plan_a"] == contract_module.PLAN_A_PREDECESSOR
    assert lock["binding_02_inputs"] == supplement_inputs
    assert lock["prebinding_recovery_inputs"] == recovery_inputs
    assert lock["binding_02_inputs"]["supplement_record"]["phase1_commit_oid"] == (
        "0a814e476efffebfacaedb904afddbef38ddee15"
    )
    assert lock["binding_02_inputs"]["binding_01_retirement"]["phase2_commit_oid"] == (
        "95e29a8618a4cf6bab1addb26376b1917ddb8404"
    )
    assert lock["binding_02_inputs"]["carried_role_resource_provenance"]["projected_total"] == 6
    assert lock["lifecycle"]["activation"]["historical_absence_expectation"] == (
        contract_module._historical_activation_absence_expectation(contract)
    )
    assert "observation" not in lock["lifecycle"]["activation"]
    assert len(lock["implementation"]["expected_phase2_paths"]) == 19
    assert lock["implementation"]["expected_phase2_paths"][17].endswith(
        "s10r4-stage1-exact-frame-entry-binding-02-lock.json"
    )
    assert lock["governance_and_boundary"]["base"] == governance_base
    assert lock["governance_and_boundary"]["base"]["resources"] == {
        "planning_policy": contract["resources"],
        "historical_carried": supplement["resources"]["carry_from_binding_01"],
        "implementation_reported": contract_module.project_report_resources(
            reported_resources, supplement=supplement
        ),
        "whole_role_cpu_seconds": "UNKNOWN",
        "whole_role_wall_seconds": "UNKNOWN",
    }
    assert lock["governance_and_boundary"]["prebinding_audit"]["ledger_digest"] == ledger["ledger_digest"]
    assert all(
        event["event_digest"] not in canonical_json(event["inputs"]).decode("utf-8")
        and ledger["ledger_digest"] not in canonical_json(event["inputs"]).decode("utf-8")
        for event in events
    )

    for mutate in (
        lambda value: value["governance_and_boundary"]["base"].__setitem__(
            "prebinding_audit", value["governance_and_boundary"]["prebinding_audit"]
        ),
        lambda value: value["source_realization"]["pinned_source_records"].pop(),
        lambda value: value["source_realization"]["pinned_source_records"].append(
            copy.deepcopy(value["source_realization"]["pinned_source_records"][-1])
        ),
        lambda value: value["source_realization"]["pinned_source_records"].__setitem__(
            0, copy.deepcopy(value["source_realization"]["pinned_source_records"][1])
        ),
        lambda value: value["source_realization"]["pinned_source_records"][0].__setitem__(
            "repository_path", "substituted/source.py"
        ),
        lambda value: value["source_realization"]["pinned_source_records"][0].__setitem__(
            "expected_git_blob_oid", "0" * 40
        ),
        lambda value: value["source_realization"]["pinned_source_records"][0].__setitem__(
            "raw_sha256", "0" * 64
        ),
        lambda value: value["source_realization"]["pinned_source_records"][0].__setitem__(
            "mode", 0o755
        ),
        lambda value: value["source_realization"]["pinned_source_records"][0].__setitem__(
            "link_count", 2
        ),
        lambda value: value["governance_and_boundary"]["prebinding_audit"].__setitem__(
            "ledger_digest", "d" * 64
        ),
        lambda value: value["prebinding_recovery_inputs"]["amendment_record"].__setitem__(
            "raw_sha256", "0" * 64
        ),
        lambda value: value["prebinding_recovery_inputs"]["retired_prebinding_attempt"].__setitem__(
            "seal_authority", True
        ),
        lambda value: value["prebinding_recovery_inputs"]["successor_prebinding_ledger"].__setitem__(
            "path",
            "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/gates/s10r4/audit-verdict.json",
        ),
    ):
        forged = copy.deepcopy(lock)
        mutate(forged)
        forged["self_identity"]["canonical_self_sha256"] = canonical_self_hash(
            forged, ("self_identity", "canonical_self_sha256")
        )
        raises(validate_effective_lock, forged, remeasure=False)


def test_effective_lock_schema_has_no_generic_object_reachability():
    schema = load_json(PROTOCOL_ROOT / "schemas/s10r4-entry.schema.json")
    definitions = schema["definitions"]
    pending = [definitions["effectiveLock"]]
    visited = set()
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            reference = node.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/definitions/"):
                name = reference.rsplit("/", 1)[-1]
                assert name not in {"jsonObject", "jsonValue"}
                if name not in visited:
                    visited.add(name)
                    pending.append(definitions[name])
            pending.extend(value for key, value in node.items() if key != "$ref")
        elif isinstance(node, list):
            pending.extend(node)


def test_lock_self_hash_and_lifecycle_rejection():
    lock = {
        "schema_version": 1,
        "lock_id": "S10R4-A47-EXACT-FRAME-EFFECTIVE-BINDING-V1",
        "checkpoint_id": "S10R4",
        "payload_state": "EFFECTIVE_EXECUTION_BINDING",
        "phase1": {
            "contract_path": "contract.yaml",
            "contract_raw_sha256": CONTRACT_RAW_SHA256,
            "contract_canonical_sha256": "a" * 64,
            "phase1_contract_commit_oid": "b" * 40,
            "authority_records": [],
            "workflow_authority_projection_sha256": "c" * 64,
            "scientific_oracle_projection_sha256": "d" * 64,
        },
        "plans": {
            "plan_a": {
                "path": "plan-a.md", "revision": 7,
                "raw_sha256": "07db44ab4b81c2b5f0215edabfa7018981f6e00d9c8ca5f375f05c5018f4d8f8",
                "size_bytes": 60104,
            },
            "plan_b": {"path": "plan-b.md", "raw_sha256": "e" * 64, "size_bytes": 1},
            "plan_b_freeze": {
                "path": "freeze.json", "mode": 420, "size_bytes": 1,
                "raw_sha256": "f" * 64, "canonical_sha256": "1" * 64,
            },
            "parity_audit": {
                "path": "audit.json", "mode": 420, "size_bytes": 1,
                "raw_sha256": "2" * 64, "canonical_sha256": "3" * 64,
            },
        },
        "implementation": {
            "exact_path_count": 15, "files": [], "schema": {}, "unit_test": {},
            "command_templates": {}, "environment": FIXED_ENVIRONMENT,
            "timeouts": {"materialize": 600, "tool_identity": 60, "native_build": 3600, "formal_child": 7200},
        },
        "predecessor_and_registries": {
            "predecessor_input_hashes": [], "predecessor_raw_root": "/raw",
            "raw_inventory": [], "registries": [],
        },
        "source_realization": {
            "ductile": {}, "geko": {}, "actual_yaml": {}, "normal_workflow_sources": [],
            "native_build": {}, "llvm_executable_closure": llvm_executable_closure(),
            "container": "perlee", "mount": {"host": "/data1/perlee", "container": "/src", "mode": "rw"},
            "gpu_selection_predicate": {},
        },
        "governance_and_boundary": {
            "risk_tier": "R3", "repair_numeric_stop_cap": None, "resource_policy": {},
            "implementation_projection_sha256": "4" * 64,
            "prelabel_projection_sha256": "5" * 64, "formal_absence": {},
            "outcome_document_policy_projection_sha256": "6" * 64,
            "downstream_handoff_projection_sha256": "7" * 64,
        },
        "lifecycle": {
            "lock_state": "effective",
            "execution_status": "ready",
            "checkpoint_state": "LOCKED_READY",
            "scientific_outcome": "not_evaluated",
            "edge": None,
            "formal_evidence_allowed": True,
        },
        "self_identity": {
            "algorithm": "sha256_canonical_json_with_only_this_value_zeroed",
            "canonical_self_sha256": "0" * 64,
        },
    }
    lock["self_identity"]["canonical_self_sha256"] = canonical_self_hash(
        lock, ("self_identity", "canonical_self_sha256")
    )
    # The retired revision-7 active-at-construction shape must fail closed.  A
    # revision-10 production lock has dormant pre_audit/activation/post_audit
    # projections and is exercised by the strict synthetic lock tests below.
    raises(validate_effective_lock, lock)


def child(identity):
    document = {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        **identity,
        "identity": identity,
        "outputs": {"status": "complete"},
        "artifact_inventory": [],
        "completion_digest": "0" * 64,
    }
    document["completion_digest"] = completion_digest(document)
    return document


def test_child_finalize_scan_and_duplicate_protection(tmp_path):
    expected = [(tmp_path / "one/result.json", {"slot": 1}), (tmp_path / "two/result.json", {"slot": 2})]
    for path, identity in expected:
        finalize_child(path, child(identity), identity)
    rows = scan_exact_children(tmp_path, expected)
    assert [row["identity"]["slot"] for row in rows] == [1, 2]
    finalize_child(expected[0][0], child({"slot": 1}), {"slot": 1})
    raises(finalize_child, expected[0][0], child({"slot": 1, "extra": True}), {"slot": 1, "extra": True})


def test_git_blob_oid_known_value():
    assert git_blob_oid(b"test content\n") == "d670460b4b4aece5915caf5c68d12f560a9fe3e4"


def test_runner_exposes_all_frozen_commands_without_import_side_effects():
    runner = PROTOCOL_ROOT / "run_s10r4_entry.py"
    spec = importlib.util.spec_from_file_location("s10r4_runner_under_test", runner)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    commands = set(module.parser()._subparsers._group_actions[0].choices)
    assert {
        "validate-contract", "prepare-prelabel", "verify-prelabel", "build-lock", "verify-lock",
        "census", "classify-select", "mapping", "native-conformance", "gpu-environment",
        "correctness", "noise", "decision", "reproduction", "_census-child", "_mapping-child",
        "_correctness-build-child",
    } <= commands


def test_no_retired_module_import_or_formal_placeholder():
    implementation = [
        PROTOCOL_ROOT / "run_s10r4_entry.py",
        *sorted((PROTOCOL_ROOT / "s10r4").glob("*.py")),
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in implementation)
    assert "import s10r3" not in source and "from s10r3" not in source
    assert "formal_placeholder" not in source


@pytest.mark.parametrize("success,expected_code", [(True, 0), (False, 23)])
def test_census_worker_executes_injected_native_boundary_and_scans(
    tmp_path, monkeypatch, success, expected_code
):
    raw_config = {"DepthU": 32}
    config_hash = canonical_sha256(raw_config)
    child_root = tmp_path / f"pass-A/000-{config_hash}"
    child_root.mkdir(parents=True)
    request = census_request(
        "A",
        {"registry_index": 0, "config_hash": config_hash, "raw_config": raw_config},
        child_root,
        {**FIXED_ENVIRONMENT, "PYTHONPATH": "pinned"},
        "a" * 64,
    )
    request_path = child_root / "request.json"
    atomic_write_json(request_path, request)

    def backend(value):
        artifact_root = Path(value["artifact_root"])
        artifact_root.mkdir(parents=True)
        result = census_result(success, value["config_hash"])
        write_census_artifacts(artifact_root, result)
        return result

    monkeypatch.chdir(child_root)
    result_path = child_root / "result.json"
    assert execute_census_worker(request, result_path, backend=backend) == expected_code
    (child_root / "stdout.log").write_bytes(b"stdout\n")
    (child_root / "stderr.log").write_bytes(b"")
    argv = materialize_command_template(
        "census_child", {"child_root": child_root.resolve().as_posix()}
    )
    finalize_process_completion(
        child_root / "process-completion.json",
        command_id="census_child",
        identity={
            key: request[key]
            for key in (
                "pass_id",
                "registry_index",
                "config_hash",
                "input_digest",
                "effective_lock_digest",
            )
        },
        argv=argv,
        cwd=child_root,
        environment=request["environment"],
        process_returncode=expected_code,
        allowed_returncodes=(0, 23),
        resource_observation={
            "wall_seconds": 1.0,
            "child_cpu_seconds": 0.5,
            "new_child_tree_bytes": 7,
            "measurement_semantics": "parent_monotonic_wall_rusage_children_and_child_tree_bytes",
        },
    )
    rows = scan_exact_children(
        tmp_path,
        [
            (
                result_path,
                {
                    "document_kind": "census_child",
                    "pass_id": "A",
                    "registry_index": 0,
                    "config_hash": config_hash,
                },
            )
        ],
    )
    assert rows[0]["outputs"]["process_returncode"] == expected_code


@pytest.mark.parametrize("worker_code", [0, 23, 24])
def test_mapping_worker_executes_injected_complete_boundary(tmp_path, monkeypatch, worker_code):
    root = tmp_path / "mapping"
    root.mkdir()
    selected = []
    for index in range(10):
        raw_config = {"DepthU": 32, "SyntheticOrdinal": index}
        selected.append(
            {"config_hash": canonical_sha256(raw_config), "raw_config": raw_config}
        )
    request = mapping_request(
        "A",
        1,
        selected,
        root,
        {**FIXED_ENVIRONMENT, "PYTHONPATH": "pinned"},
        "a" * 64,
    )
    atomic_write_json(root / "request.json", request)

    def backend(_):
        if worker_code == 0:
            return {
                "status": "success",
                "worker_returncode": 0,
                "rows": mapping_rows(
                    "A", tuple(row["config_hash"] for row in request["selected_rows"])
                ),
            }
        return {
            "status": "allowlisted_failure",
            "worker_returncode": worker_code,
            "signature_id": "codegen_resource_overflow" if worker_code == 23 else "required_field_unresolved",
            "failing_pass_id": "A",
            "first_failing_config_hash": selected[0]["config_hash"],
            "first_failing_sorted_slot": 0,
            "exact_signature_fields": {"complete": True},
        }

    monkeypatch.chdir(root)
    result_path = root / "result.json"
    assert execute_mapping_worker(request, result_path, backend=backend) == worker_code
    (root / "stdout.log").write_bytes(b"stdout\n")
    (root / "stderr.log").write_bytes(b"")
    argv = materialize_command_template(
        "mapping_child", {"attempt_root": root.resolve().as_posix()}
    )
    finalize_process_completion(
        root / "process-completion.json",
        command_id="mapping_child",
        identity={
            key: request[key]
            for key in ("pass_id", "attempt", "input_digest", "effective_lock_digest")
        },
        argv=argv,
        cwd=root,
        environment=request["environment"],
        process_returncode=worker_code,
        allowed_returncodes=(0, 23, 24),
        resource_observation={
            "wall_seconds": 1.0,
            "child_cpu_seconds": 0.5,
            "new_child_tree_bytes": 7,
            "measurement_semantics": "parent_monotonic_wall_rusage_children_and_child_tree_bytes",
        },
    )
    result = load_json(result_path)
    assert result["outputs"]["worker_returncode"] == worker_code
    assert result["completion_digest"] == completion_digest(result)
    assert scan_exact_children(
        root, [(result_path, {"document_kind": "mapping_attempt", "pass_id": "A", "attempt": 1})]
    )[0] == result


@pytest.mark.parametrize(
    "fault",
    [
        "missing_stdout", "missing_stderr", "missing_result", "missing_completion",
        "drift_stdout", "drift_stderr", "drift_result", "result_completion_digest",
        "completion_document_digest", "artifact_projection", "argv", "cwd",
        "environment", "identity", "returncode",
    ],
)
def test_process_completion_faults_fail_closed_and_finalization_is_no_replace(
    tmp_path, monkeypatch, fault
):
    root = tmp_path / fault
    root.mkdir()
    raw_config = {"DepthU": 32}
    config_hash = canonical_sha256(raw_config)
    request = census_request(
        "A",
        {"registry_index": 0, "config_hash": config_hash, "raw_config": raw_config},
        root,
        {**FIXED_ENVIRONMENT, "PYTHONPATH": "pinned"},
        "a" * 64,
    )
    atomic_write_json(root / "request.json", request)

    def backend(value):
        artifact_root = Path(value["artifact_root"])
        artifact_root.mkdir(parents=True)
        result = census_result(True, value["config_hash"])
        write_census_artifacts(artifact_root, result)
        return result

    monkeypatch.chdir(root)
    result_path = root / "result.json"
    assert execute_census_worker(request, result_path, backend=backend) == 0
    (root / "stdout.log").write_bytes(b"stdout\n")
    (root / "stderr.log").write_bytes(b"")
    argv = materialize_command_template(
        "census_child", {"child_root": root.resolve().as_posix()}
    )
    identity = {
        key: request[key]
        for key in (
            "pass_id", "registry_index", "config_hash", "input_digest",
            "effective_lock_digest",
        )
    }
    completion_path = root / "process-completion.json"
    resource = {
        "wall_seconds": 1.0,
        "child_cpu_seconds": 0.5,
        "new_child_tree_bytes": 7,
        "measurement_semantics": "parent_monotonic_wall_rusage_children_and_child_tree_bytes",
    }

    def finalize():
        return finalize_process_completion(
            completion_path,
            command_id="census_child",
            identity=identity,
            argv=argv,
            cwd=root,
            environment=request["environment"],
            process_returncode=0,
            allowed_returncodes=(0, 23),
            resource_observation=resource,
        )

    finalize()
    raises(finalize)

    if fault.startswith("missing_"):
        {
            "missing_stdout": root / "stdout.log",
            "missing_stderr": root / "stderr.log",
            "missing_result": result_path,
            "missing_completion": completion_path,
        }[fault].unlink()
    elif fault == "drift_stdout":
        (root / "stdout.log").write_bytes(b"stdout drift\n")
    elif fault == "drift_stderr":
        (root / "stderr.log").write_bytes(b"stderr drift\n")
    elif fault == "drift_result":
        result_path.write_bytes(result_path.read_bytes() + b" \n")
    elif fault == "result_completion_digest":
        result = load_json(result_path)
        result["completion_digest"] = "0" * 64
        result_path.write_bytes(canonical_json(result, newline=True))
    elif fault == "completion_document_digest":
        completion = load_json(completion_path)
        completion["document_digest"] = "0" * 64
        completion_path.write_bytes(canonical_json(completion, newline=True))
    else:
        completion = load_json(completion_path)
        if fault == "artifact_projection":
            completion["artifact_projection_sha256"] = "0" * 64
        elif fault == "argv":
            completion["argv"] = [*completion["argv"], "--drift"]
        elif fault == "cwd":
            completion["cwd"] = tmp_path.resolve().as_posix()
        elif fault == "environment":
            completion["environment"]["PYTHONPATH"] = "drift"
        elif fault == "identity":
            completion["identity"]["pass_id"] = "B"
        elif fault == "returncode":
            completion["process_returncode"] = 23
        completion_path.write_bytes(canonical_json(seal_digest(completion), newline=True))

    raises(
        scan_exact_children,
        tmp_path,
        [
            (
                result_path,
                {
                    "document_kind": "census_child", "pass_id": "A",
                    "registry_index": 0, "config_hash": config_hash,
                },
            )
        ],
    )


@pytest.mark.parametrize("worker_code,stage", [(0, None), (31, "generate"), (32, "compile")])
def test_correctness_build_worker_executes_injected_stage_boundary(
    tmp_path, monkeypatch, worker_code, stage
):
    root = tmp_path / "correctness"
    root.mkdir()
    selected = {
        **gpu(0),
        "logical_device_index": 0,
        "container_mount": {"host": "/data1/perlee", "container": "/src", "mode": "rw"},
        "allocation_snapshot_sha256": "a" * 64,
        "process_snapshot_sha256": "b" * 64,
    }
    request = correctness_build_request(
        config_hash="h0",
        raw_config={"DepthU": 32},
        anchor_index=0,
        size_id="size-00",
        size=[8, 8, 1, 128],
        attempt=1,
        attempt_root=root,
        selected_card=selected,
        environment={**FIXED_ENVIRONMENT, "PYTHONPATH": "pinned", "ROCR_VISIBLE_DEVICES": "0"},
        effective_lock_digest="a" * 64,
    )

    def backend(_):
        return {"status": "PASS" if worker_code == 0 else "FAIL", "failure_stage": stage, "worker_returncode": worker_code}

    monkeypatch.chdir(root)
    result_path = root / "build-result.json"
    assert execute_correctness_build_worker(request, result_path, backend=backend) == worker_code
    result = load_json(result_path)
    assert result["outputs"]["failure_stage"] == stage
    assert len(result["document_digest"]) == 64


def test_gpu_snapshot_parsers_are_structured_and_deterministic():
    allocation = b'''{"card0":{"Card series":"AMD Instinct MI300X","Unique ID":"u0","Serial Number":"s0","Compute Partition":"SPX","Memory Partition":"NPS1","GPU use (%)":"0","GPU Memory Allocated (%)":"0"}}'''
    rows = parse_allocation_snapshot(allocation)
    assert rows == [gpu(0)]
    assert parse_process_snapshot(b"GPU[0] : PID 41 PID 40\n") == {0: [40, 41]}
    raises(parse_allocation_snapshot, b'{"card0":{"Card series":"unknown"}}')


def test_client_csv_decision_and_noise_rewrite(tmp_path):
    result = tmp_path / "result.csv"
    result.write_text(
        "M,N,NumBatches,K,Validation,ValidationError,GFlops,TimeUS\n"
        "8,8,1,128,PASSED,,123.5,7.25\n",
        encoding="utf-8",
    )
    parsed = parse_single_result_csv(result, [8, 8, 1, 128])
    assert parsed["quality_gflops"] == 123.5
    assert decide_client_result(0, [result], [8, 8, 1, 128])["status"] == "PASS"
    assert decide_client_result(7, [], [8, 8, 1, 128])["failure_stage"] == "smoke"
    source = (
        b"results-file=old.csv\nnum-warmups=321\nnum-enqueues-per-sync=321\n"
        b"max-enqueues-per-sync=321\nother=preserved\n"
    )
    rewritten = rewrite_results_file(source, tmp_path / "new.csv")
    assert rewritten.replace((tmp_path / "new.csv").as_posix().encode(), b"old.csv") == source
    raises(rewrite_results_file, source + b"results-file=again.csv\n", tmp_path / "x.csv")


def test_formal_runner_handlers_are_concrete_and_internal_workers_dispatch():
    runner = PROTOCOL_ROOT / "run_s10r4_entry.py"
    spec = importlib.util.spec_from_file_location("s10r4_runner_handlers", runner)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    choices = module.parser()._subparsers._group_actions[0].choices
    expected = {
        "census": "command_census",
        "classify-select": "command_classify_select",
        "mapping": "command_mapping",
        "native-conformance": "command_native_conformance",
        "gpu-environment": "command_gpu_environment",
        "correctness": "command_correctness",
        "noise": "command_noise",
        "decision": "command_decision",
        "reproduction": "command_reproduction",
    }
    for command, handler_name in expected.items():
        assert choices[command].get_default("handler").__name__ == handler_name
    for command in ("_census-child", "_mapping-child", "_correctness-build-child"):
        assert choices[command].get_default("handler").__name__ == "command_internal_worker"


def test_strace_root_manifest_is_parsed_without_launching_processes(tmp_path):
    runner = PROTOCOL_ROOT / "run_s10r4_entry.py"
    spec = importlib.util.spec_from_file_location("s10r4_runner_strace", runner)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    expected = [sys.executable, "worker.py", "_correctness-build-child", "--request", str(tmp_path / "request.json"), "--result", str(tmp_path / "result.json")]
    trace = tmp_path / "execve.log"
    trace.write_text(f'123 execve({sys.executable!r}, {expected!r}, 0x0) = 0\n', encoding="utf-8")
    root_executable = Path(sys.executable).resolve(strict=True)
    root_binding = {
        "command_kind": "correctness_build_child",
        "requested_executable": sys.executable,
        "resolved_executable": root_executable.as_posix(),
        "executable_sha256": raw_sha256(root_executable),
        "argv": expected,
        "cwd": tmp_path.as_posix(),
        "environment": FIXED_ENVIRONMENT,
    }
    manifest = module._parse_strace_execve(
        trace,
        {"source_realization": {"llvm_executable_closure": []}},
        expected,
        root_binding,
    )
    assert manifest["record_count"] == 1
    assert manifest["records"][0]["argv"] == expected
    assert manifest["records"][0]["association_kind"] == "root_python"
    assert not ({"parent_pid", "cwd", "environment"} & set(manifest["records"][0]))
    failed = tmp_path / "failed-execve.log"
    failed.write_text(f'124 execve({sys.executable!r}, {expected!r}, 0x0) = -1 ENOENT\n', encoding="utf-8")
    raises(
        module._parse_strace_execve,
        failed,
        {"source_realization": {"llvm_executable_closure": []}},
        expected,
        root_binding,
    )


def load_runner(name):
    runner = PROTOCOL_ROOT / "run_s10r4_entry.py"
    spec = importlib.util.spec_from_file_location(name, runner)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _synthetic_internal_mapping_request(root):
    environment = {
        **FIXED_ENVIRONMENT,
        "PYTHONPATH": (
            "/src/rocm-libraries/agent_run/260802-ductile-factorized-guidance-"
            "s10r4-exact-frame-binding-02/artifacts/prelabel-build/pinned-source/"
            "projects/hipblaslt/tensilelite"
        ),
    }
    request = {
        "checkpoint_id": "S10R4",
        "document_kind": "mapping_request",
        "cwd": root.as_posix(),
        "environment": environment,
        "effective_lock_digest": "a" * 64,
    }
    request["input_digest"] = canonical_sha256(request)
    return request


def test_real_cli_internal_worker_reaches_handler_from_request_bound_child_cwd(tmp_path):
    request_path = tmp_path / "request.json"
    result_path = tmp_path / "result.json"
    request = _synthetic_internal_mapping_request(tmp_path)
    atomic_write_json(request_path, request)
    completed = subprocess.run(
        materialize_command_template("mapping_child", {"attempt_root": tmp_path.as_posix()}),
        cwd=tmp_path,
        env=request["environment"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 2
    assert b"mapping worker request exact field set mismatch" in completed.stderr
    assert not result_path.exists()
    assert not (tmp_path / "process-completion.json").exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["request.json"]


def test_top_level_non_repository_cwd_fails_closed(tmp_path):
    argv = materialize_command_template("validate_contract")
    argv[1] = (PROTOCOL_ROOT / "run_s10r4_entry.py").as_posix()
    completed = subprocess.run(
        argv,
        cwd=tmp_path,
        env=FIXED_ENVIRONMENT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 2
    assert b"command cwd must be /src/rocm-libraries" in completed.stderr
    assert not list(tmp_path.iterdir())


def test_top_level_extra_environment_fails_closed():
    completed = subprocess.run(
        materialize_command_template("validate_contract"),
        cwd=REPO_ROOT,
        env={**FIXED_ENVIRONMENT, "EXTRA": "forbidden"},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 2
    assert b"fixed environment mismatch" in completed.stderr


@pytest.mark.parametrize("fault", ["relative", "different_parent", "wrong_cwd", "extra_env", "wrong_argv"])
def test_wrong_worker_request_result_cwd_environment_or_argv_fails_closed(
    tmp_path, fault
):
    child = tmp_path / "child"
    child.mkdir()
    request_path = child / "request.json"
    result_path = child / "result.json"
    request = _synthetic_internal_mapping_request(child)
    atomic_write_json(request_path, request)
    argv = materialize_command_template("mapping_child", {"attempt_root": child.as_posix()})
    cwd = child
    environment = dict(request["environment"])
    if fault == "relative":
        argv = [*argv[:-3], "request.json", "--result", "result.json"]
    elif fault == "different_parent":
        foreign = tmp_path / "foreign"
        foreign.mkdir()
        argv[-1] = (foreign / "result.json").as_posix()
    elif fault == "wrong_cwd":
        cwd = tmp_path
    elif fault == "extra_env":
        environment["EXTRA"] = "forbidden"
    else:
        argv[-1] = (child / "other-result.json").as_posix()
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 2
    assert b"S10R4_FAIL_CLOSED" in completed.stderr
    assert not result_path.exists()
    assert not (child / "process-completion.json").exists()


@pytest.mark.parametrize(
    ("fault", "expected_reason"),
    [
        ("preexisting_result", b"formal worker request/result boundary mismatch"),
        ("request_cwd_mismatch", b"formal worker cwd differs from its request"),
        (
            "environment_missing",
            b"formal worker request environment differs from the frozen worker environment",
        ),
        (
            "environment_value_drift",
            b"formal worker request environment differs from the frozen worker environment",
        ),
        ("wrong_document_kind", b"formal worker request identity mismatch"),
        ("wrong_input_digest", b"formal worker request digest mismatch"),
        (
            "wrong_correctness_gpu_card_environment",
            b"formal worker request environment differs from the frozen worker environment",
        ),
    ],
)
def test_permanent_internal_admission_fail_closed_variants(
    tmp_path, fault, expected_reason
):
    child = tmp_path / "child"
    child.mkdir()
    request_path = child / "request.json"
    result_path = child / "result.json"
    request = _synthetic_internal_mapping_request(child)
    command_id = "mapping_child"
    if fault == "request_cwd_mismatch":
        request["cwd"] = (tmp_path / "foreign-request-cwd").as_posix()
    elif fault == "environment_missing":
        del request["environment"]["PYTHONHASHSEED"]
    elif fault == "environment_value_drift":
        request["environment"]["PYTHONHASHSEED"] = "1"
    elif fault == "wrong_document_kind":
        request["document_kind"] = "census_request"
    elif fault == "wrong_correctness_gpu_card_environment":
        request["document_kind"] = "correctness_build_request"
        request["selected_gpu"] = {"physical_visible_index": 0}
        request["environment"]["ROCR_VISIBLE_DEVICES"] = "1"
        command_id = "correctness_build_child"
        request_path = child / "build-request.json"
        result_path = child / "build-result.json"
    if fault != "wrong_input_digest":
        request["input_digest"] = canonical_sha256(
            {key: value for key, value in request.items() if key != "input_digest"}
        )
    else:
        request["input_digest"] = "0" * 64
    atomic_write_json(request_path, request)
    preexisting_result = b"preexisting result must remain untouched\n"
    if fault == "preexisting_result":
        result_path.write_bytes(preexisting_result)
    completed = subprocess.run(
        materialize_command_template(command_id, {"attempt_root": child.as_posix()}),
        cwd=child,
        env=request["environment"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 2
    assert b"S10R4_FAIL_CLOSED" in completed.stderr
    assert expected_reason in completed.stderr
    if fault == "preexisting_result":
        assert result_path.read_bytes() == preexisting_result
        expected_files = sorted([request_path.name, result_path.name])
    else:
        assert not result_path.exists()
        expected_files = [request_path.name]
    assert not (child / "process-completion.json").exists()
    for forbidden in (
        "native",
        "formal-codegen",
        "formal-mapping",
        "formal-native",
        "formal-gpu",
        "reproduction",
    ):
        assert not (child / forbidden).exists()
    assert sorted(
        path.relative_to(child).as_posix()
        for path in child.rglob("*")
        if path.is_file()
    ) == expected_files


def install_synthetic_projector_state(module, monkeypatch, root, state):
    """Drive the real reached-stage projector from synthetic lower boundaries."""
    paths = {
        "CODEGEN_ROOT": root / "formal-codegen",
        "MAPPING_ROOT": root / "formal-mapping",
        "NATIVE_ROOT": root / "formal-native",
        "GPU_ROOT": root / "formal-gpu",
        "REPRODUCTION_ROOT": root / "reproduction",
        "FRAME_PATH": root / "frame.json",
        "CLASSIFICATION_PATH": root / "classification.json",
        "SELECTION_PATH": root / "selection.json",
        "MAPPING_CORPUS_PATH": root / "mapping-corpus.json",
        "CONFORMANCE_PATH": root / "conformance.json",
        "ENVIRONMENT_PATH": root / "environment.json",
        "CORRECTNESS_PATH": root / "correctness.json",
        "NOISE_PATH": root / "noise.json",
        "DECISION_PATH": root / "decision.json",
        "BLOCKER_PATH": root / "blocker.json",
        "GATE_RECORD_PATH": root / "gate.json",
        "REPORT_PATH": root / "report.md",
        "LOCK_PATH": root / "effective-lock.json",
    }
    for name, path in paths.items():
        monkeypatch.setattr(module, name, path)
    atomic_write_json(paths["FRAME_PATH"], {"rows": []})
    atomic_write_json(paths["LOCK_PATH"], {"synthetic_lock": True})
    resource_path = paths["CODEGEN_ROOT"] / "resource-reforecast.json"
    payloads = {
        paths["CLASSIFICATION_PATH"]: {},
        paths["SELECTION_PATH"]: {
            "status": state["selection_status"], "selected_hashes": [], "k": 10,
        },
        paths["MAPPING_CORPUS_PATH"]: {"status": state["mapping_corpus_status"]},
        paths["CONFORMANCE_PATH"]: {"status": "PASS"},
        paths["ENVIRONMENT_PATH"]: {"status": "PASS"},
        paths["CORRECTNESS_PATH"]: {"status": state["correctness_status"]},
        paths["NOISE_PATH"]: {"status": state["noise_status"]},
    }
    markers = (
        (resource_path, state["resource_reforecast"]),
        (paths["CLASSIFICATION_PATH"], state["classification"]),
        (paths["SELECTION_PATH"], state["selection_status"] is not None),
        (paths["MAPPING_CORPUS_PATH"], state["mapping_corpus_status"] is not None),
        (paths["CONFORMANCE_PATH"], state["native_conformance"]),
        (paths["ENVIRONMENT_PATH"], state["gpu_environment"]),
        (paths["CORRECTNESS_PATH"], state["correctness_status"] is not None),
        (paths["NOISE_PATH"], state["noise_status"] is not None),
    )
    for path, present in markers:
        if present:
            atomic_write_json(path, payloads.get(path, {"resource": True}))
    monkeypatch.setattr(
        module,
        "_exact_census_prefix",
        lambda pass_id: state["census_a_count"] if pass_id == "A" else state["census_b_count"],
    )
    monkeypatch.setattr(module, "_seal_resource_reforecast", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(module, "_recompute_classification_and_selection", lambda: ({}, {}, []))
    monkeypatch.setattr(
        module,
        "_exact_mapping_prefix",
        lambda pass_id, *_args, **_kwargs: state[
            "mapping_a_status" if pass_id == "A" else "mapping_b_status"
        ],
    )
    monkeypatch.setattr(
        module,
        "_exact_correctness_prefix",
        lambda *_args, **_kwargs: state["correctness_count"],
    )
    monkeypatch.setattr(
        module,
        "_exact_noise_prefix",
        lambda *_args, **_kwargs: state["noise_count"],
    )
    def synthetic_payload(path, _kind):
        if path in payloads:
            return copy.deepcopy(payloads[path])
        return load_json(path)["payload"]

    monkeypatch.setattr(module, "_load_payload", synthetic_payload)
    monkeypatch.setattr(
        module,
        "_rederive_mapping_corpus",
        lambda *_args, **_kwargs: load_json(paths["MAPPING_CORPUS_PATH"]),
    )
    monkeypatch.setattr(
        module,
        "rederive_native_conformance",
        lambda **_kwargs: copy.deepcopy(payloads[paths["CONFORMANCE_PATH"]]),
    )
    monkeypatch.setattr(module, "_rederive_environment_summary", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        module,
        "_rederive_correctness_summary",
        lambda *_args, **_kwargs: load_json(paths["CORRECTNESS_PATH"]),
    )
    monkeypatch.setattr(
        module,
        "_rederive_noise_summary",
        lambda *_args, **_kwargs: load_json(paths["NOISE_PATH"]),
    )
    return paths


def install_actual_admission(module, monkeypatch, command, *, pass_id=None, lock=None):
    """Install only activation/prelabel fakes; admission and projection stay real."""
    lock_value = lock or {"source_realization": {"llvm_executable_closure": []}}
    monkeypatch.setattr(module, "verify_committed_effective_lock", lambda _path: lock_value)
    monkeypatch.setattr(module, "validate_effective_lock", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(module, "verify_prelabel", lambda **_kwargs: {"status": "PASS"})
    substitutions = {} if pass_id is None else {"pass_id": pass_id}
    argv = materialize_command_template(command, substitutions)
    monkeypatch.setattr(module.sys, "executable", argv[0])
    monkeypatch.setattr(module.sys, "argv", argv[1:])
    values = {"command": command, "lock": module.LOCK_PATH.as_posix()}
    if pass_id is not None:
        values["pass_id"] = pass_id
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    "producer,stage,reason",
    [
        ("census", "codegen_census_pass_A_all_114", "ARTIFACT_PRESERVATION_OR_COMPLETION_IMPOSSIBLE"),
        ("mapping", "mapping_pass_A", "ARTIFACT_PRESERVATION_OR_COMPLETION_IMPOSSIBLE"),
        ("native-conformance", "native_sentinel_runtime_conformance", "UNSAFE_PLATFORM_STATE"),
        ("gpu-environment", "GPU_environment", "NO_ELIGIBLE_GPU_MATERIAL_AVAILABILITY"),
        ("correctness", "nine_correctness_cells", "SELECTED_GPU_IDENTITY_UNAVAILABLE"),
        ("noise", "sixty_three_noise_cells", "SELECTED_GPU_IDENTITY_UNAVAILABLE"),
    ],
)
def test_internal_blocker_only_creation_rederivation_and_faults(
    tmp_path, monkeypatch, producer, stage, reason
):
    module = load_runner(f"s10r4_runner_blocker_only_{producer.replace('-', '_')}")
    states = {
        "census": _stage_state(),
        "mapping": _stage_state(
            census_a_count=114, census_b_count=114, resource_reforecast=True,
            classification=True, selection_status="PASS",
        ),
        "native-conformance": _stage_state(
            census_a_count=114, census_b_count=114, resource_reforecast=True,
            classification=True, selection_status="PASS", mapping_a_status="PASS",
            mapping_b_status="PASS", mapping_corpus_status="PASS",
        ),
        "gpu-environment": _stage_state(
            census_a_count=114, census_b_count=114, resource_reforecast=True,
            classification=True, selection_status="PASS", mapping_a_status="PASS",
            mapping_b_status="PASS", mapping_corpus_status="PASS", native_conformance=True,
        ),
        "correctness": _stage_state(
            census_a_count=114, census_b_count=114, resource_reforecast=True,
            classification=True, selection_status="PASS", mapping_a_status="PASS",
            mapping_b_status="PASS", mapping_corpus_status="PASS", native_conformance=True,
            gpu_environment=True,
        ),
        "noise": _stage_state(
            census_a_count=114, census_b_count=114, resource_reforecast=True,
            classification=True, selection_status="PASS", mapping_a_status="PASS",
            mapping_b_status="PASS", mapping_corpus_status="PASS", native_conformance=True,
            gpu_environment=True, correctness_count=9, correctness_status="PASS",
        ),
    }
    paths = install_synthetic_projector_state(module, monkeypatch, tmp_path, states[producer])
    blocker_path = paths["BLOCKER_PATH"]
    evidence = tmp_path / "raw/allocation.stdout"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"complete material snapshot\n")
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "BLOCKER_PATH", blocker_path)
    projection = module._project_reached_formal_stage("a" * 64)
    assert (projection.stage_id, projection.command_id) == (stage, producer)
    document = module.write_operational_blocker(
        producer_command_id=producer,
        reason_code=reason,
        evidence_paths=[evidence],
        pre_block_projection=projection,
        lock_digest="a" * 64,
    )
    validate_document_schema(document)
    assert module._validate_existing_operational_blocker("a" * 64, producer)["reason_code"] == reason
    assert module.write_operational_blocker(
        producer_command_id=producer,
        reason_code=reason,
        evidence_paths=[evidence],
        pre_block_projection=projection,
        lock_digest="a" * 64,
    ) == document
    raises(
        module.write_operational_blocker,
        producer_command_id=producer,
        reason_code="TRANSIENT_BUSY",
        evidence_paths=[evidence],
        pre_block_projection=projection,
        lock_digest="a" * 64,
    )
    raises(
        module.write_operational_blocker,
        producer_command_id="noise" if producer != "noise" else "census",
        reason_code="UNSAFE_PLATFORM_STATE",
        evidence_paths=[evidence],
        pre_block_projection=projection,
        lock_digest="a" * 64,
    )
    evidence.write_bytes(b"drift\n")
    raises(module._validate_existing_operational_blocker, "a" * 64, producer)


def test_internal_worker_command_ids_resolve_to_the_single_frozen_materializer(tmp_path):
    module = load_runner("s10r4_runner_internal_command_identity")
    request = tmp_path / "slot/request.json"
    cases = {
        "_census-child": "census_child",
        "_mapping-child": "mapping_child",
        "_correctness-build-child": "correctness_build_child",
    }
    for cli_name, command_id in cases.items():
        observed_id, substitutions = module._command_template_identity(
            SimpleNamespace(command=cli_name, request=request.as_posix())
        )
        assert observed_id == command_id
        assert list(substitutions.values()) == [request.parent.resolve(strict=False).as_posix()]
        materialize_command_template(command_id, substitutions)


def test_top_correctness_orchestrates_exact_dynamic_nine_cells(tmp_path, monkeypatch):
    module = load_runner("s10r4_runner_correctness_top")
    install_synthetic_projector_state(
        module,
        monkeypatch,
        tmp_path / "stage",
        _stage_state(
            census_a_count=114, census_b_count=114, resource_reforecast=True,
            classification=True, selection_status="PASS", mapping_a_status="PASS",
            mapping_b_status="PASS", mapping_corpus_status="PASS", native_conformance=True,
            gpu_environment=True,
        ),
    )
    frame_path = tmp_path / "frame.json"
    size_path = tmp_path / "sizes.json"
    hashes = [f"h{index}" for index in range(10)]
    atomic_write_json(frame_path, {"rows": [{"config_hash": value, "raw_config": {"DepthU": 32}} for value in hashes]})
    atomic_write_json(
        size_path,
        {"sizes": [{"size_id": f"size-0{index}", "value": [8 + index, 8, 1, 128]} for index in range(3)]},
    )
    monkeypatch.setattr(module, "FRAME_PATH", frame_path)
    monkeypatch.setattr(module, "SIZE_PATH", size_path)
    monkeypatch.setattr(module, "GPU_ROOT", tmp_path / "gpu")
    monkeypatch.setattr(module, "CORRECTNESS_PATH", tmp_path / "correctness.json")
    arguments = install_actual_admission(module, monkeypatch, "correctness")

    def payload(_, kind):
        return {
            "codegen_classification": {},
            "environment": {"status": "PASS", "selected_gpu": gpu(0)},
            "operational_selection": {"status": "PASS", "k": 10, "selected_hashes": hashes},
            "mapping_corpus": {"status": "PASS"},
            "sentinel_conformance": {"status": "PASS"},
        }[kind]

    calls = []

    def attempt(_lock, _lock_digest, _gpu, row, anchor, size_id, _size, attempt_number):
        calls.append((row["config_hash"], anchor, size_id, attempt_number))
        return module.seal_digest(
            {
                "document_kind": "correctness_attempt",
                "status": "PASS",
                "failure_stage": None,
                "signature": {},
                "client_parameters_path": f"/tmp/{anchor}-{size_id}.ini",
                "client_parameters_sha256": "c" * 64,
                "client_path": "/tmp/tensilelite-client",
                "client_sha256": "b" * 64,
            }
        )

    captured = {}
    monkeypatch.setattr(module, "_load_payload", payload)
    monkeypatch.setattr(module, "_correctness_attempt", attempt)
    monkeypatch.setattr(module, "_print", lambda value: None)
    monkeypatch.setattr(
        module,
        "_write_formal",
        lambda path, kind, value: captured.update({"kind": kind, "payload": value}) or {"document_digest": "d" * 64},
    )
    module.command_correctness(arguments)
    assert [(anchor, size) for _, anchor, size, _ in calls] == [
        (anchor, f"size-0{size}") for anchor in (0, 4, 9) for size in range(3)
    ]
    assert all(attempt_number == 1 for *_, attempt_number in calls)
    assert captured["payload"]["cell_count"] == 9 and captured["payload"]["status"] == "PASS"


def test_top_noise_orchestrates_exact_sixty_three_cells(tmp_path, monkeypatch):
    module = load_runner("s10r4_runner_noise_top")
    install_synthetic_projector_state(
        module,
        monkeypatch,
        tmp_path / "stage",
        _stage_state(
            census_a_count=114, census_b_count=114, resource_reforecast=True,
            classification=True, selection_status="PASS", mapping_a_status="PASS",
            mapping_b_status="PASS", mapping_corpus_status="PASS", native_conformance=True,
            gpu_environment=True, correctness_count=9, correctness_status="PASS",
        ),
    )
    monkeypatch.setattr(module, "GPU_ROOT", tmp_path / "gpu")
    monkeypatch.setattr(module, "NOISE_PATH", tmp_path / "noise.json")
    arguments = install_actual_admission(module, monkeypatch, "noise")
    cells = [
        {
            "anchor_index": anchor,
            "size_id": f"size-0{size}",
            "size": [8 + size, 8, 1, 128],
            "config_hash": f"h{anchor}",
            "attempt_digest": "a" * 64,
            "client_parameters_path": "/tmp/source.ini",
            "client_parameters_sha256": "c" * 64,
        }
        for anchor in (0, 4, 9)
        for size in range(3)
    ]

    def payload(_, kind):
        return {
            "codegen_classification": {},
            "environment": {"status": "PASS", "selected_gpu": gpu(0)},
            "smoke_correctness": {"status": "PASS", "successful_cells": cells},
            "operational_selection": {"status": "PASS", "k": 10, "selected_hashes": []},
            "mapping_corpus": {"status": "PASS"},
            "sentinel_conformance": {"status": "PASS"},
        }[kind]

    calls = []

    def observation(_gpu, cell, repeat, lock_digest):
        assert lock_digest == raw_sha256(module.LOCK_PATH)
        calls.append((cell["anchor_index"], cell["size_id"], repeat))
        return {"quality_gflops": 100.0, "document_digest": canonical_sha256(calls[-1])}

    captured = {}
    monkeypatch.setattr(module, "_load_payload", payload)
    monkeypatch.setattr(module, "_noise_observation", observation)
    monkeypatch.setattr(module, "_print", lambda value: None)
    monkeypatch.setattr(
        module,
        "_write_formal",
        lambda path, kind, value: captured.update({"kind": kind, "payload": value}) or {"document_digest": "d" * 64},
    )
    module.command_noise(arguments)
    assert len(calls) == 63
    assert calls[0] == (0, "size-00", 1) and calls[-1] == (9, "size-02", 7)
    assert captured["payload"]["status"] == "PASS"
    assert captured["payload"]["aggregate"]["delta_noise_rank"] == 60


def test_top_decision_writes_exact_outcome_specific_documents_in_temp(tmp_path, monkeypatch):
    module = load_runner("s10r4_runner_decision_top")
    install_synthetic_projector_state(
        module,
        monkeypatch,
        tmp_path / "stage",
        _stage_state(
            census_a_count=114, census_b_count=114, resource_reforecast=True,
            classification=True, selection_status="PASS", mapping_a_status="PASS",
            mapping_b_status="PASS", mapping_corpus_status="PASS", native_conformance=True,
            gpu_environment=True, correctness_count=9, correctness_status="PASS",
            noise_count=63, noise_status="PASS",
        ),
    )
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "DECISION_PATH", tmp_path / "decision.json")
    monkeypatch.setattr(module, "REPORT_PATH", tmp_path / "report.md")
    monkeypatch.setattr(module, "GATE_RECORD_PATH", tmp_path / "gate.json")
    monkeypatch.setattr(module, "BLOCKER_PATH", tmp_path / "blocker.json")
    arguments = install_actual_admission(module, monkeypatch, "decision")
    facts = {
        field: True
        for field in (
            "exact_frame_integrity_pass",
            "all_228_codegen_children_stably_classified",
            "stable_survivor_count_at_least_10",
            "full_mandatory_cover",
            "k_at_most_20",
            "mapping_a_b_pass",
            "native_conformance_pass",
            "all_9_correctness_cells_pass",
            "all_63_noise_cells_complete_and_pass",
        )
    }
    facts.update(
        {
            "changes_required": False,
            "operational_blocked": False,
            "negative_mapping": False,
            "negative_correctness": False,
            "inconclusive_noise": False,
        }
    )
    monkeypatch.setattr(module, "_decision_facts", lambda: facts)
    monkeypatch.setattr(module, "_print", lambda value: None)
    module.command_decision(arguments)
    decision = load_json(tmp_path / "decision.json")
    assert decision["payload"]["edge"] == "S10R4:S1_ENTRY_GO_EXACT_FRAME"
    assert (tmp_path / "report.md").is_file() and (tmp_path / "gate.json").is_file()
    first = {path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()}
    module.command_decision(arguments)
    assert first == {
        path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()
    }


def test_top_census_orchestrates_exact_114_by_2_without_processes(tmp_path, monkeypatch):
    module = load_runner("s10r4_runner_census_top")
    rows = []
    for index in range(114):
        raw_config = {"DepthU": 32, "SyntheticOrdinal": index}
        rows.append(
            {
                "registry_index": index,
                "config_hash": canonical_sha256(raw_config),
                "raw_config": raw_config,
            }
        )
    frame = tmp_path / "frame.json"
    atomic_write_json(frame, {"rows": rows})
    monkeypatch.setattr(module, "FRAME_PATH", frame)
    monkeypatch.setattr(module, "CODEGEN_ROOT", tmp_path / "codegen")
    for name, path in {
        "MAPPING_ROOT": tmp_path / "mapping",
        "NATIVE_ROOT": tmp_path / "native",
        "GPU_ROOT": tmp_path / "gpu",
        "REPRODUCTION_ROOT": tmp_path / "reproduction",
        "CLASSIFICATION_PATH": tmp_path / "classification.json",
        "SELECTION_PATH": tmp_path / "selection.json",
        "MAPPING_CORPUS_PATH": tmp_path / "mapping-corpus.json",
        "CONFORMANCE_PATH": tmp_path / "conformance.json",
        "ENVIRONMENT_PATH": tmp_path / "environment.json",
        "CORRECTNESS_PATH": tmp_path / "correctness.json",
        "NOISE_PATH": tmp_path / "noise.json",
        "DECISION_PATH": tmp_path / "decision.json",
        "BLOCKER_PATH": tmp_path / "blocker.json",
        "GATE_RECORD_PATH": tmp_path / "gate.json",
        "REPORT_PATH": tmp_path / "report.md",
        "LOCK_PATH": tmp_path / "effective-lock.json",
    }.items():
        monkeypatch.setattr(module, name, path)
    atomic_write_json(module.LOCK_PATH, {"synthetic_lock": True})
    arguments_a = install_actual_admission(module, monkeypatch, "census", pass_id="A")
    monkeypatch.setattr(module, "_print", lambda _: None)
    launches = []

    def run_logged(argv, cwd, _environment, stdout, stderr, _timeout):
        request = load_json(cwd / "request.json")
        artifact_root = Path(request["artifact_root"])
        artifact_root.mkdir()
        native = census_result(True, request["config_hash"])
        inventory = write_census_artifacts(artifact_root, native)
        native["stable_input_classification"] = "native_membership_success"
        document = {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": "census_child",
            "pass_id": request["pass_id"],
            "registry_index": request["registry_index"],
            "config_hash": request["config_hash"],
            "input_digest": request["input_digest"],
            "cwd": request["cwd"],
            "argv": argv,
            "environment": request["environment"],
            "effective_lock_digest": request["effective_lock_digest"],
            "outputs": native,
            "artifact_inventory": inventory,
        }
        finalize_child(
            cwd / "result.json",
            document,
            {
                "document_kind": "census_child",
                "pass_id": request["pass_id"],
                "registry_index": request["registry_index"],
                "config_hash": request["config_hash"],
            },
        )
        stdout.write_bytes(b"stdout\n")
        stderr.write_bytes(b"")
        launches.append((request["pass_id"], request["registry_index"]))
        return 0, {
            "wall_seconds": 1.0,
            "child_cpu_seconds": 0.5,
            "new_child_tree_bytes": 1,
            "measurement_semantics": "parent_monotonic_wall_rusage_children_and_child_tree_bytes",
        }

    monkeypatch.setattr(module, "_run_logged_observed", run_logged)
    module.command_census(arguments_a)
    reforecast = load_json(tmp_path / "codegen/resource-reforecast.json")
    assert reforecast["terminal_child_count"] == 3
    assert reforecast["projected_full_census"]["wall_seconds"] == 228.0
    arguments_b = install_actual_admission(module, monkeypatch, "census", pass_id="B")
    module.command_census(arguments_b)
    assert len(launches) == 228
    assert launches[0] == ("A", 0) and launches[-1] == ("B", 113)


def test_top_classify_select_and_mapping_orchestrate_mocked_branches(tmp_path, monkeypatch):
    module = load_runner("s10r4_runner_classify_mapping_top")
    state = _stage_state(
        census_a_count=114, census_b_count=114, resource_reforecast=True,
    )
    install_synthetic_projector_state(module, monkeypatch, tmp_path / "stage", state)
    rows = [
        {
            "registry_index": index,
            "config_hash": f"h{index:03d}",
            "raw_config": {"DepthU": 32},
            "candidate_atom_ids_in_config": ["atom"],
            "stream_rank": 0,
            "conditional_priority_rank": 0,
            "chunk_index": 0,
            "draw_index": index,
        }
        for index in range(114)
    ]
    frame_path = tmp_path / "frame.json"
    atomic_write_json(frame_path, {"rows": rows, "registry_digest": "a" * 64})
    monkeypatch.setattr(module, "FRAME_PATH", frame_path)
    monkeypatch.setattr(module, "CLASSIFICATION_PATH", tmp_path / "classification.json")
    monkeypatch.setattr(module, "SELECTION_PATH", tmp_path / "selection.json")
    monkeypatch.setattr(module, "MAPPING_ROOT", tmp_path / "mapping")
    monkeypatch.setattr(module, "MAPPING_CORPUS_PATH", tmp_path / "mapping-corpus.json")
    classify_arguments = install_actual_admission(module, monkeypatch, "classify-select")
    monkeypatch.setattr(module, "_print", lambda _: None)
    terminal = [
        {
            "config_hash": row["config_hash"],
            "completion_digest": f"{index:064x}",
            "outputs": census_result(True),
        }
        for index, row in enumerate(rows)
    ]
    monkeypatch.setattr(module, "_census_results", lambda _pass_id: copy.deepcopy(terminal))
    real_load = module.load_json

    def load(path):
        if str(path).endswith("s10r3-candidate-atom-registry.json"):
            return {"rows": [{"atom_id": "atom"}]}
        return real_load(path)

    monkeypatch.setattr(module, "load_json", load)
    module.command_classify_select(classify_arguments)
    monkeypatch.setattr(
        module,
        "_load_payload",
        lambda path, kind: load_json(path)["payload"],
    )
    selection = module._load_payload(module.SELECTION_PATH, "operational_selection")
    assert selection["status"] == "PASS" and selection["k"] == 10

    selected_hashes = selection["selected_hashes"]
    raw_a = mapping_rows("A", selected_hashes)
    raw_b = mapping_rows("B", selected_hashes)
    calls = []

    def terminal_mapping(pass_id, _selected, _lock_digest, existing_only=False):
        calls.append((pass_id, existing_only))
        return "mapping_pass_PASS", copy.deepcopy(raw_a if pass_id == "A" else raw_b), []

    monkeypatch.setattr(module, "_mapping_pass_terminal", terminal_mapping)
    mapping_a_arguments = install_actual_admission(module, monkeypatch, "mapping", pass_id="A")
    module.command_mapping(mapping_a_arguments)
    state["mapping_a_status"] = "PASS"
    mapping_b_arguments = install_actual_admission(module, monkeypatch, "mapping", pass_id="B")
    module.command_mapping(mapping_b_arguments)
    corpus = module._load_payload(module.MAPPING_CORPUS_PATH, "mapping_corpus")
    assert corpus["status"] == "PASS" and corpus["rows_per_pass"] == 30
    assert calls == [("A", False), ("A", True), ("B", False)]


def test_top_native_and_gpu_use_actual_formal_admission(tmp_path, monkeypatch):
    module = load_runner("s10r4_runner_native_gpu_reproduction_top")
    install_synthetic_projector_state(
        module,
        monkeypatch,
        tmp_path / "stage",
        _stage_state(
            census_a_count=114, census_b_count=114, resource_reforecast=True,
            classification=True, selection_status="PASS", mapping_a_status="PASS",
            mapping_b_status="PASS", mapping_corpus_status="PASS",
        ),
    )
    module.BUILD_ROOT = tmp_path / "build"
    module.NATIVE_ROOT = tmp_path / "native"
    module.CONFORMANCE_PATH = tmp_path / "conformance.json"
    module.ENVIRONMENT_PATH = tmp_path / "environment.json"
    module.BLOCKER_PATH = tmp_path / "blocker.json"
    module.GPU_ROOT = tmp_path / "gpu"
    module.REPRODUCTION_ROOT = tmp_path / "reproduction"
    module.DECISION_PATH = tmp_path / "decision.json"
    module.FRAME_PATH = tmp_path / "frame.json"
    module.RAW_ROOT = tmp_path / "raw"
    atomic_write_json(module.FRAME_PATH, {"rows": []})
    lock = {"source_realization": {"native_build_products": []}}
    native_arguments = install_actual_admission(
        module, monkeypatch, "native-conformance", lock=lock
    )
    monkeypatch.setattr(module, "_print", lambda _: None)
    monkeypatch.setattr(module, "load_contract", lambda: {})
    monkeypatch.setattr(
        module,
        "_load_payload",
        lambda _path, kind: {
            "codegen_classification": {},
            "operational_selection": {"status": "PASS", "selected_hashes": [], "k": 10},
            "mapping_corpus": {"status": "PASS"},
            "sentinel_conformance": {"status": "PASS"},
        }[kind],
    )
    monkeypatch.setattr(
        module,
        "run_native_conformance",
        lambda **_: module.seal_digest(
            {
                "schema_version": 1,
                "checkpoint_id": "S10R4",
                "document_kind": "sentinel_conformance",
                "status": "PASS",
                "effective_lock_digest": "a" * 64,
                "input_binding_digest": "b" * 64,
                "argv": ["binary", "--input", "input", "--output", "output"],
                "environment": FIXED_ENVIRONMENT,
                "binary": {},
                "transcript": {},
                "stdout_sha256": "c" * 64,
                "stderr_sha256": "d" * 64,
                "fault_substitutions": {},
            }
        ),
    )
    module.command_native_conformance(native_arguments)
    assert module._load_payload(module.CONFORMANCE_PATH, "sentinel_conformance")["status"] == "PASS"

    monkeypatch.setattr(
        module,
        "_gpu_snapshot",
        lambda _root, _ordinal: {
            "allocation_rows": [gpu(2), gpu(1)],
            "pid_rows": {"1": [], "2": []},
            "allocation_stdout_sha256": "a" * 64,
            "process_stdout_sha256": "b" * 64,
        },
    )
    gpu_arguments = install_actual_admission(module, monkeypatch, "gpu-environment", lock=lock)
    module.command_gpu_environment(gpu_arguments)
    environment = load_json(module.ENVIRONMENT_PATH)["payload"]
    assert environment["selected_gpu"]["physical_visible_index"] == 1



def test_lock_commands_are_mock_orchestrated_without_creating_a_lock(tmp_path, monkeypatch):
    module = load_runner("s10r4_runner_lock_commands")
    output = tmp_path / "lock.json"
    monkeypatch.setattr(module, "LOCK_PATH", output)
    monkeypatch.setattr(module, "_relative_argument", lambda value, expected, **_: expected)
    monkeypatch.setattr(module, "verify_prelabel", lambda **_: {"status": "PRELABEL_VERIFIED"})
    monkeypatch.setattr(
        module,
        "construct_effective_lock",
        lambda **_: {"lifecycle": {"pre_audit": {"lock_state": "absent"}}},
    )
    monkeypatch.setattr(module, "raw_sha256", lambda _: "a" * 64)
    monkeypatch.setattr(module, "_print", lambda _: None)
    module.command_build_lock(SimpleNamespace(output=output.as_posix()))
    assert not output.exists()
    monkeypatch.setattr(
        module,
        "verify_committed_effective_lock",
        lambda _: {"self_identity": {"canonical_self_sha256": "s" * 64}},
    )
    module.command_verify_lock(SimpleNamespace(lock=output.as_posix()))


@pytest.mark.parametrize(
    "command,kind,handler_name,returncode",
    [
        ("_census-child", "census_request", "execute_census_worker", 0),
        ("_mapping-child", "mapping_request", "execute_mapping_worker", 23),
        ("_correctness-build-child", "correctness_build_request", "execute_correctness_build_worker", 32),
    ],
)
def test_internal_worker_command_dispatches_exact_mocked_handler(
    tmp_path, monkeypatch, command, kind, handler_name, returncode
):
    module = load_runner(f"s10r4_runner_internal_{command}")
    environment = {**FIXED_ENVIRONMENT, "PYTHONPATH": module.WORKER_PYTHONPATH}
    selected = gpu(0)
    if command == "_correctness-build-child":
        environment["ROCR_VISIBLE_DEVICES"] = "0"
    request = {
        "checkpoint_id": "S10R4",
        "document_kind": kind,
        "cwd": tmp_path.as_posix(),
        "environment": environment,
        "effective_lock_digest": "a" * 64,
    }
    if command == "_correctness-build-child":
        request["selected_gpu"] = selected
    request["input_digest"] = canonical_sha256(request)
    request_path = tmp_path / "request.json"
    atomic_write_json(request_path, request)
    result_path = tmp_path / "result.json"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module.os, "environ", environment)
    monkeypatch.setattr(module, handler_name, lambda _request, _result: returncode)
    monkeypatch.setattr(module, "_admit_current_argv", lambda _arguments: None)
    assert module.command_internal_worker(
        SimpleNamespace(command=command, request=request_path.as_posix(), result=result_path.as_posix())
    ) == returncode


def test_toolchain_wrapper_and_strace_manifest_equality_is_mocked(tmp_path, monkeypatch):
    from s10r4.correctness import _ToolchainCallRecorder

    module = load_runner("s10r4_runner_strace_wrapper_equality")
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    monkeypatch.chdir(attempt)
    boundaries = []
    recorder = _ToolchainCallRecorder(lambda: boundaries.append("sealed"))
    completed = recorder.run(["/usr/bin/true", "--synthetic"], env=FIXED_ENVIRONMENT)
    completed_again = recorder.run(["/usr/bin/true", "--synthetic"], env=FIXED_ENVIRONMENT)
    assert completed.returncode == completed_again.returncode == 0 and boundaries == ["sealed", "sealed"]
    request = attempt / "build-request.json"
    result = attempt / "build-result.json"
    expected_root = [
        sys.executable,
        (PROTOCOL_ROOT / "run_s10r4_entry.py").as_posix(),
        "_correctness-build-child",
        "--request",
        request.as_posix(),
        "--result",
        result.as_posix(),
    ]
    tool = recorder.records[0]
    trace = attempt / "build-execve.log"
    trace.write_text(
        f"100 execve({sys.executable!r}, {expected_root!r}, 0x0) = 0\n"
        f"101 execve({tool['requested_executable']!r}, {tool['argv']!r}, 0x0) = 0\n"
        f"102 execve({tool['requested_executable']!r}, {tool['argv']!r}, 0x0) = 0\n",
        encoding="utf-8",
    )
    lock = {
        "source_realization": {
            "llvm_executable_closure": [
                {
                    "present": True,
                    "resolved_path": tool["resolved_executable"],
                    "sha256": tool["executable_sha256"],
                }
            ]
        }
    }
    root_executable = Path(sys.executable).resolve(strict=True)
    root_binding = {
        "command_kind": "correctness_build_child",
        "requested_executable": sys.executable,
        "resolved_executable": root_executable.as_posix(),
        "executable_sha256": raw_sha256(root_executable),
        "argv": expected_root,
        "cwd": attempt.as_posix(),
        "environment": FIXED_ENVIRONMENT,
    }
    manifest = module._parse_strace_execve(trace, lock, expected_root, root_binding, recorder.records)
    assert manifest["wrapper_call_count"] == 2
    assert [row["occurrence_rank"] for row in manifest["records"][1:]] == [0, 1]
    assert all(row["association_kind"] == "toolchain_wrapper" for row in manifest["records"][1:])
    assert all(not ({"parent_pid", "cwd", "environment"} & set(row)) for row in manifest["records"])
