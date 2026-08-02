# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Build/bind the actual native Formocast and runtime queue adapter."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path
from typing import Any, Mapping

from .census import verify_pinned_source
from .contract import (
    S10R4Error,
    atomic_write_json,
    canonical_sha256,
    load_json,
    materialize_command_template,
    raw_sha256,
)


CMAKE_TEXT = """cmake_minimum_required(VERSION 3.25.2)
project(s10r4_native LANGUAGES CXX C ASM)
set(HIPBLASLT_ENABLE_FETCH OFF CACHE BOOL "" FORCE)
set(HIPBLASLT_ENABLE_DEVICE OFF CACHE BOOL "" FORCE)
set(HIPBLASLT_ENABLE_EXTOPS OFF CACHE BOOL "" FORCE)
set(HIPBLASLT_ENABLE_MATRIX_TRANSFORM OFF CACHE BOOL "" FORCE)
set(HIPBLASLT_ENABLE_CLIENT OFF CACHE BOOL "" FORCE)
set(HIPBLASLT_ENABLE_HOST OFF CACHE BOOL "" FORCE)
set(HIPBLASLT_BUNDLE_PYTHON_DEPS OFF CACHE BOOL "" FORCE)
set(HIPBLASLT_ENABLE_ROCROLLER OFF CACHE BOOL "" FORCE)
set(HIPBLASLT_ENABLE_MXDATAGENERATOR OFF CACHE BOOL "" FORCE)
set(TENSILELITE_ENABLE_HOST ON CACHE BOOL "" FORCE)
set(TENSILELITE_ENABLE_CLIENT ON CACHE BOOL "" FORCE)
set(TENSILELITE_BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
find_package(hip REQUIRED)
add_subdirectory("/src/rocm-libraries/agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame/artifacts/prelabel-build/pinned-source/projects/hipblaslt" hipblaslt)
add_executable(s10r4-native "/src/rocm-libraries/study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/native_formocast_runtime_adapter.cpp")
target_link_libraries(s10r4-native PRIVATE tensilelite::client-common)
set_target_properties(s10r4-native PROPERTIES CXX_STANDARD 20 CXX_STANDARD_REQUIRED ON CXX_EXTENSIONS OFF)
"""

FIXED_ENVIRONMENT = {
    "LC_ALL": "C",
    "PYTHONHASHSEED": "0",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
    "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
}


def _run_bound(argv: list[str], cwd: Path, stdout_path: Path, stderr_path: Path, timeout: int) -> None:
    if stdout_path.exists() or stderr_path.exists():
        raise S10R4Error(f"refusing to overwrite prior native build log: {stdout_path}")
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        try:
            completed = subprocess.run(
                argv,
                cwd=cwd,
                env=FIXED_ENVIRONMENT,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise S10R4Error(f"native build command timed out; preserved logs: {argv[0]}") from exc
    if completed.returncode != 0:
        raise S10R4Error(f"native build command failed with {completed.returncode}; no retry is permitted")


def _ordinary_product(path: Path) -> dict[str, Any]:
    info = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise S10R4Error(f"native product is not an unambiguous ordinary file: {path}")
    return {
        "path": path.resolve(strict=True).as_posix(),
        "mode": stat.S_IMODE(info.st_mode),
        "size_bytes": info.st_size,
        "sha256": raw_sha256(path),
    }


def _tool_product(path: Path) -> dict[str, Any]:
    requested = path.as_posix()
    resolved = path.resolve(strict=True)
    record = _ordinary_product(resolved)
    return {"requested_path": requested, "resolved_path": record.pop("path"), **record}


def build_native_products(build_root: Path, pinned_source: Path, adapter_source: Path) -> dict[str, Any]:
    verify_pinned_source(pinned_source)
    native_root = build_root / "native"
    source_root = native_root / "source"
    binary_root = native_root / "build"
    manifest_path = native_root / "s10r4-native-build.json"
    if manifest_path.exists():
        manifest = load_json(manifest_path)
        validate_native_build(manifest, build_root, pinned_source, adapter_source)
        return manifest
    if native_root.exists() and any(native_root.iterdir()):
        raise S10R4Error("BLOCKED_PLAN_GAP: partial native build exists and may not be cleaned or retried")
    source_root.mkdir(parents=True, exist_ok=False)
    binary_root.mkdir(parents=True, exist_ok=False)
    cmake_path = source_root / "CMakeLists.txt"
    descriptor = os.open(cmake_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(CMAKE_TEXT.encode("utf-8"))
        stream.flush()
        os.fsync(stream.fileno())
    configure_argv = materialize_command_template("native_configure")
    build_argv = materialize_command_template("native_build")
    logs = native_root / "logs"
    _run_bound(configure_argv, native_root, logs / "configure.stdout", logs / "configure.stderr", 3600)
    _run_bound(build_argv, native_root, logs / "build.stdout", logs / "build.stderr", 3600)
    products = [
        cmake_path,
        binary_root / "CMakeCache.txt",
        binary_root / "compile_commands.json",
        binary_root / "s10r4-native",
        binary_root / "hipblaslt/tensilelite/client/tensilelite-client",
    ]
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        "document_kind": "native_build",
        "native_executed": False,
        "pinned_source_root": pinned_source.resolve(strict=True).as_posix(),
        "adapter_source": _ordinary_product(adapter_source),
        "cmake_sha256": raw_sha256(cmake_path),
        "configure_argv": configure_argv,
        "build_argv": build_argv,
        "cwd": native_root.resolve(strict=True).as_posix(),
        "environment": FIXED_ENVIRONMENT,
        "products": [_ordinary_product(path) for path in products],
        "logs": [_ordinary_product(logs / name) for name in ("configure.stdout", "configure.stderr", "build.stdout", "build.stderr")],
        "compiler": _tool_product(Path("/opt/rocm/bin/amdclang++")),
        "cmake": _tool_product(Path("/opt/venv/bin/cmake")),
        "target_order": ["s10r4-native", "tensilelite-client"],
        "link_order": ["s10r4-native->tensilelite::client-common", "tensilelite-client->tensilelite-client-common"],
        "manifest_digest": "0" * 64,
    }
    manifest["manifest_digest"] = canonical_sha256(
        {key: value for key, value in manifest.items() if key != "manifest_digest"}
    )
    atomic_write_json(manifest_path, manifest)
    return manifest


def validate_native_build(manifest: Mapping[str, Any], build_root: Path, pinned_source: Path, adapter_source: Path) -> None:
    if manifest.get("document_kind") != "native_build" or manifest.get("native_executed") is not False:
        raise S10R4Error("native build manifest identity/execution state mismatch")
    if manifest.get("pinned_source_root") != pinned_source.resolve(strict=True).as_posix():
        raise S10R4Error("native build pinned source root mismatch")
    if manifest.get("adapter_source", {}).get("sha256") != raw_sha256(adapter_source):
        raise S10R4Error("native adapter source changed after build")
    for record in manifest.get("products", []):
        path = Path(record["path"])
        if _ordinary_product(path) != record:
            raise S10R4Error(f"native build product identity drift: {path}")
    if manifest.get("compiler") != _tool_product(Path("/opt/rocm/bin/amdclang++")):
        raise S10R4Error("native build compiler identity drift")
    if manifest.get("cmake") != _tool_product(Path("/opt/venv/bin/cmake")):
        raise S10R4Error("native build CMake identity drift")
    if manifest.get("configure_argv") != materialize_command_template("native_configure"):
        raise S10R4Error("native build configure argv drift")
    if manifest.get("build_argv") != materialize_command_template("native_build"):
        raise S10R4Error("native build argv drift")
    projection = {key: value for key, value in manifest.items() if key != "manifest_digest"}
    if canonical_sha256(projection) != manifest.get("manifest_digest"):
        raise S10R4Error("native build manifest digest mismatch")


def require_effective_lock(lock: Mapping[str, Any]) -> None:
    lifecycle = lock.get("lifecycle", {}).get("post_audit")
    if not isinstance(lifecycle, dict) or (
        lifecycle.get("lock_state"), lifecycle.get("execution_status"),
        lifecycle.get("checkpoint_state"), lifecycle.get("scientific_outcome"),
        lifecycle.get("edge"), lifecycle.get("formal_evidence_allowed"),
    ) != ("effective", "ready", "LOCKED_READY", "not_evaluated", None, True):
        raise S10R4Error("native execution requires a verified LOCKED_READY effective lock")


def run_native_fixture(
    *,
    lock: Mapping[str, Any],
    binary: Path,
    input_path: Path,
    output_path: Path,
    cwd: Path,
) -> dict[str, Any]:
    require_effective_lock(lock)
    argv = materialize_command_template(
        "native_fixture_execution",
        {
            "binary_path": binary.resolve(strict=True).as_posix(),
            "input_path": input_path.resolve(strict=True).as_posix(),
            "output_path": output_path.resolve(strict=False).as_posix(),
        },
    )
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=FIXED_ENVIRONMENT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=7200,
        check=False,
    )
    if completed.returncode != 0 or not output_path.is_file():
        raise S10R4Error("native fixture execution failed or did not produce its structured transcript")
    return load_json(output_path)
