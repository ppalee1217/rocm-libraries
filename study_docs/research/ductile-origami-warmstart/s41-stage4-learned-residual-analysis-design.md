---
checkpoint_id: S41
title: Stage 4 cluster-held-out learned residual analysis
stage: 4
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
hypothesis_id: S41-H1
dependencies:
  - checkpoint_id: S40
    required_edge: S4_ACTIVATE
entry_criteria:
  - S4_ACTIVATE
criterion_refs:
  - S4_LEARNED_RESIDUAL_POSITIVE
failure_ids:
  - FT-SURROGATE-NO-GAIN
  - FT-INCONCLUSIVE
allowed_outgoing_edges: []
formal_report_path: reports/learned-residual-surrogate-report.md
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
  - s41-stage4-learned-residual-analysis-design.md
forbidden_downstream_roots:
  - actual GA validation
  - production or deployment artifacts
consensus_status: approved_two_reviewer_agree
---

# S41 — Stage 4 cluster-held-out learned residual analysis

導航：[active checkpoint index](README.md)｜[experiment plan §19](../ductile-origami-warmstart-experiment-plan.md#19-stage-4-modelsplitclaim-contract)

## 1. 白話目標

用唯一預註冊的inclusion-weighted ridge residual correction，檢驗learned predictor能否在完整unseen cluster中，同時改善ranking、factorized prior mass與oracle gap。S41只做offline cluster-held-out analysis，不做model zoo、不用row split、不跑actual GA。

## 2. Hypothesis 與 falsification

**S41-H1：**在每個parent-designated primary held-out unit上，learned residual predictor都strictly優於Formocast ranking，其factorized prior都strictly優於Formocast-factorized與same-entropy shuffled prior，且其oracle gap strictly更小。

反證或inconclusive：

- 任一primary held-out unit任一必要gate未strictly改善；
- tie；
- required support、coverage、mapping或importance evidence不足；
- preprocessing、feature selection或lambda selection讀取outer-test labels；
- 使用forbidden feature或row-random split；
- factorization/hook偏離frozen procedure。

## 3. Dependencies、entry 與 terminal status

只有S40 committed `S4_ACTIVATE`可開始S41。Qualified cluster registry、prospective-test身分、split roles、feature manifest schema與all model/evaluation rules必須在outer labels進入model pipeline前由effective lock綁定。

S41沒有automatic outgoing edge。Positive完成Stage 4 offline predictor-substitution claim；actual GA需要另有第五個prospectively sealed cluster與fresh user/mentor gate，不屬本checkpoint。

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

- 使用parent D5相同的self-normalized real-top-decile prior mass`M_a(T)`；
- learned factorized prior必須strictly同時勝Formocast-factorized prior與same-entropy shuffled。

### Oracle gap

```text
oracle_gap_a = max(0, M_oracle(T) - M_a(T))
```

Learned oracle gap必須strictly小於Formocast oracle gap。

每個primary held-out unit都必須同時通過ranking、prior mass與oracle gap。Tie不算positive；required support或coverage缺失是inconclusive。

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

它綁定S40 closure、qualified registry、primary/secondary units、feature manifest、target、ridge grid、preprocessing、inner objective/tie-break、split manifest、weights、factorization、comparators、primary gates、Plan-B、exact whitelists與formal report。

Outputs：

- feature manifest與mapping completeness audit；
- outer/inner split manifest；
- per-fold preprocessing state與selected lambda；
- predictions、factorized priors與comparator outputs；
- per-primary-unit ranking、prior mass、ESS/support、oracle gap；
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

Report逐primary unit呈現feature/split lineage、lambda selection、all comparators、ranking、prior mass、support與oracle gap；secondary LOCO不得混入primary verdict。Positive、negative、inconclusive都照常closeout。

## 11. Design-consensus record

- Reviewer A objection：原parent只寫「lightweight predictor」與「穩定優於」，model family、feature leakage、lambda selection與strict gate未操作化。
- Reviewer B objection：若prospective fourth cluster與LOCO平均，或允許x-of-y，弱cluster會被平均掩蓋且primary test不再prospective。
- 採納方案：唯一inclusion-weighted ridge、固定residual target/grid、training-only preprocessing、equal-cluster inner loss、strict per-primary-unit三gate。
- 捨棄方案：model zoo、row split、effect margin、CI/significance、oracle-gap ratio、x-of-y relaxation與actual GA；理由是它們未被parent授權或超出data/time/claim boundary。
- Shared resolution：prospective fourth cluster存在時它是唯一primary；否則所有LOCO units皆primary且all-pass。Tie不算positive，missing support為inconclusive。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`
