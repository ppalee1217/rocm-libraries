---
name: script-development
description: Use when creating, modifying, or documenting utility scripts, automation scripts, experiment helpers, maintenance scripts, batch file operations, or reproducible command-line workflows in this hipBLASLt / TensileLite / Ductile-GEKO repo. Prefer `code-change-verification` when the primary task is reviewing, testing, validating, or summarizing an existing code or script change. Emphasizes safety, dry-run behavior, reproducibility, stable input/output formats, and clear verification.
---

# Script Development Workflow

## Purpose

Use this skill when the primary task is to create or change utility scripts, automation scripts, experiment helpers, maintenance scripts, or batch file operations. Use `code-change-verification` instead when the script already changed and the task is mainly to test, validate, review verification evidence, or summarize confidence.

## Safety

- Prefer dry-run mode for destructive or bulk operations.
- Do not delete, move, rename, or overwrite files unless explicitly requested.
- Avoid hard-coded absolute paths.
- Preserve existing input/output formats unless explicitly asked to change them.
- Do not silently expand the script scope.

## GPU / ROCm boundary

Scripts that invoke GPU- or ROCm-dependent commands (`rocprof`, `hipcc`, `amdclang++`, kernel generation, benchmarks) must be designed to run inside the `perlee` container, and their help text and docs should say so. Do not have a script implicitly assume host GPU access.

## Reproducibility

- Make scripts rerunnable when practical.
- Prefer explicit input/output paths over hidden global state.
- Document required arguments, assumptions, and expected outputs.
- When modifying scripts, explain how to run and verify them.

## Experiment reproduce entrypoints

- For an experiment or report under `study_docs/research/`, provide a reproduce entrypoint that supports `help`, `-h`, and `--help`.
- The help text must list modes, environment overrides, examples, output directories or artifact roots, and whether a dry-run mode is supported.
- Name the entrypoint so it maps clearly to its experiment/report; keep experiment-specific scripts local to that experiment's directory and put only shared helpers at a shared root.
- Reproduce scripts should read final result artifacts by default and write explicit output paths. Do not rerun expensive GPU experiments from a plotting or summary script unless the user explicitly asks.

## Verification

When creating or modifying a script, provide: the exact command to run; the expected output; files or directories affected; whether the command is dry-run, smoke test, or full run; and any limitations or unverified cases.

## Final response

After script work, summarize: what changed, which files were affected, how to run it, how to verify it, and any safety concerns or follow-up items.
