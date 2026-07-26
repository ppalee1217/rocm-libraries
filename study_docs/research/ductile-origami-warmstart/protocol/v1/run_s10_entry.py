#!/usr/bin/env python3
# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Fail-closed S10 Stage-1 entry-gate runner.

The runner deliberately separates pre-lock construction evidence from
outcome-bearing mapping, GPU smoke, noise, and decision evidence. H4 is a
fresh, live, unreserved availability gate inside exact ``perlee``; it makes no
reservation, exclusivity, future-availability, or five-day-budget claim.
"""

from __future__ import annotations

import argparse
import ast
import copy
import csv
import datetime as dt
import hashlib
import itertools
import json
import math
import os
import posixpath
import re
import random
import shlex
import stat
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml
import numpy as np

from Tensile.ductile.evidence import (
    EvidenceValidationError,
    atomic_write_bytes,
    atomic_write_json,
    canonical_json_bytes,
    canonical_sha256,
    plain_value,
    sha256_file,
    strict_load_json,
    strict_load_yaml,
    validate_schema_document,
    write_effective_lock,
)


ROOT = Path(__file__).resolve().parents[5]
PROTOCOL = Path(__file__).resolve().parent
S10_RUN_ROOT = (
    ROOT
    / "agent_run/260725-ductile-factorized-guidance-s0-s1-recovery"
    / "milestones/S10"
)

SCHEMA_PATH = PROTOCOL / "schemas/s10-entry.schema.json"
CONTRACT_PATH = PROTOCOL / "s10-entry-contract.yaml"
INPUT_PATH = PROTOCOL / "inputs/s10-generated.yaml"
PROVENANCE_PATH = PROTOCOL / "manifests/s10-yaml-provenance.json"
MAPPING_PATH = PROTOCOL / "manifests/s10-mapping-corpus.json"
SIZE_REGISTRY_PATH = PROTOCOL / "manifests/s10-size-registry.json"
ENVIRONMENT_PATH = PROTOCOL / "manifests/s10-environment.json"
LOCK_PATH = PROTOCOL / "locks/s10-stage1-entry-lock.json"
SMOKE_PATH = PROTOCOL / "evidence/s10-smoke-correctness.json"
NOISE_PATH = PROTOCOL / "evidence/s10-noise-pilot.json"
DECISION_PATH = PROTOCOL / "evidence/s10-decision.json"

S00_CLOSURE = "8d1be2af3e5033ee74a1a8e3b31536f132a014cb"
S00_REPORT = (
    ROOT
    / "study_docs/research/ductile-origami-warmstart/reports/staged"
    / "s00-foundation-verification-report.md"
)
S00_REPORT_SHA256 = (
    "7a5ef5015d219c007c9cb1109d0f2579846239e5ee76f087a62e7ecd3c9feeb7"
)
DUCTILE_REF = "refs/remotes/origin/ductile_integration"
DUCTILE_COMMIT = "5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39"
GEKO_REF = "refs/remotes/origin/users/pkamd/geko_pr"
GEKO_COMMIT = "d32abacfd13579d1f523f035b7a10b0734c4ac47"
MERGE_BASE = "8f2bacb6cfc3ada0697f20bf271743d94c2d325f"
TEMPLATE_PATH = (
    "projects/hipblaslt/utilities/geko/geko/config_generator/config.yaml"
)
TEMPLATE_BLOB = "e9bae943716ae380129d7314de448fc5cc9f26ed"
TEMPLATE_SHA256 = (
    "e12e22b4ede4263ccc549ca0d19e0bb68b2efc10b70462ed8ba7a6749af7dc6e"
)

DUCTILE_TREES = {
    "projects/hipblaslt": "d8d72b3f3262a4feac63099c1ae12f699c52a808",
    "projects/hipblaslt/tensilelite": "0bc3b63205f3aa5e62b64d0302726e7f5177527d",
    "projects/hipblaslt/tensilelite/rocisa": (
        "db94c6621fbe545e6ac410bbdcb564e83eb805f0"
    ),
    "shared/origami": "17663aaba3c7b6e9c68c7e0b5e7f639422242fa4",
    "shared/stinkytofu": "628e1de27adba9a8936208564d6f2a401d63d612",
}
GEKO_TREE = "c9d28b254face6463c44a526782033ed5632a4c8"
MATERIALIZATION_POLICY = "preserve_validated_pinned_source_symlink_v1"
DUCTILE_SYMLINK_COUNT = 13
DUCTILE_REGULAR_COUNT = 4427
GEKO_REGULAR_COUNT = 78
INTEGRATION_REGULAR_COUNT = 4505
INTEGRATION_LEAF_COUNT = 4518
DUCTILE_SYMLINK_INVENTORY_SHA256 = (
    "0f3a23e838ae0a45597ee07ac36b781d11b1ee81188c5f9b7f33ccd94328a444"
)
EXPECTED_ACTUAL_YAML_SHA256 = (
    "faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36"
)
EXPECTED_GROUPS_SHA256 = (
    "0526a9b3c1d8a1bbe1db2cb03616bfda6e5a1f2dfad3826c0747d8dcb3ab9140"
)
EXPECTED_LEGACY_SPACE_MAP_SHA256 = (
    "5785871bc0779fb67627943ef2ed5fde8e96647be7e0bb0db4f770473cd7a1a0"
)
EXPECTED_AXIS_ORDER_SHA256 = (
    "926a6d9502546dda22ea2edc483c0f61ef74b3e378bcf32f222f17130bb668a3"
)
EXPECTED_WEIGHTS_SHA256 = (
    "56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f"
)
EXPECTED_CONTRACT_SEMANTIC_SHA256 = (
    "c2de2b08b837f1d9fd6590fb8f0c2aa2f3169db7fd134c76d89c6c24843f43d0"
)
EXPECTED_CONTRACT_RAW_SHA256 = (
    "029de2493df60318f2f3ba6ab656e6d85211eee67de7a28e1be2a3310b288a10"
)
R8_GENERATION = "successor-001"
R8_ARCHIVE_ROOT = S10_RUN_ROOT / "r8-parent-lock"
R8_PARENT_RAW_ROOT = R8_ARCHIVE_ROOT / "raw/final-prelock-r7"
R8_ORIGINAL_PARENT_RAW_ROOT = S10_RUN_ROOT / "final-prelock-r7"
R8_PARENT_LOCK_PATH = (
    R8_ARCHIVE_ROOT
    / "retired/study_docs/research/ductile-origami-warmstart/protocol/v1"
    / "locks/s10-stage1-entry-lock.json"
)
R8_PARENT_LOCK_ID = (
    "s10-lock-d7b5c87ac3c30e3b6cd8d9f2ff7267624525f2b877a0191a698c28e29935c6ed"
)
R8_PARENT_LOCK_BODY_SHA256 = (
    "d7b5c87ac3c30e3b6cd8d9f2ff7267624525f2b877a0191a698c28e29935c6ed"
)
R8_PARENT_LOCK_RAW_SHA256 = (
    "fca28ece474b8ae8e26748c23983be84682e2f9880f410759b4948429c6101cb"
)
R8_PARENT_ENVIRONMENT_SHA256 = (
    "dc1d8b5fd3959979ddaf1f61bd79f7e57b1ad502e39db65ee306327999bb762e"
)
R8_PARENT_RAW_TREE_SHA256 = (
    "f8b1f8fbb175f08813e9e897435939656291e7e2a205dba4983f1b9d220e3489"
)
R8_PARENT_RAW_TREE_ENTRY_COUNT = 11767
R8_PARENT_RAW_TREE_REGULAR_BYTES = 12278622411
R8_ARCHIVE_MANIFESTS = {
    "closure": (
        R8_ARCHIVE_ROOT / "manifests/parent-closure.json",
        "ae9a1d3469b6e2adb917e9cae543658893b4998c79b2a57610a3dbbdf61dc750",
    ),
    "failure": (
        R8_ARCHIVE_ROOT / "manifests/failure.json",
        "b73732285050595789bc8333686effc8287f518b271b64ac52555b43b3457d01",
    ),
    "absence": (
        R8_ARCHIVE_ROOT / "manifests/absence.json",
        "b268e4ddfc0092692046de78d9edcb661a41bb2c268199d125060605826a59e0",
    ),
    "seal": (
        R8_ARCHIVE_ROOT / "manifests/seal.json",
        "e6281b219149c70d5981af7306875ff1c1e8d7e07e645c9fd0a8dd1f7b6fcf26",
    ),
}
R8_RECOVERY_AUTHORITY = (
    ROOT / "agent_run/260725-ductile-factorized-guidance-s0-s1-recovery/adjudication.md"
)
R8_RECOVERY_AUTHORITY_SNAPSHOT = (
    S10_RUN_ROOT
    / "r9-successor-001-lock/snapshots/agent_run"
    / "260725-ductile-factorized-guidance-s0-s1-recovery/adjudication.md"
)
R8_RECOVERY_AUTHORITY_SHA256 = (
    "095b3021416a555032b660fe926e9995aad260e88ca6233a99b0b1ee9f3c5c59"
)
R9_CHILD_GENERATION = "successor-002"
R9_ARCHIVE_ROOT = S10_RUN_ROOT / "r9-successor-001-lock"
R9_PARENT_RAW_ROOT = (
    R9_ARCHIVE_ROOT / "raw/final-prelock-r8-successor-001"
)
R9_ORIGINAL_PARENT_RAW_ROOT = (
    S10_RUN_ROOT / "final-prelock-r8-successor-001"
)
R9_CHILD_RAW_ROOT = S10_RUN_ROOT / "final-prelock-r9-successor-002"
R9_PARENT_LOCK_PATH = (
    R9_ARCHIVE_ROOT
    / "retired/study_docs/research/ductile-origami-warmstart/protocol/v1"
    / "locks/s10-stage1-entry-lock.json"
)
R9_PARENT_LOCK_ID = (
    "s10-lock-c04c6a827bc6dc204fc46b9b4a7d1ed46896ef5f51996a0853a3abad26bb1e33"
)
R9_PARENT_LOCK_BODY_SHA256 = (
    "c04c6a827bc6dc204fc46b9b4a7d1ed46896ef5f51996a0853a3abad26bb1e33"
)
R9_PARENT_LOCK_RAW_SHA256 = (
    "590912852b27d84e4992d844de3b65e544b96aeda947c0aa7a80d295d16e4b28"
)
R9_PARENT_ENVIRONMENT_SHA256 = (
    "e59d2d5cf7e4d31d12c1e761674540c7eee8dd7297e7567f4a0b19291fa7bafb"
)
R9_PARENT_RAW_TREE_SHA256 = (
    "bc99fb3a13ee74a118c3f75fff1d18387b1738e8a99cd1af34e660441c88bf65"
)
R9_PARENT_RAW_TREE_ENTRY_COUNT = 11788
R9_PARENT_RAW_TREE_REGULAR_BYTES = 12279134329
R9_TRANSITION_ID = (
    "s10-transition-f3a3ecd6bc393877aca044e2784d97ea62988c17d0ea2b09ba9fea857b177ed3"
)
R9_CLAIM_PATH = (
    R9_ARCHIVE_ROOT
    / "claims"
    / f"{R9_PARENT_LOCK_ID}.json"
)
R9_CLAIM_SHA256 = (
    "a452f68d1233eea84e6164c9d43ced524d658bcd172564cd4be256a8136a06ad"
)
R9_ARCHIVE_MANIFESTS = {
    "closure": (
        R9_ARCHIVE_ROOT / "manifests/parent-closure.json",
        "e1ace1236f09f735f7bcd72565d7957d8c778df33e6cf97e55dbc131541d2519",
    ),
    "failure": (
        R9_ARCHIVE_ROOT / "manifests/failure.json",
        "c892d3061db6bfdeadb2e1abd770ba9e7f3020a53372be8c0e7cc8db3b994c3d",
    ),
    "absence": (
        R9_ARCHIVE_ROOT / "manifests/absence.json",
        "b4bfb72fda228347d8804b5233eaeb3845c11b6e62d7b5b5e976aec5b57dbbeb",
    ),
    "rehash": (
        R9_ARCHIVE_ROOT / "audit/independent-full-rehash.json",
        "f44d92e05c2995ad5e91209779da2041b4abb6e458ce283d084fd547d19bff8e",
    ),
    "seal": (
        R9_ARCHIVE_ROOT / "manifests/seal.json",
        "8a86d633e960d43a6eb8f9fe8ede937762479101d30f5a58beef2ece0a19869b",
    ),
}
R9_RECOVERY_AUTHORITY = R8_RECOVERY_AUTHORITY
R9_RECOVERY_AUTHORITY_SHA256 = (
    "46dee6a54eb0deeb69b0e166f2406bbeed18d57300610e9a4be49af0de55d1ea"
)
CURRENT_GENERATION = "successor-003"
R10_ARCHIVE_ROOT = S10_RUN_ROOT / "r10-successor-002-lock"
R10_PARENT_RAW_ROOT = (
    R10_ARCHIVE_ROOT / "raw/final-prelock-r9-successor-002"
)
R10_ORIGINAL_PARENT_RAW_ROOT = (
    S10_RUN_ROOT / "final-prelock-r9-successor-002"
)
R10_CHILD_RAW_ROOT = S10_RUN_ROOT / "final-prelock-r10-successor-003"
R10_PARENT_LOCK_PATH = (
    R10_ARCHIVE_ROOT
    / "retired/study_docs/research/ductile-origami-warmstart/protocol/v1"
    / "locks/s10-stage1-entry-lock.json"
)
R10_PARENT_LOCK_ID = (
    "s10-lock-2a1e31d88538791ed8abe5f37f67f81be7d032a1575da2a872928ad15e66d81a"
)
R10_PARENT_LOCK_BODY_SHA256 = (
    "2a1e31d88538791ed8abe5f37f67f81be7d032a1575da2a872928ad15e66d81a"
)
R10_PARENT_LOCK_RAW_SHA256 = (
    "ab475892cdb15fe85c854ff89a2a92d0ed945ab630da8fdefbad75b5ba47f3f3"
)
R10_PARENT_ENVIRONMENT_SHA256 = (
    "af4c58941102b6a26d1b473033c17a0d6bbf9ae80d986555d9212e54f79197a1"
)
R10_PARENT_RAW_TREE_SHA256 = (
    "088fd008995448bd3d99538acb0bc5e60391ff05e0da51ece6adae14a1dd1e19"
)
R10_PARENT_RAW_TREE_ENTRY_COUNT = 11792
R10_PARENT_RAW_TREE_REGULAR_BYTES = 12279373335
R10_TRANSITION_ID = (
    "s10-transition-6241204f902c6a37db47a405e1b7389e34c3614d7d5290257358b5d994eef7ea"
)
R10_CLAIM_PATH = (
    R10_ARCHIVE_ROOT / "claims" / f"{R10_PARENT_LOCK_ID}.json"
)
R10_CLAIM_SHA256 = (
    "9f51a2ad22556d1e8e817bd35ca140db7ed53b5a97a05bca1662d8663c85e14d"
)
R10_ARCHIVE_MANIFESTS = {
    "closure": (
        R10_ARCHIVE_ROOT / "manifests/parent-closure.json",
        "766e742e0d3957a13887f9bb51294c707f8dcd1633dfa7cd39073cadaf86c554",
    ),
    "failure": (
        R10_ARCHIVE_ROOT / "manifests/failure.json",
        "b6820f29015d5123c8eae18ff67132482ee843ab6fa1c619226b1456ac736854",
    ),
    "absence": (
        R10_ARCHIVE_ROOT / "manifests/absence.json",
        "ac950e07f90532fc17c2bf56a308a6483570d992c0fdb12198f866973f9f90bd",
    ),
    "rehash": (
        R10_ARCHIVE_ROOT / "audit/independent-full-rehash.json",
        "df09ea1ef5bb1eced8863da0cde61df0e66a75dbb83da2c211fad15af2344079",
    ),
    "seal": (
        R10_ARCHIVE_ROOT / "manifests/seal.json",
        "2b39f47c6603b44d9d8e8499f58b9d161dff7139d5411cfb9e81c4a3a0bac466",
    ),
}
R10_RECOVERY_AUTHORITY = R9_RECOVERY_AUTHORITY
R10_RECOVERY_AUTHORITY_SHA256 = (
    "d0166dd259b9227df440e124afc49da1baba36e5dbfc66bd7796c0cbff0118df"
)
FROZEN_PLAN_B_SHA256 = (
    "3cb50d05c3481e4fb6d2a0fd9b23cb0e6876d2b9b0582af17a7220710e2a40d7"
)
AMENDED_PLAN_A_SHA256 = (
    "60862d9597a14175659cfa5ee93f747b71c5cdb7b7051c16a6d5a7ea852accd3"
)
EXPECTED_CONSUMER_STDERR = (
    "GA:WARNING Some variables have a larger search space than pop_size. "
    "Increasing pop_size for the first generations.\n"
)
EXPECTED_AXIS_ORDER = [
    "TransposeLDS",
    "GlobalReadVectorWidthA",
    "GlobalReadVectorWidthB",
    "WaveSeparateGlobalReadA",
    "WaveSeparateGlobalReadB",
    "UnrollLoopSwapGlobalReadOrder",
    "PrefetchGlobalRead",
    "DirectToVgprA",
    "StaggerU",
    "StaggerUStride",
    "WorkGroupMapping",
    "WorkGroupMappingXCC",
    "1LDSBuffer",
    "DepthU",
    "NonTemporalD",
    "NonTemporalC",
    "NonTemporalA",
    "NonTemporalB",
    "SourceSwap",
    "StorePriorityOpt",
    "NumElementsPerBatchStore",
    "StoreSyncOpt",
    "MIArchVgpr",
    "AdaptiveGemm",
    "ExtraMiLatencyLeft",
    "TailloopInNll",
    "ScheduleGROverBarrier",
    "group_0",
    "group_1",
    "group_2",
]
R4_SOURCE_BLOBS = {
    "projects/hipblaslt/tensilelite/Tensile/BenchmarkStructs.py": "4968b29b5eacddc56b20c42cb4b2c1e3d8d6f406",
    "projects/hipblaslt/tensilelite/Tensile/Common/GlobalParameters.py": "e576b94fab302382aa55c46a077168b4aaf8b08f",
    "projects/hipblaslt/tensilelite/Tensile/Common/ValidParameters.py": "f0166a77e3646d922debfdd3aa5734a88a98304a",
    "projects/hipblaslt/tensilelite/Tensile/BenchmarkProblems.py": "c9e4144ca0b2d7396c57249eaf3770b12ebd87f8",
    "projects/hipblaslt/tensilelite/Tensile/backends/ductile_backend.py": "e295e481f832cf00d9826e7aaf6130aaaf9651d2",
    "projects/hipblaslt/tensilelite/Tensile/ductile/core/space.py": "315d39b2fd5b714736145dff9ac1bf1e196bf61f",
    "projects/hipblaslt/tensilelite/Tensile/LibraryIO.py": "794e1e528e9113a25e46a8e628f7e441132e1a14",
    "projects/hipblaslt/tensilelite/Tensile/ductile/config/__init__.py": "7bfe80353c1ce3b45156207895af2cd6311b43da",
    "projects/hipblaslt/tensilelite/Tensile/ductile/config/defaults.yaml": "dacc78a3de71a402b8af6d202400453014a2852d",
    "projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py": "de47028571bba928ec7f4184e1f1085c7ab86280",
}

IMPLEMENTATION_WHITELIST = [
    "projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10_entry.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10_entry.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/s10-entry.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s10-entry-contract.yaml",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/inputs/s10-generated.yaml",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10-yaml-provenance.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10-mapping-corpus.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10-size-registry.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10-environment.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s10-stage1-entry-lock.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s10-smoke-correctness.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s10-noise-pilot.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s10-decision.json",
]
DELIVERY_WHITELIST = IMPLEMENTATION_WHITELIST + [
    "study_docs/research/ductile-origami-warmstart/reports/staged/s10-stage1-entry-gate-report.md",
    "study_docs/research/ductile-origami-warmstart-experiment-plan.md",
    "study_docs/research/ductile-origami-warmstart/README.md",
    "study_docs/research/ductile-origami-warmstart/s10-stage1-entry-access-mapping-gate-design.md",
]
FORBIDDEN_ROOTS = [
    "study_docs/research/ductile-origami-warmstart/reports/staged/s11-stage1-model-only-factorization-report.md",
    "study_docs/research/ductile-origami-warmstart/reports/staged/s12-stage1-real-score-audit-report.md",
    "study_docs/research/ductile-origami-warmstart/reports/gen0-factorization-mvp-report.md",
    "study_docs/research/ductile-origami-warmstart/reports/short-horizon-persistence-report.md",
    "study_docs/research/ductile-origami-warmstart/reports/bounded-regime-replication-report.md",
    "study_docs/research/ductile-origami-warmstart/reports/staged/s40-stage4-activation-report.md",
    "study_docs/research/ductile-origami-warmstart/reports/learned-residual-surrogate-report.md",
]
POST_LOCK_PATHS = (
    ENVIRONMENT_PATH,
    LOCK_PATH,
    MAPPING_PATH,
    SMOKE_PATH,
    NOISE_PATH,
    DECISION_PATH,
)
ENV_UPDATABLE_KEYS = ("StreamK", "MI_FILTER", "GA_VALIDATION_PROFILE")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_RE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$")
SITE_PACKAGES = Path("/opt/venv/lib/python3.12/site-packages")
CONTAINER_REPO = Path("/src/rocm-libraries")
PYTHON = Path("/opt/venv/bin/python3")
CMAKE = Path("/opt/venv/bin/cmake")
ROCM_CMAKE = Path("/opt/rocm/share/rocmcmakebuildtools/cmake")
COMPILER = Path("/opt/rocm/bin/amdclang++")
OFFLOAD_BUNDLER = Path("/opt/rocm/lib/llvm/bin/clang-offload-bundler")
ROCM_SMI = Path("/opt/rocm/bin/rocm-smi")
LIVE_DEVICE_ARGV = [
    str(ROCM_SMI),
    "--showid",
    "--showproductname",
    "--showserial",
    "--showuniqueid",
    "--showbus",
    "--showuse",
    "--showmemuse",
    "--showmeminfo",
    "vram",
    "--showcomputepartition",
    "--showmemorypartition",
    "--json",
]
LIVE_PROCESS_ARGV = [str(ROCM_SMI), "--showpidgpus"]
LIVE_H4_POLICY = {
    "sample_count": 3,
    "minimum_sample_spacing_seconds": 2,
    "arch": "gfx942",
    "compute_partition": "SPX",
    "memory_partition": "NPS1",
    "gpu_use_percent": 0,
    "maximum_vram_allocation_percent": 1,
    "mapped_kfd_pid_count": 0,
    "selection_key": [
        "maximum_sampled_vram_used_bytes",
        "container_visible_index",
        "unique_id",
    ],
    "maximum_complete_attempts": 3,
    "maximum_during_sample_period_seconds": 1,
}
POSTLOCK_RESULT_MARKER = "S10_POSTLOCK_RESULT="


class S10Error(EvidenceValidationError):
    """Stable S10 failure with a machine-readable error code."""


def _fail(code: str, message: str) -> None:
    raise S10Error(message, code=code)


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str, *, field: str) -> dt.datetime:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        _fail("h4_malformed", f"{field} must be an explicit UTC timestamp")
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise S10Error(str(exc), code="h4_malformed") from exc


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        _fail("unsafe_path", f"path is outside repository: {path}")


def _assert_scratch_root(path: Path) -> Path:
    resolved = path.resolve()
    allowed = S10_RUN_ROOT.resolve()
    if resolved == allowed or allowed not in resolved.parents:
        _fail(
            "unsafe_path",
            f"scratch root must be a child of {_rel(S10_RUN_ROOT)}",
        )
    if (
        resolved == R8_PARENT_RAW_ROOT.resolve()
        or R8_PARENT_RAW_ROOT.resolve() in resolved.parents
        or resolved == R8_ORIGINAL_PARENT_RAW_ROOT.resolve()
        or R8_ORIGINAL_PARENT_RAW_ROOT.resolve() in resolved.parents
        or resolved == R9_PARENT_RAW_ROOT.resolve()
        or R9_PARENT_RAW_ROOT.resolve() in resolved.parents
        or resolved == R9_ORIGINAL_PARENT_RAW_ROOT.resolve()
        or R9_ORIGINAL_PARENT_RAW_ROOT.resolve() in resolved.parents
        or resolved == R10_PARENT_RAW_ROOT.resolve()
        or R10_PARENT_RAW_ROOT.resolve() in resolved.parents
        or resolved == R10_ORIGINAL_PARENT_RAW_ROOT.resolve()
        or R10_ORIGINAL_PARENT_RAW_ROOT.resolve() in resolved.parents
    ):
        _fail("parent_evidence_reuse", "retired ancestor raw lineage cannot be active")
    return resolved


def _r8_manifest_ref(role: str) -> dict[str, str]:
    path, digest = R8_ARCHIVE_MANIFESTS[role]
    return {"path": _rel(path), "raw_sha256": digest}


def _r8_parent_reference() -> dict[str, Any]:
    return {
        "generation": "genesis",
        "archive_root": _rel(R8_ARCHIVE_ROOT),
        "lock": {
            "path": _rel(R8_PARENT_LOCK_PATH),
            "raw_sha256": R8_PARENT_LOCK_RAW_SHA256,
            "body_sha256": R8_PARENT_LOCK_BODY_SHA256,
            "lock_id": R8_PARENT_LOCK_ID,
        },
        "environment": {
            "path": _rel(
                R8_ARCHIVE_ROOT
                / "retired/study_docs/research/ductile-origami-warmstart"
                / "protocol/v1/manifests/s10-environment.json"
            ),
            "raw_sha256": R8_PARENT_ENVIRONMENT_SHA256,
        },
        "closure": _r8_manifest_ref("closure"),
        "failure": _r8_manifest_ref("failure"),
        "absence": _r8_manifest_ref("absence"),
        "seal": _r8_manifest_ref("seal"),
        "raw_tree": {
            "path": _rel(R8_PARENT_RAW_ROOT),
            "tree_canonical_sha256": R8_PARENT_RAW_TREE_SHA256,
            "entry_count": R8_PARENT_RAW_TREE_ENTRY_COUNT,
            "regular_file_bytes": R8_PARENT_RAW_TREE_REGULAR_BYTES,
        },
    }


def _r8_recovery_authority() -> dict[str, str]:
    return {
        "path": _rel(R8_RECOVERY_AUTHORITY),
        "raw_sha256": R8_RECOVERY_AUTHORITY_SHA256,
    }


def _r8_lifecycle_fields() -> dict[str, Any]:
    return {
        "generation": R8_GENERATION,
        "evidence_reuse": False,
        "parent_lock": _r8_parent_reference(),
        "recovery_authority": _r8_recovery_authority(),
    }


def _r9_manifest_ref(role: str) -> dict[str, str]:
    path, digest = R9_ARCHIVE_MANIFESTS[role]
    return {"path": _rel(path), "raw_sha256": digest}


def _r9_parent_reference() -> dict[str, Any]:
    return {
        "generation": R8_GENERATION,
        "archive_root": _rel(R9_ARCHIVE_ROOT),
        "transition_id": R9_TRANSITION_ID,
        "claim": {
            "path": _rel(R9_CLAIM_PATH),
            "raw_sha256": R9_CLAIM_SHA256,
        },
        "lock": {
            "path": _rel(R9_PARENT_LOCK_PATH),
            "raw_sha256": R9_PARENT_LOCK_RAW_SHA256,
            "body_sha256": R9_PARENT_LOCK_BODY_SHA256,
            "lock_id": R9_PARENT_LOCK_ID,
        },
        "environment": {
            "path": _rel(
                R9_ARCHIVE_ROOT
                / "retired/study_docs/research/ductile-origami-warmstart"
                / "protocol/v1/manifests/s10-environment.json"
            ),
            "raw_sha256": R9_PARENT_ENVIRONMENT_SHA256,
        },
        "closure": _r9_manifest_ref("closure"),
        "failure": _r9_manifest_ref("failure"),
        "absence": _r9_manifest_ref("absence"),
        "rehash": _r9_manifest_ref("rehash"),
        "seal": _r9_manifest_ref("seal"),
        "raw_tree": {
            "path": _rel(R9_PARENT_RAW_ROOT),
            "tree_canonical_sha256": R9_PARENT_RAW_TREE_SHA256,
            "entry_count": R9_PARENT_RAW_TREE_ENTRY_COUNT,
            "regular_file_bytes": R9_PARENT_RAW_TREE_REGULAR_BYTES,
        },
    }


def _current_recovery_authority(
    snapshot_path: Path | None = None,
) -> dict[str, str]:
    path = snapshot_path or R10_RECOVERY_AUTHORITY
    return {
        "path": _rel(path),
        "raw_sha256": R10_RECOVERY_AUTHORITY_SHA256,
    }


def _r10_manifest_ref(role: str) -> dict[str, str]:
    path, digest = R10_ARCHIVE_MANIFESTS[role]
    return {"path": _rel(path), "raw_sha256": digest}


def _r10_parent_reference() -> dict[str, Any]:
    return {
        "generation": R9_CHILD_GENERATION,
        "archive_root": _rel(R10_ARCHIVE_ROOT),
        "transition_id": R10_TRANSITION_ID,
        "claim": {
            "path": _rel(R10_CLAIM_PATH),
            "raw_sha256": R10_CLAIM_SHA256,
        },
        "lock": {
            "path": _rel(R10_PARENT_LOCK_PATH),
            "raw_sha256": R10_PARENT_LOCK_RAW_SHA256,
            "body_sha256": R10_PARENT_LOCK_BODY_SHA256,
            "lock_id": R10_PARENT_LOCK_ID,
        },
        "environment": {
            "path": _rel(
                R10_ARCHIVE_ROOT
                / "retired/study_docs/research/ductile-origami-warmstart"
                / "protocol/v1/manifests/s10-environment.json"
            ),
            "raw_sha256": R10_PARENT_ENVIRONMENT_SHA256,
        },
        "closure": _r10_manifest_ref("closure"),
        "failure": _r10_manifest_ref("failure"),
        "absence": _r10_manifest_ref("absence"),
        "rehash": _r10_manifest_ref("rehash"),
        "seal": _r10_manifest_ref("seal"),
        "raw_tree": {
            "path": _rel(R10_PARENT_RAW_ROOT),
            "tree_canonical_sha256": R10_PARENT_RAW_TREE_SHA256,
            "entry_count": R10_PARENT_RAW_TREE_ENTRY_COUNT,
            "regular_file_bytes": R10_PARENT_RAW_TREE_REGULAR_BYTES,
        },
    }


def _current_lifecycle_fields(
    recovery_authority: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "generation": CURRENT_GENERATION,
        "evidence_reuse": False,
        "parent_lock": _r10_parent_reference(),
        "recovery_authority": dict(
            recovery_authority or _current_recovery_authority()
        ),
    }


def _verify_archive_file(item: Mapping[str, Any], *, role: str) -> None:
    path_text = item.get("archive_path")
    if not isinstance(path_text, str):
        _fail("parent_archive_drift", f"{role} archive path is malformed")
    path = ROOT / path_text
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise S10Error(
            f"{role} archive path unavailable: {path_text}",
            code="parent_archive_drift",
        ) from exc
    kind = item.get("kind")
    if kind == "regular_file":
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_size != item.get("size")
            or sha256_file(path) != item.get("raw_sha256")
        ):
            _fail("parent_archive_drift", f"{role} file drift: {path_text}")
    elif kind == "symlink":
        if (
            not stat.S_ISLNK(info.st_mode)
            or os.readlink(path) != item.get("link_text")
        ):
            _fail("parent_archive_drift", f"{role} symlink drift: {path_text}")
    elif kind == "directory":
        if not stat.S_ISDIR(info.st_mode):
            _fail("parent_archive_drift", f"{role} directory drift: {path_text}")
    else:
        _fail("parent_archive_drift", f"{role} has unsupported kind: {kind!r}")
    if f"{info.st_mode:06o}" != item.get("mode"):
        _fail("parent_archive_drift", f"{role} mode drift: {path_text}")


def _archive_paths(root: Path) -> list[str]:
    result: list[str] = []
    pending = [root]
    while pending:
        current = pending.pop()
        result.append(current.relative_to(ROOT).as_posix())
        info = os.lstat(current)
        if stat.S_ISDIR(info.st_mode):
            with os.scandir(current) as entries:
                children = sorted((Path(item.path) for item in entries), reverse=True)
            pending.extend(children)
    return sorted(result)


def _verify_r8_parent_archive(*, rehash_raw_tree: bool = True) -> dict[str, Any]:
    if not R8_ARCHIVE_ROOT.is_dir() or R8_ARCHIVE_ROOT.is_symlink():
        _fail("parent_archive_missing", "sealed R8 parent archive is unavailable")
    documents: dict[str, Any] = {}
    for role, (path, digest) in R8_ARCHIVE_MANIFESTS.items():
        if (
            not path.is_file()
            or path.is_symlink()
            or sha256_file(path) != digest
        ):
            _fail("parent_archive_drift", f"R8 {role} manifest identity differs")
        documents[role] = strict_load_json(path)
    closure = documents["closure"]
    failure = documents["failure"]
    absence = documents["absence"]
    seal = documents["seal"]
    if (
        closure.get("archive_root") != _rel(R8_ARCHIVE_ROOT)
        or closure.get("parent_lock")
        != {
            "archive_path": _rel(R8_PARENT_LOCK_PATH),
            "body_sha256": R8_PARENT_LOCK_BODY_SHA256,
            "environment_raw_sha256": R8_PARENT_ENVIRONMENT_SHA256,
            "lock_id": R8_PARENT_LOCK_ID,
            "raw_sha256": R8_PARENT_LOCK_RAW_SHA256,
            "source_path": _rel(LOCK_PATH),
            "state": "effective",
        }
    ):
        _fail("wrong_parent_lock", "R8 parent closure identifies another parent")
    raw_tree = closure.get("raw_tree")
    if not isinstance(raw_tree, dict) or {
        "archive_root": raw_tree.get("archive_root"),
        "entry_count": raw_tree.get("entry_count"),
        "regular_file_bytes": raw_tree.get("regular_file_bytes"),
        "source_root": raw_tree.get("source_root"),
        "tree_canonical_sha256": raw_tree.get("tree_canonical_sha256"),
    } != {
        "archive_root": _rel(R8_PARENT_RAW_ROOT),
        "entry_count": R8_PARENT_RAW_TREE_ENTRY_COUNT,
        "regular_file_bytes": R8_PARENT_RAW_TREE_REGULAR_BYTES,
        "source_root": _rel(R8_ORIGINAL_PARENT_RAW_ROOT),
        "tree_canonical_sha256": R8_PARENT_RAW_TREE_SHA256,
    }:
        _fail("parent_archive_drift", "R8 raw-tree summary differs")
    entries = raw_tree.get("entries")
    if (
        not isinstance(entries, list)
        or len(entries) != R8_PARENT_RAW_TREE_ENTRY_COUNT
        or canonical_sha256(entries) != R8_PARENT_RAW_TREE_SHA256
    ):
        _fail("parent_archive_drift", "R8 raw-tree ledger differs")
    expected_direct = {
        "request": "95444bdfc768d6af63871c783af19e7762a2a5f21dd0813d69380f040cd1242a",
        "stdout": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "stderr": "58638c453b05200c8dfb6de6fae2abe040afd120b1cf262f590b7d8e8224cd3b",
        "native_manifest": "06b1f6a31f5756d70ee50d7fa366662e914921328035f132044f356f0ac82d6d",
    }
    direct = failure.get("direct_evidence")
    if (
        failure.get("parent_lock_id") != R8_PARENT_LOCK_ID
        or failure.get("parent_lock_raw_sha256") != R8_PARENT_LOCK_RAW_SHA256
        or not isinstance(direct, list)
        or {item.get("evidence_role"): item.get("raw_sha256") for item in direct}
        != expected_direct
        or failure.get("direct_observations", {}).get("rows_emitted") is not False
        or failure.get("direct_observations", {}).get("marker_found_in_stdout")
        is not False
    ):
        _fail("parent_failure_missing", "R8 parent failure evidence differs")
    if (
        absence.get("rows_absence")
        != {
            "mapping_raw_absent": True,
            "pass_b_absent": True,
            "rows_emitted": False,
        }
        or absence.get("marker_absence", {}).get("found") is not False
    ):
        _fail("parent_failure_missing", "R8 failure absence boundary differs")
    if (
        seal.get("status") != "SEALED"
        or seal.get("archive_root") != _rel(R8_ARCHIVE_ROOT)
        or seal.get("parent_lock")
        != {
            "body_sha256": R8_PARENT_LOCK_BODY_SHA256,
            "lock_id": R8_PARENT_LOCK_ID,
            "raw_sha256": R8_PARENT_LOCK_RAW_SHA256,
        }
        or seal.get("raw_tree")
        != {
            "entry_count": R8_PARENT_RAW_TREE_ENTRY_COUNT,
            "regular_file_bytes": R8_PARENT_RAW_TREE_REGULAR_BYTES,
            "tree_canonical_sha256": R8_PARENT_RAW_TREE_SHA256,
        }
    ):
        _fail("parent_archive_drift", "R8 archive seal differs")
    for item in [
        *closure.get("preserved_files", []),
        *closure.get("retired_parent_files", []),
        *direct,
    ]:
        _verify_archive_file(item, role="R8 preserved")
    if (
        not R8_PARENT_LOCK_PATH.is_file()
        or sha256_file(R8_PARENT_LOCK_PATH) != R8_PARENT_LOCK_RAW_SHA256
    ):
        _fail("wrong_parent_lock", "retired parent lock bytes differ")
    parent = strict_load_json(R8_PARENT_LOCK_PATH)
    if (
        parent.get("parent_lock") is not None
        or parent.get("body_sha256") != R8_PARENT_LOCK_BODY_SHA256
        or parent.get("lock_id") != R8_PARENT_LOCK_ID
    ):
        _fail("lifecycle_cycle", "retired lock is not the genesis parent")
    if R8_ORIGINAL_PARENT_RAW_ROOT.exists():
        _fail("parent_reactivation", "original R7 raw root was reactivated")
    if (
        not R8_RECOVERY_AUTHORITY_SNAPSHOT.is_file()
        or sha256_file(R8_RECOVERY_AUTHORITY_SNAPSHOT)
        != R8_RECOVERY_AUTHORITY_SHA256
    ):
        _fail("recovery_authority_mismatch", "R8 recovery authority differs")
    if rehash_raw_tree:
        recorded_paths = sorted(item["archive_path"] for item in entries)
        if recorded_paths != _archive_paths(R8_PARENT_RAW_ROOT):
            _fail("parent_archive_drift", "R8 raw-tree membership differs")
        for item in entries:
            _verify_archive_file(item, role="R8 raw tree")
    return _r8_parent_reference()


def _verify_r8_successor_fields(document: Mapping[str, Any], *, role: str) -> None:
    expected = _r8_lifecycle_fields()
    actual = {key: document.get(key) for key in expected}
    if actual != expected:
        _fail("successor_lifecycle_mismatch", f"{role} successor fields differ")


def _verify_r9_parent_archive(*, rehash_raw_tree: bool = True) -> dict[str, Any]:
    """Verify successor-001's immutable archive and its recursive genesis parent."""

    _verify_r8_parent_archive(rehash_raw_tree=rehash_raw_tree)
    if not R9_ARCHIVE_ROOT.is_dir() or R9_ARCHIVE_ROOT.is_symlink():
        _fail("parent_archive_missing", "sealed R9 parent archive is unavailable")
    documents: dict[str, Any] = {}
    for role, (path, digest) in R9_ARCHIVE_MANIFESTS.items():
        if not path.is_file() or path.is_symlink() or sha256_file(path) != digest:
            _fail("parent_archive_drift", f"R9 {role} manifest identity differs")
        documents[role] = strict_load_json(path)
    if (
        not R9_CLAIM_PATH.is_file()
        or R9_CLAIM_PATH.is_symlink()
        or sha256_file(R9_CLAIM_PATH) != R9_CLAIM_SHA256
    ):
        _fail("parent_claim_drift", "R9 parent-consumption claim identity differs")
    claim = strict_load_json(R9_CLAIM_PATH)
    if (
        claim.get("state") != "TRANSITION_CLAIMED"
        or claim.get("claim_key") != R9_PARENT_LOCK_ID
        or claim.get("parent_generation") != R8_GENERATION
        or claim.get("intended_child_generation") != R9_CHILD_GENERATION
        or claim.get("transition_id") != R9_TRANSITION_ID
        or claim.get("claim_semantics", {}).get("single_use_parent_consumption")
        is not True
        or claim.get("claim_semantics", {}).get(
            "forbid_sibling_or_sequential_sibling_creation"
        )
        is not True
        or claim.get("claim_semantics", {}).get(
            "forbid_parent_rollback_or_reactivation"
        )
        is not True
    ):
        _fail("parent_claim_drift", "R9 parent-consumption claim semantics differ")
    if sorted(item.name for item in R9_CLAIM_PATH.parent.iterdir()) != [
        f"{R9_PARENT_LOCK_ID}.json"
    ]:
        _fail("lineage_sibling", "R9 parent has multiple consumption claims")
    closure = documents["closure"]
    failure = documents["failure"]
    absence = documents["absence"]
    rehash = documents["rehash"]
    seal = documents["seal"]
    if (
        closure.get("archive_root") != _rel(R9_ARCHIVE_ROOT)
        or closure.get("transition_id") != R9_TRANSITION_ID
        or closure.get("claim")
        != {
            "path": _rel(R9_CLAIM_PATH),
            "raw_sha256": R9_CLAIM_SHA256,
            "state": "TRANSITION_CLAIMED",
        }
    ):
        _fail("parent_archive_drift", "R9 closure identity differs")
    expected_parent = {
        "archive_path": _rel(R9_PARENT_LOCK_PATH),
        "body_sha256": R9_PARENT_LOCK_BODY_SHA256,
        "generation": R8_GENERATION,
        "lock_id": R9_PARENT_LOCK_ID,
        "raw_sha256": R9_PARENT_LOCK_RAW_SHA256,
        "state": "retired",
    }
    if closure.get("parent_lock") != expected_parent:
        _fail("wrong_parent_lock", "R9 closure identifies another parent")
    raw_tree = closure.get("raw_tree")
    expected_raw_summary = {
        "archive_root": _rel(R9_PARENT_RAW_ROOT),
        "entry_count": R9_PARENT_RAW_TREE_ENTRY_COUNT,
        "regular_file_bytes": R9_PARENT_RAW_TREE_REGULAR_BYTES,
        "source_root": _rel(R9_ORIGINAL_PARENT_RAW_ROOT),
        "tree_canonical_sha256": R9_PARENT_RAW_TREE_SHA256,
    }
    if (
        not isinstance(raw_tree, dict)
        or {
            key: raw_tree.get(key)
            for key in expected_raw_summary
        }
        != expected_raw_summary
    ):
        _fail("parent_archive_drift", "R9 raw-tree summary differs")
    entries = raw_tree.get("entries")
    if (
        not isinstance(entries, list)
        or len(entries) != R9_PARENT_RAW_TREE_ENTRY_COUNT
        or canonical_sha256(entries) != R9_PARENT_RAW_TREE_SHA256
    ):
        _fail("parent_archive_drift", "R9 raw-tree ledger differs")
    observations = failure.get("mapping_observations", {})
    if (
        failure.get("classification")
        != "CHANGES_REQUIRED/postlock_harness_defect"
        or failure.get("parent_lock_id") != R9_PARENT_LOCK_ID
        or observations.get("attribute_error_rows") != 3
        or observations.get("pinned_validation_boundary_none_rows") != 27
        or observations.get("scientific_negative_supported") is not False
        or observations.get("actual_rows_are_incident_evidence_only") is not True
    ):
        _fail("parent_failure_missing", "R9 parent failure semantics differ")
    if (
        absence.get("no_active_lock") is not True
        or absence.get("downstream_edge_absent") is not True
        or any(item.get("absent") is not True for item in absence.get("checks", []))
    ):
        _fail("parent_failure_missing", "R9 parent absence boundary differs")
    if (
        rehash.get("raw_tree")
        != {
            "entry_count": R9_PARENT_RAW_TREE_ENTRY_COUNT,
            "membership_match": True,
            "metadata_and_bytes_match": True,
            "regular_file_bytes": R9_PARENT_RAW_TREE_REGULAR_BYTES,
            "tree_canonical_sha256": R9_PARENT_RAW_TREE_SHA256,
        }
        or seal.get("state") != "PARENT_ARCHIVE_SEALED/NO_ACTIVE_LOCK"
        or seal.get("transition_id") != R9_TRANSITION_ID
        or seal.get("raw_tree")
        != {
            "entry_count": R9_PARENT_RAW_TREE_ENTRY_COUNT,
            "regular_file_bytes": R9_PARENT_RAW_TREE_REGULAR_BYTES,
            "tree_canonical_sha256": R9_PARENT_RAW_TREE_SHA256,
        }
    ):
        _fail("parent_archive_drift", "R9 archive seal/full-rehash differs")
    for item in [
        *closure.get("bound_and_governing_snapshots", []),
        *closure.get("retired_parent_files", []),
    ]:
        _verify_archive_file(item, role="R9 preserved")
    if (
        not R9_PARENT_LOCK_PATH.is_file()
        or sha256_file(R9_PARENT_LOCK_PATH) != R9_PARENT_LOCK_RAW_SHA256
    ):
        _fail("wrong_parent_lock", "retired successor-001 lock bytes differ")
    parent = strict_load_json(R9_PARENT_LOCK_PATH)
    if (
        parent.get("generation") != R8_GENERATION
        or parent.get("body_sha256") != R9_PARENT_LOCK_BODY_SHA256
        or parent.get("lock_id") != R9_PARENT_LOCK_ID
    ):
        _fail("wrong_parent_lock", "retired successor-001 lock identity differs")
    _verify_r8_successor_fields(parent, role="retired successor-001 lock")
    if R9_ORIGINAL_PARENT_RAW_ROOT.exists():
        _fail("parent_reactivation", "retired successor-001 raw root was reactivated")
    if LOCK_PATH.exists():
        active = strict_load_json(LOCK_PATH)
        valid_successor_002 = (
            active.get("generation") == R9_CHILD_GENERATION
            and active.get("parent_lock") == _r9_parent_reference()
        )
        valid_successor_003 = (
            active.get("generation") == CURRENT_GENERATION
            and active.get("parent_lock") == _r10_parent_reference()
        )
        if not (valid_successor_002 or valid_successor_003):
            _fail("parent_reactivation", "canonical lock is not the unique child leaf")
    archive_identities = {
        R8_PARENT_LOCK_RAW_SHA256,
        R9_PARENT_LOCK_RAW_SHA256,
        R8_PARENT_RAW_TREE_SHA256,
        R9_PARENT_RAW_TREE_SHA256,
    }
    if len(archive_identities) != 4:
        _fail("lineage_reuse", "ancestor lock/raw identities are not unique")
    if rehash_raw_tree:
        recorded_paths = sorted(item["archive_path"] for item in entries)
        if recorded_paths != _archive_paths(R9_PARENT_RAW_ROOT):
            _fail("parent_archive_drift", "R9 raw-tree membership differs")
        for item in entries:
            _verify_archive_file(item, role="R9 raw tree")
    return _r9_parent_reference()


def _verify_r10_parent_archive(*, rehash_raw_tree: bool = True) -> dict[str, Any]:
    """Verify successor-002's archive and its complete recursive ancestry."""

    _verify_r9_parent_archive(rehash_raw_tree=rehash_raw_tree)
    if not R10_ARCHIVE_ROOT.is_dir() or R10_ARCHIVE_ROOT.is_symlink():
        _fail("parent_archive_missing", "sealed R10 parent archive is unavailable")
    documents: dict[str, Any] = {}
    for role, (path, digest) in R10_ARCHIVE_MANIFESTS.items():
        if not path.is_file() or path.is_symlink() or sha256_file(path) != digest:
            _fail("parent_archive_drift", f"R10 {role} manifest identity differs")
        documents[role] = strict_load_json(path)
    if (
        not R10_CLAIM_PATH.is_file()
        or R10_CLAIM_PATH.is_symlink()
        or sha256_file(R10_CLAIM_PATH) != R10_CLAIM_SHA256
    ):
        _fail("parent_claim_drift", "R10 parent-consumption claim identity differs")
    claim = strict_load_json(R10_CLAIM_PATH)
    if (
        claim.get("state") != "TRANSITION_CLAIMED"
        or claim.get("intended_child_generation") != CURRENT_GENERATION
        or claim.get("transition_id") != R10_TRANSITION_ID
        or claim.get("no_rollback") is not True
        or claim.get("parent_lock") != {
            "generation": R9_CHILD_GENERATION,
            "lock_id": R10_PARENT_LOCK_ID,
            "body_sha256": R10_PARENT_LOCK_BODY_SHA256,
            "raw_sha256": R10_PARENT_LOCK_RAW_SHA256,
        }
        or claim.get("finding", {}).get("id") != "S10-R9-SCHEMA-001"
        or claim.get("finding", {}).get("verdict") != "CHANGES_REQUIRED"
    ):
        _fail("parent_claim_drift", "R10 parent-consumption claim semantics differ")
    if sorted(item.name for item in R10_CLAIM_PATH.parent.iterdir()) != [
        f"{R10_PARENT_LOCK_ID}.json"
    ]:
        _fail("lineage_sibling", "R10 parent has multiple consumption claims")
    closure = documents["closure"]
    failure = documents["failure"]
    absence = documents["absence"]
    rehash = documents["rehash"]
    seal = documents["seal"]
    if (
        closure.get("archive_root") != _rel(R10_ARCHIVE_ROOT)
        or closure.get("transition_id") != R10_TRANSITION_ID
        or closure.get("claim")
        != {
            "path": _rel(R10_CLAIM_PATH),
            "raw_sha256": R10_CLAIM_SHA256,
            "state": "TRANSITION_CLAIMED",
        }
    ):
        _fail("parent_archive_drift", "R10 closure identity differs")
    expected_parent = {
        "archive_path": _rel(R10_PARENT_LOCK_PATH),
        "body_sha256": R10_PARENT_LOCK_BODY_SHA256,
        "generation": R9_CHILD_GENERATION,
        "lock_id": R10_PARENT_LOCK_ID,
        "raw_sha256": R10_PARENT_LOCK_RAW_SHA256,
        "state": "retired",
    }
    if closure.get("parent_lock") != expected_parent:
        _fail("wrong_parent_lock", "R10 closure identifies another parent")
    terminal = closure.get("terminal_refusal_after_claim")
    if (
        not isinstance(terminal, list)
        or [item.get("command") for item in terminal]
        != ["mapping", "smoke", "noise"]
        or any(item.get("exit_code") != 49 for item in terminal)
    ):
        _fail("parent_archive_drift", "R10 post-claim terminal refusal differs")
    raw_tree = closure.get("raw_tree")
    expected_raw_summary = {
        "archive_root": _rel(R10_PARENT_RAW_ROOT),
        "entry_count": R10_PARENT_RAW_TREE_ENTRY_COUNT,
        "regular_file_bytes": R10_PARENT_RAW_TREE_REGULAR_BYTES,
        "source_root": _rel(R10_ORIGINAL_PARENT_RAW_ROOT),
        "tree_canonical_sha256": R10_PARENT_RAW_TREE_SHA256,
    }
    if (
        not isinstance(raw_tree, dict)
        or {key: raw_tree.get(key) for key in expected_raw_summary}
        != expected_raw_summary
    ):
        _fail("parent_archive_drift", "R10 raw-tree summary differs")
    entries = raw_tree.get("entries")
    if (
        not isinstance(entries, list)
        or len(entries) != R10_PARENT_RAW_TREE_ENTRY_COUNT
        or canonical_sha256(entries) != R10_PARENT_RAW_TREE_SHA256
    ):
        _fail("parent_archive_drift", "R10 raw-tree ledger differs")
    verifier = failure.get("verifier_authority")
    verifier_map = {
        item.get("path"): item.get("raw_sha256")
        for item in verifier
    } if isinstance(verifier, list) else {}
    if (
        failure.get("classification") != "CHANGES_REQUIRED/strict_schema_defect"
        or failure.get("finding_id") != "S10-R9-SCHEMA-001"
        or failure.get("parent_lock", {}).get("lock_id") != R10_PARENT_LOCK_ID
        or verifier_map.get(
            "agent_run/260725-ductile-factorized-guidance-s0-s1-recovery/"
            "milestones/S10/r9-verifier-successor-002/schema-negative-matrix.json"
        )
        != "793ae1dc39d8710298d2d980395e706ea70d0b9e695ec431d8d37627c9ca5de7"
        or failure.get("scientific_branch", {}).get(
            "canonical_negative_remains_incident_evidence_only"
        )
        is not True
    ):
        _fail("parent_failure_missing", "R10 parent schema failure differs")
    if (
        absence.get("no_active_lock") is not True
        or any(item.get("absent") is not True for item in absence.get("checks", []))
    ):
        _fail("parent_failure_missing", "R10 parent absence boundary differs")
    if (
        rehash.get("raw_tree")
        != {
            "entry_count": R10_PARENT_RAW_TREE_ENTRY_COUNT,
            "membership_match": True,
            "metadata_and_bytes_match": True,
            "regular_file_bytes": R10_PARENT_RAW_TREE_REGULAR_BYTES,
            "tree_canonical_sha256": R10_PARENT_RAW_TREE_SHA256,
        }
        or seal.get("state") != "PARENT_ARCHIVE_SEALED/NO_ACTIVE_LOCK"
        or seal.get("transition_id") != R10_TRANSITION_ID
        or seal.get("raw_tree")
        != {
            "entry_count": R10_PARENT_RAW_TREE_ENTRY_COUNT,
            "regular_file_bytes": R10_PARENT_RAW_TREE_REGULAR_BYTES,
            "tree_canonical_sha256": R10_PARENT_RAW_TREE_SHA256,
        }
    ):
        _fail("parent_archive_drift", "R10 archive seal/full-rehash differs")
    for item in [
        *closure.get("bound_governing_and_verifier_snapshots", []),
        *closure.get("retired_parent_files", []),
    ]:
        _verify_archive_file(item, role="R10 preserved")
    if (
        not R10_PARENT_LOCK_PATH.is_file()
        or sha256_file(R10_PARENT_LOCK_PATH) != R10_PARENT_LOCK_RAW_SHA256
    ):
        _fail("wrong_parent_lock", "retired successor-002 lock bytes differ")
    parent = strict_load_json(R10_PARENT_LOCK_PATH)
    if (
        parent.get("generation") != R9_CHILD_GENERATION
        or parent.get("body_sha256") != R10_PARENT_LOCK_BODY_SHA256
        or parent.get("lock_id") != R10_PARENT_LOCK_ID
        or parent.get("evidence_reuse") is not False
        or parent.get("parent_lock") != _r9_parent_reference()
        or parent.get("recovery_authority", {}).get("raw_sha256")
        != R9_RECOVERY_AUTHORITY_SHA256
    ):
        _fail("wrong_parent_lock", "retired successor-002 lock identity differs")
    archived_authority = R10_PARENT_RAW_ROOT / "authority/r9-adjudication.md"
    if (
        not archived_authority.is_file()
        or archived_authority.is_symlink()
        or sha256_file(archived_authority) != R9_RECOVERY_AUTHORITY_SHA256
    ):
        _fail("recovery_authority_mismatch", "archived R9 authority differs")
    if R10_ORIGINAL_PARENT_RAW_ROOT.exists():
        _fail("parent_reactivation", "retired successor-002 raw root was reactivated")
    if LOCK_PATH.exists():
        active = strict_load_json(LOCK_PATH)
        if (
            active.get("generation") != CURRENT_GENERATION
            or active.get("parent_lock") != _r10_parent_reference()
        ):
            _fail("parent_reactivation", "canonical lock is not successor-003")
    archive_identities = {
        R8_PARENT_LOCK_RAW_SHA256,
        R9_PARENT_LOCK_RAW_SHA256,
        R10_PARENT_LOCK_RAW_SHA256,
        R8_PARENT_RAW_TREE_SHA256,
        R9_PARENT_RAW_TREE_SHA256,
        R10_PARENT_RAW_TREE_SHA256,
    }
    if len(archive_identities) != 6:
        _fail("lineage_reuse", "ancestor lock/raw identities are not unique")
    if rehash_raw_tree:
        recorded_paths = sorted(item["archive_path"] for item in entries)
        if recorded_paths != _archive_paths(R10_PARENT_RAW_ROOT):
            _fail("parent_archive_drift", "R10 raw-tree membership differs")
        for item in entries:
            _verify_archive_file(item, role="R10 raw tree")
    return _r10_parent_reference()


def _verify_successor_fields(document: Mapping[str, Any], *, role: str) -> None:
    if (
        document.get("generation") != CURRENT_GENERATION
        or document.get("evidence_reuse") is not False
        or document.get("parent_lock") != _r10_parent_reference()
    ):
        _fail("successor_lifecycle_mismatch", f"{role} successor fields differ")
    authority = document.get("recovery_authority")
    if (
        not isinstance(authority, dict)
        or set(authority) != {"path", "raw_sha256"}
        or authority["raw_sha256"] != R10_RECOVERY_AUTHORITY_SHA256
    ):
        _fail("recovery_authority_mismatch", f"{role} R10 authority differs")
    path = ROOT / authority["path"]
    if (
        not path.is_file()
        or path.is_symlink()
        or sha256_file(path) != R10_RECOVERY_AUTHORITY_SHA256
        or path.name != "r10-adjudication.md"
        or path.parent.name != "authority"
    ):
        _fail("recovery_authority_mismatch", f"{role} R10 snapshot differs")
    _assert_scratch_root(path.parents[1])


def _schema() -> Mapping[str, Any]:
    return strict_load_json(SCHEMA_PATH)


def _validate(document: Mapping[str, Any], *, context: str) -> None:
    validate_schema_document(document, _schema(), context=context)


def _git(*args: str, text: bool = True) -> str | bytes:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    )
    if proc.returncode:
        stderr = proc.stderr if text else proc.stderr.decode("utf-8", "replace")
        _fail("git_object_error", f"git {' '.join(args)}: {stderr.strip()}")
    return proc.stdout


def _git_oid(spec: str) -> str:
    oid = str(_git("rev-parse", spec)).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", oid):
        _fail("git_object_error", f"invalid object id for {spec}: {oid}")
    return oid


def _blob_bytes(oid: str) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{40}", oid):
        _fail("git_object_error", f"invalid blob id: {oid}")
    return bytes(_git("cat-file", "blob", oid, text=False))


def _blob_bytes_batch(entries: Sequence[Mapping[str, str]]) -> dict[str, bytes]:
    oids = list(dict.fromkeys(item["blob"] for item in entries))
    proc = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=ROOT,
        input=("".join(f"{oid}\n" for oid in oids)).encode("ascii"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        _fail(
            "git_object_error",
            f"git cat-file --batch failed: {proc.stderr.decode('utf-8', 'replace')}",
        )
    result: dict[str, bytes] = {}
    offset = 0
    for requested in oids:
        newline = proc.stdout.find(b"\n", offset)
        if newline < 0:
            _fail("git_object_error", "truncated git cat-file batch header")
        header = proc.stdout[offset:newline].decode("ascii").split()
        if len(header) != 3 or header[0] != requested or header[1] != "blob":
            _fail("git_object_error", f"unexpected git cat-file header: {header}")
        size = int(header[2])
        start = newline + 1
        end = start + size
        if end >= len(proc.stdout) or proc.stdout[end : end + 1] != b"\n":
            _fail("git_object_error", f"truncated git blob {requested}")
        result[requested] = proc.stdout[start:end]
        offset = end + 1
    if offset != len(proc.stdout):
        _fail("git_object_error", "unexpected trailing git cat-file bytes")
    return result


def _resolve_authorities() -> dict[str, Any]:
    ductile = _git_oid(f"{DUCTILE_REF}^{{commit}}")
    geko = _git_oid(f"{GEKO_REF}^{{commit}}")
    if ductile != DUCTILE_COMMIT:
        _fail("authority_mismatch", f"Ductile ref resolved to {ductile}")
    if geko != GEKO_COMMIT:
        _fail("authority_mismatch", f"GEKO ref resolved to {geko}")
    merge_base = str(_git("merge-base", ductile, geko)).strip()
    if merge_base != MERGE_BASE:
        _fail("authority_mismatch", f"merge base resolved to {merge_base}")
    trees = {
        path: _git_oid(f"{ductile}:{path}")
        for path in DUCTILE_TREES
    }
    if trees != DUCTILE_TREES:
        _fail("authority_mismatch", f"Ductile tree mismatch: {trees}")
    geko_tree = _git_oid(
        f"{geko}:projects/hipblaslt/utilities/geko"
    )
    if geko_tree != GEKO_TREE:
        _fail("authority_mismatch", f"GEKO utility tree is {geko_tree}")
    template_blob = _git_oid(f"{geko}:{TEMPLATE_PATH}")
    template = _blob_bytes(template_blob)
    if template_blob != TEMPLATE_BLOB:
        _fail("authority_mismatch", f"template blob is {template_blob}")
    if hashlib.sha256(template).hexdigest() != TEMPLATE_SHA256:
        _fail("authority_mismatch", "template raw SHA-256 mismatch")
    return {
        "ductile": {
            "ref": DUCTILE_REF,
            "commit": ductile,
            "commit_tree": _git_oid(f"{ductile}^{{tree}}"),
            "trees": trees,
        },
        "geko": {
            "ref": GEKO_REF,
            "commit": geko,
            "commit_tree": _git_oid(f"{geko}^{{tree}}"),
            "utility_tree": geko_tree,
            "template_path": TEMPLATE_PATH,
            "template_blob": template_blob,
            "template_raw_sha256": TEMPLATE_SHA256,
        },
        "merge_base": merge_base,
    }


def _tree_entries(commit: str, prefixes: Sequence[str]) -> list[dict[str, str]]:
    raw = bytes(
        _git(
            "ls-tree",
            "-rz",
            commit,
            "--",
            *prefixes,
            text=False,
        )
    )
    entries = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, path_bytes = record.split(b"\t", 1)
        mode, object_type, oid = meta.decode("ascii").split()
        path = path_bytes.decode("utf-8")
        if object_type != "blob" or mode not in {"100644", "100755", "120000"}:
            _fail("unexpected_git_entry", f"{mode} {object_type} {path}")
        if not any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes):
            _fail("unexpected_path", f"tree entry outside requested prefixes: {path}")
        entries.append({"path": path, "mode": mode, "blob": oid})
    if not entries:
        _fail("git_object_error", f"no files for {commit}:{prefixes}")
    return sorted(entries, key=lambda item: item["path"].encode("utf-8"))


def _safe_relative_path(value: str, *, context: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith("/")
        or "\x00" in value
        or posixpath.normpath(value) != value
        or value in {".", ".."}
        or value.startswith("../")
    ):
        _fail("unsafe_path", f"{context}: {value!r}")
    return value


def _directory_closure(paths: Iterable[str]) -> list[str]:
    closure: set[str] = set()
    for value in paths:
        relative = _safe_relative_path(value, context="source path")
        parent = posixpath.dirname(relative)
        while parent:
            closure.add(parent)
            parent = posixpath.dirname(parent)
    return sorted(closure, key=lambda item: item.encode("utf-8"))


def _resolve_source_symlinks(
    entries: Sequence[Mapping[str, str]],
    blob_cache: Mapping[str, bytes] | None = None,
) -> list[dict[str, str]]:
    blobs = blob_cache or {}

    def blob(oid: str) -> bytes:
        return blobs[oid] if oid in blobs else _blob_bytes(oid)

    entry_map = {item["path"]: item for item in entries}
    links = [item for item in entries if item["mode"] == "120000"]
    if len(links) != DUCTILE_SYMLINK_COUNT:
        _fail(
            "symlink_inventory_mismatch",
            f"expected {DUCTILE_SYMLINK_COUNT} Ductile links, found {len(links)}",
        )
    inventory = []
    for item in links:
        source_path = _safe_relative_path(item["path"], context="symlink source")
        link_bytes = blob(item["blob"])
        try:
            link_text = link_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise S10Error(str(exc), code="symlink_target_invalid") from exc
        if (
            not link_text
            or link_text.startswith("/")
            or "\x00" in link_text
            or "\n" in link_text
            or "\r" in link_text
        ):
            _fail("symlink_target_invalid", f"impure link bytes at {source_path}")
        target_path = posixpath.normpath(
            posixpath.join(posixpath.dirname(source_path), link_text)
        )
        if (
            target_path.startswith("../")
            or target_path == ".."
            or not target_path.startswith("projects/hipblaslt/")
        ):
            _fail("symlink_escape", f"{source_path} -> {link_text}")
        if (
            target_path == "projects/hipblaslt/utilities/geko"
            or target_path.startswith("projects/hipblaslt/utilities/geko/")
        ):
            _fail("symlink_overlay_target", f"{source_path} -> {target_path}")
        target = entry_map.get(target_path)
        if target is None:
            _fail("symlink_target_missing", f"{source_path} -> {target_path}")
        if target["mode"] == "120000":
            _fail("symlink_chain", f"{source_path} -> {target_path}")
        if target["mode"] != "100644":
            _fail("symlink_target_nonregular", f"{source_path} -> {target_path}")
        target_bytes = blob(target["blob"])
        inventory.append(
            {
                "path": source_path,
                "mode": item["mode"],
                "blob": item["blob"],
                "link_text": link_text,
                "link_sha256": hashlib.sha256(link_bytes).hexdigest(),
                "target_path": target_path,
                "target_mode": target["mode"],
                "target_blob": target["blob"],
                "target_raw_sha256": hashlib.sha256(target_bytes).hexdigest(),
            }
        )
    inventory.sort(key=lambda item: item["path"].encode("utf-8"))
    inventory_hash = canonical_sha256(inventory)
    if inventory_hash != DUCTILE_SYMLINK_INVENTORY_SHA256:
        _fail(
            "symlink_inventory_mismatch",
            f"{inventory_hash} != {DUCTILE_SYMLINK_INVENTORY_SHA256}",
        )
    return inventory


def _ensure_real_directories(root: Path, relative_parent: str) -> None:
    current = root
    if not relative_parent:
        return
    for component in relative_parent.split("/"):
        current = current / component
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            try:
                os.mkdir(current, 0o755)
            except FileExistsError:
                info = os.lstat(current)
                if not stat.S_ISDIR(info.st_mode):
                    _fail("symlink_ancestor", f"non-directory ancestor: {current}")
            else:
                info = os.lstat(current)
        if not stat.S_ISDIR(info.st_mode):
            _fail("symlink_ancestor", f"non-directory ancestor: {current}")


def _exclusive_write_blob(
    root: Path,
    entry: Mapping[str, str],
    blob_cache: Mapping[str, bytes] | None = None,
) -> None:
    relative = _safe_relative_path(entry["path"], context="blob path")
    _ensure_real_directories(root, posixpath.dirname(relative))
    target = root / relative
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(target, flags, 0o600)
    except FileExistsError:
        _fail("materialization_collision", f"target already exists: {target}")
    data = (
        blob_cache[entry["blob"]]
        if blob_cache is not None
        else _blob_bytes(entry["blob"])
    )
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(target, 0o755 if entry["mode"] == "100755" else 0o644)
    except BaseException:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise


def _integration_semantic_manifest(
    ductile_entries: Sequence[Mapping[str, str]],
    geko_entries: Sequence[Mapping[str, str]],
    symlinks: Sequence[Mapping[str, str]],
    blob_cache: Mapping[str, bytes] | None = None,
) -> dict[str, Any]:
    origins = {
        **{item["path"]: "ductile" for item in ductile_entries},
        **{item["path"]: "geko" for item in geko_entries},
    }
    inventory_by_path = {item["path"]: item for item in symlinks}
    combined = sorted(
        [*ductile_entries, *geko_entries],
        key=lambda item: item["path"].encode("utf-8"),
    )
    entries = []
    for item in combined:
        data = (
            blob_cache[item["blob"]]
            if blob_cache is not None
            else _blob_bytes(item["blob"])
        )
        kind = "symlink" if item["mode"] == "120000" else "regular"
        record: dict[str, Any] = {
            "path": item["path"],
            "origin": origins[item["path"]],
            "source_mode": item["mode"],
            "blob": item["blob"],
            "kind": kind,
            "raw_sha256": hashlib.sha256(data).hexdigest(),
        }
        if kind == "symlink":
            record["resolution"] = inventory_by_path[item["path"]]
        entries.append(record)
    directories = _directory_closure(item["path"] for item in combined)
    body = {
        "schema_version": "1.0.0",
        "kind": "s10_integration_semantic_manifest",
        "materialization_policy": MATERIALIZATION_POLICY,
        "ductile_commit": DUCTILE_COMMIT,
        "geko_commit": GEKO_COMMIT,
        "counts": {
            "ductile_regular": DUCTILE_REGULAR_COUNT,
            "ductile_symlink": DUCTILE_SYMLINK_COUNT,
            "geko_regular": GEKO_REGULAR_COUNT,
            "regular": INTEGRATION_REGULAR_COUNT,
            "symlink": DUCTILE_SYMLINK_COUNT,
            "leaves": INTEGRATION_LEAF_COUNT,
            "directories": len(directories),
        },
        "directory_closure": directories,
        "directory_closure_sha256": canonical_sha256(directories),
        "resolution_inventory": list(symlinks),
        "resolution_inventory_sha256": canonical_sha256(symlinks),
        "entries": entries,
    }
    return {**body, "manifest_sha256": canonical_sha256(body)}


def _scan_integration(root: Path, semantic: Mapping[str, Any]) -> dict[str, Any]:
    root_info = os.lstat(root)
    if not stat.S_ISDIR(root_info.st_mode):
        _fail("integration_drift", f"integration root is not a directory: {root}")
    expected = {item["path"]: item for item in semantic["entries"]}
    expected_directories = set(semantic["directory_closure"])
    observed_directories: set[str] = set()
    observed: list[dict[str, Any]] = []

    def walk(directory: Path, relative: str = "") -> None:
        try:
            children = sorted(
                os.scandir(directory), key=lambda item: item.name.encode("utf-8")
            )
        except OSError as exc:
            raise S10Error(str(exc), code="integration_drift") from exc
        for child in children:
            child_relative = f"{relative}/{child.name}" if relative else child.name
            info = child.stat(follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                observed_directories.add(child_relative)
                walk(Path(child.path), child_relative)
                continue
            item = expected.get(child_relative)
            if item is None:
                if child_relative in expected_directories and stat.S_ISLNK(info.st_mode):
                    _fail("symlink_ancestor", child_relative)
                _fail("unexpected_path", f"unexpected integration leaf: {child_relative}")
            if stat.S_ISREG(info.st_mode):
                if item["kind"] != "regular":
                    _fail("expected_link_is_regular", child_relative)
                if info.st_nlink != 1:
                    _fail("hardlink_rejected", child_relative)
                filesystem_mode = "100755" if info.st_mode & 0o111 else "100644"
                if filesystem_mode != item["source_mode"]:
                    _fail("mode_mismatch", f"{child_relative}: {filesystem_mode}")
                raw_hash = sha256_file(Path(child.path))
                if raw_hash != item["raw_sha256"]:
                    _fail("integration_drift", f"content mismatch: {child_relative}")
                observed.append(
                    {
                        "path": child_relative,
                        "kind": "regular",
                        "source_mode": item["source_mode"],
                        "filesystem_mode": filesystem_mode,
                        "raw_sha256": raw_hash,
                    }
                )
                continue
            if stat.S_ISLNK(info.st_mode):
                if item["kind"] != "symlink":
                    _fail("expected_regular_is_link", child_relative)
                if info.st_nlink != 1:
                    _fail("hardlink_rejected", child_relative)
                resolution = item["resolution"]
                link_text = os.readlink(child.path)
                if link_text != resolution["link_text"]:
                    _fail("symlink_target_mismatch", child_relative)
                target = root / resolution["target_path"]
                target_info = os.lstat(target)
                if stat.S_ISLNK(target_info.st_mode):
                    _fail("expected_regular_is_link", resolution["target_path"])
                if not stat.S_ISREG(target_info.st_mode):
                    _fail("symlink_target_nonregular", child_relative)
                if target_info.st_nlink != 1:
                    _fail("hardlink_rejected", resolution["target_path"])
                followed = os.stat(child.path)
                if (followed.st_dev, followed.st_ino) != (
                    target_info.st_dev,
                    target_info.st_ino,
                ):
                    _fail("symlink_target_mismatch", child_relative)
                if sha256_file(target) != resolution["target_raw_sha256"]:
                    _fail("symlink_target_mismatch", child_relative)
                observed.append(
                    {
                        "path": child_relative,
                        "kind": "symlink",
                        "source_mode": "120000",
                        "link_text": link_text,
                        "link_sha256": hashlib.sha256(
                            os.fsencode(link_text)
                        ).hexdigest(),
                        "target_path": resolution["target_path"],
                        "target_raw_sha256": resolution["target_raw_sha256"],
                    }
                )
                continue
            _fail("special_node_rejected", child_relative)

    walk(root)
    if observed_directories != expected_directories:
        _fail(
            "directory_closure_mismatch",
            f"missing={sorted(expected_directories-observed_directories)[:5]} "
            f"extra={sorted(observed_directories-expected_directories)[:5]}",
        )
    if {item["path"] for item in observed} != set(expected):
        missing = sorted(set(expected) - {item["path"] for item in observed})
        _fail("materialization_incomplete", f"missing leaves: {missing[:5]}")
    regular_count = sum(item["kind"] == "regular" for item in observed)
    symlink_count = sum(item["kind"] == "symlink" for item in observed)
    if (
        len(observed) != INTEGRATION_LEAF_COUNT
        or regular_count != INTEGRATION_REGULAR_COUNT
        or symlink_count != DUCTILE_SYMLINK_COUNT
    ):
        _fail("materialization_incomplete", "integration closure cardinality mismatch")
    observed.sort(key=lambda item: item["path"].encode("utf-8"))
    return {
        "materialization_policy": MATERIALIZATION_POLICY,
        "manifest_sha256": semantic["manifest_sha256"],
        "directory_closure_sha256": canonical_sha256(
            sorted(observed_directories, key=lambda item: item.encode("utf-8"))
        ),
        "leaf_count": len(observed),
        "regular_count": regular_count,
        "symlink_count": symlink_count,
        "observed_sha256": canonical_sha256(observed),
    }


def _phase_seal(
    root: Path, semantic: Mapping[str, Any], phase: str
) -> dict[str, Any]:
    return {
        "phase": phase,
        "root": _rel(root),
        "audit": _scan_integration(root, semantic),
    }


def _materialize_integration(root: Path, authorities: Mapping[str, Any]) -> dict[str, Any]:
    if root.exists():
        _fail("already_exists", f"integration root already exists: {root}")
    root.mkdir(parents=True)
    ductile_prefixes = [
        "projects/hipblaslt",
        "cmake/modules",
        "shared/origami",
        "shared/stinkytofu",
    ]
    ductile_entries = _tree_entries(DUCTILE_COMMIT, ductile_prefixes)
    ductile_regular = [item for item in ductile_entries if item["mode"] != "120000"]
    if len(ductile_regular) != DUCTILE_REGULAR_COUNT:
        _fail("materialization_incomplete", "Ductile regular-file count mismatch")
    overlay_prefix = "projects/hipblaslt/utilities/geko"
    if any(
        item["path"] == overlay_prefix
        or item["path"].startswith(overlay_prefix + "/")
        for item in ductile_entries
    ):
        _fail("overlay_collision", f"Ductile destination exists: {overlay_prefix}")
    geko_entries = _tree_entries(GEKO_COMMIT, [overlay_prefix])
    if any(item["mode"] == "120000" for item in geko_entries):
        _fail("geko_symlink_rejected", "GEKO overlay contains a symlink")
    if len(geko_entries) != GEKO_REGULAR_COUNT:
        _fail("materialization_incomplete", "GEKO regular-file count mismatch")
    if len({item["path"] for item in [*ductile_entries, *geko_entries]}) != (
        len(ductile_entries) + len(geko_entries)
    ):
        _fail("overlay_collision", "Ductile and GEKO leaf collision")
    blob_cache = _blob_bytes_batch([*ductile_entries, *geko_entries])
    symlinks = _resolve_source_symlinks(ductile_entries, blob_cache)
    semantic = _integration_semantic_manifest(
        ductile_entries, geko_entries, symlinks, blob_cache
    )
    for entry in sorted(
        [*ductile_regular, *geko_entries],
        key=lambda item: item["path"].encode("utf-8"),
    ):
        _exclusive_write_blob(root, entry, blob_cache)
    for item in symlinks:
        _ensure_real_directories(root, posixpath.dirname(item["path"]))
        target = root / item["path"]
        try:
            os.symlink(item["link_text"], target)
        except FileExistsError:
            _fail("materialization_collision", f"link target exists: {target}")
    seal = _phase_seal(root, semantic, "after-materialization")
    wrapper = {
        "schema_version": "1.0.0",
        "kind": "s10_integration_run_manifest",
        "materialization_policy": MATERIALIZATION_POLICY,
        "root": _rel(root),
        "semantic_manifest": None,
        "phase_seals": [seal],
    }
    return {"semantic": semantic, "wrapper": wrapper}


def _serialize_input(document: Mapping[str, Any]) -> bytes:
    text = yaml.safe_dump(
        plain_value(document),
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=4096,
    )
    return text.encode("utf-8")


def _derive_input() -> tuple[bytes, dict[str, Any]]:
    raw = _blob_bytes(TEMPLATE_BLOB)
    if hashlib.sha256(raw).hexdigest() != TEMPLATE_SHA256:
        _fail("authority_mismatch", "template bytes drifted")
    config = strict_load_yaml(raw.decode("utf-8"), from_text=True)
    if not isinstance(config, dict):
        _fail("input_derivation_error", "template is not a mapping")
    source_keys = list(config)
    preserved = {
        "TRANSA": "N",
        "TRANSB": "N",
        "DataType": "B",
        "DestDataType": "B",
        "ComputeDataType": "S",
    }
    for key, expected in preserved.items():
        if config.get(key) != expected:
            _fail("input_derivation_error", f"{key} != {expected}")
    sizes = config.get("Sizes")
    if (
        not isinstance(sizes, list)
        or len(sizes) != 17
        or any(not isinstance(size, list) or len(size) != 4 for size in sizes)
    ):
        _fail("input_derivation_error", "template must contain 17 four-field sizes")
    source_sizes = copy.deepcopy(sizes)
    config["ARCH"] = "gfx942"
    config["StreamK"] = False
    config["ONE_SIZE_PER_CONFIG"] = False
    config["GA"] = True
    config["SIZE_OPTION"] = 0
    config["CLUSTER"] = 0
    for key, expected in preserved.items():
        if config[key] != expected:
            _fail("input_derivation_error", f"preserved field changed: {key}")
    if config["Sizes"] != source_sizes:
        _fail("input_derivation_error", "size rows/order changed")
    derived = _serialize_input(config)
    reparsed = strict_load_yaml(derived.decode("utf-8"), from_text=True)
    if reparsed != config or list(reparsed) != list(config):
        _fail("input_derivation_error", "fixed serializer round-trip mismatch")
    resolved_defaults = {
        **copy.deepcopy(config),
        "MACROTILE_OPT": False,
        "MT_DU": None,
        "USE_HEURISTICS": False,
        "MI_FILTER": 2,
        "EPILOGUES": True,
        "GA_VALIDATION_PROFILE": 1,
        "CMS": False,
        "CMS_PRIORITY": False,
        "CUs": 304,
        "XCC": 8,
        "WGMUnit": 8,
        "MAX_NUM_KERNELS_PER_CONFIG": sys.maxsize,
    }
    return derived, {
        "source_keys": source_keys,
        "derived_keys": list(config),
        "raw_sizes": source_sizes,
        "raw_size_count": len(source_sizes),
        "distinct_size_count": len({tuple(item) for item in source_sizes}),
        "overrides": {
            "ARCH": "gfx942",
            "StreamK": False,
            "ONE_SIZE_PER_CONFIG": False,
        },
        "materialized_semantics": {"GA": True, "SIZE_OPTION": 0, "CLUSTER": 0},
        "preserved": preserved,
        "cleared_environment": list(ENV_UPDATABLE_KEYS),
        "serializer": {
            "library": "PyYAML.safe_dump",
            "sort_keys": False,
            "default_flow_style": False,
            "allow_unicode": True,
            "width": 4096,
        },
        "resolved_config": resolved_defaults,
        "derived_raw_sha256": hashlib.sha256(derived).hexdigest(),
    }


def _base_env() -> dict[str, str]:
    keep = (
        "PATH",
        "LD_LIBRARY_PATH",
        "LIBRARY_PATH",
        "CPATH",
        "CMAKE_PREFIX_PATH",
        "ROCM_PATH",
        "TMPDIR",
        "LANG",
        "LC_ALL",
    )
    env = {key: os.environ[key] for key in keep if key in os.environ}
    for key in ENV_UPDATABLE_KEYS:
        env.pop(key, None)
    env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "GIT_CEILING_DIRECTORIES": str(CONTAINER_REPO),
        }
    )
    return env


def _safe_env_record(env: Mapping[str, str]) -> dict[str, str]:
    allowed = {
        "PATH",
        "LD_LIBRARY_PATH",
        "LIBRARY_PATH",
        "CPATH",
        "CMAKE_PREFIX_PATH",
        "ROCM_PATH",
        "TMPDIR",
        "LANG",
        "LC_ALL",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONHASHSEED",
        "GIT_CEILING_DIRECTORIES",
        "PYTHONPATH",
        "FETCHCONTENT_FULLY_DISCONNECTED",
        "HIPBLASLT_ENABLE_FETCH",
        "ORIGAMI_ENABLE_FETCH",
    }
    return {key: env[key] for key in sorted(env) if key in allowed}


def _run_logged(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    log_root: Path,
    name: str,
    check: bool = True,
) -> tuple[subprocess.CompletedProcess[bytes], dict[str, Any]]:
    log_root.mkdir(parents=True, exist_ok=True)
    stdout_path = log_root / f"{name}.stdout"
    stderr_path = log_root / f"{name}.stderr"
    if stdout_path.exists() or stderr_path.exists():
        _fail("already_exists", f"log target exists for {name}")
    started = _utc_now()
    proc = subprocess.run(
        list(argv),
        cwd=cwd,
        env=dict(env),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ended = _utc_now()
    atomic_write_bytes(stdout_path, proc.stdout)
    atomic_write_bytes(stderr_path, proc.stderr)
    os.chmod(stdout_path, 0o644)
    os.chmod(stderr_path, 0o644)
    record = {
        "argv": list(argv),
        "cwd": _rel(cwd),
        "environment": _safe_env_record(env),
        "started_at": started,
        "ended_at": ended,
        "exit_code": proc.returncode,
        "stdout": {
            "path": _rel(stdout_path),
            "raw_sha256": sha256_file(stdout_path),
            "bytes": stdout_path.stat().st_size,
        },
        "stderr": {
            "path": _rel(stderr_path),
            "raw_sha256": sha256_file(stderr_path),
            "bytes": stderr_path.stat().st_size,
        },
    }
    if check and proc.returncode:
        tail = proc.stderr.decode("utf-8", "replace")[-2000:]
        _fail("command_failed", f"{name} exit {proc.returncode}: {tail}")
    return proc, record


def _identity_command(
    argv: Sequence[str], *, cwd: Path, env: Mapping[str, str], log_root: Path, name: str
) -> dict[str, Any]:
    _, record = _run_logged(
        argv, cwd=cwd, env=env, log_root=log_root, name=name
    )
    return record


def _native_configure_argv(root: Path, build: Path) -> list[str]:
    nanobind_dir = SITE_PACKAGES / "nanobind/cmake"
    return [
        str(CMAKE),
        "-S",
        str(root / "projects/hipblaslt/tensilelite/rocisa"),
        "-B",
        str(build),
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_CXX_COMPILER={COMPILER}",
        f"-DPython_EXECUTABLE={PYTHON}",
        f"-DROCmCMakeBuildTools_DIR={ROCM_CMAKE}",
        f"-Dnanobind_DIR={nanobind_dir}",
        "-DROCM_PATH=/opt/rocm",
        "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
        "-DHIPBLASLT_ENABLE_FETCH=OFF",
        "-DORIGAMI_ENABLE_FETCH=OFF",
        "-DCMAKE_DISABLE_FIND_PACKAGE_stinkytofu=TRUE",
        "-DROCISA_INCLUDE_BUILD_INFO=ON",
    ]


def _native_build_argv(build: Path) -> list[str]:
    return [
        str(CMAKE),
        "--build",
        str(build),
        "--target",
        "_rocisa",
        "--parallel",
        "8",
    ]


def _parse_ldd_dependencies(raw: bytes) -> list[dict[str, Any]]:
    dependencies = []
    for line in raw.decode("utf-8", "replace").splitlines():
        match = re.search(r"=>\s+(/\S+)", line)
        if not match and line.lstrip().startswith("/"):
            match = re.match(r"\s*(/\S+)", line)
        if not match:
            continue
        dep = Path(match.group(1))
        resolved_dep = dep.resolve()
        dependencies.append(
            {
                "lexical_path": str(dep),
                "resolved_path": str(resolved_dep),
                "lexical_is_symlink": dep.is_symlink(),
                "raw_sha256": (
                    sha256_file(resolved_dep) if resolved_dep.is_file() else None
                ),
            }
        )
    return dependencies


def _parse_ldd_lexical_paths(raw: bytes) -> list[str]:
    paths = []
    for line in raw.decode("utf-8", "replace").splitlines():
        match = re.search(r"=>\s+(\S+)\s+\(", line)
        if not match:
            match = re.match(r"\s*(/\S+)\s+\(", line)
        if match:
            paths.append(match.group(1))
    return paths


def _build_native(root: Path, build: Path, log_root: Path, tag: str) -> dict[str, Any]:
    if build.exists():
        _fail("already_exists", f"native build exists: {build}")
    source = root / "projects/hipblaslt/tensilelite/rocisa"
    for required in (PYTHON, CMAKE, ROCM_CMAKE, COMPILER, SITE_PACKAGES):
        if not required.exists():
            _fail("native_tool_missing", f"required installed tool is absent: {required}")
    nanobind_dir = SITE_PACKAGES / "nanobind/cmake"
    if not nanobind_dir.is_dir():
        _fail("native_tool_missing", f"nanobind CMake package absent: {nanobind_dir}")
    env = _base_env()
    env.update(
        {
            "FETCHCONTENT_FULLY_DISCONNECTED": "ON",
            "HIPBLASLT_ENABLE_FETCH": "OFF",
            "ORIGAMI_ENABLE_FETCH": "OFF",
        }
    )
    configure = _native_configure_argv(root, build)
    _, configure_record = _run_logged(
        configure,
        cwd=root,
        env=env,
        log_root=log_root,
        name=f"{tag}-native-configure",
    )
    if any(path.name == "_deps" for path in build.rglob("_deps")):
        _fail("network_fetch_detected", f"_deps created under {build}")
    build_argv = _native_build_argv(build)
    _, build_record = _run_logged(
        build_argv,
        cwd=root,
        env=env,
        log_root=log_root,
        name=f"{tag}-native-build",
    )
    if any(path.name == "_deps" for path in build.rglob("_deps")):
        _fail("network_fetch_detected", f"_deps created under {build}")
    # Raw logs are scanned directly; references to FetchContent variables are
    # allowed, but evidence of download/clone/populate is not.
    fetch_re = re.compile(
        r"(Cloning into|Performing download|Downloading|git clone|Fetching content)",
        re.IGNORECASE,
    )
    for record in (configure_record, build_record):
        for channel in ("stdout", "stderr"):
            text = (ROOT / record[channel]["path"]).read_text(
                encoding="utf-8", errors="replace"
            )
            if fetch_re.search(text):
                _fail("network_fetch_detected", f"fetch evidence in {record[channel]['path']}")
    binaries = sorted((build / "rocisa").glob("_rocisa*.so"))
    if len(binaries) != 1:
        _fail("native_lineage_mismatch", f"expected one _rocisa, found {len(binaries)}")
    binary_lexical = binaries[0]
    binary_info = os.lstat(binary_lexical)
    if not stat.S_ISREG(binary_info.st_mode) or binary_info.st_nlink != 1:
        _fail("native_lineage_mismatch", "_rocisa is not an exclusive regular file")
    binary = binary_lexical.resolve()
    if build.resolve() not in binary.parents:
        _fail("native_lineage_mismatch", f"binary outside fresh build: {binary}")
    build_info = build / "rocisa/_build_info.py"
    if (
        not build_info.is_file()
        or build_info.is_symlink()
        or os.lstat(build_info).st_nlink != 1
    ):
        _fail("native_lineage_mismatch", "_build_info.py absent")
    build_info_text = build_info.read_text(encoding="utf-8")
    if str(root) not in build_info_text or str(ROOT / "projects") in build_info_text:
        _fail("native_lineage_mismatch", "_build_info source identity is not fresh root")
    ldd_proc, ldd_record = _run_logged(
        ["ldd", str(binary)],
        cwd=root,
        env=env,
        log_root=log_root,
        name=f"{tag}-native-ldd",
    )
    dependencies = _parse_ldd_dependencies(ldd_proc.stdout)
    stinky = [
        item
        for item in dependencies
        if "stinkytofu" in item["lexical_path"]
        or "stinkytofu" in item["resolved_path"]
    ]
    if not stinky or any(
        build.resolve() not in Path(item["resolved_path"]).parents for item in stinky
    ):
        _fail("native_lineage_mismatch", "stinkytofu dependency is not source-built")
    identities = {
        "cmake": _identity_command(
            [str(CMAKE), "--version"],
            cwd=root,
            env=env,
            log_root=log_root,
            name=f"{tag}-cmake-version",
        ),
        "compiler": _identity_command(
            [str(COMPILER), "--version"],
            cwd=root,
            env=env,
            log_root=log_root,
            name=f"{tag}-compiler-version",
        ),
        "python": _identity_command(
            [str(PYTHON), "-S", "--version"],
            cwd=root,
            env=env,
            log_root=log_root,
            name=f"{tag}-python-version",
        ),
    }
    return {
        "source_trees": DUCTILE_TREES,
        "configure": configure_record,
        "build": build_record,
        "identities": identities,
        "binary": {"path": _rel(binary), "raw_sha256": sha256_file(binary)},
        "build_info": {
            "path": _rel(build_info),
            "raw_sha256": sha256_file(build_info),
        },
        "dependency_probe": ldd_record,
        "dependencies": dependencies,
        "fetch_detected": False,
        "deps_directory_present": False,
        "installed_rocisa_used": False,
    }


def _python_path(root: Path, build: Path) -> list[Path]:
    return [
        build,
        root / "projects/hipblaslt/tensilelite",
        root / "projects/hipblaslt/utilities/geko",
        SITE_PACKAGES,
    ]


def _output_manifest(root: Path) -> list[dict[str, Any]]:
    entries = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().encode()):
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode):
            _fail("symlink_rejected", f"output symlink: {path}")
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            _fail("special_node_rejected", f"output special node: {path}")
        if info.st_nlink != 1:
            _fail("hardlink_rejected", f"output hardlink: {path}")
        if path.is_file():
            entries.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "mode": "100755" if info.st_mode & 0o111 else "100644",
                    "bytes": info.st_size,
                    "raw_sha256": sha256_file(path),
                }
            )
    return entries


def _module_probe_code() -> str:
    return r"""
import hashlib, importlib, json
mods = [
    "rocisa", "rocisa._rocisa", "Tensile", "Tensile.LibraryIO",
    "Tensile.backends.ductile_backend", "Tensile.ductile.algorithm.ga",
    "Tensile.ductile.core.space", "geko",
    "geko.config_generator.config_generator",
    "geko.config_generator.load_input_config",
]
out = {}
for name in mods:
    mod = importlib.import_module(name)
    path = getattr(mod, "__file__", None)
    if not path:
        raise RuntimeError("module_without_file:" + name)
    with open(path, "rb") as stream:
        digest = hashlib.sha256(stream.read()).hexdigest()
    out[name] = {"path": path, "raw_sha256": digest}
print(json.dumps(out, sort_keys=True, separators=(",", ":")))
"""


def _generation_argv(
    root: Path,
    derived_input: Path,
    output: Path,
) -> list[str]:
    return [
        str(PYTHON),
        "-S",
        str(root / "projects/hipblaslt/utilities/geko/scripts/config_generator.py"),
        "--hipblaslt",
        str(root / "projects/hipblaslt"),
        "--config",
        str(derived_input),
        "--outputPath",
        str(output),
        "--no-shell-scripts",
        "--verbose",
        "0",
    ]


def _generate(
    root: Path,
    build: Path,
    derived_input: Path,
    generation_root: Path,
    log_root: Path,
    tag: str,
) -> dict[str, Any]:
    if generation_root.exists():
        _fail("already_exists", f"generation root exists: {generation_root}")
    generation_root.mkdir(parents=True)
    output = generation_root / "out"
    paths = _python_path(root, build)
    env = _base_env()
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in paths)
    argv = _generation_argv(root, derived_input, output)
    _, command = _run_logged(
        argv,
        cwd=root,
        env=env,
        log_root=log_root,
        name=f"{tag}-generation",
    )
    if command["exit_code"] != 0:
        _fail("command_failed", f"{tag} generation failed")
    probe_proc, probe = _run_logged(
        [str(PYTHON), "-S", "-c", _module_probe_code()],
        cwd=root,
        env=env,
        log_root=log_root,
        name=f"{tag}-module-probe",
    )
    try:
        imports = json.loads(probe_proc.stdout)
    except json.JSONDecodeError as exc:
        raise S10Error(str(exc), code="forbidden_import") from exc
    allowed_roots = [path.resolve() for path in paths]
    for name, item in imports.items():
        imported = Path(item["path"]).resolve()
        if not any(imported == base or base in imported.parents for base in allowed_roots):
            _fail("forbidden_import", f"{name} imported from {imported}")
        if name.startswith("Tensile") and (root / "projects/hipblaslt/tensilelite").resolve() not in imported.parents:
            _fail("forbidden_import", f"{name} did not use pinned TensileLite")
        if name.startswith("geko") and (root / "projects/hipblaslt/utilities/geko").resolve() not in imported.parents:
            _fail("forbidden_import", f"{name} did not use pinned GEKO")
        if name.startswith("rocisa") and build.resolve() not in imported.parents:
            _fail("forbidden_import", f"{name} did not use fresh rocisa")
    manifest = _output_manifest(generation_root)
    return {
        "command": command,
        "module_probe": probe,
        "imports": imports,
        "python_path_order": [_rel(path) if ROOT in path.resolve().parents else str(path) for path in paths],
        "output_manifest": manifest,
        "output_manifest_sha256": canonical_sha256(manifest),
    }


def _raw_document(path: Path) -> Mapping[str, Any]:
    document = strict_load_yaml(path)
    if not isinstance(document, dict):
        _fail("qualifying_yaml_count", f"{path} is not a mapping")
    return document


def _extract_raw_fields(document: Mapping[str, Any]) -> dict[str, Any]:
    try:
        backend = document["Backend"]
        problems = document["BenchmarkProblems"]
        if len(problems) != 1 or len(problems[0]) != 2:
            raise KeyError("BenchmarkProblems cardinality")
        problem_type, params = problems[0]
        fork_items = params["ForkParameters"]
        final = params["BenchmarkFinalParameters"]
        size_items = final[0]["ProblemSizes"]
    except (KeyError, IndexError, TypeError) as exc:
        raise S10Error(str(exc), code="qualifying_yaml_count") from exc
    fork = {}
    for item in fork_items:
        if not isinstance(item, dict) or len(item) != 1:
            _fail("ductile_parity_mismatch", "ForkParameters item is not singleton")
        key, value = next(iter(item.items()))
        if key in fork:
            _fail("duplicate_key", f"duplicate ForkParameters key {key}")
        fork[key] = value
    sizes = []
    for item in size_items:
        exact = item.get("Exact") if isinstance(item, dict) else None
        if (
            not isinstance(exact, list)
            or len(exact) != 4
            or any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in exact)
        ):
            _fail("ductile_parity_mismatch", f"invalid Exact size: {exact}")
        sizes.append(exact)
    groups = fork.pop("Groups", None)
    config = backend.get("Config", {}) if isinstance(backend, dict) else {}
    weights = config.get("weights")
    return {
        "architecture": document.get("LibraryLogic", {}).get("ArchitectureName"),
        "backend_name": backend.get("Name") if isinstance(backend, dict) else None,
        "data_type": problem_type.get("DataType"),
        "dest_data_type": problem_type.get("DestDataType"),
        "compute_data_type": problem_type.get("ComputeDataType"),
        "transpose_a": problem_type.get("TransposeA"),
        "transpose_b": problem_type.get("TransposeB"),
        "batched": problem_type.get("Batched"),
        "n_elements_to_validate": config.get("n_elements_to_validate"),
        "soo": config.get("soo"),
        "weights": weights,
        "groups": groups,
        "fork_parameters": fork,
        "sizes": sizes,
    }


def _is_qualifying_yaml(path: Path) -> bool:
    try:
        fields = _extract_raw_fields(_raw_document(path))
    except EvidenceValidationError:
        return False
    validation = fields["n_elements_to_validate"]
    return bool(
        fields["architecture"] == "gfx942"
        and fields["backend_name"] == "Ductile"
        and fields["data_type"] == "B"
        and fields["dest_data_type"] == "B"
        and fields["compute_data_type"] == "S"
        and fields["transpose_a"] is False
        and fields["transpose_b"] is False
        and fields["batched"] is True
        and isinstance(validation, int)
        and not isinstance(validation, bool)
        and validation > 0
        and isinstance(fields["groups"], list)
        and fields["groups"]
        and isinstance(fields["weights"], list)
        and fields["weights"]
        and isinstance(fields["soo"], bool)
        and len({tuple(item) for item in fields["sizes"]}) >= 3
    )


def _compare_generation_runs(
    generation_a: Mapping[str, Any],
    generation_b: Mapping[str, Any],
    root_a: Path,
    root_b: Path,
) -> tuple[Path, Path, list[dict[str, Any]]]:
    manifest_a = generation_a["output_manifest"]
    manifest_b = generation_b["output_manifest"]
    if manifest_a != manifest_b:
        _fail("generation_manifest_mismatch", "complete generation manifests differ")
    qualifying = [
        item for item in manifest_a
        if item["path"].endswith((".yaml", ".yml"))
        and _is_qualifying_yaml(root_a / item["path"])
    ]
    qualifying_b = [
        item for item in manifest_b
        if item["path"].endswith((".yaml", ".yml"))
        and _is_qualifying_yaml(root_b / item["path"])
    ]
    if len(qualifying) != 1 or len(qualifying_b) != 1:
        _fail(
            "qualifying_yaml_count",
            f"qualifying counts A={len(qualifying)} B={len(qualifying_b)}",
        )
    if qualifying[0]["path"] != qualifying_b[0]["path"]:
        _fail("generation_manifest_mismatch", "qualifying relative paths differ")
    path_a = root_a / qualifying[0]["path"]
    path_b = root_b / qualifying_b[0]["path"]
    if path_a.read_bytes() != path_b.read_bytes():
        _fail("generation_manifest_mismatch", "qualifying YAML bytes differ")
    return path_a, path_b, qualifying


def _typed_equal(left: Any, right: Any) -> bool:
    return canonical_json_bytes(left) == canonical_json_bytes(right)


def _ordered_update(
    base: Mapping[str, Any], updates: Iterable[tuple[str, Any]]
) -> dict[str, Any]:
    result = copy.deepcopy(dict(base))
    for key, value in updates:
        result[key] = copy.deepcopy(value)
    return result


def _strict_singleton_records(
    records: Any,
    *,
    context: str,
    expected_count: int | None = None,
) -> list[tuple[str, Any]]:
    if not isinstance(records, list) or (
        expected_count is not None and len(records) != expected_count
    ):
        _fail("raw_witness_mismatch", f"{context} cardinality mismatch")
    result = []
    names = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict) or len(record) != 1:
            _fail("raw_witness_mismatch", f"{context}[{index}] is not singleton")
        name, value = next(iter(record.items()))
        if not isinstance(name, str) or not name or name in names:
            _fail("duplicate_parameter", f"{context}[{index}] duplicate/invalid {name!r}")
        names.add(name)
        result.append((name, copy.deepcopy(value)))
    return result


def _literal_assignment(source: bytes, name: str) -> tuple[Any, str]:
    try:
        tree = ast.parse(source.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as exc:
        raise S10Error(str(exc), code="source_ast_unsupported") from exc
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(target, ast.Name) and target.id == name
            for target in (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
        )
    ]
    if len(matches) != 1:
        _fail("source_ast_unsupported", f"expected one assignment to {name}")
    node = matches[0]
    value_node = node.value
    try:
        value = ast.literal_eval(value_node)
    except (ValueError, TypeError) as exc:
        raise S10Error(str(exc), code="source_ast_unsupported") from exc
    return value, hashlib.sha256(
        ast.dump(value_node, annotate_fields=True, include_attributes=False).encode()
    ).hexdigest()


def _r4_source_identities() -> dict[str, Any]:
    identities = {}
    for path, expected_blob in R4_SOURCE_BLOBS.items():
        blob = _git_oid(f"{DUCTILE_COMMIT}:{path}")
        if blob != expected_blob:
            _fail("source_identity_mismatch", f"{path}: {blob} != {expected_blob}")
        data = _blob_bytes(blob)
        identities[path] = {
            "blob": blob,
            "raw_sha256": hashlib.sha256(data).hexdigest(),
        }
    return identities


def _default_common_parameters() -> tuple[list[tuple[str, Any]], dict[str, Any]]:
    path = "projects/hipblaslt/tensilelite/Tensile/Common/GlobalParameters.py"
    source = _blob_bytes(R4_SOURCE_BLOBS[path])
    value, ast_hash = _literal_assignment(source, "defaultBenchmarkCommonParameters")
    records = _strict_singleton_records(
        value, context="defaultBenchmarkCommonParameters"
    )
    for name, candidates in records:
        if not isinstance(candidates, list) or not candidates:
            _fail("source_ast_unsupported", f"default {name} has invalid candidates")
    return records, {
        "path": path,
        "blob": R4_SOURCE_BLOBS[path],
        "assignment_ast_sha256": ast_hash,
        "record_count": len(records),
        "records_sha256": canonical_sha256(value),
    }


def _valid_work_group(value: Any) -> bool:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
    ):
        return False
    sg0, sg1, nsg = value
    threads = sg0 * sg1 * nsg
    return (
        32 <= threads <= 1024
        and threads % 32 == 0
        and nsg in {1, 2, 4, 8, 16, 32, 64, 96, 128, 256}
        and sg0 >= 1
        and sg1 == threads // nsg // sg0
    )


def _independent_group_value_options(name: str, value: Any) -> list[Any]:
    if not isinstance(value, list):
        return [copy.deepcopy(value)]
    if not value:
        _fail("group_expansion_unsupported", f"empty options for {name}")
    if name == "MatrixInstruction":
        if any(isinstance(item, list) for item in value):
            _fail("group_expansion_unsupported", "nested MatrixInstruction")
        return [copy.deepcopy(value)]
    if name == "WorkGroup" and _valid_work_group(value):
        return [copy.deepcopy(value)]
    if any(isinstance(item, (dict, list)) for item in value):
        _fail("group_expansion_unsupported", f"unsupported nested options for {name}")
    return [copy.deepcopy(item) for item in value]


def _independent_expand_groups(groups: Any) -> tuple[list[list[dict[str, Any]]], list[dict[str, Any]]]:
    if not isinstance(groups, list):
        _fail("group_expansion_unsupported", "Groups is not a list")
    expanded = []
    index_table = []
    total = 0
    for group_index, group in enumerate(groups):
        if not isinstance(group, list) or not group:
            _fail("group_expansion_unsupported", f"group {group_index} is empty")
        expanded_group = []
        for raw_index, entry in enumerate(group):
            if not isinstance(entry, dict) or not entry:
                _fail("group_expansion_unsupported", f"group {group_index}/{raw_index}")
            names = list(entry)
            if len(names) != len(set(names)):
                _fail("duplicate_parameter", f"group {group_index}/{raw_index}")
            options = [
                _independent_group_value_options(name, entry[name])
                for name in names
            ]
            cardinality = math.prod(len(items) for items in options)
            if cardinality > 100000 or total + cardinality > 20000:
                _fail("group_expansion_unsupported", "group expansion exceeds bound")
            start = len(expanded_group)
            for values in itertools.product(*options):
                expanded_group.append(
                    {name: copy.deepcopy(value) for name, value in zip(names, values)}
                )
            index_table.append(
                {
                    "group_index": group_index,
                    "raw_index": raw_index,
                    "expanded_start": start,
                    "expanded_count": cardinality,
                    "names": names,
                    "raw_value_sha256": canonical_sha256(entry),
                }
            )
            total += cardinality
        expanded.append(expanded_group)
    return expanded, index_table


def _group_parameter_owners(
    groups: Sequence[Sequence[Mapping[str, Any]]],
) -> dict[str, int]:
    owners = {}
    for group_index, group in enumerate(groups):
        names = {name for entry in group for name in entry}
        overlap = set(owners).intersection(names)
        if overlap:
            _fail(
                "group_overlap",
                f"group {group_index} overlaps prior groups: {sorted(overlap)}",
            )
        owners.update({name: group_index for name in names})
    return owners


def _deep_update_independent(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(base))
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_update_independent(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _probability_evidence(values: Sequence[Any], beta: float) -> dict[str, Any]:
    if (
        isinstance(beta, bool)
        or not isinstance(beta, (int, float))
        or not math.isfinite(beta)
    ):
        _fail("weight_mismatch", "weight_beta is not finite numeric")
    if not isinstance(values, list) or not values or any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in values
    ):
        _fail("weight_mismatch", "weights must be finite numeric values")
    weights = np.array(values, dtype=np.float32)
    transformed = np.exp(-beta * (weights - weights.min()))
    probabilities = transformed / transformed.sum()
    raw = probabilities.tobytes(order="C")
    return {
        "values": probabilities.tolist(),
        "dtype": str(probabilities.dtype),
        "dtype_str": probabilities.dtype.str,
        "byteorder": probabilities.dtype.byteorder,
        "shape": list(probabilities.shape),
        "count": int(probabilities.size),
        "finite": bool(np.isfinite(probabilities).all()),
        "sum": float(probabilities.sum(dtype=np.float32)),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "values_sha256": canonical_sha256(probabilities.tolist()),
    }


def _numpy_identity() -> dict[str, Any]:
    module_path = Path(np.__file__).resolve()
    return {
        "version": np.__version__,
        "path": str(module_path),
        "raw_sha256": sha256_file(module_path),
    }


def _validate_axis_records(
    records: Any,
    *,
    context: str,
    require_pinned_order: bool = True,
) -> dict[str, list[Any]]:
    if not isinstance(records, list) or not records:
        _fail("axis_record_mismatch", f"{context}: empty/non-list records")
    allowed = {
        "index",
        "axis",
        "origin",
        "candidates",
        "candidate_count",
        "candidates_sha256",
    }
    required = allowed - {"origin"}
    axes = []
    reconstructed = {}
    normalized = []
    for expected_index, record in enumerate(records):
        if (
            not isinstance(record, dict)
            or not required.issubset(record)
            or not set(record).issubset(allowed)
        ):
            _fail("axis_record_mismatch", f"{context}[{expected_index}] shape")
        index = record["index"]
        axis = record["axis"]
        candidates = record["candidates"]
        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or index != expected_index
            or not isinstance(axis, str)
            or not axis
            or axis in reconstructed
            or not isinstance(candidates, list)
            or not candidates
            or isinstance(record["candidate_count"], bool)
            or record["candidate_count"] != len(candidates)
            or record["candidates_sha256"] != canonical_sha256(candidates)
        ):
            _fail(
                "axis_record_mismatch",
                f"{context}[{expected_index}] index/axis/candidates",
            )
        axes.append(axis)
        reconstructed[axis] = copy.deepcopy(candidates)
        normalized.append(
            {
                "index": index,
                "axis": axis,
                "candidates": copy.deepcopy(candidates),
                "candidate_count": len(candidates),
                "candidates_sha256": record["candidates_sha256"],
            }
        )
    if require_pinned_order and (
        axes != EXPECTED_AXIS_ORDER
        or canonical_sha256(axes) != EXPECTED_AXIS_ORDER_SHA256
        or canonical_sha256(reconstructed) != EXPECTED_LEGACY_SPACE_MAP_SHA256
    ):
        _fail("axis_order_mismatch", f"{context}: pinned order/map differs")
    return {
        "order": axes,
        "map": reconstructed,
        "normalized": normalized,
    }


def _raw_o4_witness(document: Mapping[str, Any], raw_sha256: str) -> dict[str, Any]:
    if raw_sha256 != EXPECTED_ACTUAL_YAML_SHA256:
        _fail("raw_witness_mismatch", f"actual YAML hash {raw_sha256}")
    fields = _extract_raw_fields(document)
    problems = document["BenchmarkProblems"]
    params = problems[0][1]
    outer = _strict_singleton_records(
        params["ForkParameters"],
        context="ForkParameters",
        expected_count=31,
    )
    if outer[-1][0] != "Groups" or any(name == "Groups" for name, _ in outer[:-1]):
        _fail("raw_witness_mismatch", "Groups must be the unique final fork record")
    non_groups = outer[:-1]
    expected_constants = {
        "PrefetchLocalRead": 1,
        "GlobalSplitUAlgorithm": "MultipleBuffer",
        "DtlPlusLdsBuf": 1,
    }
    singles = {}
    variables = {}
    partition_table = []
    for raw_index, (name, values) in enumerate(non_groups):
        if not isinstance(values, list) or not values:
            _fail("raw_witness_mismatch", f"{name} candidates invalid")
        is_single = len(values) == 1
        destination = singles if is_single else variables
        destination[name] = copy.deepcopy(values[0] if is_single else values)
        partition_table.append(
            {
                "raw_index": raw_index,
                "name": name,
                "candidate_count": len(values),
                "candidates_sha256": canonical_sha256(values),
                "classification": "singleton" if is_single else "variable",
                "expected_destination": (
                    "BenchmarkStep.constantParams"
                    if is_single
                    else "BenchmarkStep.forkParams"
                ),
            }
        )
    if (
        len(non_groups) != 30
        or len(variables) != 27
        or len(singles) != 3
        or set(singles) != set(expected_constants)
        or any(not _typed_equal(singles[key], expected_constants[key]) for key in singles)
    ):
        _fail("raw_partition_mismatch", "raw 30=27+3 partition/value mismatch")
    required_o4 = {
        "architecture": "gfx942",
        "backend_name": "Ductile",
        "data_type": "B",
        "dest_data_type": "B",
        "compute_data_type": "S",
        "transpose_a": False,
        "transpose_b": False,
        "batched": True,
        "n_elements_to_validate": 128,
        "soo": False,
    }
    if any(not _typed_equal(fields[key], value) for key, value in required_o4.items()):
        _fail("raw_witness_mismatch", "O4 dtype/layout/backend fields differ")
    if len(fields["sizes"]) != 16:
        _fail("raw_witness_mismatch", "generated YAML must contain 16 deduplicated sizes")
    return {
        "raw_sha256": raw_sha256,
        "outer_record_count": len(outer),
        "outer_order": [name for name, _ in outer],
        "outer_records_sha256": canonical_sha256(
            [{name: value} for name, value in outer]
        ),
        "variable_names": list(variables),
        "variable_count": len(variables),
        "singleton_constants": singles,
        "singleton_count": len(singles),
        "partition_equation": "30=27+3",
        "partition_table": partition_table,
        "groups": copy.deepcopy(outer[-1][1]),
        "groups_sha256": canonical_sha256(outer[-1][1]),
        "fields": {key: fields[key] for key in required_o4},
        "sizes": fields["sizes"],
        "backend_config": copy.deepcopy(document["Backend"]["Config"]),
        "benchmark_common_records": copy.deepcopy(
            params.get("BenchmarkCommonParameters", [])
        ),
        "fork_records": [{name: value} for name, value in non_groups],
    }


def _independent_source_model(witness: Mapping[str, Any]) -> dict[str, Any]:
    source_identities = _r4_source_identities()
    default_records, default_identity = _default_common_parameters()
    common_records = _strict_singleton_records(
        witness["benchmark_common_records"], context="BenchmarkCommonParameters"
    )
    fork_records = _strict_singleton_records(
        witness["fork_records"], context="ForkParameters(non-Groups)", expected_count=30
    )
    common = _ordered_update({}, common_records)
    fork_raw = _ordered_update({}, fork_records)
    config_params = _ordered_update(common, fork_records)
    params = _ordered_update(_ordered_update({}, default_records), config_params.items())
    single = {}
    multi = {}
    origins = {}
    raw_fork_names = {name for name, _ in fork_records}
    common_names = {name for name, _ in common_records}
    for name, candidates in params.items():
        if not isinstance(candidates, list) or not candidates:
            _fail("source_model_mismatch", f"resolved candidates invalid for {name}")
        origins[name] = (
            "raw_fork"
            if name in raw_fork_names
            else "benchmark_common"
            if name in common_names
            else "pinned_default"
        )
        if len(candidates) == 1:
            single[name] = copy.deepcopy(candidates[0])
        else:
            multi[name] = copy.deepcopy(candidates)
    base_single = copy.deepcopy(single)
    base_multi = copy.deepcopy(multi)
    groups, group_index_table = _independent_expand_groups(witness["groups"])
    if [len(group) for group in groups] != [9918, 3, 2]:
        _fail("group_mismatch", "expanded group cardinalities differ")
    groups_hash = canonical_sha256(groups)
    if groups_hash != EXPECTED_GROUPS_SHA256:
        _fail("group_mismatch", f"group hash {groups_hash}")
    _group_parameter_owners(groups)
    for index, group in enumerate(groups):
        if len(group) == 1:
            overlap = set(group[0]).intersection(multi)
            if overlap:
                _fail(
                    "group_overlap",
                    f"singleton group {index} overlaps fork axes: {sorted(overlap)}",
                )
            single.update(copy.deepcopy(group[0]))
            for key in group[0]:
                origins[key] = f"group_{index}_singleton"
        else:
            axis = f"group_{index}"
            multi[axis] = copy.deepcopy(group)
            origins[axis] = f"group_{index}_expanded"
    order = list(multi)
    if order != EXPECTED_AXIS_ORDER or canonical_sha256(order) != EXPECTED_AXIS_ORDER_SHA256:
        _fail("axis_order_mismatch", "independent axis order differs")
    axis_records = [
        {
            "index": index,
            "axis": axis,
            "origin": origins[axis],
            "candidates": copy.deepcopy(multi[axis]),
            "candidate_count": len(multi[axis]),
            "candidates_sha256": canonical_sha256(multi[axis]),
        }
        for index, axis in enumerate(order)
    ]
    legacy_hash = canonical_sha256(multi)
    if legacy_hash != EXPECTED_LEGACY_SPACE_MAP_SHA256:
        _fail("axis_map_mismatch", f"legacy map hash {legacy_hash}")
    backend_defaults = strict_load_yaml(
        _blob_bytes(
            R4_SOURCE_BLOBS[
                "projects/hipblaslt/tensilelite/Tensile/ductile/config/defaults.yaml"
            ]
        ).decode("utf-8"),
        from_text=True,
    )
    resolved_backend = _deep_update_independent(
        backend_defaults, witness["backend_config"]
    )
    raw_weights = witness["backend_config"].get("weights")
    weight_records = _strict_singleton_records(raw_weights, context="weights")
    weight_map = {}
    weight_table = []
    for position, (axis, values) in enumerate(weight_records):
        if axis not in multi or axis in weight_map or len(values) != len(multi[axis]):
            _fail("weight_mismatch", f"weight axis/cardinality mismatch: {axis}")
        weight_map[axis] = copy.deepcopy(values)
        weight_table.append(
            {
                "position": position,
                "axis": axis,
                "candidate_count": len(multi[axis]),
                "weight_count": len(values),
                "candidates_sha256": canonical_sha256(multi[axis]),
                "weights_sha256": canonical_sha256(values),
            }
        )
    if (
        list(weight_map) != ["group_0"]
        or len(weight_map["group_0"]) != 9918
        or len(multi["group_0"]) != 9918
        or canonical_sha256(raw_weights) != EXPECTED_WEIGHTS_SHA256
        or canonical_sha256(resolved_backend["weights"]) != EXPECTED_WEIGHTS_SHA256
    ):
        _fail("weight_mismatch", "group_0 positional weights differ")
    beta_origin = (
        "raw"
        if "weight_beta" in witness["backend_config"]
        else "pinned_default"
    )
    beta = resolved_backend["weight_beta"]
    if beta_origin != "pinned_default" or not _typed_equal(beta, 0.25):
        _fail("weight_mismatch", "weight_beta must be absent/raw and resolve to 0.25")
    probabilities = {
        axis: _probability_evidence(values, beta)
        for axis, values in weight_map.items()
    }
    raw_index_by_name = {
        next(iter(record)): index
        for index, record in enumerate(witness["fork_records"])
    }
    parameter_table = [
        {
            "raw_index": raw_index_by_name.get(record["axis"]),
            "axis_index": index,
            "axis": record["axis"],
            "origin": record["origin"],
            "candidate_count": record["candidate_count"],
            "candidates_sha256": record["candidates_sha256"],
            "expected_destination": "SearchSpace.map",
        }
        for index, record in enumerate(axis_records)
    ]
    normalized_axes = _validate_axis_records(
        axis_records, context="independent source model"
    )["normalized"]
    return {
        "source_identities": source_identities,
        "default_identity": default_identity,
        "resolved_base_constant_map": base_single,
        "resolved_base_fork_map": base_multi,
        "resolved_constant_map": single,
        "resolved_fork_map": multi,
        "resolved_origins": origins,
        "groups": groups,
        "group_index_table": group_index_table,
        "groups_sha256": groups_hash,
        "axis_order": order,
        "axis_order_sha256": canonical_sha256(order),
        "ordered_axis_records": axis_records,
        "ordered_axis_records_sha256": canonical_sha256(axis_records),
        "ordered_map_schema": "s10_ordered_axis_records_v1",
        "ordered_map_sha256": canonical_sha256(normalized_axes),
        "legacy_space_map_sha256": legacy_hash,
        "weight_records": [{axis: values} for axis, values in weight_records],
        "weight_table": weight_table,
        "raw_weights_sha256": canonical_sha256(raw_weights),
        "resolved_weights_sha256": canonical_sha256(resolved_backend["weights"]),
        "weight_beta": beta,
        "weight_beta_origin": beta_origin,
        "soo": resolved_backend["soo"],
        "reduce_fn": "mean" if resolved_backend["soo"] else "max",
        "probabilities": probabilities,
        "numpy": _numpy_identity(),
        "resolved_backend_config": resolved_backend,
        "parameter_table": parameter_table,
    }


def _consume_probe_code() -> str:
    return r"""
import copy, hashlib, json
from pathlib import Path
import numpy as np
from Tensile import LibraryIO
from Tensile.BenchmarkStructs import BenchmarkProcess
from Tensile.ductile import config as ductile_config
from Tensile.ductile.algorithm import GeneticAlgorithm
from Tensile.ductile.core import SearchSpace, Selection, Crossover, Mutation, Mating, Survival

def plain(x):
    if isinstance(x, dict): return {str(k): plain(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [plain(v) for v in x]
    if isinstance(x, np.ndarray): return plain(x.tolist())
    if isinstance(x, np.generic): return plain(x.item())
    if x is None or isinstance(x,(str,bool,int,float)): return x
    return repr(x)
def digest(x):
    return hashlib.sha256(json.dumps(plain(x),sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def prob_record(x):
    a = np.asarray(x)
    return {
        "values": plain(a),
        "dtype": str(a.dtype),
        "dtype_str": a.dtype.str,
        "byteorder": a.dtype.byteorder,
        "shape": list(a.shape),
        "count": int(a.size),
        "finite": bool(np.isfinite(a).all()),
        "sum": float(a.sum(dtype=np.float32)),
        "raw_sha256": hashlib.sha256(a.tobytes(order="C")).hexdigest(),
        "values_sha256": digest(a.tolist()),
    }

path = Path(__import__("sys").argv[1])
doc = LibraryIO.read(path)
bp = doc["BenchmarkProblems"][0]
process = BenchmarkProcess(bp[0], bp[1], False)
step = process[0]
fork = copy.deepcopy(step.forkParams)
constant = copy.deepcopy(step.constantParams)
for index, group in enumerate(step.paramGroups):
    if len(group) == 1:
        constant.update(group[0])
    else:
        fork["group_" + str(index)] = group
space = SearchSpace(fork, valid=lambda _: True, max_iters=250)
merged = ductile_config.update(doc["Backend"]["Config"])
selection = Selection.get(**ductile_config.populate(merged, "selection"))
crossover = Crossover.get(**ductile_config.populate(merged, "crossover"))
mutation = Mutation(space, **merged["mutation"])
mating = Mating(space=space, selection=selection, crossover=crossover, mutation=mutation, max_iters=merged["max_iters"])
survival = Survival.get(**ductile_config.populate(merged, "survival"))
ga = GeneticAlgorithm(space, mating, evaluate=lambda _: np.ones((1,1)), survival=survival,
    pop_size=merged["pop_size"], n_gen=merged["n_gen"], soo=merged["soo"],
    period=merged["period"], tol=merged["tol"], div_thr=merged["div_thr"],
    seed=merged["seed"], verbose=0, log_file=None, checkpoint_path=None,
    weights=merged["weights"], weight_beta=merged["weight_beta"])
result = {
    "document_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "raw_group_count": len(bp[1]["ForkParameters"][-1]["Groups"]),
    "expanded_group_count": len(step.paramGroups),
    "raw_groups_sha256": digest(bp[1]["ForkParameters"][-1]["Groups"]),
    "expanded_groups_sha256": digest(step.paramGroups),
    "expanded_groups": plain(step.paramGroups),
    "fork_parameters": plain(step.forkParams),
    "constant_parameters": plain(constant),
    "search_space_map": plain(space.map),
    "search_space_map_sha256": digest(space.map),
    "search_space_order": list(space.map),
    "ordered_axis_records": [
        {
            "index": i,
            "axis": k,
            "candidates": plain(space.map[k]),
            "candidate_count": len(space.map[k]),
            "candidates_sha256": digest(space.map[k]),
        }
        for i,k in enumerate(space.map)
    ],
    "weights": plain(merged["weights"]),
    "weights_sha256": digest(merged["weights"]),
    "weight_beta": plain(merged["weight_beta"]),
    "probabilities": {k: prob_record(v) for k,v in ga.probs.items()},
    "probability_axis_order": list(ga.probs),
    "resolved_backend_o4": {
        "soo": plain(merged["soo"]),
        "n_elements_to_validate": plain(merged["n_elements_to_validate"]),
        "weight_beta": plain(merged["weight_beta"]),
    },
    "numpy": {
        "version": np.__version__,
        "path": str(Path(np.__file__).resolve()),
        "raw_sha256": hashlib.sha256(Path(np.__file__).resolve().read_bytes()).hexdigest(),
    },
    "soo": bool(ga.soo),
    "reduce_fn": "mean" if ga.reduce_fn is np.mean else "max",
    "resolved_initial_pop_size": ga.pop_size,
}
print(json.dumps(result, sort_keys=True, separators=(",",":")))
"""


def _parse_consumer_stdout(raw: bytes) -> Mapping[str, Any]:
    lines = raw.splitlines()
    json_lines = [line for line in lines if line.startswith(b"{")]
    if len(json_lines) != 1 or any(
        not line.startswith(b"#") and line != json_lines[0] for line in lines
    ):
        _fail(
            "ductile_parity_mismatch",
            "consumer stdout must contain only known comments and one JSON record",
        )
    try:
        document = json.loads(json_lines[0])
    except json.JSONDecodeError as exc:
        raise S10Error(str(exc), code="ductile_parity_mismatch") from exc
    if not isinstance(document, dict):
        _fail("ductile_parity_mismatch", "consumer JSON record is not an object")
    return document


def _validate_model_runtime(
    witness: Mapping[str, Any],
    model: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    tag: str,
) -> None:
    if actual.get("document_sha256") != witness["raw_sha256"]:
        _fail("ductile_parity_mismatch", "consumer read different bytes")
    if (
        actual.get("raw_group_count") != len(witness["groups"])
        or actual.get("expanded_group_count") != len(model["groups"])
        or actual.get("raw_groups_sha256") != witness["groups_sha256"]
        or actual.get("expanded_groups_sha256") != model["groups_sha256"]
        or not _typed_equal(actual.get("expanded_groups"), model["groups"])
    ):
        _fail("group_mismatch", "raw/model/runtime group evidence differs")
    for actual_key, model_key in (
        ("fork_parameters", "resolved_base_fork_map"),
        ("constant_parameters", "resolved_constant_map"),
        ("search_space_map", "resolved_fork_map"),
    ):
        if not _typed_equal(actual.get(actual_key), model[model_key]):
            _fail(
                "ductile_parity_mismatch",
                f"runtime {actual_key} differs from independent source model",
            )

    actual_axes = _validate_axis_records(
        actual.get("ordered_axis_records"),
        context=f"runtime {tag}",
    )
    model_axes = _validate_axis_records(
        model["ordered_axis_records"],
        context=f"source model {tag}",
    )
    if (
        actual.get("search_space_order") != model["axis_order"]
        or not _typed_equal(actual_axes["map"], model_axes["map"])
        or not _typed_equal(actual_axes["normalized"], model_axes["normalized"])
        or actual.get("search_space_map_sha256")
        != model["legacy_space_map_sha256"]
        or canonical_sha256(actual_axes["normalized"])
        != model["ordered_map_sha256"]
    ):
        _fail("axis_order_mismatch", "model/runtime indexed-axis evidence differs")

    if (
        not _typed_equal(actual.get("weights"), model["resolved_backend_config"]["weights"])
        or actual.get("weights_sha256") != model["resolved_weights_sha256"]
        or not _typed_equal(actual.get("weight_beta"), model["weight_beta"])
        or actual.get("probability_axis_order") != list(model["probabilities"])
        or not _typed_equal(actual.get("probabilities"), model["probabilities"])
        or actual.get("numpy") != model["numpy"]
    ):
        _fail("weight_mismatch", "model/runtime weights or float32 probabilities differ")
    if (
        actual.get("soo") is not False
        or model["soo"] is not False
        or actual.get("reduce_fn") != "max"
        or model["reduce_fn"] != "max"
        or not _typed_equal(
            actual.get("resolved_backend_o4"),
            {
                "soo": False,
                "n_elements_to_validate": 128,
                "weight_beta": 0.25,
            },
        )
    ):
        _fail("ductile_parity_mismatch", "runtime O4/reduction evidence differs")
    try:
        probabilities = actual["probabilities"]["group_0"]
    except (KeyError, TypeError):
        _fail("weight_mismatch", "runtime probability evidence absent")
    if (
        not isinstance(probabilities, dict)
        or probabilities.get("dtype") != "float32"
        or probabilities.get("dtype_str") not in {"<f4", "=f4"}
        or probabilities.get("byteorder") not in {"<", "="}
        or probabilities.get("shape") != [9918]
        or probabilities.get("count") != 9918
        or probabilities.get("finite") is not True
        or isinstance(probabilities.get("sum"), bool)
        or not isinstance(probabilities.get("sum"), (int, float))
        or not math.isfinite(probabilities["sum"])
    ):
        _fail("weight_mismatch", "runtime probability representation differs")


def _consume_generated_yaml(
    root: Path,
    build: Path,
    actual_path: Path,
    log_root: Path,
    tag: str,
) -> dict[str, Any]:
    env = _base_env()
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in _python_path(root, build))
    proc, record = _run_logged(
        [str(PYTHON), "-S", "-c", _consume_probe_code(), str(actual_path)],
        cwd=root,
        env=env,
        log_root=log_root,
        name=f"{tag}-ductile-consumption",
    )
    if proc.stderr.decode("utf-8", errors="strict") != EXPECTED_CONSUMER_STDERR:
        _fail(
            "ductile_parity_mismatch",
            "consumer stderr differs from the one pinned population-size warning",
        )
    actual = dict(_parse_consumer_stdout(proc.stdout))
    raw_sha256 = sha256_file(actual_path)
    document = _raw_document(actual_path)
    witness = _raw_o4_witness(document, raw_sha256)
    model = _independent_source_model(witness)
    _validate_model_runtime(witness, model, actual, tag=tag)

    actual["command"] = record
    actual["accepted_stderr"] = EXPECTED_CONSUMER_STDERR
    semantic_actual = {
        key: value for key, value in actual.items() if key != "command"
    }
    summary = {
        "raw_witness_sha256": canonical_sha256(witness),
        "source_model_sha256": canonical_sha256(model),
        "actual_runtime_sha256": canonical_sha256(semantic_actual),
        "oracle_sha256": canonical_sha256(
            {
                "raw_witness": witness,
                "source_model": model,
                "actual_runtime": semantic_actual,
            }
        ),
        "group_order_weights_probability_parity": True,
        "axis_count": len(model["axis_order"]),
        "constant_count": len(model["resolved_constant_map"]),
        "probability_axes": list(model["probabilities"]),
    }
    return {
        "raw_document": plain_value(document),
        "witness": witness,
        "model": model,
        "actual": actual,
        "semantic_actual": semantic_actual,
        "summary": summary,
    }


def _select_sizes(
    raw_sizes: Sequence[Sequence[int]],
    generated_sizes: Sequence[Sequence[int]],
    shared_hashes: Mapping[str, str],
) -> dict[str, Any]:
    deduplicated = list(dict.fromkeys(tuple(item) for item in generated_sizes))
    if len(deduplicated) < 3:
        _fail("two_size_downgrade", f"only {len(deduplicated)} distinct sizes")
    ordered = sorted(
        deduplicated,
        key=lambda item: (item[3], item[0] * item[1] * item[2], item[0], item[1], item[2]),
    )
    indices = [0, (len(ordered) - 1) // 2, len(ordered) - 1]
    selected = [ordered[index] for index in indices]
    if len(set(selected)) != 3:
        _fail("two_size_downgrade", "three-size rule did not select distinct sizes")
    return {
        "schema_version": "1.0.0",
        "kind": "s10_size_registry",
        "checkpoint_id": "S10",
        "status": "prelock_complete",
        "raw_rows": [list(item) for item in raw_sizes],
        "raw_row_count": len(raw_sizes),
        "deduplication_rule": "first occurrence by exact (M,N,batch,K) tuple",
        "distinct_source_order": [list(item) for item in deduplicated],
        "distinct_count": len(deduplicated),
        "selection_key": ["K", "M*N*batch", "M", "N", "batch"],
        "selection_indices": indices,
        "selected_sizes": [list(item) for item in selected],
        "dtype_layout": {
            "data_type": "B",
            "dest_data_type": "B",
            "compute_data_type": "S",
            "transpose_a": False,
            "transpose_b": False,
            "batched": True,
        },
        "same_space": dict(shared_hashes),
        "same_space_parity": True,
    }


def _sentinel_index(values: Sequence[Any], preferred: int) -> int:
    candidates = [
        index
        for index, value in enumerate(values)
        if not isinstance(value, bool)
        and isinstance(value, (int, float))
        and value in (-1, -2)
    ]
    return candidates[preferred % len(candidates)] if candidates else 0


def _select_mapping_ten(axis_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    validated_axes = _validate_axis_records(
        axis_records,
        context="mapping selection",
    )
    space_map = validated_axes["map"]
    keys = validated_axes["order"]
    group_keys = [key for key in keys if key.startswith("group_")]
    residual_keys = [key for key in keys if key not in group_keys]

    def vector(fn) -> dict[str, int]:
        return {key: int(fn(index, key, space_map[key])) for index, key in enumerate(keys)}

    patterns: list[tuple[str, str, dict[str, int]]] = [
        ("all-first", "all group and residual lower boundaries", vector(lambda _i, _k, _v: 0)),
        (
            "all-last",
            "all group and residual upper boundaries",
            vector(lambda _i, _k, values: len(values) - 1),
        ),
        (
            "group-first-residual-last",
            "group lower and residual upper boundaries",
            vector(lambda _i, key, values: 0 if key in group_keys else len(values) - 1),
        ),
        (
            "group-last-residual-first",
            "group upper and residual lower boundaries",
            vector(lambda _i, key, values: len(values) - 1 if key in group_keys else 0),
        ),
        (
            "alternating",
            "alternating lower/upper candidate boundaries",
            vector(lambda index, _key, values: 0 if index % 2 == 0 else len(values) - 1),
        ),
        (
            "alternating-complement",
            "complementary lower/upper candidate boundaries",
            vector(lambda index, _key, values: len(values) - 1 if index % 2 == 0 else 0),
        ),
        (
            "lower-middle",
            "lower-middle candidate coverage",
            vector(lambda _i, _k, values: (len(values) - 1) // 2),
        ),
        (
            "upper-middle",
            "upper-middle candidate coverage",
            vector(lambda _i, _k, values: len(values) // 2),
        ),
        (
            "sentinel-boundary",
            "explicit -1/-2 sentinel coverage where present",
            vector(lambda index, _key, values: _sentinel_index(values, index)),
        ),
        (
            "hash-seeded-fill-0",
            "label-blind SHA-256 seeded interior coverage",
            vector(
                lambda index, key, values: int(
                    hashlib.sha256(f"S10:{index}:{key}:0".encode()).hexdigest(), 16
                )
                % len(values)
            ),
        ),
    ]
    unique: list[tuple[str, str, dict[str, int]]] = []
    seen = set()
    fill = 1
    for name, reason, indices in patterns:
        digest = canonical_sha256(indices)
        if digest not in seen:
            unique.append((name, reason, indices))
            seen.add(digest)
    while len(unique) < 10:
        indices = vector(
            lambda index, key, values, fill=fill: int(
                hashlib.sha256(f"S10:{index}:{key}:{fill}".encode()).hexdigest(), 16
            )
            % len(values)
        )
        digest = canonical_sha256(indices)
        if digest not in seen:
            unique.append(
                (
                    f"hash-seeded-fill-{fill}",
                    "label-blind SHA-256 seeded deduplication fill",
                    indices,
                )
            )
            seen.add(digest)
        fill += 1
        if fill > 1000:
            _fail("mapping_unresolved", "unable to derive ten unique mappings")
    if len(unique) != 10:
        _fail("mapping_unresolved", f"mapping selection produced {len(unique)}")
    candidates = []
    for slot, (name, reason, indices) in enumerate(unique):
        values = {key: copy.deepcopy(space_map[key][index]) for key, index in indices.items()}
        candidates.append(
            {
                "slot": slot,
                "pattern": name,
                "coverage_reason": reason,
                "indices": indices,
                "values": values,
                "config_hash": canonical_sha256(values),
            }
        )
    hashes = sorted(item["config_hash"] for item in candidates)
    anchor_hashes = [hashes[0], hashes[(len(hashes) - 1) // 2], hashes[-1]]
    if len(set(anchor_hashes)) != 3:
        _fail("mapping_unresolved", "anchor hashes are not distinct")
    coverage_fields = [
        field
        for field in (
            "DepthU",
            "GlobalSplitU",
            "GlobalReadVectorWidthA",
            "GlobalReadVectorWidthB",
            "VectorWidth",
            "PrefetchGlobalRead",
        )
        if field in space_map
    ]
    sentinels = sorted(
        {
            value
            for values in space_map.values()
            for value in values
            if not isinstance(value, bool)
            and isinstance(value, (int, float))
            and value in (-1, -2)
        }
    )
    return {
        "ordered_axis_schema": "s10_ordered_axis_records_v1",
        "axis_order": keys,
        "axis_order_sha256": canonical_sha256(keys),
        "ordered_axis_records_sha256": canonical_sha256(
            validated_axes["normalized"]
        ),
        "legacy_space_map_sha256": canonical_sha256(space_map),
        "selection_rule": [
            "all-first",
            "all-last",
            "group-first/residual-last",
            "group-last/residual-first",
            "alternating/complement",
            "lower/upper-middle",
            "sentinel-boundary",
            "hash-seeded-fill",
        ],
        "candidates": candidates,
        "candidate_hashes": [item["config_hash"] for item in candidates],
        "anchor_rule": "sorted hashes at indices 0,4,9",
        "anchor_hashes": anchor_hashes,
        "coverage": {
            "group_keys": group_keys,
            "residual_keys": residual_keys,
            "required_fields_present": coverage_fields,
            "sentinels_present": sentinels,
        },
    }


def _contract() -> Mapping[str, Any]:
    document = strict_load_yaml(CONTRACT_PATH)
    _validate(document, context="S10 contract")
    if (
        sha256_file(CONTRACT_PATH) != EXPECTED_CONTRACT_RAW_SHA256
        or canonical_sha256(document) != EXPECTED_CONTRACT_SEMANTIC_SHA256
    ):
        _fail(
            "contract_semantic_mismatch",
            "material contract semantics differ from the frozen preregistration",
        )
    if document["implementation_whitelist"] != IMPLEMENTATION_WHITELIST:
        _fail("wrong_whitelist", "implementation whitelist mismatch")
    if document["delivery_whitelist"] != DELIVERY_WHITELIST:
        _fail("wrong_whitelist", "delivery whitelist mismatch")
    if document["forbidden_roots"] != FORBIDDEN_ROOTS:
        _fail("wrong_whitelist", "forbidden roots mismatch")
    return document


def _reject_early_postlock_targets() -> None:
    for path in POST_LOCK_PATHS:
        if path.exists():
            _fail("early_postlock_artifact", f"unexpected {_rel(path)}")


def _preflight(*, require_outputs: bool = False) -> dict[str, Any]:
    authorities = _resolve_authorities()
    _contract()
    _verify_r10_parent_archive()
    if not LOCK_PATH.is_file() and (
        not R10_RECOVERY_AUTHORITY.is_file()
        or sha256_file(R10_RECOVERY_AUTHORITY)
        != R10_RECOVERY_AUTHORITY_SHA256
    ):
        _fail("recovery_authority_mismatch", "R10 adjudication differs")
    if _git_oid(f"{S00_CLOSURE}^{{commit}}") != S00_CLOSURE:
        _fail("authority_mismatch", "S00 closure commit unavailable")
    if sha256_file(S00_REPORT) != S00_REPORT_SHA256:
        _fail("authority_mismatch", "S00 report hash mismatch")
    if require_outputs:
        for path in (INPUT_PATH, PROVENANCE_PATH, SIZE_REGISTRY_PATH):
            if not path.is_file():
                _fail("prelock_incomplete", f"missing pre-lock artifact {_rel(path)}")
    return {
        "status": "PASS",
        "checkpoint_id": "S10",
        "authorities": authorities,
        "contract_sha256": sha256_file(CONTRACT_PATH),
    }


def _write_ignored_manifest(path: Path, document: Mapping[str, Any]) -> dict[str, str]:
    atomic_write_json(path, document)
    os.chmod(path, 0o644)
    return {"path": _rel(path), "raw_sha256": sha256_file(path)}


def _append_phase_seal(
    run: Mapping[str, Any],
    phase: str,
) -> dict[str, str]:
    wrapper = run["integration_wrapper"]
    if any(item["phase"] == phase for item in wrapper["phase_seals"]):
        _fail("phase_seal_duplicate", f"{run['tag']}:{phase}")
    seal = _phase_seal(run["integration"], run["integration_semantic"], phase)
    wrapper["phase_seals"].append(seal)
    seal_path = (
        run["integration_wrapper_path"].parent
        / f"integration-{run['tag']}-phase-{phase}.json"
    )
    return _write_ignored_manifest(seal_path, seal)


def _require_semantic_parity(runs: Sequence[Mapping[str, Any]]) -> None:
    if len(runs) != 2:
        _fail("integration_parity_mismatch", "exactly two fresh roots are required")
    if (
        runs[0]["integration_semantic"] != runs[1]["integration_semantic"]
        or runs[0]["integration_semantic_ref"]["raw_sha256"]
        != runs[1]["integration_semantic_ref"]["raw_sha256"]
    ):
        _fail("integration_parity_mismatch", "root-independent manifests differ")


def prepare(scratch_root: Path) -> dict[str, Any]:
    if ROOT.resolve() != CONTAINER_REPO.resolve():
        _fail("wrong_container", "prepare must run in mounted /src/rocm-libraries")
    if not Path("/.dockerenv").exists():
        _fail("wrong_container", "prepare must run inside existing perlee container")
    scratch_root = _assert_scratch_root(scratch_root)
    if scratch_root.exists():
        _fail("already_exists", f"scratch root exists: {scratch_root}")
    _reject_early_postlock_targets()
    for path in (INPUT_PATH, PROVENANCE_PATH, SIZE_REGISTRY_PATH):
        if path.exists():
            _fail("already_exists", f"pre-prepare target exists: {_rel(path)}")
    preflight = _preflight()
    authorities = preflight["authorities"]
    scratch_root.mkdir(parents=True)
    logs = scratch_root / "logs"
    raw_manifests = scratch_root / "manifests"
    raw_manifests.mkdir()
    authority_dir = scratch_root / "authority"
    authority_dir.mkdir()
    authority_snapshot = authority_dir / "r10-adjudication.md"
    if sha256_file(R10_RECOVERY_AUTHORITY) != R10_RECOVERY_AUTHORITY_SHA256:
        _fail("recovery_authority_mismatch", "R10 adjudication changed before snapshot")
    atomic_write_bytes(authority_snapshot, R10_RECOVERY_AUTHORITY.read_bytes())
    os.chmod(authority_snapshot, 0o644)
    recovery_authority = _current_recovery_authority(authority_snapshot)

    derived, derivation = _derive_input()
    derived_path = scratch_root / "derived-input.yaml"
    atomic_write_bytes(derived_path, derived)
    os.chmod(derived_path, 0o644)

    runs = []
    for tag in ("a", "b"):
        run_root = scratch_root / f"run-{tag}"
        integration = run_root / "integration"
        native = run_root / "native-build"
        generation = run_root / "generation"
        integration_bundle = _materialize_integration(integration, authorities)
        integration_semantic_ref = _write_ignored_manifest(
            raw_manifests / f"integration-{tag}-semantic.json",
            integration_bundle["semantic"],
        )
        integration_wrapper_path = raw_manifests / f"integration-{tag}.json"
        integration_bundle["wrapper"]["semantic_manifest"] = integration_semantic_ref
        run = {
            "tag": tag,
            "root": run_root,
            "integration": integration,
            "native": native,
            "generation": generation,
            "integration_semantic": integration_bundle["semantic"],
            "integration_semantic_ref": integration_semantic_ref,
            "integration_wrapper": integration_bundle["wrapper"],
            "integration_wrapper_path": integration_wrapper_path,
        }
        _write_ignored_manifest(
            raw_manifests / f"integration-{tag}-phase-after-materialization.json",
            integration_bundle["wrapper"]["phase_seals"][0],
        )
        _append_phase_seal(run, "before-native-build")
        native_manifest = _build_native(integration, native, logs, tag)
        _append_phase_seal(run, "after-native-build")
        native_ref = _write_ignored_manifest(
            raw_manifests / f"native-{tag}.json", native_manifest
        )
        _append_phase_seal(run, "before-generation")
        generation_manifest = _generate(
            integration, native, derived_path, generation, logs, tag
        )
        _append_phase_seal(run, "after-generation")
        generation_ref = _write_ignored_manifest(
            raw_manifests / f"generation-{tag}.json", generation_manifest
        )
        run.update(
            {
                "native_manifest": native_manifest,
                "native_ref": native_ref,
                "generation_manifest": generation_manifest,
                "generation_ref": generation_ref,
            }
        )
        runs.append(run)
    _require_semantic_parity(runs)
    raw_a, raw_b, qualifying = _compare_generation_runs(
        runs[0]["generation_manifest"],
        runs[1]["generation_manifest"],
        runs[0]["generation"],
        runs[1]["generation"],
    )
    raw_hash = sha256_file(raw_a)
    if raw_hash != sha256_file(raw_b):
        _fail("generation_manifest_mismatch", "raw YAML hashes differ")

    raw_fields = _extract_raw_fields(_raw_document(raw_a))
    oracle_runs = []
    for run, actual in zip(runs, (raw_a, raw_b)):
        _append_phase_seal(run, "before-ductile-consumption")
        oracle = _consume_generated_yaml(
            run["integration"],
            run["native"],
            actual,
            logs,
            run["tag"],
        )
        oracle_refs = {
            "raw_document": _write_ignored_manifest(
                raw_manifests / f"oracle-{run['tag']}-raw-document.json",
                oracle["raw_document"],
            ),
            "raw_witness": _write_ignored_manifest(
                raw_manifests / f"oracle-{run['tag']}-raw-witness.json",
                oracle["witness"],
            ),
            "source_model": _write_ignored_manifest(
                raw_manifests / f"oracle-{run['tag']}-source-model.json",
                oracle["model"],
            ),
            "actual_runtime": _write_ignored_manifest(
                raw_manifests / f"oracle-{run['tag']}-actual-runtime.json",
                oracle["actual"],
            ),
        }
        oracle["refs"] = oracle_refs
        run["oracle_refs"] = oracle_refs
        oracle_runs.append(oracle)
        _append_phase_seal(run, "after-ductile-consumption")
        run["integration_ref"] = _write_ignored_manifest(
            run["integration_wrapper_path"], run["integration_wrapper"]
        )
    if any(
        not _typed_equal(oracle_runs[0][key], oracle_runs[1][key])
        for key in ("witness", "model", "semantic_actual", "summary")
    ):
        _fail("ductile_parity_mismatch", "dual-root consumption differs")
    oracle = oracle_runs[0]
    model = oracle["model"]
    shared_hashes = {
        "raw_yaml_sha256": raw_hash,
        "search_space_map_sha256": model["legacy_space_map_sha256"],
        "groups_sha256": model["groups_sha256"],
        "candidate_order_sha256": model["axis_order_sha256"],
        "weights_sha256": model["resolved_weights_sha256"],
    }
    size_registry = _select_sizes(
        derivation["raw_sizes"], raw_fields["sizes"], shared_hashes
    )
    mapping_selection = _select_mapping_ten(model["ordered_axis_records"])
    consumed_summary = {
        "oracle_schema": "s10_three_layer_ductile_oracle_v1",
        "fresh_root_count": 2,
        "each_root_independently_matched_source_model": True,
        "cross_root_parity": True,
        "raw_witness_sha256": oracle["summary"]["raw_witness_sha256"],
        "source_model_sha256": oracle["summary"]["source_model_sha256"],
        "actual_runtime_sha256": oracle["summary"]["actual_runtime_sha256"],
        "oracle_sha256": oracle["summary"]["oracle_sha256"],
        "raw_partition_equation": oracle["witness"]["partition_equation"],
        "raw_partition_table": oracle["witness"]["partition_table"],
        "axis_index_table": [
            {
                key: record[key]
                for key in (
                    "index",
                    "axis",
                    "origin",
                    "candidate_count",
                    "candidates_sha256",
                )
            }
            for record in model["ordered_axis_records"]
        ],
        "parameter_table": model["parameter_table"],
        "group_index_table": model["group_index_table"],
        "weight_table": model["weight_table"],
        "hashes": {
            "raw_yaml_sha256": raw_hash,
            "raw_groups_sha256": oracle["witness"]["groups_sha256"],
            "expanded_groups_sha256": model["groups_sha256"],
            "legacy_space_map_sha256": model["legacy_space_map_sha256"],
            "axis_order_sha256": model["axis_order_sha256"],
            "ordered_axis_records_sha256": model["ordered_axis_records_sha256"],
            "ordered_map_sha256": model["ordered_map_sha256"],
            "raw_weights_sha256": model["raw_weights_sha256"],
            "resolved_weights_sha256": model["resolved_weights_sha256"],
        },
        "weight_beta": {
            "raw_present": False,
            "resolved": model["weight_beta"],
            "origin": model["weight_beta_origin"],
        },
        "probability_evidence": {
            "axes": list(model["probabilities"]),
            "records": model["probabilities"],
            "numpy": model["numpy"],
            "full_itemwise_and_byte_parity": True,
        },
        "soo": model["soo"],
        "reduce_fn": model["reduce_fn"],
        "accepted_consumer_stderr": EXPECTED_CONSUMER_STDERR,
        "source_provenance": model["source_identities"],
        "oracle_runs": [
            {
                "tag": run["tag"],
                "raw_document": run["oracle_refs"]["raw_document"],
                "raw_witness": run["oracle_refs"]["raw_witness"],
                "source_model": run["oracle_refs"]["source_model"],
                "actual_runtime": run["oracle_refs"]["actual_runtime"],
            }
            for run in runs
        ],
    }
    provenance = {
        "schema_version": "1.0.0",
        "kind": "s10_yaml_provenance",
        "checkpoint_id": "S10",
        "status": "prelock_complete",
        "created_at": _utc_now(),
        **_current_lifecycle_fields(recovery_authority),
        "authorities": authorities,
        "template": {
            "path": TEMPLATE_PATH,
            "blob": TEMPLATE_BLOB,
            "raw_sha256": TEMPLATE_SHA256,
        },
        "derived_input": {
            "path": _rel(derived_path),
            "raw_sha256": sha256_file(derived_path),
            "derivation": derivation,
        },
        "runs": [
            {
                "tag": run["tag"],
                "integration": run["integration_ref"],
                "integration_semantic": run["integration_semantic_ref"],
                "native": run["native_ref"],
                "generation": run["generation_ref"],
                "integration_manifest_sha256": run["integration_semantic"]["manifest_sha256"],
                "integration_wrapper_sha256": run["integration_ref"]["raw_sha256"],
                "native_binary_sha256": run["native_manifest"]["binary"]["raw_sha256"],
                "generation_manifest_sha256": run["generation_manifest"]["output_manifest_sha256"],
                "imports": run["generation_manifest"]["imports"],
            }
            for run in runs
        ],
        "generation_parity": {
            "complete_manifest_identical": True,
            "manifest_sha256": runs[0]["generation_manifest"]["output_manifest_sha256"],
            "qualifying_count_per_run": [1, 1],
            "qualifying_relative_path": qualifying[0]["path"],
        },
        "actual_yaml": {
            "run_a_path": _rel(raw_a),
            "run_b_path": _rel(raw_b),
            "tracked_copy_path": _rel(INPUT_PATH),
            "run_a_raw_sha256": raw_hash,
            "run_b_raw_sha256": raw_hash,
            "tracked_copy_raw_sha256": raw_hash,
            "byte_copy_only": True,
            "artifact_role": "fresh experimental actual fixture",
        },
        "raw_fields": {
            key: raw_fields[key]
            for key in (
                "architecture",
                "backend_name",
                "data_type",
                "dest_data_type",
                "compute_data_type",
                "transpose_a",
                "transpose_b",
                "batched",
                "n_elements_to_validate",
                "soo",
            )
        },
        "consumption": consumed_summary,
        "mapping_selection": mapping_selection,
        "exclusions": {
            "compatibility_probes_reused": False,
            "build_3_reused": False,
            "build_2_rejected": True,
            "current_checkout_imported": False,
            "installed_rocisa_used": False,
            "production_or_deployment_claim": False,
        },
    }
    _validate(provenance, context="S10 provenance")
    _validate(size_registry, context="S10 size registry")
    if hashlib.sha256(raw_a.read_bytes()).hexdigest() != raw_hash:
        _fail("raw_copy_hash_mismatch", "raw source changed before copy")
    atomic_write_bytes(INPUT_PATH, raw_a.read_bytes())
    os.chmod(INPUT_PATH, 0o644)
    if sha256_file(INPUT_PATH) != raw_hash:
        _fail("raw_copy_hash_mismatch", "tracked copy hash mismatch")
    atomic_write_json(PROVENANCE_PATH, provenance)
    atomic_write_json(SIZE_REGISTRY_PATH, size_registry)
    os.chmod(PROVENANCE_PATH, 0o644)
    os.chmod(SIZE_REGISTRY_PATH, 0o644)
    return {
        "status": "PRELOCK_PREPARED",
        "actual_yaml_sha256": raw_hash,
        "generation_manifest_sha256": provenance["generation_parity"]["manifest_sha256"],
        "distinct_sizes": size_registry["distinct_count"],
        "selected_sizes": size_registry["selected_sizes"],
        "mapping_hashes": mapping_selection["candidate_hashes"],
        "anchor_hashes": mapping_selection["anchor_hashes"],
        "tracked_outputs": [_rel(INPUT_PATH), _rel(PROVENANCE_PATH), _rel(SIZE_REGISTRY_PATH)],
    }


def _require_exact_perlee() -> None:
    if ROOT.resolve() != CONTAINER_REPO.resolve() or not Path("/.dockerenv").exists():
        _fail("wrong_container", "live GPU work requires exact existing perlee")
    if not ROCM_SMI.is_file():
        _fail("live_gpu_unavailable", f"read-only probe tool absent: {ROCM_SMI}")


def _parse_pid_gpu_map(raw: bytes) -> dict[int, list[int]]:
    text = raw.decode("utf-8", "replace")
    result: dict[int, list[int]] = {}
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"PID\s+(\d+)\s+is using\s+\d+\s+DRM device\(s\):", line.strip())
        if not match:
            continue
        if index + 1 >= len(lines):
            _fail("h4_malformed", "truncated ROCm-SMI PID/device mapping")
        devices = lines[index + 1].strip().split()
        if any(not item.isdigit() for item in devices):
            _fail("h4_malformed", "malformed ROCm-SMI PID/device mapping")
        result[int(match.group(1))] = [int(item) for item in devices]
    return result


def _number_field(item: Mapping[str, Any], key: str, *, integer: bool) -> int | float:
    value = item.get(key)
    try:
        parsed = int(value) if integer else float(value)
    except (TypeError, ValueError) as exc:
        raise S10Error(f"{key} is malformed: {value!r}", code="h4_malformed") from exc
    if parsed < 0:
        _fail("h4_malformed", f"{key} is negative")
    return parsed


def _parse_live_devices(
    raw: bytes,
    pid_gpu_map: Mapping[int, Sequence[int]],
) -> list[dict[str, Any]]:
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise S10Error(str(exc), code="h4_malformed") from exc
    if not isinstance(document, dict) or not document:
        _fail("h4_malformed", "ROCm-SMI returned no devices")
    devices = []
    for card, item in sorted(
        document.items(),
        key=lambda pair: int(pair[0][4:]) if re.fullmatch(r"card\d+", pair[0]) else -1,
    ):
        if not re.fullmatch(r"card\d+", card) or not isinstance(item, dict):
            _fail("h4_malformed", f"unexpected ROCm-SMI device entry {card!r}")
        device_index = int(card[4:])
        identity = {
            "container_visible_index": device_index,
            "unique_id": str(item.get("Unique ID", "")),
            "serial_number": str(item.get("Serial Number", "")),
            "pci_bus": str(item.get("PCI Bus", "")),
            "arch": str(item.get("GFX Version", "")),
            "compute_partition": str(item.get("Compute Partition", "")),
            "memory_partition": str(item.get("Memory Partition", "")),
        }
        if (
            not identity["unique_id"]
            or not identity["serial_number"]
            or not re.fullmatch(
                r"[0-9A-Fa-f]{4}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}\.[0-7]",
                identity["pci_bus"],
            )
        ):
            _fail("h4_malformed", f"incomplete identity for {card}")
        gpu_use = float(_number_field(item, "GPU use (%)", integer=False))
        vram_percent = float(
            _number_field(item, "GPU Memory Allocated (VRAM%)", integer=False)
        )
        vram_used = int(_number_field(item, "VRAM Total Used Memory (B)", integer=True))
        vram_total = int(_number_field(item, "VRAM Total Memory (B)", integer=True))
        if vram_total <= 0 or vram_used > vram_total:
            _fail("h4_malformed", f"invalid VRAM counters for {card}")
        pids = sorted(
            pid for pid, mapped in pid_gpu_map.items() if device_index in mapped
        )
        reasons = []
        if identity["arch"] != LIVE_H4_POLICY["arch"]:
            reasons.append("wrong_arch")
        if identity["compute_partition"] != LIVE_H4_POLICY["compute_partition"]:
            reasons.append("wrong_compute_partition")
        if identity["memory_partition"] != LIVE_H4_POLICY["memory_partition"]:
            reasons.append("wrong_memory_partition")
        if gpu_use != LIVE_H4_POLICY["gpu_use_percent"]:
            reasons.append("gpu_use_nonzero")
        if vram_percent > LIVE_H4_POLICY["maximum_vram_allocation_percent"]:
            reasons.append("vram_allocation_above_one_percent")
        if pids:
            reasons.append("mapped_kfd_pid")
        devices.append(
            {
                "identity": identity,
                "gpu_use_percent": gpu_use,
                "vram_allocation_percent": vram_percent,
                "vram_used_bytes": vram_used,
                "vram_total_bytes": vram_total,
                "mapped_kfd_pids": pids,
                "eligible": not reasons,
                "ineligibility_reasons": reasons,
            }
        )
    return devices


def _select_live_device(samples: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], list[Any]]:
    if len(samples) != 3 or [item.get("sample_index") for item in samples] != [0, 1, 2]:
        _fail("h4_malformed", "live H4 requires exactly three ordered samples")
    by_sample = []
    for sample in samples:
        devices = sample.get("devices")
        if not isinstance(devices, list) or not devices:
            _fail("h4_malformed", "live H4 sample has no devices")
        by_sample.append(
            {item["identity"]["container_visible_index"]: item for item in devices}
        )
    if not all(set(table) == set(by_sample[0]) for table in by_sample[1:]):
        _fail("device_mismatch", "visible device set drifted during live H4")
    candidates = []
    for device_index in sorted(by_sample[0]):
        rows = [table[device_index] for table in by_sample]
        identities = [row["identity"] for row in rows]
        if not all(_typed_equal(identity, identities[0]) for identity in identities[1:]):
            continue
        if not all(row["eligible"] for row in rows):
            continue
        key = [
            max(row["vram_used_bytes"] for row in rows),
            device_index,
            identities[0]["unique_id"],
        ]
        candidates.append((key, identities[0]))
    if not candidates:
        _fail("live_gpu_unavailable", "no device passed all three live H4 samples")
    candidates.sort(key=lambda item: tuple(item[0]))
    return plain_value(candidates[0][1]), plain_value(candidates[0][0])


def _probe_live_h4(log_root: Path) -> dict[str, Any]:
    _require_exact_perlee()
    if log_root.exists():
        _fail("already_exists", f"live H4 log root exists: {_rel(log_root)}")
    env = _base_env()
    version_proc, version_command = _run_logged(
        [str(ROCM_SMI), "--version"],
        cwd=ROOT,
        env=env,
        log_root=log_root,
        name="h4-rocm-smi-version",
    )
    version_lines = version_proc.stdout.decode("utf-8", "replace").splitlines()
    if not version_lines or not version_lines[0].startswith("ROCM-SMI version: "):
        _fail("h4_malformed", "ROCm-SMI version output is malformed")
    samples = []
    previous_start: float | None = None
    for sample_index in range(3):
        if previous_start is not None:
            wait = 2.0 - (time.monotonic() - previous_start)
            if wait > 0:
                time.sleep(wait)
        sample_start = time.monotonic()
        spacing = None if previous_start is None else sample_start - previous_start
        device_proc, device_command = _run_logged(
            LIVE_DEVICE_ARGV,
            cwd=ROOT,
            env=env,
            log_root=log_root,
            name=f"h4-sample-{sample_index}-devices",
        )
        process_proc, process_command = _run_logged(
            LIVE_PROCESS_ARGV,
            cwd=ROOT,
            env=env,
            log_root=log_root,
            name=f"h4-sample-{sample_index}-processes",
        )
        pid_map = _parse_pid_gpu_map(process_proc.stdout)
        samples.append(
            {
                "sample_index": sample_index,
                "captured_at": device_command["started_at"],
                "seconds_since_previous": spacing,
                "device_command": device_command,
                "process_command": process_command,
                "devices": _parse_live_devices(device_proc.stdout, pid_map),
            }
        )
        previous_start = sample_start
    selected, selection_key = _select_live_device(samples)
    return {
        "schema_version": "1.0.0",
        "kind": "s10_h4_live_availability",
        "checkpoint_id": "S10",
        "container": "perlee",
        "availability_mode": "live_unreserved",
        "tool_version": version_lines[0].split(": ", 1)[1],
        "tool_command": version_command,
        "policy": plain_value(LIVE_H4_POLICY),
        "samples": samples,
        "selected_device": selected,
        "selection_key": selection_key,
        "claim_limitations": [
            "Observed availability only; no reservation or exclusivity claim",
            "No future-availability or five-day-budget claim",
            "Residual sub-sample contention may remain undetected",
        ],
    }


def _evidence_regular_path(
    relative: Any,
    *,
    role: str,
    expected_path: Path | None = None,
) -> Path:
    if not isinstance(relative, str):
        _fail("manifest_tamper", f"{role} path is not a string")
    safe = _safe_relative_path(relative, context=f"{role} path")
    path = ROOT / safe
    if expected_path is not None and safe != _rel(expected_path):
        _fail("manifest_tamper", f"{role} path substitution")
    resolved = path.resolve()
    allowed = S10_RUN_ROOT.resolve()
    if allowed not in resolved.parents:
        _fail("manifest_tamper", f"{role} path is outside ignored S10 evidence")
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        _fail("manifest_tamper", f"{role} path is absent")
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or path.is_symlink()
    ):
        _fail("manifest_tamper", f"{role} is not an exclusive regular file")
    current = allowed
    for component in resolved.relative_to(allowed).parts[:-1]:
        current = current / component
        ancestor = os.lstat(current)
        if not stat.S_ISDIR(ancestor.st_mode):
            _fail("manifest_tamper", f"{role} has a non-directory ancestor")
    return path


def _load_ignored_ref(
    reference: Mapping[str, Any],
    *,
    role: str,
    expected_path: Path | None = None,
) -> Mapping[str, Any]:
    if not isinstance(reference, dict) or set(reference) != {"path", "raw_sha256"}:
        _fail("manifest_tamper", f"{role} reference field set mismatch")
    if (
        not isinstance(reference["raw_sha256"], str)
        or HASH_RE.fullmatch(reference["raw_sha256"]) is None
    ):
        _fail("manifest_tamper", f"{role} raw hash is malformed")
    path = _evidence_regular_path(
        reference["path"], role=role, expected_path=expected_path
    )
    if sha256_file(path) != reference["raw_sha256"]:
        _fail("manifest_tamper", f"{role} raw hash mismatch")
    document = strict_load_json(path)
    if not isinstance(document, dict):
        _fail("manifest_tamper", f"{role} is not an object")
    return document


def _load_ignored_log(
    reference: Mapping[str, Any],
    *,
    role: str,
    expected_path: Path | None = None,
) -> bytes:
    if (
        not isinstance(reference, dict)
        or set(reference) != {"path", "raw_sha256", "bytes"}
        or isinstance(reference["bytes"], bool)
        or not isinstance(reference["bytes"], int)
        or reference["bytes"] < 0
    ):
        _fail("manifest_tamper", f"{role} log reference field set mismatch")
    path = _evidence_regular_path(
        reference["path"], role=role, expected_path=expected_path
    )
    if (
        path.stat().st_size != reference["bytes"]
        or sha256_file(path) != reference["raw_sha256"]
    ):
        _fail("manifest_tamper", f"{role} log identity mismatch")
    return path.read_bytes()


def _recorded_text(value: str) -> str:
    """Translate this checkout's root to the canonical in-container root."""
    return value.replace(str(ROOT.resolve()), str(CONTAINER_REPO))


def _host_path(recorded_path: Path) -> Path:
    """Resolve an absolute evidence path in either host or container context."""
    try:
        return ROOT / recorded_path.relative_to(CONTAINER_REPO)
    except ValueError:
        return recorded_path


def _verify_command_record(
    record: Any,
    *,
    role: str,
    expected_argv: Sequence[str],
    expected_cwd: Path,
    log_root: Path,
    log_name: str,
    environment_requirements: Mapping[str, str] | None = None,
) -> tuple[bytes, bytes]:
    if (
        not isinstance(record, dict)
        or set(record)
        != {
            "argv",
            "cwd",
            "environment",
            "started_at",
            "ended_at",
            "exit_code",
            "stdout",
            "stderr",
        }
        or record["argv"] != [_recorded_text(str(item)) for item in expected_argv]
        or record["cwd"] != _rel(expected_cwd)
        or record["exit_code"] != 0
    ):
        _fail("manifest_tamper", f"{role} command identity differs")
    _parse_utc(record["started_at"], field=f"{role}.started_at")
    _parse_utc(record["ended_at"], field=f"{role}.ended_at")
    environment = record["environment"]
    allowed_environment = {
        "PATH",
        "LD_LIBRARY_PATH",
        "LIBRARY_PATH",
        "CPATH",
        "CMAKE_PREFIX_PATH",
        "ROCM_PATH",
        "TMPDIR",
        "LANG",
        "LC_ALL",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONHASHSEED",
        "GIT_CEILING_DIRECTORIES",
        "PYTHONPATH",
        "FETCHCONTENT_FULLY_DISCONNECTED",
        "HIPBLASLT_ENABLE_FETCH",
        "ORIGAMI_ENABLE_FETCH",
    }
    if (
        not isinstance(environment, dict)
        or not set(environment).issubset(allowed_environment)
        or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in environment.items()
        )
        or environment.get("PYTHONDONTWRITEBYTECODE") != "1"
        or environment.get("PYTHONHASHSEED") != "0"
        or environment.get("GIT_CEILING_DIRECTORIES") != str(CONTAINER_REPO)
    ):
        _fail("manifest_tamper", f"{role} environment differs")
    for key, value in (environment_requirements or {}).items():
        if environment.get(key) != _recorded_text(value):
            _fail("manifest_tamper", f"{role} environment {key} differs")
    stdout = _load_ignored_log(
        record["stdout"],
        role=f"{role}-stdout",
        expected_path=log_root / f"{log_name}.stdout",
    )
    stderr = _load_ignored_log(
        record["stderr"],
        role=f"{role}-stderr",
        expected_path=log_root / f"{log_name}.stderr",
    )
    return stdout, stderr


def _verify_live_h4_record(
    record: Any,
    *,
    scratch_root: Path,
) -> None:
    expected_fields = {
        "schema_version",
        "kind",
        "checkpoint_id",
        "container",
        "availability_mode",
        "tool_version",
        "tool_command",
        "policy",
        "samples",
        "selected_device",
        "selection_key",
        "claim_limitations",
    }
    if (
        not isinstance(record, dict)
        or set(record) != expected_fields
        or record["schema_version"] != "1.0.0"
        or record["kind"] != "s10_h4_live_availability"
        or record["checkpoint_id"] != "S10"
        or record["container"] != "perlee"
        or record["availability_mode"] != "live_unreserved"
        or not _typed_equal(record["policy"], LIVE_H4_POLICY)
        or record["claim_limitations"]
        != [
            "Observed availability only; no reservation or exclusivity claim",
            "No future-availability or five-day-budget claim",
            "Residual sub-sample contention may remain undetected",
        ]
    ):
        _fail("h4_malformed", "live H4 record identity/policy differs")
    logs = scratch_root / "postlock/lock-probe/logs"
    version_stdout, _ = _verify_command_record(
        record["tool_command"],
        role="h4-rocm-smi-version",
        expected_argv=[str(ROCM_SMI), "--version"],
        expected_cwd=ROOT,
        log_root=logs,
        log_name="h4-rocm-smi-version",
    )
    version_lines = version_stdout.decode("utf-8", "replace").splitlines()
    if (
        not version_lines
        or version_lines[0] != f"ROCM-SMI version: {record['tool_version']}"
    ):
        _fail("h4_malformed", "live H4 tool identity differs")
    samples = record["samples"]
    if (
        not isinstance(samples, list)
        or len(samples) != 3
        or [item.get("sample_index") for item in samples if isinstance(item, dict)]
        != [0, 1, 2]
    ):
        _fail("h4_malformed", "live H4 sample set/order differs")
    rebuilt_samples = []
    for sample_index, sample in enumerate(samples):
        if set(sample) != {
            "sample_index",
            "captured_at",
            "seconds_since_previous",
            "device_command",
            "process_command",
            "devices",
        }:
            _fail("h4_malformed", f"live H4 sample {sample_index} field set differs")
        _parse_utc(sample["captured_at"], field=f"h4.samples[{sample_index}].captured_at")
        spacing = sample["seconds_since_previous"]
        if (
            (sample_index == 0 and spacing is not None)
            or (
                sample_index > 0
                and (
                    isinstance(spacing, bool)
                    or not isinstance(spacing, (int, float))
                    or spacing < 2
                )
            )
        ):
            _fail("h4_malformed", "live H4 sample spacing differs")
        device_stdout, _ = _verify_command_record(
            sample["device_command"],
            role=f"h4-sample-{sample_index}-devices",
            expected_argv=LIVE_DEVICE_ARGV,
            expected_cwd=ROOT,
            log_root=logs,
            log_name=f"h4-sample-{sample_index}-devices",
        )
        process_stdout, _ = _verify_command_record(
            sample["process_command"],
            role=f"h4-sample-{sample_index}-processes",
            expected_argv=LIVE_PROCESS_ARGV,
            expected_cwd=ROOT,
            log_root=logs,
            log_name=f"h4-sample-{sample_index}-processes",
        )
        devices = _parse_live_devices(
            device_stdout, _parse_pid_gpu_map(process_stdout)
        )
        if not _typed_equal(devices, sample["devices"]):
            _fail("h4_malformed", f"live H4 sample {sample_index} semantic drift")
        rebuilt_samples.append({**sample, "devices": devices})
    selected, selection_key = _select_live_device(rebuilt_samples)
    if (
        not _typed_equal(selected, record["selected_device"])
        or not _typed_equal(selection_key, record["selection_key"])
    ):
        _fail("device_mismatch", "live H4 deterministic selection differs")


def _verify_regular_hash_record(
    record: Any,
    *,
    role: str,
    expected_path: Path | None = None,
    include_bytes: bool = False,
) -> Path:
    expected_fields = {"path", "raw_sha256", "bytes"} if include_bytes else {
        "path",
        "raw_sha256",
    }
    if (
        not isinstance(record, dict)
        or set(record) != expected_fields
        or not isinstance(record["raw_sha256"], str)
        or HASH_RE.fullmatch(record["raw_sha256"]) is None
    ):
        _fail("manifest_tamper", f"{role} regular-file record shape differs")
    path = _evidence_regular_path(
        record["path"], role=role, expected_path=expected_path
    )
    if (
        sha256_file(path) != record["raw_sha256"]
        or (
            include_bytes
            and (
                isinstance(record["bytes"], bool)
                or not isinstance(record["bytes"], int)
                or path.stat().st_size != record["bytes"]
            )
        )
    ):
        _fail("manifest_tamper", f"{role} regular-file identity differs")
    return path


def _verify_absolute_hash_record(record: Any, *, role: str) -> Path:
    if (
        not isinstance(record, dict)
        or set(record) != {"path", "raw_sha256"}
        or not isinstance(record["path"], str)
        or not Path(record["path"]).is_absolute()
        or not isinstance(record["raw_sha256"], str)
        or HASH_RE.fullmatch(record["raw_sha256"]) is None
    ):
        _fail("manifest_tamper", f"{role} absolute-file record shape differs")
    path = _host_path(Path(record["path"]))
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        _fail("manifest_tamper", f"{role} absolute file is absent")
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or path.is_symlink()
        or sha256_file(path) != record["raw_sha256"]
    ):
        _fail("manifest_tamper", f"{role} absolute-file identity differs")
    return path


def _verify_dependency_closure(
    dependencies: Any,
    ldd_stdout: bytes,
    *,
    build: Path,
    tag: str,
) -> None:
    if (
        not isinstance(dependencies, list)
        or any(
            not isinstance(item, dict)
            or set(item)
            != {
                "lexical_path",
                "resolved_path",
                "lexical_is_symlink",
                "raw_sha256",
            }
            or not isinstance(item["lexical_path"], str)
            or not Path(item["lexical_path"]).is_absolute()
            or not isinstance(item["resolved_path"], str)
            or not Path(item["resolved_path"]).is_absolute()
            or not isinstance(item["lexical_is_symlink"], bool)
            or (
                item["raw_sha256"] is not None
                and (
                    not isinstance(item["raw_sha256"], str)
                    or HASH_RE.fullmatch(item["raw_sha256"]) is None
                )
            )
            for item in dependencies
        )
        or _parse_ldd_lexical_paths(ldd_stdout)
        != [item["lexical_path"] for item in dependencies]
    ):
        _fail("native_lineage_mismatch", f"native-{tag} dependency table differs")
    in_container = ROOT.resolve() == CONTAINER_REPO.resolve()
    for item in dependencies:
        recorded_lexical = Path(item["lexical_path"])
        is_repo_dependency = False
        try:
            recorded_lexical.relative_to(CONTAINER_REPO)
            is_repo_dependency = True
        except ValueError:
            pass
        # The exact container audit re-hashes every dependency. A host audit
        # cannot substitute its own distro libraries, but it still re-hashes
        # every dependency mounted from the recorded repository.
        if not in_container and not is_repo_dependency:
            continue
        lexical = _host_path(recorded_lexical)
        if not lexical.exists() and not lexical.is_symlink():
            _fail("native_lineage_mismatch", f"native-{tag} dependency is absent")
        resolved = lexical.resolve()
        recorded_resolved = _host_path(Path(item["resolved_path"])).resolve()
        if (
            lexical.is_symlink() is not item["lexical_is_symlink"]
            or resolved != recorded_resolved
            or (
                item["raw_sha256"] is not None
                and (
                    not resolved.is_file()
                    or sha256_file(resolved) != item["raw_sha256"]
                )
            )
        ):
            _fail("native_lineage_mismatch", f"native-{tag} dependency identity differs")
    stinky = [
        item
        for item in dependencies
        if "stinkytofu" in item["lexical_path"]
        or "stinkytofu" in item["resolved_path"]
    ]
    if not stinky or any(
        build.resolve() not in _host_path(Path(item["resolved_path"])).resolve().parents
        for item in stinky
    ):
        _fail("native_lineage_mismatch", f"native-{tag} stinky lineage differs")


def _verify_native_raw_manifest(
    manifest: Mapping[str, Any],
    tracked_run: Mapping[str, Any],
    *,
    scratch_root: Path,
    tag: str,
) -> None:
    if set(manifest) != {
        "source_trees",
        "configure",
        "build",
        "identities",
        "binary",
        "build_info",
        "dependency_probe",
        "dependencies",
        "fetch_detected",
        "deps_directory_present",
        "installed_rocisa_used",
    }:
        _fail("manifest_tamper", f"native-{tag} field set differs")
    run_root = scratch_root / f"run-{tag}"
    integration = run_root / "integration"
    build = run_root / "native-build"
    logs = scratch_root / "logs"
    fetch_environment = {
        "FETCHCONTENT_FULLY_DISCONNECTED": "ON",
        "HIPBLASLT_ENABLE_FETCH": "OFF",
        "ORIGAMI_ENABLE_FETCH": "OFF",
    }
    configure_stdout, configure_stderr = _verify_command_record(
        manifest["configure"],
        role=f"native-{tag}-configure",
        expected_argv=_native_configure_argv(integration, build),
        expected_cwd=integration,
        log_root=logs,
        log_name=f"{tag}-native-configure",
        environment_requirements=fetch_environment,
    )
    build_stdout, build_stderr = _verify_command_record(
        manifest["build"],
        role=f"native-{tag}-build",
        expected_argv=_native_build_argv(build),
        expected_cwd=integration,
        log_root=logs,
        log_name=f"{tag}-native-build",
        environment_requirements=fetch_environment,
    )
    fetch_re = re.compile(
        rb"(Cloning into|Performing download|Downloading|git clone|Fetching content)",
        re.IGNORECASE,
    )
    if any(
        fetch_re.search(raw)
        for raw in (configure_stdout, configure_stderr, build_stdout, build_stderr)
    ):
        _fail("network_fetch_detected", f"native-{tag} fetch evidence")
    if (
        manifest["source_trees"] != DUCTILE_TREES
        or manifest["fetch_detected"] is not False
        or manifest["deps_directory_present"] is not False
        or manifest["installed_rocisa_used"] is not False
        or any(path.name == "_deps" for path in build.rglob("_deps"))
    ):
        _fail("native_lineage_mismatch", f"native-{tag} policy differs")
    binary = _verify_regular_hash_record(
        manifest["binary"], role=f"native-{tag}-binary"
    )
    if (
        binary.parent != build / "rocisa"
        or not binary.name.startswith("_rocisa")
        or binary.suffix != ".so"
        or tracked_run["native_binary_sha256"]
        != manifest["binary"]["raw_sha256"]
    ):
        _fail("native_lineage_mismatch", f"native-{tag} binary binding differs")
    build_info = _verify_regular_hash_record(
        manifest["build_info"],
        role=f"native-{tag}-build-info",
        expected_path=build / "rocisa/_build_info.py",
    )
    build_info_text = build_info.read_text(encoding="utf-8")
    if (
        _recorded_text(str(integration)) not in build_info_text
        or _recorded_text(str(ROOT / "projects")) in build_info_text
    ):
        _fail("native_lineage_mismatch", f"native-{tag} build-info source differs")
    ldd_stdout, _ = _verify_command_record(
        manifest["dependency_probe"],
        role=f"native-{tag}-ldd",
        expected_argv=["ldd", str(binary)],
        expected_cwd=integration,
        log_root=logs,
        log_name=f"{tag}-native-ldd",
    )
    _verify_dependency_closure(
        manifest["dependencies"], ldd_stdout, build=build, tag=tag
    )
    identities = manifest["identities"]
    if not isinstance(identities, dict) or set(identities) != {
        "cmake",
        "compiler",
        "python",
    }:
        _fail("manifest_tamper", f"native-{tag} identities differ")
    for name, argv in (
        ("cmake", [str(CMAKE), "--version"]),
        ("compiler", [str(COMPILER), "--version"]),
        ("python", [str(PYTHON), "-S", "--version"]),
    ):
        _verify_command_record(
            identities[name],
            role=f"native-{tag}-{name}",
            expected_argv=argv,
            expected_cwd=integration,
            log_root=logs,
            log_name=f"{tag}-{name}-version",
        )


def _verify_import_closure(
    probed_imports: Any,
    recorded_imports: Any,
    tracked_imports: Any,
    *,
    python_paths: Sequence[Path],
    integration: Path,
    build: Path,
    tag: str,
) -> None:
    if (
        not _typed_equal(probed_imports, recorded_imports)
        or not _typed_equal(tracked_imports, recorded_imports)
    ):
        _fail("forbidden_import", f"generation-{tag} import table differs")
    expected_modules = {
        "rocisa",
        "rocisa._rocisa",
        "Tensile",
        "Tensile.LibraryIO",
        "Tensile.backends.ductile_backend",
        "Tensile.ductile.algorithm.ga",
        "Tensile.ductile.core.space",
        "geko",
        "geko.config_generator.config_generator",
        "geko.config_generator.load_input_config",
    }
    if not isinstance(probed_imports, dict) or set(probed_imports) != expected_modules:
        _fail("forbidden_import", f"generation-{tag} import module set differs")
    allowed_roots = [path.resolve() for path in python_paths]
    exact_module_paths = {
        "rocisa": build / "rocisa/__init__.py",
        "Tensile": integration / "projects/hipblaslt/tensilelite/Tensile/__init__.py",
        "Tensile.LibraryIO": (
            integration / "projects/hipblaslt/tensilelite/Tensile/LibraryIO.py"
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
        "geko": integration / "projects/hipblaslt/utilities/geko/geko/__init__.py",
        "geko.config_generator.config_generator": (
            integration
            / "projects/hipblaslt/utilities/geko/geko/config_generator/config_generator.py"
        ),
        "geko.config_generator.load_input_config": (
            integration
            / "projects/hipblaslt/utilities/geko/geko/config_generator/load_input_config.py"
        ),
    }
    for name, item in probed_imports.items():
        imported = _verify_absolute_hash_record(
            item, role=f"generation-{tag}-import-{name}"
        ).resolve()
        if not any(imported == base or base in imported.parents for base in allowed_roots):
            _fail("forbidden_import", f"{name} imported from {imported}")
        if name.startswith("Tensile") and (
            integration / "projects/hipblaslt/tensilelite"
        ).resolve() not in imported.parents:
            _fail("forbidden_import", f"{name} did not use pinned TensileLite")
        if name.startswith("geko") and (
            integration / "projects/hipblaslt/utilities/geko"
        ).resolve() not in imported.parents:
            _fail("forbidden_import", f"{name} did not use pinned GEKO")
        if name.startswith("rocisa") and build.resolve() not in imported.parents:
            _fail("forbidden_import", f"{name} did not use fresh rocisa")
        if name == "rocisa._rocisa":
            if (
                imported.parent != (build / "rocisa").resolve()
                or not imported.name.startswith("_rocisa")
                or imported.suffix != ".so"
            ):
                _fail("forbidden_import", f"{name} path differs")
        elif imported != exact_module_paths[name].resolve():
            _fail("forbidden_import", f"{name} path differs")


def _verify_output_manifest_closure(
    output_manifest: Any,
    output_manifest_sha256: Any,
    tracked_manifest_sha256: Any,
    *,
    generation: Path,
    tag: str,
) -> None:
    live_manifest = _output_manifest(generation)
    if (
        not _typed_equal(output_manifest, live_manifest)
        or output_manifest_sha256 != canonical_sha256(live_manifest)
        or tracked_manifest_sha256 != output_manifest_sha256
    ):
        _fail("generation_manifest_mismatch", f"generation-{tag} output closure differs")


def _verify_generation_raw_manifest(
    manifest: Mapping[str, Any],
    tracked_run: Mapping[str, Any],
    *,
    scratch_root: Path,
    tag: str,
    derived_input: Path,
) -> None:
    if set(manifest) != {
        "command",
        "module_probe",
        "imports",
        "python_path_order",
        "output_manifest",
        "output_manifest_sha256",
    }:
        _fail("manifest_tamper", f"generation-{tag} field set differs")
    run_root = scratch_root / f"run-{tag}"
    integration = run_root / "integration"
    build = run_root / "native-build"
    generation = run_root / "generation"
    output = generation / "out"
    logs = scratch_root / "logs"
    python_paths = _python_path(integration, build)
    python_path_text = os.pathsep.join(str(path) for path in python_paths)
    _verify_command_record(
        manifest["command"],
        role=f"generation-{tag}-command",
        expected_argv=_generation_argv(integration, derived_input, output),
        expected_cwd=integration,
        log_root=logs,
        log_name=f"{tag}-generation",
        environment_requirements={"PYTHONPATH": python_path_text},
    )
    probe_stdout, _ = _verify_command_record(
        manifest["module_probe"],
        role=f"generation-{tag}-module-probe",
        expected_argv=[str(PYTHON), "-S", "-c", _module_probe_code()],
        expected_cwd=integration,
        log_root=logs,
        log_name=f"{tag}-module-probe",
        environment_requirements={"PYTHONPATH": python_path_text},
    )
    try:
        probed_imports = json.loads(probe_stdout)
    except json.JSONDecodeError as exc:
        raise S10Error(str(exc), code="manifest_tamper") from exc
    _verify_import_closure(
        probed_imports,
        manifest["imports"],
        tracked_run["imports"],
        python_paths=python_paths,
        integration=integration,
        build=build,
        tag=tag,
    )
    expected_path_order = [
        _rel(path) if ROOT in path.resolve().parents else str(path)
        for path in python_paths
    ]
    if (
        manifest["python_path_order"] != expected_path_order
    ):
        _fail("generation_manifest_mismatch", f"generation-{tag} closure differs")
    _verify_output_manifest_closure(
        manifest["output_manifest"],
        manifest["output_manifest_sha256"],
        tracked_run["generation_manifest_sha256"],
        generation=generation,
        tag=tag,
    )


def _verify_raw_lineage(
    provenance: Mapping[str, Any],
    *,
    expected_scratch_root: Path | None = None,
) -> Path:
    derived_record = provenance.get("derived_input")
    if not isinstance(derived_record, dict) or set(derived_record) != {
        "path",
        "raw_sha256",
        "derivation",
    }:
        _fail("manifest_tamper", "derived-input record shape differs")
    relative = _safe_relative_path(
        derived_record["path"], context="derived-input path"
    )
    derived_path = ROOT / relative
    scratch_root = _assert_scratch_root(derived_path.parent)
    if (
        derived_path.name != "derived-input.yaml"
        or (
            expected_scratch_root is not None
            and scratch_root != _assert_scratch_root(expected_scratch_root)
        )
    ):
        _fail("manifest_tamper", "derived-input scratch-root binding differs")
    derived_path = _evidence_regular_path(
        relative, role="derived-input", expected_path=scratch_root / "derived-input.yaml"
    )
    expected_bytes, expected_derivation = _derive_input()
    if (
        sha256_file(derived_path) != derived_record["raw_sha256"]
        or derived_path.read_bytes() != expected_bytes
        or not _typed_equal(derived_record["derivation"], expected_derivation)
    ):
        _fail("manifest_tamper", "derived-input semantic closure differs")
    runs = provenance.get("runs")
    if (
        not isinstance(runs, list)
        or len(runs) != 2
        or [run.get("tag") for run in runs if isinstance(run, dict)] != ["a", "b"]
    ):
        _fail("manifest_tamper", "raw lineage run set/order differs")
    generation_manifests = []
    for run in runs:
        tag = run["tag"]
        native = _load_ignored_ref(
            run["native"],
            role=f"native-{tag}",
            expected_path=scratch_root / "manifests" / f"native-{tag}.json",
        )
        generation = _load_ignored_ref(
            run["generation"],
            role=f"generation-{tag}",
            expected_path=scratch_root / "manifests" / f"generation-{tag}.json",
        )
        _verify_native_raw_manifest(
            native, run, scratch_root=scratch_root, tag=tag
        )
        _verify_generation_raw_manifest(
            generation,
            run,
            scratch_root=scratch_root,
            tag=tag,
            derived_input=derived_path,
        )
        generation_manifests.append(generation)
    if (
        not _typed_equal(
            generation_manifests[0]["output_manifest"],
            generation_manifests[1]["output_manifest"],
        )
        or provenance["generation_parity"]["manifest_sha256"]
        != generation_manifests[0]["output_manifest_sha256"]
    ):
        _fail("generation_manifest_mismatch", "persisted dual-generation parity differs")
    qualifying_relative = provenance["generation_parity"]["qualifying_relative_path"]
    actual = provenance["actual_yaml"]
    for tag, field in (("a", "run_a_path"), ("b", "run_b_path")):
        expected_actual = (
            scratch_root / f"run-{tag}" / "generation" / qualifying_relative
        )
        if (
            actual[field] != _rel(expected_actual)
            or sha256_file(
                _evidence_regular_path(
                    actual[field],
                    role=f"actual-yaml-{tag}",
                    expected_path=expected_actual,
                )
            )
            != actual[f"run_{tag}_raw_sha256"]
        ):
            _fail("generation_manifest_mismatch", f"actual YAML {tag} binding differs")
    return scratch_root


def _verify_oracle_lineage(
    provenance: Mapping[str, Any],
    *,
    scratch_root: Path,
) -> None:
    consumption = provenance.get("consumption")
    if not isinstance(consumption, dict):
        _fail("manifest_tamper", "tracked oracle summary absent")
    oracle_runs = consumption.get("oracle_runs")
    if (
        not isinstance(oracle_runs, list)
        or [item.get("tag") for item in oracle_runs if isinstance(item, dict)]
        != ["a", "b"]
    ):
        _fail("manifest_tamper", "tracked oracle run set/order differs")
    current_document = plain_value(_raw_document(INPUT_PATH))
    expected_witness = _raw_o4_witness(current_document, sha256_file(INPUT_PATH))
    expected_model = _independent_source_model(expected_witness)
    payloads = []
    for run in oracle_runs:
        if set(run) != {
            "tag",
            "raw_document",
            "raw_witness",
            "source_model",
            "actual_runtime",
        }:
            _fail("manifest_tamper", f"oracle {run.get('tag')} reference shape")
        tag = run["tag"]
        raw_document = _load_ignored_ref(
            run["raw_document"],
            role=f"oracle-{tag}-raw-document",
            expected_path=scratch_root / "manifests" / f"oracle-{tag}-raw-document.json",
        )
        witness = _load_ignored_ref(
            run["raw_witness"],
            role=f"oracle-{tag}-raw-witness",
            expected_path=scratch_root / "manifests" / f"oracle-{tag}-raw-witness.json",
        )
        model = _load_ignored_ref(
            run["source_model"],
            role=f"oracle-{tag}-source-model",
            expected_path=scratch_root / "manifests" / f"oracle-{tag}-source-model.json",
        )
        actual = dict(
            _load_ignored_ref(
                run["actual_runtime"],
                role=f"oracle-{tag}-actual-runtime",
                expected_path=scratch_root / "manifests" / f"oracle-{tag}-actual-runtime.json",
            )
        )
        if (
            not _typed_equal(raw_document, current_document)
            or not _typed_equal(witness, expected_witness)
            or not _typed_equal(model, expected_model)
        ):
            _fail("manifest_tamper", f"oracle {tag} source layer differs")
        expected_actual_keys = {
            "accepted_stderr",
            "command",
            "constant_parameters",
            "document_sha256",
            "expanded_group_count",
            "expanded_groups",
            "expanded_groups_sha256",
            "fork_parameters",
            "numpy",
            "ordered_axis_records",
            "probabilities",
            "probability_axis_order",
            "raw_group_count",
            "raw_groups_sha256",
            "reduce_fn",
            "resolved_backend_o4",
            "resolved_initial_pop_size",
            "search_space_map",
            "search_space_map_sha256",
            "search_space_order",
            "soo",
            "weight_beta",
            "weights",
            "weights_sha256",
        }
        if set(actual) != expected_actual_keys:
            _fail("manifest_tamper", f"oracle {tag} actual field set differs")
        command = actual.pop("command")
        integration = scratch_root / f"run-{tag}" / "integration"
        build = scratch_root / f"run-{tag}" / "native-build"
        actual_path = (
            scratch_root
            / f"run-{tag}"
            / "generation"
            / provenance["generation_parity"]["qualifying_relative_path"]
        )
        stdout, stderr = _verify_command_record(
            command,
            role=f"oracle-{tag}-command",
            expected_argv=[
                str(PYTHON),
                "-S",
                "-c",
                _consume_probe_code(),
                str(actual_path),
            ],
            expected_cwd=integration,
            log_root=scratch_root / "logs",
            log_name=f"{tag}-ductile-consumption",
            environment_requirements={
                "PYTHONPATH": os.pathsep.join(
                    str(path) for path in _python_path(integration, build)
                )
            },
        )
        if (
            stderr.decode("utf-8", errors="strict") != EXPECTED_CONSUMER_STDERR
            or actual.get("accepted_stderr") != EXPECTED_CONSUMER_STDERR
        ):
            _fail("manifest_tamper", f"oracle {tag} accepted stderr differs")
        parsed = dict(_parse_consumer_stdout(stdout))
        semantic_actual = copy.deepcopy(actual)
        semantic_actual.pop("accepted_stderr")
        if not _typed_equal(parsed, semantic_actual):
            _fail("manifest_tamper", f"oracle {tag} stdout/payload differs")
        _validate_model_runtime(expected_witness, expected_model, parsed, tag=tag)
        semantic_actual["accepted_stderr"] = EXPECTED_CONSUMER_STDERR
        payloads.append(semantic_actual)
    if not _typed_equal(payloads[0], payloads[1]):
        _fail("ductile_parity_mismatch", "persisted dual-root runtime differs")

    normalized_axis_table = [
        {
            key: record[key]
            for key in (
                "index",
                "axis",
                "origin",
                "candidate_count",
                "candidates_sha256",
            )
        }
        for record in expected_model["ordered_axis_records"]
    ]
    expected_hashes = {
        "raw_yaml_sha256": expected_witness["raw_sha256"],
        "raw_groups_sha256": expected_witness["groups_sha256"],
        "expanded_groups_sha256": expected_model["groups_sha256"],
        "legacy_space_map_sha256": expected_model["legacy_space_map_sha256"],
        "axis_order_sha256": expected_model["axis_order_sha256"],
        "ordered_axis_records_sha256": expected_model[
            "ordered_axis_records_sha256"
        ],
        "ordered_map_sha256": expected_model["ordered_map_sha256"],
        "raw_weights_sha256": expected_model["raw_weights_sha256"],
        "resolved_weights_sha256": expected_model["resolved_weights_sha256"],
    }
    actual_hash = canonical_sha256(payloads[0])
    oracle_hash = canonical_sha256(
        {
            "raw_witness": expected_witness,
            "source_model": expected_model,
            "actual_runtime": payloads[0],
        }
    )
    if (
        consumption.get("oracle_schema") != "s10_three_layer_ductile_oracle_v1"
        or consumption.get("fresh_root_count") != 2
        or consumption.get("each_root_independently_matched_source_model") is not True
        or consumption.get("cross_root_parity") is not True
        or consumption.get("raw_witness_sha256")
        != canonical_sha256(expected_witness)
        or consumption.get("source_model_sha256")
        != canonical_sha256(expected_model)
        or consumption.get("actual_runtime_sha256") != actual_hash
        or consumption.get("oracle_sha256") != oracle_hash
        or consumption.get("raw_partition_equation") != "30=27+3"
        or not _typed_equal(
            consumption.get("raw_partition_table"),
            expected_witness["partition_table"],
        )
        or not _typed_equal(
            consumption.get("axis_index_table"), normalized_axis_table
        )
        or not _typed_equal(
            consumption.get("parameter_table"), expected_model["parameter_table"]
        )
        or not _typed_equal(
            consumption.get("group_index_table"), expected_model["group_index_table"]
        )
        or not _typed_equal(
            consumption.get("weight_table"), expected_model["weight_table"]
        )
        or consumption.get("hashes") != expected_hashes
        or consumption.get("accepted_consumer_stderr") != EXPECTED_CONSUMER_STDERR
        or consumption.get("source_provenance")
        != expected_model["source_identities"]
        or consumption.get("weight_beta")
        != {
            "raw_present": False,
            "resolved": expected_model["weight_beta"],
            "origin": expected_model["weight_beta_origin"],
        }
        or not _typed_equal(
            consumption.get("probability_evidence"),
            {
                "axes": list(expected_model["probabilities"]),
                "records": expected_model["probabilities"],
                "numpy": expected_model["numpy"],
                "full_itemwise_and_byte_parity": True,
            },
        )
        or consumption.get("soo") is not False
        or consumption.get("reduce_fn") != "max"
    ):
        _fail("manifest_tamper", "tracked oracle parity/index tables differ")


def _verify_integration_lineage(
    provenance: Mapping[str, Any],
    *,
    scratch_root: Path,
    phase: str | None = None,
) -> list[dict[str, Any]]:
    seals = []
    semantic_hashes = []
    for run in provenance["runs"]:
        semantic = _load_ignored_ref(
            run["integration_semantic"],
            role=f"integration-{run['tag']}-semantic",
            expected_path=(
                scratch_root
                / "manifests"
                / f"integration-{run['tag']}-semantic.json"
            ),
        )
        wrapper = _load_ignored_ref(
            run["integration"],
            role=f"integration-{run['tag']}-wrapper",
            expected_path=(
                scratch_root / "manifests" / f"integration-{run['tag']}.json"
            ),
        )
        if (
            set(wrapper)
            != {
                "schema_version",
                "kind",
                "materialization_policy",
                "root",
                "semantic_manifest",
                "phase_seals",
            }
            or wrapper["schema_version"] != "1.0.0"
            or wrapper["kind"] != "s10_integration_run_manifest"
            or wrapper["materialization_policy"] != MATERIALIZATION_POLICY
            or wrapper["semantic_manifest"] != run["integration_semantic"]
        ):
            _fail("manifest_tamper", f"integration {run['tag']} wrapper mismatch")
        if (
            semantic.get("materialization_policy") != MATERIALIZATION_POLICY
            or semantic.get("resolution_inventory_sha256")
            != DUCTILE_SYMLINK_INVENTORY_SHA256
            or semantic.get("counts")
            != {
                "ductile_regular": DUCTILE_REGULAR_COUNT,
                "ductile_symlink": DUCTILE_SYMLINK_COUNT,
                "geko_regular": GEKO_REGULAR_COUNT,
                "regular": INTEGRATION_REGULAR_COUNT,
                "symlink": DUCTILE_SYMLINK_COUNT,
                "leaves": INTEGRATION_LEAF_COUNT,
                "directories": len(semantic.get("directory_closure", [])),
            }
        ):
            _fail("manifest_tamper", f"integration {run['tag']} semantic policy mismatch")
        semantic_body = {
            key: value for key, value in semantic.items() if key != "manifest_sha256"
        }
        if (
            semantic.get("manifest_sha256") != canonical_sha256(semantic_body)
            or run["integration_manifest_sha256"] != semantic["manifest_sha256"]
            or run["integration_wrapper_sha256"] != run["integration"]["raw_sha256"]
        ):
            _fail("manifest_tamper", f"integration {run['tag']} identity mismatch")
        if canonical_sha256(semantic["directory_closure"]) != semantic[
            "directory_closure_sha256"
        ]:
            _fail("manifest_tamper", f"integration {run['tag']} directory closure mismatch")
        if canonical_sha256(semantic["resolution_inventory"]) != semantic[
            "resolution_inventory_sha256"
        ]:
            _fail("manifest_tamper", f"integration {run['tag']} resolution inventory mismatch")
        root = ROOT / wrapper["root"]
        expected_root = scratch_root / f"run-{run['tag']}" / "integration"
        resolved_root = root.resolve()
        if (
            S10_RUN_ROOT.resolve() not in resolved_root.parents
            or resolved_root != expected_root.resolve()
        ):
            _fail("manifest_tamper", f"integration {run['tag']} root outside S10")
        audit = _scan_integration(root, semantic)
        expected_phases = [
            "after-materialization",
            "before-native-build",
            "after-native-build",
            "before-generation",
            "after-generation",
            "before-ductile-consumption",
            "after-ductile-consumption",
        ]
        recorded = wrapper["phase_seals"]
        if (
            not isinstance(recorded, list)
            or [item.get("phase") for item in recorded] != expected_phases
            or any(item.get("audit") != audit for item in recorded)
        ):
            _fail("phase_drift", f"integration {run['tag']} phase seals mismatch")
        semantic_hashes.append(run["integration_semantic"]["raw_sha256"])
        if phase is not None:
            seal = {
                "schema_version": "1.0.0",
                "kind": "s10_integration_phase_seal",
                "tag": run["tag"],
                "phase": phase,
                "semantic_manifest": run["integration_semantic"],
                "run_manifest": run["integration"],
                "root": wrapper["root"],
                "audit": audit,
            }
            seal_path = (
                root.parent.parent
                / "seals"
                / f"{run['tag']}-{phase}.json"
            )
            if seal_path.exists():
                if strict_load_json(seal_path) != seal:
                    _fail("phase_drift", f"phase seal drift: {_rel(seal_path)}")
            else:
                seal_path.parent.mkdir(parents=True, exist_ok=True)
                atomic_write_json(seal_path, seal)
            seals.append({"path": _rel(seal_path), "raw_sha256": sha256_file(seal_path)})
    if len(set(semantic_hashes)) != 1:
        _fail("integration_parity_mismatch", "dual-root semantic manifests differ")
    return seals


def _verify_prelock_artifacts(
    *,
    phase: str | None = None,
    expected_scratch_root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    provenance = strict_load_json(PROVENANCE_PATH)
    sizes = strict_load_json(SIZE_REGISTRY_PATH)
    _validate(provenance, context="S10 provenance")
    _validate(sizes, context="S10 size registry")
    _verify_successor_fields(provenance, role="S10 provenance")
    actual_hash = sha256_file(INPUT_PATH)
    actual = provenance["actual_yaml"]
    if not (
        actual["run_a_raw_sha256"]
        == actual["run_b_raw_sha256"]
        == actual["tracked_copy_raw_sha256"]
        == actual_hash
    ):
        _fail("raw_copy_hash_mismatch", "actual YAML binding mismatch")
    if sizes["same_space"]["raw_yaml_sha256"] != actual_hash:
        _fail("lock_binding_mismatch", "size registry actual YAML mismatch")
    mapping = provenance["mapping_selection"]
    if len(mapping["candidates"]) != 10 or len(mapping["anchor_hashes"]) != 3:
        _fail("lock_binding_mismatch", "mapping-ten/anchor cardinality mismatch")
    scratch_root = _verify_raw_lineage(
        provenance, expected_scratch_root=expected_scratch_root
    )
    _verify_oracle_lineage(provenance, scratch_root=scratch_root)
    _verify_integration_lineage(
        provenance, scratch_root=scratch_root, phase=phase
    )
    return provenance, sizes


def prelock_check(scratch_root: Path) -> dict[str, Any]:
    _reject_early_postlock_targets()
    _assert_scratch_root(scratch_root)
    _preflight(require_outputs=True)
    provenance, sizes = _verify_prelock_artifacts(
        phase="prelock-check",
        expected_scratch_root=scratch_root,
    )
    return {
        "status": "PRELOCK_PASS",
        "H4": "LIVE_PROBE_REQUIRED",
        "h4": None,
        "actual_yaml_sha256": provenance["actual_yaml"]["tracked_copy_raw_sha256"],
        "selected_sizes": sizes["selected_sizes"],
        "postlock_targets_absent": True,
    }


def _bound_file(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        _fail("lock_binding_mismatch", f"bound file absent/unsafe: {_rel(path)}")
    return {"path": _rel(path), "raw_sha256": sha256_file(path)}


def _derived_lock(base: Mapping[str, Any]) -> dict[str, Any]:
    body = plain_value(base)
    if "lock_id" in body or "body_sha256" in body:
        _fail("lock_binding_mismatch", "derived fields supplied in lock base")
    digest = canonical_sha256(body)
    return {**body, "body_sha256": digest, "lock_id": f"s10-lock-{digest}"}


def create_lock(plan_b: Path) -> dict[str, Any]:
    _reject_early_postlock_targets()
    _preflight(require_outputs=True)
    provenance, sizes = _verify_prelock_artifacts(phase="immediately-pre-lock")
    scratch_root = (ROOT / provenance["derived_input"]["path"]).parent.resolve()
    scratch_root = _assert_scratch_root(scratch_root)
    if plan_b.name != "plan_b.md" or plan_b.parent.resolve() != S10_RUN_ROOT.resolve():
        _fail("wrong_plan_b", f"unexpected Plan-B path: {plan_b}")
    if not plan_b.is_file():
        _fail("wrong_plan_b", "frozen Plan-B absent")
    if sha256_file(plan_b) != FROZEN_PLAN_B_SHA256:
        _fail("wrong_plan_b", "frozen Plan-B byte identity differs")
    plan_a = S10_RUN_ROOT / "plan_a.md"
    if not plan_a.is_file() or sha256_file(plan_a) != AMENDED_PLAN_A_SHA256:
        _fail("authority_mismatch", "amended Plan-A byte identity differs")
    h4 = _probe_live_h4(scratch_root / "postlock/lock-probe/logs")
    _verify_live_h4_record(h4, scratch_root=scratch_root)
    environment = {
        "schema_version": "1.0.0",
        "kind": "s10_environment",
        "checkpoint_id": "S10",
        "status": "prelock_complete",
        "created_at": _utc_now(),
        "container": "perlee",
        "repo_mount": "/src/rocm-libraries",
        "arch": "gfx942",
        "availability_mode": "live_unreserved",
        "selected_device": h4["selected_device"],
        "h4": h4,
        "tool_identities": [
            run["native"]
            for run in provenance["runs"]
        ],
        "prohibitions": {
            "network_fetch": True,
            "dependency_install": True,
            "container_mutation": True,
            "other_container_access": True,
        },
    }
    _validate(environment, context="S10 environment")
    atomic_write_json(ENVIRONMENT_PATH, environment)
    lock_base = {
        "schema_version": "1.0.0",
        "kind": "s10_stage1_entry_lock",
        "checkpoint_id": "S10",
        "state": "effective",
        "created_at": _utc_now(),
        "generation": provenance["generation"],
        "evidence_reuse": provenance["evidence_reuse"],
        "parent_lock": provenance["parent_lock"],
        "recovery_authority": provenance["recovery_authority"],
        "s00_closure_commit": S00_CLOSURE,
        "authorities": provenance["authorities"],
        "adjudication": provenance["recovery_authority"],
        "plan_a": _bound_file(plan_a),
        "plan_b": {"path": _rel(plan_b), "raw_sha256": sha256_file(plan_b)},
        "implementation_whitelist": IMPLEMENTATION_WHITELIST,
        "delivery_whitelist": DELIVERY_WHITELIST,
        "forbidden_roots": FORBIDDEN_ROOTS,
        "bound_files": [
            _bound_file(path)
            for path in (
                Path(__file__),
                ROOT
                / "projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10_entry.py",
                SCHEMA_PATH,
                CONTRACT_PATH,
                INPUT_PATH,
                PROVENANCE_PATH,
                SIZE_REGISTRY_PATH,
                ENVIRONMENT_PATH,
            )
        ],
        "integration_manifests": [
            {
                "tag": run["tag"],
                "manifest_sha256": run["integration_manifest_sha256"],
                "semantic": run["integration_semantic"],
                "run": run["integration"],
            }
            for run in provenance["runs"]
        ],
        "native_manifests": [
            {"tag": run["tag"], "binary_sha256": run["native_binary_sha256"], "raw": run["native"]}
            for run in provenance["runs"]
        ],
        "generation_manifests": [
            {"tag": run["tag"], "manifest_sha256": run["generation_manifest_sha256"], "raw": run["generation"]}
            for run in provenance["runs"]
        ],
        "actual_yaml_sha256": sha256_file(INPUT_PATH),
        "size_registry_sha256": sha256_file(SIZE_REGISTRY_PATH),
        "environment_sha256": sha256_file(ENVIRONMENT_PATH),
        "h4_semantic_sha256": canonical_sha256(h4),
        "mapping_candidates": provenance["mapping_selection"]["candidates"],
        "anchor_hashes": provenance["mapping_selection"]["anchor_hashes"],
        "device": h4["selected_device"],
        "noise_schedule": {
            "anchors": 3,
            "sizes": 3,
            "repeats": 7,
            "observations_per_level": 63,
            "levels": [1, 2, 4],
            "cv_p95_threshold": 0.005,
            "warmup_policy": "fixed from generated YAML",
            "balanced_order_seed": int(sha256_file(INPUT_PATH)[:16], 16),
        },
        "report_target": (
            "study_docs/research/ductile-origami-warmstart/reports/staged/"
            "s10-stage1-entry-gate-report.md"
        ),
    }
    lock = _derived_lock(lock_base)
    _validate(lock, context="S10 effective lock")
    raw_hash = write_effective_lock(LOCK_PATH, lock, _schema())
    return {
        "status": "LOCK_EFFECTIVE",
        "lock_id": lock["lock_id"],
        "raw_sha256": raw_hash,
        "availability_mode": "live_unreserved",
        "device": h4["selected_device"],
        "selection_key": h4["selection_key"],
    }


def _load_lock() -> tuple[dict[str, Any], str]:
    _verify_r10_parent_archive()
    if not LOCK_PATH.is_file():
        if R10_CLAIM_PATH.is_file():
            _fail(
                "transition_claimed",
                "successor transition is claimed and no active child lock exists",
            )
        _fail("lock_binding_mismatch", "effective lock is absent")
    lock = strict_load_json(LOCK_PATH)
    _validate(lock, context="S10 effective lock")
    _verify_successor_fields(lock, role="S10 effective lock")
    rebuilt = _derived_lock(
        {key: value for key, value in lock.items() if key not in {"lock_id", "body_sha256"}}
    )
    if lock != rebuilt:
        _fail("lock_binding_mismatch", "lock derived identity mismatch")
    for item in lock["bound_files"]:
        path = ROOT / item["path"]
        if not path.is_file() or sha256_file(path) != item["raw_sha256"]:
            _fail("lock_binding_mismatch", f"bound file drift: {item['path']}")
    environment = strict_load_json(ENVIRONMENT_PATH)
    _validate(environment, context="S10 environment")
    provenance = strict_load_json(PROVENANCE_PATH)
    _validate(provenance, context="S10 provenance")
    _verify_successor_fields(provenance, role="S10 provenance")
    if (
        lock["environment_sha256"]
        in {
            R8_PARENT_ENVIRONMENT_SHA256,
            R9_PARENT_ENVIRONMENT_SHA256,
            R10_PARENT_ENVIRONMENT_SHA256,
        }
        or lock["lock_id"]
        in {R8_PARENT_LOCK_ID, R9_PARENT_LOCK_ID, R10_PARENT_LOCK_ID}
        or lock["body_sha256"]
        in {
            R8_PARENT_LOCK_BODY_SHA256,
            R9_PARENT_LOCK_BODY_SHA256,
            R10_PARENT_LOCK_BODY_SHA256,
        }
    ):
        _fail("parent_evidence_reuse", "active child reuses parent identity")
    scratch_root = _assert_scratch_root(
        (ROOT / provenance["derived_input"]["path"]).parent
    )
    _verify_live_h4_record(environment["h4"], scratch_root=scratch_root)
    if (
        lock["environment_sha256"] != sha256_file(ENVIRONMENT_PATH)
        or lock["h4_semantic_sha256"] != canonical_sha256(environment["h4"])
        or not _typed_equal(lock["device"], environment["selected_device"])
    ):
        _fail("lock_binding_mismatch", "live H4/environment lock binding differs")
    return lock, sha256_file(LOCK_PATH)


def _require_no_existing(path: Path) -> None:
    if path.exists() or path.is_symlink():
        _fail("already_exists", f"target exists: {_rel(path)}")


def _require_not_terminal(command: str) -> None:
    if DECISION_PATH.exists() or DECISION_PATH.is_symlink():
        _fail(
            "terminal_command_refused",
            f"{command} is forbidden after the terminal S10 decision",
        )


def _write_exclusive_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        _fail("already_exists", f"exclusive target exists: {_rel(path)}")
    data = canonical_json_bytes(document) + b"\n"
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        raise


def _active_scratch_root() -> Path:
    provenance = strict_load_json(PROVENANCE_PATH)
    path = ROOT / provenance["derived_input"]["path"]
    return _assert_scratch_root(path.parent)


def _parse_marked_json(raw: bytes, *, phase: str) -> Mapping[str, Any]:
    """Extract the one machine record from a noisy pinned-tool stdout stream."""

    matches = [
        line[len(POSTLOCK_RESULT_MARKER) :]
        for line in raw.decode("utf-8", "replace").splitlines()
        if line.startswith(POSTLOCK_RESULT_MARKER)
    ]
    if len(matches) != 1:
        _fail(f"{phase}_unresolved", f"{phase} executor emitted {len(matches)} result records")
    try:
        value = json.loads(matches[0])
    except json.JSONDecodeError as exc:
        raise S10Error(str(exc), code=f"{phase}_unresolved") from exc
    if not isinstance(value, dict):
        _fail(f"{phase}_unresolved", f"{phase} executor result is not an object")
    return value


def _mapping_executor_code() -> str:
    """Pinned post-lock mapping executor.

    This source is passed via ``python -c`` only after an effective lock exists.
    Its process cwd is a declared ignored toolchain directory so rocISA's
    assembler-capability probes cannot create compiler defaults in repo root.
    """

    return r'''
import hashlib, json, math, sys, traceback
from Tensile import LibraryIO
from Tensile.BenchmarkStructs import BenchmarkProcess
from Tensile.Common.Architectures import gfxToIsa
from Tensile.Common.Capabilities import makeIsaInfoMap
from Tensile.Common.GlobalParameters import assignGlobalParameters
from Tensile.Common.Types import makeDebugConfig
from Tensile.KernelWriterAssembly import KernelWriterAssembly
from Tensile.Toolchain.Component import Assembler
from Tensile.SolutionLibrary import MasterSolutionLibrary
from Tensile.TensileCreateLibrary.Run import (
    processKernelSource,
    passPostKernelInfoToSolution,
    passPostKernelInfoToLibrary,
)
from Tensile.SolutionStructs.Naming import getKernelFileBase, getKernelNameMin
from Tensile.backends.ductile_backend import _generate_single_solution_with_groups
from rocisa import rocIsa

MARKER = "S10_POSTLOCK_RESULT="

def plain(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite value")
        return value
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if hasattr(value, "state"):
        return plain(value.state)
    return str(value)

def digest(value):
    return hashlib.sha256(
        json.dumps(plain(value), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

def reject(candidate, size, stage, reason_code, reason_text, internal_subreason):
    return {
        "config_hash": candidate["config_hash"],
        "size": size,
        "raw_indices": candidate["indices"],
        "raw_values": candidate["values"],
        "expanded_groups": {
            k: v for k, v in candidate["values"].items() if k.startswith("group_")
        },
        "resolved_solution": None,
        "codegen_identity": None,
        "size_mapping": None,
        "effective_gsu": None,
        "resolved_sentinels": {},
        "formocast_input": None,
        "field_provenance": {},
        "status": "rejected",
        "rejection": {
            "stage": stage,
            "reason_code": reason_code,
            "reason_text": str(reason_text),
            "internal_subreason": internal_subreason,
        },
        "prediction": None,
        "tie": False,
    }

def resolved_record(
    candidate, size, solution, library_solution, results, kernels, source_hashes, split_gsu
):
    state = solution._state
    sm = library_solution.sizeMapping
    required = [
        "waveNum", "macroTile", "matrixInstruction", "grvwA", "grvwB",
        "gwvwC", "gwvwD", "depthU", "globalSplitU", "workGroupMapping",
        "globalAccumulation", "workGroupMappingXCC", "workGroupMappingXCCGroup",
        "globalSplitUCoalesced", "globalSplitUWorkGroupMappingRoundRobin",
        "CUOccupancy", "PrefetchGlobalRead", "MathClocksUnrolledLoop",
        "DirectToVgprA", "DirectToVgprB", "NumLoadsCoalescedA",
        "NumLoadsCoalescedB", "VectorWidthA", "VectorWidthB", "LocalSplitU",
        "DirectToLdsA", "DirectToLdsB", "WaveGroup",
    ]
    missing = [key for key in required if not hasattr(sm, key)]
    if missing:
        raise KeyError("missing SizeMapping fields: " + ",".join(missing))
    mi = list(sm.matrixInstruction)
    wave_group = list(sm.WaveGroup)
    if len(mi) != 4 or len(wave_group) != 2 or len(sm.macroTile) != 3:
        raise ValueError("invalid fixed-width SizeMapping field")
    gsu = int(sm.globalSplitU)
    if gsu < 1:
        raise ValueError("unsupported unresolved/auto GlobalSplitU")
    mapping = {
        "waveNum": int(sm.waveNum),
        "macroTile": [int(value) for value in sm.macroTile],
        "matrixInstruction": [int(value) for value in mi],
        "grvwA": int(sm.grvwA),
        "grvwB": int(sm.grvwB),
        "gwvwC": int(sm.gwvwC),
        "gwvwD": int(sm.gwvwD),
        "depthU": int(sm.depthU),
        "globalSplitU": gsu,
        "workGroupMapping": int(sm.workGroupMapping),
        "globalAccumulation": int(sm.globalAccumulation),
        "workGroupMappingXCC": int(sm.workGroupMappingXCC),
        "workGroupMappingXCCGroup": int(sm.workGroupMappingXCCGroup),
        "globalSplitUCoalesced": bool(sm.globalSplitUCoalesced),
        "globalSplitUWorkGroupMappingRoundRobin": bool(
            sm.globalSplitUWorkGroupMappingRoundRobin
        ),
        "CUOccupancy": int(sm.CUOccupancy),
        "PrefetchGlobalRead": int(sm.PrefetchGlobalRead),
        "MathClocksUnrolledLoop": int(sm.MathClocksUnrolledLoop),
        "DirectToVgprA": bool(sm.DirectToVgprA),
        "DirectToVgprB": bool(sm.DirectToVgprB),
        "NumLoadsCoalescedA": int(sm.NumLoadsCoalescedA),
        "NumLoadsCoalescedB": int(sm.NumLoadsCoalescedB),
        "VectorWidthA": int(sm.VectorWidthA),
        "VectorWidthB": int(sm.VectorWidthB),
        "LocalSplitU": int(sm.LocalSplitU),
        "DirectToLdsA": bool(sm.DirectToLdsA),
        "DirectToLdsB": bool(sm.DirectToLdsB),
        "waveGroup": [int(value) for value in wave_group],
    }
    problem = {
        "M": int(size[0]), "N": int(size[1]), "NumBatches": int(size[2]), "K": int(size[3]),
        "bpeA": 2, "bpeB": 2, "bpeD": 2, "bpeCompute": 4,
        "transA": False, "transB": False,
        "swizzleTensorA": False, "swizzleTensorB": False,
        "dataType": "BFloat16",
    }
    resolved = plain(state)
    sentinels = {}
    for key, value in candidate["values"].items():
        if value in (-1, -2):
            sentinels[key] = {"raw": value, "resolved": plain(state.get(key))}
    return {
        "config_hash": candidate["config_hash"],
        "size": size,
        "raw_indices": candidate["indices"],
        "raw_values": candidate["values"],
        "expanded_groups": {
            k: v for k, v in candidate["values"].items() if k.startswith("group_")
        },
        "resolved_solution": resolved,
        "codegen_identity": {
            "kernel_names": [getKernelNameMin(k, split_gsu) for k in kernels],
            "source_sha256": source_hashes,
            "result_count": len(results),
            "isa": [9, 4, 2],
        },
        "size_mapping": mapping,
        "effective_gsu": gsu,
        "resolved_sentinels": sentinels,
        "formocast_input": {"problem": problem, "size_mapping": mapping, "hardware": "gfx942"},
        "field_provenance": {
            "size_mapping": "SolutionLibrary.MasterSolutionLibrary.BenchmarkingLibrary",
            "CUOccupancy": "TensileCreateLibrary.Run.passPostKernelInfoToLibrary",
            "PrefetchGlobalRead": "TensileCreateLibrary.Run.passPostKernelInfoToSolution",
            "MathClocksUnrolledLoop": "TensileCreateLibrary.Run.passPostKernelInfoToSolution",
            "effective_gsu": "ContractionSolution.calculateAutoGSU explicit-GSU branch",
            "formocast_input": "client/src/SolutionIterator.cpp field mapping",
        },
        "status": "accepted",
        "rejection": None,
        "prediction": None,
        "tie": False,
    }

request = json.load(open(sys.argv[1], "r", encoding="utf-8"))
config = LibraryIO.read(request["yaml_path"])
process = BenchmarkProcess(
    config["BenchmarkProblems"][0][0],
    config["BenchmarkProblems"][0][1],
    False,
)
step = process[0]
isa = gfxToIsa("gfx942")
isa_map = makeIsaInfoMap([isa], request["compiler"])
assignGlobalParameters(config["GlobalParameters"], isa_map)
debug = makeDebugConfig(config["GlobalParameters"])
assembler = Assembler(request["compiler"], "4", False)
rows = []
visited_kernel_bases = set()
for candidate in request["candidates"]:
    try:
        solution = _generate_single_solution_with_groups(
            candidate["values"], process.problemType, dict(step.constantParams),
            assembler, debug, isa_map, silent=True,
        )
    except BaseException:
        raise
    if solution is None:
        rows.extend(
            reject(
                candidate,
                size,
                "solution_resolution",
                "pinned_validation_boundary_none",
                "pinned solution validation API returned None",
                "internal_subreason_unknown",
            )
            for size in request["sizes"]
        )
        continue
    solution["SolutionIndex"] = int(candidate["slot"])
    kernels = solution.getKernels()
    unique_kernels = []
    for kernel in kernels:
        base = getKernelFileBase(debug.splitGSU, kernel)
        kernel.duplicate = base in visited_kernel_bases
        if not kernel.duplicate:
            kernel["BaseName"] = base
            unique_kernels.append(kernel)
        visited_kernel_bases.add(base)
    if not unique_kernels:
        rows.extend(
            reject(
                candidate,
                size,
                "post_codegen",
                "canonical_duplicate_kernel",
                "all candidate kernels duplicate an earlier canonical BaseName",
                "canonical_getKernelFileBase_visited_set",
            )
            for size in request["sizes"]
        )
        continue
    writer = KernelWriterAssembly(assembler, debug)
    ti = rocIsa.getInstance()
    options = ti.getOutputOptions()
    results = [
        processKernelSource(writer, ti.getData(), options, debug.splitGSU, kernel)
        for kernel in unique_kernels
    ]
    nonzero = [int(result.err) for result in results if int(result.err) != 0]
    if nonzero:
        rows.extend(
            reject(
                candidate,
                size,
                "post_codegen",
                "pinned_codegen_nonzero",
                "pinned processKernelSource returned nonzero error",
                ",".join(str(value) for value in nonzero),
            )
            for size in request["sizes"]
        )
        continue
    passPostKernelInfoToSolution(
        results, unique_kernels, [solution], debug.splitGSU
    )
    master = MasterSolutionLibrary.BenchmarkingLibrary(
        [solution], assembler, debug.splitGSU, False, False, isa_map
    )
    passPostKernelInfoToLibrary(
        results, unique_kernels, {"gfx942": master}, debug.splitGSU
    )
    library_solution = master.solutions[int(candidate["slot"])]
    source_hashes = [
        hashlib.sha256(
            result.src if isinstance(result.src, bytes) else result.src.encode()
        ).hexdigest()
        for result in results
    ]
    rows.extend(
        resolved_record(
            candidate, size, solution, library_solution, results, unique_kernels,
            source_hashes, debug.splitGSU
        )
        for size in request["sizes"]
    )
print(MARKER + json.dumps({"rows": rows}, sort_keys=True, separators=(",", ":")))
'''


def _mapping_native_helper_source() -> bytes:
    """Native parity helper built from the pinned integration after lock."""

    source = r'''
#include <Tensile/ContractionProblem.hpp>
#include <Tensile/ContractionSolution.hpp>
#include <origami/simulator/tensilelite/formocast_simulator.hpp>

#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <string>

int main(int argc, char** argv)
{
    if(argc != 3)
        throw std::runtime_error("usage: s10-formocast INPUT OUTPUT");
    std::ifstream input(argv[1]);
    std::ofstream output(argv[2], std::ios::trunc);
    if(!input || !output)
        throw std::runtime_error("cannot open helper input/output");

    size_t row = 0;
    while(true)
    {
        uint64_t M, N, batches, K;
        int waveNum, mt0, mt1, mt2, mi0, mi1, mi2, mi3;
        int grvwA, grvwB, gwvwC, gwvwD, depthU, suppliedGSU;
        int wgm, accumulation, xcc, xccGroup, gsuCoalesced, gsuWgmRR;
        int occupancy, pgr, mathClocks, dtvA, dtvB, nlca, nlcb;
        int vectorWidthA, vectorWidthB, lsu, dtlA, dtlB, waveGroup0, waveGroup1;
        if(!(input >> row >> M >> N >> batches >> K
             >> waveNum >> mt0 >> mt1 >> mt2 >> mi0 >> mi1 >> mi2 >> mi3
             >> grvwA >> grvwB >> gwvwC >> gwvwD >> depthU >> suppliedGSU
             >> wgm >> accumulation >> xcc >> xccGroup >> gsuCoalesced >> gsuWgmRR
             >> occupancy >> pgr >> mathClocks >> dtvA >> dtvB >> nlca >> nlcb
             >> vectorWidthA >> vectorWidthB >> lsu >> dtlA >> dtlB
             >> waveGroup0 >> waveGroup1))
        {
            if(input.eof())
                break;
            throw std::runtime_error("malformed helper input");
        }

        TensileLite::ContractionSolution solution;
        auto& source = solution.sizeMapping;
        source.waveNum = waveNum;
        source.macroTile = TensileLite::dim3(mt0, mt1, mt2);
        source.matrixInstruction = {mi0, mi1, mi2, mi3};
        source.grvwA = grvwA;
        source.grvwB = grvwB;
        source.gwvwC = gwvwC;
        source.gwvwD = gwvwD;
        source.depthU = depthU;
        source.globalSplitU = suppliedGSU;
        source.workGroupMapping = wgm;
        source.globalAccumulation = accumulation;
        source.workGroupMappingXCC = xcc;
        source.workGroupMappingXCCGroup = xccGroup;
        source.globalSplitUCoalesced = gsuCoalesced != 0;
        source.globalSplitUWorkGroupMappingRoundRobin = gsuWgmRR != 0;
        source.CUOccupancy = occupancy;
        source.PrefetchGlobalRead = pgr;
        source.MathClocksUnrolledLoop = mathClocks;
        source.DirectToVgprA = dtvA != 0;
        source.DirectToVgprB = dtvB != 0;
        source.NumLoadsCoalescedA = nlca;
        source.NumLoadsCoalescedB = nlcb;
        source.VectorWidthA = vectorWidthA;
        source.VectorWidthB = vectorWidthB;
        source.LocalSplitU = lsu;
        source.DirectToLdsA = dtlA != 0;
        source.DirectToLdsB = dtlB != 0;
        source.waveGroup = {waveGroup0, waveGroup1};

        auto exact = solution.getSizeMapping();
        TensileLite::ContractionProblemGemm problem;
        auto effectiveGSU = solution.calculateAutoGSU(problem, nullptr);
        if(effectiveGSU != static_cast<uint32_t>(suppliedGSU))
            throw std::runtime_error("effective GSU differs from explicit SizeMapping");

        origami::Formocast::ProblemInfo pi{};
        pi.M = M;
        pi.N = N;
        pi.NumBatches = batches;
        pi.K = K;
        pi.transA = false;
        pi.transB = false;
        pi.bpeA = 2;
        pi.bpeB = 2;
        pi.bpeD = 2;
        pi.bpeCompute = 4;
        pi.swizzleTensorA = false;
        pi.swizzleTensorB = false;
        pi.dataType = origami::data_type_t::BFloat16;

        // Field-for-field reproduction of SolutionIterator.cpp::getSizeMapping.
        origami::Formocast::SizeMapping sm{};
        sm.waveNum = exact.waveNum;
        sm.macroTile[0] = exact.macroTile.x;
        sm.macroTile[1] = exact.macroTile.y;
        sm.matrixInstruction = exact.matrixInstruction;
        sm.grvwA = exact.grvwA;
        sm.grvwB = exact.grvwB;
        sm.gwvwC = exact.gwvwC;
        sm.gwvwD = exact.gwvwD;
        sm.depthU = exact.depthU;
        sm.globalSplitU = effectiveGSU;
        sm.workGroupMapping = exact.workGroupMapping;
        sm.globalAccumulation = exact.globalAccumulation;
        sm.workGroupMappingXCC = exact.workGroupMappingXCC;
        sm.workGroupMappingXCCGroup = exact.workGroupMappingXCCGroup;
        sm.globalSplitUCoalesced = exact.globalSplitUCoalesced;
        sm.globalSplitUWorkGroupMappingRoundRobin
            = exact.globalSplitUWorkGroupMappingRoundRobin;
        sm.CUOccupancy = exact.CUOccupancy;
        sm.PrefetchGlobalRead = exact.PrefetchGlobalRead;
        sm.MathClocksUnrolledLoop = exact.MathClocksUnrolledLoop;
        sm.DirectToVgprA = exact.DirectToVgprA;
        sm.DirectToVgprB = exact.DirectToVgprB;
        sm.NumLoadsCoalescedA = exact.NumLoadsCoalescedA;
        sm.NumLoadsCoalescedB = exact.NumLoadsCoalescedB;
        sm.VectorWidthA = exact.VectorWidthA;
        sm.VectorWidthB = exact.VectorWidthB;
        sm.LocalSplitU = exact.LocalSplitU;
        sm.DirectToLdsA = exact.DirectToLdsA;
        sm.DirectToLdsB = exact.DirectToLdsB;
        sm.waveGroup = exact.waveGroup;

        origami::Formocast formocast;
        formocast.setProblem(pi);
        formocast.setSolution(sm);
        formocast.setHardware(origami::hardware_t::architecture_t::gfx942);
        auto prediction = formocast.predictedPerformance();
        if(!std::isfinite(prediction.microSeconds)
           || !std::isfinite(prediction.hitRate))
        {
            output << row << ' ' << effectiveGSU
                   << " rejected formocast_nonfinite_prediction\n";
            continue;
        }
        output << row << ' ' << effectiveGSU << " accepted "
               << std::setprecision(17) << prediction.microSeconds << ' '
               << prediction.hitRate << '\n';
    }
    if(!input.eof() || !output)
        throw std::runtime_error("helper stream failure");
}
'''
    return source.encode("utf-8")


def _mapping_native_cmake_source(
    integration_root: Path,
    helper_source: Path,
) -> bytes:
    return (
        "cmake_minimum_required(VERSION 3.25.2)\n"
        "project(s10_mapping_native LANGUAGES CXX C ASM)\n"
        "set(HIPBLASLT_ENABLE_FETCH OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_DEVICE OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_EXTOPS OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_MATRIX_TRANSFORM OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_CLIENT OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_HOST OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_BUNDLE_PYTHON_DEPS OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_ROCROLLER OFF CACHE BOOL \"\" FORCE)\n"
        "set(HIPBLASLT_ENABLE_MXDATAGENERATOR OFF CACHE BOOL \"\" FORCE)\n"
        "set(TENSILELITE_ENABLE_HOST ON CACHE BOOL \"\" FORCE)\n"
        "set(TENSILELITE_ENABLE_CLIENT ON CACHE BOOL \"\" FORCE)\n"
        "set(TENSILELITE_BUILD_TESTING OFF CACHE BOOL \"\" FORCE)\n"
        "set(BUILD_TESTING OFF CACHE BOOL \"\" FORCE)\n"
        "find_package(hip REQUIRED)\n"
        f"add_subdirectory(\"{_recorded_text(str(integration_root / 'projects/hipblaslt'))}\" hipblaslt)\n"
        f"add_executable(s10-formocast \"{_recorded_text(str(helper_source))}\")\n"
        "target_link_libraries(s10-formocast PRIVATE tensilelite::tensilelite-host hip::device)\n"
    ).encode("utf-8")


def _native_host_configure_argv(source: Path, build: Path) -> list[str]:
    return [
        str(CMAKE),
        "-S",
        _recorded_text(str(source)),
        "-B",
        _recorded_text(str(build)),
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_CXX_COMPILER={COMPILER}",
    ]


def _build_mapping_native_helper(
    *,
    mapping_root: Path,
    integration_root: Path,
) -> tuple[Path, dict[str, Any]]:
    """Build the direct C++ mapping helper only in post-lock scratch."""

    native_root = mapping_root / "native-helper"
    build = native_root / "build"
    logs = native_root / "logs"
    native_root.mkdir(parents=True)
    source_path = native_root / "s10-formocast.cpp"
    cmake_path = native_root / "CMakeLists.txt"
    helper = build / "s10-formocast"
    atomic_write_bytes(source_path, _mapping_native_helper_source())
    os.chmod(source_path, 0o644)
    atomic_write_bytes(
        cmake_path,
        _mapping_native_cmake_source(integration_root, source_path),
    )
    os.chmod(cmake_path, 0o644)
    env = _base_env()
    configure_proc, configure = _run_logged(
        _native_host_configure_argv(native_root, build),
        cwd=native_root,
        env=env,
        log_root=logs,
        name="mapping-native-configure",
        check=False,
    )
    if configure_proc.returncode:
        _fail("mapping_unresolved", "pinned native host configure failed")
    build_proc, build_command = _run_logged(
        [
            str(CMAKE),
            "--build",
            _recorded_text(str(build)),
            "--target",
            "s10-formocast",
            "tensilelite-client",
            "--parallel",
            "16",
        ],
        cwd=native_root,
        env=env,
        log_root=logs,
        name="mapping-native-build",
        check=False,
    )
    if build_proc.returncode:
        _fail("mapping_unresolved", "pinned native host build failed")
    client = build / "hipblaslt/tensilelite/client/tensilelite-client"
    if not helper.is_file() or not client.is_file():
        _fail("mapping_unresolved", "fresh pinned native helper/client absent")
    build_manifest_path = native_root / "build-manifest.json"
    atomic_write_json(build_manifest_path, _output_manifest(build))
    return helper, {
        "source": _bound_file(source_path),
        "cmake_source": _bound_file(cmake_path),
        "configure": configure,
        "build": build_command,
        "binary": _bound_file(helper),
        "pinned_client": _bound_file(client),
        "build_manifest": _bound_file(build_manifest_path),
    }


def _mapping_helper_line(index: int, row: Mapping[str, Any]) -> str:
    problem = row["formocast_input"]["problem"]
    mapping = row["size_mapping"]
    values = [
        index,
        problem["M"],
        problem["N"],
        problem["NumBatches"],
        problem["K"],
        mapping["waveNum"],
        *mapping["macroTile"],
        *mapping["matrixInstruction"],
        mapping["grvwA"],
        mapping["grvwB"],
        mapping["gwvwC"],
        mapping["gwvwD"],
        mapping["depthU"],
        mapping["globalSplitU"],
        mapping["workGroupMapping"],
        mapping["globalAccumulation"],
        mapping["workGroupMappingXCC"],
        mapping["workGroupMappingXCCGroup"],
        int(mapping["globalSplitUCoalesced"]),
        int(mapping["globalSplitUWorkGroupMappingRoundRobin"]),
        mapping["CUOccupancy"],
        mapping["PrefetchGlobalRead"],
        mapping["MathClocksUnrolledLoop"],
        int(mapping["DirectToVgprA"]),
        int(mapping["DirectToVgprB"]),
        mapping["NumLoadsCoalescedA"],
        mapping["NumLoadsCoalescedB"],
        mapping["VectorWidthA"],
        mapping["VectorWidthB"],
        mapping["LocalSplitU"],
        int(mapping["DirectToLdsA"]),
        int(mapping["DirectToLdsB"]),
        *mapping["waveGroup"],
    ]
    if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        _fail("mapping_unresolved", "native helper input is not integral")
    return " ".join(str(value) for value in values)


def _enrich_mapping_rows(
    rows: list[dict[str, Any]],
    *,
    helper: Path,
    pass_root: Path,
) -> dict[str, Any]:
    native_root = pass_root / "native"
    logs = native_root / "logs"
    native_root.mkdir(parents=True)
    input_path = native_root / "input.txt"
    output_path = native_root / "output.txt"
    accepted = [
        (index, row) for index, row in enumerate(rows) if row.get("status") == "accepted"
    ]
    input_bytes = "".join(
        _mapping_helper_line(index, row) + "\n" for index, row in accepted
    ).encode("ascii")
    atomic_write_bytes(input_path, input_bytes)
    os.chmod(input_path, 0o644)
    proc, command = _run_logged(
        [_recorded_text(str(helper)), _recorded_text(str(input_path)), _recorded_text(str(output_path))],
        cwd=native_root,
        env=_base_env(),
        log_root=logs,
        name="mapping-native-formocast",
        check=False,
    )
    if proc.returncode or not output_path.is_file():
        _fail("mapping_unresolved", "mapping native Formocast helper failed")
    predictions: dict[int, tuple[int, str, float | None, float | None]] = {}
    for line in output_path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) not in (4, 5):
            _fail("mapping_unresolved", "malformed native Formocast output")
        index, gsu = int(fields[0]), int(fields[1])
        status = fields[2]
        if index in predictions or status not in {"accepted", "rejected"}:
            _fail("mapping_unresolved", "invalid native Formocast output")
        if status == "accepted":
            if len(fields) != 5:
                _fail("mapping_unresolved", "accepted Formocast output lacks values")
            prediction, hit_rate = float(fields[3]), float(fields[4])
            if not math.isfinite(prediction) or not math.isfinite(hit_rate):
                _fail("postlock_harness_defect", "accepted Formocast output is nonfinite")
            predictions[index] = (gsu, status, prediction, hit_rate)
        else:
            if len(fields) != 4 or fields[3] != "formocast_nonfinite_prediction":
                _fail("postlock_harness_defect", "unregistered Formocast rejection")
            predictions[index] = (gsu, status, None, None)
    if set(predictions) != {index for index, _ in accepted}:
        _fail("mapping_unresolved", "native Formocast output coverage mismatch")
    for index, row in accepted:
        effective_gsu, status, prediction, hit_rate = predictions[index]
        if effective_gsu != row["size_mapping"]["globalSplitU"]:
            _fail("mapping_unresolved", "native effective GSU differs from SizeMapping")
        row["effective_gsu"] = effective_gsu
        row["field_provenance"]["effective_gsu"] = (
            "direct pinned ContractionSolution.calculateAutoGSU"
        )
        row["field_provenance"]["formocast_input"] = (
            "direct pinned ContractionSolution.getSizeMapping and "
            "SolutionIterator.cpp field mapping"
        )
        if status == "accepted":
            row["prediction"] = prediction
        else:
            row["status"] = "rejected"
            row["prediction"] = None
            row["tie"] = False
            row["rejection"] = {
                "stage": "formocast",
                "reason_code": "formocast_nonfinite_prediction",
                "reason_text": "pinned Formocast returned a nonfinite prediction",
                "internal_subreason": "pinned_formocast_structured_rejection",
            }
    prediction_counts: dict[tuple[tuple[int, ...], float], int] = {}
    for _, row in accepted:
        if row["status"] != "accepted":
            continue
        key = (tuple(row["size"]), float(row["prediction"]))
        prediction_counts[key] = prediction_counts.get(key, 0) + 1
    for _, row in accepted:
        if row["status"] != "accepted":
            continue
        row["tie"] = (
            prediction_counts[(tuple(row["size"]), float(row["prediction"]))] > 1
        )
    return {
        "input": _bound_file(input_path),
        "output": _bound_file(output_path),
        "command": command,
        "accepted_count": len(accepted),
        "formocast_accepted_count": sum(
            1 for _, row in accepted if row["status"] == "accepted"
        ),
        "formocast_rejected_count": sum(
            1
            for _, row in accepted
            if row["status"] == "rejected"
            and row["rejection"]["stage"] == "formocast"
        ),
        "native_manifest": _output_manifest(native_root),
    }


def _mapping_request(
    lock: Mapping[str, Any],
    *,
    path: Path,
) -> dict[str, Any]:
    request = {
        "schema_version": "1.0.0",
        "yaml_path": _recorded_text(str(INPUT_PATH)),
        "compiler": str(COMPILER),
        "candidates": lock["mapping_candidates"],
        "sizes": strict_load_json(SIZE_REGISTRY_PATH)["selected_sizes"],
    }
    atomic_write_json(path, request)
    return request


def _mapping_pass(
    lock: Mapping[str, Any],
    *,
    pass_root: Path,
    pass_name: str,
    native_helper: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if pass_root.exists():
        _fail("already_exists", f"mapping pass root exists: {_rel(pass_root)}")
    toolchain_root = pass_root / "toolchain"
    logs = pass_root / "logs"
    toolchain_root.mkdir(parents=True)
    request_path = pass_root / "request.json"
    _mapping_request(lock, path=request_path)
    provenance = strict_load_json(PROVENANCE_PATH)
    run = provenance["runs"][0]
    integration = strict_load_json(ROOT / run["integration"]["path"])
    native = strict_load_json(ROOT / run["native"]["path"])
    integration_root = ROOT / integration["root"]
    native_binary = ROOT / native["binary"]["path"]
    python_path = _python_path(integration_root, native_binary.parent)
    env = _base_env()
    env["PYTHONPATH"] = os.pathsep.join(_recorded_text(str(path)) for path in python_path)
    proc, command = _run_logged(
        [str(PYTHON), "-S", "-c", _mapping_executor_code(), _recorded_text(str(request_path))],
        cwd=toolchain_root,
        env=env,
        log_root=logs,
        name=pass_name,
        check=False,
    )
    toolchain_manifest = _output_manifest(toolchain_root)
    if proc.returncode:
        _fail(
            "postlock_harness_defect",
            f"{pass_name} executor exited unexpectedly with {proc.returncode}",
        )
    try:
        result = _parse_marked_json(proc.stdout, phase="mapping")
    except EvidenceValidationError as exc:
        raise S10Error(str(exc), code="postlock_harness_defect") from exc
    rows = result.get("rows")
    if not isinstance(rows, list) or len(rows) != 30:
        _fail("postlock_harness_defect", f"{pass_name} did not return 30 rows")
    rejection_log = command["stderr"]["raw_sha256"]
    for row in rows:
        if row.get("status") == "rejected" and isinstance(row.get("rejection"), dict):
            row["rejection"]["log_sha256"] = rejection_log
    native = _enrich_mapping_rows(rows, helper=native_helper, pass_root=pass_root)
    return plain_value(rows), {
        "pass": pass_name,
        "request": _bound_file(request_path),
        "command": command,
        "toolchain_cwd": _rel(toolchain_root),
        "toolchain_manifest": toolchain_manifest,
        "toolchain_manifest_sha256": canonical_sha256(toolchain_manifest),
        "source_root": _rel(integration_root),
        "native_binary": _bound_file(native_binary),
        "native_formocast": native,
    }


def _execute_mapping_raw() -> Mapping[str, Any]:
    lock, lock_hash = _load_lock()
    scratch_root = _active_scratch_root()
    mapping_root = scratch_root / "postlock/mapping"
    if mapping_root.exists():
        _fail("already_exists", f"mapping raw root exists: {_rel(mapping_root)}")
    mapping_root.mkdir(parents=True)
    provenance = strict_load_json(PROVENANCE_PATH)
    integration = strict_load_json(
        ROOT / provenance["runs"][0]["integration"]["path"]
    )
    integration_root = ROOT / integration["root"]
    native_helper, native_build = _build_mapping_native_helper(
        mapping_root=mapping_root,
        integration_root=integration_root,
    )
    rows, first = _mapping_pass(
        lock,
        pass_root=mapping_root / "pass-a",
        pass_name="mapping-pass-a",
        native_helper=native_helper,
    )
    rerun_rows, second = _mapping_pass(
        lock,
        pass_root=mapping_root / "pass-b",
        pass_name="mapping-pass-b",
        native_helper=native_helper,
    )
    raw = {
        "lock_raw_sha256": lock_hash,
        "rows": rows,
        "rerun_rows": rerun_rows,
        "executor": {
            "kind": "pinned_ductile_post_codegen_mapping_v1",
            "native_build": native_build,
            "passes": [first, second],
            "compiler_default_outputs_confined": True,
            "prelock_actual_candidate_results_reused": False,
        },
    }
    raw_path = mapping_root / "mapping-raw.json"
    atomic_write_json(raw_path, raw)
    return raw


def _load_postlock_raw(name: str) -> Mapping[str, Any]:
    """Load exact ignored executor output for a post-lock phase.

    GPU/native executors write append-free raw observations under the ignored
    S10 run root.  This tracked runner owns canonical validation and promotion;
    it never guesses a missing post-codegen/runtime field.
    """

    path = _active_scratch_root() / "postlock" / name / f"{name}-raw.json"
    if not path.is_file():
        _fail(f"{name}_unresolved", f"required raw executor record absent: {_rel(path)}")
    document = strict_load_json(path)
    if not isinstance(document, dict):
        _fail(f"{name}_unresolved", "raw executor record is not an object")
    return document


def _mapping_from_raw(raw: Mapping[str, Any]) -> dict[str, Any]:
    lock, lock_hash = _load_lock()
    required = {"lock_raw_sha256", "rows", "rerun_rows", "executor"}
    if set(raw) != required or raw["lock_raw_sha256"] != lock_hash:
        _fail("lock_binding_mismatch", "mapping raw lock/fields mismatch")
    rows = raw["rows"]
    rerun = raw["rerun_rows"]
    if not isinstance(rows, list) or len(rows) != 30 or rerun != rows:
        _fail("mapping_unresolved", "mapping requires 30 deterministic rows")
    expected_pairs = {
        (candidate["config_hash"], tuple(size))
        for candidate in lock["mapping_candidates"]
        for size in strict_load_json(SIZE_REGISTRY_PATH)["selected_sizes"]
    }
    seen = set()
    required_row = {
        "config_hash",
        "size",
        "raw_indices",
        "raw_values",
        "expanded_groups",
        "resolved_solution",
        "codegen_identity",
        "size_mapping",
        "effective_gsu",
        "resolved_sentinels",
        "formocast_input",
        "field_provenance",
        "status",
        "rejection",
        "prediction",
        "tie",
    }
    for row in rows:
        if not isinstance(row, dict) or set(row) != required_row:
            _fail("mapping_unresolved", "mapping row field set mismatch")
        pair = (row["config_hash"], tuple(row["size"]))
        if pair not in expected_pairs or pair in seen:
            _fail("mapping_unresolved", f"unexpected/duplicate mapping pair {pair}")
        seen.add(pair)
        if row["status"] == "accepted":
            if row["rejection"] is not None:
                _fail("mapping_unresolved", "accepted row has rejection")
            if not isinstance(row["field_provenance"], dict):
                _fail("mapping_unresolved", "accepted row lacks field provenance")
            for field in (
                "CUOccupancy",
                "PrefetchGlobalRead",
                "MathClocksUnrolledLoop",
                "effective_gsu",
            ):
                if field not in row["field_provenance"]:
                    _fail("mapping_unresolved", f"missing provenance for {field}")
            prediction = row["prediction"]
            if isinstance(prediction, bool) or not isinstance(prediction, (int, float)) or not math.isfinite(prediction):
                _fail("mapping_unresolved", "accepted prediction is nonfinite")
        elif row["status"] == "rejected":
            rejection = row["rejection"]
            if (
                not isinstance(rejection, dict)
                or set(rejection)
                != {
                    "stage",
                    "reason_code",
                    "reason_text",
                    "internal_subreason",
                    "log_sha256",
                }
                or not HASH_RE.fullmatch(str(rejection["log_sha256"]))
            ):
                _fail("mapping_unresolved", "rejection provenance is incomplete")
            typed = (
                (
                    rejection["stage"] == "solution_resolution"
                    and rejection["reason_code"]
                    == "pinned_validation_boundary_none"
                    and rejection["internal_subreason"]
                    == "internal_subreason_unknown"
                )
                or (
                    rejection["stage"] == "post_codegen"
                    and rejection["reason_code"]
                    in {"canonical_duplicate_kernel", "pinned_codegen_nonzero"}
                )
                or (
                    rejection["stage"] == "formocast"
                    and rejection["reason_code"]
                    == "formocast_nonfinite_prediction"
                    and rejection["internal_subreason"]
                    == "pinned_formocast_structured_rejection"
                )
            )
            if not typed:
                _fail(
                    "postlock_harness_defect",
                    "mapping row contains an unregistered rejection taxonomy",
                )
        else:
            _fail("mapping_unresolved", f"invalid mapping status {row['status']}")
    if seen != expected_pairs:
        _fail("mapping_unresolved", "mapping pair coverage mismatch")
    anchor_failures = sorted(
        {
            row["config_hash"]
            for row in rows
            if row["config_hash"] in lock["anchor_hashes"]
            and row["status"] == "rejected"
        }
    )
    formocast_rejections = [
        row
        for row in rows
        if row["status"] == "rejected"
        and row["rejection"]["stage"] == "formocast"
        and row["rejection"]["reason_code"] == "formocast_nonfinite_prediction"
    ]
    entry_failure_ids: list[str] = []
    if anchor_failures:
        entry_failure_ids.append("mapping_anchor_prerequisite_rejected")
    if not formocast_rejections:
        entry_failure_ids.append("required_formocast_rejection_unobserved")
    entry_pass = not entry_failure_ids
    return {
        "schema_version": "1.0.0",
        "kind": "s10_mapping_corpus",
        "checkpoint_id": "S10",
        "status": "complete",
        "created_at": _utc_now(),
        "effective_lock_raw_sha256": lock_hash,
        "candidate_count": 10,
        "size_count": 3,
        "row_count": 30,
        "anchor_hashes": lock["anchor_hashes"],
        "rows": rows,
        "deterministic_rerun_parity": True,
        "mapping_evidence_integrity": {
            "status": "PASS",
            "execution": "complete",
            "reason_code": "fresh_exact_30_row_ab_parity",
            "reason_text": (
                "fresh mapping passes A and B produced the same 30 typed rows "
                "without an unexpected exception"
            ),
            "failure_id": None,
        },
        "mapping_entry": {
            "status": "PASS" if entry_pass else "FAIL",
            "execution": "complete",
            "reason_code": (
                "all_locked_entry_prerequisites_satisfied"
                if entry_pass
                else "locked_mapping_entry_prerequisite_failed"
            ),
            "reason_text": (
                "all locked anchors and frozen O7 coverage are present"
                if entry_pass
                else "; ".join(entry_failure_ids)
            ),
            "failure_id": None if entry_pass else "S10-MAPPING-ENTRY-FAIL",
            "anchor_failure_hashes": anchor_failures,
            "formocast_rejection_count": len(formocast_rejections),
        },
        "executor": raw["executor"],
    }


def mapping() -> dict[str, Any]:
    _require_not_terminal("mapping")
    _require_no_existing(MAPPING_PATH)
    document = _mapping_from_raw(_execute_mapping_raw())
    _validate(document, context="S10 mapping corpus")
    atomic_write_json(MAPPING_PATH, document)
    return {"status": "MAPPING_COMPLETE", "rows": 30, "raw_sha256": sha256_file(MAPPING_PATH)}


def _descendant_pids(root_pid: int) -> set[int]:
    """Best-effort live Linux process-tree closure for collision attribution."""

    found = {root_pid}
    pending = [root_pid]
    while pending:
        parent = pending.pop()
        children_path = Path(f"/proc/{parent}/task/{parent}/children")
        try:
            fields = children_path.read_text(encoding="ascii").split()
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        for field in fields:
            if not field.isdigit():
                _fail("device_mismatch", "malformed executor process lineage")
            child = int(field)
            if child not in found:
                found.add(child)
                pending.append(child)
    return found


def _monitor_sample(
    *,
    lock: Mapping[str, Any],
    phase: str,
    sample_index: int,
    cwd: Path,
    log_root: Path,
    name_prefix: str,
    allowed_pids: set[int],
    seconds_since_previous: float | None,
) -> tuple[dict[str, Any], bool]:
    device_proc, device_command = _run_logged(
        LIVE_DEVICE_ARGV,
        cwd=cwd,
        env=_base_env(),
        log_root=log_root,
        name=f"{name_prefix}-{phase}-{sample_index}-devices",
        check=False,
    )
    process_proc, process_command = _run_logged(
        LIVE_PROCESS_ARGV,
        cwd=cwd,
        env=_base_env(),
        log_root=log_root,
        name=f"{name_prefix}-{phase}-{sample_index}-processes",
        check=False,
    )
    reasons = []
    if device_proc.returncode or process_proc.returncode:
        reasons.append("monitor_command_failure")
        devices = []
    else:
        pid_map = _parse_pid_gpu_map(process_proc.stdout)
        devices = _parse_live_devices(device_proc.stdout, pid_map)
        index = lock["device"]["container_visible_index"]
        matches = [
            row
            for row in devices
            if row["identity"]["container_visible_index"] == index
        ]
        if len(matches) != 1:
            reasons.append("locked_device_absent_or_duplicated")
        else:
            selected = matches[0]
            if not _typed_equal(selected["identity"], lock["device"]):
                reasons.append("locked_device_identity_drift")
            if phase in {"before", "after"}:
                if not selected["eligible"]:
                    reasons.extend(
                        f"{phase}:{reason}"
                        for reason in selected["ineligibility_reasons"]
                    )
            else:
                foreign = sorted(
                    set(selected["mapped_kfd_pids"]).difference(allowed_pids)
                )
                if foreign:
                    reasons.append(
                        "during:foreign_mapped_kfd_pids="
                        + ",".join(str(pid) for pid in foreign)
                    )
    sample = {
        "phase": phase,
        "sample_index": sample_index,
        "captured_at": device_command["started_at"],
        "seconds_since_previous": seconds_since_previous,
        "allowed_executor_lineage_pids": sorted(allowed_pids),
        "device_command": device_command,
        "process_command": process_command,
        "devices": devices,
        "contamination_reasons": reasons,
        "clean": not reasons,
    }
    return sample, bool(reasons)


def _run_monitored(
    argv: Sequence[str],
    *,
    lock: Mapping[str, Any],
    cwd: Path,
    env: Mapping[str, str],
    attempt_root: Path,
    name: str,
) -> dict[str, Any]:
    """Run one whole GPU executor attempt with before/during/after sampling."""

    logs = attempt_root / "logs"
    logs.mkdir(parents=True)
    stdout_path = logs / f"{name}.stdout"
    stderr_path = logs / f"{name}.stderr"
    samples = []
    before, contaminated = _monitor_sample(
        lock=lock,
        phase="before",
        sample_index=0,
        cwd=attempt_root,
        log_root=logs,
        name_prefix=name,
        allowed_pids=set(),
        seconds_since_previous=None,
    )
    samples.append(before)
    if contaminated:
        return {
            "status": "contaminated",
            "command": None,
            "samples": samples,
            "maximum_during_sample_period_seconds": 1,
        }

    started = _utc_now()
    proc = subprocess.Popen(
        list(argv),
        cwd=cwd,
        env=dict(env),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    lineage = {proc.pid}
    during_index = 0
    previous_start: float | None = None
    while True:
        sample_start = time.monotonic()
        lineage.update(_descendant_pids(proc.pid))
        gap = None if previous_start is None else sample_start - previous_start
        during, dirty = _monitor_sample(
            lock=lock,
            phase="during",
            sample_index=during_index,
            cwd=attempt_root,
            log_root=logs,
            name_prefix=name,
            allowed_pids=lineage,
            seconds_since_previous=gap,
        )
        if gap is not None and gap > 1:
            during["contamination_reasons"].append(
                f"during:sample_gap={gap:.9f}"
            )
            during["clean"] = False
            dirty = True
        samples.append(during)
        contaminated = contaminated or dirty
        during_index += 1
        previous_start = sample_start
        if proc.poll() is not None:
            break
        remaining = 1.0 - (time.monotonic() - sample_start)
        if remaining > 0:
            time.sleep(remaining)
    stdout, stderr = proc.communicate()
    ended = _utc_now()
    atomic_write_bytes(stdout_path, stdout)
    atomic_write_bytes(stderr_path, stderr)
    post_start = time.monotonic()
    after, dirty = _monitor_sample(
        lock=lock,
        phase="after",
        sample_index=0,
        cwd=attempt_root,
        log_root=logs,
        name_prefix=name,
        allowed_pids=set(),
        seconds_since_previous=(
            None if previous_start is None else post_start - previous_start
        ),
    )
    samples.append(after)
    contaminated = contaminated or dirty
    command = {
        "argv": list(argv),
        "cwd": _rel(cwd),
        "environment": _safe_env_record(env),
        "started_at": started,
        "ended_at": ended,
        "exit_code": proc.returncode,
        "stdout": {
            "path": _rel(stdout_path),
            "raw_sha256": sha256_file(stdout_path),
            "bytes": stdout_path.stat().st_size,
        },
        "stderr": {
            "path": _rel(stderr_path),
            "raw_sha256": sha256_file(stderr_path),
            "bytes": stderr_path.stat().st_size,
        },
    }
    return {
        "status": "contaminated" if contaminated else "clean",
        "command": command,
        "samples": samples,
        "executor_pid": proc.pid,
        "observed_executor_lineage_pids": sorted(lineage),
        "maximum_during_sample_period_seconds": 1,
    }


def _postlock_native_client() -> Path:
    raw = strict_load_json(_active_scratch_root() / "postlock/mapping/mapping-raw.json")
    try:
        reference = raw["executor"]["native_build"]["pinned_client"]
    except (KeyError, TypeError) as exc:
        raise S10Error("mapping native client binding absent", code="smoke_incomplete") from exc
    if (
        not isinstance(reference, dict)
        or set(reference) != {"path", "raw_sha256"}
        or HASH_RE.fullmatch(str(reference["raw_sha256"])) is None
    ):
        _fail("smoke_incomplete", "mapping native client reference malformed")
    path = _evidence_regular_path(reference["path"], role="mapping-native-client")
    if sha256_file(path) != reference["raw_sha256"]:
        _fail("smoke_incomplete", "mapping native client hash differs")
    return path


def _singleton_benchmark_yaml(
    *,
    lock: Mapping[str, Any],
    candidate_hash: str,
    sizes: Sequence[Sequence[int]],
    multiplier: int,
    path: Path,
) -> dict[str, Any]:
    candidates = [
        candidate
        for candidate in lock["mapping_candidates"]
        if candidate["config_hash"] == candidate_hash
    ]
    if len(candidates) != 1:
        _fail("mapping_unresolved", f"locked candidate absent: {candidate_hash}")
    candidate = candidates[0]
    config = copy.deepcopy(strict_load_yaml(INPUT_PATH))
    config.pop("Backend", None)
    group = config["BenchmarkProblems"][0][1]
    flattened = {}
    for axis, value in candidate["values"].items():
        if not axis.startswith("group_"):
            flattened[axis] = plain_value(value)
    grouped = sorted(
        (
            (int(axis.split("_", 1)[1]), value)
            for axis, value in candidate["values"].items()
            if axis.startswith("group_")
        ),
        key=lambda item: item[0],
    )
    for _, value in grouped:
        if not isinstance(value, dict):
            _fail("mapping_unresolved", "locked group value is not an object")
        for name, resolved in value.items():
            flattened[name] = plain_value(resolved)
    fork = [{name: [value]} for name, value in flattened.items()]
    group["ForkParameters"] = fork
    finals = group["BenchmarkFinalParameters"]
    problem_sizes = [{"Exact": [int(value) for value in size]} for size in sizes]
    finals[0] = {"ProblemSizes": problem_sizes}
    globals_ = config["GlobalParameters"]
    base_enqueues = globals_.get("EnqueuesPerSync")
    if (
        isinstance(base_enqueues, bool)
        or not isinstance(base_enqueues, int)
        or base_enqueues < 1
    ):
        _fail("noise_incomplete", "baseline EnqueuesPerSync is invalid")
    globals_["EnqueuesPerSync"] = base_enqueues * multiplier
    globals_["NumElementsToValidate"] = 128
    globals_["ExitOnFails"] = 2
    globals_["Device"] = lock["device"]["container_visible_index"]
    globals_["KeepBuildTmp"] = True
    atomic_write_bytes(
        path,
        yaml.safe_dump(
            plain_value(config),
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            width=4096,
        ).encode("utf-8"),
    )
    os.chmod(path, 0o644)
    return {
        "candidate_hash": candidate_hash,
        "multiplier": multiplier,
        "timed_iterations": base_enqueues * multiplier,
        "path": _bound_file(path),
    }


def _tensile_benchmark_argv(
    *,
    integration_root: Path,
    config: Path,
    output: Path,
    device_index: int,
    client: Path,
) -> list[str]:
    return [
        str(PYTHON),
        "-S",
        _recorded_text(
            str(integration_root / "projects/hipblaslt/tensilelite/Tensile/bin/Tensile")
        ),
        _recorded_text(str(config)),
        _recorded_text(str(output)),
        "--device",
        str(device_index),
        "--gpu-targets",
        "gfx942",
        "--cxx-compiler",
        str(COMPILER),
        "--c-compiler",
        str(COMPILER),
        "--assembler",
        str(COMPILER),
        "--offload-bundler",
        str(OFFLOAD_BUNDLER),
        "--prebuilt-client",
        _recorded_text(str(client)),
    ]


def _benchmark_csv_rows(output: Path) -> tuple[Path, list[dict[str, str]]]:
    candidates = sorted(output.glob("**/Data/*.csv"))
    if len(candidates) != 1:
        _fail("smoke_incomplete", f"expected one benchmark CSV, found {len(candidates)}")
    path = candidates[0]
    with path.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        _fail("smoke_incomplete", "benchmark CSV is empty")
    return path, rows


def _parsed_benchmark_rows(
    output: Path,
    sizes: Sequence[Sequence[int]],
    *,
    error_code: str,
) -> tuple[Path, list[dict[str, Any]]]:
    path, rows = _benchmark_csv_rows(output)
    parsed = []
    expected = {tuple(size) for size in sizes}
    for row in rows:
        try:
            size = tuple(int(row[f"Size{letter}"]) for letter in "IJKL")
            timing = float(row["WinnerTimeUS"])
            quality = float(row["WinnerGFlops"])
        except (KeyError, TypeError, ValueError) as exc:
            raise S10Error("malformed benchmark CSV", code=error_code) from exc
        if (
            size not in expected
            or not math.isfinite(timing)
            or not math.isfinite(quality)
            or timing <= 0
            or quality <= 0
        ):
            _fail(error_code, "benchmark CSV contains invalid size/timing/quality")
        parsed.append({"size": list(size), "timing": timing, "quality": quality})
    if {tuple(row["size"]) for row in parsed} != expected or len(parsed) != len(expected):
        _fail(error_code, "benchmark CSV size coverage differs")
    return path, parsed


def _execute_smoke_raw() -> Mapping[str, Any]:
    lock, lock_hash = _load_lock()
    if not MAPPING_PATH.is_file():
        _fail("mapping_unresolved", "mapping corpus must precede smoke")
    mapping_doc = strict_load_json(MAPPING_PATH)
    candidate_hash = sorted(lock["anchor_hashes"])[0]
    candidate_rows = [
        row
        for row in mapping_doc["rows"]
        if row["config_hash"] == candidate_hash
    ]
    if len(candidate_rows) != 3 or any(
        row["status"] != "accepted" for row in candidate_rows
    ):
        _fail("smoke_incomplete", "locked smoke anchor is not valid for all sizes")
    scratch_root = _active_scratch_root()
    smoke_root = scratch_root / "postlock/smoke"
    if smoke_root.exists():
        _fail("already_exists", f"smoke raw root exists: {_rel(smoke_root)}")
    smoke_root.mkdir(parents=True)
    provenance = strict_load_json(PROVENANCE_PATH)
    run = provenance["runs"][0]
    integration = strict_load_json(ROOT / run["integration"]["path"])
    native = strict_load_json(ROOT / run["native"]["path"])
    integration_root = ROOT / integration["root"]
    native_binary = ROOT / native["binary"]["path"]
    client = _postlock_native_client()
    sizes = strict_load_json(SIZE_REGISTRY_PATH)["selected_sizes"]
    env = _base_env()
    env["PYTHONPATH"] = os.pathsep.join(
        _recorded_text(str(path))
        for path in (
            native_binary.parent,
            integration_root / "projects/hipblaslt/tensilelite",
        )
    )
    attempts = []
    selected = None
    for attempt_index in range(1, 4):
        attempt_root = smoke_root / f"attempt-{attempt_index}"
        attempt_root.mkdir()
        config = attempt_root / "singleton.yaml"
        output = attempt_root / "output"
        config_record = _singleton_benchmark_yaml(
            lock=lock,
            candidate_hash=candidate_hash,
            sizes=sizes,
            multiplier=1,
            path=config,
        )
        execution = _run_monitored(
            _tensile_benchmark_argv(
                integration_root=integration_root,
                config=config,
                output=output,
                device_index=lock["device"]["container_visible_index"],
                client=client,
            ),
            lock=lock,
            cwd=attempt_root,
            env=env,
            attempt_root=attempt_root,
            name="smoke-pipeline",
        )
        attempt = {
            "attempt": attempt_index,
            "config": config_record,
            "execution": execution,
            "phase_manifest": _output_manifest(attempt_root),
        }
        attempts.append(attempt)
        if execution["status"] == "contaminated":
            continue
        command = execution["command"]
        if command is None or command["exit_code"] != 0:
            _fail("correctness_failure", "smoke pipeline failed")
        result_path, parsed = _parsed_benchmark_rows(
            output, sizes, error_code="smoke_incomplete"
        )
        runs = []
        by_size = {tuple(row["size"]): row for row in parsed}
        for size in sizes:
            row = by_size[tuple(size)]
            runs.append(
                {
                    "size": size,
                    "generate": command,
                    "compile": command,
                    "benchmark": command,
                    "binary_sha256": sha256_file(client),
                    "result_sha256": sha256_file(result_path),
                    "validation_count": 128,
                    "correctness": "pass",
                    "timing": row["timing"],
                    "quality": row["quality"],
                }
            )
        selected = {
            "attempt": attempt_index,
            "result": _bound_file(result_path),
            "runs": runs,
            "monitoring": execution,
        }
        break
    if selected is None:
        _fail("device_mismatch", "all three complete smoke attempts were contaminated")
    h4 = strict_load_json(ENVIRONMENT_PATH)["h4"]["record"]
    environment = {
        "container": "perlee",
        "arch": "gfx942",
        "availability_mode": "live_unreserved",
        "device": lock["device"],
        "rocm": h4["tool_version"],
        "driver": "bound by fresh ROCm-SMI device/process command records",
        "clock_power_policy": "observed; no clock or power mutation",
        "commands": [
            selected["monitoring"]["samples"][0]["device_command"],
            selected["monitoring"]["samples"][0]["process_command"],
        ],
        "monitoring": {
            "maximum_complete_attempts": 3,
            "contaminated_attempts": sum(
                attempt["execution"]["status"] == "contaminated"
                for attempt in attempts
            ),
            "selected_attempt": selected["attempt"],
            "attempts": attempts,
        },
    }
    raw = {
        "lock_raw_sha256": lock_hash,
        "environment_revalidation": environment,
        "candidate_hash": candidate_hash,
        "runs": selected["runs"],
    }
    atomic_write_json(smoke_root / "smoke-raw.json", raw)
    return raw


def _smoke_from_raw(raw: Mapping[str, Any]) -> dict[str, Any]:
    lock, lock_hash = _load_lock()
    required = {"lock_raw_sha256", "environment_revalidation", "candidate_hash", "runs"}
    if set(raw) != required or raw["lock_raw_sha256"] != lock_hash:
        _fail("lock_binding_mismatch", "smoke raw lock/fields mismatch")
    if raw["candidate_hash"] != sorted(lock["anchor_hashes"])[0]:
        _fail("smoke_incomplete", "smoke candidate is not smallest-hash anchor")
    environment = raw["environment_revalidation"]
    required_env = {
        "container",
        "arch",
        "availability_mode",
        "device",
        "rocm",
        "driver",
        "clock_power_policy",
        "commands",
        "monitoring",
    }
    if not isinstance(environment, dict) or set(environment) != required_env:
        _fail("device_mismatch", "environment revalidation is incomplete")
    if (
        environment["container"] != "perlee"
        or environment["arch"] != "gfx942"
        or environment["availability_mode"] != "live_unreserved"
        or environment["device"] != lock["device"]
    ):
        _fail("device_mismatch", "live environment/device differs from lock")
    if (
        not isinstance(environment["commands"], list)
        or not environment["commands"]
        or not isinstance(environment["monitoring"], dict)
        or environment["monitoring"].get("selected_attempt") not in {1, 2, 3}
    ):
        _fail("device_mismatch", "smoke monitoring evidence is incomplete")
    sizes = strict_load_json(SIZE_REGISTRY_PATH)["selected_sizes"]
    runs = raw["runs"]
    if not isinstance(runs, list) or len(runs) != 3:
        _fail("smoke_incomplete", "smoke requires three size runs")
    for expected, run in zip(sizes, runs):
        required_run = {
            "size",
            "generate",
            "compile",
            "benchmark",
            "binary_sha256",
            "result_sha256",
            "validation_count",
            "correctness",
            "timing",
            "quality",
        }
        if not isinstance(run, dict) or set(run) != required_run or run["size"] != expected:
            _fail("smoke_incomplete", "smoke run field/size mismatch")
        for stage in ("generate", "compile", "benchmark"):
            if not isinstance(run[stage], dict) or run[stage].get("exit_code") != 0:
                _fail("smoke_incomplete", f"{stage} failed")
        if (
            isinstance(run["validation_count"], bool)
            or not isinstance(run["validation_count"], int)
            or run["validation_count"] <= 0
            or run["correctness"] != "pass"
        ):
            _fail("correctness_failure", "nonzero passing validation required")
        for field in ("timing", "quality"):
            value = run[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                _fail("smoke_incomplete", f"{field} must be finite positive")
    return {
        "schema_version": "1.0.0",
        "kind": "s10_smoke_correctness",
        "checkpoint_id": "S10",
        "status": "pass",
        "created_at": _utc_now(),
        "effective_lock_raw_sha256": lock_hash,
        "environment_revalidation": environment,
        "candidate_hash": raw["candidate_hash"],
        "runs": runs,
    }


def smoke() -> dict[str, Any]:
    _require_not_terminal("smoke")
    _require_no_existing(SMOKE_PATH)
    if not MAPPING_PATH.is_file():
        _fail("mapping_unresolved", "mapping corpus must precede smoke")
    document = _smoke_from_raw(_execute_smoke_raw())
    _validate(document, context="S10 smoke")
    atomic_write_json(SMOKE_PATH, document)
    return {"status": "SMOKE_PASS", "sizes": 3, "raw_sha256": sha256_file(SMOKE_PATH)}


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        _fail("noise_incomplete", "percentile input is empty")
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return float(ordered[lower])
    fraction = rank - lower
    return float(ordered[lower] * (1 - fraction) + ordered[upper] * fraction)


def _noise_executor_code() -> str:
    return r'''
import csv, datetime, hashlib, json, math, os, pathlib, subprocess, sys

MARKER = "S10_POSTLOCK_RESULT="

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

request = json.load(open(sys.argv[1], "r", encoding="utf-8"))
root = pathlib.Path(request["attempt_root"])
logs = root / "executor-logs"
logs.mkdir()
commands = []

def run(argv, name):
    stdout = logs / (name + ".stdout")
    stderr = logs / (name + ".stderr")
    started = now()
    proc = subprocess.run(
        argv, cwd=root, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    ended = now()
    stdout.write_bytes(proc.stdout)
    stderr.write_bytes(proc.stderr)
    commands.append({
        "argv": argv,
        "cwd": str(root),
        "started_at": started,
        "ended_at": ended,
        "exit_code": proc.returncode,
        "stdout": {"path": str(stdout), "raw_sha256": digest(stdout), "bytes": stdout.stat().st_size},
        "stderr": {"path": str(stderr), "raw_sha256": digest(stderr), "bytes": stderr.stat().st_size},
    })
    if proc.returncode:
        raise RuntimeError(name + " exited " + str(proc.returncode))

configs = {}
for item in request["anchors"]:
    run(item["build_argv"], "build-" + item["anchor_hash"])
    found = sorted(pathlib.Path(item["output"]).glob("**/*ClientParameters*.ini"))
    if len(found) != 1:
        raise RuntimeError("expected one client config for " + item["anchor_hash"])
    configs[item["anchor_hash"]] = found[0]

observations = []
order = 0
for cell in request["schedule"]:
    anchor = cell["anchor_hash"]
    repeat = cell["repeat"]
    base = configs[anchor]
    cell_root = root / ("cell-" + str(order).zfill(2))
    cell_root.mkdir()
    result_path = cell_root / "result.csv"
    config_path = cell_root / "ClientParameters.ini"
    lines = base.read_text(encoding="utf-8").splitlines()
    replaced = False
    updated = []
    for line in lines:
        if line.startswith("results-file="):
            updated.append("results-file=" + str(result_path))
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        raise RuntimeError("client config lacks results-file")
    config_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
    run(
        [request["client"], "--config-file", str(config_path)],
        "cell-" + str(order).zfill(2),
    )
    with result_path.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != len(request["sizes"]):
        raise RuntimeError("client result row count differs")
    seen = set()
    for row in rows:
        size = [int(row["Size" + letter]) for letter in "IJKL"]
        key = tuple(size)
        if key not in {tuple(value) for value in request["sizes"]} or key in seen:
            raise RuntimeError("client result size coverage differs")
        seen.add(key)
        quality = float(row["WinnerGFlops"])
        timing = float(row["WinnerTimeUS"])
        if not math.isfinite(quality) or quality <= 0 or not math.isfinite(timing) or timing <= 0:
            raise RuntimeError("client result is nonpositive/nonfinite")
        observations.append({
            "anchor_hash": anchor,
            "size": size,
            "repeat": repeat,
            "order": order * len(request["sizes"]) + len(seen) - 1,
            "timed_iterations": request["timed_iterations"],
            "quality": quality,
            "correctness": "pass",
            "raw_output_sha256": digest(result_path),
        })
    order += 1

print(MARKER + json.dumps(
    {"observations": observations, "commands": commands},
    sort_keys=True, separators=(",", ":")
))
'''


def _execute_noise_level(
    *,
    lock: Mapping[str, Any],
    multiplier: int,
    level_root: Path,
    integration_root: Path,
    native_binary: Path,
    client: Path,
    sizes: Sequence[Sequence[int]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    anchors = lock["anchor_hashes"]
    env = _base_env()
    env["PYTHONPATH"] = os.pathsep.join(
        _recorded_text(str(path))
        for path in (
            native_binary.parent,
            integration_root / "projects/hipblaslt/tensilelite",
        )
    )
    schedule = [
        {"anchor_hash": anchor, "repeat": repeat}
        for anchor in anchors
        for repeat in range(7)
    ]
    rng = random.Random(
        lock["noise_schedule"]["balanced_order_seed"] + multiplier
    )
    rng.shuffle(schedule)
    attempts = []
    for attempt_index in range(1, 4):
        attempt_root = level_root / f"attempt-{attempt_index}"
        attempt_root.mkdir(parents=True)
        anchor_requests = []
        timed_iterations = None
        for anchor in anchors:
            anchor_root = attempt_root / f"anchor-{anchor}"
            anchor_root.mkdir()
            config = anchor_root / "singleton.yaml"
            output = anchor_root / "output"
            config_record = _singleton_benchmark_yaml(
                lock=lock,
                candidate_hash=anchor,
                sizes=sizes,
                multiplier=multiplier,
                path=config,
            )
            timed_iterations = config_record["timed_iterations"]
            anchor_requests.append(
                {
                    "anchor_hash": anchor,
                    "build_argv": _tensile_benchmark_argv(
                        integration_root=integration_root,
                        config=config,
                        output=output,
                        device_index=lock["device"]["container_visible_index"],
                        client=client,
                    ),
                    "output": _recorded_text(str(output)),
                    "config": config_record,
                }
            )
        request = {
            "attempt_root": _recorded_text(str(attempt_root)),
            "client": _recorded_text(str(client)),
            "sizes": sizes,
            "timed_iterations": timed_iterations,
            "anchors": [
                {
                    "anchor_hash": item["anchor_hash"],
                    "build_argv": item["build_argv"],
                    "output": item["output"],
                }
                for item in anchor_requests
            ],
            "schedule": schedule,
        }
        request_path = attempt_root / "request.json"
        atomic_write_json(request_path, request)
        execution = _run_monitored(
            [
                str(PYTHON),
                "-S",
                "-c",
                _noise_executor_code(),
                _recorded_text(str(request_path)),
            ],
            lock=lock,
            cwd=attempt_root,
            env=env,
            attempt_root=attempt_root,
            name=f"noise-{multiplier}x",
        )
        attempt = {
            "attempt": attempt_index,
            "request": _bound_file(request_path),
            "anchor_configs": anchor_requests,
            "execution": execution,
            "phase_manifest": _output_manifest(attempt_root),
        }
        attempts.append(attempt)
        if execution["status"] == "contaminated":
            continue
        if execution["command"] is None or execution["command"]["exit_code"] != 0:
            _fail("noise_incomplete", f"{multiplier}x noise executor failed")
        result = _parse_marked_json(
            _load_ignored_log(
                execution["command"]["stdout"],
                role=f"noise-{multiplier}x-executor-stdout",
            ),
            phase="noise",
        )
        observations = result.get("observations")
        if not isinstance(observations, list) or len(observations) != 63:
            _fail("noise_incomplete", f"{multiplier}x executor lacks 63 cells")
        level = {"multiplier": multiplier, "observations": observations}
        return level, {
            "selected_attempt": attempt_index,
            "maximum_complete_attempts": 3,
            "attempts": attempts,
            "executor_commands": result.get("commands"),
        }
    _fail("device_mismatch", f"all three {multiplier}x noise attempts contaminated")


def _level_p95_cv(observations: Sequence[Mapping[str, Any]]) -> float:
    grouped: dict[tuple[str, tuple[int, ...]], list[float]] = {}
    for item in observations:
        grouped.setdefault(
            (item["anchor_hash"], tuple(item["size"])), []
        ).append(float(item["quality"]))
    if len(grouped) != 9:
        _fail("noise_incomplete", "noise level lacks nine anchor/size groups")
    return _percentile([_cv(values) for values in grouped.values()], 0.95)


def _execute_noise_raw() -> Mapping[str, Any]:
    lock, lock_hash = _load_lock()
    if not SMOKE_PATH.is_file():
        _fail("smoke_incomplete", "passing smoke must precede noise")
    mapping_doc = strict_load_json(MAPPING_PATH)
    for anchor in lock["anchor_hashes"]:
        rows = [
            row for row in mapping_doc["rows"] if row["config_hash"] == anchor
        ]
        if len(rows) != 3 or any(row["status"] != "accepted" for row in rows):
            _fail("noise_incomplete", f"locked anchor is not valid: {anchor}")
    scratch_root = _active_scratch_root()
    noise_root = scratch_root / "postlock/noise"
    if noise_root.exists():
        _fail("already_exists", f"noise raw root exists: {_rel(noise_root)}")
    noise_root.mkdir(parents=True)
    provenance = strict_load_json(PROVENANCE_PATH)
    run = provenance["runs"][0]
    integration = strict_load_json(ROOT / run["integration"]["path"])
    native = strict_load_json(ROOT / run["native"]["path"])
    integration_root = ROOT / integration["root"]
    native_binary = ROOT / native["binary"]["path"]
    client = _postlock_native_client()
    sizes = strict_load_json(SIZE_REGISTRY_PATH)["selected_sizes"]
    levels = []
    monitoring = []
    for multiplier in (1, 2, 4):
        level, monitor = _execute_noise_level(
            lock=lock,
            multiplier=multiplier,
            level_root=noise_root / f"level-{multiplier}x",
            integration_root=integration_root,
            native_binary=native_binary,
            client=client,
            sizes=sizes,
        )
        levels.append(level)
        monitoring.append({"multiplier": multiplier, **monitor})
        if _level_p95_cv(level["observations"]) <= 0.005:
            break
    raw = {
        "lock_raw_sha256": lock_hash,
        "levels": levels,
        "reduce_fn": strict_load_json(PROVENANCE_PATH)["consumption"]["reduce_fn"],
        "monitoring": {
            "fixed_device": lock["device"],
            "maximum_during_sample_period_seconds": 1,
            "levels": monitoring,
        },
    }
    atomic_write_json(noise_root / "noise-raw.json", raw)
    return raw


def _cv(values: Sequence[float]) -> float:
    if len(values) != 7 or any(value <= 0 or not math.isfinite(value) for value in values):
        _fail("noise_incomplete", "CV requires seven finite positive observations")
    mean = statistics.fmean(values)
    return statistics.stdev(values) / mean


def _noise_from_raw(raw: Mapping[str, Any]) -> dict[str, Any]:
    lock, lock_hash = _load_lock()
    required = {"lock_raw_sha256", "levels", "reduce_fn", "monitoring"}
    if set(raw) != required or raw["lock_raw_sha256"] != lock_hash:
        _fail("lock_binding_mismatch", "noise raw lock/fields mismatch")
    if raw["reduce_fn"] not in {"mean", "max"}:
        _fail("noise_incomplete", "unknown reduce_fn")
    sizes = strict_load_json(SIZE_REGISTRY_PATH)["selected_sizes"]
    anchors = lock["anchor_hashes"]
    expected_pairs = {(anchor, tuple(size), repeat) for anchor in anchors for size in sizes for repeat in range(7)}
    levels = raw["levels"]
    if not isinstance(levels, list) or not 1 <= len(levels) <= 3:
        _fail("noise_incomplete", "noise levels must be a one-to-three item list")
    multipliers = [
        level.get("multiplier") if isinstance(level, dict) else None
        for level in levels
    ]
    if multipliers != [1, 2, 4][: len(multipliers)]:
        _fail("noise_incomplete", "noise escalation levels must be the ordered 1x/2x/4x prefix")
    complete_levels = []
    selected = None
    for level in levels:
        if not isinstance(level, dict) or set(level) != {"multiplier", "observations"}:
            _fail("noise_incomplete", "noise level field set mismatch")
        if level["multiplier"] not in {1, 2, 4}:
            _fail("noise_incomplete", "unexpected escalation multiplier")
        observations = level["observations"]
        if len(observations) != 63:
            _fail("noise_incomplete", "complete level must contain exactly 63 observations")
        seen = set()
        by_pair: dict[tuple[str, tuple[int, ...]], list[float]] = {}
        by_anchor_repeat: dict[tuple[str, int], list[float]] = {}
        for item in observations:
            required_obs = {
                "anchor_hash",
                "size",
                "repeat",
                "order",
                "timed_iterations",
                "quality",
                "correctness",
                "raw_output_sha256",
            }
            if not isinstance(item, dict) or set(item) != required_obs:
                _fail("noise_incomplete", "noise observation fields mismatch")
            identity = (item["anchor_hash"], tuple(item["size"]), item["repeat"])
            if identity not in expected_pairs or identity in seen:
                _fail("noise_incomplete", f"unexpected/duplicate observation {identity}")
            seen.add(identity)
            if item["correctness"] != "pass":
                _fail("correctness_failure", "noise correctness failure")
            quality = item["quality"]
            if isinstance(quality, bool) or not isinstance(quality, (int, float)) or quality <= 0 or not math.isfinite(quality):
                _fail("noise_incomplete", "noise quality must be finite positive")
            if not HASH_RE.fullmatch(str(item["raw_output_sha256"])):
                _fail("noise_incomplete", "noise raw output hash malformed")
            by_pair.setdefault((item["anchor_hash"], tuple(item["size"])), []).append(float(quality))
            by_anchor_repeat.setdefault((item["anchor_hash"], item["repeat"]), []).append(float(quality))
        if seen != expected_pairs or sorted(item["order"] for item in observations) != list(range(63)):
            _fail("noise_incomplete", "noise panel/order is incomplete")
        cvs = [
            {
                "anchor_hash": anchor,
                "size": list(size),
                "cv": _cv(values),
            }
            for (anchor, size), values in sorted(by_pair.items())
        ]
        p95_cv = _percentile([item["cv"] for item in cvs], 0.95)
        aggregate = []
        for (anchor, repeat), values in sorted(by_anchor_repeat.items()):
            if len(values) != 3:
                _fail("noise_incomplete", "anchor/repeat lacks three sizes")
            q = statistics.fmean(values) if raw["reduce_fn"] == "mean" else max(values)
            aggregate.append({"anchor_hash": anchor, "repeat": repeat, "Q_ar": q})
        medians = {
            anchor: statistics.median(
                math.log(item["Q_ar"])
                for item in aggregate
                if item["anchor_hash"] == anchor
            )
            for anchor in anchors
        }
        deviations = [
            abs(math.log(item["Q_ar"]) - medians[item["anchor_hash"]])
            for item in aggregate
        ]
        delta_noise = math.exp(_percentile(deviations, 0.95)) - 1.0
        completed = {
            "multiplier": level["multiplier"],
            "observations": observations,
            "cvs": cvs,
            "p95_cv": p95_cv,
            "aggregate_quality": aggregate,
            "log_deviations": deviations,
            "delta_noise": delta_noise,
        }
        complete_levels.append(completed)
        if selected is None and p95_cv <= 0.005:
            selected = completed
            break
    if not complete_levels:
        _fail("noise_incomplete", "no complete noise level")
    status = "stable" if selected is not None else "noise_blocked"
    if selected is None and complete_levels[-1]["multiplier"] != 4:
        _fail("noise_incomplete", "escalation stopped before 4x cap")
    chosen = selected or complete_levels[-1]
    return {
        "schema_version": "1.0.0",
        "kind": "s10_noise_pilot",
        "checkpoint_id": "S10",
        "status": status,
        "created_at": _utc_now(),
        "effective_lock_raw_sha256": lock_hash,
        "anchor_hashes": anchors,
        "sizes": sizes,
        "repeat_count": 7,
        "balanced_order_seed": lock["noise_schedule"]["balanced_order_seed"],
        "level_multipliers": [1, 2, 4],
        "completed_levels": complete_levels,
        "selected_multiplier": chosen["multiplier"] if selected else None,
        "capped_multiplier": 4,
        "p95_cv": chosen["p95_cv"],
        "cv_threshold": 0.005,
        "reduce_fn": raw["reduce_fn"],
        "delta_noise": chosen["delta_noise"],
        "monitoring": raw["monitoring"],
    }


def noise() -> dict[str, Any]:
    _require_not_terminal("noise")
    _require_no_existing(NOISE_PATH)
    if not SMOKE_PATH.is_file():
        _fail("smoke_incomplete", "passing smoke must precede noise")
    document = _noise_from_raw(_execute_noise_raw())
    _validate(document, context="S10 noise")
    atomic_write_json(NOISE_PATH, document)
    return {
        "status": document["status"],
        "completed_levels": len(document["completed_levels"]),
        "p95_cv": document["p95_cv"],
        "delta_noise": document["delta_noise"],
        "raw_sha256": sha256_file(NOISE_PATH),
    }


def decide() -> dict[str, Any]:
    _require_no_existing(DECISION_PATH)
    lock, lock_hash = _load_lock()
    required = [PROVENANCE_PATH, SIZE_REGISTRY_PATH, ENVIRONMENT_PATH, MAPPING_PATH]
    artifacts: list[dict[str, str]] = []
    for path in required:
        if not path.is_file():
            _fail("decision_incomplete", f"missing {_rel(path)}")
        document = strict_load_json(path)
        _validate(document, context=f"S10 decision input {_rel(path)}")
        artifacts.append(_bound_file(path))
    provenance = strict_load_json(PROVENANCE_PATH)
    sizes = strict_load_json(SIZE_REGISTRY_PATH)
    mapping_doc = strict_load_json(MAPPING_PATH)
    environment = strict_load_json(ENVIRONMENT_PATH)
    integrity = mapping_doc["mapping_evidence_integrity"]
    entry = mapping_doc["mapping_entry"]
    if (
        integrity["status"] != "PASS"
        or integrity["execution"] != "complete"
    ):
        _fail(
            "postlock_harness_defect",
            "mapping evidence integrity is not complete PASS; no decision is permitted",
        )

    def gate(
        name: str,
        role: str,
        status: str,
        execution: str,
        reason_code: str,
        reason_text: str,
        *,
        evidence: Sequence[Mapping[str, str]] = (),
        failure_id: str | None = None,
        blocked_by: Sequence[str] = (),
        blocked_absence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "name": name,
            "role": role,
            "status": status,
            "execution": execution,
            "reason_code": reason_code,
            "reason_text": reason_text,
            "failure_id": failure_id,
            "blocked_by": list(blocked_by),
            "evidence": list(evidence),
            "blocked_absence": blocked_absence,
        }

    gates = [
        gate(
            "actual_guidance",
            "prerequisite",
            "PASS",
            "complete",
            "fresh_actual_guidance",
            "fresh dual-generation provenance is complete",
            evidence=[_bound_file(PROVENANCE_PATH)],
        ),
        gate(
            "three_sizes",
            "prerequisite",
            "PASS",
            "complete",
            "fresh_three_size_registry",
            "three frozen same-space sizes are present",
            evidence=[_bound_file(SIZE_REGISTRY_PATH)],
        ),
        gate(
            "h4_and_environment",
            "prerequisite",
            "PASS",
            "complete",
            "fresh_live_unreserved_lock",
            "fresh live R5 selection and environment are lock-bound",
            evidence=[_bound_file(ENVIRONMENT_PATH), _bound_file(LOCK_PATH)],
        ),
        gate(
            "mapping_evidence_integrity",
            "evidence_integrity",
            "PASS",
            "complete",
            integrity["reason_code"],
            integrity["reason_text"],
            evidence=[_bound_file(MAPPING_PATH)],
        ),
        gate(
            "mapping_entry",
            "entry_gate",
            entry["status"],
            "complete",
            entry["reason_code"],
            entry["reason_text"],
            evidence=[_bound_file(MAPPING_PATH)],
            failure_id=entry["failure_id"],
        ),
    ]
    mapping_negative = entry["status"] == "FAIL"
    if mapping_negative:
        blocked = "mapping_entry"
        raw_smoke = _active_scratch_root() / "postlock/smoke"
        raw_noise = _active_scratch_root() / "postlock/noise"
        raw_decision = (
            _active_scratch_root()
            / "postlock/decision/negative-stop-raw.json"
        )
        absence_targets = [
            (SMOKE_PATH, raw_smoke, "smoke"),
            (NOISE_PATH, raw_noise, "noise"),
        ]
        prechecks = []
        for canonical, raw, role in absence_targets:
            if (
                canonical.exists()
                or canonical.is_symlink()
                or raw.exists()
                or raw.is_symlink()
            ):
                _fail(
                    "decision_incomplete",
                    f"{role} must be blocked-absent after mapping-entry FAIL",
                )
            prechecks.append(
                {
                    "role": role,
                    "canonical_path": _rel(canonical),
                    "raw_path": _rel(raw),
                    "canonical_absent": True,
                    "raw_absent": True,
                    "checked_at": _utc_now(),
                }
            )
        raw_decision.parent.mkdir(parents=True, exist_ok=False)
        postchecks = []
        for canonical, raw, role in absence_targets:
            if (
                canonical.exists()
                or canonical.is_symlink()
                or raw.exists()
                or raw.is_symlink()
            ):
                _fail("decision_incomplete", f"{role} absence changed")
            postchecks.append(
                {
                    "role": role,
                    "canonical_path": _rel(canonical),
                    "raw_path": _rel(raw),
                    "canonical_absent": True,
                    "raw_absent": True,
                    "checked_at": _utc_now(),
                }
            )
        stop_rule = {
            "mapping_integrity": "PASS",
            "mapping_entry": "FAIL",
            "downstream_execution": "not_activated",
            "taxonomy": "FT-BLOCKED-MAPPING",
            "criterion": "S1_ENTRY_BLOCKED",
            "edge": None,
        }
        negative_stop = {
            "schema_version": "1.0.0",
            "kind": "s10_negative_stop_raw",
            "checkpoint_id": "S10",
            "created_at": _utc_now(),
            "effective_lock": _bound_file(LOCK_PATH),
            "mapping": _bound_file(MAPPING_PATH),
            "derivation": {
                "mapping_evidence_integrity": integrity,
                "mapping_entry": entry,
            },
            "stop_rule": stop_rule,
            "stop_rule_identity": canonical_sha256(stop_rule),
            "bound_implementation": [
                _bound_file(Path(__file__)),
                _bound_file(SCHEMA_PATH),
                _bound_file(CONTRACT_PATH),
            ],
            "absence_rechecks": {
                "before_exclusive_decision_directory": prechecks,
                "after_exclusive_decision_directory": postchecks,
            },
            "decision_evidence_only": True,
            "smoke_or_noise_evidence": False,
        }
        _write_exclusive_json(raw_decision, negative_stop)
        negative_stop_ref = _bound_file(raw_decision)
        artifacts.append(negative_stop_ref)
        gates.extend(
            [
                gate(
                    "smoke_correctness",
                    "blocked_absent",
                    "BLOCKED",
                    "not_activated",
                    "blocked_by_mapping_entry",
                    "smoke was not activated after definitive mapping-entry FAIL",
                    blocked_by=[blocked],
                    blocked_absence={
                        "canonical_path": _rel(SMOKE_PATH),
                        "raw_path": _rel(raw_smoke),
                        "must_be_absent": True,
                        "blocked_by": blocked,
                    },
                ),
                gate(
                    "noise_stable",
                    "blocked_absent",
                    "BLOCKED",
                    "not_activated",
                    "blocked_by_mapping_entry",
                    "noise was not activated after definitive mapping-entry FAIL",
                    blocked_by=[blocked],
                    blocked_absence={
                        "canonical_path": _rel(NOISE_PATH),
                        "raw_path": _rel(raw_noise),
                        "must_be_absent": True,
                        "blocked_by": blocked,
                    },
                ),
            ]
        )
        scientific_outcome = "negative"
        criterion = "S1_ENTRY_BLOCKED"
        edge = None
        failure_taxonomy = ["FT-BLOCKED-MAPPING"]
        decision_evidence = negative_stop_ref
    else:
        if entry["status"] != "PASS":
            _fail("decision_incomplete", "mapping entry is not terminally classifiable")
        for path in (SMOKE_PATH, NOISE_PATH):
            if not path.is_file():
                _fail("decision_incomplete", f"missing {_rel(path)}")
            document = strict_load_json(path)
            _validate(document, context=f"S10 decision input {_rel(path)}")
            artifacts.append(_bound_file(path))
        smoke_doc = strict_load_json(SMOKE_PATH)
        noise_doc = strict_load_json(NOISE_PATH)
        smoke_pass = smoke_doc["status"] == "pass"
        noise_pass = (
            noise_doc["status"] == "stable"
            and noise_doc["p95_cv"] <= 0.005
        )
        gates.extend(
            [
                gate(
                    "smoke_correctness",
                    "execution_gate",
                    "PASS" if smoke_pass else "FAIL",
                    "complete",
                    "smoke_complete" if smoke_pass else "smoke_failed",
                    "locked three-size smoke is complete",
                    evidence=[_bound_file(SMOKE_PATH)],
                    failure_id=None if smoke_pass else "S10-SMOKE-FAIL",
                ),
                gate(
                    "noise_stable",
                    "execution_gate",
                    "PASS" if noise_pass else "INCONCLUSIVE",
                    "complete",
                    "noise_threshold_pass" if noise_pass else "noise_cap_indeterminate",
                    "locked complete noise level was evaluated",
                    evidence=[_bound_file(NOISE_PATH)],
                    failure_id=None if noise_pass else "S10-NOISE-INCONCLUSIVE",
                ),
            ]
        )
        go = all(item["status"] == "PASS" for item in gates)
        scientific_outcome = "positive" if go else "inconclusive"
        criterion = "S1_ENTRY_GO" if go else "S1_ENTRY_BLOCKED"
        edge = "S1_ENTRY_GO -> S11" if go else None
        failure_taxonomy = [] if go else ["FT-INCONCLUSIVE"]
        decision_evidence = None

    if (
        provenance["status"] != "prelock_complete"
        or sizes["distinct_count"] < 3
        or len(sizes["selected_sizes"]) != 3
        or environment["status"] != "prelock_complete"
    ):
        _fail("decision_incomplete", "an ordered prerequisite gate is not PASS")
    decision_doc = {
        "schema_version": "1.0.0",
        "kind": "s10_decision",
        "checkpoint_id": "S10",
        "status": "complete",
        "created_at": _utc_now(),
        "effective_lock_raw_sha256": lock_hash,
        "study_mode": "ready_actual_yaml_guidance",
        "completion_correctness": "complete",
        "scientific_outcome": scientific_outcome,
        "criterion": criterion,
        "edge": edge,
        "gates": gates,
        "failure_taxonomy": failure_taxonomy,
        "artifacts": artifacts,
        "decision_evidence": decision_evidence,
        "claim_limitations": [
            "No Formocast ranking claim",
            "No factorization or Gen0 claim",
            "No speedup, convergence, generalization, deployment, or production claim",
        ],
    }
    _validate(decision_doc, context="S10 decision")
    atomic_write_json(DECISION_PATH, decision_doc)
    return {
        "status": criterion,
        "edge": edge,
        "raw_sha256": sha256_file(DECISION_PATH),
    }


def validate_phase(phase: str) -> dict[str, Any]:
    if phase == "prelock":
        _reject_early_postlock_targets()
    _preflight(require_outputs=True)
    _verify_prelock_artifacts()
    if phase == "prelock":
        return {"status": "PRELOCK_VALID", "H4": "LIVE_PROBE_REQUIRED"}
    lock, lock_hash = _load_lock()
    for path in (ENVIRONMENT_PATH, MAPPING_PATH, DECISION_PATH):
        document = strict_load_json(path)
        _validate(document, context=f"S10 post-lock {_rel(path)}")
        if (
            path != ENVIRONMENT_PATH
            and document.get("effective_lock_raw_sha256") != lock_hash
        ):
            _fail("lock_binding_mismatch", f"{_rel(path)} has wrong lock")
    decision_doc = strict_load_json(DECISION_PATH)
    if decision_doc["scientific_outcome"] == "negative":
        for path in (SMOKE_PATH, NOISE_PATH):
            if path.exists() or path.is_symlink():
                _fail(
                    "decision_incomplete",
                    f"negative decision requires blocked absence: {_rel(path)}",
                )
        stop = decision_doc.get("decision_evidence")
        if (
            not isinstance(stop, dict)
            or not (ROOT / stop["path"]).is_file()
            or sha256_file(ROOT / stop["path"]) != stop["raw_sha256"]
        ):
            _fail("decision_incomplete", "negative stop evidence is unavailable")
    else:
        for path in (SMOKE_PATH, NOISE_PATH):
            document = strict_load_json(path)
            _validate(document, context=f"S10 post-lock {_rel(path)}")
            if document.get("effective_lock_raw_sha256") != lock_hash:
                _fail("lock_binding_mismatch", f"{_rel(path)} has wrong lock")
    if decision_doc["criterion"] == "S1_ENTRY_GO" and decision_doc["edge"] != "S1_ENTRY_GO -> S11":
        _fail("decision_incomplete", "GO decision edge mismatch")
    if decision_doc["criterion"] != "S1_ENTRY_GO" and decision_doc["edge"] is not None:
        _fail("decision_incomplete", "non-GO decision carries downstream edge")
    return {"status": "POSTLOCK_VALID", "lock_id": lock["lock_id"]}


def reproduce(output_dir: Path) -> dict[str, Any]:
    """Fresh verifier-only reproduction entry.

    It creates a new ignored root and re-runs all deterministic pre-lock
    construction.  Post-lock mapping reproduction is intentionally refused
    until an effective lock and original mapping corpus exist.
    """

    if output_dir.exists():
        _fail("already_exists", f"reproduction output exists: {output_dir}")
    result = prepare(output_dir)
    if LOCK_PATH.exists():
        if not MAPPING_PATH.is_file():
            _fail("mapping_unresolved", "effective lock exists without mapping corpus")
        result["locked_mapping_headline_sha256"] = sha256_file(MAPPING_PATH)
    return {"status": "REPRODUCED", "prelock": result}


def reproduce_mapping(output_dir: Path) -> dict[str, Any]:
    """Fresh verifier-owned mapping A/B and independent gate derivation."""

    output_dir = _assert_scratch_root(output_dir)
    if output_dir.exists() or output_dir.is_symlink():
        _fail("already_exists", f"mapping reproduction output exists: {output_dir}")
    lock, lock_hash = _load_lock()
    output_dir.mkdir(parents=True)
    provenance = strict_load_json(PROVENANCE_PATH)
    integration = strict_load_json(
        ROOT / provenance["runs"][0]["integration"]["path"]
    )
    integration_root = ROOT / integration["root"]
    helper, native_build = _build_mapping_native_helper(
        mapping_root=output_dir,
        integration_root=integration_root,
    )
    rows, first = _mapping_pass(
        lock,
        pass_root=output_dir / "pass-a",
        pass_name="verifier-mapping-pass-a",
        native_helper=helper,
    )
    rerun, second = _mapping_pass(
        lock,
        pass_root=output_dir / "pass-b",
        pass_name="verifier-mapping-pass-b",
        native_helper=helper,
    )
    raw = {
        "lock_raw_sha256": lock_hash,
        "rows": rows,
        "rerun_rows": rerun,
        "executor": {
            "kind": "fresh_verifier_pinned_ductile_post_codegen_mapping_v2",
            "native_build": native_build,
            "passes": [first, second],
            "compiler_default_outputs_confined": True,
            "prelock_actual_candidate_results_reused": False,
        },
    }
    document = _mapping_from_raw(raw)
    _validate(document, context="fresh verifier mapping reproduction")
    output_path = output_dir / "mapping-reproduction.json"
    _write_exclusive_json(output_path, document)
    canonical = strict_load_json(MAPPING_PATH)
    comparable_fields = [
        "candidate_count",
        "size_count",
        "row_count",
        "anchor_hashes",
        "rows",
        "deterministic_rerun_parity",
        "mapping_evidence_integrity",
        "mapping_entry",
    ]
    parity = all(document[key] == canonical[key] for key in comparable_fields)
    if not parity:
        _fail("mapping_unresolved", "fresh verifier mapping differs")
    return {
        "status": "MAPPING_REPRODUCED",
        "output": _bound_file(output_path),
        "canonical_mapping": _bound_file(MAPPING_PATH),
        "semantic_parity": True,
        "independent_gate_derivation": {
            "mapping_evidence_integrity": document["mapping_evidence_integrity"],
            "mapping_entry": document["mapping_entry"],
        },
    }


def _summary_json(value: Mapping[str, Any]) -> None:
    sys.stdout.buffer.write(canonical_json_bytes(value) + b"\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight")
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--scratch-root", required=True, type=Path)
    check_parser = sub.add_parser("prelock-check")
    check_parser.add_argument("--scratch-root", required=True, type=Path)
    lock_parser = sub.add_parser("lock")
    lock_parser.add_argument("--plan-b", required=True, type=Path)
    sub.add_parser("mapping")
    sub.add_parser("smoke")
    sub.add_parser("noise")
    sub.add_parser("decision")
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--phase", choices=("prelock", "postlock"), required=True)
    reproduce_parser = sub.add_parser("reproduce")
    reproduce_parser.add_argument("--output-dir", required=True, type=Path)
    reproduce_mapping_parser = sub.add_parser("reproduce-mapping")
    reproduce_mapping_parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "preflight":
            result = _preflight()
        elif args.command == "prepare":
            result = prepare(args.scratch_root)
        elif args.command == "prelock-check":
            result = prelock_check(args.scratch_root)
        elif args.command == "lock":
            result = create_lock(args.plan_b)
        elif args.command == "mapping":
            result = mapping()
        elif args.command == "smoke":
            result = smoke()
        elif args.command == "noise":
            result = noise()
        elif args.command == "decision":
            result = decide()
        elif args.command == "validate":
            result = validate_phase(args.phase)
        elif args.command == "reproduce":
            result = reproduce(args.output_dir)
        elif args.command == "reproduce-mapping":
            result = reproduce_mapping(args.output_dir)
        else:
            _fail("unknown_command", args.command)
    except EvidenceValidationError as exc:
        _summary_json(
            {
                "status": "ERROR",
                "checkpoint_id": "S10",
                "error_code": exc.code,
                "message": str(exc),
            }
        )
        stable_codes = {
            "authority_mismatch": 20,
            "overlay_collision": 21,
            "forbidden_import": 22,
            "network_fetch_detected": 23,
            "native_lineage_mismatch": 24,
            "generation_manifest_mismatch": 25,
            "qualifying_yaml_count": 26,
            "ductile_parity_mismatch": 27,
            "two_size_downgrade": 28,
            "live_gpu_unavailable": 40,
            "lock_binding_mismatch": 41,
            "mapping_unresolved": 42,
            "postlock_harness_defect": 47,
            "transition_claimed": 48,
            "terminal_command_refused": 49,
            "device_mismatch": 43,
            "correctness_failure": 44,
            "noise_incomplete": 45,
            "noise_blocked": 46,
        }
        return stable_codes.get(exc.code, 2)
    _summary_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
