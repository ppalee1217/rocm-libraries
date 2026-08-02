# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT
"""Exact size registry, mapping parity, and bounded attempt semantics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contract import (
    S10R4Error,
    canonical_sha256,
    ordinary_file_records,
    load_json,
    materialize_command_template,
    validate_document_schema,
)


SIZES = (
    ("size-00", [8, 8, 1, 128]),
    ("size-01", [256, 256, 1, 1024]),
    ("size-02", [2304, 1024, 1, 214336]),
)

PARITY_FIELDS = (
    "size",
    "raw_config",
    "resolved_solution",
    "canonical_config_hash",
    "size_mapping",
    "formocast_input",
    "required_field_provenance",
)

SIZE_BY_ID = {size_id: tuple(value) for size_id, value in SIZES}

REQUIRED_MAPPING_FIELDS = (
    "waveNum",
    "macroTile",
    "matrixInstruction",
    "grvwA",
    "grvwB",
    "gwvwC",
    "gwvwD",
    "depthU",
    "globalSplitU",
    "workGroupMapping",
    "globalAccumulation",
    "workGroupMappingXCC",
    "workGroupMappingXCCGroup",
    "globalSplitUCoalesced",
    "globalSplitUWorkGroupMappingRoundRobin",
    "CUOccupancy",
    "PrefetchGlobalRead",
    "MathClocksUnrolledLoop",
    "DirectToVgprA",
    "DirectToVgprB",
    "NumLoadsCoalescedA",
    "NumLoadsCoalescedB",
    "VectorWidthA",
    "VectorWidthB",
    "LocalSplitU",
    "DirectToLdsA",
    "DirectToLdsB",
    "waveGroup",
)


def build_size_registry() -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        "document_kind": "size_registry",
        "coordinate_order": ["M", "N", "NumBatches", "K"],
        "dtype": "BFloat16",
        "layout": "NN",
        "batched": True,
        "soo": False,
        "reduce_fn": "max",
        "n_elements_to_validate": 128,
        "row_count": 3,
        "sizes": [{"size_id": size_id, "value": value} for size_id, value in SIZES],
        "registry_digest": "0" * 64,
    }
    document["registry_digest"] = canonical_sha256(
        {key: value for key, value in document.items() if key != "registry_digest"}
    )
    return document


def validate_size_registry(document: Mapping[str, Any]) -> None:
    validate_document_schema(document)
    if document.get("checkpoint_id") != "S10R4" or document.get("document_kind") != "size_registry":
        raise S10R4Error("size registry identity mismatch")
    if document.get("sizes") != [{"size_id": size_id, "value": value} for size_id, value in SIZES]:
        raise S10R4Error("size registry values/order mismatch")
    if document.get("row_count") != 3:
        raise S10R4Error("size registry row count mismatch")
    projection = {key: value for key, value in document.items() if key != "registry_digest"}
    if canonical_sha256(projection) != document.get("registry_digest"):
        raise S10R4Error("size registry digest mismatch")


def validate_size_mapping(mapping: Mapping[str, Any], provenance: Mapping[str, Any]) -> None:
    if set(mapping) != set(REQUIRED_MAPPING_FIELDS):
        raise S10R4Error("SizeMapping exact field set mismatch")
    if set(provenance) != set(REQUIRED_MAPPING_FIELDS):
        raise S10R4Error("required-field provenance exact set mismatch")
    for field in REQUIRED_MAPPING_FIELDS:
        source = provenance[field]
        if not isinstance(source, dict) or not source.get("source_path") or source.get("guessed") is not False:
            raise S10R4Error(f"required mapping field has absent/guessed provenance: {field}")
    if not (isinstance(mapping["macroTile"], list) and len(mapping["macroTile"]) == 3):
        raise S10R4Error("macroTile must contain exactly three integers")
    if not (isinstance(mapping["matrixInstruction"], list) and len(mapping["matrixInstruction"]) == 4):
        raise S10R4Error("matrixInstruction must contain exactly four integers")
    if not (isinstance(mapping["waveGroup"], list) and len(mapping["waveGroup"]) == 2):
        raise S10R4Error("waveGroup must contain exactly two integers")


def validate_mapping_batch(rows: Sequence[Mapping[str, Any]], selected_hashes: Sequence[str], pass_id: str) -> None:
    if pass_id not in ("A", "B"):
        raise S10R4Error("mapping pass must be A or B")
    expected = [(config_hash, size_id) for config_hash in selected_hashes for size_id, _ in SIZES]
    observed: list[tuple[str, str]] = []
    if len(rows) != 3 * len(selected_hashes):
        raise S10R4Error("mapping batch is not exact 3K")
    for ordinal, row in enumerate(rows):
        if row.get("pass_id") != pass_id or row.get("sorted_slot") != ordinal:
            raise S10R4Error("mapping row pass/ordinal mismatch")
        expected_keys = {"pass_id", "sorted_slot", "size_id", *PARITY_FIELDS}
        if set(row) != expected_keys:
            raise S10R4Error("mapping row exact field set mismatch")
        config_hash = row.get("canonical_config_hash")
        size_id = row.get("size_id")
        if not isinstance(config_hash, str) or not isinstance(size_id, str) or size_id not in SIZE_BY_ID:
            raise S10R4Error("mapping row identity malformed")
        size = row.get("size")
        if (
            not isinstance(size, list)
            or len(size) != 4
            or any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in size)
            or tuple(size) != SIZE_BY_ID[size_id]
        ):
            raise S10R4Error("mapping row size differs from its exact size-registry identity")
        formocast = row.get("formocast_input")
        if not isinstance(formocast, dict) or set(formocast) != {"problem", "size_mapping"}:
            raise S10R4Error("mapping row Formocast input has an inexact field set")
        problem = formocast.get("problem")
        if not isinstance(problem, dict) or set(problem) != {"M", "N", "NumBatches", "K"}:
            raise S10R4Error("mapping row Formocast problem has an inexact field set")
        if [problem[key] for key in ("M", "N", "NumBatches", "K")] != size:
            raise S10R4Error("mapping row size and Formocast problem are not identical")
        if formocast.get("size_mapping") != row.get("size_mapping"):
            raise S10R4Error("mapping row Formocast SizeMapping differs from its row projection")
        validate_size_mapping(row["size_mapping"], row["required_field_provenance"])
        observed.append((config_hash, size_id))
    if observed != expected:
        raise S10R4Error("mapping batch order/completeness mismatch")


def compare_mapping_passes(pass_a: Sequence[Mapping[str, Any]], pass_b: Sequence[Mapping[str, Any]]) -> None:
    if len(pass_a) != len(pass_b):
        raise S10R4Error("mapping A/B row-count mismatch")
    for ordinal, (left, right) in enumerate(zip(pass_a, pass_b)):
        for field in PARITY_FIELDS:
            if left.get(field) != right.get(field):
                raise S10R4Error(f"mapping A/B parity mismatch at row {ordinal}: {field}")


@dataclass(frozen=True)
class MappingAttempt:
    status: str
    signature_id: str | None = None
    failing_pass_id: str | None = None
    first_failing_config_hash: str | None = None
    first_failing_sorted_slot: int | None = None
    exact_signature_fields: Mapping[str, Any] | None = None
    complete_request_digest: str | None = None
    source_toolchain_harness_identity: str | None = None

    def __post_init__(self) -> None:
        optional = (
            self.signature_id, self.failing_pass_id, self.first_failing_config_hash,
            self.first_failing_sorted_slot, self.exact_signature_fields,
            self.complete_request_digest, self.source_toolchain_harness_identity,
        )
        if self.status == "success":
            if any(value is not None for value in optional):
                raise S10R4Error("mapping success attempt carries failure identity")
            return
        if self.status != "allowlisted_failure" or any(value is None for value in optional):
            raise S10R4Error("mapping attempt status/failure identity is incomplete")
        if self.failing_pass_id not in ("A", "B"):
            raise S10R4Error("mapping failure pass identity is invalid")
        for name, value in (
            ("first_failing_config_hash", self.first_failing_config_hash),
            ("complete_request_digest", self.complete_request_digest),
            ("source_toolchain_harness_identity", self.source_toolchain_harness_identity),
        ):
            if (
                not isinstance(value, str) or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise S10R4Error(f"mapping failure {name} is malformed")
        if (
            not isinstance(self.first_failing_sorted_slot, int)
            or isinstance(self.first_failing_sorted_slot, bool)
            or not 0 <= self.first_failing_sorted_slot < 60
        ):
            raise S10R4Error("mapping failure sorted-slot identity is malformed")
        expected_signatures = {
            "codegen_resource_overflow": {
                "failure_stage": "kernel_source_generation",
                "native_error_class": "KernelWriterAssembly_overflowedResources",
                "native_error_code": 5,
                "processKernelSource_result_code": -2,
                "worker_returncode": 23,
                "post_filter_solution_present": False,
            },
            "required_field_unresolved": {
                "failure_stage": "required_field_resolution",
                "resolver_result": None,
                "guessed_value_used": False,
                "input_source_and_mapping_identity_complete": True,
            },
        }
        if self.signature_id not in expected_signatures:
            raise S10R4Error("mapping failure signature ID is not allowlisted")
        if dict(self.exact_signature_fields or {}) != expected_signatures[self.signature_id]:
            raise S10R4Error("mapping failure exact signature fields mismatch")


def decide_mapping_attempts(attempts: Sequence[MappingAttempt]) -> str:
    if len(attempts) == 1 and attempts[0].status == "success":
        return "mapping_pass_PASS"
    if len(attempts) != 2:
        raise S10R4Error("mapping attempts must be one success or two failed reproductions")
    first, second = attempts
    if first.status == "success":
        raise S10R4Error("CHANGES_REQUIRED: retry after mapping success is forbidden")
    if first.status != "allowlisted_failure" or second.status != "allowlisted_failure":
        raise S10R4Error("CHANGES_REQUIRED: nonallowlisted/partial mapping attempt")
    equality = (
        first.signature_id,
        first.failing_pass_id,
        first.first_failing_config_hash,
        first.first_failing_sorted_slot,
        first.exact_signature_fields,
        first.complete_request_digest,
        first.source_toolchain_harness_identity,
    ) == (
        second.signature_id,
        second.failing_pass_id,
        second.first_failing_config_hash,
        second.first_failing_sorted_slot,
        second.exact_signature_fields,
        second.complete_request_digest,
        second.source_toolchain_harness_identity,
    )
    if not equality:
        raise S10R4Error("CHANGES_REQUIRED: mapping failure reproduction mismatch")
    return "negative_S1_ENTRY_BLOCKED_FT_BLOCKED_MAPPING_edge_null"


def project_size_mapping(solution: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project the pinned Contractions.SizeMapping.FromOriginalState fields exactly."""
    global_accumulation = {
        "SingleBuffer": 1,
        "MultipleBuffer": 2,
        "MultipleBufferSingleKernel": 3,
        "PartialsBuffer": 4,
    }.get(solution.get("_GlobalAccumulation"), 0)
    sources: dict[str, tuple[Any, str]] = {
        "waveNum": (solution["NumThreads"] // solution["WavefrontSize"], "NumThreads//WavefrontSize"),
        "macroTile": ([solution["MacroTile0"], solution["MacroTile1"], 1], "MacroTile0,MacroTile1,constant_one"),
        "matrixInstruction": (list(solution["MatrixInstruction"][:4]), "MatrixInstruction[0:4]"),
        "grvwA": (solution["GlobalReadVectorWidthA"], "GlobalReadVectorWidthA"),
        "grvwB": (solution["GlobalReadVectorWidthB"], "GlobalReadVectorWidthB"),
        "gwvwC": (solution["StoreVectorWidth"], "StoreVectorWidth"),
        "gwvwD": (solution["StoreVectorWidth"], "StoreVectorWidth"),
        "depthU": (solution["DepthU"], "DepthU"),
        "globalSplitU": (solution["GlobalSplitU"], "GlobalSplitU"),
        "workGroupMapping": (solution["WorkGroupMapping"], "WorkGroupMapping"),
        "globalAccumulation": (global_accumulation, "_GlobalAccumulation exact enum projection"),
        "workGroupMappingXCC": (solution["WorkGroupMappingXCC"], "WorkGroupMappingXCC"),
        "workGroupMappingXCCGroup": (solution["WorkGroupMappingXCCGroup"], "WorkGroupMappingXCCGroup"),
        "globalSplitUCoalesced": (bool(solution["GlobalSplitUCoalesced"]), "GlobalSplitUCoalesced"),
        "globalSplitUWorkGroupMappingRoundRobin": (
            bool(solution["GlobalSplitUWorkGroupMappingRoundRobin"]),
            "GlobalSplitUWorkGroupMappingRoundRobin",
        ),
        "CUOccupancy": (solution["CUOccupancy"], "CUOccupancy"),
        "PrefetchGlobalRead": (int(solution["PrefetchGlobalRead"]), "PrefetchGlobalRead"),
        "MathClocksUnrolledLoop": (solution["MathClocksUnrolledLoop"], "MathClocksUnrolledLoop"),
        "DirectToVgprA": (bool(solution["DirectToVgprA"]), "DirectToVgprA"),
        "DirectToVgprB": (bool(solution["DirectToVgprB"]), "DirectToVgprB"),
        "NumLoadsCoalescedA": (solution["NumLoadsCoalescedA"], "NumLoadsCoalescedA"),
        "NumLoadsCoalescedB": (solution["NumLoadsCoalescedB"], "NumLoadsCoalescedB"),
        "VectorWidthA": (solution["VectorWidthA"], "VectorWidthA"),
        "VectorWidthB": (solution["VectorWidthB"], "VectorWidthB"),
        "LocalSplitU": (solution["LocalSplitU"], "LocalSplitU"),
        "DirectToLdsA": (bool(solution["DirectToLdsA"]), "DirectToLdsA"),
        "DirectToLdsB": (bool(solution["DirectToLdsB"]), "DirectToLdsB"),
        "waveGroup": (list(solution["MIWaveGroup"]), "MIWaveGroup"),
    }
    mapping = {field: sources[field][0] for field in REQUIRED_MAPPING_FIELDS}
    provenance = {
        field: {
            "source_path": f"Contractions.SizeMapping.FromOriginalState.{sources[field][1]}",
            "source_value_sha256": canonical_sha256(sources[field][0]),
            "guessed": False,
        }
        for field in REQUIRED_MAPPING_FIELDS
    }
    validate_size_mapping(mapping, provenance)
    return mapping, provenance


def mapping_request(
    pass_id: str,
    attempt: int,
    selected_rows: Sequence[Mapping[str, Any]],
    cwd: Path,
    environment: Mapping[str, str],
    effective_lock_digest: str,
) -> dict[str, Any]:
    if pass_id not in ("A", "B") or attempt not in (1, 2):
        raise S10R4Error("mapping request pass/attempt outside frozen table")
    if len(effective_lock_digest) != 64 or any(ch not in "0123456789abcdef" for ch in effective_lock_digest):
        raise S10R4Error("mapping request effective-lock digest is malformed")
    rows = sorted(selected_rows, key=lambda row: row["config_hash"])
    hashes = [row.get("config_hash") for row in rows]
    if not 10 <= len(rows) <= 20 or len(set(hashes)) != len(rows):
        raise S10R4Error("mapping request selection is not a distinct frozen K in [10,20]")
    if any(
        not isinstance(row.get("raw_config"), Mapping)
        or canonical_sha256(row["raw_config"]) != row.get("config_hash")
        for row in rows
    ):
        raise S10R4Error("mapping request config hash differs from its raw configuration")
    request: dict[str, Any] = {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        "document_kind": "mapping_request",
        "pass_id": pass_id,
        "attempt": attempt,
        "selected_rows": [
            {"config_hash": row["config_hash"], "raw_config": row["raw_config"]} for row in rows
        ],
        "sizes": [{"size_id": size_id, "value": value} for size_id, value in SIZES],
        "cwd": cwd.resolve(strict=False).as_posix(),
        "environment": dict(environment),
        "effective_lock_digest": effective_lock_digest,
        "timeout_s": 7200,
        "actual_yaml": "/src/rocm-libraries/study_docs/research/ductile-origami-warmstart/protocol/v1/inputs/s10-generated.yaml",
        "actual_yaml_sha256": "faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36",
        "source_commit": "5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39",
    }
    request["input_digest"] = canonical_sha256(request)
    validate_document_schema(request)
    return request


def _actual_mapping_backend(request: Mapping[str, Any]) -> dict[str, Any]:
    from .census import (
        _actual_census_backend,
        _worker_artifact_inventory,
        classify_native_membership,
        reconcile_native_artifacts,
    )

    rows: list[dict[str, Any]] = []
    for config_slot, selected in enumerate(request["selected_rows"]):
        child_root = Path(request["cwd"]) / f"rows/config-{config_slot:02d}-{selected['config_hash']}"
        child_request = {
            "config_hash": selected["config_hash"],
            "raw_config": selected["raw_config"],
            "actual_yaml": request["actual_yaml"],
            "actual_yaml_sha256": request["actual_yaml_sha256"],
            "cwd": child_root.as_posix(),
            "artifact_root": (child_root / "artifacts").as_posix(),
        }
        child_root.mkdir(parents=True, exist_ok=False)
        native = _actual_census_backend(child_request)
        native_inventory = _worker_artifact_inventory(Path(child_request["artifact_root"]))
        native = reconcile_native_artifacts(native, native_inventory, selected["config_hash"])
        classify_native_membership(native)
        if native["process_returncode"] != 0:
            first_error = next((row for row in native["required_assembly_kernels"] if row["err"]), None)
            signature = {
                "failure_stage": "kernel_source_generation",
                "native_error_class": "KernelWriterAssembly_overflowedResources",
                "native_error_code": None if first_error is None else first_error["overflowed_resources"],
                "processKernelSource_result_code": (
                    None if first_error is None else first_error["processKernelSource_result_code"]
                ),
                "worker_returncode": native["process_returncode"],
                "post_filter_solution_present": native["post_filter_solution_present"],
            }
            if signature != {
                "failure_stage": "kernel_source_generation",
                "native_error_class": "KernelWriterAssembly_overflowedResources",
                "native_error_code": 5,
                "processKernelSource_result_code": -2,
                "worker_returncode": 23,
                "post_filter_solution_present": False,
            }:
                raise S10R4Error("mapping attrition is not the allowlisted resource-overflow signature")
            return {
                "status": "allowlisted_failure",
                "worker_returncode": 23,
                "signature_id": "codegen_resource_overflow",
                "failing_pass_id": request["pass_id"],
                "first_failing_config_hash": selected["config_hash"],
                "first_failing_sorted_slot": 3 * config_slot,
                "exact_signature_fields": signature,
            }
        solution = native.get("resolved_solution")
        if not isinstance(solution, dict):
            raise S10R4Error("mapping native resolution lacks the exact solution state")
        try:
            mapping, provenance = project_size_mapping(solution)
        except KeyError as exc:
            return {
                "status": "allowlisted_failure",
                "worker_returncode": 24,
                "signature_id": "required_field_unresolved",
                "failing_pass_id": request["pass_id"],
                "first_failing_config_hash": selected["config_hash"],
                "first_failing_sorted_slot": 3 * config_slot,
                "exact_signature_fields": {
                    "failure_stage": "required_field_resolution",
                    "resolver_result": None,
                    "guessed_value_used": False,
                    "input_source_and_mapping_identity_complete": True,
                },
            }
        for size_id, value in SIZES:
            rows.append(
                {
                    "pass_id": request["pass_id"],
                    "sorted_slot": len(rows),
                    "size_id": size_id,
                    "size": value,
                    "raw_config": selected["raw_config"],
                    "resolved_solution": solution,
                    "canonical_config_hash": selected["config_hash"],
                    "size_mapping": mapping,
                    "formocast_input": {
                        "problem": {"M": value[0], "N": value[1], "NumBatches": value[2], "K": value[3]},
                        "size_mapping": mapping,
                    },
                    "required_field_provenance": provenance,
                }
            )
    validate_mapping_batch(rows, [row["config_hash"] for row in request["selected_rows"]], request["pass_id"])
    return {"status": "success", "worker_returncode": 0, "rows": rows}


def execute_mapping_worker(
    request: Mapping[str, Any],
    result_path: Path,
    *,
    backend: Any = None,
) -> int:
    expected = {
        "schema_version", "checkpoint_id", "document_kind", "pass_id", "attempt",
        "selected_rows", "sizes", "cwd", "environment", "timeout_s", "actual_yaml",
        "actual_yaml_sha256", "source_commit", "effective_lock_digest", "input_digest",
    }
    if set(request) != expected or request.get("document_kind") != "mapping_request":
        raise S10R4Error("mapping worker request exact field set mismatch")
    if canonical_sha256({key: value for key, value in request.items() if key != "input_digest"}) != request["input_digest"]:
        raise S10R4Error("mapping worker request digest mismatch")
    if Path.cwd().resolve().as_posix() != request["cwd"] or result_path.parent.resolve() != Path(request["cwd"]):
        raise S10R4Error("mapping worker cwd/result association mismatch")
    output = (backend or _actual_mapping_backend)(request)
    returncode = output.get("worker_returncode")
    if returncode not in (0, 23, 24):
        raise S10R4Error("mapping worker produced an unknown return code")
    if returncode == 0:
        validate_mapping_batch(
            output["rows"],
            [row["config_hash"] for row in request["selected_rows"]],
            request["pass_id"],
        )
    rows_root = Path(request["cwd"]) / "rows"
    if rows_root.is_dir():
        records, _ = ordinary_file_records(rows_root)
    else:
        records = []
    document = {
        "schema_version": 1,
        "checkpoint_id": "S10R4",
        "document_kind": "mapping_attempt",
        "pass_id": request["pass_id"],
        "attempt": request["attempt"],
        "input_digest": request["input_digest"],
        "cwd": request["cwd"],
        "argv": materialize_command_template("mapping_child", {"attempt_root": request["cwd"]}),
        "environment": request["environment"],
        "effective_lock_digest": request["effective_lock_digest"],
        "outputs": output,
        "artifact_inventory": records,
    }
    from .ledger import finalize_child

    finalize_child(
        result_path,
        document,
        {"document_kind": "mapping_attempt", "pass_id": request["pass_id"], "attempt": request["attempt"]},
    )
    validate_document_schema(load_json(result_path))
    return int(returncode)
