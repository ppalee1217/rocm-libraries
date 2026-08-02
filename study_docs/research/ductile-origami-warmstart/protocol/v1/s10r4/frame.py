# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Direct, standalone replay of the immutable S10R3 G3 raw discovery frame."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from .contract import (
    REPO_ROOT,
    S10R4Error,
    canonical_json,
    canonical_sha256,
    load_json,
    ordinary_file_records,
    raw_sha256,
    require_exact_keys,
    sha256_bytes,
    validate_document_schema,
)


EXPECTED_PREDECESSOR_HASHES = {
    "study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s10r3-stage1-bounded-cover-entry-lock.json": "2333589fada1df201d233807a8b7cdee10b7554e64cc61b3cc00d352f1b8e352",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r3-candidate-atom-registry.json": "24ae3c4eb0a358f3e9ed6f3f5d2cdeae54bdf151bdb347d68d2ede879613d010",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r3-support-classification.json": "d3477cb6fc616b4ca10f28a4ce8ac798b3432b7116355aec73ca173c4a99a115",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r3-size-registry.json": "353b91a42029a9959d2adc20755cda3d08345a8a14a85e55b8d8c6058ca745a4",
    "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s10r3-decision.json": "c324205db9bb9c1ebc94c806c3e9b95158dd74b466f774f30cf93fab2f6c6aa5",
}

ROW_KEYS = (
    "registry_index",
    "occurrence_id",
    "stream_id",
    "stream_rank",
    "conditional_atom_id_or_null",
    "conditional_priority_rank",
    "chunk_index",
    "draw_index",
    "raw_config",
    "raw_config_canonical_sha256",
    "config_hash",
    "source_child_relative_path",
    "source_child_sha256",
    "source_ledger_event_index",
    "candidate_atom_ids_in_config",
    "candidate_atom_membership_sha256",
)


def verify_predecessor_inputs(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative, expected in EXPECTED_PREDECESSOR_HASHES.items():
        path = repo_root / relative
        digest = raw_sha256(path)
        if digest != expected:
            raise S10R4Error(f"predecessor input hash mismatch: {relative}")
        observed[relative] = digest
    return observed


def _document_digest(document: Mapping[str, Any], field: str) -> str:
    stored = document.get(field)
    if not isinstance(stored, str) or len(stored) != 64:
        raise S10R4Error(f"invalid {field}")
    projected = {key: value for key, value in document.items() if key != field}
    if canonical_sha256(projected) != stored:
        raise S10R4Error(f"{field} mismatch")
    return stored


def _candidate_index(candidate_registry: Mapping[str, Any]) -> dict[tuple[str, bytes], str]:
    rows = candidate_registry.get("rows")
    if not isinstance(rows, list) or candidate_registry.get("row_count") != len(rows):
        raise S10R4Error("candidate registry row count mismatch")
    result: dict[tuple[str, bytes], str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise S10R4Error("candidate registry row is not an object")
        axis_name = row.get("axis_name")
        atom_id = row.get("atom_id")
        if not isinstance(axis_name, str) or not isinstance(atom_id, str):
            raise S10R4Error("candidate registry row identity is malformed")
        key = (axis_name, canonical_json(row.get("typed_value")))
        if key in result:
            raise S10R4Error("candidate registry has duplicate typed axis value")
        result[key] = atom_id
    return result


def _recompute_membership(config: Mapping[str, Any], candidates: Mapping[tuple[str, bytes], str]) -> list[str]:
    atoms: list[str] = []
    for axis_name, value in config.items():
        atom_id = candidates.get((axis_name, canonical_json(value)))
        if atom_id is None:
            raise S10R4Error(f"config value is absent from prelocked candidate registry: {axis_name}")
        atoms.append(atom_id)
    atoms.sort()
    if len(atoms) != 30 or len(set(atoms)) != 30:
        raise S10R4Error("accepted config does not contain exactly one atom from each of 30 axes")
    return atoms


def _load_ledger(raw_root: Path) -> dict[tuple[str, int], int]:
    index = load_json(raw_root / "ledger/ledger-index.json")
    if index.get("checkpoint_id") != "S10R3" or index.get("event_count") != 512:
        raise S10R4Error("predecessor ledger index identity/count mismatch")
    expected_streams = {"global": 32, **{f"conditional-{i:02d}": 32 for i in range(15)}}
    if index.get("per_stream_next_chunk") != expected_streams:
        raise S10R4Error("predecessor ledger schedule mismatch")
    previous = "0" * 64
    association: dict[tuple[str, int], int] = {}
    for event_index in range(512):
        path = raw_root / f"ledger/events/{event_index:012d}.json"
        event = load_json(path)
        if event.get("event_index") != event_index or event.get("previous_event_digest") != previous:
            raise S10R4Error(f"predecessor ledger chain/index mismatch at {event_index}")
        event_digest = _document_digest(event, "event_digest")
        stream_id = event.get("stream_id")
        chunk_index = event.get("chunk_index")
        if stream_id not in expected_streams or not isinstance(chunk_index, int) or not 0 <= chunk_index < 32:
            raise S10R4Error(f"predecessor ledger event association malformed at {event_index}")
        key = (stream_id, chunk_index)
        if key in association:
            raise S10R4Error(f"duplicate predecessor ledger association: {key}")
        association[key] = event_index
        previous = event_digest
    if previous != index.get("last_digest") or len(association) != 512:
        raise S10R4Error("predecessor ledger terminal digest/association mismatch")
    return association


def _chunk_schedule() -> list[tuple[str, int]]:
    return [("global", index) for index in range(32)] + [
        (f"conditional-{priority:02d}", index)
        for priority in range(15)
        for index in range(32)
    ]


def replay_exact_frame(raw_root: Path, *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    raw_root = raw_root.resolve(strict=True)
    verify_predecessor_inputs(repo_root)
    before_identity = os.stat(raw_root, follow_symlinks=False)
    inventory, total_size = ordinary_file_records(raw_root)
    inventory_projection = canonical_sha256(inventory)
    evidence_records = [
        record
        for record in inventory
        if record["relative_path"] not in (".command-writer.lock", "ledger/writer.lock")
    ]
    if len(evidence_records) != 3586:
        raise S10R4Error(f"predecessor raw child record count is {len(evidence_records)}, expected 3586")
    candidate_path = repo_root / next(
        relative for relative in EXPECTED_PREDECESSOR_HASHES if relative.endswith("candidate-atom-registry.json")
    )
    candidate_registry = load_json(candidate_path)
    candidates = _candidate_index(candidate_registry)
    ledger = _load_ledger(raw_root)
    rows: list[dict[str, Any]] = []
    nominal_draws = 0
    for stream_id, chunk_index in _chunk_schedule():
        relative = f"chunks/{stream_id}/{chunk_index:04d}.json"
        path = raw_root / relative
        raw = path.read_bytes()
        chunk = load_json(path)
        if chunk.get("checkpoint_id") != "S10R3" or chunk.get("document_kind") != "support_chunk":
            raise S10R4Error(f"raw chunk identity mismatch: {relative}")
        _document_digest(chunk, "document_digest")
        payload = chunk.get("payload")
        if not isinstance(payload, dict):
            raise S10R4Error(f"raw chunk payload is malformed: {relative}")
        expected_rank = 0 if stream_id == "global" else int(stream_id[-2:]) + 1
        expected_priority = 0 if stream_id == "global" else int(stream_id[-2:])
        if (
            payload.get("stream_id") != stream_id
            or payload.get("stream_rank") != expected_rank
            or payload.get("conditional_priority_rank") != expected_priority
            or payload.get("chunk_index") != chunk_index
            or payload.get("draw_count") != 512
        ):
            raise S10R4Error(f"raw chunk schedule fields mismatch: {relative}")
        atom_id = payload.get("atom_id")
        if (stream_id == "global" and atom_id is not None) or (
            stream_id != "global" and not isinstance(atom_id, str)
        ):
            raise S10R4Error(f"raw chunk conditional atom mismatch: {relative}")
        draws = payload.get("draws")
        if not isinstance(draws, list) or len(draws) != 512:
            raise S10R4Error(f"raw chunk draw completeness mismatch: {relative}")
        nominal_draws += len(draws)
        for expected_draw_index, draw in enumerate(draws):
            if not isinstance(draw, dict) or draw.get("draw_index") != expected_draw_index:
                raise S10R4Error(f"raw draw index mismatch: {relative}:{expected_draw_index}")
            validation = draw.get("validation")
            if not isinstance(validation, dict) or not isinstance(validation.get("accepted"), bool):
                raise S10R4Error(f"raw draw validation is malformed: {relative}:{expected_draw_index}")
            if not validation["accepted"]:
                continue
            config = draw.get("config")
            config_hash = draw.get("config_hash")
            if not isinstance(config, dict) or not isinstance(config_hash, str):
                raise S10R4Error(f"accepted raw draw lacks config identity: {relative}:{expected_draw_index}")
            recalculated_hash = sha256_bytes(canonical_json(config))
            if recalculated_hash != config_hash:
                raise S10R4Error(f"accepted raw config hash mismatch: {relative}:{expected_draw_index}")
            membership = _recompute_membership(config, candidates)
            covered = draw.get("covered_atom_ids")
            if not isinstance(covered, list) or sorted(covered) != membership:
                raise S10R4Error(f"accepted raw membership mismatch: {relative}:{expected_draw_index}")
            rows.append(
                {
                    "registry_index": -1,
                    "occurrence_id": f"{stream_id}:{chunk_index:04d}:{expected_draw_index:04d}",
                    "stream_id": stream_id,
                    "stream_rank": expected_rank,
                    "conditional_atom_id_or_null": atom_id,
                    "conditional_priority_rank": expected_priority,
                    "chunk_index": chunk_index,
                    "draw_index": expected_draw_index,
                    "raw_config": config,
                    "raw_config_canonical_sha256": recalculated_hash,
                    "config_hash": config_hash,
                    "source_child_relative_path": relative,
                    "source_child_sha256": sha256_bytes(raw),
                    "source_ledger_event_index": ledger[(stream_id, chunk_index)],
                    "candidate_atom_ids_in_config": membership,
                    "candidate_atom_membership_sha256": canonical_sha256(membership),
                }
            )
    if nominal_draws != 262_144:
        raise S10R4Error(f"predecessor draw count is {nominal_draws}, expected 262144")
    rows.sort(
        key=lambda row: (
            row["stream_rank"],
            row["conditional_priority_rank"],
            row["chunk_index"],
            row["draw_index"],
            row["config_hash"],
        )
    )
    if len(rows) != 114 or len({row["occurrence_id"] for row in rows}) != 114:
        raise S10R4Error(f"accepted occurrence count is {len(rows)}, expected 114 distinct occurrences")
    if len({row["config_hash"] for row in rows}) != 114:
        raise S10R4Error("accepted config hashes are not exactly 114 distinct values")
    for index, row in enumerate(rows):
        row["registry_index"] = index
        require_exact_keys(row, ROW_KEYS, where=f"exact-frame row {index}")
    after_identity = os.stat(raw_root, follow_symlinks=False)
    if (
        before_identity.st_dev,
        before_identity.st_ino,
        before_identity.st_mtime_ns,
    ) != (after_identity.st_dev, after_identity.st_ino, after_identity.st_mtime_ns):
        raise S10R4Error("predecessor raw root mutated during replay")
    result: dict[str, Any] = {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        "document_kind": "exact_frame_registry",
        "source_checkpoint": "S10R3",
        "source_generation": "S10R3-A46.5-G3",
        "raw_inventory": {
            "root": raw_root.as_posix(),
            "ordinary_file_count": len(inventory),
            "evidence_record_count": len(evidence_records),
            "total_size_bytes": total_size,
            "projection_sha256": inventory_projection,
            "records": inventory,
        },
        "ledger_event_count": 512,
        "raw_child_record_count": len(evidence_records),
        "nominal_draw_count": nominal_draws,
        "accepted_occurrence_count": len(rows),
        "distinct_config_hash_count": len({row["config_hash"] for row in rows}),
        "row_count": len(rows),
        "row_order": [
            "stream_rank",
            "conditional_priority_rank",
            "chunk_index",
            "draw_index",
            "config_hash",
        ],
        "rows": rows,
        "registry_digest": "0" * 64,
    }
    result["registry_digest"] = canonical_sha256(
        {key: value for key, value in result.items() if key != "registry_digest"}
    )
    return result


def validate_exact_frame_registry(document: Mapping[str, Any]) -> None:
    validate_document_schema(document)
    if document.get("document_kind") != "exact_frame_registry" or document.get("checkpoint_id") != "S10R4":
        raise S10R4Error("exact-frame registry identity mismatch")
    if document.get("row_count") != 114 or document.get("accepted_occurrence_count") != 114:
        raise S10R4Error("exact-frame registry does not contain exactly 114 rows")
    rows = document.get("rows")
    if not isinstance(rows, list) or len(rows) != 114:
        raise S10R4Error("exact-frame registry row array mismatch")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise S10R4Error("exact-frame row is not an object")
        require_exact_keys(row, ROW_KEYS, where=f"exact-frame row {index}")
        if row["registry_index"] != index or row["raw_config_canonical_sha256"] != row["config_hash"]:
            raise S10R4Error(f"exact-frame row identity mismatch at {index}")
        if sha256_bytes(canonical_json(row["raw_config"])) != row["config_hash"]:
            raise S10R4Error(f"exact-frame row config digest mismatch at {index}")
        if canonical_sha256(row["candidate_atom_ids_in_config"]) != row["candidate_atom_membership_sha256"]:
            raise S10R4Error(f"exact-frame row membership digest mismatch at {index}")
    if len({row["occurrence_id"] for row in rows}) != 114 or len({row["config_hash"] for row in rows}) != 114:
        raise S10R4Error("exact-frame registry contains duplicates")
    projection = {key: value for key, value in document.items() if key != "registry_digest"}
    if canonical_sha256(projection) != document.get("registry_digest"):
        raise S10R4Error("exact-frame registry self digest mismatch")
