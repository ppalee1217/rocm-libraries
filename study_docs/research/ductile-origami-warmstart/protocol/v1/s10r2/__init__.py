# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""S10R2 support-aware Stage-1 entry protocol.

This package is deliberately independent of every S10R1 implementation and
artifact.  Public helpers are pure or fail closed until a sealed S10R2 lock is
present.
"""

from .calibration import Allocation, CalibrationError, ResourceCaps, derive_caps
from .contract import ContractError, load_contract, verify_lock_seal
from .mapping import MappingError, exact_ten_greedy_cover, mandatory_atoms
from .state_machine import Stage, TransitionError, assert_transition
from .support import (
    CHUNK_SIZE,
    GLOBAL_CHUNKS,
    MAX_CONDITIONAL_TARGETS,
    MAX_TOTAL_CHUNKS,
    AtomRegistry,
    SupportState,
)

__all__ = [
    "Allocation",
    "AtomRegistry",
    "CHUNK_SIZE",
    "CalibrationError",
    "ContractError",
    "GLOBAL_CHUNKS",
    "MAX_CONDITIONAL_TARGETS",
    "MAX_TOTAL_CHUNKS",
    "MappingError",
    "ResourceCaps",
    "Stage",
    "SupportState",
    "TransitionError",
    "assert_transition",
    "derive_caps",
    "exact_ten_greedy_cover",
    "load_contract",
    "mandatory_atoms",
    "verify_lock_seal",
]
