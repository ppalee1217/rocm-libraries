# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Strict canonical serialization and M00 error types."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
import hashlib
import json
import math

import jsonschema
import yaml


class M00Error(RuntimeError):
    criterion_id = "M00.ACC.CONTRACT-LOCK"
    reason_code = "M00_ERROR"
    exit_code = 2

    def __init__(self, message: str, *, reason_code: str | None = None,
                 criterion_id: str | None = None):
        super().__init__(message)
        self.human_message = message
        if reason_code is not None:
            self.reason_code = reason_code
        if criterion_id is not None:
            self.criterion_id = criterion_id

    def as_dict(self) -> dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "reason_code": self.reason_code,
            "message": self.human_message,
        }


class ContractError(M00Error):
    criterion_id = "M00.ACC.CONTRACT-LOCK"
    reason_code = "CONTRACT_INVALID"
    exit_code = 2


class GuardError(M00Error):
    reason_code = "GUARD_REJECTED"
    exit_code = 3


class MissingEvidenceError(M00Error):
    criterion_id = "M00.STOP.MISSING-EVIDENCE"
    reason_code = "MISSING_EVIDENCE"
    exit_code = 4


class InstrumentationError(M00Error):
    criterion_id = "M00.FAL.INSTRUMENTATION"
    reason_code = "TRAJECTORY_MISMATCH"
    exit_code = 5


class ReportLifecycleError(M00Error):
    criterion_id = "M00.ACC.BASELINE-GUARD"
    reason_code = "REPORT_GATE_REJECTED"
    exit_code = 6


class StrictSafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate keys and aliases."""

    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            event = self.get_event()
            raise yaml.constructor.ConstructorError(
                None, None, f"YAML aliases are forbidden: *{event.anchor}",
                event.start_mark,
            )
        return super().compose_node(parent, index)


def _construct_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                "mapping keys must be strings", key_node.start_mark,
            )
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"duplicate key: {key}", key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def _reject_duplicate_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(
                f"duplicate JSON key: {key}", reason_code="DUPLICATE_KEY"
            )
        result[key] = value
    return result


def _plain_finite(value: Any, path: str = "$") -> Any:
    try:
        import numpy as np
    except ImportError:  # pragma: no cover - NumPy is an M00 prerequisite
        np = None

    if np is not None and isinstance(value, np.ndarray):
        value = value.tolist()
    if np is not None and isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractError(
                    f"{path}: object key is not a string",
                    reason_code="NON_STRING_KEY",
                )
            result[key] = _plain_finite(item, f"{path}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_plain_finite(item, f"{path}[{index}]")
                for index, item in enumerate(value)]
    if isinstance(value, float) and not math.isfinite(value):
        raise ContractError(
            f"{path}: non-finite float is forbidden",
            reason_code="NON_FINITE_VALUE",
        )
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ContractError(
        f"{path}: unsupported canonical type {type(value).__name__}",
        reason_code="UNSUPPORTED_CANONICAL_TYPE",
    )


def canonical_json_bytes(value: Any) -> bytes:
    plain = _plain_finite(value)
    return json.dumps(
        plain,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_json_text(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def load_yaml_strict(path: str | Path) -> Any:
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            value = yaml.load(stream, Loader=StrictSafeLoader)
    except (OSError, yaml.YAMLError) as exc:
        raise ContractError(
            f"cannot load strict YAML {path}: {exc}",
            reason_code="YAML_LOAD_FAILED",
        ) from exc
    return _plain_finite(value)


def load_json_strict(path: str | Path) -> Any:
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            value = json.load(stream, object_pairs_hook=_reject_duplicate_json)
    except ContractError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(
            f"cannot load strict JSON {path}: {exc}",
            reason_code="JSON_LOAD_FAILED",
        ) from exc
    return _plain_finite(value)


def validate_instance(instance: Any, schema: Any, *, label: str) -> None:
    try:
        jsonschema.Draft7Validator.check_schema(schema)
        errors = sorted(
            jsonschema.Draft7Validator(schema).iter_errors(instance),
            key=lambda error: list(error.absolute_path),
        )
    except jsonschema.SchemaError as exc:
        raise ContractError(
            f"invalid Draft-7 schema for {label}: {exc.message}",
            reason_code="SCHEMA_INVALID",
        ) from exc
    if errors:
        error = errors[0]
        location = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}"
            for part in error.absolute_path
        )
        raise ContractError(
            f"{label} failed schema validation at {location}: {error.message}",
            reason_code="SCHEMA_VALIDATION_FAILED",
        )


def load_and_validate(data_path: str | Path, schema_path: str | Path) -> Any:
    data_path = Path(data_path)
    if data_path.suffix in {".yaml", ".yml"}:
        instance = load_yaml_strict(data_path)
    elif data_path.suffix == ".json":
        instance = load_json_strict(data_path)
    else:
        raise ContractError(
            f"unsupported canonical input suffix: {data_path.suffix}",
            reason_code="UNSUPPORTED_CANONICAL_INPUT",
        )
    schema = load_json_strict(schema_path)
    validate_instance(instance, schema, label=str(data_path))
    return instance


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise MissingEvidenceError(
            f"cannot hash artifact {path}: {exc}",
            reason_code="ARTIFACT_UNREADABLE",
        ) from exc
    return digest.hexdigest()
