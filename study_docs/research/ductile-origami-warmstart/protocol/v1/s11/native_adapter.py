# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Pinned JSON-lines adapter for the native Ductile Formocast runtime path."""

from __future__ import annotations

import math
import os
import stat
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from .canonical import (
    canonical_json_bytes,
    canonical_sha256,
    exclusive_write_json,
    sha256_file,
    strict_json_loads,
    strict_load_json,
)


class NativeAdapterError(ValueError):
    """Native runtime output is partial, substituted, or not finite."""


SCALAR_MAPPING_FIELDS = (
    "waveNum",
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
)


def derive_sealed_execution_argv(
    *,
    compiler_path: Path | str,
    pinned_source_root: Path | str,
    rocm_root: Path | str,
    linked_sources: Sequence[Path | str],
    linked_objects: Sequence[Path | str],
    generated_header: Path | str,
    helper_path: Path | str,
    qualification_python_path: Path | str,
    qualification_worker_source_path: Path | str,
    qualification_yaml_path: Path | str,
    qualification_repository_root: Path | str = "{pinned_source_root}",
    qualification_workspace_root: Path | str = "{workspace_root}",
) -> dict[str, Any]:
    """Purely derive every compiler, linker, and qualification process argv.

    The two brace-delimited qualification values are sealed placeholders.  A
    worker may substitute only those two values at execution time; all other
    tokens are immutable and compared in exact order.
    """

    sources = [str(path) for path in linked_sources]
    objects = [str(path) for path in linked_objects]
    if not sources or len(sources) != len(objects):
        raise NativeAdapterError("sealed argv source/object closure is malformed")
    common = [
        str(compiler_path), "-std=c++17", "-O2", "-fno-fast-math",
        "-D__HIP_PLATFORM_AMD__", "-I",
        str(Path(pinned_source_root) / "shared/origami/include"),
        "-I", str(Path(rocm_root) / "include"), "-include",
        str(generated_header), "-c",
    ]
    return {
        "compile_argv": [
            [*common, source, "-o", output]
            for source, output in zip(sources, objects)
        ],
        "link_argv": [
            str(compiler_path), *objects, "-L", str(Path(rocm_root) / "lib"),
            "-lamdhip64", "-lstdc++", "-lm", "-o", str(helper_path),
        ],
        "qualification_argv": [
            str(qualification_python_path), str(qualification_worker_source_path),
            "--repository-root", str(qualification_repository_root),
            "--yaml", str(qualification_yaml_path),
            "--compiler", str(compiler_path),
            "--workspace-root", str(qualification_workspace_root),
        ],
    }


def materialize_sealed_qualification_argv(
    template: Sequence[str], *, pinned_source_root: Path | str,
    workspace_root: Path | str,
) -> list[str]:
    """Substitute exactly the two permitted runtime identities in a sealed argv."""

    if (
        type(template) is not list
        or template.count("{pinned_source_root}") != 1
        or template.count("{workspace_root}") != 1
        or any(type(token) is not str for token in template)
    ):
        raise NativeAdapterError("qualification argv template is malformed")
    substitutions = {
        "{pinned_source_root}": str(Path(pinned_source_root).resolve()),
        "{workspace_root}": str(Path(workspace_root).resolve()),
    }
    return [substitutions.get(token, token) for token in template]


def validate_native_build_provenance_document(document: Mapping[str, Any]) -> None:
    """Validate the complete on-disk provenance envelope and both hashes."""

    expected = {
        "document_kind", "schema_version", "checkpoint_id", "compiler_path",
        "compiler_sha256", "compiler_version", "helper_path", "helper_sha256",
        "build", "provenance_sha256",
    }
    if type(document) is not dict or set(document) != expected:
        raise NativeAdapterError("native build provenance envelope schema changed")
    outer = dict(document)
    recorded = outer.pop("provenance_sha256")
    if (
        document["document_kind"] != "s11_native_build_provenance"
        or document["schema_version"] != 1
        or document["checkpoint_id"] != "S11"
        or type(recorded) is not str
        or canonical_sha256(outer) != recorded
    ):
        raise NativeAdapterError("native build provenance envelope self-hash failure")
    build = document["build"]
    if type(build) is not dict:
        raise NativeAdapterError("native build provenance body is malformed")
    build_body = dict(build)
    build_hash = build_body.pop("build_sha256", None)
    if (
        build.get("document_kind") != "s11_native_build_execution"
        or build.get("schema_version") != 1
        or build.get("checkpoint_id") != "S11"
        or type(build_hash) is not str
        or canonical_sha256(build_body) != build_hash
    ):
        raise NativeAdapterError("native build execution provenance self-hash failure")


def build_native_formocast_helper(
    *,
    contract: Mapping[str, Any],
    pinned_materialization_root: Path | str,
    build_root: Path | str,
    compiler_path: Path | str,
    compiler_sha256: str,
    compiler_version: str,
    adapter_source_path: Path | str,
    adapter_source_sha256: str,
) -> dict[str, Any]:
    """Compile and link the real helper from exact pinned Origami sources."""

    from .contract import (
        PINNED_ORIGAMI_LINK_SOURCES,
        _approved_scratch_destination,
        verify_pinned_integration,
    )

    root = _approved_scratch_destination(build_root)
    provenance_path = root / "native-build-provenance.json"
    if provenance_path.exists():
        document = strict_load_json(provenance_path)
        validate_native_build_provenance_document(document)
        for row in (
            *document["build"]["generated_headers"],
            *document["build"]["linked_objects"],
            *document["build"]["linked_sources"],
        ):
            if sha256_file(row["path"]) != row["sha256"]:
                raise NativeAdapterError("sealed native build input/output drift")
        if sha256_file(document["helper_path"]) != document["helper_sha256"]:
            raise NativeAdapterError("sealed native helper drift")
        return document
    if root.exists() and any(root.iterdir()):
        raise NativeAdapterError("native build root is nonempty and unsealed")
    root.mkdir(parents=True, exist_ok=True)
    compiler = Path(compiler_path)
    bound_compiler = compiler.resolve()
    adapter_source = Path(adapter_source_path).resolve()
    if (
        not stat.S_ISREG(bound_compiler.lstat().st_mode)
        or bound_compiler.is_symlink()
        or sha256_file(bound_compiler) != compiler_sha256
        or adapter_source.is_symlink()
        or sha256_file(adapter_source) != adapter_source_sha256
    ):
        raise NativeAdapterError("native compiler/adapter source binding mismatch")
    version = subprocess.run(
        [str(compiler), "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
    )
    lines = version.stdout.decode("utf-8", errors="replace").splitlines()
    if version.returncode != 0 or not lines or lines[0] != compiler_version:
        raise NativeAdapterError("native compiler version binding mismatch")
    pinned = verify_pinned_integration(pinned_materialization_root, contract)
    source_root = Path(pinned["source_root"])
    origami_sources = [source_root / relative for relative in PINNED_ORIGAMI_LINK_SOURCES]
    generated_root = root / "generated"
    generated_root.mkdir()
    generated = generated_root / "s11_pinned_build.hpp"
    generated.write_text(
        "#pragma once\n#define S11_PINNED_DUCTILE_COMMIT \""
        + contract["source_pins"]["ductile_commit"]
        + "\"\n",
        encoding="ascii",
    )
    linked_sources = [adapter_source, *origami_sources]
    linked_objects = [root / f"native_{index:02d}.o" for index in range(len(linked_sources))]
    helper = root / "s11-native-formocast"
    rocm_root = next(
        (parent for parent in bound_compiler.parents if (parent / "include/hip/hip_runtime.h").is_file()),
        None,
    )
    if rocm_root is None:
        raise NativeAdapterError("compiler installation lacks the bound HIP headers")
    argv = derive_sealed_execution_argv(
        compiler_path=compiler, pinned_source_root=source_root, rocm_root=rocm_root,
        linked_sources=linked_sources, linked_objects=linked_objects,
        generated_header=generated, helper_path=helper,
        qualification_python_path="{qualification_python_path}",
        qualification_worker_source_path="{qualification_worker_source_path}",
        qualification_yaml_path="{qualification_yaml_path}",
    )
    compile_argv = argv["compile_argv"]
    link_argv = argv["link_argv"]
    environment = {"PATH": f"{compiler.parent}:/usr/bin:/bin", "LC_ALL": "C"}
    for argv in compile_argv:
        completed = subprocess.run(
            argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=environment
        )
        if completed.returncode != 0:
            raise NativeAdapterError(
                "pinned native compile failed: "
                + completed.stderr.decode("utf-8", errors="replace")[-1000:]
            )
    linked = subprocess.run(
        link_argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=environment
    )
    if linked.returncode != 0:
        raise NativeAdapterError(
            "pinned native link failed: " + linked.stderr.decode("utf-8", errors="replace")[-1000:]
        )
    build_body = {
        "document_kind": "s11_native_build_execution", "schema_version": 1,
        "checkpoint_id": "S11",
        "compile_argv": compile_argv,
        "link_argv": link_argv,
        "pinned_source_root": str(source_root),
        "pinned_source_manifest_sha256": pinned["manifest_file_sha256"],
        "generated_headers": [{"path": str(generated), "sha256": sha256_file(generated)}],
        "linked_objects": [
            {"path": str(path), "sha256": sha256_file(path)} for path in linked_objects
        ],
        "linked_sources": [
            {"path": str(path), "sha256": sha256_file(path)} for path in linked_sources
        ],
    }
    build = {**build_body, "build_sha256": canonical_sha256(build_body)}
    body = {
        "document_kind": "s11_native_build_provenance", "schema_version": 1,
        "checkpoint_id": "S11", "compiler_path": str(compiler),
        "compiler_sha256": compiler_sha256, "compiler_version": compiler_version,
        "helper_path": str(helper), "helper_sha256": sha256_file(helper), "build": build,
    }
    document = {**body, "provenance_sha256": canonical_sha256(body)}
    exclusive_write_json(provenance_path, document)
    validate_native_build_provenance_document(document)
    return document


class NativeFormocastAdapter:
    """Invoke a prebuilt, hash-pinned native runtime helper once per identity.

    The helper contract requires the real ProblemInfo/SizeMapping/
    predictedPerformance route and returns its compiled provenance.  A fake
    executable is useful only for synthetic tests and can never satisfy a
    production lock's executable/source hashes.
    """

    def __init__(
        self,
        executable: Path | str,
        *,
        executable_sha256: str,
        native_source_path: Path | str,
        native_source_sha256: str,
        ductile_commit: str,
        timeout_seconds: int,
        compiler_path: Path | str,
        compiler_sha256: str,
        compiler_version: str,
        build_provenance: Mapping[str, Any],
    ):
        self.executable = Path(executable)
        self.executable_sha256 = executable_sha256
        self.native_source_path = Path(native_source_path)
        self.native_source_sha256 = native_source_sha256
        self.ductile_commit = ductile_commit
        self.timeout_seconds = timeout_seconds
        self.compiler_path = Path(compiler_path)
        self.compiler_sha256 = compiler_sha256
        self.compiler_version = compiler_version
        self.build_provenance = dict(build_provenance)
        info = self.executable.lstat()
        if not stat.S_ISREG(info.st_mode) or self.executable.is_symlink():
            raise NativeAdapterError("native helper must be one ordinary non-symlink file")
        if not os.access(self.executable, os.X_OK):
            raise NativeAdapterError("native helper is not executable")
        if sha256_file(self.executable) != executable_sha256:
            raise NativeAdapterError("native helper executable hash mismatch")
        source_info = self.native_source_path.lstat()
        if (
            not stat.S_ISREG(source_info.st_mode)
            or self.native_source_path.is_symlink()
            or sha256_file(self.native_source_path) != native_source_sha256
        ):
            raise NativeAdapterError("native helper source hash/mode mismatch")
        if type(timeout_seconds) is not int or timeout_seconds <= 0:
            raise NativeAdapterError("native helper timeout must be positive")
        if (
            not stat.S_ISREG(self.compiler_path.resolve().lstat().st_mode)
            or self.compiler_path.resolve().is_symlink()
            or sha256_file(self.compiler_path.resolve()) != compiler_sha256
        ):
            raise NativeAdapterError("native compiler path/hash/mode mismatch")
        version = subprocess.run(
            [str(self.compiler_path), "--version"], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        )
        lines = version.stdout.decode("utf-8", errors="replace").splitlines()
        if version.returncode != 0 or not lines or lines[0] != compiler_version:
            raise NativeAdapterError("native compiler version mismatch")
        build_keys = {
            "document_kind", "schema_version", "checkpoint_id", "build_sha256",
            "compile_argv", "link_argv", "pinned_source_root",
            "pinned_source_manifest_sha256", "generated_headers", "linked_objects",
            "linked_sources",
        }
        if set(self.build_provenance) != build_keys:
            raise NativeAdapterError("native build provenance schema changed")
        build_body = dict(self.build_provenance)
        recorded_build_hash = build_body.pop("build_sha256")
        if (
            self.build_provenance["document_kind"] != "s11_native_build_execution"
            or self.build_provenance["schema_version"] != 1
            or self.build_provenance["checkpoint_id"] != "S11"
            or canonical_sha256(build_body) != recorded_build_hash
        ):
            raise NativeAdapterError("native build provenance self-hash failure")
        if self.build_provenance["link_argv"][-1] != str(self.executable):
            raise NativeAdapterError("native helper/build link output mismatch")
        for row in (
            *self.build_provenance["generated_headers"],
            *self.build_provenance["linked_objects"],
            *self.build_provenance["linked_sources"],
        ):
            if type(row) is not dict or set(row) != {"path", "sha256"} or sha256_file(row["path"]) != row["sha256"]:
                raise NativeAdapterError("native build input/object provenance drift")

    def score(
        self,
        *,
        semantic_identity: str,
        operational_solution: Mapping[str, Any],
        problem_sizes: Sequence[Sequence[int]],
        soo: bool,
        weight_beta: float,
    ) -> dict[str, Any]:
        if len(problem_sizes) != 3 or any(
            len(size) != 4 or any(type(value) is not int or value <= 0 for value in size)
            for size in problem_sizes
        ):
            raise NativeAdapterError("all locked exact sizes are required")
        if type(soo) is not bool or type(weight_beta) is not float or not math.isfinite(weight_beta):
            raise NativeAdapterError("locked reducer/weight_beta binding is invalid")
        request = {
            "protocol": "s11_native_formocast_v1",
            "semantic_identity": semantic_identity,
            "operational_solution": dict(operational_solution),
            "problem_sizes": [list(size) for size in problem_sizes],
            "soo": soo,
            "weight_beta": weight_beta,
            "required_native_path": ["ProblemInfo", "SizeMapping", "predictedPerformance"],
        }
        expected_mapping_keys = set(SCALAR_MAPPING_FIELDS) | {
            "macroTile",
            "matrixInstruction",
            "waveGroup",
        }
        if set(operational_solution) != expected_mapping_keys:
            raise NativeAdapterError("operational SizeMapping schema/unknown-property failure")
        if (
            type(operational_solution["macroTile"]) is not list
            or len(operational_solution["macroTile"]) != 3
            or type(operational_solution["matrixInstruction"]) is not list
            or len(operational_solution["matrixInstruction"]) != 4
            or type(operational_solution["waveGroup"]) is not list
            or len(operational_solution["waveGroup"]) != 2
        ):
            raise NativeAdapterError("operational SizeMapping vector width changed")
        serialized_scalars = []
        for field in SCALAR_MAPPING_FIELDS:
            value = operational_solution[field]
            if type(value) is bool:
                value = int(value)
            if type(value) is not int:
                raise NativeAdapterError(f"SizeMapping scalar is not integral: {field}")
            serialized_scalars.append(str(value))
        mapping_tokens = [
            str(operational_solution["waveNum"]),
            *(str(value) for value in operational_solution["macroTile"]),
            *(str(value) for value in operational_solution["matrixInstruction"]),
            *(str(operational_solution[field]) for field in SCALAR_MAPPING_FIELDS[1:]),
            *(str(value) for value in operational_solution["waveGroup"]),
        ]
        mapping_tokens = [
            "1" if token == "True" else "0" if token == "False" else token
            for token in mapping_tokens
        ]
        request_sha256 = canonical_sha256(request)
        input_lines = [
            f"S11_NATIVE_FORMOCAST_V1 {request_sha256} {semantic_identity} {len(problem_sizes)}",
            *(" ".join(str(value) for value in size) for size in problem_sizes),
            " ".join(mapping_tokens),
        ]
        completed = subprocess.run(
            [str(self.executable)],
            input=("\n".join(input_lines) + "\n").encode("ascii"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=self.timeout_seconds,
            env={"PATH": os.environ.get("PATH", "")},
        )
        if completed.returncode != 0:
            raise NativeAdapterError("native helper rejected or failed")
        try:
            response = strict_json_loads(completed.stdout)
        except Exception as error:
            raise NativeAdapterError("native helper response is not strict JSON") from error
        expected = {
            "protocol",
            "request_sha256",
            "semantic_identity",
            "latencies",
            "native_path_called",
        }
        if type(response) is not dict or set(response) != expected:
            raise NativeAdapterError("native helper output schema/unknown-property failure")
        provenance = {
            "native_path": ["ProblemInfo", "SizeMapping", "predictedPerformance"],
            "native_source_sha256": self.native_source_sha256,
            "ductile_commit": self.ductile_commit,
            "executable_sha256": self.executable_sha256,
            "proxy_or_substitution": False,
            "argv": [str(self.executable)],
            "timeout_seconds": self.timeout_seconds,
            "compiler_path": str(self.compiler_path),
            "compiler_sha256": self.compiler_sha256,
            "compiler_version": self.compiler_version,
            "build_provenance_sha256": canonical_sha256(self.build_provenance),
            "pinned_source_manifest_sha256": self.build_provenance["pinned_source_manifest_sha256"],
        }
        if (
            response["protocol"] != "s11_native_formocast_v1"
            or response["request_sha256"] != request_sha256
            or response["semantic_identity"] != semantic_identity
            or response["native_path_called"] is not True
        ):
            raise NativeAdapterError("native path/provenance/substitution guard failed")
        latencies = response["latencies"]
        if type(latencies) is not list or len(latencies) != len(problem_sizes):
            raise NativeAdapterError("native helper returned partial locked-size output")
        observed_sizes: list[list[int]] = []
        for expected_size, row in zip(problem_sizes, latencies):
            if type(row) is not dict or set(row) != {"problem_size", "predicted_latency"}:
                raise NativeAdapterError("native latency row schema changed")
            latency = row["predicted_latency"]
            if list(expected_size) != row["problem_size"]:
                raise NativeAdapterError("native latency size order/substitution changed")
            if type(latency) is not float or not math.isfinite(latency) or latency <= 0:
                raise NativeAdapterError("native latency must be finite and positive")
            observed_sizes.append(row["problem_size"])
        return {
            "semantic_identity": semantic_identity,
            "latencies": latencies,
            "problem_sizes": observed_sizes,
            "provenance": provenance,
            "response_sha256": canonical_sha256(response),
        }
