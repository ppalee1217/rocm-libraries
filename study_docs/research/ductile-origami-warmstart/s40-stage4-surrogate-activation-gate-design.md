---
checkpoint_id: S40
title: Stage 4 surrogate activation and data-sufficiency gate
stage: 4
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_activated
lock_state: absent
checkpoint_instance_state: not_instantiated
risk_tier: R2
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S40
execution_tranche: T-S4-LEARNED-RESIDUAL
closure_unit: CU-S4-LEARNED-RESIDUAL
hypothesis_id: S40-H1
dependencies:
  - checkpoint_id: S12_or_S31
    required_edge: predictor_specific_failure_and_oracle_positive
  - readiness: full_stage4_data_floor
    relation: administrative_instantiation_prerequisite
entry_criteria:
  - predictor_specific_failure_and_oracle_positive_evidence_available
  - full_stage4_data_readiness_available
criterion_refs:
  - S4_TRIGGER_ELIGIBLE
  - S4_DATA_GATE_PASS
  - S4_ACTIVATE
failure_ids:
  - FT-MODEL-RANK
  - FT-MODEL-MARGINAL
  - FT-REGIME-HETEROGENEITY
  - FT-INCONCLUSIVE
operational_readiness_ids:
  - FT-SURROGATE-DATA-INSUFFICIENT
allowed_outgoing_edges:
  - criterion_id: S4_ACTIVATE
    target_checkpoint: S41
formal_report_path: reports/staged/s40-stage4-activation-report.md
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s40-s4-activate.json
tranche_final_report_path: reports/learned-residual-surrogate-report.md
terminal_report_integration: report_only_after_instantiation_else_no_report
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

S40 只有在上游已產生合法 predictor-specific + oracle-positive trigger，且完整 data floor
同時 ready 時才 instantiated／locked。未滿足前它不是一個正在執行的 scientific gate，
不建立 report、decision 或 lock。真正 instantiated 後，S40只判 forbidden causes、
cluster qualification與activation；不選features、不訓練model、不跑GA。

## 2. Hypothesis 與 falsification

**S40-H1：**在 legal trigger 與 complete data readiness 已先使 S40 instantiated 的前提下，
所有 forbidden causes均不存在，且 independent qualified clusters與prospective test條件
可完整鎖定，因此S41具有可驗證的科學基礎。

反證或inconclusive：

- 主因其實是access、mapping、hook expressiveness、plumbing、Gen0、washout、regression、heuristic saturation或單純coverage/noise；
- oracle不支持factorized main effects；
- 已宣稱ready的qualified clusters其實不獨立或不符合frozen data floor；
- inclusion、correctness、coverage、mapping或lineage不完整；
- prospective fourth cluster依outcome選擇。

## 3. Dependencies、entry 與 outgoing edge

S40只接受：

- S12 committed predictor-specific failure + oracle-positive edge；或
- S31 committed predictor heterogeneity + oracle-positive edge。

沒有合法trigger時，S40是`not_activated`，不建立S40 report、decision、lock或commit。
Trigger成立但data incomplete時，狀態是
`data_pending / not_activated / not_evaluated`；同樣不建立S40 report、decision或lock，也
不形成learned-surrogate scientific negative。只有新的prelabel-qualified data出現時才
reevaluate readiness。`FT-SURROGATE-DATA-INSUFFICIENT`只作operational readiness
provenance，不是scientific outcome。

唯一outgoing edge：

```text
S4_ACTIVATE -> S41
```

只有trigger與full data readiness同時成立，S40才instantiated，之後才可能形成
`S4_ACTIVATE`或依frozen instantiated outcome matrix判讀。

### 3.1 Gate／tranche／closure governance

- `risk_tier=R2`、`scientific_gate=S40`、
  `execution_tranche=T-S4-LEARNED-RESIDUAL`、
  `closure_unit=CU-S4-LEARNED-RESIDUAL`。
- Trigger與data readiness只是instantiation prerequisites；兩者都成立後，才freeze
  durable machine-readable contract並seal S40 effective lock。S40+S41 resource provenance
  跨cluster、generation、successor與new root保留。
- 五工作日是Layer-C planning telemetry：record＋notify，不是scientific result gate。
  不以較弱split／data floor救回；data incomplete保持data-pending，而不是為趕timebox
  terminalize為negative。
- `S4_ACTIVATE`只seal compact record
  `protocol/v1/evidence/gate-records/s40-s4-activate.json`，在verified frozen edge後
  留在同一tranche進S41；closure unit尚未完成。
- 只有instantiated後的negative／inconclusive才是terminal internal outcome並產生S40
  report。Not-activated/data-pending都沒有S40 report。若進S41，S41 final report整合S40 record。
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

- S40 instantiation前同時要求legal predictor-specific + oracle-positive trigger與完整data
  readiness；缺一就沒有S40 lock／decision／report；
- `qualified_for_stage4_data`不要求D5 PASS，但每個parent-required evidence field都必須完整；
- sizes不當clusters，shared search-space identity不當independent cluster；
- prospective cluster ID／selection rule在labels前鎖定；
- prospective labels不得回流selection後再當test；
- S40 artifact禁止model coefficients、predictions或GA outcome；
- trigger與data gate分開判讀。

Data floor維持exactly：4個independent clusters；每cluster `>=256` unique configs且
`>=2` sizes；total `>=1024` configs與`>=2048` config-size labels；complete inclusion、
correctness、mapping與coverage。已有3個qualified clusters時最多新增1個prospectively
sealed fourth cluster。

S40 positive只代表「可以公平測S41」，不代表surrogate有效。

## 7. Acceptance binding 與 stop matrix

| 狀況 | checkpoint處理 | downstream |
| --- | --- | --- |
| Trigger與data gate皆通過 | positive activation closeout | S41 |
| 無合法trigger | 上游記`not_activated`；S40不執行 | 無 |
| Trigger成立但data不足 | `data_pending / not_activated / not_evaluated`；只記operational `FT-SURROGATE-DATA-INSUFFICIENT`，新prelabel-qualified data出現才重查 | 無 |
| Instantiation後才發現forbidden cause | negative；predictor substitution不適用 | 無 |
| Instantiation後才發現artifact／lineage聲明不實 | inconclusive／evidence invalid，依frozen matrix處理 | 無 |
| 提議降低data floor／split品質 | `blocked-awaiting-user-decision` | 無 |

## 8. Formal report 與 closeout

S40 positive使用compact gate record
`protocol/v1/evidence/gate-records/s40-s4-activate.json`並繼續同tranche。S40若data
readiness不足則尚未instantiated，**不建立formal report**。只有instantiation後的
forbidden cause或inconclusive成為terminal時，唯一formal report才是
`reports/staged/s40-stage4-activation-report.md`。若S41成為
tranche final，S41 report整合S40 positive record，不另建重複positive report。

## 9. Design-consensus record

- Reviewer A historical objection：舊design把data insufficiency視為scientific negative；
  2026-08-03 amendment改採activation-before-instantiation，該舊結論已superseded。
- Reviewer B objection：任何upstream negative都啟動surrogate，會混淆predictor failure與hook/plumbing/GA failure。
- 採納方案：只接受predictor-specific+oracle-positive edge、明列forbidden causes、S40
  完全禁止training；2026-08-03另核准data readiness也必須在instantiation前成立。
- 捨棄方案：general fallback surrogate、row split或outcome-driven追加clusters直到floor；
  data-pending也不製造scientific negative。
- Current resolution：無trigger或data incomplete都不instantiate S40；只有trigger+full
  readiness進gate，且只有`S4_ACTIVATE`可進S41。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`

### 2026-08-03 activation-before-instantiation amendment

- Two reviewers完成兩輪cross-examination與一輪evidence-backed final後均`AGREE`，使用者核准。
- No trigger=`not_activated`；trigger但data incomplete=`data_pending / not_activated /
  not_evaluated`。兩者都沒有S40 report、decision、lock或learned-surrogate negative。
- `FT-SURROGATE-DATA-INSUFFICIENT`只作operational readiness provenance；五日只作Layer-C
  planning telemetry。
- 完整four-cluster/256/two-size/1024/2048 data floor、最多一個prospective fourth cluster、
  instantiated後的forbidden-cause audit、`S4_ACTIVATE`與no-training boundary保持。
