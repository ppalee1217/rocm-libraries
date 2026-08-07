---
checkpoint_id: S41
title: Stage 4 cluster-held-out learned residual analysis
stage: 4
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R1
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S41
execution_tranche: T-S4-LEARNED-RESIDUAL
closure_unit: CU-S4-LEARNED-RESIDUAL
hypothesis_id: S41-H1
dependencies:
  - checkpoint_id: S40
    required_edge: S4_ACTIVATE
  - authority_id: S11-S12-FIXED-FRAME-20260803
    relation: inherited_directional_index_authority
    required_state: approved
entry_criteria:
  - S4_ACTIVATE
criterion_refs:
  - S4_LEARNED_RESIDUAL_POSITIVE
failure_ids:
  - FT-SURROGATE-NO-GAIN
  - FT-INCONCLUSIVE
allowed_outgoing_edges: []
formal_report_path: reports/learned-residual-surrogate-report.md
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s41-s4-learned-residual-positive.json
tranche_final_report_path: reports/learned-residual-surrogate-report.md
terminal_report_integration: integrates_S40_compact_record_and_S41_terminal_evidence
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s41-stage4-learned-residual-analysis-lock.json
implementation_boundary_max:
  - single ridge residual model, nested cluster split, training-only preprocessing, frozen factorization and held-out evaluation
  - protocol/v1 schemas and lock entries required only by S41
delivery_boundary_max:
  - S41 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/learned-residual-surrogate-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - README.md
  - s41-stage4-learned-residual-analysis-design.md
forbidden_downstream_roots:
  - actual GA validation
  - production or deployment artifacts
consensus_status: approved_two_reviewer_agree
suspension_state: suspended_pending_s14
suspension_authority: RESCOPE-STAGE1-OUTCOME-20260807
---

# S41 — Stage 4 cluster-held-out learned residual analysis

> **2026-08-07 FROZEN pending S14：**本 design 依 user-approved `RESCOPE-STAGE1-OUTCOME-20260807` 保留為 immutable,execution SUSPENDED,pending Stage-1 S14（full-GA baseline-vs-guided real-GPU outcome）結果。本 checkpoint 的 hypothesis、arms、thresholds、edges、failure taxonomy 全部不變、未刪除;恢復僅需 user decision 撤銷本 freeze（移除本 banner 與 frontmatter 的 suspension_state／suspension_authority,並重啟其 DAG edge）。

導航：[active checkpoint index](README.md)｜[experiment plan §19](../ductile-origami-warmstart-experiment-plan.md#19-stage-4-modelsplitclaim-contract)

## 1. 白話目標

用唯一預註冊的inclusion-weighted ridge residual correction，在frozen finite held-out
frame內比較learned與Formocast的ranking、factorized directional `M_HT` index與oracle gap之observed
point direction。S41只做offline cluster-held-out analysis，不做model zoo、不用row split、
不跑actual GA；即使positive，也不把point comparison擴張成stable／practical／general effect。

## 2. Hypothesis 與 falsification

**S41-H1：**在每個parent-designated primary held-out unit的frozen finite frame中，
learned residual predictor的observed ranking point value都strictly高於Formocast，
其factorized `M_HT` point value都strictly高於Formocast-factorized與same-entropy
shuffled，且其observed oracle-gap point value strictly更小。

反證或inconclusive：

- 任一primary held-out unit任一必要gate未strictly改善；
- tie；
- required support、coverage、mapping或importance evidence不足；
- preprocessing、feature selection或lambda selection讀取outer-test labels；
- 使用forbidden feature或row-random split；
- factorization/hook偏離frozen procedure。
- `M_HT`被clip／winsorize／normalize、改denominator，或未繼承S12 exact`T_D5/rho_j`。

## 3. Dependencies、entry 與 terminal status

只有fresh verifier依S40 frozen contract確認、並seal在compact durable record中的
`S4_ACTIVATE`可在同一tranche開始S41；S40 internal positive此時尚不等於CU-S4
committed closeout。Qualified cluster registry、prospective-test身分、split roles、
feature manifest schema與all model/evaluation rules必須在outer labels進入model
pipeline前由effective lock綁定。

S41沒有automatic outgoing edge。Positive只支持frozen finite held-out frame內的observed
point-direction comparison；actual GA需要另有第五個prospectively sealed cluster與fresh
user/mentor gate，不屬本checkpoint。

### 3.1 Gate／tranche／closure governance

- `risk_tier=R1`、`scientific_gate=S41`、
  `execution_tranche=T-S4-LEARNED-RESIDUAL`、
  `closure_unit=CU-S4-LEARNED-RESIDUAL`；S41是本tranche final scientific gate。
- Outer labels進入model pipeline前依
  `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`重做cumulative resource preflight，
  freeze durable machine-readable contract並seal effective lock。S40+S41既有
  wall-time、CPU/GPU、storage、throughput、repair與thread consumption跨fold、
  generation、successor與new root累計。
- 五工作日只作Layer-C planning telemetry；不能以較弱split、較少cluster、reduced grid
  或x-of-y替代，也不能把time variance當scientific result。
- Positive另seal compact record
  `protocol/v1/evidence/gate-records/s41-s4-learned-residual-positive.json`；positive、
  negative與inconclusive都由S41 final report整合S40 record與每個primary unit
  terminal evidence。
- `live_run_state`可在verified S40 edge後繼續；CU-S4的
  `committed_projection_state`只在terminal commit與post-audit後更新。

## 4. Deterministic model contract

唯一model：

- inclusion-weighted ridge residual correction；
- target：`log(real latency) - log(Formocast latency)`；
- `ridge_lambda` grid：`{1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100}`；
- intercept不penalize。

Feature manifest只能包含：

- label-blind problem/config/gene fields；
- Formocast inputs；
- model-only outputs；
- 在全部qualified clusters都有完整deterministic mapping的欄位。

Feature manifest禁止：

- real scores或由real score衍生的欄位；
- oracle outputs；
- cluster ID、result ID或任何hash；
- outcome-derived selection、coverage、rank或failure features。

Preprocessing：

- continuous transform／imputation／scaling只fit當前outer-training data；
- categorical one-hot只使用training categories，另有explicit unknown bucket；
- outer-test不參與feature selection、preprocessing或calibration。

Inner selection：

- 只在outer-training clusters做cluster-grouped validation；
- 每個validation cluster計算inclusion-weighted residual MSE；
- selection objective是各validation cluster MSE的equal-cluster mean；
- loss相同時選較大的`ridge_lambda`。

## 5. Split contract

- Outer split是leave-one-entire-cluster-out；
- 同cluster的sizes、repeats、duplicates與derived rows永遠留在同fold；
- inner selection只使用outer-training clusters；
- D5 inclusion/design weights用於training與evaluation；
- 禁止random row split。

若有三個既有clusters加一個prospective sealed fourth cluster：

- 前三clusters完成全部model/lambda selection；
- prospective fourth cluster是唯一primary gate unit；
- LOCO只作secondary sensitivity。

否則所有LOCO outer clusters都是primary units，而且每一個都必須通過全部primary gates；不得跨units平均救回。

## 6. Frozen primary gates

### Ranking

- 使用frozen inclusion/design weights計算aggregate weighted Spearman；
- predicted orientation：`-log(predicted latency)`；
- real orientation：`log(aggregate quality)`；
- learned必須strictly勝Formocast。

### Prior mass

- 機械繼承stable estimator identity
  `S12-DIRECTIONAL-FINITE-FRAME-HT-EXACT-DENOMINATOR-v1`、S12 exact fixed-sample
  identities、global raw aliases、inclusion probabilities、
  all-size aggregate quality、cutoff ties、stratum／identity bootstrap與no-clipping semantics：

  ```text
  r_a(o)   = pi_nominal,a(o) / pi_nominal,0(o)
  A_aj     = sum_{o aliases j} r_a(o)
  N_HT,a   = sum_{j in D5} [A_aj / rho_j] * I[j in T_D5]
  D_exact,a = sum_{o in Fraw_global} r_a(o)
  M_HT,a   = N_HT,a / D_exact,a
  ESS_a    = [sum_{j in D5} A_aj/rho_j]^2 / sum_{j in D5}[A_aj/rho_j]^2

  w_0j = A_0j / rho_j
  Q_D5(t) = [sum_{j in D5} w_0j * I[quality_j <= t]] / sum_{j in D5} w_0j
  t_D5 = min{quality_j : Q_D5(quality_j) >= 0.90}
  T_D5 = {j in D5 : quality_j >= t_D5}
  ```

- `quality_j`是sealed all-size real quality、越大越好，所有cutoff ties都進`T_D5`。
  `M_HT`是可大於1的design-based directional index，不是bounded probability；禁止clip、
  winsorize、post-hoc normalize或sampled denominator。
- learned factorized `M_HT`必須strictly同時高於Formocast-factorized與same-entropy shuffled。

### Oracle gap

```text
oracle_gap_a = max(0, M_HT,oracle - M_HT,a)
```

Learned directional-index oracle gap必須strictly小於Formocast gap；它不是probability gap。
每個stratum／identity bootstrap replicate都重建`t_D5`、`T_D5`、estimators、contrasts、
ESS與oracle gap。

每個primary held-out unit都必須同時通過ranking、prior mass與oracle gap。Tie不算positive；required support或coverage缺失是inconclusive。

這裡的 `strictly` 只比較預註冊 point values 的方向；沒有effect margin、uncertainty或
prospective replication時，positive**不支持**practical effect、stability、statistical
significance、population generalization、prospective replication、production readiness
或actual-GA benefit。任何較強claim都需要future prospectively locked design，事前指定
effect margins與uncertainty rules。

不得自行加入effect margin、CI/significance requirement、x-of-y relaxation、oracle-gap ratio，或修改parent data floor、split、time cap與claim。

## 7. Maximum implementation 與 delivery boundary

允許：

- frozen feature-manifest validator；
- nested cluster split materialization；
- training-only preprocessing與unknown-category handling；
- single ridge grid selection/fitting/prediction；
- frozen factorization、Formocast/shuffle/oracle comparator與primary metrics；
- leakage audit與formal report。

禁止：

- model zoo、non-ridge model、row split或test-informed features；
- outer-label preprocessing、gene selection或threshold tuning；
- actual GA、fifth-cluster collection、production integration；
- x-of-y或cross-unit averaging救回；
- 加入未經user review的新gate／margin。

## 8. Future effective lock、inputs 與 outputs

Future lock：

`protocol/v1/locks/s41-stage4-learned-residual-analysis-lock.json`

它綁定`S11-S12-FIXED-FRAME-20260803`、S40 closure、qualified registry、primary/secondary
units、feature manifest、target、ridge grid、preprocessing、inner objective/tie-break、split
manifest、weights、exact inherited`rho_j/T_D5/M_HT` identities、bootstrap、comparators、
primary gates、Plan-B、exact whitelists與formal report。

Outputs：

- feature manifest與mapping completeness audit；
- outer/inner split manifest；
- per-fold preprocessing state與selected lambda；
- predictions、factorized priors與comparator outputs；
- per-primary-unit ranking、unclipped`M_HT`、`T_D5`／ties、ESS/support、directional-index
  oracle gap與bootstrap；
- leakage audit與machine decision。

## 9. Acceptance binding 與 stop matrix

| 狀況 | outcome | treatment |
| --- | --- | --- |
| 每個primary unit三gate都strictly通過 | `S4_LEARNED_RESIDUAL_POSITIVE` | positive closeout |
| 任一primary unit有valid negative | `FT-SURROGATE-NO-GAIN` | negative closeout |
| 任一required comparison tie | negative／not positive | 不得x-of-y救回 |
| Support／coverage／ESS不足 | `FT-INCONCLUSIVE` | inconclusive closeout |
| Leakage／split violation | evidence invalid | new lock/fresh evaluation |
| 想改model、features、gates或data floor | `blocked-awaiting-user-decision` | 停止 |

## 10. Formal report 與 closeout

唯一formal report：

`reports/learned-residual-surrogate-report.md`

Report逐primary unit呈現feature/split lineage、lambda selection、all comparators、ranking、
exact inherited`rho_j/T_D5/A_aj/N_HT/D_exact`、unclipped`M_HT`、support／ESS、bootstrap與
directional-index oracle gap；secondary LOCO不得混入primary verdict。`M_HT>1`不是error或
clipping trigger。Positive、negative、inconclusive都照常closeout。

Report的positive wording只能是「在frozen finite held-out frame中，observed point value
方向符合strict comparison」；不得使用「general improvement」、「stable improvement」、
「significant」、「practically better」、「production ready」或「改善actual GA」。

它也必須整合
`protocol/v1/evidence/gate-records/s40-s4-activate.json`與S41 machine decision；
S40 positive不另建重複formal report。S41 positive另seal
`protocol/v1/evidence/gate-records/s41-s4-learned-residual-positive.json`。

## 11. Design-consensus record

- Reviewer A objection：原parent只寫「lightweight predictor」與「穩定優於」，model family、feature leakage、lambda selection與strict gate未操作化。
- Reviewer B objection：若prospective fourth cluster與LOCO平均，或允許x-of-y，弱cluster會被平均掩蓋且primary test不再prospective。
- 採納方案：唯一inclusion-weighted ridge、固定residual target/grid、training-only preprocessing、equal-cluster inner loss、strict per-primary-unit三gate。
- 捨棄方案：model zoo、row split、effect margin、CI/significance、oracle-gap ratio、x-of-y relaxation與actual GA；理由是它們未被parent授權或超出data/time/claim boundary。
- Shared resolution：prospective fourth cluster存在時它是唯一primary；否則所有LOCO units皆primary且all-pass。Tie不算positive，missing support為inconclusive。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`

### 2026-08-03 finite-frame claim amendment

- Exact model、residual target、ridge grid、unpenalized intercept、training-only preprocessing、
  unknown bucket、cluster-held-out outer split、cluster-grouped inner selection、equal-cluster
  MSE、larger-lambda tie-break、weights、strict per-primary-unit comparisons、tie handling與
  no-GA boundary全部不變。
- Positive claim縮為frozen finite held-out frame的observed point-direction comparison。
  它不證明practical effect、stability、significance、population generalization、prospective
  replication、production readiness或actual-GA benefit。

### 2026-08-03 approved `S11-S12-FIXED-FRAME-20260803` amendment

- S41機械繼承stable estimator identity
  `S12-DIRECTIONAL-FINITE-FRAME-HT-EXACT-DENOMINATOR-v1`、S12 exact fixed sample、
  `rho_j`、global aliases、all-size `T_D5` cutoff／ties、
  `A_aj/N_HT/D_exact/M_HT`、stratum／identity bootstrap與no-clipping semantics。
- Learned `M_HT`必須strictly高於Formocast-factorized與same-entropy shuffled；
  `oracle_gap_a=max(0,M_HT,oracle-M_HT,a)`是directional-index gap，不是probability gap。
- Exact ridge model、feature boundary、cluster-held-out splits、per-primary-unit all-pass與
  finite-frame point-direction claim都不變。本amendment沒有啟動S40/S41，也沒有result、
  report、effective checkpoint lock或edge。
