# Agent-run conventions

The orchestrator (Claude) owns these conventions and injects the relevant parts into each Codex prompt. The Codex subagents read the repo's `.codex/skills/` for report/verification/script conventions; the orchestrator names the output paths, report formats, and which `.codex` skill each Codex agent should apply, so there is one source of truth.

## Run directory

- Root: `<repo root>/agent_run/` (gitignored; ephemeral).
- Per run: `agent_run/YYMMDD-{feature-slug}/` (`feature-slug` = lowercase kebab summary of the step). Append `-2`, `-3`, … only on a same-day same-feature collision.
- Contents (orchestrator creates the dir and the two plans; Codex agents write their own reports there):
  - `plan_a.md` — implementation plan (Step 1).
  - `plan_b.md` — goal/oracle plan, **frozen at run start** (Step 1). For a GPU experiment it also carries the pre-run freeze fields (workload set, seeds, metric definitions + boundary, success/failure/inconclusive criteria).
  - `impl_report.md` — implementer Codex's report (Step 2).
  - `verify_report.md` + `verdict.json` — verifier Codex's report + the contract verdict (Step 3).
  - `adjudication.md` — orchestrator's per-iteration adjudication + terminal decision (Step 4).
  - `codex_threads.txt` — one line per Codex thread: `role  model  reasoningEffort  threadId`.

The `agent_run/` dir holds the run's transient record only. The durable status of the milestone lives in the experiment report + the governing `study_docs/research/` plan/guide, which the SKILL's "Milestone sync" gate requires you to update before finishing.

Every doc the loop writes — the two plans, the impl/verify reports, and the report/notes — must follow the SKILL's **Doc-writing standard**: no hard-wrapping for column width; one idea per line; nested bullets; no bullet chaining 3+ facts via `，` / `；` / `（…）` / `——`.

## Rotation

Keep the **5 most recent** run directories. The orchestrator deletes only the oldest directories it created under `agent_run/` (matched by the `YYMMDD-{feature-slug}` pattern). This is the single sanctioned auto-delete; never delete anything outside `agent_run/`, and never delete a dir from the current run.

## Plan-A — implementation plan (implementer Codex input)

As detailed as the step allows — step-perfect where you can pin it, best-effort where you can't (goal + hypotheses/direction + code pointers + decision criteria, with the implementer told to spike it). Required sections:

- **File whitelist** — the exact set of files (or, for an exploratory step, the whitelist *scope*) the implementer may create/modify. Editing outside it is a violation the orchestrator will stop on.
- **Per-file changes** — exact edits (functions, anchors, intended diff), referencing existing utilities/patterns to reuse. For an exploratory step, this section instead gives the spike goal/direction + which files/functions to investigate; the implementer explores and records the actual changes it made (and why) in `impl_report.md`.
- **Verification commands** — the exact commands the implementer must run to self-check, with expected observable outcomes (exit codes, key strings, artifact paths). Flag any command the implementer's sandbox cannot run (GPU/ROCm inside `perlee`, docker, network); the orchestrator runs those and feeds results back.
- **Output** — write `impl_report.md` to this run dir with: what changed per file, the commands run with exit codes, artifact paths, anything it could not do, and any place it had to deviate from Plan-A (deviation must be reported, not hidden).

## Plan-B — goal / oracle plan (verifier Codex input, frozen)

Goal-only; **no step-level detail** (so the verifier judges intent, not steps). Required sections:

- **Main objective** — what this change is fundamentally for.
- **Desired end-result / acceptance** — the observable end state and how to confirm it (the headline acceptance check the verifier must independently reproduce).
- **Unacceptable fallbacks** — explicit outcomes that must NOT be accepted as success (for example: claiming a proven spec counts as the end-to-end result; a partial that silently drops a required case; declaring a winner from a thin/narrow workload or a single metric). This is the verifier's objective veto list.
- **Directions current → goal** — the envisioned routes from the current state to goal-achieved, precise enough to orient the verifier without prescribing the implementer's steps.
- **GPU pre-run freeze (GPU experiments only)** — the frozen workload set, seeds, metric definitions with measurement boundary, and success/failure/inconclusive criteria.

`plan_b.md` is frozen at run start. Change it only if adjudication concludes the **goal itself** was wrong, and record that conclusion in the design/experiment docs; a frozen GPU pre-run freeze changes only via `design-discussion` (user approval) and a fresh run.

## Codex prompt conventions (orchestrator injects)

- **All Codex starts:** every `mcp__codex__codex` call must explicitly pass the latest available Codex-capable model and `reasoning-effort: xhigh`; the current policy default is `model: gpt-5.6-sol`. If the requested model/effort is unavailable, stop and escalate instead of silently downgrading. Record both values in `codex_threads.txt`.
- **Implementer:** `sandbox: workspace-write`, `approval-policy: never`, `include-plan-tool: false`, no `base-instructions`. Prompt = Plan-A only. Tell it the file whitelist, the verification commands, the `impl_report.md` path, and which `.codex` skill to apply (`script-development` for scripts/reproducible commands, `experiment-report-writing` where a report fragment is produced).
- **Verifier:** fresh thread, `sandbox: read-only` (or `workspace-write` only if a fresh reproduction needs it), `approval-policy: never`, `include-plan-tool: false`, no `base-instructions`. Prompt = Plan-B (frozen) + the implementer's diff/artifacts + the initial-review prompt from `codex-review-contract.md`. Tell it to use `code-change-verification`, judge against Plan-B's goal + unacceptable-fallbacks from the actual code/artifacts, run its own fresh reproduction of the headline check, and return exactly one verdict object plus `verify_report.md`.
- GPU/ROCm commands never run inside a Codex turn; the orchestrator runs them in the `perlee` container and feeds results back via `mcp__codex__codex-reply`.
