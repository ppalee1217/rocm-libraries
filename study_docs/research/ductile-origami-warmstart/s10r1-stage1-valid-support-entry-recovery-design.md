---
checkpoint_id: S10R1
title: Cancelled Stage 1 valid-support recovery tombstone
stage: 1
design_status: approved
execution_status: cancelled
checkpoint_state: BLOCKED
scientific_outcome: not_evaluated
lock_state: superseded
risk_tier: R2
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S10R1
execution_tranche: T-S10R1-CANCELLED
closure_unit: null
governance_event: A32
retention_event: A33
operational_block_reason: user_cancelled_at_safe_boundary
superseded_by: S10R2
hypothesis_id: S10R1-H1
dependencies:
  - checkpoint_id: S00
    required_edge: S00_EVIDENCE_READY
  - checkpoint_id: S10
    required_terminal: CHECKPOINT_COMPLETE_negative_at_48c26297fc6815e6edfcc89b8503e47370fedc53
entry_criteria: []
criterion_refs: []
failure_ids: []
allowed_outgoing_edges: []
formal_report_path: null
blocker_path: null
retirement_manifest_path: retirements/s10r1-diagnostic-retirement.json
forbidden_report_paths:
  - reports/staged/s10r1-stage1-entry-recovery-report.md
forbidden_evidence_reuse:
  - every S10R1 generation-0 or generation-1 empirical, repair, cache, test, lock, selection, mapping, and verification artifact
forbidden_actions:
  - resume or recreate S10R1
  - classify S10R1 as positive, negative, inconclusive, or CHECKPOINT_COMPLETE
  - emit an S10R1 outgoing edge
  - restore retired S10R1 bulk artifacts into the active workspace
---

# S10R1 — Cancelled recovery tombstone

導航：[active checkpoint index](README.md)｜[active S10R2 design](s10r2-stage1-support-aware-entry-recovery-design.md)｜[retirement manifest](retirements/s10r1-diagnostic-retirement.json)

> **Do not execute.** 本檔只保存S10R1的取消、lineage與retention identity。完整舊
> protocol在Git history中可稽核，但不再出現在current active bytes，也不授權任何
> implementation、evidence、report或edge。

## 1. 固定 lifecycle

S10R1依user-authorized `A32`在quiescent safe boundary取消：

- `execution_status=cancelled`
- `checkpoint_state=BLOCKED`
- `scientific_outcome=not_evaluated`
- `edge=null`
- `lock_state=superseded`
- 不是`CHECKPOINT_COMPLETE`
- 不建立scientific formal report

Generation 0只完成被退役的L0與partial CPU selection diagnostics；generation 1只完成
pre-L0 implementation／self-verification，沒有effective L0、selection、mapping、GPU、
noise、decision或formal outcome。包含`DepthU=1024`在內的stochastic non-discovery
不證明support absent，也不是`FT-INCONCLUSIVE`。

S10及其commit
`48c26297fc6815e6edfcc89b8503e47370fedc53`下的terminal negative保持immutable。
S10R1沒有現在或未來的outgoing edge；只有post-audited
`S10R2:S1_ENTRY_GO`可以啟動S11。

## 2. A33 identity-only retention amendment

2026-07-28，使用者要求分析S10R1與S10R2差異、只保留新版研究需要的內容、清除
不需要的S10R1 artifacts並重排後續研究。兩位fresh
`gpt-5.6-sol / reasoning_effort=xhigh` reviewers
`/root/s10r1_cleanup_review_a`與`/root/s10r1_cleanup_review_b`收到相同證據，完成
獨立首輪、一輪交互詰問及同一final candidate review，兩者均`AGREE`：

- S10R2明文禁止重用S10R1 empirical、repair、cache、test、lock、selection、
  mapping與verification artifacts；約34 GB bulk tree與19個untracked S10R1 paths
  沒有合法的S10R2／S11 consumer。
- 「immutable diagnostic provenance」改釋為immutable lifecycle／identity
  tombstone；不再要求永久保留physical bulk bytes。
- A30–A32、source／YAML pins、L0／selection identities、已知resource lower bounds、
  `UNKNOWN`欄位、exact deletion allowlist與post-audit由
  [retirement manifest](retirements/s10r1-diagnostic-retirement.json)保存。
- 先以isolated authority commit固定`authorized_pending_cleanup`，再執行exact
  cleanup；完成後以第二個isolated commit記錄`retired_post_audited`。
- 刪除physical bytes不改S10R1 lifecycle／outcome／edge，也不把歷史wall-time、
  CPU/GPU、storage、throughput、pre-empirical engineering、repair或thread消耗歸零。
- 放棄S10R1逐檔deep forensic replay是明確retention trade-off；manifest只支持取消與
  lineage，不支持任何S10R1 scientific conclusion。

完整討論的主要反對意見已納入：不可先刪後補authority；不可為34 GB非authority
duplicates再支付逐檔content hashing；permission／mount／symlink／hardlink異常必須
fail closed；current retained storage下降不得冒充historical budget reset。

## 3. 與S10R2的設計差異

S10R1舊設計以nominal YAML first／last／sentinel boundaries作mandatory exact-ten
coverage，global及每個conditional stream最高可到`2,851,250` draws，exact-ten可行時
early stop，並把random mapping corpus與sentinel-risk observation緊密綁定。

S10R2改為：

- `supported_witnessed / support_unobserved / support_proven_absent`三態；
- global固定`16,384` draws，加最多15個conditional streams、各`16,384`，總上限
  `262,144`，不得result-driven early stop或extension；
- mandatory mapping atoms機械取
  `prelocked_candidate_atoms ∩ supported_witnessed`；
- 未觀察或proven-absent value只使整個residual gene失去S11 guidance eligibility，
  不改baseline YAML semantics，也不自動阻止其他genes或S10R2 entry；
- exact-ten random mapping與prelocked synthetic native-helper／runtime conformance
  分離；
- fresh contract、lock、implementation、evidence、verification、report與closure。

因此S10R2不是S10R1續跑，也不得從retired artifacts恢復任何state。

## 4. Resource與後續研究 gate

A33只授權retention cleanup與研究重排，不提供wall／CPU／GPU、repair／thread、
pre-empirical或Stage-1七日餘額的數值reset。Cleanup後S10R2仍為
`operational BLOCKED / scientific_outcome=not_evaluated / edge=null`，administrative
reason是`resource_relock_required`，直到新的durable resource decision逐欄記錄
prior consumption、carry-over、reset boundary與future cap。

依賴順序保持：

```text
retirement -> resource relock -> S10R2
S10R2 GO -> S11 -> S12 -> S13
S13 D6 positive -> S20
S20 positive -> S30 -> S31
eligible predictor-specific/oracle-positive + data gate -> S40 -> S41
```

任何terminal negative、inconclusive、resource gate或未核准downgrade都停止；不得用
縮samples／sizes／seeds／arms／clusters保留原claim。
