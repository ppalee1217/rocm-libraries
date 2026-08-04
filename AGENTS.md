# Codex / Agent Repository Guidance

## Role

In this repository Claude Code is the main orchestrator and Codex normally runs as a
**subagent** it drives (via `.mcp.json`): a Codex thread does short, bounded implementation
or verification turns, while every GPU/ROCm, docker, network, or long-running command is
executed by the orchestrator and fed back into the Codex thread.

## Repository-wide general rule

- The canonical repository-wide rules live in [`CLAUDE.md`](CLAUDE.md). Read it completely
  and apply its Markdown body as repository-wide guidance, regardless of which agent runtime
  you are in.
- Treat `CLAUDE.md` and this `AGENTS.md` as carrying the same substantive rules. If they ever
  diverge, `CLAUDE.md` is authoritative for the general rules.
- Key rules to apply (see `CLAUDE.md` for full text): the readability rules and reader-facing
  clarity contract; GEKO/Ductile source-branch authority; experiment execution and reporting
  discipline (including the light GPU pre-run freeze); metric selection and comparability;
  conclusion discipline; the GPU/ROCm `perlee`-container execution rule; the code reference
  rule; and scope control.

## Instruction layering

- Also follow any more specific `AGENTS.md` found between the repository root and the current
  working directory.
- In particular, work under `projects/hipblaslt/` and `projects/hipblaslt/tensilelite/` must
  follow their existing nested `AGENTS.md` files. Do not modify those official files.

## Skills

- The canonical skills are under `.claude/skills/`. Codex subagents apply the matching copies
  under `.codex/skills/` for report writing, code-change verification, and script work:
  - `experiment-report-writing`
  - `code-change-verification`
  - `script-development`
- The orchestration skills `implement-verify-loop` and `design-discussion` are driven by the
  Claude orchestrator, which tells each Codex subagent which `.codex` skill to apply and where
  to write its artifacts.

## Legacy

- The `.cursor/` and `.agents/` directories are retained as legacy from the previous
  Cursor / Codex-orchestrator workflow. They are no longer the canonical source and need not be
  kept in sync with `.claude/` or `.codex/`. Do not route work through them or edit them as part
  of normal work.
