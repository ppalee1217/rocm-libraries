# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Multiplicity-preserving S11 population and value-cell construction."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence

from .canonical import canonical_sha256


class PopulationError(ValueError):
    """Occurrence lineage or population membership is inconsistent."""


def build_populations(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Build Fraw/Fexec/Fscore while retaining every raw alias occurrence."""

    occurrence_ids: set[str] = set()
    fraw: list[Mapping[str, Any]] = []
    fexec: list[Mapping[str, Any]] = []
    fscore: list[Mapping[str, Any]] = []
    zero_credit: list[Mapping[str, Any]] = []
    for row in rows:
        occurrence_id = row.get("occurrence_id")
        frame = row.get("frame")
        if type(occurrence_id) is not str or occurrence_id in occurrence_ids:
            raise PopulationError("occurrence ID is absent or duplicated")
        if frame != "global" and not (type(frame) is str and frame.startswith("conditional/")):
            raise PopulationError("occurrence frame is not global or one conditional cell")
        occurrence_ids.add(occurrence_id)
        if not row.get("raw_valid", False):
            continue
        if row.get("canonical_credit", True) is not True:
            zero_credit.append(row)
            continue
        fraw.append(row)
        executable = row.get("qualification_state") == "executable"
        if executable:
            if type(row.get("semantic_identity")) is not str:
                raise PopulationError("Fexec occurrence lost operational identity")
            fexec.append(row)
        scored = row.get("scores_complete_finite", False)
        if scored:
            if not executable:
                raise PopulationError("Fscore must be a subset of Fexec")
            benefit = row.get("benefit")
            if type(benefit) is not float or not math.isfinite(benefit):
                raise PopulationError("Fscore occurrence lacks finite benefit")
            fscore.append(row)

    def split(values: Iterable[Mapping[str, Any]]) -> tuple[list[Any], dict[str, list[Any]]]:
        global_rows: list[Any] = []
        conditional: dict[str, list[Any]] = defaultdict(list)
        for row in values:
            if row["frame"] == "global":
                global_rows.append(row)
            else:
                conditional[row["frame"]].append(row)
        return global_rows, dict(conditional)

    raw_global, raw_conditional = split(fraw)
    exec_global, exec_conditional = split(fexec)
    score_global, score_conditional = split(fscore)
    uexec_global = sorted({row["semantic_identity"] for row in exec_global})
    result = {
        "Fraw_global": raw_global,
        "Fexec_global": exec_global,
        "Fscore_global": score_global,
        "Fraw_conditional": raw_conditional,
        "Fexec_conditional": exec_conditional,
        "Fscore_conditional": score_conditional,
        "Uexec_global": uexec_global,
        "aliases_by_identity": {
            identity: [row["occurrence_id"] for row in fexec if row["semantic_identity"] == identity]
            for identity in sorted({row["semantic_identity"] for row in fexec})
        },
        "Y_exec_global": None if not raw_global else len(exec_global) / len(raw_global),
        "C_score_occ_global": None if not exec_global else len(score_global) / len(exec_global),
        "zero_credit_diagnostics": zero_credit,
    }
    lineage = {
        key: value
        for key, value in result.items()
        if key not in ("Fraw_global", "Fexec_global", "Fscore_global", "Fraw_conditional", "Fexec_conditional", "Fscore_conditional", "zero_credit_diagnostics")
    }
    return {**result, "population_lineage_sha256": canonical_sha256(lineage)}


def _matches(row: Mapping[str, Any], gene: str, candidate_id: str) -> bool:
    values = row.get("candidate_ids")
    if type(values) is not dict:
        raise PopulationError("occurrence candidate mapping is absent")
    return values.get(gene) == candidate_id


def value_cell(
    populations: Mapping[str, Any], *, gene: str, candidate_id: str
) -> dict[str, Any]:
    """Compute exact G*/D* formulas without leaking conditional rows globally."""

    stream_id = f"conditional/{gene}/{candidate_id[:16]}"
    graw = [row for row in populations["Fraw_global"] if _matches(row, gene, candidate_id)]
    gexec = [row for row in populations["Fexec_global"] if _matches(row, gene, candidate_id)]
    gscore = [row for row in populations["Fscore_global"] if _matches(row, gene, candidate_id)]
    craw = list(populations["Fraw_conditional"].get(stream_id, []))
    cexec = list(populations["Fexec_conditional"].get(stream_id, []))
    cscore = list(populations["Fscore_conditional"].get(stream_id, []))
    for row in (*craw, *cexec, *cscore):
        if not _matches(row, gene, candidate_id):
            raise PopulationError("conditional row does not preserve its fixed raw value")
    draw, dexec, dscore = graw + craw, gexec + cexec, gscore + cscore
    return {
        "gene": gene,
        "candidate_id": candidate_id,
        "Graw": graw,
        "Gexec": gexec,
        "Gscore": gscore,
        "Draw": draw,
        "Dexec": dexec,
        "Dscore": dscore,
        "support_gv": len(craw),
        "Cscore_occ_gv": None if not dexec else len(dscore) / len(dexec),
        "n_gv": len(dscore),
        "sum_b_gv": sum(row["benefit"] for row in dscore),
    }


def global_mean(populations: Mapping[str, Any]) -> float | None:
    """Occurrence-weighted global mean; conditional rows are structurally unreachable."""

    rows = populations["Fscore_global"]
    return None if not rows else sum(row["benefit"] for row in rows) / len(rows)
