# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Fail-closed S10R2 lifecycle transitions."""

from __future__ import annotations

from enum import Enum


class TransitionError(ValueError):
    """Raised when an S10R2 lifecycle transition is not preregistered."""


class Stage(str, Enum):
    PRELOCK = "PRELOCK"
    CAPS_CONFIRMED = "CAPS_CONFIRMED"
    PARITY_CONFIRMED = "PARITY_CONFIRMED"
    AUDIT_PASS = "AUDIT_PASS"
    LOCK_SEALED = "LOCK_SEALED"
    PRE_DRAW_REGISTRY_FROZEN = "PRE_DRAW_REGISTRY_FROZEN"
    GLOBAL_DISCOVERY = "GLOBAL_DISCOVERY"
    CONDITIONAL_ACTIVATION = "CONDITIONAL_ACTIVATION"
    CONDITIONAL_DISCOVERY = "CONDITIONAL_DISCOVERY"
    SUPPORT_CLASSIFICATION_SEALED = "SUPPORT_CLASSIFICATION_SEALED"
    EXACT_TEN_SELECTED = "EXACT_TEN_SELECTED"
    MAPPING_AB = "MAPPING_AB"
    NATIVE_CONFORMANCE = "NATIVE_CONFORMANCE"
    GPU_ENVIRONMENT = "GPU_ENVIRONMENT"
    CORRECTNESS_ANCHORS = "CORRECTNESS_ANCHORS"
    NOISE_CELLS = "NOISE_CELLS"
    DECISION_READY = "DECISION_READY"
    TERMINAL_POSITIVE = "TERMINAL_POSITIVE"
    TERMINAL_NEGATIVE = "TERMINAL_NEGATIVE"
    TERMINAL_INCONCLUSIVE = "TERMINAL_INCONCLUSIVE"
    CHANGES_REQUIRED = "CHANGES_REQUIRED"
    BLOCKED = "BLOCKED"


_TRANSITIONS: dict[Stage, frozenset[Stage]] = {
    Stage.PRELOCK: frozenset({Stage.CAPS_CONFIRMED, Stage.BLOCKED}),
    Stage.CAPS_CONFIRMED: frozenset({Stage.PARITY_CONFIRMED, Stage.BLOCKED}),
    Stage.PARITY_CONFIRMED: frozenset({Stage.AUDIT_PASS, Stage.BLOCKED}),
    Stage.AUDIT_PASS: frozenset({Stage.LOCK_SEALED, Stage.BLOCKED}),
    Stage.LOCK_SEALED: frozenset(
        {Stage.PRE_DRAW_REGISTRY_FROZEN, Stage.CHANGES_REQUIRED, Stage.BLOCKED}
    ),
    Stage.PRE_DRAW_REGISTRY_FROZEN: frozenset(
        {Stage.GLOBAL_DISCOVERY, Stage.CHANGES_REQUIRED, Stage.BLOCKED}
    ),
    Stage.GLOBAL_DISCOVERY: frozenset(
        {
            Stage.GLOBAL_DISCOVERY,
            Stage.CONDITIONAL_ACTIVATION,
            Stage.CHANGES_REQUIRED,
            Stage.BLOCKED,
        }
    ),
    Stage.CONDITIONAL_ACTIVATION: frozenset(
        {
            Stage.CONDITIONAL_DISCOVERY,
            Stage.SUPPORT_CLASSIFICATION_SEALED,
            Stage.CHANGES_REQUIRED,
            Stage.BLOCKED,
        }
    ),
    Stage.CONDITIONAL_DISCOVERY: frozenset(
        {
            Stage.CONDITIONAL_DISCOVERY,
            Stage.SUPPORT_CLASSIFICATION_SEALED,
            Stage.CHANGES_REQUIRED,
            Stage.BLOCKED,
        }
    ),
    Stage.SUPPORT_CLASSIFICATION_SEALED: frozenset(
        {
            Stage.EXACT_TEN_SELECTED,
            Stage.TERMINAL_INCONCLUSIVE,
            Stage.CHANGES_REQUIRED,
            Stage.BLOCKED,
        }
    ),
    Stage.EXACT_TEN_SELECTED: frozenset(
        {Stage.MAPPING_AB, Stage.TERMINAL_INCONCLUSIVE, Stage.CHANGES_REQUIRED, Stage.BLOCKED}
    ),
    Stage.MAPPING_AB: frozenset(
        {
            Stage.NATIVE_CONFORMANCE,
            Stage.TERMINAL_NEGATIVE,
            Stage.CHANGES_REQUIRED,
            Stage.BLOCKED,
        }
    ),
    Stage.NATIVE_CONFORMANCE: frozenset(
        {Stage.GPU_ENVIRONMENT, Stage.CHANGES_REQUIRED, Stage.BLOCKED}
    ),
    Stage.GPU_ENVIRONMENT: frozenset(
        {Stage.CORRECTNESS_ANCHORS, Stage.CHANGES_REQUIRED, Stage.BLOCKED}
    ),
    Stage.CORRECTNESS_ANCHORS: frozenset(
        {
            Stage.CORRECTNESS_ANCHORS,
            Stage.NOISE_CELLS,
            Stage.TERMINAL_NEGATIVE,
            Stage.CHANGES_REQUIRED,
            Stage.BLOCKED,
        }
    ),
    Stage.NOISE_CELLS: frozenset(
        {
            Stage.NOISE_CELLS,
            Stage.DECISION_READY,
            Stage.TERMINAL_INCONCLUSIVE,
            Stage.CHANGES_REQUIRED,
            Stage.BLOCKED,
        }
    ),
    Stage.DECISION_READY: frozenset(
        {
            Stage.TERMINAL_POSITIVE,
            Stage.TERMINAL_NEGATIVE,
            Stage.TERMINAL_INCONCLUSIVE,
            Stage.CHANGES_REQUIRED,
            Stage.BLOCKED,
        }
    ),
    Stage.CHANGES_REQUIRED: frozenset(),
    Stage.BLOCKED: frozenset(),
    Stage.TERMINAL_POSITIVE: frozenset(),
    Stage.TERMINAL_NEGATIVE: frozenset(),
    Stage.TERMINAL_INCONCLUSIVE: frozenset(),
}


def assert_transition(current: Stage | str, following: Stage | str) -> Stage:
    """Return the normalized next stage or fail closed."""

    try:
        current_stage = Stage(current)
        following_stage = Stage(following)
    except ValueError as error:
        raise TransitionError(f"unknown S10R2 stage: {error}") from error
    if following_stage not in _TRANSITIONS[current_stage]:
        raise TransitionError(
            f"illegal S10R2 transition {current_stage.value} -> {following_stage.value}"
        )
    return following_stage


def transition_path_is_valid(stages: list[Stage | str]) -> bool:
    """Validate a complete non-empty path."""

    if not stages:
        raise TransitionError("transition path must not be empty")
    normalized = [Stage(stage) for stage in stages]
    for current, following in zip(normalized, normalized[1:]):
        assert_transition(current, following)
    return True
