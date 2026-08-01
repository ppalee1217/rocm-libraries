# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Fresh S10R3 registry, stateless sampling, schedule, and support tri-state."""

from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any, Callable, Mapping, Sequence

from .contract import canonical_json_bytes, canonical_sha256


class ProtocolError(ValueError):
    """The fixed discovery protocol or typed registry was violated."""


CHUNK_SIZE = 512
GLOBAL_CHUNKS = 32
CONDITIONAL_CHUNKS = 32
MAX_CONDITIONAL_TARGETS = 15
MAX_TOTAL_CHUNKS = 512
MAX_TOTAL_DRAWS = 262_144
FIRST_REFORECAST_CHUNK = 6
SEED_NAMESPACE = "S10R3|A45|clean-restart|2026-07-30|v1"
SEED_NAMESPACE_SHA256 = (
    "6cff1a13675818285047f6b64d97c7918bd0453974623d9ede59cb313be79ca6"
)
CATEGORICAL_DOMAIN = b"S10R3-CATEGORICAL-V1"

ACTUAL_YAML_SOURCE = (
    "study_docs/research/ductile-origami-warmstart/protocol/v1/inputs/"
    "s10-generated.yaml"
)
ACTUAL_YAML_BLOB = "1fd6fb401d5baebd4665a87e9002687fb725b2dc"
ACTUAL_YAML_SHA256 = "faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36"
BENCHMARK_STRUCTS_BLOB = "4968b29b5eacddc56b20c42cb4b2c1e3d8d6f406"


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
        if type(self.axis_index) is not int or self.axis_index < 0:
            raise ProtocolError("axis_index must be a non-negative exact integer")
        if not self.axis_name or "/" in self.axis_name:
            raise ProtocolError("axis_name must be non-empty and path-safe")
        if not self.values:
            raise ProtocolError("axis candidate list must not be empty")
        canonical_json_bytes(list(self.values))
        if self.value_yaml_pointers and len(self.value_yaml_pointers) != len(self.values):
            raise ProtocolError("candidate/YAML pointer cardinality mismatch")
        if self.derivation_indices_by_value and len(
            self.derivation_indices_by_value
        ) != len(self.values):
            raise ProtocolError("candidate/derivation cardinality mismatch")
        if self.currently_weighted:
            if len(self.probabilities) != len(self.values):
                raise ProtocolError("weighted probability cardinality mismatch")
            packed = b"".join(struct.pack("=f", value) for value in self.probabilities)
            unpacked = tuple(struct.unpack("=f", packed[i : i + 4])[0] for i in range(0, len(packed), 4))
            if any(not math.isfinite(value) or value < 0 for value in unpacked):
                raise ProtocolError("weighted probability is invalid")
            if not math.isclose(sum(unpacked), 1.0, rel_tol=0.0, abs_tol=1e-6):
                raise ProtocolError("weighted probability sum is invalid")
            if hashlib.sha256(packed).hexdigest() != self.probabilities_raw_sha256:
                raise ProtocolError("weighted probability byte digest mismatch")
        elif self.probabilities or self.probabilities_raw_sha256 is not None:
            raise ProtocolError("uniform axis cannot bind probabilities")


def _exact_int(value: Any, expected: int) -> bool:
    return type(value) is int and value == expected


def _priority(
    axis: AxisSpec, value: Any, value_index: int, atom_id: str, prelocked: bool
) -> tuple[int, int, int, int, int, str]:
    sentinel_rank = 0 if _exact_int(value, -2) else 1 if _exact_int(value, -1) else 2
    axis_scope_rank = 0 if prelocked else 1 if axis.grouped else 2
    boundary_rank = 0 if value_index == 0 else 1 if value_index == len(axis.values) - 1 else 2
    return (
        sentinel_rank,
        axis_scope_rank,
        boundary_rank,
        axis.axis_index,
        value_index,
        atom_id,
    )


class AtomRegistry:
    """Complete S10R3-owned typed registry for the 30 pinned axes."""

    def __init__(self, axes: Sequence[AxisSpec]):
        ordered = tuple(sorted(axes, key=lambda item: item.axis_index))
        if len(ordered) != 30:
            raise ProtocolError(f"S10R3 requires 30 axes, got {len(ordered)}")
        if tuple(item.axis_index for item in ordered) != tuple(range(30)):
            raise ProtocolError("axis indices must be contiguous 0..29")
        if len({item.axis_name for item in ordered}) != 30:
            raise ProtocolError("axis names must be unique")
        self.axes = ordered
        self.rows = tuple(self._rows())
        if len({item["atom_id"] for item in self.rows}) != len(self.rows):
            raise ProtocolError("atom IDs must be unique")

    def _rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for axis in self.axes:
            prelocked = (
                not axis.grouped
                and not axis.currently_weighted
                and axis.frozen_free
                and len(axis.values) > 1
            )
            source_symbols = [
                "BenchmarkProcess.__init__",
                "constructLazyForkPermutations",
            ]
            if axis.grouped:
                source_symbols += [
                    "_groupedParameterValueOptions",
                    "_expandGroupedParameters",
                ]
            for value_index, value in enumerate(axis.values):
                value_bytes = canonical_json_bytes(value)
                value_digest = hashlib.sha256(value_bytes).hexdigest()
                atom_id = f"cand/a{axis.axis_index:02d}/v{value_index:05d}/{value_digest[:16]}"
                first = value_index == 0
                last = value_index == len(axis.values) - 1
                sentinel_minus_two = _exact_int(value, -2)
                sentinel_minus_one = _exact_int(value, -1)
                diagnostic = prelocked or first or last or sentinel_minus_two or sentinel_minus_one
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
                        "typed_value": value,
                        "canonical_value_bytes": value_bytes.hex(),
                        "value_sha256": value_digest,
                        "yaml_pointer": (
                            axis.value_yaml_pointers[value_index]
                            if axis.value_yaml_pointers
                            else f"{axis.yaml_pointer}/{value_index}"
                        ),
                        "source_symbol_and_blob": {
                            "symbols": source_symbols,
                            "git_blob": BENCHMARK_STRUCTS_BLOB,
                        },
                        "actual_yaml": {
                            "path": ACTUAL_YAML_SOURCE,
                            "git_blob": ACTUAL_YAML_BLOB,
                            "sha256": ACTUAL_YAML_SHA256,
                        },
                        "derivation_indices": (
                            list(axis.derivation_indices_by_value[value_index])
                            if axis.derivation_indices_by_value
                            else []
                        ),
                        "nominal_role_flags": {
                            "prelocked_candidate": prelocked,
                            "conditional_diagnostic": diagnostic,
                            "first": first,
                            "last": last,
                            "sentinel_minus_two": sentinel_minus_two,
                            "sentinel_minus_one": sentinel_minus_one,
                        },
                        "operational_semantic_category": (
                            "grouped"
                            if axis.grouped
                            else "weighted"
                            if axis.currently_weighted
                            else "residual"
                        ),
                        "deterministic_priority": list(
                            _priority(axis, value, value_index, atom_id, prelocked)
                        ),
                        "conditional_eligibility": diagnostic,
                    }
                )
        return rows

    def document(self) -> dict[str, Any]:
        rows_by_axis: dict[int, list[str]] = {}
        for row in self.rows:
            rows_by_axis.setdefault(row["axis_index"], []).append(row["atom_id"])
        axes = []
        for axis in self.axes:
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
                    "candidate_atom_ids": rows_by_axis[axis.axis_index],
                    "candidates_sha256": canonical_sha256(list(axis.values)),
                    "probability": (
                        {
                            "kind": "actual_float32_weighted",
                            "values": list(axis.probabilities),
                            "raw_sha256": axis.probabilities_raw_sha256,
                        }
                        if axis.currently_weighted
                        else {"kind": "uniform", "values": None, "raw_sha256": None}
                    ),
                }
            )
        body = {
            "document_kind": "candidate_registry",
            "schema_version": 1,
            "checkpoint_id": "S10R3",
            "axis_count": 30,
            "axis_order": [item.axis_name for item in self.axes],
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
            row["atom_id"]
            for row in self.rows
            if row["nominal_role_flags"]["prelocked_candidate"]
        )

    def diagnostic_atoms(self) -> frozenset[str]:
        return frozenset(
            row["atom_id"] for row in self.rows if row["conditional_eligibility"]
        )


def axis_specs_from_registry(document: Mapping[str, Any]) -> tuple[AxisSpec, ...]:
    body = dict(document)
    digest = body.pop("registry_digest", None)
    if digest != canonical_sha256(body):
        raise ProtocolError("candidate registry digest mismatch")
    if document.get("checkpoint_id") != "S10R3":
        raise ProtocolError("foreign candidate registry")
    rows_by_axis: dict[int, list[Mapping[str, Any]]] = {}
    for row in document.get("rows", []):
        if type(row) is not dict or type(row.get("axis_index")) is not int:
            raise ProtocolError("candidate registry row is malformed")
        rows_by_axis.setdefault(row["axis_index"], []).append(row)
    result = []
    for axis in document.get("axes", []):
        axis_index = axis["axis_index"]
        rows = sorted(rows_by_axis.get(axis_index, []), key=lambda row: row["value_index"])
        if [row["value_index"] for row in rows] != list(range(axis["candidate_count"])):
            raise ProtocolError("candidate indices are incomplete")
        probability = axis["probability"]
        result.append(
            AxisSpec(
                axis_index=axis_index,
                axis_name=axis["axis_name"],
                values=tuple(row["typed_value"] for row in rows),
                grouped=axis["grouped"],
                frozen_free=axis["frozen_free"],
                currently_weighted=axis["currently_weighted"],
                yaml_pointer=axis["yaml_pointer"],
                value_yaml_pointers=tuple(row["yaml_pointer"] for row in rows),
                derivation_indices_by_value=tuple(
                    tuple(row["derivation_indices"]) for row in rows
                ),
                probabilities=(
                    tuple(probability["values"])
                    if axis["currently_weighted"]
                    else ()
                ),
                probabilities_raw_sha256=probability["raw_sha256"],
            )
        )
    rebuilt = AtomRegistry(result)
    if rebuilt.document() != document:
        raise ProtocolError("candidate registry does not round-trip exactly")
    return rebuilt.axes


def _length_delimited(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return len(encoded).to_bytes(8, "big") + encoded


def deterministic_seed(
    stream_id: str,
    conditional_atom_id: str | None,
    chunk_index: int,
    draw_index: int,
) -> int:
    if (
        type(chunk_index) is not int
        or type(draw_index) is not int
        or not 0 <= chunk_index < 2**64
        or not 0 <= draw_index < 2**64
    ):
        raise ProtocolError("seed indices must be unsigned 64-bit integers")
    atom = conditional_atom_id if conditional_atom_id is not None else "GLOBAL"
    material = b"".join(
        (
            _length_delimited(SEED_NAMESPACE),
            _length_delimited(stream_id),
            _length_delimited(atom),
            chunk_index.to_bytes(8, "big"),
            draw_index.to_bytes(8, "big"),
        )
    )
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big")


def categorical_u64(seed: int, axis_index: int) -> int:
    if type(seed) is not int or type(axis_index) is not int:
        raise ProtocolError("categorical seed and axis index must be exact integers")
    return int.from_bytes(
        hashlib.sha256(
            CATEGORICAL_DOMAIN
            + seed.to_bytes(8, "big")
            + axis_index.to_bytes(8, "big")
        ).digest()[:8],
        "big",
    )


def uniform_masses(count: int) -> tuple[int, ...]:
    if type(count) is not int or count <= 0:
        raise ProtocolError("uniform cardinality must be a positive exact integer")
    quotient, remainder = divmod(2**64, count)
    masses = tuple(quotient + (1 if index < remainder else 0) for index in range(count))
    if sum(masses) != 2**64:
        raise ProtocolError("uniform integer mass invariant failed")
    return masses


def weighted_masses(probabilities: Sequence[float]) -> tuple[int, ...]:
    if not probabilities:
        raise ProtocolError("weighted probabilities cannot be empty")
    values = []
    for value in probabilities:
        packed = struct.pack("=f", value)
        rounded = struct.unpack("=f", packed)[0]
        if not math.isfinite(rounded) or rounded < 0:
            raise ProtocolError("invalid float32 probability")
        values.append(Fraction(*rounded.as_integer_ratio()))
    total = sum(values, Fraction())
    if total <= 0:
        raise ProtocolError("weighted probability total must be positive")
    exact = [value * 2**64 / total for value in values]
    floors = [item.numerator // item.denominator for item in exact]
    remaining = 2**64 - sum(floors)
    ranks = sorted(
        range(len(values)),
        key=lambda index: (-(exact[index] - floors[index]), index),
    )
    for index in ranks[:remaining]:
        floors[index] += 1
    if sum(floors) != 2**64 or any(item < 0 for item in floors):
        raise ProtocolError("weighted integer mass invariant failed")
    return tuple(floors)


def categorical_index(axis: AxisSpec, u64: int) -> int:
    if type(u64) is not int or not 0 <= u64 < 2**64:
        raise ProtocolError("categorical variate must be unsigned 64-bit")
    masses = (
        weighted_masses(axis.probabilities)
        if axis.currently_weighted
        else uniform_masses(len(axis.values))
    )
    cumulative = 0
    for index, mass in enumerate(masses):
        cumulative += mass
        if u64 < cumulative:
            return index
    raise ProtocolError("categorical partition does not cover uint64")


def sample_config(
    axes: Sequence[AxisSpec],
    *,
    stream_id: str,
    conditional_atom_id: str | None,
    chunk_index: int,
    draw_index: int,
    registry: AtomRegistry,
) -> dict[str, Any]:
    seed = deterministic_seed(stream_id, conditional_atom_id, chunk_index, draw_index)
    config = {
        axis.axis_name: axis.values[
            categorical_index(axis, categorical_u64(seed, axis.axis_index))
        ]
        for axis in axes
    }
    if conditional_atom_id is not None:
        row = registry.row_by_atom().get(conditional_atom_id)
        if row is None or not row["conditional_eligibility"]:
            raise ProtocolError("conditional target is not eligible")
        config[row["axis_name"]] = row["typed_value"]
        if config[row["axis_name"]] != row["typed_value"] or type(
            config[row["axis_name"]]
        ) is not type(row["typed_value"]):
            raise ProtocolError("conditional target fixed-value proof failed")
    return config


def generate_discovery_chunk(
    registry: AtomRegistry,
    *,
    stream_id: str,
    conditional_atom_id: str | None,
    chunk_index: int,
) -> list[dict[str, Any]]:
    draws = [
        sample_config(
            registry.axes,
            stream_id=stream_id,
            conditional_atom_id=conditional_atom_id,
            chunk_index=chunk_index,
            draw_index=draw_index,
            registry=registry,
        )
        for draw_index in range(CHUNK_SIZE)
    ]
    if len(draws) != CHUNK_SIZE:
        raise ProtocolError("discovery chunk cardinality drift")
    if conditional_atom_id:
        row = registry.row_by_atom()[conditional_atom_id]
        if any(
            row["axis_name"] not in draw
            or draw[row["axis_name"]] != row["typed_value"]
            or type(draw[row["axis_name"]]) is not type(row["typed_value"])
            for draw in draws
        ):
            raise ProtocolError("conditional chunk fixed-atom proof failed")
    return draws


def activate_conditional_targets(
    registry: AtomRegistry,
    global_classification: Mapping[str, SupportState | str],
) -> tuple[str, ...]:
    if set(global_classification) != {row["atom_id"] for row in registry.rows}:
        raise ProtocolError("global classification must cover every registry atom")
    candidates = [
        row
        for row in registry.rows
        if row["conditional_eligibility"]
        and SupportState(global_classification[row["atom_id"]])
        is SupportState.SUPPORT_UNOBSERVED
    ]
    candidates.sort(key=lambda row: tuple(row["deterministic_priority"]))
    return tuple(row["atom_id"] for row in candidates[:MAX_CONDITIONAL_TARGETS])


def classify_support(
    registry: AtomRegistry,
    witnessed_atoms: set[str] | frozenset[str],
    absence_proofs: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, SupportState]:
    proofs = absence_proofs or {}
    valid_kinds = {
        "finite_exhaustive",
        "sound_constraint",
        "independently_validated_complete_proof",
    }
    result: dict[str, SupportState] = {}
    for row in registry.rows:
        atom_id = row["atom_id"]
        if atom_id in witnessed_atoms:
            result[atom_id] = SupportState.SUPPORTED_WITNESSED
            continue
        proof = proofs.get(atom_id)
        if proof is not None:
            if (
                type(proof) is not dict
                or proof.get("proof_kind") not in valid_kinds
                or type(proof.get("proof_sha256")) is not str
                or len(proof["proof_sha256"]) != 64
                or proof.get("complete") is not True
                or proof.get("independently_validated") is not True
            ):
                raise ProtocolError("absence proof is incomplete or invalid")
            result[atom_id] = SupportState.SUPPORT_PROVEN_ABSENT
        else:
            result[atom_id] = SupportState.SUPPORT_UNOBSERVED
    unknown = set(witnessed_atoms) | set(proofs)
    unknown -= {row["atom_id"] for row in registry.rows}
    if unknown:
        raise ProtocolError("support evidence references unknown atoms")
    return result


def guidance_eligible_axes(
    registry: AtomRegistry, classification: Mapping[str, SupportState | str]
) -> frozenset[str]:
    eligible = set()
    for axis in registry.axes:
        rows = [row for row in registry.rows if row["axis_index"] == axis.axis_index]
        if all(
            SupportState(classification[row["atom_id"]])
            is SupportState.SUPPORTED_WITNESSED
            for row in rows
        ):
            eligible.add(axis.axis_name)
    return frozenset(eligible)


def validate_batch(
    configs: Sequence[Mapping[str, Any]],
    validator: Callable[[Mapping[str, Any]], Any],
) -> list[dict[str, Any]]:
    """Fail-closed adapter around a pinned-validity-equivalent callable."""

    records = []
    for index, config in enumerate(configs):
        record = {
            "draw_index": index,
            "config": dict(config),
            "config_hash": canonical_sha256(dict(config)),
            "_validate_solution": False,
            "resolver_none": False,
            "kernel_writer_error": None,
            "exception_taxonomy": None,
            "accepted": False,
        }
        try:
            result = validator(config)
            if result is None:
                record["resolver_none"] = True
            elif type(result) is bool:
                record["accepted"] = result
            elif isinstance(result, Mapping):
                record["accepted"] = result.get("accepted") is True
                record["resolver_none"] = result.get("resolver_none") is True
                record["kernel_writer_error"] = result.get("kernel_writer_error")
            else:
                raise ProtocolError("validator returned an unknown type")
        except Exception as error:  # validation exceptions are data, never acceptance
            record["exception_taxonomy"] = type(error).__name__
            record["accepted"] = False
        records.append(record)
    return records
