# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Strict S11 base+r2 contract resolution, lock, and admission helpers."""

from __future__ import annotations

import copy
import hashlib
import io
import os
import stat
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema
import yaml

from .canonical import (
    canonical_sha256,
    exclusive_write_json,
    sha256_file,
    strict_json_loads,
    strict_load_json,
)


class ContractError(ValueError):
    """The S11 authority, contract, lock, or formal admission is invalid."""


PACKAGE_ROOT = Path(__file__).resolve().parent
PROTOCOL_ROOT = PACKAGE_ROOT.parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[5]
DEFAULT_CONTRACT_PATH = PROTOCOL_ROOT / "s11-stage1-model-only-factorization-contract.yaml"
DEFAULT_REVISION_PATH = PROTOCOL_ROOT / "s11-stage1-model-only-factorization-contract-r2.yaml"
DEFAULT_PREIMPLEMENTATION_LOCK_PATH = (
    PROTOCOL_ROOT / "locks/s11-stage1-model-only-factorization-preimplementation-lock-r2.json"
)
DEFAULT_STRUCTURAL_REGISTRY_PATH = PROTOCOL_ROOT / "manifests/s11-structural-registry.json"
DEFAULT_SCHEMA_PATH = PROTOCOL_ROOT / "schemas/s11-factorization.schema.json"
DEFAULT_LOCK_PATH = PROTOCOL_ROOT / "locks/s11-stage1-model-only-factorization-lock.json"

BASE_SHA256 = "6b91bb18ba4e70c2a1aaee38440c95365454cd584ae0c74d6d7ab087e5aa6bab"
REVISION_SHA256 = "f30cee7d9570c43dcdbb266956d4d88f5f8f798cd256bad1f51a6c607ef4cec8"
PREIMPLEMENTATION_LOCK_SHA256 = (
    "46e54fc8f33507f02ac3b4d1b63af9bc88a9c116db37ae14f59f30832d384fcd"
)
STRUCTURAL_REGISTRY_SHA256 = (
    "0ab89fbd946ca596a98580efcc75f47480868c48bdaf90069897e74d0326e413"
)
APPROVED_IMPLEMENTATION_PARENT_COMMIT = (
    "e7b2c33d91a127e498e3f2c2440769b188efedfd"
)
ORDERED_CONTRACT_HASHES = [BASE_SHA256, REVISION_SHA256]
FORMAL_COMMANDS = (
    "global-discovery",
    "conditional-discovery",
    "qualify",
    "score",
    "analyze",
    "decide",
    "reproduce",
)
EXPECTED_IMPLEMENTATION_WHITELIST = (
    "projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s11_factorization.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/run_s11_factorization.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/s11-factorization.schema.json",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/__init__.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/canonical.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/contract.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/decision.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/guidance.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/ledger.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/native_adapter.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/native_formocast_runtime_adapter.cpp",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/populations.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/qualification.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/qualification_worker.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/registry.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/sampling.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/state_machine.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/statistics.py",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/s11/workflow.py",
)
IMPLEMENTATION_MANIFEST_PATH = (
    PROTOCOL_ROOT / "manifests/s11-implementation.json"
)
TOOLCHAIN_KEYS = (
    "validator_adapter_path", "validator_adapter_sha256", "validator_source_sha256",
    "validator_source_path", "validator_protocol", "validator_worker_count",
    "validator_argv", "validator_working_directory", "validator_tmpdir",
    "validator_pythonpycacheprefix", "validator_timeout_seconds", "compiler_path",
    "compiler_sha256",
    "compiler_version",
    "qualification_python_path", "qualification_python_sha256",
    "qualification_worker_source_path", "qualification_worker_source_sha256",
    "native_helper_path", "native_helper_sha256", "native_helper_source_path",
    "native_helper_source_sha256", "native_build_argv", "qualification_argv",
    "resolver_source_sha256",
    "kernelwriter_source_sha256", "semantic_identity_schema",
    "qualification_fingerprint_sha256", "qualification_timeout_seconds",
    "native_timeout_seconds",
)
TIMEOUT_KEYS = (
    "validator_timeout_seconds", "qualification_timeout_seconds", "native_timeout_seconds"
)
PINNED_SOURCE_PREFIXES = (
    "projects/hipblaslt/tensilelite",
    "shared/origami",
)
PINNED_SKIPPED_SYMLINKS = ("projects/hipblaslt/tensilelite/CLAUDE.md",)
PINNED_ORIGAMI_LINK_SOURCES = (
    "shared/origami/src/origami/gemm.cpp",
    "shared/origami/src/origami/hardware.cpp",
    "shared/origami/src/origami/heuristics.cpp",
    "shared/origami/src/origami/logger.cpp",
    "shared/origami/src/origami/origami.cpp",
    "shared/origami/src/origami/streamk.cpp",
    "shared/origami/src/origami/types.cpp",
    "shared/origami/src/simulator/tensilelite/formocast.cpp",
    "shared/origami/src/simulator/tensilelite/formocast_simulator.cpp",
)
NATIVE_BUILD_PROVENANCE_KEYS = {
    "document_kind", "schema_version", "checkpoint_id", "build_sha256",
    "compile_argv", "link_argv", "pinned_source_root", "pinned_source_manifest_sha256",
    "generated_headers", "linked_objects", "linked_sources",
}


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: yaml.Loader, node: yaml.Node, deep: bool = False) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ContractError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def strict_load_yaml(path: Path | str) -> dict[str, Any]:
    target = Path(path)
    info = target.lstat()
    if not stat.S_ISREG(info.st_mode) or target.is_symlink():
        raise ContractError(f"YAML authority is not an ordinary file: {target}")
    try:
        document = yaml.load(target.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        raise ContractError("malformed strict UTF-8 YAML") from error
    if type(document) is not dict:
        raise ContractError("YAML authority root must be a mapping")
    return document


def _require_raw_hash(path: Path | str, expected: str, label: str) -> None:
    if sha256_file(path) != expected:
        raise ContractError(f"{label} raw SHA-256 mismatch")


def _pointer_parts(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ContractError("revision patch path is not an absolute JSON pointer")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def _append_unique(document: dict[str, Any], pointer: str, values: Sequence[Any]) -> None:
    target: Any = document
    parts = _pointer_parts(pointer)
    for part in parts:
        if type(target) is not dict or part not in target:
            raise ContractError(f"revision patch path is unknown: {pointer}")
        target = target[part]
    if type(target) is not list or type(values) is not list:
        raise ContractError(f"append_unique target/value is not a list: {pointer}")
    for value in values:
        if value in target:
            raise ContractError(f"revision patch duplicates tuple entry: {value}")
        target.append(copy.deepcopy(value))


def load_contract(
    path: Path | str = DEFAULT_CONTRACT_PATH,
    *,
    revision_path: Path | str = DEFAULT_REVISION_PATH,
    preimplementation_lock_path: Path | str = DEFAULT_PREIMPLEMENTATION_LOCK_PATH,
    verify_hashes: bool = True,
) -> dict[str, Any]:
    """Resolve the active contract as ordered strict base plus revision 2."""

    if verify_hashes:
        _require_raw_hash(path, BASE_SHA256, "base contract")
        _require_raw_hash(revision_path, REVISION_SHA256, "revision-2 contract")
        _require_raw_hash(
            preimplementation_lock_path,
            PREIMPLEMENTATION_LOCK_SHA256,
            "revision-2 preimplementation lock",
        )
        _require_raw_hash(
            DEFAULT_STRUCTURAL_REGISTRY_PATH,
            STRUCTURAL_REGISTRY_SHA256,
            "S11 structural registry",
        )
    base = strict_load_yaml(path)
    revision = strict_load_yaml(revision_path)
    prelock = strict_load_json(preimplementation_lock_path)
    revision_keys = {
        "document_kind", "schema_version", "checkpoint_id", "revision", "status",
        "formal_evidence_authorized", "reason", "scientific_change", "measurement_change",
        "claim_change", "lineage_change", "evidence_reuse", "predecessor",
        "active_contract_resolution", "half_tuple_model_test_expansion",
        "write_boundary_addendum", "ownership", "formal_admission",
    }
    if set(revision) != revision_keys:
        raise ContractError("revision-2 schema/unknown-field failure")
    if (
        revision["document_kind"] != "s11_factorization_contract_revision"
        or revision["revision"] != 2
        or revision["checkpoint_id"] != "S11"
        or any(revision[key] is not False for key in ("scientific_change", "measurement_change", "claim_change", "lineage_change"))
    ):
        raise ContractError("revision-2 identity/scientific boundary changed")
    resolution = revision["active_contract_resolution"]
    if set(resolution) != {
        "identity", "loader", "base_hash_must_match_before_overlay", "unknown_patch_path",
        "duplicate_tuple_entry", "mutation_of_unlisted_base_field", "all_unlisted_base_fields",
        "patch_operations",
    } or resolution["identity"] != "ordered_base_plus_revision_2":
        raise ContractError("active contract resolution law changed")
    expected_operations = [
        {"op": "append_unique", "path": "/statistics/half_stability/exact_tuple", "values": ["per_size_and_aggregate_direction", "each_model_test_result"]},
        {"op": "append_unique", "path": "/fixed_frame_analysis/semantic_half_tuple", "values": ["per_size_and_aggregate_direction", "each_model_test_result"]},
    ]
    if resolution["patch_operations"] != expected_operations:
        raise ContractError("revision-2 patch order/path/value changed")
    if type(prelock) is not dict or set(prelock) != {
        "active_contract", "checkpoint_id", "document_kind", "effective_formal_lock",
        "formal_evidence_authorized", "implementation_bindings", "lock_id",
        "outcome_artifact_state", "parent_preimplementation_lock", "schema_version",
        "state", "structural_registry", "toolchain_bindings",
    }:
        raise ContractError("revision-2 preimplementation lock schema changed")
    if (
        prelock["active_contract"] != {
            "base_path": "study_docs/research/ductile-origami-warmstart/protocol/v1/s11-stage1-model-only-factorization-contract.yaml",
            "base_sha256": BASE_SHA256,
            "identity": "ordered_base_plus_revision_2",
            "revision_path": "study_docs/research/ductile-origami-warmstart/protocol/v1/s11-stage1-model-only-factorization-contract-r2.yaml",
            "revision_sha256": REVISION_SHA256,
        }
        or prelock["structural_registry"].get("sha256") != STRUCTURAL_REGISTRY_SHA256
        or prelock["formal_evidence_authorized"] is not False
        or prelock["effective_formal_lock"] != "absent"
    ):
        raise ContractError("revision-2 preimplementation lock parity failure")
    resolved = copy.deepcopy(base)
    for operation in resolution["patch_operations"]:
        _append_unique(resolved, operation["path"], operation["values"])
    resolved["_active_contract"] = {
        "identity": "ordered_base_plus_revision_2",
        "ordered_raw_sha256": list(ORDERED_CONTRACT_HASHES),
        "preimplementation_lock_sha256": PREIMPLEMENTATION_LOCK_SHA256,
    }
    return resolved


def run_readonly_git(
    repository_root: Path | str, *arguments: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    """Run read-only Git commands, including in the container's linked worktree mount."""

    root = Path(repository_root).resolve()
    environment = os.environ.copy()
    # Read-only verification must never hydrate a partial clone or prompt for
    # credentials.  Missing local objects are a verification failure.
    environment["GIT_NO_LAZY_FETCH"] = "1"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["GIT_ASKPASS"] = "/bin/false"
    dot_git = root / ".git"
    temporary_repository: tempfile.TemporaryDirectory[str] | None = None
    if dot_git.is_file():
        marker = dot_git.read_text(encoding="utf-8").strip()
        if marker.startswith("gitdir: "):
            git_dir = Path(marker[8:])
            if not git_dir.is_absolute():
                git_dir = (root / git_dir).resolve()
            if not git_dir.exists() and str(git_dir).startswith("/data1/perlee/"):
                git_dir = Path("/src") / git_dir.relative_to("/data1/perlee")
            common_marker = git_dir / "commondir"
            if common_marker.is_file():
                common_dir = (git_dir / common_marker.read_text(encoding="utf-8").strip()).resolve()
                temporary_repository = tempfile.TemporaryDirectory(
                    prefix="s11-git-read-", dir=os.environ.get("TMPDIR")
                )
                temporary_git = Path(temporary_repository.name)
                (temporary_git / "objects/info").mkdir(parents=True)
                (temporary_git / "objects/pack").mkdir()
                (temporary_git / "refs/heads").mkdir(parents=True)
                (temporary_git / "objects/info/alternates").write_text(
                    str(common_dir / "objects") + "\n", encoding="utf-8"
                )
                (temporary_git / "config").write_text(
                    "[core]\nrepositoryformatversion = 0\nbare = true\n", encoding="utf-8"
                )
                head_value = (git_dir / "HEAD").read_text(encoding="ascii").strip()
                if head_value.startswith("ref: "):
                    ref = head_value[5:]
                    ref_paths = (git_dir / ref, common_dir / ref)
                    resolved_head = next(
                        (path.read_text(encoding="ascii").strip() for path in ref_paths if path.is_file()),
                        None,
                    )
                    if resolved_head is None:
                        packed = common_dir / "packed-refs"
                        if packed.is_file():
                            for line in packed.read_text(encoding="ascii").splitlines():
                                if not line.startswith(("#", "^")) and line.endswith(" " + ref):
                                    resolved_head = line.split(" ", 1)[0]
                                    break
                    if resolved_head is None:
                        raise ContractError("linked-worktree HEAD ref cannot be resolved read-only")
                    head_value = resolved_head
                (temporary_git / "HEAD").write_text(head_value + "\n", encoding="ascii")
                environment["GIT_DIR"] = str(temporary_git)
                environment["GIT_WORK_TREE"] = str(root)
            else:
                environment["GIT_DIR"] = str(git_dir)
                environment["GIT_WORK_TREE"] = str(root)
    try:
        completed = subprocess.run(
            ["git", *arguments], cwd=root, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=environment,
        )
    finally:
        if temporary_repository is not None:
            temporary_repository.cleanup()
    if check and completed.returncode != 0:
        raise ContractError(
            f"git {' '.join(arguments)} failed: "
            + completed.stderr.decode("utf-8", errors="replace")[-500:]
        )
    return completed


def _run_git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return run_readonly_git(REPOSITORY_ROOT, *arguments, check=check)


def _git_blob_sha256(commit: str, path: str) -> str:
    completed = _run_git("show", f"{commit}:{path}")
    return hashlib.sha256(completed.stdout).hexdigest()


def _git_blob_sha256_at(repository_root: Path, commit: str, path: str) -> str:
    completed = run_readonly_git(repository_root, "show", f"{commit}:{path}")
    return hashlib.sha256(completed.stdout).hexdigest()


def validate_implementation_commit_topology(
    repository_root: Path | str, *, implementation_commit: str,
    implementation_parent_commit: str, manifest_relative_path: str,
    implementation_bindings: Sequence[Mapping[str, Any]] | None = None,
    require_clean_head: bool = False,
    approved_parent_commit: str = APPROVED_IMPLEMENTATION_PARENT_COMMIT,
) -> None:
    """Validate the exact P0b -> P1 implementation/manifest commit shape."""

    root = Path(repository_root).resolve()
    if implementation_parent_commit != approved_parent_commit:
        raise ContractError("implementation parent differs from approved P0b")
    for commit, label in (
        (implementation_commit, "implementation"),
        (implementation_parent_commit, "implementation parent"),
    ):
        if (
            run_readonly_git(root, "cat-file", "-t", commit).stdout.strip()
            != b"commit"
        ):
            raise ContractError(f"{label} commit is unavailable")
    parents = run_readonly_git(
        root, "show", "-s", "--format=%P", implementation_commit
    ).stdout.decode("ascii").split()
    if parents != [implementation_parent_commit]:
        raise ContractError("implementation commit must have exactly the sealed parent")
    changed = run_readonly_git(
        root, "diff-tree", "--no-commit-id", "--name-only", "-r",
        implementation_commit,
    ).stdout.decode("utf-8").splitlines()
    expected = sorted([*EXPECTED_IMPLEMENTATION_WHITELIST, manifest_relative_path])
    if sorted(changed) != expected or len(changed) != len(expected):
        raise ContractError("implementation commit diff is not exact 19-plus-manifest")
    if run_readonly_git(
        root, "merge-base", "--is-ancestor", implementation_commit, "HEAD",
        check=False,
    ).returncode != 0:
        raise ContractError("implementation commit is not reachable from HEAD")
    if implementation_bindings is not None:
        if [row.get("path") for row in implementation_bindings] != list(
            EXPECTED_IMPLEMENTATION_WHITELIST
        ):
            raise ContractError("implementation binding path order changed")
        for row in implementation_bindings:
            if (
                type(row) is not dict
                or set(row) != {"path", "sha256"}
                or not _hex_digest(row["sha256"])
                or _git_blob_sha256_at(
                    root, implementation_commit, row["path"]
                )
                != row["sha256"]
            ):
                raise ContractError("implementation binding blob differs from P1")
    if require_clean_head:
        head = run_readonly_git(root, "rev-parse", "HEAD").stdout.decode("ascii").strip()
        if head != implementation_commit:
            raise ContractError("effective lock must be created with HEAD at P1")
        if run_readonly_git(
            root, "status", "--porcelain", "--untracked-files=all"
        ).stdout:
            raise ContractError("P1 worktree must be clean before effective-lock creation")
        working_manifest = root / manifest_relative_path
        committed_manifest = run_readonly_git(
            root, "show", f"{implementation_commit}:{manifest_relative_path}"
        ).stdout
        if working_manifest.read_bytes() != committed_manifest:
            raise ContractError("working implementation manifest differs from committed P1")


def validate_lock_commit_topology(
    repository_root: Path | str, *, implementation_commit: str,
    lock_relative_path: str,
) -> str:
    """Find reachable P2 and require it to be the lock-only child of P1."""

    root = Path(repository_root).resolve()
    descendants = run_readonly_git(
        root, "rev-list", "--ancestry-path", "--reverse",
        f"{implementation_commit}..HEAD",
    ).stdout.decode("ascii").splitlines()
    if not descendants:
        raise ContractError("reachable lock commit P2 is absent")
    lock_commit = descendants[0]
    parents = run_readonly_git(
        root, "show", "-s", "--format=%P", lock_commit
    ).stdout.decode("ascii").split()
    if parents != [implementation_commit]:
        raise ContractError("lock commit must have implementation commit as sole parent")
    changed = run_readonly_git(
        root, "diff-tree", "--no-commit-id", "--name-only", "-r", lock_commit
    ).stdout.decode("utf-8").splitlines()
    if changed != [lock_relative_path]:
        raise ContractError("lock commit must contain exactly the effective lock")
    lock_oid = run_readonly_git(
        root, "rev-parse", f"{lock_commit}:{lock_relative_path}"
    ).stdout.strip()
    head_lock_oid = run_readonly_git(
        root, "rev-parse", f"HEAD:{lock_relative_path}"
    ).stdout.strip()
    if lock_oid != head_lock_oid:
        raise ContractError("effective lock changed after P2")
    return lock_commit


def _approved_scratch_destination(path: Path | str) -> Path:
    target = Path(path).absolute()
    roots = [
        (REPOSITORY_ROOT / row["path"]).resolve()
        for row in strict_load_yaml(DEFAULT_REVISION_PATH)["write_boundary_addendum"]["ignored_descendant_roots"]
    ]
    resolved_parent = target.parent.resolve()
    if not any(resolved_parent == root or root in resolved_parent.parents for root in roots):
        raise ContractError("pinned integration destination is outside approved ignored roots")
    cursor = REPOSITORY_ROOT.resolve()
    try:
        relative = target.relative_to(cursor)
    except ValueError as error:
        raise ContractError("pinned integration destination escapes the repository") from error
    for part in relative.parts:
        cursor /= part
        if cursor.exists() and cursor.is_symlink():
            raise ContractError("pinned integration destination contains a symlink")
    return target


def materialize_pinned_integration(
    destination: Path | str, contract: Mapping[str, Any]
) -> dict[str, Any]:
    """Materialize the exact pinned TensileLite/Origami blobs into ignored scratch."""

    target = _approved_scratch_destination(destination)
    manifest_path = target / "pinned-integration-manifest.json"
    if manifest_path.exists():
        return verify_pinned_integration(target, contract)
    if target.exists() and any(target.iterdir()):
        raise ContractError("pinned integration destination is nonempty and unsealed")
    target.mkdir(parents=True, exist_ok=True)
    source_root = target / "source"
    source_root.mkdir()
    pins = contract["source_pins"]
    commit = pins["ductile_commit"]
    if _run_git("show", "-s", "--format=%T", commit).stdout.decode("ascii").strip() != pins["ductile_commit_tree"]:
        raise ContractError("pinned integration commit tree mismatch")
    if _run_git("rev-parse", f"{commit}:projects/hipblaslt/tensilelite").stdout.decode("ascii").strip() != pins["tensilelite_tree"]:
        raise ContractError("pinned TensileLite subtree mismatch")
    listing = _run_git("ls-tree", "-r", "-z", commit, "--", *PINNED_SOURCE_PREFIXES).stdout
    tree_rows: list[tuple[str, str, str]] = []
    skipped: list[str] = []
    for raw in listing.split(b"\0"):
        if not raw:
            continue
        header, encoded_path = raw.split(b"\t", 1)
        mode, kind, oid = header.decode("ascii").split()
        relative = encoded_path.decode("utf-8")
        if mode == "120000":
            skipped.append(relative)
            continue
        if kind != "blob" or mode not in ("100644", "100755"):
            raise ContractError("pinned integration contains an unsupported tree entry")
        tree_rows.append((mode, oid, relative))
    if tuple(skipped) != PINNED_SKIPPED_SYMLINKS:
        raise ContractError("pinned integration symlink omission set changed")
    archive = _run_git("archive", "--format=tar", commit, *PINNED_SOURCE_PREFIXES).stdout
    entries: list[dict[str, Any]] = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as stream:
        members = {member.name.rstrip("/"): member for member in stream.getmembers()}
        for mode, oid, relative in tree_rows:
            member = members.get(relative)
            if member is None or not member.isfile() or member.issym() or member.islnk():
                raise ContractError(f"pinned archive member is absent/non-regular: {relative}")
            extracted = stream.extractfile(member)
            if extracted is None:
                raise ContractError(f"pinned archive member cannot be read: {relative}")
            payload = extracted.read()
            output = source_root / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as handle:
                handle.write(payload)
            output.chmod(0o755 if mode == "100755" else 0o644)
            entries.append(
                {
                    "path": relative,
                    "git_mode": mode,
                    "git_blob_oid": oid,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
    body = {
        "document_kind": "s11_pinned_integration_materialization",
        "schema_version": 1,
        "checkpoint_id": "S11",
        "commit": commit,
        "commit_tree": pins["ductile_commit_tree"],
        "tensilelite_tree": pins["tensilelite_tree"],
        "source_prefixes": list(PINNED_SOURCE_PREFIXES),
        "skipped_symlinks": list(PINNED_SKIPPED_SYMLINKS),
        "entries": entries,
    }
    exclusive_write_json(manifest_path, {**body, "materialization_sha256": canonical_sha256(body)})
    return verify_pinned_integration(target, contract)


def verify_pinned_integration(
    destination: Path | str, contract: Mapping[str, Any]
) -> dict[str, Any]:
    target = _approved_scratch_destination(destination)
    manifest_path = target / "pinned-integration-manifest.json"
    document = strict_load_json(manifest_path)
    expected = {
        "document_kind", "schema_version", "checkpoint_id", "commit", "commit_tree",
        "tensilelite_tree", "source_prefixes", "skipped_symlinks", "entries",
        "materialization_sha256",
    }
    if type(document) is not dict or set(document) != expected:
        raise ContractError("pinned integration manifest schema changed")
    body = dict(document)
    recorded = body.pop("materialization_sha256")
    pins = contract["source_pins"]
    if (
        canonical_sha256(body) != recorded
        or document["document_kind"] != "s11_pinned_integration_materialization"
        or document["checkpoint_id"] != "S11"
        or document["commit"] != pins["ductile_commit"]
        or document["commit_tree"] != pins["ductile_commit_tree"]
        or document["tensilelite_tree"] != pins["tensilelite_tree"]
        or document["source_prefixes"] != list(PINNED_SOURCE_PREFIXES)
        or document["skipped_symlinks"] != list(PINNED_SKIPPED_SYMLINKS)
    ):
        raise ContractError("pinned integration manifest identity/hash mismatch")
    source_root = target / "source"
    observed_paths: list[str] = []
    for row in document["entries"]:
        if type(row) is not dict or set(row) != {"path", "git_mode", "git_blob_oid", "sha256"}:
            raise ContractError("pinned integration entry schema changed")
        _safe_relative(row["path"])
        path = source_root / row["path"]
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or path.is_symlink()
            or sha256_file(path) != row["sha256"]
            or ("100755" if info.st_mode & stat.S_IXUSR else "100644") != row["git_mode"]
        ):
            raise ContractError(f"pinned integration materialized blob drift: {row['path']}")
        observed_paths.append(row["path"])
    actual_paths = sorted(
        str(path.relative_to(source_root)) for path in source_root.rglob("*") if path.is_file()
    )
    if actual_paths != sorted(observed_paths):
        raise ContractError("pinned integration contains a missing/extra file")
    for binding in pins["ductile_files"]:
        if sha256_file(source_root / binding["path"]) != binding["sha256"]:
            raise ContractError(f"pinned Ductile source hash mismatch: {binding['path']}")
    return {
        **dict(document),
        "manifest_file_sha256": sha256_file(manifest_path),
        "source_root": str(source_root),
    }


def _safe_relative(value: str) -> None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ContractError(f"unsafe contract path: {value}")


def _validate_invariants(contract: Mapping[str, Any]) -> None:
    active = contract["_active_contract"]
    if active["ordered_raw_sha256"] != list(ORDERED_CONTRACT_HASHES):
        raise ContractError("ordered active contract hash binding changed")
    if (
        contract["document_kind"] != "s11_factorization_contract"
        or contract["checkpoint_id"] != "S11"
        or contract["status"] != "frozen_preimplementation"
        or contract["risk_tier"] != "R2"
        or contract["formal_evidence_authorized"] != "only_by_future_effective_lock"
        or contract["positive_criterion"] != "S1_GUIDANCE_LOCKED"
        or contract["sole_positive_edge"] != "S12"
    ):
        raise ContractError("active S11 identity/status/edge changed")
    schedule = contract["schedule"]
    if schedule["chunk_nominal_draws"] != 512 or schedule["global"] != {
        "stream_id": "global", "diagnostic_prefix_accepted": 4096,
        "canonical_prefix_accepted": 8192, "complete_chunks": 65536,
        "complete_nominal_draws": 33554432, "target_stop": "forbidden",
        "early_stop": "forbidden", "extension": "forbidden",
        "later_accepts_after_canonical_prefix": "append_only_zero_credit_diagnostic",
    }:
        raise ContractError("global fixed-cap schedule changed")
    conditional = schedule["conditional"]
    if conditional["complete_chunks_per_activated_value"] != 512 or conditional["complete_nominal_draws_per_activated_value"] != 262144 or conditional["canonical_prefix_accepted"] != 256:
        raise ContractError("conditional fixed-cap schedule changed")
    if schedule["boundary_overshoot_credit"] != 0 or schedule["cap_extension"] != "forbidden":
        raise ContractError("prefix credit/extension law changed")
    statistics = contract["statistics"]
    if (
        statistics["alpha"] != 32 or statistics["epsilon"] != 0.20
        or statistics["permutations"] != 2000 or statistics["bootstraps"] != 2000
        or statistics["reducer"] != "max" or statistics["quantile"] != "hyndman_fan_type_7"
        or statistics["half_stability"]["exact_tuple"][-2:] != ["per_size_and_aggregate_direction", "each_model_test_result"]
        or contract["fixed_frame_analysis"]["semantic_half_tuple"][-2:] != ["per_size_and_aggregate_direction", "each_model_test_result"]
    ):
        raise ContractError("fixed statistics/revision-2 half tuple changed")
    native = contract["native_scoring"]
    if (
        native["problem_sizes"] != [[8, 8, 1, 128], [256, 256, 1, 1024], [2304, 1024, 1, 214336]]
        or native["soo"] is not False or native["actual_reducer"] != "max"
        or native["weight_beta"] != 0.25
    ):
        raise ContractError("locked structural/native frame changed")
    if contract["qualification"]["blocked_mapping"]["allowlist"] != []:
        raise ContractError("blocked-mapping allowlist must remain empty")
    boundaries = contract["write_boundaries"]
    if tuple(boundaries["implementation_whitelist_exact"]) != EXPECTED_IMPLEMENTATION_WHITELIST:
        raise ContractError("exact implementation whitelist changed")
    if boundaries["ownership"]["implementer_exact_paths"] != boundaries["implementation_whitelist_exact"]:
        raise ContractError("implementation ownership/whitelist parity failed")
    for name in ("implementation_whitelist_exact", "execution_whitelist_exact", "delivery_whitelist_union_exact"):
        if len(boundaries[name]) != len(set(boundaries[name])):
            raise ContractError(f"duplicate path in {name}")
        for value in boundaries[name]:
            _safe_relative(value)
    if tuple(contract["formal_commands"]) != FORMAL_COMMANDS:
        raise ContractError("formal command order changed")
    expected_outcomes = [
        "EVIDENCE_INVALID", "CHANGES_REQUIRED", "FT-BLOCKED-MAPPING", "FT-INCONCLUSIVE",
        "S1_GUIDANCE_LOCKED", "COMPLETE_DETERMINISTIC_NO_GUIDANCE",
    ]
    if contract["outcomes"]["ordering"] != expected_outcomes:
        raise ContractError("terminal first-match precedence changed")
    scratch = contract["_active_contract"]
    if scratch["identity"] != "ordered_base_plus_revision_2":
        raise ContractError("active contract identity changed")


def validate_contract(
    contract_path: Path | str = DEFAULT_CONTRACT_PATH,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
    *,
    revision_path: Path | str = DEFAULT_REVISION_PATH,
    preimplementation_lock_path: Path | str = DEFAULT_PREIMPLEMENTATION_LOCK_PATH,
    verify_base_authorities: bool = True,
    verify_hashes: bool = True,
) -> dict[str, Any]:
    contract = load_contract(
        contract_path, revision_path=revision_path,
        preimplementation_lock_path=preimplementation_lock_path,
        verify_hashes=verify_hashes,
    )
    schema = strict_load_json(schema_path)
    instance = {key: value for key, value in contract.items() if key != "_active_contract"}
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(instance), key=lambda item: list(item.path))
    except jsonschema.SchemaError as error:
        raise ContractError(f"S11 schema is invalid: {error.message}") from error
    if errors:
        error = errors[0]
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise ContractError(f"contract schema failure at {pointer}: {error.message}")
    _validate_invariants(contract)
    if verify_base_authorities:
        base_commit = contract["base_commit"]
        if _run_git("cat-file", "-t", base_commit).stdout.strip() != b"commit":
            raise ContractError("base commit is unavailable")
        for binding in contract["authority_bindings"]:
            if _git_blob_sha256(base_commit, binding["path"]) != binding["base_sha256"]:
                raise ContractError(f"base authority hash mismatch: {binding['path']}")
        if sha256_file(REPOSITORY_ROOT / contract["input"]["path"]) != contract["input"]["sha256"]:
            raise ContractError("actual YAML raw hash mismatch")
        structural = strict_load_json(DEFAULT_STRUCTURAL_REGISTRY_PATH)
        from .registry import verify_structural_registry, extract_registry
        verify_structural_registry(structural, repository_root=REPOSITORY_ROOT)
        residual = extract_registry(
            REPOSITORY_ROOT / contract["input"]["path"],
            structural_registry=structural,
        )
        if (
            residual["registry_sha256"] != contract["registry"]["registry_sha256"]
            or len(residual["eligible_genes"]) != contract["registry"]["eligible_gene_count"]
            or len(residual["conditional_streams"]) != contract["registry"]["activated_value_count"]
            or residual["problem_sizes"] != contract["native_scoring"]["problem_sizes"]
        ):
            raise ContractError("residual registry replay does not match the frozen binding")
    return contract


def contract_identity(contract: Mapping[str, Any]) -> str:
    return canonical_sha256(dict(contract))


def _formal_absence_paths(contract: Mapping[str, Any]) -> list[str]:
    paths = list(contract["formal_outcome_paths"])
    paths.append(
        "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/gate-records/s11-s1-guidance-locked.json"
    )
    return sorted(set(paths))


def preflight(
    contract_path: Path | str = DEFAULT_CONTRACT_PATH,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
    *,
    revision_path: Path | str = DEFAULT_REVISION_PATH,
    preimplementation_lock_path: Path | str = DEFAULT_PREIMPLEMENTATION_LOCK_PATH,
) -> dict[str, Any]:
    contract = validate_contract(
        contract_path, schema_path, revision_path=revision_path,
        preimplementation_lock_path=preimplementation_lock_path,
    )
    present = [relative for relative in _formal_absence_paths(contract) if (REPOSITORY_ROOT / relative).exists()]
    if DEFAULT_LOCK_PATH.exists():
        present.append(str(DEFAULT_LOCK_PATH.relative_to(REPOSITORY_ROOT)))
    if present:
        raise ContractError("pre-evidence formal artifact absence failed: " + ", ".join(sorted(set(present))))
    return {
        "checkpoint_id": "S11",
        "status": contract["status"],
        "active_contract_identity": "ordered_base_plus_revision_2",
        "ordered_contract_raw_sha256": list(ORDERED_CONTRACT_HASHES),
        "contract_canonical_sha256": contract_identity(contract),
        "formal_admission_enabled": False,
        "effective_lock_absent": True,
        "formal_outcome_paths_absent": True,
        "structural_registry_verified": True,
    }


def _contains_pending(value: Any) -> bool:
    if value == "required_pending":
        return True
    if type(value) is list:
        return any(_contains_pending(item) for item in value)
    if type(value) is dict:
        return any(_contains_pending(key) or _contains_pending(item) for key, item in value.items())
    return False


def _hex_digest(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _git_commit_hash(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 40
        and all(character in "0123456789abcdef" for character in value)
    )


def _ordinary_bound_file(
    value: Any, expected_hash: str, label: str, *, executable: bool,
    allow_launcher_symlink: bool = False,
) -> Path:
    if type(value) is not str or not Path(value).is_absolute():
        raise ContractError(f"{label} path must be absolute")
    path = Path(value)
    if (path != path.resolve() or path.is_symlink()) and not allow_launcher_symlink:
        raise ContractError(f"{label} path must already be resolved and non-symlink")
    bound = path.resolve()
    info = bound.lstat()
    if not stat.S_ISREG(info.st_mode) or bound.is_symlink() or sha256_file(bound) != expected_hash:
        raise ContractError(f"{label} path/hash/mode mismatch")
    if executable and not os.access(path, os.X_OK):
        raise ContractError(f"{label} is not executable")
    return path


def _approved_bound_directory(value: Any, label: str) -> Path:
    if type(value) is not str or not Path(value).is_absolute():
        raise ContractError(f"{label} path must be absolute")
    path = Path(value)
    if path != path.resolve() or path.is_symlink() or not path.is_dir():
        raise ContractError(f"{label} must be a resolved non-symlink directory")
    approved = [
        (REPOSITORY_ROOT / row["path"]).resolve()
        for row in strict_load_yaml(DEFAULT_REVISION_PATH)["write_boundary_addendum"][
            "ignored_descendant_roots"
        ]
    ]
    if not any(path == root or root in path.parents for root in approved):
        raise ContractError(f"{label} is outside approved ignored scratch")
    return path


def qualification_compiler_argv(compiler_path: Path | str) -> list[str]:
    return [
        str(compiler_path), "-x", "assembler", "--target=amdgcn-amd-amdhsa",
        "-mcode-object-version=4", "-c", "-mcpu=gfx942",
    ]


def expected_qualification_fingerprint(tools: Mapping[str, Any]) -> str:
    projection = {key: tools[key] for key in TOOLCHAIN_KEYS if key != "qualification_fingerprint_sha256"}
    return canonical_sha256(
        {
            "semantic_identity_schema": tools["semantic_identity_schema"],
            "resolver_sha256": tools["resolver_source_sha256"],
            "kernelwriter_sha256": tools["kernelwriter_source_sha256"],
            "compiler_argv": qualification_compiler_argv(tools["compiler_path"]),
            "toolchain_sha256": canonical_sha256(projection),
            "timeout_seconds": tools["qualification_timeout_seconds"],
            "generation_path": "normal_non_proxy_kernelwriter",
        }
    )


def _validate_native_build_provenance(
    build: Mapping[str, Any], tools: Mapping[str, Any], contract: Mapping[str, Any]
) -> None:
    if type(build) is not dict or set(build) != NATIVE_BUILD_PROVENANCE_KEYS:
        raise ContractError("native build provenance schema/unknown-field failure")
    build_body = dict(build)
    recorded_build_hash = build_body.pop("build_sha256")
    if (
        build["document_kind"] != "s11_native_build_execution"
        or build["schema_version"] != 1
        or build["checkpoint_id"] != "S11"
        or not _hex_digest(recorded_build_hash)
        or canonical_sha256(build_body) != recorded_build_hash
    ):
        raise ContractError("native build provenance identity/self-hash failure")
    expected_compile_count = 1 + len(PINNED_ORIGAMI_LINK_SOURCES)
    if type(build["compile_argv"]) is not list or len(build["compile_argv"]) != expected_compile_count:
        raise ContractError("native compile argv set has the wrong exact source closure")
    if type(build["link_argv"]) is not list or not build["link_argv"]:
        raise ContractError("native link argv is absent")
    source_root = Path(build["pinned_source_root"])
    if not source_root.is_absolute() or source_root != source_root.resolve() or source_root.is_symlink():
        raise ContractError("pinned source root must be resolved/non-symlink")
    verified = verify_pinned_integration(source_root.parent, contract)
    if verified["source_root"] != str(source_root) or verified["manifest_file_sha256"] != build["pinned_source_manifest_sha256"]:
        raise ContractError("pinned source materialization/build binding mismatch")
    for name, expected_count in (
        ("generated_headers", 1),
        ("linked_objects", expected_compile_count),
        ("linked_sources", expected_compile_count),
    ):
        rows = build[name]
        if type(rows) is not list or len(rows) != expected_count:
            raise ContractError(f"native {name} count changed")
        for row in rows:
            if type(row) is not dict or set(row) != {"path", "sha256"} or not _hex_digest(row["sha256"]):
                raise ContractError(f"native {name} binding is malformed")
            _ordinary_bound_file(row["path"], row["sha256"], f"native {name}", executable=False)
    expected_sources = [
        str((REPOSITORY_ROOT / contract["toolchain_bindings"]["native_helper_source_path"]).resolve()),
        *(str((source_root / relative).resolve()) for relative in PINNED_ORIGAMI_LINK_SOURCES),
    ]
    if [row["path"] for row in build["linked_sources"]] != expected_sources:
        raise ContractError("native linked source set/order changed")
    compiler = tools["compiler_path"]
    object_paths = [row["path"] for row in build["linked_objects"]]
    rocm_root = next(
        (parent for parent in Path(compiler).resolve().parents
         if (parent / "include/hip/hip_runtime.h").is_file()),
        None,
    )
    if rocm_root is None:
        raise ContractError("bound compiler installation lacks HIP headers")
    from .native_adapter import derive_sealed_execution_argv

    expected_argv = derive_sealed_execution_argv(
        compiler_path=compiler, pinned_source_root=source_root, rocm_root=rocm_root,
        linked_sources=expected_sources, linked_objects=object_paths,
        generated_header=build["generated_headers"][0]["path"],
        helper_path=tools["native_helper_path"],
        qualification_python_path=tools["qualification_python_path"],
        qualification_worker_source_path=(
            REPOSITORY_ROOT / tools["qualification_worker_source_path"]
        ).resolve(),
        qualification_yaml_path=(REPOSITORY_ROOT / contract["input"]["path"]).resolve(),
    )
    if build["compile_argv"] != expected_argv["compile_argv"]:
        raise ContractError("native compile argv exact sequence changed")
    if build["link_argv"] != expected_argv["link_argv"]:
        raise ContractError("native link argv exact sequence changed")
    if tools["qualification_argv"] != expected_argv["qualification_argv"]:
        raise ContractError("qualification process argv exact sequence changed")


def _validate_toolchain(tools: Mapping[str, Any], contract: Mapping[str, Any]) -> None:
    if type(tools) is not dict or set(tools) != set(TOOLCHAIN_KEYS) or _contains_pending(tools):
        raise ContractError("toolchain binding exact schema/pending check failed")
    for key in (
        "validator_adapter_sha256", "validator_source_sha256", "compiler_sha256",
        "qualification_python_sha256", "qualification_worker_source_sha256",
        "native_helper_sha256", "native_helper_source_sha256", "resolver_source_sha256",
        "kernelwriter_source_sha256", "qualification_fingerprint_sha256",
    ):
        if not _hex_digest(tools[key]):
            raise ContractError(f"toolchain digest is malformed: {key}")
    validator = _ordinary_bound_file(
        tools["validator_adapter_path"], tools["validator_adapter_sha256"],
        "validator adapter", executable=True, allow_launcher_symlink=True,
    )
    validator_relative = contract["toolchain_bindings"][
        "qualification_worker_source_path"
    ]
    if tools["validator_source_path"] != validator_relative:
        raise ContractError("validator worker source path binding changed")
    validator_source = REPOSITORY_ROOT / validator_relative
    if sha256_file(validator_source) != tools["validator_source_sha256"]:
        raise ContractError("validator worker source hash mismatch")
    compiler = _ordinary_bound_file(
        tools["compiler_path"], tools["compiler_sha256"], "compiler", executable=True,
        allow_launcher_symlink=True,
    )
    python = _ordinary_bound_file(
        tools["qualification_python_path"], tools["qualification_python_sha256"],
        "qualification Python", executable=True, allow_launcher_symlink=True,
    )
    if (
        validator != python
        or tools["validator_adapter_sha256"]
        != tools["qualification_python_sha256"]
    ):
        raise ContractError("validator/qualification Python launcher binding differs")
    version = subprocess.run(
        [str(compiler), "--version"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
    )
    first_line = version.stdout.decode("utf-8", errors="replace").splitlines()
    if version.returncode != 0 or not first_line or tools["compiler_version"] != first_line[0]:
        raise ContractError("compiler version binding mismatch")
    worker_relative = contract["toolchain_bindings"]["qualification_worker_source_path"]
    native_relative = contract["toolchain_bindings"]["native_helper_source_path"]
    if tools["qualification_worker_source_path"] != worker_relative or tools["native_helper_source_path"] != native_relative:
        raise ContractError("fixed implementation source path binding changed")
    if sha256_file(REPOSITORY_ROOT / worker_relative) != tools["qualification_worker_source_sha256"]:
        raise ContractError("qualification worker source hash mismatch")
    if sha256_file(REPOSITORY_ROOT / native_relative) != tools["native_helper_source_sha256"]:
        raise ContractError("native helper source hash mismatch")
    _ordinary_bound_file(
        tools["native_helper_path"], tools["native_helper_sha256"], "native helper", executable=True
    )
    if tools["semantic_identity_schema"] != contract["toolchain_bindings"]["semantic_identity_schema"]:
        raise ContractError("semantic identity schema binding changed")
    if any(type(tools[key]) is not int or tools[key] <= 0 for key in TIMEOUT_KEYS):
        raise ContractError("toolchain timeout binding is malformed")
    from .sampling import PERSISTENT_VALIDATOR_PROTOCOL, derive_persistent_validator_argv

    if (
        tools["validator_protocol"] != PERSISTENT_VALIDATOR_PROTOCOL
        or type(tools["validator_worker_count"]) is not int
        or not 1 <= tools["validator_worker_count"] <= 64
    ):
        raise ContractError("persistent validator protocol/worker binding changed")
    working_directory = _approved_bound_directory(
        tools["validator_working_directory"], "validator working directory"
    )
    tmpdir = _approved_bound_directory(tools["validator_tmpdir"], "validator TMPDIR")
    pycache = _approved_bound_directory(
        tools["validator_pythonpycacheprefix"], "validator PYTHONPYCACHEPREFIX"
    )
    if working_directory in (tmpdir, pycache) or tmpdir == pycache:
        raise ContractError("validator cwd/TMPDIR/PYTHONPYCACHEPREFIX must be distinct")
    _validate_native_build_provenance(tools["native_build_argv"], tools, contract)
    source_root = Path(tools["native_build_argv"]["pinned_source_root"])
    expected_validator_argv = derive_persistent_validator_argv(
        executable=validator, worker_source_path=validator_source,
        pinned_source_root=source_root,
        actual_yaml_path=REPOSITORY_ROOT / contract["input"]["path"],
        compiler_path=tools["compiler_path"],
    )
    if tools["validator_argv"] != expected_validator_argv:
        raise ContractError("persistent validator argv exact sequence changed")
    if sha256_file(source_root / "projects/hipblaslt/tensilelite/Tensile/backends/ductile_backend.py") != tools["resolver_source_sha256"]:
        raise ContractError("pinned resolver source hash mismatch")
    if sha256_file(source_root / "projects/hipblaslt/tensilelite/Tensile/KernelWriterAssembly.py") != tools["kernelwriter_source_sha256"]:
        raise ContractError("pinned KernelWriter source hash mismatch")
    if tools["qualification_fingerprint_sha256"] != expected_qualification_fingerprint(tools):
        raise ContractError("qualification fingerprint/toolchain projection mismatch")


def _validate_manifest(
    manifest: Mapping[str, Any], contract: Mapping[str, Any], *,
    implementation_commit: str, repository_root: Path = REPOSITORY_ROOT,
) -> None:
    expected = {
        "document_kind", "schema_version", "checkpoint_id",
        "implementation_parent_commit",
        "implementation_bindings", "toolchain_bindings", "timeouts", "scratch_roots",
    }
    if type(manifest) is not dict or set(manifest) != expected:
        raise ContractError("implementation manifest schema/unknown-field failure")
    if (
        manifest["document_kind"] != "s11_implementation_manifest"
        or manifest["schema_version"] != 2
        or manifest["checkpoint_id"] != "S11"
    ):
        raise ContractError("implementation manifest identity changed")
    bindings = manifest["implementation_bindings"]
    if [item.get("path") for item in bindings] != list(EXPECTED_IMPLEMENTATION_WHITELIST):
        raise ContractError("implementation manifest exact path order changed")
    for item in bindings:
        if set(item) != {"path", "sha256"} or not _hex_digest(item["sha256"]):
            raise ContractError("implementation binding is malformed")
        if (
            _git_blob_sha256_at(repository_root, implementation_commit, item["path"])
            != item["sha256"]
        ):
            raise ContractError(f"implementation commit/blob mismatch: {item['path']}")
    if (
        manifest["implementation_parent_commit"]
        != APPROVED_IMPLEMENTATION_PARENT_COMMIT
    ):
        raise ContractError("implementation parent commit differs from approved P0b")
    tools = manifest["toolchain_bindings"]
    _validate_toolchain(tools, contract)
    if (
        type(manifest["timeouts"]) is not dict
        or set(manifest["timeouts"]) != set(TIMEOUT_KEYS)
        or any(manifest["timeouts"][key] != tools[key] for key in TIMEOUT_KEYS)
    ):
        raise ContractError("sealed timeout exact schema/parity failure")
    expected_roots = [row["path"] for row in strict_load_yaml(DEFAULT_REVISION_PATH)["write_boundary_addendum"]["ignored_descendant_roots"]]
    if manifest["scratch_roots"] != expected_roots:
        raise ContractError("exact scratch-root binding changed")


def create_effective_lock(
    output_path: Path | str,
    *,
    implementation_manifest_path: Path | str,
    contract_path: Path | str = DEFAULT_CONTRACT_PATH,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    """Create the future effective lock; never called during pre-evidence engineering."""

    if Path(output_path).resolve() != DEFAULT_LOCK_PATH.resolve():
        raise ContractError("effective lock output path is not the exact contract path")
    if Path(implementation_manifest_path).resolve() != IMPLEMENTATION_MANIFEST_PATH.resolve():
        raise ContractError("implementation manifest path is not the exact contract path")
    contract = validate_contract(contract_path, schema_path)
    preflight(contract_path, schema_path)
    manifest = strict_load_json(implementation_manifest_path)
    manifest_relative = str(IMPLEMENTATION_MANIFEST_PATH.relative_to(REPOSITORY_ROOT))
    implementation_commit = _run_git("rev-parse", "HEAD").stdout.decode("ascii").strip()
    validate_implementation_commit_topology(
        REPOSITORY_ROOT, implementation_commit=implementation_commit,
        implementation_parent_commit=manifest["implementation_parent_commit"],
        manifest_relative_path=manifest_relative,
        implementation_bindings=manifest["implementation_bindings"],
        require_clean_head=True,
    )
    _validate_manifest(
        manifest, contract, implementation_commit=implementation_commit
    )
    manifest_payload = _run_git(
        "show", f"{implementation_commit}:{manifest_relative}"
    ).stdout
    if hashlib.sha256(manifest_payload).hexdigest() != sha256_file(implementation_manifest_path):
        raise ContractError("implementation manifest working bytes are not the committed blob")
    manifest_blob_oid = _run_git(
        "rev-parse", f"{implementation_commit}:{manifest_relative}"
    ).stdout.decode("ascii").strip()
    body = {
        "document_kind": "s11_effective_lock",
        "schema_version": 3,
        "checkpoint_id": "S11",
        "state": "LOCKED_READY",
        "ordered_contract_raw_sha256": list(ORDERED_CONTRACT_HASHES),
        "active_contract_canonical_sha256": contract_identity(contract),
        "preimplementation_lock_sha256": PREIMPLEMENTATION_LOCK_SHA256,
        "structural_registry_sha256": STRUCTURAL_REGISTRY_SHA256,
        "implementation_manifest_sha256": sha256_file(implementation_manifest_path),
        "implementation_manifest_path": manifest_relative,
        "implementation_manifest_commit": implementation_commit,
        "implementation_manifest_blob_oid": manifest_blob_oid,
        "implementation_parent_commit": manifest["implementation_parent_commit"],
        "implementation_commit": implementation_commit,
        "implementation_bindings": manifest["implementation_bindings"],
        "toolchain_bindings": manifest["toolchain_bindings"],
        "timeouts": manifest["timeouts"],
        "seed": contract["seed"],
        "scratch_roots": manifest["scratch_roots"],
        "firewall": contract["firewall"],
        "formal_commands": contract["formal_commands"],
        "formal_outcome_paths": contract["formal_outcome_paths"],
    }
    lock = {**body, "lock_sha256": canonical_sha256(body)}
    exclusive_write_json(output_path, lock)
    return lock


def verify_effective_lock(
    lock_path: Path | str = DEFAULT_LOCK_PATH,
    *,
    contract_path: Path | str = DEFAULT_CONTRACT_PATH,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    contract = validate_contract(contract_path, schema_path)
    lock = strict_load_json(lock_path)
    body = dict(lock)
    recorded = body.pop("lock_sha256", None)
    if canonical_sha256(body) != recorded:
        raise ContractError("effective lock self-hash failure")
    expected_keys = {
        "document_kind", "schema_version", "checkpoint_id", "state",
        "ordered_contract_raw_sha256", "active_contract_canonical_sha256",
        "preimplementation_lock_sha256", "structural_registry_sha256",
        "implementation_manifest_sha256", "implementation_manifest_path",
        "implementation_manifest_commit", "implementation_manifest_blob_oid",
        "implementation_parent_commit", "implementation_commit",
        "implementation_bindings",
        "toolchain_bindings", "timeouts", "seed", "scratch_roots", "firewall",
        "formal_commands", "formal_outcome_paths", "lock_sha256",
    }
    if set(lock) != expected_keys:
        raise ContractError("effective lock schema/unknown-field failure")
    if (
        lock["document_kind"] != "s11_effective_lock" or lock["schema_version"] != 3
        or lock["state"] != "LOCKED_READY" or lock["ordered_contract_raw_sha256"] != list(ORDERED_CONTRACT_HASHES)
        or lock["active_contract_canonical_sha256"] != contract_identity(contract)
        or lock["preimplementation_lock_sha256"] != PREIMPLEMENTATION_LOCK_SHA256
        or lock["structural_registry_sha256"] != STRUCTURAL_REGISTRY_SHA256
        or lock["seed"] != contract["seed"] or lock["firewall"] != contract["firewall"]
        or lock["formal_commands"] != contract["formal_commands"]
        or lock["formal_outcome_paths"] != contract["formal_outcome_paths"]
        or lock["implementation_manifest_commit"] != lock["implementation_commit"]
        or not _git_commit_hash(lock["implementation_parent_commit"])
    ):
        raise ContractError("effective lock/active contract parity failure")
    manifest_relative = str(IMPLEMENTATION_MANIFEST_PATH.relative_to(REPOSITORY_ROOT))
    if lock["implementation_manifest_path"] != manifest_relative:
        raise ContractError("locked implementation manifest path changed")
    manifest_payload = _run_git(
        "show", f"{lock['implementation_manifest_commit']}:{manifest_relative}"
    ).stdout
    if (
        hashlib.sha256(manifest_payload).hexdigest() != lock["implementation_manifest_sha256"]
        or _run_git(
            "rev-parse", f"{lock['implementation_manifest_commit']}:{manifest_relative}"
        ).stdout.decode("ascii").strip() != lock["implementation_manifest_blob_oid"]
    ):
        raise ContractError("locked committed implementation manifest drift")
    manifest = strict_json_loads(manifest_payload)
    if sha256_file(IMPLEMENTATION_MANIFEST_PATH) != lock["implementation_manifest_sha256"]:
        raise ContractError("working implementation manifest differs from committed P1")
    validate_implementation_commit_topology(
        REPOSITORY_ROOT, implementation_commit=lock["implementation_commit"],
        implementation_parent_commit=lock["implementation_parent_commit"],
        manifest_relative_path=manifest_relative,
        implementation_bindings=lock["implementation_bindings"],
    )
    lock_relative = str(DEFAULT_LOCK_PATH.relative_to(REPOSITORY_ROOT))
    lock_commit = validate_lock_commit_topology(
        REPOSITORY_ROOT, implementation_commit=lock["implementation_commit"],
        lock_relative_path=lock_relative,
    )
    committed_lock = _run_git("show", f"{lock_commit}:{lock_relative}").stdout
    if hashlib.sha256(committed_lock).hexdigest() != sha256_file(lock_path):
        raise ContractError("working effective lock differs from committed P2")
    _validate_manifest(
        manifest, contract, implementation_commit=lock["implementation_commit"]
    )
    if (
        manifest["implementation_parent_commit"]
        != lock["implementation_parent_commit"]
        or manifest["implementation_bindings"] != lock["implementation_bindings"]
        or manifest["toolchain_bindings"] != lock["toolchain_bindings"]
        or manifest["timeouts"] != lock["timeouts"]
        or manifest["scratch_roots"] != lock["scratch_roots"]
    ):
        raise ContractError("effective lock/committed implementation manifest parity failure")
    return lock


def admit_formal_command(
    command: str,
    *,
    contract_path: Path | str = DEFAULT_CONTRACT_PATH,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
    lock_path: Path | str = DEFAULT_LOCK_PATH,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if command not in FORMAL_COMMANDS:
        raise ContractError(f"command is not formal-allowlisted: {command}")
    if not Path(lock_path).exists():
        raise ContractError("formal admission disabled: effective lock is absent")
    contract = validate_contract(contract_path, schema_path)
    if command not in contract["formal_commands"]:
        raise ContractError(f"command is not contract-allowlisted: {command}")
    lock = verify_effective_lock(
        lock_path, contract_path=contract_path, schema_path=schema_path
    )
    bound_contract = copy.deepcopy(contract)
    bound_contract["toolchain_bindings"] = copy.deepcopy(lock["toolchain_bindings"])
    return bound_contract, lock
