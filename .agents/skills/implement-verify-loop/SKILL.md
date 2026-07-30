---
name: implement-verify-loop
description: >-
  Executes risk-tiered engineering and experiment work from an approved design
  using one transient execution plan, a durable machine-readable frozen
  contract, six-round repair, and independent verification. Preserves hard
  scientific gates while allowing compatible gates to share an execution
  tranche and terminal closeout. Use for preregistered checkpoints with clear
  acceptance, evidence, authority, and report targets. Do not use to invent an
  ambiguous design or silently weaken a locked protocol.
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
- The canonical workflow uses one execution planner by default. When it calls
  for a paired design or operational review, issue both reviewer
  `spawn_agent` calls before waiting for either result.
- Treat `resume` as `followup_task` addressed to the same saved implementer,
  verifier, or planner agent ID.
- Record the Codex task name or agent ID wherever the canonical workflow asks
  for an agent link or ID.
- If the required model or subagent tools are unavailable, stop and report the
  limitation as required by the canonical workflow.

Apply every other sequencing gate, independence rule, whitelist, evidence
requirement, human gate, and completion condition from the canonical workflow
unchanged.
