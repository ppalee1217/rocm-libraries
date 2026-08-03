# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Stable semantic identity and exactly-two-attempt qualification semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
import stat
import subprocess
from typing import Any, Mapping, Sequence

from .canonical import (
    canonical_json_bytes,
    canonical_sha256,
    sha256_file,
    strict_json_loads,
)


class QualificationError(ValueError):
    """Qualification evidence violates the frozen attempt or identity law."""


class QualificationState(str, Enum):
    PENDING_SECOND_ATTEMPT = "pending_second_attempt"
    EXECUTABLE = "executable"
    EXECUTION_ATTRITION = "execution_attrition"
    BLOCKED_MAPPING = "blocked_mapping"
    CHANGES_REQUIRED = "changes_required_not_evaluated"


ATTEMPT_ROLES = ("producer", "fresh_verifier")
COMPLETE_RESULTS = ("accepted", "normal_reject", "mapping_impossible")


class PinnedQualificationWorker:
    """Invoke the hash-bound resolver/KernelWriter/compiler worker.

    Arbitrary attempt JSON is never accepted.  The host constructs the request,
    owns the child process, checks the exact source/toolchain provenance, and
    then projects the response into a :class:`QualificationAttempt`.
    """

    def __init__(
        self,
        *,
        python_path: Path | str,
        python_sha256: str,
        worker_source_path: Path | str,
        worker_source_sha256: str,
        compiler_path: Path | str,
        compiler_sha256: str,
        resolver_source_sha256: str,
        kernelwriter_source_sha256: str,
        semantic_identity_schema: str,
        qualification_fingerprint_sha256: str,
        qualification_argv: Sequence[str],
        timeout_seconds: int,
        repository_root: Path | str,
        actual_yaml_path: Path | str,
    ):
        self.python_path = Path(python_path)
        self.worker_source_path = Path(worker_source_path).resolve()
        self.compiler_path = Path(compiler_path)
        self.repository_root = Path(repository_root).resolve()
        self.actual_yaml_path = Path(actual_yaml_path).resolve()
        self.resolver_source_sha256 = resolver_source_sha256
        self.kernelwriter_source_sha256 = kernelwriter_source_sha256
        self.semantic_identity_schema = semantic_identity_schema
        self.qualification_fingerprint_sha256 = qualification_fingerprint_sha256
        self.qualification_argv = list(qualification_argv)
        self.timeout_seconds = timeout_seconds
        for path, expected, label in (
            (self.python_path, python_sha256, "python"),
            (self.worker_source_path, worker_source_sha256, "qualification worker source"),
            (self.compiler_path, compiler_sha256, "compiler"),
        ):
            bound = path.resolve()
            info = bound.lstat()
            if (
                not stat.S_ISREG(info.st_mode)
                or bound.is_symlink()
                or sha256_file(bound) != expected
                or (label not in ("python", "compiler") and path.is_symlink())
            ):
                raise QualificationError(f"{label} path/hash/mode mismatch")
        if type(timeout_seconds) is not int or timeout_seconds <= 0:
            raise QualificationError("qualification timeout must be positive")

    def run(
        self,
        *,
        role: str,
        workspace_root: Path | str,
        workspace_root_id: str,
        raw_configuration: Mapping[str, Any],
        occurrence_ids: Sequence[str],
        alias_fanout: Mapping[str, Sequence[str]],
    ) -> tuple[QualificationAttempt, dict[str, Any]]:
        if role not in ATTEMPT_ROLES or not workspace_root_id:
            raise QualificationError("qualification role/root identity is invalid")
        raw_sha256 = canonical_sha256(dict(raw_configuration))
        if (
            type(occurrence_ids) is not list
            or not occurrence_ids
            or len(set(occurrence_ids)) != len(occurrence_ids)
            or any(type(item) is not str or len(item) != 64 for item in occurrence_ids)
            or type(alias_fanout) is not dict
            or set(alias_fanout) != {raw_sha256}
            or alias_fanout[raw_sha256] != list(occurrence_ids)
        ):
            raise QualificationError("qualification occurrence/alias fanout binding is malformed")
        body = {
            "protocol": "s11_qualification_v1",
            "role": role,
            "workspace_root_id": workspace_root_id,
            "raw_configuration": dict(raw_configuration),
            "semantic_identity_schema": self.semantic_identity_schema,
            "occurrence_ids": list(occurrence_ids),
            "alias_fanout_sha256": canonical_sha256(dict(alias_fanout)),
        }
        request = {**body, "request_sha256": canonical_sha256(body)}
        from .native_adapter import materialize_sealed_qualification_argv

        process_argv = materialize_sealed_qualification_argv(
            self.qualification_argv, pinned_source_root=self.repository_root,
            workspace_root=workspace_root,
        )
        completed = subprocess.run(
            process_argv,
            input=canonical_json_bytes(request) + b"\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=self.timeout_seconds,
            cwd=self.repository_root,
            env={
                "PATH": f"{self.compiler_path.parent}:/usr/bin:/bin",
                "LC_ALL": "C",
                "PYTHONNOUSERSITE": "1",
                "PYTHONPATH": "",
                "Tensile_ASM_COMPILER_LAUNCHER": "",
            },
        )
        if completed.returncode != 0:
            raise QualificationError(
                "pinned qualification worker failed or was partial: "
                + completed.stderr.decode("utf-8", errors="replace")[-1000:]
            )
        response = strict_json_loads(completed.stdout)
        expected_keys = {
            "protocol",
            "request_sha256",
            "role",
            "workspace_root_id",
            "complete",
            "result",
            "semantic_identity",
            "reason_code",
            "no_guess",
            "association",
            "provenance",
            "occurrence_ids_sha256",
            "alias_fanout_sha256",
        }
        if type(response) is not dict or set(response) != expected_keys:
            raise QualificationError("qualification response schema/unknown-property failure")
        compiler_argv = [
            str(self.compiler_path),
            "-x",
            "assembler",
            "--target=amdgcn-amd-amdhsa",
            "-mcode-object-version=4",
            "-c",
            "-mcpu=gfx942",
        ]
        expected_provenance = {
            "resolver_source_sha256": self.resolver_source_sha256,
            "kernelwriter_source_sha256": self.kernelwriter_source_sha256,
            "compiler_sha256": sha256_file(self.compiler_path.resolve()),
            "compiler_argv_prefix": compiler_argv,
            "generation_path": "normal_non_proxy_KernelWriterAssembly_then_pinned_assembler",
            "association_preserved": True,
        }
        if (
            response["protocol"] != "s11_qualification_v1"
            or response["request_sha256"] != request["request_sha256"]
            or response["role"] != role
            or response["workspace_root_id"] != workspace_root_id
            or response["complete"] is not True
            or response["no_guess"] is not True
            or response["result"] not in ("accepted", "normal_reject")
            or response["provenance"] != expected_provenance
            or response["occurrence_ids_sha256"] != canonical_sha256(list(occurrence_ids))
            or response["alias_fanout_sha256"] != body["alias_fanout_sha256"]
        ):
            raise QualificationError("qualification provenance/role/substitution guard failed")
        association = response["association"]
        if type(association) is not dict or type(association.get("solution_sha256")) is not str:
            raise QualificationError("solution-to-kernel association is absent")
        if response["result"] == "accepted":
            if (
                type(response["semantic_identity"]) is not str
                or len(response["semantic_identity"]) != 64
                or type(association.get("kernels")) is not list
                or not association["kernels"]
                or any(
                    type(row) is not dict
                    or set(row) != {
                        "kernel_name",
                        "kernel_source_sha256",
                        "compile_output_sha256",
                    }
                    for row in association["kernels"]
                )
            ):
                raise QualificationError("accepted association/kernel compile lineage is incomplete")
        attempt = QualificationAttempt(
            role=role,
            workspace_root_id=workspace_root_id,
            complete=True,
            result=response["result"],
            semantic_identity=response["semantic_identity"],
            qualification_fingerprint=self.qualification_fingerprint_sha256,
            reason_code=response["reason_code"],
            no_guess=True,
            solution_sha256=association["solution_sha256"],
            size_mapping_sha256=canonical_sha256(association.get("size_mapping")),
            kernel_association_sha256=canonical_sha256(association.get("kernels")),
            occurrence_ids_sha256=response["occurrence_ids_sha256"],
            alias_fanout_sha256=response["alias_fanout_sha256"],
            transcript_sha256=canonical_sha256(response),
        )
        return attempt, dict(response)


def semantic_identity(
    resolver_projection: Mapping[str, Any],
    consumer_fields: Mapping[str, Any],
    *,
    schema_version: str,
) -> str:
    """Hash the complete consumer-relevant operational projection."""

    if not schema_version or type(schema_version) is not str:
        raise QualificationError("semantic identity schema version is absent")
    if type(resolver_projection) is not dict or type(consumer_fields) is not dict:
        raise QualificationError("semantic identity projections must be mappings")
    if not resolver_projection or not consumer_fields:
        raise QualificationError("semantic identity projection may not be partial")
    return canonical_sha256(
        {
            "schema_version": schema_version,
            "resolver_projection": dict(resolver_projection),
            "consumer_fields": dict(consumer_fields),
        }
    )


def qualification_fingerprint(
    *,
    semantic_identity_schema: str,
    resolver_sha256: str,
    kernelwriter_sha256: str,
    compiler_argv: Sequence[str],
    toolchain_sha256: str,
    timeout_seconds: int,
) -> str:
    if not compiler_argv or any(type(item) is not str for item in compiler_argv):
        raise QualificationError("compiler argv is absent or malformed")
    if type(timeout_seconds) is not int or timeout_seconds <= 0:
        raise QualificationError("qualification timeout must be positive")
    return canonical_sha256(
        {
            "semantic_identity_schema": semantic_identity_schema,
            "resolver_sha256": resolver_sha256,
            "kernelwriter_sha256": kernelwriter_sha256,
            "compiler_argv": list(compiler_argv),
            "toolchain_sha256": toolchain_sha256,
            "timeout_seconds": timeout_seconds,
            "generation_path": "normal_non_proxy_kernelwriter",
        }
    )


@dataclass(frozen=True)
class QualificationAttempt:
    role: str
    workspace_root_id: str
    complete: bool
    result: str
    semantic_identity: str | None
    qualification_fingerprint: str
    reason_code: str
    no_guess: bool = True
    solution_sha256: str = ""
    size_mapping_sha256: str = ""
    kernel_association_sha256: str = ""
    occurrence_ids_sha256: str = ""
    alias_fanout_sha256: str = ""
    transcript_sha256: str = ""

    def validate(self, expected_role: str) -> None:
        if self.role != expected_role:
            raise QualificationError("qualification attempt role/order changed")
        if not self.workspace_root_id:
            raise QualificationError("qualification attempt root identity is absent")
        if type(self.complete) is not bool or type(self.no_guess) is not bool:
            raise QualificationError("qualification flags must be booleans")
        if self.result not in COMPLETE_RESULTS:
            raise QualificationError("qualification result is not in the closed taxonomy")
        if not self.reason_code:
            raise QualificationError("qualification reason code is absent")
        if self.complete and self.result == "accepted" and self.semantic_identity is None:
            raise QualificationError("accepted attempt lost semantic identity")
        for value in (
            self.solution_sha256,
            self.size_mapping_sha256,
            self.kernel_association_sha256,
            self.occurrence_ids_sha256,
            self.alias_fanout_sha256,
            self.transcript_sha256,
        ):
            if (
                type(value) is not str
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise QualificationError("qualification association/alias transcript binding is absent")


def evaluate_attempts(
    attempts: Sequence[QualificationAttempt],
    *,
    blocked_mapping_allowlist: Sequence[str],
) -> dict[str, Any]:
    """Project exactly two total normal attempts, producer then verifier."""

    if len(attempts) not in (1, 2):
        raise QualificationError("qualification requires one pending or exactly two attempts")
    for index, attempt in enumerate(attempts):
        attempt.validate(ATTEMPT_ROLES[index])
    if len(attempts) == 1:
        state = QualificationState.PENDING_SECOND_ATTEMPT
        return {"state": state.value, "attempt_count": 1, "semantic_identity": None}

    producer, verifier = attempts
    if producer.workspace_root_id == verifier.workspace_root_id:
        state = QualificationState.CHANGES_REQUIRED
        reason = "fresh_verifier_root_not_separate"
    elif not producer.complete or not verifier.complete:
        state = QualificationState.CHANGES_REQUIRED
        reason = "partial_attempt"
    elif not producer.no_guess or not verifier.no_guess:
        state = QualificationState.CHANGES_REQUIRED
        reason = "guessed_field"
    elif producer.qualification_fingerprint != verifier.qualification_fingerprint:
        state = QualificationState.CHANGES_REQUIRED
        reason = "ambient_or_toolchain_drift"
    elif producer.occurrence_ids_sha256 != verifier.occurrence_ids_sha256:
        state = QualificationState.CHANGES_REQUIRED
        reason = "occurrence_binding_discordance"
    elif producer.alias_fanout_sha256 != verifier.alias_fanout_sha256:
        state = QualificationState.CHANGES_REQUIRED
        reason = "alias_fanout_discordance"
    elif producer.result != verifier.result:
        state = QualificationState.CHANGES_REQUIRED
        reason = "discordant_result"
    elif producer.result == "accepted":
        if producer.semantic_identity != verifier.semantic_identity:
            state = QualificationState.CHANGES_REQUIRED
            reason = "semantic_identity_discordance"
        elif producer.solution_sha256 != verifier.solution_sha256:
            state = QualificationState.CHANGES_REQUIRED
            reason = "solution_association_discordance"
        elif producer.size_mapping_sha256 != verifier.size_mapping_sha256:
            state = QualificationState.CHANGES_REQUIRED
            reason = "size_mapping_association_discordance"
        elif producer.kernel_association_sha256 != verifier.kernel_association_sha256:
            state = QualificationState.CHANGES_REQUIRED
            reason = "kernel_association_discordance"
        else:
            state = QualificationState.EXECUTABLE
            reason = "matching_complete_accept"
    elif producer.result == "normal_reject":
        state = QualificationState.EXECUTION_ATTRITION
        reason = "matching_complete_normal_reject"
    else:
        if (
            producer.reason_code == verifier.reason_code
            and producer.reason_code in set(blocked_mapping_allowlist)
        ):
            state = QualificationState.BLOCKED_MAPPING
            reason = producer.reason_code
        else:
            state = QualificationState.CHANGES_REQUIRED
            reason = "mapping_impossibility_not_exactly_allowlisted"
    return {
        "state": state.value,
        "reason": reason,
        "attempt_count": 2,
        "semantic_identity": (
            producer.semantic_identity if state is QualificationState.EXECUTABLE else None
        ),
        "fresh_verifier_root_separate": producer.workspace_root_id != verifier.workspace_root_id,
        "association_parity": (
            producer.solution_sha256 == verifier.solution_sha256
            and producer.size_mapping_sha256 == verifier.size_mapping_sha256
            and producer.kernel_association_sha256 == verifier.kernel_association_sha256
        ),
        "occurrence_alias_parity": (
            producer.occurrence_ids_sha256 == verifier.occurrence_ids_sha256
            and producer.alias_fanout_sha256 == verifier.alias_fanout_sha256
        ),
    }


def value_preservation_state(
    aliases: Sequence[Mapping[str, Any]], *, gene: str, candidate_id: str
) -> dict[str, Any]:
    """A separate trust gate; never changes Fexec membership."""

    matching = [
        row
        for row in aliases
        if row.get("gene") == gene and row.get("candidate_id") == candidate_id
    ]
    if not matching:
        return {"trusted": False, "reason": "no_executable_alias"}
    identities = {row.get("semantic_identity") for row in matching}
    relations = {row.get("relation") for row in matching}
    if None in identities or None in relations:
        return {"trusted": False, "reason": "association_loss"}
    if relations != {"value_preserving"}:
        return {"trusted": False, "reason": "normalization_or_context_dependence"}
    if len(identities) != 1:
        return {"trusted": False, "reason": "cross_value_or_context_confounded"}
    return {
        "trusted": True,
        "reason": "unique_value_preserving_relation",
        "semantic_identity": next(iter(identities)),
    }
