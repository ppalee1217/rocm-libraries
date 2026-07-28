---
checkpoint_id: S31
title: Stage 3 two-cluster bounded replication
stage: 3
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R1
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S31
execution_tranche: T-S3-REPLICATION
closure_unit: CU-S3-REPLICATION
hypothesis_id: S31-H1
dependencies:
  - checkpoint_id: S30
    required_edge: S3_REGISTRY_PROCEDURE_LOCKED
entry_criteria:
  - S3_REGISTRY_PROCEDURE_LOCKED
criterion_refs:
  - S3_BOUNDED_REPLICATION_POSITIVE
  - S4_TRIGGER_ELIGIBLE
failure_ids:
  - FT-REGIME-HETEROGENEITY
  - FT-BOUNDED-REPLICATION
  - FT-MODEL-RANK
  - FT-MODEL-MARGINAL
  - FT-HOOK-EXPRESSIVENESS
  - FT-PERSISTENCE-WASHOUT
  - FT-SHORT-HORIZON-REGRESSION
  - FT-EVALUATION-SUPPORT
  - FT-PLUMBING
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S3_BOUNDED_REPLICATION_POSITIVE
    target_checkpoint: null
  - criterion_id: predictor_heterogeneity_and_oracle_positive
    target_checkpoint: S40
formal_report_path: reports/bounded-regime-replication-report.md
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s31-s3-bounded-replication-positive.json
tranche_final_report_path: reports/bounded-regime-replication-report.md
terminal_report_integration: integrates_S30_compact_record_and_S31_terminal_evidence
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s31-stage3-bounded-replication-lock.json
implementation_boundary_max:
  - frozen two-cluster mapping, model-only, D5 and conditional H10 replication execution
  - protocol/v1 schemas and lock entries required only by S31
delivery_boundary_max:
  - S31 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/bounded-regime-replication-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - README.md
  - s31-stage3-bounded-replication-design.md
forbidden_downstream_roots:
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
---

# S31 — Stage 3 two-cluster bounded replication

導航：[active checkpoint index](README.md)｜[experiment plan §17](../ductile-origami-warmstart-experiment-plan.md#17-stage-3-per-cluster-protocol-與-gate)

## 1. 白話目標

依S30 registry對兩個primary slots完整執行相同frozen procedure：mapping/access/noise、label-blind model-only factorization、D5 audit，以及只有D5 PASS才啟動的H10 G/F/S。兩個slots都留在denominator，不能用outcome-driven replacement或只報成功者。

## 2. Hypothesis 與 falsification

**S31-H1：**凍結的guidance procedure在兩個預註冊new clusters都通過D5，並在各cluster的fresh H10 paired seeds中重現F相對G/S的AUC、late retention與final non-inferiority。

反證或inconclusive：

- 任一cluster D5 fail／inconclusive；
- 任一cluster H10 AUC、late retention或final guardrail失敗；
- 兩cluster方向不一致；
- mapping、correctness、support、plumbing或held-out seal失效；
- score/label後更換cluster、改procedure或只保留成功slot。

## 3. Dependencies、entry 與 outgoing edges

只有fresh verifier依S30 frozen contract確認、並seal在compact durable record中的
`S3_REGISTRY_PROCEDURE_LOCKED`可在同一tranche開始S31；S30 internal positive此時
尚不等於CU-S3 committed closeout。

- `S3_BOUNDED_REPLICATION_POSITIVE`完成bounded replication主線，沒有自動下游checkpoint。
- 合法predictor heterogeneity + oracle-positive evidence可形成S40 conditional edge。
- 其他negative／inconclusive停止主線，不會以S40替代。

Single-cluster evidence只能在user批准的downgraded pilot中描述，不能完成S31或產生原edge。

### 3.1 Gate／tranche／closure governance

- `risk_tier=R1`、`scientific_gate=S31`、
  `execution_tranche=T-S3-REPLICATION`、`closure_unit=CU-S3-REPLICATION`；S31是
  本tranche final scientific gate。
- 第一筆S31 score／label前依
  `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`重做entry preflight並seal durable
  machine-readable contract／effective lock。S30+S31累積wall-time、CPU/GPU、
  storage、throughput、repair與thread budget不因cluster、generation、reserve
  cutover、successor或new root重置。
- Stage 3 hard cap保持7工作日且不是完成承諾；不能用cache/dedup樂觀估算或縮成
  single-cluster救回。
- Positive另seal compact record
  `protocol/v1/evidence/gate-records/s31-s3-bounded-replication-positive.json`；
  positive、negative或inconclusive都由S31 final report整合S30 compact record與
  兩slot terminal evidence。
- `live_run_state`可在verified S30 edge後繼續；CU-S3的
  `committed_projection_state`只在terminal commit與post-audit後更新。

## 4. Maximum implementation 與 delivery boundary

允許：

- S30每個primary slot的mapping/access/noise gate；
- frozen label-blind model-only algorithm與cluster-specific deterministic outputs；
- parent D5-equivalent pool、measurement、weighted/oracle analysis；
- D5 PASS cluster的G/F/S fixed H10與fresh paired seeds；
- fixed denominator rollup、heterogeneity與failure localization。

禁止：

- outcome-drivencluster replacement、denominator change或manual exception；
- cluster-specific retuning eligibility、threshold、factorization、shuffle或gate；
- D5 fail/inconclusive cluster繼續GA來「救回」；
- 合併clusters平均後掩蓋某slot失敗；
- 直接train Stage4 model或建立S40/S41 results。

## 5. Future effective lock、inputs 與 outputs

Future lock：

`protocol/v1/locks/s31-stage3-bounded-replication-lock.json`

它綁定S30 registry/denominator/cutover、frozen procedure、per-slot sizes、mapping and model revisions、D5/H10 seeds、support rules、caps、Plan-B、exact whitelists與formal report。

Outputs per slot：

- mapping/access/noise evidence；
- model-only occurrence/catalog/guidance artifacts；
- D5 pool、measurements、weighted metrics與oracle；
- data-qualified status；
- conditional H10 trajectories、support、AUC、late retention與remeasurements；
- per-slot decision。

Rollup outputs：

- fixed denominator audit；
- bounded replication／heterogeneity decision；
- optional predictor-specific S40 trigger evidence。

## 6. Controls 與 measurement boundary

- 同一frozen algorithm可因cluster input不同產生不同label-blind genes/weights，但不得manual retune；
- 每slot D5 fail仍保留denominator且停止該slot GA；
- H10使用fresh per-cluster paired seeds與parent common-support rules；
- 两cluster是independent generalization units，sizes不是額外clusters；
- metrics逐cluster判讀，不用跨cluster平均救回；
- reserve replacement只能引用S30 prelabel technical cutover record。

S31只支持two-regime bounded replication，不支持MI300X workload generalization。

## 7. Acceptance binding 與 stop matrix

`S3_BOUNDED_REPLICATION_POSITIVE`的D5、seed、AUC、retention、non-inferiority與correctness要求全部引用parent。

| 狀況 | outcome／failure | downstream |
| --- | --- | --- |
| 2/2 clusters全部criteria通過 | positive bounded replication | 主線完成 |
| 一正一負 | `FT-REGIME-HETEROGENEITY` | 只有oracle-positive predictor case可送S40 |
| 兩者皆負 | bounded replication否證 | 無 |
| 任一access/mapping blocked | inconclusive／blocked | 無 |
| 只完成一cluster | downgrade pilot，不完成S31 | 無 |
| Predictor-specific heterogeneity + oracle positive | negative/heterogeneous closeout | conditional S40 |
| Outcome-driven replacement/amendment | held-out invalid | 無 |

## 8. Formal report 與 closeout

唯一formal report：

`reports/bounded-regime-replication-report.md`

Report必須逐slot呈現所有D5/H10 gates、未跑GA的原因、fixed denominator、reserve history、negative cases與claim boundary。Conditional S40 edge只有在S31 closeout commit明確記錄後存在。

它也必須整合
`protocol/v1/evidence/gate-records/s30-s3-registry-locked.json`與S31 machine
decision；S30 positive不另建重複formal report。S31 positive另seal
`protocol/v1/evidence/gate-records/s31-s3-bounded-replication-positive.json`。

## 9. Design-consensus record

- Reviewer A objection：如果D5 fail cluster被排除H10後又從總denominator移除，replication會selection on success。
- Reviewer B objection：cluster-specific label-blind outputs與outcome-driven retuning界線需要明確，否則任何改genes都可被稱為deterministic。
- 採納方案：固定two-slot denominator、D5 fail保留且停止GA、只有frozen algorithm的label-blind deterministic outputs可變、逐clusterall-gates判讀。
- 捨棄方案：winner-only rollup、跨clusters平均救回、D5 fail後補跑或換cluster；理由是它們破壞held-out replication。
- Shared resolution：2/2 positive才是bounded replication；異質性只有在predictor-specific且oracle-positive時才能形成S40 edge。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`
