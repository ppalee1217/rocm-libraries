# S14 per-shape — **tiny** `(8,8,1,128)` 7× interleaved remeasure 分析（意外的 null control）

> **狀態：MEASURED 5/5（capped campaign，`DUCTILE_FORCE_P0=1`，`pop_size=512`）。Quarantined 分析。
> Two-sided；不預設任何結論。** 本檔是 staged checkpoint 分析，**不是 authority
> document**。若與 research charter、experiment plan 或
> `s14-stage1-full-ga-outcome-design.md` 衝突，一律以後者為準。本檔內容未寫入
> `report-source-index.md`、其 zh-Hant mirror、S14 design、charter、qa 檔或
> `protocol/`；authority doc 可能需要的項目集中於 **§7（for main session）**。
>
> **tiny 為 `探索性` / exploratory only**（S14 design §10.2：*"tiny `(8,8,1,128)` = 探索性(僅描述,排除於
> confirmatory gate)"*；§10.4：*"combined 措辭需 medium ∧ large 都過各自 gate … tiny 探索性(無 gate)"*）。
> **本檔任何內容都不能對 confirmatory gate 有任何方向的貢獻。** 之所以仍要報告，是因為 tiny 結果顯示它其實是
> 一個 *null control*，這是另一個、也更有用的角色。
>
> **Anti-fabrication。** 每個數字後面都附來源路徑。未量測的量一律標 `NOT_EVALUATED`；
> `NOT_EVALUATED ≠ no effect`。
>
> **Run root（host）：** `/data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-baseline`
> （container `/src/rocm-libraries/agent_run/260809-s14-pershape-baseline`）。除另有說明外，相對路徑皆以該
> root 為基準。`G` = Arm G = BASELINE，`F` = Arm F = GUIDED，`+ve % = guided faster`。
>
> **Scope note。** tiny **未**納入 native-Gen0 11,405 addendum
> （`stage5_native_{baseline,guided}/seed_24001/` 只含 `large/` 與 `medium/`；
> S14 design 第 298 行：*"(C) tiny 仍排除"*）。因此 tiny **只有** capped（P0=512）campaign，
> 不存在 native-P0 交叉核對 —— 這是 `NOT_EVALUATED`，不是「no effect」。

---

## 1. Null-control 主張，在任何推論建立於其上之前先行驗證

本節的科學價值完全繫於一個主張：**在 tiny 上，Arm F 與 Arm G 是從相同分布抽 Gen0，因此真實 treatment
effect 依構造恰為零。** 我們檢查了四份獨立的 sealed artifact。四份彼此一致，而且其中一份比主張所需的還要強。

### 1.1 `[CODE AUDIT]` guidance 導出過程沒有啟動任何東西

*來源：`agent_run/260809-s14-pershape-guidance/derivation/derivation-manifest-capped.json`
→ `per_shape_activation_log.tiny`。*

| field | value |
|---|---|
| `shape_role` | `exploratory` |
| `activated` | `false` |
| `n_genes_activated` | **0** |
| `n_genes_fallback` | **27**（全部 free genes） |
| `lambda_s` / `global_lambda` | `"na"` / `"na"` |
| 每個 gene 的 `sensitivity` | `0.0` |
| 每個 gene 的 `fallback_reason` | `sensitivity_below_0_05` |
| 每個 gene 的 `rho` | `0.0` |
| 每個 gene 的 `TV_p1_vs_p0` / `KL_p1_p0` | `0.0` / `0.0` |
| 每個 gene 的 `normalized_entropy_p0` / `_p1` | `1.0` / `1.0` |
| 每個 gene 的 `best` 與 `worst` value hash | **完全相同的字串** |

逐 gene 的 `best == worst` 正是 §3.6.2 那個機制的算術指紋：Formocast 對 100 % 的 tiny config 都回傳
sentinel `9,999,999.9`（`30,490 / 30,490`，直接由
`protocol/v1/manifests/s11-native-scores.json` 量得 —— 見
`reports/staged/s11-stage1-model-only-factorization-report.md:501`），因此 midECDF 給每個 config 相同的
benefit、每個 per-value marginal 都相同、27 個 free gene 的 `S_g = 0.0000`。沒有任何 gene 通過 activation
gate `(a) ≥2 trusted values ∧ (b) S_g ≥ 0.05 ∧ (c) per-shape direction positive`。

### 1.2 `[CODE AUDIT]` weights 檔是均勻的 —— 沒有任何 gene 被引導

*來源：`agent_run/260809-s14-pershape-guidance/out-capped/ga-weights-tiny.json`。*

- `activated: false`；`lambda_s: "na"`；`weight_beta: 0.25`。
- `weights_source_per_gene` 對 **全部 27** 個 gene 都是 `"p0"`（medium 有 2 個是 `"p1"`，large 有 5 個）。
- `rho_per_gene` 對 **全部 27** 個 gene 都是 `0.0`。
- `weights` → **每個 per-gene weight vector 都是常數。** 逐值重算：`DepthU` 是
  `[7.167037964] × 6`，`1LDSBuffer` 是 `[2.77258873] × 2`，`WorkGroupMapping` 是 `[11.561487198] × 18`，
  其餘 27 個依此類推。這些恰好是 `w(v) = −log(1/|V_g|)/β`（`β = 0.25`）—— 也就是把 **uniform** 的
  `p0` prior 表達成 Ductile 的 inverse-cost weight 單位（§3.4b.2）。常數 weight vector 在資訊上等同於
  沒有 weight vector。

> **關於 brief 預期的精確說明。** brief 預期 `ga-weights-tiny.json` 會 *"carry
> only `group_0`"*。事實並非如此 —— 它帶了全部 27 個 free gene，皆為 uniform `p0`。「only `group_0`」這個
> 性質屬於 **被注入的 GA config**，不是這個檔案（§1.3）。`report-source-index.md` §6
> （"Activated genes: … tiny=none"）照字面是正確的；這裡是澄清，不是反駁。

### 1.3 `[CODE AUDIT]` 兩臂的 GA config **byte-identical** —— 這比主張本身更強

*來源：`config/s14-pershape-tiny-seed_2400{1..5}.yaml`（Arm G）與
`config/s14-pershape-guided-tiny-seed_2400{1..5}.yaml`（Arm F）。*

| seed | sha256（兩臂相同） |
|---|---|
| 24001 | `09b11a3b51259a6a3826b4f044309d90d59f4ca3249c144b2c776f52f57880eb` |
| 24002 | `8771d87b0dd5477e306deeed0d0a10196d880b48348efae26d8d2024ffcde55e` |
| 24003 | `7c438b4c68fed34ca4bc64545580a1559072b0cfa6fd1caa0a36a8a7422d99e6` |
| 24004 | `fbfa3ebd1ca53a887ef4b74c1beab3dd93728bd6e128997d56a97ba4be9e6676` |
| 24005 | `0c13a7c811f42659c39274f45acd5aaffc487b36c650e7a0dc3c2d9e7b058466` |

五對檔案的 `diff` 皆為空。`Backend.Config.weights` 在兩臂中都**恰好只有一個 entry，`group_0`**，也就是
§3.7 記載為 *"identical in both arms, never touched"* 的那個 GEKO-weighted MatrixInstruction/WorkGroup
區塊。`pop_size: 512`、`n_gen: 30`、`max_iters: 437`、`period: 5`、`seed: <the seed>` —— 全部相同。

作為對照，同樣的 `diff` 在受 treatment 的 shape 上會回傳真實差異：medium 的 guided YAML 追加了一個
`DepthU` + `1LDSBuffer` weight 區塊（新增 10 行），large 的則追加 `PrefetchGlobalRead`、
`TransposeLDS`、`UnrollLoopSwapGlobalReadOrder`、`GlobalReadVectorWidthA/B`（新增 29 行）。

**所以在 tiny 上，「F 與 G 從相同分布抽 Gen0」其實還說輕了：兩臂消耗的是字面上完全相同的檔案內容，且用同一個
GA seed。** 在 S14 §10.2 的 RNG pin（*"配對臂共用同一組
Gen0 uniforms、經 `p0` 或 `p1` 映射(只差先驗)"* —— 配對臂共用一組 Gen0 uniforms，再經
`p0` 或 `p1` 映射）之下，相同的 uniforms + 相同的 prior ⇒ **相同的 Gen0 母體**，而不只是同分布而已。

### 1.4 `[GUIDED GPU]` 建構期與執行期的佐證

*來源：`stage3_guided/seed_{24001..24005}/tiny/ga_init_evidence.json`；
`stage3_{baseline,guided}/seed_*/tiny/trajectory.jsonl`（`gen == 1` 的列）。*

五個 guided seed 都記錄了 `weights_gene_keys: ["group_0"]`、`sampling_prob_genes: ["group_0"]`、
`weights_sha256: 56c34446385e9313…`（跨 seed 相同）、`pop_size_at_construction: 512`。Arm G 早於
`ga_init_evidence.json` 這項 instrumentation，沒有對應檔案 —— 由 §1.3 的 byte-identity 來涵蓋。

Gen0 的列則從經驗上佐證了母體同一性：

| seed | Gen0 best-config hash G == F | Gen0 valid/512 (G / F) | Gen0 median-Q (G / F) | Gen0 best GFLOP/s (G / F) | Gen0 F/G |
|---|:--:|---|---|---|---:|
| 24001 | **YES** (`167dca0a…`) | 313 / 313 | 1.723722 / 1.733140 | 2.89087 / 2.88921 | 0.99943 |
| 24002 | **YES** | 321 / 321 | 1.668768 / 1.663807 | 2.80885 / 2.80201 | 0.99757 |
| 24003 | no | 289 / 289 | 1.698992 / 1.679690 | 2.92836 / 3.08467 | 1.05338 |
| 24004 | **YES** | 273 / 273 | 1.762965 / 1.743955 | 3.04423 / 3.04557 | 1.00044 |
| 24005 | **YES** | 308 / 308 | 1.681566 / 1.658752 | 2.89055 / 2.90379 | 1.00458 |

`generation_any_valid_count` —— 512 個 Gen0 個體中通過 KernelWriter/assembly build 並完成 benchmark 的
數量 —— 在五個 seed 中**兩臂皆完全相等**（313、321、289、273、308）。
該計數是抽出母體的決定性性質；在 512 候選的抽樣上出現五次精確一致，不是兩個不同分布能碰巧達成的。

**唯一的例外 seed 24003 是被解釋，而不是被辯護掉的。** Gen0 的 *best* 不同，但 valid count 相同。
Gen0 的 `best_hash_so_far` 是對*同樣*那 289 個候選、289 次帶噪音的單次 GPU 量測取 `argmax`。兩個接近平手的
候選加上一次帶噪音的抽樣就會翻轉 `argmax`；F 臂的 Gen0 best 量到高 5.3 %。這是驅動整個結果的機制
（§5.1）第一次現身：**在 tiny 上，selection 是由量測噪音決定的。** 這不是 Gen0 分布不同的證據。

> **判定：null-control 主張成立。** 在 tiny 上，沒有任何會影響 Gen0 抽樣的東西在兩臂間有差異。
> 底下量到的任何 F/G 差異，其**真值已知恰為零**。
> 本研究中沒有其他 shape 能這樣說。

---

## 2. 結果

以 `gap_large.py` 的邏輯（per-seed 表、median 列、標記為誤導的 mean-of-raw-ratios 列）與
`analyze_large.py`（directional-consistency 各分量）計算，因此數字的產生方式與 medium、large 相同。
釘死的常數：**η_tiny = 0.4466**（`0.44659979255188964`）、
**δ_tiny = 0.5630**（`0.5629886544000939`）、**R_s = 0.751728**、size **(8, 8, 1, 128)**。

*來源：`stage3_baseline/seed_{24001..24005}/tiny/champion_interleaved.json` →
`median_gflops.{G,F}`、`F_over_G_median_ratio`、`F_over_G_median_log_ratio`、`eta_s`、`delta_s`、
`nonregression_floor`、`F_median_ge_G_median_times_exp_neg_eta_s`、`F_over_G_gt_one_plus_delta_s`。*

### 2.1 Final-champion 7×-median 真實 GFLOPS（§7.1 / §7.2 格式）

| seed | G median (GFLOP/s) | F median (GFLOP/s) | **F/G ratio** | **% change** | log-ratio `ln(F/G)` | card |
|---|---:|---:|---:|---:|---:|---|
| 24001 | 4.13644 | 3.65146 | 0.8828 | **−11.72 %** | −0.12471 | hip2 |
| 24002 | 3.83508 | 3.96923 | 1.0350 | +3.50 % | +0.03438 | hip3 |
| 24003 | 3.99704 | 3.53391 | 0.8841 | **−11.59 %** | −0.12315 | hip4 |
| 24004 | 3.80317 | 3.78539 | 0.9953 | −0.47 % | −0.00469 | hip7 |
| 24005 | 3.79733 | 3.67943 | 0.9690 | −3.10 % | −0.03154 | hip6 |
| **median** | 3.83508 | 3.67943 | **0.9690** | **−3.10 %** | **−0.03154** | — |
| *(mean of raw ratios — **誤導**，見 §5b)* | *3.91381* | *3.72388* | *0.9532* | *−4.68 %* | *(geo-mean 0.9513, −4.87 %)* | — |

- **1/5 為正；median −3.10 %。** 在預先登記的 ≥4/5 門檻下，final-champion 分量會不通過 —— 但 tiny 沒有
  gate，而且更重要的是 **真實效應為零**，所以「1/5」量到的是這套機器在 n=5 下的方向性偏差，不是 treatment。
- Raw-ratio 跨度 **0.8828 … 1.0350**（1.17× 的散布）；`max |ln(F/G)| = 0.1247`；`sd(ln(F/G)) = 0.0715`。
- n=5 的精確雙尾符號檢定：1/5 ⇒ **p = 0.375**。在 n=5 下 *沒有任何* 分割能達到 p < 0.05；最極端的
  5/5 或 0/5 給出 p = 0.0625。power 依構造就不高，而這也不是顯著性檢定。
- 五個 seed 的 interleave 起始臂都是 `G`（`START_ARM[tiny] = G`，即 `report-source-index.md` §8.4 記載的
  決定性 per-shape counterbalance）。各 seed 的 card 為該 seed 的 Lock-A search
  card（hip 2/3/4/6/7）；GPU 5 從未用於 tiny 的 Lock-A remeasure，GPU 0 則完全未使用。五次 remeasure 都
  記錄 `status: PASS`、`exit_code: 0`、`verified_gpu_uuid` 與
  `lock_a_expected_gpu_uuid` 相符（`champion_interleaved_status.json`）。

### 2.2 Directional-consistency 各分量

| component | positive seeds | 判定（僅供參考 —— tiny 無 gate） |
|---|---:|---|
| Gen0 best | 3/5 | 低於 4/5 |
| gen-10 best | 2/5 | 低於 4/5 |
| AUC (best-so-far, common eval budget) | 2/5 | 低於 4/5 |
| final champion (7× median) | 1/5 | 低於 4/5 |
| final **non-regression** `F ≥ G·e^{−η_s}` | **5/5** 在釘死的 η = 0.4466 下；**2/5** 在 tiny 自身的經驗重複性下 —— 見 §3.4 | **取決於 margin** |
| final **improvement** `F > G·(1+δ_s)` | **0/5** 在釘死的 δ = 0.5630 下；1/5 在經驗 δ = 0.01457 下 | — |

各 seed 明細（`analyze_large.py` 版面）：

| seed | Gen0 G / F | d | gen-10 G / F | d | AUC F/G | d | final F/G | d |
|---|---|:--:|---|:--:|---:|:--:|---:|:--:|
| 24001 | 2.89087 / 2.88921 | − | 4.12421 / 3.58207 | − | 0.8967 | − | 0.8828 | − |
| 24002 | 2.80885 / 2.80201 | − | 3.64123 / 3.64811 | + | 0.9835 | − | 1.0350 | + |
| 24003 | 2.92836 / 3.08467 | + | 3.50418 / 3.50100 | − | 1.0106 | + | 0.8841 | − |
| 24004 | 3.04423 / 3.04557 | + | 3.79700 / 3.82234 | + | 1.0022 | + | 0.9953 | − |
| 24005 | 2.89055 / 2.90379 | + | 3.75903 / 3.67386 | − | 0.9850 | − | 0.9690 | − |

*來源：`stage3_{baseline,guided}/seed_*/tiny/trajectory.jsonl`（`best_gflops_so_far`、
`cumulative_complete_evals`、`gen`）。*

**AUC 穩健性檢查。** `analyze_large.py` 是從 trajectory 的第一列起積分原始的 `best_gflops_so_far`。
S14 §10.2 釘死的卻是另一個 AUC：`A = (1/B*)∫₀^{B*} log(I(u)/R_s) du`，其中 `u` = **post-Gen0** 的
完成評估數、`B* = min(evals_G, evals_F)`。tiny 兩者都算了。釘死的公式給出各 seed 的
`A_F − A_G` 為 −0.1051、−0.0167、+0.0109、+0.0023、−0.0141 ⇒ **2/5 為正** —— 與 `analyze_large.py`
形式的判定相同。因此 tiny 的 AUC 結論對採用哪一個公式並不敏感。（兩個公式竟然有差異這件事，已於 §7 列為
formal report 需處理的項目，因為 §7.1/§7.2 中 medium 與 large 的 AUC 判定是用非釘死的形式算的。）

### 2.3 tiny 釘死的 margin 在結構上是空洞的 —— 凡引用「5/5 PASS」處都須註明

`η_tiny = 0.4466` ⇒ 非退步 floor `e^{−η} = 0.6398`。`δ_tiny = 0.5630` ⇒ 改善 gate
`F/G > 1.5630`。實際觀測到的跨度是 **0.8828 … 1.0350**。

在 tiny 上要*不通過*非退步，guided champion 得比 baseline **慢 36 %**；要*通過*改善，得**快 56 %**。
在一個 champion 母體整個落在 3.53–4.14 GFLOP/s 的 shape 上，兩者都遠不可及。**tiny 的非退步結果不可能是
5/5 PASS 以外的任何結果，改善結果也不可能是 0/5 以外的任何結果。** 這兩格帶有零資訊量，不得當作有資訊來報告。
根因：`η_s` 是以 3-anchor × 7-repeat pilot（§3.8）擬合的*量測重複性*margin，而 tiny 的 pilot
殘差極大 —— S14 §10.2 明確拒絕讓其進入 aggregate 的那個 tiny 汙染
（*"不用 tiny-汙染的 aggregate delta_noise"*），卻仍然留在 tiny 自己的 per-shape
margin 裡。

---

## 3. 量測品質稽核（在任何詮釋**之前**完成）

§7.1a/§7.1b 已確立 7× remeasure 受到單邊 dropout 汙染，在 medium 約 ~28 %、在 large 為 0/70。
本節以原始重複值對 tiny 重做同一份稽核。

### 3.1 臂內散布與 dropout 普查 —— 全部 10 個臂

*來源：`stage3_baseline/seed_*/tiny/champion_interleaved.json` → `remeasure.{G,F}`；原始順序與
時間戳來自 `champion_interleaved_raw.jsonl`。*

| seed / arm | 7 次量測的 GFLOP/s | max/min | dropouts（< 該臂最大值的 80 %） |
|---|---|---:|---:|
| 24001 G | 4.12305 · 4.12149 · 4.13644 · 4.12188 · 4.15386 · 4.26820 · 4.15136 | 1.036× | 0 |
| 24001 F | 3.63427 · 3.64720 · 3.65146 · 3.65452 · 3.65625 · 3.64832 · 3.65645 | 1.006× | 0 |
| 24002 G | 3.83172 · 3.83508 · 3.83755 · 3.83564 · 3.83665 · 3.83295 · 3.83183 | 1.002× | 0 |
| 24002 F | 3.98333 · 3.93813 · 3.97078 · 3.96923 · 3.96143 · 3.97331 · 3.96048 | 1.011× | 0 |
| 24003 G | 3.97874 · 3.99631 · 4.01097 · 4.01012 · 3.97488 · 3.99704 · 4.01392 | 1.010× | 0 |
| 24003 F | 3.48778 · 3.54050 · 3.53391 · 3.51969 · 3.55056 · 3.54222 · 3.47936 | 1.020× | 0 |
| **24004 G** | 3.82056 · 3.80946 · 3.78233 · 3.83732 · 3.79491 · 3.80317 · **0.301263** | **12.737×** | **1** |
| 24004 F | 3.81234 · 3.81689 · 3.78255 · 3.77341 · 3.78539 · 3.77504 · 3.78659 | 1.012× | 0 |
| 24005 G | 3.79788 · 3.79119 · 3.79766 · 3.79722 · 3.79602 · 3.79755 · 3.79733 | 1.002× | 0 |
| 24005 F | 3.68397 · 3.67839 · 3.55749 · 3.67943 · 3.68221 · 3.68232 · 3.67839 | 1.036× | 0 |

**十個臂中有九個重複性極佳（max/min ≤ 1.036×）。** dropout 總計 **1 / 70 = 1.43 %**，
與 §7.1a 的 tiny 列完全一致。brief 中引述的 `0.301263` 逐字元確認無誤，發生在 **hip 7**、seed 24004、Arm G。

### 3.2 這唯一一次 dropout 對 median 與對 P95 各造成什麼影響

| statistic | 實測（7 次重複） | 移除 dropout（6 次重複） | **納入** dropout 的影響 |
|---|---:|---:|---|
| seed-24004 Arm-G median | **3.803170** | 3.806315 | **−0.083 %** |
| seed-24004 F/G ratio | **0.995325** | 0.994503 | **+0.083 %** |
| P95 of \|log residual\|，僅 seed-24004 Arm G | **1.777606** | 0.007665 | **膨脹 232×** |
| P95 of \|log residual\|，pooled 於全部 70 次 tiny 重複 | **0.014469** | 0.012654 *（整臂完全排除）* | **+14 %** |

- **median 紋風不動，正如預先登記的設計所意圖。** 七次中出現一次 dropout 只會讓 median 位移一個 order
  statistic；第 4 個（共 7 個）值從第 3 與第 4 個乾淨值的中點移到第 3 個乾淨值。位移為 **−0.083 %**，
  比它所吸收的擾動小三個數量級（該 dropout 讀值低了 92.2 %）。形式上，7 個值的 median 可容忍最多 3 個
  dropout（其 breakdown point 為 ⌊(7−1)/2⌋ = 3）；7 取 1 離過半數還很遠。
- **P95 的行為則相反，而且方向取決於 pool。** 在*那單一臂內*計算（n = 7）時，第 95 百分位會落在該離群值上，
  讀出 **1.777606** —— 是同一臂無 dropout 值（0.007665）的 232×，也是 pooled tiny
  值的 123×。若在整個 70 次重複的 pool 上計算，第 95 百分位大約是第 4 大的殘差，因此單一離群值搆不到它，
  該統計量只從 0.012654 移到 0.014469。**這正是 §7.1a 那句「a P95 statistic cannot see a 1-in-70 event
  (it is the 98.6th percentile)」背後的具體算術。** 其推論對本研究很重要：以 70 次重複擬合的 per-shape
  P95 在結構上對罕見汙染是盲的，所以「per-shape P95 說 tiny 是乾淨的」與「tiny 有一個 12.7× 的離群值」
  兩句話都成立、彼此並不矛盾。

### 3.3 dropout 的根因 —— medium 的機制是**被反證的**；機制本身是 `NOT_EVALUATED`

§7.1b 對 medium 的根因是*warm-up 以 enqueue 次數而非時間指定*：`num-warmups = 321` 在一個 10 µs 的 kernel
上只買到約 ~3.2 ms，計時視窗在 DPM 狀態仍在爬升時就打開，結果由 governor 的競速決定。§7.1b 也直接量了
tiny，發現其吞吐量**對 warm-up 長度不變**（321 與 20,544 次 warm-up 下都是 4.0 GFLOP/s），因為在
16,384 FLOP 下 tiny 是 dispatch-latency-bound、由 command processor 處理、不受 shader clock 節制。因此
medium 的機制不該適用於此。以下就 tiny 自身的證據來檢視：

**與 clock-floor 事件（量級上）相符的證據：**

- 該 dropout 位於**其臂最大值的 0.078509**（`0.301263 / 3.83732`）。§7.1b 引述的 MI300X DPM-floor 對
  峰值時脈比為 `165 / 2100 = 0.0786` —— 吻合到 **0.1 %**。散布 12.737× 與 `2100 / 165 = 12.727×`
  吻合到 0.08 %。
- **反對過度解讀的警告。** §7.1a 所述的 dropout 區間 `[0.0785, 0.7847]` 正是以*這一次量測*作為其下端點，
  所以「它落在觀測區間內」是循環論證。與*物理*時脈比的吻合並非循環，但單一點與單一比值吻合仍是薄弱的證據。

**反對 §7.1b warm-up 觸發機制的證據（三條獨立線索）：**

1. **在 session 中的位置。** 該 dropout 是**第 7 次（共 7 次）重複**，時間為 `2026-08-12T00:55:34.178713Z`，
   即**在一個 37.8 s 視窗中的第 34.7 s**，而該卡在此期間已以 ~2.5–3.4 s 的節奏連續跑了 12 個 benchmark
   process（`champion_interleaved_raw.jsonl`，seed 24004）。第 1–6 次重複 —— **包含真正冷啟動的第 1 次** ——
   全部乾淨。warm-up 太短會把風險集中在冷啟動；觀測到的模式恰恰相反。失敗那次重複之前的量測間隔
   （3.02 s）相對於該視窗的 2.48–3.43 s 範圍毫無異常。
2. **tiny 的 dropout 發生率不隨 warm-up 長度而下降。** `[GPU]`
   `tiny_mechanism_probe/summary.json`（hip 5，每個 variant 25 個全新 process，idle-gated）：

   | variant | overrides | median GFLOP/s | max/min | dropouts（< 最大值的 80 %） |
   |---|---|---:|---:|---:|
   | `A_baseline` | production 設定（321 次 warm-up、RBS 4096） | 3.8 | 1.072 | **0 / 25** |
   | `W321_norot` | 321 次 warm-up、RBS 0 | 4.0 | 1.046 | **0 / 25** |
   | `W5136_norot` | **5,136** 次 warm-up（production 的 16×）、RBS 0 | 4.0 | **1.688** | **1 / 25**（位於最大值的 0.60） |
   | `W20544_norot` | 20,544 次 warm-up、RBS 0 | 4.0 | 1.015 | **0 / 25** |

   這 100 次掃描中唯一的 dropout 發生在 **production warm-up 的 16×**，而在 production warm-up 下一次都
   沒發生。在 medium 上同一個旋鈕產生了乾淨的單調膝點（48 % → 32 % → 12 % →
   8 % → 0 %）。**§7.1b 的 warm-up 掃描是 medium 的結果，不能外推到 tiny。**
3. **失敗的那個 process 並未卡住。** `W5136_norot` 離群值的 wall time 為 **0.65 s**，相對於該 variant 的
   0.68 s median —— 正常。*量到的 kernel rate* 偏低而 wall time 沒有偏高，這與 host 端 hang 或排程停滯
   不一致，卻與 GPU 在約 ~1.3 ms 的計時視窗中確實跑得很慢一致。

**反對單純「全有全無 floor」讀法的證據。** 把所有曾經做過的 tiny 重複匯總 ——
70 次 Lock-A（`champion_interleaved.json`）、70 次 hip-5 replication（`tiny_gpu5_probe_summary.json`）、
100 次 mechanism-probe（`tiny_mechanism_probe/summary.json`）= **240 次量測、4 次 dropout（1.67 %）** ——
這些 dropout 的深度分別是其臂最大值的 **0.0785、0.0742、0.5544、0.60**。兩個在時脈 floor、
兩個在中段，分布於兩張不同的卡、重複位置分別為 1、5、7 與 19。所以 tiny 也會產生*漸進式*的 dropout，
而不只是 floor 式的；那個誘人的「medium 是漸進式 / tiny 是二元」故事**並不成立**。

> **判定：`NOT_EVALUATED` —— tiny 的 dropout 機制未獲解釋。** 其量級與完整的 DPM-floor 時脈狀態相容，
> 但 §7.1b 的觸發機制（冷卡上 warm-up 太短）被位置、被 warm-up 掃描、被 wall-time 證據所反證。
> 任何已做的量測都無法區分的候選觸發機制包括：計時視窗*內部*的暫時性 governor 降頻；
> driver/queue 事件；firmware 功耗突波。要區分它們需要在計時視窗期間取樣時脈遙測，而 §7.1b.2 記載此事在
> 本 container 中不可能（`/sys` 唯讀、無 host root）。**這裡不主張任何機制。** *已*確立的是其後果：該事件是
> 單邊的（只會太慢，不會太快）、發生率介於 1/70 到 1/240 之間，而且不會移動 7 個值的 median。

### 3.4 釘死的 η 對上 tiny 自身的經驗重複性 —— 以及兩者下的 gate 結果

依 Lock A 的定義 `η = P95(|log y − median log y|)` 重算噪音 margin，直接取自 tiny 自己的 70 次 remeasure
重複：

| estimate | value | 對比釘死的 η_tiny = 0.4466 |
|---|---:|---|
| **釘死值**（3-anchor × 7-repeat pilot，`noise/per_shape_noise.json`，S14 §10.2） | **0.44659979** | — |
| **經驗值**，pooled 於全部 70 次重複 | **0.014469** | 釘死值保守 **30.9×** |
| 經驗值，僅乾淨重複（69 次，排除該 dropout） | 0.011198 | 釘死值保守 39.9× |
| 經驗值，排除整個 seed-24004-G 臂（63 次） | 0.012654 | 釘死值保守 35.3× |

pooled 的 0.014469 與 §7.1a 的 tiny 列（`0.0145`，"31× conservative"）到小數三位皆一致 ——
這是一次獨立重算，與紀錄相符。

**兩種 margin 下的 gate 結果**（兩種都報，如 §7.2a 對 large 的規定）：

| seed | F/G | 釘死 η = 0.4466 → floor **0.639800** | 經驗 η = 0.014469 → floor **0.985635** |
|---|---:|---|---|
| 24001 | 0.8828 | PASS | **FAIL** |
| 24002 | 1.0350 | PASS | PASS |
| 24003 | 0.8841 | PASS | **FAIL** |
| 24004 | 0.9953 | PASS | PASS |
| 24005 | 0.9690 | PASS | **FAIL** |
| **median** | **0.9690** | **PASS**（0.9690 ≥ 0.6398） | **FAIL**（0.9690 < 0.9856） |
| | | **5/5 PASS** | **2/5 —— gate 未達成** |

改善 gate：釘死 δ = 0.5630（需 F/G > 1.5630）⇒ **0/5**；經驗 δ = `e^{0.014469}−1` =
0.014574（需 F/G > 1.014574）⇒ 1/5（僅 seed 24002）。

**兩個判定都不是關於 treatment 的事實**，因為在 tiny 上 treatment 為零。§5.3 會推導這對 large 上同樣的
margin 爭議意味著什麼。

---

## 4. 這個表觀效應是**真實且可重現的** —— 而它是由「什麼都沒做」造成的

這是讓 tiny 這一節值得寫的發現，也需要自成一節，因為它排除了那個顯而易見的緊縮式讀法
（「tiny 的 ±12 % 只是量測樂透，跟 medium 一樣」）。

`[GPU]` `tiny_gpu5_probe_summary.json` 對**同樣五對 champion**重跑了**同一份 sealed remeasure 協定**，
在**不同的卡（hip 5）**、在**約 ~13.5 小時後的不同 session**
（`finished_utc: 2026-08-12T14:33:40Z` 對比 Lock-A remeasure 的 00:24–01:51Z），過程中先擱置再還原原始
artifact。它原本是作為 §7.1b 的卡片混淆控制而跑的；其對 **F/G 統計量的 replication 價值似乎在紀錄中從未被
使用過。**

| seed | Lock-A 卡上的 F/G | hip 5 上的 F/G | `ln` 差 | % 差 |
|---|---:|---:|---:|---:|
| 24001 | 0.882754 (hip2) | 0.880834 | −0.00218 | −0.217 % |
| 24002 | 1.034980 (hip3) | 1.035487 | +0.00049 | +0.049 % |
| 24003 | 0.884132 (hip4) | 0.899425 | +0.01715 | +1.730 % |
| 24004 | 0.995325 (hip7) | 0.999070 | +0.00376 | +0.376 % |
| 24005 | 0.968952 (hip6) | 0.971117 | +0.00223 | +0.224 % |

`sd(ln difference) = 0.00752`；`max |ln difference| = 0.01715`。注意這次 replication 本身也對 dropout
穩健：hip-5 的執行帶有 2/70 個 dropout（seed 24003 Arm F 第 1 次重複，在最大值的 0.0742；seed
24004 Arm G 第 5 次重複，在最大值的 0.5544），仍將每個 ratio 重現到 1.7 % 以內。

**log 空間中的變異數分解：**

| component | sd | 變異數占比 |
|---|---:|---:|
| 觀測到的跨 seed `ln(F/G)` 散布（Lock-A 卡） | **0.07150** | 100 % |
| *同一個* `ln(F/G)` 在獨立卡與獨立 session 上的可重現性 | **0.00752** | **1.11 %** |
| ⇒ 可歸因於真實 champion 差異 | — | **98.89 %** |

**tiny 的各 seed F/G 值不是量測樂透。它們是兩個真正不同的 kernel 之間真實、可重現的效能差異 —— 而且是在
可證明為零的 treatment 下產生的。**

佐證這些 champion 確實是不同的物件：`champion_interleaved.json → arms.{G,F}`
顯示兩臂的 canonical config hash 在**五個 seed 中全部**不同，差異落在 **30 個 gene 中的 9–14 個**，
其中包含 `group_0` 的 `MatrixInstruction`，因而也包含 MacroTile：

| seed | Arm G MacroTile | Arm F MacroTile | genes differing |
|---|---|---|---:|
| 24001 | `MT16x64x64_MI16x16x1` | `MT64x64x64_MI16x16x1` | 11 |
| 24002 | `MT32x96x64_MI16x16x1` | `MT16x128x64_MI16x16x1` | 10 |
| 24003 | `MT16x64x128_MI16x16x1` | `MT128x32x64_MI32x32x1` | 14 |
| 24004 | `MT32x96x64_MI16x16x1` | `MT32x96x64_MI16x16x1` | 11 |
| 24005 | `MT64x48x64_MI16x16x1` | `MT64x64x64_MI32x32x1` | 9 |

---

## 5. 詮釋 —— null-control 讀法，附根因

### 5.1 根因：相同的輸入如何產生 12 % 的輸出差異

以下每項發現都是一個機制，不是把表格再講一次。

**Step 1 —— Gen0 完全相同（§1）。** 同一個檔案、同一個 seed、同一組 uniforms、同一個 prior。同樣的 512 個
個體；artifact 確認五個 seed 的 valid count 都相同。

**Step 2 —— Gen0 的 *fitness* 並不相同，因為 fitness 是 GPU 量測。** 在個體完全相同的母體上，
兩臂的 Gen0 median-Q 相差 0.30–1.36 %、Gen0 best-GFLOP/s 相差 0.04–5.34 %。這些差異就是量測噪音，
而它們是*唯一*有差異的東西。

**Step 3 —— 在 tiny 上那個噪音是決定性的，因為 fitness landscape 幾乎是平的。** 在 16,384 FLOP 下
tiny 是 dispatch-latency-bound（§7.1b，並由 probe 的 warm-up 不變性確認）：kernel 的時間都花在啟動額外
負擔上，所以 kernel *configuration* 幾乎不重要。兩臂、五個 seed 的十個 champion 全部落在
**3.53–4.14 GFLOP/s** —— 一個 1.17× 的帶 —— 而 Gen0 的 best 已經是
2.80–3.08，也就是說 GA 整個 7,570–9,982 次評估的搜尋，相對於自己的隨機起點只買到
**+15 % 到 +43 %（median +29 %）**。
當候選之間的差距小於量測噪音時，`argmax` 就是在對噪音做選擇。這正是 §3.6.2 從建模面所描述的 regime
（"tiny is *outside* Formocast's modelled regime"）在量測面的顯現。

**Step 4 —— 分歧不可逆且會累積。** S14 §10.2 在 Gen0 之後重置演化 RNG stream，但 selection 的*輸入*
（量到的 fitness）已經不同，所以從第 1 代起 parent set 就不同。兩臂接著在不同時點觸發 Ductile 原生的早停
（`period: 5`、diversity floor）—— G 跑了 20/24/30/22/23 代、F 跑了 21/30/23/21/23 代 —— 因此它們甚至拿到
**不同的評估預算**（釘死的 post-Gen0 共同預算 `B* = 7,297–8,121`；完成評估總數 G 為 7,669–9,969、
F 為 7,570–9,982）。

**Step 5 —— 終點是兩個真正不同的 kernel，其真實效能差異最多達 12 %，且可重現（§4）。** 1.17× 的 champion
帶寬與 F/G 散布的寬度恰好相同 —— 也就是說，tiny 的表觀 treatment 效應無非就是*從 GA 自身結果分布中抽兩次
獨立樣本*，而在這個 shape 上該分布寬 1.17×。

**次要觀察 —— winner's curse 存在且很小。** 搜尋期的 `best_fitness` 在 **10/10 個臂**都高於 7×-median
的 remeasure，高出 0.34–3.33 %（`optimization_result.json → best_fitness` 對比
`median_gflops`）。這就是 §5(i) 所預測的樂觀偏差，也是 remeasure 存在的三個理由之一。它*不是* F/G 散布的
來源 —— 該偏差是單邊的、且兩臂相近，所以在比值中大致抵銷。

### 5.2 本節貢獻的那個數字：「零 treatment 下的表觀效應」的經驗下界

| shape | activated genes | true effect | median F/G | span | `sd(ln F/G)` | `max abs ln(F/G)` | positive | dropouts |
|---|---:|---|---:|---|---:|---:|---:|---:|
| **tiny**（null control） | **0** | **恰為 0** | **0.9690**（−3.10 %） | 0.8828–1.0350（1.17×） | **0.0715** | **0.1247** | 1/5 | 1/70 |
| medium —— live campaign-2 | 2 | 未知 | 1.0274（+2.74 %） | 0.9884–1.0733（1.09×） | 0.0340 | 0.0707 | 3/5 | 17/70（24 %） |
| medium —— §7.1 所印出的 campaign-1 | 2 | 未知 | 0.9971（−0.29 %） | 0.3551–2.1175（5.96×） | 0.6515 | 1.0354 | 2/5 | （§7.1a：39/140 = 28 %） |
| large | 5 | 未知 | 1.0006（+0.06 %） | 0.9279–1.0622（1.14×） | 0.0530 | 0.0749 | 3/5 | 0/70 |

*tiny 與 large 取自 `stage3_baseline/seed_*/{tiny,large}/champion_interleaved.json`；medium campaign-2
取自 live 的 `stage3_baseline/seed_*/medium/champion_interleaved.json`（§7.1 所印、已被取代的 campaign-1
數值，於該處引用至
`medium_recheck_control/.../preserved_campaign1_20260812T135613Z/...`）。*

**重點：在 treatment 可證明為零的那個 shape 上，這條 pipeline 產生的各 seed 表觀效應，比兩個有 treatment
的 shape 都要大。** tiny 的 `sd(ln F/G) = 0.0715`，對比 large 的 0.0530
與 medium 乾淨 campaign-2 的 0.0340；`max abs ln(F/G)` 在 tiny 是 0.1247，對比 0.0749 與 0.0707。tiny 五個
seed 中有兩個顯示 −11.6 % 與 −11.7 % 的「效應」。

*那個*排序的根因（同樣是機制，不是裸事實）：純機器效應的大小，由 GA 在給定 shape 上自身結果分布有多寬決定，
而後者又由 fitness landscape 相對於噪音有多獎勵 configuration 決定。tiny 的 landscape 是平的、由噪音主導，
所以其結果分布很寬。large 的則由 main loop 主導、盆地很緊 —— §7.2 指出其 baseline
臂跨 seed 只有 ±4.4 % 的跨度 —— 所以其結果分布很窄。有 treatment 的 shape 之所以比沒有 treatment 的
機器噪音更小，**是因為它們的物理特性，不是因為 treatment。**

### 5.3 這允許什麼 —— 以及，謹慎地說，不允許什麼

**它「可以」：**

- **給出這條 pipeline 在 n=5 下「無 treatment 之表觀效應」的經驗下界。**
  在一個已知為 null 的 shape 上：median |表觀效應| ≈ 3.1 %、各 seed |表觀效應| 最高 11.7 %、
  `sd(ln) = 0.0715`、方向分割 1/5（`p = 0.375`）。日後任何在這條 pipeline 上宣稱該量級的各 seed 效應，
  都必須面對「零 treatment 在此就產生了它」這個事實。
- **一次同時打掉一個緊縮論證與一個膨脹論證。** 這個表觀效應*不是*量測樂透（§4：其變異數的 98.9 % 在獨立卡
  與獨立 session 上仍然存在），所以在這條 pipeline 上，「跨卡可重現 ⇒ 它是 treatment 效應」是
  **無效的推理**。在不同隨機 stream 下的 GA 隨機性同樣可重現，因為它終止於不同的 *kernel*，
  而 kernel 的效能是穩定的。
- **補上 §7.2a margin 爭議所缺的經驗數據點。** §7.2a 未解決 large 的非退步該以釘死的 η（5/5 PASS）
  或以經驗的 within-window η（3/5）來判定。tiny 回答的是經驗 margin *對一個已知 null 會做什麼*：在
  η_empirical = 0.0145 下，**null control 在 5 個 seed 中有 3 個被讀成退步，且在 median 上不通過。**
  理由是結構性的，不是 tiny 的怪癖：`η_s` 量的是量測**一個固定 config** 的重複性，而 `F/G` 比較的是隨機
  搜尋產生的**兩個不同 config**。在 tiny 上，臂間離散度（`sd(ln) = 0.0715`）是 within-window
  重複性（0.0145）的 **4.9×**；在 large 上是 **2.0×**（0.0530 對 0.0269）。在兩個 shape 上，`F/G` 的主導項
  都是 GA 結果的變異性，而量測重複性 margin 對它在任何方向上都沒有描述力。
- **顯示 tiny 釘死的 margin 是空洞的**（§2.3），使讀者不會把「tiny：5/5
  非退步 PASS」誤當成一個結果。

**它「不可以」：**

- **在數值上轉移到 medium 或 large。** 這些是刻意分歧的 regime（§3.6.1），不是平滑的掃描。
  η_tiny = 0.4466 對 η_medium = 0.0042（**106×**）以及 η_large = 0.1229。tiny 是
  dispatch-latency-bound、0 個 activated gene；medium 是 loop-structure-bound、2 個；large 是
  memory-pipeline-bound、5 個，且不論 seed 為何基本上都落在同一個盆地。GA 動態、噪音
  margin、landscape 曲率與問題 regime 全都不同。**tiny 的 0.0715 不是其他 shape 的校正常數，
  把它從那些數字中扣掉的做法都站不住腳。**
- **構成一個 null distribution。** 從形狀未知的分布中抽五對配對樣本，不足以支撐「零 treatment 有多常看起來
  像 X」的分位數、CI 或 p 值。以上全部都是描述性的。
- **允許說「medium 與 large 的效應只是機器」。** §5.2 的比較是啟發式的並列，不是檢定：它說的是 large 觀測到
  的離散度*不大於*零 treatment 在另一個 shape 上所產生的。這值得一提且值得報告，但它**不是** large 效應為零
  的證據 —— large 自身的機器變異從未被量測，因為 large 沒有 null 臂。要量它需要在 large 上做一次
  G-vs-G（A/A）replication，而那**沒有跑** —— `NOT_EVALUATED`。
- **對 confirmatory gate 有任何方向的貢獻。** S14 §10.2/§10.4 依設計排除 tiny，並要求 medium ∧ large
  （intersection-union，無 aggregate 救援）。tiny 僅為探索性。

---

## 6. 對此讀法的威脅，明說而非帶過

1. **n = 5。** 在 n = 5 下，精確雙尾符號檢定在任何分割都達不到 p < 0.05（5/5 或 0/5 給出
   p = 0.0625；觀測到的 1/5 給出 p = 0.375）。一切皆為描述性。
2. **資料中含有一次 dropout。** 它對所報 median 的影響是 −0.083 %（§3.2），因此不改變任何結論，但該臂並非
   純淨無瑕，此處是揭露而非修補。
3. **起始臂在 shape *內部*未做 counterbalance。** 五個 tiny seed 全部從 G 起始
   （`START_ARM[tiny] = G`）；S14 §10.2 的 pin 寫的是 *"臂順序 counterbalanced(部分 seed G→F、部分 F→G)"* ——
   部分 seed G→F、部分 F→G。實作是**跨 shape** 做 counterbalance（`{medium: G, large: F,
   tiny: G}`），而 `report-source-index.md` §8.4 記載此為刻意設計。對 tiny 的後果是：在每次重複中，
   Arm G 永遠占據冷的第 1 個位置。因此任何 position-1 的懲罰都是**不利於** Arm G、**有利於** Arm F ——
   而量到的 tiny 結果卻是 F 為負。**順序上的不對稱不可能製造出 tiny 的負向結果；若有影響，反而是遮蔽了一部分。**
   儘管如此，這仍是相對於 pin 字面規定的殘餘偏離。
4. **dropout 機制未獲解釋**（§3.3），原則上可能以 240 次重複普查無法解析的比率再次發生。它是單邊的
   （只會太慢），所以它對 median-of-7 估計量的最壞影響是有界且很小的。
5. **`ga_init_evidence.json` 只存在於 guided 臂。** baseline 臂的建構狀態是由 config 的 byte-identity
   （§1.3）涵蓋，而非由它自己的證據檔。
6. **GA 搜尋本身未受汙染。** §7.1b.1 已對 medium 確立此點（在一次長時間存活的搜尋 invocation 中，
   卡片全程都是暖的；只有短促而孤立的 remeasure session 會冷啟動）。tiny 搜尋期的
   `best_fitness` 值（十次執行全部落在 3.81–4.28）與 remeasure 的
   median（3.53–4.14）落在同一帶，並帶有 §5.1 所述那個小的單邊 winner's-curse 落差，沒有退化的特徵。
   champion 的*選擇*未受汙染。

---

## 7. For main session —— authority doc 可能需要的項目

依對現有紀錄改動幅度排序。**以下沒有任何一項已寫入任何
authority document。**

1. **§7 的 status 表已過期。** 它寫的是 *"7× interleaved G/F remeasure medians — tiny: `NOT_EVALUATED`
   (3/5 remeasured; 24002/24003 pending)"* 與 *"Per-shape directional-consistency gate outcome … tiny
   `NOT_EVALUATED`"*。5/5 全部完成且 PASS（`champion_interleaved_status.json`，完成於
   2026-08-12T00:25–01:51Z；seed 24002 是在 §8.4 的 `DEVIATION-REMEASURE-STOPLINE-20260812` 修正之後）。
   結果見上文 §2。建議在 §7.1/§7.2 旁新增一個小節。
2. **§7.1a 的 dropout 區間被 run root 中既有的資料推翻。** §7.1a/§7.1b 陳述 *"every
   dropout ever observed lies within `[0.0785, 0.7847]` of its arm's maximum, and the lower end matches
   the clock ratio `~165/2100 = 0.0786`"*。`tiny_gpu5_probe_summary.json` 含有一個位於
   **0.074248** 的 dropout（seed 24003 Arm F 第 1 次重複：`0.267398 / 3.60144`）—— 低於所述的下界。
   該區間至少應放寬為 `[0.0742, 0.7847]`，而「lower end matches the clock ratio」的推論也應從 *matches*
   弱化為 *brackets*。
3. **§7.1b 的 warm-up 機制應限縮到 medium；tiny 的 dropout 成因是 `NOT_EVALUATED`。**
   `tiny_mechanism_probe/summary.json` 顯示 tiny 在掃描中唯一的 dropout 發生在 **5,136** 次 warm-up
   （production 的 16×），而在 321 次是 **0/25**、在 20,544 次也是 **0/25** —— tiny 的 dropout 發生率並
   不隨 warm-up 長度單調變化。再加上 Lock-A 的那次 dropout 是在**持續負載 34.7 s 之後的第 7 次（共 7 次）
   重複**，medium 的機制對 tiny 是被反證的。§7.1b 的單調膝點表格是 medium 的結果。見 §3.3。
4. **§7.2a 應引用 tiny。** 尚未解決的「釘死 vs 經驗」margin 問題，現在有了一個已知為 null 的資料點：
   在經驗的 within-window η 下，tiny null control 讀出 **2/5 PASS、median FAIL**，
   也就是說經驗 margin 在真實效應恰為零之處宣告了退步。根因：η
   量的是一個固定 config 的重複性；`F/G` 比較的是兩個不同的 champion。見 §5.3。
5. **`analyze_large.py` 的 AUC 不是 §10.2 釘死的 AUC。** pin 是
   `A = (1/B*)∫₀^{B*} log(I(u)/R_s) du`，積分於 **post-Gen0** 的評估；而該 script 是從 Gen0 那一列起積分
   原始的 `best_gflops_so_far`。在 tiny 上兩者都給 2/5，所以 tiny 不受影響 —— 但 §7.1/§7.2 中 medium 與
   large 的 AUC 分量是用非釘死的形式算的，應在 formal report 之前重新推導。
6. **凡提及 tiny 的 5/5 非退步之處，都要記載 tiny 釘死的 margin 是空洞的**
   （§2.3）：floor 0.6398 與改善 gate 1.5630，對上 0.8828–1.0350 的觀測跨度，意味著這兩格不可能有別的
   結果。另有一個值得在報告中寫一句的諷刺：S14 §10.2 拒絕使用
   *"tiny-汙染的 aggregate delta_noise"*，但 tiny 自己的 per-shape η 卻帶著同樣的汙染。
7. **`§7.1c` 是一個懸空的 cross-reference。** `report-source-index.md:1703` 為「max estimator 把 medium 各
   seed 的 F/G 收斂到 ±7 % 以內」一事引用了 *"(§7.1c)"*；但檔案中並不存在 `§7.1c`。
8. **這是澄清，不是反駁：** `out-capped/ga-weights-tiny.json` 帶的是全部 27 個 free gene、皆為
   uniform `p0`，不是「only `group_0`」。「only `group_0`」這個性質屬於 GA config 中被注入的
   `Backend.Config.weights` 區塊。§6 的 "Activated genes: … tiny=none" 是正確的。
9. **可能可用於報告、目前未被使用的新證據：** `tiny_gpu5_probe_summary.json` 在
   §7.1b 中只因其 dropout 計數（2/70，為 hip 5 除罪）而被引用。它同時也是**對全部五個 tiny F/G ratio 的
   獨立跨卡、跨 session replication**，誤差在 0.05–1.73 % 以內（§4）。這正是把 tiny 從「有噪音的探索性
   shape」升級為「帶有可重現非零表觀效應的 null control」的關鍵，也是本分析中最值得引用的一點。
10. **large 上的 A/A control 是 `NOT_EVALUATED`。** 要把 §5.2 的跨 shape 比較從啟發式變成檢定，最乾淨的
    做法是在 large 上做一次 G-vs-G replication（兩次 baseline 執行、不同的
    RNG stream、相同協定）。它沒有跑，這裡也不提議跑；記下這個缺口，是為了確保
    「tiny 為 large 的機器變異定界」這句話絕不會在缺少它的情況下被主張。

---

*本分析於 2026-08-13 以唯讀方式對 sealed artifact 執行。未啟動任何實驗、未取得任何量測、未修改任何 artifact。
重算使用 run root 中 `gap_large.py` 與 `analyze_large.py` 的邏輯，另以 §10.2 釘死的 AUC 公式交叉核對。
無 seal、無 commit、無 push。*
