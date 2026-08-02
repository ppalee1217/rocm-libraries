# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Append-only, no-replace child artifact storage and completeness scans."""

from __future__ import annotations

import fcntl
import math
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from .contract import (
    S10R4Error,
    atomic_write_json,
    canonical_json,
    canonical_sha256,
    load_json,
    materialize_command_template,
    ordinary_file_records,
    raw_sha256,
    seal_digest,
    validate_document_schema,
    validate_sealed_digest,
)


PROCESS_COMPLETION_FIELDS = {
    "schema_version", "checkpoint_id", "document_kind", "command_id", "identity",
    "argv", "cwd", "environment", "process_returncode", "stdout", "stderr",
    "worker_result", "artifact_projection_sha256", "resource_observation",
    "document_digest",
}
PROCESS_FILE_FIELDS = {"path", "mode", "size_bytes", "sha256"}
PROCESS_RESULT_FIELDS = {
    "path", "mode", "size_bytes", "raw_sha256", "canonical_sha256", "completion_digest",
}
PROCESS_RESOURCE_FIELDS = {
    "wall_seconds", "child_cpu_seconds", "new_child_tree_bytes", "measurement_semantics",
}


def _ordinary_process_file(path: Path, root: Path) -> dict[str, Any]:
    try:
        info = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise S10R4Error(f"process completion input is absent or unreadable: {path}") from exc
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise S10R4Error(f"process completion input is not one ordinary file: {path}")
    try:
        relative = path.resolve(strict=True).relative_to(root.resolve(strict=True)).as_posix()
    except ValueError as exc:
        raise S10R4Error(f"process completion input escapes child root: {path}") from exc
    return {
        "path": relative,
        "mode": stat.S_IMODE(info.st_mode),
        "size_bytes": info.st_size,
        "sha256": raw_sha256(path),
    }


def _worker_result_record(path: Path, root: Path) -> dict[str, Any]:
    record = _ordinary_process_file(path, root)
    document = load_json(path)
    validate_document_schema(document)
    validate_child(document, {})
    return {
        "path": record["path"],
        "mode": record["mode"],
        "size_bytes": record["size_bytes"],
        "raw_sha256": record["sha256"],
        "canonical_sha256": canonical_sha256(document),
        "completion_digest": document["completion_digest"],
    }


def _validate_resource_observation(value: Mapping[str, Any]) -> None:
    if set(value) != PROCESS_RESOURCE_FIELDS:
        raise S10R4Error("process completion resource observation fields mismatch")
    for field in ("wall_seconds", "child_cpu_seconds"):
        observed = value[field]
        if (
            not isinstance(observed, (int, float))
            or isinstance(observed, bool)
            or not math.isfinite(observed)
            or observed < 0
        ):
            raise S10R4Error(f"process completion resource observation has invalid {field}")
    storage = value["new_child_tree_bytes"]
    if not isinstance(storage, int) or isinstance(storage, bool) or storage < 0:
        raise S10R4Error("process completion resource observation has invalid child-tree bytes")
    if value["measurement_semantics"] != "parent_monotonic_wall_rusage_children_and_child_tree_bytes":
        raise S10R4Error("process completion resource measurement semantics mismatch")


def validate_process_completion(
    path: Path,
    *,
    command_id: str,
    identity: Mapping[str, Any],
    argv: list[str],
    cwd: Path,
    environment: Mapping[str, str],
    allowed_returncodes: Iterable[int],
) -> dict[str, Any]:
    document = load_json(path)
    validate_document_schema(document)
    validate_sealed_digest(document)
    if set(document) != PROCESS_COMPLETION_FIELDS:
        raise S10R4Error("process completion fields mismatch")
    if (
        document["schema_version"] != 1
        or document["checkpoint_id"] != "S10R4"
        or document["document_kind"] != "process_completion"
        or document["command_id"] != command_id
        or document["identity"] != dict(identity)
        or document["argv"] != argv
        or document["cwd"] != cwd.resolve(strict=True).as_posix()
        or document["environment"] != dict(environment)
        or document["process_returncode"] not in set(allowed_returncodes)
    ):
        raise S10R4Error("process completion command/identity/runtime binding mismatch")
    for name in ("stdout", "stderr"):
        if set(document[name]) != PROCESS_FILE_FIELDS:
            raise S10R4Error(f"process completion {name} record fields mismatch")
        expected = _ordinary_process_file(cwd / f"{name}.log", cwd)
        if document[name] != expected:
            raise S10R4Error(f"process completion {name} record drift")
    if set(document["worker_result"]) != PROCESS_RESULT_FIELDS:
        raise S10R4Error("process completion worker-result fields mismatch")
    result_record = _worker_result_record(cwd / "result.json", cwd)
    if document["worker_result"] != result_record:
        raise S10R4Error("process completion worker-result drift")
    result = load_json(cwd / "result.json")
    result_returncode_field = {
        "census_child": "process_returncode",
        "mapping_child": "worker_returncode",
    }.get(command_id)
    if (
        result_returncode_field is None
        or result.get("outputs", {}).get(result_returncode_field)
        != document["process_returncode"]
    ):
        raise S10R4Error("process completion result return-code binding mismatch")
    if document["artifact_projection_sha256"] != canonical_sha256(result.get("artifact_inventory")):
        raise S10R4Error("process completion artifact projection drift")
    _validate_resource_observation(document["resource_observation"])
    return document


def finalize_process_completion(
    path: Path,
    *,
    command_id: str,
    identity: Mapping[str, Any],
    argv: list[str],
    cwd: Path,
    environment: Mapping[str, str],
    process_returncode: int,
    allowed_returncodes: Iterable[int],
    resource_observation: Mapping[str, Any],
) -> dict[str, Any]:
    if path.exists():
        raise S10R4Error(f"refusing to replace finalized process completion: {path}")
    allowed = tuple(allowed_returncodes)
    if process_returncode not in allowed:
        raise S10R4Error("process completion return code is outside its allowlist")
    stdout = _ordinary_process_file(cwd / "stdout.log", cwd)
    stderr = _ordinary_process_file(cwd / "stderr.log", cwd)
    worker_result = _worker_result_record(cwd / "result.json", cwd)
    result = load_json(cwd / "result.json")
    _validate_resource_observation(resource_observation)
    result_returncode_field = {
        "census_child": "process_returncode",
        "mapping_child": "worker_returncode",
    }.get(command_id)
    if (
        result_returncode_field is None
        or result.get("outputs", {}).get(result_returncode_field) != process_returncode
    ):
        raise S10R4Error("process completion result return-code binding mismatch")
    document = seal_digest(
        {
            "schema_version": 1,
            "checkpoint_id": "S10R4",
            "document_kind": "process_completion",
            "command_id": command_id,
            "identity": dict(identity),
            "argv": list(argv),
            "cwd": cwd.resolve(strict=True).as_posix(),
            "environment": dict(environment),
            "process_returncode": process_returncode,
            "stdout": stdout,
            "stderr": stderr,
            "worker_result": worker_result,
            "artifact_projection_sha256": canonical_sha256(result.get("artifact_inventory")),
            "resource_observation": dict(resource_observation),
        }
    )
    validate_document_schema(document)
    atomic_write_json(path, document)
    return validate_process_completion(
        path,
        command_id=command_id,
        identity=identity,
        argv=argv,
        cwd=cwd,
        environment=environment,
        allowed_returncodes=allowed,
    )


@contextmanager
def exclusive_scope(scope: Path) -> Iterator[None]:
    scope.mkdir(parents=True, exist_ok=True)
    lock_path = scope / ".s10r4-writer.lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise S10R4Error(f"S10R4 scope already has a writer: {scope}") from exc
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def completion_digest(document: Mapping[str, Any]) -> str:
    projected = {key: value for key, value in document.items() if key != "completion_digest"}
    return canonical_sha256(projected)


def validate_child(document: Mapping[str, Any], expected_identity: Mapping[str, Any]) -> None:
    if document.get("schema_version") != 1 or document.get("checkpoint_id") != "S10R4":
        raise S10R4Error("child schema/checkpoint identity mismatch")
    for key, value in expected_identity.items():
        if document.get(key) != value:
            raise S10R4Error(f"child expected identity mismatch: {key}")
    if document.get("completion_digest") != completion_digest(document):
        raise S10R4Error("child completion digest mismatch")


def finalize_child(path: Path, document: Mapping[str, Any], expected_identity: Mapping[str, Any]) -> str:
    child = dict(document)
    child["completion_digest"] = "0" * 64
    child["completion_digest"] = completion_digest(child)
    validate_child(child, expected_identity)
    payload = canonical_json(child, newline=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_bytes()
        if existing != payload:
            raise S10R4Error(f"terminal child collision: {path}")
        validate_child(load_json(path), expected_identity)
        return child["completion_digest"]
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".partial", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise S10R4Error(f"terminal child appeared during finalization: {path}")
        os.link(temporary, path)
        temporary.unlink()
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()
    return child["completion_digest"]


def scan_exact_children(
    scope: Path,
    expected: Iterable[tuple[Path, Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    expected_rows = list(expected)
    allowed = {path.resolve(strict=False) for path, _ in expected_rows}
    observed: list[dict[str, Any]] = []
    for path, identity in expected_rows:
        if not path.exists():
            raise S10R4Error(f"missing terminal child: {path}")
        info = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise S10R4Error(f"terminal child is not an unambiguous ordinary file: {path}")
        document = load_json(path)
        validate_child(document, identity)
        request_path = path.parent / "request.json"
        child_kind = document.get("document_kind")
        if child_kind in ("census_child", "mapping_attempt") and not request_path.is_file():
            raise S10R4Error(f"terminal process child lacks its request: {path}")
        if request_path.exists():
            request = load_json(request_path)
            request_digest = request.get("input_digest")
            if (
                not isinstance(request_digest, str)
                or canonical_sha256({key: value for key, value in request.items() if key != "input_digest"}) != request_digest
                or document.get("input_digest") != request_digest
                or request.get("cwd") != path.parent.resolve().as_posix()
            ):
                raise S10R4Error(f"terminal child request association mismatch: {path}")
            allowed.add(request_path.resolve(strict=True))
            if child_kind in ("census_child", "mapping_attempt"):
                completion_path = path.parent / "process-completion.json"
                if child_kind == "census_child":
                    command_id = "census_child"
                    completion_identity = {
                        key: request[key]
                        for key in (
                            "pass_id", "registry_index", "config_hash", "input_digest",
                            "effective_lock_digest",
                        )
                    }
                    allowed_returncodes = (0, 23)
                    substitutions = {"child_root": path.parent.resolve(strict=True).as_posix()}
                else:
                    command_id = "mapping_child"
                    completion_identity = {
                        key: request[key]
                        for key in ("pass_id", "attempt", "input_digest", "effective_lock_digest")
                    }
                    allowed_returncodes = (0, 23, 24)
                    substitutions = {"attempt_root": path.parent.resolve(strict=True).as_posix()}
                child_argv = materialize_command_template(command_id, substitutions)
                if not completion_path.is_file():
                    raise S10R4Error(f"terminal process child lacks its completion: {path}")
                if (
                    document.get("cwd") != request["cwd"]
                    or document.get("argv") != child_argv
                    or document.get("environment") != request["environment"]
                    or document.get("effective_lock_digest")
                    != request["effective_lock_digest"]
                ):
                    raise S10R4Error(f"terminal child request/runtime binding mismatch: {path}")
                if child_kind == "census_child" and (
                    request.get("pass_id") != document.get("pass_id")
                    or request.get("registry_index") != document.get("registry_index")
                    or request.get("config_hash") != document.get("config_hash")
                    or canonical_sha256(request.get("raw_config")) != request.get("config_hash")
                ):
                    raise S10R4Error(f"census request/config association mismatch: {path}")
                validate_process_completion(
                    completion_path,
                    command_id=command_id,
                    identity=completion_identity,
                    argv=child_argv,
                    cwd=path.parent,
                    environment=request["environment"],
                    allowed_returncodes=allowed_returncodes,
                )
                for terminal_name in (
                    "process-completion.json", "stdout.log", "stderr.log",
                ):
                    allowed.add((path.parent / terminal_name).resolve(strict=True))
            artifact_root_value = request.get("artifact_root")
            if child_kind == "mapping_attempt":
                artifact_root_value = (path.parent / "rows").as_posix()
            if artifact_root_value is not None:
                artifact_root = Path(artifact_root_value)
                if not artifact_root.exists() and document.get("artifact_inventory") == []:
                    artifact_root = None
                elif not artifact_root.exists():
                    raise S10R4Error(f"terminal child artifact root is missing: {path}")
            else:
                artifact_root = None
            if artifact_root is not None:
                artifact_root = artifact_root.resolve(strict=True)
                try:
                    artifact_root.relative_to(path.parent.resolve(strict=True))
                except ValueError as exc:
                    raise S10R4Error(f"terminal child artifact root escapes child: {path}") from exc
                records, _ = ordinary_file_records(artifact_root)
                if records != document.get("artifact_inventory"):
                    raise S10R4Error(f"terminal child artifact inventory drift: {path}")
                if (
                    child_kind == "census_child"
                    and document.get("outputs", {}).get("reconciled_artifact_inventory") != records
                ):
                    raise S10R4Error(
                        f"terminal census native/artifact reconciliation drift: {path}"
                    )
                for record in records:
                    allowed.add((artifact_root / record["relative_path"]).resolve(strict=True))
        observed.append(document)
    for root, directories, files in os.walk(scope, followlinks=False):
        for directory in directories:
            path = Path(root) / directory
            if path.is_symlink():
                raise S10R4Error(f"symlink in formal child scope: {path}")
        for filename in files:
            path = Path(root) / filename
            if filename == ".s10r4-writer.lock":
                continue
            if filename in ("stdout.log", "stderr.log"):
                request_path = path.parent / "request.json"
                if request_path.is_file():
                    request_kind = load_json(request_path).get("document_kind")
                    if request_kind not in ("census_request", "mapping_request"):
                        continue
            if path.resolve(strict=False) not in allowed:
                raise S10R4Error(f"unknown/partial/colliding child artifact: {path}")
    return observed


def census_expectations(scope: Path, pass_id: str, registry: Iterable[Mapping[str, Any]]) -> list[tuple[Path, dict[str, Any]]]:
    if pass_id not in ("A", "B"):
        raise S10R4Error("census pass must be A or B")
    result = []
    for row in registry:
        index = int(row["registry_index"])
        config_hash = str(row["config_hash"])
        path = scope / f"pass-{pass_id}/{index:03d}-{config_hash}/result.json"
        result.append((path, {"document_kind": "census_child", "pass_id": pass_id, "registry_index": index, "config_hash": config_hash}))
    return result


def correctness_expectations(scope: Path, anchors: Iterable[int], sizes: Iterable[str]) -> list[tuple[Path, dict[str, Any]]]:
    result = []
    for anchor in anchors:
        for size_id in sizes:
            path = scope / f"{anchor:02d}-{size_id}/attempt-01/attempt.json"
            result.append((path, {"document_kind": "correctness_attempt", "anchor_index": anchor, "size_id": size_id, "attempt": 1}))
    return result
