# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from Tensile.ductile.m00.canonical import M00Error
from Tensile.ductile.m00.registries import (
    BaselineRegistry,
    ShapeRegistry,
    authorize_shape_access,
    guarded_load_shape,
    render_baseline_claim,
)


REPO = Path(__file__).resolve().parents[7]
SCHEMAS = REPO / (
    "study_docs/research/ductile-origami-warmstart/protocol/schemas"
)
HEADER = (
    "shape_id,cluster_id,tile_id,dtype,transpose_a,transpose_b,m,n,k,"
    "batch,cohort,role,selection_provenance,source_sha256,sealed_at\n"
)


def shape_row(shape_id, cluster_id, role, *,
              m=16, n=16, k=16, batch=1,
              source_sha="a" * 64):
    cohort = "final_holdout" if role == "final_holdout" else "development"
    return (
        f"{shape_id},{cluster_id},tile-{shape_id},f16,N,T,{m},{n},{k},{batch},"
        f"{cohort},{role},unit-test,{source_sha},2026-07-24T00:00:00Z\n"
    )


class TestSplitGuards(unittest.TestCase):
    def registry(self, root, rows):
        path = root / "shapes.csv"
        path.write_text(HEADER + "".join(rows), encoding="utf-8")
        return ShapeRegistry(
            path, SCHEMAS / "shape-registry.schema.json"
        )

    def test_holdout_access_is_rejected_before_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry = self.registry(Path(temporary), [
                shape_row("holdout", "cluster-h", "final_holdout")
            ])
            with self.assertRaisesRegex(M00Error, "holdout"):
                authorize_shape_access(registry, ["holdout"])

    def test_shape_and_cluster_overlap_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry = self.registry(Path(temporary), [
                shape_row("judgment", "same-cluster",
                          "development_judgment"),
                shape_row("holdout", "same-cluster", "final_holdout"),
            ])
            with self.assertRaisesRegex(M00Error, "shape IDs"):
                registry.assert_disjoint(["judgment"], ["judgment"])
            with self.assertRaisesRegex(M00Error, "clusters"):
                registry.assert_disjoint(["judgment"], ["holdout"])

    def test_canonical_shape_overlap_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry = self.registry(Path(temporary), [
                shape_row(
                    "judgment", "cluster-j", "development_judgment"
                ),
                shape_row("holdout", "cluster-h", "final_holdout"),
            ])
            with self.assertRaisesRegex(M00Error, "canonical shapes"):
                registry.assert_disjoint(["judgment"], ["holdout"])

    def test_missing_duplicate_and_malformed_rows_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = self.registry(root, [
                shape_row("development", "cluster-a", "development")
            ])
            with self.assertRaisesRegex(M00Error, "not registered"):
                registry.resolve(["missing"])
            with self.assertRaises(M00Error):
                self.registry(root, [
                    shape_row("duplicate", "a", "development"),
                    shape_row("duplicate", "b", "development"),
                ])
            malformed = root / "malformed.csv"
            malformed.write_text(
                HEADER + shape_row("bad", "c", "development").replace(
                    ",16,16,16,1,", ",0,16,16,1,"
                ),
                encoding="utf-8",
            )
            with self.assertRaises(M00Error):
                ShapeRegistry(
                    malformed, SCHEMAS / "shape-registry.schema.json"
                )

    def test_disjoint_development_roles_are_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry = self.registry(Path(temporary), [
                shape_row("guide", "cluster-g", "development_guidance"),
                shape_row(
                    "judge", "cluster-j", "development_judgment", m=32
                ),
            ])
            rows = authorize_shape_access(registry, ["guide"])
            registry.assert_disjoint(["guide"], ["judge"])
        self.assertEqual("guide", rows[0]["shape_id"])

    def test_registry_hash_seal_and_role_precede_loader(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "shape.json"
            source.write_bytes(b"sealed-shape")
            source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
            registry = self.registry(root, [
                shape_row(
                    "guide", "cluster-g", "development_guidance",
                    source_sha=source_sha,
                )
            ])
            calls = []

            def loader(row, path):
                calls.append((row["shape_id"], path.name))
                return b"payload"

            with self.assertRaisesRegex(M00Error, "role mismatch"):
                guarded_load_shape(
                    registry, "guide", source_path=source,
                    required_role="final_holdout", loader=loader,
                )
            self.assertEqual([], calls)
            source.write_bytes(b"tampered")
            with self.assertRaisesRegex(M00Error, "source hash"):
                guarded_load_shape(
                    registry, "guide", source_path=source,
                    required_role="development_guidance", loader=loader,
                )
            self.assertEqual([], calls)
            source.write_bytes(b"sealed-shape")
            self.assertEqual(
                b"payload",
                guarded_load_shape(
                    registry, "guide", source_path=source,
                    required_role="development_guidance", loader=loader,
                ),
            )
            self.assertEqual([("guide", "shape.json")], calls)


class TestBaselineGuards(unittest.TestCase):
    def write_registry(self, root, entries):
        path = root / "baseline.json"
        path.write_text(json.dumps({
            "schema_version": "1.0", "entries": entries
        }), encoding="utf-8")
        return BaselineRegistry(
            path, SCHEMAS / "baseline-registry.schema.json"
        )

    @staticmethod
    def entry(kind, evidence_sha, owner_sha=None):
        return {
            "baseline_id": "baseline-one",
            "source_kind": kind,
            "generator_revision": "1" * 40,
            "fork_params_sha256": "2" * 64,
            "weights_sha256": "3" * 64,
            "evidence_artifacts": [{
                "path": "evidence.raw",
                "sha256": evidence_sha,
                "evidence_type": "raw_artifact",
            }],
            "owner_attestation": (
                {"path": "owner.json", "sha256": owner_sha}
                if owner_sha is not None else None
            ),
            "allowed_claim_scope": ["observability_only"],
            "claim_template_id": (
                "original-tuningdriver-v1"
                if kind == "original_tuningdriver"
                else "geko-proxy-v1"
            ),
            "protocol_lock_sha256": "4" * 64,
        }

    def test_empty_canonical_registry_cannot_make_original_claim(self):
        registry = BaselineRegistry(
            REPO / (
                "study_docs/research/ductile-origami-warmstart/protocol/"
                "baseline-registry.json"
            ),
            SCHEMAS / "baseline-registry.schema.json",
        )
        with self.assertRaisesRegex(M00Error, "not registered"):
            render_baseline_claim(
                registry, "original", "observability_only",
                artifact_root=REPO, protocol_lock_sha256="4" * 64,
            )

    def test_original_hash_and_owner_attestation_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence = root / "evidence.raw"
            owner = root / "owner.json"
            evidence.write_bytes(b"evidence")
            owner.write_bytes(b"owner")
            evidence_sha = hashlib.sha256(evidence.read_bytes()).hexdigest()
            with self.assertRaises(M00Error):
                self.write_registry(
                    root,
                    [self.entry(
                        "original_tuningdriver", evidence_sha, None
                    )],
                )
            owner_sha = hashlib.sha256(owner.read_bytes()).hexdigest()
            registry = self.write_registry(
                root,
                [self.entry(
                    "original_tuningdriver", "0" * 64, owner_sha
                )],
            )
            with self.assertRaisesRegex(M00Error, "checksum"):
                render_baseline_claim(
                    registry, "baseline-one", "observability_only",
                    artifact_root=root, protocol_lock_sha256="4" * 64,
                )
            registry = self.write_registry(
                root,
                [self.entry(
                    "original_tuningdriver", evidence_sha, "0" * 64
                )],
            )
            with self.assertRaisesRegex(M00Error, "attestation checksum"):
                render_baseline_claim(
                    registry, "baseline-one", "observability_only",
                    artifact_root=root, protocol_lock_sha256="4" * 64,
                )

    def test_proxy_scope_wording_and_valid_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence = root / "evidence.raw"
            evidence.write_bytes(b"proxy")
            evidence_sha = hashlib.sha256(evidence.read_bytes()).hexdigest()
            registry = self.write_registry(
                root,
                [self.entry("geko_gfx942_proxy", evidence_sha)],
            )
            with self.assertRaisesRegex(M00Error, "scope"):
                render_baseline_claim(
                    registry, "baseline-one", "final_comparison",
                    artifact_root=root, protocol_lock_sha256="4" * 64,
                )
            with self.assertRaisesRegex(M00Error, "wording"):
                render_baseline_claim(
                    registry, "baseline-one", "observability_only",
                    artifact_root=root, protocol_lock_sha256="4" * 64,
                    requested_wording="original baseline",
                )
            claim = render_baseline_claim(
                registry, "baseline-one", "observability_only",
                artifact_root=root, protocol_lock_sha256="4" * 64,
            )
        self.assertIn("proxy", claim)
        self.assertIn("not an original TuningDriver", claim)

    def test_original_requires_typed_manifest_and_bound_owner(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "tuningdriver.bin"
            artifact.write_bytes(b"typed-tuningdriver-evidence")
            artifact_sha = hashlib.sha256(
                artifact.read_bytes()
            ).hexdigest()
            manifest = {
                "schema_version": "1.0",
                "evidence_type": "tuningdriver",
                "baseline_id": "baseline-one",
                "generator_revision": "1" * 40,
                "fork_params_sha256": "2" * 64,
                "weights_sha256": "3" * 64,
                "artifact_sha256": artifact_sha,
                "protocol_lock_sha256": "4" * 64,
                "allowed_claim_scope": ["observability_only"],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            manifest_sha = hashlib.sha256(
                manifest_path.read_bytes()
            ).hexdigest()
            owner = {
                "schema_version": "1.0",
                "attestation_type": "tuningdriver-owner",
                "owner": "baseline-owner",
                "issued_at": "2026-07-24T00:00:00Z",
                "baseline_id": "baseline-one",
                "generator_revision": "1" * 40,
                "fork_params_sha256": "2" * 64,
                "weights_sha256": "3" * 64,
                "artifact_sha256": artifact_sha,
                "generator_manifest_sha256": manifest_sha,
                "protocol_lock_sha256": "4" * 64,
                "allowed_claim_scope": ["observability_only"],
            }
            owner_path = root / "owner.json"
            owner_path.write_text(
                json.dumps(owner, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            owner_sha = hashlib.sha256(owner_path.read_bytes()).hexdigest()
            entry = self.entry(
                "original_tuningdriver", artifact_sha, owner_sha
            )
            entry["evidence_artifacts"] = [
                {
                    "path": artifact.name,
                    "sha256": artifact_sha,
                    "evidence_type": "tuningdriver_artifact",
                },
                {
                    "path": manifest_path.name,
                    "sha256": manifest_sha,
                    "evidence_type": "tuningdriver_manifest",
                },
            ]
            registry = self.write_registry(root, [entry])
            claim = render_baseline_claim(
                registry, "baseline-one", "observability_only",
                artifact_root=root, protocol_lock_sha256="4" * 64,
            )
            self.assertIn("Original TuningDriver", claim)
            owner["weights_sha256"] = "9" * 64
            owner_path.write_text(
                json.dumps(owner, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            entry["owner_attestation"]["sha256"] = hashlib.sha256(
                owner_path.read_bytes()
            ).hexdigest()
            registry = self.write_registry(root, [entry])
            with self.assertRaisesRegex(M00Error, "complete TuningDriver"):
                render_baseline_claim(
                    registry, "baseline-one", "observability_only",
                    artifact_root=root, protocol_lock_sha256="4" * 64,
                )


if __name__ == "__main__":
    unittest.main()
