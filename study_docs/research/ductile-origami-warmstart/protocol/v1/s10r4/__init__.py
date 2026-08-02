# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Stable public API for the S10R4 exact-frame operational-entry protocol."""

from .conformance import build_native_fixture, validate_native_fixture
from .contract import PROTOCOL_ID, S10R4Error, canonical_json, load_contract
from .correctness import aggregate_noise, anchor_indices
from .frame import replay_exact_frame, validate_exact_frame_registry
from .mapping import build_size_registry, validate_size_registry
from .selector import SelectionResult, Witness, deterministic_select
from .state_machine import Lifecycle, decide_outcome

__all__ = [
    "PROTOCOL_ID",
    "S10R4Error",
    "Lifecycle",
    "SelectionResult",
    "Witness",
    "aggregate_noise",
    "anchor_indices",
    "build_native_fixture",
    "build_size_registry",
    "canonical_json",
    "decide_outcome",
    "deterministic_select",
    "load_contract",
    "replay_exact_frame",
    "validate_exact_frame_registry",
    "validate_native_fixture",
    "validate_size_registry",
]
