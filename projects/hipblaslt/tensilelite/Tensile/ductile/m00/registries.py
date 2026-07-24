# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Strict shape, baseline, and revision registries with fail-closed guards."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import csv
import re

from .canonical import (
    GuardError,
    load_and_validate,
    load_json_strict,
    sha256_file,
    validate_instance,
)


SHAPE_COLUMNS = (
    "shape_id", "cluster_id", "tile_id", "dtype", "transpose_a",
    "transpose_b", "m", "n", "k", "batch", "cohort", "role",
    "selection_provenance", "source_sha256", "sealed_at",
)
GUIDANCE_ROLES = {"pilot", "development", "development_guidance"}
CANONICAL_SHAPE_FIELDS = (
    "dtype", "transpose_a", "transpose_b", "m", "n", "k", "batch",
)


def _registry_error(message: str, reason: str, criterion: str) -> GuardError:
    return GuardError(message, reason_code=reason, criterion_id=criterion)


class ShapeRegistry:
    def __init__(self, path: str | Path, schema_path: str | Path):
        self.path = Path(path)
        self.schema_path = Path(schema_path)
        self.rows = self._load()
        self.by_id = {row["shape_id"]: row for row in self.rows}

    def _load(self) -> list[dict[str, Any]]:
        try:
            with self.path.open("r", encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream, strict=True)
                if tuple(reader.fieldnames or ()) != SHAPE_COLUMNS:
                    raise ValueError(
                        f"header must exactly equal {','.join(SHAPE_COLUMNS)}"
                    )
                rows = []
                seen = set()
                for line, raw in enumerate(reader, 2):
                    if None in raw or set(raw) != set(SHAPE_COLUMNS):
                        raise ValueError(f"malformed row {line}")
                    if any(value is None for value in raw.values()):
                        raise ValueError(f"missing field on row {line}")
                    row = dict(raw)
                    if not row["shape_id"] or row["shape_id"] in seen:
                        raise ValueError(f"empty or duplicate shape ID on row {line}")
                    seen.add(row["shape_id"])
                    for field in ("m", "n", "k", "batch"):
                        if not re.fullmatch(r"[1-9][0-9]*", row[field]):
                            raise ValueError(
                                f"{field} must be a positive canonical integer "
                                f"on row {line}"
                            )
                        row[field] = int(row[field])
                    rows.append(row)
        except (OSError, csv.Error, ValueError) as exc:
            raise _registry_error(
                f"invalid shape registry {self.path}: {exc}",
                "SHAPE_REGISTRY_INVALID",
                "M00.ACC.SPLIT-GUARD",
            ) from exc
        schema = load_json_strict(self.schema_path)
        try:
            validate_instance(
                {"schema_version": "1.0", "rows": rows},
                schema,
                label=str(self.path),
            )
        except Exception as exc:
            raise _registry_error(
                f"invalid shape registry {self.path}: {exc}",
                "SHAPE_REGISTRY_SCHEMA_INVALID",
                "M00.ACC.SPLIT-GUARD",
            ) from exc
        return rows

    def resolve(self, shape_ids: Iterable[str]) -> list[dict[str, Any]]:
        resolved = []
        for shape_id in shape_ids:
            if shape_id not in self.by_id:
                raise _registry_error(
                    f"shape is not registered: {shape_id}",
                    "SHAPE_NOT_REGISTERED",
                    "M00.ACC.SPLIT-GUARD",
                )
            resolved.append(dict(self.by_id[shape_id]))
        return resolved

    def authorize_guidance(self, shape_ids: Iterable[str],
                           caller_role: str = "development_guidance"):
        if caller_role not in GUIDANCE_ROLES:
            raise _registry_error(
                f"role cannot access guidance payload: {caller_role}",
                "SHAPE_ACCESS_FORBIDDEN",
                "M00.ACC.SPLIT-GUARD",
            )
        rows = self.resolve(shape_ids)
        forbidden = [row["shape_id"] for row in rows
                     if row["role"] == "final_holdout"]
        if forbidden:
            raise _registry_error(
                f"final holdout access forbidden: {forbidden}",
                "FINAL_HOLDOUT_ACCESS",
                "M00.ACC.SPLIT-GUARD",
            )
        return rows

    def assert_disjoint(self, judgment_shape_ids: Iterable[str],
                        holdout_shape_ids: Iterable[str]) -> None:
        judgment = self.resolve(judgment_shape_ids)
        holdout = self.resolve(holdout_shape_ids)
        judgment_ids = {row["shape_id"] for row in judgment}
        holdout_ids = {row["shape_id"] for row in holdout}
        judgment_clusters = {row["cluster_id"] for row in judgment}
        holdout_clusters = {row["cluster_id"] for row in holdout}
        judgment_shapes = {
            tuple(row[field] for field in CANONICAL_SHAPE_FIELDS)
            for row in judgment
        }
        holdout_shapes = {
            tuple(row[field] for field in CANONICAL_SHAPE_FIELDS)
            for row in holdout
        }
        if judgment_ids & holdout_ids:
            raise _registry_error(
                "development judgment and final holdout shape IDs overlap",
                "SHAPE_ID_OVERLAP",
                "M00.ACC.SPLIT-GUARD",
            )
        if judgment_clusters & holdout_clusters:
            raise _registry_error(
                "development judgment and final holdout clusters overlap",
                "CLUSTER_ID_OVERLAP",
                "M00.ACC.SPLIT-GUARD",
            )
        if judgment_shapes & holdout_shapes:
            raise _registry_error(
                "development judgment and final holdout canonical shapes "
                "overlap",
                "CANONICAL_SHAPE_OVERLAP",
                "M00.ACC.SPLIT-GUARD",
            )


def authorize_shape_access(registry: ShapeRegistry,
                           requested_shape_ids: Iterable[str],
                           caller_role: str = "development_guidance",
                           *, comparison_shape_ids: Iterable[str] | None = None):
    rows = registry.authorize_guidance(requested_shape_ids, caller_role)
    if comparison_shape_ids is not None:
        registry.assert_disjoint(requested_shape_ids, comparison_shape_ids)
    return rows


def guarded_load_shape(
        registry: ShapeRegistry,
        shape_id: str, *,
        source_path: str | Path,
        required_role: str,
        loader):
    """Validate registry provenance before allowing any payload loader call."""
    if not callable(loader):
        raise _registry_error(
            "shape loader must be callable",
            "SHAPE_LOADER_INVALID",
            "M00.ACC.SPLIT-GUARD",
        )
    row = registry.resolve([shape_id])[0]
    if row["role"] != required_role:
        raise _registry_error(
            f"shape role mismatch: expected {required_role}, "
            f"got {row['role']}",
            "SHAPE_ROLE_MISMATCH",
            "M00.ACC.SPLIT-GUARD",
        )
    if not row["sealed_at"]:
        raise _registry_error(
            "shape registry entry is not sealed",
            "SHAPE_SEAL_MISSING",
            "M00.ACC.SPLIT-GUARD",
        )
    source = Path(source_path)
    if source.is_symlink() or not source.is_file() or \
            sha256_file(source) != row["source_sha256"]:
        raise _registry_error(
            "shape source hash does not match sealed registry entry",
            "SHAPE_SOURCE_HASH_MISMATCH",
            "M00.ACC.SPLIT-GUARD",
        )
    return loader(dict(row), source)


class BaselineRegistry:
    def __init__(self, path: str | Path, schema_path: str | Path):
        self.path = Path(path)
        self.data = load_and_validate(path, schema_path)
        self.by_id = {
            entry["baseline_id"]: entry for entry in self.data["entries"]
        }
        if len(self.by_id) != len(self.data["entries"]):
            raise _registry_error(
                "duplicate baseline ID",
                "BASELINE_ID_DUPLICATE",
                "M00.ACC.BASELINE-GUARD",
            )

    def resolve(self, baseline_id: str) -> dict[str, Any]:
        if baseline_id not in self.by_id:
            raise _registry_error(
                f"baseline is not registered: {baseline_id}",
                "BASELINE_NOT_REGISTERED",
                "M00.ACC.BASELINE-GUARD",
            )
        return dict(self.by_id[baseline_id])


class RevisionRegistry:
    def __init__(self, path: str | Path, schema_path: str | Path,
                 repo_root: str | Path | None = None):
        self.path = Path(path)
        self.data = load_and_validate(path, schema_path)
        ids = [entry["revision_id"] for entry in self.data["entries"]]
        if len(ids) != len(set(ids)):
            raise _registry_error(
                "duplicate revision ID",
                "REVISION_ID_DUPLICATE",
                "M00.ACC.CONTRACT-LOCK",
            )
        if repo_root is not None:
            self._verify_materialized(Path(repo_root))

    def _verify_materialized(self, repo_root: Path) -> None:
        imported = [
            entry for entry in self.data["entries"]
            if entry["kind"] == "imported_blob"
        ]
        if len(imported) != 15:
            raise _registry_error(
                "revision registry must contain exactly 15 imported blobs",
                "REVISION_BLOB_SET_INVALID",
                "M00.ACC.CONTRACT-LOCK",
            )
        for entry in imported:
            path = repo_root / entry["path"]
            if path.is_symlink() or not path.is_file() or \
                    sha256_file(path) != entry["materialized_sha256"]:
                raise _registry_error(
                    f"materialized revision hash mismatch: {entry['path']}",
                    "REVISION_MATERIALIZED_HASH_MISMATCH",
                    "M00.ACC.CONTRACT-LOCK",
                )
        from .contract import digest_path_set
        whitelist = load_json_strict(
            self.path.parent / "m00-whitelist.json"
        )
        actual = digest_path_set(repo_root, whitelist["source_set_paths"])
        if actual != self.data["m00_source_set"]["sha256"] or \
                len(whitelist["source_set_paths"]) != \
                self.data["m00_source_set"]["path_count"]:
            raise _registry_error(
                "M00 source-set digest differs from revision registry",
                "REVISION_SOURCE_SET_MISMATCH",
                "M00.ACC.CONTRACT-LOCK",
            )


def _contained_evidence(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise _registry_error(
            f"baseline evidence path escapes root: {relative}",
            "BASELINE_PATH_ESCAPE",
            "M00.ACC.BASELINE-GUARD",
        )
    path = root / rel
    if path.is_symlink() or not path.is_file() or \
            not path.resolve().is_relative_to(root.resolve()):
        raise _registry_error(
            f"baseline evidence artifact missing: {relative}",
            "BASELINE_EVIDENCE_MISSING",
            "M00.ACC.BASELINE-GUARD",
        )
    return path


def render_baseline_claim(
        registry: BaselineRegistry,
        baseline_id: str,
        claim_scope: str,
        *,
        artifact_root: str | Path,
        protocol_lock_sha256: str,
        requested_wording: str | None = None) -> str:
    entry = registry.resolve(baseline_id)
    if claim_scope not in entry["allowed_claim_scope"]:
        raise _registry_error(
            f"baseline claim scope is not allowed: {claim_scope}",
            "BASELINE_SCOPE_FORBIDDEN",
            "M00.ACC.BASELINE-GUARD",
        )
    if entry["protocol_lock_sha256"] != protocol_lock_sha256:
        raise _registry_error(
            "baseline protocol-lock hash mismatch",
            "BASELINE_LOCK_MISMATCH",
            "M00.ACC.BASELINE-GUARD",
        )
    if requested_wording is not None:
        raise _registry_error(
            "caller-supplied baseline wording is forbidden",
            "BASELINE_WORDING_FORBIDDEN",
            "M00.ACC.BASELINE-GUARD",
        )

    root = Path(artifact_root)
    for evidence in entry["evidence_artifacts"]:
        artifact = _contained_evidence(root, evidence["path"])
        if sha256_file(artifact) != evidence["sha256"]:
            raise _registry_error(
                f"baseline artifact checksum mismatch: {evidence['path']}",
                "BASELINE_EVIDENCE_HASH_MISMATCH",
                "M00.ACC.BASELINE-GUARD",
            )

    source_kind = entry["source_kind"]
    if source_kind == "original_tuningdriver":
        owner = entry.get("owner_attestation")
        if not owner:
            raise _registry_error(
                "original baseline requires owner attestation",
                "ORIGINAL_OWNER_ATTESTATION_MISSING",
                "M00.ACC.BASELINE-GUARD",
            )
        owner_path = _contained_evidence(root, owner["path"])
        if sha256_file(owner_path) != owner["sha256"]:
            raise _registry_error(
                "owner attestation checksum mismatch",
                "ORIGINAL_OWNER_ATTESTATION_MISMATCH",
                "M00.ACC.BASELINE-GUARD",
            )
        by_type = {
            evidence["evidence_type"]: evidence
            for evidence in entry["evidence_artifacts"]
        }
        if len(entry["evidence_artifacts"]) != 2 or set(by_type) != {
                "tuningdriver_artifact", "tuningdriver_manifest"}:
            raise _registry_error(
                "original baseline requires typed TuningDriver artifact "
                "and manifest evidence",
                "ORIGINAL_EVIDENCE_TYPE_INVALID",
                "M00.ACC.BASELINE-GUARD",
            )
        artifact_evidence = by_type["tuningdriver_artifact"]
        manifest_evidence = by_type["tuningdriver_manifest"]
        manifest_path = _contained_evidence(
            root, manifest_evidence["path"]
        )
        manifest = load_json_strict(manifest_path)
        manifest_fields = {
            "schema_version", "evidence_type", "baseline_id",
            "generator_revision", "fork_params_sha256", "weights_sha256",
            "artifact_sha256", "protocol_lock_sha256",
            "allowed_claim_scope",
        }
        if not isinstance(manifest, dict) or \
                set(manifest) != manifest_fields or \
                manifest["schema_version"] != "1.0" or \
                manifest["evidence_type"] != "tuningdriver" or \
                manifest["baseline_id"] != entry["baseline_id"] or \
                manifest["generator_revision"] != \
                entry["generator_revision"] or \
                manifest["fork_params_sha256"] != \
                entry["fork_params_sha256"] or \
                manifest["weights_sha256"] != entry["weights_sha256"] or \
                manifest["artifact_sha256"] != \
                artifact_evidence["sha256"] or \
                manifest["protocol_lock_sha256"] != \
                protocol_lock_sha256 or \
                manifest["allowed_claim_scope"] != \
                entry["allowed_claim_scope"]:
            raise _registry_error(
                "TuningDriver manifest provenance is incomplete or "
                "mismatched",
                "ORIGINAL_MANIFEST_MISMATCH",
                "M00.ACC.BASELINE-GUARD",
            )
        owner_document = load_json_strict(owner_path)
        owner_fields = {
            "schema_version", "attestation_type", "owner", "issued_at",
            "baseline_id", "generator_revision", "fork_params_sha256",
            "weights_sha256", "artifact_sha256",
            "generator_manifest_sha256", "protocol_lock_sha256",
            "allowed_claim_scope",
        }
        if not isinstance(owner_document, dict) or \
                set(owner_document) != owner_fields or \
                owner_document["schema_version"] != "1.0" or \
                owner_document["attestation_type"] != \
                "tuningdriver-owner" or \
                not owner_document["owner"] or \
                not re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
                    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
                    owner_document["issued_at"],
                ) or \
                owner_document["baseline_id"] != entry["baseline_id"] or \
                owner_document["generator_revision"] != \
                entry["generator_revision"] or \
                owner_document["fork_params_sha256"] != \
                entry["fork_params_sha256"] or \
                owner_document["weights_sha256"] != \
                entry["weights_sha256"] or \
                owner_document["artifact_sha256"] != \
                artifact_evidence["sha256"] or \
                owner_document["generator_manifest_sha256"] != \
                manifest_evidence["sha256"] or \
                owner_document["protocol_lock_sha256"] != \
                protocol_lock_sha256 or \
                owner_document["allowed_claim_scope"] != \
                entry["allowed_claim_scope"]:
            raise _registry_error(
                "owner attestation does not bind complete TuningDriver "
                "provenance",
                "ORIGINAL_OWNER_BINDING_MISMATCH",
                "M00.ACC.BASELINE-GUARD",
            )
        if entry["claim_template_id"] != "original-tuningdriver-v1":
            raise _registry_error(
                "invalid original baseline claim template",
                "ORIGINAL_TEMPLATE_INVALID",
                "M00.ACC.BASELINE-GUARD",
            )
        return (
            f"Original TuningDriver baseline '{baseline_id}' with generator "
            f"revision {entry['generator_revision']} and owner-attested "
            f"evidence; claim scope: {claim_scope}."
        )

    if source_kind == "geko_gfx942_proxy":
        if entry.get("owner_attestation") is not None or \
                entry["claim_template_id"] != "geko-proxy-v1":
            raise _registry_error(
                "invalid proxy baseline provenance",
                "PROXY_PROVENANCE_INVALID",
                "M00.ACC.BASELINE-GUARD",
            )
        return (
            f"GEKO gfx942 proxy baseline '{baseline_id}' with generator "
            f"revision {entry['generator_revision']}; claim scope: "
            f"{claim_scope}. This is proxy evidence and is not an original "
            "TuningDriver baseline."
        )

    raise _registry_error(
        f"unknown baseline source kind: {source_kind}",
        "BASELINE_SOURCE_KIND_INVALID",
        "M00.ACC.BASELINE-GUARD",
    )
