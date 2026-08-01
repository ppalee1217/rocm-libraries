# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Stable, side-effect-free public surface for the S10R3 protocol package."""

from .conformance import ConformanceError
from .contract import ContractError
from .correctness import CorrectnessError
from .ledger import LedgerError
from .mapping import MappingError
from .selector import BoundedCoverResult, GreedyStep, SelectionError, Witness
from .state_machine import Stage
from .support import (
    CHUNK_SIZE,
    CONDITIONAL_CHUNKS,
    GLOBAL_CHUNKS,
    MAX_CONDITIONAL_TARGETS,
    MAX_TOTAL_CHUNKS,
    MAX_TOTAL_DRAWS,
    AtomRegistry,
    AxisSpec,
    ProtocolError,
    SupportState,
)

__all__ = [
    "AtomRegistry",
    "AxisSpec",
    "BoundedCoverResult",
    "CHUNK_SIZE",
    "CONDITIONAL_CHUNKS",
    "ConformanceError",
    "ContractError",
    "CorrectnessError",
    "GLOBAL_CHUNKS",
    "GreedyStep",
    "LedgerError",
    "MAX_CONDITIONAL_TARGETS",
    "MAX_TOTAL_CHUNKS",
    "MAX_TOTAL_DRAWS",
    "MappingError",
    "ProtocolError",
    "SelectionError",
    "Stage",
    "SupportState",
    "Witness",
]
