# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Deterministic, resumable S11 global and conditional chunk sampling.

The sampler deliberately stops at the raw configuration boundary.  A caller
must supply the frozen validator adapter; this module never imports historical
S10 runners or artifacts.  Chunk seeds depend only on the sealed nonce,
stream, and chunk index, so worker scheduling cannot change a slot.
"""

from __future__ import annotations

import base64
import hashlib
import math
import os
import selectors
import stat
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np

from .canonical import (
    canonical_json_bytes,
    canonical_sha256,
    exclusive_write_json,
    sha256_file,
    strict_json_loads,
)


class SamplingError(ValueError):
    """Sampling state, registry data, or validator output is invalid."""


class SlotDisposition(str, Enum):
    ACCEPTED = "accepted"
    VALIDATOR_REJECTED = "validator_rejected"
    VALIDATOR_EXCEPTION = "validator_exception"
    MALFORMED_RESULT = "malformed_validator_result"


@dataclass(frozen=True)
class StreamSpec:
    stream_id: str
    target_accepted: int
    hard_cap_chunks: int
    nominal_slots_per_chunk: int = 512
    fixed_gene: str | None = None
    fixed_candidate_id: str | None = None

    def validate(self) -> None:
        if not self.stream_id or type(self.stream_id) is not str:
            raise SamplingError("stream_id must be a nonempty string")
        for value, label in (
            (self.target_accepted, "target_accepted"),
            (self.hard_cap_chunks, "hard_cap_chunks"),
            (self.nominal_slots_per_chunk, "nominal_slots_per_chunk"),
        ):
            if type(value) is not int or value <= 0:
                raise SamplingError(f"{label} must be a positive integer")
        if (self.fixed_gene is None) != (self.fixed_candidate_id is None):
            raise SamplingError("conditional fixed gene and candidate must be paired")


Validator = Callable[[Mapping[str, Any]], bool]

PERSISTENT_VALIDATOR_PROTOCOL = "s11_validator_session_v2"
SYNTHETIC_VALIDATOR_PROTOCOL = "s11_validator_callable_v1"
VALIDATION_CODES = {
    "accepted": 0,
    "validator_rejected": 1,
    "malformed_validator_result": 2,
    "timeout": 3,
    "eof": 4,
    "nonzero_exit": 5,
    "malformed_response": 6,
    "write_failure": 7,
    "validator_exception": 8,
}
VALIDATION_CODE_NAMES = {value: key for key, value in VALIDATION_CODES.items()}
MAX_VALIDATOR_RESPONSE_BYTES = 64 * 1024


def derive_persistent_validator_argv(
    *, executable: Path | str, worker_source_path: Path | str,
    pinned_source_root: Path | str, actual_yaml_path: Path | str,
    compiler_path: Path | str,
) -> list[str]:
    """Return the only formal persistent-validator process argv."""

    return [
        str(Path(executable)), str(Path(worker_source_path).resolve()),
        "--validator-session", "--repository-root",
        str(Path(pinned_source_root).resolve()), "--yaml",
        str(Path(actual_yaml_path).resolve()), "--compiler",
        str(Path(compiler_path)),
    ]


class _ValidatorSession:
    """One process with exactly one in-flight request and matched response."""

    def __init__(self, owner: "PinnedValidatorAdapter"):
        self.owner = owner
        self.process: subprocess.Popen[bytes] | None = None
        self._response_buffer = b""
        self._in_flight = threading.Lock()

    def _start(self) -> None:
        self.process = subprocess.Popen(
            self.owner.argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=self.owner.cwd,
            env=self.owner.environment,
        )
        assert self.process.stdout is not None
        os.set_blocking(self.process.stdout.fileno(), False)
        self._response_buffer = b""
        self.owner.spawn_count += 1

    def close(self) -> None:
        process = self.process
        self.process = None
        if process is None:
            return
        if process.poll() is None:
            process.kill()
        process.wait()

    def _fault(
        self, request_sha256: str, fault_class: str, *,
        response_raw: bytes = b"", response_truncated: bool = False,
    ) -> dict[str, Any]:
        raw_response_sha256 = (
            hashlib.sha256(response_raw).hexdigest() if response_raw else None
        )
        self.close()
        fault_binding = {
            "fault_class": fault_class,
            "request_sha256": request_sha256,
            "raw_response_sha256": raw_response_sha256,
            "raw_response_truncated": response_truncated,
        }
        return {
            "code": VALIDATION_CODES[fault_class],
            "request_sha256": request_sha256,
            "response_sha256": None,
            "fault_digest": canonical_sha256(fault_binding),
            "raw_response_sha256": raw_response_sha256,
            "raw_response_truncated": response_truncated,
        }

    def _read_response(self) -> tuple[str, bytes, bool]:
        """Read one bounded line under the already-started draw deadline."""

        assert self.process is not None and self.process.stdout is not None
        deadline = time.monotonic() + self.owner.timeout_seconds
        selector = selectors.DefaultSelector()
        try:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while True:
                newline = self._response_buffer.find(b"\n")
                if newline >= 0:
                    response = self._response_buffer[: newline + 1]
                    self._response_buffer = self._response_buffer[newline + 1 :]
                    return "line", response, False
                if len(self._response_buffer) > MAX_VALIDATOR_RESPONSE_BYTES:
                    return (
                        "malformed_response",
                        self._response_buffer[:MAX_VALIDATOR_RESPONSE_BYTES],
                        True,
                    )
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return "timeout", self._response_buffer, False
                if not selector.select(remaining):
                    return "timeout", self._response_buffer, False
                try:
                    incoming = os.read(
                        self.process.stdout.fileno(),
                        min(
                            4096,
                            MAX_VALIDATOR_RESPONSE_BYTES + 1
                            - len(self._response_buffer),
                        ),
                    )
                except BlockingIOError:
                    continue
                if not incoming:
                    return "eof", self._response_buffer, False
                self._response_buffer += incoming
        finally:
            selector.close()

    def exchange(
        self, raw: Mapping[str, Any], request_context: Mapping[str, Any]
    ) -> dict[str, Any]:
        if not self._in_flight.acquire(blocking=False):
            raise SamplingError("validator session already has an in-flight request")
        try:
            return self._exchange(raw, request_context)
        finally:
            self._in_flight.release()

    def _exchange(
        self, raw: Mapping[str, Any], request_context: Mapping[str, Any]
    ) -> dict[str, Any]:
        if self.process is None or self.process.poll() is not None:
            self.close()
            self._start()
        assert self.process is not None
        assert self.process.stdin is not None and self.process.stdout is not None
        request = {
            "protocol": self.owner.protocol,
            "stream_id": request_context.get("stream_id"),
            "chunk_index": request_context.get("chunk_index"),
            "slot_index": request_context.get("slot_index"),
            "raw_configuration": dict(raw),
        }
        if (
            type(request["stream_id"]) is not str
            or type(request["chunk_index"]) is not int
            or type(request["slot_index"]) is not int
        ):
            raise SamplingError("persistent validator request context is malformed")
        request_sha256 = canonical_sha256(request)
        try:
            self.process.stdin.write(canonical_json_bytes(request) + b"\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            return self._fault(request_sha256, "write_failure")

        # The per-draw timeout starts only after the canonical request has been
        # dispatched and flushed.  No second request can enter this session.
        status, response_raw, response_truncated = self._read_response()
        if status == "timeout":
            return self._fault(
                request_sha256, "timeout", response_raw=response_raw,
                response_truncated=response_truncated,
            )
        if status == "eof":
            return self._fault(
                request_sha256,
                "nonzero_exit" if self.process.poll() not in (None, 0) else "eof",
                response_raw=response_raw,
                response_truncated=response_truncated,
            )
        if status == "malformed_response":
            return self._fault(
                request_sha256, "malformed_response", response_raw=response_raw,
                response_truncated=response_truncated,
            )
        try:
            response = strict_json_loads(response_raw)
        except Exception:
            return self._fault(
                request_sha256, "malformed_response", response_raw=response_raw,
                response_truncated=response_truncated,
            )
        if (
            type(response) is not dict
            or set(response) != {"protocol", "request_sha256", "accepted", "provenance"}
            or response.get("protocol") != self.owner.protocol
            or response.get("request_sha256") != request_sha256
            or type(response.get("accepted")) is not bool
            or response.get("provenance") != self.owner.provenance
        ):
            return self._fault(
                request_sha256, "malformed_response", response_raw=response_raw,
                response_truncated=response_truncated,
            )
        return {
            "code": VALIDATION_CODES[
                "accepted" if response["accepted"] else "validator_rejected"
            ],
            "request_sha256": request_sha256,
            "response_sha256": canonical_sha256(response),
            "fault_digest": None,
            "raw_response_sha256": None,
            "raw_response_truncated": False,
        }


class PinnedValidatorAdapter:
    """Bounded persistent pool for the frozen actual valid_fn/IndividualSet path."""

    def __init__(
        self,
        executable: Path | str,
        *,
        executable_sha256: str,
        validator_source_path: Path | str,
        validator_source_sha256: str,
        timeout_seconds: int,
        protocol: str,
        worker_count: int,
        argv: Sequence[str],
        cwd: Path | str,
        tmpdir: Path | str | None = None,
        pythonpycacheprefix: Path | str | None = None,
    ):
        self.executable_launcher = Path(executable)
        self.executable = self.executable_launcher.resolve()
        self.validator_source_path = Path(validator_source_path).resolve()
        self.executable_sha256 = executable_sha256
        self.validator_source_sha256 = validator_source_sha256
        self.timeout_seconds = timeout_seconds
        self.protocol = protocol
        self.worker_count = worker_count
        self.argv = list(argv)
        self.cwd = Path(cwd).resolve()
        self.tmpdir = Path(tmpdir if tmpdir is not None else cwd).resolve()
        self.pythonpycacheprefix = Path(
            pythonpycacheprefix if pythonpycacheprefix is not None else cwd
        ).resolve()
        self.spawn_count = 0
        info = self.executable.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or not os.access(self.executable, os.X_OK)
            or sha256_file(self.executable) != executable_sha256
        ):
            raise SamplingError("validator executable identity/mode mismatch")
        source_info = self.validator_source_path.lstat()
        if (
            not stat.S_ISREG(source_info.st_mode)
            or self.validator_source_path.is_symlink()
            or sha256_file(self.validator_source_path) != validator_source_sha256
        ):
            raise SamplingError("validator source identity/mode mismatch")
        if type(timeout_seconds) is not int or timeout_seconds <= 0:
            raise SamplingError("validator timeout must be positive")
        if protocol != PERSISTENT_VALIDATOR_PROTOCOL:
            raise SamplingError("persistent validator protocol identity mismatch")
        if type(worker_count) is not int or not 1 <= worker_count <= 64:
            raise SamplingError("persistent validator worker count is outside the bound")
        if not self.cwd.is_dir() or self.cwd.is_symlink():
            raise SamplingError("persistent validator cwd is unavailable")
        if (
            not self.tmpdir.is_dir()
            or self.tmpdir.is_symlink()
            or not self.pythonpycacheprefix.is_dir()
            or self.pythonpycacheprefix.is_symlink()
        ):
            raise SamplingError("persistent validator temp/cache root is unavailable")
        if not self.argv or Path(self.argv[0]).resolve() != self.executable:
            raise SamplingError("persistent validator argv/executable binding mismatch")
        if any(type(item) is not str or not item for item in self.argv):
            raise SamplingError("persistent validator argv is malformed")
        self.provenance = {
            "executable_sha256": self.executable_sha256,
            "validator_source_sha256": self.validator_source_sha256,
            "normal_valid_fn_path": True,
            "valid_fn": "Tensile.backends.ductile_backend._validate_solution",
            "proxy_or_substitution": False,
            "session_protocol": self.protocol,
        }
        self.environment = {
            "PATH": f"{self.executable.parent}:/usr/bin:/bin",
            "LC_ALL": "C",
            "PYTHONNOUSERSITE": "1",
            "PYTHONPATH": "",
            "TMPDIR": str(self.tmpdir),
            "PYTHONPYCACHEPREFIX": str(self.pythonpycacheprefix),
            "Tensile_ASM_COMPILER_LAUNCHER": "",
        }
        self._sessions = [_ValidatorSession(self) for _ in range(worker_count)]

    def __call__(self, raw: Mapping[str, Any]) -> bool:
        result = self._sessions[0].exchange(
            raw, {"stream_id": "direct", "chunk_index": 0, "slot_index": 0}
        )
        if result["code"] >= VALIDATION_CODES["timeout"]:
            raise SamplingError("persistent validator session failed")
        return result["code"] == VALIDATION_CODES["accepted"]

    def validate_many(
        self, raws: Sequence[Mapping[str, Any]],
        request_contexts: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Dispatch concurrently while returning one exact input-ordered vector."""

        if len(request_contexts) != len(raws):
            raise SamplingError("persistent validator request-context count changed")
        results: list[dict[str, Any] | None] = [None] * len(raws)

        def run_session(session_index: int) -> None:
            session = self._sessions[session_index]
            for index in range(session_index, len(raws), self.worker_count):
                results[index] = session.exchange(raws[index], request_contexts[index])

        with ThreadPoolExecutor(max_workers=self.worker_count) as pool:
            list(pool.map(run_session, range(self.worker_count)))
        if any(result is None for result in results):
            raise SamplingError("persistent validator ordered assembly is incomplete")
        return [dict(result) for result in results if result is not None]

    def close(self) -> None:
        for session in self._sessions:
            session.close()

    def __enter__(self) -> "PinnedValidatorAdapter":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()


def derive_uint128(master_nonce: str, domain: str, *parts: object) -> int:
    """Derive one domain-separated PCG64 seed without ambient RNG state."""

    if (
        type(master_nonce) is not str
        or len(master_nonce) != 64
        or any(character not in "0123456789abcdef" for character in master_nonce)
    ):
        raise SamplingError("master nonce must be a lowercase SHA-256-sized hex string")
    if not domain or "\x00" in domain:
        raise SamplingError("seed domain is malformed")
    material = "\x00".join(
        ["S11-PCG64-v1", master_nonce, domain, *(str(part) for part in parts)]
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:16], "big")


def _eligible_gene_table(registry: Mapping[str, Any]) -> list[dict[str, Any]]:
    genes = registry.get("sampling_axes", registry.get("eligible_genes"))
    if type(genes) is not list or not genes:
        raise SamplingError("registry has no eligible genes")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for gene in genes:
        if type(gene) is not dict:
            raise SamplingError("eligible gene row is malformed")
        name = gene.get("gene", gene.get("axis_name"))
        if type(name) is not str:
            raise SamplingError("eligible gene/axis name is malformed")
        ids = gene.get("candidate_ids")
        values = gene.get("candidates")
        probabilities = gene.get("baseline_probabilities")
        if name in seen or not (
            type(ids) is list
            and type(values) is list
            and type(probabilities) is list
            and len(ids) == len(values) == len(probabilities) >= 1
        ):
            raise SamplingError("registry candidate vectors are inconsistent")
        if any(type(probability) is not float or probability <= 0 for probability in probabilities):
            raise SamplingError("baseline probabilities must be positive floats")
        if not math.isclose(sum(probabilities), 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise SamplingError("baseline probabilities must sum to one")
        if len(set(ids)) != len(ids):
            raise SamplingError("candidate IDs contain aliases")
        seen.add(name)
        result.append(gene)
    return result


def _decode_typed(value: Mapping[str, Any]) -> Any:
    """Decode the closed typed-value representation emitted by registry.py."""

    if type(value) is not dict or set(value) != {"type", "value"}:
        raise SamplingError("typed candidate schema is malformed")
    kind, payload = value["type"], value["value"]
    if kind == "null" and payload is None:
        return None
    if kind == "bool" and type(payload) is bool:
        return payload
    if kind == "int" and type(payload) is str:
        return int(payload)
    if kind == "float" and type(payload) is str:
        result = float.fromhex(payload)
        if math.isfinite(result):
            return result
    if kind == "str" and type(payload) is str:
        return payload
    if kind == "list" and type(payload) is list:
        return [_decode_typed(item) for item in payload]
    if kind == "map" and type(payload) is dict:
        return {key: _decode_typed(item) for key, item in payload.items()}
    raise SamplingError("typed candidate payload is invalid")


def _sampling_registry_sha256(registry: Mapping[str, Any]) -> str:
    recorded = registry.get("registry_sha256")
    if type(recorded) is str and len(recorded) == 64:
        return recorded
    return canonical_sha256(_eligible_gene_table(registry))


def _pack_validation_codes(codes: Sequence[int]) -> str:
    if any(type(code) is not int or not 0 <= code <= 15 for code in codes):
        raise SamplingError("validation code is outside the compact nibble codec")
    packed = bytearray((len(codes) + 1) // 2)
    for index, code in enumerate(codes):
        packed[index // 2] |= code << (4 if index % 2 else 0)
    return base64.b64encode(bytes(packed)).decode("ascii")


def _unpack_validation_codes(encoded: str, count: int) -> list[int]:
    try:
        packed = base64.b64decode(encoded.encode("ascii"), validate=True)
    except Exception as error:
        raise SamplingError("compact validation-code base64 is malformed") from error
    if len(packed) != (count + 1) // 2:
        raise SamplingError("compact validation-code length changed")
    codes = [
        (packed[index // 2] >> (4 if index % 2 else 0)) & 0x0F
        for index in range(count)
    ]
    if count % 2 and packed[-1] & 0xF0:
        raise SamplingError("compact validation-code padding is nonzero")
    if any(code not in VALIDATION_CODE_NAMES for code in codes):
        raise SamplingError("compact validation code is unknown")
    return codes


def _axis_choice_widths(genes: Sequence[Mapping[str, Any]]) -> list[int]:
    widths = []
    for gene in genes:
        count = len(gene["candidate_ids"])
        if not 1 <= count <= 65536:
            raise SamplingError("axis cardinality is outside the uint16 codec bound")
        widths.append(1 if count <= 256 else 2)
    return widths


def _pack_candidate_choices(
    choices: Sequence[int], widths: Sequence[int]
) -> str:
    if not widths or len(choices) % len(widths):
        raise SamplingError("candidate choices do not align to the axis-width vector")
    packed = bytearray()
    for index, choice in enumerate(choices):
        width = widths[index % len(widths)]
        if type(choice) is not int or not 0 <= choice < 1 << (8 * width):
            raise SamplingError("candidate choice does not fit its axis width")
        packed.extend(choice.to_bytes(width, "big"))
    return base64.b64encode(bytes(packed)).decode("ascii")


def _unpack_candidate_choices(
    encoded: str, *, widths: Sequence[int], slots: int,
) -> list[int]:
    try:
        packed = base64.b64decode(encoded.encode("ascii"), validate=True)
    except Exception as error:
        raise SamplingError("compact candidate-choice base64 is malformed") from error
    if len(packed) != slots * sum(widths):
        raise SamplingError("compact candidate-choice length changed")
    choices = []
    cursor = 0
    for _ in range(slots):
        for width in widths:
            choices.append(int.from_bytes(packed[cursor : cursor + width], "big"))
            cursor += width
    return choices


def _pack_flags(flags: Sequence[bool]) -> str:
    packed = bytearray((len(flags) + 7) // 8)
    for index, flag in enumerate(flags):
        if type(flag) is not bool:
            raise SamplingError("compact flag vector contains a non-boolean")
        if flag:
            packed[index // 8] |= 1 << (index % 8)
    return base64.b64encode(bytes(packed)).decode("ascii")


def _unpack_flags(encoded: str, count: int) -> list[bool]:
    try:
        packed = base64.b64decode(encoded.encode("ascii"), validate=True)
    except Exception as error:
        raise SamplingError("compact flag-vector base64 is malformed") from error
    if len(packed) != (count + 7) // 8:
        raise SamplingError("compact flag-vector length changed")
    if count % 8 and packed and packed[-1] >> (count % 8):
        raise SamplingError("compact flag-vector padding is nonzero")
    return [bool(packed[index // 8] & (1 << (index % 8))) for index in range(count)]


def _validator_results(
    validator: Validator, raws: Sequence[Mapping[str, Any]],
    request_contexts: Sequence[Mapping[str, Any]],
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    validate_many = getattr(validator, "validate_many", None)
    if callable(validate_many):
        protocol = getattr(validator, "protocol", None)
        provenance = getattr(validator, "provenance", None)
        if protocol != PERSISTENT_VALIDATOR_PROTOCOL or type(provenance) is not dict:
            raise SamplingError("persistent validator binding is incomplete")
        results = validate_many(raws, request_contexts)
        if type(results) is not list or len(results) != len(raws):
            raise SamplingError("persistent validator result count/order changed")
        return protocol, dict(provenance), results

    protocol = SYNTHETIC_VALIDATOR_PROTOCOL
    provenance = {
        "synthetic_callable": True,
        "normal_valid_fn_path": False,
        "proxy_or_substitution": False,
    }
    results = []
    for raw, request_context in zip(raws, request_contexts, strict=True):
        request = {
            "protocol": protocol,
            "stream_id": request_context["stream_id"],
            "chunk_index": request_context["chunk_index"],
            "slot_index": request_context["slot_index"],
            "raw_configuration": dict(raw),
        }
        request_sha256 = canonical_sha256(request)
        try:
            accepted = validator(raw)
            if type(accepted) is not bool:
                results.append(
                    {
                        "code": VALIDATION_CODES["malformed_validator_result"],
                        "request_sha256": request_sha256,
                        "response_sha256": None,
                        "fault_digest": canonical_sha256(
                            {
                                "fault_class": "malformed_validator_result",
                                "request_sha256": request_sha256,
                                "raw_response_sha256": None,
                                "raw_response_truncated": False,
                            }
                        ),
                        "raw_response_sha256": None,
                        "raw_response_truncated": False,
                    }
                )
                continue
            response = {
                "protocol": protocol,
                "request_sha256": request_sha256,
                "accepted": accepted,
                "provenance": provenance,
            }
            results.append(
                {
                    "code": VALIDATION_CODES[
                        "accepted" if accepted else "validator_rejected"
                    ],
                    "request_sha256": request_sha256,
                    "response_sha256": canonical_sha256(response),
                    "fault_digest": None,
                    "raw_response_sha256": None,
                    "raw_response_truncated": False,
                }
            )
        except Exception:
            results.append(
                {
                    "code": VALIDATION_CODES["validator_exception"],
                    "request_sha256": request_sha256,
                    "response_sha256": None,
                    "fault_digest": canonical_sha256(
                        {
                            "fault_class": "validator_exception",
                            "request_sha256": request_sha256,
                            "raw_response_sha256": None,
                            "raw_response_truncated": False,
                        }
                    ),
                    "raw_response_sha256": None,
                    "raw_response_truncated": False,
                }
            )
    return protocol, provenance, results


def _expanded_disposition(code: int) -> str:
    if code == VALIDATION_CODES["accepted"]:
        return SlotDisposition.ACCEPTED.value
    if code == VALIDATION_CODES["validator_rejected"]:
        return SlotDisposition.VALIDATOR_REJECTED.value
    if code == VALIDATION_CODES["malformed_validator_result"]:
        return SlotDisposition.MALFORMED_RESULT.value
    return SlotDisposition.VALIDATOR_EXCEPTION.value


def sample_chunk(
    registry: Mapping[str, Any],
    spec: StreamSpec,
    *,
    master_nonce: str,
    chunk_index: int,
    validator: Validator,
    lock_sha256: str = "0" * 64,
) -> dict[str, Any]:
    """Sample one chunk and encode its complete semantics without raw duplication."""

    spec.validate()
    if type(chunk_index) is not int or not 0 <= chunk_index < spec.hard_cap_chunks:
        raise SamplingError("chunk index is outside the frozen stream cap")
    genes = _eligible_gene_table(registry)
    choice_widths = _axis_choice_widths(genes)
    by_name = {gene.get("gene", gene.get("axis_name")): gene for gene in genes}
    if spec.fixed_gene is not None:
        if spec.fixed_gene not in by_name:
            raise SamplingError("conditional stream gene is not in the registry")
        if spec.fixed_candidate_id not in by_name[spec.fixed_gene]["candidate_ids"]:
            raise SamplingError("conditional candidate is not in the frozen order")

    rng = np.random.Generator(
        np.random.PCG64(derive_uint128(master_nonce, "discovery-chunk", spec.stream_id, chunk_index))
    )
    choices: list[int] = []
    raws: list[dict[str, Any]] = []
    for slot_index in range(spec.nominal_slots_per_chunk):
        raw: dict[str, Any] = {}
        for gene in genes:
            name = gene.get("gene", gene.get("axis_name"))
            if name == spec.fixed_gene:
                choice = gene["candidate_ids"].index(spec.fixed_candidate_id)
            else:
                choice = int(rng.choice(len(gene["candidate_ids"]), p=gene["baseline_probabilities"]))
            width = choice_widths[len(choices) % len(choice_widths)]
            if not 0 <= choice < 1 << (8 * width):
                raise SamplingError("candidate choice does not fit its axis codec")
            choices.append(choice)
            decoded = _decode_typed(gene["candidates"][choice])
            if gene.get("axis_kind") == "protected_group":
                if type(decoded) is not dict:
                    raise SamplingError("protected group candidate is not a mapping")
                raw.update(decoded)
            else:
                raw[name] = decoded
        raws.append(raw)
    request_contexts = [
        {
            "stream_id": spec.stream_id,
            "chunk_index": chunk_index,
            "slot_index": slot_index,
        }
        for slot_index in range(spec.nominal_slots_per_chunk)
    ]
    protocol, provenance, results = _validator_results(
        validator, raws, request_contexts
    )
    codes = [row["code"] for row in results]
    binding_rows = [
        {
            "request_sha256": row["request_sha256"],
            "response_sha256": row["response_sha256"],
            "fault_digest": row["fault_digest"],
        }
        for row in results
    ]
    fault_results = [row for row in results if row["fault_digest"] is not None]
    fault_response_present = [
        row["raw_response_sha256"] is not None for row in fault_results
    ]
    fault_response_digest_bytes = b"".join(
        bytes.fromhex(row["raw_response_sha256"])
        if row["raw_response_sha256"] is not None else bytes(32)
        for row in fault_results
    )
    fault_response_truncated = [
        row["raw_response_truncated"] for row in fault_results
    ]
    counts = {disposition.value: 0 for disposition in SlotDisposition}
    for code in codes:
        counts[_expanded_disposition(code)] += 1
    body = {
        "document_kind": "s11_compact_sampling_chunk",
        "schema_version": 3,
        "checkpoint_id": "S11",
        "lock_sha256": lock_sha256,
        "registry_sha256": _sampling_registry_sha256(registry),
        "seed_identity_sha256": canonical_sha256({"master_nonce": master_nonce}),
        "stream_id": spec.stream_id,
        "chunk_index": chunk_index,
        "nominal_slots": spec.nominal_slots_per_chunk,
        "seed_uint128_hex": f"{derive_uint128(master_nonce, 'discovery-chunk', spec.stream_id, chunk_index):032x}",
        "fixed_gene": spec.fixed_gene,
        "fixed_candidate_id": spec.fixed_candidate_id,
        "axis_order": [gene.get("gene", gene.get("axis_name")) for gene in genes],
        "choice_codec": "axis-uint8-or-uint16-be-slot-major-base64-v1",
        "axis_choice_width_bytes": choice_widths,
        "candidate_choice_bytes_b64": _pack_candidate_choices(
            choices, choice_widths
        ),
        "validation_codec": "nibble-slot-major-base64-v1",
        "validation_codes_b64": _pack_validation_codes(codes),
        "validator_protocol": protocol,
        "validator_provenance": provenance,
        "slot_binding_rule": "canonical-context-request-response-or-fault-sha256-v2",
        "slot_bindings_sha256": canonical_sha256(binding_rows),
        "fault_response_codec": "fault-slot-ordered-sha256-and-bitflags-base64-v1",
        "fault_response_digest_bytes_b64": base64.b64encode(
            fault_response_digest_bytes
        ).decode("ascii"),
        "fault_response_present_bits_b64": _pack_flags(fault_response_present),
        "fault_response_truncated_bits_b64": _pack_flags(
            fault_response_truncated
        ),
        "counts": counts,
    }
    provisional = {**body, "chunk_semantic_sha256": ""}
    semantic = expand_compact_chunk(
        {**provisional, "chunk_sha256": canonical_sha256(provisional)},
        registry=registry, spec=spec, master_nonce=master_nonce,
        expected_lock_sha256=lock_sha256, verify_semantic_digest=False,
    )
    body["chunk_semantic_sha256"] = semantic["chunk_sha256"]
    return {**body, "chunk_sha256": canonical_sha256(body)}


def expand_compact_chunk(
    chunk: Mapping[str, Any], *, registry: Mapping[str, Any], spec: StreamSpec,
    master_nonce: str, expected_lock_sha256: str,
    verify_semantic_digest: bool = True,
) -> dict[str, Any]:
    """Mechanically rebuild every raw/candidate/occurrence/response slot."""

    expected_keys = {
        "document_kind", "schema_version", "checkpoint_id", "lock_sha256",
        "registry_sha256", "seed_identity_sha256", "stream_id", "chunk_index",
        "nominal_slots", "seed_uint128_hex", "fixed_gene", "fixed_candidate_id",
        "axis_order", "choice_codec", "candidate_choice_bytes_b64",
        "axis_choice_width_bytes",
        "validation_codec", "validation_codes_b64", "validator_protocol",
        "validator_provenance", "slot_binding_rule", "slot_bindings_sha256",
        "fault_response_codec", "fault_response_digest_bytes_b64",
        "fault_response_present_bits_b64", "fault_response_truncated_bits_b64",
        "counts", "chunk_semantic_sha256",
        "chunk_sha256",
    }
    if type(chunk) is not dict or set(chunk) != expected_keys:
        raise SamplingError("compact chunk schema/unknown-property failure")
    body = dict(chunk)
    recorded = body.pop("chunk_sha256")
    if canonical_sha256(body) != recorded:
        raise SamplingError("compact chunk self-hash mismatch")
    genes = _eligible_gene_table(registry)
    if (
        chunk["document_kind"] != "s11_compact_sampling_chunk"
        or chunk["schema_version"] != 3
        or chunk["checkpoint_id"] != "S11"
        or chunk["lock_sha256"] != expected_lock_sha256
        or chunk["registry_sha256"] != _sampling_registry_sha256(registry)
        or chunk["seed_identity_sha256"]
        != canonical_sha256({"master_nonce": master_nonce})
        or chunk["stream_id"] != spec.stream_id
        or chunk["nominal_slots"] != spec.nominal_slots_per_chunk
        or chunk["fixed_gene"] != spec.fixed_gene
        or chunk["fixed_candidate_id"] != spec.fixed_candidate_id
        or chunk["axis_order"]
        != [gene.get("gene", gene.get("axis_name")) for gene in genes]
        or chunk["choice_codec"]
        != "axis-uint8-or-uint16-be-slot-major-base64-v1"
        or chunk["validation_codec"] != "nibble-slot-major-base64-v1"
        or chunk["slot_binding_rule"]
        != "canonical-context-request-response-or-fault-sha256-v2"
        or chunk["fault_response_codec"]
        != "fault-slot-ordered-sha256-and-bitflags-base64-v1"
    ):
        raise SamplingError("compact chunk identity/spec/codec binding changed")
    index = chunk["chunk_index"]
    if type(index) is not int or not 0 <= index < spec.hard_cap_chunks:
        raise SamplingError("compact chunk index is outside the frozen cap")
    seed = derive_uint128(master_nonce, "discovery-chunk", spec.stream_id, index)
    if chunk["seed_uint128_hex"] != f"{seed:032x}":
        raise SamplingError("compact chunk seed/order binding changed")
    choice_widths = _axis_choice_widths(genes)
    if chunk["axis_choice_width_bytes"] != choice_widths:
        raise SamplingError("compact per-axis candidate width binding changed")
    choice_indices = _unpack_candidate_choices(
        chunk["candidate_choice_bytes_b64"], widths=choice_widths,
        slots=spec.nominal_slots_per_chunk,
    )
    codes = _unpack_validation_codes(
        chunk["validation_codes_b64"], spec.nominal_slots_per_chunk
    )
    rng = np.random.Generator(np.random.PCG64(seed))
    slots = []
    accepted_ids = []
    binding_rows = []
    fault_slots = [
        slot_index
        for slot_index, code in enumerate(codes)
        if code not in (VALIDATION_CODES["accepted"], VALIDATION_CODES["validator_rejected"])
    ]
    fault_count = len(fault_slots)
    try:
        fault_digest_bytes = base64.b64decode(
            chunk["fault_response_digest_bytes_b64"].encode("ascii"), validate=True
        )
    except Exception as error:
        raise SamplingError("compact fault-response digest base64 is malformed") from error
    if len(fault_digest_bytes) != fault_count * 32:
        raise SamplingError("compact fault-response digest vector length changed")
    fault_present = _unpack_flags(
        chunk["fault_response_present_bits_b64"], fault_count
    )
    fault_truncated = _unpack_flags(
        chunk["fault_response_truncated_bits_b64"], fault_count
    )
    fault_by_slot = {}
    for ordinal, slot_index in enumerate(fault_slots):
        raw_digest = fault_digest_bytes[ordinal * 32 : (ordinal + 1) * 32]
        if fault_present[ordinal]:
            raw_response_sha256 = raw_digest.hex()
        else:
            if any(raw_digest):
                raise SamplingError("absent fault response has a nonzero digest payload")
            raw_response_sha256 = None
        if fault_truncated[ordinal] and not fault_present[ordinal]:
            raise SamplingError("truncated fault response is marked absent")
        fault_by_slot[slot_index] = {
            "raw_response_sha256": raw_response_sha256,
            "raw_response_truncated": fault_truncated[ordinal],
        }
    counts = {disposition.value: 0 for disposition in SlotDisposition}
    cursor = 0
    for slot_index in range(spec.nominal_slots_per_chunk):
        raw: dict[str, Any] = {}
        candidate_ids: dict[str, str] = {}
        for gene in genes:
            name = gene.get("gene", gene.get("axis_name"))
            choice = choice_indices[cursor]
            cursor += 1
            expected_choice = (
                gene["candidate_ids"].index(spec.fixed_candidate_id)
                if name == spec.fixed_gene
                else int(rng.choice(
                    len(gene["candidate_ids"]), p=gene["baseline_probabilities"]
                ))
            )
            if choice != expected_choice or choice >= len(gene["candidate_ids"]):
                raise SamplingError("compact candidate choice changed frozen draw order")
            decoded = _decode_typed(gene["candidates"][choice])
            if gene.get("axis_kind") == "protected_group":
                if type(decoded) is not dict:
                    raise SamplingError("protected group candidate is not a mapping")
                raw.update(decoded)
            else:
                raw[name] = decoded
            candidate_ids[name] = gene["candidate_ids"][choice]
        occurrence_body = {
            "stream_id": spec.stream_id,
            "chunk_index": index,
            "slot_index": slot_index,
            "candidate_ids": candidate_ids,
            "raw_configuration": raw,
        }
        occurrence_id = canonical_sha256(occurrence_body)
        disposition = _expanded_disposition(codes[slot_index])
        row = {
            **occurrence_body,
            "occurrence_id": occurrence_id,
            "disposition": disposition,
        }
        slots.append(row)
        counts[disposition] += 1
        if disposition == SlotDisposition.ACCEPTED.value:
            accepted_ids.append(occurrence_id)
        request = {
            "protocol": chunk["validator_protocol"],
            "stream_id": spec.stream_id,
            "chunk_index": index,
            "slot_index": slot_index,
            "raw_configuration": raw,
        }
        request_sha256 = canonical_sha256(request)
        if codes[slot_index] in (
            VALIDATION_CODES["accepted"], VALIDATION_CODES["validator_rejected"]
        ):
            response = {
                "protocol": chunk["validator_protocol"],
                "request_sha256": request_sha256,
                "accepted": codes[slot_index] == VALIDATION_CODES["accepted"],
                "provenance": chunk["validator_provenance"],
            }
            response_sha256 = canonical_sha256(response)
            fault_digest = None
        else:
            response_sha256 = None
            fault = fault_by_slot.get(slot_index)
            if fault is None:
                raise SamplingError("compact fault-response slot binding is missing")
            fault_digest = canonical_sha256(
                {
                    "fault_class": VALIDATION_CODE_NAMES[codes[slot_index]],
                    "request_sha256": request_sha256,
                    "raw_response_sha256": fault["raw_response_sha256"],
                    "raw_response_truncated": fault["raw_response_truncated"],
                }
            )
        binding_rows.append(
            {
                "request_sha256": request_sha256,
                "response_sha256": response_sha256,
                "fault_digest": fault_digest,
            }
        )
    if binding_rows and canonical_sha256(binding_rows) != chunk["slot_bindings_sha256"]:
        raise SamplingError("compact per-slot request/response/fault binding changed")
    if counts != chunk["counts"]:
        raise SamplingError("compact disposition counts changed")
    expanded_body = {
        "document_kind": "s11_sampling_chunk",
        "schema_version": 1,
        "checkpoint_id": "S11",
        "stream_id": spec.stream_id,
        "chunk_index": index,
        "nominal_slots": spec.nominal_slots_per_chunk,
        "seed_uint128_hex": f"{seed:032x}",
        "fixed_gene": spec.fixed_gene,
        "fixed_candidate_id": spec.fixed_candidate_id,
        "counts": counts,
        "slots": slots,
        "accepted_occurrence_ids": accepted_ids,
    }
    semantic = canonical_sha256(expanded_body)
    if verify_semantic_digest and semantic != chunk["chunk_semantic_sha256"]:
        raise SamplingError("compact-versus-expanded semantic digest differs")
    return {**expanded_body, "chunk_sha256": semantic}


def commit_chunk(path: Path | str, chunk: Mapping[str, Any]) -> None:
    """Publish a completed chunk once; caller commits its ledger event next."""

    body = dict(chunk)
    recorded = body.pop("chunk_sha256", None)
    if canonical_sha256(body) != recorded:
        raise SamplingError("chunk digest does not match its payload")
    exclusive_write_json(path, dict(chunk))


def sample_complete_stream(
    registry: Mapping[str, Any],
    spec: StreamSpec,
    *,
    master_nonce: str,
    validator: Validator,
    workers: int = 1,
    first_missing_chunk: int = 0,
) -> list[dict[str, Any]]:
    """Generate every remaining fixed-cap chunk; never stop on acceptance count."""

    spec.validate()
    if type(workers) is not int or workers <= 0:
        raise SamplingError("worker count must be positive")
    if workers != 1 and callable(getattr(validator, "validate_many", None)):
        raise SamplingError(
            "persistent validation parallelism is bound inside the adapter"
        )
    if type(first_missing_chunk) is not int or not 0 <= first_missing_chunk <= spec.hard_cap_chunks:
        raise SamplingError("resume cursor is outside the immutable cap")
    indices = list(range(first_missing_chunk, spec.hard_cap_chunks))

    def generate(index: int) -> dict[str, Any]:
        return sample_chunk(
            registry, spec, master_nonce=master_nonce, chunk_index=index, validator=validator
        )

    if workers == 1:
        return [generate(index) for index in indices]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        chunks = list(pool.map(generate, indices))
    return sorted(chunks, key=lambda chunk: chunk["chunk_index"])


class _CanonicalStringListHasher:
    """Incrementally hash the canonical JSON representation of a string list."""

    def __init__(self) -> None:
        self._hash = hashlib.sha256()
        self._hash.update(b"[")
        self.count = 0

    def add(self, value: str) -> None:
        if type(value) is not str:
            raise SamplingError("occurrence identity is not a string")
        if self.count:
            self._hash.update(b",")
        self._hash.update(canonical_json_bytes(value))
        self.count += 1

    def hexdigest(self) -> str:
        result = self._hash.copy()
        result.update(b"]")
        return result.hexdigest()


class _CanonicalValueListHasher:
    """Incrementally hash a canonical JSON list of closed metadata values."""

    def __init__(self) -> None:
        self._hash = hashlib.sha256(b"[")
        self.count = 0

    def add(self, value: Any) -> None:
        if self.count:
            self._hash.update(b",")
        self._hash.update(canonical_json_bytes(value))
        self.count += 1

    def hexdigest(self) -> str:
        result = self._hash.copy()
        result.update(b"]")
        return result.hexdigest()


def canonical_prefix(
    chunks: Iterable[Any], target_accepted: int, *,
    registry: Mapping[str, Any], spec: StreamSpec, master_nonce: str,
    expected_lock_sha256: str, preexpanded: bool = False,
) -> dict[str, Any]:
    """Stream compact chunks and retain only the exact first-N accepted rows."""

    if type(target_accepted) is not int or target_accepted <= 0:
        raise SamplingError("prefix target must be positive")
    credited_ids: list[str] = []
    credited_rows: list[dict[str, Any]] = []
    acceptance_ledger: list[dict[str, Any]] = []
    zero_credit = _CanonicalStringListHasher()
    full_acceptance_ledger = _CanonicalValueListHasher()
    zero_credit_acceptance_ledger = _CanonicalValueListHasher()
    chunk_hashes = _CanonicalStringListHasher()
    accepted_observed = 0
    chunks_observed = 0
    for index, item in enumerate(chunks):
        if preexpanded:
            if type(item) is not tuple or len(item) != 2:
                raise SamplingError("preexpanded compact chunk pair is malformed")
            compact, chunk = item
        else:
            compact, chunk = item, None
        if type(compact) is not dict:
            raise SamplingError("compact prefix input is not an object")
        if compact.get("chunk_index") != index:
            raise SamplingError("prefix chunks must be contiguous from chunk zero")
        if chunk is None:
            chunk = expand_compact_chunk(
                compact, registry=registry, spec=spec, master_nonce=master_nonce,
                expected_lock_sha256=expected_lock_sha256,
            )
        elif (
            type(chunk) is not dict
            or chunk.get("chunk_index") != index
            or chunk.get("chunk_sha256") != compact.get("chunk_semantic_sha256")
        ):
            raise SamplingError("preexpanded chunk semantic binding changed")
        chunk_hashes.add(compact["chunk_sha256"])
        chunks_observed += 1
        for row in chunk["slots"]:
            if row["disposition"] != SlotDisposition.ACCEPTED.value:
                continue
            occurrence_id = row["occurrence_id"]
            acceptance_index = accepted_observed
            accepted_observed += 1
            if len(credited_ids) < target_accepted:
                acceptance_row = {
                    "acceptance_index": acceptance_index,
                    "occurrence_id": occurrence_id,
                    "canonical_credit": True,
                    "downstream_credit": "full",
                }
                credited_ids.append(occurrence_id)
                credited_rows.append(dict(row))
                acceptance_ledger.append(acceptance_row)
            else:
                acceptance_row = {
                    "acceptance_index": acceptance_index,
                    "occurrence_id": occurrence_id,
                    "canonical_credit": False,
                    "downstream_credit": "zero_diagnostic_only",
                }
                zero_credit.add(occurrence_id)
                zero_credit_acceptance_ledger.add(acceptance_row)
            full_acceptance_ledger.add(acceptance_row)
    return {
        "target_accepted": target_accepted,
        "chunks_observed": chunks_observed,
        "accepted_observed": accepted_observed,
        "accepted_credited": len(credited_ids),
        "overshoot_diagnostic": zero_credit.count,
        "complete": len(credited_ids) == target_accepted,
        "credited_occurrence_ids": credited_ids,
        "credited_rows": credited_rows,
        "acceptance_ledger": acceptance_ledger,
        "acceptance_ledger_count": full_acceptance_ledger.count,
        "acceptance_ledger_sha256": full_acceptance_ledger.hexdigest(),
        "zero_credit_occurrence_count": zero_credit.count,
        "zero_credit_occurrence_ids_sha256": zero_credit.hexdigest(),
        "zero_credit_acceptance_ledger_count": zero_credit_acceptance_ledger.count,
        "zero_credit_acceptance_ledger_sha256": (
            zero_credit_acceptance_ledger.hexdigest()
        ),
        "chunk_hashes_sha256": chunk_hashes.hexdigest(),
        "prefix_sha256": canonical_sha256(credited_ids),
    }


def stream_terminal_state(
    *,
    stream_kind: str,
    accepted_credited: int,
    chunks_committed: int,
    target_accepted: int,
    hard_cap_chunks: int,
    read_only_checkpoint: int | None = None,
) -> str:
    """Exact global/conditional discovery state without Layer-C stopping."""

    if stream_kind not in ("global", "conditional"):
        raise SamplingError("unknown stream kind")
    if any(type(value) is not int or value < 0 for value in (accepted_credited, chunks_committed)):
        raise SamplingError("stream counters must be non-negative integers")
    if chunks_committed > hard_cap_chunks:
        raise SamplingError("stream exceeded its immutable fixed cap")
    if chunks_committed == hard_cap_chunks:
        if stream_kind == "conditional" and read_only_checkpoint is not None:
            if accepted_credited >= read_only_checkpoint:
                return "CAP_COMPLETE_CANONICAL" if accepted_credited >= target_accepted else "CAP_COMPLETE_DIAGNOSTIC_ONLY"
            return "CAP_TERMINAL_SUPPORT_INSUFFICIENT"
        return "CAP_COMPLETE_CANONICAL" if accepted_credited >= target_accepted else "CAP_TERMINAL_INCOMPLETE"
    if (
        stream_kind == "conditional"
        and read_only_checkpoint is not None
        and accepted_credited >= read_only_checkpoint
    ):
        return "READ_ONLY_CHECKPOINT_CONTINUE_FIXED_CAP"
    if accepted_credited >= target_accepted:
        return "CANONICAL_PREFIX_COMPLETE_CONTINUE_FIXED_CAP"
    return "CONTINUE_FIXED_CAP"


def resource_forecast(*, accepted: int, nominal_draws: int, targets: Sequence[int]) -> dict[str, Any]:
    """Layer-C-only forecast: it is informational and can never stop science."""

    if accepted < 0 or nominal_draws <= 0 or any(target <= 0 for target in targets):
        raise SamplingError("forecast counters/targets are invalid")
    rate = accepted / nominal_draws
    forecasts = {
        str(target): (None if rate == 0.0 else int(math.ceil(target / rate)))
        for target in targets
    }
    return {
        "layer": "C",
        "authority": "notify_only",
        "accepted": accepted,
        "nominal_draws": nominal_draws,
        "forecasts": forecasts,
        "may_stop_or_downgrade": False,
    }
