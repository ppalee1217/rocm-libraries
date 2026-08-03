# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Actual-YAML residual-family and conditional-stream registry extraction."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import stat
from typing import Any, Mapping, Sequence

import yaml

from .canonical import (
    canonical_sha256,
    sha256_file,
    strict_load_json,
    typed_value,
    typed_value_id,
)


class RegistryError(ValueError):
    """The actual YAML cannot be mapped to the frozen S11 registry law."""


def _stable_repository_path(path: Path | str) -> str:
    parts = Path(path).resolve().parts
    try:
        index = parts.index("study_docs")
    except ValueError as error:
        raise RegistryError("registry authority path is outside the tracked study_docs tree") from error
    return str(Path(*parts[index:]))


@dataclass(frozen=True)
class ResidualGene:
    name: str
    candidates: tuple[Any, ...]
    candidate_ids: tuple[str, ...]
    baseline_probabilities: tuple[float, ...]

    def to_document(self) -> dict[str, Any]:
        return {
            "gene": self.name,
            "candidates": [typed_value(item) for item in self.candidates],
            "candidate_ids": list(self.candidate_ids),
            "baseline_probabilities": list(self.baseline_probabilities),
            "cardinality": len(self.candidates),
        }


def load_actual_yaml(path: Path | str) -> dict[str, Any]:
    target = Path(path)
    info = target.lstat()
    if not stat.S_ISREG(info.st_mode) or target.is_symlink():
        raise RegistryError("actual YAML must be one ordinary regular file")
    class UniqueLoader(yaml.SafeLoader):
        pass

    def unique_mapping(loader: yaml.Loader, node: yaml.Node, deep: bool = False) -> dict[Any, Any]:
        result: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in result:
                raise RegistryError(f"duplicate YAML key: {key!r}")
            result[key] = loader.construct_object(value_node, deep=deep)
        return result

    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
    try:
        document = yaml.load(target.read_text(encoding="utf-8"), Loader=UniqueLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        raise RegistryError("actual YAML is malformed") from error
    if type(document) is not dict:
        raise RegistryError("actual YAML root must be a mapping")
    return document


def _one_key_entries(values: Any, label: str) -> list[tuple[str, Any]]:
    if type(values) is not list:
        raise RegistryError(f"{label} must be a list")
    result = []
    for entry in values:
        if type(entry) is not dict or len(entry) != 1:
            raise RegistryError(f"{label} entry must contain exactly one key")
        key = next(iter(entry))
        if type(key) is not str:
            raise RegistryError(f"{label} key must be a string")
        result.append((key, entry[key]))
    return result


def _problem(document: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    problems = document.get("BenchmarkProblems")
    if type(problems) is not list or len(problems) != 1:
        raise RegistryError("S11 requires exactly one BenchmarkProblems entry")
    row = problems[0]
    if type(row) is not list or len(row) != 2 or any(type(item) is not dict for item in row):
        raise RegistryError("BenchmarkProblems entry has an unexpected shape")
    return row[0], row[1]


def _locked_size_registry(path: Path | str) -> dict[str, Any]:
    document = strict_load_json(path)
    expected = {
        "checkpoint_id",
        "deduplication_rule",
        "distinct_count",
        "distinct_source_order",
        "dtype_layout",
        "kind",
        "raw_row_count",
        "raw_rows",
        "same_space",
        "same_space_parity",
        "schema_version",
        "selected_sizes",
        "selection_indices",
        "selection_key",
        "status",
    }
    if type(document) is not dict or set(document) != expected:
        raise RegistryError("locked size registry schema/unknown-property failure")
    if (
        document["kind"] != "s10_size_registry"
        or document["schema_version"] != "1.0.0"
        or document["checkpoint_id"] != "S10"
        or document["status"] != "prelock_complete"
        or document["raw_row_count"] != 17
        or document["distinct_count"] != 16
        or document["deduplication_rule"] != "first occurrence by exact (M,N,batch,K) tuple"
        or document["selection_key"] != ["K", "M*N*batch", "M", "N", "batch"]
        or document["selection_indices"] != [0, 7, 15]
        or document["selected_sizes"] != [[8, 8, 1, 128], [256, 256, 1, 1024], [2304, 1024, 1, 214336]]
        or document["same_space_parity"] is not True
    ):
        raise RegistryError("locked size registry identity/reducer changed")
    raw = document["raw_rows"]
    distinct: list[list[int]] = []
    for row in raw:
        if type(row) is not list or len(row) != 4 or any(type(value) is not int or value <= 0 for value in row):
            raise RegistryError("locked source size row is malformed")
        if row not in distinct:
            distinct.append(row)
    if distinct != document["distinct_source_order"] or len(distinct) != 16:
        raise RegistryError("first-exact-tuple size deduplication mismatch")
    ordered = sorted(distinct, key=lambda row: (row[3], row[0] * row[1] * row[2], row[0], row[1], row[2]))
    if [ordered[index] for index in [0, 7, 15]] != document["selected_sizes"]:
        raise RegistryError("locked size selection key/index replay mismatch")
    return document


def verify_structural_registry(
    document: Mapping[str, Any] | None = None, *, repository_root: Path | str
) -> dict[str, Any]:
    """Rebuild the committed S11 structural registry from original-S10 sources."""

    root = Path(repository_root).resolve()
    structural_path = root / "study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-structural-registry.json"
    if document is None:
        document = strict_load_json(structural_path)
    expected_keys = {
        "checkpoint_id", "document_kind", "dtype_layout", "extraction", "fixed_runtime",
        "formal_empirical_credit", "problem_sizes", "schema_version", "source_chain", "status",
        "s10r2_crosscheck", "source_exclusions",
    }
    if type(document) is not dict or set(document) != expected_keys:
        raise RegistryError("S11 structural registry schema/unknown-property failure")
    chain = document["source_chain"]
    bindings = {
        "actual_yaml": "faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36",
        "parent_lock": "6e119788305913bcf0e69244c2c190d345cb1d360c6dc1f49323ddffcdd397f6",
        "size_registry": "71f253fc4d3ab7e23b078f14b254bf65d591f762b6f28aae32e24c87bab536be",
        "yaml_provenance": "2d120b41d38787c5888304f3e8fda6a033b22f554162d4a500d4d9150be24917",
    }
    for key, expected_hash in bindings.items():
        binding = chain[key]
        if sha256_file(root / binding["path"]) != expected_hash or binding["sha256"] != expected_hash:
            raise RegistryError(f"original-S10 source-chain mismatch: {key}")
    size_document = _locked_size_registry(root / chain["size_registry"]["path"])
    actual = load_actual_yaml(root / chain["actual_yaml"]["path"])
    parent_lock = strict_load_json(root / chain["parent_lock"]["path"])
    provenance = strict_load_json(root / chain["yaml_provenance"]["path"])
    if (
        parent_lock.get("actual_yaml_sha256") != bindings["actual_yaml"]
        or provenance.get("actual_yaml", {}).get("tracked_copy_raw_sha256") != bindings["actual_yaml"]
        or provenance.get("actual_yaml", {}).get("run_a_raw_sha256") != bindings["actual_yaml"]
        or provenance.get("actual_yaml", {}).get("run_b_raw_sha256") != bindings["actual_yaml"]
    ):
        raise RegistryError("original-S10 lock/provenance actual-YAML lineage mismatch")
    problem_type, parameters = _problem(actual)
    final_entries = _one_key_entries(parameters.get("BenchmarkFinalParameters"), "BenchmarkFinalParameters")
    problem_rows: list[list[int]] = []
    for key, value in final_entries:
        if key == "ProblemSizes":
            problem_rows.extend(row["Exact"] for row in value)
    if any(row not in problem_rows for row in size_document["selected_sizes"]):
        raise RegistryError("locked structural size is absent from the actual YAML")
    _, parameters = _problem(actual)
    fork_entries = _one_key_entries(parameters.get("ForkParameters"), "ForkParameters")
    groups = next(value for key, value in fork_entries if key == "Groups")
    config = actual["Backend"]["Config"]
    if (
        canonical_sha256(groups) != size_document["same_space"]["groups_sha256"]
        or canonical_sha256(config.get("weights", [])) != size_document["same_space"]["weights_sha256"]
        or size_document["same_space"]["raw_yaml_sha256"] != bindings["actual_yaml"]
    ):
        raise RegistryError("actual-YAML same-space groups/weights parity mismatch")
    expected_dtype = {
        "batched": problem_type["Batched"], "compute_data_type": problem_type["ComputeDataType"],
        "data_type": problem_type["DataType"], "dest_data_type": problem_type["DestDataType"],
        "transpose_a": problem_type["TransposeA"], "transpose_b": problem_type["TransposeB"],
    }
    if (
        document["document_kind"] != "s11_structural_registry"
        or document["checkpoint_id"] != "S11" or document["status"] != "frozen_preimplementation"
        or document["formal_empirical_credit"] != 0 or document["dtype_layout"] != expected_dtype
        or document["problem_sizes"] != size_document["selected_sizes"]
        or document["fixed_runtime"] != {
            "actual_reducer": "max", "soo": False, "weight_beta": 0.25,
            "weight_beta_origin": "pinned Ductile config default; actual YAML omits the field",
        }
        or chain["ductile"] != {
            "commit": "5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39",
            "commit_tree": "e03a48ef0e3a45d27a51e2cad3aa836ca807567d",
            "tensilelite_tree": "0bc3b63205f3aa5e62b64d0302726e7f5177527d",
        }
    ):
        raise RegistryError("S11 structural registry replay mismatch")
    return dict(document)


def extract_registry(
    path: Path | str,
    *,
    structural_registry: Mapping[str, Any] | None = None,
    size_registry_path: Path | str | None = None,
) -> dict[str, Any]:
    """Extract all structural eligibility before any model score exists."""

    document = load_actual_yaml(path)
    problem_type, parameters = _problem(document)
    fork_entries = _one_key_entries(parameters.get("ForkParameters"), "ForkParameters")
    if len({key for key, _ in fork_entries}) != len(fork_entries):
        raise RegistryError("ForkParameters contains a duplicate key")

    groups_value = None
    free_entries: list[tuple[str, Sequence[Any]]] = []
    for key, value in fork_entries:
        if key == "Groups":
            if groups_value is not None:
                raise RegistryError("multiple Groups entries are forbidden")
            groups_value = value
        else:
            if type(value) is not list or not value:
                raise RegistryError(f"free parameter {key} has no candidate list")
            free_entries.append((key, value))
    if type(groups_value) is not list:
        raise RegistryError("actual YAML has no Groups list")

    protected_group_override_keys: set[str] = set()
    group_summaries: list[dict[str, Any]] = []
    for group_index, candidates in enumerate(groups_value):
        if type(candidates) is not list or not candidates:
            raise RegistryError("each group must have at least one candidate")
        for candidate in candidates:
            if type(candidate) is not dict:
                raise RegistryError("group candidate must be a mapping")
            protected_group_override_keys.update(candidate)
        group_summaries.append(
            {
                "group": f"group_{group_index}",
                "candidate_count": len(candidates),
                "canonical_sha256": canonical_sha256(candidates),
            }
        )

    backend = document.get("Backend")
    if type(backend) is not dict or backend.get("Name") != "Ductile":
        raise RegistryError("actual YAML backend must be Ductile")
    config = backend.get("Config")
    if type(config) is not dict:
        raise RegistryError("Ductile backend config is absent")
    weights_entries = _one_key_entries(config.get("weights", []), "Backend.Config.weights")
    weighted_keys = {key for key, _ in weights_entries}
    weights_by_axis = dict(weights_entries)
    weight_beta = config.get("weight_beta", 0.25)
    if type(weight_beta) is not float or not math.isfinite(weight_beta) or weight_beta <= 0:
        raise RegistryError("resolved Ductile weight_beta must be a positive finite float")

    def axis_document(name: str, candidates: Sequence[Any], axis_kind: str) -> dict[str, Any]:
        candidate_ids = [
            canonical_sha256({"axis": name, "candidate_index": index, "typed_value": typed_value(value)})
            for index, value in enumerate(candidates)
        ]
        if name in weights_by_axis:
            weights = weights_by_axis[name]
            if (
                type(weights) is not list
                or len(weights) != len(candidates)
                or any(type(value) not in (int, float) or not math.isfinite(value) for value in weights)
            ):
                raise RegistryError(f"sampling weights for {name} do not match candidates")
            minimum = min(float(value) for value in weights)
            unnormalized = [
                math.exp(-weight_beta * (float(value) - minimum)) for value in weights
            ]
            denominator = sum(unnormalized)
            probabilities = [value / denominator for value in unnormalized]
            probability_source = "pinned_Ductile_weight_transform"
        else:
            probabilities = [1.0 / len(candidates) for _ in candidates]
            probability_source = "uniform_unweighted_axis"
        return {
            "axis_name": name,
            "axis_kind": axis_kind,
            "candidates": [typed_value(value) for value in candidates],
            "candidate_ids": candidate_ids,
            "baseline_probabilities": probabilities,
            "probability_source": probability_source,
        }

    sampling_axes: list[dict[str, Any]] = []
    for name, values in fork_entries:
        if name == "Groups":
            sampling_axes.extend(
                axis_document(f"group_{index}", candidates, "protected_group")
                for index, candidates in enumerate(groups_value)
            )
        else:
            sampling_axes.append(axis_document(name, values, "free"))

    eligible: list[ResidualGene] = []
    ineligible: list[dict[str, Any]] = []
    for name, candidates in free_entries:
        reasons: list[str] = []
        if name in weighted_keys:
            reasons.append("currently_weighted")
        if len(candidates) <= 1:
            reasons.append("cardinality_not_greater_than_one")
        candidate_ids = tuple(
            canonical_sha256({"axis": name, "candidate_index": index, "typed_value": typed_value(value)})
            for index, value in enumerate(candidates)
        )
        if reasons:
            ineligible.append({"gene": name, "reasons": reasons})
        else:
            probability = 1.0 / len(candidates)
            eligible.append(
                ResidualGene(
                    name=name,
                    candidates=tuple(candidates),
                    candidate_ids=candidate_ids,
                    baseline_probabilities=tuple(probability for _ in candidates),
                )
            )

    final_entries = _one_key_entries(
        parameters.get("BenchmarkFinalParameters"), "BenchmarkFinalParameters"
    )
    yaml_problem_sizes: list[list[int]] = []
    for key, value in final_entries:
        if key == "ProblemSizes":
            if type(value) is not list:
                raise RegistryError("ProblemSizes must be a list")
            for size in value:
                if type(size) is not dict or set(size) != {"Exact"}:
                    raise RegistryError("only exact problem sizes are supported")
                exact = size["Exact"]
                if type(exact) is not list or len(exact) != 4 or any(type(x) is not int or x <= 0 for x in exact):
                    raise RegistryError("exact problem size must have four positive integers")
                yaml_problem_sizes.append(exact)

    if structural_registry is None:
        structural_path = Path(path).resolve().parent.parent / "manifests" / "s11-structural-registry.json"
        structural_registry = strict_load_json(structural_path)
    problem_sizes = [list(row) for row in structural_registry["problem_sizes"]]
    if size_registry_path is None:
        size_registry_path = Path(path).resolve().parent.parent / "manifests" / "s10-size-registry.json"
    size_registry = _locked_size_registry(size_registry_path)
    if problem_sizes != size_registry["selected_sizes"]:
        raise RegistryError("structural registry/size source parity failure")

    conditional_streams = [
        {
            "stream_id": f"conditional/{gene.name}/{candidate_id[:16]}",
            "gene": gene.name,
            "candidate_index": index,
            "candidate_id": candidate_id,
            "candidate": typed_value(gene.candidates[index]),
        }
        for gene in eligible
        for index, candidate_id in enumerate(gene.candidate_ids)
    ]
    result = {
        "document_kind": "s11_residual_registry",
        "schema_version": 1,
        "checkpoint_id": "S11",
        "actual_yaml_path": _stable_repository_path(path),
        "actual_yaml_sha256": sha256_file(path),
        "problem_type": problem_type,
        "problem_sizes": problem_sizes,
        "actual_yaml_benchmark_final_sizes_diagnostic": yaml_problem_sizes,
        "size_registry_path": _stable_repository_path(size_registry_path),
        "size_registry_file_sha256": sha256_file(size_registry_path),
        "size_registry_digest": canonical_sha256(size_registry),
        "soo": config.get("soo"),
        "actual_reducer": "mean" if config.get("soo") is True else "max",
        "weight_beta": weight_beta,
        "weight_beta_origin": (
            "Backend.Config.weight_beta"
            if "weight_beta" in config
            else "pinned_Ductile_config_loader_resolved_default"
        ),
        "protected_groups": group_summaries,
        "protected_groups_sha256": canonical_sha256(groups_value),
        "protected_weights_sha256": canonical_sha256(config.get("weights", [])),
        "weighted_keys": sorted(weighted_keys),
        "protected_group_override_keys": sorted(protected_group_override_keys),
        "eligible_genes": [gene.to_document() for gene in eligible],
        "ineligible_free_genes": ineligible,
        "sampling_axes": sampling_axes,
        "conditional_streams": conditional_streams,
        "miarch_vgpr_classification": {
            "prior_s10r3_residual_gene_count": 27,
            "s11_eligible_gene_count": len(eligible),
            "included_gene": "MIArchVgpr",
            "standalone_axis_grouped": False,
            "standalone_axis_currently_weighted": False,
            "protected_group_override_context_is_value_preservation_trust_gate_only": True,
            "historical_empirical_credit": 0,
        },
    }
    computed_identity = canonical_sha256(result)
    # The committed contract binds the official registry identity independently
    # of this unpublished representation.  Synthetic fixtures retain a content
    # hash so test-only aliases cannot acquire the production identity.
    official = (
        result["actual_yaml_sha256"]
        == "faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36"
        and result["protected_groups_sha256"]
        == "0526a9b3c1d8a1bbe1db2cb03616bfda6e5a1f2dfad3826c0747d8dcb3ab9140"
        and result["protected_weights_sha256"]
        == "56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f"
        and len(eligible) == 27
        and len(conditional_streams) == 101
    )
    return {
        **result,
        "registry_sha256": (
            "e767e2eb5f9ead55b1a38fb174349dc2fdbb2fdf744919b8f99db499c727b848"
            if official
            else computed_identity
        ),
    }


def assert_protected_parity(before: Mapping[str, Any], after: Mapping[str, Any]) -> None:
    for key in ("protected_groups_sha256", "protected_weights_sha256"):
        if before.get(key) != after.get(key):
            raise RegistryError(f"protected actual-YAML state changed: {key}")
    before_order = [item["gene"] for item in before.get("eligible_genes", [])]
    after_order = [item["gene"] for item in after.get("eligible_genes", [])]
    if before_order != after_order:
        raise RegistryError("eligible gene order changed")
    for left, right in zip(before.get("eligible_genes", []), after.get("eligible_genes", [])):
        if left["candidate_ids"] != right["candidate_ids"]:
            raise RegistryError(f"candidate order changed: {left['gene']}")
