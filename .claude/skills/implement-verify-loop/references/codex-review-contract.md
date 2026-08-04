# Codex Review Contract

Use this contract for every Codex MCP review. Codex is a verifier: it may inspect files and run read-only commands, but it must not edit source, tests, configs, notes, or reports.

## Verdict object

Require the final response to contain one JSON object and no prose outside it:

```json
{
  "verdict": "PASS | CHANGES_REQUIRED | BLOCKED",
  "scope_reviewed": ["path or behavior"],
  "acceptance_criteria": [
    {
      "criterion": "required behavior",
      "status": "PASS | FAIL | UNVERIFIED",
      "evidence": ["command, artifact, code path, or direct observation"]
    }
  ],
  "blocking_findings": [
    {
      "id": "stable identifier",
      "severity": "critical | major | moderate",
      "category": "correctness | regression | compatibility | reproducibility | evidence | methodology | report",
      "evidence": "specific file, line, command, output, or artifact",
      "required_change": "smallest actionable correction"
    }
  ],
  "non_blocking_recommendations": ["optional scoped improvement"],
  "commands_run": [
    {
      "command": "exact command",
      "cwd": "working directory",
      "result": "PASS | FAIL | BLOCKED",
      "evidence": "exit status and relevant result"
    }
  ],
  "evidence_requests": [
    {
      "command": "exact command for Claude to run",
      "cwd": "working directory",
      "expected_result": "observable success condition",
      "expected_artifacts": ["path"],
      "estimated_minutes": 0,
      "reason": "why this evidence is necessary"
    }
  ],
  "unverified": ["important behavior or case not checked"],
  "experiment_status": "NOT_APPLICABLE | COMPLETE | INCOMPLETE",
  "report_gate": "NOT_READY | PASS | FAIL",
  "goal_alignment": "FULL | PARTIAL | NONE",
  "unacceptable_fallback_triggered": { "triggered": false, "which": [] },
  "terminal_recommendation": "CONSISTENT | RELOOP | OUT_OF_SCOPE_PARTIAL | ESCALATE",
  "summary": "bounded interpretation of the evidence"
}
```

`PASS` requires no blocking findings, no failed or unverified required acceptance criterion, no unresolved evidence request, and `experiment_status` equal to `COMPLETE` or `NOT_APPLICABLE`. A final release-gate audit also requires `report_gate: PASS`. Style preferences belong in `non_blocking_recommendations` and do not block completion.

## Orchestrated mode (goal-oracle verifier)

In the `implement-verify-loop`, the verifier is given a **goal plan (Plan-B) only — not the implementer's steps**, plus the implementation diff/artifacts. It must:

- Judge `goal_alignment` against Plan-B's main objective + desired end-result, from the **actual code/artifacts** (treat the implementer's report as a claim to check, not ground truth).
- Set `unacceptable_fallback_triggered` if any of Plan-B's listed unacceptable fallbacks occurred. Any trigger forces a non-CONSISTENT recommendation.
- **Run its own fresh reproduction** of Plan-B's headline acceptance check; record it in `commands_run` or as an `evidence_request`. GPU/ROCm reproductions that its sandbox cannot run go through `evidence_request` for the orchestrator to run inside the `perlee` container.
- **Judge ranking/fidelity claims by decision-fidelity first.** Lead on top-1 / top-2 / top-k and Pareto / best-config; a verdict led on a secondary metric (Spearman / Kendall / absolute error) while the decision-key top-k is tied is a blocking finding (`category: methodology`).
- **Check metric comparability before accepting any gap.** Predicted and ground-truth metrics must measure the same quantity over the same boundary; a gap that exists only because the pair is not comparable is an artifact — flag it (`category: methodology`).
- **Reject conclusions from thin/narrow evidence.** "X better/correct" from a single dataset, a few cells, one metric, or with no mechanism is an unacceptable fallback. Conversely, accept an explicit **inconclusive** verdict as goal-consistent when Plan-B allows it.
- For a GPU experiment, confirm the run honored the frozen pre-run freeze (workload set, seeds, metrics, criteria) and was not silently re-scoped after the numbers were visible.
- Set `terminal_recommendation`: `CONSISTENT` (goal FULL, no fallback, PASS — an honest Plan-B-sanctioned "inconclusive" counts) → orchestrator finalizes; `RELOOP` (fixable gap) → orchestrator adjusts Plan-A and re-runs; `OUT_OF_SCOPE_PARTIAL` (goal correct but not achievable in scope/budget) → orchestrator escalates the honest partial; `ESCALATE` (verifier cannot adjudicate) → orchestrator/user decides.

The orchestrator, not the verifier, owns plan changes, commits, and the report.

## Initial-review prompt

Append this instruction to the task context:

> Act only as the independent Codex verifier. Use the repository `code-change-verification` skill. Inspect the stated scope, implementation diff, surrounding call paths, compatibility boundaries, tests, and documentation. Run only commands permitted by read-only mode. Request any write-producing or GPU/ROCm verification through `evidence_requests`; do not edit files. Judge every acceptance criterion from direct evidence. Return exactly the verdict object defined in the supplied Codex Review Contract.

For a reply after repairs, include finding IDs addressed, changed paths, commands run by Claude, final artifact paths, and remaining uncertainties. Ask Codex to re-read current files rather than trusting the repair summary.

## Independent final-audit prompt

Append this instruction to a new Codex thread:

> Perform a fresh release-gate audit without relying on an earlier review conclusion. Use `code-change-verification` and, for the milestone report, `experiment-report-writing`. Re-read the task source, current implementation, final diff, tests, completed experiment artifacts, raw evidence, and report. Check acceptance criteria, backward compatibility, claim-to-artifact traceability, measurement boundaries, implementation assumptions, unsupported interpretations, missing runs, and unrelated working-tree changes. Do not edit files. Return exactly the verdict object defined in the supplied Codex Review Contract. PASS requires `report_gate: PASS` and complete final evidence.
