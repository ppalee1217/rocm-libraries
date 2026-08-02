#!/usr/bin/env python3
# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Strict CLI for the S10R4 exact-frame operational-entry protocol."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import os
import re
import resource
import stat
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[5]
sys.path.insert(0, str(SCRIPT_PATH.parent))

from s10r4.census import (
    census_request,
    execute_census_worker,
    materialize_pinned_source,
    resolve_geko_commit,
    source_identity,
    stable_classify,
    verify_pinned_source,
)
from s10r4.conformance import (
    build_native_fixture,
    rederive_native_conformance,
    run_native_conformance,
    validate_native_fixture,
    validate_native_transcript,
)
from s10r4.contract import (
    COMMAND_TEMPLATES,
    FIXED_ENVIRONMENT,
    S10R4Error,
    atomic_write_bytes,
    atomic_write_json,
    canonical_json,
    canonical_sha256,
    construct_effective_lock,
    document_record,
    ensure_prelabel_absence,
    load_contract,
    load_json,
    materialize_command_template,
    ordinary_file_records,
    raw_sha256,
    seal_digest,
    validate_sealed_digest,
    validate_command_template,
    validate_document_schema,
    validate_effective_lock,
    validate_environment,
    validate_phase1,
    verify_committed_effective_lock,
)
from s10r4.correctness import (
    CorrectnessAttempt,
    aggregate_noise,
    anchor_indices,
    correctness_build_request,
    decide_client_result,
    decide_correctness_attempts,
    execute_correctness_build_worker,
    parse_single_result_csv,
    rewrite_results_file,
    select_gpu,
    validate_snapshot_pair,
    verify_gpu_continuity,
)
from s10r4.frame import replay_exact_frame, validate_exact_frame_registry
from s10r4.ledger import (
    census_expectations,
    completion_digest,
    exclusive_scope,
    finalize_child,
    finalize_process_completion,
    scan_exact_children,
    validate_child,
    validate_process_completion,
)
from s10r4.mapping import (
    MappingAttempt,
    build_size_registry,
    compare_mapping_passes,
    decide_mapping_attempts,
    execute_mapping_worker,
    mapping_request,
    validate_mapping_batch,
    validate_size_registry,
)
from s10r4.native_adapter import build_native_products, validate_native_build
from s10r4.selector import deterministic_select, selection_to_document, witness_from_frame_row
from s10r4.state_machine import StageProjection, decide_outcome, project_formal_stage


RUN_ROOT = REPO_ROOT / "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame"
BUILD_ROOT = RUN_ROOT / "artifacts/prelabel-build"
FIXTURE_ROOT = RUN_ROOT / "artifacts/prelabel-fixtures"
FRAME_PATH = REPO_ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r4-exact-frame-registry.json"
SIZE_PATH = REPO_ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r4-size-registry.json"
FIXTURE_PATH = REPO_ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r4-native-fixture.json"
LOCK_PATH = REPO_ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s10r4-stage1-exact-frame-entry-lock.json"
RAW_ROOT = REPO_ROOT / "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/formal-cpu"
CODEGEN_ROOT = RUN_ROOT / "artifacts/formal-codegen"
MAPPING_ROOT = RUN_ROOT / "artifacts/formal-mapping"
NATIVE_ROOT = RUN_ROOT / "artifacts/formal-native"
GPU_ROOT = RUN_ROOT / "artifacts/formal-gpu"
REPRODUCTION_ROOT = RUN_ROOT / "artifacts/reproduction"
MANIFEST_ROOT = REPO_ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests"
EVIDENCE_ROOT = REPO_ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence"
CLASSIFICATION_PATH = MANIFEST_ROOT / "s10r4-codegen-classification.json"
SELECTION_PATH = MANIFEST_ROOT / "s10r4-operational-selection.json"
MAPPING_CORPUS_PATH = MANIFEST_ROOT / "s10r4-mapping-corpus.json"
CONFORMANCE_PATH = MANIFEST_ROOT / "s10r4-sentinel-conformance.json"
ENVIRONMENT_PATH = MANIFEST_ROOT / "s10r4-environment.json"
CORRECTNESS_PATH = EVIDENCE_ROOT / "s10r4-smoke-correctness.json"
NOISE_PATH = EVIDENCE_ROOT / "s10r4-noise-pilot.json"
DECISION_PATH = EVIDENCE_ROOT / "s10r4-decision.json"
BLOCKER_PATH = EVIDENCE_ROOT / "s10r4-operational-blocker.json"
GATE_RECORD_PATH = EVIDENCE_ROOT / "gate-records/s10r4-s1-entry-go-exact-frame.json"
REPORT_PATH = REPO_ROOT / "study_docs/research/ductile-origami-warmstart/reports/staged/s10r4-stage1-exact-frame-entry-report.md"
WORKER_PYTHONPATH = "/src/rocm-libraries/agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame/artifacts/prelabel-build/pinned-source/projects/hipblaslt/tensilelite"
BLOCKER_REASON_CODES = {
    "NO_ELIGIBLE_GPU_MATERIAL_AVAILABILITY",
    "SELECTED_GPU_IDENTITY_UNAVAILABLE",
    "UNSAFE_PLATFORM_STATE",
    "ARTIFACT_PRESERVATION_OR_COMPLETION_IMPOSSIBLE",
}


def _relative_argument(value: str, expected: Path, *, name: str) -> Path:
    candidate = Path(value)
    absolute = candidate if candidate.is_absolute() else Path.cwd() / candidate
    if absolute.resolve(strict=False) != expected.resolve(strict=False):
        raise S10R4Error(f"{name} differs from its exact frozen path")
    return expected


def _require_fixed_runtime() -> None:
    expected_cwd = Path("/src/rocm-libraries")
    if Path.cwd().resolve() != expected_cwd:
        raise S10R4Error("S10R4 command cwd must be /src/rocm-libraries")
    observed = {key: os.environ.get(key) for key in FIXED_ENVIRONMENT}
    if observed != FIXED_ENVIRONMENT:
        raise S10R4Error(f"S10R4 fixed environment mismatch: {observed}")


def _print(value: Any) -> None:
    sys.stdout.buffer.write(canonical_json(value, newline=True))


def command_validate_contract(_: argparse.Namespace) -> None:
    contract = validate_phase1()
    _print(
        {
            "checkpoint_id": "S10R4",
            "contract_id": contract["contract_id"],
            "contract_raw_sha256": raw_sha256(SCRIPT_PATH.parent / "s10r4-stage1-exact-frame-entry-contract.yaml"),
            "formal_outcome_lock_absence": "PASS",
        }
    )


def _prelabel_summary(
    *,
    frame_path: Path,
    size_path: Path,
    fixture_path: Path,
    source: Mapping[str, Any],
    geko: Mapping[str, Any],
    build_root: Path,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        "document_kind": "prelabel_build_summary",
        "outcome_blind": True,
        "frame": document_record(frame_path),
        "sizes": document_record(size_path),
        "native_fixture": document_record(fixture_path),
        "source_identity": dict(source),
        "geko_identity": dict(geko),
        "native_build_manifest": document_record(
            build_root / "native/s10r4-native-build.json"
        ),
        "native_executed": False,
        "formal_evidence_executed": False,
    }


def command_prepare_prelabel(arguments: argparse.Namespace) -> None:
    contract = validate_phase1()
    raw_root = _relative_argument(arguments.raw_root, RAW_ROOT, name="raw root")
    build_root = _relative_argument(arguments.build_root, BUILD_ROOT, name="build root")
    fixture_root = _relative_argument(arguments.fixture_root, FIXTURE_ROOT, name="fixture root")
    frame_path = _relative_argument(arguments.frame_registry, FRAME_PATH, name="frame registry")
    size_path = _relative_argument(arguments.size_registry, SIZE_PATH, name="size registry")
    fixture_path = _relative_argument(arguments.native_fixture, FIXTURE_PATH, name="native fixture")

    initial_frame = replay_exact_frame(raw_root)
    size_registry = build_size_registry()
    native_fixture = build_native_fixture(contract)
    validate_exact_frame_registry(initial_frame)
    validate_size_registry(size_registry)
    validate_native_fixture(native_fixture, contract)
    atomic_write_json(frame_path, initial_frame)
    atomic_write_json(size_path, size_registry)
    atomic_write_json(fixture_path, native_fixture)

    source_identity_record = materialize_pinned_source(build_root)
    geko_identity = resolve_geko_commit(build_root)
    native_manifest = build_native_products(
        build_root,
        build_root / "pinned-source",
        SCRIPT_PATH.parent / "s10r4/native_formocast_runtime_adapter.cpp",
    )

    repeated_frame = replay_exact_frame(raw_root)
    if canonical_json(repeated_frame, newline=True) != canonical_json(initial_frame, newline=True):
        raise S10R4Error("second unchanged raw replay did not produce byte-identical registry bytes")
    verify_pinned_source(build_root / "pinned-source")
    validate_native_build(
        native_manifest,
        build_root,
        build_root / "pinned-source",
        SCRIPT_PATH.parent / "s10r4/native_formocast_runtime_adapter.cpp",
    )
    fixture_root.mkdir(parents=True, exist_ok=True)
    summary = _prelabel_summary(
        frame_path=frame_path,
        size_path=size_path,
        fixture_path=fixture_path,
        source=source_identity_record,
        geko=geko_identity,
        build_root=build_root,
    )
    atomic_write_json(fixture_root / "prelabel-build-summary.json", summary)
    ensure_prelabel_absence(contract)
    _print(
        {
            "checkpoint_id": "S10R4",
            "status": "PRELABEL_PREPARED",
            "ledger_events": initial_frame["ledger_event_count"],
            "raw_children": initial_frame["raw_child_record_count"],
            "nominal_draws": initial_frame["nominal_draw_count"],
            "accepted_occurrences": initial_frame["accepted_occurrence_count"],
            "distinct_config_hashes": initial_frame["distinct_config_hash_count"],
            "registry_rows": initial_frame["row_count"],
            "size_rows": size_registry["row_count"],
            "fixture_payload_sha256": native_fixture["fixture_digest"],
            "native_executed": False,
        }
    )


def verify_prelabel(*, effective_lock_present: bool = False) -> dict[str, Any]:
    contract = load_contract() if effective_lock_present else validate_phase1()
    frame = load_json(FRAME_PATH)
    sizes = load_json(SIZE_PATH)
    fixture = load_json(FIXTURE_PATH)
    validate_exact_frame_registry(frame)
    validate_size_registry(sizes)
    validate_native_fixture(fixture, contract)
    replay = replay_exact_frame(RAW_ROOT)
    if canonical_json(frame, newline=True) != canonical_json(replay, newline=True):
        raise S10R4Error("durable exact-frame registry differs from fresh direct replay")
    pinned_source = BUILD_ROOT / "pinned-source"
    verify_pinned_source(pinned_source)
    current_source_identity = source_identity(pinned_source)
    current_geko_identity = resolve_geko_commit(BUILD_ROOT)
    native_manifest = load_json(BUILD_ROOT / "native/s10r4-native-build.json")
    validate_native_build(
        native_manifest,
        BUILD_ROOT,
        pinned_source,
        SCRIPT_PATH.parent / "s10r4/native_formocast_runtime_adapter.cpp",
    )
    summary = load_json(FIXTURE_ROOT / "prelabel-build-summary.json")
    expected_summary = _prelabel_summary(
        frame_path=FRAME_PATH,
        size_path=SIZE_PATH,
        fixture_path=FIXTURE_PATH,
        source=current_source_identity,
        geko=current_geko_identity,
        build_root=BUILD_ROOT,
    )
    if summary != expected_summary:
        raise S10R4Error("prelabel summary differs from complete current source/product validation")
    if not effective_lock_present:
        ensure_prelabel_absence(contract)
    return {
        "checkpoint_id": "S10R4",
        "status": "PRELABEL_VERIFIED",
        "ledger_events": frame["ledger_event_count"],
        "raw_children": frame["raw_child_record_count"],
        "nominal_draws": frame["nominal_draw_count"],
        "accepted_occurrences": frame["accepted_occurrence_count"],
        "distinct_config_hashes": frame["distinct_config_hash_count"],
        "registry_rows": frame["row_count"],
        "size_rows": sizes["row_count"],
        "fixture_payload_sha256": fixture["fixture_digest"],
        "second_replay_byte_identical": True,
        "native_executed": False,
    }


def command_verify_prelabel(_: argparse.Namespace) -> None:
    _print(verify_prelabel())


def command_build_lock(arguments: argparse.Namespace) -> None:
    output = _relative_argument(arguments.output, LOCK_PATH, name="effective lock output")
    verify_prelabel()
    lock = construct_effective_lock(
        output=output,
        plan_a_path=RUN_ROOT / "gates/s10r4/plan_a.md",
        plan_b_path=RUN_ROOT / "gates/s10r4/plan_b.md",
        plan_b_freeze_path=RUN_ROOT / "gates/s10r4/plan_b.freeze.json",
        audit_verdict_path=RUN_ROOT / "gates/s10r4/audit-verdict.json",
        native_build_manifest=BUILD_ROOT / "native/s10r4-native-build.json",
    )
    _print(
        {
            "checkpoint_id": "S10R4",
            "lock_state": lock["lifecycle"]["pre_audit"]["lock_state"],
            "activation_required": True,
            "lock_raw_sha256": raw_sha256(output),
        }
    )


def command_verify_lock(arguments: argparse.Namespace) -> None:
    path = _relative_argument(arguments.lock, LOCK_PATH, name="effective lock")
    lock = verify_committed_effective_lock(path)
    _print({"checkpoint_id": "S10R4", "status": "LOCKED_READY", "self_sha256": lock["self_identity"]["canonical_self_sha256"]})


def _command_template_identity(arguments: argparse.Namespace) -> tuple[str, dict[str, str]]:
    command_id = {
        "validate-contract": "validate_contract",
        "prepare-prelabel": "prepare_prelabel",
        "verify-prelabel": "verify_prelabel",
        "_census-child": "census_child",
        "_mapping-child": "mapping_child",
        "_correctness-build-child": "correctness_build_child",
    }.get(arguments.command, arguments.command)
    substitutions: dict[str, str] = {}
    if command_id in ("census", "mapping"):
        substitutions["pass_id"] = arguments.pass_id
    elif command_id == "census_child":
        substitutions["child_root"] = Path(arguments.request).resolve(strict=False).parent.as_posix()
    elif command_id in ("mapping_child", "correctness_build_child"):
        substitutions["attempt_root"] = Path(arguments.request).resolve(strict=False).parent.as_posix()
    return command_id, substitutions


def _admit_current_argv(arguments: argparse.Namespace) -> None:
    command_id, substitutions = _command_template_identity(arguments)
    validate_command_template(command_id, [sys.executable, *sys.argv], substitutions)


def _formal_admission(arguments: argparse.Namespace) -> tuple[dict[str, Any], str]:
    path = _relative_argument(arguments.lock, LOCK_PATH, name="effective lock")
    lock = verify_committed_effective_lock(path)
    validate_effective_lock(lock)
    _admit_current_argv(arguments)
    verify_prelabel(effective_lock_present=True)
    lock_digest = raw_sha256(path)
    projection = _project_reached_formal_stage(lock_digest)
    is_current = projection.command_id is not None and arguments.command == projection.command_id
    is_resume = (
        projection.resume_command_id is not None
        and arguments.command == projection.resume_command_id
    )
    admitted = is_current or is_resume
    if not admitted:
        raise S10R4Error(
            f"formal command differs from artifact-derived stage: "
            f"command={arguments.command} stage={projection.stage_id} expected={projection.command_id}"
        )
    expected_pass = projection.pass_id if is_current else projection.resume_pass_id
    if expected_pass is not None and getattr(arguments, "pass_id", None) != expected_pass:
        raise S10R4Error("formal pass differs from artifact-derived stage")
    return lock, lock_digest


def _worker_environment(*, card_index: int | None = None) -> dict[str, str]:
    environment = {**FIXED_ENVIRONMENT, "PYTHONPATH": WORKER_PYTHONPATH}
    if card_index is not None:
        environment["ROCR_VISIBLE_DEVICES"] = str(card_index)
    return environment


def _run_logged(
    argv: list[str],
    cwd: Path,
    environment: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
    timeout_s: int,
) -> int:
    return _run_logged_observed(
        argv, cwd, environment, stdout_path, stderr_path, timeout_s
    )[0]


def _run_logged_observed(
    argv: list[str],
    cwd: Path,
    environment: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
    timeout_s: int,
) -> tuple[int, dict[str, Any]]:
    if stdout_path.exists() or stderr_path.exists():
        raise S10R4Error(f"refusing to overwrite formal process logs: {stdout_path}")
    stdout_path.parent.mkdir(parents=True, exist_ok=True)

    def child_tree_bytes() -> int:
        total = 0
        for root, directories, files in os.walk(cwd, followlinks=False):
            for name in [*directories, *files]:
                candidate = Path(root) / name
                info = candidate.stat(follow_symlinks=False)
                if stat.S_ISREG(info.st_mode):
                    total += info.st_size
        return total

    storage_start = child_tree_bytes()
    wall_start_ns = time.monotonic_ns()
    usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        try:
            completed = subprocess.run(
                argv,
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise S10R4Error(f"formal subprocess timed out with preserved logs: {argv[0]}") from exc
        except OSError as exc:
            raise S10R4Error(f"formal subprocess could not be launched: {argv[0]}") from exc
    if completed.returncode < 0:
        raise S10R4Error(f"formal subprocess terminated by signal: {completed.returncode}")
    usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
    storage_bytes = child_tree_bytes() - storage_start
    if storage_bytes < 0:
        raise S10R4Error("formal subprocess reduced its child tree during resource observation")
    observation = {
        "wall_seconds": (time.monotonic_ns() - wall_start_ns) / 1_000_000_000,
        "child_cpu_seconds": (
            usage_end.ru_utime + usage_end.ru_stime - usage_start.ru_utime - usage_start.ru_stime
        ),
        "new_child_tree_bytes": storage_bytes,
        "measurement_semantics": "parent_monotonic_wall_rusage_children_and_child_tree_bytes",
    }
    return completed.returncode, observation


def _formal_document(kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    document = seal_digest(
        {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": kind,
            "payload": dict(payload),
        }
    )
    validate_document_schema(document)
    return document


def _write_formal(path: Path, kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    document = _formal_document(kind, payload)
    atomic_write_json(path, document)
    return document


def _direct_evidence_record(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    try:
        relative = resolved.relative_to(REPO_ROOT.resolve(strict=True)).as_posix()
    except ValueError as exc:
        raise S10R4Error("operational blocker evidence is outside the repository") from exc
    info = resolved.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise S10R4Error("operational blocker evidence is not one ordinary file")
    return {
        "path": relative,
        "mode": stat.S_IMODE(info.st_mode),
        "size_bytes": info.st_size,
        "raw_sha256": raw_sha256(resolved),
    }


def write_operational_blocker(
    *,
    producer_command_id: str,
    reason_code: str,
    evidence_paths: Sequence[Path],
    pre_block_projection: StageProjection,
    lock_digest: str,
) -> dict[str, Any]:
    """Sole internal creation route for a terminal material operational blocker."""
    if reason_code not in BLOCKER_REASON_CODES:
        raise S10R4Error("unknown or non-material operational blocker reason code")
    if (
        producer_command_id != pre_block_projection.command_id
        or producer_command_id not in {
            "census", "mapping", "native-conformance", "gpu-environment", "correctness", "noise"
        }
        or pre_block_projection.blocker_present
    ):
        raise S10R4Error("operational blocker producer is not the currently admitted atomic boundary")
    if not evidence_paths or len({path.resolve(strict=True) for path in evidence_paths}) != len(evidence_paths):
        raise S10R4Error("operational blocker direct evidence is empty or duplicated")
    records = [_direct_evidence_record(path) for path in evidence_paths]
    payload = {
        "status": "BLOCKED",
        "scientific_outcome": "not_evaluated",
        "criterion": "BLOCKED",
        "failure_id": None,
        "edge": None,
        "reached_stage": pre_block_projection.stage_id,
        "producer_command_id": producer_command_id,
        "reason_code": reason_code,
        "direct_evidence": records,
        "direct_evidence_projection_sha256": canonical_sha256(records),
        "pre_block_stage_projection": asdict(pre_block_projection),
        "effective_lock_digest": lock_digest,
    }
    document = _formal_document("operational_blocker", payload)
    atomic_write_json(BLOCKER_PATH, document)
    return document


def _validate_existing_operational_blocker(lock_digest: str, producer_command_id: str) -> dict[str, Any]:
    payload = _load_payload(BLOCKER_PATH, "operational_blocker")
    if (
        payload["producer_command_id"] != producer_command_id
        or payload["reason_code"] not in BLOCKER_REASON_CODES
        or payload["effective_lock_digest"] != lock_digest
    ):
        raise S10R4Error("existing operational blocker producer/reason/lock identity mismatch")
    records = payload["direct_evidence"]
    current = [_direct_evidence_record(REPO_ROOT / row["path"]) for row in records]
    if current != records or payload["direct_evidence_projection_sha256"] != canonical_sha256(records):
        raise S10R4Error("existing operational blocker direct evidence drift")
    expected_pre_block = _project_reached_formal_stage(lock_digest, ignore_blocker=True)
    if payload["pre_block_stage_projection"] != asdict(expected_pre_block):
        raise S10R4Error("existing operational blocker pre-block stage projection drift")
    if payload["reached_stage"] != expected_pre_block.stage_id or producer_command_id != expected_pre_block.command_id:
        raise S10R4Error("existing operational blocker no longer belongs to its reached stage")
    expected = _formal_document("operational_blocker", payload)
    if expected != load_json(BLOCKER_PATH):
        raise S10R4Error("existing operational blocker is not byte-identically rederived")
    return payload


def _resume_existing_operational_blocker(
    lock_digest: str, producer_command_id: str
) -> bool:
    if not BLOCKER_PATH.exists():
        return False
    _validate_existing_operational_blocker(lock_digest, producer_command_id)
    _print(
        {
            "checkpoint_id": "S10R4",
            "status": "BLOCKED",
            "document_digest": load_json(BLOCKER_PATH)["document_digest"],
        }
    )
    return True


def _load_payload(path: Path, kind: str) -> dict[str, Any]:
    document = load_json(path)
    validate_document_schema(document)
    if document.get("document_kind") != kind:
        raise S10R4Error(f"formal prerequisite kind mismatch: {path}")
    if canonical_sha256({key: value for key, value in document.items() if key != "document_digest"}) != document.get("document_digest"):
        raise S10R4Error(f"formal prerequisite digest mismatch: {path}")
    payload = document.get("payload")
    if not isinstance(payload, dict):
        raise S10R4Error(f"formal prerequisite payload malformed: {path}")
    return payload


def _exact_census_prefix(pass_id: str) -> int:
    frame = load_json(FRAME_PATH)
    expected = census_expectations(CODEGEN_ROOT, pass_id, frame["rows"])
    root = CODEGEN_ROOT / f"pass-{pass_id}"
    if not root.exists():
        return 0
    if not root.is_dir() or root.is_symlink():
        raise S10R4Error(f"census pass {pass_id} scope is not one directory")
    expected_directories = [path.parent.name for path, _ in expected]
    observed_directories = sorted(
        [path.name for path in root.iterdir() if path.name != ".s10r4-writer.lock"],
        key=os.fsencode,
    )
    if any(not (root / name).is_dir() for name in observed_directories):
        raise S10R4Error(f"census pass {pass_id} scope contains an unknown top-level file")
    count = len(observed_directories)
    if observed_directories != expected_directories[:count]:
        raise S10R4Error(f"census pass {pass_id} is not an exact registry-order prefix")
    if count:
        scan_exact_children(root, expected[:count])
    return count


def _exact_mapping_prefix(pass_id: str, selected: list[dict[str, Any]], lock_digest: str) -> str | None:
    root = MAPPING_ROOT / f"pass-{pass_id}"
    if not root.exists():
        return None
    if not root.is_dir() or root.is_symlink():
        raise S10R4Error(f"mapping pass {pass_id} scope is not one directory")
    observed = sorted(
        [path.name for path in root.iterdir() if path.name != ".s10r4-writer.lock"],
        key=os.fsencode,
    )
    if observed not in (["attempt-01"], ["attempt-01", "attempt-02"]):
        raise S10R4Error(f"mapping pass {pass_id} is not an exact one/two-attempt prefix")
    for name in observed:
        attempt_root = root / name
        if not attempt_root.is_dir() or not (attempt_root / "request.json").is_file() or not (attempt_root / "result.json").is_file():
            raise S10R4Error(f"mapping pass {pass_id} contains a partial attempt")
    terminal, _, children = _mapping_pass_terminal(pass_id, selected, lock_digest, existing_only=True)
    expected_count = 1 if children[0]["outputs"]["status"] == "success" else 2
    if len(observed) != expected_count:
        raise S10R4Error(f"mapping pass {pass_id} attempt count differs from its terminal signature")
    return "PASS" if terminal == "mapping_pass_PASS" else "NEGATIVE_MAPPING"


def _exact_correctness_prefix(selection: Mapping[str, Any]) -> int:
    root = GPU_ROOT / "correctness"
    if not root.exists():
        return 0
    if not root.is_dir() or root.is_symlink():
        raise S10R4Error("correctness scope is not one directory")
    expected = [
        f"{anchor:02d}-{size_id}"
        for anchor in anchor_indices(selection["k"])
        for size_id in ("size-00", "size-01", "size-02")
    ]
    observed = sorted(
        [path.name for path in root.iterdir() if path.name != ".s10r4-writer.lock"],
        key=os.fsencode,
    )
    if observed != expected[:len(observed)]:
        raise S10R4Error("correctness cells are not the exact anchor/size-order prefix")
    for ordinal, name in enumerate(observed):
        cell_root = root / name
        attempts = sorted(
            [path.name for path in cell_root.iterdir() if path.name != ".s10r4-writer.lock"],
            key=os.fsencode,
        )
        if attempts not in (["attempt-01"], ["attempt-01", "attempt-02"]):
            raise S10R4Error("correctness cell is not an exact terminal attempt prefix")
        documents = []
        for attempt, attempt_name in enumerate(attempts, 1):
            attempt_path = cell_root / attempt_name / "attempt.json"
            if not attempt_path.is_file():
                raise S10R4Error("correctness cell contains a partial attempt")
            document = load_json(attempt_path)
            validate_document_schema(document)
            validate_sealed_digest(document)
            anchor_text, size_id = name.split("-size-", 1)
            if (
                document.get("document_kind") != "correctness_attempt"
                or document.get("anchor_index") != int(anchor_text)
                or document.get("size_id") != f"size-{size_id}"
                or document.get("attempt") != attempt
            ):
                raise S10R4Error("correctness attempt identity differs from its exact slot")
            documents.append(document)
        first = _correctness_attempt_value(documents[0])
        expected_attempts = 1 if first.status == "PASS" else 2
        if len(documents) != expected_attempts:
            raise S10R4Error("correctness cell lacks its exact terminal attempt count")
        decide_correctness_attempts([_correctness_attempt_value(document) for document in documents])
        if ordinal + 1 < len(observed) and documents[-1]["status"] != "PASS":
            raise S10R4Error("a terminal negative correctness cell has unreachable later cells")
    return len(observed)


def _exact_noise_prefix(selection: Mapping[str, Any]) -> int:
    root = GPU_ROOT / "noise"
    if not root.exists():
        return 0
    if not root.is_dir() or root.is_symlink():
        raise S10R4Error("noise scope is not one directory")
    expected_groups = [
        f"{anchor:02d}-{size_id}"
        for anchor in anchor_indices(selection["k"])
        for size_id in ("size-00", "size-01", "size-02")
    ]
    observed_groups = sorted(
        [path.name for path in root.iterdir() if path.name != ".s10r4-writer.lock"],
        key=os.fsencode,
    )
    if observed_groups != expected_groups[:len(observed_groups)]:
        raise S10R4Error("noise groups are not the exact anchor/size-order prefix")
    total = 0
    incomplete_seen = False
    for group in observed_groups:
        repeat_root = root / group
        observed_repeats = sorted(
            [path.name for path in repeat_root.iterdir() if path.name != ".s10r4-writer.lock"],
            key=os.fsencode,
        )
        expected_repeats = [f"repeat-{repeat:02d}" for repeat in range(1, 8)]
        if observed_repeats != expected_repeats[:len(observed_repeats)] or incomplete_seen:
            raise S10R4Error("noise observations are not the exact group/repeat-order prefix")
        for repeat_name in observed_repeats:
            observation = repeat_root / repeat_name / "observation.json"
            if not observation.is_file():
                raise S10R4Error("noise prefix contains a partial observation")
            document = load_json(observation)
            validate_document_schema(document)
            validate_sealed_digest(document)
            if document.get("document_kind") != "noise_observation":
                raise S10R4Error("noise prefix document kind mismatch")
        total += len(observed_repeats)
        incomplete_seen = len(observed_repeats) < 7
    return total


def _project_reached_formal_stage(lock_digest: str, *, ignore_blocker: bool = False) -> StageProjection:
    a_count = _exact_census_prefix("A")
    b_count = _exact_census_prefix("B")
    reforecast = _resource_reforecast_path().exists()
    if reforecast:
        if a_count < 3:
            raise S10R4Error("resource reforecast exists before its three-child boundary")
        _seal_resource_reforecast(load_json(FRAME_PATH), lock_digest)
    classification = CLASSIFICATION_PATH.exists()
    selection_status: str | None = None
    selection: dict[str, Any] | None = None
    if classification:
        _load_payload(CLASSIFICATION_PATH, "codegen_classification")
    if SELECTION_PATH.exists():
        selection = _load_payload(SELECTION_PATH, "operational_selection")
        selection_status = selection.get("status")
    if classification != SELECTION_PATH.exists():
        raise S10R4Error("classification/selection durable boundary is partial")
    if classification:
        _recompute_classification_and_selection()
    mapping_a: str | None = None
    mapping_b: str | None = None
    if selection_status == "PASS" and selection is not None:
        frame = load_json(FRAME_PATH)
        by_hash = {row["config_hash"]: row for row in frame["rows"]}
        try:
            selected = [by_hash[value] for value in selection["selected_hashes"]]
        except (KeyError, TypeError) as exc:
            raise S10R4Error("selection hashes do not resolve into the exact frame") from exc
        mapping_a = _exact_mapping_prefix("A", selected, lock_digest)
        if mapping_a == "PASS":
            mapping_b = _exact_mapping_prefix("B", selected, lock_digest)
        elif (MAPPING_ROOT / "pass-B").exists():
            raise S10R4Error("mapping pass B exists after terminal negative pass A")
    elif MAPPING_ROOT.exists():
        raise S10R4Error("mapping raw scope exists before a positive selection")
    mapping_corpus_status = None
    if MAPPING_CORPUS_PATH.exists():
        mapping_corpus_status = _load_payload(MAPPING_CORPUS_PATH, "mapping_corpus").get("status")
        if _rederive_mapping_corpus(lock_digest) != load_json(MAPPING_CORPUS_PATH):
            raise S10R4Error("mapping corpus differs from its raw terminal attempts")
    native = CONFORMANCE_PATH.exists()
    if native:
        native_payload = _load_payload(CONFORMANCE_PATH, "sentinel_conformance")
        expected_native = rederive_native_conformance(
            fixture_path=FIXTURE_PATH,
            formal_root=NATIVE_ROOT,
            binary=BUILD_ROOT / "native/build/s10r4-native",
            lock_digest=lock_digest,
            lock=load_json(LOCK_PATH),
            contract=load_contract(),
        )
        if expected_native != native_payload:
            raise S10R4Error("native conformance differs from its raw transcript")
    elif NATIVE_ROOT.exists() and mapping_corpus_status != "PASS":
        raise S10R4Error("native raw scope exists before mapping A/B PASS")
    environment = ENVIRONMENT_PATH.exists()
    if environment:
        _rederive_environment_summary(lock_digest)
    selection_for_panels = selection if selection_status == "PASS" and selection is not None else None
    correctness_count = _exact_correctness_prefix(selection_for_panels) if selection_for_panels is not None else 0
    correctness_status = None
    if CORRECTNESS_PATH.exists():
        correctness_status = _load_payload(CORRECTNESS_PATH, "smoke_correctness").get("status")
        if _rederive_correctness_summary(load_json(LOCK_PATH), lock_digest) != load_json(CORRECTNESS_PATH):
            raise S10R4Error("correctness summary differs from its raw terminal cells")
    noise_count = _exact_noise_prefix(selection_for_panels) if selection_for_panels is not None else 0
    noise_status = None
    if NOISE_PATH.exists():
        noise_status = _load_payload(NOISE_PATH, "noise_pilot").get("status")
        if _rederive_noise_summary(lock_digest) != load_json(NOISE_PATH):
            raise S10R4Error("noise summary differs from its raw observations")
    base_state = {
        "census_a_count": a_count,
        "census_b_count": b_count,
        "resource_reforecast": reforecast,
        "classification": classification,
        "selection_status": selection_status,
        "mapping_a_status": mapping_a,
        "mapping_b_status": mapping_b,
        "mapping_corpus_status": mapping_corpus_status,
        "native_conformance": native,
        "gpu_environment": environment,
        "blocker_producer": None,
        "correctness_count": correctness_count,
        "correctness_status": correctness_status,
        "noise_count": noise_count,
        "noise_status": noise_status,
        "decision": False,
        "reproduction": False,
    }
    # Validate the complete raw/summary base before inspecting any terminal
    # overlay.  A blocker, decision, or reproduction can never establish its
    # own otherwise-incomplete stage.
    project_formal_stage(base_state)

    blocker_producer = None
    if BLOCKER_PATH.exists() and not ignore_blocker:
        blocker = _load_payload(BLOCKER_PATH, "operational_blocker")
        blocker_producer = blocker.get("producer_command_id")
        future_by_producer = {
            "census": [MAPPING_ROOT, MAPPING_CORPUS_PATH, NATIVE_ROOT, CONFORMANCE_PATH, GPU_ROOT, ENVIRONMENT_PATH, CORRECTNESS_PATH, NOISE_PATH],
            "mapping": [NATIVE_ROOT, CONFORMANCE_PATH, GPU_ROOT, ENVIRONMENT_PATH, CORRECTNESS_PATH, NOISE_PATH],
            "native-conformance": [GPU_ROOT, ENVIRONMENT_PATH, CORRECTNESS_PATH, NOISE_PATH],
            "gpu-environment": [GPU_ROOT / "correctness", GPU_ROOT / "noise", ENVIRONMENT_PATH, CORRECTNESS_PATH, NOISE_PATH],
            "correctness": [GPU_ROOT / "noise", NOISE_PATH],
            "noise": [],
        }
        if blocker_producer not in future_by_producer:
            raise S10R4Error("operational blocker has an unknown producer command")
        forbidden = [
            *future_by_producer[blocker_producer], DECISION_PATH, GATE_RECORD_PATH,
            REPORT_PATH, REPRODUCTION_ROOT,
        ]
        if any(path.exists() for path in forbidden):
            raise S10R4Error("operational blocker coexists with a forbidden terminal/later artifact")
    decision_present = DECISION_PATH.exists()
    if decision_present:
        _validate_decision_overlay(lock_digest)
    elif REPORT_PATH.exists() or GATE_RECORD_PATH.exists():
        raise S10R4Error("terminal report/gate record exists without a canonical decision")

    reproduction_output = REPRODUCTION_ROOT / "s10r4-independent-result.json"
    reproduction = REPRODUCTION_ROOT.exists()
    if reproduction:
        if not REPRODUCTION_ROOT.is_dir() or REPRODUCTION_ROOT.is_symlink():
            raise S10R4Error("reproduction raw scope is not one directory")
        names = sorted(path.name for path in REPRODUCTION_ROOT.iterdir())
        if names != [reproduction_output.name] or not reproduction_output.is_file():
            raise S10R4Error("reproduction raw scope is partial or contains an unknown artifact")
        if not decision_present:
            raise S10R4Error("reproduction exists without a canonical decision")
        _validate_reproduction_overlay(lock_digest, reproduction_output)

    state = dict(base_state)
    state.update(
        {
            "blocker_producer": blocker_producer,
            "decision": decision_present,
            "reproduction": reproduction,
        }
    )
    return project_formal_stage(state)


def _census_results(pass_id: str) -> list[dict[str, Any]]:
    frame = load_json(FRAME_PATH)
    expected = census_expectations(CODEGEN_ROOT, pass_id, frame["rows"])
    return scan_exact_children(CODEGEN_ROOT / f"pass-{pass_id}", expected)


def _resource_reforecast_path() -> Path:
    return CODEGEN_ROOT / "resource-reforecast.json"


def _census_completion_identity(request: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: request[key]
        for key in (
            "pass_id", "registry_index", "config_hash", "input_digest",
            "effective_lock_digest",
        )
    }


def _load_census_process_completion(child_root: Path, request: Mapping[str, Any]) -> dict[str, Any]:
    return validate_process_completion(
        child_root / "process-completion.json",
        command_id="census_child",
        identity=_census_completion_identity(request),
        argv=materialize_command_template(
            "census_child", {"child_root": child_root.resolve(strict=True).as_posix()}
        ),
        cwd=child_root,
        environment=request["environment"],
        allowed_returncodes=(0, 23),
    )


def _seal_resource_reforecast(frame: Mapping[str, Any], lock_digest: str) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    identities: list[dict[str, Any]] = []
    for row in frame["rows"][:3]:
        child_root = CODEGEN_ROOT / f"pass-A/{row['registry_index']:03d}-{row['config_hash']}"
        request = load_json(child_root / "request.json")
        result = load_json(child_root / "result.json")
        validate_child(
            result,
            {
                "document_kind": "census_child",
                "pass_id": "A",
                "registry_index": row["registry_index"],
                "config_hash": row["config_hash"],
            },
        )
        identity = _census_completion_identity(request)
        completion = _load_census_process_completion(child_root, request)
        if completion["process_returncode"] != result["outputs"]["process_returncode"]:
            raise S10R4Error("census process completion/result return-code mismatch")
        observation = completion["resource_observation"]
        observations.append(observation)
        identities.append(
            {
                **identity,
                "completion_digest": result["completion_digest"],
                "process_completion_digest": completion["document_digest"],
            }
        )
    observed = {
        "wall_seconds": sum(float(row["wall_seconds"]) for row in observations),
        "cpu_seconds": sum(float(row["child_cpu_seconds"]) for row in observations),
        "new_transient_storage_bytes": sum(int(row["new_child_tree_bytes"]) for row in observations),
    }
    projected = {
        key: value * 228 / 3
        for key, value in observed.items()
    }
    resources = load_contract()["resources"]
    targets = resources["planning_targets"]
    multiplier = float(resources["projected_cost_multiplier_notification"])
    document = seal_digest(
        {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": "resource_reforecast",
            "effective_lock_digest": lock_digest,
            "terminal_child_count": 3,
            "total_scheduled_children": 228,
            "child_identities": identities,
            "observed_first_three": observed,
            "projected_full_census": projected,
            "planning_targets": targets,
            "notification": {
                "storage_threshold_bytes": resources["default_transient_notification_bytes"],
                "projected_cost_multiplier": multiplier,
                "storage_threshold_reached": projected["new_transient_storage_bytes"]
                >= resources["default_transient_notification_bytes"],
                "wall_projection_above_multiplier": projected["wall_seconds"] >= targets["wall_s"] * multiplier,
                "cpu_projection_above_multiplier": projected["cpu_seconds"] >= targets["cpu_s"] * multiplier,
                "action": "record_notify_continue",
            },
            "outcome_blind": True,
        }
    )
    validate_document_schema(document)
    atomic_write_json(_resource_reforecast_path(), document)
    return document


def command_census(arguments: argparse.Namespace) -> None:
    _, lock_digest = _formal_admission(arguments)
    if _resume_existing_operational_blocker(lock_digest, "census"):
        return
    pass_id = arguments.pass_id
    if pass_id == "B":
        _census_results("A")
    elif (CODEGEN_ROOT / "pass-B").exists():
        raise S10R4Error("census pass A cannot be rerun after pass B began")
    frame = load_json(FRAME_PATH)
    worker_env = _worker_environment()
    validate_environment(worker_env, worker_pythonpath=WORKER_PYTHONPATH)
    pass_root = CODEGEN_ROOT / f"pass-{pass_id}"
    with exclusive_scope(pass_root):
        existing_flags = [
            (pass_root / f"{row['registry_index']:03d}-{row['config_hash']}/result.json").is_file()
            for row in frame["rows"]
        ]
        existing_count = sum(existing_flags)
        if existing_flags != [index < existing_count for index in range(len(existing_flags))]:
            raise S10R4Error("census terminal children are not an exact registry-order prefix")
        if pass_id == "A":
            if existing_count > 3 and not _resource_reforecast_path().is_file():
                raise S10R4Error("census advanced beyond three children without the required reforecast")
            if existing_count >= 3:
                _seal_resource_reforecast(frame, lock_digest)
        elif not _resource_reforecast_path().is_file():
            raise S10R4Error("census pass B requires the three-child resource reforecast")
        for row in frame["rows"]:
            child_root = pass_root / f"{row['registry_index']:03d}-{row['config_hash']}"
            result_path = child_root / "result.json"
            if result_path.exists():
                request = load_json(child_root / "request.json")
                _load_census_process_completion(child_root, request)
                continue
            child_root.mkdir(parents=True, exist_ok=False)
            request = census_request(pass_id, row, child_root, worker_env, lock_digest)
            request_path = child_root / "request.json"
            atomic_write_json(request_path, request)
            argv = materialize_command_template(
                "census_child", {"child_root": child_root.resolve().as_posix()}
            )
            code, observation = _run_logged_observed(
                argv, child_root, worker_env, child_root / "stdout.log", child_root / "stderr.log", 7200,
            )
            if code not in (0, 23) or not result_path.is_file():
                raise S10R4Error(f"census child did not produce an allowlisted terminal result: {child_root}")
            child = load_json(result_path)
            if child.get("outputs", {}).get("process_returncode") != code:
                raise S10R4Error("census child process/result return-code mismatch")
            validate_document_schema(child)
            validate_child(
                child,
                {
                    "document_kind": "census_child", "pass_id": pass_id,
                    "registry_index": row["registry_index"], "config_hash": row["config_hash"],
                },
            )
            artifact_records, _ = ordinary_file_records(Path(request["artifact_root"]))
            if artifact_records != child.get("artifact_inventory"):
                raise S10R4Error("census child artifact inventory is incomplete before completion seal")
            finalize_process_completion(
                child_root / "process-completion.json",
                command_id="census_child",
                identity=_census_completion_identity(request),
                argv=argv,
                cwd=child_root,
                environment=worker_env,
                process_returncode=code,
                allowed_returncodes=(0, 23),
                resource_observation=observation,
            )
            if pass_id == "A" and row["registry_index"] == 2:
                _seal_resource_reforecast(frame, lock_digest)
            if pass_id == "A" and row["registry_index"] > 2 and not _resource_reforecast_path().is_file():
                raise S10R4Error("census fourth child cannot begin before resource reforecast")
    results = _census_results(pass_id)
    _print(
        {
            "checkpoint_id": "S10R4", "status": "CENSUS_PASS_COMPLETE", "pass_id": pass_id,
            "terminal_children": len(results), "effective_lock_digest": lock_digest,
        }
    )


def command_classify_select(arguments: argparse.Namespace) -> None:
    _, lock_digest = _formal_admission(arguments)
    if CLASSIFICATION_PATH.exists() or SELECTION_PATH.exists():
        if not CLASSIFICATION_PATH.is_file() or not SELECTION_PATH.is_file():
            raise S10R4Error("classification/selection resume boundary is partial")
        classification = _load_payload(CLASSIFICATION_PATH, "codegen_classification")
        selection = _load_payload(SELECTION_PATH, "operational_selection")
        if classification.get("effective_lock_digest") != lock_digest or selection.get("effective_lock_digest") != lock_digest:
            raise S10R4Error("classification/selection resume lock mismatch")
        _recompute_classification_and_selection()
        _print({"checkpoint_id": "S10R4", "status": selection["status"], "selection_digest": load_json(SELECTION_PATH)["document_digest"]})
        return
    frame = load_json(FRAME_PATH)
    pass_a = _census_results("A")
    pass_b = _census_results("B")
    classification_rows = []
    survivors = []
    for row, left, right in zip(frame["rows"], pass_a, pass_b):
        if left["config_hash"] != row["config_hash"] or right["config_hash"] != row["config_hash"]:
            raise S10R4Error("census/frame association drift")
        stable = stable_classify(left["outputs"], right["outputs"])
        item = {
            "registry_index": row["registry_index"],
            "config_hash": row["config_hash"],
            "stable_class": stable,
            "pass_a_completion_digest": left["completion_digest"],
            "pass_b_completion_digest": right["completion_digest"],
        }
        classification_rows.append(item)
        if stable == "operational_codegen_witnessed":
            survivors.append(row)
    classification = _write_formal(
        CLASSIFICATION_PATH,
        "codegen_classification",
        {
            "status": "PASS",
            "frame_registry_digest": frame["registry_digest"],
            "effective_lock_digest": lock_digest,
            "pass_count": 2,
            "child_count": 228,
            "row_count": 114,
            "survivor_count": len(survivors),
            "rows": classification_rows,
        },
    )
    candidate_registry = load_json(
        REPO_ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r3-candidate-atom-registry.json"
    )
    candidate_atoms = [row["atom_id"] for row in candidate_registry["rows"]]
    try:
        result = deterministic_select([witness_from_frame_row(row) for row in survivors], candidate_atoms)
        selection_payload = {
            **selection_to_document(result),
            "status": "PASS",
            "classification_digest": classification["document_digest"],
            "effective_lock_digest": lock_digest,
        }
    except S10R4Error as exc:
        if "FT-BLOCKED-MAPPING" not in str(exc):
            raise
        selection_payload = {
            "status": "NEGATIVE_MAPPING",
            "criterion": "S1_ENTRY_BLOCKED",
            "failure_id": "FT-BLOCKED-MAPPING",
            "edge": None,
            "reason": str(exc),
            "survivor_hashes": sorted(row["config_hash"] for row in survivors),
            "classification_digest": classification["document_digest"],
            "effective_lock_digest": lock_digest,
        }
    selection = _write_formal(SELECTION_PATH, "operational_selection", selection_payload)
    _print(
        {
            "checkpoint_id": "S10R4", "status": selection_payload["status"],
            "survivor_count": len(survivors), "selection_digest": selection["document_digest"],
        }
    )


def _mapping_attempt_object(child: Mapping[str, Any], request: Mapping[str, Any]) -> MappingAttempt:
    output = child["outputs"]
    if output["status"] == "success":
        return MappingAttempt("success")
    selected = request["selected_rows"]
    slot = output["first_failing_sorted_slot"]
    if (
        output["failing_pass_id"] != request["pass_id"]
        or not isinstance(slot, int) or isinstance(slot, bool)
        or slot % 3 != 0 or not 0 <= slot // 3 < len(selected)
        or output["first_failing_config_hash"] != selected[slot // 3]["config_hash"]
    ):
        raise S10R4Error("mapping failure site does not derive from request/pass identity")
    return MappingAttempt(
        "allowlisted_failure",
        output["signature_id"],
        output["failing_pass_id"],
        output["first_failing_config_hash"],
        output["first_failing_sorted_slot"],
        output["exact_signature_fields"],
        canonical_sha256(
            {
                key: value
                for key, value in request.items()
                if key not in ("input_digest", "attempt", "cwd")
            }
        ),
        canonical_sha256(
            {
                "source_commit": request["source_commit"],
                "environment": request["environment"],
                "actual_yaml_sha256": request["actual_yaml_sha256"],
            }
        ),
    )


def _run_mapping_attempt(
    pass_id: str,
    attempt: int,
    selected: list[dict[str, Any]],
    lock_digest: str,
    *,
    existing_only: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    attempt_root = MAPPING_ROOT / f"pass-{pass_id}/attempt-{attempt:02d}"
    result_path = attempt_root / "result.json"
    request_path = attempt_root / "request.json"
    environment = _worker_environment()
    expected_request = mapping_request(pass_id, attempt, selected, attempt_root, environment, lock_digest)

    def completion_identity(request: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: request[key]
            for key in ("pass_id", "attempt", "input_digest", "effective_lock_digest")
        }

    def load_terminal(*, require_completion: bool) -> tuple[dict[str, Any], dict[str, Any]]:
        if not result_path.is_file() or not request_path.is_file():
            raise S10R4Error("mapping attempt resume boundary is partial")
        request = load_json(request_path)
        if request != expected_request:
            raise S10R4Error("mapping attempt request differs from exact reconstruction")
        result = load_json(result_path)
        validate_document_schema(result)
        validate_child(
            result,
            {"document_kind": "mapping_attempt", "pass_id": pass_id, "attempt": attempt},
        )
        expected_argv = materialize_command_template(
            "mapping_child", {"attempt_root": attempt_root.resolve(strict=True).as_posix()}
        )
        if (
            result.get("cwd") != request["cwd"]
            or result.get("argv") != expected_argv
            or result.get("environment") != request["environment"]
            or result.get("effective_lock_digest") != request["effective_lock_digest"]
        ):
            raise S10R4Error("mapping attempt result/request runtime binding mismatch")
        if result.get("input_digest") != request["input_digest"]:
            raise S10R4Error("mapping attempt result/request digest mismatch")
        rows_root = attempt_root / "rows"
        records = ordinary_file_records(rows_root)[0] if rows_root.is_dir() else []
        if records != result.get("artifact_inventory"):
            raise S10R4Error("mapping attempt artifact inventory drift")
        code = result.get("outputs", {}).get("worker_returncode")
        if code not in (0, 23, 24):
            raise S10R4Error("mapping terminal return code is outside its allowlist")
        if require_completion:
            completion = validate_process_completion(
                attempt_root / "process-completion.json",
                command_id="mapping_child",
                identity=completion_identity(request),
                argv=expected_argv,
                cwd=attempt_root,
                environment=request["environment"],
                allowed_returncodes=(0, 23, 24),
            )
            if completion["process_returncode"] != code:
                raise S10R4Error("mapping process completion/result return-code mismatch")
        return result, request

    if result_path.exists():
        return load_terminal(require_completion=True)
    if existing_only:
        raise S10R4Error(f"mapping pass {pass_id} lacks its complete terminal attempt")
    if attempt_root.exists():
        raise S10R4Error("mapping attempt has a partial/crashed terminal boundary")
    attempt_root.mkdir(parents=True, exist_ok=False)
    atomic_write_json(request_path, expected_request)
    argv = materialize_command_template(
        "mapping_child", {"attempt_root": attempt_root.resolve().as_posix()}
    )
    code, observation = _run_logged_observed(
        argv, attempt_root, environment, attempt_root / "stdout.log", attempt_root / "stderr.log", 7200
    )
    if code not in (0, 23, 24) or not result_path.is_file():
        raise S10R4Error("mapping worker did not produce an allowlisted terminal result")
    result, request = load_terminal(require_completion=False)
    if result.get("outputs", {}).get("worker_returncode") != code:
        raise S10R4Error("mapping process/result return-code mismatch")
    finalize_process_completion(
        attempt_root / "process-completion.json",
        command_id="mapping_child",
        identity=completion_identity(request),
        argv=argv,
        cwd=attempt_root,
        environment=environment,
        process_returncode=code,
        allowed_returncodes=(0, 23, 24),
        resource_observation=observation,
    )
    load_terminal(require_completion=True)
    return result, request


def _mapping_pass_terminal(
    pass_id: str,
    selected: list[dict[str, Any]],
    lock_digest: str,
    *,
    existing_only: bool = False,
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    first, request_one = _run_mapping_attempt(
        pass_id, 1, selected, lock_digest, existing_only=existing_only
    )
    attempts = [_mapping_attempt_object(first, request_one)]
    children = [first]
    if attempts[0].status != "success":
        second, request_two = _run_mapping_attempt(
            pass_id, 2, selected, lock_digest, existing_only=existing_only
        )
        attempts.append(_mapping_attempt_object(second, request_two))
        children.append(second)
    terminal = decide_mapping_attempts(attempts)
    rows = children[-1]["outputs"].get("rows", []) if terminal == "mapping_pass_PASS" else []
    return terminal, rows, children


def _rederive_mapping_corpus(lock_digest: str) -> dict[str, Any]:
    selection = _load_payload(SELECTION_PATH, "operational_selection")
    if selection.get("status") != "PASS":
        raise S10R4Error("mapping corpus resume lacks a positive selection")
    frame = load_json(FRAME_PATH)
    by_hash = {row["config_hash"]: row for row in frame["rows"]}
    selected = [by_hash[config_hash] for config_hash in selection["selected_hashes"]]
    existing = _load_payload(MAPPING_CORPUS_PATH, "mapping_corpus")
    if existing.get("status") == "PASS":
        pass_a_terminal, pass_a_rows, _ = _mapping_pass_terminal("A", selected, lock_digest, existing_only=True)
        pass_b_terminal, pass_b_rows, _ = _mapping_pass_terminal("B", selected, lock_digest, existing_only=True)
        if pass_a_terminal != "mapping_pass_PASS" or pass_b_terminal != "mapping_pass_PASS":
            raise S10R4Error("mapping PASS corpus differs from its raw attempt terminals")
        validate_mapping_batch(pass_a_rows, selection["selected_hashes"], "A")
        validate_mapping_batch(pass_b_rows, selection["selected_hashes"], "B")
        compare_mapping_passes(pass_a_rows, pass_b_rows)
        payload = {
            "status": "PASS", "k": selection["k"], "rows_per_pass": 3 * selection["k"],
            "selected_hashes": selection["selected_hashes"], "pass_a_rows": pass_a_rows,
            "pass_b_rows": pass_b_rows, "effective_lock_digest": lock_digest,
        }
    else:
        failing_pass = existing.get("failing_pass")
        if failing_pass not in ("A", "B"):
            raise S10R4Error("negative mapping corpus lacks its exact failing pass")
        terminal, _, children = _mapping_pass_terminal(failing_pass, selected, lock_digest, existing_only=True)
        if terminal == "mapping_pass_PASS":
            raise S10R4Error("negative mapping corpus rederives as PASS")
        payload = {
            "status": "NEGATIVE_MAPPING", "criterion": "S1_ENTRY_BLOCKED",
            "failure_id": "FT-BLOCKED-MAPPING", "edge": None, "failing_pass": failing_pass,
            "attempt_digests": [child["completion_digest"] for child in children],
            "effective_lock_digest": lock_digest,
        }
    return _formal_document("mapping_corpus", payload)


def command_mapping(arguments: argparse.Namespace) -> None:
    _, lock_digest = _formal_admission(arguments)
    if _resume_existing_operational_blocker(lock_digest, "mapping"):
        return
    if MAPPING_CORPUS_PATH.exists():
        corpus = _load_payload(MAPPING_CORPUS_PATH, "mapping_corpus")
        if corpus.get("effective_lock_digest") != lock_digest:
            raise S10R4Error("mapping resume lock mismatch")
        if _rederive_mapping_corpus(lock_digest) != load_json(MAPPING_CORPUS_PATH):
            raise S10R4Error("mapping corpus differs from raw terminal-attempt recomputation")
        _print({"checkpoint_id": "S10R4", "status": corpus["status"], "document_digest": load_json(MAPPING_CORPUS_PATH)["document_digest"]})
        return
    selection = _load_payload(SELECTION_PATH, "operational_selection")
    if selection.get("status") != "PASS":
        raise S10R4Error("mapping is unreached after terminal selection")
    frame = load_json(FRAME_PATH)
    by_hash = {row["config_hash"]: row for row in frame["rows"]}
    selected = [by_hash[config_hash] for config_hash in selection["selected_hashes"]]
    if arguments.pass_id == "A" and (MAPPING_ROOT / "pass-B").exists():
        raise S10R4Error("mapping pass A cannot resume after pass B began")
    pass_a_rows: list[dict[str, Any]] | None = None
    if arguments.pass_id == "B":
        pass_a_terminal, pass_a_rows, _ = _mapping_pass_terminal(
            "A", selected, lock_digest, existing_only=True
        )
        if pass_a_terminal != "mapping_pass_PASS":
            raise S10R4Error("mapping pass B requires terminal PASS from pass A")
    with exclusive_scope(MAPPING_ROOT / f"pass-{arguments.pass_id}"):
        terminal, rows, children = _mapping_pass_terminal(arguments.pass_id, selected, lock_digest)
    if terminal != "mapping_pass_PASS":
        corpus = _write_formal(
            MAPPING_CORPUS_PATH,
            "mapping_corpus",
            {
                "status": "NEGATIVE_MAPPING", "criterion": "S1_ENTRY_BLOCKED",
                "failure_id": "FT-BLOCKED-MAPPING", "edge": None,
                "failing_pass": arguments.pass_id,
                "attempt_digests": [child["completion_digest"] for child in children],
                "effective_lock_digest": lock_digest,
            },
        )
        _print({"checkpoint_id": "S10R4", "status": "NEGATIVE_MAPPING", "document_digest": corpus["document_digest"]})
        return
    if arguments.pass_id == "A":
        _print({"checkpoint_id": "S10R4", "status": "MAPPING_PASS_COMPLETE", "pass_id": "A", "row_count": len(rows)})
        return
    if pass_a_rows is None:
        raise S10R4Error("mapping pass-A terminal rows are absent")
    pass_a = pass_a_rows
    validate_mapping_batch(pass_a, selection["selected_hashes"], "A")
    validate_mapping_batch(rows, selection["selected_hashes"], "B")
    compare_mapping_passes(pass_a, rows)
    corpus = _write_formal(
        MAPPING_CORPUS_PATH,
        "mapping_corpus",
        {
            "status": "PASS", "k": selection["k"], "rows_per_pass": 3 * selection["k"],
            "selected_hashes": selection["selected_hashes"], "pass_a_rows": pass_a,
            "pass_b_rows": rows, "effective_lock_digest": lock_digest,
        },
    )
    _print({"checkpoint_id": "S10R4", "status": "MAPPING_A_B_PASS", "document_digest": corpus["document_digest"]})


def command_native_conformance(arguments: argparse.Namespace) -> None:
    contract = load_contract()
    lock, lock_digest = _formal_admission(arguments)
    if _resume_existing_operational_blocker(lock_digest, "native-conformance"):
        return
    if CONFORMANCE_PATH.exists():
        payload = _load_payload(CONFORMANCE_PATH, "sentinel_conformance")
        if payload.get("effective_lock_digest") != lock_digest:
            raise S10R4Error("native conformance resume lock mismatch")
        expected = rederive_native_conformance(
            fixture_path=FIXTURE_PATH,
            formal_root=NATIVE_ROOT,
            binary=BUILD_ROOT / "native/build/s10r4-native",
            lock_digest=lock_digest,
            lock=lock,
            contract=contract,
        )
        if expected != payload:
            raise S10R4Error("native conformance resume summary differs from raw transcript recomputation")
        _print({"checkpoint_id": "S10R4", "status": "NATIVE_CONFORMANCE_PASS", "document_digest": load_json(CONFORMANCE_PATH)["document_digest"]})
        return
    mapping = _load_payload(MAPPING_CORPUS_PATH, "mapping_corpus")
    if mapping.get("status") != "PASS":
        raise S10R4Error("native conformance requires mapping A/B PASS")
    binary = BUILD_ROOT / "native/build/s10r4-native"
    with exclusive_scope(NATIVE_ROOT):
        raw_terminal_paths = [
            NATIVE_ROOT / "native-transcript.json", NATIVE_ROOT / "native.stdout",
            NATIVE_ROOT / "native.stderr", NATIVE_ROOT / "native-input-binding.json",
            NATIVE_ROOT / "cohort-input.txt",
        ]
        if any(path.exists() for path in raw_terminal_paths):
            if not all(path.is_file() for path in raw_terminal_paths):
                raise S10R4Error("native conformance raw resume boundary is partial")
            result = rederive_native_conformance(
                fixture_path=FIXTURE_PATH, formal_root=NATIVE_ROOT, binary=binary,
                lock_digest=lock_digest, lock=lock, contract=contract,
            )
        else:
            result = run_native_conformance(
                fixture_path=FIXTURE_PATH,
                formal_root=NATIVE_ROOT,
                binary=binary,
                lock_digest=lock_digest,
                lock=lock,
                contract=contract,
            )
        document = _write_formal(CONFORMANCE_PATH, "sentinel_conformance", result)
    _print(
        {
            "checkpoint_id": "S10R4", "status": "NATIVE_CONFORMANCE_PASS",
            "document_digest": document["document_digest"],
        }
    )


GPU_ALLOCATION_ARGV = materialize_command_template("gpu_allocation_snapshot")
GPU_PROCESS_ARGV = materialize_command_template("gpu_process_snapshot")


def _gpu_snapshot(root: Path, ordinal: str) -> dict[str, Any]:
    snapshot_root = root / ordinal
    snapshot_root.mkdir(parents=True, exist_ok=False)
    allocation_stdout = snapshot_root / "allocation.stdout"
    allocation_stderr = snapshot_root / "allocation.stderr"
    process_stdout = snapshot_root / "process.stdout"
    process_stderr = snapshot_root / "process.stderr"
    allocation_code = _run_logged(
        GPU_ALLOCATION_ARGV, REPO_ROOT, FIXED_ENVIRONMENT,
        allocation_stdout, allocation_stderr, 60,
    )
    process_code = _run_logged(
        GPU_PROCESS_ARGV, REPO_ROOT, FIXED_ENVIRONMENT,
        process_stdout, process_stderr, 60,
    )
    if allocation_code != 0 or process_code != 0:
        raise S10R4Error("GPU snapshot command returned nonzero")
    allocation, processes = validate_snapshot_pair(
        allocation_stdout.read_bytes(), process_stdout.read_bytes()
    )
    return {
        "allocation_rows": allocation,
        "pid_rows": {str(key): value for key, value in processes.items()},
        "allocation_stdout_sha256": raw_sha256(allocation_stdout),
        "allocation_stderr_sha256": raw_sha256(allocation_stderr),
        "process_stdout_sha256": raw_sha256(process_stdout),
        "process_stderr_sha256": raw_sha256(process_stderr),
        "allocation_argv": GPU_ALLOCATION_ARGV,
        "process_argv": GPU_PROCESS_ARGV,
    }


def _rederive_gpu_snapshot(root: Path, ordinal: str) -> dict[str, Any]:
    snapshot_root = root / ordinal
    allocation_stdout = snapshot_root / "allocation.stdout"
    allocation_stderr = snapshot_root / "allocation.stderr"
    process_stdout = snapshot_root / "process.stdout"
    process_stderr = snapshot_root / "process.stderr"
    if not all(path.is_file() for path in (allocation_stdout, allocation_stderr, process_stdout, process_stderr)):
        raise S10R4Error("GPU snapshot resume evidence is partial")
    allocation, processes = validate_snapshot_pair(allocation_stdout.read_bytes(), process_stdout.read_bytes())
    return {
        "allocation_rows": allocation,
        "pid_rows": {str(key): value for key, value in processes.items()},
        "allocation_stdout_sha256": raw_sha256(allocation_stdout),
        "allocation_stderr_sha256": raw_sha256(allocation_stderr),
        "process_stdout_sha256": raw_sha256(process_stdout),
        "process_stderr_sha256": raw_sha256(process_stderr),
        "allocation_argv": GPU_ALLOCATION_ARGV,
        "process_argv": GPU_PROCESS_ARGV,
    }


def _snapshot_selected(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    pids = {int(key): value for key, value in snapshot["pid_rows"].items()}
    return dict(select_gpu(snapshot["allocation_rows"], pids))


def _assert_selected_snapshot(selected: Mapping[str, Any], snapshot: Mapping[str, Any]) -> None:
    rows = {row["physical_visible_index"]: row for row in snapshot["allocation_rows"]}
    index = int(selected["physical_visible_index"])
    if index not in rows:
        raise S10R4Error("selected GPU disappeared from allocation snapshot")
    verify_gpu_continuity(selected, rows[index], snapshot["pid_rows"].get(str(index), []))


def _rederive_environment_summary(lock_digest: str) -> dict[str, Any]:
    document = load_json(ENVIRONMENT_PATH)
    payload = _load_payload(ENVIRONMENT_PATH, "environment")
    if payload.get("effective_lock_digest") != lock_digest:
        raise S10R4Error("GPU environment resume lock mismatch")
    snapshot = _rederive_gpu_snapshot(GPU_ROOT / "environment", "initial")
    if payload.get("initial_snapshot") != snapshot:
        raise S10R4Error("GPU environment summary differs from its exact raw snapshot")
    selected = payload.get("selected_gpu")
    if not isinstance(selected, dict):
        raise S10R4Error("GPU environment resume selection is malformed")
    _assert_selected_snapshot(selected, snapshot)
    if (
        selected.get("allocation_snapshot_sha256") != snapshot["allocation_stdout_sha256"]
        or selected.get("process_snapshot_sha256") != snapshot["process_stdout_sha256"]
    ):
        raise S10R4Error("GPU environment selected-card snapshot binding drift")
    expected_payload = {
        "status": "PASS",
        "selected_gpu": selected,
        "initial_snapshot": snapshot,
        "reservation_required": False,
        "exclusivity_claimed": False,
        "effective_lock_digest": lock_digest,
    }
    if _formal_document("environment", expected_payload) != document:
        raise S10R4Error("GPU environment document differs from raw snapshot recomputation")
    return payload


def _wait_for_selected_gpu(root: Path, selected: Mapping[str, Any]) -> dict[str, Any]:
    waits: list[dict[str, Any]] = []
    ordinal = 0
    while True:
        snapshot = _gpu_snapshot(root, f"gpu-preflight-{ordinal:03d}")
        try:
            _assert_selected_snapshot(selected, snapshot)
        except S10R4Error as exc:
            if not str(exc).startswith("WAIT_RECHECK_SAME_CARD:"):
                raise
            waits.append(snapshot)
            ordinal += 1
            time.sleep(30)
            continue
        return {
            "selected_card_wait_count": len(waits),
            "wait_snapshots": waits,
            "terminal_snapshot": snapshot,
        }


def command_gpu_environment(arguments: argparse.Namespace) -> None:
    _, lock_digest = _formal_admission(arguments)
    if _resume_existing_operational_blocker(lock_digest, "gpu-environment"):
        return
    if ENVIRONMENT_PATH.exists():
        _rederive_environment_summary(lock_digest)
        _print({"checkpoint_id": "S10R4", "status": "GPU_ENVIRONMENT_PASS", "document_digest": load_json(ENVIRONMENT_PATH)["document_digest"]})
        return
    if _load_payload(CONFORMANCE_PATH, "sentinel_conformance").get("status") != "PASS":
        raise S10R4Error("GPU environment requires native conformance PASS")
    environment_root = GPU_ROOT / "environment"
    with exclusive_scope(environment_root):
        initial_root = environment_root / "initial"
        snapshot = (
            _rederive_gpu_snapshot(environment_root, "initial")
            if initial_root.exists()
            else _gpu_snapshot(environment_root, "initial")
        )
        try:
            selected = _snapshot_selected(snapshot)
        except S10R4Error:
            materially_matching = [
                row
                for row in snapshot["allocation_rows"]
                if row.get("gfx_version") == "gfx942"
                and row.get("compute_partition") == "SPX"
                and row.get("memory_partition") == "NPS1"
            ]
            if materially_matching:
                raise S10R4Error(
                    "WAIT_RECHECK_ELIGIBLE_CARD: matching gfx942/SPX/NPS1 hardware is transiently busy"
                )
            blocker = write_operational_blocker(
                producer_command_id="gpu-environment",
                reason_code="NO_ELIGIBLE_GPU_MATERIAL_AVAILABILITY",
                evidence_paths=[
                    environment_root / "initial/allocation.stdout",
                    environment_root / "initial/allocation.stderr",
                    environment_root / "initial/process.stdout",
                    environment_root / "initial/process.stderr",
                ],
                pre_block_projection=_project_reached_formal_stage(lock_digest),
                lock_digest=lock_digest,
            )
            _print({"checkpoint_id": "S10R4", "status": "BLOCKED", "document_digest": blocker["document_digest"]})
            return
        payload = {
            "status": "PASS",
            "selected_gpu": {
                **selected,
                "logical_device_index": 0,
                "container_mount": {"host": "/data1/perlee", "container": "/src", "mode": "rw"},
                "allocation_snapshot_sha256": snapshot["allocation_stdout_sha256"],
                "process_snapshot_sha256": snapshot["process_stdout_sha256"],
            },
            "initial_snapshot": snapshot,
            "reservation_required": False,
            "exclusivity_claimed": False,
            "effective_lock_digest": lock_digest,
        }
        document = _write_formal(ENVIRONMENT_PATH, "environment", payload)
    _print(
        {
            "checkpoint_id": "S10R4", "status": "GPU_ENVIRONMENT_PASS",
            "physical_visible_index": selected["physical_visible_index"],
            "document_digest": document["document_digest"],
        }
    )


def _parse_strace_execve(
    path: Path,
    lock: Mapping[str, Any],
    expected_root: list[str],
    root_command_binding: Mapping[str, Any],
    toolchain_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise S10R4Error("correctness build strace is empty")
    if "<unfinished ...>" in text or "execve resumed>" in text:
        raise S10R4Error("correctness build strace contains an unfinished/resumed execve")
    attempt_root = Path(expected_root[4]).parent.resolve(strict=True)
    permitted_roots = (
        Path("/opt/rocm").resolve(strict=True),
        Path("/opt/rocm-7.2.4").resolve(strict=True),
        Path(WORKER_PYTHONPATH).resolve(strict=True),
        attempt_root,
    )
    permitted_files = (SCRIPT_PATH.resolve(strict=True),)

    output_options = {
        "-o", "-MF", "--output", "--output-file", "--output-dir",
        "--output-directory", "--dependency-file",
    }
    input_options = {"-I", "-L", "-include", "-isystem", "--sysroot"}
    path_suffixes = (
        ".a", ".bc", ".co", ".cpp", ".cxx", ".d", ".h", ".hpp", ".hsaco",
        ".ini", ".json", ".ll", ".o", ".py", ".s", ".so", ".txt", ".yaml", ".yml",
    )

    def path_candidates(argv: Sequence[str]) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        next_direction: str | None = None
        for index, argument in enumerate(argv[1:], start=1):
            if argument in output_options:
                next_direction = "output"
                continue
            if argument in input_options:
                next_direction = "input"
                continue
            direction = next_direction or "input"
            next_direction = None
            values: list[str] = []
            if argument.startswith("@"):
                values = [argument[1:]]
            elif argument.startswith("-") and "=" in argument:
                option, candidate = argument.split("=", 1)
                direction = "output" if option in output_options else "input"
                values = [candidate]
            elif argument.startswith(("-I", "-L")) and len(argument) > 2:
                values = [argument[2:]]
            elif argument.startswith("-Wl,"):
                values = [part for part in argument[4:].split(",") if part]
            elif not argument.startswith("-"):
                values = [argument]
            for candidate in values:
                if not (
                    candidate.startswith(("/", "./", "../"))
                    or "/" in candidate
                    or candidate.endswith(path_suffixes)
                    or direction == "output"
                ):
                    continue
                candidates.append(
                    {
                        "argument_index": index,
                        "argument": argument,
                        "candidate": candidate,
                        "direction": direction,
                    }
                )
        if next_direction is not None:
            raise S10R4Error("exec argv path option lacks a value")
        return candidates

    def classify_paths(argv: Sequence[str], observed_cwd: Path | None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for candidate_row in path_candidates(argv):
            raw = Path(candidate_row["candidate"])
            if not raw.is_absolute() and observed_cwd is None:
                raise S10R4Error("unmatched compiler descendant has a relative argv path")
            resolved = (raw if raw.is_absolute() else observed_cwd / raw).resolve(strict=False)
            value = candidate_row["argument"]
            direction = candidate_row["direction"]
            if resolved in permitted_files:
                classification = resolved.as_posix()
            else:
                classification = next(
                    (root.as_posix() for root in permitted_roots if resolved == root or root in resolved.parents),
                    None,
                )
            if classification is None:
                raise S10R4Error(f"strace argv path escapes frozen roots: {value}")
            if direction == "output" and not (resolved == attempt_root or attempt_root in resolved.parents):
                raise S10R4Error(f"strace argv writable path escapes attempt root: {value}")
            rows.append(
                {
                    "argument_index": candidate_row["argument_index"],
                    "argument": value,
                    "resolved_path": resolved.as_posix(),
                    "direction": direction,
                    "permitted_scope": classification,
                }
            )
        return rows

    root_fields = {
        "command_kind", "requested_executable", "resolved_executable", "executable_sha256",
        "argv", "cwd", "environment",
    }
    if set(root_command_binding) != root_fields or root_command_binding.get("command_kind") != "correctness_build_child":
        raise S10R4Error("correctness root command binding has an inexact field set")
    if root_command_binding.get("argv") != expected_root:
        raise S10R4Error("correctness root command binding argv mismatch")
    if root_command_binding.get("cwd") != attempt_root.as_posix():
        raise S10R4Error("correctness root command binding cwd mismatch")
    if not isinstance(root_command_binding.get("environment"), dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in root_command_binding["environment"].items()
    ):
        raise S10R4Error("correctness root command binding environment is malformed")
    root_executable = Path(expected_root[0]).resolve(strict=True)
    if (
        root_command_binding.get("requested_executable") != expected_root[0]
        or root_command_binding.get("resolved_executable") != root_executable.as_posix()
        or root_command_binding.get("executable_sha256") != raw_sha256(root_executable)
    ):
        raise S10R4Error("correctness root command binding executable mismatch")

    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        if "execve" not in line:
            continue
        marker = "execve("
        position = line.find(marker)
        if position < 0:
            raise S10R4Error("strace contains an ambiguous execve record")
        call = line[position + len(marker):]
        first_comma = call.find(", [")
        if first_comma < 0:
            raise S10R4Error("strace execve record is unparsable")
        try:
            executable = ast.literal_eval(call[:first_comma])
        except (ValueError, SyntaxError) as exc:
            raise S10R4Error("strace executable token is ambiguous") from exc
        argv_start = first_comma + 2
        depth = 0
        quote = False
        escaped = False
        end = None
        for index, character in enumerate(call[argv_start:], start=argv_start):
            if quote:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    quote = False
            else:
                if character == '"':
                    quote = True
                elif character == "[":
                    depth += 1
                elif character == "]":
                    depth -= 1
                    if depth == 0:
                        end = index + 1
                        break
        if end is None:
            raise S10R4Error("strace argv is truncated")
        try:
            argv = ast.literal_eval(call[argv_start:end])
        except (ValueError, SyntaxError) as exc:
            raise S10R4Error("strace argv token is ambiguous") from exc
        if not re.search(r"\)\s*=\s*0\s*$", call[end:]):
            raise S10R4Error("strace contains a failed or ambiguous execve result")
        if not isinstance(executable, str) or not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
            raise S10R4Error("strace execve types are malformed")
        pid_match = re.match(r"^\s*(?:\[pid\s+)?(?P<pid>\d+)\]?\s+", line)
        if pid_match is None:
            raise S10R4Error("strace execve record lacks an unambiguous process id")
        if not Path(executable).is_absolute():
            raise S10R4Error("strace executable path is not absolute")
        resolved = Path(executable).resolve(strict=True)
        records.append(
            {
                "trace_ordinal": len(records),
                "observed_trace_pid": int(pid_match.group("pid")),
                "requested_executable": executable,
                "resolved_executable": resolved.as_posix(),
                "argv": argv,
                "execve_result": 0,
                "executable_sha256": raw_sha256(resolved),
                "path_containment": [],
                "association_kind": "unclassified",
            }
        )
    if (
        not records
        or records[0]["argv"] != expected_root
        or records[0]["requested_executable"] != root_command_binding["requested_executable"]
        or records[0]["resolved_executable"] != root_command_binding["resolved_executable"]
        or records[0]["executable_sha256"] != root_command_binding["executable_sha256"]
    ):
        raise S10R4Error("strace root Python exec does not match the frozen worker command")
    records[0]["path_containment"] = classify_paths(expected_root, attempt_root)
    records[0]["association_kind"] = "root_python"

    closure = {
        (row["resolved_path"], row["sha256"])
        for row in lock["source_realization"].get("llvm_executable_closure", [])
        if row.get("present") is True
    }
    calls = [] if toolchain_calls is None else toolchain_calls
    required_call_fields = {
        "wrapper_ordinal", "requested_executable", "resolved_executable", "executable_sha256",
        "argv", "cwd", "environment", "return_status", "input_output_paths", "call_api",
    }
    wrapper_occurrences: dict[tuple[str, tuple[str, ...]], int] = {}
    trace_by_key: dict[tuple[str, tuple[str, ...]], list[int]] = {}
    for index, record in enumerate(records[1:], start=1):
        identity = (record["resolved_executable"], record["executable_sha256"])
        if identity not in closure:
            raise S10R4Error(f"strace contains a foreign executable: {record['requested_executable']}")
        key = (record["resolved_executable"], tuple(record["argv"]))
        trace_by_key.setdefault(key, []).append(index)

    matched: set[int] = set()
    normalized_calls: list[dict[str, Any]] = []
    for expected_ordinal, call_record in enumerate(calls):
        if set(call_record) != required_call_fields or call_record.get("wrapper_ordinal") != expected_ordinal:
            raise S10R4Error("toolchain wrapper call record has an inexact field set or ordinal")
        argv = call_record.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
            raise S10R4Error("toolchain wrapper argv is malformed")
        requested = call_record.get("requested_executable")
        if not isinstance(requested, str) or not Path(requested).is_absolute() or argv[0] != requested:
            raise S10R4Error("toolchain wrapper executable is not exact and absolute")
        resolved = Path(requested).resolve(strict=True)
        if (
            call_record.get("resolved_executable") != resolved.as_posix()
            or call_record.get("executable_sha256") != raw_sha256(resolved)
            or (resolved.as_posix(), call_record["executable_sha256"]) not in closure
        ):
            raise S10R4Error("toolchain wrapper executable identity is outside the lock closure")
        cwd = Path(call_record.get("cwd", "")).resolve(strict=True)
        if not isinstance(call_record.get("environment"), dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in call_record["environment"].items()
        ):
            raise S10R4Error("toolchain wrapper environment is malformed")
        classified = classify_paths(argv, cwd)
        recorded_paths = call_record.get("input_output_paths")
        if not isinstance(recorded_paths, list):
            raise S10R4Error("toolchain wrapper input/output path record is malformed")
        projection = [
            {
                "argument_index": row.get("argument_index"),
                "argument": row.get("argument"),
                "resolved_path": row.get("resolved_path"),
                "direction": row.get("direction"),
            }
            for row in recorded_paths
        ]
        expected_projection = [
            {key: row[key] for key in ("argument_index", "argument", "resolved_path", "direction")}
            for row in classified
        ]
        if projection != expected_projection or any(set(row) != {
            "argument_index", "argument", "resolved_path", "direction", "exists_before",
        } for row in recorded_paths):
            raise S10R4Error("toolchain wrapper input/output paths differ from argv")
        key = (resolved.as_posix(), tuple(argv))
        occurrence_rank = wrapper_occurrences.get(key, 0)
        wrapper_occurrences[key] = occurrence_rank + 1
        trace_indices = trace_by_key.get(key, [])
        if occurrence_rank >= len(trace_indices):
            raise S10R4Error("toolchain wrapper invocation lacks its occurrence-ranked strace exec")
        trace_index = trace_indices[occurrence_rank]
        if trace_index in matched:
            raise S10R4Error("toolchain wrapper invocation is multiply matched")
        matched.add(trace_index)
        records[trace_index]["path_containment"] = classified
        records[trace_index]["association_kind"] = "toolchain_wrapper"
        records[trace_index]["wrapper_ordinal"] = expected_ordinal
        records[trace_index]["occurrence_rank"] = occurrence_rank
        normalized_calls.append({**call_record, "occurrence_rank": occurrence_rank})

    for index, record in enumerate(records[1:], start=1):
        if index in matched:
            continue
        record["path_containment"] = classify_paths(record["argv"], None)
        record["association_kind"] = "compiler_driver_descendant"

    if len(matched) != len(calls):
        raise S10R4Error("toolchain wrapper/strace multiset is incomplete")
    if any(record["association_kind"] == "unclassified" for record in records):
        raise S10R4Error("nested exec manifest contains an unclassified record")
    manifest = seal_digest(
        {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": "nested_exec_manifest",
            "root_command_binding": dict(root_command_binding),
            "record_count": len(records),
            "wrapper_call_count": len(calls),
            "wrapper_matched_count": len(matched),
            "driver_descendant_count": sum(
                record["association_kind"] == "compiler_driver_descendant" for record in records
            ),
            "wrapper_calls": normalized_calls,
            "records": records,
        }
    )
    validate_document_schema(manifest)
    atomic_write_json(path.parent / "nested-exec-manifest.json", manifest)
    return manifest


def _results_path_from_config(config_path: Path, attempt_root: Path) -> Path:
    values = []
    for line in config_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("results-file="):
            values.append(line.split("=", 1)[1])
    if len(values) != 1:
        raise S10R4Error("generated ClientParameters.ini results-file field is absent/duplicated")
    path = Path(values[0])
    path = path if path.is_absolute() else config_path.parent / path
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(attempt_root.resolve())
    except ValueError as exc:
        raise S10R4Error("generated result CSV escapes correctness attempt root") from exc
    return resolved


def _correctness_attempt(
    lock: Mapping[str, Any],
    lock_digest: str,
    selected_gpu: Mapping[str, Any],
    row: Mapping[str, Any],
    anchor_index: int,
    size_id: str,
    size: list[int],
    attempt: int,
) -> dict[str, Any]:
    attempt_root = GPU_ROOT / f"correctness/{anchor_index:02d}-{size_id}/attempt-{attempt:02d}"
    attempt_path = attempt_root / "attempt.json"
    if attempt_path.exists():
        document = load_json(attempt_path)
        validate_sealed_digest(document)
        validate_document_schema(document)
        for key, value in {
            "document_kind": "correctness_attempt", "config_hash": row["config_hash"],
            "anchor_index": anchor_index, "size_id": size_id, "attempt": attempt,
            "effective_lock_digest": lock_digest,
        }.items():
            if document.get(key) != value:
                raise S10R4Error(f"correctness attempt resume identity mismatch: {key}")
        card_index = int(selected_gpu["physical_visible_index"])
        expected_request = correctness_build_request(
            config_hash=row["config_hash"], raw_config=row["raw_config"], anchor_index=anchor_index,
            size_id=size_id, size=size, attempt=attempt, attempt_root=attempt_root,
            selected_card=selected_gpu, environment=_worker_environment(card_index=card_index),
            effective_lock_digest=lock_digest,
        )
        request = load_json(attempt_root / "build-request.json")
        if request != expected_request:
            raise S10R4Error("correctness resume build request differs from exact reconstruction")
        build_result = load_json(attempt_root / "build-result.json")
        validate_sealed_digest(build_result)
        validate_document_schema(build_result)
        if (
            build_result.get("input_digest") != request["input_digest"]
            or build_result.get("effective_lock_digest") != lock_digest
            or build_result.get("document_digest") != document.get("build_result_digest")
        ):
            raise S10R4Error("correctness resume build-result association mismatch")
        build_output = build_result.get("outputs", {})
        if document.get("status") == "PASS" or document.get("failure_stage") in ("smoke", "nonzero_correctness"):
            config_path = Path(document["client_parameters_path"]).resolve(strict=True)
            try:
                config_path.relative_to(attempt_root.resolve(strict=True))
            except ValueError as exc:
                raise S10R4Error("correctness resume config escapes attempt root") from exc
            if raw_sha256(config_path) != document["client_parameters_sha256"]:
                raise S10R4Error("correctness resume config digest drift")
            client_exec = load_json(attempt_root / "client-exec.json")
            validate_sealed_digest(client_exec)
            if client_exec.get("document_digest") != document.get("client_exec_digest"):
                raise S10R4Error("correctness resume client-exec association mismatch")
            client = Path(document["client_path"]).resolve(strict=True)
            if (
                client.as_posix() != client_exec.get("argv", [None])[0]
                or raw_sha256(client) != document["client_sha256"]
                or client_exec.get("binary_sha256") != document["client_sha256"]
            ):
                raise S10R4Error("correctness resume client binary drift")
            output_root = attempt_root / "output"
            for record in [*build_output.get("code_objects", []), build_output.get("library")]:
                if not isinstance(record, dict):
                    raise S10R4Error("correctness resume build inventory is incomplete")
                artifact = output_root / record["relative_path"]
                info = artifact.stat(follow_symlinks=False)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_nlink != 1
                    or stat.S_IMODE(info.st_mode) != record["mode"]
                    or info.st_size != record["size_bytes"]
                    or raw_sha256(artifact) != record["sha256"]
                ):
                    raise S10R4Error("correctness resume build artifact drift")
        return document
    attempt_root.mkdir(parents=True, exist_ok=False)
    snapshot = _wait_for_selected_gpu(attempt_root, selected_gpu)
    card_index = int(selected_gpu["physical_visible_index"])
    environment = _worker_environment(card_index=card_index)
    request = correctness_build_request(
        config_hash=row["config_hash"], raw_config=row["raw_config"], anchor_index=anchor_index,
        size_id=size_id, size=size, attempt=attempt, attempt_root=attempt_root,
        selected_card=selected_gpu, environment=environment,
        effective_lock_digest=lock_digest,
    )
    request_path = attempt_root / "build-request.json"
    result_path = attempt_root / "build-result.json"
    atomic_write_json(request_path, request)
    child_argv = materialize_command_template(
        "correctness_build_child", {"attempt_root": attempt_root.resolve().as_posix()}
    )
    child_executable = Path(child_argv[0]).resolve(strict=True)
    root_command_binding = {
        "command_kind": "correctness_build_child",
        "requested_executable": child_argv[0],
        "resolved_executable": child_executable.as_posix(),
        "executable_sha256": raw_sha256(child_executable),
        "argv": child_argv,
        "cwd": attempt_root.resolve(strict=True).as_posix(),
        "environment": environment,
    }
    execve_path = attempt_root / "build-execve.log"
    argv = materialize_command_template(
        "correctness_build_trace", {"attempt_root": attempt_root.resolve().as_posix()}
    )
    if argv[argv.index("--") + 1 :] != child_argv:
        raise S10R4Error("correctness trace/root command materialization mismatch")
    code = _run_logged(argv, attempt_root, environment, attempt_root / "build.stdout", attempt_root / "build.stderr", 7200)
    if code not in (0, 31, 32) or not result_path.is_file():
        raise S10R4Error("correctness build child lacks an allowlisted terminal result")
    build_result = load_json(result_path)
    validate_sealed_digest(build_result)
    build_output = build_result.get("outputs", {})
    if build_output.get("worker_returncode") != code:
        raise S10R4Error("correctness build process/result return-code mismatch")
    exec_manifest = _parse_strace_execve(
        execve_path,
        lock,
        child_argv,
        root_command_binding,
        build_output.get("toolchain_calls"),
    )
    comparable_identity = canonical_sha256(
        {
            "request": {
                key: value
                for key, value in request.items()
                if key not in ("input_digest", "attempt", "cwd")
            },
            "selected_gpu": {
                key: selected_gpu[key]
                for key in (
                    "physical_visible_index", "unique_id", "serial_number", "gfx_version",
                    "compute_partition", "memory_partition",
                )
            },
            "toolchain_closure": lock["source_realization"]["llvm_executable_closure"],
            "worker_template": COMMAND_TEMPLATES["correctness_build_child"],
        }
    )
    if code in (31, 32):
        stage = "generate" if code == 31 else "compile"
        document = seal_digest(
            {
                "schema_version": 1, "checkpoint_id": "S10R4", "document_kind": "correctness_attempt",
                "config_hash": row["config_hash"], "anchor_index": anchor_index, "size_id": size_id,
                "attempt": attempt, "status": "FAIL", "failure_stage": stage,
                "effective_lock_digest": lock_digest,
                "signature": {
                    "config_hash": row["config_hash"], "anchor_index": anchor_index, "size_id": size_id,
                    "failure_stage": stage, "process_returncode": code,
                    "validation_status_and_error_code": None,
                    "source_toolchain_GPU_command_identity": comparable_identity,
                },
                "build_result_digest": build_result["document_digest"],
                "gpu_snapshot": snapshot,
            }
        )
        validate_document_schema(document)
        atomic_write_json(attempt_path, document)
        return document
    config_path = Path(build_output["client_parameters_path"])
    try:
        config_path.resolve(strict=True).relative_to(attempt_root.resolve(strict=True))
    except ValueError as exc:
        raise S10R4Error("correctness client config escapes its attempt root") from exc
    if raw_sha256(config_path) != build_output["client_parameters_sha256"]:
        raise S10R4Error("correctness client config drift after build boundary")
    output_root = attempt_root / "output"
    for record in [*build_output["code_objects"], build_output["library"]]:
        artifact = output_root / record["relative_path"]
        info = artifact.stat(follow_symlinks=False)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != record["mode"]
            or info.st_size != record["size_bytes"]
            or raw_sha256(artifact) != record["sha256"]
        ):
            raise S10R4Error("correctness build artifact drift before client execution")
    csv_path = _results_path_from_config(config_path, attempt_root)
    client = Path(request["prebuilt_client"])
    client_argv = materialize_command_template(
        "correctness_client",
        {"client_path": client.as_posix(), "config_path": config_path.as_posix()},
    )
    client_code = _run_logged(
        client_argv, attempt_root,
        {**FIXED_ENVIRONMENT, "ROCR_VISIBLE_DEVICES": str(card_index)},
        attempt_root / "client.stdout", attempt_root / "client.stderr", 7200,
    )
    csv_paths = [csv_path] if csv_path.is_file() else []
    decision = decide_client_result(client_code, csv_paths, size)
    client_exec = seal_digest(
        {
            "schema_version": 1, "checkpoint_id": "S10R4", "document_kind": "client_exec",
            "argv": client_argv, "cwd": attempt_root.as_posix(),
            "environment": {**FIXED_ENVIRONMENT, "ROCR_VISIBLE_DEVICES": str(card_index)},
            "binary_sha256": raw_sha256(client), "config_sha256": raw_sha256(config_path),
            "code_objects": build_output["code_objects"], "library": build_output["library"],
            "gpu_preflight_digest": canonical_sha256(snapshot), "process_returncode": client_code,
            "result_csv_sha256": raw_sha256(csv_path) if csv_path.is_file() else None,
            "stdout_sha256": raw_sha256(attempt_root / "client.stdout"),
            "stderr_sha256": raw_sha256(attempt_root / "client.stderr"),
        }
    )
    validate_document_schema(client_exec)
    atomic_write_json(attempt_root / "client-exec.json", client_exec)
    signature = {
        "config_hash": row["config_hash"], "anchor_index": anchor_index, "size_id": size_id,
        "failure_stage": decision["failure_stage"], "process_returncode": client_code,
        "validation_status_and_error_code": None if "validation" not in decision else {
            "status": decision["validation"]["validation"],
            "error_code": decision["validation"]["validation_error_code"],
        },
        "source_toolchain_GPU_command_identity": comparable_identity,
    }
    document = seal_digest(
        {
            "schema_version": 1, "checkpoint_id": "S10R4", "document_kind": "correctness_attempt",
            "config_hash": row["config_hash"], "anchor_index": anchor_index, "size_id": size_id,
            "attempt": attempt, "status": decision["status"], "failure_stage": decision["failure_stage"],
            "effective_lock_digest": lock_digest,
            "signature": signature, "validation": decision.get("validation"),
            "build_result_digest": build_result["document_digest"],
            "client_exec_digest": client_exec["document_digest"], "gpu_snapshot": snapshot,
            "client_parameters_path": config_path.as_posix(), "client_parameters_sha256": raw_sha256(config_path),
            "client_path": client.resolve(strict=True).as_posix(), "client_sha256": raw_sha256(client),
        }
    )
    validate_document_schema(document)
    atomic_write_json(attempt_path, document)
    return document


def _correctness_attempt_value(document: Mapping[str, Any]) -> CorrectnessAttempt:
    return CorrectnessAttempt(document["status"], document["failure_stage"], document["signature"])


def _rederive_correctness_summary(lock: Mapping[str, Any], lock_digest: str) -> dict[str, Any]:
    environment = _load_payload(ENVIRONMENT_PATH, "environment")
    selection = _load_payload(SELECTION_PATH, "operational_selection")
    mapping = _load_payload(MAPPING_CORPUS_PATH, "mapping_corpus")
    if environment.get("status") != "PASS" or selection.get("status") != "PASS" or mapping.get("status") != "PASS":
        raise S10R4Error("correctness resume prerequisites are not PASS")
    existing = _load_payload(CORRECTNESS_PATH, "smoke_correctness")
    prefix_count = _exact_correctness_prefix(selection)
    if prefix_count == 0:
        raise S10R4Error("correctness summary has no raw cells")
    if existing.get("status") == "PASS" and prefix_count != 9:
        raise S10R4Error("correctness PASS summary has a non-complete raw prefix")
    if existing.get("status") == "NEGATIVE_CORRECTNESS":
        successful_count = existing.get("cell_count")
        if not isinstance(successful_count, int) or prefix_count != successful_count + 1:
            raise S10R4Error("negative correctness summary/raw prefix boundary mismatch")
    frame = load_json(FRAME_PATH)
    by_hash = {row["config_hash"]: row for row in frame["rows"]}
    selected_rows = [by_hash[value] for value in selection["selected_hashes"]]
    sizes = load_json(SIZE_PATH)["sizes"]
    successful: list[dict[str, Any]] = []
    terminal_failure: dict[str, Any] | None = None
    for anchor_index in anchor_indices(selection["k"]):
        row = selected_rows[anchor_index]
        for size_row in sizes:
            first = _correctness_attempt(
                lock, lock_digest, environment["selected_gpu"], row, anchor_index,
                size_row["size_id"], size_row["value"], 1,
            )
            documents = [first]
            attempts = [_correctness_attempt_value(first)]
            if first["status"] != "PASS":
                second = _correctness_attempt(
                    lock, lock_digest, environment["selected_gpu"], row, anchor_index,
                    size_row["size_id"], size_row["value"], 2,
                )
                documents.append(second)
                attempts.append(_correctness_attempt_value(second))
            outcome = decide_correctness_attempts(attempts)
            if outcome != "correctness_cell_PASS":
                terminal_failure = {
                    "anchor_index": anchor_index,
                    "size_id": size_row["size_id"],
                    "attempt_digests": [item["document_digest"] for item in documents],
                }
                break
            successful_attempt = documents[-1]
            successful.append(
                {
                    "anchor_index": anchor_index, "size_id": size_row["size_id"],
                    "size": size_row["value"], "config_hash": row["config_hash"],
                    "attempt_digest": successful_attempt["document_digest"],
                    "client_parameters_path": successful_attempt["client_parameters_path"],
                    "client_parameters_sha256": successful_attempt["client_parameters_sha256"],
                    "client_path": successful_attempt["client_path"],
                    "client_sha256": successful_attempt["client_sha256"],
                }
            )
        if terminal_failure is not None:
            break
    payload: dict[str, Any] = {
        "status": "PASS" if terminal_failure is None else "NEGATIVE_CORRECTNESS",
        "cell_count": len(successful), "successful_cells": successful,
        "terminal_failure": terminal_failure, "effective_lock_digest": lock_digest,
    }
    if terminal_failure is not None:
        payload.update({"criterion": "S1_ENTRY_BLOCKED", "failure_id": "FT-BLOCKED-CORRECTNESS", "edge": None})
    return _formal_document("smoke_correctness", payload)


def command_correctness(arguments: argparse.Namespace) -> None:
    lock, lock_digest = _formal_admission(arguments)
    if _resume_existing_operational_blocker(lock_digest, "correctness"):
        return
    if CORRECTNESS_PATH.exists():
        payload = _load_payload(CORRECTNESS_PATH, "smoke_correctness")
        if payload.get("effective_lock_digest") != lock_digest:
            raise S10R4Error("correctness resume lock mismatch")
        if _rederive_correctness_summary(lock, lock_digest) != load_json(CORRECTNESS_PATH):
            raise S10R4Error("correctness summary differs from raw terminal-cell recomputation")
        _print({"checkpoint_id": "S10R4", "status": payload["status"], "document_digest": load_json(CORRECTNESS_PATH)["document_digest"]})
        return
    environment = _load_payload(ENVIRONMENT_PATH, "environment")
    if environment.get("status") != "PASS":
        raise S10R4Error("correctness requires GPU environment PASS")
    selected_gpu = environment["selected_gpu"]
    selection = _load_payload(SELECTION_PATH, "operational_selection")
    mapping = _load_payload(MAPPING_CORPUS_PATH, "mapping_corpus")
    if selection.get("status") != "PASS" or mapping.get("status") != "PASS":
        raise S10R4Error("correctness prerequisites are not PASS")
    indices = anchor_indices(selection["k"])
    frame = load_json(FRAME_PATH)
    by_hash = {row["config_hash"]: row for row in frame["rows"]}
    selected_rows = [by_hash[value] for value in selection["selected_hashes"]]
    sizes = load_json(SIZE_PATH)["sizes"]
    successful = []
    terminal_failure = None
    with exclusive_scope(GPU_ROOT / "correctness"):
        for anchor_index in indices:
            row = selected_rows[anchor_index]
            for size_row in sizes:
                first = _correctness_attempt(
                        lock, lock_digest, selected_gpu, row, anchor_index, size_row["size_id"], size_row["value"], 1
                )
                attempts = [_correctness_attempt_value(first)]
                documents = [first]
                if first["status"] != "PASS":
                    second = _correctness_attempt(
                            lock, lock_digest, selected_gpu, row, anchor_index, size_row["size_id"], size_row["value"], 2
                    )
                    attempts.append(_correctness_attempt_value(second))
                    documents.append(second)
                outcome = decide_correctness_attempts(attempts)
                if outcome != "correctness_cell_PASS":
                    terminal_failure = {
                        "anchor_index": anchor_index, "size_id": size_row["size_id"],
                        "attempt_digests": [item["document_digest"] for item in documents],
                    }
                    break
                successful_attempt = documents[-1]
                successful.append(
                    {
                        "anchor_index": anchor_index, "size_id": size_row["size_id"],
                        "size": size_row["value"], "config_hash": row["config_hash"],
                        "attempt_digest": successful_attempt["document_digest"],
                        "client_parameters_path": successful_attempt["client_parameters_path"],
                        "client_parameters_sha256": successful_attempt["client_parameters_sha256"],
                        "client_path": successful_attempt["client_path"],
                        "client_sha256": successful_attempt["client_sha256"],
                    }
                )
            if terminal_failure:
                break
    payload = {
        "status": "PASS" if terminal_failure is None else "NEGATIVE_CORRECTNESS",
        "cell_count": len(successful), "successful_cells": successful,
        "terminal_failure": terminal_failure, "effective_lock_digest": lock_digest,
    }
    if terminal_failure:
        payload.update({"criterion": "S1_ENTRY_BLOCKED", "failure_id": "FT-BLOCKED-CORRECTNESS", "edge": None})
    document = _write_formal(CORRECTNESS_PATH, "smoke_correctness", payload)
    _print({"checkpoint_id": "S10R4", "status": payload["status"], "document_digest": document["document_digest"]})


def _load_noise_observation(path: Path, expected: Mapping[str, Any]) -> dict[str, Any]:
    document = load_json(path)
    validate_document_schema(document)
    if document.get("document_kind") != "noise_observation":
        raise S10R4Error("noise resume document kind mismatch")
    if canonical_sha256({key: value for key, value in document.items() if key != "document_digest"}) != document.get("document_digest"):
        raise S10R4Error("noise resume document digest mismatch")
    for key, value in expected.items():
        if document.get(key) != value:
            raise S10R4Error(f"noise resume identity mismatch: {key}")
    quality = document.get("quality_gflops")
    if (
        not isinstance(quality, (int, float))
        or isinstance(quality, bool)
        or not math.isfinite(float(quality))
        or quality <= 0
    ):
        raise S10R4Error("noise resume quality is not positive")
    return document


def _noise_observation(
    selected_gpu: Mapping[str, Any],
    cell: Mapping[str, Any],
    repeat: int,
    lock_digest: str,
) -> dict[str, Any]:
    group_id = f"{int(cell['anchor_index']):02d}-{cell['size_id']}"
    slot_root = GPU_ROOT / f"noise/{group_id}/repeat-{repeat:02d}"
    observation_path = slot_root / "observation.json"
    identity = {
        "config_hash": cell["config_hash"],
        "anchor_index": cell["anchor_index"],
        "size_id": cell["size_id"],
        "repeat": repeat,
        "effective_lock_digest": lock_digest,
    }
    if observation_path.exists():
        return _load_noise_observation(observation_path, identity)
    slot_root.mkdir(parents=True, exist_ok=False)
    snapshot = _wait_for_selected_gpu(slot_root, selected_gpu)
    source_config = Path(cell["client_parameters_path"]).resolve(strict=True)
    source_root = (GPU_ROOT / "correctness").resolve(strict=True)
    try:
        source_config.relative_to(source_root)
    except ValueError as exc:
        raise S10R4Error("noise source config is outside the reached correctness scope") from exc
    if raw_sha256(source_config) != cell["client_parameters_sha256"]:
        raise S10R4Error("noise source config differs from the successful correctness input")
    csv_path = slot_root / "result.csv"
    config_path = slot_root / "ClientParameters.ini"
    rewritten = rewrite_results_file(source_config.read_bytes(), csv_path)
    atomic_write_bytes(config_path, rewritten)
    if config_path.read_bytes() != rewrite_results_file(source_config.read_bytes(), csv_path):
        raise S10R4Error("noise config rewrite is not byte-deterministic")
    expected_client = (BUILD_ROOT / "native/build/hipblaslt/tensilelite/client/tensilelite-client").resolve(strict=True)
    client = Path(cell["client_path"]).resolve(strict=True)
    if client != expected_client or raw_sha256(client) != cell["client_sha256"]:
        raise S10R4Error("noise client differs from its successful correctness input")
    card_index = int(selected_gpu["physical_visible_index"])
    environment = {**FIXED_ENVIRONMENT, "ROCR_VISIBLE_DEVICES": str(card_index)}
    argv = materialize_command_template(
        "noise_client",
        {
            "client_path": client.as_posix(),
            "config_path": config_path.resolve(strict=True).as_posix(),
        },
    )
    code = _run_logged(
        argv, slot_root, environment, slot_root / "stdout.log", slot_root / "stderr.log", 7200
    )
    if code != 0 or not csv_path.is_file():
        raise S10R4Error("noise client did not complete with its exact CSV")
    parsed = parse_single_result_csv(csv_path, cell["size"])
    if parsed["validation"] != "PASSED":
        raise S10R4Error("noise result validation is not PASSED")
    document = seal_digest(
        {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": "noise_observation",
            **identity,
            "size": cell["size"],
            "source_correctness_attempt_digest": cell["attempt_digest"],
            "source_client_parameters": {
                "path": source_config.as_posix(),
                "sha256": cell["client_parameters_sha256"],
            },
            "client": {"path": client.as_posix(), "sha256": raw_sha256(client)},
            "argv": argv,
            "cwd": slot_root.resolve(strict=True).as_posix(),
            "environment": environment,
            "gpu_snapshot": snapshot,
            "process_returncode": code,
            "config_sha256": raw_sha256(config_path),
            "result_csv_sha256": raw_sha256(csv_path),
            "stdout_sha256": raw_sha256(slot_root / "stdout.log"),
            "stderr_sha256": raw_sha256(slot_root / "stderr.log"),
            "quality_gflops": parsed["quality_gflops"],
            "winner_time_us": parsed["winner_time_us"],
        }
    )
    validate_document_schema(document)
    atomic_write_json(observation_path, document)
    return document


def _rederive_noise_summary(lock_digest: str) -> dict[str, Any]:
    correctness = _load_payload(CORRECTNESS_PATH, "smoke_correctness")
    selection = _load_payload(SELECTION_PATH, "operational_selection")
    cells = correctness.get("successful_cells")
    if correctness.get("status") != "PASS" or not isinstance(cells, list) or len(cells) != 9:
        raise S10R4Error("noise resume lacks nine successful correctness cells")
    if _exact_noise_prefix(selection) != 63:
        raise S10R4Error("noise summary does not have the exact 63-observation raw prefix")
    groups: dict[str, list[float]] = {}
    observation_digests: dict[str, list[str]] = {}
    for cell in cells:
        group_id = f"{int(cell['anchor_index']):02d}-{cell['size_id']}"
        groups[group_id] = []
        observation_digests[group_id] = []
        for repeat in range(1, 8):
            observation = _load_noise_observation(
                GPU_ROOT / f"noise/{group_id}/repeat-{repeat:02d}/observation.json",
                {
                    "config_hash": cell["config_hash"],
                    "anchor_index": cell["anchor_index"],
                    "size_id": cell["size_id"],
                    "repeat": repeat,
                    "effective_lock_digest": lock_digest,
                },
            )
            groups[group_id].append(float(observation["quality_gflops"]))
            observation_digests[group_id].append(observation["document_digest"])
    aggregate = aggregate_noise(groups)
    payload = {
        "status": "PASS" if aggregate["cv_pass"] else "INCONCLUSIVE_NOISE",
        "criterion": None,
        "failure_id": None if aggregate["cv_pass"] else "FT-INCONCLUSIVE",
        "edge": None,
        "observation_digests": observation_digests,
        "aggregate": aggregate,
        "effective_lock_digest": lock_digest,
    }
    return _formal_document("noise_pilot", payload)


def command_noise(arguments: argparse.Namespace) -> None:
    _, lock_digest = _formal_admission(arguments)
    if _resume_existing_operational_blocker(lock_digest, "noise"):
        return
    if NOISE_PATH.exists():
        payload = _load_payload(NOISE_PATH, "noise_pilot")
        if payload.get("effective_lock_digest") != lock_digest:
            raise S10R4Error("noise resume lock mismatch")
        if _rederive_noise_summary(lock_digest) != load_json(NOISE_PATH):
            raise S10R4Error("noise summary differs from all 63 raw observation recomputation")
        _print({"checkpoint_id": "S10R4", "status": payload["status"], "document_digest": load_json(NOISE_PATH)["document_digest"]})
        return
    environment = _load_payload(ENVIRONMENT_PATH, "environment")
    correctness = _load_payload(CORRECTNESS_PATH, "smoke_correctness")
    if environment.get("status") != "PASS" or correctness.get("status") != "PASS":
        raise S10R4Error("noise requires environment and all correctness cells PASS")
    cells = correctness.get("successful_cells")
    if not isinstance(cells, list) or len(cells) != 9:
        raise S10R4Error("noise requires exactly nine successful correctness cells")
    selection = _load_payload(SELECTION_PATH, "operational_selection")
    expected_cells = [
        (anchor, size_id)
        for anchor in anchor_indices(selection["k"])
        for size_id in ("size-00", "size-01", "size-02")
    ]
    observed_cells = [(cell.get("anchor_index"), cell.get("size_id")) for cell in cells]
    if observed_cells != expected_cells:
        raise S10R4Error("noise correctness-cell order/identity differs from the exact 3x3 panel")
    groups: dict[str, list[float]] = {}
    observation_digests: dict[str, list[str]] = {}
    with exclusive_scope(GPU_ROOT / "noise"):
        for cell in cells:
            group_id = f"{int(cell['anchor_index']):02d}-{cell['size_id']}"
            if group_id in groups:
                raise S10R4Error("duplicate correctness group admitted to noise")
            groups[group_id] = []
            observation_digests[group_id] = []
            for repeat in range(1, 8):
                observation = _noise_observation(environment["selected_gpu"], cell, repeat, lock_digest)
                groups[group_id].append(float(observation["quality_gflops"]))
                observation_digests[group_id].append(observation["document_digest"])
    aggregate = aggregate_noise(groups)
    payload = {
        "status": "PASS" if aggregate["cv_pass"] else "INCONCLUSIVE_NOISE",
        "criterion": None,
        "failure_id": None if aggregate["cv_pass"] else "FT-INCONCLUSIVE",
        "edge": None,
        "observation_digests": observation_digests,
        "aggregate": aggregate,
        "effective_lock_digest": lock_digest,
    }
    document = _write_formal(NOISE_PATH, "noise_pilot", payload)
    _print({"checkpoint_id": "S10R4", "status": payload["status"], "document_digest": document["document_digest"]})


def _classification_and_selection_facts() -> tuple[dict[str, Any], dict[str, Any]]:
    classification = _load_payload(CLASSIFICATION_PATH, "codegen_classification")
    selection = _load_payload(SELECTION_PATH, "operational_selection")
    if classification.get("child_count") != 228 or classification.get("row_count") != 114:
        raise S10R4Error("classification is not the complete 114x2 census")
    rows = classification.get("rows")
    if not isinstance(rows, list) or len(rows) != 114:
        raise S10R4Error("classification row set is incomplete")
    return classification, selection


def _decision_facts() -> dict[str, Any]:
    frame = load_json(FRAME_PATH)
    validate_exact_frame_registry(frame)
    classification, selection = _classification_and_selection_facts()
    greedy_steps = selection.get("greedy_steps", [])
    mandatory_atoms = selection.get("mandatory_atoms", [])
    full_cover = (
        selection.get("status") == "PASS"
        and (
            not mandatory_atoms
            or (isinstance(greedy_steps, list) and bool(greedy_steps) and not greedy_steps[-1].get("remaining_atoms"))
        )
    )
    facts: dict[str, Any] = {
        "changes_required": False,
        "operational_blocked": False,
        "negative_mapping": selection.get("status") == "NEGATIVE_MAPPING",
        "negative_correctness": False,
        "inconclusive_noise": False,
        "exact_frame_integrity_pass": True,
        "all_228_codegen_children_stably_classified": classification.get("child_count") == 228,
        "stable_survivor_count_at_least_10": classification.get("survivor_count", -1) >= 10,
        "full_mandatory_cover": full_cover,
        "k_at_most_20": selection.get("status") == "PASS" and 10 <= selection.get("k", -1) <= 20,
        "mapping_a_b_pass": False,
        "native_conformance_pass": False,
        "all_9_correctness_cells_pass": False,
        "all_63_noise_cells_complete_and_pass": False,
    }
    if facts["negative_mapping"]:
        return facts
    mapping = _load_payload(MAPPING_CORPUS_PATH, "mapping_corpus")
    if mapping.get("status") == "NEGATIVE_MAPPING":
        facts["negative_mapping"] = True
        return facts
    facts["mapping_a_b_pass"] = mapping.get("status") == "PASS"
    conformance = _load_payload(CONFORMANCE_PATH, "sentinel_conformance")
    facts["native_conformance_pass"] = conformance.get("status") == "PASS"
    correctness = _load_payload(CORRECTNESS_PATH, "smoke_correctness")
    if correctness.get("status") == "NEGATIVE_CORRECTNESS":
        facts["negative_correctness"] = True
        return facts
    facts["all_9_correctness_cells_pass"] = (
        correctness.get("status") == "PASS"
        and correctness.get("cell_count") == 9
        and len(correctness.get("successful_cells", [])) == 9
    )
    noise = _load_payload(NOISE_PATH, "noise_pilot")
    if noise.get("status") == "INCONCLUSIVE_NOISE":
        facts["inconclusive_noise"] = True
        return facts
    aggregate = noise.get("aggregate", {})
    facts["all_63_noise_cells_complete_and_pass"] = (
        noise.get("status") == "PASS"
        and aggregate.get("repeat_count") == 63
        and aggregate.get("group_count") == 9
        and aggregate.get("cv_pass") is True
    )
    return facts


def _terminal_report_bytes(outcome: Mapping[str, Any], decision_digest: str) -> bytes:
    lines = [
        "# S10R4 Stage-1 exact-frame entry report",
        "",
        "This is the mechanically generated terminal formal report for the fixture-only S10R4 claim.",
        "",
        f"- Scientific outcome: `{outcome['scientific_outcome']}`",
        f"- Criterion: `{outcome['criterion']}`",
        f"- Failure ID: `{outcome['failure_id']}`",
        f"- Edge: `{outcome['edge']}`",
        f"- Decision digest: `{decision_digest}`",
        "- Verification status: `RESULT_PENDING_FRESH_VERIFICATION`",
        "",
        "This report is not fresh verification, closeout, or a general support/performance claim.",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _ordinary_report_record(path: Path) -> dict[str, Any]:
    info = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise S10R4Error("terminal report is not one ordinary file")
    return {
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "mode": stat.S_IMODE(info.st_mode),
        "size_bytes": info.st_size,
        "raw_sha256": raw_sha256(path),
    }


def _expected_decision_materialization(
    lock_digest: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], bytes]:
    facts = _decision_facts()
    outcome = decide_outcome(facts)
    payload = {
        **outcome,
        "execution_status": "completed",
        "checkpoint_state": "RUNNING",
        "verification_status": "RESULT_PENDING_FRESH_VERIFICATION",
        "facts": facts,
        "effective_lock_digest": lock_digest,
    }
    decision = _formal_document("decision", payload)
    report = _terminal_report_bytes(outcome, decision["document_digest"])
    return facts, outcome, decision, report


def _expected_gate_record(
    outcome: Mapping[str, Any], decision: Mapping[str, Any], lock_digest: str
) -> dict[str, Any]:
    return _formal_document(
        "positive_gate_record",
        {
            **outcome,
            "qualified_edge_token": "S10R4:S1_ENTRY_GO_EXACT_FRAME",
            "decision_digest": decision["document_digest"],
            "decision_projection_sha256": canonical_sha256(outcome),
            "report": _ordinary_report_record(REPORT_PATH),
            "effective_lock_digest": lock_digest,
        },
    )


def _validate_decision_overlay(lock_digest: str) -> dict[str, Any]:
    _, outcome, expected_decision, expected_report = _expected_decision_materialization(
        lock_digest
    )
    if load_json(DECISION_PATH) != expected_decision:
        raise S10R4Error("existing decision differs from deterministic recomputation")
    if not REPORT_PATH.is_file() or REPORT_PATH.read_bytes() != expected_report:
        raise S10R4Error("canonical decision lacks its exact terminal report")
    if outcome["scientific_outcome"] == "positive":
        if not GATE_RECORD_PATH.is_file() or load_json(GATE_RECORD_PATH) != _expected_gate_record(
            outcome, expected_decision, lock_digest
        ):
            raise S10R4Error("positive decision lacks its exact gate record")
    elif GATE_RECORD_PATH.exists():
        raise S10R4Error("non-positive decision cannot coexist with a positive gate record")
    return expected_decision["payload"]


def command_decision(arguments: argparse.Namespace) -> None:
    _, lock_digest = _formal_admission(arguments)
    if BLOCKER_PATH.exists():
        raise S10R4Error("operational BLOCKED permits only the blocker document, not a decision")
    _, outcome, expected_decision, expected_report = _expected_decision_materialization(
        lock_digest
    )
    if DECISION_PATH.exists():
        decision = load_json(DECISION_PATH)
        if decision != expected_decision:
            raise S10R4Error("existing decision differs from deterministic recomputation")
    else:
        atomic_write_json(DECISION_PATH, expected_decision)
        decision = expected_decision
    if REPORT_PATH.exists():
        if REPORT_PATH.read_bytes() != expected_report:
            raise S10R4Error("existing terminal report differs from deterministic construction")
    else:
        atomic_write_bytes(REPORT_PATH, expected_report)
    if outcome["scientific_outcome"] == "positive":
        expected_gate = _expected_gate_record(outcome, decision, lock_digest)
        if GATE_RECORD_PATH.exists():
            if load_json(GATE_RECORD_PATH) != expected_gate:
                raise S10R4Error("existing positive gate record differs from deterministic construction")
        else:
            atomic_write_json(GATE_RECORD_PATH, expected_gate)
    elif GATE_RECORD_PATH.exists():
        raise S10R4Error("non-positive decision cannot coexist with a positive gate record")
    _validate_decision_overlay(lock_digest)
    _print({"checkpoint_id": "S10R4", **outcome, "decision_digest": decision["document_digest"]})


def _recompute_classification_and_selection() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    frame = load_json(FRAME_PATH)
    pass_a = _census_results("A")
    pass_b = _census_results("B")
    rows: list[dict[str, Any]] = []
    survivors: list[dict[str, Any]] = []
    for frame_row, left, right in zip(frame["rows"], pass_a, pass_b):
        if left.get("config_hash") != frame_row["config_hash"] or right.get("config_hash") != frame_row["config_hash"]:
            raise S10R4Error("classification raw census/frame association drift")
        stable = stable_classify(left["outputs"], right["outputs"])
        rows.append(
            {
                "registry_index": frame_row["registry_index"],
                "config_hash": frame_row["config_hash"],
                "stable_class": stable,
                "pass_a_completion_digest": left["completion_digest"],
                "pass_b_completion_digest": right["completion_digest"],
            }
        )
        if stable == "operational_codegen_witnessed":
            survivors.append(frame_row)
    classification, selection = _classification_and_selection_facts()
    if rows != classification["rows"] or len(survivors) != classification["survivor_count"]:
        raise S10R4Error("reproduction classification differs from the formal classification")
    lock_digest = classification.get("effective_lock_digest")
    expected_classification = _formal_document(
        "codegen_classification",
        {
            "status": "PASS", "frame_registry_digest": frame["registry_digest"],
            "effective_lock_digest": lock_digest, "pass_count": 2, "child_count": 228,
            "row_count": 114, "survivor_count": len(survivors), "rows": rows,
        },
    )
    if expected_classification != load_json(CLASSIFICATION_PATH):
        raise S10R4Error("classification summary differs from all 228 raw child recomputation")
    if selection.get("status") == "PASS":
        candidate_registry = load_json(
            REPO_ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r3-candidate-atom-registry.json"
        )
        recomputed = selection_to_document(
            deterministic_select(
                [witness_from_frame_row(row) for row in survivors],
                [row["atom_id"] for row in candidate_registry["rows"]],
            )
        )
        for key in (
            "selector_id", "mandatory_atoms", "operational_atoms", "survivor_hashes",
            "greedy_steps", "c_greedy", "k", "selected_hashes",
        ):
            if recomputed[key] != selection[key]:
                raise S10R4Error(f"reproduction selection mismatch: {key}")
        expected_selection_payload = {
            **recomputed,
            "status": "PASS",
            "classification_digest": expected_classification["document_digest"],
            "effective_lock_digest": lock_digest,
        }
    else:
        candidate_registry = load_json(
            REPO_ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r3-candidate-atom-registry.json"
        )
        try:
            deterministic_select(
                [witness_from_frame_row(row) for row in survivors],
                [row["atom_id"] for row in candidate_registry["rows"]],
            )
        except S10R4Error as exc:
            if "FT-BLOCKED-MAPPING" not in str(exc):
                raise
        else:
            raise S10R4Error("reproduction selection unexpectedly admits an operational cover")
        if selection.get("status") != "NEGATIVE_MAPPING" or selection.get("survivor_hashes") != sorted(
            row["config_hash"] for row in survivors
        ):
            raise S10R4Error("reproduction negative selection differs from deterministic reconstruction")
        try:
            deterministic_select(
                [witness_from_frame_row(row) for row in survivors],
                [row["atom_id"] for row in candidate_registry["rows"]],
            )
        except S10R4Error as exc:
            reason = str(exc)
        else:  # pragma: no cover - guarded above
            raise S10R4Error("negative selection unexpectedly became positive")
        expected_selection_payload = {
            "status": "NEGATIVE_MAPPING", "criterion": "S1_ENTRY_BLOCKED",
            "failure_id": "FT-BLOCKED-MAPPING", "edge": None, "reason": reason,
            "survivor_hashes": sorted(row["config_hash"] for row in survivors),
            "classification_digest": expected_classification["document_digest"],
            "effective_lock_digest": lock_digest,
        }
    if _formal_document("operational_selection", expected_selection_payload) != load_json(SELECTION_PATH):
        raise S10R4Error("selection summary differs from deterministic raw-child recomputation")
    return classification, selection, survivors


def _reproduction_validate_reached(
    selection: Mapping[str, Any], decision: Mapping[str, Any], lock_digest: str
) -> dict[str, Any]:
    if selection.get("status") != "PASS":
        return _decision_facts()
    mapping = _load_payload(MAPPING_CORPUS_PATH, "mapping_corpus")
    frame = load_json(FRAME_PATH)
    by_hash = {row["config_hash"]: row for row in frame["rows"]}
    selected_rows = [by_hash[value] for value in selection["selected_hashes"]]
    if mapping.get("status") == "PASS":
        pass_a_terminal, raw_pass_a, _ = _mapping_pass_terminal(
            "A", selected_rows, lock_digest, existing_only=True
        )
        pass_b_terminal, raw_pass_b, _ = _mapping_pass_terminal(
            "B", selected_rows, lock_digest, existing_only=True
        )
        if pass_a_terminal != "mapping_pass_PASS" or pass_b_terminal != "mapping_pass_PASS":
            raise S10R4Error("reproduction raw mapping terminal differs from PASS corpus")
        if raw_pass_a != mapping["pass_a_rows"] or raw_pass_b != mapping["pass_b_rows"]:
            raise S10R4Error("reproduction mapping corpus differs from raw terminal attempts")
        validate_mapping_batch(mapping["pass_a_rows"], selection["selected_hashes"], "A")
        validate_mapping_batch(mapping["pass_b_rows"], selection["selected_hashes"], "B")
        compare_mapping_passes(mapping["pass_a_rows"], mapping["pass_b_rows"])
    elif mapping.get("status") == "NEGATIVE_MAPPING":
        failing_pass = mapping.get("failing_pass")
        if failing_pass not in ("A", "B"):
            raise S10R4Error("reproduction negative mapping lacks its failing pass")
        terminal, _, children = _mapping_pass_terminal(
            failing_pass, selected_rows, lock_digest, existing_only=True
        )
        if terminal == "mapping_pass_PASS" or [row["completion_digest"] for row in children] != mapping.get(
            "attempt_digests"
        ):
            raise S10R4Error("reproduction negative mapping differs from raw terminal attempts")
    if CONFORMANCE_PATH.exists():
        conformance = _load_payload(CONFORMANCE_PATH, "sentinel_conformance")
        if conformance.get("status") == "PASS":
            fixture = load_json(FIXTURE_PATH)
            transcript_path = REPO_ROOT / conformance["transcript"]["path"]
            if raw_sha256(transcript_path) != conformance["transcript"]["raw_sha256"]:
                raise S10R4Error("reproduction native transcript digest differs from conformance binding")
            transcript = load_json(transcript_path)
            validate_native_transcript(fixture, transcript)
    if CORRECTNESS_PATH.exists():
        correctness = _load_payload(CORRECTNESS_PATH, "smoke_correctness")
        for cell in correctness.get("successful_cells", []):
            attempt_path = GPU_ROOT / f"correctness/{int(cell['anchor_index']):02d}-{cell['size_id']}/attempt-01/attempt.json"
            attempt = load_json(attempt_path)
            if attempt.get("document_digest") != cell["attempt_digest"] or attempt.get("status") != "PASS":
                raise S10R4Error("reproduction correctness cell association mismatch")
    if NOISE_PATH.exists():
        noise = _load_payload(NOISE_PATH, "noise_pilot")
        groups: dict[str, list[float]] = {}
        correctness = _load_payload(CORRECTNESS_PATH, "smoke_correctness")
        cells = {
            f"{int(cell['anchor_index']):02d}-{cell['size_id']}": cell
            for cell in correctness.get("successful_cells", [])
        }
        for group_id, digests in noise["observation_digests"].items():
            if group_id not in cells:
                raise S10R4Error("reproduction noise group lacks a successful correctness source")
            cell = cells[group_id]
            groups[group_id] = []
            for repeat, expected_digest in enumerate(digests, start=1):
                observation_path = GPU_ROOT / f"noise/{group_id}/repeat-{repeat:02d}/observation.json"
                observation = _load_noise_observation(
                    observation_path,
                    {
                        "config_hash": cell["config_hash"],
                        "anchor_index": cell["anchor_index"],
                        "size_id": cell["size_id"],
                        "repeat": repeat,
                        "effective_lock_digest": lock_digest,
                    },
                )
                if observation["document_digest"] != expected_digest:
                    raise S10R4Error("reproduction noise observation association mismatch")
                groups[group_id].append(float(observation["quality_gflops"]))
        if aggregate_noise(groups) != noise["aggregate"]:
            raise S10R4Error("reproduction noise aggregate differs from formal aggregate")
    facts = _decision_facts()
    reproduced = decide_outcome(facts)
    for key in ("scientific_outcome", "criterion", "failure_id", "edge"):
        if reproduced[key] != decision[key]:
            raise S10R4Error(f"reproduction decision mismatch: {key}")
    return facts


def _expected_reproduction_result(lock_digest: str) -> dict[str, Any]:
    replay = replay_exact_frame(RAW_ROOT)
    if canonical_json(replay, newline=True) != FRAME_PATH.read_bytes():
        raise S10R4Error("reproduction exact-frame replay differs byte-for-byte")
    _, selection, _ = _recompute_classification_and_selection()
    decision = _validate_decision_overlay(lock_digest)
    facts = _reproduction_validate_reached(selection, decision, lock_digest)
    document = {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        "document_kind": "reproduction_result",
        "identity": {"reproduction_id": "s10r4-independent-raw-to-decision-v1"},
        "effective_lock_digest": lock_digest,
        "input_digest": canonical_sha256(
            {
                "frame": raw_sha256(FRAME_PATH),
                "decision": canonical_sha256(decision),
                "lock": lock_digest,
            }
        ),
        "cwd": REPO_ROOT.resolve(strict=True).as_posix(),
        "argv": materialize_command_template("reproduction"),
        "environment": FIXED_ENVIRONMENT,
        "outputs": {
            "status": "PASS",
            "recomputed_facts": facts,
            "outcome": {
                key: decision[key]
                for key in ("scientific_outcome", "criterion", "failure_id", "edge")
            },
            "new_outcome_workload_executed": False,
        },
        "artifact_inventory": [],
    }
    document["completion_digest"] = completion_digest(document)
    validate_document_schema(document)
    validate_child(document, {"document_kind": "reproduction_result"})
    return document


def _validate_reproduction_overlay(lock_digest: str, output: Path) -> dict[str, Any]:
    expected = _expected_reproduction_result(lock_digest)
    observed = load_json(output)
    if observed != expected:
        raise S10R4Error("existing reproduction differs from deterministic raw recomputation")
    return expected


def command_reproduction(arguments: argparse.Namespace) -> None:
    _, lock_digest = _formal_admission(arguments)
    output = _relative_argument(arguments.output, REPRODUCTION_ROOT / "s10r4-independent-result.json", name="reproduction output")
    if not DECISION_PATH.is_file():
        raise S10R4Error("reproduction requires the canonical decision")
    document = _expected_reproduction_result(lock_digest)
    finalize_child(output, document, {"document_kind": "reproduction_result"})
    if load_json(output) != document:
        raise S10R4Error("reproduction finalized bytes differ from deterministic construction")
    _print({"checkpoint_id": "S10R4", "status": "REPRODUCTION_PASS", "completion_digest": load_json(output)["completion_digest"]})


def command_internal_worker(arguments: argparse.Namespace) -> int:
    request_path = Path(arguments.request).resolve(strict=True)
    result_path = Path(arguments.result).resolve(strict=False)
    if result_path.exists() or request_path.parent != result_path.parent:
        raise S10R4Error("formal worker request/result boundary mismatch")
    request = load_json(request_path)
    expected_kind = {
        "_census-child": "census_request",
        "_mapping-child": "mapping_request",
        "_correctness-build-child": "correctness_build_request",
    }[arguments.command]
    if request.get("checkpoint_id") != "S10R4" or request.get("document_kind") != expected_kind:
        raise S10R4Error("formal worker request identity mismatch")
    stored_digest = request.get("input_digest")
    projection = {key: value for key, value in request.items() if key != "input_digest"}
    if not isinstance(stored_digest, str) or canonical_sha256(projection) != stored_digest:
        raise S10R4Error("formal worker request digest mismatch")
    if Path.cwd().resolve().as_posix() != request.get("cwd"):
        raise S10R4Error("formal worker cwd differs from its request")
    observed_environment = {key: os.environ.get(key) for key in request.get("environment", {})}
    if observed_environment != request.get("environment") or set(os.environ) != set(request.get("environment", {})):
        raise S10R4Error("formal worker process environment differs from its exact request")
    if arguments.command in ("_census-child", "_mapping-child"):
        validate_environment(request["environment"], worker_pythonpath=WORKER_PYTHONPATH)
    else:
        expected = _worker_environment(card_index=int(request["selected_gpu"]["physical_visible_index"]))
        if request["environment"] != expected:
            raise S10R4Error("correctness worker environment/card binding mismatch")
    handlers = {
        "_census-child": execute_census_worker,
        "_mapping-child": execute_mapping_worker,
        "_correctness-build-child": execute_correctness_build_worker,
    }
    return int(handlers[arguments.command](request, result_path))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="run_s10r4_entry.py", allow_abbrev=False)
    subcommands = root.add_subparsers(dest="command", required=True)
    validate = subcommands.add_parser("validate-contract", allow_abbrev=False)
    validate.set_defaults(handler=command_validate_contract)
    prepare = subcommands.add_parser("prepare-prelabel", allow_abbrev=False)
    prepare.add_argument("--raw-root", required=True)
    prepare.add_argument("--build-root", required=True)
    prepare.add_argument("--fixture-root", required=True)
    prepare.add_argument("--frame-registry", required=True)
    prepare.add_argument("--size-registry", required=True)
    prepare.add_argument("--native-fixture", required=True)
    prepare.set_defaults(handler=command_prepare_prelabel)
    verify = subcommands.add_parser("verify-prelabel", allow_abbrev=False)
    verify.set_defaults(handler=command_verify_prelabel)
    build_lock = subcommands.add_parser("build-lock", allow_abbrev=False)
    build_lock.add_argument("--output", required=True)
    build_lock.set_defaults(handler=command_build_lock)
    verify_lock = subcommands.add_parser("verify-lock", allow_abbrev=False)
    verify_lock.add_argument("--lock", required=True)
    verify_lock.set_defaults(handler=command_verify_lock)
    handlers = {
        "classify-select": command_classify_select,
        "native-conformance": command_native_conformance,
        "gpu-environment": command_gpu_environment,
        "correctness": command_correctness,
        "noise": command_noise,
        "decision": command_decision,
    }
    for name, handler in handlers.items():
        formal = subcommands.add_parser(name, allow_abbrev=False)
        formal.add_argument("--lock", required=True)
        formal.set_defaults(handler=handler)
    for name, handler in (("census", command_census), ("mapping", command_mapping)):
        formal = subcommands.add_parser(name, allow_abbrev=False)
        formal.add_argument("--pass-id", choices=("A", "B"), required=True)
        formal.add_argument("--lock", required=True)
        formal.set_defaults(handler=handler)
    reproduction = subcommands.add_parser("reproduction", allow_abbrev=False)
    reproduction.add_argument("--lock", required=True)
    reproduction.add_argument("--output", required=True)
    reproduction.set_defaults(handler=command_reproduction)
    for name in ("_census-child", "_mapping-child", "_correctness-build-child"):
        worker = subcommands.add_parser(name, allow_abbrev=False)
        worker.add_argument("--request", required=True)
        worker.add_argument("--result", required=True)
        worker.set_defaults(handler=command_internal_worker)
    return root


def main() -> int:
    try:
        _require_fixed_runtime()
        arguments = parser().parse_args()
        _admit_current_argv(arguments)
        return int(arguments.handler(arguments) or 0)
    except S10R4Error as exc:
        print(f"S10R4_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # unknowns never become scientific evidence
        print(f"S10R4_FAIL_CLOSED: unexpected {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
