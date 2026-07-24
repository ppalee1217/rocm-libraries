# Repository onboarding role

The primary reader is a new engineer (short-term internship) ramping up on
`projects/hipblaslt` and its in-repo kernel generator `tensilelite`. The learning
path is sequential: code trace -> understand the overall workflow -> optimize a GEMM
kernel -> verify the speedup with rocprof and TensileLite benchmarks. Assume limited
prior context; explanations must build up from the basics.

# Language

- Use Traditional Chinese for general communication and for onboarding / learning docs.
- Keep technical terms, proper nouns, function names, file names, and tool names in English.
- Do not force English technical terms into uncommon Chinese translations.

# Writing and reasoning standards

- Lead with a plain-language overview before technical detail; do not hide reasoning behind jargon.
- Define each project-specific or domain term the first time it appears.
- Keep explanations self-contained: a reader should not need prior chats, PRs, or unstated assumptions.
- Be evidence-based and avoid overstated conclusions.
- Avoid long multi-fact `>` blockquotes; they read poorly. Reserve `>` for a single short
  callout idea. When a point carries multiple facts, use a plain lead sentence followed by a
  bullet list instead of a multi-line blockquote.

## Experiment execution, conclusion, and downgrade discipline

### Wait for complete evidence

- Do not write a final experiment report, finalize interpretation, or mark an implementation
  complete while any required run, data collection, simulation, or background job is still
  running, missing, or unverified.
- Report final metrics only from final result files cross-checked against raw artifacts. Do not
  use partial, interim, or still-changing output as the final result.
- Independent work may continue while jobs run, but the gated result, verdict, report, and
  completion status must wait. If an early report is explicitly required, label it
  `partial` / `in-progress` and list every pending run and unavailable conclusion.

### Verify every milestone before starting the next

- When a specification defines ordered or dependent milestones, work on exactly one active
  milestone at a time: implement it, independently verify it, fix and re-verify it, and only
  then consider a downstream milestone.
- Do not ask one implementer to build multiple milestones and verify them only after the batch.
  Do not modify downstream milestone files speculatively while an upstream milestone is still
  unverified.
- `CHANGES_REQUIRED`, `BLOCKED`, `FAIL`, missing evidence, or a still-running verification stops
  that dependency path. Advance only after the current milestone verifier returns `PASS`, or
  along a different branch that the design explicitly authorizes from a verified gate outcome.
- A broad request such as "implement all milestones" authorizes the full sequence, not a single
  batch implementation. Preserve a separate baseline, scope, plan, evidence set, and verdict for
  every milestone.

### GPU and ROCm execution environment

- Run every GPU- or ROCm-dependent command only inside the Docker container named exactly
  `perlee`. This includes hardware probes and ROCm builds/tests/tools such as `rocminfo`,
  `rocm_agent_enumerator`, `hipcc`, `amdclang++`, `rocprof`, kernel generation, compilation,
  benchmarks, and correctness/noise runs. Do not run these commands on the host.
- Target only `perlee` in Docker commands. Never enumerate, inspect, enter, start, stop, restart,
  pause, unpause, rename, remove, copy to/from, or otherwise touch any other user's container.
- Do not start, stop, restart, recreate, or mutate the `perlee` container itself without the
  user's explicit approval. Dependency installation remains a separate human gate.
- If `perlee` is unavailable, stopped, lacks the repository mount or GPU access, or rejects the
  command, stop and ask the user. Never substitute the host or another container.

### Do not over-conclude

- A hypothesis and expected direction come before the result, but remain hypotheses until
  multiple repeated and diverse workloads provide convergent evidence.
- Never declare a winner or a component irrelevant from one dataset, a few narrow workloads,
  a single metric, or an unexplained result. If reachable evidence is too narrow or does not
  converge, the verdict is `inconclusive`.
- Reason forward from the original design purpose: explain what a component or effect is for
  and what omitting it could cost. A local observation such as "unused on this path" or "no
  effect in this run" is evidence about that scope only, not proof that it is unimportant.
  Record omitted-but-relevant effects as tracked gaps.
- Before accepting a result, check confounders, setup artifacts, workload coverage, assumptions,
  and a plausible mechanism. State the measurement boundary, sample size, repetitions, metrics,
  and what the result cannot support.

### Downgrades require the user's decision

- Never autonomously downgrade an experiment or implementation. A downgrade includes reducing
  workloads, runs, seeds, metrics, validation, acceptance criteria, or scope; replacing an
  original baseline with a proxy; skipping a milestone; or converting a planned confirmation
  into a smoke test, pilot, exploratory run, or weaker claim.
- When a downgrade may be needed, pause that decision and give the user a decision packet:
  1. the experiment design and setup;
  2. the experiment goal and planned evidence;
  3. completed, running, and missing work;
  4. the problem encountered, supporting evidence, and root cause if known;
  5. why a downgrade is being considered and how it changes statistical power, comparability,
     acceptance criteria, and allowed claims;
  6. alternatives that preserve the original plan, with expected time, resource, and risk;
  7. a recommendation, clearly separated from the user's final choice.
- Until the user chooses, mark the step `blocked-awaiting-user-decision`; do not silently apply
  the downgrade or interpret partial evidence as final. If approved, record the user's decision,
  rationale, changed scope, and limitations. Approval to downgrade never permits over-claiming.

# Code reference rule

- Cite every concrete code location as a markdown link with a line anchor, using a path
  relative to the current document, e.g. `[runContractionProblem](../../path/to/tensile_host.cpp#L3235-L3463)`.
- Link text is the symbol or function name; the URL carries the path and `#Lstart-Lend`.
- Do not paste bare absolute paths inline; they are noisy and hard to read.
- Verify line numbers against the current code before citing (they drift across commits).
  If unsure, link the file without a line anchor rather than guess.

# Scope control

- Do not modify the official `projects/hipblaslt/AGENTS.md` or
  `projects/hipblaslt/tensilelite/AGENTS.md`; follow them for build and PR conventions.
  This rule only adds learning / onboarding guidance on top.
- Do not delete, move, or rename files unless explicitly requested.

# Skill pointer

When writing, editing, reviewing, or restructuring an onboarding or code-trace report
(a user guide that helps a reader quickly understand the repo), use the
`hipblaslt-code-trace` skill at `.claude/skills/hipblaslt-code-trace/SKILL.md` for the
report structure and conventions.

# Learning roadmap: canonical + mirrors (keep in sync)

The 8-week internship learning roadmap exists in three places. The **canonical**
(only-edit) copy is `study_docs/learning-roadmap.md`. The other two are **read-only
mirrors**: the Claude Code plan file
(`~/.claude/plans/rocm-libraries-repo-familiar-starry-aurora.md`) and
`.cursor/learning-roadmap.md`.

- Always edit `study_docs/learning-roadmap.md`, never a mirror.
- Inside Claude Code, a PostToolUse hook (in `/data1/perlee/.claude/settings.json`)
  auto-copies the canonical file to both mirrors on every edit.
- The hook does NOT fire when editing in Cursor or when editing a mirror directly.
  In those cases, manually sync: copy `study_docs/learning-roadmap.md` over both mirrors.

# Learning notes must mirror the full daily roadmap

Each daily study note (`study_docs/notes/MMDD-*.md`) is what the learner reads to decide
what to do that day, so its "對應 roadmap item" section MUST list EVERY item from that
day's roadmap section — nothing dropped:

- Every main item, all of its sub-bullets, and its `✅ 完成判準` line.
- ALL optional / recommended items too — `（AMD 資源，選做）`, `（全程指引，建議）`,
  `（選讀／按需）` — copied verbatim WITH their tag kept, so the learner sees what is
  skippable but never misses that it exists. Never omit an item just because it is optional.
- Preserve the roadmap's checkbox state (`- [x]` done / `- [ ]` not done).
- Carry each item's `📚 參考資源` too, not just the item text: put an inline `📚 參考資源：...`
  line under the item AND consolidate the same links in the bottom "code & doc 參考" section
  (dual-track). Only link files that exist. A missing reference means the learner does not
  know where to look it up.

A missing item in the note means the learner silently skips that work. Use the
`learning-notes` skill as the authoritative procedure; when creating or reviewing a note,
verify its "對應 roadmap item" list matches the roadmap section one-for-one.

# Claude / Cursor parity (rules and skills MUST stay in sync)

This repo is driven from both Claude Code and Cursor, so the agent instructions are
duplicated on each side. Every Claude-side file has a Cursor-side counterpart, and the
two must always carry the same content:

- General rules: `CLAUDE.md` ↔ `.cursor/rules/hipblaslt-onboarding.mdc`
  (same substantive rules; only the `.mdc` frontmatter and a few platform-specific
  notes — e.g. how the auto-sync hook behaves — may differ in wording).
- Skills: `.claude/skills/<name>/SKILL.md` ↔ `.cursor/skills/<name>/SKILL.md`
  (byte-identical — no platform-specific content).

Rule: whenever you edit one side — your own general rule OR any SKILL — apply the
same change to its counterpart **in the same task**. Never leave the two out of sync.
After editing, `diff` the pair to confirm (skills must be byte-identical; the rule
files must match in substance, allowing only frontmatter / platform-specific wording).

Note: `.claude/` and `.cursor/skills/` sit outside the sparse-checkout cone, so staging
them needs `git add --sparse`.
