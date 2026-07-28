# Copyright Advanced Micro Devices, Inc., or its affiliates.
# SPDX-License-Identifier: MIT

"""Offline tests for the fresh S10R2 support-aware entry protocol."""

from __future__ import annotations

import ast
import copy
import datetime as dt
import hashlib
import json
import math
import statistics
import sys
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[6]
PROTOCOL = (
    ROOT / "study_docs/research/ductile-origami-warmstart/protocol/v1"
)
for path in (ROOT / "projects/hipblaslt/tensilelite", PROTOCOL):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from Tensile.ductile.evidence import canonical_sha256  # noqa: E402
from s10r2.calibration import (  # noqa: E402
    Allocation,
    CalibrationError,
    CalibrationMetrics,
    derive_caps,
    validate_allocation,
)
from s10r2.conformance import (  # noqa: E402
    EARLY_TERMINATE,
    GUARD_ORDER,
    ConformanceError,
    expected_queue,
    materialize_native_fixture,
    run_native_formocast_conformance,
    run_runtime_substitution_fault_tests,
)
from s10r2.contract import (  # noqa: E402
    ContractError,
    EXPECTED_IMPLEMENTATION_WHITELIST,
    _verify_frozen_allocation_binding,
    _verify_frozen_registry_bindings,
    canonicalize_contract,
    load_contract,
    lock_body,
    verify_human_machine_parity,
)
from s10r2.correctness import (  # noqa: E402
    CorrectnessError,
    anchor_hashes,
    validate_noise_cells,
    verify_correctness_anchors,
)
from s10r2.ledger import (  # noqa: E402
    FrozenResourceCaps,
    LedgerError,
    ResourceCounter,
    ResourceLimitError,
    RunLedger,
    enforce_stop,
)
from s10r2.mapping import (  # noqa: E402
    MappingError,
    exact_ten_greedy_cover,
    mandatory_atoms,
    verify_ab_parity,
)
from s10r2.state_machine import (  # noqa: E402
    Stage,
    TransitionError,
    assert_transition,
    transition_path_is_valid,
)
from s10r2.support import (  # noqa: E402
    CHUNK_SIZE,
    FIRST_REFORECAST_CHUNK,
    FIRST_REFORECAST_DRAWS,
    AxisSpec,
    AtomRegistry,
    SupportError,
    SupportState,
    activate_targets,
    axis_specs_from_registry,
    classify_support,
    deterministic_chunk_seed,
    sample_discovery_chunk,
    schedule_summary,
)

import run_s10r2_entry as runner  # noqa: E402


def allocation(**updates):
    values = {
        "allocation_id": "perlee:gfx942:0:window",
        "container_name": "perlee",
        "device_arch": "gfx942",
        "partition_mode": "SPX",
        "numa_mode": "NPS1",
        "available_wall_s": 600_000,
        "available_cpu_s": 5_000_000,
        "available_gpu_s": 100_000,
        "valid_from_utc": "2026-07-28T00:00:00Z",
        "valid_until_utc": "2026-08-04T00:00:00Z",
        "confirmed": True,
    }
    values.update(updates)
    return Allocation(**values)


def metrics(**updates):
    values = {
        "selection_chunk_wall_s": 1.0,
        "selection_chunk_cpu_s": 1.0,
        "mapping_row_wall_s": 1.0,
        "mapping_row_cpu_s": 1.0,
        "correctness_cell_wall_s": 2.0,
        "correctness_cell_cpu_s": 1.0,
        "correctness_cell_gpu_s": 1.0,
        "noise_cell_wall_s": 1.0,
        "noise_cell_cpu_s": 0.5,
        "noise_cell_gpu_s": 0.5,
        "native_build_wall_s": 10.0,
        "native_build_cpu_s": 10.0,
        "fixed_overhead_wall_s": 10.0,
        "fixed_overhead_cpu_s": 10.0,
        "projected_transient_storage_bytes": 1024**3,
    }
    values.update(updates)
    return CalibrationMetrics(**values)


def axes() -> list[AxisSpec]:
    result = []
    for index in range(30):
        values = (False, 0) if index == 0 else (index,)
        result.append(
            AxisSpec(
                axis_index=index,
                axis_name=f"axis_{index}",
                values=values,
                grouped=False,
                frozen_free=True,
                currently_weighted=False,
                yaml_pointer=f"/axes/{index}",
            )
        )
    return result


def witnesses(count: int = 10, required: set[str] | None = None):
    required = required or set()
    atom_list = sorted(required)
    rows = []
    for index in range(count):
        coverage = [atom_list[index]] if index < len(atom_list) else []
        rows.append(
            {
                "stream_rank": 0,
                "conditional_priority_rank": -1,
                "chunk_index": 0,
                "draw_index": index,
                "config_hash": f"{index + 1:064x}",
                "covered_atom_ids": coverage,
            }
        )
    return rows


def test_contract_loads_with_frozen_pre_evidence_semantics():
    contract = load_contract()
    assert contract["checkpoint_id"] == "S10R2"
    assert contract["status"] == "frozen_pre_evidence"
    assert contract["resource"]["numeric_relock"]["caps"]["wall_s"] == 11827


def test_contract_canonical_human_machine_parity():
    contract = load_contract()
    projection = json.loads(json.dumps(contract))
    assert verify_human_machine_parity(contract, projection) == canonical_sha256(contract)
    projection["schedule"]["chunk_size"] = 511
    with pytest.raises(ContractError, match="parity mismatch"):
        verify_human_machine_parity(contract, projection)


def test_contract_semantics_reject_schedule_drift(monkeypatch):
    contract = load_contract()
    contract["schedule"]["global_chunks"] = 31
    from s10r2 import contract as contract_module

    with pytest.raises(ContractError, match="schedule mismatch"):
        contract_module._semantic_contract_checks(contract)


def test_state_machine_happy_path_and_illegal_skip():
    assert transition_path_is_valid(
        [
            Stage.PRELOCK,
            Stage.CAPS_CONFIRMED,
            Stage.PARITY_CONFIRMED,
            Stage.AUDIT_PASS,
            Stage.LOCK_SEALED,
        ]
    )
    with pytest.raises(TransitionError):
        assert_transition(Stage.PRELOCK, Stage.GLOBAL_DISCOVERY)
    assert assert_transition(
        Stage.CORRECTNESS_ANCHORS, Stage.CORRECTNESS_ANCHORS
    ) == Stage.CORRECTNESS_ANCHORS
    assert assert_transition(Stage.NOISE_CELLS, Stage.NOISE_CELLS) == Stage.NOISE_CELLS


def test_fixed_schedule_boundaries_and_first_reforecast():
    summary = schedule_summary([f"target-{index}" for index in range(15)])
    assert summary["total_chunks"] == 512
    assert summary["total_draws"] == 262_144
    assert FIRST_REFORECAST_CHUNK == 6
    assert FIRST_REFORECAST_DRAWS == 3_072
    with pytest.raises(SupportError):
        schedule_summary([f"target-{index}" for index in range(16)])


def test_atom_registry_is_typed_complete_and_prelocked():
    registry = AtomRegistry(axes())
    document = registry.document()
    assert document["axis_count"] == 30
    assert document["row_count"] == 31
    axis_zero = [row for row in registry.rows if row["axis_index"] == 0]
    assert axis_zero[0]["exact_typed_value"] is False
    assert axis_zero[1]["exact_typed_value"] == 0
    assert axis_zero[0]["value_sha256"] != axis_zero[1]["value_sha256"]
    assert {row["atom_id"] for row in axis_zero}.issubset(registry.prelocked_atoms())
    assert AtomRegistry(axis_specs_from_registry(document)).document() == document


def test_registry_requires_exactly_thirty_contiguous_axes():
    with pytest.raises(SupportError, match="exactly 30"):
        AtomRegistry(axes()[:-1])
    broken = axes()
    broken[-1] = AxisSpec(31, "axis_29", (29,), False, True, False, "/axes/29")
    with pytest.raises(SupportError, match="contiguous"):
        AtomRegistry(broken)


def test_stochastic_zero_remains_unobserved_and_complete_proof_is_required():
    registry = AtomRegistry(axes())
    states = classify_support(registry, set())
    assert set(states.values()) == {SupportState.SUPPORT_UNOBSERVED.value}
    atom = registry.rows[0]["atom_id"]
    with pytest.raises(SupportError, match="incomplete absence proof"):
        classify_support(registry, set(), {atom: {"proof_kind": "stochastic_zero"}})
    proven = classify_support(
        registry,
        set(),
        {atom: {"proof_kind": "finite_exhaustive", "proof_digest": "a" * 64}},
    )
    assert proven[atom] == SupportState.SUPPORT_PROVEN_ABSENT.value


def test_conditional_activation_requires_full_global_and_is_deterministic():
    registry = AtomRegistry(axes())
    states = classify_support(registry, set())
    with pytest.raises(SupportError, match="32"):
        activate_targets(registry, states, completed_global_chunks=31)
    targets_a = activate_targets(registry, states, completed_global_chunks=32)
    targets_b = activate_targets(registry, states, completed_global_chunks=32)
    assert targets_a == targets_b
    assert len(targets_a) == 15


def test_chunk_seed_and_sampling_are_reproducible_and_fixed_size():
    axis_specs = axes()

    def validator(config):
        return (config["axis_0"] is False, "validator_false")

    one = sample_discovery_chunk(
        axis_specs,
        {},
        validator,
        base_seed=123,
        stream_id="global",
        chunk_index=0,
    )
    two = sample_discovery_chunk(
        axis_specs,
        {},
        validator,
        base_seed=123,
        stream_id="global",
        chunk_index=0,
    )
    assert one == two
    assert one["draws"] == CHUNK_SIZE
    assert one["accepted_count"] + one["rejected_count"] == CHUNK_SIZE
    assert deterministic_chunk_seed(123, stream_id="global", chunk_index=0) != (
        deterministic_chunk_seed(123, stream_id="global", chunk_index=1)
    )
    with pytest.raises(SupportError, match="exactly 512"):
        sample_discovery_chunk(
            axis_specs,
            {},
            validator,
            base_seed=123,
            stream_id="global",
            chunk_index=0,
            chunk_size=511,
        )


def test_mandatory_atoms_are_only_witnessed_prelocked_atoms():
    states = {"a": "supported_witnessed", "b": "support_unobserved", "c": "supported_witnessed"}
    assert mandatory_atoms({"a", "b"}, states) == frozenset({"a"})


def test_exact_ten_does_not_require_ten_mandatory_atoms():
    required = {"atom-a"}
    selected = exact_ten_greedy_cover(witnesses(10, required), required)
    assert len(selected["config_hashes"]) == 10
    assert selected["required_atom_ids"] == ["atom-a"]


def test_exact_ten_rejects_too_few_witnesses_and_cover_over_ten():
    with pytest.raises(MappingError, match="fewer than ten"):
        exact_ten_greedy_cover(witnesses(9), set())
    required = {f"atom-{index}" for index in range(11)}
    with pytest.raises(MappingError, match="more than ten"):
        exact_ten_greedy_cover(witnesses(11, required), required)


def test_exact_ten_is_deterministic_under_input_permutation():
    rows = witnesses()
    forward = exact_ten_greedy_cover(rows, set())
    reverse = exact_ten_greedy_cover(list(reversed(rows)), set())
    assert forward["config_hashes"] == reverse["config_hashes"]


def mapping_rows():
    hashes = [f"{index + 1:064x}" for index in range(10)]
    sizes = ["small", "medium", "large"]
    rows = [
        {
            "config_hash": config_hash,
            "size_id": size,
            "mapping_status": "accepted",
            "mapped_payload": {"depth_u": 32, "size": size},
            "guessed_required_fields": [],
            "unresolved_required_fields": [],
        }
        for config_hash in hashes
        for size in sizes
    ]
    return hashes, sizes, rows


def test_mapping_ab_requires_exact_30_and_parity():
    hashes, sizes, rows = mapping_rows()
    assert verify_ab_parity(rows, copy.deepcopy(rows), expected_config_hashes=hashes, expected_size_ids=sizes)[
        "status"
    ] == "PASS"
    changed = copy.deepcopy(rows)
    changed[0]["mapped_payload"]["depth_u"] = 64
    with pytest.raises(MappingError, match="parity mismatch"):
        verify_ab_parity(rows, changed, expected_config_hashes=hashes, expected_size_ids=sizes)
    with pytest.raises(MappingError, match="30"):
        verify_ab_parity(rows[:-1], rows, expected_config_hashes=hashes, expected_size_ids=sizes)


def test_anchor_and_correctness_panel():
    hashes = [f"{index:064x}" for index in range(10)]
    anchors = anchor_hashes(hashes)
    assert anchors == [hashes[0], hashes[4], hashes[9]]
    sizes = ["s", "m", "l"]
    rows = [
        {
            "config_hash": anchor,
            "size_id": size,
            "generated": True,
            "compiled": True,
            "smoke_pass": True,
            "nonzero_validation": True,
            "quality": 100.0,
        }
        for anchor in anchors
        for size in sizes
    ]
    assert verify_correctness_anchors(rows, anchors=anchors, size_ids=sizes)["status"] == "PASS"
    rows[0]["nonzero_validation"] = False
    with pytest.raises(CorrectnessError, match="FT-BLOCKED-CORRECTNESS"):
        verify_correctness_anchors(rows, anchors=anchors, size_ids=sizes)


def test_noise_requires_exact_63_and_threshold():
    anchors = ["a" * 64, "b" * 64, "c" * 64]
    sizes = ["s", "m", "l"]
    rows = [
        {
            "config_hash": anchor,
            "size_id": size,
            "repeat": repeat,
            "quality": 100.0 + repeat * 0.01,
        }
        for anchor in anchors
        for size in sizes
        for repeat in range(7)
    ]
    result = validate_noise_cells(rows, anchors=anchors, size_ids=sizes)
    assert result["raw_observation_count"] == 63
    assert result["aggregate_quality_count"] == 21
    assert result["anchor_count"] == 3
    assert result["applied_reduce_fn"] == "max"
    assert result["status"] == "PASS"
    with pytest.raises(CorrectnessError, match="63"):
        validate_noise_cells(rows[:-1], anchors=anchors, size_ids=sizes)


def test_noise_uses_max_size_aggregate_before_cv_and_delta():
    anchors = ["a" * 64, "b" * 64, "c" * 64]
    sizes = ["s", "m", "l"]
    varying = [50.0, 150.0, 25.0, 175.0, 75.0, 125.0, 10.0]
    rows = [
        {
            "config_hash": anchor,
            "size_id": size,
            "repeat": repeat,
            "quality": (
                varying[repeat]
                if size == "s"
                else 1_000.0 if size == "m" else 500.0
            ),
        }
        for anchor in anchors
        for repeat in range(7)
        for size in sizes
    ]
    result = validate_noise_cells(rows, anchors=anchors, size_ids=sizes)
    assert result["anchor_cvs"] == {anchor: 0.0 for anchor in anchors}
    assert result["cv_p95"] == 0.0
    assert result["delta_noise"] == 0.0
    assert result["status"] == "PASS"


def test_noise_matches_independent_q_ar_reference():
    anchors = ["a" * 64, "b" * 64, "c" * 64]
    sizes = ["s", "m", "l"]
    aggregate = {
        anchor: [
            1000.0
            * (1.0 + anchor_index * 0.0002 + repeat * 0.0001)
            for repeat in range(7)
        ]
        for anchor_index, anchor in enumerate(anchors)
    }
    rows = [
        {
            "config_hash": anchor,
            "size_id": size,
            "repeat": repeat,
            "quality": aggregate[anchor][repeat] - (20.0, 0.0, 10.0)[size_index],
        }
        for anchor in anchors
        for repeat in range(7)
        for size_index, size in enumerate(sizes)
    ]
    result = validate_noise_cells(rows, anchors=anchors, size_ids=sizes)

    reference_cvs = [
        statistics.pstdev(aggregate[anchor])
        / statistics.fmean(aggregate[anchor])
        for anchor in anchors
    ]
    ordered_cvs = sorted(reference_cvs)
    reference_cv_p95 = ordered_cvs[1] * 0.1 + ordered_cvs[2] * 0.9
    deviations = []
    for anchor in anchors:
        logs = [math.log(value) for value in aggregate[anchor]]
        median = statistics.median(logs)
        deviations.extend(abs(value - median) for value in logs)
    ordered_deviations = sorted(deviations)
    position = (len(ordered_deviations) - 1) * 0.95
    lower = math.floor(position)
    upper = math.ceil(position)
    fraction = position - lower
    reference_p95 = (
        ordered_deviations[lower] * (1 - fraction)
        + ordered_deviations[upper] * fraction
    )
    assert result["cv_p95"] == pytest.approx(reference_cv_p95)
    assert result["delta_noise"] == pytest.approx(math.exp(reference_p95) - 1)


def test_gpu_pid_parser_and_selection_enforce_selected_card_ownership():
    output = """
================ GPUs Indexed by PID ================
PID 101 is using 1 DRM device(s):
0
PID 202 is using 2 DRM device(s):
2 3
=====================================================
"""
    parsed = runner._parse_gpu_pid_output(
        output, visible_indices=[0, 1, 2, 3]
    )
    assert parsed == {
        "0": [101],
        "1": [],
        "2": [202],
        "3": [202],
    }
    snapshot = {
        "devices": {
            f"card{index}": {
                "GFX Version": "gfx942",
                "Compute Partition": "SPX",
                "Memory Partition": "NPS1",
                "GPU use (%)": "0",
                "GPU Memory Allocated (VRAM%)": "0",
            }
            for index in range(4)
        }
    }
    selected_index, _ = runner._select_idle_gfx942(
        snapshot, {"physical_device_pids": parsed}
    )
    assert selected_index == 1
    runner._assert_selected_card_pid_free(
        1, {"physical_device_pids": parsed}
    )
    with pytest.raises(runner.RunnerError, match="foreign PID"):
        runner._assert_selected_card_pid_free(
            0, {"physical_device_pids": parsed}
        )


@pytest.mark.parametrize(
    "output",
    [
        "PID 101 is using 2 DRM device(s):\n0\n",
        "PID 101 is using 1 DRM device(s):\n9\n",
        "PID 101, Item searched for but not found\n",
        "No KFD PIDs currently running\nPID 101 is using 1 DRM device(s):\n0\n",
    ],
)
def test_gpu_pid_parser_fails_closed_on_malformed_or_ambiguous_output(output):
    with pytest.raises(runner.RunnerError):
        runner._parse_gpu_pid_output(output, visible_indices=[0, 1])


def test_gpu_pid_snapshot_fails_closed_on_command_failure(monkeypatch):
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=1,
            stdout=b"",
            stderr=b"failure",
        ),
    )
    with pytest.raises(runner.RunnerError, match="snapshot failed"):
        runner._gpu_process_snapshot(
            {"devices": {"card0": {}}}
        )


def test_ledger_append_replay_resume_and_tamper(tmp_path):
    ledger = RunLedger(tmp_path / "run")
    payload = {
        "stage": "LOCK_SEALED",
        "contract_digest": "a" * 64,
        "lock_digest": "b" * 64,
        "resource_counter": asdict(ResourceCounter()),
        "resume_cursor": {"stream_id": "global", "next_chunk_index": 0},
    }
    first = ledger.append(payload)
    second_payload = dict(payload)
    second_payload["stage"] = "PRE_DRAW_REGISTRY_FROZEN"
    second_payload["resume_cursor"] = {"stream_id": "global", "next_chunk_index": 1}
    ledger.append(second_payload)
    assert len(ledger.load()) == 2
    assert ledger.resume_cursor().next_chunk_index == 1
    first_path = next((tmp_path / "run/events").glob("00000000-*.json"))
    document = json.loads(first_path.read_text())
    document["stage"] = "tampered"
    first_path.write_text(json.dumps(document))
    with pytest.raises(LedgerError, match="digest mismatch"):
        ledger.load()


def test_ledger_rejects_illegal_stage_skip_and_concurrent_writer(tmp_path):
    ledger = RunLedger(tmp_path / "run")
    payload = {
        "stage": "LOCK_SEALED",
        "contract_digest": "a" * 64,
        "lock_digest": "b" * 64,
        "resource_counter": asdict(ResourceCounter()),
    }
    ledger.append(payload)
    with pytest.raises(LedgerError, match="transition"):
        ledger.append({**payload, "stage": "GLOBAL_DISCOVERY"})
    with ledger.acquire_writer():
        with pytest.raises(LedgerError, match="another"):
            ledger.acquire_writer()


def test_resource_pre_reservation_and_five_gib_stop():
    caps = FrozenResourceCaps(100, 100, 100, 5 * 1024**3)
    current = ResourceCounter(10, 10, 10, 4 * 1024**3)
    enforce_stop(current, ResourceCounter(1, 1, 1, 1024**3), caps)
    with pytest.raises(ResourceLimitError, match="transient_storage_bytes"):
        enforce_stop(current, ResourceCounter(1, 1, 1, 1024**3 + 1), caps)


@pytest.mark.parametrize(
    "unit_kind",
    [
        "selection_chunk",
        "mapping_ab",
        "native_conformance",
        "gpu_environment",
        "correctness_anchor",
        "noise_anchor_repeat",
        "decision",
    ],
)
def test_projected_resource_stop_is_durable_for_every_formal_unit(
    tmp_path, monkeypatch, unit_kind
):
    root = tmp_path / unit_kind
    ledger = RunLedger(root / "ledger")
    current = ResourceCounter(9.0, 0.0, 0.0, 0)
    with ledger.acquire_writer():
        ledger.append(
            {
                "stage": Stage.LOCK_SEALED.value,
                "contract_digest": "a" * 64,
                "lock_digest": "b" * 64,
                "resource_counter": asdict(current),
            }
        )
        ledger.fsync()
    monkeypatch.setattr(runner, "_repo_relative", lambda path: str(path))
    monkeypatch.setattr(
        runner, "_allocation_block_if_needed", lambda **_kwargs: None
    )
    with ledger.acquire_writer():
        result = runner._resource_block_if_needed(
            ledger=ledger,
            root=root,
            contract_digest="a" * 64,
            lock_digest="b" * 64,
            caps=FrozenResourceCaps(10.0, 10.0, 10.0, 10),
            current=current,
            reservation=ResourceCounter(2.0, 0.0, 0.0, 0),
            next_atomic_unit={"kind": unit_kind},
        )
    assert result["status"] == "BLOCKED_RESOURCE_CAP"
    assert result["scientific_outcome"] == "not_evaluated"
    assert result["edge"] is None
    assert result["stop_phase"] == "pre_start_projection"
    event = ledger.load()[-1]
    assert event["stage"] == Stage.BLOCKED.value
    assert event["resource_counter"] == asdict(current)
    assert event["requested_reservation"]["wall_s"] == 2.0
    assert event["projected_resource_counter"]["wall_s"] == 11.0
    assert event["next_atomic_unit"] == {"kind": unit_kind}


@pytest.mark.parametrize(
    "unit_kind",
    [
        "selection_chunk",
        "mapping_ab",
        "native_conformance",
        "gpu_environment",
        "correctness_anchor",
        "noise_anchor_repeat",
        "decision",
    ],
)
def test_actual_resource_overrun_binds_artifact_and_recovers_once(
    tmp_path, monkeypatch, unit_kind
):
    root = tmp_path / unit_kind
    ledger = RunLedger(root / "ledger")
    current = ResourceCounter(1.0, 1.0, 0.0, 1)
    with ledger.acquire_writer():
        ledger.append(
            {
                "stage": Stage.LOCK_SEALED.value,
                "contract_digest": "c" * 64,
                "lock_digest": "d" * 64,
                "resource_counter": asdict(current),
            }
        )
        ledger.fsync()
    monkeypatch.setattr(runner, "_repo_relative", lambda path: str(path))
    monkeypatch.setattr(
        runner, "_allocation_block_if_needed", lambda **_kwargs: None
    )
    call = {
        "ledger": ledger,
        "root": root,
        "contract_digest": "c" * 64,
        "lock_digest": "d" * 64,
        "caps": FrozenResourceCaps(10.0, 10.0, 10.0, 10),
        "current": current,
        "reservation": ResourceCounter(1.0, 1.0, 0.0, 1),
        "actual_counter": ResourceCounter(11.0, 2.0, 0.0, 2),
        "next_atomic_unit": {"kind": unit_kind},
        "completed_artifact_ref": {
            "path": f"{unit_kind}.json",
            "sha256": "e" * 64,
        },
    }
    with ledger.acquire_writer():
        first = runner._resource_block_if_needed(**call)
    assert first["stop_phase"] == "completed_unit_actual"
    assert first["exceeded"] == ["wall_s"]
    event_path = ledger._event_paths()[-1]
    event_path.unlink()
    with ledger.acquire_writer():
        recovered = runner._resource_block_if_needed(**call)
    assert recovered["status"] == "BLOCKED_RESOURCE_CAP"
    events = ledger.load()
    assert len(events) == 2
    assert events[-1]["stage"] == Stage.BLOCKED.value
    assert events[-1]["resource_counter"]["wall_s"] == 11.0
    assert events[-1]["completed_artifact_ref"]["sha256"] == "e" * 64
    assert events[-1]["recovered_unledgered_complete_artifact"] is True


def test_post_lock_allocation_expiry_is_durable_operational_block(
    tmp_path, monkeypatch
):
    contract = load_contract()
    contract_digest = canonical_sha256(contract)
    root = tmp_path / "allocation-expired"
    ledger = RunLedger(root / "ledger")
    current = ResourceCounter(1.0, 1.0, 0.0, 1)
    with ledger.acquire_writer():
        ledger.append(
            {
                "stage": Stage.LOCK_SEALED.value,
                "contract_digest": contract_digest,
                "lock_digest": "d" * 64,
                "resource_counter": asdict(current),
            }
        )
        ledger.fsync()
    monkeypatch.setattr(runner, "_repo_relative", lambda path: str(path))
    with ledger.acquire_writer():
        blocked = runner._allocation_block_if_needed(
            ledger=ledger,
            root=root,
            contract_digest=contract_digest,
            lock_digest="d" * 64,
            current=current,
            reservation=ResourceCounter(1.0, 0.0, 0.0, 0),
            next_atomic_unit={"kind": "selection_chunk"},
            contract=contract,
            at_utc="2026-08-05T00:00:00Z",
        )
    assert blocked["status"] == "BLOCKED_ALLOCATION_WINDOW"
    assert blocked["scientific_outcome"] == "not_evaluated"
    assert blocked["edge"] is None
    assert "expired" in blocked["violation"]
    event = ledger.load()[-1]
    assert event["stage"] == Stage.BLOCKED.value
    assert event["block_reason"] == "BLOCKED_ALLOCATION_WINDOW"


def test_cap_derivation_is_deterministic_and_allocation_bounded():
    first = derive_caps(allocation(), metrics())
    second = derive_caps(allocation(), metrics())
    assert first == second
    assert first.transient_storage_bytes == 1024**3
    with pytest.raises(CalibrationError, match="does not fit"):
        derive_caps(allocation(available_wall_s=10), metrics())
    with pytest.raises(CalibrationError, match="5 GiB"):
        derive_caps(metrics=metrics(projected_transient_storage_bytes=5 * 1024**3 + 1), allocation=allocation())


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"valid_from_utc": "not-a-time"}, "valid UTC timestamp"),
        ({"valid_from_utc": "2026-07-28T00:00:00"}, "timezone-aware UTC"),
        (
            {
                "valid_from_utc": "2026-07-29T00:00:00Z",
                "valid_until_utc": "2026-07-28T00:00:00Z",
            },
            "start before end",
        ),
    ],
)
def test_allocation_rejects_malformed_naive_and_inverted_windows(
    updates, message
):
    with pytest.raises(CalibrationError, match=message):
        validate_allocation(
            allocation(**updates),
            at_utc=dt.datetime(2026, 7, 28, 12, tzinfo=dt.timezone.utc),
        )


def test_allocation_rejects_future_expired_and_insufficient_windows():
    current = dt.datetime(2026, 7, 28, 12, tzinfo=dt.timezone.utc)
    with pytest.raises(CalibrationError, match="not yet active"):
        validate_allocation(
            allocation(
                valid_from_utc="2026-07-29T00:00:00Z",
                valid_until_utc="2026-07-30T00:00:00Z",
            ),
            at_utc=current,
        )
    with pytest.raises(CalibrationError, match="expired"):
        validate_allocation(
            allocation(
                valid_from_utc="2026-07-26T00:00:00Z",
                valid_until_utc="2026-07-27T00:00:00Z",
            ),
            at_utc=current,
        )
    with pytest.raises(CalibrationError, match="required duration"):
        validate_allocation(
            allocation(
                valid_from_utc="2026-07-28T00:00:00Z",
                valid_until_utc="2026-07-28T12:01:00Z",
            ),
            at_utc=current,
            required_duration_s=61,
        )


def test_metric_provenance_binds_corrected_gpu_pid_calibration():
    contract = load_contract()
    metrics_path = (
        ROOT
        / contract["formal_execution"]["calibration_metrics_record"]
    )
    document = json.loads(metrics_path.read_text(encoding="utf-8"))
    parsed = runner._metrics(document)
    assert parsed.correctness_cell_wall_s == 20.140861546620727
    gpu = document["metric_provenance"]["records"]["gpu"]
    assert gpu["path"].endswith(
        "calibration/gpu-v2/s10r2-gpu-calibration.json"
    )
    assert (
        gpu["document_digest"]
        == contract["resource"]["calibration_protocol"]["gpu_fixed_cost"][
            "calibration_digest"
        ]
    )
    broken = copy.deepcopy(document)
    broken["metric_provenance"]["records"]["gpu"]["sha256"] = "0" * 64
    with pytest.raises(runner.RunnerError, match="file hash mismatch"):
        runner._metrics(broken)


def cohort():
    return [
        {"ordinal": 0, "check_solution": True, "microseconds": 2.0},
        {"ordinal": 1, "check_solution": False, "microseconds": 0.1},
        {"ordinal": 2, "check_solution": True, "microseconds": 1.0},
        {"ordinal": 3, "check_solution": True, "microseconds": 2.0},
    ]


def test_queue_semantics_stable_sort_thresholds_and_disabled():
    assert expected_queue(cohort(), 0.0)["queue_prefix"] == [2]
    half = expected_queue(cohort(), 0.5)
    assert half["sorted_ordinals"] == [2, 0, 3]
    assert half["queue_prefix"] == [2, 0, 3]
    assert expected_queue(cohort(), 2.0)["queue_prefix"] == [0, 1, 2, 3]


def test_native_conformance_and_substitution_faults():
    fixture = {"cohort": cohort(), "thresholds": [0.0, 0.5, 1.0, 2.0]}
    transcript = {
        "native_path_called": True,
        "runtime_check_solution_called": True,
        "guard_order": GUARD_ORDER,
        "early_terminate": EARLY_TERMINATE,
        "queues": {
            str(value): expected_queue(fixture["cohort"], value)
            for value in fixture["thresholds"]
        },
    }
    assert run_native_formocast_conformance(transcript, fixture)["status"] == "PASS"
    broken = copy.deepcopy(transcript)
    broken["runtime_check_solution_called"] = False
    with pytest.raises(ConformanceError, match="checkSolution"):
        run_native_formocast_conformance(broken, fixture)

    valid = {
        "helper_path": "p",
        "helper_sha256": "a",
        "predicted_performance_source_blob": "b",
        "host_adapter_sha256": "c",
        "queue_adapter_source_blob": "d",
    }

    def validator(candidate):
        if candidate != valid:
            raise ValueError("binding mismatch")

    mutations = {key: f"changed-{key}" for key in valid}
    result = run_runtime_substitution_fault_tests(
        validator, valid, mutations=mutations
    )
    assert set(result["results"].values()) == {"FAIL_CLOSED"}


def test_contract_native_fixture_is_complete_and_reproduces_locked_transcript():
    native = load_contract()["native_conformance"]
    materialized = materialize_native_fixture(
        native["synthetic_fixture"], native["thresholds"]
    )
    assert hashlib.sha256(materialized["input_bytes"]).hexdigest() == (
        "aa10a2faab53f1ef0c756a21e9e704e01d9878aec0c02e54ee7a0486fba860f0"
    )
    assert materialized["expected_queues"] == native["synthetic_fixture"][
        "expected_queues"
    ]
    assert materialized["cohort"][0]["microseconds"] == materialized["cohort"][2][
        "microseconds"
    ]
    assert materialized["cohort"][1]["check_solution"] is False


def test_runner_contract_and_dry_schedule_preserve_lock_lifecycle(
    monkeypatch, tmp_path
):
    committed_lock = PROTOCOL / "locks/s10r2-stage1-support-aware-entry-lock.json"
    result = runner.validate_contract()
    assert result["human_machine_parity"] == "PASS"
    if committed_lock.is_file():
        _, expected_lock_digest = runner.require_effective_lock(
            committed_lock,
            enforce_allocation_window=False,
        )
        assert result["formal_evidence_authorized"] is True
        assert result["effective_lock_digest"] == expected_lock_digest
    else:
        assert result["formal_evidence_authorized"] is False
        assert result["effective_lock_digest"] is None

    isolated_missing_lock = tmp_path / "isolated-no-lock.json"
    monkeypatch.setattr(runner, "LOCK_PATH", isolated_missing_lock)
    isolated = runner.validate_contract()
    assert isolated["human_machine_parity"] == "PASS"
    assert isolated["formal_evidence_authorized"] is False
    assert isolated["effective_lock_digest"] is None

    schedule = runner.dry_run_schedule(15)
    assert schedule["formal_draws_executed"] == 0
    assert schedule["total_draws"] == 262_144


def test_formal_preflight_fails_without_lock():
    with pytest.raises(FileNotFoundError):
        runner.require_effective_lock(PROTOCOL / "locks/does-not-exist.json")


def test_every_formal_entrypoint_fails_before_side_effect_without_lock(tmp_path):
    missing = tmp_path / "missing-lock.json"
    calls = [
        lambda: runner.initialize_formal_run(lock_path=missing),
        lambda: runner.formal_discovery_step(
            max_new_chunks=1, lock_path=missing
        ),
        lambda: runner.seal_support_classification(lock_path=missing),
        lambda: runner.select_exact_ten(lock_path=missing),
        lambda: runner.run_formal_mapping(lock_path=missing),
        lambda: runner.run_formal_native_conformance(lock_path=missing),
        lambda: runner.record_formal_gpu_environment(lock_path=missing),
        lambda: runner.run_formal_correctness(lock_path=missing),
        lambda: runner.run_formal_noise(lock_path=missing),
        lambda: runner.materialize_formal_decision(lock_path=missing),
        lambda: runner.reproduce_formal_decision(
            lock_path=missing,
            output_path=tmp_path / "reproduction.json",
        ),
    ]
    for call in calls:
        with pytest.raises(FileNotFoundError):
            call()
    assert list(tmp_path.iterdir()) == []


def test_contract_whitelists_and_frozen_numeric_gate_are_exact():
    contract = load_contract()
    assert contract["implementation_whitelist"] == EXPECTED_IMPLEMENTATION_WHITELIST
    assert set(EXPECTED_IMPLEMENTATION_WHITELIST).issubset(
        contract["delivery_whitelist"]
    )
    assert contract["resource"]["prospective_limits"]["repair_rounds"] == 6
    assert (
        contract["authority"]["repair_budget_amendment_commit"]
        == "bfe700ca76a17bd65509f3afff70abaf0ad125f4"
    )
    frozen = copy.deepcopy(contract)
    frozen["resource"]["numeric_relock"]["caps"] = None
    with pytest.raises(ContractError, match="complete numeric relock"):
        from s10r2 import contract as contract_module

        contract_module._semantic_contract_checks(frozen)


def test_effective_lock_rejects_nonfresh_or_stale_audit_before_artifacts():
    contract = load_contract()
    with pytest.raises(ContractError, match="fresh AUDIT_PASS"):
        lock_body(
            contract=contract,
            schema_path=PROTOCOL / "schemas/s10r2-entry.schema.json",
            audit={"verdict": "AUDIT_PASS", "fresh": False},
            allocation_fixture={},
            implementation={},
            registry_digest="a" * 64,
            artifact_bindings={},
            prelock_elapsed_s=0,
        )


def _registry_bindings(contract):
    return {
        "candidate_atom_registry": {
            "path": contract["support"]["candidate_registry_path"],
            "document_digest_field": "registry_digest",
            "document_digest": contract["support"]["candidate_registry_digest"],
        },
        "size_registry": {
            "path": contract["correctness"]["size_registry_path"],
            "document_digest_field": "size_registry_digest",
            "document_digest": contract["correctness"]["size_registry_digest"],
        },
    }


def test_frozen_registry_bindings_reject_every_substitution_axis():
    contract = load_contract()
    bindings = _registry_bindings(contract)
    candidate_digest = contract["support"]["candidate_registry_digest"]
    _verify_frozen_registry_bindings(
        contract, bindings, candidate_digest=candidate_digest
    )

    alternate = copy.deepcopy(bindings)
    alternate["candidate_atom_registry"].update(
        {
            "path": "alternate/self-consistent-registry.json",
            "document_digest": "0" * 64,
        }
    )
    with pytest.raises(ContractError, match="candidate registry digest"):
        _verify_frozen_registry_bindings(
            contract, alternate, candidate_digest="0" * 64
        )

    with pytest.raises(ContractError, match="candidate registry digest"):
        _verify_frozen_registry_bindings(
            contract, bindings, candidate_digest="0" * 64
        )

    mismatched_document = copy.deepcopy(bindings)
    mismatched_document["candidate_atom_registry"]["document_digest"] = "0" * 64
    with pytest.raises(ContractError, match="candidate_atom_registry"):
        _verify_frozen_registry_bindings(
            contract, mismatched_document, candidate_digest=candidate_digest
        )

    alternate_path = copy.deepcopy(bindings)
    alternate_path["candidate_atom_registry"]["path"] = "alternate/registry.json"
    with pytest.raises(ContractError, match="candidate_atom_registry"):
        _verify_frozen_registry_bindings(
            contract, alternate_path, candidate_digest=candidate_digest
        )

    alternate_size = copy.deepcopy(bindings)
    alternate_size["size_registry"]["path"] = "alternate/sizes.json"
    with pytest.raises(ContractError, match="size_registry"):
        _verify_frozen_registry_bindings(
            contract, alternate_size, candidate_digest=candidate_digest
        )


def test_frozen_allocation_record_must_equal_calibration_fixture(tmp_path):
    contract = load_contract()
    fixture_allocation = allocation()
    relative = contract["formal_execution"]["allocation_record"]
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(asdict(fixture_allocation)),
        encoding="utf-8",
    )
    bindings = {
        "allocation_record": {
            "path": relative,
            "sha256": "unused-by-cross-binding-helper",
            "document_digest_field": None,
            "document_digest": None,
        }
    }
    _verify_frozen_allocation_binding(
        contract,
        bindings,
        fixture_allocation=fixture_allocation,
        repository_root=tmp_path,
    )
    substitutions = [
        ("valid_until_utc", "2026-08-05T00:00:00Z"),
        ("confirmed", 1),
        ("available_wall_s", 600_000.0),
    ]
    for field, value in substitutions:
        altered = asdict(fixture_allocation)
        altered[field] = value
        path.write_text(json.dumps(altered), encoding="utf-8")
        with pytest.raises(ContractError, match="differs from calibrated fixture"):
            _verify_frozen_allocation_binding(
                contract,
                bindings,
                fixture_allocation=fixture_allocation,
                repository_root=tmp_path,
            )


def test_formal_initialize_recovers_between_its_two_ledger_events(
    tmp_path, monkeypatch
):
    contract = load_contract()
    lock_digest = "d" * 64
    formal_root = tmp_path / "formal"
    ledger = RunLedger(formal_root / "ledger")
    initial = ResourceCounter(
        **contract["resource"]["numeric_relock"]["initial_resource_counter"]
    )
    with ledger.acquire_writer():
        first = ledger.append(
            runner._event_payload(
                stage=Stage.LOCK_SEALED,
                contract_digest=canonical_sha256(contract),
                lock_digest=lock_digest,
                counter=initial,
                fixture_digest=contract["resource"]["numeric_relock"][
                    "calibration_fixture_digest"
                ],
                lock_path="test-lock.json",
                resume_cursor={"stream_id": "global", "next_chunk_index": 0},
            )
        )
        ledger.fsync()
    monkeypatch.setattr(
        runner,
        "require_effective_lock",
        lambda _path, **_kwargs: (contract, lock_digest),
    )
    monkeypatch.setattr(runner, "_formal_root", lambda _contract, _root: formal_root)
    monkeypatch.setattr(
        runner,
        "_load_registry_document",
        lambda: ({"registry_digest": "registry-test"}, None),
    )
    monkeypatch.setattr(runner, "_repo_relative", lambda path: str(path))
    monkeypatch.setattr(
        runner,
        "_absolute_storage_counter",
        lambda current, _contract, **_updates: current,
    )
    recovered = runner.initialize_formal_run(lock_path=tmp_path / "lock.json")
    assert recovered["status"] == "FORMAL_RUN_INITIALIZED"
    assert recovered["lock_event_digest"] == first["event_digest"]
    assert [event["stage"] for event in ledger.load()] == [
        Stage.LOCK_SEALED.value,
        Stage.PRE_DRAW_REGISTRY_FROZEN.value,
    ]
    repeated = runner.initialize_formal_run(lock_path=tmp_path / "lock.json")
    assert repeated["status"] == "FORMAL_RUN_ALREADY_INITIALIZED"


def test_formal_discovery_adopts_complete_unledgered_chunk(tmp_path, monkeypatch):
    contract = load_contract()
    lock_digest = "e" * 64
    formal_root = tmp_path / "formal"
    ledger = RunLedger(formal_root / "ledger")
    initial = ResourceCounter(
        **contract["resource"]["numeric_relock"]["initial_resource_counter"]
    )
    with ledger.acquire_writer():
        ledger.append(
            runner._event_payload(
                stage=Stage.LOCK_SEALED,
                contract_digest=canonical_sha256(contract),
                lock_digest=lock_digest,
                counter=initial,
                fixture_digest="fixture",
                resume_cursor={"stream_id": "global", "next_chunk_index": 0},
            )
        )
        ledger.append(
            runner._event_payload(
                stage=Stage.PRE_DRAW_REGISTRY_FROZEN,
                contract_digest=canonical_sha256(contract),
                lock_digest=lock_digest,
                counter=initial,
                fixture_digest="registry",
                resume_cursor={"stream_id": "global", "next_chunk_index": 0},
            )
        )
        ledger.fsync()

    monkeypatch.setattr(
        runner, "require_effective_lock", lambda _path: (contract, lock_digest)
    )
    monkeypatch.setattr(runner, "_formal_root", lambda _contract, _root: formal_root)
    monkeypatch.setattr(runner, "_integration_root", lambda _contract: tmp_path)
    monkeypatch.setattr(runner, "_repo_relative", lambda path: str(path))

    def counter(current, _contract, *, wall_delta=0, cpu_delta=0, gpu_delta=0):
        return ResourceCounter(
            wall_s=current.wall_s + wall_delta,
            cpu_s=current.cpu_s + cpu_delta,
            gpu_s=current.gpu_s + gpu_delta,
            transient_storage_bytes=current.transient_storage_bytes,
        )

    monkeypatch.setattr(runner, "_absolute_storage_counter", counter)
    calls = {"count": 0}

    def validate(**_kwargs):
        calls["count"] += 1
        return (
            [{"valid": False, "reason": "validator_false"} for _ in range(512)],
            {"wall_s": 0.1, "cpu_s": 0.2, "gpu_s": 0.0},
        )

    monkeypatch.setattr(runner, "run_pinned_validator_batch", validate)
    first = runner.formal_discovery_step.__wrapped__(
        max_new_chunks=1,
        run_root=formal_root,
        lock_path=tmp_path / "lock.json",
    )
    assert first["completed_now"] == 1
    assert calls["count"] == 1
    chunk_event_path = ledger._event_paths()[-1]
    chunk_event_path.unlink()

    def unexpected_validation(**_kwargs):
        raise AssertionError("complete orphan chunk must not be re-evaluated")

    monkeypatch.setattr(
        runner, "run_pinned_validator_batch", unexpected_validation
    )
    recovered = runner.formal_discovery_step.__wrapped__(
        max_new_chunks=1,
        run_root=formal_root,
        lock_path=tmp_path / "lock.json",
    )
    assert recovered["completed_now"] == 1
    event = ledger.load()[-1]
    assert event["recovered_unledgered_complete_chunk"] is True
    assert event["chunk_index"] == 0


def test_benchmark_csv_parser_and_client_result_rewrite(tmp_path):
    sizes = [
        {"size_id": "small", "values": [8, 8, 1, 128]},
        {"size_id": "medium", "values": [256, 256, 1, 1024]},
        {"size_id": "large", "values": [2304, 1024, 1, 214336]},
    ]
    result = tmp_path / "result.csv"
    result.write_text(
        "SizeI,SizeJ,SizeK,SizeL,WinnerTimeUS,WinnerGFlops\n"
        "8,8,1,128,1.0,2.0\n"
        "256,256,1,1024,3.0,4.0\n"
        "2304,1024,1,214336,5.0,6.0\n",
        encoding="utf-8",
    )
    parsed_path, rows = runner._benchmark_csv_rows(tmp_path, sizes)
    assert parsed_path == result
    assert [row["size_id"] for row in rows] == ["small", "medium", "large"]
    base = tmp_path / "base.ini"
    base.write_text("device-idx=0\nresults-file=old.csv\n", encoding="utf-8")
    rewritten = tmp_path / "rewritten.ini"
    runner._rewrite_client_results(base, rewritten, tmp_path / "new.csv")
    assert "results-file=" + str(tmp_path / "new.csv") in rewritten.read_text()


def test_mapping_worker_duplicate_suppression_is_candidate_local():
    source = runner.mapping_worker_code()
    loop = source.index('for candidate in request["candidates"]:')
    scoped = source.index("visited_kernel_bases = set()", loop)
    solution = source.index("solution = _generate_single_solution_with_groups", loop)
    assert loop < scoped < solution


def test_s10r2_python_has_no_s10r1_imports():
    sources = list((PROTOCOL / "s10r2").glob("*.py")) + [
        PROTOCOL / "run_s10r2_entry.py"
    ]
    for path in sources:
        tree = ast.parse(path.read_text(), filename=str(path))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        assert not any("s10r1" in name.lower() for name in imported), path


def test_native_source_binds_real_runtime_and_formocast_paths():
    source = (
        PROTOCOL / "s10r2/native_formocast_runtime_adapter.cpp"
    ).read_text()
    assert "AllSolutionsIterator" in source
    assert "iterator.preProblem(&currentProblem)" in source
    assert "formocast.predictedPerformance()" in source
    assert "evaluate_formocast_all_solutions_cohort" in source
