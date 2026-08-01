# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Pinned resolver mapping records and exact fresh A/B parity."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from .contract import canonical_sha256


class MappingError(ValueError):
    """A mapping row, provenance field, pass, or parity invariant failed."""


SIZES = (
    {"size_id": "small", "value": [8, 8, 1, 128]},
    {"size_id": "medium", "value": [256, 256, 1, 1024]},
    {"size_id": "large", "value": [2304, 1024, 1, 214336]},
)

FORMOCAST_FIELDS = (
    "waveNum",
    "macroTile",
    "matrixInstruction",
    "grvwA",
    "grvwB",
    "gwvwC",
    "gwvwD",
    "depthU",
    "globalSplitU",
    "workGroupMapping",
    "globalAccumulation",
    "workGroupMappingXCC",
    "workGroupMappingXCCGroup",
    "globalSplitUCoalesced",
    "globalSplitUWorkGroupMappingRoundRobin",
    "CUOccupancy",
    "PrefetchGlobalRead",
    "MathClocksUnrolledLoop",
    "DirectToVgprA",
    "DirectToVgprB",
    "NumLoadsCoalescedA",
    "NumLoadsCoalescedB",
    "VectorWidthA",
    "VectorWidthB",
    "LocalSplitU",
    "DirectToLdsA",
    "DirectToLdsB",
    "waveGroup",
)

MAPPING_RESULT_MARKER = "S10R3_MAPPING_RESULT="
MAPPING_FAILURE_MARKER = "S10R3_MAPPING_FAILURE="
MAPPING_FAILURE_RETURN_CODE = 23


def mapping_worker_code() -> str:
    """Return the pinned-process worker used independently by passes A and B."""

    return r'''
import hashlib
import inspect
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
from Tensile.SolutionStructs.Naming import getKernelFileBase
from Tensile.backends.ductile_backend import _generate_single_solution_with_groups
from rocisa import rocIsa

MARKER = "S10R3_MAPPING_RESULT="
FAILURE_MARKER = "S10R3_MAPPING_FAILURE="
FAILURE_RETURN_CODE = 23
FIELDS = [
    "waveNum", "macroTile", "matrixInstruction", "grvwA", "grvwB",
    "gwvwC", "gwvwD", "depthU", "globalSplitU", "workGroupMapping",
    "globalAccumulation", "workGroupMappingXCC", "workGroupMappingXCCGroup",
    "globalSplitUCoalesced", "globalSplitUWorkGroupMappingRoundRobin",
    "CUOccupancy", "PrefetchGlobalRead", "MathClocksUnrolledLoop",
    "DirectToVgprA", "DirectToVgprB", "NumLoadsCoalescedA",
    "NumLoadsCoalescedB", "VectorWidthA", "VectorWidthB", "LocalSplitU",
    "DirectToLdsA", "DirectToLdsB", "waveGroup",
]

def canonical_digest(value):
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def emit_codegen_failure(slot, candidate, kernel_failures):
    if not kernel_failures or any(
        item.get("result_error_code") != -2
        or item.get("overflowed_resources") != 5
        for item in kernel_failures
    ):
        raise RuntimeError("nonallowlisted mapping code-generation failure")
    body = {
        "failure_kind": "required_mapping_code_generation",
        "category": "code_generation_nonzero",
        "error_class": "KernelWriterAssembly_overflowedResources",
        "error_code": 5,
        "slot": slot,
        "config_hash": canonical_digest(candidate),
        "kernel_failures": kernel_failures,
    }
    failure = {**body, "failure_signature": canonical_digest(body)}
    print(
        FAILURE_MARKER
        + json.dumps(
            failure,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    )
    raise SystemExit(FAILURE_RETURN_CODE)

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
        state_value = value.state
        if inspect.ismethod(state_value):
            if state_value.__self__ is not value or state_value.__name__ != "state":
                raise TypeError("unsupported mapping state method binding")
            return plain(state_value())
        if callable(state_value):
            raise TypeError("unsupported callable mapping state")
        return plain(state_value)
    raise TypeError("unsupported mapping value: " + type(value).__name__)

request = json.load(open(sys.argv[1], "r", encoding="utf-8"))
if request["config_hashes"] != [
    canonical_digest(candidate) for candidate in request["configs"]
]:
    raise RuntimeError("pinned mapping config order/hash binding drift")
for path_key, hash_key in (
    ("yaml_path", "yaml_sha256"),
    ("provenance_source_path", "provenance_source_sha256"),
):
    if hashlib.sha256(open(request[path_key], "rb").read()).hexdigest() != request[hash_key]:
        raise RuntimeError("pinned mapping source binding drift: " + path_key)
document = LibraryIO.read(request["yaml_path"])
benchmark_problem = document["BenchmarkProblems"][0]
process = BenchmarkProcess(benchmark_problem[0], benchmark_problem[1], False)
step = process[0]
isa = gfxToIsa("gfx942")
isa_map = makeIsaInfoMap([isa], request["compiler"])
assignGlobalParameters(document["GlobalParameters"], isa_map)
debug = makeDebugConfig(document["GlobalParameters"])
assembler = Assembler(request["compiler"], "4", False)
source_path = request["provenance_source_path"]
source_sha256 = hashlib.sha256(open(source_path, "rb").read()).hexdigest()
provenance = {
    field: {
        "source": "pinned MasterSolutionLibrary SizeMapping",
        "source_path": request["provenance_record_path"],
        "source_sha256": source_sha256,
    }
    for field in FIELDS
}
rows = []
for slot, candidate in enumerate(request["configs"]):
    visited = set()
    solution = _generate_single_solution_with_groups(
        candidate,
        process.problemType,
        dict(step.constantParams),
        assembler,
        debug,
        isa_map,
        silent=True,
    )
    if solution is None:
        raise RuntimeError("pinned mapping resolver returned None")
    solution["SolutionIndex"] = slot
    unique_kernels = []
    for kernel in solution.getKernels():
        base = getKernelFileBase(debug.splitGSU, kernel)
        if base not in visited:
            kernel.duplicate = False
            kernel["BaseName"] = base
            unique_kernels.append(kernel)
        visited.add(base)
    if not unique_kernels:
        raise RuntimeError("pinned mapping produced no unique kernel")
    writer = KernelWriterAssembly(assembler, debug)
    toolchain = rocIsa.getInstance()
    options = toolchain.getOutputOptions()
    generated = []
    kernel_failures = []
    for kernel_index, kernel in enumerate(unique_kernels):
        result = processKernelSource(
            writer, toolchain.getData(), options, debug.splitGSU, kernel
        )
        generated.append(result)
        if int(result.err) != 0:
            kernel_failures.append(
                {
                    "kernel_index": kernel_index,
                    "kernel_name": str(result.name),
                    "result_error_code": int(result.err),
                    "overflowed_resources": int(
                        getattr(writer.states, "overflowedResources", 0)
                    ),
                }
            )
    if kernel_failures:
        emit_codegen_failure(slot, candidate, kernel_failures)
    passPostKernelInfoToSolution(
        generated, unique_kernels, [solution], debug.splitGSU
    )
    master = MasterSolutionLibrary.BenchmarkingLibrary(
        [solution], assembler, debug.splitGSU, False, False, isa_map
    )
    passPostKernelInfoToLibrary(
        generated, unique_kernels, {"gfx942": master}, debug.splitGSU
    )
    mapped = master.solutions[slot].sizeMapping
    required_native = [
        "waveNum", "macroTile", "matrixInstruction", "grvwA", "grvwB",
        "gwvwC", "gwvwD", "depthU", "globalSplitU", "workGroupMapping",
        "globalAccumulation", "workGroupMappingXCC",
        "workGroupMappingXCCGroup", "globalSplitUCoalesced",
        "globalSplitUWorkGroupMappingRoundRobin", "CUOccupancy",
        "PrefetchGlobalRead", "MathClocksUnrolledLoop", "DirectToVgprA",
        "DirectToVgprB", "NumLoadsCoalescedA", "NumLoadsCoalescedB",
        "VectorWidthA", "VectorWidthB", "LocalSplitU", "DirectToLdsA",
        "DirectToLdsB", "WaveGroup",
    ]
    missing = [field for field in required_native if not hasattr(mapped, field)]
    if missing:
        raise KeyError("unresolved SizeMapping fields: " + ",".join(missing))
    size_mapping = {
        "waveNum": int(mapped.waveNum),
        "macroTile": [int(value) for value in mapped.macroTile],
        "matrixInstruction": [int(value) for value in mapped.matrixInstruction],
        "grvwA": int(mapped.grvwA),
        "grvwB": int(mapped.grvwB),
        "gwvwC": int(mapped.gwvwC),
        "gwvwD": int(mapped.gwvwD),
        "depthU": int(mapped.depthU),
        "globalSplitU": int(mapped.globalSplitU),
        "workGroupMapping": int(mapped.workGroupMapping),
        "globalAccumulation": int(mapped.globalAccumulation),
        "workGroupMappingXCC": int(mapped.workGroupMappingXCC),
        "workGroupMappingXCCGroup": int(mapped.workGroupMappingXCCGroup),
        "globalSplitUCoalesced": bool(mapped.globalSplitUCoalesced),
        "globalSplitUWorkGroupMappingRoundRobin": bool(
            mapped.globalSplitUWorkGroupMappingRoundRobin
        ),
        "CUOccupancy": int(mapped.CUOccupancy),
        "PrefetchGlobalRead": int(mapped.PrefetchGlobalRead),
        "MathClocksUnrolledLoop": int(mapped.MathClocksUnrolledLoop),
        "DirectToVgprA": bool(mapped.DirectToVgprA),
        "DirectToVgprB": bool(mapped.DirectToVgprB),
        "NumLoadsCoalescedA": int(mapped.NumLoadsCoalescedA),
        "NumLoadsCoalescedB": int(mapped.NumLoadsCoalescedB),
        "VectorWidthA": int(mapped.VectorWidthA),
        "VectorWidthB": int(mapped.VectorWidthB),
        "LocalSplitU": int(mapped.LocalSplitU),
        "DirectToLdsA": bool(mapped.DirectToLdsA),
        "DirectToLdsB": bool(mapped.DirectToLdsB),
        "waveGroup": [int(value) for value in mapped.WaveGroup],
    }
    if size_mapping["globalSplitU"] < 1:
        raise ValueError("unresolved/auto GlobalSplitU is forbidden")
    rows.append(
        {
            "config": plain(candidate),
            "resolved_solution": plain(solution._state),
            "size_mapping": size_mapping,
            "formocast_input": size_mapping,
            "required_field_provenance": provenance,
        }
    )
print(
    MARKER
    + json.dumps(
        {"processed_configs": len(request["configs"]), "rows": rows},
        sort_keys=True,
        separators=(",", ":"),
    )
)
'''


def size_registry_document() -> dict[str, Any]:
    body = {
        "document_kind": "size_registry",
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "coordinate_order": ["M", "N", "batch", "K"],
        "dtype": "B/B/S",
        "layout": "NN",
        "batched": True,
        "soo": False,
        "reduce_fn": "max",
        "n_elements_to_validate": 128,
        "sizes": list(SIZES),
    }
    return {**body, "registry_digest": canonical_sha256(body)}


def canonical_config_hash(config: Mapping[str, Any]) -> str:
    return canonical_sha256(dict(config))


def canonical_solution_hash(solution: Mapping[str, Any]) -> str:
    return canonical_sha256(dict(solution))


def mapping_row(
    *,
    pass_id: str,
    config: Mapping[str, Any],
    size_id: str,
    resolved_solution: Mapping[str, Any],
    size_mapping: Mapping[str, Any],
    formocast_input: Mapping[str, Any],
    required_field_provenance: Mapping[str, Any],
) -> dict[str, Any]:
    if pass_id not in {"A", "B"}:
        raise MappingError("mapping pass must be A or B")
    expected_sizes = {item["size_id"] for item in SIZES}
    if size_id not in expected_sizes:
        raise MappingError("mapping size is foreign")
    if set(formocast_input) != set(FORMOCAST_FIELDS):
        raise MappingError("Formocast required field set is incomplete")
    if set(required_field_provenance) != set(FORMOCAST_FIELDS):
        raise MappingError("Formocast provenance field set is incomplete")
    for field in FORMOCAST_FIELDS:
        provenance = required_field_provenance[field]
        if (
            type(provenance) is not dict
            or set(provenance) != {"source", "source_path", "source_sha256"}
            or not all(provenance.values())
        ):
            raise MappingError(f"required field provenance is guessed/unresolved: {field}")
    config_hash = canonical_config_hash(config)
    solution_hash = canonical_solution_hash(resolved_solution)
    body = {
        "pass_id": pass_id,
        "config_hash": config_hash,
        "size_id": size_id,
        "raw_config": dict(config),
        "resolved_solution": dict(resolved_solution),
        "resolved_solution_hash": solution_hash,
        "size_mapping": dict(size_mapping),
        "formocast_input": dict(formocast_input),
        "required_field_provenance": dict(required_field_provenance),
    }
    return {**body, "row_digest": canonical_sha256(body)}


def run_mapping_batch(
    *,
    pass_id: str,
    configs: Sequence[Mapping[str, Any]],
    resolver: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not 10 <= len(configs) <= 20:
        raise MappingError("mapping corpus must contain exact K in [10,20]")
    if len({canonical_config_hash(config) for config in configs}) != len(configs):
        raise MappingError("mapping corpus configs must be distinct")
    rows = []
    for config in configs:
        for size in SIZES:
            result = resolver(config, size)
            if type(result) is not dict:
                raise MappingError("resolver returned a non-object")
            required = {
                "resolved_solution",
                "size_mapping",
                "formocast_input",
                "required_field_provenance",
            }
            if set(result) != required:
                raise MappingError("resolver result schema is incomplete or unknown")
            rows.append(
                mapping_row(
                    pass_id=pass_id,
                    config=config,
                    size_id=size["size_id"],
                    **result,
                )
            )
    if len(rows) != 3 * len(configs) or len(rows) > 60:
        raise MappingError("mapping pass row count invariant failed")
    return rows


def _row_parity_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: row[key]
        for key in (
            "config_hash",
            "size_id",
            "raw_config",
            "resolved_solution",
            "resolved_solution_hash",
            "size_mapping",
            "formocast_input",
            "required_field_provenance",
        )
    }


def verify_mapping_parity(
    pass_a: Sequence[Mapping[str, Any]],
    pass_b: Sequence[Mapping[str, Any]],
    *,
    k: int,
) -> dict[str, Any]:
    if type(k) is not int or not 10 <= k <= 20:
        raise MappingError("mapping parity K must be in [10,20]")
    if len(pass_a) != 3 * k or len(pass_b) != 3 * k:
        raise MappingError("mapping A/B must each contain exactly 3K rows")
    by_key: dict[str, dict[tuple[str, str], Mapping[str, Any]]] = {"A": {}, "B": {}}
    for expected_pass, rows in (("A", pass_a), ("B", pass_b)):
        for row in rows:
            if row.get("pass_id") != expected_pass:
                raise MappingError("mapping pass-local identity mismatch")
            body = dict(row)
            recorded = body.pop("row_digest", None)
            if recorded != canonical_sha256(body):
                raise MappingError("mapping row digest mismatch")
            key = (row["config_hash"], row["size_id"])
            if key in by_key[expected_pass]:
                raise MappingError("mapping row key duplicated")
            by_key[expected_pass][key] = row
    if set(by_key["A"]) != set(by_key["B"]):
        raise MappingError("mapping A/B key sets differ")
    for key in by_key["A"]:
        if _row_parity_projection(by_key["A"][key]) != _row_parity_projection(
            by_key["B"][key]
        ):
            raise MappingError(f"mapping A/B parity failed: {key}")
    body = {
        "document_kind": "mapping_corpus",
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "k": k,
        "rows_per_pass": 3 * k,
        "pass_a": list(pass_a),
        "pass_b": list(pass_b),
        "parity": True,
    }
    return {**body, "corpus_digest": canonical_sha256(body)}
