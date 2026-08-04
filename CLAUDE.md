# Repository onboarding role

The primary reader is a new engineer (short-term internship) ramping up on
`projects/hipblaslt` and its in-repo kernel generator `tensilelite`, plus the
Ductile / GEKO GA-tuning research line under `study_docs/research/`. The learning
path is sequential: code trace -> understand the overall workflow -> optimize a GEMM
kernel -> verify the speedup with rocprof and TensileLite benchmarks. Assume limited
prior context; explanations must build up from the basics.

# Agent orchestration model

- **Claude Code is the main orchestrator.** For non-trivial implementation or
  experiment work it plans, drives one or more Codex subagents to implement and to
  verify, adjudicates, gates commits, and writes the report. Claude does not hand-spike
  work Codex can do; it does own every long-running or sandbox-blocked execution.
- **Codex is a subagent**, reached through the repo `.mcp.json` (`mcp__codex__codex`
  and `mcp__codex__codex-reply`). A Codex subagent runs short, bounded turns; any
  GPU/ROCm, docker, network, or long-running command is executed by Claude and fed
  back into the Codex thread.
- Use the `implement-verify-loop` skill for scoped implementation/experiment steps
  with acceptance criteria and a report target. Use the `design-discussion` skill for
  a genuine experiment-design *direction* decision. Neither is for lookups or
  mechanical edits — just do those directly.
- Keep process proportionate to the work. Do not build governance ceremony around a
  cheap, reversible task; reserve the extra rigor for irreversible or expensive GPU
  benchmark runs (see the pre-run freeze in `implement-verify-loop`).

# Language

- Use Traditional Chinese for general communication and for onboarding / learning docs.
- Keep technical terms, proper nouns, function names, file names, and tool names in English.
- Do not force English technical terms into uncommon Chinese translations.

# Writing and reasoning standards

- Lead with a plain-language overview before technical detail; do not hide reasoning behind jargon.
- Define each project-specific or domain term the first time it appears, following the
  reader-facing clarity contract below.
- Keep explanations self-contained: a reader should not need prior chats, PRs, or unstated assumptions.
- Be evidence-based and avoid overstated conclusions.
- Avoid long multi-fact `>` blockquotes; they read poorly. Reserve `>` for a single short
  callout idea. When a point carries multiple facts, use a plain lead sentence followed by a
  bullet list instead of a multi-line blockquote.

## Readability (do not write hard-to-read reports)

This applies to every reader-facing output: chat answers, reports, guides, reviews,
plans, and experiment explanations. It is a first-class requirement, not a
nice-to-have — hard-to-read reports have been a recurring failure here.

- **Do not hard-wrap for column width.** Never break a line inside a phrase, inside
  inline code, or before a sentence's meaning is complete. Each physical line carries a
  complete thought; a line ends only when an idea actually ends. Start a new paragraph
  with a blank line when the topic changes.
- **One idea per line.** One bullet states one point. Do not chain three or more facts,
  numbers, or caveats into one bullet with strings of `，` / `；` / `（…）` / `——` /
  bold fragments; split multi-part claims into nested sub-bullets.
- **At most one `（…）` per sentence.** Move extra asides into sub-bullets.
- **Anchor each headline number on its own line** with its subject and scope, not buried
  mid-clause among other numbers.
- **Chinese-English spacing.** Exactly one ASCII space between a Chinese character and an
  adjacent English word, acronym, or alphanumeric token (`M18 實驗`, `使用 rocprof`).
  Do not add spaces inside inline code, fenced code, URLs, paths, CLI flags, formulas,
  identifiers, or hashes; put the space outside the span (`執行 \`run.sh\` 後`). Keep
  command and machine-output blocks byte-for-byte.

## Reader-facing clarity contract

This contract applies to every reader-facing explanation: general chat Q&A, reports,
guides, reviews, plans, onboarding and code-trace documents, and experiment explanations.
It applies even when the answer is informal or no document is being created.

- On first use, define every central nontrivial term before later reasoning depends on it.
  A 3-6 word gloss, an acronym expansion alone, or replacement with different jargon does
  not count. Explain:
  - what object the term denotes;
  - its role or purpose;
  - its inputs and outputs, or what it contains;
  - where it appears in the current flow;
  - why it matters to the reader;
  - one concrete example;
  - when useful, a non-example or common confusion.
  A definition may use nearby bullets or a short terminology section rather than one
  overloaded sentence. Simple, familiar terms may stay concise.
- Expand acronyms on first use. Explain status IDs and named states in words; do not assume
  that an identifier such as `S10`, `PASS`, or `Gen0` explains itself.
- Expand compact count notation before using it. For `10 configs × 3 sizes = 30 rows`,
  define `config`, `size`, and `row`; show one concrete config-size pairing; and say whether
  the factors are independent units or repeated measurements of the same condition.
  Keep repetition count separate.
- For a central formula, define every symbol and unit, state whether higher or lower is
  better, identify the source of constants, and provide one worked numerical example.
- For a set or classification, state the membership rule; who creates or selects members,
  and whether that happens before or after results; which later actor consumes the
  classification and exactly how; and what conclusion membership does **not** support.
- Explain dataflow as **actor -> action -> input -> output -> next consumer**. Name who
  produces each piece of information and what exact decision, lookup, validation, or
  transformation the next stage performs with it. Never stop at "used downstream."
- If the user says they do not understand, restart with a simpler mental model or analogy,
  then rebuild the explanation step by step. Do not merely paraphrase the same terms.
- Label planned behavior, live observation, and committed result separately. Also separate
  a technical `PASS` (the implementation or check met its criteria) from the scientific
  outcome (positive, negative, or inconclusive).

## Reader-facing self-audit

Before sending an explanation, verify that a first-time reader can answer, for every
central term: **what is it, why does it exist, how does it move or act, what is one
example, who consumes it downstream and how, and what is not implied?** Unexplained
acronyms, status IDs, set membership, or compact count notation fail the audit. If the
main explanation fails this audit, a technical appendix or glossary does not repair it.

# GEKO and Ductile source-branch authority

- Treat GEKO and Ductile as codebases that remain authoritative on two separate remote
  feature branches; do not assume that either one has been integrated into the current
  checkout or that they share one authoritative revision.
- Ductile source authority is `refs/remotes/origin/ductile_integration`; the currently
  known pin is `5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39`.
- GEKO source authority is `refs/remotes/origin/users/pkamd/geko_pr`; the currently known
  pin is `d32abacfd13579d1f523f035b7a10b0734c4ac47`.
- The branch names and their separation are default repository knowledge. Exact commit
  pins are checkpoint inputs: resolve and record both independently before work that
  depends on them, because either remote-tracking ref may advance.
- Never infer the Ductile revision from the GEKO branch, or the GEKO revision from the
  Ductile branch. Incidental files reachable from the other branch, the current checkout,
  merge ancestry, ignored caches, build products, or container contents do not replace
  either source authority.
- If an experiment combines both codebases, record the exact two source commits plus the
  integration commit, patch, worktree, or archive identity used to combine them. Until
  that evidence exists, describe them as separate-branch sources, not as an integrated
  codebase.

# Experiment execution and reporting discipline

- When work depends on a long-running or background experiment, data-collection, or
  simulation/benchmark job, do not write the experiment report, finalize the result
  interpretation, or mark the implementation complete until that job has fully finished
  (success status, all planned runs present) and its outputs are verified.
- Report metrics and verdicts only from the final result files, cross-checked against the
  raw artifacts; never from partial, interim, or still-running output.
- While such a job runs, independent work (documentation, unrelated code, other
  milestones) may proceed; the gated step is the results, verdict, and report or
  implementation completion.
- If a report must be produced before all runs finish, clearly mark it partial or
  in-progress and list the pending runs.
- For an **irreversible or expensive GPU/ROCm benchmark run**, freeze the workload set,
  seeds, metric definitions with their measurement boundary, and success/failure/
  inconclusive criteria **before launching**, and do not silently re-scope them after
  seeing the numbers. This is the one heavyweight gate, kept light — no machine-readable
  lock, hash chain, or amendment ledger. A genuine change to a frozen design goes through
  `design-discussion` (user approval) and a fresh run.

# Metric selection and comparability

- For ranking / design-space-exploration (DSE) / fidelity work, lead with
  decision-fidelity metrics — top-1 / top-2 / top-k and Pareto / best-config
  identification — and give them the highest priority. Treat rank-correlation (Spearman /
  Kendall) and absolute error as secondary: report them, do not lead a verdict on them.
- Prioritise metrics by what the decision actually needs. A difference that appears only on
  a low-priority metric while the decision-key metrics are tied is not a basis for a verdict.
- Ensure metric comparability (apples-to-apples). The predicted metric and the ground-truth
  metric must measure the same quantity over the same boundary — same components (compute /
  DMA / scheduling / overlap) and same clock domain. State each metric's measurement boundary.
- A gap that arises only because the two metrics are not comparable is a measurement
  artifact, not a real finding. Reconcile the boundary before interpreting the gap.

# Conclusion discipline (do not over-conclude)

- Do not draw a conclusion from a single dataset, a few data points, or a single metric.
  Wrong conclusions are a serious failure; treat any verdict as gated on convergent evidence.
- Reason from design purpose, not backward from a local result. When judging whether a
  component, field, parameter, or behavior "matters" or "can be ignored", reason FORWARD
  from its original design purpose: what is it for, and what would omitting it cost? Do NOT
  reason backward from a partial or local observation ("the current code path does not
  consume it", "this one run did not change") to conclude it is irrelevant — that hides
  effects which surface later at larger workloads or under a swept axis. Record an
  omitted-but-relevant effect as an explicit tracked gap rather than dismissing it.
- Form a hypothesis and an expected direction first, but hold it as a hypothesis, not a
  conclusion.
- Before accepting a result — especially a counterintuitive one — check confounders,
  experiment-design effects, and whether the result is an artifact of the setup, the
  workload, or the stated assumptions. Require a correct mechanism that explains it.
- Run multiple, diverse workloads and repeated runs designed to test the hypothesis, and
  conclude only after the results actually converge across them.
- If the evidence cannot converge (for example the reachable workload set is too narrow),
  the honest verdict is "inconclusive" — not a declared winner.
- Do not call one approach "better/correct" than another merely because its results "look"
  better on the available data — especially when the two approaches differ by construction
  or when one is the ground-truth-faithful reference. State the measurement boundary, the
  sample size, and the mechanism before any comparative verdict.

# GPU and ROCm execution environment

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
- Because a Codex subagent's sandbox cannot reach the container, GPU/ROCm commands are always
  run by Claude (the orchestrator) and the results fed back into the Codex thread.

# Code reference rule

- Cite every concrete code location as a markdown link with a line anchor, using a path
  relative to the current document, e.g. `[runContractionProblem](../../path/to/tensile_host.cpp#L3235-L3463)`.
- Link text is the symbol or function name; the URL carries the path and `#Lstart-Lend`.
- Do not paste bare absolute paths inline; they are noisy and hard to read.
- Verify line numbers against the current code before citing (they drift across commits).
  If unsure, link the file without a line anchor rather than guess.

# Scope control

- Before broad edits, inspect the relevant directory and existing structure; prefer local,
  scoped edits over broad rewrites.
- Do not delete, move, or rename files unless explicitly requested.
- Preserve existing CLIs, paths, config names, and output formats unless explicitly asked to
  change them.
- Commit only when the user explicitly asks.
- Do not modify the official `projects/hipblaslt/AGENTS.md` or
  `projects/hipblaslt/tensilelite/AGENTS.md`; follow them for build and PR conventions.
  This repo's rules only add learning / onboarding / orchestration guidance on top.

# Skill pointers

- Onboarding or code-trace reports (a user guide that helps a reader understand the repo):
  use the `hipblaslt-code-trace` skill.
- Implementation or experiment steps with acceptance criteria and a report target: use the
  `implement-verify-loop` skill (Claude orchestrates Codex implementer + independent Codex
  verifier).
- A genuine experiment-design direction decision: use the `design-discussion` skill.
- Experiment reports, code-change verification, and script work: the `experiment-report-writing`,
  `code-change-verification`, and `script-development` skills carry the conventions; the Codex
  subagents apply the matching `.codex/skills/` copies.
- Learning roadmap, daily notes, and quizzes: the `learning-roadmap-authoring`,
  `learning-notes`, and `learning-quiz` skills.

# Learning roadmap: canonical + mirrors (keep in sync)

The 8-week internship learning roadmap exists in three places. The **canonical**
(only-edit) copy is `study_docs/learning-roadmap.md`. The other two are **read-only
mirrors**: the Claude Code plan file
(`~/.claude/plans/rocm-libraries-repo-familiar-starry-aurora.md`) and
`.cursor/learning-roadmap.md`.

- Always edit `study_docs/learning-roadmap.md`, never a mirror.
- Inside Claude Code, a PostToolUse hook (in `/data1/perlee/.claude/settings.json`)
  auto-copies the canonical file to both mirrors on every edit.
- The hook does NOT fire when editing a mirror directly. In that case, manually sync:
  copy `study_docs/learning-roadmap.md` over both mirrors.

# Learning notes must mirror the full daily roadmap

Each daily study note (`study_docs/notes/MMDD-*.md`) is what the learner reads to decide
what to do that day, so its "對應 roadmap item" section MUST list EVERY item from that
day's roadmap section — nothing dropped:

- Every main item, all of its sub-bullets, and its `✅ 完成判準` line.
- ALL optional / recommended items too — `（AMD 資源，選做）`, `（全程指引，建議）`,
  `（選讀／按需）` — copied verbatim WITH their tag kept, so the learner sees what is
  skippable but never misses that it exists. Never omit an item just because it is optional.
- Preserve the roadmap's checkbox state (`- [x]` done / `- [ ]` not done).
- Carry each item's `📚 參考資源` too: put an inline `📚 參考資源：...` line under the
  item AND consolidate the same links in the bottom "code & doc 參考" section. Only link
  files that exist.

A missing item in the note means the learner silently skips that work. Use the
`learning-notes` skill as the authoritative procedure; when creating or reviewing a note,
verify its "對應 roadmap item" list matches the roadmap section one-for-one.

# Legacy: `.cursor` and `.agents`

This repo was previously driven with Cursor and with Codex as the orchestrator. The
`.cursor/` and `.agents/` directories are retained as **legacy** and are no longer the
canonical workflow source:

- The canonical agent instructions are now this `CLAUDE.md`, `AGENTS.md`, and the skills
  under `.claude/skills/` (with `.codex/skills/` copies for the Codex subagents).
- Do not edit `.cursor/` or `.agents/` as part of normal work, and do not treat them as
  authoritative. There is no requirement to keep them byte-identical with `.claude/`.
- Prefer running work through Claude Code as the orchestrator.
