# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Canonical, typed, crash-safe serialization helpers for S11."""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping


class CanonicalError(ValueError):
    """Input cannot be represented by the S11 canonical format."""


def _reject_constant(value: str) -> None:
    raise CanonicalError(f"non-finite JSON constant is forbidden: {value}")


def _object_no_duplicates(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json_loads(raw: str | bytes) -> Any:
    """Load JSON while rejecting duplicates and non-finite numbers."""

    try:
        return json.loads(
            raw,
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CanonicalError("malformed UTF-8 JSON") from error


def strict_load_json(path: Path | str) -> Any:
    target = Path(path)
    info = target.lstat()
    if not stat.S_ISREG(info.st_mode) or target.is_symlink():
        raise CanonicalError(f"JSON input is not an ordinary file: {target}")
    return strict_json_loads(target.read_bytes())


def _check_json(value: Any, pointer: str = "") -> None:
    if value is None or type(value) in (bool, int, str):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise CanonicalError(f"non-finite float at {pointer or '/'}")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _check_json(item, f"{pointer}/{index}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise CanonicalError(f"non-string object key at {pointer or '/'}")
            _check_json(item, f"{pointer}/{key.replace('~', '~0').replace('/', '~1')}")
        return
    raise CanonicalError(f"unsupported JSON type at {pointer or '/'}: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return canonical UTF-8 JSON (sorted keys, compact, finite-only)."""

    _check_json(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path | str, *, chunk_bytes: int = 1024 * 1024) -> str:
    target = Path(path)
    info = target.lstat()
    if not stat.S_ISREG(info.st_mode) or target.is_symlink():
        raise CanonicalError(f"hash target is not an ordinary file: {target}")
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        while block := stream.read(chunk_bytes):
            digest.update(block)
    return digest.hexdigest()


def typed_value(value: Any) -> dict[str, Any]:
    """Encode YAML candidate values without bool/int or float/string aliases.

    Float values use hexadecimal syntax, making `-0.0` and exact binary values
    stable across YAML and JSON libraries.
    """

    if value is None:
        return {"type": "null", "value": None}
    if type(value) is bool:
        return {"type": "bool", "value": value}
    if type(value) is int:
        return {"type": "int", "value": str(value)}
    if type(value) is float:
        if not math.isfinite(value):
            raise CanonicalError("candidate values must be finite")
        return {"type": "float", "value": value.hex()}
    if type(value) is str:
        return {"type": "str", "value": value}
    if type(value) in (list, tuple):
        return {"type": "list", "value": [typed_value(item) for item in value]}
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise CanonicalError("typed mappings require string keys")
        return {
            "type": "map",
            "value": {key: typed_value(value[key]) for key in sorted(value)},
        }
    raise CanonicalError(f"unsupported typed candidate: {type(value).__name__}")


def typed_value_id(value: Any) -> str:
    return canonical_sha256(typed_value(value))


def atomic_write_json(path: Path | str, value: Mapping[str, Any]) -> None:
    """Atomically replace an unpublished derived view and fsync its parent."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json_bytes(dict(value)) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        parent_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def exclusive_write_json(path: Path | str, value: Mapping[str, Any]) -> None:
    """Create one immutable JSON event with `O_EXCL` semantics."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json_bytes(dict(value)) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        parent_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    except Exception:
        # The caller sees the partial path and must treat it as an incident.
        raise
