---
name: implement-verify-loop
description: >-
  Implements, independently verifies, reports, and commits exactly one stable
  checkpoint indexed by an authoritative parent experiment plan, using two
  independent planners, a fresh implementer, and a fresh verifier. Routes
  consequential design issues through two additional fresh design-discussion
  subagents until both confirm one consensus. For a multi-checkpoint
  experiment, repeats the full plan → implement → verify/fix → report → parent
  update → closeout audit → commit loop sequentially; never starts downstream
  work before the active checkpoint is committed and audited. Use for
  experiment checkpoints with complete acceptance criteria and report targets.
  Do not use for initial design, rules maintenance, trivial edits, or ambiguous
  goals.
---

# Implement and Verify Loop

Before taking task action, read the canonical workflow in
[`../../../.cursor/skills/implement-verify-loop/SKILL.md`](../../../.cursor/skills/implement-verify-loop/SKILL.md)
completely. Follow it with these Codex runtime mappings:

- Treat `$ARGUMENTS` as the current user request plus any explicitly named
  design note, specification, scope, or report path.
- Treat `AskQuestion` as asking the user a concise direct question through the
  input mechanism available in the current Codex mode.
- Map `model: gpt-5.6-sol-xhigh` to `model: gpt-5.6-sol` with
  `reasoning_effort: xhigh`.
- Use `fork_turns: none` for every fresh subagent and provide the complete
  role-specific prompt and artifact paths explicitly.
- Issue the two planner `spawn_agent` calls before waiting for either result.
- Treat `resume` as `followup_task` addressed to the same saved implementer,
  verifier, or planner agent ID.
- Record the Codex task name or agent ID wherever the canonical workflow asks
  for an agent link or ID.
- If the required model or subagent tools are unavailable, stop and report the
  limitation as required by the canonical workflow.

Apply every other sequencing gate, independence rule, whitelist, evidence
requirement, human gate, and completion condition from the canonical workflow
unchanged.
