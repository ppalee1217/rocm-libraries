---
name: experiment-report-writing
description: Use when writing, editing, reviewing, or restructuring experiment reports, run summaries, result tables, measurement notes, milestone reports, data-collection explanations, implementation-analysis sections, or interpretation notes for this hipBLASLt / TensileLite / Ductile-GEKO research repo. Requires self-contained explanation of terms, experiment design and parameters, a reviewable enumeration of implementation assumptions, workflow, implementation details, collected evidence, result interpretation, validity analysis, and milestone-scoped reporting. Use together with script-development when scripts or commands are needed to collect, process, reproduce, or validate report data.
---

# Experiment Report Writing Workflow

Use this skill when the task involves experiment reports, result interpretation, experiment-design explanation, measurement analysis, milestone reporting, data collection, implementation analysis, or validity discussion.

This repo's experiment plans and reports live under `study_docs/research/` (for example the `ductile-origami-warmstart` experiment line). GPU/ROCm evidence must come from runs inside the `perlee` container, per the repo GPU execution rule.

## Readability first (the top failure mode to avoid)

Reports in this repo have failed most often by being hard to read: text hard-wrapped at odd places, and single bullets that glue many facts together. Fix that before anything else. These rules bind every report and every reader-facing explanation.

- **Do not hard-wrap for column width.** Never break a line inside a phrase, inside inline code, or before a sentence's meaning is complete. Each physical line carries a complete thought; a line ends only when an idea actually ends. Start a new paragraph with a blank line when the topic changes.
- **One idea per line.** One bullet states one point. Do not chain three or more facts, numbers, or caveats into a single bullet with strings of `，` / `；` / `（…）` / `——` / bold fragments. When a claim has multiple parts, split it into nested sub-bullets.
- **At most one `（…）` per sentence.** Move extra asides into sub-bullets.
- **Anchor each headline number on its own line** with its subject and scope, for example `held-out fidelity 0.85（vs baseline 0.40）`, not buried mid-clause among other numbers.
- **Chinese-English spacing.** Put exactly one ASCII space between a Chinese character and an adjacent English word, acronym, or alphanumeric token (`M18 實驗`, `使用 rocprof`, `Ductile GA`). Do not add spaces inside inline code, fenced code, URLs, file paths, CLI flags, formulas, identifiers, or hashes; when such a span touches Chinese prose, put the space outside the span (`執行 \`run.sh\` 後`). Keep command and machine-output blocks byte-for-byte.

Before (one run-on, hard to parse):

> （operator-shape 軸,E1/E2）可以（但 E6 顯示部署有代價）:`array utilization` 是有效訊號（越高殘差越低,Spearman −0.50）;`util≥0.8` 當門檻,held-out fidelity 0.85（vs 0.40）,救回 11/12,代價 2 個 dangerous FP…

After (nested, one idea per line):

> - **operator-shape 軸：可細分出「可便宜校正」的子集，但部署有代價。**
>   - 訊號：`array utilization` 越高，殘差越低（Spearman −0.50）。
>   - 細分（E2，in-sample）：`util≥0.8` 時 held-out fidelity 0.85（vs baseline 0.40），救回 11/12，代價 2 個 dangerous FP。
>   - 結論：可增 cheap-coverage，但部署須收緊門檻。

## Core principle

An experiment report must explain not only the result, but also **how the experiment was designed, implemented, measured, and interpreted**.

A good report lets a technically informed reader understand it **without reconstructing missing context from prior conversations, code changes, or unstated assumptions**. It should make clear:

- What research question or milestone the experiment addresses.
- What technical terms, systems, models, workloads, tools, or metrics are involved.
- How the experiment workflow was designed, and what each important parameter means.
- How the implementation or coding work was performed.
- What data, logs, metrics, traces, tables, figures, or artifacts were collected.
- How the collected evidence supports or does not support the claim.
- What assumptions, limitations, and validity threats remain.

## Self-contained explanation rule

The report must be self-contained enough that a reader who only reads this report understands the experiment's purpose, setup, design, implementation, evidence, and conclusion.

### Claim unpacking rule

For every major claim in Summary, Results, Analysis, or Conclusion, unpack it so a reader can trace it without prior context. Each major claim should make clear:

- **Scope**: which workload, kernel, shape, config, run collection, or scenario the claim applies to.
- **Terms**: what project-specific terms in the claim mean.
- **Measurement boundary**: what was measured, where measurement starts and ends, and what is included or excluded.
- **Evidence**: which logs, metrics, tables, traces, artifacts, scripts, or code inspection support the claim.
- **Mechanism / meaning**: what system behavior the result reveals, or which explanation is only plausible rather than established.
- **Research relevance**: which research question, design decision, baseline, gate, or follow-up changes because of the result.
- **Limitation**: what the result does not prove, and what follow-up would be needed to generalize it.

If a single bullet contains multiple technical claims or dense terms, split it into a short sequence: **observation / evidence → mechanism or meaning → research relevance → limitation**. If the experiment did not establish the mechanism, label it as plausible, inferred, uncertain, or unexplained rather than as a causal conclusion.

### First-use definition rule

The first time a project-specific term appears, define it briefly in the same paragraph, or point to a nearby Background / Terminology section. Do not assume the reader inherits the meaning from a prior report unless the current report cites and summarizes that explanation.

### Measurement boundary rule

For any metric, timing, error, or classification used as evidence, explain the measurement boundary. At minimum, clarify:

- The raw artifact or source, such as a `rocprof` CSV, benchmark stdout log, TensileLite result file, or script output.
- The producer and consumer of the artifact when it matters to interpretation.
- The parser, aggregation rule, filtering rule, or formula used to produce the reported value.
- The start and end boundary for timing values, such as kernel-only GPU time vs end-to-end wall time.
- What the value includes and excludes, such as compile/codegen, warm-up, host overhead, failed runs, or post-processing.
- Known failure modes or misleading field names, especially when a name sounds broader or narrower than what it measures.

This matters most for wall-clock cost, kernel timing, speedup, ranking flip, decision-fidelity, Pareto retention, and cost-saving claims.

### Enumerate implementation assumptions (required, reviewable)

Every report must carry a near-front, dedicated **Experiment Design & Assumptions** section whose **Implementation Assumptions** subsection lists, as a reviewable checklist, the concrete assumptions baked into the actual implementation and measurement — not generic platitudes. A reviewer must be able to confirm the design is correct **from this list alone, without reading the runner code**.

State each assumption with four parts:

- **Assumption**: what the implementation or measurement actually assumes — concrete and specific to this experiment.
- **Why reasonable**: the justification for it.
- **Bias if wrong**: how the result would be distorted if it does not hold.
- **Verified?**: `verified` / `unverified` / supported by a named artifact (name the log, CSV, audit, or code path).

List these when present (do not leave them only in prose, Validity Threats, or runner code):

- alignment / key choice for matching records across configs, runs, or shapes, and why the naive key was rejected.
- central-tendency or fitting choice (median vs mean, robust vs exact) and why.
- oracle type — methodology oracle vs physical-hardware ground truth.
- proxy metrics standing in for the real quantity.
- which graph / trace / artifact is reused vs regenerated, and what that presumes.
- whether each parameter is fixed, swept, measured, inferred, calibrated, or tool-generated.
- sampling assumptions (sample size N, seed determinism) and how they could inflate or deflate a headline number.
- regime / class assignment rules and the heuristic behind them.
- any reported value that is a sum or aggregate of a narrower quantity than its name suggests.

## Milestone scope rule

Write one report for one coherent milestone.

- Do not mix unrelated milestones in one report; link the separate report instead.
- If the experiment depends on a previous milestone, cite or link it and briefly summarize the dependency.
- If a report starts to cover multiple independent research questions, split it.

## Experiment-completion gate (write reports only from finished, verified runs)

Before writing, updating, or finalizing an experiment report — and before marking a report task complete — confirm the underlying experiment or data-collection is fully finished and its outputs are final. Do not derive conclusions from a still-running, timed-out, or partial job.

- **Job completion**: every job the report depends on finished with a success status, is not still running, and was not killed or timed out. Reading interim console output does not count as completion.
- **Output completeness**: all runs, workloads, configs, or splits the report cites are present in the final result files. If a run is missing, re-run it or explicitly scope the report to the completed subset and label the rest as not-collected.
- **Numbers from final files only**: every number is taken from completed result files and cross-checked against the raw artifact, not from console scrollback.
- **No partial-data verdict**: never derive a headline claim, ranking, or positive/negative conclusion from a partial job.
- **If a report must be produced before completion**: mark it `status: in-progress`, list which runs are still pending, and do not present the partial result as the milestone conclusion.

While a long experiment runs, independent work (documentation, unrelated code, other milestones) may proceed; only the results, verdict, and completion are gated on the job finishing.

## Required sections to check

- **Milestone and research question**: milestone name, the question it answers, why it matters, the hypothesis or decision being evaluated, and what is out of scope.
- **Plain-language explanation**: clear enough for a reader in the area who has not followed every implementation detail; explain the design principle and key terms; do not hide reasoning behind jargon.
- **Experiment workflow design**: the end-to-end workflow (setup, input preparation, execution, logging, data collection, post-processing, analysis); which parts are manual/scripted/automated; how it connects to the research question; the meaning of important parameters.
- **Experiment design and implementation assumptions (near-front, required)**: the four-part reviewable list above.
- **Implementation and coding details**: important files, modules, scripts, configs, commands, generated artifacts; important code-level logic; how the implementation connects to the design and data; known limitations. Summarize and link to source when long.
- **Script and command support**: use `script-development`; put report scripts under `scripts/`; give a reproduce entrypoint that supports `help` / `-h` / `--help`; document inputs, outputs, and side effects. GPU/ROCm reproduction commands must state that they run inside the `perlee` container.
- **Data collection and evidence**: exactly what data was collected and its source; how it was collected; why it is sufficient or not; raw vs processed; any filtering / aggregation / normalization; missing data.
- **Experiment insight**: what insight follows; direct observation vs inferred conclusion; whether it supports, weakens, or does not answer the hypothesis; do not treat implementation success as proof of the research claim.
- **Result interpretation**: connect tables/figures/logs/metrics back to the question; what each metric means; what the result does not prove; how parameters or workload choices may influence it.
- **Validity and possible misinterpretation**: threats such as workload bias, insufficient baselines, measurement noise, small sample, missing overhead, wrong metric selection, or implementation bugs; mark uncertain conclusions clearly; state what additional evidence would be needed.
- **Follow-up actions**: what to do next, split into follow-up experiments, missing data, implementation fixes, script improvements, documentation, advisor questions, or research-direction decisions.

## Final self-audit before delivery

Scan the Summary, Results, Analysis, and Conclusion for bolded or headline-level claims. For each, verify a reader who only reads this report can answer: what exactly is claimed; which workload/kernel/config/split it applies to; what each project term means; which artifact/metric/script/code path supports it; what behavior it reveals or why the mechanism is uncertain; which research question/decision/baseline/gate/follow-up changes; what it does not prove; and what missing data or validity threat could change the interpretation.

Also confirm every design-critical implementation assumption is enumerated (four-part) in the **Experiment Design & Assumptions** section, reviewable without reading the runner code. Finally, re-read the whole report against the **Readability first** rules: no hard-wrapped lines, one idea per line, headline numbers anchored. If any answer is missing, revise before delivery. The target is explanation density, not length.

## Recommended report structure

```md
# <Milestone or Experiment Name>

## Summary
用繁體中文簡要說明這個 milestone / experiment 做了什麼、回答什麼問題、目前最重要的結論。

## How to Read This Report
- 說明讀者應如何閱讀主文、audit details 與 referenced reports。
- 標出哪些背景繼承自其他 report，哪些 claim 是本 report 新增或修正。

## Milestone Scope
- **Research question** / **Hypothesis** / **In scope** / **Out of scope** / **Related reports**

## Background and Terminology
- **Key terms** / **Required background** / **Referenced explanations**

## Experiment Design & Assumptions
- **Design principle** / **Workflow overview** / **Experiment parameters**
- **Implementation Assumptions（必備、列舉式、四欄：assumption / why reasonable / bias if wrong / verified?）**

## Implementation Details
- **Changed or used files** / **Important logic** / **Code path** / **Commands or scripts** / **Limitations**

## Data Collection
- **Collected data** / **Collection method** / **Measurement parameters** / **Post-processing** / **Missing data**

## Results
- **Raw observations** / **Processed results** / **Figures and tables** / **Metric meaning**

## Analysis and Interpretation
- **Main insight** / **Hypothesis check** / **Parameter impact** / **What it proves** / **What it does not prove**

## Validity Threats

## Conclusion
- 明確標記哪些是 evidence-backed，哪些仍是 assumption 或 uncertainty。

## Follow-up Items

## Appendix: Artifact / Field Guide
- 視需要列出重要 logs、CSV columns、artifacts、producer/consumer、evidence class，以及不應如何解讀。
```
