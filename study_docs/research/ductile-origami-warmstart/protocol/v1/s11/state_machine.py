# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Fail-closed S11 lifecycle and stage transitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .canonical import atomic_write_json, exclusive_write_json, strict_load_json


class LifecycleError(ValueError):
    """A stage transition or lifecycle projection is invalid."""


class Stage(str, Enum):
    PREFLIGHT = "preflight"
    GLOBAL_DISCOVERY = "global_discovery"
    CONDITIONAL_DISCOVERY = "conditional_discovery"
    QUALIFICATION = "qualification"
    NATIVE_SCORING = "native_scoring"
    ANALYSIS = "analysis"
    DECISION = "decision"
    REPRODUCTION = "reproduction"


STAGE_ORDER = (
    Stage.PREFLIGHT,
    Stage.GLOBAL_DISCOVERY,
    Stage.CONDITIONAL_DISCOVERY,
    Stage.QUALIFICATION,
    Stage.NATIVE_SCORING,
    Stage.ANALYSIS,
    Stage.DECISION,
    Stage.REPRODUCTION,
)


@dataclass(frozen=True)
class RunState:
    lock_sha256: str
    stage: Stage
    stage_complete: bool
    formal_event_count: int
    terminal: bool = False

    def to_document(self) -> dict[str, Any]:
        return {
            "document_kind": "s11_run_state",
            "schema_version": 1,
            "checkpoint_id": "S11",
            "lock_sha256": self.lock_sha256,
            "stage": self.stage.value,
            "stage_complete": self.stage_complete,
            "formal_event_count": self.formal_event_count,
            "terminal": self.terminal,
        }


def next_stage(current: Stage, *, terminal: bool = False) -> Stage | None:
    if terminal:
        return None
    index = STAGE_ORDER.index(Stage(current))
    return STAGE_ORDER[index + 1] if index + 1 < len(STAGE_ORDER) else None


def validate_transition(before: Mapping[str, Any], after: Mapping[str, Any]) -> None:
    required = {
        "document_kind",
        "schema_version",
        "checkpoint_id",
        "lock_sha256",
        "stage",
        "stage_complete",
        "formal_event_count",
        "terminal",
    }
    if set(before) != required or set(after) != required:
        raise LifecycleError("run-state schema or unknown-property failure")
    if any(
        before[key] != after[key]
        for key in ("document_kind", "schema_version", "checkpoint_id", "lock_sha256")
    ):
        raise LifecycleError("run-state binding changed")
    if type(after["formal_event_count"]) is not int or after["formal_event_count"] < 0:
        raise LifecycleError("formal event count is invalid")
    if after["formal_event_count"] < before["formal_event_count"]:
        raise LifecycleError("formal event count cannot decrease")
    before_stage, after_stage = Stage(before["stage"]), Stage(after["stage"])
    if dict(before) == dict(after):
        return
    if before["terminal"]:
        raise LifecycleError("terminal run state cannot transition")
    if after_stage == before_stage:
        if before["stage_complete"] and not after["stage_complete"]:
            raise LifecycleError("completed stage cannot reopen")
        return
    if not before["stage_complete"] or after_stage != next_stage(before_stage):
        raise LifecycleError("stage transition skipped or reordered a frozen stage")
    if after["stage_complete"]:
        raise LifecycleError("a newly entered stage cannot already be complete")


class LifecycleStore:
    """Crash-safe single run-state projection bound to one effective lock."""

    def __init__(self, path: Path | str, lock_sha256: str):
        self.path = Path(path)
        self.lock_sha256 = lock_sha256

    def initialize(self) -> dict[str, Any]:
        if self.path.exists():
            raise LifecycleError("run state already exists; use resume/status")
        document = RunState(
            lock_sha256=self.lock_sha256,
            stage=Stage.PREFLIGHT,
            stage_complete=False,
            formal_event_count=0,
        ).to_document()
        exclusive_write_json(self.path, document)
        return document

    def load(self) -> dict[str, Any]:
        document = strict_load_json(self.path)
        if type(document) is not dict:
            raise LifecycleError("run-state root is not an object")
        validate_transition(document, document)
        if document["lock_sha256"] != self.lock_sha256:
            raise LifecycleError("run state belongs to another effective lock")
        return document

    def update(
        self,
        *,
        stage_complete: bool | None = None,
        formal_event_count: int | None = None,
        advance: bool = False,
        terminal: bool | None = None,
    ) -> dict[str, Any]:
        before = self.load()
        after = dict(before)
        if stage_complete is not None:
            after["stage_complete"] = stage_complete
        if formal_event_count is not None:
            after["formal_event_count"] = formal_event_count
        if terminal is not None:
            after["terminal"] = terminal
        if advance:
            destination = next_stage(Stage(before["stage"]), terminal=before["terminal"])
            if destination is None:
                raise LifecycleError("terminal/final stage has no successor")
            after["stage"] = destination.value
            after["stage_complete"] = False
        validate_transition(before, after)
        atomic_write_json(self.path, after)
        return after
