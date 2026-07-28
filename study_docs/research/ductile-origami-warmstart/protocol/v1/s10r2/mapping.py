# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Performance-blind S10R2 exact-ten selection and mapping parity."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from Tensile.ductile.evidence import canonical_json_bytes, canonical_sha256


class MappingError(ValueError):
    """Exact-ten construction or mapping parity failure."""


MAPPING_RESULT_MARKER = "S10R2_MAPPING_RESULT="


def mapping_worker_code() -> str:
    """Pinned subprocess source for calibration and fresh A/B mapping passes."""

    return r'''
import hashlib
import json
import math
import sys

from Tensile import LibraryIO
from Tensile.BenchmarkStructs import BenchmarkProcess
from Tensile.Common.Architectures import gfxToIsa
from Tensile.Common.Capabilities import makeIsaInfoMap
from Tensile.Common.GlobalParameters import assignGlobalParameters
from Tensile.Common.Types import makeDebugConfig
from Tensile.KernelWriterAssembly import KernelWriterAssembly
from Tensile.Toolchain.Component import Assembler
from Tensile.SolutionLibrary import MasterSolutionLibrary
from Tensile.TensileCreateLibrary.Run import (
    passPostKernelInfoToLibrary,
    passPostKernelInfoToSolution,
    processKernelSource,
)
from Tensile.SolutionStructs.Naming import getKernelFileBase, getKernelNameMin
from Tensile.backends.ductile_backend import _generate_single_solution_with_groups
from rocisa import rocIsa

MARKER = "S10R2_MAPPING_RESULT="

def plain(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("non-finite mapping value")
        return value
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if hasattr(value, "state"):
        return plain(value.state)
    raise TypeError("unsupported mapping value: " + type(value).__name__)

def rejected(candidate, size, reason):
    return {
        "config_hash": candidate["config_hash"],
        "size_id": size["size_id"],
        "size": size["values"],
        "mapping_status": "rejected",
        "raw_indices": candidate["candidate_indices"],
        "raw_values": candidate["config"],
        "mapped_payload": None,
        "guessed_required_fields": [],
        "unresolved_required_fields": ["resolved_solution"],
        "rejection": reason,
    }

def accepted(candidate, size, solution, library_solution, results, kernels, split_gsu):
    state = solution._state
    mapping_source = library_solution.sizeMapping
    required = [
        "waveNum", "macroTile", "matrixInstruction", "grvwA", "grvwB",
        "gwvwC", "gwvwD", "depthU", "globalSplitU", "workGroupMapping",
        "globalAccumulation", "workGroupMappingXCC", "workGroupMappingXCCGroup",
        "globalSplitUCoalesced", "globalSplitUWorkGroupMappingRoundRobin",
        "CUOccupancy", "PrefetchGlobalRead", "MathClocksUnrolledLoop",
        "DirectToVgprA", "DirectToVgprB", "NumLoadsCoalescedA",
        "NumLoadsCoalescedB", "VectorWidthA", "VectorWidthB", "LocalSplitU",
        "DirectToLdsA", "DirectToLdsB", "WaveGroup",
    ]
    missing = [field for field in required if not hasattr(mapping_source, field)]
    if missing:
        raise KeyError("missing SizeMapping fields: " + ",".join(missing))
    matrix_instruction = list(mapping_source.matrixInstruction)
    macro_tile = list(mapping_source.macroTile)
    wave_group = list(mapping_source.WaveGroup)
    if len(matrix_instruction) != 4 or len(macro_tile) != 3 or len(wave_group) != 2:
        raise ValueError("invalid fixed-width SizeMapping field")
    gsu = int(mapping_source.globalSplitU)
    if gsu < 1:
        raise ValueError("unresolved/auto GlobalSplitU is forbidden")
    size_mapping = {
        "waveNum": int(mapping_source.waveNum),
        "macroTile": [int(value) for value in macro_tile],
        "matrixInstruction": [int(value) for value in matrix_instruction],
        "grvwA": int(mapping_source.grvwA),
        "grvwB": int(mapping_source.grvwB),
        "gwvwC": int(mapping_source.gwvwC),
        "gwvwD": int(mapping_source.gwvwD),
        "depthU": int(mapping_source.depthU),
        "globalSplitU": gsu,
        "workGroupMapping": int(mapping_source.workGroupMapping),
        "globalAccumulation": int(mapping_source.globalAccumulation),
        "workGroupMappingXCC": int(mapping_source.workGroupMappingXCC),
        "workGroupMappingXCCGroup": int(mapping_source.workGroupMappingXCCGroup),
        "globalSplitUCoalesced": bool(mapping_source.globalSplitUCoalesced),
        "globalSplitUWorkGroupMappingRoundRobin": bool(
            mapping_source.globalSplitUWorkGroupMappingRoundRobin
        ),
        "CUOccupancy": int(mapping_source.CUOccupancy),
        "PrefetchGlobalRead": int(mapping_source.PrefetchGlobalRead),
        "MathClocksUnrolledLoop": int(mapping_source.MathClocksUnrolledLoop),
        "DirectToVgprA": bool(mapping_source.DirectToVgprA),
        "DirectToVgprB": bool(mapping_source.DirectToVgprB),
        "NumLoadsCoalescedA": int(mapping_source.NumLoadsCoalescedA),
        "NumLoadsCoalescedB": int(mapping_source.NumLoadsCoalescedB),
        "VectorWidthA": int(mapping_source.VectorWidthA),
        "VectorWidthB": int(mapping_source.VectorWidthB),
        "LocalSplitU": int(mapping_source.LocalSplitU),
        "DirectToLdsA": bool(mapping_source.DirectToLdsA),
        "DirectToLdsB": bool(mapping_source.DirectToLdsB),
        "waveGroup": [int(value) for value in wave_group],
    }
    resolved_sentinels = {}
    for field, value in candidate["config"].items():
        if type(value) is int and value in (-2, -1):
            resolved_sentinels[field] = {
                "raw": value,
                "resolved": plain(state.get(field)),
            }
    problem = {
        "M": int(size["values"][0]),
        "N": int(size["values"][1]),
        "NumBatches": int(size["values"][2]),
        "K": int(size["values"][3]),
        "bpeA": 2,
        "bpeB": 2,
        "bpeD": 2,
        "bpeCompute": 4,
        "transA": False,
        "transB": False,
        "swizzleTensorA": False,
        "swizzleTensorB": False,
        "dataType": "BFloat16",
    }
    payload = {
        "resolved_solution": plain(state),
        "codegen_identity": {
            "kernel_names": [getKernelNameMin(kernel, split_gsu) for kernel in kernels],
            "source_sha256": [
                hashlib.sha256(
                    result.src
                    if isinstance(result.src, bytes)
                    else result.src.encode("utf-8")
                ).hexdigest()
                for result in results
            ],
            "result_count": len(results),
            "isa": [9, 4, 2],
        },
        "size_mapping": size_mapping,
        "effective_gsu": gsu,
        "resolved_sentinels": resolved_sentinels,
        "formocast_input": {
            "problem": problem,
            "size_mapping": size_mapping,
            "hardware": "gfx942",
        },
        "field_provenance": {
            "resolved_solution": "pinned _generate_single_solution_with_groups",
            "size_mapping": "pinned MasterSolutionLibrary.BenchmarkingLibrary",
            "CUOccupancy": "pinned passPostKernelInfoToLibrary",
            "PrefetchGlobalRead": "pinned passPostKernelInfoToSolution",
            "MathClocksUnrolledLoop": "pinned passPostKernelInfoToSolution",
            "effective_gsu": "pinned explicit GlobalSplitU mapping",
            "formocast_input": "pinned SolutionIterator.cpp field map",
        },
    }
    return {
        "config_hash": candidate["config_hash"],
        "size_id": size["size_id"],
        "size": size["values"],
        "mapping_status": "accepted",
        "raw_indices": candidate["candidate_indices"],
        "raw_values": candidate["config"],
        "mapped_payload": payload,
        "guessed_required_fields": [],
        "unresolved_required_fields": [],
        "rejection": None,
    }

request = json.load(open(sys.argv[1], "r", encoding="utf-8"))
config = LibraryIO.read(request["yaml_path"])
benchmark_problem = config["BenchmarkProblems"][0]
process = BenchmarkProcess(benchmark_problem[0], benchmark_problem[1], False)
step = process[0]
isa = gfxToIsa("gfx942")
isa_map = makeIsaInfoMap([isa], request["compiler"])
assignGlobalParameters(config["GlobalParameters"], isa_map)
debug = makeDebugConfig(config["GlobalParameters"])
assembler = Assembler(request["compiler"], "4", False)
rows = []
for candidate in request["candidates"]:
    # Each candidate is an independent mapping/provenance row.  Kernel-name
    # reuse across two distinct candidates is not a mapping failure, so
    # duplicate suppression is scoped to one candidate's split-GSU kernels.
    visited_kernel_bases = set()
    solution = _generate_single_solution_with_groups(
        candidate["config"],
        process.problemType,
        dict(step.constantParams),
        assembler,
        debug,
        isa_map,
        silent=True,
    )
    if solution is None:
        if request["retain_rows"]:
            rows.extend(
                rejected(candidate, size, "pinned_validation_boundary_none")
                for size in request["sizes"]
            )
        continue
    solution["SolutionIndex"] = int(candidate["slot"])
    kernels = solution.getKernels()
    unique_kernels = []
    for kernel in kernels:
        base = getKernelFileBase(debug.splitGSU, kernel)
        kernel.duplicate = base in visited_kernel_bases
        if not kernel.duplicate:
            kernel["BaseName"] = base
            unique_kernels.append(kernel)
        visited_kernel_bases.add(base)
    if not unique_kernels:
        if request["retain_rows"]:
            rows.extend(
                rejected(candidate, size, "canonical_duplicate_kernel")
                for size in request["sizes"]
            )
        continue
    writer = KernelWriterAssembly(assembler, debug)
    toolchain = rocIsa.getInstance()
    options = toolchain.getOutputOptions()
    results = [
        processKernelSource(
            writer, toolchain.getData(), options, debug.splitGSU, kernel
        )
        for kernel in unique_kernels
    ]
    errors = [int(result.err) for result in results if int(result.err) != 0]
    if errors:
        if request["retain_rows"]:
            rows.extend(
                rejected(candidate, size, "pinned_codegen_nonzero")
                for size in request["sizes"]
            )
        continue
    passPostKernelInfoToSolution(results, unique_kernels, [solution], debug.splitGSU)
    master = MasterSolutionLibrary.BenchmarkingLibrary(
        [solution], assembler, debug.splitGSU, False, False, isa_map
    )
    passPostKernelInfoToLibrary(
        results, unique_kernels, {"gfx942": master}, debug.splitGSU
    )
    library_solution = master.solutions[int(candidate["slot"])]
    if request["retain_rows"]:
        rows.extend(
            accepted(
                candidate,
                size,
                solution,
                library_solution,
                results,
                unique_kernels,
                debug.splitGSU,
            )
            for size in request["sizes"]
        )
print(
    MARKER
    + json.dumps(
        {
            "processed_candidates": len(request["candidates"]),
            "processed_size_rows": len(request["candidates"]) * len(request["sizes"]),
            "rows": rows if request["retain_rows"] else None,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
)
'''


def mandatory_atoms(
    prelocked_atoms: set[str] | frozenset[str],
    support_states: Mapping[str, str],
) -> frozenset[str]:
    unknown = set(prelocked_atoms).difference(support_states)
    if unknown:
        raise MappingError(f"support states missing prelocked atoms: {sorted(unknown)}")
    return frozenset(
        atom_id
        for atom_id in prelocked_atoms
        if support_states[atom_id] == "supported_witnessed"
    )


def _occurrence_key(witness: Mapping[str, Any]) -> tuple[Any, ...]:
    required = {
        "stream_rank",
        "conditional_priority_rank",
        "chunk_index",
        "draw_index",
        "config_hash",
    }
    missing = sorted(required.difference(witness))
    if missing:
        raise MappingError(f"witness missing occurrence fields: {missing}")
    return (
        int(witness["stream_rank"]),
        int(witness["conditional_priority_rank"]),
        int(witness["chunk_index"]),
        int(witness["draw_index"]),
        str(witness["config_hash"]),
    )


def _deduplicate_witnesses(
    witnesses: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    first: dict[str, dict[str, Any]] = {}
    for raw in witnesses:
        witness = dict(raw)
        config_hash = witness.get("config_hash")
        coverage = witness.get("covered_atom_ids")
        if not isinstance(config_hash, str) or len(config_hash) != 64:
            raise MappingError("witness config_hash must be a SHA-256 string")
        if not isinstance(coverage, Sequence) or isinstance(coverage, (str, bytes)):
            raise MappingError("witness covered_atom_ids must be a sequence")
        witness["covered_atom_ids"] = sorted(set(str(atom) for atom in coverage))
        key = _occurrence_key(witness)
        previous = first.get(config_hash)
        if previous is None or key < _occurrence_key(previous):
            first[config_hash] = witness
    return sorted(first.values(), key=_occurrence_key)


def exact_ten_greedy_cover(
    witnesses: Sequence[Mapping[str, Any]],
    required_atoms: set[str] | frozenset[str],
) -> dict[str, Any]:
    """Select exactly ten distinct hashes with the frozen greedy/tie-break rule."""

    unique = _deduplicate_witnesses(witnesses)
    if len(unique) < 10:
        raise MappingError("FT-INCONCLUSIVE: fewer than ten distinct valid witnesses")
    remaining = set(required_atoms)
    selected: list[dict[str, Any]] = []
    pool = list(unique)
    while remaining:
        ranked = sorted(
            pool,
            key=lambda witness: (
                -len(remaining.intersection(witness["covered_atom_ids"])),
                _occurrence_key(witness),
                witness["config_hash"],
            ),
        )
        best = ranked[0]
        gain = remaining.intersection(best["covered_atom_ids"])
        if not gain:
            raise MappingError("FT-INCONCLUSIVE: mandatory atom is not covered")
        selected.append(best)
        pool.remove(best)
        remaining.difference_update(gain)
        if len(selected) > 10:
            raise MappingError("FT-INCONCLUSIVE: mandatory cover requires more than ten configs")
    selected_hashes = {witness["config_hash"] for witness in selected}
    for witness in unique:
        if len(selected) == 10:
            break
        if witness["config_hash"] not in selected_hashes:
            selected.append(witness)
            selected_hashes.add(witness["config_hash"])
    if len(selected) != 10:
        raise MappingError("FT-INCONCLUSIVE: unable to fill exact-ten corpus")
    selected.sort(key=lambda witness: witness["config_hash"])
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "selection_rule": "deterministic_greedy_cover_v1",
        "required_atom_ids": sorted(required_atoms),
        "config_hashes": [witness["config_hash"] for witness in selected],
        "witnesses": selected,
        "anchor_indices": [0, 4, 9],
        "anchor_hashes": [selected[index]["config_hash"] for index in (0, 4, 9)],
    }
    return {**body, "mapping_corpus_digest": canonical_sha256(body)}


def verify_ab_parity(
    pass_a: Sequence[Mapping[str, Any]],
    pass_b: Sequence[Mapping[str, Any]],
    *,
    expected_config_hashes: Sequence[str],
    expected_size_ids: Sequence[str],
) -> dict[str, Any]:
    """Require exact 10x3 row identity and byte-semantic A/B parity."""

    if len(expected_config_hashes) != 10 or len(set(expected_config_hashes)) != 10:
        raise MappingError("mapping corpus must contain ten distinct config hashes")
    if len(expected_size_ids) != 3 or len(set(expected_size_ids)) != 3:
        raise MappingError("mapping requires three distinct size ids")
    expected_keys = {
        (config_hash, size_id)
        for config_hash in expected_config_hashes
        for size_id in expected_size_ids
    }

    def index(rows: Sequence[Mapping[str, Any]], label: str) -> dict[tuple[str, str], bytes]:
        if len(rows) != 30:
            raise MappingError(f"{label} must contain exactly 30 rows")
        result: dict[tuple[str, str], bytes] = {}
        for row in rows:
            key = (str(row.get("config_hash")), str(row.get("size_id")))
            if key in result:
                raise MappingError(f"{label} contains duplicate row {key}")
            if row.get("mapping_status") != "accepted":
                raise MappingError(f"{label} contains non-accepted mapping row {key}")
            if row.get("guessed_required_fields"):
                raise MappingError(f"{label} guessed required mapping fields for {key}")
            if row.get("unresolved_required_fields"):
                raise MappingError(f"{label} has unresolved required mapping fields for {key}")
            result[key] = canonical_json_bytes(row)
        if set(result) != expected_keys:
            raise MappingError(f"{label} row keys differ from exact 10x3 panel")
        return result

    indexed_a = index(pass_a, "pass A")
    indexed_b = index(pass_b, "pass B")
    mismatches = sorted(key for key in expected_keys if indexed_a[key] != indexed_b[key])
    if mismatches:
        raise MappingError(f"fresh A/B mapping parity mismatch: {mismatches}")
    body = {
        "schema_version": 1,
        "row_count": 30,
        "pass_a_digest": canonical_sha256(list(pass_a)),
        "pass_b_digest": canonical_sha256(list(pass_b)),
        "status": "PASS",
    }
    return {**body, "parity_digest": canonical_sha256(body)}
