# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Fail-closed M00 whitelist, protected-path, and report-phase guard."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import re
import subprocess

from .canonical import GuardError, load_and_validate, sha256_file
from .contract import ContractStore, ProtocolLock


FORBIDDEN_PATH_FRAGMENTS = (
    "Tensile/backends/",
    "Tensile/BenchmarkProblems.py",
    "Tensile/Tensile.py",
    "/geko/",
    "/formocast/",
    "/mapping.py",
    "/guidance.py",
    "/model.py",
    "/schedule.py",
    "CMakeLists.txt",
)


def verify_protected_path_hashes(
        repo_root: str | Path,
        locked_hashes: dict[str, str]) -> None:
    """Fail closed if any lock-bound protected file is missing or changed."""
    root = Path(repo_root).resolve()
    for relative, expected_sha in locked_hashes.items():
        path = root / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts or \
                path.is_symlink() or not path.is_file() or \
                not path.resolve(strict=False).is_relative_to(root) or \
                sha256_file(path) != expected_sha:
            raise GuardError(
                f"protected path changed: {relative}",
                reason_code="PROTECTED_PATH_CHANGED",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            )


class M00ScopeGuard:
    def __init__(self, repo_root: str | Path, contract_path: str | Path):
        self.repo_root = Path(repo_root).resolve()
        self.store = ContractStore(contract_path)
        whitelist_rel = self.store.base_contract["locks"]["whitelist_path"]
        self.whitelist_path = self.repo_root / whitelist_rel
        self.whitelist = load_and_validate(
            self.whitelist_path,
            self.store.protocol_root / "schemas/m00-whitelist.schema.json",
        )

    def _git(self, arguments: list[str]) -> bytes:
        command = ["git", *arguments]
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise GuardError(
                f"scope git command failed: {exc}",
                reason_code="SCOPE_GIT_FAILED",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            ) from exc
        if result.returncode:
            raise GuardError(
                f"scope git command failed ({result.returncode}): "
                f"{result.stderr.decode('utf-8', errors='replace')}",
                reason_code="SCOPE_GIT_FAILED",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            )
        return result.stdout

    @property
    def _pathspec(self) -> list[str]:
        return [
            "--", ".",
            ":(exclude)agent_run/260724-ductile-origami-warmstart-"
            "sequential/milestones/m00/plan_b.md",
            ":(exclude)agent_run/260724-ductile-origami-warmstart-all/**",
        ]

    def changed_paths(self) -> set[str]:
        parent = self.whitelist["parent_commit"]
        outputs = [
            self._git(["diff", "--name-only", "-z", parent,
                       *self._pathspec]),
            self._git(["diff", "--cached", "--name-only", "-z", parent,
                       *self._pathspec]),
            self._git(["ls-files", "--others", "--exclude-standard", "-z",
                       *self._pathspec]),
        ]
        paths = set()
        for output in outputs:
            paths.update(
                value.decode("utf-8")
                for value in output.split(b"\0") if value
            )
        return paths

    def _verify_parent(self) -> None:
        actual = self._git(["rev-parse", "HEAD"]).decode("ascii").strip()
        expected = self.whitelist["parent_commit"]
        if actual != expected:
            raise GuardError(
                f"parent commit mismatch: expected {expected}, got {actual}",
                reason_code="PARENT_COMMIT_MISMATCH",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            )

    def _verify_protected(self, lock: dict[str, Any]) -> None:
        expected_paths = set(self.whitelist["protected_paths"])
        locked = lock["protected_path_sha256"]
        if set(locked) != expected_paths:
            raise GuardError(
                "protected path set differs from protocol lock",
                reason_code="PROTECTED_PATH_SET_MISMATCH",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            )
        verify_protected_path_hashes(self.repo_root, locked)

    @staticmethod
    def _is_downstream(path: str) -> bool:
        if re.search(r"(^|/)m0[1-9]([-/]|$)", path, re.IGNORECASE):
            return True
        return any(fragment.lower() in path.lower()
                   for fragment in FORBIDDEN_PATH_FRAGMENTS)

    def verify(self, phase: str) -> dict[str, Any]:
        if phase not in {"implementation", "verification"}:
            raise GuardError(
                f"unknown scope phase: {phase}",
                reason_code="SCOPE_PHASE_INVALID",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            )
        self._verify_parent()
        lock = ProtocolLock(self.store, self.repo_root).verify()
        self._verify_protected(lock)
        changed = self.changed_paths()
        allowed = set(self.whitelist["implementation_paths"])
        allowed.update(self.whitelist["protected_paths"])
        allowed.update(self.whitelist["planning_paths"])
        extra = sorted(changed - allowed)
        if extra:
            raise GuardError(
                f"changed path is outside the M00 whitelist: {extra}",
                reason_code="BLOCKED_SCOPE_CONTAMINATION",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            )
        downstream = sorted(path for path in changed
                            if self._is_downstream(path))
        if downstream:
            raise GuardError(
                f"downstream path changed during M00: {downstream}",
                reason_code="BLOCKED_SCOPE_CONTAMINATION",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            )
        final_report = self.repo_root / self.whitelist[
            "conditional_report_paths"
        ][0]
        if final_report.exists() or final_report.is_symlink():
            raise GuardError(
                "final M00 report must not exist before independent rendering",
                reason_code="FINAL_REPORT_PREEXISTS",
                criterion_id="M00.ACC.CONTRACT-LOCK",
            )
        return {
            "phase": phase,
            "parent_commit": self.whitelist["parent_commit"],
            "changed_paths": sorted(changed),
            "protected_paths": sorted(self.whitelist["protected_paths"]),
            "final_report_absent": True,
        }
