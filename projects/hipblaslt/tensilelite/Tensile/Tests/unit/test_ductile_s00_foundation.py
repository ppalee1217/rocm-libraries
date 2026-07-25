# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

import copy
import importlib.util
import json
import pickle
import random
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import yaml

from Tensile.ductile.evidence import (
    CheckpointValidationError,
    EvidenceValidationError,
    append_amendment,
    atomic_write_json,
    build_ga_event,
    canonical_sha256,
    freeze_payload,
    reconcile_artifacts,
    sha256_file,
    strict_load_json,
    strict_load_yaml,
    validate_event_chain,
    validate_lineage,
    validate_schema_document,
)
from Tensile.ductile.evidence import _validator_for


REPO_ROOT = Path(__file__).resolve().parents[6]
PROTOCOL = (
    REPO_ROOT
    / "study_docs/research/ductile-origami-warmstart/protocol/v1"
)
RUNNER_PATH = PROTOCOL / "run_s00_foundation.py"
SPEC = importlib.util.spec_from_file_location("s00_foundation_runner", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)
DUMMY_LOCK_SHA256 = canonical_sha256({"lock": "preflight-only"})
DUMMY_LOCK = {
    "seeds": {
        "neutrality": 41001,
        "resume": 41002,
        "reconciliation": 41003,
        "lineage": 41004,
    },
    "sources": [{"path": "ga.py", "sha256": canonical_sha256("ga")}],
    "fixtures": [{"path": "fixture.json", "sha256": canonical_sha256("fixture")}],
    "contract": {"path": "contract.yaml", "sha256": canonical_sha256("contract")},
}


def _write_temp_contract_and_lock(
        directory, *, parent_lock=None, contract=None):
    directory = Path(directory)
    ledger_path = directory / "amendment-ledger.jsonl"
    if not ledger_path.exists():
        ledger_path.write_bytes(b"")
    opaque_path = directory / "opaque-planner-input.txt"
    if not opaque_path.exists():
        opaque_path.write_text("independent opaque test input\n", encoding="utf-8")
    if contract is None:
        contract = strict_load_yaml(PROTOCOL / "study-contract.yaml")
    contract = copy.deepcopy(contract)
    contract["amendment_ledger"] = {
        "path": str(ledger_path.relative_to(REPO_ROOT)),
        "raw_sha256": RUNNER.AMENDMENT_RAW_SHA256,
        "head_sha256": RUNNER.AMENDMENT_HEAD_SHA256,
        "amendment_id": RUNNER.AMENDMENT_ID,
    }
    contract_path = directory / "study-contract.yaml"
    contract_path.write_text(
        yaml.safe_dump(contract, sort_keys=False), encoding="utf-8"
    )
    base = RUNNER._successor_lock_base(
        contract, contract_path=contract_path
    )
    if parent_lock is not None:
        base["parent_lock"] = parent_lock
    lock = RUNNER._derived_lock_document(base)
    lock_path = directory / f"{lock['lock_id']}.json"
    atomic_write_json(lock_path, lock)
    return contract, contract_path, ledger_path, lock, lock_path


class TestStrictEvidencePrimitives(unittest.TestCase):
    def test_strict_json_and_yaml_reject_duplicate_keys(self):
        for loader, text in (
            (strict_load_json, '{"x":1,"x":2}'),
            (strict_load_yaml, "x: 1\nx: 2\n"),
        ):
            with self.subTest(loader=loader.__name__):
                with self.assertRaises(EvidenceValidationError) as context:
                    loader(text, from_text=True)
                self.assertEqual(context.exception.code, "duplicate_key")

    def test_canonical_hash_is_order_independent_and_finite_only(self):
        self.assertEqual(
            canonical_sha256({"a": 1, "b": 2}),
            canonical_sha256({"b": 2, "a": 1}),
        )
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaises(EvidenceValidationError):
                    canonical_sha256({"value": value})

    def test_payload_is_recursively_immutable(self):
        payload = freeze_payload({"items": [{"x": 1}]})
        with self.assertRaises(TypeError):
            payload["items"][0]["x"] = 2

    def test_schema_metaschema_and_unknown_field_rejection(self):
        for path in sorted((PROTOCOL / "schemas").glob("*.json")):
            schema = strict_load_json(path)
            _validator_for(schema)
        lineage = strict_load_json(PROTOCOL / "fixtures/valid-run.json")["lineage"]
        lineage["extra"] = True
        schema = strict_load_json(PROTOCOL / "schemas/lineage.schema.json")
        with self.assertRaises(EvidenceValidationError):
            validate_schema_document(lineage, schema)

    def test_atomic_exclusive_writer_and_amendment_chain(self):
        schema = strict_load_json(PROTOCOL / "schemas/amendment.schema.json")
        digest = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "artifact.json"
            atomic_write_json(target, {"value": 1})
            with self.assertRaises(EvidenceValidationError) as context:
                atomic_write_json(target, {"value": 1})
            self.assertEqual(context.exception.code, "already_exists")

            ledger = Path(directory) / "ledger.jsonl"
            first = {
                "amendment_id": "a1",
                "previous_entry_sha256": None,
                "superseded_lock_id": "lock-1",
                "superseded_lock_sha256": digest,
                "trigger": "test",
                "reason": "test",
                "changed_bindings": ["fixture"],
                "affected_evidence": ["neutrality"],
                "required_rerun_scope": ["all"],
                "new_lock_target": "lock-2.json",
                "decision_authority": "user",
            }
            first_hash = append_amendment(ledger, first, schema)
            second = dict(first, amendment_id="a2",
                          previous_entry_sha256=first_hash)
            append_amendment(ledger, second, schema)
            self.assertEqual(len(ledger.read_bytes().splitlines()), 2)


class TestFixtureValidation(unittest.TestCase):
    def test_complete_fixture_matrix(self):
        result = RUNNER.validate_fixtures()
        self.assertEqual(result["valid"], "success")
        self.assertGreaterEqual(result["invalid_lineage_cases"], 13)
        self.assertGreaterEqual(result["invalid_event_cases"], 7)
        self.assertGreaterEqual(result["backend_failure_cases"], 4)

    def test_valid_events_pass_schema_and_hash_chain(self):
        fixture = strict_load_json(PROTOCOL / "fixtures/valid-run.json")
        result = validate_event_chain(fixture["events"])
        self.assertEqual(result["next_sequence"], len(fixture["events"]))
        cross_run = copy.deepcopy(fixture["events"])
        cross_run[1]["run_id"] = "different-run"
        with self.assertRaises(EvidenceValidationError) as context:
            validate_event_chain(cross_run)
        self.assertEqual(
            context.exception.code, "event_lineage_mismatch"
        )

    def test_reconciliation_observation_exposes_rebuildable_chains(self):
        observation = RUNNER.run_reconciliation()
        self.assertEqual(observation["criterion_status"], "PASS")
        for name, expected in (
                ("valid_success", "success"),
                ("explicit_backend_failure", "backend_failure")):
            chain = observation[name]
            rebuilt = RUNNER.reconcile_artifacts(chain["records"])
            self.assertEqual(rebuilt["outcome"], expected)
            self.assertEqual(rebuilt["chain_head"], chain["chain_head"])
            self.assertTrue(all(
                record["record_sha256"] and record["payload_sha256"]
                for record in chain["records"]
            ))
        self.assertTrue(observation["invalid_cases"])
        self.assertTrue(all(
            item["observed_error"] == item["expected_error"]
            for item in observation["invalid_cases"]
        ))

    def test_lineage_requires_every_bound_identity(self):
        lineage = strict_load_json(
            PROTOCOL / "fixtures/valid-run.json"
        )["lineage"]
        validate_lineage(lineage)
        for field in (
            "parent_id", "input_sha256", "source_bundle_sha256",
            "fixture_sha256", "seed", "effective_lock_sha256",
        ):
            with self.subTest(field=field):
                candidate = copy.deepcopy(lineage)
                candidate.pop(field)
                with self.assertRaises(EvidenceValidationError):
                    validate_lineage(candidate)
        for field in (
            "effective_lock_sha256", "input_sha256",
            "source_bundle_sha256", "fixture_sha256",
        ):
            with self.subTest(malformed_hash=field):
                candidate = copy.deepcopy(lineage)
                candidate[field] = "not-a-sha256"
                with self.assertRaises(EvidenceValidationError) as context:
                    validate_lineage(candidate)
                self.assertEqual(
                    context.exception.code, "lineage_hash_malformed"
                )


class TestObserverAndCheckpointBehavior(unittest.TestCase):
    def test_observer_neutrality_with_adversarial_callback(self):
        result = RUNNER.run_neutrality(
            DUMMY_LOCK, effective_lock_sha256=DUMMY_LOCK_SHA256
        )
        self.assertEqual(result["criterion_status"], "PASS")
        self.assertEqual(
            result["first_divergence"]["status"], "no_divergence"
        )
        self.assertEqual(result["observer_off"]["events"], [])
        self.assertTrue(result["observer_on"]["events"])
        self.assertGreater(result["callback_counts"]["python"], 0)
        self.assertGreater(result["callback_counts"]["numpy"], 0)

    def test_continuous_and_checkpoint_resume_parity(self):
        result = RUNNER.run_resume(
            DUMMY_LOCK, effective_lock_sha256=DUMMY_LOCK_SHA256
        )
        self.assertEqual(result["criterion_status"], "PASS")
        self.assertEqual(
            result["first_divergence"]["status"], "no_divergence"
        )
        ids = [
            item["manifest"]["checkpoint_id"]
            for item in result["checkpoint_evidence"]["resumed"]
        ]
        self.assertEqual(len(ids), len(set(ids)))

    def test_callback_exception_restores_both_global_rngs(self):
        lineage = RUNNER._lineage(
            DUMMY_LOCK,
            "neutrality",
            "callback-error",
            "callback-error-run",
            effective_lock_sha256=DUMMY_LOCK_SHA256,
        )

        def callback(_event):
            random.random()
            np.random.random()
            raise RuntimeError("observer failed")

        ga, _ = RUNNER._make_ga(41001, callback, lineage)
        py_before = random.getstate()
        np_before = np.random.get_state()
        with self.assertRaisesRegex(RuntimeError, "observer failed"):
            ga._emit("test", 0, {"value": 1})
        self.assertEqual(canonical_sha256(py_before), canonical_sha256(random.getstate()))
        self.assertEqual(canonical_sha256(np_before), canonical_sha256(np.random.get_state()))

    def test_default_observer_disabled_path_remains_available(self):
        ga, evaluations = RUNNER._make_ga(41001, None, None)
        result = RUNNER._run_ga(ga, evaluations)
        self.assertEqual(result["termination_reason"], "fixed_horizon")
        self.assertEqual(result["final_generation"], 4)

    def test_tamper_wrong_id_and_lineage_reject_before_state_restore(self):
        lineage = RUNNER._lineage(
            DUMMY_LOCK,
            "resume",
            "tamper",
            "tamper-run",
            effective_lock_sha256=DUMMY_LOCK_SHA256,
        )
        with tempfile.TemporaryDirectory() as directory:
            checkpoint_path = Path(directory) / "checkpoint.pkl"
            events = []
            writer, _ = RUNNER._make_ga(
                41002,
                lambda event: events.append(event.as_dict()),
                lineage,
                checkpoint_path=checkpoint_path,
                interrupt=2,
            )
            with self.assertRaises(RUNNER.DurableInterruption):
                writer.optimize()
            with open(checkpoint_path, "rb") as stream:
                envelope = pickle.load(stream)
            manifest = envelope["manifest"]
            journal = RUNNER._journal(manifest)

            reader, _ = RUNNER._make_ga(
                41002, lambda _event: None, lineage,
                checkpoint_path=checkpoint_path,
            )
            state_before = {
                "stats": copy.deepcopy(reader.stats),
                "sequence": reader._observer_sequence,
                "rng": canonical_sha256(random.getstate()),
            }
            with self.assertRaises(CheckpointValidationError):
                reader.load(
                    envelope,
                    expected_checkpoint_id="ga-checkpoint-" + "0" * 64,
                    prior_checkpoint_journal=journal,
                )
            self.assertEqual(reader.stats, state_before["stats"])
            self.assertEqual(reader._observer_sequence, state_before["sequence"])
            self.assertEqual(canonical_sha256(random.getstate()), state_before["rng"])

            tampered = copy.deepcopy(envelope)
            tampered["state"]["checkpoint_lineage"]["input_sha256"] = "f" * 64
            with self.assertRaises(EvidenceValidationError):
                reader.load(
                    tampered,
                    expected_checkpoint_id=manifest["checkpoint_id"],
                    prior_checkpoint_journal=journal,
                )
            self.assertEqual(reader.stats, state_before["stats"])
            self.assertEqual(reader._observer_sequence, state_before["sequence"])

            lineage_mutations = {
                "effective_lock_sha256": "e" * 64,
                "input_sha256": "d" * 64,
                "source_bundle_sha256": "c" * 64,
                "fixture_sha256": "b" * 64,
                "seed": {"name": "resume", "value": 999},
            }
            for field, value in lineage_mutations.items():
                with self.subTest(field=field):
                    candidate = copy.deepcopy(envelope)
                    candidate["state"]["checkpoint_lineage"][field] = value
                    with self.assertRaises(EvidenceValidationError):
                        reader.load(
                            candidate,
                            expected_checkpoint_id=manifest["checkpoint_id"],
                            prior_checkpoint_journal=journal,
                        )
            missing = copy.deepcopy(envelope)
            missing["state"]["checkpoint_lineage"].pop("fixture_sha256")
            with self.assertRaises(EvidenceValidationError):
                reader.load(
                    missing,
                    expected_checkpoint_id=manifest["checkpoint_id"],
                    prior_checkpoint_journal=journal,
                )
            wrong_seed = copy.deepcopy(envelope)
            wrong_seed["state"]["seed"] = 999
            with self.assertRaises(EvidenceValidationError):
                reader.load(
                    wrong_seed,
                    expected_checkpoint_id=manifest["checkpoint_id"],
                    prior_checkpoint_journal=journal,
                )
            wrong_parent_journal = dict(journal, parent_checkpoint_id="wrong")
            with self.assertRaises(EvidenceValidationError):
                reader.load(
                    envelope,
                    expected_checkpoint_id=manifest["checkpoint_id"],
                    prior_checkpoint_journal=wrong_parent_journal,
                )

    def test_event_identity_is_deterministic_without_rng(self):
        kwargs = {
            "run_id": "run",
            "effective_lock_sha256": "0" * 64,
            "sequence": 0,
            "previous_event_sha256": None,
            "kind": "test",
            "generation": 0,
            "payload": {"x": 1},
        }
        before = (canonical_sha256(random.getstate()),
                  canonical_sha256(np.random.get_state()))
        left = build_ga_event(**kwargs)
        right = build_ga_event(**kwargs)
        after = (canonical_sha256(random.getstate()),
                 canonical_sha256(np.random.get_state()))
        self.assertEqual(left, right)
        self.assertEqual(before, after)


class TestEffectiveLockLifecycle(unittest.TestCase):
    def test_invalid_lock_never_creates_successful_evidence_output(self):
        with tempfile.TemporaryDirectory(
                dir=REPO_ROOT, prefix=".s00-lock-negative-") as directory:
            _, contract_path, _, lock, _ = _write_temp_contract_and_lock(
                directory
            )
            directory = Path(directory)
            missing = directory / "missing-lock.json"
            invalid = directory / "invalid-lock.json"
            invalid.write_text("{not-json", encoding="utf-8")
            non_effective = copy.deepcopy(lock)
            non_effective["state"] = "superseded"
            non_effective = RUNNER._derived_lock_document({
                key: value for key, value in non_effective.items()
                if key not in {"lock_id", "body_sha256"}
            })
            non_effective_path = directory / "non-effective.json"
            atomic_write_json(non_effective_path, non_effective)
            tampered_base = {
                key: value for key, value in lock.items()
                if key not in {"lock_id", "body_sha256"}
            }
            tampered_base["sources"] = copy.deepcopy(tampered_base["sources"])
            tampered_base["sources"][0]["sha256"] = "0" * 64
            tampered_path = directory / "tampered.json"
            atomic_write_json(
                tampered_path, RUNNER._derived_lock_document(tampered_base)
            )
            for name, lock_path in (
                    ("missing", missing),
                    ("invalid", invalid),
                    ("non-effective", non_effective_path),
                    ("tampered", tampered_path)):
                with self.subTest(name=name):
                    output = directory / f"evidence-{name}"
                    with self.assertRaises(EvidenceValidationError):
                        RUNNER._write_successor_evidence_to(
                            output,
                            command="unit-test-invalid-lock",
                            lock_path=lock_path,
                            contract_path=contract_path,
                            verify_plan_bytes=False,
                        )
                    self.assertFalse(output.exists())

    def test_amendment_successor_preserves_and_invalidates_prior_bytes(self):
        with tempfile.TemporaryDirectory(
                dir=REPO_ROOT, prefix=".s00-lock-successor-") as directory:
            directory = Path(directory)
            _, contract_path, _, lock, lock_path = (
                _write_temp_contract_and_lock(directory)
            )
            authoritative_output = directory / "authoritative"
            RUNNER._write_successor_evidence_to(
                authoritative_output,
                command="unit-test-authoritative-invocation",
                lock_path=lock_path,
                contract_path=contract_path,
                verify_plan_bytes=False,
            )
            replay_output = directory / "replay-evidence"
            RUNNER._write_successor_evidence_to(
                replay_output,
                command="unit-test-different-invocation",
                lock_path=lock_path,
                contract_path=contract_path,
                verify_plan_bytes=False,
            )
            authoritative_decision, _ = RUNNER._write_successor_decision_to(
                authoritative_output,
                authoritative_output,
                command="unit-test-authoritative-decision",
                lock_path=lock_path,
                contract_path=contract_path,
                verify_plan_bytes=False,
                independent_reproduction=False,
            )
            replay_decision, _ = RUNNER._write_successor_decision_to(
                replay_output,
                replay_output,
                command="unit-test-different-decision-invocation",
                lock_path=lock_path,
                contract_path=contract_path,
                verify_plan_bytes=False,
                independent_reproduction=False,
            )
            self.assertEqual(
                authoritative_decision["canonical_outcome_sha256"],
                replay_decision["canonical_outcome_sha256"],
            )
            self.assertEqual(
                authoritative_decision["semantic_outcome"],
                replay_decision["semantic_outcome"],
            )
            self.assertNotEqual(
                authoritative_decision["artifact_sha256"],
                replay_decision["artifact_sha256"],
            )
            authoritative_artifacts = {}
            replay_artifacts = {}
            authoritative_hashes = {
                path.name: sha256_file(path)
                for path in authoritative_output.glob("*.json")
            }
            lock_hash = sha256_file(lock_path)
            for kind in (
                    "neutrality", "resume-parity", "reconciliation",
                    "lineage-fail-closed"):
                authoritative = strict_load_json(
                    authoritative_output
                    / f"s00-{kind}-successor-001.json"
                )
                replay = strict_load_json(
                    replay_output / f"s00-{kind}-successor-001.json"
                )
                authoritative_artifacts[kind] = authoritative
                replay_artifacts[kind] = replay
                self.assertEqual(
                    authoritative["canonical_outcome_sha256"],
                    replay["canonical_outcome_sha256"],
                )
                self.assertEqual(
                    authoritative["observation"], replay["observation"]
                )
                self.assertNotEqual(
                    authoritative["artifact_sha256"],
                    replay["artifact_sha256"],
                )
            RUNNER._assert_reproduction_matches(
                authoritative_artifacts,
                replay_artifacts,
                authoritative_decision,
                replay_decision,
            )
            mismatched = copy.deepcopy(replay_artifacts)
            mismatched["neutrality"]["observation"][
                "observer_on"
            ]["raw_run"]["final_generation"] += 1
            with self.assertRaises(EvidenceValidationError) as context:
                RUNNER._assert_reproduction_matches(
                    authoritative_artifacts,
                    mismatched,
                    authoritative_decision,
                    replay_decision,
                )
            self.assertEqual(
                context.exception.code, "reproduction_outcome_mismatch"
            )

            with self.assertRaises(EvidenceValidationError):
                RUNNER._validate_artifact(
                    PROTOCOL / "evidence/s00-neutrality.json",
                    lock,
                    "neutrality",
                    lock_path=lock_path,
                )
            self.assertEqual(sha256_file(lock_path), lock_hash)
            self.assertEqual(
                {
                    path.name: sha256_file(path)
                    for path in authoritative_output.glob("*.json")
                },
                authoritative_hashes,
            )


class TestSuccessorRecovery(unittest.TestCase):
    def _valid_lock(self):
        contract = strict_load_yaml(PROTOCOL / "study-contract.yaml")
        return RUNNER._derived_lock_document(
            RUNNER._successor_lock_base(contract)
        )

    def _assert_reconcile_code(self, records, expected):
        with self.assertRaises(EvidenceValidationError) as context:
            reconcile_artifacts(RUNNER._rehash_records(records))
        self.assertEqual(context.exception.code, expected)

    def test_reconciliation_rejects_named_nonterminal_statuses(self):
        records = strict_load_json(
            PROTOCOL / "fixtures/valid-run.json"
        )["records"]
        for target, status, expected in (
                (0, "in_progress", "record_status_in_progress"),
                (2, "timeout", "record_status_timeout"),
                (2, "killed", "record_status_killed")):
            with self.subTest(status=status):
                candidate = copy.deepcopy(records)
                candidate[target]["status"] = status
                self._assert_reconcile_code(candidate, expected)

    def test_reconciliation_rejects_global_conflicting_record_id(self):
        records = strict_load_json(
            PROTOCOL / "fixtures/valid-run.json"
        )["records"]
        records[3]["record_id"] = records[1]["record_id"]
        self._assert_reconcile_code(records, "duplicate_record_id")

    def test_reconciliation_rejects_contradictory_summary_payload(self):
        records = strict_load_json(
            PROTOCOL / "fixtures/valid-run.json"
        )["records"]
        records[3]["payload"] = {"outcome": "backend_failure"}
        self._assert_reconcile_code(records, "summary_payload_mismatch")

    def test_reconciliation_enforces_exact_kind_order_and_payload_semantics(self):
        valid = strict_load_json(PROTOCOL / "fixtures/valid-run.json")
        failure = strict_load_json(
            PROTOCOL / "fixtures/backend-failure.json"
        )
        RUNNER.validate_fixtures()
        cases = []
        swapped = copy.deepcopy(valid["records"])
        swapped[1], swapped[2] = swapped[2], swapped[1]
        cases.append((swapped, "partial_success_chain"))
        bad_input = copy.deepcopy(valid["records"])
        bad_input[0]["payload"] = {"config": []}
        cases.append((bad_input, "generated_input_payload_mismatch"))
        bad_backend = copy.deepcopy(valid["records"])
        bad_backend[1]["payload"]["exit_code"] = 7
        cases.append((bad_backend, "backend_payload_mismatch"))
        bad_score = copy.deepcopy(valid["records"])
        bad_score[2]["payload"]["score"] = "3.5"
        cases.append((bad_score, "observation_payload_mismatch"))
        zero_failure = copy.deepcopy(failure["failure_records"])
        zero_failure[1]["payload"]["exit_code"] = 0
        cases.append((zero_failure, "backend_payload_mismatch"))
        for records, expected in cases:
            with self.subTest(expected=expected):
                self._assert_reconcile_code(records, expected)

    def test_successor_lock_rejects_each_single_substitution_before_output(self):
        lock = self._valid_lock()
        cases = RUNNER._single_substitution_cases(lock)
        self.assertGreater(len(cases), 150)
        for name, candidate in cases:
            with self.subTest(name=name):
                with self.assertRaises(EvidenceValidationError):
                    RUNNER._validate_successor_lock(
                        candidate,
                        verify_bound_bytes=False,
                        verify_plan_bytes=False,
                    )

    def test_successor_lock_rejects_illegal_genesis_and_parent_variants(self):
        lock = self._valid_lock()
        for parent in (
                None,
                {"lock_id": lock["lock_id"], "sha256": lock["body_sha256"]},
                {"lock_id": "s00-lock-" + "0" * 64, "sha256": "0" * 64},
                {"lock_id": RUNNER.OLD_LOCK_ID, "sha256": "0" * 64}):
            with self.subTest(parent=parent):
                base = {
                    key: copy.deepcopy(value)
                    for key, value in lock.items()
                    if key not in {"lock_id", "body_sha256"}
                }
                base["parent_lock"] = parent
                with self.assertRaises(EvidenceValidationError):
                    RUNNER._validate_successor_lock(
                        RUNNER._derived_lock_document(base),
                        verify_bound_bytes=False,
                        verify_plan_bytes=False,
                    )

    def test_combined_substituted_lock_cannot_write_evidence_or_decision(self):
        with tempfile.TemporaryDirectory(
                dir=REPO_ROOT, prefix=".s00-combined-lock-") as directory:
            directory = Path(directory)
            _, contract_path, _, lock, _ = _write_temp_contract_and_lock(
                directory
            )
            invalid = RUNNER._combined_substituted_lock(lock)
            invalid_path = directory / "combined-invalid.json"
            atomic_write_json(invalid_path, invalid)
            for action in ("evidence", "decision"):
                output = directory / f"out-{action}"
                with self.subTest(action=action):
                    with self.assertRaises(EvidenceValidationError):
                        if action == "evidence":
                            RUNNER._write_successor_evidence_to(
                                output,
                                command="unit-combined-invalid",
                                lock_path=invalid_path,
                                contract_path=contract_path,
                                verify_plan_bytes=False,
                            )
                        else:
                            RUNNER._write_successor_decision_to(
                                output,
                                output,
                                command="unit-combined-invalid",
                                lock_path=invalid_path,
                                contract_path=contract_path,
                                verify_plan_bytes=False,
                                independent_reproduction=False,
                            )
                    self.assertFalse(output.exists())

    def test_first_amendment_head_parent_and_old_bytes(self):
        binding = RUNNER._read_amendment_head()
        self.assertEqual(binding["amendment_id"], RUNNER.AMENDMENT_ID)
        old_hashes = RUNNER._assert_immutable_old_generation()
        self.assertEqual(old_hashes, RUNNER.IMMUTABLE_OLD_GENERATION)
        RUNNER._validate_genesis_lock()
        lock = self._valid_lock()
        self.assertEqual(
            lock["parent_lock"],
            {
                "lock_id": RUNNER.OLD_LOCK_ID,
                "sha256": RUNNER.OLD_LOCK_RAW_SHA256,
            },
        )
        with self.assertRaises(EvidenceValidationError):
            RUNNER._validate_artifact(
                PROTOCOL / "evidence/s00-neutrality.json",
                lock,
                "neutrality",
                lock_path=PROTOCOL
                / "locks/s00-foundation-lock-successor-001.json",
            )

    def test_neutrality_artifact_contains_recomputable_raw_trajectories_events_and_absence(self):
        observation = RUNNER.run_neutrality(
            DUMMY_LOCK, effective_lock_sha256=DUMMY_LOCK_SHA256
        )
        RUNNER._validate_neutrality_observation(observation)
        missing = copy.deepcopy(observation)
        missing["observer_on"].pop("events")
        with self.assertRaises(EvidenceValidationError):
            RUNNER._validate_neutrality_observation(missing)
        changed = copy.deepcopy(observation)
        changed["first_divergence"]["status"] = "divergence"
        with self.assertRaises(EvidenceValidationError):
            RUNNER._validate_neutrality_observation(changed)

    def test_resume_artifact_contains_raw_runs_events_manifests_boundary_and_absence(self):
        observation = RUNNER.run_resume(
            DUMMY_LOCK, effective_lock_sha256=DUMMY_LOCK_SHA256
        )
        RUNNER._validate_resume_observation(observation)
        mutations = []
        missing_manifest = copy.deepcopy(observation)
        missing_manifest["checkpoint_evidence"]["resumed"].pop()
        mutations.append(missing_manifest)
        missing_event = copy.deepcopy(observation)
        missing_event["resumed"]["events"].pop()
        mutations.append(missing_event)
        missing_boundary = copy.deepcopy(observation)
        missing_boundary["resume_boundary"].pop("prior_event_head")
        mutations.append(missing_boundary)
        duplicate = copy.deepcopy(observation)
        duplicate["resumed"]["events"][1]["event_id"] = (
            duplicate["resumed"]["events"][0]["event_id"]
        )
        mutations.append(duplicate)
        for candidate in mutations:
            with self.assertRaises(EvidenceValidationError):
                RUNNER._validate_resume_observation(candidate)

    def test_decision_requires_each_successor_evidence_class(self):
        with tempfile.TemporaryDirectory(
                dir=REPO_ROOT, prefix=".s00-decision-gate-") as directory:
            directory = Path(directory)
            _, contract_path, _, _, lock_path = (
                _write_temp_contract_and_lock(directory)
            )
            evidence = directory / "evidence"
            RUNNER._write_successor_evidence_to(
                evidence,
                command="unit-decision-gate",
                lock_path=lock_path,
                contract_path=contract_path,
                verify_plan_bytes=False,
            )
            for kind in (
                    "neutrality", "resume-parity", "reconciliation",
                    "lineage-fail-closed"):
                for mode in ("remove", "fail"):
                    with self.subTest(kind=kind, mode=mode):
                        candidate = directory / f"{kind}-{mode}"
                        shutil.copytree(evidence, candidate)
                        path = candidate / (
                            f"s00-{kind}-successor-001.json"
                        )
                        if mode == "remove":
                            path.unlink()
                        else:
                            artifact = strict_load_json(path)
                            artifact["criterion_status"] = "FAIL"
                            body = {
                                key: value for key, value in artifact.items()
                                if key not in {
                                    "artifact_id", "artifact_sha256"}
                            }
                            digest = canonical_sha256(body)
                            artifact["artifact_sha256"] = digest
                            artifact["artifact_id"] = f"s00-{kind}-{digest}"
                            path.unlink()
                            atomic_write_json(path, artifact)
                        output = directory / f"decision-{kind}-{mode}"
                        with self.assertRaises(EvidenceValidationError):
                            RUNNER._write_successor_decision_to(
                                output,
                                candidate,
                                command="unit-decision-negative",
                                lock_path=lock_path,
                                contract_path=contract_path,
                                verify_plan_bytes=False,
                                independent_reproduction=False,
                            )
                        self.assertFalse(output.exists())

    def test_old_decision_is_not_current_after_ledger_append(self):
        lock = self._valid_lock()
        with self.assertRaises(EvidenceValidationError):
            RUNNER._validate_decision(
                PROTOCOL / "evidence/s00-decision.json",
                lock,
                lock_path=PROTOCOL
                / "locks/s00-foundation-lock-successor-001.json",
            )

    def test_successor_reproduction_ignores_only_volatile_provenance(self):
        lock = self._valid_lock()
        lock_sha256 = canonical_sha256({"successor": "unit"})
        left_observation = RUNNER.run_neutrality(
            lock, effective_lock_sha256=lock_sha256
        )
        right_observation = RUNNER.run_neutrality(
            lock, effective_lock_sha256=lock_sha256
        )
        left = RUNNER._artifact(
            "neutrality", lock, lock_sha256, [],
            left_observation, "unit invocation A",
        )
        right = RUNNER._artifact(
            "neutrality", lock, lock_sha256, [],
            right_observation, "unit invocation B",
        )
        self.assertEqual(
            left["canonical_outcome_sha256"],
            right["canonical_outcome_sha256"],
        )
        self.assertEqual(left["observation"], right["observation"])
        self.assertNotEqual(
            left["artifact_sha256"], right["artifact_sha256"]
        )
        changed = copy.deepcopy(right_observation)
        changed["observer_on"]["raw_run"]["final_generation"] = 3
        with self.assertRaises(EvidenceValidationError):
            RUNNER._validate_neutrality_observation(changed)


if __name__ == "__main__":
    unittest.main()
