---
milestone_id: S13
title: Stage 1 actual Gen0 sampler mechanism
stage: 1
lifecycle: active
design_status: draft
execution_status: gated
outcome: not_evaluated
decision: pending
hypothesis_id: S13-H1
depends_on:
  - S12:D5_PASS
entry_gate_ids: [D5_PASS]
criterion_refs: [D6_MECHANISM_POSITIVE]
failure_taxonomy_refs:
  - FT-PLUMBING
  - FT-GEN0-MECHANISM
  - FT-HEURISTIC-SATURATION
  - FT-ENTROPY-ONLY
  - FT-WASHOUT-UNTESTED
  - FT-INCONCLUSIVE
planned_report_paths:
  - ../../reports/gen0-factorization-mvp-report.md
authority:
  charter: ../../../surrogate-dse-plan.md
  protocol: ../../../ductile-origami-warmstart-experiment-plan.md
  charter_hash: pending
  protocol_hash: pending
lock:
  approved_at: null
  locked_at: null
  lock_sha256: null
supersedes: [M06-Gen0-concepts-only]
---

# S13 — Stage 1 actual Gen0 sampler mechanism

導航：[design index](../README.md)

## 1. Authority 與 change budget

本檔只實作parent D6 actual Gen0 endpoint。D5 cutoff、arms、seeds、`P0`、replay、noise與success gate全部引用parent／lock。

禁止：

- 修改Stage1 guidance；
- 增加H10或natural-stop；
- 將oracle當正式arm；
- 用best取代median guardrail；
- 將三seeds包裝成統計顯著。

## 2. 白話目標

確認S12的offline訊號經過真實Ductile validity、population去重與有限sampler後，Gen0仍比existing guidance與same-entropy shuffled更好。

## 3. Hypothesis 與 falsification

**S13-H1：**Formocast residual guidance在actual Gen0中，提高top-decile exposure，方向性勝existing／proxy與same-entropy shuffled，且median品質、correctness、validity與sampler realization不失守。

反證：

- proposal／replay／candidate order不一致；
- F不勝G或S；
- median guardrail失敗；
- correctness／validity新增失敗；
- sampler envelope顯示systematic anomaly。

## 4. 能與不能說明

能：

- actual Gen0 mechanism是否成立；
- offline prior是否穿過sampler；
- entropy-only、heuristic saturation或plumbing問題。

不能：

- Gen0優勢會維持幾代；
- H10 evaluation efficiency；
- 新cluster replication。

Positive後暫記`FT-WASHOUT-UNTESTED`，由S20解析。

## 5. Inputs

- `D5_PASS`與immutable D5 cutoff；
- S11 weights／shuffle lock；
- S12 correctness／noise evidence；
- resolved initial population `P0`；
- formal paired seed bundle；
- exact sampler／validity／mapping revisions；
- replay／proposal／benchmark schemas。

## 6. Outputs／artifacts

- per-arm CPU sampler replay
- replay envelope／decision
- formal Gen0 proposals
- canonicalized config-set hashes
- proposal lock
- deduplicated benchmark union
- per-slot results／multiplicity
- top-decile hit／median／best／diversity
- correctness／validity ledger
- D6 decision
- `s13-decision.json`

## 7. Controls／measurement boundary

- U／G／F／S arms依parent；
- same paired seeds跨arms；
- proposal先lock、後benchmark；
- population比較不用set iteration order；
- replay seeds與formal seeds分離；
- D5 cutoff固定；
- noise-derived median guardrail固定；
- oracle不進formal result。

## 8. Implementation points

- GA constructor `P0` resolution與assertion；
- exact `SearchSpace.sample(P0)` replay；
- canonical proposal serializer／population hash；
- candidate-order／weight-order validator；
- union benchmark scheduler；
- multiplicity-aware result join；
- D6 gate／failure renderer。

## 9. Acceptance evidence

唯一positive criterion：`D6_MECHANISM_POSITIVE`。

Evidence binding至少包含：

- F vs G／S paired hit deltas；
- median guardrail；
- proposal/replay parity；
- validity／correctness；
- realized entropy／diversity；
- parent／lock／artifact hashes。

## 10. Stop／degrade／failure

- Plumbing mismatch：結果無效，修復需new lock／seeds，不能前進S20。
- F不勝G：`FT-HEURISTIC-SATURATION`或`FT-GEN0-MECHANISM`。
- F不勝S：`FT-ENTROPY-ONLY`。
- Noise／support不足：`FT-INCONCLUSIVE`。
- Positive：授權建立／approve S20。

任何negative不追加generations救回。

## 11. Risks／diagnostics

- constructor改變requested population；
- replay環境與formal環境不一致；
- set order被誤用；
- duplicate union回填multiplicity錯；
- D5 pool overlap造成誤讀；
- shared GPU環境漂移；
- selected Stage1 seeds被誤當Stage2 fresh evidence。

## 12. Planned report／handoff

Milestone與Stage 1 rollup共用：

`../../reports/gen0-factorization-mvp-report.md`

Positive handoff給S20：

- immutable model／genes／weights／hyperparameters；
- fresh-seed independence requirement；
- Stage1 telemetry供`U_floor` prelock；
- selected-seed traces只作diagnostic；
- unresolved washout question。

## 13. Lock checklist

- [ ] D5_PASS evidence綁定
- [ ] P0／arms／formal seeds固定
- [ ] Replay seeds／envelope rule固定
- [ ] Proposal serialization／hash規則固定
- [ ] Benchmark union／join規則固定
- [ ] Correctness／noise guardrail固定
- [ ] Reports／decision paths固定
- [ ] Design approved／locked
