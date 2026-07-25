---
checkpoint_id: S10
title: Stage 1 access、artifact、mapping 與 noise entry gate
stage: 1
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
hypothesis_id: S10-H1
dependencies:
  - checkpoint_id: S00
    required_edge: S00_EVIDENCE_READY
entry_criteria:
  - S00_EVIDENCE_READY
criterion_refs:
  - S1_ENTRY_GO
  - S1_ENTRY_DEGRADED_PROXY
  - S1_ENTRY_BLOCKED
failure_ids:
  - FT-BLOCKED-ACCESS
  - FT-BLOCKED-MAPPING
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S1_ENTRY_GO
    target_checkpoint: S11
  - criterion_id: S1_ENTRY_DEGRADED_PROXY
    target_checkpoint: S11
    user_review_required: true
formal_report_path: reports/staged/s10-stage1-entry-gate-report.md
blocker_path: reports/gen0-factorization-blocker-memo.md
future_effective_lock_path: protocol/v1/locks/s10-stage1-entry-lock.json
implementation_boundary_max:
  - Stage 1 YAML provenance, environment, access, mapping, size-registry, correctness and noise harnesses
  - protocol/v1 schemas and lock entries required only by S10
delivery_boundary_max:
  - S10 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/staged/s10-stage1-entry-gate-report.md
  - reports/gen0-factorization-blocker-memo.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - README.md
  - s10-stage1-entry-access-mapping-gate-design.md
forbidden_downstream_roots:
  - reports/staged/s11-stage1-model-only-factorization-report.md
  - reports/staged/s12-stage1-real-score-audit-report.md
  - reports/gen0-factorization-mvp-report.md
  - reports/short-horizon-persistence-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
---

# S10 — Stage 1 entry access／artifact／mapping／noise gate

導航：[active checkpoint index](README.md)｜[research charter](../surrogate-dse-plan.md)｜[experiment plan §2](../ductile-origami-warmstart-experiment-plan.md#2-d1d2-entry-gate)

## 1. 白話目標

在S00完整closeout後，確認研究對象與執行條件真的存在：actual generated YAML有可信provenance、gfx942環境可用、config→Formocast mapping不靠猜、sizes共享同一space、correctness與noise足以支撐後續。

## 2. Hypothesis 與 falsification

**S10-H1：**可以在不修改space／weights、不猜required metadata的前提下，鎖定actual YAML、canonical mapping、same-space sizes、gfx942 access、correctness與noise protocol，得到誠實的Stage 1 entry decision。

反證／hard blocker：

- YAML來源、generator revision、candidate order或existing weights不可驗；
- occupancy、effective GSU、math clocks、sentinel或required backend fields只能由default／猜值補；
- actual／proxy candidate space與order parity不可證；
- gfx942 slot未確認，或generate／compile／benchmark／correctness smoke失敗；
- parent cap內noise不可控；
- remaining complete-work budget不符合parent entry rule。

## 3. Dependencies、entry 與 outgoing edges

只有已closeout並committed的`S00_EVIDENCE_READY`可開始S10；不允許提前做YAML／GPU discovery。

- `S1_ENTRY_GO -> S11`
- `S1_ENTRY_DEGRADED_PROXY -> blocked-awaiting-user-decision`；只有user批准downgrade後才可進S11。
- `S1_ENTRY_BLOCKED`沒有downstream edge。

Two-size／reduced-regime也是downgrade，即使parent描述了其判讀方式，仍須decision packet與user review。

## 4. Maximum implementation 與 delivery boundary

允許：

- actual YAML byte copy、SHA、source/generator provenance與search-space manifest；
- canonical ten-config mapping corpus、field parity、round-trip與coverage harness；
- same-space size registry；
- gfx942 environment capture、smoke、correctness與noise pilot；
- actual-guidance／branch-proxy／blocked study-mode decision；
- S10-specific lock、formal report或唯一hard-blocker memo。

禁止：

- 修改search space、groups、candidate order或weights；
- 產生treatment guidance、D5 pool、real-score treatment labels或Gen0 proposals；
- 把branch proxy稱為deployed／production incumbent；
- 建立S11+ artifacts/reports；
- 用M01 artifact、hash、registry、lock或test作PASS evidence。

Future planners必須把maximum boundary縮成exact implementation與delivery whitelists。

## 5. Future effective lock、inputs 與 outputs

Future lock：

`protocol/v1/locks/s10-stage1-entry-lock.json`

它至少綁定S00 closure、committed authorities、Plan-B、exact whitelists、YAML discovery rule、ten-config selection rule、size selection rule、GPU/environment capture、correctness/noise procedure、seeds、study-mode state machine與report targets。

Inputs：

- S00 evidence interface與effective lineage；
- candidate actual YAML／generator provenance；
- mapping source revisions；
- gfx942 reservation evidence；
- parent D1–D2 rules。

Outputs：

- frozen YAML／provenance／search-space manifest；
- environment/revision manifest；
- canonical mapping-10與parity results；
- size registry；
- smoke/correctness evidence；
- noise pilot與`delta_noise`；
- study-mode／entry decision。

## 6. Controls 與 measurement boundary

- actual YAML vs branch proxy逐欄、逐candidate比較；
- same config/size mapping determinism；
- sentinel、boundary、rejection與model-tie cases；
- parent指定anchors與repeat noise measurement；
- source、environment與artifact identities由S00 lineage承載；
- real treatment labels與S11 guidance都尚不存在。

S10只判「可否合法開始」，不判Formocast ranking、factorization或Gen0效果。

## 7. Acceptance binding 與 stop matrix

S10只引用parent的`S1_ENTRY_GO`、`S1_ENTRY_DEGRADED_PROXY`與`S1_ENTRY_BLOCKED`，不在本design改寫門檻。

| 狀況 | checkpoint處理 | report |
| --- | --- | --- |
| Actual YAML guidance完整可追溯 | GO closeout | S10 formal report |
| Exact-space branch proxy成立 | 先`blocked-awaiting-user-decision` | user批准後才formal closeout |
| Two-size／reduced regime | 先`blocked-awaiting-user-decision` | 不得自動降級 |
| Hard access／artifact／mapping blocker | durable `BLOCKED` | blocker memo |
| Outcome-bearing entry evidence已開始後的negative／inconclusive | formal closeout | S10 formal report |
| Implementation defect | `CHANGES_REQUIRED`，限S10修復重驗 | 不得假裝blocker |

## 8. Report、blocker 與 closeout

唯一formal report：

`reports/staged/s10-stage1-entry-gate-report.md`

唯一hard blocker target：

`reports/gen0-factorization-blocker-memo.md`

Blocker memo只能用於未能取得access、可信artifact或canonical mapping；一旦已形成可判讀的checkpoint evidence，negative／inconclusive必須用formal report。Closeout遵守README十步lifecycle；formal report與blocker memo不會同時冒充同一次terminal record。

## 9. Design-consensus record

- Reviewer A objection：舊DAG允許S10 discovery與S00並行，會產生沒有新lineage contract承載的artifact。
- Reviewer B objection：parent雖定義`DEGRADED_PROXY`與two-size判讀，直接自動進S11仍構成未經user批准的scope／claim downgrade。
- 採納方案：strict S00→S10序列；保留parent scientific mode，但在任何proxy/reduced-regime outgoing edge前加入`blocked-awaiting-user-decision`。
- 捨棄方案：並行access discovery、以舊M01 evidence bootstrap、或把proxy當ordinary GO；理由是它們破壞zero-state、comparability與review authority。
- Shared resolution：只有actual-guidance GO可無額外downgrade decision地進S11；hard blocker保留唯一memo path。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`
