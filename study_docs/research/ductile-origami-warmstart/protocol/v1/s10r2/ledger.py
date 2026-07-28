# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Append-only, hash-linked S10R2 event ledger and resource enforcement."""

from __future__ import annotations

import os
import fcntl
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from Tensile.ductile.evidence import (
    atomic_write_json,
    canonical_sha256,
    strict_load_json,
)
from .state_machine import Stage, TransitionError, assert_transition


class LedgerError(ValueError):
    """Ledger integrity or resume failure."""


class ResourceLimitError(LedgerError):
    """A frozen resource limit would be exceeded."""


GENESIS_DIGEST = "0" * 64


@dataclass(frozen=True)
class ResourceCounter:
    wall_s: float = 0.0
    cpu_s: float = 0.0
    gpu_s: float = 0.0
    transient_storage_bytes: int = 0

    def add(self, other: "ResourceCounter") -> "ResourceCounter":
        values = {
            "wall_s": self.wall_s + other.wall_s,
            "cpu_s": self.cpu_s + other.cpu_s,
            "gpu_s": self.gpu_s + other.gpu_s,
            "transient_storage_bytes": (
                self.transient_storage_bytes + other.transient_storage_bytes
            ),
        }
        if any(value < 0 for value in values.values()):
            raise ResourceLimitError("resource counters must be non-negative")
        return ResourceCounter(**values)


@dataclass(frozen=True)
class FrozenResourceCaps:
    wall_s: float
    cpu_s: float
    gpu_s: float
    transient_storage_bytes: int

    def __post_init__(self) -> None:
        if (
            self.wall_s <= 0
            or self.cpu_s <= 0
            or self.gpu_s <= 0
            or self.transient_storage_bytes <= 0
        ):
            raise ResourceLimitError("all frozen resource caps must be positive")


@dataclass(frozen=True)
class ResumeCursor:
    event_id: int
    event_digest: str
    stage: str
    stream_id: str | None
    next_chunk_index: int | None


def enforce_stop(
    current: ResourceCounter,
    reservation: ResourceCounter,
    caps: FrozenResourceCaps,
) -> ResourceCounter:
    """Reserve the next atomic unit or reject it before work begins."""

    projected = current.add(reservation)
    limits = {
        "wall_s": (projected.wall_s, caps.wall_s),
        "cpu_s": (projected.cpu_s, caps.cpu_s),
        "gpu_s": (projected.gpu_s, caps.gpu_s),
        "transient_storage_bytes": (
            projected.transient_storage_bytes,
            caps.transient_storage_bytes,
        ),
    }
    exceeded = [name for name, (value, cap) in limits.items() if value > cap]
    if exceeded:
        raise ResourceLimitError(
            "next atomic unit exceeds frozen resource cap(s): " + ", ".join(exceeded)
        )
    return projected


class RunLedger:
    """One immutable JSON file per event; no mutable index is authoritative."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.events_root = self.root / "events"

    def _event_paths(self) -> list[Path]:
        if not self.events_root.exists():
            return []
        return sorted(
            path
            for path in self.events_root.iterdir()
            if path.is_file() and path.name.endswith(".json")
        )

    @staticmethod
    def _event_body(event: Mapping[str, Any]) -> dict[str, Any]:
        body = dict(event)
        body.pop("event_digest", None)
        return body

    @classmethod
    def _validate_event(
        cls,
        event: Mapping[str, Any],
        *,
        expected_id: int,
        expected_parent: str,
    ) -> str:
        required = {
            "schema_version",
            "event_id",
            "parent_digest",
            "stage",
            "contract_digest",
            "lock_digest",
            "resource_counter",
            "event_digest",
        }
        missing = sorted(required.difference(event))
        if missing:
            raise LedgerError(f"ledger event missing keys: {missing}")
        if event["schema_version"] != 1:
            raise LedgerError("unsupported ledger schema")
        if event["event_id"] != expected_id:
            raise LedgerError(
                f"ledger event id mismatch: expected {expected_id}, got {event['event_id']}"
            )
        if event["parent_digest"] != expected_parent:
            raise LedgerError("ledger parent digest mismatch")
        actual_digest = canonical_sha256(cls._event_body(event))
        if event["event_digest"] != actual_digest:
            raise LedgerError("ledger event digest mismatch")
        return actual_digest

    def load(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        parent = GENESIS_DIGEST
        for event_id, path in enumerate(self._event_paths()):
            expected_name_prefix = f"{event_id:08d}-"
            if not path.name.startswith(expected_name_prefix):
                raise LedgerError(f"unexpected ledger filename {path.name}")
            event = strict_load_json(path)
            if not isinstance(event, Mapping):
                raise LedgerError(f"ledger event is not an object: {path}")
            digest = self._validate_event(
                event,
                expected_id=event_id,
                expected_parent=parent,
            )
            if path.stem != f"{event_id:08d}-{digest}":
                raise LedgerError(f"ledger filename/digest mismatch: {path}")
            events.append(dict(event))
            parent = digest
        for previous, following in zip(events, events[1:]):
            try:
                assert_transition(previous["stage"], following["stage"])
            except TransitionError as error:
                raise LedgerError(f"ledger stage transition invalid: {error}") from error
            if (
                following["contract_digest"] != previous["contract_digest"]
                or following["lock_digest"] != previous["lock_digest"]
            ):
                raise LedgerError("ledger contract/lock identity changed")
            before = resource_counter_from_event(previous)
            after = resource_counter_from_event(following)
            for field in asdict(before):
                if getattr(after, field) < getattr(before, field):
                    raise LedgerError(f"ledger resource counter decreased: {field}")
        return events

    def append(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        events = self.load()
        event_id = len(events)
        parent = events[-1]["event_digest"] if events else GENESIS_DIGEST
        if "event_id" in payload or "event_digest" in payload or "parent_digest" in payload:
            raise LedgerError("caller may not supply ledger identity fields")
        if events:
            try:
                assert_transition(events[-1]["stage"], str(payload.get("stage")))
            except TransitionError as error:
                raise LedgerError(f"ledger stage transition invalid: {error}") from error
        body = {
            "schema_version": 1,
            "event_id": event_id,
            "parent_digest": parent,
            **dict(payload),
        }
        body.setdefault("stream_id", None)
        body.setdefault("chunk_index", None)
        body.setdefault("draw_interval", None)
        body.setdefault("fixture_digest", None)
        body.setdefault("process_version", "s10r2/v1")
        body.setdefault("support_observation_ref", None)
        body.setdefault("exit_status", "complete")
        body.setdefault("resume_cursor", None)
        required = {"stage", "contract_digest", "lock_digest", "resource_counter"}
        missing = sorted(required.difference(body))
        if missing:
            raise LedgerError(f"ledger append missing keys: {missing}")
        digest = canonical_sha256(body)
        event = {**body, "event_digest": digest}
        self.events_root.mkdir(parents=True, exist_ok=True)
        path = self.events_root / f"{event_id:08d}-{digest}.json"
        atomic_write_json(path, event, exclusive=True)
        return event

    def acquire_writer(self):
        """Acquire the single non-blocking writer guard for one command."""

        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / ".writer.lock"
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(descriptor)
            raise LedgerError("another S10R2 writer holds the run lock")
        return _WriterGuard(descriptor)

    def resume_cursor(self) -> ResumeCursor:
        events = self.load()
        if not events:
            return ResumeCursor(-1, GENESIS_DIGEST, "PRELOCK", None, None)
        event = events[-1]
        cursor = event.get("resume_cursor")
        if cursor is not None and not isinstance(cursor, Mapping):
            raise LedgerError("resume_cursor must be an object or null")
        return ResumeCursor(
            event_id=event["event_id"],
            event_digest=event["event_digest"],
            stage=str(event["stage"]),
            stream_id=(None if cursor is None else cursor.get("stream_id")),
            next_chunk_index=(None if cursor is None else cursor.get("next_chunk_index")),
        )

    def fsync(self) -> None:
        """Make the current directory entries durable at a safe boundary."""

        if not self.events_root.exists():
            return
        descriptor = os.open(self.events_root, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def resource_counter_from_event(event: Mapping[str, Any]) -> ResourceCounter:
    value = event.get("resource_counter")
    if not isinstance(value, Mapping):
        raise LedgerError("resource_counter must be an object")
    try:
        counter = ResourceCounter(
            wall_s=float(value["wall_s"]),
            cpu_s=float(value["cpu_s"]),
            gpu_s=float(value["gpu_s"]),
            transient_storage_bytes=int(value["transient_storage_bytes"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise LedgerError(f"invalid resource_counter: {error}") from error
    if any(number < 0 for number in asdict(counter).values()):
        raise LedgerError("resource counters must be non-negative")
    return counter


class _WriterGuard:
    def __init__(self, descriptor: int):
        self.descriptor = descriptor

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        try:
            fcntl.flock(self.descriptor, fcntl.LOCK_UN)
        finally:
            os.close(self.descriptor)
        return False
