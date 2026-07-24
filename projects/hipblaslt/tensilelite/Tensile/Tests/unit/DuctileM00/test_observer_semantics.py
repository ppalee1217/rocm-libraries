# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

import random
import tempfile
import unittest
from pathlib import Path

import numpy as np

from Tensile.ductile.core.population import Individual, Population
from Tensile.ductile.m00.canonical import canonical_json_bytes
from Tensile.ductile.m00.contract import ContractStore
from Tensile.ductile.m00.runner import (
    _seed_sequence_from_state,
    build_actual_ga,
    normalize_checkpoint,
)


REPO = Path(__file__).resolve().parents[7]
CONTRACT = REPO / (
    "study_docs/research/ductile-origami-warmstart/protocol/"
    "experiment-contract.yaml"
)


class Recorder:
    def __init__(self):
        self.generations = []
        self.space = None

    def __call__(self, configs):
        matrix = np.asarray([
            [1.0 + sum(config.values()) / 100.0 for config in configs],
            [1.2 + sum(config.values()) / 100.0 for config in configs],
        ], dtype=np.float64)
        self.generations.append({
            "configs": configs,
            "scores": matrix.tolist(),
            "python_state": repr(random.getstate()),
            "numpy_state": repr(np.random.get_state()),
            "seed_state": dict(self.space.seed_seq.state),
        })
        return matrix


def run_actual(store, scenario, root, observer=None):
    profile = store.profile(scenario)
    recorder = Recorder()
    checkpoint = root / f"{scenario}.checkpoint"
    ga = build_actual_ga(
        store.effective_contract, profile, recorder, checkpoint,
        observer=observer,
    )
    recorder.space = ga.space
    champion, fitness = ga.optimize()
    normalize_checkpoint(checkpoint)
    return {
        "generations": recorder.generations,
        "champion": champion,
        "fitness": fitness.tolist(),
        "python_state": repr(random.getstate()),
        "numpy_state": repr(np.random.get_state()),
        "seed_state": dict(ga.space.seed_seq.state),
        "checkpoint": checkpoint.read_bytes(),
        "reason": ga.termination_reason,
        "final_generation": ga.final_generation,
    }


class TestObserverSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = ContractStore(CONTRACT)

    def test_off_off_and_off_on_are_byte_exact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            off_a = run_actual(self.store, "fixed_horizon", root / "a")
            off_b = run_actual(self.store, "fixed_horizon", root / "b")
            events = []
            on = run_actual(
                self.store, "fixed_horizon", root / "on", events.append
            )
        self.assertEqual(off_a, off_b)
        self.assertEqual(off_a, on)
        self.assertIn("initial_population", [event.kind for event in events])
        self.assertIn("fitness_matrix", [event.kind for event in events])
        self.assertIn("final_champion", [event.kind for event in events])

    def test_observer_must_be_callable_or_none(self):
        profile = self.store.profile("fixed_horizon")
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "observer"):
                build_actual_ga(
                    self.store.effective_contract,
                    profile,
                    lambda configs: np.ones((2, len(configs))),
                    Path(temporary) / "checkpoint",
                    observer=object(),
                )

    def test_early_stop_is_observer_neutral(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            off = run_actual(self.store, "early_stop", root / "off")
            on = run_actual(
                self.store, "early_stop", root / "on", lambda event: None
            )
        self.assertEqual(off, on)
        self.assertEqual("early_stop", off["reason"])
        self.assertLess(
            off["final_generation"],
            self.store.profile("early_stop").n_gen,
        )

    def test_checkpoint_resume_matches_continuous(self):
        profile = self.store.profile("checkpoint_resume")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            continuous = run_actual(
                self.store, "checkpoint_resume", root / "continuous"
            )
            recorder = Recorder()
            checkpoint = root / "segmented.checkpoint"
            first = build_actual_ga(
                self.store.effective_contract,
                profile,
                recorder,
                checkpoint,
                n_gen=profile.split_generation,
            )
            recorder.space = first.space
            first.optimize()
            normalize_checkpoint(checkpoint)
            seed_state = dict(first.space.seed_seq.state)
            second = build_actual_ga(
                self.store.effective_contract,
                profile,
                recorder,
                checkpoint,
            )
            second.load(checkpoint)
            second.space.seed_seq = _seed_sequence_from_state(seed_state)
            recorder.space = second.space
            champion, fitness = second.optimize()
            normalize_checkpoint(checkpoint)
            segmented = {
                "generations": recorder.generations,
                "champion": champion,
                "fitness": fitness.tolist(),
                "python_state": repr(random.getstate()),
                "numpy_state": repr(np.random.get_state()),
                "seed_state": dict(second.space.seed_seq.state),
                "checkpoint": checkpoint.read_bytes(),
                "reason": second.termination_reason,
                "final_generation": second.final_generation,
            }
        self.assertEqual(continuous, segmented)

    def test_payload_is_detached_and_recursively_immutable(self):
        captured = []
        with tempfile.TemporaryDirectory() as temporary:
            run_actual(
                self.store, "fixed_horizon", Path(temporary), captured.append
            )
        initial = next(
            event for event in captured if event.kind == "initial_population"
        )
        with self.assertRaises(TypeError):
            initial.payload["new"] = 1
        with self.assertRaises(TypeError):
            initial.payload["ordered_configs"][0]["a"] = 99
        canonical_json_bytes(initial.payload)

    def test_observer_failure_propagates_without_rng_drift(self):
        callback_state = {}

        def failing(event):
            callback_state["python"] = random.getstate()
            callback_state["numpy"] = np.random.get_state()
            random.random()
            np.random.random()
            raise OSError("sink failed")

        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(OSError, "sink failed"):
                run_actual(
                    self.store, "fixed_horizon",
                    Path(temporary), failing,
                )
        self.assertEqual(callback_state["python"], random.getstate())
        np.testing.assert_equal(callback_state["numpy"], np.random.get_state())

    def test_both_global_rngs_are_exercised(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_actual(
                self.store, "fixed_horizon", Path(temporary)
            )
        first = result["generations"][0]
        last = result["generations"][-1]
        self.assertNotEqual(first["python_state"], last["python_state"])
        self.assertNotEqual(first["numpy_state"], last["numpy_state"])

    def test_pure_numpy_hamming_matches_exact_pairwise_definition(self):
        population = Population([
            Individual({"a": 0, "b": 0}),
            Individual({"a": 0, "b": 1}),
            Individual({"a": 1, "b": 1}),
        ])
        self.assertAlmostEqual(2.0 / 3.0, population.diversity())
        self.assertEqual(
            {"a": 2.0 / 3.0, "b": 2.0 / 3.0},
            population.diversity(reduce=False),
        )


if __name__ == "__main__":
    unittest.main()
