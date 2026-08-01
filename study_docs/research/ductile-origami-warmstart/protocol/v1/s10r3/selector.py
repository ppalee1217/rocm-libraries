# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Deterministic greedy bounded-cover selector frozen for S10R3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .contract import canonical_sha256
from .support import AtomRegistry, SupportState


class SelectionError(ValueError):
    """A witness corpus cannot be selected under the frozen bounded-cover rule."""


@dataclass(frozen=True)
class Witness:
    config: Mapping[str, Any]
    config_hash: str
    atom_ids: frozenset[str]
    stream_rank: int
    conditional_priority_rank: int
    chunk_index: int
    draw_index: int

    def __post_init__(self) -> None:
        if self.config_hash != canonical_sha256(dict(self.config)):
            raise SelectionError("witness config hash mismatch")
        for value in (
            self.stream_rank,
            self.conditional_priority_rank,
            self.chunk_index,
            self.draw_index,
        ):
            if type(value) is not int or value < 0:
                raise SelectionError("first-occurrence fields must be non-negative integers")

    @property
    def occurrence_key(self) -> tuple[int, int, int, int, str]:
        return (
            self.stream_rank,
            self.conditional_priority_rank,
            self.chunk_index,
            self.draw_index,
            self.config_hash,
        )


@dataclass(frozen=True)
class GreedyStep:
    step_index: int
    config_hash: str
    gain: int
    newly_covered_atoms: tuple[str, ...]
    remaining_after: int


@dataclass(frozen=True)
class BoundedCoverResult:
    status: str
    failure_reason: str | None
    mandatory_atoms: tuple[str, ...]
    distinct_witness_count: int
    greedy_steps: tuple[GreedyStep, ...]
    c_greedy: int | None
    k: int | None
    final_config_hashes: tuple[str, ...]
    final_witnesses: tuple[Witness, ...]
    l_axis: int
    disclosure: str | None


def mandatory_mapping_atoms(
    registry: AtomRegistry,
    classification: Mapping[str, SupportState | str],
) -> frozenset[str]:
    expected = {row["atom_id"] for row in registry.rows}
    if set(classification) != expected:
        raise SelectionError("support classification must exactly cover the registry")
    return frozenset(
        atom_id
        for atom_id in registry.prelocked_atoms()
        if SupportState(classification[atom_id]) is SupportState.SUPPORTED_WITNESSED
    )


def canonicalize_distinct_witnesses(
    witnesses: Sequence[Witness],
) -> tuple[Witness, ...]:
    """Keep the first accepted occurrence per config hash and union its atom coverage."""

    ordered = sorted(witnesses, key=lambda item: item.occurrence_key)
    first: dict[str, Witness] = {}
    coverage: dict[str, set[str]] = {}
    raw_config: dict[str, bytes] = {}
    from .contract import canonical_json_bytes

    for witness in ordered:
        encoded = canonical_json_bytes(dict(witness.config))
        if witness.config_hash in raw_config and raw_config[witness.config_hash] != encoded:
            raise SelectionError("config hash collision with different canonical bytes")
        raw_config[witness.config_hash] = encoded
        first.setdefault(witness.config_hash, witness)
        coverage.setdefault(witness.config_hash, set()).update(witness.atom_ids)
    result = []
    for config_hash, witness in first.items():
        result.append(
            Witness(
                config=witness.config,
                config_hash=config_hash,
                atom_ids=frozenset(coverage[config_hash]),
                stream_rank=witness.stream_rank,
                conditional_priority_rank=witness.conditional_priority_rank,
                chunk_index=witness.chunk_index,
                draw_index=witness.draw_index,
            )
        )
    return tuple(sorted(result, key=lambda item: item.occurrence_key))


def _l_axis(
    registry: AtomRegistry, mandatory_atoms: frozenset[str]
) -> int:
    rows = registry.row_by_atom()
    per_axis: dict[int, int] = {}
    for atom_id in mandatory_atoms:
        axis_index = int(rows[atom_id]["axis_index"])
        per_axis[axis_index] = per_axis.get(axis_index, 0) + 1
    return max(per_axis.values(), default=0)


def deterministic_greedy_bounded_cover(
    registry: AtomRegistry,
    classification: Mapping[str, SupportState | str],
    witnesses: Sequence[Witness],
) -> BoundedCoverResult:
    mandatory = mandatory_mapping_atoms(registry, classification)
    distinct = canonicalize_distinct_witnesses(witnesses)
    l_axis = _l_axis(registry, mandatory)
    if len(distinct) < 10:
        return BoundedCoverResult(
            "inconclusive",
            "fresh_distinct_valid_witnesses_less_than_10",
            tuple(sorted(mandatory)),
            len(distinct),
            (),
            None,
            None,
            (),
            (),
            l_axis,
            None,
        )
    remaining = set(mandatory)
    selected: list[Witness] = []
    steps: list[GreedyStep] = []
    available = list(distinct)
    while remaining:
        ranked = sorted(
            available,
            key=lambda item: (
                -len(item.atom_ids & remaining),
                item.occurrence_key,
                item.config_hash,
            ),
        )
        if not ranked or not (ranked[0].atom_ids & remaining):
            return BoundedCoverResult(
                "inconclusive",
                "greedy_does_not_cover_all_mandatory_atoms",
                tuple(sorted(mandatory)),
                len(distinct),
                tuple(steps),
                None,
                None,
                (),
                (),
                l_axis,
                None,
            )
        chosen = ranked[0]
        newly = tuple(sorted(chosen.atom_ids & remaining))
        remaining.difference_update(newly)
        selected.append(chosen)
        available.remove(chosen)
        steps.append(
            GreedyStep(
                len(steps),
                chosen.config_hash,
                len(newly),
                newly,
                len(remaining),
            )
        )
    c_greedy = len(selected)
    if c_greedy > 20:
        disclosure = (
            "global_minimum_cover_feasibility_not_evaluated"
            if l_axis <= 20
            else None
        )
        return BoundedCoverResult(
            "inconclusive",
            "c_greedy_greater_than_20",
            tuple(sorted(mandatory)),
            len(distinct),
            tuple(steps),
            c_greedy,
            None,
            (),
            (),
            l_axis,
            disclosure,
        )
    k = max(10, c_greedy)
    selected_hashes = {item.config_hash for item in selected}
    if len(selected) < k:
        for witness in distinct:
            if witness.config_hash not in selected_hashes:
                selected.append(witness)
                selected_hashes.add(witness.config_hash)
                if len(selected) == k:
                    break
    if len(selected) != k or len(selected_hashes) != k:
        raise SelectionError("exact K padding invariant failed")
    final = tuple(sorted(selected, key=lambda item: item.config_hash))
    return BoundedCoverResult(
        "selected",
        None,
        tuple(sorted(mandatory)),
        len(distinct),
        tuple(steps),
        c_greedy,
        k,
        tuple(item.config_hash for item in final),
        final,
        l_axis,
        None,
    )
