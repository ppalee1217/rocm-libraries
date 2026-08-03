---
document_type: prospective_authority_amendment
authority_id: S11-S12-FIXED-FRAME-20260803
risk_tier: R3
approval_state: approved_pre_evidence
scientific_outcome: not_evaluated
evidence_executed: false
created_date: 2026-08-03
---

# S11／S12 fixed-frame measurement 權威修正

> **白話結論：**這次只修正尚未執行的 S11／S12 measurement authority。S11 改成一個
> 固定 8,192 accepted-occurrence inferential frame，並為 global 與每條 conditional
> stream 設定有限 nominal-draw cap；S12 改用可超過 1、不得 clipping 的 design-based
> `M_HT` directional index。這次沒有執行 experiment、讀取 result、建立 lock、寫 report
> 或產生 scientific edge。

本檔是 prospective Layer-B authority candidate；只有 Main 之後把 exact delivery
whitelist 以 isolated commit seal，才成為 Layer-A authority。它不是 S11／S12 runner、
effective lock、formal evidence 或 scientific report。第一次閱讀請先看
[繁中變更指南](s11-s12-fixed-frame-measurement-change-guide.md)。

## 1. Authority identity、範圍與不可推導事項

- Authority ID：`S11-S12-FIXED-FRAME-20260803`。
- Authority gate：`AUTH-S11-S12-FIXED-FRAME-20260803`；risk tier 是 `R3`，因為它在
  evidence 前 prospectively 修改 S11／S12 measurement、stopping 與 claim authority。
- Scientific gate／outcome／edge：`N/A / not_evaluated / null`。
- `evidence_executed=false`；S11 仍是
  `approved / not_started / DESIGN_APPROVED / not_evaluated / lock absent`，S12 仍是
  `approved / gated / DESIGN_APPROVED / not_evaluated / lock absent`。
- 本 amendment 不授權 S11 process、Formocast、KernelWriter、compile、GPU correctness、
  GFLOPS、S12 labels、report、dependency installation、container mutation、push 或
  publication。
- 本 amendment 不把 planned behavior 當 live observation，也不把 technical document
  validation 當 scientific `PASS`。

## 2. 不可變 history 與 evidence reuse boundary

S00 至 S10R4 的 exact committed outcomes、reports、decisions 與 edges 全部不變：

| Checkpoint | Committed／historical state | Scientific outcome | Edge／S11 credit |
| --- | --- | --- | --- |
| S00 | `CHECKPOINT_COMPLETE` | `positive` | 只保留既有 `S00_EVIDENCE_READY -> S10` |
| S10 | `CHECKPOINT_COMPLETE` | `negative / FT-BLOCKED-MAPPING` | `edge=null` |
| S10R1 | `cancelled / BLOCKED` | `not_evaluated` | `edge=null`；reuse forbidden |
| S10R2 | `CHECKPOINT_COMPLETE` | `inconclusive / FT-INCONCLUSIVE` | `edge=null`；zero S11 credit |
| S10R3 | `CHECKPOINT_COMPLETE` | `negative / FT-BLOCKED-MAPPING` | `edge=null`；zero S11 credit |
| S10R4/B01–B07 | retired／superseded／not admitted | `not_evaluated` | `edge=null`；zero S11 credit |

S10R3 的 `114 accepts / 262,144 nominal draws` 只可作 pre-empirical planning rate；其
rows、seeds、support classifications、mapping、diagnostics、GPU 或 decisions 都不能進入
S11 `Fraw/Fexec/Fscore`、support、score、guidance、criterion 或 gate evidence。S11 必須
使用 fresh domain-separated seeds，從 global draw 0 與每條 conditional draw 0 建立
自己的 evidence。

## 3. 核准程序與 authority record

- Reviewer A：`/root/full_study_review_a`，fresh read-only design reviewer，requested／
  actual capability `gpt-5.6-sol`、reasoning `xhigh`。
- Reviewer B：`/root/s11_contract_auditor`，未參與 S11 implementation、未讀 Plan-A 的
  independent non-implementer auditor；因 fresh-thread limit 而揭露並沿用 prior
  S11 contract-audit role。Orchestrator 沒有提供 exact model metadata；沒有刻意選擇
  lower-capability substitution。
- 程序：兩輪 cross-examination，加一輪 evidence-backed final；兩位 final 都是
  `AGREE`，沒有 material dissent。
- 使用者收到 unified full-study recommendation 後，核准本 prospective R3 amendment、
  exact authority／design synchronization 與 no-experiment boundary。
- 被拒絕的替代方案包括：重開 S10R4、重用 historical rows、以 4,096 作 effect／precision
  early stop、為把 index 壓到 0–1 而 clipping 或改成 sampled denominator、以及把 day／
  repair／resource counter變成 scientific stop。

## 4. S11 fixed schedule 與 planning calculation

### 4.1 Frozen family 與 atomic chunk

Registry 必須包含 actual YAML 中每個 frozen-free、ungrouped、currently-unweighted 且
cardinality 大於 1 的 residual gene value，保持 typed candidate order、existing groups
與 existing weights。除非在 score 前已有 finite、sound、兩次 complete attempts 都重現的
absence proof，否則每個 value 都要啟動；禁止 model-ranked top-k screen。

每個 atomic chunk 固定 512 nominal slots，使用 fresh domain-separated PCG64 seed。每條
stream 的 credited frame 是 canonical first-`N` accepted prefix；chunk boundary 的
overshoot 只作 diagnostic，不可取得 sample credit。禁止 reseed、cap extension 或按結果
挑 prefix。

### 4.2 Global planning rate、margin 與 cap

Historical planning-only acceptance rate是：

```text
p_plan = 114 / 262,144 = 57 / 131,072 ~= 0.00043487548828125
draws_for_8192 = 8,192 / p_plan = 1,073,741,824 / 57 ~= 18,837,575.85964912
chunks_for_8192 = draws_for_8192 / 512 = 2,097,152 / 57 ~= 36,792.14035087719
margin_chunks = 1.5 * chunks_for_8192 = 1,048,576 / 19 ~= 55,188.21052631579
global_cap_chunks = next_power_of_two(margin_chunks) = 65,536
global_cap_draws = 65,536 * 512 = 33,554,432
```

`p_plan` 只規劃 finite envelope，不是 S11 acceptance estimate、evidence 或 claim。Actual
acceptance 不因與它不同而停止或換 seed。

### 4.3 Global 與 conditional schedules

- Global inferential frame是 canonical first 8,192 accepted `Fraw_global` occurrences。
- Canonical first 4,096 只作 read-only diagnostic。固定兩個 4,096 halves 在 terminal
  8,192 frame 上作 semantic stability comparison；任一 half 都不能停止 experiment、
  emit outcome 或選擇是否收集第二 half。
- Global finite cap是 exactly 65,536 chunks，即 33,554,432 nominal draws。Cap 時少於
  8,192 accepts 為 `inconclusive / FT-INCONCLUSIVE`。
- 每個 activated、非 `support_proven_absent` value 的 conditional stream固定 exactly
  512 chunks，即 262,144 nominal draws，目標 canonical first 256 accepted
  `Fraw_cond(g,v)` occurrences。
- Conditional 128 point只作 read-only support／precision diagnostic。Cap-terminal prefix
  有 128–255 accepts時只在 terminal analysis測試一次；少於128是support-insufficient。
- Global rows不能取得conditional support credit；conditional rows不能進 global yield、
  coverage、ECDF、`Uexec` 或 future D5。

## 5. Population、cell 與 qualification measurement

### 5.1 Population objects

- `Fraw` 是 pinned `valid_fn` 接受、且位於 `IndividualSet` dedup 前的 raw occurrence
  multiset。Occurrence 是一次 accepted nominal slot；相同 config 抽到兩次仍是兩筆。
- `Fexec` 是 `Fraw` 中完成 unique resolver projection、stable consumer-relevant semantic
  operational identity、normal non-proxy KernelWriter generation 與 pinned compile 的
  occurrence submultiset。Value preservation不是 `Fexec` membership；它另由 value trust
  gate 判定。
- `Fscore` 是 `Fexec` 中所有 locked sizes 都由 pinned native Formocast path產生 finite
  score與complete provenance的 occurrence submultiset。
- `Uexec/Uscore` 是對應 occurrence multiset 的 deduplicated operational identities。
  Unique identity可含多個raw aliases；dedup只節省工作，不能刪 occurrence mass。

Global 與 conditional populations各自保存。Global primary diagnostics為：

```text
Y_exec_global = |Fexec_global| / |Fraw_global|
C_score_occ_global = |Fscore_global| / |Fexec_global|
C_score_unique_global = |Uscore_global| / |Uexec_global|  # secondary only
```

分母為零時 ratio 是 undefined，不能填 0。`C_score_occ_global>=0.95` 是 required global
model coverage；`Y_exec_global`沒有新增 numeric threshold，但必須完整報告。

### 5.2 Exact value-cell multisets

對 registry cell `(g,v)`，`X_g(o)` 是 occurrence `o` 的 raw gene value：

```text
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

`Draw/Dexec/Dscore` 只服務 value-cell survivor estimand；它們不能改 global population。
`support_gv`只計 conditional accepts。`global_mean_g`只來自 terminal global `Fscore`，
不依賴 final trusted set `T_g`。

### 5.3 Exactly two qualification attempts

每個 deduplicated semantic identity恰有兩次 complete ordinary qualification：producer一次、
fresh verifier一次。兩次matching complete ordinary rejection是execution attrition；partial、
discordant、association-lost、ambient invalidation或guessed evidence一律
`CHANGES_REQUIRED / not_evaluated`。只有 pre-allowlisted、no-guess native impossibility由
兩次 complete attempts 重現，且修復需要新的 scientific authority，才是
`FT-BLOCKED-MAPPING`。

## 6. Benefit、trusted survivor estimand 與 resampling

### 6.1 Terminal global mid-ECDF benefit

對 locked size `s`，以 terminal global `Fscore` occurrence mass建立 Formocast latency
mid-empirical cumulative distribution function（mid-ECDF）。`L_s(o)`越低越好；`W`是該
size全部 global scoreable occurrence mass，`W_<`是 latency嚴格小於 `L_s(o)` 的 mass，
`W_=`是等於它的 mass：

```text
r_s(o) = [W_<(L_s(o)) + 0.5 * W_=(L_s(o))] / W
b_s(o) = 1 - r_s(o)
benefit(o) = sealed_actual_size_reducer({b_s(o) for every locked size s})
```

`r_s`越小表示預測 latency越好，`b_s`與`benefit`越大越好。Conditional rows query同一個
terminal global ECDF；它們不重建或改變 ECDF。所有 sizes of one occurrence 永遠是一個
analysis block。

### 6.2 Trusted set、shrinkage 與 probabilities

Value `v` 進入 `T_g`，必須同時有 `support_gv>=128`、至少一個 `Dexec_gv` occurrence、
unique value-preserving relation、`Cscore_occ_gv>=0.95` 與 complete model-only
statistics。Normalized-away、context-dependent、collision-confounded、execution-attrited、
score-attrited或unresolved values都是untrusted，不代表absent。

```text
mu_gv = (sum_b_gv + 32 * global_mean_g) / (n_gv + 32)
S_g = max_{v in T_g}(mu_gv) - min_{v in T_g}(mu_gv)
q_g(v) = exp(lambda * (mu_gv - min_{u in T_g} mu_gu)) / Z,  v in T_g
q_g(v) = 0,                                                v not in T_g
p1_g(v) = 0.20 * p0_g(v) + 0.80 * q_g(v)
Hnorm_g = H(p1_g) / log(|V_g|)
```

`alpha=32` 是 shrinkage constant，`epsilon=0.20` 是 baseline mixture。Lambda grid固定
`{0,0.25,...,8.00}`；選擇讓所有 guided genes `Hnorm_g>=0.80` 的最大 positive global
lambda。Untrusted values精確保留 `0.20*p0_g(v)>0`。Same-entropy shuffle固定 untrusted
mass，只在 `T_g` 對 `q_g` 做 prelocked deterministic nonidentity permutation。

### 6.3 Bootstrap 與 familywise permutation

Trust／mapping／coverage先凍結 final testable family `Gtest`，之後才能觀察 `S_g`。
Resampling固定 2,000 replicates；global occurrence與其所有 sizes保持同一 block，global
與各 conditional cells分開resample，每個 replicate都重建global ECDF、cell statistics、
`mu_gv`、`S_g`、best／worst與size directions。

Bootstrap replicate `r` 的 fixed observed best-vs-worst contrast與recurrence定義為：

```text
Delta_gr* = mu_g,best,r* - mu_g,worst,r*
half_width_g = [Q_0.975({Delta_gr*}) - Q_0.025({Delta_gr*})] / 2
recurrence_g = (1 / 2,000) * sum_r I[(best_gr*, worst_gr*)=(best_g, worst_g)]
```

Required `half_width_g<=0.025`、`recurrence_g>=0.90`；`[0.80,0.90)`只作borderline，
不能guided。

Permutation replicate `r` 使用一份shared-global occurrence permutation保留cross-gene
dependency。Conditional部分則對每個gene pool恰產生一份independently domain-separated
permutation，再依該gene各value的fixed observed cell counts分配；禁止為每個conditional
cell另產生permutation：

```text
M_r = max_{g in Gtest} S_gr*
Q95_own,g = HF7_0.95({S_gr*}_{r=1..2000})
Q95_family = HF7_0.95({M_r}_{r=1..2000})
```

Hyndman–Fan Type 7（HF7）對排序後 `x_(1)..x_(n)` 定義
`h=(n-1)q+1`、`j=floor(h)`、`gamma=h-j`、
`HF7_q=(1-gamma)x_(j)+gamma*x_(j+1)`。在 `n=2,000, q=0.95` 時，
`h=1900.05`，所以 `Q95=0.95*x_(1900)+0.05*x_(1901)`。Observed `S_g` 必須
`>=0.05`，並且嚴格大於 `Q95_own,g` 與 `Q95_family`；ties fail。

### 6.4 Fixed-half semantic stability

兩個固定 4,096 halves共用sealed conditional corpus，但各自只用自己的global half重建
reference。它們必須exact重建並比較完整semantic tuple：每value的`Dexec_gv`、
`Dscore_gv`、`n_gv`、`Cscore_occ_gv`與`mu_gv`；trust states／reasons、`T_g`、guided
states／reasons；按actual-YAML candidate order作best／worst tie-break後的best／worst；
per-size directions；每一項model-test result；own/familywise pass；同一positive global
lambda；每gene guidance probabilities；shuffle mapping；以及canonical guidance hash。
全部欄位都必須exact相同。Numeric drift只報告、不另加threshold；terminal full-frame
float32 guidance bundle另外做integrity hash。Halves不是independent scientific replication。

## 7. S11 terminal matrix 與 claim boundary

Mapping-impossibility allowlist固定為`empty-v1`，其內容精確為`entries: []`。因此在目前
authority下，沒有mapping scientific outcome可被觸發；任何候選mapping impossibility都需
新的pre-evidence authority先加入exact allowlist，不能由runner或verifier臨場擴充。

下表是互斥的first-match terminal precedence。只有所有較早rows已被證明false，才可到達
較晚row；不能先選較有利或較容易命名的outcome。

| First-match order | Terminal condition | State／outcome | Edge／可支持結論 |
| --- | --- | --- | --- |
| 1 | 任一prelabel／label-firewall leakage | evidence invalid；`not_evaluated` | 無scientific outcome或edge；fresh lock／seeds並從draw 0重跑 |
| 2 | Harness／schema／order／round-trip defect、partial／discordant qualification、identity／association loss、guessed field或其他qualification／evidence-integrity failure | `CHANGES_REQUIRED / not_evaluated` | 無scientific outcome或edge |
| 3 | Exact allowlisted no-guess native impossibility由兩次complete attempts重現，且需new authority | `FT-BLOCKED-MAPPING` | blocked；無edge；`empty-v1`下不可到達 |
| 4 | 沒有positive gene，且material stochastic support、coverage、precision、recurrence、half-stability、catalog shortage或`|Uexec_global|<256`可能改變no-guidance結論 | `inconclusive / FT-INCONCLUSIVE` | `edge=null` |
| 5 | 至少一個stable gene有`|T_g|>=2`且通過全部fixed、familywise、coverage、entropy、round-trip、shuffle、firewall、replay與fresh-verification gates；`|Uexec_global|>=256`；global lambda positive | positive | `S1_GUIDANCE_LOCKED -> S12`；只支持survivor-frame label-blind guidance |
| 6 | Complete bounded family有deterministic terminal evidence，且沒有gene通過effect／permutation／direction／entropy，或global lambda為0 | complete bounded no-guidance negative | `edge=null`；只支持本frozen procedure未建立guidance |

S11 positive只表示在 executable-and-scoreable survivor frame 中，至少一個 complete
residual gene可建立stable、familywise、label-blind candidate guidance。它不支持raw
transport、acceptance yield、representativeness、GPU correctness、real ranking、real
performance、Gen0 benefit或production value。S12才是pre-registered full-`Fraw`
transport audit。Label leakage使整次 S11 evidence invalid，必須新 lock、fresh seeds並從
draw 0全量重跑。

## 8. S12 `M_HT`、`T_D5` 與 bootstrap

Stable estimator identity固定為
`S12-DIRECTIONAL-FINITE-FRAME-HT-EXACT-DENOMINATOR-v1`；任何consumer只能按此identity
機械繼承以下sample、set、numerator、exact denominator與reconstruction semantics。

D5從global `Uexec`無replacement抽exactly 256 unique identities；`Uscore`依global
occurrence mass形成10個weighted deciles，`Uexec\Uscore`是第11個stratum。`rho_j` 是
identity `j` 由這個sealed stratified design得到的inclusion probability，必須滿足
`0<rho_j<=1`。所有 arms、shuffle與oracle共用同一sample、`rho_j`和materialized
`T_D5`。

對 arm `a`、selected identity `j` 與它的 global raw aliases：

```text
r_a(o)   = pi_nominal,a(o) / pi_nominal,0(o)
A_aj     = sum_{o aliases j} r_a(o)
N_HT,a   = sum_{j in D5} [A_aj / rho_j] * I[j in T_D5]
D_exact,a = sum_{o in Fraw_global} r_a(o)
M_HT,a   = N_HT,a / D_exact,a
ESS_a    = [sum_{j in D5} A_aj/rho_j]^2 / sum_{j in D5}[A_aj/rho_j]^2
```

`M_HT` 是 design-based directional finite-frame raw-mass capture estimator：numerator用
Horvitz–Thompson inverse-inclusion expansion，denominator是known complete global `Fraw`
mass。它不是bounded probability或observed mass fraction；realized value可大於1，越大
表示directionally估計arm投向real-high-quality set的raw mass較多。禁止clip、winsorize、
post-hoc normalize或改用sampled denominator。

### 8.1 Prelabel `T_D5` rule

在 exactly-256 D5 sample中，先用baseline design weight：

```text
w_0j = A_0j / rho_j
Q_D5(t) = [sum_{j in D5} w_0j * I[quality_j <= t]] / sum_{j in D5} w_0j
t_D5 = min{quality_j : Q_D5(quality_j) >= 0.90}
T_D5 = {j in D5 : quality_j >= t_D5}
```

`quality_j` 是按sealed reducer聚合所有locked sizes的real quality，越大越好。Cutoff是
weighted empirical cumulative mass首次到達0.90的最小observed quality；所有 cutoff ties
都進 `T_D5`。這個rule、orientation與tie handling在labels前seal；它不是看完結果後挑
exactly 10% identities。

### 8.2 Stratum／identity bootstrap

S12 bootstrap固定沿sealed strata重抽 unique identity blocks；同identity的aliases、sizes、
repeats與derived rows不能拆開。每個bootstrap replicate都重新建立 `t_D5`、`T_D5`、
`A_aj`、`N_HT,a`、`M_HT,a`、arm contrasts、`ESS_a`與oracle gap，而不是固定observed
top set。Failed／unscored rows依frozen no-replacement matrix保留，不得replacement。

Preserved D5 criteria仍是：aggregate Spearman pass `>=0.25`、borderline
`[0.20,0.25)`；top-decile lift pass `>=2.0`、borderline `[1.5,2.0)`；direction至少
2/3 sizes；`M_HT` strictly勝baseline與same-entropy shuffle；`ESS>=25`；planned real
coverage `>=0.95`；correctness；five-fold config-level oracle；existing
bootstrap／permutation／tie與label-firewall rules。S12在本 amendment 中不執行。

## 9. S41 estimator inheritance

S41不再使用或描述「self-normalized `M_a(T)`」。每個 primary held-out unit必須機械繼承
stable estimator identity
`S12-DIRECTIONAL-FINITE-FRAME-HT-EXACT-DENOMINATOR-v1`及本檔 exact
`r_a/A_aj/N_HT/D_exact/M_HT/T_D5/rho_j` identities、shared sample、all-size quality、ties、
bootstrap reconstruction與no-clipping semantics。Stage-4 comparator為：

```text
oracle_gap_a = max(0, M_HT,oracle - M_HT,a)
```

Learned `M_HT`必須strictly同時高於Formocast-factorized與same-entropy shuffled，且learned
directional-index oracle gap必須strictly小於Formocast gap。這是finite held-out frame的
observed directional index comparison，不是probability gap、practical effect、stability、
significance、population generalization、prospective replication或actual-GA evidence。

## 10. Supersession、reseal 與 exact delivery paths

本 amendment只supersede下列active normative clauses；historical `4H/5H/6H`與historical
dependency records保持原bytes／historical label，不可重新解讀成current authority：

- Parent active §§4–6 的 4,096 early-stop／8,192 accepted hard-cap、128 precision-stop、
  per-gene own-null-only test、bounded `M_a(T)`與self-normalized wording。
- S11 design active §§1–8 的same clauses與`frozen repair budget` wording。
- S12 design active hypothesis／inputs／outputs／controls／formula／claim／report expectations。
- S41 active prior-mass與oracle-gap comparator wording。
- S20／S31把day count當hard scientific stop的prose；days改為Layer-C record＋notify。

Authority／design synchronization 的exact 14-path delivery set是：

1. `study_docs/research/ductile-origami-warmstart/s11-s12-fixed-frame-measurement-amendment.md`
2. `study_docs/research/ductile-origami-warmstart/s11-s12-fixed-frame-measurement-change-guide.md`
3. `study_docs/research/surrogate-dse-plan.md`
4. `study_docs/research/ductile-origami-warmstart-experiment-plan.md`
5. `study_docs/research/ductile-origami-warmstart-experiment-guide.md`
6. `study_docs/research/ductile-origami-warmstart/README.md`
7. `study_docs/research/ductile-origami-warmstart/s10r4-to-s11-experiment-plan-change-guide.md`
8. `study_docs/research/ductile-origami-warmstart/s11-stage1-model-only-factorization-design.md`
9. `study_docs/research/ductile-origami-warmstart/s12-stage1-real-score-ranking-oracle-audit-design.md`
10. `study_docs/research/ductile-origami-warmstart/s20-stage2-h10-persistence-design.md`
11. `study_docs/research/ductile-origami-warmstart/s31-stage3-bounded-replication-design.md`
12. `study_docs/research/ductile-origami-warmstart/s41-stage4-learned-residual-analysis-design.md`
13. `study_docs/research/ductile-origami-warmstart/protocol/v1/s11-s12-fixed-frame-measurement-authority-contract.yaml`
14. `study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s11-s12-fixed-frame-measurement-authority-lock.yaml`

Paths 13–14是pre-sealed candidates；本 document implementer不得修改。Main只有在14 paths
exact staged audit、`CLOSEOUT_ACK`、isolated commit與post-commit audit都成功後，才可把
本 authority投影成committed。先前 untracked S11 runner、package、experiment-contract
draft與schema都在本 closure之外，不能stage、commit、讀作 authority或執行。

Future S11 machine contract與effective lock必須在 evidence 前以本 amendment重新產生、
完成human/machine parity與fresh adversarial audit，並綁定exact family、sizes、reducer、
seeds、caps、two-attempt qualification、firewall、formulas、whitelists與outcome matrix。
任何舊 draft／lock都不能因檔名相同而沿用。

## 11. Artifact layers 與下一個合法動作

Exact-path commit與post-commit audit都成功後，Layer A精確有11份authority：

1. `s11-s12-fixed-frame-measurement-amendment.md`；
2. `../surrogate-dse-plan.md`；
3. `../ductile-origami-warmstart-experiment-plan.md`；
4. `README.md`；
5. `s11-stage1-model-only-factorization-design.md`；
6. `s12-stage1-real-score-ranking-oracle-audit-design.md`；
7. `s20-stage2-h10-persistence-design.md`；
8. `s31-stage3-bounded-replication-design.md`；
9. `s41-stage4-learned-residual-analysis-design.md`；
10. `protocol/v1/s11-s12-fixed-frame-measurement-authority-contract.yaml`；
11. `protocol/v1/locks/s11-s12-fixed-frame-measurement-authority-lock.yaml`。

同一post-commit projection中，Layer B精確只有3份non-authoritative guides：

1. `s11-s12-fixed-frame-measurement-change-guide.md`；
2. `../ductile-origami-warmstart-experiment-guide.md`；
3. `s10r4-to-s11-experiment-plan-change-guide.md`。

這三份guides不因同commit交付而升格為Layer A，不能覆蓋上述11份authorities。Commit前，
12份implementation documents與pre-sealed contract/lock仍只是delivery candidates；既有
untracked S11 candidates不屬於這個14-path projection。
- Layer C：plans、review routing、resource forecast、command summary、repair與live-state
  bookkeeping；只能record／notify／traceable correction，不能改science。

本 authority commit仍只是authority closure：沒有experiment、result、effective S11/S12
lock、formal report、scientific outcome或edge。下一個合法動作是 Main完成exact-path
authority closeout後，依新authority重新對齊S11 machine contract、runner/schema parity、
fresh audit與effective lock；全部prelabel gates通過後，才可從fresh global／conditional
draw 0開始S11。S12保持gated且unexecuted。
