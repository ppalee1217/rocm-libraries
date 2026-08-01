#!/usr/bin/env python3
# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Only CLI orchestrator for the sealed S10R3 bounded-cover entry protocol."""

from __future__ import annotations

import argparse
import copy
import csv
import fcntl
import functools
import hashlib
import inspect
import itertools
import json
import math
import os
import re
import resource
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

PROTOCOL_ROOT = Path(__file__).resolve().parent
ROOT = PROTOCOL_ROOT.parents[4]
if str(PROTOCOL_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOCOL_ROOT))

from s10r3.conformance import (  # noqa: E402
    assert_fault_rejected,
    compare_native_transcript,
    expected_native_transcript,
    materialize_fixture,
    validate_fixture,
    validate_pinned_guard_source,
)
from s10r3.contract import (  # noqa: E402
    ContractError,
    DEFAULT_LOCK_PATH,
    EXPECTED_CONTRACT_RAW_SHA256,
    FORMAL_OUTCOME_PATHS,
    NATIVE_BUILD_MANIFEST_PATH,
    REGISTRY_PATH,
    SENTINEL_FIXTURE_PATH,
    SIZE_REGISTRY_PATH,
    SOURCE_IDENTITIES,
    SUCCESSOR_FORMAL_SCOPES,
    SUCCESSOR_OUTCOME_PATHS,
    PRODUCTION_ADMISSION_LOCK_PATH,
    admission_lock_identity,
    atomic_write_json,
    build_effective_lock,
    canonical_sha256,
    file_record,
    load_contract,
    sha256_file,
    strict_load_json,
    strict_load_yaml,
    stable_admission_lock,
    validate_effective_lock,
    validate_document,
    verify_committed_effective_lock,
    validate_mapping_failure_batch,
    validate_mapping_worker_completion,
    execute_g2_transition,
    G2_LINEAGE_SELECTOR,
)
from s10r3.correctness import (  # noqa: E402
    anchor_hashes,
    validate_noise_cells,
    verify_correctness_cells,
)
from s10r3.ledger import RunLedger  # noqa: E402
from s10r3.mapping import (  # noqa: E402
    MAPPING_FAILURE_MARKER,
    MAPPING_FAILURE_RETURN_CODE,
    MAPPING_RESULT_MARKER,
    MappingError,
    SIZES,
    mapping_worker_code,
    run_mapping_batch,
    size_registry_document,
    verify_mapping_parity,
)
from s10r3.native_adapter import (  # noqa: E402
    NativeBinding,
    PinnedNativeFormocastRuntimeAdapter,
)
from s10r3.selector import Witness, deterministic_greedy_bounded_cover  # noqa: E402
from s10r3.state_machine import Stage, require_complete_unit  # noqa: E402
from s10r3.support import (  # noqa: E402
    CHUNK_SIZE,
    CONDITIONAL_CHUNKS,
    GLOBAL_CHUNKS,
    AtomRegistry,
    AxisSpec,
    SupportState,
    activate_conditional_targets,
    axis_specs_from_registry,
    classify_support,
    generate_discovery_chunk,
)


class RunnerError(ValueError):
    """An S10R3 CLI precondition, binding, or execution invariant failed."""


def _no_symlink_absolute(path: Path | str, *, label: str) -> Path:
    candidate = Path(path)
    absolute = Path(os.path.abspath(candidate))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if os.path.lexists(current) and current.is_symlink():
            raise RunnerError(f"{label} path contains symlink")
    return absolute


def _ordinary_file(path: Path | str, *, label: str) -> Path:
    absolute = _no_symlink_absolute(path, label=label)
    try:
        info = absolute.lstat()
    except OSError as error:
        raise RunnerError(f"{label} is absent") from error
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RunnerError(f"{label} is not one ordinary regular file")
    return absolute


def _ordinary_directory(
    path: Path | str, *, label: str, exact_parent: Path | None = None
) -> Path:
    absolute = _no_symlink_absolute(path, label=label)
    try:
        info = absolute.lstat()
    except OSError as error:
        raise RunnerError(f"{label} is absent") from error
    if not stat.S_ISDIR(info.st_mode):
        raise RunnerError(f"{label} is not one ordinary directory")
    if absolute.resolve() != absolute:
        raise RunnerError(f"{label} resolved identity drift")
    if exact_parent is not None and absolute.parent != exact_parent.resolve():
        raise RunnerError(f"{label} parent identity drift")
    return absolute


DUCTILE_COMMIT = "5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39"
GEKO_COMMIT = "d32abacfd13579d1f523f035b7a10b0734c4ac47"
ACTUAL_YAML = PROTOCOL_ROOT / "inputs/s10-generated.yaml"
NATIVE_SOURCE = PROTOCOL_ROOT / "s10r3/native_formocast_runtime_adapter.cpp"
NATIVE_HOST_ADAPTER = PROTOCOL_ROOT / "s10r3/native_adapter.py"

PRELABEL_BUILD_ROOT = ROOT / (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "prelabel-build"
)
PRELABEL_FIXTURE_ROOT = ROOT / (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "prelabel-fixtures"
)
PRELABEL_TEST_ROOT = ROOT / (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "prelabel-tests"
)
REGISTRY_MARKER = "S10R3_REGISTRY_PROBE="
VALIDATOR_MARKER = "S10R3_VALIDATOR_RESULT="
FORMAL_RUN_BASE = ROOT / "agent_run/260730-ductile-factorized-guidance-s10r3-restart"
FORMAL_CPU_ROOT = FORMAL_RUN_BASE / "artifacts/formal-cpu"
FORMAL_MAPPING_ROOT = FORMAL_RUN_BASE / "artifacts/formal-mapping"
FORMAL_NATIVE_ROOT = FORMAL_RUN_BASE / "artifacts/formal-native"
FORMAL_GPU_ROOT = FORMAL_RUN_BASE / "artifacts/formal-gpu"
REPRODUCTION_ROOT = FORMAL_RUN_BASE / "artifacts/reproduction"
SUPPORT_PATH = ROOT / FORMAL_OUTCOME_PATHS[0]
MAPPING_PATH = ROOT / FORMAL_OUTCOME_PATHS[1]
CORRECTNESS_PATH = ROOT / FORMAL_OUTCOME_PATHS[2]
NOISE_PATH = ROOT / FORMAL_OUTCOME_PATHS[3]
DECISION_PATH = ROOT / FORMAL_OUTCOME_PATHS[4]
GATE_RECORD_PATH = ROOT / FORMAL_OUTCOME_PATHS[5]
REPORT_PATH = ROOT / FORMAL_OUTCOME_PATHS[6]
SENTINEL_CONFORMANCE_PATH = (
    PROTOCOL_ROOT / "manifests/s10r3-sentinel-conformance.json"
)
FORMAL_ENVIRONMENT = {
    "LC_ALL": "C",
    "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
    "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
    "PYTHONHASHSEED": "0",
}


def _exact_path(path: Path | str, expected: Path | str, *, label: str) -> Path:
    actual = (ROOT / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    target = (ROOT / expected).resolve() if not Path(expected).is_absolute() else Path(expected).resolve()
    if actual != target:
        raise RunnerError(f"{label} must be the exact predeclared path")
    if actual == ROOT or ROOT not in actual.parents:
        raise RunnerError(f"{label} escapes the repository")
    return actual


def _git(*arguments: str, text: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT}", *arguments],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    )
    if completed.returncode:
        raise RunnerError(
            "Git identity command failed: "
            + (
                completed.stderr[-2000:]
                if text
                else completed.stderr.decode("utf-8", errors="replace")[-2000:]
            )
        )
    return completed.stdout


def _atomic_write_bytes(path: Path, payload: bytes, *, exclusive: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive and path.exists():
        raise RunnerError(f"exclusive artifact already exists: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            try:
                os.link(temporary, path)
            except FileExistsError as error:
                raise RunnerError(f"exclusive artifact already exists: {path}") from error
            temporary.unlink()
        else:
            os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def _assert_prelabel_absence() -> None:
    # A46.2 formal CPU/mapping and support classification are protected
    # predecessor sources until Main retires them. Prelabel code must not read,
    # enumerate, or reject those paths; only G2/later outputs must be absent.
    for relative in SUCCESSOR_OUTCOME_PATHS:
        if (ROOT / relative).exists():
            raise RunnerError(f"formal outcome path exists before labels: {relative}")
    sentinel_result = (
        PROTOCOL_ROOT / "manifests/s10r3-sentinel-conformance.json"
    )
    blocker = PROTOCOL_ROOT / "evidence/s10r3-operational-blocker.json"
    for path in (sentinel_result, blocker):
        if path.exists():
            raise RunnerError(f"forbidden pre-label durable path exists: {path}")
    for relative in SUCCESSOR_FORMAL_SCOPES:
        if (ROOT / relative).exists():
            raise RunnerError(f"formal artifact scope exists before labels: {relative}")


def validate_contract_command() -> dict[str, Any]:
    contract = load_contract()
    _assert_prelabel_absence()
    return {
        "checkpoint_id": "S10R3",
        "contract_id": contract["contract_id"],
        "formal_evidence": False,
        "status": "PHASE1_CONTRACT_VALID",
    }


def _materialize_pinned_source(output: Path) -> dict[str, Any]:
    if output.exists():
        raise RunnerError("pinned source root must be absent")
    output.mkdir(parents=True)
    archive_command = [
        "git",
        "-c",
        f"safe.directory={ROOT}",
        "archive",
        "--format=tar",
        DUCTILE_COMMIT,
        "projects/hipblaslt",
        "shared/origami",
        "cmake",
        "CMakeLists.txt",
    ]
    archive = subprocess.Popen(
        archive_command,
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if archive.stdout is None:
        raise RunnerError("cannot open pinned source archive stream")
    with tarfile.open(fileobj=archive.stdout, mode="r|") as stream:
        for member in stream:
            relative = Path(member.name)
            if relative.is_absolute() or ".." in relative.parts:
                raise RunnerError(f"unsafe archive member: {member.name}")
            destination = output / relative
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                payload = stream.extractfile(member)
                if payload is None:
                    raise RunnerError(f"cannot read archive member: {member.name}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                _atomic_write_bytes(destination, payload.read())
                os.chmod(destination, member.mode & 0o777)
            elif member.issym():
                target = Path(member.linkname)
                resolved = (destination.parent / target).resolve()
                if output.resolve() not in resolved.parents:
                    raise RunnerError(f"unsafe archive symlink: {member.name}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(member.linkname, destination)
            else:
                raise RunnerError(f"unsupported archive entry: {member.name}")
    stderr = b"" if archive.stderr is None else archive.stderr.read()
    returncode = archive.wait()
    if returncode:
        raise RunnerError(
            "git archive failed: " + stderr.decode("utf-8", errors="replace")[-2000:]
        )
    identities = {
        "formocast_source_blob": str(
            _git(
                "rev-parse",
                f"{DUCTILE_COMMIT}:shared/origami/src/simulator/tensilelite/"
                "formocast_simulator.cpp",
                text=True,
            )
        ).strip(),
        "formocast_header_blob": str(
            _git(
                "rev-parse",
                f"{DUCTILE_COMMIT}:shared/origami/include/origami/simulator/"
                "tensilelite/formocast_simulator.hpp",
                text=True,
            )
        ).strip(),
        "runtime_source_blob": str(
            _git(
                "rev-parse",
                f"{DUCTILE_COMMIT}:projects/hipblaslt/tensilelite/client/src/"
                "SolutionIterator.cpp",
                text=True,
            )
        ).strip(),
        "runtime_header_blob": str(
            _git(
                "rev-parse",
                f"{DUCTILE_COMMIT}:projects/hipblaslt/tensilelite/client/include/"
                "SolutionIterator.hpp",
                text=True,
            )
        ).strip(),
        "candidate_construction_blob": str(
            _git(
                "rev-parse",
                f"{DUCTILE_COMMIT}:projects/hipblaslt/tensilelite/Tensile/"
                "BenchmarkStructs.py",
                text=True,
            )
        ).strip(),
    }
    expected = {
        "formocast_source_blob": SOURCE_IDENTITIES["native_formocast_source_blob"][1],
        "formocast_header_blob": SOURCE_IDENTITIES["native_formocast_header_blob"][1],
        "runtime_source_blob": SOURCE_IDENTITIES["runtime_queue_source_blob"][1],
        "runtime_header_blob": SOURCE_IDENTITIES["runtime_queue_header_blob"][1],
        "candidate_construction_blob": SOURCE_IDENTITIES[
            "candidate_construction_blob"
        ][1],
    }
    if identities != expected:
        raise RunnerError("pinned materialized source identity mismatch")
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "commit": DUCTILE_COMMIT,
        "root": str(output.relative_to(ROOT)),
        "source_identities": identities,
        "outcome_blind": True,
        "formal_evidence": False,
    }
    body["manifest_digest"] = canonical_sha256(body)
    atomic_write_json(output / "s10r3-materialization.json", body, exclusive=True)
    return body


def _native_cmake_source(integration: Path) -> bytes:
    return (
        "cmake_minimum_required(VERSION 3.25.2)\n"
        "project(s10r3_native LANGUAGES CXX C ASM)\n"
        'set(HIPBLASLT_ENABLE_FETCH OFF CACHE BOOL "" FORCE)\n'
        'set(HIPBLASLT_ENABLE_DEVICE OFF CACHE BOOL "" FORCE)\n'
        'set(HIPBLASLT_ENABLE_EXTOPS OFF CACHE BOOL "" FORCE)\n'
        'set(HIPBLASLT_ENABLE_MATRIX_TRANSFORM OFF CACHE BOOL "" FORCE)\n'
        'set(HIPBLASLT_ENABLE_CLIENT OFF CACHE BOOL "" FORCE)\n'
        'set(HIPBLASLT_ENABLE_HOST OFF CACHE BOOL "" FORCE)\n'
        'set(HIPBLASLT_BUNDLE_PYTHON_DEPS OFF CACHE BOOL "" FORCE)\n'
        'set(HIPBLASLT_ENABLE_ROCROLLER OFF CACHE BOOL "" FORCE)\n'
        'set(HIPBLASLT_ENABLE_MXDATAGENERATOR OFF CACHE BOOL "" FORCE)\n'
        'set(TENSILELITE_ENABLE_HOST ON CACHE BOOL "" FORCE)\n'
        'set(TENSILELITE_ENABLE_CLIENT ON CACHE BOOL "" FORCE)\n'
        'set(TENSILELITE_BUILD_TESTING OFF CACHE BOOL "" FORCE)\n'
        'set(BUILD_TESTING OFF CACHE BOOL "" FORCE)\n'
        "find_package(hip REQUIRED)\n"
        f'add_subdirectory("{integration / "projects/hipblaslt"}" hipblaslt)\n'
        f'add_executable(s10r3-native "{NATIVE_SOURCE}")\n'
        "target_link_libraries(s10r3-native PRIVATE tensilelite::client-common)\n"
        "set_target_properties(s10r3-native PROPERTIES CXX_STANDARD 20 "
        "CXX_STANDARD_REQUIRED ON CXX_EXTENSIONS OFF)\n"
    ).encode("utf-8")


def _build_native_helper(
    *,
    integration: Path,
    build_root: Path,
    materialization: Mapping[str, Any],
) -> dict[str, Any]:
    native_root = build_root / "native"
    source_root = native_root / "source"
    binary_root = native_root / "build"
    log_root = native_root / "logs"
    resume_failed_build = native_root.exists()
    source_root.mkdir(parents=True, exist_ok=resume_failed_build)
    log_root.mkdir(parents=True, exist_ok=resume_failed_build)
    cmake_path = source_root / "CMakeLists.txt"
    expected_cmake = _native_cmake_source(integration)
    if resume_failed_build:
        required_partial = (
            cmake_path,
            binary_root / "CMakeCache.txt",
            log_root / "configure.stdout",
            log_root / "configure.stderr",
            log_root / "build.stdout",
            log_root / "build.stderr",
        )
        if not all(path.is_file() and not path.is_symlink() for path in required_partial):
            raise RunnerError("partial native build is not the exact resumable state")
        if cmake_path.read_bytes() != expected_cmake:
            raise RunnerError("partial native CMake input changed before resume")
        if (binary_root / "s10r3-native").exists() or (
            native_root / "s10r3-native-build.json"
        ).exists():
            raise RunnerError("completed native output cannot enter build resume")
    else:
        _atomic_write_bytes(cmake_path, expected_cmake)
    configure = [
        "/opt/venv/bin/cmake",
        "-S",
        str(source_root),
        "-B",
        str(binary_root),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_CXX_COMPILER=/opt/rocm/bin/amdclang++",
    ]
    build = [
        "/opt/venv/bin/cmake",
        "--build",
        str(binary_root),
        "--target",
        "s10r3-native",
        "--parallel",
        "16",
    ]
    records = []
    started = time.monotonic()
    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    environment = {
        "LC_ALL": "C",
        "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
        "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
    }
    if resume_failed_build:
        records.extend(
            [
                {
                    "id": "configure",
                    "argv": configure,
                    "cwd": str(native_root.relative_to(ROOT)),
                    "environment": environment,
                    "exit_status": 0,
                    "stdout_path": str(
                        (log_root / "configure.stdout").relative_to(ROOT)
                    ),
                    "stdout_sha256": sha256_file(log_root / "configure.stdout"),
                    "stderr_path": str(
                        (log_root / "configure.stderr").relative_to(ROOT)
                    ),
                    "stderr_sha256": sha256_file(log_root / "configure.stderr"),
                },
                {
                    "id": "build-initial",
                    "argv": build,
                    "cwd": str(native_root.relative_to(ROOT)),
                    "environment": environment,
                    "exit_status": 2,
                    "stdout_path": str((log_root / "build.stdout").relative_to(ROOT)),
                    "stdout_sha256": sha256_file(log_root / "build.stdout"),
                    "stderr_path": str((log_root / "build.stderr").relative_to(ROOT)),
                    "stderr_sha256": sha256_file(log_root / "build.stderr"),
                    "preserved_failed_attempt": True,
                },
            ]
        )
        retry_index = 1
        while (log_root / f"build-retry-{retry_index:02d}.stdout").exists():
            retry_stdout = log_root / f"build-retry-{retry_index:02d}.stdout"
            retry_stderr = log_root / f"build-retry-{retry_index:02d}.stderr"
            if not retry_stderr.is_file():
                raise RunnerError("partial native retry log pair is incomplete")
            records.append(
                {
                    "id": f"build-retry-{retry_index:02d}",
                    "argv": build,
                    "cwd": str(native_root.relative_to(ROOT)),
                    "environment": environment,
                    "exit_status": 2,
                    "stdout_path": str(retry_stdout.relative_to(ROOT)),
                    "stdout_sha256": sha256_file(retry_stdout),
                    "stderr_path": str(retry_stderr.relative_to(ROOT)),
                    "stderr_sha256": sha256_file(retry_stderr),
                    "preserved_failed_attempt": True,
                }
            )
            retry_index += 1
        commands = ((f"build-retry-{retry_index:02d}", build),)
    else:
        commands = (("configure", configure), ("build", build))
    for command_id, argv in commands:
        completed = subprocess.run(
            argv,
            cwd=native_root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=3600,
        )
        stdout_path = log_root / f"{command_id}.stdout"
        stderr_path = log_root / f"{command_id}.stderr"
        _atomic_write_bytes(stdout_path, completed.stdout)
        _atomic_write_bytes(stderr_path, completed.stderr)
        records.append(
            {
                "id": command_id,
                "argv": argv,
                "cwd": str(native_root.relative_to(ROOT)),
                "environment": environment,
                "exit_status": completed.returncode,
                "stdout_path": str(stdout_path.relative_to(ROOT)),
                "stdout_sha256": sha256_file(stdout_path),
                "stderr_path": str(stderr_path.relative_to(ROOT)),
                "stderr_sha256": sha256_file(stderr_path),
            }
        )
        if completed.returncode:
            raise RunnerError(
                f"native helper {command_id} failed: "
                + completed.stderr.decode("utf-8", errors="replace")[-3000:]
            )
    binary = binary_root / "s10r3-native"
    if not binary.is_file() or binary.is_symlink():
        raise RunnerError("native build did not produce one regular helper binary")
    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "outcome_blind": True,
        "formal_evidence": False,
        "native_executed": False,
        "integration_manifest_digest": materialization["manifest_digest"],
        "source_identities": materialization["source_identities"],
        "cpp_source": file_record(NATIVE_SOURCE),
        "host_adapter": file_record(NATIVE_HOST_ADAPTER),
        "cmake_path": str(cmake_path.relative_to(ROOT)),
        "cmake_sha256": sha256_file(cmake_path),
        "binary_path": str(binary.relative_to(ROOT)),
        "binary_sha256": sha256_file(binary),
        "toolchain": {
            "cmake_path": "/opt/venv/bin/cmake",
            "cmake_sha256": sha256_file("/opt/venv/bin/cmake"),
            "cxx_path": "/opt/rocm/bin/amdclang++",
            "cxx_sha256": sha256_file("/opt/rocm/bin/amdclang++"),
            "build_type": "Release",
            "cxx_standard": 20,
            "link_target": "tensilelite::client-common",
        },
        "commands": records,
        "resource_measurement": {
            "wall_s": time.monotonic() - started,
            "cpu_s": (
                usage_after.ru_utime
                + usage_after.ru_stime
                - usage_before.ru_utime
                - usage_before.ru_stime
            ),
            "maximum_child_rss_kib": usage_after.ru_maxrss,
        },
    }
    body["build_manifest_digest"] = canonical_sha256(body)
    atomic_write_json(
        native_root / "s10r3-native-build.json", body, exclusive=True
    )
    return body


def _registry_probe_code() -> str:
    return r'''
import copy
import hashlib
import itertools
import json
import sys

import numpy as np
from Tensile import BenchmarkStructs, LibraryIO
from Tensile.BenchmarkStructs import BenchmarkProcess
from Tensile.ductile import config as ductile_config
from Tensile.ductile.algorithm import GeneticAlgorithm
from Tensile.ductile.core import SearchSpace, Selection, Crossover, Mutation, Mating, Survival

MARKER = "S10R3_REGISTRY_PROBE="

def plain(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return plain(value.item())
    raise TypeError("unsupported S10R3 probe type: " + type(value).__name__)

yaml_path = sys.argv[1]
document = LibraryIO.read(yaml_path)
benchmark_problem = document["BenchmarkProblems"][0]
process = BenchmarkProcess(benchmark_problem[0], benchmark_problem[1], False)
step = process[0]
fork = copy.deepcopy(step.forkParams)
constant = copy.deepcopy(step.constantParams)
for group_index, group in enumerate(step.paramGroups):
    if len(group) == 1:
        constant.update(group[0])
    else:
        fork["group_" + str(group_index)] = group
space = SearchSpace(fork, valid=lambda _: True, max_iters=250)

merged = ductile_config.update(document["Backend"]["Config"])
selection = Selection.get(**ductile_config.populate(merged, "selection"))
crossover = Crossover.get(**ductile_config.populate(merged, "crossover"))
mutation = Mutation(space, **merged["mutation"])
mating = Mating(
    space=space,
    selection=selection,
    crossover=crossover,
    mutation=mutation,
    max_iters=merged["max_iters"],
)
survival = Survival.get(**ductile_config.populate(merged, "survival"))
ga = GeneticAlgorithm(
    space,
    mating,
    evaluate=lambda _: np.ones((1, 1)),
    survival=survival,
    pop_size=merged["pop_size"],
    n_gen=merged["n_gen"],
    soo=merged["soo"],
    period=merged["period"],
    tol=merged["tol"],
    div_thr=merged["div_thr"],
    seed=merged["seed"],
    verbose=0,
    log_file=None,
    checkpoint_path=None,
    weights=merged["weights"],
    weight_beta=merged["weight_beta"],
)

fork_records = benchmark_problem[1]["ForkParameters"]
raw_axis = {}
groups_record_index = None
raw_groups = None
for raw_index, record in enumerate(fork_records):
    if not isinstance(record, dict) or len(record) != 1:
        raise ValueError("ForkParameters record must be a singleton object")
    name, values = next(iter(record.items()))
    if name == "Groups":
        groups_record_index = raw_index
        raw_groups = values
    else:
        raw_axis[name] = (raw_index, values)
if groups_record_index is None or raw_groups is None:
    raise ValueError("Groups record is absent")

group_derivations = []
for group_index, raw_entries in enumerate(raw_groups):
    expanded = []
    derivations = []
    pointers = []
    for raw_entry_index, raw_entry in enumerate(raw_entries):
        names = list(raw_entry)
        options = [
            BenchmarkStructs._groupedParameterValueOptions(name, raw_entry[name])
            for name in names
        ]
        for option_indices in itertools.product(
            *(range(len(values)) for values in options)
        ):
            expanded.append(
                {
                    name: copy.deepcopy(options[field_index][choice_index])
                    for field_index, (name, choice_index) in enumerate(
                        zip(names, option_indices)
                    )
                }
            )
            derivations.append(
                [group_index, raw_entry_index, *[int(value) for value in option_indices]]
            )
            pointers.append(
                "/BenchmarkProblems/0/1/ForkParameters/"
                + str(groups_record_index)
                + "/Groups/"
                + str(group_index)
                + "/"
                + str(raw_entry_index)
            )
    if plain(expanded) != plain(step.paramGroups[group_index]):
        raise ValueError("fresh grouped expansion differs from BenchmarkProcess")
    group_derivations.append((expanded, derivations, pointers))

axes = []
for axis_index, (axis_name, candidates) in enumerate(space.map.items()):
    if axis_name.startswith("group_"):
        group_index = int(axis_name.split("_", 1)[1])
        expanded, derivations, pointers = group_derivations[group_index]
        if plain(candidates) != plain(expanded):
            raise ValueError("SearchSpace grouped candidates differ from expansion")
        yaml_pointer = (
            "/BenchmarkProblems/0/1/ForkParameters/"
            + str(groups_record_index)
            + "/Groups/"
            + str(group_index)
        )
        grouped = True
    else:
        raw_index, raw_candidates = raw_axis[axis_name]
        if plain(candidates) != plain(raw_candidates):
            raise ValueError("SearchSpace candidates differ from actual YAML")
        yaml_pointer = (
            "/BenchmarkProblems/0/1/ForkParameters/"
            + str(raw_index)
            + "/"
            + axis_name
        )
        pointers = [
            yaml_pointer + "/" + str(value_index)
            for value_index in range(len(candidates))
        ]
        derivations = [[] for _ in candidates]
        grouped = False
    weighted = axis_name in ga.probs
    probabilities = None
    probabilities_raw_sha256 = None
    if weighted:
        array = np.asarray(ga.probs[axis_name], dtype=np.float32)
        if array.shape != (len(candidates),):
            raise ValueError("weighted probability cardinality mismatch")
        probabilities = plain(array)
        probabilities_raw_sha256 = hashlib.sha256(
            array.tobytes(order="C")
        ).hexdigest()
    axes.append(
        {
            "axis_index": axis_index,
            "axis_name": axis_name,
            "values": plain(candidates),
            "grouped": grouped,
            "frozen_free": True,
            "currently_weighted": weighted,
            "yaml_pointer": yaml_pointer,
            "value_yaml_pointers": pointers,
            "derivation_indices_by_value": derivations,
            "probabilities": probabilities,
            "probabilities_raw_sha256": probabilities_raw_sha256,
        }
    )
result = {
    "schema_version": 1,
    "document_sha256": hashlib.sha256(open(yaml_path, "rb").read()).hexdigest(),
    "axis_count": len(axes),
    "axis_order": [axis["axis_name"] for axis in axes],
    "axes": axes,
    "expanded_group_cardinalities": [len(group) for group in step.paramGroups],
    "weighted_axes": list(ga.probs),
    "weight_beta": merged["weight_beta"],
}
print(MARKER + json.dumps(result, sort_keys=True, separators=(",", ":")))
'''


def _build_candidate_registry(
    *, integration: Path, output: Path, scratch: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    if output.exists():
        raise RunnerError("candidate registry output must be absent")
    scratch.mkdir(parents=True)
    environment = {
        "PYTHONPATH": str(integration / "projects/hipblaslt/tensilelite"),
        "PATH": "/opt/rocm/bin:/usr/bin:/bin",
        "LC_ALL": "C",
    }
    completed = subprocess.run(
        ["/opt/venv/bin/python3", "-c", _registry_probe_code(), str(ACTUAL_YAML)],
        cwd=integration,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1800,
        check=False,
    )
    stdout_path = scratch / "registry-probe.stdout"
    stderr_path = scratch / "registry-probe.stderr"
    _atomic_write_bytes(stdout_path, completed.stdout)
    _atomic_write_bytes(stderr_path, completed.stderr)
    if completed.returncode:
        raise RunnerError(
            "pinned registry probe failed: "
            + completed.stderr.decode("utf-8", errors="replace")[-3000:]
        )
    marked = [
        line[len(REGISTRY_MARKER) :]
        for line in completed.stdout.decode("utf-8", errors="replace").splitlines()
        if line.startswith(REGISTRY_MARKER)
    ]
    if len(marked) != 1:
        raise RunnerError("pinned registry probe emitted an invalid record count")
    probe = json.loads(marked[0])
    if (
        probe.get("axis_count") != 30
        or probe.get("document_sha256") != sha256_file(ACTUAL_YAML)
        or probe.get("expanded_group_cardinalities") != [9918, 3, 2]
        or probe.get("weight_beta") != 0.25
    ):
        raise RunnerError("pinned registry probe fixed identity mismatch")
    axes = [
        AxisSpec(
            axis_index=item["axis_index"],
            axis_name=item["axis_name"],
            values=tuple(item["values"]),
            grouped=item["grouped"],
            frozen_free=item["frozen_free"],
            currently_weighted=item["currently_weighted"],
            yaml_pointer=item["yaml_pointer"],
            value_yaml_pointers=tuple(item["value_yaml_pointers"]),
            derivation_indices_by_value=tuple(
                tuple(row) for row in item["derivation_indices_by_value"]
            ),
            probabilities=(
                tuple(item["probabilities"]) if item["currently_weighted"] else ()
            ),
            probabilities_raw_sha256=item["probabilities_raw_sha256"],
        )
        for item in probe["axes"]
    ]
    registry = AtomRegistry(axes).document()
    if registry["axis_order"] != probe["axis_order"]:
        raise RunnerError("candidate registry axis order drift")
    registry["pinned_identity_digests"] = {
        "ordered_axes_and_candidate_order": SOURCE_IDENTITIES[
            "ordered_axes_and_candidate_order"
        ][1],
        "expanded_groups": SOURCE_IDENTITIES["expanded_groups"][1],
        "search_space_map": SOURCE_IDENTITIES["search_space_map"][1],
        "baseline_weights": SOURCE_IDENTITIES["baseline_weights"][1],
    }
    # The registry digest covers the added pinned-identity projection too.
    old_digest = registry.pop("registry_digest")
    registry["registry_digest"] = canonical_sha256(registry)
    atomic_write_json(output, registry, exclusive=True)
    measurement = {
        "command_sha256": canonical_sha256(_registry_probe_code()),
        "stdout_sha256": sha256_file(stdout_path),
        "stderr_sha256": sha256_file(stderr_path),
        "exit_status": completed.returncode,
        "axis_count": registry["axis_count"],
        "row_count": registry["row_count"],
        "pre_identity_registry_digest": old_digest,
        "registry_digest": registry["registry_digest"],
    }
    return registry, measurement


def _verify_registry(document: Mapping[str, Any]) -> AtomRegistry:
    if document.get("pinned_identity_digests") != {
        "ordered_axes_and_candidate_order": SOURCE_IDENTITIES[
            "ordered_axes_and_candidate_order"
        ][1],
        "expanded_groups": SOURCE_IDENTITIES["expanded_groups"][1],
        "search_space_map": SOURCE_IDENTITIES["search_space_map"][1],
        "baseline_weights": SOURCE_IDENTITIES["baseline_weights"][1],
    }:
        raise RunnerError("candidate registry pinned identity digest drift")
    core = dict(document)
    digest = core.pop("registry_digest", None)
    if digest != canonical_sha256(core):
        raise RunnerError("candidate registry digest mismatch")
    core.pop("pinned_identity_digests")
    # Reconstruct the digest shape produced by AtomRegistry before the pinned projection.
    core["registry_digest"] = canonical_sha256(core)
    axes = axis_specs_from_registry(core)
    registry = AtomRegistry(axes)
    rebuilt = registry.document()
    if rebuilt != core:
        raise RunnerError("candidate registry exact typed round-trip failed")
    return registry


def _write_size_registry(path: Path) -> dict[str, Any]:
    if path.exists():
        raise RunnerError("size registry output must be absent")
    document = size_registry_document()
    atomic_write_json(path, document, exclusive=True)
    return document


def _critical_prelabel_manifest(
    *,
    build_root: Path,
    fixture_root: Path,
    materialization: Mapping[str, Any],
    native: Mapping[str, Any],
    registry: Mapping[str, Any],
    size_registry: Mapping[str, Any],
    registry_measurement: Mapping[str, Any],
    exclusive: bool = True,
) -> dict[str, Any]:
    fixture_path = fixture_root / "s10r3-sentinel-fixture.json"
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "formal_evidence": False,
        "native_executed": False,
        "source_commit": DUCTILE_COMMIT,
        "materialization_manifest_digest": materialization["manifest_digest"],
        "native_build_manifest_digest": native["build_manifest_digest"],
        "native_binary_sha256": native["binary_sha256"],
        "candidate_registry_digest": registry["registry_digest"],
        "size_registry_digest": size_registry["registry_digest"],
        "fixture_digest": strict_load_json(fixture_path)["fixture_digest"],
        "registry_probe": dict(registry_measurement),
        "critical_files": [
            file_record(REGISTRY_PATH),
            file_record(SIZE_REGISTRY_PATH),
            file_record(fixture_path),
            file_record(build_root / "native/s10r3-native-build.json"),
            file_record(build_root / "native/build/s10r3-native"),
            file_record(build_root / "pinned-source/s10r3-materialization.json"),
        ],
    }
    body["manifest_digest"] = canonical_sha256(body)
    atomic_write_json(
        build_root / "s10r3-prelabel-materialization.json",
        body,
        exclusive=exclusive,
    )
    return body


def _refresh_complete_prelabel_bindings(
    *,
    build: Path,
    fixtures: Path,
    registry_path: Path,
    size_registry_path: Path,
) -> dict[str, Any]:
    _assert_prelabel_descendants(build, fixtures)
    materialization = strict_load_json(
        build / "pinned-source/s10r3-materialization.json"
    )
    materialization_body = dict(materialization)
    materialization_digest = materialization_body.pop("manifest_digest", None)
    if (
        materialization_digest != canonical_sha256(materialization_body)
        or materialization.get("commit") != DUCTILE_COMMIT
    ):
        raise RunnerError("completed materialization cannot be refreshed")
    native_path = build / "native/s10r3-native-build.json"
    native = strict_load_json(native_path)
    native_body = dict(native)
    recorded_native = native_body.pop("build_manifest_digest", None)
    if (
        recorded_native != canonical_sha256(native_body)
        or native.get("native_executed") is not False
    ):
        raise RunnerError("completed native manifest cannot be refreshed")
    binary = build / "native/build/s10r3-native"
    if (
        not binary.is_file()
        or binary.is_symlink()
        or native["binary_path"] != str(binary.relative_to(ROOT))
        or native["binary_sha256"] != sha256_file(binary)
    ):
        raise RunnerError("completed native binary binding drift")
    native["cpp_source"] = file_record(NATIVE_SOURCE)
    native["host_adapter"] = file_record(NATIVE_HOST_ADAPTER)
    native["binary_sha256"] = sha256_file(binary)
    native["build_manifest_digest"] = canonical_sha256(
        {
            key: value
            for key, value in native.items()
            if key != "build_manifest_digest"
        }
    )
    atomic_write_json(native_path, native, exclusive=False)
    registry = strict_load_json(registry_path)
    _verify_registry(registry)
    size_registry = strict_load_json(size_registry_path)
    if size_registry != size_registry_document():
        raise RunnerError("size registry cannot be refreshed")
    fixture_path = fixtures / "s10r3-sentinel-fixture.json"
    fixture = strict_load_json(fixture_path)
    validate_fixture(fixture)
    source_blob = str(
        _git(
            "rev-parse",
            f"{DUCTILE_COMMIT}:shared/origami/src/simulator/tensilelite/"
            "formocast_simulator.cpp",
            text=True,
        )
    ).strip()
    source = _git(
        "show",
        f"{DUCTILE_COMMIT}:shared/origami/src/simulator/tensilelite/"
        "formocast_simulator.cpp",
        text=True,
    )
    validate_pinned_guard_source(source, source_blob=source_blob, fixture=fixture)
    old_critical = strict_load_json(
        build / "s10r3-prelabel-materialization.json"
    )
    critical = _critical_prelabel_manifest(
        build_root=build,
        fixture_root=fixtures,
        materialization=materialization,
        native=native,
        registry=registry,
        size_registry=size_registry,
        registry_measurement=old_critical["registry_probe"],
        exclusive=False,
    )
    return {
        "checkpoint_id": "S10R3",
        "formal_evidence": False,
        "native_executed": False,
        "status": "PRELABEL_PREPARED",
        "manifest_digest": critical["manifest_digest"],
        "binding_refresh": True,
    }


def prepare_prelabel(
    *,
    build_root: Path | str,
    fixture_root: Path | str,
    registry_path: Path | str,
    size_registry_path: Path | str,
) -> dict[str, Any]:
    _assert_prelabel_absence()
    build = _exact_path(build_root, PRELABEL_BUILD_ROOT, label="build root")
    fixtures = _exact_path(fixture_root, PRELABEL_FIXTURE_ROOT, label="fixture root")
    registry = _exact_path(registry_path, ROOT / REGISTRY_PATH, label="registry")
    size_registry = _exact_path(
        size_registry_path, ROOT / SIZE_REGISTRY_PATH, label="size registry"
    )
    completed_refresh = (
        (build / "s10r3-prelabel-materialization.json").is_file()
        and (build / "native/s10r3-native-build.json").is_file()
        and (fixtures / "s10r3-sentinel-fixture.json").is_file()
        and registry.is_file()
        and size_registry.is_file()
    )
    if completed_refresh:
        return _refresh_complete_prelabel_bindings(
            build=build,
            fixtures=fixtures,
            registry_path=registry,
            size_registry_path=size_registry,
        )
    resume_failed_build = build.exists()
    if resume_failed_build:
        if (
            not build.is_dir()
            or not fixtures.is_dir()
            or any(fixtures.iterdir())
            or registry.exists()
            or size_registry.exists()
            or set(path.name for path in build.iterdir()) != {"native", "pinned-source"}
        ):
            raise RunnerError("existing pre-label outputs are not the exact resumable state")
    else:
        for path in (build, fixtures, registry, size_registry):
            if path.exists():
                raise RunnerError(f"pre-label preparation output must be absent: {path}")
        build.mkdir(parents=True)
        fixtures.mkdir(parents=True)
    integration = build / "pinned-source"
    if resume_failed_build:
        materialization = strict_load_json(
            integration / "s10r3-materialization.json"
        )
        digest_body = dict(materialization)
        stored_digest = digest_body.pop("manifest_digest", None)
        if (
            stored_digest != canonical_sha256(digest_body)
            or materialization.get("commit") != DUCTILE_COMMIT
            or materialization.get("source_identities")
            != {
                "formocast_source_blob": SOURCE_IDENTITIES[
                    "native_formocast_source_blob"
                ][1],
                "formocast_header_blob": SOURCE_IDENTITIES[
                    "native_formocast_header_blob"
                ][1],
                "runtime_source_blob": SOURCE_IDENTITIES[
                    "runtime_queue_source_blob"
                ][1],
                "runtime_header_blob": SOURCE_IDENTITIES[
                    "runtime_queue_header_blob"
                ][1],
                "candidate_construction_blob": SOURCE_IDENTITIES[
                    "candidate_construction_blob"
                ][1],
            }
        ):
            raise RunnerError("partial pinned-source materialization is not valid")
    else:
        materialization = _materialize_pinned_source(integration)
    native = _build_native_helper(
        integration=integration,
        build_root=build,
        materialization=materialization,
    )
    registry_document, measurement = _build_candidate_registry(
        integration=integration,
        output=registry,
        scratch=build / "registry",
    )
    size_document = _write_size_registry(size_registry)
    fixture = materialize_fixture(fixtures / "s10r3-sentinel-fixture.json")
    source_bytes = _git(
        "show",
        f"{DUCTILE_COMMIT}:shared/origami/src/simulator/tensilelite/"
        "formocast_simulator.cpp",
        text=True,
    )
    validate_pinned_guard_source(
        source_bytes,
        source_blob=str(
            _git(
                "rev-parse",
                f"{DUCTILE_COMMIT}:shared/origami/src/simulator/tensilelite/"
                "formocast_simulator.cpp",
                text=True,
            )
        ).strip(),
        fixture=fixture,
    )
    manifest = _critical_prelabel_manifest(
        build_root=build,
        fixture_root=fixtures,
        materialization=materialization,
        native=native,
        registry=registry_document,
        size_registry=size_document,
        registry_measurement=measurement,
    )
    return {
        "checkpoint_id": "S10R3",
        "formal_evidence": False,
        "native_executed": False,
        "status": "PRELABEL_PREPARED",
        "manifest_digest": manifest["manifest_digest"],
    }


def _assert_prelabel_descendants(build: Path, fixtures: Path) -> None:
    immediate = {path.name for path in build.iterdir()}
    if immediate != {
        "native",
        "pinned-source",
        "registry",
        "s10r3-prelabel-materialization.json",
    }:
        raise RunnerError("unexpected prelabel-build descendant class")
    fixture_descendants = [path for path in fixtures.rglob("*") if path.is_file()]
    if fixture_descendants != [fixtures / "s10r3-sentinel-fixture.json"]:
        raise RunnerError("unexpected prelabel-fixture descendant class")
    for root in (build / "native", build / "registry", fixtures):
        for path in root.rglob("*"):
            if path.is_symlink():
                raise RunnerError("prelabel artifact symlink is forbidden")
    forbidden_names = ("transcript", "prediction-result", "conformance-result")
    for path in itertools.chain((build / "native").rglob("*"), fixtures.rglob("*")):
        if any(token in path.name.lower() for token in forbidden_names):
            raise RunnerError("native outcome-like prelabel artifact is forbidden")


def verify_prelabel(
    *,
    build_root: Path | str,
    fixture_root: Path | str,
    registry_path: Path | str,
    size_registry_path: Path | str,
) -> dict[str, Any]:
    _assert_prelabel_absence()
    build = _exact_path(build_root, PRELABEL_BUILD_ROOT, label="build root")
    fixtures = _exact_path(fixture_root, PRELABEL_FIXTURE_ROOT, label="fixture root")
    registry_path = _exact_path(
        registry_path, ROOT / REGISTRY_PATH, label="registry"
    )
    size_registry_path = _exact_path(
        size_registry_path, ROOT / SIZE_REGISTRY_PATH, label="size registry"
    )
    _assert_prelabel_descendants(build, fixtures)
    registry_document = strict_load_json(registry_path)
    _verify_registry(registry_document)
    size_document = strict_load_json(size_registry_path)
    if size_document != size_registry_document():
        raise RunnerError("size registry identity drift")
    fixture = strict_load_json(fixtures / "s10r3-sentinel-fixture.json")
    validate_fixture(fixture)
    materialization = strict_load_json(
        build / "pinned-source/s10r3-materialization.json"
    )
    materialization_digest = dict(materialization)
    recorded_materialization = materialization_digest.pop("manifest_digest", None)
    if (
        recorded_materialization != canonical_sha256(materialization_digest)
        or materialization["commit"] != DUCTILE_COMMIT
    ):
        raise RunnerError("pinned source materialization manifest drift")
    native = strict_load_json(build / "native/s10r3-native-build.json")
    native_body = dict(native)
    recorded_native = native_body.pop("build_manifest_digest", None)
    if recorded_native != canonical_sha256(native_body):
        raise RunnerError("native build manifest digest drift")
    binary = build / "native/build/s10r3-native"
    if (
        native["binary_path"] != str(binary.relative_to(ROOT))
        or sha256_file(binary) != native["binary_sha256"]
        or native["native_executed"] is not False
    ):
        raise RunnerError("native helper binary binding drift")
    if native["cpp_source"] != file_record(NATIVE_SOURCE):
        raise RunnerError("native C++ adapter source drift")
    if native["host_adapter"] != file_record(NATIVE_HOST_ADAPTER):
        raise RunnerError("native host adapter source drift")
    source_blob = str(
        _git(
            "rev-parse",
            f"{DUCTILE_COMMIT}:shared/origami/src/simulator/tensilelite/"
            "formocast_simulator.cpp",
            text=True,
        )
    ).strip()
    source = _git(
        "show",
        f"{DUCTILE_COMMIT}:shared/origami/src/simulator/tensilelite/"
        "formocast_simulator.cpp",
        text=True,
    )
    validate_pinned_guard_source(source, source_blob=source_blob, fixture=fixture)
    manifest = strict_load_json(build / "s10r3-prelabel-materialization.json")
    body = dict(manifest)
    recorded = body.pop("manifest_digest", None)
    if recorded != canonical_sha256(body):
        raise RunnerError("prelabel materialization manifest digest drift")
    for record in manifest["critical_files"]:
        if file_record(record["path"]) != record:
            raise RunnerError(f"critical prelabel file drift: {record['path']}")
    if (
        manifest["candidate_registry_digest"] != registry_document["registry_digest"]
        or manifest["size_registry_digest"] != size_document["registry_digest"]
        or manifest["fixture_digest"] != fixture["fixture_digest"]
        or manifest["native_binary_sha256"] != native["binary_sha256"]
        or manifest["native_executed"] is not False
    ):
        raise RunnerError("prelabel cross-document binding drift")
    return {
        "checkpoint_id": "S10R3",
        "formal_evidence": False,
        "native_executed": False,
        "status": "PRELABEL_IDENTITIES_VERIFIED",
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_or_match_json(path: Path, document: Mapping[str, Any]) -> bool:
    """Write one immutable document or adopt its exact crash orphan."""

    target = _no_symlink_absolute(path, label="immutable JSON output")
    if os.path.lexists(target):
        _ordinary_file(target, label="immutable JSON output")
        if strict_load_json(target) != dict(document):
            raise RunnerError(f"existing artifact differs from replay: {path}")
        return True
    atomic_write_json(target, document, exclusive=True)
    return False


def _raw_document(kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    body = {
        "document_kind": kind,
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "payload": dict(payload),
    }
    return {**body, "document_digest": canonical_sha256(body)}


def _mapping_file_record(path: Path) -> dict[str, Any]:
    absolute = _ordinary_file(path, label="mapping artifact")
    try:
        relative = absolute.relative_to(ROOT.resolve())
    except ValueError as error:
        raise RunnerError("mapping artifact escapes repository root") from error
    info = absolute.lstat()
    return {
        "path": relative.as_posix(),
        "mode": f"0{info.st_mode & 0o777:03o}",
        "size_bytes": info.st_size,
        "sha256": sha256_file(absolute),
    }


def _load_raw_document(path: Path, kind: str) -> dict[str, Any]:
    target = _ordinary_file(path, label=f"raw {kind} document")
    document = strict_load_json(target)
    if set(document) != {
        "document_kind",
        "schema_version",
        "checkpoint_id",
        "payload",
        "document_digest",
    }:
        raise RunnerError(f"raw {kind} schema/unknown-property failure")
    body = dict(document)
    recorded = body.pop("document_digest")
    if (
        document["document_kind"] != kind
        or document["schema_version"] != 1
        or document["checkpoint_id"] != "S10R3"
        or recorded != canonical_sha256(body)
    ):
        raise RunnerError(f"raw {kind} identity/digest failure")
    if kind == "mapping_failure_batch":
        validate_mapping_failure_batch(document)
    elif kind == "mapping_worker_completion" and document["payload"].get(
        "returncode"
    ) == MAPPING_FAILURE_RETURN_CODE:
        validate_mapping_worker_completion(document)
    return document


def _formal_identity(
    lock_path: Path, lock: Mapping[str, Any]
) -> dict[str, Any]:
    registry = strict_load_json(REGISTRY_PATH)
    size_registry = strict_load_json(SIZE_REGISTRY_PATH)
    fixture = strict_load_json(SENTINEL_FIXTURE_PATH)
    return {
        "contract_raw_sha256": EXPECTED_CONTRACT_RAW_SHA256,
        "effective_lock_raw_sha256": sha256_file(lock_path),
        "effective_lock_self_sha256": lock["self_identity"][
            "canonical_self_sha256"
        ],
        "source_registry_fixture_digests": {
            "candidate_registry": registry["registry_digest"],
            "size_registry": size_registry["registry_digest"],
            "sentinel_fixture": fixture["fixture_digest"],
        },
    }


def _formal_document(
    *,
    kind: str,
    lock_path: Path,
    lock: Mapping[str, Any],
    payload: Mapping[str, Any],
    raw_children: Sequence[Mapping[str, Any]],
    upstream_identities: Mapping[str, str],
) -> dict[str, Any]:
    children = [dict(item) for item in raw_children]
    if len({item["path"] for item in children}) != len(children):
        raise RunnerError(f"{kind} raw child path duplicated")
    body = {
        "document_kind": kind,
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        **_formal_identity(lock_path, lock),
        "raw_children": children,
        "upstream_identities": dict(upstream_identities),
        "payload": dict(payload),
    }
    document = {**body, "document_digest": canonical_sha256(body)}
    validate_document(document, kind)
    return document


def _load_formal_document(
    path: Path,
    *,
    kind: str,
    lock_path: Path,
    lock: Mapping[str, Any],
) -> dict[str, Any]:
    target = _ordinary_file(path, label=f"formal {kind} document")
    document = strict_load_json(target)
    validate_document(document, kind)
    body = dict(document)
    recorded = body.pop("document_digest", None)
    if (
        document.get("document_kind") != kind
        or recorded != canonical_sha256(body)
        or {
            key: document[key]
            for key in (
                "contract_raw_sha256",
                "effective_lock_raw_sha256",
                "effective_lock_self_sha256",
                "source_registry_fixture_digests",
            )
        }
        != _formal_identity(lock_path, lock)
    ):
        raise RunnerError(f"{kind} formal identity/digest drift")
    for record in document["raw_children"]:
        if file_record(record["path"]) != record:
            raise RunnerError(f"{kind} raw child drift: {record['path']}")
    return document


class _FormalWriter:
    """Non-blocking cross-command serialization inside one allowed scope."""

    def __init__(self, path: Path):
        self.path = path
        self.stream: Any = None

    def __enter__(self) -> "_FormalWriter":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open("a+b")
        try:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self.stream.close()
            self.stream = None
            raise RunnerError("another formal writer is active") from error
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if self.stream is not None:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
            self.stream.close()
            self.stream = None


def _serialized_formal(scope: Path):
    def decorate(function):
        signature = inspect.signature(function)

        @functools.wraps(function)
        def wrapped(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            admission_path = ROOT / PRODUCTION_ADMISSION_LOCK_PATH
            with stable_admission_lock(
                admission_path, allow_production=True
            ) as (admission_fd, admission_identity):
                _require_formal(bound.arguments["lock_path"])
                with _FormalWriter(scope / ".command-writer.lock"):
                    admission_lock_identity(
                        admission_path,
                        admission_fd,
                        allow_production=True,
                        expected_identity=admission_identity,
                    )
                    return function(*args, **kwargs)

        return wrapped

    return decorate


def _assert_no_terminal(*, allow_reproduction: bool = False) -> None:
    if not DECISION_PATH.exists():
        return
    if allow_reproduction:
        return
    decision = strict_load_json(DECISION_PATH)
    outcome = decision.get("payload", {}).get("scientific_outcome")
    raise RunnerError(f"formal pipeline is already terminal: {outcome}")


def _validator_worker_code() -> str:
    return r'''
import json
import sys

from Tensile import LibraryIO
from Tensile.BenchmarkStructs import BenchmarkProcess
from Tensile.Common.Architectures import gfxToIsa
from Tensile.Common.Capabilities import makeIsaInfoMap
from Tensile.Common.GlobalParameters import assignGlobalParameters
from Tensile.Common.Types import makeDebugConfig
from Tensile.Toolchain.Component import Assembler
from Tensile.backends.ductile_backend import _validate_solution

MARKER = "S10R3_VALIDATOR_RESULT="
request = json.load(open(sys.argv[1], "r", encoding="utf-8"))
document = LibraryIO.read(request["yaml_path"])
benchmark_problem = document["BenchmarkProblems"][0]
process = BenchmarkProcess(benchmark_problem[0], benchmark_problem[1], False)
step = process[0]
isa = gfxToIsa("gfx942")
isa_map = makeIsaInfoMap([isa], request["compiler"])
assignGlobalParameters(document["GlobalParameters"], isa_map)
debug = makeDebugConfig(document["GlobalParameters"])
assembler = Assembler(request["compiler"], "4", False)
rows = []
for config in request["configs"]:
    row = {
        "accepted": False,
        "resolver_none": False,
        "kernel_writer_error": None,
        "exception_taxonomy": None,
        "_validate_solution": False,
        "get_kernel_src": False,
    }
    try:
        valid = _validate_solution(
            process.problemType,
            dict(step.constantParams),
            assembler,
            debug,
            isa_map,
            config,
            get_kernel_src=False,
        )
        row["accepted"] = bool(valid)
        row["resolver_none"] = valid is None
    except Exception as error:
        row["exception_taxonomy"] = type(error).__name__
    rows.append(row)
print(
    MARKER
    + json.dumps(
        {"processed": len(request["configs"]), "rows": rows},
        sort_keys=True,
        separators=(",", ":"),
    )
)
'''


def _covered_atoms(registry: AtomRegistry, config: Mapping[str, Any]) -> list[str]:
    covered = []
    for axis in registry.axes:
        value = config.get(axis.axis_name)
        matches = [
            row["atom_id"]
            for row in registry.rows
            if row["axis_index"] == axis.axis_index
            and type(row["typed_value"]) is type(value)
            and row["typed_value"] == value
        ]
        if len(matches) != 1:
            raise RunnerError(f"config does not identify one atom on {axis.axis_name}")
        covered.append(matches[0])
    return covered


def _validator_chunk(
    *,
    registry: AtomRegistry,
    stream_id: str,
    atom_id: str | None,
    stream_rank: int,
    conditional_priority_rank: int,
    chunk_index: int,
    output: Path,
) -> dict[str, Any]:
    configs = generate_discovery_chunk(
        registry,
        stream_id=stream_id,
        conditional_atom_id=atom_id,
        chunk_index=chunk_index,
    )
    scratch = output.parent / f".{output.stem}-worker"
    scratch.mkdir(parents=True, exist_ok=True)
    request_path = scratch / "request.json"
    request = {
        "schema_version": 1,
        "yaml_path": str(ACTUAL_YAML),
        "compiler": "/opt/rocm/bin/amdclang++",
        "configs": configs,
    }
    if request_path.exists():
        if strict_load_json(request_path) != request:
            raise RunnerError("uncommitted validator request differs from replay")
    else:
        atomic_write_json(request_path, request, exclusive=True)
    environment = {
        **FORMAL_ENVIRONMENT,
        "PYTHONPATH": str(
            PRELABEL_BUILD_ROOT / "pinned-source/projects/hipblaslt/tensilelite"
        ),
    }
    completion = None
    for completion_path in sorted(scratch.glob("attempt-*.complete.json")):
        candidate = _load_raw_document(
            completion_path, "validator_worker_completion"
        )
        payload = candidate["payload"]
        stdout_candidate = ROOT / payload["stdout_path"]
        stderr_candidate = ROOT / payload["stderr_path"]
        if (
            sha256_file(stdout_candidate) != payload["stdout_sha256"]
            or sha256_file(stderr_candidate) != payload["stderr_sha256"]
        ):
            raise RunnerError("validator completion log binding drift")
        if payload["returncode"] == 0:
            completion = candidate
    if completion is None:
        attempt = len(list(scratch.glob("attempt-*.stdout"))) + 1
        stdout_path = scratch / f"attempt-{attempt:02d}.stdout"
        stderr_path = scratch / f"attempt-{attempt:02d}.stderr"
        completion_path = scratch / f"attempt-{attempt:02d}.complete.json"
        started = time.monotonic()
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        completed = subprocess.run(
            [
                "/opt/venv/bin/python3",
                "-c",
                _validator_worker_code(),
                str(request_path),
            ],
            cwd=scratch,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=3600,
        )
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        _atomic_write_bytes(stdout_path, completed.stdout)
        _atomic_write_bytes(stderr_path, completed.stderr)
        completion = _raw_document(
            "validator_worker_completion",
            {
                "attempt": attempt,
                "returncode": completed.returncode,
                "stdout_path": str(stdout_path.relative_to(ROOT)),
                "stdout_sha256": sha256_file(stdout_path),
                "stderr_path": str(stderr_path.relative_to(ROOT)),
                "stderr_sha256": sha256_file(stderr_path),
                "wall_s": time.monotonic() - started,
                "cpu_s": max(
                    0.0,
                    (
                        after.ru_utime
                        + after.ru_stime
                        - before.ru_utime
                        - before.ru_stime
                    ),
                ),
                "maximum_child_rss_kib": max(0, after.ru_maxrss),
            },
        )
        atomic_write_json(completion_path, completion, exclusive=True)
    completion_payload = completion["payload"]
    stdout_path = ROOT / completion_payload["stdout_path"]
    stderr_path = ROOT / completion_payload["stderr_path"]
    stdout_bytes = stdout_path.read_bytes()
    stderr_bytes = stderr_path.read_bytes()
    if completion_payload["returncode"]:
        raise RunnerError(
            "pinned validator worker failed closed: "
            + stderr_bytes.decode("utf-8", errors="replace")[-2000:]
        )
    marked = [
        line[len(VALIDATOR_MARKER) :]
        for line in stdout_bytes.decode("utf-8", errors="replace").splitlines()
        if line.startswith(VALIDATOR_MARKER)
    ]
    if len(marked) != 1:
        raise RunnerError("pinned validator worker emitted no unique result")
    result = json.loads(marked[0])
    rows = result.get("rows")
    if result.get("processed") != CHUNK_SIZE or not isinstance(rows, list) or len(
        rows
    ) != CHUNK_SIZE:
        raise RunnerError("pinned validator result cardinality mismatch")
    draws = []
    for draw_index, (config, validation) in enumerate(zip(configs, rows)):
        if (
            type(validation) is not dict
            or type(validation.get("accepted")) is not bool
            or validation.get("get_kernel_src") is not False
        ):
            raise RunnerError("pinned validator row schema failure")
        draws.append(
            {
                "draw_index": draw_index,
                "config": config,
                "config_hash": canonical_sha256(config),
                "covered_atom_ids": _covered_atoms(registry, config),
                "validation": validation,
            }
        )
    payload = {
        "stream_id": stream_id,
        "atom_id": atom_id,
        "stream_rank": stream_rank,
        "conditional_priority_rank": conditional_priority_rank,
        "chunk_index": chunk_index,
        "draw_count": CHUNK_SIZE,
        "draws": draws,
        "command": {
            "argv": [
                "/opt/venv/bin/python3",
                "-c",
                hashlib.sha256(_validator_worker_code().encode()).hexdigest(),
                str(request_path.relative_to(ROOT)),
            ],
            "cwd": str(scratch.relative_to(ROOT)),
            "environment": environment,
            "returncode": completion_payload["returncode"],
            "request_sha256": sha256_file(request_path),
            "stdout_sha256": sha256_file(stdout_path),
            "stderr_sha256": sha256_file(stderr_path),
            "attempt": completion_payload["attempt"],
        },
        "measurement": {
            "wall_s": completion_payload["wall_s"],
            "cpu_s": completion_payload["cpu_s"],
            "maximum_child_rss_kib": completion_payload[
                "maximum_child_rss_kib"
            ],
        },
    }
    document = _raw_document("support_chunk", payload)
    atomic_write_json(output, document, exclusive=True)
    return document


def _chunk_path(stream_rank: int, chunk_index: int) -> Path:
    label = "global" if stream_rank == 0 else f"conditional-{stream_rank - 1:02d}"
    return FORMAL_CPU_ROOT / "chunks" / label / f"{chunk_index:04d}.json"


def _verified_chunk(path: Path, *, stream_id: str, chunk_index: int) -> dict[str, Any]:
    document = _load_raw_document(path, "support_chunk")
    payload = document["payload"]
    if (
        payload.get("stream_id") != stream_id
        or payload.get("chunk_index") != chunk_index
        or payload.get("draw_count") != CHUNK_SIZE
        or len(payload.get("draws", [])) != CHUNK_SIZE
    ):
        raise RunnerError("support chunk resume identity mismatch")
    return document


def _global_targets(registry: AtomRegistry) -> tuple[str, ...]:
    witnessed: set[str] = set()
    for chunk_index in range(GLOBAL_CHUNKS):
        chunk = _verified_chunk(
            _chunk_path(0, chunk_index),
            stream_id="global",
            chunk_index=chunk_index,
        )
        for draw in chunk["payload"]["draws"]:
            if draw["validation"]["accepted"]:
                witnessed.update(draw["covered_atom_ids"])
    global_states = classify_support(registry, witnessed)
    return activate_conditional_targets(registry, global_states)


@_serialized_formal(FORMAL_CPU_ROOT)
def support_discovery_command(lock_path: Path | str) -> dict[str, Any]:
    _require_formal(lock_path)
    lock_target = Path(lock_path).resolve()
    _assert_no_terminal()
    if SUPPORT_PATH.exists():
        raise RunnerError("support discovery cannot run after classification seal")
    registry = _verify_registry(strict_load_json(REGISTRY_PATH))
    lock_digest = sha256_file(lock_target)
    ledger = RunLedger(FORMAL_CPU_ROOT / "ledger", lock_digest)
    with ledger:
        state = ledger.load_and_verify()
        event_by_stream_chunk = {
            (event["stream_id"], event["chunk_index"]): event
            for event in state["events"]
        }

        def complete_stream(
            stream_id: str,
            atom_id: str | None,
            stream_rank: int,
            conditional_priority_rank: int,
        ) -> None:
            for chunk_index in range(
                state["index"]["per_stream_next_chunk"].get(stream_id, 0),
                GLOBAL_CHUNKS if stream_rank == 0 else CONDITIONAL_CHUNKS,
            ):
                path = _chunk_path(stream_rank, chunk_index)
                if path.exists():
                    chunk = _verified_chunk(
                        path, stream_id=stream_id, chunk_index=chunk_index
                    )
                    recovered = True
                else:
                    chunk = _validator_chunk(
                        registry=registry,
                        stream_id=stream_id,
                        atom_id=atom_id,
                        stream_rank=stream_rank,
                        conditional_priority_rank=conditional_priority_rank,
                        chunk_index=chunk_index,
                        output=path,
                    )
                    recovered = False
                event = ledger.append(
                    stage=(
                        Stage.GLOBAL_DISCOVERY
                        if stream_rank == 0
                        else Stage.CONDITIONAL_DISCOVERY
                    ),
                    stream_id=stream_id,
                    atom_id=atom_id,
                    chunk_index=chunk_index,
                    payload={
                        "chunk": file_record(path),
                        "chunk_document_digest": chunk["document_digest"],
                        "recovered_unledgered_complete_artifact": recovered,
                    },
                )
                event_by_stream_chunk[(stream_id, chunk_index)] = event

        complete_stream("global", None, 0, 0)
        targets = _global_targets(registry)
        for priority_rank, atom_id in enumerate(targets):
            complete_stream(
                f"conditional-{priority_rank:02d}",
                atom_id,
                priority_rank + 1,
                priority_rank,
            )
    final = ledger.load_and_verify()
    expected_events = GLOBAL_CHUNKS + len(_global_targets(registry)) * CONDITIONAL_CHUNKS
    if final["index"]["event_count"] != expected_events:
        raise RunnerError("support discovery ledger is incomplete")
    return {
        "checkpoint_id": "S10R3",
        "status": "SUPPORT_DISCOVERY_COMPLETE",
        "chunk_count": expected_events,
        "draw_count": expected_events * CHUNK_SIZE,
        "conditional_target_count": len(_global_targets(registry)),
        "ledger_last_digest": final["index"]["last_digest"],
    }


def _discovery_evidence(
    registry: AtomRegistry,
) -> tuple[list[Witness], set[str], list[dict[str, Any]], tuple[str, ...]]:
    targets = _global_targets(registry)
    witnesses = []
    witnessed_atoms: set[str] = set()
    raw_children = []
    schedules = [(0, "global", None, 0)]
    schedules.extend(
        (rank + 1, f"conditional-{rank:02d}", atom_id, rank)
        for rank, atom_id in enumerate(targets)
    )
    for stream_rank, stream_id, atom_id, priority_rank in schedules:
        for chunk_index in range(
            GLOBAL_CHUNKS if stream_rank == 0 else CONDITIONAL_CHUNKS
        ):
            path = _chunk_path(stream_rank, chunk_index)
            chunk = _verified_chunk(
                path, stream_id=stream_id, chunk_index=chunk_index
            )
            raw_children.append(file_record(path))
            for draw in chunk["payload"]["draws"]:
                if draw["validation"]["accepted"]:
                    coverage = frozenset(draw["covered_atom_ids"])
                    witnessed_atoms.update(coverage)
                    witnesses.append(
                        Witness(
                            config=draw["config"],
                            config_hash=draw["config_hash"],
                            atom_ids=coverage,
                            stream_rank=stream_rank,
                            conditional_priority_rank=priority_rank,
                            chunk_index=chunk_index,
                            draw_index=draw["draw_index"],
                        )
                    )
    ledger = RunLedger(FORMAL_CPU_ROOT / "ledger", sha256_file(DEFAULT_LOCK_PATH))
    state = ledger.load_and_verify()
    recorded_paths = {item["path"] for item in raw_children}
    for path in sorted(FORMAL_CPU_ROOT.rglob("*")):
        if (
            path.is_file()
            and not path.is_symlink()
            and not path.name.endswith("writer.lock")
            and str(path.relative_to(ROOT)) not in recorded_paths
        ):
            raw_children.append(file_record(path))
    expected = GLOBAL_CHUNKS + len(targets) * CONDITIONAL_CHUNKS
    if state["index"]["event_count"] != expected:
        raise RunnerError("support evidence ledger count mismatch")
    return witnesses, witnessed_atoms, raw_children, targets


@_serialized_formal(FORMAL_CPU_ROOT)
def support_classification_command(lock_path: Path | str) -> dict[str, Any]:
    lock = _require_formal(lock_path)
    lock_target = Path(lock_path).resolve()
    _assert_no_terminal()
    registry = _verify_registry(strict_load_json(REGISTRY_PATH))
    witnesses, witnessed_atoms, children, targets = _discovery_evidence(registry)
    classifications = classify_support(registry, witnessed_atoms)
    counts = {
        state.value: sum(1 for value in classifications.values() if value is state)
        for state in SupportState
    }
    document = _formal_document(
        kind="support_classification",
        lock_path=lock_target,
        lock=lock,
        raw_children=children,
        upstream_identities={},
        payload={
            "global_chunk_count": GLOBAL_CHUNKS,
            "conditional_target_atom_ids": list(targets),
            "conditional_chunk_count_per_target": CONDITIONAL_CHUNKS,
            "total_chunk_count": GLOBAL_CHUNKS + len(targets) * CONDITIONAL_CHUNKS,
            "total_draw_count": (
                GLOBAL_CHUNKS + len(targets) * CONDITIONAL_CHUNKS
            )
            * CHUNK_SIZE,
            "accepted_occurrence_count": len(witnesses),
            "classifications": {
                atom_id: state.value for atom_id, state in classifications.items()
            },
            "state_counts": counts,
            "stochastic_zero_is_not_absence": True,
        },
    )
    recovered = _write_or_match_json(SUPPORT_PATH, document)
    return {
        "checkpoint_id": "S10R3",
        "status": "SUPPORT_CLASSIFICATION_SEALED",
        "document_digest": document["document_digest"],
        "recovered": recovered,
    }


def _formal_report_bytes(decision: Mapping[str, Any]) -> bytes:
    payload = decision["payload"]
    lines = [
        "# S10R3 Stage-1 bounded-cover entry report",
        "",
        f"- Scientific outcome: `{payload['scientific_outcome']}`",
        f"- Criterion: `{payload['criterion']}`",
        f"- Failure ID: `{payload['failure_id']}`",
        f"- Edge: `{payload['edge']}`",
        f"- Decision digest: `{decision['document_digest']}`",
        "- State: terminal scientific decision pending independent reproduction, "
        "fresh verification, and Main closeout.",
        "",
        "This report does not claim checkpoint completion.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def _terminal_decision(
    *,
    lock_path: Path,
    lock: Mapping[str, Any],
    scientific_outcome: str,
    criterion: str,
    failure_id: str | None,
    edge: str | None,
    evidence: Mapping[str, str],
    raw_children: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    document = _formal_document(
        kind="decision",
        lock_path=lock_path,
        lock=lock,
        raw_children=raw_children,
        upstream_identities=evidence,
        payload={
            "scientific_outcome": scientific_outcome,
            "criterion": criterion,
            "failure_id": failure_id,
            "edge": edge,
            "terminal": True,
            "checkpoint_complete": False,
            "closeout_state": "pending_independent_reproduction_and_verification",
        },
    )
    _write_or_match_json(DECISION_PATH, document)
    report = _formal_report_bytes(document)
    if REPORT_PATH.exists():
        if REPORT_PATH.read_bytes() != report:
            raise RunnerError("existing formal report differs from decision")
    else:
        _atomic_write_bytes(REPORT_PATH, report)
    return document


def _support_document(lock_path: Path, lock: Mapping[str, Any]) -> dict[str, Any]:
    return _load_formal_document(
        SUPPORT_PATH,
        kind="support_classification",
        lock_path=lock_path,
        lock=lock,
    )


@_serialized_formal(FORMAL_CPU_ROOT)
def select_bounded_cover_command(lock_path: Path | str) -> dict[str, Any]:
    lock = _require_formal(lock_path)
    lock_target = Path(lock_path).resolve()
    _assert_no_terminal()
    support = _support_document(lock_target, lock)
    registry = _verify_registry(strict_load_json(REGISTRY_PATH))
    witnesses, _, children, _ = _discovery_evidence(registry)
    classifications = {
        atom_id: SupportState(value)
        for atom_id, value in support["payload"]["classifications"].items()
    }
    result = deterministic_greedy_bounded_cover(
        registry, classifications, witnesses
    )
    selection_payload = {
        "status": result.status,
        "failure_reason": result.failure_reason,
        "mandatory_atoms": list(result.mandatory_atoms),
        "distinct_witness_count": result.distinct_witness_count,
        "greedy_steps": [
            {
                "step_index": step.step_index,
                "config_hash": step.config_hash,
                "gain": step.gain,
                "newly_covered_atoms": list(step.newly_covered_atoms),
                "remaining_after": step.remaining_after,
            }
            for step in result.greedy_steps
        ],
        "c_greedy": result.c_greedy,
        "k": result.k,
        "final_config_hashes": list(result.final_config_hashes),
        "final_witnesses": [
            {
                "config": dict(item.config),
                "config_hash": item.config_hash,
                "atom_ids": sorted(item.atom_ids),
                "stream_rank": item.stream_rank,
                "conditional_priority_rank": item.conditional_priority_rank,
                "chunk_index": item.chunk_index,
                "draw_index": item.draw_index,
            }
            for item in result.final_witnesses
        ],
        "l_axis": result.l_axis,
        "disclosure": result.disclosure,
        "support_classification_digest": support["document_digest"],
    }
    selection = _raw_document("bounded_cover_selection", selection_payload)
    selection_path = FORMAL_CPU_ROOT / "bounded-cover-selection.json"
    recovered = _write_or_match_json(selection_path, selection)
    if result.status != "selected":
        decision = _terminal_decision(
            lock_path=lock_target,
            lock=lock,
            scientific_outcome="inconclusive",
            criterion="FT-INCONCLUSIVE",
            failure_id=result.failure_reason,
            edge=None,
            evidence={
                "support_classification": support["document_digest"],
                "bounded_cover_selection": selection["document_digest"],
            },
            raw_children=[*children, file_record(selection_path)],
        )
        return {
            "checkpoint_id": "S10R3",
            "status": "TERMINAL_INCONCLUSIVE",
            "decision_digest": decision["document_digest"],
            "recovered": recovered,
        }
    return {
        "checkpoint_id": "S10R3",
        "status": "BOUNDED_K_SELECTED",
        "k": result.k,
        "c_greedy": result.c_greedy,
        "selection_digest": selection["document_digest"],
        "recovered": recovered,
    }


def _selection_document() -> dict[str, Any]:
    selection = _load_raw_document(
        FORMAL_CPU_ROOT / "bounded-cover-selection.json",
        "bounded_cover_selection",
    )
    if selection["payload"]["status"] != "selected":
        raise RunnerError("mapping requires a successfully selected bounded K")
    return selection


def _parse_mapping_failure_marker(
    stdout_bytes: bytes, configs: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    try:
        stdout = stdout_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise RunnerError("mapping failure stdout is not UTF-8") from error
    marked = [
        line[len(MAPPING_FAILURE_MARKER) :]
        for line in stdout.splitlines()
        if line.startswith(MAPPING_FAILURE_MARKER)
    ]
    if len(marked) != 1:
        raise RunnerError("mapping worker failure emitted no unique signature")
    try:
        failure = json.loads(marked[0])
    except json.JSONDecodeError as error:
        raise RunnerError("mapping worker failure signature is not JSON") from error
    canonical_marker = json.dumps(
        failure,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    if marked[0] != canonical_marker or type(failure) is not dict:
        raise RunnerError("mapping worker failure signature is not canonical")
    required = {
        "failure_kind",
        "category",
        "error_class",
        "error_code",
        "slot",
        "config_hash",
        "kernel_failures",
        "failure_signature",
    }
    if set(failure) != required:
        raise RunnerError("mapping worker failure signature schema drift")
    slot = failure["slot"]
    if (
        failure["failure_kind"] != "required_mapping_code_generation"
        or failure["category"] != "code_generation_nonzero"
        or failure["error_class"]
        != "KernelWriterAssembly_overflowedResources"
        or failure["error_code"] != 5
        or type(slot) is not int
        or not 0 <= slot < len(configs)
        or failure["config_hash"] != canonical_sha256(dict(configs[slot]))
        or type(failure["kernel_failures"]) is not list
        or not failure["kernel_failures"]
    ):
        raise RunnerError("mapping worker failure signature identity drift")
    for kernel_failure in failure["kernel_failures"]:
        if (
            type(kernel_failure) is not dict
            or set(kernel_failure)
            != {
                "kernel_index",
                "kernel_name",
                "result_error_code",
                "overflowed_resources",
            }
            or type(kernel_failure["kernel_index"]) is not int
            or kernel_failure["kernel_index"] < 0
            or type(kernel_failure["kernel_name"]) is not str
            or not kernel_failure["kernel_name"]
            or kernel_failure["result_error_code"] != -2
            or kernel_failure["overflowed_resources"] != 5
        ):
            raise RunnerError("mapping worker kernel failure schema drift")
    body = dict(failure)
    signature = body.pop("failure_signature")
    if signature != canonical_sha256(body):
        raise RunnerError("mapping worker failure signature digest drift")
    return failure


def _run_mapping_worker(
    pass_id: str, configs: Sequence[Mapping[str, Any]], output_root: Path
) -> dict[str, Any]:
    expected_output_root = FORMAL_MAPPING_ROOT / f"pass-{pass_id.lower()}"
    output_root = _no_symlink_absolute(output_root, label="mapping pass root")
    expected_output_root = Path(os.path.abspath(expected_output_root))
    if output_root != expected_output_root:
        raise RunnerError("mapping pass root is not the exact canonical path")
    output_root.mkdir(parents=True, exist_ok=True)
    output_root = _ordinary_directory(
        output_root,
        label="mapping pass root",
        exact_parent=Path(os.path.abspath(FORMAL_MAPPING_ROOT)),
    )
    request_path = output_root / "request.json"
    provenance_path = (
        PRELABEL_BUILD_ROOT
        / "pinned-source/projects/hipblaslt/tensilelite/Tensile/Contractions.py"
    )
    request = {
        "schema_version": 1,
        "pass_id": pass_id,
        "yaml_path": str(ACTUAL_YAML),
        "yaml_sha256": sha256_file(ACTUAL_YAML),
        "compiler": "/opt/rocm/bin/amdclang++",
        "configs": [dict(item) for item in configs],
        "config_hashes": [canonical_sha256(dict(item)) for item in configs],
        "provenance_source_path": str(provenance_path),
        "provenance_record_path": str(provenance_path.relative_to(ROOT)),
        "provenance_source_sha256": sha256_file(provenance_path),
        "worker_source_sha256": hashlib.sha256(
            mapping_worker_code().encode("utf-8")
        ).hexdigest(),
    }
    if os.path.lexists(request_path):
        request_path = _ordinary_file(request_path, label="mapping request")
        if strict_load_json(request_path) != request:
            raise RunnerError("partial mapping request differs from deterministic replay")
    else:
        atomic_write_json(request_path, request, exclusive=True)
    environment = {
        **FORMAL_ENVIRONMENT,
        "PYTHONPATH": os.pathsep.join(
            (
                str(
                    PRELABEL_BUILD_ROOT
                    / "pinned-source/projects/hipblaslt/tensilelite"
                ),
                str(
                    PRELABEL_BUILD_ROOT
                    / "pinned-source/projects/hipblaslt/tensilelite/"
                    "Tensile/Utilities"
                ),
            )
        ),
    }
    attempt_entries = sorted(output_root.glob("attempt-*"))
    attempt_roots = []
    for path in attempt_entries:
        if re.fullmatch(r"attempt-[0-9]{2}", path.name) is None:
            raise RunnerError("mapping attempt path shape drift")
        attempt_roots.append(
            _ordinary_directory(
                path,
                label="mapping attempt root",
                exact_parent=output_root,
            )
        )
    if [path.name for path in attempt_roots] != [
        f"attempt-{attempt:02d}" for attempt in range(1, len(attempt_roots) + 1)
    ]:
        raise RunnerError("mapping attempt directory sequence drift")
    if len(attempt_roots) > 2:
        raise RunnerError("mapping worker attempt cap exceeded")

    completions = []

    def load_completion(attempt_root: Path) -> dict[str, Any]:
        attempt_root = _ordinary_directory(
            attempt_root,
            label="mapping attempt root",
            exact_parent=output_root,
        )
        completion_path = attempt_root / "completion.json"
        if not os.path.lexists(completion_path):
            raise RunnerError("partial mapping attempt requires independent inspection")
        candidate = _load_raw_document(
            completion_path, "mapping_worker_completion"
        )
        payload = candidate["payload"]
        if set(payload) != {
            "attempt",
            "returncode",
            "cwd_path",
            "stdout_path",
            "stdout_sha256",
            "stderr_path",
            "stderr_sha256",
            "worker_artifacts",
            "wall_s",
            "cpu_s",
            "maximum_child_rss_kib",
        }:
            raise RunnerError("mapping completion payload schema drift")
        expected_attempt = int(attempt_root.name[-2:])
        expected_cwd = str(attempt_root.relative_to(ROOT))
        stdout_candidate = attempt_root / "worker.stdout"
        stderr_candidate = attempt_root / "worker.stderr"
        if (
            type(payload["attempt"]) is not int
            or type(payload["returncode"]) is not int
            or type(payload["cwd_path"]) is not str
            or type(payload["stdout_path"]) is not str
            or type(payload["stdout_sha256"]) is not str
            or type(payload["stderr_path"]) is not str
            or type(payload["stderr_sha256"]) is not str
            or type(payload["maximum_child_rss_kib"]) is not int
        ):
            raise RunnerError("mapping completion scalar type drift")
        if (
            type(payload["wall_s"]) not in {int, float}
            or not math.isfinite(payload["wall_s"])
            or payload["wall_s"] < 0
            or type(payload["cpu_s"]) not in {int, float}
            or not math.isfinite(payload["cpu_s"])
            or payload["cpu_s"] < 0
            or payload["maximum_child_rss_kib"] < 0
        ):
            raise RunnerError("mapping completion measurement drift")
        if (
            payload["attempt"] != expected_attempt
            or payload["cwd_path"] != expected_cwd
            or payload["stdout_path"] != str(stdout_candidate.relative_to(ROOT))
            or payload["stderr_path"] != str(stderr_candidate.relative_to(ROOT))
            or sha256_file(stdout_candidate) != payload["stdout_sha256"]
            or sha256_file(stderr_candidate) != payload["stderr_sha256"]
        ):
            raise RunnerError("mapping completion log/cwd binding drift")
        artifacts = payload["worker_artifacts"]
        artifact_paths = [
            path
            for path in sorted(attempt_root.rglob("*"))
            if path.is_file()
            and path not in {stdout_candidate, stderr_candidate, completion_path}
            and not path.is_symlink()
        ]
        observed_artifacts = [_mapping_file_record(path) for path in artifact_paths]
        if (
            any(path.is_symlink() for path in attempt_root.rglob("*"))
            or type(artifacts) is not list
            or artifacts != observed_artifacts
        ):
            raise RunnerError("mapping completion worker artifact drift")
        return candidate

    completions.extend(load_completion(path) for path in attempt_roots)

    def run_attempt(attempt: int) -> dict[str, Any]:
        attempt_root = output_root / f"attempt-{attempt:02d}"
        try:
            attempt_root.mkdir(mode=0o700)
        except FileExistsError as error:
            raise RunnerError("exclusive mapping attempt directory exists") from error
        attempt_root = _ordinary_directory(
            attempt_root,
            label="mapping attempt root",
            exact_parent=output_root,
        )
        stdout_path = attempt_root / "worker.stdout"
        stderr_path = attempt_root / "worker.stderr"
        completion_path = attempt_root / "completion.json"
        started = time.monotonic()
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        completed = subprocess.run(
            [
                "/opt/venv/bin/python3",
                "-c",
                mapping_worker_code(),
                str(request_path),
            ],
            cwd=attempt_root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=7200,
        )
        _ordinary_directory(
            attempt_root,
            label="mapping attempt root",
            exact_parent=output_root,
        )
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        _atomic_write_bytes(stdout_path, completed.stdout)
        _atomic_write_bytes(stderr_path, completed.stderr)
        descendants = list(attempt_root.rglob("*"))
        if any(path.is_symlink() for path in descendants):
            raise RunnerError("mapping worker created a symlink artifact")
        if any(not path.is_dir() and not path.is_file() for path in descendants):
            raise RunnerError("mapping worker created a nonordinary artifact")
        worker_artifacts = [
            _mapping_file_record(path)
            for path in sorted(descendants)
            if path.is_file()
            and path not in {stdout_path, stderr_path, completion_path}
            and not path.is_symlink()
        ]
        completion = _raw_document(
            "mapping_worker_completion",
            {
                "attempt": attempt,
                "returncode": completed.returncode,
                "cwd_path": str(attempt_root.relative_to(ROOT)),
                "stdout_path": str(stdout_path.relative_to(ROOT)),
                "stdout_sha256": sha256_file(stdout_path),
                "stderr_path": str(stderr_path.relative_to(ROOT)),
                "stderr_sha256": sha256_file(stderr_path),
                "worker_artifacts": worker_artifacts,
                "wall_s": time.monotonic() - started,
                "cpu_s": max(
                    0.0,
                    after.ru_utime
                    + after.ru_stime
                    - before.ru_utime
                    - before.ru_stime,
                ),
                "maximum_child_rss_kib": max(0, after.ru_maxrss),
            },
        )
        atomic_write_json(completion_path, completion, exclusive=True)
        return completion

    if not completions:
        completions.append(run_attempt(1))

    def outcome(
        completion: Mapping[str, Any],
    ) -> tuple[str, bytes, bytes, dict[str, Any] | None]:
        payload = completion["payload"]
        stdout_bytes = (ROOT / payload["stdout_path"]).read_bytes()
        stderr_bytes = (ROOT / payload["stderr_path"]).read_bytes()
        if payload["returncode"] == 0:
            return "success", stdout_bytes, stderr_bytes, None
        if payload["returncode"] != MAPPING_FAILURE_RETURN_CODE:
            raise RunnerError(
                "pinned mapping worker failed closed: "
                + stderr_bytes.decode("utf-8", errors="replace")[-4000:]
            )
        validate_mapping_worker_completion(
            completion, repository_root=ROOT, require_files=True
        )
        failure = _parse_mapping_failure_marker(stdout_bytes, configs)
        return "mapping_failure", stdout_bytes, stderr_bytes, failure

    outcomes = [outcome(completion) for completion in completions]
    if outcomes[0][0] == "mapping_failure" and len(completions) == 1:
        completions.append(run_attempt(2))
        outcomes.append(outcome(completions[-1]))
    if len(completions) == 2 and outcomes[0][0] == "success":
        raise RunnerError("mapping worker ran an attempt after success")
    if len(completions) == 2 and outcomes[0][0] != outcomes[1][0]:
        raise RunnerError("mapping worker attempt outcomes are not reproducible")

    successful = [
        (completion, item)
        for completion, item in zip(completions, outcomes)
        if item[0] == "success"
    ]
    if successful:
        completion, (_, stdout_bytes, stderr_bytes, _) = successful[-1]
    else:
        if len(outcomes) != 2 or any(item[0] != "mapping_failure" for item in outcomes):
            raise RunnerError("mapping worker has no complete reproducibility unit")
        first_failure = outcomes[0][3]
        second_failure = outcomes[1][3]
        if first_failure != second_failure:
            raise RunnerError("mapping worker failure signatures are not reproducible")
        attempts = []
        for completion in completions:
            payload = completion["payload"]
            attempts.append(
                {
                    "completion_digest": completion["document_digest"],
                    **{
                        key: payload[key]
                        for key in (
                            "attempt",
                            "returncode",
                            "cwd_path",
                            "stdout_path",
                            "stdout_sha256",
                            "stderr_path",
                            "stderr_sha256",
                            "worker_artifacts",
                        )
                    },
                }
            )
        failure_document = _raw_document(
            "mapping_failure_batch",
            {
                "status": "FT-BLOCKED-MAPPING",
                "pass_id": pass_id,
                "k": len(configs),
                "complete": True,
                "reproducible": True,
                "attempt_count": 2,
                "request_path": str(request_path.relative_to(ROOT)),
                "request_sha256": sha256_file(request_path),
                "config_hashes": request["config_hashes"],
                "failure": first_failure,
                "attempts": attempts,
                "worker_binding": {
                    "worker_source_sha256": request["worker_source_sha256"],
                    "yaml_path": request["yaml_path"],
                    "yaml_sha256": request["yaml_sha256"],
                    "provenance_source_path": request[
                        "provenance_source_path"
                    ],
                    "provenance_source_sha256": request[
                        "provenance_source_sha256"
                    ],
                    "compiler": request["compiler"],
                },
            },
        )
        validate_mapping_failure_batch(
            failure_document,
            request=request,
            completions=completions,
            repository_root=ROOT,
            require_files=True,
        )
        _write_or_match_json(output_root / "mapping-failure.json", failure_document)
        return failure_document

    completion_payload = completion["payload"]
    stdout_path = ROOT / completion_payload["stdout_path"]
    stderr_path = ROOT / completion_payload["stderr_path"]
    marked = [
        line[len(MAPPING_RESULT_MARKER) :]
        for line in stdout_bytes.decode("utf-8", errors="replace").splitlines()
        if line.startswith(MAPPING_RESULT_MARKER)
    ]
    if len(marked) != 1:
        raise RunnerError("pinned mapping worker emitted no unique result")
    result = json.loads(marked[0])
    worker_rows = result.get("rows")
    if (
        result.get("processed_configs") != len(configs)
        or not isinstance(worker_rows, list)
        or len(worker_rows) != len(configs)
    ):
        raise RunnerError("pinned mapping worker row cardinality mismatch")
    by_hash = {
        canonical_sha256(row["config"]): row for row in worker_rows
    }
    if set(by_hash) != {canonical_sha256(config) for config in configs}:
        raise RunnerError("pinned mapping worker config identity mismatch")

    def resolver(
        config: Mapping[str, Any], size: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        del size
        row = by_hash[canonical_sha256(config)]
        return {
            key: row[key]
            for key in (
                "resolved_solution",
                "size_mapping",
                "formocast_input",
                "required_field_provenance",
            )
        }

    rows = run_mapping_batch(pass_id=pass_id, configs=configs, resolver=resolver)
    payload = {
        "pass_id": pass_id,
        "k": len(configs),
        "row_count": len(rows),
        "rows": rows,
        "command": {
            "argv": [
                "/opt/venv/bin/python3",
                "-c",
                hashlib.sha256(mapping_worker_code().encode()).hexdigest(),
                str(request_path.relative_to(ROOT)),
            ],
            "cwd": completion_payload["cwd_path"],
            "environment": environment,
            "returncode": completion_payload["returncode"],
            "request_sha256": sha256_file(request_path),
            "stdout_sha256": sha256_file(stdout_path),
            "stderr_sha256": sha256_file(stderr_path),
            "attempt": completion_payload["attempt"],
        },
        "measurement": {
            "wall_s": completion_payload["wall_s"],
            "cpu_s": completion_payload["cpu_s"],
            "maximum_child_rss_kib": completion_payload[
                "maximum_child_rss_kib"
            ],
        },
    }
    document = _raw_document("mapping_pass", payload)
    atomic_write_json(output_root / "mapping-pass.json", document, exclusive=True)
    return document


def _mapping_pass(pass_id: str) -> dict[str, Any]:
    document = _load_raw_document(
        FORMAL_MAPPING_ROOT / f"pass-{pass_id.lower()}/mapping-pass.json",
        "mapping_pass",
    )
    if document["payload"]["pass_id"] != pass_id:
        raise RunnerError("mapping pass identity drift")
    return document


@_serialized_formal(FORMAL_MAPPING_ROOT)
def mapping_command(pass_id: str, lock_path: Path | str) -> dict[str, Any]:
    lock = _require_formal(lock_path)
    lock_target = Path(lock_path).resolve()
    _assert_no_terminal()
    selection = _selection_document()
    configs = [row["config"] for row in selection["payload"]["final_witnesses"]]
    if pass_id == "B" and not (
        FORMAL_MAPPING_ROOT / "pass-a/mapping-pass.json"
    ).is_file():
        raise RunnerError("mapping pass B requires complete pass A")
    if pass_id == "A" and (
        FORMAL_MAPPING_ROOT / "pass-b/mapping-pass.json"
    ).exists():
        raise RunnerError("mapping pass A cannot run after pass B")
    pass_root = FORMAL_MAPPING_ROOT / f"pass-{pass_id.lower()}"
    with _FormalWriter(FORMAL_MAPPING_ROOT / ".writer.lock"):
        pass_document = (
            _mapping_pass(pass_id)
            if (pass_root / "mapping-pass.json").is_file()
            else _run_mapping_worker(pass_id, configs, pass_root)
        )
        if pass_document["document_kind"] == "mapping_failure_batch":
            terminal_stage = require_complete_unit(
                complete=(
                    pass_document["payload"]["complete"] is True
                    and pass_document["payload"]["reproducible"] is True
                    and pass_document["payload"]["attempt_count"] == 2
                ),
                failure_kind="mapping",
                current=(Stage.MAPPING_A if pass_id == "A" else Stage.MAPPING_B),
            )
            if terminal_stage is not Stage.TERMINAL_NEGATIVE_MAPPING:
                raise RunnerError("mapping failure selected the wrong terminal stage")
            children = [
                file_record(path)
                for path in sorted(FORMAL_MAPPING_ROOT.rglob("*"))
                if path.is_file()
                and not path.is_symlink()
                and not path.name.endswith("writer.lock")
            ]
            corpus = _formal_document(
                kind="mapping_corpus",
                lock_path=lock_target,
                lock=lock,
                raw_children=children,
                upstream_identities={
                    "bounded_cover_selection": selection["document_digest"],
                    "mapping_failure_batch": pass_document["document_digest"],
                },
                payload={
                    "status": "FT-BLOCKED-MAPPING",
                    "failure": "reproducible_required_mapping_code_generation",
                    "k": selection["payload"]["k"],
                    "selection": selection["payload"],
                    "failed_pass": pass_id,
                    "failure_batch": pass_document["payload"],
                    "toolchain_binding": lock["runtime_binding"]["toolchain"],
                    "pass_b_activated": pass_id == "B",
                },
            )
            _write_or_match_json(MAPPING_PATH, corpus)
            decision = _terminal_decision(
                lock_path=lock_target,
                lock=lock,
                scientific_outcome="negative",
                criterion="S1_ENTRY_BLOCKED",
                failure_id="FT-BLOCKED-MAPPING",
                edge=None,
                evidence={"mapping_corpus": corpus["document_digest"]},
                raw_children=children,
            )
            return {
                "checkpoint_id": "S10R3",
                "status": "TERMINAL_NEGATIVE_MAPPING",
                "decision_digest": decision["document_digest"],
            }
        if pass_document["document_kind"] != "mapping_pass":
            raise RunnerError("mapping worker returned an unknown document kind")
        if pass_id == "A":
            return {
                "checkpoint_id": "S10R3",
                "status": "MAPPING_A_COMPLETE",
                "row_count": pass_document["payload"]["row_count"],
                "pass_digest": pass_document["document_digest"],
            }
        pass_a = _mapping_pass("A")
        try:
            parity = verify_mapping_parity(
                pass_a["payload"]["rows"],
                pass_document["payload"]["rows"],
                k=selection["payload"]["k"],
            )
            parity_status = "PASS"
            failure = None
        except MappingError as error:
            parity = None
            parity_status = "FAIL"
            failure = str(error)
        children = [
            file_record(path)
            for path in sorted(FORMAL_MAPPING_ROOT.rglob("*"))
            if path.is_file()
            and not path.is_symlink()
            and not path.name.endswith("writer.lock")
        ]
        corpus = _formal_document(
            kind="mapping_corpus",
            lock_path=lock_target,
            lock=lock,
            raw_children=children,
            upstream_identities={
                "bounded_cover_selection": selection["document_digest"]
            },
            payload={
                "status": parity_status,
                "failure": failure,
                "k": selection["payload"]["k"],
                "selection": selection["payload"],
                "pass_a": pass_a["payload"],
                "pass_b": pass_document["payload"],
                "parity": parity,
            },
        )
        _write_or_match_json(MAPPING_PATH, corpus)
        if parity_status == "FAIL":
            decision = _terminal_decision(
                lock_path=lock_target,
                lock=lock,
                scientific_outcome="negative",
                criterion="S1_ENTRY_BLOCKED",
                failure_id="FT-BLOCKED-MAPPING",
                edge=None,
                evidence={"mapping_corpus": corpus["document_digest"]},
                raw_children=children,
            )
            return {
                "checkpoint_id": "S10R3",
                "status": "TERMINAL_NEGATIVE_MAPPING",
                "decision_digest": decision["document_digest"],
            }
    return {
        "checkpoint_id": "S10R3",
        "status": "MAPPING_B_PARITY_PASS",
        "row_count_per_pass": pass_document["payload"]["row_count"],
        "mapping_corpus_digest": corpus["document_digest"],
    }
def _native_fixture_input(fixture: Mapping[str, Any]) -> bytes:
    validate_fixture(fixture)
    lines = [
        f"{fixture['input_header']['row_count']} "
        f"{fixture['input_header']['threshold_count']}"
    ]
    for threshold in fixture["thresholds"]:
        lines.append(f"{threshold:.1f} {threshold:.1f}")
    problem = fixture["problem"]
    ordered_fields = (
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

    def flatten(value: Any) -> list[str]:
        if type(value) is bool:
            return ["1" if value else "0"]
        if type(value) is int:
            return [str(value)]
        if type(value) is list and all(type(item) is int for item in value):
            return [str(item) for item in value]
        raise RunnerError("native fixture contains an unsupported typed value")

    for row in fixture["rows"]:
        mapping = copy.deepcopy(fixture["base_size_mapping"])
        mapping.update(row["mapping_overrides"])
        fields = [
            str(row["ordinal"]),
            "1" if row["check_solution"] else "0",
            str(problem["M"]),
            str(problem["N"]),
            str(problem["NumBatches"]),
            str(problem["K"]),
        ]
        for field in ordered_fields:
            fields.extend(flatten(mapping[field]))
        if len(fields) != 40:
            raise RunnerError("native fixture input field count drift")
        lines.append(" ".join(fields))
    return ("\n".join(lines) + "\n").encode("ascii")


def _native_binding(
    lock: Mapping[str, Any], native_manifest: Mapping[str, Any]
) -> NativeBinding:
    identities = {
        item["id"]: item["identity"]
        for item in lock["input_binding"]["source_and_yaml_identities"]
    }
    return NativeBinding(
        binary_path=native_manifest["binary_path"],
        binary_sha256=native_manifest["binary_sha256"],
        cpp_source_path=native_manifest["cpp_source"]["path"],
        cpp_source_sha256=native_manifest["cpp_source"]["sha256"],
        host_adapter_path=native_manifest["host_adapter"]["path"],
        host_adapter_sha256=native_manifest["host_adapter"]["sha256"],
        formocast_source_blob=identities["native_formocast_source_blob"],
        formocast_header_blob=identities["native_formocast_header_blob"],
        runtime_source_blob=identities["runtime_queue_source_blob"],
        runtime_header_blob=identities["runtime_queue_header_blob"],
    )


@_serialized_formal(FORMAL_NATIVE_ROOT)
def native_conformance_command(lock_path: Path | str) -> dict[str, Any]:
    lock = _require_formal(lock_path)
    lock_target = Path(lock_path).resolve()
    _assert_no_terminal()
    mapping = _load_formal_document(
        MAPPING_PATH,
        kind="mapping_corpus",
        lock_path=lock_target,
        lock=lock,
    )
    if mapping["payload"]["status"] != "PASS":
        raise RunnerError("native conformance requires mapping parity PASS")
    fixture = strict_load_json(SENTINEL_FIXTURE_PATH)
    native_manifest = strict_load_json(NATIVE_BUILD_MANIFEST_PATH)
    native_body = dict(native_manifest)
    recorded_native = native_body.pop("build_manifest_digest", None)
    if recorded_native != canonical_sha256(native_body):
        raise RunnerError("native build manifest digest drift")
    with _FormalWriter(FORMAL_NATIVE_ROOT / ".writer.lock"):
        input_path = FORMAL_NATIVE_ROOT / "cohort-input.txt"
        transcript_path = FORMAL_NATIVE_ROOT / "native-transcript.json"
        expected_input = _native_fixture_input(fixture)
        if input_path.exists():
            if input_path.read_bytes() != expected_input:
                raise RunnerError("existing native input differs from fixture")
        else:
            _atomic_write_bytes(input_path, expected_input)
        if SENTINEL_CONFORMANCE_PATH.exists():
            document = _load_formal_document(
                SENTINEL_CONFORMANCE_PATH,
                kind="sentinel_conformance",
                lock_path=lock_target,
                lock=lock,
            )
            return {
                "checkpoint_id": "S10R3",
                "status": "NATIVE_CONFORMANCE_PASS",
                "document_digest": document["document_digest"],
                "recovered": True,
            }
        if transcript_path.exists():
            raise RunnerError(
                "uncommitted native transcript requires independent inspection"
            )
        binding = _native_binding(lock, native_manifest)
        adapter = PinnedNativeFormocastRuntimeAdapter(
            binding, repository_root=ROOT
        )
        invocation = adapter.invoke(
            lock=lock,
            fixture=fixture,
            input_path=input_path,
            output_path=transcript_path,
            locked_ready=True,
        )
        stdout_path = FORMAL_NATIVE_ROOT / "native.stdout"
        stderr_path = FORMAL_NATIVE_ROOT / "native.stderr"
        _atomic_write_bytes(stdout_path, invocation.pop("stdout_text").encode())
        _atomic_write_bytes(stderr_path, invocation.pop("stderr_text").encode())
        faults = {}
        fault_bindings = {
            "native_helper_binary_or_path": replace(
                binding, binary_sha256="0" * 64
            ),
            "source_blob_or_guard_order": replace(
                binding, formocast_source_blob="0" * 40
            ),
            "host_adapter": replace(binding, host_adapter_sha256="0" * 64),
        }
        for fault_id, fault_binding in fault_bindings.items():
            rejected = False
            try:
                PinnedNativeFormocastRuntimeAdapter(
                    fault_binding, repository_root=ROOT
                ).validate_binding(lock)
            except Exception:
                rejected = True
            assert_fault_rejected(fault_id, rejected)
            faults[fault_id] = {"rejected": True}
        substituted = copy.deepcopy(invocation["transcript"])
        substituted["queues"]["0.0"]["queue_prefix"] = [2]
        rejected = False
        try:
            compare_native_transcript(fixture, substituted)
        except Exception:
            rejected = True
        assert_fault_rejected(
            "runtime_check_solution_or_queue_semantics", rejected
        )
        faults["runtime_check_solution_or_queue_semantics"] = {"rejected": True}
        fault_path = FORMAL_NATIVE_ROOT / "substitution-faults.json"
        fault_document = _raw_document(
            "native_substitution_faults",
            {
                "fault_count": 4,
                "faults": faults,
                "all_rejected": True,
            },
        )
        atomic_write_json(fault_path, fault_document, exclusive=True)
        children = [
            file_record(path)
            for path in sorted(FORMAL_NATIVE_ROOT.rglob("*"))
            if path.is_file()
            and not path.is_symlink()
            and not path.name.endswith("writer.lock")
        ]
        document = _formal_document(
            kind="sentinel_conformance",
            lock_path=lock_target,
            lock=lock,
            raw_children=children,
            upstream_identities={
                "mapping_corpus": mapping["document_digest"],
                "native_build_manifest": native_manifest[
                    "build_manifest_digest"
                ],
            },
            payload={
                "status": "PASS",
                "fixture_digest": fixture["fixture_digest"],
                "native_transcript": invocation["transcript"],
                "expected_transcript": expected_native_transcript(fixture),
                "invocation": invocation,
                "faults": faults,
                "native_path_called": True,
                "runtime_check_solution_called": True,
                "runtime_pre_problem_called": True,
            },
        )
        atomic_write_json(SENTINEL_CONFORMANCE_PATH, document, exclusive=True)
    return {
        "checkpoint_id": "S10R3",
        "status": "NATIVE_CONFORMANCE_PASS",
        "document_digest": document["document_digest"],
        "recovered": False,
    }


def _require_gpu_surface() -> None:
    if not Path("/.dockerenv").exists() or ROOT != Path("/src/rocm-libraries"):
        raise RunnerError("formal GPU operation requires the perlee container mount")
    if not Path("/dev/kfd").exists():
        raise RunnerError("formal GPU operation requires the ROCm KFD device")


def _gpu_snapshot() -> dict[str, Any]:
    command = [
        "/opt/rocm/bin/rocm-smi",
        "--showproductname",
        "--showuniqueid",
        "--showserial",
        "--showuse",
        "--showmemuse",
        "--showcomputepartition",
        "--showmemorypartition",
        "--json",
    ]
    completed = subprocess.run(
        command,
        env=FORMAL_ENVIRONMENT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    if completed.returncode:
        raise RunnerError("ROCm-SMI allocation snapshot failed")
    try:
        devices = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RunnerError("ROCm-SMI allocation snapshot is not strict JSON") from error
    if type(devices) is not dict or not devices:
        raise RunnerError("ROCm-SMI allocation snapshot has no devices")
    return {
        "command": command,
        "returncode": completed.returncode,
        "devices": devices,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }


def _visible_physical_gpu_indices(snapshot: Mapping[str, Any]) -> list[int]:
    indices = sorted(
        int(name[4:])
        for name in snapshot.get("devices", {})
        if type(name) is str and name.startswith("card") and name[4:].isdigit()
    )
    if not indices:
        raise RunnerError("ROCm-SMI snapshot contains no physical cards")
    return indices


def _parse_gpu_pid_output(
    stdout: str, *, visible_indices: Sequence[int]
) -> dict[str, list[int]]:
    visible = set(visible_indices)
    if len(visible) != len(visible_indices):
        raise RunnerError("visible GPU index set is ambiguous")
    result = {str(index): [] for index in sorted(visible)}
    lines = [
        line.strip()
        for line in stdout.splitlines()
        if line.strip() and not line.startswith("=")
    ]
    if lines == ["No KFD PIDs currently running"]:
        return result
    if not lines or "No KFD PIDs currently running" in lines:
        raise RunnerError("ROCm-SMI PID output is incomplete")
    pid_pattern = re.compile(
        r"^PID ([1-9][0-9]*) is using ([1-9][0-9]*) DRM device\(s\):$"
    )
    device_pattern = re.compile(r"^[0-9]+(?:\s+[0-9]+)*$")
    seen = set()
    cursor = 0
    while cursor < len(lines):
        match = pid_pattern.fullmatch(lines[cursor])
        if match is None or cursor + 1 >= len(lines):
            raise RunnerError("ROCm-SMI PID output contains an unparsed record")
        pid = int(match.group(1))
        count = int(match.group(2))
        if device_pattern.fullmatch(lines[cursor + 1]) is None:
            raise RunnerError("ROCm-SMI PID device list is malformed")
        device_indices = [int(value) for value in lines[cursor + 1].split()]
        if (
            pid in seen
            or len(device_indices) != count
            or len(set(device_indices)) != count
            or any(index not in visible for index in device_indices)
        ):
            raise RunnerError("ROCm-SMI PID/device mapping is ambiguous")
        seen.add(pid)
        for index in device_indices:
            result[str(index)].append(pid)
        cursor += 2
    return result


def _gpu_process_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    command = ["/opt/rocm/bin/rocm-smi", "--showpidgpus"]
    completed = subprocess.run(
        command,
        env=FORMAL_ENVIRONMENT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    if completed.returncode or completed.stderr.strip():
        raise RunnerError("ROCm-SMI process snapshot failed or emitted diagnostics")
    stdout = completed.stdout.decode("utf-8", errors="strict")
    visible = _visible_physical_gpu_indices(snapshot)
    mapping = _parse_gpu_pid_output(stdout, visible_indices=visible)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": stdout,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        "visible_physical_device_indices": visible,
        "physical_device_pids": mapping,
    }


def _select_idle_gfx942(
    snapshot: Mapping[str, Any], processes: Mapping[str, Any]
) -> tuple[int, dict[str, Any]]:
    candidates = []
    for name, raw in snapshot["devices"].items():
        if (
            type(name) is str
            and name.startswith("card")
            and name[4:].isdigit()
            and type(raw) is dict
        ):
            index = int(name[4:])
            pids = processes["physical_device_pids"].get(str(index))
            if (
                raw.get("GFX Version") == "gfx942"
                and raw.get("Compute Partition") == "SPX"
                and raw.get("Memory Partition") == "NPS1"
                and raw.get("GPU use (%)") == "0"
                and raw.get("GPU Memory Allocated (VRAM%)") == "0"
                and pids == []
            ):
                candidates.append((index, raw))
    if not candidates:
        raise RunnerError("no currently idle eligible gfx942 SPX/NPS1 card")
    return min(candidates, key=lambda item: item[0])


def _gpu_environment_document() -> dict[str, Any]:
    return _load_raw_document(
        FORMAL_GPU_ROOT / "gpu-environment.json", "gpu_environment"
    )


def _assert_gpu_idle(environment: Mapping[str, Any]) -> dict[str, Any]:
    snapshot = _gpu_snapshot()
    processes = _gpu_process_snapshot(snapshot)
    selected = environment["payload"]["selected_device"]
    index = selected["physical_visible_index"]
    device = snapshot["devices"].get(f"card{index}")
    expected = {
        "Unique ID": selected["unique_id"],
        "Serial Number": selected["serial_number"],
        "GFX Version": "gfx942",
        "Compute Partition": "SPX",
        "Memory Partition": "NPS1",
        "GPU use (%)": "0",
        "GPU Memory Allocated (VRAM%)": "0",
    }
    if type(device) is not dict or any(
        device.get(key) != value for key, value in expected.items()
    ):
        raise RunnerError("selected GPU is no longer identical and idle")
    if processes["physical_device_pids"].get(str(index)) != []:
        raise RunnerError("selected GPU has a foreign PID immediately before cell")
    return {"allocation": snapshot, "processes": processes}


@_serialized_formal(FORMAL_GPU_ROOT)
def gpu_environment_command(lock_path: Path | str) -> dict[str, Any]:
    lock = _require_formal(lock_path)
    lock_target = Path(lock_path).resolve()
    _assert_no_terminal()
    _require_gpu_surface()
    conformance = _load_formal_document(
        SENTINEL_CONFORMANCE_PATH,
        kind="sentinel_conformance",
        lock_path=lock_target,
        lock=lock,
    )
    with _FormalWriter(FORMAL_GPU_ROOT / ".writer.lock"):
        path = FORMAL_GPU_ROOT / "gpu-environment.json"
        if path.exists():
            environment = _gpu_environment_document()
            return {
                "checkpoint_id": "S10R3",
                "status": "GPU_ENVIRONMENT_PASS",
                "selected_device": environment["payload"]["selected_device"],
                "recovered": True,
            }
        snapshot = _gpu_snapshot()
        processes = _gpu_process_snapshot(snapshot)
        index, device = _select_idle_gfx942(snapshot, processes)
        environment = _raw_document(
            "gpu_environment",
            {
                "status": "PASS",
                "container_mount": str(ROOT),
                "selection_rule": (
                    "lowest currently free gfx942 SPX/NPS1 card with zero use, "
                    "zero VRAM allocation and no foreign PID"
                ),
                "selected_device": {
                    "physical_visible_index": index,
                    "logical_device_index": 0,
                    "unique_id": device["Unique ID"],
                    "serial_number": device["Serial Number"],
                    "gfx_version": device["GFX Version"],
                    "compute_partition": device["Compute Partition"],
                    "memory_partition": device["Memory Partition"],
                },
                "allocation_snapshot": snapshot,
                "process_snapshot": processes,
                "upstream_sentinel_conformance": conformance[
                    "document_digest"
                ],
                "captured_at_utc": _utc_now(),
            },
        )
        atomic_write_json(path, environment, exclusive=True)
    return {
        "checkpoint_id": "S10R3",
        "status": "GPU_ENVIRONMENT_PASS",
        "selected_device": environment["payload"]["selected_device"],
        "recovered": False,
    }


def _plain(value: Any) -> Any:
    if value is None or type(value) in (str, bool, int, float):
        return value
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    raise RunnerError(f"unsupported YAML value type: {type(value).__name__}")


def _singleton_yaml_bytes(
    *,
    candidate: Mapping[str, Any],
    size: Sequence[int],
    device_index: int,
) -> bytes:
    config = copy.deepcopy(strict_load_yaml(ACTUAL_YAML))
    config.pop("Backend", None)
    problem_group = config["BenchmarkProblems"][0][1]
    flattened: dict[str, Any] = {}
    for axis, value in candidate.items():
        if not axis.startswith("group_"):
            flattened[axis] = _plain(value)
    grouped = sorted(
        (
            (int(axis.split("_", 1)[1]), value)
            for axis, value in candidate.items()
            if axis.startswith("group_")
        ),
        key=lambda item: item[0],
    )
    for _, group in grouped:
        if type(group) is not dict:
            raise RunnerError("grouped candidate must resolve to an object")
        flattened.update({str(key): _plain(value) for key, value in group.items()})
    problem_group["ForkParameters"] = [
        {name: [value]} for name, value in flattened.items()
    ]
    finals = problem_group["BenchmarkFinalParameters"]
    size_slots = [
        index
        for index, entry in enumerate(finals)
        if type(entry) is dict and "ProblemSizes" in entry
    ]
    if size_slots != [0]:
        raise RunnerError("actual YAML has an unexpected final size slot")
    finals[0] = {"ProblemSizes": [{"Exact": [int(value) for value in size]}]}
    globals_ = config["GlobalParameters"]
    globals_["NumElementsToValidate"] = 128
    globals_["ExitOnFails"] = 2
    globals_["Device"] = int(device_index)
    globals_["KeepBuildTmp"] = True
    return yaml.safe_dump(
        _plain(config),
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=4096,
    ).encode("utf-8")


def _benchmark_csv_row(
    output_root: Path, expected_size: Sequence[int]
) -> tuple[Path, dict[str, Any]]:
    candidates = sorted(output_root.glob("**/Data/*.csv"))
    if len(candidates) != 1:
        raise RunnerError(f"expected one benchmark CSV, found {len(candidates)}")
    with candidates[0].open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 1:
        raise RunnerError("benchmark CSV must contain exactly one size row")
    raw = rows[0]
    try:
        observed_size = [int(raw[f"Size{letter}"]) for letter in "IJKL"]
        timing = float(raw["WinnerTimeUS"])
        quality = float(raw["WinnerGFlops"])
    except (KeyError, TypeError, ValueError) as error:
        raise RunnerError("benchmark CSV is malformed") from error
    if (
        observed_size != list(expected_size)
        or not math.isfinite(timing)
        or not math.isfinite(quality)
        or timing <= 0
        or quality <= 0
    ):
        raise RunnerError("benchmark CSV size/timing/quantity mismatch")
    return candidates[0], {
        "size": observed_size,
        "timing_us": timing,
        "quantity": quality,
    }


def _find_generated_runtime(output_root: Path) -> tuple[Path, Path, list[Path]]:
    code_objects = sorted(output_root.glob("**/*.co"))
    configs = sorted(output_root.glob("**/*ClientParameters*.ini"))
    clients = sorted(
        path
        for path in output_root.rglob("client-benchmarks")
        if path.is_file() and os.access(path, os.X_OK)
    )
    if not code_objects or len(configs) != 1 or len(clients) != 1:
        raise RunnerError(
            "successful correctness cell lacks unique code objects/client/config"
        )
    return clients[0], configs[0], code_objects


def _run_correctness_attempt(
    *,
    config_hash: str,
    config: Mapping[str, Any],
    size: Mapping[str, Any],
    attempt_root: Path,
    environment: Mapping[str, Any],
    attempt: int,
) -> dict[str, Any]:
    if attempt_root.exists():
        raise RunnerError("correctness attempt output already exists")
    attempt_root.mkdir(parents=True)
    preflight = _assert_gpu_idle(environment)
    config_path = attempt_root / "singleton.yaml"
    output_root = attempt_root / "output"
    _atomic_write_bytes(
        config_path,
        _singleton_yaml_bytes(
            candidate=config,
            size=size["value"],
            device_index=0,
        ),
    )
    command = [
        "/opt/venv/bin/python3",
        str(
            PRELABEL_BUILD_ROOT
            / "pinned-source/projects/hipblaslt/tensilelite/Tensile/bin/Tensile"
        ),
        str(config_path),
        str(output_root),
        "--device",
        "0",
        "--gpu-targets",
        "gfx942",
        "--cxx-compiler",
        "/opt/rocm/bin/amdclang++",
        "--c-compiler",
        "/opt/rocm/bin/amdclang++",
        "--assembler",
        "/opt/rocm/bin/amdclang++",
        "--offload-bundler",
        "/opt/rocm/lib/llvm/bin/clang-offload-bundler",
    ]
    child_environment = {
        **FORMAL_ENVIRONMENT,
        "PYTHONPATH": str(
            PRELABEL_BUILD_ROOT / "pinned-source/projects/hipblaslt/tensilelite"
        ),
        "ROCR_VISIBLE_DEVICES": str(
            environment["payload"]["selected_device"]["physical_visible_index"]
        ),
    }
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    completed = subprocess.run(
        command,
        cwd=attempt_root,
        env=child_environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=7200,
    )
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    stdout_path = attempt_root / "stdout.log"
    stderr_path = attempt_root / "stderr.log"
    _atomic_write_bytes(stdout_path, completed.stdout)
    _atomic_write_bytes(stderr_path, completed.stderr)
    measurement = {
        "wall_s": time.monotonic() - started,
        "cpu_s": (
            after.ru_utime
            + after.ru_stime
            - before.ru_utime
            - before.ru_stime
        ),
        "gpu_s": time.monotonic() - started,
        "maximum_child_rss_kib": after.ru_maxrss,
    }
    if completed.returncode:
        payload = {
            "status": "FAIL",
            "failure_phase": "generate_compile_smoke_or_nonzero_correctness",
            "attempt": attempt,
            "config_hash": config_hash,
            "size_id": size["size_id"],
            "command": {
                "argv": command,
                "cwd": str(attempt_root.relative_to(ROOT)),
                "environment": child_environment,
                "returncode": completed.returncode,
                "stdout_sha256": sha256_file(stdout_path),
                "stderr_sha256": sha256_file(stderr_path),
            },
            "preflight": preflight,
            "measurement": measurement,
        }
        return _raw_document("correctness_attempt", payload)
    result_path, result = _benchmark_csv_row(output_root, size["value"])
    client, client_config, code_objects = _find_generated_runtime(output_root)
    payload = {
        "status": "PASS",
        "failure_phase": None,
        "attempt": attempt,
        "config_hash": config_hash,
        "size_id": size["size_id"],
        "size": list(size["value"]),
        "generate": True,
        "compile": True,
        "smoke": True,
        "nonzero_correctness": True,
        "validation_elements": 128,
        "timing_us": result["timing_us"],
        "quantity": result["quantity"],
        "result_path": str(result_path.relative_to(ROOT)),
        "result_sha256": sha256_file(result_path),
        "client_path": str(client.relative_to(ROOT)),
        "client_sha256": sha256_file(client),
        "client_config_path": str(client_config.relative_to(ROOT)),
        "client_config_sha256": sha256_file(client_config),
        "code_objects": [file_record(path) for path in code_objects],
        "command": {
            "argv": command,
            "cwd": str(attempt_root.relative_to(ROOT)),
            "environment": child_environment,
            "returncode": completed.returncode,
            "stdout_sha256": sha256_file(stdout_path),
            "stderr_sha256": sha256_file(stderr_path),
        },
        "preflight": preflight,
        "measurement": measurement,
    }
    return _raw_document("correctness_attempt", payload)


def _formal_gpu_children() -> list[dict[str, Any]]:
    return [
        file_record(path)
        for path in sorted(FORMAL_GPU_ROOT.rglob("*"))
        if path.is_file()
        and not path.is_symlink()
        and not path.name.endswith("writer.lock")
    ]


def _load_or_run_correctness_attempt(
    *,
    cell_root: Path,
    logical_attempt: int,
    config_hash: str,
    config: Mapping[str, Any],
    size: Mapping[str, Any],
    environment: Mapping[str, Any],
) -> dict[str, Any]:
    completed = []
    for path in sorted(cell_root.glob("attempt-*/attempt.json")):
        document = _load_raw_document(path, "correctness_attempt")
        if document["payload"]["attempt"] == logical_attempt:
            completed.append(document)
    if len(completed) > 1:
        raise RunnerError("correctness logical attempt has duplicate completions")
    if completed:
        return completed[0]
    base_name = f"attempt-{logical_attempt:02d}"
    attempt_root = cell_root / base_name
    retry = 0
    while attempt_root.exists():
        retry += 1
        attempt_root = cell_root / f"{base_name}-retry-{retry:02d}"
    document = _run_correctness_attempt(
        config_hash=config_hash,
        config=config,
        size=size,
        attempt_root=attempt_root,
        environment=environment,
        attempt=logical_attempt,
    )
    atomic_write_json(attempt_root / "attempt.json", document, exclusive=True)
    return document


@_serialized_formal(FORMAL_GPU_ROOT)
def correctness_command(lock_path: Path | str) -> dict[str, Any]:
    lock = _require_formal(lock_path)
    lock_target = Path(lock_path).resolve()
    _assert_no_terminal()
    _require_gpu_surface()
    environment = _gpu_environment_document()
    conformance = _load_formal_document(
        SENTINEL_CONFORMANCE_PATH,
        kind="sentinel_conformance",
        lock_path=lock_target,
        lock=lock,
    )
    mapping = _load_formal_document(
        MAPPING_PATH,
        kind="mapping_corpus",
        lock_path=lock_target,
        lock=lock,
    )
    selection = mapping["payload"]["selection"]
    hashes = selection["final_config_hashes"]
    anchors = anchor_hashes(hashes)
    configs = {
        row["config_hash"]: row["config"]
        for row in selection["final_witnesses"]
    }
    cells = []
    with _FormalWriter(FORMAL_GPU_ROOT / ".writer.lock"):
        for anchor_index, config_hash in enumerate(anchors):
            for size in SIZES:
                cell_root = (
                    FORMAL_GPU_ROOT
                    / "correctness"
                    / f"{anchor_index:02d}-{size['size_id']}"
                )
                final_path = cell_root / "cell.json"
                if final_path.exists():
                    cell = _load_raw_document(final_path, "correctness_attempt")
                else:
                    first = _load_or_run_correctness_attempt(
                        cell_root=cell_root,
                        logical_attempt=1,
                        config_hash=config_hash,
                        config=configs[config_hash],
                        size=size,
                        environment=environment,
                    )
                    if first["payload"]["status"] == "PASS":
                        cell = first
                    else:
                        second = _load_or_run_correctness_attempt(
                            cell_root=cell_root,
                            logical_attempt=2,
                            config_hash=config_hash,
                            config=configs[config_hash],
                            size=size,
                            environment=environment,
                        )
                        if second["payload"]["status"] == "FAIL":
                            if (
                                second["payload"]["failure_phase"]
                                != first["payload"]["failure_phase"]
                            ):
                                raise RunnerError(
                                    "correctness failures are not reproducible"
                                )
                            children = _formal_gpu_children()
                            failure_summary = _formal_document(
                                kind="correctness",
                                lock_path=lock_target,
                                lock=lock,
                                raw_children=children,
                                upstream_identities={
                                    "mapping_corpus": mapping["document_digest"],
                                    "sentinel_conformance": conformance[
                                        "document_digest"
                                    ],
                                },
                                payload={
                                    "status": "FAIL",
                                    "failure_id": "FT-BLOCKED-CORRECTNESS",
                                    "failed_config_hash": config_hash,
                                    "failed_size_id": size["size_id"],
                                    "attempts": [
                                        first["document_digest"],
                                        second["document_digest"],
                                    ],
                                    "reproducible": True,
                                },
                            )
                            _write_or_match_json(
                                CORRECTNESS_PATH, failure_summary
                            )
                            decision = _terminal_decision(
                                lock_path=lock_target,
                                lock=lock,
                                scientific_outcome="negative",
                                criterion="S1_ENTRY_BLOCKED",
                                failure_id="FT-BLOCKED-CORRECTNESS",
                                edge=None,
                                evidence={
                                    "correctness": failure_summary[
                                        "document_digest"
                                    ]
                                },
                                raw_children=children,
                            )
                            return {
                                "checkpoint_id": "S10R3",
                                "status": "TERMINAL_NEGATIVE_CORRECTNESS",
                                "decision_digest": decision["document_digest"],
                            }
                        cell = second
                    atomic_write_json(final_path, cell, exclusive=True)
                if cell["payload"]["status"] != "PASS":
                    raise RunnerError("completed correctness cell is not passing")
                cells.append(
                    {
                        key: cell["payload"][key]
                        for key in (
                            "config_hash",
                            "size_id",
                            "generate",
                            "compile",
                            "smoke",
                            "nonzero_correctness",
                            "validation_elements",
                            "timing_us",
                            "quantity",
                            "result_sha256",
                            "client_sha256",
                            "client_config_sha256",
                        )
                    }
                )
        verified = verify_correctness_cells(hashes, cells)
        children = _formal_gpu_children()
        document = _formal_document(
            kind="correctness",
            lock_path=lock_target,
            lock=lock,
            raw_children=children,
            upstream_identities={
                "mapping_corpus": mapping["document_digest"],
                "sentinel_conformance": conformance["document_digest"],
                "gpu_environment": environment["document_digest"],
            },
            payload={"status": "PASS", **verified},
        )
        _write_or_match_json(CORRECTNESS_PATH, document)
    return {
        "checkpoint_id": "S10R3",
        "status": "CORRECTNESS_PASS",
        "cell_count": 9,
        "document_digest": document["document_digest"],
    }


def _rewrite_client_results(
    source: Path, destination: Path, result_path: Path
) -> None:
    lines = source.read_text(encoding="utf-8").splitlines()
    replaced = 0
    output = []
    for line in lines:
        if line.startswith("results-file="):
            output.append(f"results-file={result_path}")
            replaced += 1
        else:
            output.append(line)
    if replaced != 1:
        raise RunnerError("client config lacks one results-file setting")
    _atomic_write_bytes(destination, ("\n".join(output) + "\n").encode())


def _run_noise_observation(
    *,
    source_cell: Mapping[str, Any],
    repeat: int,
    output_root: Path,
    environment: Mapping[str, Any],
) -> dict[str, Any]:
    if output_root.exists():
        raise RunnerError("noise observation output already exists")
    output_root.mkdir(parents=True)
    preflight = _assert_gpu_idle(environment)
    source_config = ROOT / source_cell["client_config_path"]
    client = ROOT / source_cell["client_path"]
    if (
        sha256_file(source_config) != source_cell["client_config_sha256"]
        or sha256_file(client) != source_cell["client_sha256"]
    ):
        raise RunnerError("noise source client/config binding drift")
    result_path = output_root / "result.csv"
    config_path = output_root / "ClientParameters.ini"
    _rewrite_client_results(source_config, config_path, result_path)
    command = [str(client), "--config-file", str(config_path)]
    child_environment = {
        **FORMAL_ENVIRONMENT,
        "ROCR_VISIBLE_DEVICES": str(
            environment["payload"]["selected_device"]["physical_visible_index"]
        ),
    }
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    completed = subprocess.run(
        command,
        cwd=output_root,
        env=child_environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=3600,
    )
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    stdout_path = output_root / "stdout.log"
    stderr_path = output_root / "stderr.log"
    _atomic_write_bytes(stdout_path, completed.stdout)
    _atomic_write_bytes(stderr_path, completed.stderr)
    if completed.returncode:
        raise RunnerError("noise client failed; no observation was committed")
    result_file, result = _benchmark_csv_row(
        output_root, source_cell["size"]
    )
    payload = {
        "status": "PASS",
        "config_hash": source_cell["config_hash"],
        "size_id": source_cell["size_id"],
        "size": source_cell["size"],
        "repeat": repeat,
        "quantity": result["quantity"],
        "timing_us": result["timing_us"],
        "correctness": "pass",
        "result_sha256": sha256_file(result_file),
        "command": {
            "argv": command,
            "cwd": str(output_root.relative_to(ROOT)),
            "environment": child_environment,
            "returncode": completed.returncode,
            "stdout_sha256": sha256_file(stdout_path),
            "stderr_sha256": sha256_file(stderr_path),
        },
        "preflight": preflight,
        "measurement": {
            "wall_s": time.monotonic() - started,
            "cpu_s": (
                after.ru_utime
                + after.ru_stime
                - before.ru_utime
                - before.ru_stime
            ),
            "gpu_s": time.monotonic() - started,
            "maximum_child_rss_kib": after.ru_maxrss,
        },
    }
    return _raw_document("noise_observation", payload)


def _load_or_run_noise_observation(
    *,
    slot_root: Path,
    source_cell: Mapping[str, Any],
    repeat: int,
    environment: Mapping[str, Any],
) -> dict[str, Any]:
    final_path = slot_root / "observation.json"
    if final_path.exists():
        return _load_raw_document(final_path, "noise_observation")
    completed = []
    for path in sorted(slot_root.glob("attempt-*/attempt.json")):
        completed.append(_load_raw_document(path, "noise_observation"))
    if len(completed) > 1:
        raise RunnerError("noise slot has duplicate completed observations")
    if completed:
        document = completed[0]
    else:
        attempt = 1
        attempt_root = slot_root / f"attempt-{attempt:02d}"
        while attempt_root.exists():
            attempt += 1
            attempt_root = slot_root / f"attempt-{attempt:02d}"
        document = _run_noise_observation(
            source_cell=source_cell,
            repeat=repeat,
            output_root=attempt_root,
            environment=environment,
        )
        atomic_write_json(
            attempt_root / "attempt.json", document, exclusive=True
        )
    atomic_write_json(final_path, document, exclusive=True)
    return document


@_serialized_formal(FORMAL_GPU_ROOT)
def noise_command(lock_path: Path | str) -> dict[str, Any]:
    lock = _require_formal(lock_path)
    lock_target = Path(lock_path).resolve()
    _assert_no_terminal()
    _require_gpu_surface()
    correctness = _load_formal_document(
        CORRECTNESS_PATH,
        kind="correctness",
        lock_path=lock_target,
        lock=lock,
    )
    if correctness["payload"]["status"] != "PASS":
        raise RunnerError("noise requires all nine correctness cells passing")
    mapping = _load_formal_document(
        MAPPING_PATH,
        kind="mapping_corpus",
        lock_path=lock_target,
        lock=lock,
    )
    hashes = mapping["payload"]["selection"]["final_config_hashes"]
    anchors = anchor_hashes(hashes)
    environment = _gpu_environment_document()
    observations = []
    with _FormalWriter(FORMAL_GPU_ROOT / ".writer.lock"):
        for anchor_index, config_hash in enumerate(anchors):
            for size in SIZES:
                cell = _load_raw_document(
                    FORMAL_GPU_ROOT
                    / "correctness"
                    / f"{anchor_index:02d}-{size['size_id']}/cell.json",
                    "correctness_attempt",
                )["payload"]
                if (
                    cell.get("config_hash") != config_hash
                    or cell.get("size_id") != size["size_id"]
                ):
                    raise RunnerError("noise source correctness cell mismatch")
                for repeat in range(7):
                    root = (
                        FORMAL_GPU_ROOT
                        / "noise"
                        / f"{anchor_index:02d}-{size['size_id']}-{repeat:02d}"
                    )
                    observation = _load_or_run_noise_observation(
                        slot_root=root,
                        source_cell=cell,
                        repeat=repeat,
                        environment=environment,
                    )
                    observations.append(
                        {
                            key: observation["payload"][key]
                            for key in (
                                "config_hash",
                                "size_id",
                                "repeat",
                                "quantity",
                            )
                        }
                    )
        verified = validate_noise_cells(hashes, observations)
        children = _formal_gpu_children()
        document = _formal_document(
            kind="noise",
            lock_path=lock_target,
            lock=lock,
            raw_children=children,
            upstream_identities={
                "correctness": correctness["document_digest"],
                "mapping_corpus": mapping["document_digest"],
            },
            payload={"status": "PASS", **verified},
        )
        _write_or_match_json(NOISE_PATH, document)
        if not verified["stable"]:
            decision = _terminal_decision(
                lock_path=lock_target,
                lock=lock,
                scientific_outcome="inconclusive",
                criterion="FT-INCONCLUSIVE",
                failure_id="noise_instability",
                edge=None,
                evidence={"noise": document["document_digest"]},
                raw_children=children,
            )
            return {
                "checkpoint_id": "S10R3",
                "status": "TERMINAL_INCONCLUSIVE",
                "decision_digest": decision["document_digest"],
            }
    return {
        "checkpoint_id": "S10R3",
        "status": "NOISE_PASS",
        "observation_count": 63,
        "cv_p95": verified["cv_p95"],
        "document_digest": document["document_digest"],
    }


def _all_reached_raw_children() -> list[dict[str, Any]]:
    records = []
    for root in (
        FORMAL_CPU_ROOT,
        FORMAL_MAPPING_ROOT,
        FORMAL_NATIVE_ROOT,
        FORMAL_GPU_ROOT,
    ):
        if os.path.lexists(root):
            root = _ordinary_directory(root, label="formal raw-child root")
            descendants = list(root.rglob("*"))
            if any(path.is_symlink() for path in descendants):
                raise RunnerError("formal raw-child tree contains symlink")
            if any(
                not path.is_dir() and not path.is_file() for path in descendants
            ):
                raise RunnerError("formal raw-child tree contains nonordinary entry")
            records.extend(
                file_record(path)
                for path in sorted(descendants)
                if path.is_file()
                and not path.name.endswith("writer.lock")
            )
    paths = [item["path"] for item in records]
    if len(paths) != len(set(paths)):
        raise RunnerError("reached raw child path set is duplicated")
    return records


@_serialized_formal(FORMAL_GPU_ROOT)
def decision_command(lock_path: Path | str) -> dict[str, Any]:
    lock = _require_formal(lock_path)
    lock_target = Path(lock_path).resolve()
    if DECISION_PATH.exists():
        decision = _load_formal_document(
            DECISION_PATH,
            kind="decision",
            lock_path=lock_target,
            lock=lock,
        )
        return {
            "checkpoint_id": "S10R3",
            "status": "DECISION_ALREADY_TERMINAL",
            "scientific_outcome": decision["payload"]["scientific_outcome"],
            "edge": decision["payload"]["edge"],
            "document_digest": decision["document_digest"],
        }
    noise = _load_formal_document(
        NOISE_PATH,
        kind="noise",
        lock_path=lock_target,
        lock=lock,
    )
    correctness = _load_formal_document(
        CORRECTNESS_PATH,
        kind="correctness",
        lock_path=lock_target,
        lock=lock,
    )
    mapping = _load_formal_document(
        MAPPING_PATH,
        kind="mapping_corpus",
        lock_path=lock_target,
        lock=lock,
    )
    conformance = _load_formal_document(
        SENTINEL_CONFORMANCE_PATH,
        kind="sentinel_conformance",
        lock_path=lock_target,
        lock=lock,
    )
    if (
        mapping["payload"]["status"] != "PASS"
        or conformance["payload"]["status"] != "PASS"
        or correctness["payload"]["status"] != "PASS"
        or noise["payload"]["status"] != "PASS"
        or noise["payload"]["stable"] is not True
    ):
        raise RunnerError("positive decision criteria are not all satisfied")
    children = _all_reached_raw_children()
    decision = _terminal_decision(
        lock_path=lock_target,
        lock=lock,
        scientific_outcome="positive",
        criterion="S1_ENTRY_GO",
        failure_id=None,
        edge="S11",
        evidence={
            "mapping_corpus": mapping["document_digest"],
            "sentinel_conformance": conformance["document_digest"],
            "correctness": correctness["document_digest"],
            "noise": noise["document_digest"],
        },
        raw_children=children,
    )
    gate = _formal_document(
        kind="positive_gate_record",
        lock_path=lock_target,
        lock=lock,
        raw_children=children,
        upstream_identities={"decision": decision["document_digest"]},
        payload={
            "criterion": "S1_ENTRY_GO",
            "edge": "S11",
            "activation_authority": "Main closeout only",
            "activation_status": "pending_fresh_verification_and_closeout",
            "s11_written": False,
        },
    )
    _write_or_match_json(GATE_RECORD_PATH, gate)
    return {
        "checkpoint_id": "S10R3",
        "status": "TERMINAL_POSITIVE",
        "scientific_outcome": "positive",
        "edge": "S11",
        "decision_digest": decision["document_digest"],
        "gate_record_digest": gate["document_digest"],
    }


def _reconstruct_reached_outcome(
    lock_path: Path, lock: Mapping[str, Any]
) -> dict[str, Any]:
    decision = _load_formal_document(
        DECISION_PATH,
        kind="decision",
        lock_path=lock_path,
        lock=lock,
    )
    payload = decision["payload"]
    outcome = payload["scientific_outcome"]
    failure_id = payload["failure_id"]
    required_raw_child_paths: set[str] = set()
    if outcome == "positive":
        mapping = _load_formal_document(
            MAPPING_PATH,
            kind="mapping_corpus",
            lock_path=lock_path,
            lock=lock,
        )
        parity = verify_mapping_parity(
            mapping["payload"]["pass_a"]["rows"],
            mapping["payload"]["pass_b"]["rows"],
            k=mapping["payload"]["k"],
        )
        if parity["parity"] is not True:
            raise RunnerError("reproduction mapping parity failed")
        fixture = strict_load_json(SENTINEL_FIXTURE_PATH)
        conformance = _load_formal_document(
            SENTINEL_CONFORMANCE_PATH,
            kind="sentinel_conformance",
            lock_path=lock_path,
            lock=lock,
        )
        compare_native_transcript(
            fixture, conformance["payload"]["native_transcript"]
        )
        correctness = _load_formal_document(
            CORRECTNESS_PATH,
            kind="correctness",
            lock_path=lock_path,
            lock=lock,
        )
        hashes = mapping["payload"]["selection"]["final_config_hashes"]
        rebuilt_correctness = verify_correctness_cells(
            hashes, correctness["payload"]["cells"]
        )
        noise = _load_formal_document(
            NOISE_PATH,
            kind="noise",
            lock_path=lock_path,
            lock=lock,
        )
        raw_observations = []
        for path in sorted((FORMAL_GPU_ROOT / "noise").glob("*/observation.json")):
            item = _load_raw_document(path, "noise_observation")["payload"]
            raw_observations.append(
                {
                    key: item[key]
                    for key in ("config_hash", "size_id", "repeat", "quantity")
                }
            )
        rebuilt_noise = validate_noise_cells(hashes, raw_observations)
        if (
            rebuilt_correctness["summary_digest"]
            != correctness["payload"]["summary_digest"]
            or rebuilt_noise["summary_digest"]
            != noise["payload"]["summary_digest"]
            or rebuilt_noise["stable"] is not True
        ):
            raise RunnerError("positive raw-evidence reconstruction differs")
    elif failure_id in {
        "fresh_distinct_valid_witnesses_less_than_10",
        "greedy_does_not_cover_all_mandatory_atoms",
        "c_greedy_greater_than_20",
    }:
        registry = _verify_registry(strict_load_json(REGISTRY_PATH))
        support = _support_document(lock_path, lock)
        witnesses, _, _, _ = _discovery_evidence(registry)
        classifications = {
            atom_id: SupportState(value)
            for atom_id, value in support["payload"]["classifications"].items()
        }
        rebuilt = deterministic_greedy_bounded_cover(
            registry, classifications, witnesses
        )
        if rebuilt.status != "inconclusive" or rebuilt.failure_reason != failure_id:
            raise RunnerError("selection-inconclusive outcome did not reproduce")
    elif failure_id == "FT-BLOCKED-MAPPING":
        mapping = _load_formal_document(
            MAPPING_PATH,
            kind="mapping_corpus",
            lock_path=lock_path,
            lock=lock,
        )
        mapping_payload = mapping["payload"]
        if mapping_payload["status"] == "FT-BLOCKED-MAPPING":
            batch = mapping_payload["failure_batch"]
            selection = mapping_payload["selection"]
            expected_configs = [
                row["config"] for row in selection["final_witnesses"]
            ]
            expected_hashes = [
                canonical_sha256(dict(config)) for config in expected_configs
            ]
            failed_pass = mapping_payload["failed_pass"]
            if (
                set(mapping_payload)
                != {
                    "status",
                    "failure",
                    "k",
                    "selection",
                    "failed_pass",
                    "failure_batch",
                    "toolchain_binding",
                    "pass_b_activated",
                }
                or set(batch)
                != {
                    "status",
                    "pass_id",
                    "k",
                    "complete",
                    "reproducible",
                    "attempt_count",
                    "request_path",
                    "request_sha256",
                    "config_hashes",
                    "failure",
                    "attempts",
                    "worker_binding",
                }
                or batch["status"] != "FT-BLOCKED-MAPPING"
                or mapping_payload["failure"]
                != "reproducible_required_mapping_code_generation"
                or batch["pass_id"] != failed_pass
                or batch["complete"] is not True
                or batch["reproducible"] is not True
                or batch["attempt_count"] != 2
                or batch["k"] != mapping_payload["k"]
                or selection["k"] != mapping_payload["k"]
                or type(mapping_payload["k"]) is not int
                or not 10 <= mapping_payload["k"] <= 20
                or len(expected_configs) != mapping_payload["k"]
                or batch["config_hashes"] != expected_hashes
                or mapping_payload["toolchain_binding"]
                != lock["runtime_binding"]["toolchain"]
                or mapping_payload["pass_b_activated"]
                != (failed_pass == "B")
                or failed_pass not in {"A", "B"}
            ):
                raise RunnerError("mapping failure batch completeness drift")
            toolchain_by_id = {
                item["id"]: item for item in mapping_payload["toolchain_binding"]
            }
            if (
                len(toolchain_by_id) != len(mapping_payload["toolchain_binding"])
                or set(toolchain_by_id) != {
                    "python",
                    "pytest",
                    "cxx_compiler",
                    "rocm_toolchain",
                }
                or toolchain_by_id["cxx_compiler"]["path"]
                != batch["worker_binding"]["compiler"]
            ):
                raise RunnerError("mapping failure toolchain binding drift")
            pass_root = FORMAL_MAPPING_ROOT / (
                "pass-a" if failed_pass == "A" else "pass-b"
            )
            pass_root = _ordinary_directory(
                pass_root,
                label="mapping reproduction pass root",
                exact_parent=Path(os.path.abspath(FORMAL_MAPPING_ROOT)),
            )
            request_path = _ordinary_file(
                ROOT / batch["request_path"], label="mapping reproduction request"
            )
            if request_path != pass_root / "request.json":
                raise RunnerError("mapping failure request/pass path mismatch")
            request = strict_load_json(request_path)
            worker_binding = batch["worker_binding"]
            if (
                set(request)
                != {
                    "schema_version",
                    "pass_id",
                    "yaml_path",
                    "yaml_sha256",
                    "compiler",
                    "configs",
                    "config_hashes",
                    "provenance_source_path",
                    "provenance_record_path",
                    "provenance_source_sha256",
                    "worker_source_sha256",
                }
                or set(worker_binding)
                != {
                    "worker_source_sha256",
                    "yaml_path",
                    "yaml_sha256",
                    "provenance_source_path",
                    "provenance_source_sha256",
                    "compiler",
                }
                or request["schema_version"] != 1
                or sha256_file(request_path) != batch["request_sha256"]
                or request["configs"] != expected_configs
                or request["config_hashes"] != expected_hashes
                or request["pass_id"] != failed_pass
                or request["worker_source_sha256"]
                != hashlib.sha256(mapping_worker_code().encode("utf-8")).hexdigest()
                or worker_binding["worker_source_sha256"]
                != request["worker_source_sha256"]
                or worker_binding["yaml_path"] != request["yaml_path"]
                or worker_binding["yaml_path"] != str(ACTUAL_YAML)
                or worker_binding["yaml_sha256"] != request["yaml_sha256"]
                or sha256_file(worker_binding["yaml_path"])
                != worker_binding["yaml_sha256"]
                or worker_binding["provenance_source_path"]
                != request["provenance_source_path"]
                or worker_binding["provenance_source_path"]
                != str(
                    PRELABEL_BUILD_ROOT
                    / "pinned-source/projects/hipblaslt/tensilelite/"
                    "Tensile/Contractions.py"
                )
                or worker_binding["provenance_source_sha256"]
                != request["provenance_source_sha256"]
                or sha256_file(worker_binding["provenance_source_path"])
                != worker_binding["provenance_source_sha256"]
                or worker_binding["compiler"] != request["compiler"]
                or worker_binding["compiler"] != "/opt/rocm/bin/amdclang++"
                or request["provenance_record_path"]
                != str(
                    Path(worker_binding["provenance_source_path"]).relative_to(ROOT)
                )
            ):
                raise RunnerError("mapping failure request/source binding drift")
            if len(batch["attempts"]) != 2:
                raise RunnerError("mapping failure attempt cardinality drift")
            failure_document = _load_raw_document(
                pass_root / "mapping-failure.json", "mapping_failure_batch"
            )
            if (
                failure_document["payload"] != batch
                or mapping["upstream_identities"]["mapping_failure_batch"]
                != failure_document["document_digest"]
                or request_path != pass_root / "request.json"
            ):
                raise RunnerError("mapping failure batch raw binding drift")
            reproduced_failures = []
            required_raw_child_paths.update(
                {
                    batch["request_path"],
                    (pass_root / "mapping-failure.json")
                    .relative_to(ROOT.resolve())
                    .as_posix(),
                }
            )
            for expected_attempt, attempt in enumerate(batch["attempts"], 1):
                expected_attempt_root = _ordinary_directory(
                    pass_root / f"attempt-{expected_attempt:02d}",
                    label="mapping reproduction attempt root",
                    exact_parent=pass_root,
                )
                if (
                    set(attempt)
                    != {
                        "completion_digest",
                        "attempt",
                        "returncode",
                        "cwd_path",
                        "stdout_path",
                        "stdout_sha256",
                        "stderr_path",
                        "stderr_sha256",
                        "worker_artifacts",
                    }
                    or attempt["attempt"] != expected_attempt
                    or attempt["returncode"] != MAPPING_FAILURE_RETURN_CODE
                    or ROOT / attempt["cwd_path"] != expected_attempt_root
                    or ROOT / attempt["stdout_path"]
                    != expected_attempt_root / "worker.stdout"
                    or ROOT / attempt["stderr_path"]
                    != expected_attempt_root / "worker.stderr"
                ):
                    raise RunnerError("mapping failure attempt identity drift")
                completion = _load_raw_document(
                    expected_attempt_root / "completion.json",
                    "mapping_worker_completion",
                )
                try:
                    validate_mapping_worker_completion(
                        completion, repository_root=ROOT, require_files=True
                    )
                except ContractError as error:
                    raise RunnerError(
                        "mapping failure completion semantic/raw binding drift"
                    ) from error
                completion_payload = completion["payload"]
                if (
                    completion["document_digest"] != attempt["completion_digest"]
                    or any(
                        completion_payload[key] != attempt[key]
                        for key in (
                            "attempt",
                            "returncode",
                            "cwd_path",
                            "stdout_path",
                            "stdout_sha256",
                            "stderr_path",
                            "stderr_sha256",
                            "worker_artifacts",
                        )
                    )
                    or sha256_file(ROOT / attempt["stdout_path"])
                    != attempt["stdout_sha256"]
                    or sha256_file(ROOT / attempt["stderr_path"])
                    != attempt["stderr_sha256"]
                ):
                    raise RunnerError("mapping failure attempt raw binding drift")
                required_raw_child_paths.update(
                    {
                        (expected_attempt_root / "completion.json")
                        .relative_to(ROOT.resolve())
                        .as_posix(),
                        attempt["stdout_path"],
                        attempt["stderr_path"],
                        *(
                            record["path"]
                            for record in attempt["worker_artifacts"]
                        ),
                    }
                )
                reproduced_failures.append(
                    _parse_mapping_failure_marker(
                        (ROOT / attempt["stdout_path"]).read_bytes(),
                        expected_configs,
                    )
                )
            if (
                reproduced_failures[0] != reproduced_failures[1]
                or reproduced_failures[0] != batch["failure"]
            ):
                raise RunnerError("mapping failure signature did not reproduce")
            observed_attempts = sorted(pass_root.glob("attempt-*"))
            for path in observed_attempts:
                _ordinary_directory(
                    path,
                    label="mapping reproduction attempt root",
                    exact_parent=pass_root,
                )
            if [path.name for path in observed_attempts] != [
                "attempt-01",
                "attempt-02",
            ]:
                raise RunnerError("mapping failure attempt set is not exactly two")
            if (pass_root / "mapping-pass.json").exists():
                raise RunnerError("successful mapping pass exists beside failure batch")
            if failed_pass == "A" and (
                FORMAL_MAPPING_ROOT / "pass-b"
            ).exists():
                raise RunnerError("mapping pass B exists after pass-A terminal failure")
        else:
            try:
                verify_mapping_parity(
                    mapping_payload["pass_a"]["rows"],
                    mapping_payload["pass_b"]["rows"],
                    k=mapping_payload["k"],
                )
            except MappingError:
                pass
            else:
                raise RunnerError("mapping-negative outcome did not reproduce")
    elif failure_id == "FT-BLOCKED-CORRECTNESS":
        correctness = _load_formal_document(
            CORRECTNESS_PATH,
            kind="correctness",
            lock_path=lock_path,
            lock=lock,
        )
        if (
            correctness["payload"]["status"] != "FAIL"
            or correctness["payload"]["reproducible"] is not True
            or len(correctness["payload"]["attempts"]) != 2
        ):
            raise RunnerError("correctness-negative outcome did not reproduce")
    elif failure_id == "noise_instability":
        mapping = _load_formal_document(
            MAPPING_PATH,
            kind="mapping_corpus",
            lock_path=lock_path,
            lock=lock,
        )
        observations = []
        for path in sorted((FORMAL_GPU_ROOT / "noise").glob("*/observation.json")):
            item = _load_raw_document(path, "noise_observation")["payload"]
            observations.append(
                {
                    key: item[key]
                    for key in ("config_hash", "size_id", "repeat", "quantity")
                }
            )
        rebuilt = validate_noise_cells(
            mapping["payload"]["selection"]["final_config_hashes"],
            observations,
        )
        if rebuilt["stable"] is not False:
            raise RunnerError("noise-inconclusive outcome did not reproduce")
    else:
        raise RunnerError("decision has no recognized frozen terminal branch")
    return {
        "scientific_outcome": outcome,
        "criterion": payload["criterion"],
        "failure_id": failure_id,
        "edge": payload["edge"],
        "decision_digest": decision["document_digest"],
        "_required_raw_child_paths": sorted(required_raw_child_paths),
    }


@_serialized_formal(REPRODUCTION_ROOT)
def reproduction_command(
    lock_path: Path | str, output: Path | str
) -> dict[str, Any]:
    lock = _require_formal(lock_path)
    lock_target = Path(lock_path).resolve()
    output_target = _exact_path(
        output,
        REPRODUCTION_ROOT / "s10r3-independent-result.json",
        label="reproduction output",
    )
    if not DECISION_PATH.is_file():
        raise RunnerError("reproduction requires a terminal decision")
    with _FormalWriter(REPRODUCTION_ROOT / ".writer.lock"):
        reconstructed = _reconstruct_reached_outcome(lock_target, lock)
        required_raw_child_paths = set(
            reconstructed.pop("_required_raw_child_paths")
        )
        raw_children = _all_reached_raw_children()
        raw_child_paths = {item["path"] for item in raw_children}
        if not required_raw_child_paths.issubset(raw_child_paths):
            raise RunnerError("reproduction raw_children omit required mapping files")
        document = _formal_document(
            kind="reproduction",
            lock_path=lock_target,
            lock=lock,
            raw_children=raw_children,
            upstream_identities={
                "decision": reconstructed["decision_digest"]
            },
            payload={
                **reconstructed,
                "status": "PASS",
                "independent_raw_evidence_reconstruction": True,
                "checkpoint_complete": False,
                "next_state": "VERIFIED_PENDING_CLOSEOUT",
            },
        )
        recovered = _write_or_match_json(output_target, document)
    return {
        "checkpoint_id": "S10R3",
        "status": "VERIFIED_PENDING_CLOSEOUT",
        "scientific_outcome": reconstructed["scientific_outcome"],
        "edge": reconstructed["edge"],
        "document_digest": document["document_digest"],
        "recovered": recovered,
    }


def formal_stage_projection(present: set[str] | frozenset[str]) -> str:
    """Pure fail-closed projection used to audit artifact-order admission."""

    allowed = {
        "support",
        "selection",
        "mapping_a",
        "mapping_b",
        "mapping",
        "native",
        "gpu_environment",
        "correctness",
        "noise",
        "decision",
        "reproduction",
    }
    if not set(present) <= allowed:
        raise RunnerError("formal stage projection contains an unknown artifact")
    prerequisites = {
        "selection": {"support"},
        "mapping_a": {"support", "selection"},
        "mapping_b": {"support", "selection", "mapping_a"},
        "mapping": {"support", "selection", "mapping_a", "mapping_b"},
        "native": {"support", "selection", "mapping_a", "mapping_b", "mapping"},
        "gpu_environment": {
            "support",
            "selection",
            "mapping_a",
            "mapping_b",
            "mapping",
            "native",
        },
        "correctness": {
            "support",
            "selection",
            "mapping_a",
            "mapping_b",
            "mapping",
            "native",
            "gpu_environment",
        },
        "noise": {
            "support",
            "selection",
            "mapping_a",
            "mapping_b",
            "mapping",
            "native",
            "gpu_environment",
            "correctness",
        },
        "reproduction": {"decision"},
    }
    for artifact, required in prerequisites.items():
        if artifact in present and not required <= set(present):
            raise RunnerError(f"formal artifact order failure at {artifact}")
    if "decision" in present:
        return "VERIFIED_PENDING_CLOSEOUT" if "reproduction" in present else "TERMINAL"
    order = (
        ("noise", "NOISE"),
        ("correctness", "CORRECTNESS"),
        ("gpu_environment", "GPU_ENVIRONMENT"),
        ("native", "NATIVE_CONFORMANCE"),
        ("mapping", "MAPPING_B"),
        ("mapping_b", "MAPPING_B_PENDING_PARITY"),
        ("mapping_a", "MAPPING_A"),
        ("selection", "BOUNDED_K_SELECTED"),
        ("support", "SUPPORT_CLASSIFICATION_SEALED"),
    )
    for artifact, stage in order:
        if artifact in present:
            return stage
    return "LOCKED_READY"


def _require_formal(lock_path: Path | str) -> dict[str, Any]:
    lock = _exact_path(lock_path, DEFAULT_LOCK_PATH, label="effective lock")
    if Path.cwd().resolve() != ROOT:
        raise RunnerError("formal command cwd differs from /src/rocm-libraries")
    mismatched_environment = {
        name: (os.environ.get(name), value)
        for name, value in FORMAL_ENVIRONMENT.items()
        if os.environ.get(name) != value
    }
    if mismatched_environment:
        raise RunnerError(
            f"formal runner environment differs from lock: {mismatched_environment}"
        )
    if verify_committed_effective_lock(lock) != "LOCKED_READY":
        raise RunnerError("formal command admission did not reach LOCKED_READY")
    document = strict_load_json(lock)
    validate_effective_lock(document)
    return document


def verify_effective_lock_command(lock_path: Path | str) -> dict[str, Any]:
    admission_path = ROOT / PRODUCTION_ADMISSION_LOCK_PATH
    with stable_admission_lock(
        admission_path, allow_production=True
    ) as (admission_fd, admission_identity):
        lock = _exact_path(lock_path, DEFAULT_LOCK_PATH, label="effective lock")
        document = strict_load_json(lock)
        validate_effective_lock(document)
        admission_lock_identity(
            admission_path,
            admission_fd,
            allow_production=True,
            expected_identity=admission_identity,
        )
    return {
        "checkpoint_id": "S10R3",
        "status": "EFFECTIVE_LOCK_VALID",
        "formal_evidence": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_s10r3_entry.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-contract")
    prepare = subparsers.add_parser("prepare-prelabel")
    verify = subparsers.add_parser("verify-prelabel")
    for command in (prepare, verify):
        command.add_argument("--build-root", required=True)
        command.add_argument("--fixture-root", required=True)
        command.add_argument("--registry", required=True)
        command.add_argument("--size-registry", required=True)
    create_lock = subparsers.add_parser("create-effective-lock")
    create_lock.add_argument("--plan-a-freeze", required=True)
    create_lock.add_argument("--plan-b-freeze", required=True)
    create_lock.add_argument("--repair-rounds-used", required=True, type=int)
    create_lock.add_argument("--resource-lineage", required=True)
    create_lock.add_argument("--output", required=True)
    verify_lock = subparsers.add_parser("verify-effective-lock")
    verify_lock.add_argument("--lock", required=True)
    retire_g2 = subparsers.add_parser("g2-retirement")
    retire_g2.add_argument("--production", action="store_true")
    retire_g2.add_argument("--seal-output")
    formal = (
        "support-discovery",
        "support-classification",
        "select-bounded-cover",
        "native-conformance",
        "gpu-environment",
        "correctness",
        "noise",
        "decision",
    )
    for name in formal:
        item = subparsers.add_parser(name)
        item.add_argument("--lock", required=True)
    mapping = subparsers.add_parser("mapping")
    mapping.add_argument("--pass-id", choices=("A", "B"), required=True)
    mapping.add_argument("--lock", required=True)
    reproduction = subparsers.add_parser("reproduction")
    reproduction.add_argument("--lock", required=True)
    reproduction.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "validate-contract":
            result = validate_contract_command()
        elif arguments.command == "prepare-prelabel":
            result = prepare_prelabel(
                build_root=arguments.build_root,
                fixture_root=arguments.fixture_root,
                registry_path=arguments.registry,
                size_registry_path=arguments.size_registry,
            )
        elif arguments.command == "verify-prelabel":
            result = verify_prelabel(
                build_root=arguments.build_root,
                fixture_root=arguments.fixture_root,
                registry_path=arguments.registry,
                size_registry_path=arguments.size_registry,
            )
        elif arguments.command == "create-effective-lock":
            resource_lineage = strict_load_json(arguments.resource_lineage)
            if set(resource_lineage) != {"records"}:
                raise RunnerError("resource lineage input must contain only records")
            result = build_effective_lock(
                plan_a_freeze=arguments.plan_a_freeze,
                plan_b_freeze=arguments.plan_b_freeze,
                repair_rounds_used=arguments.repair_rounds_used,
                resource_lineage_records=resource_lineage["records"],
                output=_exact_path(arguments.output, DEFAULT_LOCK_PATH, label="lock output"),
            )
        elif arguments.command == "verify-effective-lock":
            result = verify_effective_lock_command(arguments.lock)
        elif arguments.command == "g2-retirement":
            if arguments.production is not True:
                raise RunnerError("G2 retirement defaults denied without --production")
            try:
                result = execute_g2_transition(
                    selector=G2_LINEAGE_SELECTOR,
                    allow_production=True,
                    durable_seal_path=arguments.seal_output,
                )
            except ContractError as error:
                result = {
                    "checkpoint_id": "S10R3",
                    "action": "blocked",
                    "state": "BLOCKED_TRANSITION",
                    "execution_status": "CHANGES_REQUIRED",
                    "scientific_outcome": "not_evaluated",
                    "edge": None,
                    "formal_evidence_started": False,
                    "error": str(error),
                }
        elif arguments.command == "support-discovery":
            result = support_discovery_command(arguments.lock)
        elif arguments.command == "support-classification":
            result = support_classification_command(arguments.lock)
        elif arguments.command == "select-bounded-cover":
            result = select_bounded_cover_command(arguments.lock)
        elif arguments.command == "mapping":
            result = mapping_command(arguments.pass_id, arguments.lock)
        elif arguments.command == "native-conformance":
            result = native_conformance_command(arguments.lock)
        elif arguments.command == "gpu-environment":
            result = gpu_environment_command(arguments.lock)
        elif arguments.command == "correctness":
            result = correctness_command(arguments.lock)
        elif arguments.command == "noise":
            result = noise_command(arguments.lock)
        elif arguments.command == "decision":
            result = decision_command(arguments.lock)
        elif arguments.command == "reproduction":
            result = reproduction_command(arguments.lock, arguments.output)
        else:
            raise RunnerError(f"unhandled command: {arguments.command}")
    except (
        RunnerError,
        ValueError,
        OSError,
        subprocess.SubprocessError,
    ) as error:
        print(
            json.dumps(
                {
                    "checkpoint_id": "S10R3",
                    "scientific_outcome": "not_evaluated",
                    "edge": None,
                    "status": "CHANGES_REQUIRED",
                    "error": str(error),
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 2
    print(
        json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
