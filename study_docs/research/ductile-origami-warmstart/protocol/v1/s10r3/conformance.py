# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Score-blind sentinel oracle and native/runtime conformance checks."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Mapping

from .contract import (
    atomic_write_json,
    canonical_sha256,
)


class ConformanceError(ValueError):
    """The sentinel fixture, guard source, native path, or queue semantics drifted."""


FORMOCAST_SOURCE_BLOB = "cac2b324984a9fe2e1fadb018702486545e86e80"
GUARD_ORDER = (
    "global-split-u-zero",
    "small-mn-macro-tile-gap",
    "large-mn-macro-tile-gap",
    "bf16-half-depthu-k-batch-mi",
    "direct-to-lds-a-small-m",
    "direct-to-lds-b-small-n",
    "derived-plr-zero",
)
EARLY_TERMINATE = {"microSeconds": 9_999_999.9, "hitRate": 0.0}
DEPTH_U_K_CONDITION = (
    "(K>=64 && depthU<=32) || (K<=32 && depthU>32) || "
    "(K>32 && depthU>K)"
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
        "BF16_or_Half && bpeA==2 && bpeB==2 && depthU_K_condition && "
        "NumBatches<NumCUs && matrixInstruction[2]>=32",
    ),
    ("direct-to-lds-a-small-m", "DirectToLdsA && M < MT0"),
    ("direct-to-lds-b-small-n", "DirectToLdsB && N < MT1"),
    ("derived-plr-zero", "PLR == 0"),
)


def independent_oracle(fixture: Mapping[str, Any]) -> dict[str, Any]:
    rows = fixture["rows"]
    mask = fixture["validity_mask"]
    if len(rows) != 4 or mask != [True, False, True, True]:
        raise ConformanceError("sentinel row count or validity mask drift")
    performance = []
    for index, (row, valid) in enumerate(zip(rows, mask)):
        if row["ordinal"] != index or row["check_solution"] is not valid:
            raise ConformanceError("sentinel ordinals/validity are inconsistent")
        value = row["oracle_microseconds"]
        if valid:
            if type(value) not in (int, float) or type(value) is bool:
                raise ConformanceError("valid sentinel row lacks an oracle value")
            performance.append((index, float(value)))
        elif value is not None:
            raise ConformanceError("invalid sentinel row must not carry a prediction")
    performance.sort(key=lambda item: (item[1], item[0]))
    result = {}
    for threshold in fixture["thresholds"]:
        token = str(float(threshold))
        if float(threshold) == 0.0:
            ordinal, threshold_value = performance[0]
            result[token] = {
                "prediction_disabled": False,
                "sorted_ordinals": [item[0] for item in performance],
                "threshold_index": 0,
                "threshold_value": threshold_value,
                "queue_prefix": [ordinal],
            }
            continue
        if threshold > 1.0:
            result[token] = {
                "prediction_disabled": True,
                "sorted_ordinals": [row["ordinal"] for row in rows],
                "threshold_index": None,
                "threshold_value": None,
                "queue_prefix": [row["ordinal"] for row in rows],
            }
            continue
        threshold_index = min(
            len(performance) - 1, int(len(performance) * float(threshold))
        )
        threshold_value = performance[threshold_index][1]
        sorted_ordinals = [item[0] for item in performance]
        result[token] = {
            "prediction_disabled": False,
            "sorted_ordinals": sorted_ordinals,
            "threshold_index": threshold_index,
            "threshold_value": threshold_value,
            "queue_prefix": [
                ordinal
                for ordinal, microseconds in performance
                if microseconds <= threshold_value
            ],
        }
    return result


def fixture_document() -> dict[str, Any]:
    base_size_mapping = {
        "waveNum": 4,
        "macroTile": [64, 64, 1],
        "matrixInstruction": [16, 16, 16, 1],
        "grvwA": 4,
        "grvwB": 4,
        "gwvwC": 4,
        "gwvwD": 4,
        "depthU": 32,
        "globalSplitU": 1,
        "workGroupMapping": 1,
        "globalAccumulation": 0,
        "workGroupMappingXCC": 1,
        "workGroupMappingXCCGroup": -1,
        "globalSplitUCoalesced": False,
        "globalSplitUWorkGroupMappingRoundRobin": False,
        "CUOccupancy": 2,
        "PrefetchGlobalRead": 2,
        "MathClocksUnrolledLoop": 16,
        "DirectToVgprA": False,
        "DirectToVgprB": False,
        "NumLoadsCoalescedA": 1,
        "NumLoadsCoalescedB": 1,
        "VectorWidthA": 4,
        "VectorWidthB": 4,
        "LocalSplitU": 1,
        "DirectToLdsA": False,
        "DirectToLdsB": False,
        "waveGroup": [2, 2],
    }
    rows = [
        {
            "ordinal": 0,
            "check_solution": True,
            "mapping_overrides": {},
            "oracle_microseconds": 18.199829979797979,
        },
        {
            "ordinal": 1,
            "check_solution": False,
            "mapping_overrides": {"macroTile": [96, 64, 1]},
            "oracle_microseconds": None,
        },
        {
            "ordinal": 2,
            "check_solution": True,
            "mapping_overrides": {},
            "oracle_microseconds": 18.199829979797979,
        },
        {
            "ordinal": 3,
            "check_solution": True,
            "mapping_overrides": {"macroTile": [128, 64, 1]},
            "oracle_microseconds": 22.466412606060604,
        },
    ]
    document: dict[str, Any] = {
        "document_kind": "sentinel_fixture",
        "schema_version": 1,
        "fixture_id": "s10r3-native-whole-cohort-v1",
        "checkpoint_id": "S10R3",
        "outcome_blind": True,
        "derivation": "hand_calculated_source_equation_oracle_frozen_before_native_execution",
        "input_header": {"row_count": 4, "threshold_count": 4},
        "problem": {
            "M": 256,
            "N": 256,
            "NumBatches": 1,
            "K": 1024,
            "transpose_a": False,
            "transpose_b": False,
            "data_type": "BFloat16",
            "compute_type": "Float",
        },
        "base_size_mapping": base_size_mapping,
        "rows": rows,
        "validity_mask": [True, False, True, True],
        "expected_tie_sets": [
            {
                "ordinals": [0, 2],
                "oracle_microseconds": 18.199829979797979,
            }
        ],
        "thresholds": [0.0, 0.5, 1.0, 2.0],
        "guard_order": list(GUARD_ORDER),
        "early_terminate": copy.deepcopy(EARLY_TERMINATE),
        "expected_guard_trace": {
            "source_blob": FORMOCAST_SOURCE_BLOB,
            "first_true_wins": True,
            "ordered_predicates": [
                {"id": guard_id, "predicate": predicate}
                for guard_id, predicate in GUARD_PREDICATES
            ],
            "return_for_each_first_true": copy.deepcopy(EARLY_TERMINATE),
        },
    }
    document["expected_queues"] = independent_oracle(document)
    document["fixture_digest"] = canonical_sha256(document)
    return document


def validate_fixture(document: Mapping[str, Any]) -> None:
    if dict(document) != fixture_document():
        raise ConformanceError("sentinel fixture differs from the exact S10R3 oracle")
    if document["expected_queues"] != independent_oracle(document):
        raise ConformanceError("sentinel independent oracle self-check failed")


def materialize_fixture(path: Path | str) -> dict[str, Any]:
    document = fixture_document()
    atomic_write_json(path, document, exclusive=True)
    return document


def _normalized(text: str) -> str:
    return re.sub(r"\s+", "", text)


def validate_pinned_guard_source(
    source: str,
    *,
    source_blob: str,
    fixture: Mapping[str, Any],
) -> None:
    validate_fixture(fixture)
    if source_blob != FORMOCAST_SOURCE_BLOB:
        raise ConformanceError("pinned Formocast source blob mismatch")
    start = source.find("// 3.1 Early terminate")
    end = source.find("// 5. Cache Hit Rates", start)
    if start < 0 or end < 0:
        raise ConformanceError("declared early-termination source section is absent")
    section = source[start:end]
    normalized = _normalized(section)
    anchors = [
        "if(GlobalSplitU==0)",
        "if((M<128&&MT0-M>=16)||(N<128&&MT1-N>=16))",
        "if((M>=128&&MT0-M>=32)||(N>=128&&MT1-N>=32))",
        (
            "if(problem.dataType==data_type_t::BFloat16||"
            "problem.dataType==data_type_t::Half)"
        ),
        "if(DirectToLdsA&&M<MT0)",
        "if(DirectToLdsB&&N<MT1)",
        "if(PLR==0)",
    ]
    positions = []
    for anchor in anchors:
        if normalized.count(anchor) != 1:
            raise ConformanceError(f"guard missing or duplicated: {anchor}")
        positions.append(normalized.index(anchor))
    if positions != sorted(positions):
        raise ConformanceError("guard blocks are reordered")
    if normalized.count("returnpp;") != 7:
        raise ConformanceError("unexpected return placement in guard section")
    if normalized.count("pp.microSeconds=9999999.9;") != 7:
        raise ConformanceError("early-terminate microSeconds assignment drift")
    if normalized.count("pp.hitRate=0;") != 7:
        raise ConformanceError("early-terminate hitRate assignment drift")
    for index, position in enumerate(positions):
        block_end = positions[index + 1] if index + 1 < len(positions) else len(normalized)
        block = normalized[position:block_end]
        micro = block.find("pp.microSeconds=9999999.9;")
        hit = block.find("pp.hitRate=0;")
        returned = block.find("returnpp;")
        if not (0 <= micro < returned and 0 <= hit < returned):
            raise ConformanceError("guard assignment appears after return")
    nested = (
        "((K>=64&&depthU<=32)||(K<=32&&depthU>32)||"
        "(K>32&&depthU>K))&&NumBatches<hw_consts.NumCUs&&"
        "sizeMapping.matrixInstruction[2]>=32"
    )
    if nested not in normalized:
        raise ConformanceError("nested BF16/Half depthU/K predicate drift")
    if fixture["guard_order"] != list(GUARD_ORDER):
        raise ConformanceError("fixture guard order drift")
    if fixture["early_terminate"] != EARLY_TERMINATE:
        raise ConformanceError("fixture early-terminate pair drift")
    trace = fixture["expected_guard_trace"]
    if trace != {
        "source_blob": FORMOCAST_SOURCE_BLOB,
        "first_true_wins": True,
        "ordered_predicates": [
            {"id": guard_id, "predicate": predicate}
            for guard_id, predicate in GUARD_PREDICATES
        ],
        "return_for_each_first_true": EARLY_TERMINATE,
    }:
        raise ConformanceError("fixture expected guard trace drift")


def expected_native_transcript(fixture: Mapping[str, Any]) -> dict[str, Any]:
    validate_fixture(fixture)
    return {
        "schema_version": 1,
        "symbol": "s10r3_native::evaluate_formocast_all_solutions_cohort",
        "status": "PASS",
        "native_path_called": True,
        "runtime_check_solution_called": True,
        "runtime_pre_problem_called": True,
        "guard_order": list(GUARD_ORDER),
        "early_terminate": copy.deepcopy(EARLY_TERMINATE),
        "first_true_wins": True,
        "predictions": [
            {
                "ordinal": row["ordinal"],
                "microSeconds": row["oracle_microseconds"],
            }
            for row in fixture["rows"]
            if row["check_solution"]
        ],
        "queues": copy.deepcopy(fixture["expected_queues"]),
    }


def compare_native_transcript(
    fixture: Mapping[str, Any], transcript: Mapping[str, Any]
) -> None:
    expected = expected_native_transcript(fixture)
    if dict(transcript) != expected:
        raise ConformanceError("native Formocast/runtime transcript differs from oracle")


def assert_fault_rejected(fault_id: str, rejected: bool) -> None:
    allowed = {
        "native_helper_binary_or_path",
        "source_blob_or_guard_order",
        "host_adapter",
        "runtime_check_solution_or_queue_semantics",
    }
    if fault_id not in allowed or rejected is not True:
        raise ConformanceError("required native substitution fault did not fail closed")
