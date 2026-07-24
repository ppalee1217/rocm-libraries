# Copyright (c) Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Fresh, root-contained M00 artifact bundle writing and checksums."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any
import os
import platform
import re
import shutil
import sys

from .canonical import (
    MissingEvidenceError,
    canonical_json_bytes,
    sha256_file,
)


_GENERATED_INPUT_PATTERNS = {
    "generation": re.compile(r"^generation-[0-9]{4}\.json$"),
    "invocation": re.compile(r"^invocation-[0-9]{4}\.json$"),
}


def generated_input_inventory(
        root: str | Path) -> tuple[str, tuple[Path, ...]]:
    """Classify one strict generated-input layout and reject everything else."""
    directory = Path(root) / "generated-inputs"
    if directory.is_symlink() or not directory.is_dir():
        raise MissingEvidenceError(
            "recognized generated-input directory is missing",
            reason_code="GENERATED_INPUT_INVENTORY_MISSING",
        )
    recognized: dict[str, list[Path]] = {
        key: [] for key in _GENERATED_INPUT_PATTERNS
    }
    unknown = []
    for path in sorted(directory.iterdir()):
        if path.is_symlink() or not path.is_file():
            unknown.append(path.name)
            continue
        matches = [
            kind for kind, pattern in _GENERATED_INPUT_PATTERNS.items()
            if pattern.fullmatch(path.name)
        ]
        if len(matches) != 1:
            unknown.append(path.name)
        else:
            recognized[matches[0]].append(path)
    active = [kind for kind, paths in recognized.items() if paths]
    if unknown or len(active) != 1:
        detail = {
            "unknown": unknown,
            "active_layouts": active,
        }
        raise MissingEvidenceError(
            f"generated-input inventory is unknown, empty, or mixed: "
            f"{detail}",
            reason_code="GENERATED_INPUT_INVENTORY_INVALID",
        )
    kind = active[0]
    return kind, tuple(recognized[kind])


@dataclass(frozen=True)
class ArtifactLayout:
    manifest: str = "run-manifest.json"
    environment: str = "environment.json"
    search_space: str = "search-space.json"
    ga_events: str = "ga-events.jsonl"
    observer_events: str = "observer-events.jsonl"
    observations: str = "benchmark-observations.jsonl"
    checkpoint: str = "checkpoints/ga.checkpoint"
    checkpoint_metadata: str = "checkpoints/ga.checkpoint.metadata.json"
    trajectory: str = "trajectory.json"
    summary: str = "summary.json"
    checksums: str = "checksums.sha256"

    @property
    def required_files(self) -> tuple[str, ...]:
        return (
            self.manifest,
            self.environment,
            self.search_space,
            "contract/experiment-contract.yaml",
            "contract/effective-contract.json",
            "contract/shape-registry.csv",
            "contract/baseline-registry.json",
            "contract/revision-registry.json",
            "contract/protocol-lock.json",
            "contract/amendment-chain.jsonl",
            self.ga_events,
            self.observer_events,
            self.observations,
            self.checkpoint,
            self.checkpoint_metadata,
            self.trajectory,
            self.summary,
            self.checksums,
        )


class RunBundleWriter:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        if self.root.exists() or self.root.is_symlink():
            raise MissingEvidenceError(
                f"artifact root must not already exist: {self.root}",
                reason_code="ARTIFACT_ROOT_EXISTS",
            )
        self.root.parent.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(mode=0o755)
        self._counter = 0

    def contained(self, relative: str | Path, *, must_exist: bool = False) -> Path:
        relative = Path(relative)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise MissingEvidenceError(
                f"artifact path escapes root: {relative}",
                reason_code="ARTIFACT_PATH_ESCAPE",
            )
        candidate = self.root.joinpath(relative)
        current = self.root
        for part in relative.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise MissingEvidenceError(
                    f"symlink forbidden in artifact path: {current}",
                    reason_code="ARTIFACT_SYMLINK",
                )
        resolved_root = self.root.resolve()
        resolved_candidate = candidate.resolve(strict=False)
        if not resolved_candidate.is_relative_to(resolved_root):
            raise MissingEvidenceError(
                f"artifact path escapes root: {relative}",
                reason_code="ARTIFACT_PATH_ESCAPE",
            )
        if must_exist and not candidate.is_file():
            raise MissingEvidenceError(
                f"artifact is missing: {relative}",
                reason_code="ARTIFACT_MISSING",
            )
        if candidate.is_symlink():
            raise MissingEvidenceError(
                f"symlink artifact forbidden: {relative}",
                reason_code="ARTIFACT_SYMLINK",
            )
        return candidate

    def _atomic_write(self, relative: str | Path, data: bytes) -> Path:
        target = self.contained(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            raise MissingEvidenceError(
                f"artifact overwrite forbidden: {relative}",
                reason_code="ARTIFACT_OVERWRITE",
            )
        self._counter += 1
        temporary = target.with_name(f".{target.name}.m00-tmp-{self._counter:06d}")
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        except OSError as exc:
            raise MissingEvidenceError(
                f"atomic artifact write failed for {relative}: {exc}",
                reason_code="ARTIFACT_WRITE_FAILED",
            ) from exc
        return target

    def write_bytes(self, relative: str | Path, data: bytes) -> Path:
        return self._atomic_write(relative, data)

    def write_text(self, relative: str | Path, text: str) -> Path:
        return self._atomic_write(relative, text.encode("utf-8"))

    def write_json(self, relative: str | Path, value: Any) -> Path:
        return self._atomic_write(relative, canonical_json_bytes(value) + b"\n")

    def copy_file(self, source: str | Path, relative: str | Path) -> Path:
        source = Path(source)
        if source.is_symlink() or not source.is_file():
            raise MissingEvidenceError(
                f"contract source missing or symlinked: {source}",
                reason_code="CONTRACT_ARTIFACT_MISSING",
            )
        return self._atomic_write(relative, source.read_bytes())

    def ensure_required(self, *, include_checksums: bool = True) -> None:
        layout = ArtifactLayout()
        required = layout.required_files if include_checksums else tuple(
            item for item in layout.required_files if item != layout.checksums
        )
        missing = [item for item in required
                   if not self.contained(item).is_file()]
        try:
            generated_input_inventory(self.root)
        except MissingEvidenceError as exc:
            missing.append(
                f"generated-input inventory: {exc.human_message}"
            )
        stdout = list(self.root.joinpath("subprocess").glob("invocation-*.stdout.jsonl"))
        stderr = list(self.root.joinpath("subprocess").glob("invocation-*.stderr.txt"))
        if not stdout:
            missing.append("subprocess/invocation-<NNNN>.stdout.jsonl")
        if len(stdout) != len(stderr):
            missing.append("paired subprocess stderr")
        if missing:
            raise MissingEvidenceError(
                f"required artifact set incomplete: {sorted(missing)}",
                reason_code="REQUIRED_ARTIFACT_MISSING",
            )


class ChecksumManifest:
    filename = "checksums.sha256"

    @staticmethod
    def _files(root: Path) -> dict[str, Path]:
        result = {}
        if root.is_symlink() or not root.is_dir():
            raise MissingEvidenceError(
                f"bundle root missing or symlinked: {root}",
                reason_code="ARTIFACT_ROOT_INVALID",
            )
        for path in root.rglob("*"):
            if path.is_symlink():
                raise MissingEvidenceError(
                    f"symlink forbidden in bundle: {path}",
                    reason_code="ARTIFACT_SYMLINK",
                )
            if path.is_file():
                relative = path.relative_to(root).as_posix()
                if relative != ChecksumManifest.filename:
                    result[relative] = path
        return result

    @classmethod
    def write(cls, root: str | Path) -> str:
        root = Path(root)
        target = root / cls.filename
        if target.exists() or target.is_symlink():
            raise MissingEvidenceError(
                "checksum manifest overwrite forbidden",
                reason_code="CHECKSUM_MANIFEST_EXISTS",
            )
        files = cls._files(root)
        lines = [f"{sha256_file(files[name])}  {name}\n"
                 for name in sorted(files)]
        with target.open("x", encoding="utf-8") as stream:
            stream.writelines(lines)
            stream.flush()
            os.fsync(stream.fileno())
        return sha256_file(target)

    @classmethod
    def verify(cls, root: str | Path) -> dict[str, str]:
        root = Path(root)
        target = root / cls.filename
        if target.is_symlink() or not target.is_file():
            raise MissingEvidenceError(
                "checksum manifest missing",
                reason_code="CHECKSUM_MANIFEST_MISSING",
            )
        entries = {}
        try:
            for line_number, line in enumerate(
                    target.read_text(encoding="utf-8").splitlines(), 1):
                parts = line.split("  ", 1)
                if len(parts) != 2 or len(parts[0]) != 64:
                    raise ValueError(f"malformed line {line_number}")
                digest, relative = parts
                if relative in entries or Path(relative).is_absolute() or \
                        ".." in Path(relative).parts:
                    raise ValueError(f"invalid path on line {line_number}")
                entries[relative] = digest
        except (OSError, ValueError) as exc:
            raise MissingEvidenceError(
                f"invalid checksum manifest: {exc}",
                reason_code="CHECKSUM_MANIFEST_INVALID",
            ) from exc
        files = cls._files(root)
        if set(entries) != set(files):
            raise MissingEvidenceError(
                "checksum coverage differs from regular artifact set",
                reason_code="CHECKSUM_COVERAGE_MISMATCH",
            )
        for relative, path in files.items():
            if sha256_file(path) != entries[relative]:
                raise MissingEvidenceError(
                    f"checksum mismatch: {relative}",
                    reason_code="CHECKSUM_MISMATCH",
                )
        return entries


def capture_environment(*, cwd: str | Path, argv: list[str],
                        contract_sha256: str, revision_sha256: str) -> dict[str, Any]:
    packages = {}
    for package in ("numpy", "joblib", "PyYAML", "jsonschema", "pandas"):
        try:
            packages[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            packages[package] = "not-installed"
    return {
        "schema_version": "1.0",
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "packages": packages,
        "cwd": os.fspath(Path(cwd).resolve()),
        "argv": list(argv),
        "contract_sha256": contract_sha256,
        "revision_sha256": revision_sha256,
        "gpu_probed": False,
        "rocm_probed": False,
        "environment_variables_captured": False,
    }
