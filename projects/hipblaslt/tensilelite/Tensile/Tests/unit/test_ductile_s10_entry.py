# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""CPU-only fail-closed tests for the S10 Stage-1 entry protocol."""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from Tensile.ductile.evidence import (
    EvidenceValidationError,
    canonical_sha256,
    strict_load_json,
    strict_load_yaml,
    validate_schema_document,
)


_REPO = Path(__file__).resolve().parents[6]
_RUNNER_PATH = (
    _REPO
    / "study_docs/research/ductile-origami-warmstart/protocol/v1"
    / "run_s10_entry.py"
)
_SPEC = importlib.util.spec_from_file_location("ductile_s10_entry_runner", _RUNNER_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {_RUNNER_PATH}")
s10 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(s10)


def _assert_code(test: unittest.TestCase, code: str):
    return test.assertRaisesRegex(EvidenceValidationError, rf"^{code}:")


def _live_device(index: int, used: int, *, eligible: bool = True) -> dict:
    return {
        "identity": {
            "container_visible_index": index,
            "unique_id": f"0x{index + 1:016x}",
            "serial_number": f"SERIAL-{index}",
            "pci_bus": f"0000:{index + 1:02X}:00.0",
            "arch": "gfx942",
            "compute_partition": "SPX",
            "memory_partition": "NPS1",
        },
        "gpu_use_percent": 0.0,
        "vram_allocation_percent": 0.5,
        "vram_used_bytes": used,
        "vram_total_bytes": 100000,
        "mapped_kfd_pids": [],
        "eligible": eligible,
        "ineligibility_reasons": [] if eligible else ["fixture_ineligible"],
    }


def _live_samples(rows: list[list[dict]]) -> list[dict]:
    return [
        {
            "sample_index": index,
            "captured_at": f"2026-07-25T00:00:0{index}Z",
            "seconds_since_previous": None if index == 0 else 2.0,
            "device_command": {},
            "process_command": {},
            "devices": devices,
        }
        for index, devices in enumerate(rows)
    ]


class TestS10SchemaAndContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = strict_load_json(s10.SCHEMA_PATH)
        cls.contract = strict_load_yaml(s10.CONTRACT_PATH)

    def test_schema_meta_and_contract_validate(self):
        validate_schema_document(self.contract, self.schema, context="S10 contract")
        self.assertEqual(self.contract["implementation_whitelist"], s10.IMPLEMENTATION_WHITELIST)
        self.assertEqual(self.contract["delivery_whitelist"], s10.DELIVERY_WHITELIST)
        self.assertEqual(self.contract["forbidden_roots"], s10.FORBIDDEN_ROOTS)

    def test_actual_prelock_artifacts_validate_with_compatible_size_schema(self):
        if not all(
            path.is_file()
            for path in (s10.PROVENANCE_PATH, s10.SIZE_REGISTRY_PATH, s10.INPUT_PATH)
        ):
            self.assertFalse(s10.LOCK_PATH.exists())
            return
        provenance = strict_load_json(s10.PROVENANCE_PATH)
        sizes = strict_load_json(s10.SIZE_REGISTRY_PATH)
        s10._validate(provenance, context="actual provenance")
        s10._validate(sizes, context="actual size registry")
        for row in [
            *sizes["raw_rows"],
            *sizes["distinct_source_order"],
            *sizes["selected_sizes"],
        ]:
            self.assertEqual(len(row), 4)
            self.assertTrue(
                all(
                    isinstance(value, int)
                    and not isinstance(value, bool)
                    and value > 0
                    for value in row
                )
            )
        invalid = copy.deepcopy(sizes)
        invalid["selected_sizes"][0] = [8, 8, 1]
        with self.assertRaises(EvidenceValidationError):
            s10._validate(invalid, context="short size")
        invalid = copy.deepcopy(sizes)
        invalid["selected_sizes"][0] = [8, 8, True, 128]
        with self.assertRaises(EvidenceValidationError):
            s10._validate(invalid, context="boolean size")

    def test_all_document_kinds_are_top_level_strict(self):
        for name in (
            "contract",
            "provenance",
            "size_registry",
            "environment",
            "lock",
            "mapping",
            "smoke",
            "noise",
            "decision",
        ):
            with self.subTest(name=name):
                self.assertFalse(self.schema["$defs"][name]["additionalProperties"])

    def test_unknown_wrong_authority_and_wrong_whitelist_rejected(self):
        unknown = copy.deepcopy(self.contract)
        unknown["unexpected"] = True
        with self.assertRaises(EvidenceValidationError):
            s10._validate(unknown, context="unknown")
        authority = copy.deepcopy(self.contract)
        authority["authorities"]["ductile_commit"] = "0" * 40
        with self.assertRaises(EvidenceValidationError):
            s10._validate(authority, context="authority")
        whitelist = copy.deepcopy(self.contract)
        whitelist["implementation_whitelist"] = whitelist["implementation_whitelist"][:-1]
        with self.assertRaises(EvidenceValidationError):
            s10._validate(whitelist, context="whitelist")

    def test_material_contract_substitutions_fail_preflight_semantic_binding(self):
        cases = {
            "threshold": ("noise", "cv_p95_threshold", 0.01),
            "count": ("noise", "repeats", 1),
            "formula": ("noise", "delta_noise_formula", "mean(abs(delta))"),
            "selection": (
                "mapping_selection",
                "noise_anchor_rule",
                "sorted hashes at indices 0,1,2",
            ),
            "h4": ("h4", "sample_count", 2),
            "lifecycle": ("lock_lifecycle", "lock_requires_valid_live_h4", False),
        }
        for name, (section, field, replacement) in cases.items():
            with self.subTest(name=name):
                mutated = copy.deepcopy(self.contract)
                mutated[section][field] = replacement
                with (
                    mock.patch.object(s10, "_resolve_authorities", return_value={}),
                    mock.patch.object(
                        s10, "strict_load_yaml", return_value=mutated
                    ),
                    _assert_code(self, "contract_semantic_mismatch"),
                ):
                    s10._preflight()

    def test_wrong_hash_is_rejected(self):
        self.assertIsNone(s10.HASH_RE.fullmatch("not-a-hash"))
        self.assertIsNotNone(s10.HASH_RE.fullmatch("a" * 64))

    def test_duplicate_keys_and_nonfinite_numbers_rejected(self):
        with _assert_code(self, "duplicate_key"):
            strict_load_json('{"a":1,"a":2}', from_text=True)
        with _assert_code(self, "duplicate_key"):
            strict_load_yaml("a: 1\na: 2\n", from_text=True)
        with _assert_code(self, "non_finite_number"):
            strict_load_json('{"value":NaN}', from_text=True)

    def _negative_decision_fixture(self):
        names_roles = [
            ("actual_guidance", "prerequisite", "PASS"),
            ("three_sizes", "prerequisite", "PASS"),
            ("h4_and_environment", "prerequisite", "PASS"),
            ("mapping_evidence_integrity", "evidence_integrity", "PASS"),
            ("mapping_entry", "entry_gate", "FAIL"),
            ("smoke_correctness", "blocked_absent", "BLOCKED"),
            ("noise_stable", "blocked_absent", "BLOCKED"),
        ]
        gates = []
        for index, (name, role, status) in enumerate(names_roles):
            blocked = status == "BLOCKED"
            failed = status == "FAIL"
            gates.append(
                {
                    "name": name,
                    "role": role,
                    "status": status,
                    "execution": "not_activated" if blocked else "complete",
                    "reason_code": (
                        "locked_mapping_entry_prerequisite_failed"
                        if failed
                        else "blocked_by_mapping_entry"
                        if blocked
                        else "fixture_pass"
                    ),
                    "reason_text": "fixture",
                    "failure_id": "S10-MAPPING-ENTRY-FAIL" if failed else None,
                    "blocked_by": ["mapping_entry"] if blocked else [],
                    "evidence": (
                        []
                        if blocked
                        else [
                            {
                                "path": f"gate-{index}.json",
                                "raw_sha256": f"{index + 1:064x}",
                            }
                        ]
                    ),
                    "blocked_absence": (
                        {
                            "canonical_path": f"blocked-{index}.json",
                            "raw_path": f"blocked-raw-{index}",
                            "must_be_absent": True,
                            "blocked_by": "mapping_entry",
                        }
                        if blocked
                        else None
                    ),
                }
            )
        return {
            "schema_version": "1.0.0",
            "kind": "s10_decision",
            "checkpoint_id": "S10",
            "status": "complete",
            "created_at": "2026-07-26T00:00:00Z",
            "effective_lock_raw_sha256": "f" * 64,
            "study_mode": "ready_actual_yaml_guidance",
            "completion_correctness": "complete",
            "scientific_outcome": "negative",
            "criterion": "S1_ENTRY_BLOCKED",
            "edge": None,
            "gates": gates,
            "failure_taxonomy": ["FT-BLOCKED-MAPPING"],
            "artifacts": [
                {"path": f"artifact-{index}.json", "raw_sha256": f"{index + 20:064x}"}
                for index in range(4)
            ],
            "decision_evidence": {
                "path": "negative-stop-raw.json",
                "raw_sha256": "e" * 64,
            },
            "claim_limitations": ["fixture only"],
        }

    def _mapping_fixture(self):
        rows = []
        for index in range(30):
            rows.append(
                {
                    "config_hash": f"{index + 1:064x}",
                    "size": [8 + index, 8, 1, 128],
                    "raw_indices": {},
                    "raw_values": {},
                    "expanded_groups": {},
                    "resolved_solution": None,
                    "codegen_identity": None,
                    "size_mapping": None,
                    "effective_gsu": None,
                    "resolved_sentinels": {},
                    "formocast_input": None,
                    "field_provenance": {},
                    "status": "rejected",
                    "rejection": {
                        "stage": "solution_resolution",
                        "reason_code": "pinned_validation_boundary_none",
                        "reason_text": "fixture",
                        "internal_subreason": "internal_subreason_unknown",
                        "log_sha256": "0" * 64,
                    },
                    "prediction": None,
                    "tie": False,
                }
            )
        return {
            "schema_version": "1.0.0",
            "kind": "s10_mapping_corpus",
            "checkpoint_id": "S10",
            "status": "complete",
            "created_at": "2026-07-26T00:00:00Z",
            "effective_lock_raw_sha256": "f" * 64,
            "candidate_count": 10,
            "size_count": 3,
            "row_count": 30,
            "anchor_hashes": ["1" * 64, "2" * 64, "3" * 64],
            "rows": rows,
            "deterministic_rerun_parity": True,
            "mapping_evidence_integrity": {
                "status": "PASS",
                "execution": "complete",
                "reason_code": "fresh_exact_30_row_ab_parity",
                "reason_text": "fixture",
                "failure_id": None,
            },
            "mapping_entry": {
                "status": "FAIL",
                "execution": "complete",
                "reason_code": "locked_mapping_entry_prerequisite_failed",
                "reason_text": "fixture",
                "failure_id": "S10-MAPPING-ENTRY-FAIL",
                "anchor_failure_hashes": ["1" * 64],
                "formocast_rejection_count": 0,
            },
            "executor": {},
        }

    def test_r10_schema_rejects_exact_nine_verifier_mutations(self):
        decision = self._negative_decision_fixture()
        mapping = self._mapping_fixture()
        s10._validate(decision, context="canonical negative decision")
        s10._validate(mapping, context="canonical mapping")

        cases = []
        mutated = copy.deepcopy(decision)
        mutated["gates"][0]["role"] = "evidence_integrity"
        cases.append(("decision_prerequisite_wrong_role", mutated))
        mutated = copy.deepcopy(decision)
        mutated["gates"][3]["role"] = "prerequisite"
        cases.append(("decision_integrity_wrong_role", mutated))
        mutated = copy.deepcopy(decision)
        mutated["gates"][4]["role"] = "prerequisite"
        cases.append(("decision_entry_wrong_role", mutated))
        mutated = copy.deepcopy(decision)
        mutated["gates"][4]["failure_id"] = None
        cases.append(("decision_entry_fail_without_failure_id", mutated))
        mutated = copy.deepcopy(decision)
        mutated["gates"][4]["evidence"] = []
        cases.append(("decision_entry_fail_without_evidence", mutated))
        mutated = copy.deepcopy(decision)
        mutated["gates"][5]["blocked_absence"] = None
        cases.append(("decision_blocked_absence_missing", mutated))
        mutated = copy.deepcopy(decision)
        mutated["gates"][5]["blocked_by"] = []
        cases.append(("decision_blocked_by_missing", mutated))
        mutated = copy.deepcopy(mapping)
        mutated["mapping_entry"].update(
            {
                "reason_code": "all_locked_entry_prerequisites_satisfied",
                "failure_id": None,
                "anchor_failure_hashes": [],
                "formocast_rejection_count": 1,
            }
        )
        cases.append(("mapping_entry_inconsistent_fail", mutated))
        mutated = copy.deepcopy(mapping)
        mutated["rows"][0]["rejection"]["reason_code"] = (
            "canonical_duplicate_kernel"
        )
        cases.append(("mapping_rejection_stage_reason_mismatch", mutated))

        for name, document in cases:
            with self.subTest(name=name), self.assertRaises(
                EvidenceValidationError
            ):
                s10._validate(document, context=name)

    def test_unsafe_scratch_path_rejected(self):
        with _assert_code(self, "unsafe_path"):
            s10._assert_scratch_root(_REPO / "outside-s10")


class TestSourceIntegration(unittest.TestCase):
    _TARGET = {
        "path": "projects/hipblaslt/target.h",
        "mode": "100644",
        "blob": "1" * 40,
    }
    _LINK = {
        "path": "projects/hipblaslt/alias.h",
        "mode": "120000",
        "blob": "2" * 40,
    }
    _BLOBS = {"1" * 40: b"target bytes", "2" * 40: b"target.h"}

    def _synthetic_inventory(self, entries=None, blobs=None):
        entries = entries or [copy.deepcopy(self._TARGET), copy.deepcopy(self._LINK)]
        blobs = blobs or self._BLOBS
        expected = [
            {
                "path": "projects/hipblaslt/alias.h",
                "mode": "120000",
                "blob": "2" * 40,
                "link_text": "target.h",
                "link_sha256": __import__("hashlib").sha256(b"target.h").hexdigest(),
                "target_path": "projects/hipblaslt/target.h",
                "target_mode": "100644",
                "target_blob": "1" * 40,
                "target_raw_sha256": __import__("hashlib").sha256(
                    blobs["1" * 40]
                ).hexdigest(),
            }
        ]
        with (
            mock.patch.object(s10, "DUCTILE_SYMLINK_COUNT", 1),
            mock.patch.object(
                s10, "DUCTILE_SYMLINK_INVENTORY_SHA256", canonical_sha256(expected)
            ),
            mock.patch.object(s10, "_blob_bytes", side_effect=lambda oid: blobs[oid]),
        ):
            return s10._resolve_source_symlinks(entries)

    def _mini_root_and_semantic(self, root: Path):
        target_bytes = b"target bytes"
        target_hash = __import__("hashlib").sha256(target_bytes).hexdigest()
        target_path = "projects/hipblaslt/target.h"
        link_path = "projects/hipblaslt/alias.h"
        target = root / target_path
        target.parent.mkdir(parents=True)
        target.write_bytes(target_bytes)
        os.chmod(target, 0o644)
        (root / link_path).symlink_to("target.h")
        directories = s10._directory_closure([target_path, link_path])
        resolution = {
            "path": link_path,
            "mode": "120000",
            "blob": "2" * 40,
            "link_text": "target.h",
            "link_sha256": __import__("hashlib").sha256(b"target.h").hexdigest(),
            "target_path": target_path,
            "target_mode": "100644",
            "target_blob": "1" * 40,
            "target_raw_sha256": target_hash,
        }
        semantic = {
            "manifest_sha256": "f" * 64,
            "directory_closure": directories,
            "entries": [
                {
                    "path": link_path,
                    "kind": "symlink",
                    "source_mode": "120000",
                    "raw_sha256": resolution["link_sha256"],
                    "resolution": resolution,
                },
                {
                    "path": target_path,
                    "kind": "regular",
                    "source_mode": "100644",
                    "raw_sha256": target_hash,
                },
            ],
        }
        return semantic

    def _mini_counts(self, *, regular=1, links=1, leaves=2):
        return mock.patch.multiple(
            s10,
            INTEGRATION_REGULAR_COUNT=regular,
            DUCTILE_SYMLINK_COUNT=links,
            INTEGRATION_LEAF_COUNT=leaves,
        )

    def test_exact_pinned_thirteen_link_inventory(self):
        entries = s10._tree_entries(
            s10.DUCTILE_COMMIT,
            [
                "projects/hipblaslt",
                "cmake/modules",
                "shared/origami",
                "shared/stinkytofu",
            ],
        )
        inventory = s10._resolve_source_symlinks(entries)
        self.assertEqual(len(inventory), 13)
        self.assertEqual(canonical_sha256(inventory), s10.DUCTILE_SYMLINK_INVENTORY_SHA256)
        self.assertTrue(all(item["target_mode"] == "100644" for item in inventory))

    def test_valid_source_link_and_inventory_mismatch(self):
        inventory = self._synthetic_inventory()
        self.assertEqual(inventory[0]["target_path"], self._TARGET["path"])
        with (
            mock.patch.object(s10, "DUCTILE_SYMLINK_COUNT", 2),
            mock.patch.object(s10, "_blob_bytes", side_effect=lambda oid: self._BLOBS[oid]),
            _assert_code(self, "symlink_inventory_mismatch"),
        ):
            s10._resolve_source_symlinks([self._TARGET, self._LINK])
        actual = s10._tree_entries(
            s10.DUCTILE_COMMIT,
            [
                "projects/hipblaslt",
                "cmake/modules",
                "shared/origami",
                "shared/stinkytofu",
            ],
        )
        fourteenth = {
            "path": "projects/hipblaslt/unexpected-link",
            "mode": "120000",
            "blob": self._LINK["blob"],
        }
        with _assert_code(self, "symlink_inventory_mismatch"):
            s10._resolve_source_symlinks([*actual, fourteenth])

    def test_geko_link_is_rejected(self):
        expected = self._synthetic_inventory()
        with tempfile.TemporaryDirectory() as tmp:
            with (
                mock.patch.object(
                    s10,
                    "_tree_entries",
                    side_effect=[
                        [copy.deepcopy(self._TARGET), copy.deepcopy(self._LINK)],
                        [copy.deepcopy(self._LINK)],
                    ],
                ),
                mock.patch.object(s10, "DUCTILE_REGULAR_COUNT", 1),
                mock.patch.object(s10, "DUCTILE_SYMLINK_COUNT", 1),
                mock.patch.object(
                    s10,
                    "DUCTILE_SYMLINK_INVENTORY_SHA256",
                    canonical_sha256(expected),
                ),
                mock.patch.object(
                    s10, "_blob_bytes", side_effect=lambda oid: self._BLOBS[oid]
                ),
                _assert_code(self, "geko_symlink_rejected"),
            ):
                s10._materialize_integration(Path(tmp) / "integration", {})

    def test_escape_chain_missing_nonregular_and_overlay_target_rejected(self):
        cases = []
        escape_blobs = {**self._BLOBS, "2" * 40: b"../../../escape"}
        cases.append(("symlink_escape", [self._TARGET, self._LINK], escape_blobs, 1))
        chain = copy.deepcopy(self._TARGET)
        chain["mode"] = "120000"
        chain_blobs = {**self._BLOBS, "1" * 40: b"alias.h"}
        cases.append(("symlink_chain", [chain, self._LINK], chain_blobs, 2))
        cases.append(("symlink_target_missing", [self._LINK], self._BLOBS, 1))
        executable = copy.deepcopy(self._TARGET)
        executable["mode"] = "100755"
        cases.append(
            ("symlink_target_nonregular", [executable, self._LINK], self._BLOBS, 1)
        )
        overlay_target = copy.deepcopy(self._TARGET)
        overlay_target["path"] = "projects/hipblaslt/utilities/geko/target.h"
        overlay_link = copy.deepcopy(self._LINK)
        overlay_blobs = {**self._BLOBS, "2" * 40: b"utilities/geko/target.h"}
        cases.append(
            (
                "symlink_overlay_target",
                [overlay_target, overlay_link],
                overlay_blobs,
                1,
            )
        )
        for code, entries, blobs, count in cases:
            with self.subTest(code=code):
                with (
                    mock.patch.object(s10, "DUCTILE_SYMLINK_COUNT", count),
                    mock.patch.object(s10, "_blob_bytes", side_effect=lambda oid, b=blobs: b[oid]),
                    _assert_code(self, code),
                ):
                    s10._resolve_source_symlinks(entries)

    def test_expected_link_regular_expected_regular_link_and_target_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            semantic = self._mini_root_and_semantic(root)
            with self._mini_counts():
                audit = s10._scan_integration(root, semantic)
                self.assertEqual(audit["symlink_count"], 1)
                link = root / "projects/hipblaslt/alias.h"
                link.unlink()
                link.write_bytes(b"target.h")
                with _assert_code(self, "expected_link_is_regular"):
                    s10._scan_integration(root, semantic)
                link.unlink()
                link.symlink_to("other.h")
                with _assert_code(self, "symlink_target_mismatch"):
                    s10._scan_integration(root, semantic)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            semantic = self._mini_root_and_semantic(root)
            target = root / "projects/hipblaslt/target.h"
            target.unlink()
            target.symlink_to("alias.h")
            with self._mini_counts(), _assert_code(self, "expected_regular_is_link"):
                s10._scan_integration(root, semantic)

    def test_directory_ancestor_hardlink_special_and_manifest_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            semantic = self._mini_root_and_semantic(root)
            (root / "extra").mkdir()
            with self._mini_counts(), _assert_code(self, "directory_closure_mismatch"):
                s10._scan_integration(root, semantic)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            semantic = self._mini_root_and_semantic(root)
            second = root / "projects/hipblaslt/second.h"
            os.link(root / "projects/hipblaslt/target.h", second)
            semantic["entries"].append(
                {
                    "path": "projects/hipblaslt/second.h",
                    "kind": "regular",
                    "source_mode": "100644",
                    "raw_sha256": semantic["entries"][1]["raw_sha256"],
                }
            )
            with self._mini_counts(regular=2, leaves=3), _assert_code(
                self, "hardlink_rejected"
            ):
                s10._scan_integration(root, semantic)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            semantic = self._mini_root_and_semantic(root)
            semantic["entries"][1]["raw_sha256"] = "0" * 64
            with self._mini_counts(), _assert_code(self, "integration_drift"):
                s10._scan_integration(root, semantic)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root.mkdir(exist_ok=True)
            fifo = root / "node"
            os.mkfifo(fifo)
            semantic = {
                "manifest_sha256": "f" * 64,
                "directory_closure": [],
                "entries": [
                    {
                        "path": "node",
                        "kind": "regular",
                        "source_mode": "100644",
                        "raw_sha256": "0" * 64,
                    }
                ],
            }
            with self._mini_counts(regular=1, links=0, leaves=1), _assert_code(
                self, "special_node_rejected"
            ):
                s10._scan_integration(root, semantic)

    def test_symlink_ancestor_and_generated_output_link_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "real").mkdir()
            (root / "ancestor").symlink_to("real")
            semantic = {
                "manifest_sha256": "f" * 64,
                "directory_closure": ["ancestor"],
                "entries": [
                    {
                        "path": "ancestor/file",
                        "kind": "regular",
                        "source_mode": "100644",
                        "raw_sha256": "0" * 64,
                    }
                ],
            }
            with self._mini_counts(regular=1, links=0, leaves=1), _assert_code(
                self, "symlink_ancestor"
            ):
                s10._scan_integration(root, semantic)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "target").write_bytes(b"x")
            (root / "link").symlink_to("target")
            with _assert_code(self, "symlink_rejected"):
                s10._output_manifest(root)

    def test_cross_run_semantic_parity_and_phase_drift_rejected(self):
        semantic = {"manifest_sha256": "a" * 64}
        runs = [
            {
                "integration_semantic": semantic,
                "integration_semantic_ref": {"raw_sha256": "b" * 64},
            },
            {
                "integration_semantic": copy.deepcopy(semantic),
                "integration_semantic_ref": {"raw_sha256": "b" * 64},
            },
        ]
        s10._require_semantic_parity(runs)
        runs[1]["integration_semantic"]["manifest_sha256"] = "c" * 64
        with _assert_code(self, "integration_parity_mismatch"):
            s10._require_semantic_parity(runs)
        inventory = []
        directories = []
        semantic_body = {
            "materialization_policy": s10.MATERIALIZATION_POLICY,
            "resolution_inventory_sha256": canonical_sha256(inventory),
            "resolution_inventory": inventory,
            "counts": {
                "ductile_regular": 0,
                "ductile_symlink": 0,
                "geko_regular": 0,
                "regular": 0,
                "symlink": 0,
                "leaves": 0,
                "directories": 0,
            },
            "directory_closure": directories,
            "directory_closure_sha256": canonical_sha256(directories),
        }
        semantic = {**semantic_body, "manifest_sha256": canonical_sha256(semantic_body)}
        semantic_ref = {"path": "semantic.json", "raw_sha256": "1" * 64}
        wrapper_ref = {"path": "wrapper.json", "raw_sha256": "2" * 64}
        wrapper = {
            "schema_version": "1.0.0",
            "kind": "s10_integration_run_manifest",
            "materialization_policy": s10.MATERIALIZATION_POLICY,
            "root": s10._rel(s10.S10_RUN_ROOT / "synthetic/run-a/integration"),
            "semantic_manifest": semantic_ref,
            "phase_seals": [
                {"phase": phase, "audit": {"drifted": True}}
                for phase in (
                    "after-materialization",
                    "before-native-build",
                    "after-native-build",
                    "before-generation",
                    "after-generation",
                    "before-ductile-consumption",
                    "after-ductile-consumption",
                )
            ],
        }
        provenance = {
            "runs": [
                {
                    "tag": "a",
                    "integration_semantic": semantic_ref,
                    "integration": wrapper_ref,
                    "integration_manifest_sha256": semantic["manifest_sha256"],
                    "integration_wrapper_sha256": wrapper_ref["raw_sha256"],
                }
            ]
        }
        with (
            mock.patch.object(
                s10, "_load_ignored_ref", side_effect=[semantic, wrapper]
            ),
            mock.patch.object(s10, "_scan_integration", return_value={"clean": True}),
            mock.patch.multiple(
                s10,
                DUCTILE_REGULAR_COUNT=0,
                DUCTILE_SYMLINK_COUNT=0,
                GEKO_REGULAR_COUNT=0,
                INTEGRATION_REGULAR_COUNT=0,
                INTEGRATION_LEAF_COUNT=0,
                DUCTILE_SYMLINK_INVENTORY_SHA256=canonical_sha256([]),
            ),
            _assert_code(self, "phase_drift"),
        ):
            s10._verify_integration_lineage(
                provenance,
                scratch_root=s10.S10_RUN_ROOT / "synthetic",
            )

    def test_overlay_destination_collision_rejected(self):
        collision = {
            "path": "projects/hipblaslt/utilities/geko/already.txt",
            "mode": "100644",
            "blob": "1" * 40,
        }
        with tempfile.TemporaryDirectory() as tmp:
            with (
                mock.patch.object(s10, "_tree_entries", side_effect=[[collision], []]),
                mock.patch.object(s10, "DUCTILE_REGULAR_COUNT", 1),
                mock.patch.object(s10, "DUCTILE_SYMLINK_COUNT", 0),
                mock.patch.object(
                    s10, "DUCTILE_SYMLINK_INVENTORY_SHA256", canonical_sha256([])
                ),
                _assert_code(self, "overlay_collision"),
            ):
                s10._materialize_integration(Path(tmp) / "integration", {})

    def test_manifest_reorder_is_rejected(self):
        first = [{"path": "a.txt", "raw_sha256": "1" * 64}]
        second = list(reversed(first + [{"path": "b.txt", "raw_sha256": "2" * 64}]))
        with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
            with _assert_code(self, "generation_manifest_mismatch"):
                s10._compare_generation_runs(
                    {"output_manifest": first},
                    {"output_manifest": second},
                    Path(left),
                    Path(right),
                )

    def test_python_path_never_uses_current_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "integration"
            build = Path(tmp) / "build"
            paths = s10._python_path(root, build)
        self.assertNotIn(_REPO / "projects/hipblaslt/tensilelite", paths)
        self.assertEqual(
            paths,
            [
                build,
                root / "projects/hipblaslt/tensilelite",
                root / "projects/hipblaslt/utilities/geko",
                s10.SITE_PACKAGES,
            ],
        )


class TestInputDerivationAndGeneration(unittest.TestCase):
    def test_derived_input_preserves_rows_layout_and_clears_environment(self):
        raw, record = s10._derive_input()
        document = strict_load_yaml(raw.decode("utf-8"), from_text=True)
        self.assertEqual(len(document["Sizes"]), 17)
        self.assertEqual(document["Sizes"], record["raw_sizes"])
        self.assertLess(len({tuple(row) for row in document["Sizes"]}), 17)
        self.assertEqual(
            [document[key] for key in ("DataType", "DestDataType", "ComputeDataType")],
            ["B", "B", "S"],
        )
        self.assertEqual([document["TRANSA"], document["TRANSB"]], ["N", "N"])
        for key, expected in {
            "ARCH": "gfx942",
            "StreamK": False,
            "ONE_SIZE_PER_CONFIG": False,
            "GA": True,
            "SIZE_OPTION": 0,
            "CLUSTER": 0,
        }.items():
            self.assertEqual(document[key], expected)
        with mock.patch.dict(
            os.environ,
            {key: "adversarial" for key in s10.ENV_UPDATABLE_KEYS},
            clear=False,
        ):
            environment = s10._base_env()
        for key in s10.ENV_UPDATABLE_KEYS:
            self.assertNotIn(key, environment)

    def test_generation_requires_complete_manifest_parity_and_one_yaml(self):
        entry = {"path": "actual.yaml", "raw_sha256": "a" * 64, "bytes": 4, "mode": "100644"}
        with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
            left_path = Path(left) / "actual.yaml"
            right_path = Path(right) / "actual.yaml"
            left_path.write_bytes(b"same")
            right_path.write_bytes(b"same")
            with mock.patch.object(s10, "_is_qualifying_yaml", return_value=True):
                a, b, qualifying = s10._compare_generation_runs(
                    {"output_manifest": [entry]},
                    {"output_manifest": [entry]},
                    Path(left),
                    Path(right),
                )
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(qualifying, [entry])
            with (
                mock.patch.object(s10, "_is_qualifying_yaml", return_value=False),
                _assert_code(self, "qualifying_yaml_count"),
            ):
                s10._compare_generation_runs(
                    {"output_manifest": [entry]},
                    {"output_manifest": [entry]},
                    Path(left),
                    Path(right),
                )

    def test_generation_rejects_multiple_yaml_and_byte_mismatch(self):
        entries = [
            {"path": "a.yaml", "raw_sha256": "a" * 64},
            {"path": "b.yaml", "raw_sha256": "b" * 64},
        ]
        with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
            for root in (Path(left), Path(right)):
                (root / "a.yaml").write_bytes(b"a")
                (root / "b.yaml").write_bytes(b"b")
            with (
                mock.patch.object(s10, "_is_qualifying_yaml", return_value=True),
                _assert_code(self, "qualifying_yaml_count"),
            ):
                s10._compare_generation_runs(
                    {"output_manifest": entries},
                    {"output_manifest": entries},
                    Path(left),
                    Path(right),
                )
            one = [entries[0]]
            (Path(right) / "a.yaml").write_bytes(b"different")
            with (
                mock.patch.object(s10, "_is_qualifying_yaml", return_value=True),
                _assert_code(self, "generation_manifest_mismatch"),
            ):
                s10._compare_generation_runs(
                    {"output_manifest": one},
                    {"output_manifest": one},
                    Path(left),
                    Path(right),
                )


class TestDuctileConsumptionAndSelection(unittest.TestCase):
    def test_three_size_rule_and_two_size_rejection(self):
        raw = [[8, 8, 1, 32]] * 15 + [[16, 8, 1, 64], [32, 8, 1, 128]]
        generated = [
            [32, 8, 1, 128],
            [8, 8, 1, 32],
            [16, 8, 1, 64],
            [8, 8, 1, 32],
        ]
        hashes = {
            "raw_yaml_sha256": "1" * 64,
            "search_space_map_sha256": "2" * 64,
            "groups_sha256": "3" * 64,
            "candidate_order_sha256": "4" * 64,
            "weights_sha256": "5" * 64,
        }
        selected = s10._select_sizes(raw, generated, hashes)
        self.assertEqual(
            selected["selected_sizes"],
            [[8, 8, 1, 32], [16, 8, 1, 64], [32, 8, 1, 128]],
        )
        self.assertEqual(selected["same_space"], hashes)
        with _assert_code(self, "two_size_downgrade"):
            s10._select_sizes(raw, generated[:2], hashes)

    def test_mapping_ten_and_anchor_rules(self):
        space = {
            "group_0": [{"DepthU": 16}, {"DepthU": 32}, {"DepthU": 64}],
            "GlobalSplitU": [-1, -2, 1, 2],
            "VectorWidth": [1, 2, 4, 8],
            "PrefetchGlobalRead": [0, 1, 2],
            "DepthU": [16, 32, 64, 128],
        }
        order = list(space)
        records = [
            {
                "index": index,
                "axis": axis,
                "origin": "synthetic",
                "candidates": values,
                "candidate_count": len(values),
                "candidates_sha256": canonical_sha256(values),
            }
            for index, (axis, values) in enumerate(space.items())
        ]
        with mock.patch.multiple(
            s10,
            EXPECTED_AXIS_ORDER=order,
            EXPECTED_AXIS_ORDER_SHA256=canonical_sha256(order),
            EXPECTED_LEGACY_SPACE_MAP_SHA256=canonical_sha256(space),
        ):
            result = s10._select_mapping_ten(records)
        self.assertEqual(len(result["candidates"]), 10)
        self.assertEqual(len(set(result["candidate_hashes"])), 10)
        ordered = sorted(result["candidate_hashes"])
        self.assertEqual(result["anchor_hashes"], [ordered[0], ordered[4], ordered[9]])
        self.assertEqual(result["coverage"]["sentinels_present"], [-2, -1])
        self.assertEqual(result["candidates"][0]["pattern"], "all-first")
        self.assertEqual(result["candidates"][1]["pattern"], "all-last")

    def test_consumer_probe_binds_order_weights_soo_and_reduce_fn(self):
        probe = s10._consume_probe_code()
        for required in (
            "BenchmarkProcess",
            "SearchSpace(fork",
            "GeneticAlgorithm(",
            '"raw_groups_sha256": digest(',
            '"expanded_groups_sha256": digest(',
            '"search_space_order": list(space.map)',
            '"weights": plain(merged["weights"])',
            '"soo": bool(ga.soo)',
            '"reduce_fn": "mean" if ga.reduce_fn is np.mean else "max"',
        ):
            self.assertIn(required, probe)
        self.assertEqual(
            s10._parse_consumer_stdout(b"# one\n# two\n{\"ok\":true}\n"),
            {"ok": True},
        )
        with _assert_code(self, "ductile_parity_mismatch"):
            s10._parse_consumer_stdout(b"unexpected\n{\"ok\":true}\n")

    def test_ordered_updates_preserve_first_insertion_and_typed_values(self):
        result = s10._ordered_update(
            {"first": [1], "second": [2]},
            [("second", [3]), ("third", [False])],
        )
        self.assertEqual(list(result), ["first", "second", "third"])
        self.assertEqual(result["second"], [3])
        self.assertFalse(s10._typed_equal(False, 0))
        self.assertTrue(s10._typed_equal([False], [False]))

    def test_axis_records_reject_reorder_duplicate_index_and_sorted_map_blindness(self):
        space = {"z": [1, 2], "a": [3, 4]}
        records = [
            {
                "index": index,
                "axis": axis,
                "candidates": values,
                "candidate_count": len(values),
                "candidates_sha256": canonical_sha256(values),
            }
            for index, (axis, values) in enumerate(space.items())
        ]
        with mock.patch.multiple(
            s10,
            EXPECTED_AXIS_ORDER=list(space),
            EXPECTED_AXIS_ORDER_SHA256=canonical_sha256(list(space)),
            EXPECTED_LEGACY_SPACE_MAP_SHA256=canonical_sha256(space),
        ):
            validated = s10._validate_axis_records(records, context="synthetic")
            self.assertEqual(validated["order"], ["z", "a"])
            reordered = copy.deepcopy(records)
            reordered.reverse()
            for index, record in enumerate(reordered):
                record["index"] = index
            self.assertEqual(
                canonical_sha256(
                    {record["axis"]: record["candidates"] for record in reordered}
                ),
                canonical_sha256(space),
            )
            with _assert_code(self, "axis_order_mismatch"):
                s10._validate_axis_records(reordered, context="reordered")
            duplicate_index = copy.deepcopy(records)
            duplicate_index[1]["index"] = 0
            with _assert_code(self, "axis_record_mismatch"):
                s10._validate_axis_records(duplicate_index, context="duplicate")

    def test_group_expansion_preserves_raw_indices_and_rejects_unsupported_shape(self):
        groups = [
            [
                {"A": [0, 1], "WorkGroup": [16, 16, 1]},
                {"MatrixInstruction": [16, 16, 16, 1]},
            ]
        ]
        expanded, table = s10._independent_expand_groups(groups)
        self.assertEqual(
            expanded,
            [
                [
                    {"A": 0, "WorkGroup": [16, 16, 1]},
                    {"A": 1, "WorkGroup": [16, 16, 1]},
                    {"MatrixInstruction": [16, 16, 16, 1]},
                ]
            ],
        )
        self.assertEqual(
            [(row["raw_index"], row["expanded_start"], row["expanded_count"]) for row in table],
            [(0, 0, 2), (1, 2, 1)],
        )
        with _assert_code(self, "group_expansion_unsupported"):
            s10._independent_expand_groups([[[{"unsupported": True}]]])
        with _assert_code(self, "group_overlap"):
            s10._group_parameter_owners(
                [
                    [{"A": 0, "B": 1}],
                    [{"B": 2, "C": 3}],
                ]
            )

    def test_probability_evidence_is_float32_and_mutation_sensitive(self):
        first = s10._probability_evidence([0.0, 1.0, 2.0], 0.25)
        second = s10._probability_evidence([0.0, 1.0, 2.5], 0.25)
        beta_changed = s10._probability_evidence([0.0, 1.0, 2.0], 0.5)
        self.assertEqual(first["dtype"], "float32")
        self.assertEqual(first["shape"], [3])
        self.assertTrue(first["finite"])
        self.assertNotEqual(first["raw_sha256"], second["raw_sha256"])
        self.assertNotEqual(first["raw_sha256"], beta_changed["raw_sha256"])
        with _assert_code(self, "weight_mismatch"):
            s10._probability_evidence([False, 1.0], 0.25)

    def test_source_identity_and_literal_ast_fail_closed(self):
        source = inspect.getsource(s10._independent_source_model)
        for forbidden_call in (
            "BenchmarkProcess(",
            "DuctileBackend(",
            "SearchSpace(",
            "GeneticAlgorithm(",
        ):
            self.assertNotIn(forbidden_call, source)
        with mock.patch.object(s10, "_git_oid", return_value="0" * 40), _assert_code(
            self, "source_identity_mismatch"
        ):
            s10._r4_source_identities()
        with _assert_code(self, "source_ast_unsupported"):
            s10._literal_assignment(b"defaultBenchmarkCommonParameters = build()", "defaultBenchmarkCommonParameters")
        with _assert_code(self, "duplicate_parameter"):
            s10._strict_singleton_records(
                [{"A": [1]}, {"A": [2]}],
                context="duplicate",
            )

    def test_raw_o3_reorder_does_not_redefine_o4_axis_order(self):
        input_path = s10.INPUT_PATH
        if not input_path.is_file():
            input_path = (
                s10.R8_ARCHIVE_ROOT
                / "retired/study_docs/research/ductile-origami-warmstart"
                / "protocol/v1/inputs/s10-generated.yaml"
            )
        document = s10._raw_document(input_path)
        fork_records = document["BenchmarkProblems"][0][1]["ForkParameters"]
        original_raw_order = [next(iter(record)) for record in fork_records]
        fork_records[0], fork_records[1] = fork_records[1], fork_records[0]
        with mock.patch.object(s10, "EXPECTED_ACTUAL_YAML_SHA256", "0" * 64):
            witness = s10._raw_o4_witness(document, "0" * 64)
            model = s10._independent_source_model(witness)
        self.assertNotEqual(witness["outer_order"], original_raw_order)
        self.assertEqual(model["axis_order"], s10.EXPECTED_AXIS_ORDER)


class TestRawReferenceClosure(unittest.TestCase):
    _TEMP_PARENT = s10.S10_RUN_ROOT / "preflight-tool-cache/tool-tmp"

    @staticmethod
    def _hash(path: Path) -> str:
        return s10.sha256_file(path)

    def _command_fixture(self, root: Path) -> tuple[dict, Path]:
        logs = root / "logs"
        logs.mkdir(parents=True)
        stdout = logs / "fixture.stdout"
        stderr = logs / "fixture.stderr"
        stdout.write_bytes(b"stdout\n")
        stderr.write_bytes(b"stderr\n")
        record = {
            "argv": ["tool", "--fixed"],
            "cwd": s10._rel(root),
            "environment": {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONHASHSEED": "0",
                "GIT_CEILING_DIRECTORIES": str(s10.CONTAINER_REPO),
            },
            "started_at": "2026-07-25T00:00:00Z",
            "ended_at": "2026-07-25T00:00:01Z",
            "exit_code": 0,
            "stdout": {
                "path": s10._rel(stdout),
                "raw_sha256": self._hash(stdout),
                "bytes": stdout.stat().st_size,
            },
            "stderr": {
                "path": s10._rel(stderr),
                "raw_sha256": self._hash(stderr),
                "bytes": stderr.stat().st_size,
            },
        }
        return record, logs

    def test_command_and_log_per_field_substitutions_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=self._TEMP_PARENT) as tmp:
            root = Path(tmp)
            record, logs = self._command_fixture(root)
            s10._verify_command_record(
                record,
                role="fixture",
                expected_argv=["tool", "--fixed"],
                expected_cwd=root,
                log_root=logs,
                log_name="fixture",
            )
            cases = {
                "argv": lambda value: value["argv"].append("--changed"),
                "cwd": lambda value: value.__setitem__("cwd", "wrong"),
                "environment": lambda value: value["environment"].__setitem__(
                    "PYTHONHASHSEED", "1"
                ),
                "stdout_hash": lambda value: value["stdout"].__setitem__(
                    "raw_sha256", "0" * 64
                ),
                "stdout_bytes": lambda value: value["stdout"].__setitem__(
                    "bytes", value["stdout"]["bytes"] + 1
                ),
                "stderr_path": lambda value: value["stderr"].__setitem__(
                    "path", value["stdout"]["path"]
                ),
            }
            for name, mutate in cases.items():
                with self.subTest(name=name):
                    changed = copy.deepcopy(record)
                    mutate(changed)
                    with _assert_code(self, "manifest_tamper"):
                        s10._verify_command_record(
                            changed,
                            role="fixture",
                            expected_argv=["tool", "--fixed"],
                            expected_cwd=root,
                            log_root=logs,
                            log_name="fixture",
                        )

    def test_regular_binary_reference_per_field_substitutions_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=self._TEMP_PARENT) as tmp:
            root = Path(tmp)
            binary = root / "binary.so"
            other = root / "other.so"
            binary.write_bytes(b"binary")
            other.write_bytes(b"other")
            record = {
                "path": s10._rel(binary),
                "raw_sha256": self._hash(binary),
                "bytes": binary.stat().st_size,
            }
            self.assertEqual(
                s10._verify_regular_hash_record(
                    record,
                    role="binary",
                    expected_path=binary,
                    include_bytes=True,
                ),
                binary,
            )
            cases = {
                "path": {
                    **record,
                    "path": s10._rel(other),
                    "raw_sha256": self._hash(other),
                    "bytes": other.stat().st_size,
                },
                "raw_sha256": {**record, "raw_sha256": "0" * 64},
                "bytes": {**record, "bytes": record["bytes"] + 1},
            }
            for name, changed in cases.items():
                with self.subTest(name=name), _assert_code(self, "manifest_tamper"):
                    s10._verify_regular_hash_record(
                        changed,
                        role="binary",
                        expected_path=binary,
                        include_bytes=True,
                    )

    def test_host_dependency_split_rehashes_repo_and_rejects_malformed_external(self):
        with tempfile.TemporaryDirectory(dir=self._TEMP_PARENT) as tmp:
            host_repo = Path(tmp)
            build = host_repo / "build"
            dependency = build / "libstinkytofu.so"
            dependency.parent.mkdir()
            dependency.write_bytes(b"repo dependency")
            container_repo = Path("/src/rocm-libraries")
            recorded_path = container_repo / "build/libstinkytofu.so"
            record = {
                "lexical_path": str(recorded_path),
                "resolved_path": str(recorded_path),
                "lexical_is_symlink": False,
                "raw_sha256": self._hash(dependency),
            }
            stdout = f"libstinkytofu.so => {recorded_path} (0x1)\n".encode()
            with (
                mock.patch.object(s10, "ROOT", host_repo),
                mock.patch.object(s10, "CONTAINER_REPO", container_repo),
            ):
                s10._verify_dependency_closure(
                    [record], stdout, build=build, tag="a"
                )
                with _assert_code(self, "native_lineage_mismatch"):
                    s10._verify_dependency_closure(
                        [{**record, "raw_sha256": "0" * 64}],
                        stdout,
                        build=build,
                        tag="a",
                    )
                malformed = {
                    "lexical_path": "/lib/libexternal.so",
                    "resolved_path": "/lib/libexternal.so",
                    "lexical_is_symlink": False,
                    "raw_sha256": None,
                    "unexpected": True,
                }
                with _assert_code(self, "native_lineage_mismatch"):
                    s10._verify_dependency_closure(
                        [malformed],
                        b"libexternal.so => /lib/libexternal.so (0x1)\n",
                        build=build,
                        tag="a",
                    )

    def test_import_path_and_hash_substitutions_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=self._TEMP_PARENT) as tmp:
            root = Path(tmp)
            integration = root / "integration"
            build = root / "native-build"
            module_paths = {
                "rocisa": build / "rocisa/__init__.py",
                "rocisa._rocisa": build / "rocisa/_rocisa.test.so",
                "Tensile": (
                    integration
                    / "projects/hipblaslt/tensilelite/Tensile/__init__.py"
                ),
                "Tensile.LibraryIO": (
                    integration
                    / "projects/hipblaslt/tensilelite/Tensile/LibraryIO.py"
                ),
                "Tensile.backends.ductile_backend": (
                    integration
                    / "projects/hipblaslt/tensilelite/Tensile/backends/ductile_backend.py"
                ),
                "Tensile.ductile.algorithm.ga": (
                    integration
                    / "projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py"
                ),
                "Tensile.ductile.core.space": (
                    integration
                    / "projects/hipblaslt/tensilelite/Tensile/ductile/core/space.py"
                ),
                "geko": (
                    integration
                    / "projects/hipblaslt/utilities/geko/geko/__init__.py"
                ),
                "geko.config_generator.config_generator": (
                    integration
                    / "projects/hipblaslt/utilities/geko/geko/config_generator/config_generator.py"
                ),
                "geko.config_generator.load_input_config": (
                    integration
                    / "projects/hipblaslt/utilities/geko/geko/config_generator/load_input_config.py"
                ),
            }
            imports = {}
            for index, (name, path) in enumerate(module_paths.items()):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(f"{index}:{name}".encode())
                imports[name] = {
                    "path": str(path),
                    "raw_sha256": self._hash(path),
                }
            python_paths = [
                build,
                integration / "projects/hipblaslt/tensilelite",
                integration / "projects/hipblaslt/utilities/geko",
                s10.SITE_PACKAGES,
            ]
            s10._verify_import_closure(
                imports,
                imports,
                imports,
                python_paths=python_paths,
                integration=integration,
                build=build,
                tag="a",
            )
            changed = copy.deepcopy(imports)
            changed["Tensile.LibraryIO"]["raw_sha256"] = "0" * 64
            with _assert_code(self, "manifest_tamper"):
                s10._verify_import_closure(
                    changed,
                    changed,
                    changed,
                    python_paths=python_paths,
                    integration=integration,
                    build=build,
                    tag="a",
                )
            substitute = (
                integration / "projects/hipblaslt/tensilelite/Tensile/substitute.py"
            )
            substitute.write_bytes(b"substitute")
            changed = copy.deepcopy(imports)
            changed["Tensile.LibraryIO"] = {
                "path": str(substitute),
                "raw_sha256": self._hash(substitute),
            }
            with _assert_code(self, "forbidden_import"):
                s10._verify_import_closure(
                    changed,
                    changed,
                    changed,
                    python_paths=python_paths,
                    integration=integration,
                    build=build,
                    tag="a",
                )

    def test_output_manifest_per_field_substitutions_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=self._TEMP_PARENT) as tmp:
            generation = Path(tmp) / "generation"
            output = generation / "out/result.yaml"
            output.parent.mkdir(parents=True)
            output.write_bytes(b"result\n")
            manifest = s10._output_manifest(generation)
            digest = canonical_sha256(manifest)
            s10._verify_output_manifest_closure(
                manifest, digest, digest, generation=generation, tag="a"
            )
            cases = {
                "entry_hash": (
                    [{**manifest[0], "raw_sha256": "0" * 64}],
                    digest,
                    digest,
                ),
                "manifest_hash": (manifest, "0" * 64, digest),
                "tracked_hash": (manifest, digest, "0" * 64),
            }
            for name, arguments in cases.items():
                with (
                    self.subTest(name=name),
                    _assert_code(self, "generation_manifest_mismatch"),
                ):
                    s10._verify_output_manifest_closure(
                        *arguments, generation=generation, tag="a"
                    )

    def test_derived_native_generation_reference_substitutions_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=self._TEMP_PARENT) as tmp:
            scratch = Path(tmp)
            manifests = scratch / "manifests"
            manifests.mkdir()
            derived = scratch / "derived-input.yaml"
            derived.write_bytes(b"derived\n")
            output_manifest = [{"path": "out/result.yaml", "raw_sha256": "1" * 64}]
            runs = []
            actual = {}
            for tag in ("a", "b"):
                native_path = manifests / f"native-{tag}.json"
                generation_path = manifests / f"generation-{tag}.json"
                native_path.write_text("{}\n", encoding="utf-8")
                generation_path.write_text(
                    json.dumps(
                        {
                            "output_manifest": output_manifest,
                            "output_manifest_sha256": canonical_sha256(
                                output_manifest
                            ),
                        }
                    ),
                    encoding="utf-8",
                )
                actual_path = scratch / f"run-{tag}/generation/out/result.yaml"
                actual_path.parent.mkdir(parents=True)
                actual_path.write_bytes(b"actual\n")
                actual[f"run_{tag}_path"] = s10._rel(actual_path)
                actual[f"run_{tag}_raw_sha256"] = self._hash(actual_path)
                runs.append(
                    {
                        "tag": tag,
                        "native": {
                            "path": s10._rel(native_path),
                            "raw_sha256": self._hash(native_path),
                        },
                        "generation": {
                            "path": s10._rel(generation_path),
                            "raw_sha256": self._hash(generation_path),
                        },
                    }
                )
            provenance = {
                "derived_input": {
                    "path": s10._rel(derived),
                    "raw_sha256": self._hash(derived),
                    "derivation": {"kind": "fixture"},
                },
                "runs": runs,
                "generation_parity": {
                    "manifest_sha256": canonical_sha256(output_manifest),
                    "qualifying_relative_path": "out/result.yaml",
                },
                "actual_yaml": actual,
            }
            with (
                mock.patch.object(
                    s10,
                    "_derive_input",
                    return_value=(b"derived\n", {"kind": "fixture"}),
                ),
                mock.patch.object(s10, "_verify_native_raw_manifest"),
                mock.patch.object(s10, "_verify_generation_raw_manifest"),
            ):
                self.assertEqual(
                    s10._verify_raw_lineage(
                        provenance, expected_scratch_root=scratch
                    ),
                    scratch,
                )
                cases = {
                    "derived_hash": ("derived_input", None),
                    "native_hash": ("native", 0),
                    "generation_hash": ("generation", 0),
                }
                for name, (field, index) in cases.items():
                    with self.subTest(name=name):
                        changed = copy.deepcopy(provenance)
                        if index is None:
                            changed[field]["raw_sha256"] = "0" * 64
                        else:
                            changed["runs"][index][field]["raw_sha256"] = "0" * 64
                        with _assert_code(self, "manifest_tamper"):
                            s10._verify_raw_lineage(
                                changed, expected_scratch_root=scratch
                            )


class TestLockLifecycle(unittest.TestCase):
    def test_recursive_archives_and_exact_successor_lifecycle(self):
        parent = s10._verify_r10_parent_archive(rehash_raw_tree=False)
        self.assertEqual(parent, s10._r10_parent_reference())
        authority_path = (
            s10.R10_CHILD_RAW_ROOT / "authority/r10-adjudication.md"
        )
        lifecycle = s10._current_lifecycle_fields(
            {
                "path": s10._rel(authority_path),
                "raw_sha256": s10.R10_RECOVERY_AUTHORITY_SHA256,
            }
        )
        real_sha256_file = s10.sha256_file

        def fixture_hash(path):
            if Path(path) == authority_path:
                return s10.R10_RECOVERY_AUTHORITY_SHA256
            return real_sha256_file(path)

        with (
            mock.patch.object(Path, "is_file", return_value=True),
            mock.patch.object(Path, "is_symlink", return_value=False),
            mock.patch.object(s10, "sha256_file", side_effect=fixture_hash),
        ):
            s10._verify_successor_fields(lifecycle, role="fixture")
        cases = {
            "wrong_generation": ("generation", "successor-004"),
            "evidence_reuse": ("evidence_reuse", True),
            "cycle": (
                "parent_lock",
                {**lifecycle["parent_lock"], "generation": "successor-003"},
            ),
            "sibling": (
                "parent_lock",
                {
                    **lifecycle["parent_lock"],
                    "lock": {
                        **lifecycle["parent_lock"]["lock"],
                        "lock_id": "s10-lock-" + "0" * 64,
                    },
                },
            ),
            "wrong_authority": (
                "recovery_authority",
                {
                    **lifecycle["recovery_authority"],
                    "raw_sha256": "0" * 64,
                },
            ),
        }
        for name, (field, value) in cases.items():
            with self.subTest(name=name):
                changed = copy.deepcopy(lifecycle)
                changed[field] = value
                code = (
                    "recovery_authority_mismatch"
                    if name == "wrong_authority"
                    else "successor_lifecycle_mismatch"
                )
                with (
                    mock.patch.object(Path, "is_file", return_value=True),
                    mock.patch.object(Path, "is_symlink", return_value=False),
                    mock.patch.object(s10, "sha256_file", side_effect=fixture_hash),
                    _assert_code(self, code),
                ):
                    s10._verify_successor_fields(changed, role=name)

    def test_r9_archive_manifest_drift_is_rejected(self):
        real_sha256_file = s10.sha256_file
        failure_path = s10.R9_ARCHIVE_MANIFESTS["failure"][0]

        def drift(path):
            if Path(path) == failure_path:
                return "0" * 64
            return real_sha256_file(path)

        with (
            mock.patch.object(s10, "sha256_file", side_effect=drift),
            _assert_code(self, "parent_archive_drift"),
        ):
            s10._verify_r9_parent_archive(rehash_raw_tree=False)

    def test_r9_single_use_claim_identity_drift_is_rejected(self):
        real_sha256_file = s10.sha256_file

        def drift(path):
            if Path(path) == s10.R9_CLAIM_PATH:
                return "0" * 64
            return real_sha256_file(path)

        with (
            mock.patch.object(s10, "sha256_file", side_effect=drift),
            _assert_code(self, "parent_claim_drift"),
        ):
            s10._verify_r9_parent_archive(rehash_raw_tree=False)

    def test_r10_archive_manifest_drift_is_rejected(self):
        real_sha256_file = s10.sha256_file
        failure_path = s10.R10_ARCHIVE_MANIFESTS["failure"][0]

        def drift(path):
            if Path(path) == failure_path:
                return "0" * 64
            return real_sha256_file(path)

        with (
            mock.patch.object(s10, "sha256_file", side_effect=drift),
            _assert_code(self, "parent_archive_drift"),
        ):
            s10._verify_r10_parent_archive(rehash_raw_tree=False)

    def test_r10_single_use_claim_identity_drift_is_rejected(self):
        real_sha256_file = s10.sha256_file

        def drift(path):
            if Path(path) == s10.R10_CLAIM_PATH:
                return "0" * 64
            return real_sha256_file(path)

        with (
            mock.patch.object(s10, "sha256_file", side_effect=drift),
            _assert_code(self, "parent_claim_drift"),
        ):
            s10._verify_r10_parent_archive(rehash_raw_tree=False)

    def test_parent_raw_roots_cannot_be_reactivated(self):
        for path in (
            s10.R8_PARENT_RAW_ROOT,
            s10.R8_PARENT_RAW_ROOT / "child",
            s10.R8_ORIGINAL_PARENT_RAW_ROOT,
            s10.R8_ORIGINAL_PARENT_RAW_ROOT / "child",
            s10.R9_PARENT_RAW_ROOT,
            s10.R9_PARENT_RAW_ROOT / "child",
            s10.R9_ORIGINAL_PARENT_RAW_ROOT,
            s10.R9_ORIGINAL_PARENT_RAW_ROOT / "child",
            s10.R10_PARENT_RAW_ROOT,
            s10.R10_PARENT_RAW_ROOT / "child",
            s10.R10_ORIGINAL_PARENT_RAW_ROOT,
            s10.R10_ORIGINAL_PARENT_RAW_ROOT / "child",
        ):
            with self.subTest(path=path), _assert_code(
                self, "parent_evidence_reuse"
            ):
                s10._assert_scratch_root(path)

    def test_live_h4_parser_enforces_resources_partition_and_pid_mapping(self):
        raw = json.dumps(
            {
                "card0": {
                    "Unique ID": "0x0000000000000001",
                    "Serial Number": "SERIAL-0",
                    "PCI Bus": "0000:01:00.0",
                    "GFX Version": "gfx942",
                    "Compute Partition": "SPX",
                    "Memory Partition": "NPS1",
                    "GPU use (%)": "0",
                    "GPU Memory Allocated (VRAM%)": "1",
                    "VRAM Total Used Memory (B)": "100",
                    "VRAM Total Memory (B)": "10000",
                }
            }
        ).encode()
        parsed = s10._parse_live_devices(raw, {})
        self.assertTrue(parsed[0]["eligible"])
        cases = {
            "foreign_pid": ({1234: [0]}, "mapped_kfd_pid"),
            "gpu_use": ({}, "gpu_use_nonzero"),
            "vram": ({}, "vram_allocation_above_one_percent"),
            "partition": ({}, "wrong_compute_partition"),
        }
        for name, (pid_map, reason) in cases.items():
            with self.subTest(name=name):
                changed = json.loads(raw)
                if name == "gpu_use":
                    changed["card0"]["GPU use (%)"] = "1"
                elif name == "vram":
                    changed["card0"]["GPU Memory Allocated (VRAM%)"] = "1.1"
                elif name == "partition":
                    changed["card0"]["Compute Partition"] = "CPX"
                item = s10._parse_live_devices(json.dumps(changed).encode(), pid_map)[0]
                self.assertFalse(item["eligible"])
                self.assertIn(reason, item["ineligibility_reasons"])

    def test_live_h4_selection_requires_three_stable_samples_and_exact_key(self):
        samples = _live_samples(
            [
                [_live_device(0, 100), _live_device(1, 120)],
                [_live_device(0, 200), _live_device(1, 130)],
                [_live_device(0, 150), _live_device(1, 140)],
            ]
        )
        device, key = s10._select_live_device(samples)
        self.assertEqual(device["container_visible_index"], 1)
        self.assertEqual(key, [140, 1, "0x0000000000000002"])
        with _assert_code(self, "h4_malformed"):
            s10._select_live_device(samples[:2])
        drift = copy.deepcopy(samples)
        drift[2]["devices"][0]["identity"]["serial_number"] = "DRIFT"
        for sample in drift:
            sample["devices"] = [sample["devices"][0]]
        with _assert_code(self, "live_gpu_unavailable"):
            s10._select_live_device(drift)

    def test_pid_gpu_parser_rejects_truncated_mapping(self):
        parsed = s10._parse_pid_gpu_map(
            b"PID 123 is using 2 DRM device(s):\n0 7 \n"
        )
        self.assertEqual(parsed, {123: [0, 7]})
        with _assert_code(self, "h4_malformed"):
            s10._parse_pid_gpu_map(b"PID 123 is using 1 DRM device(s):\n")

    def test_effective_lock_identity_is_content_derived_and_substitution_fails(self):
        base = {"schema_version": "1.0.0", "kind": "test", "payload": [1, 2, 3]}
        first = s10._derived_lock(base)
        second = s10._derived_lock(base)
        self.assertEqual(first, second)
        self.assertEqual(first["body_sha256"], canonical_sha256(base))
        self.assertEqual(first["lock_id"], f"s10-lock-{first['body_sha256']}")
        changed = s10._derived_lock({**base, "payload": [1, 2, 4]})
        self.assertNotEqual(first["lock_id"], changed["lock_id"])
        with _assert_code(self, "lock_binding_mismatch"):
            s10._derived_lock({**base, "body_sha256": "0" * 64})

    def test_all_six_postlock_targets_are_rejected_individually(self):
        expected = (
            s10.ENVIRONMENT_PATH,
            s10.LOCK_PATH,
            s10.MAPPING_PATH,
            s10.SMOKE_PATH,
            s10.NOISE_PATH,
            s10.DECISION_PATH,
        )
        self.assertEqual(s10.POST_LOCK_PATHS, expected)
        for target in expected:
            with self.subTest(target=target.name):
                with (
                    mock.patch.object(
                        Path,
                        "exists",
                        autospec=True,
                        side_effect=lambda path, target=target: path == target,
                    ),
                    _assert_code(self, "early_postlock_artifact"),
                ):
                    s10._reject_early_postlock_targets()

    def test_early_guard_precedes_preflight_and_writes_in_every_entry(self):
        entry_sources = {
            "prepare": inspect.getsource(s10.prepare),
            "prelock_check": inspect.getsource(s10.prelock_check),
            "create_lock": inspect.getsource(s10.create_lock),
            "validate_phase": inspect.getsource(s10.validate_phase),
        }
        for name, source in entry_sources.items():
            with self.subTest(name=name):
                guard = source.index("_reject_early_postlock_targets")
                later = [
                    source.find(token)
                    for token in (
                        "_preflight(",
                        "scratch_root.mkdir(",
                        "atomic_write_json(",
                        "write_effective_lock(",
                        "_verify_prelock_artifacts(",
                    )
                    if source.find(token) >= 0
                ]
                self.assertTrue(later)
                self.assertLess(guard, min(later))


class TestMappingSmokeNoiseDecision(unittest.TestCase):
    def test_mapping_pass_uses_canonical_python_argv_and_environment(self):
        lock = {"mapping_candidates": [], "anchor_hashes": []}
        provenance = {
            "runs": [
                {
                    "integration": {"path": "integration.json"},
                    "native": {"path": "native.json"},
                }
            ]
        }
        integration = {"root": "fresh-successor/integration"}
        native = {"binary": {"path": "fresh-successor/native/rocisa/_rocisa.so"}}
        captured = {}
        completed = mock.Mock(returncode=0, stdout=b"", stderr=b"")

        def run_logged(argv, **kwargs):
            captured["argv"] = argv
            captured["env"] = kwargs["env"]
            return completed, {"stderr": {"raw_sha256": "f" * 64}}

        with tempfile.TemporaryDirectory() as tmp:
            pass_root = Path(tmp) / "pass-a"
            with (
                mock.patch.object(s10, "_mapping_request"),
                mock.patch.object(
                    s10,
                    "strict_load_json",
                    side_effect=[provenance, integration, native],
                ),
                mock.patch.object(s10, "_run_logged", side_effect=run_logged),
                mock.patch.object(s10, "_output_manifest", return_value=[]),
                mock.patch.object(
                    s10, "_parse_marked_json", return_value={"rows": [{}] * 30}
                ),
                mock.patch.object(s10, "_enrich_mapping_rows", return_value={}),
                mock.patch.object(
                    s10,
                    "_bound_file",
                    return_value={"path": "fixture", "raw_sha256": "e" * 64},
                ),
                mock.patch.object(s10, "_rel", side_effect=lambda path: str(path)),
            ):
                s10._mapping_pass(
                    lock,
                    pass_root=pass_root,
                    pass_name="mapping-pass-a",
                    native_helper=Path(tmp) / "helper",
                )
        integration_root = s10.ROOT / integration["root"]
        native_parent = (s10.ROOT / native["binary"]["path"]).parent
        self.assertEqual(captured["argv"][:3], [str(s10.PYTHON), "-S", "-c"])
        self.assertEqual(
            captured["env"]["PYTHONPATH"],
            os.pathsep.join(
                str(path)
                for path in s10._python_path(integration_root, native_parent)
            ),
        )

    def test_minus_s_old_import_failure_and_repaired_request_boundary(self):
        code = (
            "import json,joblib,sys;"
            "request=json.load(open(sys.argv[1],encoding='utf-8'));"
            "print('REQUEST_READ',len(request['candidates']))"
        )
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text('{"candidates":[]}\n', encoding="utf-8")
            old_env = s10._base_env()
            old_env["PYTHONPATH"] = tmp
            old = subprocess.run(
                [str(s10.PYTHON), "-S", "-c", code, str(request)],
                env=old_env,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(old.returncode, 0)
            self.assertIn(b"joblib", old.stderr)
            repaired_env = s10._base_env()
            repaired_env["PYTHONPATH"] = os.pathsep.join(
                [tmp, str(s10.SITE_PACKAGES)]
            )
            repaired = subprocess.run(
                [str(s10.PYTHON), "-S", "-c", code, str(request)],
                env=repaired_env,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertEqual(repaired.returncode, 0, repaired.stderr.decode())
        self.assertEqual(repaired.stdout, b"REQUEST_READ 0\n")

    def test_mapping_requires_exact_deterministic_thirty_rows(self):
        lock = {
            "mapping_candidates": [{"config_hash": f"{index:064x}"} for index in range(10)],
            "anchor_hashes": ["1" * 64, "2" * 64, "3" * 64],
        }
        raw = {
            "lock_raw_sha256": "f" * 64,
            "rows": [],
            "rerun_rows": [],
            "executor": {},
        }
        with (
            mock.patch.object(s10, "_load_lock", return_value=(lock, "f" * 64)),
            _assert_code(self, "mapping_unresolved"),
        ):
            s10._mapping_from_raw(raw)

    def test_synthetic_mapping_taxonomy_and_entry_split(self):
        candidates = [
            {"config_hash": f"{index + 1:064x}"} for index in range(10)
        ]
        sizes = [[8, 8, 1, 32], [16, 8, 1, 64], [32, 8, 1, 128]]
        lock = {
            "mapping_candidates": candidates,
            "anchor_hashes": [item["config_hash"] for item in candidates[:3]],
        }
        rows = []
        for candidate in candidates:
            for size in sizes:
                rows.append(
                    {
                        "config_hash": candidate["config_hash"],
                        "size": size,
                        "raw_indices": {},
                        "raw_values": {},
                        "expanded_groups": {},
                        "resolved_solution": None,
                        "codegen_identity": None,
                        "size_mapping": None,
                        "effective_gsu": None,
                        "resolved_sentinels": {},
                        "formocast_input": None,
                        "field_provenance": {},
                        "status": "rejected",
                        "rejection": {
                            "stage": "solution_resolution",
                            "reason_code": "pinned_validation_boundary_none",
                            "reason_text": "synthetic pinned boundary",
                            "internal_subreason": "internal_subreason_unknown",
                            "log_sha256": "e" * 64,
                        },
                        "prediction": None,
                        "tie": False,
                    }
                )
        raw = {
            "lock_raw_sha256": "f" * 64,
            "rows": rows,
            "rerun_rows": copy.deepcopy(rows),
            "executor": {"kind": "synthetic"},
        }
        with (
            mock.patch.object(s10, "_load_lock", return_value=(lock, "f" * 64)),
            mock.patch.object(
                s10, "strict_load_json", return_value={"selected_sizes": sizes}
            ),
        ):
            document = s10._mapping_from_raw(raw)
        self.assertEqual(document["mapping_evidence_integrity"]["status"], "PASS")
        self.assertEqual(document["mapping_entry"]["status"], "FAIL")
        self.assertEqual(
            document["mapping_entry"]["failure_id"], "S10-MAPPING-ENTRY-FAIL"
        )
        unexpected = copy.deepcopy(raw)
        unexpected["rows"][0]["rejection"]["reason_code"] = "AttributeError"
        unexpected["rerun_rows"] = copy.deepcopy(unexpected["rows"])
        with (
            mock.patch.object(s10, "_load_lock", return_value=(lock, "f" * 64)),
            mock.patch.object(
                s10, "strict_load_json", return_value={"selected_sizes": sizes}
            ),
            _assert_code(self, "postlock_harness_defect"),
        ):
            s10._mapping_from_raw(unexpected)

    def _noise_raw(self):
        anchors = ["1" * 64, "2" * 64, "3" * 64]
        sizes = [[8, 8, 1, 32], [16, 8, 1, 64], [32, 8, 1, 128]]
        observations = []
        order = 0
        for anchor_index, anchor in enumerate(anchors):
            for size_index, size in enumerate(sizes):
                for repeat in range(7):
                    observations.append(
                        {
                            "anchor_hash": anchor,
                            "size": size,
                            "repeat": repeat,
                            "order": order,
                            "timed_iterations": 100,
                            "quality": 100.0 + anchor_index + size_index,
                            "correctness": "pass",
                            "raw_output_sha256": f"{order + 1:064x}",
                        }
                    )
                    order += 1
        lock = {
            "anchor_hashes": anchors,
            "noise_schedule": {"balanced_order_seed": 7},
        }
        return lock, sizes, {
            "lock_raw_sha256": "f" * 64,
            "levels": [{"multiplier": 1, "observations": observations}],
            "reduce_fn": "mean",
            "monitoring": {
                "fixed_device": {"container_visible_index": 0},
                "maximum_during_sample_period_seconds": 1,
                "levels": [{"multiplier": 1, "selected_attempt": 1}],
            },
        }

    def test_complete_noise_panel_and_formulas(self):
        lock, sizes, raw = self._noise_raw()
        with (
            mock.patch.object(s10, "_load_lock", return_value=(lock, "f" * 64)),
            mock.patch.object(
                s10,
                "strict_load_json",
                return_value={"selected_sizes": sizes},
            ),
        ):
            result = s10._noise_from_raw(raw)
        self.assertEqual(result["status"], "stable")
        self.assertEqual(len(result["completed_levels"][0]["observations"]), 63)
        self.assertAlmostEqual(result["p95_cv"], 0.0)
        self.assertAlmostEqual(result["delta_noise"], 0.0)
        self.assertEqual(result["monitoring"], raw["monitoring"])

    def test_postlock_executor_source_keeps_r7_and_toolchain_boundaries(self):
        mapping_source = s10._mapping_executor_code()
        native_source = s10._mapping_native_helper_source().decode("utf-8")
        mapping_entry = inspect.getsource(s10.mapping)
        self.assertIn("makeIsaInfoMap", mapping_source)
        self.assertIn("Assembler(request[\"compiler\"]", mapping_source)
        self.assertIn("passPostKernelInfoToSolution", mapping_source)
        self.assertIn("passPostKernelInfoToLibrary", mapping_source)
        self.assertIn("getKernelFileBase", mapping_source)
        self.assertIn("visited_kernel_bases", mapping_source)
        self.assertIn("kernel.duplicate", mapping_source)
        self.assertIn('kernel[\"BaseName\"] = base', mapping_source)
        self.assertIn("except BaseException:", mapping_source)
        self.assertNotIn("except BaseException as exc", mapping_source)
        self.assertNotIn("AttributeError:", mapping_source)
        self.assertIn("result.src", mapping_source)
        self.assertNotIn("result.source", mapping_source)
        self.assertIn("solution.getSizeMapping()", native_source)
        self.assertIn("solution.calculateAutoGSU(problem, nullptr)", native_source)
        self.assertIn("_execute_mapping_raw()", mapping_entry)
        self.assertNotIn("_load_postlock_raw", mapping_entry)

    def test_mapping_executor_unexpected_exit_is_harness_defect(self):
        lock = {"mapping_candidates": [], "anchor_hashes": []}
        provenance = {
            "runs": [
                {
                    "integration": {"path": "integration.json"},
                    "native": {"path": "native.json"},
                }
            ]
        }
        integration = {"root": "fresh-successor/integration"}
        native = {"binary": {"path": "fresh-successor/native/rocisa/_rocisa.so"}}
        completed = mock.Mock(returncode=70, stdout=b"", stderr=b"AttributeError")
        command = {"stderr": {"raw_sha256": "f" * 64}}
        with tempfile.TemporaryDirectory() as tmp:
            with (
                mock.patch.object(s10, "_mapping_request"),
                mock.patch.object(
                    s10,
                    "strict_load_json",
                    side_effect=[provenance, integration, native],
                ),
                mock.patch.object(
                    s10, "_run_logged", return_value=(completed, command)
                ),
                mock.patch.object(s10, "_output_manifest", return_value=[]),
                _assert_code(self, "postlock_harness_defect"),
            ):
                s10._mapping_pass(
                    lock,
                    pass_root=Path(tmp) / "pass-a",
                    pass_name="mapping-pass-a",
                    native_helper=Path(tmp) / "helper",
                )

    def test_terminal_commands_refuse_after_decision(self):
        with (
            mock.patch.object(Path, "exists", return_value=True),
            _assert_code(self, "terminal_command_refused"),
        ):
            s10._require_not_terminal("mapping")

    def test_monitor_rejects_foreign_mapped_pid(self):
        lock = {"device": _live_device(0, 10)["identity"]}
        devices = [_live_device(0, 10)]
        devices[0]["mapped_kfd_pids"] = [101, 202]
        devices[0]["eligible"] = False
        devices[0]["ineligibility_reasons"] = ["mapped_kfd_pid"]
        completed = mock.Mock(returncode=0, stdout=b"", stderr=b"")
        command = {"started_at": "2026-07-25T00:00:00Z"}
        with (
            mock.patch.object(
                s10, "_run_logged", return_value=(completed, command)
            ),
            mock.patch.object(s10, "_parse_pid_gpu_map", return_value={}),
            mock.patch.object(s10, "_parse_live_devices", return_value=devices),
        ):
            sample, contaminated = s10._monitor_sample(
                lock=lock,
                phase="during",
                sample_index=0,
                cwd=_REPO,
                log_root=_REPO,
                name_prefix="fixture",
                allowed_pids={101},
                seconds_since_previous=None,
            )
        self.assertTrue(contaminated)
        self.assertIn(
            "during:foreign_mapped_kfd_pids=202",
            sample["contamination_reasons"],
        )

    def test_noise_rejects_incomplete_mixed_or_failed_correctness(self):
        lock, sizes, raw = self._noise_raw()
        cases = []
        incomplete = copy.deepcopy(raw)
        incomplete["levels"][0]["observations"].pop()
        cases.append(("noise_incomplete", incomplete))
        mixed = copy.deepcopy(raw)
        mixed["levels"][0]["multiplier"] = 2
        mixed["levels"].append(copy.deepcopy(mixed["levels"][0]))
        mixed["levels"][1]["multiplier"] = 1
        cases.append(("noise_incomplete", mixed))
        incorrect = copy.deepcopy(raw)
        incorrect["levels"][0]["observations"][0]["correctness"] = "fail"
        cases.append(("correctness_failure", incorrect))
        for code, case in cases:
            with self.subTest(code=code):
                with (
                    mock.patch.object(s10, "_load_lock", return_value=(lock, "f" * 64)),
                    mock.patch.object(
                        s10,
                        "strict_load_json",
                        return_value={"selected_sizes": sizes},
                    ),
                    _assert_code(self, code),
                ):
                    s10._noise_from_raw(case)

    def test_go_schema_cannot_be_claimed_from_partial_or_proxy_criteria(self):
        names = [
            "actual_guidance",
            "three_sizes",
            "h4_and_environment",
            "mapping_evidence_integrity",
            "mapping_entry",
            "smoke_correctness",
            "noise_stable",
        ]
        decision = {
            "schema_version": "1.0.0",
            "kind": "s10_decision",
            "checkpoint_id": "S10",
            "status": "complete",
            "created_at": "2026-07-25T00:00:00Z",
            "effective_lock_raw_sha256": "f" * 64,
            "study_mode": "ready_actual_yaml_guidance",
            "completion_correctness": "complete",
            "scientific_outcome": "positive",
            "criterion": "S1_ENTRY_GO",
            "edge": "S1_ENTRY_GO -> S11",
            "gates": [
                {
                    "name": name,
                    "role": (
                        "prerequisite"
                        if index < 3
                        else (
                            "evidence_integrity"
                            if index == 3
                            else "entry_gate" if index == 4 else "execution_gate"
                        )
                    ),
                    "status": "FAIL" if index == 0 else "PASS",
                    "execution": "complete",
                    "reason_code": "fixture",
                    "reason_text": "fixture",
                    "failure_id": "fixture" if index == 0 else None,
                    "blocked_by": [],
                    "evidence": [
                        {
                            "path": f"gate-{index}",
                            "raw_sha256": f"{index + 1:064x}",
                        }
                    ],
                    "blocked_absence": None,
                }
                for index, name in enumerate(names)
            ],
            "failure_taxonomy": [],
            "artifacts": [
                {"path": f"artifact-{index}", "raw_sha256": f"{index + 1:064x}"}
                for index in range(4)
            ],
            "decision_evidence": None,
            "claim_limitations": ["no downstream claim"],
        }
        with self.assertRaises(EvidenceValidationError):
            s10._validate(decision, context="proxy GO")


if __name__ == "__main__":
    unittest.main()
