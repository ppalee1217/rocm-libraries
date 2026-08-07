---
checkpoint_id: S30
title: Stage 3 held-out registry and frozen-procedure gate
stage: 3
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R2
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S30
execution_tranche: T-S3-REPLICATION
closure_unit: CU-S3-REPLICATION
hypothesis_id: S30-H1
dependencies:
  - checkpoint_id: S20
    required_edge: S2_DIRECTIONAL_PERSISTENCE_POSITIVE
entry_criteria:
  - S2_DIRECTIONAL_PERSISTENCE_POSITIVE
criterion_refs:
  - S3_REGISTRY_PROCEDURE_LOCKED
failure_ids:
  - FT-BLOCKED-ACCESS
  - FT-BLOCKED-MAPPING
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S3_REGISTRY_PROCEDURE_LOCKED
    target_checkpoint: S31
formal_report_path: reports/staged/s30-heldout-registry-freeze-report.md
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s30-s3-registry-locked.json
tranche_final_report_path: reports/bounded-regime-replication-report.md
terminal_report_integration: terminal_here_on_nonpass_else_integrated_by_S31
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s30-stage3-heldout-registry-freeze-lock.json
implementation_boundary_max:
  - prelabel Stage 3 cluster registry, reserve cutover, denominator and frozen procedure
  - protocol/v1 schemas and lock entries required only by S30
delivery_boundary_max:
  - S30 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/staged/s30-heldout-registry-freeze-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - README.md
  - s30-stage3-heldout-registry-freeze-design.md
forbidden_downstream_roots:
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
suspension_state: suspended_pending_s14
suspension_authority: RESCOPE-STAGE1-OUTCOME-20260807
---

# S30 — Stage 3 held-out registry／procedure freeze

> **2026-08-07 FROZEN pending S14：**本 design 依 user-approved `RESCOPE-STAGE1-OUTCOME-20260807` 保留為 immutable,execution SUSPENDED,pending Stage-1 S14（full-GA baseline-vs-guided real-GPU outcome）結果。本 checkpoint 的 hypothesis、arms、thresholds、edges、failure taxonomy 全部不變、未刪除;恢復僅需 user decision 撤銷本 freeze（移除本 banner 與 frontmatter 的 suspension_state／suspension_authority,並重啟其 DAG edge）。

導航：[active checkpoint index](README.md)｜[experiment plan §16](../ductile-origami-warmstart-experiment-plan.md#16-stage-3-entryfreeze-與-clusters)

## 1. 白話目標

在任何Stage 3 Formocast score或real label出現前，鎖定兩個primary held-out clusters、
optional technical reserve、cutover規則、固定denominator與完整frozen procedure。S30只做
prelabel scientific freeze，不執行D5或GA；day/report/failure/resource estimates另作Layer-C
planning telemetry，不是S30 outcome或edge criterion。

## 2. Hypothesis 與 falsification

**S30-H1：**可依非outcome導向規則預註冊兩個真正獨立、符合parent scope的primary clusters，並在labels前鎖定唯一procedure、reserve cutover與two-slot denominator。

反證或blocked：

- primary cluster identity／selection provenance不完整；
- cluster不獨立、dtype/layout/architecture不符或same-space sizes不足；
- reserve選擇或cutover可在看到score/label後改；
- frozen procedure仍有cluster-specific discretionary retuning；
- 兩個 primary slots、兩個 same-space sizes、reserve priority/cutover、two-slot denominator
  或 frozen procedure任一未鎖定。

## 3. Dependencies、entry 與 outgoing edge

只有S20 committed `S2_DIRECTIONAL_PERSISTENCE_POSITIVE`可開始S30。

唯一outgoing edge：

```text
S3_REGISTRY_PROCEDURE_LOCKED -> S31
```

Single-cluster pilot不能通過S30；若提出，先`blocked-awaiting-user-decision`，即使獲准也不解鎖original S31。

### 3.1 Gate／tranche／closure governance

- `risk_tier=R2`、`scientific_gate=S30`、
  `execution_tranche=T-S3-REPLICATION`、`closure_unit=CU-S3-REPLICATION`。
- 第一筆Stage-3 Formocast score或label前freeze durable machine-readable contract並seal
  effective lock。Stage-3 registry、reserve、recovery、generation、successor與new root
  保留wall-time、CPU/GPU、storage、throughput、repair與thread provenance。
- 七工作日、report day、failure buffer、CPU/GPU/storage與availability estimates全是
  Layer-C planning telemetry：record＋notify。只有direct evidence連到safety、availability、
  完整workload／closure或evidence-integrity風險才safe-pause；它們不形成scientific
  negative、positive criterion或edge。
- Positive只seal compact record
  `protocol/v1/evidence/gate-records/s30-s3-registry-locked.json`，在verified frozen
  edge後留在同一tranche進S31；closure unit尚未完成。
- Negative／inconclusive是terminal internal outcome，產生S30 planned report並停止。
  S31 final report若可達，必須整合S30 record。`committed_projection_state`只在
  CU-S3 terminal commit與post-audit後更新。

## 4. Maximum implementation 與 delivery boundary

允許：

- two-primary cluster registry與prelabel selection provenance；
- 每cluster same-space size identities與scope checks；
- 最多一個optional technical reserve及固定priority；
- access/artifact/mapping technical cutover state machine；
- two-slot denominator；
- Stage 1/2 procedure freeze manifest；
- Layer-C D5／H10／report／failure-buffer planning telemetry（不能改scientific decision）。

禁止：

- 執行Formocast scoring、D5 real measurement或GA；
- 依outcome替換primary、重新排序reserve或更改denominator；
- 在cluster-specific labels後調eligibility、threshold、factorization、arms或gate；
- 把development cluster算入held-out denominator；
- 實作S31 benchmark/results。

## 5. Future effective lock、inputs 與 outputs

Future lock：

`protocol/v1/locks/s30-stage3-heldout-registry-freeze-lock.json`

Inputs：

- S20 positive closure；
- candidate cluster inventory與selection evidence；
- access/artifact/mapping feasibility evidence（無scores/labels）；
- frozen Stage 1/2 procedure；Layer-C actual resource telemetry另記、只作planning；
- exact Plan-B與whitelists。

Outputs：

- primary/reserve cluster registry；
- selection provenance與same-space size registry；
- reserve priority與prelabel cutover rules；
- fixed two-slot denominator；
- frozen procedure/source/analysis manifest；
- machine decision。

## 6. Controls 與 measurement boundary

- Primary與reserve identities同時prelock；
- reserve只處理access、artifact damage或deterministic mapping technical failure；
- replacement必須在該slot第一筆Formocast score與第一筆real label前；
- D5 fail、coverage不足、inconclusive、無eligible genes、oracle或GA negative不能replacement；
- Stage 1/2 development cluster不進denominator；
- S30 artifact root禁止score/label/result fields。

S30只證明replication registry與procedure已凍結，不證明transfer效果。

## 7. Acceptance binding 與 stop matrix

唯一positive criterion是parent的`S3_REGISTRY_PROCEDURE_LOCKED`。

| 狀況 | checkpoint處理 | downstream |
| --- | --- | --- |
| Two-primary registry、procedure、reserve/cutover與two-slot denominator全部鎖定 | positive closeout | S31 |
| Prelabel technical failure且reserve符合規則 | 依prelocked cutover後重驗S30 | 尚無 |
| 只能做single-cluster pilot | `blocked-awaiting-user-decision`；不完成S30 | 無 |
| 暫時資源不可用 | Layer-C record＋notify；有real安全／availability／完整workload／evidence風險才safe-pause | 尚無scientific outcome |
| Score／label提前產生 | held-out seal失效；fresh registry/new lock | 無 |
| Outcome-driven replacement請求 | forbidden plan change | 無 |

## 8. Formal report 與 closeout

S30 positive使用compact gate record
`protocol/v1/evidence/gate-records/s30-s3-registry-locked.json`並繼續同tranche。
S30若negative／inconclusive而成為terminal，唯一formal report才是
`reports/staged/s30-heldout-registry-freeze-report.md`；它記錄registry identities、
selection rule、reserve/cutover、denominator、frozen hashes、Layer-C planning telemetry、seal
audit與先前records，但不虛構S31 outcome。若S31成為tranche final，其report整合S30
positive record，不另建重複positive report。

## 9. Design-consensus record

- Reviewer A objection：若S30與S31合併，cluster registry可能在看到early scores後被「技術性」調整。
- Reviewer B objection：reserve若只鎖候選集合而不鎖priority/cutover time，仍可outcome-driven replacement。
- 採納方案：獨立S30 checkpoint、score/label禁止、primary+reserve+priority+cutover同時鎖、
  固定two-slot denominator；budget只作Layer-C planning telemetry，不是scientific gate。
- 捨棄方案：S31啟動後再選第二cluster、D5 fail後換reserve、single-cluster完成原checkpoint；理由是它們破壞held-out denominator。
- Shared resolution：只有完整prelabel freeze可進S31；pilot屬downgrade且不能取得原edge。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`

### 2026-08-03 Layer-C lifecycle amendment

- `S1-REBASELINE-20260803` 保留兩個primary independent clusters、每cluster exactly兩個
  same-space sizes、最多一個prelocked reserve、fixed priority/cutover、two-slot denominator
  與frozen Stage1/2 procedure為scientific invariants。
- 七工作日、report day、failure buffer、CPU/GPU/storage與availability estimates改為
  record＋notify的Layer-C planning telemetry，不再位於hypothesis、positive criterion、
  machine output或scientific stop matrix。
- Single-cluster仍是original edge外的downgrade，必須新user design decision；本amendment
  沒有降低原two-cluster science。
