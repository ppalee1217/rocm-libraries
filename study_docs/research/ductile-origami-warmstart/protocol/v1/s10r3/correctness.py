# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Correctness-panel completeness and frozen S10R3 noise statistics."""

from __future__ import annotations

import math
import statistics
from typing import Any, Mapping, Sequence

from .contract import canonical_sha256


class CorrectnessError(ValueError):
    """A correctness or noise record violates the frozen panel."""


SIZE_IDS = ("small", "medium", "large")
REPEATS = tuple(range(7))


def anchor_hashes(sorted_config_hashes: Sequence[str]) -> tuple[str, str, str]:
    k = len(sorted_config_hashes)
    if not 10 <= k <= 20:
        raise CorrectnessError("final K must be in [10,20]")
    if list(sorted_config_hashes) != sorted(sorted_config_hashes):
        raise CorrectnessError("final config hashes must be sorted")
    if len(set(sorted_config_hashes)) != k:
        raise CorrectnessError("final config hashes must be distinct")
    indices = (0, (k - 1) // 2, k - 1)
    anchors = tuple(sorted_config_hashes[index] for index in indices)
    if len(set(anchors)) != 3:
        raise CorrectnessError("dynamic anchors must be three distinct hashes")
    return anchors


def verify_correctness_cells(
    sorted_config_hashes: Sequence[str],
    cells: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    anchors = anchor_hashes(sorted_config_hashes)
    required = {(anchor, size_id) for anchor in anchors for size_id in SIZE_IDS}
    seen: dict[tuple[str, str], Mapping[str, Any]] = {}
    for cell in cells:
        key = (cell.get("config_hash"), cell.get("size_id"))
        if key not in required or key in seen:
            raise CorrectnessError("correctness cell is foreign or duplicated")
        for phase in ("generate", "compile", "smoke", "nonzero_correctness"):
            if cell.get(phase) is not True:
                raise CorrectnessError(f"correctness cell failed phase: {phase}")
        seen[key] = cell
    if set(seen) != required:
        raise CorrectnessError("correctness panel is partial")
    body = {
        "document_kind": "correctness",
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "anchors": list(anchors),
        "size_ids": list(SIZE_IDS),
        "cell_count": 9,
        "cells": [dict(seen[key]) for key in sorted(seen)],
        "all_passed": True,
    }
    return {**body, "summary_digest": canonical_sha256(body)}


def _finite_positive(value: Any, *, field: str) -> float:
    if type(value) not in (int, float) or type(value) is bool:
        raise CorrectnessError(f"{field} must be an exact JSON number")
    converted = float(value)
    if not math.isfinite(converted) or converted <= 0:
        raise CorrectnessError(f"{field} must be finite and positive")
    return converted


def _cv(values: Sequence[float]) -> float:
    if len(values) != 7:
        raise CorrectnessError("anchor Q series must contain seven repeats")
    mean = statistics.fmean(values)
    return statistics.stdev(values) / mean


def _percentile_linear(values: Sequence[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise CorrectnessError("percentile input cannot be empty")
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def validate_noise_cells(
    sorted_config_hashes: Sequence[str],
    observations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    anchors = anchor_hashes(sorted_config_hashes)
    required = {
        (anchor, size_id, repeat)
        for anchor in anchors
        for size_id in SIZE_IDS
        for repeat in REPEATS
    }
    seen: dict[tuple[str, str, int], float] = {}
    for item in observations:
        repeat = item.get("repeat")
        if type(repeat) is not int:
            raise CorrectnessError("noise repeat must be an exact integer")
        key = (item.get("config_hash"), item.get("size_id"), repeat)
        if key not in required or key in seen:
            raise CorrectnessError("noise observation is foreign or duplicated")
        seen[key] = _finite_positive(item.get("quantity"), field="quantity")
    if set(seen) != required:
        raise CorrectnessError("noise panel must contain exactly 63 observations")
    q_ar: dict[tuple[str, int], float] = {}
    for anchor in anchors:
        for repeat in REPEATS:
            q_ar[(anchor, repeat)] = max(
                seen[(anchor, size_id, repeat)] for size_id in SIZE_IDS
            )
    anchor_cvs = {
        anchor: _cv([q_ar[(anchor, repeat)] for repeat in REPEATS])
        for anchor in anchors
    }
    cv_p95 = _percentile_linear(list(anchor_cvs.values()), 0.95)
    log_deviations = []
    for anchor in anchors:
        values = [q_ar[(anchor, repeat)] for repeat in REPEATS]
        median_log = statistics.median(math.log(value) for value in values)
        log_deviations.extend(abs(math.log(value) - median_log) for value in values)
    delta_noise = math.exp(_percentile_linear(log_deviations, 0.95)) - 1
    body = {
        "document_kind": "noise",
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "reduce_fn": "max",
        "observation_count": 63,
        "q_ar": [
            {
                "config_hash": anchor,
                "repeat": repeat,
                "quantity": q_ar[(anchor, repeat)],
            }
            for anchor in anchors
            for repeat in REPEATS
        ],
        "anchor_cv": anchor_cvs,
        "cv_p95": cv_p95,
        "threshold": 0.005,
        "stable": cv_p95 <= 0.005,
        "delta_noise": delta_noise,
    }
    return {**body, "summary_digest": canonical_sha256(body)}
