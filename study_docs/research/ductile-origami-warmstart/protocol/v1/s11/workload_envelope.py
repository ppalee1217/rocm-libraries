# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Deterministic, planning-only S11 workload-envelope materialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import canonical_json_bytes, canonical_sha256
from .contract import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_PREIMPLEMENTATION_LOCK_PATH,
    DEFAULT_REVISION_PATH,
    REPOSITORY_ROOT,
    load_contract,
)
from .registry import extract_registry
from .sampling import resource_forecast


# These constants are synthetic planning calibrations, not measurements or workload authority.
SYNTHETIC_BYTES_PER_CHUNK = 40_000
SYNTHETIC_ACCEPTED_PER_RUNTIME_CALIBRATION = 1_000
SYNTHETIC_NOMINAL_DRAWS_PER_RUNTIME_CALIBRATION = 10_000


def _rooted(default_path: Path, repository_root: Path) -> Path:
    return repository_root / default_path.relative_to(REPOSITORY_ROOT)


def build_workload_envelope(
    *, repository_root: Path | str = REPOSITORY_ROOT
) -> dict[str, Any]:
    """Build the non-gating S11 workload envelope from tracked production inputs."""

    root = Path(repository_root).resolve()
    contract = load_contract(
        _rooted(DEFAULT_CONTRACT_PATH, root),
        revision_path=_rooted(DEFAULT_REVISION_PATH, root),
        preimplementation_lock_path=_rooted(DEFAULT_PREIMPLEMENTATION_LOCK_PATH, root),
    )
    registry = extract_registry(root / contract["input"]["path"])

    activated_value_count = len(registry["conditional_streams"])
    eligible_gene_count = len(registry["eligible_genes"])

    schedule = contract["schedule"]
    global_schedule = schedule["global"]
    conditional_schedule = schedule["conditional"]
    chunk_nominal_draws = schedule["chunk_nominal_draws"]
    global_complete_chunks = global_schedule["complete_chunks"]
    global_complete_nominal_draws = global_schedule["complete_nominal_draws"]
    global_canonical_prefix = global_schedule["canonical_prefix_accepted"]
    conditional_chunks_per_value = conditional_schedule[
        "complete_chunks_per_activated_value"
    ]
    conditional_draws_per_value = conditional_schedule[
        "complete_nominal_draws_per_activated_value"
    ]
    conditional_canonical_prefix = conditional_schedule["canonical_prefix_accepted"]
    boundary_overshoot_credit = schedule["boundary_overshoot_credit"]
    contract_problem_sizes = contract["native_scoring"]["problem_sizes"]
    locked_problem_sizes = registry["problem_sizes"]
    locked_size_count = len(contract_problem_sizes)
    attempts_per_semantic_identity = contract["qualification"][
        "complete_attempts_total"
    ]

    if global_complete_chunks * chunk_nominal_draws != global_complete_nominal_draws:
        raise ValueError("global schedule chunk/draw arithmetic is inconsistent")
    if conditional_chunks_per_value * chunk_nominal_draws != conditional_draws_per_value:
        raise ValueError("conditional schedule chunk/draw arithmetic is inconsistent")
    if boundary_overshoot_credit != 0:
        raise ValueError("credited-prefix envelope requires zero boundary overshoot credit")
    if locked_problem_sizes != contract_problem_sizes:
        raise ValueError("extractor and contract locked problem sizes disagree")

    conditional_nominal_draws = activated_value_count * conditional_draws_per_value
    conditional_chunks = activated_value_count * conditional_chunks_per_value
    producer_chunk_count = global_complete_chunks + conditional_chunks
    total_nominal_draws = global_complete_nominal_draws + conditional_nominal_draws
    credited_upper_bound = (
        global_canonical_prefix
        + activated_value_count * conditional_canonical_prefix
    )
    qualification_attempts_upper_bound = (
        attempts_per_semantic_identity * credited_upper_bound
    )
    formocast_per_size_upper_bound = credited_upper_bound
    formocast_upper_bound_by_locked_size = {
        canonical_json_bytes(problem_size).decode("utf-8"): formocast_per_size_upper_bound
        for problem_size in locked_problem_sizes
    }
    if len(formocast_upper_bound_by_locked_size) != locked_size_count:
        raise ValueError("locked problem-size keys are not unique")
    formocast_total_upper_bound = sum(formocast_upper_bound_by_locked_size.values())

    totals = {
        "global_nominal_draws": global_complete_nominal_draws,
        "conditional_nominal_draws": conditional_nominal_draws,
        "conditional_chunks": conditional_chunks,
        "producer_chunk_count": producer_chunk_count,
        "total_nominal_draws": total_nominal_draws,
        "credited_accepted_occurrence_upper_bound": credited_upper_bound,
        "attempts_per_semantic_identity": attempts_per_semantic_identity,
        "qualification_attempts_upper_bound": qualification_attempts_upper_bound,
        "unique_identity_qualification_attempt_upper_bound": (
            qualification_attempts_upper_bound
        ),
        "locked_size_count": locked_size_count,
        "formocast_score_call_upper_bound_per_locked_size": (
            formocast_per_size_upper_bound
        ),
        "formocast_score_call_upper_bound_by_locked_size": (
            formocast_upper_bound_by_locked_size
        ),
        "formocast_score_call_upper_bound_total": formocast_total_upper_bound,
    }

    runtime_targets = {
        "validator_accepted_occurrences": credited_upper_bound,
        "qualification_attempts": qualification_attempts_upper_bound,
        "formocast_score_calls": formocast_total_upper_bound,
    }
    runtime_forecast = resource_forecast(
        accepted=SYNTHETIC_ACCEPTED_PER_RUNTIME_CALIBRATION,
        nominal_draws=SYNTHETIC_NOMINAL_DRAWS_PER_RUNTIME_CALIBRATION,
        targets=list(runtime_targets.values()),
    )
    planning_marker = {
        "authority": "record_and_notify_only",
        "layer": "C",
        "may_stop_or_downgrade": False,
        "basis": "synthetic_planning_calibration",
    }
    planning_estimates = {
        "storage": {
            **planning_marker,
            "synthetic_bytes_per_chunk": SYNTHETIC_BYTES_PER_CHUNK,
            "producer_chunk_count": producer_chunk_count,
            "worst_case_bytes": SYNTHETIC_BYTES_PER_CHUNK * producer_chunk_count,
        },
        "runtime": {
            **planning_marker,
            "synthetic_calibration": {
                "accepted": SYNTHETIC_ACCEPTED_PER_RUNTIME_CALIBRATION,
                "nominal_draws": SYNTHETIC_NOMINAL_DRAWS_PER_RUNTIME_CALIBRATION,
            },
            "synthetic_targets": runtime_targets,
            "resource_forecast": runtime_forecast,
        },
    }

    outcome_ordering = contract["outcomes"]["ordering"]
    blocked_mapping_allowlist = contract["qualification"]["blocked_mapping"][
        "allowlist"
    ]
    if blocked_mapping_allowlist != []:
        raise ValueError("workload envelope requires the frozen empty-v1 mapping allowlist")
    global_uexec_minimum = contract["outcomes"]["positive"]["requirements"][
        "global_Uexec_min"
    ]
    global_threshold_reachable = global_canonical_prefix >= global_uexec_minimum
    if not global_threshold_reachable:
        raise ValueError("global accepted prefix cannot reach the decision minimum")

    branches = {
        "EVIDENCE_INVALID": {
            "terminal_code": "EVIDENCE_INVALID",
            "reachable": True,
            "note": "reachable first in decision ordering when label leakage is present",
        },
        "CHANGES_REQUIRED": {
            "terminal_code": "CHANGES_REQUIRED",
            "reachable": True,
            "note": "reachable on integrity failure or discordant/partial qualification",
        },
        "FT-BLOCKED-MAPPING": {
            "terminal_code": "FT-BLOCKED-MAPPING",
            "reachable": False,
            "note": "structurally unreachable under the frozen empty-v1 mapping allowlist",
        },
        "FT-INCONCLUSIVE": {
            "terminal_code": "FT-INCONCLUSIVE",
            "reachable": True,
            "note": "reachable through any sealed shortage-family condition",
            "sub_reasons": [
                f"global_uexec_count<{global_uexec_minimum}",
                "material_stochastic_shortage",
                "not bounded_family_complete",
            ],
        },
        "S1_GUIDANCE_LOCKED": {
            "terminal_code": "S1_GUIDANCE_LOCKED",
            "reachable": True,
            "note": (
                "positive branch is representable because the global accepted-prefix "
                "upper bound reaches the sealed Uexec minimum"
            ),
        },
        "COMPLETE_DETERMINISTIC_NO_GUIDANCE": {
            "terminal_code": "COMPLETE_DETERMINISTIC_NO_GUIDANCE",
            "reachable": True,
            "note": "reachable when the complete non-shortage family misses a positive gate",
        },
    }
    if set(branches) != set(outcome_ordering):
        raise ValueError("terminal reachability summary drifted from contract ordering")
    terminal_branch_reachability = [branches[code] for code in outcome_ordering]

    body = {
        "document_kind": "s11_workload_envelope",
        "schema_version": 1,
        "checkpoint_id": "S11",
        "status": "planning_only",
        "authority": "record_and_notify_only",
        "label": "synthetic_calibration_planning_artifact",
        "family": {
            "activated_value_count": activated_value_count,
            "eligible_gene_count": eligible_gene_count,
            "registry_sha256": registry["registry_sha256"],
            "actual_yaml_path": registry["actual_yaml_path"],
            "actual_yaml_sha256": registry["actual_yaml_sha256"],
        },
        "schedule_source": {
            "chunk_nominal_draws": chunk_nominal_draws,
            "global_complete_chunks": global_complete_chunks,
            "global_complete_nominal_draws": global_complete_nominal_draws,
            "global_canonical_prefix_accepted": global_canonical_prefix,
            "conditional_complete_chunks_per_activated_value": (
                conditional_chunks_per_value
            ),
            "conditional_complete_nominal_draws_per_activated_value": (
                conditional_draws_per_value
            ),
            "conditional_canonical_prefix_accepted": conditional_canonical_prefix,
            "boundary_overshoot_credit": boundary_overshoot_credit,
            "locked_size_count": locked_size_count,
            "locked_problem_sizes": locked_problem_sizes,
        },
        "totals": totals,
        "planning_estimates": planning_estimates,
        "terminal_branch_reachability": terminal_branch_reachability,
    }
    manifest = {**body, "envelope_sha256": canonical_sha256(body)}
    canonical_json_bytes(manifest)
    return manifest
