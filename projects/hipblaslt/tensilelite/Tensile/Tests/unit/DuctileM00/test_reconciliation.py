# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from Tensile.ductile.m00.artifacts import (
    ChecksumManifest,
    RunBundleWriter,
    generated_input_inventory,
)
from Tensile.ductile.m00.canonical import (
    ContractError,
    MissingEvidenceError,
    canonical_json_text,
    sha256_bytes,
)
from Tensile.ductile.m00.contract import ContractStore
from Tensile.ductile.m00.reconcile import (
    RawReconciler,
    verify_complete_fitness_vector,
    verify_terminal_classifications,
)
from Tensile.ductile.m00.runner import (
    _ledger_candidates,
    _run_bundle,
    run_adversarial_ledger,
)


REPO = Path(__file__).resolve().parents[7]
PROTOCOL = REPO / "study_docs/research/ductile-origami-warmstart/protocol"
CONTRACT = PROTOCOL / "experiment-contract.yaml"


def observations():
    result = []
    for candidate_id, values in (("c0", (1.0, 2.0)), ("c1", (3.0, 4.0))):
        for shape_id, value in zip(("s0", "s1"), values):
            result.append({
                "candidate_id": candidate_id,
                "shape_id": shape_id,
                "outcome": "success",
                "value": value,
            })
    return result


def vector():
    matrix = np.asarray([[1.0, 3.0], [2.0, 4.0]], dtype=np.float64)
    return {
        "candidate_ids": ["c0", "c1"],
        "shape_ids": ["s0", "s1"],
        "dtype": matrix.dtype.str,
        "shape": list(matrix.shape),
        "values": matrix.tolist(),
        "data_sha256": sha256_bytes(matrix.tobytes(order="C")),
    }


class TestFitnessVector(unittest.TestCase):
    def test_adversarial_candidate_identity_oracle_is_exact(self):
        candidates = _ledger_candidates(ContractStore(CONTRACT))
        self.assertEqual(
            [
                "complete", "invalid", "duplicate", "compile_failed",
                "benchmark_failed", "partial",
            ],
            [item["classification"] for item in candidates],
        )
        self.assertEqual(
            candidates[0]["config"], candidates[2]["config"]
        )
        self.assertEqual(
            candidates[0]["config_id"], candidates[2]["config_id"]
        )
        self.assertEqual(
            5, len({
                item["config_id"] for item in candidates
            })
        )

    def test_complete_vector_is_exact(self):
        self.assertEqual(
            (2, 0, 2),
            verify_complete_fitness_vector(
                ["c0", "c1"], ["s0", "s1"], observations(), vector()
            ),
        )

    def test_partial_vector_never_counts_complete(self):
        partial = observations()[:-1]
        with self.assertRaisesRegex(
                MissingEvidenceError, "incomplete"):
            verify_complete_fitness_vector(
                ["c0", "c1"], ["s0", "s1"], partial, vector()
            )

    def test_vector_order_value_and_hash_tampering_fail(self):
        cases = []
        wrong_order = vector()
        wrong_order["candidate_ids"] = ["c1", "c0"]
        cases.append(wrong_order)
        wrong_value = vector()
        wrong_value["values"][0][0] = 9.0
        cases.append(wrong_value)
        wrong_hash = vector()
        wrong_hash["data_sha256"] = "0" * 64
        cases.append(wrong_hash)
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(MissingEvidenceError):
                    verify_complete_fitness_vector(
                        ["c0", "c1"], ["s0", "s1"],
                        observations(), case,
                    )

    def test_adversarial_terminal_classification_matrix(self):
        cases = {
            "complete": (["success", "success"], "success", "success"),
            "invalid": (["invalid", "invalid"], None, None),
            "duplicate": (["duplicate", "duplicate"], None, None),
            "compile_failed": (
                ["compile_failed", "compile_failed"], "failure", None
            ),
            "benchmark_failed": (
                ["benchmark_failed", "benchmark_failed"],
                "success", "failure",
            ),
            "partial": (
                ["success", "partial"], "success", "failure"
            ),
        }
        for classification, (outcomes, compile_result,
                             benchmark_result) in cases.items():
            with self.subTest(classification=classification):
                records = [{
                    "candidate_id": "c0",
                    "shape_id": shape_id,
                    "outcome": outcome,
                } for shape_id, outcome in zip(("s0", "s1"), outcomes)]
                counts = verify_terminal_classifications(
                    ["c0"],
                    ["s0", "s1"],
                    records,
                    [{
                        "candidate_id": "c0",
                        "classification": classification,
                    }],
                    (
                        {"c0": compile_result}
                        if compile_result is not None else {}
                    ),
                    (
                        {"c0": benchmark_result}
                        if benchmark_result is not None else {}
                    ),
                )
                self.assertEqual(1, counts[classification])

        with self.assertRaisesRegex(
                MissingEvidenceError, "classification mismatch"):
            verify_terminal_classifications(
                ["c0"],
                ["s0", "s1"],
                [
                    {"candidate_id": "c0", "shape_id": "s0",
                     "outcome": "success"},
                    {"candidate_id": "c0", "shape_id": "s1",
                     "outcome": "success"},
                ],
                [{"candidate_id": "c0", "classification": "invalid"}],
                {"c0": "success"},
                {"c0": "success"},
            )

        duplicate_payload = {
            "candidate_id": "c0",
            "classification": "duplicate",
            "config_id": "1" * 64,
            "config": {"a": 1, "b": 2, "c": 0},
            "duplicate_of_candidate_id": "p0",
            "duplicate_of_config_id": "1" * 64,
        }
        counts = verify_terminal_classifications(
            ["c0"], ["s0", "s1"], [], [duplicate_payload], {}, {}
        )
        self.assertEqual(1, counts["duplicate"])
        matrix = np.asarray([[-1.0], [-1.0]], dtype=np.float64)
        self.assertEqual(
            (0, 0, 0),
            verify_complete_fitness_vector(
                ["c0"], ["s0", "s1"], [], {
                    "candidate_ids": ["c0"],
                    "shape_ids": ["s0", "s1"],
                    "dtype": matrix.dtype.str,
                    "shape": list(matrix.shape),
                    "values": matrix.tolist(),
                    "data_sha256": sha256_bytes(matrix.tobytes(order="C")),
                },
                allow_partial=True,
                zero_cost_candidate_ids={"c0"},
            ),
        )

    def test_artifact_root_and_path_containment_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            writer = RunBundleWriter(parent / "fresh")
            with self.assertRaises(MissingEvidenceError):
                writer.write_text("../escape", "no")
            with self.assertRaises(MissingEvidenceError):
                RunBundleWriter(parent / "fresh")
            (writer.root / "linked").symlink_to(parent)
            with self.assertRaises(MissingEvidenceError):
                writer.write_text("linked/escape", "no")

    def test_generated_input_inventory_is_strict_and_layout_typed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for kind, name in (
                    ("generation", "generation-0001.json"),
                    ("invocation", "invocation-0001.json")):
                case = root / kind
                (case / "generated-inputs").mkdir(parents=True)
                (case / "generated-inputs" / name).write_text(
                    "{}\n", encoding="utf-8"
                )
                actual_kind, files = generated_input_inventory(case)
                self.assertEqual(kind, actual_kind)
                self.assertEqual([name], [path.name for path in files])

            missing = root / "missing"
            missing.mkdir()
            with self.assertRaisesRegex(
                    MissingEvidenceError, "directory is missing"):
                generated_input_inventory(missing)

            unknown = root / "unknown"
            (unknown / "generated-inputs").mkdir(parents=True)
            (unknown / "generated-inputs/arbitrary.json").write_text(
                "{}\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(
                    MissingEvidenceError, "unknown, empty, or mixed"):
                generated_input_inventory(unknown)

            mixed = root / "mixed"
            (mixed / "generated-inputs").mkdir(parents=True)
            for name in (
                    "generation-0001.json", "invocation-0001.json"):
                (mixed / "generated-inputs" / name).write_text(
                    "{}\n", encoding="utf-8"
                )
            with self.assertRaisesRegex(
                    MissingEvidenceError, "unknown, empty, or mixed"):
                generated_input_inventory(mixed)

    def test_raw_required_inventory_path_uses_typed_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "generated-inputs").mkdir()
            (root / "subprocess").mkdir()
            (root / "generated-inputs/generation-0000.json").write_text(
                "{}\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(
                    MissingEvidenceError, "required raw artifact missing"):
                RawReconciler(root, CONTRACT)._required(
                    expect_summary=False,
                    expect_checksums=False,
                )


@unittest.skipUnless(
    (PROTOCOL / "protocol-lock.json").exists(),
    "protocol lock is initialized after pre-lock tests",
)
class TestRawBundleNegativeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.bundle = cls.root / "source"
        _run_bundle(
            contract_path=CONTRACT,
            output=cls.bundle,
            scenario_id="fixed_horizon",
            observer_mode="off",
            run_kind="continuous",
        )
        cls.adversarial = cls.root / "adversarial"
        run_adversarial_ledger(CONTRACT, cls.adversarial)
        cls.on_bundle = cls.root / "source-on"
        _run_bundle(
            contract_path=CONTRACT,
            output=cls.on_bundle,
            scenario_id="fixed_horizon",
            observer_mode="on",
            run_kind="continuous",
        )

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def clone(self, name, *, source=None):
        target = self.root / name
        shutil.copytree(source or self.bundle, target)
        return target

    def rebuild_checksums(self, root):
        (root / "checksums.sha256").unlink()
        ChecksumManifest.write(root)

    def test_bundle_reconciles_from_raw(self):
        summary = RawReconciler(self.bundle, CONTRACT).reconcile()
        self.assertTrue(summary.complete)
        self.assertEqual(
            summary.complete_candidate_evals,
            summary.ductile_legacy_positive_candidate_evals,
        )

    def test_missing_event_observation_and_artifacts_fail_closed(self):
        cases = {
            "event": lambda root: (
                root / "ga-events.jsonl"
            ).write_text(
                "\n".join(
                    (root / "ga-events.jsonl").read_text(
                        encoding="utf-8"
                    ).splitlines()[1:]
                ) + "\n",
                encoding="utf-8",
            ),
            "observation": lambda root: (
                root / "benchmark-observations.jsonl"
            ).write_text(
                "\n".join(
                    (root / "benchmark-observations.jsonl").read_text(
                        encoding="utf-8"
                    ).splitlines()[:-1]
                ) + "\n",
                encoding="utf-8",
            ),
            "stdout": lambda root: (
                root / "subprocess/invocation-0001.stdout.jsonl"
            ).unlink(),
            "stderr": lambda root: (
                root / "subprocess/invocation-0001.stderr.txt"
            ).unlink(),
            "generated": lambda root: (
                root / "generated-inputs/generation-0001.json"
            ).unlink(),
            "checkpoint": lambda root: (
                root / "checkpoints/ga.checkpoint"
            ).unlink(),
            "run_closure": lambda root: (
                root / "ga-events.jsonl"
            ).write_text(
                "\n".join(
                    (root / "ga-events.jsonl").read_text(
                        encoding="utf-8"
                    ).splitlines()[:-1]
                ) + "\n",
                encoding="utf-8",
            ),
            "manifest": lambda root: (
                root / "run-manifest.json"
            ).unlink(),
            "environment": lambda root: (
                root / "environment.json"
            ).unlink(),
            "search_space": lambda root: (
                root / "search-space.json"
            ).unlink(),
            "observer": lambda root: (
                root / "observer-events.jsonl"
            ).unlink(),
            "checkpoint_metadata": lambda root: (
                root / "checkpoints/ga.checkpoint.metadata.json"
            ).unlink(),
            "trajectory": lambda root: (
                root / "trajectory.json"
            ).unlink(),
            "summary": lambda root: (
                root / "summary.json"
            ).unlink(),
            "base_contract": lambda root: (
                root / "contract/experiment-contract.yaml"
            ).unlink(),
            "effective_contract": lambda root: (
                root / "contract/effective-contract.json"
            ).unlink(),
            "shape_registry": lambda root: (
                root / "contract/shape-registry.csv"
            ).unlink(),
            "baseline_registry": lambda root: (
                root / "contract/baseline-registry.json"
            ).unlink(),
            "revision_registry": lambda root: (
                root / "contract/revision-registry.json"
            ).unlink(),
            "protocol_lock": lambda root: (
                root / "contract/protocol-lock.json"
            ).unlink(),
            "amendment_chain": lambda root: (
                root / "contract/amendment-chain.jsonl"
            ).unlink(),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                root = self.clone(name)
                mutate(root)
                self.rebuild_checksums(root)
                with self.assertRaises(MissingEvidenceError):
                    RawReconciler(root, CONTRACT).reconcile()

    def test_missing_enabled_observer_event_fails_closed(self):
        root = self.clone("observer-event", source=self.on_bundle)
        path = root / "observer-events.jsonl"
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
        ]
        records = [
            record for record in records
            if record["kind"] != "final_champion"
        ]
        for sequence, record in enumerate(records):
            record["sequence"] = sequence
            record["event_id"] = f"observer-{sequence:06d}"
        path.write_text(
            "\n".join(canonical_json_text(record) for record in records) +
            "\n",
            encoding="utf-8",
        )
        self.rebuild_checksums(root)
        with self.assertRaisesRegex(MissingEvidenceError, "observer"):
            RawReconciler(root, CONTRACT).reconcile()

    def test_checksum_tampering_fails_before_reconciliation(self):
        root = self.clone("checksum")
        path = root / "subprocess/invocation-0001.stderr.txt"
        path.write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(MissingEvidenceError, "checksum"):
            RawReconciler(root, CONTRACT).reconcile()

    def test_causal_candidate_set_tampering_is_detected(self):
        root = self.clone("causal")
        path = root / "ga-events.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines]
        for record in records:
            if record["kind"] == "generation_finished":
                payload = record["payload"]
                payload["candidate_set_sha256"] = "0" * 64
                record["payload"] = payload
                record["payload_sha256"] = sha256_bytes(
                    canonical_json_text(payload).encode("utf-8")
                )
                break
        path.write_text(
            "\n".join(canonical_json_text(record) for record in records) +
            "\n",
            encoding="utf-8",
        )
        self.rebuild_checksums(root)
        with self.assertRaisesRegex(
                MissingEvidenceError, "candidate-set"):
            RawReconciler(root, CONTRACT).reconcile()

    def test_terminal_checkpoint_and_generated_input_tampering_is_detected(self):
        terminal_root = self.clone("terminal-causal")
        event_path = terminal_root / "ga-events.jsonl"
        records = [
            json.loads(line)
            for line in event_path.read_text(encoding="utf-8").splitlines()
        ]
        for record in records:
            if record["kind"] == "candidate_terminal":
                record["payload"]["classification"] = "invalid"
                record["payload_sha256"] = sha256_bytes(
                    canonical_json_text(record["payload"]).encode("utf-8")
                )
                break
        event_path.write_text(
            "\n".join(canonical_json_text(record) for record in records) +
            "\n",
            encoding="utf-8",
        )
        self.rebuild_checksums(terminal_root)
        with self.assertRaisesRegex(
                MissingEvidenceError, "classification mismatch"):
            RawReconciler(terminal_root, CONTRACT).reconcile()

        checkpoint_root = self.clone("checkpoint-causal")
        trajectory_path = checkpoint_root / "trajectory.json"
        trajectory = json.loads(
            trajectory_path.read_text(encoding="utf-8")
        )
        trajectory["checkpoint_sha256"] = "0" * 64
        trajectory_path.write_text(
            canonical_json_text(trajectory) + "\n", encoding="utf-8"
        )
        self.rebuild_checksums(checkpoint_root)
        with self.assertRaisesRegex(
                MissingEvidenceError, "trajectory closure"):
            RawReconciler(checkpoint_root, CONTRACT).reconcile()

        generated_root = self.clone("generated-causal")
        generated_path = (
            generated_root / "generated-inputs/generation-0001.json"
        )
        generated = json.loads(
            generated_path.read_text(encoding="utf-8")
        )
        generated["candidates"][0]["config"]["a"] = 999
        generated_path.write_text(
            canonical_json_text(generated) + "\n", encoding="utf-8"
        )
        self.rebuild_checksums(generated_root)
        with self.assertRaises(MissingEvidenceError):
            RawReconciler(generated_root, CONTRACT).reconcile()

    def test_unknown_summary_key_is_rejected(self):
        root = self.clone("summary-shape")
        path = root / "summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["invented"] = 0
        path.write_text(canonical_json_text(summary) + "\n",
                        encoding="utf-8")
        self.rebuild_checksums(root)
        with self.assertRaises(Exception):
            RawReconciler(root, CONTRACT).reconcile()

    def test_missing_checksum_manifest_is_rejected(self):
        root = self.clone("missing-checksum")
        (root / "checksums.sha256").unlink()
        with self.assertRaisesRegex(MissingEvidenceError, "checksum"):
            RawReconciler(root, CONTRACT).reconcile()

    def test_unknown_mixed_and_extra_generated_inputs_reject(self):
        for name, filename in (
                ("unknown-generated", "arbitrary.json"),
                ("mixed-generated", "invocation-9999.json")):
            root = self.clone(name)
            (root / "generated-inputs" / filename).write_text(
                "{}\n", encoding="utf-8"
            )
            self.rebuild_checksums(root)
            with self.assertRaisesRegex(
                    MissingEvidenceError, "generated-input"):
                RawReconciler(root, CONTRACT).reconcile()

        extra = self.clone(
            "extra-adversarial-generated",
            source=self.adversarial / "bundles/continuous",
        )
        source = extra / "generated-inputs/invocation-0001.json"
        (extra / "generated-inputs/invocation-9999.json").write_bytes(
            source.read_bytes()
        )
        self.rebuild_checksums(extra)
        with self.assertRaisesRegex(
                MissingEvidenceError, "generated-input"):
            RawReconciler(extra, CONTRACT).reconcile()

    def test_adversarial_identity_duplicate_and_valid_unique_tamper_reject(self):
        source = self.adversarial / "bundles/continuous"

        def mutate_terminal(name, mutate,
                            expected=MissingEvidenceError):
            root = self.clone(name, source=source)
            path = root / "ga-events.jsonl"
            records = [
                json.loads(line) for line in
                path.read_text(encoding="utf-8").splitlines()
            ]
            terminals = {
                item["payload"]["candidate_id"]: item
                for item in records
                if item["kind"] == "candidate_terminal"
            }
            mutate(terminals)
            for item in terminals.values():
                item["payload_sha256"] = sha256_bytes(
                    canonical_json_text(item["payload"]).encode("utf-8")
                )
            path.write_text(
                "\n".join(canonical_json_text(item) for item in records) +
                "\n", encoding="utf-8",
            )
            self.rebuild_checksums(root)
            with self.assertRaises(expected):
                RawReconciler(root, CONTRACT).reconcile()

        mutate_terminal(
            "semantic-permutation",
            lambda terminals: (
                terminals["p0"]["payload"].update(
                    classification="invalid"
                ),
                terminals["p1"]["payload"].update(
                    classification="complete"
                ),
            ),
        )

        def different_config(terminals):
            payload = terminals["p2"]["payload"]
            payload["config"]["a"] = 2
            changed_id = sha256_bytes(
                canonical_json_text(payload["config"]).encode("utf-8")
            )
            payload["config_id"] = changed_id
            payload["duplicate_of_config_id"] = changed_id

        mutate_terminal("duplicate-config-differs", different_config)
        mutate_terminal(
            "duplicate-reference-absent",
            lambda terminals: terminals["p2"]["payload"].pop(
                "duplicate_of_candidate_id"
            ),
            (MissingEvidenceError, ContractError),
        )
        mutate_terminal(
            "duplicate-reference-wrong",
            lambda terminals: terminals["p2"]["payload"].update(
                duplicate_of_candidate_id="p1"
            ),
        )
        mutate_terminal(
            "duplicate-reference-orphan",
            lambda terminals: terminals["p2"]["payload"].update(
                duplicate_of_candidate_id="p2"
            ),
        )

        for name, mutate in (
                ("valid-unique-omitted",
                 lambda summary: summary.pop("valid_unique")),
                ("valid-unique-poisoned",
                 lambda summary: summary.update(valid_unique=3))):
            root = self.clone(name, source=source)
            path = root / "summary.json"
            summary = json.loads(path.read_text(encoding="utf-8"))
            mutate(summary)
            path.write_text(
                canonical_json_text(summary) + "\n", encoding="utf-8"
            )
            self.rebuild_checksums(root)
            with self.assertRaises(MissingEvidenceError):
                RawReconciler(root, CONTRACT).reconcile()

    def test_duplicate_event_attempt_and_observation_ids_reject(self):
        event_root = self.clone("duplicate-event-id")
        event_path = event_root / "ga-events.jsonl"
        records = [
            json.loads(line) for line in
            event_path.read_text(encoding="utf-8").splitlines()
        ]
        records[1]["event_id"] = records[0]["event_id"]
        event_path.write_text(
            "\n".join(canonical_json_text(item) for item in records) +
            "\n", encoding="utf-8",
        )
        self.rebuild_checksums(event_root)
        with self.assertRaisesRegex(MissingEvidenceError, "event ID"):
            RawReconciler(event_root, CONTRACT).reconcile()

        observation_root = self.clone("duplicate-observation-id")
        observation_path = (
            observation_root / "benchmark-observations.jsonl"
        )
        observations = [
            json.loads(line) for line in
            observation_path.read_text(encoding="utf-8").splitlines()
        ]
        observations[1]["observation_id"] = observations[0][
            "observation_id"
        ]
        observation_path.write_text(
            "\n".join(canonical_json_text(item) for item in observations) +
            "\n", encoding="utf-8",
        )
        self.rebuild_checksums(observation_root)
        with self.assertRaisesRegex(MissingEvidenceError, "observation ID"):
            RawReconciler(observation_root, CONTRACT).reconcile()

        stage_root = self.clone("duplicate-stage-id")
        stage_path = stage_root / "ga-events.jsonl"
        records = [
            json.loads(line) for line in
            stage_path.read_text(encoding="utf-8").splitlines()
        ]
        first_stage = next(
            item["payload"]["stage_id"] for item in records
            if item["kind"] == "compile_started"
        )
        for item in records:
            if item["kind"] == "benchmark_started":
                item["payload"]["stage_id"] = first_stage
                item["payload_sha256"] = sha256_bytes(
                    canonical_json_text(item["payload"]).encode("utf-8")
                )
                break
        stage_path.write_text(
            "\n".join(canonical_json_text(item) for item in records) +
            "\n", encoding="utf-8",
        )
        self.rebuild_checksums(stage_root)
        with self.assertRaisesRegex(MissingEvidenceError, "stage attempt"):
            RawReconciler(stage_root, CONTRACT).reconcile()

    def test_adversarial_raw_rebuild_twice_and_missing_attempt_fail(self):
        expected = {
            "proposed_candidates": 6,
            "compile_attempts": 4,
            "compile_failures": 1,
            "benchmark_attempts": 3,
            "benchmark_failures": 1,
            "candidate_shape_samples": 3,
            "ductile_legacy_positive_candidate_evals": 2,
            "complete_candidate_evals": 1,
            "partial_candidate_evals": 1,
        }
        for bundle_name in ("continuous", "resumed"):
            source = self.adversarial / "bundles" / bundle_name
            rebuilt = []
            for suffix in ("a", "b"):
                target = self.clone(
                    f"ledger-{bundle_name}-{suffix}", source=source
                )
                (target / "summary.json").unlink()
                (target / "checksums.sha256").unlink()
                summary = RawReconciler(
                    target, CONTRACT
                ).reconcile(
                    verify_checksums=False, write_summary=True
                ).as_dict()
                rebuilt.append(summary)
            self.assertEqual(rebuilt[0], rebuilt[1])
            for key, value in expected.items():
                self.assertEqual(value, rebuilt[0][key])

        missing = self.clone(
            "ledger-missing-attempt",
            source=self.adversarial / "bundles/continuous",
        )
        (missing / "subprocess/invocation-0004.stdout.jsonl").unlink()
        self.rebuild_checksums(missing)
        with self.assertRaises(MissingEvidenceError):
            RawReconciler(missing, CONTRACT).reconcile()


if __name__ == "__main__":
    unittest.main()
