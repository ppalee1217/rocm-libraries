# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Frozen anchor correctness and noise-panel validation."""

from __future__ import annotations

import math
import statistics
from typing import Any, Mapping, Sequence

from Tensile.ductile.evidence import canonical_sha256


class CorrectnessError(ValueError):
    """Correctness/noise panel is incomplete or violates the frozen rule."""


def anchor_hashes(sorted_config_hashes: Sequence[str]) -> list[str]:
    if len(sorted_config_hashes) != 10:
        raise CorrectnessError("exact-ten corpus is required before anchor selection")
    if list(sorted_config_hashes) != sorted(sorted_config_hashes):
        raise CorrectnessError("config hashes must be sorted before selecting anchors")
    if len(set(sorted_config_hashes)) != 10:
        raise CorrectnessError("config hashes must be distinct")
    return [sorted_config_hashes[index] for index in (0, 4, 9)]


def verify_correctness_anchors(
    rows: Sequence[Mapping[str, Any]],
    *,
    anchors: Sequence[str],
    size_ids: Sequence[str],
) -> dict[str, Any]:
    if len(anchors) != 3 or len(set(anchors)) != 3:
        raise CorrectnessError("three distinct frozen anchors are required")
    if len(size_ids) != 3 or len(set(size_ids)) != 3:
        raise CorrectnessError("three distinct frozen sizes are required")
    expected = {(anchor, size_id) for anchor in anchors for size_id in size_ids}
    if len(rows) != 9:
        raise CorrectnessError("correctness panel must contain exactly nine rows")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (str(row.get("config_hash")), str(row.get("size_id")))
        if key in seen:
            raise CorrectnessError(f"duplicate correctness row {key}")
        seen.add(key)
        if row.get("generated") is not True or row.get("compiled") is not True:
            raise CorrectnessError(f"generate/compile failure for {key}")
        if row.get("smoke_pass") is not True or row.get("nonzero_validation") is not True:
            raise CorrectnessError(f"FT-BLOCKED-CORRECTNESS for {key}")
        quality = row.get("quality")
        if not isinstance(quality, (int, float)) or isinstance(quality, bool):
            raise CorrectnessError(f"missing numeric quality for {key}")
        if not math.isfinite(float(quality)) or float(quality) <= 0:
            raise CorrectnessError(f"non-finite/non-positive quality for {key}")
    if seen != expected:
        raise CorrectnessError("correctness rows differ from frozen 3x3 panel")
    body = {
        "schema_version": 1,
        "row_count": 9,
        "anchors": list(anchors),
        "size_ids": list(size_ids),
        "rows_digest": canonical_sha256(list(rows)),
        "status": "PASS",
    }
    return {**body, "correctness_digest": canonical_sha256(body)}


def _percentile_linear(values: Sequence[float], q: float) -> float:
    if not values:
        raise CorrectnessError("percentile requires observations")
    ordered = sorted(float(value) for value in values)
    if not 0 <= q <= 1:
        raise CorrectnessError("percentile q must be in [0,1]")
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _cv(values: Sequence[float]) -> float:
    if len(values) != 7:
        raise CorrectnessError("each noise cell requires exactly seven repeats")
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise CorrectnessError("noise qualities must be finite and positive")
    mean = statistics.fmean(values)
    return statistics.pstdev(values) / mean


def validate_noise_cells(
    rows: Sequence[Mapping[str, Any]],
    *,
    anchors: Sequence[str],
    size_ids: Sequence[str],
    cv_p95_threshold: float = 0.005,
) -> dict[str, Any]:
    if len(anchors) != 3 or len(set(anchors)) != 3:
        raise CorrectnessError("noise panel requires three distinct frozen anchors")
    if len(size_ids) != 3 or len(set(size_ids)) != 3:
        raise CorrectnessError("noise panel requires three distinct frozen sizes")
    if len(rows) != 63:
        raise CorrectnessError("noise panel must contain exactly 63 observations")
    expected_cells = {
        (anchor, repeat) for anchor in anchors for repeat in range(7)
    }
    cells: dict[tuple[str, int], dict[str, float]] = {}
    for row in rows:
        anchor = str(row.get("config_hash"))
        size_id = str(row.get("size_id"))
        repeat = row.get("repeat")
        quality = row.get("quality")
        if type(repeat) is not int or not 0 <= repeat < 7:
            raise CorrectnessError(
                f"invalid repeat index for {(anchor, size_id)}"
            )
        key = (anchor, repeat)
        if key not in expected_cells or size_id not in size_ids:
            raise CorrectnessError(
                f"unexpected noise observation {(anchor, size_id, repeat)}"
            )
        if not isinstance(quality, (int, float)) or isinstance(quality, bool):
            raise CorrectnessError(
                f"invalid quality for {(anchor, size_id, repeat)}"
            )
        numeric_quality = float(quality)
        if not math.isfinite(numeric_quality) or numeric_quality <= 0:
            raise CorrectnessError(
                f"non-finite/non-positive quality for "
                f"{(anchor, size_id, repeat)}"
            )
        cell = cells.setdefault(key, {})
        if size_id in cell:
            raise CorrectnessError(
                f"duplicate noise observation {(anchor, size_id, repeat)}"
            )
        cell[size_id] = numeric_quality
    expected_sizes = set(size_ids)
    if set(cells) != expected_cells or any(
        set(cell) != expected_sizes for cell in cells.values()
    ):
        raise CorrectnessError("noise panel is incomplete")

    # The authority defines Q_ar by reducing the three size qualities for one
    # anchor/repeat with the actual reducer used downstream.
    aggregate_quality = {
        (anchor, repeat): max(cells[(anchor, repeat)].values())
        for anchor in anchors
        for repeat in range(7)
    }
    anchor_cvs = {
        anchor: _cv(
            [aggregate_quality[(anchor, repeat)] for repeat in range(7)]
        )
        for anchor in anchors
    }
    cv_p95 = _percentile_linear(list(anchor_cvs.values()), 0.95)

    absolute_log_deviations: list[float] = []
    for anchor in anchors:
        log_qualities = [
            math.log(aggregate_quality[(anchor, repeat)])
            for repeat in range(7)
        ]
        within_anchor_median = statistics.median(log_qualities)
        absolute_log_deviations.extend(
            abs(value - within_anchor_median) for value in log_qualities
        )
    delta_noise = (
        math.exp(_percentile_linear(absolute_log_deviations, 0.95)) - 1
    )
    body = {
        "schema_version": 1,
        "raw_observation_count": 63,
        "aggregate_quality_count": 21,
        "anchor_count": 3,
        "sizes_per_aggregate": 3,
        "repeats_per_anchor": 7,
        "anchor_cvs": anchor_cvs,
        "cv_p95": cv_p95,
        "cv_p95_threshold": cv_p95_threshold,
        "delta_noise": delta_noise,
        "delta_noise_formula": (
            "exp(P95(abs(log(Q_ar)-median_r(log(Q_ar)))))-1"
        ),
        "applied_reduce_fn": "max",
        "status": "PASS" if cv_p95 <= cv_p95_threshold else "INCONCLUSIVE",
        "rows_digest": canonical_sha256(list(rows)),
    }
    return {**body, "noise_digest": canonical_sha256(body)}
