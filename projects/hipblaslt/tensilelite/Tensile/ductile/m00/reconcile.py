# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Raw-only reconstruction of M00 run summaries."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import math
import pickle

import numpy as np

from .artifacts import (
    ArtifactLayout,
    ChecksumManifest,
    generated_input_inventory,
)
from .canonical import (
    ContractError,
    MissingEvidenceError,
    canonical_json_bytes,
    load_json_strict,
    sha256_bytes,
    sha256_file,
    validate_instance,
)
from .contract import ContractStore
from .events import LifecycleTracker, read_jsonl_events


TERMINAL_CLASSES = (
    "invalid", "duplicate", "compile_failed", "benchmark_failed",
    "partial", "complete",
)


def _missing(message: str, reason: str) -> MissingEvidenceError:
    return MissingEvidenceError(message, reason_code=reason)


def _strict_json_lines(path: Path, schema: dict[str, Any]) -> list[dict[str, Any]]:
    records = []

    def hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key {key}")
            result[key] = value
        return result

    try:
        with path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    raise ValueError(f"blank line {line_number}")
                value = json.loads(line, object_pairs_hook=hook)
                validate_instance(value, schema, label=f"{path}:{line_number}")
                records.append(value)
    except MissingEvidenceError:
        raise
    except Exception as exc:
        raise _missing(
            f"invalid typed JSONL {path}: {exc}", "TYPED_JSONL_INVALID"
        ) from exc
    return records


def _candidate_set_sha(candidate_ids: list[str]) -> str:
    return sha256_bytes(canonical_json_bytes(candidate_ids))


def verify_terminal_classifications(
        candidate_ids: list[str],
        shape_ids: list[str],
        observations: list[dict[str, Any]],
        terminal_payloads: list[dict[str, Any]],
        compile_status: dict[str, str],
        benchmark_status: dict[str, str]) -> Counter:
    """Verify terminal labels from explicit observations and stage outcomes."""
    by_pair = defaultdict(list)
    for observation in observations:
        by_pair[(observation["candidate_id"], observation["shape_id"])].append(
            observation
        )
    terminal_by_id = defaultdict(list)
    for payload in terminal_payloads:
        terminal_by_id[payload["candidate_id"]].append(payload)
    if set(terminal_by_id) != set(candidate_ids) or any(
            len(values) != 1 for values in terminal_by_id.values()):
        raise _missing(
            "candidate terminal classifications are incomplete",
            "CANDIDATE_TERMINAL_MISSING",
        )
    zero_cost_duplicates = {
        candidate_id for candidate_id, payloads in terminal_by_id.items()
        if payloads[0]["classification"] == "duplicate" and
        {
            "config_id", "config", "duplicate_of_candidate_id",
            "duplicate_of_config_id",
        }.issubset(payloads[0])
    }
    expected_pairs = {
        (candidate_id, shape_id)
        for candidate_id in candidate_ids
        if candidate_id not in zero_cost_duplicates
        for shape_id in shape_ids
    }
    if set(by_pair) != expected_pairs or any(
            len(records) != 1 for records in by_pair.values()):
        raise _missing(
            "terminal classification lacks an exact observation matrix",
            "TERMINAL_OBSERVATION_MATRIX_INVALID",
        )

    counts = Counter({name: 0 for name in TERMINAL_CLASSES})
    for candidate_id in candidate_ids:
        outcomes = (
            [] if candidate_id in zero_cost_duplicates else [
                by_pair[(candidate_id, shape_id)][0]["outcome"]
                for shape_id in shape_ids
            ]
        )
        compile_result = compile_status.get(candidate_id, "not_attempted")
        benchmark_result = benchmark_status.get(
            candidate_id, "not_attempted"
        )
        if candidate_id in zero_cost_duplicates and not outcomes and \
                compile_result == benchmark_result == "not_attempted":
            expected = "duplicate"
        elif all(outcome == "duplicate" for outcome in outcomes) and \
                compile_result == benchmark_result == "not_attempted":
            expected = "duplicate"
        elif all(outcome == "invalid" for outcome in outcomes) and \
                compile_result == benchmark_result == "not_attempted":
            expected = "invalid"
        elif all(outcome == "compile_failed" for outcome in outcomes) and \
                compile_result == "failure" and \
                benchmark_result == "not_attempted":
            expected = "compile_failed"
        elif all(outcome == "benchmark_failed" for outcome in outcomes) and \
                compile_result == "success" and \
                benchmark_result == "failure":
            expected = "benchmark_failed"
        elif all(outcome == "success" for outcome in outcomes) and \
                compile_result == benchmark_result == "success":
            expected = "complete"
        elif any(outcome == "success" for outcome in outcomes) and \
                all(outcome in {
                    "success", "partial", "benchmark_failed"
                } for outcome in outcomes) and \
                compile_result == "success" and \
                benchmark_result in {"success", "failure"}:
            expected = "partial"
        else:
            raise _missing(
                f"candidate {candidate_id} has an unexplained stage/outcome "
                "combination",
                "TERMINAL_CLASSIFICATION_UNEXPLAINED",
            )
        actual = terminal_by_id[candidate_id][0]["classification"]
        if actual != expected:
            raise _missing(
                f"candidate {candidate_id} terminal classification mismatch: "
                f"expected {expected}, got {actual}",
                "TERMINAL_CLASSIFICATION_MISMATCH",
            )
        counts[actual] += 1
    return counts


def verify_complete_fitness_vector(
        candidate_ids: list[str],
        shape_ids: list[str],
        observations: list[dict[str, Any]],
        vector_payload: dict[str, Any], *,
        allow_partial: bool = False,
        zero_cost_candidate_ids: set[str] | None = None
        ) -> tuple[int, int, int]:
    """Validate exact order/value/bytes and return complete/partial/positive."""
    zero_cost_candidate_ids = zero_cost_candidate_ids or set()
    if not zero_cost_candidate_ids.issubset(candidate_ids):
        raise _missing(
            "zero-cost fitness candidate is unknown",
            "FITNESS_ZERO_COST_CANDIDATE_INVALID",
        )
    by_pair = defaultdict(list)
    for observation in observations:
        by_pair[(observation["candidate_id"], observation["shape_id"])].append(
            observation
        )
    expected_pairs = {
        (candidate_id, shape_id)
        for candidate_id in candidate_ids
        if candidate_id not in zero_cost_candidate_ids
        for shape_id in shape_ids
    }
    if set(by_pair) != expected_pairs or any(
            len(records) != 1 for records in by_pair.values()):
        raise _missing(
            "fitness vector contains incomplete candidate observations",
            "PARTIAL_FITNESS_VECTOR",
        )
    matrix = []
    complete = 0
    partial = 0
    partial_positive = 0
    for shape_id in shape_ids:
        row = []
        for candidate_id in candidate_ids:
            if candidate_id in zero_cost_candidate_ids:
                row.append(-1.0)
                continue
            records = by_pair[(candidate_id, shape_id)]
            record = records[0]
            if record["outcome"] != "success" or \
                    record["value"] is None or \
                    not math.isfinite(record["value"]):
                row.append(-1.0)
                continue
            row.append(float(record["value"]))
        matrix.append(row)

    for candidate_index, candidate_id in enumerate(candidate_ids):
        values = [
            matrix[shape_index][candidate_index]
            for shape_index in range(len(shape_ids))
        ]
        present = [value for value in values if value > 0]
        if len(present) == len(shape_ids):
            complete += 1
        elif present:
            partial += 1
            if any(value > 0 for value in present):
                partial_positive += 1

    if not allow_partial and complete != len(candidate_ids):
        raise _missing(
            "fitness vector contains incomplete candidate observations",
            "PARTIAL_FITNESS_VECTOR",
        )
    array = np.asarray(matrix, dtype=np.float64)
    expected_dtype = array.dtype.str
    expected_shape = list(array.shape)
    if vector_payload.get("candidate_ids") != candidate_ids or \
            vector_payload.get("shape_ids") != shape_ids or \
            vector_payload.get("dtype") != expected_dtype or \
            vector_payload.get("shape") != expected_shape or \
            vector_payload.get("values") != array.tolist() or \
            vector_payload.get("data_sha256") != sha256_bytes(
                array.tobytes(order="C")
            ):
        raise _missing(
            "raw fitness vector does not match typed observations",
            "FITNESS_VECTOR_MISMATCH",
        )
    positive = sum(
        any(array[shape_index, candidate_index] > 0
            for shape_index in range(len(shape_ids)))
        for candidate_index in range(len(candidate_ids))
    )
    return complete, partial, positive


def _verify_observer_stream(
        path: Path,
        schema_path: Path,
        manifest: dict[str, Any],
        trajectory: dict[str, Any]) -> None:
    if manifest["observer_mode"] == "off":
        disabled = load_json_strict(path)
        if disabled != {"schema_version": "1.0", "observer": "disabled"}:
            raise _missing(
                "observer-off metadata is not explicit and exact",
                "OBSERVER_DISABLED_METADATA_INVALID",
            )
        return

    events = read_jsonl_events(path, schema_path=schema_path)
    if not events:
        raise _missing(
            "enabled observer event stream is empty",
            "OBSERVER_EVENTS_MISSING",
        )
    by_kind = defaultdict(list)
    for record, payload in events:
        by_kind[record["kind"]].append((record, payload))
    generations = trajectory["generations"]
    expected_count = len(generations)
    resumed = manifest["run_kind"] in {
        "resumed", "adversarial_resumed"
    }
    exact_counts = {
        "initial_population": 1,
        "resume_loaded": 1 if resumed else 0,
        "proposal_batch": expected_count,
        "fitness_matrix": expected_count,
        "generation_stats": expected_count,
        "checkpoint_written": expected_count,
        "termination": 1,
        "final_champion": 1,
    }
    bad_counts = {
        kind: (len(by_kind[kind]), expected)
        for kind, expected in exact_counts.items()
        if len(by_kind[kind]) != expected
    }
    if bad_counts:
        raise _missing(
            f"observer lifecycle coverage mismatch: {bad_counts}",
            "OBSERVER_EVENT_COVERAGE_MISSING",
        )

    initial = by_kind["initial_population"][0][1]
    first = generations[0]
    if initial["ordered_indices"] != first["ordered_indices"] or \
            initial["ordered_configs"] != first["ordered_configs"]:
        raise _missing(
            "observer initial population differs from raw trajectory",
            "OBSERVER_INITIAL_POPULATION_MISMATCH",
        )

    proposal_by_generation = {
        record["generation"]: payload
        for record, payload in by_kind["proposal_batch"]
    }
    fitness_by_generation = {
        record["generation"]: payload
        for record, payload in by_kind["fitness_matrix"]
    }
    stats_by_generation = {
        record["generation"]: payload
        for record, payload in by_kind["generation_stats"]
    }
    expected_generations = {
        item["generation"] for item in generations
    }
    if set(proposal_by_generation) != expected_generations or \
            set(fitness_by_generation) != expected_generations or \
            set(stats_by_generation) != expected_generations:
        raise _missing(
            "observer generation identity coverage is incomplete",
            "OBSERVER_GENERATION_COVERAGE_MISSING",
        )
    for index, generation in enumerate(generations):
        number = generation["generation"]
        proposal = proposal_by_generation[number]
        observed_fitness = fitness_by_generation[number]
        expected_fitness = generation["fitness"]
        stats = stats_by_generation[number]
        if proposal["ordered_indices"] != generation["ordered_indices"] or \
                proposal["ordered_configs"] != generation["ordered_configs"]:
            raise _missing(
                f"observer proposal mismatch at generation {number}",
                "OBSERVER_PROPOSAL_MISMATCH",
            )
        if observed_fitness != {
                key: expected_fitness[key]
                for key in ("dtype", "shape", "values", "data_sha256")
        }:
            raise _missing(
                f"observer fitness mismatch at generation {number}",
                "OBSERVER_FITNESS_MISMATCH",
            )
        for key in ("f_avg", "f_max", "diversity"):
            if stats[key] != trajectory["stats"][key][index]:
                raise _missing(
                    f"observer {key} mismatch at generation {number}",
                    "OBSERVER_STATS_MISMATCH",
                )

    termination_record, termination = by_kind["termination"][-1]
    champion_record, champion = by_kind["final_champion"][-1]
    if termination_record["generation"] != trajectory["final_generation"] or \
            termination["reason"] != trajectory["termination_reason"]:
        raise _missing(
            "observer termination differs from raw trajectory",
            "OBSERVER_TERMINATION_MISMATCH",
        )
    if champion_record["generation"] != trajectory["final_generation"] or \
            champion["configs"] != trajectory["champion"] or \
            champion["fitness"] != trajectory["champion_fitness"] or \
            champion["fitness_dtype"] != \
            trajectory["champion_fitness_dtype"] or \
            champion["fitness_sha256"] != \
            trajectory["champion_fitness_sha256"]:
        raise _missing(
            "observer champion differs from raw trajectory",
            "OBSERVER_CHAMPION_MISMATCH",
        )


@dataclass(frozen=True)
class ReconciledSummary:
    schema_version: str
    run_id: str
    complete: bool
    generations_started: int
    generations_finished: int
    proposed_candidates: int
    valid_unique: int
    terminal_counts: dict[str, int]
    compile_attempts: int
    compile_failures: int
    benchmark_attempts: int
    benchmark_failures: int
    subprocess_invocations: int
    subprocess_failures: int
    candidate_shape_samples: int
    ductile_legacy_positive_candidate_evals: int
    complete_candidate_evals: int
    partial_candidate_evals: int
    partial_positive_candidate_evals: int
    checkpoint_count: int
    checkpoint_generation: int
    final_generation: int
    f_avg_sequence: list[float]
    f_max_sequence: list[float]
    population_size_sequence: list[int]
    decay_mode_sequence: list[str]
    diversity_sequence: list[float]
    champion_hash: str
    champion_fitness_sha256: str
    termination_reason: str
    stage_timing_ns: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RawReconciler:
    def __init__(self, run_root: str | Path, contract_path: str | Path):
        self.root = Path(run_root)
        self.store = ContractStore(contract_path)
        self.schemas = self.store.protocol_root / "schemas"
        self.layout = ArtifactLayout()
        self.generated_input_layout = None
        self.generated_input_files: tuple[Path, ...] = ()

    def _path(self, relative: str) -> Path:
        path = self.root / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts or \
                path.is_symlink() or not path.resolve(strict=False).is_relative_to(
                    self.root.resolve()
                ):
            raise _missing(
                f"artifact path invalid: {relative}", "ARTIFACT_PATH_INVALID"
            )
        return path

    def _required(self, *, expect_summary: bool,
                  expect_checksums: bool) -> None:
        required = list(self.layout.required_files)
        if not expect_summary:
            required.remove(self.layout.summary)
        if not expect_checksums:
            required.remove(self.layout.checksums)
        missing = [relative for relative in required
                   if not self._path(relative).is_file()]
        try:
            self.generated_input_layout, self.generated_input_files = \
                generated_input_inventory(self.root)
        except MissingEvidenceError:
            missing.append("recognized generated-input inventory")
        stdout = list(self._path("subprocess").glob(
            "invocation-*.stdout.jsonl"
        ))
        stderr = list(self._path("subprocess").glob(
            "invocation-*.stderr.txt"
        ))
        if not stdout or len(stdout) != len(stderr):
            missing.append("paired subprocess artifacts")
        if missing:
            raise _missing(
                f"required raw artifact missing: {sorted(missing)}",
                "REQUIRED_ARTIFACT_MISSING",
            )

    def _load_schema_json(self, relative: str, schema_name: str):
        try:
            value = load_json_strict(self._path(relative))
            validate_instance(
                value,
                load_json_strict(self.schemas / schema_name),
                label=relative,
            )
        except ContractError as exc:
            raise _missing(
                f"required raw JSON artifact is missing or invalid: "
                f"{relative}: {exc}",
                "REQUIRED_JSON_ARTIFACT_INVALID",
            ) from exc
        return value

    def _verify_contract_copy(self, manifest: dict[str, Any]) -> None:
        copied_base = self._path("contract/experiment-contract.yaml")
        copied_effective = self._load_schema_json(
            "contract/effective-contract.json",
            "experiment-contract.schema.json",
        )
        if sha256_file(copied_base) != self.store.base_file_sha256 or \
                copied_effective != self.store.effective_contract or \
                manifest["contract_sha256"] != \
                self.store.base_canonical_sha256 or \
                manifest["effective_contract_sha256"] != \
                self.store.effective_sha256:
            raise _missing(
                "run contract copy or manifest binding mismatch",
                "RUN_CONTRACT_MISMATCH",
            )
        copies = {
            "shape-registry.csv": self.store.base_contract["locks"][
                "registry_paths"
            ]["shape"],
            "baseline-registry.json": self.store.base_contract["locks"][
                "registry_paths"
            ]["baseline"],
            "revision-registry.json": self.store.base_contract["locks"][
                "registry_paths"
            ]["revision"],
            "protocol-lock.json": self.store.base_contract["locks"][
                "protocol_lock_path"
            ],
            "amendment-chain.jsonl": self.store.base_contract["study"][
                "amendment_chain_path"
            ],
        }
        repo_root = self.store.protocol_root.parents[3]
        for name, relative in copies.items():
            original = repo_root / relative
            copied = self._path(f"contract/{name}")
            if sha256_file(original) != sha256_file(copied):
                raise _missing(
                    f"run contract artifact differs: {name}",
                    "RUN_CONTRACT_COPY_MISMATCH",
                )
        protocol_lock = load_json_strict(
            repo_root / copies["protocol-lock.json"]
        )
        revision_registry = load_json_strict(
            repo_root / copies["revision-registry.json"]
        )
        parent_ids = [
            item["object_id"] for item in revision_registry["entries"]
            if item["kind"] == "parent_commit"
        ]
        locked_ids = [
            item["object_id"] for item in revision_registry["entries"]
            if item["kind"] == "locked_commit"
        ]
        if parent_ids != [manifest["parent_commit"]] or \
                locked_ids != [manifest["locked_ductile_object"]] or \
                manifest["source_set_sha256"] != \
                protocol_lock["m00_source_set_sha256"]:
            raise _missing(
                "run manifest revision/source provenance mismatch",
                "RUN_PROVENANCE_MISMATCH",
            )

    def _checkpoint(self, metadata: dict[str, Any]):
        checkpoint = self._path(self.layout.checkpoint)
        if sha256_file(checkpoint) != metadata["checkpoint_sha256"]:
            raise _missing(
                "checkpoint metadata hash mismatch",
                "CHECKPOINT_HASH_MISMATCH",
            )
        try:
            with checkpoint.open("rb") as stream:
                state = pickle.load(stream)
        except Exception as exc:
            raise _missing(
                f"checkpoint decode failed: {exc}",
                "CHECKPOINT_DECODE_FAILED",
            ) from exc
        required = {
            "gen", "soo", "space_map", "stats", "best", "n_evals",
            "old_pop", "pop", "pop_size", "_pop_size", "decay_type",
            "random_state", "np_random_state", "seed_sequence_state",
            "protocol_lineage",
        }
        if not isinstance(state, dict) or set(state) != required:
            raise _missing(
                "checkpoint field set is invalid",
                "CHECKPOINT_FIELDS_INVALID",
            )
        projection = metadata["projection"]
        champion_configs = [{
            key: state["space_map"][key][value]
            for key, value in individual.X.items()
        } for individual in state["best"]]
        champion_fitness = np.asarray(
            [individual.F for individual in state["best"]],
            dtype=np.float64,
        )
        expected_projection = {
            "generation": int(state["gen"]),
            "legacy_n_evals": int(state["n_evals"]),
            "population_size": len(state["pop"]),
            "decay_mode": state["decay_type"],
            "champion_hash": sha256_bytes(canonical_json_bytes(
                champion_configs
            )),
            "champion_fitness_sha256": sha256_bytes(
                champion_fitness.tobytes(order="C")
            ),
        }
        if projection != expected_projection:
            raise _missing(
                "checkpoint canonical projection mismatch",
                "CHECKPOINT_PROJECTION_MISMATCH",
            )
        if metadata["python_random_state_sha256"] != sha256_bytes(
                canonical_json_bytes(_state_plain(state["random_state"]))
        ) or metadata["numpy_random_state_sha256"] != sha256_bytes(
                canonical_json_bytes(_state_plain(state["np_random_state"]))
        ):
            raise _missing(
                "checkpoint RNG state hash mismatch",
                "CHECKPOINT_RNG_MISMATCH",
            )
        expected_lineage = metadata["protocol_lineage"]
        if state["protocol_lineage"] != expected_lineage or \
                _state_plain(state["seed_sequence_state"]) != \
                metadata["seed_sequence_state"]:
            raise _missing(
                "checkpoint protocol or SeedSequence lineage mismatch",
                "CHECKPOINT_LINEAGE_MISMATCH",
            )
        return state

    def reconcile(self, *, verify_checksums: bool = True,
                  write_summary: bool = False) -> ReconciledSummary:
        self._required(
            expect_summary=not write_summary,
            expect_checksums=verify_checksums,
        )
        if verify_checksums:
            ChecksumManifest.verify(self.root)

        manifest = self._load_schema_json(
            self.layout.manifest, "run-manifest.schema.json"
        )
        environment = self._load_schema_json(
            self.layout.environment, "environment.schema.json"
        )
        search_space = self._load_schema_json(
            self.layout.search_space, "search-space.schema.json"
        )
        checkpoint_metadata = self._load_schema_json(
            self.layout.checkpoint_metadata,
            "checkpoint-metadata.schema.json",
        )
        self._verify_contract_copy(manifest)
        if manifest["scenario_id"] == "adversarial_ledger":
            return self._reconcile_adversarial(
                manifest, environment, search_space,
                checkpoint_metadata,
                write_summary=write_summary,
            )
        expected_space = self.store.effective_contract["search"]["space"]
        expected_shapes = [
            shape["shape_id"] for shape in self.store.effective_contract[
                "measurement"
            ]["cpu_fixture"]["shapes"]
        ]
        revision_path = self.store.protocol_root.parents[3] / \
            self.store.base_contract["locks"]["registry_paths"]["revision"]
        repo_root = self.store.protocol_root.parents[3]
        locks = self.store.base_contract["locks"]
        lock_path = repo_root / locks["protocol_lock_path"]
        lock = load_json_strict(lock_path)
        profile = self.store.profile(manifest["scenario_id"])
        expected_lineage = {
            "schema_version": "1.0",
            "scenario_id": manifest["scenario_id"],
            "seed": profile.seed,
            "n_gen": profile.n_gen,
            "split_generation": profile.split_generation,
            "contract_sha256": self.store.base_canonical_sha256,
            "effective_contract_sha256": self.store.effective_sha256,
            "split_registry_sha256": sha256_file(
                repo_root / locks["registry_paths"]["shape"]
            ),
            "baseline_registry_sha256": sha256_file(
                repo_root / locks["registry_paths"]["baseline"]
            ),
            "revision_registry_sha256": sha256_file(revision_path),
            "protocol_lock_sha256": sha256_file(lock_path),
            "source_set_sha256": lock["m00_source_set_sha256"],
        }
        if environment["contract_sha256"] != \
                self.store.base_canonical_sha256 or \
                environment["revision_sha256"] != \
                sha256_file(revision_path) or \
                search_space["ordered_genes"] != expected_space or \
                search_space["ordered_shape_ids"] != expected_shapes or \
                search_space["search_space_sha256"] != sha256_bytes(
                    canonical_json_bytes(expected_space)
                ) or checkpoint_metadata["protocol_lineage"] != \
                expected_lineage:
            raise _missing(
                "environment or search-space provenance mismatch",
                "RUN_CONTEXT_MISMATCH",
            )

        event_schema = self.schemas / "ga-event.schema.json"
        events = read_jsonl_events(self._path(self.layout.ga_events),
                                   schema_path=event_schema)
        if not events:
            raise _missing("GA event stream is empty", "RUN_EVENTS_MISSING")
        kinds = [record["kind"] for record, payload in events]
        if kinds[0] != "run_started" or kinds[-1] != "run_finished" or \
                kinds.count("run_started") != 1 or \
                kinds.count("run_finished") != 1:
            raise _missing(
                "run lifecycle is not exactly paired",
                "RUN_LIFECYCLE_UNPAIRED",
            )
        run_start = events[0][1]
        run_finish = events[-1][1]
        if not run_finish.get("complete") or \
                not manifest["complete"] or \
                run_start["expected_stages"] != [
                    "compile", "benchmark", "subprocess"
                ]:
            raise _missing(
                "run capabilities or complete closure missing",
                "RUN_CAPABILITY_MISSING",
            )
        interruption_count = kinds.count("run_interrupted")
        if manifest["run_kind"] == "resumed":
            if interruption_count != 1 or \
                    manifest["resume_from_sha256"] is None:
                raise _missing(
                    "resumed run lacks one durable interruption lineage",
                    "RESUME_LIFECYCLE_INVALID",
                )
        elif interruption_count != 0 or \
                manifest["resume_from_sha256"] is not None:
            raise _missing(
                "continuous run contains resume-only lifecycle state",
                "RESUME_LIFECYCLE_INVALID",
            )

        observation_schema = load_json_strict(
            self.schemas / "benchmark-observation.schema.json"
        )
        observations = _strict_json_lines(
            self._path(self.layout.observations), observation_schema
        )
        observation_ids = [
            observation["observation_id"] for observation in observations
        ]
        if len(observation_ids) != len(set(observation_ids)):
            raise _missing(
                "duplicate observation ID",
                "OBSERVATION_ID_DUPLICATE",
            )
        by_generation_obs = defaultdict(list)
        for observation in observations:
            if observation["run_id"] != manifest["run_id"]:
                raise _missing(
                    "observation run ID mismatch",
                    "OBSERVATION_RUN_MISMATCH",
                )
            by_generation_obs[observation["generation"]].append(observation)

        generation_starts = {}
        generation_finishes = {}
        vector_events = {}
        stats_events = {}
        terminal_by_generation = defaultdict(list)
        lifecycle = LifecycleTracker()
        stage_attempts = Counter()
        stage_failures = Counter()
        stage_timing = Counter()
        stage_starts = {}
        stage_finishes = {}
        stage_candidates = defaultdict(list)
        stage_status = defaultdict(dict)
        checkpoint_events = []
        all_stage_ids = set()
        invocation_ids = set()
        for record, payload in events:
            kind = record["kind"]
            generation = record["generation"]
            if kind == "generation_started":
                if generation in generation_starts:
                    raise _missing(
                        "duplicate generation start",
                        "GENERATION_START_DUPLICATE",
                    )
                if payload["candidate_set_sha256"] != _candidate_set_sha(
                        payload["candidate_ids"]):
                    raise _missing(
                        "generation candidate-set hash mismatch",
                        "CANDIDATE_SET_HASH_MISMATCH",
                    )
                generation_starts[generation] = payload
            elif kind == "generation_finished":
                if generation in generation_finishes:
                    raise _missing(
                        "duplicate generation finish",
                        "GENERATION_FINISH_DUPLICATE",
                    )
                generation_finishes[generation] = payload
            elif kind == "fitness_vector":
                if generation in vector_events:
                    raise _missing(
                        "duplicate fitness vector",
                        "FITNESS_VECTOR_DUPLICATE",
                    )
                vector_events[generation] = payload
            elif kind == "generation_stats":
                if generation in stats_events:
                    raise _missing(
                        "duplicate generation stats",
                        "GENERATION_STATS_DUPLICATE",
                    )
                stats_events[generation] = payload
            elif kind == "candidate_terminal":
                terminal_by_generation[generation].append(payload)
            elif kind.endswith("_started") and kind.split("_", 1)[0] in {
                    "compile", "benchmark", "subprocess"}:
                stage = kind.split("_", 1)[0]
                if payload["stage_id"] in all_stage_ids:
                    raise _missing(
                        f"duplicate stage attempt ID: {payload['stage_id']}",
                        "STAGE_ATTEMPT_ID_DUPLICATE",
                    )
                all_stage_ids.add(payload["stage_id"])
                if stage == "subprocess":
                    if payload["invocation_id"] in invocation_ids:
                        raise _missing(
                            "duplicate subprocess invocation ID",
                            "INVOCATION_ID_DUPLICATE",
                        )
                    invocation_ids.add(payload["invocation_id"])
                lifecycle.start(stage, payload["stage_id"])
                key = (stage, payload["stage_id"])
                stage_starts[key] = (generation, payload)
                if stage in {"compile", "benchmark"}:
                    stage_candidates[(stage, generation)].append(
                        payload["candidate_id"]
                    )
                else:
                    stage_candidates[(stage, generation)].append(
                        payload["invocation_id"]
                    )
                stage_attempts[stage] += 1
            elif kind.endswith("_finished") and kind.split("_", 1)[0] in {
                    "compile", "benchmark", "subprocess"}:
                stage = kind.split("_", 1)[0]
                lifecycle.finish(stage, payload["stage_id"])
                key = (stage, payload["stage_id"])
                start_generation, start_payload = stage_starts[key]
                identity_key = (
                    "candidate_id" if stage in {"compile", "benchmark"}
                    else "invocation_id"
                )
                if generation != start_generation or \
                        payload[identity_key] != start_payload[identity_key]:
                    raise _missing(
                        f"{stage} start/finish causal identity mismatch",
                        "STAGE_CAUSAL_MISMATCH",
                    )
                stage_finishes[key] = (generation, payload)
                if stage in {"compile", "benchmark"}:
                    stage_status[(stage, generation)][
                        payload["candidate_id"]
                    ] = payload["status"]
                stage_timing[stage] += payload["duration_ns"]
                if payload["status"] != "success":
                    stage_failures[stage] += 1
            elif kind == "checkpoint_written":
                checkpoint_events.append(payload)
        lifecycle.verify_closed()

        generations = sorted(generation_starts)
        expected_generations = list(range(1, run_finish["final_generation"] + 1))
        if generations != expected_generations or \
                set(generation_finishes) != set(generations) or \
                set(vector_events) != set(generations) or \
                set(stats_events) != set(generations):
            raise _missing(
                "generation lifecycle/vector/stats coverage is incomplete",
                "GENERATION_COVERAGE_MISSING",
            )
        expected_generated_files = {
            f"generation-{generation:04d}.json"
            for generation in generations
        }
        if self.generated_input_layout != "generation" or {
                path.name for path in self.generated_input_files
                } != expected_generated_files:
            raise _missing(
                "healthy generated-input inventory does not exactly match "
                "the generation lifecycle",
                "GENERATED_INPUT_INVENTORY_MISMATCH",
            )

        terminal_counts = Counter({name: 0 for name in TERMINAL_CLASSES})
        total_complete = total_partial = total_positive = 0
        proposed = 0
        for generation in generations:
            started = generation_starts[generation]
            finished = generation_finishes[generation]
            candidate_ids = started["candidate_ids"]
            proposed += len(candidate_ids)
            if finished["candidate_set_sha256"] != \
                    started["candidate_set_sha256"]:
                raise _missing(
                    "generation closure candidate-set mismatch",
                    "GENERATION_CAUSAL_MISMATCH",
                )
            terminals = terminal_by_generation[generation]
            classified = verify_terminal_classifications(
                candidate_ids,
                search_space["ordered_shape_ids"],
                by_generation_obs[generation],
                terminals,
                stage_status[("compile", generation)],
                stage_status[("benchmark", generation)],
            )
            terminal_counts.update(classified)
            for stage in ("compile", "benchmark"):
                if Counter(stage_candidates[(stage, generation)]) != \
                        Counter(candidate_ids):
                    raise _missing(
                        f"{stage} lifecycle does not cover every candidate",
                        "CANDIDATE_STAGE_COVERAGE_MISSING",
                    )
            if len(stage_candidates[("subprocess", generation)]) != 1:
                raise _missing(
                    "generation must have exactly one subprocess lifecycle",
                    "SUBPROCESS_COVERAGE_INVALID",
                )
            complete, partial, positive = verify_complete_fitness_vector(
                candidate_ids,
                search_space["ordered_shape_ids"],
                by_generation_obs[generation],
                vector_events[generation],
            )
            total_complete += complete
            total_partial += partial
            total_positive += positive
            self._verify_generation_artifacts(
                manifest, generation, candidate_ids,
                by_generation_obs[generation],
                stage_starts, stage_finishes,
            )

        checkpoint_state = self._checkpoint(checkpoint_metadata)
        if len(checkpoint_events) < 1 or \
                checkpoint_events[-1]["checkpoint_sha256"] != \
                checkpoint_metadata["checkpoint_sha256"]:
            raise _missing(
                "checkpoint event/sidecar mismatch",
                "CHECKPOINT_EVENT_MISMATCH",
            )
        if checkpoint_state["n_evals"] != total_positive or \
                total_positive != total_complete + 0:
            raise _missing(
                "legacy evaluation count has an unexplained delta",
                "LEGACY_EVAL_DELTA_UNEXPLAINED",
            )

        trajectory = load_json_strict(self._path(self.layout.trajectory))
        checkpoint_champion = [{
            key: checkpoint_state["space_map"][key][value]
            for key, value in individual.X.items()
        } for individual in checkpoint_state["best"]]
        checkpoint_fitness = np.asarray(
            [individual.F for individual in checkpoint_state["best"]],
            dtype=np.float64,
        )
        if trajectory["run_id"] != manifest["run_id"] or \
                trajectory["termination_reason"] != \
                run_finish["termination_reason"] or \
                trajectory["final_generation"] != \
                run_finish["final_generation"] or \
                trajectory["final_generation"] != \
                checkpoint_metadata["projection"]["generation"] or \
                trajectory["checkpoint_sha256"] != \
                checkpoint_metadata["checkpoint_sha256"] or \
                trajectory["champion_hash"] != \
                checkpoint_metadata["projection"]["champion_hash"] or \
                trajectory["champion_fitness_sha256"] != \
                checkpoint_metadata["projection"][
                    "champion_fitness_sha256"
                ] or \
                trajectory["champion"] != checkpoint_champion or \
                trajectory["champion_fitness_dtype"] != \
                checkpoint_fitness.dtype.str or \
                trajectory["champion_fitness"] != \
                checkpoint_fitness.tolist() or \
                sha256_bytes(canonical_json_bytes(
                    trajectory["champion"]
                )) != trajectory["champion_hash"] or \
                sha256_bytes(checkpoint_fitness.tobytes(order="C")) != \
                trajectory["champion_fitness_sha256"] or \
                sha256_bytes(canonical_json_bytes(
                    trajectory["final_python_random_state"]
                )) != checkpoint_metadata[
                    "python_random_state_sha256"
                ] or \
                sha256_bytes(canonical_json_bytes(
                    trajectory["final_numpy_random_state"]
                )) != checkpoint_metadata[
                    "numpy_random_state_sha256"
                ] or \
                trajectory["final_seed_sequence_state"] != \
                checkpoint_metadata["seed_sequence_state"] or \
                trajectory["checkpoint_lineage"] != \
                checkpoint_metadata["protocol_lineage"]:
            raise _missing(
                "trajectory closure mismatch",
                "TRAJECTORY_CLOSURE_MISMATCH",
            )
        _verify_observer_stream(
            self._path(self.layout.observer_events),
            event_schema,
            manifest,
            trajectory,
        )
        stats = [stats_events[generation] for generation in generations]
        valid_unique = sum(
            terminal_counts[key] for key in (
                "compile_failed", "benchmark_failed", "partial", "complete"
            )
        )
        if proposed != terminal_counts["invalid"] + \
                terminal_counts["duplicate"] + valid_unique:
            raise _missing(
                "proposed candidate accounting is not mutually exclusive",
                "CANDIDATE_ACCOUNTING_INVALID",
            )
        summary = ReconciledSummary(
            schema_version="1.0",
            run_id=manifest["run_id"],
            complete=True,
            generations_started=len(generation_starts),
            generations_finished=len(generation_finishes),
            proposed_candidates=proposed,
            valid_unique=valid_unique,
            terminal_counts=dict(terminal_counts),
            compile_attempts=stage_attempts["compile"],
            compile_failures=stage_failures["compile"],
            benchmark_attempts=stage_attempts["benchmark"],
            benchmark_failures=stage_failures["benchmark"],
            subprocess_invocations=stage_attempts["subprocess"],
            subprocess_failures=stage_failures["subprocess"],
            candidate_shape_samples=len(observations),
            ductile_legacy_positive_candidate_evals=total_positive,
            complete_candidate_evals=total_complete,
            partial_candidate_evals=total_partial,
            partial_positive_candidate_evals=0,
            checkpoint_count=len(checkpoint_events),
            checkpoint_generation=int(checkpoint_state["gen"]),
            final_generation=run_finish["final_generation"],
            f_avg_sequence=[item["f_avg"] for item in stats],
            f_max_sequence=[item["f_max"] for item in stats],
            population_size_sequence=[
                item["population_size"] for item in stats
            ],
            decay_mode_sequence=[item["decay_mode"] for item in stats],
            diversity_sequence=[item["diversity"] for item in stats],
            champion_hash=trajectory["champion_hash"],
            champion_fitness_sha256=trajectory[
                "champion_fitness_sha256"
            ],
            termination_reason=run_finish["termination_reason"],
            stage_timing_ns={
                stage: stage_timing[stage]
                for stage in ("compile", "benchmark", "subprocess")
            },
        )
        summary_data = summary.as_dict()
        summary_schema = load_json_strict(
            self.schemas / "summary.schema.json"
        )
        validate_instance(summary_data, summary_schema, label="raw summary")
        summary_path = self._path(self.layout.summary)
        if write_summary:
            if summary_path.exists() or summary_path.is_symlink():
                raise _missing(
                    "summary already exists", "SUMMARY_PREEXISTS"
                )
            with summary_path.open("x", encoding="utf-8") as stream:
                stream.write(
                    canonical_json_bytes(summary_data).decode("utf-8") + "\n"
                )
        else:
            existing = load_json_strict(summary_path)
            validate_instance(existing, summary_schema, label="summary.json")
            if canonical_json_bytes(existing) != canonical_json_bytes(
                    summary_data):
                raise _missing(
                    "summary differs from raw-only reconstruction",
                    "SUMMARY_RECONCILIATION_MISMATCH",
                )
        return summary

    def _reconcile_adversarial(
            self, manifest: dict[str, Any],
            environment: dict[str, Any],
            search_space: dict[str, Any],
            checkpoint_metadata: dict[str, Any], *,
            write_summary: bool) -> ReconciledSummary:
        repo_root = self.store.protocol_root.parents[3]
        locks = self.store.base_contract["locks"]
        revision_path = repo_root / locks["registry_paths"]["revision"]
        lock_path = repo_root / locks["protocol_lock_path"]
        lock = load_json_strict(lock_path)
        profile = self.store.profile("checkpoint_resume")
        expected_lineage = {
            "schema_version": "1.0",
            "scenario_id": "adversarial_ledger",
            "seed": profile.seed,
            "n_gen": profile.n_gen,
            "split_generation": profile.split_generation,
            "contract_sha256": self.store.base_canonical_sha256,
            "effective_contract_sha256": self.store.effective_sha256,
            "split_registry_sha256": sha256_file(
                repo_root / locks["registry_paths"]["shape"]
            ),
            "baseline_registry_sha256": sha256_file(
                repo_root / locks["registry_paths"]["baseline"]
            ),
            "revision_registry_sha256": sha256_file(revision_path),
            "protocol_lock_sha256": sha256_file(lock_path),
            "source_set_sha256": lock["m00_source_set_sha256"],
        }
        expected_space = self.store.effective_contract["search"]["space"]
        shape_ids = [
            shape["shape_id"] for shape in self.store.effective_contract[
                "measurement"
            ]["cpu_fixture"]["shapes"]
        ]
        if environment["contract_sha256"] != \
                self.store.base_canonical_sha256 or \
                environment["revision_sha256"] != \
                sha256_file(revision_path) or \
                search_space["scenario_id"] != "adversarial_ledger" or \
                search_space["ordered_genes"] != expected_space or \
                search_space["ordered_shape_ids"] != shape_ids or \
                checkpoint_metadata["protocol_lineage"] != \
                expected_lineage:
            raise _missing(
                "adversarial run context or lineage mismatch",
                "LEDGER_CONTEXT_MISMATCH",
            )

        event_schema = self.schemas / "ga-event.schema.json"
        events = read_jsonl_events(
            self._path(self.layout.ga_events),
            schema_path=event_schema,
        )
        kinds = [record["kind"] for record, _ in events]
        if not events or kinds[0] != "run_started" or \
                kinds[-1] != "run_finished" or \
                kinds.count("run_started") != 1 or \
                kinds.count("run_finished") != 1:
            raise _missing(
                "adversarial run lifecycle is unpaired",
                "LEDGER_RUN_LIFECYCLE_INVALID",
            )
        interruption_count = kinds.count("run_interrupted")
        if manifest["run_kind"] == "adversarial_resumed":
            if interruption_count != 1 or \
                    manifest["resume_from_sha256"] is None:
                raise _missing(
                    "adversarial resume lineage is missing",
                    "LEDGER_RESUME_LIFECYCLE_INVALID",
                )
        elif manifest["run_kind"] == "adversarial_continuous":
            if interruption_count or \
                    manifest["resume_from_sha256"] is not None:
                raise _missing(
                    "continuous adversarial run contains interruption state",
                    "LEDGER_RESUME_LIFECYCLE_INVALID",
                )
        else:
            raise _missing(
                "invalid complete adversarial run kind",
                "LEDGER_RUN_KIND_INVALID",
            )
        if not manifest["complete"]:
            raise _missing(
                "adversarial manifest is not complete",
                "LEDGER_RUN_INCOMPLETE",
            )

        observation_schema = load_json_strict(
            self.schemas / "benchmark-observation.schema.json"
        )
        observations = _strict_json_lines(
            self._path(self.layout.observations), observation_schema
        )
        observation_ids = [
            item["observation_id"] for item in observations
        ]
        if len(observation_ids) != len(set(observation_ids)) or \
                any(item["run_id"] != manifest["run_id"]
                    for item in observations):
            raise _missing(
                "adversarial observation identity is invalid",
                "LEDGER_OBSERVATION_ID_INVALID",
            )

        generation_starts = [
            payload for record, payload in events
            if record["kind"] == "generation_started"
        ]
        generation_finishes = [
            payload for record, payload in events
            if record["kind"] == "generation_finished"
        ]
        vectors = [
            payload for record, payload in events
            if record["kind"] == "fitness_vector"
        ]
        stats = [
            payload for record, payload in events
            if record["kind"] == "generation_stats"
        ]
        terminals = [
            payload for record, payload in events
            if record["kind"] == "candidate_terminal"
        ]
        candidate_ids = [f"p{index}" for index in range(6)]
        expected_classifications = [
            "complete", "invalid", "duplicate", "compile_failed",
            "benchmark_failed", "partial",
        ]
        if len(generation_starts) != 1 or \
                len(generation_finishes) != 1 or len(vectors) != 1 or \
                len(stats) != 1 or \
                generation_starts[0]["candidate_ids"] != candidate_ids or \
                generation_starts[0]["candidate_set_sha256"] != \
                _candidate_set_sha(candidate_ids) or \
                generation_finishes[0]["candidate_set_sha256"] != \
                _candidate_set_sha(candidate_ids):
            raise _missing(
                "adversarial generation closure is invalid",
                "LEDGER_GENERATION_CLOSURE_INVALID",
            )
        if [item["candidate_id"] for item in terminals] != candidate_ids or \
                [item["classification"] for item in terminals] != \
                expected_classifications:
            raise _missing(
                "adversarial p0-p5 semantic identities are invalid",
                "LEDGER_SEMANTIC_IDENTITY_MISMATCH",
            )

        lifecycle = LifecycleTracker()
        started = {}
        finished = {}
        stage_status = defaultdict(dict)
        stage_attempts = Counter()
        stage_failures = Counter()
        stage_timing = Counter()
        all_stage_ids = set()
        invocation_ids = set()
        for record, payload in events:
            kind = record["kind"]
            if kind.endswith("_started") and kind.split("_", 1)[0] in {
                    "compile", "benchmark", "subprocess"}:
                stage = kind.split("_", 1)[0]
                stable_id = payload["stage_id"]
                if stable_id in all_stage_ids:
                    raise _missing(
                        f"duplicate adversarial attempt ID: {stable_id}",
                        "STAGE_ATTEMPT_ID_DUPLICATE",
                    )
                all_stage_ids.add(stable_id)
                if stage == "subprocess":
                    invocation_id = payload["invocation_id"]
                    if invocation_id in invocation_ids:
                        raise _missing(
                            "duplicate adversarial invocation ID",
                            "INVOCATION_ID_DUPLICATE",
                        )
                    invocation_ids.add(invocation_id)
                lifecycle.start(stage, stable_id)
                started[(stage, stable_id)] = (record, payload)
                stage_attempts[stage] += 1
            elif kind.endswith("_finished") and \
                    kind.split("_", 1)[0] in {
                        "compile", "benchmark", "subprocess"}:
                stage = kind.split("_", 1)[0]
                stable_id = payload["stage_id"]
                lifecycle.finish(stage, stable_id)
                if (stage, stable_id) not in started:
                    raise _missing(
                        "orphan adversarial stage finish",
                        "LEDGER_STAGE_ORPHAN",
                    )
                start_record, start_payload = started[(stage, stable_id)]
                if start_record["sequence"] >= record["sequence"] or \
                        start_record["generation"] != \
                        record["generation"]:
                    raise _missing(
                        "adversarial stage sequence is not causal",
                        "LEDGER_STAGE_SEQUENCE_INVALID",
                    )
                finished[(stage, stable_id)] = (record, payload)
                stage_timing[stage] += payload["duration_ns"]
                if payload["status"] != "success":
                    stage_failures[stage] += 1
                if stage in {"compile", "benchmark"}:
                    if payload["candidate_id"] != \
                            start_payload["candidate_id"]:
                        raise _missing(
                            "adversarial stage candidate mismatch",
                            "LEDGER_STAGE_CAUSAL_MISMATCH",
                        )
                    stage_status[(stage, 1)][
                        payload["candidate_id"]
                    ] = payload["status"]
        lifecycle.verify_closed()

        terminal_counts = verify_terminal_classifications(
            candidate_ids, shape_ids, observations, terminals,
            stage_status[("compile", 1)],
            stage_status[("benchmark", 1)],
        )
        valid_unique = sum(
            terminal_counts[key] for key in (
                "compile_failed", "benchmark_failed", "partial", "complete"
            )
        )
        if 6 != terminal_counts["invalid"] + \
                terminal_counts["duplicate"] + valid_unique or \
                valid_unique != 4:
            raise _missing(
                "adversarial valid-unique accounting is invalid",
                "LEDGER_VALID_UNIQUE_INVALID",
            )
        complete, partial, positive = verify_complete_fitness_vector(
            candidate_ids, shape_ids, observations, vectors[0],
            allow_partial=True,
            zero_cost_candidate_ids={"p2"},
        )
        partial_positive = positive - complete
        if positive != complete + partial_positive or \
                partial_positive != partial:
            raise _missing(
                "adversarial legacy-positive delta is unexplained",
                "LEGACY_EVAL_DELTA_UNEXPLAINED",
            )

        subprocess_starts = {
            payload["invocation_id"]: payload
            for record, payload in events
            if record["kind"] == "subprocess_started"
        }
        subprocess_finishes = {
            payload["invocation_id"]: payload
            for record, payload in events
            if record["kind"] == "subprocess_finished"
        }
        if len(subprocess_starts) != 8 or \
                set(subprocess_starts) != set(subprocess_finishes):
            raise _missing(
                "adversarial subprocess attempt coverage is invalid",
                "LEDGER_SUBPROCESS_COVERAGE_INVALID",
            )
        expected_generated_files = {
            f"{invocation_id}.json"
            for invocation_id in subprocess_starts
        }
        if self.generated_input_layout != "invocation" or {
                path.name for path in self.generated_input_files
                } != expected_generated_files:
            raise _missing(
                "adversarial generated-input inventory does not exactly "
                "match subprocess invocations",
                "GENERATED_INPUT_INVENTORY_MISMATCH",
            )
        generated_candidates = {}
        generated_stages = []
        for invocation_id in sorted(subprocess_starts):
            generated_relative = (
                f"generated-inputs/{invocation_id}.json"
            )
            generated = self._load_schema_json(
                generated_relative, "generated-input.schema.json"
            )
            start_payload = subprocess_starts[invocation_id]
            finish_payload = subprocess_finishes[invocation_id]
            generated_path = self._path(generated_relative)
            stdout_relative = (
                f"subprocess/{invocation_id}.stdout.jsonl"
            )
            stderr_relative = f"subprocess/{invocation_id}.stderr.txt"
            stdout_path = self._path(stdout_relative)
            stderr_path = self._path(stderr_relative)
            if generated["run_id"] != manifest["run_id"] or \
                    generated["scenario_id"] != \
                    "adversarial_ledger" or \
                    generated["invocation_id"] != invocation_id or \
                    len(generated["candidates"]) != 1 or \
                    generated["shapes"] != \
                    self.store.effective_contract["measurement"][
                        "cpu_fixture"
                    ]["shapes"] or \
                    start_payload["input_sha256"] != \
                    sha256_file(generated_path) or \
                    finish_payload["stdout_path"] != stdout_relative or \
                    finish_payload["stdout_sha256"] != \
                    sha256_file(stdout_path) or \
                    finish_payload["stderr_path"] != stderr_relative or \
                    finish_payload["stderr_sha256"] != \
                    sha256_file(stderr_path):
                raise _missing(
                    "adversarial subprocess artifact binding mismatch",
                    "LEDGER_SUBPROCESS_ARTIFACT_MISMATCH",
                )
            candidate = generated["candidates"][0]
            if candidate["config_id"] != sha256_bytes(
                    canonical_json_bytes(candidate["config"])
                    ) or (
                        candidate["candidate_id"] in generated_candidates and
                        generated_candidates[candidate["candidate_id"]] !=
                        candidate
                    ):
                raise _missing(
                    "adversarial generated candidate identity is invalid",
                    "LEDGER_GENERATED_CANDIDATE_INVALID",
                )
            generated_candidates[candidate["candidate_id"]] = candidate
            generated_stages.append((
                candidate["candidate_id"],
                generated["stage"],
                generated["expected_outcome"],
            ))
            expected_exit = 0
            if generated["expected_outcome"] == "compile_failed" and \
                    generated["stage"] == "compile":
                expected_exit = 11
            elif generated["expected_outcome"] == "benchmark_failed" and \
                    generated["stage"] == "benchmark":
                expected_exit = 12
            if finish_payload["exit_code"] != expected_exit or \
                    finish_payload["status"] != (
                        "success" if expected_exit == 0 else "failure"
                    ):
                raise _missing(
                    "adversarial subprocess exit contradicts input",
                    "LEDGER_SUBPROCESS_EXIT_MISMATCH",
                )
            worker_records = _read_worker_stdout(stdout_path)
            linked_observations = [
                item for item in observations
                if item["invocation_id"] == invocation_id
            ]
            worker_observations = [
                item for item in worker_records if "outcome" in item
            ]
            if [_worker_projection(item, strict=True)
                    for item in worker_observations] != [
                        _worker_projection(item)
                        for item in linked_observations
                    ]:
                raise _missing(
                    "adversarial worker stdout differs from observations",
                    "LEDGER_STDOUT_OBSERVATION_MISMATCH",
                )
            for item in linked_observations:
                if item["generated_input_path"] != \
                        generated_relative or \
                        item["generated_input_sha256"] != \
                        sha256_file(generated_path) or \
                        item["stdout_path"] != stdout_relative or \
                        item["stdout_sha256"] != \
                        sha256_file(stdout_path) or \
                        item["stderr_path"] != stderr_relative or \
                        item["stderr_sha256"] != \
                        sha256_file(stderr_path):
                    raise _missing(
                        "adversarial observation link mismatch",
                        "LEDGER_OBSERVATION_LINK_MISMATCH",
                    )
        if generated_stages != [
                ("p0", "compile", "complete"),
                ("p0", "benchmark", "complete"),
                ("p1", "classify", "invalid"),
                ("p3", "compile", "compile_failed"),
                ("p4", "compile", "benchmark_failed"),
                ("p4", "benchmark", "benchmark_failed"),
                ("p5", "compile", "partial"),
                ("p5", "benchmark", "partial"),
                ] or set(generated_candidates) != {
                    "p0", "p1", "p3", "p4", "p5"
                }:
            raise _missing(
                "adversarial subprocess cost does not match p0-p5 semantics",
                "LEDGER_SUBPROCESS_SEMANTIC_MISMATCH",
            )
        duplicate = terminals[2]
        original = generated_candidates["p0"]
        if duplicate["candidate_id"] != "p2" or \
                duplicate["duplicate_of_candidate_id"] != "p0" or \
                duplicate["config"] != original["config"] or \
                duplicate["config_id"] != original["config_id"] or \
                duplicate["duplicate_of_config_id"] != \
                original["config_id"] or \
                duplicate["config_id"] != sha256_bytes(
                    canonical_json_bytes(duplicate["config"])
                ):
            raise _missing(
                "p2 duplicate provenance does not exactly reference p0",
                "LEDGER_DUPLICATE_CAUSAL_MISMATCH",
            )

        checkpoint_path = self._path(self.layout.checkpoint)
        if sha256_file(checkpoint_path) != \
                checkpoint_metadata["checkpoint_sha256"]:
            raise _missing(
                "adversarial checkpoint hash mismatch",
                "LEDGER_CHECKPOINT_HASH_MISMATCH",
            )
        try:
            with checkpoint_path.open("rb") as stream:
                checkpoint_state = pickle.load(stream)
        except Exception as exc:
            raise _missing(
                f"adversarial checkpoint decode failed: {exc}",
                "LEDGER_CHECKPOINT_DECODE_FAILED",
            ) from exc
        classifications = [
            next(
                payload["classification"] for record, payload in events
                if record["kind"] == "candidate_terminal" and
                payload["candidate_id"] == candidate_id
            )
            for candidate_id in candidate_ids
        ]
        if checkpoint_state != {
                "checkpoint_kind": "adversarial_ledger",
                "cursor": 6,
                "run_id": manifest["run_id"],
                "protocol_lineage": expected_lineage,
                "terminal_classifications": classifications,
                "invocation_count": 8,
                "observation_count": len(observations)}:
            raise _missing(
                "adversarial checkpoint state mismatch",
                "LEDGER_CHECKPOINT_STATE_MISMATCH",
            )
        p0_config = generated_candidates["p0"]["config"]
        p0_values = np.asarray([
            next(
                item["value"] for item in observations
                if item["candidate_id"] == "p0" and
                item["shape_id"] == shape_id
            ) for shape_id in shape_ids
        ], dtype=np.float64)
        expected_projection = {
            "generation": 1,
            "legacy_n_evals": positive,
            "population_size": 6,
            "decay_mode": "none",
            "champion_hash": sha256_bytes(canonical_json_bytes([p0_config])),
            "champion_fitness_sha256": sha256_bytes(
                p0_values.tobytes(order="C")
            ),
        }
        if checkpoint_metadata["projection"] != expected_projection or \
                checkpoint_metadata["protocol_lineage"] != \
                expected_lineage:
            raise _missing(
                "adversarial checkpoint metadata mismatch",
                "LEDGER_CHECKPOINT_METADATA_MISMATCH",
            )
        checkpoint_events = [
            payload for record, payload in events
            if record["kind"] == "checkpoint_written"
        ]
        if len(checkpoint_events) != 1 or \
                checkpoint_events[0]["checkpoint_sha256"] != \
                checkpoint_metadata["checkpoint_sha256"]:
            raise _missing(
                "adversarial checkpoint event mismatch",
                "LEDGER_CHECKPOINT_EVENT_MISMATCH",
            )

        trajectory = load_json_strict(self._path(self.layout.trajectory))
        if trajectory != {
                "schema_version": "1.0",
                "run_id": manifest["run_id"],
                "scenario_id": "adversarial_ledger",
                "run_kind": manifest["run_kind"],
                "candidate_ids": candidate_ids,
                "terminal_classifications": classifications,
                "fitness": vectors[0],
                "checkpoint_sha256":
                    checkpoint_metadata["checkpoint_sha256"],
                "checkpoint_lineage": expected_lineage,
                "final_generation": 1,
                "termination_reason": "ledger_complete"}:
            raise _missing(
                "adversarial trajectory closure mismatch",
                "LEDGER_TRAJECTORY_MISMATCH",
            )

        summary = ReconciledSummary(
            schema_version="1.0",
            run_id=manifest["run_id"],
            complete=True,
            generations_started=1,
            generations_finished=1,
            proposed_candidates=6,
            valid_unique=valid_unique,
            terminal_counts=dict(terminal_counts),
            compile_attempts=stage_attempts["compile"],
            compile_failures=stage_failures["compile"],
            benchmark_attempts=stage_attempts["benchmark"],
            benchmark_failures=stage_failures["benchmark"],
            subprocess_invocations=stage_attempts["subprocess"],
            subprocess_failures=stage_failures["subprocess"],
            candidate_shape_samples=sum(
                item["outcome"] == "success" for item in observations
            ),
            ductile_legacy_positive_candidate_evals=positive,
            complete_candidate_evals=complete,
            partial_candidate_evals=partial,
            partial_positive_candidate_evals=partial_positive,
            checkpoint_count=1,
            checkpoint_generation=1,
            final_generation=1,
            f_avg_sequence=[stats[0]["f_avg"]],
            f_max_sequence=[stats[0]["f_max"]],
            population_size_sequence=[stats[0]["population_size"]],
            decay_mode_sequence=[stats[0]["decay_mode"]],
            diversity_sequence=[stats[0]["diversity"]],
            champion_hash=expected_projection["champion_hash"],
            champion_fitness_sha256=expected_projection[
                "champion_fitness_sha256"
            ],
            termination_reason="ledger_complete",
            stage_timing_ns={
                stage: stage_timing[stage]
                for stage in ("compile", "benchmark", "subprocess")
            },
        )
        summary_data = summary.as_dict()
        validate_instance(
            summary_data,
            load_json_strict(self.schemas / "summary.schema.json"),
            label="adversarial raw summary",
        )
        summary_path = self._path(self.layout.summary)
        if write_summary:
            if summary_path.exists() or summary_path.is_symlink():
                raise _missing(
                    "summary already exists", "SUMMARY_PREEXISTS"
                )
            with summary_path.open("x", encoding="utf-8") as stream:
                stream.write(
                    canonical_json_bytes(summary_data).decode("utf-8") +
                    "\n"
                )
        else:
            existing = load_json_strict(summary_path)
            if canonical_json_bytes(existing) != canonical_json_bytes(
                    summary_data):
                raise _missing(
                    "adversarial summary differs from raw reconstruction",
                    "SUMMARY_RECONCILIATION_MISMATCH",
                )
        return summary

    def _verify_generation_artifacts(
            self, manifest: dict[str, Any], generation: int,
            candidate_ids: list[str],
            observations: list[dict[str, Any]],
            stage_starts: dict, stage_finishes: dict) -> None:
        generated_relative = f"generated-inputs/generation-{generation:04d}.json"
        generated = self._load_schema_json(
            generated_relative, "generated-input.schema.json"
        )
        expected_shapes = self.store.effective_contract["measurement"][
            "cpu_fixture"
        ]["shapes"]
        genes = self.store.effective_contract["search"]["space"]
        if generated["run_id"] != manifest["run_id"] or \
                generated["scenario_id"] != manifest["scenario_id"] or \
                generated["evaluator_mode"] != self.store.profile(
                    manifest["scenario_id"]
                ).evaluator_mode or \
                generated["generation"] != generation or \
                generated["shapes"] != expected_shapes or \
                [item["candidate_id"] for item in generated["candidates"]] != \
                candidate_ids:
            raise _missing(
                "generated input does not match generation proposal order",
                "GENERATED_INPUT_CAUSAL_MISMATCH",
            )
        allowed_values = {
            gene["name"]: gene["values"] for gene in genes
        }
        for index, candidate in enumerate(generated["candidates"]):
            config = candidate["config"]
            config_id = sha256_bytes(canonical_json_bytes(config))
            expected_id = (
                f"g{generation:04d}-c{index:04d}-{config_id[:12]}"
            )
            if candidate["config_id"] != config_id or \
                    candidate["candidate_id"] != expected_id or \
                    set(config) != set(allowed_values) or any(
                        value not in allowed_values[name]
                        for name, value in config.items()
                    ):
                raise _missing(
                    "generated candidate identity/config is invalid",
                    "GENERATED_CANDIDATE_INVALID",
                )
        generated_sha = sha256_file(self._path(generated_relative))
        generated_candidates = {
            item["candidate_id"]: item for item in generated["candidates"]
        }
        generated_shape_ids = [
            item["shape_id"] for item in generated["shapes"]
        ]
        invocation_ids = {item["invocation_id"] for item in observations}
        if len(invocation_ids) != 1:
            raise _missing(
                "generation observations do not have one invocation",
                "INVOCATION_PAIRING_INVALID",
            )
        invocation_id = next(iter(invocation_ids))
        subprocess_start = stage_starts.get(("subprocess", invocation_id))
        subprocess_finish = stage_finishes.get(("subprocess", invocation_id))
        if subprocess_start is None or subprocess_finish is None or \
                subprocess_start[1]["input_sha256"] != generated_sha:
            raise _missing(
                "subprocess lifecycle does not bind generated input",
                "SUBPROCESS_INPUT_MISMATCH",
            )
        stdout_relative = (
            f"subprocess/invocation-{generation:04d}.stdout.jsonl"
        )
        stderr_relative = f"subprocess/invocation-{generation:04d}.stderr.txt"
        stdout_path = self._path(stdout_relative)
        stderr_path = self._path(stderr_relative)
        if not stdout_path.is_file() or not stderr_path.is_file():
            raise _missing(
                "subprocess stdout/stderr pair missing",
                "SUBPROCESS_ARTIFACT_MISSING",
            )
        stdout_sha = sha256_file(stdout_path)
        stderr_sha = sha256_file(stderr_path)
        for observation in observations:
            if observation["generated_input_path"] != generated_relative or \
                    observation["generated_input_sha256"] != generated_sha or \
                    observation["stdout_path"] != stdout_relative or \
                    observation["stdout_sha256"] != stdout_sha or \
                    observation["stderr_path"] != stderr_relative or \
                    observation["stderr_sha256"] != stderr_sha or \
                    observation["candidate_id"] not in generated_candidates or \
                    observation["config_id"] != generated_candidates[
                        observation["candidate_id"]
                    ]["config_id"] or \
                    observation["shape_id"] not in generated_shape_ids or \
                    observation["generation"] != generation or \
                    observation["invocation_id"] != invocation_id:
                raise _missing(
                    "observation artifact link/hash mismatch",
                    "OBSERVATION_ARTIFACT_LINK_MISMATCH",
                )
        expected_pairs = {
            (candidate_id, shape_id)
            for candidate_id in candidate_ids
            for shape_id in generated_shape_ids
        }
        actual_pairs = [
            (item["candidate_id"], item["shape_id"])
            for item in observations
        ]
        if len(actual_pairs) != len(set(actual_pairs)) or \
                set(actual_pairs) != expected_pairs:
            raise _missing(
                "observation candidate/shape matrix is incomplete",
                "OBSERVATION_MATRIX_INCOMPLETE",
            )
        finish_payload = subprocess_finish[1]
        if finish_payload["stdout_path"] != stdout_relative or \
                finish_payload["stdout_sha256"] != stdout_sha or \
                finish_payload["stderr_path"] != stderr_relative or \
                finish_payload["stderr_sha256"] != stderr_sha or \
                finish_payload["exit_code"] != 0 or \
                finish_payload["status"] != "success":
            raise _missing(
                "subprocess closure does not bind stdout/stderr",
                "SUBPROCESS_OUTPUT_MISMATCH",
            )
        worker_records = _read_worker_stdout(stdout_path)
        worker_projection = [_worker_projection(item, strict=True)
                             for item in worker_records]
        observation_projection = [_worker_projection(item)
                                  for item in observations]
        if worker_projection != observation_projection:
            raise _missing(
                "typed observations differ from raw worker stdout",
                "STDOUT_OBSERVATION_MISMATCH",
            )


def _state_plain(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, tuple):
        return [_state_plain(item) for item in value]
    if isinstance(value, list):
        return [_state_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _state_plain(item) for key, item in value.items()}
    return value


def _read_worker_stdout(path: Path):
    records = []

    def strict_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate worker key: {key}")
            result[key] = value
        return result

    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                raise ValueError("blank stdout line")
            records.append(json.loads(line, object_pairs_hook=strict_object))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise _missing(
            f"worker stdout is invalid: {exc}", "WORKER_STDOUT_INVALID"
        ) from exc
    return records


def _worker_projection(record, *, strict=False):
    keys = (
        "schema_version", "run_id", "invocation_id", "candidate_id",
        "config_id", "shape_id", "generation", "sample_index", "outcome",
        "value", "failure_reason", "source",
    )
    try:
        if strict and set(record) != set(keys):
            raise KeyError(
                f"unexpected worker fields: {sorted(set(record) - set(keys))}"
            )
        return {key: record[key] for key in keys}
    except KeyError as exc:
        raise _missing(
            f"worker/observation field missing: {exc}",
            "WORKER_RECORD_FIELD_MISSING",
        ) from exc
