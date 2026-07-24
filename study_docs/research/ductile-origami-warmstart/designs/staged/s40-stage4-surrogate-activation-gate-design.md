---
milestone_id: S40
title: Stage 4 surrogate activation 與 data-sufficiency gate
stage: 4
lifecycle: conditional
design_status: draft
execution_status: gated
outcome: not_evaluated
decision: pending
hypothesis_id: S40-H1
depends_on:
  - S12_or_S31:predictor_specific_failure_and_oracle_positive
entry_gate_ids: [S4_TRIGGER_ELIGIBLE, S4_DATA_GATE_PASS]
criterion_refs: [S4_TRIGGER_ELIGIBLE, S4_DATA_GATE_PASS, S4_ACTIVATE]
failure_taxonomy_refs:
  - FT-SURROGATE-DATA-INSUFFICIENT
  - FT-MODEL-RANK
  - FT-MODEL-MARGINAL
  - FT-REGIME-HETEROGENEITY
planned_report_paths:
  - ../../reports/staged/s40-stage4-activation-report.md
data_insufficiency_memo_paths:
  - ../../reports/learned-residual-data-insufficiency-memo.md
authority:
  charter: ../../../surrogate-dse-plan.md
  protocol: ../../../ductile-origami-warmstart-experiment-plan.md
  charter_hash: pending
  protocol_hash: pending
lock:
  approved_at: null
  locked_at: null
  lock_sha256: null
supersedes: []
---

# S40 — Stage 4 surrogate activation／data-sufficiency gate

導航：[design index](../README.md)

## 1. Authority 與 change budget

本檔只判斷是否有科學與資料理由建立S41；不選model、features或hyperparameters，也不執行surrogate training。

禁止：

- 把任何negative都解釋成需要surrogate；
- 降低四-cluster data floor；
- 使用row-random split；
- 為達資料數連續追加clusters直到成功。

## 2. 白話目標

先確認失敗真的是predictor問題、hook仍可表達，且有足夠獨立clusters做cluster-held-out研究；條件不足就不要開新題目。

## 3. Hypothesis 與 falsification

**S40-H1：**上游有predictor-specific、oracle-positive evidence，禁止trigger均不存在，且至少四個Stage4 data-qualified clusters可在cap內鎖定，因此建立S41是合理且可驗證的。

反證：

- hook expressiveness、plumbing、Gen0、washout或heuristic saturation才是主因；
- oracle不支持factorized main effects；
- 合格clusters不足；
- prospective fourth cluster無法在cap內取得；
- data lineage／inclusion／correctness不完整。

## 4. 能與不能說明

能：

- Stage4是否科學上eligible；
- 資料是否足夠；
- 是否授權建立S41。

不能：

- learned residual一定有效；
- 模型family或features該選什麼；
- actual GA會改善。

## 5. Trigger inputs

允許來源：

- S12：`FT-MODEL-RANK`或`FT-MODEL-MARGINAL`，但cross-fitted oracle穩定positive；
- S31：predictor heterogeneity，且失敗cluster oracle支持同一hook。

禁止來源：

- access／mapping；
- `FT-HOOK-EXPRESSIVENESS`；
- plumbing；
- Gen0 mechanism failure；
- H10 washout／regression；
- heuristic saturation；
- noise／coverage不足。

## 6. Stage4 data-qualified cluster

不要求`D5_PASS`。每cluster至少：

- independent search-space ID；
- pre-label selection provenance；
- frozen mapping／revision；
- 256 unique judgment configs；
- 至少2 sizes；
- inclusion probabilities／analysis weights；
- correctness、coverage、failure rows與lineage完整；
- 無label leakage／outcome-driven amendment。

Mapping靠猜、coverage／correctness不完整或pool不足者不qualified。

## 7. Prospective fourth cluster

若已有3個qualified clusters，可在parent time/resource cap內新增最多1個：

- cluster ID／selection rule在labels前鎖定；
- 不依前三clusters結果挑容易regime；
- 只取得label pool，不跑GA；
- labels不得回流調model後再當test。

少於3個，或第四cluster無法取得：

`FT-SURROGATE-DATA-INSUFFICIENT`

## 8. Outputs／artifacts

- trigger evidence bundle
- forbidden-trigger checklist
- qualified-cluster registry
- per-cluster qualification evidence
- prospective fourth-cluster lock（若適用）
- data-floor decision
- parent／source hashes
- `s40-decision.json`

## 9. Acceptance evidence

- `S4_TRIGGER_ELIGIBLE`
- `S4_DATA_GATE_PASS`
- `S4_ACTIVATE`

只有前兩項同時通過才可ACTIVATE並建立S41。

## 10. Stop／outcomes

- 無合法trigger：`not_activated`，由上游report引用。
- Trigger成立但data不足：negative／`FT-SURROGATE-DATA-INSUFFICIENT`。
- Trigger與data都過：positive activation decision；這不是surrogate效果positive。
- Artifact／lineage不足：inconclusive或blocked。

## 11. Risks／diagnostics

- D5_PASS被誤當data qualification；
- predictor failure其實是mapping／coverage；
- clusters共享search-space identity而非獨立；
- prospective cluster按結果挑選；
- sizes被錯算clusters；
- activation report被誤讀成model成功。

## 12. Planned report／handoff

Milestone report：`../../reports/staged/s40-stage4-activation-report.md`

Data不足memo：`../../reports/learned-residual-data-insufficiency-memo.md`

ACTIVATE後才建立：

`s41-stage4-learned-residual-analysis-design.md`

Handoff必須包含：

- qualified cluster registry；
- prospective-test身分；
- forbidden leakage rules；
- trigger／oracle evidence；
-尚未決定的model implementation問題。

## 13. Lock checklist

- [ ] Trigger／forbidden rules引用固定
- [ ] Cluster qualification schema固定
- [ ] Data-floor criterion引用固定
- [ ] Prospective fourth-cluster規則固定
- [ ] Parent／source hashes固定
- [ ] Report／decision paths固定
- [ ] Design approved／locked
