# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Append-only, single-writer, crash-safe S10R3 event ledger."""

from __future__ import annotations

import fcntl
import os
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .contract import canonical_json_bytes, canonical_sha256, strict_load_json
from .state_machine import Stage


class LedgerError(ValueError):
    """The ledger is malformed, locked, interrupted ambiguously, or drifted."""


GENESIS_DIGEST = "0" * 64


class RunLedger:
    """One immutable zero-padded JSON event per committed atomic unit."""

    def __init__(self, root: Path | str, effective_lock_sha256: str):
        self.root = Path(root)
        self.events_root = self.root / "events"
        self.index_path = self.root / "ledger-index.json"
        self.writer_lock_path = self.root / "writer.lock"
        if (
            type(effective_lock_sha256) is not str
            or len(effective_lock_sha256) != 64
            or any(character not in "0123456789abcdef" for character in effective_lock_sha256)
        ):
            raise LedgerError("effective-lock SHA-256 is malformed")
        self.effective_lock_sha256 = effective_lock_sha256
        self.events_root.mkdir(parents=True, exist_ok=True)
        self._guard: _WriterGuard | None = None

    def __enter__(self) -> "RunLedger":
        self._guard = _WriterGuard(self.writer_lock_path)
        self._guard.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        assert self._guard is not None
        self._guard.__exit__(exc_type, exc, traceback)
        self._guard = None

    def _require_writer(self) -> None:
        if self._guard is None:
            raise LedgerError("append requires the exclusive writer guard")

    @staticmethod
    def event_name(index: int) -> str:
        if type(index) is not int or index < 0:
            raise LedgerError("event index must be a non-negative exact integer")
        return f"{index:012d}.json"

    def _scan_events(self) -> list[dict[str, Any]]:
        entries = sorted(self.events_root.iterdir(), key=lambda path: path.name)
        committed = []
        for entry in entries:
            info = entry.lstat()
            if not stat.S_ISREG(info.st_mode) or entry.is_symlink():
                raise LedgerError("ledger contains a non-regular entry")
            if entry.name.endswith(".tmp"):
                final_name = entry.name[: -len(".tmp")]
                if (self.events_root / final_name).exists():
                    raise LedgerError("temporary event aliases a committed final event")
                continue
            if entry.name != self.event_name(len(committed)):
                raise LedgerError("ledger event is missing, duplicate, or reordered")
            document = strict_load_json(entry)
            committed.append(document)
        return committed

    def load_and_verify(self) -> dict[str, Any]:
        events = self._scan_events()
        previous = GENESIS_DIGEST
        next_chunks: dict[str, int] = {}
        for index, event in enumerate(events):
            expected_keys = {
                "schema_version",
                "checkpoint_id",
                "event_index",
                "stage",
                "stream_id",
                "atom_id",
                "chunk_index",
                "payload_digest",
                "previous_event_digest",
                "effective_lock_sha256",
                "timestamp_utc",
                "event_digest",
            }
            if set(event) != expected_keys:
                raise LedgerError("ledger event schema/unknown-property failure")
            if (
                event["schema_version"] != 1
                or type(event["event_index"]) is not int
                or event["event_index"] != index
                or event["checkpoint_id"] != "S10R3"
                or event["previous_event_digest"] != previous
                or event["effective_lock_sha256"] != self.effective_lock_sha256
            ):
                raise LedgerError("ledger identity/digest-chain invariant failed")
            Stage(event["stage"])
            digest_body = dict(event)
            recorded = digest_body.pop("event_digest")
            if canonical_sha256(digest_body) != recorded:
                raise LedgerError("ledger event digest mismatch")
            stream_id = event["stream_id"]
            chunk_index = event["chunk_index"]
            if type(stream_id) is not str or type(chunk_index) is not int:
                raise LedgerError("ledger stream/chunk type failure")
            expected_chunk = next_chunks.get(stream_id, 0)
            if chunk_index != expected_chunk:
                raise LedgerError("stream chunk is duplicated, missing, or reordered")
            next_chunks[stream_id] = expected_chunk + 1
            previous = recorded
        expected_index = {
            "document_kind": "ledger_index",
            "schema_version": 1,
            "checkpoint_id": "S10R3",
            "effective_lock_sha256": self.effective_lock_sha256,
            "event_count": len(events),
            "last_digest": previous,
            "per_stream_next_chunk": next_chunks,
        }
        if self.index_path.exists():
            try:
                current_index = strict_load_json(self.index_path)
            except Exception:
                current_index = None
            if current_index != expected_index:
                self._write_index(expected_index)
        else:
            self._write_index(expected_index)
        return {"events": events, "index": expected_index}

    def _write_index(self, document: Mapping[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".ledger-index.", suffix=".tmp", dir=self.root
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(canonical_json_bytes(dict(document)) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.index_path)
            directory_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if temporary.exists():
                temporary.unlink()

    def append(
        self,
        *,
        stage: Stage | str,
        stream_id: str,
        atom_id: str | None,
        chunk_index: int,
        payload: Mapping[str, Any],
        timestamp_utc: str | None = None,
    ) -> dict[str, Any]:
        self._require_writer()
        state = self.load_and_verify()
        index = state["index"]["event_count"]
        expected_chunk = state["index"]["per_stream_next_chunk"].get(stream_id, 0)
        if chunk_index != expected_chunk:
            raise LedgerError("append is not at the first missing chunk boundary")
        body = {
            "schema_version": 1,
            "checkpoint_id": "S10R3",
            "event_index": index,
            "stage": Stage(stage).value,
            "stream_id": stream_id,
            "atom_id": atom_id,
            "chunk_index": chunk_index,
            "payload_digest": canonical_sha256(dict(payload)),
            "previous_event_digest": state["index"]["last_digest"],
            "effective_lock_sha256": self.effective_lock_sha256,
            "timestamp_utc": timestamp_utc
            or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        event = {**body, "event_digest": canonical_sha256(body)}
        final_path = self.events_root / self.event_name(index)
        temporary_path = self.events_root / f"{self.event_name(index)}.tmp"
        try:
            descriptor = os.open(
                temporary_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o644,
            )
        except FileExistsError as error:
            raise LedgerError("uncommitted event temporary already exists") from error
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json_bytes(event) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        if final_path.exists():
            raise LedgerError("final event path already exists")
        os.replace(temporary_path, final_path)
        directory_fd = os.open(self.events_root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        new_index = {
            **state["index"],
            "event_count": index + 1,
            "last_digest": event["event_digest"],
            "per_stream_next_chunk": {
                **state["index"]["per_stream_next_chunk"],
                stream_id: chunk_index + 1,
            },
        }
        self._write_index(new_index)
        return event


class _WriterGuard:
    def __init__(self, path: Path):
        self.path = path
        self.stream: Any = None

    def __enter__(self) -> "_WriterGuard":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open("a+b")
        try:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self.stream.close()
            self.stream = None
            raise LedgerError("another ledger writer holds the lock") from error
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if self.stream is not None:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
            self.stream.close()
            self.stream = None
