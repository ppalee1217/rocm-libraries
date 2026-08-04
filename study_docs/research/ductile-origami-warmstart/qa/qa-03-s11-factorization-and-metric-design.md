# QA-03 — S11 factorization 與 metric

> **文件角色：**這是從 [實驗白話導讀 hub](../../ductile-origami-warmstart-experiment-guide.md) 拆分出來的白話導讀主題檔，方便在單一主題上持續討論。它不是 experiment authority，也不是 contract、lock 或 report，不會取代正式的 charter、experiment plan、checkpoint design、lock 或 report。
>
> **衝突處理：**若本檔與正式文件衝突，以 [research charter](../../surrogate-dse-plan.md)、[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)、[active checkpoint index](../README.md) 及各 checkpoint design 為準。
>
> **2026-08-04 current status override：**S10R3 已 terminal negative；S10R4 已 retired／not evaluated；S11 已 sealed `LOCKED_READY`。沒有 S11/S12 result、effective checkpoint lock、report 或 edge；最新狀態仍須對照 active checkpoint index、formal artifacts 與 Git history。

> **S11 current note：**本檔頂部「Current S11 mechanism」段反映 sealed `LOCKED_READY`（2026-08-04）的 CURRENT design，比下方由舊 §8 遷入的 8,192-frame 敘述新；兩者衝突時以 current 段與正式 s11 design／authority contract 為準。

---

## 0. Current S11 mechanism（as sealed `LOCKED_READY`, 2026-08-04）

本段依 sealed S11 實作程式碼（`protocol/v1/s11/` 與 native adapter）整理，是目前的 CURRENT
機制；下方 §8 是由舊導讀遷入的較早敘述，兩者衝突時以本段與正式
[S11 design](../s11-stage1-model-only-factorization-design.md) 及 authority contract 為準。

### 0.1 Formocast 實際怎麼跑模擬

Formocast 不是經驗公式、也不是 ML 模型，而是 `origami` 內的 physics/analytical simulator。
每次評分：

- 輸入一個 `ProblemInfo`（矩陣 M／N／NumBatches／K、`dataType=BFloat16`、`gfx942`）；
- 輸入一個 `SizeMapping`（一整組 kernel 參數：macroTile、matrixInstruction、depthU、
  globalSplitU、grvwA/B… 約 35 個欄位）；
- 呼叫 `origami::Formocast::predictedPerformance()`，取 `microSeconds`（預測延遲，越低越好）。

它對 **3 個 locked size** 各跑一次；任何一個回傳非有限或 ≤0 就報錯（不容許 proxy 公式）。
實作見 [native adapter](../protocol/v1/s11/native_formocast_runtime_adapter.cpp)。

### 0.2 Fscore 分數怎麼來，以及 factorization 到底怎麼做

**分數不是直接用 Formocast 原始延遲。** 不同 size 延遲差幾個數量級，直接平均會被大數字
淹沒，所以做 **mid-ECDF rank** 轉換（見 §0.6）：對每個 size 把這筆 occurrence 的延遲和整個
族群比，得 `percentile`，`size_benefit = 1 - percentile`；一筆 occurrence 有 3 個
size_benefit，用 pinned 的 `max` reducer 取一個，就是它的 `benefit`（0~1，越高越好）。

**factorization 不是「固定其他參數」，而是 marginal（邊際）聚合。** 要評「gene `g` = 值 `v`」
時，把**所有「g 剛好等於 v」的完整 config**撈出來（其他參數是隨機變動的），取它們 benefit
的（帶 shrinkage 的）平均：

```text
mu_gv = (sum_b_gv + 32 * global_mean_g) / (n_gv + 32)
```

也就是「在其他參數隨機的情況下，g=v 這些 config 的平均 benefit」。這正是它的 bias 來源：若
v 常和「其他好參數」共現，`mu_gv` 會把別人的功勞算在 v 頭上（confounding）——所以才有 §0.7
的診斷。實作見 [populations.py `value_cell`](../protocol/v1/s11/populations.py) 與
[statistics.py `gene_marginals`](../protocol/v1/s11/statistics.py)。

### 0.3 execution attrition 是什麼

一筆被 sampler 抽中、通過 validator 的 config 進 `Fraw`；要能評分還得通過
resolver + KernelWriter 產生 kernel + `amdclang++` 編譯，成功才進 `Fexec`。中間卡掉的就是
**execution attrition（執行流失）**。處理方式：流失的 occurrence **仍留在 `Fraw`**（分母），
不進 `Fexec`；比例記為 `Y_exec = |Fexec|/|Fraw|`，只回報、**不 gate**；且**絕不**被當成
「Formocast 沒訊號（model missingness）」——工程流失與模型缺值嚴格分開。三層漏斗見
[populations.py `build_populations`](../protocol/v1/s11/populations.py)。

### 0.4 residual gene / conditional value / global

- **residual gene**：扣掉既有 grouped/weighted guidance 後、ungrouped、目前 unweighted、
  候選值 >1 的自由參數，才是 S11 有資格引導的。registry 確認 **27** 個 eligible residual gene。
- **candidate / conditional value**：一個 gene 的一個取值；針對「某 gene 的某值」開的專屬
  抽樣流會把該 gene 釘死、其他隨機抽，確保該值有足夠樣本。registry 確認 **101** 個 conditional stream。
- **global**：所有 gene 按 baseline 機率隨機抽的主流，提供整體 ECDF 基準與自然分布樣本。

### 0.5 抽樣數量／內容怎麼決定，會不會 bias

- global：抽到 **8,192 accepts**（硬上限 65,536 chunks × 512 = 33,554,432 draws）。
- 每個 conditional value：抽到 **256 accepts**（≈262,144 draws）；至少 128 才算 support 足夠。
- 這些是**先驗鎖定**（pre-registered）的，不是看結果才調，避免「看到數字才改門檻」。
- 分 global／conditional 的用意：global 自然偏向常被抽的值，罕見值樣本太少；conditional 專門補。
- 抽樣本身用固定 seed 的 PCG64 ＋ baseline `p0`（`rng.choice(..., p=baseline_probabilities)`），
  **決定性可重播**。真正的 bias 風險在**估計端**（marginal 的 confounding／survivorship），由 §0.7 偵測；
  label firewall 保證抽樣/評分完全不看真實 GFLOPS。見 [sampling.py](../protocol/v1/s11/sampling.py)。

### 0.6 mid-ECDF 是什麼，以及 metric 有哪些（AND-gate，非加權總分）

**mid-ECDF**：對某 size，`percentile = (比它小的個數 + 0.5×和它相等的個數) / 總數`
（「+0.5×相等」= mid，平手取中點排名），`benefit = 1 - percentile`。它是「贏過族群多少比例」
的**相對排名**，不是「快幾 %」。conditional 的 occurrence 拿去和**同一個 terminal global
ECDF** 比，基準一致。實作見 [statistics.py `_midranks` / `midrank_latency_benefits`](../protocol/v1/s11/statistics.py)。

一個 gene 要能引導，必須**每一項都通過**（不是加權平均）：

| Metric | 意義 | 門檻 |
|---|---|---|
| `support_gv` | 該值 conditional 樣本數 | ≥128 |
| `Cscore_occ_gv` | 該值可評分覆蓋率 | ≥0.95 |
| `S_g`（sensitivity） | gene 內 best 與 worst 值的 `mu` 差 | ≥0.05 |
| permutation test | 隨機重排後 `S_g` 是否仍這麼大（own-null + familywise） | 觀測值 strict > 隨機 P95（2000 次） |
| bootstrap stability | best/worst 排名穩不穩 | CI half-width ≤0.025 **且** recurrence ≥0.90（2000 次） |
| size direction | 3 個 size 方向是否一致 | ≥2/3 |
| entropy floor | 引導後分布不塌成獨尊一值 | normalized entropy ≥0.80 |

全過 → 算 `q = softmax over trusted values`，混成 `p1 = 0.20·p0 + 0.80·q`；`lambda`（0~8、
step 0.25）取「所有 guided gene 都仍滿足 entropy≥0.80 的最大值」。見
[guidance.py](../protocol/v1/s11/guidance.py)。

### 0.7 平衡 mu_gv 偏差的參數與三個診斷

參數**固定且 pre-registered**（寫死在 contract，封在 effective lock）：`alpha=32`、
`epsilon=0.20`、`lambda ∈ {0,0.25,…,8}`、entropy floor `0.80`、`S_g≥0.05`、bootstrap/
permutation `2000` 次、`ARM_SENSITIVITY_ESS_MIN_FRACTION=0.05`。三個診斷（**只報告、不 gate**、label-blind）：

- **shrinkage `alpha=0` 敏感度**：`mu_gv` 的 `32·global_mean` 收縮項在樣本少時會把估計拉向
  全域平均。此診斷再算一次不收縮版本（`Σbenefit/n`），看該 gene 的 guided/best-worst/lambda
  決策**會不會翻轉**；翻轉 = 這決策是被 shrinkage 撐出來的、不穩。
- **additivity / reconstruction（效度）**：交叉驗證「把各 gene 邊際加回去能不能還原 Formocast
  對整組的排名」；低 = 訊號主要在交互作用裡，拆成邊際會失真。
- **arm-sensitivity / survivorship / per-size margin**：分別偵測 confounding（不同抽樣分布下
  best/worst 是否變）、倖存者偏差（`Y_exec_gv`）、以及提醒延遲差是 Formocast model 量、非實測。

### 0.8 OPTION_C shrinkage gate 與七個正式階段

「alpha=0 敏感度」原本只報告；要不要升成關卡有爭議，使用者選擇用 **decision-loss simulation**
裁決：用**已知正確答案**的合成資料比較 alpha=32 vs alpha=0 誰的決策錯得少。faithful 實作
（用真實 selection path、estimator-independent 真值）在預設 panel 得 **OPTION_C** →
**若一個 gene 的決策在去掉 shrinkage 後會翻轉，就不准供正向 edge；若全部翻轉，整個 S11 判
`FT-INCONCLUSIVE`**。這是唯一動到科學判定矩陣的地方。

七個正式階段（每階段只讀前一階段封好的產物、寫自己那份，都要先過 `admit_formal_command`）：

| 階段 | 目的 | 交接產物 |
|---|---|---|
| global-discovery | 主抽樣到 8,192 accepts，建 global ECDF 原料 | `s11-global-prefix.json` |
| conditional-discovery | 101 個 stream 各釘死抽到 256 accepts | `s11-conditional-prefixes.json` |
| qualify | resolver + KernelWriter + `amdclang++` 編譯（定 `Fexec`，execution attrition） | `s11-qualifications.json` |
| score | 對 executable 身分的 3 size 呼叫 native Formocast（定 `Fscore`） | `s11-native-scores.json` |
| analyze | 算 benefit/`mu_gv`、跑所有 model tests、算診斷、建 `p1`、套 OPTION_C gate | `s11-analysis.json` + `s11-guidance.json` |
| decide | 套 first-match terminal matrix：positive `S1_GUIDANCE_LOCKED` / `FT-INCONCLUSIVE` / no-guidance | `s11-decision.json` |
| reproduce | 兩個 fixed half 獨立重建，檢查 §6.4 categorical decision projection 一致 | `s11-reproduction.json` |

---

## 8. S11：Factorization 與 guidance lock

> **HISTORICAL note：**以下 §8 是舊導讀敘述，保留作背景；current 機制以上方 §0 為準。

S11 是真正執行 factorization 的 checkpoint。

### 8.1 Global valid-occurrence frame

- 固定canonical first 8,192 accepted occurrences作inferential frame；
- duplicate occurrences 保留；
- first4,096與固定兩個4,096 halves只read-only，不能停止或emit outcome；
- atomic chunk固定512 nominal slots；cap是65,536 chunks／33,554,432 draws；
- dedup 只用來減少 mapping/Formocast 重算，analysis 時恢復 multiplicity。

Planning只使用historical`114 / 262,144` acceptance rate：

```text
p_plan = 114 / 262,144 = 57 / 131,072 ~= 0.00043487548828125
draws_for_8192 = 8,192 / p_plan = 1,073,741,824 / 57 ~= 18,837,575.85964912
chunks_for_8192 = draws_for_8192 / 512 = 2,097,152 / 57 ~= 36,792.14035087719
margin_chunks = 1.5 * chunks_for_8192 = 1,048,576 / 19 ~= 55,188.21052631579
global_cap_chunks = next_power_of_two(margin_chunks) = 65,536
global_cap_draws = 65,536 * 512 = 33,554,432
```

Cap時少於8,192 accepts是inconclusive，不能reseed或extension。Historical rows只作planning，
不進S11 evidence。

### 8.2 Conditional top-up

對每個 eligible `(gene, value)`：

- 固定該 value；
- 其他 keys 按 nominal probabilities 抽；
- 通過同一 valid_fn；
- 固定512 chunks／262,144 nominal draws；
- target canonical first256 accepted；
- 128只read-only；cap-terminal 128–255 prefix只測一次；
- 少於128是support-insufficient；不能pool global rows、reseed或extension。

Global與conditional exact cell是：

```text
Graw_gv   = {o in Fraw_global   : X_g(o)=v}
Gexec_gv  = {o in Fexec_global  : X_g(o)=v}
Gscore_gv = {o in Fscore_global : X_g(o)=v}
Draw_gv   = Graw_gv   multiset-union Fraw_cond(g,v)
Dexec_gv  = Gexec_gv  multiset-union Fexec_cond(g,v)
Dscore_gv = Gscore_gv multiset-union Fscore_cond(g,v)

support_gv = |Fraw_cond(g,v)|
Cscore_occ_gv = |Dscore_gv| / |Dexec_gv|
n_gv = |Dscore_gv|
sum_b_gv = sum_{o in Dscore_gv} benefit(o)
global_mean_g = [sum_{o in Fscore_global} benefit(o)] / |Fscore_global|
```

Global rows不給conditional support credit；conditional rows不進global yield、coverage、ECDF、
`Uexec`或future D5。

### 8.3 Model benefit

對terminal global `Fscore`每個locked size，以occurrence-weighted latency mid-ECDF轉成
benefit。Lower latency較好：

```text
r_s(o) = [W_<(L_s(o)) + 0.5 * W_=(L_s(o))] / W
b_s(o) = 1 - r_s(o)
benefit(o) = sealed_actual_size_reducer({b_s(o) for every locked size s})
```

Conditional rowsquery同一global ECDF；all sizes of one occurrence是一個analysis block。

### 8.4 Shrinkage conditional mean

概念公式：

```text
mu_gv = (sum_b_gv + 32 * global_mean_g) / (n_gv + 32)
S_g = max_{v in T_g}(mu_gv) - min_{v in T_g}(mu_gv)
```

Shrinkage 避免小樣本 value 因偶然高分得到極端權重。

### 8.5 Gene eligibility

一個 gene 要接受 guidance，需同時滿足：

- 每 value support ≥128；
- model coverage ≥95%；
- sensitivity `S_g ≥ 0.05`；
- 2,000 次permutations；每replicate有一份shared-global occurrence permutation，conditional
  部分則每gene pool恰有一份independently domain-separated permutation，再依該gene各value
  的fixed observed cell counts分配；observed `S_g` strict勝own-null與familywise max-null
  Type-7 P95；ties fail；禁止per-conditional-cell permutation；
- 2,000 次 bootstrap 半寬 ≤0.025；
- best/worst pair 重現率 ≥90%；
- 至少 2/3 sizes 方向一致。

Family statistic是`M_r=max_{g in Gtest}S_gr*`；2,000 replicates的Type-7 P95是
`0.95*x_(1900)+0.05*x_(1901)`。兩個固定halves各自重建global reference並exact比較完整
semantic tuple：每value的`Dexec_gv/Dscore_gv/n_gv/Cscore_occ_gv/mu_gv`、trust與guided
states／reasons、`T_g`、actual-YAML-order best／worst tie-break及best／worst、per-size
directions、每一項model-test result、own/familywise pass、同一positive global lambda、每gene
guidance probabilities、shuffle mapping及canonical guidance hash。它們不是independent
replication。

### 8.6 Probability construction

```text
epsilon = 0.20
alpha = 32
```

最終 probability 可理解成：

```text
20% uniform exploration
+ 80% Formocast preference
```

所有 guided genes 共用 global lambda，且 normalized entropy 必須 ≥0.80。

### 8.7 轉回 Ductile weights

研究先產生想要的 probability：

```text
p_g(v)
```

再轉成 Ductile 可接受的 cost weight：

```text
w_g(v) = -log(p_g(v)) / weight_beta
```

經 Ductile 自己的 weight→probability conversion 後，必須 round-trip 回原本的 probability。

---

