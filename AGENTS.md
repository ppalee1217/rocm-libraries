# Codex Repository Guidance

## Repository-wide general rule

- Before doing repository work, read
  [`.cursor/rules/hipblaslt-onboarding.mdc`](.cursor/rules/hipblaslt-onboarding.mdc)
  completely.
- Ignore that file's Cursor-only YAML frontmatter (`description` and
  `alwaysApply`), and apply its Markdown body as repository-wide guidance.
- Treat references to Cursor as references to the current Codex session when
  they describe the active agent or editor behavior.
- Keep the source file canonical. Do not duplicate its full contents here.

## Instruction layering

- Also follow any more specific `AGENTS.md` found between the repository root
  and the current working directory.
- In particular, work under `projects/hipblaslt/` and
  `projects/hipblaslt/tensilelite/` must follow their existing nested
  `AGENTS.md` files.

## Codex skill location

- Repository-scoped Codex skills live under `.agents/skills/`.
- `.cursor/skills/` remains the canonical workflow source. Each matching
  `.agents/skills/` directory is a complete, standalone Codex-native port:
  it contains the full workflow and every required reference, script, and
  asset instead of pointing back to the Cursor `SKILL.md`.
- Codex-only runtime mappings belong in a short `Codex runtime mappings`
  section delimited by `BEGIN/END CODEX RUNTIME MAPPINGS` comments inside the
  migrated `.agents` skill. They may translate model names, input prompts,
  subagent calls, resume behavior, or Cursor/editor terminology, but must not
  change workflow authority, sequencing, evidence, or completion semantics.
- When adding, removing, renaming, or changing a Cursor skill, migrate the
  corresponding `.agents` skill and all bundled resources in the same task.
- Keep each migrated skill's `name` and `description` exactly synchronized
  with the canonical Cursor frontmatter, and verify that no `.agents` skill
  depends on reading a `.cursor/.../SKILL.md`.
