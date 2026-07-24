---
milestone_id: S12
title: Stage 1 real-score ranking、prior-mass 與 oracle audit
stage: 1
lifecycle: active
design_status: draft
execution_status: gated
outcome: not_evaluated
decision: pending
hypothesis_id: S12-H1
depends_on:
  - S11:S1_GUIDANCE_LOCKED
entry_gate_ids: [S1_GUIDANCE_LOCKED]
criterion_refs: [D5_PASS, D5_BORDERLINE_INCONCLUSIVE, D5_FAIL]
failure_taxonomy_refs:
  - FT-MODEL-RANK
  - FT-MODEL-MARGINAL
  - FT-HOOK-EXPRESSIVENESS
  - FT-HEURISTIC-SATURATION
  - FT-ENTROPY-ONLY
  - FT-INCONCLUSIVE
planned_report_paths:
  - ../../reports/staged/s12-stage1-real-score-audit-report.md
contributes_to_stage_report: ../../reports/gen0-factorization-mvp-report.md
authority:
  charter: ../../../surrogate-dse-plan.md
  protocol: ../../../ductile-origami-warmstart-experiment-plan.md
  charter_hash: pending
  protocol_hash: pending
lock:
  approved_at: null
  locked_at: null
  lock_sha256: null
supersedes: [M05-concepts-only]
---

# S12 — Stage 1 real-score ranking／prior-mass／oracle audit

導航：[design index](../README.md)

## 1. Authority 與 change budget

本檔實作 parent D3–D5 bounded judgment。Exact pool size、strata、weights、criteria與oracle rules只引用parent。

禁止：

- D5 labels出現後調gene／weights／hyperparameters；
- 替換失敗rows；
- 將oracle回灌正式guidance；
- 只報通過的sizes／configs。

## 2. 白話目標

用預先鎖定的real-score pool回答：Formocast whole ranking是否真的有訊號、factorized prior是否對準高品質區，以及若失敗，問題在model還是hook表達力。

## 3. Hypothesis 與 falsification

**S12-H1：**在S11鎖定的finite frame與real-score judgment pool上，Formocast whole ranking及Formocast-factorized prior能通過D5，並超越existing／proxy與same-entropy shuffled controls。

反證：

- ranking低於D5 gate；
- prior mass不勝baseline或shuffled；
- coverage／ESS／correctness不足；
- cross-fitted oracle也無factorized訊號；
- sampling／analysis lineage不完整。

## 4. 能與不能說明

能：

- bounded whole-ranking與prior-mass evidence；
- model vs marginalization vs hook failure；
- Stage4 data-qualified status。

不能：

- actual Ductile Gen0改善；
- H10 persistence；
- workload-level generalization。

## 5. Inputs

- S11 immutable guidance lock；
- deduplicated catalog與occurrence multiplicity；
- size registry／noise protocol；
- sealed D5 sample／strata／inclusion manifest；
- measurement／correctness runner；
- parent analysis revision與oracle fold rule。

任何real labels前，sample IDs、folds與analysis hashes必須固定。

## 6. Outputs／artifacts

- real-score pool manifest
- per-config／per-size real scores
- correctness／failure ledger
- weighted analysis table
- density-ratio／importance ESS results
- rank／top-decile／prior-mass metrics
- oracle fold manifest
- cross-fitted oracle results
- D5 gate summary
- `qualified_for_stage4_data` evidence
- `s12-decision.json`

## 7. Controls／measurement boundary

- 256 unique configs是analysis units；
- all sizes綁在同config block；
- stratified inclusion weights與multiplicity不可遺失；
- unscored／failed rows保留；
- bootstrap／permutation遵守parent；
- oracle folds以config hash分組；
- model-only lock在labels解封後不可改。

### Stage4 data qualification

`qualified_for_stage4_data`不要求`D5_PASS`，但要求：

- independent cluster ID與pre-label provenance；
- frozen mapping／revision；
-完整judgment pool、inclusion weights、correctness、coverage與lineage；
- 無leakage或outcome amendment。

## 8. Implementation points

- pool materializer／scheduler；
- benchmark result parser；
- design-weighted analysis；
- self-normalized prior-mass estimator；
- ESS／coverage diagnostics；
- cross-fit oracle pipeline；
- D5 decision renderer；
- Stage4 qualification renderer。

## 9. Acceptance evidence

- `D5_PASS`
- `D5_BORDERLINE_INCONCLUSIVE`
- `D5_FAIL`

Report必須逐項回答parent criterion IDs，並綁定raw／weighted結果與artifacts。

## 10. Stop／degrade／failure

- D5_PASS：授權S13。
- Borderline／inconclusive：Stage 1停止，不調參重用pool。
- D5_FAIL：依canonical FT分類。
- Labels已產生但pipeline中止：仍建立正式negative／inconclusive report，不退回blocker memo。
- Predictor failure+oracle positive：可提交S40 trigger evidence，但不自動activate。

## 11. Risks／diagnostics

- multiplicity／survey weight算錯；
- alternative prior importance weights退化；
- score ties與top-decile cutoff不穩；
- measurement missingness集中於gene/value；
- oracle leakage；
- Stage4 qualification與D5_PASS混為一談。

## 12. Planned report／handoff

Milestone report：`../../reports/staged/s12-stage1-real-score-audit-report.md`

若S12 terminal，另finalize：

`../../reports/gen0-factorization-mvp-report.md`

D5_PASS交付S13：

- immutable D5 cutoff／decision；
- correctness／noise evidence；
- arms與proposal-lock inputs；
- cross-fit oracle只作diagnostic。

Predictor-specific failure交付S40：

- trigger evidence；
- oracle／control結果；
- qualified-cluster evidence。

## 13. Lock checklist

- [ ] S11 guidance lock verified
- [ ] Pool／strata／fold IDs固定
- [ ] Inclusion／analysis weights固定
- [ ] Measurement／correctness schedule固定
- [ ] Analysis／bootstrap／permutation revision固定
- [ ] Real labels尚未解封
- [ ] Reports／decision paths固定
- [ ] Design approved／locked
