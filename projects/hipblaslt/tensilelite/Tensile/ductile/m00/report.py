# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Independent-attestation gate and exclusive M00 report renderer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import (
    ContractError,
    ReportLifecycleError,
    load_and_validate,
    load_json_strict,
    sha256_file,
    validate_instance,
)
from .contract import ContractStore, ProtocolLock


ACC_CRITERIA = (
    "M00.ACC.OBS-SEMANTICS",
    "M00.ACC.RECONCILE",
    "M00.ACC.SPLIT-GUARD",
    "M00.ACC.BASELINE-GUARD",
    "M00.ACC.CONTRACT-LOCK",
)


def validate_evidence_file(
        path_value: str | Path, authorized_root: str | Path, *,
        expected_sha256: str | None = None,
        label: str = "criterion evidence") -> Path:
    """Require one regular, non-symlink file inside one verifier run root."""
    root = Path(authorized_root).resolve()
    path = Path(path_value)
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ReportLifecycleError(
            f"{label} escapes the authorized verifier root",
            reason_code="ATTESTATION_CRITERION_PATH_INVALID",
        ) from exc
    cursor = root
    if root.is_symlink() or ".." in relative.parts:
        raise ReportLifecycleError(
            f"{label} path is invalid",
            reason_code="ATTESTATION_CRITERION_PATH_INVALID",
        )
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ReportLifecycleError(
                f"{label} path contains a symlink",
                reason_code="ATTESTATION_CRITERION_PATH_INVALID",
            )
    if not path.resolve(strict=False).is_relative_to(root) or \
            not path.is_file() or \
            expected_sha256 is not None and \
            sha256_file(path) != expected_sha256:
        raise ReportLifecycleError(
            f"{label} is missing or hash-mismatched",
            reason_code="ATTESTATION_CRITERION_MISMATCH",
        )
    return path


def validate_criterion_result_binding(
        criterion: str, envelope: dict[str, Any], *,
        schema_path: str | Path,
        authorized_root: str | Path,
        source_set_sha256: str,
        protocol_lock_sha256: str) -> dict[str, Any]:
    """Parse and bind a typed criterion result and every evidence artifact."""
    expected_fields = {
        "status", "artifact_path", "artifact_sha256",
        "source_set_sha256", "protocol_lock_sha256", "fresh_evidence",
    }
    if not isinstance(envelope, dict) or set(envelope) != expected_fields:
        raise ReportLifecycleError(
            f"criterion envelope fields are invalid: {criterion}",
            reason_code="ATTESTATION_CRITERION_MISMATCH",
        )
    artifact = validate_evidence_file(
        envelope["artifact_path"], authorized_root,
        expected_sha256=envelope["artifact_sha256"],
        label=f"{criterion} result artifact",
    )
    try:
        schema_document = load_json_strict(schema_path)
        result_schema = {
            "$schema": schema_document["$schema"],
            **schema_document["definitions"]["criterion_result"],
            "definitions": schema_document["definitions"],
        }
        result = load_json_strict(artifact)
        validate_instance(
            result, result_schema, label=f"{criterion} result artifact"
        )
    except (ContractError, KeyError) as exc:
        raise ReportLifecycleError(
            f"typed criterion result is invalid: {criterion}: {exc}",
            reason_code="ATTESTATION_CRITERION_RESULT_INVALID",
        ) from exc
    expected = {
        "criterion": criterion,
        "status": envelope["status"],
        "source_set_sha256": source_set_sha256,
        "protocol_lock_sha256": protocol_lock_sha256,
        "fresh_evidence": envelope["fresh_evidence"],
    }
    if any(result[key] != value for key, value in expected.items()) or \
            envelope["source_set_sha256"] != source_set_sha256 or \
            envelope["protocol_lock_sha256"] != protocol_lock_sha256:
        raise ReportLifecycleError(
            f"criterion envelope/result content mismatch: {criterion}",
            reason_code="ATTESTATION_CRITERION_RESULT_MISMATCH",
        )
    evidence_paths = [item["path"] for item in result["fresh_evidence"]]
    if len(evidence_paths) != len(set(evidence_paths)):
        raise ReportLifecycleError(
            f"duplicate declared evidence path: {criterion}",
            reason_code="ATTESTATION_CRITERION_RESULT_MISMATCH",
        )
    for item in result["fresh_evidence"]:
        validate_evidence_file(
            item["path"], authorized_root,
            expected_sha256=item["sha256"],
            label=f"{criterion} declared evidence",
        )
    return result


def _verify_differential_checksums(root: Path) -> None:
    manifest = root / "differential-checksums.sha256"
    entries = {}
    try:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            digest, relative = line.split("  ", 1)
            rel = Path(relative)
            if len(digest) != 64 or relative in entries or \
                    rel.is_absolute() or ".." in rel.parts:
                raise ValueError("invalid differential checksum entry")
            entries[relative] = digest
    except (OSError, ValueError) as exc:
        raise ReportLifecycleError(
            f"differential checksum manifest is invalid: {exc}",
            reason_code="ATTESTATION_EVIDENCE_INVALID",
        ) from exc
    files = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ReportLifecycleError(
                "symlink in attested evidence",
                reason_code="ATTESTATION_EVIDENCE_INVALID",
            )
        if path.is_file() and path != manifest:
            files[path.relative_to(root).as_posix()] = path
    if set(files) != set(entries) or any(
            sha256_file(path) != entries[relative]
            for relative, path in files.items()):
        raise ReportLifecycleError(
            "attested evidence checksum coverage mismatch",
            reason_code="ATTESTATION_EVIDENCE_INVALID",
        )


@dataclass(frozen=True)
class VerifierAttestation:
    data: dict[str, Any]
    path: Path

    @property
    def overall(self) -> str:
        return self.data["overall"]

    @classmethod
    def load(cls, path: str | Path, schema_path: str | Path):
        path = Path(path)
        return cls(load_and_validate(path, schema_path), path)


def validate_report_gate(
        contract_path: str | Path,
        attestation_path: str | Path,
        *,
        repo_root: str | Path) -> VerifierAttestation:
    store = ContractStore(contract_path)
    attestation = VerifierAttestation.load(
        attestation_path,
        store.protocol_root / "schemas/verifier-attestation.schema.json",
    )
    lock_path = Path(repo_root) / store.base_contract["locks"][
        "protocol_lock_path"
    ]
    lock = ProtocolLock(store, repo_root).verify()
    data = attestation.data
    if data["issuer_role"] != "independent-verifier":
        raise ReportLifecycleError(
            "positive or final report requires an independent verifier",
            reason_code="ATTESTATION_ROLE_INVALID",
        )
    whitelist = load_json_strict(
        Path(repo_root) / store.base_contract["locks"]["whitelist_path"]
    )
    allowed_root = (
        Path(repo_root) / whitelist["generated_roots"][1]
    ).resolve()
    expected = {
        "source_set_sha256": lock["m00_source_set_sha256"],
        "contract_sha256": store.base_canonical_sha256,
        "effective_contract_sha256": store.effective_sha256,
        "protocol_lock_sha256": sha256_file(lock_path),
    }
    mismatches = [
        key for key, value in expected.items() if data.get(key) != value
    ]
    run_root = Path(data["run_root"])
    checksum_path = run_root / "differential-checksums.sha256"
    differential_path = run_root / "differential-summary.json"
    if not run_root.resolve(strict=False).is_relative_to(allowed_root) or \
            not run_root.is_dir() or run_root.is_symlink() or \
            not checksum_path.is_file() or \
            not differential_path.is_file() or \
            data["bundle_checksum_manifest_sha256"] != \
            sha256_file(checksum_path) or \
            data["differential_summary_sha256"] != \
            sha256_file(differential_path):
        mismatches.append("run_evidence")
    if mismatches:
        raise ReportLifecycleError(
            f"attestation linked hash mismatch: {sorted(mismatches)}",
            reason_code="ATTESTATION_LINK_MISMATCH",
        )
    _verify_differential_checksums(run_root)
    differential = load_json_strict(differential_path)
    if differential.get("overall") != "PASS":
        raise ReportLifecycleError(
            "attested differential evidence is not healthy",
            reason_code="ATTESTATION_VERDICT_INCONSISTENT",
        )

    criteria = data["criteria"]
    criterion_evidence = data["criterion_evidence"]
    authorized_root = run_root.resolve().parent
    criterion_schema = (
        store.protocol_root / "schemas/verifier-attestation.schema.json"
    )
    for criterion in (
            *ACC_CRITERIA, "M00.FAL.INSTRUMENTATION",
            "M00.STOP.MISSING-EVIDENCE"):
        evidence = criterion_evidence[criterion]
        if criteria[criterion] == "UNVERIFIED" or \
                evidence["status"] == "UNVERIFIED" or \
                evidence["status"] != criteria[criterion]:
            raise ReportLifecycleError(
                f"criterion is missing direct verified evidence: "
                f"{criterion}",
                reason_code="ATTESTATION_CRITERION_UNVERIFIED",
            )
        validate_criterion_result_binding(
            criterion, evidence,
            schema_path=criterion_schema,
            authorized_root=authorized_root,
            source_set_sha256=lock["m00_source_set_sha256"],
            protocol_lock_sha256=sha256_file(lock_path),
        )
    acc_values = [criteria[key] for key in ACC_CRITERIA]
    if all(value == "PASS" for value in acc_values) and \
            criteria["M00.FAL.INSTRUMENTATION"] is False and \
            criteria["M00.STOP.MISSING-EVIDENCE"] is False:
        derived_overall = "PASS"
    elif "FAIL" in acc_values or \
            criteria["M00.FAL.INSTRUMENTATION"] is True or \
            criteria["M00.STOP.MISSING-EVIDENCE"] is True:
        derived_overall = "FAIL"
    elif "BLOCKED" in acc_values:
        derived_overall = "BLOCKED"
    else:
        derived_overall = "INCONCLUSIVE"
    if data["overall"] != derived_overall:
        raise ReportLifecycleError(
            "attestation overall does not match criterion evidence",
            reason_code="ATTESTATION_VERDICT_INCONSISTENT",
        )
    if data["overall"] == "PASS":
        if any(criteria[key] != "PASS" for key in ACC_CRITERIA) or \
                criteria["M00.FAL.INSTRUMENTATION"] is not False or \
                criteria["M00.STOP.MISSING-EVIDENCE"] is not False or \
                data["root_causes"] or data["required_fixes"] or \
                data["evidence_gaps"]:
            raise ReportLifecycleError(
                "positive attestation has inconsistent criterion verdicts",
                reason_code="ATTESTATION_VERDICT_INCONSISTENT",
            )
    elif data["overall"] not in {"FAIL", "BLOCKED", "INCONCLUSIVE"}:
        raise ReportLifecycleError(
            "attestation outcome is not reportable",
            reason_code="ATTESTATION_OUTCOME_INVALID",
        )
    elif not (
            data["root_causes"] or data["required_fixes"] or
            data["evidence_gaps"]):
        raise ReportLifecycleError(
            "non-positive attestation lacks root cause, fix, or gap",
            reason_code="ATTESTATION_EXPLANATION_MISSING",
        )
    return attestation


def _render(attestation: VerifierAttestation) -> str:
    data = attestation.data
    lines = [
        "# M00 study contract and observability report",
        "",
        f"- Outcome: `{data['overall']}`",
        "- Evidence class: deterministic CPU fixture observability only",
        "- GPU/ROCm/performance claim: none",
        "- Original TuningDriver baseline claim: none",
        f"- Independent verifier: `{data['issuer']}`",
        f"- Evidence root: `{data['run_root']}`",
        "",
        "## Criterion verdicts",
        "",
    ]
    for key in (*ACC_CRITERIA, "M00.FAL.INSTRUMENTATION",
                "M00.STOP.MISSING-EVIDENCE"):
        value = data["criteria"][key]
        rendered = str(value).lower() if isinstance(value, bool) else value
        lines.append(f"- `{key}`: `{rendered}`")
    lines.extend([
        "",
        "## Root causes",
        "",
    ])
    lines.extend(
        [f"- {value}" for value in data["root_causes"]] or ["- None."]
    )
    lines.extend([
        "",
        "## Required fixes",
        "",
    ])
    lines.extend(
        [f"- {value}" for value in data["required_fixes"]] or ["- None."]
    )
    lines.extend([
        "",
        "## Evidence gaps",
        "",
    ])
    lines.extend(
        [f"- {value}" for value in data["evidence_gaps"]] or ["- None."]
    )
    lines.extend([
        "",
        "## Claim boundary",
        "",
        "This report does not establish GPU correctness, benchmark "
        "performance, warm-start quality, a downstream winner, or final-"
        "holdout results.",
        "",
    ])
    return "\n".join(lines)


def render_m00_report(
        contract_path: str | Path,
        attestation_path: str | Path,
        output_path: str | Path,
        *,
        repo_root: str | Path) -> Path:
    attestation = validate_report_gate(
        contract_path, attestation_path, repo_root=repo_root
    )
    output = Path(output_path)
    expected = Path(repo_root) / ContractStore(contract_path).base_contract[
        "locks"
    ]["final_report_path"]
    return render_attested_report(attestation, output, expected)


def render_attested_report(
        attestation: VerifierAttestation,
        output_path: str | Path,
        expected_output_path: str | Path) -> Path:
    """Render an already validated attestation with exclusive-create."""
    output = Path(output_path)
    expected = Path(expected_output_path)
    if output.resolve(strict=False) != expected.resolve(strict=False):
        raise ReportLifecycleError(
            "report output is not the canonical final M00 report path",
            reason_code="REPORT_PATH_INVALID",
        )
    if output.exists() or output.is_symlink():
        raise ReportLifecycleError(
            "M00 report already exists",
            reason_code="REPORT_PREEXISTS",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("x", encoding="utf-8") as stream:
            stream.write(_render(attestation))
    except OSError as exc:
        raise ReportLifecycleError(
            f"cannot create M00 report: {exc}",
            reason_code="REPORT_WRITE_FAILED",
        ) from exc
    return output


def verify_m00_report(
        contract_path: str | Path,
        attestation_path: str | Path,
        report_path: str | Path,
        *,
        repo_root: str | Path) -> None:
    attestation = validate_report_gate(
        contract_path, attestation_path, repo_root=repo_root
    )
    report = Path(report_path)
    if report.is_symlink() or not report.is_file():
        raise ReportLifecycleError(
            "M00 report is missing", reason_code="REPORT_MISSING"
        )
    if report.read_text(encoding="utf-8") != _render(attestation):
        raise ReportLifecycleError(
            "M00 report text does not match attestation",
            reason_code="REPORT_CONTENT_MISMATCH",
        )
