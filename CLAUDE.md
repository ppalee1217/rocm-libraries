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

## GEKO and Ductile source-branch authority

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

### Govern experiments by risk, hard gates, and closure units

- Classify work before any outcome label is visible:
  - `R0 mechanical`: deterministic, non-outcome mechanical work.
  - `R1 standard preregistered outcome checkpoint`: ordinary execution and interpretation of an
    approved outcome gate.
  - `R2 material measurement/claim/lineage risk`: work that can materially change measurement,
    comparability, provenance, selection, lineage, or allowed claims.
  - `R3 authority/destructive/post-label change`: new authority, destructive work, or any
    post-label protocol, contract, lock, fixture, threshold, selection, lineage, or claim change.
- Freeze the tier before labels. After labels, risk may only escalate. A generation, successor,
  rename, replacement role, fresh thread, or new run root cannot reset tier, repair count,
  thread count, lineage, or authority history.
- Before outcome-bearing R1-R3 work, extract a durable machine-readable frozen contract from the
  approved parent/design, verify its human/machine parity, and seal its tracked lock before
  labels. It must define criteria, outcome/edge matrix, evidence/measurement/claim boundaries,
  fixtures, lineage, whitelists, authority, repair and resource budgets, downgrade gate, and lock
  identity. A transient execution plan cannot replace or amend it.
- Use one execution planner by default. R2/R3 add one fresh adversarial oracle/authority auditor
  before labels. A fresh implementer is not mandatory and may continue within one execution
  tranche. Every outcome-bearing R1-R3 gate requires a fresh verifier who did not implement that
  gate. Same-model fresh threads are process independence, not scientific replication.
- A model pin is a disclosed preference or capability requirement, not a universal R0/R1 hard
  stop. Record requested and actual models and capability differences; stop only when an
  approved non-substitutable capability is unavailable.
- Keep three units separate:
  - A `scientific_gate` is a hard preregistered outcome/claim/authority edge.
  - An `execution_tranche` may share planner, implementer, verifier, run root, and repair ledger.
  - A `closure_unit` may give compatible adjacent gates one terminal report/update/staged audit
    and commit without weakening any scientific edge.
- Dependent outcome work waits for the upstream gate's verified frozen edge, not necessarily its
  later terminal paperwork. Independent label-blind preparations may run in parallel only when
  write, index, run-root, evidence, and authority boundaries do not overlap. Never speculate on
  a dependent outcome.
- Track `live_run_state` separately from `committed_projection_state`. Partial artifacts and
  working-tree progress belong only to live state; committed projection changes only after the
  durable closeout commit and post-commit audit.
- Repair rounds are bounded at six for every R0-R3 gate. Reaching two consecutive rounds
  without material progress triggers the non-design dual-agent adjudication below before another
  repair; it does not by itself terminate the overall goal. A unified, contract-preserving repair
  decision may continue within the six-round budget. Generations, successors, renames,
  replacements, or fresh threads cannot reset counts, and a seventh repair requires new human
  authority. Total fresh role-thread caps for one gate/lineage remain R2 = 5 and R3 = 6.
- While an explicitly requested goal remains achievable under existing authority, do not
  terminalize it merely because of `CHANGES_REQUIRED`, an ordinary test failure, missing
  nonmaterial telemetry, planning variance, a recoverable process/environment interruption, or
  another contract-preserving implementation blocker. Exhaust safe in-scope diagnosis, repair,
  rerun, and the authorized dual-agent operational adjudication within their frozen caps while
  keeping the user informed. Pause for the user only at the experiment-design gate below or when
  continuation genuinely needs missing destructive/external/platform authority, would violate a
  hard scientific or safety boundary, or has exhausted the six-round budget with no valid
  authority-preserving path.
- Treat pre-empirical share, wall-time, CPU/GPU time, storage, throughput, the first-1%
  reforecast, a 2x variance, and the default 5 GiB transient-storage ceiling as operational
  planning targets by default. Notify the user before long-running work and when a planning
  target is crossed, but notification is not an approval gate and the complete frozen workload
  continues. A target becomes hard only when an approved pre-label design explicitly freezes
  the exact resource quantity and boundary as a scientific/comparability criterion or as an
  external, physical, allocation, or safety limit.
- Preserve known cumulative resource usage and its parent/child/inclusive measurement boundary
  across generations, successors, replacement roles, process restarts, and new run roots as
  best-effort provenance. Never erase, fabricate, or silently present `UNKNOWN` as zero.
  Historical consumption, missing telemetry, a projection above 2x, or an internal planning-cap
  exceed does not by itself pause, terminate, or debit successor-entry authority.
- Resource telemetry is operational planning evidence, not a scientific outcome or claim
  criterion by default. Pause at a safe boundary only when direct or materially indicative
  operational evidence ties continuation to unsafe operation; an external/platform limit;
  unavailable compute, allocation, memory, or storage; inability to complete the full frozen
  workload, verification, closure, or artifact preservation; label-dependent stopping or
  selection; a required workload/claim change; corrupted or unverifiable evidence; or an
  explicitly frozen scientific resource boundary. Bare `UNKNOWN`, planning variance, internal
  cap crossing, or cumulative total is not such evidence. Record nonmaterial gaps and improve
  telemetry prospectively; never rerun outcome-bearing work solely to perfect accounting. This
  rule does not relax scientific sample/draw/seed/arm/population/generation/repetition caps,
  repair/thread caps, downgrade gates, or evidence requirements, and it never creates or changes
  a scientific outcome/edge.
- Technical verification and staged closeout may be one fresh verifier pass when implementation
  is stable and the complete staged draft is ready; record separate technical and closeout
  verdicts. Any later staged change requires the affected audit again. Post-commit audit remains
  mandatory.
- An isolated terminal commit is permitted only when existing authority covers the exact
  closure unit and frozen delivery whitelist. Push, PR, credentials, external writes,
  dependency installation, and container mutation remain separately gated.
- Positive, negative, and inconclusive outcomes all require durable terminal evidence. A
  predeclared `BLOCKED` state may create only its specified blocker memo; it does not unlock a
  dependent edge. `skipped_by_gate` and `not_activated` get no fabricated report of their own.
- Keep transient `agent_run/` evidence out of commits. Preserve unrelated user changes and
  pre-existing index entries.

### Make every closure report a durable decision record

- The committed report must be self-contained. Restate the frozen oracle and evidence boundary;
  record exact commands, working directories, exit codes, raw artifact hashes, every
  implement/verify iteration, findings, repairs, deviations, actual outcome, verified gate, and
  what the evidence can and cannot support.
- For every agent-decided issue, record the trigger, affected invariant, material alternatives,
  supporting and opposing evidence, assumptions, participants, decision, rationale and
  trade-offs, implementation/measurement/gate/claim impact, resolution, remaining uncertainty,
  and why user review was or was not required.
- When `design-discussion` was used, also synthesize both reviewers' substantive objections,
  accepted and rejected alternatives, shared consensus or preserved dissent, round/time usage,
  and final responses. Do not paste raw chat or private chain-of-thought. A link to ignored
  transient evidence is not a substitute for the durable report.
- Do not embed a closure commit's own SHA, a `SELF` placeholder, or a delivery-manifest hash in
  the tracked report or parent plan. Link the commit through stable checkpoint/report identity,
  commit trailers, Git history, the transient post-commit audit, and the final handoff.

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

### Bound design discussion, operational adjudication, and preserve dissent

- Trigger `design-discussion` only for material experiment-design ambiguity involving protocol,
  measurement/claim/lineage, stopping rules, or scientific authority. Do not trigger it for
  mechanical repairs, deterministic artifact recovery, ordinary implementation choices, or
  resource waiting.
- Give two fresh independent reviewers the same neutral prompt and evidence. Allow at most two
  cross-examination rounds plus one evidence-backed final round, with at most 60 total agent
  wall-minutes. A new thread or renamed issue cannot reset either cap.
- Do not force `AGREE`. For an experiment-design issue, preserve the reviewers' unified
  conclusion or dissent and always pause for the user's decision before changing or resuming the
  affected design path; reviewer agreement is analysis, not design authority.
- For a non-design issue that would otherwise stop progress, has multiple consequential
  contract-preserving repairs, or has repeated for two rounds without material progress, use two
  independent operational reviewers with the same bounded cross-examination procedure. Use
  fresh threads when thread headroom exists; otherwise resume two independent non-implementer
  roles and disclose their prior roles instead of bypassing the thread cap.
  If they agree on a non-destructive action that preserves the frozen contract and existing
  authority, the repository owner pre-authorizes the Main agent to record and execute it without
  another user round-trip. If they dissent, preserve both positions; the Main agent may proceed
  only with an action uniquely compelled by the frozen contract and direct evidence. Otherwise
  reclassify the unresolved issue under the applicable experiment-design, authority, or safety
  gate instead of inventing consensus.
- A frozen-contract change includes a changed goal, acceptance threshold, evidence source,
  report target, gate order/edge, preregistered fixture or measurement boundary, whitelist,
  immutable lock/lifecycle invariant, lineage, or allowed claim. After labels, such a change is
  R3 and cannot be made through reviewer consensus alone.
- `CHANGES_REQUIRED` alone is not a contract change. A contract-preserving in-scope repair,
  rerun, correctly isolated test harness, or explicitly designed negative branch does not need
  repeated human approval and should not terminalize an achievable goal before the six-round
  repair budget is exhausted.
- Reviewer agreement cannot invent the user's initial intent or grant missing commit/push,
  credential, external-system, dependency-installation, container, or destructive authority.

### Recover only deterministic disposable artifacts automatically

- Automatic recovery is limited to one exact ordinary regular file that is baseline-absent,
  newly untracked, unstaged, exactly attributed to the current workflow, byte-regenerable,
  nonsensitive, and neither evidence-bearing nor independently valuable.
- Prove lexical and resolved path, active-area ownership, baseline absence, exact creator
  attribution, `lstat` type/mode/link count, Git/index/ignore state, size, SHA-256, timestamps,
  and lack of user/concurrent overlap before action.
- For a qualifying file, automatically move only that exact file into a new incident-specific
  ignored `agent_run/...` quarantine, verify identical hashes and source absence, then audit full
  status/diff/index, whitelist, and unrelated user changes. No dual reviewers are required.
- Never use globs, recursion, broad variables, `git clean`, reset, checkout, stash, unlink, or
  directory removal in this automatic path.
- Tracked, staged, pre-existing, attribution-ambiguous, concurrently modified, sensitive,
  evidence-bearing, plan-listed, or independently valuable artifacts remain at a human/dual
  review gate. Dual review can resolve classification; it cannot invent destructive authority.

### Downgrades require the user's decision

- Never autonomously downgrade an experiment or implementation. A downgrade includes reducing
  workloads, runs, seeds, metrics, validation, acceptance criteria, or scope; replacing an
  original baseline with a proxy; skipping a checkpoint; or converting a planned confirmation
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
