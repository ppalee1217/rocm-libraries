# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Strict native Formocast/runtime transcript comparison for S10R4."""

from __future__ import annotations

import copy
import math
import os
import stat
import struct
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contract import (
    FIXED_ENVIRONMENT,
    S10R4Error,
    atomic_write_bytes,
    atomic_write_json,
    canonical_sha256,
    document_record,
    load_json,
    materialize_command_template,
    raw_sha256,
    require_exact_keys,
    seal_digest,
    validate_document_schema,
)


FIXTURE_PAYLOAD_SHA256 = "f0b15e5bfe263b1378d5627c7307fda1c0a52569b7784c3fc0df51358510191d"
FIXTURE_KEYS = (
    "base_size_mapping",
    "checkpoint_id",
    "derivation",
    "document_kind",
    "early_terminate",
    "expected_guard_trace",
    "expected_queues",
    "expected_tie_sets",
    "fixture_id",
    "guard_order",
    "input_header",
    "outcome_blind",
    "problem",
    "rows",
    "schema_version",
    "thresholds",
    "validity_mask",
)
GUARD_PREDICATES = (
    ("global-split-u-zero", "GlobalSplitU == 0"),
    (
        "small-mn-macro-tile-gap",
        "(M < 128 && MT0 - M >= 16) || (N < 128 && MT1 - N >= 16)",
    ),
    (
        "large-mn-macro-tile-gap",
        "(M >= 128 && MT0 - M >= 32) || (N >= 128 && MT1 - N >= 32)",
    ),
    (
        "bf16-half-depthu-k-batch-mi",
        "BF16_or_Half && bpeA==2 && bpeB==2 && depthU_K_condition && NumBatches<NumCUs && matrixInstruction[2]>=32",
    ),
    ("direct-to-lds-a-small-m", "DirectToLdsA && M < MT0"),
    ("direct-to-lds-b-small-n", "DirectToLdsB && N < MT1"),
    ("derived-plr-zero", "PLR == 0"),
)


MAPPING_FIELD_ORDER = (
    "waveNum",
    "macroTile",
    "matrixInstruction",
    "grvwA",
    "grvwB",
    "gwvwC",
    "gwvwD",
    "depthU",
    "globalSplitU",
    "workGroupMapping",
    "globalAccumulation",
    "workGroupMappingXCC",
    "workGroupMappingXCCGroup",
    "globalSplitUCoalesced",
    "globalSplitUWorkGroupMappingRoundRobin",
    "CUOccupancy",
    "PrefetchGlobalRead",
    "MathClocksUnrolledLoop",
    "DirectToVgprA",
    "DirectToVgprB",
    "NumLoadsCoalescedA",
    "NumLoadsCoalescedB",
    "VectorWidthA",
    "VectorWidthB",
    "LocalSplitU",
    "DirectToLdsA",
    "DirectToLdsB",
    "waveGroup",
)


def build_native_fixture(contract: Mapping[str, Any]) -> dict[str, Any]:
    frozen = contract["prelabel_registries"]["native_fixture"]
    native_source = contract["source_and_input_identity"]["native_formocast"]
    rows = [
        {
            "ordinal": ordinal,
            "check_solution": frozen["validity_mask"][index],
            "mapping_overrides": frozen["mapping_overrides"][index],
            "oracle_microseconds": frozen["oracle_microseconds"][index],
        }
        for index, ordinal in enumerate(frozen["row_ordinals"])
    ]
    payload: dict[str, Any] = {
        "base_size_mapping": frozen["base_size_mapping"],
        "checkpoint_id": "S10R4",
        "derivation": "hand_calculated_source_equation_oracle_frozen_before_native_execution",
        "document_kind": "sentinel_fixture",
        "early_terminate": native_source["early_terminate"],
        "expected_guard_trace": {
            "source_blob": native_source["source_blob"],
            "first_true_wins": True,
            "return_for_each_first_true": native_source["early_terminate"],
            "ordered_predicates": [
                {"id": guard_id, "predicate": predicate}
                for guard_id, predicate in GUARD_PREDICATES
            ],
        },
        "expected_queues": frozen["expected_queues"],
        "expected_tie_sets": [
            {"ordinals": [0, 2], "oracle_microseconds": 18.199829979797979}
        ],
        "fixture_id": "s10r4-native-whole-cohort-v1",
        "guard_order": native_source["guard_first_true_order"],
        "input_header": {"row_count": 4, "threshold_count": 4},
        "outcome_blind": True,
        "problem": frozen["problem"],
        "rows": rows,
        "schema_version": 1,
        "thresholds": frozen["thresholds"],
        "validity_mask": frozen["validity_mask"],
    }
    require_exact_keys(payload, FIXTURE_KEYS, where="native fixture payload")
    digest = canonical_sha256(payload)
    if digest != FIXTURE_PAYLOAD_SHA256 or digest != frozen["canonical_payload_sha256"]:
        raise S10R4Error("native fixture canonical payload SHA-256 mismatch")
    return {**payload, "fixture_digest": digest}


def validate_native_fixture(fixture: Mapping[str, Any], contract: Mapping[str, Any]) -> None:
    validate_document_schema(fixture)
    require_exact_keys(fixture, (*FIXTURE_KEYS, "fixture_digest"), where="native fixture")
    payload = {key: fixture[key] for key in FIXTURE_KEYS}
    if fixture["fixture_digest"] != FIXTURE_PAYLOAD_SHA256:
        raise S10R4Error("native fixture stored payload digest mismatch")
    if canonical_sha256(payload) != FIXTURE_PAYLOAD_SHA256:
        raise S10R4Error("native fixture recomputed payload digest mismatch")
    if fixture != build_native_fixture(contract):
        raise S10R4Error("native fixture differs from frozen mechanical construction")


def exact_binary64(left: Any, right: Any, *, where: str) -> None:
    if isinstance(left, bool) or isinstance(right, bool) or not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        raise S10R4Error(f"{where} is not a strict JSON number")
    left = float(left)
    right = float(right)
    if not math.isfinite(left) or not math.isfinite(right):
        raise S10R4Error(f"{where} is non-finite")
    if (left == 0.0 and math.copysign(1.0, left) < 0) or (right == 0.0 and math.copysign(1.0, right) < 0):
        raise S10R4Error(f"{where} contains negative zero")
    if struct.pack(">d", left) != struct.pack(">d", right):
        raise S10R4Error(f"{where} differs at IEEE-754 binary64 value equality")


def _exact_scalar(expected: Any, actual: Any, *, where: str) -> None:
    if isinstance(expected, bool):
        if type(actual) is not bool or actual is not expected:
            raise S10R4Error(f"{where} boolean mismatch")
    elif isinstance(expected, int):
        if type(actual) is not int or actual != expected:
            raise S10R4Error(f"{where} integer mismatch")
    elif isinstance(expected, float):
        exact_binary64(expected, actual, where=where)
    elif expected is None:
        if actual is not None:
            raise S10R4Error(f"{where} null mismatch")
    elif isinstance(expected, str):
        if type(actual) is not str or actual != expected:
            raise S10R4Error(f"{where} string mismatch")
    else:
        raise S10R4Error(f"unsupported expected scalar at {where}")


def exact_tree(expected: Any, actual: Any, *, where: str = "transcript") -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise S10R4Error(f"{where} object field mismatch")
        for key in expected:
            exact_tree(expected[key], actual[key], where=f"{where}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise S10R4Error(f"{where} list mismatch")
        for index, (left, right) in enumerate(zip(expected, actual)):
            exact_tree(left, right, where=f"{where}[{index}]")
    else:
        _exact_scalar(expected, actual, where=where)


def expected_transcript(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Create the comparison transcript; fixture payload identity is validated elsewhere."""
    rows: list[dict[str, Any]] = []
    fixture_rows = fixture["rows"]
    for index, fixture_row in enumerate(fixture_rows):
        rows.append(
            {
                "ordinal": fixture_row["ordinal"],
                "checkSolution": fixture_row["check_solution"],
                "microSeconds": fixture_row["oracle_microseconds"],
                "problem_constants": {
                    "transpose_a": False,
                    "transpose_b": False,
                    "data_type": "BFloat16",
                    "compute_type": "Float",
                },
            }
        )
    queues = []
    for threshold in fixture["thresholds"]:
        item = fixture["expected_queues"][f"{threshold:.1f}"]
        queues.append({"threshold": threshold, **item})
    return {
        "schema_version": 1,
        "fixture_id": fixture["fixture_id"],
        "rows": rows,
        "tie_ordinals": fixture["expected_tie_sets"][0]["ordinals"],
        "queues": queues,
    }


def validate_native_transcript(fixture: Mapping[str, Any], actual: Mapping[str, Any]) -> None:
    exact_tree(expected_transcript(fixture), actual)


def validate_fault_substitutions(results: Mapping[str, Any]) -> None:
    expected = {
        "native_helper_binary_or_path",
        "source_blob_or_guard_order",
        "host_adapter",
        "runtime_queue_semantics",
    }
    if set(results) != expected:
        raise S10R4Error("native substitution fault set mismatch")
    for fault, result in results.items():
        if not isinstance(result, dict) or result.get("accepted") is not False or result.get("criterion") != "CHANGES_REQUIRED":
            raise S10R4Error(f"native substitution did not fail closed: {fault}")


def validate_native_binary_binding(
    binary: Path,
    lock: Mapping[str, Any],
    candidate: Mapping[str, Any] | None = None,
) -> None:
    expected_products = lock.get("source_realization", {}).get("native_build_products", [])
    resolved = binary.resolve(strict=True)
    matches = [row for row in expected_products if row.get("path") == resolved.as_posix()]
    if len(matches) != 1:
        raise S10R4Error("native helper binary path is absent/ambiguous in the effective lock")
    info = resolved.stat(follow_symlinks=False)
    observed = {
        "path": resolved.as_posix(),
        "mode": stat.S_IMODE(info.st_mode),
        "size_bytes": info.st_size,
        "sha256": raw_sha256(resolved),
    }
    if (dict(candidate) if candidate is not None else observed) != matches[0] or observed != matches[0]:
        raise S10R4Error("native helper binary identity differs from the effective lock")


def _fault_rejected(callback: Any) -> dict[str, Any]:
    try:
        callback()
    except S10R4Error as exc:
        return {
            "accepted": False,
            "criterion": "CHANGES_REQUIRED",
            "rejection_sha256": canonical_sha256(str(exc)),
        }
    raise S10R4Error("native substitution fault was unexpectedly accepted")


def _flatten(value: Any) -> list[str]:
    if isinstance(value, bool):
        return ["1" if value else "0"]
    if type(value) is int:
        return [str(value)]
    if isinstance(value, list):
        result: list[str] = []
        for child in value:
            result.extend(_flatten(child))
        return result
    raise S10R4Error("native fixture mapping contains a non-integer/non-boolean scalar")


def fixture_ascii_bytes(fixture: Mapping[str, Any]) -> bytes:
    lines = [f"{len(fixture['rows'])} {len(fixture['thresholds'])}"]
    for threshold in fixture["thresholds"]:
        lines.append(f"{threshold:.1f} {threshold:.1f}")
    problem = fixture["problem"]
    base = fixture["base_size_mapping"]
    for index, row in enumerate(fixture["rows"]):
        mapping = {**base, **row["mapping_overrides"]}
        fields = [
            str(row["ordinal"]),
            "1" if row["check_solution"] else "0",
            str(problem["M"]),
            str(problem["N"]),
            str(problem["NumBatches"]),
            str(problem["K"]),
        ]
        for name in MAPPING_FIELD_ORDER:
            if name not in mapping:
                raise S10R4Error(f"native fixture mapping is missing {name}")
            fields.extend(_flatten(mapping[name]))
        if len(fields) != 40:  # six row/problem fields plus 34 flattened mapping fields
            raise S10R4Error("native fixture ASCII row does not contain exactly 40 scalars")
        lines.append(" ".join(fields))
    encoded = ("\n".join(lines) + "\n").encode("ascii")
    if b"\r" in encoded:
        raise S10R4Error("native fixture ASCII transform contains CR")
    return encoded


def ordered_field_digest() -> str:
    return canonical_sha256(list(MAPPING_FIELD_ORDER))


def prepare_native_input_binding(
    fixture_path: Path,
    formal_root: Path,
    lock_digest: str,
    contract: Mapping[str, Any],
) -> tuple[Path, dict[str, Any]]:
    fixture = load_json(fixture_path)
    validate_native_fixture(fixture, contract)
    payload = fixture_ascii_bytes(fixture)
    input_path = formal_root / "cohort-input.txt"
    atomic_write_bytes(input_path, payload)
    if input_path.read_bytes() != fixture_ascii_bytes(fixture):
        raise S10R4Error("native fixture transform is not byte-identical on recomputation")
    info = input_path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise S10R4Error("native input is not an unambiguous ordinary file")
    binding = seal_digest(
        {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": "native_input_binding",
            "fixture": document_record(fixture_path),
            "fixture_payload_sha256": fixture["fixture_digest"],
            "transformation_id": "s10r4-native-fixture-ascii-v1",
            "ordered_fields": list(MAPPING_FIELD_ORDER),
            "ordered_fields_digest": ordered_field_digest(),
            "output": {
                "path": input_path.resolve(strict=True).as_posix(),
                "mode": stat.S_IMODE(info.st_mode),
                "size_bytes": info.st_size,
                "sha256": raw_sha256(input_path),
            },
            "effective_lock_digest": lock_digest,
        }
    )
    binding_path = formal_root / "native-input-binding.json"
    validate_document_schema(binding)
    atomic_write_json(binding_path, binding)
    return input_path, binding


def run_native_conformance(
    *,
    fixture_path: Path,
    formal_root: Path,
    binary: Path,
    lock_digest: str,
    lock: Mapping[str, Any],
    contract: Mapping[str, Any],
    runner: Any = None,
) -> dict[str, Any]:
    validate_native_binary_binding(binary, lock)
    input_path, binding = prepare_native_input_binding(fixture_path, formal_root, lock_digest, contract)
    transcript_path = formal_root / "native-transcript.json"
    stdout_path = formal_root / "native.stdout"
    stderr_path = formal_root / "native.stderr"
    for path in (transcript_path, stdout_path, stderr_path):
        if path.exists():
            raise S10R4Error(f"native conformance terminal path already exists: {path}")
    argv = materialize_command_template(
        "native_fixture_execution",
        {
            "binary_path": binary.resolve(strict=True).as_posix(),
            "input_path": input_path.resolve(strict=True).as_posix(),
            "output_path": transcript_path.resolve(strict=False).as_posix(),
        },
    )
    if runner is None:
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            completed = subprocess.run(
                argv,
                cwd=Path("/src/rocm-libraries"),
                env=FIXED_ENVIRONMENT,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                timeout=7200,
                check=False,
            )
        returncode = completed.returncode
    else:
        returncode = runner(argv, Path("/src/rocm-libraries"), FIXED_ENVIRONMENT, stdout_path, stderr_path, 7200)
    if returncode != 0 or not transcript_path.is_file():
        raise S10R4Error("native conformance process did not complete exactly")
    fixture = load_json(fixture_path)
    transcript = load_json(transcript_path)
    validate_native_transcript(fixture, transcript)
    expected_binary = next(
        row
        for row in lock["source_realization"]["native_build_products"]
        if row["path"] == binary.resolve(strict=True).as_posix()
    )
    substituted_binary = {**expected_binary, "sha256": "0" * 64}
    source_fault = copy.deepcopy(fixture)
    source_fault["expected_guard_trace"]["ordered_predicates"][0]["predicate"] += " substituted"
    adapter_fault = copy.deepcopy(transcript)
    adapter_fault["rows"][0]["checkSolution"] = not adapter_fault["rows"][0]["checkSolution"]
    queue_fault = copy.deepcopy(transcript)
    queue_fault["queues"][2]["ordinals"] = list(reversed(queue_fault["queues"][2]["ordinals"]))
    fault_results = {
        "native_helper_binary_or_path": _fault_rejected(
            lambda: validate_native_binary_binding(binary, lock, substituted_binary)
        ),
        "source_blob_or_guard_order": _fault_rejected(
            lambda: validate_native_fixture(source_fault, contract)
        ),
        "host_adapter": _fault_rejected(
            lambda: validate_native_transcript(fixture, adapter_fault)
        ),
        "runtime_queue_semantics": _fault_rejected(
            lambda: validate_native_transcript(fixture, queue_fault)
        ),
    }
    validate_fault_substitutions(fault_results)
    return seal_digest(
        {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": "sentinel_conformance",
            "status": "PASS",
            "effective_lock_digest": lock_digest,
            "input_binding_digest": binding["document_digest"],
            "argv": argv,
            "environment": FIXED_ENVIRONMENT,
            "binary": {
                "path": binary.resolve(strict=True).as_posix(),
                "sha256": raw_sha256(binary.resolve(strict=True)),
            },
            "transcript": document_record(transcript_path),
            "stdout_sha256": raw_sha256(stdout_path),
            "stderr_sha256": raw_sha256(stderr_path),
            "fault_substitutions": fault_results,
        }
    )


def rederive_native_conformance(
    *,
    fixture_path: Path,
    formal_root: Path,
    binary: Path,
    lock_digest: str,
    lock: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Recompute the conformance summary from existing raw native evidence only."""
    validate_native_binary_binding(binary, lock)
    _, binding = prepare_native_input_binding(fixture_path, formal_root, lock_digest, contract)
    transcript_path = formal_root / "native-transcript.json"
    stdout_path = formal_root / "native.stdout"
    stderr_path = formal_root / "native.stderr"
    if not all(path.is_file() for path in (transcript_path, stdout_path, stderr_path)):
        raise S10R4Error("native conformance resume evidence is partial")
    fixture = load_json(fixture_path)
    transcript = load_json(transcript_path)
    validate_native_transcript(fixture, transcript)
    expected_binary = next(
        (
            row
            for row in lock["source_realization"]["native_build_products"]
            if row["path"] == binary.resolve(strict=True).as_posix()
        ),
        None,
    )
    if expected_binary is None:
        raise S10R4Error("native conformance resume binary is absent from the lock")
    substituted_binary = {**expected_binary, "sha256": "0" * 64}
    source_fault = copy.deepcopy(fixture)
    source_fault["expected_guard_trace"]["ordered_predicates"][0]["predicate"] += " substituted"
    adapter_fault = copy.deepcopy(transcript)
    adapter_fault["rows"][0]["checkSolution"] = not adapter_fault["rows"][0]["checkSolution"]
    queue_fault = copy.deepcopy(transcript)
    queue_fault["queues"][2]["ordinals"] = list(reversed(queue_fault["queues"][2]["ordinals"]))
    fault_results = {
        "native_helper_binary_or_path": _fault_rejected(
            lambda: validate_native_binary_binding(binary, lock, substituted_binary)
        ),
        "source_blob_or_guard_order": _fault_rejected(lambda: validate_native_fixture(source_fault, contract)),
        "host_adapter": _fault_rejected(lambda: validate_native_transcript(fixture, adapter_fault)),
        "runtime_queue_semantics": _fault_rejected(lambda: validate_native_transcript(fixture, queue_fault)),
    }
    validate_fault_substitutions(fault_results)
    argv = materialize_command_template(
        "native_fixture_execution",
        {
            "binary_path": binary.resolve(strict=True).as_posix(),
            "input_path": (formal_root / "cohort-input.txt").resolve(strict=True).as_posix(),
            "output_path": transcript_path.resolve(strict=True).as_posix(),
        },
    )
    return seal_digest(
        {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": "sentinel_conformance",
            "status": "PASS",
            "effective_lock_digest": lock_digest,
            "input_binding_digest": binding["document_digest"],
            "argv": argv,
            "environment": FIXED_ENVIRONMENT,
            "binary": {"path": binary.resolve(strict=True).as_posix(), "sha256": raw_sha256(binary.resolve(strict=True))},
            "transcript": document_record(transcript_path),
            "stdout_sha256": raw_sha256(stdout_path),
            "stderr_sha256": raw_sha256(stderr_path),
            "fault_substitutions": fault_results,
        }
    )
