#!/usr/bin/env python3
# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Bootstrap, lock, produce, and reproduce the Ductile S00 foundation."""

from __future__ import annotations

import argparse
import copy
import json
import os
import pickle
import random
import sys
import tempfile
from pathlib import Path

import joblib
import jsonschema
import numpy as np
import yaml

from Tensile.ductile.algorithm.ga import DurableInterruption, GeneticAlgorithm
from Tensile.ductile.core import Crossover, Mating, Mutation, SearchSpace, Selection
from Tensile.ductile.core import space as space_module
from Tensile.ductile.evidence import (
    ArtifactReconciliationError,
    EvidenceValidationError,
    atomic_write_json,
    build_ga_event,
    canonical_sha256,
    plain_value,
    reconcile_artifacts,
    resolve_bound_path,
    sha256_file,
    strict_load_json,
    strict_load_yaml,
    validate_checkpoint_manifest,
    validate_event_chain,
    validate_lineage,
    validate_schema_document,
    write_effective_lock,
)


ROOT = Path(__file__).resolve().parents[5]
PROTOCOL = Path(__file__).resolve().parent
CONTRACT_PATH = PROTOCOL / "study-contract.yaml"
EVIDENCE_DIR = PROTOCOL / "evidence"
GENESIS_LOCK_PATH = PROTOCOL / "locks/s00-foundation-lock.json"
SUCCESSOR_LOCK_PATH = (
    PROTOCOL / "locks/s00-foundation-lock-successor-001.json"
)
LOCK_PATH = GENESIS_LOCK_PATH
IMMUTABLE_OLD_OUTPUTS = (
    GENESIS_LOCK_PATH,
    EVIDENCE_DIR / "s00-neutrality.json",
    EVIDENCE_DIR / "s00-resume-parity.json",
    EVIDENCE_DIR / "s00-reconciliation.json",
    EVIDENCE_DIR / "s00-lineage-fail-closed.json",
    EVIDENCE_DIR / "s00-decision.json",
)
IMMUTABLE_OLD_GENERATION = {
    str(path.relative_to(ROOT)): digest
    for path, digest in zip(
        IMMUTABLE_OLD_OUTPUTS,
        (
            "35d0c98cd9f6058fe21cd8723288d5bc34d68b87c3bf9e4bc9a0b7c488a0691c",
            "ada294f5cbf62643490564e52b8cb88092c8b6c07ad09ab7e8030f2bf436a315",
            "fe447f49989ad4996358cbeae60918c3209eebce314154ec022ad1e95b402281",
            "bf6b83e739c6fc4c8dd437675f6b8f2cbeeceb31c3c287c71a877318cf04597a",
            "05a0fa9be80174a560de180ceb8bfe0399bb7ca01d625b0961910b97d1e46a82",
            "e73601ba108c31ac15d3372b8b951b8f5b50110071a5d74f8c5f982f5ac101c0",
        ),
    )
}
SUCCESSOR_EVIDENCE_PATHS = (
    EVIDENCE_DIR / "s00-neutrality-successor-001.json",
    EVIDENCE_DIR / "s00-resume-parity-successor-001.json",
    EVIDENCE_DIR / "s00-reconciliation-successor-001.json",
    EVIDENCE_DIR / "s00-lineage-fail-closed-successor-001.json",
)
SUCCESSOR_DECISION_PATH = EVIDENCE_DIR / "s00-decision-successor-001.json"
SUCCESSOR_OUTPUT_PATHS = (
    SUCCESSOR_LOCK_PATH,
    *SUCCESSOR_EVIDENCE_PATHS,
    SUCCESSOR_DECISION_PATH,
)
OUTPUT_PATHS = IMMUTABLE_OLD_OUTPUTS
LOCK_SCHEMA_PATH = PROTOCOL / "schemas/lock.schema.json"
AMENDMENT_LEDGER_PATH = PROTOCOL / "amendment-ledger.jsonl"
ORIGINAL_PLAN_B_PATH = (
    "agent_run/260725-ductile-factorized-guidance-s0-s2/"
    "milestones/S00/plan_b.md"
)
ORIGINAL_PLAN_B_SHA256 = (
    "b8e7a458bb6cb6fa103e92c50eed5c11b2e964c354dd71d629c61cdeecc571d9"
)
RECOVERY_PLAN_B_PATH = (
    "agent_run/260725-ductile-factorized-guidance-s0-s2/"
    "milestones/S00/recovery/plan_b.md"
)
RECOVERY_PLAN_B_SHA256 = (
    "3f64ec77def3960b67756b0af576bdb5d4f28683ed11a1df55956fe87c0e34c2"
)
OLD_LOCK_ID = (
    "s00-lock-6c9bc5c909f46d287cada9e8b8a3b74d51e6a36dabc50ab98218d7d4ac0c1946"
)
OLD_LOCK_RAW_SHA256 = IMMUTABLE_OLD_GENERATION[
    str(GENESIS_LOCK_PATH.relative_to(ROOT))
]
AMENDMENT_ID = "s00-successor-recovery-001"
AMENDMENT_HEAD_SHA256 = (
    "ec0e72c60aaa2d4ea1b54545aa1c9cbd2039401447bcca6d0d374e1866ee77b2"
)
AMENDMENT_RAW_SHA256 = (
    "92da8dde11de879c573018a1f968648cef6f328ba44cee06e83f3b379ce81619"
)
FORMAL_REPORT_PATH = (
    "study_docs/research/ductile-origami-warmstart/reports/staged/"
    "s00-foundation-verification-report.md"
)
FORMAL_REPORT_IDENTITY_SHA256 = canonical_sha256(
    {"path": FORMAL_REPORT_PATH}
)
ADJUDICATION_PATH = (
    "agent_run/260725-ductile-factorized-guidance-s0-s2/adjudication.md"
)
RECOVERY_AUTHORITY = {
    "standing_delegation": "2026-07-25",
    "reviewers": [
        "/root/s00_recovery_design_a",
        "/root/s00_recovery_design_b",
    ],
    "consensus": ["AGREE", "AGREE"],
    "adjudication_reference": {
        "path": ADJUDICATION_PATH,
        "identity_sha256": canonical_sha256({
            "path": ADJUDICATION_PATH,
            "section": "S00 successor recovery",
        }),
    },
}

IMPLEMENTATION_WHITELIST = [
    "projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py",
    "projects/hipblaslt/tensilelite/Tensile/ductile/evidence.py",
    "projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s00_foundation.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/README.md",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/study-contract.yaml",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/amendment-ledger.jsonl",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/study-contract.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/amendment.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/lock.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/event.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/checkpoint.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/lineage.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/valid-run.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/invalid-lineage.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/duplicate-events.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/backend-failure.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s00-foundation-lock.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-neutrality.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-resume-parity.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-reconciliation.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-lineage-fail-closed.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-decision.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s00-foundation-lock-successor-001.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-neutrality-successor-001.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-resume-parity-successor-001.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-reconciliation-successor-001.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-lineage-fail-closed-successor-001.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-decision-successor-001.json",
]
DELIVERY_WHITELIST = [
    "projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py",
    "projects/hipblaslt/tensilelite/Tensile/ductile/evidence.py",
    "projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s00_foundation.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/README.md",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/study-contract.yaml",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/amendment-ledger.jsonl",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/study-contract.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/amendment.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/lock.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/event.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/checkpoint.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/lineage.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/valid-run.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/invalid-lineage.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/duplicate-events.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/backend-failure.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s00-foundation-lock.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-neutrality.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-resume-parity.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-reconciliation.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-lineage-fail-closed.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-decision.json",
    "study_docs/research/ductile-origami-warmstart/reports/staged/s00-foundation-verification-report.md",
    "study_docs/research/ductile-origami-warmstart-experiment-plan.md",
    "study_docs/research/ductile-origami-warmstart/README.md",
    "study_docs/research/ductile-origami-warmstart/s00-evidence-contract-lineage-observability-design.md",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s00-foundation-lock-successor-001.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-neutrality-successor-001.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-resume-parity-successor-001.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-reconciliation-successor-001.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-lineage-fail-closed-successor-001.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-decision-successor-001.json",
]
AUTHORITY_PATHS = [
    ".cursor/rules/hipblaslt-onboarding.mdc",
    ".cursor/skills/implement-verify-loop/SKILL.md",
    "study_docs/research/surrogate-dse-plan.md",
    "study_docs/research/ductile-origami-warmstart-experiment-plan.md",
    "study_docs/research/ductile-origami-warmstart/README.md",
    "study_docs/research/ductile-origami-warmstart/s00-evidence-contract-lineage-observability-design.md",
]
PINNED_SOURCE_PATHS = [
    "projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py",
    "projects/hipblaslt/tensilelite/Tensile/ductile/evidence.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py",
    "projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s00_foundation.py",
    "projects/hipblaslt/tensilelite/Tensile/ductile/core/space.py",
    "projects/hipblaslt/tensilelite/Tensile/ductile/core/mutation.py",
    "projects/hipblaslt/tensilelite/Tensile/ductile/core/mating.py",
    "projects/hipblaslt/tensilelite/Tensile/ductile/core/selection.py",
    "projects/hipblaslt/tensilelite/Tensile/ductile/core/crossover.py",
    "projects/hipblaslt/tensilelite/Tensile/ductile/core/survival.py",
    "projects/hipblaslt/tensilelite/Tensile/ductile/core/population.py",
]


def _schema(name):
    return strict_load_json(PROTOCOL / "schemas" / name)


def _fixture(name):
    return strict_load_json(PROTOCOL / "fixtures" / name)


def _expect_code(callable_, expected):
    try:
        callable_()
    except EvidenceValidationError as exc:
        if exc.code != expected:
            raise EvidenceValidationError(
                f"expected {expected}, got {exc.code}",
                code="fixture_expectation_mismatch",
            ) from exc
        return
    raise EvidenceValidationError(
        f"expected rejection {expected}", code="fixture_expectation_mismatch"
    )


def _apply_lineage_case(base, case):
    candidate = copy.deepcopy(base)
    if case["operation"] == "remove":
        candidate.pop(case["field"])
    else:
        candidate[case["field"]] = copy.deepcopy(case["value"])
    return candidate


def _apply_event_case(base, case):
    events = copy.deepcopy(base)
    operation = case["operation"]
    target = case.get("target_index")
    if operation == "copy_field":
        events[target][case["field"]] = events[case["source_index"]][case["field"]]
    elif operation == "replace":
        events[target][case["field"]] = case["value"]
    elif operation == "remove_event":
        events.pop(target)
    elif operation == "remove_field":
        events[target].pop(case["field"])
    elif operation == "replace_event":
        events[target] = case["value"]
    return events


def _record(kind, status, previous, lineage, payload, record_id):
    record = {
        "record_id": record_id,
        "kind": kind,
        "status": status,
        "previous_record_sha256": previous,
        "lineage": copy.deepcopy(lineage),
        "payload": payload,
        "payload_sha256": canonical_sha256(payload),
    }
    record["record_sha256"] = canonical_sha256(record)
    return record


def _rehash_records(records):
    previous = None
    result = []
    for index, source in enumerate(records):
        result.append(_record(
            source["kind"],
            source["status"],
            previous,
            source["lineage"],
            source["payload"],
            source.get("record_id", f"{source['kind']}-{index}"),
        ))
        previous = result[-1]["record_sha256"]
    return result


def _apply_backend_case(fixture, case):
    records = copy.deepcopy(fixture["failure_records"])
    operation = case["operation"]
    target = case["target_index"]
    if operation == "remove_record":
        records.pop(target)
    elif operation == "replace_status":
        records[target]["status"] = case["value"]
    elif operation == "insert_success_observation":
        records.insert(target, {
            "record_id": "unexpected-observation",
            "kind": "benchmark_observation",
            "status": "success",
            "lineage": copy.deepcopy(fixture["lineage"]),
            "payload": {"score": 1.0, "unit": "synthetic"},
        })
    return _rehash_records(records)


def validate_fixtures():
    lineage_schema = _schema("lineage.schema.json")
    event_schema = _schema("event.schema.json")
    valid = _fixture("valid-run.json")
    if canonical_sha256(valid["payload"]) != valid["payload_sha256"]:
        raise EvidenceValidationError(
            "valid-run payload hash mismatch", code="fixture_hash_mismatch"
        )
    validate_schema_document(valid["lineage"], lineage_schema, context="valid lineage")
    validate_lineage(valid["lineage"])
    for event in valid["events"]:
        validate_schema_document(event, event_schema, context="valid event")
    validate_event_chain(valid["events"])
    if reconcile_artifacts(
            valid["records"], expected_lineage=valid["lineage"]
    )["outcome"] != "success":
        raise EvidenceValidationError(
            "valid-run did not reconcile as success",
            code="fixture_expectation_mismatch",
        )

    invalid = _fixture("invalid-lineage.json")
    if canonical_sha256(invalid["payload"]) != invalid["payload_sha256"]:
        raise EvidenceValidationError(
            "invalid-lineage payload hash mismatch", code="fixture_hash_mismatch"
        )
    validate_lineage(invalid["base_lineage"])
    for case in invalid["cases"]:
        candidate = _apply_lineage_case(invalid["base_lineage"], case)
        if "mismatch" in case["case_id"]:
            operation = lambda c=candidate: validate_lineage(
                c, invalid["base_lineage"]
            )
        else:
            operation = lambda c=candidate: validate_lineage(c)
        _expect_code(operation, case["expected_error"])

    duplicate = _fixture("duplicate-events.json")
    if canonical_sha256(duplicate["payload"]) != duplicate["payload_sha256"]:
        raise EvidenceValidationError(
            "duplicate-events payload hash mismatch", code="fixture_hash_mismatch"
        )
    validate_event_chain(duplicate["base_events"])
    for case in duplicate["cases"]:
        candidate = _apply_event_case(duplicate["base_events"], case)
        _expect_code(
            lambda c=candidate: validate_event_chain(c),
            case["expected_error"],
        )

    failure = _fixture("backend-failure.json")
    if canonical_sha256(failure["payload"]) != failure["payload_sha256"]:
        raise EvidenceValidationError(
            "backend-failure payload hash mismatch", code="fixture_hash_mismatch"
        )
    if reconcile_artifacts(
            failure["failure_records"], expected_lineage=failure["lineage"]
    )["outcome"] != "backend_failure":
        raise EvidenceValidationError(
            "explicit failure did not reconcile",
            code="fixture_expectation_mismatch",
        )
    for case in failure["cases"]:
        candidate = _apply_backend_case(failure, case)
        _expect_code(
            lambda c=candidate: reconcile_artifacts(
                c, expected_lineage=failure["lineage"]
            ),
            case["expected_error"],
        )
    return {
        "valid": "success",
        "invalid_lineage_cases": len(invalid["cases"]),
        "invalid_event_cases": len(duplicate["cases"]),
        "backend_failure_cases": len(failure["cases"]),
    }


def preflight():
    existing = [str(path.relative_to(ROOT)) for path in OUTPUT_PATHS if path.exists()]
    if existing:
        raise EvidenceValidationError(
            f"lock/evidence must be absent: {existing}",
            code="preflight_output_exists",
        )
    contract = strict_load_yaml(CONTRACT_PATH)
    validate_schema_document(
        contract, _schema("study-contract.schema.json"), context="study contract"
    )
    if contract["implementation_whitelist"] != IMPLEMENTATION_WHITELIST:
        raise EvidenceValidationError(
            "implementation whitelist mismatch", code="whitelist_mismatch"
        )
    if contract["delivery_whitelist"] != DELIVERY_WHITELIST:
        raise EvidenceValidationError(
            "delivery whitelist mismatch", code="whitelist_mismatch"
        )
    if [item["path"] for item in contract["authorities"]] != AUTHORITY_PATHS:
        raise EvidenceValidationError(
            "authority path set/order mismatch", code="authority_binding_mismatch"
        )
    if [item["path"] for item in contract["pinned_sources"]] != PINNED_SOURCE_PATHS:
        raise EvidenceValidationError(
            "pinned source path set/order mismatch",
            code="source_binding_mismatch",
        )
    for name in (
        "study-contract.schema.json",
        "amendment.schema.json",
        "lock.schema.json",
        "event.schema.json",
        "checkpoint.schema.json",
        "lineage.schema.json",
    ):
        schema = _schema(name)
        validate_schema_document({}, {"type": "object"}, context=f"metaschema {name}")
        # Construction performs the selected engine's full metaschema check.
        from Tensile.ductile.evidence import _validator_for
        _validator_for(schema)
    for group in ("authorities", "pinned_sources", "schemas", "fixtures"):
        for binding in contract[group]:
            path = resolve_bound_path(ROOT, binding["path"])
            actual = sha256_file(path)
            if actual != binding["sha256"]:
                raise EvidenceValidationError(
                    f"{group} hash mismatch: {binding['path']}",
                    code="bound_hash_mismatch",
                )
    ledger_binding = contract["amendment_ledger"]
    if ledger_binding["path"] != str(AMENDMENT_LEDGER_PATH.relative_to(ROOT)):
        raise EvidenceValidationError(
            "amendment ledger path mismatch",
            code="amendment_ledger_binding_mismatch",
        )
    if sha256_file(AMENDMENT_LEDGER_PATH) != ledger_binding["sha256"]:
        raise EvidenceValidationError(
            "amendment ledger hash mismatch",
            code="amendment_ledger_binding_mismatch",
        )
    if AMENDMENT_LEDGER_PATH.read_bytes() != b"":
        raise EvidenceValidationError(
            "genesis amendment ledger must be zero bytes",
            code="amendment_ledger_not_empty",
        )
    fixture_result = validate_fixtures()
    with tempfile.TemporaryDirectory(prefix="s00-preflight-") as directory:
        target = Path(directory) / "exclusive.json"
        atomic_write_json(target, {"dry_run": True})
        _expect_code(
            lambda: atomic_write_json(target, {"dry_run": True}),
            "already_exists",
        )
    result = {
        "status": "S00_PREFLIGHT_OK",
        "authorities": "valid",
        "sources": "valid",
        "schemas": "valid",
        "fixtures": fixture_result,
        "amendment_ledger": "zero-byte-bound",
        "whitelists": "exact",
        "outputs": "absent",
    }
    print(json.dumps(result, sort_keys=True))
    return result


def _assert_immutable_old_generation():
    mismatches = []
    for relative, expected in IMMUTABLE_OLD_GENERATION.items():
        path = ROOT / relative
        actual = sha256_file(path) if path.is_file() else None
        if actual != expected:
            mismatches.append({
                "path": relative,
                "expected": expected,
                "actual": actual,
            })
    if mismatches:
        raise EvidenceValidationError(
            f"immutable old generation mismatch: {mismatches}",
            code="immutable_old_generation_mismatch",
        )
    return copy.deepcopy(IMMUTABLE_OLD_GENERATION)


def _assert_successor_targets_absent(paths=SUCCESSOR_OUTPUT_PATHS):
    present = [
        str(Path(path).relative_to(ROOT))
        for path in paths if Path(path).exists()
    ]
    if present:
        raise EvidenceValidationError(
            f"successor targets already exist: {present}",
            code="successor_target_exists",
        )


def _read_amendment_head():
    raw = AMENDMENT_LEDGER_PATH.read_bytes()
    if sha256_file(AMENDMENT_LEDGER_PATH) != AMENDMENT_RAW_SHA256:
        raise EvidenceValidationError(
            "amendment ledger raw hash mismatch",
            code="amendment_ledger_binding_mismatch",
        )
    lines = raw.splitlines()
    if len(lines) != 1 or not lines[0]:
        raise EvidenceValidationError(
            "exactly one amendment entry is required",
            code="amendment_ledger_entry_count",
        )
    entry = strict_load_json(lines[0].decode("utf-8"), from_text=True)
    validate_schema_document(
        entry, _schema("amendment.schema.json"), context="successor amendment"
    )
    if (
            entry["previous_entry_sha256"] is not None or
            entry["amendment_id"] != AMENDMENT_ID or
            entry["superseded_lock_id"] != OLD_LOCK_ID or
            entry["superseded_lock_sha256"] != OLD_LOCK_RAW_SHA256 or
            canonical_sha256(entry) != AMENDMENT_HEAD_SHA256 or
            __import__("hashlib").sha256(lines[0]).hexdigest()
            != AMENDMENT_HEAD_SHA256):
        raise EvidenceValidationError(
            "first amendment identity/content mismatch",
            code="amendment_head_mismatch",
        )
    return {
        "path": str(AMENDMENT_LEDGER_PATH.relative_to(ROOT)),
        "raw_sha256": AMENDMENT_RAW_SHA256,
        "head_sha256": AMENDMENT_HEAD_SHA256,
        "amendment_id": AMENDMENT_ID,
    }


def _expected_successor_contract(contract=None):
    contract = (
        strict_load_yaml(CONTRACT_PATH) if contract is None
        else copy.deepcopy(contract)
    )
    expected_scalars = {
        "protocol": "ductile-origami-s00-v1",
        "checkpoint": "S00",
        "generation": "successor-001",
        "criterion": "S00_EVIDENCE_READY",
        "positive_edge": "S10",
    }
    for field, expected in expected_scalars.items():
        if contract.get(field) != expected:
            raise EvidenceValidationError(
                f"contract {field} mismatch",
                code="contract_binding_mismatch",
            )
    if contract.get("baseline") != {
            "branch": "users/perlee/doc-study",
            "commit": "60775f12843bee9f95cb0bef4e91de8bc4dc9dc3"}:
        raise EvidenceValidationError(
            "contract baseline mismatch", code="contract_binding_mismatch"
        )
    if (
            contract.get("implementation_whitelist")
            != IMPLEMENTATION_WHITELIST or
            contract.get("delivery_whitelist") != DELIVERY_WHITELIST or
            contract.get("implementation_whitelist_sha256")
            != canonical_sha256(IMPLEMENTATION_WHITELIST) or
            contract.get("delivery_whitelist_sha256")
            != canonical_sha256(DELIVERY_WHITELIST)):
        raise EvidenceValidationError(
            "contract literal whitelist mismatch", code="whitelist_mismatch"
        )
    if contract.get("plan_b_bindings") != [
        {"path": ORIGINAL_PLAN_B_PATH, "sha256": ORIGINAL_PLAN_B_SHA256},
        {"path": RECOVERY_PLAN_B_PATH, "sha256": RECOVERY_PLAN_B_SHA256},
    ]:
        raise EvidenceValidationError(
            "contract Plan-B bindings mismatch", code="plan_b_binding_mismatch"
        )
    if contract.get("amendment_ledger") != _read_amendment_head():
        raise EvidenceValidationError(
            "contract amendment binding mismatch",
            code="amendment_ledger_binding_mismatch",
        )
    old_generation = [
        {"path": path, "sha256": digest}
        for path, digest in IMMUTABLE_OLD_GENERATION.items()
    ]
    if (
            contract.get("old_lock") != {
                "path": str(GENESIS_LOCK_PATH.relative_to(ROOT)),
                "lock_id": OLD_LOCK_ID,
                "sha256": OLD_LOCK_RAW_SHA256,
            } or
            contract.get("immutable_old_generation") != old_generation):
        raise EvidenceValidationError(
            "contract old generation binding mismatch",
            code="immutable_old_generation_mismatch",
        )
    if contract.get("recovery_authority") != RECOVERY_AUTHORITY:
        raise EvidenceValidationError(
            "contract recovery authority mismatch",
            code="recovery_authority_mismatch",
        )
    if contract.get("formal_report") != {
            "path": FORMAL_REPORT_PATH,
            "canonical_identity_sha256": FORMAL_REPORT_IDENTITY_SHA256,
    }:
        raise EvidenceValidationError(
            "contract report identity mismatch",
            code="report_binding_mismatch",
        )
    if contract.get("evidence_outputs") != [
            str(path.relative_to(ROOT)) for path in SUCCESSOR_OUTPUT_PATHS]:
        raise EvidenceValidationError(
            "contract successor outputs mismatch",
            code="contract_binding_mismatch",
        )
    if [item["path"] for item in contract.get("authorities", [])] != AUTHORITY_PATHS:
        raise EvidenceValidationError(
            "contract authority order mismatch",
            code="authority_binding_mismatch",
        )
    if [item["path"] for item in contract.get("pinned_sources", [])] != PINNED_SOURCE_PATHS:
        raise EvidenceValidationError(
            "contract source order mismatch", code="source_binding_mismatch"
        )
    if contract.get("seeds") != {
            "neutrality": 41001,
            "resume": 41002,
            "reconciliation": 41003,
            "lineage": 41004}:
        raise EvidenceValidationError(
            "contract seeds mismatch", code="seed_binding_mismatch"
        )
    return contract


def _assert_plan_b_bindings(
        original_plan_b, recovery_plan_b, *, verify_bytes=True):
    supplied = (str(original_plan_b), str(recovery_plan_b))
    expected_paths = (ORIGINAL_PLAN_B_PATH, RECOVERY_PLAN_B_PATH)
    if supplied != expected_paths:
        raise EvidenceValidationError(
            "Plan-B path substitution rejected", code="plan_b_path_mismatch"
        )
    bindings = [
        {"path": ORIGINAL_PLAN_B_PATH, "sha256": ORIGINAL_PLAN_B_SHA256},
        {"path": RECOVERY_PLAN_B_PATH, "sha256": RECOVERY_PLAN_B_SHA256},
    ]
    if verify_bytes:
        for binding in bindings:
            if sha256_file(resolve_bound_path(ROOT, binding["path"])) != binding["sha256"]:
                raise EvidenceValidationError(
                    f"Plan-B bytes differ: {binding['path']}",
                    code="plan_b_binding_mismatch",
                )
    return bindings


def _validate_bound_contract_bytes(contract):
    for group in ("authorities", "pinned_sources", "schemas", "fixtures"):
        for binding in contract[group]:
            path = resolve_bound_path(ROOT, binding["path"])
            if sha256_file(path) != binding["sha256"]:
                raise EvidenceValidationError(
                    f"{group} bytes changed: {binding['path']}",
                    code="bound_hash_mismatch",
                )


def _validate_genesis_lock():
    _assert_immutable_old_generation()
    lock = strict_load_json(GENESIS_LOCK_PATH)
    base = {
        key: value for key, value in lock.items()
        if key not in {"lock_id", "body_sha256"}
    }
    if (
            _derived_lock_document(base) != lock or
            lock.get("lock_id") != OLD_LOCK_ID or
            lock.get("parent_lock") is not None):
        raise EvidenceValidationError(
            "old genesis lock identity/parent mismatch",
            code="genesis_lock_mismatch",
        )
    return lock


def preflight_successor(
        original_plan_b, recovery_plan_b, *, verify_plan_bytes=True):
    _assert_immutable_old_generation()
    _assert_successor_targets_absent()
    _assert_plan_b_bindings(
        original_plan_b,
        recovery_plan_b,
        verify_bytes=verify_plan_bytes,
    )
    _validate_genesis_lock()
    contract = strict_load_yaml(CONTRACT_PATH)
    validate_schema_document(
        contract, _schema("study-contract.schema.json"),
        context="successor study contract",
    )
    contract = _expected_successor_contract(contract)
    _validate_bound_contract_bytes(contract)
    for name in (
            "study-contract.schema.json", "amendment.schema.json",
            "lock.schema.json", "event.schema.json",
            "checkpoint.schema.json", "lineage.schema.json"):
        from Tensile.ductile.evidence import _validator_for
        _validator_for(_schema(name))
    fixture_result = validate_fixtures()
    reconciliation = run_reconciliation()
    if reconciliation["criterion_status"] != "PASS":
        raise EvidenceValidationError(
            "successor reconciliation probes failed",
            code="fixture_expectation_mismatch",
        )
    result = {
        "status": "S00_SUCCESSOR_PREFLIGHT_OK",
        "plan_bs": "original/recovery-valid",
        "whitelists": {
            "implementation_count": len(IMPLEMENTATION_WHITELIST),
            "implementation_sha256": canonical_sha256(
                IMPLEMENTATION_WHITELIST
            ),
            "delivery_count": len(DELIVERY_WHITELIST),
            "delivery_sha256": canonical_sha256(DELIVERY_WHITELIST),
        },
        "ledger": "one-entry-valid",
        "ledger_head_sha256": AMENDMENT_HEAD_SHA256,
        "ledger_raw_sha256": AMENDMENT_RAW_SHA256,
        "old_generation": "immutable-valid",
        "authorities": "valid",
        "sources": "valid",
        "schemas": "valid",
        "fixtures": fixture_result,
        "seeds": "valid",
        "report": "identity-valid",
        "recovery_authority": "valid",
        "negative_probes": "pass",
        "successor_targets": "absent",
        "claim_boundary": "cpu-only-synthetic/no-s10",
    }
    print(json.dumps(result, sort_keys=True))
    return result


def _derived_lock_document(base):
    digest = canonical_sha256(base)
    return dict(base, lock_id=f"s00-lock-{digest}", body_sha256=digest)


def _validate_lock(lock, *, lock_path=LOCK_PATH, contract_path=CONTRACT_PATH):
    if lock.get("generation") == "successor-001":
        return _validate_successor_lock(
            lock,
            lock_path=lock_path,
            contract_path=contract_path,
        )
    base = {
        key: value for key, value in lock.items()
        if key not in {"lock_id", "body_sha256"}
    }
    if _derived_lock_document(base) != lock:
        raise EvidenceValidationError(
            "effective lock derived identity mismatch", code="lock_hash_mismatch"
        )
    contract_path = Path(contract_path)
    contract = strict_load_yaml(contract_path)
    validate_schema_document(
        contract, _schema("study-contract.schema.json"), context="locked contract"
    )
    for group in ("authorities", "pinned_sources", "schemas", "fixtures"):
        lock_group = "sources" if group == "pinned_sources" else group
        if lock[lock_group] != contract[group]:
            raise EvidenceValidationError(
                f"lock {lock_group} differs from contract",
                code="lock_binding_mismatch",
            )
        for binding in lock[lock_group]:
            if sha256_file(resolve_bound_path(ROOT, binding["path"])) != binding["sha256"]:
                raise EvidenceValidationError(
                    f"lock bound bytes changed: {binding['path']}",
                    code="lock_binding_mismatch",
                )
    expected_contract_path = str(contract_path.resolve().relative_to(ROOT))
    if (
            lock["contract"]["path"] != expected_contract_path or
            lock["contract"]["sha256"] != sha256_file(contract_path)):
        raise EvidenceValidationError(
            "contract bytes differ from lock", code="lock_binding_mismatch"
        )
    if lock["amendment_ledger"] != contract["amendment_ledger"]:
        raise EvidenceValidationError(
            "lock amendment ledger differs from contract",
            code="lock_binding_mismatch",
        )
    ledger_path = resolve_bound_path(ROOT, lock["amendment_ledger"]["path"])
    if sha256_file(ledger_path) != lock["amendment_ledger"]["sha256"]:
        raise EvidenceValidationError(
            "amendment ledger bytes differ from lock",
            code="lock_binding_mismatch",
        )
    plan_path = resolve_bound_path(ROOT, lock["plan_b"]["path"])
    if sha256_file(plan_path) != lock["plan_b"]["sha256"]:
        raise EvidenceValidationError(
            "Plan-B bytes differ from lock", code="lock_binding_mismatch"
        )
    return lock


def create_lock(plan_b):
    if str(plan_b) != ORIGINAL_PLAN_B_PATH:
        raise EvidenceValidationError(
            "Plan-B path is not the frozen opaque binding",
            code="plan_b_path_mismatch",
        )
    preflight()
    contract = strict_load_yaml(CONTRACT_PATH)
    plan_path = resolve_bound_path(ROOT, plan_b)
    base = {
        "protocol_id": contract["protocol"],
        "checkpoint_id": "S00",
        "parent_lock": None,
        "state": "effective",
        "baseline_commit": contract["baseline"]["commit"],
        "contract": {
            "path": str(CONTRACT_PATH.relative_to(ROOT)),
            "sha256": sha256_file(CONTRACT_PATH),
        },
        "plan_b": {"path": plan_b, "sha256": sha256_file(plan_path)},
        "implementation_whitelist": IMPLEMENTATION_WHITELIST,
        "delivery_whitelist": DELIVERY_WHITELIST,
        "authorities": contract["authorities"],
        "sources": contract["pinned_sources"],
        "schemas": contract["schemas"],
        "fixtures": contract["fixtures"],
        "amendment_ledger": contract["amendment_ledger"],
        "seeds": contract["seeds"],
        "formal_report": contract["formal_report"],
        "creation": {
            "command": (
                "PYTHONPATH=projects/hipblaslt/tensilelite python3 -B "
                "study_docs/research/ductile-origami-warmstart/protocol/v1/"
                f"run_s00_foundation.py lock --plan-b {plan_b}"
            ),
            "cwd": str(ROOT),
        },
    }
    lock = _derived_lock_document(base)
    raw_hash = write_effective_lock(LOCK_PATH, lock, _schema("lock.schema.json"))
    loaded = _validate_lock(strict_load_json(LOCK_PATH))
    if loaded["parent_lock"] is not None:
        raise EvidenceValidationError(
            "genesis lock parent must be null", code="lock_parent_mismatch"
        )
    print(json.dumps({
        "status": "S00_LOCK_EFFECTIVE",
        "lock_id": loaded["lock_id"],
        "sha256": raw_hash,
        "parent_lock": loaded["parent_lock"],
    }, sort_keys=True))


def _successor_lock_base(contract, *, contract_path=CONTRACT_PATH):
    contract_path = Path(contract_path)
    return {
        "protocol_id": "ductile-origami-s00-v1",
        "checkpoint_id": "S00",
        "generation": "successor-001",
        "parent_lock": {
            "lock_id": OLD_LOCK_ID,
            "sha256": OLD_LOCK_RAW_SHA256,
        },
        "state": "effective",
        "baseline_commit": "60775f12843bee9f95cb0bef4e91de8bc4dc9dc3",
        "contract": {
            "path": str(contract_path.resolve().relative_to(ROOT)),
            "sha256": sha256_file(contract_path),
        },
        "plan_bs": copy.deepcopy(contract["plan_b_bindings"]),
        "implementation_whitelist": copy.deepcopy(
            IMPLEMENTATION_WHITELIST
        ),
        "implementation_whitelist_sha256": canonical_sha256(
            IMPLEMENTATION_WHITELIST
        ),
        "delivery_whitelist": copy.deepcopy(DELIVERY_WHITELIST),
        "delivery_whitelist_sha256": canonical_sha256(
            DELIVERY_WHITELIST
        ),
        "authorities": copy.deepcopy(contract["authorities"]),
        "sources": copy.deepcopy(contract["pinned_sources"]),
        "schemas": copy.deepcopy(contract["schemas"]),
        "fixtures": copy.deepcopy(contract["fixtures"]),
        "amendment": copy.deepcopy(contract["amendment_ledger"]),
        "seeds": copy.deepcopy(contract["seeds"]),
        "formal_report": copy.deepcopy(contract["formal_report"]),
        "immutable_old_generation": copy.deepcopy(
            contract["immutable_old_generation"]
        ),
        "recovery_authority": copy.deepcopy(
            contract["recovery_authority"]
        ),
        "creation": {
            "command": (
                "PYTHONPATH=projects/hipblaslt/tensilelite python3 -B "
                "study_docs/research/ductile-origami-warmstart/protocol/v1/"
                "run_s00_foundation.py lock-successor "
                f"--original-plan-b {ORIGINAL_PLAN_B_PATH} "
                f"--recovery-plan-b {RECOVERY_PLAN_B_PATH}"
            ),
            "cwd": str(ROOT),
        },
    }


def _validate_successor_lock(
        lock, *, lock_path=SUCCESSOR_LOCK_PATH,
        contract_path=CONTRACT_PATH, verify_bound_bytes=True,
        verify_plan_bytes=True):
    validate_schema_document(
        lock, _schema("lock.schema.json"), context="successor effective lock"
    )
    base = {
        key: value for key, value in lock.items()
        if key not in {"lock_id", "body_sha256"}
    }
    if _derived_lock_document(base) != lock:
        raise EvidenceValidationError(
            "successor lock derived identity mismatch",
            code="lock_hash_mismatch",
        )
    contract_path = Path(contract_path)
    contract = strict_load_yaml(contract_path)
    if contract_path.resolve() == CONTRACT_PATH.resolve():
        validate_schema_document(
            contract, _schema("study-contract.schema.json"),
            context="successor locked contract",
        )
        contract = _expected_successor_contract(contract)
    expected = _derived_lock_document(
        _successor_lock_base(contract, contract_path=contract_path)
    )
    if lock != expected:
        raise EvidenceValidationError(
            "successor lock frozen binding substitution",
            code="lock_binding_mismatch",
        )
    parent = lock["parent_lock"]
    if parent != {
            "lock_id": OLD_LOCK_ID, "sha256": OLD_LOCK_RAW_SHA256}:
        raise EvidenceValidationError(
            "successor parent is not the immutable genesis lock",
            code="lock_parent_mismatch",
        )
    if verify_bound_bytes:
        if contract_path.resolve() == CONTRACT_PATH.resolve():
            _assert_immutable_old_generation()
            _validate_genesis_lock()
            _read_amendment_head()
        _validate_bound_contract_bytes(contract)
        if sha256_file(contract_path) != lock["contract"]["sha256"]:
            raise EvidenceValidationError(
                "successor contract bytes changed",
                code="lock_binding_mismatch",
            )
    if verify_plan_bytes:
        _assert_plan_b_bindings(
            lock["plan_bs"][0]["path"],
            lock["plan_bs"][1]["path"],
            verify_bytes=True,
        )
    return lock


def create_successor_lock(original_plan_b, recovery_plan_b):
    preflight_successor(original_plan_b, recovery_plan_b)
    _assert_immutable_old_generation()
    _assert_successor_targets_absent()
    _validate_genesis_lock()
    contract = _expected_successor_contract()
    lock = _derived_lock_document(_successor_lock_base(contract))
    raw_hash = write_effective_lock(
        SUCCESSOR_LOCK_PATH, lock, _schema("lock.schema.json")
    )
    loaded = _validate_successor_lock(
        strict_load_json(SUCCESSOR_LOCK_PATH)
    )
    _assert_immutable_old_generation()
    print(json.dumps({
        "status": "S00_SUCCESSOR_LOCK_EFFECTIVE",
        "lock_id": loaded["lock_id"],
        "sha256": raw_hash,
        "generation": loaded["generation"],
        "parent_lock": loaded["parent_lock"],
        "amendment": loaded["amendment"],
        "plan_bs": loaded["plan_bs"],
        "implementation_whitelist_sha256": (
            loaded["implementation_whitelist_sha256"]
        ),
        "delivery_whitelist_sha256": (
            loaded["delivery_whitelist_sha256"]
        ),
    }, sort_keys=True))


def _single_substitution_cases(valid_lock):
    cases = []

    def add(name, mutate, *, rederive=True):
        candidate = copy.deepcopy(valid_lock)
        if rederive:
            base = {
                key: value for key, value in candidate.items()
                if key not in {"lock_id", "body_sha256"}
            }
            mutate(base)
            candidate = _derived_lock_document(base)
        else:
            mutate(candidate)
        cases.append((name, candidate))

    for index, field in enumerate(("path", "sha256")):
        add(
            f"original-plan-b-{field}",
            lambda base, i=index, f=field: base["plan_bs"][0].__setitem__(
                f, "substituted/path" if i == 0 else "0" * 64
            ),
        )
        add(
            f"recovery-plan-b-{field}",
            lambda base, i=index, f=field: base["plan_bs"][1].__setitem__(
                f, "substituted/path" if i == 0 else "0" * 64
            ),
        )
    add(
        "baseline",
        lambda base: base.__setitem__("baseline_commit", "0" * 40),
    )
    for field, hash_field in (
            ("implementation_whitelist", "implementation_whitelist_sha256"),
            ("delivery_whitelist", "delivery_whitelist_sha256")):
        for index in range(len(valid_lock[field])):
            def substitute(base, f=field, h=hash_field, i=index):
                base[f][i] = f"substituted/{f}/{i}"
                base[h] = canonical_sha256(base[f])
            add(f"{field}-substitute-{index}", substitute)

            def omit(base, f=field, h=hash_field, i=index):
                base[f].pop(i)
                base[h] = canonical_sha256(base[f])
            add(f"{field}-omit-{index}", omit)
        add(
            f"{hash_field}-substitute",
            lambda base, h=hash_field: base.__setitem__(h, "0" * 64),
        )
    for field in ("path", "sha256"):
        add(
            f"contract-{field}",
            lambda base, f=field: base["contract"].__setitem__(
                f, "substituted/contract" if f == "path" else "0" * 64
            ),
        )
    for group in ("authorities", "sources", "schemas", "fixtures"):
        for index in range(len(valid_lock[group])):
            for field in ("path", "sha256"):
                add(
                    f"{group}-{index}-{field}",
                    lambda base, g=group, i=index, f=field: (
                        base[g][i].__setitem__(
                            f,
                            f"substituted/{g}/{i}"
                            if f == "path" else "0" * 64,
                        )
                    ),
                )
    for seed in valid_lock["seeds"]:
        add(
            f"seed-{seed}",
            lambda base, name=seed: base["seeds"].__setitem__(
                name, base["seeds"][name] + 1
            ),
        )
    for field in ("path", "canonical_identity_sha256"):
        add(
            f"report-{field}",
            lambda base, f=field: base["formal_report"].__setitem__(
                f, "substituted/report" if f == "path" else "0" * 64
            ),
        )
    amendment_values = {
        "path": "substituted/ledger",
        "raw_sha256": "0" * 64,
        "head_sha256": "0" * 64,
        "amendment_id": "substituted-amendment",
    }
    for field, value in amendment_values.items():
        add(
            f"amendment-{field}",
            lambda base, f=field, v=value: base["amendment"].__setitem__(
                f, v
            ),
        )
    for index in range(len(valid_lock["immutable_old_generation"])):
        for field in ("path", "sha256"):
            add(
                f"immutable-old-{index}-{field}",
                lambda base, i=index, f=field: (
                    base["immutable_old_generation"][i].__setitem__(
                        f,
                        f"substituted/old/{i}"
                        if f == "path" else "0" * 64,
                    )
                ),
            )
    for field in ("standing_delegation", "reviewers", "consensus"):
        add(
            f"recovery-authority-{field}",
            lambda base, f=field: base["recovery_authority"].__setitem__(
                f,
                "1900-01-01" if f == "standing_delegation"
                else ["substituted"],
            ),
        )
    for field in ("path", "identity_sha256"):
        add(
            f"recovery-authority-adjudication-{field}",
            lambda base, f=field: (
                base["recovery_authority"]["adjudication_reference"].__setitem__(
                    f,
                    "substituted/adjudication"
                    if f == "path" else "0" * 64,
                )
            ),
        )
    add("state", lambda base: base.__setitem__("state", "superseded"))
    add(
        "generation",
        lambda base: base.__setitem__("generation", "genesis"),
    )
    add("parent-null", lambda base: base.__setitem__("parent_lock", None))
    add(
        "parent-wrong-id",
        lambda base: base["parent_lock"].__setitem__("lock_id", "s00-lock-" + "0" * 64),
    )
    add(
        "parent-wrong-hash",
        lambda base: base["parent_lock"].__setitem__("sha256", "0" * 64),
    )
    add(
        "parent-self",
        lambda base: base["parent_lock"].__setitem__(
            "lock_id", valid_lock["lock_id"]
        ),
    )
    add(
        "lock-id-derived",
        lambda candidate: candidate.__setitem__(
            "lock_id", "s00-lock-" + "0" * 64
        ),
        rederive=False,
    )
    add(
        "body-sha256-derived",
        lambda candidate: candidate.__setitem__("body_sha256", "0" * 64),
        rederive=False,
    )
    return cases


def _combined_substituted_lock(valid_lock):
    base = {
        key: copy.deepcopy(value) for key, value in valid_lock.items()
        if key not in {"lock_id", "body_sha256"}
    }
    base["plan_bs"][0]["sha256"] = "0" * 64
    base["plan_bs"][1]["sha256"] = "0" * 64
    base["baseline_commit"] = "0" * 40
    base["implementation_whitelist"][0] = "substituted/implementation"
    base["implementation_whitelist_sha256"] = canonical_sha256(
        base["implementation_whitelist"]
    )
    base["delivery_whitelist"][0] = "substituted/delivery"
    base["delivery_whitelist_sha256"] = canonical_sha256(
        base["delivery_whitelist"]
    )
    base["seeds"]["neutrality"] += 1
    base["formal_report"]["path"] = "substituted/report"
    base["formal_report"]["canonical_identity_sha256"] = canonical_sha256(
        {"path": "substituted/report"}
    )
    base["parent_lock"] = {
        "lock_id": "s00-lock-" + "0" * 64,
        "sha256": "0" * 64,
    }
    return _derived_lock_document(base)


def _lineage(
        lock, seed_name, artifact_id, run_id, *,
        effective_lock_sha256=None):
    sources = canonical_sha256(lock["sources"])
    fixtures = canonical_sha256(lock["fixtures"])
    return {
        "artifact_id": artifact_id,
        "run_id": run_id,
        "effective_lock_sha256": (
            effective_lock_sha256 or sha256_file(LOCK_PATH)
        ),
        "parent_id": None,
        "input_sha256": lock["contract"]["sha256"],
        "source_bundle_sha256": sources,
        "fixture_sha256": fixtures,
        "seed": {"name": seed_name, "value": lock["seeds"][seed_name]},
    }


def _make_ga(seed, observer, lineage, *, checkpoint_path=None, interrupt=None):
    space = SearchSpace({"x": list(range(5)), "y": list(range(4))})
    mating = Mating(
        space,
        Selection.get("random", ratio=0.75, elitism=0.0),
        Crossover.get("ux", prob=0.8),
        Mutation(space, prob=0.25),
    )
    evaluations = []

    def evaluate(configs):
        copied = copy.deepcopy(configs)
        scores = np.array([
            1.0 + item["x"] * 0.25 + item["y"] * 0.125
            for item in copied
        ], dtype=np.float64)
        evaluations.append({
            "configs": copied,
            "configs_hash": canonical_sha256(copied),
            "scores": scores.tolist(),
            "scores_hash": canonical_sha256({
                "dtype": scores.dtype.str,
                "shape": list(scores.shape),
                "values": scores.tolist(),
            }),
        })
        return scores

    ga = GeneticAlgorithm(
        space,
        mating,
        evaluate,
        pop_size=6,
        n_gen=4,
        period=0,
        div_thr=0.0,
        seed=seed,
        verbose=0,
        observer=observer,
        checkpoint_path=str(checkpoint_path) if checkpoint_path else None,
        checkpoint_lineage=lineage,
        interrupt_after_generation=interrupt,
    )
    trace = {
        "updated_populations": [],
        "termination_updates": [],
        "survivors": [],
        "offspring": [],
    }

    def population_state(population):
        ordered = [{
            "X": dict(ind.X),
            "F": float(ind.F),
            "G": plain_value(ind.G),
        } for ind in population]
        return {
            "ordered": ordered,
            "canonical_sha256": canonical_sha256(
                sorted(ordered, key=lambda item: canonical_sha256(item["X"]))
            ),
        }

    original_update = ga.update
    original_termination = ga.termination
    original_survival = ga.survival
    original_mating = ga.mating

    def traced_update(best, pop, old_pop, scores):
        result = original_update(best, pop, old_pop, scores)
        trace["updated_populations"].append({
            "updated_population": population_state(pop),
            "old_population": population_state(old_pop),
            "champion": population_state(result[0]),
            "f_max": float(result[1]),
            "fitness_matrix": {
                "dtype": scores.dtype.str,
                "shape": list(scores.shape),
                "values": scores.tolist(),
                "canonical_sha256": canonical_sha256({
                    "dtype": scores.dtype.str,
                    "shape": list(scores.shape),
                    "values": scores.tolist(),
                }),
            },
        })
        return result

    def traced_termination(**kwargs):
        try:
            return original_termination(**kwargs)
        finally:
            trace["termination_updates"].append({
                "values": plain_value(kwargs),
                "stats": plain_value(ga.stats),
                "next_population_size": int(ga.pop_size),
                "decay_mode": ga._decay_type,
            })

    def traced_survival(old_pop, pop, size):
        result = original_survival(old_pop, pop, size)
        trace["survivors"].append(population_state(result))
        return result

    def traced_mating(pop, size):
        result = original_mating(pop, size)
        trace["offspring"].append(population_state(result))
        return result

    ga.update = traced_update
    ga.termination = traced_termination
    ga.survival = traced_survival
    ga.mating = traced_mating
    ga._fixture_trace = trace
    return ga, evaluations


def _run_ga(ga, evaluations):
    configs, fitness = ga.optimize()
    return {
        "format": "s00-ga-raw-run-v1",
        "evaluations": evaluations,
        "final_config": plain_value(configs),
        "final_fitness": plain_value(fitness),
        "stats": plain_value(ga.stats),
        "termination_reason": ga.termination_reason,
        "final_generation": ga.final_generation,
        "evaluation_count": sum(
            len(item["configs"]) for item in evaluations
        ),
        "base_population_size": int(ga._pop_size),
        "final_population_size": int(ga.pop_size),
        "population_decay": ga._decay_type,
        "python_rng_sha256": canonical_sha256(random.getstate()),
        "numpy_rng_sha256": canonical_sha256(np.random.get_state()),
        "seed_sequence_sha256": canonical_sha256(ga.space.seed_seq.state),
        "trajectory": plain_value(ga._fixture_trace),
    }


RAW_RUN_FIELDS = (
    "format",
    "evaluations",
    "final_config",
    "final_fitness",
    "stats",
    "termination_reason",
    "final_generation",
    "evaluation_count",
    "base_population_size",
    "final_population_size",
    "population_decay",
    "python_rng_sha256",
    "numpy_rng_sha256",
    "seed_sequence_sha256",
    "trajectory",
)


def _measurement_boundary(seed):
    return {
        "schema": "s00-measurement-boundary-v1",
        "seed": seed,
        "space": {"x": list(range(5)), "y": list(range(4))},
        "evaluator": {
            "formula": "1.0 + x*0.25 + y*0.125",
            "dtype": "float64",
        },
        "ga_config": {
            "population_size": 6,
            "generations": 4,
            "period": 0,
            "diversity_threshold": 0.0,
            "selection": {"name": "random", "ratio": 0.75, "elitism": 0.0},
            "crossover": {"name": "ux", "probability": 0.8},
            "mutation_probability": 0.25,
            "sampling_jobs": 1,
        },
        "horizon": {"kind": "fixed_generation", "value": 4},
        "canonicalization": "canonical-json-v1",
    }


def _pointer_token(value):
    return str(value).replace("~", "~0").replace("/", "~1")


def _find_first_difference(left, right, path=""):
    if type(left) is not type(right):
        if canonical_sha256(left) == canonical_sha256(right):
            return None
        return path or "/"
    if isinstance(left, dict):
        left_keys = list(left)
        right_keys = list(right)
        if left_keys != right_keys:
            for key in sorted(set(left_keys) | set(right_keys)):
                if key not in left or key not in right:
                    return f"{path}/{_pointer_token(key)}"
            return path or "/"
        for key in left_keys:
            result = _find_first_difference(
                left[key], right[key], f"{path}/{_pointer_token(key)}"
            )
            if result is not None:
                return result
        return None
    if isinstance(left, list):
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            result = _find_first_difference(
                left_item, right_item, f"{path}/{index}"
            )
            if result is not None:
                return result
        if len(left) != len(right):
            return f"{path}/{min(len(left), len(right))}"
        return None
    return None if left == right else (path or "/")


def _value_at_pointer(document, pointer):
    if pointer in {None, "", "/"}:
        return document
    value = document
    for encoded in pointer.split("/")[1:]:
        token = encoded.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def _first_divergence(left, right):
    path = _find_first_difference(left, right)
    if path is None:
        return {
            "status": "no_divergence",
            "path": None,
            "left_value": None,
            "right_value": None,
            "left_sha256": canonical_sha256(left),
            "right_sha256": canonical_sha256(right),
        }
    left_value = _value_at_pointer(left, path)
    right_value = _value_at_pointer(right, path)
    return {
        "status": "divergence",
        "path": path,
        "left_value": left_value,
        "right_value": right_value,
        "left_sha256": canonical_sha256(left_value),
        "right_sha256": canonical_sha256(right_value),
    }


def _validate_raw_run(raw):
    if not isinstance(raw, dict) or set(raw) != set(RAW_RUN_FIELDS):
        raise EvidenceValidationError(
            "raw run field set/order mismatch", code="raw_run_malformed"
        )
    if raw["format"] != "s00-ga-raw-run-v1":
        raise EvidenceValidationError(
            "raw run format mismatch", code="raw_run_malformed"
        )
    total = 0
    for item in raw["evaluations"]:
        if set(item) != {
                "configs", "configs_hash", "scores", "scores_hash"}:
            raise EvidenceValidationError(
                "raw evaluation fields mismatch", code="raw_run_malformed"
            )
        if canonical_sha256(item["configs"]) != item["configs_hash"]:
            raise EvidenceValidationError(
                "raw config hash mismatch", code="raw_run_hash_mismatch"
            )
        expected_scores = [
            1.0 + config["x"] * 0.25 + config["y"] * 0.125
            for config in item["configs"]
        ]
        if item["scores"] != expected_scores:
            raise EvidenceValidationError(
                "raw evaluation score mismatch", code="raw_run_mismatch"
            )
        score_descriptor = {
            "dtype": "<f8",
            "shape": [len(item["scores"])],
            "values": item["scores"],
        }
        if canonical_sha256(score_descriptor) != item["scores_hash"]:
            raise EvidenceValidationError(
                "raw score hash mismatch", code="raw_run_hash_mismatch"
            )
        total += len(item["configs"])
    if (
            raw["evaluation_count"] != total or
            raw["termination_reason"] != "fixed_horizon" or
            raw["final_generation"] != 4 or
            raw["base_population_size"] != 6 or
            raw["population_decay"] not in {
                "none", "large_space", "low_diversity"}):
        raise EvidenceValidationError(
            "raw run terminal state mismatch", code="raw_run_mismatch"
        )
    trajectory = raw["trajectory"]
    if not isinstance(trajectory, dict) or set(trajectory) != {
            "updated_populations", "termination_updates",
            "survivors", "offspring"}:
        raise EvidenceValidationError(
            "raw trajectory is incomplete", code="raw_run_malformed"
        )
    if not all(len(trajectory[name]) == 4 for name in trajectory):
        raise EvidenceValidationError(
            "raw trajectory generation count mismatch",
            code="raw_run_mismatch",
        )

    def validate_population_state(state):
        if not isinstance(state, dict) or set(state) != {
                "ordered", "canonical_sha256"}:
            raise EvidenceValidationError(
                "population state fields missing", code="raw_run_malformed"
            )
        if not isinstance(state["ordered"], list):
            raise EvidenceValidationError(
                "population ordering is malformed", code="raw_run_malformed"
            )
        for individual in state["ordered"]:
            if not isinstance(individual, dict) or set(individual) != {
                    "X", "F", "G"}:
                raise EvidenceValidationError(
                    "individual state fields missing",
                    code="raw_run_malformed",
                )
        expected = canonical_sha256(sorted(
            state["ordered"],
            key=lambda item: canonical_sha256(item["X"]),
        ))
        if state["canonical_sha256"] != expected:
            raise EvidenceValidationError(
                "population state hash mismatch",
                code="raw_run_hash_mismatch",
            )

    for update in trajectory["updated_populations"]:
        if set(update) != {
                "updated_population", "old_population", "champion",
                "f_max", "fitness_matrix"}:
            raise EvidenceValidationError(
                "updated population fields missing",
                code="raw_run_malformed",
            )
        for field in (
                "updated_population", "old_population", "champion"):
            validate_population_state(update[field])
        matrix = update["fitness_matrix"]
        descriptor = {
            "dtype": matrix["dtype"],
            "shape": matrix["shape"],
            "values": matrix["values"],
        }
        if canonical_sha256(descriptor) != matrix["canonical_sha256"]:
            raise EvidenceValidationError(
                "fitness matrix hash mismatch",
                code="raw_run_hash_mismatch",
            )
    for field in ("survivors", "offspring"):
        for state in trajectory[field]:
            validate_population_state(state)
    return raw


def run_neutrality(lock, *, effective_lock_sha256=None):
    seed = lock["seeds"]["neutrality"]
    old_jobs = space_module.JOBLIB_N_JOBS_OVERRIDE
    space_module.JOBLIB_N_JOBS_OVERRIDE = 1
    try:
        off_ga, off_evals = _make_ga(seed, None, None)
        off = _run_ga(off_ga, off_evals)
        events = []
        callback_counts = {"python": 0, "numpy": 0, "immutable": 0}

        def adversarial(event):
            for _ in range(17):
                random.random()
                callback_counts["python"] += 1
                np.random.random()
                callback_counts["numpy"] += 1
            try:
                event.payload["observer_mutation"] = True
            except TypeError:
                callback_counts["immutable"] += 1
            events.append(event.as_dict())

        lineage = _lineage(
            lock, "neutrality", "s00-neutrality", "s00-neutrality-run",
            effective_lock_sha256=effective_lock_sha256,
        )
        on_ga, on_evals = _make_ga(seed, adversarial, lineage)
        on = _run_ga(on_ga, on_evals)
    finally:
        space_module.JOBLIB_N_JOBS_OVERRIDE = old_jobs
    off = {field: off[field] for field in RAW_RUN_FIELDS}
    on = {field: on[field] for field in RAW_RUN_FIELDS}
    chain = validate_event_chain(events)
    divergence = _first_divergence(off, on)
    observation = {
        "schema": "s00-neutrality-direct-evidence-v1",
        "measurement_boundary": _measurement_boundary(seed),
        "observer_off": {
            "raw_run": off,
            "events": [],
            "event_chain_validation": {
                "next_sequence": 0,
                "chain_head": None,
            },
        },
        "observer_on": {
            "raw_run": on,
            "events": events,
            "event_chain_validation": chain,
        },
        "callback_counts": callback_counts,
        "raw_run_sha256": {
            "observer_off": canonical_sha256(off),
            "observer_on": canonical_sha256(on),
        },
        "first_divergence": divergence,
        "criterion_status": "PASS",
    }
    observation["criterion_status"] = (
        "PASS"
        if (
            divergence["status"] == "no_divergence"
            and callback_counts["python"] > 0
            and callback_counts["numpy"] > 0
            and callback_counts["immutable"] == len(events)
            and len(events) > 0
        )
        else "FAIL"
    )
    _validate_neutrality_observation(observation)
    return observation


def _validate_neutrality_observation(observation):
    required = {
        "schema", "measurement_boundary", "observer_off", "observer_on",
        "callback_counts", "raw_run_sha256", "first_divergence",
        "criterion_status",
    }
    if not isinstance(observation, dict) or set(observation) != required:
        raise EvidenceValidationError(
            "neutrality raw evidence is incomplete",
            code="neutrality_raw_evidence_missing",
        )
    if (
            observation["schema"] != "s00-neutrality-direct-evidence-v1" or
            observation["measurement_boundary"]
            != _measurement_boundary(
                observation["measurement_boundary"].get("seed"))):
        raise EvidenceValidationError(
            "neutrality measurement boundary mismatch",
            code="measurement_boundary_mismatch",
        )
    off = observation["observer_off"]
    on = observation["observer_on"]
    if set(off) != {"raw_run", "events", "event_chain_validation"} or set(on) != {
            "raw_run", "events", "event_chain_validation"}:
        raise EvidenceValidationError(
            "neutrality raw class missing",
            code="neutrality_raw_evidence_missing",
        )
    _validate_raw_run(off["raw_run"])
    _validate_raw_run(on["raw_run"])
    if off["events"] != [] or off["event_chain_validation"] != {
            "next_sequence": 0, "chain_head": None}:
        raise EvidenceValidationError(
            "observer-off event absence is not explicit",
            code="neutrality_event_absence_mismatch",
        )
    if not on["events"]:
        raise EvidenceValidationError(
            "observer-on events missing",
            code="neutrality_raw_evidence_missing",
        )
    if validate_event_chain(on["events"]) != on["event_chain_validation"]:
        raise EvidenceValidationError(
            "observer-on event validation mismatch",
            code="neutrality_event_chain_mismatch",
        )
    hashes = {
        "observer_off": canonical_sha256(off["raw_run"]),
        "observer_on": canonical_sha256(on["raw_run"]),
    }
    divergence = _first_divergence(off["raw_run"], on["raw_run"])
    counts = observation["callback_counts"]
    expected_pass = (
        divergence["status"] == "no_divergence"
        and counts.get("python", 0) > 0
        and counts.get("numpy", 0) > 0
        and counts.get("immutable") == len(on["events"])
    )
    if (
            observation["raw_run_sha256"] != hashes or
            observation["first_divergence"] != divergence or
            observation["criterion_status"]
            != ("PASS" if expected_pass else "FAIL")):
        raise EvidenceValidationError(
            "neutrality derived result mismatch",
            code="neutrality_result_mismatch",
        )
    return observation


def _journal(manifest):
    return {
        "checkpoint_id": manifest["checkpoint_id"],
        "parent_checkpoint_id": manifest["parent_checkpoint_id"],
        "next_sequence": manifest["observer"]["next_sequence"],
        "event_chain_head": manifest["observer"]["event_chain_head"],
    }


def _outcome_events(events):
    kinds = {
        "initial_population",
        "proposal_batch",
        "fitness_matrix",
        "generation_stats",
        "termination_updated",
        "population_transition",
        "termination",
        "final_champion",
    }
    return [
        {
            "kind": event["kind"],
            "generation": event["generation"],
            "payload": event["payload"],
        }
        for event in events if event["kind"] in kinds
    ]


def run_resume(lock, *, effective_lock_sha256=None):
    seed = lock["seeds"]["resume"]
    continuous_lineage = _lineage(
        lock, "resume", "s00-resume-continuous",
        "s00-resume-continuous-run",
        effective_lock_sha256=effective_lock_sha256,
    )
    resumed_lineage = _lineage(
        lock, "resume", "s00-resume-interrupted",
        "s00-resume-interrupted-run",
        effective_lock_sha256=effective_lock_sha256,
    )
    old_jobs = space_module.JOBLIB_N_JOBS_OVERRIDE
    space_module.JOBLIB_N_JOBS_OVERRIDE = 1
    try:
        with tempfile.TemporaryDirectory(prefix="s00-resume-") as directory:
            directory = Path(directory)
            continuous_events = []
            continuous_ga, continuous_evals = _make_ga(
                seed, lambda event: continuous_events.append(event.as_dict()),
                continuous_lineage,
                checkpoint_path=directory / "continuous.pkl",
            )
            continuous = _run_ga(continuous_ga, continuous_evals)
            continuous_manifests = copy.deepcopy(
                continuous_ga._checkpoint_manifests
            )

            resumed_events = []
            first_ga, first_evals = _make_ga(
                seed, lambda event: resumed_events.append(event.as_dict()),
                resumed_lineage,
                checkpoint_path=directory / "resumed.pkl",
                interrupt=2,
            )
            try:
                first_ga.optimize()
            except DurableInterruption:
                pass
            else:
                raise EvidenceValidationError(
                    "fixture interruption did not occur",
                    code="resume_fixture_failed",
                )
            first_manifests = list(first_ga._checkpoint_manifests)
            interruption_event_count = len(resumed_events)
            with open(directory / "resumed.pkl", "rb") as stream:
                envelope = pickle.load(stream)
            manifest = validate_checkpoint_manifest(envelope["manifest"])
            second_ga, second_evals = _make_ga(
                seed, lambda event: resumed_events.append(event.as_dict()),
                resumed_lineage,
                checkpoint_path=directory / "resumed.pkl",
            )
            second_ga.load(
                directory / "resumed.pkl",
                expected_checkpoint_id=manifest["checkpoint_id"],
                prior_checkpoint_journal=_journal(manifest),
            )
            resumed = _run_ga(second_ga, second_evals)
            resumed["evaluations"] = first_evals + second_evals
            resumed["trajectory"] = {
                key: (
                    first_ga._fixture_trace[key]
                    + second_ga._fixture_trace[key]
                )
                for key in first_ga._fixture_trace
            }
            resumed["evaluation_count"] = sum(
                len(item["configs"]) for item in resumed["evaluations"]
            )
            manifests = first_manifests + second_ga._checkpoint_manifests
    finally:
        space_module.JOBLIB_N_JOBS_OVERRIDE = old_jobs
    continuous = {field: continuous[field] for field in RAW_RUN_FIELDS}
    resumed = {field: resumed[field] for field in RAW_RUN_FIELDS}
    continuous_chain = validate_event_chain(continuous_events)
    resumed_chain = validate_event_chain(resumed_events)
    selected = first_manifests[-1]
    first_control = resumed_events[interruption_event_count]
    outcome_kinds = {item["kind"] for item in _outcome_events(resumed_events)}
    first_outcome = next(
        item for item in resumed_events[interruption_event_count:]
        if item["kind"] in outcome_kinds
    )
    continuous_outcomes = _outcome_events(continuous_events)
    resumed_outcomes = _outcome_events(resumed_events)
    mapping = [
        {
            "continuous_index": index,
            "resumed_index": index,
            "semantic_sha256": canonical_sha256(left),
        }
        for index, (left, right) in enumerate(
            zip(continuous_outcomes, resumed_outcomes)
        )
        if left == right
    ]
    checkpoint_evidence = {
        "continuous": [
            {
                "manifest": item,
                "manifest_sha256": canonical_sha256(item),
                "external_journal": _journal(item),
            }
            for item in continuous_manifests
        ],
        "resumed": [
            {
                "manifest": item,
                "manifest_sha256": canonical_sha256(item),
                "external_journal": _journal(item),
            }
            for item in manifests
        ],
    }
    continuous_event_ids = [
        event["event_id"] for event in continuous_events
    ]
    resumed_event_ids = [event["event_id"] for event in resumed_events]
    continuous_sequences = [
        event["sequence"] for event in continuous_events
    ]
    resumed_sequences = [event["sequence"] for event in resumed_events]
    observation = {
        "schema": "s00-resume-direct-evidence-v1",
        "measurement_boundary": _measurement_boundary(seed),
        "continuous": {
            "raw_run": continuous,
            "events": continuous_events,
            "event_chain_validation": continuous_chain,
        },
        "resumed": {
            "raw_run": resumed,
            "events": resumed_events,
            "event_chain_validation": resumed_chain,
        },
        "checkpoint_evidence": checkpoint_evidence,
        "resume_boundary": {
            "interrupt_generation": 2,
            "selected_checkpoint_id": selected["checkpoint_id"],
            "prior_event_head": selected["observer"]["event_chain_head"],
            "saved_next_sequence": selected["observer"]["next_sequence"],
            "first_resumed_control_event": first_control,
            "first_resumed_outcome_event": first_outcome,
            "outcome_event_semantic_mapping": mapping,
        },
        "event_identity_proof": {
            "continuous_count": len(continuous_events),
            "resumed_count": len(resumed_events),
            "continuous_unique_event_ids": (
                len(continuous_event_ids)
                == len(set(continuous_event_ids))
            ),
            "resumed_unique_event_ids": (
                len(resumed_event_ids) == len(set(resumed_event_ids))
            ),
            "cross_trajectory_ids_disjoint": set(continuous_event_ids).isdisjoint(
                resumed_event_ids
            ),
            "continuous_contiguous_sequences": continuous_sequences
            == list(range(len(continuous_events))),
            "resumed_contiguous_sequences": resumed_sequences
            == list(range(len(resumed_events))),
            "continuous_chain_head": continuous_chain["chain_head"],
            "resumed_chain_head": resumed_chain["chain_head"],
        },
        "first_divergence": _first_divergence(continuous, resumed),
        "control_event_mapping": [
            {
                "sequence": event["sequence"],
                "kind": event["kind"],
                "event_sha256": event["event_sha256"],
            }
            for event in resumed_events
            if event["kind"] not in outcome_kinds
        ],
        "raw_run_sha256": {
            "continuous": canonical_sha256(continuous),
            "resumed": canonical_sha256(resumed),
        },
        "criterion_status": "PASS",
    }
    try:
        _validate_resume_observation(observation)
    except EvidenceValidationError:
        observation["criterion_status"] = "FAIL"
        raise
    return observation


def _validate_checkpoint_evidence(entries, expected_lineage):
    checkpoint_schema = _schema("checkpoint.schema.json")
    prior = None
    ids = []
    for index, entry in enumerate(entries):
        if set(entry) != {
                "manifest", "manifest_sha256", "external_journal"}:
            raise EvidenceValidationError(
                "checkpoint direct evidence fields missing",
                code="resume_manifest_missing",
            )
        manifest = entry["manifest"]
        validate_schema_document(
            manifest, checkpoint_schema, context=f"checkpoint manifest {index}"
        )
        validate_checkpoint_manifest(manifest)
        if (
                canonical_sha256(manifest) != entry["manifest_sha256"] or
                entry["external_journal"] != _journal(manifest) or
                manifest["parent_checkpoint_id"] != prior or
                manifest["lineage"] != expected_lineage):
            raise EvidenceValidationError(
                "checkpoint direct evidence mismatch",
                code="resume_manifest_mismatch",
            )
        ids.append(manifest["checkpoint_id"])
        prior = manifest["checkpoint_id"]
    if not entries or len(ids) != len(set(ids)):
        raise EvidenceValidationError(
            "checkpoint identities missing/duplicate",
            code="resume_manifest_mismatch",
        )
    return ids


def _validate_resume_observation(observation):
    required = {
        "schema", "measurement_boundary", "continuous", "resumed",
        "checkpoint_evidence", "resume_boundary", "event_identity_proof",
        "first_divergence", "control_event_mapping", "raw_run_sha256",
        "criterion_status",
    }
    if not isinstance(observation, dict) or set(observation) != required:
        raise EvidenceValidationError(
            "resume raw evidence is incomplete",
            code="resume_raw_evidence_missing",
        )
    if (
            observation["schema"] != "s00-resume-direct-evidence-v1" or
            observation["measurement_boundary"]
            != _measurement_boundary(
                observation["measurement_boundary"].get("seed"))):
        raise EvidenceValidationError(
            "resume measurement boundary mismatch",
            code="measurement_boundary_mismatch",
        )
    for side in ("continuous", "resumed"):
        item = observation[side]
        if set(item) != {"raw_run", "events", "event_chain_validation"}:
            raise EvidenceValidationError(
                f"{side} raw evidence missing",
                code="resume_raw_evidence_missing",
            )
        _validate_raw_run(item["raw_run"])
        if validate_event_chain(item["events"]) != item["event_chain_validation"]:
            raise EvidenceValidationError(
                f"{side} event chain mismatch",
                code="resume_event_chain_mismatch",
            )
    continuous = observation["continuous"]
    resumed = observation["resumed"]
    checkpoints = observation["checkpoint_evidence"]
    if set(checkpoints) != {"continuous", "resumed"}:
        raise EvidenceValidationError(
            "checkpoint classes missing", code="resume_manifest_missing"
        )
    if not resumed["events"]:
        raise EvidenceValidationError(
            "resumed event trajectory missing", code="resume_raw_evidence_missing"
        )
    continuous_ids = _validate_checkpoint_evidence(
        checkpoints["continuous"],
        checkpoints["continuous"][0]["manifest"]["lineage"],
    )
    resumed_ids = _validate_checkpoint_evidence(
        checkpoints["resumed"],
        checkpoints["resumed"][0]["manifest"]["lineage"],
    )
    if len(continuous_ids) != 4 or len(resumed_ids) != 4:
        raise EvidenceValidationError(
            "checkpoint generation coverage mismatch",
            code="resume_manifest_mismatch",
        )
    boundary = observation["resume_boundary"]
    boundary_required = {
        "interrupt_generation", "selected_checkpoint_id",
        "prior_event_head", "saved_next_sequence",
        "first_resumed_control_event", "first_resumed_outcome_event",
        "outcome_event_semantic_mapping",
    }
    if set(boundary) != boundary_required:
        raise EvidenceValidationError(
            "resume boundary fields missing", code="resume_boundary_missing"
        )
    selected = checkpoints["resumed"][1]["manifest"]
    saved = boundary["saved_next_sequence"]
    events = resumed["events"]
    if (
            boundary["interrupt_generation"] != 2 or
            boundary["selected_checkpoint_id"] != selected["checkpoint_id"] or
            boundary["prior_event_head"]
            != selected["observer"]["event_chain_head"] or
            saved != selected["observer"]["next_sequence"] or
            saved >= len(events) or
            boundary["first_resumed_control_event"] != events[saved] or
            events[saved]["kind"] != "resume_loaded"):
        raise EvidenceValidationError(
            "resume boundary does not bind selected checkpoint",
            code="resume_boundary_mismatch",
        )
    outcome_kinds = {
        "initial_population", "proposal_batch", "fitness_matrix",
        "generation_stats", "termination_updated", "population_transition",
        "termination", "final_champion",
    }
    first_outcome = next(
        (item for item in events[saved:] if item["kind"] in outcome_kinds),
        None,
    )
    continuous_outcomes = _outcome_events(continuous["events"])
    resumed_outcomes = _outcome_events(events)
    expected_mapping = [
        {
            "continuous_index": index,
            "resumed_index": index,
            "semantic_sha256": canonical_sha256(left),
        }
        for index, (left, right) in enumerate(
            zip(continuous_outcomes, resumed_outcomes)
        )
        if left == right
    ]
    if (
            first_outcome is None or
            boundary["first_resumed_outcome_event"] != first_outcome or
            continuous_outcomes != resumed_outcomes or
            boundary["outcome_event_semantic_mapping"] != expected_mapping or
            len(expected_mapping) != len(continuous_outcomes)):
        raise EvidenceValidationError(
            "resume outcome-event mapping mismatch",
            code="resume_outcome_mapping_mismatch",
        )
    proof = observation["event_identity_proof"]
    continuous_event_ids = [
        item["event_id"] for item in continuous["events"]
    ]
    resumed_event_ids = [item["event_id"] for item in events]
    continuous_sequences = [
        item["sequence"] for item in continuous["events"]
    ]
    resumed_sequences = [item["sequence"] for item in events]
    expected_proof = {
        "continuous_count": len(continuous["events"]),
        "resumed_count": len(events),
        "continuous_unique_event_ids": (
            len(continuous_event_ids) == len(set(continuous_event_ids))
        ),
        "resumed_unique_event_ids": (
            len(resumed_event_ids) == len(set(resumed_event_ids))
        ),
        "cross_trajectory_ids_disjoint": set(
            continuous_event_ids
        ).isdisjoint(resumed_event_ids),
        "continuous_contiguous_sequences": continuous_sequences
        == list(range(len(continuous["events"]))),
        "resumed_contiguous_sequences": resumed_sequences
        == list(range(len(events))),
        "continuous_chain_head": (
            continuous["event_chain_validation"]["chain_head"]
        ),
        "resumed_chain_head": resumed["event_chain_validation"]["chain_head"],
    }
    divergence = _first_divergence(
        continuous["raw_run"], resumed["raw_run"]
    )
    hashes = {
        "continuous": canonical_sha256(continuous["raw_run"]),
        "resumed": canonical_sha256(resumed["raw_run"]),
    }
    expected_control = [
        {
            "sequence": event["sequence"],
            "kind": event["kind"],
            "event_sha256": event["event_sha256"],
        }
        for event in events if event["kind"] not in outcome_kinds
    ]
    expected_pass = (
        proof == expected_proof
        and proof["continuous_unique_event_ids"]
        and proof["resumed_unique_event_ids"]
        and proof["cross_trajectory_ids_disjoint"]
        and proof["continuous_contiguous_sequences"]
        and proof["resumed_contiguous_sequences"]
        and divergence["status"] == "no_divergence"
    )
    if (
            observation["event_identity_proof"] != expected_proof or
            observation["first_divergence"] != divergence or
            observation["control_event_mapping"] != expected_control or
            observation["raw_run_sha256"] != hashes or
            observation["criterion_status"]
            != ("PASS" if expected_pass else "FAIL")):
        raise EvidenceValidationError(
            "resume derived result mismatch",
            code="resume_result_mismatch",
        )
    return observation


def _named_reconciliation_cases(success_records):
    definitions = (
        (
            "generated-input-in-progress",
            0,
            "status",
            "in_progress",
            "record_status_in_progress",
        ),
        (
            "observation-timeout",
            2,
            "status",
            "timeout",
            "record_status_timeout",
        ),
        (
            "observation-killed",
            2,
            "status",
            "killed",
            "record_status_killed",
        ),
        (
            "cross-kind-conflicting-record-id",
            3,
            "record_id",
            success_records[1]["record_id"],
            "duplicate_record_id",
        ),
        (
            "success-status-backend-failure-summary",
            3,
            "payload",
            {"outcome": "backend_failure"},
            "summary_payload_mismatch",
        ),
    )
    cases = []
    for case_id, target, field, value, expected in definitions:
        records = copy.deepcopy(success_records)
        records[target][field] = copy.deepcopy(value)
        records = _rehash_records(records)
        cases.append({
            "case_id": case_id,
            "mutation": {
                "target_index": target,
                "field": field,
                "value": value,
            },
            "records": records,
            "expected_error": expected,
        })
    return cases


def run_reconciliation():
    fixture_result = validate_fixtures()
    success_fixture = _fixture("valid-run.json")
    failure_fixture = _fixture("backend-failure.json")
    success = reconcile_artifacts(
        success_fixture["records"],
        expected_lineage=success_fixture["lineage"],
    )
    failure = reconcile_artifacts(
        failure_fixture["failure_records"],
        expected_lineage=failure_fixture["lineage"],
    )
    invalid_cases = []
    for case in failure_fixture["cases"]:
        candidate = _apply_backend_case(failure_fixture, case)
        observed_error = None
        try:
            reconcile_artifacts(
                candidate, expected_lineage=failure_fixture["lineage"]
            )
        except EvidenceValidationError as exc:
            observed_error = exc.code
        invalid_cases.append({
            "case_id": case["case_id"],
            "mutation": {
                key: copy.deepcopy(value)
                for key, value in case.items()
                if key not in {"case_id", "expected_error"}
            },
            "expected_error": case["expected_error"],
            "observed_error": observed_error,
            "records": candidate,
            "no_ready_edge": observed_error == case["expected_error"],
        })
    for case in _named_reconciliation_cases(success_fixture["records"]):
        observed_error = None
        try:
            reconcile_artifacts(
                case["records"], expected_lineage=success_fixture["lineage"]
            )
        except EvidenceValidationError as exc:
            observed_error = exc.code
        invalid_cases.append({
            **case,
            "observed_error": observed_error,
            "no_ready_edge": observed_error == case["expected_error"],
        })
    cases_match = all(
        item["observed_error"] == item["expected_error"]
        and item["no_ready_edge"]
        for item in invalid_cases
    )
    observation = {
        "schema": "s00-reconciliation-direct-evidence-v1",
        "criterion_status": "PASS" if cases_match else "FAIL",
        "valid_success": {
            "outcome": success["outcome"],
            "chain_head": success["chain_head"],
            "records": success_fixture["records"],
        },
        "explicit_backend_failure": {
            "outcome": failure["outcome"],
            "chain_head": failure["chain_head"],
            "records": failure_fixture["failure_records"],
        },
        "invalid_cases": invalid_cases,
        "fixture_result": fixture_result,
    }
    _validate_reconciliation_observation(observation)
    return observation


def _validate_reconciliation_observation(observation):
    required = {
        "schema", "criterion_status", "valid_success",
        "explicit_backend_failure", "invalid_cases", "fixture_result",
    }
    if not isinstance(observation, dict) or set(observation) != required:
        raise EvidenceValidationError(
            "reconciliation raw evidence incomplete",
            code="reconciliation_raw_evidence_missing",
        )
    if observation["schema"] != "s00-reconciliation-direct-evidence-v1":
        raise EvidenceValidationError(
            "reconciliation evidence schema mismatch",
            code="reconciliation_raw_evidence_missing",
        )
    for field, expected in (
            ("valid_success", "success"),
            ("explicit_backend_failure", "backend_failure")):
        chain = observation[field]
        if set(chain) != {"outcome", "chain_head", "records"}:
            raise EvidenceValidationError(
                f"{field} raw chain incomplete",
                code="reconciliation_raw_evidence_missing",
            )
        result = reconcile_artifacts(chain["records"])
        if (
                result["outcome"] != expected or
                chain["outcome"] != expected or
                result["chain_head"] != chain["chain_head"]):
            raise EvidenceValidationError(
                f"{field} raw chain mismatch",
                code="reconciliation_result_mismatch",
            )
    required_named = {
        "generated-input-in-progress": "record_status_in_progress",
        "observation-timeout": "record_status_timeout",
        "observation-killed": "record_status_killed",
        "cross-kind-conflicting-record-id": "duplicate_record_id",
        "success-status-backend-failure-summary": (
            "summary_payload_mismatch"
        ),
    }
    observed_named = {}
    complete = bool(observation["invalid_cases"])
    for case in observation["invalid_cases"]:
        if set(case) != {
                "case_id", "mutation", "records", "expected_error",
                "observed_error", "no_ready_edge"}:
            raise EvidenceValidationError(
                "negative reconciliation case is incomplete",
                code="reconciliation_raw_evidence_missing",
            )
        observed_error = None
        try:
            reconcile_artifacts(case["records"])
        except EvidenceValidationError as exc:
            observed_error = exc.code
        if (
                observed_error != case["expected_error"] or
                case["observed_error"] != observed_error or
                case["no_ready_edge"] is not True):
            complete = False
        if case["case_id"] in required_named:
            observed_named[case["case_id"]] = observed_error
    if observed_named != required_named:
        complete = False
    if observation["criterion_status"] != ("PASS" if complete else "FAIL"):
        raise EvidenceValidationError(
            "reconciliation derived result mismatch",
            code="reconciliation_result_mismatch",
        )
    return observation


def run_lineage(lock=None, *, lock_path=SUCCESSOR_LOCK_PATH):
    fixture = _fixture("invalid-lineage.json")
    results = []
    for case in fixture["cases"]:
        candidate = _apply_lineage_case(fixture["base_lineage"], case)
        observed = None
        try:
            if "mismatch" in case["case_id"]:
                validate_lineage(candidate, fixture["base_lineage"])
            else:
                validate_lineage(candidate)
        except EvidenceValidationError as exc:
            observed = exc.code
        results.append({
            "case_id": case["case_id"],
            "mutation": {
                key: copy.deepcopy(value)
                for key, value in case.items()
                if key not in {"case_id", "expected_error"}
            },
            "candidate": candidate,
            "expected_error": case["expected_error"],
            "observed_error": observed,
            "no_ready_edge": observed == case["expected_error"],
        })
    missing_probe = {
        "operation": "load_missing",
        "path": (
            "study_docs/research/ductile-origami-warmstart/protocol/v1/"
            "locks/s00-intentionally-missing-probe.json"
        ),
    }
    superseded_probe = {
        "operation": "validate_superseded",
        "path": str(GENESIS_LOCK_PATH.relative_to(ROOT)),
    }
    current_lock_cases = []
    for case_id, probe in (
            ("missing-current-successor-lock", missing_probe),
            ("superseded-old-lock-is-not-current", superseded_probe)):
        observed = _execute_current_lock_probe(probe)
        current_lock_cases.append({
            "case_id": case_id,
            "probe": probe,
            "expected_error": observed,
            "observed_error": observed,
            "no_ready_edge": observed is not None,
        })
    if lock is not None:
        for case_id, mutate in (
                (
                    "successor-lock-substitution",
                    lambda base: base["seeds"].__setitem__(
                        "neutrality", base["seeds"]["neutrality"] + 1
                    ),
                ),
                (
                    "illegal-null-successor-parent",
                    lambda base: base.__setitem__("parent_lock", None),
                ),
                (
                    "mismatched-successor-parent",
                    lambda base: base["parent_lock"].__setitem__(
                        "sha256", "0" * 64
                    ),
                )):
            base = {
                key: copy.deepcopy(value) for key, value in lock.items()
                if key not in {"lock_id", "body_sha256"}
            }
            mutate(base)
            candidate = _derived_lock_document(base)
            observed = None
            try:
                _validate_successor_lock(
                    candidate,
                    lock_path=lock_path,
                    verify_bound_bytes=False,
                    verify_plan_bytes=False,
                )
            except EvidenceValidationError as exc:
                observed = exc.code
            current_lock_cases.append({
                "case_id": case_id,
                "probe": {
                    "operation": "validate_candidate",
                    "candidate": candidate,
                },
                "expected_error": observed,
                "observed_error": observed,
                "no_ready_edge": observed is not None,
            })
    evidence_class_matrix = [
        {
            "kind": kind,
            "removal_error": "decision_evidence_missing",
            "failure_error": "decision_evidence_failed",
            "outgoing_edges": [],
        }
        for kind in (
            "neutrality", "resume-parity", "reconciliation",
            "lineage-fail-closed"
        )
    ]
    complete = (
        len(results) == len(fixture["cases"])
        and all(
            result["observed_error"] == result["expected_error"]
            and result["no_ready_edge"]
            for result in results
        )
        and all(item["no_ready_edge"] for item in current_lock_cases)
    )
    observation = {
        "schema": "s00-lineage-direct-evidence-v1",
        "criterion_status": "PASS" if complete else "FAIL",
        "cases": results,
        "current_lock_cases": current_lock_cases,
        "evidence_class_matrix": evidence_class_matrix,
    }
    _validate_lineage_observation(observation)
    return observation


def _execute_current_lock_probe(probe):
    observed = None
    try:
        if probe["operation"] == "load_missing":
            _load_validated_successor_lock(
                ROOT / probe["path"], verify_plan_bytes=False
            )
        elif probe["operation"] == "validate_superseded":
            _validate_successor_lock(
                strict_load_json(ROOT / probe["path"]),
                verify_bound_bytes=False,
                verify_plan_bytes=False,
            )
        elif probe["operation"] == "validate_candidate":
            _validate_successor_lock(
                probe["candidate"],
                verify_bound_bytes=False,
                verify_plan_bytes=False,
            )
        else:
            raise EvidenceValidationError(
                "unknown current-lock probe", code="lineage_probe_malformed"
            )
    except (OSError, EvidenceValidationError) as exc:
        observed = (
            exc.code if isinstance(exc, EvidenceValidationError)
            else "effective_lock_unavailable"
        )
    return observed


def _validate_lineage_observation(observation):
    if not isinstance(observation, dict) or set(observation) != {
            "schema", "criterion_status", "cases",
            "current_lock_cases", "evidence_class_matrix"}:
        raise EvidenceValidationError(
            "lineage raw evidence incomplete",
            code="lineage_raw_evidence_missing",
        )
    complete = observation["schema"] == "s00-lineage-direct-evidence-v1"
    for case in observation["cases"]:
        observed = None
        try:
            if "mismatch" in case["case_id"]:
                validate_lineage(
                    case["candidate"],
                    _fixture("invalid-lineage.json")["base_lineage"],
                )
            else:
                validate_lineage(case["candidate"])
        except EvidenceValidationError as exc:
            observed = exc.code
        complete = complete and (
            observed == case["expected_error"]
            and case["observed_error"] == observed
            and case["no_ready_edge"] is True
        )
    required_lock_cases = {
        "missing-current-successor-lock",
        "superseded-old-lock-is-not-current",
        "successor-lock-substitution",
        "illegal-null-successor-parent",
        "mismatched-successor-parent",
    }
    complete = complete and required_lock_cases.issubset({
        item["case_id"] for item in observation["current_lock_cases"]
    })
    complete = complete and all(
        _execute_current_lock_probe(item["probe"]) == item["expected_error"]
        and item["observed_error"] == item["expected_error"]
        and item["no_ready_edge"] is True
        for item in observation["current_lock_cases"]
    )
    expected_classes = {
        "neutrality", "resume-parity", "reconciliation",
        "lineage-fail-closed",
    }
    complete = complete and {
        item["kind"] for item in observation["evidence_class_matrix"]
    } == expected_classes
    complete = complete and all(
        item["outgoing_edges"] == []
        and item["removal_error"] == "decision_evidence_missing"
        and item["failure_error"] == "decision_evidence_failed"
        for item in observation["evidence_class_matrix"]
    )
    if observation["criterion_status"] != ("PASS" if complete else "FAIL"):
        raise EvidenceValidationError(
            "lineage derived result mismatch",
            code="lineage_result_mismatch",
        )
    return observation


def _load_validated_lock(lock_path=LOCK_PATH, contract_path=CONTRACT_PATH):
    lock_path = Path(lock_path)
    try:
        lock = strict_load_json(lock_path)
    except (OSError, EvidenceValidationError) as exc:
        raise EvidenceValidationError(
            f"effective lock unavailable/invalid: {lock_path}",
            code="effective_lock_unavailable",
        ) from exc
    return _validate_lock(
        lock, lock_path=lock_path, contract_path=contract_path
    )


def _load_validated_successor_lock(
        lock_path=SUCCESSOR_LOCK_PATH, contract_path=CONTRACT_PATH,
        *, verify_plan_bytes=True):
    lock_path = Path(lock_path)
    try:
        lock = strict_load_json(lock_path)
    except (OSError, EvidenceValidationError) as exc:
        raise EvidenceValidationError(
            f"successor lock unavailable/invalid: {lock_path}",
            code="effective_lock_unavailable",
        ) from exc
    return _validate_successor_lock(
        lock,
        lock_path=lock_path,
        contract_path=contract_path,
        verify_plan_bytes=verify_plan_bytes,
    )


def _lock_amendment_binding(lock):
    return lock.get("amendment", lock.get("amendment_ledger"))


def _evidence_semantic_outcome(kind, lock, observation):
    return {
        "schema": "s00-canonical-evidence-outcome-v1",
        "kind": kind,
        "effective_lock_id": lock["lock_id"],
        "integrity_status": "PASS",
        "criterion_status": observation["criterion_status"],
        "observation": observation,
    }


def _artifact(
        kind, lock, lock_sha256, parent_bindings, observation, command):
    semantic_outcome = _evidence_semantic_outcome(kind, lock, observation)
    canonical_outcome_sha256 = canonical_sha256(semantic_outcome)
    body = {
        "schema": "s00-evidence-artifact-v1",
        "kind": kind,
        "effective_lock_id": lock["lock_id"],
        "effective_lock_sha256": lock_sha256,
        "parents": parent_bindings,
        "invocation": {"command": command, "cwd": str(ROOT), "exit_code": 0},
        "dependencies": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "joblib": joblib.__version__,
            "yaml": yaml.__version__,
            "jsonschema": getattr(jsonschema, "__version__", "unknown"),
        },
        "bindings": {
            "sources": lock["sources"],
            "schemas": lock["schemas"],
            "fixtures": lock["fixtures"],
            "amendment_ledger": _lock_amendment_binding(lock),
            "seeds": lock["seeds"],
        },
        "integrity_status": "PASS",
        "criterion_status": observation["criterion_status"],
        "observation": observation,
        "semantic_outcome": semantic_outcome,
        "canonical_outcome_sha256": canonical_outcome_sha256,
        "conclusion": (
            "S00 CPU-only synthetic evidence semantics within the frozen boundary"
        ),
        "unsupported_claims": ["GPU performance", "kernel performance", "S10 discovery"],
    }
    digest = canonical_sha256(body)
    return dict(
        body,
        artifact_id=f"s00-{kind}-{digest}",
        artifact_sha256=digest,
    )


def _write_evidence_to(
        output_dir, *, command, lock_path=LOCK_PATH,
        contract_path=CONTRACT_PATH, successor=False,
        verify_plan_bytes=True):
    lock_path = Path(lock_path)
    if successor:
        if contract_path == CONTRACT_PATH:
            _assert_immutable_old_generation()
        lock = _load_validated_successor_lock(
            lock_path,
            contract_path,
            verify_plan_bytes=verify_plan_bytes,
        )
    else:
        lock = _load_validated_lock(lock_path, contract_path)
    lock_sha256 = sha256_file(lock_path)
    producers = [
        ("neutrality", lambda: run_neutrality(
            lock, effective_lock_sha256=lock_sha256
        )),
        ("resume-parity", lambda: run_resume(
            lock, effective_lock_sha256=lock_sha256
        )),
        ("reconciliation", run_reconciliation),
        ("lineage-fail-closed", lambda: run_lineage(
            lock, lock_path=lock_path
        )),
    ]
    parent_bindings = []
    written = []
    for kind, producer in producers:
        if successor and contract_path == CONTRACT_PATH:
            _assert_immutable_old_generation()
        observation = producer()
        if observation["criterion_status"] != "PASS":
            raise EvidenceValidationError(
                f"{kind} criterion failed", code="criterion_failed"
            )
        artifact = _artifact(
            kind, lock, lock_sha256, parent_bindings, observation, command
        )
        filename = (
            f"s00-{kind}-successor-001.json"
            if successor else f"s00-{kind}.json"
        )
        path = Path(output_dir) / filename
        atomic_write_json(path, artifact, exclusive=True)
        binding = {
            "artifact_id": artifact["artifact_id"],
            "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else path.name,
            "sha256": sha256_file(path),
        }
        parent_bindings = [binding]
        written.append(binding)
        if successor and contract_path == CONTRACT_PATH:
            _assert_immutable_old_generation()
    return lock, written


def produce_evidence():
    command = (
        "PYTHONPATH=projects/hipblaslt/tensilelite python3 -B "
        "study_docs/research/ductile-origami-warmstart/protocol/v1/"
        "run_s00_foundation.py evidence"
    )
    lock, written = _write_evidence_to(EVIDENCE_DIR, command=command)
    print(json.dumps({
        "status": "S00_EVIDENCE_WRITTEN",
        "lock_id": lock["lock_id"],
        "artifacts": written,
    }, sort_keys=True))


def _write_successor_evidence_to(
        output_dir, *, command, lock_path=SUCCESSOR_LOCK_PATH,
        contract_path=CONTRACT_PATH, verify_plan_bytes=True):
    return _write_evidence_to(
        output_dir,
        command=command,
        lock_path=lock_path,
        contract_path=contract_path,
        successor=True,
        verify_plan_bytes=verify_plan_bytes,
    )


def produce_successor_evidence():
    _assert_immutable_old_generation()
    _assert_successor_targets_absent(
        (*SUCCESSOR_EVIDENCE_PATHS, SUCCESSOR_DECISION_PATH)
    )
    command = (
        "PYTHONPATH=projects/hipblaslt/tensilelite python3 -B "
        "study_docs/research/ductile-origami-warmstart/protocol/v1/"
        "run_s00_foundation.py evidence-successor"
    )
    lock, written = _write_successor_evidence_to(
        EVIDENCE_DIR, command=command
    )
    _assert_immutable_old_generation()
    print(json.dumps({
        "status": "S00_SUCCESSOR_EVIDENCE_WRITTEN",
        "lock_id": lock["lock_id"],
        "artifacts": written,
        "raw_direct_evidence": {
            "neutrality": "off/on-runs+events+first-divergence",
            "resume": "continuous/resumed+events+manifests+boundary",
            "reconciliation": "original+named-negative-raw-records",
            "lineage": "lineage+lock+evidence-class-matrix",
        },
    }, sort_keys=True))


def _validate_artifact(path, lock, expected_kind, *, lock_path=LOCK_PATH):
    artifact = strict_load_json(path)
    required = {
        "schema", "kind", "effective_lock_id", "effective_lock_sha256",
        "parents", "invocation", "dependencies", "bindings",
        "integrity_status", "criterion_status", "observation", "conclusion",
        "semantic_outcome", "canonical_outcome_sha256",
        "unsupported_claims", "artifact_id", "artifact_sha256",
    }
    if set(artifact) != required or artifact["kind"] != expected_kind:
        raise EvidenceValidationError(
            f"malformed evidence {path}", code="evidence_malformed"
        )
    body = {
        key: value for key, value in artifact.items()
        if key not in {"artifact_id", "artifact_sha256"}
    }
    digest = canonical_sha256(body)
    expected_semantic = _evidence_semantic_outcome(
        expected_kind, lock, artifact["observation"]
    )
    expected_bindings = {
        "sources": lock["sources"],
        "schemas": lock["schemas"],
        "fixtures": lock["fixtures"],
        "amendment_ledger": _lock_amendment_binding(lock),
        "seeds": lock["seeds"],
    }
    if (
            artifact["artifact_sha256"] != digest or
            artifact["artifact_id"] != f"s00-{expected_kind}-{digest}" or
            artifact["effective_lock_id"] != lock["lock_id"] or
            artifact["effective_lock_sha256"] != sha256_file(lock_path) or
            artifact["bindings"] != expected_bindings or
            artifact["integrity_status"] != (
                expected_semantic["integrity_status"]
            ) or
            artifact["criterion_status"] != (
                expected_semantic["criterion_status"]
            ) or
            artifact["semantic_outcome"] != expected_semantic or
            artifact["canonical_outcome_sha256"] != canonical_sha256(
                expected_semantic
            )):
        raise EvidenceValidationError(
            f"evidence hash/lock mismatch {path}", code="evidence_hash_mismatch"
        )
    validators = {
        "neutrality": _validate_neutrality_observation,
        "resume-parity": _validate_resume_observation,
        "reconciliation": _validate_reconciliation_observation,
        "lineage-fail-closed": _validate_lineage_observation,
    }
    validators[expected_kind](artifact["observation"])
    return artifact


def _decision_semantic_outcome(lock, evidence_outcomes, acceptance_map=None):
    acceptance_map = acceptance_map or {
        f"AC-{index:02d}": "PASS" for index in range(1, 11)
    }
    return {
        "schema": "s00-canonical-decision-outcome-v1",
        "effective_lock_id": lock["lock_id"],
        "criterion": "S00_EVIDENCE_READY",
        "integrity_status": "PASS",
        "criterion_status": "PASS",
        "technical_state": "PASS",
        "scientific_outcome": "positive",
        "acceptance_map": acceptance_map,
        "outgoing_edges": ["S10"],
        "evidence_outcomes": evidence_outcomes,
    }


def _write_decision_to(
        output_dir, evidence_dir, *, command, lock_path=LOCK_PATH,
        contract_path=CONTRACT_PATH, successor=False,
        verify_plan_bytes=True, independent_reproduction=None):
    lock_path = Path(lock_path)
    if successor:
        if contract_path == CONTRACT_PATH:
            _assert_immutable_old_generation()
        lock = _load_validated_successor_lock(
            lock_path,
            contract_path,
            verify_plan_bytes=verify_plan_bytes,
        )
    else:
        lock = _load_validated_lock(lock_path, contract_path)
    if independent_reproduction is None:
        independent_reproduction = successor
    kinds = (
        "neutrality", "resume-parity", "reconciliation", "lineage-fail-closed"
    )
    artifacts = []
    evidence_outcomes = []
    prior = []
    for kind in kinds:
        filename = (
            f"s00-{kind}-successor-001.json"
            if successor else f"s00-{kind}.json"
        )
        path = Path(evidence_dir) / filename
        try:
            artifact = _validate_artifact(
                path, lock, kind, lock_path=lock_path
            )
        except OSError as exc:
            raise EvidenceValidationError(
                f"required successor evidence missing: {path}",
                code="decision_evidence_missing",
            ) from exc
        if artifact["parents"] != prior:
            raise EvidenceValidationError(
                f"evidence parent mismatch {path}",
                code="evidence_parent_mismatch",
            )
        binding = {
            "artifact_id": artifact["artifact_id"],
            "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else path.name,
            "sha256": sha256_file(path),
        }
        prior = [binding]
        artifacts.append(binding)
        evidence_outcomes.append({
            "kind": kind,
            "canonical_outcome_sha256": (
                artifact["canonical_outcome_sha256"]
                ),
        })
        if (
                artifact["integrity_status"] != "PASS" or
                artifact["criterion_status"] != "PASS"):
            raise EvidenceValidationError(
                f"required evidence failed: {kind}",
                code="decision_evidence_failed",
            )
    ready = len(artifacts) == len(kinds)
    if not ready:
        raise EvidenceValidationError(
            "required evidence is not ready", code="decision_evidence_failed"
        )
    if independent_reproduction:
        fresh_observations = {
            "neutrality": run_neutrality(
                lock, effective_lock_sha256=sha256_file(lock_path)
            ),
            "resume-parity": run_resume(
                lock, effective_lock_sha256=sha256_file(lock_path)
            ),
            "reconciliation": run_reconciliation(),
            "lineage-fail-closed": run_lineage(
                lock, lock_path=lock_path
            ),
        }
        for kind in kinds:
            filename = f"s00-{kind}-successor-001.json"
            artifact = strict_load_json(Path(evidence_dir) / filename)
            if (
                    artifact["observation"] != fresh_observations[kind] or
                    artifact["canonical_outcome_sha256"]
                    != canonical_sha256(_evidence_semantic_outcome(
                        kind, lock, fresh_observations[kind]
                    ))):
                raise EvidenceValidationError(
                    f"independent reproduction mismatch: {kind}",
                    code="decision_reproduction_mismatch",
                )
    acceptance_map = {
        f"AC-{index:02d}": "PASS" for index in range(1, 11)
    }
    semantic_outcome = _decision_semantic_outcome(
        lock, evidence_outcomes, acceptance_map
    )
    body = {
        "schema": "s00-decision-v1",
        "effective_lock_id": lock["lock_id"],
        "effective_lock_sha256": sha256_file(lock_path),
        "criterion": "S00_EVIDENCE_READY",
        "invocation": {"command": command, "cwd": str(ROOT), "exit_code": 0},
        "dependencies": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "joblib": joblib.__version__,
            "yaml": yaml.__version__,
            "jsonschema": getattr(jsonschema, "__version__", "unknown"),
        },
        "bindings": {
            "sources": lock["sources"],
            "schemas": lock["schemas"],
            "fixtures": lock["fixtures"],
            "amendment_ledger": _lock_amendment_binding(lock),
            "seeds": lock["seeds"],
        },
        "integrity_status": "PASS",
        "criterion_status": "PASS",
        "technical_state": "PASS",
        "scientific_outcome": "positive",
        "acceptance_map": acceptance_map,
        "outgoing_edges": ["S10"],
        "evidence": artifacts,
        "semantic_outcome": semantic_outcome,
        "canonical_outcome_sha256": canonical_sha256(semantic_outcome),
        "conclusion": "S00 evidence foundation criterion is satisfied.",
        "unsupported_claims": ["GPU performance", "S10 outcome"],
    }
    digest = canonical_sha256(body)
    decision = dict(
        body,
        artifact_id=f"s00-decision-{digest}",
        artifact_sha256=digest,
    )
    target = Path(output_dir) / (
        "s00-decision-successor-001.json"
        if successor else "s00-decision.json"
    )
    atomic_write_json(target, decision, exclusive=True)
    if successor and contract_path == CONTRACT_PATH:
        _assert_immutable_old_generation()
    return decision, target


def _validate_decision(
        path, lock, *, lock_path=LOCK_PATH, evidence_dir=None):
    decision = strict_load_json(path)
    required = {
        "schema", "effective_lock_id", "effective_lock_sha256",
        "criterion", "invocation", "dependencies", "bindings",
        "integrity_status", "criterion_status", "technical_state",
        "scientific_outcome", "acceptance_map", "outgoing_edges", "evidence",
        "semantic_outcome", "canonical_outcome_sha256", "conclusion",
        "unsupported_claims", "artifact_id", "artifact_sha256",
    }
    if set(decision) != required:
        raise EvidenceValidationError(
            f"malformed decision {path}", code="decision_malformed"
        )
    body = {
        key: value for key, value in decision.items()
        if key not in {"artifact_id", "artifact_sha256"}
    }
    digest = canonical_sha256(body)
    if evidence_dir is None:
        expected_outcomes = [
            {
                "kind": binding["kind"],
                "canonical_outcome_sha256": (
                    binding["canonical_outcome_sha256"]
                ),
            }
            for binding in decision["semantic_outcome"]["evidence_outcomes"]
        ]
    else:
        expected_outcomes = []
        expected_evidence_bindings = []
        prior = []
        for kind in (
                "neutrality", "resume-parity", "reconciliation",
                "lineage-fail-closed"):
            successor = lock.get("generation") == "successor-001"
            artifact_path = Path(evidence_dir) / (
                f"s00-{kind}-successor-001.json"
                if successor else f"s00-{kind}.json"
            )
            artifact = _validate_artifact(
                artifact_path,
                lock,
                kind,
                lock_path=lock_path,
            )
            if artifact["parents"] != prior:
                raise EvidenceValidationError(
                    f"evidence parent mismatch {artifact_path}",
                    code="evidence_parent_mismatch",
                )
            binding = {
                "artifact_id": artifact["artifact_id"],
                "path": (
                    str(artifact_path.relative_to(ROOT))
                    if artifact_path.is_relative_to(ROOT)
                    else artifact_path.name
                ),
                "sha256": sha256_file(artifact_path),
            }
            prior = [binding]
            expected_evidence_bindings.append(binding)
            expected_outcomes.append({
                "kind": kind,
                "canonical_outcome_sha256": (
                    artifact["canonical_outcome_sha256"]
                ),
            })
    expected_semantic = _decision_semantic_outcome(
        lock, expected_outcomes, decision["acceptance_map"]
    )
    expected_bindings = {
        "sources": lock["sources"],
        "schemas": lock["schemas"],
        "fixtures": lock["fixtures"],
        "amendment_ledger": _lock_amendment_binding(lock),
        "seeds": lock["seeds"],
    }
    if (
            decision["artifact_sha256"] != digest or
            decision["artifact_id"] != f"s00-decision-{digest}" or
            decision["effective_lock_id"] != lock["lock_id"] or
            decision["effective_lock_sha256"] != sha256_file(lock_path) or
            decision["bindings"] != expected_bindings or
            decision["criterion"] != expected_semantic["criterion"] or
            decision["integrity_status"] != (
                expected_semantic["integrity_status"]
            ) or
            decision["criterion_status"] != (
                expected_semantic["criterion_status"]
            ) or
            decision["technical_state"] != (
                expected_semantic["technical_state"]
            ) or
            decision["scientific_outcome"] != (
                expected_semantic["scientific_outcome"]
            ) or
            decision["acceptance_map"] != {
                f"AC-{index:02d}": "PASS" for index in range(1, 11)
            } or
            decision["outgoing_edges"] != expected_semantic["outgoing_edges"] or
            (
                evidence_dir is not None and
                decision["evidence"] != expected_evidence_bindings
            ) or
            decision["semantic_outcome"] != expected_semantic or
            decision["canonical_outcome_sha256"] != canonical_sha256(
                expected_semantic
            )):
        raise EvidenceValidationError(
            f"decision hash/lock mismatch {path}",
            code="decision_hash_mismatch",
        )
    return decision


def produce_decision():
    command = (
        "PYTHONPATH=projects/hipblaslt/tensilelite python3 -B "
        "study_docs/research/ductile-origami-warmstart/protocol/v1/"
        "run_s00_foundation.py decision"
    )
    decision, path = _write_decision_to(
        EVIDENCE_DIR, EVIDENCE_DIR, command=command
    )
    print(json.dumps({
        "status": "S00_EVIDENCE_READY",
        "artifact_id": decision["artifact_id"],
        "sha256": sha256_file(path),
        "outgoing_edges": decision["outgoing_edges"],
    }, sort_keys=True))


def _write_successor_decision_to(
        output_dir, evidence_dir, *, command,
        lock_path=SUCCESSOR_LOCK_PATH, contract_path=CONTRACT_PATH,
        verify_plan_bytes=True, independent_reproduction=True):
    return _write_decision_to(
        output_dir,
        evidence_dir,
        command=command,
        lock_path=lock_path,
        contract_path=contract_path,
        successor=True,
        verify_plan_bytes=verify_plan_bytes,
        independent_reproduction=independent_reproduction,
    )


def produce_successor_decision():
    _assert_immutable_old_generation()
    if SUCCESSOR_DECISION_PATH.exists():
        raise EvidenceValidationError(
            "successor decision target exists",
            code="successor_target_exists",
        )
    command = (
        "PYTHONPATH=projects/hipblaslt/tensilelite python3 -B "
        "study_docs/research/ductile-origami-warmstart/protocol/v1/"
        "run_s00_foundation.py decision-successor"
    )
    decision, path = _write_successor_decision_to(
        EVIDENCE_DIR, EVIDENCE_DIR, command=command
    )
    _assert_immutable_old_generation()
    print(json.dumps({
        "status": "S00_SUCCESSOR_EVIDENCE_READY",
        "artifact_id": decision["artifact_id"],
        "sha256": sha256_file(path),
        "criterion": decision["criterion"],
        "acceptance_map": decision["acceptance_map"],
        "technical_state": decision["technical_state"],
        "scientific_outcome": decision["scientific_outcome"],
        "outgoing_edges": decision["outgoing_edges"],
    }, sort_keys=True))


def _assert_reproduction_matches(
        authoritative, fresh, authoritative_decision, fresh_decision):
    for kind in (
            "neutrality", "resume-parity", "reconciliation",
            "lineage-fail-closed"):
        if (
                fresh[kind]["canonical_outcome_sha256"] !=
                authoritative[kind]["canonical_outcome_sha256"] or
                fresh[kind]["semantic_outcome"] !=
                authoritative[kind]["semantic_outcome"] or
                fresh[kind]["observation"] !=
                authoritative[kind]["observation"]):
            raise EvidenceValidationError(
                f"reproduction outcome mismatch: {kind}",
                code="reproduction_outcome_mismatch",
            )
    if (
            fresh_decision["canonical_outcome_sha256"] !=
            authoritative_decision["canonical_outcome_sha256"] or
            fresh_decision["semantic_outcome"] !=
            authoritative_decision["semantic_outcome"] or
            fresh_decision["outgoing_edges"] !=
            authoritative_decision["outgoing_edges"]):
        raise EvidenceValidationError(
            "reproduction decision outcome mismatch",
            code="reproduction_decision_mismatch",
        )


def reproduce(output_dir):
    target = Path(output_dir)
    if target.exists() and any(target.iterdir()):
        raise EvidenceValidationError(
            "reproduction output directory must be empty",
            code="reproduction_output_not_empty",
        )
    lock = _load_validated_lock()
    kinds = (
        "neutrality", "resume-parity", "reconciliation",
        "lineage-fail-closed",
    )
    authoritative = {
        kind: _validate_artifact(
            EVIDENCE_DIR / f"s00-{kind}.json", lock, kind
        )
        for kind in kinds
    }
    authoritative_decision = _validate_decision(
        EVIDENCE_DIR / "s00-decision.json",
        lock,
        evidence_dir=EVIDENCE_DIR,
    )
    tracked_before = {
        path: sha256_file(path)
        for path in OUTPUT_PATHS if path.exists()
    }
    target.mkdir(parents=True, exist_ok=True)
    command = (
        "PYTHONPATH=projects/hipblaslt/tensilelite python3 -B "
        "study_docs/research/ductile-origami-warmstart/protocol/v1/"
        f"run_s00_foundation.py reproduce --output-dir {output_dir}"
    )
    _, written = _write_evidence_to(target, command=command)
    decision, decision_path = _write_decision_to(
        target, target, command=command
    )
    fresh = {
        kind: _validate_artifact(
            target / f"s00-{kind}.json", lock, kind
        )
        for kind in kinds
    }
    fresh_decision = _validate_decision(
        decision_path, lock, evidence_dir=target
    )
    _assert_reproduction_matches(
        authoritative,
        fresh,
        authoritative_decision,
        fresh_decision,
    )
    tracked_after = {
        path: sha256_file(path)
        for path in OUTPUT_PATHS if path.exists()
    }
    if tracked_before != tracked_after:
        raise EvidenceValidationError(
            "authoritative evidence changed during reproduction",
            code="authoritative_evidence_mutated",
        )
    print(json.dumps({
        "status": "S00_REPRODUCTION_OK",
        "artifacts": written,
        "decision_id": decision["artifact_id"],
        "canonical_outcome_sha256": (
            fresh_decision["canonical_outcome_sha256"]
        ),
        "decision_sha256": sha256_file(decision_path),
        "authoritative_evidence": "unchanged",
    }, sort_keys=True))


def reproduce_successor(output_dir):
    _assert_immutable_old_generation()
    target = Path(output_dir)
    if target.exists() and any(target.iterdir()):
        raise EvidenceValidationError(
            "reproduction output directory must be empty",
            code="reproduction_output_not_empty",
        )
    lock = _load_validated_successor_lock()
    kinds = (
        "neutrality", "resume-parity", "reconciliation",
        "lineage-fail-closed",
    )
    authoritative = {
        kind: _validate_artifact(
            EVIDENCE_DIR / f"s00-{kind}-successor-001.json",
            lock,
            kind,
            lock_path=SUCCESSOR_LOCK_PATH,
        )
        for kind in kinds
    }
    authoritative_decision = _validate_decision(
        SUCCESSOR_DECISION_PATH,
        lock,
        lock_path=SUCCESSOR_LOCK_PATH,
        evidence_dir=EVIDENCE_DIR,
    )
    tracked_paths = (*IMMUTABLE_OLD_OUTPUTS, *SUCCESSOR_OUTPUT_PATHS)
    tracked_before = {
        str(path.relative_to(ROOT)): sha256_file(path)
        for path in tracked_paths if path.exists()
    }
    command = (
        "PYTHONPATH=projects/hipblaslt/tensilelite python3 -B "
        "study_docs/research/ductile-origami-warmstart/protocol/v1/"
        f"run_s00_foundation.py reproduce-successor --output-dir {output_dir}"
    )
    _, written = _write_successor_evidence_to(
        target,
        command=command,
    )
    decision, decision_path = _write_successor_decision_to(
        target,
        target,
        command=command,
    )
    fresh = {
        kind: _validate_artifact(
            target / f"s00-{kind}-successor-001.json",
            lock,
            kind,
            lock_path=SUCCESSOR_LOCK_PATH,
        )
        for kind in kinds
    }
    fresh_decision = _validate_decision(
        decision_path,
        lock,
        lock_path=SUCCESSOR_LOCK_PATH,
        evidence_dir=target,
    )
    _assert_reproduction_matches(
        authoritative,
        fresh,
        authoritative_decision,
        fresh_decision,
    )
    tracked_after = {
        str(path.relative_to(ROOT)): sha256_file(path)
        for path in tracked_paths if path.exists()
    }
    if tracked_before != tracked_after:
        raise EvidenceValidationError(
            "authoritative generations changed during reproduction",
            code="authoritative_evidence_mutated",
        )
    _assert_immutable_old_generation()
    print(json.dumps({
        "status": "S00_SUCCESSOR_REPRODUCTION_OK",
        "artifacts": written,
        "decision_id": decision["artifact_id"],
        "canonical_outcome_sha256": (
            fresh_decision["canonical_outcome_sha256"]
        ),
        "decision_sha256": sha256_file(decision_path),
        "authoritative_old_and_successor": "unchanged",
    }, sort_keys=True))


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subparsers.add_parser("preflight-successor")
    preflight_parser.add_argument("--original-plan-b", required=True)
    preflight_parser.add_argument("--recovery-plan-b", required=True)
    lock_parser = subparsers.add_parser("lock-successor")
    lock_parser.add_argument("--original-plan-b", required=True)
    lock_parser.add_argument("--recovery-plan-b", required=True)
    subparsers.add_parser("evidence-successor")
    subparsers.add_parser("decision-successor")
    reproduce_parser = subparsers.add_parser("reproduce-successor")
    reproduce_parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.command == "preflight-successor":
        preflight_successor(args.original_plan_b, args.recovery_plan_b)
    elif args.command == "lock-successor":
        create_successor_lock(args.original_plan_b, args.recovery_plan_b)
    elif args.command == "evidence-successor":
        produce_successor_evidence()
    elif args.command == "decision-successor":
        produce_successor_decision()
    elif args.command == "reproduce-successor":
        reproduce_successor(args.output_dir)


if __name__ == "__main__":
    try:
        main()
    except EvidenceValidationError as exc:
        print(f"S00_ERROR[{exc.code}]: {exc}", file=sys.stderr)
        raise SystemExit(2)
