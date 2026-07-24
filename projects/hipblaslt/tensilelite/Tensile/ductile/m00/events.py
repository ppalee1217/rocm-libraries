# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Immutable observer snapshots and strict JSONL event writing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any
import json

from .canonical import (
    ContractError,
    MissingEvidenceError,
    _plain_finite,
    canonical_json_bytes,
    canonical_json_text,
    load_json_strict,
    sha256_bytes,
    validate_instance,
)


def _freeze_plain(value):
    if isinstance(value, dict):
        return MappingProxyType({
            key: _freeze_plain(item) for key, item in value.items()
        })
    if isinstance(value, list):
        return tuple(_freeze_plain(item) for item in value)
    return value


def freeze_payload(payload: Any):
    """Return a detached, recursively immutable, JSON-compatible snapshot."""
    return _freeze_plain(_plain_finite(payload))


def thaw_payload(payload: Any):
    if isinstance(payload, MappingProxyType):
        return {key: thaw_payload(value) for key, value in payload.items()}
    if isinstance(payload, tuple):
        return [thaw_payload(value) for value in payload]
    return payload


@dataclass(frozen=True)
class GAEvent:
    sequence: int
    event_id: str
    kind: str
    generation: int | None
    payload: Any

    def __post_init__(self):
        if self.sequence < 0:
            raise ContractError("event sequence must be non-negative")
        if not self.event_id or not self.kind:
            raise ContractError("event ID and kind must be non-empty")
        if self.generation is not None and self.generation < 0:
            raise ContractError("event generation must be non-negative")
        object.__setattr__(self, "payload", freeze_payload(self.payload))

    def to_record(self) -> dict[str, Any]:
        payload = thaw_payload(self.payload)
        payload_bytes = canonical_json_bytes(payload)
        return {
            "schema_version": "1.0",
            "sequence": self.sequence,
            "event_id": self.event_id,
            "kind": self.kind,
            "generation": self.generation,
            "payload": payload,
            "payload_sha256": sha256_bytes(payload_bytes),
        }


class JsonlEventSink:
    """Exclusive-create event sink with contiguous sequence enforcement."""

    def __init__(self, path: str | Path, *, schema_path: str | Path | None = None,
                 start_sequence: int = 0, append: bool = False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._schema = load_json_strict(schema_path) if schema_path else None
        self._event_ids = set()
        if append:
            existing = read_jsonl_events(
                self.path, schema_path=schema_path
            )
            if len(existing) != start_sequence:
                raise MissingEvidenceError(
                    "append sequence does not match durable event prefix",
                    reason_code="EVENT_APPEND_SEQUENCE_MISMATCH",
                )
            self._event_ids = {
                record["event_id"] for record, _ in existing
            }
            self._stream = self.path.open("a", encoding="utf-8")
        else:
            self._stream = self.path.open("x", encoding="utf-8")
        self._next_sequence = start_sequence
        self._closed = False

    @property
    def next_sequence(self) -> int:
        return self._next_sequence

    def __call__(self, event: GAEvent) -> None:
        self.write(event)

    def emit(self, kind: str, generation: int | None, payload: Any,
             *, event_id: str | None = None) -> GAEvent:
        event = GAEvent(
            sequence=self._next_sequence,
            event_id=event_id or f"event-{self._next_sequence:06d}",
            kind=kind,
            generation=generation,
            payload=payload,
        )
        self.write(event)
        return event

    def write(self, event: GAEvent) -> None:
        if self._closed:
            raise MissingEvidenceError(
                "cannot write to a closed event sink",
                reason_code="EVENT_SINK_CLOSED",
            )
        if event.sequence != self._next_sequence:
            raise MissingEvidenceError(
                f"non-contiguous event sequence: expected "
                f"{self._next_sequence}, got {event.sequence}",
                reason_code="EVENT_SEQUENCE_GAP",
            )
        if event.event_id in self._event_ids:
            raise MissingEvidenceError(
                f"duplicate event ID: {event.event_id}",
                reason_code="EVENT_ID_DUPLICATE",
            )
        record = event.to_record()
        if self._schema is not None:
            validate_instance(record, self._schema, label=str(self.path))
        try:
            self._stream.write(canonical_json_text(record) + "\n")
            self._stream.flush()
        except OSError as exc:
            raise MissingEvidenceError(
                f"observer sink write failed: {exc}",
                reason_code="EVENT_SINK_IO_FAILURE",
            ) from exc
        self._event_ids.add(event.event_id)
        self._next_sequence += 1

    def close(self) -> None:
        if not self._closed:
            try:
                self._stream.flush()
                self._stream.close()
            except OSError as exc:
                raise MissingEvidenceError(
                    f"observer sink close failed: {exc}",
                    reason_code="EVENT_SINK_IO_FAILURE",
                ) from exc
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
        return False


@dataclass(frozen=True)
class LifecycleKey:
    stage: str
    stable_id: str


class LifecycleTracker:
    """Validates exactly one start/finish pair per stable stage ID."""

    def __init__(self):
        self.started: set[LifecycleKey] = set()
        self.finished: set[LifecycleKey] = set()

    def start(self, stage: str, stable_id: str) -> None:
        key = LifecycleKey(stage, stable_id)
        if key in self.started:
            raise MissingEvidenceError(
                f"duplicate {stage} start for {stable_id}",
                reason_code="DUPLICATE_STAGE_START",
            )
        self.started.add(key)

    def finish(self, stage: str, stable_id: str) -> None:
        key = LifecycleKey(stage, stable_id)
        if key not in self.started or key in self.finished:
            raise MissingEvidenceError(
                f"unpaired {stage} finish for {stable_id}",
                reason_code="UNPAIRED_STAGE_FINISH",
            )
        self.finished.add(key)

    def verify_closed(self) -> None:
        missing = self.started - self.finished
        if missing:
            detail = sorted((key.stage, key.stable_id) for key in missing)
            raise MissingEvidenceError(
                f"unfinished lifecycle stages: {detail}",
                reason_code="UNFINISHED_STAGE",
            )


def read_jsonl_events(path: str | Path, *, schema_path: str | Path | None = None):
    schema = load_json_strict(schema_path) if schema_path else None
    records = []
    event_ids = set()

    def strict_object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate event key: {key}")
            value[key] = item
        return value

    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            for expected, line in enumerate(stream):
                if not line.strip():
                    raise MissingEvidenceError(
                        f"blank JSONL line in {path}",
                        reason_code="BLANK_JSONL_LINE",
                    )
                record = json.loads(line, object_pairs_hook=strict_object)
                if schema is not None:
                    validate_instance(record, schema, label=str(path))
                if record["sequence"] != expected:
                    raise MissingEvidenceError(
                        f"event sequence gap in {path}",
                        reason_code="EVENT_SEQUENCE_GAP",
                    )
                if record["event_id"] in event_ids:
                    raise MissingEvidenceError(
                        f"duplicate event ID in {path}: "
                        f"{record['event_id']}",
                        reason_code="EVENT_ID_DUPLICATE",
                    )
                event_ids.add(record["event_id"])
                payload = record["payload"]
                payload_bytes = canonical_json_bytes(payload)
                if sha256_bytes(payload_bytes) != record["payload_sha256"]:
                    raise MissingEvidenceError(
                        f"event payload checksum mismatch in {path}",
                        reason_code="EVENT_PAYLOAD_TAMPER",
                    )
                records.append((record, payload))
    except MissingEvidenceError:
        raise
    except (OSError, json.JSONDecodeError, KeyError, TypeError,
            ValueError) as exc:
        raise MissingEvidenceError(
            f"invalid event JSONL {path}: {exc}",
            reason_code="EVENT_JSONL_INVALID",
        ) from exc
    return records
