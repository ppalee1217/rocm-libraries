# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Candidate registry, fixed discovery schedule, and support tri-state."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from Tensile.ductile.evidence import canonical_config_hash, canonical_json_bytes, canonical_sha256

CHUNK_SIZE = 512
GLOBAL_CHUNKS = 32
MAX_CONDITIONAL_TARGETS = 15
CONDITIONAL_CHUNKS = 32
MAX_TOTAL_CHUNKS = 512
MAX_TOTAL_DRAWS = 262_144
FIRST_REFORECAST_CHUNK = 6
FIRST_REFORECAST_DRAWS = 3_072

ACTUAL_YAML_SOURCE = (
    "study_docs/research/ductile-origami-warmstart/protocol/v1/inputs/"
    "s10-generated.yaml"
)
ACTUAL_YAML_BLOB = "1fd6fb401d5baebd4665a87e9002687fb725b2dc"
ACTUAL_YAML_SHA256 = "faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36"
BENCHMARK_STRUCTS_BLOB = "4968b29b5eacddc56b20c42cb4b2c1e3d8d6f406"


class SupportError(ValueError):
    """Invalid registry, schedule, or support classification."""


class SupportState(str, Enum):
    SUPPORTED_WITNESSED = "supported_witnessed"
    SUPPORT_UNOBSERVED = "support_unobserved"
    SUPPORT_PROVEN_ABSENT = "support_proven_absent"


@dataclass(frozen=True)
class AxisSpec:
    axis_index: int
    axis_name: str
    values: tuple[Any, ...]
    grouped: bool
    frozen_free: bool
    currently_weighted: bool
    yaml_pointer: str
    value_yaml_pointers: tuple[str, ...] = ()
    derivation_indices_by_value: tuple[tuple[int, ...], ...] = ()
    probabilities: tuple[float, ...] = ()
    probabilities_raw_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.axis_index < 0:
            raise SupportError("axis_index must be non-negative")
        if not self.axis_name or "/" in self.axis_name:
            raise SupportError("axis_name must be non-empty and path-safe")
        if not self.values:
            raise SupportError("axis candidate list must not be empty")
        if self.value_yaml_pointers and len(self.value_yaml_pointers) != len(self.values):
            raise SupportError("value YAML pointer count must match candidates")
        if self.derivation_indices_by_value and len(
            self.derivation_indices_by_value
        ) != len(self.values):
            raise SupportError("derivation-index count must match candidates")
        if self.currently_weighted:
            if len(self.probabilities) != len(self.values):
                raise SupportError("weighted axis probabilities must match candidates")
            vector = np.asarray(self.probabilities, dtype=np.float32)
            if (
                not np.isfinite(vector).all()
                or (vector < 0).any()
                or not np.isclose(vector.sum(dtype=np.float32), 1.0, rtol=0, atol=1e-6)
            ):
                raise SupportError("weighted axis probabilities are invalid")
            if not self.probabilities_raw_sha256:
                raise SupportError("weighted axis probability bytes must be hashed")
            if (
                hashlib.sha256(vector.tobytes(order="C")).hexdigest()
                != self.probabilities_raw_sha256
            ):
                raise SupportError("weighted axis probability byte hash mismatch")
        elif self.probabilities or self.probabilities_raw_sha256 is not None:
            raise SupportError("unweighted axis must not supply weighted probabilities")


def _is_exact_int(value: Any, expected: int) -> bool:
    return type(value) is int and value == expected


def _priority(
    *,
    value: Any,
    axis: AxisSpec,
    value_index: int,
    atom_id: str,
    prelocked: bool,
) -> tuple[int, int, int, int, int, str]:
    sentinel_rank = 0 if _is_exact_int(value, -2) else 1 if _is_exact_int(value, -1) else 2
    axis_scope_rank = 0 if prelocked else 1 if axis.grouped else 2
    boundary_rank = (
        0 if value_index == 0 else 1 if value_index == len(axis.values) - 1 else 2
    )
    return (
        sentinel_rank,
        axis_scope_rank,
        boundary_rank,
        axis.axis_index,
        value_index,
        atom_id,
    )


class AtomRegistry:
    """Complete, typed, pre-draw registry for all ordered axis candidates."""

    def __init__(self, axes: Sequence[AxisSpec]):
        if len(axes) != 30:
            raise SupportError(f"S10R2 requires exactly 30 ordered axes, got {len(axes)}")
        ordered = sorted(axes, key=lambda axis: axis.axis_index)
        if [axis.axis_index for axis in ordered] != list(range(30)):
            raise SupportError("axis indices must be unique and contiguous 0..29")
        if len({axis.axis_name for axis in ordered}) != 30:
            raise SupportError("axis names must be unique")
        self.axes = tuple(ordered)
        self.rows = tuple(self._build_rows())
        if len({row["atom_id"] for row in self.rows}) != len(self.rows):
            raise SupportError("atom ids must be unique")

    def _build_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for axis in self.axes:
            prelocked_axis = (
                not axis.grouped
                and not axis.currently_weighted
                and axis.frozen_free
                and len(axis.values) > 1
            )
            symbols = ["BenchmarkProcess.__init__", "constructLazyForkPermutations"]
            if axis.grouped:
                symbols.extend(
                    ["_groupedParameterValueOptions", "_expandGroupedParameters"]
                )
            for value_index, value in enumerate(axis.values):
                value_bytes = canonical_json_bytes(value)
                value_sha256 = hashlib.sha256(value_bytes).hexdigest()
                atom_id = (
                    f"cand/a{axis.axis_index:02d}/v{value_index:05d}/"
                    f"{value_sha256[:16]}"
                )
                first = value_index == 0
                last = value_index == len(axis.values) - 1
                sentinel = _is_exact_int(value, -2) or _is_exact_int(value, -1)
                diagnostic = prelocked_axis or first or last or sentinel
                yaml_pointer = (
                    axis.value_yaml_pointers[value_index]
                    if axis.value_yaml_pointers
                    else f"{axis.yaml_pointer}/{value_index}"
                )
                derivation_indices = (
                    list(axis.derivation_indices_by_value[value_index])
                    if axis.derivation_indices_by_value
                    else []
                )
                rows.append(
                    {
                        "axis_id": f"axis/a{axis.axis_index:02d}/{axis.axis_name}",
                        "atom_id": atom_id,
                        "axis_index": axis.axis_index,
                        "axis_name": axis.axis_name,
                        "value_index": value_index,
                        "candidate_count": len(axis.values),
                        "grouped": axis.grouped,
                        "frozen_free": axis.frozen_free,
                        "currently_weighted": axis.currently_weighted,
                        "exact_typed_value": value,
                        "value_canonical_json_hex": value_bytes.hex(),
                        "value_sha256": value_sha256,
                        "actual_yaml_source": ACTUAL_YAML_SOURCE,
                        "actual_yaml_blob": ACTUAL_YAML_BLOB,
                        "actual_yaml_sha256": ACTUAL_YAML_SHA256,
                        "yaml_pointer": yaml_pointer,
                        "candidate_source_blob": BENCHMARK_STRUCTS_BLOB,
                        "source_symbols": symbols,
                        "derivation_indices": derivation_indices,
                        "role_flags": {
                            "prelocked_candidate": prelocked_axis,
                            "conditional_diagnostic": diagnostic,
                            "first": first,
                            "last": last,
                            "sentinel_minus_two": _is_exact_int(value, -2),
                            "sentinel_minus_one": _is_exact_int(value, -1),
                        },
                        "conditional_priority": list(
                            _priority(
                                value=value,
                                axis=axis,
                                value_index=value_index,
                                atom_id=atom_id,
                                prelocked=prelocked_axis,
                            )
                        ),
                    }
                )
        return rows

    def document(self) -> dict[str, Any]:
        axes = []
        atom_ids_by_axis: dict[int, list[str]] = {}
        for row in self.rows:
            atom_ids_by_axis.setdefault(row["axis_index"], []).append(row["atom_id"])
        for axis in self.axes:
            probability = (
                {
                    "kind": "actual_float32_weighted",
                    "values": list(axis.probabilities),
                    "raw_sha256": axis.probabilities_raw_sha256,
                    "sum_float32": float(
                        np.asarray(axis.probabilities, dtype=np.float32).sum(
                            dtype=np.float32
                        )
                    ),
                }
                if axis.currently_weighted
                else {"kind": "uniform", "values": None, "raw_sha256": None}
            )
            axes.append(
                {
                    "axis_id": f"axis/a{axis.axis_index:02d}/{axis.axis_name}",
                    "axis_index": axis.axis_index,
                    "axis_name": axis.axis_name,
                    "candidate_count": len(axis.values),
                    "grouped": axis.grouped,
                    "frozen_free": axis.frozen_free,
                    "currently_weighted": axis.currently_weighted,
                    "yaml_pointer": axis.yaml_pointer,
                    "candidate_atom_ids": atom_ids_by_axis[axis.axis_index],
                    "candidates_sha256": canonical_sha256(list(axis.values)),
                    "probability": probability,
                }
            )
        body = {
            "schema_version": 1,
            "checkpoint_id": "S10R2",
            "axis_count": 30,
            "axis_order": [axis.axis_name for axis in self.axes],
            "axes": axes,
            "row_count": len(self.rows),
            "always_required_structural_atoms": [],
            "rows": list(self.rows),
        }
        return {**body, "registry_digest": canonical_sha256(body)}

    def row_by_atom(self) -> dict[str, Mapping[str, Any]]:
        return {row["atom_id"]: row for row in self.rows}

    def prelocked_atoms(self) -> frozenset[str]:
        return frozenset(
            row["atom_id"] for row in self.rows if row["role_flags"]["prelocked_candidate"]
        )

    def diagnostic_atoms(self) -> frozenset[str]:
        return frozenset(
            row["atom_id"] for row in self.rows if row["role_flags"]["conditional_diagnostic"]
        )


def axis_specs_from_registry(document: Mapping[str, Any]) -> tuple[AxisSpec, ...]:
    """Reconstruct and verify typed axis specifications from a sealed registry."""

    body = dict(document)
    recorded_digest = body.pop("registry_digest", None)
    if recorded_digest != canonical_sha256(body):
        raise SupportError("candidate registry digest mismatch")
    axes = document.get("axes")
    rows = document.get("rows")
    if not isinstance(axes, Sequence) or isinstance(axes, (str, bytes)):
        raise SupportError("candidate registry axes must be a sequence")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise SupportError("candidate registry rows must be a sequence")
    rows_by_axis: dict[int, list[Mapping[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise SupportError("candidate registry row must be an object")
        rows_by_axis.setdefault(int(row["axis_index"]), []).append(row)
    result: list[AxisSpec] = []
    for axis in axes:
        if not isinstance(axis, Mapping):
            raise SupportError("candidate registry axis must be an object")
        axis_index = int(axis["axis_index"])
        candidates = sorted(
            rows_by_axis.get(axis_index, []), key=lambda row: int(row["value_index"])
        )
        if [int(row["value_index"]) for row in candidates] != list(
            range(int(axis["candidate_count"]))
        ):
            raise SupportError("candidate registry value indices are incomplete")
        probability = axis.get("probability")
        if not isinstance(probability, Mapping):
            raise SupportError("candidate registry probability must be an object")
        weighted = bool(axis["currently_weighted"])
        probabilities = (
            tuple(float(value) for value in probability["values"]) if weighted else ()
        )
        result.append(
            AxisSpec(
                axis_index=axis_index,
                axis_name=str(axis["axis_name"]),
                values=tuple(row["exact_typed_value"] for row in candidates),
                grouped=bool(axis["grouped"]),
                frozen_free=bool(axis["frozen_free"]),
                currently_weighted=weighted,
                yaml_pointer=str(axis["yaml_pointer"]),
                value_yaml_pointers=tuple(str(row["yaml_pointer"]) for row in candidates),
                derivation_indices_by_value=tuple(
                    tuple(int(value) for value in row["derivation_indices"])
                    for row in candidates
                ),
                probabilities=probabilities,
                probabilities_raw_sha256=(
                    str(probability["raw_sha256"]) if weighted else None
                ),
            )
        )
    rebuilt = AtomRegistry(result)
    if rebuilt.document() != document:
        raise SupportError("candidate registry does not round-trip exactly")
    return rebuilt.axes


def classify_support(
    registry: AtomRegistry,
    witnessed_atoms: set[str] | frozenset[str],
    complete_absence_proofs: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, str]:
    """Classify each atom without turning stochastic non-discovery into absence."""

    rows = registry.row_by_atom()
    unknown_witnesses = sorted(set(witnessed_atoms).difference(rows))
    if unknown_witnesses:
        raise SupportError(f"witness references unknown atoms: {unknown_witnesses}")
    proofs = complete_absence_proofs or {}
    unknown_proofs = sorted(set(proofs).difference(rows))
    if unknown_proofs:
        raise SupportError(f"absence proof references unknown atoms: {unknown_proofs}")
    overlap = sorted(set(witnessed_atoms).intersection(proofs))
    if overlap:
        raise SupportError(f"atom cannot be both witnessed and proven absent: {overlap}")
    states: dict[str, str] = {}
    for atom_id in rows:
        if atom_id in witnessed_atoms:
            states[atom_id] = SupportState.SUPPORTED_WITNESSED.value
        elif atom_id in proofs:
            proof = proofs[atom_id]
            if proof.get("proof_kind") not in {
                "finite_exhaustive",
                "sound_constraint",
                "independently_validated_complete_equivalent",
            }:
                raise SupportError(f"incomplete absence proof for {atom_id}")
            if not proof.get("proof_digest"):
                raise SupportError(f"absence proof digest missing for {atom_id}")
            states[atom_id] = SupportState.SUPPORT_PROVEN_ABSENT.value
        else:
            states[atom_id] = SupportState.SUPPORT_UNOBSERVED.value
    return states


def activate_targets(
    registry: AtomRegistry,
    global_states: Mapping[str, str],
    *,
    completed_global_chunks: int,
) -> list[str]:
    """Mechanically activate the first fifteen unobserved diagnostic atoms."""

    if completed_global_chunks != GLOBAL_CHUNKS:
        raise SupportError("conditional activation requires exactly 32 complete global chunks")
    rows = registry.row_by_atom()
    if set(global_states) != set(rows):
        raise SupportError("global support state must cover the complete atom registry")
    candidates = [
        row
        for row in registry.rows
        if row["role_flags"]["conditional_diagnostic"]
        and global_states[row["atom_id"]] == SupportState.SUPPORT_UNOBSERVED.value
    ]
    candidates.sort(key=lambda row: tuple(row["conditional_priority"]))
    return [row["atom_id"] for row in candidates[:MAX_CONDITIONAL_TARGETS]]


def schedule_summary(conditional_targets: Sequence[str]) -> dict[str, int]:
    if len(conditional_targets) > MAX_CONDITIONAL_TARGETS:
        raise SupportError("more than fifteen conditional targets")
    if len(set(conditional_targets)) != len(conditional_targets):
        raise SupportError("conditional targets must be unique")
    total_chunks = GLOBAL_CHUNKS + len(conditional_targets) * CONDITIONAL_CHUNKS
    total_draws = total_chunks * CHUNK_SIZE
    if total_chunks > MAX_TOTAL_CHUNKS or total_draws > MAX_TOTAL_DRAWS:
        raise SupportError("fixed schedule exceeds S10R2 ceiling")
    return {
        "chunk_size": CHUNK_SIZE,
        "global_chunks": GLOBAL_CHUNKS,
        "conditional_target_count": len(conditional_targets),
        "conditional_chunks_each": CONDITIONAL_CHUNKS,
        "total_chunks": total_chunks,
        "total_draws": total_draws,
    }


def deterministic_chunk_seed(
    base_seed: int,
    *,
    stream_id: str,
    chunk_index: int,
) -> int:
    if base_seed < 0 or chunk_index < 0 or not stream_id:
        raise SupportError("invalid seed inputs")
    payload = canonical_json_bytes(
        {
            "checkpoint": "S10R2",
            "base_seed": base_seed,
            "stream_id": stream_id,
            "chunk_index": chunk_index,
        }
    )
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")


def sample_discovery_chunk(
    axes: Sequence[AxisSpec],
    probabilities: Mapping[str, Sequence[float]],
    validator: Callable[[Mapping[str, Any]], tuple[bool, str]],
    *,
    base_seed: int,
    stream_id: str,
    chunk_index: int,
    fixed_atom: Mapping[str, Any] | None = None,
    chunk_size: int = CHUNK_SIZE,
) -> dict[str, Any]:
    """Execute one deterministic validity-only chunk.

    The caller supplies the pinned validator.  Only accepted configs and a
    rejection taxonomy are retained; no Formocast, GFLOPS, or GPU value enters
    this function.
    """

    draws = generate_discovery_draws(
        axes,
        probabilities,
        base_seed=base_seed,
        stream_id=stream_id,
        chunk_index=chunk_index,
        fixed_atom=fixed_atom,
        chunk_size=chunk_size,
    )
    validation_results = []
    for draw in draws["rows"]:
        try:
            valid, reason = validator(draw["config"])
        except Exception as error:
            valid = False
            reason = f"validator_exception:{type(error).__name__}"
        validation_results.append({"valid": bool(valid), "reason": reason})
    return finalize_discovery_chunk(draws, validation_results)


def generate_discovery_draws(
    axes: Sequence[AxisSpec],
    probabilities: Mapping[str, Sequence[float]],
    *,
    base_seed: int,
    stream_id: str,
    chunk_index: int,
    fixed_atom: Mapping[str, Any] | None = None,
    chunk_size: int = CHUNK_SIZE,
) -> dict[str, Any]:
    """Generate the exact deterministic configs without evaluating validity."""

    if chunk_size != CHUNK_SIZE:
        raise SupportError("formal S10R2 chunk size is exactly 512")
    ordered = sorted(axes, key=lambda axis: axis.axis_index)
    seed = deterministic_chunk_seed(
        base_seed, stream_id=stream_id, chunk_index=chunk_index
    )
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    fixed_axis = None if fixed_atom is None else fixed_atom.get("axis_name")
    fixed_value = None if fixed_atom is None else fixed_atom.get("exact_typed_value")
    for draw_index in range(CHUNK_SIZE):
        config: dict[str, Any] = {}
        candidate_indices: dict[str, int] = {}
        for axis in ordered:
            if axis.axis_name == fixed_axis:
                value_index = next(
                    (
                        index
                        for index, value in enumerate(axis.values)
                        if canonical_json_bytes(value) == canonical_json_bytes(fixed_value)
                    ),
                    None,
                )
                if value_index is None:
                    raise SupportError("fixed atom value is absent from its axis")
            else:
                p = probabilities.get(axis.axis_name)
                if p is not None:
                    vector = np.asarray(p, dtype=np.float32)
                    if vector.shape != (len(axis.values),):
                        raise SupportError(f"probability length mismatch for {axis.axis_name}")
                    if not np.isclose(vector.sum(), 1.0, rtol=0, atol=1e-6):
                        raise SupportError(f"probabilities do not sum to one for {axis.axis_name}")
                    value_index = int(rng.choice(len(axis.values), p=vector))
                else:
                    value_index = int(rng.choice(len(axis.values)))
            config[axis.axis_name] = axis.values[value_index]
            candidate_indices[axis.axis_name] = value_index
        rows.append(
            {
                "draw_index": draw_index,
                "config": config,
                "candidate_indices": candidate_indices,
                "config_hash": canonical_config_hash(config),
            }
        )
    return {
        "schema_version": 1,
        "stream_id": stream_id,
        "chunk_index": chunk_index,
        "seed": seed,
        "draws": CHUNK_SIZE,
        "fixed_atom_id": None if fixed_atom is None else fixed_atom.get("atom_id"),
        "rows": rows,
    }


def finalize_discovery_chunk(
    draws: Mapping[str, Any],
    validation_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Join pinned validator results with deterministic draws and discard rejects."""

    rows = draws.get("rows")
    if (
        not isinstance(rows, Sequence)
        or isinstance(rows, (str, bytes))
        or len(rows) != CHUNK_SIZE
        or len(validation_results) != CHUNK_SIZE
    ):
        raise SupportError("discovery chunk/result cardinality mismatch")
    accepted: list[dict[str, Any]] = []
    rejection_taxonomy: dict[str, int] = {}
    for draw, result in zip(rows, validation_results):
        valid = result.get("valid")
        reason = result.get("reason")
        if type(valid) is not bool:
            raise SupportError("validator result valid flag must be boolean")
        if valid:
            accepted.append(dict(draw))
        else:
            reason = str(reason or "validator_false")
            rejection_taxonomy[reason] = rejection_taxonomy.get(reason, 0) + 1
    body = {
        "schema_version": 1,
        "stream_id": draws["stream_id"],
        "chunk_index": draws["chunk_index"],
        "seed": draws["seed"],
        "draws": CHUNK_SIZE,
        "fixed_atom_id": draws.get("fixed_atom_id"),
        "accepted": accepted,
        "accepted_count": len(accepted),
        "rejected_count": CHUNK_SIZE - len(accepted),
        "rejection_taxonomy": dict(sorted(rejection_taxonomy.items())),
    }
    return {**body, "chunk_digest": canonical_sha256(body)}
