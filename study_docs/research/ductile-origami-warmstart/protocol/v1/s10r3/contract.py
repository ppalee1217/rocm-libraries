# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Strict contract, identity, schema, and effective-lock utilities for S10R3."""

from __future__ import annotations

import copy
import ctypes
import errno
import fcntl
import hashlib
import json
import math
import os
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import jsonschema
import yaml


class ContractError(ValueError):
    """A frozen S10R3 contract or binding invariant was violated."""


PACKAGE_ROOT = Path(__file__).resolve().parent
PROTOCOL_ROOT = PACKAGE_ROOT.parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[5]
DEFAULT_CONTRACT_PATH = PROTOCOL_ROOT / "s10r3-stage1-bounded-cover-entry-contract.yaml"
DEFAULT_SCHEMA_PATH = PROTOCOL_ROOT / "schemas/s10r3-entry.schema.json"
DEFAULT_LOCK_PATH = PROTOCOL_ROOT / "locks/s10r3-stage1-bounded-cover-entry-lock.json"
PLAN_A_FREEZE_ID = "S10R3-PLAN-A"
PLAN_B_FREEZE_ID = "S10R3-PLAN-B-V9"

PHASE1_SEAL_COMMIT = "8ae987bb89558c798b01eff2c27f0a212f534288"
PHASE1_SEAL_PARENT = "d9e52829d39268b52a30dea9ad1ad985731fdbb3"
PREDECESSOR_EFFECTIVE_LOCK_COMMIT = "d9e52829d39268b52a30dea9ad1ad985731fdbb3"
EXPECTED_CONTRACT_SCHEMA_VERSION = 10
EXPECTED_CONTRACT_ID = "S10R3-A46-5-REPRODUCIBLE-MAPPING-FAILURE-RECOVERY-V1"
EXPECTED_CONTRACT_RAW_SHA256 = (
    "f89f37b5b7585fdaaab30db4b2d29c50d951d468b5f39ff8c207cbed119177c0"
)
EXPECTED_CONTRACT_CANONICAL_SHA256 = (
    "7af6cfe8db1c3d28c62e0454e98f4660666c2fad447c6b074669c3bd4df2d71d"
)
EXPECTED_ORACLE_PROJECTION_SHA256 = (
    "185c6ae6c7b255c1330b4723b8a241ba111c0d23715bdb28149b024f78729e1e"
)
EXPECTED_PLAN_A_REVISION = 20
EXPECTED_PLAN_A_PATH = (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/"
    "gates/s10r3/plan_a.md"
)
EXPECTED_PLAN_A_SHA256 = (
    "d2e29f1500862dfff27e5ad205767c6d0e50e4a06f762548387358b94ea58710"
)
EXPECTED_PLAN_A_SIZE_BYTES = 132458
EXPECTED_PLAN_A_FREEZE_SHA256 = (
    "f9422cca2ac256dec9e2e2d9e4bfaf75bc5faebb8f87196ddab45177fdbc6b35"
)
EXPECTED_PLAN_B_REVISION = 9
EXPECTED_PLAN_B_PATH = (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/"
    "gates/s10r3/plan_b.md"
)
EXPECTED_PLAN_B_SHA256 = (
    "16d4798cbb3109364ec5637e8fee03667f421df445581b15b67cfcb5c895f81d"
)
# The complete raw freeze record authenticates its own size field.  Plan-A
# intentionally withholds the goal-oracle byte count from the Plan-A-only
# implementer, so the size is carried from that authenticated record.
EXPECTED_PLAN_B_SIZE_BYTES: int | None = None
EXPECTED_PLAN_B_FREEZE_SHA256 = (
    "ffdb4fffd3764ee16cdf22147998d6a1253967798f6db8974b65db7763f9fc86"
)
SELF_HASH_PLACEHOLDER = "0" * 64

IMPLEMENTATION_PATHS = (
    "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r3_entry.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/s10r3-entry.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r3/__init__.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r3/conformance.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r3/contract.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r3/correctness.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r3/ledger.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r3/mapping.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r3/native_adapter.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r3/native_formocast_runtime_adapter.cpp",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r3/selector.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r3/state_machine.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10r3/support.py",
    "projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10r3_entry.py",
)

REGISTRY_PATH = (
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/"
    "s10r3-candidate-atom-registry.json"
)
SIZE_REGISTRY_PATH = (
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/"
    "s10r3-size-registry.json"
)
SENTINEL_FIXTURE_PATH = (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "prelabel-fixtures/s10r3-sentinel-fixture.json"
)
NATIVE_BINARY_PATH = (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "prelabel-build/native/build/s10r3-native"
)
NATIVE_BUILD_MANIFEST_PATH = (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "prelabel-build/native/s10r3-native-build.json"
)

FORMAL_OUTCOME_PATHS = (
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/"
    "s10r3-support-classification.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/"
    "s10r3-mapping-corpus.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/"
    "s10r3-smoke-correctness.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/"
    "s10r3-noise-pilot.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/"
    "s10r3-decision.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/"
    "gate-records/s10r3-s1-entry-go.json",
    "study_docs/research/ductile-origami-warmstart/reports/staged/"
    "s10r3-stage1-bounded-cover-entry-report.md",
)
FORMAL_SCOPES = (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/formal-cpu/",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/formal-mapping/",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/formal-native/",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/formal-gpu/",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/reproduction/",
)
PREDECESSOR_ACTIVE_PATHS = (FORMAL_OUTCOME_PATHS[0],)
PREDECESSOR_ACTIVE_SCOPES = FORMAL_SCOPES[:2]
SUCCESSOR_OUTCOME_PATHS = FORMAL_OUTCOME_PATHS[1:]
SUCCESSOR_FORMAL_SCOPES = FORMAL_SCOPES[2:]

SOURCE_IDENTITIES = {
    "ductile_commit": (
        "git_commit",
        "5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39",
    ),
    "geko_commit": ("git_commit", "d32abacfd13579d1f523f035b7a10b0734c4ac47"),
    "actual_yaml": (
        "git_blob_and_sha256",
        "1fd6fb401d5baebd4665a87e9002687fb725b2dc:"
        "faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36",
    ),
    "candidate_construction_blob": (
        "git_blob",
        "4968b29b5eacddc56b20c42cb4b2c1e3d8d6f406",
    ),
    "native_formocast_source_blob": (
        "git_blob",
        "cac2b324984a9fe2e1fadb018702486545e86e80",
    ),
    "native_formocast_header_blob": (
        "git_blob",
        "96741965d34f2da1b0a08eaecab15e72082a78bc",
    ),
    "runtime_queue_source_blob": (
        "git_blob",
        "33e86cfc4bf3d4ce8fa8da194b94c024bbb5639f",
    ),
    "runtime_queue_header_blob": (
        "git_blob",
        "bad091c0f299f30c4235bc8313c9e8f134fa66a5",
    ),
    "ordered_axes_and_candidate_order": (
        "sha256",
        "926a6d9502546dda22ea2edc483c0f61ef74b3e378bcf32f222f17130bb668a3",
    ),
    "expanded_groups": (
        "sha256",
        "0526a9b3c1d8a1bbe1db2cb03616bfda6e5a1f2dfad3826c0747d8dcb3ab9140",
    ),
    "search_space_map": (
        "sha256",
        "5785871bc0779fb67627943ef2ed5fde8e96647be7e0bb0db4f770473cd7a1a0",
    ),
    "baseline_weights": (
        "sha256",
        "56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f",
    ),
}

COMMAND_ENVIRONMENT = [
    {"name": "LC_ALL", "value": "C"},
    {"name": "LD_LIBRARY_PATH", "value": "/opt/rocm/lib:/opt/rocm/lib64"},
    {"name": "PATH", "value": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin"},
    {"name": "PYTHONHASHSEED", "value": "0"},
]

PRELABEL_ROOTS = (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "prelabel-build",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "prelabel-fixtures",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "prelabel-tests",
)
PRODUCTION_ADMISSION_LOCK_PATH = (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/gates/s10r3/"
    "execution-transition.lock"
)
PRODUCTION_ADMISSION_RESOLVED_PATH = (
    "/data1/perlee/rocm-libraries/agent_run/"
    "260730-ductile-factorized-guidance-s10r3-restart/gates/s10r3/"
    "execution-transition.lock"
)
PRODUCTION_STAGING_MANIFEST_PATH = (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.3-G1/predecessor-manifest.json"
)
PRODUCTION_STAGING_MANIFEST_TEMP_PATH = (
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.3-G1/"
    ".predecessor-manifest.a46-4.tmp"
)
PRODUCTION_LINEAGE_SEAL_PATH = (
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/lineage/"
    "s10r3-predecessor-lock-1cd089d3.json"
)
PRODUCTION_TRANSITION_PATHS = (
    PRODUCTION_ADMISSION_LOCK_PATH,
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/gates/s10r3/"
    "execution-transition-journal.json",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/gates/s10r3/"
    "execution-transition-journal.json.tmp",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/formal-cpu",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/formal-mapping",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/"
    "s10r3-support-classification.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/"
    "s10r3-stage1-bounded-cover-entry-lock.json",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.3-G1/formal-cpu",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.3-G1/formal-mapping",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.3-G1/"
    "s10r3-support-classification.json",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.3-G1/effective-lock.json",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.3-G1",
    PRODUCTION_STAGING_MANIFEST_PATH,
    PRODUCTION_STAGING_MANIFEST_TEMP_PATH,
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/"
    "lock-1cd089d3abe79d4918d965a2afa868421ec8d810644b8c7ede00f0ef05960301",
    PRODUCTION_LINEAGE_SEAL_PATH,
)
PRODUCTION_G2_LINEAGE_SEAL_PATH = (
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/lineage/"
    "s10r3-predecessor-lock-ddf438e5.json"
)
PRODUCTION_G2_TRANSITION_PATHS = (
    PRODUCTION_ADMISSION_LOCK_PATH,
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/gates/s10r3/"
    "execution-transition-g2-g3-journal.json",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/gates/s10r3/"
    "execution-transition-g2-g3-journal.json.tmp",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/formal-cpu",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/formal-mapping",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/"
    "s10r3-support-classification.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/"
    "s10r3-stage1-bounded-cover-entry-lock.json",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.5-G2",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.5-G2/formal-cpu",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.5-G2/formal-mapping",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.5-G2/"
    "s10r3-support-classification.json",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.5-G2/effective-lock.json",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/.staging-S10R3-A46.5-G2/predecessor-manifest.json",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/lock-ddf438e5c71fb4f1328511bff508d3cde347d8c6200c7f3bc72892c4acaaf8c3",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/lock-ddf438e5c71fb4f1328511bff508d3cde347d8c6200c7f3bc72892c4acaaf8c3/formal-cpu",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/lock-ddf438e5c71fb4f1328511bff508d3cde347d8c6200c7f3bc72892c4acaaf8c3/formal-mapping",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/lock-ddf438e5c71fb4f1328511bff508d3cde347d8c6200c7f3bc72892c4acaaf8c3/s10r3-support-classification.json",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/lock-ddf438e5c71fb4f1328511bff508d3cde347d8c6200c7f3bc72892c4acaaf8c3/effective-lock.json",
    "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/"
    "retired-predecessors/lock-ddf438e5c71fb4f1328511bff508d3cde347d8c6200c7f3bc72892c4acaaf8c3/"
    "predecessor-manifest.json",
    PRODUCTION_G2_LINEAGE_SEAL_PATH,
)
_PRODUCTION_TRANSITION_PATH_SET = frozenset(
    (*PRODUCTION_TRANSITION_PATHS, *PRODUCTION_G2_TRANSITION_PATHS)
)
G1_TRANSITION_ID = "S10R3-A46.3-G1-RETIREMENT"
G1_PREDECESSOR_GENERATION_ID = "S10R3-A46.2-G1"
G1_SUCCESSOR_GENERATION_ID = "S10R3-A46.3-G2"
G1_PHASE1_SEAL_COMMIT = "0e5b40ca8ebde31913e76a82e71ff3324d66a9fd"
G1_CONTRACT_RAW_SHA256 = (
    "96aa1e2399694094be7e04daab24a3fdd9564fddd5cc91fb5c500116a8044e1b"
)

TRANSITION_ID = "S10R3-A46.5-G2-RETIREMENT"
PREDECESSOR_GENERATION_ID = "S10R3-A46.3-G2"
SUCCESSOR_GENERATION_ID = "S10R3-A46.5-G3"
SUCCESSOR_LOCK_ID = "S10R3-A46-5-EFFECTIVE-LOCK-G3"
PREDECESSOR_COMPONENT_IDS = (
    "formal_cpu",
    "formal_mapping",
    "support_classification",
    "effective_lock",
)
PRODUCTION_SINGLE_FILE_LOGICAL_BASENAMES = {
    "support_classification": "s10r3-support-classification.json",
    "effective_lock": "s10r3-stage1-bounded-cover-entry-lock.json",
}
_MANIFEST_COMPONENT_CORE_FIELDS = (
    "component_id",
    "source_root",
    "final_root",
    "entry_count",
    "regular_file_count",
    "directory_count",
    "total_bytes",
    "inventory_sha256",
)
_FROZEN_COMPONENT_AUXILIARY_FIELDS = {
    "formal_cpu": (),
    "formal_mapping": (),
    "support_classification": ("raw_sha256", "document_digest"),
    "effective_lock": ("raw_sha256", "canonical_self_sha256"),
}
TRANSITION_STATES = (
    "PREPARED",
    "MOVING",
    "FINALIZED",
    "BLOCKED_TRANSITION",
)
SUCCESSOR_AUDIT_CHECKS = (
    "schema_and_unknown_field_rejection",
    "phase1_and_plan_b_survival",
    "exact_path_mode_hash_and_binary_binding",
    "source_yaml_registry_fixture_parity",
    "role_counter_and_whitelist_parity",
    "outcome_artifact_absence",
    "predecessor_capsule_and_seal_lineage",
    "successor_entry_preconditions",
    "canonical_self_hash",
)
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
_AT_FDCWD = -100
_RENAME_NOREPLACE = 1
MANIFEST_REPAIR_AUTHORITY = "A46.4"
_MANIFEST_REPAIR_LOCK_CONTEXT_KEY = object()
G2_LINEAGE_SELECTOR = "g2_predecessor_capsule_lineage"


@dataclass(frozen=True)
class G2ComponentSpec:
    """One immutable ordered G2 component identity."""

    component_id: str
    source_root: str
    staging_root: str
    final_root: str
    entry_count: int
    regular_file_count: int
    directory_count: int
    total_bytes: int
    inventory_sha256: str
    single_file_logical_basename: str | None


@dataclass(frozen=True)
class G2LineageSpec:
    """Immutable explicit selector result for the A46.5 G2 retirement."""

    selector: str
    transition_id: str
    predecessor_generation_id: str
    successor_generation_id: str
    successor_lock_id: str
    admission_lock: str
    admission_identity_digest: str
    journal: str
    journal_temp: str
    staging_capsule: str
    final_capsule: str
    manifest_path: str
    seal_path: str
    predecessor_lock_commit: str
    predecessor_lock_raw_sha256: str
    predecessor_lock_canonical_self_sha256: str
    components: tuple[G2ComponentSpec, ...]
    manifest_schema_bytes: bytes
    journal_schema_bytes: bytes
    seal_schema_bytes: bytes


def g2_lineage_spec(
    *,
    selector: str,
    contract: Mapping[str, Any] | None = None,
) -> G2LineageSpec:
    """Select the committed G2 lineage explicitly; there is no current default."""

    if selector != G2_LINEAGE_SELECTOR:
        raise ContractError("explicit A46.5 G2 lineage selector is required")
    authority = dict(contract) if contract is not None else load_contract()
    try:
        lineage = authority[selector]
        paths = lineage["paths"]
        frozen = lineage["ordered_components"]
        predecessor = lineage["manifest_json_schema"]["properties"]["predecessor"][
            "const"
        ]
    except (KeyError, TypeError) as error:
        raise ContractError("A46.5 G2 lineage specification is incomplete") from error
    expected_ids = list(PREDECESSOR_COMPONENT_IDS)
    if [item.get("component_id") for item in frozen] != expected_ids:
        raise ContractError("A46.5 G2 component order drift")
    components = tuple(
        G2ComponentSpec(
            component_id=item["component_id"],
            source_root=item["source_root"],
            staging_root=item["staging_root"],
            final_root=item["final_root"],
            entry_count=item["entry_count"],
            regular_file_count=item["regular_file_count"],
            directory_count=item["directory_count"],
            total_bytes=item["total_bytes"],
            inventory_sha256=item["inventory_sha256"],
            single_file_logical_basename=(
                Path(item["source_root"]).name
                if item["directory_count"] == 0
                else None
            ),
        )
        for item in frozen
    )
    result = G2LineageSpec(
        selector=selector,
        transition_id=lineage["transition_id"],
        predecessor_generation_id=lineage["predecessor_generation_id"],
        successor_generation_id=lineage["successor_generation_id"],
        successor_lock_id=lineage["successor_lock_id"],
        admission_lock=paths["admission_lock"],
        admission_identity_digest=lineage["admission_lock"]["identity_digest"],
        journal=paths["journal"],
        journal_temp=paths["journal_temp"],
        staging_capsule=paths["staging_capsule"],
        final_capsule=paths["final_capsule"],
        manifest_path=f'{paths["final_capsule"]}/{paths["capsule_manifest_name"]}',
        seal_path=paths["durable_lineage_seal"],
        predecessor_lock_commit=predecessor["effective_lock_commit"],
        predecessor_lock_raw_sha256=predecessor["effective_lock_raw_sha256"],
        predecessor_lock_canonical_self_sha256=predecessor[
            "effective_lock_canonical_self_sha256"
        ],
        components=components,
        manifest_schema_bytes=canonical_json_bytes(lineage["manifest_json_schema"]),
        journal_schema_bytes=canonical_json_bytes(lineage["journal_json_schema"]),
        seal_schema_bytes=canonical_json_bytes(lineage["seal_json_schema"]),
    )
    if (
        result.transition_id != TRANSITION_ID
        or result.predecessor_generation_id != PREDECESSOR_GENERATION_ID
        or result.successor_generation_id != SUCCESSOR_GENERATION_ID
        or result.successor_lock_id != SUCCESSOR_LOCK_ID
    ):
        raise ContractError("A46.5 G2 generation identity drift")
    return result


class ManifestRepairLockContext:
    """Opaque capability created only by the acquired-lock context manager."""

    __slots__ = ()

    def __new__(cls, key: object | None = None):
        if key is not _MANIFEST_REPAIR_LOCK_CONTEXT_KEY:
            raise ContractError(
                "manifest-repair lock context cannot be caller-constructed"
            )
        return super().__new__(cls)


_ACTIVE_MANIFEST_REPAIR_LOCK_CONTEXTS: dict[
    ManifestRepairLockContext, dict[str, Any]
] = {}


class _UniqueSafeLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueSafeLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if type(key) is not str:
            raise ContractError("YAML mapping keys must be strings")
        if key in result:
            raise ContractError(f"duplicate YAML mapping key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def _validate_json_value(value: Any, *, path: str = "$") -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ContractError(f"non-finite JSON number at {path}")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _validate_json_value(item, path=f"{path}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ContractError(f"non-string mapping key at {path}")
            _validate_json_value(item, path=f"{path}.{key}")
        return
    raise ContractError(f"unsupported exact JSON type at {path}: {type(value).__name__}")


def strict_load_yaml(path: Path | str) -> dict[str, Any]:
    try:
        value = yaml.load(Path(path).read_text(encoding="utf-8"), Loader=_UniqueSafeLoader)
    except (OSError, UnicodeError, yaml.YAMLError, ContractError) as error:
        raise ContractError(f"strict YAML load failed: {error}") from error
    if type(value) is not dict:
        raise ContractError("YAML document root must be an object")
    _validate_json_value(value)
    return value


def _duplicate_json_key(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON mapping key: {key}")
        result[key] = value
    return result


def strict_load_json(path: Path | str, *, object_root: bool = True) -> Any:
    try:
        value = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_duplicate_json_key,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ContractError(f"non-finite JSON token: {token}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ContractError) as error:
        raise ContractError(f"strict JSON load failed: {error}") from error
    if object_root and type(value) is not dict:
        raise ContractError("JSON document root must be an object")
    _validate_json_value(value)
    return value


def canonical_json_bytes(value: Any) -> bytes:
    _validate_json_value(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _authorized_transition_path(
    path: Path | str, *, allow_production: bool = False
) -> tuple[Path, str]:
    """Authorize exactly one production path or a resolved synthetic path."""

    candidate = Path(path)
    if candidate.is_absolute():
        absolute = candidate
        try:
            lexical = candidate.relative_to(REPOSITORY_ROOT).as_posix()
        except ValueError:
            lexical = None
    else:
        absolute = REPOSITORY_ROOT / candidate
        lexical = candidate.as_posix()

    if allow_production:
        if lexical is None or lexical not in _PRODUCTION_TRANSITION_PATH_SET:
            raise ContractError(
                "path is not in the exact production transition allowlist"
            )
        return absolute, lexical
    if lexical is not None and lexical in _PRODUCTION_TRANSITION_PATH_SET:
        raise ContractError("production transition path is Main-only")

    absolute = absolute.resolve(strict=False)
    if not any(
        _path_within(absolute, (REPOSITORY_ROOT / root).resolve(strict=False))
        for root in PRELABEL_ROOTS
    ):
        raise ContractError("synthetic transition path is outside prelabel roots")
    try:
        lexical = absolute.relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError as error:
        raise ContractError("transition path escapes repository root") from error
    return absolute, lexical


def _identity_digest(identity: Mapping[str, Any]) -> str:
    projection = dict(identity)
    projection.pop("identity_digest", None)
    return canonical_sha256(projection)


def admission_lock_identity(
    path: Path | str,
    descriptor: int,
    *,
    allow_production: bool = False,
    expected_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Recompute stable-inode identity from an open FD and no-follow lstat."""

    absolute, lexical = _authorized_transition_path(
        path, allow_production=allow_production
    )
    try:
        opened = os.fstat(descriptor)
        linked = absolute.lstat()
    except OSError as error:
        raise ContractError(f"admission lock identity read failed: {error}") from error
    parity = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
    )
    if any(getattr(opened, field) != getattr(linked, field) for field in parity):
        raise ContractError("admission lock FD/path inode identity mismatch")
    if not stat.S_ISREG(opened.st_mode) or stat.S_ISLNK(linked.st_mode):
        raise ContractError("admission lock is not a no-follow regular file")
    if stat.S_IMODE(opened.st_mode) != 0o600:
        raise ContractError("admission lock mode is not 0600")
    if opened.st_nlink != 1:
        raise ContractError("admission lock link count is not one")
    if opened.st_size != 0 or os.pread(descriptor, 1, 0) != b"":
        raise ContractError("admission lock is not empty")
    if allow_production:
        if lexical != PRODUCTION_ADMISSION_LOCK_PATH:
            raise ContractError("production admission identity path mismatch")
        resolved_path = PRODUCTION_ADMISSION_RESOLVED_PATH
    else:
        resolved_path = absolute.as_posix()
    identity: dict[str, Any] = {
        "lexical_path": lexical,
        "resolved_path": resolved_path,
        "st_dev": opened.st_dev,
        "st_ino": opened.st_ino,
        "entry_type": "regular_file",
        "mode": "0600",
        "nlink": opened.st_nlink,
        "size_bytes": opened.st_size,
        "raw_sha256": EMPTY_SHA256,
    }
    identity["identity_digest"] = _identity_digest(identity)
    if expected_identity is not None and identity != dict(expected_identity):
        raise ContractError("stable admission lock identity changed")
    return identity


def create_stable_admission_lock(
    path: Path | str, *, allow_production: bool = False
) -> dict[str, Any]:
    """Exclusive-create the permanent empty admission inode exactly once."""

    absolute, _ = _authorized_transition_path(path, allow_production=allow_production)
    absolute.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags, 0o600)
    except OSError as error:
        raise ContractError(f"exclusive admission lock creation failed: {error}") from error
    try:
        os.fchmod(descriptor, 0o600)
        os.fsync(descriptor)
        identity = admission_lock_identity(
            absolute, descriptor, allow_production=allow_production
        )
    finally:
        os.close(descriptor)
    directory_fd = os.open(absolute.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return identity


@contextmanager
def stable_admission_lock(
    path: Path | str,
    *,
    exclusive: bool = False,
    allow_production: bool = False,
    expected_identity: Mapping[str, Any] | None = None,
):
    """Lock and continuously bind one stable admission inode."""

    absolute, _ = _authorized_transition_path(path, allow_production=allow_production)
    flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise ContractError(f"admission lock open failed: {error}") from error
    operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    try:
        try:
            fcntl.flock(descriptor, operation | fcntl.LOCK_NB)
        except OSError as error:
            raise ContractError(f"admission lock acquisition failed: {error}") from error
        identity = admission_lock_identity(
            absolute,
            descriptor,
            allow_production=allow_production,
            expected_identity=expected_identity,
        )
        yield descriptor, identity
        admission_lock_identity(
            absolute,
            descriptor,
            allow_production=allow_production,
            expected_identity=identity,
        )
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _renameat2_noreplace(source: Path, destination: Path) -> None:
    """Invoke Linux renameat2 directly; an ordinary rename is never a fallback."""

    libc = ctypes.CDLL(None, use_errno=True)
    primitive = getattr(libc, "renameat2", None)
    if primitive is None:
        raise ContractError("renameat2 RENAME_NOREPLACE is unavailable")
    primitive.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    primitive.restype = ctypes.c_int
    result = primitive(
        _AT_FDCWD,
        os.fsencode(source),
        _AT_FDCWD,
        os.fsencode(destination),
        _RENAME_NOREPLACE,
    )
    if result != 0:
        error_number = ctypes.get_errno()
        if error_number in (errno.ENOSYS, errno.EINVAL):
            raise ContractError("renameat2 RENAME_NOREPLACE is unavailable")
        raise ContractError(
            f"renameat2 RENAME_NOREPLACE failed: {os.strerror(error_number)}"
        )


def rename_noreplace(
    source: Path | str,
    destination: Path | str,
    *,
    allow_production: bool = False,
) -> None:
    """Move one synthetic transition item with true same-device no-replace."""

    source_path, _ = _authorized_transition_path(
        source, allow_production=allow_production
    )
    destination_path, _ = _authorized_transition_path(
        destination, allow_production=allow_production
    )
    try:
        source_info = source_path.lstat()
        source_parent = source_path.parent.stat()
        destination_parent = destination_path.parent.stat()
    except OSError as error:
        raise ContractError(f"rename precondition read failed: {error}") from error
    if stat.S_ISLNK(source_info.st_mode) or not (
        stat.S_ISREG(source_info.st_mode) or stat.S_ISDIR(source_info.st_mode)
    ):
        raise ContractError("rename source must be a regular file or directory")
    if stat.S_ISREG(source_info.st_mode) and source_info.st_nlink != 1:
        raise ContractError("rename source regular file link count is not one")
    if source_parent.st_dev != destination_parent.st_dev:
        raise ContractError("rename source and destination are on different devices")
    if os.path.lexists(destination_path):
        raise ContractError("rename destination already exists")
    _renameat2_noreplace(source_path, destination_path)
    if source_path.exists() or not destination_path.exists():
        raise ContractError("renameat2 postcondition failed")


def component_inventory(
    root: Path | str,
    component_id: str,
    *,
    single_file_logical_basename: str | None = None,
) -> dict[str, Any]:
    """Compute the frozen root-excluded UTF-8-byte-sorted component inventory."""

    component_root = Path(root)
    try:
        root_info = component_root.lstat()
    except OSError as error:
        raise ContractError(f"component inventory root read failed: {error}") from error
    if stat.S_ISLNK(root_info.st_mode):
        raise ContractError("component inventory root may not be a symlink")
    if single_file_logical_basename is not None:
        if (
            type(single_file_logical_basename) is not str
            or not single_file_logical_basename
            or single_file_logical_basename in (".", "..")
            or "/" in single_file_logical_basename
            or "\\" in single_file_logical_basename
            or "\x00" in single_file_logical_basename
        ):
            raise ContractError("single-file logical basename is unsafe")
        if not stat.S_ISREG(root_info.st_mode):
            raise ContractError(
                "single-file logical basename requires a regular-file component"
            )
        frozen_basename = PRODUCTION_SINGLE_FILE_LOGICAL_BASENAMES.get(
            component_id
        )
        if (
            frozen_basename is not None
            and single_file_logical_basename != frozen_basename
        ):
            raise ContractError(
                "single-file logical basename does not match frozen component"
            )
    records: list[dict[str, Any]] = []

    def add(path: Path, logical_path: str) -> None:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise ContractError(f"inventory symlink forbidden: {logical_path}")
        if stat.S_ISDIR(info.st_mode):
            records.append(
                {
                    "logical_path": logical_path.rstrip("/") + "/",
                    "entry_type": "directory",
                    "mode": f"{stat.S_IMODE(info.st_mode):04o}",
                    "size_bytes": 0,
                    "sha256": None,
                }
            )
            with os.scandir(path) as entries:
                children = sorted(entries, key=lambda item: os.fsencode(item.name))
            for child in children:
                child_logical = f"{logical_path.rstrip('/')}/{child.name}"
                add(Path(child.path), child_logical)
            return
        if not stat.S_ISREG(info.st_mode):
            raise ContractError(f"inventory nonregular entry forbidden: {logical_path}")
        if info.st_nlink != 1:
            raise ContractError(f"inventory hard link forbidden: {logical_path}")
        records.append(
            {
                "logical_path": logical_path,
                "entry_type": "regular_file",
                "mode": f"{stat.S_IMODE(info.st_mode):04o}",
                "size_bytes": info.st_size,
                "sha256": sha256_file(path),
            }
        )

    if stat.S_ISDIR(root_info.st_mode):
        with os.scandir(component_root) as entries:
            children = sorted(entries, key=lambda item: os.fsencode(item.name))
        for child in children:
            add(Path(child.path), child.name)
    elif stat.S_ISREG(root_info.st_mode):
        if root_info.st_nlink != 1:
            raise ContractError("component inventory root hard link forbidden")
        add(
            component_root,
            single_file_logical_basename or component_root.name,
        )
    else:
        raise ContractError("component inventory root is nonregular")
    records.sort(key=lambda item: item["logical_path"].encode("utf-8"))
    regular_files = [item for item in records if item["entry_type"] == "regular_file"]
    directories = [item for item in records if item["entry_type"] == "directory"]
    return {
        "component_id": component_id,
        "entries": records,
        "entry_count": len(records),
        "regular_file_count": len(regular_files),
        "directory_count": len(directories),
        "total_bytes": sum(item["size_bytes"] for item in regular_files),
        "inventory_sha256": canonical_sha256(records),
    }


def validate_component_inventory(
    inventory: Mapping[str, Any], expected: Mapping[str, Any]
) -> None:
    fields = (
        "component_id",
        "entry_count",
        "regular_file_count",
        "directory_count",
        "total_bytes",
        "inventory_sha256",
    )
    if any(inventory.get(field) != expected.get(field) for field in fields):
        raise ContractError("component inventory does not match frozen identity")
    if canonical_sha256(inventory.get("entries")) != inventory.get("inventory_sha256"):
        raise ContractError("component inventory digest mismatch")


def _self_digest(document: Mapping[str, Any], field: str) -> str:
    projection = copy.deepcopy(dict(document))
    projection[field] = SELF_HASH_PLACEHOLDER
    return canonical_sha256(projection)


def _event_digest(event: Mapping[str, Any]) -> str:
    return _self_digest(event, "event_digest")


def new_transition_journal(identity: Mapping[str, Any]) -> dict[str, Any]:
    event = {
        "event_index": 0,
        "previous_event_digest": None,
        "action": "prepared",
        "state": "PREPARED",
        "component_id": None,
        "admission_lock_identity_digest": identity["identity_digest"],
        "event_digest": SELF_HASH_PLACEHOLDER,
    }
    event["event_digest"] = _event_digest(event)
    document: dict[str, Any] = {
        "schema_version": 1,
        "document_kind": "s10r3_predecessor_transition_journal",
        "transition_id": G1_TRANSITION_ID,
        "admission_lock_identity": dict(identity),
        "state": "PREPARED",
        "relocated_components": [],
        "events": [event],
        "document_digest": SELF_HASH_PLACEHOLDER,
    }
    document["document_digest"] = _self_digest(document, "document_digest")
    validate_transition_journal(document, production_identity=False)
    return document


def append_transition_event(
    journal: Mapping[str, Any],
    *,
    action: str,
    component_id: str | None = None,
) -> dict[str, Any]:
    document = copy.deepcopy(dict(journal))
    validate_transition_journal(document, production_identity=False)
    if document["state"] in ("FINALIZED", "BLOCKED_TRANSITION"):
        raise ContractError("terminal transition journal cannot be extended")
    relocated = list(document["relocated_components"])
    if action == "component_relocated":
        if len(relocated) >= len(PREDECESSOR_COMPONENT_IDS):
            raise ContractError("all predecessor components are already relocated")
        expected = PREDECESSOR_COMPONENT_IDS[len(relocated)]
        if component_id != expected:
            raise ContractError("predecessor component relocation order mismatch")
        relocated.append(component_id)
        state = "MOVING"
    elif action == "staging_verified":
        if tuple(relocated) != PREDECESSOR_COMPONENT_IDS or component_id is not None:
            raise ContractError("staging verification requires four ordered components")
        if document["events"][-1]["action"] == "staging_verified":
            raise ContractError("staging verification may occur only once")
        state = "MOVING"
    elif action == "finalized":
        if (
            tuple(relocated) != PREDECESSOR_COMPONENT_IDS
            or document["events"][-1]["action"] != "staging_verified"
            or component_id is not None
        ):
            raise ContractError("finalization requires the staging_verified event")
        state = "FINALIZED"
    elif action == "blocked":
        if component_id is not None:
            raise ContractError("blocked event component_id must be null")
        state = "BLOCKED_TRANSITION"
    else:
        raise ContractError("unknown transition journal action")
    previous = document["events"][-1]["event_digest"]
    event = {
        "event_index": len(document["events"]),
        "previous_event_digest": previous,
        "action": action,
        "state": state,
        "component_id": component_id,
        "admission_lock_identity_digest": document["admission_lock_identity"][
            "identity_digest"
        ],
        "event_digest": SELF_HASH_PLACEHOLDER,
    }
    event["event_digest"] = _event_digest(event)
    document["events"].append(event)
    document["relocated_components"] = relocated
    document["state"] = state
    document["document_digest"] = SELF_HASH_PLACEHOLDER
    document["document_digest"] = _self_digest(document, "document_digest")
    validate_transition_journal(document, production_identity=False)
    return document


def validate_transition_journal(
    journal: Mapping[str, Any], *, production_identity: bool = True
) -> None:
    document = dict(journal)
    required = {
        "schema_version",
        "document_kind",
        "transition_id",
        "admission_lock_identity",
        "state",
        "relocated_components",
        "events",
        "document_digest",
    }
    if set(document) != required:
        raise ContractError("transition journal unknown or missing field")
    if (
        document["schema_version"] != 1
        or document["document_kind"] != "s10r3_predecessor_transition_journal"
        or document["transition_id"] != G1_TRANSITION_ID
        or document["state"] not in TRANSITION_STATES
    ):
        raise ContractError("transition journal envelope mismatch")
    events = document["events"]
    if type(events) is not list or not events:
        raise ContractError("transition journal event array is empty")
    identity = document["admission_lock_identity"]
    if type(identity) is not dict or identity.get("identity_digest") != _identity_digest(identity):
        raise ContractError("transition journal admission identity digest mismatch")
    if production_identity:
        schema = load_contract()["predecessor_capsule_lineage"]["journal_json_schema"]
        try:
            jsonschema.Draft7Validator(schema).validate(document)
        except jsonschema.ValidationError as error:
            raise ContractError(f"transition journal schema failed: {error.message}") from error
    relocated: list[str] = []
    staging_verified = False
    blocked = False
    previous: str | None = None
    for index, raw_event in enumerate(events):
        if type(raw_event) is not dict or set(raw_event) != {
            "event_index",
            "previous_event_digest",
            "action",
            "state",
            "component_id",
            "admission_lock_identity_digest",
            "event_digest",
        }:
            raise ContractError("transition journal event shape mismatch")
        event = raw_event
        if event["event_index"] != index or event["previous_event_digest"] != previous:
            raise ContractError("transition journal event chain mismatch")
        if event["event_digest"] != _event_digest(event):
            raise ContractError("transition journal event digest mismatch")
        if event["admission_lock_identity_digest"] != identity["identity_digest"]:
            raise ContractError("transition journal admission identity changed")
        action = event["action"]
        if index == 0:
            if action != "prepared" or event["state"] != "PREPARED" or event["component_id"] is not None:
                raise ContractError("transition journal must begin with prepared")
        elif blocked:
            raise ContractError("blocked transition journal has trailing events")
        elif action == "component_relocated":
            if staging_verified or len(relocated) >= len(PREDECESSOR_COMPONENT_IDS):
                raise ContractError("illegal component relocation event")
            expected = PREDECESSOR_COMPONENT_IDS[len(relocated)]
            if event["component_id"] != expected or event["state"] != "MOVING":
                raise ContractError("component relocation order/state mismatch")
            relocated.append(expected)
        elif action == "staging_verified":
            if (
                staging_verified
                or tuple(relocated) != PREDECESSOR_COMPONENT_IDS
                or event["component_id"] is not None
                or event["state"] != "MOVING"
            ):
                raise ContractError("staging_verified action/state mismatch")
            staging_verified = True
        elif action == "finalized":
            if (
                not staging_verified
                or index != len(events) - 1
                or event["component_id"] is not None
                or event["state"] != "FINALIZED"
            ):
                raise ContractError("fake or misplaced finalization")
        elif action == "blocked":
            if event["component_id"] is not None or event["state"] != "BLOCKED_TRANSITION":
                raise ContractError("blocked action/state mismatch")
            blocked = True
        else:
            raise ContractError("unknown transition journal event action")
        previous = event["event_digest"]
    if document["relocated_components"] != relocated:
        raise ContractError("transition journal relocated component projection mismatch")
    if document["state"] != events[-1]["state"]:
        raise ContractError("transition journal terminal state mismatch")
    if document["state"] == "FINALIZED" and (
        len(events) != 7 or events[-1]["action"] != "finalized"
    ):
        raise ContractError("finalized journal is not the exact seven-event chain")
    if document["state"] == "PREPARED" and len(events) != 1:
        raise ContractError("prepared journal has extra events")
    if document["document_digest"] != _self_digest(document, "document_digest"):
        raise ContractError("transition journal document digest mismatch")


def write_transition_journal(
    path: Path | str,
    journal: Mapping[str, Any],
    *,
    allow_production: bool = False,
) -> None:
    """Durably replace only a journal, through its fixed adjacent .tmp path."""

    validate_transition_journal(journal, production_identity=allow_production)
    target, _ = _authorized_transition_path(path, allow_production=allow_production)
    temporary = Path(f"{target}.tmp")
    _authorized_transition_path(temporary, allow_production=allow_production)
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(temporary, flags, 0o600)
    except OSError as error:
        raise ContractError(f"fixed journal temporary creation failed: {error}") from error
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json_bytes(dict(journal)) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def transition_recovery_action(
    journal: Mapping[str, Any], locations: Mapping[str, str]
) -> dict[str, Any]:
    """Derive the sole forward action from a legal journal/filesystem boundary."""

    validate_transition_journal(journal, production_identity=False)
    if set(locations) != set(PREDECESSOR_COMPONENT_IDS) or any(
        location not in ("source", "staging", "final")
        for location in locations.values()
    ):
        raise ContractError("recovery location projection is incomplete")
    if journal["state"] == "BLOCKED_TRANSITION":
        return {"action": "blocked", "component_id": None}
    relocated_count = len(journal["relocated_components"])
    actual = [locations[item] for item in PREDECESSOR_COMPONENT_IDS]
    expected_staging = ["staging"] * relocated_count + ["source"] * (
        len(PREDECESSOR_COMPONENT_IDS) - relocated_count
    )
    one_ahead = (
        ["staging"] * (relocated_count + 1)
        + ["source"] * (len(PREDECESSOR_COMPONENT_IDS) - relocated_count - 1)
        if relocated_count < len(PREDECESSOR_COMPONENT_IDS)
        else None
    )
    last_action = journal["events"][-1]["action"]
    if actual == ["final"] * len(PREDECESSOR_COMPONENT_IDS):
        if last_action == "staging_verified":
            return {"action": "record_finalized", "component_id": None}
        if journal["state"] == "FINALIZED":
            return {"action": "complete", "component_id": None}
        raise ContractError("final capsule exists before staging verification")
    if "final" in actual:
        raise ContractError("partial final capsule state is ambiguous")
    if actual == one_ahead:
        return {
            "action": "record_component_relocated",
            "component_id": PREDECESSOR_COMPONENT_IDS[relocated_count],
        }
    if actual != expected_staging:
        raise ContractError("filesystem state is not a legal forward prefix")
    if relocated_count < len(PREDECESSOR_COMPONENT_IDS):
        return {
            "action": "relocate_component",
            "component_id": PREDECESSOR_COMPONENT_IDS[relocated_count],
        }
    if last_action == "component_relocated":
        return {"action": "verify_staging", "component_id": None}
    if last_action == "staging_verified":
        return {"action": "finalize_staging", "component_id": None}
    raise ContractError("journal/filesystem recovery state is inconsistent")


def _json_file_sha256(document: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(dict(document)) + b"\n").hexdigest()


def validate_capsule_manifest(
    manifest: Mapping[str, Any],
    *,
    require_frozen: bool = True,
    component_roots: Mapping[str, Path | str] | None = None,
) -> None:
    """Validate manifest schema, self digest, mappings, and fresh inventories."""

    document = dict(manifest)
    if require_frozen:
        schema = load_contract()["predecessor_capsule_lineage"][
            "manifest_json_schema"
        ]
        try:
            jsonschema.Draft7Validator(schema).validate(document)
        except jsonschema.ValidationError as error:
            raise ContractError(f"capsule manifest schema failed: {error.message}") from error
    elif set(document) != {
        "schema_version",
        "document_kind",
        "transition_id",
        "inventory_algorithm",
        "component_inventory",
        "predecessor",
        "entries",
        "summary",
        "later_evidence_absence",
        "diagnostic_only",
        "admissible_for_successor",
        "document_digest",
    }:
        raise ContractError("capsule manifest unknown or missing field")
    if document.get("document_digest") != _self_digest(document, "document_digest"):
        raise ContractError("capsule manifest document digest mismatch")
    if document.get("diagnostic_only") is not True or document.get(
        "admissible_for_successor"
    ) is not False:
        raise ContractError("predecessor capsule may never be admitted to G2")
    component_specs = document.get("component_inventory")
    entries = document.get("entries")
    if type(component_specs) is not list or type(entries) is not list:
        raise ContractError("capsule manifest inventory shape mismatch")
    component_ids = [item.get("component_id") for item in component_specs]
    if len(component_ids) != len(set(component_ids)):
        raise ContractError("capsule manifest component IDs are duplicated")
    source_paths = [item.get("source_path") for item in entries]
    if (
        not all(type(path) is str for path in source_paths)
        or len(source_paths) != len(set(source_paths))
        or source_paths != sorted(source_paths, key=lambda path: path.encode("utf-8"))
    ):
        raise ContractError("capsule manifest entry order/path uniqueness mismatch")
    by_component: dict[str, list[dict[str, Any]]] = {
        component_id: [] for component_id in component_ids
    }
    for entry in entries:
        if type(entry) is not dict or entry.get("component_id") not in by_component:
            raise ContractError("capsule manifest entry component mismatch")
        component = next(
            item
            for item in component_specs
            if item["component_id"] == entry["component_id"]
        )
        logical = entry.get("logical_path")
        if type(logical) is not str or not logical or logical.startswith("/"):
            raise ContractError("capsule manifest logical path is invalid")
        logical_path = Path(logical.rstrip("/"))
        if ".." in logical_path.parts:
            raise ContractError("capsule manifest logical path escapes component")
        source_root = component["source_root"]
        final_root = component["final_root"]
        single_file = component["directory_count"] == 0
        expected_source = source_root if single_file else f"{source_root}/{logical}"
        expected_final = final_root if single_file else f"{final_root}/{logical}"
        if entry.get("source_path") != expected_source or entry.get(
            "final_path"
        ) != expected_final:
            raise ContractError("capsule manifest source/final path mapping mismatch")
        by_component[entry["component_id"]].append(
            {
                field: entry[field]
                for field in (
                    "logical_path",
                    "entry_type",
                    "mode",
                    "size_bytes",
                    "sha256",
                )
            }
        )
    for component in component_specs:
        records = by_component[component["component_id"]]
        files = [item for item in records if item["entry_type"] == "regular_file"]
        directories = [item for item in records if item["entry_type"] == "directory"]
        observed = {
            "component_id": component["component_id"],
            "entries": records,
            "entry_count": len(records),
            "regular_file_count": len(files),
            "directory_count": len(directories),
            "total_bytes": sum(item["size_bytes"] for item in files),
            "inventory_sha256": canonical_sha256(records),
        }
        validate_component_inventory(observed, component)
        if component_roots is not None:
            if component["component_id"] not in component_roots:
                raise ContractError("fresh capsule inventory root is missing")
            single_file_logical_basename = None
            if component["directory_count"] == 0:
                single_file_logical_basename = Path(
                    component["source_root"]
                ).name
            fresh = component_inventory(
                component_roots[component["component_id"]],
                component["component_id"],
                single_file_logical_basename=single_file_logical_basename,
            )
            validate_component_inventory(fresh, component)
            if fresh["entries"] != records:
                raise ContractError("manifest entries differ from fresh inventory")
    summary = document.get("summary")
    if type(summary) is not dict:
        raise ContractError("capsule manifest summary is invalid")
    expected_summary = {
        "regular_file_count": sum(item["regular_file_count"] for item in component_specs),
        "directory_count": sum(item["directory_count"] for item in component_specs),
        "total_bytes": sum(item["total_bytes"] for item in component_specs),
        "component_counts": {
            item["component_id"]: item["entry_count"] for item in component_specs
        },
        "symlink_count": 0,
        "hardlink_count": 0,
    }
    if summary != expected_summary:
        raise ContractError("capsule manifest aggregate summary mismatch")


def build_capsule_manifest(
    inventories: Sequence[Mapping[str, Any]],
    component_paths: Mapping[str, tuple[str, str]],
    *,
    predecessor: Mapping[str, Any],
    inventory_algorithm: Mapping[str, Any],
    later_evidence_absence: Mapping[str, Any],
    frozen_components: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a manifest from already recomputed inventories without filesystem I/O."""

    authoritative_frozen: list[dict[str, Any]] | None = None
    if frozen_components is not None:
        schema_components = load_contract()["predecessor_capsule_lineage"][
            "manifest_json_schema"
        ]["properties"]["component_inventory"]["const"]
        if (
            type(frozen_components) is not list
            or any(type(item) is not dict for item in frozen_components)
            or frozen_components != schema_components
        ):
            raise ContractError(
                "frozen capsule components must equal the contract schema const"
            )
        authoritative_frozen = copy.deepcopy(schema_components)
        frozen_ids = [item.get("component_id") for item in authoritative_frozen]
        if frozen_ids != list(PREDECESSOR_COMPONENT_IDS):
            raise ContractError("frozen capsule component order/identity drift")
        for item in authoritative_frozen:
            auxiliary = _FROZEN_COMPONENT_AUXILIARY_FIELDS[item["component_id"]]
            if set(item) != set(_MANIFEST_COMPONENT_CORE_FIELDS) | set(auxiliary):
                raise ContractError("frozen capsule component field drift")
        inventory_fields = {
            "component_id",
            "entries",
            "entry_count",
            "regular_file_count",
            "directory_count",
            "total_bytes",
            "inventory_sha256",
        }
        if any(
            type(inventory) is not dict or set(inventory) != inventory_fields
            for inventory in inventories
        ):
            raise ContractError("frozen capsule inventory has unknown or missing field")
        if type(component_paths) is not dict or set(component_paths) != set(
            PREDECESSOR_COMPONENT_IDS
        ):
            raise ContractError("frozen capsule component path set mismatch")

    specs: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    for inventory in inventories:
        component_id = inventory["component_id"]
        if component_id not in component_paths:
            raise ContractError("capsule component path mapping is missing")
        source_root, final_root = component_paths[component_id]
        spec = {
            "component_id": component_id,
            "source_root": source_root,
            "final_root": final_root,
            **{
                field: inventory[field]
                for field in (
                    "entry_count",
                    "regular_file_count",
                    "directory_count",
                    "total_bytes",
                    "inventory_sha256",
                )
            },
        }
        specs.append(spec)
        for record in inventory["entries"]:
            logical = record["logical_path"]
            single_file = inventory["directory_count"] == 0
            entries.append(
                {
                    "component_id": component_id,
                    "logical_path": logical,
                    "source_path": source_root if single_file else f"{source_root}/{logical}",
                    "final_path": final_root if single_file else f"{final_root}/{logical}",
                    **{
                        field: record[field]
                        for field in ("entry_type", "mode", "size_bytes", "sha256")
                    },
                }
            )
    if authoritative_frozen is not None:
        computed_core = [
            {field: item[field] for field in _MANIFEST_COMPONENT_CORE_FIELDS}
            for item in specs
        ]
        frozen_core = [
            {field: item[field] for field in _MANIFEST_COMPONENT_CORE_FIELDS}
            for item in authoritative_frozen
        ]
        if computed_core != frozen_core:
            raise ContractError("computed capsule component core/order drift")
        for spec, frozen in zip(specs, authoritative_frozen):
            for field in _FROZEN_COMPONENT_AUXILIARY_FIELDS[spec["component_id"]]:
                spec[field] = frozen[field]
    entries.sort(key=lambda item: item["source_path"].encode("utf-8"))
    document: dict[str, Any] = {
        "schema_version": 1,
        "document_kind": "s10r3_predecessor_capsule_manifest",
        "transition_id": G1_TRANSITION_ID,
        "inventory_algorithm": dict(inventory_algorithm),
        "component_inventory": specs,
        "predecessor": dict(predecessor),
        "entries": entries,
        "summary": {
            "regular_file_count": sum(item["regular_file_count"] for item in specs),
            "directory_count": sum(item["directory_count"] for item in specs),
            "total_bytes": sum(item["total_bytes"] for item in specs),
            "component_counts": {
                item["component_id"]: item["entry_count"] for item in specs
            },
            "symlink_count": 0,
            "hardlink_count": 0,
        },
        "later_evidence_absence": dict(later_evidence_absence),
        "diagnostic_only": True,
        "admissible_for_successor": False,
        "document_digest": SELF_HASH_PLACEHOLDER,
    }
    document["document_digest"] = _self_digest(document, "document_digest")
    validate_capsule_manifest(
        document, require_frozen=authoritative_frozen is not None
    )
    return document


def _strict_json_bytes(raw: bytes) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_json_key,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ContractError(f"non-finite JSON constant: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f"strict JSON decode failed: {error}") from error
    _validate_json_value(value)
    if type(value) is not dict:
        raise ContractError("strict JSON root must be an object")
    return value


def _utc_timestamp_from_ns(value: int) -> str:
    seconds, nanoseconds = divmod(value, 1_000_000_000)
    prefix = datetime.fromtimestamp(seconds, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    return f"{prefix}.{nanoseconds:09d}Z"


def _manifest_snapshot(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ContractError(f"manifest no-follow open failed: {error}") from error
    try:
        opened_before = os.fstat(descriptor)
        linked_before = path.lstat()
        if (
            opened_before.st_dev != linked_before.st_dev
            or opened_before.st_ino != linked_before.st_ino
            or opened_before.st_mode != linked_before.st_mode
            or opened_before.st_nlink != linked_before.st_nlink
            or opened_before.st_size != linked_before.st_size
            or not stat.S_ISREG(opened_before.st_mode)
            or stat.S_ISLNK(linked_before.st_mode)
        ):
            raise ContractError("manifest FD/path identity mismatch")
        chunks: list[bytes] = []
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            chunks.append(block)
        raw = b"".join(chunks)
        opened_after = os.fstat(descriptor)
        linked_after = path.lstat()
        if (
            opened_before.st_dev,
            opened_before.st_ino,
            opened_before.st_mode,
            opened_before.st_nlink,
            opened_before.st_size,
            opened_before.st_mtime_ns,
            opened_before.st_ctime_ns,
        ) != (
            opened_after.st_dev,
            opened_after.st_ino,
            opened_after.st_mode,
            opened_after.st_nlink,
            opened_after.st_size,
            opened_after.st_mtime_ns,
            opened_after.st_ctime_ns,
        ) or (
            opened_after.st_dev,
            opened_after.st_ino,
            opened_after.st_mode,
            opened_after.st_nlink,
            opened_after.st_size,
        ) != (
            linked_after.st_dev,
            linked_after.st_ino,
            linked_after.st_mode,
            linked_after.st_nlink,
            linked_after.st_size,
        ):
            raise ContractError("manifest changed while being read")
    finally:
        os.close(descriptor)
    document = _strict_json_bytes(raw)
    identity = {
        "entry_type": "regular_file",
        "mode": f"0{stat.S_IMODE(opened_after.st_mode):03o}",
        "nlink": opened_after.st_nlink,
        "st_dev": opened_after.st_dev,
        "st_ino": opened_after.st_ino,
        "size_bytes": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "document_digest": document.get("document_digest"),
        "mtime_utc": _utc_timestamp_from_ns(opened_after.st_mtime_ns),
        "ctime_utc": _utc_timestamp_from_ns(opened_after.st_ctime_ns),
    }
    return identity, document


def _corrected_manifest_content_identity(
    document: Mapping[str, Any], contract: Mapping[str, Any]
) -> None:
    expected = contract["predecessor_capsule_lineage"][
        "one_time_manifest_repair"
    ]["corrected_manifest_identity"]
    raw = canonical_json_bytes(dict(document)) + b"\n"
    if (
        len(raw) != expected["size_bytes"]
        or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
        or document.get("document_digest") != expected["document_digest"]
    ):
        raise ContractError("mechanical corrected manifest identity mismatch")


def _validate_known_old_manifest_schema_error(
    errors: Sequence[jsonschema.ValidationError],
    *,
    actual: Sequence[Mapping[str, Any]],
    frozen: Sequence[Mapping[str, Any]],
) -> None:
    if len(errors) != 1:
        raise ContractError("old manifest must have exactly one frozen-schema error")
    error = errors[0]
    if (
        error.validator != "const"
        or list(error.absolute_path) != ["component_inventory"]
        or list(error.absolute_schema_path)
        != ["properties", "component_inventory", "const"]
        or error.validator_value != list(frozen)
        or error.instance != list(actual)
    ):
        raise ContractError("old manifest frozen failure is not the exact known const mismatch")


def _mechanically_corrected_manifest(
    old_document: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, Any]:
    lineage = contract["predecessor_capsule_lineage"]
    schema = lineage["manifest_json_schema"]
    frozen = lineage["frozen_predecessor_inventory"]["components"]
    try:
        schema_const = schema["properties"]["component_inventory"]["const"]
    except (KeyError, TypeError) as error:
        raise ContractError("frozen component_inventory const is absent") from error
    if type(schema_const) is not list or schema_const != frozen:
        raise ContractError("frozen component_inventory const authority drift")
    corrected = copy.deepcopy(dict(old_document))
    corrected["component_inventory"] = copy.deepcopy(schema_const)
    corrected["document_digest"] = _self_digest(corrected, "document_digest")
    corrected_errors = list(
        jsonschema.Draft7Validator(schema).iter_errors(corrected)
    )
    if corrected_errors:
        raise ContractError(
            f"mechanical corrected manifest frozen validation failed: "
            f"{corrected_errors[0].message}"
        )
    _corrected_manifest_content_identity(corrected, contract)
    return corrected


def _validate_repair_manifest_profile(
    document: Mapping[str, Any], *, branch: str, contract: Mapping[str, Any]
) -> None:
    validate_capsule_manifest(document, require_frozen=False)
    lineage = contract["predecessor_capsule_lineage"]
    schema = lineage["manifest_json_schema"]
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(dict(document)))
    frozen = lineage["frozen_predecessor_inventory"]["components"]
    actual = document.get("component_inventory")
    if (
        type(actual) is not list
        or len(actual) != len(PREDECESSOR_COMPONENT_IDS)
        or any(type(item) is not dict for item in actual)
        or type(document.get("entries")) is not list
        or len(document["entries"]) != 4129
    ):
        raise ContractError("manifest repair entry/component count drift")
    if branch == "corrected":
        if actual != frozen:
            raise ContractError(
                "corrected manifest is not the exact frozen component inventory"
            )
        if errors:
            raise ContractError(
                f"corrected manifest frozen validation failed: {errors[0].message}"
            )
        _corrected_manifest_content_identity(document, contract)
        return
    if branch != "old":
        raise ContractError("unknown manifest repair branch")
    try:
        legacy = [
            {field: item[field] for field in _MANIFEST_COMPONENT_CORE_FIELDS}
            for item in frozen
        ]
    except (KeyError, TypeError) as error:
        raise ContractError("frozen component inventory core authority drift") from error
    if actual != legacy:
        raise ContractError(
            "manifest repair is not the exact mechanical legacy projection"
        )
    _validate_known_old_manifest_schema_error(
        errors, actual=actual, frozen=frozen
    )
    _mechanically_corrected_manifest(document, contract)


def _repair_component_state(
    contract: Mapping[str, Any], *, allow_production: bool
) -> list[dict[str, Any]]:
    transition = contract["write_boundaries"]["execution_artifacts"][
        "scoped_artifact_policy"
    ][
        "a46_3_closed_transition_exception"
    ]["components"]
    frozen = contract["predecessor_capsule_lineage"][
        "frozen_predecessor_inventory"
    ]["components"]
    if len(transition) != 4 or len(frozen) != 4:
        raise ContractError("manifest repair component set is not exactly four")
    state: list[dict[str, Any]] = []
    for component_id, paths, expected in zip(
        PREDECESSOR_COMPONENT_IDS, transition, frozen
    ):
        if expected["component_id"] != component_id:
            raise ContractError("manifest repair component order drift")
        source, _ = _authorized_transition_path(
            str(paths["source"]).rstrip("/"), allow_production=allow_production
        )
        staging, _ = _authorized_transition_path(
            str(paths["staging_destination"]).rstrip("/"),
            allow_production=allow_production,
        )
        if os.path.lexists(source) or not os.path.lexists(staging):
            raise ContractError("manifest repair source/staging multiplicity drift")
        single_file_name = (
            Path(expected["source_root"]).name
            if expected["directory_count"] == 0
            else None
        )
        inventory = component_inventory(
            staging,
            component_id,
            single_file_logical_basename=single_file_name,
        )
        validate_component_inventory(inventory, expected)
        state.append(
            {
                "component_id": component_id,
                "source_path": str(paths["source"]).rstrip("/"),
                "staging_path": str(paths["staging_destination"]).rstrip("/"),
                "inventory_sha256": inventory["inventory_sha256"],
                "source_absent": True,
                "staging_present": True,
            }
        )
    return state


def _scope_lock_identity(path: Path, descriptor: int) -> dict[str, Any]:
    """Bind one privately opened component-scope FD to its no-follow path."""

    try:
        opened = os.fstat(descriptor)
        linked = path.lstat()
    except OSError as error:
        raise ContractError(f"scope lock identity read failed: {error}") from error
    if stat.S_ISREG(opened.st_mode):
        entry_type = "regular_file"
    elif stat.S_ISDIR(opened.st_mode):
        entry_type = "directory"
    else:
        raise ContractError("scope lock is not a regular file or directory")
    if (
        stat.S_ISLNK(linked.st_mode)
        or opened.st_dev != linked.st_dev
        or opened.st_ino != linked.st_ino
        or opened.st_mode != linked.st_mode
        or opened.st_nlink != linked.st_nlink
        or opened.st_size != linked.st_size
    ):
        raise ContractError("scope lock FD/path identity changed")
    return {
        "st_dev": opened.st_dev,
        "st_ino": opened.st_ino,
        "entry_type": entry_type,
        "mode": f"0{stat.S_IMODE(opened.st_mode):03o}",
        "nlink": opened.st_nlink,
        "size_bytes": opened.st_size,
    }


def _open_scope_lock(path: Path) -> int:
    try:
        linked = path.lstat()
    except OSError as error:
        raise ContractError(f"scope lock path read failed: {error}") from error
    if stat.S_ISLNK(linked.st_mode):
        raise ContractError("scope lock path is a symlink")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    if stat.S_ISDIR(linked.st_mode):
        flags |= os.O_DIRECTORY
    elif not stat.S_ISREG(linked.st_mode):
        raise ContractError("scope lock path is not a regular file or directory")
    try:
        return os.open(path, flags)
    except OSError as error:
        raise ContractError(f"scope lock open failed: {error}") from error


def _probe_exclusive_flock(path: Path, descriptor: int, label: str) -> None:
    """Prove both path contention and this exact descriptor's EX ownership."""

    probe = _open_scope_lock(path)
    acquired = False
    try:
        try:
            fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError as error:
            if error.errno not in (errno.EACCES, errno.EAGAIN):
                raise ContractError(
                    f"{label} exclusive-flock probe failed: {error}"
                ) from error
        if acquired:
            raise ContractError(f"{label} descriptor is not exclusively flocked")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EAGAIN):
                raise ContractError(
                    f"{label} registered descriptor does not own the exclusive flock"
                ) from error
            raise ContractError(
                f"{label} descriptor ownership reassertion failed: {error}"
            ) from error
        os.fstat(descriptor)
    finally:
        if acquired:
            fcntl.flock(probe, fcntl.LOCK_UN)
        os.close(probe)


def _manifest_repair_scope_paths(
    contract: Mapping[str, Any], *, allow_production: bool
) -> list[tuple[str, Path, str]]:
    components = contract["write_boundaries"]["execution_artifacts"][
        "scoped_artifact_policy"
    ]["a46_3_closed_transition_exception"]["components"]
    if type(components) is not list or len(components) != len(
        PREDECESSOR_COMPONENT_IDS
    ):
        raise ContractError("manifest-repair scope set is not exactly four")
    result: list[tuple[str, Path, str]] = []
    for component_id, component in zip(PREDECESSOR_COMPONENT_IDS, components):
        if type(component) is not dict:
            raise ContractError("manifest-repair scope component shape drift")
        path, lexical = _authorized_transition_path(
            str(component["staging_destination"]).rstrip("/"),
            allow_production=allow_production,
        )
        result.append((component_id, path, lexical))
    if [item[0] for item in result] != list(PREDECESSOR_COMPONENT_IDS) or len(
        {item[2] for item in result}
    ) != len(PREDECESSOR_COMPONENT_IDS):
        raise ContractError("manifest-repair scope paths are not exact and ordered")
    return result


@contextmanager
def acquire_manifest_repair_locks(
    *,
    expected_admission_identity: Mapping[str, Any],
    allow_production: bool = False,
    contract: Mapping[str, Any] | None = None,
):
    """Acquire the opaque lease; admission EX is the runtime quiescence proof."""

    if type(allow_production) is not bool:
        raise ContractError("manifest-repair production permission must be boolean")
    if allow_production is True and contract is not None:
        raise ContractError("production repair must load the committed contract")
    authority = dict(contract) if contract is not None else load_contract()
    admission_raw = authority["predecessor_capsule_lineage"]["paths"][
        "admission_lock"
    ]
    admission_path, admission_lexical = _authorized_transition_path(
        admission_raw, allow_production=allow_production
    )
    if allow_production and admission_lexical != PRODUCTION_ADMISSION_LOCK_PATH:
        raise ContractError("production repair admission path mismatch")
    scope_specs = _manifest_repair_scope_paths(
        authority, allow_production=allow_production
    )
    admission_descriptor: int | None = None
    scopes: list[dict[str, Any]] = []
    context: ManifestRepairLockContext | None = None
    try:
        try:
            admission_descriptor = os.open(
                admission_path, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
            )
        except OSError as error:
            raise ContractError(f"admission lock open failed: {error}") from error
        try:
            fcntl.flock(
                admission_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB
            )
        except OSError as error:
            raise ContractError(
                f"exclusive admission lock acquisition failed: {error}"
            ) from error
        admission_identity_value = admission_lock_identity(
            admission_path,
            admission_descriptor,
            allow_production=allow_production,
            expected_identity=expected_admission_identity,
        )
        for scope_id, path, lexical in scope_specs:
            descriptor = _open_scope_lock(path)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                os.close(descriptor)
                raise ContractError(
                    f"exclusive scope lock acquisition failed for {scope_id}: {error}"
                ) from error
            try:
                identity = _scope_lock_identity(path, descriptor)
            except Exception:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
                os.close(descriptor)
                raise
            scopes.append(
                {
                    "scope_id": scope_id,
                    "path": path,
                    "lexical_path": lexical,
                    "descriptor": descriptor,
                    "identity": identity,
                }
            )
        context = ManifestRepairLockContext(_MANIFEST_REPAIR_LOCK_CONTEXT_KEY)
        _ACTIVE_MANIFEST_REPAIR_LOCK_CONTEXTS[context] = {
            "authority_sha256": canonical_sha256(authority),
            "allow_production": allow_production,
            "admission_path": admission_path,
            "admission_descriptor": admission_descriptor,
            "admission_identity": admission_identity_value,
            "scopes": scopes,
        }
        _validate_manifest_repair_lock_context(
            context, contract=authority, allow_production=allow_production
        )
        yield context
    finally:
        if context is not None:
            _ACTIVE_MANIFEST_REPAIR_LOCK_CONTEXTS.pop(context, None)
        for scope in reversed(scopes):
            try:
                fcntl.flock(scope["descriptor"], fcntl.LOCK_UN)
            finally:
                os.close(scope["descriptor"])
        if admission_descriptor is not None:
            try:
                fcntl.flock(admission_descriptor, fcntl.LOCK_UN)
            finally:
                os.close(admission_descriptor)


def _validate_manifest_repair_lock_context(
    context: object,
    *,
    contract: Mapping[str, Any],
    allow_production: bool,
) -> tuple[Path, int, dict[str, Any], list[dict[str, Any]]]:
    if type(context) is not ManifestRepairLockContext:
        raise ContractError("active acquired manifest-repair lock context required")
    record = _ACTIVE_MANIFEST_REPAIR_LOCK_CONTEXTS.get(context)
    if record is None:
        raise ContractError("manifest-repair lock context is stale or foreign")
    if (
        record["authority_sha256"] != canonical_sha256(contract)
        or record["allow_production"] is not allow_production
    ):
        raise ContractError("manifest-repair lock context authority mismatch")
    admission_path = record["admission_path"]
    admission_descriptor = record["admission_descriptor"]
    admission_identity_value = admission_lock_identity(
        admission_path,
        admission_descriptor,
        allow_production=allow_production,
        expected_identity=record["admission_identity"],
    )
    _probe_exclusive_flock(
        admission_path, admission_descriptor, "manifest-repair admission lock"
    )
    expected_scopes = _manifest_repair_scope_paths(
        contract, allow_production=allow_production
    )
    scopes = record["scopes"]
    if [item["scope_id"] for item in scopes] != list(PREDECESSOR_COMPONENT_IDS):
        raise ContractError("scope locks are missing or out of frozen order")
    projection: list[dict[str, Any]] = []
    for scope, (scope_id, path, lexical) in zip(scopes, expected_scopes):
        if (
            scope["scope_id"] != scope_id
            or scope["path"] != path
            or scope["lexical_path"] != lexical
        ):
            raise ContractError("manifest-repair scope path/order drift")
        identity = _scope_lock_identity(path, scope["descriptor"])
        if identity != scope["identity"]:
            raise ContractError("scope lock FD/path identity changed")
        _probe_exclusive_flock(
            path, scope["descriptor"], f"manifest-repair scope {scope_id}"
        )
        projection.append(
            {"scope_id": scope_id, "path": lexical, **identity}
        )
    return (
        admission_path,
        admission_descriptor,
        admission_identity_value,
        projection,
    )


def classify_one_time_manifest_repair(
    *,
    target_path: str,
    temp_path: str,
    target_identity: Mapping[str, Any],
    target_document: Mapping[str, Any],
    journal_path: str,
    journal_raw_sha256: str,
    journal: Mapping[str, Any],
    admission_lock_identity_value: Mapping[str, Any],
    scope_lock_projection: Sequence[Mapping[str, Any]],
    component_state: Sequence[Mapping[str, Any]],
    final_capsule_absent: bool,
    lineage_seal_absent: bool,
    temp_absent: bool,
    contract: Mapping[str, Any] | None = None,
) -> str:
    """Classify the sole exact A46.4 repair boundary without mutation."""

    authority = dict(contract) if contract is not None else load_contract()
    lineage = authority["predecessor_capsule_lineage"]
    repair = lineage["one_time_manifest_repair"]
    paths = lineage["paths"]
    if target_path != repair["target_path"] or temp_path != repair["fixed_temp_path"]:
        raise ContractError("manifest repair target/temp path drift")
    if journal_path != paths["journal"]:
        raise ContractError("manifest repair journal path drift")
    if (
        final_capsule_absent is not True
        or lineage_seal_absent is not True
        or temp_absent is not True
    ):
        raise ContractError("manifest repair final/seal/temp absence drift")
    validate_transition_journal(journal, production_identity=False)
    expected_journal = repair["pre_repair_journal_identity"]
    observed_journal = {
        "raw_sha256": journal_raw_sha256,
        "document_digest": journal.get("document_digest"),
        "state": journal.get("state"),
        "event_count": len(journal.get("events", [])),
        "last_action": journal.get("events", [{}])[-1].get("action"),
        "relocated_components": journal.get("relocated_components"),
        "admission_lock_identity_digest": journal.get(
            "admission_lock_identity", {}
        ).get("identity_digest"),
    }
    if observed_journal != expected_journal:
        raise ContractError("manifest repair journal is not the exact five-event prefix")
    if (
        admission_lock_identity_value.get("identity_digest")
        != expected_journal["admission_lock_identity_digest"]
        or journal["admission_lock_identity"]
        != dict(admission_lock_identity_value)
    ):
        raise ContractError("manifest repair admission identity drift")
    if type(scope_lock_projection) is not list or [
        item.get("scope_id") if type(item) is dict else None
        for item in scope_lock_projection
    ] != list(PREDECESSOR_COMPONENT_IDS):
        raise ContractError("manifest repair scope-lock projection drift")
    expected_components = authority["write_boundaries"]["execution_artifacts"][
        "scoped_artifact_policy"
    ][
        "a46_3_closed_transition_exception"
    ]["components"]
    frozen_components = lineage["frozen_predecessor_inventory"]["components"]
    expected_state = [
        {
            "component_id": component_id,
            "source_path": str(paths_item["source"]).rstrip("/"),
            "staging_path": str(paths_item["staging_destination"]).rstrip("/"),
            "inventory_sha256": frozen_item["inventory_sha256"],
            "source_absent": True,
            "staging_present": True,
        }
        for component_id, paths_item, frozen_item in zip(
            PREDECESSOR_COMPONENT_IDS, expected_components, frozen_components
        )
    ]
    if list(component_state) != expected_state:
        raise ContractError("manifest repair component/source state drift")
    old_fields = (
        "entry_type",
        "mode",
        "nlink",
        "st_dev",
        "st_ino",
        "size_bytes",
        "raw_sha256",
        "document_digest",
        "mtime_utc",
        "ctime_utc",
    )
    corrected_fields = (
        "entry_type",
        "mode",
        "nlink",
        "st_dev",
        "size_bytes",
        "raw_sha256",
        "document_digest",
    )
    observed = dict(target_identity)
    old = repair["old_manifest_identity"]
    corrected = repair["corrected_manifest_identity"]
    if {field: observed.get(field) for field in old_fields} == {
        field: old[field] for field in old_fields
    }:
        _validate_repair_manifest_profile(
            target_document, branch="old", contract=authority
        )
        return "replace_once"
    if {field: observed.get(field) for field in corrected_fields} == {
        field: corrected[field] for field in corrected_fields
    }:
        _validate_repair_manifest_profile(
            target_document, branch="corrected", contract=authority
        )
        return "verify_staging"
    raise ContractError("BLOCKED_TRANSITION: manifest identity is neither exact branch")


def _capture_manifest_repair_state(
    *,
    contract: Mapping[str, Any],
    lock_context: ManifestRepairLockContext,
    allow_production: bool,
) -> dict[str, Any]:
    lineage = contract["predecessor_capsule_lineage"]
    repair = lineage["one_time_manifest_repair"]
    target, _ = _authorized_transition_path(
        repair["target_path"], allow_production=allow_production
    )
    temporary, _ = _authorized_transition_path(
        repair["fixed_temp_path"], allow_production=allow_production
    )
    _, _, identity, scope_projection = _validate_manifest_repair_lock_context(
        lock_context,
        contract=contract,
        allow_production=allow_production,
    )
    target_identity, target_document = _manifest_snapshot(target)
    journal, _ = _authorized_transition_path(
        lineage["paths"]["journal"], allow_production=allow_production
    )
    journal_identity, journal_document = _manifest_snapshot(journal)
    final_capsule, _ = _authorized_transition_path(
        lineage["paths"]["final_capsule"], allow_production=allow_production
    )
    seal, _ = _authorized_transition_path(
        lineage["paths"]["durable_lineage_seal"],
        allow_production=allow_production,
    )
    return {
        "target_path": repair["target_path"],
        "temp_path": repair["fixed_temp_path"],
        "target_identity": target_identity,
        "target_document": target_document,
        "journal_path": lineage["paths"]["journal"],
        "journal_raw_sha256": journal_identity["raw_sha256"],
        "journal": journal_document,
        "admission_lock_identity_value": identity,
        "scope_lock_projection": scope_projection,
        "component_state": _repair_component_state(
            contract, allow_production=allow_production
        ),
        "final_capsule_absent": not os.path.lexists(final_capsule),
        "lineage_seal_absent": not os.path.lexists(seal),
        "temp_absent": not os.path.lexists(temporary),
        "contract": contract,
    }


def repair_staging_manifest_once(
    *,
    corrected_builder: Callable[[], Mapping[str, Any]],
    lock_context: ManifestRepairLockContext | None = None,
    no_live_s10r3_writer: bool | None = None,
    admission_lock_path: Path | str | None = None,
    admission_descriptor: int | None = None,
    expected_admission_identity: Mapping[str, Any] | None = None,
    admission_exclusive: bool | None = None,
    scope_lock_proofs: Sequence[Mapping[str, Any]] | None = None,
    allow_production: bool = False,
    contract: Mapping[str, Any] | None = None,
) -> str:
    """Repair under the live lease; caller idle-writer assertions have no authority."""

    if type(allow_production) is not bool:
        raise ContractError("manifest-repair production permission must be boolean")
    if allow_production is True and contract is not None:
        raise ContractError("production repair must load the committed contract")
    authority = dict(contract) if contract is not None else load_contract()
    if any(
        item is not None
        for item in (
            no_live_s10r3_writer,
            admission_lock_path,
            admission_descriptor,
            expected_admission_identity,
            admission_exclusive,
            scope_lock_proofs,
        )
    ):
        raise ContractError(
            "bare idle-writer/lock booleans, descriptors, identities, or proofs are forbidden"
        )
    _validate_manifest_repair_lock_context(
        lock_context,
        contract=authority,
        allow_production=allow_production,
    )
    before = _capture_manifest_repair_state(
        contract=authority,
        lock_context=lock_context,
        allow_production=allow_production,
    )
    action = classify_one_time_manifest_repair(**before)
    if action == "verify_staging":
        return action
    first = dict(corrected_builder())
    second = dict(corrected_builder())
    first_bytes = canonical_json_bytes(first) + b"\n"
    second_bytes = canonical_json_bytes(second) + b"\n"
    if first_bytes != second_bytes:
        raise ContractError("corrected manifest double build is not byte-identical")
    mechanical_corrected = _mechanically_corrected_manifest(
        before["target_document"], authority
    )
    if first != mechanical_corrected:
        raise ContractError(
            "corrected builder is not the exact mechanical projection"
        )
    _validate_manifest_repair_lock_context(
        lock_context,
        contract=authority,
        allow_production=allow_production,
    )
    repair = authority["predecessor_capsule_lineage"]["one_time_manifest_repair"]
    expected = repair["corrected_manifest_identity"]
    if (
        len(first_bytes) != expected["size_bytes"]
        or hashlib.sha256(first_bytes).hexdigest() != expected["raw_sha256"]
        or first.get("document_digest") != expected["document_digest"]
    ):
        raise ContractError("corrected manifest builder identity mismatch")
    _validate_repair_manifest_profile(first, branch="corrected", contract=authority)
    target, _ = _authorized_transition_path(
        repair["target_path"], allow_production=allow_production
    )
    temporary, _ = _authorized_transition_path(
        repair["fixed_temp_path"], allow_production=allow_production
    )
    if target.parent != temporary.parent:
        raise ContractError("manifest repair temp is not in target parent")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(temporary, flags, 0o600)
    except OSError as error:
        raise ContractError(f"fixed manifest temporary creation failed: {error}") from error
    try:
        os.fchmod(descriptor, 0o600)
        offset = 0
        while offset < len(first_bytes):
            written = os.write(descriptor, first_bytes[offset:])
            if written <= 0:
                raise ContractError("manifest temporary short write made no progress")
            offset += written
        os.fsync(descriptor)
        written_identity = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    temp_identity, temp_document = _manifest_snapshot(temporary)
    if (
        (written_identity.st_dev, written_identity.st_ino)
        != (temp_identity["st_dev"], temp_identity["st_ino"])
        or temp_identity["mode"] != "0600"
        or temp_identity["nlink"] != 1
        or temp_identity["size_bytes"] != expected["size_bytes"]
        or temp_identity["raw_sha256"] != expected["raw_sha256"]
        or temp_document != first
    ):
        raise ContractError("opened manifest temporary identity/content mismatch")
    _validate_repair_manifest_profile(
        temp_document, branch="corrected", contract=authority
    )
    immediate = _capture_manifest_repair_state(
        contract=authority,
        lock_context=lock_context,
        allow_production=allow_production,
    )
    if immediate["temp_absent"] is not False:
        raise ContractError("validated manifest temporary disappeared before replace")
    for key in (
        "target_path",
        "target_identity",
        "target_document",
        "journal_path",
        "journal_raw_sha256",
        "journal",
        "admission_lock_identity_value",
        "scope_lock_projection",
        "component_state",
        "final_capsule_absent",
        "lineage_seal_absent",
    ):
        if immediate[key] != before[key]:
            raise ContractError(f"manifest repair pre-replace race: {key}")
    try:
        os.replace(temporary, target)
    except OSError as error:
        raise ContractError(f"single manifest replacement failed: {error}") from error
    directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    after = _capture_manifest_repair_state(
        contract=authority,
        lock_context=lock_context,
        allow_production=allow_production,
    )
    if classify_one_time_manifest_repair(**after) != "verify_staging":
        raise ContractError("manifest repair postcondition failed")
    for key in (
        "journal_raw_sha256",
        "journal",
        "admission_lock_identity_value",
        "scope_lock_projection",
        "component_state",
    ):
        if after[key] != before[key]:
            raise ContractError(f"manifest repair changed protected {key}")
    return "verify_staging"


def validate_lineage_seal(
    seal: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
    journal: Mapping[str, Any] | None = None,
    require_frozen: bool = True,
    contract: Mapping[str, Any] | None = None,
) -> None:
    document = dict(seal)
    authority = dict(contract) if contract is not None else load_contract()
    if require_frozen:
        schema = authority["predecessor_capsule_lineage"]["seal_json_schema"]
        try:
            jsonschema.Draft7Validator(schema).validate(document)
        except jsonschema.ValidationError as error:
            raise ContractError(f"lineage seal schema failed: {error.message}") from error
    if document.get("document_digest") != _self_digest(document, "document_digest"):
        raise ContractError("lineage seal document digest mismatch")
    if document.get("diagnostic_only") is not True or document.get(
        "admissible_for_successor"
    ) is not False:
        raise ContractError("lineage seal predecessor admission mismatch")
    if document.get("manifest_repair") != manifest_repair_binding(authority):
        raise ContractError("lineage seal manifest-repair binding mismatch")
    expected_authority = {
        "path": DEFAULT_CONTRACT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "commit": G1_PHASE1_SEAL_COMMIT,
        "raw_sha256": G1_CONTRACT_RAW_SHA256,
        "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
    }
    if document.get("authority_contract") != expected_authority:
        raise ContractError("lineage seal A46.4 authority binding mismatch")
    if manifest is not None:
        validate_capsule_manifest(manifest, require_frozen=require_frozen)
        bound = document.get("capsule_manifest", {})
        if (
            bound.get("sha256") != _json_file_sha256(manifest)
            or bound.get("document_digest") != manifest.get("document_digest")
        ):
            raise ContractError("lineage seal capsule manifest binding mismatch")
    if journal is not None:
        validate_transition_journal(journal, production_identity=require_frozen)
        if journal.get("state") != "FINALIZED":
            raise ContractError("lineage seal requires a finalized journal")
        bound = document.get("terminal_journal", {})
        if (
            bound.get("sha256") != _json_file_sha256(journal)
            or bound.get("document_digest") != journal.get("document_digest")
            or bound.get("state") != "FINALIZED"
            or document.get("admission_lock_identity")
            != journal.get("admission_lock_identity")
        ):
            raise ContractError("lineage seal terminal journal binding mismatch")


def build_lineage_seal(
    *,
    authority_contract: Mapping[str, Any],
    final_capsule_root: str,
    predecessor_lock: Mapping[str, Any],
    manifest_path: str,
    manifest: Mapping[str, Any],
    journal_path: str,
    journal: Mapping[str, Any],
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the non-self-referential durable predecessor lineage seal."""

    authority = dict(contract) if contract is not None else load_contract()
    expected_authority = {
        "path": DEFAULT_CONTRACT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "commit": G1_PHASE1_SEAL_COMMIT,
        "raw_sha256": G1_CONTRACT_RAW_SHA256,
        "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
    }
    if dict(authority_contract) != expected_authority:
        raise ContractError("lineage seal requires committed A46.4 authority")
    validate_capsule_manifest(manifest, require_frozen=False)
    validate_transition_journal(journal, production_identity=False)
    if journal["state"] != "FINALIZED":
        raise ContractError("lineage seal requires finalized journal")
    document: dict[str, Any] = {
        "schema_version": 1,
        "document_kind": "s10r3_predecessor_lineage_seal",
        "checkpoint_id": "S10R3",
        "authority_contract": dict(authority_contract),
        "transition_id": G1_TRANSITION_ID,
        "final_capsule_root": final_capsule_root,
        "predecessor_lock": dict(predecessor_lock),
        "capsule_manifest": {
            "path": manifest_path,
            "sha256": _json_file_sha256(manifest),
            "document_digest": manifest["document_digest"],
        },
        "terminal_journal": {
            "path": journal_path,
            "sha256": _json_file_sha256(journal),
            "document_digest": journal["document_digest"],
            "state": "FINALIZED",
        },
        "admission_lock_identity": copy.deepcopy(
            journal["admission_lock_identity"]
        ),
        "manifest_repair": manifest_repair_binding(authority),
        "lifecycle": {
            "execution_status": "CHANGES_REQUIRED",
            "scientific_outcome": "not_evaluated",
            "edge": None,
            "transition_state": "FINALIZED",
        },
        "diagnostic_only": True,
        "admissible_for_successor": False,
        "document_digest": SELF_HASH_PLACEHOLDER,
    }
    document["document_digest"] = _self_digest(document, "document_digest")
    validate_lineage_seal(
        document,
        manifest=manifest,
        journal=journal,
        require_frozen=False,
        contract=authority,
    )
    return document


def _g2_schema(spec: G2LineageSpec, kind: str) -> dict[str, Any]:
    raw = {
        "manifest": spec.manifest_schema_bytes,
        "journal": spec.journal_schema_bytes,
        "seal": spec.seal_schema_bytes,
    }[kind]
    return json.loads(raw.decode("utf-8"))


def _g2_component_frozen_record(
    contract: Mapping[str, Any], component_id: str
) -> dict[str, Any]:
    records = contract[G2_LINEAGE_SELECTOR]["manifest_json_schema"]["properties"][
        "component_inventory"
    ]["const"]
    matches = [item for item in records if item["component_id"] == component_id]
    if len(matches) != 1:
        raise ContractError("G2 frozen component identity is not unique")
    return copy.deepcopy(matches[0])


def validate_g2_capsule_manifest(
    manifest: Mapping[str, Any],
    *,
    selector: str,
    spec: G2LineageSpec | None = None,
    require_frozen: bool = True,
    component_roots: Mapping[str, Path | str] | None = None,
) -> None:
    """Validate the A46.5 manifest without reinterpreting the historical G1."""

    selected = spec or g2_lineage_spec(selector=selector)
    if selected.selector != selector or selector != G2_LINEAGE_SELECTOR:
        raise ContractError("explicit G2 manifest selector mismatch")
    document = dict(manifest)
    if require_frozen:
        try:
            jsonschema.Draft7Validator(_g2_schema(selected, "manifest")).validate(
                document
            )
        except jsonschema.ValidationError as error:
            raise ContractError(f"G2 capsule manifest schema failed: {error.message}") from error
    required = {
        "schema_version",
        "document_kind",
        "transition_id",
        "inventory_algorithm",
        "component_inventory",
        "predecessor",
        "entries",
        "summary",
        "later_evidence_absence",
        "diagnostic_only",
        "admissible_for_successor",
        "document_digest",
    }
    if set(document) != required:
        raise ContractError("G2 capsule manifest unknown or missing field")
    if (
        document["schema_version"] != 1
        or document["document_kind"] != "predecessor_capsule_manifest"
        or document["transition_id"] != selected.transition_id
        or document["inventory_algorithm"]
        != "root_excluded_utf8_byte_sorted_v1"
        or document["diagnostic_only"] is not True
        or document["admissible_for_successor"] is not False
    ):
        raise ContractError("G2 capsule manifest envelope drift")
    if document["document_digest"] != _self_digest(document, "document_digest"):
        raise ContractError("G2 capsule manifest self digest mismatch")
    components = document["component_inventory"]
    entries = document["entries"]
    if type(components) is not list or type(entries) is not list:
        raise ContractError("G2 capsule manifest inventory shape mismatch")
    component_ids = [
        item.get("component_id") if type(item) is dict else None for item in components
    ]
    expected_ids = [item.component_id for item in selected.components]
    if component_ids != expected_ids or len(component_ids) != len(set(component_ids)):
        raise ContractError("G2 capsule manifest component order/uniqueness drift")
    if require_frozen:
        frozen_const = _g2_schema(selected, "manifest")["properties"][
            "component_inventory"
        ]["const"]
        if components != frozen_const:
            raise ContractError("G2 capsule manifest frozen component const drift")
    by_component: dict[str, list[dict[str, Any]]] = {
        component_id: [] for component_id in expected_ids
    }
    order_projection: list[tuple[int, bytes]] = []
    unique_paths: set[tuple[str, str]] = set()
    for entry in entries:
        if type(entry) is not dict or set(entry) != {
            "component_id",
            "logical_path",
            "source_path",
            "final_path",
            "entry_type",
            "mode",
            "size_bytes",
            "sha256",
        }:
            raise ContractError("G2 capsule manifest entry shape drift")
        component_id = entry["component_id"]
        if component_id not in by_component:
            raise ContractError("G2 capsule manifest entry component drift")
        component_index = expected_ids.index(component_id)
        logical = entry["logical_path"]
        if (
            type(logical) is not str
            or not logical
            or logical.startswith("/")
            or ".." in Path(logical.rstrip("/")).parts
        ):
            raise ContractError("G2 capsule manifest logical path escapes")
        unique_key = (component_id, logical)
        if unique_key in unique_paths:
            raise ContractError("G2 capsule manifest component/path duplication")
        unique_paths.add(unique_key)
        order_projection.append((component_index, logical.encode("utf-8")))
        component = components[component_index]
        single_file = component["directory_count"] == 0
        expected_source = (
            component["source_root"]
            if single_file
            else f'{component["source_root"]}/{logical}'
        )
        expected_final = (
            component["final_root"]
            if single_file
            else f'{component["final_root"]}/{logical}'
        )
        if entry["source_path"] != expected_source or entry["final_path"] != expected_final:
            raise ContractError("G2 capsule manifest source/final root mapping drift")
        if entry["entry_type"] == "regular_file":
            if (
                type(entry["size_bytes"]) is not int
                or entry["size_bytes"] < 0
                or type(entry["sha256"]) is not str
                or len(entry["sha256"]) != 64
            ):
                raise ContractError("G2 regular-file entry shape drift")
        elif entry["entry_type"] == "directory":
            if entry["size_bytes"] != 0 or entry["sha256"] is not None:
                raise ContractError("G2 directory entry shape drift")
        else:
            raise ContractError("G2 manifest entry type drift")
        by_component[component_id].append(
            {
                key: entry[key]
                for key in (
                    "logical_path",
                    "entry_type",
                    "mode",
                    "size_bytes",
                    "sha256",
                )
            }
        )
    if order_projection != sorted(order_projection):
        raise ContractError("G2 entries are not component-then-UTF-8 ordered")
    for component, component_spec in zip(components, selected.components):
        records = by_component[component_spec.component_id]
        if records != sorted(records, key=lambda item: item["logical_path"].encode("utf-8")):
            raise ContractError("G2 per-component logical path order drift")
        files = [item for item in records if item["entry_type"] == "regular_file"]
        directories = [item for item in records if item["entry_type"] == "directory"]
        observed = {
            "component_id": component_spec.component_id,
            "entries": records,
            "entry_count": len(records),
            "regular_file_count": len(files),
            "directory_count": len(directories),
            "total_bytes": sum(item["size_bytes"] for item in files),
            "inventory_sha256": canonical_sha256(records),
        }
        validate_component_inventory(observed, component)
        if component_roots is not None:
            if component_spec.component_id not in component_roots:
                raise ContractError("G2 fresh component root is missing")
            fresh = component_inventory(
                component_roots[component_spec.component_id],
                component_spec.component_id,
                single_file_logical_basename=component_spec.single_file_logical_basename,
            )
            validate_component_inventory(fresh, component)
            if fresh["entries"] != records:
                raise ContractError("G2 manifest differs from fresh inventory bytes")
    summary = document["summary"]
    expected_summary = {
        "entry_count": sum(item["entry_count"] for item in components),
        "regular_file_count": sum(item["regular_file_count"] for item in components),
        "directory_count": sum(item["directory_count"] for item in components),
        "total_bytes": sum(item["total_bytes"] for item in components),
        "symlink_count": 0,
        "hardlink_count": 0,
    }
    if summary != expected_summary:
        raise ContractError("G2 capsule manifest aggregate summary drift")


def build_g2_capsule_manifest(
    inventories: Sequence[Mapping[str, Any]],
    *,
    selector: str,
    spec: G2LineageSpec | None = None,
    contract: Mapping[str, Any] | None = None,
    require_frozen: bool = True,
) -> dict[str, Any]:
    """Build the G2 manifest in frozen component then UTF-8 path order."""

    authority = dict(contract) if contract is not None else load_contract()
    selected = spec or g2_lineage_spec(selector=selector, contract=authority)
    if selector != G2_LINEAGE_SELECTOR or selected.selector != selector:
        raise ContractError("explicit G2 manifest builder selector mismatch")
    observed = [dict(item) for item in inventories]
    if [item.get("component_id") for item in observed] != [
        item.component_id for item in selected.components
    ]:
        raise ContractError("G2 manifest builder component order drift")
    if require_frozen:
        frozen_records = authority[selector]["manifest_json_schema"]["properties"][
            "component_inventory"
        ]["const"]
    else:
        frozen_records = [
            {
                "component_id": item.component_id,
                "source_root": item.source_root,
                "final_root": item.final_root,
                "entry_count": item.entry_count,
                "regular_file_count": item.regular_file_count,
                "directory_count": item.directory_count,
                "total_bytes": item.total_bytes,
                "inventory_sha256": item.inventory_sha256,
            }
            for item in selected.components
        ]
    entries: list[dict[str, Any]] = []
    for inventory, component, frozen in zip(
        observed, selected.components, frozen_records
    ):
        validate_component_inventory(inventory, frozen)
        for record in inventory["entries"]:
            logical = record["logical_path"]
            entries.append(
                {
                    "component_id": component.component_id,
                    "logical_path": logical,
                    "source_path": (
                        component.source_root
                        if component.directory_count == 0
                        else f"{component.source_root}/{logical}"
                    ),
                    "final_path": (
                        component.final_root
                        if component.directory_count == 0
                        else f"{component.final_root}/{logical}"
                    ),
                    **{
                        key: record[key]
                        for key in ("entry_type", "mode", "size_bytes", "sha256")
                    },
                }
            )
    document: dict[str, Any] = {
        "schema_version": 1,
        "document_kind": "predecessor_capsule_manifest",
        "transition_id": selected.transition_id,
        "inventory_algorithm": "root_excluded_utf8_byte_sorted_v1",
        "component_inventory": copy.deepcopy(frozen_records),
        "predecessor": copy.deepcopy(
            authority[selector]["manifest_json_schema"]["properties"]["predecessor"][
                "const"
            ]
        ),
        "entries": entries,
        "summary": {
            "entry_count": sum(item["entry_count"] for item in frozen_records),
            "regular_file_count": sum(
                item["regular_file_count"] for item in frozen_records
            ),
            "directory_count": sum(item["directory_count"] for item in frozen_records),
            "total_bytes": sum(item["total_bytes"] for item in frozen_records),
            "symlink_count": 0,
            "hardlink_count": 0,
        },
        "later_evidence_absence": copy.deepcopy(
            authority[selector]["manifest_json_schema"]["properties"][
                "later_evidence_absence"
            ]["const"]
        ),
        "diagnostic_only": True,
        "admissible_for_successor": False,
        "document_digest": SELF_HASH_PLACEHOLDER,
    }
    document["document_digest"] = _self_digest(document, "document_digest")
    validate_g2_capsule_manifest(
        document,
        selector=selector,
        spec=selected,
        require_frozen=require_frozen,
    )
    return document


def _g2_event_digest(event: Mapping[str, Any]) -> str:
    return _self_digest(event, "event_digest")


def new_g2_transition_journal(
    admission_identity_digest: str,
    *,
    selector: str,
    spec: G2LineageSpec | None = None,
) -> dict[str, Any]:
    selected = spec or g2_lineage_spec(selector=selector)
    if admission_identity_digest != selected.admission_identity_digest:
        raise ContractError("G2 prepared admission identity mismatch")
    event: dict[str, Any] = {
        "event_index": 0,
        "event_type": "prepared",
        "state": "PREPARED",
        "component_id": None,
        "admission_lock_identity_digest": admission_identity_digest,
        "previous_event_digest": None,
        "event_digest": SELF_HASH_PLACEHOLDER,
    }
    event["event_digest"] = _g2_event_digest(event)
    document: dict[str, Any] = {
        "schema_version": 1,
        "document_kind": "execution_transition_journal",
        "transition_id": selected.transition_id,
        "admission_lock_identity_digest": admission_identity_digest,
        "state": "PREPARED",
        "events": [event],
        "document_digest": SELF_HASH_PLACEHOLDER,
    }
    document["document_digest"] = _self_digest(document, "document_digest")
    validate_g2_transition_journal(
        document, selector=selector, spec=selected, require_frozen=False
    )
    return document


def validate_g2_transition_journal(
    journal: Mapping[str, Any],
    *,
    selector: str,
    spec: G2LineageSpec | None = None,
    require_frozen: bool = True,
) -> None:
    selected = spec or g2_lineage_spec(selector=selector)
    if selector != G2_LINEAGE_SELECTOR or selected.selector != selector:
        raise ContractError("explicit G2 journal selector mismatch")
    document = dict(journal)
    if require_frozen:
        try:
            jsonschema.Draft7Validator(_g2_schema(selected, "journal")).validate(
                document
            )
        except jsonschema.ValidationError as error:
            raise ContractError(f"G2 transition journal schema failed: {error.message}") from error
    if set(document) != {
        "schema_version",
        "document_kind",
        "transition_id",
        "admission_lock_identity_digest",
        "state",
        "events",
        "document_digest",
    }:
        raise ContractError("G2 transition journal unknown or missing field")
    if (
        document["schema_version"] != 1
        or document["document_kind"] != "execution_transition_journal"
        or document["transition_id"] != selected.transition_id
        or document["admission_lock_identity_digest"]
        != selected.admission_identity_digest
    ):
        raise ContractError("G2 transition journal envelope drift")
    events = document["events"]
    if type(events) is not list or not events or len(events) > 7:
        raise ContractError("G2 transition journal event count drift")
    expected_sequence = [
        ("prepared", None, "PREPARED"),
        *[
            ("component_relocated", item.component_id, "MOVING")
            for item in selected.components
        ],
        ("staging_verified", None, "MOVING"),
        ("finalized", None, "FINALIZED"),
    ]
    previous: str | None = None
    blocked = False
    for index, event in enumerate(events):
        if type(event) is not dict or set(event) != {
            "event_index",
            "event_type",
            "state",
            "component_id",
            "admission_lock_identity_digest",
            "previous_event_digest",
            "event_digest",
        }:
            raise ContractError("G2 transition event shape drift")
        if (
            event["event_index"] != index
            or event["previous_event_digest"] != previous
            or event["admission_lock_identity_digest"]
            != document["admission_lock_identity_digest"]
            or event["event_digest"] != _g2_event_digest(event)
        ):
            raise ContractError("G2 transition event chain/admission drift")
        if event["event_type"] == "blocked":
            if (
                index == 0
                or index != len(events) - 1
                or event["state"] != "BLOCKED_TRANSITION"
                or event["component_id"] is not None
            ):
                raise ContractError("G2 blocked-last semantics drift")
            blocked = True
        elif blocked or index >= len(expected_sequence) or (
            event["event_type"], event["component_id"], event["state"]
        ) != expected_sequence[index]:
            raise ContractError("G2 transition event is not a legal forward prefix")
        previous = event["event_digest"]
    if document["state"] != events[-1]["state"]:
        raise ContractError("G2 transition journal terminal state drift")
    if document["state"] == "FINALIZED" and (
        len(events) != 7 or events[-1]["event_type"] != "finalized"
    ):
        raise ContractError("G2 finalized journal is not exact seven-event chain")
    if document["state"] == "BLOCKED_TRANSITION" and not blocked:
        raise ContractError("G2 blocked state lacks one terminal blocked event")
    if document["state"] not in TRANSITION_STATES:
        raise ContractError("G2 journal state is unknown")
    if document["document_digest"] != _self_digest(document, "document_digest"):
        raise ContractError("G2 transition journal self digest mismatch")


def append_g2_transition_event(
    journal: Mapping[str, Any],
    *,
    event_type: str,
    selector: str,
    spec: G2LineageSpec | None = None,
    component_id: str | None = None,
) -> dict[str, Any]:
    selected = spec or g2_lineage_spec(selector=selector)
    document = copy.deepcopy(dict(journal))
    validate_g2_transition_journal(
        document, selector=selector, spec=selected, require_frozen=False
    )
    if document["state"] in ("FINALIZED", "BLOCKED_TRANSITION"):
        raise ContractError("terminal G2 journal cannot be extended")
    index = len(document["events"])
    expected = [
        ("component_relocated", item.component_id, "MOVING")
        for item in selected.components
    ] + [("staging_verified", None, "MOVING"), ("finalized", None, "FINALIZED")]
    if event_type == "blocked":
        if component_id is not None:
            raise ContractError("G2 blocked event component must be null")
        state = "BLOCKED_TRANSITION"
    else:
        expected_index = index - 1
        if expected_index >= len(expected) or (event_type, component_id) != expected[
            expected_index
        ][:2]:
            raise ContractError("G2 append event is not the next legal action")
        state = expected[expected_index][2]
    event: dict[str, Any] = {
        "event_index": index,
        "event_type": event_type,
        "state": state,
        "component_id": component_id,
        "admission_lock_identity_digest": document[
            "admission_lock_identity_digest"
        ],
        "previous_event_digest": document["events"][-1]["event_digest"],
        "event_digest": SELF_HASH_PLACEHOLDER,
    }
    event["event_digest"] = _g2_event_digest(event)
    document["events"].append(event)
    document["state"] = state
    document["document_digest"] = SELF_HASH_PLACEHOLDER
    document["document_digest"] = _self_digest(document, "document_digest")
    validate_g2_transition_journal(
        document, selector=selector, spec=selected, require_frozen=False
    )
    return document


def _g2_file_identity(path: Path, lexical: str) -> dict[str, Any]:
    info = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ContractError("G2 lineage file is not one regular file")
    return {
        "path": lexical,
        "mode": f"0{stat.S_IMODE(info.st_mode):03o}",
        "size_bytes": info.st_size,
        "raw_sha256": sha256_file(path),
    }


def validate_g2_lineage_seal(
    seal: Mapping[str, Any],
    *,
    selector: str,
    spec: G2LineageSpec | None = None,
    manifest: Mapping[str, Any] | None = None,
    journal: Mapping[str, Any] | None = None,
    component_roots: Mapping[str, Path | str] | None = None,
    require_frozen: bool = True,
    require_files: bool = False,
) -> None:
    selected = spec or g2_lineage_spec(selector=selector)
    if selector != G2_LINEAGE_SELECTOR or selected.selector != selector:
        raise ContractError("explicit G2 seal selector mismatch")
    document = dict(seal)
    if require_frozen:
        try:
            jsonschema.Draft7Validator(_g2_schema(selected, "seal")).validate(
                document
            )
        except jsonschema.ValidationError as error:
            raise ContractError(f"G2 lineage seal schema failed: {error.message}") from error
    if document.get("document_digest") != _self_digest(document, "document_digest"):
        raise ContractError("G2 lineage seal self digest mismatch")
    expected_authority = {
        "path": DEFAULT_CONTRACT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "commit": PHASE1_SEAL_COMMIT,
        "raw_sha256": EXPECTED_CONTRACT_RAW_SHA256,
        "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
    }
    expected_predecessor = {
        "generation_id": selected.predecessor_generation_id,
        "commit": selected.predecessor_lock_commit,
        "raw_sha256": selected.predecessor_lock_raw_sha256,
        "canonical_self_sha256": selected.predecessor_lock_canonical_self_sha256,
    }
    if (
        document.get("authority_contract") != expected_authority
        or document.get("transition_id") != selected.transition_id
        or document.get("final_capsule_root") != selected.final_capsule
        or document.get("predecessor_lock") != expected_predecessor
        or document.get("scientific_oracle_projection_sha256")
        != EXPECTED_ORACLE_PROJECTION_SHA256
    ):
        raise ContractError("G2 lineage seal authority/path identity drift")
    expected_lifecycle = {
        "execution_status": "CHANGES_REQUIRED",
        "scientific_outcome": "not_evaluated",
        "edge": None,
        "diagnostic_only": True,
        "admissible_for_successor": False,
        "empirical_reuse": "forbidden",
        "attempt_02": "diagnostic_only",
    }
    if document.get("lifecycle") != expected_lifecycle:
        raise ContractError("G2 lineage seal lifecycle drift")
    aggregate = {
        "entry_count": sum(item.entry_count for item in selected.components),
        "regular_file_count": sum(
            item.regular_file_count for item in selected.components
        ),
        "directory_count": sum(item.directory_count for item in selected.components),
        "total_bytes": sum(item.total_bytes for item in selected.components),
    }
    if document.get("aggregate_inventory") != aggregate:
        raise ContractError("G2 lineage seal aggregate inventory drift")
    if manifest is not None:
        validate_g2_capsule_manifest(
            manifest,
            selector=selector,
            spec=selected,
            require_frozen=require_frozen,
            component_roots=component_roots,
        )
        binding = document.get("capsule_manifest", {})
        if (
            binding.get("path") != selected.manifest_path
            or binding.get("raw_sha256") != _json_file_sha256(manifest)
            or binding.get("document_digest") != manifest["document_digest"]
        ):
            raise ContractError("G2 seal manifest binding drift")
    if journal is not None:
        validate_g2_transition_journal(
            journal,
            selector=selector,
            spec=selected,
            require_frozen=require_frozen,
        )
        binding = document.get("terminal_journal", {})
        if (
            journal["state"] != "FINALIZED"
            or binding.get("path") != selected.journal
            or binding.get("raw_sha256") != _json_file_sha256(journal)
            or binding.get("document_digest") != journal["document_digest"]
            or binding.get("state") != "FINALIZED"
            or document.get("admission_lock_identity", {}).get("identity_digest")
            != journal["admission_lock_identity_digest"]
        ):
            raise ContractError("G2 seal terminal journal/admission binding drift")
    if require_files:
        for field, expected_path in (
            ("capsule_manifest", selected.manifest_path),
            ("terminal_journal", selected.journal),
        ):
            binding = document[field]
            path = REPOSITORY_ROOT / expected_path
            identity = _g2_file_identity(path, expected_path)
            if any(binding.get(key) != value for key, value in identity.items()):
                raise ContractError("G2 seal bound file bytes drift")


def build_g2_lineage_seal(
    *,
    selector: str,
    admission_identity: Mapping[str, Any],
    manifest_path: Path | str,
    manifest: Mapping[str, Any],
    journal_path: Path | str,
    journal: Mapping[str, Any],
    spec: G2LineageSpec | None = None,
    component_roots: Mapping[str, Path | str] | None = None,
    require_frozen: bool = True,
) -> dict[str, Any]:
    selected = spec or g2_lineage_spec(selector=selector)
    if admission_identity.get("identity_digest") != selected.admission_identity_digest:
        raise ContractError("G2 seal admission identity mismatch")
    validate_g2_capsule_manifest(
        manifest,
        selector=selector,
        spec=selected,
        require_frozen=require_frozen,
        component_roots=component_roots,
    )
    validate_g2_transition_journal(
        journal, selector=selector, spec=selected, require_frozen=require_frozen
    )
    if journal["state"] != "FINALIZED":
        raise ContractError("G2 seal requires finalized journal")
    manifest_file = _g2_file_identity(Path(manifest_path), selected.manifest_path)
    journal_file = _g2_file_identity(Path(journal_path), selected.journal)
    document: dict[str, Any] = {
        "schema_version": 1,
        "document_kind": "predecessor_lineage_seal",
        "checkpoint_id": "S10R3",
        "authority_contract": {
            "path": DEFAULT_CONTRACT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
            "commit": PHASE1_SEAL_COMMIT,
            "raw_sha256": EXPECTED_CONTRACT_RAW_SHA256,
            "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
        },
        "transition_id": selected.transition_id,
        "final_capsule_root": selected.final_capsule,
        "predecessor_lock": {
            "generation_id": selected.predecessor_generation_id,
            "commit": selected.predecessor_lock_commit,
            "raw_sha256": selected.predecessor_lock_raw_sha256,
            "canonical_self_sha256": selected.predecessor_lock_canonical_self_sha256,
        },
        "capsule_manifest": {
            **manifest_file,
            "document_digest": manifest["document_digest"],
        },
        "terminal_journal": {
            **journal_file,
            "document_digest": journal["document_digest"],
            "state": "FINALIZED",
        },
        "admission_lock_identity": copy.deepcopy(dict(admission_identity)),
        "aggregate_inventory": {
            "entry_count": sum(item.entry_count for item in selected.components),
            "regular_file_count": sum(
                item.regular_file_count for item in selected.components
            ),
            "directory_count": sum(
                item.directory_count for item in selected.components
            ),
            "total_bytes": sum(item.total_bytes for item in selected.components),
        },
        "lifecycle": {
            "execution_status": "CHANGES_REQUIRED",
            "scientific_outcome": "not_evaluated",
            "edge": None,
            "diagnostic_only": True,
            "admissible_for_successor": False,
            "empirical_reuse": "forbidden",
            "attempt_02": "diagnostic_only",
        },
        "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
        "document_digest": SELF_HASH_PLACEHOLDER,
    }
    document["document_digest"] = _self_digest(document, "document_digest")
    validate_g2_lineage_seal(
        document,
        selector=selector,
        spec=selected,
        manifest=manifest,
        journal=journal,
        component_roots=component_roots,
        require_frozen=require_frozen,
    )
    return document


def write_g2_transition_journal(
    path: Path | str,
    journal: Mapping[str, Any],
    *,
    selector: str,
    spec: G2LineageSpec | None = None,
    allow_production: bool = False,
) -> None:
    """Write only the selected G2 journal through its one fixed temp path."""

    selected = spec or g2_lineage_spec(selector=selector)
    target, lexical = _authorized_transition_path(
        path, allow_production=allow_production
    )
    temporary, temp_lexical = _authorized_transition_path(
        selected.journal_temp, allow_production=allow_production
    )
    if lexical != selected.journal or temp_lexical != selected.journal_temp:
        raise ContractError("G2 journal path is not the explicit selected path")
    if temporary != Path(f"{target}.tmp"):
        raise ContractError("G2 journal temp is not the fixed adjacent path")
    validate_g2_transition_journal(
        journal,
        selector=selector,
        spec=selected,
        require_frozen=allow_production,
    )
    if os.path.lexists(temporary):
        raise ContractError("unexpected G2 fixed journal temp exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json_bytes(dict(journal)) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def _g2_component_expected(component: G2ComponentSpec) -> dict[str, Any]:
    return {
        "component_id": component.component_id,
        "entry_count": component.entry_count,
        "regular_file_count": component.regular_file_count,
        "directory_count": component.directory_count,
        "total_bytes": component.total_bytes,
        "inventory_sha256": component.inventory_sha256,
    }


def _g2_component_locations(
    spec: G2LineageSpec, *, allow_production: bool
) -> tuple[dict[str, str], dict[str, Path]]:
    locations: dict[str, str] = {}
    paths: dict[str, Path] = {}
    for component in spec.components:
        candidates = {
            "source": _authorized_transition_path(
                component.source_root, allow_production=allow_production
            )[0],
            "staging": _authorized_transition_path(
                component.staging_root, allow_production=allow_production
            )[0],
            "final": _authorized_transition_path(
                component.final_root, allow_production=allow_production
            )[0],
        }
        present = [name for name, path in candidates.items() if os.path.lexists(path)]
        if len(present) != 1:
            raise ContractError("G2 component source/staging/final multiplicity is not one")
        location = present[0]
        path = candidates[location]
        inventory = component_inventory(
            path,
            component.component_id,
            single_file_logical_basename=component.single_file_logical_basename,
        )
        validate_component_inventory(inventory, _g2_component_expected(component))
        locations[component.component_id] = location
        paths[component.component_id] = path
    return locations, paths


@contextmanager
def _g2_transition_locks(
    spec: G2LineageSpec, *, allow_production: bool
):
    admission_path, _ = _authorized_transition_path(
        spec.admission_lock, allow_production=allow_production
    )
    descriptors: list[tuple[str, int, os.stat_result]] = []
    with stable_admission_lock(
        admission_path,
        exclusive=True,
        allow_production=allow_production,
    ) as (admission_fd, identity):
        if identity["identity_digest"] != spec.admission_identity_digest:
            raise ContractError("G2 stable admission inode differs from frozen identity")
        _, paths = _g2_component_locations(spec, allow_production=allow_production)
        try:
            for component in spec.components:
                path = paths[component.component_id]
                flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                descriptor = os.open(path, flags)
                info = os.fstat(descriptor)
                linked = path.lstat()
                if (
                    stat.S_ISLNK(linked.st_mode)
                    or (info.st_dev, info.st_ino) != (linked.st_dev, linked.st_ino)
                ):
                    raise ContractError("G2 scope lock no-follow identity mismatch")
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as error:
                    os.close(descriptor)
                    raise ContractError("G2 ordered scope lock acquisition failed") from error
                descriptors.append((component.component_id, descriptor, info))

            def recheck() -> None:
                _, current = _g2_component_locations(
                    spec, allow_production=allow_production
                )
                for component_id, descriptor, opened in descriptors:
                    linked = current[component_id].lstat()
                    now = os.fstat(descriptor)
                    if (
                        (now.st_dev, now.st_ino) != (opened.st_dev, opened.st_ino)
                        or (linked.st_dev, linked.st_ino)
                        != (opened.st_dev, opened.st_ino)
                    ):
                        raise ContractError("G2 scope lock identity changed")
                admission_lock_identity(
                    admission_path,
                    admission_fd,
                    allow_production=allow_production,
                    expected_identity=identity,
                )

            yield admission_fd, identity, recheck
            recheck()
        finally:
            for _, descriptor, _ in reversed(descriptors):
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                finally:
                    os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_rename_parents(
    source: Path | str,
    destination: Path | str,
    *,
    allow_production: bool,
) -> None:
    """Durably order both rename parents before any journal acknowledgement."""

    source_path, _ = _authorized_transition_path(
        source, allow_production=allow_production
    )
    destination_path, _ = _authorized_transition_path(
        destination, allow_production=allow_production
    )
    parents: list[Path] = []
    for parent in (source_path.parent, destination_path.parent):
        if parent not in parents:
            _fsync_directory(parent)
            parents.append(parent)


def _g2_expected_locations(
    journal: Mapping[str, Any], spec: G2LineageSpec
) -> tuple[list[str], list[str] | None]:
    relocated = sum(
        event["event_type"] == "component_relocated" for event in journal["events"]
    )
    exact = ["staging"] * relocated + ["source"] * (
        len(spec.components) - relocated
    )
    one_ahead = None
    if relocated < len(spec.components):
        one_ahead = ["staging"] * (relocated + 1) + ["source"] * (
            len(spec.components) - relocated - 1
        )
    return exact, one_ahead


def execute_g2_transition(
    *,
    selector: str,
    allow_production: bool,
    durable_seal_path: Path | str | None = None,
    spec: G2LineageSpec | None = None,
    require_frozen: bool | None = None,
) -> dict[str, Any]:
    """Run or resume the sole forward G2 retirement sequence."""

    if type(allow_production) is not bool:
        raise ContractError("G2 production flag must be an explicit boolean")
    selected = spec or g2_lineage_spec(selector=selector)
    if selector != G2_LINEAGE_SELECTOR or selected.selector != selector:
        raise ContractError("explicit G2 transition selector is required")
    frozen = allow_production if require_frozen is None else require_frozen
    if allow_production:
        exact = g2_lineage_spec(selector=selector)
        if selected != exact or frozen is not True:
            raise ContractError("production G2 transition requires the exact frozen spec")
        if durable_seal_path is not None and Path(durable_seal_path).as_posix() != selected.seal_path:
            raise ContractError("production G2 seal path is not exact")
    journal_path, _ = _authorized_transition_path(
        selected.journal, allow_production=allow_production
    )
    staging_root, _ = _authorized_transition_path(
        selected.staging_capsule, allow_production=allow_production
    )
    final_root, _ = _authorized_transition_path(
        selected.final_capsule, allow_production=allow_production
    )
    journal_temp_path, _ = _authorized_transition_path(
        selected.journal_temp, allow_production=allow_production
    )
    staging_manifest = staging_root / "predecessor-manifest.json"
    final_manifest = final_root / "predecessor-manifest.json"
    _authorized_transition_path(staging_manifest, allow_production=allow_production)
    _authorized_transition_path(final_manifest, allow_production=allow_production)
    with _g2_transition_locks(selected, allow_production=allow_production) as (
        admission_fd,
        admission_identity,
        recheck_locks,
    ):
        if os.path.lexists(journal_temp_path):
            raise ContractError("unexpected G2 journal temp blocks recovery")
        if journal_path.exists():
            journal = strict_load_json(journal_path)
            validate_g2_transition_journal(
                journal,
                selector=selector,
                spec=selected,
                require_frozen=frozen,
            )
        else:
            journal = new_g2_transition_journal(
                admission_identity["identity_digest"],
                selector=selector,
                spec=selected,
            )
            write_g2_transition_journal(
                journal_path,
                journal,
                selector=selector,
                spec=selected,
                allow_production=allow_production,
            )
            recheck_locks()
        if journal["state"] == "BLOCKED_TRANSITION":
            raise ContractError("G2 transition is durably blocked")
        while journal["state"] != "FINALIZED":
            locations, _ = _g2_component_locations(
                selected, allow_production=allow_production
            )
            actual = [locations[item.component_id] for item in selected.components]
            exact, one_ahead = _g2_expected_locations(journal, selected)
            last = journal["events"][-1]["event_type"]
            if actual == ["final"] * len(selected.components):
                if last != "staging_verified":
                    raise ContractError("G2 final capsule precedes staging verification")
                recheck_locks()
                journal = append_g2_transition_event(
                    journal,
                    event_type="finalized",
                    selector=selector,
                    spec=selected,
                )
                write_g2_transition_journal(
                    journal_path,
                    journal,
                    selector=selector,
                    spec=selected,
                    allow_production=allow_production,
                )
                recheck_locks()
                continue
            if "final" in actual:
                raise ContractError("partial G2 final capsule is forbidden")
            relocated = sum(item == "staging" for item in exact)
            if actual == one_ahead:
                component = selected.components[relocated]
                _fsync_rename_parents(
                    component.source_root,
                    component.staging_root,
                    allow_production=allow_production,
                )
                recheck_locks()
                journal = append_g2_transition_event(
                    journal,
                    event_type="component_relocated",
                    component_id=component.component_id,
                    selector=selector,
                    spec=selected,
                )
                write_g2_transition_journal(
                    journal_path,
                    journal,
                    selector=selector,
                    spec=selected,
                    allow_production=allow_production,
                )
                recheck_locks()
                continue
            if actual != exact:
                raise ContractError("G2 filesystem is not a legal journal prefix")
            if relocated < len(selected.components):
                recheck_locks()
                if os.path.lexists(staging_manifest):
                    raise ContractError("G2 manifest exists before all relocations")
                if not staging_root.exists():
                    staging_root.mkdir(mode=0o700, parents=True)
                    _fsync_directory(staging_root.parent)
                component = selected.components[relocated]
                rename_noreplace(
                    component.source_root,
                    component.staging_root,
                    allow_production=allow_production,
                )
                _fsync_rename_parents(
                    component.source_root,
                    component.staging_root,
                    allow_production=allow_production,
                )
                continue
            staging_roots = {
                item.component_id: _authorized_transition_path(
                    item.staging_root, allow_production=allow_production
                )[0]
                for item in selected.components
            }
            inventories = [
                component_inventory(
                    staging_roots[item.component_id],
                    item.component_id,
                    single_file_logical_basename=item.single_file_logical_basename,
                )
                for item in selected.components
            ]
            first = build_g2_capsule_manifest(
                inventories,
                selector=selector,
                spec=selected,
                require_frozen=frozen,
            )
            second = build_g2_capsule_manifest(
                inventories,
                selector=selector,
                spec=selected,
                require_frozen=frozen,
            )
            if canonical_json_bytes(first) != canonical_json_bytes(second):
                raise ContractError("G2 double manifest build is not byte-identical")
            if staging_manifest.exists():
                if strict_load_json(staging_manifest) != first:
                    raise ContractError("existing G2 staging manifest bytes drift")
            else:
                atomic_write_json(staging_manifest, first, exclusive=True)
            validate_g2_capsule_manifest(
                first,
                selector=selector,
                spec=selected,
                require_frozen=frozen,
                component_roots=staging_roots,
            )
            if last == "component_relocated":
                recheck_locks()
                journal = append_g2_transition_event(
                    journal,
                    event_type="staging_verified",
                    selector=selector,
                    spec=selected,
                )
                write_g2_transition_journal(
                    journal_path,
                    journal,
                    selector=selector,
                    spec=selected,
                    allow_production=allow_production,
                )
                recheck_locks()
                continue
            if last != "staging_verified":
                raise ContractError("G2 manifest exists at an illegal journal boundary")
            if os.path.lexists(final_root):
                raise ContractError("G2 final capsule destination already exists")
            recheck_locks()
            rename_noreplace(
                staging_root, final_root, allow_production=allow_production
            )
            _fsync_rename_parents(
                staging_root,
                final_root,
                allow_production=allow_production,
            )
        final_roots = {
            item.component_id: _authorized_transition_path(
                item.final_root, allow_production=allow_production
            )[0]
            for item in selected.components
        }
        manifest = strict_load_json(final_manifest)
        validate_g2_capsule_manifest(
            manifest,
            selector=selector,
            spec=selected,
            require_frozen=frozen,
            component_roots=final_roots,
        )
        seal = build_g2_lineage_seal(
            selector=selector,
            admission_identity=admission_identity,
            manifest_path=final_manifest,
            manifest=manifest,
            journal_path=journal_path,
            journal=journal,
            spec=selected,
            component_roots=final_roots,
            require_frozen=frozen,
        )
        if durable_seal_path is not None:
            seal_path, seal_lexical = _authorized_transition_path(
                durable_seal_path, allow_production=allow_production
            )
            if seal_lexical != selected.seal_path:
                raise ContractError("G2 durable seal path differs from selected spec")
            if seal_path.exists():
                if strict_load_json(seal_path) != seal:
                    raise ContractError("existing G2 durable seal bytes drift")
            else:
                atomic_write_json(seal_path, seal, exclusive=True)
        admission_lock_identity(
            selected.admission_lock,
            admission_fd,
            allow_production=allow_production,
            expected_identity=admission_identity,
        )
    return {
        "checkpoint_id": "S10R3",
        "action": "complete",
        "state": "FINALIZED",
        "manifest": _g2_file_identity(final_manifest, selected.manifest_path),
        "manifest_document_digest": manifest["document_digest"],
        "journal": _g2_file_identity(journal_path, selected.journal),
        "journal_document_digest": journal["document_digest"],
        "seal_document_digest": seal["document_digest"],
        "seal_written": durable_seal_path is not None,
        "execution_status": "CHANGES_REQUIRED",
        "scientific_outcome": "not_evaluated",
        "edge": None,
        "formal_evidence_started": False,
    }


def build_resource_lineage_binding(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    binding: dict[str, Any] = {
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "generation_id": SUCCESSOR_GENERATION_ID,
        "predecessor_generation_id": PREDECESSOR_GENERATION_ID,
        "records": [copy.deepcopy(dict(item)) for item in records],
        "canonical_sha256": canonical_sha256(list(records)),
        "reset": False,
        "omission": "forbidden",
        "scientific_or_stop_gate": False,
    }
    validate_resource_lineage_binding(binding)
    return binding


def validate_resource_lineage_binding(binding: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "checkpoint_id",
        "generation_id",
        "predecessor_generation_id",
        "records",
        "canonical_sha256",
        "reset",
        "omission",
        "scientific_or_stop_gate",
    }
    if set(binding) != required:
        raise ContractError("resource lineage unknown or missing field")
    if (
        binding["schema_version"] != 1
        or binding["checkpoint_id"] != "S10R3"
        or binding["generation_id"] != SUCCESSOR_GENERATION_ID
        or binding["predecessor_generation_id"] != PREDECESSOR_GENERATION_ID
        or binding["reset"] is not False
        or binding["omission"] != "forbidden"
        or binding["scientific_or_stop_gate"] is not False
    ):
        raise ContractError("resource lineage authority/reset invariant failed")
    records = binding["records"]
    if type(records) is not list or len(records) != 4 or [
        item.get("generation_id") if type(item) is dict else None for item in records
    ] != [
        G1_PREDECESSOR_GENERATION_ID,
        PREDECESSOR_GENERATION_ID,
        PREDECESSOR_GENERATION_ID,
        SUCCESSOR_GENERATION_ID,
    ]:
        raise ContractError("resource lineage must preserve four append-only records")
    if len({item.get("lineage_id") for item in records}) != 4:
        raise ContractError("resource lineage IDs must be distinct")
    quantities = (
        "wall_time",
        "cpu_time",
        "gpu_time",
        "persistent_storage",
        "transient_storage",
    )
    for record in records:
        if set(record) != {"lineage_id", "generation_id", *quantities}:
            raise ContractError("resource lineage record shape mismatch")
        if type(record["lineage_id"]) is not str or not record["lineage_id"]:
            raise ContractError("resource lineage ID is invalid")
        for name in quantities:
            quantity = record[name]
            if type(quantity) is not dict:
                raise ContractError("resource lineage quantity is invalid")
            if quantity.get("status") == "KNOWN":
                if set(quantity) != {
                    "status",
                    "value",
                    "unit",
                    "measurement_boundary",
                    "source",
                } or type(quantity["value"]) not in (int, float) or isinstance(
                    quantity["value"], bool
                ) or not math.isfinite(quantity["value"]) or quantity["value"] < 0 or quantity[
                    "unit"
                ] not in ("seconds", "bytes"):
                    raise ContractError("known resource quantity is malformed")
                if not quantity["measurement_boundary"] or not quantity["source"]:
                    raise ContractError("known resource quantity provenance is absent")
            elif quantity.get("status") == "UNKNOWN":
                if set(quantity) != {
                    "status",
                    "reason",
                    "measurement_boundary",
                } or not quantity["reason"] or not quantity["measurement_boundary"]:
                    raise ContractError("unknown resource quantity boundary is malformed")
            else:
                raise ContractError("resource quantity status must be KNOWN or UNKNOWN")
    if binding["canonical_sha256"] != canonical_sha256(records):
        raise ContractError("resource lineage canonical digest mismatch")


def oracle_projection(contract: Mapping[str, Any]) -> dict[str, Any]:
    definition = contract["implementation_binding_schema"][
        "scientific_oracle_projection_definition"
    ]
    keys = definition["selected_top_level_properties"]
    if type(keys) is not list or not all(type(key) is str for key in keys):
        raise ContractError("scientific projection key list is invalid")
    if set(keys) - set(contract):
        raise ContractError("scientific projection references absent properties")
    return {key: copy.deepcopy(contract[key]) for key in keys}


def load_contract(path: Path | str = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    document = strict_load_yaml(path)
    validate_phase1_contract(document, path=path)
    return document


def manifest_repair_binding(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return the one exact A46.4 lineage-seal repair projection."""

    try:
        repair = contract["predecessor_capsule_lineage"][
            "one_time_manifest_repair"
        ]
        seal_binding = contract["predecessor_capsule_lineage"][
            "seal_json_schema"
        ]["properties"]["manifest_repair"]["const"]
    except (KeyError, TypeError) as error:
        raise ContractError("A46.4 manifest-repair schema binding is absent") from error
    expected = {
        "authority_amendment": MANIFEST_REPAIR_AUTHORITY,
        "target_path": repair["target_path"],
        "old_manifest": {
            key: repair["old_manifest_identity"][key]
            for key in ("size_bytes", "raw_sha256", "document_digest")
        },
        "corrected_manifest": {
            key: repair["corrected_manifest_identity"][key]
            for key in ("size_bytes", "raw_sha256", "document_digest")
        },
        "pre_repair_journal": {
            key: repair["pre_repair_journal_identity"][key]
            for key in ("raw_sha256", "document_digest", "state", "event_count")
        },
        "replacement_count": 1,
        "quarantine": False,
        "diagnostic_only": True,
        "admissible_for_successor": False,
    }
    if seal_binding != expected:
        raise ContractError("A46.4 lineage-seal repair projection drift")
    return copy.deepcopy(expected)


def successor_manifest_repair_binding(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return the historical G1-to-G2 A46.4 repair projection read-only."""

    repair = contract["predecessor_capsule_lineage"]["one_time_manifest_repair"]
    expected = {
        "authority_amendment": MANIFEST_REPAIR_AUTHORITY,
        "old_manifest_raw_sha256": repair["old_manifest_identity"]["raw_sha256"],
        "old_manifest_document_digest": repair["old_manifest_identity"][
            "document_digest"
        ],
        "corrected_manifest_raw_sha256": repair["corrected_manifest_identity"][
            "raw_sha256"
        ],
        "corrected_manifest_document_digest": repair[
            "corrected_manifest_identity"
        ]["document_digest"],
        "replacement_count": 1,
        "lineage_seal_bound": True,
    }
    return copy.deepcopy(expected)


EMBEDDED_SCHEMA_PATHS = (
    "implementation_binding_schema.effective_lock_json_schema",
    "implementation_binding_schema.external_phase2_audit_artifact_schema",
    "mapping_failure_recovery.successor_failure_oracle.failure_signature_json_schema",
    "mapping_failure_recovery.successor_failure_oracle.attempt_completion_json_schema",
    "mapping_failure_recovery.successor_failure_oracle.failure_batch_json_schema",
    "g2_predecessor_capsule_lineage.manifest_json_schema",
    "g2_predecessor_capsule_lineage.journal_json_schema",
    "g2_predecessor_capsule_lineage.seal_json_schema",
    "predecessor_capsule_lineage.manifest_json_schema",
    "predecessor_capsule_lineage.journal_json_schema",
    "predecessor_capsule_lineage.seal_json_schema",
    "operational_blocker_policy.packet_json_schema",
)


def _embedded_schema_paths(value: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if type(value) is not dict:
        return paths
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if key.endswith("_json_schema") or key == "external_phase2_audit_artifact_schema":
            paths.append(path)
        paths.extend(_embedded_schema_paths(child, path))
    return paths


def _dotted_value(document: Mapping[str, Any], path: str) -> Any:
    value: Any = document
    for part in path.split("."):
        if type(value) is not dict or part not in value:
            raise ContractError(f"embedded schema is absent: {path}")
        value = value[part]
    return value


def validate_embedded_contract_schemas(contract: Mapping[str, Any]) -> None:
    """Meta-validate exactly the twelve frozen Draft-07 schema paths."""

    discovered = _embedded_schema_paths(contract)
    if discovered != list(EMBEDDED_SCHEMA_PATHS):
        raise ContractError("embedded schema dotted path set/order drift")
    schemas = {path: _dotted_value(contract, path) for path in EMBEDDED_SCHEMA_PATHS}
    for name, schema in schemas.items():
        if (
            type(schema) is not dict
            or schema.get("$schema") != "http://json-schema.org/draft-07/schema#"
            or schema.get("type") != "object"
            or schema.get("additionalProperties") is not False
        ):
            raise ContractError(f"embedded {name} schema envelope drift")
        try:
            jsonschema.Draft7Validator.check_schema(schema)
        except jsonschema.SchemaError as error:
            raise ContractError(f"embedded {name} schema is invalid: {error.message}") from error
    manifest_repair_binding(contract)
    successor_manifest_repair_binding(contract)
    if schemas["operational_blocker_policy.packet_json_schema"]["properties"]["packet_id"].get(
        "const"
    ) != "S10R3-A46-OPERATIONAL-BLOCKER":
        raise ContractError("operational-blocker authority token drift")
    expected_checks = list(SUCCESSOR_AUDIT_CHECKS)
    check_properties = schemas[
        "implementation_binding_schema.external_phase2_audit_artifact_schema"
    ]["properties"]["checks"]
    if check_properties.get("required") != expected_checks or list(
        check_properties.get("properties", {})
    ) != expected_checks:
        raise ContractError("external Phase-2 audit check order/set drift")


def validate_phase1_contract(
    document: Mapping[str, Any], *, path: Path | str = DEFAULT_CONTRACT_PATH
) -> None:
    raw_path = Path(path)
    if sha256_file(raw_path) != EXPECTED_CONTRACT_RAW_SHA256:
        raise ContractError("Phase-1 contract raw SHA-256 mismatch")
    if canonical_sha256(dict(document)) != EXPECTED_CONTRACT_CANONICAL_SHA256:
        raise ContractError("Phase-1 contract canonical SHA-256 mismatch")
    if canonical_sha256(oracle_projection(document)) != EXPECTED_ORACLE_PROJECTION_SHA256:
        raise ContractError("scientific/oracle projection SHA-256 mismatch")
    required = {
        "schema_version": EXPECTED_CONTRACT_SCHEMA_VERSION,
        "contract_id": EXPECTED_CONTRACT_ID,
        "checkpoint_id": "S10R3",
        "payload_state": "PREIMPLEMENTATION_SCIENTIFIC_SEAL_PAYLOAD",
        "scientific_outcome": "not_evaluated",
        "edge": None,
    }
    for key, expected in required.items():
        if document.get(key) != expected or type(document.get(key)) is not type(expected):
            raise ContractError(f"Phase-1 contract invariant failed: {key}")
    if document["identity"]["risk_tier"] != "R3":
        raise ContractError("risk tier drift")
    if document["identity"]["base_head"] != PHASE1_SEAL_PARENT:
        raise ContractError("Phase-1 parent drift")
    if document["seal_protocol"]["phase2"]["formal_evidence_allowed_only_after_post_audit"] is not True:
        raise ContractError("formal evidence admission drift")
    if tuple(document["write_boundaries"]["implementation"]) != IMPLEMENTATION_PATHS:
        raise ContractError("implementation whitelist drift")
    if document["bounded_cover_selector"]["k_maximum"] != 20:
        raise ContractError("bounded K maximum drift")
    if document["discovery_schedule"]["total"] != {
        "maximum_chunks": 512,
        "maximum_draws": 262144,
    }:
        raise ContractError("fixed discovery schedule drift")
    fixed = document["implementation_binding_schema"]["fixed_source_identity_map"]
    for identity_id, (identity_type, identity) in SOURCE_IDENTITIES.items():
        if fixed.get(identity_id) != {
            "identity_type": identity_type,
            "identity": identity,
        }:
            raise ContractError(f"fixed source identity drift: {identity_id}")
    validate_embedded_contract_schemas(document)


def _repo_relative(path: Path | str) -> tuple[Path, str]:
    candidate = Path(path)
    absolute = candidate.resolve() if candidate.is_absolute() else (REPOSITORY_ROOT / candidate).resolve()
    try:
        relative = absolute.relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError as error:
        raise ContractError("path escapes repository root") from error
    return absolute, relative


def _git_state(relative: str) -> str:
    git = ["git", "-c", f"safe.directory={REPOSITORY_ROOT}"]
    tracked = subprocess.run(
        [*git, "ls-files", "--error-unmatch", "--", relative],
        cwd=REPOSITORY_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    if tracked:
        dirty = subprocess.run(
            [*git, "diff", "--quiet", "--", relative],
            cwd=REPOSITORY_ROOT,
            check=False,
        ).returncode != 0
        staged = subprocess.run(
            [*git, "diff", "--cached", "--quiet", "--", relative],
            cwd=REPOSITORY_ROOT,
            check=False,
        ).returncode != 0
        return "tracked_modified" if dirty or staged else "tracked_clean"
    ignored = subprocess.run(
        [*git, "check-ignore", "--no-index", "-q", "--", relative],
        cwd=REPOSITORY_ROOT,
        check=False,
    ).returncode == 0
    return "ignored" if ignored else "untracked"


def file_record(path: Path | str) -> dict[str, Any]:
    absolute, relative = _repo_relative(path)
    info = absolute.lstat()
    if not stat.S_ISREG(info.st_mode) or absolute.is_symlink():
        raise ContractError(f"bound path is not one ordinary regular file: {relative}")
    return {
        "path": relative,
        "mode": f"0{stat.S_IMODE(info.st_mode):03o}",
        "size_bytes": info.st_size,
        "sha256": sha256_file(absolute),
        "git_state": _git_state(relative),
    }


def atomic_write_json(
    path: Path | str, document: Mapping[str, Any], *, exclusive: bool = False
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if exclusive and target.exists():
        raise ContractError(f"exclusive output already exists: {target}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json_bytes(dict(document)) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            try:
                os.link(temporary, target)
            except FileExistsError as error:
                raise ContractError(f"exclusive output already exists: {target}") from error
            temporary.unlink()
        else:
            os.replace(temporary, target)
        directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def _validate_raw_document_digest(document: Mapping[str, Any], kind: str) -> None:
    body = copy.deepcopy(dict(document))
    digest = body.pop("document_digest", None)
    if digest != canonical_sha256(body):
        raise ContractError(f"raw {kind} document digest mismatch")


def validate_mapping_failure_signature(
    failure: Mapping[str, Any],
    *,
    config_hashes: Sequence[str] | None = None,
) -> None:
    """Validate the exact allowlisted mapping code-generation signature."""

    schema = load_contract()["mapping_failure_recovery"]["successor_failure_oracle"][
        "failure_signature_json_schema"
    ]
    try:
        jsonschema.Draft7Validator(schema).validate(dict(failure))
    except jsonschema.ValidationError as error:
        raise ContractError(
            f"mapping failure signature schema failed: {error.message}"
        ) from error
    body = copy.deepcopy(dict(failure))
    signature = body.pop("failure_signature")
    if signature != canonical_sha256(body):
        raise ContractError("mapping failure signature digest mismatch")
    if config_hashes is not None:
        hashes = list(config_hashes)
        slot = failure["slot"]
        if slot >= len(hashes) or failure["config_hash"] != hashes[slot]:
            raise ContractError("mapping failure slot/config order binding mismatch")


def _validate_mapping_file_record(
    record: Mapping[str, Any],
    *,
    repository_root: Path,
    require_file: bool,
    attempt_root: Path | None = None,
) -> Path:
    if type(record) is not dict or set(record) != {
        "path",
        "mode",
        "size_bytes",
        "sha256",
    }:
        raise ContractError("mapping raw artifact record shape drift")
    path = _resolve_mapping_relative_path(
        record["path"], repository_root=repository_root, label="worker artifact"
    )
    if attempt_root is not None:
        try:
            relative = path.relative_to(attempt_root)
        except ValueError as error:
            raise ContractError("mapping worker artifact escapes attempt directory") from error
        if not relative.parts:
            raise ContractError("mapping worker artifact is not strictly within attempt")
    if require_file:
        try:
            info = path.lstat()
        except OSError as error:
            raise ContractError("mapping raw artifact is absent") from error
        if (
            path.is_symlink()
            or not stat.S_ISREG(info.st_mode)
            or f"0{stat.S_IMODE(info.st_mode):03o}" != record["mode"]
            or info.st_size != record["size_bytes"]
            or sha256_file(path) != record["sha256"]
        ):
            raise ContractError("mapping raw artifact record drift")
    return path


def _resolve_mapping_relative_path(
    value: Any, *, repository_root: Path, label: str
) -> Path:
    if type(value) is not str or not value or "\\" in value:
        raise ContractError(f"mapping {label} path shape drift")
    parts = value.split("/")
    if value.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        raise ContractError(f"mapping {label} path traversal drift")
    root = repository_root.resolve()
    path = root.joinpath(*parts)
    current = root
    for part in parts:
        current = current / part
        if os.path.lexists(current) and current.is_symlink():
            raise ContractError(f"mapping {label} path contains symlink")
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ContractError(f"mapping {label} path escapes repository") from error
    return resolved


def validate_mapping_worker_completion(
    document: Mapping[str, Any],
    *,
    repository_root: Path = REPOSITORY_ROOT,
    require_files: bool = False,
) -> None:
    """Validate one allowlisted failure-attempt completion and its raw files."""

    schema = load_contract()["mapping_failure_recovery"]["successor_failure_oracle"][
        "attempt_completion_json_schema"
    ]
    try:
        jsonschema.Draft7Validator(schema).validate(dict(document))
    except jsonschema.ValidationError as error:
        raise ContractError(
            f"mapping worker completion schema failed: {error.message}"
        ) from error
    _validate_raw_document_digest(document, "mapping_worker_completion")
    payload = document["payload"]
    attempt = payload["attempt"]
    suffix = f"/attempt-{attempt:02d}"
    if not payload["cwd_path"].endswith(suffix):
        raise ContractError("mapping completion attempt/cwd mismatch")
    attempt_root = _resolve_mapping_relative_path(
        payload["cwd_path"],
        repository_root=repository_root,
        label="attempt cwd",
    )
    if payload["stdout_path"] != f'{payload["cwd_path"]}/worker.stdout' or payload[
        "stderr_path"
    ] != f'{payload["cwd_path"]}/worker.stderr':
        raise ContractError("mapping completion log path mismatch")
    stdout_path = _resolve_mapping_relative_path(
        payload["stdout_path"],
        repository_root=repository_root,
        label="stdout",
    )
    stderr_path = _resolve_mapping_relative_path(
        payload["stderr_path"],
        repository_root=repository_root,
        label="stderr",
    )
    if (
        stdout_path != attempt_root / "worker.stdout"
        or stderr_path != attempt_root / "worker.stderr"
    ):
        raise ContractError("mapping completion resolved log path mismatch")
    if require_files:
        for path, digest_key in (
            (stdout_path, "stdout_sha256"),
            (stderr_path, "stderr_sha256"),
        ):
            try:
                info = path.lstat()
            except OSError as error:
                raise ContractError("mapping completion log is absent") from error
            if (
                path.is_symlink()
                or not stat.S_ISREG(info.st_mode)
                or sha256_file(path) != payload[digest_key]
            ):
                raise ContractError("mapping completion log bytes drift")
    artifact_paths = [item["path"] for item in payload["worker_artifacts"]]
    if artifact_paths != sorted(artifact_paths, key=lambda item: item.encode("utf-8")):
        raise ContractError("mapping worker artifact order drift")
    if len(artifact_paths) != len(set(artifact_paths)):
        raise ContractError("mapping worker artifact path duplication")
    for record in payload["worker_artifacts"]:
        _validate_mapping_file_record(
            record,
            repository_root=repository_root,
            require_file=require_files,
            attempt_root=attempt_root,
        )


def validate_mapping_failure_batch(
    document: Mapping[str, Any],
    *,
    request: Mapping[str, Any] | None = None,
    completions: Sequence[Mapping[str, Any]] | None = None,
    repository_root: Path = REPOSITORY_ROOT,
    require_files: bool = False,
) -> None:
    """Validate the two-attempt raw mapping-failure reproducibility unit."""

    schema = load_contract()["mapping_failure_recovery"]["successor_failure_oracle"][
        "failure_batch_json_schema"
    ]
    try:
        jsonschema.Draft7Validator(schema).validate(dict(document))
    except jsonschema.ValidationError as error:
        raise ContractError(f"mapping failure batch schema failed: {error.message}") from error
    _validate_raw_document_digest(document, "mapping_failure_batch")
    payload = document["payload"]
    if payload["k"] != len(payload["config_hashes"]):
        raise ContractError("mapping failure K/config hash count mismatch")
    validate_mapping_failure_signature(
        payload["failure"], config_hashes=payload["config_hashes"]
    )
    pass_lower = payload["pass_id"].lower()
    expected_root = (
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/"
        f"artifacts/formal-mapping/pass-{pass_lower}"
    )
    if payload["request_path"] != f"{expected_root}/request.json":
        raise ContractError("mapping failure request/pass path mismatch")
    attempts = payload["attempts"]
    if [item["attempt"] for item in attempts] != [1, 2]:
        raise ContractError("mapping failure attempts are not exactly one then two")
    for index, attempt in enumerate(attempts, 1):
        cwd = f"{expected_root}/attempt-{index:02d}"
        if (
            attempt["cwd_path"] != cwd
            or attempt["stdout_path"] != f"{cwd}/worker.stdout"
            or attempt["stderr_path"] != f"{cwd}/worker.stderr"
        ):
            raise ContractError("mapping failure attempt path/order mismatch")
    if request is not None:
        required = {
            "schema_version",
            "pass_id",
            "yaml_path",
            "yaml_sha256",
            "compiler",
            "configs",
            "config_hashes",
            "provenance_source_path",
            "provenance_record_path",
            "provenance_source_sha256",
            "worker_source_sha256",
        }
        if type(request) is not dict or set(request) != required:
            raise ContractError("mapping request unknown or missing field")
        if (
            request["schema_version"] != 1
            or request["pass_id"] != payload["pass_id"]
            or request["compiler"] != payload["worker_binding"]["compiler"]
            or request["config_hashes"] != payload["config_hashes"]
            or request["config_hashes"]
            != [canonical_sha256(item) for item in request["configs"]]
        ):
            raise ContractError("mapping request order/compiler binding drift")
        request_path = repository_root / payload["request_path"]
        if require_files and (
            not request_path.is_file()
            or request_path.is_symlink()
            or sha256_file(request_path) != payload["request_sha256"]
            or strict_load_json(request_path) != dict(request)
        ):
            raise ContractError("mapping request raw bytes drift")
        worker = payload["worker_binding"]
        if worker != {
            "worker_source_sha256": request["worker_source_sha256"],
            "yaml_path": request["yaml_path"],
            "yaml_sha256": request["yaml_sha256"],
            "provenance_source_path": request["provenance_source_path"],
            "provenance_source_sha256": request["provenance_source_sha256"],
            "compiler": request["compiler"],
        }:
            raise ContractError("mapping request worker/source binding drift")
    if completions is not None:
        complete = list(completions)
        if len(complete) != 2:
            raise ContractError("mapping failure requires two completions")
        for index, completion in enumerate(complete):
            validate_mapping_worker_completion(
                completion,
                repository_root=repository_root,
                require_files=require_files,
            )
            candidate = completion["payload"]
            expected = attempts[index]
            projection = {
                "completion_digest": completion["document_digest"],
                **{
                    key: candidate[key]
                    for key in (
                        "attempt",
                        "returncode",
                        "cwd_path",
                        "stdout_path",
                        "stdout_sha256",
                        "stderr_path",
                        "stderr_sha256",
                        "worker_artifacts",
                    )
                },
            }
            if expected != projection:
                raise ContractError("mapping failure completion projection drift")


def validate_document(document: Mapping[str, Any], kind: str) -> None:
    schema = strict_load_json(DEFAULT_SCHEMA_PATH)
    if kind not in schema["properties"]["document_kind"]["enum"]:
        raise ContractError(f"unknown S10R3 document kind: {kind}")
    if kind == "effective_lock":
        validate_effective_lock(document, require_current_files=False)
        return
    if kind == "s10r3_predecessor_capsule_manifest":
        validate_capsule_manifest(document, require_frozen=True)
        return
    if kind == "s10r3_predecessor_transition_journal":
        validate_transition_journal(document, production_identity=True)
        return
    if kind == "s10r3_predecessor_lineage_seal":
        validate_lineage_seal(document, require_frozen=True)
        return
    contract = load_contract()
    if kind == "external_phase2_audit":
        embedded = contract["implementation_binding_schema"][
            "external_phase2_audit_artifact_schema"
        ]
        try:
            jsonschema.Draft7Validator(embedded).validate(dict(document))
        except jsonschema.ValidationError as error:
            raise ContractError(
                f"external Phase-2 audit schema failed: {error.message}"
            ) from error
        validate_successor_audit_checks(list(document["checks"]))
        return
    if kind == "operational_blocker":
        embedded = contract["operational_blocker_policy"]["packet_json_schema"]
        try:
            jsonschema.Draft7Validator(embedded).validate(dict(document))
        except jsonschema.ValidationError as error:
            raise ContractError(
                f"operational blocker schema failed: {error.message}"
            ) from error
        return
    if kind == "mapping_worker_completion":
        validate_mapping_worker_completion(document)
        return
    if kind == "mapping_failure_batch":
        validate_mapping_failure_batch(document)
        return
    envelope = {"document_kind": kind, "document": dict(document)}
    try:
        jsonschema.Draft7Validator(schema).validate(envelope)
    except jsonschema.ValidationError as error:
        raise ContractError(f"S10R3 schema validation failed: {error.message}") from error


def _command_templates() -> list[dict[str, Any]]:
    runner = (
        "study_docs/research/ductile-origami-warmstart/protocol/v1/"
        "run_s10r3_entry.py"
    )
    lock = (
        "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/"
        "s10r3-stage1-bounded-cover-entry-lock.json"
    )
    python = "/opt/venv/bin/python3"
    base = [python, runner]
    commands = {
        "validate_contract": [*base, "validate-contract"],
        "build_registry": [
            *base,
            "prepare-prelabel",
            "--build-root",
            "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/prelabel-build",
            "--fixture-root",
            "agent_run/260730-ductile-factorized-guidance-s10r3-restart/artifacts/prelabel-fixtures",
            "--registry",
            REGISTRY_PATH,
            "--size-registry",
            SIZE_REGISTRY_PATH,
        ],
        "offline_tests": [
            "/opt/venv/bin/pytest",
            "-q",
            "projects/hipblaslt/tensilelite/Tensile/Tests/unit/"
            "test_ductile_s10r3_entry.py",
        ],
        "support_discovery": [*base, "support-discovery", "--lock", lock],
        "support_classification": [*base, "support-classification", "--lock", lock],
        "bounded_cover_selection": [*base, "select-bounded-cover", "--lock", lock],
        "mapping_pass_a": [*base, "mapping", "--pass-id", "A", "--lock", lock],
        "mapping_pass_b": [*base, "mapping", "--pass-id", "B", "--lock", lock],
        "native_conformance": [*base, "native-conformance", "--lock", lock],
        "gpu_environment": [*base, "gpu-environment", "--lock", lock],
        "correctness": [*base, "correctness", "--lock", lock],
        "noise": [*base, "noise", "--lock", lock],
        "decision": [*base, "decision", "--lock", lock],
        "reproduction": [
            *base,
            "reproduction",
            "--lock",
            lock,
            "--output",
            "agent_run/260730-ductile-factorized-guidance-s10r3-restart/"
            "artifacts/reproduction/s10r3-independent-result.json",
        ],
    }
    return [
        {
            "id": command_id,
            "cwd": "/src/rocm-libraries",
            "exact_argv": argv,
            "environment": copy.deepcopy(COMMAND_ENVIRONMENT),
        }
        for command_id, argv in commands.items()
    ]


def _tool_record(tool_id: str, path: str, version_argv: Sequence[str]) -> dict[str, Any]:
    completed = subprocess.run(
        list(version_argv),
        cwd=REPOSITORY_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={
            "LC_ALL": "C",
            "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
            "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
        },
    )
    if completed.returncode:
        raise ContractError(f"tool version command failed for {tool_id}")
    tool = Path(path)
    if not tool.is_file():
        raise ContractError(f"tool path absent for {tool_id}")
    return {
        "id": tool_id,
        "path": path,
        "version": completed.stdout.rstrip("\n"),
        "sha256": sha256_file(tool),
    }


def _absence_projection() -> dict[str, Any]:
    records = []
    for relative in FORMAL_OUTCOME_PATHS:
        if (REPOSITORY_ROOT / relative).exists():
            raise ContractError(f"formal outcome path already exists: {relative}")
        records.append({"path": relative, "exists": False})
    scope_records = []
    for relative in FORMAL_SCOPES:
        scope = REPOSITORY_ROOT / relative
        descendants = list(scope.rglob("*")) if scope.exists() else []
        if scope.exists() or descendants:
            raise ContractError(f"formal artifact scope is not absent: {relative}")
        scope_records.append({"path": relative, "exists": False, "descendant_count": 0})
    blocker = (
        REPOSITORY_ROOT
        / "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/"
        "s10r3-operational-blocker.json"
    )
    if blocker.exists():
        packet = strict_load_json(blocker)
        contract = load_contract()
        try:
            jsonschema.Draft7Validator(
                contract["operational_blocker_policy"]["packet_json_schema"]
            ).validate(packet)
        except jsonschema.ValidationError as error:
            raise ContractError("operational blocker packet is invalid") from error
        if packet["state"] != "resumed" or packet["events"][-1]["event_type"] != "resumed":
            raise ContractError("effective lock requires restored operational projection")
        lineage = {
            "state": "resumed",
            "packet_present": True,
            "packet_file": file_record(blocker),
            "packet_schema_valid": True,
            "last_event_type": "resumed",
            "restored_projection_verified": True,
        }
    else:
        lineage = {"state": "never_blocked", "packet_present": False}
    return {
        "checked_path_set": list(FORMAL_OUTCOME_PATHS),
        "checked_scope_set": list(FORMAL_SCOPES),
        "records": records,
        "scope_records": scope_records,
        "operational_lineage": lineage,
        "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def _load_freeze(path: Path | str, *, plan_id: str) -> dict[str, Any]:
    record = strict_load_json(path)
    if record.get("checkpoint_id") != "S10R3" or record.get("plan_id") != plan_id:
        raise ContractError(f"{plan_id} freeze identity mismatch")
    plan_path = REPOSITORY_ROOT / str(record["path"])
    if (
        not plan_path.is_file()
        or sha256_file(plan_path) != record.get("sha256")
        or plan_path.stat().st_size != record.get("size_bytes")
        or record.get("frozen") is not True
    ):
        raise ContractError(f"{plan_id} frozen bytes mismatch")
    return record


def _current_phase1_plan_binding() -> dict[str, Any]:
    return {
        "commit_oid": PHASE1_SEAL_COMMIT,
        "contract_path": DEFAULT_CONTRACT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "contract_raw_sha256": EXPECTED_CONTRACT_RAW_SHA256,
        "contract_canonical_sha256": EXPECTED_CONTRACT_CANONICAL_SHA256,
        "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
        "post_commit_audit": "AUDIT_PASS_POSTCOMMIT_A46_5",
    }


def _load_current_freeze(
    path: Path | str,
    *,
    plan_id: str,
    revision: int,
    plan_path: str,
    plan_sha256: str,
    plan_size_bytes: int,
    freeze_sha256: str,
) -> dict[str, Any]:
    if sha256_file(path) != freeze_sha256:
        raise ContractError(f"current {plan_id} freeze-record SHA-256 mismatch")
    record = _load_freeze(path, plan_id=plan_id)
    current = {
        "path": plan_path,
        "sha256": plan_sha256,
        "size_bytes": plan_size_bytes,
        "revision": revision,
    }
    if {key: record.get(key) for key in current} != current:
        raise ContractError(f"current {plan_id} freeze binding mismatch")
    phase1 = record.get("phase1_seal")
    if type(phase1) is not dict or phase1 != _current_phase1_plan_binding():
        raise ContractError(f"current {plan_id} Phase-1 binding mismatch")
    return record


def _load_current_plan_a_freeze(path: Path | str) -> dict[str, Any]:
    try:
        return _load_current_freeze(
            path,
            plan_id=PLAN_A_FREEZE_ID,
            revision=EXPECTED_PLAN_A_REVISION,
            plan_path=EXPECTED_PLAN_A_PATH,
            plan_sha256=EXPECTED_PLAN_A_SHA256,
            plan_size_bytes=EXPECTED_PLAN_A_SIZE_BYTES,
            freeze_sha256=EXPECTED_PLAN_A_FREEZE_SHA256,
        )
    except ContractError as error:
        raise ContractError(str(error).replace(PLAN_A_FREEZE_ID, "Plan-A")) from error


def _load_current_plan_b_freeze(path: Path | str) -> dict[str, Any]:
    if sha256_file(path) != EXPECTED_PLAN_B_FREEZE_SHA256:
        raise ContractError("current Plan-B freeze-record SHA-256 mismatch")
    record = strict_load_json(path)
    expected_fields = {
        "schema_version": 1,
        "checkpoint_id": "S10R3",
        "plan_id": PLAN_B_FREEZE_ID,
        "revision": EXPECTED_PLAN_B_REVISION,
        "plan_kind": "goal_oracle",
        "path": EXPECTED_PLAN_B_PATH,
        "sha256": EXPECTED_PLAN_B_SHA256,
        "mode": "0664",
        "authored_by": "/root",
        "phase1_seal_commit": PHASE1_SEAL_COMMIT,
        "frozen_contract_raw_sha256": EXPECTED_CONTRACT_RAW_SHA256,
        "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
        "phase1_post_commit_verdict": "AUDIT_PASS_POSTCOMMIT_A46_5",
        "repair_count_is_stop_gate": False,
        "frozen": True,
        "mutable": False,
    }
    for key, expected in expected_fields.items():
        actual = record.get(key)
        if type(actual) is not type(expected) or actual != expected:
            raise ContractError("current Plan-B top-level freeze binding mismatch")
    if type(record.get("size_bytes")) is not int or record["size_bytes"] < 1:
        raise ContractError("current Plan-B size binding mismatch")
    expected_visible_to = ["main", "adversarial_auditor", "fresh_verifier"]
    expected_forbidden_to = ["fresh_implementer"]
    if (
        type(record.get("visible_to")) is not list
        or record.get("visible_to") != expected_visible_to
        or type(record.get("forbidden_to")) is not list
        or record.get("forbidden_to") != expected_forbidden_to
        or "role_visibility" in record
    ):
        raise ContractError("current Plan-B role visibility mismatch")
    plan_path = REPOSITORY_ROOT / EXPECTED_PLAN_B_PATH
    if (
        not plan_path.is_file()
        or stat.S_IMODE(plan_path.stat().st_mode) != 0o664
        or plan_path.stat().st_size != record["size_bytes"]
        or sha256_file(plan_path) != EXPECTED_PLAN_B_SHA256
    ):
        raise ContractError("current Plan-B frozen plan bytes mismatch")
    return record


def _governance_binding(repair_rounds_used: int) -> dict[str, Any]:
    if type(repair_rounds_used) is not int or repair_rounds_used < 9:
        raise ContractError("repair_rounds_used must be an integer at least 9")
    return {
        "risk_tier": "R3",
        "main_role": "/root",
        "auditor_role": "/root/s10r3_a46_3_reviewer_a",
        "a46_5_reviewer_a_role": "/root/s10r3_a46_5_reviewer_a",
        "implementer_role": "/root/s10r3_fresh_implementer",
        "verifier_role": "/root/s10r3_fresh_verifier",
        "repair_rounds_used": repair_rounds_used,
        "repair_rounds_stop_cap": None,
        "repair_count_is_stop_gate": False,
        "fresh_role_threads_used": 13,
        "fresh_role_threads_maximum": 13,
    }


def _git_commit_and_blob(path: Path | str) -> tuple[str, str]:
    _, relative = _repo_relative(path)
    commit = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={REPOSITORY_ROOT}",
            "log",
            "-1",
            "--format=%H",
            "--",
            relative,
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    if len(commit) != 40:
        raise ContractError("tracked lineage seal has no containing commit")
    blob = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={REPOSITORY_ROOT}",
            "rev-parse",
            f"{commit}:{relative}",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    committed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={REPOSITORY_ROOT}",
            "show",
            f"{commit}:{relative}",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    if committed != (REPOSITORY_ROOT / relative).read_bytes():
        raise ContractError("tracked lineage seal differs from committed bytes")
    return commit, blob


def _current_predecessor_lineage_binding(
    contract: Mapping[str, Any], admission_identity: Mapping[str, Any]
) -> dict[str, Any]:
    lineage = contract[G2_LINEAGE_SELECTOR]
    selected = g2_lineage_spec(selector=G2_LINEAGE_SELECTOR, contract=contract)
    paths = lineage["paths"]
    final_root = REPOSITORY_ROOT / paths["final_capsule"]
    manifest_path = final_root / paths["capsule_manifest_name"]
    journal_path = REPOSITORY_ROOT / paths["journal"]
    seal_path = REPOSITORY_ROOT / paths["durable_lineage_seal"]
    manifest = strict_load_json(manifest_path)
    roots = {
        item.component_id: REPOSITORY_ROOT / item.final_root
        for item in selected.components
    }
    if os.path.lexists(REPOSITORY_ROOT / selected.staging_capsule) or any(
        os.path.lexists(REPOSITORY_ROOT / item.source_root)
        for item in selected.components
    ):
        raise ContractError("G3 admission requires all G2 canonical sources absent")
    validate_g2_capsule_manifest(
        manifest,
        selector=G2_LINEAGE_SELECTOR,
        spec=selected,
        require_frozen=True,
        component_roots=roots,
    )
    journal = strict_load_json(journal_path)
    validate_g2_transition_journal(
        journal,
        selector=G2_LINEAGE_SELECTOR,
        spec=selected,
        require_frozen=True,
    )
    if journal["state"] != "FINALIZED":
        raise ContractError("successor requires terminal finalized journal")
    if journal["admission_lock_identity_digest"] != admission_identity[
        "identity_digest"
    ]:
        raise ContractError("successor predecessor admission identity mismatch")
    seal = strict_load_json(seal_path)
    validate_g2_lineage_seal(
        seal,
        selector=G2_LINEAGE_SELECTOR,
        spec=selected,
        manifest=manifest,
        journal=journal,
        component_roots=roots,
        require_frozen=True,
        require_files=True,
    )
    if seal["authority_contract"] != {
        "path": DEFAULT_CONTRACT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "commit": PHASE1_SEAL_COMMIT,
        "raw_sha256": EXPECTED_CONTRACT_RAW_SHA256,
        "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
    }:
        raise ContractError("lineage seal A46.5 authority binding mismatch")
    seal_commit, seal_blob = _git_commit_and_blob(seal_path)
    return {
        "predecessor_generation_id": PREDECESSOR_GENERATION_ID,
        "predecessor_lock": {
            "commit": PREDECESSOR_EFFECTIVE_LOCK_COMMIT,
            "raw_sha256": selected.predecessor_lock_raw_sha256,
            "canonical_self_sha256": selected.predecessor_lock_canonical_self_sha256,
        },
        "transition_id": TRANSITION_ID,
        "final_capsule_root": paths["final_capsule"],
        "capsule_manifest": file_record(manifest_path),
        "terminal_journal": file_record(journal_path),
        "admission_lock_identity_digest": admission_identity["identity_digest"],
        "role_provenance": {
            "fresh_role_threads_used": 13,
            "fresh_role_threads_maximum": 13,
            "new_fresh_role_creation": "forbidden",
            "a46_5_reviewers": [
                "/root/s10r3_a46_5_reviewer_a",
                "/root/s10r3_a46_3_reviewer_a",
            ],
            "implementer_as_reviewer": "forbidden",
        },
        "durable_lineage_seal": {
            "file": file_record(seal_path),
            "commit": seal_commit,
            "blob": seal_blob,
        },
        "diagnostic_only": True,
        "admissible_for_current_execution": False,
        "empirical_reuse": "forbidden",
        "cumulative_resource_lineage_reset": "forbidden",
    }


def _successor_entry_preconditions() -> dict[str, Any]:
    return {
        "transition_state": "FINALIZED",
        "capsule_recomputed": True,
        "admission_lock_identity_reverified": True,
        "seal_committed_and_post_audited": True,
        "canonical_predecessor_lock_absent_before_build": True,
        "successor_lock_destination_absent_before_build": True,
        "fresh_execution_starts_at": "cpu_support_discovery_global_draw_zero",
        "predecessor_k_admissible": False,
        "cumulative_resource_lineage_recomputed": True,
    }


def validate_successor_audit_checks(checks: Sequence[str]) -> None:
    if type(checks) is not list or checks != list(SUCCESSOR_AUDIT_CHECKS):
        raise ContractError("successor lock requires the exact ordered nine checks")


def _production_admitted(function):
    """Hold the stable shared admission inode for the complete successor build."""

    def wrapped(*args, **kwargs):
        admission_path = REPOSITORY_ROOT / PRODUCTION_ADMISSION_LOCK_PATH
        with stable_admission_lock(
            admission_path, allow_production=True
        ) as (descriptor, identity):
            kwargs["_admission_identity"] = identity
            result = function(*args, **kwargs)
            admission_lock_identity(
                admission_path,
                descriptor,
                allow_production=True,
                expected_identity=identity,
            )
            return result

    return wrapped


@_production_admitted
def build_effective_lock(
    *,
    plan_a_freeze: Path | str,
    plan_b_freeze: Path | str,
    repair_rounds_used: int,
    resource_lineage_records: Sequence[Mapping[str, Any]],
    output: Path | str = DEFAULT_LOCK_PATH,
    _admission_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = load_contract()
    output_path, output_relative = _repo_relative(output)
    if output_relative != DEFAULT_LOCK_PATH.relative_to(REPOSITORY_ROOT).as_posix():
        raise ContractError("successor lock output is not the canonical path")
    if os.path.lexists(output_path):
        raise ContractError("successor lock destination exists before build")
    if _admission_identity is None:
        raise ContractError("successor build is outside stable admission")
    predecessor_binding = _current_predecessor_lineage_binding(
        contract, _admission_identity
    )
    plan_a = _load_current_plan_a_freeze(plan_a_freeze)
    plan_b = _load_current_plan_b_freeze(plan_b_freeze)
    implementation_files = [file_record(path) for path in IMPLEMENTATION_PATHS]
    native_binary = file_record(NATIVE_BINARY_PATH)
    inputs = [
        {"id": identity_id, "identity_type": value[0], "identity": value[1]}
        for identity_id, value in SOURCE_IDENTITIES.items()
    ]
    fixtures = [
        {"id": "candidate_atom_registry", "file": file_record(REGISTRY_PATH)},
        {"id": "size_registry", "file": file_record(SIZE_REGISTRY_PATH)},
        {"id": "sentinel_fixture", "file": file_record(SENTINEL_FIXTURE_PATH)},
    ]
    absence = _absence_projection()
    boundaries = contract["write_boundaries"]
    document: dict[str, Any] = {
        "schema_version": 2,
        "lock_id": SUCCESSOR_LOCK_ID,
        "generation_id": SUCCESSOR_GENERATION_ID,
        "checkpoint_id": "S10R3",
        "payload_state": "EFFECTIVE_EXECUTION_BINDING",
        "lifecycle": {
            "lock_state": "effective",
            "execution_status": "ready",
            "checkpoint_state": "LOCKED_READY",
            "scientific_outcome": "not_evaluated",
            "edge": None,
            "formal_evidence_allowed": False,
        },
        "phase1": {
            "seal_commit_oid": PHASE1_SEAL_COMMIT,
            "contract_path": str(
                DEFAULT_CONTRACT_PATH.relative_to(REPOSITORY_ROOT).as_posix()
            ),
            "contract_raw_sha256": EXPECTED_CONTRACT_RAW_SHA256,
            "contract_canonical_sha256": EXPECTED_CONTRACT_CANONICAL_SHA256,
            "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
        },
        "plans": {
            "plan_b": {
                "path": plan_b["path"],
                "sha256": plan_b["sha256"],
                "size_bytes": plan_b["size_bytes"],
                "frozen": True,
            },
            "plan_a": {
                "path": plan_a["path"],
                "sha256": plan_a["sha256"],
                "size_bytes": plan_a["size_bytes"],
                "revision": plan_a["revision"],
            },
        },
        "implementation_binding": {
            "status": "complete",
            "required_path_set": list(IMPLEMENTATION_PATHS),
            "files": implementation_files,
        },
        "runtime_binding": {
            "native_binary": native_binary,
            "toolchain": [
                _tool_record("python", "/opt/venv/bin/python3", ["/opt/venv/bin/python3", "--version"]),
                _tool_record("pytest", "/opt/venv/bin/pytest", ["/opt/venv/bin/pytest", "--version"]),
                _tool_record(
                    "cxx_compiler",
                    "/opt/rocm/bin/amdclang++",
                    ["/opt/rocm/bin/amdclang++", "--version"],
                ),
                _tool_record(
                    "rocm_toolchain",
                    "/opt/rocm/bin/hipcc",
                    ["/opt/rocm/bin/hipcc", "--version"],
                ),
            ],
            "command_templates": _command_templates(),
            "final_k_binary_rule": {
                "prelabel_instance_required": False,
                "generation_admission": (
                    "only_after_locked_exact_K_and_before_corresponding_correctness_cell"
                ),
                "lineage_key_fields": [
                    "effective_lock_sha256",
                    "config_hash",
                    "size_id",
                    "toolchain_sha256",
                    "exact_argv_sha256",
                ],
                "replacement": False,
            },
        },
        "input_binding": {
            "required_identity_ids": list(SOURCE_IDENTITIES),
            "source_and_yaml_identities": inputs,
            "required_registry_fixture_ids": [
                "candidate_atom_registry",
                "size_registry",
                "sentinel_fixture",
            ],
            "registry_and_fixtures": fixtures,
        },
        "governance_binding": _governance_binding(repair_rounds_used),
        "boundary_binding": {
            "implementation_boundary_sha256": canonical_sha256(
                boundaries["implementation"]
            ),
            "execution_artifact_boundary_sha256": canonical_sha256(
                boundaries["execution_artifacts"]
            ),
            "delivery_boundary_sha256": canonical_sha256(boundaries["delivery"]),
            "protected_unrelated_boundary_sha256": canonical_sha256(
                boundaries["protected_unrelated_paths"]
            ),
            "unknown_write_path": "forbidden",
        },
        "resource_lineage_binding": build_resource_lineage_binding(
            resource_lineage_records
        ),
        "outcome_absence": absence,
        "predecessor_lineage_binding": predecessor_binding,
        "successor_entry_preconditions": _successor_entry_preconditions(),
        "audit_request": {
            "requested_verdict": "AUDIT_PASS_POST_BINDING",
            "auditor_role": "/root/s10r3_a46_3_reviewer_a",
            "audit_artifact_path": (
                "agent_run/260730-ductile-factorized-guidance-s10r3-restart/"
                "gates/s10r3/phase2-audit-verdict.json"
            ),
            "outcome_absence_projection_sha256": canonical_sha256(absence),
            "audit_checks": list(SUCCESSOR_AUDIT_CHECKS),
        },
        "self_identity": {
            "algorithm": "sha256",
            "canonicalization": (
                "utf8_sorted_keys_compact_separators_no_nan_exact_json_types"
            ),
            "hash_scope": (
                "entire_lock_with_self_identity_canonical_self_sha256_replaced_by_64_ascii_zeroes"
            ),
            "placeholder": SELF_HASH_PLACEHOLDER,
            "canonical_self_sha256": SELF_HASH_PLACEHOLDER,
            "phase2_seal_commit_oid_embedded": False,
        },
    }
    document["self_identity"]["canonical_self_sha256"] = canonical_sha256(document)
    validate_effective_lock(document, require_current_files=True)
    atomic_write_json(output, document, exclusive=True)
    return document


def _assert_exact_set(
    actual: Sequence[str], expected: Sequence[str], *, field: str
) -> None:
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise ContractError(f"{field} exact set invariant failed")


def validate_effective_lock(
    document: Mapping[str, Any], *, require_current_files: bool = True
) -> None:
    contract = load_contract()
    schema = contract["implementation_binding_schema"]["effective_lock_json_schema"]
    try:
        jsonschema.Draft7Validator(schema).validate(dict(document))
    except jsonschema.ValidationError as error:
        raise ContractError(f"effective lock schema failed: {error.message}") from error
    if document["schema_version"] != 2 or document["lock_id"] != SUCCESSOR_LOCK_ID:
        raise ContractError("successor lock schema/identity mismatch")
    if document["generation_id"] != SUCCESSOR_GENERATION_ID:
        raise ContractError("successor lock generation mismatch")
    validate_successor_audit_checks(document["audit_request"]["audit_checks"])
    validate_resource_lineage_binding(document["resource_lineage_binding"])
    if document["successor_entry_preconditions"] != _successor_entry_preconditions():
        raise ContractError("successor entry preconditions mismatch")
    predecessor = document["predecessor_lineage_binding"]
    expected_role_provenance = {
        "fresh_role_threads_used": 13,
        "fresh_role_threads_maximum": 13,
        "new_fresh_role_creation": "forbidden",
        "a46_5_reviewers": [
            "/root/s10r3_a46_5_reviewer_a",
            "/root/s10r3_a46_3_reviewer_a",
        ],
        "implementer_as_reviewer": "forbidden",
    }
    if (
        predecessor["predecessor_generation_id"] != PREDECESSOR_GENERATION_ID
        or predecessor.get("role_provenance") != expected_role_provenance
        or predecessor["diagnostic_only"] is not True
        or predecessor["admissible_for_current_execution"] is not False
        or predecessor["empirical_reuse"] != "forbidden"
        or predecessor["cumulative_resource_lineage_reset"] != "forbidden"
    ):
        raise ContractError("predecessor lineage was admitted to successor execution")
    binding = document["implementation_binding"]
    _assert_exact_set(binding["required_path_set"], IMPLEMENTATION_PATHS, field="implementation paths")
    _assert_exact_set(
        [item["path"] for item in binding["files"]],
        IMPLEMENTATION_PATHS,
        field="implementation file records",
    )
    _assert_exact_set(
        [item["id"] for item in document["input_binding"]["source_and_yaml_identities"]],
        list(SOURCE_IDENTITIES),
        field="source identities",
    )
    by_id = {
        item["id"]: (item["identity_type"], item["identity"])
        for item in document["input_binding"]["source_and_yaml_identities"]
    }
    if by_id != SOURCE_IDENTITIES:
        raise ContractError("effective lock fixed source value mismatch")
    _assert_exact_set(
        [item["id"] for item in document["runtime_binding"]["command_templates"]],
        [item["id"] for item in _command_templates()],
        field="command templates",
    )
    if document["runtime_binding"]["command_templates"] != _command_templates():
        raise ContractError("effective lock command template mismatch")
    _assert_exact_set(
        [item["id"] for item in document["runtime_binding"]["toolchain"]],
        ["python", "pytest", "cxx_compiler", "rocm_toolchain"],
        field="toolchain",
    )
    outcome = document["outcome_absence"]
    if outcome["checked_path_set"] != list(FORMAL_OUTCOME_PATHS):
        raise ContractError("outcome absence path order/set mismatch")
    if outcome["checked_scope_set"] != list(FORMAL_SCOPES):
        raise ContractError("outcome absence scope order/set mismatch")
    _assert_exact_set(
        [item["path"] for item in outcome["records"]],
        FORMAL_OUTCOME_PATHS,
        field="outcome absence records",
    )
    _assert_exact_set(
        [item["path"] for item in outcome["scope_records"]],
        FORMAL_SCOPES,
        field="formal scope absence records",
    )
    if canonical_sha256(outcome) != document["audit_request"][
        "outcome_absence_projection_sha256"
    ]:
        raise ContractError("outcome absence projection digest mismatch")
    boundaries = contract["write_boundaries"]
    expected_boundaries = {
        "implementation_boundary_sha256": canonical_sha256(boundaries["implementation"]),
        "execution_artifact_boundary_sha256": canonical_sha256(
            boundaries["execution_artifacts"]
        ),
        "delivery_boundary_sha256": canonical_sha256(boundaries["delivery"]),
        "protected_unrelated_boundary_sha256": canonical_sha256(
            boundaries["protected_unrelated_paths"]
        ),
        "unknown_write_path": "forbidden",
    }
    if document["boundary_binding"] != expected_boundaries:
        raise ContractError("effective lock boundary digest mismatch")
    if document["phase1"] != {
        "seal_commit_oid": PHASE1_SEAL_COMMIT,
        "contract_path": DEFAULT_CONTRACT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "contract_raw_sha256": EXPECTED_CONTRACT_RAW_SHA256,
        "contract_canonical_sha256": EXPECTED_CONTRACT_CANONICAL_SHA256,
        "scientific_oracle_projection_sha256": EXPECTED_ORACLE_PROJECTION_SHA256,
    }:
        raise ContractError("Phase-1 lock binding mismatch")
    expected_plan_a = {
        "path": EXPECTED_PLAN_A_PATH,
        "sha256": EXPECTED_PLAN_A_SHA256,
        "size_bytes": EXPECTED_PLAN_A_SIZE_BYTES,
        "revision": EXPECTED_PLAN_A_REVISION,
    }
    if document["plans"]["plan_a"] != expected_plan_a:
        raise ContractError("current Plan-A lock binding mismatch")
    expected_plan_b = {
        "path": EXPECTED_PLAN_B_PATH,
        "sha256": EXPECTED_PLAN_B_SHA256,
        "size_bytes": document["plans"]["plan_b"].get("size_bytes"),
        "frozen": True,
    }
    if (
        type(expected_plan_b["size_bytes"]) is not int
        or expected_plan_b["size_bytes"] < 1
        or document["plans"]["plan_b"] != expected_plan_b
    ):
        raise ContractError("current Plan-B lock binding mismatch")
    governance = document["governance_binding"]
    if (
        type(governance["repair_rounds_used"]) is not int
        or governance["repair_rounds_used"] < 9
        or governance["repair_rounds_stop_cap"] is not None
        or governance["repair_count_is_stop_gate"] is not False
        or governance["auditor_role"] != "/root/s10r3_a46_3_reviewer_a"
        or governance.get("a46_5_reviewer_a_role")
        != "/root/s10r3_a46_5_reviewer_a"
        or governance["fresh_role_threads_used"] != 13
        or governance["fresh_role_threads_maximum"] != 13
        or "repair_rounds_maximum" in governance
    ):
        raise ContractError("repair provenance governance mismatch")
    placeholder_copy = copy.deepcopy(dict(document))
    placeholder_copy["self_identity"]["canonical_self_sha256"] = SELF_HASH_PLACEHOLDER
    if canonical_sha256(placeholder_copy) != document["self_identity"]["canonical_self_sha256"]:
        raise ContractError("effective lock canonical self hash mismatch")
    if require_current_files:
        file_records = list(binding["files"])
        file_records.append(document["runtime_binding"]["native_binary"])
        for item in document["input_binding"]["registry_and_fixtures"]:
            file_records.append(item["file"])
        for record in file_records:
            if file_record(record["path"]) != record:
                raise ContractError(f"bound file record drift: {record['path']}")
        for key in ("capsule_manifest", "terminal_journal"):
            record = predecessor[key]
            if file_record(record["path"]) != record:
                raise ContractError(f"predecessor lineage file drift: {record['path']}")
        seal_binding = predecessor["durable_lineage_seal"]
        if file_record(seal_binding["file"]["path"]) != seal_binding["file"]:
            raise ContractError("durable lineage seal file drift")
        commit, blob = _git_commit_and_blob(seal_binding["file"]["path"])
        if (commit, blob) != (seal_binding["commit"], seal_binding["blob"]):
            raise ContractError("durable lineage seal tracked identity drift")
        manifest = strict_load_json(predecessor["capsule_manifest"]["path"])
        journal = strict_load_json(predecessor["terminal_journal"]["path"])
        seal = strict_load_json(seal_binding["file"]["path"])
        selected = g2_lineage_spec(selector=G2_LINEAGE_SELECTOR, contract=contract)
        roots = {
            item.component_id: REPOSITORY_ROOT / item.final_root
            for item in selected.components
        }
        validate_g2_lineage_seal(
            seal,
            selector=G2_LINEAGE_SELECTOR,
            spec=selected,
            manifest=manifest,
            journal=journal,
            component_roots=roots,
            require_frozen=True,
            require_files=True,
        )
        admission_path = REPOSITORY_ROOT / PRODUCTION_ADMISSION_LOCK_PATH
        with stable_admission_lock(
            admission_path, allow_production=True
        ) as (_, identity):
            if identity["identity_digest"] != predecessor[
                "admission_lock_identity_digest"
            ]:
                raise ContractError("successor admission identity digest drift")


def verify_committed_effective_lock(
    path: Path | str = DEFAULT_LOCK_PATH,
) -> str:
    admission_path = REPOSITORY_ROOT / PRODUCTION_ADMISSION_LOCK_PATH
    with stable_admission_lock(
        admission_path, allow_production=True
    ) as (descriptor, identity):
        result = _verify_committed_effective_lock_under_admission(path)
        admission_lock_identity(
            admission_path,
            descriptor,
            allow_production=True,
            expected_identity=identity,
        )
        return result


def _verify_committed_effective_lock_under_admission(
    path: Path | str = DEFAULT_LOCK_PATH,
) -> str:
    absolute, relative = _repo_relative(path)
    document = strict_load_json(absolute)
    validate_effective_lock(document, require_current_files=True)
    completed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={REPOSITORY_ROOT}",
            "show",
            f"HEAD:{relative}",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode or completed.stdout != absolute.read_bytes():
        raise ContractError("effective lock exact bytes are not committed at HEAD")
    audit_path = REPOSITORY_ROOT / (
        "agent_run/260730-ductile-factorized-guidance-s10r3-restart/"
        "gates/s10r3/phase2-post-commit-audit-verdict.json"
    )
    audit = strict_load_json(audit_path)
    if (
        audit.get("verdict") != "AUDIT_PASS_POST_BINDING"
        and audit.get("verdict") != "AUDIT_PASS_POST_COMMIT"
    ):
        raise ContractError("required Phase-2 post-commit audit is absent")
    if audit.get("lock_path") != relative:
        raise ContractError("post-commit audit lock path mismatch")
    if audit.get("lock_raw_sha256") != sha256_file(absolute):
        raise ContractError("post-commit audit lock hash mismatch")
    return "LOCKED_READY"
