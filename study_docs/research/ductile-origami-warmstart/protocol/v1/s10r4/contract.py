# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Strict, outcome-blind contract and artifact primitives for S10R4."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import string
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

import yaml


BASE_PROTOCOL_ID = "S10R4-A47-EXACT-FRAME-OPERATIONAL-ENTRY-V1"
PROTOCOL_ID = "S10R4-A48-EXACT-FRAME-BINDING-02"
CONTRACT_RAW_SHA256 = "be79e72f0eb7d54a6457eb5fabcdcd64b67523966300597efb0877e0fb82eeba"
SUPPLEMENT_RAW_SHA256 = "5954c1df2684efa19682ec361b978239843218ab9e21d410be13ef9801708e65"
AMENDMENT_RAW_SHA256 = "99caae254aa6e062241d55a9b37a8414cfbdc645593dc28e44fb0f5ae96c0fde"
AMENDMENT_CANONICAL_SHA256 = "515bc700887bf0d6b2da0c58e2e90e6c07a1cd780b1382d65af498083d52b7a8"
REPO_ROOT = Path(__file__).resolve().parents[6]
PROTOCOL_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROTOCOL_ROOT / "s10r4-stage1-exact-frame-entry-contract.yaml"
SUPPLEMENT_PATH = PROTOCOL_ROOT / "s10r4-stage1-exact-frame-entry-binding-02-contract.yaml"
AMENDMENT_PATH = (
    PROTOCOL_ROOT
    / "s10r4-stage1-exact-frame-entry-binding-02-prebinding-recovery-contract.yaml"
)
SCHEMA_PATH = PROTOCOL_ROOT / "schemas/s10r4-entry.schema.json"
FORBIDDEN_BINDING_01_RUN_PREFIX = "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame/"
BINDING_02_RUN_PREFIX = "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/"
BINDING_02_LOCK_PATH = (
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/"
    "s10r4-stage1-exact-frame-entry-binding-02-lock.json"
)


class S10R4Error(RuntimeError):
    """A fail-closed S10R4 validation failure."""


def _reject_constant(value: str) -> None:
    raise S10R4Error(f"non-finite JSON number is forbidden: {value}")


def _pairs_no_duplicates(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if not isinstance(key, str):
            raise S10R4Error("JSON object key is not a string")
        if key in result:
            raise S10R4Error(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json_bytes(data: bytes, *, require_object: bool = True) -> Any:
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise S10R4Error(f"invalid strict JSON: {exc}") from exc
    if require_object and not isinstance(value, dict):
        raise S10R4Error("JSON root must be an object")
    reject_nonfinite(value)
    return value


class _UniqueSafeLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: _UniqueSafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict[str, Any]:
    loader.flatten_mapping(node)
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise S10R4Error("YAML mapping key is not a string")
        if key in result:
            raise S10R4Error(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def strict_yaml_bytes(data: bytes) -> dict[str, Any]:
    try:
        value = yaml.load(data.decode("utf-8"), Loader=_UniqueSafeLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise S10R4Error(f"invalid strict YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise S10R4Error("YAML root must be an object")
    reject_nonfinite(value)
    return value


def reject_nonfinite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise S10R4Error("non-finite number is forbidden")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise S10R4Error("mapping key is not a string")
            reject_nonfinite(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            reject_nonfinite(child)


def canonical_json(data: Any, *, newline: bool = False) -> bytes:
    reject_nonfinite(data)
    encoded = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return encoded + (b"\n" if newline else b"")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(data: Any) -> str:
    return sha256_bytes(canonical_json(data))


def load_json(path: Path, *, require_object: bool = True) -> Any:
    return strict_json_bytes(path.read_bytes(), require_object=require_object)


def load_base_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    raw = path.read_bytes()
    if sha256_bytes(raw) != CONTRACT_RAW_SHA256:
        raise S10R4Error("S10R4 frozen contract raw SHA-256 mismatch")
    contract = strict_yaml_bytes(raw)
    if contract.get("contract_id") != BASE_PROTOCOL_ID:
        raise S10R4Error("S10R4 base contract identity mismatch")
    if contract.get("scientific_outcome") != "not_evaluated" or contract.get("edge") is not None:
        raise S10R4Error("preimplementation contract contains an outcome or edge")
    return contract


SUPPLEMENT_KEYS = {
    "schema_version", "document_kind", "checkpoint_id", "binding_id", "contract_id",
    "payload_state", "scientific_outcome", "edge", "composition", "authority",
    "workflow_authority", "binding_01_retirement", "identity_replacements",
    "canonical_governance_paths", "binding_run_root_replacement",
    "prelabel_and_raw_replacements", "implementation_repairs", "phase1_seal",
    "effective_lock_required_supplement_bindings", "history_preserving_retirement",
    "phase2_seal", "scientific_invariants", "resources", "outcome_and_closeout",
}

AMENDMENT_KEYS = {
    "schema_version", "document_kind", "checkpoint_id", "amendment_id", "binding_id",
    "execution_tranche", "payload_state", "scientific_outcome", "edge", "authority",
    "trigger", "retired_prebinding_attempt", "successor_prebinding_ledger",
    "resource_projection_repair", "implementation_authority", "required_regressions",
    "scientific_invariants", "review_and_seal", "effective_lock_required_amendment_bindings",
}


def load_contract_supplement(path: Path = SUPPLEMENT_PATH) -> dict[str, Any]:
    raw = path.read_bytes()
    if sha256_bytes(raw) != SUPPLEMENT_RAW_SHA256:
        raise S10R4Error("S10R4 binding-02 supplement raw SHA-256 mismatch")
    supplement = strict_yaml_bytes(raw)
    require_exact_keys(supplement, SUPPLEMENT_KEYS, where="binding-02 supplement")
    if (
        supplement.get("schema_version") != 1
        or supplement.get("document_kind") != "s10r4_binding_recovery_contract_supplement"
        or supplement.get("checkpoint_id") != "S10R4"
        or supplement.get("binding_id") != "binding-02"
        or supplement.get("contract_id") != PROTOCOL_ID
        or supplement.get("scientific_outcome") != "not_evaluated"
        or supplement.get("edge") is not None
    ):
        raise S10R4Error("S10R4 binding-02 supplement identity mismatch")
    replacements = supplement["identity_replacements"]
    require_exact_keys(
        replacements,
        {
            "authority_commit_oid", "authority_amendment", "execution_tranche", "run_root",
            "contract_supplement_path", "effective_lock_path", "plan_root", "closure_root",
        },
        where="binding-02 identity replacements",
    )
    expected = {
        "authority_commit_oid": "37c846e5b0edc182fd84432da3596090dbf3ee15",
        "authority_amendment": "A48",
        "execution_tranche": "T-S10R4-B02",
        "run_root": BINDING_02_RUN_PREFIX.removesuffix("/"),
        "contract_supplement_path": SUPPLEMENT_PATH.relative_to(REPO_ROOT).as_posix(),
        "effective_lock_path": BINDING_02_LOCK_PATH,
        "plan_root": BINDING_02_RUN_PREFIX + "gates/s10r4",
        "closure_root": BINDING_02_RUN_PREFIX + "closure",
    }
    if replacements != expected:
        raise S10R4Error("unknown or incomplete binding-02 identity replacement")
    replacement = supplement["binding_run_root_replacement"]
    if (
        replacement.get("base_prefix") != FORBIDDEN_BINDING_01_RUN_PREFIX
        or replacement.get("binding_02_prefix") != BINDING_02_RUN_PREFIX
        or replacement.get("applies_to_every_base_contract_path_under_prefix") is not True
        or replacement.get("binding_02_composed_runtime_path_with_base_prefix") != "forbidden"
    ):
        raise S10R4Error("binding-02 run-root replacement is malformed")
    composition = supplement["composition"]
    if (
        composition.get("base_contract", {}).get("path") != CONTRACT_PATH.relative_to(REPO_ROOT).as_posix()
        or composition.get("base_contract", {}).get("raw_sha256") != CONTRACT_RAW_SHA256
        or composition.get("base_contract", {}).get("phase1_commit_oid")
        != "9e10067d6ea7ae6b979cf99d97ebee007d1ceec6"
        or composition.get("unknown_replacement") != "forbidden"
        or composition.get("scientific_field_replacement") != "forbidden"
        or composition.get("original_contract_mutation") != "forbidden"
        or composition.get("supplement_alias_or_fallback") != "forbidden"
    ):
        raise S10R4Error("binding-02 composition authority mismatch")
    return supplement


def load_prebinding_recovery_amendment(path: Path = AMENDMENT_PATH) -> dict[str, Any]:
    """Load the sole committed binding-02 prebinding-recovery amendment."""
    if path != AMENDMENT_PATH:
        raise S10R4Error("prebinding-recovery amendment aliases or fallbacks are forbidden")
    raw = path.read_bytes()
    if sha256_bytes(raw) != AMENDMENT_RAW_SHA256:
        raise S10R4Error("S10R4 prebinding-recovery amendment raw SHA-256 mismatch")
    amendment = strict_yaml_bytes(raw)
    require_exact_keys(amendment, AMENDMENT_KEYS, where="prebinding-recovery amendment")
    if (
        amendment.get("schema_version") != 1
        or amendment.get("document_kind")
        != "s10r4_binding_02_prebinding_operational_recovery_amendment"
        or amendment.get("checkpoint_id") != "S10R4"
        or amendment.get("amendment_id") != "S10R4-A49-B02-PREBINDING-RECOVERY-V1"
        or amendment.get("binding_id") != "binding-02"
        or amendment.get("execution_tranche") != "T-S10R4-B02"
        or amendment.get("scientific_outcome") != "not_evaluated"
        or amendment.get("edge") is not None
        or canonical_sha256(amendment) != AMENDMENT_CANONICAL_SHA256
    ):
        raise S10R4Error("S10R4 prebinding-recovery amendment identity mismatch")
    return amendment


def _replace_binding_descendants(value: Any, *, old_lock: str) -> Any:
    if isinstance(value, dict):
        return {key: _replace_binding_descendants(child, old_lock=old_lock) for key, child in value.items()}
    if isinstance(value, list):
        return [_replace_binding_descendants(child, old_lock=old_lock) for child in value]
    if isinstance(value, str):
        replaced = value.replace(FORBIDDEN_BINDING_01_RUN_PREFIX, BINDING_02_RUN_PREFIX)
        if replaced == old_lock:
            replaced = BINDING_02_LOCK_PATH
        return replaced
    return value


def _assert_composed_scientific_identity(base: Mapping[str, Any], composed: Mapping[str, Any]) -> None:
    scientific_composed = dict(composed)
    if "binding_02_operational_inputs" not in scientific_composed:
        raise S10R4Error("composed contract lacks binding-02 operational inputs")
    scientific_composed.pop("binding_02_operational_inputs")
    restored = _replace_binding_descendants(scientific_composed, old_lock=BINDING_02_LOCK_PATH)
    restored["contract_id"] = BASE_PROTOCOL_ID
    restored_identity = restored["identity"]
    base_identity = base["identity"]
    restored_identity["execution_tranche"] = base_identity["execution_tranche"]
    restored_identity["authority_commit"] = base_identity["authority_commit"]
    restored_identity["authority_amendment"] = base_identity["authority_amendment"]
    restored_identity["effective_lock_path"] = base_identity["effective_lock_path"]
    # Reverse the one run-root substitution after the generic inverse pass.
    def reverse(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: reverse(child) for key, child in value.items()}
        if isinstance(value, list):
            return [reverse(child) for child in value]
        if isinstance(value, str):
            if value == BINDING_02_LOCK_PATH:
                return base_identity["effective_lock_path"]
            return value.replace(BINDING_02_RUN_PREFIX, FORBIDDEN_BINDING_01_RUN_PREFIX)
        return value
    if reverse(restored) != base:
        raise S10R4Error("binding-02 composition changed a scientific field")


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    if path != CONTRACT_PATH:
        raise S10R4Error("binding-02 contract aliases or fallbacks are forbidden")
    base = load_base_contract(path)
    supplement = load_contract_supplement()
    old_lock = base["identity"]["effective_lock_path"]
    composed = _replace_binding_descendants(base, old_lock=old_lock)
    composed["contract_id"] = PROTOCOL_ID
    replacements = supplement["identity_replacements"]
    composed["identity"]["execution_tranche"] = replacements["execution_tranche"]
    composed["identity"]["authority_commit"] = replacements["authority_commit_oid"]
    composed["identity"]["authority_amendment"] = replacements["authority_amendment"]
    composed["identity"]["effective_lock_path"] = replacements["effective_lock_path"]
    composed["binding_02_operational_inputs"] = {
        "supplement_and_recovery": _supplement_lock_inputs(supplement),
        "prebinding_recovery": _prebinding_recovery_lock_inputs(
            load_prebinding_recovery_amendment()
        ),
    }
    _assert_composed_scientific_identity(base, composed)
    encoded = canonical_json(composed).decode("utf-8")
    if FORBIDDEN_BINDING_01_RUN_PREFIX in encoded or old_lock in encoded:
        raise S10R4Error("residual binding-01 runtime identity in composed contract")
    return composed


def validate_document_schema(document: Mapping[str, Any], *, schema_path: Path = SCHEMA_PATH) -> None:
    """Validate one external S10R4 document against the frozen strict union."""
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - the frozen runtime supplies it
        raise S10R4Error("jsonschema is unavailable in the frozen runtime") from exc
    schema = load_json(schema_path)
    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        raise S10R4Error(f"invalid S10R4 JSON Schema: {exc.message}") from exc
    errors = sorted(
        jsonschema.Draft7Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        leaf_errors = []

        def collect_leaf_errors(error):
            if error.context:
                for child in error.context:
                    collect_leaf_errors(child)
                return
            leaf_errors.append(error)

        for root_error in errors:
            collect_leaf_errors(root_error)
        error = max(
            leaf_errors,
            key=lambda candidate: (
                len(candidate.absolute_path),
                tuple(str(part) for part in candidate.absolute_path),
            ),
        )
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise S10R4Error(f"S10R4 schema rejection at {location}: {error.message}")


def require_exact_keys(value: Mapping[str, Any], keys: Iterable[str], *, where: str) -> None:
    expected = set(keys)
    actual = set(value)
    if actual != expected:
        raise S10R4Error(
            f"{where} keys mismatch: missing={sorted(expected - actual)} "
            f"unknown={sorted(actual - expected)}"
        )


def contained_path(root: Path, candidate: Path) -> Path:
    root_real = root.resolve(strict=True)
    candidate_real = candidate.resolve(strict=False)
    try:
        candidate_real.relative_to(root_real)
    except ValueError as exc:
        raise S10R4Error(f"path escapes root: {candidate}") from exc
    return candidate_real


def safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise S10R4Error(f"unsafe relative path: {value!r}")
    return path


def ordinary_file_records(root: Path) -> tuple[list[dict[str, Any]], int]:
    """Inventory a stable ordinary-file tree without following links."""
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise S10R4Error(f"inventory root is not a directory: {root}")
    records: list[dict[str, Any]] = []
    total_size = 0
    seen_inodes: set[tuple[int, int]] = set()
    stack = [root]
    while stack:
        directory = stack.pop()
        before = directory.stat(follow_symlinks=False)
        entries = sorted(os.scandir(directory), key=lambda entry: os.fsencode(entry.name))
        for entry in entries:
            path = Path(entry.path)
            info = entry.stat(follow_symlinks=False)
            mode = info.st_mode
            if stat.S_ISLNK(mode):
                raise S10R4Error(f"symlink forbidden in inventory: {path}")
            if stat.S_ISDIR(mode):
                stack.append(path)
                continue
            if not stat.S_ISREG(mode):
                raise S10R4Error(f"non-ordinary file forbidden in inventory: {path}")
            inode = (info.st_dev, info.st_ino)
            if info.st_nlink != 1 or inode in seen_inodes:
                raise S10R4Error(f"hard-link ambiguity in inventory: {path}")
            seen_inodes.add(inode)
            relative = path.relative_to(root).as_posix()
            digest = raw_sha256(path)
            after = path.stat(follow_symlinks=False)
            identity_before = (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns)
            identity_after = (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns)
            if identity_before != identity_after:
                raise S10R4Error(f"file mutated during inventory: {path}")
            records.append(
                {
                    "relative_path": relative,
                    "mode": stat.S_IMODE(mode),
                    "size_bytes": info.st_size,
                    "sha256": digest,
                }
            )
            total_size += info.st_size
        after_dir = directory.stat(follow_symlinks=False)
        if (before.st_dev, before.st_ino, before.st_mtime_ns) != (
            after_dir.st_dev,
            after_dir.st_ino,
            after_dir.st_mtime_ns,
        ):
            raise S10R4Error(f"directory mutated during inventory: {directory}")
    records.sort(key=lambda record: record["relative_path"].encode("utf-8"))
    return records, total_size


def atomic_write_json(path: Path, data: Any, *, no_overwrite: bool = True, mode: int = 0o644) -> None:
    """Atomically write canonical JSON and fsync both file and parent."""
    payload = canonical_json(data, newline=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if no_overwrite:
            if path.is_file() and path.read_bytes() == payload:
                return
            raise S10R4Error(f"refusing to overwrite existing path: {path}")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temporary)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise S10R4Error(f"target appeared during atomic write: {path}")
        os.link(temp_path, path)
        temp_path.unlink()
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def atomic_write_bytes(path: Path, payload: bytes, *, mode: int = 0o644) -> None:
    """Atomically create exact bytes, adopting only an identical existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_file() and path.read_bytes() == payload:
            return
        raise S10R4Error(f"refusing to overwrite unequal existing bytes: {path}")
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise S10R4Error(f"target appeared during atomic byte write: {path}")
        os.link(temporary, path)
        temporary.unlink()
        parent = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def seal_digest(document: Mapping[str, Any], field: str = "document_digest") -> dict[str, Any]:
    sealed = dict(document)
    sealed[field] = "0" * 64
    sealed[field] = canonical_sha256({key: value for key, value in sealed.items() if key != field})
    return sealed


def validate_sealed_digest(document: Mapping[str, Any], field: str = "document_digest") -> None:
    value = document.get(field)
    if not isinstance(value, str) or len(value) != 64:
        raise S10R4Error(f"{field} is absent or malformed")
    projection = {key: child for key, child in document.items() if key != field}
    if canonical_sha256(projection) != value:
        raise S10R4Error(f"{field} mismatch")


def canonical_self_hash(document: Mapping[str, Any], path: Sequence[str]) -> str:
    clone = json.loads(canonical_json(document))
    cursor: Any = clone
    for key in path[:-1]:
        if not isinstance(cursor, dict) or key not in cursor:
            raise S10R4Error("lock self-hash path is absent")
        cursor = cursor[key]
    leaf = path[-1]
    if not isinstance(cursor, dict) or leaf not in cursor:
        raise S10R4Error("lock self-hash leaf is absent")
    value = cursor[leaf]
    if not isinstance(value, str) or len(value) != 64:
        raise S10R4Error("lock self-hash field is not a 64-character string")
    cursor[leaf] = "0" * 64
    return canonical_sha256(clone)


def ensure_prelabel_absence(contract: Mapping[str, Any], repo_root: Path = REPO_ROOT) -> None:
    for relative in contract["prelabel_absence"]["durable_paths"]:
        if (repo_root / relative).exists():
            raise S10R4Error(f"formal/outcome durable path must be absent: {relative}")
    for relative in contract["prelabel_absence"]["raw_scopes"]:
        if (repo_root / relative).exists():
            raise S10R4Error(f"formal raw scope must be absent: {relative}")
    lock = repo_root / contract["identity"]["effective_lock_path"]
    if lock.exists():
        raise S10R4Error("production effective lock must be absent during prelabel implementation")


def validate_phase1() -> dict[str, Any]:
    contract = load_contract()
    ensure_prelabel_absence(contract)
    yaml_path = REPO_ROOT / contract["source_and_input_identity"]["actual_yaml"]["path"]
    if raw_sha256(yaml_path) != contract["source_and_input_identity"]["actual_yaml"]["sha256"]:
        raise S10R4Error("actual YAML identity mismatch")
    if contract["identity"]["risk_tier"] != "R3":
        raise S10R4Error("S10R4 risk tier is not R3")
    return contract


def document_record(path: Path) -> dict[str, Any]:
    info = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise S10R4Error(f"document is not one unambiguous ordinary file: {path}")
    obj = load_json(path)
    return {
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "mode": stat.S_IMODE(info.st_mode),
        "size_bytes": info.st_size,
        "raw_sha256": raw_sha256(path),
        "canonical_sha256": canonical_sha256(obj),
    }


def validate_document_kind(document: Mapping[str, Any], allowed: Iterable[str]) -> str:
    kind = document.get("document_kind")
    if not isinstance(kind, str) or kind not in set(allowed):
        raise S10R4Error(f"unknown S10R4 document kind: {kind!r}")
    return kind


FIXED_ENVIRONMENT = {
    "LC_ALL": "C",
    "PYTHONHASHSEED": "0",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
    "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
}

COMMAND_TEMPLATES = {
    "validate_contract": [
        "/opt/venv/bin/python3",
        "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
        "validate-contract",
    ],
    "verify_prelabel": [
        "/opt/venv/bin/python3",
        "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
        "verify-prelabel",
    ],
    "prepare_prelabel": [
        "/opt/venv/bin/python3",
        "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
        "prepare-prelabel",
        "--raw-root", "/src/rocm-libraries/agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/formal-cpu",
        "--build-root", "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/artifacts/prelabel-build",
        "--fixture-root", "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/artifacts/prelabel-fixtures",
        "--frame-registry", "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r4-exact-frame-registry.json",
        "--size-registry", "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r4-size-registry.json",
        "--native-fixture", "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r4-native-fixture.json",
    ],
    "build-lock": [
        "/opt/venv/bin/python3",
        "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
        "build-lock", "--output",
        "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s10r4-stage1-exact-frame-entry-binding-02-lock.json",
    ],
    "census_child": [
        "/opt/venv/bin/python3",
        "/src/rocm-libraries/study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
        "_census-child",
        "--request",
        "{child_root}/request.json",
        "--result",
        "{child_root}/result.json",
    ],
    "mapping_child": [
        "/opt/venv/bin/python3",
        "/src/rocm-libraries/study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
        "_mapping-child",
        "--request",
        "{attempt_root}/request.json",
        "--result",
        "{attempt_root}/result.json",
    ],
    "correctness_build_child": [
        "/opt/venv/bin/python3",
        "/src/rocm-libraries/study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
        "_correctness-build-child",
        "--request",
        "{attempt_root}/build-request.json",
        "--result",
        "{attempt_root}/build-result.json",
    ],
    "gpu_allocation_snapshot": [
        "/opt/rocm/bin/rocm-smi", "--showproductname", "--showuniqueid", "--showserial",
        "--showuse", "--showmemuse", "--showcomputepartition", "--showmemorypartition", "--json",
    ],
    "gpu_process_snapshot": ["/opt/rocm/bin/rocm-smi", "--showpidgpus"],
}

for _name in (
    "census", "classify-select", "mapping", "native-conformance", "gpu-environment",
    "correctness", "noise", "decision", "verify-lock",
):
    COMMAND_TEMPLATES.setdefault(
        _name,
        [
            "/opt/venv/bin/python3",
            "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
            _name,
            "--lock",
            "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s10r4-stage1-exact-frame-entry-binding-02-lock.json",
        ],
    )

COMMAND_TEMPLATES["census"] = [
    "/opt/venv/bin/python3",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
    "census", "--pass-id", "{pass_id}", "--lock",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s10r4-stage1-exact-frame-entry-binding-02-lock.json",
]
COMMAND_TEMPLATES["mapping"] = [
    "/opt/venv/bin/python3",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
    "mapping", "--pass-id", "{pass_id}", "--lock",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s10r4-stage1-exact-frame-entry-binding-02-lock.json",
]
COMMAND_TEMPLATES["reproduction"] = [
    "/opt/venv/bin/python3",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
    "reproduction", "--lock",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s10r4-stage1-exact-frame-entry-binding-02-lock.json",
    "--output",
    "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/artifacts/reproduction/s10r4-independent-result.json",
]

COMMAND_TEMPLATES.update(
    {
        "materialize_ductile_source": [
            "/usr/bin/git", "-c", "safe.directory=/src/rocm-libraries", "archive", "--format=tar",
            "5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39", "projects/hipblaslt", "shared/origami",
            "cmake", "CMakeLists.txt",
        ],
        "resolve_geko_commit": [
            "/usr/bin/git", "-c", "safe.directory=/src/rocm-libraries", "cat-file", "-e",
            "d32abacfd13579d1f523f035b7a10b0734c4ac47^{{commit}}",
        ],
        "native_configure": [
            "/opt/venv/bin/cmake", "-S",
            "/src/rocm-libraries/agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/artifacts/prelabel-build/native/source",
            "-B", "/src/rocm-libraries/agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/artifacts/prelabel-build/native/build",
            "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=/opt/rocm/bin/amdclang++",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        ],
        "native_build": [
            "/opt/venv/bin/cmake", "--build",
            "/src/rocm-libraries/agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/artifacts/prelabel-build/native/build",
            "--target", "s10r4-native", "tensilelite-client", "--parallel", "16", "--verbose",
        ],
        "correctness_build_trace": [
            "/usr/bin/strace", "-f", "-qq", "-s", "1048576", "-e", "trace=execve", "-o",
            "{attempt_root}/build-execve.log", "--", "/opt/venv/bin/python3",
            "/src/rocm-libraries/study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py",
            "_correctness-build-child", "--request", "{attempt_root}/build-request.json", "--result",
            "{attempt_root}/build-result.json",
        ],
        "native_fixture_execution": [
            "{binary_path}", "--input", "{input_path}", "--output", "{output_path}",
        ],
        "correctness_client": ["{client_path}", "--config-file", "{config_path}"],
        "noise_client": ["{client_path}", "--config-file", "{config_path}"],
    }
)

COMMAND_PLACEHOLDERS = {
    command_id: frozenset(
        field_name
        for part in template
        for _, field_name, format_spec, conversion in string.Formatter().parse(part)
        if field_name is not None
    )
    for command_id, template in COMMAND_TEMPLATES.items()
}


def materialize_command_template(command_id: str, substitutions: Mapping[str, str] | None = None) -> list[str]:
    """Materialize one frozen argv template and reject every ambiguous substitution."""
    template = COMMAND_TEMPLATES.get(command_id)
    if template is None:
        raise S10R4Error(f"unknown frozen command template: {command_id}")
    values = {} if substitutions is None else dict(substitutions)
    expected = COMMAND_PLACEHOLDERS[command_id]
    if set(values) != set(expected):
        raise S10R4Error(
            f"command substitution mismatch for {command_id}: "
            f"missing={sorted(set(expected) - set(values))} unknown={sorted(set(values) - set(expected))}"
        )
    if any(not isinstance(value, str) for value in values.values()):
        raise S10R4Error("command substitutions must be strings")
    if "pass_id" in values and values["pass_id"] not in ("A", "B"):
        raise S10R4Error("command pass_id substitution must be A or B")
    materialized: list[str] = []
    for part in template:
        try:
            value = part.format_map(values)
        except (KeyError, ValueError) as exc:
            raise S10R4Error(f"command template could not be materialized: {command_id}") from exc
        frozen_git_type_literal = (
            command_id == "resolve_geko_commit"
            and value == "d32abacfd13579d1f523f035b7a10b0734c4ac47^{commit}"
        )
        if not isinstance(value, str) or (re.search(r"\{[^{}]*\}", value) and not frozen_git_type_literal):
            raise S10R4Error(f"command template retains an unresolved placeholder: {command_id}")
        materialized.append(value)
    return materialized


def validate_environment(environment: Mapping[str, str], *, worker_pythonpath: str | None = None) -> None:
    expected = dict(FIXED_ENVIRONMENT)
    if worker_pythonpath is not None:
        expected["PYTHONPATH"] = worker_pythonpath
    if dict(environment) != expected:
        raise S10R4Error("command environment differs from the exact S10R4 allowlist")


def validate_command_template(
    command_id: str,
    argv: Sequence[str],
    substitutions: Mapping[str, str] | None = None,
) -> None:
    expected = materialize_command_template(command_id, substitutions)
    if list(argv) != expected:
        raise S10R4Error(f"argv differs from frozen command template: {command_id}")


LLVM_EXECUTABLE_NAMES = (
    "clang++",
    "clang",
    "ld.lld",
    "llvm-mc",
    "llvm-objcopy",
    "clang-offload-bundler",
)


def llvm_executable_closure(root: Path = Path("/opt/rocm-7.2.4/lib/llvm/bin")) -> list[dict[str, Any]]:
    """Bind the exact pre-outcome LLVM driver/descendant executable allowlist."""
    records: list[dict[str, Any]] = []
    for name in LLVM_EXECUTABLE_NAMES:
        requested = root / name
        if not requested.exists():
            records.append({"requested_path": requested.as_posix(), "present": False})
            continue
        resolved = requested.resolve(strict=True)
        info = resolved.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not os.access(resolved, os.X_OK):
            raise S10R4Error(f"LLVM closure member is not one executable ordinary file: {requested}")
        records.append(
            {
                "requested_path": requested.as_posix(),
                "present": True,
                "resolved_path": resolved.as_posix(),
                "mode": stat.S_IMODE(info.st_mode),
                "size_bytes": info.st_size,
                "sha256": raw_sha256(resolved),
            }
        )
    return records


PLAN_A_REVISION = 16
PLAN_A_RAW_SHA256 = "4b70dfafbd42fd38af5760d009464a65a832215790d333c6681ed5a8072fdd7f"
PLAN_A_SIZE_BYTES = 51130
PLAN_A_PREDECESSOR = {
    "revision": 15,
    "raw_sha256": "942778d354ad2f0cd53b82e8ae43c299a594e456ef56b2249db048f6c2f2276f",
    "size_bytes": 44424,
}
PHASE1_COMMIT_OID = "9e10067d6ea7ae6b979cf99d97ebee007d1ceec6"
SUPPLEMENT_PHASE1_COMMIT_OID = "0a814e476efffebfacaedb904afddbef38ddee15"
RECOVERY_AUTHORITY_COMMIT_OID = "37c846e5b0edc182fd84432da3596090dbf3ee15"
BINDING_01_SOURCE_COMMIT_OID = "95e29a8618a4cf6bab1addb26376b1917ddb8404"
BINDING_01_REVERT_COMMIT_OID = "3881ac62dec7c9ca74cf4b2ad4005727b3b34808"
AMENDMENT_COMMIT_OID = "c2c8864f5dd54d6d03562289f8d8c37de3c9b602"
AMENDMENT_BLOB_OID = "c229f627fab19551f8302f4637812020ea3e4ebd"
BINDING_02_ROOT = REPO_ROOT / BINDING_02_RUN_PREFIX.removesuffix("/")
RETIRED_PREBINDING_LEDGER_PATH = BINDING_02_ROOT / "gates/s10r4/audit-verdict.json"
PREBINDING_LEDGER_PATH = BINDING_02_ROOT / "gates/s10r4/audit-verdict-r2.json"
POST_COMMIT_LEDGER_PATH = BINDING_02_ROOT / "closure/post-commit-audit.json"
PLAN_A_REVISION_LEDGER_PATH = BINDING_02_ROOT / "gates/s10r4/plan_a-revisions.jsonl"
BASELINE_PATH = BINDING_02_ROOT / "baseline.md"
IMPLEMENTER_REPORT_PATHS = (
    BINDING_02_ROOT / "gates/s10r4/implementer-report.md",
    BINDING_02_ROOT / "gates/s10r4/implementer-report.json",
)
RECOVERY_AUTHORITY_PATH = REPO_ROOT / "study_docs/research/ductile-origami-warmstart/s10r4-binding-02-execution-recovery-authority.md"
AUTHORITY_ROOT = BINDING_02_ROOT / "authority"
RECOVERY_AUTHORITY_AUDIT_PATH = AUTHORITY_ROOT / "postcommit-audit.json"
SUPPLEMENT_POSTCOMMIT_AUDIT_PATH = AUTHORITY_ROOT / "supplement-postcommit-audit.json"
SUPPLEMENT_REVIEWER_A_R2_PATH = AUTHORITY_ROOT / "reviewer-a-supplement-precommit-verdict-r2.json"
SUPPLEMENT_ADVERSARIAL_R2_PATH = AUTHORITY_ROOT / "adversarial-supplement-precommit-audit-r2.json"
BINDING_01_REVERT_AUDIT_PATH = AUTHORITY_ROOT / "binding-01-revert-postcommit-audit.json"
AMENDMENT_REVIEWER_A_PATH = AUTHORITY_ROOT / "prebinding-recovery-amendment-reviewer-a.json"
AMENDMENT_ADVERSARIAL_PATH = AUTHORITY_ROOT / "prebinding-recovery-amendment-adversarial.json"
AMENDMENT_POSTCOMMIT_AUDIT_PATH = (
    AUTHORITY_ROOT / "prebinding-recovery-amendment-postcommit-audit.json"
)
ADJUDICATION_PATH = BINDING_02_ROOT / "gates/s10r4/adjudication.md"

AUDIT_EVENT_FIELDS = {
    "ordinal", "phase", "verdict", "auditor_task_id", "fresh",
    "implementation_participation", "created_utc", "inputs", "findings",
    "previous_event_digest", "event_digest",
}
PREBINDING_PHASES = (
    ("PHASE1_POST_COMMIT", "AUDIT_PASS_PREIMPLEMENTATION"),
    ("PLAN_A_PARITY", "AUDIT_PASS_PLAN_A_PARITY"),
    ("IMPLEMENTATION_PARITY", "AUDIT_PASS_IMPLEMENTATION_PARITY"),
    ("FINAL_PREBINDING", "AUDIT_PASS_PREBINDING"),
)
POST_COMMIT_PHASES = (
    ("PHASE2_POST_BINDING", "AUDIT_PASS_POST_BINDING"),
    ("TERMINAL_POST_COMMIT", "AUDIT_PASS_TERMINAL"),
)
AUDIT_INPUT_FIELDS = {
    "PHASE1_POST_COMMIT": {
        "authority_commit_oid", "contract_record", "phase1_commit_oid", "phase1_parent_oid",
        "phase1_diff_paths", "phase1_committed_record", "diagnostic_audit_record",
        "supplement_record", "supplement_commit_oid", "supplement_postcommit_audit_record",
        "supplement_precommit_verdict_records", "recovery_authority_record",
        "recovery_authority_audit_record", "binding_01_revert_record",
        "prebinding_recovery_amendment_record",
        "prebinding_recovery_precommit_verdict_records",
        "prebinding_recovery_postcommit_audit_record",
    },
    "PLAN_A_PARITY": {
        "authority_commit_oid", "contract_record", "plan_a_record", "predecessor_plan_a",
        "plan_a_revision_ledger_record", "selected_revision_record", "plan_b_record",
        "plan_b_freeze_record", "diagnostic_audit_records",
        "append_only_adjudication_record", "retired_prebinding_attempt_record",
    },
    "IMPLEMENTATION_PARITY": {
        "contract_record", "plan_a_record", "plan_b_record", "implementation_records",
        "prelabel_records", "implementer_report_records", "self_checks",
        "implementation_projection_sha256", "prelabel_projection_sha256", "formal_absence",
    },
    "FINAL_PREBINDING": {
        "authority_commit_oid", "contract_record", "plan_a_record", "plan_b_record",
        "lock_input_projection_hashes", "source_realization", "tool_realization",
        "container_device_realization", "role_resource_boundary_realization",
        "expected_phase2_paths", "existing_phase2_records", "formal_absence",
        "unrelated_worktree_observation", "lock_output_absence",
        "prebinding_recovery_inputs",
    },
    "PHASE2_POST_BINDING": {
        "phase2_commit_oid", "phase2_parent_oid", "commit_is_ancestor_of_head",
        "changed_paths", "path_records", "lock_record", "lock_self_sha256",
        "prebinding_ledger_record", "formal_absence", "auditor_task_id", "fresh",
        "unrelated_worktree_observation", "exact_commit_projection_sha256",
    },
    "TERMINAL_POST_COMMIT": {
        "terminal_commit_oid", "terminal_parent_oid", "delivery_records",
        "delivery_manifest_record", "closeout_ack_record", "verifier_verdict_record",
        "report_record", "decision_record", "final_state", "edge",
    },
}


def _binding_record(path: Path, *, canonical: Any = None) -> dict[str, Any]:
    info = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise S10R4Error(f"binding is not one ordinary file: {path}")
    if canonical is None and path.suffix == ".json":
        canonical = load_json(path)
    return {
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "mode": stat.S_IMODE(info.st_mode),
        "size_bytes": info.st_size,
        "raw_sha256": raw_sha256(path),
        "canonical_sha256": None if canonical is None else canonical_sha256(canonical),
    }


def _base_contract_record() -> dict[str, Any]:
    return _binding_record(CONTRACT_PATH, canonical=load_base_contract())


def _supplement_lock_inputs(supplement: Mapping[str, Any]) -> dict[str, Any]:
    committed = _committed_path_record(
        SUPPLEMENT_PHASE1_COMMIT_OID, SUPPLEMENT_PATH.relative_to(REPO_ROOT).as_posix()
    )
    current = _binding_record(SUPPLEMENT_PATH, canonical=supplement)
    if (
        committed["path"] != current["path"]
        or committed["git_mode"] != "100644"
        or committed["size_bytes"] != current["size_bytes"]
        or committed["raw_sha256"] != current["raw_sha256"]
    ):
        raise S10R4Error("binding-02 supplement commit/current-byte identity mismatch")
    supplement_record = {
        **committed,
        "phase1_commit_oid": SUPPLEMENT_PHASE1_COMMIT_OID,
        "canonical_sha256": current["canonical_sha256"],
    }
    exact_raw = {
        RECOVERY_AUTHORITY_PATH: "43102f3db93d3b8044738b1c25413ab3d01dda1da0b360baeeb549bc7f3fed0c",
        RECOVERY_AUTHORITY_AUDIT_PATH: "1eb70fa4129a2112f58acec9371da8ad97a1bc2bdf0d37d91c1e8a544c681147",
        SUPPLEMENT_POSTCOMMIT_AUDIT_PATH: "461b84f89edef1f8e5d79daf7fc8b9974d8cc08a9cc84e9472c35d77395ed6dc",
        SUPPLEMENT_REVIEWER_A_R2_PATH: "7ca420f29ba4ff64cb256d9ac1fb908664693e4ae13fc265fb1799ebe649143b",
        SUPPLEMENT_ADVERSARIAL_R2_PATH: "f45f8735bde5a26975680739f6f1e6af6885d6281505b04fac4e8fdba9a5472f",
        BINDING_01_REVERT_AUDIT_PATH: "bf19e964d6cb967e0841b1056a945f4db40ebe662521ef786e365d4a65125695",
    }
    for path, digest in exact_raw.items():
        if raw_sha256(path) != digest:
            raise S10R4Error(f"binding-02 authority record raw identity mismatch: {path}")
    recovery_audit = load_json(RECOVERY_AUTHORITY_AUDIT_PATH)
    supplement_audit = load_json(SUPPLEMENT_POSTCOMMIT_AUDIT_PATH)
    reviewer = load_json(SUPPLEMENT_REVIEWER_A_R2_PATH)
    adversarial = load_json(SUPPLEMENT_ADVERSARIAL_R2_PATH)
    revert = load_json(BINDING_01_REVERT_AUDIT_PATH)
    if (
        recovery_audit.get("verdict") != "AUDIT_PASS_AUTHORITY_POSTCOMMIT"
        or supplement_audit.get("verdict") != "AUDIT_PASS_BINDING_02_SUPPLEMENT"
        or supplement_audit.get("audited_supplement_commit_oid") != SUPPLEMENT_PHASE1_COMMIT_OID
        or reviewer.get("verdict") != "PASS"
        or adversarial.get("verdict") != "PASS"
        or reviewer.get("candidate", {}).get("raw_sha256") != SUPPLEMENT_RAW_SHA256
        or adversarial.get("candidate", {}).get("raw_sha256") != SUPPLEMENT_RAW_SHA256
        or revert.get("verdict") != "AUDIT_PASS_BINDING_01_HISTORY_PRESERVING_REVERT"
        or revert.get("revert_commit", {}).get("oid") != BINDING_01_REVERT_COMMIT_OID
        or revert.get("revert_commit", {}).get("old_phase_2_commit_reverted")
        != BINDING_01_SOURCE_COMMIT_OID
    ):
        raise S10R4Error("binding-02 authority verdict/commit identity mismatch")

    def verdict_record(path: Path, document: Mapping[str, Any], *, role: str) -> dict[str, Any]:
        record = _binding_record(path, canonical=document)
        return {**record, "role": role, "verdict": document["verdict"]}

    supplement_audit_record = _binding_record(
        SUPPLEMENT_POSTCOMMIT_AUDIT_PATH, canonical=supplement_audit
    )
    retirement = supplement["binding_01_retirement"]
    threads = supplement["workflow_authority"]["threads"]
    resources = supplement["resources"]
    return {
        "supplement_record": supplement_record,
        "supplement_postcommit_audit_record": {
            **supplement_audit_record,
            "audited_supplement_commit_oid": supplement_audit["audited_supplement_commit_oid"],
            "verdict": supplement_audit["verdict"],
        },
        "supplement_precommit_verdict_records": [
            verdict_record(
                SUPPLEMENT_REVIEWER_A_R2_PATH, reviewer, role="fresh_independent_reviewer_a"
            ),
            verdict_record(
                SUPPLEMENT_ADVERSARIAL_R2_PATH,
                adversarial,
                role="independent_adversarial_auditor",
            ),
        ],
        "recovery_authority_record": {
            **_binding_record(RECOVERY_AUTHORITY_PATH),
            "commit_oid": RECOVERY_AUTHORITY_COMMIT_OID,
        },
        "recovery_authority_postcommit_audit_record": verdict_record(
            RECOVERY_AUTHORITY_AUDIT_PATH, recovery_audit, role="authority_postcommit_auditor"
        ),
        "binding_01_retirement": {
            "state": retirement["state"],
            "scientific_outcome": retirement["scientific_outcome"],
            "edge": retirement["edge"],
            "completed_terminal_census_prefix": retirement["completed_terminal_census_prefix"],
            "run_root": retirement["run_root"],
            "phase2_commit_oid": retirement["phase2_commit_oid"],
            "projection_sha256": canonical_sha256(retirement),
            "revert_commit_oid": BINDING_01_REVERT_COMMIT_OID,
            "revert_audit_record": verdict_record(
                BINDING_01_REVERT_AUDIT_PATH, revert, role="history_preserving_revert_auditor"
            ),
        },
        "carried_role_resource_provenance": {
            "original_design_reviewers_used": threads["original_design_reviewers_used"],
            "adversarial_auditor_threads_used": threads["adversarial_auditor_threads_used"],
            "implementer_threads_used": threads["implementer_threads_used"],
            "binding_recovery_operational_reviewer_threads_used": threads[
                "binding_recovery_operational_reviewer_threads_used"
            ],
            "planned_fresh_verifier_threads": threads["planned_fresh_verifier_threads"],
            "projected_total": threads["projected_total"],
            "maximum": threads["maximum"],
            "historical_observed_activity_lower_bound_seconds": resources[
                "carry_from_binding_01"
            ]["observed_activity_lower_bound_seconds"],
            "historical_storage_bytes_before_final_reports": resources[
                "carry_from_binding_01"
            ]["storage_bytes_before_final_reports"],
            "historical_whole_role_cpu_seconds": resources["carry_from_binding_01"][
                "whole_role_cpu_seconds"
            ],
            "historical_whole_role_wall_seconds": resources["carry_from_binding_01"][
                "whole_role_wall_seconds"
            ],
            "reset_on_binding_02": resources["reset_on_binding_02"],
            "role_projection_sha256": canonical_sha256(threads),
            "resource_projection_sha256": canonical_sha256(resources),
        },
    }


def _prebinding_recovery_lock_inputs(amendment: Mapping[str, Any]) -> dict[str, Any]:
    """Remeasure the immutable A49 amendment, audits, and retired attempt."""
    committed = _committed_path_record(
        AMENDMENT_COMMIT_OID, AMENDMENT_PATH.relative_to(REPO_ROOT).as_posix()
    )
    current = _binding_record(AMENDMENT_PATH, canonical=amendment)
    if committed != {
        "path": AMENDMENT_PATH.relative_to(REPO_ROOT).as_posix(),
        "git_mode": "100644",
        "blob_oid": AMENDMENT_BLOB_OID,
        "size_bytes": 10403,
        "raw_sha256": AMENDMENT_RAW_SHA256,
    } or current != {
        "path": AMENDMENT_PATH.relative_to(REPO_ROOT).as_posix(),
        "mode": 0o664,
        "size_bytes": 10403,
        "raw_sha256": AMENDMENT_RAW_SHA256,
        "canonical_sha256": AMENDMENT_CANONICAL_SHA256,
    }:
        raise S10R4Error("prebinding-recovery amendment commit/current-byte mismatch")
    amendment_record = {
        **committed,
        "canonical_sha256": AMENDMENT_CANONICAL_SHA256,
        "commit_oid": AMENDMENT_COMMIT_OID,
    }

    exact_audits = (
        (
            AMENDMENT_REVIEWER_A_PATH,
            "fc222c2cbc53cab14d0d02cf291a41d5f367bf9f61607c0452b41e254d030d1d",
            "0e43ca4b2a84b1cfb2330fca5f14fd61721eb8f35e5b36c96beba023d2fe93ca",
            6892,
            "/root/s10r4_failure_reviewer_a",
        ),
        (
            AMENDMENT_ADVERSARIAL_PATH,
            "db1dc835eaebc878fcd5f3d8e5c5cfbbb8e30885808b1e9e10d26cf4f86b8df4",
            "b3f85a384e29aefba542ba15cbc25e89b329625d48d51963f63e8342638da4ac",
            8228,
            "/root/s10r4_adversarial_auditor",
        ),
    )
    precommit_records: list[dict[str, Any]] = []
    for path, raw_digest, canonical_digest, size, task_id in exact_audits:
        document = load_json(path)
        record = _binding_record(path, canonical=document)
        candidate = document.get("candidate")
        observed_task = document.get("reviewer_task_id")
        if observed_task is None:
            observed_task = document.get("reviewer", {}).get("task_id")
        if (
            record != {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "mode": 0o664,
                "size_bytes": size,
                "raw_sha256": raw_digest,
                "canonical_sha256": canonical_digest,
            }
            or document.get("verdict") != "PASS"
            or document.get("findings") != []
            or observed_task != task_id
            or not isinstance(candidate, Mapping)
            or candidate.get("path") != amendment_record["path"]
            or candidate.get("size_bytes") != amendment_record["size_bytes"]
            or candidate.get("raw_sha256") != amendment_record["raw_sha256"]
            or candidate.get("canonical_sha256") != amendment_record["canonical_sha256"]
        ):
            raise S10R4Error(f"prebinding-recovery precommit verdict mismatch: {path}")
        precommit_records.append(
            {
                **record,
                "reviewer_task_id": task_id,
                "candidate_raw_sha256": candidate["raw_sha256"],
                "candidate_canonical_sha256": candidate["canonical_sha256"],
                "verdict": "PASS",
                "findings": [],
            }
        )

    postcommit = load_json(AMENDMENT_POSTCOMMIT_AUDIT_PATH)
    postcommit_binding = _binding_record(
        AMENDMENT_POSTCOMMIT_AUDIT_PATH, canonical=postcommit
    )
    expected_postcommit_binding = {
        "path": AMENDMENT_POSTCOMMIT_AUDIT_PATH.relative_to(REPO_ROOT).as_posix(),
        "mode": 0o664,
        "size_bytes": 7297,
        "raw_sha256": "ed92bc2f8690ba75cf5cebabac5a41a176b5bb702bbc09a19d11b22e9a146e74",
        "canonical_sha256": canonical_sha256(postcommit),
    }
    if (
        postcommit_binding != expected_postcommit_binding
        or postcommit_binding["canonical_sha256"]
        != "5503bae535fec733da478e87278254e8f736c5ea4467c1eacb7b1394af81ab8b"
        or postcommit.get("audited_commit_oid") != AMENDMENT_COMMIT_OID
        or postcommit.get("verdict")
        != "AUDIT_PASS_PREBINDING_RECOVERY_AMENDMENT_POSTCOMMIT"
        or postcommit.get("findings") != []
        or postcommit.get("commit_audit", {}).get("changed_paths")
        != [{"status": "A", "path": amendment_record["path"]}]
        or postcommit.get("commit_audit", {}).get("amendment_record", {}).get("blob_oid")
        != AMENDMENT_BLOB_OID
    ):
        raise S10R4Error("prebinding-recovery postcommit audit mismatch")
    postcommit_record = {
        **postcommit_binding,
        "audited_commit_oid": AMENDMENT_COMMIT_OID,
        "verdict": "AUDIT_PASS_PREBINDING_RECOVERY_AMENDMENT_POSTCOMMIT",
    }

    retired_document = load_json(RETIRED_PREBINDING_LEDGER_PATH)
    retired_binding = _binding_record(
        RETIRED_PREBINDING_LEDGER_PATH, canonical=retired_document
    )
    retired = amendment["retired_prebinding_attempt"]
    retired_info = RETIRED_PREBINDING_LEDGER_PATH.stat(follow_symlinks=False)
    expected_retired_binding = {
        "path": retired["path"],
        "mode": retired["mode"],
        "size_bytes": retired["size_bytes"],
        "raw_sha256": retired["raw_sha256"],
        "canonical_sha256": retired["canonical_sha256"],
    }
    if (
        retired_binding != expected_retired_binding
        or not stat.S_ISREG(retired_info.st_mode)
        or retired_info.st_nlink != 1
        or retired_document.get("ledger_digest") != retired["ledger_digest"]
        or [event.get("event_digest") for event in retired_document.get("events", [])]
        != retired["event_digests"]
        or retired.get("state") != "retired_prebinding_diagnostic"
        or retired.get("seal_authority") is not False
        or retired.get("preserve_in_place") is not True
        or retired.get("use_as_lock_input_or_pass_verdict") != "forbidden"
    ):
        raise S10R4Error("retired prebinding-attempt identity mismatch")
    retired_record = {
        **retired_binding,
        "link_count": retired_info.st_nlink,
        "state": "retired_prebinding_diagnostic",
        "seal_authority": False,
        "ledger_digest": retired["ledger_digest"],
        "event_digests": list(retired["event_digests"]),
    }
    successor = amendment["successor_prebinding_ledger"]
    successor_path = PREBINDING_LEDGER_PATH.relative_to(REPO_ROOT).as_posix()
    if (
        successor.get("path") != successor_path
        or successor.get("role")
        != "sole_active_binding_02_prebinding_seal_ledger_after_this_amendment"
        or successor.get("required_event_count") != 4
        or successor.get("retired_event_or_digest_reuse") != "forbidden"
        or successor.get("current_byte_remeasurement") != "required"
    ):
        raise S10R4Error("successor prebinding-ledger authority mismatch")
    return {
        "amendment_record": amendment_record,
        "precommit_verdict_records": precommit_records,
        "postcommit_audit_record": postcommit_record,
        "retired_prebinding_attempt": retired_record,
        "successor_prebinding_ledger": {
            "path": successor_path,
            "role": successor["role"],
            "required_event_count": 4,
            "retired_event_or_digest_reuse": "forbidden",
            "current_byte_remeasurement": "required",
        },
    }


REPORT_RESOURCE_KEYS = {
    "historical_carried", "observed_activity_end_utc",
    "observed_activity_lower_bound_seconds", "observed_activity_start_utc",
    "peak_and_transient", "storage_bytes_before_reports",
    "whole_role_cpu_seconds", "whole_role_wall_seconds",
}
LOCK_REPORTED_RESOURCE_KEYS = {
    "observed_activity_end_utc", "observed_activity_lower_bound_seconds",
    "observed_activity_start_utc", "storage_bytes_before_reports",
    "whole_role_cpu_seconds", "whole_role_wall_seconds",
}
HISTORICAL_RESOURCE_KEYS = {
    "observed_activity_lower_bound_seconds", "storage_bytes_before_final_reports",
    "whole_role_cpu_seconds", "whole_role_wall_seconds",
}
PEAK_TRANSIENT_RESOURCE_KEYS = {
    "current_prelabel_build_bytes", "peak_storage_bytes",
    "preliminary_rejected_attempt_artifacts_created", "repair_archive_bytes",
    "repair_archive_present", "transient_s10r4_pycache_bytes_removed",
    "transient_s10r4_pycache_file_count_removed",
}
STORAGE_RESOURCE_KEYS = {
    "implementation", "prelabel_build", "prelabel_durable", "prelabel_fixtures",
    "prelabel_tests_and_repair_archive", "total",
}


def _nonnegative_number(value: Any, *, where: str, unknown_allowed: bool = False) -> None:
    if unknown_allowed and value == "UNKNOWN":
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise S10R4Error(f"{where} must be a nonnegative finite number")
    if not math.isfinite(value) or value < 0:
        raise S10R4Error(f"{where} must be a nonnegative finite number")


def _nonnegative_integer(value: Any, *, where: str, unknown_allowed: bool = False) -> None:
    if unknown_allowed and value == "UNKNOWN":
        return
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise S10R4Error(f"{where} must be a nonnegative integer")


def project_report_resources(
    resources: Mapping[str, Any], *, supplement: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Validate the immutable eight-key report shape and return six lock keys."""
    if not isinstance(resources, Mapping):
        raise S10R4Error("implementer report resources are not an object")
    require_exact_keys(resources, REPORT_RESOURCE_KEYS, where="implementer report resources")
    historical = resources["historical_carried"]
    if not isinstance(historical, Mapping):
        raise S10R4Error("implementer report historical resources are not an object")
    require_exact_keys(
        historical, HISTORICAL_RESOURCE_KEYS, where="implementer report historical resources"
    )
    authority = (
        load_contract_supplement() if supplement is None else supplement
    )["resources"]["carry_from_binding_01"]
    if dict(historical) != authority:
        raise S10R4Error("implementer report historical resources differ from supplement")

    peak = resources["peak_and_transient"]
    if not isinstance(peak, Mapping):
        raise S10R4Error("implementer report peak/transient resources are not an object")
    require_exact_keys(
        peak, PEAK_TRANSIENT_RESOURCE_KEYS, where="implementer report peak/transient resources"
    )
    _nonnegative_integer(
        peak["current_prelabel_build_bytes"], where="current_prelabel_build_bytes"
    )
    _nonnegative_integer(
        peak["peak_storage_bytes"], where="peak_storage_bytes", unknown_allowed=True
    )
    if not isinstance(peak["preliminary_rejected_attempt_artifacts_created"], bool):
        raise S10R4Error("preliminary rejected-attempt resource flag is not boolean")
    _nonnegative_integer(peak["repair_archive_bytes"], where="repair_archive_bytes")
    if not isinstance(peak["repair_archive_present"], bool):
        raise S10R4Error("repair archive resource flag is not boolean")
    _nonnegative_integer(
        peak["transient_s10r4_pycache_bytes_removed"],
        where="transient_s10r4_pycache_bytes_removed",
        unknown_allowed=True,
    )
    _nonnegative_integer(
        peak["transient_s10r4_pycache_file_count_removed"],
        where="transient_s10r4_pycache_file_count_removed",
    )

    storage = resources["storage_bytes_before_reports"]
    if not isinstance(storage, Mapping):
        raise S10R4Error("implementer report storage resources are not an object")
    require_exact_keys(storage, STORAGE_RESOURCE_KEYS, where="implementer report storage resources")
    for key in STORAGE_RESOURCE_KEYS:
        _nonnegative_integer(storage[key], where=f"storage_bytes_before_reports.{key}")
    if storage["total"] != sum(storage[key] for key in STORAGE_RESOURCE_KEYS - {"total"}):
        raise S10R4Error("implementer report storage total does not equal its exact components")

    _nonnegative_number(
        resources["observed_activity_lower_bound_seconds"],
        where="observed_activity_lower_bound_seconds",
    )
    for key in ("observed_activity_start_utc", "observed_activity_end_utc"):
        if not isinstance(resources[key], str) or not resources[key]:
            raise S10R4Error(f"implementer report {key} is not a nonempty string")
    for key in ("whole_role_cpu_seconds", "whole_role_wall_seconds"):
        _nonnegative_number(resources[key], where=key, unknown_allowed=True)
    projection = {
        "observed_activity_end_utc": resources["observed_activity_end_utc"],
        "observed_activity_lower_bound_seconds": resources[
            "observed_activity_lower_bound_seconds"
        ],
        "observed_activity_start_utc": resources["observed_activity_start_utc"],
        "storage_bytes_before_reports": dict(storage),
        "whole_role_cpu_seconds": resources["whole_role_cpu_seconds"],
        "whole_role_wall_seconds": resources["whole_role_wall_seconds"],
    }
    require_exact_keys(
        projection, LOCK_REPORTED_RESOURCE_KEYS, where="lock reported-resource projection"
    )
    return projection


def _run_git(
    arguments: Sequence[str], *, repo_root: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    effective_root = REPO_ROOT if repo_root is None else repo_root
    completed = subprocess.run(
        ["/usr/bin/git", "-c", "safe.directory=/src/rocm-libraries", *arguments],
        cwd=effective_root,
        env={"LC_ALL": "C", "PATH": "/usr/bin:/bin"},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    if check and completed.returncode != 0:
        raise S10R4Error(f"Git binding command failed: {' '.join(arguments)}")
    return completed


def _prebinding_path_record(relative: str) -> dict[str, Any]:
    path = REPO_ROOT / relative
    record = _binding_record(path)
    status_result = _run_git(["status", "--porcelain=v1", "--untracked-files=all", "--", relative])
    lines = status_result.stdout.decode("utf-8").splitlines()
    if len(lines) != 1:
        raise S10R4Error(f"prebinding Git state is absent or ambiguous: {relative}")
    status_code = lines[0][:2]
    if lines[0][3:] != relative:
        raise S10R4Error(f"prebinding Git status path association mismatch: {relative}")
    state = "untracked" if status_code == "??" else "modified"
    if state == "modified" and status_code == "  ":
        raise S10R4Error(f"prebinding implementation path is unexpectedly clean: {relative}")
    index_result = _run_git(["ls-files", "--stage", "--", relative])
    index_mode: str | None = None
    index_blob_oid: str | None = None
    if index_result.stdout:
        entries = index_result.stdout.decode("utf-8").splitlines()
        if len(entries) != 1:
            raise S10R4Error(f"prebinding index state is ambiguous: {relative}")
        prefix, stored_path = entries[0].split("\t", 1)
        index_mode, index_blob_oid, stage = prefix.split(" ")
        if stored_path != relative or stage != "0":
            raise S10R4Error(f"prebinding index association mismatch: {relative}")
    record["git_state"] = {
        "state": state,
        "status_code": status_code,
        "index_mode": index_mode,
        "index_blob_oid": index_blob_oid,
        "worktree_mode": record["mode"],
        "worktree_size_bytes": record["size_bytes"],
        "worktree_raw_sha256": record["raw_sha256"],
    }
    return record


def _committed_path_record(commit: str, relative: str) -> dict[str, Any]:
    listing = _run_git(["ls-tree", commit, "--", relative]).stdout.decode("utf-8").splitlines()
    if len(listing) != 1:
        raise S10R4Error(f"commit path is absent or ambiguous: {commit}:{relative}")
    prefix, stored_path = listing[0].split("\t", 1)
    mode, object_type, blob_oid = prefix.split(" ")
    if stored_path != relative or object_type != "blob":
        raise S10R4Error(f"commit path is not one blob: {commit}:{relative}")
    payload = _run_git(["show", f"{commit}:{relative}"]).stdout
    return {
        "path": relative,
        "git_mode": mode,
        "blob_oid": blob_oid,
        "size_bytes": len(payload),
        "raw_sha256": sha256_bytes(payload),
    }


def _event_digest(event: Mapping[str, Any]) -> str:
    return canonical_sha256({key: value for key, value in event.items() if key != "event_digest"})


def _ledger_digest(document: Mapping[str, Any]) -> str:
    return canonical_sha256({key: value for key, value in document.items() if key != "ledger_digest"})


def validate_audit_ledger(
    document: Mapping[str, Any],
    *,
    kind: str,
    require_count: int | None = None,
) -> list[dict[str, Any]]:
    require_exact_keys(
        document,
        {"schema_version", "checkpoint_id", "document_kind", "events", "ledger_digest"},
        where=f"{kind} audit ledger",
    )
    if document["schema_version"] != 1 or document["checkpoint_id"] != "S10R4" or document["document_kind"] != kind:
        raise S10R4Error(f"{kind} audit ledger identity mismatch")
    if document["ledger_digest"] != _ledger_digest(document):
        raise S10R4Error(f"{kind} audit ledger digest mismatch")
    events = document["events"]
    if not isinstance(events, list) or (require_count is not None and len(events) != require_count):
        raise S10R4Error(f"{kind} audit ledger event count mismatch")
    phases = PREBINDING_PHASES if kind == "prebinding_audit_ledger" else POST_COMMIT_PHASES
    if len(events) > len(phases):
        raise S10R4Error(f"{kind} audit ledger has an unknown extra event")
    previous: str | None = None
    validated: list[dict[str, Any]] = []

    def contains_value(value: Any, forbidden: set[str]) -> bool:
        if isinstance(value, Mapping):
            return any(contains_value(child, forbidden) for child in value.values())
        if isinstance(value, list):
            return any(contains_value(child, forbidden) for child in value)
        return isinstance(value, str) and value in forbidden

    for ordinal, event in enumerate(events):
        if not isinstance(event, dict):
            raise S10R4Error(f"{kind} audit event is not an object")
        require_exact_keys(event, AUDIT_EVENT_FIELDS, where=f"{kind} event {ordinal}")
        phase, verdict = phases[ordinal]
        if (
            event["ordinal"] != ordinal
            or event["phase"] != phase
            or event["verdict"] != verdict
            or event["previous_event_digest"] != previous
            or event["event_digest"] != _event_digest(event)
            or event["fresh"] is not True
            or event["implementation_participation"] is not False
            or event["findings"] != []
            or not isinstance(event["auditor_task_id"], str)
            or not event["auditor_task_id"].startswith("/root/")
            or not isinstance(event["created_utc"], str)
        ):
            raise S10R4Error(f"{kind} audit event chain/verdict/freshness mismatch at {ordinal}")
        if not isinstance(event["inputs"], dict):
            raise S10R4Error(f"{kind} audit event inputs are not an object")
        require_exact_keys(event["inputs"], AUDIT_INPUT_FIELDS[phase], where=f"{kind} {phase} inputs")
        if contains_value(
            event["inputs"], {event["event_digest"], document["ledger_digest"]}
        ):
            raise S10R4Error(
                f"{kind} event {ordinal} inputs contain a self-derived event/ledger digest"
            )
        previous = event["event_digest"]
        validated.append(dict(event))
    return validated


def _validate_active_prebinding_document(
    document: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    events = validate_audit_ledger(document, kind="prebinding_audit_ledger", require_count=4)
    recovery = _prebinding_recovery_lock_inputs(load_prebinding_recovery_amendment())
    retired = recovery["retired_prebinding_attempt"]
    retired_digests = {
        retired["ledger_digest"],
        *retired["event_digests"],
        # Binding-01 identities are carried by the committed supplement; its
        # empirical run-root ledger bytes are neither needed nor opened here.
        "3efbf295227089c17045a197ee56ea36a0d4cee5423341e4f03b89362d46c80a",
        "e02404f24b72a87b606cf7fc5a5bea9db0d8194f7481d917e88d7a53b4c2138d",
        "d593d13fddd9423077a2e11f56dc3808087c5afbbae8a3783a3f9f8f90863545",
    }
    if (
        document["ledger_digest"] in retired_digests
        or any(event["event_digest"] in retired_digests for event in events)
        or len({event["event_digest"] for event in events}) != 4
    ):
        raise S10R4Error("successor prebinding ledger reuses a retired event or ledger digest")
    return dict(document), events


def load_prebinding_audit_ledger(path: Path | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if path is None:
        path = PREBINDING_LEDGER_PATH
    if path != PREBINDING_LEDGER_PATH:
        raise S10R4Error(
            "only the exact audit-verdict-r2.json successor may be active prebinding authority"
        )
    if not path.exists():
        raise S10R4Error("active successor prebinding audit ledger is absent")
    return _validate_active_prebinding_document(load_json(path))


def load_post_commit_audit_ledger(path: Path | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if path is None:
        path = POST_COMMIT_LEDGER_PATH
    document = load_json(path)
    events = validate_audit_ledger(document, kind="post_commit_audit_ledger")
    if not events:
        raise S10R4Error("post-commit audit ledger lacks Phase-2 activation event")
    return document, events


TOOL_VERSION_SPECS = (
    ("git", "/usr/bin/git", ["/usr/bin/git", "--version"], (0,), "git version 2.43.0", False),
    ("env", "/usr/bin/env", ["/usr/bin/env", "--version"], (0,), "env (GNU coreutils) 9.4", False),
    ("python", "/opt/venv/bin/python3", ["/opt/venv/bin/python3", "--version"], (0,), "Python 3.12.3", False),
    ("pytest", "/opt/venv/bin/pytest", ["/opt/venv/bin/pytest", "--version"], (0,), "pytest 8.4.2", False),
    ("cmake", "/opt/venv/bin/cmake", ["/opt/venv/bin/cmake", "--version"], (0,), "cmake version 3.25.2", False),
    ("ninja", "/usr/local/bin/ninja", ["/usr/local/bin/ninja", "--version"], (0,), "1.11.1.git.kitware.jobserver-1", False),
    ("amdclang++", "/opt/rocm/bin/amdclang++", ["/opt/rocm/bin/amdclang++", "--version"], (0,), "AMD clang version 22.0.0git", True),
    ("hipcc", "/opt/rocm/bin/hipcc", ["/opt/rocm/bin/hipcc", "--version"], (0,), "HIP version: 7.2.53211-97f5574fe2", False),
    ("rocm-smi", "/opt/rocm/bin/rocm-smi", ["/opt/rocm/bin/rocm-smi", "--version"], (0,), "ROCM-SMI version: 4.0.0+97f5574fe2", False),
    ("strace", "/usr/bin/strace", ["/usr/bin/strace", "--version"], (0,), "strace -- version 6.8", False),
)


def _tool_version_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for tool_id, requested, argv, allowed, required_line, prefix in TOOL_VERSION_SPECS:
        resolved = Path(requested).resolve(strict=True)
        info = resolved.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not os.access(resolved, os.X_OK):
            raise S10R4Error(f"bound tool is not one executable ordinary file: {requested}")
        completed = subprocess.run(
            argv,
            cwd=Path("/src/rocm-libraries"),
            env=FIXED_ENVIRONMENT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
        if completed.returncode not in allowed:
            raise S10R4Error(f"tool version command returned outside its allowlist: {tool_id}")
        combined = completed.stdout if completed.stdout else completed.stderr
        first_line = combined.decode("utf-8", errors="strict").splitlines()[0] if combined else ""
        version_matches = first_line.startswith(required_line) if prefix else first_line == required_line
        if not version_matches:
            raise S10R4Error(f"tool version first line mismatch: {tool_id}: {first_line!r}")
        records.append(
            {
                "tool_id": tool_id,
                "requested_path": requested,
                "resolved_path": resolved.as_posix(),
                "mode": stat.S_IMODE(info.st_mode),
                "size_bytes": info.st_size,
                "binary_sha256": raw_sha256(resolved),
                "version_argv": argv,
                "allowed_returncodes": list(allowed),
                "returncode": completed.returncode,
                "stdout_sha256": sha256_bytes(completed.stdout),
                "stderr_sha256": sha256_bytes(completed.stderr),
                "first_line": first_line,
            }
        )
    return records


def _commit_resolution(commit: str) -> dict[str, Any]:
    argv = ["/usr/bin/git", "-c", "safe.directory=/src/rocm-libraries", "cat-file", "-e", f"{commit}^{{commit}}"]
    completed = subprocess.run(
        argv,
        cwd=Path("/src/rocm-libraries"),
        env=FIXED_ENVIRONMENT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise S10R4Error(f"pinned commit does not resolve: {commit}")
    return {
        "commit": commit,
        "argv": argv,
        "returncode": 0,
        "stdout_sha256": sha256_bytes(completed.stdout),
        "stderr_sha256": sha256_bytes(completed.stderr),
    }


def pinned_source_declarations(contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the contract-ordered exact eight materialized source declarations."""
    identity = contract["source_and_input_identity"]
    declared: list[dict[str, Any]] = []
    for row in identity["normal_workflow_sources"]:
        declared.append(
            {
                "source_role": "normal_workflow_source",
                "repository_path": row["path"],
                "required_symbols": [row["required_symbol"]],
                "expected_git_blob_oid": row["blob"],
            }
        )
    formocast = identity["native_formocast"]
    for role, path_key, blob_key in (
        ("native_formocast_source", "source_path", "source_blob"),
        ("native_formocast_header", "header_path", "header_blob"),
    ):
        declared.append(
            {
                "source_role": role,
                "repository_path": formocast[path_key],
                "required_symbols": [formocast["symbol"]],
                "expected_git_blob_oid": formocast[blob_key],
            }
        )
    runtime = identity["runtime_queue"]
    for role, path_key, blob_key in (
        ("runtime_queue_source", "source_path", "source_blob"),
        ("runtime_queue_header", "header_path", "header_blob"),
    ):
        declared.append(
            {
                "source_role": role,
                "repository_path": runtime[path_key],
                "required_symbols": list(runtime["symbols"]),
                "expected_git_blob_oid": runtime[blob_key],
            }
        )
    if len(declared) != 8:
        raise S10R4Error("contract materialized-source declaration is not the exact eight-set")
    paths = [row["repository_path"] for row in declared]
    blobs = [row["expected_git_blob_oid"] for row in declared]
    if len(set(paths)) != 8 or len(set(blobs)) != 8:
        raise S10R4Error("contract materialized-source paths/blobs are not unique")
    return declared


def _source_realization(contract: Mapping[str, Any], native_build_manifest: Path) -> dict[str, Any]:
    pinned_root = REPO_ROOT / "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/artifacts/prelabel-build/pinned-source"
    source_records: list[dict[str, Any]] = []
    for declared in pinned_source_declarations(contract):
        materialized = pinned_root / declared["repository_path"]
        info = materialized.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise S10R4Error(
                f"pinned materialized source is not ordinary: {declared['repository_path']}"
            )
        data = materialized.read_bytes()
        blob_oid = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
        if blob_oid != declared["expected_git_blob_oid"]:
            raise S10R4Error(f"pinned source blob mismatch: {declared['repository_path']}")
        source_records.append(
            {
                **declared,
                "materialized_path": materialized.resolve(strict=True).as_posix(),
                "mode": stat.S_IMODE(info.st_mode),
                "link_count": info.st_nlink,
                "size_bytes": info.st_size,
                "raw_sha256": sha256_bytes(data),
            }
        )
    actual_yaml_declared = contract["source_and_input_identity"]["actual_yaml"]
    actual_yaml_path = REPO_ROOT / actual_yaml_declared["path"]
    yaml_data = actual_yaml_path.read_bytes()
    actual_yaml = {
        "path": actual_yaml_declared["path"],
        "git_blob_oid": hashlib.sha1(b"blob " + str(len(yaml_data)).encode("ascii") + b"\0" + yaml_data).hexdigest(),
        "mode": stat.S_IMODE(actual_yaml_path.stat(follow_symlinks=False).st_mode),
        "size_bytes": len(yaml_data),
        "raw_sha256": sha256_bytes(yaml_data),
    }
    if actual_yaml["raw_sha256"] != actual_yaml_declared["sha256"]:
        raise S10R4Error("actual YAML binding mismatch")
    native_build = load_json(native_build_manifest)
    if native_build.get("native_executed") is not False:
        raise S10R4Error("prelabel native build manifest claims execution")
    prelabel_summary_path = REPO_ROOT / "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/artifacts/prelabel-fixtures/prelabel-build-summary.json"
    prelabel_summary = load_json(prelabel_summary_path)
    if prelabel_summary.get("source_identity", {}).get("files") != source_records:
        raise S10R4Error("prelabel summary does not bind the exact ordered eight materialized sources")
    return {
        "ductile_commit_resolution": _commit_resolution(contract["source_and_input_identity"]["ductile"]["commit"]),
        "geko_commit_resolution": _commit_resolution(contract["source_and_input_identity"]["geko"]["commit"]),
        "pinned_source_records": source_records,
        "actual_yaml": actual_yaml,
        "tool_records": _tool_version_records(),
        "llvm_executable_closure": llvm_executable_closure(),
        "native_build_manifest": _binding_record(native_build_manifest),
        "native_build_products": native_build["products"],
        "prelabel_summary": _binding_record(prelabel_summary_path),
        "container_realization": _container_realization(),
        "gpu_selection_predicate": {
            "projection": contract["gpu_correctness_and_noise"]["card_selection"]["eligible_predicate"],
            "projection_sha256": canonical_sha256(contract["gpu_correctness_and_noise"]["card_selection"]["eligible_predicate"]),
        },
        "in_process_boundaries": [
            "strict_parsing_schema_hashing", "frame_replay", "safe_archive_extraction",
            "selection", "classification_seal", "summary_construction", "state_projection",
            "decision", "raw_to_decision_recomputation",
        ],
    }


def _device_node_record(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": path.as_posix(), "present": False, "type": None, "mode": None, "major": None, "minor": None}
    info = path.stat(follow_symlinks=False)
    if stat.S_ISCHR(info.st_mode):
        kind = "character_device"
    elif stat.S_ISDIR(info.st_mode):
        kind = "directory"
    else:
        kind = "other"
    return {
        "path": path.as_posix(), "present": True, "type": kind,
        "mode": stat.S_IMODE(info.st_mode),
        "major": os.major(info.st_rdev) if stat.S_ISCHR(info.st_mode) else None,
        "minor": os.minor(info.st_rdev) if stat.S_ISCHR(info.st_mode) else None,
    }


def _container_realization() -> dict[str, Any]:
    mountinfo = Path("/proc/self/mountinfo").read_bytes()
    matches = [line for line in mountinfo.splitlines() if len(line.split()) > 5 and line.split()[4] == b"/src"]
    if len(matches) != 1:
        raise S10R4Error("container /src mount observation is absent or ambiguous")
    fields = matches[0].decode("utf-8").split()
    separator = fields.index("-")
    mount_options = fields[5].split(",")
    if "rw" not in mount_options:
        raise S10R4Error("container /src mount is not read/write")
    nodes = [_device_node_record(Path("/dev/kfd")), _device_node_record(Path("/dev/dri"))]
    dri = Path("/dev/dri")
    if dri.is_dir():
        nodes.extend(_device_node_record(path) for path in sorted(dri.iterdir(), key=lambda item: os.fsencode(item.name)))
    return {
        "container_name": "perlee",
        "host_path": "/data1/perlee",
        "container_path": "/src",
        "mode": "rw",
        "mount_observation": {
            "mount_point": fields[4], "mount_options": mount_options,
            "filesystem_type": fields[separator + 1], "source": fields[separator + 2],
            "record_sha256": sha256_bytes(matches[0]),
        },
        "device_surface": nodes,
    }


def _absence_observation(contract: Mapping[str, Any], *, include_lock: bool) -> dict[str, Any]:
    durable = [
        {"path": relative, "absent": not (REPO_ROOT / relative).exists()}
        for relative in contract["prelabel_absence"]["durable_paths"]
    ]
    raw = [
        {"path": relative, "absent": not (REPO_ROOT / relative).exists()}
        for relative in contract["prelabel_absence"]["raw_scopes"]
    ]
    lock_relative = contract["identity"]["effective_lock_path"]
    lock_absent = not (REPO_ROOT / lock_relative).exists()
    if any(not row["absent"] for row in [*durable, *raw]) or (include_lock and not lock_absent):
        raise S10R4Error("formal/outcome/raw/lock absence observation failed")
    return {
        "durable": durable,
        "raw_scopes": raw,
        "lock": {"path": lock_relative, "absent": lock_absent},
        "projection_sha256": canonical_sha256({"durable": durable, "raw_scopes": raw, "lock": {"path": lock_relative, "absent": lock_absent}}),
    }


def _historical_activation_absence_expectation(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return schema/path rules only; this is not an activation observation."""
    return {
        "event_input_field": "formal_absence",
        "durable_paths": list(contract["prelabel_absence"]["durable_paths"]),
        "raw_scope_paths": list(contract["prelabel_absence"]["raw_scopes"]),
        "lock_path": contract["identity"]["effective_lock_path"],
        "formal_absent_value": True,
        "lock_absent_value": False,
        "projection_rule": "sha256_canonical_json_of_exact_durable_raw_scopes_and_lock_rows",
        "validation_rule": "immutable_ordinal_0_historical_record_without_live_absence_remeasurement",
    }


def _validate_historical_activation_absence(
    observation: Mapping[str, Any], contract: Mapping[str, Any]
) -> None:
    """Validate the immutable ordinal-0 observation without consulting live paths."""
    require_exact_keys(
        observation,
        {"durable", "raw_scopes", "lock", "projection_sha256"},
        where="historical activation absence",
    )
    expectation = _historical_activation_absence_expectation(contract)
    durable = [
        {"path": relative, "absent": expectation["formal_absent_value"]}
        for relative in expectation["durable_paths"]
    ]
    raw_scopes = [
        {"path": relative, "absent": expectation["formal_absent_value"]}
        for relative in expectation["raw_scope_paths"]
    ]
    lock = {
        "path": expectation["lock_path"],
        "absent": expectation["lock_absent_value"],
    }
    expected_projection = {"durable": durable, "raw_scopes": raw_scopes, "lock": lock}
    if (
        observation["durable"] != durable
        or observation["raw_scopes"] != raw_scopes
        or observation["lock"] != lock
        or observation["projection_sha256"] != canonical_sha256(expected_projection)
    ):
        raise S10R4Error("post-binding historical activation absence mismatch")


def _unrelated_worktree_observation(phase2_paths: Sequence[str]) -> dict[str, Any]:
    completed = _run_git(["status", "--porcelain=v1", "--untracked-files=all"])
    lines = completed.stdout.decode("utf-8").splitlines()
    phase2 = set(phase2_paths)
    prebinding_ledger = PREBINDING_LEDGER_PATH.relative_to(REPO_ROOT).as_posix()
    unrelated = []
    for line in lines:
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path not in phase2 and path != prebinding_ledger:
            unrelated.append(line)
    staged_set = set(
        _run_git(["diff", "--cached", "--name-only", "--"]).stdout.decode("utf-8").splitlines()
    )
    staged_phase2 = [relative for relative in phase2_paths if relative in staged_set]
    if staged_phase2:
        raise S10R4Error("prebinding Phase-2 paths are unexpectedly staged")
    return {
        "status_lines": unrelated,
        "status_projection_sha256": canonical_sha256(unrelated),
        "attribution": "UNKNOWN_EXTERNAL_PRESERVED",
        "staged_phase2_paths": staged_phase2,
    }


def _boundary_realization(contract: Mapping[str, Any]) -> dict[str, Any]:
    boundaries = contract["write_boundaries"]
    return {
        "implementation_paths": list(boundaries["implementation_exact_paths"]),
        "prelabel_paths": list(boundaries["prelabel_durable_exact_paths"][:-1]),
        "formal_paths": list(boundaries["formal_durable_exact_paths"]),
        "delivery_paths": list(contract["seal_protocol"]["phase2"]["exact_commit_paths"]),
        "forbidden": list(boundaries["forbidden"]),
        "implementation_projection_sha256": canonical_sha256(boundaries["implementation_exact_paths"]),
        "prelabel_projection_sha256": canonical_sha256(boundaries["prelabel_durable_exact_paths"][:-1]),
        "formal_projection_sha256": canonical_sha256(boundaries["formal_durable_exact_paths"]),
        "delivery_projection_sha256": canonical_sha256(contract["seal_protocol"]["phase2"]["exact_commit_paths"]),
        "forbidden_projection_sha256": canonical_sha256(boundaries["forbidden"]),
    }


def _initial_stage_projection(contract: Mapping[str, Any]) -> dict[str, Any]:
    absence = _absence_observation(contract, include_lock=False)
    return {
        "stage_id": "census_A",
        "resumable_prefix_count": 0,
        "terminal_branch": None,
        "blocker_present": False,
        "formal_absence_projection_sha256": absence["projection_sha256"],
    }


def _selected_revision_record() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for raw_line in PLAN_A_REVISION_LEDGER_PATH.read_bytes().splitlines():
        record = strict_json_bytes(raw_line)
        records.append(record)
    if [record.get("revision") for record in records] != [13, 14, 15, 16]:
        raise S10R4Error("Plan-A revision ledger is not the exact append-only 13/14/15/16 lineage")
    expected_chain = (
        (13, "f577e0f7fc272d2c950793e0218640a5306a6634b516ad69eb563c5f1b79eab8", 42589,
         12, "c2d8b709f64d80bbb0b3a169397d689ec2e6faf7d974723d6d8688938bcda4d1"),
        (14, "61ccdcd9003ac45f85da438a2fc1cb87d216153d885fbe8f25a7ecf3eb4ca285", 44012,
         13, "f577e0f7fc272d2c950793e0218640a5306a6634b516ad69eb563c5f1b79eab8"),
        (15, PLAN_A_PREDECESSOR["raw_sha256"], PLAN_A_PREDECESSOR["size_bytes"],
         14, "61ccdcd9003ac45f85da438a2fc1cb87d216153d885fbe8f25a7ecf3eb4ca285"),
        (16, PLAN_A_RAW_SHA256, PLAN_A_SIZE_BYTES, 15, PLAN_A_PREDECESSOR["raw_sha256"]),
    )
    for record, (revision, digest, size, previous_revision, previous_digest) in zip(
        records, expected_chain
    ):
        if (
            record.get("revision") != revision
            or record.get("plan_a_raw_sha256") != digest
            or record.get("plan_a_size_bytes") != size
            or record.get("previous_revision") != previous_revision
            or record.get("previous_raw_sha256") != previous_digest
        ):
            raise S10R4Error("Plan-A revision ledger chain mismatch")
    selected = records[-1]
    expected = {
        "author_task_id", "checkpoint_id", "contract_raw_sha256", "created_utc", "direct_evidence",
        "outcome_access", "plan_a_path", "plan_a_raw_sha256", "plan_a_size_bytes",
        "previous_raw_sha256", "previous_revision", "revision", "state", "trigger",
    }
    require_exact_keys(selected, expected, where="selected Plan-A revision record")
    if (
        selected["checkpoint_id"] != "S10R4"
        or selected["revision"] != PLAN_A_REVISION
        or selected["plan_a_raw_sha256"] != PLAN_A_RAW_SHA256
        or selected["plan_a_size_bytes"] != PLAN_A_SIZE_BYTES
        or selected["previous_revision"] != PLAN_A_PREDECESSOR["revision"]
        or selected["previous_raw_sha256"] != PLAN_A_PREDECESSOR["raw_sha256"]
    ):
        raise S10R4Error("selected Plan-A revision record identity mismatch")
    return selected


def _governance_base(
    contract: Mapping[str, Any],
    auditor_task_id: str,
    phase2_paths: Sequence[str],
) -> dict[str, Any]:
    report = load_json(IMPLEMENTER_REPORT_PATHS[1])
    role_records = [
        {
            "role": "original_design_reviewer_a", "task_id": "UNKNOWN_HISTORICAL",
            "fresh": False, "implementation_participation": False,
        },
        {
            "role": "original_design_reviewer_b", "task_id": "UNKNOWN_HISTORICAL",
            "fresh": False, "implementation_participation": False,
        },
        {
            "role": "adversarial_auditor", "task_id": auditor_task_id,
            "fresh": False, "implementation_participation": False,
        },
        {
            "role": "implementer", "task_id": "/root/s10r4_fresh_implementer",
            "fresh": False, "implementation_participation": True,
        },
        {
            "role": "binding_recovery_operational_reviewer",
            "task_id": "/root/s10r4_failure_reviewer_a",
            "fresh": False,
            "implementation_participation": False,
        },
        {
            "role": "fresh_verifier", "task_id": None,
            "fresh": True, "implementation_participation": False,
        },
    ]
    carried = load_contract_supplement()["resources"]["carry_from_binding_01"]
    report_resources = report["resources"] if "resources" in report else None
    projected_resources = project_report_resources(report_resources)
    resources = {
        "planning_policy": contract["resources"],
        "historical_carried": dict(carried),
        "implementation_reported": projected_resources,
        "whole_role_cpu_seconds": projected_resources["whole_role_cpu_seconds"],
        "whole_role_wall_seconds": projected_resources["whole_role_wall_seconds"],
    }
    base = {
        "risk_tier": "R3",
        "repair_numeric_stop_cap": None,
        "role_records": role_records,
        "projected_role_thread_count": 6,
        "still_fresh_verifier_thread_count": 1,
        "resources": resources,
        "boundaries": _boundary_realization(contract),
        "absence": _absence_observation(contract, include_lock=True),
        "baseline": _binding_record(BASELINE_PATH),
        "unrelated_worktree_observation": _unrelated_worktree_observation(phase2_paths),
        "expected_stage_projection": _initial_stage_projection(contract),
        "outcome_document_policy_projection_sha256": canonical_sha256(contract["outcome_document_policy"]),
        "downstream_handoff_projection_sha256": canonical_sha256(contract["downstream_handoff"]),
    }
    _validate_governance_base(base)
    return base


def _validate_governance_base(base: Mapping[str, Any]) -> None:
    """Reject any prebinding-ledger identity from the non-self-derived base."""
    forbidden_keys = {
        "prebinding_audit", "prebinding_ledger", "prebinding_ledger_path",
        "ledger_record", "ledger_digest", "event_digest", "event_digests",
        "final_event_digest",
    }
    ledger_path = PREBINDING_LEDGER_PATH.relative_to(REPO_ROOT).as_posix()

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key in forbidden_keys or key.startswith("prebinding_audit"):
                    raise S10R4Error("governance base contains a self-derived audit-ledger field")
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif value == ledger_path or value == PREBINDING_LEDGER_PATH.as_posix():
            raise S10R4Error("governance base contains the prebinding audit-ledger path")

    visit(base)


def _validate_prebinding_ledger_inputs(
    events: Sequence[Mapping[str, Any]],
    *,
    contract: Mapping[str, Any],
    plan_a_path: Path,
    plan_b_path: Path,
    plan_b_freeze_path: Path,
    implementation_records: Sequence[Mapping[str, Any]],
    prelabel_records: Sequence[Mapping[str, Any]],
    source_realization: Mapping[str, Any],
    governance_base: Mapping[str, Any],
    phase2_paths: Sequence[str],
    lock_input_projection_hashes: Mapping[str, Any],
    prebinding_recovery_inputs: Mapping[str, Any],
) -> None:
    contract_record = _base_contract_record()
    binding_02_inputs = _supplement_lock_inputs(load_contract_supplement())
    plan_a_record = _binding_record(plan_a_path)
    plan_b_record = _binding_record(plan_b_path)
    if plan_a_record["raw_sha256"] != PLAN_A_RAW_SHA256 or plan_a_record["size_bytes"] != PLAN_A_SIZE_BYTES:
        raise S10R4Error("current Plan-A revision 16 identity mismatch")
    phase1 = events[0]["inputs"]
    _require_binding_record(phase1["diagnostic_audit_record"], where="Phase-1 diagnostic audit")
    phase1_parent = _run_git(["rev-parse", f"{PHASE1_COMMIT_OID}^"]).stdout.decode("ascii").strip()
    phase1_record = _committed_path_record(PHASE1_COMMIT_OID, contract["identity"]["contract_path"])
    if (
        phase1["authority_commit_oid"] != contract["identity"]["authority_commit"]
        or phase1["contract_record"] != contract_record
        or phase1["phase1_commit_oid"] != PHASE1_COMMIT_OID
        or phase1["phase1_parent_oid"] != phase1_parent
        or phase1["phase1_diff_paths"] != [contract["identity"]["contract_path"]]
        or phase1["phase1_committed_record"] != phase1_record
        or phase1["supplement_record"] != binding_02_inputs["supplement_record"]
        or phase1["supplement_commit_oid"] != SUPPLEMENT_PHASE1_COMMIT_OID
        or phase1["supplement_postcommit_audit_record"]
        != binding_02_inputs["supplement_postcommit_audit_record"]
        or phase1["supplement_precommit_verdict_records"]
        != binding_02_inputs["supplement_precommit_verdict_records"]
        or phase1["recovery_authority_record"]
        != binding_02_inputs["recovery_authority_record"]
        or phase1["recovery_authority_audit_record"]
        != binding_02_inputs["recovery_authority_postcommit_audit_record"]
        or phase1["binding_01_revert_record"]
        != binding_02_inputs["binding_01_retirement"]["revert_audit_record"]
        or phase1["prebinding_recovery_amendment_record"]
        != prebinding_recovery_inputs["amendment_record"]
        or phase1["prebinding_recovery_precommit_verdict_records"]
        != prebinding_recovery_inputs["precommit_verdict_records"]
        or phase1["prebinding_recovery_postcommit_audit_record"]
        != prebinding_recovery_inputs["postcommit_audit_record"]
    ):
        raise S10R4Error("prebinding Phase-1 audit inputs differ from current authority")
    plans = events[1]["inputs"]
    if not isinstance(plans["diagnostic_audit_records"], list):
        raise S10R4Error("Plan-A parity diagnostic audit records are not a list")
    for index, record in enumerate(plans["diagnostic_audit_records"]):
        _require_binding_record(record, where=f"Plan-A diagnostic audit record {index}")
    if (
        plans["authority_commit_oid"] != contract["identity"]["authority_commit"]
        or plans["contract_record"] != contract_record
        or plans["plan_a_record"] != {**plan_a_record, "revision": PLAN_A_REVISION}
        or plans["predecessor_plan_a"] != PLAN_A_PREDECESSOR
        or plans["plan_a_revision_ledger_record"] != _binding_record(PLAN_A_REVISION_LEDGER_PATH)
        or plans["selected_revision_record"] != _selected_revision_record()
        or plans["plan_b_record"] != plan_b_record
        or plans["plan_b_freeze_record"] != _binding_record(plan_b_freeze_path)
        or plans["append_only_adjudication_record"] != _binding_record(ADJUDICATION_PATH)
        or plans["retired_prebinding_attempt_record"]
        != prebinding_recovery_inputs["retired_prebinding_attempt"]
    ):
        raise S10R4Error("prebinding Plan-A parity inputs differ from current plan bindings")
    implementation = events[2]["inputs"]
    self_checks = implementation["self_checks"]
    if not isinstance(self_checks, list) or len(self_checks) != 4:
        raise S10R4Error("implementation audit must bind exactly four self-check records")
    expected_self_check_argv = (
        ("validate-contract", materialize_command_template("validate_contract")),
        ("prepare-prelabel", materialize_command_template("prepare_prelabel")),
        ("verify-prelabel", materialize_command_template("verify_prelabel")),
        (
            "pytest",
            [
                "/opt/venv/bin/pytest", "-q",
                "projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10r4_entry.py",
            ],
        ),
    )
    for index, (record, (command_id, argv)) in enumerate(zip(self_checks, expected_self_check_argv)):
        if not isinstance(record, dict):
            raise S10R4Error(f"self-check record {index} is not an object")
        require_exact_keys(
            record,
            {"command_id", "argv", "exit_code", "stdout_sha256", "stderr_sha256", "key_counts"},
            where=f"self-check record {index}",
        )
        require_exact_keys(
            record["key_counts"], {"stdout_json_root_key_count", "pytest_passed_count"},
            where=f"self-check record {index} key counts",
        )
        key_counts = record["key_counts"]
        json_count = key_counts["stdout_json_root_key_count"]
        pytest_count = key_counts["pytest_passed_count"]
        if (
            record["command_id"] != command_id
            or record["argv"] != argv
            or record["exit_code"] != 0
            or not isinstance(record["stdout_sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", record["stdout_sha256"]) is None
            or not isinstance(record["stderr_sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", record["stderr_sha256"]) is None
            or (index < 3 and (not isinstance(json_count, int) or json_count <= 0 or pytest_count is not None))
            or (index == 3 and (json_count is not None or not isinstance(pytest_count, int) or pytest_count <= 0))
        ):
            raise S10R4Error(f"self-check record {index} differs from the exact command/exit/key-count binding")
    report_records = [_binding_record(path) for path in IMPLEMENTER_REPORT_PATHS]
    formal_absence = _absence_observation(contract, include_lock=True)
    if (
        implementation["contract_record"] != contract_record
        or implementation["plan_a_record"] != {**plan_a_record, "revision": PLAN_A_REVISION}
        or implementation["plan_b_record"] != plan_b_record
        or implementation["implementation_records"] != list(implementation_records)
        or implementation["prelabel_records"] != list(prelabel_records)
        or implementation["implementer_report_records"] != report_records
        or implementation["implementation_projection_sha256"] != canonical_sha256(implementation_records)
        or implementation["prelabel_projection_sha256"] != canonical_sha256(prelabel_records)
        or implementation["formal_absence"] != formal_absence
    ):
        raise S10R4Error("prebinding implementation parity inputs differ from current bytes")
    final = events[3]["inputs"]
    if (
        final["authority_commit_oid"] != contract["identity"]["authority_commit"]
        or final["contract_record"] != contract_record
        or final["plan_a_record"] != {**plan_a_record, "revision": PLAN_A_REVISION}
        or final["plan_b_record"] != plan_b_record
        or final["lock_input_projection_hashes"] != lock_input_projection_hashes
        or final["source_realization"] != source_realization
        or final["tool_realization"] != source_realization["tool_records"]
        or final["container_device_realization"] != source_realization["container_realization"]
        or final["role_resource_boundary_realization"] != governance_base
        or final["expected_phase2_paths"] != list(phase2_paths)
        or final["existing_phase2_records"] != [*implementation_records, *prelabel_records]
        or final["formal_absence"] != formal_absence
        or final["unrelated_worktree_observation"] != governance_base["unrelated_worktree_observation"]
        or final["lock_output_absence"] != {"path": contract["identity"]["effective_lock_path"], "absent": True}
        or final["prebinding_recovery_inputs"] != prebinding_recovery_inputs
    ):
        raise S10R4Error("final prebinding audit inputs differ from current realization")


def _command_template_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for command_id in sorted(COMMAND_TEMPLATES):
        placeholders = sorted(COMMAND_PLACEHOLDERS[command_id])
        concrete: list[list[str]] = []
        if not placeholders:
            concrete = [materialize_command_template(command_id)]
        elif placeholders == ["pass_id"]:
            concrete = [
                materialize_command_template(command_id, {"pass_id": pass_id})
                for pass_id in ("A", "B")
            ]
        records.append(
            {
                "command_id": command_id,
                "template": list(COMMAND_TEMPLATES[command_id]),
                "placeholders": placeholders,
                "concrete_allowlist": concrete,
            }
        )
    return records


def _prospective_json_binding_record(path: Path, document: Mapping[str, Any]) -> dict[str, Any]:
    payload = canonical_json(document, newline=True)
    return {
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "mode": 0o644,
        "size_bytes": len(payload),
        "raw_sha256": sha256_bytes(payload),
        "canonical_sha256": canonical_sha256(document),
    }


def _construct_effective_lock_v11(
    *,
    output: Path,
    plan_a_path: Path,
    plan_b_path: Path,
    plan_b_freeze_path: Path,
    audit_verdict_path: Path,
    native_build_manifest: Path,
    prebinding_ledger: Mapping[str, Any] | None,
    write: bool,
) -> dict[str, Any]:
    contract = validate_phase1()
    expected_output = REPO_ROOT / contract["identity"]["effective_lock_path"]
    if output.resolve(strict=False) != expected_output.resolve(strict=False) or output.exists():
        raise S10R4Error("effective lock output is not the absent production exact path")
    if audit_verdict_path != PREBINDING_LEDGER_PATH:
        raise S10R4Error("effective lock must use only the exact audit-verdict-r2.json successor")
    if (
        raw_sha256(plan_a_path) != PLAN_A_RAW_SHA256
        or plan_a_path.stat().st_size != PLAN_A_SIZE_BYTES
    ):
        raise S10R4Error("current Plan-A revision 16 identity mismatch")
    if prebinding_ledger is not None:
        if audit_verdict_path.exists():
            raise S10R4Error("in-memory preflight requires the successor ledger path absent")
        ledger, events = _validate_active_prebinding_document(prebinding_ledger)
        ledger_record = _prospective_json_binding_record(audit_verdict_path, ledger)
    else:
        ledger, events = load_prebinding_audit_ledger(audit_verdict_path)
        ledger_record = _binding_record(audit_verdict_path)
    implementation_paths = list(contract["write_boundaries"]["implementation_exact_paths"])
    prelabel_paths = list(contract["write_boundaries"]["prelabel_durable_exact_paths"][:-1])
    phase2_paths = list(contract["seal_protocol"]["phase2"]["exact_commit_paths"])
    if phase2_paths != [*implementation_paths[:-1], *prelabel_paths, contract["identity"]["effective_lock_path"], implementation_paths[-1]]:
        raise S10R4Error("contract Phase-2 exact path order is not the frozen 19-path projection")
    implementation_records = [_prebinding_path_record(relative) for relative in implementation_paths]
    prelabel_records = [_prebinding_path_record(relative) for relative in prelabel_paths]
    frame = load_json(REPO_ROOT / prelabel_paths[0])
    raw_inventory = frame["raw_inventory"]
    if (
        raw_inventory.get("ordinary_file_count") != len(raw_inventory.get("records", []))
        or raw_inventory.get("projection_sha256") != canonical_sha256(raw_inventory["records"])
    ):
        raise S10R4Error("exact-frame raw inventory projection mismatch")
    source_realization = _source_realization(contract, native_build_manifest)
    governance_base = _governance_base(contract, events[3]["auditor_task_id"], phase2_paths)
    _validate_governance_base(governance_base)
    phase1 = {
        "contract_record": _base_contract_record(),
        "composed_contract_projection_sha256": canonical_sha256(contract),
        "phase1_contract_commit_oid": PHASE1_COMMIT_OID,
        "phase1_post_commit_audit": {
            "ledger_path": audit_verdict_path.relative_to(REPO_ROOT).as_posix(),
            "event_ordinal": 0,
            "event_digest": events[0]["event_digest"],
        },
        "authority_records": [
            {
                "id": row["id"],
                **_binding_record(REPO_ROOT / row["path"]),
            }
            for row in contract["authority"]["committed_projection"]
        ],
        "workflow_authority_projection_sha256": canonical_sha256(contract["workflow_authority"]),
        "scientific_oracle_projection_sha256": canonical_sha256(contract["scientific_oracle"]),
    }
    plan_a_record = {**_binding_record(plan_a_path), "revision": PLAN_A_REVISION}
    plans = {
        "plan_a": plan_a_record,
        "predecessor_plan_a": PLAN_A_PREDECESSOR,
        "plan_a_revision_ledger": _binding_record(PLAN_A_REVISION_LEDGER_PATH),
        "selected_revision_record": _selected_revision_record(),
        "plan_b": _binding_record(plan_b_path),
        "plan_b_freeze": _binding_record(plan_b_freeze_path),
        "parity_audit": {
            "ledger_path": audit_verdict_path.relative_to(REPO_ROOT).as_posix(),
            "event_ordinal": 1,
            "event_digest": events[1]["event_digest"],
        },
    }
    implementation = {
        "exact_path_count": 15,
        "files": implementation_records,
        "schema": next(row for row in implementation_records if row["path"].endswith("s10r4-entry.schema.json")),
        "unit_test": next(row for row in implementation_records if row["path"].endswith("test_ductile_s10r4_entry.py")),
        "command_templates": _command_template_records(),
        "environment": dict(FIXED_ENVIRONMENT),
        "timeouts": {
            "independent_reproduction": 7200,
            "census_child": 7200,
            "mapping_attempt": 7200,
            "native_fixture_command": 7200,
            "gpu_allocation_process_snapshot_command": 60,
            "correctness_cell_attempt": 7200,
            "noise_cell": 7200,
        },
        "expected_phase2_paths": phase2_paths,
    }
    predecessor = {
        "predecessor_input_hashes": contract["predecessor_frame"]["committed_inputs"],
        "predecessor_raw_root": contract["predecessor_frame"]["raw_frame"]["container_root"],
        "raw_inventory": raw_inventory,
        "raw_inventory_count": raw_inventory["ordinary_file_count"],
        "raw_inventory_size_bytes": sum(int(row["size_bytes"]) for row in raw_inventory["records"]),
        "raw_inventory_projection_sha256": raw_inventory["projection_sha256"],
        "exact_frame_registry": _binding_record(REPO_ROOT / prelabel_paths[0]),
        "size_registry": _binding_record(REPO_ROOT / prelabel_paths[1]),
        "native_fixture": _binding_record(REPO_ROOT / prelabel_paths[2]),
    }
    binding_02_inputs = _supplement_lock_inputs(load_contract_supplement())
    prebinding_recovery_inputs = _prebinding_recovery_lock_inputs(
        load_prebinding_recovery_amendment()
    )
    lock_input_projection_hashes = {
        "phase1": canonical_sha256(phase1),
        "plans": canonical_sha256(plans),
        "implementation": canonical_sha256(implementation),
        "predecessor_and_registries": canonical_sha256(predecessor),
        "source_realization": canonical_sha256(source_realization),
        "governance_base": canonical_sha256(governance_base),
        "binding_02_inputs": canonical_sha256(binding_02_inputs),
        "prebinding_recovery_inputs": canonical_sha256(prebinding_recovery_inputs),
    }
    _validate_prebinding_ledger_inputs(
        events,
        contract=contract,
        plan_a_path=plan_a_path,
        plan_b_path=plan_b_path,
        plan_b_freeze_path=plan_b_freeze_path,
        implementation_records=implementation_records,
        prelabel_records=prelabel_records,
        source_realization=source_realization,
        governance_base=governance_base,
        phase2_paths=phase2_paths,
        lock_input_projection_hashes=lock_input_projection_hashes,
        prebinding_recovery_inputs=prebinding_recovery_inputs,
    )
    lifecycle = {
        "pre_audit": {
            "execution_status": "blocked", "checkpoint_state": "BLOCKED", "lock_state": "absent",
            "scientific_outcome": "not_evaluated", "edge": None, "formal_evidence_allowed": False,
        },
        "activation": {
            "post_commit_ledger_path": POST_COMMIT_LEDGER_PATH.relative_to(REPO_ROOT).as_posix(),
            "required_ordinal": 0,
            "required_phase": "PHASE2_POST_BINDING",
            "required_verdict": "AUDIT_PASS_POST_BINDING",
            "exact_phase2_paths": phase2_paths,
            "lock_hash_rule": "event_lock_raw_canonical_and_self_equal_current_immutable_lock",
            "commit_ancestry_rule": "phase2_commit_is_ancestor_of_current_HEAD",
            "auditor_independence_rule": "fresh_true_implementation_participation_false_findings_empty",
            "absence_rule": "historical_ordinal_0_all_formal_outcome_and_raw_scopes_absent_without_live_remeasurement",
            "historical_absence_expectation": _historical_activation_absence_expectation(contract),
        },
        "post_audit": {
            "execution_status": "ready", "checkpoint_state": "LOCKED_READY", "lock_state": "effective",
            "scientific_outcome": "not_evaluated", "edge": None, "formal_evidence_allowed": True,
        },
    }
    prebinding_audit = {
        "ledger_record": ledger_record,
        "ledger_digest": ledger["ledger_digest"],
        "event_digests": [event["event_digest"] for event in events],
    }
    governance = {"base": governance_base, "prebinding_audit": prebinding_audit}
    lock: dict[str, Any] = {
        "schema_version": 1,
        "lock_id": "S10R4-A49-EXACT-FRAME-BINDING-02-EFFECTIVE-LOCK-V2",
        "checkpoint_id": "S10R4",
        "payload_state": "EFFECTIVE_EXECUTION_BINDING",
        "phase1": phase1,
        "plans": plans,
        "implementation": implementation,
        "predecessor_and_registries": predecessor,
        "source_realization": source_realization,
        "binding_02_inputs": binding_02_inputs,
        "prebinding_recovery_inputs": prebinding_recovery_inputs,
        "governance_and_boundary": governance,
        "lifecycle": lifecycle,
        "self_identity": {
            "algorithm": "sha256_canonical_json_with_only_this_value_zeroed",
            "canonical_self_sha256": "0" * 64,
        },
    }
    lock["self_identity"]["canonical_self_sha256"] = canonical_self_hash(
        lock, ("self_identity", "canonical_self_sha256")
    )
    validate_effective_lock(
        lock,
        remeasure=False,
        prebinding_ledger=ledger,
        prebinding_ledger_record=ledger_record,
    )
    if write:
        if prebinding_ledger is not None:
            raise S10R4Error("production lock construction cannot use an unwritten candidate ledger")
        atomic_write_json(output, lock)
    return lock


def construct_effective_lock(
    *,
    output: Path,
    plan_a_path: Path,
    plan_b_path: Path,
    plan_b_freeze_path: Path,
    audit_verdict_path: Path,
    native_build_manifest: Path,
    prebinding_ledger: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Construct the production binding. Main owns invoking this function."""
    return _construct_effective_lock_v11(
        output=output,
        plan_a_path=plan_a_path,
        plan_b_path=plan_b_path,
        plan_b_freeze_path=plan_b_freeze_path,
        audit_verdict_path=audit_verdict_path,
        native_build_manifest=native_build_manifest,
        prebinding_ledger=prebinding_ledger,
        write=write,
    )


def validate_effective_lock(
    lock: Mapping[str, Any],
    *,
    remeasure: bool = True,
    prebinding_ledger: Mapping[str, Any] | None = None,
    prebinding_ledger_record: Mapping[str, Any] | None = None,
) -> None:
    return _validate_effective_lock_v11(
        lock,
        remeasure=remeasure,
        prebinding_ledger=prebinding_ledger,
        prebinding_ledger_record=prebinding_ledger_record,
    )


def verify_committed_effective_lock(path: Path) -> dict[str, Any]:
    return _verify_committed_effective_lock_v11(path)


def _require_binding_record(
    record: Mapping[str, Any],
    *,
    where: str,
    extras: Iterable[str] = (),
) -> None:
    require_exact_keys(
        record,
        {"path", "mode", "size_bytes", "raw_sha256", "canonical_sha256", *extras},
        where=where,
    )
    if (
        not isinstance(record["path"], str)
        or not isinstance(record["mode"], int)
        or not isinstance(record["size_bytes"], int)
        or record["size_bytes"] < 0
        or not isinstance(record["raw_sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", record["raw_sha256"]) is None
        or (
            record["canonical_sha256"] is not None
            and (
                not isinstance(record["canonical_sha256"], str)
                or re.fullmatch(r"[0-9a-f]{64}", record["canonical_sha256"]) is None
            )
        )
    ):
        raise S10R4Error(f"{where} has a malformed file binding")


def _require_prebinding_record(record: Mapping[str, Any], *, where: str) -> None:
    _require_binding_record(record, where=where, extras={"git_state"})
    git_state = record["git_state"]
    require_exact_keys(
        git_state,
        {
            "state", "status_code", "index_mode", "index_blob_oid", "worktree_mode",
            "worktree_size_bytes", "worktree_raw_sha256",
        },
        where=f"{where}.git_state",
    )
    if (
        git_state["state"] not in ("untracked", "modified")
        or not isinstance(git_state["status_code"], str)
        or len(git_state["status_code"]) != 2
        or git_state["worktree_mode"] != record["mode"]
        or git_state["worktree_size_bytes"] != record["size_bytes"]
        or git_state["worktree_raw_sha256"] != record["raw_sha256"]
    ):
        raise S10R4Error(f"{where} prebinding Git observation mismatch")


def _binding_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: record[key]
        for key in ("path", "mode", "size_bytes", "raw_sha256", "canonical_sha256")
    }


def _validate_lock_source_shapes(source: Mapping[str, Any]) -> None:
    require_exact_keys(
        source,
        {
            "ductile_commit_resolution", "geko_commit_resolution", "pinned_source_records",
            "actual_yaml", "tool_records", "llvm_executable_closure", "native_build_manifest",
            "native_build_products", "prelabel_summary", "container_realization",
            "gpu_selection_predicate", "in_process_boundaries",
        },
        where="effective lock source_realization",
    )
    for name in ("ductile_commit_resolution", "geko_commit_resolution"):
        require_exact_keys(
            source[name], {"commit", "argv", "returncode", "stdout_sha256", "stderr_sha256"},
            where=f"effective lock source_realization.{name}",
        )
    require_exact_keys(
        source["actual_yaml"], {"path", "git_blob_oid", "mode", "size_bytes", "raw_sha256"},
        where="effective lock source_realization.actual_yaml",
    )
    pinned_records = source["pinned_source_records"]
    if not isinstance(pinned_records, list) or len(pinned_records) != 8:
        raise S10R4Error("effective lock source realization is not the exact ordered eight-set")
    declared_sources = pinned_source_declarations(load_contract())
    pinned_root = (
        REPO_ROOT
        / "agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/artifacts/prelabel-build/pinned-source"
    ).resolve(strict=False)
    for index, row in enumerate(pinned_records):
        require_exact_keys(
            row,
            {
                "source_role", "repository_path", "required_symbols", "expected_git_blob_oid",
                "materialized_path", "mode", "link_count", "size_bytes", "raw_sha256",
            },
            where=f"effective lock pinned_source_records[{index}]",
        )
        declared = declared_sources[index]
        if (
            {key: row[key] for key in declared} != declared
            or row["link_count"] != 1
            or not isinstance(row["mode"], int) or isinstance(row["mode"], bool)
            or not 0 <= row["mode"] <= 0o7777
            or not isinstance(row["size_bytes"], int) or isinstance(row["size_bytes"], bool)
            or row["size_bytes"] < 0
            or not isinstance(row["materialized_path"], str)
            or Path(row["materialized_path"]).resolve(strict=False)
            != (pinned_root / declared["repository_path"]).resolve(strict=False)
            or re.fullmatch(r"[0-9a-f]{64}", row["raw_sha256"]) is None
        ):
            raise S10R4Error(f"effective lock pinned source declaration mismatch at {index}")
    if (
        len({row["repository_path"] for row in pinned_records}) != 8
        or len({row["expected_git_blob_oid"] for row in pinned_records}) != 8
        or len({row["materialized_path"] for row in pinned_records}) != 8
    ):
        raise S10R4Error("effective lock pinned source paths/blobs are not unique")
    bound_summary = load_json(REPO_ROOT / source["prelabel_summary"]["path"])
    if bound_summary.get("source_identity", {}).get("files") != pinned_records:
        raise S10R4Error("effective-lock prelabel exact-eight source set drift")
    for index, row in enumerate(source["tool_records"]):
        require_exact_keys(
            row,
            {
                "tool_id", "requested_path", "resolved_path", "mode", "size_bytes", "binary_sha256",
                "version_argv", "allowed_returncodes", "returncode", "stdout_sha256", "stderr_sha256",
                "first_line",
            },
            where=f"effective lock tool_records[{index}]",
        )
    if [row["tool_id"] for row in source["tool_records"]] != [row[0] for row in TOOL_VERSION_SPECS]:
        raise S10R4Error("effective lock tool realization order mismatch")
    _require_binding_record(source["native_build_manifest"], where="effective lock native_build_manifest")
    _require_binding_record(source["prelabel_summary"], where="effective lock prelabel_summary")
    container = source["container_realization"]
    require_exact_keys(
        container,
        {"container_name", "host_path", "container_path", "mode", "mount_observation", "device_surface"},
        where="effective lock container_realization",
    )
    require_exact_keys(
        container["mount_observation"],
        {"mount_point", "mount_options", "filesystem_type", "source", "record_sha256"},
        where="effective lock mount_observation",
    )
    for index, row in enumerate(container["device_surface"]):
        require_exact_keys(
            row, {"path", "present", "type", "mode", "major", "minor"},
            where=f"effective lock device_surface[{index}]",
        )
    require_exact_keys(
        source["gpu_selection_predicate"], {"projection", "projection_sha256"},
        where="effective lock gpu_selection_predicate",
    )
    if source["gpu_selection_predicate"]["projection_sha256"] != canonical_sha256(
        source["gpu_selection_predicate"]["projection"]
    ):
        raise S10R4Error("effective lock GPU predicate projection mismatch")


def _validate_effective_lock_v11(
    lock: Mapping[str, Any],
    *,
    remeasure: bool,
    prebinding_ledger: Mapping[str, Any] | None = None,
    prebinding_ledger_record: Mapping[str, Any] | None = None,
) -> None:
    validate_document_schema(lock)
    require_exact_keys(
        lock,
        {
            "schema_version", "lock_id", "checkpoint_id", "payload_state", "phase1", "plans",
            "implementation", "predecessor_and_registries", "source_realization",
            "binding_02_inputs", "prebinding_recovery_inputs",
            "governance_and_boundary", "lifecycle", "self_identity",
        },
        where="effective lock",
    )
    section_keys: dict[str, set[str]] = {
        "phase1": {
            "contract_record", "composed_contract_projection_sha256", "phase1_contract_commit_oid", "phase1_post_commit_audit", "authority_records",
            "workflow_authority_projection_sha256", "scientific_oracle_projection_sha256",
        },
        "plans": {
            "plan_a", "predecessor_plan_a", "plan_a_revision_ledger", "selected_revision_record",
            "plan_b", "plan_b_freeze", "parity_audit",
        },
        "implementation": {
            "exact_path_count", "files", "schema", "unit_test", "command_templates", "environment",
            "timeouts", "expected_phase2_paths",
        },
        "predecessor_and_registries": {
            "predecessor_input_hashes", "predecessor_raw_root", "raw_inventory", "raw_inventory_count",
            "raw_inventory_size_bytes", "raw_inventory_projection_sha256", "exact_frame_registry",
            "size_registry", "native_fixture",
        },
        "governance_and_boundary": {"base", "prebinding_audit"},
        "lifecycle": {"pre_audit", "activation", "post_audit"},
        "self_identity": {"algorithm", "canonical_self_sha256"},
    }
    for section, keys in section_keys.items():
        require_exact_keys(lock[section], keys, where=f"effective lock {section}")
    _validate_lock_source_shapes(lock["source_realization"])
    _require_binding_record(lock["phase1"]["contract_record"], where="effective lock phase1.contract_record")
    require_exact_keys(
        lock["phase1"]["phase1_post_commit_audit"], {"ledger_path", "event_ordinal", "event_digest"},
        where="effective lock phase1_post_commit_audit",
    )
    for index, record in enumerate(lock["phase1"]["authority_records"]):
        _require_binding_record(record, where=f"effective lock authority_records[{index}]", extras={"id"})
    _require_binding_record(lock["plans"]["plan_a"], where="effective lock plan_a", extras={"revision"})
    require_exact_keys(
        lock["plans"]["predecessor_plan_a"], {"revision", "raw_sha256", "size_bytes"},
        where="effective lock predecessor_plan_a",
    )
    for name in ("plan_a_revision_ledger", "plan_b", "plan_b_freeze"):
        _require_binding_record(lock["plans"][name], where=f"effective lock {name}")
    require_exact_keys(
        lock["plans"]["parity_audit"], {"ledger_path", "event_ordinal", "event_digest"},
        where="effective lock parity_audit",
    )
    for index, record in enumerate(lock["implementation"]["files"]):
        _require_prebinding_record(record, where=f"effective lock implementation.files[{index}]")
    _require_prebinding_record(lock["implementation"]["schema"], where="effective lock implementation.schema")
    _require_prebinding_record(lock["implementation"]["unit_test"], where="effective lock implementation.unit_test")
    for index, row in enumerate(lock["implementation"]["command_templates"]):
        require_exact_keys(
            row, {"command_id", "template", "placeholders", "concrete_allowlist"},
            where=f"effective lock command_templates[{index}]",
        )
    require_exact_keys(
        lock["implementation"]["timeouts"],
        {
            "independent_reproduction", "census_child", "mapping_attempt",
            "native_fixture_command", "gpu_allocation_process_snapshot_command",
            "correctness_cell_attempt", "noise_cell",
        },
        where="effective lock implementation.timeouts",
    )
    if lock["implementation"]["timeouts"] != {
        "independent_reproduction": 7200,
        "census_child": 7200,
        "mapping_attempt": 7200,
        "native_fixture_command": 7200,
        "gpu_allocation_process_snapshot_command": 60,
        "correctness_cell_attempt": 7200,
        "noise_cell": 7200,
    }:
        raise S10R4Error("effective lock exact timeout map mismatch")
    predecessor = lock["predecessor_and_registries"]
    for name in ("exact_frame_registry", "size_registry", "native_fixture"):
        _require_binding_record(predecessor[name], where=f"effective lock predecessor.{name}")
    governance = lock["governance_and_boundary"]
    base = governance["base"]
    _validate_governance_base(base)
    require_exact_keys(
        base,
        {
            "risk_tier", "repair_numeric_stop_cap", "role_records", "projected_role_thread_count",
            "still_fresh_verifier_thread_count",
            "resources", "boundaries", "absence", "baseline", "unrelated_worktree_observation",
            "expected_stage_projection", "outcome_document_policy_projection_sha256",
            "downstream_handoff_projection_sha256",
        },
        where="effective lock governance base",
    )
    require_exact_keys(
        governance["prebinding_audit"], {"ledger_record", "ledger_digest", "event_digests"},
        where="effective lock prebinding_audit",
    )
    _require_binding_record(governance["prebinding_audit"]["ledger_record"], where="effective lock prebinding ledger")
    if prebinding_ledger is None:
        ledger, ledger_events = load_prebinding_audit_ledger()
        expected_ledger_record = _binding_record(PREBINDING_LEDGER_PATH)
    else:
        ledger, ledger_events = _validate_active_prebinding_document(prebinding_ledger)
        expected_ledger_record = _prospective_json_binding_record(PREBINDING_LEDGER_PATH, ledger)
        if (
            prebinding_ledger_record is not None
            and dict(prebinding_ledger_record) != expected_ledger_record
        ):
            raise S10R4Error("prospective successor-ledger binding record mismatch")
    if (
        governance["prebinding_audit"]["ledger_record"]
        != expected_ledger_record
        or governance["prebinding_audit"]["ledger_digest"] != ledger["ledger_digest"]
        or governance["prebinding_audit"]["event_digests"]
        != [event["event_digest"] for event in ledger_events]
        or lock["phase1"]["phase1_post_commit_audit"]["event_digest"]
        != ledger_events[0]["event_digest"]
        or lock["plans"]["parity_audit"]["event_digest"]
        != ledger_events[1]["event_digest"]
    ):
        raise S10R4Error("effective-lock cumulative prebinding audit attachment mismatch")
    _require_binding_record(base["baseline"], where="effective lock baseline")
    for index, role in enumerate(base["role_records"]):
        require_exact_keys(
            role, {"role", "task_id", "fresh", "implementation_participation"},
            where=f"effective lock role_records[{index}]",
        )
    require_exact_keys(
        base["boundaries"],
        {
            "implementation_paths", "prelabel_paths", "formal_paths", "delivery_paths", "forbidden",
            "implementation_projection_sha256", "prelabel_projection_sha256", "formal_projection_sha256",
            "delivery_projection_sha256", "forbidden_projection_sha256",
        },
        where="effective lock boundaries",
    )
    require_exact_keys(
        base["absence"], {"durable", "raw_scopes", "lock", "projection_sha256"},
        where="effective lock absence",
    )
    require_exact_keys(
        base["expected_stage_projection"],
        {"stage_id", "resumable_prefix_count", "terminal_branch", "blocker_present", "formal_absence_projection_sha256"},
        where="effective lock expected_stage_projection",
    )
    require_exact_keys(
        base["unrelated_worktree_observation"],
        {"status_lines", "status_projection_sha256", "attribution", "staged_phase2_paths"},
        where="effective lock unrelated_worktree_observation",
    )
    if (
        lock["schema_version"] != 1
        or lock["lock_id"] != "S10R4-A49-EXACT-FRAME-BINDING-02-EFFECTIVE-LOCK-V2"
        or lock["checkpoint_id"] != "S10R4"
        or lock["payload_state"] != "EFFECTIVE_EXECUTION_BINDING"
    ):
        raise S10R4Error("effective lock identity mismatch")
    contract = load_contract()
    if (
        lock["phase1"]["contract_record"] != _base_contract_record()
        or lock["phase1"]["composed_contract_projection_sha256"] != canonical_sha256(contract)
        or lock["binding_02_inputs"] != _supplement_lock_inputs(load_contract_supplement())
        or lock["prebinding_recovery_inputs"]
        != _prebinding_recovery_lock_inputs(load_prebinding_recovery_amendment())
    ):
        raise S10R4Error("effective lock contract binding mismatch")
    if lock["phase1"]["phase1_contract_commit_oid"] != PHASE1_COMMIT_OID:
        raise S10R4Error("effective lock Phase-1 commit mismatch")
    if (
        lock["plans"]["plan_a"]["revision"] != PLAN_A_REVISION
        or lock["plans"]["plan_a"]["raw_sha256"] != PLAN_A_RAW_SHA256
        or lock["plans"]["plan_a"]["size_bytes"] != PLAN_A_SIZE_BYTES
        or lock["plans"]["predecessor_plan_a"] != PLAN_A_PREDECESSOR
    ):
        raise S10R4Error("effective lock Plan-A revision lineage mismatch")
    implementation_paths = list(contract["write_boundaries"]["implementation_exact_paths"])
    prelabel_paths = list(contract["write_boundaries"]["prelabel_durable_exact_paths"][:-1])
    phase2_paths = list(contract["seal_protocol"]["phase2"]["exact_commit_paths"])
    files = lock["implementation"]["files"]
    if (
        lock["implementation"]["exact_path_count"] != 15
        or [row["path"] for row in files] != implementation_paths
        or lock["implementation"]["schema"] != next(row for row in files if row["path"].endswith("s10r4-entry.schema.json"))
        or lock["implementation"]["unit_test"] != next(row for row in files if row["path"].endswith("test_ductile_s10r4_entry.py"))
        or lock["implementation"]["command_templates"] != _command_template_records()
        or lock["implementation"]["environment"] != FIXED_ENVIRONMENT
        or lock["implementation"]["expected_phase2_paths"] != phase2_paths
    ):
        raise S10R4Error("effective lock implementation projection mismatch")
    if [predecessor[name]["path"] for name in ("exact_frame_registry", "size_registry", "native_fixture")] != prelabel_paths:
        raise S10R4Error("effective lock prelabel registry path order mismatch")
    raw_inventory = predecessor["raw_inventory"]
    if (
        predecessor["raw_inventory_count"] != raw_inventory.get("ordinary_file_count")
        or predecessor["raw_inventory_count"] != len(raw_inventory.get("records", []))
        or predecessor["raw_inventory_size_bytes"] != sum(int(row["size_bytes"]) for row in raw_inventory["records"])
        or predecessor["raw_inventory_projection_sha256"] != raw_inventory.get("projection_sha256")
    ):
        raise S10R4Error("effective lock raw inventory projection mismatch")
    if (
        base["risk_tier"] != "R3"
        or base["repair_numeric_stop_cap"] is not None
        or base["projected_role_thread_count"] != 6
        or base["still_fresh_verifier_thread_count"] != 1
        or len(base["role_records"]) != 6
        or [row["role"] for row in base["role_records"]]
        != [
            "original_design_reviewer_a", "original_design_reviewer_b",
            "adversarial_auditor", "implementer",
            "binding_recovery_operational_reviewer", "fresh_verifier",
        ]
        or base["role_records"][-1]["task_id"] is not None
        or base["resources"]["historical_carried"]
        != load_contract_supplement()["resources"]["carry_from_binding_01"]
    ):
        raise S10R4Error("effective lock governance mismatch")
    if base["boundaries"] != _boundary_realization(contract):
        raise S10R4Error("effective lock write-boundary realization mismatch")
    expected_lifecycle = {
        "pre_audit": {
            "execution_status": "blocked", "checkpoint_state": "BLOCKED", "lock_state": "absent",
            "scientific_outcome": "not_evaluated", "edge": None, "formal_evidence_allowed": False,
        },
        "activation": {
            "post_commit_ledger_path": POST_COMMIT_LEDGER_PATH.relative_to(REPO_ROOT).as_posix(),
            "required_ordinal": 0, "required_phase": "PHASE2_POST_BINDING",
            "required_verdict": "AUDIT_PASS_POST_BINDING", "exact_phase2_paths": phase2_paths,
            "lock_hash_rule": "event_lock_raw_canonical_and_self_equal_current_immutable_lock",
            "commit_ancestry_rule": "phase2_commit_is_ancestor_of_current_HEAD",
            "auditor_independence_rule": "fresh_true_implementation_participation_false_findings_empty",
            "absence_rule": "historical_ordinal_0_all_formal_outcome_and_raw_scopes_absent_without_live_remeasurement",
            "historical_absence_expectation": _historical_activation_absence_expectation(contract),
        },
        "post_audit": {
            "execution_status": "ready", "checkpoint_state": "LOCKED_READY", "lock_state": "effective",
            "scientific_outcome": "not_evaluated", "edge": None, "formal_evidence_allowed": True,
        },
    }
    if lock["lifecycle"] != expected_lifecycle:
        raise S10R4Error("effective lock dormant lifecycle mismatch")
    if canonical_self_hash(lock, ("self_identity", "canonical_self_sha256")) != lock["self_identity"]["canonical_self_sha256"]:
        raise S10R4Error("effective lock canonical self-hash mismatch")
    if remeasure:
        for stored in lock["source_realization"]["pinned_source_records"]:
            path = Path(stored["materialized_path"])
            info = path.stat(follow_symlinks=False)
            data = path.read_bytes()
            observed_blob = hashlib.sha1(
                b"blob " + str(len(data)).encode("ascii") + b"\0" + data
            ).hexdigest()
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) != stored["mode"]
                or info.st_size != stored["size_bytes"]
                or sha256_bytes(data) != stored["raw_sha256"]
                or observed_blob != stored["expected_git_blob_oid"]
            ):
                raise S10R4Error(
                    f"effective-lock materialized source drift: {stored['repository_path']}"
                )
        for stored in files:
            if _binding_projection(stored) != _binding_record(REPO_ROOT / stored["path"]):
                raise S10R4Error(f"effective-lock implementation byte drift: {stored['path']}")
        for stored in (predecessor["exact_frame_registry"], predecessor["size_registry"], predecessor["native_fixture"]):
            if stored != _binding_record(REPO_ROOT / stored["path"]):
                raise S10R4Error(f"effective-lock prelabel binding drift: {stored['path']}")
        for stored in lock["phase1"]["authority_records"]:
            if _binding_projection(stored) != _binding_record(REPO_ROOT / stored["path"]):
                raise S10R4Error(f"effective-lock authority binding drift: {stored['path']}")
        for stored in (
            lock["plans"]["plan_a"], lock["plans"]["plan_a_revision_ledger"],
            lock["plans"]["plan_b"], lock["plans"]["plan_b_freeze"], base["baseline"],
        ):
            if _binding_projection(stored) != _binding_record(REPO_ROOT / stored["path"]):
                raise S10R4Error(f"effective-lock plan/governance binding drift: {stored['path']}")
        if lock["plans"]["selected_revision_record"] != _selected_revision_record():
            raise S10R4Error("effective-lock selected Plan-A revision record drift")
        for declared in contract["predecessor_frame"]["committed_inputs"]:
            if raw_sha256(REPO_ROOT / declared["path"]) != declared["raw_sha256"]:
                raise S10R4Error(f"effective-lock predecessor input drift: {declared['path']}")
        report = load_json(IMPLEMENTER_REPORT_PATHS[1])
        report_resources = report["resources"] if "resources" in report else None
        projected_resources = project_report_resources(report_resources)
        expected_resources = {
            "planning_policy": contract["resources"],
            "historical_carried": dict(
                load_contract_supplement()["resources"]["carry_from_binding_01"]
            ),
            "implementation_reported": projected_resources,
            "whole_role_cpu_seconds": projected_resources["whole_role_cpu_seconds"],
            "whole_role_wall_seconds": projected_resources["whole_role_wall_seconds"],
        }
        if base["resources"] != expected_resources:
            raise S10R4Error("effective-lock measured resource realization drift")


def _clean_worktree_path(relative: str) -> None:
    if _run_git(["status", "--porcelain=v1", "--untracked-files=all", "--", relative]).stdout:
        raise S10R4Error(f"Phase-2 path is not clean: {relative}")


def _verify_committed_effective_lock_v11(path: Path) -> dict[str, Any]:
    contract = load_contract()
    expected = REPO_ROOT / contract["identity"]["effective_lock_path"]
    if path.resolve(strict=True) != expected.resolve(strict=True):
        raise S10R4Error("effective lock path mismatch")
    lock = load_json(path)
    validate_effective_lock(lock, remeasure=True)
    ledger, events = load_post_commit_audit_ledger()
    event = events[0]
    inputs = event["inputs"]
    commit = inputs["phase2_commit_oid"]
    parent = inputs["phase2_parent_oid"]
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise S10R4Error("post-binding Phase-2 commit OID is malformed")
    observed_parent = _run_git(["rev-parse", f"{commit}^"]).stdout.decode("ascii").strip()
    if parent != observed_parent or not isinstance(parent, str) or re.fullmatch(r"[0-9a-f]{40}", parent) is None:
        raise S10R4Error("post-binding Phase-2 parent OID mismatch")
    ancestry = _run_git(["merge-base", "--is-ancestor", commit, "HEAD"], check=False)
    if ancestry.returncode != 0 or inputs["commit_is_ancestor_of_head"] is not True:
        raise S10R4Error("post-binding Phase-2 commit is not in current HEAD lineage")
    phase2_paths = list(contract["seal_protocol"]["phase2"]["exact_commit_paths"])
    diff_lines = _run_git(["diff", "--name-only", parent, commit, "--"]).stdout.decode("utf-8").splitlines()
    if sorted(diff_lines) != sorted(phase2_paths) or len(diff_lines) != len(phase2_paths) or inputs["changed_paths"] != phase2_paths:
        raise S10R4Error("post-binding Phase-2 diff is not the exact ordered 19-path projection")
    path_records = [_committed_path_record(commit, relative) for relative in phase2_paths]
    if inputs["path_records"] != path_records:
        raise S10R4Error("post-binding committed path records mismatch")
    lock_record = _binding_record(path)
    if inputs["lock_record"] != lock_record or inputs["lock_self_sha256"] != lock["self_identity"]["canonical_self_sha256"]:
        raise S10R4Error("post-binding immutable lock identity mismatch")
    prebinding_ledger, _ = load_prebinding_audit_ledger()
    expected_prebinding = {
        **_binding_record(PREBINDING_LEDGER_PATH), "ledger_digest": prebinding_ledger["ledger_digest"],
    }
    if inputs["prebinding_ledger_record"] != expected_prebinding:
        raise S10R4Error("post-binding prebinding-ledger identity mismatch")
    _validate_historical_activation_absence(inputs["formal_absence"], contract)
    if (
        inputs["auditor_task_id"] != event["auditor_task_id"]
        or inputs["fresh"] is not True
        or inputs["unrelated_worktree_observation"]
        != lock["governance_and_boundary"]["base"]["unrelated_worktree_observation"]
    ):
        raise S10R4Error("post-binding auditor or unrelated-worktree projection mismatch")
    exact_projection = {
        key: value for key, value in inputs.items() if key != "exact_commit_projection_sha256"
    }
    if inputs["exact_commit_projection_sha256"] != canonical_sha256(exact_projection):
        raise S10R4Error("post-binding exact-commit projection digest mismatch")
    binding_by_path = {
        row["path"]: row
        for row in [
            *lock["implementation"]["files"],
            lock["predecessor_and_registries"]["exact_frame_registry"],
            lock["predecessor_and_registries"]["size_registry"],
            lock["predecessor_and_registries"]["native_fixture"],
        ]
    }
    for committed in path_records:
        relative = committed["path"]
        _clean_worktree_path(relative)
        current = _binding_record(REPO_ROOT / relative)
        stored = lock_record if relative == lock_record["path"] else binding_by_path.get(relative)
        if stored is None or _binding_projection(stored) != current:
            raise S10R4Error(f"post-binding current byte projection mismatch: {relative}")
        if committed["size_bytes"] != current["size_bytes"] or committed["raw_sha256"] != current["raw_sha256"]:
            raise S10R4Error(f"post-binding committed/current raw identity mismatch: {relative}")
        expected_git_mode = "100755" if current["mode"] & 0o111 else "100644"
        if committed["git_mode"] != expected_git_mode:
            raise S10R4Error(f"post-binding committed mode mismatch: {relative}")
    native_manifest = REPO_ROOT / lock["source_realization"]["native_build_manifest"]["path"]
    if lock["source_realization"] != _source_realization(contract, native_manifest):
        raise S10R4Error("effective-lock complete source/tool/container/device realization drift")
    if ledger["events"][0]["event_digest"] != event["event_digest"]:
        raise S10R4Error("post-binding ledger event identity drift")
    return lock
