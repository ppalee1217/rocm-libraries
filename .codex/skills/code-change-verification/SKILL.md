---
name: code-change-verification
description: Use when reviewing, testing, validating, or summarizing existing code changes, bug fixes, scripts, configs, notebooks, simulation code, experiment utilities, or code-adjacent documentation in this hipBLASLt / TensileLite / Ductile-GEKO repo. Prefer `script-development` when the primary task is to create or modify a script. Emphasizes scoped verification, minimal relevant tests, honest reporting of what was and was not verified, and clear follow-up actions.
---

# Code Change Verification Workflow

## Purpose

Verify existing code or script changes in a scoped, evidence-based way. Use `script-development` instead when the task is mainly to create, modify, or document script behavior.

Applies to source code, scripts, configs, notebooks, simulation code, experiment utilities, tests, and code-adjacent documentation that describes behavior, commands, outputs, or workflows.

## Core principle

Verify the smallest meaningful behavior affected by the change. Do not claim the whole project works unless broad tests were actually run. Distinguish clearly between: what was inspected, changed, tested, passed, failed, not tested, and what remains uncertain.

## GPU / ROCm execution boundary

Any GPU- or ROCm-dependent verification (`rocminfo`, `hipcc`, `amdclang++`, `rocprof`, kernel generation, compilation, benchmarks, correctness runs) runs only inside the `perlee` container, per the repo GPU rule. Never run these on the host or against another user's container. If `perlee` is unavailable, stop and report it as a blocker rather than substituting an environment.

## Experiment-dependent verification

If verification depends on an experiment, data-collection, or simulation job (including background or long-running jobs), do not summarize results or conclude pass/fail until that job has fully completed (success status, all planned runs present) and outputs are final. Report metrics only from completed result files, never from partial output. See the **Experiment-completion gate** in `experiment-report-writing`.

## Verification boundary

Before running or recommending tests, identify the boundary: the changed feature/bug fix/code path; the files or modules affected; the expected behavior after the change; the highest-risk assumptions; the smallest relevant test or command; and anything explicitly out of scope.

## Pre-verification inspection

Inspect the relevant implementation and surrounding call path. Check for changed function signatures, CLI arguments, config keys, file paths, output formats, dependency assumptions, or experiment-workflow assumptions; generated files that should not be hand-edited; and backward-compatibility risks.

## Test selection

Prefer the smallest relevant verification first:

1. Unit test for the changed function or module, if available.
2. Focused integration test for the affected workflow, if available.
3. Existing regression test that covers the behavior.
4. Smoke test using the smallest representative input.
5. Static check, lint, type check, or syntax check.
6. Manual verification procedure when no runnable test exists.

Do not run expensive, destructive, or very long commands unless the user asks or the task requires it. Anything estimated at 30 minutes or more is a human gate.

## Commands

When proposing or running commands, include the exact command, the expected result, the directory to run it in, required environment assumptions (including "inside `perlee`" for GPU work), and important output files or logs to inspect.

## Result interpretation

Explain what the result means. Distinguish direct evidence, inferred confidence, remaining risk, and failure cause if any. Do not overstate. Prefer "the focused smoke test passed for the tested input; broader shapes and full benchmark runs were not verified" over "the feature is fully verified."

## Failure handling

If a test fails: report the exact failing command; summarize the relevant error; identify the likely failure layer (syntax, import/dependency, runtime exception, assertion mismatch, numerical mismatch, file path, environment, timeout, resource limit, or toolchain issue); state whether the failure is from the current change or pre-existing; and propose the smallest next debugging step. Do not hide failures.

## When tests cannot be run

Explain why (missing dependency, dataset, hardware, simulator, license; command too expensive; environment unavailable; user-specific credentials or paths). Then give a manual verification procedure with commands, expected output, files to inspect, metrics to compare, and known limitations.

## Verification report format

```md
## Verification Summary

- **Changed behavior**
  - Describe the behavior that was expected to change.
- **Commands run**
  - `<command>`
    - Result: pass / fail / not run.
    - Notes: brief interpretation.
- **Evidence**
  - Direct evidence from tests, logs, diffs, or inspection.
- **Not verified**
  - Important cases that were not checked.
- **Remaining risks**
  - Risks, edge cases, or assumptions.
- **Recommended next steps**
  - Smallest useful follow-up checks.
```

## Code review checklist

Does the change match the requested scope? Are unrelated files modified? Are generated, vendored, or bulky artifact files modified unexpectedly? Are existing APIs, CLIs, config names, output paths, or output formats preserved? Are errors handled clearly and edge cases considered? Are tests or manual steps provided? Is documentation updated if behavior changed? Is the implementation simpler than a broad rewrite? Are assumptions stated clearly?

## Final response expectations

Report what was verified, what command or inspection was used, whether it passed / failed / was not run, what confidence the verification provides, what remains unverified, and the recommended next action.
