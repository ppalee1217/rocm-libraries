---
checkpoint_id: S11
title: Stage 1 model-only factorization 與 guidance lock
stage: 1
design_status: approved
execution_status: not_started
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R2
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S11
execution_tranche: T-S1-MECHANISM
closure_unit: CU-S1-MECHANISM
hypothesis_id: S11-H1
dependencies:
  - authority_id: S1-REBASELINE-20260803
    relation: administrative_prerequisite
    required_state: approved
  - authority_id: S11-S12-FIXED-FRAME-20260803
    relation: prospective_measurement_amendment
    required_state: approved
incoming_scientific_edge: null
entry_criteria:
  - approved_S1_REBASELINE_20260803_administrative_prerequisite
criterion_refs:
  - S1_GUIDANCE_LOCKED
failure_ids:
  - FT-BLOCKED-MAPPING
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S1_GUIDANCE_LOCKED
    target_checkpoint: S12
formal_report_path: reports/staged/s11-stage1-model-only-factorization-report.md
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s11-s1-guidance-locked.json
tranche_final_report_path: reports/gen0-factorization-mvp-report.md
terminal_report_integration: terminal_here_on_negative_or_inconclusive_else_integrated_by_S13
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s11-stage1-model-only-factorization-lock.json
implementation_boundary_max:
  - model-only occurrence, catalog, scoring, factorization, weight, shuffle and guidance-lock pipeline
  - protocol/v1 schemas and lock entries required only by S11
delivery_boundary_max:
  - S11 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/staged/s11-stage1-model-only-factorization-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - README.md
  - s11-stage1-model-only-factorization-design.md
forbidden_downstream_roots:
  - reports/staged/s12-stage1-real-score-audit-report.md
  - reports/gen0-factorization-mvp-report.md
  - reports/short-horizon-persistence-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
---

# S11 — Stage 1 model-only factorization／guidance lock

導航：[active checkpoint index](README.md)｜[experiment plan §§3–5](../ductile-origami-warmstart-experiment-plan.md#3-三種分布與分析單位)

## 1. 白話目標

S11 要在完全 label-blind 的條件下，以固定global／conditional schedules fresh建立三層
population：validator accepted 的
raw occurrences `Fraw`、完成 resolver／normal KernelWriter generation／pinned compile 的
executable occurrences `Fexec`，以及全部 locked sizes 都有 finite native Formocast
output 的 `Fscore`。Global inferential frame固定為canonical first8,192 accepts；每個
activated conditional value固定512 chunks／262,144 nominal draws並target first256 accepts。
它再用trusted survivor cells、own-null與familywise model tests建立residual-gene guidance、
weights與same-entropy shuffle，通過candidate-order／probability round-trip後鎖定。

這一步只建立 guidance，不能偷看 real GFLOPS，也不能把 normalized-away、collision-
confounded、context-dependent、execution-attrited 或 score-attrited raw value 當成 trusted
guidance witness。本 design 已由
[S1 rebaseline authority](s10r4-retirement-s11-rebaseline-authority.md) prospectively amended；
fixed schedule與measurement則由
[S11／S12 fixed-frame authority](s11-s12-fixed-frame-measurement-amendment.md)
prospectively amended。下方2026-07/08舊dependency records只是historical provenance。

## 2. Hypothesis 與 falsification

**S11-H1：**依 `S1-REBASELINE-20260803` 與
`S11-S12-FIXED-FRAME-20260803` 的fresh fixed frames、trusted survivor estimand及
familywise model-only criteria，Formocast能對至少一個`|T_g|>=2`的residual gene產生穩定
prior，並可無損轉成與`SearchSpace.map`完全對齊的weights與shuffled control。這是future
hypothesis，不是authority closure的結果。

反證或inconclusive：

- 無 eligible／guidable residual gene、`|T_g|<2`，或 global lambda 退化；
- mapping、coverage、support、sensitivity或stability未過；
- own-null或familywise max-null P95未strictly超過；
- global cap時未取得8,192 accepts，或material conditional shortage仍可能改變no-guidance；
- occurrence multiplicity在dedup後遺失；
- probability／cost round-trip、candidate order或weight sign錯誤；
- existing group／weight被修改；
- behavior-changing resolver overwrite、context dependence、collision-confounding、
  execution attrition 或 score attrition 仍被當成 trusted raw-value guidance evidence；
- 任何real score、oracle output或outcome-derived feature參與gene／weight選擇。

## 3. Dependencies、entry 與 outgoing edge

S11 的 `incoming_scientific_edge=null`。Entry authority包括user-approved administrative
prerequisite `S1-REBASELINE-20260803`與prospective measurement amendment
`S11-S12-FIXED-FRAME-20260803`；兩者都不是empirical S10R3/S10R4 success edge。
S00–S10R3 completed history保持 immutable；S10R4/B01–B07
已依 amendment 退役且沒有 outcome/report/edge。S10R3/S10R4 rows、support states、
seeds、mapping、GPU、noise、decisions、diagnostics 與 dirty B07 bytes 對 S11 trust、
support、score、guidance 或 gate credit 全為零。

S11現在只取得future planning authority：既有draft runner／package／contract／schema不得
直接沿用；仍需依new authority重新對齊machine-readable contract與implementation、完成
Plan-B、Plan-A、fresh verification、effective lock與prelabel audit。本次amendment沒有建立
S11 evidence、effective checkpoint lock、result或report，也沒有proxy／reduced-mode edge。

唯一**未來** outgoing scientific edge：

```text
S11:S1_GUIDANCE_LOCKED -> S12
```

它只有在 S11 自己的 contract、lock、完整 evidence、fresh verification、terminal commit
與 post-audit 都成立後才存在。無 guidable gene、mapping failure、label leakage、
model-only stability不足或 `|Uexec|<256` 都不會解鎖 S12。

### 3.1 Gate／tranche／closure governance

- `risk_tier=R2`、`scientific_gate=S11`、
  `execution_tranche=T-S1-MECHANISM`、`closure_unit=CU-S1-MECHANISM`。
- 執行前依A37與current governance重做resource planning，先seal durable
  machine-readable contract與effective lock。Historical known usage與
  `UNKNOWN` measurement boundary保留作provenance，但不單獨debit S11 entry；
  missing telemetry或internal planning target crossing只record＋notify。只有A37
  material safety／availability／full-workload／optional-stopping／evidence condition
  才pause。Scientific sample／seed／repair／thread與downgrade gates仍是hard。
- Positive只seal compact durable gate record
  `protocol/v1/evidence/gate-records/s11-s1-guidance-locked.json`並在verified frozen
  edge後留在同一tranche進S12；此時closure unit尚未`COMPLETE`。
- Negative／inconclusive是本tranche的terminal internal gate，立即產生本design的
  planned terminal report並停止後續；`CHANGES_REQUIRED`依current reviewer-governed
  traceable repair semantics修復，不是scientific outcome，也不受frozen numeric repair
  budget限制。
- 若走到S13，最終`reports/gen0-factorization-mvp-report.md`必須整合S11 compact
  record與後續gate records；`live_run_state`與`committed_projection_state`分開，
  後者只在CU-S1 closure commit與post-commit audit後更新。

## 4. Maximum implementation 與 delivery boundary

允許：

- `pi_nominal`／`Fraw` occurrence collection與multiplicity-preserving catalog；
- `Fraw -> Fexec -> Fscore`：resolver、normal non-proxy KernelWriter generation、pinned
  compile、stable `Uexec` catalog、native Formocast scoring與coverage/tie audit；
- conditional top-up、trusted-set `T_g`、shrinkage marginals、gene decisions與global lambda；
- probability→hook-cost conversion、candidate-order parity與round-trip tests；
- same-entropy non-identity shuffle；
- guidance lock與sealed-label attestation。

禁止：

- 讀取或產生real GFLOPS、D5 judgments或oracle outputs；
- 修改existing groups／weights、candidate space或size registry；
- 加入Injection A、widening或parent未指定threshold；
- 建立S12+ evidence/report；
- 使用M02 pipeline、fixture或hash作相容性/PASS target。

Future plans必須將boundary縮成exact paths/symbols；S11 closeout不得包含下游implementation。

## 5. Future effective lock、inputs 與 outputs

Future lock：

`protocol/v1/locks/s11-stage1-model-only-factorization-lock.json`

它綁定 approved administrative `S1-REBASELINE-20260803`、fixed-frame measurement
`S11-S12-FIXED-FRAME-20260803`、S00–S10R3 immutable history identities與S10R4
retirement／zero-credit matrix；另綁定frozen YAML／space／
groups／weights／sizes、pinned sampler／`valid_fn`／resolver／normal KernelWriter／
compiler／native Formocast revisions、parent constants、fresh S11 randomness bundles、
global65,536-chunk與per-value512-chunk schedules、two-attempt qualification、terminal
formulas／outcome matrix、label-seal evidence、Plan-B、exact whitelists與report target。
B01–B06只能作 historical
provenance，B07 是 forbidden input；任何 S10R3/S10R4 empirical row都不得取得 S11
criterion credit。S11 必須由 fresh S11 seeds 自己建立 `Fraw/Fexec/Fscore`。

Outputs至少包括：

- raw `Fraw` occurrence frame、executable `Fexec/Uexec` catalog、scoreable
  `Fscore/Uscore` catalog、alias collision與multiplicity-preserving lineage；
- global／conditional terminal prefix manifests、chunk/slot counts、two-attempt qualification
  parity、global yield／coverage與per-cell`Draw/Dexec/Dscore`；
- model scores、coverage、ties與conditional top-ups；
- terminal global mid-ECDF、eligible/guided gene decision、own/familywise null與marginals；
- Formocast residual weights；
- shuffle manifest；
- probability round-trip與candidate-order results；
- immutable guidance bundle與machine decision。

## 6. Controls 與 measurement boundary

- `Fraw`是fresh validator-accepted raw occurrence multiset；duplicates保留，accepted後不因
  resolver／generation／compile／score failure從raw mass刪除。`Fexec`要求complete resolver
  projection、normal non-proxy KernelWriter generation、pinned compile與stable semantic
  identity；value preservation另在trust gate判。`Fscore`要求所有locked sizes都有finite
  native Formocast output。`Uexec/Uscore`只deduplicate work，不改occurrence mass。
- 每個semantic identity恰有producer與fresh verifier各一次complete qualification。Matching
  complete ordinary rejection是execution attrition；partial／discordant／association-lost／
  guessed evidence是`CHANGES_REQUIRED / not_evaluated`。
- Global inferential frame固定canonical first8,192 `Fraw_global` occurrences；first4,096與
  固定兩halves只read-only。Global cap是65,536個512-slot chunks＝33,554,432 draws；cap
  少於8,192 accepts是inconclusive。每activated conditional value固定512 chunks＝262,144
  draws、target first256 accepts；128只read-only，terminal 128–255 prefix只測一次，少於
  128是support-insufficient。禁止reseed、extension或pooling。
- Planning calculation固定為下式；historical rows／seeds對S11 criterion credit為零：

  ```text
  p_plan = 114 / 262,144 = 57 / 131,072 ~= 0.00043487548828125
  draws_for_8192 = 8,192 / p_plan = 1,073,741,824 / 57 ~= 18,837,575.85964912
  chunks_for_8192 = draws_for_8192 / 512 = 2,097,152 / 57 ~= 36,792.14035087719
  margin_chunks = 1.5 * chunks_for_8192 = 1,048,576 / 19 ~= 55,188.21052631579
  global_cap_chunks = next_power_of_two(margin_chunks) = 65,536
  global_cap_draws = 65,536 * 512 = 33,554,432
  ```

Exact global diagnostics與value cells是：

```text
Y_exec_global = |Fexec_global| / |Fraw_global|
C_score_occ_global = |Fscore_global| / |Fexec_global|
C_score_unique_global = |Uscore_global| / |Uexec_global|  # secondary only

Graw_gv   = {o in Fraw_global   : X_g(o)=v}
Gexec_gv  = {o in Fexec_global  : X_g(o)=v}
Gscore_gv = {o in Fscore_global : X_g(o)=v}
Draw_gv   = Graw_gv   multiset-union Fraw_cond(g,v)
Dexec_gv  = Gexec_gv  multiset-union Fexec_cond(g,v)
Dscore_gv = Gscore_gv multiset-union Fscore_cond(g,v)

support_gv    = |Fraw_cond(g,v)|
Cscore_occ_gv = |Dscore_gv| / |Dexec_gv|  # undefined if |Dexec_gv|=0
n_gv          = |Dscore_gv|
sum_b_gv      = sum_{o in Dscore_gv} benefit(o)
global_mean_g = [sum_{o in Fscore_global} benefit(o)] / |Fscore_global|
```

Global rows給zero conditional support credit；conditional rows不進global yield、coverage、
ECDF、`Uexec`或future D5。`C_score_occ_global>=0.95`；沒有新增execution-yield threshold。

Terminal global benefit與guidance formulas是：

```text
r_s(o) = [W_<(L_s(o)) + 0.5 * W_=(L_s(o))] / W
b_s(o) = 1 - r_s(o)
benefit(o) = sealed_actual_size_reducer({b_s(o) for every locked size s})
mu_gv = (sum_b_gv + 32 * global_mean_g) / (n_gv + 32)
S_g = max_{v in T_g}(mu_gv) - min_{v in T_g}(mu_gv)
q_g(v) = exp(lambda * (mu_gv - min_{u in T_g} mu_gu)) / Z,  v in T_g
q_g(v) = 0,                                                v not in T_g
p1_g(v) = 0.20 * p0_g(v) + 0.80 * q_g(v)
```

`L_s`是Formocast latency、越低越好；`W_<`／`W_=`是terminal global scoreable occurrence
mass。Conditional rowsquery同一global ECDF；all sizes of one occurrence是一個block。
`T_g`只含`support_gv>=128`、`|Dexec_gv|>=1`、unique value-preserving relation、
`Cscore_occ_gv>=0.95`與complete statistics的values。Untrusted values不是absent，並精確
保留`0.20*p0>0`。

Trust／mapping／coverage先凍結`Gtest`。2,000 block bootstraps重建ECDF與statistics，要求
fixed best-vs-worst 95% interval half-width`<=0.025`、recurrence`>=0.90`。每個permutation
replicate使用一份shared-global occurrence permutation；conditional部分對每個gene pool恰
產生一份independently domain-separated permutation，再依該gene各value的fixed observed
cell counts分配，禁止per-conditional-cell permutations。2,000 replicates計：

```text
M_r = max_{g in Gtest} S_gr*
Q95_own,g = HF7_0.95({S_gr*}_{r=1..2000})
Q95_family = HF7_0.95({M_r}_{r=1..2000})
```

Hyndman–Fan Type 7的`n=2,000` P95是
`0.95*x_(1900)+0.05*x_(1901)`；observed `S_g>=0.05`且嚴格大於own與family P95，ties
fail。另要求size direction 2/3、lambda grid 0..8 step0.25、entropy`>=0.80`、
round-trip／order／firewall與same-entropy shuffle。

兩個fixed 4,096 halves必須exact重建並比較完整semantic tuple：每value的`Dexec_gv`、
`Dscore_gv`、`n_gv`、`Cscore_occ_gv`與`mu_gv`；trust states／reasons、`T_g`、guided
states／reasons；按actual-YAML candidate order作best／worst tie-break後的best／worst；
per-size directions；每一項model-test result；own/familywise pass；同一positive global
lambda；每gene guidance probabilities；shuffle mapping；canonical guidance hash。全部欄位
都必須exact相同；numeric drift只報告。

兩固定halves共用sealed conditional corpus、各自重建global reference；完整semantic tuple
依本節前述每value cells／means、states／reasons、actual-YAML-order tie-break、全部tests、
probabilities、shuffle及canonical hash逐欄exact比較。Numeric drift只報告；full terminal
float32 guidance bundle另做integrity hash。Halves不是independent replication。

S11能說明model-only factorization是否可建立，不能說明real ranking、prior mass或actual
Gen0效果。它必須在S12任何GFLOPS前證明future D5 frame從 `Uexec` fixed 256 identities
without replacement建立，且每個 selected identity 先通過native/runtime、normal
generate/compile、correctness與noise readiness；本 authority closure不執行這些工作。

## 7. Acceptance binding 與 stop matrix

唯一positive criterion是parent的`S1_GUIDANCE_LOCKED`。Formal evidence須綁定guided genes、model-only criteria、coverage/support、weights/shuffle hashes、round-trip/order tests與no-leakage attestation。

Mapping-impossibility allowlist固定為`empty-v1`、精確內容`entries: []`；在沒有新的
pre-evidence authority前，mapping scientific outcome不可到達。下表是互斥first-match
terminal precedence；只有所有較早rows已證明false，才可到達較晚row。

| First-match order | 狀況 | checkpoint處理 | downstream |
| --- | --- | --- | --- |
| 1 | 任一prelabel／label-firewall leakage | evidence invalid／`not_evaluated`；新lock／fresh seeds後draw-0全量重跑 | 無 |
| 2 | Harness／schema／order／round-trip、partial／discordant qualification、association／identity或其他qualification／evidence-integrity failure | `CHANGES_REQUIRED / not_evaluated`；不得猜值 | 無 |
| 3 | 兩次complete attempts重現exact allowlisted no-guess native impossibility且需new authority | `FT-BLOCKED-MAPPING`；`empty-v1`下不可到達 | 無 |
| 4 | Material stochastic support／coverage／precision／recurrence／half-stability shortage、global cap少於8,192 accepts或`|Uexec_global|<256`可能改變no-guidance結論 | `inconclusive / FT-INCONCLUSIVE / edge=null`；不得降門檻 | 無 |
| 5 | 至少一個stable gene有`|T_g|>=2`且全部fixed／familywise／coverage／entropy／round-trip／shuffle／firewall／replay／fresh-verification gates通過，`|Uexec_global|>=256`且global lambda positive | positive closeout | S12 |
| 6 | Complete bounded family有deterministic terminal evidence，沒有gene通過effect／permutation／direction／entropy，或lambda為0 | complete bounded no-guidance negative formal closeout | 無 |

## 8. Formal report 與 closeout

S11 positive使用compact gate record
`protocol/v1/evidence/gate-records/s11-s1-guidance-locked.json`並繼續同tranche。
S11若negative／inconclusive而成為terminal，唯一formal report才是
`reports/staged/s11-stage1-model-only-factorization-report.md`；它需自含label-seal
證據、所有criteria、failure localization、artifacts、iteration history、先前gate
record與claim boundary。若S13成為tranche final，S13 report整合本record，不另製造
重複的S11 positive report。

Report必須另外列global／per-value chunk與slot counts、terminal accepted prefixes、
`Fraw/Fexec/Fscore`與`Draw/Dexec/Dscore` counts、two-attempt parity、global／cell yield與
coverage、mid-ECDF lineage、own/familywise P95、bootstrap、half semantic tuple、所有
untrusted reasons及terminal shortage。Positive只支持executable-and-scoreable survivor
frame中的label-blind candidate guidance；不支持raw transport、yield、representativeness、
correctness、real performance或actual Gen0 benefit。

## 9. Design-consensus record

- Reviewer A objection：只說「model-only」不足以防止D5 pool或real labels透過cache／artifact root影響gene selection。
- Reviewer B objection：把existing groups拆成independent genes或在shuffle後只比較nominal entropy，會改變protected baseline或掩蓋validity效應。
- 採納方案：explicit label-seal、root-level forbidden evidence、multiplicity-preserving occurrence frame、existing-group immutability、nominal shuffle加realized diagnostics。
- 捨棄方案：從real GFLOPS挑genes、按D5結果重調lambda、拆group或改weights；理由是它們造成leakage並改變研究問題。
- Shared resolution：S11只能交付immutable model-only guidance；任何negative仍正式closeout但不建立下游Stage 1 outcome。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`

> **Historical boundary：**以下 2026-07-26 至 2026-08-03 binding-06 dependency
> amendments保留當時 authority trail，但凡仍要求 S10R4 positive edge、
> `F_valid(raw) -> F_effective -> F_codegen` 舊名稱或 whole-gene fail-closed 的文字，
> 均由本檔 active §§1–7 與最後的 `S1-REBASELINE-20260803` record supersede，不能再作
> current entry／measurement authority。

### 2026-07-26 R12 dependency amendment

- S10已durable closeout為negative且沒有outgoing edge；不得由S11把它重解讀為GO。
- 兩位fresh recovery reviewers同意新增獨立S10R1，保持S10 immutable，並把
  validity、Formocast model sentinel與runtime queue semantics分離。
- 當時R12曾把S11 dependency指向S10R1；該historical authority已被下列A32
  amendment取消，沒有形成edge。S11的occurrence counts、model-only criteria、
  weights、shuffle、label seal與claim全部不變。
- Reviewer A final：`AGREE`。
- Reviewer B final：`AGREE`。
- 使用者已委派`/data1/perlee`內的此類block由design-discussion共識決定；
  amendment不授權push或任何downgrade。

### 2026-07-28 A32／S10R2 dependency amendment

- User-authorized A32在safe boundary取消S10R1：operational `cancelled / BLOCKED`、
  scientific `not_evaluated`、`edge=null`，沒有scientific report且不是
  `CHECKPOINT_COMPLETE`。
- S10R1 generations只作diagnostic lineage並禁止re-use；A33退休bulk bytes而不改
  outcome／edge／resource history。S11 dependency維持唯一post-audited
  `S10R2:S1_ENTRY_GO`。
- S11 hypothesis、4,096／8,192 occurrences、128／256 conditional support、
  thresholds、weights、shuffle、label seal、claim與timebox均不變。

### 2026-07-28 A34 prospective resource reservation

- Resource-relock reviewers`/root/s10r2_next_plan_a`與
  `/root/s10r2_next_plan_b`經一輪cross-examination及同一final candidate後均
  `AGREE`：historical S10R1 resource lower bounds／`UNKNOWN`不可重寫，A33 cleanup
  不是reset。
- `T-S1-MECHANISM`取得reserved、尚未activated的prospective allowance：最多5個
  new fresh role threads與3個new repair rounds；S11→S13內不得由internal edge、
  generation或new root再reset，且S13仍受R1 gate-specific最多2 repairs。這是A34
  historical boundary；prospective repair caps後由A44統一supersede為6。
- Reservation不構成S11 entry或resource preflight pass。只有post-audited
  `S10R2:S1_ENTRY_GO`可activate；entry時仍須把S10R2後的actual prospective
  consumption帶入shared Stage-1 7-day／1.4-day pre-empirical／5-GiB envelope，
  並以具單位wall／CPU／GPU caps與完整panel buffer重做preflight。
- 本amendment不改S11 hypothesis、4,096／8,192 occurrences、128／256 conditional
  support、thresholds、weights、shuffle、label seal、claim、edge或timebox。

### 2026-07-29 A38 S10R3 dependency amendment

- S10R2已依其frozen exact-ten criterion closeout為
  `CHECKPOINT_COMPLETE / inconclusive / FT-INCONCLUSIVE / edge=null`。它保持
  immutable，沒有S11 edge；舊`C_greedy=18`只作S10R3 design diagnostic。
- 使用者核准新的R3 sibling S10R3。S10R3使用fresh registry、disjoint seeds、
  append-only ledger與bounded deterministic exact-K：

  ```text
  K = max(10, C_greedy)
  K_max = 20
  ```

  只有post-audited `S10R3:S1_ENTRY_GO`可activate既有
  `T-S1-MECHANISM` reservation並啟動S11。
- S11把fresh S10R3 exact-K corpus當mapping／conformance fixture，不假設固定十筆；
  自己的4,096／8,192 accepted-occurrence frame、128／256 conditional support、
  eligible-gene criteria、`alpha`、`epsilon`、lambda grid、weights、shuffle、
  label seal、outgoing `S1_GUIDANCE_LOCKED -> S12`與claim全部不變。

### 2026-07-30 A44 universal six-round repair amendment

- 所有prospective R0–R3 gate-specific repair cap統一為6 rounds；因此
  `T-S1-MECHANISM`尚未activated的repair allowance與S11、S12、S13各gate上限都以6
  為準。既有消耗完整carry over，S11→S13 internal edge、generation、replacement、
  restart或new root都不能reset，第7輪仍需新的human authority。
- 本amendment只改execution governance；不改S11 entry dependency、4,096／8,192
  accepted-occurrence frame、128／256 conditional support、eligible-gene criteria、
  `alpha`、`epsilon`、lambda grid、weights、shuffle、label seal、claim、edge或
  timebox。
- Experiment-design ambiguity仍須雙agent交互詰問後交使用者決定；非設計
  contract-preserving雙agent共識已預授權直接執行。本authority不授權push、
  downgrade、destructive operation、dependency install或container mutation。
- S10R1與S10R2 outcome-bearing artifacts禁止作S11 evidence。S10R2只保留terminal
  provenance；S10R3 exact-K rows也只能作entry fixture，不能替代S11自己的
  multiplicity-preserving frame。
- S11 entry採A37 resource semantics：known／`UNKNOWN`歷史帳保留但不單獨debit
  successor；planning variance只record＋notify，只有material safety、availability、
  full-workload、optional-stopping或evidence condition暫停。Scientific workload、
  repair/thread caps與downgrade gates不變。
- A38未改S11的scientific hypothesis、samples、seeds、thresholds、workloads、
  failure taxonomy、report path、internal edge或claim，也不授權push。

### Historical/superseded 2026-08-02 A47 S10R4 exact-frame dependency amendment

- S10R3已closeout為immutable
  `CHECKPOINT_COMPLETE / negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING /
  edge=null`，因此不再是S11 edge source。
- 兩位fresh independent reviewers完成兩輪cross-examination及一輪evidence-backed
  final，均`AGREE`；使用者選擇並核准新增R3 sibling S10R4。
- 只有post-audited `S10R4:S1_ENTRY_GO_EXACT_FRAME`可啟動S11。該edge只證明S10R3
  exact sealed frame經normal codegen filter後含bounded reproducible entry fixture；
  不證明general operational support或independent replication。
- S11不得把S10R4的114-row frame、survival rate或selected K當作自己的formal
  occurrence frame。S11以disjoint seeds fresh建立multiplicity-preserving `F_valid`，
  再以同一normal KernelWriter filter形成`F_codegen`；所有codegen rejects保留在
  `F_valid` global occurrence-mass coverage分母，只對survivors mapping/scoring。
- Parent既有whole-config Formocast coverage `>=95%`、4,096/8,192 accepted
  occurrences、128/256 conditional support及conditional/non-pooled semantics不變。
- Whole-gene fail-closed eligibility保持；post-observation value-level guidance proposal
  延後，不在本amendment採用。
- S11其餘model-only criteria、`alpha`、`epsilon`、lambda grid、weights、shuffle、
  label seal、`S1_GUIDANCE_LOCKED -> S12`、timebox與claim不變；不授權push。

### Historical/superseded 2026-08-02 A51 S10R4 binding-04 dual-lineage dependency amendment

- S10R4 binding-02曾完成effective lock與`LOCKED_READY`，但第一個formal child留下
  partial後fail closed，現為
  `cancelled / BLOCKED / not_evaluated / edge=null / lock=superseded`。Binding-03則在
  effective lock前fail closed，現為
  `binding_status=superseded_prelock / execution_status=cancelled /
  checkpoint_state=BLOCKED / criterion_status=CHANGES_REQUIRED /
  scientific_outcome=not_evaluated / edge=null / lock_state=absent /
  lock_never_created=true`。A51沒有重解讀任一failure為KernelWriter、mapping或
  scientific outcome；它建立fresh binding-04 authority。
- 兩位fresh independent reviewers以相同direct evidence完成一輪cross-examination及
  一輪evidence-backed final並均`AGREE`；使用者核准dual-lineage amendment。
- S10R4唯一可能的post-audited edge仍是`S1_ENTRY_GO_EXACT_FRAME`。該edge現在只證明
  固定114-occurrence raw frame經pinned resolver與normal KernelWriter workflow產生
  bounded reproducible distinct-effective-state entry fixture，不證明literal raw
  realization、injectivity、general support或value-level causal effect。
- S11不得重用S10R4的114 rows作formal population。它必須以disjoint seeds fresh建立
  multiplicity-preserving `F_valid(raw) -> F_effective -> F_codegen`；raw occurrence
  始終保留於denominator，resolver collision group保留aliases及multiplicity，effective
  semantics才供mapping與operational features使用。
- Raw candidate value只有在frozen relation中沒有behavior-changing overwrite且確實
  realized時才取得guidance evidence。Normalized-away、context-dependent、ambiguous或
  collision-confounded raw values沒有controllability/guidance credit；whole-gene
  fail-closed eligibility與deferred value-level guidance proposal保持。
- Parent既有4,096/8,192 accepted occurrences、128/256 conditional support、whole-config
  Formocast coverage `>=95%`、`alpha`、`epsilon`、lambda grid、weights、shuffle、label
  seal、`S1_GUIDANCE_LOCKED -> S12`、timebox與claim不變；不授權push。

### Historical/superseded 2026-08-03 S10R4 binding-06 provenance-successor dependency amendment

- Binding-04在effective lock與formal rows前發現source-closure defect，固定為
  `superseded_prelock / cancelled / BLOCKED / CHANGES_REQUIRED / not_evaluated /
  edge=null / lock=absent / lock_never_created=true`。該defect不是codegen attrition、
  mapping/correctness failure或scientific result。
- Binding-05保留下列science，但其ignored ledger在implementation前違反
  sorted-canonical event-hash規則，固定為`superseded_prelock / cancelled / BLOCKED /
  CHANGES_REQUIRED / not_evaluated / edge=null / lock=absent`，提供zero S11 credit。
- Current B06必須以actual YAML/defaults、`initGEMM`、`assignDerivedParameters`及
  `getTensorParameters`證明`Index0=0 / Index1=1`，再關閉ordinary與wave-separated
  TDM的`MacroTile{ti}`至`MacroTile0/1`。此外，兩位existing reviewers獨立author/traverse
  whole pinned Tensile subtree exact 89-node dynamic-access closure（68 direct＋21
  `tP["mt"]` carrier consumers），canonical records相同且
  unresolved exact 0，才能建立effective lock。
- B06不改S10R4的114 raw denominator、dual-lineage operational identity、ordered 114x2
  census、selector、mapping/native/correctness/noise、outcome matrix或claim。B02-B04
  以及B05 formal/run-root artifacts不提供B06或S11 evidence credit。
- S11唯一dependency仍是post-audited
  `S10R4:S1_ENTRY_GO_EXACT_FRAME`。只有B06 terminal commit及postcommit audit後的positive
  edge有效；B06 technical closure PASS或`LOCKED_READY`都不能啟動S11。
- S11仍需disjoint seeds fresh建立
  `F_valid(raw) -> F_effective -> F_codegen`，保留raw mass、aliases及multiplicity。
  Existing 4,096/8,192 occurrences、128/256 support、coverage、whole-gene fail-closed、
  model criteria、weights、shuffle、label seal、timebox、claim與S12 edge全部不變。
- B06只更新dependency provenance；不授權S11 implementation、evidence、report、lock或push。

### 2026-08-03 approved `S1-REBASELINE-20260803` amendment

- Reviewer A `/root/full_research_design_audit_a` 與 Reviewer B
  `/root/full_research_design_audit_b` 完成兩輪 cross-examination 與一輪
  evidence-backed final，均 `AGREE`，沒有 material dissent；使用者核准 amendment。
- S10R4/B01–B07 退役且 `not_evaluated / edge=null`。S11 entry 改為 administrative
  prerequisite；`incoming_scientific_edge=null`，不補造 S10R4 success。
- Exact active population 是 `Fraw/Fexec/Fscore`；normal resolver、KernelWriter generation
  與 pinned compile 全在 Formocast 前決定 `Fexec`。Primary score coverage以 `Fexec`
  occurrence mass為 denominator。
- Whole-gene fail-closed 改為 trusted set `T_g`；untrusted value保持
  `p1=0.20*p0`，shrinkage `alpha=32`，其餘 numeric criteria／schedule／label firewall不變。
- S11現為 `approved / not_started / DESIGN_APPROVED / not_evaluated / lock absent`。
  本 amendment 沒有執行 S11 evidence；唯一 future edge仍是
  `S11:S1_GUIDANCE_LOCKED -> S12`。

### 2026-08-03 approved `S11-S12-FIXED-FRAME-20260803` amendment

- Full-study Reviewer A `/root/full_study_review_a`與independent non-implementer Reviewer B
  `/root/s11_contract_auditor`完成兩輪cross-examination與一輪evidence-backed final，均
  `AGREE`、無material dissent；使用者核准prospective R3 amendment。
- Global fixed frame改成canonical first8,192 accepts；first4,096與固定halves只read-only。
  Finite cap是65,536 chunks／33,554,432 draws。每activated conditional value固定512
  chunks／262,144 draws、target first256；128只read-only。
- Exact global／conditional cells、terminal global mid-ECDF、2,000 block bootstraps、own-null
  與familywise max-null Type-7 P95、strict ties及semantic half-stability依active §§5–7綁定。
- `Fexec`與raw-value trust分離；每semantic identity固定producer＋fresh verifier兩次complete
  qualification。S11 positive claim限executable-and-scoreable survivor-frame guidance。
- 本 amendment 不執行S11、沒有result／effective checkpoint lock／report／edge。既有
  untracked runner／package／contract／schema必須在committed authority後另行對齊、驗證與
  reseal，不能提供本次authority evidence。
