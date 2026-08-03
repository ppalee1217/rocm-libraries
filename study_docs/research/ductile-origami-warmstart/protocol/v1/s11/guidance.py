# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""S11 p0/q/p1 guidance, entropy, shuffle, and consumer round-trip."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

from .canonical import canonical_sha256
from .sampling import derive_uint128


class GuidanceError(ValueError):
    """Guidance violates probability, entropy, shuffle, or consumer semantics."""


def normalized_entropy(probabilities: Sequence[float]) -> float:
    if len(probabilities) < 2 or any(
        type(value) is not float or not math.isfinite(value) or value <= 0.0
        for value in probabilities
    ):
        raise GuidanceError("entropy probabilities must be finite and strictly positive")
    if not math.isclose(sum(probabilities), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise GuidanceError("entropy probabilities do not sum to one")
    return -sum(value * math.log(value) for value in probabilities) / math.log(len(probabilities))


def construct_gene_probabilities(
    *,
    candidate_order: Sequence[str],
    baseline: Mapping[str, float],
    marginals: Mapping[str, float],
    trusted: Sequence[str],
    lambda_value: float,
    epsilon: float = 0.20,
) -> dict[str, Any]:
    if epsilon != 0.20 or lambda_value < 0 or not math.isfinite(lambda_value):
        raise GuidanceError("epsilon/lambda binding changed")
    if list(baseline) != list(candidate_order) or set(trusted) != set(marginals):
        raise GuidanceError("candidate order, trusted set, or marginals differ")
    if len(set(candidate_order)) != len(candidate_order) or len(trusted) < 2:
        raise GuidanceError("guided gene needs at least two unique trusted candidates")
    p0 = [float(baseline[candidate_id]) for candidate_id in candidate_order]
    if any(value <= 0 or not math.isfinite(value) for value in p0) or not math.isclose(
        sum(p0), 1.0, rel_tol=0.0, abs_tol=1e-12
    ):
        raise GuidanceError("baseline is not a positive probability vector")
    minimum = min(marginals.values())
    exponentials = {
        candidate_id: math.exp(lambda_value * (marginals[candidate_id] - minimum))
        for candidate_id in trusted
    }
    denominator = sum(exponentials.values())
    q = [
        exponentials[candidate_id] / denominator if candidate_id in exponentials else 0.0
        for candidate_id in candidate_order
    ]
    p1 = [epsilon * base + (1.0 - epsilon) * guided for base, guided in zip(p0, q)]
    for index, candidate_id in enumerate(candidate_order):
        if candidate_id not in trusted and p1[index] != epsilon * p0[index]:
            raise GuidanceError("untrusted mass was not exactly epsilon*p0")
    return {
        "candidate_order": list(candidate_order),
        "p0": p0,
        "q": q,
        "p1": p1,
        "lambda": lambda_value,
        "normalized_entropy": normalized_entropy(p1),
        "untrusted_rule": "exactly_0.20_times_p0",
    }


def select_global_lambda(
    gene_inputs: Mapping[str, Mapping[str, Any]], *, entropy_min: float = 0.80
) -> dict[str, Any]:
    """Select largest shared lambda in {0,.25,...,8} satisfying every guided gene."""

    if not gene_inputs or entropy_min != 0.80:
        raise GuidanceError("global lambda requires guided genes and entropy floor 0.80")
    chosen = None
    bundles = None
    for quarter_step in range(32, -1, -1):
        lambda_value = quarter_step * 0.25
        candidate_bundles = {
            gene: construct_gene_probabilities(lambda_value=lambda_value, **inputs)
            for gene, inputs in gene_inputs.items()
        }
        if all(bundle["normalized_entropy"] >= entropy_min for bundle in candidate_bundles.values()):
            chosen, bundles = lambda_value, candidate_bundles
            break
    assert chosen is not None and bundles is not None
    return {
        "global_lambda": chosen,
        "positive_lambda": chosen > 0.0,
        "entropy_min": entropy_min,
        "genes": bundles,
    }


def deterministic_nonidentity_shuffle(
    *,
    candidate_order: Sequence[str],
    trusted: Sequence[str],
    q: Sequence[float],
    master_nonce: str,
    gene: str,
) -> dict[str, Any]:
    """Permute only trusted q mass; untrusted positions remain fixed."""

    if len(candidate_order) != len(q) or len(trusted) < 2:
        raise GuidanceError("shuffle vectors/trusted set are invalid")
    trusted_indices = [index for index, item in enumerate(candidate_order) if item in set(trusted)]
    if len(trusted_indices) != len(trusted):
        raise GuidanceError("shuffle trusted IDs are outside candidate order")
    rng = np.random.Generator(np.random.PCG64(derive_uint128(master_nonce, "guidance-shuffle", gene)))
    permutation = list(rng.permutation(len(trusted_indices)))
    if permutation == list(range(len(permutation))):
        permutation = permutation[1:] + permutation[:1]
    shuffled = list(float(value) for value in q)
    original_values = [shuffled[index] for index in trusted_indices]
    for destination, source in enumerate(permutation):
        shuffled[trusted_indices[destination]] = original_values[source]
    for index in set(range(len(q))) - set(trusted_indices):
        if shuffled[index] != q[index]:
            raise GuidanceError("shuffle changed untrusted mass")
    mapping = {
        candidate_order[trusted_indices[destination]]: candidate_order[trusted_indices[source]]
        for destination, source in enumerate(permutation)
    }
    return {
        "q_shuffled": shuffled,
        "mapping": mapping,
        "nonidentity": mapping != {item: item for item in trusted},
        "multiset_preserved": sorted(shuffled) == sorted(float(value) for value in q),
    }


def float32_inverse_cost_roundtrip(
    probabilities: Sequence[float], *, weight_beta: float, atol: float = 2e-7
) -> dict[str, Any]:
    """Exercise Ductile's production exp(-beta*(w-min)) consumer in float32."""

    if type(weight_beta) is not float or weight_beta <= 0 or not math.isfinite(weight_beta):
        raise GuidanceError("weight_beta must be a bound positive float")
    vector = np.asarray(probabilities, dtype=np.float64)
    if np.any(~np.isfinite(vector)) or np.any(vector <= 0) or not math.isclose(
        float(vector.sum()), 1.0, rel_tol=0.0, abs_tol=1e-12
    ):
        raise GuidanceError("round-trip probabilities are invalid")
    costs32 = np.asarray(-np.log(vector) / weight_beta, dtype=np.float32)
    consumer = np.exp(-weight_beta * (costs32.astype(np.float64) - float(costs32.min())))
    consumer /= consumer.sum()
    maximum_error = float(np.max(np.abs(consumer - vector)))
    return {
        "weights_float32": [float(value) for value in costs32],
        "consumer_probabilities": [float(value) for value in consumer],
        "maximum_absolute_error": maximum_error,
        "atol": atol,
        "pass": maximum_error <= atol,
        "weights_sha256": canonical_sha256([float(value) for value in costs32]),
    }


def guidance_bundle_identity(bundle: Mapping[str, Any]) -> str:
    return canonical_sha256(dict(bundle))
