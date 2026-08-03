#!/usr/bin/env python3
# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Fail-closed command line entry point for S11 factorization."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

PROTOCOL_ROOT = Path(__file__).resolve().parent
if str(PROTOCOL_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOCOL_ROOT))

from s11.canonical import canonical_json_bytes, sha256_file, strict_load_json
from s11.contract import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_LOCK_PATH,
    DEFAULT_PREIMPLEMENTATION_LOCK_PATH,
    DEFAULT_REVISION_PATH,
    DEFAULT_SCHEMA_PATH,
    REPOSITORY_ROOT,
    admit_formal_command,
    create_effective_lock,
    preflight,
    validate_contract,
    verify_effective_lock,
)
from s11.decision import decide
from s11.ledger import ChunkLedger
from s11.sampling import (
    StreamSpec, canonical_prefix, commit_chunk, expand_compact_chunk, sample_chunk,
)
from s11.workflow import execute_formal_stage, verify_closeout


FORMAL_COMMANDS = (
    "global-discovery",
    "conditional-discovery",
    "qualify",
    "score",
    "analyze",
    "decide",
    "reproduce",
)


def _emit(value: Any) -> None:
    sys.stdout.buffer.write(canonical_json_bytes(value) + b"\n")


def _synthetic_self_test() -> dict[str, Any]:
    candidate_ids = ["a" * 64, "b" * 64]
    registry = {
        "eligible_genes": [
            {
                "gene": "SyntheticGene",
                "candidate_ids": candidate_ids,
                "candidates": [
                    {"type": "int", "value": "0"},
                    {"type": "int", "value": "1"},
                ],
                "baseline_probabilities": [0.5, 0.5],
            }
        ]
    }
    spec = StreamSpec("global", target_accepted=4, hard_cap_chunks=2, nominal_slots_per_chunk=8)
    chunk = sample_chunk(
        registry, spec, master_nonce="1" * 64, chunk_index=0,
        validator=lambda _: True, lock_sha256="2" * 64,
    )
    repeated = sample_chunk(
        registry, spec, master_nonce="1" * 64, chunk_index=0,
        validator=lambda _: True, lock_sha256="2" * 64,
    )
    prefix = canonical_prefix(
        [chunk], 4, registry=registry, spec=spec, master_nonce="1" * 64,
        expected_lock_sha256="2" * 64,
    )
    decision = decide(
        {
            "integrity_failure": False,
            "label_leakage": False,
            "qualification_discordant_or_partial": False,
            "blocked_mapping_exact_allowlisted": False,
            "bounded_family_complete": False,
            "material_stochastic_shortage": True,
            "global_uexec_count": 0,
            "stable_guided_gene_count": 0,
            "positive_global_lambda": False,
            "all_positive_gates_pass": False,
        }
    )
    with tempfile.TemporaryDirectory(prefix="s11-synthetic-") as directory:
        chunk_path = Path(directory) / "chunk.json"
        commit_chunk(chunk_path, chunk)
        expanded = expand_compact_chunk(
            chunk, registry=registry, spec=spec, master_nonce="1" * 64,
            expected_lock_sha256="2" * 64,
        )
        with ChunkLedger(Path(directory) / "ledger", "2" * 64) as ledger:
            ledger.append_chunk(
                stage="global_discovery",
                stream_id="global",
                chunk_index=0,
                nominal_slots=8,
                accepted_count=8,
                disposition_counts=expanded["counts"],
                chunk_relative_path="chunk.json",
                chunk_byte_length=chunk_path.stat().st_size,
                chunk_file_sha256=sha256_file(chunk_path),
                chunk_semantic_sha256=chunk["chunk_semantic_sha256"],
            )
            replay = ledger.full_verify()
    return {
        "checkpoint_id": "S11",
        "mode": "synthetic_only",
        "deterministic_chunk": chunk == repeated,
        "canonical_prefix_count": prefix["accepted_credited"],
        "ledger_event_count": replay["event_count"],
        "terminal_fixture": decision["terminal_code"],
        "pass": chunk == repeated and prefix["accepted_credited"] == 4 and replay["event_count"] == 1,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_PATH)
    parser.add_argument("--revision", type=Path, default=DEFAULT_REVISION_PATH)
    parser.add_argument("--preimplementation-lock", type=Path, default=DEFAULT_PREIMPLEMENTATION_LOCK_PATH)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-contract")
    subparsers.add_parser("preflight")
    subparsers.add_parser("self-test")
    create = subparsers.add_parser("create-lock")
    create.add_argument("--output", type=Path, default=DEFAULT_LOCK_PATH)
    create.add_argument("--implementation-manifest", type=Path, required=True)
    verify = subparsers.add_parser("verify-lock")
    verify.add_argument("--lock", type=Path, default=DEFAULT_LOCK_PATH)
    status = subparsers.add_parser("status")
    status.add_argument("--lock", type=Path, default=DEFAULT_LOCK_PATH)
    closeout = subparsers.add_parser("verify-closeout")
    closeout.add_argument("--commit", required=True)
    closeout.add_argument("--output", type=Path, required=True)
    for command in FORMAL_COMMANDS:
        formal = subparsers.add_parser(command)
        formal.add_argument("--lock", type=Path, default=DEFAULT_LOCK_PATH)
        formal.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    validation_kwargs = {
        "revision_path": arguments.revision,
        "preimplementation_lock_path": arguments.preimplementation_lock,
    }
    if arguments.command == "validate-contract":
        contract = validate_contract(arguments.contract, arguments.schema, **validation_kwargs)
        _emit({"checkpoint_id": "S11", "status": contract["status"], "valid": True})
    elif arguments.command == "preflight":
        _emit(preflight(arguments.contract, arguments.schema, **validation_kwargs))
    elif arguments.command == "self-test":
        _emit(_synthetic_self_test())
    elif arguments.command == "create-lock":
        _emit(
            create_effective_lock(
                arguments.output,
                contract_path=arguments.contract,
                schema_path=arguments.schema,
                implementation_manifest_path=arguments.implementation_manifest,
            )
        )
    elif arguments.command == "verify-lock":
        _emit(
            verify_effective_lock(
                arguments.lock,
                contract_path=arguments.contract,
                schema_path=arguments.schema,
            )
        )
    elif arguments.command == "status":
        contract = validate_contract(arguments.contract, arguments.schema, **validation_kwargs)
        if not arguments.lock.exists():
            _emit({"checkpoint_id": "S11", **contract["initial_state"], "edge": None})
        else:
            lock = verify_effective_lock(
                arguments.lock,
                contract_path=arguments.contract,
                schema_path=arguments.schema,
            )
            _emit({"checkpoint_id": "S11", "lock": lock["state"], "scientific_outcome": "not_evaluated", "edge": None})
    elif arguments.command == "verify-closeout":
        contract = validate_contract(arguments.contract, arguments.schema, **validation_kwargs)
        _emit(
            verify_closeout(
                arguments.commit, output=arguments.output,
                repository_root=REPOSITORY_ROOT, contract=contract,
            )
        )
    else:
        contract, lock = admit_formal_command(
            arguments.command,
            contract_path=arguments.contract,
            schema_path=arguments.schema,
            lock_path=arguments.lock,
        )
        _emit(
            execute_formal_stage(
                arguments.command,
                contract=contract,
                lock=lock,
                output=arguments.output,
                repository_root=REPOSITORY_ROOT,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
