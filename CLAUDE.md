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
