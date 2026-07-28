---
checkpoint_id: S40
title: Stage 4 surrogate activation and data-sufficiency gate
stage: 4
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R2
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S40
execution_tranche: T-S4-LEARNED-RESIDUAL
closure_unit: CU-S4-LEARNED-RESIDUAL
hypothesis_id: S40-H1
dependencies:
  - checkpoint_id: S12_or_S31
    required_edge: predictor_specific_failure_and_oracle_positive
entry_criteria:
  - predictor_specific_failure_and_oracle_positive_evidence_available
criterion_refs:
  - S4_TRIGGER_ELIGIBLE
  - S4_DATA_GATE_PASS
  - S4_ACTIVATE
failure_ids:
  - FT-SURROGATE-DATA-INSUFFICIENT
  - FT-MODEL-RANK
  - FT-MODEL-MARGINAL
  - FT-REGIME-HETEROGENEITY
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S4_ACTIVATE
    target_checkpoint: S41
formal_report_path: reports/staged/s40-stage4-activation-report.md
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s40-s4-activate.json
tranche_final_report_path: reports/learned-residual-surrogate-report.md
terminal_report_integration: terminal_here_on_nonactivate_else_integrated_by_S41
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s40-stage4-activation-lock.json
implementation_boundary_max:
  - trigger adjudication, forbidden-cause audit, cluster qualification, prospective-cluster seal and data-floor decision
  - protocol/v1 schemas and lock entries required only by S40
delivery_boundary_max:
  - S40 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/staged/s40-stage4-activation-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - README.md
  - s40-stage4-surrogate-activation-gate-design.md
forbidden_downstream_roots:
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
---

# S40 — Stage 4 surrogate activation／data-sufficiency gate

導航：[active checkpoint index](README.md)｜[experiment plan §18](../ductile-origami-warmstart-experiment-plan.md#18-stage-4-trigger-與-data-gate)

## 1. 白話目標

只有上游證明失敗真的是predictor-specific、oracle仍支持factorized main effects時，才啟動S40。S40只判trigger、forbidden causes、cluster qualification與parent data floor；不選features、不訓練model、不跑GA。

## 2. Hypothesis 與 falsification

**S40-H1：**上游存在合法predictor-specific、oracle-positive evidence，所有forbidden causes均不存在，而且parent要求的independent qualified clusters與prospective test條件可完整鎖定，因此S41具有可驗證的科學基礎。

反證或inconclusive：

- 主因其實是access、mapping、hook expressiveness、plumbing、Gen0、washout、regression、heuristic saturation或單純coverage/noise；
- oracle不支持factorized main effects；
- qualified clusters不足或不獨立；
- inclusion、correctness、coverage、mapping或lineage不完整；
- prospective fourth cluster無法在cap內取得或依outcome選擇。

## 3. Dependencies、entry 與 outgoing edge

S40只接受：

- S12 committed predictor-specific failure + oracle-positive edge；或
- S31 committed predictor heterogeneity + oracle-positive edge。

沒有合法trigger時，S40不執行；由上游report記`not_activated`，不建立S40 report或commit。

唯一outgoing edge：

```text
S4_ACTIVATE -> S41
```

Trigger成立但data不足是S40 formal scientific negative，不是blocker memo。

### 3.1 Gate／tranche／closure governance

- `risk_tier=R2`、`scientific_gate=S40`、
  `execution_tranche=T-S4-LEARNED-RESIDUAL`、
  `closure_unit=CU-S4-LEARNED-RESIDUAL`。
- 任何trigger adjudication或prospective label前，依
  `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`完成cumulative resource preflight，
  freeze durable machine-readable contract並seal effective lock。S40+S41所有
  wall-time、CPU/GPU、storage、throughput、repair與thread consumption跨cluster、
  generation、successor與new root累計。
- Stage 4 hard cap仍精確為5工作日且不是完成承諾；data floor或prospective cluster
  無法在剩餘cap內完成時，照原criterion terminal，不以較弱split／data floor救回。
- `S4_ACTIVATE`只seal compact record
  `protocol/v1/evidence/gate-records/s40-s4-activate.json`，在verified frozen edge後
  留在同一tranche進S41；closure unit尚未完成。
- Trigger成立後的negative／inconclusive是terminal internal outcome，產生S40
  planned report。若進S41，S41 final report整合S40 record。
- `live_run_state`與`committed_projection_state`分離；後者只在CU-S4 terminal
  commit與post-audit後更新。

## 4. Maximum implementation 與 delivery boundary

允許：

- upstream trigger evidence與forbidden-cause adjudication；
- per-cluster independent identity、prelabel provenance、mapping/revision、judgment pool、weights、correctness、coverage與lineage qualification；
- parent prospective fourth-cluster seal與label-only acquisition gate；
- data-floor decision與activation record。

禁止：

- model family、feature、hyperparameter或preprocessing selection；
- fitting/predicting learned residual；
- 降低cluster/config/size data floor或使用row-random split；
- 連續追加clusters直到成功；
- 把D5 PASS當成data qualification充分條件；
- 建立S41 results或actual GA。

## 5. Future effective lock、inputs 與 outputs

Future lock：

`protocol/v1/locks/s40-stage4-activation-lock.json`

Inputs：

- upstream closeout與trigger/oracle/control evidence；
- candidate qualified-cluster datasets及完整lineage；
- parent forbidden-cause與data-floor rules；
- prospective cluster selection rule（如適用）；
- Plan-B與exact whitelists。

Outputs：

- trigger evidence bundle；
- forbidden-cause checklist；
- qualified-cluster registry與per-cluster evidence；
- prospective fourth-cluster lock（如適用）；
- data-floor／activation machine decision。

## 6. Controls 與 measurement boundary

- `qualified_for_stage4_data`不要求D5 PASS，但每個parent-required evidence field都必須完整；
- sizes不當clusters，shared search-space identity不當independent cluster；
- prospective cluster ID／selection rule在labels前鎖定；
- prospective labels不得回流selection後再當test；
- S40 artifact禁止model coefficients、predictions或GA outcome；
- trigger與data gate分開判讀。

S40 positive只代表「可以公平測S41」，不代表surrogate有效。

## 7. Acceptance binding 與 stop matrix

| 狀況 | checkpoint處理 | downstream |
| --- | --- | --- |
| Trigger與data gate皆通過 | positive activation closeout | S41 |
| 無合法trigger | 上游記`not_activated`；S40不執行 | 無 |
| Trigger成立但data不足 | negative `FT-SURROGATE-DATA-INSUFFICIENT` formal closeout | 無 |
| Forbidden cause成立 | negative；predictor substitution不適用 | 無 |
| Artifact／lineage不足 | inconclusive formal closeout | 無 |
| 提議降低data floor／split品質 | `blocked-awaiting-user-decision` | 無 |

## 8. Formal report 與 closeout

S40 positive使用compact gate record
`protocol/v1/evidence/gate-records/s40-s4-activate.json`並繼續同tranche。S40若data
insufficiency、forbidden cause或inconclusive而成為terminal，唯一formal report是
`reports/staged/s40-stage4-activation-report.md`；不另建blocker memo。若S41成為
tranche final，S41 report整合S40 positive record，不另建重複positive report。

## 9. Design-consensus record

- Reviewer A objection：把data insufficiency寫成blocker memo會把可判讀的scientific negative排除在formal outcome lifecycle外。
- Reviewer B objection：任何upstream negative都啟動surrogate，會混淆predictor failure與hook/plumbing/GA failure。
- 採納方案：只接受predictor-specific+oracle-positive edge、明列forbidden causes、data insufficiency作formal negative、S40完全禁止training。
- 捨棄方案：general fallback surrogate、data-insufficiency memo、row split或追加clusters直到floor；理由是它們迴避trigger因果與independent validation。
- Shared resolution：無trigger由上游記not_activated；有trigger後S40一定以formal report結束，只有ACTIVATE可進S41。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`
