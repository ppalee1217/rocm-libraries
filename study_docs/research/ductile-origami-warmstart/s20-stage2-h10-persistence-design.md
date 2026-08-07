---
checkpoint_id: S20
title: Stage 2 fixed-H10 short-horizon persistence
stage: 2
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R1
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S20
execution_tranche: T-S20
closure_unit: CU-S20
hypothesis_id: S20-H1
dependencies:
  - checkpoint_id: S13
    required_edge: D6_MECHANISM_POSITIVE
entry_criteria:
  - D6_MECHANISM_POSITIVE
criterion_refs:
  - S2_DIRECTIONAL_PERSISTENCE_POSITIVE
failure_ids:
  - FT-PERSISTENCE-WASHOUT
  - FT-SHORT-HORIZON-REGRESSION
  - FT-EVALUATION-SUPPORT
  - FT-ENTROPY-ONLY
  - FT-PLUMBING
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S2_DIRECTIONAL_PERSISTENCE_POSITIVE
    target_checkpoint: S30
formal_report_path: reports/short-horizon-persistence-report.md
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s20-s2-persistence-positive.json
tranche_final_report_path: reports/short-horizon-persistence-report.md
terminal_report_integration: standalone_report_integrates_s20_gate_record
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s20-stage2-h10-persistence-lock.json
implementation_boundary_max:
  - fixed H10 G/F/S execution, fresh-seed pairing, checkpoint parity, common support, AUC, late retention and remeasurement
  - protocol/v1 schemas and lock entries required only by S20
delivery_boundary_max:
  - S20 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/short-horizon-persistence-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - README.md
  - s20-stage2-h10-persistence-design.md
forbidden_downstream_roots:
  - reports/staged/s30-heldout-registry-freeze-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
suspension_state: suspended_pending_s14
suspension_authority: RESCOPE-STAGE1-OUTCOME-20260807
---

# S20 — Stage 2 fixed-H10 short-horizon persistence

> **2026-08-07 FROZEN pending S14：**本 design 依 user-approved `RESCOPE-STAGE1-OUTCOME-20260807` 保留為 immutable,execution SUSPENDED,pending Stage-1 S14（full-GA baseline-vs-guided real-GPU outcome）結果。本 checkpoint 的 hypothesis、arms、thresholds、edges、failure taxonomy 全部不變、未刪除;恢復僅需 user decision 撤銷本 freeze（移除本 banner 與 frontmatter 的 suspension_state／suspension_authority,並重啟其 DAG edge）。

導航：[active checkpoint index](README.md)｜[experiment plan §§13–15](../ductile-origami-warmstart-experiment-plan.md#part-ii--stage-2short-horizon-persistence-protocol)

## 1. 白話目標

把S13的Gen0 advantage放進固定H10主實驗，檢驗它能否穿過mutation／selection transitions，在相同complete-evaluation support上改善G/F/S quality trajectory，而且final independently remeasured quality不退步。H5只是blinded operational checkpoint，不能取代H10。

## 2. Hypothesis 與 falsification

**S20-H1：**使用parent固定的G/F/S arms與全部fresh paired seeds，F在Gen0後common evaluation support上的best-so-far log-quality AUC同時勝G與S，late retention成立，final remeasurement通過noise-derived non-inferiority。

反證或inconclusive：

- F-G或F-S AUC／paired direction未過；
- H10 late retention失敗；
- final remeasurement regression；
- formal run未達prelocked common support；
- checkpoint/resume parity、mapping、plumbing或correctness失敗；
- Stage 1 selected seeds被混入formal independent denominator。

## 3. Dependencies、entry 與 outgoing edge

只有S13 committed `D6_MECHANISM_POSITIVE`可開始S20。Entry還必須確認完整G/F/S×fresh seeds×H10 budget、report day與failure buffer。

唯一outgoing edge：

```text
S2_DIRECTIONAL_PERSISTENCE_POSITIVE -> S30
```

`S2_H5_RESOURCE_BOUNDED_PILOT`沒有entry權。資源只夠H5時必須decision packet並停在`blocked-awaiting-user-decision`；即使user批准pilot，它也不能完成S20或解鎖S30。

### 3.1 Gate／tranche／closure governance

- `risk_tier=R1`、`scientific_gate=S20`、`execution_tranche=T-S20`、
  `closure_unit=CU-S20`；本checkpoint是standalone tranche與closure。
- Entry依governance baseline
  `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`先做cumulative wall-time／CPU／GPU／
  storage／throughput preflight，再seal durable machine-readable contract與
  effective lock。依`A46_reviewer_governed_uncapped_provenance`，repair沒有numeric
  maximum；repair count與history只作traceable provenance，不是stop、approval、success或
  completion criterion。Reviewer-governed、contract-preserving repairs持續進行；scientific
  sample、thread、downgrade、evidence、safety與resource boundaries仍是hard boundaries，且
  任何generation、resume、successor或new root都不能重置這些boundaries。
- Stage 2 hands-on target 4工作日與5工作日planning envelope都只作Layer-C telemetry：
  operator記錄observed throughput／projection並通知後繼續完整frozen workload。只有direct
  evidence連到unsafe operation、platform／allocation不可用、full H10×G/F/S×fresh-seed
  workload／verification／artifact preservation無法完成、optional stopping、evidence
  integrity或明確frozen scientific resource boundary時才safe-pause。Day count本身不會
  terminalize、判inconclusive或形成edge；任何縮H10／arms／seeds仍須downgrade user gate。
- Positive另seal compact record
  `protocol/v1/evidence/gate-records/s20-s2-persistence-positive.json`；positive、
  negative與inconclusive均由`reports/short-horizon-persistence-report.md`形成
  terminal decision record。
- `live_run_state`與`committed_projection_state`分離；只有CU-S20 terminal commit
  及post-audit後更新後者。

## 4. Maximum implementation 與 delivery boundary

允許：

- parent G/F/S arms、fresh paired seeds與fixed H10 runner；
- generation state、complete fitness matrix、evaluation support與trajectory capture；
- continuous-vs-resume parity；
- prelabel `U_floor` materialization；
- AUC、late retention、final champion independent remeasurement與failure diagnosis。

禁止：

- 重調Stage 1 guidance、genes、weights或hyperparameters；
- 依H5 comparative outcome決定是否跑H6–H10；
- 以H5 pilot、selected Stage 1 seeds或partial arms滿足S20；
- 修改fitness、mutation、selection、survival、size allocation或stop semantics；
- 開始S30 registry工作。

## 5. Future effective lock、inputs 與 outputs

Future lock：

`protocol/v1/locks/s20-stage2-h10-persistence-lock.json`

它綁定S13 closure、frozen YAML/space/sizes/groups/weights/model/genes/hyperparameters、fresh seed bundle、H10 configuration、complete-evaluation semantics、`U_floor` rule與value、checkpoint parity、caps、Plan-B、exact whitelists與report target。

Outputs：

- fresh-seed manifest；
- `U_floor` decision；
- checkpoint/resume parity；
- per-arm/seed proposals、complete evaluations與trajectories；
- AUC、H5 diagnostic、H10 late retention與support；
- champion remeasurements、correctness/plumbing evidence與machine decision。

## 6. Controls 與 measurement boundary

- G／F／S共用paired fresh seeds與environment blocks；
- Stage 1 selected seeds只作continuity diagnostic；
- primary x-axis只計全部locked sizes complete且correct的candidate evaluation；
- primary AUC全部積分到同一prelocked`U_floor`；
- generation-end right-continuous step function，不用batch內set order製造anytime curve；
- H5 comparative quality保持sealed，checkpoint只看health／integrity；
- final quality獨立重測。

S20回答single-development-cluster H10 persistence，不是full convergence或system speedup。

## 7. Acceptance binding 與 stop matrix

`S2_DIRECTIONAL_PERSISTENCE_POSITIVE`的arms、seed count、AUC、late retention、noise guardrail與support rules全部引用parent。

| 狀況 | outcome／failure | downstream |
| --- | --- | --- |
| 全部S2 criteria通過 | positive closeout | S30 |
| AUC／late retention失敗 | `FT-PERSISTENCE-WASHOUT` | 無 |
| AUC正向但final regression | `FT-SHORT-HORIZON-REGRESSION` | 無 |
| 任一formal run未達`U_floor` | `FT-EVALUATION-SUPPORT`／inconclusive | 無 |
| F不勝S | `FT-ENTROPY-ONLY` | 無 |
| H5-only／縮seed／縮arm提案 | `blocked-awaiting-user-decision` | 無 |
| Technical defect | active checkpoint修復並重驗 | 無，直到closeout |

## 8. Formal report 與 closeout

唯一formal report：

`reports/short-horizon-persistence-report.md`

Report需完整記錄每個fresh pair、support、AUC、late retention、remeasurement、H5 handling、resume evidence與failure attribution。Negative／inconclusive照常closeout；只有positive committed closeout解鎖S30。

## 9. Design-consensus record

- Reviewer A objection：H5 checkpoint若能看comparative quality，會形成outcome-dependent optional stopping。
- Reviewer B objection：使用Stage 1 seeds或observed minimum support，會破壞fresh evidence與common-support estimand。
- 採納方案：entry即承諾H10、H5只看operational health、fresh formal seeds、prelabel`U_floor`與independent final remeasurement。
- 捨棄方案：H5取代H10、漂亮才延長、observed support事後下修、selected-seed混入formal denominator；理由是它們降低evidence strength並改變acceptance。
- Shared resolution：完整H10 positive是唯一S30 edge；任何resource-bounded pilot需user review且無解鎖權。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`
