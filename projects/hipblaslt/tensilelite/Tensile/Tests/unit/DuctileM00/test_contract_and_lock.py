# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from Tensile.ductile.config import update
from Tensile.ductile.m00.canonical import (
    ContractError,
    canonical_json_bytes,
    load_yaml_strict,
)
from Tensile.ductile.m00.contract import (
    AmendmentChain,
    ContractStore,
    ProtocolLock,
)


REPO = Path(__file__).resolve().parents[7]
PROTOCOL = REPO / "study_docs/research/ductile-origami-warmstart/protocol"
CONTRACT = PROTOCOL / "experiment-contract.yaml"


class TestContractAndLock(unittest.TestCase):
    def test_canonical_contract_default_is_cwd_independent(self):
        tensilelite = REPO / "projects/hipblaslt/tensilelite"
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(tensilelite)
        for cwd in (REPO, Path(tempfile.gettempdir())):
            with self.subTest(cwd=cwd):
                result = subprocess.run(
                    [
                        os.fspath(Path(os.sys.executable)),
                        "-m", "Tensile.ductile.m00.runner",
                        "validate-contract",
                    ],
                    cwd=cwd,
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(0, result.returncode, result.stderr)

    def test_duplicate_alias_and_nonfinite_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            duplicate = root / "duplicate.yaml"
            duplicate.write_text("x: 1\nx: 2\n", encoding="utf-8")
            alias = root / "alias.yaml"
            alias.write_text("x: &x [1]\ny: *x\n", encoding="utf-8")
            with self.assertRaises(ContractError):
                load_yaml_strict(duplicate)
            with self.assertRaises(ContractError):
                load_yaml_strict(alias)
            with self.assertRaises(ContractError):
                canonical_json_bytes({"x": float("nan")})

    def test_execution_constants_come_only_from_effective_contract(self):
        store = ContractStore(CONTRACT)
        profile = store.profile("fixed_horizon")
        self.assertEqual(1701, profile.seed)
        self.assertEqual(6, profile.pop_size)
        with self.assertRaisesRegex(ContractError, "overrides"):
            store.assert_no_execution_overrides(
                ["--seed=9"], {"M00_MODEL": "forbidden"}
            )

    def test_dependency_neutral_recursive_merge(self):
        merged = update({
            "selection": {
                "common": {"ratio": 0.25},
                "tournament": {"k": 3},
            },
            "weights": [{"a": [1.0, 2.0]}],
        })
        self.assertEqual(0.25, merged["selection"]["common"]["ratio"])
        self.assertTrue(merged["selection"]["common"]["replacement"])
        self.assertEqual(3, merged["selection"]["tournament"]["k"])
        self.assertEqual([{"a": [1.0, 2.0]}], merged["weights"])

    def test_base_contract_mutation_without_amendment_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "protocol"
            shutil.copytree(PROTOCOL, copied)
            contract = copied / "experiment-contract.yaml"
            text = contract.read_text(encoding="utf-8")
            contract.write_text(
                text.replace("protocol_version: 1.0.0",
                             "protocol_version: 1.0.9"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "genesis"):
                ContractStore(contract)

    def test_valid_linked_append_preserves_base(self):
        store = ContractStore(CONTRACT)
        with tempfile.TemporaryDirectory() as temporary:
            chain_path = Path(temporary) / "amendment-chain.jsonl"
            shutil.copyfile(PROTOCOL / "amendment-chain.jsonl", chain_path)
            chain = AmendmentChain(
                chain_path, PROTOCOL / "schemas/amendment.schema.json"
            )
            base_bytes = canonical_json_bytes(store.base_contract)
            record = chain.append(
                store.base_contract,
                store.schema,
                protocol_version="1.0.1",
                owner="unit-test-owner",
                occurred_at="2026-07-24T01:00:00Z",
                reason="exercise append-only protocol",
                decision_provenance="unit-test",
                changed_keys=["/study/protocol_version"],
                operations=[{
                    "op": "replace",
                    "path": "/study/protocol_version",
                    "value": "1.0.1",
                }],
            )
            effective, hashes = chain.evaluate(
                store.base_contract, store.schema
            )
        self.assertEqual("1.0.1", effective["study"]["protocol_version"])
        self.assertEqual(2, len(hashes))
        self.assertEqual(base_bytes, canonical_json_bytes(store.base_contract))
        self.assertEqual(1, record["sequence"])

    def test_bad_parent_and_chain_rewrite_are_rejected(self):
        store = ContractStore(CONTRACT)
        with tempfile.TemporaryDirectory() as temporary:
            chain_path = Path(temporary) / "chain.jsonl"
            shutil.copyfile(PROTOCOL / "amendment-chain.jsonl", chain_path)
            chain = AmendmentChain(
                chain_path, PROTOCOL / "schemas/amendment.schema.json"
            )
            line = json.loads(chain_path.read_text(encoding="utf-8"))
            line["owner"] = "rewritten-owner"
            chain_path.write_text(
                json.dumps(line, sort_keys=True, separators=(",", ":")) +
                "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "rewritten"):
                chain.assert_append_only()

    def test_bad_parent_same_version_and_tail_deletion_are_rejected(self):
        store = ContractStore(CONTRACT)
        operation = [{
            "op": "replace",
            "path": "/study/protocol_version",
            "value": "1.0.1",
        }]
        with tempfile.TemporaryDirectory() as temporary:
            chain_path = Path(temporary) / "chain.jsonl"
            shutil.copyfile(PROTOCOL / "amendment-chain.jsonl", chain_path)
            chain = AmendmentChain(
                chain_path, PROTOCOL / "schemas/amendment.schema.json"
            )
            chain.append(
                store.base_contract, store.schema,
                protocol_version="1.0.1",
                owner="owner", occurred_at="2026-07-24T01:00:00Z",
                reason="linked test", decision_provenance="unit-test",
                changed_keys=["/study/protocol_version"],
                operations=operation,
            )
            lines = chain_path.read_text(encoding="utf-8").splitlines()
            bad = json.loads(lines[1])
            bad["parent_line_sha256"] = "0" * 64
            chain_path.write_text(
                lines[0] + "\n" +
                json.dumps(bad, sort_keys=True, separators=(",", ":")) +
                "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "parent hash"):
                AmendmentChain(
                    chain_path, PROTOCOL / "schemas/amendment.schema.json"
                ).evaluate(store.base_contract, store.schema)

            chain_path.write_text(lines[0] + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "rewritten"):
                chain.assert_append_only()

            same_path = Path(temporary) / "same.jsonl"
            shutil.copyfile(PROTOCOL / "amendment-chain.jsonl", same_path)
            same = AmendmentChain(
                same_path, PROTOCOL / "schemas/amendment.schema.json"
            )
            with self.assertRaisesRegex(
                    ContractError, "version did not increase"):
                same.append(
                    store.base_contract, store.schema,
                    protocol_version="1.0.0",
                    owner="owner",
                    occurred_at="2026-07-24T01:00:00Z",
                    reason="same version",
                    decision_provenance="unit-test",
                    changed_keys=["/study/protocol_version"],
                    operations=operation,
                )

    def test_missing_amendment_provenance_is_rejected(self):
        store = ContractStore(CONTRACT)
        with tempfile.TemporaryDirectory() as temporary:
            chain_path = Path(temporary) / "chain.jsonl"
            shutil.copyfile(PROTOCOL / "amendment-chain.jsonl", chain_path)
            chain = AmendmentChain(
                chain_path, PROTOCOL / "schemas/amendment.schema.json"
            )
            with self.assertRaises(ContractError):
                chain.append(
                    store.base_contract,
                    store.schema,
                    protocol_version="1.0.1",
                    owner="",
                    occurred_at="",
                    reason="",
                    decision_provenance="",
                    changed_keys=["/study/protocol_version"],
                    operations=[{
                        "op": "replace",
                        "path": "/study/protocol_version",
                        "value": "1.0.1",
                    }],
                )

    def test_amendment_changed_key_set_must_match_operations(self):
        store = ContractStore(CONTRACT)
        with tempfile.TemporaryDirectory() as temporary:
            chain_path = Path(temporary) / "chain.jsonl"
            shutil.copyfile(PROTOCOL / "amendment-chain.jsonl", chain_path)
            chain = AmendmentChain(
                chain_path, PROTOCOL / "schemas/amendment.schema.json"
            )
            with self.assertRaisesRegex(ContractError, "changed-key"):
                chain.append(
                    store.base_contract,
                    store.schema,
                    protocol_version="1.0.1",
                    owner="owner",
                    occurred_at="2026-07-24T01:00:00Z",
                    reason="negative changed-key test",
                    decision_provenance="unit-test",
                    changed_keys=["/search/scenarios/0/seed"],
                    operations=[{
                        "op": "replace",
                        "path": "/study/protocol_version",
                        "value": "1.0.1",
                    }],
                )

    def test_canonical_protocol_lock_when_initialized(self):
        lock_path = PROTOCOL / "protocol-lock.json"
        if not lock_path.exists():
            self.skipTest("protocol lock is initialized after pre-lock tests")
        store = ContractStore(CONTRACT)
        before = lock_path.read_bytes()
        lock = ProtocolLock(store, REPO).verify()
        self.assertEqual("locked", lock["lock_state"])
        whitelist = json.loads(
            (PROTOCOL / "m00-whitelist.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(whitelist["protected_paths"]),
            set(lock["protected_path_sha256"]),
        )
        self.assertEqual(11, len(lock["protected_path_sha256"]))
        for relative, expected in lock["protected_path_sha256"].items():
            import hashlib
            self.assertEqual(
                expected,
                hashlib.sha256((REPO / relative).read_bytes()).hexdigest(),
            )
        with self.assertRaisesRegex(Exception, "already exists"):
            ProtocolLock(store, REPO).initialize("must-not-overwrite")
        self.assertEqual(before, lock_path.read_bytes())

    def test_locked_blob_provenance_and_materialized_hashes(self):
        registry = json.loads(
            (PROTOCOL / "revision-registry.json").read_text(encoding="utf-8")
        )
        locked = next(
            entry["object_id"] for entry in registry["entries"]
            if entry["kind"] == "locked_commit"
        )
        imported = [
            entry for entry in registry["entries"]
            if entry["kind"] == "imported_blob"
        ]
        self.assertEqual(15, len(imported))
        for entry in imported:
            with self.subTest(path=entry["path"]):
                object_id = subprocess.check_output(
                    ["git", "rev-parse", f"{locked}:{entry['path']}"],
                    cwd=REPO,
                    text=True,
                ).strip()
                self.assertEqual(entry["object_id"], object_id)
                import hashlib
                materialized = hashlib.sha256(
                    (REPO / entry["path"]).read_bytes()
                ).hexdigest()
                self.assertEqual(
                    entry["materialized_sha256"], materialized
                )


if __name__ == "__main__":
    unittest.main()
