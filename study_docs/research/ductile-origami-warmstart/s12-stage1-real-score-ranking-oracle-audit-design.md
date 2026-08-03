---
checkpoint_id: S12
title: Stage 1 real-score ranking、prior-mass 與 oracle audit
stage: 1
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R2
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S12
execution_tranche: T-S1-MECHANISM
closure_unit: CU-S1-MECHANISM
hypothesis_id: S12-H1
dependencies:
  - checkpoint_id: S11
    required_edge: S1_GUIDANCE_LOCKED
entry_criteria:
  - S1_GUIDANCE_LOCKED
criterion_refs:
  - D5_PASS
  - D5_BORDERLINE_INCONCLUSIVE
  - D5_FAIL
  - S4_TRIGGER_ELIGIBLE
failure_ids:
  - FT-MODEL-RANK
  - FT-MODEL-MARGINAL
  - FT-HOOK-EXPRESSIVENESS
  - FT-HEURISTIC-SATURATION
  - FT-ENTROPY-ONLY
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: D5_PASS
    target_checkpoint: S13
  - criterion_id: predictor_specific_failure_and_oracle_positive
    target_checkpoint: S40
formal_report_path: reports/staged/s12-stage1-real-score-audit-report.md
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s12-d5-pass.json
tranche_final_report_path: reports/gen0-factorization-mvp-report.md
terminal_report_integration: terminal_here_on_nonpass_else_integrated_by_S13
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s12-stage1-real-score-audit-lock.json
implementation_boundary_max:
  - frozen D5 pool materialization, measurement, weighted analysis and cross-fitted oracle
  - protocol/v1 schemas and lock entries required only by S12
delivery_boundary_max:
  - S12 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/staged/s12-stage1-real-score-audit-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - README.md
  - s12-stage1-real-score-ranking-oracle-audit-design.md
forbidden_downstream_roots:
  - reports/gen0-factorization-mvp-report.md
  - reports/short-horizon-persistence-report.md
  - reports/staged/s30-heldout-registry-freeze-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
---

# S12 — Stage 1 real-score ranking／prior-mass／oracle audit

導航：[active checkpoint index](README.md)｜[experiment plan §6](../ductile-origami-warmstart-experiment-plan.md#6-d3d5-real-score-finite-frame-audit)

## 1. 白話目標

在 S11 guidance 完全凍結後，才從 `Uexec` 無 replacement 抽 exactly 256 個 unique
executable identities，建立 frozen D5 judgment pool並取得 real scores。S12回答 whole-
config ranking是否有訊號、factorized prior是否把完整 `Fraw` mass放到真實高品質區，
以及失敗究竟在 predictor、marginalization 還是 hook 表達力。

本 design 已由
[S1 rebaseline authority](s10r4-retirement-s11-rebaseline-authority.md) prospectively amended；
本 closure 沒有實作或產生 S12 evidence。

## 2. Hypothesis 與 falsification

**S12-H1：**在parent預註冊的finite-frame sampling與weighted analysis下，Formocast whole ranking及factorized prior通過D5，且prior mass同時勝existing／proxy與same-entropy shuffled。

反證或inconclusive：

- ranking／lift低於parent gate；
- factorized prior不勝baseline或shuffle；
- coverage、correctness、importance ESS或support不足；
- cross-fitted oracle也不支持factorized main effects；
- inclusion／multiplicity／fold／measurement lineage不完整；
- D5 labels回寫S11 genes、weights、shuffle或hyperparameters。

## 3. Dependencies、entry 與 outgoing edges

只有`S1_GUIDANCE_LOCKED`可開始S12。S11 guidance hash、D5 sample IDs、strata、folds、measurement schedule與analysis revision必須在第一筆real label前進入effective lock。

- `D5_PASS -> S13`
- 合法的predictor-specific failure + oracle-positive evidence可形成`S40` conditional edge。
- Borderline、ordinary fail、hook failure、coverage/noise failure都不解鎖S13或S40。

兩條edge各自綁定其criteria；oracle-positive edge不能被當成D5 PASS。

### 3.1 Gate／tranche／closure governance

- `risk_tier=R2`、`scientific_gate=S12`、
  `execution_tranche=T-S1-MECHANISM`、`closure_unit=CU-S1-MECHANISM`。
- 第一筆real label前，依governance baseline
  `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`完成cumulative resource preflight，
  seal durable machine-readable contract與effective lock。S10R2、S11與S12已消耗的
  wall-time、CPU/GPU、storage、throughput、repair與thread budget跨generation、
  successor與new root累計。
- `D5_PASS`只seal compact durable record
  `protocol/v1/evidence/gate-records/s12-d5-pass.json`，在verified frozen edge後留在
  同一tranche進S13；closure unit尚未完成。
- Borderline、negative、inconclusive或合法predictor-specific negative是terminal
  internal outcome，產生S12 planned report並停止S1主路徑；只有明列的oracle-positive
  conditional edge可另送S40。
- S13 final report整合S11／S12 gate records。`live_run_state`不得被投影成committed
  fact；`committed_projection_state`只在CU-S1 terminal commit與post-audit後更新。

## 4. Maximum implementation 與 delivery boundary

允許：

- parent D5 finite pool、strata與inclusion manifest materialization；
- generate／compile／benchmark／correctness與failure ledger；
- design-weighted ranking、top-decile、density-ratio prior mass與ESS；
- parent-specifiedbootstrap／permutation；
- config-level cross-fitted oracle；
- Stage4 data qualification與predictor-trigger evidence rendering。

禁止：

- 看到labels後修改S11 guidance、genes、lambda、weights或shuffle；
- replacement失敗rows、刪除rejections或只報通過sizes；
- 把oracle回寫成S13 treatment；
- 建立S13 proposals、S40 activation report或S41 model；
- 以M05 data／fold／oracle artifacts填補本checkpoint。

## 5. Future effective lock、inputs 與 outputs

Future lock：

`protocol/v1/locks/s12-stage1-real-score-audit-lock.json`

Inputs：

- immutable S11 guidance lock與label-seal transition；
- catalog/multiplicity、sizes、mapping與noise protocol；
- presealed D5 strata/sample/fold manifests；
- measurement/correctness runner與analysis revision。

Outputs：

- real-score pool manifest與per-config/per-size observations；
- correctness/failure ledger；
- weighted metrics、density-ratio prior mass與ESS；
- oracle fold manifest與cross-fitted results；
- D5 gate summary；
- `qualified_for_stage4_data`與conditional trigger evidence；
- S12 machine decision。

## 6. Controls 與 measurement boundary

- D5 frame exactly 是從 `Uexec` sampled without replacement的256個 unique executable
  identities；`|Uexec|<256` 時 upstream S11為 `inconclusive / FT-INCONCLUSIVE / edge=null`，
  不得降門檻、以alias／size／repeat補數，也不得建立S12 evidence。
- `Uscore` 依 `Fscore` occurrence mass形成10個 weighted deciles；`Uexec\Uscore` 是第11個
  executable-unscored stratum。Existing largest-remainder rule保留，每個非空stratum至少1
  identity，無replacement或label-driven expansion。
- Unique executable identity是analysis unit；同identity的sizes、occurrences與raw aliases
  留在同一block/fold。3 sizes形成同identity的repeated observations，不是3個independent
  configs。
- `Fraw`、`Fexec`、`Fscore` occurrence multiplicity、stratified inclusion probability與
  design weight完整保留。Nonexecutable raw mass位於D5 measurement frame之外，但留在
  primary raw denominator並取得零 top-decile numerator credit。
- Executable-unscored selected identities接受真實measurement；若其real result落在`T`，
  可以取得 numerator credit。Unscored／failed rows不刪除或replacement。
- 在任何 GFLOPS label 前，每個 selected identity 必須通過 pinned native/runtime
  conformance、normal generate/compile、correctness與noise readiness；failure依frozen
  no-replacement outcome matrix處理。
- metric ties使用真實midranks，sampling-only tie-break不進metric；
- oracle只診斷main-effect ceiling，不參與S13 arm；
- D5 measurements不得因outcome被replacement或擴充。

Primary raw-denominator prior mass精確為：

```text
r_a(o) = pi_nominal,a(o) / pi_nominal,0(o)
M_a(T) = [sum_{j in D5} ((sum_{o aliases j} r_a(o)) / rho_j)
          * I[j in real_top_decile_T]]
         / [sum_{o in Fraw} r_a(o)]
```

`o`是raw occurrence，`j`是selected `Uexec` identity，`rho_j`是其sampling inclusion
probability，`T`是real top-decile set；`M_a(T)`越大表示arm把更多完整raw prior mass放入
real top decile。不得用selected-only denominator或representative raw alias取代此公式。

Preserved criteria不變：aggregate Spearman pass `>=0.25`、borderline `[0.20,0.25)`；
top-decile lift pass `>=2.0`、borderline `[1.5,2.0)`；direction至少2/3 sizes；prior mass
strictly勝 baseline與same-entropy shuffle；ESS `>=25`；planned real-measurement coverage
`>=0.95`；correctness required；five-fold config-level oracle；existing bootstrap、
permutation、tie與label-firewall rules。

S12不能說明actual Gen0、H10 persistence或held-out replication。

## 7. Acceptance binding 與 stop matrix

所有formula、pool size、threshold、coverage、ESS與oracle rules只引用parent`D5_PASS`、`D5_BORDERLINE_INCONCLUSIVE`與`D5_FAIL`。

| 狀況 | checkpoint處理 | outgoing edge |
| --- | --- | --- |
| D5全部criterion通過 | positive formal closeout | S13 |
| Predictor-specific failure且oracle positive | negative formal closeout | 可送S40 trigger |
| Borderline／support／coverage／ESS不足 | inconclusive formal closeout | 無 |
| Hook expressiveness failure | negative formal closeout | 無 |
| Labels產生後pipeline中止 | negative／inconclusive formal closeout | 不得退回blocker |
| Guidance需要修改 | 新authority/new lock/fresh judgment pool | 原pool不重用 |

## 8. Formal report 與 closeout

S12 positive使用compact gate record
`protocol/v1/evidence/gate-records/s12-d5-pass.json`並繼續同tranche。S12若
borderline／negative／inconclusive而成為terminal，唯一formal report是
`reports/staged/s12-stage1-real-score-audit-report.md`，必須包含raw overlap counts、
ties、coverage、weighted/unweighted metrics、ESS、oracle diagnosis、all failure
rows、先前gate records、outcome與可以／不能支持的claim。若S13成為tranche final，
S13 report整合S12 positive record，不另建重複positive report。Conditional S40 edge
只在S12 terminal record明列trigger並完成對應closure audit後存在。

## 9. Design-consensus record

- Reviewer A objection：若D5 labels出現後仍允許改factorization，whole-ranking與prior-mass結果會被同一pool過度擬合。
- Reviewer B objection：cross-fitted oracle容易被誤當treatment，或把`qualified_for_stage4_data`錯等同`D5_PASS`。
- 採納方案：sample/fold/analysis prelock、immutable S11 guidance、oracle diagnostic-only、Stage4 qualification獨立欄位與conditional edge。
- 捨棄方案：full-pool oracle回灌、failed-row replacement、只報pass sizes、以oracle-positive救回D5；理由是它們改變estimand與acceptance。
- Shared resolution：S12只有D5 PASS可進S13；S40只接收明確predictor-specific、oracle-positive failure。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`

### 2026-08-03 approved `S1-REBASELINE-20260803` amendment

- S12 sole dependency仍是 `S11:S1_GUIDANCE_LOCKED`；administrative rebaseline不能替代它。
- D5 frame改明確綁定 exactly 256 `Uexec` identities、10個 `Uscore` deciles與1個
  `Uexec\Uscore` stratum；no replacement、folds、thresholds與label firewall不變。
- Primary prior mass denominator綁定 complete `Fraw` aliases。Nonexecutable raw mass零
  numerator；executable-unscored selected identities經real measurement仍可取得credit。
- 每個selected identity在GFLOPS前先通過native/runtime、normal generate/compile、
  correctness與noise readiness。本 authority closure沒有執行或報告任何S12 evidence。
