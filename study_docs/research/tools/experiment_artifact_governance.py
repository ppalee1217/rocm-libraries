"""Deterministic reference rules for experiment artifact governance.

This module projects operational corrections and validates candidate-to-seal
transitions.  It deliberately does not read experiment outcomes.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from itertools import groupby
from typing import Any, Iterable


class GovernanceError(ValueError):
    """The artifact set cannot be projected without ambiguity."""


PROJECTION_RULE = "operational-last-correction-wins-v1"
REGISTRY_SCHEMA_VERSION = "sealed-layer-c-registry-v1"
TRANSITION_REGISTRY_SCHEMA_VERSION = "sealed-transition-registry-v1"
RFC3339_UTC = re.compile(
    r"^(?P<second>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(?P<fraction>\d+))?Z$"
)

SUCCESSOR_CHANGE_FIELDS = frozenset(
    {
        "effective_contract",
        "effective_lock",
        "source_or_input",
        "seed",
        "workload",
        "fixture",
        "threshold",
        "stopping_rule",
        "outcome_matrix",
        "formal_selection",
        "formal_mapping",
        "formal_measurement",
        "correctness_or_noise_evidence",
        "decision",
        "sample_inclusion",
        "execution_order",
        "comparability",
        "measurement_boundary",
        "lineage",
        "claim",
        "edge",
        "post_label_desired_outcome_relaxation",
        "explicit_scientific_or_safety_identity",
    }
)

BOOKKEEPING_CHANGE_FIELDS = frozenset(
    {
        "json_or_yaml_serialization",
        "timestamp",
        "display_label",
        "live_status",
        "resource_estimate",
        "command_summary",
        "heartbeat",
        "agent_routing",
        "derived_cache",
        "unrelated_workspace_drift",
        "preseal_candidate_revision",
    }
)
ALL_CHANGE_FIELDS = SUCCESSOR_CHANGE_FIELDS | BOOKKEEPING_CHANGE_FIELDS
EVIDENCE_REUSE_VALUES = frozenset(
    {"reusable_formal_input", "diagnostic_only", "forbidden_to_read"}
)


def _reject_constant(value: str) -> None:
    raise GovernanceError(f"non-finite JSON constant: {value}")


def _object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GovernanceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json_loads(raw: bytes) -> dict[str, Any]:
    """Parse one UTF-8 JSON object while rejecting ambiguous JSON."""

    if not isinstance(raw, bytes):
        raise GovernanceError("artifact bytes must be bytes")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_from_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GovernanceError("artifact is not strict UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise GovernanceError("artifact root must be an object")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Return the shared canonical JSON representation."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise GovernanceError("value is not canonical finite JSON") from exc


def raw_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _exact_keys(value: dict[str, Any], expected: set[str], kind: str) -> None:
    actual = set(value)
    if actual != expected:
        raise GovernanceError(
            f"{kind} keys differ: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise GovernanceError(f"{field} must be a nonempty string")
    return value


def _target_key(path: Any, sequence_or_id: Any) -> tuple[str, str]:
    return (
        _nonempty_string(path, "target.path"),
        _nonempty_string(sequence_or_id, "target.sequence_or_id"),
    )


def _timestamp_key(value: Any) -> tuple[datetime, Decimal]:
    timestamp = _nonempty_string(value, "recorded_at_utc")
    match = RFC3339_UTC.fullmatch(timestamp)
    if match is None:
        raise GovernanceError("recorded_at_utc must be RFC3339 UTC")
    try:
        second = datetime.fromisoformat(match.group("second") + "+00:00")
        fraction_text = match.group("fraction")
        fraction = Decimal(f"0.{fraction_text}") if fraction_text else Decimal(0)
    except (ValueError, InvalidOperation) as exc:
        raise GovernanceError("recorded_at_utc is not a real timestamp") from exc
    return second, fraction


def _field_set(value: Any, field: str) -> frozenset[str]:
    if not isinstance(value, list):
        raise GovernanceError(f"{field} must be a list")
    fields = [_nonempty_string(item, field) for item in value]
    if len(fields) != len(set(fields)):
        raise GovernanceError(f"{field} contains duplicates")
    return frozenset(fields)


def _nonempty_field_set(value: Any, field: str) -> frozenset[str]:
    fields = _field_set(value, field)
    if not fields:
        raise GovernanceError(f"{field} must not be empty")
    return fields


def _json_pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _json_pointer_unescape(value: str) -> str:
    if re.search(r"~(?![01])", value):
        raise GovernanceError("JSON pointer contains an invalid escape")
    return value.replace("~1", "/").replace("~0", "~")


def _payload_leaves(value: Any, pointer: str = "") -> dict[str, Any]:
    if isinstance(value, dict) and value:
        leaves: dict[str, Any] = {}
        for key in sorted(value):
            child = f"{pointer}/{_json_pointer_escape(key)}"
            leaves.update(_payload_leaves(value[key], child))
        return leaves
    if isinstance(value, list) and value:
        leaves = {}
        for index, child_value in enumerate(value):
            leaves.update(_payload_leaves(child_value, f"{pointer}/{index}"))
        return leaves
    return {pointer: value}


def _pointer_set(value: Any, field: str) -> frozenset[str]:
    pointers = _field_set(value, field)
    for pointer in pointers:
        if pointer and not pointer.startswith("/"):
            raise GovernanceError(f"{field} contains a non-JSON-pointer value")
        for segment in pointer.split("/")[1:]:
            decoded = _json_pointer_unescape(segment)
            if _json_pointer_escape(decoded) != segment:
                raise GovernanceError(f"{field} contains a noncanonical JSON pointer")
    return pointers


def _parse_layer_c_registry(
    registry_raw: bytes,
    expected_registry_sha256: str,
) -> list[tuple[str, re.Pattern[str], re.Pattern[str], frozenset[str], frozenset[str]]]:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_registry_sha256):
        raise GovernanceError("sealed Layer-C registry hash is malformed")
    if raw_sha256(registry_raw) != expected_registry_sha256:
        raise GovernanceError("sealed Layer-C registry identity differs")
    registry = strict_json_loads(registry_raw)
    if canonical_json_bytes(registry) != registry_raw:
        raise GovernanceError("sealed Layer-C registry is not canonical JSON")
    _exact_keys(
        registry,
        {"event_type", "schema_version", "rules"},
        "sealed Layer-C registry",
    )
    if registry["event_type"] != "sealed_layer_c_registry":
        raise GovernanceError("Layer-C registry event type differs")
    if registry["schema_version"] != REGISTRY_SCHEMA_VERSION:
        raise GovernanceError("Layer-C registry schema version differs")
    if not isinstance(registry["rules"], list):
        raise GovernanceError("Layer-C registry rules must be a list")

    parsed = []
    seen_rule_ids: set[str] = set()
    for entry in registry["rules"]:
        if not isinstance(entry, dict):
            raise GovernanceError("Layer-C registry rule must be an object")
        _exact_keys(
            entry,
            {
                "rule_id",
                "path_pattern",
                "sequence_or_id_pattern",
                "payload_leaf_pointers",
                "correctable_leaf_pointers",
            },
            "Layer-C registry rule",
        )
        rule_id = _nonempty_string(entry["rule_id"], "rule_id")
        if rule_id in seen_rule_ids:
            raise GovernanceError("duplicate Layer-C registry rule ID")
        seen_rule_ids.add(rule_id)
        path_pattern_text = _nonempty_string(entry["path_pattern"], "path_pattern")
        sequence_pattern_text = _nonempty_string(
            entry["sequence_or_id_pattern"], "sequence_or_id_pattern"
        )
        try:
            path_pattern = re.compile(path_pattern_text)
            sequence_pattern = re.compile(sequence_pattern_text)
        except re.error as exc:
            raise GovernanceError("Layer-C registry contains an invalid pattern") from exc
        payload_pointers = _pointer_set(
            entry["payload_leaf_pointers"], "payload_leaf_pointers"
        )
        correctable_pointers = _pointer_set(
            entry["correctable_leaf_pointers"], "correctable_leaf_pointers"
        )
        if not correctable_pointers <= payload_pointers:
            raise GovernanceError("correctable leaves exceed payload schema")
        parsed.append(
            (
                rule_id,
                path_pattern,
                sequence_pattern,
                payload_pointers,
                correctable_pointers,
            )
        )
    return parsed


def _parse_transition_registry(
    registry_raw: bytes,
    expected_registry_sha256: str,
) -> tuple[frozenset[str], dict[str, str], dict[str, str]]:
    """Validate the sealed authority and scientific-scope registry."""

    if not re.fullmatch(r"[0-9a-f]{64}", expected_registry_sha256):
        raise GovernanceError("sealed transition registry hash is malformed")
    if raw_sha256(registry_raw) != expected_registry_sha256:
        raise GovernanceError("sealed transition registry identity differs")
    registry = strict_json_loads(registry_raw)
    if canonical_json_bytes(registry) != registry_raw:
        raise GovernanceError("sealed transition registry is not canonical JSON")
    _exact_keys(
        registry,
        {
            "event_type",
            "schema_version",
            "approved_authorities",
            "payload_scope_by_pointer",
            "artifact_scope_by_id",
        },
        "sealed transition registry",
    )
    if registry["event_type"] != "sealed_transition_registry":
        raise GovernanceError("transition registry event type differs")
    if registry["schema_version"] != TRANSITION_REGISTRY_SCHEMA_VERSION:
        raise GovernanceError("transition registry schema version differs")
    approved_authorities = _nonempty_field_set(
        registry["approved_authorities"], "approved_authorities"
    )

    payload_scopes = registry["payload_scope_by_pointer"]
    if not isinstance(payload_scopes, dict):
        raise GovernanceError("payload_scope_by_pointer must be an object")
    _pointer_set(list(payload_scopes), "payload_scope_by_pointer")
    for pointer, scope in payload_scopes.items():
        if _nonempty_string(scope, f"payload scope for {pointer!r}") not in SUCCESSOR_CHANGE_FIELDS:
            raise GovernanceError("payload registry contains a non-scientific scope")

    artifact_scopes = registry["artifact_scope_by_id"]
    if not isinstance(artifact_scopes, dict):
        raise GovernanceError("artifact_scope_by_id must be an object")
    for artifact_id, scope in artifact_scopes.items():
        _nonempty_string(artifact_id, "artifact_scope_by_id key")
        if _nonempty_string(scope, f"artifact scope for {artifact_id!r}") not in SUCCESSOR_CHANGE_FIELDS:
            raise GovernanceError("artifact registry contains a non-scientific scope")
    return approved_authorities, payload_scopes, artifact_scopes


def _match_layer_c_rule(
    key: tuple[str, str],
    rules: list[
        tuple[str, re.Pattern[str], re.Pattern[str], frozenset[str], frozenset[str]]
    ],
) -> tuple[str, re.Pattern[str], re.Pattern[str], frozenset[str], frozenset[str]]:
    matches = [
        rule
        for rule in rules
        if rule[1].fullmatch(key[0]) and rule[2].fullmatch(key[1])
    ]
    if len(matches) != 1:
        raise GovernanceError("operational target has no unique sealed Layer-C rule")
    return matches[0]


def _parse_operational_record(raw: bytes) -> tuple[tuple[str, str], dict[str, Any]]:
    value = strict_json_loads(raw)
    _exact_keys(
        value,
        {
            "event_type",
            "artifact_layer",
            "path",
            "sequence_or_id",
            "payload",
        },
        "operational record",
    )
    if value["event_type"] != "operational_record":
        raise GovernanceError("original event type is not operational_record")
    if value["artifact_layer"] != "operational_bookkeeping":
        raise GovernanceError("correction target is not Layer C")
    if not isinstance(value["payload"], dict):
        raise GovernanceError("operational payload must be an object")
    key = _target_key(value["path"], value["sequence_or_id"])
    return key, value


def _parse_correction(
    raw: bytes,
) -> tuple[tuple[str, str], dict[str, Any], tuple[datetime, Decimal]]:
    value = strict_json_loads(raw)
    if canonical_json_bytes(value) != raw:
        raise GovernanceError("correction event is not canonical JSON")
    _exact_keys(
        value,
        {
            "event_type",
            "target",
            "reason",
            "corrected_payload",
            "author_or_actor",
            "recorded_at_utc",
            "projection_rule",
            "scientific_impact",
        },
        "correction event",
    )
    if value["event_type"] != "operational_correction":
        raise GovernanceError("event type is not operational_correction")
    if value["projection_rule"] != PROJECTION_RULE:
        raise GovernanceError("unknown correction projection rule")
    if value["scientific_impact"] != "none":
        raise GovernanceError("scientific impact requires amendment or successor")
    _nonempty_string(value["reason"], "reason")
    _nonempty_string(value["author_or_actor"], "author_or_actor")
    timestamp = _timestamp_key(value["recorded_at_utc"])
    if not isinstance(value["corrected_payload"], dict):
        raise GovernanceError("corrected_payload must be a complete object")
    target = value["target"]
    if not isinstance(target, dict):
        raise GovernanceError("target must be an object")
    _exact_keys(target, {"path", "sequence_or_id", "raw_sha256"}, "target")
    target_key = _target_key(target["path"], target["sequence_or_id"])
    digest = _nonempty_string(target["raw_sha256"], "target.raw_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise GovernanceError("target.raw_sha256 is malformed")
    return target_key, value, timestamp


def project_operational_records(
    original_records: Iterable[bytes],
    correction_events: Iterable[bytes],
    layer_c_registry_raw: bytes,
    expected_registry_sha256: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Project Layer-C records with deterministic correction semantics.

    Original bytes are never modified.  The returned dictionary is a derived
    view keyed by an injective ``(path, sequence_or_id)`` tuple. The registry is
    the sealed classification and payload-field boundary; event self-labels do
    not grant correction eligibility.
    """

    registry = _parse_layer_c_registry(
        layer_c_registry_raw, expected_registry_sha256
    )
    originals: dict[
        tuple[str, str],
        tuple[
            bytes,
            dict[str, Any],
            tuple[str, re.Pattern[str], re.Pattern[str], frozenset[str], frozenset[str]],
        ],
    ] = {}
    for raw in original_records:
        key, value = _parse_operational_record(raw)
        if key in originals:
            raise GovernanceError("duplicate or ambiguous original target")
        rule = _match_layer_c_rule(key, registry)
        payload_pointers = rule[3]
        if not set(_payload_leaves(value["payload"])) <= payload_pointers:
            raise GovernanceError("original payload exceeds sealed Layer-C schema")
        originals[key] = (raw, value, rule)

    parsed: list[
        tuple[tuple[str, str], tuple[datetime, Decimal], str, dict[str, Any]]
    ] = []
    for raw in correction_events:
        correction_digest = raw_sha256(raw)
        key, value, timestamp = _parse_correction(raw)
        if key not in originals:
            raise GovernanceError("correction target is not sealed Layer C")
        original_raw, original_value, rule = originals[key]
        if value["target"]["raw_sha256"] != raw_sha256(original_raw):
            raise GovernanceError("correction target raw hash differs")
        payload_pointers, correctable_pointers = rule[3], rule[4]
        corrected_payload = value["corrected_payload"]
        corrected_leaves = _payload_leaves(corrected_payload)
        if set(corrected_leaves) != payload_pointers:
            raise GovernanceError("corrected payload differs from sealed Layer-C schema")
        original_leaves = _payload_leaves(original_value["payload"])
        changed_pointers = {
            pointer
            for pointer in payload_pointers
            if pointer not in original_leaves
            or canonical_json_bytes(corrected_leaves[pointer])
            != canonical_json_bytes(original_leaves[pointer])
        }
        if not changed_pointers <= correctable_pointers:
            raise GovernanceError("correction changes an immutable Layer-C leaf")
        parsed.append((key, timestamp, correction_digest, value))

    parsed.sort(key=lambda row: (row[0], row[1], row[2]))
    effective = {key: dict(value["payload"]) for key, (_, value, _rule) in originals.items()}
    for key, target_rows_iterator in groupby(parsed, key=lambda row: row[0]):
        target_rows = list(target_rows_iterator)
        timestamp_groups = [
            list(rows)
            for _timestamp, rows in groupby(target_rows, key=lambda row: row[1])
        ]
        if timestamp_groups and len(timestamp_groups[-1]) > 1:
            raise GovernanceError("unresolved corrections share one timestamp")
        for timestamp_group in timestamp_groups:
            if len(timestamp_group) == 1:
                effective[key] = dict(timestamp_group[0][3]["corrected_payload"])
            # By the fixed projection rule, a conflicting earlier group is
            # superseded by the later unique complete correction. An unresolved
            # latest group failed above.

    for key, payload in effective.items():
        payload_pointers = originals[key][2][3]
        if set(_payload_leaves(payload)) != payload_pointers:
            raise GovernanceError("effective payload is incomplete for sealed Layer-C schema")

    return {key: effective[key] for key in sorted(effective)}


def select_seal_candidate(
    candidate_records: Iterable[bytes], selected_raw_sha256: str
) -> dict[str, Any]:
    """Select exactly one complete Layer-B revision by raw content hash."""

    if not re.fullmatch(r"[0-9a-f]{64}", selected_raw_sha256):
        raise GovernanceError("selected candidate hash is malformed")
    matches: list[bytes] = []
    for raw in candidate_records:
        digest = raw_sha256(raw)
        if digest == selected_raw_sha256:
            matches.append(raw)
    if len(matches) != 1:
        raise GovernanceError("selected candidate is absent or ambiguous")

    value = strict_json_loads(matches[0])
    _exact_keys(
        value,
        {
            "event_type",
            "artifact_layer",
            "path",
            "revision",
            "candidate_status",
            "payload",
        },
        "candidate",
    )
    if value["event_type"] != "candidate_revision":
        raise GovernanceError("candidate event type differs")
    if value["artifact_layer"] != "pre_seal_candidate":
        raise GovernanceError("candidate is not Layer B")
    _nonempty_string(value["path"], "candidate.path")
    if not isinstance(value["revision"], int) or isinstance(value["revision"], bool):
        raise GovernanceError("candidate revision must be an integer")
    if value["revision"] < 1:
        raise GovernanceError("candidate revision must be positive")
    if not isinstance(value["payload"], dict):
        raise GovernanceError("candidate payload must be an object")
    if value["candidate_status"] != "complete":
        raise GovernanceError("partial candidate cannot be sealed")
    return value


def _safe_repo_relative_path(value: Any) -> str:
    path = _nonempty_string(value, "artifact path")
    if (
        path.startswith("/")
        or "\\" in path
        or any(segment in {"", ".", ".."} for segment in path.split("/"))
        or any(ord(character) < 32 or ord(character) == 127 for character in path)
    ):
        raise GovernanceError("artifact path must be a safe repo-relative path")
    return path


def _artifact_inventory(
    value: Any,
) -> tuple[tuple[dict[str, str], ...], dict[str, dict[str, str]]]:
    if not isinstance(value, list) or not value:
        raise GovernanceError("artifact_inventory must be a nonempty ordered array")
    records: list[dict[str, str]] = []
    by_id: dict[str, dict[str, str]] = {}
    paths: set[str] = set()
    for record in value:
        if not isinstance(record, dict):
            raise GovernanceError("artifact inventory record must be an object")
        _exact_keys(
            record,
            {"artifact_id", "path", "sha256"},
            "artifact inventory record",
        )
        artifact_id = _nonempty_string(record["artifact_id"], "artifact_id")
        path = _safe_repo_relative_path(record["path"])
        digest = _nonempty_string(record["sha256"], "artifact sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise GovernanceError("artifact sha256 must be lowercase 64-hex")
        if artifact_id in by_id:
            raise GovernanceError("artifact inventory contains duplicate artifact IDs")
        if path in paths:
            raise GovernanceError("artifact inventory contains duplicate paths")
        normalized = {"artifact_id": artifact_id, "path": path, "sha256": digest}
        records.append(normalized)
        by_id[artifact_id] = normalized
        paths.add(path)
    artifact_ids = [record["artifact_id"] for record in records]
    if artifact_ids != sorted(artifact_ids, key=lambda item: item.encode("utf-8")):
        raise GovernanceError("artifact inventory is not ordered by artifact_id UTF-8 bytes")
    return tuple(records), by_id


def _validate_sealed_shape(
    value: dict[str, Any],
) -> tuple[str, tuple[dict[str, str], ...], dict[str, dict[str, str]]]:
    event_type = value.get("event_type")
    if event_type == "sealed_scientific_milestone":
        _exact_keys(
            value,
            {
                "event_type",
                "artifact_layer",
                "milestone_id",
                "artifact_inventory",
                "payload",
            },
            "sealed milestone",
        )
    elif event_type in {"scientific_amendment", "scientific_successor"}:
        _exact_keys(
            value,
            {
                "event_type",
                "artifact_layer",
                "milestone_id",
                "artifact_inventory",
                "predecessor",
                "reason",
                "authority",
                "affected_scope",
                "evidence_reuse_boundary",
                "payload",
            },
            "sealed transition",
        )
        _nonempty_string(value["reason"], "reason")
        _nonempty_string(value["authority"], "authority")
        link = value["predecessor"]
        if not isinstance(link, dict):
            raise GovernanceError("predecessor link must be an object")
        _exact_keys(link, {"milestone_id", "raw_sha256"}, "predecessor link")
        _nonempty_string(link["milestone_id"], "predecessor.milestone_id")
        predecessor_hash = _nonempty_string(
            link["raw_sha256"], "predecessor.raw_sha256"
        )
        if not re.fullmatch(r"[0-9a-f]{64}", predecessor_hash):
            raise GovernanceError("predecessor raw hash is malformed")
        affected_scope = _nonempty_field_set(value["affected_scope"], "affected_scope")
        if not affected_scope <= SUCCESSOR_CHANGE_FIELDS:
            raise GovernanceError("affected_scope contains a non-scientific or unknown field")
        if not isinstance(value["evidence_reuse_boundary"], dict):
            raise GovernanceError("evidence reuse boundary must be an object")
        if any(
            reuse not in EVIDENCE_REUSE_VALUES
            for reuse in value["evidence_reuse_boundary"].values()
        ):
            raise GovernanceError(
                "evidence reuse boundary contains an unknown classification"
            )
    else:
        raise GovernanceError("artifact is not a sealed milestone")

    if value["artifact_layer"] != "sealed_scientific_milestone":
        raise GovernanceError("sealed artifact is not Layer A")
    milestone_id = _nonempty_string(value["milestone_id"], "milestone_id")
    artifact_inventory, inventory_by_id = _artifact_inventory(value["artifact_inventory"])
    if not isinstance(value["payload"], dict):
        raise GovernanceError("sealed payload must be an object")
    return milestone_id, artifact_inventory, inventory_by_id


def validate_sealed_transition(
    predecessor_raw: bytes,
    successor_raw: bytes,
    transition_registry_raw: bytes,
    expected_transition_registry_sha256: str,
) -> dict[str, Any]:
    """Validate one registry-authorized, scope-complete Layer-A transition."""

    approved_authorities, payload_scopes, artifact_scopes = _parse_transition_registry(
        transition_registry_raw, expected_transition_registry_sha256
    )
    predecessor = strict_json_loads(predecessor_raw)
    successor = strict_json_loads(successor_raw)
    predecessor_id, _predecessor_inventory, predecessor_by_id = _validate_sealed_shape(
        predecessor
    )
    if successor.get("event_type") not in {
        "scientific_amendment",
        "scientific_successor",
    }:
        raise GovernanceError("sealed milestone requires amendment or successor")
    successor_id, _successor_inventory, successor_by_id = _validate_sealed_shape(
        successor
    )
    if successor_id == predecessor_id:
        raise GovernanceError("sealed milestone cannot be overwritten in place")
    if successor["predecessor"] != {
        "milestone_id": predecessor_id,
        "raw_sha256": raw_sha256(predecessor_raw),
    }:
        raise GovernanceError("predecessor identity differs")
    if successor["authority"] not in approved_authorities:
        raise GovernanceError("successor authority is not approved by the transition registry")

    predecessor_leaves = _payload_leaves(predecessor["payload"])
    successor_leaves = _payload_leaves(successor["payload"])
    observed_pointers = set(predecessor_leaves) | set(successor_leaves)
    unknown_pointers = observed_pointers - set(payload_scopes)
    if unknown_pointers:
        raise GovernanceError(
            f"transition registry does not classify payload pointers: {sorted(unknown_pointers)}"
        )
    observed_artifact_ids = set(predecessor_by_id) | set(successor_by_id)
    unknown_artifact_ids = observed_artifact_ids - set(artifact_scopes)
    if unknown_artifact_ids:
        raise GovernanceError(
            f"transition registry does not classify artifact IDs: {sorted(unknown_artifact_ids)}"
        )

    for artifact_id in set(predecessor_by_id) & set(successor_by_id):
        if canonical_json_bytes(predecessor_by_id[artifact_id]) != canonical_json_bytes(
            successor_by_id[artifact_id]
        ):
            raise GovernanceError(
                "an artifact ID cannot be reused with a changed path or hash"
            )

    reuse_boundary = successor["evidence_reuse_boundary"]
    if set(reuse_boundary) != set(predecessor_by_id):
        raise GovernanceError("evidence reuse boundary does not classify every artifact")
    for artifact_id, classification in reuse_boundary.items():
        if classification == "reusable_formal_input":
            if artifact_id not in successor_by_id:
                raise GovernanceError("reusable formal input is absent from successor")
            if canonical_json_bytes(predecessor_by_id[artifact_id]) != canonical_json_bytes(
                successor_by_id[artifact_id]
            ):
                raise GovernanceError("reusable formal input differs in successor")
        elif artifact_id in successor_by_id:
            raise GovernanceError(
                "diagnostic-only or forbidden predecessor artifact remains in successor"
            )

    actual_changed_scopes: set[str] = set()
    for pointer in observed_pointers:
        if (
            pointer not in predecessor_leaves
            or pointer not in successor_leaves
            or canonical_json_bytes(predecessor_leaves[pointer])
            != canonical_json_bytes(successor_leaves[pointer])
        ):
            actual_changed_scopes.add(payload_scopes[pointer])
    for artifact_id in observed_artifact_ids:
        if (
            artifact_id not in predecessor_by_id
            or artifact_id not in successor_by_id
            or canonical_json_bytes(predecessor_by_id[artifact_id])
            != canonical_json_bytes(successor_by_id[artifact_id])
        ):
            actual_changed_scopes.add(artifact_scopes[artifact_id])
    if not actual_changed_scopes:
        raise GovernanceError("sealed transition has no actual scientific change")
    if set(successor["affected_scope"]) != actual_changed_scopes:
        raise GovernanceError(
            "affected_scope differs from registry-derived actual scientific scopes"
        )
    return successor


def requires_successor(change_flags: dict[str, bool]) -> bool:
    """Classify whether a proposed change crosses the scientific boundary."""

    if set(change_flags) != ALL_CHANGE_FIELDS:
        raise GovernanceError(
            "change flags must completely classify the scientific and bookkeeping boundary"
        )
    if any(not isinstance(value, bool) for value in change_flags.values()):
        raise GovernanceError("change flags must be booleans")
    return any(change_flags[field] for field in SUCCESSOR_CHANGE_FIELDS)
