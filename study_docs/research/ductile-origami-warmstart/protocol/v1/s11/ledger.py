# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Append-only S11 ledger with an O(1) verified derived index.

Normal append validates the index plus the current tail event.  It never
reparses all prior events.  Full replay is an explicit verifier/status action,
so N chunks cost O(N), not O(N^2).
"""

from __future__ import annotations

import fcntl
import os
import stat
from pathlib import Path
from typing import Any, Mapping

from .canonical import (
    atomic_write_json,
    canonical_sha256,
    exclusive_write_json,
    strict_load_json,
)
from .state_machine import Stage


class LedgerError(ValueError):
    """The ledger is malformed, concurrently owned, or hash-chain invalid."""


GENESIS_DIGEST = "0" * 64


class ChunkLedger:
    """One zero-padded immutable JSON event per committed chunk/unit."""

    def __init__(self, root: Path | str, lock_sha256: str):
        if (
            type(lock_sha256) is not str
            or len(lock_sha256) != 64
            or any(character not in "0123456789abcdef" for character in lock_sha256)
        ):
            raise LedgerError("effective-lock SHA-256 is malformed")
        self.root = Path(root)
        self.events_root = self.root / "events"
        self.index_path = self.root / "ledger-index.json"
        self.writer_lock_path = self.root / "writer.lock"
        self.lock_sha256 = lock_sha256
        self._guard_stream: Any = None

    @staticmethod
    def event_name(index: int) -> str:
        if type(index) is not int or index < 0:
            raise LedgerError("event index must be a non-negative integer")
        return f"{index:012d}.json"

    def __enter__(self) -> "ChunkLedger":
        self.root.mkdir(parents=True, exist_ok=True)
        self.events_root.mkdir(parents=True, exist_ok=True)
        self._guard_stream = self.writer_lock_path.open("a+b")
        try:
            fcntl.flock(self._guard_stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self._guard_stream.close()
            self._guard_stream = None
            raise LedgerError("ledger already has an active writer") from error
        if not self.index_path.exists():
            if any(self.events_root.iterdir()):
                raise LedgerError("events exist without a derived index; explicit repair required")
            atomic_write_json(self.index_path, self._index(0, GENESIS_DIGEST, {}))
        self._recover_single_published_tail()
        self._load_tail_verified()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        assert self._guard_stream is not None
        fcntl.flock(self._guard_stream.fileno(), fcntl.LOCK_UN)
        self._guard_stream.close()
        self._guard_stream = None

    def _require_writer(self) -> None:
        if self._guard_stream is None:
            raise LedgerError("ledger append requires the exclusive writer guard")

    def _index(
        self, event_count: int, last_digest: str, per_stream_next_chunk: Mapping[str, int]
    ) -> dict[str, Any]:
        body = {
            "document_kind": "s11_ledger_index",
            "schema_version": 1,
            "checkpoint_id": "S11",
            "lock_sha256": self.lock_sha256,
            "event_count": event_count,
            "last_digest": last_digest,
            "per_stream_next_chunk": dict(per_stream_next_chunk),
        }
        return {**body, "index_digest": canonical_sha256(body)}

    def _validate_index(self, document: Mapping[str, Any]) -> None:
        expected = {
            "document_kind",
            "schema_version",
            "checkpoint_id",
            "lock_sha256",
            "event_count",
            "last_digest",
            "per_stream_next_chunk",
            "index_digest",
        }
        if set(document) != expected:
            raise LedgerError("ledger index schema/unknown-property failure")
        body = dict(document)
        recorded = body.pop("index_digest")
        if canonical_sha256(body) != recorded:
            raise LedgerError("ledger index digest mismatch")
        if (
            document["document_kind"] != "s11_ledger_index"
            or document["schema_version"] != 1
            or document["checkpoint_id"] != "S11"
            or document["lock_sha256"] != self.lock_sha256
            or type(document["event_count"]) is not int
            or document["event_count"] < 0
            or type(document["per_stream_next_chunk"]) is not dict
        ):
            raise LedgerError("ledger index identity/type failure")
        if any(type(key) is not str or type(value) is not int or value < 0 for key, value in document["per_stream_next_chunk"].items()):
            raise LedgerError("ledger stream index is malformed")

    def _validate_event(
        self,
        event: Mapping[str, Any],
        *,
        expected_index: int,
        expected_previous: str,
    ) -> None:
        expected = {
            "document_kind",
            "schema_version",
            "checkpoint_id",
            "event_index",
            "stage",
            "stream_id",
            "chunk_index",
            "nominal_slots",
            "accepted_count",
            "disposition_counts",
            "chunk_relative_path",
            "chunk_byte_length",
            "chunk_file_sha256",
            "chunk_semantic_sha256",
            "previous_event_digest",
            "lock_sha256",
            "event_digest",
        }
        if set(event) != expected:
            raise LedgerError("ledger event schema/unknown-property failure")
        body = dict(event)
        recorded = body.pop("event_digest")
        if canonical_sha256(body) != recorded:
            raise LedgerError("ledger event digest mismatch")
        if (
            event["document_kind"] != "s11_chunk_metadata_event"
            or event["schema_version"] != 2
            or event["checkpoint_id"] != "S11"
            or event["event_index"] != expected_index
            or event["previous_event_digest"] != expected_previous
            or event["lock_sha256"] != self.lock_sha256
        ):
            raise LedgerError("ledger event chain/binding failure")
        Stage(event["stage"])
        if (
            type(event["stream_id"]) is not str
            or type(event["chunk_index"]) is not int
            or type(event["nominal_slots"]) is not int
            or type(event["accepted_count"]) is not int
            or event["chunk_index"] < 0
            or event["nominal_slots"] < 0
            or not 0 <= event["accepted_count"] <= event["nominal_slots"]
        ):
            raise LedgerError("ledger event counts/types are invalid")
        counts = event["disposition_counts"]
        if (
            type(counts) is not dict
            or set(counts)
            != {
                "accepted", "validator_rejected", "validator_exception",
                "malformed_validator_result",
            }
            or any(type(value) is not int or value < 0 for value in counts.values())
            or sum(counts.values()) != event["nominal_slots"]
            or counts["accepted"] != event["accepted_count"]
        ):
            raise LedgerError("ledger event disposition/count parity failure")
        relative_value = event["chunk_relative_path"]
        if (
            type(relative_value) is not str
            or not relative_value
        ):
            raise LedgerError("ledger chunk location/length binding is malformed")
        relative = Path(relative_value)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or type(event["chunk_byte_length"]) is not int
            or event["chunk_byte_length"] <= 0
        ):
            raise LedgerError("ledger chunk location/length binding is malformed")
        for key in ("chunk_file_sha256", "chunk_semantic_sha256"):
            value = event[key]
            if (
                type(value) is not str
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise LedgerError("ledger chunk digest binding is malformed")

    def _recover_single_published_tail(self) -> None:
        """Adopt one complete event published just before an index-update crash."""

        self._require_writer()
        index = strict_load_json(self.index_path)
        self._validate_index(index)
        event_count = self._event_file_count()
        count = index["event_count"]
        if event_count == count:
            return
        if event_count != count + 1:
            raise LedgerError("ledger/index divergence is not one recoverable complete tail")
        orphan = strict_load_json(self.events_root / self.event_name(count))
        self._validate_event(orphan, expected_index=count, expected_previous=index["last_digest"])
        expected_chunk = index["per_stream_next_chunk"].get(orphan["stream_id"], 0)
        if orphan["chunk_index"] != expected_chunk:
            raise LedgerError("published tail stream cursor mismatch")
        cursors = dict(index["per_stream_next_chunk"])
        cursors[orphan["stream_id"]] = expected_chunk + 1
        atomic_write_json(self.index_path, self._index(count + 1, orphan["event_digest"], cursors))

    def _event_file_count(self) -> int:
        count = 0
        maximum = -1
        with os.scandir(self.events_root) as entries:
            for entry in entries:
                if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
                    raise LedgerError("ledger contains a non-regular entry")
                name = entry.name
                if (
                    len(name) != 17
                    or not name.endswith(".json")
                    or not name[:12].isdigit()
                ):
                    raise LedgerError("ledger event filename is malformed")
                maximum = max(maximum, int(name[:12]))
                count += 1
        if maximum != count - 1:
            raise LedgerError("ledger event is missing, duplicate, or reordered")
        return count

    def _load_tail_verified(self) -> dict[str, Any]:
        document = strict_load_json(self.index_path)
        self._validate_index(document)
        count = document["event_count"]
        if count == 0:
            if document["last_digest"] != GENESIS_DIGEST or document["per_stream_next_chunk"]:
                raise LedgerError("empty ledger index is inconsistent")
            return dict(document)
        tail_path = self.events_root / self.event_name(count - 1)
        if not tail_path.is_file() or tail_path.is_symlink():
            raise LedgerError("ledger tail event is absent or not regular")
        tail = strict_load_json(tail_path)
        expected_previous = (
            GENESIS_DIGEST
            if count == 1
            else strict_load_json(self.events_root / self.event_name(count - 2))["event_digest"]
        )
        self._validate_event(tail, expected_index=count - 1, expected_previous=expected_previous)
        if tail["event_digest"] != document["last_digest"]:
            raise LedgerError("ledger tail does not match derived index")
        if document["per_stream_next_chunk"].get(tail["stream_id"]) != tail["chunk_index"] + 1:
            raise LedgerError("ledger tail stream cursor mismatch")
        return dict(document)

    def append_chunk(
        self,
        *,
        stage: Stage | str,
        stream_id: str,
        chunk_index: int,
        nominal_slots: int,
        accepted_count: int,
        disposition_counts: Mapping[str, int],
        chunk_relative_path: str,
        chunk_byte_length: int,
        chunk_file_sha256: str,
        chunk_semantic_sha256: str,
    ) -> dict[str, Any]:
        self._require_writer()
        index = self._load_tail_verified()  # O(1): index plus at most two tail files.
        expected_chunk = index["per_stream_next_chunk"].get(stream_id, 0)
        if chunk_index != expected_chunk:
            raise LedgerError("append is not at the first missing stream chunk")
        body = {
            "document_kind": "s11_chunk_metadata_event",
            "schema_version": 2,
            "checkpoint_id": "S11",
            "event_index": index["event_count"],
            "stage": Stage(stage).value,
            "stream_id": stream_id,
            "chunk_index": chunk_index,
            "nominal_slots": nominal_slots,
            "accepted_count": accepted_count,
            "disposition_counts": dict(disposition_counts),
            "chunk_relative_path": chunk_relative_path,
            "chunk_byte_length": chunk_byte_length,
            "chunk_file_sha256": chunk_file_sha256,
            "chunk_semantic_sha256": chunk_semantic_sha256,
            "previous_event_digest": index["last_digest"],
            "lock_sha256": self.lock_sha256,
        }
        event = {**body, "event_digest": canonical_sha256(body)}
        exclusive_write_json(
            self.events_root / self.event_name(index["event_count"]), event
        )
        cursors = dict(index["per_stream_next_chunk"])
        cursors[stream_id] = chunk_index + 1
        atomic_write_json(
            self.index_path,
            self._index(index["event_count"] + 1, event["event_digest"], cursors),
        )
        return event

    def full_verify(self) -> dict[str, Any]:
        """Perform the verifier's explicit O(N) replay and compare the index."""

        previous = GENESIS_DIGEST
        cursors: dict[str, int] = {}
        event_count = self._event_file_count()
        for count in range(event_count):
            entry = self.events_root / self.event_name(count)
            info = entry.lstat()
            if not stat.S_ISREG(info.st_mode) or entry.is_symlink():
                raise LedgerError("ledger contains a non-regular entry")
            if entry.name != self.event_name(count):
                raise LedgerError("ledger event is missing, duplicate, or reordered")
            event = strict_load_json(entry)
            self._validate_event(event, expected_index=count, expected_previous=previous)
            expected_chunk = cursors.get(event["stream_id"], 0)
            if event["chunk_index"] != expected_chunk:
                raise LedgerError("stream chunk is missing, duplicated, or reordered")
            cursors[event["stream_id"]] = expected_chunk + 1
            previous = event["event_digest"]
        expected_index = self._index(event_count, previous, cursors)
        actual_index = strict_load_json(self.index_path)
        if actual_index != expected_index:
            raise LedgerError("derived ledger index differs from full replay")
        return {
            "event_count": event_count,
            "last_digest": previous,
            "per_stream_next_chunk": cursors,
        }
