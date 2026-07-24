# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

import json
import tempfile
import unittest
from pathlib import Path

from Tensile.ductile.m00.canonical import (
    GuardError,
    MissingEvidenceError,
    ReportLifecycleError,
    load_json_strict,
    sha256_file,
)
from Tensile.ductile.m00.contract import (
    ContractStore,
    protected_path_union,
)
from Tensile.ductile.m00.report import (
    VerifierAttestation,
    render_attested_report,
    render_m00_report,
    validate_criterion_result_binding,
    verify_m00_report,
)
from Tensile.ductile.m00.runner import (
    _independent_criterion_claims,
    _repo_root,
    _tensilelite_root,
)
from Tensile.ductile.m00.scope import (
    M00ScopeGuard,
    verify_protected_path_hashes,
)


REPO = Path(__file__).resolve().parents[7]
PROTOCOL = REPO / "study_docs/research/ductile-origami-warmstart/protocol"
CONTRACT = PROTOCOL / "experiment-contract.yaml"
FINAL_REPORT = REPO / (
    "study_docs/research/ductile-origami-warmstart/reports/"
    "m00-study-contract-observability-report.md"
)
PROTECTED_SHA256 = {
    ".claude/skills/implement-verify-loop/SKILL.md":
        "a73c4d15464f3e05d814c546d87baa3373c14571b6bc4203032008a711c51c17",
    ".cursor/rules/hipblaslt-onboarding.mdc":
        "9d06b053858cdaa156d26b6e269183cf0fffb4aa188d364219f59d57d17dc885",
    ".cursor/skills/implement-verify-loop/SKILL.md":
        "a73c4d15464f3e05d814c546d87baa3373c14571b6bc4203032008a711c51c17",
    "CLAUDE.md":
        "64ec23b36e5a6c5909b9a08fd8edea2a194a56fc13ac37ffcc8991acb38eeff9",
    "AGENTS.md":
        "ff2a38432998a47a0da671ed7428b0034703478bf05fcc6d2a3ed7a384e5646e",
    ".agents/skills/design-discussion/SKILL.md":
        "413067e4c671e96dc08a5792da62f6f6858993184991df656daa960e32d5c79d",
    ".agents/skills/hipblaslt-code-trace/SKILL.md":
        "61eeffd07fbd66deaecd7799a927a8bfd522488aa5b5570ec598313968f4d053",
    ".agents/skills/implement-verify-loop/SKILL.md":
        "8b14344eefafb84b60a72eb5cf13ce1eb9ded139385fbd0abfda23533466aa59",
    ".agents/skills/learning-notes/SKILL.md":
        "e66f14f5acc33ded139de6b2589704028e02cf3b8d3c53e1c158f42f92483a84",
    ".agents/skills/learning-quiz/SKILL.md":
        "5093bfcdf82830be863ab2458097b96813615970de7972186d660913fe1ae86a",
    ".agents/skills/learning-roadmap-authoring/SKILL.md":
        "b9c7b7a28775f5f9da9232824607c513877e49d604b3ed2934775fc725301c5e",
}


def placeholder_criterion_evidence(criteria, root):
    return {
        key: {
            "status": value,
            "artifact_path": str(root / "probe.json"),
            "artifact_sha256": "0" * 64,
            "source_set_sha256": "0" * 64,
            "protocol_lock_sha256": "0" * 64,
            "fresh_evidence": [],
        }
        for key, value in criteria.items()
    }


class TestWhitelistShape(unittest.TestCase):
    def test_whitelist_has_exact_protected_and_conditional_groups(self):
        whitelist = load_json_strict(PROTOCOL / "m00-whitelist.json")
        self.assertEqual(
            set(PROTECTED_SHA256), set(whitelist["protected_paths"])
        )
        self.assertEqual(
            [FINAL_REPORT.relative_to(REPO).as_posix()],
            whitelist["conditional_report_paths"],
        )
        self.assertFalse(
            set(whitelist["protected_paths"]) &
            set(whitelist["implementation_paths"])
        )
        self.assertFalse(
            set(whitelist["protected_paths"]) &
            set(whitelist["source_set_paths"])
        )
        contract_protected = set(
            ContractStore(CONTRACT).base_contract["locks"][
                "protected_paths"
            ]
        )
        self.assertTrue(
            contract_protected.issubset(whitelist["protected_paths"])
        )
        self.assertNotIn(
            FINAL_REPORT.relative_to(REPO).as_posix(),
            whitelist["implementation_paths"],
        )

    def test_protected_union_and_hash_guard_fail_closed(self):
        self.assertEqual(
            ["a", "b"],
            protected_path_union(["a"], ["a", "b"]),
        )
        with self.assertRaisesRegex(GuardError, "subset"):
            protected_path_union(["a"], ["b"])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a").write_bytes(b"a")
            (root / "b").write_bytes(b"b")
            hashes = {
                "a": sha256_file(root / "a"),
                "b": sha256_file(root / "b"),
            }
            verify_protected_path_hashes(root, hashes)
            (root / "a").write_bytes(b"changed")
            with self.assertRaisesRegex(GuardError, "protected path"):
                verify_protected_path_hashes(root, hashes)
            (root / "a").write_bytes(b"a")
            (root / "b").unlink()
            with self.assertRaisesRegex(GuardError, "protected path"):
                verify_protected_path_hashes(root, hashes)

    def test_all_authorized_protected_hashes_are_exact(self):
        self.assertEqual(
            PROTECTED_SHA256,
            {
                relative: sha256_file(REPO / relative)
                for relative in PROTECTED_SHA256
            },
        )

    def test_downstream_paths_are_rejected_by_guard_classifier(self):
        forbidden = [
            "study_docs/research/x/m01/build.py",
            "projects/hipblaslt/tensilelite/Tensile/backends/gpu.py",
            "projects/hipblaslt/tensilelite/Tensile/BenchmarkProblems.py",
            "x/mapping.py",
            "x/schedule.py",
        ]
        for path in forbidden:
            with self.subTest(path=path):
                self.assertTrue(M00ScopeGuard._is_downstream(path))
        self.assertFalse(M00ScopeGuard._is_downstream(
            "projects/hipblaslt/tensilelite/Tensile/ductile/m00/scope.py"
        ))

    def test_final_report_is_absent_during_implementation(self):
        self.assertFalse(FINAL_REPORT.exists())

    def test_default_paths_spdx_and_dependency_declarations(self):
        store = ContractStore(CONTRACT)
        self.assertEqual(REPO, _repo_root(store))
        self.assertEqual(
            REPO / "projects/hipblaslt/tensilelite",
            _tensilelite_root(),
        )
        whitelist = load_json_strict(PROTOCOL / "m00-whitelist.json")
        header_paths = [
            REPO / relative for relative in whitelist["source_set_paths"]
            if relative.endswith(".py")
        ]
        header_paths.extend([
            REPO / (
                "projects/hipblaslt/tensilelite/Tensile/ductile/"
                "config/defaults.yaml"
            ),
            CONTRACT,
            REPO / "projects/hipblaslt/tensilelite/pyproject.toml",
        ])
        for path in header_paths:
            with self.subTest(path=path):
                lines = path.read_text(encoding="utf-8").splitlines()
                self.assertTrue(lines[0].startswith("# Copyright"))
                self.assertEqual(
                    "# SPDX-License-Identifier: MIT", lines[1]
                )
        pyproject = (
            REPO / "projects/hipblaslt/tensilelite/pyproject.toml"
        ).read_text(encoding="utf-8")
        requirements = (
            REPO / "projects/hipblaslt/tensilelite/requirements.txt"
        ).read_text(encoding="utf-8")
        self.assertEqual(1, pyproject.count('"jsonschema>=3.2"'))
        self.assertEqual(1, requirements.splitlines().count(
            "jsonschema>=3.2"
        ))
        m00_package = _tensilelite_root() / "Tensile/ductile/m00"
        for forbidden in (
                "analysis.py", "mapping.py", "guidance.py", "model.py",
                "schedule.py"):
            self.assertFalse((m00_package / forbidden).exists())

    def test_renderer_uses_exclusive_create_and_attested_text(self):
        data = {
            "overall": "PASS",
            "issuer": "isolated-independent-verifier",
            "run_root": "/isolated/evidence",
            "criteria": {
                "M00.ACC.OBS-SEMANTICS": "PASS",
                "M00.ACC.RECONCILE": "PASS",
                "M00.ACC.SPLIT-GUARD": "PASS",
                "M00.ACC.BASELINE-GUARD": "PASS",
                "M00.ACC.CONTRACT-LOCK": "PASS",
                "M00.FAL.INSTRUMENTATION": False,
                "M00.STOP.MISSING-EVIDENCE": False,
            },
            "root_causes": [],
            "required_fixes": [],
            "evidence_gaps": [],
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / FINAL_REPORT.relative_to(REPO)
            attestation = VerifierAttestation(data, root / "attestation.json")
            render_attested_report(attestation, output, output)
            with self.assertRaisesRegex(
                    ReportLifecycleError, "already exists"):
                render_attested_report(
                    attestation, output, output,
                )
            self.assertIn("Outcome: `PASS`",
                          output.read_text(encoding="utf-8"))
        self.assertFalse(FINAL_REPORT.exists())

    def test_direct_criterion_evidence_positive_negative_inconclusive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            probe = root / "probe.json"
            probe.write_text('{"direct":true}\n', encoding="utf-8")
            source_sha = "1" * 64
            lock_sha = "2" * 64
            lock = {"m00_source_set_sha256": source_sha}
            base_statuses = {
                "M00.ACC.OBS-SEMANTICS": "PASS",
                "M00.ACC.RECONCILE": "PASS",
                "M00.ACC.SPLIT-GUARD": "PASS",
                "M00.ACC.BASELINE-GUARD": "PASS",
                "M00.ACC.CONTRACT-LOCK": "PASS",
                "M00.FAL.INSTRUMENTATION": False,
                "M00.STOP.MISSING-EVIDENCE": False,
            }
            for expected, override in (
                    ("PASS", {}),
                    ("FAIL", {"M00.ACC.SPLIT-GUARD": "FAIL"}),
                    (
                        "INCONCLUSIVE",
                        {"M00.ACC.SPLIT-GUARD": "INCONCLUSIVE"},
                    )):
                statuses = {**base_statuses, **override}
                evidence = {}
                for index, (key, value) in enumerate(statuses.items()):
                    fresh = [{
                        "path": str(probe),
                        "sha256": sha256_file(probe),
                    }]
                    artifact = root / (
                        f"{expected.lower()}-criterion-{index:02d}.json"
                    )
                    artifact.write_text(json.dumps({
                        "schema_version": "1.0",
                        "criterion": key,
                        "status": value,
                        "source_set_sha256": source_sha,
                        "protocol_lock_sha256": lock_sha,
                        "fresh_evidence": fresh,
                    }), encoding="utf-8")
                    evidence[key] = {
                        "status": value,
                        "artifact_path": str(artifact),
                        "artifact_sha256": sha256_file(artifact),
                        "source_set_sha256": source_sha,
                        "protocol_lock_sha256": lock_sha,
                        "fresh_evidence": fresh,
                    }
                document = root / f"{expected.lower()}.json"
                nonpositive = expected != "PASS"
                document.write_text(json.dumps({
                    "schema_version": "1.0",
                    "criteria": evidence,
                    "root_causes": (
                        ["directly verified non-positive criterion"]
                        if nonpositive else []
                    ),
                    "required_fixes": [],
                    "evidence_gaps": [],
                }), encoding="utf-8")
                result = _independent_criterion_claims(
                    document, lock=lock, lock_sha256=lock_sha,
                    allowed_root=root,
                )
                self.assertEqual(expected, result[2])
                attestation = VerifierAttestation({
                    "overall": expected,
                    "issuer": "unit-verifier",
                    "run_root": str(root),
                    "criteria": statuses,
                    "root_causes": result[3],
                    "required_fixes": result[4],
                    "evidence_gaps": result[5],
                }, document)
                report = root / f"{expected.lower()}.md"
                render_attested_report(attestation, report, report)
                self.assertIn(
                    f"Outcome: `{expected}`",
                    report.read_text(encoding="utf-8"),
                )

            stale = json.loads((root / "pass.json").read_text())
            stale["criteria"]["M00.ACC.SPLIT-GUARD"][
                "artifact_sha256"
            ] = "0" * 64
            stale_path = root / "stale.json"
            stale_path.write_text(json.dumps(stale), encoding="utf-8")
            with self.assertRaisesRegex(
                    MissingEvidenceError, "stale or mismatched"):
                _independent_criterion_claims(
                    stale_path, lock=lock, lock_sha256=lock_sha,
                    allowed_root=root,
                )
            unverified = json.loads((root / "pass.json").read_text())
            unverified["criteria"]["M00.ACC.SPLIT-GUARD"][
                "status"
            ] = "UNVERIFIED"
            unverified_path = root / "unverified.json"
            unverified_path.write_text(
                json.dumps(unverified), encoding="utf-8"
            )
            with self.assertRaisesRegex(
                    MissingEvidenceError, "UNVERIFIED"):
                _independent_criterion_claims(
                    unverified_path, lock=lock, lock_sha256=lock_sha,
                    allowed_root=root,
                )

            mismatch = json.loads((root / "pass.json").read_text())
            item = mismatch["criteria"]["M00.ACC.RECONCILE"]
            artifact = Path(item["artifact_path"])
            result = json.loads(artifact.read_text())
            result["status"] = "FAIL"
            artifact.write_text(json.dumps(result), encoding="utf-8")
            item["artifact_sha256"] = sha256_file(artifact)
            mismatch_path = root / "status-content-mismatch.json"
            mismatch_path.write_text(json.dumps(mismatch), encoding="utf-8")
            with self.assertRaisesRegex(
                    MissingEvidenceError, "stale or mismatched"):
                _independent_criterion_claims(
                    mismatch_path, lock=lock, lock_sha256=lock_sha,
                    allowed_root=root,
                )

    def test_typed_criterion_result_rejects_untrusted_declarations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            authorized = root / "authorized"
            authorized.mkdir()
            evidence = authorized / "evidence.json"
            evidence.write_text('{"direct":true}\n', encoding="utf-8")
            source_sha = "1" * 64
            lock_sha = "2" * 64
            schema = PROTOCOL / "schemas/verifier-attestation.schema.json"

            def write_case(name, *,
                           result_override=None,
                           envelope_override=None):
                fresh = [{
                    "path": str(evidence),
                    "sha256": sha256_file(evidence),
                }]
                result = {
                    "schema_version": "1.0",
                    "criterion": "M00.ACC.RECONCILE",
                    "status": "PASS",
                    "source_set_sha256": source_sha,
                    "protocol_lock_sha256": lock_sha,
                    "fresh_evidence": fresh,
                }
                if result_override:
                    result_override(result)
                artifact = authorized / f"{name}.json"
                artifact.write_text(json.dumps(result), encoding="utf-8")
                envelope = {
                    "status": "PASS",
                    "artifact_path": str(artifact),
                    "artifact_sha256": sha256_file(artifact),
                    "source_set_sha256": source_sha,
                    "protocol_lock_sha256": lock_sha,
                    "fresh_evidence": fresh,
                }
                if envelope_override:
                    envelope_override(envelope)
                return envelope

            valid = write_case("valid")
            validate_criterion_result_binding(
                "M00.ACC.RECONCILE", valid,
                schema_path=schema,
                authorized_root=authorized,
                source_set_sha256=source_sha,
                protocol_lock_sha256=lock_sha,
            )

            cases = {
                "status-mismatch": write_case(
                    "status-mismatch",
                    result_override=lambda value: value.update(
                        status="FAIL"
                    ),
                ),
                "unknown-criterion": write_case(
                    "unknown-criterion",
                    result_override=lambda value: value.update(
                        criterion="M00.ACC.UNKNOWN"
                    ),
                ),
                "stale-source": write_case(
                    "stale-source",
                    result_override=lambda value: value.update(
                        source_set_sha256="0" * 64
                    ),
                    envelope_override=lambda value: value.update(
                        source_set_sha256="0" * 64
                    ),
                ),
                "extra-declaration": write_case(
                    "extra-declaration",
                    result_override=lambda value: value.update(extra=True),
                ),
                "evidence-list-mismatch": write_case(
                    "evidence-list-mismatch",
                    envelope_override=lambda value: value.update(
                        fresh_evidence=[]
                    ),
                ),
                "duplicate-evidence": write_case(
                    "duplicate-evidence",
                    result_override=lambda value: value.update(
                        fresh_evidence=value["fresh_evidence"] * 2
                    ),
                    envelope_override=lambda value: value.update(
                        fresh_evidence=value["fresh_evidence"] * 2
                    ),
                ),
                "missing-evidence": write_case(
                    "missing-evidence",
                    result_override=lambda value: value.update(
                        fresh_evidence=[{
                            "path": str(authorized / "missing.json"),
                            "sha256": "0" * 64,
                        }]
                    ),
                    envelope_override=lambda value: value.update(
                        fresh_evidence=[{
                            "path": str(authorized / "missing.json"),
                            "sha256": "0" * 64,
                        }]
                    ),
                ),
            }
            for name, envelope in cases.items():
                with self.subTest(name=name):
                    with self.assertRaises(ReportLifecycleError):
                        validate_criterion_result_binding(
                            "M00.ACC.RECONCILE", envelope,
                            schema_path=schema,
                            authorized_root=authorized,
                            source_set_sha256=source_sha,
                            protocol_lock_sha256=lock_sha,
                        )

            outside = root / "outside.json"
            outside.write_text('{"outside":true}\n', encoding="utf-8")
            escaped = write_case(
                "escaped-evidence",
                result_override=lambda value: value.update(
                    fresh_evidence=[{
                        "path": str(outside),
                        "sha256": sha256_file(outside),
                    }]
                ),
                envelope_override=lambda value: value.update(
                    fresh_evidence=[{
                        "path": str(outside),
                        "sha256": sha256_file(outside),
                    }]
                ),
            )
            with self.assertRaises(ReportLifecycleError):
                validate_criterion_result_binding(
                    "M00.ACC.RECONCILE", escaped,
                    schema_path=schema,
                    authorized_root=authorized,
                    source_set_sha256=source_sha,
                    protocol_lock_sha256=lock_sha,
                )

            symlink = authorized / "evidence-link.json"
            symlink.symlink_to(evidence)
            linked = write_case(
                "symlink-evidence",
                result_override=lambda value: value.update(
                    fresh_evidence=[{
                        "path": str(symlink),
                        "sha256": sha256_file(evidence),
                    }]
                ),
                envelope_override=lambda value: value.update(
                    fresh_evidence=[{
                        "path": str(symlink),
                        "sha256": sha256_file(evidence),
                    }]
                ),
            )
            with self.assertRaises(ReportLifecycleError):
                validate_criterion_result_binding(
                    "M00.ACC.RECONCILE", linked,
                    schema_path=schema,
                    authorized_root=authorized,
                    source_set_sha256=source_sha,
                    protocol_lock_sha256=lock_sha,
                )


@unittest.skipUnless(
    (PROTOCOL / "protocol-lock.json").exists(),
    "protocol lock is initialized after pre-lock tests",
)
class TestLiveScopeAndReportGate(unittest.TestCase):
    def test_live_implementation_scope_passes(self):
        result = M00ScopeGuard(REPO, CONTRACT).verify("implementation")
        self.assertTrue(result["final_report_absent"])
        self.assertEqual(11, len(result["protected_paths"]))

    def test_self_check_cannot_render_final_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attestation = root / "self.json"
            criteria = {
                "M00.ACC.OBS-SEMANTICS": "PASS",
                "M00.ACC.RECONCILE": "PASS",
                "M00.ACC.SPLIT-GUARD": "PASS",
                "M00.ACC.BASELINE-GUARD": "PASS",
                "M00.ACC.CONTRACT-LOCK": "PASS",
                "M00.FAL.INSTRUMENTATION": False,
                "M00.STOP.MISSING-EVIDENCE": False,
            }
            attestation.write_text(json.dumps({
                "schema_version": "1.0",
                "issuer_role": "implementer-self-check",
                "issuer": "unit-test",
                "issued_at": "2026-07-24T00:00:00Z",
                "overall": "PASS",
                "source_set_sha256": "0" * 64,
                "contract_sha256": "0" * 64,
                "effective_contract_sha256": "0" * 64,
                "protocol_lock_sha256": "0" * 64,
                "run_root": str(root),
                "bundle_checksum_manifest_sha256": "0" * 64,
                "differential_summary_sha256": "0" * 64,
                "criteria": criteria,
                "criterion_evidence":
                    placeholder_criterion_evidence(criteria, root),
                "root_causes": [],
                "required_fixes": [],
                "evidence_gaps": [],
            }), encoding="utf-8")
            output = root / "report.md"
            with self.assertRaisesRegex(
                    ReportLifecycleError, "independent"):
                render_m00_report(
                    CONTRACT, attestation, output, repo_root=REPO
                )
            self.assertFalse(output.exists())
            self.assertFalse(FINAL_REPORT.exists())

    def test_stale_independent_attestation_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attestation = root / "stale.json"
            criteria = {
                "M00.ACC.OBS-SEMANTICS": "PASS",
                "M00.ACC.RECONCILE": "PASS",
                "M00.ACC.SPLIT-GUARD": "PASS",
                "M00.ACC.BASELINE-GUARD": "PASS",
                "M00.ACC.CONTRACT-LOCK": "PASS",
                "M00.FAL.INSTRUMENTATION": False,
                "M00.STOP.MISSING-EVIDENCE": False,
            }
            attestation.write_text(json.dumps({
                "schema_version": "1.0",
                "issuer_role": "independent-verifier",
                "issuer": "unit-test",
                "issued_at": "2026-07-24T00:00:00Z",
                "overall": "PASS",
                "source_set_sha256": "0" * 64,
                "contract_sha256": "0" * 64,
                "effective_contract_sha256": "0" * 64,
                "protocol_lock_sha256": "0" * 64,
                "run_root": str(root),
                "bundle_checksum_manifest_sha256": "0" * 64,
                "differential_summary_sha256": "0" * 64,
                "criteria": criteria,
                "criterion_evidence":
                    placeholder_criterion_evidence(criteria, root),
                "root_causes": [],
                "required_fixes": [],
                "evidence_gaps": [],
            }), encoding="utf-8")
            with self.assertRaisesRegex(
                    ReportLifecycleError, "mismatch"):
                render_m00_report(
                    CONTRACT, attestation, root / "report.md",
                    repo_root=REPO,
                )
            self.assertFalse(FINAL_REPORT.exists())


if __name__ == "__main__":
    unittest.main()
