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

- Repository-scoped Codex skill adapters live under `.agents/skills/`.
- Each adapter reads the matching canonical workflow under `.cursor/skills/`
  and documents only the runtime-specific mappings needed by Codex.
- When adding, removing, or renaming a Cursor skill, update its Codex adapter
  in the same task.
- When a canonical skill description changes, keep the adapter's `name` and
  `description` in sync; canonical body-only changes require no duplication.
