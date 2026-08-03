# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Pre-evidence S11 factorization machinery.

The package is deliberately import-safe: importing it never reads an outcome
artifact, starts a subprocess, or creates a run directory.  Formal commands
are admitted only by :mod:`s11.contract` after an effective lock exists.
"""

from .canonical import canonical_json_bytes, canonical_sha256, typed_value
from .contract import ContractError, load_contract, validate_contract

__all__ = [
    "ContractError",
    "canonical_json_bytes",
    "canonical_sha256",
    "load_contract",
    "typed_value",
    "validate_contract",
]
