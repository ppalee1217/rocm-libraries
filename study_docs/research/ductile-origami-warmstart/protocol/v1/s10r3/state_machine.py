# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Fail-closed S10R3 stage machine with explicit scientific terminal branches."""

from __future__ import annotations

from enum import Enum


class TransitionError(ValueError):
    """A requested S10R3 lifecycle transition is not frozen."""


class Stage(str, Enum):
    PREIMPLEMENTATION = "PREIMPLEMENTATION"
    IMPLEMENTATION_READY = "IMPLEMENTATION_READY"
    LOCKED_READY = "LOCKED_READY"
    GLOBAL_DISCOVERY = "GLOBAL_DISCOVERY"
    CONDITIONAL_ACTIVATION = "CONDITIONAL_ACTIVATION"
    CONDITIONAL_DISCOVERY = "CONDITIONAL_DISCOVERY"
    SUPPORT_CLASSIFICATION_SEALED = "SUPPORT_CLASSIFICATION_SEALED"
    BOUNDED_K_SELECTED = "BOUNDED_K_SELECTED"
    MAPPING_A = "MAPPING_A"
    MAPPING_B = "MAPPING_B"
    NATIVE_CONFORMANCE = "NATIVE_CONFORMANCE"
    GPU_ENVIRONMENT = "GPU_ENVIRONMENT"
    CORRECTNESS = "CORRECTNESS"
    NOISE = "NOISE"
    DECISION_READY = "DECISION_READY"
    TERMINAL_POSITIVE = "TERMINAL_POSITIVE"
    TERMINAL_NEGATIVE = "TERMINAL_NEGATIVE"
    TERMINAL_NEGATIVE_MAPPING = "TERMINAL_NEGATIVE_MAPPING"
    TERMINAL_NEGATIVE_CORRECTNESS = "TERMINAL_NEGATIVE_CORRECTNESS"
    TERMINAL_INCONCLUSIVE = "TERMINAL_INCONCLUSIVE"
    VERIFIED_PENDING_CLOSEOUT = "VERIFIED_PENDING_CLOSEOUT"
    CHANGES_REQUIRED = "CHANGES_REQUIRED"
    BLOCKED = "BLOCKED"


_TRANSITIONS: dict[Stage, frozenset[Stage]] = {
    Stage.PREIMPLEMENTATION: frozenset({Stage.IMPLEMENTATION_READY}),
    Stage.IMPLEMENTATION_READY: frozenset({Stage.LOCKED_READY}),
    Stage.LOCKED_READY: frozenset({Stage.GLOBAL_DISCOVERY}),
    Stage.GLOBAL_DISCOVERY: frozenset({Stage.GLOBAL_DISCOVERY, Stage.CONDITIONAL_ACTIVATION}),
    Stage.CONDITIONAL_ACTIVATION: frozenset(
        {Stage.CONDITIONAL_DISCOVERY, Stage.SUPPORT_CLASSIFICATION_SEALED}
    ),
    Stage.CONDITIONAL_DISCOVERY: frozenset(
        {Stage.CONDITIONAL_DISCOVERY, Stage.SUPPORT_CLASSIFICATION_SEALED}
    ),
    Stage.SUPPORT_CLASSIFICATION_SEALED: frozenset(
        {Stage.BOUNDED_K_SELECTED, Stage.TERMINAL_INCONCLUSIVE}
    ),
    Stage.BOUNDED_K_SELECTED: frozenset({Stage.MAPPING_A}),
    Stage.MAPPING_A: frozenset(
        {Stage.MAPPING_A, Stage.MAPPING_B, Stage.TERMINAL_NEGATIVE_MAPPING}
    ),
    Stage.MAPPING_B: frozenset(
        {Stage.MAPPING_B, Stage.NATIVE_CONFORMANCE, Stage.TERMINAL_NEGATIVE_MAPPING}
    ),
    Stage.NATIVE_CONFORMANCE: frozenset({Stage.GPU_ENVIRONMENT}),
    Stage.GPU_ENVIRONMENT: frozenset({Stage.CORRECTNESS}),
    Stage.CORRECTNESS: frozenset(
        {Stage.CORRECTNESS, Stage.NOISE, Stage.TERMINAL_NEGATIVE_CORRECTNESS}
    ),
    Stage.NOISE: frozenset({Stage.NOISE, Stage.DECISION_READY, Stage.TERMINAL_INCONCLUSIVE}),
    Stage.DECISION_READY: frozenset(
        {
            Stage.TERMINAL_POSITIVE,
            Stage.TERMINAL_NEGATIVE,
            Stage.TERMINAL_INCONCLUSIVE,
        }
    ),
    Stage.TERMINAL_POSITIVE: frozenset({Stage.VERIFIED_PENDING_CLOSEOUT}),
    Stage.TERMINAL_NEGATIVE: frozenset({Stage.VERIFIED_PENDING_CLOSEOUT}),
    Stage.TERMINAL_NEGATIVE_MAPPING: frozenset({Stage.VERIFIED_PENDING_CLOSEOUT}),
    Stage.TERMINAL_NEGATIVE_CORRECTNESS: frozenset({Stage.VERIFIED_PENDING_CLOSEOUT}),
    Stage.TERMINAL_INCONCLUSIVE: frozenset({Stage.VERIFIED_PENDING_CLOSEOUT}),
    Stage.VERIFIED_PENDING_CLOSEOUT: frozenset(),
    Stage.CHANGES_REQUIRED: frozenset(),
    Stage.BLOCKED: frozenset(),
}

_SIDE_EXITS = frozenset({Stage.CHANGES_REQUIRED, Stage.BLOCKED})
_TERMINAL = frozenset(
    {
        Stage.TERMINAL_POSITIVE,
        Stage.TERMINAL_NEGATIVE,
        Stage.TERMINAL_NEGATIVE_MAPPING,
        Stage.TERMINAL_NEGATIVE_CORRECTNESS,
        Stage.TERMINAL_INCONCLUSIVE,
    }
)


def assert_transition(current: Stage | str, following: Stage | str) -> Stage:
    current_stage = Stage(current)
    following_stage = Stage(following)
    if current_stage not in _TERMINAL and following_stage in _SIDE_EXITS:
        return following_stage
    if following_stage not in _TRANSITIONS[current_stage]:
        raise TransitionError(
            f"forbidden S10R3 transition: {current_stage.value} -> {following_stage.value}"
        )
    return following_stage


def transition_path_is_valid(stages: list[Stage | str]) -> bool:
    try:
        for current, following in zip(stages, stages[1:]):
            assert_transition(current, following)
    except (ValueError, TransitionError):
        return False
    return True


def require_complete_unit(
    *,
    complete: bool,
    failure_kind: str,
    current: Stage | str,
) -> Stage:
    """Scientific terminalization requires a complete, reproducible unit."""

    current_stage = Stage(current)
    if not complete:
        raise TransitionError("partial mapping/correctness panel cannot terminalize")
    if failure_kind == "mapping" and current_stage in {Stage.MAPPING_A, Stage.MAPPING_B}:
        return Stage.TERMINAL_NEGATIVE_MAPPING
    if failure_kind == "correctness" and current_stage is Stage.CORRECTNESS:
        return Stage.TERMINAL_NEGATIVE_CORRECTNESS
    raise TransitionError("failure kind/current stage does not define a terminal branch")
