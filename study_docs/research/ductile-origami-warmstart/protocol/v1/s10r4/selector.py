# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Deterministic bounded operational set-cover selection for S10R4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .contract import S10R4Error


@dataclass(frozen=True)
class Witness:
    config_hash: str
    atoms: frozenset[str]
    first_occurrence: tuple[int, int, int, int, str]


@dataclass(frozen=True)
class GreedyStep:
    ordinal: int
    config_hash: str
    gained_atoms: tuple[str, ...]
    remaining_atoms: tuple[str, ...]


@dataclass(frozen=True)
class SelectionResult:
    mandatory_atoms: tuple[str, ...]
    operational_atoms: tuple[str, ...]
    survivor_hashes: tuple[str, ...]
    greedy_steps: tuple[GreedyStep, ...]
    c_greedy: int
    k: int
    selected_hashes: tuple[str, ...]


def witness_from_frame_row(row: Mapping[str, Any]) -> Witness:
    config_hash = row.get("config_hash")
    atoms = row.get("candidate_atom_ids_in_config")
    if not isinstance(config_hash, str) or not isinstance(atoms, list) or not all(isinstance(v, str) for v in atoms):
        raise S10R4Error("malformed survivor frame row")
    return Witness(
        config_hash=config_hash,
        atoms=frozenset(atoms),
        first_occurrence=(
            int(row["stream_rank"]),
            int(row["conditional_priority_rank"]),
            int(row["chunk_index"]),
            int(row["draw_index"]),
            config_hash,
        ),
    )


def deterministic_select(
    witnesses: Sequence[Witness],
    prelocked_candidate_atoms: Iterable[str],
    *,
    minimum_k: int = 10,
    maximum_k: int = 20,
) -> SelectionResult:
    if minimum_k != 10 or maximum_k != 20:
        raise S10R4Error("S10R4 selector bounds are frozen at 10 and 20")
    if len({item.config_hash for item in witnesses}) != len(witnesses):
        raise S10R4Error("duplicate survivor config hash")
    if len(witnesses) < minimum_k:
        raise S10R4Error("FT-BLOCKED-MAPPING: fewer than ten stable survivors")
    operational = frozenset(atom for item in witnesses for atom in item.atoms)
    mandatory = frozenset(prelocked_candidate_atoms) & operational
    remaining = set(mandatory)
    chosen: list[Witness] = []
    steps: list[GreedyStep] = []
    available = list(witnesses)
    while remaining:
        ranked = sorted(
            available,
            key=lambda item: (
                -len(item.atoms & remaining),
                item.first_occurrence,
                item.config_hash,
            ),
        )
        if not ranked or len(ranked[0].atoms & remaining) == 0:
            raise S10R4Error("FT-BLOCKED-MAPPING: mandatory operational atoms are not coverable")
        selected = ranked[0]
        gained = tuple(sorted(selected.atoms & remaining))
        remaining -= selected.atoms
        chosen.append(selected)
        available.remove(selected)
        steps.append(
            GreedyStep(
                ordinal=len(steps),
                config_hash=selected.config_hash,
                gained_atoms=gained,
                remaining_atoms=tuple(sorted(remaining)),
            )
        )
    c_greedy = len(chosen)
    if c_greedy > maximum_k:
        raise S10R4Error("FT-BLOCKED-MAPPING: greedy cover exceeds K_max=20")
    k = max(minimum_k, c_greedy)
    if len(chosen) < k:
        for item in sorted(available, key=lambda witness: (witness.first_occurrence, witness.config_hash)):
            chosen.append(item)
            if len(chosen) == k:
                break
    if len(chosen) != k:
        raise S10R4Error("FT-BLOCKED-MAPPING: insufficient survivors for deterministic padding")
    selected_hashes = tuple(sorted(item.config_hash for item in chosen))
    return SelectionResult(
        mandatory_atoms=tuple(sorted(mandatory)),
        operational_atoms=tuple(sorted(operational)),
        survivor_hashes=tuple(sorted(item.config_hash for item in witnesses)),
        greedy_steps=tuple(steps),
        c_greedy=c_greedy,
        k=k,
        selected_hashes=selected_hashes,
    )


def selection_to_document(result: SelectionResult) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        "document_kind": "operational_selection",
        "selector_id": "deterministic_greedy_set_cover_v2_bounded_k20",
        "mandatory_atoms": list(result.mandatory_atoms),
        "operational_atoms": list(result.operational_atoms),
        "survivor_hashes": list(result.survivor_hashes),
        "greedy_steps": [
            {
                "ordinal": step.ordinal,
                "config_hash": step.config_hash,
                "gained_atoms": list(step.gained_atoms),
                "remaining_atoms": list(step.remaining_atoms),
            }
            for step in result.greedy_steps
        ],
        "c_greedy": result.c_greedy,
        "k": result.k,
        "selected_hashes": list(result.selected_hashes),
    }

