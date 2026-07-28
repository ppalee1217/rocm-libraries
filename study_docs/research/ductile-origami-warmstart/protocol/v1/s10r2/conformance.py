# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Score-blind native/runtime conformance validation."""

from __future__ import annotations

import copy
import hashlib
from typing import Any, Callable, Mapping, Sequence

from Tensile.ductile.evidence import canonical_json_bytes, canonical_sha256


class ConformanceError(ValueError):
    """Native helper or queue-semantics conformance defect."""


EARLY_TERMINATE = {"microSeconds": 9_999_999.9, "hitRate": 0.0}
GUARD_ORDER = [
    "global-split-u-zero",
    "small-mn-macro-tile-gap",
    "large-mn-macro-tile-gap",
    "bf16-half-depthu-k-batch-mi",
    "direct-to-lds-a-small-m",
    "direct-to-lds-b-small-n",
    "derived-plr-zero",
]

_MAPPING_SCALARS = (
    "waveNum",
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
)
_MAPPING_VECTORS = {
    "macroTile": 3,
    "matrixInstruction": 4,
    "waveGroup": 2,
}


def _exact_int(value: Any, *, field: str) -> int:
    if type(value) is not int:
        raise ConformanceError(f"{field} must be an exact integer")
    return value


def materialize_native_fixture(
    fixture: Mapping[str, Any],
    thresholds: Sequence[float],
) -> dict[str, Any]:
    """Validate and serialize the complete prelocked synthetic cohort."""

    rows = fixture.get("rows")
    problem = fixture.get("problem")
    base_mapping = fixture.get("base_size_mapping")
    header = fixture.get("input_header")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise ConformanceError("synthetic fixture rows must be a non-empty sequence")
    if not isinstance(problem, Mapping) or not isinstance(base_mapping, Mapping):
        raise ConformanceError("synthetic fixture problem/mapping must be objects")
    if not isinstance(header, Mapping):
        raise ConformanceError("synthetic fixture input_header must be an object")
    if (
        header.get("row_count") != len(rows)
        or header.get("threshold_count") != len(thresholds)
    ):
        raise ConformanceError("synthetic fixture header count mismatch")
    expected_mapping_fields = set(_MAPPING_SCALARS).union(_MAPPING_VECTORS)
    if set(base_mapping) != expected_mapping_fields:
        raise ConformanceError("synthetic base SizeMapping field set mismatch")
    exact_problem = {
        field: _exact_int(problem.get(field), field=f"problem.{field}")
        for field in ("M", "N", "NumBatches", "K")
    }
    if (
        problem.get("transpose_a") is not False
        or problem.get("transpose_b") is not False
        or problem.get("data_type") != "BFloat16"
        or problem.get("compute_type") != "Float"
    ):
        raise ConformanceError("synthetic problem type identity mismatch")

    lines = [f"{len(rows)} {len(thresholds)}"]
    for threshold in thresholds:
        value = float(threshold)
        if value < 0:
            raise ConformanceError("prediction threshold must be non-negative")
        token = str(value)
        lines.append(f"{token} {token}")

    normalized_rows: list[dict[str, Any]] = []
    validity_mask: list[bool] = []
    for ordinal, row in enumerate(rows):
        if not isinstance(row, Mapping) or row.get("ordinal") != ordinal:
            raise ConformanceError("synthetic cohort ordinals must be contiguous")
        valid = row.get("check_solution")
        if type(valid) is not bool:
            raise ConformanceError("check_solution must be an exact boolean")
        overrides = row.get("mapping_overrides")
        if not isinstance(overrides, Mapping) or not set(overrides).issubset(
            expected_mapping_fields
        ):
            raise ConformanceError("synthetic mapping override field mismatch")
        mapping = copy.deepcopy(dict(base_mapping))
        mapping.update(copy.deepcopy(dict(overrides)))
        values: list[int] = [
            ordinal,
            int(valid),
            exact_problem["M"],
            exact_problem["N"],
            exact_problem["NumBatches"],
            exact_problem["K"],
        ]
        for field in ("waveNum",):
            values.append(_exact_int(mapping[field], field=field))
        for field, length in (("macroTile", 3), ("matrixInstruction", 4)):
            vector = mapping[field]
            if (
                not isinstance(vector, Sequence)
                or isinstance(vector, (str, bytes))
                or len(vector) != length
            ):
                raise ConformanceError(f"{field} must have length {length}")
            values.extend(
                _exact_int(value, field=f"{field}[{index}]")
                for index, value in enumerate(vector)
            )
        for field in _MAPPING_SCALARS[1:]:
            value = mapping[field]
            if type(value) is bool:
                values.append(int(value))
            else:
                values.append(_exact_int(value, field=field))
        wave_group = mapping["waveGroup"]
        if (
            not isinstance(wave_group, Sequence)
            or isinstance(wave_group, (str, bytes))
            or len(wave_group) != 2
        ):
            raise ConformanceError("waveGroup must have length two")
        values.extend(
            _exact_int(value, field=f"waveGroup[{index}]")
            for index, value in enumerate(wave_group)
        )
        lines.append(" ".join(str(value) for value in values))
        microseconds = row.get("expected_microseconds")
        if valid:
            if (
                isinstance(microseconds, bool)
                or not isinstance(microseconds, (int, float))
                or float(microseconds) <= 0
            ):
                raise ConformanceError("valid fixture row needs positive latency")
        elif microseconds is not None:
            raise ConformanceError("invalid fixture row must not have a latency")
        normalized_rows.append(
            {
                "ordinal": ordinal,
                "check_solution": valid,
                "microseconds": microseconds,
            }
        )
        validity_mask.append(valid)

    if fixture.get("validity_mask") != validity_mask:
        raise ConformanceError("synthetic validity mask mismatch")
    expected = {
        str(float(threshold)): expected_queue(normalized_rows, float(threshold))
        for threshold in thresholds
    }
    if fixture.get("expected_queues") != expected:
        raise ConformanceError("frozen synthetic expected queues are inconsistent")
    return {
        "input_bytes": ("\n".join(lines) + "\n").encode("ascii"),
        "cohort": normalized_rows,
        "thresholds": [float(value) for value in thresholds],
        "expected_queues": expected,
        "fixture_digest": canonical_sha256(fixture),
        "input_sha256": hashlib.sha256(
            ("\n".join(lines) + "\n").encode("ascii")
        ).hexdigest(),
        "canonical_fixture_hex": canonical_json_bytes(fixture).hex(),
    }


def expected_queue(
    rows: Sequence[Mapping[str, Any]],
    prediction_threshold: float,
) -> dict[str, Any]:
    if not rows:
        raise ConformanceError("synthetic cohort must not be empty")
    if prediction_threshold > 1:
        return {
            "prediction_disabled": True,
            "sorted_ordinals": [int(row["ordinal"]) for row in rows],
            "threshold_index": None,
            "threshold_value": None,
            "queue_prefix": [int(row["ordinal"]) for row in rows],
        }
    valid = [row for row in rows if row.get("check_solution") is True]
    if not valid:
        raise ConformanceError("synthetic cohort has no checkSolution-valid rows")
    sorted_rows = sorted(valid, key=lambda row: float(row["microseconds"]))
    index = min(len(sorted_rows) - 1, int(len(sorted_rows) * prediction_threshold))
    threshold_value = float(sorted_rows[index]["microseconds"])
    if prediction_threshold == 0:
        prefix = sorted_rows[:1]
    else:
        prefix = [
            row for row in sorted_rows if float(row["microseconds"]) <= threshold_value
        ]
    return {
        "prediction_disabled": False,
        "sorted_ordinals": [int(row["ordinal"]) for row in sorted_rows],
        "threshold_index": index,
        "threshold_value": threshold_value,
        "queue_prefix": [int(row["ordinal"]) for row in prefix],
    }


def run_native_formocast_conformance(
    transcript: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare a native transcript with the prelocked, score-blind fixture."""

    if transcript.get("native_path_called") is not True:
        raise ConformanceError("native Formocast path was not called")
    if transcript.get("runtime_check_solution_called") is not True:
        raise ConformanceError("runtime checkSolution path was not called")
    if transcript.get("guard_order") != GUARD_ORDER:
        raise ConformanceError("Formocast guard order mismatch")
    if transcript.get("early_terminate") != EARLY_TERMINATE:
        raise ConformanceError("Formocast early-terminate pair mismatch")
    expected_by_threshold = {
        str(float(threshold)): expected_queue(fixture["cohort"], float(threshold))
        for threshold in fixture["thresholds"]
    }
    frozen_expected = fixture.get("expected_queues")
    if frozen_expected is not None and frozen_expected != expected_by_threshold:
        raise ConformanceError("frozen expected queues are internally inconsistent")
    if transcript.get("queues") != expected_by_threshold:
        raise ConformanceError("runtime queue transcript mismatch")
    body = {
        "schema_version": 1,
        "fixture_digest": canonical_sha256(fixture),
        "transcript_digest": canonical_sha256(transcript),
        "status": "PASS",
        "score_blind": True,
    }
    return {**body, "conformance_digest": canonical_sha256(body)}


def run_runtime_substitution_fault_tests(
    validator: Callable[[Mapping[str, Any]], None],
    valid_binding: Mapping[str, Any],
    *,
    mutations: Mapping[str, Any],
) -> dict[str, Any]:
    required = {
        "helper_path",
        "helper_sha256",
        "predicted_performance_source_blob",
        "host_adapter_sha256",
        "queue_adapter_source_blob",
    }
    if set(mutations) != required:
        raise ConformanceError("fault suite must mutate every preregistered binding class")
    results: dict[str, str] = {}
    for field in sorted(required):
        candidate = dict(valid_binding)
        candidate[field] = mutations[field]
        try:
            validator(candidate)
        except Exception:
            results[field] = "FAIL_CLOSED"
        else:
            raise ConformanceError(f"binding substitution did not fail closed: {field}")
    return {
        "schema_version": 1,
        "status": "PASS",
        "results": results,
        "fault_suite_digest": canonical_sha256(results),
    }
