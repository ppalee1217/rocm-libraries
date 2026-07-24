# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from Tensile.ductile.m00.canonical import (
    MissingEvidenceError,
    ReportLifecycleError,
    load_json_strict,
    sha256_file,
)
from Tensile.ductile.m00.artifacts import ChecksumManifest
from Tensile.ductile.m00.report import validate_report_gate
from Tensile.ductile.m00.runner import (
    _resume_bundle,
    run_differential,
    verify_run,
)


REPO = Path(__file__).resolve().parents[7]
PROTOCOL = REPO / "study_docs/research/ductile-origami-warmstart/protocol"
CONTRACT = PROTOCOL / "experiment-contract.yaml"
FINAL_REPORT = REPO / (
    "study_docs/research/ductile-origami-warmstart/reports/"
    "m00-study-contract-observability-report.md"
)


@unittest.skipUnless(
    (PROTOCOL / "protocol-lock.json").exists(),
    "protocol lock is initialized after pre-lock tests",
)
class TestRunnerEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.output = cls.root / "fresh-differential"
        run_differential(CONTRACT, cls.output)
        cls.attestation = cls.root / "self-check.json"
        verify_run(CONTRACT, cls.output, cls.attestation)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_all_differentials_and_resume_pass(self):
        summary = load_json_strict(
            self.output / "differential-summary.json"
        )
        self.assertEqual("PASS", summary["overall"])
        self.assertFalse(summary["instrumentation_falsified"])
        self.assertTrue(all(summary["comparisons"].values()))
        self.assertIn("fixed_off_repeat", summary["comparisons"])
        self.assertIn(
            "continuous_durable_resume_equivalence",
            summary["comparisons"],
        )

    def test_bundles_have_raw_artifacts_checksums_and_no_probes(self):
        bundles = sorted((self.output / "bundles").iterdir())
        self.assertEqual(11, len(bundles))
        for bundle in bundles:
            with self.subTest(bundle=bundle.name):
                self.assertTrue((bundle / "checksums.sha256").is_file())
                self.assertTrue((bundle / "summary.json").is_file())
                self.assertTrue((bundle / "ga-events.jsonl").is_file())
                self.assertTrue(
                    (bundle / "benchmark-observations.jsonl").is_file()
                )
                environment = load_json_strict(
                    bundle / "environment.json"
                )
                self.assertFalse(environment["gpu_probed"])
                self.assertFalse(environment["rocm_probed"])

    def test_observer_off_is_explicit_and_on_is_event_stream(self):
        off = load_json_strict(
            self.output / "bundles/fixed-off-a/observer-events.jsonl"
        )
        self.assertEqual("disabled", off["observer"])
        first_on = (
            self.output / "bundles/fixed-on/observer-events.jsonl"
        ).read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(0, json.loads(first_on)["sequence"])

    def test_self_check_is_not_independent_attestation(self):
        attestation = load_json_strict(self.attestation)
        self.assertEqual("implementer-self-check",
                         attestation["issuer_role"])
        self.assertEqual("BLOCKED", attestation["overall"])
        self.assertEqual(
            "UNVERIFIED",
            attestation["criteria"]["M00.ACC.SPLIT-GUARD"],
        )
        self.assertFalse(FINAL_REPORT.exists())

    def test_resume_is_cross_process_durable_and_lineage_bound(self):
        commands = load_json_strict(
            self.output / "differential-command-log.json"
        )["commands"]
        names = [item["name"] for item in commands]
        for mode in ("off", "on"):
            name = f"resume-durable-{mode}"
            self.assertIn(f"{name}-interrupt", names)
            self.assertIn(f"{name}-resume", names)
            state = self.output / "interruptions" / name
            final = self.output / "bundles" / name
            interrupted_manifest = load_json_strict(
                state / "run-manifest.json"
            )
            resumed_manifest = load_json_strict(
                final / "run-manifest.json"
            )
            self.assertFalse(interrupted_manifest["complete"])
            self.assertEqual("interrupted",
                             interrupted_manifest["run_kind"])
            self.assertFalse((state / "summary.json").exists())
            self.assertFalse((state / "trajectory.json").exists())
            self.assertTrue(resumed_manifest["complete"])
            self.assertEqual("resumed", resumed_manifest["run_kind"])
            self.assertEqual(
                interrupted_manifest["run_id"],
                resumed_manifest["run_id"],
            )
            metadata = load_json_strict(
                final / "checkpoints/ga.checkpoint.metadata.json"
            )
            lineage = metadata["protocol_lineage"]
            for key in (
                    "contract_sha256", "effective_contract_sha256",
                    "split_registry_sha256",
                    "baseline_registry_sha256",
                    "revision_registry_sha256",
                    "protocol_lock_sha256", "source_set_sha256"):
                self.assertRegex(lineage[key], r"^[0-9a-f]{64}$")
            self.assertEqual(
                sha256_file(state / "checksums.sha256"),
                resumed_manifest["resume_from_sha256"],
            )

    def test_integrated_adversarial_ledger_exact_oracle(self):
        summary = load_json_strict(
            self.output / "adversarial/adversarial-summary.json"
        )
        self.assertEqual("PASS", summary["overall"])
        self.assertTrue(summary["continuous_resume_parity"])
        self.assertTrue(summary["observational_run_ids_unique"])
        oracle = summary["oracle"]
        self.assertEqual(6, oracle["proposed_candidates"])
        self.assertEqual(4, oracle["valid_unique"])
        self.assertEqual(4, oracle["compile_attempts"])
        self.assertEqual(1, oracle["compile_failures"])
        self.assertEqual(3, oracle["benchmark_attempts"])
        self.assertEqual(1, oracle["benchmark_failures"])
        self.assertEqual(3, oracle["candidate_shape_samples"])
        self.assertEqual(2, oracle[
            "ductile_legacy_positive_candidate_evals"
        ])
        self.assertEqual(1, oracle["complete_candidate_evals"])
        self.assertEqual(1, oracle["partial_candidate_evals"])
        self.assertEqual({
            "invalid": 1, "duplicate": 1, "compile_failed": 1,
            "benchmark_failed": 1, "complete": 1, "partial": 1,
        }, oracle["terminal_counts"])
        expected_classifications = [
            "complete", "invalid", "duplicate", "compile_failed",
            "benchmark_failed", "partial",
        ]
        for name in ("continuous", "resumed"):
            bundle = self.output / "adversarial/bundles" / name
            raw_summary = load_json_strict(bundle / "summary.json")
            self.assertEqual(4, raw_summary["valid_unique"])
            self.assertEqual(8, raw_summary["subprocess_invocations"])
            trajectory = load_json_strict(bundle / "trajectory.json")
            self.assertEqual(
                expected_classifications,
                trajectory["terminal_classifications"],
            )
            events = [
                json.loads(line) for line in
                (bundle / "ga-events.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            duplicate = next(
                item["payload"] for item in events
                if item["kind"] == "candidate_terminal" and
                item["payload"]["candidate_id"] == "p2"
            )
            p0_generated = next(
                load_json_strict(path)["candidates"][0]
                for path in sorted(
                    (bundle / "generated-inputs").glob(
                        "invocation-*.json"
                    )
                )
                if load_json_strict(path)["candidates"][0][
                    "candidate_id"
                ] == "p0"
            )
            self.assertEqual("p0", duplicate[
                "duplicate_of_candidate_id"
            ])
            self.assertEqual(p0_generated["config"], duplicate["config"])
            self.assertEqual(
                p0_generated["config_id"], duplicate["config_id"]
            )
            self.assertFalse(any(
                load_json_strict(path)["candidates"][0][
                    "candidate_id"
                ] == "p2"
                for path in (bundle / "generated-inputs").glob(
                    "invocation-*.json"
                )
            ))

    def test_durable_resume_stale_lineage_fails_closed(self):
        source = (
            self.output / "interruptions/resume-durable-off"
        )
        stale = self.root / "stale-resume-state"
        shutil.copytree(source, stale)
        state_path = stale / "resume-state.json"
        state = load_json_strict(state_path)
        state["protocol_lineage"]["source_set_sha256"] = "0" * 64
        state_path.write_text(
            json.dumps(state, sort_keys=True, separators=(",", ":")) +
            "\n", encoding="utf-8",
        )
        (stale / "checksums.sha256").unlink()
        ChecksumManifest.write(stale)
        with self.assertRaisesRegex(
                MissingEvidenceError, "lineage"):
            _resume_bundle(
                contract_path=CONTRACT,
                state_root=stale,
                output=self.root / "must-not-resume",
            )
        self.assertFalse((self.root / "must-not-resume").exists())

    def test_existing_output_and_attestation_are_never_overwritten(self):
        with self.assertRaisesRegex(
                MissingEvidenceError, "already exists"):
            run_differential(CONTRACT, self.output)
        with self.assertRaisesRegex(
                MissingEvidenceError, "already exists"):
            verify_run(
                CONTRACT, self.output, self.attestation
            )

    def test_independent_attestation_requires_direct_criterion_evidence(self):
        target = self.root / "must-not-overclaim.json"
        with self.assertRaisesRegex(
                MissingEvidenceError, "criterion-specific"):
            verify_run(
                CONTRACT, self.output, target,
                issuer_role="independent-verifier",
            )
        self.assertFalse(target.exists())

    def test_status_mismatch_rejects_minting_and_report_gate(self):
        verifier_root = REPO / (
            "agent_run/260724-ductile-origami-warmstart-sequential/"
            "milestones/m00/evidence/verifier"
        )
        verifier_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
                prefix="criterion-binding-", dir=verifier_root) as temporary:
            root = Path(temporary)
            actual = root / "actual"
            shutil.copytree(self.output, actual)
            probe = actual / "differential-summary.json"
            lock_path = PROTOCOL / "protocol-lock.json"
            lock = load_json_strict(lock_path)
            source_sha = lock["m00_source_set_sha256"]
            lock_sha = sha256_file(lock_path)
            statuses = {
                "M00.ACC.OBS-SEMANTICS": "PASS",
                "M00.ACC.RECONCILE": "PASS",
                "M00.ACC.SPLIT-GUARD": "PASS",
                "M00.ACC.BASELINE-GUARD": "PASS",
                "M00.ACC.CONTRACT-LOCK": "PASS",
                "M00.FAL.INSTRUMENTATION": False,
                "M00.STOP.MISSING-EVIDENCE": False,
            }

            def criterion_item(index, criterion, artifact_status):
                fresh = [{
                    "path": str(probe),
                    "sha256": sha256_file(probe),
                }]
                artifact = root / f"criterion-{index:02d}.json"
                artifact.write_text(json.dumps({
                    "schema_version": "1.0",
                    "criterion": criterion,
                    "status": artifact_status,
                    "source_set_sha256": source_sha,
                    "protocol_lock_sha256": lock_sha,
                    "fresh_evidence": fresh,
                }, sort_keys=True), encoding="utf-8")
                return {
                    "status": statuses[criterion],
                    "artifact_path": str(artifact),
                    "artifact_sha256": sha256_file(artifact),
                    "source_set_sha256": source_sha,
                    "protocol_lock_sha256": lock_sha,
                    "fresh_evidence": fresh,
                }

            evidence = {
                criterion: criterion_item(
                    index, criterion, status
                )
                for index, (criterion, status) in enumerate(
                    statuses.items()
                )
            }

            def write_document(path, criteria):
                path.write_text(json.dumps({
                    "schema_version": "1.0",
                    "criteria": criteria,
                    "root_causes": [],
                    "required_fixes": [],
                    "evidence_gaps": [],
                }, sort_keys=True), encoding="utf-8")

            valid_document = root / "valid-criteria.json"
            write_document(valid_document, evidence)
            valid_attestation = root / "valid-attestation.json"
            verify_run(
                CONTRACT, actual, valid_attestation,
                issuer_role="independent-verifier",
                criteria_evidence_path=valid_document,
            )
            self.assertEqual(
                "PASS", load_json_strict(valid_attestation)["overall"]
            )
            validate_report_gate(
                CONTRACT, valid_attestation, repo_root=REPO
            )

            mismatch_evidence = json.loads(json.dumps(evidence))
            mismatch_evidence["M00.ACC.RECONCILE"] = criterion_item(
                99, "M00.ACC.RECONCILE", "FAIL"
            )
            mismatch_document = root / "mismatch-criteria.json"
            write_document(mismatch_document, mismatch_evidence)
            must_not_exist = root / "mismatch-attestation.json"
            with self.assertRaisesRegex(
                    MissingEvidenceError, "stale or mismatched"):
                verify_run(
                    CONTRACT, actual, must_not_exist,
                    issuer_role="independent-verifier",
                    criteria_evidence_path=mismatch_document,
                )
            self.assertFalse(must_not_exist.exists())

            handcrafted = load_json_strict(valid_attestation)
            handcrafted["criterion_evidence"][
                "M00.ACC.RECONCILE"
            ] = mismatch_evidence["M00.ACC.RECONCILE"]
            handcrafted_path = root / "handcrafted-mismatch.json"
            handcrafted_path.write_text(
                json.dumps(handcrafted, sort_keys=True),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                    ReportLifecycleError, "content mismatch"):
                validate_report_gate(
                    CONTRACT, handcrafted_path, repo_root=REPO
                )
            self.assertFalse(FINAL_REPORT.exists())


if __name__ == "__main__":
    unittest.main()
