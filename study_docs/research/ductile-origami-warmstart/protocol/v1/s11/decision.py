# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Ordered, mutually-exclusive S11 terminal matrix projection."""

from __future__ import annotations

from typing import Any, Mapping

from .canonical import canonical_sha256


class DecisionError(ValueError):
    """Decision inputs are incomplete or violate terminal precedence."""


REQUIRED_INPUTS = {
    "integrity_failure",
    "label_leakage",
    "qualification_discordant_or_partial",
    "blocked_mapping_exact_allowlisted",
    "bounded_family_complete",
    "material_stochastic_shortage",
    "global_uexec_count",
    "stable_guided_gene_count",
    "positive_global_lambda",
    "all_positive_gates_pass",
}


def decide(inputs: Mapping[str, Any]) -> dict[str, Any]:
    if set(inputs) != REQUIRED_INPUTS:
        raise DecisionError("decision input schema/unknown-property failure")
    boolean_fields = REQUIRED_INPUTS - {"global_uexec_count", "stable_guided_gene_count"}
    if any(type(inputs[field]) is not bool for field in boolean_fields):
        raise DecisionError("decision flags must be booleans")
    if any(
        type(inputs[field]) is not int or inputs[field] < 0
        for field in ("global_uexec_count", "stable_guided_gene_count")
    ):
        raise DecisionError("decision counts must be non-negative integers")

    if inputs["label_leakage"]:
        branch = {
            "terminal_code": "EVIDENCE_INVALID",
            "operational_status": "CHANGES_REQUIRED",
            "scientific_outcome": "not_evaluated",
            "criterion": None,
            "edge": None,
            "required_action": "new_lock_fresh_seeds_full_draw0_rerun",
        }
    elif inputs["integrity_failure"] or inputs["qualification_discordant_or_partial"]:
        branch = {
            "terminal_code": "CHANGES_REQUIRED",
            "operational_status": "CHANGES_REQUIRED",
            "scientific_outcome": "not_evaluated",
            "criterion": None,
            "edge": None,
            "required_action": "reviewer_governed_uncapped_traceable_repair",
        }
    elif inputs["blocked_mapping_exact_allowlisted"]:
        raise DecisionError("FT-BLOCKED-MAPPING is unreachable while the frozen allowlist is empty")
    else:
        positive = (
            inputs["bounded_family_complete"]
            and not inputs["material_stochastic_shortage"]
            and inputs["global_uexec_count"] >= 256
            and inputs["stable_guided_gene_count"] >= 1
            and inputs["positive_global_lambda"]
            and inputs["all_positive_gates_pass"]
        )
        if positive:
            branch = {
                "terminal_code": "S1_GUIDANCE_LOCKED",
                "operational_status": "complete",
                "scientific_outcome": "positive",
                "criterion": "S1_GUIDANCE_LOCKED",
                "edge": "S12",
                "required_action": "closeout_claim_index",
            }
        elif (
            inputs["material_stochastic_shortage"]
            or inputs["global_uexec_count"] < 256
            or not inputs["bounded_family_complete"]
        ):
            branch = {
                "terminal_code": "FT-INCONCLUSIVE",
                "operational_status": "complete",
                "scientific_outcome": "inconclusive",
                "criterion": "FT-INCONCLUSIVE",
                "edge": None,
                "required_action": "closeout_claim_index",
            }
        else:
            branch = {
                "terminal_code": "COMPLETE_DETERMINISTIC_NO_GUIDANCE",
                "operational_status": "complete",
                "scientific_outcome": "negative",
                "criterion": "frozen_procedure_did_not_establish_guidance",
                "edge": None,
                "required_action": "closeout_claim_index",
            }
    packet = {
        "document_kind": "s11_machine_decision",
        "schema_version": 1,
        "checkpoint_id": "S11",
        **branch,
        "inputs_sha256": canonical_sha256(dict(inputs)),
    }
    return {**packet, "decision_sha256": canonical_sha256(packet)}


def _artifact_digest(document: Mapping[str, Any], kind: str) -> str:
    if type(document) is not dict or document.get("document_kind") != kind:
        raise DecisionError(f"decision source is not {kind}")
    body = dict(document)
    recorded = body.pop("artifact_sha256", None)
    if type(recorded) is not str or canonical_sha256(body) != recorded:
        raise DecisionError(f"decision source {kind} self-hash failure")
    return recorded


def decide_from_artifacts(
    *,
    global_prefix: Mapping[str, Any],
    conditional_prefixes: Mapping[str, Any],
    qualifications: Mapping[str, Any],
    analysis: Mapping[str, Any],
    guidance: Mapping[str, Any],
    registry: Mapping[str, Any] | None = None,
    native_scores: Mapping[str, Any] | None = None,
    formal_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive every terminal input from verified stage artifacts.

    This is the only decision entry point used by the formal workflow.  There
    is intentionally no parameter for a terminal truth flag.
    """

    if type(registry) is not dict or type(native_scores) is not dict or type(formal_evidence) is not dict:
        raise DecisionError(
            "formal decision requires registry, native scores, and ledger-derived evidence"
        )
    sources = {
        "s11_registry": _artifact_digest(registry, "s11_registry"),
        "s11_global_prefix": _artifact_digest(global_prefix, "s11_global_prefix"),
        "s11_conditional_prefixes": _artifact_digest(
            conditional_prefixes, "s11_conditional_prefixes"
        ),
        "s11_qualifications": _artifact_digest(
            qualifications, "s11_qualifications"
        ),
        "s11_native_scores": _artifact_digest(native_scores, "s11_native_scores"),
        "s11_analysis": _artifact_digest(analysis, "s11_analysis"),
        "s11_guidance": _artifact_digest(guidance, "s11_guidance"),
    }
    lock_values = {
        document.get("lock_sha256")
        for document in (
            registry, global_prefix, conditional_prefixes, qualifications,
            native_scores, analysis, guidance,
        )
    }
    expected_dependencies = {
        "s11_global_prefix": {"registry": sources["s11_registry"]},
        "s11_conditional_prefixes": {
            "registry": sources["s11_registry"],
            "global_prefix": sources["s11_global_prefix"],
        },
        "s11_qualifications": {
            "global_prefix": sources["s11_global_prefix"],
            "conditional_prefixes": sources["s11_conditional_prefixes"],
        },
        "s11_native_scores": {"qualifications": sources["s11_qualifications"]},
        "s11_analysis": {
            "registry": sources["s11_registry"],
            "global_prefix": sources["s11_global_prefix"],
            "conditional_prefixes": sources["s11_conditional_prefixes"],
            "qualifications": sources["s11_qualifications"],
            "native_scores": sources["s11_native_scores"],
        },
        "s11_guidance": {"analysis": sources["s11_analysis"]},
    }
    documents = {
        document["document_kind"]: document
        for document in (
            global_prefix, conditional_prefixes, qualifications, native_scores,
            analysis, guidance,
        )
    }
    if len(lock_values) != 1 or any(
        documents[kind].get("dependencies") != dependencies
        for kind, dependencies in expected_dependencies.items()
    ):
        raise DecisionError("formal artifact dependency chain changed")
    evidence_expected_keys = {
        "document_kind", "schema_version", "checkpoint_id", "lock_sha256",
        "production_schedule", "source_artifact_sha256", "streams",
        "dependency_chain_verified", "synthetic", "evidence_sha256",
    }
    if set(formal_evidence) != evidence_expected_keys:
        raise DecisionError("ledger-derived formal evidence is absent or malformed")
    evidence_body = dict(formal_evidence)
    evidence_hash = evidence_body.pop("evidence_sha256")
    expected_source_names = {
        "registry", "global_prefix", "conditional_prefixes", "qualifications",
        "native_scores", "analysis", "guidance",
    }
    evidence_sources = formal_evidence["source_artifact_sha256"]
    if (
        formal_evidence["document_kind"] != "s11_formal_evidence_attestation"
        or formal_evidence["schema_version"] != 1
        or formal_evidence["checkpoint_id"] != "S11"
        or formal_evidence["lock_sha256"] not in lock_values
        or formal_evidence["dependency_chain_verified"] is not True
        or formal_evidence["synthetic"] is not False
        or canonical_sha256(evidence_body) != evidence_hash
        or type(evidence_sources) is not dict
        or set(evidence_sources) != expected_source_names
        or evidence_sources != {
            "registry": sources["s11_registry"],
            "global_prefix": sources["s11_global_prefix"],
            "conditional_prefixes": sources["s11_conditional_prefixes"],
            "qualifications": sources["s11_qualifications"],
            "native_scores": sources["s11_native_scores"],
            "analysis": sources["s11_analysis"],
            "guidance": sources["s11_guidance"],
        }
    ):
        raise DecisionError("ledger-derived formal evidence identity/parity failure")
    schedule = formal_evidence["production_schedule"]
    registry_streams = registry.get("conditional_streams")
    conditional_streams = conditional_prefixes.get("streams")
    if type(registry_streams) is not list or type(conditional_streams) is not list:
        raise DecisionError("formal stream registry/artifact schema is incomplete")
    expected_stream_ids = [
        "global",
        *(row.get("stream_id") for row in registry_streams),
    ]
    stream_attestations = formal_evidence["streams"]
    artifact_streams = [global_prefix.get("stream"), *conditional_streams]
    if (
        schedule != {
            "chunk_nominal_draws": 512,
            "global_target_accepted": 8192,
            "global_complete_chunks": 65536,
            "conditional_target_accepted": 256,
            "conditional_complete_chunks": 512,
            "conditional_stream_ids": expected_stream_ids[1:],
        }
        or type(stream_attestations) is not list
        or [row.get("stream_id") for row in stream_attestations] != expected_stream_ids
        or [row.get("stream_id") for row in artifact_streams] != expected_stream_ids
        or any(
            type(row) is not dict
            or set(row) != {
                "stream_id", "target_accepted", "hard_cap_chunks",
                "nominal_slots_per_chunk", "ledger_replay_sha256",
                "credited_rows_sha256", "chunk_hashes_sha256", "raw_files",
            }
            or type(row["raw_files"]) is not list
            or not row["raw_files"]
            or any(
                type(raw) is not dict or set(raw) != {"path", "sha256"}
                or type(raw["path"]) is not str or type(raw["sha256"]) is not str
                or len(raw["sha256"]) != 64
                for raw in row["raw_files"]
            )
            for row in stream_attestations
        )
        or any(
            row["nominal_slots_per_chunk"] != 512
            or row["target_accepted"] != (8192 if index == 0 else 256)
            or row["hard_cap_chunks"] != (65536 if index == 0 else 512)
            for index, row in enumerate(stream_attestations)
        )
        or any(
            row["ledger_replay_sha256"] != canonical_sha256(stream["ledger_replay"])
            or row["credited_rows_sha256"] != canonical_sha256(stream["credited_rows"])
            or row["chunk_hashes_sha256"] != stream["chunk_hashes_sha256"]
            for row, stream in zip(stream_attestations, artifact_streams)
        )
    ):
        raise DecisionError("formal production schedule/raw ledger attestation changed")
    records = qualifications.get("qualification_records")
    streams = conditional_prefixes.get("streams")
    shortages = analysis.get("material_shortages")
    population = analysis.get("population_summary")
    half = analysis.get("semantic_half_stability")
    audits = analysis.get("read_audit")
    if not (
        type(records) is list
        and type(streams) is list
        and type(shortages) is list
        and type(population) is dict
        and type(half) is dict
        and type(audits) is dict
    ):
        raise DecisionError("artifact-derived decision source schema is incomplete")
    states = [record.get("projection", {}).get("state") for record in records]
    inputs = {
        "integrity_failure": not (
            analysis.get("terminal_analysis_complete") is True
            and guidance.get("integrity_complete") is True
        ),
        "label_leakage": audits.get("label_source_firewall_pass") is not True,
        "qualification_discordant_or_partial": any(
            state in (None, "pending_second_attempt", "changes_required_not_evaluated")
            for state in states
        ),
        "blocked_mapping_exact_allowlisted": any(
            state == "blocked_mapping" for state in states
        ),
        "bounded_family_complete": (
            global_prefix.get("stream", {}).get("cap_complete") is True
            and conditional_prefixes.get("activation_complete") is True
            and all(stream.get("cap_complete") is True for stream in streams)
        ),
        "material_stochastic_shortage": bool(shortages)
        or global_prefix.get("stream", {}).get("prefix", {}).get("complete") is not True
        or any(stream.get("prefix", {}).get("complete") is not True for stream in streams)
        or half.get("stable") is not True,
        "global_uexec_count": population.get("global_uexec_count"),
        "stable_guided_gene_count": analysis.get("stable_guided_gene_count"),
        "positive_global_lambda": guidance.get("positive_global_lambda") is True,
        "all_positive_gates_pass": (
            analysis.get("all_model_gates_pass") is True
            and guidance.get("all_guidance_gates_pass") is True
            and half.get("stable") is True
        ),
    }
    projected = decide(inputs)
    body = dict(projected)
    body.pop("decision_sha256")
    body["derived_inputs"] = inputs
    body["source_artifact_sha256"] = sources
    body["formal_evidence_sha256"] = formal_evidence["evidence_sha256"]
    body["caller_supplied_terminal_flags"] = False
    body["option_c_shrinkage_gate"] = analysis.get("option_c_shrinkage_gate")
    return {**body, "decision_sha256": canonical_sha256(body)}


def branch_artifact_policy(decision: Mapping[str, Any]) -> dict[str, Any]:
    """Project report/gate/edge exclusivity without writing any artifact."""

    code = decision.get("terminal_code")
    if code == "S1_GUIDANCE_LOCKED":
        return {"scientific_report": "forbidden", "compact_gate_record": "required", "edge": "S12"}
    if code in ("FT-INCONCLUSIVE", "COMPLETE_DETERMINISTIC_NO_GUIDANCE"):
        return {"scientific_report": "required", "compact_gate_record": "forbidden", "edge": None}
    if code in ("CHANGES_REQUIRED", "EVIDENCE_INVALID"):
        return {"scientific_report": "forbidden", "compact_gate_record": "forbidden", "edge": None}
    if code == "FT-BLOCKED-MAPPING":
        return {"scientific_report": "forbidden", "compact_gate_record": "forbidden", "edge": None, "decision_packet": "required"}
    raise DecisionError("unknown terminal code for branch artifact policy")
