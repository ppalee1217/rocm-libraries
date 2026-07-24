# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""M00 CPU-only actual-Ductile runner and verification CLI."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import argparse
import hashlib
import json
import os
import pickle
import random
import shutil
import subprocess
import sys
import time
import uuid

import numpy as np

from ..algorithm import GeneticAlgorithm
from ..algorithm.ga import DurableInterruption
from ..core import (
    Crossover, Mating, Mutation, SearchSpace, Selection, Survival,
)
from ..core.population import Individual
from ..core import space as space_module
from .artifacts import (
    ArtifactLayout,
    ChecksumManifest,
    RunBundleWriter,
    capture_environment,
    generated_input_inventory,
)
from .canonical import (
    ContractError,
    InstrumentationError,
    M00Error,
    MissingEvidenceError,
    ReportLifecycleError,
    canonical_json_bytes,
    canonical_json_text,
    load_json_strict,
    sha256_bytes,
    sha256_file,
    validate_instance,
)
from .contract import ContractStore, ExecutionProfile, ProtocolLock
from .events import GAEvent, JsonlEventSink, thaw_payload
from .reconcile import RawReconciler, _state_plain
from .registries import BaselineRegistry, RevisionRegistry, ShapeRegistry
from .report import (
    render_m00_report,
    validate_criterion_result_binding,
    validate_evidence_file,
    verify_m00_report,
)
from .scope import M00ScopeGuard


PARENT_COMMIT = "8ff9ef002457ac4f11f5f5fe3f60c858d554806c"
LOCKED_DUCTILE_OBJECT = "5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39"
CANONICAL_CONTRACT = (
    Path(__file__).resolve().parents[6]
    / "study_docs/research/ductile-origami-warmstart/protocol/"
    "experiment-contract.yaml"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _repo_root(store: ContractStore) -> Path:
    return store.protocol_root.parents[3]


def _tensilelite_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _schema(store: ContractStore, name: str) -> Path:
    return store.protocol_root / "schemas" / name


def _seed_sequence_from_state(state: dict[str, Any]):
    sequence = np.random.SeedSequence(
        state["entropy"],
        spawn_key=tuple(state["spawn_key"]),
        pool_size=state["pool_size"],
    )
    if state["n_children_spawned"]:
        sequence.spawn(state["n_children_spawned"])
    return sequence


def _checkpoint_plain(value):
    if isinstance(value, Individual):
        return Individual(
            dict(value.X), float(value.F), _checkpoint_plain(value.G)
        )
    if isinstance(value, np.ndarray):
        return _checkpoint_plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: _checkpoint_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_checkpoint_plain(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_checkpoint_plain(item) for item in value)
    return value


def normalize_checkpoint(path: str | Path) -> bytes:
    """Canonicalize equivalent NumPy view graphs without changing values."""
    path = Path(path)
    with path.open("rb") as stream:
        state = pickle.load(stream)
    normalized = pickle.dumps(
        _checkpoint_plain(state), protocol=pickle.HIGHEST_PROTOCOL
    )
    temporary = path.with_name(f".{path.name}.normalize.tmp")
    with temporary.open("xb") as stream:
        stream.write(normalized)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    return normalized


def build_actual_ga(
        contract: dict[str, Any],
        profile: ExecutionProfile,
        evaluate,
        checkpoint_path: str | Path,
        *,
        observer=None,
        n_gen: int | None = None,
        checkpoint_lineage: dict[str, Any] | None = None,
        interrupt_after_generation: int | None = None) -> GeneticAlgorithm:
    search = contract["search"]
    sampling_jobs = search["sampling_jobs"]
    if sampling_jobs != 1:
        raise ContractError(
            "M00 deterministic profile requires sampling_jobs=1",
            reason_code="SAMPLING_JOBS_INVALID",
        )
    space_module.JOBLIB_N_JOBS_OVERRIDE = sampling_jobs
    ordered_space = {
        gene["name"]: list(gene["values"]) for gene in search["space"]
    }
    actual_space = SearchSpace(ordered_space, max_iters=search["max_iters"])
    selection_cfg = search["operators"]["selection"]
    selection = Selection.get(
        selection_cfg["name"],
        k=selection_cfg["k"],
        ratio=selection_cfg["ratio"],
        elitism=selection_cfg["elitism"],
        replacement=selection_cfg["replacement"],
    )
    crossover_cfg = search["operators"]["crossover"]
    crossover = Crossover.get(
        crossover_cfg["name"],
        prob=crossover_cfg["probability"],
        mode=crossover_cfg["mode"],
    )
    mutation = Mutation(
        actual_space,
        prob=search["operators"]["mutation"]["probability"],
    )
    mating = Mating(
        actual_space, selection, crossover, mutation,
        max_iters=search["mating_max_iters"],
    )
    survival = Survival.get(search["operators"]["survival"])
    ga = GeneticAlgorithm(
        actual_space,
        mating,
        evaluate,
        survival=survival,
        pop_size=profile.pop_size,
        n_gen=n_gen if n_gen is not None else profile.n_gen,
        soo=search["soo"],
        period=profile.period,
        tol=profile.tolerance,
        div_thr=profile.diversity_threshold,
        seed=profile.seed,
        verbose=0,
        checkpoint_path=os.fspath(checkpoint_path),
        observer=observer,
        checkpoint_lineage=checkpoint_lineage,
        interrupt_after_generation=interrupt_after_generation,
    )
    return ga


def _checkpoint_lineage(
        store: ContractStore, scenario_id: str,
        profile: ExecutionProfile) -> dict[str, Any]:
    repo = _repo_root(store)
    locks = store.base_contract["locks"]
    lock_path = repo / locks["protocol_lock_path"]
    lock = load_json_strict(lock_path)
    return {
        "schema_version": "1.0",
        "scenario_id": scenario_id,
        "seed": profile.seed,
        "n_gen": profile.n_gen,
        "split_generation": profile.split_generation,
        "contract_sha256": store.base_canonical_sha256,
        "effective_contract_sha256": store.effective_sha256,
        "split_registry_sha256": sha256_file(
            repo / locks["registry_paths"]["shape"]
        ),
        "baseline_registry_sha256": sha256_file(
            repo / locks["registry_paths"]["baseline"]
        ),
        "revision_registry_sha256": sha256_file(
            repo / locks["registry_paths"]["revision"]
        ),
        "protocol_lock_sha256": sha256_file(lock_path),
        "source_set_sha256": lock["m00_source_set_sha256"],
    }


class _ObserverAdapter:
    def __init__(self, sink: JsonlEventSink):
        self.sink = sink

    def __call__(self, event: GAEvent):
        self.sink.emit(
            event.kind, event.generation, thaw_payload(event.payload),
            event_id=f"observer-{self.sink.next_sequence:06d}",
        )


class _FixtureEvaluator:
    def __init__(self, *, writer: RunBundleWriter, event_sink: JsonlEventSink,
                 store: ContractStore, run_id: str, profile: ExecutionProfile,
                 start_generation: int = 1):
        self.writer = writer
        self.event_sink = event_sink
        self.store = store
        self.run_id = run_id
        self.profile = profile
        self.next_generation = start_generation
        self.space = None
        self.observations = []
        self.generations = []

    def __call__(self, configs: list[dict[str, Any]]) -> np.ndarray:
        generation = self.next_generation
        self.next_generation += 1
        py_state = _state_plain(random.getstate())
        np_state = _state_plain(np.random.get_state())
        seed_state = _state_plain(self.space.seed_seq.state)
        genes = self.store.effective_contract["search"]["space"]
        candidate_ids = []
        candidates = []
        ordered_indices = []
        for index, config in enumerate(configs):
            config_id = sha256_bytes(canonical_json_bytes(config))
            candidate_id = f"g{generation:04d}-c{index:04d}-{config_id[:12]}"
            candidate_ids.append(candidate_id)
            candidates.append({
                "candidate_id": candidate_id,
                "config_id": config_id,
                "config": config,
            })
            ordered_indices.append({
                gene["name"]: gene["values"].index(config[gene["name"]])
                for gene in genes
            })
        candidate_set_sha = sha256_bytes(canonical_json_bytes(candidate_ids))
        self.event_sink.emit("generation_started", generation, {
            "candidate_ids": candidate_ids,
            "candidate_set_sha256": candidate_set_sha,
        })
        for candidate_id in candidate_ids:
            stage_id = f"compile-{candidate_id}"
            self.event_sink.emit("compile_started", generation, {
                "stage_id": stage_id, "candidate_id": candidate_id,
            })
            self.event_sink.emit("compile_finished", generation, {
                "stage_id": stage_id, "candidate_id": candidate_id,
                "status": "success", "duration_ns": 0,
            })
            benchmark_id = f"benchmark-{candidate_id}"
            self.event_sink.emit("benchmark_started", generation, {
                "stage_id": benchmark_id, "candidate_id": candidate_id,
            })

        invocation_id = f"invocation-{generation:04d}"
        generated = {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "scenario_id": self.profile.scenario_id,
            "invocation_id": invocation_id,
            "generation": generation,
            "evaluator_mode": self.profile.evaluator_mode,
            "shapes": self.store.effective_contract["measurement"][
                "cpu_fixture"
            ]["shapes"],
            "candidates": candidates,
        }
        generated_relative = (
            f"generated-inputs/generation-{generation:04d}.json"
        )
        generated_path = self.writer.write_json(generated_relative, generated)
        generated_sha = sha256_file(generated_path)
        stdout_relative = (
            f"subprocess/invocation-{generation:04d}.stdout.jsonl"
        )
        stderr_relative = (
            f"subprocess/invocation-{generation:04d}.stderr.txt"
        )
        argv = [
            sys.executable, "-m", "Tensile.ductile.m00.runner",
            "_cpu-worker", "--input", os.fspath(generated_path),
        ]
        self.event_sink.emit("subprocess_started", generation, {
            "stage_id": invocation_id,
            "invocation_id": invocation_id,
            "argv": argv,
            "cwd": os.fspath(_tensilelite_root()),
            "input_sha256": generated_sha,
        })
        environment = os.environ.copy()
        environment["PYTHONHASHSEED"] = self.store.effective_contract[
            "platform"
        ]["m00_execution"]["pythonhashseed"]
        environment["PYTHONPATH"] = os.fspath(_tensilelite_root())
        started = time.monotonic_ns()
        try:
            result = subprocess.run(
                argv,
                cwd=_tensilelite_root(),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=self.store.effective_contract["measurement"][
                    "cpu_fixture"
                ]["timeout_seconds"],
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise MissingEvidenceError(
                f"CPU fixture worker failed: {exc}",
                reason_code="CPU_WORKER_FAILED",
            ) from exc
        duration = time.monotonic_ns() - started
        stdout_path = self.writer.write_bytes(stdout_relative, result.stdout)
        stderr_path = self.writer.write_bytes(stderr_relative, result.stderr)
        stdout_sha = sha256_file(stdout_path)
        stderr_sha = sha256_file(stderr_path)
        status = "success" if result.returncode == 0 else "failure"
        self.event_sink.emit("subprocess_finished", generation, {
            "stage_id": invocation_id,
            "invocation_id": invocation_id,
            "status": status,
            "duration_ns": duration,
            "exit_code": result.returncode,
            "stdout_path": stdout_relative,
            "stdout_sha256": stdout_sha,
            "stderr_path": stderr_relative,
            "stderr_sha256": stderr_sha,
        })
        if result.returncode != 0:
            raise MissingEvidenceError(
                f"CPU worker exited {result.returncode}",
                reason_code="CPU_WORKER_NONZERO",
            )
        worker_records = []
        try:
            for line in result.stdout.decode("utf-8").splitlines():
                worker_records.append(json.loads(line))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MissingEvidenceError(
                f"CPU worker stdout is invalid: {exc}",
                reason_code="CPU_WORKER_OUTPUT_INVALID",
            ) from exc
        expected_count = len(candidates) * len(generated["shapes"])
        if len(worker_records) != expected_count:
            raise MissingEvidenceError(
                "CPU worker output count mismatch",
                reason_code="CPU_WORKER_OUTPUT_INCOMPLETE",
            )

        by_pair = {}
        for record in worker_records:
            key = (record["candidate_id"], record["shape_id"])
            if key in by_pair:
                raise MissingEvidenceError(
                    "duplicate CPU worker observation",
                    reason_code="CPU_WORKER_OUTPUT_DUPLICATE",
                )
            by_pair[key] = record
            observation = {
                **record,
                "observation_id":
                    f"observation-{len(self.observations):06d}",
                "generated_input_path": generated_relative,
                "generated_input_sha256": generated_sha,
                "stdout_path": stdout_relative,
                "stdout_sha256": stdout_sha,
                "stderr_path": stderr_relative,
                "stderr_sha256": stderr_sha,
                "duration_ns": duration,
            }
            self.observations.append(observation)

        shape_ids = [shape["shape_id"] for shape in generated["shapes"]]
        matrix = np.asarray([
            [by_pair[(candidate_id, shape_id)]["value"]
             for candidate_id in candidate_ids]
            for shape_id in shape_ids
        ], dtype=np.float64)
        for candidate_id in candidate_ids:
            benchmark_id = f"benchmark-{candidate_id}"
            self.event_sink.emit("benchmark_finished", generation, {
                "stage_id": benchmark_id,
                "candidate_id": candidate_id,
                "status": "success",
                "duration_ns": duration,
            })
            self.event_sink.emit("candidate_terminal", generation, {
                "candidate_id": candidate_id,
                "classification": "complete",
            })
        vector = {
            "candidate_ids": candidate_ids,
            "shape_ids": shape_ids,
            "dtype": matrix.dtype.str,
            "shape": list(matrix.shape),
            "values": matrix.tolist(),
            "data_sha256": sha256_bytes(matrix.tobytes(order="C")),
        }
        self.event_sink.emit("fitness_vector", generation, vector)
        self.event_sink.emit("generation_finished", generation, {
            "candidate_set_sha256": candidate_set_sha,
        })
        self.generations.append({
            "generation": generation,
            "candidate_ids": candidate_ids,
            "ordered_indices": ordered_indices,
            "ordered_configs": configs,
            "fitness": vector,
            "python_random_state": py_state,
            "numpy_random_state": np_state,
            "seed_sequence_state": seed_state,
        })
        return matrix


def _cpu_worker(input_path: str | Path) -> int:
    generated = load_json_strict(input_path)
    mode = generated["evaluator_mode"]
    for candidate in generated["candidates"]:
        for shape in generated["shapes"]:
            if mode == "flat":
                value = 1.0
            elif mode == "formula":
                weighted = sum(
                    (index + 1) * float(value)
                    for index, (key, value) in enumerate(
                        sorted(candidate["config"].items())
                    )
                )
                value = round(
                    1.0 + float(shape["factor"]) + weighted / 100.0, 12
                )
            else:
                raise ContractError(
                    f"unknown CPU evaluator mode: {mode}",
                    reason_code="CPU_EVALUATOR_MODE_INVALID",
                )
            record = {
                "schema_version": "1.0",
                "run_id": generated["run_id"],
                "invocation_id": generated["invocation_id"],
                "candidate_id": candidate["candidate_id"],
                "config_id": candidate["config_id"],
                "shape_id": shape["shape_id"],
                "generation": generated["generation"],
                "sample_index": 0,
                "outcome": "success",
                "value": value,
                "failure_reason": None,
                "source": "deterministic_cpu_fixture",
            }
            sys.stdout.write(canonical_json_text(record) + "\n")
    return 0


def _copy_contract_bundle(writer: RunBundleWriter,
                          store: ContractStore) -> None:
    repo = _repo_root(store)
    contract = store.base_contract
    writer.copy_file(
        store.contract_path, "contract/experiment-contract.yaml"
    )
    writer.write_json(
        "contract/effective-contract.json", store.effective_contract
    )
    sources = {
        "shape-registry.csv": contract["locks"]["registry_paths"]["shape"],
        "baseline-registry.json":
            contract["locks"]["registry_paths"]["baseline"],
        "revision-registry.json":
            contract["locks"]["registry_paths"]["revision"],
        "protocol-lock.json": contract["locks"]["protocol_lock_path"],
        "amendment-chain.jsonl":
            contract["study"]["amendment_chain_path"],
    }
    for name, relative in sources.items():
        writer.copy_file(repo / relative, f"contract/{name}")


def _write_checkpoint_metadata(
        writer: RunBundleWriter, ga: GeneticAlgorithm,
        lineage: dict[str, Any]) -> dict[str, Any]:
    checkpoint = writer.contained("checkpoints/ga.checkpoint", must_exist=True)
    with checkpoint.open("rb") as stream:
        state = pickle.load(stream)
    metadata = {
        "schema_version": "1.0",
        "checkpoint_path": "checkpoints/ga.checkpoint",
        "checkpoint_sha256": sha256_file(checkpoint),
        "projection": {
            "generation": int(state["gen"]),
            "legacy_n_evals": int(state["n_evals"]),
            "population_size": len(state["pop"]),
            "decay_mode": state["decay_type"],
            "champion_hash": sha256_bytes(canonical_json_bytes(
                [{
                    key: state["space_map"][key][value]
                    for key, value in individual.X.items()
                } for individual in state["best"]]
            )),
            "champion_fitness_sha256": sha256_bytes(
                np.asarray([
                    individual.F for individual in state["best"]
                ], dtype=np.float64).tobytes(order="C")
            ),
        },
        "python_random_state_sha256": sha256_bytes(
            canonical_json_bytes(_state_plain(state["random_state"]))
        ),
        "numpy_random_state_sha256": sha256_bytes(
            canonical_json_bytes(_state_plain(state["np_random_state"]))
        ),
        "seed_sequence_state": _state_plain(state["seed_sequence_state"]),
        "protocol_lineage": lineage,
    }
    writer.write_json(
        "checkpoints/ga.checkpoint.metadata.json", metadata
    )
    return metadata


def _prepare_bundle(*, contract_path: str | Path, output: str | Path,
                    scenario_id: str, observer_mode: str,
                    run_id: str) -> dict[str, Any]:
    store = ContractStore(contract_path)
    ProtocolLock(store, _repo_root(store)).verify()
    store.assert_no_execution_overrides()
    profile = store.profile(scenario_id)
    writer = RunBundleWriter(output)
    _copy_contract_bundle(writer, store)
    writer.write_json("search-space.json", {
        "schema_version": "1.0",
        "scenario_id": scenario_id,
        "ordered_genes": store.effective_contract["search"]["space"],
        "ordered_shape_ids": [
            shape["shape_id"] for shape in store.effective_contract[
                "measurement"
            ]["cpu_fixture"]["shapes"]
        ],
        "search_space_sha256": sha256_bytes(canonical_json_bytes(
            store.effective_contract["search"]["space"]
        )),
    })
    event_sink = JsonlEventSink(
        writer.contained("ga-events.jsonl"),
        schema_path=_schema(store, "ga-event.schema.json"),
    )
    observer_sink = None
    observer = None
    if observer_mode == "on":
        observer_sink = JsonlEventSink(
            writer.contained("observer-events.jsonl"),
            schema_path=_schema(store, "ga-event.schema.json"),
        )
        observer = _ObserverAdapter(observer_sink)
    elif observer_mode == "off":
        writer.write_json("observer-events.jsonl", {
            "schema_version": "1.0",
            "observer": "disabled",
        })
    else:
        raise ContractError("observer mode must be off or on")
    event_sink.emit("run_started", None, {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "observer_enabled": observer_mode == "on",
        "expected_stages": ["compile", "benchmark", "subprocess"],
        "shape_ids": [
            shape["shape_id"] for shape in store.effective_contract[
                "measurement"
            ]["cpu_fixture"]["shapes"]
        ],
    })
    evaluator = _FixtureEvaluator(
        writer=writer, event_sink=event_sink, store=store,
        run_id=run_id, profile=profile,
    )
    checkpoint = writer.contained("checkpoints/ga.checkpoint")
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    return {
        "store": store,
        "profile": profile,
        "writer": writer,
        "run_id": run_id,
        "scenario_id": scenario_id,
        "observer_mode": observer_mode,
        "event_sink": event_sink,
        "observer_sink": observer_sink,
        "observer": observer,
        "evaluator": evaluator,
        "checkpoint": checkpoint,
        "lineage": _checkpoint_lineage(store, scenario_id, profile),
        "started_at": _utc_now(),
        "resume_from_sha256": None,
    }


def _write_run_context(ctx: dict[str, Any], *, run_kind: str,
                       complete: bool) -> None:
    store = ctx["store"]
    writer = ctx["writer"]
    lock = load_json_strict(
        _repo_root(store) / store.base_contract["locks"][
            "protocol_lock_path"
        ]
    )
    writer.write_json("run-manifest.json", {
        "schema_version": "1.0",
        "run_id": ctx["run_id"],
        "scenario_id": ctx["scenario_id"],
        "run_kind": run_kind,
        "observer_mode": ctx["observer_mode"],
        "execution_kind": "deterministic_cpu_fixture",
        "arm": "m00-observability",
        "complete": complete,
        "resume_from_sha256": ctx["resume_from_sha256"],
        "shape_ids": [
            shape["shape_id"] for shape in store.effective_contract[
                "measurement"
            ]["cpu_fixture"]["shapes"]
        ],
        "seed": ctx["profile"].seed,
        "command_argv": list(sys.argv),
        "cwd": os.fspath(Path.cwd()),
        "parent_commit": PARENT_COMMIT,
        "locked_ductile_object": LOCKED_DUCTILE_OBJECT,
        "contract_sha256": store.base_canonical_sha256,
        "effective_contract_sha256": store.effective_sha256,
        "source_set_sha256": lock["m00_source_set_sha256"],
        "started_at": ctx["started_at"],
        "finished_at": _utc_now(),
    })
    revision_sha = sha256_file(
        _repo_root(store) / store.base_contract["locks"][
            "registry_paths"
        ]["revision"]
    )
    writer.write_json("environment.json", capture_environment(
        cwd=Path.cwd(),
        argv=list(sys.argv),
        contract_sha256=store.base_canonical_sha256,
        revision_sha256=revision_sha,
    ))


def _finalize_bundle(ctx: dict[str, Any], ga: GeneticAlgorithm,
                     champion, champion_fitness, *,
                     run_kind: str) -> None:
    writer = ctx["writer"]
    evaluator = ctx["evaluator"]
    event_sink = ctx["event_sink"]
    for generation, f_avg, f_max, diversity in zip(
            evaluator.generations,
            ga.stats["f_avg"],
            ga.stats["f_max"],
            ga.stats["diversity"]):
        event_sink.emit("generation_stats", generation["generation"], {
            "f_avg": float(f_avg),
            "f_max": float(f_max),
            "diversity": float(diversity),
            "population_size": len(generation["candidate_ids"]),
            "decay_mode": "none",
        })
    metadata = _write_checkpoint_metadata(
        writer, ga, ctx["lineage"]
    )
    event_sink.emit("checkpoint_written", ga.final_generation, {
        "checkpoint_path": "checkpoints/ga.checkpoint",
        "checkpoint_sha256": metadata["checkpoint_sha256"],
        "generation": metadata["projection"]["generation"],
    })
    champion_hash = sha256_bytes(canonical_json_bytes(champion))
    champion_fitness_array = np.asarray(champion_fitness)
    trajectory = {
        "schema_version": "1.0",
        "run_id": ctx["run_id"],
        "scenario_id": ctx["scenario_id"],
        "run_kind": run_kind,
        "generations": evaluator.generations,
        "stats": {
            key: _state_plain(value) for key, value in ga.stats.items()
        },
        "final_python_random_state": _state_plain(random.getstate()),
        "final_numpy_random_state": _state_plain(np.random.get_state()),
        "final_seed_sequence_state": _state_plain(ga.space.seed_seq.state),
        "checkpoint_sha256": metadata["checkpoint_sha256"],
        "checkpoint_lineage": ctx["lineage"],
        "champion": champion,
        "champion_hash": champion_hash,
        "champion_fitness": champion_fitness_array.tolist(),
        "champion_fitness_dtype": champion_fitness_array.dtype.str,
        "champion_fitness_sha256": sha256_bytes(
            champion_fitness_array.tobytes(order="C")
        ),
        "final_generation": ga.final_generation,
        "termination_reason": ga.termination_reason,
    }
    writer.write_json("trajectory.json", trajectory)
    writer.write_text(
        "benchmark-observations.jsonl",
        "".join(
            canonical_json_text(record) + "\n"
            for record in evaluator.observations
        ),
    )
    event_sink.emit("run_finished", ga.final_generation, {
        "complete": True,
        "termination_reason": ga.termination_reason,
        "final_generation": ga.final_generation,
    })
    event_sink.close()
    if ctx["observer_sink"] is not None:
        ctx["observer_sink"].close()
    _write_run_context(ctx, run_kind=run_kind, complete=True)
    RawReconciler(writer.root, ctx["store"].contract_path).reconcile(
        verify_checksums=False, write_summary=True
    )
    ChecksumManifest.write(writer.root)
    writer.ensure_required()


def _run_bundle(*, contract_path: str | Path, output: str | Path,
                scenario_id: str, observer_mode: str,
                run_kind: str = "continuous",
                run_id: str | None = None) -> None:
    if run_kind != "continuous":
        raise ContractError(
            "same-process segmented execution is forbidden; use durable resume",
            reason_code="SAME_PROCESS_RESUME_FORBIDDEN",
        )
    run_id = run_id or (
        f"{scenario_id}-{observer_mode}-{uuid.uuid4().hex}"
    )
    ctx = _prepare_bundle(
        contract_path=contract_path, output=output,
        scenario_id=scenario_id, observer_mode=observer_mode,
        run_id=run_id,
    )
    ga = build_actual_ga(
        ctx["store"].effective_contract, ctx["profile"],
        ctx["evaluator"], ctx["checkpoint"],
        observer=ctx["observer"],
        checkpoint_lineage=ctx["lineage"],
    )
    ctx["evaluator"].space = ga.space
    champion, champion_fitness = ga.optimize()
    normalize_checkpoint(ctx["checkpoint"])
    _finalize_bundle(
        ctx, ga, champion, champion_fitness, run_kind="continuous"
    )


def _interrupt_bundle(*, contract_path: str | Path, output: str | Path,
                      scenario_id: str, observer_mode: str,
                      run_id: str) -> None:
    ctx = _prepare_bundle(
        contract_path=contract_path, output=output,
        scenario_id=scenario_id, observer_mode=observer_mode,
        run_id=run_id,
    )
    split = ctx["profile"].split_generation
    if split is None:
        raise ContractError(
            "durable interruption requires contract split_generation",
            reason_code="SPLIT_GENERATION_MISSING",
        )
    ga = build_actual_ga(
        ctx["store"].effective_contract, ctx["profile"],
        ctx["evaluator"], ctx["checkpoint"],
        observer=ctx["observer"],
        checkpoint_lineage=ctx["lineage"],
        interrupt_after_generation=split,
    )
    ctx["evaluator"].space = ga.space
    try:
        ga.optimize()
    except DurableInterruption as exc:
        if exc.generation != split:
            raise
    else:
        raise ContractError(
            "durable interruption point was not reached",
            reason_code="DURABLE_INTERRUPTION_MISSING",
        )
    normalize_checkpoint(ctx["checkpoint"])
    metadata = _write_checkpoint_metadata(
        ctx["writer"], ga, ctx["lineage"]
    )
    ctx["writer"].write_text(
        "benchmark-observations.jsonl",
        "".join(
            canonical_json_text(record) + "\n"
            for record in ctx["evaluator"].observations
        ),
    )
    ctx["event_sink"].emit("run_interrupted", split, {
        "complete": False,
        "next_generation": split + 1,
        "checkpoint_path": "checkpoints/ga.checkpoint",
        "checkpoint_sha256": metadata["checkpoint_sha256"],
    })
    event_count = ctx["event_sink"].next_sequence
    ctx["event_sink"].close()
    observer_count = 0
    if ctx["observer_sink"] is not None:
        observer_count = ctx["observer_sink"].next_sequence
        ctx["observer_sink"].close()
    ctx["writer"].write_json("resume-state.json", {
        "schema_version": "1.0",
        "run_id": run_id,
        "scenario_id": scenario_id,
        "observer_mode": observer_mode,
        "next_generation": split + 1,
        "event_count": event_count,
        "observer_event_count": observer_count,
        "checkpoint_sha256": metadata["checkpoint_sha256"],
        "protocol_lineage": ctx["lineage"],
        "generations": ctx["evaluator"].generations,
        "observations": ctx["evaluator"].observations,
        "started_at": ctx["started_at"],
    })
    _write_run_context(ctx, run_kind="interrupted", complete=False)
    ChecksumManifest.write(ctx["writer"].root)


def _resume_bundle(*, contract_path: str | Path, state_root: str | Path,
                   output: str | Path) -> None:
    state_root = Path(state_root)
    ChecksumManifest.verify(state_root)
    layout, _ = generated_input_inventory(state_root)
    if layout != "generation":
        raise MissingEvidenceError(
            "durable GA resume requires generation generated inputs",
            reason_code="RESUME_GENERATED_INPUT_LAYOUT_INVALID",
        )
    state = load_json_strict(state_root / "resume-state.json")
    store = ContractStore(contract_path)
    ProtocolLock(store, _repo_root(store)).verify()
    profile = store.profile(state["scenario_id"])
    lineage = _checkpoint_lineage(store, state["scenario_id"], profile)
    if state["protocol_lineage"] != lineage or \
            state["next_generation"] != profile.split_generation + 1 or \
            state["checkpoint_sha256"] != sha256_file(
                state_root / "checkpoints/ga.checkpoint"
            ):
        raise MissingEvidenceError(
            "durable resume state lineage or checkpoint mismatch",
            reason_code="RESUME_LINEAGE_MISMATCH",
        )
    manifest = load_json_strict(state_root / "run-manifest.json")
    validate_instance(
        manifest,
        load_json_strict(_schema(store, "run-manifest.schema.json")),
        label="interrupted run manifest",
    )
    if manifest["complete"] or manifest["run_kind"] != "interrupted" or \
            (state_root / "summary.json").exists() or \
            (state_root / "trajectory.json").exists():
        raise MissingEvidenceError(
            "durable interruption state is not incomplete",
            reason_code="RESUME_STATE_NOT_INCOMPLETE",
        )
    writer = RunBundleWriter(output)
    skip = {
        "checksums.sha256", "run-manifest.json", "environment.json",
        "resume-state.json", "benchmark-observations.jsonl",
        "checkpoints/ga.checkpoint.metadata.json",
    }
    for path in sorted(state_root.rglob("*")):
        if path.is_file():
            relative = path.relative_to(state_root).as_posix()
            if relative not in skip:
                writer.copy_file(path, relative)
    writer.copy_file(
        state_root / "checkpoints/ga.checkpoint.metadata.json",
        "checkpoints/interruption.checkpoint.metadata.json",
    )
    writer.copy_file(
        state_root / "checkpoints/ga.checkpoint",
        "checkpoints/interruption.checkpoint",
    )
    event_sink = JsonlEventSink(
        writer.contained("ga-events.jsonl"),
        schema_path=_schema(store, "ga-event.schema.json"),
        start_sequence=state["event_count"],
        append=True,
    )
    observer_sink = None
    observer = None
    if state["observer_mode"] == "on":
        observer_sink = JsonlEventSink(
            writer.contained("observer-events.jsonl"),
            schema_path=_schema(store, "ga-event.schema.json"),
            start_sequence=state["observer_event_count"],
            append=True,
        )
        observer = _ObserverAdapter(observer_sink)
    evaluator = _FixtureEvaluator(
        writer=writer, event_sink=event_sink, store=store,
        run_id=state["run_id"], profile=profile,
        start_generation=state["next_generation"],
    )
    evaluator.generations = list(state["generations"])
    evaluator.observations = list(state["observations"])
    checkpoint = writer.contained("checkpoints/ga.checkpoint", must_exist=True)
    ga = build_actual_ga(
        store.effective_contract, profile, evaluator, checkpoint,
        observer=observer, checkpoint_lineage=lineage,
    )
    try:
        ga.load(checkpoint)
    except Exception as exc:
        raise MissingEvidenceError(
            f"durable checkpoint load failed: {exc}",
            reason_code="RESUME_CHECKPOINT_LOAD_FAILED",
        ) from exc
    evaluator.space = ga.space
    champion, champion_fitness = ga.optimize()
    normalize_checkpoint(checkpoint)
    ctx = {
        "store": store,
        "profile": profile,
        "writer": writer,
        "run_id": state["run_id"],
        "scenario_id": state["scenario_id"],
        "observer_mode": state["observer_mode"],
        "event_sink": event_sink,
        "observer_sink": observer_sink,
        "observer": observer,
        "evaluator": evaluator,
        "checkpoint": checkpoint,
        "lineage": lineage,
        "started_at": state["started_at"],
        "resume_from_sha256": sha256_file(
            state_root / "checksums.sha256"
        ),
    }
    _finalize_bundle(
        ctx, ga, champion, champion_fitness, run_kind="resumed"
    )


_LEDGER_CLASSIFICATIONS = (
    "complete", "invalid", "duplicate", "compile_failed",
    "benchmark_failed", "partial",
)


def _ledger_candidates(store: ContractStore) -> list[dict[str, Any]]:
    genes = store.effective_contract["search"]["space"]
    result = []
    config_indices = (4, 0, 4, 2, 3, 5)
    for index, classification in enumerate(_LEDGER_CLASSIFICATIONS):
        config_index = config_indices[index]
        config = {
            gene["name"]: gene["values"][
                (config_index // (2 ** gene_index)) % len(gene["values"])
            ]
            for gene_index, gene in enumerate(genes)
        }
        result.append({
            "candidate_id": f"p{index}",
            "config_id": sha256_bytes(canonical_json_bytes(config)),
            "config": config,
            "classification": classification,
        })
    return result


def _adversarial_lineage(store: ContractStore) -> dict[str, Any]:
    profile = store.profile("checkpoint_resume")
    lineage = _checkpoint_lineage(
        store, "checkpoint_resume", profile
    )
    lineage["scenario_id"] = "adversarial_ledger"
    return lineage


def _ledger_worker(input_path: str | Path) -> int:
    generated = load_json_strict(input_path)
    candidate = generated["candidates"][0]
    candidate_id = candidate["candidate_id"]
    classification = generated["expected_outcome"]
    stage = generated["stage"]
    if stage == "compile" and classification != "compile_failed":
        sys.stdout.write(canonical_json_text({
            "schema_version": "1.0",
            "stage": "compile",
            "candidate_id": candidate_id,
            "status": "success",
        }) + "\n")
        return 0
    outcome = classification
    if stage == "benchmark" and classification == "complete":
        outcomes = ("success", "success")
    elif stage == "benchmark" and classification == "partial":
        outcomes = ("success", "partial")
    else:
        outcomes = (outcome, outcome)
    for shape_index, (shape, record_outcome) in enumerate(
            zip(generated["shapes"], outcomes)):
        value = None
        failure_reason = record_outcome
        if record_outcome == "success":
            value = float(shape["factor"]) + 1.0 + (
                0.1 if candidate_id == "p5" else 0.0
            )
            failure_reason = None
        sys.stdout.write(canonical_json_text({
            "schema_version": "1.0",
            "run_id": generated["run_id"],
            "invocation_id": generated["invocation_id"],
            "candidate_id": candidate_id,
            "config_id": candidate["config_id"],
            "shape_id": shape["shape_id"],
            "generation": 1,
            "sample_index": 0,
            "outcome": record_outcome,
            "value": value,
            "failure_reason": failure_reason,
            "source": "deterministic_cpu_fixture",
        }) + "\n")
    if classification == "compile_failed":
        return 11
    if classification == "benchmark_failed":
        return 12
    return 0


def _new_ledger_context(*, contract_path: str | Path,
                        output: str | Path, run_id: str) -> dict[str, Any]:
    store = ContractStore(contract_path)
    ProtocolLock(store, _repo_root(store)).verify()
    store.assert_no_execution_overrides()
    writer = RunBundleWriter(output)
    _copy_contract_bundle(writer, store)
    shapes = store.effective_contract["measurement"]["cpu_fixture"][
        "shapes"
    ]
    writer.write_json("search-space.json", {
        "schema_version": "1.0",
        "scenario_id": "adversarial_ledger",
        "ordered_genes": store.effective_contract["search"]["space"],
        "ordered_shape_ids": [shape["shape_id"] for shape in shapes],
        "search_space_sha256": sha256_bytes(canonical_json_bytes(
            store.effective_contract["search"]["space"]
        )),
    })
    writer.write_json("observer-events.jsonl", {
        "schema_version": "1.0", "observer": "disabled",
    })
    sink = JsonlEventSink(
        writer.contained("ga-events.jsonl"),
        schema_path=_schema(store, "ga-event.schema.json"),
    )
    candidate_ids = [
        item["candidate_id"] for item in _ledger_candidates(store)
    ]
    sink.emit("run_started", None, {
        "run_id": run_id,
        "scenario_id": "adversarial_ledger",
        "observer_enabled": False,
        "expected_stages": ["compile", "benchmark", "subprocess"],
        "shape_ids": [shape["shape_id"] for shape in shapes],
    })
    sink.emit("generation_started", 1, {
        "candidate_ids": candidate_ids,
        "candidate_set_sha256": sha256_bytes(
            canonical_json_bytes(candidate_ids)
        ),
    })
    return {
        "store": store,
        "profile": store.profile("checkpoint_resume"),
        "writer": writer,
        "run_id": run_id,
        "scenario_id": "adversarial_ledger",
        "observer_mode": "off",
        "event_sink": sink,
        "observer_sink": None,
        "lineage": _adversarial_lineage(store),
        "started_at": _utc_now(),
        "resume_from_sha256": None,
        "candidates": _ledger_candidates(store),
        "observations": [],
        "invocation_count": 0,
        "terminal_classifications": [],
    }


def _ledger_subprocess(ctx: dict[str, Any], candidate: dict[str, Any],
                       stage: str) -> tuple[subprocess.CompletedProcess, int,
                                            str, str, str]:
    ctx["invocation_count"] += 1
    invocation_id = f"invocation-{ctx['invocation_count']:04d}"
    generated = {
        "schema_version": "1.0",
        "run_id": ctx["run_id"],
        "scenario_id": "adversarial_ledger",
        "invocation_id": invocation_id,
        "generation": 1,
        "evaluator_mode": "adversarial",
        "stage": stage,
        "expected_outcome": candidate["classification"],
        "shapes": ctx["store"].effective_contract["measurement"][
            "cpu_fixture"
        ]["shapes"],
        "candidates": [{
            key: candidate[key]
            for key in ("candidate_id", "config_id", "config")
        }],
    }
    generated_relative = f"generated-inputs/{invocation_id}.json"
    generated_path = ctx["writer"].write_json(
        generated_relative, generated
    )
    generated_sha = sha256_file(generated_path)
    stdout_relative = f"subprocess/{invocation_id}.stdout.jsonl"
    stderr_relative = f"subprocess/{invocation_id}.stderr.txt"
    argv = [
        sys.executable, "-m", "Tensile.ductile.m00.runner",
        "_ledger-worker", "--input", os.fspath(generated_path),
    ]
    ctx["event_sink"].emit("subprocess_started", 1, {
        "stage_id": invocation_id,
        "invocation_id": invocation_id,
        "argv": argv,
        "cwd": os.fspath(_tensilelite_root()),
        "input_sha256": generated_sha,
    })
    environment = os.environ.copy()
    environment["PYTHONHASHSEED"] = ctx["store"].effective_contract[
        "platform"
    ]["m00_execution"]["pythonhashseed"]
    environment["PYTHONPATH"] = os.fspath(_tensilelite_root())
    started = time.monotonic_ns()
    result = subprocess.run(
        argv, cwd=_tensilelite_root(), env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, timeout=30,
    )
    duration = time.monotonic_ns() - started
    stdout_path = ctx["writer"].write_bytes(
        stdout_relative, result.stdout
    )
    stderr_path = ctx["writer"].write_bytes(
        stderr_relative, result.stderr
    )
    stdout_sha = sha256_file(stdout_path)
    stderr_sha = sha256_file(stderr_path)
    ctx["event_sink"].emit("subprocess_finished", 1, {
        "stage_id": invocation_id,
        "invocation_id": invocation_id,
        "status": "success" if result.returncode == 0 else "failure",
        "duration_ns": duration,
        "exit_code": result.returncode,
        "stdout_path": stdout_relative,
        "stdout_sha256": stdout_sha,
        "stderr_path": stderr_relative,
        "stderr_sha256": stderr_sha,
    })
    records = []
    for line in result.stdout.decode("utf-8").splitlines():
        record = json.loads(line)
        if "outcome" in record:
            record.update({
                "observation_id":
                    f"observation-{len(ctx['observations']) + len(records):06d}",
                "generated_input_path": generated_relative,
                "generated_input_sha256": generated_sha,
                "stdout_path": stdout_relative,
                "stdout_sha256": stdout_sha,
                "stderr_path": stderr_relative,
                "stderr_sha256": stderr_sha,
                "duration_ns": duration,
            })
            records.append(record)
    ctx["observations"].extend(records)
    return result, duration, invocation_id, generated_relative, stdout_relative


def _execute_ledger_candidates(ctx: dict[str, Any],
                               start: int, stop: int) -> None:
    for candidate in ctx["candidates"][start:stop]:
        candidate_id = candidate["candidate_id"]
        classification = candidate["classification"]
        if classification == "invalid":
            result, _, _, _, _ = _ledger_subprocess(
                ctx, candidate, "classify"
            )
            if result.returncode != 0:
                raise MissingEvidenceError(
                    "classification worker failed",
                    reason_code="LEDGER_WORKER_FAILED",
                )
        elif classification != "duplicate":
            compile_id = f"compile-attempt-{candidate_id}"
            ctx["event_sink"].emit("compile_started", 1, {
                "stage_id": compile_id, "candidate_id": candidate_id,
            })
            result, duration, _, _, _ = _ledger_subprocess(
                ctx, candidate, "compile"
            )
            compile_success = classification != "compile_failed"
            if (result.returncode == 0) != compile_success:
                raise MissingEvidenceError(
                    "compile worker result contradicts ledger oracle",
                    reason_code="LEDGER_WORKER_RESULT_MISMATCH",
                )
            ctx["event_sink"].emit("compile_finished", 1, {
                "stage_id": compile_id,
                "candidate_id": candidate_id,
                "status": "success" if compile_success else "failure",
                "duration_ns": duration,
            })
            if compile_success:
                benchmark_id = f"benchmark-attempt-{candidate_id}"
                ctx["event_sink"].emit("benchmark_started", 1, {
                    "stage_id": benchmark_id,
                    "candidate_id": candidate_id,
                })
                result, duration, _, _, _ = _ledger_subprocess(
                    ctx, candidate, "benchmark"
                )
                benchmark_success = classification != "benchmark_failed"
                if (result.returncode == 0) != benchmark_success:
                    raise MissingEvidenceError(
                        "benchmark worker result contradicts ledger oracle",
                        reason_code="LEDGER_WORKER_RESULT_MISMATCH",
                    )
                ctx["event_sink"].emit("benchmark_finished", 1, {
                    "stage_id": benchmark_id,
                    "candidate_id": candidate_id,
                    "status":
                        "success" if benchmark_success else "failure",
                    "duration_ns": duration,
                })
        terminal = {
            "candidate_id": candidate_id,
            "classification": classification,
        }
        if classification == "duplicate":
            original = ctx["candidates"][0]
            terminal.update({
                "config_id": candidate["config_id"],
                "config": candidate["config"],
                "duplicate_of_candidate_id": original["candidate_id"],
                "duplicate_of_config_id": original["config_id"],
            })
        ctx["event_sink"].emit("candidate_terminal", 1, terminal)
        ctx["terminal_classifications"].append(classification)


def _ledger_matrix(ctx: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    shape_ids = [
        shape["shape_id"] for shape in ctx["store"].effective_contract[
            "measurement"
        ]["cpu_fixture"]["shapes"]
    ]
    candidate_ids = [
        item["candidate_id"] for item in ctx["candidates"]
    ]
    by_pair = {
        (record["candidate_id"], record["shape_id"]): record
        for record in ctx["observations"]
    }
    matrix = np.asarray([
        [
            float(by_pair[(candidate_id, shape_id)]["value"])
            if (candidate_id, shape_id) in by_pair and
            by_pair[(candidate_id, shape_id)]["outcome"] == "success"
            else -1.0
            for candidate_id in candidate_ids
        ]
        for shape_id in shape_ids
    ], dtype=np.float64)
    vector = {
        "candidate_ids": candidate_ids,
        "shape_ids": shape_ids,
        "dtype": matrix.dtype.str,
        "shape": list(matrix.shape),
        "values": matrix.tolist(),
        "data_sha256": sha256_bytes(matrix.tobytes(order="C")),
    }
    return matrix, vector


def _write_ledger_checkpoint(ctx: dict[str, Any], cursor: int) -> dict[str, Any]:
    matrix, vector = _ledger_matrix(ctx) if cursor == 6 else (
        np.empty((0, 0)), None
    )
    state = {
        "checkpoint_kind": "adversarial_ledger",
        "cursor": cursor,
        "run_id": ctx["run_id"],
        "protocol_lineage": ctx["lineage"],
        "terminal_classifications": ctx["terminal_classifications"],
        "invocation_count": ctx["invocation_count"],
        "observation_count": len(ctx["observations"]),
    }
    checkpoint = ctx["writer"].write_bytes(
        "checkpoints/ga.checkpoint",
        pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL),
    )
    complete_candidate = ctx["candidates"][0]
    champion_hash = sha256_bytes(canonical_json_bytes(
        [complete_candidate["config"]]
    ))
    champion_fitness = (
        matrix[:, 0] if cursor == 6 else np.asarray([], dtype=np.float64)
    )
    metadata = {
        "schema_version": "1.0",
        "checkpoint_path": "checkpoints/ga.checkpoint",
        "checkpoint_sha256": sha256_file(checkpoint),
        "projection": {
            "generation": 1,
            "legacy_n_evals": 2 if cursor == 6 else 0,
            "population_size": 6,
            "decay_mode": "none",
            "champion_hash": champion_hash,
            "champion_fitness_sha256": sha256_bytes(
                champion_fitness.tobytes(order="C")
            ),
        },
        "python_random_state_sha256": sha256_bytes(
            canonical_json_bytes([])
        ),
        "numpy_random_state_sha256": sha256_bytes(
            canonical_json_bytes([])
        ),
        "seed_sequence_state": {
            "entropy": ctx["profile"].seed,
            "spawn_key": [],
            "pool_size": 4,
            "n_children_spawned": 0,
        },
        "protocol_lineage": ctx["lineage"],
    }
    ctx["writer"].write_json(
        "checkpoints/ga.checkpoint.metadata.json", metadata
    )
    return metadata


def _finalize_ledger(ctx: dict[str, Any], *, run_kind: str) -> None:
    matrix, vector = _ledger_matrix(ctx)
    ctx["event_sink"].emit("fitness_vector", 1, vector)
    candidate_ids = vector["candidate_ids"]
    candidate_set_sha = sha256_bytes(canonical_json_bytes(candidate_ids))
    ctx["event_sink"].emit("generation_stats", 1, {
        "f_avg": float(matrix[matrix > 0].mean()),
        "f_max": float(matrix.max()),
        "diversity": 0.0,
        "population_size": 6,
        "decay_mode": "none",
    })
    ctx["event_sink"].emit("generation_finished", 1, {
        "candidate_set_sha256": candidate_set_sha,
    })
    metadata = _write_ledger_checkpoint(ctx, 6)
    ctx["event_sink"].emit("checkpoint_written", 1, {
        "checkpoint_path": "checkpoints/ga.checkpoint",
        "checkpoint_sha256": metadata["checkpoint_sha256"],
        "generation": 1,
    })
    ctx["event_sink"].emit("run_finished", 1, {
        "complete": True,
        "termination_reason": "ledger_complete",
        "final_generation": 1,
    })
    ctx["event_sink"].close()
    ctx["writer"].write_text(
        "benchmark-observations.jsonl",
        "".join(
            canonical_json_text(record) + "\n"
            for record in ctx["observations"]
        ),
    )
    ctx["writer"].write_json("trajectory.json", {
        "schema_version": "1.0",
        "run_id": ctx["run_id"],
        "scenario_id": "adversarial_ledger",
        "run_kind": run_kind,
        "candidate_ids": candidate_ids,
        "terminal_classifications": ctx["terminal_classifications"],
        "fitness": vector,
        "checkpoint_sha256": metadata["checkpoint_sha256"],
        "checkpoint_lineage": ctx["lineage"],
        "final_generation": 1,
        "termination_reason": "ledger_complete",
    })
    _write_run_context(ctx, run_kind=run_kind, complete=True)
    RawReconciler(
        ctx["writer"].root, ctx["store"].contract_path
    ).reconcile(verify_checksums=False, write_summary=True)
    ChecksumManifest.write(ctx["writer"].root)
    ctx["writer"].ensure_required()


def _run_adversarial_bundle(*, contract_path: str | Path,
                            output: str | Path, run_id: str) -> None:
    ctx = _new_ledger_context(
        contract_path=contract_path, output=output, run_id=run_id
    )
    _execute_ledger_candidates(ctx, 0, 6)
    _finalize_ledger(ctx, run_kind="adversarial_continuous")


def _interrupt_adversarial_bundle(*, contract_path: str | Path,
                                  output: str | Path,
                                  run_id: str) -> None:
    ctx = _new_ledger_context(
        contract_path=contract_path, output=output, run_id=run_id
    )
    _execute_ledger_candidates(ctx, 0, 3)
    metadata = _write_ledger_checkpoint(ctx, 3)
    ctx["event_sink"].emit("run_interrupted", 1, {
        "complete": False,
        "next_generation": 2,
        "checkpoint_path": "checkpoints/ga.checkpoint",
        "checkpoint_sha256": metadata["checkpoint_sha256"],
    })
    event_count = ctx["event_sink"].next_sequence
    ctx["event_sink"].close()
    ctx["writer"].write_text(
        "benchmark-observations.jsonl",
        "".join(
            canonical_json_text(record) + "\n"
            for record in ctx["observations"]
        ),
    )
    ctx["writer"].write_json("ledger-state.json", {
        "schema_version": "1.0",
        "run_id": run_id,
        "event_count": event_count,
        "next_candidate": 3,
        "invocation_count": ctx["invocation_count"],
        "terminal_classifications": ctx["terminal_classifications"],
        "observations": ctx["observations"],
        "protocol_lineage": ctx["lineage"],
        "started_at": ctx["started_at"],
        "checkpoint_sha256": metadata["checkpoint_sha256"],
    })
    _write_run_context(
        ctx, run_kind="adversarial_interrupted", complete=False
    )
    ChecksumManifest.write(ctx["writer"].root)


def _resume_adversarial_bundle(*, contract_path: str | Path,
                               state_root: str | Path,
                               output: str | Path) -> None:
    state_root = Path(state_root)
    ChecksumManifest.verify(state_root)
    layout, _ = generated_input_inventory(state_root)
    if layout != "invocation":
        raise MissingEvidenceError(
            "adversarial resume requires invocation generated inputs",
            reason_code="LEDGER_GENERATED_INPUT_LAYOUT_INVALID",
        )
    state = load_json_strict(state_root / "ledger-state.json")
    store = ContractStore(contract_path)
    ProtocolLock(store, _repo_root(store)).verify()
    lineage = _adversarial_lineage(store)
    if state["protocol_lineage"] != lineage or \
            state["next_candidate"] != 3 or \
            state["checkpoint_sha256"] != sha256_file(
                state_root / "checkpoints/ga.checkpoint"
            ):
        raise MissingEvidenceError(
            "adversarial durable state lineage mismatch",
            reason_code="LEDGER_RESUME_LINEAGE_MISMATCH",
        )
    with (state_root / "checkpoints/ga.checkpoint").open("rb") as stream:
        checkpoint = pickle.load(stream)
    if checkpoint != {
            "checkpoint_kind": "adversarial_ledger",
            "cursor": 3,
            "run_id": state["run_id"],
            "protocol_lineage": lineage,
            "terminal_classifications": state["terminal_classifications"],
            "invocation_count": state["invocation_count"],
            "observation_count": len(state["observations"])}:
        raise MissingEvidenceError(
            "adversarial checkpoint decode or cursor mismatch",
            reason_code="LEDGER_CHECKPOINT_MISMATCH",
        )
    writer = RunBundleWriter(output)
    skip = {
        "checksums.sha256", "run-manifest.json", "environment.json",
        "ledger-state.json", "benchmark-observations.jsonl",
        "checkpoints/ga.checkpoint",
        "checkpoints/ga.checkpoint.metadata.json",
    }
    for path in sorted(state_root.rglob("*")):
        if path.is_file():
            relative = path.relative_to(state_root).as_posix()
            if relative not in skip:
                writer.copy_file(path, relative)
    writer.copy_file(
        state_root / "checkpoints/ga.checkpoint",
        "checkpoints/interruption.checkpoint",
    )
    writer.copy_file(
        state_root / "checkpoints/ga.checkpoint.metadata.json",
        "checkpoints/interruption.checkpoint.metadata.json",
    )
    sink = JsonlEventSink(
        writer.contained("ga-events.jsonl"),
        schema_path=_schema(store, "ga-event.schema.json"),
        start_sequence=state["event_count"], append=True,
    )
    ctx = {
        "store": store,
        "profile": store.profile("checkpoint_resume"),
        "writer": writer,
        "run_id": state["run_id"],
        "scenario_id": "adversarial_ledger",
        "observer_mode": "off",
        "event_sink": sink,
        "observer_sink": None,
        "lineage": lineage,
        "started_at": state["started_at"],
        "resume_from_sha256": sha256_file(
            state_root / "checksums.sha256"
        ),
        "candidates": _ledger_candidates(store),
        "observations": list(state["observations"]),
        "invocation_count": state["invocation_count"],
        "terminal_classifications":
            list(state["terminal_classifications"]),
    }
    _execute_ledger_candidates(ctx, 3, 6)
    _finalize_ledger(ctx, run_kind="adversarial_resumed")


def run_adversarial_ledger(contract_path: str | Path,
                           output: str | Path) -> Path:
    store = ContractStore(contract_path)
    ProtocolLock(store, _repo_root(store)).verify()
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise MissingEvidenceError(
            "adversarial output already exists",
            reason_code="ARTIFACT_ROOT_EXISTS",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    environment = os.environ.copy()
    environment["PYTHONHASHSEED"] = store.effective_contract["platform"][
        "m00_execution"
    ]["pythonhashseed"]
    environment["PYTHONPATH"] = os.fspath(_tensilelite_root())
    continuous_id = f"m00-ledger-{uuid.uuid4().hex}"
    resumed_id = f"m00-ledger-{uuid.uuid4().hex}"
    commands = [
        ("continuous", [
            sys.executable, "-m", "Tensile.ductile.m00.runner",
            "_adversarial-run", "--contract",
            os.fspath(store.contract_path), "--output",
            os.fspath(output / "bundles/continuous"),
            "--run-id", continuous_id,
        ]),
        ("interrupt", [
            sys.executable, "-m", "Tensile.ductile.m00.runner",
            "_adversarial-interrupt", "--contract",
            os.fspath(store.contract_path), "--output",
            os.fspath(output / "interruptions/resumed"),
            "--run-id", resumed_id,
        ]),
        ("resume", [
            sys.executable, "-m", "Tensile.ductile.m00.runner",
            "_adversarial-resume", "--contract",
            os.fspath(store.contract_path), "--state",
            os.fspath(output / "interruptions/resumed"),
            "--output", os.fspath(output / "bundles/resumed"),
        ]),
    ]
    command_log = []
    for name, argv in commands:
        started = time.monotonic_ns()
        result = subprocess.run(
            argv, cwd=_tensilelite_root(), env=environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=120,
        )
        command_log.append({
            "name": name,
            "argv": argv,
            "cwd": os.fspath(_tensilelite_root()),
            "exit_code": result.returncode,
            "duration_ns": time.monotonic_ns() - started,
            "stdout_sha256": sha256_bytes(result.stdout),
            "stderr_sha256": sha256_bytes(result.stderr),
        })
        if result.returncode:
            raise MissingEvidenceError(
                f"adversarial child {name} failed: "
                f"{result.stderr.decode('utf-8', errors='replace')}",
                reason_code="ADVERSARIAL_CHILD_FAILED",
            )
    summaries = {
        name: load_json_strict(
            output / "bundles" / name / "summary.json"
        )
        for name in ("continuous", "resumed")
    }
    stable_keys = (
        "proposed_candidates", "valid_unique", "terminal_counts",
        "compile_attempts",
        "compile_failures", "benchmark_attempts", "benchmark_failures",
        "candidate_shape_samples",
        "ductile_legacy_positive_candidate_evals",
        "complete_candidate_evals", "partial_candidate_evals",
        "partial_positive_candidate_evals",
    )
    projections = {
        name: {key: summary[key] for key in stable_keys}
        for name, summary in summaries.items()
    }
    expected = {
        "proposed_candidates": 6,
        "valid_unique": 4,
        "terminal_counts": {
            "invalid": 1, "duplicate": 1, "compile_failed": 1,
            "benchmark_failed": 1, "partial": 1, "complete": 1,
        },
        "compile_attempts": 4,
        "compile_failures": 1,
        "benchmark_attempts": 3,
        "benchmark_failures": 1,
        "candidate_shape_samples": 3,
        "ductile_legacy_positive_candidate_evals": 2,
        "complete_candidate_evals": 1,
        "partial_candidate_evals": 1,
        "partial_positive_candidate_evals": 1,
    }
    expected_classifications = list(_LEDGER_CLASSIFICATIONS)
    trajectories = {
        name: load_json_strict(
            output / "bundles" / name / "trajectory.json"
        )
        for name in ("continuous", "resumed")
    }
    if projections["continuous"] != expected or \
            projections["resumed"] != expected or any(
                trajectory["candidate_ids"] != [
                    f"p{index}" for index in range(6)
                ] or trajectory["terminal_classifications"] !=
                expected_classifications
                for trajectory in trajectories.values()
            ):
        raise MissingEvidenceError(
            f"adversarial ledger oracle mismatch: "
            f"{projections}, {trajectories}",
            reason_code="ADVERSARIAL_ORACLE_MISMATCH",
        )
    (output / "adversarial-command-log.json").write_text(
        canonical_json_text({
            "schema_version": "1.0", "commands": command_log
        }) + "\n", encoding="utf-8",
    )
    (output / "adversarial-summary.json").write_text(
        canonical_json_text({
            "schema_version": "1.0",
            "overall": "PASS",
            "continuous_resume_parity": True,
            "observational_run_ids_unique": continuous_id != resumed_id,
            "oracle": expected,
            "bundle_summary_sha256": {
                name: sha256_file(
                    output / "bundles" / name / "summary.json"
                )
                for name in ("continuous", "resumed")
            },
        }) + "\n", encoding="utf-8",
    )
    _write_tree_checksums(output)
    return output


def _trajectory_projection(path: Path) -> dict[str, Any]:
    value = load_json_strict(path / "trajectory.json")
    return {
        key: item for key, item in value.items()
        if key not in {"run_id", "run_kind"}
    }


def _tree_files(root: Path, manifest_name: str):
    result = {}
    if root.is_symlink() or not root.is_dir():
        raise MissingEvidenceError(
            "differential root is missing or symlinked",
            reason_code="DIFFERENTIAL_ROOT_INVALID",
        )
    for path in root.rglob("*"):
        if path.is_symlink():
            raise MissingEvidenceError(
                f"symlink in differential evidence: {path}",
                reason_code="DIFFERENTIAL_SYMLINK",
            )
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            if relative != manifest_name:
                result[relative] = path
    return result


def _write_tree_checksums(root: Path) -> str:
    name = "differential-checksums.sha256"
    target = root / name
    files = _tree_files(root, name)
    with target.open("x", encoding="utf-8") as stream:
        for relative in sorted(files):
            stream.write(f"{sha256_file(files[relative])}  {relative}\n")
    return sha256_file(target)


def _verify_tree_checksums(root: Path) -> None:
    name = "differential-checksums.sha256"
    target = root / name
    if target.is_symlink() or not target.is_file():
        raise MissingEvidenceError(
            "differential checksum manifest missing",
            reason_code="DIFFERENTIAL_CHECKSUM_MISSING",
        )
    entries = {}
    try:
        for line in target.read_text(encoding="utf-8").splitlines():
            digest, relative = line.split("  ", 1)
            path = Path(relative)
            if len(digest) != 64 or relative in entries or \
                    path.is_absolute() or ".." in path.parts:
                raise ValueError("invalid checksum entry")
            entries[relative] = digest
    except (OSError, ValueError) as exc:
        raise MissingEvidenceError(
            f"differential checksum manifest invalid: {exc}",
            reason_code="DIFFERENTIAL_CHECKSUM_INVALID",
        ) from exc
    files = _tree_files(root, name)
    if set(entries) != set(files) or any(
            entries[name] != sha256_file(path)
            for name, path in files.items()):
        raise MissingEvidenceError(
            "differential checksum mismatch",
            reason_code="DIFFERENTIAL_CHECKSUM_MISMATCH",
        )


def _bundle_specs(store: ContractStore):
    return [
        ("fixed-off-a", "fixed_horizon", "off", "continuous"),
        ("fixed-off-b", "fixed_horizon", "off", "continuous"),
        ("fixed-on", "fixed_horizon", "on", "continuous"),
        ("early-off", "early_stop", "off", "continuous"),
        ("early-on", "early_stop", "on", "continuous"),
        ("resume-continuous-off", "checkpoint_resume", "off", "continuous"),
        ("resume-continuous-on", "checkpoint_resume", "on", "continuous"),
        ("resume-durable-off", "checkpoint_resume", "off", "durable"),
        ("resume-durable-on", "checkpoint_resume", "on", "durable"),
        ("resume-repeat-off", "checkpoint_resume", "off", "continuous"),
        ("resume-repeat-on", "checkpoint_resume", "on", "continuous"),
    ]


def run_differential(contract_path: str | Path, output: str | Path) -> Path:
    store = ContractStore(contract_path)
    ProtocolLock(store, _repo_root(store)).verify()
    store.assert_no_execution_overrides()
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise MissingEvidenceError(
            f"differential output already exists: {output}",
            reason_code="ARTIFACT_ROOT_EXISTS",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    environment = os.environ.copy()
    environment["PYTHONHASHSEED"] = store.effective_contract["platform"][
        "m00_execution"
    ]["pythonhashseed"]
    environment["PYTHONPATH"] = os.fspath(_tensilelite_root())
    command_log = []
    for name, scenario, mode, run_kind in _bundle_specs(store):
        bundle = output / "bundles" / name
        run_id = f"m00-{uuid.uuid4().hex}"
        commands = []
        if run_kind == "durable":
            state = output / "interruptions" / name
            commands.append((
                f"{name}-interrupt",
                [
                    sys.executable, "-m", "Tensile.ductile.m00.runner",
                    "_interrupt-run", "--contract",
                    os.fspath(store.contract_path),
                    "--output", os.fspath(state), "--scenario", scenario,
                    "--observer-mode", mode, "--run-id", run_id,
                ],
            ))
            commands.append((
                f"{name}-resume",
                [
                    sys.executable, "-m", "Tensile.ductile.m00.runner",
                    "_resume-run", "--contract",
                    os.fspath(store.contract_path),
                    "--state", os.fspath(state),
                    "--output", os.fspath(bundle),
                ],
            ))
        else:
            commands.append((
                name,
                [
                    sys.executable, "-m", "Tensile.ductile.m00.runner",
                    "_child-run", "--contract",
                    os.fspath(store.contract_path),
                    "--output", os.fspath(bundle), "--scenario", scenario,
                    "--observer-mode", mode, "--run-kind", "continuous",
                    "--run-id", run_id,
                ],
            ))
        for command_name, argv in commands:
            started = time.monotonic_ns()
            result = subprocess.run(
                argv,
                cwd=_tensilelite_root(),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=300,
            )
            duration = time.monotonic_ns() - started
            command_log.append({
                "name": command_name,
                "argv": argv,
                "cwd": os.fspath(_tensilelite_root()),
                "exit_code": result.returncode,
                "duration_ns": duration,
                "stdout_sha256": sha256_bytes(result.stdout),
                "stderr_sha256": sha256_bytes(result.stderr),
            })
            if result.returncode:
                raise MissingEvidenceError(
                    f"child bundle {command_name} failed "
                    f"({result.returncode}): "
                    f"{result.stderr.decode('utf-8', errors='replace')}",
                    reason_code="DIFFERENTIAL_CHILD_FAILED",
                )
    run_adversarial_ledger(
        store.contract_path, output / "adversarial"
    )
    projections = {
        name: _trajectory_projection(output / "bundles" / name)
        for name, scenario, mode, run_kind in _bundle_specs(store)
    }
    comparisons = {
        "fixed_off_repeat":
            projections["fixed-off-a"] == projections["fixed-off-b"],
        "fixed_off_on":
            projections["fixed-off-a"] == projections["fixed-on"],
        "early_stop_off_on":
            projections["early-off"] == projections["early-on"],
        "resume_continuous_off_on":
            projections["resume-continuous-off"] ==
            projections["resume-continuous-on"],
        "resume_durable_off_on":
            projections["resume-durable-off"] ==
            projections["resume-durable-on"],
        "continuous_durable_resume_equivalence":
            projections["resume-continuous-off"] ==
            projections["resume-durable-off"],
        "resume_continuous_repeat_off":
            projections["resume-continuous-off"] ==
            projections["resume-repeat-off"],
        "resume_continuous_repeat_on":
            projections["resume-continuous-on"] ==
            projections["resume-repeat-on"],
    }
    run_ids = [
        load_json_strict(
            output / "bundles" / name / "run-manifest.json"
        )["run_id"]
        for name, scenario, mode, run_kind in _bundle_specs(store)
    ]
    comparisons["observational_run_ids_unique"] = (
        len(run_ids) == len(set(run_ids))
    )
    if not all(comparisons.values()):
        (output / "differential-summary.json").write_text(
            canonical_json_text({
                "schema_version": "1.0",
                "overall": "FAIL",
                "instrumentation_falsified": True,
                "comparisons": comparisons,
            }) + "\n",
            encoding="utf-8",
        )
        raise InstrumentationError(
            f"actual-path differential mismatch: {comparisons}"
        )
    summaries = {
        name: sha256_file(output / "bundles" / name / "summary.json")
        for name, scenario, mode, run_kind in _bundle_specs(store)
    }
    (output / "differential-command-log.json").write_text(
        canonical_json_text({
            "schema_version": "1.0", "commands": command_log
        }) + "\n", encoding="utf-8"
    )
    (output / "differential-summary.json").write_text(
        canonical_json_text({
            "schema_version": "1.0",
            "overall": "PASS",
            "instrumentation_falsified": False,
            "comparisons": comparisons,
            "bundle_summary_sha256": summaries,
            "adversarial_summary_sha256": sha256_file(
                output / "adversarial/adversarial-summary.json"
            ),
        }) + "\n",
        encoding="utf-8",
    )
    _write_tree_checksums(output)
    return output


_CRITERION_KEYS = (
    "M00.ACC.OBS-SEMANTICS",
    "M00.ACC.RECONCILE",
    "M00.ACC.SPLIT-GUARD",
    "M00.ACC.BASELINE-GUARD",
    "M00.ACC.CONTRACT-LOCK",
    "M00.FAL.INSTRUMENTATION",
    "M00.STOP.MISSING-EVIDENCE",
)


def _independent_criterion_claims(
        evidence_path: str | Path, *,
        lock: dict[str, Any], lock_sha256: str,
        allowed_root: Path,
        authorized_root: Path | None = None
        ) -> tuple[dict[str, Any], dict[str, Any],
                   str, list[str], list[str], list[str]]:
    authorized_root = (
        Path(authorized_root) if authorized_root is not None
        else Path(allowed_root)
    ).resolve()
    if authorized_root.is_symlink() or not authorized_root.is_dir() or \
            not authorized_root.is_relative_to(Path(allowed_root).resolve()):
        raise MissingEvidenceError(
            "authorized verifier evidence root is invalid",
            reason_code="CRITERION_EVIDENCE_ROOT_INVALID",
        )
    try:
        validate_evidence_file(
            evidence_path, authorized_root,
            label="criterion evidence envelope",
        )
    except ReportLifecycleError as exc:
        raise MissingEvidenceError(
            exc.human_message,
            reason_code="CRITERION_EVIDENCE_MISMATCH",
        ) from exc
    document = load_json_strict(evidence_path)
    if not isinstance(document, dict) or set(document) != {
            "schema_version", "criteria", "root_causes",
            "required_fixes", "evidence_gaps"} or \
            document["schema_version"] != "1.0" or \
            set(document["criteria"]) != set(_CRITERION_KEYS):
        raise MissingEvidenceError(
            "criterion-specific evidence document is incomplete",
            reason_code="CRITERION_EVIDENCE_INCOMPLETE",
        )
    criteria = {}
    evidence = {}
    for criterion in _CRITERION_KEYS:
        item = document["criteria"][criterion]
        if not isinstance(item, dict) or set(item) != {
                "status", "artifact_path", "artifact_sha256",
                "source_set_sha256", "protocol_lock_sha256",
                "fresh_evidence"}:
            raise MissingEvidenceError(
                f"criterion evidence fields are invalid: {criterion}",
                reason_code="CRITERION_EVIDENCE_INVALID",
            )
        if criterion.startswith("M00.ACC.") and item["status"] not in {
                "PASS", "FAIL", "BLOCKED", "INCONCLUSIVE",
                "UNVERIFIED"} or \
                criterion in {
                    "M00.FAL.INSTRUMENTATION",
                    "M00.STOP.MISSING-EVIDENCE",
                } and not isinstance(item["status"], bool) and \
                item["status"] != "UNVERIFIED":
            raise MissingEvidenceError(
                f"criterion evidence status is invalid: {criterion}",
                reason_code="CRITERION_EVIDENCE_INVALID",
            )
        if item["status"] == "UNVERIFIED":
            raise MissingEvidenceError(
                f"criterion remains UNVERIFIED: {criterion}",
                reason_code="CRITERION_UNVERIFIED",
            )
        try:
            validate_criterion_result_binding(
                criterion, item,
                schema_path=(
                    Path(__file__).resolve().parents[6] /
                    "study_docs/research/ductile-origami-warmstart/"
                    "protocol/schemas/verifier-attestation.schema.json"
                ),
                authorized_root=authorized_root,
                source_set_sha256=lock["m00_source_set_sha256"],
                protocol_lock_sha256=lock_sha256,
            )
        except ReportLifecycleError as exc:
            raise MissingEvidenceError(
                f"criterion evidence is stale or mismatched: "
                f"{criterion}: {exc.human_message}",
                reason_code="CRITERION_EVIDENCE_MISMATCH",
            ) from exc
        criteria[criterion] = item["status"]
        evidence[criterion] = item
    acc = [criteria[key] for key in _CRITERION_KEYS[:5]]
    if all(value == "PASS" for value in acc) and \
            criteria["M00.FAL.INSTRUMENTATION"] is False and \
            criteria["M00.STOP.MISSING-EVIDENCE"] is False:
        overall = "PASS"
    elif "FAIL" in acc or \
            criteria["M00.FAL.INSTRUMENTATION"] is True or \
            criteria["M00.STOP.MISSING-EVIDENCE"] is True:
        overall = "FAIL"
    elif "BLOCKED" in acc:
        overall = "BLOCKED"
    else:
        overall = "INCONCLUSIVE"
    for key in ("root_causes", "required_fixes", "evidence_gaps"):
        if not isinstance(document[key], list) or \
                any(not isinstance(value, str) or not value
                    for value in document[key]):
            raise MissingEvidenceError(
                "criterion evidence explanation fields are invalid",
                reason_code="CRITERION_EVIDENCE_INVALID",
            )
    if overall == "PASS" and any(
            document[key] for key in (
                "root_causes", "required_fixes", "evidence_gaps"
            )):
        raise MissingEvidenceError(
            "positive criterion evidence contains unresolved gaps",
            reason_code="CRITERION_EVIDENCE_INCONSISTENT",
        )
    if overall != "PASS" and not any(
            document[key] for key in (
                "root_causes", "required_fixes", "evidence_gaps"
            )):
        raise MissingEvidenceError(
            "non-positive criterion evidence lacks explanation",
            reason_code="CRITERION_EVIDENCE_INCONSISTENT",
        )
    return (
        criteria, evidence, overall,
        document["root_causes"], document["required_fixes"],
        document["evidence_gaps"],
    )


def verify_run(contract_path: str | Path, run_root: str | Path,
               attestation_path: str | Path, *,
               issuer_role: str = "implementer-self-check",
               criteria_evidence_path: str | Path | None = None) -> Path:
    store = ContractStore(contract_path)
    if issuer_role == "independent-verifier":
        M00ScopeGuard(
            _repo_root(store), contract_path
        ).verify("verification")
    lock_path = _repo_root(store) / store.base_contract["locks"][
        "protocol_lock_path"
    ]
    lock = ProtocolLock(store, _repo_root(store)).verify()
    root = Path(run_root).resolve()
    _verify_tree_checksums(root)
    for name, scenario, mode, run_kind in _bundle_specs(store):
        RawReconciler(root / "bundles" / name, contract_path).reconcile()
    adversarial_root = root / "adversarial"
    _verify_tree_checksums(adversarial_root)
    for name in ("continuous", "resumed"):
        RawReconciler(
            adversarial_root / "bundles" / name, contract_path
        ).reconcile()
    adversarial_summary = load_json_strict(
        adversarial_root / "adversarial-summary.json"
    )
    if adversarial_summary["overall"] != "PASS" or \
            not adversarial_summary["continuous_resume_parity"] or \
            not adversarial_summary["observational_run_ids_unique"]:
        raise MissingEvidenceError(
            "integrated adversarial ledger is not PASS",
            reason_code="ADVERSARIAL_LEDGER_NOT_PASS",
        )
    differential = load_json_strict(root / "differential-summary.json")
    projections = {
        name: _trajectory_projection(root / "bundles" / name)
        for name, scenario, mode, run_kind in _bundle_specs(store)
    }
    recomputed = {
        "fixed_off_repeat":
            projections["fixed-off-a"] == projections["fixed-off-b"],
        "fixed_off_on":
            projections["fixed-off-a"] == projections["fixed-on"],
        "early_stop_off_on":
            projections["early-off"] == projections["early-on"],
        "resume_continuous_off_on":
            projections["resume-continuous-off"] ==
            projections["resume-continuous-on"],
        "resume_durable_off_on":
            projections["resume-durable-off"] ==
            projections["resume-durable-on"],
        "continuous_durable_resume_equivalence":
            projections["resume-continuous-off"] ==
            projections["resume-durable-off"],
        "resume_continuous_repeat_off":
            projections["resume-continuous-off"] ==
            projections["resume-repeat-off"],
        "resume_continuous_repeat_on":
            projections["resume-continuous-on"] ==
            projections["resume-repeat-on"],
    }
    run_ids = [
        load_json_strict(
            root / "bundles" / name / "run-manifest.json"
        )["run_id"]
        for name, scenario, mode, run_kind in _bundle_specs(store)
    ]
    recomputed["observational_run_ids_unique"] = (
        len(run_ids) == len(set(run_ids))
    )
    if differential["comparisons"] != recomputed or \
            differential["overall"] != "PASS" or \
            differential["instrumentation_falsified"] or \
            not all(recomputed.values()):
        raise InstrumentationError("differential summary is not PASS")
    lock_sha = sha256_file(lock_path)
    if issuer_role == "independent-verifier":
        if criteria_evidence_path is None:
            raise MissingEvidenceError(
                "independent verification requires criterion-specific "
                "direct evidence",
                reason_code="CRITERION_EVIDENCE_MISSING",
            )
        whitelist = load_json_strict(
            _repo_root(store) / store.base_contract["locks"][
                "whitelist_path"
            ]
        )
        allowed_root = (
            _repo_root(store) / whitelist["generated_roots"][1]
        )
        criteria, criterion_evidence, overall, root_causes, \
            required_fixes, evidence_gaps = _independent_criterion_claims(
                criteria_evidence_path,
                lock=lock,
                lock_sha256=lock_sha,
                allowed_root=allowed_root,
                authorized_root=root.parent,
            )
    else:
        direct_path = root / "differential-summary.json"
        direct = {
            "artifact_path": os.fspath(direct_path),
            "artifact_sha256": sha256_file(direct_path),
            "source_set_sha256": lock["m00_source_set_sha256"],
            "protocol_lock_sha256": lock_sha,
            "fresh_evidence": [{
                "path": os.fspath(direct_path),
                "sha256": sha256_file(direct_path),
            }],
        }
        criteria = {
            "M00.ACC.OBS-SEMANTICS": "PASS",
            "M00.ACC.RECONCILE": "PASS",
            "M00.ACC.SPLIT-GUARD": "UNVERIFIED",
            "M00.ACC.BASELINE-GUARD": "UNVERIFIED",
            "M00.ACC.CONTRACT-LOCK": "UNVERIFIED",
            "M00.FAL.INSTRUMENTATION": False,
            "M00.STOP.MISSING-EVIDENCE": "UNVERIFIED",
        }
        criterion_evidence = {
            key: {
                "status": value,
                **(
                    direct if value != "UNVERIFIED" else {
                        "artifact_path": None,
                        "artifact_sha256": None,
                        "source_set_sha256":
                            lock["m00_source_set_sha256"],
                        "protocol_lock_sha256": lock_sha,
                        "fresh_evidence": [],
                    }
                ),
            }
            for key, value in criteria.items()
        }
        overall = "BLOCKED"
        root_causes = []
        required_fixes = []
        evidence_gaps = [
            "Implementer self-check does not independently verify split, "
            "baseline, contract-lock, or negative missing-evidence probes."
        ]
    attestation = {
        "schema_version": "1.0",
        "issuer_role": issuer_role,
        "issuer": (
            "independent-verifier" if issuer_role == "independent-verifier"
            else "m00-implementer-self-check"
        ),
        "issued_at": _utc_now(),
        "overall": overall,
        "source_set_sha256": lock["m00_source_set_sha256"],
        "contract_sha256": store.base_canonical_sha256,
        "effective_contract_sha256": store.effective_sha256,
        "protocol_lock_sha256": lock_sha,
        "run_root": os.fspath(root),
        "bundle_checksum_manifest_sha256": sha256_file(
            root / "differential-checksums.sha256"
        ),
        "differential_summary_sha256": sha256_file(
            root / "differential-summary.json"
        ),
        "criteria": criteria,
        "criterion_evidence": criterion_evidence,
        "root_causes": root_causes,
        "required_fixes": required_fixes,
        "evidence_gaps": evidence_gaps,
    }
    schema = load_json_strict(
        _schema(store, "verifier-attestation.schema.json")
    )
    from .canonical import validate_instance
    validate_instance(attestation, schema, label="self-check attestation")
    target = Path(attestation_path)
    if target.exists() or target.is_symlink():
        raise MissingEvidenceError(
            "attestation output already exists",
            reason_code="ATTESTATION_PREEXISTS",
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        stream.write(canonical_json_text(attestation) + "\n")
    return target


def validate_contract(contract_path: str | Path) -> None:
    store = ContractStore(contract_path)
    protocol = store.protocol_root
    ShapeRegistry(
        protocol / "shape-registry.csv",
        protocol / "schemas/shape-registry.schema.json",
    )
    BaselineRegistry(
        protocol / "baseline-registry.json",
        protocol / "schemas/baseline-registry.schema.json",
    )
    RevisionRegistry(
        protocol / "revision-registry.json",
        protocol / "schemas/revision-registry.schema.json",
        repo_root=_repo_root(store),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m Tensile.ductile.m00.runner")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-contract")
    validate.add_argument("--contract", default=os.fspath(CANONICAL_CONTRACT))
    lock = sub.add_parser("validate-lock")
    lock.add_argument("--contract", default=os.fspath(CANONICAL_CONTRACT))
    initialize = sub.add_parser("initialize-lock")
    initialize.add_argument(
        "--contract", default=os.fspath(CANONICAL_CONTRACT)
    )
    initialize.add_argument("--owner", required=True)
    scope = sub.add_parser("verify-scope")
    scope.add_argument("--repo-root", required=True)
    scope.add_argument("--contract", default=os.fspath(CANONICAL_CONTRACT))
    scope.add_argument("--phase", choices=("implementation", "verification"),
                       required=True)
    differential = sub.add_parser("differential")
    differential.add_argument(
        "--contract", default=os.fspath(CANONICAL_CONTRACT)
    )
    differential.add_argument("--output", required=True)
    adversarial = sub.add_parser("adversarial-ledger")
    adversarial.add_argument(
        "--contract", default=os.fspath(CANONICAL_CONTRACT)
    )
    adversarial.add_argument("--output", required=True)
    verify = sub.add_parser("verify-run")
    verify.add_argument("--contract", default=os.fspath(CANONICAL_CONTRACT))
    verify.add_argument("--run", required=True)
    verify.add_argument("--attestation", required=True)
    verify.add_argument("--criteria-evidence")
    verify.add_argument(
        "--issuer-role",
        choices=("implementer-self-check", "independent-verifier"),
        default="implementer-self-check",
    )
    render = sub.add_parser("render-report")
    render.add_argument("--contract", default=os.fspath(CANONICAL_CONTRACT))
    render.add_argument("--attestation", required=True)
    render.add_argument("--output", required=True)
    verify_report = sub.add_parser("verify-report")
    verify_report.add_argument(
        "--contract", default=os.fspath(CANONICAL_CONTRACT)
    )
    verify_report.add_argument("--attestation", required=True)
    verify_report.add_argument("--report", required=True)

    child = sub.add_parser("_child-run")
    child.add_argument("--contract", default=os.fspath(CANONICAL_CONTRACT))
    child.add_argument("--output", required=True)
    child.add_argument("--scenario", required=True)
    child.add_argument("--observer-mode", choices=("off", "on"), required=True)
    child.add_argument("--run-kind", choices=("continuous",), required=True)
    child.add_argument("--run-id", required=True)
    interrupt = sub.add_parser("_interrupt-run")
    interrupt.add_argument(
        "--contract", default=os.fspath(CANONICAL_CONTRACT)
    )
    interrupt.add_argument("--output", required=True)
    interrupt.add_argument("--scenario", required=True)
    interrupt.add_argument(
        "--observer-mode", choices=("off", "on"), required=True
    )
    interrupt.add_argument("--run-id", required=True)
    resume = sub.add_parser("_resume-run")
    resume.add_argument(
        "--contract", default=os.fspath(CANONICAL_CONTRACT)
    )
    resume.add_argument("--state", required=True)
    resume.add_argument("--output", required=True)
    adversarial_child = sub.add_parser("_adversarial-run")
    adversarial_child.add_argument(
        "--contract", default=os.fspath(CANONICAL_CONTRACT)
    )
    adversarial_child.add_argument("--output", required=True)
    adversarial_child.add_argument("--run-id", required=True)
    adversarial_interrupt = sub.add_parser("_adversarial-interrupt")
    adversarial_interrupt.add_argument(
        "--contract", default=os.fspath(CANONICAL_CONTRACT)
    )
    adversarial_interrupt.add_argument("--output", required=True)
    adversarial_interrupt.add_argument("--run-id", required=True)
    adversarial_resume = sub.add_parser("_adversarial-resume")
    adversarial_resume.add_argument(
        "--contract", default=os.fspath(CANONICAL_CONTRACT)
    )
    adversarial_resume.add_argument("--state", required=True)
    adversarial_resume.add_argument("--output", required=True)
    ledger_worker = sub.add_parser("_ledger-worker")
    ledger_worker.add_argument("--input", required=True)
    worker = sub.add_parser("_cpu-worker")
    worker.add_argument("--input", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-contract":
            validate_contract(args.contract)
        elif args.command == "validate-lock":
            store = ContractStore(args.contract)
            ProtocolLock(store, _repo_root(store)).verify()
        elif args.command == "initialize-lock":
            store = ContractStore(args.contract)
            ProtocolLock(store, _repo_root(store)).initialize(args.owner)
        elif args.command == "verify-scope":
            M00ScopeGuard(args.repo_root, args.contract).verify(args.phase)
        elif args.command == "differential":
            run_differential(args.contract, args.output)
        elif args.command == "adversarial-ledger":
            run_adversarial_ledger(args.contract, args.output)
        elif args.command == "verify-run":
            verify_run(
                args.contract, args.run, args.attestation,
                issuer_role=args.issuer_role,
                criteria_evidence_path=args.criteria_evidence,
            )
        elif args.command == "render-report":
            store = ContractStore(args.contract)
            render_m00_report(
                args.contract, args.attestation, args.output,
                repo_root=_repo_root(store),
            )
        elif args.command == "verify-report":
            store = ContractStore(args.contract)
            verify_m00_report(
                args.contract, args.attestation, args.report,
                repo_root=_repo_root(store),
            )
        elif args.command == "_child-run":
            _run_bundle(
                contract_path=args.contract, output=args.output,
                scenario_id=args.scenario,
                observer_mode=args.observer_mode,
                run_kind=args.run_kind,
                run_id=args.run_id,
            )
        elif args.command == "_interrupt-run":
            _interrupt_bundle(
                contract_path=args.contract, output=args.output,
                scenario_id=args.scenario,
                observer_mode=args.observer_mode,
                run_id=args.run_id,
            )
        elif args.command == "_resume-run":
            _resume_bundle(
                contract_path=args.contract, state_root=args.state,
                output=args.output,
            )
        elif args.command == "_adversarial-run":
            _run_adversarial_bundle(
                contract_path=args.contract, output=args.output,
                run_id=args.run_id,
            )
        elif args.command == "_adversarial-interrupt":
            _interrupt_adversarial_bundle(
                contract_path=args.contract, output=args.output,
                run_id=args.run_id,
            )
        elif args.command == "_adversarial-resume":
            _resume_adversarial_bundle(
                contract_path=args.contract, state_root=args.state,
                output=args.output,
            )
        elif args.command == "_ledger-worker":
            return _ledger_worker(args.input)
        elif args.command == "_cpu-worker":
            return _cpu_worker(args.input)
        return 0
    except M00Error as exc:
        sys.stderr.write(canonical_json_text(exc.as_dict()) + "\n")
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
