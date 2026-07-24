---
name: design-discussion
description: Uses two independent GPT-5.6 Sol subagents to deliberate experiment or implementation design, repeatedly cross-examine assumptions and evidence until both explicitly confirm one consensus, and preserve the resulting decision for the governing design and experiment report. Use for experiment design, architecture or approach selection, hypothesis validation strategy, ambiguous result interpretation, unexpected implementation or verification design issues, and other consequential design-direction decisions. Do not use for lookups, mechanical edits, implementation execution, or choices with an obvious conventional default.
---

# Design Discussion

Before taking task action, read the canonical workflow in
[`../../../.cursor/skills/design-discussion/SKILL.md`](../../../.cursor/skills/design-discussion/SKILL.md)
completely. Follow it with these Codex runtime mappings:

- Treat `$ARGUMENTS` as the current user request plus any explicitly named
  target document.
- Treat `AskQuestion` as asking the user a concise direct question through the
  input mechanism available in the current Codex mode.
- Map `model: gpt-5.6-sol-xhigh` to `model: gpt-5.6-sol` with
  `reasoning_effort: xhigh`.
- Use `fork_turns: none` when spawning the two fresh subagents so they receive
  only the identical, self-contained prompt prepared by the main agent.
- Issue both `spawn_agent` calls before waiting for either result.
- Treat `resume` as `followup_task` addressed to the same saved agent ID. Do
  not replace an existing debate participant with a new subagent.
- If the required model or subagent tools are unavailable, stop and report the
  limitation as required by the canonical workflow.

Apply every other instruction, gate, evidence rule, document-lifecycle rule,
and completion condition from the canonical workflow unchanged.
