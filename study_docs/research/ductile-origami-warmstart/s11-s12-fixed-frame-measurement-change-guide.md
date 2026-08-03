# S11／S12 fixed-frame measurement 變更指南

> **這次改了什麼：**S11 不再在 4,096 accepted occurrences 看 effect 後決定是否停止，
> 而是固定收集 canonical first 8,192 accepted occurrences；global 與每個 conditional
> stream 都有事前固定的 nominal-draw cap。S12 的 raw-mass metric改名為 `M_HT`，明確是
> 可大於 1 的 design-based directional index，不能 clipping 成 0–1。
>
> **為什麼要改：**舊 global schedule有第二次 inferential look，且在 historical
> planning rate下舊 nominal envelope很可能收不到8,192 accepts；舊 S12 公式使用
> inverse-inclusion expansion，realized value本來就可能超過1，把它叫probability或硬裁切
> 會改變 estimand 並加入未註冊 bias。

這份指南服務第一次閱讀的工程師，不是 runner、contract、lock 或 scientific report。
正式 authority 是
[S11／S12 fixed-frame measurement amendment](s11-s12-fixed-frame-measurement-amendment.md)，
數值與 checkpoint DAG 以
[experiment plan](../ductile-origami-warmstart-experiment-plan.md)為準。兩者衝突時，本指南
不能覆蓋 authority。

## 1. 先分開 planned、live 與 committed

- **Committed historical results：**S00 positive；S10 negative；S10R1 not evaluated；S10R2
  inconclusive；S10R3 negative；S10R4 retired／not evaluated。它們不能補造通往S11的edge。
- **Planned authority：**本次固定S11/S12 schedule、formulas與terminal matrix；尚未被
  experiment觀察。
- **Live workspace：**authority/design candidates與受保護的untracked S11 implementation
  candidates；它們不是committed authority、evidence或result。
- **Future scientific state：**S11 `not_started / not_evaluated`；S12
  `gated / not_evaluated`；沒有S11/S12 PASS、report、lock或edge。

Technical document validation只表示文字／公式同步，並不是scientific `PASS`。Scientific
outcome只有future runner產生complete evidence、fresh verifier判讀並完成durable closeout後
才能是positive、negative或inconclusive。

## 2. 核心名詞

### 2.1 Occurrence 與 unique identity

**Occurrence** 是 pinned sampler一個nominal slot通過`valid_fn`後產生的一次accepted raw
draw。它的角色是保存sampling mass；輸入是seed、chunk、slot與raw config，輸出是一筆有
occurrence ID的ledger row。相同config被接受兩次就是兩個occurrences。例如slot 17與slot
403都產生同一raw config，兩筆都要保留。Occurrence membership不表示compile、Formocast
或GPU成功。

**Unique identity** 是resolver、normal generation與compile後，consumer認為相同語意的
operational object。它把多個raw aliases deduplicate，讓runner只qualify／score一次，再把
結果fan out回所有occurrences。例如兩個raw configs被resolver正規化成同一stable semantic
identity，它們是兩個occurrences、但一個`Uexec` identity。Unique identity不是sample count，
也不是每個size各算一次。

### 2.2 `Fraw`、`Fexec`、`Fscore`

- **`Fraw`**：validator接受的raw occurrence multiset，位於population dedup之前。Runner
  產生它；execution-yield、conditional support與S12 full-raw denominator消費它。例：100筆
  accepted slots就是100個`Fraw` occurrences，即使只有80個distinct configs。它不證明
  resolver或compile成功。
- **`Fexec`**：`Fraw`中完成unique resolver projection、stable semantic identity、normal
  non-proxy KernelWriter generation及pinned compile的occurrence submultiset。Qualification
  producer與fresh verifier各做一次complete attempt；mapping/scoring與`Uexec` catalog消費
  結果。Normalized-away raw value仍可能屬於`Fexec`，但不能因此取得value-level trust。
- **`Fscore`**：`Fexec`中所有locked sizes都有finite native Formocast output與complete
  provenance的occurrence submultiset。S11 ECDF、benefit與model cells消費它。缺一size的
  identity仍留在`Fexec`，不是從raw denominator消失，也不能誤稱GPU performance失敗。

### 2.3 Global stream 與 conditional stream

**Global stream** 使用unconditional actual-YAML probabilities，產生整體 occurrence frame；
它的 `Fraw_global/Fexec_global/Fscore_global` 決定yield、coverage、global ECDF、`Uexec`與
future D5。**Conditional stream** 固定一個 `(gene,value)`，其他keys仍按nominal
probabilities抽樣；它只補該value cell的support與survivor statistics。

例：global stream自然抽到128筆`DepthU=256`，conditional stream另固定`DepthU=256`收256
筆。Cell analysis可使用兩者的multiset union，但conditional support仍只等於256；global
128筆不能冒充conditional support，conditional 256筆也不能進global D5。

### 2.4 Survivor estimand

**Survivor estimand** 是S11 model-only guidance實際估計的對象：只有已execution-qualified
且所有sizes可score的`Dscore_gv` occurrences進入benefit mean；`Dexec_gv`則是coverage
denominator。它回答「在可執行、可完整score的survivors中，value的model benefit方向如何」。
Analyzer產生cell statistics，guidance builder用它選`T_g`與probabilities。它不回答raw
population transport、acceptance yield、representativeness、GPU correctness或real
performance；S12用full-`Fraw` denominator另驗transport。

### 2.5 Familywise test

**Familywise test** 是同時保護「至少一個gene通過」這個family-level claim的permutation
gate。Design在看`S_g`前先凍結`Gtest`；每個replicate用一份shared-global occurrence
permutation，並對每個gene pool恰產生一份independently domain-separated conditional
permutation，再依該gene各value的fixed observed cell counts分配。禁止每conditional cell
各產生permutation。2,000 replicates各計`M_r=max_g S_gr*`。Verifier要求每個guided gene的
observed `S_g`同時嚴格超過自己的null P95和family max-null P95。它不表示統計上普遍顯著，
也不能把不在`Gtest`的gene補進來。

### 2.6 `rho_j`、`T_D5` 與 `M_HT`

**`rho_j`** 是D5 stratified without-replacement design對unique identity `j`的已知inclusion
probability，範圍 `(0,1]`。Sampler在labels前產生它；S12 analyzer用`1/rho_j`把sampled
identity的raw alias mass展開回finite frame。它不是arm probability，也不是real-quality
score。

**`T_D5`** 是exactly-256 D5 sample內的weighted real-high-quality identity set。Analyzer
以baseline weights `A_0j/rho_j`與all-size aggregate quality建立weighted empirical CDF；
cutoff是cumulative weight首次到0.90的最小observed quality，所有cutoff ties都入set。所有
arms、shuffle與oracle共用同一個materialized set。Membership表示這筆sample在sealed rule
下屬於high-quality set，不證明population top 10%或未來GA benefit。

**`M_HT`** 是design-based directional finite-frame raw-mass capture estimator。`HT`指
Horvitz–Thompson inverse-inclusion expansion：S12 analyzer把sampled aliases的arm density
ratio除以`rho_j`形成numerator，再除以known complete `Fraw_global` arm mass。它的目的不是
估一個bounded probability，而是用固定sample比較arm是否directionally把更多raw mass投向
`T_D5`。因此realized value可大於1，不能clip、winsorize或post-hoc normalize。

Stable estimator identity固定為
`S12-DIRECTIONAL-FINITE-FRAME-HT-EXACT-DENOMINATOR-v1`；S12、S31與S41用這個字串
辨識同一sample、`rho_j/T_D5/A_aj/N_HT/D_exact/M_HT`、tie、bootstrap及no-clipping
semantics。

### 2.7 Layer A／B／C

- **Layer A sealed scientific milestone**：exact commit／lock seal後控制authority、formal
  input、evidence或decision的bytes。Downstream contract依hash消費它；只能由authorized
  amendment／successor改變。本次文件在Main commit前還不是Layer A。
- **Layer B pre-seal candidate**：labels前仍可traceable revision的authority、design、
  contract或implementation候選。Main審核後才可seal；candidate存在不表示核准或結果。
- **Layer C operational bookkeeping**：resource forecast、routing、command summary、repair
  與live state。Operators用它排程並record＋notify；它不能改sample、measurement、outcome、
  claim或edge。五日／七日規劃屬Layer C，不是scientific stop。

### 2.8 Nominal draw

**Nominal draw** 是sealed PCG64 stream中的一個seed／chunk／slot嘗試，不論`valid_fn`是否
接受都消耗一個draw位置並計入finite cap。Sampler產生draw ledger；validator只把accepted
draw轉成`Fraw` occurrence。Rejected draw不是occurrence，但不能刪掉或重抽來逃避cap。

### 2.9 Terminal global mid-ECDF

**Terminal global mid-empirical cumulative distribution function（mid-ECDF）** 是在完整
terminal global `Fscore` occurrence multiset上、逐locked size一次建立的weighted empirical
reference；tie mass以`W_< + 0.5 W_=`定位。S11 analyzer產生它；global與conditional rows都
query同一reference，conditional rows不能重建或改變它。它的next consumer是benefit與cell
statistics，而不是terminal outcome本身。

### 2.10 Complete qualification attempt

**Complete qualification attempt** 是一位qualification actor對一個deduplicated semantic
identity，使用完整pinned resolver、normal non-proxy KernelWriter與toolchain，保存全部input、
steps、terminal status、provenance及association後的一次terminal execution。每identity恰有
producer與fresh verifier各一次。Matching attempts只允許輸出：(a)同一qualified executable
identity，交給native Formocast scorer；或(b)同一complete ordinary rejection，交給attrition
ledger與terminal verifier。Partial、discordant、association-lost、ambient-invalidated或guessed
輸出只能交給fresh verifier作`CHANGES_REQUIRED / not_evaluated`，不能交給scorer。Mapping
allowlist為`empty-v1`、`entries: []`，所以沒有mapping scientific output可達；新增例外必須先
有新的pre-evidence authority。

### 2.11 Block bootstrap

**Block bootstrap** 的resampling object是global occurrence連同其全部sizes，以及conditional
cell occurrence blocks；同identity aliases／sizes／repeats在S12也保持同一stratum／identity
block。每個S11 replicate重建terminal global mid-ECDF、`Dexec/Dscore/n/Cscore`、`mu_gv`、
`S_g`、best／worst與directions；每個S12 replicate重建`t_D5/T_D5/A_aj/N_HT/D_exact/M_HT`、
contrasts、ESS與oracle gap。Analyzer輸出replicate distributions，fresh verifier消費half-width、
recurrence與frozen gates；它不是把observed ECDF或`T_D5`固定後只重算最後一個ratio。

## 3. Actor → action → input → output → next consumer

```mermaid
flowchart LR
  registry["Design author\nseal family / seeds / caps"]
  sampler["S11 sampler\nfresh nominal slots"]
  qualify["Producer + fresh verifier\n2 complete qualifications"]
  score["Native Formocast\nall locked sizes"]
  stats["S11 analyzer\nECDF / cells / resampling"]
  guide["Guidance builder\nT_g / p1 / shuffle"]
  d5["S12 sampler + analyzer\nD5 / T_D5 / M_HT"]
  verify["Fresh verifier\ncriterion / outcome / edge"]

  registry --> sampler --> qualify --> score --> stats --> guide --> d5 --> verify
```

Table role `actor_input_output_consumer`：

| Actor | Action | Input | Output | Next consumer |
| --- | --- | --- | --- | --- |
| Design author／Main | Seal family、seeds、caps與authority identity | Actual YAML、approved authority、pre-sealed machine authority | Effective S11 lock candidate／seal | S11 sampler與fresh verifier |
| S11 sampler | Consume nominal slots、validate、preserve multiplicity | Effective lock、global／conditional PCG64 streams | Draw ledger、`Fraw_global`、`Fraw_cond(g,v)` | Qualification producer／verifier |
| Qualification producer＋fresh verifier | Each perform one complete qualification attempt | Raw aliases、pinned resolver／writer／toolchain | Matching executable identity、matching ordinary attrition，或`CHANGES_REQUIRED` evidence | Formocast scorer、attrition ledger或terminal verifier |
| Native Formocast scorer | Score every locked size with provenance | `Uexec` qualified identities | `Fscore/Uscore`與unscored taxonomy | S11 analyzer |
| S11 analyzer／resampler | Build terminal mid-ECDF、cells、bootstrap與familywise null | Terminal global frame、conditional prefixes、score lineage | Full semantic tuple與model-test results | Guidance builder與fresh verifier |
| Guidance builder | Construct trusted set、probabilities與shuffle | Frozen `T_g`、tests、actual-YAML order | `p1`、weights、shuffle、canonical guidance hash | S12 sampler／lock consumer |
| S12 sampler／analyzer | Draw fixed D5、measure quality、reconstruct exact estimator | Immutable S11 guidance、`Uexec`、full global aliases | `T_D5`、`M_HT`、contrasts、oracle diagnostics | Fresh verifier |
| Fresh terminal verifier | Apply first-match matrix and frozen criteria | Complete evidence bundle、contract／lock identities | `not_evaluated`、inconclusive、negative或positive decision | Closeout／next authorized checkpoint |

逐步資料流是：

1. Design author → seal registry、seeds、512-slot chunks與caps → 輸入actual YAML與本authority
   → 輸出effective S11 lock → S11 sampler只按lock從draw 0開始。
2. S11 sampler → draw／validate並保留multiplicity → 輸入global／conditional PCG64 streams
   → 輸出`Fraw_global`與`Fraw_cond(g,v)` → qualification actors逐identity處理。
3. Producer＋fresh verifier → 各做一次complete ordinary qualification → 輸入raw aliases、
   pinned resolver／writer／toolchain → 輸出matching executable identity或attrition evidence
   → native Formocast scorer只接收`Uexec`。
4. Formocast scorer → 對每個locked size產生finite score → 輸入qualified identities → 輸出
   `Fscore`與unscored taxonomy → S11 analyzer建立global ECDF與value cells。
5. S11 analyzer → 重建benefit、bootstrap與familywise null → 輸入terminal 8,192 global frame
   和terminal conditional prefixes → 輸出trusted/guided decisions → guidance builder只在
   `T_g`上建立`q`、`p1`與shuffle。
6. S12 sampler／analyzer → 從global `Uexec`抽fixed 256、測real quality並重建`T_D5`／`M_HT`
   → 輸入immutable S11 guidance與full global aliases → 輸出D5 metrics／oracle diagnostics
   → fresh verifier按frozen D5 matrix判定；S12目前尚未執行。

## 4. Before／after checkpoint matrix

Table role `before_after_checkpoint`：

| Checkpoint／topic | Before active wording | After approved authority | 沒有改變 |
| --- | --- | --- | --- |
| S11 global | 4,096可因stability停止；8,192 accepted hard cap | first 4,096只read-only；固定first 8,192 inferential frame；65,536 chunks／33,554,432 draws finite cap | fresh seeds、multiplicity、label firewall |
| S11 conditional | 128 minimum，precision不足到256 | 每value固定512 chunks／262,144 draws，target first256；128只read-only；cap-terminal 128–255只測一次 | global不給support credit、no pooling |
| S11 multiplicity | own-null P95 | own-null P95加familywise max-null P95；同2,000 replicates、Type-7、strict ties | `S_g>=0.05`、bootstrap／entropy／direction／coverage |
| S12 prior metric | `M_a(T)`被描述成0–1 mass fraction | exact `M_HT` directional index，可>1、no clipping；prelabel `T_D5` rule | fixed256、no replacement、10+1 strata、ESS／coverage／correctness |
| S20／S31 time | 5／7工作日hard-stop prose | Layer-C record＋notify；只有material safety／availability／full-workload／evidence condition才pause | 不可縮H10、arms、seeds或two-cluster denominator |
| S41 comparator | self-normalized `M_a(T)` probability-like gap | mechanical inheritance of `M_HT`與directional-index gap | ridge model、split、finite-frame point-direction claim |

S00–S10R4 committed history沒有被改寫；S13、S20、S30、S31的scientific criteria與edges也
沒有因本amendment改變。

## 5. Schedule 與 acceptance-rate算例

Table role `finite_schedule`：

| Stream | Accepted frame | Read-only point | Nominal cap | Terminal shortage |
| --- | --- | --- | --- | --- |
| Global | canonical first8,192 | first4,096及兩固定halves | 65,536 chunks ×512 =33,554,432 draws | `<8,192` → inconclusive |
| 每個conditional `(g,v)` | canonical first256 | first128 | 512 chunks ×512 =262,144 draws | `<128` support-insufficient；128–255 terminal test once |

Historical S10R3只為規劃提供114 accepts／262,144 draws：

```text
p_plan = 114 / 262,144 = 57 / 131,072 ~= 0.00043487548828125
draws_for_8192 = 8,192 / p_plan = 1,073,741,824 / 57 ~= 18,837,575.85964912
chunks_for_8192 = draws_for_8192 / 512 = 2,097,152 / 57 ~= 36,792.14035087719
margin_chunks = 1.5 * chunks_for_8192 = 1,048,576 / 19 ~= 55,188.21052631579
global_cap_chunks = next_power_of_two(margin_chunks) = 65,536
global_cap_draws = 65,536 * 512 = 33,554,432
```

這不是預測S11一定會得到8,192 accepts；它只說明finite cap怎麼事前算出。若actual rate更低，
runner仍跑到完整cap，再依frozen matrix判inconclusive，不能換seed或縮frame。

## 6. Exact cells、benefit 與 tests

對cell `(g,v)`：

```text
Graw_gv   = {o in Fraw_global   : X_g(o)=v}
Gexec_gv  = {o in Fexec_global  : X_g(o)=v}
Gscore_gv = {o in Fscore_global : X_g(o)=v}
Draw_gv   = Graw_gv   multiset-union Fraw_cond(g,v)
Dexec_gv  = Gexec_gv  multiset-union Fexec_cond(g,v)
Dscore_gv = Gscore_gv multiset-union Fscore_cond(g,v)

support_gv    = |Fraw_cond(g,v)|
Cscore_occ_gv = |Dscore_gv| / |Dexec_gv|
n_gv          = |Dscore_gv|
sum_b_gv      = sum_{o in Dscore_gv} benefit(o)
global_mean_g = [sum_{o in Fscore_global} benefit(o)] / |Fscore_global|
```

對terminal global `Fscore`、locked size `s`：

```text
r_s(o) = [W_<(L_s(o)) + 0.5 * W_=(L_s(o))] / W
b_s(o) = 1 - r_s(o)
benefit(o) = sealed_actual_size_reducer({b_s(o) for every locked size s})
mu_gv = (sum_b_gv + 32 * global_mean_g) / (n_gv + 32)
S_g = max_{v in T_g}(mu_gv) - min_{v in T_g}(mu_gv)
```

Lower Formocast latency得到較小midrank `r_s`與較大benefit。Conditional rows查同一global
ECDF。Bootstrap以occurrence＋all-size block重抽；permutation family statistic是
`M_r=max_{g in Gtest}S_gr*`。每個replicate的conditional部分對每個gene pool恰用一份
independently domain-separated permutation，再按fixed observed cell counts配置給values。
2,000 replicate的P95用Hyndman–Fan Type 7：
`Q95=0.95*x_(1900)+0.05*x_(1901)`。Observed `S_g`必須嚴格大於own與family P95；tie fail。

Block bootstrap的fixed observed best-vs-worst contrast與recurrence是：

```text
Delta_gr* = mu_g,best,r* - mu_g,worst,r*
half_width_g = [Q_0.975({Delta_gr*}) - Q_0.025({Delta_gr*})] / 2
recurrence_g = (1 / 2,000) * sum_r I[(best_gr*, worst_gr*)=(best_g, worst_g)]
```

Required`half_width_g<=0.025`、`recurrence_g>=0.90`；`[0.80,0.90)`只是borderline。

兩個fixed halves必須exact比較完整semantic tuple：每value的`Dexec_gv`、`Dscore_gv`、
`n_gv`、`Cscore_occ_gv`、`mu_gv`；trust states／reasons、`T_g`、guided states／reasons；
以actual-YAML candidate order作best／worst tie-break後的best／worst；per-size directions；
每一項model-test result；own/familywise pass；同一positive global lambda；每gene guidance
probabilities；shuffle mapping；canonical guidance hash。

## 7. `M_HT` formula 與一個 `M_HT>1` toy example

Stable estimator identity是
`S12-DIRECTIONAL-FINITE-FRAME-HT-EXACT-DENOMINATOR-v1`。Exact S12 formula：

```text
r_a(o)   = pi_nominal,a(o) / pi_nominal,0(o)
A_aj     = sum_{o aliases j} r_a(o)
N_HT,a   = sum_{j in D5} [A_aj / rho_j] * I[j in T_D5]
D_exact,a = sum_{o in Fraw_global} r_a(o)
M_HT,a   = N_HT,a / D_exact,a
```

Toy finite frame不是project result。假設arm `a`的complete global raw mass
`D_exact,a=100`；D5抽到一個屬於`T_D5`的identity `j`，其raw aliases合計`A_aj=40`，
而sealed design給它`rho_j=0.25`。則：

```text
N_HT,a = (40 / 0.25) * 1 = 160
M_HT,a = 160 / 100 = 1.6
```

`1.6`不是「160% probability」。它是一次without-replacement sample的inverse-inclusion
expanded numerator除以known denominator；sample恰好包含高mass identity時，estimate可overshoot。
Clipping成1會把`160`偷偷改成`100`，使large-mass arms系統性向下偏，並破壞arms、bootstrap
與S41 comparator的同一estimand。正確做法是保留1.6、報uncertainty與support，而不是裁切。

`T_D5`在sample內用baseline weight `w_0j=A_0j/rho_j`：

```text
Q_D5(t) = [sum_j w_0j * I[quality_j <= t]] / sum_j w_0j
t_D5 = min{quality_j : Q_D5(quality_j) >= 0.90}
T_D5 = {j in D5 : quality_j >= t_D5}
```

All-size aggregate quality越大越好；cutoff ties全部進set。Stratum／identity bootstrap每次都
重建cutoff、set、`M_HT`、contrasts、ESS與oracle gap，不能固定observed `T_D5`。

## 8. S11／S12能與不能下的結論

S11 positive可以說：在固定global／conditional frame與executable-and-scoreable survivor
estimand中，至少一個完整residual gene建立了stable、familywise、label-blind guidance，
因此可沿`S1_GUIDANCE_LOCKED -> S12`測transport。

S11不能說：raw population有代表性、acceptance yield良好、Formocast real ranking正確、
GPU correctness通過、real performance改善、Gen0變好或production可用。

S12若通過，可以說：在fixed D5 design與complete global `Fraw` denominator下，ranking、
lift及directional `M_HT` comparisons達到pre-registered gates。它仍不能說actual Gen0、H10
persistence、held-out replication、general speedup或deployment value；這些分別屬S13、S20、
S31與未來工作。

Negative表示完整bounded procedure沒有建立對應criterion；inconclusive表示support、coverage、
precision、stability或catalog shortage仍可能改變結論。兩者都不能偷換成「模型沒用」。

## 9. 本次文件、禁止重用的history與下一個順序

本次同步12份implementation documents：

- 新增本指南與 `s11-s12-fixed-frame-measurement-amendment.md`；
- 更新 `../surrogate-dse-plan.md`、`../ductile-origami-warmstart-experiment-plan.md`、
  `../ductile-origami-warmstart-experiment-guide.md`、`README.md`；
- 更新 `s10r4-to-s11-experiment-plan-change-guide.md`、S11、S12、S20、S31、S41 designs。

另有兩份Main已pre-seal、document implementer不能修改的delivery candidates：

- `protocol/v1/s11-s12-fixed-frame-measurement-authority-contract.yaml`；
- `protocol/v1/locks/s11-s12-fixed-frame-measurement-authority-lock.yaml`。

Exact-path commit與post-commit audit成功後，artifact projection精確是11份Layer-A
authorities：`s11-s12-fixed-frame-measurement-amendment.md`、`../surrogate-dse-plan.md`、
`../ductile-origami-warmstart-experiment-plan.md`、`README.md`、
`s11-stage1-model-only-factorization-design.md`、
`s12-stage1-real-score-ranking-oracle-audit-design.md`、
`s20-stage2-h10-persistence-design.md`、`s31-stage3-bounded-replication-design.md`、
`s41-stage4-learned-residual-analysis-design.md`、
`protocol/v1/s11-s12-fixed-frame-measurement-authority-contract.yaml`與
`protocol/v1/locks/s11-s12-fixed-frame-measurement-authority-lock.yaml`。另精確有3份
postcommit non-authoritative Layer-B guides：`s11-s12-fixed-frame-measurement-change-guide.md`、
`../ductile-origami-warmstart-experiment-guide.md`與
`s10r4-to-s11-experiment-plan-change-guide.md`。這三份guides不升格為Layer A，也不能覆蓋
11份authorities。

不得重用S10R3 rows／seeds／support／mapping、S10R4 B01–B07 bytes、舊S11 draft contract／
runner/package/schema、舊4,096 early-look decisions或舊bounded `M_a(T)` interpretation。

下一個合法順序是：

1. Main只stage exact14-path delivery set，完成fresh staged audit、isolated authority commit與
   post-commit audit；
2. 依committed authority重新對齊S11 runner、schema與machine contract；
3. fresh adversarial parity與implementation verification通過後seal effective S11 lock；
4. 證明S11 outcome／label artifacts仍absent，再從fresh global／conditional draw 0執行S11；
5. 只有S11 verified positive edge存在，S12才可另行plan、seal與執行。

目前停在第1步之前；沒有S11 process、result、lock、report或scientific edge。
