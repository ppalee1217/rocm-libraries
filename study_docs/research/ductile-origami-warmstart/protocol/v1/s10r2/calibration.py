# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Outcome-blind S10R2 calibration and deterministic numeric-cap derivation."""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from Tensile.ductile.evidence import atomic_write_json, canonical_sha256

from .support import GLOBAL_CHUNKS, MAX_TOTAL_CHUNKS


class CalibrationError(ValueError):
    """Invalid allocation, calibration metric, or cap proposal."""


@dataclass(frozen=True)
class Allocation:
    allocation_id: str
    container_name: str
    device_arch: str
    partition_mode: str
    numa_mode: str
    available_wall_s: float
    available_cpu_s: float
    available_gpu_s: float
    valid_from_utc: str
    valid_until_utc: str
    confirmed: bool


@dataclass(frozen=True)
class CalibrationMetrics:
    """Only synthetic/foundation timing and storage measurements are allowed."""

    selection_chunk_wall_s: float
    selection_chunk_cpu_s: float
    mapping_row_wall_s: float
    mapping_row_cpu_s: float
    correctness_cell_wall_s: float
    correctness_cell_cpu_s: float
    correctness_cell_gpu_s: float
    noise_cell_wall_s: float
    noise_cell_cpu_s: float
    noise_cell_gpu_s: float
    native_build_wall_s: float
    native_build_cpu_s: float
    fixed_overhead_wall_s: float
    fixed_overhead_cpu_s: float
    projected_transient_storage_bytes: int

    def __post_init__(self) -> None:
        for field, value in asdict(self).items():
            if value < 0:
                raise CalibrationError(f"calibration metric {field} must be non-negative")
        if self.selection_chunk_wall_s == 0 or self.selection_chunk_cpu_s == 0:
            raise CalibrationError("selection calibration metrics must be non-zero")


@dataclass(frozen=True)
class ResourceCaps:
    wall_s: int
    cpu_s: int
    gpu_s: int
    transient_storage_bytes: int
    safety_factor: float
    derivation_digest: str


def parse_utc_timestamp(value: Any, *, field: str) -> dt.datetime:
    """Parse one strict, timezone-aware UTC timestamp."""

    if not isinstance(value, str) or not value or value != value.strip():
        raise CalibrationError(f"{field} must be a non-empty UTC timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CalibrationError(f"{field} is not a valid UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise CalibrationError(f"{field} must be timezone-aware UTC")
    return parsed.astimezone(dt.timezone.utc)


def validate_allocation(
    allocation: Allocation,
    *,
    at_utc: dt.datetime | None = None,
    required_duration_s: float = 0.0,
) -> tuple[dt.datetime, dt.datetime]:
    """Validate identity, numeric limits, and the active allocation window."""

    if not allocation.confirmed:
        raise CalibrationError("allocation is not confirmed")
    if allocation.container_name != "perlee":
        raise CalibrationError("allocation must bind the existing perlee container")
    if allocation.device_arch != "gfx942":
        raise CalibrationError("allocation must bind gfx942")
    if allocation.partition_mode != "SPX" or allocation.numa_mode != "NPS1":
        raise CalibrationError("allocation must bind SPX/NPS1")
    if not allocation.allocation_id:
        raise CalibrationError("allocation_id must not be empty")
    if not allocation.valid_from_utc or not allocation.valid_until_utc:
        raise CalibrationError("allocation time window is incomplete")
    for name in ("available_wall_s", "available_cpu_s", "available_gpu_s"):
        if float(getattr(allocation, name)) <= 0:
            raise CalibrationError(f"{name} must be positive")
    start = parse_utc_timestamp(
        allocation.valid_from_utc, field="valid_from_utc"
    )
    end = parse_utc_timestamp(
        allocation.valid_until_utc, field="valid_until_utc"
    )
    if start >= end:
        raise CalibrationError("allocation time window must have start before end")
    current = at_utc or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None or current.utcoffset() != dt.timedelta(0):
        raise CalibrationError("allocation validation time must be timezone-aware UTC")
    current = current.astimezone(dt.timezone.utc)
    if current < start:
        raise CalibrationError("allocation time window is not yet active")
    if current >= end:
        raise CalibrationError("allocation time window has expired")
    if (
        isinstance(required_duration_s, bool)
        or not isinstance(required_duration_s, (int, float))
        or not math.isfinite(float(required_duration_s))
        or float(required_duration_s) < 0
    ):
        raise CalibrationError(
            "required allocation duration must be finite and non-negative"
        )
    if current + dt.timedelta(seconds=float(required_duration_s)) > end:
        raise CalibrationError(
            "allocation time window cannot cover the required duration"
        )
    return start, end


def derive_caps(
    allocation: Allocation,
    metrics: CalibrationMetrics,
    *,
    safety_factor: float = 2.0,
    shared_stage_wall_s: int = 7 * 24 * 60 * 60,
    storage_ceiling_bytes: int = 5 * 1024**3,
) -> ResourceCaps:
    """Derive full-panel caps without consulting any outcome-bearing value."""

    validate_allocation(allocation)
    if not math.isfinite(safety_factor) or safety_factor < 1.0:
        raise CalibrationError("safety_factor must be finite and at least one")
    if shared_stage_wall_s <= 0 or storage_ceiling_bytes <= 0:
        raise CalibrationError("shared ceilings must be positive")

    mapping_rows = 60  # 30 rows in each fresh A/B pass
    correctness_cells = 9
    noise_cells = 63
    wall_need = (
        MAX_TOTAL_CHUNKS * metrics.selection_chunk_wall_s
        + mapping_rows * metrics.mapping_row_wall_s
        + correctness_cells * metrics.correctness_cell_wall_s
        + noise_cells * metrics.noise_cell_wall_s
        + metrics.native_build_wall_s
        + metrics.fixed_overhead_wall_s
    )
    cpu_need = (
        MAX_TOTAL_CHUNKS * metrics.selection_chunk_cpu_s
        + mapping_rows * metrics.mapping_row_cpu_s
        + correctness_cells * metrics.correctness_cell_cpu_s
        + noise_cells * metrics.noise_cell_cpu_s
        + metrics.native_build_cpu_s
        + metrics.fixed_overhead_cpu_s
    )
    gpu_need = (
        correctness_cells * metrics.correctness_cell_gpu_s
        + noise_cells * metrics.noise_cell_gpu_s
    )
    proposed = {
        "wall_s": math.ceil(wall_need * safety_factor),
        "cpu_s": math.ceil(cpu_need * safety_factor),
        "gpu_s": max(1, math.ceil(gpu_need * safety_factor)),
        "transient_storage_bytes": metrics.projected_transient_storage_bytes,
    }
    if proposed["transient_storage_bytes"] <= 0:
        raise CalibrationError("projected transient storage must be positive")
    if proposed["transient_storage_bytes"] > storage_ceiling_bytes:
        raise CalibrationError("projected transient storage exceeds 5 GiB ceiling")
    available = {
        "wall_s": min(int(allocation.available_wall_s), shared_stage_wall_s),
        "cpu_s": int(allocation.available_cpu_s),
        "gpu_s": int(allocation.available_gpu_s),
    }
    exceeded = [
        name for name in ("wall_s", "cpu_s", "gpu_s") if proposed[name] > available[name]
    ]
    if exceeded:
        raise CalibrationError(
            "full frozen panel does not fit confirmed allocation: " + ", ".join(exceeded)
        )
    body = {
        "schema_version": 1,
        "allocation": asdict(allocation),
        "calibration_metrics": asdict(metrics),
        "schedule": {
            "global_chunks": GLOBAL_CHUNKS,
            "maximum_total_chunks": MAX_TOTAL_CHUNKS,
            "mapping_rows_ab": mapping_rows,
            "correctness_cells": correctness_cells,
            "noise_cells": noise_cells,
        },
        "safety_factor": safety_factor,
        "proposed": proposed,
        "shared_stage_wall_s": shared_stage_wall_s,
        "storage_ceiling_bytes": storage_ceiling_bytes,
    }
    digest = canonical_sha256(body)
    return ResourceCaps(
        wall_s=proposed["wall_s"],
        cpu_s=proposed["cpu_s"],
        gpu_s=proposed["gpu_s"],
        transient_storage_bytes=proposed["transient_storage_bytes"],
        safety_factor=safety_factor,
        derivation_digest=digest,
    )


def write_calibration_fixture(
    path: Path | str,
    *,
    contract_digest: str,
    source_identity: Mapping[str, Any],
    allocation: Allocation,
    metrics: CalibrationMetrics,
    caps: ResourceCaps | None,
    preemp_engineering_s: float,
    status: str,
    reason: str | None,
) -> dict[str, Any]:
    if status not in {"CALIBRATION_COMPLETE", "BLOCKED"}:
        raise CalibrationError("invalid calibration status")
    if preemp_engineering_s < 0:
        raise CalibrationError("preemp_engineering_s must be non-negative")
    document = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "outcome_blind": True,
        "contract_digest": contract_digest,
        "source_identity": dict(source_identity),
        "allocation": asdict(allocation),
        "calibration_metrics": asdict(metrics),
        "proposed_caps": None if caps is None else asdict(caps),
        "preemp_engineering_s": preemp_engineering_s,
        "status": status,
        "reason": reason,
        "forbidden_payloads_absent": [
            "actual_validity_draws",
            "support_classification",
            "formocast_scores",
            "gflops",
            "correctness_labels",
            "noise_labels",
            "s10r1_artifacts",
        ],
    }
    document["fixture_digest"] = canonical_sha256(document)
    atomic_write_json(path, document, exclusive=True)
    return document
