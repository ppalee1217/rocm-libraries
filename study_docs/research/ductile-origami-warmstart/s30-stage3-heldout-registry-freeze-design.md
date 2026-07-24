---
checkpoint_id: S30
title: Stage 3 held-out registry and frozen-procedure gate
stage: 3
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
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
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s30-stage3-heldout-registry-freeze-lock.json
implementation_boundary_max:
  - prelabel Stage 3 cluster registry, reserve cutover, denominator, frozen procedure and complete budget gate
  - protocol/v1 schemas and lock entries required only by S30
delivery_boundary_max:
  - S30 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/staged/s30-heldout-registry-freeze-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - s30-stage3-heldout-registry-freeze-design.md
forbidden_downstream_roots:
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
---

# S30 — Stage 3 held-out registry／procedure freeze

導航：[active checkpoint index](README.md)｜[experiment plan §16](../ductile-origami-warmstart-experiment-plan.md#16-stage-3-entryfreeze-與-clusters)

## 1. 白話目標

在任何Stage 3 Formocast score或real label出現前，鎖定兩個primary held-out clusters、optional technical reserve、cutover規則、固定denominator、完整frozen procedure與足以完成兩cluster D5/H10的budget。S30只做prelabel freeze，不執行D5或GA。

## 2. Hypothesis 與 falsification

**S30-H1：**可依非outcome導向規則預註冊兩個真正獨立、符合parent scope的primary clusters，並在labels前鎖定唯一procedure、reserve cutover、two-slot denominator與完整resource envelope。

反證或blocked：

- primary cluster identity／selection provenance不完整；
- cluster不獨立、dtype/layout/architecture不符或same-space sizes不足；
- reserve選擇或cutover可在看到score/label後改；
- frozen procedure仍有cluster-specific discretionary retuning；
- 完整two-cluster D5+conditional H10 budget、report day或buffer未確認。

## 3. Dependencies、entry 與 outgoing edge

只有S20 committed `S2_DIRECTIONAL_PERSISTENCE_POSITIVE`可開始S30。

唯一outgoing edge：

```text
S3_REGISTRY_PROCEDURE_LOCKED -> S31
```

Single-cluster pilot或不完整budget不能通過S30；若提出，先`blocked-awaiting-user-decision`，即使獲准也不解鎖original S31。

## 4. Maximum implementation 與 delivery boundary

允許：

- two-primary cluster registry與prelabel selection provenance；
- 每cluster same-space size identities與scope checks；
- 最多一個optional technical reserve及固定priority；
- access/artifact/mapping technical cutover state machine；
- two-slot denominator；
- Stage 1/2 procedure freeze manifest；
- complete D5、conditional H10、report與failure-buffer budget gate。

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
- frozen Stage 1/2 procedure與actual resource telemetry；
- exact Plan-B與whitelists。

Outputs：

- primary/reserve cluster registry；
- selection provenance與same-space size registry；
- reserve priority與prelabel cutover rules；
- fixed two-slot denominator；
- frozen procedure/source/analysis manifest；
- complete budget/cap/buffer evidence；
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
| Two-primary registry、procedure與budget全部鎖定 | positive closeout | S31 |
| Prelabel technical failure且reserve符合規則 | 依prelocked cutover後重驗S30 | 尚無 |
| 只能做single-cluster pilot | `blocked-awaiting-user-decision`；不完成S30 | 無 |
| Complete panel budget不足 | blocked或inconclusive | 無 |
| Score／label提前產生 | held-out seal失效；fresh registry/new lock | 無 |
| Outcome-driven replacement請求 | forbidden plan change | 無 |

## 8. Formal report 與 closeout

唯一formal report：

`reports/staged/s30-heldout-registry-freeze-report.md`

Report記錄registry identities、selection rule、reserve/cutover、denominator、frozen hashes、budget證據與seal audit，但不含任何Stage 3 outcome。只有positive committed closeout解鎖S31。

## 9. Design-consensus record

- Reviewer A objection：若S30與S31合併，cluster registry可能在看到early scores後被「技術性」調整。
- Reviewer B objection：reserve若只鎖候選集合而不鎖priority/cutover time，仍可outcome-driven replacement。
- 採納方案：獨立S30 checkpoint、score/label禁止、primary+reserve+priority+cutover同時鎖、固定two-slot denominator與完整budget gate。
- 捨棄方案：S31啟動後再選第二cluster、D5 fail後換reserve、single-cluster完成原checkpoint；理由是它們破壞held-out denominator。
- Shared resolution：只有完整prelabel freeze可進S31；pilot屬downgrade且不能取得原edge。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`
