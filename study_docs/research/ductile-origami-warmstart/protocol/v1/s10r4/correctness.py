# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Frozen GPU identity, correctness-attempt, and noise aggregation rules."""

from __future__ import annotations

import math
import statistics
import csv
import io
import json
import os
import re
import shlex
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contract import (
    FIXED_ENVIRONMENT,
    S10R4Error,
    atomic_write_bytes,
    atomic_write_json,
    canonical_sha256,
    load_json,
    ordinary_file_records,
    raw_sha256,
    seal_digest,
    validate_document_schema,
)


def anchor_indices(k: int) -> tuple[int, int, int]:
    if not 10 <= k <= 20:
        raise S10R4Error("anchor K must be inside the frozen [10,20] bound")
    return 0, (k - 1) // 2, k - 1


def select_gpu(allocation_rows: Sequence[Mapping[str, Any]], pid_rows: Mapping[int, Sequence[int]]) -> Mapping[str, Any]:
    eligible: list[Mapping[str, Any]] = []
    for row in allocation_rows:
        index = row.get("physical_visible_index")
        if not isinstance(index, int):
            raise S10R4Error("GPU allocation row lacks a physical index")
        if (
            row.get("gfx_version") == "gfx942"
            and row.get("compute_partition") == "SPX"
            and row.get("memory_partition") == "NPS1"
            and row.get("gpu_use_percent") == "0"
            and row.get("vram_allocated_percent") == "0"
            and list(pid_rows.get(index, ())) == []
        ):
            eligible.append(row)
    if not eligible:
        raise S10R4Error("BLOCKED: no free eligible gfx942/SPX/NPS1 card")
    return min(eligible, key=lambda row: int(row["physical_visible_index"]))


def verify_gpu_continuity(selected: Mapping[str, Any], current: Mapping[str, Any], foreign_pids: Sequence[int]) -> None:
    identity_fields = (
        "physical_visible_index",
        "unique_id",
        "serial_number",
        "gfx_version",
        "compute_partition",
        "memory_partition",
    )
    if any(selected.get(field) != current.get(field) for field in identity_fields):
        raise S10R4Error("selected GPU identity drift")
    if (
        current.get("gpu_use_percent") != "0"
        or current.get("vram_allocated_percent") != "0"
        or foreign_pids
    ):
        raise S10R4Error("WAIT_RECHECK_SAME_CARD: selected GPU is no longer eligible")


@dataclass(frozen=True)
class CorrectnessAttempt:
    status: str
    failure_stage: str | None
    signature: Mapping[str, Any]


def decide_correctness_attempts(attempts: Sequence[CorrectnessAttempt]) -> str:
    if len(attempts) == 1 and attempts[0].status == "PASS":
        return "correctness_cell_PASS"
    if len(attempts) != 2:
        raise S10R4Error("correctness attempts must be one PASS or two failed reproductions")
    first, second = attempts
    if first.status == "PASS":
        raise S10R4Error("CHANGES_REQUIRED: correctness retry after PASS")
    allowed = {"generate", "compile", "smoke", "nonzero_correctness"}
    if (
        first.status != "FAIL"
        or second.status != "FAIL"
        or first.failure_stage not in allowed
        or second.failure_stage != first.failure_stage
        or first.signature != second.signature
    ):
        raise S10R4Error("CHANGES_REQUIRED: correctness failure is not an exact allowlisted reproduction")
    return "negative_S1_ENTRY_BLOCKED_FT_BLOCKED_CORRECTNESS_edge_null"


def nearest_rank(values: Sequence[float], probability: float) -> float:
    if not values or not 0.0 < probability <= 1.0:
        raise S10R4Error("invalid nearest-rank input")
    ordered = sorted(values)
    rank = math.ceil(probability * len(ordered))
    return ordered[rank - 1]


def aggregate_noise(groups: Mapping[str, Sequence[float]]) -> dict[str, Any]:
    if len(groups) != 9:
        raise S10R4Error("noise panel must contain exactly nine groups")
    group_rows: list[dict[str, Any]] = []
    deviations: list[float] = []
    for group_id in sorted(groups):
        qualities = list(groups[group_id])
        if len(qualities) != 7 or any(not isinstance(q, (int, float)) or not math.isfinite(q) or q <= 0 for q in qualities):
            raise S10R4Error(f"noise group {group_id} does not contain seven positive finite qualities")
        qualities = [float(q) for q in qualities]
        mean = statistics.fmean(qualities)
        sample_sd = statistics.stdev(qualities)
        cv_percent = 100.0 * sample_sd / mean
        logs = sorted(math.log(q) for q in qualities)
        median_log = logs[3]
        deviations.extend(abs(math.log(q) - median_log) for q in qualities)
        group_rows.append(
            {
                "group_id": group_id,
                "qualities": qualities,
                "mean": mean,
                "sample_standard_deviation": sample_sd,
                "cv_percent": cv_percent,
            }
        )
    cv_p95 = nearest_rank([row["cv_percent"] for row in group_rows], 0.95)
    d60 = nearest_rank(deviations, 0.95)
    delta_noise = math.exp(d60) - 1.0
    if not math.isfinite(delta_noise) or delta_noise < 0:
        raise S10R4Error("delta_noise is not finite and nonnegative")
    return {
        "group_count": 9,
        "repeat_count": 63,
        "groups": group_rows,
        "cv_p95_percent": cv_p95,
        "cv_threshold_percent": 0.5,
        "cv_pass": cv_p95 <= 0.5,
        "delta_noise": delta_noise,
        "delta_noise_rank": 60,
        "schedule": {"NumWarmups": 321, "EnqueuesPerSync": 321, "MaxEnqueuesPerSync": 321},
    }


def validate_client_parameters(text: str) -> None:
    required = {
        "num-warmups": "321",
        "num-enqueues-per-sync": "321",
        "max-enqueues-per-sync": "321",
    }
    observed: dict[str, list[str]] = {key: [] for key in required}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key in observed:
            observed[key].append(value)
    for key, expected in required.items():
        if observed[key] != [expected]:
            raise S10R4Error(f"ClientParameters.ini frozen schedule mismatch: {key}")


def parse_allocation_snapshot(payload: bytes) -> list[dict[str, Any]]:
    """Normalize the exact rocm-smi JSON command without accepting text inference."""
    try:
        source = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise S10R4Error("GPU allocation snapshot is not strict JSON") from exc
    if not isinstance(source, dict):
        raise S10R4Error("GPU allocation snapshot root is not an object")
    rows: list[dict[str, Any]] = []
    for card_key, card in source.items():
        if not isinstance(card_key, str) or not isinstance(card, dict):
            raise S10R4Error("GPU allocation snapshot card row is malformed")
        match = re.search(r"(\d+)$", card_key)
        if match is None:
            raise S10R4Error("GPU allocation snapshot card index is ambiguous")
        lowered = {str(key).lower().replace(" ", "_"): value for key, value in card.items()}

        def exact(*names: str) -> Any:
            values = [lowered[name] for name in names if name in lowered]
            if len(values) != 1:
                raise S10R4Error(f"GPU snapshot field is absent/ambiguous: {names[0]}")
            return values[0]

        product = str(exact("card_series", "card_model", "gpu_product_name"))
        gfx_match = re.search(r"gfx\d+", product)
        gfx = gfx_match.group(0) if gfx_match else ("gfx942" if "MI300X" in product.upper() else None)
        if gfx is None:
            raise S10R4Error("GPU gfx identity cannot be resolved from exact product field")
        rows.append(
            {
                "physical_visible_index": int(match.group(1)),
                "unique_id": str(exact("unique_id", "unique_id_(unique_id)")),
                "serial_number": str(exact("serial_number", "serial_number_(serial_number)")),
                "gfx_version": gfx,
                "compute_partition": str(exact("compute_partition")),
                "memory_partition": str(exact("memory_partition")),
                "gpu_use_percent": str(exact("gpu_use_(%)", "gpu_use_percent", "gpu_use")),
                "vram_allocated_percent": str(
                    exact("gpu_memory_allocated_(%)", "vram_allocated_percent", "gpu_memory_use_percent")
                ),
            }
        )
    return sorted(rows, key=lambda row: row["physical_visible_index"])


def parse_process_snapshot(payload: bytes) -> dict[int, list[int]]:
    text = payload.decode("utf-8", errors="strict")
    result: dict[int, list[int]] = {}
    for line in text.splitlines():
        card = re.search(r"(?:GPU|card)\s*\[?(\d+)\]?", line, re.IGNORECASE)
        if card is None:
            continue
        pids = [int(value) for value in re.findall(r"\bPID\s*[:=]?\s*(\d+)\b", line, re.IGNORECASE)]
        result.setdefault(int(card.group(1)), []).extend(pids)
    return {card: sorted(set(pids)) for card, pids in result.items()}


def validate_snapshot_pair(
    allocation_payload: bytes,
    process_payload: bytes,
) -> tuple[list[dict[str, Any]], dict[int, list[int]]]:
    allocation = parse_allocation_snapshot(allocation_payload)
    processes = parse_process_snapshot(process_payload)
    for row in allocation:
        processes.setdefault(row["physical_visible_index"], [])
    if set(processes) - {row["physical_visible_index"] for row in allocation}:
        raise S10R4Error("GPU process snapshot references an unknown card")
    return allocation, processes


def correctness_build_request(
    *,
    config_hash: str,
    raw_config: Mapping[str, Any],
    anchor_index: int,
    size_id: str,
    size: Sequence[int],
    attempt: int,
    attempt_root: Path,
    selected_card: Mapping[str, Any],
    environment: Mapping[str, str],
    effective_lock_digest: str,
) -> dict[str, Any]:
    if attempt not in (1, 2) or size_id not in {"size-00", "size-01", "size-02"} or len(size) != 4:
        raise S10R4Error("correctness build request identity is outside the frozen panel")
    if len(effective_lock_digest) != 64 or any(ch not in "0123456789abcdef" for ch in effective_lock_digest):
        raise S10R4Error("correctness build effective-lock digest is malformed")
    request: dict[str, Any] = {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        "document_kind": "correctness_build_request",
        "config_hash": config_hash,
        "raw_config": dict(raw_config),
        "anchor_index": anchor_index,
        "size_id": size_id,
        "size": list(size),
        "attempt": attempt,
        "cwd": attempt_root.resolve(strict=False).as_posix(),
        "environment": dict(environment),
        "selected_gpu": dict(selected_card),
        "effective_lock_digest": effective_lock_digest,
        "actual_yaml": "/src/rocm-libraries/study_docs/research/ductile-origami-warmstart/protocol/v1/inputs/s10-generated.yaml",
        "actual_yaml_sha256": "faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36",
        "prebuilt_client": "/src/rocm-libraries/agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame/artifacts/prelabel-build/native/build/hipblaslt/tensilelite/client/tensilelite-client",
        "timeout_s": 7200,
    }
    request["input_digest"] = canonical_sha256(request)
    validate_document_schema(request)
    return request


def _find_exactly_one(root: Path, name: str) -> Path:
    matches = sorted(path for path in root.rglob(name) if path.is_file())
    if len(matches) != 1:
        raise S10R4Error(f"expected exactly one {name}, observed {len(matches)}")
    return matches[0]


def _kernel_payload_sha256(value: Any) -> str:
    if isinstance(value, bytes):
        import hashlib

        return hashlib.sha256(value).hexdigest()
    return canonical_sha256(value)


class _ToolchainCallRecorder:
    """Pass through pinned tool invocations while recording their exact boundary."""

    def __init__(self, before_build_call: Any):
        self.before_build_call = before_build_call
        self.records: list[dict[str, Any]] = []
        self.version_probes: list[dict[str, Any]] = []
        self._inside_check_output = False
        self._run = subprocess.run
        self._check_output = subprocess.check_output

    @staticmethod
    def _argv(args: Any) -> list[str]:
        if isinstance(args, (str, bytes)):
            if isinstance(args, bytes):
                args = args.decode("utf-8", errors="strict")
            values = shlex.split(args)
        else:
            values = [os.fspath(value) for value in args]
        if not values or not all(isinstance(value, str) and value for value in values):
            raise S10R4Error("toolchain invocation argv is empty or malformed")
        return values

    @staticmethod
    def _is_version_probe(argv: Sequence[str]) -> bool:
        return len(argv) == 2 and argv[1] in ("--version", "-v")

    @staticmethod
    def _effective_cwd(kwargs: Mapping[str, Any]) -> Path:
        requested = kwargs.get("cwd")
        return Path.cwd().resolve(strict=True) if requested is None else Path(requested).resolve(strict=True)

    @staticmethod
    def _effective_environment(kwargs: Mapping[str, Any]) -> dict[str, str]:
        requested = kwargs.get("env")
        source = os.environ if requested is None else requested
        if not isinstance(source, Mapping):
            raise S10R4Error("toolchain invocation environment is not a mapping")
        environment = {os.fspath(key): os.fspath(value) for key, value in source.items()}
        if any(not key or "\x00" in key or "=" in key or "\x00" in value for key, value in environment.items()):
            raise S10R4Error("toolchain invocation environment is malformed")
        return environment

    @staticmethod
    def _input_output_paths(argv: Sequence[str], cwd: Path) -> list[dict[str, Any]]:
        output_options = {
            "-o", "-MF", "--output", "--output-file", "--output-dir",
            "--output-directory", "--dependency-file",
        }
        input_options = {"-I", "-L", "-include", "-isystem", "--sysroot"}
        path_suffixes = (
            ".a", ".bc", ".co", ".cpp", ".cxx", ".d", ".h", ".hpp", ".hsaco",
            ".ini", ".json", ".ll", ".o", ".py", ".s", ".so", ".txt", ".yaml", ".yml",
        )
        rows: list[dict[str, Any]] = []
        next_direction: str | None = None
        for index, argument in enumerate(argv[1:], start=1):
            if argument in output_options:
                next_direction = "output"
                continue
            if argument in input_options:
                next_direction = "input"
                continue
            direction = next_direction or "input"
            next_direction = None
            candidates: list[str] = []
            if argument.startswith("@"):
                candidates = [argument[1:]]
            elif argument.startswith("-") and "=" in argument:
                option, candidate = argument.split("=", 1)
                if option in output_options:
                    direction = "output"
                candidates = [candidate]
            elif argument.startswith(("-I", "-L")) and len(argument) > 2:
                candidates = [argument[2:]]
            elif argument.startswith("-Wl,"):
                candidates = [part for part in argument[4:].split(",") if part]
            elif not argument.startswith("-"):
                candidates = [argument]
            for candidate in candidates:
                if not (
                    direction == "output"
                    or candidate.startswith(("/", "./", "../"))
                    or "/" in candidate
                    or candidate.endswith(path_suffixes)
                ):
                    continue
                raw = Path(candidate)
                resolved = (raw if raw.is_absolute() else cwd / raw).resolve(strict=False)
                rows.append(
                    {
                        "argument_index": index,
                        "argument": argument,
                        "resolved_path": resolved.as_posix(),
                        "direction": direction,
                        "exists_before": resolved.exists(),
                    }
                )
        if next_direction is not None:
            raise S10R4Error("toolchain path option lacks a value")
        return rows

    @classmethod
    def _identity(cls, argv: Sequence[str], kwargs: Mapping[str, Any]) -> dict[str, Any]:
        if not Path(argv[0]).is_absolute():
            raise S10R4Error("toolchain wrapper executable is not absolute")
        executable = Path(argv[0]).resolve(strict=True)
        info = executable.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or not os.access(executable, os.X_OK):
            raise S10R4Error("toolchain executable is not an executable ordinary file")
        cwd = cls._effective_cwd(kwargs)
        return {
            "argv": list(argv),
            "cwd": cwd.as_posix(),
            "environment": cls._effective_environment(kwargs),
            "requested_executable": argv[0],
            "resolved_executable": executable.as_posix(),
            "executable_sha256": raw_sha256(executable),
            "input_output_paths": cls._input_output_paths(argv, cwd),
        }

    def _record(self, identity: Mapping[str, Any], returncode: int, *, call_api: str) -> None:
        self.records.append(
            {
                "wrapper_ordinal": len(self.records),
                **identity,
                "call_api": call_api,
                "return_status": returncode,
            }
        )

    def run(self, args: Any, *positional: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        if self._inside_check_output:
            return self._run(args, *positional, **kwargs)
        argv = self._argv(args)
        shell = kwargs.get("shell", False)
        if shell:
            # Tensile's import-time ROCm version query is the only shell-shaped
            # call in the pinned module. Resolve that metadata in-process so the
            # formal exec graph contains no forbidden /bin/sh node.
            if argv != ["/opt/rocm/bin/hipconfig", "--version"]:
                raise S10R4Error("foreign shell-shaped process requested by correctness build")
            version_file = Path("/opt/rocm/.info/version")
            version = version_file.read_text(encoding="utf-8").strip().split("-", 1)[0]
            payload = (version + "\n").encode("ascii")
            self.version_probes.append(
                {
                    "kind": "in_process_rocm_version",
                    "requested_argv": argv,
                    "source_path": version_file.as_posix(),
                    "source_sha256": raw_sha256(version_file),
                }
            )
            return subprocess.CompletedProcess(args, 0, stdout=payload)
        if not self._is_version_probe(argv):
            self.before_build_call()
        identity = self._identity(argv, kwargs)
        completed = self._run(args, *positional, **kwargs)
        self._record(identity, int(completed.returncode), call_api="subprocess.run")
        return completed

    def check_output(self, args: Any, *positional: Any, **kwargs: Any) -> bytes:
        argv = self._argv(args)
        if kwargs.get("shell", False):
            raise S10R4Error("shell execution is forbidden in correctness build")
        if not self._is_version_probe(argv):
            self.before_build_call()
        identity = self._identity(argv, kwargs)
        try:
            self._inside_check_output = True
            output = self._check_output(args, *positional, **kwargs)
        except subprocess.CalledProcessError as exc:
            self._record(identity, int(exc.returncode), call_api="subprocess.check_output")
            raise
        finally:
            self._inside_check_output = False
        self._record(identity, 0, call_api="subprocess.check_output")
        return output


def _actual_correctness_build_backend(request: Mapping[str, Any]) -> dict[str, Any]:
    import yaml
    from .census import singleton_yaml_document

    actual_yaml = Path(request["actual_yaml"])
    if raw_sha256(actual_yaml) != request["actual_yaml_sha256"]:
        raise S10R4Error("correctness actual YAML identity mismatch")
    root = Path(request["cwd"])
    singleton_path = root / "singleton.yaml"
    output = root / "output"
    base = yaml.safe_load(actual_yaml.read_text(encoding="utf-8"))
    singleton = singleton_yaml_document(base, request["raw_config"], (request["size"],), correctness=True)
    atomic_write_bytes(singleton_path, yaml.safe_dump(singleton, sort_keys=False).encode("utf-8"))
    user_args = [
        singleton_path.as_posix(), output.as_posix(), "--build-only", "--device", "0",
        "--gpu-targets", "gfx942", "--prebuilt-client", request["prebuilt_client"],
        "--cxx-compiler", "/opt/rocm/bin/amdclang++", "--c-compiler", "/opt/rocm/bin/amdclang++",
        "--assembler", "/opt/rocm/bin/amdclang++",
        "--offload-bundler", "/opt/rocm/lib/llvm/bin/clang-offload-bundler",
    ]
    observed: dict[str, Any] = {
        "resolved_solution": None,
        "required_assembly_kernels": [],
        "required_helper_kernels": [],
        "process_kernel_results": [],
    }
    generation_path = root / "generation-boundary.json"

    def seal_generation_boundary() -> None:
        if generation_path.exists():
            return
        assembly = observed["required_assembly_kernels"]
        helpers = observed["required_helper_kernels"]
        if (
            not isinstance(observed["resolved_solution"], dict)
            or not assembly
            or any(row.get("terminal_native_result") is not True for row in assembly)
            or any(row.get("err") is True for row in assembly)
            or not helpers
            or any(not row.get("source_present") or not row.get("header_present") for row in helpers)
        ):
            raise S10R4Error("correctness generation boundary is incomplete before toolchain execution")
        current_records, _ = ordinary_file_records(output)
        boundary = seal_digest(
            {
                "schema_version": 1,
                "checkpoint_id": "S10R4",
                "document_kind": "generation_boundary",
                "config_hash": request["config_hash"],
                "size_id": request["size_id"],
                "raw_config_sha256": canonical_sha256(request["raw_config"]),
                "resolved_solution_sha256": canonical_sha256(observed["resolved_solution"]),
                "singleton_yaml_sha256": raw_sha256(singleton_path),
                "user_args": user_args,
                "assembly_artifacts": assembly,
                "helper_artifacts": helpers,
                "process_kernel_results": observed["process_kernel_results"],
                "declared_artifact_inventory": current_records,
                "status": "PASS",
            }
        )
        validate_document_schema(boundary)
        atomic_write_json(generation_path, boundary)

    recorder = _ToolchainCallRecorder(seal_generation_boundary)
    original_run = subprocess.run
    original_check_output = subprocess.check_output
    subprocess.run = recorder.run
    subprocess.check_output = recorder.check_output
    caught: BaseException | None = None
    originals: tuple[Any, ...] | None = None
    try:
        from Tensile import BenchmarkProblems
        from Tensile.Tensile import Tensile
        from Tensile.TensileCreateLibrary import Run
        from Tensile.SolutionStructs.Naming import getKeyNoInternalArgs

        original_benchmark = BenchmarkProblems.writeBenchmarkFiles
        original_write = Run.writeSolutionsAndKernels
        original_benchmark_write = BenchmarkProblems.writeSolutionsAndKernels
        original_process = Run.processKernelSource
        originals = (
            BenchmarkProblems,
            Run,
            original_benchmark,
            original_write,
            original_benchmark_write,
            original_process,
        )

        def benchmark_wrapper(*args: Any, **kwargs: Any) -> Any:
            solutions = args[1] if len(args) > 1 else kwargs["solutions"]
            if len(solutions) != 1:
                raise S10R4Error("correctness singleton resolved other than one solution")
            observed["resolved_solution"] = dict(solutions[0]._state)
            return original_benchmark(*args, **kwargs)

        def write_wrapper(*args: Any, **kwargs: Any) -> Any:
            kernels = args[4]
            helpers = args[5]
            split_gsu = args[7]
            names = [getKeyNoInternalArgs(kernel, split_gsu) for kernel in kernels]
            if not names or len(names) != len(set(names)):
                raise S10R4Error("correctness required assembly set is empty or duplicated")
            observed["required_assembly_kernels"] = [{"name": name} for name in sorted(names)]
            helper_rows = []
            for helper in helpers:
                name = helper.getKernelName()
                source_error, source = helper.getSourceFileString()
                header = helper.getHeaderFileString()
                helper_rows.append(
                    {
                        "name": name,
                        "source_present": source_error == 0 and isinstance(source, str) and bool(source),
                        "source_sha256": canonical_sha256(source) if isinstance(source, str) else None,
                        "header_present": isinstance(header, str) and bool(header),
                        "header_sha256": canonical_sha256(header) if isinstance(header, str) else None,
                    }
                )
            observed["required_helper_kernels"] = sorted(helper_rows, key=lambda row: row["name"])
            return original_benchmark_write(*args, **kwargs)

        def process_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = original_process(*args, **kwargs)
            record = {
                "name": result.name,
                "terminal_native_result": True,
                "err": result.err != 0,
                "native_result_error_code": result.err,
                "source_present": bool(result.src),
                "header_present": bool(result.header),
                "source_sha256": _kernel_payload_sha256(result.src) if result.src else None,
                "header_sha256": _kernel_payload_sha256(result.header) if result.header else None,
            }
            observed["process_kernel_results"].append(record)
            for row in observed["required_assembly_kernels"]:
                if row["name"] == result.name:
                    row.update(record)
                    break
            return result

        BenchmarkProblems.writeBenchmarkFiles = benchmark_wrapper
        BenchmarkProblems.writeSolutionsAndKernels = write_wrapper
        Run.writeSolutionsAndKernels = write_wrapper
        Run.processKernelSource = process_wrapper
        Tensile(user_args)
    except BaseException as exc:
        caught = exc
    finally:
        subprocess.run = original_run
        subprocess.check_output = original_check_output
        if originals is not None:
            (
                benchmark_module,
                run_module,
                original_benchmark,
                original_write,
                original_benchmark_write,
                original_process,
            ) = originals
            benchmark_module.writeBenchmarkFiles = original_benchmark
            benchmark_module.writeSolutionsAndKernels = original_benchmark_write
            run_module.writeSolutionsAndKernels = original_write
            run_module.processKernelSource = original_process

    if caught is not None:
        assembly = observed["required_assembly_kernels"]
        complete_generate_failure = (
            isinstance(observed["resolved_solution"], dict)
            and bool(assembly)
            and all(row.get("terminal_native_result") is True for row in assembly)
            and any(row.get("err") is True for row in assembly)
            and not generation_path.exists()
        )
        failed_calls = [row for row in recorder.records if row["return_status"] != 0]
        if complete_generate_failure:
            failure = seal_digest(
                {
                    "schema_version": 1,
                    "checkpoint_id": "S10R4",
                    "document_kind": "generation_failure",
                    "config_hash": request["config_hash"],
                    "size_id": request["size_id"],
                    "singleton_yaml_sha256": raw_sha256(singleton_path),
                    "resolved_solution_sha256": canonical_sha256(observed["resolved_solution"]),
                    "assembly_results": assembly,
                    "helper_results": observed["required_helper_kernels"],
                    "exception_type": type(caught).__name__,
                    "exception_text_sha256": canonical_sha256(str(caught)),
                    "status": "FAIL",
                    "failure_stage": "generate",
                }
            )
            validate_document_schema(failure)
            atomic_write_json(root / "generation-failure.json", failure)
            return {
                "status": "FAIL",
                "failure_stage": "generate",
                "worker_returncode": 31,
                "generation_failure_digest": failure["document_digest"],
                "toolchain_calls": recorder.records,
                "in_process_version_probes": recorder.version_probes,
            }
        if generation_path.exists() and len(failed_calls) == 1:
            return {
                "status": "FAIL",
                "failure_stage": "compile",
                "worker_returncode": 32,
                "generation_boundary_digest": load_json(generation_path)["document_digest"],
                "failed_toolchain_call": failed_calls[0],
                "toolchain_calls": recorder.records,
                "in_process_version_probes": recorder.version_probes,
            }
        raise S10R4Error("correctness build exception does not match one complete structured stage") from caught
    seal_generation_boundary()
    records, _ = ordinary_file_records(output)
    generation_boundary = load_json(generation_path)
    client_config = _find_exactly_one(output, "ClientParameters.ini")
    validate_client_parameters(client_config.read_text(encoding="utf-8"))
    code_objects = [row for row in records if row["relative_path"].endswith((".co", ".hsaco"))]
    libraries = [row for row in records if Path(row["relative_path"]).name == "TensileLibrary.yaml"]
    if not code_objects or len(libraries) != 1:
        raise S10R4Error("correctness compile boundary code-object/library inventory mismatch")
    if not recorder.records or any(row["return_status"] != 0 for row in recorder.records):
        raise S10R4Error("correctness PASS lacks a complete successful toolchain call record")
    compile_boundary = seal_digest(
        {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": "compile_boundary",
            "generation_boundary_digest": generation_boundary["document_digest"],
            "code_objects": code_objects,
            "library": libraries[0],
            "client_parameters": {
                "path": client_config.as_posix(),
                "sha256": raw_sha256(client_config),
            },
            "toolchain_calls": recorder.records,
            "in_process_version_probes": recorder.version_probes,
            "complete_output_inventory": records,
            "user_args": user_args,
            "status": "PASS",
        }
    )
    validate_document_schema(compile_boundary)
    atomic_write_json(root / "compile-boundary.json", compile_boundary)
    return {
        "status": "PASS",
        "failure_stage": None,
        "worker_returncode": 0,
        "generation_boundary_digest": generation_boundary["document_digest"],
        "compile_boundary_digest": compile_boundary["document_digest"],
        "client_parameters_path": client_config.as_posix(),
        "client_parameters_sha256": raw_sha256(client_config),
        "code_objects": code_objects,
        "library": libraries[0],
        "toolchain_calls": recorder.records,
        "in_process_version_probes": recorder.version_probes,
        "user_args": user_args,
    }


def execute_correctness_build_worker(
    request: Mapping[str, Any],
    result_path: Path,
    *,
    backend: Any = None,
) -> int:
    expected = {
        "schema_version", "checkpoint_id", "document_kind", "config_hash", "raw_config",
        "anchor_index", "size_id", "size", "attempt", "cwd", "environment", "selected_gpu",
        "effective_lock_digest", "actual_yaml", "actual_yaml_sha256", "prebuilt_client", "timeout_s", "input_digest",
    }
    if set(request) != expected or request.get("document_kind") != "correctness_build_request":
        raise S10R4Error("correctness build request exact field set mismatch")
    if canonical_sha256({key: value for key, value in request.items() if key != "input_digest"}) != request["input_digest"]:
        raise S10R4Error("correctness build request digest mismatch")
    if Path.cwd().resolve().as_posix() != request["cwd"] or result_path.parent.resolve() != Path(request["cwd"]):
        raise S10R4Error("correctness build cwd/result association mismatch")
    output = (backend or _actual_correctness_build_backend)(request)
    returncode = output.get("worker_returncode")
    if returncode not in (0, 31, 32):
        raise S10R4Error("correctness build worker return code is unknown")
    document = seal_digest(
        {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": "correctness_build_result",
            "config_hash": request["config_hash"],
            "anchor_index": request["anchor_index"],
            "size_id": request["size_id"],
            "attempt": request["attempt"],
            "input_digest": request["input_digest"],
            "effective_lock_digest": request["effective_lock_digest"],
            "outputs": output,
        }
    )
    atomic_write_json(result_path, document)
    validate_document_schema(load_json(result_path))
    return int(returncode)


def parse_single_result_csv(path: Path, expected_size: Sequence[int]) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(raw))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise S10R4Error("result CSV header is absent or duplicated")
    rows = list(reader)
    if len(rows) != 1:
        raise S10R4Error("result CSV must contain exactly one row")
    row = rows[0]
    validation = row.get("Validation")
    if validation not in ("PASSED", "FAILED", "INVALID"):
        raise S10R4Error("result CSV Validation is outside the frozen enum")
    dimensions = []
    try:
        for key in ("M", "N", "NumBatches", "K"):
            if key not in row:
                raise S10R4Error(f"result CSV lacks {key}")
            dimensions.append(int(row[key]))
    except ValueError as exc:
        raise S10R4Error("result CSV contains a non-integer size coordinate") from exc
    if dimensions != list(expected_size):
        raise S10R4Error("result CSV size identity mismatch")
    quality_field = "GFlops" if "GFlops" in row else "GFLOPS" if "GFLOPS" in row else None
    time_field = "TimeUS" if "TimeUS" in row else "WinnerTimeUS" if "WinnerTimeUS" in row else None
    if quality_field is None or time_field is None:
        raise S10R4Error("result CSV lacks exact quality/time fields")
    try:
        quality = float(row[quality_field])
        winner_time = float(row[time_field])
    except ValueError as exc:
        raise S10R4Error("result CSV contains a nonnumeric quality/time") from exc
    if not math.isfinite(quality) or quality <= 0 or not math.isfinite(winner_time) or winner_time <= 0:
        raise S10R4Error("result CSV quality/time is not positive finite")
    return {
        "validation": validation,
        "validation_error_code": row.get("ValidationError", ""),
        "size": dimensions,
        "quality_gflops": quality,
        "winner_time_us": winner_time,
        "csv_sha256": raw_sha256(path),
    }


def decide_client_result(returncode: int, csv_paths: Sequence[Path], expected_size: Sequence[int]) -> dict[str, Any]:
    if len(csv_paths) == 0 and returncode != 0:
        return {"status": "FAIL", "failure_stage": "smoke", "process_returncode": returncode}
    if len(csv_paths) != 1:
        raise S10R4Error("correctness client result CSV inventory is incomplete/ambiguous")
    parsed = parse_single_result_csv(csv_paths[0], expected_size)
    if parsed["validation"] in ("FAILED", "INVALID"):
        return {
            "status": "FAIL", "failure_stage": "nonzero_correctness",
            "process_returncode": returncode, "validation": parsed,
        }
    if returncode != 0 or parsed["validation"] != "PASSED":
        raise S10R4Error("correctness client exit/validation decision is inconsistent")
    return {"status": "PASS", "failure_stage": None, "process_returncode": 0, "validation": parsed}


def rewrite_results_file(config: bytes, output_path: Path) -> bytes:
    try:
        text = config.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise S10R4Error("ClientParameters.ini is not UTF-8") from exc
    lines = text.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if line.startswith("results-file=")]
    if len(matches) != 1:
        raise S10R4Error("ClientParameters.ini results-file is absent or duplicated")
    ending = "\r\n" if lines[matches[0]].endswith("\r\n") else "\n" if lines[matches[0]].endswith("\n") else ""
    lines[matches[0]] = f"results-file={output_path.as_posix()}{ending}"
    rewritten = "".join(lines).encode("utf-8")
    validate_client_parameters(rewritten.decode("utf-8"))
    return rewritten
