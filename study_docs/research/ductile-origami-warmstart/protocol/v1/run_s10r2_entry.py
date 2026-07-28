#!/usr/bin/env python3
# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""S10R2 support-aware entry runner.

Pre-evidence commands are available before the effective lock.  Every formal
command path calls ``require_effective_lock`` first; this module never imports
or searches S10R1.
"""

from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import fcntl
import functools
import hashlib
import json
import math
import os
import re
import resource
import subprocess
import sys
import tarfile
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

ROOT = Path(__file__).resolve().parents[5]
PROTOCOL = Path(__file__).resolve().parent
TENSILE_PYTHON = ROOT / "projects/hipblaslt/tensilelite"
for path in (str(TENSILE_PYTHON), str(PROTOCOL)):
    if path not in sys.path:
        sys.path.insert(0, path)

from Tensile.ductile.evidence import (  # noqa: E402
    atomic_write_bytes,
    atomic_write_json,
    canonical_sha256,
    plain_value,
    sha256_file,
    strict_load_json,
    strict_load_yaml,
)
from s10r2.calibration import (  # noqa: E402
    Allocation,
    CalibrationError,
    CalibrationMetrics,
    ResourceCaps,
    derive_caps,
    parse_utc_timestamp,
    validate_allocation,
    write_calibration_fixture,
)
from s10r2.contract import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    DEFAULT_SCHEMA_PATH,
    ContractError,
    implementation_hashes,
    load_contract,
    lock_body,
    seal_lock_document,
    verify_human_machine_parity,
    verify_lock_seal,
)
from s10r2.conformance import (  # noqa: E402
    materialize_native_fixture,
    run_native_formocast_conformance,
    run_runtime_substitution_fault_tests,
)
from s10r2.correctness import (  # noqa: E402
    anchor_hashes,
    validate_noise_cells,
    verify_correctness_anchors,
)
from s10r2.ledger import (  # noqa: E402
    FrozenResourceCaps,
    ResourceCounter,
    RunLedger,
    enforce_stop,
    resource_counter_from_event,
)
from s10r2.native_adapter import (  # noqa: E402
    NativeBinding,
    PinnedNativeFormocastRuntimeAdapter,
)
from s10r2.state_machine import Stage  # noqa: E402
from s10r2.mapping import (  # noqa: E402
    MAPPING_RESULT_MARKER,
    MappingError,
    exact_ten_greedy_cover,
    mandatory_atoms,
    mapping_worker_code,
    verify_ab_parity,
)
from s10r2.support import (  # noqa: E402
    AtomRegistry,
    AxisSpec,
    CONDITIONAL_CHUNKS,
    GLOBAL_CHUNKS,
    activate_targets,
    axis_specs_from_registry,
    classify_support,
    finalize_discovery_chunk,
    generate_discovery_draws,
    schedule_summary,
)

LOCK_PATH = PROTOCOL / "locks/s10r2-stage1-support-aware-entry-lock.json"
REGISTRY_PATH = PROTOCOL / "manifests/s10r2-candidate-atom-registry.json"
SIZE_REGISTRY_PATH = PROTOCOL / "manifests/s10r2-size-registry.json"
SUPPORT_PATH = PROTOCOL / "manifests/s10r2-support-classification.json"
MAPPING_PATH = PROTOCOL / "manifests/s10r2-mapping-corpus.json"
SENTINEL_PATH = PROTOCOL / "manifests/s10r2-sentinel-conformance.json"
CORRECTNESS_PATH = PROTOCOL / "evidence/s10r2-smoke-correctness.json"
NOISE_PATH = PROTOCOL / "evidence/s10r2-noise-pilot.json"
DECISION_PATH = PROTOCOL / "evidence/s10r2-decision.json"
GATE_RECORD_PATH = PROTOCOL / "evidence/gate-records/s10r2-s1-entry-go.json"
OUTCOME_PATHS = (
    SUPPORT_PATH,
    MAPPING_PATH,
    SENTINEL_PATH,
    CORRECTNESS_PATH,
    NOISE_PATH,
    DECISION_PATH,
    GATE_RECORD_PATH,
)
DUCTILE_COMMIT = "5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39"
NATIVE_SOURCE = PROTOCOL / "s10r2/native_formocast_runtime_adapter.cpp"
NATIVE_HOST_ADAPTER = PROTOCOL / "s10r2/native_adapter.py"
ACTUAL_YAML = PROTOCOL / "inputs/s10-generated.yaml"
S10_MAPPING_CORPUS = PROTOCOL / "manifests/s10-mapping-corpus.json"
REGISTRY_MARKER = "S10R2_REGISTRY_PROBE="
VALIDATOR_MARKER = "S10R2_VALIDATOR_RESULT="


class RunnerError(ValueError):
    """S10R2 command precondition failure."""


def _require_run_root(path: Path | str) -> Path:
    root = Path(path).resolve()
    allowed = (ROOT / "agent_run").resolve()
    try:
        root.relative_to(allowed)
    except ValueError as error:
        raise RunnerError("scratch path must be below the ignored agent_run root") from error
    check = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", str(root)],
        cwd=ROOT,
        check=False,
    )
    if check.returncode != 0:
        raise RunnerError("scratch path is not ignored by Git")
    return root


def _git(*arguments: str, text: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    )
    return completed.stdout


def materialize_pinned_native_source(output_root: Path | str) -> dict[str, Any]:
    """Materialize the pinned source without creating a worktree or Git ref."""

    output = _require_run_root(output_root)
    if output.exists() and any(output.iterdir()):
        raise RunnerError("pinned integration output must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    archive_command = [
        "git",
        "archive",
        "--format=tar",
        DUCTILE_COMMIT,
        "projects/hipblaslt/.agent",
        "projects/hipblaslt/.clang-format",
        "projects/hipblaslt/.githooks",
        "projects/hipblaslt/.github",
        "projects/hipblaslt/.gitignore",
        "projects/hipblaslt/.readthedocs.yaml",
        "projects/hipblaslt/.style.yapf",
        "projects/hipblaslt/AGENTS.md",
        "projects/hipblaslt/AGENTS_reference.md",
        "projects/hipblaslt/CHANGELOG.md",
        "projects/hipblaslt/CLAUDE.md",
        "projects/hipblaslt/CMakeLists.txt",
        "projects/hipblaslt/CMakePresets.json",
        "projects/hipblaslt/CODEOWNERS",
        "projects/hipblaslt/CONTRIBUTING.md",
        "projects/hipblaslt/LICENSE.md",
        "projects/hipblaslt/README.md",
        "projects/hipblaslt/clients",
        "projects/hipblaslt/cmake",
        "projects/hipblaslt/deps",
        "projects/hipblaslt/device-library",
        "projects/hipblaslt/docker",
        "projects/hipblaslt/docs",
        "projects/hipblaslt/install.sh",
        "projects/hipblaslt/library/include/hipblaslt-version.h.in",
        "projects/hipblaslt/requirements.txt",
        "projects/hipblaslt/rtest.py",
        "projects/hipblaslt/scripts",
        "projects/hipblaslt/tasks.py",
        "projects/hipblaslt/tensilelite",
        "projects/hipblaslt/tools",
        "projects/hipblaslt/utilities",
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
        raise RunnerError("cannot open git-archive stream")
    # Streaming mode prevents the source archive from consuming GiBs of RAM.
    with tarfile.open(fileobj=archive.stdout, mode="r|") as stream:
        for member in stream:
            relative = Path(member.name)
            if relative.is_absolute() or ".." in relative.parts:
                raise RunnerError(f"unsafe archive member: {member.name}")
            destination = output / relative
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            elif member.issym():
                target = Path(member.linkname)
                resolved = (destination.parent / target).resolve()
                try:
                    resolved.relative_to(output)
                except ValueError as error:
                    raise RunnerError(f"unsafe archive symlink: {member.name}") from error
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(member.linkname, destination)
            elif member.isfile():
                payload = stream.extractfile(member)
                if payload is None:
                    raise RunnerError(f"cannot extract archive member: {member.name}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                atomic_write_bytes(destination, payload.read(), exclusive=True)
                os.chmod(destination, member.mode & 0o777)
            else:
                raise RunnerError(f"unsupported archive member type: {member.name}")
    stderr = b"" if archive.stderr is None else archive.stderr.read()
    returncode = archive.wait()
    if returncode:
        raise RunnerError(
            "git archive failed: " + stderr.decode("utf-8", errors="replace")
        )
    pinned = {
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
                f"{DUCTILE_COMMIT}:shared/origami/include/origami/simulator/tensilelite/"
                "formocast_simulator.hpp",
                text=True,
            )
        ).strip(),
        "solution_iterator_source_blob": str(
            _git(
                "rev-parse",
                f"{DUCTILE_COMMIT}:projects/hipblaslt/tensilelite/client/src/"
                "SolutionIterator.cpp",
                text=True,
            )
        ).strip(),
        "solution_iterator_header_blob": str(
            _git(
                "rev-parse",
                f"{DUCTILE_COMMIT}:projects/hipblaslt/tensilelite/client/include/"
                "SolutionIterator.hpp",
                text=True,
            )
        ).strip(),
    }
    expected = {
        "formocast_source_blob": "cac2b324984a9fe2e1fadb018702486545e86e80",
        "formocast_header_blob": "96741965d34f2da1b0a08eaecab15e72082a78bc",
        "solution_iterator_source_blob": "33e86cfc4bf3d4ce8fa8da194b94c024bbb5639f",
        "solution_iterator_header_blob": "bad091c0f299f30c4235bc8313c9e8f134fa66a5",
    }
    if pinned != expected:
        raise RunnerError(f"pinned native source identities mismatch: {pinned}")
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "commit": DUCTILE_COMMIT,
        "root": str(output),
        "source_identities": pinned,
        "outcome_blind": True,
    }
    body["manifest_digest"] = canonical_sha256(body)
    atomic_write_json(output / "s10r2-materialization.json", body, exclusive=True)
    return body


def _native_cmake_source(integration_root: Path, source_path: Path) -> bytes:
    return (
        "cmake_minimum_required(VERSION 3.25.2)\n"
        "project(s10r2_native LANGUAGES CXX C ASM)\n"
        "set(HIPBLASLT_ENABLE_FETCH OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_DEVICE OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_EXTOPS OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_MATRIX_TRANSFORM OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_CLIENT OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_HOST OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_BUNDLE_PYTHON_DEPS OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_ROCROLLER OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_MXDATAGENERATOR OFF CACHE BOOL \"\" FORCE)\n"
        "set(TENSILELITE_ENABLE_HOST ON CACHE BOOL \"\" FORCE)\n"
        "set(TENSILELITE_ENABLE_CLIENT ON CACHE BOOL \"\" FORCE)\n"
        "set(TENSILELITE_BUILD_TESTING OFF CACHE BOOL \"\" FORCE)\n"
        "set(BUILD_TESTING OFF CACHE BOOL \"\" FORCE)\n"
        "find_package(hip REQUIRED)\n"
        f"add_subdirectory(\"{integration_root / 'projects/hipblaslt'}\" hipblaslt)\n"
        f"add_executable(s10r2-native \"{source_path}\")\n"
        "target_link_libraries(s10r2-native PRIVATE tensilelite::client-common)\n"
        "set_target_properties(s10r2-native PROPERTIES CXX_STANDARD 20 "
        "CXX_STANDARD_REQUIRED ON CXX_EXTENSIONS OFF)\n"
    ).encode("utf-8")


def build_pinned_native_helper(
    *,
    integration_root: Path | str,
    build_root: Path | str,
) -> dict[str, Any]:
    integration = _require_run_root(integration_root)
    build = _require_run_root(build_root)
    manifest = _object(
        integration / "s10r2-materialization.json", label="materialization manifest"
    )
    if manifest.get("commit") != DUCTILE_COMMIT:
        raise RunnerError("native integration commit mismatch")
    if build.exists() and any(build.iterdir()):
        raise RunnerError("native build root must be absent or empty")
    source_root = build / "source"
    binary_root = build / "build"
    logs = build / "logs"
    source_root.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    cmake_path = source_root / "CMakeLists.txt"
    atomic_write_bytes(
        cmake_path,
        _native_cmake_source(integration, NATIVE_SOURCE),
        exclusive=True,
    )
    configure = [
        "/opt/venv/bin/cmake",
        "-S",
        str(source_root),
        "-B",
        str(binary_root),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_CXX_COMPILER=/opt/rocm/bin/amdclang++",
    ]
    build_command = [
        "/opt/venv/bin/cmake",
        "--build",
        str(binary_root),
        "--target",
        "s10r2-native",
        "--parallel",
        "16",
    ]
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    records = []
    for name, command in (("configure", configure), ("build", build_command)):
        completed = subprocess.run(
            command,
            cwd=build,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        atomic_write_bytes(logs / f"{name}.stdout", completed.stdout, exclusive=True)
        atomic_write_bytes(logs / f"{name}.stderr", completed.stderr, exclusive=True)
        records.append(
            {
                "name": name,
                "argv": command,
                "returncode": completed.returncode,
                "stdout_sha256": canonical_sha256(
                    completed.stdout.decode("utf-8", "replace")
                ),
                "stderr_sha256": canonical_sha256(
                    completed.stderr.decode("utf-8", "replace")
                ),
            }
        )
        if completed.returncode:
            raise RunnerError(f"native {name} failed; inspect {logs}")
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    binary = binary_root / "s10r2-native"
    if not binary.is_file():
        raise RunnerError("native helper binary was not produced")
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "outcome_blind": True,
        "integration_manifest_digest": manifest["manifest_digest"],
        "source_identities": manifest["source_identities"],
        "source_path": str(NATIVE_SOURCE),
        "source_sha256": sha256_file(NATIVE_SOURCE),
        "host_adapter_path": str(NATIVE_HOST_ADAPTER),
        "host_adapter_sha256": sha256_file(NATIVE_HOST_ADAPTER),
        "cmake_source_sha256": sha256_file(cmake_path),
        "binary_path": str(binary),
        "binary_sha256": sha256_file(binary),
        "toolchain": {
            "cmake": configure[0],
            "cxx": "/opt/rocm/bin/amdclang++",
            "build_type": "Release",
            "parallel_jobs": 16,
        },
        "commands": records,
        "resource_measurement": {
            "wall_s": time.monotonic() - started,
            "cpu_s": (
                after.ru_utime
                + after.ru_stime
                - before.ru_utime
                - before.ru_stime
            ),
        },
    }
    body["build_manifest_digest"] = canonical_sha256(body)
    atomic_write_json(build / "s10r2-native-build.json", body, exclusive=True)
    return body


def build_pinned_client(
    *,
    native_build_manifest_path: Path | str,
    output_root: Path | str,
) -> dict[str, Any]:
    """Build the pinned reusable client as an outcome-blind toolchain cost."""

    output = _require_run_root(output_root)
    if output.exists() and any(output.iterdir()):
        raise RunnerError("pinned client output root must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    native = _object(native_build_manifest_path, label="native build manifest")
    recorded = native.get("build_manifest_digest")
    body_without_digest = dict(native)
    body_without_digest.pop("build_manifest_digest", None)
    if recorded != canonical_sha256(body_without_digest):
        raise RunnerError("native build manifest digest mismatch before client build")
    binary_root = Path(str(native["binary_path"])).resolve().parent
    _require_run_root(binary_root)
    build_root = binary_root
    command = [
        "/opt/venv/bin/cmake",
        "--build",
        str(build_root),
        "--target",
        "tensilelite-client",
        "--parallel",
        "16",
    ]
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    completed = subprocess.run(
        command,
        cwd=output,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
            "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
            "LC_ALL": "C",
        },
        timeout=3600,
    )
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    atomic_write_bytes(output / "stdout.log", completed.stdout, exclusive=True)
    atomic_write_bytes(output / "stderr.log", completed.stderr, exclusive=True)
    client = build_root / "hipblaslt/tensilelite/client/tensilelite-client"
    if completed.returncode or not client.is_file():
        raise RunnerError("pinned tensilelite-client build failed")
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "fixture_id": "s10r2-pinned-tensilelite-client-build-v1",
        "outcome_blind": True,
        "formal_evidence": False,
        "native_build_manifest_digest": recorded,
        "command": command,
        "client_path": str(client),
        "client_sha256": sha256_file(client),
        "elapsed_wall_s": time.monotonic() - started,
        "elapsed_cpu_s": (
            after.ru_utime
            + after.ru_stime
            - before.ru_utime
            - before.ru_stime
        ),
        "maximum_child_rss_kib": after.ru_maxrss,
        "retained_bytes": sum(
            path.stat().st_size for path in output.rglob("*") if path.is_file()
        ),
        "exit_status": completed.returncode,
        "stdout_sha256": sha256_file(output / "stdout.log"),
        "stderr_sha256": sha256_file(output / "stderr.log"),
    }
    body["client_build_digest"] = canonical_sha256(body)
    atomic_write_json(output / "s10r2-client-build.json", body, exclusive=True)
    return body


def run_native_fixture(
    *,
    build_manifest_path: Path | str,
    output_root: Path | str,
) -> dict[str, Any]:
    """Run the prelocked, outcome-blind native fixture in ignored scratch."""

    output = _require_run_root(output_root)
    if output.exists() and any(output.iterdir()):
        raise RunnerError("native fixture output root must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    contract = load_contract()
    native = contract["native_conformance"]
    fixture = materialize_native_fixture(
        native["synthetic_fixture"], native["thresholds"]
    )
    input_path = output / "s10r2-native-fixture.tsv"
    transcript_path = output / "s10r2-native-transcript.json"
    atomic_write_bytes(input_path, fixture["input_bytes"], exclusive=True)

    build = _object(build_manifest_path, label="native build manifest")
    recorded_digest = build.get("build_manifest_digest")
    build_body = dict(build)
    build_body.pop("build_manifest_digest", None)
    if recorded_digest != canonical_sha256(build_body):
        raise RunnerError("native build manifest digest mismatch")
    source_identities = build.get("source_identities")
    if source_identities != {
        "formocast_source_blob": contract["source_identity"]["native_formocast"][
            "source_blob"
        ],
        "formocast_header_blob": contract["source_identity"]["native_formocast"][
            "header_blob"
        ],
        "solution_iterator_source_blob": contract["source_identity"]["runtime_queue"][
            "source_blob"
        ],
        "solution_iterator_header_blob": contract["source_identity"]["runtime_queue"][
            "header_blob"
        ],
    }:
        raise RunnerError("native build source identities differ from contract")
    binary = Path(str(build.get("binary_path"))).resolve()
    _require_run_root(binary.parent)
    binding = NativeBinding(
        helper_path=str(binary),
        helper_sha256=str(build.get("binary_sha256")),
        helper_source_sha256=str(build.get("source_sha256")),
        host_adapter_sha256=str(build.get("host_adapter_sha256")),
        formocast_source_blob=str(source_identities["formocast_source_blob"]),
        formocast_header_blob=str(source_identities["formocast_header_blob"]),
        solution_iterator_source_blob=str(
            source_identities["solution_iterator_source_blob"]
        ),
        solution_iterator_header_blob=str(
            source_identities["solution_iterator_header_blob"]
        ),
        symbol=str(native["helper_symbol"]),
    )
    expected_binding = {
        "helper_sha256": build["binary_sha256"],
        "helper_source_sha256": build["source_sha256"],
        "host_adapter_sha256": build["host_adapter_sha256"],
        **source_identities,
        "symbol": native["helper_symbol"],
    }
    transcript = PinnedNativeFormocastRuntimeAdapter(binding).evaluate_cohort(
        input_path=input_path,
        output_path=transcript_path,
        expected_binding=expected_binding,
        helper_source_path=NATIVE_SOURCE,
        host_adapter_path=NATIVE_HOST_ADAPTER,
        cwd=output,
    )
    conformance_fixture = {
        "cohort": fixture["cohort"],
        "thresholds": fixture["thresholds"],
        "expected_queues": fixture["expected_queues"],
    }
    conformance = run_native_formocast_conformance(
        transcript, conformance_fixture
    )
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "outcome_blind": True,
        "formal_evidence": False,
        "fixture_id": native["synthetic_fixture"]["fixture_id"],
        "fixture_digest": fixture["fixture_digest"],
        "fixture_input_sha256": sha256_file(input_path),
        "transcript_sha256": sha256_file(transcript_path),
        "build_manifest_digest": recorded_digest,
        "binding": expected_binding,
        "conformance": conformance,
    }
    body["record_digest"] = canonical_sha256(body)
    atomic_write_json(output / "s10r2-native-fixture-result.json", body, exclusive=True)
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

MARKER = "S10R2_REGISTRY_PROBE="

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
    raise TypeError("unsupported probe value: " + type(value).__name__)

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
            raise ValueError("SearchSpace grouped candidates differ from fresh expansion")
        yaml_pointer = (
            "/BenchmarkProblems/0/1/ForkParameters/"
            + str(groups_record_index)
            + "/Groups/"
            + str(group_index)
        )
        grouped = True
    else:
        if axis_name not in raw_axis:
            raise ValueError("SearchSpace axis has no raw ForkParameters source")
        raw_index, raw_candidates = raw_axis[axis_name]
        if plain(candidates) != plain(raw_candidates):
            raise ValueError("SearchSpace candidates differ from raw ForkParameters")
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
    "numpy_version": np.__version__,
}
print(MARKER + json.dumps(result, sort_keys=True, separators=(",", ":")))
'''


def materialize_candidate_registry(
    *,
    integration_root: Path | str,
    output_path: Path | str = REGISTRY_PATH,
) -> dict[str, Any]:
    """Create the complete fresh pre-draw atom registry from pinned code/YAML."""

    integration = _require_run_root(integration_root)
    materialization = _object(
        integration / "s10r2-materialization.json",
        label="materialization manifest",
    )
    if materialization.get("commit") != DUCTILE_COMMIT:
        raise RunnerError("candidate registry integration commit mismatch")
    if sha256_file(ACTUAL_YAML) != (
        "faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36"
    ):
        raise RunnerError("actual YAML byte identity mismatch")
    actual_blob = str(_git("hash-object", str(ACTUAL_YAML), text=True)).strip()
    if actual_blob != "1fd6fb401d5baebd4665a87e9002687fb725b2dc":
        raise RunnerError("actual YAML Git blob mismatch")
    candidate_source = (
        integration
        / "projects/hipblaslt/tensilelite/Tensile/BenchmarkStructs.py"
    )
    if str(
        _git(
            "rev-parse",
            f"{DUCTILE_COMMIT}:projects/hipblaslt/tensilelite/Tensile/"
            "BenchmarkStructs.py",
            text=True,
        )
    ).strip() != "4968b29b5eacddc56b20c42cb4b2c1e3d8d6f406":
        raise RunnerError("pinned candidate-construction blob mismatch")
    if not candidate_source.is_file():
        raise RunnerError("pinned BenchmarkStructs.py is absent")
    pinned_python = integration / "projects/hipblaslt/tensilelite"
    environment = {
        "PYTHONPATH": str(pinned_python),
        "PATH": "/opt/rocm/bin:/usr/bin:/bin",
        "LC_ALL": "C",
    }
    completed = subprocess.run(
        [sys.executable, "-c", _registry_probe_code(), str(ACTUAL_YAML)],
        cwd=integration,
        env=environment,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=600,
    )
    if completed.returncode:
        raise RunnerError(
            "pinned candidate registry probe failed: "
            + completed.stderr.decode("utf-8", "replace")[-2000:]
        )
    marked = [
        line[len(REGISTRY_MARKER) :]
        for line in completed.stdout.decode("utf-8", "replace").splitlines()
        if line.startswith(REGISTRY_MARKER)
    ]
    if len(marked) != 1:
        raise RunnerError("candidate registry probe did not emit one record")
    try:
        probe = json.loads(marked[0])
    except json.JSONDecodeError as error:
        raise RunnerError(f"candidate registry probe JSON failed: {error}") from error
    if (
        probe.get("schema_version") != 1
        or probe.get("document_sha256") != sha256_file(ACTUAL_YAML)
        or probe.get("axis_count") != 30
    ):
        raise RunnerError("candidate registry probe identity mismatch")
    axes = []
    for raw in probe["axes"]:
        axes.append(
            AxisSpec(
                axis_index=int(raw["axis_index"]),
                axis_name=str(raw["axis_name"]),
                values=tuple(raw["values"]),
                grouped=bool(raw["grouped"]),
                frozen_free=bool(raw["frozen_free"]),
                currently_weighted=bool(raw["currently_weighted"]),
                yaml_pointer=str(raw["yaml_pointer"]),
                value_yaml_pointers=tuple(raw["value_yaml_pointers"]),
                derivation_indices_by_value=tuple(
                    tuple(int(value) for value in row)
                    for row in raw["derivation_indices_by_value"]
                ),
                probabilities=(
                    tuple(float(value) for value in raw["probabilities"])
                    if raw["currently_weighted"]
                    else ()
                ),
                probabilities_raw_sha256=raw["probabilities_raw_sha256"],
            )
        )
    registry = AtomRegistry(axes).document()
    if registry["axis_order"] != probe["axis_order"]:
        raise RunnerError("candidate registry axis order mismatch")
    atomic_write_json(output_path, registry, exclusive=True)
    os.chmod(output_path, 0o644)
    return {
        "checkpoint_id": "S10R2",
        "registry_path": str(Path(output_path)),
        "registry_digest": registry["registry_digest"],
        "axis_count": registry["axis_count"],
        "row_count": registry["row_count"],
        "prelocked_atom_count": sum(
            1 for row in registry["rows"] if row["role_flags"]["prelocked_candidate"]
        ),
        "diagnostic_atom_count": sum(
            1
            for row in registry["rows"]
            if row["role_flags"]["conditional_diagnostic"]
        ),
        "formal_draws_executed": 0,
        "probe_stdout_sha256": canonical_sha256(
            completed.stdout.decode("utf-8", "replace")
        ),
        "probe_stderr_sha256": canonical_sha256(
            completed.stderr.decode("utf-8", "replace")
        ),
    }


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

MARKER = "S10R2_VALIDATOR_RESULT="
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
results = []
for config_row in request["configs"]:
    valid = _validate_solution(
        process.problemType,
        dict(step.constantParams),
        assembler,
        debug,
        isa_map,
        config_row,
        get_kernel_src=False,
    )
    if request["retain_results"]:
        results.append(
            {"valid": bool(valid), "reason": None if valid else "validator_false"}
        )
print(
    MARKER
    + json.dumps(
        {
            "processed": len(request["configs"]),
            "results": results if request["retain_results"] else None,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
)
'''


def run_pinned_validator_batch(
    *,
    integration_root: Path | str,
    configs: Sequence[Mapping[str, Any]],
    scratch_root: Path | str,
    retain_results: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Call the exact pinned Ductile validity boundary for one atomic batch."""

    integration = _require_run_root(integration_root)
    scratch = _require_run_root(scratch_root)
    if scratch.exists() and any(scratch.iterdir()):
        raise RunnerError("validator scratch root must be absent or empty")
    scratch.mkdir(parents=True, exist_ok=True)
    if len(configs) == 0:
        raise RunnerError("validator batch must not be empty")
    request = {
        "schema_version": 1,
        "yaml_path": str(ACTUAL_YAML),
        "compiler": "/opt/rocm/bin/amdclang++",
        "configs": [dict(config) for config in configs],
        "retain_results": retain_results,
    }
    request_path = scratch / "request.json"
    stdout_path = scratch / "stdout.log"
    stderr_path = scratch / "stderr.log"
    atomic_write_json(request_path, request, exclusive=True)
    environment = {
        "PYTHONPATH": str(
            integration / "projects/hipblaslt/tensilelite"
        ),
        "PATH": "/opt/rocm/bin:/usr/bin:/bin",
        "LC_ALL": "C",
    }
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    completed = subprocess.run(
        [sys.executable, "-c", _validator_worker_code(), str(request_path)],
        cwd=scratch,
        env=environment,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=3600,
    )
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    atomic_write_bytes(stdout_path, completed.stdout, exclusive=True)
    atomic_write_bytes(stderr_path, completed.stderr, exclusive=True)
    measurement = {
        "wall_s": time.monotonic() - started,
        "cpu_s": (
            after.ru_utime
            + after.ru_stime
            - before.ru_utime
            - before.ru_stime
        ),
        "returncode": completed.returncode,
        "request_sha256": sha256_file(request_path),
        "stdout_sha256": sha256_file(stdout_path),
        "stderr_sha256": sha256_file(stderr_path),
        "config_count": len(configs),
        "worker_sha256": canonical_sha256(_validator_worker_code()),
        "maximum_child_rss_kib": after.ru_maxrss,
    }
    if completed.returncode:
        raise RunnerError(
            "pinned validator worker failed closed: "
            + completed.stderr.decode("utf-8", "replace")[-2000:]
        )
    marked = [
        line[len(VALIDATOR_MARKER) :]
        for line in completed.stdout.decode("utf-8", "replace").splitlines()
        if line.startswith(VALIDATOR_MARKER)
    ]
    if len(marked) != 1:
        raise RunnerError("pinned validator worker did not emit one result")
    try:
        result = json.loads(marked[0])
    except json.JSONDecodeError as error:
        raise RunnerError(f"pinned validator JSON failed: {error}") from error
    if result.get("processed") != len(configs):
        raise RunnerError("pinned validator processed-count mismatch")
    rows = result.get("results")
    if retain_results:
        if (
            not isinstance(rows, list)
            or len(rows) != len(configs)
            or any(
                not isinstance(row, Mapping) or type(row.get("valid")) is not bool
                for row in rows
            )
        ):
            raise RunnerError("pinned validator result cardinality/type mismatch")
        return [dict(row) for row in rows], measurement
    if rows is not None:
        raise RunnerError("outcome-blind validator calibration leaked labels")
    measurement["validity_labels_retained"] = False
    return [], measurement


def calibrate_selection_chunk(
    *,
    integration_root: Path | str,
    output_root: Path | str,
    registry_path: Path | str = REGISTRY_PATH,
) -> dict[str, Any]:
    """Measure one synthetic 512-config validator batch without retaining labels."""

    output = _require_run_root(output_root)
    if output.exists() and any(output.iterdir()):
        raise RunnerError("selection calibration output must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    contract = load_contract()
    protocol = contract["resource"]["calibration_protocol"]["selection_chunk"]
    if (
        protocol["config_count"] != 512
        or protocol["candidate_index_rule"]
        != "(draw_index*17 + axis_index*13) mod candidate_count"
        or protocol["retain_validity_labels"] is not False
    ):
        raise RunnerError("selection calibration protocol mismatch")
    registry_document = _object(registry_path, label="candidate atom registry")
    if registry_document.get("registry_digest") != protocol[
        "candidate_registry_digest"
    ]:
        raise RunnerError("selection calibration registry digest mismatch")
    axes = axis_specs_from_registry(registry_document)
    configs = []
    for draw_index in range(512):
        configs.append(
            {
                axis.axis_name: axis.values[
                    (draw_index * 17 + axis.axis_index * 13) % len(axis.values)
                ]
                for axis in axes
            }
        )
    fixture_config_digest = canonical_sha256(configs)
    expected_digest = protocol.get("fixture_config_digest")
    if expected_digest is not None and expected_digest != fixture_config_digest:
        raise RunnerError("selection calibration fixture digest mismatch")
    _, measurement = run_pinned_validator_batch(
        integration_root=integration_root,
        configs=configs,
        scratch_root=output / "validator",
        retain_results=False,
    )
    retained = sum(
        path.stat().st_size
        for path in output.rglob("*")
        if path.is_file()
    )
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "fixture_id": protocol["fixture_id"],
        "fixture_config_digest": fixture_config_digest,
        "candidate_registry_digest": registry_document["registry_digest"],
        "config_count": 512,
        "outcome_blind": True,
        "formal_draws_executed": 0,
        "validity_labels_retained": False,
        "elapsed_wall_s": measurement["wall_s"],
        "elapsed_cpu_s": measurement["cpu_s"],
        "elapsed_gpu_s": 0.0,
        "maximum_child_rss_kib": measurement["maximum_child_rss_kib"],
        "retained_bytes": retained,
        "exit_status": measurement["returncode"],
        "worker_sha256": measurement["worker_sha256"],
        "request_sha256": measurement["request_sha256"],
        "stdout_sha256": measurement["stdout_sha256"],
        "stderr_sha256": measurement["stderr_sha256"],
    }
    body["calibration_digest"] = canonical_sha256(body)
    atomic_write_json(
        output / "s10r2-selection-calibration.json", body, exclusive=True
    )
    return body


def _gpu_calibration_source() -> bytes:
    return b"""#include <hip/hip_runtime.h>
#include <cstdio>

__global__ void s10r2_empty_kernel() {}

int main()
{
    constexpr int launches = 10000;
    hipEvent_t begin;
    hipEvent_t end;
    if(hipEventCreate(&begin) != hipSuccess || hipEventCreate(&end) != hipSuccess)
        return 2;
    if(hipEventRecord(begin) != hipSuccess)
        return 3;
    for(int index = 0; index < launches; ++index)
        s10r2_empty_kernel<<<1, 1>>>();
    if(hipGetLastError() != hipSuccess || hipEventRecord(end) != hipSuccess
       || hipEventSynchronize(end) != hipSuccess)
        return 4;
    float milliseconds = 0.0f;
    if(hipEventElapsedTime(&milliseconds, begin, end) != hipSuccess)
        return 5;
    std::printf("%.9f\\n", static_cast<double>(milliseconds) / 1000.0);
    hipEventDestroy(begin);
    hipEventDestroy(end);
    return 0;
}
"""


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
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            "PATH": "/opt/rocm/bin:/usr/bin:/bin",
            "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
            "LC_ALL": "C",
        },
        timeout=60,
    )
    if completed.returncode:
        raise RunnerError("ROCm-SMI allocation snapshot failed")
    try:
        devices = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RunnerError(f"ROCm-SMI allocation JSON failed: {error}") from error
    if not isinstance(devices, Mapping) or not devices:
        raise RunnerError("ROCm-SMI allocation has no visible devices")
    return {
        "command": command,
        "devices": dict(devices),
        "stdout_sha256": canonical_sha256(
            completed.stdout.decode("utf-8", "replace")
        ),
        "stderr_sha256": canonical_sha256(
            completed.stderr.decode("utf-8", "replace")
        ),
    }


def _select_idle_gfx942(
    snapshot: Mapping[str, Any],
    process_snapshot: Mapping[str, Any],
) -> tuple[int, dict[str, Any]]:
    physical_device_pids = process_snapshot.get("physical_device_pids")
    if not isinstance(physical_device_pids, Mapping):
        raise RunnerError("ROCm-SMI process snapshot lacks physical-device coverage")
    eligible = []
    for name, raw in snapshot["devices"].items():
        if not name.startswith("card") or not name[4:].isdigit():
            continue
        if not isinstance(raw, Mapping):
            continue
        index = int(name[4:])
        pids = physical_device_pids.get(str(index))
        if not isinstance(pids, list):
            raise RunnerError(
                f"ROCm-SMI process snapshot lacks coverage for card{index}"
            )
        if (
            raw.get("GFX Version") == "gfx942"
            and raw.get("Compute Partition") == "SPX"
            and raw.get("Memory Partition") == "NPS1"
            and raw.get("GPU use (%)") == "0"
            and raw.get("GPU Memory Allocated (VRAM%)") == "0"
            and not pids
        ):
            eligible.append((index, dict(raw)))
    if not eligible:
        raise RunnerError(
            "no zero-use/zero-VRAM/no-foreign-PID gfx942 SPX/NPS1 card "
            "satisfies the frozen selection rule"
        )
    return min(eligible, key=lambda item: item[0])


def calibrate_gpu_fixed_cost(
    *,
    output_root: Path | str,
) -> dict[str, Any]:
    """Run the count-bounded empty HIP launch fixture without scientific labels."""

    output = _require_run_root(output_root)
    if output.exists() and any(output.iterdir()):
        raise RunnerError("GPU calibration output must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    contract = load_contract()
    protocol = contract["resource"]["calibration_protocol"]["gpu_fixed_cost"]
    if (
        protocol["launch_count"] != 10_000
        or protocol["retain_correctness_or_performance_labels"] is not False
    ):
        raise RunnerError("GPU fixed-cost calibration protocol mismatch")
    before = _gpu_snapshot()
    processes_before = _gpu_process_snapshot(before)
    device_index, device = _select_idle_gfx942(before, processes_before)
    source = _gpu_calibration_source()
    source_sha256 = __import__("hashlib").sha256(source).hexdigest()
    expected_source = protocol.get("source_sha256")
    if expected_source is not None and expected_source != source_sha256:
        raise RunnerError("GPU calibration source digest mismatch")
    source_path = output / "s10r2-empty-hip-launch.cpp"
    binary_path = output / "s10r2-empty-hip-launch"
    atomic_write_bytes(source_path, source, exclusive=True)
    os.chmod(source_path, 0o644)
    compile_command = [
        "/opt/rocm/bin/hipcc",
        "-O2",
        str(source_path),
        "-o",
        str(binary_path),
    ]
    before_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    compile_started = time.monotonic()
    compiled = subprocess.run(
        compile_command,
        cwd=output,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            "PATH": "/opt/rocm/bin:/usr/bin:/bin",
            "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
            "LC_ALL": "C",
        },
        timeout=600,
    )
    compile_wall = time.monotonic() - compile_started
    atomic_write_bytes(output / "compile.stdout", compiled.stdout, exclusive=True)
    atomic_write_bytes(output / "compile.stderr", compiled.stderr, exclusive=True)
    if compiled.returncode or not binary_path.is_file():
        raise RunnerError("empty HIP calibration fixture failed to compile")

    run_environment = {
        "PATH": "/opt/rocm/bin:/usr/bin:/bin",
        "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
        "LC_ALL": "C",
        "ROCR_VISIBLE_DEVICES": str(device_index),
    }
    run_started = time.monotonic()
    executed = subprocess.run(
        [str(binary_path)],
        cwd=output,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=run_environment,
        timeout=300,
    )
    run_wall = time.monotonic() - run_started
    after_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    atomic_write_bytes(output / "run.stdout", executed.stdout, exclusive=True)
    atomic_write_bytes(output / "run.stderr", executed.stderr, exclusive=True)
    if executed.returncode:
        raise RunnerError("empty HIP calibration fixture failed to execute")
    try:
        gpu_s = float(executed.stdout.decode("ascii").strip())
    except ValueError as error:
        raise RunnerError("empty HIP fixture emitted invalid GPU time") from error
    if not 0 < gpu_s <= run_wall * 2:
        raise RunnerError("empty HIP fixture GPU time is not credible")
    after = _gpu_snapshot()
    processes_after = _gpu_process_snapshot(after)
    _assert_selected_card_pid_free(device_index, processes_after)
    retained = sum(
        path.stat().st_size for path in output.rglob("*") if path.is_file()
    )
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "fixture_id": protocol["fixture_id"],
        "source_sha256": source_sha256,
        "launch_count": 10_000,
        "outcome_blind": True,
        "formal_gpu_evidence": False,
        "correctness_or_performance_labels_retained": False,
        "selected_device": {
            "container_visible_index": device_index,
            "unique_id": device["Unique ID"],
            "serial_number": device["Serial Number"],
            "gfx_version": device["GFX Version"],
            "compute_partition": device["Compute Partition"],
            "memory_partition": device["Memory Partition"],
        },
        "allocation_snapshot_before": before,
        "process_snapshot_before": processes_before,
        "allocation_snapshot_after": after,
        "process_snapshot_after": processes_after,
        "elapsed_wall_s": compile_wall + run_wall,
        "compile_wall_s": compile_wall,
        "run_wall_s": run_wall,
        "elapsed_cpu_s": (
            after_usage.ru_utime
            + after_usage.ru_stime
            - before_usage.ru_utime
            - before_usage.ru_stime
        ),
        "elapsed_gpu_s": gpu_s,
        "maximum_child_rss_kib": after_usage.ru_maxrss,
        "retained_bytes": retained,
        "exit_status": executed.returncode,
        "binary_sha256": sha256_file(binary_path),
        "compile_stdout_sha256": sha256_file(output / "compile.stdout"),
        "compile_stderr_sha256": sha256_file(output / "compile.stderr"),
        "run_stdout_sha256": sha256_file(output / "run.stdout"),
        "run_stderr_sha256": sha256_file(output / "run.stderr"),
    }
    body["calibration_digest"] = canonical_sha256(body)
    atomic_write_json(output / "s10r2-gpu-calibration.json", body, exclusive=True)
    return body


def materialize_size_registry(
    output_path: Path | str = SIZE_REGISTRY_PATH,
) -> dict[str, Any]:
    """Write the three authority-locked sizes before any formal evidence."""

    contract = load_contract()
    sizes = contract["correctness"]["sizes"]
    if sizes != [
        [8, 8, 1, 128],
        [256, 256, 1, 1024],
        [2304, 1024, 1, 214336],
    ]:
        raise RunnerError("S10R2 size registry differs from authority")
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "source": "s10r2-stage1-support-aware-entry-contract.yaml",
        "sizes": [
            {"size_id": size_id, "values": size}
            for size_id, size in zip(("small", "medium", "large"), sizes)
        ],
    }
    document = {**body, "size_registry_digest": canonical_sha256(body)}
    recovered = _write_or_match_json(output_path, document)
    os.chmod(output_path, 0o644)
    return document


def run_pinned_mapping_batch(
    *,
    integration_root: Path | str,
    candidates: Sequence[Mapping[str, Any]],
    sizes: Sequence[Mapping[str, Any]],
    scratch_root: Path | str,
    retain_rows: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run one fresh pinned mapping pass or an outcome-blind timing fixture."""

    integration = _require_run_root(integration_root)
    scratch = _require_run_root(scratch_root)
    if scratch.exists() and any(scratch.iterdir()):
        raise RunnerError("mapping scratch root must be absent or empty")
    scratch.mkdir(parents=True, exist_ok=True)
    if not candidates or not sizes:
        raise RunnerError("mapping batch candidates/sizes must be non-empty")
    request = {
        "schema_version": 1,
        "yaml_path": str(ACTUAL_YAML),
        "compiler": "/opt/rocm/bin/amdclang++",
        "candidates": [dict(candidate) for candidate in candidates],
        "sizes": [dict(size) for size in sizes],
        "retain_rows": retain_rows,
    }
    request_path = scratch / "request.json"
    stdout_path = scratch / "stdout.log"
    stderr_path = scratch / "stderr.log"
    atomic_write_json(request_path, request, exclusive=True)
    environment = {
        "PYTHONPATH": os.pathsep.join(
            (
                str(integration / "projects/hipblaslt/tensilelite"),
                str(
                    integration
                    / "projects/hipblaslt/tensilelite/Tensile/Utilities"
                ),
            )
        ),
        "PATH": "/opt/rocm/bin:/usr/bin:/bin",
        "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
        "LC_ALL": "C",
    }
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    completed = subprocess.run(
        [sys.executable, "-c", mapping_worker_code(), str(request_path)],
        cwd=scratch,
        env=environment,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=3600,
    )
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    atomic_write_bytes(stdout_path, completed.stdout, exclusive=True)
    atomic_write_bytes(stderr_path, completed.stderr, exclusive=True)
    measurement = {
        "wall_s": time.monotonic() - started,
        "cpu_s": (
            after.ru_utime
            + after.ru_stime
            - before.ru_utime
            - before.ru_stime
        ),
        "returncode": completed.returncode,
        "maximum_child_rss_kib": after.ru_maxrss,
        "request_sha256": sha256_file(request_path),
        "stdout_sha256": sha256_file(stdout_path),
        "stderr_sha256": sha256_file(stderr_path),
        "worker_sha256": canonical_sha256(mapping_worker_code()),
    }
    if completed.returncode:
        raise RunnerError(
            "pinned mapping worker failed closed: "
            + completed.stderr.decode("utf-8", "replace")[-4000:]
        )
    marked = [
        line[len(MAPPING_RESULT_MARKER) :]
        for line in completed.stdout.decode("utf-8", "replace").splitlines()
        if line.startswith(MAPPING_RESULT_MARKER)
    ]
    if len(marked) != 1:
        raise RunnerError("pinned mapping worker did not emit one result")
    try:
        result = json.loads(marked[0])
    except json.JSONDecodeError as error:
        raise RunnerError(f"pinned mapping result JSON failed: {error}") from error
    if (
        result.get("processed_candidates") != len(candidates)
        or result.get("processed_size_rows") != len(candidates) * len(sizes)
    ):
        raise RunnerError("pinned mapping processed-count mismatch")
    rows = result.get("rows")
    if retain_rows:
        if not isinstance(rows, list) or len(rows) != len(candidates) * len(sizes):
            raise RunnerError("pinned mapping row cardinality mismatch")
        return [dict(row) for row in rows], measurement
    if rows is not None:
        raise RunnerError("outcome-blind mapping calibration leaked rows")
    return [], measurement


def calibrate_mapping_row(
    *,
    integration_root: Path | str,
    output_root: Path | str,
) -> dict[str, Any]:
    """Measure a committed S10 foundation config without retaining mapping labels."""

    output = _require_run_root(output_root)
    if output.exists() and any(output.iterdir()):
        raise RunnerError("mapping calibration output must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    contract = load_contract()
    protocol = contract["resource"]["calibration_protocol"]["mapping_row"]
    if (
        sha256_file(S10_MAPPING_CORPUS) != protocol["foundation_source_sha256"]
        or protocol["retain_mapping_or_Formocast_labels"] is not False
        or protocol["allowed_use"]
        != "resource_timing_only_not_S10R2_gate_evidence"
    ):
        raise RunnerError("mapping calibration foundation/protocol mismatch")
    foundation = _object(S10_MAPPING_CORPUS, label="S10 foundation mapping corpus")
    candidates = [
        row
        for row in foundation.get("rows", [])
        if row.get("config_hash") == protocol["fixed_config_hash"]
    ]
    if len(candidates) != 3:
        raise RunnerError("mapping calibration foundation config coverage mismatch")
    source = candidates[0]
    if any(
        row.get("raw_values") != source.get("raw_values")
        or row.get("raw_indices") != source.get("raw_indices")
        for row in candidates
    ):
        raise RunnerError("mapping calibration foundation config identity mismatch")
    candidate = {
        "slot": 0,
        "config_hash": protocol["fixed_config_hash"],
        "config": source["raw_values"],
        "candidate_indices": source["raw_indices"],
    }
    _, measurement = run_pinned_mapping_batch(
        integration_root=integration_root,
        candidates=[candidate],
        sizes=[
            {
                "size_id": protocol["fixed_size_id"],
                "values": protocol["fixed_size"],
            }
        ],
        scratch_root=output / "mapping",
        retain_rows=False,
    )
    retained = sum(
        path.stat().st_size for path in output.rglob("*") if path.is_file()
    )
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "fixture_id": protocol["fixture_id"],
        "foundation_source_sha256": protocol["foundation_source_sha256"],
        "fixed_config_hash": protocol["fixed_config_hash"],
        "fixed_size_id": protocol["fixed_size_id"],
        "outcome_blind": True,
        "formal_mapping_evidence": False,
        "mapping_or_Formocast_labels_retained": False,
        "elapsed_wall_s": measurement["wall_s"],
        "elapsed_cpu_s": measurement["cpu_s"],
        "elapsed_gpu_s": 0.0,
        "maximum_child_rss_kib": measurement["maximum_child_rss_kib"],
        "retained_bytes": retained,
        "exit_status": measurement["returncode"],
        "worker_sha256": measurement["worker_sha256"],
        "request_sha256": measurement["request_sha256"],
        "stdout_sha256": measurement["stdout_sha256"],
        "stderr_sha256": measurement["stderr_sha256"],
    }
    body["calibration_digest"] = canonical_sha256(body)
    atomic_write_json(output / "s10r2-mapping-calibration.json", body, exclusive=True)
    return body


def _singleton_yaml_bytes(
    *,
    candidate: Mapping[str, Any],
    sizes: Sequence[Sequence[int]],
    device_index: int,
) -> bytes:
    config = copy.deepcopy(strict_load_yaml(ACTUAL_YAML))
    config.pop("Backend", None)
    problem_group = config["BenchmarkProblems"][0][1]
    flattened: dict[str, Any] = {}
    for axis, value in candidate.items():
        if not axis.startswith("group_"):
            flattened[axis] = plain_value(value)
    grouped = sorted(
        (
            (int(axis.split("_", 1)[1]), value)
            for axis, value in candidate.items()
            if axis.startswith("group_")
        ),
        key=lambda item: item[0],
    )
    for _, group in grouped:
        if not isinstance(group, Mapping):
            raise RunnerError("foundation grouped candidate must be an object")
        for name, value in group.items():
            flattened[str(name)] = plain_value(value)
    problem_group["ForkParameters"] = [
        {name: [value]} for name, value in flattened.items()
    ]
    finals = problem_group["BenchmarkFinalParameters"]
    problem_size_slots = [
        index
        for index, entry in enumerate(finals)
        if isinstance(entry, Mapping) and "ProblemSizes" in entry
    ]
    if problem_size_slots != [0]:
        raise RunnerError("unexpected BenchmarkFinalParameters size slot")
    finals[0] = {
        "ProblemSizes": [
            {"Exact": [int(value) for value in size]} for size in sizes
        ]
    }
    globals_ = config["GlobalParameters"]
    globals_["NumElementsToValidate"] = 128
    globals_["ExitOnFails"] = 2
    globals_["Device"] = int(device_index)
    globals_["KeepBuildTmp"] = True
    return yaml.safe_dump(
        plain_value(config),
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=4096,
    ).encode("utf-8")


def calibrate_correctness_build_cell(
    *,
    integration_root: Path | str,
    client_build_path: Path | str,
    output_root: Path | str,
) -> dict[str, Any]:
    """Measure one foundation generate/compile cell in strict build-only mode."""

    integration = _require_run_root(integration_root)
    output = _require_run_root(output_root)
    if output.exists() and any(output.iterdir()):
        raise RunnerError("correctness build calibration output must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    contract = load_contract()
    protocol = contract["resource"]["calibration_protocol"][
        "correctness_build_cell"
    ]
    if (
        protocol["build_only"] is not True
        or protocol["retain_GFLOPS_correctness_or_noise_labels"] is not False
        or sha256_file(S10_MAPPING_CORPUS) != protocol["foundation_source_sha256"]
    ):
        raise RunnerError("correctness build calibration protocol mismatch")
    foundation = _object(S10_MAPPING_CORPUS, label="S10 foundation mapping corpus")
    candidates = [
        row
        for row in foundation.get("rows", [])
        if row.get("config_hash") == protocol["fixed_config_hash"]
    ]
    if len(candidates) != 3:
        raise RunnerError("correctness build foundation config coverage mismatch")
    candidate = candidates[0]["raw_values"]
    client_record = _object(client_build_path, label="pinned client build record")
    client_body = dict(client_record)
    client_digest = client_body.pop("client_build_digest", None)
    if client_digest != canonical_sha256(client_body):
        raise RunnerError("pinned client build record digest mismatch")
    client = Path(str(client_record["client_path"])).resolve()
    _require_run_root(client.parent)
    if sha256_file(client) != client_record["client_sha256"]:
        raise RunnerError("pinned client binary hash mismatch")
    config_path = output / "singleton-build-only.yaml"
    generated_output = output / "generated"
    atomic_write_bytes(
        config_path,
        _singleton_yaml_bytes(
            candidate=candidate,
            sizes=[protocol["fixed_size"]],
            device_index=0,
        ),
        exclusive=True,
    )
    os.chmod(config_path, 0o644)
    command = [
        sys.executable,
        str(
            integration
            / "projects/hipblaslt/tensilelite/Tensile/bin/Tensile"
        ),
        str(config_path),
        str(generated_output),
        "--build-only",
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
        "--prebuilt-client",
        str(client),
    ]
    environment = {
        "PYTHONPATH": str(integration / "projects/hipblaslt/tensilelite"),
        "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
        "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
        "LC_ALL": "C",
    }
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    completed = subprocess.run(
        command,
        cwd=output,
        env=environment,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=3600,
    )
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    atomic_write_bytes(output / "stdout.log", completed.stdout, exclusive=True)
    atomic_write_bytes(output / "stderr.log", completed.stderr, exclusive=True)
    if completed.returncode:
        raise RunnerError(
            "foundation correctness build-only calibration failed: "
            + completed.stderr.decode("utf-8", "replace")[-4000:]
        )
    csv_files = list(generated_output.glob("**/Data/*.csv"))
    if csv_files:
        raise RunnerError("build-only calibration unexpectedly produced benchmark CSV")
    retained = sum(
        path.stat().st_size for path in output.rglob("*") if path.is_file()
    )
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "fixture_id": protocol["fixture_id"],
        "foundation_source_sha256": protocol["foundation_source_sha256"],
        "fixed_config_hash": protocol["fixed_config_hash"],
        "fixed_size_id": protocol["fixed_size_id"],
        "build_only": True,
        "outcome_blind": True,
        "formal_correctness_evidence": False,
        "GFLOPS_correctness_or_noise_labels_retained": False,
        "benchmark_csv_count": 0,
        "config_sha256": sha256_file(config_path),
        "client_build_digest": client_digest,
        "client_sha256": client_record["client_sha256"],
        "elapsed_wall_s": time.monotonic() - started,
        "elapsed_cpu_s": (
            after.ru_utime
            + after.ru_stime
            - before.ru_utime
            - before.ru_stime
        ),
        "elapsed_gpu_s": 0.0,
        "maximum_child_rss_kib": after.ru_maxrss,
        "retained_bytes": retained,
        "generated_file_count": sum(
            1 for path in generated_output.rglob("*") if path.is_file()
        ),
        "exit_status": completed.returncode,
        "stdout_sha256": sha256_file(output / "stdout.log"),
        "stderr_sha256": sha256_file(output / "stderr.log"),
    }
    body["calibration_digest"] = canonical_sha256(body)
    atomic_write_json(
        output / "s10r2-correctness-build-calibration.json",
        body,
        exclusive=True,
    )
    return body


def _object(path: Path | str, *, label: str) -> dict[str, Any]:
    value = strict_load_json(path)
    if not isinstance(value, Mapping):
        raise RunnerError(f"{label} must be a JSON object")
    return dict(value)


def _write_or_match_json(path: Path | str, document: Mapping[str, Any]) -> bool:
    """Write once, or adopt one byte-equivalent complete orphan after a crash."""

    target = Path(path)
    if target.is_file():
        existing = _object(target, label=f"existing {target.name}")
        if existing != dict(document):
            raise RunnerError(f"existing artifact differs from deterministic replay: {target}")
        return True
    atomic_write_json(target, document, exclusive=True)
    return False


def _allocation(document: Mapping[str, Any]) -> Allocation:
    required = {
        "allocation_id",
        "container_name",
        "device_arch",
        "partition_mode",
        "numa_mode",
        "available_wall_s",
        "available_cpu_s",
        "available_gpu_s",
        "valid_from_utc",
        "valid_until_utc",
        "confirmed",
    }
    missing = sorted(required.difference(document))
    if missing:
        raise RunnerError(f"allocation missing keys: {missing}")
    try:
        return Allocation(**{key: document[key] for key in required})
    except TypeError as error:
        raise RunnerError(f"invalid allocation: {error}") from error


def _validate_contract_allocation(
    contract: Mapping[str, Any],
    *,
    at_utc: str | dt.datetime | None = None,
    required_duration_s: float = 0.0,
) -> Allocation:
    path = _resolve_repo_path(
        contract["formal_execution"]["allocation_record"]
    )
    allocation = _allocation(_object(path, label="allocation record"))
    try:
        validation_time = (
            None
            if at_utc is None
            else (
                at_utc
                if isinstance(at_utc, dt.datetime)
                else parse_utc_timestamp(at_utc, field="allocation validation time")
            )
        )
        validate_allocation(
            allocation,
            at_utc=validation_time,
            required_duration_s=required_duration_s,
        )
    except CalibrationError as error:
        raise RunnerError(f"allocation window is not authorized: {error}") from error
    return allocation


def _metrics(document: Mapping[str, Any]) -> CalibrationMetrics:
    names = set(CalibrationMetrics.__dataclass_fields__)
    if set(document) != names | {"metric_provenance"}:
        raise RunnerError(
            "calibration metric keys mismatch: expected metrics plus "
            f"metric_provenance, got {sorted(document)}"
        )
    provenance = document.get("metric_provenance")
    if (
        not isinstance(provenance, Mapping)
        or provenance.get("schema_version") != 2
        or provenance.get("outcome_blind") is not True
    ):
        raise RunnerError("calibration metric provenance is absent or invalid")
    records = provenance.get("records")
    expected_records = {
        "selection",
        "mapping",
        "correctness_build",
        "gpu",
        "native_build",
        "client_build",
    }
    if not isinstance(records, Mapping) or set(records) != expected_records:
        raise RunnerError("calibration metric provenance record set mismatch")
    record_documents: dict[str, dict[str, Any]] = {}
    for name, raw in records.items():
        if not isinstance(raw, Mapping) or set(raw) != {
            "path",
            "sha256",
            "digest_field",
            "document_digest",
        }:
            raise RunnerError(f"invalid calibration provenance binding: {name}")
        relative = str(raw["path"])
        if "s10r1" in relative.lower():
            raise RunnerError("calibration provenance may not reference S10R1")
        path = _resolve_repo_path(relative)
        if sha256_file(path) != raw["sha256"]:
            raise RunnerError(f"calibration provenance file hash mismatch: {name}")
        record = _object(path, label=f"{name} calibration provenance")
        record_documents[name] = record
        body = dict(record)
        digest = body.pop(str(raw["digest_field"]), None)
        if (
            digest != raw["document_digest"]
            or digest != canonical_sha256(body)
        ):
            raise RunnerError(
                f"calibration provenance document digest mismatch: {name}"
            )
    formulas = provenance.get("formulas")
    if not isinstance(formulas, Mapping) or set(formulas) != {
        "correctness_cell_wall_s",
        "correctness_cell_cpu_s",
        "correctness_cell_gpu_s",
        "noise_cell_wall_s",
        "noise_cell_cpu_s",
        "noise_cell_gpu_s",
        "fixed_overhead_wall_s",
        "fixed_overhead_cpu_s",
    }:
        raise RunnerError("calibration metric derivation formula set mismatch")
    selection = record_documents["selection"]
    mapping = record_documents["mapping"]
    correctness = record_documents["correctness_build"]
    gpu = record_documents["gpu"]
    native = record_documents["native_build"]["resource_measurement"]
    client = record_documents["client_build"]
    correctness_wall = (
        float(correctness["elapsed_wall_s"]) + float(gpu["run_wall_s"])
    )
    correctness_cpu = (
        float(correctness["elapsed_cpu_s"]) + float(gpu["elapsed_cpu_s"])
    )
    expected_values = {
        "selection_chunk_wall_s": float(selection["elapsed_wall_s"]),
        "selection_chunk_cpu_s": float(selection["elapsed_cpu_s"]),
        "mapping_row_wall_s": float(mapping["elapsed_wall_s"]),
        "mapping_row_cpu_s": float(mapping["elapsed_cpu_s"]),
        "correctness_cell_wall_s": correctness_wall,
        "correctness_cell_cpu_s": correctness_cpu,
        "correctness_cell_gpu_s": correctness_wall,
        "noise_cell_wall_s": correctness_wall,
        "noise_cell_cpu_s": correctness_cpu,
        "noise_cell_gpu_s": correctness_wall,
        "native_build_wall_s": float(native["wall_s"]),
        "native_build_cpu_s": float(native["cpu_s"]),
        "fixed_overhead_wall_s": (
            float(selection["elapsed_wall_s"])
            + float(mapping["elapsed_wall_s"])
            + float(gpu["elapsed_wall_s"])
            + float(gpu["run_wall_s"])
            + float(client["elapsed_wall_s"])
            + float(correctness["elapsed_wall_s"])
        ),
        "fixed_overhead_cpu_s": (
            float(selection["elapsed_cpu_s"])
            + float(mapping["elapsed_cpu_s"])
            + 2 * float(gpu["elapsed_cpu_s"])
            + float(client["elapsed_cpu_s"])
            + float(correctness["elapsed_cpu_s"])
        ),
    }
    mismatches = {
        name: (document[name], expected)
        for name, expected in expected_values.items()
        if (
            not isinstance(document[name], (int, float))
            or isinstance(document[name], bool)
            or not math.isclose(
                float(document[name]),
                expected,
                rel_tol=1e-15,
                abs_tol=1e-12,
            )
        )
    }
    if mismatches:
        raise RunnerError(
            f"calibration metrics do not reproduce provenance: {mismatches}"
        )
    try:
        return CalibrationMetrics(
            **{name: document[name] for name in names}
        )
    except TypeError as error:
        raise RunnerError(f"invalid calibration metrics: {error}") from error


def validate_contract() -> dict[str, Any]:
    contract = load_contract()
    digest = verify_human_machine_parity(contract, json.loads(json.dumps(contract)))
    lock_ready = False
    lock_digest = None
    if LOCK_PATH.is_file():
        _, lock_digest = require_effective_lock(LOCK_PATH)
        lock_ready = True
    return {
        "checkpoint_id": "S10R2",
        "status": contract["status"],
        "contract_digest": digest,
        "schema_sha256": sha256_file(DEFAULT_SCHEMA_PATH),
        "human_machine_parity": "PASS",
        "effective_lock_digest": lock_digest,
        "formal_evidence_authorized": lock_ready,
    }


def dry_run_schedule(conditional_target_count: int) -> dict[str, Any]:
    if not 0 <= conditional_target_count <= 15:
        raise RunnerError("conditional target count must be in [0,15]")
    targets = [f"dry-run-target-{index:02d}" for index in range(conditional_target_count)]
    result = schedule_summary(targets)
    result.update(
        {
            "checkpoint_id": "S10R2",
            "outcome_blind": True,
            "formal_draws_executed": 0,
            "first_resource_reforecast": {
                "global_chunk": 6,
                "draws": 3072,
            },
        }
    )
    return result


def derive_resource_fixture(
    *,
    allocation_path: Path | str,
    metrics_path: Path | str,
    output_path: Path | str,
    preemp_engineering_s: float,
) -> dict[str, Any]:
    contract = load_contract()
    allocation = _allocation(_object(allocation_path, label="allocation"))
    metrics = _metrics(_object(metrics_path, label="calibration metrics"))
    caps: ResourceCaps | None = None
    status = "CALIBRATION_COMPLETE"
    reason = None
    try:
        caps = derive_caps(allocation, metrics)
    except Exception as error:
        status = "BLOCKED"
        reason = f"{type(error).__name__}: {error}"
    fixture = write_calibration_fixture(
        output_path,
        contract_digest=canonical_sha256(contract),
        source_identity=contract["source_identity"],
        allocation=allocation,
        metrics=metrics,
        caps=caps,
        preemp_engineering_s=preemp_engineering_s,
        status=status,
        reason=reason,
    )
    if status != "CALIBRATION_COMPLETE":
        raise RunnerError(reason or "resource calibration blocked")
    return fixture


def _assert_preoutcome_absence() -> None:
    present = [str(path.relative_to(ROOT)) for path in OUTCOME_PATHS if path.exists()]
    if present:
        raise RunnerError(f"outcome artifact exists before lock seal: {present}")


def _assert_preformal_absence(contract: Mapping[str, Any]) -> None:
    _assert_preoutcome_absence()
    root = _resolve_repo_path(contract["formal_execution"]["run_root"])
    if root.exists() and any(root.iterdir()):
        raise RunnerError("formal run state exists before effective lock seal")


def _resolve_repo_path(relative: str) -> Path:
    candidate = (ROOT / relative).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as error:
        raise RunnerError(f"path escapes repository: {relative}") from error
    return candidate


def _repo_relative(path: Path | str) -> str:
    candidate = Path(path).resolve()
    try:
        return str(candidate.relative_to(ROOT.resolve()))
    except ValueError as error:
        raise RunnerError(f"path is outside repository: {candidate}") from error


def _artifact_binding(
    path: Path | str,
    *,
    document_digest_field: str | None,
) -> dict[str, Any]:
    candidate = Path(path).resolve()
    if not candidate.is_file():
        raise RunnerError(f"lock-bound artifact is absent: {candidate}")
    document_digest = None
    if document_digest_field is not None:
        document = _object(candidate, label=f"bound {candidate.name}")
        body = dict(document)
        document_digest = body.pop(document_digest_field, None)
        if document_digest != canonical_sha256(body):
            raise RunnerError(f"lock-bound document digest mismatch: {candidate}")
    return {
        "path": _repo_relative(candidate),
        "sha256": sha256_file(candidate),
        "document_digest_field": document_digest_field,
        "document_digest": document_digest,
    }


def _lock_artifact_bindings(
    contract: Mapping[str, Any],
    *,
    calibration_path: Path | str,
    registry_path: Path | str,
) -> dict[str, dict[str, Any]]:
    formal = contract["formal_execution"]
    materialization_path = _resolve_repo_path(formal["pinned_materialization_manifest"])
    native_build_path = _resolve_repo_path(formal["native_build_manifest"])
    client_build_path = _resolve_repo_path(formal["client_build_record"])
    size_registry_path = _resolve_repo_path(
        contract["correctness"]["size_registry_path"]
    )
    native = _object(native_build_path, label="native build manifest")
    client = _object(client_build_path, label="client build record")
    native_binary = Path(str(native["binary_path"])).resolve()
    client_binary = Path(str(client["client_path"])).resolve()
    expected_native = contract["native_conformance"]["binding"]
    if (
        native.get("build_manifest_digest") != expected_native["build_manifest_digest"]
        or native.get("binary_sha256") != expected_native["helper_binary_sha256"]
        or sha256_file(native_binary) != expected_native["helper_binary_sha256"]
    ):
        raise RunnerError("native helper binding differs from contract")
    expected_client = contract["resource"]["calibration_protocol"]["client_build"]
    if (
        client.get("client_build_digest") != expected_client["client_build_digest"]
        or client.get("client_sha256") != expected_client["client_sha256"]
        or sha256_file(client_binary) != expected_client["client_sha256"]
    ):
        raise RunnerError("pinned client binding differs from contract")
    return {
        "allocation_record": _artifact_binding(
            _resolve_repo_path(formal["allocation_record"]),
            document_digest_field=None,
        ),
        "calibration_metrics_record": _artifact_binding(
            _resolve_repo_path(formal["calibration_metrics_record"]),
            document_digest_field=None,
        ),
        "candidate_atom_registry": _artifact_binding(
            registry_path,
            document_digest_field="registry_digest",
        ),
        "client_binary": _artifact_binding(
            client_binary,
            document_digest_field=None,
        ),
        "client_build_record": _artifact_binding(
            client_build_path,
            document_digest_field="client_build_digest",
        ),
        "native_build_manifest": _artifact_binding(
            native_build_path,
            document_digest_field="build_manifest_digest",
        ),
        "native_helper_binary": _artifact_binding(
            native_binary,
            document_digest_field=None,
        ),
        "pinned_materialization_manifest": _artifact_binding(
            materialization_path,
            document_digest_field="manifest_digest",
        ),
        "resource_calibration_fixture": _artifact_binding(
            calibration_path,
            document_digest_field="fixture_digest",
        ),
        "size_registry": _artifact_binding(
            size_registry_path,
            document_digest_field="size_registry_digest",
        ),
    }


def create_effective_lock(
    *,
    audit_path: Path | str,
    calibration_path: Path | str,
    registry_path: Path | str = REGISTRY_PATH,
    output_path: Path | str = LOCK_PATH,
) -> dict[str, Any]:
    contract = load_contract()
    if contract["status"] not in {"frozen_pre_evidence", "effective"}:
        raise RunnerError("numeric resource relock is not frozen")
    audit = _object(audit_path, label="adversarial audit")
    calibration = _object(calibration_path, label="calibration fixture")
    expected_registry_path = _resolve_repo_path(
        contract["support"]["candidate_registry_path"]
    )
    if Path(registry_path).resolve() != expected_registry_path:
        raise RunnerError("candidate registry path differs from frozen contract")
    registry = _object(registry_path, label="candidate atom registry")
    recorded_registry_digest = registry.get("registry_digest")
    registry_body = dict(registry)
    registry_body.pop("registry_digest", None)
    if recorded_registry_digest != canonical_sha256(registry_body):
        raise RunnerError("candidate atom registry digest mismatch")
    _assert_preformal_absence(contract)
    implementation = implementation_hashes(
        contract["implementation_whitelist"], repository_root=ROOT
    )
    boundary = contract["resource"]["numeric_relock"]["preemp_engineering"][
        "prospective_boundary_utc"
    ]
    boundary_time = dt.datetime.fromisoformat(
        str(boundary).replace("Z", "+00:00")
    ).timestamp()
    prelock_elapsed_s = time.time() - boundary_time
    body = lock_body(
        contract=contract,
        contract_path=DEFAULT_CONTRACT_PATH,
        schema_path=DEFAULT_SCHEMA_PATH,
        audit=audit,
        allocation_fixture=calibration,
        implementation=implementation,
        registry_digest=str(recorded_registry_digest),
        artifact_bindings=_lock_artifact_bindings(
            contract,
            calibration_path=calibration_path,
            registry_path=registry_path,
        ),
        prelock_elapsed_s=prelock_elapsed_s,
        sealed_at_utc=_utc_now(),
    )
    lock = seal_lock_document(body)
    atomic_write_json(output_path, lock, exclusive=True)
    os.chmod(output_path, 0o644)
    return lock


def _require_committed_lock_projection(
    lock_path: Path | str,
    contract: Mapping[str, Any],
) -> str:
    required_paths = [
        _repo_relative(lock_path),
        *contract["implementation_whitelist"],
        contract["support"]["candidate_registry_path"],
        contract["correctness"]["size_registry_path"],
    ]
    for relative in dict.fromkeys(str(path) for path in required_paths):
        candidate = _resolve_repo_path(relative)
        try:
            head_blob = str(
                _git("rev-parse", f"HEAD:{relative}", text=True)
            ).strip()
            index_blob = str(
                _git("rev-parse", f":{relative}", text=True)
            ).strip()
            worktree_blob = str(
                _git("hash-object", str(candidate), text=True)
            ).strip()
        except subprocess.CalledProcessError as error:
            raise RunnerError(
                f"effective lock projection is not committed: {relative}"
            ) from error
        if not head_blob or head_blob != index_blob or head_blob != worktree_blob:
            raise RunnerError(
                f"effective lock projection differs from committed HEAD: {relative}"
            )
    return str(_git("rev-parse", "HEAD", text=True)).strip()


def require_effective_lock(
    path: Path | str = LOCK_PATH,
    *,
    enforce_allocation_window: bool = True,
    required_allocation_s: float = 0.0,
) -> tuple[dict[str, Any], str]:
    contract = load_contract()
    lock = _object(path, label="effective lock")
    digest = verify_lock_seal(
        lock,
        contract,
        schema_path=DEFAULT_SCHEMA_PATH,
        repository_root=ROOT,
    )
    _require_committed_lock_projection(path, contract)
    if enforce_allocation_window:
        _validate_contract_allocation(
            contract,
            required_duration_s=required_allocation_s,
        )
    return contract, digest


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _tree_size(path: Path | str) -> int:
    root = Path(path)
    if not root.exists():
        return 0
    return sum(item.stat().st_size for item in root.rglob("*") if item.is_file())


def _formal_root(
    contract: Mapping[str, Any],
    override: Path | str | None = None,
) -> Path:
    expected = _resolve_repo_path(contract["formal_execution"]["run_root"])
    if override is not None and Path(override).resolve() != expected:
        raise RunnerError("formal run root differs from frozen contract")
    return _require_run_root(expected)


def _lineage_root(contract: Mapping[str, Any]) -> Path:
    return _require_run_root(
        _resolve_repo_path(contract["formal_execution"]["lineage_root"])
    )


def _integration_root(contract: Mapping[str, Any]) -> Path:
    return _require_run_root(
        _resolve_repo_path(contract["formal_execution"]["pinned_integration_root"])
    )


def _frozen_caps(contract: Mapping[str, Any]) -> FrozenResourceCaps:
    caps = contract["resource"]["numeric_relock"]["caps"]
    return FrozenResourceCaps(
        wall_s=float(caps["wall_s"]),
        cpu_s=float(caps["cpu_s"]),
        gpu_s=float(caps["gpu_s"]),
        transient_storage_bytes=int(caps["transient_storage_bytes"]),
    )


def _counter(value: Mapping[str, Any]) -> ResourceCounter:
    required = {"wall_s", "cpu_s", "gpu_s", "transient_storage_bytes"}
    if set(value) != required:
        raise RunnerError("resource counter fields differ from frozen contract")
    return ResourceCounter(
        wall_s=float(value["wall_s"]),
        cpu_s=float(value["cpu_s"]),
        gpu_s=float(value["gpu_s"]),
        transient_storage_bytes=int(value["transient_storage_bytes"]),
    )


def _reservation(contract: Mapping[str, Any], name: str) -> ResourceCounter:
    reservations = contract["resource"]["numeric_relock"]["reservations"]
    if name not in reservations:
        raise RunnerError(f"unknown frozen resource reservation: {name}")
    return _counter(reservations[name])


def _latest_counter(
    ledger: RunLedger,
    contract: Mapping[str, Any],
) -> ResourceCounter:
    events = ledger.load()
    if events:
        return resource_counter_from_event(events[-1])
    return _counter(contract["resource"]["numeric_relock"]["initial_resource_counter"])


def _absolute_storage_counter(
    previous: ResourceCounter,
    contract: Mapping[str, Any],
    *,
    wall_delta: float = 0.0,
    cpu_delta: float = 0.0,
    gpu_delta: float = 0.0,
) -> ResourceCounter:
    current_storage = _tree_size(_lineage_root(contract))
    return ResourceCounter(
        wall_s=previous.wall_s + wall_delta,
        cpu_s=previous.cpu_s + cpu_delta,
        gpu_s=previous.gpu_s + gpu_delta,
        transient_storage_bytes=max(
            previous.transient_storage_bytes,
            current_storage,
        ),
    )


def _assert_resource_counter(
    counter: ResourceCounter,
    caps: FrozenResourceCaps,
) -> None:
    enforce_stop(counter, ResourceCounter(), caps)


def _resource_exceeded_fields(
    counter: ResourceCounter,
    caps: FrozenResourceCaps,
) -> list[str]:
    values = asdict(counter)
    limits = asdict(caps)
    return sorted(
        name for name, value in values.items() if value > limits[name]
    )


def _allocation_block_if_needed(
    *,
    ledger: RunLedger,
    root: Path,
    contract_digest: str,
    lock_digest: str,
    current: ResourceCounter,
    reservation: ResourceCounter,
    next_atomic_unit: Mapping[str, Any],
    actual_counter: ResourceCounter | None = None,
    completed_artifact_ref: Mapping[str, Any] | None = None,
    recovered_unledgered_complete_artifact: bool = False,
    contract: Mapping[str, Any] | None = None,
    at_utc: str | None = None,
) -> dict[str, Any] | None:
    """Durably block work that starts outside its frozen allocation window."""

    active_contract = load_contract() if contract is None else dict(contract)
    if canonical_sha256(active_contract) != contract_digest:
        raise RunnerError("allocation check contract digest mismatch")
    allocation_path = _resolve_repo_path(
        active_contract["formal_execution"]["allocation_record"]
    )
    allocation = _allocation(_object(allocation_path, label="allocation record"))
    checked_at = at_utc or _utc_now()
    try:
        validate_allocation(
            allocation,
            at_utc=parse_utc_timestamp(
                checked_at, field="allocation check timestamp"
            ),
            required_duration_s=reservation.wall_s,
        )
        return None
    except CalibrationError as error:
        violation = str(error)

    packet_path = root / "allocation-window-decision-packet.json"
    phase = (
        "completed_unit_actual"
        if actual_counter is not None
        else "pre_start_projection"
    )
    terminal_counter = actual_counter if actual_counter is not None else current
    expected_identity = {
        "contract_digest": contract_digest,
        "lock_digest": lock_digest,
        "stop_phase": phase,
        "current_resource_counter": asdict(current),
        "requested_reservation": asdict(reservation),
        "next_atomic_unit": dict(next_atomic_unit),
        "completed_artifact_ref": (
            None if completed_artifact_ref is None else dict(completed_artifact_ref)
        ),
    }
    existing = packet_path.is_file()
    if existing:
        packet = _object(packet_path, label="allocation-window decision packet")
        body = dict(packet)
        recorded = body.pop("allocation_window_packet_digest", None)
        if (
            recorded != canonical_sha256(body)
            or any(packet.get(key) != value for key, value in expected_identity.items())
            or packet.get("block_reason") != "BLOCKED_ALLOCATION_WINDOW"
            or packet.get("scientific_outcome") != "not_evaluated"
            or packet.get("edge") is not None
        ):
            raise RunnerError("allocation-window decision packet identity mismatch")
        terminal_counter = _counter(packet["terminal_resource_counter"])
    else:
        body = {
            "schema_version": 1,
            "checkpoint_id": "S10R2",
            **expected_identity,
            "lifecycle_state": "BLOCKED",
            "block_reason": "BLOCKED_ALLOCATION_WINDOW",
            "scientific_outcome": "not_evaluated",
            "edge": None,
            "checked_at_utc": checked_at,
            "allocation": {
                "allocation_id": allocation.allocation_id,
                "valid_from_utc": allocation.valid_from_utc,
                "valid_until_utc": allocation.valid_until_utc,
            },
            "violation": violation,
            "terminal_resource_counter": asdict(terminal_counter),
            "resume_under_same_lock": False,
            "schedule_or_criterion_changed": False,
        }
        packet = {
            **body,
            "allocation_window_packet_digest": canonical_sha256(body),
        }
        _write_or_match_json(packet_path, packet)
        os.chmod(packet_path, 0o644)
    event = ledger.append(
        _event_payload(
            stage=Stage.BLOCKED,
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            counter=terminal_counter,
            fixture_digest=packet["allocation_window_packet_digest"],
            support_observation_ref={
                "path": _repo_relative(packet_path),
                "sha256": sha256_file(packet_path),
                "allocation_window_packet_digest": packet[
                    "allocation_window_packet_digest"
                ],
            },
            block_reason="BLOCKED_ALLOCATION_WINDOW",
            scientific_outcome="not_evaluated",
            edge=None,
            allocation_stop_phase=phase,
            current_resource_counter=packet["current_resource_counter"],
            requested_reservation=packet["requested_reservation"],
            next_atomic_unit=dict(next_atomic_unit),
            completed_artifact_ref=packet["completed_artifact_ref"],
            recovered_unledgered_complete_artifact=(
                recovered_unledgered_complete_artifact or existing
            ),
            resume_cursor=None,
        )
    )
    ledger.fsync()
    return {
        "status": "BLOCKED_ALLOCATION_WINDOW",
        "scientific_outcome": "not_evaluated",
        "edge": None,
        "stop_phase": phase,
        "violation": packet["violation"],
        "decision_packet": packet,
        "decision_packet_path": _repo_relative(packet_path),
        "event_digest": event["event_digest"],
    }


def _resource_block_if_needed(
    *,
    ledger: RunLedger,
    root: Path,
    contract_digest: str,
    lock_digest: str,
    caps: FrozenResourceCaps,
    current: ResourceCounter,
    reservation: ResourceCounter,
    next_atomic_unit: Mapping[str, Any],
    actual_counter: ResourceCounter | None = None,
    completed_artifact_ref: Mapping[str, Any] | None = None,
    recovered_unledgered_complete_artifact: bool = False,
) -> dict[str, Any] | None:
    """Durably stop one formal run before or after an over-cap atomic unit.

    The caller holds the ledger writer lock.  A completed over-cap artifact is
    bound only to the terminal operational BLOCKED event; it is never advanced
    into its scientific lifecycle stage.
    """

    allocation_block = _allocation_block_if_needed(
        ledger=ledger,
        root=root,
        contract_digest=contract_digest,
        lock_digest=lock_digest,
        current=current,
        reservation=reservation,
        next_atomic_unit=next_atomic_unit,
        actual_counter=actual_counter,
        completed_artifact_ref=completed_artifact_ref,
        recovered_unledgered_complete_artifact=(
            recovered_unledgered_complete_artifact
        ),
    )
    if allocation_block is not None:
        return allocation_block

    packet_path = root / "resource-cap-decision-packet.json"
    phase = (
        "completed_unit_actual"
        if actual_counter is not None
        else "pre_start_projection"
    )
    projected = current.add(reservation)
    candidate = actual_counter if actual_counter is not None else projected
    existing = packet_path.is_file()
    if existing:
        packet = _object(packet_path, label="resource-cap decision packet")
        body = dict(packet)
        recorded = body.pop("resource_cap_packet_digest", None)
        expected_identity = {
            "contract_digest": contract_digest,
            "lock_digest": lock_digest,
            "stop_phase": phase,
            "current_resource_counter": asdict(current),
            "requested_reservation": asdict(reservation),
            "next_atomic_unit": dict(next_atomic_unit),
            "completed_artifact_ref": (
                None
                if completed_artifact_ref is None
                else dict(completed_artifact_ref)
            ),
        }
        if (
            recorded != canonical_sha256(body)
            or any(packet.get(key) != value for key, value in expected_identity.items())
            or packet.get("block_reason") != "BLOCKED_RESOURCE_CAP"
            or packet.get("scientific_outcome") != "not_evaluated"
            or packet.get("edge") is not None
        ):
            raise RunnerError("resource-cap decision packet identity mismatch")
        terminal_counter = _counter(packet["terminal_resource_counter"])
        exceeded = list(packet["exceeded"])
    else:
        exceeded = _resource_exceeded_fields(candidate, caps)
        if not exceeded:
            return None
        terminal_counter = (
            actual_counter if actual_counter is not None else current
        )
        body = {
            "schema_version": 1,
            "checkpoint_id": "S10R2",
            "contract_digest": contract_digest,
            "lock_digest": lock_digest,
            "lifecycle_state": "BLOCKED",
            "block_reason": "BLOCKED_RESOURCE_CAP",
            "scientific_outcome": "not_evaluated",
            "edge": None,
            "stop_phase": phase,
            "current_resource_counter": asdict(current),
            "requested_reservation": asdict(reservation),
            "projected_resource_counter": asdict(projected),
            "measured_resource_counter": (
                None if actual_counter is None else asdict(actual_counter)
            ),
            "terminal_resource_counter": asdict(terminal_counter),
            "caps": asdict(caps),
            "exceeded": exceeded,
            "next_atomic_unit": dict(next_atomic_unit),
            "completed_artifact_ref": (
                None
                if completed_artifact_ref is None
                else dict(completed_artifact_ref)
            ),
            "resume_under_same_lock": False,
            "schedule_or_criterion_changed": False,
        }
        packet = {
            **body,
            "resource_cap_packet_digest": canonical_sha256(body),
        }
        _write_or_match_json(packet_path, packet)
        os.chmod(packet_path, 0o644)
    event = ledger.append(
        _event_payload(
            stage=Stage.BLOCKED,
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            counter=terminal_counter,
            fixture_digest=packet["resource_cap_packet_digest"],
            support_observation_ref={
                "path": _repo_relative(packet_path),
                "sha256": sha256_file(packet_path),
                "resource_cap_packet_digest": packet[
                    "resource_cap_packet_digest"
                ],
            },
            block_reason="BLOCKED_RESOURCE_CAP",
            scientific_outcome="not_evaluated",
            edge=None,
            resource_stop_phase=phase,
            current_resource_counter=packet["current_resource_counter"],
            requested_reservation=packet["requested_reservation"],
            projected_resource_counter=packet["projected_resource_counter"],
            measured_resource_counter=packet["measured_resource_counter"],
            exceeded=exceeded,
            next_atomic_unit=dict(next_atomic_unit),
            completed_artifact_ref=packet["completed_artifact_ref"],
            recovered_unledgered_complete_artifact=(
                recovered_unledgered_complete_artifact or existing
            ),
            resume_cursor=None,
        )
    )
    ledger.fsync()
    return {
        "status": "BLOCKED_RESOURCE_CAP",
        "scientific_outcome": "not_evaluated",
        "edge": None,
        "stop_phase": phase,
        "exceeded": exceeded,
        "decision_packet": packet,
        "decision_packet_path": _repo_relative(packet_path),
        "event_digest": event["event_digest"],
    }


def _event_payload(
    *,
    stage: Stage,
    contract_digest: str,
    lock_digest: str,
    counter: ResourceCounter,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "stage": stage.value,
        "contract_digest": contract_digest,
        "lock_digest": lock_digest,
        "resource_counter": asdict(counter),
        "recorded_at_utc": _utc_now(),
        **extra,
    }


def _load_registry_document() -> tuple[dict[str, Any], AtomRegistry]:
    document = _object(REGISTRY_PATH, label="candidate atom registry")
    axes = axis_specs_from_registry(document)
    registry = AtomRegistry(axes)
    if registry.document() != document:
        raise RunnerError("candidate atom registry round-trip mismatch")
    return document, registry


def _load_size_registry() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    document = _object(SIZE_REGISTRY_PATH, label="size registry")
    body = dict(document)
    recorded = body.pop("size_registry_digest", None)
    if recorded != canonical_sha256(body):
        raise RunnerError("size registry digest mismatch")
    sizes = document.get("sizes")
    if (
        not isinstance(sizes, list)
        or [row.get("size_id") for row in sizes] != ["small", "medium", "large"]
        or [row.get("values") for row in sizes]
        != [[8, 8, 1, 128], [256, 256, 1, 1024], [2304, 1024, 1, 214336]]
    ):
        raise RunnerError("size registry differs from frozen three-size panel")
    return document, [dict(row) for row in sizes]


class _FormalCommandGuard:
    def __init__(self, root: Path):
        self.root = root
        self.descriptor: int | None = None

    def __enter__(self):
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / ".formal-command.lock"
        self.descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(self.descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(self.descriptor)
            self.descriptor = None
            raise RunnerError("another formal S10R2 command is active")
        return self

    def __exit__(self, _type, _value, _traceback):
        if self.descriptor is not None:
            try:
                fcntl.flock(self.descriptor, fcntl.LOCK_UN)
            finally:
                os.close(self.descriptor)
                self.descriptor = None
        return False


def _serialized_formal(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        lock_path = kwargs.get("lock_path", LOCK_PATH)
        contract, lock_digest = require_effective_lock(
            lock_path,
            enforce_allocation_window=False,
        )
        root = _formal_root(contract, kwargs.get("run_root"))
        with _FormalCommandGuard(root):
            ledger = RunLedger(root / "ledger")
            events = ledger.load()
            if not events:
                _validate_contract_allocation(contract)
            elif Stage(events[-1]["stage"]) != Stage.BLOCKED:
                current = _latest_counter(ledger, contract)
                with ledger.acquire_writer():
                    blocked = _allocation_block_if_needed(
                        ledger=ledger,
                        root=root,
                        contract_digest=canonical_sha256(contract),
                        lock_digest=lock_digest,
                        current=current,
                        reservation=ResourceCounter(),
                        next_atomic_unit={
                            "kind": "formal_command_entry",
                            "command": function.__name__,
                        },
                    )
                if blocked is not None:
                    return blocked
            return function(*args, **kwargs)

    return wrapper


def initialize_formal_run(
    *,
    run_root: Path | str | None = None,
    lock_path: Path | str = LOCK_PATH,
) -> dict[str, Any]:
    """Create the sole formal ledger after a verified effective lock."""

    contract, lock_digest = require_effective_lock(
        lock_path,
        enforce_allocation_window=False,
    )
    _validate_contract_allocation(
        contract,
        required_duration_s=float(
            contract["resource"]["numeric_relock"]["caps"]["wall_s"]
        ),
    )
    seal_commit = str(_git("rev-parse", "HEAD", text=True)).strip()
    root = _formal_root(contract, run_root)
    ledger = RunLedger(root / "ledger")
    contract_digest = canonical_sha256(contract)
    initial = _counter(
        contract["resource"]["numeric_relock"]["initial_resource_counter"]
    )
    _assert_resource_counter(initial, _frozen_caps(contract))
    registry_document, _ = _load_registry_document()
    existing = ledger.load()
    if not existing and root.exists():
        unexpected = [
            path for path in root.iterdir() if path.name != "ledger"
        ]
        if unexpected:
            raise RunnerError(
                "formal run root contains state without a recoverable ledger"
            )
    root.mkdir(parents=True, exist_ok=True)
    with ledger.acquire_writer():
        events = ledger.load()
        if not events:
            first = ledger.append(
                _event_payload(
                    stage=Stage.LOCK_SEALED,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=initial,
                    fixture_digest=contract["resource"]["numeric_relock"][
                        "calibration_fixture_digest"
                    ],
                    lock_path=_repo_relative(lock_path),
                    seal_commit=seal_commit,
                    resume_cursor={"stream_id": "global", "next_chunk_index": 0},
                )
            )
            ledger.fsync()
            events = [first]
        else:
            first = events[0]
            if (
                Stage(first["stage"]) != Stage.LOCK_SEALED
                or first["contract_digest"] != contract_digest
                or first["lock_digest"] != lock_digest
            ):
                raise RunnerError("formal initialization ledger identity mismatch")
        if len(events) > 1:
            if (
                len(events) == 2
                and Stage(events[1]["stage"]) == Stage.PRE_DRAW_REGISTRY_FROZEN
            ):
                second = events[1]
                return {
                    "status": "FORMAL_RUN_ALREADY_INITIALIZED",
                    "formal_root": _repo_relative(root),
                    "lock_event_digest": first["event_digest"],
                    "registry_event_digest": second["event_digest"],
                    "scientific_outcome": "not_evaluated",
                    "edge": None,
                }
            raise RunnerError("formal run has advanced beyond initialization")
        current = _absolute_storage_counter(initial, contract)
        _assert_resource_counter(current, _frozen_caps(contract))
        second = ledger.append(
            _event_payload(
                stage=Stage.PRE_DRAW_REGISTRY_FROZEN,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                counter=current,
                fixture_digest=registry_document["registry_digest"],
                support_observation_ref={
                    "path": _repo_relative(REGISTRY_PATH),
                    "sha256": sha256_file(REGISTRY_PATH),
                    "registry_digest": registry_document["registry_digest"],
                },
                resume_cursor={"stream_id": "global", "next_chunk_index": 0},
            )
        )
        ledger.fsync()
    return {
        "status": "FORMAL_RUN_INITIALIZED",
        "formal_root": _repo_relative(root),
        "lock_event_digest": first["event_digest"],
        "registry_event_digest": second["event_digest"],
        "scientific_outcome": "not_evaluated",
        "edge": None,
    }


def _discovery_events(ledger: RunLedger) -> list[dict[str, Any]]:
    return [
        event
        for event in ledger.load()
        if event["stage"]
        in {Stage.GLOBAL_DISCOVERY.value, Stage.CONDITIONAL_DISCOVERY.value}
    ]


def _activation_event(ledger: RunLedger) -> dict[str, Any] | None:
    events = [
        event
        for event in ledger.load()
        if event["stage"] == Stage.CONDITIONAL_ACTIVATION.value
    ]
    if len(events) > 1:
        raise RunnerError("formal ledger has more than one conditional activation")
    return None if not events else events[0]


def _load_chunk_record(event: Mapping[str, Any]) -> dict[str, Any]:
    reference = event.get("support_observation_ref")
    if not isinstance(reference, Mapping):
        raise RunnerError("discovery event lacks chunk reference")
    path = _resolve_repo_path(str(reference["path"]))
    if sha256_file(path) != reference.get("sha256"):
        raise RunnerError("discovery chunk raw hash mismatch")
    document = _object(path, label="discovery chunk")
    body = dict(document)
    recorded = body.pop("chunk_digest", None)
    if recorded != canonical_sha256(body) or recorded != reference.get("chunk_digest"):
        raise RunnerError("discovery chunk semantic digest mismatch")
    if (
        document.get("stream_id") != event.get("stream_id")
        or document.get("chunk_index") != event.get("chunk_index")
    ):
        raise RunnerError("discovery chunk identity differs from ledger")
    return document


def _covered_atom_ids(
    registry: AtomRegistry,
    candidate_indices: Mapping[str, Any],
) -> list[str]:
    by_axis_value = {
        (int(row["axis_index"]), int(row["value_index"])): row["atom_id"]
        for row in registry.rows
    }
    covered = []
    for axis in registry.axes:
        value_index = candidate_indices.get(axis.axis_name)
        if type(value_index) is not int:
            raise RunnerError("accepted witness lacks exact candidate index")
        try:
            covered.append(by_axis_value[(axis.axis_index, value_index)])
        except KeyError as error:
            raise RunnerError("accepted witness candidate index is out of range") from error
    return sorted(covered)


def _witnesses_from_events(
    ledger: RunLedger,
    registry: AtomRegistry,
) -> list[dict[str, Any]]:
    activation = _activation_event(ledger)
    ranks = (
        {}
        if activation is None
        else {
            atom_id: index
            for index, atom_id in enumerate(activation["activated_targets"])
        }
    )
    witnesses = []
    for event in _discovery_events(ledger):
        record = _load_chunk_record(event)
        stream_id = str(record["stream_id"])
        conditional = stream_id != "global"
        target_id = record.get("fixed_atom_id")
        if conditional and target_id not in ranks:
            raise RunnerError("conditional discovery stream is not activated")
        for row in record["accepted"]:
            occurrence = {
                "stream_rank": 1 if conditional else 0,
                "conditional_priority_rank": (
                    ranks[target_id] if conditional else -1
                ),
                "stream_id": stream_id,
                "conditional_target_atom_id": target_id,
                "chunk_index": int(record["chunk_index"]),
                "draw_index": int(row["draw_index"]),
                "config_hash": str(row["config_hash"]),
                "candidate_indices": dict(row["candidate_indices"]),
                "config": dict(row["config"]),
                "covered_atom_ids": _covered_atom_ids(
                    registry, row["candidate_indices"]
                ),
                "validity_provenance": {
                    "chunk_digest": record["chunk_digest"],
                    "validator_worker_sha256": record["validator_measurement"][
                        "worker_sha256"
                    ],
                    "ductile_commit": DUCTILE_COMMIT,
                },
            }
            occurrence["occurrence_id"] = canonical_sha256(occurrence)
            witnesses.append(occurrence)
    return witnesses


def _global_states(
    ledger: RunLedger,
    registry: AtomRegistry,
) -> dict[str, str]:
    witnessed: set[str] = set()
    for event in _discovery_events(ledger):
        if event["stage"] != Stage.GLOBAL_DISCOVERY.value:
            continue
        record = _load_chunk_record(event)
        for row in record["accepted"]:
            witnessed.update(_covered_atom_ids(registry, row["candidate_indices"]))
    return classify_support(registry, witnessed)


def _next_discovery_unit(
    ledger: RunLedger,
    registry: AtomRegistry,
) -> tuple[str, int, Mapping[str, Any] | None, int] | None:
    events = ledger.load()
    if not events:
        raise RunnerError("formal run has not been initialized")
    last = Stage(events[-1]["stage"])
    if last not in {
        Stage.PRE_DRAW_REGISTRY_FROZEN,
        Stage.GLOBAL_DISCOVERY,
        Stage.CONDITIONAL_ACTIVATION,
        Stage.CONDITIONAL_DISCOVERY,
    }:
        raise RunnerError(f"formal discovery is not legal from {last.value}")
    global_events = [
        event
        for event in events
        if event["stage"] == Stage.GLOBAL_DISCOVERY.value
    ]
    if len(global_events) < GLOBAL_CHUNKS:
        if [event["chunk_index"] for event in global_events] != list(
            range(len(global_events))
        ):
            raise RunnerError("global chunk indices are not contiguous")
        return "global", len(global_events), None, -1
    activation = _activation_event(ledger)
    if activation is None:
        return None
    targets = activation["activated_targets"]
    rows = registry.row_by_atom()
    for rank, atom_id in enumerate(targets):
        stream_id = f"conditional-{rank:04d}-{atom_id.replace('/', '_')}"
        completed = [
            event
            for event in events
            if event["stage"] == Stage.CONDITIONAL_DISCOVERY.value
            and event["stream_id"] == stream_id
        ]
        if len(completed) < CONDITIONAL_CHUNKS:
            if [event["chunk_index"] for event in completed] != list(
                range(len(completed))
            ):
                raise RunnerError("conditional chunk indices are not contiguous")
            return stream_id, len(completed), rows[atom_id], rank
    return None


def _append_conditional_activation(
    *,
    ledger: RunLedger,
    contract: Mapping[str, Any],
    contract_digest: str,
    lock_digest: str,
    registry: AtomRegistry,
) -> dict[str, Any]:
    if _activation_event(ledger) is not None:
        raise RunnerError("conditional activation already exists")
    global_events = [
        event
        for event in ledger.load()
        if event["stage"] == Stage.GLOBAL_DISCOVERY.value
    ]
    states = _global_states(ledger, registry)
    targets = activate_targets(
        registry,
        states,
        completed_global_chunks=len(global_events),
    )
    current = _latest_counter(ledger, contract)
    return ledger.append(
        _event_payload(
            stage=Stage.CONDITIONAL_ACTIVATION,
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            counter=current,
            fixture_digest=REGISTRY_PATH.name,
            activated_targets=targets,
            schedule=schedule_summary(targets),
            activation_rule=(
                "first_15_final_global_unobserved_by_frozen_priority"
            ),
            resume_cursor={
                "stream_id": None if not targets else "conditional-0000",
                "next_chunk_index": None if not targets else 0,
            },
        )
    )


def _resource_reforecast(
    *,
    contract: Mapping[str, Any],
    ledger: RunLedger,
    pending_measurement: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    chunks = [
        event
        for event in ledger.load()
        if event["stage"] == Stage.GLOBAL_DISCOVERY.value
    ]
    measurements = [event["measurement"] for event in chunks]
    if pending_measurement is not None:
        if len(chunks) != 5:
            raise RunnerError(
                "pending first resource reforecast requires five durable chunks"
            )
        measurements.append(pending_measurement)
    elif len(measurements) >= 6:
        measurements = measurements[:6]
    if len(measurements) != 6:
        raise RunnerError("first resource reforecast requires exactly six global chunks")
    wall = sum(float(measurement["wall_s"]) for measurement in measurements)
    cpu = sum(float(measurement["cpu_s"]) for measurement in measurements)
    numeric = contract["resource"]["numeric_relock"]
    projection = numeric["unbuffered_projection"]
    metrics = contract["resource"]["calibration_protocol"]["metric_derivation"]
    calibrated_selection_wall = (
        contract["resource"]["calibration_protocol"]["selection_chunk"]["wall_s"]
        * 512
    )
    calibrated_selection_cpu = (
        contract["resource"]["calibration_protocol"]["selection_chunk"]["cpu_s"]
        * 512
    )
    projected_wall = (
        float(projection["wall_s"])
        - calibrated_selection_wall
        + wall / 6 * 512
    )
    projected_cpu = (
        float(projection["cpu_s"])
        - calibrated_selection_cpu
        + cpu / 6 * 512
    )
    current_storage = _tree_size(_lineage_root(contract))
    storage_projection = max(
        current_storage,
        int(projection["transient_storage_bytes"]),
    )
    caps = numeric["caps"]
    exceeded = []
    for name, value in (
        ("wall_s", projected_wall),
        ("cpu_s", projected_cpu),
        ("gpu_s", float(projection["gpu_s"])),
        ("transient_storage_bytes", storage_projection),
    ):
        if value > float(caps[name]):
            exceeded.append(name)
    return {
        "boundary_global_chunk": 6,
        "boundary_draws": 3072,
        "label_blind_inputs": [
            "chunk_count",
            "elapsed_wall_s",
            "elapsed_cpu_s",
            "transient_storage_bytes",
        ],
        "support_labels_read": False,
        "observed_selection_wall_s": wall,
        "observed_selection_cpu_s": cpu,
        "projected": {
            "wall_s": projected_wall,
            "cpu_s": projected_cpu,
            "gpu_s": float(projection["gpu_s"]),
            "transient_storage_bytes": storage_projection,
        },
        "caps": dict(caps),
        "status": "BLOCKED_RESOURCE_CAP" if exceeded else "PASS",
        "exceeded": exceeded,
        "metric_derivation_identity": canonical_sha256(metrics),
    }


def _recorded_reforecast(
    ledger: RunLedger,
    *,
    contract: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    global_events = [
        event
        for event in ledger.load()
        if event["stage"] == Stage.GLOBAL_DISCOVERY.value
    ]
    if len(global_events) < 6:
        return None
    boundary = global_events[5]
    reference = boundary.get("resource_reforecast_ref")
    if not isinstance(reference, Mapping):
        raise RunnerError("global chunk 6 lacks its frozen resource reforecast")
    path = _resolve_repo_path(str(reference["path"]))
    if sha256_file(path) != reference.get("sha256"):
        raise RunnerError("resource reforecast file/hash mismatch")
    document = _object(path, label="resource reforecast")
    reproduced = _resource_reforecast(contract=contract, ledger=ledger)
    if document != reproduced or document.get("status") != reference.get("status"):
        raise RunnerError("resource reforecast does not reproduce")
    if document["status"] != "PASS" and len(global_events) != 6:
        raise RunnerError("discovery advanced beyond a blocked resource reforecast")
    return document, boundary


@_serialized_formal
def formal_discovery_step(
    *,
    max_new_chunks: int,
    run_root: Path | str | None = None,
    lock_path: Path | str = LOCK_PATH,
) -> dict[str, Any]:
    """Resume the fixed CPU validity-only schedule at atomic chunk boundaries."""

    if type(max_new_chunks) is not int or max_new_chunks < 1:
        raise RunnerError("max_new_chunks must be a positive integer")
    contract, lock_digest = require_effective_lock(lock_path)
    root = _formal_root(contract, run_root)
    ledger = RunLedger(root / "ledger")
    contract_digest = canonical_sha256(contract)
    _, registry = _load_registry_document()
    axes = axis_specs_from_registry(registry.document())
    probabilities = {
        axis.axis_name: axis.probabilities
        for axis in axes
        if axis.currently_weighted
    }
    caps = _frozen_caps(contract)
    completed_now = 0
    with ledger.acquire_writer():
        recorded_reforecast = _recorded_reforecast(
            ledger,
            contract=contract,
        )
        if (
            recorded_reforecast is not None
            and recorded_reforecast[0]["status"] != "PASS"
        ):
            reforecast, boundary = recorded_reforecast
            events = ledger.load()
            if Stage(events[-1]["stage"]) == Stage.GLOBAL_DISCOVERY:
                blocked = ledger.append(
                    _event_payload(
                        stage=Stage.BLOCKED,
                        contract_digest=contract_digest,
                        lock_digest=lock_digest,
                        counter=resource_counter_from_event(boundary),
                        fixture_digest=canonical_sha256(reforecast),
                        support_observation_ref=boundary[
                            "resource_reforecast_ref"
                        ],
                        block_reason="BLOCKED_RESOURCE_CAP",
                        resume_cursor=None,
                        recovered_after_boundary=True,
                    )
                )
                ledger.fsync()
            else:
                blocked = events[-1]
            return {
                "status": "BLOCKED_RESOURCE_CAP",
                "completed_now": 0,
                "last_event_digest": blocked["event_digest"],
                "reforecast": reforecast,
            }
        while completed_now < max_new_chunks:
            unit = _next_discovery_unit(ledger, registry)
            if unit is None:
                global_count = sum(
                    event["stage"] == Stage.GLOBAL_DISCOVERY.value
                    for event in ledger.load()
                )
                if global_count == GLOBAL_CHUNKS and _activation_event(ledger) is None:
                    _append_conditional_activation(
                        ledger=ledger,
                        contract=contract,
                        contract_digest=contract_digest,
                        lock_digest=lock_digest,
                        registry=registry,
                    )
                    ledger.fsync()
                    unit = _next_discovery_unit(ledger, registry)
                    if unit is None:
                        break
                else:
                    break
            stream_id, chunk_index, fixed_atom, target_rank = unit
            current = _latest_counter(ledger, contract)
            safe_stream = stream_id.replace("/", "_")
            chunk_root = root / "discovery" / safe_stream / f"chunk-{chunk_index:04d}"
            chunk_path = chunk_root / "chunk.json"
            recovered = chunk_path.is_file()
            if recovered:
                record = _object(chunk_path, label="unledgered discovery chunk")
                body = dict(record)
                recorded = body.pop("chunk_digest", None)
                if (
                    recorded != canonical_sha256(body)
                    or record.get("contract_digest") != contract_digest
                    or record.get("lock_digest") != lock_digest
                    or record.get("stream_id") != stream_id
                    or record.get("chunk_index") != chunk_index
                    or record.get("fixed_atom_id")
                    != (None if fixed_atom is None else fixed_atom["atom_id"])
                    or record.get("target_rank") != target_rank
                ):
                    raise RunnerError("unledgered discovery chunk cannot be adopted")
                measurement = record.get("validator_measurement")
                if not isinstance(measurement, Mapping):
                    raise RunnerError("unledgered discovery chunk lacks measurement")
            else:
                reservation = _reservation(contract, "selection_chunk")
                blocked = _resource_block_if_needed(
                    ledger=ledger,
                    root=root,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    caps=caps,
                    current=current,
                    reservation=reservation,
                    next_atomic_unit={
                        "kind": "selection_chunk",
                        "stream_id": stream_id,
                        "chunk_index": chunk_index,
                        "fixed_atom_id": (
                            None
                            if fixed_atom is None
                            else fixed_atom["atom_id"]
                        ),
                    },
                )
                if blocked is not None:
                    return {**blocked, "completed_now": completed_now}
                chunk_root.mkdir(parents=True, exist_ok=True)
                attempts = (
                    []
                    if not chunk_root.exists()
                    else sorted(
                        path
                        for path in chunk_root.iterdir()
                        if path.is_dir() and path.name.startswith("attempt-")
                    )
                )
                if attempts:
                    raise RunnerError(
                        "incomplete discovery attempt has no complete chunk; "
                        "resource accounting cannot safely resume"
                    )
                attempt = chunk_root / "attempt-0000"
                draws = generate_discovery_draws(
                    axes,
                    probabilities,
                    base_seed=int(contract["schedule"]["base_seed"]),
                    stream_id=stream_id,
                    chunk_index=chunk_index,
                    fixed_atom=fixed_atom,
                )
                results, measurement = run_pinned_validator_batch(
                    integration_root=_integration_root(contract),
                    configs=[row["config"] for row in draws["rows"]],
                    scratch_root=attempt / "validator",
                    retain_results=True,
                )
                record = finalize_discovery_chunk(draws, results)
                record["validator_measurement"] = measurement
                record["contract_digest"] = contract_digest
                record["lock_digest"] = lock_digest
                record["target_rank"] = target_rank
                body = dict(record)
                body.pop("chunk_digest", None)
                record["chunk_digest"] = canonical_sha256(body)
                atomic_write_json(chunk_path, record, exclusive=True)
            reforecast = None
            reforecast_ref = None
            if stream_id == "global" and chunk_index == 5:
                reforecast = _resource_reforecast(
                    contract=contract,
                    ledger=ledger,
                    pending_measurement=measurement,
                )
                reforecast_path = root / "resource-reforecast-3072.json"
                _write_or_match_json(reforecast_path, reforecast)
                reforecast_ref = {
                    "path": _repo_relative(reforecast_path),
                    "sha256": sha256_file(reforecast_path),
                    "status": reforecast["status"],
                }
            next_counter = _absolute_storage_counter(
                current,
                contract,
                wall_delta=float(measurement["wall_s"]),
                cpu_delta=float(measurement["cpu_s"]),
            )
            chunk_reference = {
                "path": _repo_relative(chunk_path),
                "sha256": sha256_file(chunk_path),
                "chunk_digest": record["chunk_digest"],
            }
            if reforecast_ref is not None:
                chunk_reference["resource_reforecast_ref"] = reforecast_ref
            blocked = _resource_block_if_needed(
                ledger=ledger,
                root=root,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                caps=caps,
                current=current,
                reservation=_reservation(contract, "selection_chunk"),
                actual_counter=next_counter,
                next_atomic_unit={
                    "kind": "selection_chunk",
                    "stream_id": stream_id,
                    "chunk_index": chunk_index,
                    "fixed_atom_id": (
                        None if fixed_atom is None else fixed_atom["atom_id"]
                    ),
                },
                completed_artifact_ref=chunk_reference,
                recovered_unledgered_complete_artifact=recovered,
            )
            if blocked is not None:
                return {**blocked, "completed_now": completed_now}
            stage = (
                Stage.GLOBAL_DISCOVERY
                if stream_id == "global"
                else Stage.CONDITIONAL_DISCOVERY
            )
            event = ledger.append(
                _event_payload(
                    stage=stage,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=next_counter,
                    stream_id=stream_id,
                    chunk_index=chunk_index,
                    draw_interval=[
                        chunk_index * 512,
                        (chunk_index + 1) * 512,
                    ],
                    fixture_digest=record["chunk_digest"],
                    support_observation_ref=chunk_reference,
                    measurement=measurement,
                    recovered_unledgered_complete_chunk=recovered,
                    target_rank=target_rank,
                    resource_reforecast_ref=reforecast_ref,
                    resume_cursor={
                        "stream_id": stream_id,
                        "next_chunk_index": chunk_index + 1,
                    },
                )
            )
            ledger.fsync()
            completed_now += 1
            if reforecast is not None and reforecast["status"] != "PASS":
                blocked = ledger.append(
                    _event_payload(
                        stage=Stage.BLOCKED,
                        contract_digest=contract_digest,
                        lock_digest=lock_digest,
                        counter=next_counter,
                        fixture_digest=canonical_sha256(reforecast),
                        support_observation_ref=reforecast_ref,
                        block_reason="BLOCKED_RESOURCE_CAP",
                        resume_cursor=None,
                    )
                )
                ledger.fsync()
                return {
                    "status": "BLOCKED_RESOURCE_CAP",
                    "completed_now": completed_now,
                    "last_event_digest": blocked["event_digest"],
                    "reforecast": reforecast,
                }
        if (
            sum(
                event["stage"] == Stage.GLOBAL_DISCOVERY.value
                for event in ledger.load()
            )
            == GLOBAL_CHUNKS
            and _activation_event(ledger) is None
        ):
            _append_conditional_activation(
                ledger=ledger,
                contract=contract,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                registry=registry,
            )
            ledger.fsync()
    unit = _next_discovery_unit(ledger, registry)
    return {
        "status": "SELECTION_COMPLETE" if unit is None else "SELECTION_IN_PROGRESS",
        "completed_now": completed_now,
        "total_completed_chunks": len(_discovery_events(ledger)),
        "resume_cursor": asdict(ledger.resume_cursor()),
        "scientific_outcome": "not_evaluated",
        "edge": None,
    }


@_serialized_formal
def seal_support_classification(
    *,
    run_root: Path | str | None = None,
    lock_path: Path | str = LOCK_PATH,
    output_path: Path | str = SUPPORT_PATH,
) -> dict[str, Any]:
    """Seal final tri-state support only after the complete fixed schedule."""

    contract, lock_digest = require_effective_lock(lock_path)
    root = _formal_root(contract, run_root)
    ledger = RunLedger(root / "ledger")
    contract_digest = canonical_sha256(contract)
    registry_document, registry = _load_registry_document()
    if _next_discovery_unit(ledger, registry) is not None:
        raise RunnerError("fixed discovery schedule is incomplete")
    activation = _activation_event(ledger)
    if activation is None:
        raise RunnerError("conditional activation was not durably recorded")
    events = ledger.load()
    if Stage(events[-1]["stage"]) not in {
        Stage.CONDITIONAL_ACTIVATION,
        Stage.CONDITIONAL_DISCOVERY,
    }:
        raise RunnerError("support seal is not legal from current stage")
    witnesses = _witnesses_from_events(ledger, registry)
    witnessed_atoms = {
        atom_id for witness in witnesses for atom_id in witness["covered_atom_ids"]
    }
    states = classify_support(registry, witnessed_atoms)
    first_witness: dict[str, str] = {}
    for witness in sorted(
        witnesses,
        key=lambda row: (
            row["stream_rank"],
            row["conditional_priority_rank"],
            row["chunk_index"],
            row["draw_index"],
            row["config_hash"],
        ),
    ):
        for atom_id in witness["covered_atom_ids"]:
            first_witness.setdefault(atom_id, witness["occurrence_id"])
    atom_rows = [
        {
            "atom_id": row["atom_id"],
            "axis_id": row["axis_id"],
            "axis_index": row["axis_index"],
            "axis_name": row["axis_name"],
            "value_index": row["value_index"],
            "exact_typed_value": row["exact_typed_value"],
            "state": states[row["atom_id"]],
            "first_witness_occurrence_id": first_witness.get(row["atom_id"]),
            "complete_absence_proof": None,
        }
        for row in registry.rows
    ]
    guidance = []
    for axis in registry.axes:
        axis_rows = [
            row for row in atom_rows if row["axis_index"] == axis.axis_index
        ]
        all_witnessed = all(
            row["state"] == "supported_witnessed" for row in axis_rows
        )
        guidance.append(
            {
                "axis_id": f"axis/a{axis.axis_index:02d}/{axis.axis_name}",
                "axis_name": axis.axis_name,
                "grouped": axis.grouped,
                "residual_candidate_gene": (
                    not axis.grouped
                    and not axis.currently_weighted
                    and axis.frozen_free
                    and len(axis.values) > 1
                ),
                "all_candidate_values_witnessed": all_witnessed,
                "s11_guidance_eligible": (
                    not axis.grouped
                    and not axis.currently_weighted
                    and axis.frozen_free
                    and len(axis.values) > 1
                    and all_witnessed
                ),
                "baseline_sampling_semantics_unchanged": True,
            }
        )
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "contract_digest": contract_digest,
        "lock_digest": lock_digest,
        "registry_digest": registry_document["registry_digest"],
        "schedule": activation["schedule"],
        "activated_targets": activation["activated_targets"],
        "completed_chunks": len(_discovery_events(ledger)),
        "completed_draws": len(_discovery_events(ledger)) * 512,
        "accepted_occurrences": len(witnesses),
        "distinct_valid_config_hashes": len(
            {witness["config_hash"] for witness in witnesses}
        ),
        "state_counts": {
            state: sum(value == state for value in states.values())
            for state in (
                "supported_witnessed",
                "support_unobserved",
                "support_proven_absent",
            )
        },
        "stochastic_zero_implies_absence": False,
        "complete_absence_proofs": [],
        "atoms": atom_rows,
        "guidance_eligibility": guidance,
        "raw_witness_ledger_root": _repo_relative(root / "ledger"),
    }
    document = {**body, "support_classification_digest": canonical_sha256(body)}
    recovered = _write_or_match_json(output_path, document)
    os.chmod(output_path, 0o644)
    current_before = _latest_counter(ledger, contract)
    current = _absolute_storage_counter(current_before, contract)
    with ledger.acquire_writer():
        blocked = _resource_block_if_needed(
            ledger=ledger,
            root=root,
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            caps=_frozen_caps(contract),
            current=current_before,
            reservation=ResourceCounter(),
            actual_counter=current,
            next_atomic_unit={"kind": "support_classification_seal"},
            completed_artifact_ref={
                "path": _repo_relative(output_path),
                "sha256": sha256_file(output_path),
                "support_classification_digest": document[
                    "support_classification_digest"
                ],
            },
            recovered_unledgered_complete_artifact=recovered,
        )
        if blocked is not None:
            return blocked
        event = ledger.append(
            _event_payload(
                stage=Stage.SUPPORT_CLASSIFICATION_SEALED,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                counter=current,
                fixture_digest=document["support_classification_digest"],
                support_observation_ref={
                    "path": _repo_relative(output_path),
                    "sha256": sha256_file(output_path),
                    "support_classification_digest": document[
                        "support_classification_digest"
                    ],
                },
                resume_cursor=None,
                recovered_unledgered_complete_artifact=recovered,
            )
        )
        ledger.fsync()
    return {
        "status": "SUPPORT_CLASSIFICATION_SEALED",
        "state_counts": document["state_counts"],
        "distinct_valid_config_hashes": document["distinct_valid_config_hashes"],
        "event_digest": event["event_digest"],
    }


def _decision_document(
    *,
    contract_digest: str,
    lock_digest: str,
    classification: str,
    criterion: str | None,
    failure_id: str | None,
    evidence: Mapping[str, Any],
    activation_state: str,
) -> dict[str, Any]:
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "contract_digest": contract_digest,
        "lock_digest": lock_digest,
        "classification": classification,
        "criterion": criterion,
        "failure_id": failure_id,
        "edge": None,
        "activation_state": activation_state,
        "fresh_verifier_required": True,
        "closeout_ack_required": classification == "positive",
        "evidence": dict(evidence),
        "claim_boundary": (
            "credible and reproducible Stage-1 entry boundary within observed "
            "operational valid support"
        ),
    }
    return {**body, "decision_digest": canonical_sha256(body)}


@_serialized_formal
def select_exact_ten(
    *,
    run_root: Path | str | None = None,
    lock_path: Path | str = LOCK_PATH,
) -> dict[str, Any]:
    """Apply the frozen score-blind exact-ten set-cover rule."""

    contract, lock_digest = require_effective_lock(lock_path)
    root = _formal_root(contract, run_root)
    ledger = RunLedger(root / "ledger")
    events = ledger.load()
    if not events or Stage(events[-1]["stage"]) != Stage.SUPPORT_CLASSIFICATION_SEALED:
        raise RunnerError("exact-ten selection requires sealed support classification")
    contract_digest = canonical_sha256(contract)
    support_document = _object(SUPPORT_PATH, label="support classification")
    support_body = dict(support_document)
    support_recorded = support_body.pop("support_classification_digest", None)
    if (
        support_recorded != canonical_sha256(support_body)
        or support_document.get("contract_digest") != contract_digest
        or support_document.get("lock_digest") != lock_digest
    ):
        raise RunnerError("support classification binding mismatch")
    _, registry = _load_registry_document()
    states = {
        row["atom_id"]: row["state"] for row in support_document["atoms"]
    }
    required = mandatory_atoms(registry.prelocked_atoms(), states)
    witnesses = _witnesses_from_events(ledger, registry)
    try:
        selection = exact_ten_greedy_cover(witnesses, required)
    except MappingError as error:
        if "FT-INCONCLUSIVE" not in str(error):
            raise
        decision = _decision_document(
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            classification="inconclusive",
            criterion=None,
            failure_id="FT-INCONCLUSIVE",
            evidence={
                "support_classification_digest": support_recorded,
                "reason": str(error),
                "mapping_started": False,
            },
            activation_state="pending_fresh_verification_and_closeout",
        )
        current_before = _latest_counter(ledger, contract)
        decision_recovered_before = DECISION_PATH.is_file()
        if not decision_recovered_before:
            with ledger.acquire_writer():
                blocked = _resource_block_if_needed(
                    ledger=ledger,
                    root=root,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    caps=_frozen_caps(contract),
                    current=current_before,
                    reservation=_reservation(contract, "decision"),
                    next_atomic_unit={
                        "kind": "decision",
                        "classification": "inconclusive",
                    },
                )
            if blocked is not None:
                return blocked
        recovered_decision = _write_or_match_json(DECISION_PATH, decision)
        os.chmod(DECISION_PATH, 0o644)
        current = _absolute_storage_counter(current_before, contract)
        with ledger.acquire_writer():
            blocked = _resource_block_if_needed(
                ledger=ledger,
                root=root,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                caps=_frozen_caps(contract),
                current=current_before,
                reservation=_reservation(contract, "decision"),
                actual_counter=current,
                next_atomic_unit={
                    "kind": "decision",
                    "classification": "inconclusive",
                },
                completed_artifact_ref={
                    "path": _repo_relative(DECISION_PATH),
                    "sha256": sha256_file(DECISION_PATH),
                    "decision_digest": decision["decision_digest"],
                },
                recovered_unledgered_complete_artifact=(
                    recovered_decision or decision_recovered_before
                ),
            )
            if blocked is not None:
                return blocked
            event = ledger.append(
                _event_payload(
                    stage=Stage.TERMINAL_INCONCLUSIVE,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=current,
                    fixture_digest=decision["decision_digest"],
                    support_observation_ref={
                        "path": _repo_relative(DECISION_PATH),
                        "sha256": sha256_file(DECISION_PATH),
                    },
                    resume_cursor=None,
                    recovered_unledgered_complete_artifact=recovered_decision,
                )
            )
            ledger.fsync()
        return {
            "status": "TERMINAL_INCONCLUSIVE_PENDING_VERIFICATION",
            "failure_id": "FT-INCONCLUSIVE",
            "reason": str(error),
            "event_digest": event["event_digest"],
        }
    selection.update(
        {
            "contract_digest": contract_digest,
            "lock_digest": lock_digest,
            "support_classification_digest": support_recorded,
            "performance_blind": True,
        }
    )
    body = dict(selection)
    body.pop("mapping_corpus_digest", None)
    selection["mapping_corpus_digest"] = canonical_sha256(body)
    selection_path = root / "exact-ten-selection.json"
    recovered = _write_or_match_json(selection_path, selection)
    current_before = _latest_counter(ledger, contract)
    current = _absolute_storage_counter(current_before, contract)
    with ledger.acquire_writer():
        blocked = _resource_block_if_needed(
            ledger=ledger,
            root=root,
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            caps=_frozen_caps(contract),
            current=current_before,
            reservation=ResourceCounter(),
            actual_counter=current,
            next_atomic_unit={"kind": "exact_ten_selection"},
            completed_artifact_ref={
                "path": _repo_relative(selection_path),
                "sha256": sha256_file(selection_path),
                "mapping_corpus_digest": selection[
                    "mapping_corpus_digest"
                ],
            },
            recovered_unledgered_complete_artifact=recovered,
        )
        if blocked is not None:
            return blocked
        event = ledger.append(
            _event_payload(
                stage=Stage.EXACT_TEN_SELECTED,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                counter=current,
                fixture_digest=selection["mapping_corpus_digest"],
                support_observation_ref={
                    "path": _repo_relative(selection_path),
                    "sha256": sha256_file(selection_path),
                    "mapping_corpus_digest": selection["mapping_corpus_digest"],
                },
                resume_cursor=None,
                recovered_unledgered_complete_artifact=recovered,
            )
        )
        ledger.fsync()
    return {
        "status": "EXACT_TEN_SELECTED",
        "config_hashes": selection["config_hashes"],
        "anchor_hashes": selection["anchor_hashes"],
        "event_digest": event["event_digest"],
    }


def _load_exact_ten(root: Path, ledger: RunLedger) -> dict[str, Any]:
    path = root / "exact-ten-selection.json"
    document = _object(path, label="exact-ten selection")
    body = dict(document)
    recorded = body.pop("mapping_corpus_digest", None)
    if recorded != canonical_sha256(body):
        raise RunnerError("exact-ten selection digest mismatch")
    if len(document.get("config_hashes", [])) != 10:
        raise RunnerError("exact-ten selection cardinality mismatch")
    events = [
        event
        for event in ledger.load()
        if event["stage"] == Stage.EXACT_TEN_SELECTED.value
    ]
    if (
        len(events) != 1
        or events[0].get("fixture_digest") != recorded
        or events[0].get("support_observation_ref", {}).get("sha256")
        != sha256_file(path)
    ):
        raise RunnerError("exact-ten selection differs from ledger")
    return document


@_serialized_formal
def run_formal_mapping(
    *,
    run_root: Path | str | None = None,
    lock_path: Path | str = LOCK_PATH,
    output_path: Path | str = MAPPING_PATH,
) -> dict[str, Any]:
    """Execute two fresh score-blind mapping passes and classify parity."""

    contract, lock_digest = require_effective_lock(lock_path)
    root = _formal_root(contract, run_root)
    ledger = RunLedger(root / "ledger")
    events = ledger.load()
    if not events:
        raise RunnerError("formal mapping requires exact-ten selection")
    contract_digest = canonical_sha256(contract)
    last_stage = Stage(events[-1]["stage"])
    if last_stage == Stage.MAPPING_AB:
        issue_path = root / "mapping" / "changes-required.json"
        if issue_path.is_file():
            issue = _object(issue_path, label="unledgered mapping issue")
            issue_body = dict(issue)
            recorded_issue = issue_body.pop("issue_digest", None)
            if (
                recorded_issue != canonical_sha256(issue_body)
                or issue.get("classification") != "CHANGES_REQUIRED"
                or issue.get("scientific_outcome") != "not_evaluated"
            ):
                raise RunnerError("unledgered mapping issue cannot be adopted")
            with ledger.acquire_writer():
                recovered_event = ledger.append(
                    _event_payload(
                        stage=Stage.CHANGES_REQUIRED,
                        contract_digest=contract_digest,
                        lock_digest=lock_digest,
                        counter=_latest_counter(ledger, contract),
                        fixture_digest=recorded_issue,
                        support_observation_ref={
                            "path": _repo_relative(issue_path),
                            "sha256": sha256_file(issue_path),
                        },
                        resume_cursor=None,
                        recovered_unledgered_complete_artifact=True,
                    )
                )
                ledger.fsync()
            return {
                "status": "CHANGES_REQUIRED",
                "scientific_outcome": "not_evaluated",
                "issue_event_digest": recovered_event["event_digest"],
                "recovered_unledgered_complete_artifact": True,
            }
        if MAPPING_PATH.is_file():
            mapping_document = _object(MAPPING_PATH, label="mapping corpus")
            mapping_body = dict(mapping_document)
            mapping_digest = mapping_body.pop("mapping_manifest_digest", None)
            if (
                mapping_digest != canonical_sha256(mapping_body)
                or mapping_document.get("contract_digest") != contract_digest
                or mapping_document.get("lock_digest") != lock_digest
                or mapping_document.get("status") != "FT-BLOCKED-MAPPING"
            ):
                raise RunnerError("completed mapping stage is not resumable here")
            decision = _decision_document(
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                classification="negative",
                criterion="S1_ENTRY_BLOCKED",
                failure_id="FT-BLOCKED-MAPPING",
                evidence={
                    "mapping_manifest_digest": mapping_digest,
                    "rejected_row_count": mapping_document[
                        "rejected_row_count"
                    ],
                    "fresh_ab_reproduced": True,
                },
                activation_state="pending_fresh_verification_and_closeout",
            )
            current_before = _latest_counter(ledger, contract)
            decision_recovered_before = DECISION_PATH.is_file()
            if not decision_recovered_before:
                with ledger.acquire_writer():
                    blocked = _resource_block_if_needed(
                        ledger=ledger,
                        root=root,
                        contract_digest=contract_digest,
                        lock_digest=lock_digest,
                        caps=_frozen_caps(contract),
                        current=current_before,
                        reservation=_reservation(contract, "decision"),
                        next_atomic_unit={
                            "kind": "decision",
                            "classification": "negative_mapping",
                        },
                    )
                if blocked is not None:
                    return blocked
            recovered_decision = _write_or_match_json(DECISION_PATH, decision)
            os.chmod(DECISION_PATH, 0o644)
            current = _absolute_storage_counter(current_before, contract)
            with ledger.acquire_writer():
                blocked = _resource_block_if_needed(
                    ledger=ledger,
                    root=root,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    caps=_frozen_caps(contract),
                    current=current_before,
                    reservation=_reservation(contract, "decision"),
                    actual_counter=current,
                    next_atomic_unit={
                        "kind": "decision",
                        "classification": "negative_mapping",
                    },
                    completed_artifact_ref={
                        "path": _repo_relative(DECISION_PATH),
                        "sha256": sha256_file(DECISION_PATH),
                        "decision_digest": decision["decision_digest"],
                    },
                    recovered_unledgered_complete_artifact=(
                        recovered_decision or decision_recovered_before
                    ),
                )
                if blocked is not None:
                    return blocked
                terminal_event = ledger.append(
                    _event_payload(
                        stage=Stage.TERMINAL_NEGATIVE,
                        contract_digest=contract_digest,
                        lock_digest=lock_digest,
                        counter=current,
                        fixture_digest=decision["decision_digest"],
                        support_observation_ref={
                            "path": _repo_relative(DECISION_PATH),
                            "sha256": sha256_file(DECISION_PATH),
                        },
                        resume_cursor=None,
                        recovered_unledgered_complete_artifact=True,
                    )
                )
                ledger.fsync()
            return {
                "status": "TERMINAL_NEGATIVE_PENDING_VERIFICATION",
                "failure_id": "FT-BLOCKED-MAPPING",
                "terminal_event_digest": terminal_event["event_digest"],
                "recovered_unledgered_complete_artifact": True,
            }
        raise RunnerError("mapping stage is complete and has no resumable terminal")
    if last_stage != Stage.EXACT_TEN_SELECTED:
        raise RunnerError("formal mapping requires exact-ten selection")
    selection = _load_exact_ten(root, ledger)
    size_document, sizes = _load_size_registry()
    candidates = [
        {
            "slot": slot,
            "config_hash": witness["config_hash"],
            "config": witness["config"],
            "candidate_indices": witness["candidate_indices"],
        }
        for slot, witness in enumerate(selection["witnesses"])
    ]
    if [row["config_hash"] for row in candidates] != selection["config_hashes"]:
        raise RunnerError("exact-ten witness/hash order mismatch")
    current = _latest_counter(ledger, contract)
    raw_path = root / "mapping" / "mapping-ab-raw.json"
    recovered_raw = raw_path.is_file()
    if recovered_raw:
        raw = _object(raw_path, label="unledgered mapping A/B raw record")
        raw_body = dict(raw)
        recorded_raw = raw_body.pop("raw_mapping_digest", None)
        if (
            recorded_raw != canonical_sha256(raw_body)
            or raw.get("contract_digest") != contract_digest
            or raw.get("lock_digest") != lock_digest
            or raw.get("selection_digest") != selection["mapping_corpus_digest"]
        ):
            raise RunnerError("unledgered mapping A/B record cannot be adopted")
        rows_a = raw["pass_a"]
        rows_b = raw["pass_b"]
        measurement_a = raw["measurement_a"]
        measurement_b = raw["measurement_b"]
    else:
        with ledger.acquire_writer():
            blocked = _resource_block_if_needed(
                ledger=ledger,
                root=root,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                caps=_frozen_caps(contract),
                current=current,
                reservation=_reservation(contract, "mapping_ab"),
                next_atomic_unit={"kind": "mapping_ab", "passes": ["A", "B"]},
            )
        if blocked is not None:
            return blocked
        rows_a, measurement_a = run_pinned_mapping_batch(
            integration_root=_integration_root(contract),
            candidates=candidates,
            sizes=sizes,
            scratch_root=root / "mapping" / "pass-a",
            retain_rows=True,
        )
        rows_b, measurement_b = run_pinned_mapping_batch(
            integration_root=_integration_root(contract),
            candidates=candidates,
            sizes=sizes,
            scratch_root=root / "mapping" / "pass-b",
            retain_rows=True,
        )
        raw = {
            "schema_version": 1,
            "checkpoint_id": "S10R2",
            "contract_digest": contract_digest,
            "lock_digest": lock_digest,
            "selection_digest": selection["mapping_corpus_digest"],
            "pass_a": rows_a,
            "pass_b": rows_b,
            "measurement_a": measurement_a,
            "measurement_b": measurement_b,
        }
        raw["raw_mapping_digest"] = canonical_sha256(raw)
        atomic_write_json(raw_path, raw, exclusive=True)
    current = _absolute_storage_counter(
        current,
        contract,
        wall_delta=float(measurement_a["wall_s"]) + float(measurement_b["wall_s"]),
        cpu_delta=float(measurement_a["cpu_s"]) + float(measurement_b["cpu_s"]),
    )
    raw_reference = {
        "path": _repo_relative(raw_path),
        "sha256": sha256_file(raw_path),
        "raw_mapping_digest": raw["raw_mapping_digest"],
    }
    with ledger.acquire_writer():
        blocked = _resource_block_if_needed(
            ledger=ledger,
            root=root,
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            caps=_frozen_caps(contract),
            current=_latest_counter(ledger, contract),
            reservation=_reservation(contract, "mapping_ab"),
            actual_counter=current,
            next_atomic_unit={"kind": "mapping_ab", "passes": ["A", "B"]},
            completed_artifact_ref=raw_reference,
            recovered_unledgered_complete_artifact=recovered_raw,
        )
    if blocked is not None:
        return blocked
    if canonical_sha256(rows_a) != canonical_sha256(rows_b):
        issue = {
            "schema_version": 1,
            "checkpoint_id": "S10R2",
            "classification": "CHANGES_REQUIRED",
            "scientific_outcome": "not_evaluated",
            "reason": "fresh A/B mapping rows differ",
            "raw_mapping_digest": raw["raw_mapping_digest"],
        }
        issue["issue_digest"] = canonical_sha256(issue)
        issue_path = root / "mapping" / "changes-required.json"
        recovered_issue = _write_or_match_json(issue_path, issue)
        with ledger.acquire_writer():
            mapping_event = ledger.append(
                _event_payload(
                    stage=Stage.MAPPING_AB,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=current,
                    fixture_digest=raw["raw_mapping_digest"],
                    support_observation_ref=raw_reference,
                    resume_cursor=None,
                    recovered_unledgered_complete_artifact=recovered_raw,
                )
            )
            issue_event = ledger.append(
                _event_payload(
                    stage=Stage.CHANGES_REQUIRED,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=current,
                    fixture_digest=issue["issue_digest"],
                    support_observation_ref={
                        "path": _repo_relative(issue_path),
                        "sha256": sha256_file(issue_path),
                    },
                    resume_cursor=None,
                    recovered_unledgered_complete_artifact=recovered_issue,
                )
            )
            ledger.fsync()
        return {
            "status": "CHANGES_REQUIRED",
            "scientific_outcome": "not_evaluated",
            "mapping_event_digest": mapping_event["event_digest"],
            "issue_event_digest": issue_event["event_digest"],
        }
    rejected = [
        row
        for row in rows_a
        if row.get("mapping_status") != "accepted"
        or row.get("guessed_required_fields")
        or row.get("unresolved_required_fields")
    ]
    parity = None
    if not rejected:
        parity = verify_ab_parity(
            rows_a,
            rows_b,
            expected_config_hashes=selection["config_hashes"],
            expected_size_ids=[row["size_id"] for row in sizes],
        )
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "contract_digest": contract_digest,
        "lock_digest": lock_digest,
        "selection": selection,
        "size_registry_digest": size_document["size_registry_digest"],
        "pass_a": rows_a,
        "pass_b": rows_b,
        "ab_byte_semantic_parity": True,
        "parity": parity,
        "rejected_row_count": len(rejected),
        "guessed_required_field_count": sum(
            len(row.get("guessed_required_fields", [])) for row in rows_a
        ),
        "unresolved_required_field_count": sum(
            len(row.get("unresolved_required_fields", [])) for row in rows_a
        ),
        "replacement_count": 0,
        "status": "PASS" if not rejected else "FT-BLOCKED-MAPPING",
        "raw_mapping_digest": raw["raw_mapping_digest"],
    }
    document = {**body, "mapping_manifest_digest": canonical_sha256(body)}
    recovered_manifest = _write_or_match_json(output_path, document)
    os.chmod(output_path, 0o644)
    decision = None
    decision_recovered_before = False
    if rejected:
        decision = _decision_document(
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            classification="negative",
            criterion="S1_ENTRY_BLOCKED",
            failure_id="FT-BLOCKED-MAPPING",
            evidence={
                "mapping_manifest_digest": document[
                    "mapping_manifest_digest"
                ],
                "rejected_row_count": len(rejected),
                "fresh_ab_reproduced": True,
            },
            activation_state="pending_fresh_verification_and_closeout",
        )
        decision_recovered_before = DECISION_PATH.is_file()
        if not decision_recovered_before:
            with ledger.acquire_writer():
                blocked = _resource_block_if_needed(
                    ledger=ledger,
                    root=root,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    caps=_frozen_caps(contract),
                    current=current,
                    reservation=_reservation(contract, "decision"),
                    next_atomic_unit={
                        "kind": "decision",
                        "classification": "negative_mapping",
                    },
                    completed_artifact_ref={
                        "path": _repo_relative(output_path),
                        "sha256": sha256_file(output_path),
                        "mapping_manifest_digest": document[
                            "mapping_manifest_digest"
                        ],
                    },
                    recovered_unledgered_complete_artifact=(
                        recovered_raw or recovered_manifest
                    ),
                )
            if blocked is not None:
                return blocked
    with ledger.acquire_writer():
        mapping_event = ledger.append(
            _event_payload(
                stage=Stage.MAPPING_AB,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                counter=current,
                fixture_digest=document["mapping_manifest_digest"],
                support_observation_ref={
                    "path": _repo_relative(output_path),
                    "sha256": sha256_file(output_path),
                    "mapping_manifest_digest": document[
                        "mapping_manifest_digest"
                    ],
                },
                resume_cursor=None,
                recovered_unledgered_complete_artifact=(
                    recovered_raw or recovered_manifest
                ),
            )
        )
        if rejected:
            if decision is None:
                raise RunnerError("mapping rejection lacks deterministic decision")
            recovered_decision = _write_or_match_json(DECISION_PATH, decision)
            os.chmod(DECISION_PATH, 0o644)
            decision_counter = _absolute_storage_counter(current, contract)
            blocked = _resource_block_if_needed(
                ledger=ledger,
                root=root,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                caps=_frozen_caps(contract),
                current=current,
                reservation=_reservation(contract, "decision"),
                actual_counter=decision_counter,
                next_atomic_unit={
                    "kind": "decision",
                    "classification": "negative_mapping",
                },
                completed_artifact_ref={
                    "path": _repo_relative(DECISION_PATH),
                    "sha256": sha256_file(DECISION_PATH),
                    "decision_digest": decision["decision_digest"],
                },
                recovered_unledgered_complete_artifact=(
                    recovered_decision or decision_recovered_before
                ),
            )
            if blocked is not None:
                return blocked
            terminal_event = ledger.append(
                _event_payload(
                    stage=Stage.TERMINAL_NEGATIVE,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=decision_counter,
                    fixture_digest=decision["decision_digest"],
                    support_observation_ref={
                        "path": _repo_relative(DECISION_PATH),
                        "sha256": sha256_file(DECISION_PATH),
                    },
                    resume_cursor=None,
                    recovered_unledgered_complete_artifact=recovered_decision,
                )
            )
        else:
            terminal_event = None
        ledger.fsync()
    return {
        "status": (
            "TERMINAL_NEGATIVE_PENDING_VERIFICATION"
            if rejected
            else "MAPPING_AB_PASS"
        ),
        "failure_id": "FT-BLOCKED-MAPPING" if rejected else None,
        "mapping_event_digest": mapping_event["event_digest"],
        "terminal_event_digest": (
            None if terminal_event is None else terminal_event["event_digest"]
        ),
    }


def _native_build_record_from_lock(lock: Mapping[str, Any]) -> tuple[Path, dict[str, Any]]:
    binding = lock["artifact_bindings"]["native_build_manifest"]
    path = _resolve_repo_path(binding["path"])
    return path, _object(path, label="locked native build manifest")


@_serialized_formal
def run_formal_native_conformance(
    *,
    run_root: Path | str | None = None,
    lock_path: Path | str = LOCK_PATH,
    output_path: Path | str = SENTINEL_PATH,
) -> dict[str, Any]:
    """Run the locked native helper plus all preregistered substitution faults."""

    contract, lock_digest = require_effective_lock(lock_path)
    lock = _object(lock_path, label="effective lock")
    root = _formal_root(contract, run_root)
    ledger = RunLedger(root / "ledger")
    events = ledger.load()
    if not events or Stage(events[-1]["stage"]) != Stage.MAPPING_AB:
        raise RunnerError("native conformance requires successful mapping A/B")
    mapping_document = _object(MAPPING_PATH, label="mapping corpus")
    if mapping_document.get("status") != "PASS":
        raise RunnerError("native conformance requires passing mapping corpus")
    contract_digest = canonical_sha256(contract)
    current = _latest_counter(ledger, contract)
    output_root = root / "native-conformance"
    recovered = Path(output_path).is_file()
    if recovered:
        document = _object(output_path, label="unledgered sentinel conformance")
        document_body = dict(document)
        recorded = document_body.pop("sentinel_conformance_digest", None)
        if (
            recorded != canonical_sha256(document_body)
            or document.get("contract_digest") != contract_digest
            or document.get("lock_digest") != lock_digest
            or document.get("status") != "PASS"
        ):
            raise RunnerError("unledgered sentinel conformance cannot be adopted")
        measurement = document.get("measurement")
        if not isinstance(measurement, Mapping):
            raise RunnerError("unledgered sentinel conformance lacks measurement")
        current = _absolute_storage_counter(
            current,
            contract,
            wall_delta=float(measurement["wall_s"]),
            cpu_delta=float(measurement["cpu_s"]),
        )
        with ledger.acquire_writer():
            blocked = _resource_block_if_needed(
                ledger=ledger,
                root=root,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                caps=_frozen_caps(contract),
                current=_latest_counter(ledger, contract),
                reservation=_reservation(contract, "native_conformance"),
                actual_counter=current,
                next_atomic_unit={"kind": "native_conformance"},
                completed_artifact_ref={
                    "path": _repo_relative(output_path),
                    "sha256": sha256_file(output_path),
                    "sentinel_conformance_digest": document[
                        "sentinel_conformance_digest"
                    ],
                },
                recovered_unledgered_complete_artifact=True,
            )
            if blocked is not None:
                return blocked
            event = ledger.append(
                _event_payload(
                    stage=Stage.NATIVE_CONFORMANCE,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=current,
                    fixture_digest=document["sentinel_conformance_digest"],
                    support_observation_ref={
                        "path": _repo_relative(output_path),
                        "sha256": sha256_file(output_path),
                        "sentinel_conformance_digest": document[
                            "sentinel_conformance_digest"
                        ],
                    },
                    measurement=measurement,
                    recovered_unledgered_complete_artifact=True,
                    resume_cursor=None,
                )
            )
            ledger.fsync()
        return {
            "status": "NATIVE_CONFORMANCE_PASS",
            "event_digest": event["event_digest"],
            "fault_classes": sorted(
                document["substitution_fault_tests"]["results"]
            ),
            "recovered_unledgered_complete_artifact": True,
        }
    with ledger.acquire_writer():
        blocked = _resource_block_if_needed(
            ledger=ledger,
            root=root,
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            caps=_frozen_caps(contract),
            current=current,
            reservation=_reservation(contract, "native_conformance"),
            next_atomic_unit={"kind": "native_conformance"},
        )
    if blocked is not None:
        return blocked
    if output_root.exists() and any(output_root.iterdir()):
        raise RunnerError("formal native conformance root already exists")
    output_root.mkdir(parents=True, exist_ok=True)
    native = contract["native_conformance"]
    fixture = materialize_native_fixture(
        native["synthetic_fixture"], native["thresholds"]
    )
    input_path = output_root / "fixture.tsv"
    transcript_path = output_root / "transcript.json"
    atomic_write_bytes(input_path, fixture["input_bytes"], exclusive=True)
    _, build = _native_build_record_from_lock(lock)
    source_identities = build["source_identities"]
    binary = Path(str(build["binary_path"])).resolve()
    binding = NativeBinding(
        helper_path=str(binary),
        helper_sha256=str(build["binary_sha256"]),
        helper_source_sha256=str(build["source_sha256"]),
        host_adapter_sha256=str(build["host_adapter_sha256"]),
        formocast_source_blob=str(source_identities["formocast_source_blob"]),
        formocast_header_blob=str(source_identities["formocast_header_blob"]),
        solution_iterator_source_blob=str(
            source_identities["solution_iterator_source_blob"]
        ),
        solution_iterator_header_blob=str(
            source_identities["solution_iterator_header_blob"]
        ),
        symbol=str(native["helper_symbol"]),
    )
    expected_binding = {
        "helper_sha256": build["binary_sha256"],
        "helper_source_sha256": build["source_sha256"],
        "host_adapter_sha256": build["host_adapter_sha256"],
        **source_identities,
        "symbol": native["helper_symbol"],
    }
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    adapter = PinnedNativeFormocastRuntimeAdapter(binding)
    transcript = adapter.evaluate_cohort(
        input_path=input_path,
        output_path=transcript_path,
        expected_binding=expected_binding,
        helper_source_path=NATIVE_SOURCE,
        host_adapter_path=NATIVE_HOST_ADAPTER,
        cwd=output_root,
    )
    conformance = run_native_formocast_conformance(
        transcript,
        {
            "cohort": fixture["cohort"],
            "thresholds": fixture["thresholds"],
            "expected_queues": fixture["expected_queues"],
        },
    )
    valid_fault_binding = {
        "helper_path": _repo_relative(binary),
        "helper_sha256": build["binary_sha256"],
        "predicted_performance_source_blob": contract["source_identity"][
            "native_formocast"
        ]["source_blob"],
        "host_adapter_sha256": build["host_adapter_sha256"],
        "queue_adapter_source_blob": contract["source_identity"]["runtime_queue"][
            "source_blob"
        ],
    }

    def validate_fault_binding(candidate: Mapping[str, Any]) -> None:
        if candidate != valid_fault_binding:
            raise RunnerError("substituted native/runtime binding")
        if sha256_file(binary) != candidate["helper_sha256"]:
            raise RunnerError("native helper binary drift")
        if sha256_file(NATIVE_HOST_ADAPTER) != candidate["host_adapter_sha256"]:
            raise RunnerError("host adapter drift")

    mutations = {
        field: (
            "0" * 64
            if field != "helper_path"
            else "agent_run/invalid-s10r2-helper"
        )
        for field in valid_fault_binding
    }
    fault_tests = run_runtime_substitution_fault_tests(
        validate_fault_binding,
        valid_fault_binding,
        mutations=mutations,
    )
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    measurement = {
        "wall_s": time.monotonic() - started,
        "cpu_s": (
            after.ru_utime
            + after.ru_stime
            - before.ru_utime
            - before.ru_stime
        ),
        "gpu_s": 0.0,
    }
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "contract_digest": contract_digest,
        "lock_digest": lock_digest,
        "mapping_manifest_digest": mapping_document["mapping_manifest_digest"],
        "fixture_id": native["synthetic_fixture"]["fixture_id"],
        "fixture_digest": fixture["fixture_digest"],
        "fixture_input_sha256": sha256_file(input_path),
        "transcript": transcript,
        "transcript_sha256": sha256_file(transcript_path),
        "binding": valid_fault_binding,
        "native_conformance": conformance,
        "substitution_fault_tests": fault_tests,
        "score_blind": True,
        "status": "PASS",
        "measurement": measurement,
    }
    document = {**body, "sentinel_conformance_digest": canonical_sha256(body)}
    _write_or_match_json(output_path, document)
    os.chmod(output_path, 0o644)
    current = _absolute_storage_counter(
        current,
        contract,
        wall_delta=measurement["wall_s"],
        cpu_delta=measurement["cpu_s"],
    )
    with ledger.acquire_writer():
        blocked = _resource_block_if_needed(
            ledger=ledger,
            root=root,
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            caps=_frozen_caps(contract),
            current=_latest_counter(ledger, contract),
            reservation=_reservation(contract, "native_conformance"),
            actual_counter=current,
            next_atomic_unit={"kind": "native_conformance"},
            completed_artifact_ref={
                "path": _repo_relative(output_path),
                "sha256": sha256_file(output_path),
                "sentinel_conformance_digest": document[
                    "sentinel_conformance_digest"
                ],
            },
            recovered_unledgered_complete_artifact=False,
        )
        if blocked is not None:
            return blocked
        event = ledger.append(
            _event_payload(
                stage=Stage.NATIVE_CONFORMANCE,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                counter=current,
                fixture_digest=document["sentinel_conformance_digest"],
                support_observation_ref={
                    "path": _repo_relative(output_path),
                    "sha256": sha256_file(output_path),
                    "sentinel_conformance_digest": document[
                        "sentinel_conformance_digest"
                    ],
                },
                measurement=measurement,
                recovered_unledgered_complete_artifact=False,
                resume_cursor=None,
            )
        )
        ledger.fsync()
    return {
        "status": "NATIVE_CONFORMANCE_PASS",
        "event_digest": event["event_digest"],
        "fault_classes": sorted(fault_tests["results"]),
    }


def _require_perlee_surface(contract: Mapping[str, Any]) -> None:
    formal = contract["formal_execution"]
    variable = str(formal["required_container_env"])
    if os.environ.get(variable) != formal["required_container_name"]:
        raise RunnerError(
            f"formal GPU command requires {variable}=perlee inside docker exec"
        )
    if not Path("/.dockerenv").exists():
        raise RunnerError("formal GPU command is not running in a container")
    if not str(ROOT.resolve()).startswith("/src/rocm-libraries"):
        raise RunnerError("formal GPU command does not use the perlee repository mount")


def _visible_physical_gpu_indices(
    allocation_snapshot: Mapping[str, Any],
) -> list[int]:
    devices = allocation_snapshot.get("devices")
    if not isinstance(devices, Mapping):
        raise RunnerError("ROCm-SMI allocation snapshot lacks devices")
    indices = sorted(
        int(name[4:])
        for name in devices
        if isinstance(name, str)
        and name.startswith("card")
        and name[4:].isdigit()
    )
    if not indices:
        raise RunnerError("ROCm-SMI allocation snapshot has no physical cards")
    return indices


def _parse_gpu_pid_output(
    stdout: str,
    *,
    visible_indices: Sequence[int],
) -> dict[str, list[int]]:
    """Parse one self-consistent ROCm-SMI PID-to-DRM-device snapshot."""

    visible = set(visible_indices)
    if len(visible) != len(visible_indices):
        raise RunnerError("visible physical GPU indices are ambiguous")
    physical_device_pids: dict[str, list[int]] = {
        str(index): [] for index in sorted(visible)
    }
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    substantive = [
        line for line in lines if not line.startswith("=")
    ]
    if substantive == ["No KFD PIDs currently running"]:
        return physical_device_pids
    if not substantive or "No KFD PIDs currently running" in substantive:
        raise RunnerError("ROCm-SMI PID output is incomplete or ambiguous")

    pid_pattern = re.compile(
        r"^PID ([1-9][0-9]*) is using ([1-9][0-9]*) DRM device\(s\):$"
    )
    device_pattern = re.compile(r"^[0-9]+(?:\s+[0-9]+)*$")
    seen_pids: set[int] = set()
    cursor = 0
    while cursor < len(substantive):
        match = pid_pattern.fullmatch(substantive[cursor])
        if match is None or cursor + 1 >= len(substantive):
            raise RunnerError("ROCm-SMI PID output contains an unparsed record")
        pid = int(match.group(1))
        expected_count = int(match.group(2))
        device_line = substantive[cursor + 1]
        if device_pattern.fullmatch(device_line) is None:
            raise RunnerError("ROCm-SMI PID output has malformed device indices")
        device_indices = [int(value) for value in device_line.split()]
        if (
            pid in seen_pids
            or len(device_indices) != expected_count
            or len(set(device_indices)) != len(device_indices)
            or any(index not in visible for index in device_indices)
        ):
            raise RunnerError("ROCm-SMI PID/device mapping is ambiguous")
        seen_pids.add(pid)
        for index in device_indices:
            physical_device_pids[str(index)].append(pid)
        cursor += 2
    for pids in physical_device_pids.values():
        pids.sort()
    return physical_device_pids


def _gpu_process_snapshot(
    allocation_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    command = ["/opt/rocm/bin/rocm-smi", "--showpidgpus"]
    completed = subprocess.run(
        command,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            "PATH": "/opt/rocm/bin:/usr/bin:/bin",
            "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
            "LC_ALL": "C",
        },
        timeout=60,
    )
    if completed.returncode:
        raise RunnerError("ROCm-SMI process snapshot failed")
    if completed.stderr.strip():
        raise RunnerError("ROCm-SMI process snapshot emitted diagnostics")
    stdout = completed.stdout.decode("utf-8", "replace")
    visible_indices = _visible_physical_gpu_indices(allocation_snapshot)
    physical_device_pids = _parse_gpu_pid_output(
        stdout,
        visible_indices=visible_indices,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        "stdout": stdout,
        "visible_physical_device_indices": visible_indices,
        "physical_device_pids": physical_device_pids,
        "observed_pid_count": len(
            {
                pid
                for pids in physical_device_pids.values()
                for pid in pids
            }
        ),
        "parser_status": "PASS",
    }


def _assert_selected_card_pid_free(
    physical_index: int,
    process_snapshot: Mapping[str, Any],
) -> None:
    mapping = process_snapshot.get("physical_device_pids")
    if not isinstance(mapping, Mapping):
        raise RunnerError("ROCm-SMI PID snapshot lacks parsed device map")
    selected_pids = mapping.get(str(physical_index))
    if not isinstance(selected_pids, list):
        raise RunnerError(
            "ROCm-SMI PID snapshot lacks selected-device coverage"
        )
    if selected_pids:
        raise RunnerError(
            f"selected physical GPU has foreign PID(s): {selected_pids}"
        )


@_serialized_formal
def record_formal_gpu_environment(
    *,
    run_root: Path | str | None = None,
    lock_path: Path | str = LOCK_PATH,
) -> dict[str, Any]:
    """Select and freeze the lowest currently idle eligible device."""

    contract, lock_digest = require_effective_lock(lock_path)
    _require_perlee_surface(contract)
    root = _formal_root(contract, run_root)
    ledger = RunLedger(root / "ledger")
    events = ledger.load()
    if not events or Stage(events[-1]["stage"]) != Stage.NATIVE_CONFORMANCE:
        raise RunnerError("GPU environment requires native conformance PASS")
    current = _latest_counter(ledger, contract)
    path = root / "gpu-environment.json"
    attempt_path = root / "gpu-environment-attempt.json"
    if path.is_file():
        document = _load_gpu_environment(root)
        if (
            document.get("contract_digest") != canonical_sha256(contract)
            or document.get("lock_digest") != lock_digest
            or document.get("status") != "PASS"
        ):
            raise RunnerError("unledgered GPU environment cannot be adopted")
        measurement = document["measurement"]
        current = _absolute_storage_counter(
            current,
            contract,
            wall_delta=float(measurement["wall_s"]),
            cpu_delta=float(measurement["cpu_s"]),
        )
        with ledger.acquire_writer():
            blocked = _resource_block_if_needed(
                ledger=ledger,
                root=root,
                contract_digest=canonical_sha256(contract),
                lock_digest=lock_digest,
                caps=_frozen_caps(contract),
                current=_latest_counter(ledger, contract),
                reservation=_reservation(contract, "gpu_environment"),
                actual_counter=current,
                next_atomic_unit={"kind": "gpu_environment"},
                completed_artifact_ref={
                    "path": _repo_relative(path),
                    "sha256": sha256_file(path),
                    "gpu_environment_digest": document[
                        "gpu_environment_digest"
                    ],
                },
                recovered_unledgered_complete_artifact=True,
            )
            if blocked is not None:
                return blocked
            event = ledger.append(
                _event_payload(
                    stage=Stage.GPU_ENVIRONMENT,
                    contract_digest=canonical_sha256(contract),
                    lock_digest=lock_digest,
                    counter=current,
                    fixture_digest=document["gpu_environment_digest"],
                    support_observation_ref={
                        "path": _repo_relative(path),
                        "sha256": sha256_file(path),
                        "gpu_environment_digest": document[
                            "gpu_environment_digest"
                        ],
                    },
                    measurement=measurement,
                    recovered_unledgered_complete_artifact=True,
                    resume_cursor=None,
                )
            )
            ledger.fsync()
        return {
            "status": "GPU_ENVIRONMENT_PASS",
            "selected_device": document["selected_device"],
            "event_digest": event["event_digest"],
            "recovered_unledgered_complete_artifact": True,
        }
    if attempt_path.is_file():
        raise RunnerError(
            "incomplete GPU environment attempt cannot be resource-accounted"
        )
    with ledger.acquire_writer():
        blocked = _resource_block_if_needed(
            ledger=ledger,
            root=root,
            contract_digest=canonical_sha256(contract),
            lock_digest=lock_digest,
            caps=_frozen_caps(contract),
            current=current,
            reservation=_reservation(contract, "gpu_environment"),
            next_atomic_unit={"kind": "gpu_environment"},
        )
    if blocked is not None:
        return blocked
    atomic_write_json(
        attempt_path,
        {
            "schema_version": 1,
            "checkpoint_id": "S10R2",
            "contract_digest": canonical_sha256(contract),
            "lock_digest": lock_digest,
            "started_utc": _utc_now(),
            "status": "IN_PROGRESS",
        },
        exclusive=True,
    )
    started = time.monotonic()
    before_cpu = resource.getrusage(resource.RUSAGE_CHILDREN)
    snapshot = _gpu_snapshot()
    processes = _gpu_process_snapshot(snapshot)
    physical_index, device = _select_idle_gfx942(snapshot, processes)
    after_cpu = resource.getrusage(resource.RUSAGE_CHILDREN)
    measurement = {
        "wall_s": time.monotonic() - started,
        "cpu_s": (
            after_cpu.ru_utime
            + after_cpu.ru_stime
            - before_cpu.ru_utime
            - before_cpu.ru_stime
        ),
        "gpu_s": 0.0,
    }
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "contract_digest": canonical_sha256(contract),
        "lock_digest": lock_digest,
        "container_name": "perlee",
        "container_hostname": os.uname().nodename,
        "repository_mount": str(ROOT.resolve()),
        "selection_rule": contract["formal_execution"][
            "physical_device_selection"
        ],
        "availability_mode": "live_unreserved_user_authorized",
        "selected_device": {
            "physical_visible_index": physical_index,
            "logical_device_index": 0,
            "unique_id": device["Unique ID"],
            "serial_number": device["Serial Number"],
            "gfx_version": device["GFX Version"],
            "compute_partition": device["Compute Partition"],
            "memory_partition": device["Memory Partition"],
        },
        "allocation_snapshot": snapshot,
        "process_snapshot": processes,
        "clock_power_policy": "observed_only_no_mutation",
        "measurement": measurement,
        "status": "PASS",
    }
    document = {**body, "gpu_environment_digest": canonical_sha256(body)}
    atomic_write_json(path, document, exclusive=True)
    current = _absolute_storage_counter(
        current,
        contract,
        wall_delta=measurement["wall_s"],
        cpu_delta=measurement["cpu_s"],
    )
    with ledger.acquire_writer():
        blocked = _resource_block_if_needed(
            ledger=ledger,
            root=root,
            contract_digest=canonical_sha256(contract),
            lock_digest=lock_digest,
            caps=_frozen_caps(contract),
            current=_latest_counter(ledger, contract),
            reservation=_reservation(contract, "gpu_environment"),
            actual_counter=current,
            next_atomic_unit={"kind": "gpu_environment"},
            completed_artifact_ref={
                "path": _repo_relative(path),
                "sha256": sha256_file(path),
                "gpu_environment_digest": document[
                    "gpu_environment_digest"
                ],
            },
            recovered_unledgered_complete_artifact=False,
        )
        if blocked is not None:
            return blocked
        event = ledger.append(
            _event_payload(
                stage=Stage.GPU_ENVIRONMENT,
                contract_digest=canonical_sha256(contract),
                lock_digest=lock_digest,
                counter=current,
                fixture_digest=document["gpu_environment_digest"],
                support_observation_ref={
                    "path": _repo_relative(path),
                    "sha256": sha256_file(path),
                    "gpu_environment_digest": document[
                        "gpu_environment_digest"
                    ],
                },
                measurement=measurement,
                recovered_unledgered_complete_artifact=False,
                resume_cursor=None,
            )
        )
        ledger.fsync()
    return {
        "status": "GPU_ENVIRONMENT_PASS",
        "selected_device": document["selected_device"],
        "event_digest": event["event_digest"],
    }


def _load_gpu_environment(root: Path) -> dict[str, Any]:
    path = root / "gpu-environment.json"
    document = _object(path, label="GPU environment")
    body = dict(document)
    recorded = body.pop("gpu_environment_digest", None)
    if recorded != canonical_sha256(body):
        raise RunnerError("GPU environment digest mismatch")
    return document


def _assert_formal_device_idle(
    environment: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = _gpu_snapshot()
    selected = environment["selected_device"]
    index = int(selected["physical_visible_index"])
    name = f"card{index}"
    device = snapshot["devices"].get(name)
    if not isinstance(device, Mapping):
        raise RunnerError("selected physical GPU is no longer visible")
    expected = {
        "Unique ID": selected["unique_id"],
        "Serial Number": selected["serial_number"],
        "GFX Version": "gfx942",
        "Compute Partition": "SPX",
        "Memory Partition": "NPS1",
        "GPU use (%)": "0",
        "GPU Memory Allocated (VRAM%)": "0",
    }
    mismatches = {
        field: (device.get(field), value)
        for field, value in expected.items()
        if device.get(field) != value
    }
    if mismatches:
        raise RunnerError(f"selected formal GPU is not idle/identical: {mismatches}")
    processes = _gpu_process_snapshot(snapshot)
    _assert_selected_card_pid_free(index, processes)
    return {
        "allocation_snapshot": snapshot,
        "process_snapshot": processes,
        "selected_device_no_foreign_pid": True,
    }


def _client_from_lock(lock: Mapping[str, Any]) -> tuple[Path, dict[str, Any]]:
    binding = lock["artifact_bindings"]["client_build_record"]
    record_path = _resolve_repo_path(binding["path"])
    record = _object(record_path, label="locked client build record")
    client = Path(str(record["client_path"])).resolve()
    if (
        sha256_file(client) != record["client_sha256"]
        or sha256_file(client)
        != lock["artifact_bindings"]["client_binary"]["sha256"]
    ):
        raise RunnerError("locked client binary identity mismatch")
    return client, record


def _benchmark_csv_rows(
    output_root: Path,
    sizes: Sequence[Mapping[str, Any]],
) -> tuple[Path, list[dict[str, Any]]]:
    direct = output_root / "result.csv"
    candidates = [direct] if direct.is_file() else sorted(output_root.glob("**/Data/*.csv"))
    if len(candidates) != 1:
        raise RunnerError(f"expected one benchmark CSV, found {len(candidates)}")
    path = candidates[0]
    with path.open("r", encoding="utf-8", newline="") as stream:
        raw_rows = list(csv.DictReader(stream))
    expected = {
        tuple(int(value) for value in row["values"]): str(row["size_id"])
        for row in sizes
    }
    parsed: list[dict[str, Any]] = []
    seen: set[tuple[int, ...]] = set()
    for raw in raw_rows:
        try:
            size = tuple(int(raw[f"Size{letter}"]) for letter in "IJKL")
            timing = float(raw["WinnerTimeUS"])
            quality = float(raw["WinnerGFlops"])
        except (KeyError, TypeError, ValueError) as error:
            raise RunnerError("malformed benchmark CSV") from error
        if (
            size not in expected
            or size in seen
            or not math.isfinite(timing)
            or not math.isfinite(quality)
            or timing <= 0
            or quality <= 0
        ):
            raise RunnerError("benchmark CSV size/timing/quality mismatch")
        seen.add(size)
        parsed.append(
            {
                "size_id": expected[size],
                "size": list(size),
                "timing_us": timing,
                "quality": quality,
            }
        )
    if seen != set(expected) or len(parsed) != len(expected):
        raise RunnerError("benchmark CSV does not cover exact three-size panel")
    parsed.sort(key=lambda row: ["small", "medium", "large"].index(row["size_id"]))
    return path, parsed


def _run_anchor_pipeline(
    *,
    contract: Mapping[str, Any],
    lock: Mapping[str, Any],
    root: Path,
    anchor_hash: str,
    raw_config: Mapping[str, Any],
    sizes: Sequence[Mapping[str, Any]],
    environment: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    anchor_root = root / "correctness" / f"anchor-{anchor_hash}"
    if anchor_root.exists() and any(anchor_root.iterdir()):
        raise RunnerError(f"correctness anchor scratch already exists: {anchor_hash}")
    anchor_root.mkdir(parents=True, exist_ok=True)
    preflight = _assert_formal_device_idle(environment)
    config_path = anchor_root / "singleton.yaml"
    output_root = anchor_root / "output"
    atomic_write_bytes(
        config_path,
        _singleton_yaml_bytes(
            candidate=raw_config,
            sizes=[row["values"] for row in sizes],
            device_index=0,
        ),
        exclusive=True,
    )
    os.chmod(config_path, 0o644)
    client, client_record = _client_from_lock(lock)
    command = [
        sys.executable,
        str(
            _integration_root(contract)
            / "projects/hipblaslt/tensilelite/Tensile/bin/Tensile"
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
        "--prebuilt-client",
        str(client),
    ]
    run_environment = {
        "PYTHONPATH": str(
            _integration_root(contract) / "projects/hipblaslt/tensilelite"
        ),
        "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
        "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
        "LC_ALL": "C",
        "ROCR_VISIBLE_DEVICES": str(
            environment["selected_device"]["physical_visible_index"]
        ),
    }
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    completed = subprocess.run(
        command,
        cwd=anchor_root,
        env=run_environment,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=7200,
    )
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    wall_s = time.monotonic() - started
    stdout_path = anchor_root / "stdout.log"
    stderr_path = anchor_root / "stderr.log"
    atomic_write_bytes(stdout_path, completed.stdout, exclusive=True)
    atomic_write_bytes(stderr_path, completed.stderr, exclusive=True)
    measurement = {
        "wall_s": wall_s,
        "cpu_s": (
            after.ru_utime
            + after.ru_stime
            - before.ru_utime
            - before.ru_stime
        ),
        "gpu_s": wall_s,
        "gpu_accounting": "elapsed_wall_upper_bound",
    }
    command_record = {
        "argv": command,
        "cwd": str(anchor_root),
        "environment": {
            "ROCR_VISIBLE_DEVICES": run_environment["ROCR_VISIBLE_DEVICES"],
            "logical_device_index": 0,
        },
        "returncode": completed.returncode,
        "stdout_sha256": sha256_file(stdout_path),
        "stderr_sha256": sha256_file(stderr_path),
    }
    if completed.returncode:
        body = {
            "schema_version": 1,
            "anchor_hash": anchor_hash,
            "status": "FAIL",
            "failure": "locked_generate_compile_smoke_or_correctness_pipeline",
            "command": command_record,
            "measurement": measurement,
            "preflight_snapshot": preflight,
            "rows": [],
        }
        return {**body, "anchor_record_digest": canonical_sha256(body)}, measurement
    result_path, parsed = _benchmark_csv_rows(output_root, sizes)
    code_objects = sorted(output_root.glob("**/*.co"))
    if not code_objects:
        raise RunnerError("successful correctness pipeline produced no code object")
    rows = [
        {
            "config_hash": anchor_hash,
            "size_id": row["size_id"],
            "size": row["size"],
            "generated": True,
            "compiled": True,
            "smoke_pass": True,
            "nonzero_validation": True,
            "validation_elements": 128,
            "timing_us": row["timing_us"],
            "quality": row["quality"],
            "result_sha256": sha256_file(result_path),
        }
        for row in parsed
    ]
    body = {
        "schema_version": 1,
        "anchor_hash": anchor_hash,
        "status": "PASS",
        "command": command_record,
        "measurement": measurement,
        "preflight_snapshot": preflight,
        "config_sha256": sha256_file(config_path),
        "client_build_digest": client_record["client_build_digest"],
        "client_sha256": sha256_file(client),
        "code_object_sha256": {
            _repo_relative(path): sha256_file(path) for path in code_objects
        },
        "result_path": _repo_relative(result_path),
        "result_sha256": sha256_file(result_path),
        "rows": rows,
    }
    return {**body, "anchor_record_digest": canonical_sha256(body)}, measurement


def _correctness_failure_documents(
    *,
    contract_digest: str,
    lock_digest: str,
    anchors: Sequence[str],
    completed_anchor_hashes: Sequence[str],
    failed_record: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    failure_body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "contract_digest": contract_digest,
        "lock_digest": lock_digest,
        "anchors": list(anchors),
        "completed_anchor_hashes": list(completed_anchor_hashes),
        "rows": [],
        "failure_anchor_record": dict(failed_record),
        "status": "FT-BLOCKED-CORRECTNESS",
        "fresh_reproduction_required": True,
    }
    failure = {
        **failure_body,
        "correctness_digest": canonical_sha256(failure_body),
    }
    decision = _decision_document(
        contract_digest=contract_digest,
        lock_digest=lock_digest,
        classification="negative",
        criterion="S1_ENTRY_BLOCKED",
        failure_id="FT-BLOCKED-CORRECTNESS",
        evidence={
            "correctness_digest": failure["correctness_digest"],
            "failed_anchor_hash": failed_record["anchor_hash"],
            "fresh_reproduction_required": True,
        },
        activation_state="pending_fresh_verification_and_closeout",
    )
    return failure, decision


@_serialized_formal
def run_formal_correctness(
    *,
    run_root: Path | str | None = None,
    lock_path: Path | str = LOCK_PATH,
    output_path: Path | str = CORRECTNESS_PATH,
) -> dict[str, Any]:
    """Run the frozen three-anchor by three-size correctness panel."""

    contract, lock_digest = require_effective_lock(lock_path)
    _require_perlee_surface(contract)
    lock = _object(lock_path, label="effective lock")
    root = _formal_root(contract, run_root)
    ledger = RunLedger(root / "ledger")
    events = ledger.load()
    if not events or Stage(events[-1]["stage"]) not in {
        Stage.GPU_ENVIRONMENT,
        Stage.CORRECTNESS_ANCHORS,
    }:
        raise RunnerError("correctness panel is not legal from current stage")
    mapping_document = _object(MAPPING_PATH, label="mapping corpus")
    if mapping_document.get("status") != "PASS":
        raise RunnerError("correctness requires passing mapping corpus")
    _, sizes = _load_size_registry()
    environment = _load_gpu_environment(root)
    anchors = mapping_document["selection"]["anchor_hashes"]
    witness_by_hash = {
        row["config_hash"]: row
        for row in mapping_document["selection"]["witnesses"]
    }
    completed_events = [
        event
        for event in ledger.load()
        if event["stage"] == Stage.CORRECTNESS_ANCHORS.value
    ]
    completed_hashes = [event["anchor_hash"] for event in completed_events]
    if completed_hashes != anchors[: len(completed_hashes)]:
        raise RunnerError("correctness anchor ledger order mismatch")
    contract_digest = canonical_sha256(contract)
    for index, completed_event in enumerate(completed_events):
        reference = completed_event.get("support_observation_ref")
        if not isinstance(reference, Mapping):
            raise RunnerError("correctness event lacks anchor record reference")
        record_path = _resolve_repo_path(str(reference["path"]))
        if sha256_file(record_path) != reference.get("sha256"):
            raise RunnerError("completed correctness anchor hash mismatch")
        completed_record = _object(
            record_path, label="completed correctness anchor"
        )
        completed_body = dict(completed_record)
        completed_digest = completed_body.pop("anchor_record_digest", None)
        if (
            completed_digest != canonical_sha256(completed_body)
            or completed_digest != reference.get("anchor_record_digest")
            or completed_record.get("anchor_hash")
            != completed_event.get("anchor_hash")
            or completed_record.get("contract_digest") != contract_digest
            or completed_record.get("lock_digest") != lock_digest
        ):
            raise RunnerError("completed correctness anchor binding mismatch")
        if completed_record.get("status") == "PASS":
            continue
        if index != len(completed_events) - 1:
            raise RunnerError("correctness advanced beyond a failed anchor")
        failure, decision = _correctness_failure_documents(
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            anchors=anchors,
            completed_anchor_hashes=completed_hashes,
            failed_record=completed_record,
        )
        current_before = _latest_counter(ledger, contract)
        artifacts_started = Path(output_path).is_file() or DECISION_PATH.is_file()
        if not artifacts_started:
            with ledger.acquire_writer():
                blocked = _resource_block_if_needed(
                    ledger=ledger,
                    root=root,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    caps=_frozen_caps(contract),
                    current=current_before,
                    reservation=_reservation(contract, "decision"),
                    next_atomic_unit={
                        "kind": "decision",
                        "classification": "negative_correctness",
                    },
                )
            if blocked is not None:
                return blocked
        recovered_failure = _write_or_match_json(output_path, failure)
        recovered_decision = _write_or_match_json(DECISION_PATH, decision)
        os.chmod(output_path, 0o644)
        os.chmod(DECISION_PATH, 0o644)
        current = _absolute_storage_counter(current_before, contract)
        with ledger.acquire_writer():
            blocked = _resource_block_if_needed(
                ledger=ledger,
                root=root,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                caps=_frozen_caps(contract),
                current=current_before,
                reservation=_reservation(contract, "decision"),
                actual_counter=current,
                next_atomic_unit={
                    "kind": "decision",
                    "classification": "negative_correctness",
                },
                completed_artifact_ref={
                    "decision": {
                        "path": _repo_relative(DECISION_PATH),
                        "sha256": sha256_file(DECISION_PATH),
                        "decision_digest": decision["decision_digest"],
                    },
                    "correctness": {
                        "path": _repo_relative(output_path),
                        "sha256": sha256_file(output_path),
                        "correctness_digest": failure[
                            "correctness_digest"
                        ],
                    },
                },
                recovered_unledgered_complete_artifact=(
                    recovered_failure
                    or recovered_decision
                    or artifacts_started
                ),
            )
            if blocked is not None:
                return blocked
            terminal = ledger.append(
                _event_payload(
                    stage=Stage.TERMINAL_NEGATIVE,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=current,
                    fixture_digest=decision["decision_digest"],
                    support_observation_ref={
                        "path": _repo_relative(DECISION_PATH),
                        "sha256": sha256_file(DECISION_PATH),
                    },
                    resume_cursor=None,
                    recovered_unledgered_complete_artifact=True,
                )
            )
            ledger.fsync()
        return {
            "status": "TERMINAL_NEGATIVE_PENDING_FRESH_REPRODUCTION",
            "failure_id": "FT-BLOCKED-CORRECTNESS",
            "event_digest": terminal["event_digest"],
            "recovered_unledgered_complete_artifact": True,
        }
    for anchor_hash in anchors[len(completed_hashes) :]:
        current = _latest_counter(ledger, contract)
        record_path = (
            root / "correctness" / f"anchor-{anchor_hash}" / "anchor-record.json"
        )
        recovered = record_path.is_file()
        if recovered:
            record = _object(record_path, label="unledgered correctness anchor")
            body = dict(record)
            recorded = body.pop("anchor_record_digest", None)
            if (
                recorded != canonical_sha256(body)
                or record.get("contract_digest") != contract_digest
                or record.get("lock_digest") != lock_digest
                or record.get("anchor_hash") != anchor_hash
            ):
                raise RunnerError("unledgered correctness anchor cannot be adopted")
            measurement = record.get("measurement")
            if not isinstance(measurement, Mapping):
                raise RunnerError("unledgered correctness anchor lacks measurement")
        else:
            with ledger.acquire_writer():
                blocked = _resource_block_if_needed(
                    ledger=ledger,
                    root=root,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    caps=_frozen_caps(contract),
                    current=current,
                    reservation=_reservation(contract, "correctness_anchor"),
                    next_atomic_unit={
                        "kind": "correctness_anchor",
                        "anchor_hash": anchor_hash,
                    },
                )
            if blocked is not None:
                return blocked
            record, measurement = _run_anchor_pipeline(
                contract=contract,
                lock=lock,
                root=root,
                anchor_hash=anchor_hash,
                raw_config=witness_by_hash[anchor_hash]["config"],
                sizes=sizes,
                environment=environment,
            )
            record["contract_digest"] = contract_digest
            record["lock_digest"] = lock_digest
            body = dict(record)
            body.pop("anchor_record_digest", None)
            record["anchor_record_digest"] = canonical_sha256(body)
            atomic_write_json(record_path, record, exclusive=True)
        current = _absolute_storage_counter(
            current,
            contract,
            wall_delta=measurement["wall_s"],
            cpu_delta=measurement["cpu_s"],
            gpu_delta=measurement["gpu_s"],
        )
        with ledger.acquire_writer():
            blocked = _resource_block_if_needed(
                ledger=ledger,
                root=root,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                caps=_frozen_caps(contract),
                current=_latest_counter(ledger, contract),
                reservation=_reservation(contract, "correctness_anchor"),
                actual_counter=current,
                next_atomic_unit={
                    "kind": "correctness_anchor",
                    "anchor_hash": anchor_hash,
                },
                completed_artifact_ref={
                    "path": _repo_relative(record_path),
                    "sha256": sha256_file(record_path),
                    "anchor_record_digest": record["anchor_record_digest"],
                },
                recovered_unledgered_complete_artifact=recovered,
            )
            if blocked is not None:
                return blocked
            event = ledger.append(
                _event_payload(
                    stage=Stage.CORRECTNESS_ANCHORS,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=current,
                    fixture_digest=record["anchor_record_digest"],
                    support_observation_ref={
                        "path": _repo_relative(record_path),
                        "sha256": sha256_file(record_path),
                        "anchor_record_digest": record["anchor_record_digest"],
                    },
                    anchor_hash=anchor_hash,
                    measurement=measurement,
                    recovered_unledgered_complete_artifact=recovered,
                    resume_cursor=None,
                )
            )
            if record["status"] != "PASS":
                failure, decision = _correctness_failure_documents(
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    anchors=anchors,
                    completed_anchor_hashes=completed_hashes + [anchor_hash],
                    failed_record=record,
                )
                artifacts_started = (
                    Path(output_path).is_file() or DECISION_PATH.is_file()
                )
                if not artifacts_started:
                    blocked = _resource_block_if_needed(
                        ledger=ledger,
                        root=root,
                        contract_digest=contract_digest,
                        lock_digest=lock_digest,
                        caps=_frozen_caps(contract),
                        current=current,
                        reservation=_reservation(contract, "decision"),
                        next_atomic_unit={
                            "kind": "decision",
                            "classification": "negative_correctness",
                        },
                    )
                    if blocked is not None:
                        return blocked
                recovered_failure = _write_or_match_json(output_path, failure)
                os.chmod(output_path, 0o644)
                recovered_decision = _write_or_match_json(
                    DECISION_PATH, decision
                )
                os.chmod(DECISION_PATH, 0o644)
                decision_counter = _absolute_storage_counter(current, contract)
                blocked = _resource_block_if_needed(
                    ledger=ledger,
                    root=root,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    caps=_frozen_caps(contract),
                    current=current,
                    reservation=_reservation(contract, "decision"),
                    actual_counter=decision_counter,
                    next_atomic_unit={
                        "kind": "decision",
                        "classification": "negative_correctness",
                    },
                    completed_artifact_ref={
                        "decision": {
                            "path": _repo_relative(DECISION_PATH),
                            "sha256": sha256_file(DECISION_PATH),
                            "decision_digest": decision["decision_digest"],
                        },
                        "correctness": {
                            "path": _repo_relative(output_path),
                            "sha256": sha256_file(output_path),
                            "correctness_digest": failure[
                                "correctness_digest"
                            ],
                        },
                    },
                    recovered_unledgered_complete_artifact=(
                        recovered_failure
                        or recovered_decision
                        or artifacts_started
                    ),
                )
                if blocked is not None:
                    return blocked
                terminal = ledger.append(
                    _event_payload(
                        stage=Stage.TERMINAL_NEGATIVE,
                        contract_digest=contract_digest,
                        lock_digest=lock_digest,
                        counter=decision_counter,
                        fixture_digest=decision["decision_digest"],
                        support_observation_ref={
                            "path": _repo_relative(DECISION_PATH),
                            "sha256": sha256_file(DECISION_PATH),
                        },
                        resume_cursor=None,
                    )
                )
                ledger.fsync()
                return {
                    "status": "TERMINAL_NEGATIVE_PENDING_FRESH_REPRODUCTION",
                    "failure_id": "FT-BLOCKED-CORRECTNESS",
                    "event_digest": terminal["event_digest"],
                }
            ledger.fsync()
        completed_hashes.append(anchor_hash)
    records = [
        _object(
            root / "correctness" / f"anchor-{anchor_hash}" / "anchor-record.json",
            label="correctness anchor record",
        )
        for anchor_hash in anchors
    ]
    rows = [row for record in records for row in record["rows"]]
    verified = verify_correctness_anchors(
        rows,
        anchors=anchors,
        size_ids=[row["size_id"] for row in sizes],
    )
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "contract_digest": contract_digest,
        "lock_digest": lock_digest,
        "mapping_manifest_digest": mapping_document["mapping_manifest_digest"],
        "gpu_environment_digest": environment["gpu_environment_digest"],
        "anchors": anchors,
        "sizes": sizes,
        "anchor_records": records,
        "verification": verified,
        "rows": rows,
        "status": "PASS",
    }
    document = {**body, "correctness_digest": canonical_sha256(body)}
    _write_or_match_json(output_path, document)
    os.chmod(output_path, 0o644)
    return {
        "status": "CORRECTNESS_PASS",
        "correctness_digest": document["correctness_digest"],
        "rows": 9,
    }


def _rewrite_client_results(
    source: Path,
    destination: Path,
    result_path: Path,
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
        raise RunnerError("client config must contain exactly one results-file entry")
    atomic_write_bytes(
        destination,
        ("\n".join(output) + "\n").encode("utf-8"),
        exclusive=True,
    )


def _run_noise_batch(
    *,
    contract: Mapping[str, Any],
    lock: Mapping[str, Any],
    root: Path,
    anchor_hash: str,
    repeat: int,
    order: int,
    sizes: Sequence[Mapping[str, Any]],
    environment: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    cell_root = root / "noise" / f"cell-{order:02d}"
    if cell_root.exists() and any(cell_root.iterdir()):
        raise RunnerError("noise cell scratch already exists")
    cell_root.mkdir(parents=True, exist_ok=True)
    preflight = _assert_formal_device_idle(environment)
    base_candidates = sorted(
        (
            root / "correctness" / f"anchor-{anchor_hash}" / "output"
        ).glob("**/*ClientParameters*.ini")
    )
    if len(base_candidates) != 1:
        raise RunnerError("correctness output lacks one reusable ClientParameters.ini")
    result_path = cell_root / "result.csv"
    config_path = cell_root / "ClientParameters.ini"
    _rewrite_client_results(base_candidates[0], config_path, result_path)
    client, client_record = _client_from_lock(lock)
    command = [str(client), "--config-file", str(config_path)]
    run_environment = {
        "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
        "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
        "LC_ALL": "C",
        "ROCR_VISIBLE_DEVICES": str(
            environment["selected_device"]["physical_visible_index"]
        ),
    }
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    completed = subprocess.run(
        command,
        cwd=cell_root,
        env=run_environment,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=3600,
    )
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    wall_s = time.monotonic() - started
    stdout_path = cell_root / "stdout.log"
    stderr_path = cell_root / "stderr.log"
    atomic_write_bytes(stdout_path, completed.stdout, exclusive=True)
    atomic_write_bytes(stderr_path, completed.stderr, exclusive=True)
    measurement = {
        "wall_s": wall_s,
        "cpu_s": (
            after.ru_utime
            + after.ru_stime
            - before.ru_utime
            - before.ru_stime
        ),
        "gpu_s": wall_s,
        "gpu_accounting": "elapsed_wall_upper_bound",
    }
    if completed.returncode:
        raise RunnerError(
            f"noise client failed: rc={completed.returncode}, "
            f"stderr_sha256={sha256_file(stderr_path)}"
        )
    result_file, parsed = _benchmark_csv_rows(cell_root, sizes)
    rows = [
        {
            "config_hash": anchor_hash,
            "size_id": row["size_id"],
            "size": row["size"],
            "repeat": repeat,
            "order": order,
            "quality": row["quality"],
            "timing_us": row["timing_us"],
            "correctness": "pass",
            "result_sha256": sha256_file(result_file),
        }
        for row in parsed
    ]
    body = {
        "schema_version": 1,
        "anchor_hash": anchor_hash,
        "repeat": repeat,
        "order": order,
        "rows": rows,
        "command": {
            "argv": command,
            "cwd": str(cell_root),
            "returncode": completed.returncode,
            "ROCR_VISIBLE_DEVICES": run_environment["ROCR_VISIBLE_DEVICES"],
            "stdout_sha256": sha256_file(stdout_path),
            "stderr_sha256": sha256_file(stderr_path),
        },
        "preflight_snapshot": preflight,
        "client_build_digest": client_record["client_build_digest"],
        "measurement": measurement,
        "status": "PASS",
    }
    return {**body, "noise_batch_digest": canonical_sha256(body)}, measurement


@_serialized_formal
def run_formal_noise(
    *,
    run_root: Path | str | None = None,
    lock_path: Path | str = LOCK_PATH,
    output_path: Path | str = NOISE_PATH,
) -> dict[str, Any]:
    """Run the fixed 3x3x7 noise panel after all correctness anchors pass."""

    contract, lock_digest = require_effective_lock(lock_path)
    _require_perlee_surface(contract)
    lock = _object(lock_path, label="effective lock")
    root = _formal_root(contract, run_root)
    ledger = RunLedger(root / "ledger")
    correctness = _object(CORRECTNESS_PATH, label="correctness evidence")
    if correctness.get("status") != "PASS":
        raise RunnerError("noise requires complete correctness PASS")
    events = ledger.load()
    if not events or Stage(events[-1]["stage"]) not in {
        Stage.CORRECTNESS_ANCHORS,
        Stage.NOISE_CELLS,
    }:
        raise RunnerError("noise panel is not legal from current stage")
    _, sizes = _load_size_registry()
    environment = _load_gpu_environment(root)
    anchors = correctness["anchors"]
    schedule = [
        (anchor, repeat)
        for anchor in anchors
        for repeat in range(7)
    ]
    completed_events = [
        event
        for event in events
        if event["stage"] == Stage.NOISE_CELLS.value
    ]
    completed_keys = [
        (event["anchor_hash"], event["repeat"]) for event in completed_events
    ]
    if completed_keys != schedule[: len(completed_keys)]:
        raise RunnerError("noise ledger order differs from frozen schedule")
    contract_digest = canonical_sha256(contract)
    for order, (anchor_hash, repeat) in enumerate(
        schedule[len(completed_keys) :],
        start=len(completed_keys),
    ):
        current = _latest_counter(ledger, contract)
        record_path = root / "noise" / f"cell-{order:02d}" / "noise-batch.json"
        recovered = record_path.is_file()
        if recovered:
            record = _object(record_path, label="unledgered noise batch")
            body = dict(record)
            recorded = body.pop("noise_batch_digest", None)
            if (
                recorded != canonical_sha256(body)
                or record.get("contract_digest") != contract_digest
                or record.get("lock_digest") != lock_digest
                or record.get("anchor_hash") != anchor_hash
                or record.get("repeat") != repeat
                or record.get("order") != order
            ):
                raise RunnerError("unledgered noise batch cannot be adopted")
            measurement = record.get("measurement")
            if not isinstance(measurement, Mapping):
                raise RunnerError("unledgered noise batch lacks measurement")
        else:
            with ledger.acquire_writer():
                blocked = _resource_block_if_needed(
                    ledger=ledger,
                    root=root,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    caps=_frozen_caps(contract),
                    current=current,
                    reservation=_reservation(
                        contract, "noise_anchor_repeat"
                    ),
                    next_atomic_unit={
                        "kind": "noise_anchor_repeat",
                        "anchor_hash": anchor_hash,
                        "repeat": repeat,
                        "order": order,
                    },
                )
            if blocked is not None:
                return blocked
            record, measurement = _run_noise_batch(
                contract=contract,
                lock=lock,
                root=root,
                anchor_hash=anchor_hash,
                repeat=repeat,
                order=order,
                sizes=sizes,
                environment=environment,
            )
            record["contract_digest"] = contract_digest
            record["lock_digest"] = lock_digest
            body = dict(record)
            body.pop("noise_batch_digest", None)
            record["noise_batch_digest"] = canonical_sha256(body)
            atomic_write_json(record_path, record, exclusive=True)
        current = _absolute_storage_counter(
            current,
            contract,
            wall_delta=measurement["wall_s"],
            cpu_delta=measurement["cpu_s"],
            gpu_delta=measurement["gpu_s"],
        )
        with ledger.acquire_writer():
            blocked = _resource_block_if_needed(
                ledger=ledger,
                root=root,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                caps=_frozen_caps(contract),
                current=_latest_counter(ledger, contract),
                reservation=_reservation(
                    contract, "noise_anchor_repeat"
                ),
                actual_counter=current,
                next_atomic_unit={
                    "kind": "noise_anchor_repeat",
                    "anchor_hash": anchor_hash,
                    "repeat": repeat,
                    "order": order,
                },
                completed_artifact_ref={
                    "path": _repo_relative(record_path),
                    "sha256": sha256_file(record_path),
                    "noise_batch_digest": record["noise_batch_digest"],
                },
                recovered_unledgered_complete_artifact=recovered,
            )
            if blocked is not None:
                return blocked
            ledger.append(
                _event_payload(
                    stage=Stage.NOISE_CELLS,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=current,
                    fixture_digest=record["noise_batch_digest"],
                    support_observation_ref={
                        "path": _repo_relative(record_path),
                        "sha256": sha256_file(record_path),
                        "noise_batch_digest": record["noise_batch_digest"],
                    },
                    anchor_hash=anchor_hash,
                    repeat=repeat,
                    measurement=measurement,
                    recovered_unledgered_complete_artifact=recovered,
                    resume_cursor=None,
                )
            )
            ledger.fsync()
    records = [
        _object(root / "noise" / f"cell-{order:02d}" / "noise-batch.json", label="noise batch")
        for order in range(21)
    ]
    rows = [row for record in records for row in record["rows"]]
    validation = validate_noise_cells(
        rows,
        anchors=anchors,
        size_ids=[row["size_id"] for row in sizes],
        cv_p95_threshold=float(contract["noise"]["cv_p95_threshold"]),
    )
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "contract_digest": contract_digest,
        "lock_digest": lock_digest,
        "correctness_digest": correctness["correctness_digest"],
        "anchors": anchors,
        "sizes": sizes,
        "schedule_order": "sorted_anchor_hash_then_repeat_0_to_6",
        "batch_records": records,
        "rows": rows,
        "validation": validation,
        "status": validation["status"],
    }
    document = {**body, "noise_evidence_digest": canonical_sha256(body)}
    _write_or_match_json(output_path, document)
    os.chmod(output_path, 0o644)
    if validation["status"] == "INCONCLUSIVE":
        decision = _decision_document(
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            classification="inconclusive",
            criterion=None,
            failure_id="FT-INCONCLUSIVE",
            evidence={
                "noise_evidence_digest": document["noise_evidence_digest"],
                "cv_p95": validation["cv_p95"],
                "cv_p95_threshold": validation["cv_p95_threshold"],
            },
            activation_state="pending_fresh_verification_and_closeout",
        )
        current_before = _latest_counter(ledger, contract)
        decision_recovered_before = DECISION_PATH.is_file()
        if not decision_recovered_before:
            with ledger.acquire_writer():
                blocked = _resource_block_if_needed(
                    ledger=ledger,
                    root=root,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    caps=_frozen_caps(contract),
                    current=current_before,
                    reservation=_reservation(contract, "decision"),
                    next_atomic_unit={
                        "kind": "decision",
                        "classification": "inconclusive_noise",
                    },
                )
            if blocked is not None:
                return blocked
        recovered_decision = _write_or_match_json(DECISION_PATH, decision)
        os.chmod(DECISION_PATH, 0o644)
        current = _absolute_storage_counter(current_before, contract)
        with ledger.acquire_writer():
            blocked = _resource_block_if_needed(
                ledger=ledger,
                root=root,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                caps=_frozen_caps(contract),
                current=current_before,
                reservation=_reservation(contract, "decision"),
                actual_counter=current,
                next_atomic_unit={
                    "kind": "decision",
                    "classification": "inconclusive_noise",
                },
                completed_artifact_ref={
                    "path": _repo_relative(DECISION_PATH),
                    "sha256": sha256_file(DECISION_PATH),
                    "decision_digest": decision["decision_digest"],
                },
                recovered_unledgered_complete_artifact=(
                    recovered_decision or decision_recovered_before
                ),
            )
            if blocked is not None:
                return blocked
            event = ledger.append(
                _event_payload(
                    stage=Stage.TERMINAL_INCONCLUSIVE,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=current,
                    fixture_digest=decision["decision_digest"],
                    support_observation_ref={
                        "path": _repo_relative(DECISION_PATH),
                        "sha256": sha256_file(DECISION_PATH),
                    },
                    resume_cursor=None,
                )
            )
            ledger.fsync()
        return {
            "status": "TERMINAL_INCONCLUSIVE_PENDING_VERIFICATION",
            "failure_id": "FT-INCONCLUSIVE",
            "cv_p95": validation["cv_p95"],
            "event_digest": event["event_digest"],
        }
    return {
        "status": "NOISE_PASS",
        "noise_evidence_digest": document["noise_evidence_digest"],
        "cv_p95": validation["cv_p95"],
        "delta_noise": validation["delta_noise"],
    }


@_serialized_formal
def materialize_formal_decision(
    *,
    run_root: Path | str | None = None,
    lock_path: Path | str = LOCK_PATH,
    output_path: Path | str = DECISION_PATH,
) -> dict[str, Any]:
    """Apply the positive branch only after every locked formal artifact passes."""

    contract, lock_digest = require_effective_lock(lock_path)
    root = _formal_root(contract, run_root)
    ledger = RunLedger(root / "ledger")
    events = ledger.load()
    if not events or Stage(events[-1]["stage"]) not in {
        Stage.NOISE_CELLS,
        Stage.DECISION_READY,
    }:
        raise RunnerError("positive decision requires completed noise cells")
    mapping_document = _object(MAPPING_PATH, label="mapping corpus")
    sentinel = _object(SENTINEL_PATH, label="sentinel conformance")
    correctness = _object(CORRECTNESS_PATH, label="correctness evidence")
    noise = _object(NOISE_PATH, label="noise evidence")
    statuses = {
        "mapping": mapping_document.get("status"),
        "sentinel": sentinel.get("status"),
        "correctness": correctness.get("status"),
        "noise": noise.get("status"),
    }
    if statuses != {
        "mapping": "PASS",
        "sentinel": "PASS",
        "correctness": "PASS",
        "noise": "PASS",
    }:
        raise RunnerError(f"positive decision prerequisites do not all pass: {statuses}")
    contract_digest = canonical_sha256(contract)
    current_before = _latest_counter(ledger, contract)
    recovered_path = Path(output_path).is_file()
    if not recovered_path:
        with ledger.acquire_writer():
            blocked = _resource_block_if_needed(
                ledger=ledger,
                root=root,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                caps=_frozen_caps(contract),
                current=current_before,
                reservation=_reservation(contract, "decision"),
                next_atomic_unit={"kind": "decision"},
            )
        if blocked is not None:
            return blocked
    decision = _decision_document(
        contract_digest=contract_digest,
        lock_digest=lock_digest,
        classification="positive",
        criterion="S1_ENTRY_GO",
        failure_id=None,
        evidence={
            "support_classification_digest": _object(
                SUPPORT_PATH, label="support classification"
            )["support_classification_digest"],
            "mapping_manifest_digest": mapping_document["mapping_manifest_digest"],
            "sentinel_conformance_digest": sentinel[
                "sentinel_conformance_digest"
            ],
            "correctness_digest": correctness["correctness_digest"],
            "noise_evidence_digest": noise["noise_evidence_digest"],
        },
        activation_state="pending_fresh_verifier_closeout_commit_and_post_audit",
    )
    recovered = _write_or_match_json(output_path, decision)
    os.chmod(output_path, 0o644)
    current = _absolute_storage_counter(current_before, contract)
    with ledger.acquire_writer():
        blocked = _resource_block_if_needed(
            ledger=ledger,
            root=root,
            contract_digest=contract_digest,
            lock_digest=lock_digest,
            caps=_frozen_caps(contract),
            current=current_before,
            reservation=_reservation(contract, "decision"),
            actual_counter=current,
            next_atomic_unit={"kind": "decision"},
            completed_artifact_ref={
                "path": _repo_relative(output_path),
                "sha256": sha256_file(output_path),
                "decision_digest": decision["decision_digest"],
            },
            recovered_unledgered_complete_artifact=(
                recovered or recovered_path
            ),
        )
        if blocked is not None:
            return blocked
        if Stage(ledger.load()[-1]["stage"]) == Stage.NOISE_CELLS:
            ready = ledger.append(
                _event_payload(
                    stage=Stage.DECISION_READY,
                    contract_digest=contract_digest,
                    lock_digest=lock_digest,
                    counter=current,
                    fixture_digest=decision["decision_digest"],
                    support_observation_ref={
                        "path": _repo_relative(output_path),
                        "sha256": sha256_file(output_path),
                    },
                    resume_cursor=None,
                    recovered_unledgered_complete_artifact=recovered,
                )
            )
            ledger.fsync()
        else:
            ready = ledger.load()[-1]
            if (
                ready.get("fixture_digest") != decision["decision_digest"]
                or ready.get("support_observation_ref", {}).get("sha256")
                != sha256_file(output_path)
            ):
                raise RunnerError("DECISION_READY artifact binding mismatch")
        terminal = ledger.append(
            _event_payload(
                stage=Stage.TERMINAL_POSITIVE,
                contract_digest=contract_digest,
                lock_digest=lock_digest,
                counter=current,
                fixture_digest=decision["decision_digest"],
                support_observation_ref={
                    "path": _repo_relative(output_path),
                    "sha256": sha256_file(output_path),
                },
                verified_outgoing_edge=None,
                activation_state=decision["activation_state"],
                resume_cursor=None,
                recovered_unledgered_complete_artifact=recovered,
            )
        )
        ledger.fsync()
    return {
        "status": "TERMINAL_POSITIVE_PENDING_VERIFICATION_AND_CLOSEOUT",
        "criterion": "S1_ENTRY_GO",
        "edge": None,
        "decision_ready_event_digest": ready["event_digest"],
        "terminal_event_digest": terminal["event_digest"],
    }


def reproduce_formal_decision(
    *,
    run_root: Path | str | None = None,
    lock_path: Path | str = LOCK_PATH,
    output_path: Path | str,
) -> dict[str, Any]:
    """Freshly rederive the locked decision from raw ledger-linked artifacts."""

    contract, lock_digest = require_effective_lock(lock_path)
    root = _formal_root(contract, run_root)
    output = Path(output_path).resolve()
    try:
        output.relative_to(root)
    except ValueError as error:
        raise RunnerError("reproduction output must be below formal run root") from error
    ledger = RunLedger(root / "ledger")
    events = ledger.load()
    if not events or Stage(events[-1]["stage"]) not in {
        Stage.TERMINAL_POSITIVE,
        Stage.TERMINAL_NEGATIVE,
        Stage.TERMINAL_INCONCLUSIVE,
    }:
        raise RunnerError("formal decision is not terminalized")
    decision = _object(DECISION_PATH, label="formal decision")
    decision_body = dict(decision)
    decision_digest = decision_body.pop("decision_digest", None)
    if (
        decision_digest != canonical_sha256(decision_body)
        or decision.get("contract_digest") != canonical_sha256(contract)
        or decision.get("lock_digest") != lock_digest
    ):
        raise RunnerError("formal decision binding mismatch")
    _, registry = _load_registry_document()
    support_document = _object(SUPPORT_PATH, label="support classification")
    witnesses = _witnesses_from_events(ledger, registry)
    witnessed_atoms = {
        atom_id for witness in witnesses for atom_id in witness["covered_atom_ids"]
    }
    rederived_states = classify_support(registry, witnessed_atoms)
    recorded_states = {
        row["atom_id"]: row["state"] for row in support_document["atoms"]
    }
    if rederived_states != recorded_states:
        raise RunnerError("support classification does not reproduce")
    classification = decision["classification"]
    checks: dict[str, Any] = {
        "ledger_events": len(events),
        "support": "PASS",
    }
    required = mandatory_atoms(registry.prelocked_atoms(), rederived_states)
    if classification == "inconclusive" and not MAPPING_PATH.exists():
        try:
            exact_ten_greedy_cover(witnesses, required)
        except MappingError as error:
            if "FT-INCONCLUSIVE" not in str(error):
                raise
            checks["exact_ten"] = "REPRODUCED_FT_INCONCLUSIVE"
        else:
            raise RunnerError("recorded exact-ten inconclusive no longer reproduces")
    else:
        selection = _load_exact_ten(root, ledger)
        reproduced_selection = exact_ten_greedy_cover(witnesses, required)
        if (
            reproduced_selection["config_hashes"] != selection["config_hashes"]
            or reproduced_selection["required_atom_ids"]
            != selection["required_atom_ids"]
        ):
            raise RunnerError("exact-ten selection does not reproduce")
        checks["exact_ten"] = "PASS"
    if MAPPING_PATH.exists():
        mapping_document = _object(MAPPING_PATH, label="mapping corpus")
        if mapping_document["ab_byte_semantic_parity"] is not True:
            raise RunnerError("mapping A/B parity was not established")
        if mapping_document["status"] == "PASS":
            parity = verify_ab_parity(
                mapping_document["pass_a"],
                mapping_document["pass_b"],
                expected_config_hashes=mapping_document["selection"]["config_hashes"],
                expected_size_ids=["small", "medium", "large"],
            )
            checks["mapping"] = parity["status"]
        elif mapping_document["status"] == "FT-BLOCKED-MAPPING":
            if not mapping_document["rejected_row_count"]:
                raise RunnerError("mapping negative lacks reproduced rejected rows")
            checks["mapping"] = "REPRODUCED_FT_BLOCKED_MAPPING"
    if SENTINEL_PATH.exists():
        sentinel = _object(SENTINEL_PATH, label="sentinel conformance")
        if (
            sentinel.get("status") != "PASS"
            or sentinel.get("native_conformance", {}).get("status") != "PASS"
            or sentinel.get("substitution_fault_tests", {}).get("status") != "PASS"
        ):
            raise RunnerError("native conformance does not reproduce as PASS")
        checks["native_conformance"] = "PASS"
    if CORRECTNESS_PATH.exists():
        correctness = _object(CORRECTNESS_PATH, label="correctness evidence")
        if correctness["status"] == "PASS":
            verification = verify_correctness_anchors(
                correctness["rows"],
                anchors=correctness["anchors"],
                size_ids=["small", "medium", "large"],
            )
            checks["correctness"] = verification["status"]
        else:
            checks["correctness"] = "RECORDED_FAILURE_REQUIRES_FRESH_RERUN"
    if NOISE_PATH.exists():
        noise = _object(NOISE_PATH, label="noise evidence")
        validation = validate_noise_cells(
            noise["rows"],
            anchors=noise["anchors"],
            size_ids=["small", "medium", "large"],
            cv_p95_threshold=float(contract["noise"]["cv_p95_threshold"]),
        )
        if validation["status"] != noise["status"]:
            raise RunnerError("noise status does not reproduce")
        checks["noise"] = validation["status"]
    body = {
        "schema_version": 1,
        "checkpoint_id": "S10R2",
        "contract_digest": canonical_sha256(contract),
        "lock_digest": lock_digest,
        "decision_digest": decision_digest,
        "classification": classification,
        "checks": checks,
        "status": "PASS",
        "independent_process_required": True,
    }
    document = {**body, "reproduction_digest": canonical_sha256(body)}
    atomic_write_json(output, document, exclusive=True)
    return document


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate-contract")

    schedule = subcommands.add_parser("dry-run-schedule")
    schedule.add_argument("--conditional-target-count", type=int, required=True)

    caps = subcommands.add_parser("derive-caps")
    caps.add_argument("--allocation", type=Path, required=True)
    caps.add_argument("--metrics", type=Path, required=True)
    caps.add_argument("--output", type=Path, required=True)
    caps.add_argument("--preemp-engineering-s", type=float, required=True)

    materialize = subcommands.add_parser("materialize-pinned-native")
    materialize.add_argument("--output-root", type=Path, required=True)

    native_build = subcommands.add_parser("build-pinned-native")
    native_build.add_argument("--integration-root", type=Path, required=True)
    native_build.add_argument("--build-root", type=Path, required=True)

    native_fixture = subcommands.add_parser("run-native-fixture")
    native_fixture.add_argument("--build-manifest", type=Path, required=True)
    native_fixture.add_argument("--output-root", type=Path, required=True)

    client_build = subcommands.add_parser("build-pinned-client")
    client_build.add_argument("--native-build-manifest", type=Path, required=True)
    client_build.add_argument("--output-root", type=Path, required=True)

    registry = subcommands.add_parser("materialize-candidate-registry")
    registry.add_argument("--integration-root", type=Path, required=True)
    registry.add_argument("--output", type=Path, default=REGISTRY_PATH)

    selection_calibration = subcommands.add_parser("calibrate-selection")
    selection_calibration.add_argument("--integration-root", type=Path, required=True)
    selection_calibration.add_argument("--output-root", type=Path, required=True)
    selection_calibration.add_argument("--registry", type=Path, default=REGISTRY_PATH)

    gpu_calibration = subcommands.add_parser("calibrate-gpu")
    gpu_calibration.add_argument("--output-root", type=Path, required=True)

    size_registry = subcommands.add_parser("materialize-size-registry")
    size_registry.add_argument("--output", type=Path, default=SIZE_REGISTRY_PATH)

    mapping_calibration = subcommands.add_parser("calibrate-mapping")
    mapping_calibration.add_argument("--integration-root", type=Path, required=True)
    mapping_calibration.add_argument("--output-root", type=Path, required=True)

    correctness_calibration = subcommands.add_parser("calibrate-correctness-build")
    correctness_calibration.add_argument("--integration-root", type=Path, required=True)
    correctness_calibration.add_argument("--client-build", type=Path, required=True)
    correctness_calibration.add_argument("--output-root", type=Path, required=True)

    seal = subcommands.add_parser("seal-lock")
    seal.add_argument("--audit", type=Path, required=True)
    seal.add_argument("--calibration", type=Path, required=True)
    seal.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    seal.add_argument("--output", type=Path, default=LOCK_PATH)

    check = subcommands.add_parser("verify-lock")
    check.add_argument("--lock", type=Path, default=LOCK_PATH)

    # This command is a deliberate boundary probe.  Formal subcommands are
    # added only after their implementation is independently audited; this
    # guard proves that no outcome path can run under a draft contract.
    guard = subcommands.add_parser("formal-preflight")
    guard.add_argument("--lock", type=Path, default=LOCK_PATH)

    formal_initialize = subcommands.add_parser("formal-initialize")
    formal_initialize.add_argument("--lock", type=Path, default=LOCK_PATH)

    formal_discovery = subcommands.add_parser("formal-discovery-step")
    formal_discovery.add_argument("--lock", type=Path, default=LOCK_PATH)
    formal_discovery.add_argument("--max-new-chunks", type=int, required=True)

    formal_support = subcommands.add_parser("formal-seal-support")
    formal_support.add_argument("--lock", type=Path, default=LOCK_PATH)

    formal_select = subcommands.add_parser("formal-select-exact-ten")
    formal_select.add_argument("--lock", type=Path, default=LOCK_PATH)

    formal_mapping = subcommands.add_parser("formal-mapping")
    formal_mapping.add_argument("--lock", type=Path, default=LOCK_PATH)

    formal_native = subcommands.add_parser("formal-native-conformance")
    formal_native.add_argument("--lock", type=Path, default=LOCK_PATH)

    formal_gpu = subcommands.add_parser("formal-gpu-environment")
    formal_gpu.add_argument("--lock", type=Path, default=LOCK_PATH)

    formal_correctness = subcommands.add_parser("formal-correctness")
    formal_correctness.add_argument("--lock", type=Path, default=LOCK_PATH)

    formal_noise = subcommands.add_parser("formal-noise")
    formal_noise.add_argument("--lock", type=Path, default=LOCK_PATH)

    formal_decision = subcommands.add_parser("formal-decision")
    formal_decision.add_argument("--lock", type=Path, default=LOCK_PATH)

    formal_reproduce = subcommands.add_parser("formal-reproduce")
    formal_reproduce.add_argument("--lock", type=Path, default=LOCK_PATH)
    formal_reproduce.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate-contract":
        result = validate_contract()
    elif args.command == "dry-run-schedule":
        result = dry_run_schedule(args.conditional_target_count)
    elif args.command == "derive-caps":
        result = derive_resource_fixture(
            allocation_path=args.allocation,
            metrics_path=args.metrics,
            output_path=args.output,
            preemp_engineering_s=args.preemp_engineering_s,
        )
    elif args.command == "materialize-pinned-native":
        result = materialize_pinned_native_source(args.output_root)
    elif args.command == "build-pinned-native":
        result = build_pinned_native_helper(
            integration_root=args.integration_root,
            build_root=args.build_root,
        )
    elif args.command == "run-native-fixture":
        result = run_native_fixture(
            build_manifest_path=args.build_manifest,
            output_root=args.output_root,
        )
    elif args.command == "build-pinned-client":
        result = build_pinned_client(
            native_build_manifest_path=args.native_build_manifest,
            output_root=args.output_root,
        )
    elif args.command == "materialize-candidate-registry":
        result = materialize_candidate_registry(
            integration_root=args.integration_root,
            output_path=args.output,
        )
    elif args.command == "calibrate-selection":
        result = calibrate_selection_chunk(
            integration_root=args.integration_root,
            output_root=args.output_root,
            registry_path=args.registry,
        )
    elif args.command == "calibrate-gpu":
        result = calibrate_gpu_fixed_cost(output_root=args.output_root)
    elif args.command == "materialize-size-registry":
        result = materialize_size_registry(args.output)
    elif args.command == "calibrate-mapping":
        result = calibrate_mapping_row(
            integration_root=args.integration_root,
            output_root=args.output_root,
        )
    elif args.command == "calibrate-correctness-build":
        result = calibrate_correctness_build_cell(
            integration_root=args.integration_root,
            client_build_path=args.client_build,
            output_root=args.output_root,
        )
    elif args.command == "seal-lock":
        result = create_effective_lock(
            audit_path=args.audit,
            calibration_path=args.calibration,
            registry_path=args.registry,
            output_path=args.output,
        )
    elif args.command == "verify-lock":
        contract, lock_digest = require_effective_lock(
            args.lock,
            enforce_allocation_window=False,
        )
        result = {
            "checkpoint_id": "S10R2",
            "contract_digest": canonical_sha256(contract),
            "lock_digest": lock_digest,
            "status": "LOCK_VERIFIED",
        }
    elif args.command == "formal-preflight":
        contract, lock_digest = require_effective_lock(
            args.lock,
            enforce_allocation_window=False,
        )
        _validate_contract_allocation(
            contract,
            required_duration_s=float(
                contract["resource"]["numeric_relock"]["caps"]["wall_s"]
            ),
        )
        result = {
            "checkpoint_id": "S10R2",
            "contract_digest": canonical_sha256(contract),
            "lock_digest": lock_digest,
            "status": "LOCKED_READY",
        }
    elif args.command == "formal-initialize":
        result = initialize_formal_run(lock_path=args.lock)
    elif args.command == "formal-discovery-step":
        result = formal_discovery_step(
            max_new_chunks=args.max_new_chunks,
            lock_path=args.lock,
        )
    elif args.command == "formal-seal-support":
        result = seal_support_classification(lock_path=args.lock)
    elif args.command == "formal-select-exact-ten":
        result = select_exact_ten(lock_path=args.lock)
    elif args.command == "formal-mapping":
        result = run_formal_mapping(lock_path=args.lock)
    elif args.command == "formal-native-conformance":
        result = run_formal_native_conformance(lock_path=args.lock)
    elif args.command == "formal-gpu-environment":
        result = record_formal_gpu_environment(lock_path=args.lock)
    elif args.command == "formal-correctness":
        result = run_formal_correctness(lock_path=args.lock)
    elif args.command == "formal-noise":
        result = run_formal_noise(lock_path=args.lock)
    elif args.command == "formal-decision":
        result = materialize_formal_decision(lock_path=args.lock)
    elif args.command == "formal-reproduce":
        result = reproduce_formal_decision(
            lock_path=args.lock,
            output_path=args.output,
        )
    else:  # pragma: no cover - argparse is exhaustive
        raise RunnerError(f"unknown command {args.command}")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, RunnerError, ValueError) as error:
        print(f"S10R2_ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
