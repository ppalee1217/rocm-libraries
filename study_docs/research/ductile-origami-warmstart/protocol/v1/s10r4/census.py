# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Pinned-source materialization and structured normal-filter census semantics."""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import stat
import subprocess
import tarfile
import tempfile
import traceback
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from .contract import (
    FIXED_ENVIRONMENT,
    REPO_ROOT,
    S10R4Error,
    atomic_write_bytes,
    atomic_write_json,
    canonical_json,
    canonical_sha256,
    load_contract,
    load_json,
    materialize_command_template,
    ordinary_file_records,
    pinned_source_declarations,
    raw_sha256,
    safe_relative_path,
    seal_digest,
    validate_document_schema,
)


DUCTILE_COMMIT = "5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39"
GEKO_COMMIT = "d32abacfd13579d1f523f035b7a10b0734c4ac47"
PINNED_BLOBS = {
    "projects/hipblaslt/tensilelite/Tensile/BenchmarkProblems.py": "c9e4144ca0b2d7396c57249eaf3770b12ebd87f8",
    "projects/hipblaslt/tensilelite/Tensile/TensileCreateLibrary/Run.py": "87b6bfd931701801e1e626884068390360083e5c",
    "projects/hipblaslt/tensilelite/Tensile/backends/ductile_backend.py": "e295e481f832cf00d9826e7aaf6130aaaf9651d2",
    "projects/hipblaslt/tensilelite/Tensile/KernelWriterAssembly.py": "99ff3ec21c68facde233ba60073588bdfbefb281",
    "shared/origami/src/simulator/tensilelite/formocast_simulator.cpp": "cac2b324984a9fe2e1fadb018702486545e86e80",
    "shared/origami/include/origami/simulator/tensilelite/formocast_simulator.hpp": "96741965d34f2da1b0a08eaecab15e72082a78bc",
    "projects/hipblaslt/tensilelite/client/src/SolutionIterator.cpp": "33e86cfc4bf3d4ce8fa8da194b94c024bbb5639f",
    "projects/hipblaslt/tensilelite/client/include/SolutionIterator.hpp": "bad091c0f299f30c4235bc8313c9e8f134fa66a5",
}


def git_blob_oid(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _safe_extract(archive_stream: io.BufferedReader, destination: Path) -> None:
    pending_links: list[tuple[Path, str]] = []
    with tarfile.open(fileobj=archive_stream, mode="r|") as archive:
        for member in archive:
            relative = safe_relative_path(member.name)
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                os.chmod(target, stat.S_IMODE(member.mode))
            elif member.isreg():
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    raise S10R4Error(f"duplicate archive target: {relative}")
                source = archive.extractfile(member)
                if source is None:
                    raise S10R4Error(f"archive regular file has no payload: {relative}")
                descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, stat.S_IMODE(member.mode))
                with os.fdopen(descriptor, "wb") as output:
                    shutil.copyfileobj(source, output)
            elif member.issym():
                link = PurePosixPath(member.linkname)
                if link.is_absolute():
                    raise S10R4Error(f"archive absolute symlink forbidden: {relative}")
                resolved_parts: list[str] = []
                for part in relative.parent.parts + link.parts:
                    if part in ("", "."):
                        continue
                    if part == "..":
                        if not resolved_parts:
                            raise S10R4Error(f"archive symlink escapes root: {relative}")
                        resolved_parts.pop()
                    else:
                        resolved_parts.append(part)
                pending_links.append((target, member.linkname))
            else:
                raise S10R4Error(f"archive member type forbidden: {relative}")
    for target, linkname in pending_links:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            raise S10R4Error(f"duplicate archive symlink target: {target}")
        os.symlink(linkname, target)


def materialize_pinned_source(build_root: Path, *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_root = build_root / "pinned-source"
    if output_root.exists():
        verify_pinned_source(output_root)
        return source_identity(output_root)
    build_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".pinned-source.", dir=build_root))
    stderr_path = build_root / "materialize.stderr"
    argv = materialize_command_template("materialize_ductile_source")
    with stderr_path.open("xb") as stderr:
        try:
            process = subprocess.Popen(
                argv,
                cwd=repo_root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=stderr,
                env={
                    "LC_ALL": "C",
                    "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
                    "PYTHONHASHSEED": "0",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
                },
            )
            assert process.stdout is not None
            _safe_extract(process.stdout, temporary)
            process.stdout.close()
            try:
                returncode = process.wait(timeout=600)
            except subprocess.TimeoutExpired as exc:
                process.kill()
                process.wait()
                raise S10R4Error("pinned source archive timed out") from exc
        except BaseException:
            # Preserve the failed isolated extraction for Main adjudication; never
            # silently clean or retry a partial materialization.
            raise
    if returncode != 0:
        raise S10R4Error(f"pinned source archive failed with return code {returncode}")
    verify_pinned_source(temporary)
    os.rename(temporary, output_root)
    return source_identity(output_root)


def verify_pinned_source(root: Path) -> None:
    root = root.resolve(strict=True)
    for relative, expected_blob in PINNED_BLOBS.items():
        path = root / relative
        data = path.read_bytes()
        if git_blob_oid(data) != expected_blob:
            raise S10R4Error(f"pinned source Git blob mismatch: {relative}")


def source_identity(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    files: list[dict[str, Any]] = []
    for declared in pinned_source_declarations(load_contract()):
        path = root / declared["repository_path"]
        info = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise S10R4Error(
                f"pinned source identity is not one ordinary file: {declared['repository_path']}"
            )
        data = path.read_bytes()
        observed_blob = git_blob_oid(data)
        if observed_blob != declared["expected_git_blob_oid"]:
            raise S10R4Error(f"pinned source identity blob mismatch: {declared['repository_path']}")
        files.append(
            {
                **declared,
                "materialized_path": path.as_posix(),
                "mode": stat.S_IMODE(info.st_mode),
                "link_count": info.st_nlink,
                "size_bytes": info.st_size,
                "raw_sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return {
        "ductile_commit": DUCTILE_COMMIT,
        "root": root.as_posix(),
        "files": files,
    }


def resolve_geko_commit(build_root: Path, *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    argv = materialize_command_template("resolve_geko_commit")
    completed = subprocess.run(
        argv,
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
        env={
            "LC_ALL": "C",
            "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
        },
    )
    build_root.mkdir(parents=True, exist_ok=True)
    for path, payload in (
        (build_root / "geko-resolution.stdout", completed.stdout),
        (build_root / "geko-resolution.stderr", completed.stderr),
    ):
        if path.exists():
            if not path.is_file() or path.read_bytes() != payload:
                raise S10R4Error(f"refusing to replace unequal GEKO resolution log: {path}")
        else:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
    if completed.returncode != 0:
        raise S10R4Error("GEKO pinned commit does not resolve")
    return {
        "commit": GEKO_COMMIT,
        "argv": argv,
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        "tree_materialized": False,
    }


def _artifact_record(relative_path: str, payload: bytes) -> dict[str, Any]:
    safe_relative_path(relative_path)
    return {
        "relative_path": relative_path,
        "mode": 0o644,
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _canonical_kernel_identity(config_hash: str, kind: str, name: str) -> str:
    if kind not in ("assembly", "helper") or not name:
        raise S10R4Error("required-kernel canonical identity input is malformed")
    return canonical_sha256(
        {"input_config_hash": config_hash, "kernel_kind": kind, "kernel_name": name}
    )


def _required_set_digest(config_hash: str, kind: str, names: Sequence[str]) -> str:
    return canonical_sha256(
        {
            "input_config_hash": config_hash,
            "kernel_kind": kind,
            "sorted_kernel_names": sorted(names),
        }
    )


def _inventory_index(records: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list):
        raise S10R4Error("CHANGES_REQUIRED: finalized child artifact inventory is absent")
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {
            "relative_path", "mode", "size_bytes", "sha256"
        }:
            raise S10R4Error("CHANGES_REQUIRED: malformed child artifact record")
        relative = record.get("relative_path")
        if not isinstance(relative, str):
            raise S10R4Error("CHANGES_REQUIRED: malformed child artifact path")
        safe_relative_path(relative)
        if relative in index:
            raise S10R4Error("CHANGES_REQUIRED: duplicate child artifact identity")
        if (
            not isinstance(record.get("mode"), int)
            or isinstance(record.get("mode"), bool)
            or not 0 <= record["mode"] <= 0o7777
            or not isinstance(record.get("size_bytes"), int)
            or isinstance(record.get("size_bytes"), bool)
            or record["size_bytes"] < 0
            or not isinstance(record.get("sha256"), str)
            or len(record["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in record["sha256"])
        ):
            raise S10R4Error("CHANGES_REQUIRED: malformed child artifact identity")
        index[relative] = record
    return index


def reconcile_native_artifacts(
    result: Mapping[str, Any],
    inventory: Sequence[Mapping[str, Any]],
    config_hash: str,
) -> dict[str, Any]:
    """Bind required native identities to the finalized ordinary-file inventory."""
    if (
        not isinstance(config_hash, str)
        or len(config_hash) != 64
        or any(character not in "0123456789abcdef" for character in config_hash)
    ):
        raise S10R4Error("CHANGES_REQUIRED: census input config identity is malformed")
    if result.get("input_config_hash") != config_hash:
        raise S10R4Error("CHANGES_REQUIRED: census input config association mismatch")
    index = _inventory_index(list(inventory))
    assembly = result.get("required_assembly_kernels")
    helpers = result.get("required_helper_kernels")
    declared = result.get("required_helper_declared_artifacts")
    if not isinstance(assembly, list) or not assembly or not isinstance(helpers, list):
        raise S10R4Error("CHANGES_REQUIRED: required assembly/helper set is incomplete")
    if not isinstance(declared, list) or len(declared) != 2:
        raise S10R4Error("CHANGES_REQUIRED: helper declared-artifact set is incomplete")

    assembly_names: list[str] = []
    for row in assembly:
        if not isinstance(row, dict):
            raise S10R4Error("CHANGES_REQUIRED: malformed assembly-kernel result")
        name = row.get("name")
        if not isinstance(name, str) or not name:
            raise S10R4Error("CHANGES_REQUIRED: malformed assembly-kernel name")
        assembly_names.append(name)
        if row.get("canonical_identity") != _canonical_kernel_identity(config_hash, "assembly", name):
            raise S10R4Error("CHANGES_REQUIRED: assembly canonical identity mismatch")
        expected = row.get("expected_artifact")
        if not isinstance(expected, dict) or index.get(expected.get("relative_path")) != expected:
            raise S10R4Error("CHANGES_REQUIRED: required assembly artifact inventory mismatch")

    helper_names: list[str] = []
    for row in helpers:
        if not isinstance(row, dict):
            raise S10R4Error("CHANGES_REQUIRED: malformed helper-kernel result")
        name = row.get("name")
        if not isinstance(name, str) or not name:
            raise S10R4Error("CHANGES_REQUIRED: malformed helper-kernel name")
        helper_names.append(name)
        if row.get("canonical_identity") != _canonical_kernel_identity(config_hash, "helper", name):
            raise S10R4Error("CHANGES_REQUIRED: helper canonical identity mismatch")
        for prefix in ("source", "header"):
            digest = row.get(f"{prefix}_sha256")
            size = row.get(f"{prefix}_size_bytes")
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
                or not isinstance(size, int)
                or isinstance(size, bool)
                or size <= 0
            ):
                raise S10R4Error(f"CHANGES_REQUIRED: helper {prefix} identity is incomplete")
            expected = row.get(f"{prefix}_artifact")
            if (
                not isinstance(expected, dict)
                or index.get(expected.get("relative_path")) != expected
                or expected.get("sha256") != digest
                or expected.get("size_bytes") != size
            ):
                raise S10R4Error(
                    f"CHANGES_REQUIRED: helper {prefix} artifact inventory mismatch"
                )

    if len(set(assembly_names)) != len(assembly_names):
        raise S10R4Error("CHANGES_REQUIRED: duplicate assembly-kernel identity")
    if len(set(helper_names)) != len(helper_names):
        raise S10R4Error("CHANGES_REQUIRED: duplicate helper-kernel identity")
    for record in declared:
        if not isinstance(record, dict) or index.get(record.get("relative_path")) != record:
            raise S10R4Error("CHANGES_REQUIRED: helper declared artifact inventory mismatch")
    if len({record["relative_path"] for record in declared}) != len(declared):
        raise S10R4Error("CHANGES_REQUIRED: duplicate helper declared artifact identity")
    if result.get("required_assembly_kernel_set_digest") != _required_set_digest(
        config_hash, "assembly", assembly_names
    ):
        raise S10R4Error("CHANGES_REQUIRED: assembly set digest is not config-bound")
    if result.get("required_helper_kernel_set_digest") != _required_set_digest(
        config_hash, "helper", helper_names
    ):
        raise S10R4Error("CHANGES_REQUIRED: helper set digest is not config-bound")
    return {**result, "reconciled_artifact_inventory": list(inventory)}


def classify_native_membership(result: Mapping[str, Any]) -> str:
    assembly = result.get("required_assembly_kernels")
    helpers = result.get("required_helper_kernels")
    inventory = result.get("reconciled_artifact_inventory")
    if not isinstance(assembly, list) or not assembly or not isinstance(helpers, list):
        raise S10R4Error("CHANGES_REQUIRED: required assembly/helper set is incomplete")
    reconciled = reconcile_native_artifacts(result, inventory, result.get("input_config_hash"))
    assembly = reconciled["required_assembly_kernels"]
    for item in assembly:
        if (
            item.get("terminal_native_result") is not True
            or not isinstance(item.get("processKernelSource_result_code"), int)
            or isinstance(item.get("processKernelSource_result_code"), bool)
            or not isinstance(item.get("overflowed_resources"), int)
            or isinstance(item.get("overflowed_resources"), bool)
            or item.get("err") is not (item.get("processKernelSource_result_code") != 0)
        ):
            raise S10R4Error("CHANGES_REQUIRED: partial assembly-kernel native result")
    returncode = result.get("process_returncode")
    present = result.get("post_filter_solution_present")
    native_errors = [item.get("err") for item in assembly]
    if returncode == 0 and present is True and all(error is False for error in native_errors):
        return "native_membership_success"
    if returncode == 23 and present is False and any(error is True for error in native_errors):
        return "ordinary_all_solutions_removed_attrition"
    raise S10R4Error("CHANGES_REQUIRED: result does not match the structured native-membership oracle")


PASS_NEUTRAL_FIELDS = (
    "classification_kind",
    "ordered_failed_kernel_names",
    "ordered_native_result_error_codes",
    "ordered_processKernelSource_result_codes",
    "post_filter_solution_membership",
    "process_returncode",
    "required_assembly_kernel_set_digest",
    "required_helper_kernel_set_digest",
)


def stable_classify(pass_a: Mapping[str, Any], pass_b: Mapping[str, Any]) -> str:
    left = classify_native_membership(pass_a)
    right = classify_native_membership(pass_b)
    if left != right:
        raise S10R4Error("CHANGES_REQUIRED: census pass success/failure discordance")
    if left == "native_membership_success":
        for field in (
            "required_assembly_kernel_set_digest",
            "required_helper_kernel_set_digest",
            "post_filter_solution_identity",
        ):
            if pass_a.get(field) != pass_b.get(field):
                raise S10R4Error(f"CHANGES_REQUIRED: survivor pass identity mismatch: {field}")
        return "operational_codegen_witnessed"
    for field in PASS_NEUTRAL_FIELDS:
        if pass_a.get(field) != pass_b.get(field):
            raise S10R4Error(f"CHANGES_REQUIRED: attrition signature mismatch: {field}")
    return "stable_operational_attrition"


def census_request(
    pass_id: str,
    registry_row: Mapping[str, Any],
    cwd: Path,
    environment: Mapping[str, str],
    effective_lock_digest: str,
) -> dict[str, Any]:
    if pass_id not in ("A", "B"):
        raise S10R4Error("census pass must be A or B")
    if len(effective_lock_digest) != 64 or any(ch not in "0123456789abcdef" for ch in effective_lock_digest):
        raise S10R4Error("census request effective-lock digest is malformed")
    request = {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        "document_kind": "census_request",
        "pass_id": pass_id,
        "registry_index": registry_row["registry_index"],
        "config_hash": registry_row["config_hash"],
        "raw_config": registry_row["raw_config"],
        "cwd": cwd.resolve(strict=False).as_posix(),
        "environment": dict(environment),
        "effective_lock_digest": effective_lock_digest,
        "timeout_s": 7200,
        "actual_yaml": "/src/rocm-libraries/study_docs/research/ductile-origami-warmstart/protocol/v1/inputs/s10-generated.yaml",
        "actual_yaml_sha256": "faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36",
        "artifact_root": (cwd / "artifacts").resolve(strict=False).as_posix(),
        "source_commit": DUCTILE_COMMIT,
    }
    request["input_digest"] = canonical_sha256(request)
    validate_document_schema(request)
    return request


def _merged_raw_config(raw_config: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key, value in raw_config.items():
        if key.startswith("group_"):
            if not isinstance(value, dict):
                raise S10R4Error(f"grouped configuration is not an object: {key}")
            for nested_key, nested_value in value.items():
                merged[nested_key] = nested_value
        else:
            merged[key] = value
    if not merged or any(key.startswith("group_") for key in merged):
        raise S10R4Error("singleton configuration expansion is incomplete")
    return merged


def singleton_yaml_document(
    base: Mapping[str, Any],
    raw_config: Mapping[str, Any],
    sizes: Sequence[Sequence[int]],
    *,
    correctness: bool,
) -> dict[str, Any]:
    """Mechanically reduce the committed YAML to one exact solution and sizes."""
    document = dict(base)
    problems = document.get("BenchmarkProblems")
    if not isinstance(problems, list) or len(problems) != 1 or not isinstance(problems[0], list) or len(problems[0]) != 2:
        raise S10R4Error("actual YAML BenchmarkProblems shape is not the frozen singleton source")
    problem_type = dict(problems[0][0])
    parameters = dict(problems[0][1])
    merged = _merged_raw_config(raw_config)
    parameters["ForkParameters"] = [{key: [value]} for key, value in merged.items()]
    parameters.pop("Groups", None)
    parameters["BenchmarkFinalParameters"] = [
        {"ProblemSizes": [{"Exact": list(size)} for size in sizes]},
        {"BiasTypeArgs": ["B"]},
    ]
    document["BenchmarkProblems"] = [[problem_type, parameters]]
    document["Backend"] = {"Name": "Exhaustive"}
    global_parameters = dict(document.get("GlobalParameters", {}))
    global_parameters.update(
        {
            "CpuThreads": 0,
            "KeepBuildTmp": True,
            "Device": 0,
            "NumElementsToValidate": 128 if correctness else 0,
            "ExitOnFails": 2 if correctness else 0,
            "NumWarmups": 321,
            "EnqueuesPerSync": 321,
            "MaxEnqueuesPerSync": 321,
        }
    )
    document["GlobalParameters"] = global_parameters
    return document


def _worker_artifact_inventory(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir():
        raise S10R4Error("worker artifact root is absent")
    records, _ = ordinary_file_records(root)
    return records


def _actual_census_backend(request: Mapping[str, Any]) -> dict[str, Any]:
    """Run the pinned normal workflow in-process and record its native boundaries."""
    yaml_path = Path(request["actual_yaml"])
    if raw_sha256(yaml_path) != request["actual_yaml_sha256"]:
        raise S10R4Error("census worker actual YAML identity mismatch")
    import yaml
    from Tensile import BenchmarkProblems
    from Tensile.Tensile import Tensile
    from Tensile.TensileCreateLibrary import Run
    from Tensile.SolutionStructs.Naming import getKeyNoInternalArgs

    artifact_root = Path(request["artifact_root"])
    artifact_root.mkdir(parents=True, exist_ok=False)
    config_hash = request.get("config_hash")
    if (
        not isinstance(config_hash, str)
        or len(config_hash) != 64
        or any(character not in "0123456789abcdef" for character in config_hash)
    ):
        raise S10R4Error("census backend config hash is malformed")
    base = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    singleton = singleton_yaml_document(base, request["raw_config"], ([256, 256, 1, 1024],), correctness=False)
    singleton_path = artifact_root / "singleton.yaml"
    atomic_write_bytes(singleton_path, yaml.safe_dump(singleton, sort_keys=False).encode("utf-8"))

    observed: dict[str, Any] = {
        "writeBenchmarkFiles_calls": 0,
        "writeSolutionsAndKernels_calls": 0,
        "required_assembly_kernels": [],
        "required_helper_kernels": [],
        "post_filter_solution_present": None,
        "post_filter_solution_identity": None,
        "processKernelSource_result_codes": [],
        "required_helper_declared_artifacts": [],
        "input_config_hash": config_hash,
    }
    original_benchmark = BenchmarkProblems.writeBenchmarkFiles
    original_write = Run.writeSolutionsAndKernels
    original_benchmark_write = BenchmarkProblems.writeSolutionsAndKernels
    original_process = Run.processKernelSource
    original_remove = Run.removeInvalidSolutionsAndKernels
    input_solution: Any = None
    output_path: Path | None = None
    helper_payloads: tuple[bytes, bytes] | None = None

    def relative_artifact(path: Path, payload: bytes) -> dict[str, Any]:
        try:
            relative = path.relative_to(artifact_root).as_posix()
        except ValueError as exc:
            raise S10R4Error("native artifact path escapes the census artifact root") from exc
        return _artifact_record(relative, payload)

    def materialize_observed_artifacts() -> None:
        """Preserve exact native-boundary payloads when filtering exits before writes."""
        if output_path is None or helper_payloads is None:
            return
        source_payload, header_payload = helper_payloads
        atomic_write_bytes(output_path / "Kernels.cpp", source_payload)
        atomic_write_bytes(output_path / "Kernels.h", header_payload)
        for row in observed["required_assembly_kernels"]:
            payload = row.pop("_artifact_payload", None)
            if payload is not None:
                expected = row["expected_artifact"]
                atomic_write_bytes(artifact_root / expected["relative_path"], payload)
        for row in observed["required_helper_kernels"]:
            for prefix in ("source", "header"):
                payload = row.pop(f"_{prefix}_payload", None)
                if payload is not None:
                    expected = row[f"{prefix}_artifact"]
                    atomic_write_bytes(artifact_root / expected["relative_path"], payload)

    def benchmark_wrapper(*args: Any, **kwargs: Any) -> Any:
        nonlocal input_solution
        observed["writeBenchmarkFiles_calls"] += 1
        solutions = args[1] if len(args) > 1 else kwargs["solutions"]
        if len(solutions) != 1:
            raise S10R4Error("census singleton resolved other than exactly one solution")
        input_solution = solutions[0]
        observed["resolved_solution"] = dict(input_solution._state)
        return original_benchmark(*args, **kwargs)

    def write_wrapper(*args: Any, **kwargs: Any) -> Any:
        nonlocal output_path, helper_payloads
        observed["writeSolutionsAndKernels_calls"] += 1
        output_path = Path(args[0] if args else kwargs["outputPath"])
        solutions = args[3]
        kernels = args[4]
        helpers = args[5]
        split_gsu = args[7]
        names = [getKeyNoInternalArgs(kernel, split_gsu) for kernel in kernels]
        if not names or len(names) != len(set(names)):
            raise S10R4Error("census required assembly set is empty or duplicated")
        observed["required_assembly_kernels"] = [
            {
                "name": name,
                "canonical_identity": _canonical_kernel_identity(config_hash, "assembly", name),
            }
            for name in sorted(names)
        ]
        helper_rows = []
        helper_sources: list[str] = []
        helper_headers: list[str] = []
        for helper in helpers:
            name = helper.getKernelName()
            source_error, source = helper.getSourceFileString()
            header = helper.getHeaderFileString()
            if source_error != 0 or not isinstance(source, str) or not source:
                raise S10R4Error("census required helper source is incomplete")
            if not isinstance(header, str) or not header:
                raise S10R4Error("census required helper header is incomplete")
            source_bytes = source.encode("utf-8")
            header_bytes = header.encode("utf-8")
            identity = _canonical_kernel_identity(config_hash, "helper", name)
            component_root = output_path / "required_helpers"
            helper_sources.append(source)
            helper_headers.append(header)
            helper_rows.append(
                {
                    "name": name,
                    "canonical_identity": identity,
                    "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
                    "source_size_bytes": len(source_bytes),
                    "source_artifact": relative_artifact(
                        component_root / f"{identity}.cpp", source_bytes
                    ),
                    "header_sha256": hashlib.sha256(header_bytes).hexdigest(),
                    "header_size_bytes": len(header_bytes),
                    "header_artifact": relative_artifact(
                        component_root / f"{identity}.h", header_bytes
                    ),
                    "_source_payload": source_bytes,
                    "_header_payload": header_bytes,
                }
            )
        observed["required_helper_kernels"] = sorted(helper_rows, key=lambda row: row["name"])
        source_payload = (Run.CHeader + '#include "Kernels.h"\n' + "".join(helper_sources)).encode("utf-8")
        header_payload = (
            Run.CHeader
            + "#pragma once\n"
            + "#include <hip/hip_runtime.h>\n"
            + "#include <hip/hip_ext.h>\n\n"
            + '#include "KernelHeader.h"\n\n'
            + "".join(helper_headers)
        ).encode("utf-8")
        helper_payloads = (source_payload, header_payload)
        observed["required_helper_declared_artifacts"] = [
            relative_artifact(output_path / "Kernels.cpp", source_payload),
            relative_artifact(output_path / "Kernels.h", header_payload),
        ]
        return original_benchmark_write(*args, **kwargs)

    def process_wrapper(*args: Any, **kwargs: Any) -> Any:
        result = original_process(*args, **kwargs)
        writer = args[0] if args else kwargs["kernelWriterAssembly"]
        process_code = int(result.err)
        overflow_code = int(writer.states.overflowedResources)
        observed["processKernelSource_result_codes"].append(process_code)
        if not isinstance(result.src, str) or not result.src:
            raise S10R4Error("census assembly source payload is absent")
        source_payload = result.src.encode("utf-8")
        if output_path is None:
            raise S10R4Error("census assembly result preceded required-set binding")
        assembly_path = output_path / "build_tmp" / output_path.stem.upper() / "assembly" / f"{result.name}.s"
        for row in observed["required_assembly_kernels"]:
            if row["name"] == result.name:
                row.update(
                    {
                        "terminal_native_result": True,
                        "err": process_code != 0,
                        "processKernelSource_result_code": process_code,
                        "overflowed_resources": overflow_code,
                        "expected_artifact": relative_artifact(assembly_path, source_payload),
                        "_artifact_payload": source_payload,
                    }
                )
        return result

    def remove_wrapper(*args: Any, **kwargs: Any) -> Any:
        result = original_remove(*args, **kwargs)
        solutions = args[2]
        observed["post_filter_solution_present"] = input_solution in solutions
        if input_solution in solutions:
            observed["post_filter_solution_identity"] = canonical_sha256(input_solution._state)
        return result

    BenchmarkProblems.writeBenchmarkFiles = benchmark_wrapper
    BenchmarkProblems.writeSolutionsAndKernels = write_wrapper
    Run.writeSolutionsAndKernels = write_wrapper
    Run.processKernelSource = process_wrapper
    Run.removeInvalidSolutionsAndKernels = remove_wrapper
    try:
        user_args = [
            singleton_path.as_posix(),
            artifact_root.as_posix(),
            "--build-only",
            "--device", "0",
            "--gpu-targets", "gfx942",
            "--cxx-compiler", "/opt/rocm/bin/amdclang++",
            "--c-compiler", "/opt/rocm/bin/amdclang++",
            "--assembler", "/opt/rocm/bin/amdclang++",
            "--offload-bundler", "/opt/rocm/lib/llvm/bin/clang-offload-bundler",
        ]
        try:
            Tensile(user_args)
        except SystemExit as exc:
            complete_resource_attrition = (
                bool(observed["required_assembly_kernels"])
                and all(row.get("terminal_native_result") is True for row in observed["required_assembly_kernels"])
                and any(row.get("err") is True for row in observed["required_assembly_kernels"])
                and bool(observed["required_helper_kernels"])
                and bool(observed["required_helper_declared_artifacts"])
            )
            if exc.code not in (0, None) and not complete_resource_attrition:
                raise
            if complete_resource_attrition:
                observed["post_filter_solution_present"] = False
                observed["post_filter_solution_identity"] = None
    finally:
        BenchmarkProblems.writeBenchmarkFiles = original_benchmark
        BenchmarkProblems.writeSolutionsAndKernels = original_benchmark_write
        Run.writeSolutionsAndKernels = original_write
        Run.processKernelSource = original_process
        Run.removeInvalidSolutionsAndKernels = original_remove

    assembly = observed["required_assembly_kernels"]
    if any(row.get("terminal_native_result") is not True for row in assembly):
        raise S10R4Error("census worker lacks a terminal native result")
    materialize_observed_artifacts()
    present = observed["post_filter_solution_present"]
    worker_code = 0 if present is True and all(not row["err"] for row in assembly) else 23
    result: dict[str, Any] = {
        **observed,
        "classification_kind": "native_membership_success" if worker_code == 0 else "ordinary_all_solutions_removed_attrition",
        "ordered_failed_kernel_names": [row["name"] for row in assembly if row["err"]],
        "ordered_native_result_error_codes": [row["overflowed_resources"] for row in assembly],
        "ordered_processKernelSource_result_codes": observed["processKernelSource_result_codes"],
        "post_filter_solution_membership": present,
        "process_returncode": worker_code,
        "required_assembly_kernel_set_digest": _required_set_digest(
            config_hash, "assembly", [row["name"] for row in assembly]
        ),
        "required_helper_kernel_set_digest": _required_set_digest(
            config_hash, "helper", [row["name"] for row in observed["required_helper_kernels"]]
        ),
    }
    for row in assembly:
        row.pop("_artifact_payload", None)
    for row in observed["required_helper_kernels"]:
        row.pop("_source_payload", None)
        row.pop("_header_payload", None)
    return result


def execute_census_worker(
    request: Mapping[str, Any],
    result_path: Path,
    *,
    backend: Any = None,
) -> int:
    expected = {
        "schema_version", "checkpoint_id", "document_kind", "pass_id", "registry_index",
        "config_hash", "raw_config", "cwd", "environment", "timeout_s", "actual_yaml",
        "actual_yaml_sha256", "artifact_root", "source_commit", "effective_lock_digest", "input_digest",
    }
    if set(request) != expected or request.get("document_kind") != "census_request":
        raise S10R4Error("census worker request exact field set mismatch")
    if canonical_sha256({key: value for key, value in request.items() if key != "input_digest"}) != request["input_digest"]:
        raise S10R4Error("census worker request digest mismatch")
    if Path.cwd().resolve().as_posix() != request["cwd"] or result_path.parent.resolve() != Path(request["cwd"]):
        raise S10R4Error("census worker cwd/result association mismatch")
    worker = backend or _actual_census_backend
    native = worker(request)
    inventory = _worker_artifact_inventory(Path(request["artifact_root"]))
    native = reconcile_native_artifacts(native, inventory, request["config_hash"])
    classification = classify_native_membership(native)
    document = {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        "document_kind": "census_child",
        "pass_id": request["pass_id"],
        "registry_index": request["registry_index"],
        "config_hash": request["config_hash"],
        "input_digest": request["input_digest"],
        "cwd": request["cwd"],
        "argv": materialize_command_template("census_child", {"child_root": request["cwd"]}),
        "environment": request["environment"],
        "effective_lock_digest": request["effective_lock_digest"],
        "outputs": {**native, "stable_input_classification": classification},
        "artifact_inventory": inventory,
    }
    from .ledger import finalize_child

    finalize_child(
        result_path,
        document,
        {
            "document_kind": "census_child", "pass_id": request["pass_id"],
            "registry_index": request["registry_index"], "config_hash": request["config_hash"],
        },
    )
    validate_document_schema(load_json(result_path))
    return int(native["process_returncode"])
