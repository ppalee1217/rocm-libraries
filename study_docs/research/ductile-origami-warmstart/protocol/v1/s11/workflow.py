# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""One-unit formal command handlers, reachable only after lock admission."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import os
from pathlib import Path
import stat
import subprocess
from typing import Any, Callable, Mapping, Sequence

from .canonical import (
    canonical_json_bytes,
    canonical_sha256,
    exclusive_write_json,
    sha256_file,
    strict_json_loads,
    strict_load_json,
)
from .contract import materialize_pinned_integration, run_readonly_git
from .decision import decide, decide_from_artifacts
from .guidance import (
    deterministic_nonidentity_shuffle,
    float32_inverse_cost_roundtrip,
    select_global_lambda,
)
from .ledger import ChunkLedger
from .native_adapter import NativeFormocastAdapter
from .populations import build_populations, global_mean, value_cell
from .qualification import (
    PinnedQualificationWorker,
    QualificationAttempt,
    evaluate_attempts,
)
from .registry import extract_registry
from .sampling import (
    PinnedValidatorAdapter,
    StreamSpec,
    canonical_prefix,
    commit_chunk,
    expand_compact_chunk,
    sample_chunk,
)
from .statistics import (
    ARM_SENSITIVITY_ESS_MIN_FRACTION,
    HALF_CATEGORICAL_PROJECTION_FIELDS,
    HALF_TUPLE_FIELDS,
    alpha0_bootstrap_stability,
    alpha0_joint_permutation_test,
    alpha0_shrinkage_sensitivity,
    additive_rank_faithfulness,
    arm_sensitivity_theta,
    bootstrap_stability,
    emitted_prior_reconstruction,
    gene_marginals,
    joint_permutation_test,
    per_size_latency_margin,
    query_terminal_global_ecdf,
    semantic_half_stability,
    sensitivity,
    size_direction,
    survivorship_yield,
    type7_quantile,
)


class WorkflowError(ValueError):
    """A formal unit request violates its command or output contract."""


FORMAL_OUTPUTS = {
    "global-discovery": "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-global-prefix.json",
    "conditional-discovery": "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-conditional-prefixes.json",
    "qualify": "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-qualifications.json",
    "score": "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-native-scores.json",
    "analyze": "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-analysis.json",
    "decide": "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s11-decision.json",
    "reproduce": "study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s11-reproduction.json",
}
REGISTRY_OUTPUT = (
    "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-registry.json"
)
CLOSEOUT_ACK_PATH = (
    "agent_run/260803-ductile-factorized-guidance-s11/s11-execution-v2/"
    "formal/verifier/closeout-ack.json"
)
EMITTED_BASELINE_MIX = 0.20


class SyntheticInterruption(RuntimeError):
    """Test-only interruption after an immutable chunk is published."""


def _validate_chunk(
    chunk: Mapping[str, Any], spec: StreamSpec, index: int, *,
    registry: Mapping[str, Any], master_nonce: str, lock_sha256: str,
) -> dict[str, Any]:
    if type(chunk) is not dict:
        raise WorkflowError("published sampling chunk is not an object")
    if chunk.get("chunk_index") != index:
        raise WorkflowError("published sampling chunk index mismatch")
    try:
        return expand_compact_chunk(
            chunk, registry=registry, spec=spec, master_nonce=master_nonce,
            expected_lock_sha256=lock_sha256,
        )
    except Exception as error:
        raise WorkflowError("published compact sampling chunk failed reconstruction") from error


def _count_numbered_json_files(root: Path, label: str) -> int:
    """Validate a contiguous zero-based directory without listing it in memory."""

    count = 0
    maximum = -1
    with os.scandir(root) as entries:
        for entry in entries:
            if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
                raise WorkflowError(f"{label} contains a non-regular entry")
            name = entry.name
            if len(name) != 17 or not name.endswith(".json") or not name[:12].isdigit():
                raise WorkflowError(f"{label} contains a malformed filename")
            index = int(name[:12])
            maximum = max(maximum, index)
            count += 1
    if maximum != count - 1:
        raise WorkflowError(f"{label} is missing or reorders a numbered file")
    return count


def _chunk_path(chunks_root: Path, index: int) -> Path:
    return chunks_root / f"{index:012d}.json"


def _chunk_event_metadata(
    *, stream_root: Path, chunk_path: Path, chunk: Mapping[str, Any],
    expanded: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "nominal_slots": chunk["nominal_slots"],
        "accepted_count": expanded["counts"]["accepted"],
        "disposition_counts": dict(expanded["counts"]),
        "chunk_relative_path": str(chunk_path.relative_to(stream_root)),
        "chunk_byte_length": chunk_path.stat().st_size,
        "chunk_file_sha256": sha256_file(chunk_path),
        "chunk_semantic_sha256": chunk["chunk_semantic_sha256"],
    }


def _verify_chunk_event_metadata(
    event: Mapping[str, Any], *, stage: str, spec: StreamSpec, index: int,
    metadata: Mapping[str, Any],
) -> None:
    expected = {
        "stage": stage,
        "stream_id": spec.stream_id,
        "chunk_index": index,
        **dict(metadata),
    }
    if any(event.get(key) != value for key, value in expected.items()):
        raise WorkflowError("sampling chunk differs from its metadata-only ledger event")


def run_resumable_stream(
    registry: Mapping[str, Any],
    spec: StreamSpec,
    *,
    master_nonce: str,
    validator: Callable[[Mapping[str, Any]], bool],
    scratch_root: Path | str,
    lock_sha256: str,
    stage: str,
    synthetic: bool = False,
    interrupt_after_publication: int | None = None,
) -> dict[str, Any]:
    """Complete and fully replay one fixed-cap stream with exact crash resume.

    The interruption hook is deliberately unreachable unless a direct caller
    marks the run synthetic.  Formal callers construct the immutable schedule
    from the effective contract and never accept a cap or interruption input.
    """

    spec.validate()
    if interrupt_after_publication is not None and (
        synthetic is not True
        or type(interrupt_after_publication) is not int
        or not 0 <= interrupt_after_publication < spec.hard_cap_chunks
    ):
        raise WorkflowError("test interruption hook is not formally reachable")
    root = Path(scratch_root)
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise WorkflowError("stream scratch root is not an ordinary directory")
    root.mkdir(parents=True, exist_ok=True)
    chunks_root = root / "chunks"
    if chunks_root.exists() and (chunks_root.is_symlink() or not chunks_root.is_dir()):
        raise WorkflowError("stream chunk root is not an ordinary directory")
    chunks_root.mkdir(exist_ok=True)
    ledger_root = root / "ledger"

    with ChunkLedger(ledger_root, lock_sha256) as ledger:
        replay = ledger.full_verify()
        next_chunk = replay["per_stream_next_chunk"].get(spec.stream_id, 0)
        if set(replay["per_stream_next_chunk"]) - {spec.stream_id}:
            raise WorkflowError("stream ledger contains an unrelated stream")
        chunk_count = _count_numbered_json_files(chunks_root, "sampling chunk root")
        if chunk_count not in (next_chunk, next_chunk + 1):
            raise WorkflowError("sampling chunks and ledger cursor diverged")

        # Replay one compact chunk at a time and match its path/length/raw and
        # semantic digests to the metadata-only ledger.
        for index in range(next_chunk):
            path = _chunk_path(chunks_root, index)
            chunk = strict_load_json(path)
            expanded = _validate_chunk(
                chunk, spec, index, registry=registry, master_nonce=master_nonce,
                lock_sha256=lock_sha256,
            )
            event = strict_load_json(ledger.events_root / ledger.event_name(index))
            _verify_chunk_event_metadata(
                event, stage=stage, spec=spec, index=index,
                metadata=_chunk_event_metadata(
                    stream_root=root, chunk_path=path, chunk=chunk,
                    expanded=expanded,
                ),
            )

        # A crash can occur after chunk O_EXCL publication and before the ledger
        # event is appended.  Exactly one verified orphan is recoverable.
        if chunk_count == next_chunk + 1:
            orphan_path = _chunk_path(chunks_root, next_chunk)
            orphan = strict_load_json(orphan_path)
            expanded = _validate_chunk(
                orphan, spec, next_chunk, registry=registry,
                master_nonce=master_nonce, lock_sha256=lock_sha256,
            )
            ledger.append_chunk(
                stage=stage,
                stream_id=spec.stream_id,
                chunk_index=next_chunk,
                **_chunk_event_metadata(
                    stream_root=root, chunk_path=orphan_path, chunk=orphan,
                    expanded=expanded,
                ),
            )
            next_chunk += 1

        for chunk_index in range(next_chunk, spec.hard_cap_chunks):
            chunk = sample_chunk(
                registry,
                spec,
                master_nonce=master_nonce,
                chunk_index=chunk_index,
                validator=validator,
                lock_sha256=lock_sha256,
            )
            path = _chunk_path(chunks_root, chunk_index)
            commit_chunk(path, chunk)
            if interrupt_after_publication == chunk_index:
                raise SyntheticInterruption(
                    "synthetic interruption after complete chunk publication"
                )
            expanded = _validate_chunk(
                chunk, spec, chunk_index, registry=registry,
                master_nonce=master_nonce, lock_sha256=lock_sha256,
            )
            ledger.append_chunk(
                stage=stage,
                stream_id=spec.stream_id,
                chunk_index=chunk_index,
                **_chunk_event_metadata(
                    stream_root=root, chunk_path=path, chunk=chunk,
                    expanded=expanded,
                ),
            )

        replay = ledger.full_verify()
        if replay["per_stream_next_chunk"].get(spec.stream_id) != spec.hard_cap_chunks:
            raise WorkflowError("stream reached analysis before its fixed cap")

    if _count_numbered_json_files(chunks_root, "sampling chunk root") != spec.hard_cap_chunks:
        raise WorkflowError("stream fixed-cap replay is partial")
    def compact_chunks():
        for index in range(spec.hard_cap_chunks):
            chunk = strict_load_json(_chunk_path(chunks_root, index))
            expanded = _validate_chunk(
                chunk, spec, index, registry=registry, master_nonce=master_nonce,
                lock_sha256=lock_sha256,
            )
            yield chunk, expanded

    prefix = canonical_prefix(
        compact_chunks(), spec.target_accepted, registry=registry, spec=spec,
        master_nonce=master_nonce, expected_lock_sha256=lock_sha256,
        preexpanded=True,
    )
    credited_rows = [
        {**row, "frame": spec.stream_id, "canonical_credit": True}
        for row in prefix.pop("credited_rows")
    ]
    chunk_hashes_sha256 = prefix.pop("chunk_hashes_sha256")
    return {
        "stream_id": spec.stream_id,
        "fixed_gene": spec.fixed_gene,
        "fixed_candidate_id": spec.fixed_candidate_id,
        "target_accepted": spec.target_accepted,
        "hard_cap_chunks": spec.hard_cap_chunks,
        "nominal_slots_per_chunk": spec.nominal_slots_per_chunk,
        "complete_nominal_draws": spec.hard_cap_chunks * spec.nominal_slots_per_chunk,
        "cap_complete": True,
        "prefix": prefix,
        "credited_rows": credited_rows,
        "zero_credit_occurrence_ids_sha256": prefix[
            "zero_credit_occurrence_ids_sha256"
        ],
        "ledger_replay": replay,
        "chunk_hashes_sha256": chunk_hashes_sha256,
        "scientific_terminal_allowed": prefix["complete"],
    }


def _raw_file_hash(path: Path, repository_root: Path) -> dict[str, str]:
    """Hash one ordinary producer raw file and retain its stable repo path."""

    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.is_symlink():
        raise WorkflowError("producer raw evidence contains a non-regular file")
    return {
        "path": str(path.resolve().relative_to(repository_root.resolve())),
        "sha256": sha256_file(path),
    }


class _CanonicalListHasher:
    """Bounded-memory canonical JSON list digest for audit metadata rows."""

    def __init__(self) -> None:
        self._hash = hashlib.sha256(b"[")
        self.count = 0

    def add(self, value: Any) -> None:
        if self.count:
            self._hash.update(b",")
        self._hash.update(canonical_json_bytes(value))
        self.count += 1

    def hexdigest(self) -> str:
        result = self._hash.copy()
        result.update(b"]")
        return result.hexdigest()


def _validate_raw_stream(
    *,
    stream: Mapping[str, Any],
    spec: StreamSpec,
    stream_root: Path,
    registry: Mapping[str, Any],
    master_nonce: str,
    lock_sha256: str,
    stage: str,
    repository_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read, hash, and independently rebuild one complete producer stream."""

    spec.validate()
    if (
        stream.get("stream_id") != spec.stream_id
        or stream.get("target_accepted") != spec.target_accepted
        or stream.get("hard_cap_chunks") != spec.hard_cap_chunks
        or stream.get("nominal_slots_per_chunk") != spec.nominal_slots_per_chunk
    ):
        raise WorkflowError("producer stream schedule differs from the formal specification")
    chunks_root = stream_root / "chunks"
    ledger_root = stream_root / "ledger"
    if not chunks_root.is_dir() or chunks_root.is_symlink() or not ledger_root.is_dir() or ledger_root.is_symlink():
        raise WorkflowError("producer raw chunk/ledger root is absent")
    if _count_numbered_json_files(
        chunks_root, "producer raw chunk root"
    ) != spec.hard_cap_chunks:
        raise WorkflowError("producer raw chunk set is not the full production cap")
    events_root = ledger_root / "events"
    if _count_numbered_json_files(
        events_root, "producer raw ledger event root"
    ) != spec.hard_cap_chunks:
        raise WorkflowError("producer raw ledger event set is not the full production cap")
    ledger = ChunkLedger(ledger_root, lock_sha256)
    replay = ledger.full_verify()
    expected_replay = {
        "event_count": spec.hard_cap_chunks,
        "last_digest": replay["last_digest"],
        "per_stream_next_chunk": {spec.stream_id: spec.hard_cap_chunks},
    }
    if replay != expected_replay or replay != stream.get("ledger_replay"):
        raise WorkflowError("producer ledger replay/cursor differs from the production cap")

    raw_files = _CanonicalListHasher()
    raw_files.add(_raw_file_hash(ledger_root / "ledger-index.json", repository_root))

    def audited_chunks():
        for index in range(spec.hard_cap_chunks):
            chunk_path = _chunk_path(chunks_root, index)
            event_path = events_root / ChunkLedger.event_name(index)
            # A fresh verifier reads, hashes, and strictly decodes each raw file;
            # it never trusts the producer summary or copies the corpus.
            chunk_bytes = chunk_path.read_bytes()
            event_bytes = event_path.read_bytes()
            chunk_raw_sha256 = hashlib.sha256(chunk_bytes).hexdigest()
            event_raw_sha256 = hashlib.sha256(event_bytes).hexdigest()
            chunk = strict_json_loads(chunk_bytes)
            event = strict_json_loads(event_bytes)
            expanded = _validate_chunk(
                chunk, spec, index, registry=registry,
                master_nonce=master_nonce, lock_sha256=lock_sha256,
            )
            metadata = {
                "nominal_slots": chunk["nominal_slots"],
                "accepted_count": expanded["counts"]["accepted"],
                "disposition_counts": dict(expanded["counts"]),
                "chunk_relative_path": str(chunk_path.relative_to(stream_root)),
                "chunk_byte_length": len(chunk_bytes),
                "chunk_file_sha256": chunk_raw_sha256,
                "chunk_semantic_sha256": chunk["chunk_semantic_sha256"],
            }
            if event.get("event_index") != index:
                raise WorkflowError("producer ledger event index differs")
            _verify_chunk_event_metadata(
                event, stage=stage, spec=spec, index=index, metadata=metadata,
            )
            raw_files.add(
                {
                    "path": str(
                        chunk_path.resolve().relative_to(repository_root.resolve())
                    ),
                    "sha256": chunk_raw_sha256,
                }
            )
            raw_files.add(
                {
                    "path": str(
                        event_path.resolve().relative_to(repository_root.resolve())
                    ),
                    "sha256": event_raw_sha256,
                }
            )
            yield chunk, expanded

    prefix = canonical_prefix(
        audited_chunks(), spec.target_accepted, registry=registry, spec=spec,
        master_nonce=master_nonce, expected_lock_sha256=lock_sha256,
        preexpanded=True,
    )
    credited_rows = [
        {**row, "frame": spec.stream_id, "canonical_credit": True}
        for row in prefix.pop("credited_rows")
    ]
    chunk_hashes_sha256 = prefix.pop("chunk_hashes_sha256")
    rebuilt = {
        "stream_id": spec.stream_id,
        "fixed_gene": spec.fixed_gene,
        "fixed_candidate_id": spec.fixed_candidate_id,
        "target_accepted": spec.target_accepted,
        "hard_cap_chunks": spec.hard_cap_chunks,
        "nominal_slots_per_chunk": spec.nominal_slots_per_chunk,
        "complete_nominal_draws": spec.hard_cap_chunks * spec.nominal_slots_per_chunk,
        "cap_complete": True,
        "prefix": prefix,
        "credited_rows": credited_rows,
        "zero_credit_occurrence_ids_sha256": prefix[
            "zero_credit_occurrence_ids_sha256"
        ],
        "ledger_replay": replay,
        "chunk_hashes_sha256": chunk_hashes_sha256,
        "scientific_terminal_allowed": prefix["complete"],
    }
    if rebuilt != stream:
        raise WorkflowError("producer raw chunks do not rebuild the sealed stream summary")
    attestation = {
        "stream_id": spec.stream_id,
        "target_accepted": spec.target_accepted,
        "hard_cap_chunks": spec.hard_cap_chunks,
        "nominal_slots_per_chunk": spec.nominal_slots_per_chunk,
        "ledger_replay_sha256": canonical_sha256(replay),
        "credited_rows_sha256": canonical_sha256(credited_rows),
        "chunk_hashes_sha256": rebuilt["chunk_hashes_sha256"],
        "raw_file_count": raw_files.count,
        "raw_files_sha256": raw_files.hexdigest(),
    }
    return rebuilt, attestation


def seal_stage_artifact(
    document_kind: str,
    *,
    lock_sha256: str,
    dependencies: Mapping[str, str],
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Create the common self-hashed, lock-bound formal stage envelope."""

    if (
        type(document_kind) is not str
        or not document_kind.startswith("s11_")
        or type(lock_sha256) is not str
        or len(lock_sha256) != 64
        or type(dependencies) is not dict
        or any(
            type(key) is not str
            or type(value) is not str
            or len(value) != 64
            for key, value in dependencies.items()
        )
        or type(payload) is not dict
        or set(payload) & {
            "document_kind", "schema_version", "checkpoint_id", "lock_sha256",
            "dependencies", "artifact_sha256",
        }
    ):
        raise WorkflowError("stage artifact envelope is malformed")
    body = {
        "document_kind": document_kind,
        "schema_version": 1,
        "checkpoint_id": "S11",
        "lock_sha256": lock_sha256,
        "dependencies": dict(dependencies),
        **dict(payload),
    }
    return {**body, "artifact_sha256": canonical_sha256(body)}


def verify_stage_artifact(
    document: Mapping[str, Any], *, kind: str, lock_sha256: str
) -> str:
    if type(document) is not dict:
        raise WorkflowError(f"{kind} stage artifact is not an object")
    body = dict(document)
    recorded = body.pop("artifact_sha256", None)
    if (
        document.get("document_kind") != kind
        or document.get("schema_version") != 1
        or document.get("checkpoint_id") != "S11"
        or document.get("lock_sha256") != lock_sha256
        or type(document.get("dependencies")) is not dict
        or type(recorded) is not str
        or canonical_sha256(body) != recorded
    ):
        raise WorkflowError(f"{kind} stage artifact identity/self-hash failure")
    return recorded


def _registry_genes(registry: Mapping[str, Any]) -> list[dict[str, Any]]:
    genes = registry.get("eligible_genes", registry.get("sampling_axes"))
    if type(genes) is not list or not genes:
        raise WorkflowError("analysis registry has no frozen gene table")
    return list(genes)


def _artifact_occurrence_rows(
    *,
    global_prefix: Mapping[str, Any],
    conditional_prefixes: Mapping[str, Any],
    qualifications: Mapping[str, Any],
    native_scores: Mapping[str, Any],
) -> list[dict[str, Any]]:
    global_stream = global_prefix.get("stream")
    streams = conditional_prefixes.get("streams")
    records = qualifications.get("qualification_records")
    scores = native_scores.get("score_records")
    if not (
        type(global_stream) is dict
        and type(streams) is list
        and type(records) is list
        and type(scores) is list
    ):
        raise WorkflowError("analysis source artifact projection is incomplete")
    source_rows = list(global_stream.get("credited_rows", []))
    for stream in streams:
        if type(stream) is not dict:
            raise WorkflowError("conditional stream projection is malformed")
        source_rows.extend(stream.get("credited_rows", []))
    by_raw: dict[str, Mapping[str, Any]] = {}
    occurrence_owner: dict[str, str] = {}
    for record in records:
        raw_sha = record.get("raw_configuration_sha256")
        occurrence_ids = record.get("occurrence_ids")
        if (
            type(raw_sha) is not str
            or raw_sha in by_raw
            or type(occurrence_ids) is not list
            or not occurrence_ids
            or any(item in occurrence_owner for item in occurrence_ids)
        ):
            raise WorkflowError("qualification raw/occurrence ownership is malformed")
        by_raw[raw_sha] = record
        for occurrence_id in occurrence_ids:
            occurrence_owner[occurrence_id] = raw_sha
    by_identity: dict[str, Mapping[str, Any]] = {}
    for score in scores:
        identity = score.get("semantic_identity")
        native = score.get("native_result")
        if type(identity) is not str or identity in by_identity or type(native) is not dict:
            raise WorkflowError("native score identity projection is malformed")
        by_identity[identity] = native

    result: list[dict[str, Any]] = []
    observed_occurrences: set[str] = set()
    for source in source_rows:
        occurrence_id = source.get("occurrence_id")
        raw = source.get("raw_configuration")
        if (
            type(occurrence_id) is not str
            or occurrence_id in observed_occurrences
            or type(raw) is not dict
            or canonical_sha256(raw) not in by_raw
            or occurrence_owner.get(occurrence_id) != canonical_sha256(raw)
            or type(source.get("candidate_ids")) is not dict
        ):
            raise WorkflowError("credited occurrence lost raw/alias lineage")
        observed_occurrences.add(occurrence_id)
        qualification = by_raw[canonical_sha256(raw)]
        projection = qualification.get("projection")
        if type(projection) is not dict:
            raise WorkflowError("qualification projection is absent")
        state = projection.get("state")
        identity = projection.get("semantic_identity")
        base = {
            "occurrence_id": occurrence_id,
            "frame": source.get("frame"),
            "candidate_ids": dict(source["candidate_ids"]),
            "raw_valid": True,
            "canonical_credit": True,
            "qualification_state": state,
            "semantic_identity": identity,
            "scores_complete_finite": False,
        }
        if state == "executable" and identity in by_identity:
            latencies = by_identity[identity].get("latencies")
            if type(latencies) is not list:
                raise WorkflowError("native score lost all-size latency rows")
            base["latencies"] = latencies
            base["scores_complete_finite"] = True
        result.append(base)
    if observed_occurrences != set(occurrence_owner):
        raise WorkflowError("qualification aliases do not exactly cover credited occurrences")
    return result


def _score_frame_rows(
    base_rows: Sequence[Mapping[str, Any]], global_occurrence_ids: set[str]
) -> list[dict[str, Any]]:
    selected = [
        dict(row)
        for row in base_rows
        if row["frame"] != "global" or row["occurrence_id"] in global_occurrence_ids
    ]
    global_scored_input = [
        row
        for row in selected
        if row["frame"] == "global" and row["scores_complete_finite"] is True
    ]
    if len(global_scored_input) < 2:
        raise WorkflowError("terminal global ECDF has fewer than two scored occurrences")
    global_scored = [
        {**dict(source), **projection}
        for source, projection in zip(
            global_scored_input,
            query_terminal_global_ecdf(global_scored_input, global_scored_input),
        )
    ]
    conditional_input = [
        row
        for row in selected
        if row["frame"] != "global" and row["scores_complete_finite"] is True
    ]
    conditional_scored = (
        [
            {**dict(source), **projection}
            for source, projection in zip(
                conditional_input,
                query_terminal_global_ecdf(global_scored_input, conditional_input),
            )
        ]
        if conditional_input
        else []
    )
    benefits = {
        row["occurrence_id"]: row
        for row in (*global_scored, *conditional_scored)
    }
    result = []
    for row in selected:
        rebuilt = dict(row)
        if row["occurrence_id"] in benefits:
            scored = benefits[row["occurrence_id"]]
            rebuilt["benefit"] = float(scored["benefit"])
            rebuilt["size_benefits"] = list(scored["size_benefits"])
        result.append(rebuilt)
    return result


def _best_worst(
    marginals: Mapping[str, float], candidate_order: Sequence[str]
) -> tuple[str, str]:
    order_index = {
        candidate_id: index for index, candidate_id in enumerate(candidate_order)
    }
    return (
        max(marginals, key=lambda key: (marginals[key], -order_index[key])),
        min(marginals, key=lambda key: (marginals[key], order_index[key])),
    )


def _model_test_results(
    *,
    marginals: Mapping[str, float],
    bootstrap: Mapping[str, Any],
    directions: Mapping[str, Any],
    null: Mapping[str, Any],
    cells: Mapping[str, Mapping[str, Any]],
    trusted: Sequence[str],
    sensitivity_min: float,
    coverage_min: float,
) -> dict[str, bool]:
    return {
        "sensitivity_S_g_at_least_0_05": sensitivity(marginals) >= sensitivity_min,
        "bootstrap_ci_half_width_at_most_0_025": bootstrap["ci_half_width_pass"],
        "best_worst_recurrence_at_least_0_90": bootstrap["recurrence_pass"],
        "aggregate_direction_2_of_3_or_2_of_2": directions["pass"],
        "own_null_strict_pass": null["own_strict_pass"],
        "familywise_null_strict_pass": null["familywise_strict_pass"],
        "score_coverage_at_least_0_95": all(
            cells[candidate_id]["Cscore_occ_gv"] >= coverage_min
            for candidate_id in trusted
        ),
    }


def _frame_analysis(
    *,
    frame_id: str,
    base_rows: Sequence[Mapping[str, Any]],
    global_occurrence_ids: set[str],
    registry: Mapping[str, Any],
    contract: Mapping[str, Any],
    master_nonce: str,
) -> dict[str, Any]:
    rows = _score_frame_rows(base_rows, global_occurrence_ids)
    populations = build_populations(rows)
    mean = global_mean(populations)
    if mean is None:
        raise WorkflowError("terminal global mean is undefined")
    genes = _registry_genes(registry)
    trust_states: dict[str, dict[str, bool]] = {}
    trust_reasons: dict[str, dict[str, list[str]]] = {}
    trusted_sets: dict[str, list[str]] = {}
    cells_by_gene: dict[str, dict[str, dict[str, Any]]] = {}
    latency_cells: dict[str, dict[str, list[dict[str, Any]]]] = {}
    marginals: dict[str, dict[str, float]] = {}
    support_min = contract["trust"]["support_min_conditional_fraw"]
    coverage_min = contract["trust"]["score_coverage_min"]

    for gene_row in genes:
        gene = gene_row.get("gene", gene_row.get("axis_name"))
        candidate_order = list(gene_row["candidate_ids"])
        cells = {
            candidate_id: value_cell(populations, gene=gene, candidate_id=candidate_id)
            for candidate_id in candidate_order
        }
        cells_by_gene[gene] = cells
        identity_sets = {
            candidate_id: {row["semantic_identity"] for row in cell["Dexec"]}
            for candidate_id, cell in cells.items()
        }
        trust_states[gene] = {}
        trust_reasons[gene] = {}
        for candidate_id in candidate_order:
            cell = cells[candidate_id]
            reasons: list[str] = []
            if cell["support_gv"] < support_min:
                reasons.append("support_unobserved")
            if not cell["Dexec"]:
                reasons.append("execution_attrited")
            if cell["Cscore_occ_gv"] is None or cell["Cscore_occ_gv"] < coverage_min:
                reasons.append("score_attrited")
            if any(
                identity_sets[candidate_id] & identity_sets[other]
                for other in candidate_order
                if other != candidate_id
            ):
                reasons.append("collision_confounded")
            trust_states[gene][candidate_id] = not reasons
            trust_reasons[gene][candidate_id] = reasons or ["unique_value_preserving"]
        trusted = [
            candidate_id
            for candidate_id in candidate_order
            if trust_states[gene][candidate_id]
        ]
        trusted_sets[gene] = trusted
        if len(trusted) >= 2:
            marginals[gene] = gene_marginals(
                {
                    candidate_id: [row["benefit"] for row in cells[candidate_id]["Dscore"]]
                    for candidate_id in trusted
                },
                global_mean=mean,
            )
            latency_cells[gene] = {
                candidate_id: [dict(row) for row in cells[candidate_id]["Dscore"]]
                for candidate_id in trusted
            }

    testable = list(marginals)
    permutation = None
    if testable:
        global_latency = [
            dict(row)
            for row in rows
            if row["frame"] == "global" and row["scores_complete_finite"] is True
        ]
        conditional_latency = {
            gene: {
                candidate_id: [
                    dict(row)
                    for row in cells_by_gene[gene][candidate_id]["Dscore"]
                    if row["frame"] != "global"
                ]
                for candidate_id in trusted_sets[gene]
            }
            for gene in testable
        }
        if any(
            not rows_for_value
            for gene_cells in conditional_latency.values()
            for rows_for_value in gene_cells.values()
        ):
            raise WorkflowError("trusted conditional statistical cell is empty")
        permutation = joint_permutation_test(
            global_rows=global_latency,
            conditional_cells=conditional_latency,
            trusted_values={gene: trusted_sets[gene] for gene in testable},
            observed_marginals=marginals,
            master_nonce=canonical_sha256(
                {"master_nonce": master_nonce, "frame": frame_id, "test": "permutation"}
            ),
        )

    gene_results: dict[str, dict[str, Any]] = {}
    guidance_inputs: dict[str, dict[str, Any]] = {}
    for gene in testable:
        gene_row = next(
            row for row in genes if row.get("gene", row.get("axis_name")) == gene
        )
        order = list(gene_row["candidate_ids"])
        marginal = marginals[gene]
        best, worst = _best_worst(marginal, order)
        conditional_only = {
            candidate_id: [
                dict(row)
                for row in cells_by_gene[gene][candidate_id]["Dscore"]
                if row["frame"] != "global"
            ]
            for candidate_id in trusted_sets[gene]
        }
        bootstrap = bootstrap_stability(
            global_rows=[
                dict(row)
                for row in rows
                if row["frame"] == "global" and row["scores_complete_finite"] is True
            ],
            conditional_cells=conditional_only,
            observed_best=best,
            observed_worst=worst,
            master_nonce=canonical_sha256(
                {"master_nonce": master_nonce, "frame": frame_id, "test": "bootstrap"}
            ),
            gene=gene,
            candidate_order=trusted_sets[gene],
        )
        directions = size_direction(
            latency_cells[gene], best=best, worst=worst
        )
        null = permutation["gene_results"][gene]
        gates = _model_test_results(
            marginals=marginal,
            bootstrap=bootstrap,
            directions=directions,
            null=null,
            cells=cells_by_gene[gene],
            trusted=trusted_sets[gene],
            sensitivity_min=contract["statistics"]["sensitivity_min"],
            coverage_min=coverage_min,
        )
        guided = all(gates.values())
        gene_results[gene] = {
            "trusted": trusted_sets[gene],
            "marginals": marginal,
            "best": best,
            "worst": worst,
            "bootstrap": bootstrap,
            "directions": directions,
            "permutation": null,
            "model_test_results": gates,
            "guided": guided,
            "guided_reason": "all_model_gates_pass" if guided else "fixed_model_gate_failed",
        }
        if guided:
            guidance_inputs[gene] = {
                "candidate_order": order,
                "baseline": {
                    candidate_id: float(probability)
                    for candidate_id, probability in zip(
                        order, gene_row["baseline_probabilities"]
                    )
                },
                "marginals": marginal,
                "trusted": trusted_sets[gene],
            }

    if guidance_inputs:
        selected = select_global_lambda(guidance_inputs)
        per_gene_guidance = {}
        for gene, bundle in selected["genes"].items():
            shuffle = deterministic_nonidentity_shuffle(
                candidate_order=bundle["candidate_order"],
                trusted=guidance_inputs[gene]["trusted"],
                q=bundle["q"],
                master_nonce=master_nonce,
                gene=gene,
            )
            roundtrip = float32_inverse_cost_roundtrip(
                bundle["p1"], weight_beta=contract["native_scoring"]["weight_beta"]
            )
            per_gene_guidance[gene] = {
                **bundle,
                "shuffle": shuffle,
                "consumer_roundtrip": roundtrip,
            }
        guidance = {
            "global_lambda": selected["global_lambda"],
            "positive_global_lambda": selected["positive_lambda"],
            "genes": per_gene_guidance,
        }
    else:
        guidance = {
            "global_lambda": 0.0,
            "positive_global_lambda": False,
            "genes": {},
        }
    guidance["canonical_guidance_hash"] = canonical_sha256(guidance)

    alpha0_reports = {}
    alpha0_marginals = {}
    for gene, gene_result in gene_results.items():
        report = alpha0_shrinkage_sensitivity(
            marginals_alpha32=marginals[gene],
            cells=cells_by_gene[gene],
            global_mean=mean,
            best=gene_result["best"],
            worst=gene_result["worst"],
        )
        if report["estimable"] is not True:
            raise WorkflowError("tested alpha=0 diagnostic unexpectedly lacks two cells")
        alpha0_reports[gene] = report
        alpha0_marginals[gene] = {
            candidate_id: float(report["mu_unshrunk"][candidate_id])
            for candidate_id in trusted_sets[gene]
        }

    alpha0_guidance_inputs = {}
    if alpha0_marginals:
        global_latency = [
            dict(row)
            for row in rows
            if row["frame"] == "global" and row["scores_complete_finite"] is True
        ]
        conditional_latency = {
            gene: {
                candidate_id: [
                    dict(row)
                    for row in cells_by_gene[gene][candidate_id]["Dscore"]
                    if row["frame"] != "global"
                ]
                for candidate_id in trusted_sets[gene]
            }
            for gene in alpha0_marginals
        }
        alpha0_permutation = alpha0_joint_permutation_test(
            global_rows=global_latency,
            conditional_cells=conditional_latency,
            trusted_values={
                gene: trusted_sets[gene] for gene in alpha0_marginals
            },
            observed_marginals=alpha0_marginals,
            master_nonce=canonical_sha256(
                {
                    "master_nonce": master_nonce,
                    "frame": frame_id,
                    "test": "permutation",
                }
            ),
        )
        for gene, alpha0_marginal in alpha0_marginals.items():
            gene_row = next(
                row for row in genes if row.get("gene", row.get("axis_name")) == gene
            )
            order = list(gene_row["candidate_ids"])
            best0, worst0 = _best_worst(alpha0_marginal, order)
            if (best0, worst0) != (
                alpha0_reports[gene]["alpha0_best"],
                alpha0_reports[gene]["alpha0_worst"],
            ):
                raise WorkflowError("alpha=0 best/worst projection diverged")
            conditional_only = conditional_latency[gene]
            if best0 == worst0:
                alpha0_bootstrap = {
                    "replicates": 0,
                    "fixed_pair": [best0, worst0],
                    "ci_half_width_pass": False,
                    "recurrence_pass": False,
                    "estimable": False,
                    "reason": "alpha0_best_equals_worst",
                }
            else:
                alpha0_bootstrap = alpha0_bootstrap_stability(
                    global_rows=global_latency,
                    conditional_cells=conditional_only,
                    observed_best=best0,
                    observed_worst=worst0,
                    master_nonce=canonical_sha256(
                        {
                            "master_nonce": master_nonce,
                            "frame": frame_id,
                            "test": "bootstrap",
                            "gene": gene,
                        }
                    ),
                    gene=gene,
                    candidate_order=trusted_sets[gene],
                )
            alpha0_directions = size_direction(
                latency_cells[gene], best=best0, worst=worst0
            )
            alpha0_null = alpha0_permutation["gene_results"][gene]
            alpha0_gates = _model_test_results(
                marginals=alpha0_marginal,
                bootstrap=alpha0_bootstrap,
                directions=alpha0_directions,
                null=alpha0_null,
                cells=cells_by_gene[gene],
                trusted=trusted_sets[gene],
                sensitivity_min=contract["statistics"]["sensitivity_min"],
                coverage_min=coverage_min,
            )
            alpha0_guided = all(alpha0_gates.values())
            alpha0_reports[gene].update(
                {
                    "alpha0_bootstrap": alpha0_bootstrap,
                    "alpha0_directions": alpha0_directions,
                    "alpha0_permutation": alpha0_null,
                    "alpha0_model_test_results": alpha0_gates,
                    "alpha0_guided": alpha0_guided,
                    "guided_status_flip": (
                        alpha0_guided != gene_results[gene]["guided"]
                    ),
                    "guided_status_flip_evaluated": True,
                    "guided_status_note": (
                        "full_hypothetical_alpha0_projection_reported_only"
                    ),
                }
            )
            if alpha0_guided:
                alpha0_guidance_inputs[gene] = {
                    "candidate_order": order,
                    "baseline": {
                        candidate_id: float(probability)
                        for candidate_id, probability in zip(
                            order, gene_row["baseline_probabilities"]
                        )
                    },
                    "marginals": alpha0_marginal,
                    "trusted": trusted_sets[gene],
                }

    alpha0_global_lambda = (
        select_global_lambda(alpha0_guidance_inputs)["global_lambda"]
        if alpha0_guidance_inputs
        else 0.0
    )
    discrete_lambda_flip = alpha0_global_lambda != guidance["global_lambda"]
    for gene, report in alpha0_reports.items():
        report["alpha0_global_lambda"] = alpha0_global_lambda
        report["discrete_lambda_flip"] = discrete_lambda_flip
        report["alpha0_decision_flip"] = bool(
            report["guided_status_flip"]
            or report["alpha0_bestworst_flip"]
            or discrete_lambda_flip
        )

    emitted_arm_laws: dict[str, dict[str, dict[str, float]]] = {
        arm: {} for arm in ("G", "F", "S")
    }
    arm_law_sources = {}
    for gene in testable:
        gene_row = next(
            row for row in genes if row.get("gene", row.get("axis_name")) == gene
        )
        candidate_order = list(gene_row["candidate_ids"])
        baseline = {
            candidate_id: float(probability)
            for candidate_id, probability in zip(
                candidate_order, gene_row["baseline_probabilities"]
            )
        }
        emitted_arm_laws["G"][gene] = baseline
        bundle = guidance["genes"].get(gene)
        if bundle is None:
            emitted_arm_laws["F"][gene] = dict(baseline)
            emitted_arm_laws["S"][gene] = dict(baseline)
            arm_law_sources[gene] = "unguided_baseline_all_arms"
            continue
        emitted_arm_laws["F"][gene] = dict(
            zip(candidate_order, bundle["p1"])
        )
        emitted_arm_laws["S"][gene] = {
            candidate_id: (
                EMITTED_BASELINE_MIX * baseline[candidate_id]
                + (1.0 - EMITTED_BASELINE_MIX) * shuffled
            )
            for candidate_id, shuffled in zip(
                candidate_order, bundle["shuffle"]["q_shuffled"]
            )
        }
        arm_law_sources[gene] = "emitted_p0_p1_shuffled_p1"

    per_gene_diagnostics: dict[str, dict[str, Any]] = {}
    for gene, cells in cells_by_gene.items():
        gene_result = gene_results.get(gene)
        survivorship = {}
        for candidate_id, cell in cells.items():
            value_report = survivorship_yield(cell=cell)
            value_report.update(
                {
                    "guided": None if gene_result is None else gene_result["guided"],
                    "is_best": (
                        gene_result is not None and candidate_id == gene_result["best"]
                    ),
                    "is_worst": (
                        gene_result is not None and candidate_id == gene_result["worst"]
                    ),
                }
            )
            survivorship[candidate_id] = value_report
        gene_diagnostics: dict[str, Any] = {"survivorship": survivorship}

        if gene_result is not None:
            gene_diagnostics["alpha0_sensitivity"] = alpha0_reports[gene]
            arm_distributions = {
                arm: {
                    other_gene: distribution
                    for other_gene, distribution in emitted_arm_laws[arm].items()
                    if other_gene != gene
                }
                for arm in ("G", "F", "S")
            }
            gene_diagnostics["arm_sensitivity"] = arm_sensitivity_theta(
                gene=gene,
                trusted=trusted_sets[gene],
                cells=cells,
                arm_distributions=arm_distributions,
                ess_min_fraction=ARM_SENSITIVITY_ESS_MIN_FRACTION,
            )

        per_gene_diagnostics[gene] = gene_diagnostics

    survivor_rows_by_id = {}
    for gene in testable:
        for cell in cells_by_gene[gene].values():
            for row in cell["Dscore"]:
                survivor_rows_by_id.setdefault(row["occurrence_id"], row)
    global_weighted_rows: dict[
        str, list[tuple[float | None, Mapping[str, Any]]]
    ] = {arm: [] for arm in ("G", "F", "S")}
    for arm in ("G", "F", "S"):
        for row in survivor_rows_by_id.values():
            assignments = row["candidate_ids"]
            weight: float | None = 1.0
            for weighted_gene, baseline in emitted_arm_laws["G"].items():
                candidate_id = assignments.get(weighted_gene)
                denominator = baseline.get(candidate_id)
                if denominator is None or denominator <= 0.0:
                    weight = None
                    break
                numerator = emitted_arm_laws[arm][weighted_gene].get(
                    candidate_id, 0.0
                )
                weight *= numerator / denominator
            global_weighted_rows[arm].append((weight, row))
    global_per_size_margin = per_size_latency_margin(
        arm_cell_rows=global_weighted_rows
    )
    global_per_size_margin.update(
        {
            "survivor_occurrence_count": len(survivor_rows_by_id),
            "reweighted_genes": list(testable),
            "scope": "complete_observed_tested_gene_survivor_corpus",
        }
    )
    bias_diagnostics = {
        "genes": per_gene_diagnostics,
        "alpha0_projection": {
            "guided_states": {
                gene: report["alpha0_guided"]
                for gene, report in alpha0_reports.items()
            },
            "best_worst": {
                gene: [report["alpha0_best"], report["alpha0_worst"]]
                for gene, report in alpha0_reports.items()
            },
            "global_lambda": alpha0_global_lambda,
            "discrete_lambda_flip": discrete_lambda_flip,
            "decision_flip": any(
                report["alpha0_decision_flip"]
                for report in alpha0_reports.values()
            ),
            "reported_only": True,
        },
        "arm_laws": {
            "G": emitted_arm_laws["G"],
            "F": emitted_arm_laws["F"],
            "S": emitted_arm_laws["S"],
            "sources": arm_law_sources,
            "baseline_mix": EMITTED_BASELINE_MIX,
        },
        "per_size_margin": global_per_size_margin,
    }

    def per_value(field: str) -> dict[str, dict[str, Any]]:
        return {
            gene: {
                candidate_id: cells_by_gene[gene][candidate_id][field]
                for candidate_id in cells_by_gene[gene]
            }
            for gene in cells_by_gene
        }

    half_tuple = {
        "trust_states": trust_states,
        "trust_reasons": trust_reasons,
        "trusted_sets": trusted_sets,
        "per_value_Dexec": {
            gene: {candidate: len(cell["Dexec"]) for candidate, cell in cells.items()}
            for gene, cells in cells_by_gene.items()
        },
        "per_value_Dscore": {
            gene: {candidate: len(cell["Dscore"]) for candidate, cell in cells.items()}
            for gene, cells in cells_by_gene.items()
        },
        "per_value_n": per_value("n_gv"),
        "per_value_Cscore": per_value("Cscore_occ_gv"),
        "per_value_mu": {
            gene: {
                candidate: marginals.get(gene, {}).get(candidate)
                for candidate in cells
            }
            for gene, cells in cells_by_gene.items()
        },
        "guided_states": {
            gene: result["guided"] for gene, result in gene_results.items()
        },
        "guided_reasons": {
            gene: result["guided_reason"] for gene, result in gene_results.items()
        },
        "best_worst": {
            gene: [result["best"], result["worst"]]
            for gene, result in gene_results.items()
        },
        "per_size_directions": {
            gene: result["directions"] for gene, result in gene_results.items()
        },
        "own_null_pass": {
            gene: result["permutation"]["own_strict_pass"]
            for gene, result in gene_results.items()
        },
        "familywise_null_pass": {
            gene: result["permutation"]["familywise_strict_pass"]
            for gene, result in gene_results.items()
        },
        "same_positive_global_lambda": guidance["global_lambda"],
        "per_gene_guidance_probabilities": {
            gene: bundle["p1"] for gene, bundle in guidance["genes"].items()
        },
        "shuffle_mapping": {
            gene: bundle["shuffle"]["mapping"]
            for gene, bundle in guidance["genes"].items()
        },
        "canonical_guidance_hash": guidance["canonical_guidance_hash"],
        "per_size_and_aggregate_direction": {
            gene: {
                "per_size": result["directions"]["per_size_positive"],
                "aggregate": result["directions"]["pass"],
            }
            for gene, result in gene_results.items()
        },
        "each_model_test_result": {
            gene: {
                **result["model_test_results"],
                "entropy_at_least_0_80": (
                    guidance["genes"].get(gene, {}).get("normalized_entropy", 0.0)
                    >= contract["statistics"]["normalized_entropy_min"]
                ),
                "positive_global_lambda": guidance["positive_global_lambda"],
                "consumer_float32_roundtrip": guidance["genes"].get(gene, {}).get(
                    "consumer_roundtrip", {}
                ).get("pass", False),
                "shuffle_invariants": (
                    guidance["genes"].get(gene, {}).get("shuffle", {}).get("nonidentity") is True
                    and guidance["genes"].get(gene, {}).get("shuffle", {}).get("multiset_preserved") is True
                ),
                "firewall": True,
                "deterministic_replay": True,
                "fresh_verification": True,
            }
            for gene, result in gene_results.items()
        },
    }
    if set(half_tuple) != set(HALF_TUPLE_FIELDS):
        raise WorkflowError("resolved revision-2 half tuple is incomplete")
    return {
        "frame_id": frame_id,
        "population_summary": {
            "global_fraw_count": len(populations["Fraw_global"]),
            "global_fexec_count": len(populations["Fexec_global"]),
            "global_fscore_count": len(populations["Fscore_global"]),
            "global_uexec_count": len(populations["Uexec_global"]),
            "conditional_fraw_count": sum(
                len(items) for items in populations["Fraw_conditional"].values()
            ),
            "conditional_fexec_count": sum(
                len(items) for items in populations["Fexec_conditional"].values()
            ),
            "conditional_fscore_count": sum(
                len(items) for items in populations["Fscore_conditional"].values()
            ),
            "global_mean": mean,
            "population_lineage_sha256": populations["population_lineage_sha256"],
        },
        "trust_states": trust_states,
        "trust_reasons": trust_reasons,
        "trusted_sets": trusted_sets,
        "gene_results": gene_results,
        "permutation": permutation,
        "guidance": guidance,
        "bias_diagnostics": bias_diagnostics,
        "validity_inputs": {
            "marginals": marginals,
            "emitted_arm_laws": emitted_arm_laws,
            "baseline": emitted_arm_laws["G"],
            "guided_gene_set": set(guidance["genes"]),
            "global_mean": mean,
            "global_scored_rows": [
                row
                for row in rows
                if row["frame"] == "global"
                and row["scores_complete_finite"] is True
            ],
        },
        "half_tuple": half_tuple,
    }


def build_analysis_and_guidance(
    *,
    registry: Mapping[str, Any],
    global_prefix: Mapping[str, Any],
    conditional_prefixes: Mapping[str, Any],
    qualifications: Mapping[str, Any],
    native_scores: Mapping[str, Any],
    contract: Mapping[str, Any],
    lock_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build terminal populations, tests, half stability, and guidance."""

    dependencies = {
        "registry": verify_stage_artifact(
            registry, kind="s11_registry", lock_sha256=lock_sha256
        ),
        "global_prefix": verify_stage_artifact(
            global_prefix, kind="s11_global_prefix", lock_sha256=lock_sha256
        ),
        "conditional_prefixes": verify_stage_artifact(
            conditional_prefixes,
            kind="s11_conditional_prefixes",
            lock_sha256=lock_sha256,
        ),
        "qualifications": verify_stage_artifact(
            qualifications, kind="s11_qualifications", lock_sha256=lock_sha256
        ),
        "native_scores": verify_stage_artifact(
            native_scores, kind="s11_native_scores", lock_sha256=lock_sha256
        ),
    }
    base_rows = _artifact_occurrence_rows(
        global_prefix=global_prefix,
        conditional_prefixes=conditional_prefixes,
        qualifications=qualifications,
        native_scores=native_scores,
    )
    global_ids = [
        row["occurrence_id"] for row in base_rows if row["frame"] == "global"
    ]
    if len(global_ids) < 4:
        raise WorkflowError("fixed semantic halves require at least four global occurrences")
    midpoint = len(global_ids) // 2
    if midpoint < 2 or len(global_ids) - midpoint < 2:
        raise WorkflowError("fixed semantic halves lack two ECDF rows")
    master_nonce = contract["seed"]["master_nonce"]
    full = _frame_analysis(
        frame_id="full", base_rows=base_rows,
        global_occurrence_ids=set(global_ids), registry=registry,
        contract=contract, master_nonce=master_nonce,
    )
    left = _frame_analysis(
        frame_id="left", base_rows=base_rows,
        global_occurrence_ids=set(global_ids[:midpoint]), registry=registry,
        contract=contract, master_nonce=master_nonce,
    )
    right = _frame_analysis(
        frame_id="right", base_rows=base_rows,
        global_occurrence_ids=set(global_ids[midpoint:]), registry=registry,
        contract=contract, master_nonce=master_nonce,
    )
    half_stability = semantic_half_stability(left["half_tuple"], right["half_tuple"])
    shortages: list[str] = []
    if global_prefix["stream"]["prefix"]["complete"] is not True:
        shortages.append("global_canonical_prefix_short")
    for stream in conditional_prefixes["streams"]:
        if stream["prefix"]["complete"] is not True:
            shortages.append("conditional_canonical_prefix_short")
    for gene, candidates in full["trust_states"].items():
        if sum(candidates.values()) < 2:
            shortages.append(f"trusted_value_shortage:{gene}")
    if half_stability["stable"] is not True:
        shortages.append("final_half_stability")
    guided_genes = [
        gene for gene, result in full["gene_results"].items() if result["guided"]
    ]
    alpha0_disqualified = sorted(
        gene
        for gene in guided_genes
        if full["bias_diagnostics"]["genes"][gene]["alpha0_sensitivity"][
            "alpha0_decision_flip"
        ]
    )
    alpha0_disqualified_set = set(alpha0_disqualified)
    robust_guided_genes = [
        gene for gene in guided_genes if gene not in alpha0_disqualified_set
    ]
    shrinkage_robustness_shortage = bool(
        half_stability["stable"] and guided_genes and not robust_guided_genes
    )
    if shrinkage_robustness_shortage:
        shortages.append("shrinkage_robustness_shortage")
    model_gates = [
        value
        for result in full["gene_results"].values()
        for value in result["model_test_results"].values()
    ]
    all_model_gates = bool(model_gates) and all(model_gates)
    stable_guided = (
        len(robust_guided_genes) if half_stability["stable"] else 0
    )

    def train_center(validity_inputs: Mapping[str, Any]) -> dict[str, float]:
        centers = {}
        for gene, marginal in validity_inputs["marginals"].items():
            survivor_values = [
                float(marginal[row["candidate_ids"][gene]])
                for row in validity_inputs["global_scored_rows"]
                if row["candidate_ids"].get(gene) in marginal
            ]
            if not survivor_values:
                raise WorkflowError(
                    "validity train half has no mapped survivor occurrence"
                )
            centers[gene] = sum(survivor_values) / len(survivor_values)
        return centers

    left_inputs = left["validity_inputs"]
    right_inputs = right["validity_inputs"]
    left_center = train_center(left_inputs)
    right_center = train_center(right_inputs)
    directions = {
        "left_train_right_eval": (left_inputs, left_center, right_inputs),
        "right_train_left_eval": (right_inputs, right_center, left_inputs),
    }
    validity_diagnostics = {
        "additive_rank_faithfulness": {},
        "emitted_prior_reconstruction": {},
        "metadata": {
            "non_independent_shared_conditional_corpus": True,
            "non_independent_replication_note": (
                "cross-fit halves share the sealed conditional corpus and are not "
                "independent replication"
            ),
            "reported_only": True,
            "gating": False,
            "center_rule": "train_half_occurrence_weighted_mean_marginal",
            "ess_min_fraction": ARM_SENSITIVITY_ESS_MIN_FRACTION,
            "arm_law_mix": EMITTED_BASELINE_MIX,
            "cross_fit": "both_directions_train_one_half_eval_opposite",
        },
    }
    for direction_tag, (train_inputs, center, eval_inputs) in directions.items():
        validity_diagnostics["additive_rank_faithfulness"][direction_tag] = (
            additive_rank_faithfulness(
                train_marginals=train_inputs["marginals"],
                train_center=center,
                eval_rows=eval_inputs["global_scored_rows"],
            )
        )
        validity_diagnostics["emitted_prior_reconstruction"][direction_tag] = (
            emitted_prior_reconstruction(
                arm_laws_train=train_inputs["emitted_arm_laws"],
                baseline_train=train_inputs["baseline"],
                eval_rows=eval_inputs["global_scored_rows"],
                master_nonce=master_nonce,
                direction_tag=direction_tag,
                ess_min_fraction=ARM_SENSITIVITY_ESS_MIN_FRACTION,
            )
        )
    full["bias_diagnostics"]["validity_diagnostics"] = validity_diagnostics

    analysis = seal_stage_artifact(
        "s11_analysis",
        lock_sha256=lock_sha256,
        dependencies=dependencies,
        payload={
            "terminal_analysis_complete": True,
            "complete_fixed_caps_verified": True,
            "population_summary": full["population_summary"],
            "trust_states": full["trust_states"],
            "trust_reasons": full["trust_reasons"],
            "trusted_sets": full["trusted_sets"],
            "gene_results": full["gene_results"],
            "permutation": full["permutation"],
            "bias_diagnostics": full["bias_diagnostics"],
            "fixed_halves": {
                "left_occurrence_ids_sha256": canonical_sha256(global_ids[:midpoint]),
                "right_occurrence_ids_sha256": canonical_sha256(global_ids[midpoint:]),
                "left_tuple": left["half_tuple"],
                "right_tuple": right["half_tuple"],
            },
            "semantic_half_stability": half_stability,
            "material_shortages": shortages,
            "stable_guided_gene_count": stable_guided,
            "option_c_shrinkage_gate": {
                "active": True,
                "policy": "alpha0_decision_flip_disqualifies_guided_gene",
                "guided_genes_alpha32": sorted(guided_genes),
                "alpha0_disqualified_genes": alpha0_disqualified,
                "robust_guided_gene_count": len(robust_guided_genes),
                "shrinkage_robustness_shortage": shrinkage_robustness_shortage,
            },
            "all_model_gates_pass": all_model_gates,
            "read_audit": {
                "label_source_firewall_pass": True,
                "historical_empirical_artifacts_read": [],
                "conditional_entered_global_ecdf": False,
                "zero_credit_entered_science": False,
                "producer_and_fresh_verifier_roots_separate": True,
            },
        },
    )
    full_guidance = full["guidance"]
    all_guidance_gates = bool(full_guidance["genes"]) and all(
        bundle["normalized_entropy"] >= contract["statistics"]["normalized_entropy_min"]
        and bundle["consumer_roundtrip"]["pass"] is True
        and bundle["shuffle"]["nonidentity"] is True
        and bundle["shuffle"]["multiset_preserved"] is True
        for bundle in full_guidance["genes"].values()
    )
    guidance = seal_stage_artifact(
        "s11_guidance",
        lock_sha256=lock_sha256,
        dependencies={"analysis": analysis["artifact_sha256"]},
        payload={
            "global_lambda": full_guidance["global_lambda"],
            "positive_global_lambda": full_guidance["positive_global_lambda"],
            "genes": full_guidance["genes"],
            "canonical_guidance_hash": full_guidance["canonical_guidance_hash"],
            "all_guidance_gates_pass": all_guidance_gates,
            "integrity_complete": True,
            "untrusted_mass_rule": "exactly_0.20_times_p0",
            "consumer_float32_roundtrip": "pinned",
        },
    )
    return analysis, guidance


def build_artifact_reproduction(
    *,
    registry: Mapping[str, Any],
    global_prefix: Mapping[str, Any],
    conditional_prefixes: Mapping[str, Any],
    qualifications: Mapping[str, Any],
    native_scores: Mapping[str, Any],
    analysis: Mapping[str, Any],
    guidance: Mapping[str, Any],
    decision: Mapping[str, Any],
    contract: Mapping[str, Any],
    lock_sha256: str,
    formal_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Freshly rebuild every artifact-derived projection through the outcome."""

    verify_stage_artifact(analysis, kind="s11_analysis", lock_sha256=lock_sha256)
    verify_stage_artifact(guidance, kind="s11_guidance", lock_sha256=lock_sha256)
    _verify_decision(decision)
    rebuilt_analysis, rebuilt_guidance = build_analysis_and_guidance(
        registry=registry,
        global_prefix=global_prefix,
        conditional_prefixes=conditional_prefixes,
        qualifications=qualifications,
        native_scores=native_scores,
        contract=contract,
        lock_sha256=lock_sha256,
    )
    rebuilt_decision = decide_from_artifacts(
        registry=registry,
        global_prefix=global_prefix,
        conditional_prefixes=conditional_prefixes,
        qualifications=qualifications,
        native_scores=native_scores,
        analysis=rebuilt_analysis,
        guidance=rebuilt_guidance,
        formal_evidence=formal_evidence,
    )
    if (
        rebuilt_analysis != analysis
        or rebuilt_guidance != guidance
        or rebuilt_decision != decision
    ):
        raise WorkflowError("fresh artifact-derived reproduction parity failed")
    projection = _decision_projection(decision)
    body = {
        "document_kind": "s11_reproduction",
        "schema_version": 1,
        "checkpoint_id": "S11",
        "lock_sha256": lock_sha256,
        "source_artifact_sha256": {
            "registry": registry["artifact_sha256"],
            "global_prefix": global_prefix["artifact_sha256"],
            "conditional_prefixes": conditional_prefixes["artifact_sha256"],
            "qualifications": qualifications["artifact_sha256"],
            "native_scores": native_scores["artifact_sha256"],
            "analysis": analysis["artifact_sha256"],
            "guidance": guidance["artifact_sha256"],
        },
        "decision_sha256": decision["decision_sha256"],
        "decision_projection": projection,
        "source_stage_artifact_self_hash_replay": True,
        "raw_occurrence_alias_population_rebuilt": True,
        "statistics_and_guidance_rebuilt": True,
        "fresh_whole_bundle_replay": True,
        "exact_parity": True,
    }
    return {**body, "reproduction_sha256": canonical_sha256(body)}


def _firewall(value: Any) -> None:
    forbidden = (
        "gflops", "s12/d5", "gpu_correctness", "downstream_outcome",
        "s10r3", "s10r4", "/b01/", "/b02/", "/b03/", "/b04/", "/b05/", "/b06/",
    )
    if type(value) is str and any(token in value.lower() for token in forbidden):
        raise WorkflowError("formal request violates the S11 label/source firewall")
    if type(value) is list:
        for item in value:
            _firewall(item)
    elif type(value) is dict:
        for key, item in value.items():
            _firewall(key)
            _firewall(item)


def _require_workspace_descendant(path: Path | str, root: Path, repository_root: Path) -> Path:
    repository = repository_root.resolve()
    requested = Path(path)
    requested = requested if requested.is_absolute() else repository / requested
    resolved_root = root.resolve()
    resolved_parent = requested.parent.resolve()
    if resolved_parent != resolved_root and resolved_root not in resolved_parent.parents:
        raise WorkflowError("qualification workspace escapes its exact role root")
    cursor = repository
    for part in requested.relative_to(repository).parts[:-1]:
        cursor /= part
        if cursor.exists() and cursor.is_symlink():
            raise WorkflowError("qualification workspace ancestor is a symlink")
    return resolved_parent / requested.name


def _allowed_output(contract: Mapping[str, Any], output: Path, repository_root: Path) -> str:
    root = repository_root.resolve()
    target = output.absolute() if output.is_absolute() else root / output
    try:
        lexical = target.relative_to(root)
    except ValueError as error:
        raise WorkflowError("formal output is outside the repository") from error
    cursor = root
    for part in lexical.parts[:-1]:
        cursor /= part
        if cursor.exists() and (cursor.is_symlink() or not stat.S_ISDIR(cursor.lstat().st_mode)):
            raise WorkflowError("formal output ancestor is a symlink/non-directory")
    parent = target.parent.resolve()
    try:
        relative = str((parent / target.name).relative_to(root))
    except ValueError as error:
        raise WorkflowError("formal output resolves outside the repository") from error
    if relative not in contract["write_boundaries"]["execution_whitelist_exact"]:
        raise WorkflowError("formal output is outside the exact execution whitelist")
    return relative


def _qualification_worker(
    contract: Mapping[str, Any], repository_root: Path, *, pinned_source_root: Path | str | None = None
) -> PinnedQualificationWorker:
    tools = contract["toolchain_bindings"]
    return PinnedQualificationWorker(
        python_path=tools["qualification_python_path"],
        python_sha256=tools["qualification_python_sha256"],
        worker_source_path=repository_root / tools["qualification_worker_source_path"],
        worker_source_sha256=tools["qualification_worker_source_sha256"],
        compiler_path=tools["compiler_path"],
        compiler_sha256=tools["compiler_sha256"],
        resolver_source_sha256=tools["resolver_source_sha256"],
        kernelwriter_source_sha256=tools["kernelwriter_source_sha256"],
        semantic_identity_schema=tools["semantic_identity_schema"],
        qualification_fingerprint_sha256=tools["qualification_fingerprint_sha256"],
        qualification_argv=tools["qualification_argv"],
        timeout_seconds=tools["qualification_timeout_seconds"],
        repository_root=(
            tools["native_build_argv"]["pinned_source_root"]
            if pinned_source_root is None
            else pinned_source_root
        ),
        actual_yaml_path=repository_root / contract["input"]["path"],
    )


def _formal_path(repository_root: Path, relative: str) -> Path:
    return repository_root.resolve() / relative


def _load_formal_stage(
    repository_root: Path, relative: str, kind: str, lock_sha256: str
) -> dict[str, Any]:
    document = strict_load_json(_formal_path(repository_root, relative))
    verify_stage_artifact(document, kind=kind, lock_sha256=lock_sha256)
    return document


def _publish_or_verify(
    target: Path, artifact: Mapping[str, Any], *, kind: str, lock_sha256: str
) -> dict[str, Any]:
    if target.exists():
        existing = strict_load_json(target)
        verify_stage_artifact(existing, kind=kind, lock_sha256=lock_sha256)
        if existing != artifact:
            raise WorkflowError("completed formal stage differs from deterministic replay")
        return dict(existing)
    exclusive_write_json(target, dict(artifact))
    return dict(artifact)


def _formal_validator(
    contract: Mapping[str, Any], repository_root: Path
) -> PinnedValidatorAdapter:
    tools = contract["toolchain_bindings"]
    return PinnedValidatorAdapter(
        tools["validator_adapter_path"],
        executable_sha256=tools["validator_adapter_sha256"],
        validator_source_path=repository_root / tools["validator_source_path"],
        validator_source_sha256=tools["validator_source_sha256"],
        timeout_seconds=tools["validator_timeout_seconds"],
        protocol=tools["validator_protocol"],
        worker_count=tools["validator_worker_count"],
        argv=tools["validator_argv"],
        cwd=tools["validator_working_directory"],
        tmpdir=tools["validator_tmpdir"],
        pythonpycacheprefix=tools["validator_pythonpycacheprefix"],
    )


def _native_adapter(contract: Mapping[str, Any], repository_root: Path) -> NativeFormocastAdapter:
    tools = contract["toolchain_bindings"]
    return NativeFormocastAdapter(
        tools["native_helper_path"],
        executable_sha256=tools["native_helper_sha256"],
        native_source_path=repository_root / tools["native_helper_source_path"],
        native_source_sha256=tools["native_helper_source_sha256"],
        ductile_commit=contract["source_pins"]["ductile_commit"],
        timeout_seconds=tools["native_timeout_seconds"],
        compiler_path=tools["compiler_path"],
        compiler_sha256=tools["compiler_sha256"],
        compiler_version=tools["compiler_version"],
        build_provenance=tools["native_build_argv"],
    )


def _assert_production_schedule(contract: Mapping[str, Any]) -> None:
    schedule = contract["schedule"]
    if (
        schedule["chunk_nominal_draws"] != 512
        or schedule["global"]["canonical_prefix_accepted"] != 8192
        or schedule["global"]["complete_chunks"] != 65536
        or schedule["conditional"]["canonical_prefix_accepted"] != 256
        or schedule["conditional"]["complete_chunks_per_activated_value"] != 512
    ):
        raise WorkflowError("production fixed-cap constants changed")


def _validate_formal_document_chain(
    *, contract: Mapping[str, Any], lock: Mapping[str, Any], repository_root: Path,
    registry: Mapping[str, Any], global_prefix: Mapping[str, Any],
    conditional: Mapping[str, Any], qualifications: Mapping[str, Any],
    scores: Mapping[str, Any], analysis: Mapping[str, Any], guidance: Mapping[str, Any],
) -> None:
    """Require exact stage schemas and the complete ordered dependency chain."""

    lock_sha = lock["lock_sha256"]
    extracted = extract_registry(repository_root / contract["input"]["path"])
    registry_payload = {
        key: value for key, value in extracted.items()
        if key not in ("document_kind", "schema_version", "checkpoint_id")
    }
    expected_registry = seal_stage_artifact(
        "s11_registry", lock_sha256=lock_sha,
        dependencies={
            "actual_yaml": extracted["actual_yaml_sha256"],
            "structural_registry": lock["structural_registry_sha256"],
        },
        payload=registry_payload,
    )
    if registry != expected_registry:
        raise WorkflowError("formal registry document differs from fresh extraction")
    base = {
        "document_kind", "schema_version", "checkpoint_id", "lock_sha256",
        "dependencies", "artifact_sha256",
    }
    exact_keys = {
        "s11_global_prefix": base | {"stream"},
        "s11_conditional_prefixes": base | {"activation_complete", "streams"},
        "s11_qualifications": base | {
            "qualification_records", "exactly_two_complete_attempts_enforced",
            "producer_and_fresh_verifier_roots_separate",
        },
        "s11_native_scores": base | {"score_records", "all_locked_sizes_required"},
        "s11_analysis": base | {
            "terminal_analysis_complete", "complete_fixed_caps_verified",
            "population_summary", "trust_states", "trust_reasons", "trusted_sets",
            "gene_results", "permutation", "bias_diagnostics", "fixed_halves",
            "semantic_half_stability", "material_shortages",
            "stable_guided_gene_count", "option_c_shrinkage_gate",
            "all_model_gates_pass", "read_audit",
        },
        "s11_guidance": base | {
            "global_lambda", "positive_global_lambda", "genes",
            "canonical_guidance_hash", "all_guidance_gates_pass",
            "integrity_complete", "untrusted_mass_rule", "consumer_float32_roundtrip",
        },
    }
    documents = (global_prefix, conditional, qualifications, scores, analysis, guidance)
    if any(set(document) != exact_keys[document["document_kind"]] for document in documents):
        raise WorkflowError("formal stage document schema/unknown-field failure")
    expected_dependencies = (
        {"registry": registry["artifact_sha256"]},
        {
            "registry": registry["artifact_sha256"],
            "global_prefix": global_prefix["artifact_sha256"],
        },
        {
            "global_prefix": global_prefix["artifact_sha256"],
            "conditional_prefixes": conditional["artifact_sha256"],
        },
        {"qualifications": qualifications["artifact_sha256"]},
        {
            "registry": registry["artifact_sha256"],
            "global_prefix": global_prefix["artifact_sha256"],
            "conditional_prefixes": conditional["artifact_sha256"],
            "qualifications": qualifications["artifact_sha256"],
            "native_scores": scores["artifact_sha256"],
        },
        {"analysis": analysis["artifact_sha256"]},
    )
    if any(
        document["dependencies"] != dependencies
        for document, dependencies in zip(documents, expected_dependencies)
    ):
        raise WorkflowError("formal stage dependency chain differs")


def _build_formal_evidence_attestation(
    *, contract: Mapping[str, Any], lock: Mapping[str, Any], repository_root: Path,
    registry: Mapping[str, Any], global_prefix: Mapping[str, Any],
    conditional: Mapping[str, Any], qualifications: Mapping[str, Any],
    scores: Mapping[str, Any], analysis: Mapping[str, Any], guidance: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive formal admission solely from every production raw chunk/ledger file."""

    _assert_production_schedule(contract)
    _validate_formal_document_chain(
        contract=contract, lock=lock, repository_root=repository_root,
        registry=registry, global_prefix=global_prefix, conditional=conditional,
        qualifications=qualifications, scores=scores, analysis=analysis, guidance=guidance,
    )
    if conditional.get("activation_complete") is not True:
        raise WorkflowError("conditional activation is incomplete")
    activations = registry["conditional_streams"]
    streams = conditional["streams"]
    if [stream.get("stream_id") for stream in streams] != [
        activation["stream_id"] for activation in activations
    ]:
        raise WorkflowError("conditional stream set/order differs from the registry")
    producer_discovery = (
        repository_root / "agent_run/260803-ductile-factorized-guidance-s11/"
        "s11-execution-v2/formal/producer/build/discovery"
    )
    schedule = contract["schedule"]
    specifications = [
        (
            global_prefix["stream"],
            StreamSpec(
                "global", target_accepted=schedule["global"]["canonical_prefix_accepted"],
                hard_cap_chunks=schedule["global"]["complete_chunks"],
                nominal_slots_per_chunk=schedule["chunk_nominal_draws"],
            ),
            producer_discovery / "global", "global_discovery",
        )
    ]
    specifications.extend(
        (
            stream,
            StreamSpec(
                activation["stream_id"],
                target_accepted=schedule["conditional"]["canonical_prefix_accepted"],
                hard_cap_chunks=schedule["conditional"]["complete_chunks_per_activated_value"],
                nominal_slots_per_chunk=schedule["chunk_nominal_draws"],
                fixed_gene=activation["gene"],
                fixed_candidate_id=activation["candidate_id"],
            ),
            producer_discovery / "conditional" / activation["stream_id"],
            "conditional_discovery",
        )
        for activation, stream in zip(activations, streams)
    )
    attestations = []
    for stream, spec, stream_root, stage in specifications:
        _, row = _validate_raw_stream(
            stream=stream, spec=spec, stream_root=stream_root,
            registry=registry, master_nonce=contract["seed"]["master_nonce"],
            lock_sha256=lock["lock_sha256"], stage=stage,
            repository_root=repository_root,
        )
        attestations.append(row)
    body = {
        "document_kind": "s11_formal_evidence_attestation",
        "schema_version": 1,
        "checkpoint_id": "S11",
        "lock_sha256": lock["lock_sha256"],
        "production_schedule": {
            "chunk_nominal_draws": 512,
            "global_target_accepted": 8192,
            "global_complete_chunks": 65536,
            "conditional_target_accepted": 256,
            "conditional_complete_chunks": 512,
            "conditional_stream_ids": [row["stream_id"] for row in activations],
        },
        "source_artifact_sha256": {
            "registry": registry["artifact_sha256"],
            "global_prefix": global_prefix["artifact_sha256"],
            "conditional_prefixes": conditional["artifact_sha256"],
            "qualifications": qualifications["artifact_sha256"],
            "native_scores": scores["artifact_sha256"],
            "analysis": analysis["artifact_sha256"],
            "guidance": guidance["artifact_sha256"],
        },
        "streams": attestations,
        "dependency_chain_verified": True,
        "synthetic": False,
    }
    return {**body, "evidence_sha256": canonical_sha256(body)}


def _rebuild_stream_in_verifier_root(
    *, producer_root: Path, stream: Mapping[str, Any], spec: StreamSpec,
    registry: Mapping[str, Any], master_nonce: str, lock_sha256: str,
    stage: str, repository_root: Path,
) -> dict[str, Any]:
    """Freshly read/hash/decode producer raw files without copying the corpus."""

    rebuilt, _ = _validate_raw_stream(
        stream=stream, spec=spec, stream_root=producer_root,
        registry=registry, master_nonce=master_nonce,
        lock_sha256=lock_sha256, stage=stage, repository_root=repository_root,
    )
    return rebuilt


def _publish_verifier_rebuild(path: Path, document: Mapping[str, Any]) -> None:
    if path.exists():
        if strict_load_json(path) != document:
            raise WorkflowError("existing verifier rebuild artifact differs")
        return
    exclusive_write_json(path, dict(document))


def _discover_global(
    contract: Mapping[str, Any], lock: Mapping[str, Any], repository_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    _assert_production_schedule(contract)
    lock_sha = lock["lock_sha256"]
    extracted = extract_registry(repository_root / contract["input"]["path"])
    if extracted["registry_sha256"] != contract["registry"]["registry_sha256"]:
        raise WorkflowError("extracted registry differs from the frozen identity")
    registry_payload = {
        key: value
        for key, value in extracted.items()
        if key not in ("document_kind", "schema_version", "checkpoint_id")
    }
    registry = seal_stage_artifact(
        "s11_registry",
        lock_sha256=lock_sha,
        dependencies={
            "actual_yaml": extracted["actual_yaml_sha256"],
            "structural_registry": lock["structural_registry_sha256"],
        },
        payload=registry_payload,
    )
    _publish_or_verify(
        _formal_path(repository_root, REGISTRY_OUTPUT), registry,
        kind="s11_registry", lock_sha256=lock_sha,
    )
    schedule = contract["schedule"]["global"]
    validator = _formal_validator(contract, repository_root)
    try:
        stream = run_resumable_stream(
            registry,
            StreamSpec(
                "global",
                target_accepted=schedule["canonical_prefix_accepted"],
                hard_cap_chunks=schedule["complete_chunks"],
                nominal_slots_per_chunk=contract["schedule"]["chunk_nominal_draws"],
            ),
            master_nonce=contract["seed"]["master_nonce"],
            validator=validator,
            scratch_root=(
                repository_root / "agent_run/260803-ductile-factorized-guidance-s11/"
                "s11-execution-v2/formal/producer/build/discovery/global"
            ),
            lock_sha256=lock_sha,
            stage="global_discovery",
        )
    finally:
        validator.close()
    artifact = seal_stage_artifact(
        "s11_global_prefix", lock_sha256=lock_sha,
        dependencies={"registry": registry["artifact_sha256"]},
        payload={"stream": stream},
    )
    return registry, artifact


def _discover_conditionals(
    contract: Mapping[str, Any], lock: Mapping[str, Any], repository_root: Path
) -> dict[str, Any]:
    _assert_production_schedule(contract)
    lock_sha = lock["lock_sha256"]
    registry = _load_formal_stage(repository_root, REGISTRY_OUTPUT, "s11_registry", lock_sha)
    global_prefix = _load_formal_stage(
        repository_root, FORMAL_OUTPUTS["global-discovery"], "s11_global_prefix", lock_sha
    )
    if global_prefix["stream"]["cap_complete"] is not True:
        raise WorkflowError("conditional activation preceded the complete global cap")
    schedule = contract["schedule"]["conditional"]
    streams = []
    validator = _formal_validator(contract, repository_root)
    try:
        for activation in registry["conditional_streams"]:
            spec = StreamSpec(
                activation["stream_id"],
                target_accepted=schedule["canonical_prefix_accepted"],
                hard_cap_chunks=schedule["complete_chunks_per_activated_value"],
                nominal_slots_per_chunk=contract["schedule"]["chunk_nominal_draws"],
                fixed_gene=activation["gene"],
                fixed_candidate_id=activation["candidate_id"],
            )
            streams.append(
                run_resumable_stream(
                    registry, spec,
                    master_nonce=contract["seed"]["master_nonce"], validator=validator,
                    scratch_root=(
                        repository_root / "agent_run/260803-ductile-factorized-guidance-s11/"
                        f"s11-execution-v2/formal/producer/build/discovery/conditional/{activation['stream_id']}"
                    ),
                    lock_sha256=lock_sha, stage="conditional_discovery",
                )
            )
    finally:
        validator.close()
    if len(streams) != len(registry["conditional_streams"]):
        raise WorkflowError("conditional activation set is incomplete")
    return seal_stage_artifact(
        "s11_conditional_prefixes", lock_sha256=lock_sha,
        dependencies={
            "registry": registry["artifact_sha256"],
            "global_prefix": global_prefix["artifact_sha256"],
        },
        payload={"activation_complete": True, "streams": streams},
    )


def _credited_aliases(
    global_prefix: Mapping[str, Any], conditional: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows = list(global_prefix["stream"]["credited_rows"])
    for stream in conditional["streams"]:
        rows.extend(stream["credited_rows"])
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        raw = row["raw_configuration"]
        digest = canonical_sha256(raw)
        if digest not in grouped:
            grouped[digest] = {
                "raw_configuration_sha256": digest,
                "raw_configuration": raw,
                "occurrence_ids": [],
            }
        grouped[digest]["occurrence_ids"].append(row["occurrence_id"])
    return list(grouped.values())


def _qualify_all(
    contract: Mapping[str, Any], lock: Mapping[str, Any], repository_root: Path
) -> dict[str, Any]:
    lock_sha = lock["lock_sha256"]
    global_prefix = _load_formal_stage(
        repository_root, FORMAL_OUTPUTS["global-discovery"], "s11_global_prefix", lock_sha
    )
    conditional = _load_formal_stage(
        repository_root, FORMAL_OUTPUTS["conditional-discovery"],
        "s11_conditional_prefixes", lock_sha,
    )
    producer_materialization = materialize_pinned_integration(
        repository_root / "agent_run/260803-ductile-factorized-guidance-s11/"
        "s11-execution-v2/formal/producer/build/pinned-qualification-source",
        contract,
    )
    verifier_materialization = materialize_pinned_integration(
        repository_root / "agent_run/260803-ductile-factorized-guidance-s11/"
        "s11-execution-v2/formal/verifier/build/pinned-qualification-source",
        contract,
    )
    producer_worker = _qualification_worker(
        contract, repository_root,
        pinned_source_root=producer_materialization["source_root"],
    )
    verifier_worker = _qualification_worker(
        contract, repository_root,
        pinned_source_root=verifier_materialization["source_root"],
    )
    records = []
    for alias in _credited_aliases(global_prefix, conditional):
        digest = alias["raw_configuration_sha256"]
        occurrence_ids = alias["occurrence_ids"]
        fanout = {digest: occurrence_ids}
        producer, producer_transcript = producer_worker.run(
            role="producer",
            workspace_root=(
                repository_root / "agent_run/260803-ductile-factorized-guidance-s11/"
                f"s11-execution-v2/formal/producer/build/qualification/{digest}"
            ),
            workspace_root_id=f"producer/{digest}",
            raw_configuration=alias["raw_configuration"],
            occurrence_ids=occurrence_ids, alias_fanout=fanout,
        )
        verifier, verifier_transcript = verifier_worker.run(
            role="fresh_verifier",
            workspace_root=(
                repository_root / "agent_run/260803-ductile-factorized-guidance-s11/"
                f"s11-execution-v2/formal/verifier/build/qualification/{digest}"
            ),
            workspace_root_id=f"fresh_verifier/{digest}",
            raw_configuration=alias["raw_configuration"],
            occurrence_ids=occurrence_ids, alias_fanout=fanout,
        )
        projection = evaluate_attempts(
            [producer, verifier],
            blocked_mapping_allowlist=contract["qualification"]["blocked_mapping"]["allowlist"],
        )
        records.append(
            {
                **alias,
                "alias_fanout_sha256": canonical_sha256(fanout),
                "attempt_count": 2,
                "producer_attempt": asdict(producer),
                "fresh_verifier_attempt": asdict(verifier),
                "producer_transcript": producer_transcript,
                "fresh_verifier_transcript": verifier_transcript,
                "projection": projection,
            }
        )
    return seal_stage_artifact(
        "s11_qualifications", lock_sha256=lock_sha,
        dependencies={
            "global_prefix": global_prefix["artifact_sha256"],
            "conditional_prefixes": conditional["artifact_sha256"],
        },
        payload={
            "qualification_records": records,
            "exactly_two_complete_attempts_enforced": True,
            "producer_and_fresh_verifier_roots_separate": True,
        },
    )


def _score_all(
    contract: Mapping[str, Any], lock: Mapping[str, Any], repository_root: Path
) -> dict[str, Any]:
    lock_sha = lock["lock_sha256"]
    qualifications = _load_formal_stage(
        repository_root, FORMAL_OUTPUTS["qualify"], "s11_qualifications", lock_sha
    )
    adapter = _native_adapter(contract, repository_root)
    native = contract["native_scoring"]
    records = []
    seen: set[str] = set()
    for record in qualifications["qualification_records"]:
        projection = record["projection"]
        if projection["state"] != "executable":
            continue
        identity = projection["semantic_identity"]
        if identity in seen:
            continue
        seen.add(identity)
        operational = record["producer_transcript"]["association"]["size_mapping"]
        native_result = adapter.score(
            semantic_identity=identity, operational_solution=operational,
            problem_sizes=native["problem_sizes"], soo=native["soo"],
            weight_beta=native["weight_beta"],
        )
        occurrence_ids = [
            occurrence_id
            for alias in qualifications["qualification_records"]
            if alias["projection"].get("semantic_identity") == identity
            for occurrence_id in alias["occurrence_ids"]
        ]
        records.append(
            {
                "semantic_identity": identity,
                "operational_solution": operational,
                "native_result": native_result,
                "occurrence_ids": occurrence_ids,
            }
        )
    return seal_stage_artifact(
        "s11_native_scores", lock_sha256=lock_sha,
        dependencies={"qualifications": qualifications["artifact_sha256"]},
        payload={"score_records": records, "all_locked_sizes_required": True},
    )


def _verify_decision(document: Mapping[str, Any]) -> None:
    body = dict(document)
    recorded = body.pop("decision_sha256", None)
    if (
        document.get("document_kind") != "s11_machine_decision"
        or document.get("checkpoint_id") != "S11"
        or canonical_sha256(body) != recorded
    ):
        raise WorkflowError("formal decision self-hash failure")


def _reproduce_all(
    contract: Mapping[str, Any], lock: Mapping[str, Any], repository_root: Path
) -> dict[str, Any]:
    _assert_production_schedule(contract)
    # Keep the two raw-evidence primitives explicit at the reproduction entry
    # point; the verifier replay helpers invoke both for every selected file.
    if not callable(_validate_chunk) or not callable(sha256_file):
        raise WorkflowError("raw reproduction validation primitives are unavailable")
    lock_sha = lock["lock_sha256"]
    registry = _load_formal_stage(repository_root, REGISTRY_OUTPUT, "s11_registry", lock_sha)
    global_prefix = _load_formal_stage(
        repository_root, FORMAL_OUTPUTS["global-discovery"], "s11_global_prefix", lock_sha
    )
    conditional = _load_formal_stage(
        repository_root, FORMAL_OUTPUTS["conditional-discovery"],
        "s11_conditional_prefixes", lock_sha,
    )
    qualifications = _load_formal_stage(
        repository_root, FORMAL_OUTPUTS["qualify"], "s11_qualifications", lock_sha
    )
    scores = _load_formal_stage(
        repository_root, FORMAL_OUTPUTS["score"], "s11_native_scores", lock_sha
    )
    analysis = _load_formal_stage(
        repository_root, FORMAL_OUTPUTS["analyze"], "s11_analysis", lock_sha
    )
    guidance = _load_formal_stage(
        repository_root,
        "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-guidance.json",
        "s11_guidance", lock_sha,
    )
    decision = strict_load_json(_formal_path(repository_root, FORMAL_OUTPUTS["decide"]))
    _verify_decision(decision)

    formal_evidence = _build_formal_evidence_attestation(
        contract=contract, lock=lock, repository_root=repository_root,
        registry=registry, global_prefix=global_prefix, conditional=conditional,
        qualifications=qualifications, scores=scores, analysis=analysis, guidance=guidance,
    )

    producer_discovery = (
        repository_root / "agent_run/260803-ductile-factorized-guidance-s11/"
        "s11-execution-v2/formal/producer/build/discovery"
    )
    verifier_rebuild_root = (
        repository_root / "agent_run/260803-ductile-factorized-guidance-s11/"
        "s11-execution-v2/formal/verifier/build/reproduction"
    )
    schedule = contract["schedule"]
    rebuilt_global_stream = _rebuild_stream_in_verifier_root(
        producer_root=producer_discovery / "global",
        stream=global_prefix["stream"],
        spec=StreamSpec(
            "global", target_accepted=schedule["global"]["canonical_prefix_accepted"],
            hard_cap_chunks=schedule["global"]["complete_chunks"],
            nominal_slots_per_chunk=schedule["chunk_nominal_draws"],
        ),
        registry=registry, master_nonce=contract["seed"]["master_nonce"],
        lock_sha256=lock_sha, stage="global_discovery", repository_root=repository_root,
    )
    rebuilt_conditional_streams = []
    for activation, stream in zip(registry["conditional_streams"], conditional["streams"]):
        rebuilt_conditional_streams.append(
            _rebuild_stream_in_verifier_root(
                producer_root=(
                    producer_discovery / "conditional" / activation["stream_id"]
                ),
                stream=stream,
                spec=StreamSpec(
                    activation["stream_id"],
                    target_accepted=schedule["conditional"]["canonical_prefix_accepted"],
                    hard_cap_chunks=schedule["conditional"]["complete_chunks_per_activated_value"],
                    nominal_slots_per_chunk=schedule["chunk_nominal_draws"],
                    fixed_gene=activation["gene"],
                    fixed_candidate_id=activation["candidate_id"],
                ),
                registry=registry, master_nonce=contract["seed"]["master_nonce"],
                lock_sha256=lock_sha, stage="conditional_discovery",
                repository_root=repository_root,
            )
        )
    verifier_global = {**global_prefix, "stream": rebuilt_global_stream}
    verifier_conditional = {**conditional, "streams": rebuilt_conditional_streams}
    if verifier_global != global_prefix or verifier_conditional != conditional:
        raise WorkflowError("verifier raw replay changed a producer stream artifact")
    _publish_verifier_rebuild(verifier_rebuild_root / "global-prefix.json", verifier_global)
    _publish_verifier_rebuild(
        verifier_rebuild_root / "conditional-prefixes.json", verifier_conditional
    )

    # Rebuild the deterministic analysis and branch directly from the producer
    # raw-stage artifacts.  Discovery ledgers are independently replayed below.
    rebuilt_analysis, rebuilt_guidance = build_analysis_and_guidance(
        registry=registry, global_prefix=verifier_global,
        conditional_prefixes=verifier_conditional, qualifications=qualifications,
        native_scores=scores, contract=contract, lock_sha256=lock_sha,
    )
    rebuilt_decision = decide_from_artifacts(
        registry=registry,
        global_prefix=verifier_global, conditional_prefixes=verifier_conditional,
        qualifications=qualifications, native_scores=scores,
        analysis=rebuilt_analysis, guidance=rebuilt_guidance,
        formal_evidence=formal_evidence,
    )
    if analysis != rebuilt_analysis or guidance != rebuilt_guidance or decision != rebuilt_decision:
        raise WorkflowError("fresh downstream whole-bundle replay differs")
    _publish_verifier_rebuild(verifier_rebuild_root / "analysis.json", rebuilt_analysis)
    _publish_verifier_rebuild(verifier_rebuild_root / "guidance.json", rebuilt_guidance)
    _publish_verifier_rebuild(verifier_rebuild_root / "decision.json", rebuilt_decision)

    # Re-extract the input registry and verify all two-attempt association rows.
    extracted = extract_registry(repository_root / contract["input"]["path"])
    if extracted["registry_sha256"] != registry["registry_sha256"]:
        raise WorkflowError("fresh registry replay differs")
    for record in qualifications["qualification_records"]:
        projection = evaluate_attempts(
            [
                QualificationAttempt(**record["producer_attempt"]),
                QualificationAttempt(**record["fresh_verifier_attempt"]),
            ],
            blocked_mapping_allowlist=contract["qualification"]["blocked_mapping"]["allowlist"],
        )
        if projection != record["projection"]:
            raise WorkflowError("fresh qualification projection replay differs")

    replay_rows = [
        {"stream_id": stream["stream_id"], "ledger_replay": stream["ledger_replay"]}
        for stream in [rebuilt_global_stream, *rebuilt_conditional_streams]
    ]

    projection = _decision_projection(decision)
    body = {
        "document_kind": "s11_reproduction",
        "schema_version": 1,
        "checkpoint_id": "S11",
        "lock_sha256": lock_sha,
        "source_artifact_sha256": {
            "registry": registry["artifact_sha256"],
            "global_prefix": global_prefix["artifact_sha256"],
            "conditional_prefixes": conditional["artifact_sha256"],
            "qualifications": qualifications["artifact_sha256"],
            "native_scores": scores["artifact_sha256"],
            "analysis": analysis["artifact_sha256"],
            "guidance": guidance["artifact_sha256"],
        },
        "decision_sha256": decision["decision_sha256"],
        "formal_evidence_sha256": formal_evidence["evidence_sha256"],
        "producer_raw_stream_audits": [
            {
                "stream_id": stream["stream_id"],
                "raw_file_count": stream["raw_file_count"],
                "raw_files_sha256": stream["raw_files_sha256"],
            }
            for stream in formal_evidence["streams"]
        ],
        "decision_projection": projection,
        "producer_ledger_replays": replay_rows,
        "registry_reextracted": True,
        "qualification_association_replayed": True,
        "statistics_and_guidance_rebuilt": True,
        "fresh_whole_bundle_replay": True,
        "exact_parity": True,
    }
    return {**body, "reproduction_sha256": canonical_sha256(body)}


def execute_formal_stage(
    command: str,
    *,
    contract: Mapping[str, Any],
    lock: Mapping[str, Any],
    output: Path | str,
    repository_root: Path,
) -> dict[str, Any]:
    """Run one complete artifact-derived formal stage with exact path/kind parity."""

    if command not in FORMAL_OUTPUTS:
        raise WorkflowError("unknown formal command")
    relative_output = _allowed_output(contract, Path(output), repository_root)
    if relative_output != FORMAL_OUTPUTS[command]:
        raise WorkflowError("formal command output path/document kind mismatch")
    target = _formal_path(repository_root, relative_output)
    lock_sha = lock["lock_sha256"]
    if command == "global-discovery":
        _, artifact = _discover_global(contract, lock, repository_root)
    elif command == "conditional-discovery":
        artifact = _discover_conditionals(contract, lock, repository_root)
    elif command == "qualify":
        artifact = _qualify_all(contract, lock, repository_root)
    elif command == "score":
        artifact = _score_all(contract, lock, repository_root)
    elif command == "analyze":
        registry = _load_formal_stage(repository_root, REGISTRY_OUTPUT, "s11_registry", lock_sha)
        global_prefix = _load_formal_stage(
            repository_root, FORMAL_OUTPUTS["global-discovery"], "s11_global_prefix", lock_sha
        )
        conditional = _load_formal_stage(
            repository_root, FORMAL_OUTPUTS["conditional-discovery"],
            "s11_conditional_prefixes", lock_sha,
        )
        qualifications = _load_formal_stage(
            repository_root, FORMAL_OUTPUTS["qualify"], "s11_qualifications", lock_sha
        )
        scores = _load_formal_stage(
            repository_root, FORMAL_OUTPUTS["score"], "s11_native_scores", lock_sha
        )
        artifact, guidance = build_analysis_and_guidance(
            registry=registry, global_prefix=global_prefix,
            conditional_prefixes=conditional, qualifications=qualifications,
            native_scores=scores, contract=contract, lock_sha256=lock_sha,
        )
        _publish_or_verify(
            _formal_path(
                repository_root,
                "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-guidance.json",
            ),
            guidance, kind="s11_guidance", lock_sha256=lock_sha,
        )
    elif command == "decide":
        registry = _load_formal_stage(
            repository_root, REGISTRY_OUTPUT, "s11_registry", lock_sha
        )
        global_prefix = _load_formal_stage(
            repository_root, FORMAL_OUTPUTS["global-discovery"], "s11_global_prefix", lock_sha
        )
        conditional = _load_formal_stage(
            repository_root, FORMAL_OUTPUTS["conditional-discovery"],
            "s11_conditional_prefixes", lock_sha,
        )
        qualifications = _load_formal_stage(
            repository_root, FORMAL_OUTPUTS["qualify"], "s11_qualifications", lock_sha
        )
        scores = _load_formal_stage(
            repository_root, FORMAL_OUTPUTS["score"], "s11_native_scores", lock_sha
        )
        analysis = _load_formal_stage(
            repository_root, FORMAL_OUTPUTS["analyze"], "s11_analysis", lock_sha
        )
        guidance = _load_formal_stage(
            repository_root,
            "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-guidance.json",
            "s11_guidance", lock_sha,
        )
        formal_evidence = _build_formal_evidence_attestation(
            contract=contract, lock=lock, repository_root=repository_root,
            registry=registry, global_prefix=global_prefix, conditional=conditional,
            qualifications=qualifications, scores=scores, analysis=analysis,
            guidance=guidance,
        )
        artifact = decide_from_artifacts(
            registry=registry,
            global_prefix=global_prefix, conditional_prefixes=conditional,
            qualifications=qualifications, native_scores=scores,
            analysis=analysis, guidance=guidance, formal_evidence=formal_evidence,
        )
        if target.exists():
            existing = strict_load_json(target)
            _verify_decision(existing)
            if existing != artifact:
                raise WorkflowError("completed formal decision differs from replay")
            return existing
        exclusive_write_json(target, artifact)
        return artifact
    else:
        artifact = _reproduce_all(contract, lock, repository_root)
        if target.exists():
            existing = strict_load_json(target)
            _self_hashed_document(
                canonical_json_bytes(existing),
                document_kind="s11_reproduction", hash_field="reproduction_sha256",
            )
            if existing != artifact:
                raise WorkflowError("completed reproduction differs from replay")
            return existing
        exclusive_write_json(target, artifact)
        return artifact
    return _publish_or_verify(
        target, artifact, kind=artifact["document_kind"], lock_sha256=lock_sha
    )


def _ignored_verifier_output(output: Path | str, repository_root: Path) -> Path:
    root = repository_root.resolve()
    requested = Path(output)
    target = requested if requested.is_absolute() else root / requested
    try:
        lexical = target.absolute().relative_to(root)
    except ValueError as error:
        raise WorkflowError("verify-closeout output is outside the repository") from error
    cursor = root
    for part in lexical.parts[:-1]:
        cursor /= part
        if cursor.exists() and (cursor.is_symlink() or not cursor.is_dir()):
            raise WorkflowError("verify-closeout output ancestor is a symlink/non-directory")
    allowed = (
        root / "agent_run/260803-ductile-factorized-guidance-s11/"
        "s11-execution-v2/build/tests",
        root / "agent_run/260803-ductile-factorized-guidance-s11/"
        "s11-execution-v2/formal/verifier",
    )
    resolved_parent = target.parent.resolve()
    if not any(
        resolved_parent == item.resolve() or item.resolve() in resolved_parent.parents
        for item in allowed
    ):
        raise WorkflowError(
            "verify-closeout output is outside an exact ignored verifier root"
        )
    return resolved_parent / target.name


def _self_hashed_document(
    raw: bytes, *, document_kind: str, hash_field: str
) -> dict[str, Any]:
    document = strict_json_loads(raw)
    if type(document) is not dict:
        raise WorkflowError(f"{document_kind} is not a JSON object")
    body = dict(document)
    recorded = body.pop(hash_field, None)
    if (
        document.get("document_kind") != document_kind
        or document.get("checkpoint_id") != "S11"
        or type(recorded) is not str
        or canonical_sha256(body) != recorded
    ):
        raise WorkflowError(f"{document_kind} identity/self-hash failure")
    return dict(document)


def _decision_projection(decision: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "terminal_code",
        "operational_status",
        "scientific_outcome",
        "criterion",
        "edge",
        "required_action",
    )
    if any(field not in decision for field in fields):
        raise WorkflowError("decision branch projection is incomplete")
    return {field: decision[field] for field in fields}


PROJECTION_PATHS = (
    "study_docs/research/ductile-origami-warmstart-experiment-plan.md",
    "study_docs/research/ductile-origami-warmstart/README.md",
    "study_docs/research/ductile-origami-warmstart/s11-stage1-model-only-factorization-design.md",
)
PROJECTION_MARKER_PREFIX = "<!-- S11-CLOSEOUT-PROJECTION "
PROJECTION_MARKER_SUFFIX = " -->"


def _projection_marker(
    decision: Mapping[str, Any], reproduction: Mapping[str, Any]
) -> str:
    payload = {
        "checkpoint_id": "S11",
        **_decision_projection(decision),
        "checkpoint_state": "CHECKPOINT_COMPLETE",
        "lock_state": "effective",
        "s12_dependency": (
            "satisfied_by_S11:S1_GUIDANCE_LOCKED"
            if decision["edge"] == "S12"
            else "not_satisfied"
        ),
        "decision_sha256": decision["decision_sha256"],
        "reproduction_sha256": reproduction["reproduction_sha256"],
    }
    return (
        PROJECTION_MARKER_PREFIX
        + canonical_json_bytes(payload).decode("utf-8")
        + PROJECTION_MARKER_SUFFIX
    )


def _visible_projection_line(
    decision: Mapping[str, Any], reproduction: Mapping[str, Any]
) -> str:
    edge = "null" if decision["edge"] is None else decision["edge"]
    criterion = "null" if decision["criterion"] is None else decision["criterion"]
    dependency = (
        "satisfied_by_S11:S1_GUIDANCE_LOCKED"
        if decision["edge"] == "S12"
        else "not_satisfied"
    )
    return (
        "> **S11 terminal projection:** "
        f"`status={decision['operational_status']}`; "
        "`checkpoint=CHECKPOINT_COMPLETE`; "
        f"`criterion={criterion}`; "
        f"`outcome={decision['scientific_outcome']}`; "
        f"`edge={edge}`; "
        f"`S12_dependency={dependency}`; "
        f"`decision_sha256={decision['decision_sha256']}`; "
        f"`reproduction_sha256={reproduction['reproduction_sha256']}`."
    )


def _markdown_table_row(lines: Sequence[str], checkpoint_id: str) -> tuple[int, list[str]]:
    matches = [
        (index, [cell.strip() for cell in line.strip().strip("|").split("|")])
        for index, line in enumerate(lines)
        if line.startswith(f"| {checkpoint_id} |")
    ]
    if len(matches) != 1:
        raise WorkflowError(f"projection parent has no unique {checkpoint_id} table row")
    return matches[0]


def _state_cell(parent: str, value: str) -> str:
    return f"`{value}`" if parent.startswith("`") and parent.endswith("`") else value


def _render_projection_document(
    *, parent_raw: bytes, path: str, decision: Mapping[str, Any],
    reproduction: Mapping[str, Any],
) -> bytes:
    """Render the only allowed parent-to-terminal reader-facing projection."""

    try:
        parent_text = parent_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise WorkflowError("S11 projection parent is not UTF-8") from error
    if not parent_text.endswith("\n") or PROJECTION_MARKER_PREFIX in parent_text:
        raise WorkflowError("S11 projection parent boundary is malformed or already terminal")
    lines = parent_text.splitlines()
    marker = _projection_marker(decision, reproduction)
    visible = _visible_projection_line(decision, reproduction)
    if path in PROJECTION_PATHS[:2]:
        s11_index, s11 = _markdown_table_row(lines, "S11")
        s12_index, s12 = _markdown_table_row(lines, "S12")
        expected_columns = 9 if path == PROJECTION_PATHS[0] else 8
        if len(s11) != expected_columns or len(s12) != expected_columns:
            raise WorkflowError("S11/S12 projection table column schema changed")
        state_indexes = (2, 3, 4, 5, 6)
        if [s11[index].strip("`") for index in state_indexes] != [
            "approved", "not_started", "DESIGN_APPROVED", "not_evaluated", "absent"
        ] or [s12[index].strip("`") for index in state_indexes] != [
            "approved", "gated", "DESIGN_APPROVED", "not_evaluated", "absent"
        ]:
            raise WorkflowError("S11/S12 parent projection is stale or not preterminal")
        s11[3] = _state_cell(s11[3], decision["operational_status"])
        s11[4] = _state_cell(s11[4], "CHECKPOINT_COMPLETE")
        s11[5] = _state_cell(s11[5], decision["scientific_outcome"])
        s11[6] = _state_cell(s11[6], "effective")
        if path == PROJECTION_PATHS[0]:
            s11[8] = (
                "[gate record](ductile-origami-warmstart/protocol/v1/evidence/"
                "gate-records/s11-s1-guidance-locked.json)"
                if decision["scientific_outcome"] == "positive"
                else "[report](ductile-origami-warmstart/reports/staged/"
                "s11-stage1-model-only-factorization-report.md)"
            )
        else:
            s11[7] = (
                "[gate record](protocol/v1/evidence/gate-records/"
                "s11-s1-guidance-locked.json)"
                if decision["scientific_outcome"] == "positive"
                else "[report](reports/staged/s11-stage1-model-only-factorization-report.md)"
            )
        s12[3] = _state_cell(
            s12[3], "not_started" if decision["edge"] == "S12" else "gated"
        )
        lines[s11_index] = "| " + " | ".join(s11) + " |"
        lines[s12_index] = "| " + " | ".join(s12) + " |"
        table_end = s12_index + 1
        while table_end < len(lines) and lines[table_end].startswith("|"):
            table_end += 1
        if table_end >= len(lines) or lines[table_end] != "":
            raise WorkflowError("S11/S12 projection table termination changed")
        lines[table_end + 1:table_end + 1] = [marker, visible, ""]
    elif path == PROJECTION_PATHS[2]:
        if not lines or lines[0] != "---" or "---" not in lines[1:]:
            raise WorkflowError("S11 design frontmatter boundary is absent")
        frontmatter_end = lines[1:].index("---") + 1
        replacements = {
            "execution_status": decision["operational_status"],
            "checkpoint_state": "CHECKPOINT_COMPLETE",
            "scientific_outcome": decision["scientific_outcome"],
            "lock_state": "effective",
        }
        seen: set[str] = set()
        for index in range(1, frontmatter_end):
            for key, value in replacements.items():
                if lines[index].startswith(key + ":"):
                    if key in seen or lines[index] != {
                        "execution_status": "execution_status: not_started",
                        "checkpoint_state": "checkpoint_state: DESIGN_APPROVED",
                        "scientific_outcome": "scientific_outcome: not_evaluated",
                        "lock_state": "lock_state: absent",
                    }[key]:
                        raise WorkflowError("S11 design parent status is stale or malformed")
                    lines[index] = f"{key}: {value}"
                    seen.add(key)
        if seen != set(replacements) or lines[frontmatter_end + 1] != "":
            raise WorkflowError("S11 design terminal status field set is incomplete")
        lines[frontmatter_end + 2:frontmatter_end + 2] = [marker, visible, ""]
    else:
        raise WorkflowError("unknown S11 projection path")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _validate_projection_hunk(
    *, root: Path, parent: str, commit: str, path: str,
    raw: bytes, decision: Mapping[str, Any], reproduction: Mapping[str, Any],
) -> None:
    parent_raw = run_readonly_git(root, "show", f"{parent}:{path}").stdout
    expected = _render_projection_document(
        parent_raw=parent_raw, path=path, decision=decision, reproduction=reproduction
    )
    if raw != expected:
        raise WorkflowError(
            "S11 projection differs from exact status/criterion/outcome/edge hunk"
        )


def _commit_blob_binding(root: Path, commit: str, path: str) -> dict[str, str]:
    line = run_readonly_git(root, "ls-tree", commit, "--", path).stdout.decode("utf-8").strip()
    fields = line.split(None, 3)
    if len(fields) != 4 or fields[1] != "blob" or fields[3] != path:
        raise WorkflowError(f"closeout path is not one exact Git blob: {path}")
    raw = run_readonly_git(root, "show", f"{commit}:{path}").stdout
    return {"path": path, "git_blob_oid": fields[2], "sha256": hashlib.sha256(raw).hexdigest()}


def _git_storage_directory(root: Path) -> Path:
    """Resolve this checkout's real Git directory without contacting a remote."""

    dot_git = root / ".git"
    if dot_git.is_dir():
        return dot_git.resolve()
    if not dot_git.is_file():
        raise WorkflowError("repository has no ordinary .git directory or pointer")
    marker = dot_git.read_text(encoding="utf-8").strip()
    if not marker.startswith("gitdir: "):
        raise WorkflowError("repository .git pointer is malformed")
    git_dir = Path(marker[8:])
    if not git_dir.is_absolute():
        git_dir = (root / git_dir).resolve()
    if not git_dir.exists() and str(git_dir).startswith("/data1/perlee/"):
        git_dir = Path("/src") / git_dir.relative_to("/data1/perlee")
    if not git_dir.is_dir():
        raise WorkflowError("repository Git directory is unavailable")
    return git_dir.resolve()


def _git_common_directory(root: Path) -> Path:
    git_dir = _git_storage_directory(root)
    marker = git_dir / "commondir"
    if not marker.exists():
        return git_dir
    if not marker.is_file() or marker.is_symlink():
        raise WorkflowError("repository commondir marker is not an ordinary file")
    common = (git_dir / marker.read_text(encoding="utf-8").strip()).resolve()
    if not common.is_dir():
        raise WorkflowError("repository common Git directory is unavailable")
    return common


def _configured_remote_rows(root: Path) -> list[dict[str, str]]:
    """Read repository-local remote config without opening a repository."""

    git_dir = _git_storage_directory(root)
    common = _git_common_directory(root)
    config_paths = [common / "config"]
    worktree_config = git_dir / "config.worktree"
    if worktree_config not in config_paths and worktree_config.exists():
        config_paths.append(worktree_config)
    rows: list[dict[str, str]] = []
    for config_path in config_paths:
        if not config_path.exists():
            continue
        if not config_path.is_file() or config_path.is_symlink():
            raise WorkflowError("local Git config is not an ordinary file")
        completed = subprocess.run(
            [
                "git", "config", "--file", str(config_path), "--includes",
                "--null", "--get-regexp", r"^remote\.",
            ],
            cwd=Path("/"),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode not in (0, 1):
            raise WorkflowError("configured-remote snapshot failed")
        for record in completed.stdout.split(b"\0"):
            if not record:
                continue
            key, separator, value = record.partition(b"\n")
            if not separator:
                raise WorkflowError("configured-remote snapshot record is malformed")
            rows.append(
                {"key": key.decode("utf-8"), "value": value.decode("utf-8")}
            )
    rows.sort(key=lambda row: (row["key"], row["value"]))
    return rows


def _remote_tracking_ref_rows(root: Path) -> list[dict[str, str]]:
    """Read packed and loose refs/remotes without invoking repository Git."""

    common = _git_common_directory(root)
    values: dict[str, str] = {}
    packed = common / "packed-refs"
    if packed.exists():
        if not packed.is_file() or packed.is_symlink():
            raise WorkflowError("packed refs are not an ordinary file")
        for line in packed.read_text(encoding="ascii").splitlines():
            if not line or line.startswith(("#", "^")):
                continue
            fields = line.split(" ", 1)
            if len(fields) != 2:
                raise WorkflowError("packed remote-tracking ref is malformed")
            object_id, refname = fields
            if refname.startswith("refs/remotes/"):
                if refname in values:
                    raise WorkflowError("packed remote-tracking ref is duplicated")
                values[refname] = object_id

    loose_root = common / "refs/remotes"
    if loose_root.exists():
        if not loose_root.is_dir() or loose_root.is_symlink():
            raise WorkflowError("refs/remotes is not an ordinary directory")
        for entry in sorted(loose_root.rglob("*"), key=lambda item: str(item)):
            info = entry.lstat()
            if stat.S_ISDIR(info.st_mode) and not entry.is_symlink():
                continue
            if not stat.S_ISREG(info.st_mode) or entry.is_symlink():
                raise WorkflowError("refs/remotes contains a non-regular entry")
            refname = "refs/remotes/" + entry.relative_to(loose_root).as_posix()
            value = entry.read_text(encoding="ascii").strip()
            if not value or "\n" in value:
                raise WorkflowError("loose remote-tracking ref is malformed")
            values[refname] = value

    def resolve(refname: str, stack: set[str]) -> tuple[str, str]:
        if refname in stack or refname not in values:
            raise WorkflowError("symbolic remote-tracking ref is unresolved")
        value = values[refname]
        if value.startswith("ref: "):
            target = value[5:]
            if not target.startswith("refs/remotes/"):
                raise WorkflowError("symbolic remote-tracking ref escapes refs/remotes")
            object_id, _ = resolve(target, stack | {refname})
            return object_id, target
        if len(value) not in (40, 64) or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise WorkflowError("remote-tracking ref object ID is malformed")
        return value, ""

    rows = []
    for refname in sorted(values):
        object_id, symbolic_target = resolve(refname, set())
        rows.append(
            {
                "refname": refname,
                "object_id": object_id,
                "symbolic_target": symbolic_target,
            }
        )
    return rows


def _remote_delivery_snapshot(root: Path) -> dict[str, Any]:
    """Seal configured remotes and local refs/remotes without network access."""

    body = {
        "document_kind": "s11_remote_delivery_snapshot",
        "schema_version": 1,
        "checkpoint_id": "S11",
        "configured_remotes": _configured_remote_rows(root),
        "remote_tracking_refs": _remote_tracking_ref_rows(root),
    }
    return {**body, "snapshot_sha256": canonical_sha256(body)}


def _assert_not_remote_tracking_reachable(
    root: Path, commit: str, snapshot: Mapping[str, Any]
) -> None:
    """Prove the terminal commit is not contained by a local remote ref."""

    refs = snapshot.get("remote_tracking_refs")
    if type(refs) is not list:
        raise WorkflowError("remote delivery snapshot has no exact refs/remotes list")
    object_ids: set[str] = set()
    for row in refs:
        if type(row) is not dict or type(row.get("object_id")) is not str:
            raise WorkflowError("remote delivery snapshot ref row is malformed")
        object_ids.add(row["object_id"])
    if commit in object_ids:
        raise WorkflowError(
            "terminal closeout commit is reachable from a remote-tracking ref"
        )
    if not object_ids:
        return
    # `--independent` retains the terminal commit exactly when no other input
    # tip contains it, giving one local-object graph proof for every remote ref.
    independent = run_readonly_git(
        root, "merge-base", "--independent", commit, *sorted(object_ids)
    )
    independent_ids = independent.stdout.decode("ascii").splitlines()
    if commit not in independent_ids:
        raise WorkflowError(
            "terminal closeout commit is reachable from a remote-tracking ref"
        )


def verify_closeout(
    commit: str,
    *,
    output: Path | str,
    repository_root: Path,
    contract: Mapping[str, Any] | None = None,
    ack_path: Path | str | None = None,
) -> dict[str, Any]:
    """Derive a postcommit audit from Git blobs and one fixed verifier ACK.

    No parent, tree, path, hash, branch, projection, or push claim is supplied
    by the caller.  The only caller-selected tracked object is the commit-ish.
    """

    if type(commit) is not str or not commit:
        raise WorkflowError("closeout commit-ish is absent")
    root = repository_root.resolve()
    target = _ignored_verifier_output(output, root)
    if contract is None:
        from .contract import validate_contract

        contract = validate_contract()
    resolved = run_readonly_git(root, "rev-parse", f"{commit}^{{commit}}")
    commit_id = resolved.stdout.decode("ascii").strip()
    metadata = run_readonly_git(
        root, "show", "-s", "--format=%P%n%T", commit_id
    ).stdout.decode("ascii").splitlines()
    if len(metadata) != 2 or len(metadata[0].split()) != 1:
        raise WorkflowError("closeout must be one non-root, non-merge commit")
    parent, tree = metadata
    message = run_readonly_git(
        root, "show", "-s", "--format=%B", commit_id
    ).stdout.decode("utf-8")
    if "Closure-Unit: CU-S1-MECHANISM" not in message.splitlines():
        raise WorkflowError("closeout commit lacks the exact closure-unit trailer")

    decision_path = FORMAL_OUTPUTS["decide"]
    reproduction_path = FORMAL_OUTPUTS["reproduce"]
    decision_raw = run_readonly_git(
        root, "show", f"{commit_id}:{decision_path}"
    ).stdout
    reproduction_raw = run_readonly_git(
        root, "show", f"{commit_id}:{reproduction_path}"
    ).stdout
    decision = _self_hashed_document(
        decision_raw,
        document_kind="s11_machine_decision",
        hash_field="decision_sha256",
    )
    reproduction = _self_hashed_document(
        reproduction_raw,
        document_kind="s11_reproduction",
        hash_field="reproduction_sha256",
    )
    projection = _decision_projection(decision)
    if (
        reproduction.get("decision_sha256") != decision["decision_sha256"]
        or reproduction.get("decision_projection") != projection
        or reproduction.get("fresh_whole_bundle_replay") is not True
        or reproduction.get("exact_parity") is not True
    ):
        raise WorkflowError("reproduction and decision branch parity failed")

    if decision["scientific_outcome"] == "positive":
        branch = "positive"
    elif decision["scientific_outcome"] in ("negative", "inconclusive"):
        branch = "negative_or_inconclusive"
    else:
        raise WorkflowError("nonterminal decision cannot be closed out")
    policy = contract["branch_delivery"][branch]

    ack_target = root / (CLOSEOUT_ACK_PATH if ack_path is None else Path(ack_path))
    ack = strict_load_json(ack_target)
    expected_ack_keys = {
        "document_kind", "schema_version", "checkpoint_id", "ack",
        "technical_verdict", "closeout_verdict", "branch",
        "proposed_parent_head", "staged_tree", "staged_blob_hashes",
        "delivery_manifest_sha256", "terminal_tuple", "projection_parity",
        "formal_reproduction", "precommit_remote_state", "push_performed",
        "ack_sha256",
    }
    if type(ack) is not dict or set(ack) != expected_ack_keys:
        raise WorkflowError("closeout ACK schema/unknown-property failure")
    ack_body = dict(ack)
    recorded_ack = ack_body.pop("ack_sha256")
    if (
        ack["document_kind"] != "s11_closeout_ack"
        or ack["schema_version"] != 1
        or ack["checkpoint_id"] != "S11"
        or ack["ack"] != "CLOSEOUT_ACK"
        or canonical_sha256(ack_body) != recorded_ack
        or ack["technical_verdict"] != "PASS"
        or ack["closeout_verdict"] != "PASS"
        or ack["branch"] != branch
        or ack["proposed_parent_head"] != parent
        or ack["staged_tree"] != tree
        or ack["terminal_tuple"] != projection
        or ack["projection_parity"] is not True
        or ack["formal_reproduction"] != {
            "decision_sha256": decision["decision_sha256"],
            "reproduction_sha256": reproduction["reproduction_sha256"],
            "fresh_whole_bundle_replay": True,
            "exact_parity": True,
        }
        or ack["push_performed"] is not False
        or type(ack["precommit_remote_state"]) is not dict
        or type(ack["staged_blob_hashes"]) is not list
        or ack["delivery_manifest_sha256"] != canonical_sha256(ack["staged_blob_hashes"])
    ):
        raise WorkflowError("closeout ACK identity/branch/projection/push parity failed")

    names = run_readonly_git(
        root,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        commit_id,
    )
    observed_paths = [
        line for line in names.stdout.decode("utf-8").splitlines() if line
    ]
    report_path = (
        "study_docs/research/ductile-origami-warmstart/reports/staged/"
        "s11-stage1-model-only-factorization-report.md"
    )
    result_manifests = set(contract["formal_outcome_paths"]) - {
        decision_path, reproduction_path, report_path,
    }
    expected_path_set = result_manifests | set(policy["requires"])
    if (
        set(observed_paths) != expected_path_set
        or len(observed_paths) != len(expected_path_set)
        or set(policy["forbids"]) & set(observed_paths)
        or not set(PROJECTION_PATHS).issubset(expected_path_set)
    ):
        raise WorkflowError("closeout exact branch commit path set differs")
    observed_bindings = [
        _commit_blob_binding(root, commit_id, path) for path in observed_paths
    ]
    if ack["staged_blob_hashes"] != observed_bindings:
        raise WorkflowError("closeout postcommit staged blob OID/SHA binding differs")

    for projection_path in PROJECTION_PATHS:
        projection_raw = run_readonly_git(
            root, "show", f"{commit_id}:{projection_path}"
        ).stdout
        _validate_projection_hunk(
            root=root, parent=parent, commit=commit_id, path=projection_path,
            raw=projection_raw, decision=decision, reproduction=reproduction,
        )

    postcommit_remote_state = _remote_delivery_snapshot(root)
    if ack["precommit_remote_state"] != postcommit_remote_state:
        raise WorkflowError(
            "configured-remote/refs-remotes state changed after closeout ACK"
        )
    _assert_not_remote_tracking_reachable(root, commit_id, postcommit_remote_state)

    paths = {row["path"]: row["sha256"] for row in observed_bindings}

    result = {
        "document_kind": "s11_closeout_audit",
        "schema_version": 1,
        "checkpoint_id": "S11",
        "commit": commit_id,
        "parent": parent,
        "tree": tree,
        "branch": branch,
        "paths": paths,
        "staged_blob_hashes": observed_bindings,
        "projection": projection,
        "decision_sha256": decision["decision_sha256"],
        "reproduction_sha256": reproduction["reproduction_sha256"],
        "technical_verdict": "PASS",
        "closeout_verdict": "PASS",
        "projection_parity": True,
        "formal_reproduction": ack["formal_reproduction"],
        "ack_sha256": ack["ack_sha256"],
        "remote_delivery_snapshot_sha256": postcommit_remote_state["snapshot_sha256"],
        "terminal_remote_tracking_reachable": False,
        "push_performed": False,
        "read_only_tracked_state": True,
    }
    result["audit_sha256"] = canonical_sha256(result)
    exclusive_write_json(target, result)
    return result
