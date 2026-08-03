"""Outcome-blind tests for repository experiment artifact governance."""

from __future__ import annotations

import importlib.util
import re
from contextlib import contextmanager
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "study_docs/research/tools/experiment_artifact_governance.py"
SPEC = importlib.util.spec_from_file_location("experiment_artifact_governance", MODULE_PATH)
assert SPEC and SPEC.loader
governance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(governance)


@contextmanager
def raises(error_type, *, match):
    try:
        yield
    except error_type as exc:
        assert re.search(match, str(exc)), (match, str(exc))
    else:
        raise AssertionError(f"expected {error_type.__name__}: {match}")


def encoded(value):
    return governance.canonical_json_bytes(value)


def operational(
    payload=None,
    *,
    path="agent_run/example/command.json",
    sequence_or_id="command-7",
):
    return encoded(
        {
            "event_type": "operational_record",
            "artifact_layer": "operational_bookkeeping",
            "path": path,
            "sequence_or_id": sequence_or_id,
            "payload": (
                {"status": "runnng", "wall_s": 12} if payload is None else payload
            ),
        }
    )


def correction(original, *, timestamp, payload, reason="fix typo"):
    target = governance.strict_json_loads(original)
    return encoded(
        {
            "event_type": "operational_correction",
            "target": {
                "path": target["path"],
                "sequence_or_id": target["sequence_or_id"],
                "raw_sha256": governance.raw_sha256(original),
            },
            "reason": reason,
            "corrected_payload": payload,
            "author_or_actor": "main-agent",
            "recorded_at_utc": timestamp,
            "projection_rule": governance.PROJECTION_RULE,
            "scientific_impact": "none",
        }
    )


def layer_c_rule(
    *,
    path="agent_run/example/command.json",
    sequence_or_id="command-7",
    path_pattern=None,
    sequence_or_id_pattern=None,
    payload_leaf_pointers=("/status", "/wall_s"),
    correctable_leaf_pointers=("/status", "/wall_s"),
    rule_id="command-records",
):
    return {
        "rule_id": rule_id,
        "path_pattern": re.escape(path) if path_pattern is None else path_pattern,
        "sequence_or_id_pattern": (
            re.escape(sequence_or_id)
            if sequence_or_id_pattern is None
            else sequence_or_id_pattern
        ),
        "payload_leaf_pointers": list(payload_leaf_pointers),
        "correctable_leaf_pointers": list(correctable_leaf_pointers),
    }


def layer_c_registry(*rules, **default_rule_arguments):
    if not rules:
        rules = (layer_c_rule(**default_rule_arguments),)
    raw = encoded(
        {
            "event_type": "sealed_layer_c_registry",
            "schema_version": governance.REGISTRY_SCHEMA_VERSION,
            "rules": list(rules),
        }
    )
    return raw, governance.raw_sha256(raw)


def project(originals, corrections, registry=None):
    registry_raw, registry_sha256 = layer_c_registry() if registry is None else registry
    return governance.project_operational_records(
        originals,
        corrections,
        registry_raw,
        registry_sha256,
    )


def candidate(revision, status, payload):
    return encoded(
        {
            "event_type": "candidate_revision",
            "artifact_layer": "pre_seal_candidate",
            "path": "protocol/example-contract.yaml",
            "revision": revision,
            "candidate_status": status,
            "payload": payload,
        }
    )


def sealed(milestone_id="checkpoint-lock-v1", payload=None):
    return encoded(
        {
            "event_type": "sealed_scientific_milestone",
            "artifact_layer": "sealed_scientific_milestone",
            "milestone_id": milestone_id,
            "artifact_inventory": ["formal_inputs", "old_measurements"],
            "payload": payload or {"threshold": 0.5, "seeds": [1, 2]},
        }
    )


def successor(predecessor, *, event_type="scientific_successor", milestone_id="checkpoint-lock-v2"):
    predecessor_value = governance.strict_json_loads(predecessor)
    return encoded(
        {
            "event_type": event_type,
            "artifact_layer": "sealed_scientific_milestone",
            "milestone_id": milestone_id,
            "artifact_inventory": ["formal_inputs", "old_measurements"],
            "predecessor": {
                "milestone_id": predecessor_value["milestone_id"],
                "raw_sha256": governance.raw_sha256(predecessor),
            },
            "reason": "replace a predeclared scientific boundary",
            "authority": "user-approved-amendment-A1",
            "affected_scope": ["threshold"],
            "evidence_reuse_boundary": {
                artifact_id: (
                    "reusable_formal_input"
                    if artifact_id == "formal_inputs"
                    else "diagnostic_only"
                )
                for artifact_id in predecessor_value["artifact_inventory"]
            },
            "payload": {"threshold": 0.4, "seeds": [1, 2]},
        }
    )


def strip_codex_mapping(text):
    start = "<!-- BEGIN CODEX RUNTIME MAPPINGS -->"
    end = "<!-- END CODEX RUNTIME MAPPINGS -->"
    before, remainder = text.split(start, 1)
    _, after = remainder.split(end, 1)
    combined = before + after
    while "\n\n\n" in combined:
        combined = combined.replace("\n\n\n", "\n\n")
    return combined


def test_bad_operational_bytes_are_preserved_and_corrected_deterministically():
    original = operational()
    before = bytes(original)
    first = correction(
        original,
        timestamp="2026-08-03T12:00:00Z",
        payload={"status": "running", "wall_s": 12},
    )
    second = correction(
        original,
        timestamp="2026-08-03T12:01:00Z",
        payload={"status": "complete", "wall_s": 15},
    )
    expected = {
        ("agent_run/example/command.json", "command-7"): {
            "status": "complete",
            "wall_s": 15,
        }
    }
    assert project([original], [second, first]) == expected
    assert project([original], [first, second]) == expected
    assert original == before


def test_correction_replay_rejects_duplicate_conflict_and_malformed_target():
    original = operational()
    event = correction(
        original,
        timestamp="2026-08-03T12:00:00Z",
        payload={"status": "running", "wall_s": 12},
    )
    with raises(governance.GovernanceError, match="share one timestamp"):
        project([original], [event, event])

    later = correction(
        original,
        timestamp="2026-08-03T12:00:01Z",
        payload={"status": "duplicate-resolved", "wall_s": 13},
    )
    assert project([original], [event, later, event])[
        ("agent_run/example/command.json", "command-7")
    ] == {"status": "duplicate-resolved", "wall_s": 13}

    conflict = correction(
        original,
        timestamp="2026-08-03T12:00:00Z",
        payload={"status": "complete", "wall_s": 12},
        reason="different correction",
    )
    with raises(governance.GovernanceError, match="share one timestamp"):
        project([original], [event, conflict])

    malformed = governance.strict_json_loads(event)
    malformed["target"]["raw_sha256"] = "0" * 64
    with raises(governance.GovernanceError, match="raw hash differs"):
        project([original], [encoded(malformed)])


def test_timestamp_order_equivalence_conflict_and_later_recovery():
    original = operational()
    at_zero = correction(
        original,
        timestamp="2026-08-03T12:00:00Z",
        payload={"status": "at-zero", "wall_s": 12},
    )
    at_point_one = correction(
        original,
        timestamp="2026-08-03T12:00:00.1Z",
        payload={"status": "at-point-one", "wall_s": 12},
    )
    assert project([original], [at_point_one, at_zero])[
        ("agent_run/example/command.json", "command-7")
    ]["status"] == "at-point-one"

    equivalent = correction(
        original,
        timestamp="2026-08-03T12:00:00.100000Z",
        payload={"status": "same-instant-conflict", "wall_s": 12},
        reason="same instant expressed differently",
    )
    with raises(governance.GovernanceError, match="share one timestamp"):
        project([original], [at_point_one, equivalent])

    recovery = correction(
        original,
        timestamp="2026-08-03T12:00:01Z",
        payload={"status": "resolved", "wall_s": 13},
        reason="supersede the conflicted timestamp group",
    )
    assert project([original], [equivalent, recovery, at_point_one])[
        ("agent_run/example/command.json", "command-7")
    ] == {"status": "resolved", "wall_s": 13}


def test_structured_projection_keys_cannot_collapse_distinct_targets():
    first = operational(path="a#b", sequence_or_id="c")
    second = operational(path="a", sequence_or_id="b#c")
    registry = layer_c_registry(
        layer_c_rule(path="a#b", sequence_or_id="c", rule_id="first"),
        layer_c_rule(path="a", sequence_or_id="b#c", rule_id="second"),
    )
    projected = project([first, second], [], registry)
    assert set(projected) == {("a#b", "c"), ("a", "b#c")}


def test_compact_registry_template_identity_and_unique_match_are_enforced():
    original = operational(sequence_or_id="command-7")
    registry = layer_c_registry(
        layer_c_rule(sequence_or_id_pattern=r"command-\d+")
    )
    assert project([original], [], registry)[
        ("agent_run/example/command.json", "command-7")
    ]["status"] == "runnng"

    registry_raw, registry_hash = registry
    with raises(governance.GovernanceError, match="identity differs"):
        governance.project_operational_records(
            [original], [], registry_raw, "0" * 64
        )

    ambiguous = layer_c_registry(
        layer_c_rule(sequence_or_id_pattern=r"command-\d+", rule_id="first"),
        layer_c_rule(sequence_or_id_pattern=r"command-7", rule_id="second"),
    )
    with raises(governance.GovernanceError, match="no unique sealed Layer-C rule"):
        project([original], [], ambiguous)


def test_correction_cannot_target_sealed_contract_lock_evidence_or_decision():
    original = operational()
    event = correction(
        original,
        timestamp="2026-08-03T12:00:00Z",
        payload={"status": "complete", "wall_s": 12},
    )
    for kind in ("contract", "lock", "formal_evidence", "decision"):
        target = governance.strict_json_loads(original)
        target["artifact_layer"] = "sealed_scientific_milestone"
        target["payload"] = {"kind": kind}
        target_raw = encoded(target)
        rewritten = governance.strict_json_loads(event)
        rewritten["target"]["raw_sha256"] = governance.raw_sha256(target_raw)
        with raises(governance.GovernanceError, match="not Layer C"):
            project([target_raw], [encoded(rewritten)])


def test_registry_not_self_label_controls_layer_c_and_scientific_fields():
    mislabelled = operational(
        {"threshold": 0.5},
        path="protocol/example-lock.json",
        sequence_or_id="lock-v1",
    )
    with raises(governance.GovernanceError, match="no unique sealed Layer-C rule"):
        project([mislabelled], [], layer_c_registry())

    for field in ("sample_inclusion", "execution_order", "measurement", "claim", "edge"):
        original = operational({"status": "running", field: "original"})
        registry = layer_c_registry(
            layer_c_rule(
                payload_leaf_pointers=("/status", f"/{field}"),
                correctable_leaf_pointers=("/status",),
            )
        )
        event = correction(
            original,
            timestamp="2026-08-03T12:00:00Z",
            payload={"status": "running", field: "rewritten"},
        )
        with raises(governance.GovernanceError, match="immutable Layer-C leaf"):
            project([original], [event], registry)

    nested = operational({"metadata": {"claim": "A"}, "status": "running"})
    nested_registry = layer_c_registry(
        layer_c_rule(
            payload_leaf_pointers=("/metadata/claim", "/status"),
            correctable_leaf_pointers=("/status",),
        )
    )
    nested_correction = correction(
        nested,
        timestamp="2026-08-03T12:00:00Z",
        payload={"metadata": {"claim": "B"}, "status": "running"},
    )
    with raises(governance.GovernanceError, match="immutable Layer-C leaf"):
        project([nested], [nested_correction], nested_registry)

    command_summary = operational({"input": "old-label", "status": "running"})
    summary_registry = layer_c_registry(
        layer_c_rule(
            payload_leaf_pointers=("/input", "/status"),
            correctable_leaf_pointers=("/input", "/status"),
        )
    )
    summary_correction = correction(
        command_summary,
        timestamp="2026-08-03T12:00:00Z",
        payload={"input": "correct-label", "status": "running"},
    )
    assert project([command_summary], [summary_correction], summary_registry)[
        ("agent_run/example/command.json", "command-7")
    ]["input"] == "correct-label"


def test_scientific_impact_cannot_use_operational_correction():
    original = operational()
    event = governance.strict_json_loads(
        correction(
            original,
            timestamp="2026-08-03T12:00:00Z",
            payload={"status": "complete", "wall_s": 12},
        )
    )
    event["scientific_impact"] = "changes_sample_inclusion"
    with raises(governance.GovernanceError, match="requires amendment or successor"):
        project([original], [encoded(event)])


def test_preseal_candidate_revision_selects_only_exact_complete_version():
    first = candidate(1, "complete", {"threshold": 0.5})
    second = candidate(2, "complete", {"threshold": 0.4})
    selected = governance.select_seal_candidate([first, second], governance.raw_sha256(second))
    assert selected["revision"] == 2
    assert selected["payload"] == {"threshold": 0.4}
    selected = governance.select_seal_candidate(
        [b"{}", second], governance.raw_sha256(second)
    )
    assert selected["revision"] == 2
    with raises(governance.GovernanceError, match="absent or ambiguous"):
        governance.select_seal_candidate([second, second], governance.raw_sha256(second))


def test_partial_or_missing_candidate_cannot_be_sealed():
    partial = candidate(3, "partial", {"threshold": 0.4})
    with raises(governance.GovernanceError, match="partial candidate"):
        governance.select_seal_candidate([partial], governance.raw_sha256(partial))
    with raises(governance.GovernanceError, match="absent or ambiguous"):
        governance.select_seal_candidate([partial], "0" * 64)


def test_sealed_milestone_changes_only_through_linked_amendment_or_successor():
    predecessor = sealed()
    accepted = governance.validate_sealed_transition(predecessor, successor(predecessor))
    assert accepted["event_type"] == "scientific_successor"
    second = successor(predecessor)
    third = successor(second, milestone_id="checkpoint-lock-v3")
    assert governance.validate_sealed_transition(second, third)["milestone_id"] == (
        "checkpoint-lock-v3"
    )
    direct_rewrite = sealed(payload={"threshold": 0.4, "seeds": [1, 2]})
    with raises(governance.GovernanceError, match="requires amendment or successor"):
        governance.validate_sealed_transition(predecessor, direct_rewrite)
    same_identity = successor(predecessor, milestone_id="checkpoint-lock-v1")
    with raises(governance.GovernanceError, match="overwritten in place"):
        governance.validate_sealed_transition(predecessor, same_identity)

    missing_reason = governance.strict_json_loads(successor(predecessor))
    del missing_reason["reason"]
    with raises(governance.GovernanceError, match="keys differ"):
        governance.validate_sealed_transition(predecessor, encoded(missing_reason))

    empty_authority = governance.strict_json_loads(successor(predecessor))
    empty_authority["authority"] = ""
    with raises(governance.GovernanceError, match="authority must be a nonempty string"):
        governance.validate_sealed_transition(predecessor, encoded(empty_authority))

    incomplete_reuse = governance.strict_json_loads(successor(predecessor))
    del incomplete_reuse["evidence_reuse_boundary"]["formal_inputs"]
    with raises(governance.GovernanceError, match="classify every artifact"):
        governance.validate_sealed_transition(predecessor, encoded(incomplete_reuse))

    invalid_reuse = governance.strict_json_loads(successor(predecessor))
    invalid_reuse["evidence_reuse_boundary"]["old_measurements"] = "reuse_everything"
    with raises(governance.GovernanceError, match="unknown classification"):
        governance.validate_sealed_transition(predecessor, encoded(invalid_reuse))


def complete_change_flags(**overrides):
    flags = {field: False for field in governance.ALL_CHANGE_FIELDS}
    flags.update(overrides)
    return flags


def test_bookkeeping_metadata_does_not_require_successor():
    assert governance.requires_successor(complete_change_flags()) is False
    assert governance.requires_successor(
        complete_change_flags(
            **{field: True for field in governance.BOOKKEEPING_CHANGE_FIELDS}
        )
    ) is False
    with raises(governance.GovernanceError, match="completely classify"):
        governance.requires_successor({})


def test_existing_scientific_semantics_remain_successor_boundaries():
    for field in ("seed", "workload", "threshold", "sample_inclusion", "claim"):
        assert governance.requires_successor(complete_change_flags(**{field: True})) is True
    policy = (REPO_ROOT / "study_docs/research/experiment-artifact-governance.md").read_text()
    assert "prospective and does not rewrite history" in policy
    assert "more specific sealed scientific contract wins" in policy


def test_every_scientific_boundary_change_requires_successor():
    for field in sorted(governance.SUCCESSOR_CHANGE_FIELDS):
        assert governance.requires_successor(complete_change_flags(**{field: True})) is True


def test_general_rules_and_workflow_have_live_policy_trigger():
    policy_path = "study_docs/research/experiment-artifact-governance.md"
    cursor_rule = (REPO_ROOT / ".cursor/rules/hipblaslt-onboarding.mdc").read_text()
    claude_rule = (REPO_ROOT / "CLAUDE.md").read_text()
    cursor_skill = (REPO_ROOT / ".cursor/skills/implement-verify-loop/SKILL.md").read_text()
    agent_skill = (REPO_ROOT / ".agents/skills/implement-verify-loop/SKILL.md").read_text()
    for text in (cursor_rule, claude_rule, cursor_skill, agent_skill):
        assert policy_path in text
        assert "sealed scientific milestone" in text.lower()
        assert "operational correction" in text.lower()


def test_cursor_claude_skill_parity_and_codex_standalone_inventory():
    surfaces = [".cursor", ".claude", ".agents"]
    relative_files = {
        "SKILL.md",
        "references/authority-gates.md",
        "references/planning-contract.md",
    }
    inventories = {}
    for surface in surfaces:
        root = REPO_ROOT / surface / "skills/implement-verify-loop"
        inventories[surface] = {
            path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
        }
        assert inventories[surface] == relative_files

    cursor_root = REPO_ROOT / ".cursor/skills/implement-verify-loop"
    claude_root = REPO_ROOT / ".claude/skills/implement-verify-loop"
    agent_root = REPO_ROOT / ".agents/skills/implement-verify-loop"
    for relative in sorted(relative_files - {"SKILL.md"}):
        assert (cursor_root / relative).read_bytes() == (claude_root / relative).read_bytes()
        assert (cursor_root / relative).read_bytes() == (agent_root / relative).read_bytes()
    assert (cursor_root / "SKILL.md").read_bytes() == (claude_root / "SKILL.md").read_bytes()
    assert strip_codex_mapping((agent_root / "SKILL.md").read_text()) == (
        cursor_root / "SKILL.md"
    ).read_text()


def test_design_discussion_mirrors_and_codex_port_remain_equivalent():
    cursor = (REPO_ROOT / ".cursor/skills/design-discussion/SKILL.md").read_text()
    claude = (REPO_ROOT / ".claude/skills/design-discussion/SKILL.md").read_text()
    agent = (REPO_ROOT / ".agents/skills/design-discussion/SKILL.md").read_text()
    assert cursor == claude
    assert strip_codex_mapping(agent) == cursor


if __name__ == "__main__":
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"PASS: {len(tests)} governance tests")
