# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Executable M00 contract, protocol lock, and linked amendment chain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import copy
import json
import os

from .canonical import (
    ContractError,
    GuardError,
    canonical_json_bytes,
    canonical_json_text,
    load_and_validate,
    load_json_strict,
    sha256_bytes,
    sha256_file,
    validate_instance,
    _plain_finite,
)


FORBIDDEN_OVERRIDE_ENV = {
    "M00_SEED", "M00_POP_SIZE", "M00_N_GEN", "M00_PERIOD",
    "M00_THRESHOLD", "M00_MODEL", "M00_ANALYSIS",
}
FORBIDDEN_OVERRIDE_FLAGS = {
    "--seed", "--pop-size", "--n-gen", "--period", "--threshold",
    "--model", "--analysis", "--operator", "--shape",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _safe_repo_path(repo_root: Path, relative: str, *, require_file=True) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ContractError(
            f"contract path escapes repository root: {relative}",
            reason_code="CONTRACT_PATH_ESCAPE",
        )
    path = repo_root / rel
    if path.is_symlink() or not path.resolve(strict=False).is_relative_to(
            repo_root.resolve()):
        raise ContractError(
            f"contract path is symlinked or escapes root: {relative}",
            reason_code="CONTRACT_PATH_ESCAPE",
        )
    if require_file and not path.is_file():
        raise ContractError(
            f"contract path is missing: {relative}",
            reason_code="CONTRACT_PATH_MISSING",
        )
    return path


def digest_path_set(repo_root: str | Path, relative_paths: list[str]) -> str:
    repo_root = Path(repo_root)
    records = []
    for relative in sorted(relative_paths):
        path = _safe_repo_path(repo_root, relative)
        records.append({"path": relative, "sha256": sha256_file(path)})
    return sha256_bytes(canonical_json_bytes(records))


def digest_schema_set(schema_root: str | Path) -> str:
    root = Path(schema_root)
    files = sorted(root.glob("*.schema.json"))
    if not files:
        raise ContractError(
            f"schema set is empty: {root}",
            reason_code="SCHEMA_SET_EMPTY",
        )
    records = [{"path": path.name, "sha256": sha256_file(path)}
               for path in files]
    return sha256_bytes(canonical_json_bytes(records))


def protected_path_union(
        contract_paths: list[str],
        whitelist_paths: list[str]) -> list[str]:
    """Return the authorized protected union after enforcing base subset."""
    declared = set(contract_paths)
    authorized = set(whitelist_paths)
    if not declared.issubset(authorized):
        raise GuardError(
            "contract-declared protected paths must remain a subset of "
            "the authorized whitelist protected paths",
            reason_code="CONTRACT_PROTECTED_PATH_SUBSET_MISMATCH",
            criterion_id="M00.ACC.CONTRACT-LOCK",
        )
    return sorted(declared | authorized)


@dataclass(frozen=True)
class ExecutionProfile:
    scenario_id: str
    seed: int
    pop_size: int
    n_gen: int
    period: int
    tolerance: float
    diversity_threshold: float
    split_generation: int | None
    evaluator_mode: str

    @classmethod
    def from_contract(cls, contract: dict[str, Any],
                      scenario_id: str) -> "ExecutionProfile":
        matches = [
            item for item in contract["search"]["scenarios"]
            if item["scenario_id"] == scenario_id
        ]
        if len(matches) != 1:
            raise ContractError(
                f"scenario must be registered exactly once: {scenario_id}",
                reason_code="SCENARIO_NOT_REGISTERED",
            )
        item = matches[0]
        return cls(
            scenario_id=item["scenario_id"],
            seed=item["seed"],
            pop_size=item["pop_size"],
            n_gen=item["n_gen"],
            period=item["period"],
            tolerance=item["tolerance"],
            diversity_threshold=item["diversity_threshold"],
            split_generation=item["split_generation"],
            evaluator_mode=item["evaluator_mode"],
        )


def _parse_json_line(line: str, label: str) -> dict[str, Any]:
    def hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ContractError(
                    f"duplicate key in {label}: {key}",
                    reason_code="AMENDMENT_DUPLICATE_KEY",
                )
            result[key] = value
        return result

    try:
        value = json.loads(line, object_pairs_hook=hook)
    except (json.JSONDecodeError, ContractError) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError(
            f"invalid amendment JSON in {label}: {exc}",
            reason_code="AMENDMENT_JSON_INVALID",
        ) from exc
    if not isinstance(value, dict):
        raise ContractError(
            f"amendment line must be an object: {label}",
            reason_code="AMENDMENT_LINE_INVALID",
        )
    return _plain_finite(value)


def _json_pointer_parent(document: Any, pointer: str):
    if not pointer.startswith("/") or pointer == "/":
        raise ContractError(
            f"invalid amendment JSON pointer: {pointer}",
            reason_code="AMENDMENT_PATH_INVALID",
        )
    tokens = [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]
    current = document
    for token in tokens[:-1]:
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and \
                int(token) < len(current):
            current = current[int(token)]
        else:
            raise ContractError(
                f"amendment path does not exist: {pointer}",
                reason_code="AMENDMENT_PATH_MISSING",
            )
    return current, tokens[-1]


def apply_operations(document: dict[str, Any],
                     operations: list[dict[str, Any]]) -> dict[str, Any]:
    effective = copy.deepcopy(document)
    for operation in operations:
        parent, key = _json_pointer_parent(effective, operation["path"])
        op = operation["op"]
        if isinstance(parent, dict):
            exists = key in parent
            if op == "add" and exists:
                raise ContractError("amendment add target already exists")
            if op in {"replace", "remove"} and not exists:
                raise ContractError("amendment target does not exist")
            if op == "remove":
                del parent[key]
            else:
                parent[key] = copy.deepcopy(operation["value"])
        elif isinstance(parent, list) and key.isdigit():
            index = int(key)
            if op == "add" and index == len(parent):
                parent.append(copy.deepcopy(operation["value"]))
            elif index < len(parent) and op == "replace":
                parent[index] = copy.deepcopy(operation["value"])
            elif index < len(parent) and op == "remove":
                del parent[index]
            else:
                raise ContractError("invalid amendment list operation")
        else:
            raise ContractError("amendment parent is not a container")
    return effective


class AmendmentChain:
    def __init__(self, path: str | Path, schema_path: str | Path):
        self.path = Path(path)
        self.schema_path = Path(schema_path)
        self.schema = load_json_strict(self.schema_path)
        self._initial_line_hashes = self._line_hashes()

    def _raw_lines(self) -> list[str]:
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ContractError(
                f"cannot read amendment chain: {exc}",
                reason_code="AMENDMENT_CHAIN_MISSING",
            ) from exc
        if not lines or any(not line.strip() for line in lines):
            raise ContractError(
                "amendment chain must contain nonblank genesis",
                reason_code="AMENDMENT_CHAIN_EMPTY",
            )
        return lines

    def _line_hashes(self) -> list[str]:
        if not self.path.exists():
            return []
        return [sha256_bytes(line.encode("utf-8"))
                for line in self._raw_lines()]

    def assert_append_only(self) -> None:
        current = self._line_hashes()
        if current[:len(self._initial_line_hashes)] != self._initial_line_hashes:
            raise ContractError(
                "existing amendment lines were rewritten, deleted, or reordered",
                reason_code="AMENDMENT_CHAIN_REWRITE",
            )

    def evaluate(self, base_contract: dict[str, Any],
                 contract_schema: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        lines = self._raw_lines()
        records = []
        hashes = []
        effective = copy.deepcopy(base_contract)
        base_sha = sha256_bytes(canonical_json_bytes(base_contract))
        previous_line_sha = None
        previous_effective_sha = base_sha
        previous_version = None
        for index, line in enumerate(lines):
            record = _parse_json_line(line, f"{self.path}:{index + 1}")
            validate_instance(record, self.schema, label=f"amendment line {index}")
            canonical_line = canonical_json_text(record)
            if line != canonical_line:
                raise ContractError(
                    f"amendment line {index} is not canonical JSON",
                    reason_code="AMENDMENT_NOT_CANONICAL",
                )
            line_sha = sha256_bytes(line.encode("utf-8"))
            if record["sequence"] != index:
                raise ContractError(
                    "amendment sequence is not contiguous",
                    reason_code="AMENDMENT_SEQUENCE_INVALID",
                )
            if index == 0:
                if record["record_type"] != "genesis" or \
                        record["base_contract_sha256"] != base_sha or \
                        record["effective_contract_sha256"] != base_sha:
                    raise ContractError(
                        "amendment genesis does not bind the base contract",
                        reason_code="AMENDMENT_GENESIS_MISMATCH",
                    )
            else:
                if record["record_type"] != "amendment" or \
                        record["parent_line_sha256"] != previous_line_sha or \
                        record["parent_effective_contract_sha256"] != \
                        previous_effective_sha:
                    raise ContractError(
                        "amendment parent hash mismatch",
                        reason_code="AMENDMENT_PARENT_MISMATCH",
                    )
                if record["amendment_sha256"] != sha256_bytes(
                        canonical_json_bytes(record["operations"])):
                    raise ContractError(
                        "amendment operation hash mismatch",
                        reason_code="AMENDMENT_CONTENT_MISMATCH",
                    )
                actual_changed_keys = sorted({
                    operation["path"]
                    for operation in record["operations"]
                })
                if record["changed_keys"] != actual_changed_keys:
                    raise ContractError(
                        "amendment changed-key set does not match "
                        "operations",
                        reason_code="AMENDMENT_CHANGED_KEYS_MISMATCH",
                    )
                effective = apply_operations(effective, record["operations"])
                validate_instance(
                    effective, contract_schema,
                    label=f"effective contract at amendment {index}",
                )
                effective_sha = sha256_bytes(canonical_json_bytes(effective))
                if effective_sha != record["effective_contract_sha256"]:
                    raise ContractError(
                        "effective contract hash mismatch",
                        reason_code="AMENDMENT_EFFECTIVE_HASH_MISMATCH",
                    )
                if tuple(int(part) for part in record[
                        "protocol_version"].split(".")) <= tuple(
                        int(part) for part in previous_version.split(".")):
                    raise ContractError(
                        "amendment protocol version did not increase",
                        reason_code="AMENDMENT_VERSION_NOT_INCREMENTED",
                    )
                previous_effective_sha = effective_sha
            previous_line_sha = line_sha
            previous_version = record["protocol_version"]
            records.append(record)
            hashes.append(line_sha)
        return effective, hashes

    def append(self, base_contract: dict[str, Any],
               contract_schema: dict[str, Any], *, protocol_version: str,
               owner: str, occurred_at: str, reason: str,
               decision_provenance: str,
               changed_keys: list[str],
               operations: list[dict[str, Any]]) -> dict[str, Any]:
        self.assert_append_only()
        effective, hashes = self.evaluate(base_contract, contract_schema)
        records = [_parse_json_line(line, "amendment chain")
                   for line in self._raw_lines()]
        previous_version = tuple(
            int(part) for part in records[-1]["protocol_version"].split(".")
        )
        requested_version = tuple(
            int(part) for part in protocol_version.split(".")
        )
        if requested_version <= previous_version:
            raise ContractError(
                "amendment protocol version did not increase",
                reason_code="AMENDMENT_VERSION_NOT_INCREMENTED",
            )
        new_effective = apply_operations(effective, operations)
        validate_instance(
            new_effective, contract_schema, label="amended effective contract"
        )
        if canonical_json_bytes(new_effective) == canonical_json_bytes(
                effective):
            raise ContractError(
                "amendment did not change the effective contract",
                reason_code="AMENDMENT_NO_EFFECT",
            )
        actual_changed_keys = sorted({
            operation["path"] for operation in operations
        })
        if changed_keys != actual_changed_keys:
            raise ContractError(
                "amendment changed-key set does not match operations",
                reason_code="AMENDMENT_CHANGED_KEYS_MISMATCH",
            )
        record = {
            "schema_version": "1.0",
            "record_type": "amendment",
            "sequence": len(records),
            "protocol_version": protocol_version,
            "parent_line_sha256": hashes[-1],
            "parent_effective_contract_sha256": sha256_bytes(
                canonical_json_bytes(effective)
            ),
            "base_contract_sha256": sha256_bytes(
                canonical_json_bytes(base_contract)
            ),
            "amendment_sha256": sha256_bytes(canonical_json_bytes(operations)),
            "owner": owner,
            "occurred_at": occurred_at,
            "reason": reason,
            "decision_provenance": decision_provenance,
            "changed_keys": changed_keys,
            "operations": operations,
            "effective_contract_sha256": sha256_bytes(
                canonical_json_bytes(new_effective)
            ),
        }
        validate_instance(record, self.schema, label="new amendment")
        line = canonical_json_text(record)
        try:
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(line + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            raise ContractError(
                f"cannot append amendment: {exc}",
                reason_code="AMENDMENT_APPEND_FAILED",
            ) from exc
        self._initial_line_hashes.append(sha256_bytes(line.encode("utf-8")))
        return record


class ContractStore:
    def __init__(self, contract_path: str | Path):
        self.contract_path = Path(contract_path).resolve()
        self.protocol_root = self.contract_path.parent
        self.schema_path = self.protocol_root / "schemas/experiment-contract.schema.json"
        self.schema = load_json_strict(self.schema_path)
        self.base_contract = load_and_validate(
            self.contract_path, self.schema_path
        )
        chain_relative = self.base_contract["study"]["amendment_chain_path"]
        self.chain_path = self.protocol_root / Path(chain_relative).name
        self.chain = AmendmentChain(
            self.chain_path,
            self.protocol_root / "schemas/amendment.schema.json",
        )
        self.effective_contract, self.amendment_line_hashes = \
            self.chain.evaluate(self.base_contract, self.schema)
        self._validate_semantics()

    def _validate_semantics(self) -> None:
        contract = self.effective_contract
        scenario_ids = [
            item["scenario_id"] for item in contract["search"]["scenarios"]
        ]
        required_scenarios = {
            "fixed_horizon", "early_stop", "checkpoint_resume"
        }
        if len(scenario_ids) != len(set(scenario_ids)) or \
                set(scenario_ids) != required_scenarios:
            raise ContractError(
                "contract must register each M00 scenario exactly once",
                reason_code="SCENARIO_SET_INVALID",
            )
        profiles = {
            item["scenario_id"]: item
            for item in contract["search"]["scenarios"]
        }
        if profiles["fixed_horizon"]["period"] != 0 or \
                profiles["fixed_horizon"]["split_generation"] is not None or \
                profiles["early_stop"]["period"] <= 0 or \
                profiles["early_stop"]["split_generation"] is not None or \
                profiles["early_stop"]["evaluator_mode"] != "flat" or \
                profiles["checkpoint_resume"]["period"] != 0 or \
                not 0 < profiles["checkpoint_resume"]["split_generation"] < \
                profiles["checkpoint_resume"]["n_gen"]:
            raise ContractError(
                "M00 scenario semantics are inconsistent",
                reason_code="SCENARIO_SEMANTICS_INVALID",
            )
        gene_names = [
            item["name"] for item in contract["search"]["space"]
        ]
        shape_ids = [
            item["shape_id"] for item in contract["measurement"][
                "cpu_fixture"
            ]["shapes"]
        ]
        if len(gene_names) != len(set(gene_names)) or \
                len(shape_ids) != len(set(shape_ids)):
            raise ContractError(
                "search genes and fixture shape IDs must be unique",
                reason_code="CONTRACT_ID_DUPLICATE",
            )
        expected_criteria = {
            "M00.ACC.OBS-SEMANTICS", "M00.ACC.RECONCILE",
            "M00.ACC.SPLIT-GUARD", "M00.ACC.BASELINE-GUARD",
            "M00.ACC.CONTRACT-LOCK", "M00.FAL.INSTRUMENTATION",
            "M00.STOP.MISSING-EVIDENCE",
        }
        actual_criteria = {
            item["criterion_id"] for item in contract["criteria"]
        }
        if actual_criteria != expected_criteria:
            raise ContractError(
                "M00 criterion set is incomplete",
                reason_code="CRITERION_SET_INVALID",
            )

    @property
    def base_file_sha256(self) -> str:
        return sha256_file(self.contract_path)

    @property
    def base_canonical_sha256(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.base_contract))

    @property
    def effective_sha256(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.effective_contract))

    def profile(self, scenario_id: str) -> ExecutionProfile:
        return ExecutionProfile.from_contract(
            self.effective_contract, scenario_id
        )

    def assert_no_execution_overrides(self, argv: list[str] | None = None,
                                      environ: dict[str, str] | None = None):
        environ = os.environ if environ is None else environ
        found_env = sorted(FORBIDDEN_OVERRIDE_ENV & set(environ))
        found_flags = sorted(
            flag for flag in (argv or [])
            if flag.split("=", 1)[0] in FORBIDDEN_OVERRIDE_FLAGS
        )
        if found_env or found_flags:
            raise ContractError(
                f"execution overrides are forbidden; env={found_env}, "
                f"flags={found_flags}",
                reason_code="EXECUTION_OVERRIDE_FORBIDDEN",
            )


class ProtocolLock:
    def __init__(self, store: ContractStore, repo_root: str | Path):
        self.store = store
        self.repo_root = Path(repo_root).resolve()
        relative = store.base_contract["locks"]["protocol_lock_path"]
        self.path = _safe_repo_path(
            self.repo_root, relative, require_file=False
        )
        self.schema_path = (
            store.protocol_root / "schemas/protocol-lock.schema.json"
        )

    def _computed_fields(self) -> dict[str, Any]:
        contract = self.store.base_contract
        locks = contract["locks"]
        whitelist_path = _safe_repo_path(
            self.repo_root, locks["whitelist_path"]
        )
        whitelist = load_json_strict(whitelist_path)
        source_paths = whitelist["source_set_paths"]
        registry_hashes = {
            name: sha256_file(_safe_repo_path(self.repo_root, relative))
            for name, relative in sorted(locks["registry_paths"].items())
        }
        protected_paths = protected_path_union(
            locks["protected_paths"], whitelist["protected_paths"]
        )
        protected_hashes = {
            relative: sha256_file(_safe_repo_path(self.repo_root, relative))
            for relative in protected_paths
        }
        return {
            "base_contract_file_sha256": self.store.base_file_sha256,
            "base_contract_canonical_sha256":
                self.store.base_canonical_sha256,
            "shape_registry_sha256": registry_hashes["shape"],
            "baseline_registry_sha256": registry_hashes["baseline"],
            "revision_registry_sha256": registry_hashes["revision"],
            "whitelist_sha256": sha256_file(whitelist_path),
            "schema_set_sha256": digest_schema_set(
                self.store.protocol_root / "schemas"
            ),
            "m00_source_set_sha256": digest_path_set(
                self.repo_root, source_paths
            ),
            "analysis_sha256": sha256_file(_safe_repo_path(
                self.repo_root, contract["study"]["m00_design_path"]
            )),
            "protected_path_sha256": protected_hashes,
            "amendment_chain_genesis_sha256":
                self.store.amendment_line_hashes[0],
        }

    def initialize(self, owner: str) -> dict[str, Any]:
        if self.path.exists() or self.path.is_symlink():
            raise GuardError(
                f"protocol lock already exists: {self.path}",
                reason_code="PROTOCOL_LOCK_EXISTS",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            )
        document = {
            "schema_version": "1.0",
            "lock_state": "locked",
            "owner": owner,
            "locked_at": _utc_now(),
            **self._computed_fields(),
            "holdout_seal_state": "not_registered",
            "winner_lock_state": "not_registered",
        }
        schema = load_json_strict(self.schema_path)
        validate_instance(document, schema, label="protocol lock")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.path.open("x", encoding="utf-8") as stream:
                stream.write(canonical_json_text(document) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            raise GuardError(
                f"cannot initialize protocol lock: {exc}",
                reason_code="PROTOCOL_LOCK_WRITE_FAILED",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            ) from exc
        return document

    def verify(self) -> dict[str, Any]:
        if not self.path.is_file() or self.path.is_symlink():
            raise GuardError(
                "protocol lock is missing or symlinked",
                reason_code="PROTOCOL_LOCK_MISSING",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            )
        document = load_and_validate(self.path, self.schema_path)
        computed = self._computed_fields()
        mismatches = sorted(
            key for key, value in computed.items()
            if document.get(key) != value
        )
        if mismatches:
            raise GuardError(
                f"protocol lock mismatch: {mismatches}",
                reason_code="PROTOCOL_LOCK_MISMATCH",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            )
        return document
