# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Exact S10R4 lifecycle, formal stage order, and result-priority machine."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping

from .contract import S10R4Error


FORMAL_STAGES = (
    "verify_effective_lock_and_prelabel_absence",
    "codegen_census_pass_A_all_114",
    "codegen_census_pass_B_all_114",
    "seal_codegen_classification",
    "deterministic_operational_exact_K_selection",
    "mapping_pass_A",
    "mapping_pass_B",
    "native_sentinel_runtime_conformance",
    "GPU_environment",
    "nine_correctness_cells",
    "sixty_three_noise_cells",
    "machine_decision",
    "independent_reproduction",
    "fresh_verification",
    "terminal_closeout",
    "exact_path_commit_and_post_commit_audit",
)

PROJECTOR_STATE_FIELDS = {
    "census_a_count", "census_b_count", "resource_reforecast", "classification",
    "selection_status", "mapping_a_status", "mapping_b_status", "mapping_corpus_status",
    "native_conformance", "gpu_environment", "blocker_producer", "correctness_count",
    "correctness_status", "noise_count", "noise_status", "decision", "reproduction",
}


@dataclass(frozen=True)
class StageProjection:
    """Artifact-derived formal admission state; never a caller-selected stage."""

    stage_id: str
    command_id: str | None
    pass_id: str | None = None
    resumable_prefix_count: int = 0
    terminal_branch: str | None = None
    blocker_present: bool = False
    resume_command_id: str | None = None
    resume_pass_id: str | None = None


def _project_base_formal_stage(state: Mapping[str, Any]) -> StageProjection:
    """Validate and project the complete census-through-noise base state."""
    if set(state) != PROJECTOR_STATE_FIELDS:
        raise S10R4Error("formal stage projector input fields mismatch")
    a_count = state["census_a_count"]
    b_count = state["census_b_count"]
    correctness_count = state["correctness_count"]
    noise_count = state["noise_count"]
    if (
        not isinstance(a_count, int) or isinstance(a_count, bool) or not 0 <= a_count <= 114
        or not isinstance(b_count, int) or isinstance(b_count, bool) or not 0 <= b_count <= 114
        or not isinstance(correctness_count, int) or isinstance(correctness_count, bool) or not 0 <= correctness_count <= 9
        or not isinstance(noise_count, int) or isinstance(noise_count, bool) or not 0 <= noise_count <= 63
    ):
        raise S10R4Error("formal stage projector has an out-of-range prefix count")
    selection_status = state["selection_status"]
    mapping_a = state["mapping_a_status"]
    mapping_b = state["mapping_b_status"]
    mapping_corpus = state["mapping_corpus_status"]
    correctness_status = state["correctness_status"]
    noise_status = state["noise_status"]
    for name, value, allowed in (
        ("selection_status", selection_status, (None, "PASS", "NEGATIVE_MAPPING")),
        ("mapping_a_status", mapping_a, (None, "PASS", "NEGATIVE_MAPPING")),
        ("mapping_b_status", mapping_b, (None, "PASS", "NEGATIVE_MAPPING")),
        ("mapping_corpus_status", mapping_corpus, (None, "PASS", "NEGATIVE_MAPPING")),
        ("correctness_status", correctness_status, (None, "PASS", "NEGATIVE_CORRECTNESS")),
        ("noise_status", noise_status, (None, "PASS", "INCONCLUSIVE_NOISE")),
    ):
        if value not in allowed:
            raise S10R4Error(f"formal stage projector has unknown {name}")
    later_than_a = any(
        value
        for value in (
            b_count, state["classification"], selection_status, mapping_a, mapping_b, mapping_corpus,
            state["native_conformance"], state["gpu_environment"], correctness_count,
            correctness_status, noise_count, noise_status,
        )
    )
    if a_count < 114:
        if later_than_a or (state["resource_reforecast"] and a_count < 3):
            raise S10R4Error("census-A is not the exact resumable artifact prefix")
        return StageProjection("codegen_census_pass_A_all_114", "census", "A", a_count)
    if not state["resource_reforecast"]:
        raise S10R4Error("complete census-A lacks its mandatory three-child resource reforecast")
    later_than_b = any(
        value
        for value in (
            state["classification"], selection_status, mapping_a, mapping_b, mapping_corpus,
            state["native_conformance"], state["gpu_environment"], correctness_count,
            correctness_status, noise_count, noise_status,
        )
    )
    if b_count < 114:
        if later_than_b:
            raise S10R4Error("census-B is not the exact resumable artifact prefix")
        return StageProjection("codegen_census_pass_B_all_114", "census", "B", b_count)
    if not state["classification"] or selection_status is None:
        if state["classification"] or selection_status is not None or any(
            value for value in (mapping_a, mapping_b, mapping_corpus, state["native_conformance"], state["gpu_environment"], correctness_count, correctness_status, noise_count, noise_status)
        ):
            raise S10R4Error("classification/selection is partial or has later artifacts")
        return StageProjection("seal_codegen_classification_and_selection", "classify-select")
    if selection_status == "NEGATIVE_MAPPING":
        if any(value for value in (mapping_a, mapping_b, mapping_corpus, state["native_conformance"], state["gpu_environment"], correctness_count, correctness_status, noise_count, noise_status)):
            raise S10R4Error("negative selection has unreachable later measurement artifacts")
        return StageProjection(
            "machine_decision_negative_selection", "decision",
            terminal_branch="NEGATIVE_MAPPING", resume_command_id="classify-select",
        )
    if mapping_a is None:
        if any(value for value in (mapping_b, mapping_corpus, state["native_conformance"], state["gpu_environment"], correctness_count, correctness_status, noise_count, noise_status)):
            raise S10R4Error("mapping-A is skipped by later artifacts")
        return StageProjection(
            "mapping_pass_A", "mapping", "A", resume_command_id="classify-select"
        )
    if mapping_a == "NEGATIVE_MAPPING":
        if any(value for value in (mapping_b, state["native_conformance"], state["gpu_environment"], correctness_count, correctness_status, noise_count, noise_status)):
            raise S10R4Error("negative mapping-A has unreachable later measurement artifacts")
        if mapping_corpus is None:
            return StageProjection("mapping_pass_A_terminal_summary", "mapping", "A", 1, "NEGATIVE_MAPPING")
        if mapping_corpus != "NEGATIVE_MAPPING":
            raise S10R4Error("negative mapping-A lacks its exact corpus summary")
        return StageProjection(
            "machine_decision_negative_mapping", "decision",
            terminal_branch="NEGATIVE_MAPPING", resume_command_id="mapping", resume_pass_id="A",
        )
    if mapping_b is None:
        if any(value for value in (mapping_corpus, state["native_conformance"], state["gpu_environment"], correctness_count, correctness_status, noise_count, noise_status)):
            raise S10R4Error("mapping-B is skipped by later artifacts")
        return StageProjection(
            "mapping_pass_B", "mapping", "B", resume_command_id="mapping", resume_pass_id="A"
        )
    if mapping_b == "NEGATIVE_MAPPING":
        if any(value for value in (state["native_conformance"], state["gpu_environment"], correctness_count, correctness_status, noise_count, noise_status)):
            raise S10R4Error("negative mapping-B branch is incomplete or has later artifacts")
        if mapping_corpus is None:
            return StageProjection("mapping_pass_B_terminal_summary", "mapping", "B", 1, "NEGATIVE_MAPPING")
        if mapping_corpus != "NEGATIVE_MAPPING":
            raise S10R4Error("negative mapping-B corpus summary mismatch")
        return StageProjection(
            "machine_decision_negative_mapping", "decision",
            terminal_branch="NEGATIVE_MAPPING", resume_command_id="mapping", resume_pass_id="B",
        )
    if mapping_corpus is None:
        return StageProjection("mapping_pass_B_terminal_summary", "mapping", "B", 1)
    if mapping_corpus != "PASS":
        raise S10R4Error("mapping A/B PASS lacks the exact corpus summary")
    if not state["native_conformance"]:
        if any(value for value in (state["gpu_environment"], correctness_count, correctness_status, noise_count, noise_status)):
            raise S10R4Error("native conformance is skipped by later artifacts")
        return StageProjection(
            "native_sentinel_runtime_conformance", "native-conformance",
            resume_command_id="mapping", resume_pass_id="B",
        )
    if not state["gpu_environment"]:
        if any(value for value in (correctness_count, correctness_status, noise_count, noise_status)):
            raise S10R4Error("GPU environment is skipped by later artifacts")
        return StageProjection(
            "GPU_environment", "gpu-environment", resume_command_id="native-conformance"
        )
    if correctness_status is None:
        if noise_count or noise_status:
            raise S10R4Error("correctness is skipped by later noise artifacts")
        return StageProjection(
            "nine_correctness_cells", "correctness", resumable_prefix_count=correctness_count,
            resume_command_id="gpu-environment",
        )
    if correctness_status == "NEGATIVE_CORRECTNESS":
        if noise_count or noise_status:
            raise S10R4Error("negative correctness has unreachable noise artifacts")
        return StageProjection(
            "machine_decision_negative_correctness", "decision",
            terminal_branch="NEGATIVE_CORRECTNESS", resume_command_id="correctness",
        )
    if correctness_count != 9:
        raise S10R4Error("correctness PASS does not bind exactly nine cells")
    if noise_status is None:
        return StageProjection(
            "sixty_three_noise_cells", "noise", resumable_prefix_count=noise_count,
            resume_command_id="correctness",
        )
    if noise_count != 63:
        raise S10R4Error("terminal noise summary does not bind exactly 63 observations")
    branch = "INCONCLUSIVE_NOISE" if noise_status == "INCONCLUSIVE_NOISE" else "POSITIVE"
    return StageProjection(
        "machine_decision", "decision", terminal_branch=branch, resume_command_id="noise"
    )


def project_formal_stage(state: Mapping[str, Any]) -> StageProjection:
    """Project the base first, then apply only a validated terminal overlay."""
    if set(state) != PROJECTOR_STATE_FIELDS:
        raise S10R4Error("formal stage projector input fields mismatch")
    base_state = dict(state)
    base_state.update({"blocker_producer": None, "decision": False, "reproduction": False})
    base = _project_base_formal_stage(base_state)
    blocker_producer = state["blocker_producer"]
    decision_present = state["decision"]
    reproduction_present = state["reproduction"]
    if blocker_producer is not None:
        if decision_present or reproduction_present:
            raise S10R4Error("operational blocker coexists with a decision/reproduction branch")
        if blocker_producer != base.command_id:
            raise S10R4Error("operational blocker cannot establish its own incomplete base stage")
        return StageProjection(
            "operational_blocker",
            blocker_producer,
            pass_id=base.pass_id,
            resumable_prefix_count=base.resumable_prefix_count,
            terminal_branch="BLOCKED",
            blocker_present=True,
        )
    if decision_present or reproduction_present:
        if base.command_id != "decision" or base.terminal_branch not in (
            "NEGATIVE_MAPPING", "NEGATIVE_CORRECTNESS", "INCONCLUSIVE_NOISE", "POSITIVE",
        ):
            raise S10R4Error("decision/reproduction overlay lacks a complete scientific terminal base")
        if reproduction_present and not decision_present:
            raise S10R4Error("reproduction exists without the canonical decision")
        if reproduction_present:
            return StageProjection(
                "terminal_after_reproduction", None, terminal_branch=base.terminal_branch,
                resume_command_id="reproduction",
            )
        return StageProjection(
            "independent_reproduction", "reproduction", terminal_branch=base.terminal_branch,
            resume_command_id="decision",
        )
    return base


@dataclass(frozen=True)
class Lifecycle:
    design_status: str = "approved"
    execution_status: str = "not_started"
    checkpoint_state: str = "DESIGN_APPROVED"
    scientific_outcome: str = "not_evaluated"
    lock_state: str = "absent"
    edge: str | None = None
    formal_evidence_allowed: bool = False
    next_stage_index: int = 0
    terminal: bool = False

    def bind_effective_lock(self) -> "Lifecycle":
        if self.lock_state != "absent" or self.checkpoint_state != "DESIGN_APPROVED":
            raise S10R4Error("effective lock binding transition is duplicate or out of order")
        return replace(
            self,
            execution_status="ready",
            checkpoint_state="LOCKED_READY",
            lock_state="effective",
            formal_evidence_allowed=True,
        )

    def enter_stage(self, stage: str) -> "Lifecycle":
        if self.terminal or not self.formal_evidence_allowed or self.lock_state != "effective":
            raise S10R4Error("formal stage cannot run in current lifecycle")
        if self.next_stage_index >= len(FORMAL_STAGES) or FORMAL_STAGES[self.next_stage_index] != stage:
            raise S10R4Error(f"formal stage skipped, duplicated, or reordered: {stage}")
        return replace(
            self,
            execution_status="running",
            checkpoint_state="RUNNING",
            next_stage_index=self.next_stage_index + 1,
        )

    def technical_pass(self, outcome: Mapping[str, Any]) -> "Lifecycle":
        if self.scientific_outcome != "not_evaluated" or self.lock_state != "effective":
            raise S10R4Error("technical PASS transition is not admissible")
        scientific = outcome.get("scientific_outcome")
        if scientific not in ("positive", "negative", "inconclusive"):
            raise S10R4Error("technical PASS requires a scientific terminal outcome")
        internal_edge = (
            "S10R4:S1_ENTRY_GO_EXACT_FRAME"
            if scientific == "positive" and outcome.get("criterion") == "S1_ENTRY_GO_EXACT_FRAME"
            else None
        )
        return replace(
            self,
            execution_status="completed",
            checkpoint_state="VERIFIED_PENDING_CLOSEOUT",
            scientific_outcome=scientific,
            edge=internal_edge,
            terminal=True,
        )

    def post_commit_audit(self) -> "Lifecycle":
        if self.checkpoint_state != "VERIFIED_PENDING_CLOSEOUT":
            raise S10R4Error("post-commit audit requires VERIFIED_PENDING_CLOSEOUT")
        external_edge = (
            "S10R4:S1_ENTRY_GO_EXACT_FRAME->S11" if self.scientific_outcome == "positive" else None
        )
        return replace(self, checkpoint_state="CHECKPOINT_COMPLETE", edge=external_edge)

    def changes_required(self) -> "Lifecycle":
        return replace(
            self,
            execution_status="blocked",
            checkpoint_state="BLOCKED",
            scientific_outcome="not_evaluated",
            edge=None,
            terminal=True,
        )


def decide_outcome(facts: Mapping[str, Any]) -> dict[str, Any]:
    if facts.get("changes_required"):
        return {"scientific_outcome": "not_evaluated", "criterion": "CHANGES_REQUIRED", "failure_id": None, "edge": None}
    if facts.get("operational_blocked"):
        return {"scientific_outcome": "not_evaluated", "criterion": "BLOCKED", "failure_id": None, "edge": None}
    if facts.get("negative_mapping"):
        return {"scientific_outcome": "negative", "criterion": "S1_ENTRY_BLOCKED", "failure_id": "FT-BLOCKED-MAPPING", "edge": None}
    if facts.get("negative_correctness"):
        return {"scientific_outcome": "negative", "criterion": "S1_ENTRY_BLOCKED", "failure_id": "FT-BLOCKED-CORRECTNESS", "edge": None}
    if facts.get("inconclusive_noise"):
        return {"scientific_outcome": "inconclusive", "criterion": None, "failure_id": "FT-INCONCLUSIVE", "edge": None}
    positive_fields = (
        "exact_frame_integrity_pass",
        "all_228_codegen_children_stably_classified",
        "stable_survivor_count_at_least_10",
        "full_mandatory_cover",
        "k_at_most_20",
        "mapping_a_b_pass",
        "native_conformance_pass",
        "all_9_correctness_cells_pass",
        "all_63_noise_cells_complete_and_pass",
    )
    if all(facts.get(field) is True for field in positive_fields):
        return {
            "scientific_outcome": "positive",
            "criterion": "S1_ENTRY_GO_EXACT_FRAME",
            "failure_id": None,
            "edge": "S10R4:S1_ENTRY_GO_EXACT_FRAME",
        }
    raise S10R4Error("CHANGES_REQUIRED: outcome is not uniquely determined")


def validate_document_policy(outcome: Mapping[str, Any], present_kinds: set[str]) -> None:
    always_forbidden_preterminal = {"positive_gate_record", "terminal_report", "decision", "operational_blocker"}
    scientific = outcome.get("scientific_outcome")
    criterion = outcome.get("criterion")
    if criterion == "CHANGES_REQUIRED" and present_kinds & always_forbidden_preterminal:
        raise S10R4Error("CHANGES_REQUIRED document-presence policy violation")
    if criterion == "BLOCKED":
        if present_kinds != {"operational_blocker"}:
            raise S10R4Error("operational BLOCKED document-presence policy violation")
    if scientific == "positive" and "operational_blocker" in present_kinds:
        raise S10R4Error("positive outcome cannot contain an operational blocker")
    if scientific in ("negative", "inconclusive") and "positive_gate_record" in present_kinds:
        raise S10R4Error("non-positive outcome cannot contain the positive gate record")
