# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Frozen S11 model-only statistics with occurrence-level multiplicity."""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from typing import Any, Mapping, Sequence

import numpy as np

from .canonical import canonical_sha256
from .sampling import derive_uint128


class StatisticsError(ValueError):
    """A statistical input or frozen test definition is invalid."""


ARM_SENSITIVITY_ESS_MIN_FRACTION = 0.05


def type7_quantile(values: Sequence[float], probability: float) -> float:
    """Hyndman--Fan Type 7, implemented explicitly for auditability."""

    if not values or not 0.0 <= probability <= 1.0:
        raise StatisticsError("quantile input/probability is invalid")
    ordered = sorted(float(value) for value in values)
    if any(not math.isfinite(value) for value in ordered):
        raise StatisticsError("quantile values must be finite")
    h = (len(ordered) - 1) * probability
    lower = int(math.floor(h))
    upper = int(math.ceil(h))
    fraction = h - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def _midranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        midrank = ((cursor + 1) + end) / 2.0
        for position in range(cursor, end):
            ranks[order[position]] = midrank
        cursor = end
    return ranks


def midrank_latency_benefits(
    rows: Sequence[Mapping[str, Any]], *, reducer: str
) -> list[dict[str, Any]]:
    """Convert all-size native latency into rank benefit using actual GA reducer."""

    if reducer != "max":
        raise StatisticsError("S11 actual size reducer must remain exactly max")
    if len(rows) < 2:
        raise StatisticsError("midrank benefit requires at least two identities")
    width = None
    matrices: list[list[float]] = []
    for row in rows:
        latencies = row.get("latencies")
        if type(latencies) is not list or not latencies:
            raise StatisticsError("latency row is absent")
        vector = [
            item["predicted_latency"] if type(item) is dict else item for item in latencies
        ]
        if any(type(value) is not float or not math.isfinite(value) or value <= 0 for value in vector):
            raise StatisticsError("latencies must be finite positive floats")
        if width is None:
            width = len(vector)
        if len(vector) != width:
            raise StatisticsError("locked-size latency vector is partial")
        matrices.append(vector)
    if width != 3:
        raise StatisticsError("S11 requires all three locked sizes")
    per_size_percentiles: list[list[float]] = [[0.0] * width for _ in rows]
    for size_index in range(width):
        ranks = _midranks([row[size_index] for row in matrices])
        for row_index, rank in enumerate(ranks):
            per_size_percentiles[row_index][size_index] = (rank - 0.5) / len(rows)
    result = []
    for source, percentiles in zip(rows, per_size_percentiles):
        size_benefits = [1.0 - value for value in percentiles]
        result.append(
            {
                "semantic_identity": source["semantic_identity"],
                "size_latency_percentile": percentiles,
                "size_benefits": size_benefits,
                "benefit": max(size_benefits),
            }
        )
    return result


def query_terminal_global_ecdf(
    global_rows: Sequence[Mapping[str, Any]],
    query_rows: Sequence[Mapping[str, Any]],
    *,
    reducer: str = "max",
) -> list[dict[str, Any]]:
    """Query conditional observations against the unchanged terminal global ECDF."""

    if reducer != "max" or not global_rows:
        raise StatisticsError("terminal ECDF requires the sealed max reducer and global rows")
    global_matrix = []
    for row in global_rows:
        values = [item["predicted_latency"] if type(item) is dict else item for item in row["latencies"]]
        if len(values) != 3 or any(
            type(value) is not float or not math.isfinite(value) or value <= 0 for value in values
        ):
            raise StatisticsError("terminal global ECDF row is incomplete")
        global_matrix.append(values)
    result = []
    for row in query_rows:
        values = [item["predicted_latency"] if type(item) is dict else item for item in row["latencies"]]
        if len(values) != 3 or any(
            type(value) is not float or not math.isfinite(value) or value <= 0 for value in values
        ):
            raise StatisticsError("conditional ECDF query lacks a locked size")
        percentiles = []
        for size_index, value in enumerate(values):
            reference = [global_value[size_index] for global_value in global_matrix]
            less = sum(item < value for item in reference)
            equal = sum(item == value for item in reference)
            percentiles.append((less + 0.5 * equal) / len(reference))
        result.append(
            {
                "semantic_identity": row["semantic_identity"],
                "size_latency_percentile": percentiles,
                "size_benefits": [1.0 - value for value in percentiles],
                "benefit": max(1.0 - value for value in percentiles),
                "reference": "terminal_global_occurrence_weighted_mid_ecdf",
            }
        )
    return result


def _score_rows_against_global(
    global_rows: Sequence[Mapping[str, Any]],
    query_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Rebuild the terminal ECDF and retain the complete occurrence records."""

    scored = query_terminal_global_ecdf(global_rows, query_rows)
    return [{**dict(source), **projection} for source, projection in zip(query_rows, scored)]


def _rebuild_gene_cells(
    *,
    global_rows: Sequence[Mapping[str, Any]],
    conditional_cells: Mapping[str, Sequence[Mapping[str, Any]]],
    trusted: Sequence[str],
    gene: str,
) -> tuple[dict[str, list[dict[str, Any]]], float]:
    """Rebuild ECDF, occurrence benefits, global mean, and one gene's cells."""

    trusted_order = list(trusted)
    if len(trusted_order) < 2 or len(set(trusted_order)) != len(trusted_order):
        raise StatisticsError("a rebuilt gene needs at least two unique trusted values")
    if set(conditional_cells) != set(trusted_order):
        raise StatisticsError("conditional cells differ from the frozen trusted set")
    scored_global = _score_rows_against_global(global_rows, global_rows)
    global_mean_value = sum(float(row["benefit"]) for row in scored_global) / len(scored_global)
    cells: dict[str, list[dict[str, Any]]] = {candidate_id: [] for candidate_id in trusted_order}
    for row in scored_global:
        assignments = row.get("candidate_ids")
        if type(assignments) is not dict:
            raise StatisticsError("global occurrence gene assignment is absent")
        candidate_id = assignments.get(gene)
        if candidate_id in cells:
            cells[candidate_id].append(row)
    for candidate_id in trusted_order:
        cells[candidate_id].extend(
            _score_rows_against_global(global_rows, conditional_cells[candidate_id])
        )
        if not cells[candidate_id]:
            raise StatisticsError("trusted rebuilt cell is empty")
    return cells, global_mean_value


def shrinkage_mean(sum_b: float, n: int, global_mean: float, *, alpha: int = 32) -> float:
    if any(not math.isfinite(value) for value in (sum_b, global_mean)):
        raise StatisticsError("shrinkage inputs must be finite")
    if type(n) is not int or n < 0 or type(alpha) is not int or alpha != 32:
        raise StatisticsError("S11 shrinkage alpha must remain exactly 32")
    return (sum_b + alpha * global_mean) / (n + alpha)


def gene_marginals(
    cell_benefits: Mapping[str, Sequence[float]], *, global_mean: float, alpha: int = 32
) -> dict[str, float]:
    if len(cell_benefits) < 2:
        raise StatisticsError("a testable gene needs at least two trusted values")
    return {
        candidate_id: shrinkage_mean(
            sum(float(value) for value in benefits), len(benefits), global_mean, alpha=alpha
        )
        for candidate_id, benefits in cell_benefits.items()
    }


def alpha0_shrinkage_sensitivity(
    *,
    marginals_alpha32: Mapping[str, float],
    cells: Mapping[str, Mapping[str, Any]],
    global_mean: float,
    best: str,
    worst: str,
    alpha: int = 32,
) -> dict[str, Any]:
    """Report the unshrunk marginal displacement without changing the estimand."""

    if (
        type(alpha) is not int
        or alpha != 32
        or type(global_mean) not in (int, float)
        or not math.isfinite(float(global_mean))
    ):
        raise StatisticsError("alpha=0 sensitivity requires the frozen alpha=32 reference")
    candidate_order = list(marginals_alpha32)
    if best not in marginals_alpha32 or worst not in marginals_alpha32:
        raise StatisticsError("alpha=0 best/worst reference is outside trusted marginals")
    if any(
        type(value) not in (int, float) or not math.isfinite(float(value))
        for value in marginals_alpha32.values()
    ):
        raise StatisticsError("alpha=32 reference marginals must be finite")

    attenuation: dict[str, float] = {}
    mu_unshrunk: dict[str, float | None] = {}
    displacement: dict[str, float | None] = {}
    reasons: dict[str, str | None] = {}
    for candidate_id in candidate_order:
        cell = cells.get(candidate_id)
        if type(cell) is not dict or type(cell.get("Dscore")) is not list:
            raise StatisticsError("alpha=0 sensitivity cell is malformed")
        sum_b = cell.get("sum_b_gv")
        if type(sum_b) not in (int, float) or not math.isfinite(float(sum_b)):
            raise StatisticsError("alpha=0 sensitivity benefit sum must be finite")
        n = len(cell["Dscore"])
        attenuation[candidate_id] = n / (n + alpha)
        if n == 0:
            mu_unshrunk[candidate_id] = None
            displacement[candidate_id] = None
            reasons[candidate_id] = "n_gv_zero"
            continue
        unshrunk = float(sum_b) / n
        mu_unshrunk[candidate_id] = unshrunk
        displacement[candidate_id] = float(marginals_alpha32[candidate_id]) - unshrunk
        reasons[candidate_id] = None

    estimable_values = [
        candidate_id
        for candidate_id in candidate_order
        if mu_unshrunk[candidate_id] is not None
    ]
    estimable = len(estimable_values) >= 2
    if estimable:
        order_index = {
            candidate_id: index for index, candidate_id in enumerate(candidate_order)
        }
        best0 = max(
            estimable_values,
            key=lambda key: (mu_unshrunk[key], -order_index[key]),
        )
        worst0 = min(
            estimable_values,
            key=lambda key: (mu_unshrunk[key], order_index[key]),
        )
    else:
        best0 = None
        worst0 = None
    return {
        "attenuation": attenuation,
        "mu_unshrunk": mu_unshrunk,
        "mu_unshrunk_reason": reasons,
        "displacement": displacement,
        "alpha0_best": best0,
        "alpha0_worst": worst0,
        "estimable": estimable,
        "alpha0_bestworst_flip": (best0, worst0) != (best, worst),
    }


def survivorship_yield(*, cell: Mapping[str, Any]) -> dict[str, Any]:
    """Report per-value execution yield and score attrition."""

    if type(cell) is not dict or any(
        type(cell.get(field)) is not list for field in ("Draw", "Dexec", "Dscore")
    ):
        raise StatisticsError("survivorship cell is malformed")
    n_draw = len(cell["Draw"])
    n_exec = len(cell["Dexec"])
    n_score = len(cell["Dscore"])
    if n_exec > n_draw or n_score > n_exec:
        raise StatisticsError("survivorship counts are not nested")
    coverage = cell.get("Cscore_occ_gv")
    if coverage is not None and (
        type(coverage) not in (int, float) or not math.isfinite(float(coverage))
    ):
        raise StatisticsError("survivorship score coverage is malformed")
    return {
        "Y_exec_gv": None if n_draw == 0 else n_exec / n_draw,
        "Y_exec_reason": "draw_empty" if n_draw == 0 else None,
        "Cscore_occ_gv": coverage,
        "n_draw": n_draw,
        "n_exec": n_exec,
        "n_score": n_score,
        "exec_attrition_share": None if n_draw == 0 else (n_draw - n_exec) / n_draw,
        "score_attrition_share": None if n_exec == 0 else (n_exec - n_score) / n_exec,
    }


def _alpha0_gene_marginals(
    cell_rows: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, float]:
    if len(cell_rows) < 2 or any(not rows for rows in cell_rows.values()):
        raise StatisticsError("alpha=0 marginals require two nonempty trusted cells")
    result = {}
    for candidate_id, rows in cell_rows.items():
        benefits = [float(row["benefit"]) for row in rows]
        if any(not math.isfinite(value) for value in benefits):
            raise StatisticsError("alpha=0 marginal benefits must be finite")
        result[candidate_id] = sum(benefits) / len(benefits)
    return result


def alpha0_joint_permutation_test(
    *,
    global_rows: Sequence[Mapping[str, Any]],
    conditional_cells: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]],
    trusted_values: Mapping[str, Sequence[str]],
    observed_marginals: Mapping[str, Mapping[str, float]],
    master_nonce: str,
    replicates: int = 2000,
) -> dict[str, Any]:
    """Diagnostic-only joint permutation using unshrunk cell means."""

    if replicates != 2000:
        raise StatisticsError("S11 alpha=0 diagnostic requires exactly 2,000 permutations")
    genes = sorted(trusted_values)
    if genes != sorted(observed_marginals) or genes != sorted(conditional_cells):
        raise StatisticsError("alpha=0 permutation gene sets differ")
    if not global_rows:
        raise StatisticsError("alpha=0 global permutation corpus is incomplete")
    for row in global_rows:
        if type(row.get("candidate_ids")) is not dict:
            raise StatisticsError("alpha=0 global occurrence gene assignment is absent")
    _score_rows_against_global(global_rows, global_rows)

    own_null: dict[str, list[float]] = {gene: [] for gene in genes}
    max_null: list[float] = []
    for replicate in range(replicates):
        global_rng = np.random.Generator(
            np.random.PCG64(
                derive_uint128(master_nonce, "permutation-global", replicate)
            )
        )
        assignment_order = global_rng.permutation(len(global_rows))
        global_permuted = []
        for row, assignment_index in zip(global_rows, assignment_order):
            rebuilt = dict(row)
            rebuilt["candidate_ids"] = dict(
                global_rows[int(assignment_index)]["candidate_ids"]
            )
            global_permuted.append(rebuilt)
        replicate_sensitivities = []
        for gene in genes:
            trusted = list(trusted_values[gene])
            if len(trusted) < 2 or set(conditional_cells[gene]) != set(trusted):
                raise StatisticsError(
                    "alpha=0 permutation conditional cells differ from trusted values"
                )
            if any(not conditional_cells[gene][candidate_id] for candidate_id in trusted):
                raise StatisticsError("alpha=0 trusted permutation cell is empty")
            pooled = [
                row
                for candidate_id in trusted
                for row in conditional_cells[gene][candidate_id]
            ]
            conditional_rng = np.random.Generator(
                np.random.PCG64(
                    derive_uint128(
                        master_nonce,
                        "permutation-conditional",
                        gene,
                        replicate,
                    )
                )
            )
            permuted_conditional = [
                pooled[index]
                for index in conditional_rng.permutation(len(pooled))
            ]
            offsets = {}
            cursor = 0
            for candidate_id in trusted:
                count = len(conditional_cells[gene][candidate_id])
                offsets[candidate_id] = permuted_conditional[cursor : cursor + count]
                cursor += count
            rebuilt_cells, _ = _rebuild_gene_cells(
                global_rows=global_permuted,
                conditional_cells=offsets,
                trusted=trusted,
                gene=gene,
            )
            statistic = sensitivity(_alpha0_gene_marginals(rebuilt_cells))
            own_null[gene].append(statistic)
            replicate_sensitivities.append(statistic)
        max_null.append(max(replicate_sensitivities))

    family_p95 = type7_quantile(max_null, 0.95)
    gene_results = {}
    for gene in genes:
        observed = sensitivity(observed_marginals[gene])
        own_p95 = type7_quantile(own_null[gene], 0.95)
        gene_results[gene] = {
            "observed_S": observed,
            "own_null_p95_type7": own_p95,
            "familywise_max_null_p95_type7": family_p95,
            "own_strict_pass": observed > own_p95,
            "familywise_strict_pass": observed > family_p95,
            "ties_fail": True,
        }
    return {
        "replicates": replicates,
        "shared_global_permutation": True,
        "conditional_domain_separation": True,
        "estimand": "alpha0_unshrunk_cell_mean",
        "gene_results": gene_results,
        "max_null_sha256": canonical_sha256(max_null),
    }


def alpha0_bootstrap_stability(
    *,
    global_rows: Sequence[Mapping[str, Any]],
    conditional_cells: Mapping[str, Sequence[Mapping[str, Any]]],
    observed_best: str,
    observed_worst: str,
    master_nonce: str,
    gene: str,
    replicates: int = 2000,
    candidate_order: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Diagnostic-only bootstrap using unshrunk cell means."""

    if replicates != 2000 or observed_best == observed_worst:
        raise StatisticsError("alpha=0 bootstrap binding is invalid")
    if observed_best not in conditional_cells or observed_worst not in conditional_cells:
        raise StatisticsError("alpha=0 best/worst is outside the trusted cells")
    order = list(conditional_cells) if candidate_order is None else list(candidate_order)
    if set(order) != set(conditional_cells) or len(order) != len(conditional_cells):
        raise StatisticsError("alpha=0 bootstrap order differs from trusted cells")
    if not global_rows:
        raise StatisticsError("alpha=0 bootstrap global corpus is empty")
    _score_rows_against_global(global_rows, global_rows)
    order_index = {candidate_id: index for index, candidate_id in enumerate(order)}
    differences = []
    recurrence = 0
    for replicate in range(replicates):
        global_rng = np.random.Generator(
            np.random.PCG64(
                derive_uint128(
                    master_nonce, "bootstrap-global", gene, replicate
                )
            )
        )
        sampled_global = [
            global_rows[index]
            for index in global_rng.integers(
                0, len(global_rows), len(global_rows)
            )
        ]
        sampled_conditional = {}
        for candidate_id, rows in conditional_cells.items():
            if not rows:
                raise StatisticsError("alpha=0 trusted bootstrap cell is empty")
            rng = np.random.Generator(
                np.random.PCG64(
                    derive_uint128(
                        master_nonce,
                        "bootstrap-cell",
                        gene,
                        candidate_id,
                        replicate,
                    )
                )
            )
            sampled_conditional[candidate_id] = [
                rows[index] for index in rng.integers(0, len(rows), len(rows))
            ]
        rebuilt_cells, _ = _rebuild_gene_cells(
            global_rows=sampled_global,
            conditional_cells=sampled_conditional,
            trusted=order,
            gene=gene,
        )
        marginal = _alpha0_gene_marginals(rebuilt_cells)
        best = max(marginal, key=lambda key: (marginal[key], -order_index[key]))
        worst = min(marginal, key=lambda key: (marginal[key], order_index[key]))
        recurrence += int(best == observed_best and worst == observed_worst)
        differences.append(marginal[observed_best] - marginal[observed_worst])
    lower = type7_quantile(differences, 0.025)
    upper = type7_quantile(differences, 0.975)
    half_width = (upper - lower) / 2.0
    recurrence_rate = recurrence / replicates
    return {
        "replicates": replicates,
        "fixed_pair": [observed_best, observed_worst],
        "ci95_type7": [lower, upper],
        "ci_half_width": half_width,
        "ci_half_width_pass": half_width <= 0.025,
        "best_worst_recurrence": recurrence_rate,
        "recurrence_pass": recurrence_rate >= 0.90,
        "borderline_recurrence": 0.80 <= recurrence_rate < 0.90,
        "differences_sha256": canonical_sha256(differences),
        "estimand": "alpha0_unshrunk_cell_mean",
    }


def _arm_context_weight(
    *,
    row: Mapping[str, Any],
    arm: str,
    gene: str,
    arm_distributions: Mapping[str, Mapping[str, Mapping[str, float]]],
) -> float | None:
    assignments = row.get("candidate_ids")
    if type(assignments) is not dict:
        raise StatisticsError("arm-sensitivity occurrence assignment is absent")
    weight = 1.0
    for other_gene, baseline in arm_distributions["G"].items():
        if other_gene == gene:
            continue
        if other_gene not in assignments:
            raise StatisticsError("arm-sensitivity other-gene assignment is absent")
        candidate_id = assignments[other_gene]
        denominator = baseline.get(candidate_id)
        if denominator is None or denominator <= 0.0:
            return None
        numerator = arm_distributions[arm][other_gene].get(candidate_id, 0.0)
        weight *= numerator / denominator
    return weight


def arm_sensitivity_theta(
    *,
    gene: str,
    trusted: Sequence[str],
    cells: Mapping[str, Mapping[str, Any]],
    arm_distributions: Mapping[str, Mapping[str, Mapping[str, float]]],
    ess_min_fraction: float | None = ARM_SENSITIVITY_ESS_MIN_FRACTION,
) -> dict[str, Any]:
    """Report other-gene arm tilts over observed survivor contexts only."""

    if type(arm_distributions) is not dict or set(arm_distributions) != {"G", "F", "S"}:
        raise StatisticsError("arm distributions must contain exactly G/F/S")
    if any(type(arm_distributions[arm]) is not dict for arm in ("G", "F", "S")):
        raise StatisticsError("arm distributions are malformed")
    other_genes = set(arm_distributions["G"])
    if any(set(arm_distributions[arm]) != other_genes for arm in ("F", "S")):
        raise StatisticsError("arm distributions differ in other-gene support")
    for arm in ("G", "F", "S"):
        for other_gene, distribution in arm_distributions[arm].items():
            if other_gene == gene or type(distribution) is not dict or not distribution:
                raise StatisticsError("arm distributions must cover only non-self genes")
            if any(
                type(probability) not in (int, float)
                or not math.isfinite(float(probability))
                or probability < 0.0
                for probability in distribution.values()
            ):
                raise StatisticsError("arm probabilities must be finite and nonnegative")
    if ess_min_fraction is not None and (
        type(ess_min_fraction) not in (int, float)
        or not math.isfinite(float(ess_min_fraction))
        or not 0.0 <= ess_min_fraction <= 1.0
    ):
        raise StatisticsError("ESS minimum fraction is invalid")
    trusted_order = list(trusted)
    if not trusted_order or len(set(trusted_order)) != len(trusted_order):
        raise StatisticsError("arm sensitivity trusted order is invalid")
    if any(candidate_id not in cells for candidate_id in trusted_order):
        raise StatisticsError("arm sensitivity trusted cell is absent")

    result: dict[str, Any] = {}
    for candidate_id in trusted_order:
        rows = cells[candidate_id].get("Dscore")
        if type(rows) is not list:
            raise StatisticsError("arm sensitivity Dscore cell is malformed")
        cell_result = {
            "theta": {},
            "ess": {},
            "ess_fraction": {},
            "not_estimable": {},
        }
        for arm in ("G", "F", "S"):
            weights: list[float] = []
            benefits: list[float] = []
            invalid_ratio = False
            for row in rows:
                benefit = row.get("benefit")
                if type(benefit) not in (int, float) or not math.isfinite(float(benefit)):
                    raise StatisticsError("arm sensitivity benefit must be finite")
                weight = _arm_context_weight(
                    row=row,
                    arm=arm,
                    gene=gene,
                    arm_distributions=arm_distributions,
                )
                if weight is None:
                    invalid_ratio = True
                    continue
                weights.append(weight)
                benefits.append(float(benefit))
            weight_sum = sum(weights)
            square_sum = sum(weight * weight for weight in weights)
            ess = (
                None
                if invalid_ratio or weight_sum == 0.0 or square_sum == 0.0
                else weight_sum * weight_sum / square_sum
            )
            ess_fraction = None if ess is None or not rows else ess / len(rows)
            not_estimable = (
                invalid_ratio
                or weight_sum == 0.0
                or ess is None
                or ess < 1.0
                or (
                    ess_min_fraction is not None
                    and ess_fraction is not None
                    and ess_fraction < ess_min_fraction
                )
            )
            theta = (
                None
                if not_estimable
                else sum(weight * benefit for weight, benefit in zip(weights, benefits))
                / weight_sum
            )
            cell_result["theta"][arm] = theta
            cell_result["ess"][arm] = ess
            cell_result["ess_fraction"][arm] = ess_fraction
            cell_result["not_estimable"][arm] = not_estimable
        result[candidate_id] = cell_result

    ordering_estimable = all(
        result[candidate_id]["theta"][arm] is not None
        for candidate_id in trusted_order
        for arm in ("G", "F", "S")
    )
    if ordering_estimable:
        order_index = {
            candidate_id: index for index, candidate_id in enumerate(trusted_order)
        }

        def ordering(values: Mapping[str, float]) -> tuple[str, ...]:
            return tuple(
                sorted(
                    trusted_order,
                    key=lambda key: (-values[key], order_index[key]),
                )
            )

        def endpoints(values: Mapping[str, float]) -> tuple[str, str]:
            return (
                max(trusted_order, key=lambda key: (values[key], -order_index[key])),
                min(trusted_order, key=lambda key: (values[key], order_index[key])),
            )

        reference_values = {
            key: float(result[key]["theta"]["G"]) for key in trusted_order
        }
        reference_order = ordering(reference_values)
        reference_endpoints = endpoints(reference_values)
        for arm in ("F", "S"):
            arm_values = {
                key: float(result[key]["theta"][arm]) for key in trusted_order
            }
            result[f"ordering_change_{arm}"] = ordering(arm_values) != reference_order
            result[f"bestworst_change_{arm}"] = (
                endpoints(arm_values) != reference_endpoints
            )
    else:
        for arm in ("F", "S"):
            result[f"ordering_change_{arm}"] = None
            result[f"bestworst_change_{arm}"] = None
    result["ordering_estimable"] = ordering_estimable
    result["ess_min_fraction"] = ess_min_fraction
    return result


def per_size_latency_margin(
    *, arm_cell_rows: Mapping[str, Sequence[tuple[float | None, Mapping[str, Any]]]]
) -> dict[str, Any]:
    """Report arm-reweighted Formocast log-latency margins by locked size."""

    if type(arm_cell_rows) is not dict or set(arm_cell_rows) != {"G", "F", "S"}:
        raise StatisticsError("latency-margin rows must contain exactly G/F/S")
    parsed: dict[str, list[tuple[float | None, Mapping[str, Any], list[Any]]]] = {
        arm: [] for arm in ("G", "F", "S")
    }
    width: int | None = None
    for arm in ("G", "F", "S"):
        if type(arm_cell_rows[arm]) is not list:
            raise StatisticsError("latency-margin arm rows are malformed")
        for item in arm_cell_rows[arm]:
            if type(item) not in (tuple, list) or len(item) != 2:
                raise StatisticsError("latency-margin weighted row is malformed")
            weight, row = item
            if weight is not None and (
                type(weight) not in (int, float)
                or not math.isfinite(float(weight))
                or weight < 0.0
            ):
                raise StatisticsError("latency-margin weight is invalid")
            if type(row) is not dict or type(row.get("latencies")) is not list or not row["latencies"]:
                raise StatisticsError("latency-margin occurrence is missing latencies")
            latencies = list(row["latencies"])
            if width is None:
                width = len(latencies)
            elif len(latencies) != width:
                raise StatisticsError("latency-margin vectors have inconsistent widths")
            parsed[arm].append((None if weight is None else float(weight), row, latencies))
    width = 0 if width is None else width

    expected_log: dict[str, list[float | None]] = {}
    for arm in ("G", "F", "S"):
        arm_values: list[float | None] = []
        invalid_weight = any(weight is None for weight, _, _ in parsed[arm])
        for size_index in range(width):
            weighted_sum = 0.0
            weight_sum = 0.0
            invalid_latency = invalid_weight
            for weight, _, latencies in parsed[arm]:
                if weight is None or weight == 0.0:
                    continue
                item = latencies[size_index]
                latency = item.get("predicted_latency") if type(item) is dict else item
                if (
                    type(latency) not in (int, float)
                    or not math.isfinite(float(latency))
                    or latency <= 0.0
                ):
                    invalid_latency = True
                    continue
                weighted_sum += weight * math.log(float(latency))
                weight_sum += weight
            arm_values.append(
                None if invalid_latency or weight_sum == 0.0 else weighted_sum / weight_sum
            )
        expected_log[arm] = arm_values

    def contrast(left: str, right: str) -> list[float | None]:
        return [
            None if expected_log[left][index] is None or expected_log[right][index] is None
            else expected_log[left][index] - expected_log[right][index]
            for index in range(width)
        ]

    def ratios(values: Sequence[float | None]) -> list[float | None]:
        result = []
        for value in values:
            try:
                ratio = None if value is None else math.exp(value)
            except OverflowError:
                ratio = None
            result.append(ratio if ratio is None or math.isfinite(ratio) else None)
        return result

    g_minus_f = contrast("G", "F")
    s_minus_f = contrast("S", "F")
    return {
        "E_logL": expected_log,
        "contrast_G_minus_F": g_minus_f,
        "contrast_S_minus_F": s_minus_f,
        "ratio_G_over_F": ratios(g_minus_f),
        "ratio_S_over_F": ratios(s_minus_f),
        "note": "formocast_model_margin_terminal_frame_relative_not_real_speedup",
    }


def occurrence_weighted_spearman(
    pairs: Sequence[tuple[float, float]],
) -> dict[str, Any]:
    """Correlate occurrence-level pairs after applying tied-value midranks."""

    parsed: list[tuple[float, float]] = []
    for pair in pairs:
        if type(pair) not in (tuple, list) or len(pair) != 2:
            raise StatisticsError("Spearman input must contain value pairs")
        left, right = pair
        if (
            type(left) not in (int, float)
            or type(right) not in (int, float)
            or not math.isfinite(float(left))
            or not math.isfinite(float(right))
        ):
            raise StatisticsError("Spearman input values must be finite")
        parsed.append((float(left), float(right)))

    labels = {
        "reported_only": True,
        "gating": False,
        "non_independent_shared_conditional_corpus": True,
    }
    if len(parsed) < 2:
        return {
            "rho": None,
            "not_estimable": True,
            "reason": "degenerate_rank_variance",
            **labels,
        }

    left_ranks = _midranks([pair[0] for pair in parsed])
    right_ranks = _midranks([pair[1] for pair in parsed])
    left_mean = sum(left_ranks) / len(left_ranks)
    right_mean = sum(right_ranks) / len(right_ranks)
    left_centered = [rank - left_mean for rank in left_ranks]
    right_centered = [rank - right_mean for rank in right_ranks]
    left_square_sum = sum(value * value for value in left_centered)
    right_square_sum = sum(value * value for value in right_centered)
    if left_square_sum == 0.0 or right_square_sum == 0.0:
        return {
            "rho": None,
            "not_estimable": True,
            "reason": "degenerate_rank_variance",
            **labels,
        }
    rho = sum(
        left * right for left, right in zip(left_centered, right_centered)
    ) / math.sqrt(left_square_sum * right_square_sum)
    if not math.isfinite(rho):
        raise StatisticsError("Spearman correlation is non-finite")
    return {
        "rho": rho,
        "not_estimable": False,
        "reason": None,
        **labels,
    }


def additive_rank_faithfulness(
    *,
    train_marginals: Mapping[str, Mapping[str, float]],
    train_center: Mapping[str, float],
    eval_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Cross-fit an additive marginal score against held-out rank benefit.

    This is a faithfulness diagnostic for the fitted additive rank score, not an
    interaction or Sobol decomposition.  Centers are fixed on the train half.
    """

    if set(train_marginals) != set(train_center):
        raise StatisticsError("additive-rank train centers differ from marginals")
    for gene, marginal in train_marginals.items():
        if type(marginal) is not dict or not marginal:
            raise StatisticsError("additive-rank train marginal is malformed")
        if any(
            type(value) not in (int, float) or not math.isfinite(float(value))
            for value in marginal.values()
        ):
            raise StatisticsError("additive-rank train marginals must be finite")
        center = train_center[gene]
        if type(center) not in (int, float) or not math.isfinite(float(center)):
            raise StatisticsError("additive-rank train center must be finite")

    pairs: list[tuple[float, float]] = []
    skipped_unmapped = 0
    for row in eval_rows:
        assignments = row.get("candidate_ids")
        benefit = row.get("benefit")
        if type(assignments) is not dict:
            raise StatisticsError("additive-rank eval assignment is absent")
        if type(benefit) not in (int, float) or not math.isfinite(float(benefit)):
            raise StatisticsError("additive-rank eval benefit must be finite")
        score = 0.0
        mapped = True
        for gene, marginal in train_marginals.items():
            candidate_id = assignments.get(gene)
            if candidate_id not in marginal:
                mapped = False
                break
            score += float(marginal[candidate_id]) - float(train_center[gene])
        if not mapped:
            skipped_unmapped += 1
            continue
        pairs.append((score, float(benefit)))

    correlation = occurrence_weighted_spearman(pairs)
    return {
        "rho": correlation["rho"],
        "n_eval": len(pairs),
        "skipped_unmapped": skipped_unmapped,
        "not_estimable": correlation["not_estimable"],
        "reason": correlation["reason"],
        "center_rule": "train_half_occurrence_weighted_mean_marginal",
        "interpretation": (
            "additive-faithfulness localization diagnostic; not an orthogonal "
            "interaction-variance/Sobol decomposition; not proof of epistasis; "
            "low fidelity localizes to the factorization/additive layer"
        ),
        "reported_only": True,
        "gating": False,
        "non_independent_shared_conditional_corpus": True,
        "non_independent_replication_note": (
            "cross-fit halves share the sealed conditional corpus and are not "
            "independent replication"
        ),
    }


def _density_tilt_summary(ratios: Sequence[float | None]) -> dict[str, Any]:
    finite_logs = [math.log(ratio) for ratio in ratios if ratio is not None and ratio > 0.0]
    return {
        "mean": None if not finite_logs else sum(finite_logs) / len(finite_logs),
        "min": None if not finite_logs else min(finite_logs),
        "max": None if not finite_logs else max(finite_logs),
        "finite_count": len(finite_logs),
        "zero_ratio_count": sum(ratio == 0.0 for ratio in ratios),
        "dropped_unmapped": sum(ratio is None for ratio in ratios),
    }


def emitted_prior_reconstruction(
    *,
    arm_laws_train: Mapping[str, Mapping[str, Mapping[str, float]]],
    baseline_train: Mapping[str, Mapping[str, float]],
    eval_rows: Sequence[Mapping[str, Any]],
    master_nonce: str,
    direction_tag: str,
    ess_min_fraction: float = ARM_SENSITIVITY_ESS_MIN_FRACTION,
) -> dict[str, Any]:
    """Reconstruct emitted-prior value with held-out incremental density tilts."""

    arms = ("G", "F", "S")
    if type(arm_laws_train) is not dict or set(arm_laws_train) != set(arms):
        raise StatisticsError("emitted-prior arm laws must contain exactly G/F/S")
    if type(baseline_train) is not dict:
        raise StatisticsError("emitted-prior baseline is malformed")
    genes = set(baseline_train)
    if any(
        type(arm_laws_train[arm]) is not dict
        or set(arm_laws_train[arm]) != genes
        for arm in arms
    ):
        raise StatisticsError("emitted-prior arm-law gene supports differ")
    for gene, baseline in baseline_train.items():
        if type(baseline) is not dict or not baseline:
            raise StatisticsError("emitted-prior baseline gene law is malformed")
        for arm in arms:
            distribution = arm_laws_train[arm][gene]
            if type(distribution) is not dict or any(
                type(probability) not in (int, float)
                or not math.isfinite(float(probability))
                or probability < 0.0
                for probability in distribution.values()
            ):
                raise StatisticsError("emitted-prior arm probabilities are invalid")
        if set(arm_laws_train["G"][gene]) != set(baseline) or any(
            float(arm_laws_train["G"][gene][candidate_id]) != float(probability)
            for candidate_id, probability in baseline.items()
        ):
            raise StatisticsError("emitted-prior G law differs from baseline")
        if any(
            type(probability) not in (int, float)
            or not math.isfinite(float(probability))
            or probability < 0.0
            for probability in baseline.values()
        ):
            raise StatisticsError("emitted-prior baseline probabilities are invalid")
    if (
        type(ess_min_fraction) not in (int, float)
        or not math.isfinite(float(ess_min_fraction))
        or not 0.0 <= ess_min_fraction <= 1.0
    ):
        raise StatisticsError("emitted-prior ESS minimum fraction is invalid")
    if type(master_nonce) is not str or type(direction_tag) is not str or not direction_tag:
        raise StatisticsError("emitted-prior bootstrap binding is invalid")

    labels = {
        "interpretation": (
            "incremental-density-tilt held-out benefit reconstruction; "
            "label-blind Formocast model quantity, not real performance"
        ),
        "reported_only": True,
        "gating": False,
        "non_independent_shared_conditional_corpus": True,
        "non_independent_replication_note": (
            "cross-fit halves share the sealed conditional corpus and are not "
            "independent replication"
        ),
    }
    no_emitted_prior = all(
        set(arm_laws_train["F"][gene]) == set(arm_laws_train["G"][gene])
        and all(
            float(arm_laws_train["F"][gene][candidate_id])
            == float(probability)
            for candidate_id, probability in arm_laws_train["G"][gene].items()
        )
        for gene in genes
    )
    if no_emitted_prior:
        return {
            "not_applicable": True,
            "not_estimable": False,
            "reason": "no_emitted_prior_no_guided_gene",
            **labels,
        }

    rows = list(eval_rows)
    benefits: list[float] = []
    ratios: dict[str, list[float | None]] = {arm: [] for arm in arms}
    invalid_ratio = {arm: False for arm in arms}
    for row in rows:
        assignments = row.get("candidate_ids")
        benefit = row.get("benefit")
        if type(assignments) is not dict:
            raise StatisticsError("emitted-prior eval assignment is absent")
        if type(benefit) not in (int, float) or not math.isfinite(float(benefit)):
            raise StatisticsError("emitted-prior eval benefit must be finite")
        benefits.append(float(benefit))
        for arm in arms:
            ratio: float | None = 1.0
            for gene, baseline in baseline_train.items():
                candidate_id = assignments.get(gene)
                denominator = baseline.get(candidate_id)
                if denominator is None or denominator <= 0.0:
                    ratio = None
                    break
                numerator = arm_laws_train[arm][gene].get(candidate_id, 0.0)
                ratio *= float(numerator) / float(denominator)
                if not math.isfinite(ratio):
                    raise StatisticsError("emitted-prior density ratio is non-finite")
            if ratio is None:
                invalid_ratio[arm] = True
            ratios[arm].append(ratio)

    n_eval = len(rows)
    ess: dict[str, float | None] = {}
    ess_fraction: dict[str, float | None] = {}
    arm_not_estimable: dict[str, bool] = {}
    values: dict[str, float | None] = {}
    for arm in arms:
        weights = [weight for weight in ratios[arm] if weight is not None]
        weight_sum = sum(weights)
        square_sum = sum(weight * weight for weight in weights)
        arm_ess = (
            None
            if invalid_ratio[arm] or weight_sum == 0.0 or square_sum == 0.0
            else weight_sum * weight_sum / square_sum
        )
        arm_ess_fraction = None if arm_ess is None or n_eval == 0 else arm_ess / n_eval
        poor_overlap = (
            invalid_ratio[arm]
            or weight_sum == 0.0
            or arm_ess is None
            or arm_ess < 1.0
            or (
                arm_ess_fraction is not None
                and arm_ess_fraction < ess_min_fraction
            )
        )
        ess[arm] = arm_ess
        ess_fraction[arm] = arm_ess_fraction
        arm_not_estimable[arm] = poor_overlap
        values[arm] = (
            None
            if poor_overlap
            else sum(
                float(weight) * benefit
                for weight, benefit in zip(ratios[arm], benefits)
            )
            / weight_sum
        )

    not_estimable = any(arm_not_estimable.values())
    v_f_minus_g = (
        None if not_estimable else float(values["F"]) - float(values["G"])
    )
    v_f_minus_s = (
        None if not_estimable else float(values["F"]) - float(values["S"])
    )
    ci_f_minus_g = None
    ci_f_minus_s = None
    if n_eval < 2:
        bootstrap_reason = "insufficient_eval_occurrences"
    elif not_estimable:
        bootstrap_reason = "poor_overlap"
    else:
        bootstrap_reason = None
    replicates = 2000
    if not not_estimable and n_eval >= 2:
        bootstrap_f_minus_g: list[float] = []
        bootstrap_f_minus_s: list[float] = []
        for replicate in range(replicates):
            rng = np.random.Generator(
                np.random.PCG64(
                    derive_uint128(
                        master_nonce,
                        "emitted-prior-reconstruction-bootstrap",
                        direction_tag,
                        replicate,
                    )
                )
            )
            sampled_indices = rng.integers(0, n_eval, n_eval)
            sampled_values = {}
            for arm in arms:
                sampled_weights = [
                    float(ratios[arm][int(index)]) for index in sampled_indices
                ]
                sampled_weight_sum = sum(sampled_weights)
                if sampled_weight_sum == 0.0:
                    bootstrap_reason = "zero_weight_bootstrap_resample"
                    break
                sampled_values[arm] = sum(
                    weight * benefits[int(index)]
                    for weight, index in zip(sampled_weights, sampled_indices)
                ) / sampled_weight_sum
            if bootstrap_reason is not None:
                break
            bootstrap_f_minus_g.append(sampled_values["F"] - sampled_values["G"])
            bootstrap_f_minus_s.append(sampled_values["F"] - sampled_values["S"])
        if bootstrap_reason is None:
            ci_f_minus_g = [
                type7_quantile(bootstrap_f_minus_g, 0.025),
                type7_quantile(bootstrap_f_minus_g, 0.975),
            ]
            ci_f_minus_s = [
                type7_quantile(bootstrap_f_minus_s, 0.025),
                type7_quantile(bootstrap_f_minus_s, 0.975),
            ]

    return {
        "V": values,
        "V_F_minus_G": v_f_minus_g,
        "V_F_minus_S": v_f_minus_s,
        "ess": ess,
        "ess_fraction": ess_fraction,
        "ess_min_fraction": ess_min_fraction,
        "ci_V_F_minus_G": ci_f_minus_g,
        "ci_V_F_minus_S": ci_f_minus_s,
        "not_estimable": not_estimable,
        "not_applicable": False,
        "reason": "poor_overlap" if not_estimable else None,
        "n_eval": n_eval,
        "d_F_summary": _density_tilt_summary(ratios["F"]),
        "d_S_summary": _density_tilt_summary(ratios["S"]),
        "replicates": replicates,
        "block": "occurrence",
        "bootstrap_reason": bootstrap_reason,
        **labels,
    }


def sensitivity(marginals: Mapping[str, float]) -> float:
    if len(marginals) < 2 or any(not math.isfinite(value) for value in marginals.values()):
        raise StatisticsError("sensitivity requires two finite trusted marginals")
    return max(marginals.values()) - min(marginals.values())


def joint_permutation_test(
    *,
    global_rows: Sequence[Mapping[str, Any]],
    conditional_cells: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]],
    trusted_values: Mapping[str, Sequence[str]],
    observed_marginals: Mapping[str, Mapping[str, float]],
    master_nonce: str,
    replicates: int = 2000,
    alpha: int = 32,
) -> dict[str, Any]:
    """Own and familywise max nulls with a shared global occurrence permutation.

    Every replicate permutes the global benefit vector once and applies that
    same occurrence mapping to every gene.  Each gene's conditional corpus is
    permuted independently with a domain-separated PCG64 stream while keeping
    every cell count fixed.
    """

    if replicates != 2000 or alpha != 32:
        raise StatisticsError("S11 requires exactly 2,000 permutations and alpha=32")
    genes = sorted(trusted_values)
    if genes != sorted(observed_marginals) or genes != sorted(conditional_cells):
        raise StatisticsError("permutation gene sets differ")
    if not global_rows:
        raise StatisticsError("global permutation corpus is incomplete")
    for row in global_rows:
        if type(row.get("candidate_ids")) is not dict:
            raise StatisticsError("global occurrence gene assignment is absent")
    # This also validates every all-size latency block before any RNG is consumed.
    _score_rows_against_global(global_rows, global_rows)

    own_null: dict[str, list[float]] = {gene: [] for gene in genes}
    max_null: list[float] = []
    for replicate in range(replicates):
        global_rng = np.random.Generator(
            np.random.PCG64(derive_uint128(master_nonce, "permutation-global", replicate))
        )
        assignment_order = global_rng.permutation(len(global_rows))
        global_permuted = []
        for row, assignment_index in zip(global_rows, assignment_order):
            rebuilt = dict(row)
            rebuilt["candidate_ids"] = dict(global_rows[int(assignment_index)]["candidate_ids"])
            global_permuted.append(rebuilt)
        replicate_sensitivities: list[float] = []
        for gene in genes:
            trusted = list(trusted_values[gene])
            if len(trusted) < 2 or set(conditional_cells[gene]) != set(trusted):
                raise StatisticsError("permutation conditional cells differ from trusted values")
            if any(not conditional_cells[gene][candidate_id] for candidate_id in trusted):
                raise StatisticsError("trusted permutation conditional cell is empty")
            pooled: list[Mapping[str, Any]] = [
                row
                for candidate_id in trusted
                for row in conditional_cells[gene][candidate_id]
            ]
            conditional_rng = np.random.Generator(
                np.random.PCG64(derive_uint128(master_nonce, "permutation-conditional", gene, replicate))
            )
            permuted_conditional = [pooled[index] for index in conditional_rng.permutation(len(pooled))]
            offsets: dict[str, list[Mapping[str, Any]]] = {}
            cursor = 0
            for candidate_id in trusted:
                count = len(conditional_cells[gene][candidate_id])
                offsets[candidate_id] = permuted_conditional[cursor : cursor + count]
                cursor += count
            rebuilt_cells, global_mean_value = _rebuild_gene_cells(
                global_rows=global_permuted,
                conditional_cells=offsets,
                trusted=trusted,
                gene=gene,
            )
            marginal = gene_marginals(
                {
                    candidate_id: [float(row["benefit"]) for row in rows]
                    for candidate_id, rows in rebuilt_cells.items()
                },
                global_mean=global_mean_value,
                alpha=alpha,
            )
            statistic = sensitivity(marginal)
            own_null[gene].append(statistic)
            replicate_sensitivities.append(statistic)
        max_null.append(max(replicate_sensitivities))

    family_p95 = type7_quantile(max_null, 0.95)
    gene_results = {}
    for gene in genes:
        observed = sensitivity(observed_marginals[gene])
        own_p95 = type7_quantile(own_null[gene], 0.95)
        gene_results[gene] = {
            "observed_S": observed,
            "own_null_p95_type7": own_p95,
            "familywise_max_null_p95_type7": family_p95,
            "own_strict_pass": observed > own_p95,
            "familywise_strict_pass": observed > family_p95,
            "ties_fail": True,
        }
    return {
        "replicates": replicates,
        "shared_global_permutation": True,
        "conditional_domain_separation": True,
        "rebuilds_ecdf_benefit_global_mean_mu_and_S": True,
        "gene_results": gene_results,
        "max_null_sha256": canonical_sha256(max_null),
    }


def bootstrap_stability(
    *,
    global_rows: Sequence[Mapping[str, Any]],
    conditional_cells: Mapping[str, Sequence[Mapping[str, Any]]],
    observed_best: str,
    observed_worst: str,
    master_nonce: str,
    gene: str,
    replicates: int = 2000,
    candidate_order: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Bootstrap occurrence/all-size blocks and fixed observed best/worst pair."""

    if replicates != 2000 or observed_best == observed_worst:
        raise StatisticsError("bootstrap binding is invalid")
    if observed_best not in conditional_cells or observed_worst not in conditional_cells:
        raise StatisticsError("fixed best/worst is outside the trusted cells")
    order = list(conditional_cells) if candidate_order is None else list(candidate_order)
    if set(order) != set(conditional_cells) or len(order) != len(conditional_cells):
        raise StatisticsError("bootstrap candidate order does not match trusted cells")
    if not global_rows:
        raise StatisticsError("bootstrap global occurrence corpus is empty")
    _score_rows_against_global(global_rows, global_rows)
    order_index = {candidate_id: index for index, candidate_id in enumerate(order)}
    differences: list[float] = []
    recurrence = 0
    for replicate in range(replicates):
        global_rng = np.random.Generator(
            np.random.PCG64(derive_uint128(master_nonce, "bootstrap-global", gene, replicate))
        )
        sampled_global = [
            global_rows[index] for index in global_rng.integers(0, len(global_rows), len(global_rows))
        ]
        sampled_conditional: dict[str, list[Mapping[str, Any]]] = {}
        for candidate_id, rows in conditional_cells.items():
            if not rows:
                raise StatisticsError("trusted bootstrap conditional cell is empty")
            rng = np.random.Generator(
                np.random.PCG64(
                    derive_uint128(master_nonce, "bootstrap-cell", gene, candidate_id, replicate)
                )
            )
            sampled_conditional[candidate_id] = [
                rows[index] for index in rng.integers(0, len(rows), len(rows))
            ]
        rebuilt_cells, global_mean_value = _rebuild_gene_cells(
            global_rows=sampled_global,
            conditional_cells=sampled_conditional,
            trusted=order,
            gene=gene,
        )
        marginal = gene_marginals(
            {
                candidate_id: [float(row["benefit"]) for row in rows]
                for candidate_id, rows in rebuilt_cells.items()
            },
            global_mean=global_mean_value,
        )
        best = max(marginal, key=lambda key: (marginal[key], -order_index[key]))
        worst = min(marginal, key=lambda key: (marginal[key], order_index[key]))
        recurrence += int(best == observed_best and worst == observed_worst)
        differences.append(marginal[observed_best] - marginal[observed_worst])
    lower = type7_quantile(differences, 0.025)
    upper = type7_quantile(differences, 0.975)
    half_width = (upper - lower) / 2.0
    recurrence_rate = recurrence / replicates
    return {
        "replicates": replicates,
        "fixed_pair": [observed_best, observed_worst],
        "ci95_type7": [lower, upper],
        "ci_half_width": half_width,
        "ci_half_width_pass": half_width <= 0.025,
        "best_worst_recurrence": recurrence_rate,
        "recurrence_pass": recurrence_rate >= 0.90,
        "borderline_recurrence": 0.80 <= recurrence_rate < 0.90,
        "differences_sha256": canonical_sha256(differences),
        "rebuilds_ecdf_benefit_global_mean_mu_and_S": True,
    }


def size_direction(
    cell_rows: Mapping[str, Sequence[Mapping[str, Any]]], *, best: str, worst: str
) -> dict[str, Any]:
    if best not in cell_rows or worst not in cell_rows:
        raise StatisticsError("size-direction pair is outside cells")
    width = len(cell_rows[best][0]["size_benefits"])
    if width not in (2, 3):
        raise StatisticsError("S11 size-direction contract supports exactly 2 or 3 regimes")
    directions = []
    for size_index in range(width):
        best_mean = sum(row["size_benefits"][size_index] for row in cell_rows[best]) / len(cell_rows[best])
        worst_mean = sum(row["size_benefits"][size_index] for row in cell_rows[worst]) / len(cell_rows[worst])
        directions.append(best_mean > worst_mean)
    required = 2
    return {
        "per_size_positive": directions,
        "positive_count": sum(directions),
        "required_count": required,
        "pass": sum(directions) >= required,
    }


HALF_TUPLE_FIELDS = (
    "trust_states",
    "trust_reasons",
    "trusted_sets",
    "per_value_Dexec",
    "per_value_Dscore",
    "per_value_n",
    "per_value_Cscore",
    "per_value_mu",
    "guided_states",
    "guided_reasons",
    "best_worst",
    "per_size_directions",
    "own_null_pass",
    "familywise_null_pass",
    "same_positive_global_lambda",
    "per_gene_guidance_probabilities",
    "shuffle_mapping",
    "canonical_guidance_hash",
    "per_size_and_aggregate_direction",
    "each_model_test_result",
)

HALF_CATEGORICAL_PROJECTION_FIELDS = (
    "trust_states",
    "trust_reasons",
    "trusted_sets",
    "guided_states",
    "guided_reasons",
    "best_worst",
    "per_size_directions",
    "own_null_pass",
    "familywise_null_pass",
    "same_positive_global_lambda",
    "shuffle_mapping",
    "per_size_and_aggregate_direction",
    "each_model_test_result",
)

HALF_NUMERIC_DRIFT_FIELDS = (
    "per_value_Dexec",
    "per_value_Dscore",
    "per_value_n",
    "per_value_Cscore",
    "per_value_mu",
    "per_gene_guidance_probabilities",
    "canonical_guidance_hash",
)

if (
    set(HALF_CATEGORICAL_PROJECTION_FIELDS) & set(HALF_NUMERIC_DRIFT_FIELDS)
    or set(HALF_CATEGORICAL_PROJECTION_FIELDS) | set(HALF_NUMERIC_DRIFT_FIELDS)
    != set(HALF_TUPLE_FIELDS)
):
    raise StatisticsError("semantic half tuple projection partition is invalid")


def semantic_half_stability(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    """Gate on the pre-declared categorical decision projection between disjoint halves.

    Half-specific numeric cells and float guidance probabilities are reported drift, not gated.
    """

    missing = [field for field in HALF_TUPLE_FIELDS if field not in left or field not in right]
    if missing:
        raise StatisticsError("semantic half tuple is incomplete: " + ", ".join(missing))
    left_projection = {
        field: left[field] for field in HALF_CATEGORICAL_PROJECTION_FIELDS
    }
    right_projection = {
        field: right[field] for field in HALF_CATEGORICAL_PROJECTION_FIELDS
    }
    return {
        "stable": left_projection == right_projection,
        "categorical_projection_fields": list(HALF_CATEGORICAL_PROJECTION_FIELDS),
        "left_categorical_sha256": canonical_sha256(left_projection),
        "right_categorical_sha256": canonical_sha256(right_projection),
        "numeric_drift": {
            "gating": False,
            "reported": True,
            "fields": [
                field
                for field in HALF_NUMERIC_DRIFT_FIELDS
                if left[field] != right[field]
            ],
        },
        "tv_gate": "absent",
        "continuation": "NO_EXTENSION_PERMITTED",
    }


# Prospectively fixed, synthetic, reported-only decision-loss simulation.  The
# selector itself remains solely in workflow.build_analysis_and_guidance.
DECISION_LOSS_MARGIN = 0.02
DECISION_LOSS_ENTROPY_MIN = 0.80
DECISION_LOSS_ALPHA = 32
DECISION_LOSS_SENSITIVITY_MIN = 0.05
DECISION_LOSS_PANEL_SEED = 0xD5C1
DECISION_LOSS_REPLICATES_PER_SURFACE = 8
DECISION_LOSS_GATE_REPLICATES = 2000
DECISION_LOSS_SUPPORT_MIN = 128
_DECISION_LOSS_LOCK_SHA256 = canonical_sha256(
    {"synthetic_only": "s11-decision-loss-simulation"}
)


def decision_loss_panel() -> list[dict[str, Any]]:
    """Return the prospectively fixed non-degenerate synthetic surface panel."""

    return [
        {
            "surface_id": "shrinkage_helps_lowsupport",
            "candidate_order": ["low", "high"],
            "n_gv": {"low": 2, "high": 40},
            "global_candidate": "high",
            "global_latencies": [1.0, 4.0, 1.0, 4.0],
            "true_mean_hint": {"low": 0.5, "high": 0.5375},
            "profiles": {
                "low": [
                    {"count": 1, "latency": 1.01, "noise_weight": 1.0},
                    {"count": 1, "latency": 1.01, "noise_weight": 0.0},
                ],
                "high": [
                    {"count": 3, "latency": 0.5, "noise_weight": 0.0},
                    {"count": 33, "latency": 2.5, "noise_weight": 0.0},
                ],
            },
            "interaction": None,
            "noise_sd": 0.1,
            "seed": DECISION_LOSS_PANEL_SEED ^ 0xA01,
            "regime": "near_S_g_0.05_small_unequal_support_additive_noise",
        },
        {
            "surface_id": "shrinkage_masks_realgap",
            "candidate_order": ["low", "high"],
            "n_gv": {"low": 48, "high": 24},
            "global_candidate": "low",
            "global_latencies": [1.0, 4.0, 1.0, 4.0],
            "true_mean_hint": {"low": 26.5 / 48.0, "high": 1.0},
            "profiles": {
                "low": [
                    {"count": 5, "latency": 0.5, "noise_weight": 0.0},
                    {"count": 39, "latency": 2.5, "noise_weight": 0.0},
                ],
                "high": [
                    {"count": 21, "latency": 0.99, "noise_weight": 1.0},
                    {"count": 3, "latency": 0.99, "noise_weight": 0.0},
                ],
            },
            "interaction": None,
            "noise_sd": 0.1,
            # Six of the eight pre-registered common shocks are positive
            # enough to move 21 noisy observations across the
            # terminal-global ECDF boundary.
            "seed": DECISION_LOSS_PANEL_SEED ^ 0xD5C5,
            "regime": "real_gap_adequate_unequal_support_flip",
        },
        {
            "surface_id": "boundary_unequal_interaction",
            "candidate_order": ["low", "high"],
            "n_gv": {"low": 5, "high": 30},
            "global_candidate": "high",
            "global_latencies": [1.0, 4.0, 1.0, 4.0],
            "true_mean_hint": {"low": 0.8, "high": 0.5},
            "profiles": {
                "low": [
                    {
                        "count": 4,
                        "latency": 0.5,
                        "noise_weight": 0.0,
                        "second_gene": 0,
                    },
                    {
                        "count": 1,
                        "latency": 0.5,
                        "noise_weight": 1.0,
                        "second_gene": 1,
                    },
                ],
                "high": [
                    {
                        "count": 26,
                        "latency": 2.5,
                        "noise_weight": 0.0,
                        "second_gene": 1,
                    },
                ],
            },
            "interaction": {
                "second_gene": "H",
                "affected_candidate": "low",
                "latency_shift_if_second_gene_1": 4.0,
                "winner_at_second_gene_0": "low",
                "winner_at_second_gene_1": "high",
            },
            "noise_sd": 0.08,
            "seed": DECISION_LOSS_PANEL_SEED ^ 0xC03,
            "regime": "boundary_real_second_gene_conditioned_interaction",
        },
        {
            "surface_id": "tiny_n_1to8_additive",
            "candidate_order": ["low", "high"],
            "n_gv": {"low": 1, "high": 8},
            "global_candidate": "high",
            "global_latencies": [1.0, 4.0, 1.0, 4.0],
            "true_mean_hint": {"low": 1.0, "high": 0.25},
            "profiles": {
                "low": [
                    {"count": 1, "latency": 0.5, "noise_weight": 1.0},
                ],
                "high": [
                    {"count": 4, "latency": 4.5, "noise_weight": 0.0},
                ],
            },
            "interaction": None,
            "noise_sd": 0.08,
            "seed": DECISION_LOSS_PANEL_SEED ^ 0xD04,
            "regime": "tiny_n_1_to_8_additive",
        },
        {
            "surface_id": "largen_negligible_shrink",
            "candidate_order": ["low", "high"],
            "n_gv": {"low": 200, "high": 220},
            "global_candidate": "high",
            "global_latencies": [2.0, 2.0, 2.0, 2.0],
            "true_mean_hint": {"low": 1.0, "high": 2.0 / 220.0},
            "profiles": {
                "low": [
                    {"count": 200, "latency": 0.5, "noise_weight": 0.0},
                ],
                "high": [
                    {"count": 216, "latency": 2.5, "noise_weight": 0.0},
                ],
            },
            "interaction": None,
            "noise_sd": 0.0,
            "seed": DECISION_LOSS_PANEL_SEED ^ 0xE05,
            "regime": "large_n_clear_gap_negligible_shrink_control",
        },
    ]


def _validated_decision_loss_panel(
    panel: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    expected_fields = {
        "surface_id",
        "candidate_order",
        "n_gv",
        "global_candidate",
        "global_latencies",
        "true_mean_hint",
        "profiles",
        "interaction",
        "noise_sd",
        "seed",
        "regime",
    }
    if type(panel) not in (list, tuple) or not panel:
        raise StatisticsError("decision-loss panel must be a nonempty ordered sequence")
    normalized: list[dict[str, Any]] = []
    surface_ids: set[str] = set()
    for source in panel:
        if type(source) is not dict or set(source) != expected_fields:
            raise StatisticsError("decision-loss surface fields differ from the fixed schema")
        surface = dict(source)
        surface_id = surface["surface_id"]
        order = surface["candidate_order"]
        n_gv = surface["n_gv"]
        profiles = surface["profiles"]
        if (
            type(surface_id) is not str
            or not surface_id
            or surface_id in surface_ids
            or type(order) is not list
            or order != ["low", "high"]
            or type(n_gv) is not dict
            or set(n_gv) != set(order)
            or len(set(n_gv.values())) != len(n_gv)
            or any(type(value) is not int or value < 1 for value in n_gv.values())
            or surface["global_candidate"] not in order
            or type(surface["global_latencies"]) is not list
            or len(surface["global_latencies"]) != 4
            or any(
                type(value) is not float
                or not math.isfinite(value)
                or value <= 0.0
                for value in surface["global_latencies"]
            )
            or type(profiles) is not dict
            or set(profiles) != set(order)
        ):
            raise StatisticsError("decision-loss support/candidate specification is malformed")
        global_counts = {
            candidate: 4 if candidate == surface["global_candidate"] else 0
            for candidate in order
        }
        for candidate in order:
            profile = profiles[candidate]
            if type(profile) is not list or not profile:
                raise StatisticsError("decision-loss latency profile is empty")
            expected_conditional = n_gv[candidate] - global_counts[candidate]
            if expected_conditional < 1 or sum(item.get("count", -1) for item in profile) != expected_conditional:
                raise StatisticsError("decision-loss profile does not produce the declared n_gv")
            for item in profile:
                if (
                    type(item) is not dict
                    or not {"count", "latency", "noise_weight"} <= set(item)
                    or type(item["count"]) is not int
                    or item["count"] < 1
                    or type(item["latency"]) is not float
                    or item["latency"] <= 0.0
                    or not math.isfinite(item["latency"])
                    or type(item["noise_weight"]) is not float
                    or not math.isfinite(item["noise_weight"])
                    or set(item) - {"count", "latency", "noise_weight", "second_gene"}
                ):
                    raise StatisticsError("decision-loss latency profile item is malformed")
        if (
            type(surface["true_mean_hint"]) is not dict
            or set(surface["true_mean_hint"]) != set(order)
            or any(
                type(value) not in (int, float)
                or not math.isfinite(float(value))
                or not 0.0 <= float(value) <= 1.0
                for value in surface["true_mean_hint"].values()
            )
            or type(surface["noise_sd"]) is not float
            or surface["noise_sd"] < 0.0
            or not math.isfinite(surface["noise_sd"])
            or type(surface["seed"]) is not int
            or type(surface["regime"]) is not str
        ):
            raise StatisticsError("decision-loss surface provenance is malformed")
        interaction = surface["interaction"]
        if interaction is not None and (
            type(interaction) is not dict
            or set(interaction)
            != {
                "second_gene",
                "affected_candidate",
                "latency_shift_if_second_gene_1",
                "winner_at_second_gene_0",
                "winner_at_second_gene_1",
            }
            or interaction["second_gene"] != "H"
            or interaction["affected_candidate"] not in order
            or interaction["winner_at_second_gene_0"]
            == interaction["winner_at_second_gene_1"]
        ):
            raise StatisticsError("decision-loss interaction specification is malformed")
        surface_ids.add(surface_id)
        normalized.append(surface)
    return normalized


def _build_surface_artifacts(
    surface: Mapping[str, Any], *, noiseless: bool, draw_index: int = 0
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build sealed synthetic inputs; it deliberately contains no selection logic."""

    # Lazy import prevents statistics -> workflow import cycles.
    from .workflow import seal_stage_artifact

    order = list(surface["candidate_order"])
    interaction = surface["interaction"]
    genes = ["G"] + (["H"] if interaction is not None else [])
    candidate_ids = {
        gene: [
            canonical_sha256({"synthetic_surface_gene": gene, "candidate": candidate})
            for candidate in order
        ]
        for gene in genes
    }
    registry_payload = {
        "eligible_genes": [
            {
                "gene": gene,
                "candidates": [
                    {"type": "int", "value": str(index)} for index in range(2)
                ],
                "candidate_ids": candidate_ids[gene],
                "baseline_probabilities": [0.5, 0.5],
            }
            for gene in genes
        ]
    }
    registry = seal_stage_artifact(
        "s11_registry",
        lock_sha256=_DECISION_LOSS_LOCK_SHA256,
        dependencies={},
        payload=registry_payload,
    )
    rng = np.random.Generator(
        np.random.PCG64(
            derive_uint128(
                f'{int(surface["seed"]):064x}',
                "decision-loss-jitter",
                draw_index,
            )
        )
    )
    common_shock = 0.0 if noiseless else float(rng.normal())
    rows: list[dict[str, Any]] = []

    def add_occurrence(
        *,
        frame: str,
        index: int,
        g_candidate: str,
        latency: float | None,
        h_candidate: int = 0,
        shared_identity: str | None = None,
    ) -> dict[str, Any]:
        raw = {
            "G": order.index(g_candidate),
            "synthetic_surface": surface["surface_id"],
            "synthetic_slot": f"{frame}:{index}",
        }
        assignments = {"G": candidate_ids["G"][order.index(g_candidate)]}
        if interaction is not None:
            raw["H"] = h_candidate
            assignments["H"] = candidate_ids["H"][h_candidate]
        occurrence_id = canonical_sha256(
            {"frame": frame, "index": index, "raw_configuration": raw}
        )
        row = {
            "occurrence_id": occurrence_id,
            "frame": frame,
            "candidate_ids": assignments,
            "raw_configuration": raw,
            "canonical_credit": True,
            "synthetic_latency": latency,
            "shared_identity": shared_identity,
        }
        rows.append(row)
        return row

    global_candidate = surface["global_candidate"]
    global_rows = []
    for index, latency in enumerate(surface["global_latencies"]):
        global_rows.append(
            add_occurrence(
                frame="global",
                index=index,
                g_candidate=global_candidate,
                latency=latency,
                h_candidate=index % 2,
            )
        )

    conditional_streams = []
    for candidate in order:
        candidate_index = order.index(candidate)
        frame = f"conditional/G/{candidate_ids['G'][candidate_index][:16]}"
        executable_latencies: list[tuple[float, int]] = []
        for profile in surface["profiles"][candidate]:
            for _ in range(profile["count"]):
                second_gene = int(profile.get("second_gene", 0))
                latency = float(profile["latency"])
                if (
                    interaction is not None
                    and candidate == interaction["affected_candidate"]
                    and second_gene == 1
                ):
                    latency += float(interaction["latency_shift_if_second_gene_1"])
                latency += (
                    common_shock
                    * float(surface["noise_sd"])
                    * float(profile["noise_weight"])
                )
                executable_latencies.append((max(0.05, latency), second_gene))
        support_count = max(DECISION_LOSS_SUPPORT_MIN, len(executable_latencies))
        stream_rows = []
        for index in range(support_count):
            latency, second_gene = (
                executable_latencies[index]
                if index < len(executable_latencies)
                else (None, index % 2)
            )
            stream_rows.append(
                add_occurrence(
                    frame=frame,
                    index=index,
                    g_candidate=candidate,
                    latency=latency,
                    h_candidate=second_gene,
                )
            )
        conditional_streams.append(
            {
                "stream_id": frame,
                "fixed_gene": "G",
                "fixed_candidate_id": candidate_ids["G"][candidate_index],
                "cap_complete": True,
                "prefix": {
                    "complete": True,
                    "accepted_credited": support_count,
                    "credited_occurrence_ids": [
                        row["occurrence_id"] for row in stream_rows
                    ],
                },
                "credited_rows": [
                    {key: value for key, value in row.items() if not key.startswith("synthetic_") and key != "shared_identity"}
                    for row in stream_rows
                ],
            }
        )

    if interaction is not None:
        shared_h_identity = canonical_sha256(
            {"synthetic_surface": surface["surface_id"], "H": "collision"}
        )
        for h_index, h_id in enumerate(candidate_ids["H"]):
            frame = f"conditional/H/{h_id[:16]}"
            stream_rows = []
            for index in range(DECISION_LOSS_SUPPORT_MIN):
                stream_rows.append(
                    add_occurrence(
                        frame=frame,
                        index=index,
                        g_candidate=order[index % 2],
                        latency=2.5 if index == 0 else None,
                        h_candidate=h_index,
                        shared_identity=shared_h_identity if index == 0 else None,
                    )
                )
            conditional_streams.append(
                {
                    "stream_id": frame,
                    "fixed_gene": "H",
                    "fixed_candidate_id": h_id,
                    "cap_complete": True,
                    "prefix": {
                        "complete": True,
                        "accepted_credited": DECISION_LOSS_SUPPORT_MIN,
                        "credited_occurrence_ids": [
                            row["occurrence_id"] for row in stream_rows
                        ],
                    },
                    "credited_rows": [
                        {key: value for key, value in row.items() if not key.startswith("synthetic_") and key != "shared_identity"}
                        for row in stream_rows
                    ],
                }
            )

    global_prefix = seal_stage_artifact(
        "s11_global_prefix",
        lock_sha256=_DECISION_LOSS_LOCK_SHA256,
        dependencies={"registry": registry["artifact_sha256"]},
        payload={
            "stream": {
                "stream_id": "global",
                "cap_complete": True,
                "prefix": {
                    "complete": True,
                    "accepted_credited": len(global_rows),
                    "credited_occurrence_ids": [
                        row["occurrence_id"] for row in global_rows
                    ],
                },
                "credited_rows": [
                    {key: value for key, value in row.items() if not key.startswith("synthetic_") and key != "shared_identity"}
                    for row in global_rows
                ],
            }
        },
    )
    conditional = seal_stage_artifact(
        "s11_conditional_prefixes",
        lock_sha256=_DECISION_LOSS_LOCK_SHA256,
        dependencies={
            "registry": registry["artifact_sha256"],
            "global_prefix": global_prefix["artifact_sha256"],
        },
        payload={"activation_complete": True, "streams": conditional_streams},
    )

    qualification_records = []
    scores_by_identity: dict[str, dict[str, Any]] = {}
    for row in rows:
        raw_sha = canonical_sha256(row["raw_configuration"])
        latency = row["synthetic_latency"]
        identity = row["shared_identity"] or canonical_sha256(
            {"synthetic_semantic": raw_sha}
        )
        executable = latency is not None
        qualification_records.append(
            {
                "raw_configuration_sha256": raw_sha,
                "occurrence_ids": [row["occurrence_id"]],
                "alias_fanout_sha256": canonical_sha256(
                    {raw_sha: [row["occurrence_id"]]}
                ),
                "attempt_count": 2,
                "projection": {
                    "state": "executable" if executable else "execution_attrition",
                    "semantic_identity": identity if executable else None,
                },
            }
        )
        if executable:
            score = scores_by_identity.setdefault(
                identity,
                {
                    "semantic_identity": identity,
                    "native_result": {
                        "latencies": [float(latency), float(latency), float(latency)]
                    },
                    "occurrence_ids": [],
                },
            )
            if score["native_result"]["latencies"] != [
                float(latency),
                float(latency),
                float(latency),
            ]:
                raise StatisticsError("shared synthetic identity changed latency")
            score["occurrence_ids"].append(row["occurrence_id"])
    qualifications = seal_stage_artifact(
        "s11_qualifications",
        lock_sha256=_DECISION_LOSS_LOCK_SHA256,
        dependencies={
            "global_prefix": global_prefix["artifact_sha256"],
            "conditional_prefixes": conditional["artifact_sha256"],
        },
        payload={
            "qualification_records": qualification_records,
            "exactly_two_complete_attempts_enforced": True,
            "producer_and_fresh_verifier_roots_separate": True,
        },
    )
    scores = seal_stage_artifact(
        "s11_native_scores",
        lock_sha256=_DECISION_LOSS_LOCK_SHA256,
        dependencies={"qualifications": qualifications["artifact_sha256"]},
        payload={
            "score_records": list(scores_by_identity.values()),
            "all_locked_sizes_required": True,
        },
    )
    return registry, global_prefix, conditional, qualifications, scores


def _decision_from_analysis(
    analysis: Mapping[str, Any], guidance: Mapping[str, Any]
) -> dict[str, Any]:
    """Read both categorical arms from real production output without recomputation."""

    result = analysis["gene_results"]["G"]
    alpha0 = analysis["bias_diagnostics"]["genes"]["G"]["alpha0_sensitivity"]
    alpha0_projection = analysis["bias_diagnostics"]["alpha0_projection"]
    alpha32_decision = {
        "best": result["best"],
        "worst": result["worst"],
        "guided": result["guided"],
        "global_lambda": guidance["global_lambda"],
        "sensitivity": result["permutation"]["observed_S"],
        "model_test_results": dict(result["model_test_results"]),
    }
    alpha0_decision = {
        "best": alpha0["alpha0_best"],
        "worst": alpha0["alpha0_worst"],
        "guided": alpha0["alpha0_guided"],
        "global_lambda": alpha0_projection["global_lambda"],
        "sensitivity": alpha0["alpha0_permutation"]["observed_S"],
        "model_test_results": dict(alpha0["alpha0_model_test_results"]),
    }
    for arm in (alpha32_decision, alpha0_decision):
        discrete_lambda = float(arm["global_lambda"])
        if not math.isclose(discrete_lambda * 4.0, round(discrete_lambda * 4.0)):
            raise StatisticsError("real selector emitted a non-discrete global lambda")
    return {
        "alpha32": alpha32_decision,
        "alpha0": alpha0_decision,
        "alpha0_decision_flip": alpha0["alpha0_decision_flip"],
        "gate_replicates": analysis["permutation"]["replicates"],
        "selection_path": "workflow.build_analysis_and_guidance/_frame_analysis",
    }


def _run_surface_real_path(
    surface: Mapping[str, Any], *, noiseless: bool, draw_index: int = 0
) -> dict[str, Any]:
    # All production imports remain lazy: importing statistics cannot form a
    # statistics -> workflow -> statistics cycle.
    from .contract import load_contract
    from .workflow import build_analysis_and_guidance

    contract = load_contract()
    if (
        contract["statistics"]["alpha"] != DECISION_LOSS_ALPHA
        or contract["statistics"]["normalized_entropy_min"]
        != DECISION_LOSS_ENTROPY_MIN
        or contract["statistics"]["permutations"]
        != DECISION_LOSS_GATE_REPLICATES
        or contract["trust"]["support_min_conditional_fraw"]
        != DECISION_LOSS_SUPPORT_MIN
    ):
        raise StatisticsError("decision-loss production-path provenance changed")
    artifacts = _build_surface_artifacts(
        surface, noiseless=noiseless, draw_index=draw_index
    )
    analysis, guidance = build_analysis_and_guidance(
        registry=artifacts[0],
        global_prefix=artifacts[1],
        conditional_prefixes=artifacts[2],
        qualifications=artifacts[3],
        native_scores=artifacts[4],
        contract=contract,
        lock_sha256=_DECISION_LOSS_LOCK_SHA256,
    )
    return _decision_from_analysis(analysis, guidance)


def _ground_truth_decision(surface: Mapping[str, Any]) -> dict[str, Any]:
    """Read estimator-independent truth from the noise-free real alpha=0 path."""

    projection = _run_surface_real_path(surface, noiseless=True)
    return {
        **projection["alpha0"],
        "truth_source": "noise_free_true_means_via_real_alpha0_projection",
        "noise_free_alpha32": projection["alpha32"],
        "noise_free_alpha0_decision_flip": projection["alpha0_decision_flip"],
    }


def _decision_loss(
    estimated: Mapping[str, Any], truth: Mapping[str, Any]
) -> dict[str, Any]:
    fields = ("best", "worst", "guided", "global_lambda")
    differing = [field for field in fields if estimated[field] != truth[field]]
    misidentification = int(bool(differing))
    return {
        "misidentification": misidentification,
        "regret": misidentification * float(truth["sensitivity"]),
        "differing_fields": differing,
    }


def run_decision_loss_simulation(
    panel: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Measure both real production arms against real-path noise-free truth."""

    panel_spec = _validated_decision_loss_panel(
        decision_loss_panel() if panel is None else panel
    )
    per_regime = []
    for surface in panel_spec:
        truth = _ground_truth_decision(surface)
        alpha32_losses = []
        alpha0_losses = []
        projections = []
        for draw_index in range(DECISION_LOSS_REPLICATES_PER_SURFACE):
            projection = _run_surface_real_path(
                surface, noiseless=False, draw_index=draw_index
            )
            if projection["gate_replicates"] != DECISION_LOSS_GATE_REPLICATES:
                raise StatisticsError("real selector did not retain 2,000 replicates")
            projections.append(projection)
            alpha32_losses.append(_decision_loss(projection["alpha32"], truth))
            alpha0_losses.append(_decision_loss(projection["alpha0"], truth))
        denominator = DECISION_LOSS_REPLICATES_PER_SURFACE
        loss_alpha32 = sum(
            loss["misidentification"] for loss in alpha32_losses
        ) / denominator
        loss_alpha0 = sum(
            loss["misidentification"] for loss in alpha0_losses
        ) / denominator
        weighted_alpha32 = sum(loss["regret"] for loss in alpha32_losses) / denominator
        weighted_alpha0 = sum(loss["regret"] for loss in alpha0_losses) / denominator
        per_regime.append(
            {
                "surface_id": surface["surface_id"],
                "regime": surface["regime"],
                "n_gv": dict(surface["n_gv"]),
                "interaction": surface["interaction"],
                "truth": truth,
                "loss_alpha32": loss_alpha32,
                "loss_alpha0": loss_alpha0,
                "paired_delta": loss_alpha32 - loss_alpha0,
                "weighted_loss_alpha32": weighted_alpha32,
                "weighted_loss_alpha0": weighted_alpha0,
                "weighted_paired_delta": weighted_alpha32 - weighted_alpha0,
                "bestworst_flip_detected": any(
                    (
                        projection["alpha32"]["best"],
                        projection["alpha32"]["worst"],
                    )
                    != (
                        projection["alpha0"]["best"],
                        projection["alpha0"]["worst"],
                    )
                    for projection in projections
                ),
                "discrete_lambda": {
                    "alpha32": [
                        projection["alpha32"]["global_lambda"]
                        for projection in projections
                    ],
                    "alpha0": [
                        projection["alpha0"]["global_lambda"]
                        for projection in projections
                    ],
                },
                "alpha0_decision_flip_draws": sum(
                    projection["alpha0_decision_flip"] for projection in projections
                ),
            }
        )

    regime_count = len(per_regime)
    mean_loss_alpha32 = sum(row["loss_alpha32"] for row in per_regime) / regime_count
    mean_loss_alpha0 = sum(row["loss_alpha0"] for row in per_regime) / regime_count
    weighted_loss_alpha32 = sum(
        row["weighted_loss_alpha32"] for row in per_regime
    ) / regime_count
    weighted_loss_alpha0 = sum(
        row["weighted_loss_alpha0"] for row in per_regime
    ) / regime_count
    weighted_delta = weighted_loss_alpha32 - weighted_loss_alpha0
    if weighted_delta <= 0.0:
        recommended_option = "OPTION_B_REPORT_ONLY"
    elif weighted_delta > DECISION_LOSS_MARGIN:
        recommended_option = "OPTION_C_GATE_FLIP"
    else:
        recommended_option = "INCONCLUSIVE"
    aggregate = {
        "mean_loss_alpha32": mean_loss_alpha32,
        "mean_loss_alpha0": mean_loss_alpha0,
        "paired_delta": mean_loss_alpha32 - mean_loss_alpha0,
        "weighted_loss_alpha32": weighted_loss_alpha32,
        "weighted_loss_alpha0": weighted_loss_alpha0,
        "weighted_paired_delta": weighted_delta,
    }
    result = {
        "panel_spec_hash": canonical_sha256(panel_spec),
        "per_regime": per_regime,
        "aggregate": aggregate,
        "DECISION_LOSS_MARGIN": DECISION_LOSS_MARGIN,
        "recommended_option": recommended_option,
        "recommendation_rule": (
            "d=weighted_loss_alpha32-weighted_loss_alpha0; "
            "d<=0 -> OPTION_B_REPORT_ONLY; "
            f"d>{DECISION_LOSS_MARGIN} -> OPTION_C_GATE_FLIP; "
            "otherwise -> INCONCLUSIVE"
        ),
        "gate_replicates": DECISION_LOSS_GATE_REPLICATES,
        "noisy_draws_per_surface": DECISION_LOSS_REPLICATES_PER_SURFACE,
        "selection_path": "workflow.build_analysis_and_guidance/_frame_analysis",
        "ground_truth_path": (
            "noise_free_true_means_through_real_alpha0_production_projection"
        ),
        "reported_only": True,
        "gating": False,
        "wires_alpha0_into_gate": False,
        "synthetic_only": True,
    }
    result["result_sha256"] = canonical_sha256(result)
    return result
