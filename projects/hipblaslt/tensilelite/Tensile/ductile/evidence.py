# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Strict, protocol-neutral evidence primitives for Ductile experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

import hashlib
import json
import math
import os
import re
import tempfile

import jsonschema
import numpy as np
import yaml


class EvidenceValidationError(ValueError):
    """Base class for stable, fail-closed evidence validation failures."""

    code = "evidence_validation_error"

    def __init__(self, message: str, *, code: Optional[str] = None):
        self.code = code or self.code
        super().__init__(f"{self.code}: {message}")


class LineageMismatchError(EvidenceValidationError):
    code = "lineage_mismatch"


class CheckpointValidationError(EvidenceValidationError):
    code = "checkpoint_validation_error"


class ArtifactReconciliationError(EvidenceValidationError):
    code = "artifact_reconciliation_error"


def _reject_json_constant(value: str) -> None:
    raise EvidenceValidationError(
        f"non-finite JSON constant {value!r}", code="non_finite_number"
    )


def _reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceValidationError(
                f"duplicate object key {key!r}", code="duplicate_key"
            )
        result[key] = value
    return result


class _StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_strict_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise EvidenceValidationError(
                f"duplicate object key {key!r}", code="duplicate_key"
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_strict_mapping
)


def strict_load_json(path_or_text, *, from_text: bool = False):
    if from_text:
        text = path_or_text
    else:
        text = Path(path_or_text).read_text(encoding="utf-8")
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except EvidenceValidationError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise EvidenceValidationError(str(exc), code="malformed_json") from exc


def strict_load_yaml(path_or_text, *, from_text: bool = False):
    if from_text:
        text = path_or_text
    else:
        text = Path(path_or_text).read_text(encoding="utf-8")
    try:
        return yaml.load(text, Loader=_StrictSafeLoader)
    except EvidenceValidationError:
        raise
    except yaml.YAMLError as exc:
        raise EvidenceValidationError(str(exc), code="malformed_yaml") from exc


def plain_value(value: Any):
    """Return a detached JSON-compatible value without consuming RNG state."""

    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise EvidenceValidationError(
                "object keys must be strings", code="unsupported_value"
            )
        return {key: plain_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain_value(item) for item in value]
    if isinstance(value, np.ndarray):
        return plain_value(value.tolist())
    if isinstance(value, np.generic):
        return plain_value(value.item())
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EvidenceValidationError(
                "NaN and infinity are forbidden", code="non_finite_number"
            )
        return value
    raise EvidenceValidationError(
        f"unsupported value type {type(value).__name__}", code="unsupported_value"
    )


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            plain_value(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError(str(exc), code="canonicalization_failed") from exc


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _freeze_plain(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_plain(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_plain(item) for item in value)
    return value


def freeze_payload(value: Any):
    return _freeze_plain(plain_value(value))


@dataclass(frozen=True)
class GAEvent:
    run_id: str
    effective_lock_sha256: str
    sequence: int
    event_id: str
    previous_event_sha256: Optional[str]
    kind: str
    generation: int
    payload: Any
    payload_sha256: str
    event_sha256: str

    def as_dict(self):
        return plain_value({
            "run_id": self.run_id,
            "effective_lock_sha256": self.effective_lock_sha256,
            "sequence": self.sequence,
            "event_id": self.event_id,
            "previous_event_sha256": self.previous_event_sha256,
            "kind": self.kind,
            "generation": self.generation,
            "payload": self.payload,
            "payload_sha256": self.payload_sha256,
            "event_sha256": self.event_sha256,
        })


def build_ga_event(
    *,
    run_id: str,
    effective_lock_sha256: str,
    sequence: int,
    previous_event_sha256: Optional[str],
    kind: str,
    generation: int,
    payload: Any,
) -> GAEvent:
    frozen = freeze_payload(payload)
    payload_sha256 = canonical_sha256(frozen)
    identity_body = {
        "run_id": run_id,
        "effective_lock_sha256": effective_lock_sha256,
        "sequence": sequence,
        "previous_event_sha256": previous_event_sha256,
        "kind": kind,
        "generation": generation,
        "payload_sha256": payload_sha256,
    }
    event_id = f"ga-event-{canonical_sha256(identity_body)}"
    event_body = dict(identity_body, event_id=event_id, payload=plain_value(frozen))
    event_sha256 = canonical_sha256(event_body)
    return GAEvent(
        run_id=run_id,
        effective_lock_sha256=effective_lock_sha256,
        sequence=sequence,
        event_id=event_id,
        previous_event_sha256=previous_event_sha256,
        kind=kind,
        generation=generation,
        payload=frozen,
        payload_sha256=payload_sha256,
        event_sha256=event_sha256,
    )


def canonical_config_hash(config) -> str:
    return canonical_sha256(plain_value(config))


def canonical_population_hash(configs: Sequence[Mapping[str, Any]]) -> str:
    copies = [plain_value(config) for config in configs]
    copies.sort(key=lambda config: canonical_json_bytes(config))
    return canonical_sha256(copies)


def _validator_for(schema):
    if hasattr(jsonschema, "Draft202012Validator"):
        validator_cls = jsonschema.Draft202012Validator
        runtime_schema = schema
    else:
        # The repository's host image currently carries jsonschema 3.x.  Keep
        # authoritative schemas in 2020-12 form and mechanically map its
        # compatible $defs spelling for the older, already-provisioned engine.
        def draft7_compat(value, *, root=False):
            if isinstance(value, dict):
                converted = {}
                for key, item in value.items():
                    mapped = "definitions" if key == "$defs" else key
                    if (
                            key == "$ref" and isinstance(item, str) and
                            item.startswith("#/$defs/")):
                        item = item.replace("#/$defs/", "#/definitions/", 1)
                    converted[mapped] = draft7_compat(item)
                if root:
                    converted["$schema"] = (
                        "http://json-schema.org/draft-07/schema#"
                    )
                return converted
            if isinstance(value, list):
                return [draft7_compat(item) for item in value]
            return value

        validator_cls = jsonschema.Draft7Validator
        runtime_schema = draft7_compat(schema, root=True)
    validator_cls.check_schema(runtime_schema)
    return validator_cls(
        runtime_schema, format_checker=jsonschema.FormatChecker()
    )


def validate_schema_document(document, schema, *, context="document"):
    try:
        _validator_for(schema).validate(plain_value(document))
    except jsonschema.SchemaError as exc:
        raise EvidenceValidationError(
            f"{context} schema is invalid: {exc.message}", code="invalid_schema"
        ) from exc
    except jsonschema.ValidationError as exc:
        location = "/".join(str(item) for item in exc.absolute_path) or "<root>"
        raise EvidenceValidationError(
            f"{context} at {location}: {exc.message}", code="schema_validation_failed"
        ) from exc
    return document


_LINEAGE_REQUIRED = {
    "artifact_id",
    "run_id",
    "effective_lock_sha256",
    "parent_id",
    "input_sha256",
    "source_bundle_sha256",
    "fixture_sha256",
    "seed",
}
_LINEAGE_OPTIONAL = {"prior_event_sha256", "prior_checkpoint_id"}
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _is_sha256(value):
    return isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None


def validate_lineage(lineage, expected=None):
    if not isinstance(lineage, Mapping):
        raise LineageMismatchError("lineage must be an object", code="lineage_malformed")
    actual = plain_value(lineage)
    fields = set(actual)
    missing = _LINEAGE_REQUIRED - fields
    extra = fields - _LINEAGE_REQUIRED - _LINEAGE_OPTIONAL
    if missing:
        raise LineageMismatchError(
            f"missing fields {sorted(missing)}", code="lineage_missing_field"
        )
    if extra:
        raise LineageMismatchError(
            f"unknown fields {sorted(extra)}", code="lineage_unknown_field"
        )
    if not isinstance(actual["seed"], dict) or set(actual["seed"]) != {"name", "value"}:
        raise LineageMismatchError(
            "seed must contain exactly name and value", code="lineage_seed_malformed"
        )
    for field in {"artifact_id", "run_id"}:
        if not isinstance(actual[field], str) or not actual[field]:
            raise LineageMismatchError(
                f"{field} must be a non-empty string", code="lineage_malformed"
            )
    for field in {
        "effective_lock_sha256",
        "input_sha256",
        "source_bundle_sha256",
        "fixture_sha256",
    }:
        if not _is_sha256(actual[field]):
            raise LineageMismatchError(
                f"{field} must be lowercase 64-hex",
                code="lineage_hash_malformed",
            )
    if actual["parent_id"] is not None and (
        not isinstance(actual["parent_id"], str) or not actual["parent_id"]
    ):
        raise LineageMismatchError(
            "parent_id must be null or a non-empty string", code="lineage_malformed"
        )
    if not isinstance(actual["seed"]["name"], str) or not isinstance(
        actual["seed"]["value"], int
    ):
        raise LineageMismatchError(
            "seed name/value types are invalid", code="lineage_seed_malformed"
        )
    if (
            "prior_event_sha256" in actual and
            actual["prior_event_sha256"] is not None and
            not _is_sha256(actual["prior_event_sha256"])):
        raise LineageMismatchError(
            "prior_event_sha256 must be null or lowercase 64-hex",
            code="lineage_hash_malformed",
        )
    if (
            "prior_checkpoint_id" in actual and
            actual["prior_checkpoint_id"] is not None and
            (
                not isinstance(actual["prior_checkpoint_id"], str) or
                not actual["prior_checkpoint_id"]
            )):
        raise LineageMismatchError(
            "prior_checkpoint_id must be null or a non-empty string",
            code="lineage_malformed",
        )
    if expected is not None:
        expected_plain = plain_value(expected)
        if actual != expected_plain:
            differing = sorted(
                key
                for key in set(actual) | set(expected_plain)
                if actual.get(key) != expected_plain.get(key)
            )
            raise LineageMismatchError(
                f"mismatched fields {differing}", code="lineage_field_mismatch"
            )
    return actual


def _event_dict(event):
    return event.as_dict() if isinstance(event, GAEvent) else plain_value(event)


def validate_event_chain(
    events,
    *,
    expected_start: int = 0,
    expected_previous_sha256: Optional[str] = None,
):
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)) or not events:
        raise EvidenceValidationError("event chain is empty", code="missing_event")
    seen_ids = set()
    seen_sequences = set()
    previous = expected_previous_sha256
    run_id = None
    effective_lock_sha256 = None
    for offset, raw_event in enumerate(events):
        event = _event_dict(raw_event)
        required = {
            "run_id",
            "effective_lock_sha256",
            "sequence",
            "event_id",
            "previous_event_sha256",
            "kind",
            "generation",
            "payload",
            "payload_sha256",
            "event_sha256",
        }
        if not isinstance(event, dict) or set(event) != required:
            raise EvidenceValidationError(
                f"event {offset} field set mismatch", code="malformed_event"
            )
        if (
                not _is_sha256(event["effective_lock_sha256"]) or
                not _is_sha256(event["payload_sha256"]) or
                not _is_sha256(event["event_sha256"]) or
                (
                    event["previous_event_sha256"] is not None and
                    not _is_sha256(event["previous_event_sha256"])
                )):
            raise EvidenceValidationError(
                f"event {offset} contains malformed hash",
                code="malformed_event_hash",
            )
        if offset == 0:
            run_id = event["run_id"]
            effective_lock_sha256 = event["effective_lock_sha256"]
        elif (
                event["run_id"] != run_id or
                event["effective_lock_sha256"] != effective_lock_sha256):
            raise EvidenceValidationError(
                f"event {offset} crosses run/lock identity",
                code="event_lineage_mismatch",
            )
        if event["event_id"] in seen_ids:
            raise EvidenceValidationError(
                f"duplicate event id {event['event_id']}", code="duplicate_event_id"
            )
        if event["sequence"] in seen_sequences:
            raise EvidenceValidationError(
                f"duplicate event sequence {event['sequence']}",
                code="duplicate_event_sequence",
            )
        expected_sequence = expected_start + offset
        if event["sequence"] != expected_sequence:
            raise EvidenceValidationError(
                f"expected sequence {expected_sequence}, got {event['sequence']}",
                code="event_sequence_gap",
            )
        if event["previous_event_sha256"] != previous:
            raise EvidenceValidationError(
                f"event {event['sequence']} has wrong previous hash",
                code="event_previous_hash_mismatch",
            )
        rebuilt = build_ga_event(
            run_id=event["run_id"],
            effective_lock_sha256=event["effective_lock_sha256"],
            sequence=event["sequence"],
            previous_event_sha256=event["previous_event_sha256"],
            kind=event["kind"],
            generation=event["generation"],
            payload=event["payload"],
        ).as_dict()
        if event != rebuilt:
            raise EvidenceValidationError(
                f"event {event['sequence']} content/hash mismatch",
                code="event_hash_mismatch",
            )
        seen_ids.add(event["event_id"])
        seen_sequences.add(event["sequence"])
        previous = event["event_sha256"]
    return {"next_sequence": expected_start + len(events), "chain_head": previous}


def make_checkpoint_manifest(body):
    body = plain_value(body)
    if "checkpoint_id" in body or "payload_sha256" in body:
        raise CheckpointValidationError(
            "derived manifest fields supplied in body", code="checkpoint_derived_field"
        )
    payload_sha256 = canonical_sha256(body)
    return dict(
        body,
        checkpoint_id=f"ga-checkpoint-{payload_sha256}",
        payload_sha256=payload_sha256,
    )


def validate_checkpoint_manifest(manifest, *, expected_body=None):
    if not isinstance(manifest, Mapping):
        raise CheckpointValidationError(
            "manifest must be an object", code="checkpoint_manifest_malformed"
        )
    actual = plain_value(manifest)
    required = {
        "format",
        "version",
        "checkpoint_id",
        "parent_checkpoint_id",
        "generation",
        "n_evals",
        "soo",
        "space_map",
        "space_map_sha256",
        "snapshots",
        "component_sha256",
        "pop_size",
        "base_pop_size",
        "decay_mode",
        "seed",
        "observer",
        "lineage",
        "payload_sha256",
    }
    if set(actual) != required:
        raise CheckpointValidationError(
            "manifest field set mismatch", code="checkpoint_manifest_malformed"
        )
    if actual["format"] != "ductile-ga-checkpoint" or actual["version"] != 1:
        raise CheckpointValidationError(
            "manifest format/version mismatch", code="checkpoint_version_mismatch"
        )
    parent_checkpoint_id = actual["parent_checkpoint_id"]
    if (
            parent_checkpoint_id is not None and
            (
                not isinstance(parent_checkpoint_id, str) or
                re.fullmatch(
                    r"ga-checkpoint-[0-9a-f]{64}", parent_checkpoint_id
                ) is None
            )):
        raise CheckpointValidationError(
            "parent checkpoint identity is malformed",
            code="checkpoint_manifest_malformed",
        )
    if set(actual["observer"]) != {
        "enabled", "next_sequence", "event_chain_head"
    }:
        raise CheckpointValidationError(
            "observer cursor field set mismatch",
            code="checkpoint_manifest_malformed",
        )
    if set(actual["snapshots"]) != {
        "best", "old_population", "population", "stats"
    }:
        raise CheckpointValidationError(
            "snapshot field set mismatch", code="checkpoint_manifest_malformed"
        )
    if set(actual["component_sha256"]) != {
        "best_sha256",
        "old_population_sha256",
        "population_sha256",
        "stats_sha256",
        "python_rng_sha256",
        "numpy_rng_sha256",
        "seed_sequence_sha256",
    }:
        raise CheckpointValidationError(
            "component hash field set mismatch",
            code="checkpoint_manifest_malformed",
        )
    if not _is_sha256(actual["space_map_sha256"]):
        raise CheckpointValidationError(
            "space map hash is malformed", code="checkpoint_manifest_malformed"
        )
    for name, digest in actual["component_sha256"].items():
        if not _is_sha256(digest):
            raise CheckpointValidationError(
                f"component hash is malformed: {name}",
                code="checkpoint_manifest_malformed",
            )
    event_chain_head = actual["observer"]["event_chain_head"]
    if event_chain_head is not None and not _is_sha256(event_chain_head):
        raise CheckpointValidationError(
            "event chain head is malformed",
            code="checkpoint_manifest_malformed",
        )
    if actual["space_map_sha256"] != canonical_sha256(actual["space_map"]):
        raise CheckpointValidationError(
            "space map hash mismatch", code="checkpoint_component_mismatch"
        )
    for snapshot_name, component_name in (
            ("best", "best_sha256"),
            ("old_population", "old_population_sha256"),
            ("population", "population_sha256"),
            ("stats", "stats_sha256")):
        if (
                canonical_sha256(actual["snapshots"][snapshot_name]) !=
                actual["component_sha256"][component_name]):
            raise CheckpointValidationError(
                f"snapshot hash mismatch: {snapshot_name}",
                code="checkpoint_component_mismatch",
            )
    if "checkpoint_id" not in actual or "payload_sha256" not in actual:
        raise CheckpointValidationError(
            "manifest lacks derived identity", code="checkpoint_missing_field"
        )
    body = {
        key: value
        for key, value in actual.items()
        if key not in {"checkpoint_id", "payload_sha256"}
    }
    rebuilt = make_checkpoint_manifest(body)
    if rebuilt != actual:
        raise CheckpointValidationError(
            "manifest identity/hash mismatch", code="checkpoint_hash_mismatch"
        )
    if expected_body is not None and body != plain_value(expected_body):
        raise CheckpointValidationError(
            "manifest body/component mismatch", code="checkpoint_component_mismatch"
        )
    validate_lineage(actual.get("lineage"))
    return actual


def resolve_bound_path(repo_root, relative_path):
    root = Path(repo_root).resolve()
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise EvidenceValidationError(
            f"bound path is not repo-relative: {relative_path}", code="unsafe_bound_path"
        )
    candidate = root.joinpath(relative)
    resolved = candidate.resolve(strict=True)
    if root != resolved and root not in resolved.parents:
        raise EvidenceValidationError(
            f"bound path escapes repository: {relative_path}", code="unsafe_bound_path"
        )
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise EvidenceValidationError(
                f"bound path uses symlink: {relative_path}", code="symlink_substitution"
            )
    return resolved


def _fsync_directory(directory):
    descriptor = os.open(str(directory), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_bytes(path, data: bytes, *, exclusive: bool = True):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if exclusive and target.exists():
        raise EvidenceValidationError(
            f"target already exists: {target}", code="already_exists"
        )
    descriptor, temp_name = tempfile.mkstemp(
        dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp"
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            try:
                os.link(temp_path, target)
            except FileExistsError as exc:
                raise EvidenceValidationError(
                    f"target already exists: {target}", code="already_exists"
                ) from exc
            temp_path.unlink()
        else:
            os.replace(temp_path, target)
        _fsync_directory(target.parent)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def atomic_write_json(path, document, *, exclusive: bool = True):
    atomic_write_bytes(
        path, canonical_json_bytes(document) + b"\n", exclusive=exclusive
    )


def write_effective_lock(path, document, schema):
    validate_schema_document(document, schema, context="effective lock")
    atomic_write_json(path, document, exclusive=True)
    return sha256_file(path)


def load_effective_lock(path, schema):
    document = strict_load_json(path)
    validate_schema_document(document, schema, context="effective lock")
    return document


def append_amendment(path, entry, schema):
    ledger = Path(path)
    prior_hash = None
    if ledger.exists():
        raw_lines = ledger.read_bytes().splitlines()
        for index, line in enumerate(raw_lines):
            if not line.strip():
                raise EvidenceValidationError(
                    f"blank ledger line {index + 1}", code="malformed_ledger"
                )
            existing = strict_load_json(line.decode("utf-8"), from_text=True)
            validate_schema_document(existing, schema, context=f"amendment {index + 1}")
            if existing["previous_entry_sha256"] != prior_hash:
                raise EvidenceValidationError(
                    f"broken ledger chain at line {index + 1}",
                    code="amendment_chain_mismatch",
                )
            prior_hash = hashlib.sha256(line).hexdigest()
    candidate = plain_value(entry)
    if candidate.get("previous_entry_sha256") != prior_hash:
        raise EvidenceValidationError(
            "new amendment predecessor mismatch", code="amendment_chain_mismatch"
        )
    validate_schema_document(candidate, schema, context="new amendment")
    encoded = canonical_json_bytes(candidate)
    descriptor = os.open(
        ledger, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644
    )
    try:
        os.write(descriptor, encoded + b"\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(ledger.parent)
    return hashlib.sha256(encoded).hexdigest()


def reconcile_artifacts(records, *, expected_lineage=None):
    if not isinstance(records, list) or not records:
        raise ArtifactReconciliationError("records are missing", code="missing_record")
    allowed = {
        "generated_input",
        "backend_result",
        "benchmark_observation",
        "summary",
    }
    seen = {}
    seen_record_ids = set()
    previous_sha256 = None
    common_lineage = None
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ArtifactReconciliationError(
                f"record {index} is malformed", code="malformed_record"
            )
        required = {
            "record_id",
            "kind",
            "status",
            "previous_record_sha256",
            "lineage",
            "payload",
            "payload_sha256",
            "record_sha256",
        }
        if set(record) != required:
            raise ArtifactReconciliationError(
                f"record {index} field set mismatch", code="malformed_record"
            )
        kind = record["kind"]
        if kind not in allowed:
            raise ArtifactReconciliationError(
                f"unexpected record kind {kind}", code="unexpected_record"
            )
        record_id = record["record_id"]
        if not isinstance(record_id, str) or not record_id:
            raise ArtifactReconciliationError(
                f"record {index} has invalid identity", code="malformed_record"
            )
        if record_id in seen_record_ids:
            raise ArtifactReconciliationError(
                f"duplicate record id {record_id}", code="duplicate_record_id"
            )
        seen_record_ids.add(record_id)
        if kind in seen:
            raise ArtifactReconciliationError(
                f"duplicate record kind {kind}", code="duplicate_record"
            )
        lineage = validate_lineage(record["lineage"], expected_lineage)
        if common_lineage is None:
            common_lineage = lineage
        elif lineage != common_lineage:
            raise ArtifactReconciliationError(
                "cross-lineage records", code="cross_lineage_record"
            )
        if record["previous_record_sha256"] != previous_sha256:
            raise ArtifactReconciliationError(
                f"broken record chain at {kind}", code="record_chain_mismatch"
            )
        if canonical_sha256(record["payload"]) != record["payload_sha256"]:
            raise ArtifactReconciliationError(
                f"payload hash mismatch at {kind}", code="record_hash_mismatch"
            )
        body = {
            key: value for key, value in record.items() if key != "record_sha256"
        }
        if canonical_sha256(body) != record["record_sha256"]:
            raise ArtifactReconciliationError(
                f"record hash mismatch at {kind}", code="record_hash_mismatch"
            )
        seen[kind] = record
        previous_sha256 = record["record_sha256"]

    for record in records:
        status = record["status"]
        if status in {"in_progress", "timeout", "killed"}:
            raise ArtifactReconciliationError(
                f"nonterminal record status {status}",
                code=f"record_status_{status}",
            )
        if status not in {"success", "failure"}:
            raise ArtifactReconciliationError(
                f"invalid record status {status}",
                code="invalid_record_status",
            )

    kinds = [record["kind"] for record in records]
    backend = seen.get("backend_result")
    if backend is None or seen.get("generated_input") is None or seen.get("summary") is None:
        raise ArtifactReconciliationError(
            "required record is missing", code="missing_record"
        )
    generated = seen["generated_input"]
    generated_payload = generated["payload"]
    if (
            generated["status"] != "success" or
            not isinstance(generated_payload, dict) or
            set(generated_payload) != {"config"} or
            not isinstance(generated_payload["config"], dict)):
        raise ArtifactReconciliationError(
            "generated input payload/status mismatch",
            code="generated_input_payload_mismatch",
        )

    backend_payload = backend["payload"]
    if (
            not isinstance(backend_payload, dict) or
            set(backend_payload) != {"backend", "exit_code"} or
            not isinstance(backend_payload["backend"], str) or
            not backend_payload["backend"] or
            isinstance(backend_payload["exit_code"], bool) or
            not isinstance(backend_payload["exit_code"], int)):
        raise ArtifactReconciliationError(
            "backend payload is malformed", code="backend_payload_mismatch"
        )

    if backend["status"] == "success":
        expected = [
            "generated_input",
            "backend_result",
            "benchmark_observation",
            "summary",
        ]
        if kinds != expected or seen["summary"]["status"] != "success":
            raise ArtifactReconciliationError(
                "partial or contradictory success chain",
                code="partial_success_chain",
            )
        if backend_payload["exit_code"] != 0:
            raise ArtifactReconciliationError(
                "successful backend has nonzero exit code",
                code="backend_payload_mismatch",
            )
        observation = seen["benchmark_observation"]
        payload = observation["payload"]
        score = payload.get("score") if isinstance(payload, dict) else None
        if (
                observation["status"] != "success" or
                not isinstance(payload, dict) or
                set(payload) != {"score", "unit"} or
                isinstance(score, bool) or
                not isinstance(score, (int, float)) or
                not math.isfinite(score) or
                not isinstance(payload["unit"], str) or
                not payload["unit"]):
            raise ArtifactReconciliationError(
                "successful observation payload/status mismatch",
                code="observation_payload_mismatch",
            )
        if seen["summary"]["payload"] != {"outcome": "success"}:
            raise ArtifactReconciliationError(
                "success summary contradicts backend outcome",
                code="summary_payload_mismatch",
            )
        return {"outcome": "success", "chain_head": previous_sha256}
    if backend["status"] == "failure":
        expected = ["generated_input", "backend_result", "summary"]
        if kinds != expected or seen["summary"]["status"] != "failure":
            raise ArtifactReconciliationError(
                "partial or contradictory failure chain",
                code="partial_failure_chain",
            )
        if backend_payload["exit_code"] == 0:
            raise ArtifactReconciliationError(
                "failed backend has zero exit code",
                code="backend_payload_mismatch",
            )
        if seen["summary"]["payload"] != {"outcome": "backend_failure"}:
            raise ArtifactReconciliationError(
                "failure summary contradicts backend outcome",
                code="summary_payload_mismatch",
            )
        return {"outcome": "backend_failure", "chain_head": previous_sha256}
    raise ArtifactReconciliationError(
        f"invalid backend status {backend['status']}", code="invalid_record_status"
    )
