---
name: implement-verify-loop
description: Orchestrate one scoped implementation or experiment step where Claude plans and adjudicates, a Codex agent explores + implements from a best-effort plan, and a second independent Codex agent verifies against the goal (not the steps). Finalize an evidence-backed report only after the goal is met; otherwise escalate honestly. Invoke manually when a design note or task spec has acceptance criteria and a report target. Do not use to invent an ambiguous design or silently weaken a locked protocol.
argument-hint: "<design-note-or-spec> [report-path]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Edit
  - Write
  - Bash
  - Agent
  - AskUserQuestion
  - mcp__codex__codex
  - mcp__codex__codex-reply
---

# Implement and Verify Loop (orchestrated)

You are the **orchestrator** (Claude). You do not write the feature code yourself. You select the step, prepare two plans, drive a **Codex implementer** and an **independent Codex verifier**, adjudicate, gate commits, and finalize the report.

This is deliberately lean. Keep the process proportionate to the work: a small CPU-only script does not need heavy machinery. The one place that gets extra rigor is an irreversible or expensive GPU benchmark run — see "GPU experiment pre-run freeze".

## Roles and rationale

- **Claude (orchestrator)** = the more reliable agent → planning, adjudication, report-writing, all gating. Default to delegating the exploration/spike + implementation to Codex — it has the budget; do not hand-spike yourself unless Codex genuinely can't.
- **Codex implementer** = the higher-budget agent → does the exploration/spike AND the implementation from a best-effort plan.
- **Codex verifier** = a *second, independent* Codex → judges goal achievement from the **goal plan only**, never the steps, so it cannot rubber-stamp the implementer's interpretation.

## Execution ownership (long-running / environment-restricted work is ALWAYS the orchestrator's — for both the implementer and the verifier)

A Codex subagent must never run — and never busy-wait inside its turn on — any execution that (a) its sandbox cannot reach (GPU/ROCm inside the `perlee` container, `rocprof`, kernel benchmarks, docker, network, license-gated tools) or (b) is long enough to risk a subagent turn timeout. That is what makes a subagent hang and time out. Instead:

- The subagent does only **bounded, single-turn** reasoning/implementation/analysis. When it needs such execution, it emits the **exact command(s) + expected checks** (as its terse return, or the verifier's `evidence_request`) and **ENDS its turn** — it does not wait for the result inside the turn.
- **The orchestrator (Claude) runs it** — in the background if long, waits for full completion, and cross-checks artifacts against raw outputs. For any run estimated at 30 minutes or more, honor the human gate (get approval before launching).
- The orchestrator then **RESUMES the same subagent thread via `mcp__codex__codex-reply`** with the results, and the subagent continues. Round-trip as many times as the step needs.
- Principle: **Claude is the conductor; Codex implements and verifies in short turns; every long-running or sandbox-blocked execution routes back to Claude.**

Read `references/agent-run-conventions.md` (two-plan contract, `agent_run/` layout, rotation, codex prompt settings) and `references/codex-review-contract.md` (verifier verdict object) before the first Codex call.

**Codex model policy.** Every `mcp__codex__codex` thread this loop starts (implementer or verifier) must explicitly pass the latest available Codex-capable model and `reasoning-effort: xhigh`; the current policy default is `model: gpt-5.6-sol`. If the requested model/effort is unavailable, stop and escalate instead of silently downgrading. Record the model and effort in `codex_threads.txt`.

## GPU experiment pre-run freeze (the only heavyweight gate, kept light)

For an **irreversible or expensive GPU/ROCm benchmark run** whose result will be interpreted (not a cheap re-runnable CPU check), do a light pre-run freeze **before launching**:

- Write into `plan_b.md` and snapshot in `agent_run/<run>/`: the exact workload set, seeds, metric definitions with their measurement boundary, and the success/failure/inconclusive criteria.
- Do not change these mid-run to fit the observed result. If the design genuinely must change, stop and go through `design-discussion` (user approval), then start a fresh run.

This is the whole gate — no machine-readable lock, no hash chain, no amendment ledger, no risk-tier taxonomy. Its only job is to stop an expensive run from being silently re-scoped after you see the numbers.

## Step 0 — Select, classify, baseline

1. Treat `$ARGUMENTS` as a design/experiment note path or a complete task spec; the optional second path is the target report. Resolve the report from an explicit argument, a unique link in the source note, or a unique milestone match. Ask if zero or multiple reasonable targets remain; never invent a report path.
2. Choose the next step. Prefer acceptance criteria and scope stated in the source note; ask when scope is ambiguous instead of inventing it.
3. **Plan as much as possible, then delegate — including exploration.** Give Codex the goal, concrete hypotheses/direction, file/code pointers, and decision criteria, and let it spike + implement within its budget. Do the spike yourself only when Codex genuinely can't (GPU/ROCm the sandbox can't reach, a human/scope decision, or a first move whose being wrong is expensive).
4. Record the baseline: `git status --short` for the parent repo and every relevant submodule, plus pre-existing untracked files. Preserve unrelated user changes; never reset/checkout/stash/overwrite them.

## Step 1 — Two plans (spawn two Claude sub-agents)

Spawn two Claude sub-agents with the `Agent` tool. The defining property: **Plan-B is written from the goal, independently of Plan-A**, so the verifier oracle is not contaminated by the implementer's chosen steps. Write both into the run directory.

- **Plan-A — implementation plan** (for the implementer Codex): as detailed as the step allows — step-perfect where you can pin it, best-effort where you can't (goal + hypotheses/direction + code pointers + decision criteria, with the implementer told to spike it). Always include a **file whitelist (or whitelist scope)**, the **verification commands** (flag any the implementer's sandbox can't run — GPU/ROCm/docker — which the orchestrator runs and feeds back), and the exact `agent_run/<run>/` output path + report format.
- **Plan-B — goal/oracle plan** (for the verifier Codex), **frozen at run start**: the main objective; the desired end-result/acceptance (the headline check the verifier must independently reproduce); the explicit **unacceptable fallbacks**; and the envisioned directions from current state → goal. No step-level detail. For a GPU experiment, Plan-B also carries the pre-run freeze fields above.

## Step 2 — Implementer Codex

Start a Codex thread with `mcp__codex__codex`: `cwd` = repo root, `sandbox: workspace-write`, `approval-policy: never`, `include-plan-tool: false`. Do not pass `base-instructions`. Prompt = **Plan-A only** + instruction to use the `script-development` / `experiment-report-writing` `.codex` skills as relevant, edit **only whitelisted files**, do any exploration/spike Plan-A leaves open (recording each decision + its reason in `impl_report.md`), run the verification commands it can, and write `agent_run/<run>/impl_report.md`. For verification its sandbox cannot run (GPU/ROCm/docker), it emits the exact commands + expected checks; the orchestrator runs them and feeds results back via `mcp__codex__codex-reply`.

Tell it to **write the full report to `impl_report.md` and return only a terse status + changed-file list + report path** — not the report re-narrated inline.

After it returns: capture the full post-implementation diff vs baseline (parent + submodules). If anything changed outside the whitelist, stop and show the delta — never auto-revert.

## Step 3 — Verifier Codex (independent)

Start a **fresh** Codex thread (never reuse the implementer thread). Prompt = **Plan-B (frozen) + the implementer diff/artifacts only — NOT Plan-A** + the initial-review prompt from `references/codex-review-contract.md`. Default `sandbox: read-only`, `approval-policy: never`, `include-plan-tool: false`; grant `workspace-write` only if a fresh reproduction of the headline check needs it (record which). Require it to use `code-change-verification`, judge goal achievement against Plan-B's goal + unacceptable-fallbacks **primarily from the actual code/artifacts** (treat the impl report as a claim to check), **run its own fresh reproduction** of the headline check, and write `agent_run/<run>/verify_report.md` + `verdict.json`. Its returned message must be terse — `verdict` / `goal_alignment` / blocking-count + the `verdict.json` path.

If the verifier needs a write-producing or GPU command it cannot run, it returns an `evidence_request`; you run the approved command, record exact command/cwd/exit/artifacts, and continue the thread with `mcp__codex__codex-reply`.

## Step 4 — Adjudicate + terminal states

- **Consistent** (`verdict: PASS`, `goal_alignment: FULL`, no unacceptable fallback, experiment complete or not applicable): update the **milestone source-of-truth** (see below), then **pause for per-instance commit authorization** → on go, commit → proceed.
- **Not consistent:** analyze Plan-A, Plan-B, both Codex reports, and the docs.
  - **Cannot determine who is right → escalate to the user.**
  - **Can determine →** record only durable, scope-changing conclusions in the design/experiment docs (transient back-and-forth stays in `agent_run/`). Adjust Plan-A; change Plan-B only if the **goal itself** was wrong. Re-loop from Step 2.
- **Honest exits (do not fake convergence):**
  - At most **5** implement→verify iterations per run; stop earlier if the same blocking finding recurs twice without material progress → escalate.
  - **Goal correct but out-of-scope / over-budget** → stop and escalate with the honest partial.
  - **Inconclusive** — when the evidence cannot converge within the reachable workload, record "inconclusive" rather than declaring a winner. This is a valid finish, not a failure.

**Milestone sync (every terminal outcome — required before finishing).** After any run reaches a terminal state, bring the **milestone source-of-truth** into sync with the actual outcome:

- the resolved experiment report at its target path;
- the governing experiment plan/guide under `study_docs/research/` (revise the relevant checkpoint's current-state in place — done/achieved-with-scope, or partial + open items; do not append run history there — transient detail stays in `agent_run/`).

Do not leave the canonical experiment doc stale.

## Doc-writing standard (every doc this loop writes)

Apply `experiment-report-writing` for reports and its **readability rule** to the two plans, impl/verify reports, and the experiment report:

- **Do not hard-wrap for column width.** No line break inside a phrase, inside inline code, or before a sentence's meaning is complete. Each physical line carries a complete thought.
- **One idea per line.** Do not chain 3+ facts into one bullet via `，` / `；` / `（…）` / `——` / bold fragments.
- **At most one `（…）` per sentence.** Move extra asides into sub-bullets.
- **Nested structure for any multi-part claim**; anchor each headline number on its own line.
- **Chinese-English half-width spacing**, but keep identifiers, paths, hashes, commands, and fenced code byte-for-byte.

## Metric & conclusion standard (every plan, verdict, and adjudication)

- **Lead with decision-fidelity.** For ranking / DSE / fidelity steps, Plan-B's acceptance and the verifier's judgement lead with top-1 / top-2 / top-k and Pareto / best-config; rank-correlation (Spearman / Kendall) and absolute error are secondary. A verdict led on a secondary metric while the decision-key metric is tied is invalid.
- **Require metric comparability.** Predicted and ground-truth metrics must measure the same quantity over the same boundary (compute / DMA / scheduling / overlap; clock domain). A gap that exists only because the metrics are not comparable is an artifact, not a finding.
- **No conclusion from thin/narrow evidence.** Do not conclude "X better/correct" from a single dataset, a few cells, one metric, or with no mechanism. If the reachable workload cannot converge, the honest terminal state is **inconclusive**.
- **Guard the premise.** Because Codex does the exploration, the verifier must confirm the mechanism/reasoning is sound — not merely that the headline number appeared. A result that reaches the goal via a wrong premise is a failure, not a pass.

## Context-economy standard

The full record lives in files under `agent_run/<run>/`; the parent's context must not fill with it.

- **The record is the file; the return is a pointer.** Every agent's returned message is a one-line status, terminal verdict fields, and artifact **paths** — not the full report re-narrated or the verdict JSON pasted inline.
- **Don't re-paste large blobs.** The orchestrator reads big artifacts with file tools and quotes only load-bearing lines.
- **Checkpoint between milestones.** Prefer a fresh session/context for the next milestone rather than running many back-to-back in one ever-growing context.

## `agent_run/` (see `references/agent-run-conventions.md`)

One directory per run at `<repo root>/agent_run/YYMMDD-{feature-slug}[-N]/`, **gitignored**. Holds `plan_a.md`, frozen `plan_b.md`, `impl_report.md`, `verify_report.md`, `verdict.json`, `adjudication.md`, `codex_threads.txt`. **Rotation:** keep the 5 most recent run dirs; delete only the oldest dirs you created under `agent_run/` — the one sanctioned auto-delete; never touch anything else. Confirm `agent_run/` is gitignored with `git check-ignore` before use.

## Human gates (always pause)

- Commit, push, dependency install, network access, credential use, or any external-system write.
- A destructive operation, or a file move/rename/delete outside `agent_run/` rotation.
- Any command or experiment estimated at 30 minutes or more.
- Starting, stopping, restarting, recreating, or mutating the `perlee` container.
- An operation overlapping unrelated pre-existing user changes, or any change outside the agreed whitelist.
- A claim whose acceptance criterion, evidence source, or report target is ambiguous.

After approving a long experiment, wait for every planned run to finish successfully, verify all expected runs exist in the final result files, and cross-check reported metrics against raw artifacts. Never finalize a verdict or report from partial, timed-out, killed, or still-running output.

## Finish

Finish only when the verifier returns goal-met with full evidence, every planned run is complete, the milestone source-of-truth is synced (report + the governing `study_docs/research/` plan reflect the outcome), and the commit gate has been honored. Return a concise Traditional Chinese summary: report path, the doc update, changed behavior, verifier commands/outcomes, evidence boundary, remaining non-blocking risks, the run directory, and the final Codex verdict — and, if escalating, the honest partial and the open decision.
