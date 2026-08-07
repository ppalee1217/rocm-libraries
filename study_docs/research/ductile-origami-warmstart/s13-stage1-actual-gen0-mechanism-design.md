---
checkpoint_id: S13
title: Stage 1 actual Gen0 sampler mechanism
stage: 1
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R1
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S13
execution_tranche: T-S1-MECHANISM
closure_unit: CU-S1-MECHANISM
hypothesis_id: S13-H1
dependencies:
  - checkpoint_id: S12
    required_edge: D5_PASS
entry_criteria:
  - D5_PASS
criterion_refs:
  - D6_MECHANISM_POSITIVE
failure_ids:
  - FT-PLUMBING
  - FT-GEN0-MECHANISM
  - FT-HEURISTIC-SATURATION
  - FT-ENTROPY-ONLY
  - FT-WASHOUT-UNTESTED
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: D6_MECHANISM_POSITIVE
    target_checkpoint: S20
formal_report_path: reports/gen0-factorization-mvp-report.md
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s13-d6-mechanism-positive.json
tranche_final_report_path: reports/gen0-factorization-mvp-report.md
terminal_report_integration: integrates_S11_S12_compact_records_and_S13_terminal_evidence
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s13-stage1-actual-gen0-lock.json
implementation_boundary_max:
  - actual Gen0 P0 resolution, replay, proposal lock, deduplicated benchmark union and D6 analysis
  - protocol/v1 schemas and lock entries required only by S13
delivery_boundary_max:
  - S13 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/gen0-factorization-mvp-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - README.md
  - s13-stage1-actual-gen0-mechanism-design.md
forbidden_downstream_roots:
  - reports/short-horizon-persistence-report.md
  - reports/staged/s30-heldout-registry-freeze-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
suspension_state: suspended_pending_s14
suspension_authority: RESCOPE-STAGE1-OUTCOME-20260807
---

# S13 — Stage 1 actual Gen0 sampler mechanism

> **2026-08-07 FROZEN pending S14：**本 design 依 user-approved `RESCOPE-STAGE1-OUTCOME-20260807` 保留為 immutable,execution SUSPENDED,pending Stage-1 S14 結果。S13 的 Gen0 realization/replay machinery 折入 S14 作 optional gen-0 diagnostic;S13 D6 不再是 S14 的前置。本 checkpoint 的 hypothesis、arms、thresholds、edges、failure taxonomy 全部不變、未刪除;恢復僅需 user decision 撤銷本 freeze。

導航：[active checkpoint index](README.md)｜[experiment plan §7](../ductile-origami-warmstart-experiment-plan.md#7-d6-actual-gen0-endpoint)

## 1. 白話目標

只做actual Gen0：解析constructor的`P0`、鎖定formal proposals、建立exact sampler replay envelope、量測deduplicated benchmark union，再依D6判讀offline prior能否穿過validity、population去重與有限抽樣。S13不延伸H10，也不加入oracle arm。

## 2. Hypothesis 與 falsification

**S13-H1：**在actual Ductile Gen0中，Formocast residual guidance的top-decile exposure方向性勝existing／proxy與same-entropy shuffled，同時median quality、correctness、validity與sampler realization不失守。

反證或invalidating evidence：

- `P0`、proposal serialization、candidate order、weight order或replay不一致；
- F不勝G或S；
- median-quality noise guardrail失敗；
- 新增correctness／validity failure；
- replay envelope顯示systematic anomaly；
- results按set iteration order而非canonical proposal identity join。

## 3. Dependencies、entry 與 outgoing edge

只有fresh verifier依S12 frozen contract確認、並seal在compact durable record中的
`D5_PASS`可在同一tranche開始S13；S12 internal positive此時尚不等於CU-S1
committed closeout。D5 cutoff、S11 guidance、noise evidence、arms、formal/replay
seeds與sampler revisions都必須由S13 effective lock綁定。

唯一outgoing edge：

```text
D6_MECHANISM_POSITIVE -> S20
```

Negative／inconclusive不追加generations救回，也不解鎖S20。

### 3.1 Gate／tranche／closure governance

- `risk_tier=R1`、`scientific_gate=S13`、
  `execution_tranche=T-S1-MECHANISM`、`closure_unit=CU-S1-MECHANISM`；S13是本
  tranche的final scientific gate。
- Formal proposals前依
  `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`完成entry resource preflight並seal
  durable machine-readable contract／effective lock。Stage-1全部既有wall-time、
  CPU/GPU、storage、throughput、repair與thread consumption跨generation、
  successor與root累計，不得因進S13歸零。
- S13 positive另seal compact record
  `protocol/v1/evidence/gate-records/s13-d6-mechanism-positive.json`；positive、
  negative或inconclusive都由本final report整合S11／S12 compact records與S13
  terminal evidence。
- `live_run_state`可在verified S11／S12 edges後繼續；整個CU-S1的
  `committed_projection_state`只有本report、staged audit、isolated commit與
  post-commit audit完成後才是`COMPLETE`。

## 4. Maximum implementation 與 delivery boundary

允許：

- requested population的actual constructor resolution與`P0` amendment rule；
- exact `SearchSpace.sample(P0)` replay與realization diagnostics；
- U/G/F/S formal proposal generation、canonical serialization與proposal lock；
- cross-arm/seed deduplicated benchmark union與multiplicity-aware result join；
- D6 hit-rate、median guardrail、correctness、validity與diagnostics。

禁止：

- 修改S11 guidance、D5 cutoff、arms或seeds；
- 增加H10、mutation/selection transitions或natural stop；
- 加入oracle arm或用best取代median guardrail；
- 將三paired seeds包裝成significance；
- 實作S20或建立其report；
- 使用M06 results、seed bundle或proposal artifacts。

## 5. Future effective lock、inputs 與 outputs

Future lock：

`protocol/v1/locks/s13-stage1-actual-gen0-lock.json`

Inputs：

- D5 PASS與immutable cutoff；
- S11 weights/shuffle bundle；
- noise/correctness evidence；
- sampler/validity/mapping revisions；
- P0 resolution rule、formal/replay seeds、serialization與join schemas。

Outputs：

- resolved `P0`與constructor decision；
- per-arm replay envelope；
- formal proposals與canonical config-set hashes；
- proposal lock與deduplicated union；
- per-slot results/multiplicity；
- D6 metrics、failure attribution與machine decision。

若`P0`不同於requested value，只能依parent在任何proposal labels前append amendment；不得看到treatment quality後改。

## 6. Controls 與 measurement boundary

- U／G／F／S arms完全依parent；
- same formal seed跨arms，replay seeds與formal seeds分離；
- proposals全部lock後才benchmark；
- canonical config identity不依賴set iteration order；
- deduplicated measurement結果按proposal multiplicity回填；
- D5 cutoff與noise-derived guardrail固定；
- oracle不進formal endpoint。

S13能回答actual Gen0 mechanism，不能回答H10 persistence、evaluation efficiency或held-out replication。

## 7. Acceptance binding 與 stop matrix

唯一positive criterion是parent的`D6_MECHANISM_POSITIVE`。

| 狀況 | outcome／failure | downstream |
| --- | --- | --- |
| 全部D6 criteria通過 | positive；暫記washout尚未測 | S20 |
| Proposal/replay/order mismatch | `FT-PLUMBING`；修復需new lock/fresh proposals | 無 |
| Realization正常但quality無增益 | `FT-GEN0-MECHANISM` | 無 |
| F不勝G | `FT-HEURISTIC-SATURATION`或parent指定分類 | 無 |
| F不勝S | `FT-ENTROPY-ONLY` | 無 |
| Noise/support不足 | `FT-INCONCLUSIVE` | 無 |
| 想用額外generations或seeds救回 | downgrade/plan change，停止review | 無 |

## 8. Formal report 與 closeout

唯一formal report：

`reports/gen0-factorization-mvp-report.md`

這是S13與Stage 1 rollup的正式decision record，必須同時追溯S10–S13 authority而不重複上游report。Positive、negative與inconclusive都需要closeout；只有positive committed closeout可開始S20。

它必須整合
`protocol/v1/evidence/gate-records/s11-s1-guidance-locked.json`、
`protocol/v1/evidence/gate-records/s12-d5-pass.json`與S13 machine decision；前兩份
compact positive records不另建重複formal report。若S11或S12較早terminal，則不會
建立本S13 report。

## 9. Design-consensus record

- Reviewer A objection：把D5 oracle加入formal Gen0 arm會把diagnostic label signal變成outcome-informed treatment。
- Reviewer B objection：若proposal benchmark與proposal generation交錯，cache、failure或set ordering可能改變後續population identity。
- 採納方案：P0先解析、全arm/seed proposals先lock、canonical set identity、deduplicated union後multiplicity-aware join，oracle完全排除。
- 捨棄方案：H10順手延伸、oracle arm、best-only endpoint與set iteration hash；理由是它們越過S13機制邊界或產生不可重現identity。
- Shared resolution：S13只判actual Gen0；只有完整D6 positive可解鎖S20。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`
