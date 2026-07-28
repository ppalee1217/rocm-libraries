"""Fail-closed host binding for the pinned native Formocast/runtime helper."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from Tensile.ductile.evidence import canonical_sha256, sha256_file, strict_load_json


class NativeAdapterError(ValueError):
    """Native helper binding, invocation, or transcript failure."""


@dataclass(frozen=True)
class NativeBinding:
    helper_path: str
    helper_sha256: str
    helper_source_sha256: str
    host_adapter_sha256: str
    formocast_source_blob: str
    formocast_header_blob: str
    solution_iterator_source_blob: str
    solution_iterator_header_blob: str
    symbol: str


class PinnedNativeFormocastRuntimeAdapter:
    """The only allowed host-side path to the S10R2 native cohort helper."""

    SYMBOL = "s10r2_native::evaluate_formocast_all_solutions_cohort"

    def __init__(self, binding: NativeBinding):
        self.binding = binding

    def verify_binding(
        self,
        *,
        expected: Mapping[str, Any],
        helper_source_path: Path | str,
        host_adapter_path: Path | str,
    ) -> None:
        actual = {
            "helper_sha256": sha256_file(self.binding.helper_path),
            "helper_source_sha256": sha256_file(helper_source_path),
            "host_adapter_sha256": sha256_file(host_adapter_path),
            "formocast_source_blob": self.binding.formocast_source_blob,
            "formocast_header_blob": self.binding.formocast_header_blob,
            "solution_iterator_source_blob": self.binding.solution_iterator_source_blob,
            "solution_iterator_header_blob": self.binding.solution_iterator_header_blob,
            "symbol": self.binding.symbol,
        }
        if self.binding.helper_sha256 != actual["helper_sha256"]:
            raise NativeAdapterError("native helper binary hash mismatch")
        if self.binding.helper_source_sha256 != actual["helper_source_sha256"]:
            raise NativeAdapterError("native helper source hash mismatch")
        if self.binding.host_adapter_sha256 != actual["host_adapter_sha256"]:
            raise NativeAdapterError("host adapter source hash mismatch")
        mismatches = {
            key: (expected.get(key), value)
            for key, value in actual.items()
            if expected.get(key) != value
        }
        if mismatches:
            raise NativeAdapterError(f"native binding mismatch: {mismatches}")
        if self.binding.symbol != self.SYMBOL:
            raise NativeAdapterError("unexpected native helper symbol")

    def evaluate_cohort(
        self,
        *,
        input_path: Path | str,
        output_path: Path | str,
        expected_binding: Mapping[str, Any],
        helper_source_path: Path | str,
        host_adapter_path: Path | str,
        cwd: Path | str,
    ) -> dict[str, Any]:
        self.verify_binding(
            expected=expected_binding,
            helper_source_path=helper_source_path,
            host_adapter_path=host_adapter_path,
        )
        command = [
            str(Path(self.binding.helper_path).resolve()),
            "--input",
            str(Path(input_path).resolve()),
            "--output",
            str(Path(output_path).resolve()),
        ]
        if Path(output_path).exists():
            raise NativeAdapterError("native transcript output must be absent")
        environment = {
            "PATH": "/opt/rocm/bin:/usr/bin:/bin",
            "LD_LIBRARY_PATH": "/opt/rocm/lib:/opt/rocm/lib64",
            "LC_ALL": "C",
        }
        completed = subprocess.run(
            command,
            cwd=Path(cwd),
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            timeout=300,
        )
        if completed.returncode != 0:
            raise NativeAdapterError(
                f"native helper failed closed: rc={completed.returncode}, "
                f"stderr_sha256={canonical_sha256(completed.stderr.decode('utf-8', 'replace'))}"
            )
        output = strict_load_json(output_path)
        if not isinstance(output, Mapping):
            raise NativeAdapterError("native helper output must be a JSON object")
        if output.get("symbol") != self.SYMBOL or output.get("status") != "PASS":
            raise NativeAdapterError("native helper transcript failed validation")
        return dict(output)
