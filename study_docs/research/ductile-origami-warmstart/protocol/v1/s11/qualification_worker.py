#!/usr/bin/env python3
# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Pinned S11 resolver -> normal KernelWriter -> assembler worker.

This program is invoked only through :class:`PinnedQualificationWorker` after
its Python, source, compiler, input, and contract hashes have been checked.
It accepts one raw occurrence on stdin and emits one strict JSON attempt.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import inspect
import json
import math
import os
import sys
from pathlib import Path
from typing import Any


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plain(value: Any) -> Any:
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("non-finite resolver value")
        return value
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if type(value) is dict:
        return {str(key): plain(item) for key, item in value.items()}
    if hasattr(value, "state"):
        state = value.state
        return plain(state() if inspect.ismethod(state) else state)
    raise TypeError(f"unsupported resolver value: {type(value).__name__}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validator-session", action="store_true")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--yaml", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path)
    arguments = parser.parse_args()
    if not arguments.validator_session and arguments.workspace_root is None:
        parser.error("--workspace-root is required outside --validator-session")
    return arguments


def _strict_request(line: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate validator request key")
            result[key] = value
        return result

    value = json.loads(line, object_pairs_hook=pairs)
    if type(value) is not dict:
        raise ValueError("validator request is not an object")
    return value


def main() -> int:
    arguments = parse_arguments()
    tensile_root = arguments.repository_root / "projects/hipblaslt/tensilelite"
    sys.path.insert(0, str(tensile_root))
    from Tensile import LibraryIO
    from Tensile.BenchmarkStructs import BenchmarkProcess
    from Tensile.Common.Architectures import gfxToIsa, isaToGfx
    from Tensile.Common.Capabilities import makeIsaInfoMap
    from Tensile.Common.GlobalParameters import assignGlobalParameters
    from Tensile.Common.Types import makeDebugConfig
    from Tensile.KernelWriterAssembly import KernelWriterAssembly
    from Tensile.SolutionStructs.Naming import getKernelFileBase
    from Tensile.SolutionLibrary import MasterSolutionLibrary
    from Tensile.TensileCreateLibrary.Run import (
        passPostKernelInfoToLibrary,
        passPostKernelInfoToSolution,
        processKernelSource,
        writeAssembly,
    )
    from Tensile.Toolchain.Component import Assembler
    from Tensile.backends.ductile_backend import (
        _generate_single_solution_with_groups,
        _validate_solution,
    )
    from rocisa import rocIsa

    document = LibraryIO.read(str(arguments.yaml))
    benchmark_problem = document["BenchmarkProblems"][0]
    process = BenchmarkProcess(benchmark_problem[0], benchmark_problem[1], False)
    step = process[0]
    isa = gfxToIsa("gfx942")
    isa_map = makeIsaInfoMap([isa], str(arguments.compiler))
    assignGlobalParameters(document["GlobalParameters"], isa_map)
    debug = makeDebugConfig(document["GlobalParameters"])
    assembler = Assembler(arguments.compiler, "4", False)
    os.environ["Tensile_ASM_COMPILER_LAUNCHER"] = ""

    if arguments.validator_session:
        protocol = "s11_validator_session_v2"
        provenance = {
            "executable_sha256": file_digest(Path(sys.executable).resolve()),
            "validator_source_sha256": file_digest(Path(__file__).resolve()),
            "normal_valid_fn_path": True,
            "valid_fn": "Tensile.backends.ductile_backend._validate_solution",
            "proxy_or_substitution": False,
            "session_protocol": protocol,
        }
        expected = {
            "protocol", "stream_id", "chunk_index", "slot_index",
            "raw_configuration",
        }
        for line in sys.stdin.buffer:
            request = _strict_request(line)
            if (
                set(request) != expected
                or request["protocol"] != protocol
                or type(request["stream_id"]) is not str
                or not request["stream_id"]
                or type(request["chunk_index"]) is not int
                or request["chunk_index"] < 0
                or type(request["slot_index"]) is not int
                or request["slot_index"] < 0
                or type(request["raw_configuration"]) is not dict
                or not request["raw_configuration"]
            ):
                raise ValueError("validator request schema/context changed")
            request_sha256 = digest(request)
            with contextlib.redirect_stdout(sys.stderr):
                accepted = _validate_solution(
                    process.problemType, dict(step.constantParams), assembler,
                    debug, isa_map, request["raw_configuration"],
                )
            if type(accepted) is not bool:
                raise TypeError("pinned validator returned a non-boolean result")
            response = {
                "protocol": protocol,
                "request_sha256": request_sha256,
                "accepted": accepted,
                "provenance": provenance,
            }
            sys.__stdout__.write(canonical(response).decode("utf-8") + "\n")
            sys.__stdout__.flush()
        return 0

    request = json.load(sys.stdin)
    expected_request = {
        "protocol",
        "request_sha256",
        "role",
        "workspace_root_id",
        "raw_configuration",
        "semantic_identity_schema",
        "occurrence_ids",
        "alias_fanout_sha256",
    }
    if type(request) is not dict or set(request) != expected_request:
        raise ValueError("qualification request schema/unknown-property failure")
    body = dict(request)
    recorded_request_hash = body.pop("request_sha256")
    if digest(body) != recorded_request_hash or request["protocol"] != "s11_qualification_v1":
        raise ValueError("qualification request digest/protocol mismatch")
    if request["role"] not in ("producer", "fresh_verifier"):
        raise ValueError("qualification role is not allowlisted")
    if (
        type(request["occurrence_ids"]) is not list
        or not request["occurrence_ids"]
        or len(set(request["occurrence_ids"])) != len(request["occurrence_ids"])
        or any(type(item) is not str or len(item) != 64 for item in request["occurrence_ids"])
        or type(request["alias_fanout_sha256"]) is not str
        or len(request["alias_fanout_sha256"]) != 64
    ):
        raise ValueError("qualification occurrence/alias binding is malformed")
    assert arguments.workspace_root is not None
    workspace = arguments.workspace_root.resolve()
    workspace.mkdir(parents=True, exist_ok=False)
    assembly_root = workspace / "assembly"
    assembly_root.mkdir()

    with contextlib.redirect_stdout(sys.stderr):
        solution = _generate_single_solution_with_groups(
            request["raw_configuration"],
            process.problemType,
            dict(step.constantParams),
            assembler,
            debug,
            isa_map,
            silent=True,
        )
    if solution is None:
        raise RuntimeError("complete resolver projection unavailable")
    solution["SolutionIndex"] = 0
    visited: set[str] = set()
    unique_kernels = []
    for kernel in solution.getKernels():
        base = getKernelFileBase(debug.splitGSU, kernel)
        if base not in visited:
            kernel.duplicate = False
            kernel["BaseName"] = base
            unique_kernels.append(kernel)
        visited.add(base)
    if not unique_kernels:
        raise RuntimeError("normal KernelWriter produced no associated kernel")

    writer = KernelWriterAssembly(assembler, debug)
    toolchain = rocIsa.getInstance()
    output_options = toolchain.getOutputOptions()
    generated = []
    association_rows = []
    resolver_path = Path(inspect.getsourcefile(_generate_single_solution_with_groups) or "")
    writer_path = Path(inspect.getsourcefile(KernelWriterAssembly) or "")
    compiler_argv = [
        str(arguments.compiler), "-x", "assembler", "--target=amdgcn-amd-amdhsa",
        "-mcode-object-version=4", "-c", "-mcpu=gfx942",
    ]
    provenance = {
        "resolver_source_sha256": file_digest(resolver_path),
        "kernelwriter_source_sha256": file_digest(writer_path),
        "compiler_sha256": file_digest(arguments.compiler),
        "compiler_argv_prefix": compiler_argv,
        "generation_path": "normal_non_proxy_KernelWriterAssembly_then_pinned_assembler",
        "association_preserved": True,
    }
    for kernel in unique_kernels:
        with contextlib.redirect_stdout(sys.stderr):
            result = processKernelSource(
                writer, toolchain.getData(), output_options, debug.splitGSU, kernel
            )
        if int(result.err) != 0:
            response = {
                "protocol": "s11_qualification_v1",
                "request_sha256": recorded_request_hash,
                "role": request["role"],
                "workspace_root_id": request["workspace_root_id"],
                "complete": True,
                "result": "normal_reject",
                "semantic_identity": None,
                "reason_code": "normal_kernelwriter_reject",
                "no_guess": True,
                "association": {"solution_sha256": digest(plain(solution._state)), "kernels": []},
                "provenance": provenance,
                "occurrence_ids_sha256": digest(request["occurrence_ids"]),
                "alias_fanout_sha256": request["alias_fanout_sha256"],
            }
            sys.__stdout__.write(canonical(response).decode("utf-8") + "\n")
            return 0
        generated.append(result)
        source_path, kernel_isa, wavefront, _ = writeAssembly(assembly_root, result)
        object_path = source_path.with_suffix(".o")
        with contextlib.redirect_stdout(sys.stderr):
            assembler(isaToGfx(kernel_isa), wavefront, str(source_path), str(object_path))
        association_rows.append(
            {
                "kernel_name": str(result.name),
                "kernel_source_sha256": file_digest(source_path),
                "compile_output_sha256": file_digest(object_path),
            }
        )

    passPostKernelInfoToSolution(generated, unique_kernels, [solution], debug.splitGSU)
    master = MasterSolutionLibrary.BenchmarkingLibrary(
        [solution], assembler, debug.splitGSU, False, False, isa_map
    )
    passPostKernelInfoToLibrary(
        generated, unique_kernels, {"gfx942": master}, debug.splitGSU
    )
    mapped = master.solutions[0].sizeMapping
    required_mapping = (
        "waveNum", "macroTile", "matrixInstruction", "grvwA", "grvwB", "gwvwC",
        "gwvwD", "depthU", "globalSplitU", "workGroupMapping", "globalAccumulation",
        "workGroupMappingXCC", "workGroupMappingXCCGroup", "globalSplitUCoalesced",
        "globalSplitUWorkGroupMappingRoundRobin", "CUOccupancy", "PrefetchGlobalRead",
        "MathClocksUnrolledLoop", "DirectToVgprA", "DirectToVgprB",
        "NumLoadsCoalescedA", "NumLoadsCoalescedB", "VectorWidthA", "VectorWidthB",
        "LocalSplitU", "DirectToLdsA", "DirectToLdsB", "WaveGroup",
    )
    missing = [field for field in required_mapping if not hasattr(mapped, field)]
    if missing:
        raise RuntimeError("consumer SizeMapping projection incomplete: " + ",".join(missing))
    size_mapping = {
        "waveNum": int(mapped.waveNum),
        "macroTile": [int(value) for value in mapped.macroTile],
        "matrixInstruction": [int(value) for value in mapped.matrixInstruction],
        "grvwA": int(mapped.grvwA), "grvwB": int(mapped.grvwB),
        "gwvwC": int(mapped.gwvwC), "gwvwD": int(mapped.gwvwD),
        "depthU": int(mapped.depthU), "globalSplitU": int(mapped.globalSplitU),
        "workGroupMapping": int(mapped.workGroupMapping),
        "globalAccumulation": int(mapped.globalAccumulation),
        "workGroupMappingXCC": int(mapped.workGroupMappingXCC),
        "workGroupMappingXCCGroup": int(mapped.workGroupMappingXCCGroup),
        "globalSplitUCoalesced": bool(mapped.globalSplitUCoalesced),
        "globalSplitUWorkGroupMappingRoundRobin": bool(mapped.globalSplitUWorkGroupMappingRoundRobin),
        "CUOccupancy": int(mapped.CUOccupancy),
        "PrefetchGlobalRead": int(mapped.PrefetchGlobalRead),
        "MathClocksUnrolledLoop": int(mapped.MathClocksUnrolledLoop),
        "DirectToVgprA": bool(mapped.DirectToVgprA),
        "DirectToVgprB": bool(mapped.DirectToVgprB),
        "NumLoadsCoalescedA": int(mapped.NumLoadsCoalescedA),
        "NumLoadsCoalescedB": int(mapped.NumLoadsCoalescedB),
        "VectorWidthA": int(mapped.VectorWidthA), "VectorWidthB": int(mapped.VectorWidthB),
        "LocalSplitU": int(mapped.LocalSplitU), "DirectToLdsA": bool(mapped.DirectToLdsA),
        "DirectToLdsB": bool(mapped.DirectToLdsB),
        "waveGroup": [int(value) for value in mapped.WaveGroup],
    }
    if size_mapping["globalSplitU"] < 1:
        raise RuntimeError("unresolved/auto GlobalSplitU is forbidden")
    resolver_projection = plain(solution._state)
    identity_body = {
        "schema_version": request["semantic_identity_schema"],
        "resolver_projection": resolver_projection,
        "consumer_fields": size_mapping,
    }
    semantic_id = digest(identity_body)
    response = {
        "protocol": "s11_qualification_v1",
        "request_sha256": recorded_request_hash,
        "role": request["role"],
        "workspace_root_id": request["workspace_root_id"],
        "complete": True,
        "result": "accepted",
        "semantic_identity": semantic_id,
        "reason_code": "complete_normal_generation_and_compile",
        "no_guess": True,
        "association": {
            "solution_sha256": digest(resolver_projection),
            "kernels": association_rows,
            "size_mapping": size_mapping,
        },
        "provenance": provenance,
        "occurrence_ids_sha256": digest(request["occurrence_ids"]),
        "alias_fanout_sha256": request["alias_fanout_sha256"],
    }
    sys.__stdout__.write(canonical(response).decode("utf-8") + "\n")
    return 0


if __name__ == "__main__":
    with contextlib.redirect_stdout(sys.stderr):
        raise SystemExit(main())
