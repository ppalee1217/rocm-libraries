# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Hash-bound adapter for the real pinned S10R3 native helper."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .conformance import compare_native_transcript
from .contract import sha256_file, strict_load_json


class NativeAdapterError(ValueError):
    """Native execution was unadmitted, substituted, malformed, or unsuccessful."""


@dataclass(frozen=True)
class NativeBinding:
    binary_path: str
    binary_sha256: str
    cpp_source_path: str
    cpp_source_sha256: str
    host_adapter_path: str
    host_adapter_sha256: str
    formocast_source_blob: str
    formocast_header_blob: str
    runtime_source_blob: str
    runtime_header_blob: str
    symbol: str = "s10r3_native::evaluate_formocast_all_solutions_cohort"


class PinnedNativeFormocastRuntimeAdapter:
    def __init__(
        self,
        binding: NativeBinding,
        *,
        repository_root: Path | str,
        timeout_seconds: int = 120,
    ):
        self.binding = binding
        self.repository_root = Path(repository_root).resolve()
        self.timeout_seconds = timeout_seconds

    def validate_binding(self, lock: Mapping[str, Any]) -> None:
        binary = self.repository_root / self.binding.binary_path
        cpp_source = self.repository_root / self.binding.cpp_source_path
        host_adapter = self.repository_root / self.binding.host_adapter_path
        for path, expected, label in (
            (binary, self.binding.binary_sha256, "native binary"),
            (cpp_source, self.binding.cpp_source_sha256, "native C++ source"),
            (host_adapter, self.binding.host_adapter_sha256, "host adapter"),
        ):
            if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
                raise NativeAdapterError(f"{label} binding mismatch")
        native_record = lock["runtime_binding"]["native_binary"]
        if (
            native_record["path"] != self.binding.binary_path
            or native_record["sha256"] != self.binding.binary_sha256
        ):
            raise NativeAdapterError("effective-lock native binary mismatch")
        identities = {
            item["id"]: item["identity"]
            for item in lock["input_binding"]["source_and_yaml_identities"]
        }
        expected = {
            "native_formocast_source_blob": self.binding.formocast_source_blob,
            "native_formocast_header_blob": self.binding.formocast_header_blob,
            "runtime_queue_source_blob": self.binding.runtime_source_blob,
            "runtime_queue_header_blob": self.binding.runtime_header_blob,
        }
        if any(identities.get(key) != value for key, value in expected.items()):
            raise NativeAdapterError("pinned native/runtime source identity mismatch")

    def invoke(
        self,
        *,
        lock: Mapping[str, Any],
        fixture: Mapping[str, Any],
        input_path: Path | str,
        output_path: Path | str,
        locked_ready: bool,
    ) -> dict[str, Any]:
        if locked_ready is not True:
            raise NativeAdapterError("real native helper is forbidden before LOCKED_READY")
        self.validate_binding(lock)
        binary = self.repository_root / self.binding.binary_path
        input_target = Path(input_path)
        output_target = Path(output_path)
        if not input_target.is_file():
            raise NativeAdapterError("native helper input is absent")
        if output_target.exists():
            raise NativeAdapterError("native helper output must be absent")
        completed = subprocess.run(
            [str(binary), "--input", str(input_target), "--output", str(output_target)],
            cwd=self.repository_root,
            env={
                "LC_ALL": "C",
                "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
                "PATH": "/opt/rocm/bin:/opt/venv/bin:/usr/bin:/bin",
                "PYTHONHASHSEED": "0",
            },
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise NativeAdapterError(
                "native helper failed: "
                + completed.stderr.decode("utf-8", errors="replace")[-1000:]
            )
        transcript = strict_load_json(output_target)
        if transcript.get("symbol") != self.binding.symbol:
            raise NativeAdapterError("native transcript symbol mismatch")
        compare_native_transcript(fixture, transcript)
        from .contract import canonical_sha256

        return {
            "transcript": transcript,
            "argv": [
                str(binary),
                "--input",
                str(input_target),
                "--output",
                str(output_target),
            ],
            "stdout_sha256": canonical_sha256(
                completed.stdout.decode("utf-8", errors="replace")
            ),
            "stderr_sha256": canonical_sha256(
                completed.stderr.decode("utf-8", errors="replace")
            ),
            "stdout_text": completed.stdout.decode("utf-8", errors="strict"),
            "stderr_text": completed.stderr.decode("utf-8", errors="strict"),
        }
