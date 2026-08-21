> **⚠️ 本檔是 per-shape 附冊，不是 S14 的 outcome 陳述。**
>
> 本檔是 **medium（confirmatory）per-shape 附冊**，承載的是**詳細實驗記錄**：
> 逐 seed 數字、trajectory、remeasure、量測稽核、根因、偏差。
>
> **本檔不得被讀成「S14 過了沒有」。** S14 的 per-shape gate 是跨 shape 的**連言**，
> **gate 判定現由 [`s14-guided-results.md`](s14-guided-results.md) §5.4 承載**
> （owner 2026-08-18 指定；原承載者 `full-ga-baseline-vs-guided-outcome-report.md`
> **已由 owner 解除授權**）。本附冊只報告各子判準的**計數**，不作 gate 判定，
> 也不對 combined 措辭發言。
>
> **Non-authority framing。** 若本檔與 [research charter](../../../surrogate-dse-plan.md)、
> [experiment plan](../../../ductile-origami-warmstart-experiment-plan.md)、
> 或 [`../../s14-stage1-full-ga-outcome-design.md`](../../s14-stage1-full-ga-outcome-design.md) 衝突，
> **一律以後三者為準**。`report-source-index.md` / `.zh-Hant.md` 為 non-authority 參考索引，
> 與本檔同級。
>
> **Evidence labels（全文一致）：** `[CODE AUDIT]` ＝ 讀 code／artifact 得到的事實（附 file:line／path）；
> `[BASELINE GPU]` ＝ Arm G 真實量測；`[GUIDED GPU]` ＝ Arm F 真實量測；
> `[MODEL-ONLY]` ＝ Formocast 模型空間量。
>
> **Anti-fabrication。** 本檔每一個數字都由撰稿者**直接對 primary artifact 重算或讀取**後才寫入，
> 並附來源路徑。未量測的量一律標 `NOT_EVALUATED`；**`NOT_EVALUATED ≠ 無效果**。
>
> **Two-sided。** 本檔**不**陳述 guidance 在 medium 上幫助或傷害了結果。medium 的 final-champion 與
> non-regression 端點在 design §13.3 中被**提議**為第三種狀態 `NOT_EVALUATED / instrument-invalid`；
> 該提議屬 `PENDING_HUMAN_DECISION`，本檔照此標記，但**不**代為核准。

---

```
report_kind: per_shape_annex
gate_verdict_holder: reports/staged/s14-guided-results.md  # owner 2026-08-18；原 parent_formal_report
#   (full-ga-baseline-vs-guided-outcome-report.md) 已解除授權
shape: medium (256, 256, 1, 1024)
shape_role: confirmatory
p0_levels: [capped 512, native 11405]      # native 屬 design §12 robustness addendum，在同一 gate 之內
seeds: 24001-24005 (5 paired)
arms: G = BASELINE (uniform p0) / F = GUIDED (Lock-B capped p1)
run_root_host: /data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-baseline
run_root_container: /src/rocm-libraries/agent_run/260809-s14-pershape-baseline
final_endpoint_status: NOT_EVALUATED / instrument-invalid   # PROPOSED, design 13.3, PENDING_HUMAN_DECISION
# 2026-08-18：該端點的 gate 狀態不因 2026-08-17 的儀器修復而改變，仍為 PENDING_HUMAN_DECISION 之下
#   被提議的 NOT_EVALUATED / instrument-invalid。修復後量到的 final ratio 讀數見 §18.3，
#   其 measurement-of-record 身分本身也是 PENDING_HUMAN_DECISION（§17）。
gate_verdict: 見 formal report（本附冊不陳述）
```

**約定。** `G` = Arm G = BASELINE（全部 free gene 使用 uniform `p0`）；`F` = Arm F = GUIDED
（在 2 個 activated gene 上使用 Lock-B capped `p1`）。`F/G > 1` 讀作 **guided faster**。
以下所有相對路徑除另有說明外皆位於上述 run root 之下。

---

## 0. 本附冊的三層結構

三層的證據地位完全不同，讀者務必分清：

| 層 | 內容 | 狀態 |
|---|---|---|
| **A｜GA trajectory 端點** | Gen0 best、gen-10 best、AUC，以及 Gen0 中心／極值／有效率 | **MEASURED，且量測缺陷碰不到**（§5.1）——這些讀自 `trajectory.jsonl`，從不經過 7× remeasure 路徑 |
| **B｜7× interleaved remeasure 端點** | final champion `F/G`、non-regression、improvement | **MEASURED 但儀器被證實不可重複**（§7、§8）；design §13.3 **提議**標為 `NOT_EVALUATED / instrument-invalid`（PENDING） |
| **C｜量測稽核與根因** | 雙峰、dropout 率、warm-up 根因、arm-asymmetry、兩次 campaign 的分歧 | **MEASURED**（§6–§10）——本附冊承載最重的一塊 |
| **D｜2026-08-17 的儀器修復（successor 量測）** | 修復前後對照、修復後的 final ratio 讀數與其噪音基準 | **MEASURED**（§18）——**不是本附冊任何預註冊端點，不代入 gate 算術**。它是 B 層那把尺被修好之後重讀的結果，estimand 已改（暖機 321→1400、`RBS` 4096→401、跨窗彙整），**因此是 successor 而非 B 層的替代品**。**是否為 measurement of record 為 `PENDING_HUMAN_DECISION`**（§17） |

**A 與 B 的關係決定了 B 的損害有多大。** 三項不受汙染的子判準（Gen0／gen-10／AUC）在 capped
P0 = 512 下**各為 3/5**（§5.1），而預註冊要求是 **≥4/5**。這一點必須先講清楚，因為它決定了
**§6–§10 的整套量測爭議實際上能改變多少**——那是紀錄誠實性的問題，不是能否改寫方向性計數的問題。
（此框架取自 design §13.2；design §13 整節為 `PENDING_HUMAN_DECISION`，故此處引述其**框架事實**，
而該框架事實本身已由本檔獨立重算確認。）

---

## 1. 配置、臂、seeds、pins

### 1.1 shape 與 treatment 的具體規模

- **shape**：medium `(256, 256, 1, 1024)`，`TotalFlops = 134,217,728`。
  *`[CODE AUDIT]` `stage3_baseline/seed_24001/medium/1_BenchmarkProblems/Cijk_Ailk_Bljk_BBS_BH_Bias_HA_S_SAV_UserArgs_00/Data/00_Final.csv`。*
- **shape role**：**confirmatory**（design §10.2）。
- **treatment 規模**：medium 有 **2 個 activated gene**（`DepthU`、`1LDSBuffer`），
  相對於 **29 個 free gene**（第 30 個 gene `group_0` 兩臂相同、不在 treatment 內）。
  `DepthU` 的引導強度 `ρ = 0.566015625`（≈71 % 全強度），`1LDSBuffer` 為 `ρ = 0.80`（100 %）。
  *`[CODE AUDIT]` `260809-s14-pershape-guidance/out-capped/ga-weights-medium.json`
  → `rho_per_gene`、`weights_source_per_gene`、`weight_beta = 0.25`、`lambda_s = 8.0`、
  `amendment = ENTROPY-CAP-20260810`。*
- **任何 null 都必須與這個規模並列陳述**（index §3.4b.4）：它是「**在這種規模的 prior 之下**」的結果。

### 1.2 兩個 P0 水準——為何都在這裡

本附冊**同時**涵蓋 capped（P0 = 512）與 native（P0 = 11,405）。理由是治理性的：native 是
design §12 的 **robustness addendum，屬於同一個 gate 之內**，不是第二個 gate
（`NATIVE-P0-ROBUSTNESS-20260811` + `(b)` 2026-08-12 將 shape 範圍由 large-only 擴充為 large + medium）。
兩個水準的差異**只有 Gen0 規模這一個自變數**（design §12.3）。

> **`REDUCER-FACT-CORRECTION-20260812` 提醒。** Ductile **未實作** Pareto／非支配排序；`soo=False`
> 以 `np.max` 縮併為純量（`ga.py:95, 256–273`），故 `Q = max_s` 是 Ductile 的**原生** fitness。
> per-shape 架構下 fitness 矩陣為 `(1, N)`，`max` 退化為恆等，因此本 shape 的 `Q` 就是
> 「medium 上的正規化真實吞吐量」。此為文件層更正，不改任何 pin／gate／claim。

### 1.3 capped（P0 = 512）的 pins——已驗證

| 項目 | 要求 | 觀測 | 來源 |
|---|---|---|---|
| `DUCTILE_FORCE_P0` | `= 1`（抑制膨脹分支） | `"1"`，**10/10** run | `stage3_{baseline,guided}/seed_*/medium/driver_status.json → environment` |
| Gen0 母體 | `512` | `generation_candidate_count = 512`，**10/10** | `stage3_{baseline,guided}/seed_*/medium/trajectory.jsonl`（gen-1） |
| `DUCTILE_PERSIZE_RBS` | medium = `4096` | `{"4096": [[256,256,1,1024]]}`，10/10 | 同上 `driver_status.json` |
| `NumElementsToValidate` | `128` | `128` | `champion_interleaved.json → measurement_metadata.num_elements_to_validate` |
| horizon | `n_gen = 30` + 原生早停 `period = 5` | 實際跑到第 23–30 代（見 §1.6） | `trajectory.jsonl` 最末筆 |

### 1.4 native（P0 = 11,405）的 pins——§12.3 fail-closed 條件逐項通過

*`[CODE AUDIT]` `stage5_native_{baseline,guided}/seed_{24001..24005}/medium/ga_init_evidence.json`（10 個檔案）。*

| 欄位 | 要求（§12.3） | 觀測值 | 通過 |
|---|---|---|---|
| `pop_size_at_construction` | `11405` | `11405` | **10/10** |
| `_pop_size_at_construction` | `512` | `512` | **10/10** |
| `decay_type_at_construction` | `large_space` | `large_space` | **10/10** |
| `native_p0_variant` | `true` | `true` | **10/10** |
| `n_gen` / `period` | `30` / `5` | `30` / `5` | **10/10** |
| `weights_sha256`（G） | Lock B baseline | `56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f`，5/5 相同 | **5/5** |
| `weights_sha256`（F） | Lock B guided | `d64ebd349b0492b1092beadca16f80846eb88d6347a87ba004725ba1b737d3a0`，5/5 相同 | **5/5** |
| `weights_gene_keys`（G） | `["group_0"]` | 完全相符 | **5/5** |
| `weights_gene_keys`（F） | `["group_0", "DepthU", "1LDSBuffer"]` | 完全相符 | **5/5** |
| `sampling_prob_genes`（F） | `["1LDSBuffer", "DepthU", "group_0"]` | 完全相符 | **5/5** |

`_pop_size_at_construction == 512` 與 `pop_size_at_construction == 11405` 同時出現，正是 `ga.py:113–118`
膨脹分支的確切簽名（`int(9918 × 1.15) = 11405`），而 `decay_type == "large_space"` 是安裝於 `ga.py:116`
的 law-1 decay。這正是 capped run 以 `DUCTILE_FORCE_P0` 刻意抑制掉的建構狀態。

**stock warning 存在，`Max iterations reached` 為零。** 十份 native GA log 每一份都含**恰好一次**：

```
GA:WARNING Some variables have a larger search space than pop_size. Increasing pop_size for the first generations.
GA:INFO GeneticAlgorithm(pop_size=11405, n_gen=30, period=5, tol=0.0008, div_thr=0.5, soo=False)
```

且每一份都含**零**行 `Max iterations reached`（`ga.py:289–293` 的 stock fail-open 從未執行）。
*`[CODE AUDIT]` `stage5_native_{baseline,guided}/seed_*/medium/*optimization.log` 第 1、3 行與全檔計數。*

**`DUCTILE_FORCE_P0` 不存在於 native 搜尋環境。** 十次 native run 的
`driver_status.json → environment` 只含 `CMAKE_BUILD_PARALLEL_LEVEL`、`DUCTILE_PERSIZE_RBS`、
`HIP_VISIBLE_DEVICES`、`PYTEST_XDIST_WORKER`、`PYTHONPATH`——**沒有** `DUCTILE_FORCE_P0`。
上游以結構性方式強制：launcher 透過 `env -u DUCTILE_FORCE_P0` spawn
（`scripts/s14_native_driver.py:473–475`），runner 在該變數被設定時直接 hard-fail
（`scripts/run_pershape_seed_native.py:139–142`）。

> **絕不可誤讀的一點。** `DUCTILE_FORCE_P0=1` *確實*出現在
> `champion_interleaved.json → measurement_metadata.environment` 之中。那是 **remeasure** 程序，
> 不是搜尋。remeasure 只重播兩個固定的 champion config，從不建構 `GeneticAlgorithm`；設定它只是為了讓
> native remeasure 環境與 capped remeasure 逐位元可比。
> *`[CODE AUDIT]` `scripts/s14_native_remeasure_driver.py:187`，行內註解為 `# inert here: the remeasure
> never constructs a GA`。（工作筆記記為 `:129`；經核對，正確行號為 `:187`。）*

**沒有 live 的 `native_gen0_degraded.json`。** 全 repository 搜尋
（`find /data1/perlee/rocm-libraries -name 'native_gen0_degraded*'`）回傳**恰好兩個**路徑，兩者都在
quarantine 目錄內（見 §15.2）。`stage5_native_{baseline,guided}/` 之下有**零**個 live degradation marker。

### 1.5 treatment 在兩個 P0 水準上是**同一個物件**——逐位元驗證

- **native 與 capped 消費的是磁碟上同一批 config 檔**：`config/s14-pershape-{,guided-}medium-seed_*.yaml`，
  mtime **2026-08-09 23:07**，早於 capped 波次、更早於 native 波次。
- guided config 與 baseline config 的 `diff` 為**純新增、零刪除**：`124952a124953,124962`，
  **恰 10 行新增**——`DepthU` 的 6 個權重值與 `1LDSBuffer` 的 2 個權重值，各加一行 gene key。
  `group_0` 的 9,918 個 GEKO weight 在兩臂中**逐位元相同**。
  *`[CODE AUDIT]` `diff config/s14-pershape-medium-seed_24001.yaml config/s14-pershape-guided-medium-seed_24001.yaml`。*
  > **與工作筆記的差異（如實記錄）：** 工作筆記記為「恰得 16 行新增」。以純 `diff` 重算為 **10 行**。
  > 實質主張（只有兩個 weight 向量不同、`group_0` 完全相同）不變；差的是行數計法。此處採用可重現的
  > 純 `diff` 計數。
- 那兩個向量與 Lock B **逐位元組相等**：
  `DepthU = [6.250864028930664, 2.7637107372283936, 10.506025314331055 ×4]`、
  `1LDSBuffer = [1.6076256036758423, 4.42307186126709]`；
  `rho_per_gene = {DepthU: 0.566015625, 1LDSBuffer: 0.8}`。
  *`[CODE AUDIT]` `260809-s14-pershape-guidance/out-capped/ga-weights-medium.json`。*
- 重放 Ductile 自身的轉換 `w → exp(−0.25·(w − min w))` 並正規化（`ga.py:145–146`），精確重現
  index §3.4b.3：`DepthU → [0.2096, 0.5011, 0.0723, 0.0723, 0.0723, 0.0723]`、
  `1LDSBuffer → [0.6690, 0.3310]`,**兩個 P0 水準相同**。四個不可信的 `DepthU` 值各得
  `(1 − ρ)/6 = (1 − 0.566015625)/6 = 0.0723`,即恰好 baseline 份額。
- **未受 treatment 的 `group_0` 也一併查核，而這才是這段的重點。** `group_0 → Σp² = 1.754e-4`,
  **兩臂相同**。它是唯一沒有進入 treatment 的 gene(§10.3 只對 activated free gene 注入 `p1`),
  所以若兩臂在它上面不同，整個 arm-comparison 的前提就破了。`Σp² = 1.754e-4` 對應均勻分布下
  `1/Σp² ≈ 5,701` 個候選，與 `group_0` 是複合 gene(MacroTile 等組合）相符。
  *`[CODE AUDIT]` 由 `ga.py:145–146` 的同一轉換重放得到;此值先前只存在於已退役的工作筆記，
  2026-08-13 補回。*

**因此在兩個 P0 水準上，treatment 字面上是同一個物件**——這是 §12 Q2 的必要前提條件，且它成立。

### 1.6 母體 decay 與實際消耗的預算

**native 觀測到的每代母體**（seed 24001 arm G；第 1–9 代在 **10/10** 次 run 中相同）：

| gen | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | … | 29 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 母體 | **11,405** | 5,958 | 3,235 | 1,873 | 1,192 | 852 | 682 | 597 | 554 | **494** | 446 | 408 | 377 | 352 | … | 258 |

*來源：`stage5_native_baseline/seed_24001/medium/trajectory.jsonl → generation_candidate_count`。*

- 第 1→9 代精確依循 **law 1**（`ga.py:116`，`int(512 + (sz − 512)/2)`）；每一 seed、每一臂、每一步都
  精確到整數相符。law 1 確實已安裝且生效，如 §12.3 所要求。
- **law 2 確實有介入**：第一個 post-crossover 尺寸是 `494 = int(256 + (554 − 256)/1.25)`
  （`ga.py:291`），而非 law 1 會給的 `533`。切換在母體數列本身就看得見。
- **capped 對照**（seed 24001 arm G）：`512 ×7 → 460, 419, 386, 360, 339, 322, 308 … 261`——
  law 1 從未安裝（`DUCTILE_FORCE_P0` 跳過該分支），母體固定在 512 直到 diversity 跌破 `div_thr = 0.5`
  才由 law 2 接手。

**Crossover 代數**（`diversity < 0.5` 的第一代），取自 GA-log 統計表：

| | 24001 | 24002 | 24003 | 24004 | 24005 |
|---|---:|---:|---:|---:|---:|
| native G | 9 | 9 | 9 | **8** | 9 |
| native F | **8** | 9 | 9 | 9 | **8** |
| capped G | 7 | **6** | 9 | 8 | 10 |
| capped F | 9 | 8 | 8 | 8 | 8 |

*來源：`stage5_native_{baseline,guided}/seed_*/medium/*optimization.log` 與
`stage3_{baseline,guided}/seed_*/medium/*optimization.log` 的 `diversity` 欄。*

index §3.2b 記錄 capped **large** 的 crossover 在**第 6 代**；medium 兩種變體都更晚
（capped medium 6–10、中位數 8；native medium 8–9、中位數 9）。**機制：** diversity 是 30 個 gene 上的
平均 pairwise Hamming mismatch（`core/population.py:194–205`）；native 之下第 1–8 代母體仍是 law-1 的
11,405→597，遠多於 mating operator 所調校的 512，而 `ratio=0.5, elitism=0.05` 的 tournament selection
移除的是固定*比例*，較大 pool 的存活集合保留更多相異 allele。**law 1 因此延後了 law 2 能介入的時點**
——這恰是 §3.2b 的預測，而它成立。

**兩臂的對稱性。** 5 個 seed 中 4 個兩臂 crossover 代數相同或差一代；在 gen-1 log 行仍存在的 9 個對上，
gen-1 diversity 差異是固定的 **+0.007**（有利於 guided 臂）。因此 decay 行為是**協定層級的共有性質，
不是臂層級的 confounder**。

**實際消耗的預算與 GPU 時間：**

| | 完整 eval 中位數 | 範圍 | `generation_evaluate_seconds` 加總 |
|---|---:|---|---|
| capped G | **10,011** | 8,522–10,705 | 0.17–0.21 h |
| capped F | **10,473** | 9,106–10,592 | 0.16–0.21 h |
| native G | **32,211** | 31,284–32,435 | 0.99–1.11 h |
| native F | **31,547** | 30,876–32,444 | 1.01–1.03 h |

*來源：各 `trajectory.jsonl` 最末筆 `cumulative_complete_evals`；`generation_evaluate_seconds` 之和。*
native 每臂多跑約 **3.2×** 的評估數。上表**只有 GPU 時間**，不含 design §12.6 記錄的約 2.9 h／臂
單執行緒 `space.sample(11405)` 拒絕抽樣成本。

**實際跑到的世代數**（原生早停 `period = 5` 生效）：
capped G `[23, 30, 30, 30, 25]`、capped F `[24, 30, 30, 30, 30]`、
native G `[29, 29, 25, 30, 25]`、native F `[30, 24, 27, 27, 27]`。
*來源：各 `trajectory.jsonl` 最末筆 `gen`。*

---

## 2. 端點、門檻與分析量

- **主要端點**（design §10.2/§10.4）：final champion 的 **7× interleaved G/F remeasure 中位數**
  real-GFLOP/s，同一 process、同一張卡、同一時間窗，per-shape counterbalance `START_ARM[medium] = G`，
  `repeats_per_arm = 7`、`single_measurements = 14`。
- **分析量**：`ln(F/G)`（index §5b）。**原始比值的算術平均具誤導性**，本檔一律附幾何平均。
- **釘住的 margin**（design §12.3 明訂 native 沿用同一 η）：

  | 量 | 值 | 來源 |
  |---|---|---|
  | `η_medium` | `0.0041953471169490775` | `noise/per_shape_noise.json → shapes.medium.eta_s` |
  | `δ_medium` | `0.004204159905590865` | 同上 `delta_s` |
  | 非退步下限 `F/G ≥ e^{−η}` | `0.995813441057657` | 同上 `nonregression_floor` |
  | 改善門檻 `F/G > 1 + δ` | `1.004204159905590865` | 由 `delta_s` 導出 |
  | `R_s`（正規化分母） | `3199.94` | 同上 `R_s` |

  `η_s` 的公式為 `P95(|log y − median_r log y|)`，`numpy` percentile `method='linear'`，
  由 3-anchor × 7-repeat noise pilot 殘差逐 shape 算出（`n_residuals = 21`）。
- **AUC**：以 step-hold 對 `cumulative_complete_evals` 積分至兩臂總量的 `min`
  （design §10.2 的 `B* = min(evals_G, evals_F)`），完全依 `analyze_large.py` / `analyze_medium.py` 的程序。
- **預註冊的 directional-consistency gate**：{Gen0 增量、gen-10 增量、AUC 差} 各需 **≥4/5** 為正，
  且最終 ratio ≥ `e^{−η_s}` 於 ≥4/5 對（median 亦過）。**本附冊只報計數。**
  > **⚠ 2026-08-18 補記 —— 上一行是預註冊原文（四項連言），現行判定不是。**
  > `ETA-MARGIN-REMOVED-20260814`（owner 2026-08-14）把 `η_s` 與第四項
  > `final ratio ≥ e^{−η_s}` **一併移出 gate 成分**，且未登記替代門檻，
  > **現行 gate 為前三項**。⚠ 該 token **尚未落到預註冊設計檔本身**
  > （`s14-...-design.md:226` 在該檔命中 0 次；index §2 ledger 註明「owner to amend separately」）。
  > **`final ratio` 並未被移除為必報量** —— 其判讀方法見 `measurement_design.md` §G.3.1
  > （對 null 尺，不設倍數門檻），讀數見 §18.3 與 `s14-guided-results.md`。
  > **gate 判定現由 `staged/s14-guided-results.md` §5.4 承載**（原承載者已由 owner 解除授權）。

---

## 3. 結果——capped，P0 = 512

### 3.1 GA trajectory 端點（不受量測缺陷影響）

`[BASELINE GPU]` / `[GUIDED GPU]`。*來源：`stage3_{baseline,guided}/seed_*/medium/trajectory.jsonl`。*

| seed | Gen0 G | Gen0 F | Gen0 F/G | gen-10 G | gen-10 F | gen-10 F/G | AUC F/G | `B*`（共同預算） |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 24001 | 10,287.5 | 10,904.8 | **1.0600** | 13,165.6 | 13,394.9 | **1.0174** | **1.0358** | 8,522 |
| 24002 | 10,081.8 | 10,088.6 | **1.0007** | 11,895.1 | 12,386.4 | **1.0413** | **1.0210** | 10,011 |
| 24003 | 12,121.6 | 11,577.4 | 0.9551 | 14,550.6 | 14,276.8 | 0.9812 | 0.9783 | 10,592 |
| 24004 | 11,382.7 | 9,956.1 | 0.8747 | 12,181.0 | 13,055.9 | **1.0718** | **1.0461** | 10,469 |
| 24005 | 10,023.2 | 10,095.9 | **1.0073** | 13,041.5 | 11,488.8 | 0.8809 | 0.9509 | 9,837 |
| **F > G 的 seed 數** | | | **3/5** | | | **3/5** | **3/5** | |

Gen0 診斷量（同一份 gen-1 紀錄）：

| seed | 中心 G | 中心 F | 中心 F/G | 有效 G / F（共 512） |
|---|---:|---:|---:|---|
| 24001 | 1.3446 | 1.4031 | **1.0435** | 508 / 502 |
| 24002 | 1.3400 | 1.3230 | 0.9873 | 505 / 509 |
| 24003 | 1.4062 | 1.4002 | 0.9958 | 507 / 507 |
| 24004 | 1.3894 | 1.4242 | **1.0251** | 508 / 509 |
| 24005 | 1.3381 | 1.4043 | **1.0495** | 507 / 507 |
| **中位數 / 計數** | | | **1.0251（3/5）** | — |

中心 = `generation_Q_median_any_valid`；極值 = `best_gflops_so_far`；有效性 = `generation_any_valid_count`。

### 3.2 7× remeasure——**兩個 campaign，兩張表，不平均、不擇一**

`[BASELINE GPU]` / `[GUIDED GPU]`。兩個 campaign 的存在與治理狀態見 §6。

**Campaign 1**（2026-08-11T08:33:36Z–08:36:19Z，GPU 5）。

> **⚠ 更新 2026-08-15（owner 決定）。** 本節原記「design §13.3 **提議**此為 measurement of record
> （**PENDING**，未核准）」。**該 PENDING 已結案，但結案方式不是拔擢 campaign 1。**
> owner 的裁決是：**canonical capped medium 五個 seed 一起 revert 回 campaign 1**
> （campaign 2 於 revert 前先保存到 `preserved_campaign2_20260815T000000Z/`），
> 而 **campaign 1 與 campaign 2 都不是 measurement of record —— 一個新的 campaign 取代兩者**。
> **本附冊的處置完全不變：兩個都報告，不平均、不擇一，兩者皆不產生 tier。**
> 詳見 §6.5。

| seed | G 中位數 | F 中位數 | **F/G** | % | `ln(F/G)` | non-reg | improv |
|---|---:|---:|---:|---:|---:|---|---|
| 24001 | 13,495.3 | 13,456.3 | 0.9971 | −0.3 % | −0.0029 | True | False |
| 24002 | 12,349.9 | 8,710.9 | 0.7053 | −29.5 % | −0.3491 | False | False |
| 24003 | 6,137.5 | 6,595.3 | 1.0746 | +7.5 % | +0.0719 | True | True |
| 24004 | 6,283.1 | 13,304.5 | 2.1175 | +111.8 % | +0.7502 | True | True |
| 24005 | 13,192.3 | 4,684.9 | 0.3551 | −64.5 % | −1.0353 | False | False |
| **中位數** | — | — | **0.9971** | **−0.3 %** | **−0.0029** | **3/5** | **2/5** |
| ⚠ *原始比值算術平均（**具誤導性**）* | | | *1.0499* | *+5.0 %* | *mean ln −0.1130 ⇒ **幾何平均 0.8931，−10.7 %*** | | |

為正 **2/5**；`mean |ln(F/G)| = 0.4419`；`ln(F/G)` 母體標準差 `0.5827`。
*來源：`medium_recheck_control/capped/seed_*/preserved_campaign1_20260812T135613Z/champion_interleaved.campaign1_20260812T135613Z.json`
→ `median_gflops.{G,F}`、`F_over_G_median_ratio`、`F_over_G_median_log_ratio`、
`F_median_ge_G_median_times_exp_neg_eta_s`、`F_over_G_gt_one_plus_delta_s`。*

**Campaign 2**（2026-08-12T14:00:41Z–14:04:19Z，GPU 5）。在解盲後**就地覆寫**了 canonical path，
**其後於 2026-08-15 被移離 canonical**（capped 側）——見 §6.1。

| seed | G 中位數 | F 中位數 | **F/G** | % | `ln(F/G)` | non-reg | improv |
|---|---:|---:|---:|---:|---:|---|---|
| 24001 | 13,436.4 | 13,349.8 | 0.9936 | −0.6 % | −0.0065 | False | False |
| 24002 | 12,258.1 | 12,744.8 | 1.0397 | +4.0 % | +0.0389 | True | True |
| 24003 | 14,562.0 | 14,960.4 | 1.0274 | +2.7 % | +0.0270 | True | True |
| 24004 | 12,583.8 | 13,505.8 | 1.0733 | +7.3 % | +0.0707 | True | True |
| 24005 | 13,490.6 | 13,334.7 | 0.9884 | −1.2 % | −0.0116 | False | False |
| **中位數** | — | — | **1.0274** | **+2.7 %** | **+0.0270** | **3/5** | **3/5** |

為正 **3/5**；`mean ln = +0.0237 ⇒ 幾何平均 1.0240`；`mean |ln| = 0.0309`；母體標準差 `0.0304`。
*來源：`medium_recheck_control/capped/seed_*/preserved_campaign2_20260815T000000Z/champion_interleaved.campaign2_20260815T000000Z.json`
（**引用已於 2026-08-15 repoint**；原引 `stage3_baseline/seed_*/medium/champion_interleaved.json`
「canonical path，現由 C2 佔據」，該敘述自 2026-08-15 起不成立，見 §6.1。
**上表五列數值逐筆重算自新路徑，完全相同**；seed 24004 一列例外，見下）。
**seed 24004 沒有 campaign-2 artifact**——它於 2026-08-13 被 campaign 3 就地覆寫且無備份，
故該列取自未受污染的 `medium_recheck_summary.json → results.capped.24004`
（`F_over_G_median_ratio = 1.0732688059250783`）。*

### 3.3 逐次 raw repeat——capped

7 次重播對的是**同一個固定 champion config**，在單一 process、單一張卡、約 **22–25 秒**的視窗內完成。
它理應是本研究中最可重複的數字。

**Campaign 1**（每列 7 次；`hi` = 該臂 7 次中 > 10,000 GFLOP/s 的次數；`drop` = 低於該臂最大值 95 % 的次數）：

| seed / arm | min | median | max | max÷min | hi | drop |
|---|---:|---:|---:|---:|---:|---:|
| 24001 G | 3,771 | **13,495** | 13,598 | 3.61× | 6 | 1 |
| 24001 F | 2,234 | **13,456** | 13,547 | 6.06× | 6 | 1 |
| 24002 G | 5,255 | **12,350** | 12,420 | 2.36× | 5 | 2 |
| 24002 F | 5,852 | **8,711** | 12,784 | 2.18× | 3 | 4 |
| 24003 G | 4,712 | **6,137** | 15,067 | 3.20× | 3 | 4 |
| 24003 F | 4,478 | **6,595** | 14,800 | 3.31× | 3 | 4 |
| 24004 G | 4,988 | **6,283** | 12,504 | 2.51× | 2 | 5 |
| 24004 F | 3,925 | **13,304** | 13,400 | 3.41× | 5 | 2 |
| 24005 G | 3,808 | **13,192** | 13,539 | 3.56× | 4 | 3 |
| 24005 F | 2,166 | **4,685** | 10,535 | 4.86× | 1 | 6 |
| **合計** | | | | | | **32 / 70 = 45.7 %** |

**Campaign 2**：

| seed / arm | min | median | max | max÷min | hi | drop |
|---|---:|---:|---:|---:|---:|---:|
| 24001 G | 4,979 | **13,436** | 13,548 | 2.72× | 6 | 1 |
| 24001 F | 4,239 | **13,350** | 13,524 | 3.19× | 4 | 3 |
| 24002 G | 2,408 | **12,258** | 12,404 | 5.15× | 5 | 2 |
| 24002 F | 4,122 | **12,745** | 12,762 | 3.10× | 6 | 1 |
| 24003 G | 14,389 | **14,562** | 14,694 | 1.02× | 7 | 0 |
| 24003 F | 14,918 | **14,960** | 15,013 | 1.01× | 7 | 0 |
| 24004 G | 4,958 | **12,584** | 12,608 | 2.54× | 4 | 3 |
| 24004 F | 4,745 | **13,506** | 13,858 | 2.92× | 4 | 3 |
| 24005 G | 3,665 | **13,491** | 13,633 | 3.72× | 4 | 3 |
| 24005 F | 7,004 | **13,335** | 13,407 | 1.91× | 6 | 1 |
| **合計** | | | | | | **17 / 70 = 24.3 %** |

*來源：`…/champion_interleaved_raw{,.campaign1_20260812T135613Z}.jsonl`（各 14 筆紀錄：`arm`、`gflops`、
`repeat`、`position_in_repeat`、`timestamp`）。*

---

## 4. 結果——native，P0 = 11,405

### 4.1 GA trajectory 端點（不受量測缺陷影響）

*來源：`stage5_native_{baseline,guided}/seed_*/medium/trajectory.jsonl`。*

| seed | Gen0 G | Gen0 F | Gen0 F/G | gen-10 G | gen-10 F | gen-10 F/G | AUC F/G | `B*` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 24001 | 10,904.9 | 11,766.3 | **1.0790** | 14,046.2 | 13,720.5 | 0.9768 | **1.0331** | 32,306 |
| 24002 | 10,996.9 | 11,386.1 | **1.0354** | 13,575.1 | 13,999.5 | **1.0313** | **1.0190** | 30,876 |
| 24003 | 12,086.8 | 11,904.6 | 0.9849 | 13,692.7 | 13,586.8 | 0.9923 | 0.9994 | 31,295 |
| 24004 | 11,415.7 | 11,289.9 | 0.9890 | 14,285.2 | 13,336.4 | 0.9336 | 0.9556 | 31,547 |
| 24005 | 11,622.9 | 11,538.4 | 0.9927 | 14,222.8 | 13,777.0 | 0.9687 | **1.0261** | 31,284 |
| **F > G 的 seed 數** | | | **2/5** | | | **1/5** | **3/5** | |

Gen0 診斷量：

| seed | 中心 G | 中心 F | 中心 F/G | 有效 G / F（共 11,405） |
|---|---:|---:|---:|---|
| 24001 | 1.3567 | 1.4053 | **1.0358** | 11,285 / 11,289 |
| 24002 | 1.3570 | 1.3803 | **1.0172** | 11,293 / 11,294 |
| 24003 | 1.3335 | 1.4040 | **1.0529** | 11,300 / 11,304 |
| 24004 | 1.3622 | 1.4016 | **1.0289** | 11,283 / 11,261 |
| 24005 | 1.3543 | 1.3992 | **1.0331** | 11,284 / 11,305 |
| **中位數 / 計數** | | | **1.0331（5/5）** | — |

有效率：G **98.93–99.08 %**、F **98.74–99.12 %**（capped：G 505–508 / 512、F 502–509 / 512）。

### 4.2 7× remeasure——native 也有兩個 campaign

> **本附冊新增的更正（重要）。** 工作筆記
> `working-notes/s14-native-p0-medium-analysis.md` §3 把 native 的 7× 結果引用到
> `stage5_native_baseline/seed_*/medium/champion_interleaved.json`。**該 canonical path 現已被
> campaign 2 覆寫**（2026-08-12T14:04:44Z–14:08:18Z），因此**它已不再含有工作筆記所引的數字**。
> 工作筆記的 native 表是 **campaign 1**，其可重現路徑為
> `medium_recheck_control/native/seed_*/preserved_campaign1_20260812T135613Z/champion_interleaved.campaign1_20260812T135613Z.json`。
> 沒有任何資料遺失（保存路徑逐位元重現該表）。**這與 index §7.1a 為 capped 所做的「Citation
> repointed 2026-08-12」是同一件事，只是先前沒有人為 native 記下來。**

**Campaign 1**（2026-08-12T12:00:26Z–13:19:17Z，GPU 5）：

| seed | G 中位數 | F 中位數 | **F/G** | % | `ln(F/G)` | non-reg | improv |
|---|---:|---:|---:|---:|---:|---|---|
| 24001 | 13,980.8 | 6,802.0 | 0.4865 | −51.3 % | −0.7205 | False | False |
| 24002 | 6,187.4 | 14,022.7 | 2.2663 | +126.6 % | +0.8182 | True | True |
| 24003 | 13,607.9 | 5,082.6 | 0.3735 | −62.6 % | −0.9848 | False | False |
| 24004 | 11,531.8 | 13,136.2 | 1.1391 | +13.9 % | +0.1303 | True | True |
| 24005 | 7,516.3 | 14,826.2 | 1.9725 | +97.3 % | +0.6793 | True | True |
| **中位數** | — | — | **1.1391** | **+13.9 %** | **+0.1303** | **3/5** | **3/5** |
| ⚠ *原始比值算術平均（**具誤導性**）* | *10,564.8* | *10,773.9* | *1.2476* | *+24.8 %* | *mean ln −0.0155 ⇒ **幾何平均 0.9846，−1.5 %*** | | |

為正 **3/5**;`mean |ln| = 0.6666`;母體標準差 `0.7260`。

**這些比值不是連續分布的，是被量化的 —— 這一點必須明說，否則上表讀起來像是 native 造成了巨大的
臂間差異。** 機制如下：

1. 每個臂的 7 次重複落在**兩個模式**之一 —— 乾淨模態約 14,000 GFLOP/s,污染模態約 6,000
   GFLOP/s(§7 的雙峰)。
2. 端點取的是 7 次的**中位數**,而中位數在雙峰樣本上只會回報「哪一個模式佔多數」—— 乾淨值佔
   ≥4 次就回報高模式，否則回報低模式。**中位數在這裡是一個模式選擇器，不是一個平均。**
3. 因此 `F/G` 依構造只能落在三個值附近：**≈1**(兩臂同模式)、**≈14,000/6,000 ≈ 2.3**
   (F 高、G 低)、或 **≈0.43**(F 低、G 高)。
4. 實測的 native C1 比值是 **0.4865、2.2663、0.3735、1.1391、1.9725** —— 五個全部落在這三個
   預測位置附近，沒有一個落在中間。

**後果：上表的 `F/G` 欄位量到的是「哪個臂這次抽到乾淨模式」，不是兩個 champion 的效能差異。**
`+126.6 %` 與 `−62.6 %` 不是效應量，是模式抽籤的結果。這正是 design §13.3 把 medium 的最終端點
提議為 `NOT_EVALUATED / instrument-invalid` 的直接理由，也是為什麼**不得**對這些比值取平均、
取極值或做任何進一步統計。

*此論證先前只存在於已退役的工作筆記，2026-08-13 補回。模式位置由 §7 的原始重複值支持;
「中位數為模式選擇器」是對 median 在雙峰樣本上行為的算術陳述，非經驗宣稱。*

⚠ **「原始比值算術平均」那一列已被標記，不得被引用為效應量。** 它讀起來是 **+24.8 %**，而幾何平均——
正確的乘法型集中趨勢——是 **−1.5 %**。這比 capped campaign 1（+5.0 % vs −10.7 %）更尖銳，
因為 native campaign 1 有兩個比值高於 1.97。

**Campaign 2**（2026-08-12T14:04:44Z–14:08:18Z，GPU 5）：

| seed | G 中位數 | F 中位數 | **F/G** | % | `ln(F/G)` | non-reg | improv |
|---|---:|---:|---:|---:|---:|---|---|
| 24001 | 14,169.2 | 14,227.0 | 1.0041 | +0.4 % | +0.0041 | True | False¹ |
| 24002 | 13,997.5 | 11,556.7 | 0.8256 | −17.4 % | −0.1916 | False | False |
| 24003 | 13,700.2 | 14,037.2 | 1.0246 | +2.5 % | +0.0243 | True | True |
| 24004 | 14,835.8 | 10,428.7 | 0.7029 | −29.7 % | −0.3525 | False | False |
| 24005 | 14,260.2 | 15,026.4 | 1.0537 | +5.4 % | +0.0523 | True | True |
| **中位數** | — | — | **1.0041** | **+0.4 %** | **+0.0041** | **3/5** | **2/5** |

為正 **3/5**；`mean ln = −0.0927 ⇒ 幾何平均 0.9115`；`mean |ln| = 0.1250`；母體標準差 `0.1558`。
¹ `1.0041 < 1 + δ = 1.004204`，故 improvement 為 False——差距在第四位小數。

### 4.3 逐次 raw repeat——native

**Campaign 1**：

| seed / arm | min | median | max | max÷min | hi | drop |
|---|---:|---:|---:|---:|---:|---:|
| 24001 G | 6,107 | **13,981** | 14,194 | 2.32× | 4 | 3 |
| 24001 F | 3,609 | **6,802** | 14,165 | 3.93× | 3 | 4 |
| 24002 G | 4,630 | **6,187** | 13,959 | 3.01× | 2 | 5 |
| 24002 F | 4,482 | **14,023** | 14,079 | 3.14× | 4 | 3 |
| 24003 G | 6,986 | **13,608** | 13,784 | 1.97× | 5 | 2 |
| 24003 F | 3,516 | **5,083** | 14,013 | 3.99× | 2 | 5 |
| 24004 G | 4,490 | **11,532** | 14,945 | 3.33× | 5 | 4 |
| 24004 F | 6,394 | **13,136** | 13,286 | 2.08× | 5 | 2 |
| 24005 G | 3,755 | **7,516** | 13,927 | 3.71× | 3 | 4 |
| 24005 F | 9,182 | **14,826** | 14,869 | 1.62× | 6 | 1 |
| **合計** | | | | | | **33 / 70 = 47.1 %** |

**Campaign 2**：

| seed / arm | min | median | max | max÷min | hi | drop |
|---|---:|---:|---:|---:|---:|---:|
| 24001 G | 6,503 | **14,169** | 14,273 | 2.19× | 4 | 3 |
| 24001 F | 6,165 | **14,227** | 14,313 | 2.32× | 6 | 1 |
| 24002 G | 5,892 | **13,998** | 14,107 | 2.39× | 5 | 2 |
| 24002 F | 6,317 | **11,557** | 14,061 | 2.23× | 5 | 4 |
| 24003 G | 6,013 | **13,700** | 13,841 | 2.30× | 5 | 2 |
| 24003 F | 6,293 | **14,037** | 14,098 | 2.24× | 6 | 1 |
| 24004 G | 3,635 | **14,836** | 14,955 | 4.11× | 5 | 2 |
| 24004 F | 5,944 | **10,429** | 13,290 | 2.24× | 4 | 4 |
| 24005 G | 5,752 | **14,260** | 14,466 | 2.52× | 6 | 1 |
| 24005 F | 3,252 | **15,026** | 15,060 | 4.63× | 6 | 2 |
| **合計** | | | | | | **22 / 70 = 31.4 %** |

*來源：`stage5_native_baseline/seed_*/medium/champion_interleaved_raw.jsonl` 與
`medium_recheck_control/native/seed_*/preserved_campaign1_20260812T135613Z/champion_interleaved_raw.campaign1_20260812T135613Z.jsonl`。*

---

## 5. 方向一致性子判準——彙總

### 5.1 三項不受汙染的子判準：Gen0／gen-10／AUC 各 **3/5**（capped）

**這一節是決定「量測缺陷實際上有多重要」的關鍵，必須先講清楚。**

**Gen0、gen-10、AUC 三項全部讀自 GA trajectory（`trajectory.jsonl`），從不經過 7× remeasure 路徑。
量測缺陷碰不到它們。** 無論兩個 campaign 之爭如何裁決、無論估計量是 median 還是 max、
無論 `η_medium` 是否被更換，這三個計數都**不會改變**。

| 子判準 | capped P0 = 512 | native P0 = 11,405 | 預註冊要求 | 是否可被量測缺陷影響 |
|---|---:|---:|---|---|
| Gen0 best（`best_gflops_so_far`，gen-1 紀錄） | **3/5** | **2/5** | ≥4/5 | **否** |
| gen-10 best | **3/5** | **1/5** | ≥4/5 | **否** |
| AUC（best-so-far 對共同 `B*`） | **3/5** | **3/5** | ≥4/5 | **否** |

*來源：本檔 §3.1、§4.1，由 `analyze_medium.py` 的同一 code path 對 `trajectory.jsonl` 重算。*

capped 的 3/5、3/5、3/5 與 design §13.2 的框架事實表逐格相符（該表由本檔獨立重算確認）。

### 5.2 受量測缺陷影響的最終端點

| 子判準 | capped C1 | capped C2 | native C1 | native C2 | 要求 |
|---|---:|---:|---:|---:|---|
| final champion（7× 中位數 > 1） | **2/5** | **3/5** | **3/5** | **3/5** | ≥4/5 |
| final **非退步** `F ≥ G·e^{−η}` | **3/5** | **3/5** | **3/5** | **3/5** | ≥4/5 |
| final **改善** `F > G·(1+δ)` | **2/5** | **3/5** | **3/5** | **2/5** | ≥4/5 |

> **⚠ 這張表的四欄全部量在有缺陷的儀器上（2026-08-18 補記）。**
> 2026-08-17 的儀器修復之後，同一批 champion 在 `nw = 1400 / RBS = 401` 上重新量過：
> **capped 為 3/5**（`C03` 與 `C03CONF` 兩批，各 12 window）、**native 為 3/5**（`STAGE2_NATIVE`，12 window）。
> **這兩個數字刻意不併入上表** —— estimand 已改（暖機、`RBS`、跨窗彙整），依 §0 的層級劃分它們屬 **D 層**，
> 是 successor 而不是 B 層的替代品，**不代入 gate 算術**。逐 seed 讀數與它們的噪音基準見 **§18.3**。
> **native 的計數修前修後都是 3/5** —— 修復改變的是汙染率與離散度，不是計數（§18.1）。

**為什麼同一個非退步判準在 large 上是 5/5、在這裡只有 3/5 —— 差別不在資料，在門檻。** 非退步的
下限是 `F ≥ G·e^{−η_s}`，而 `η_medium = 0.42 %` 比 `η_large = 12.28 %` **緊約 29 倍**。也就是說
medium 是用一條窄了一個數量級的容忍帶在被判定，而它自己的量測離散度又是三個 shape 裡最大的
（per-seed F/G 散布 0.36×–2.12×，§7）。兩個效應同向疊加：**門檻更嚴、雜訊更大**。此外本 shape
有兩個 seed 退步超過 50 %，那是任何合理 margin 都擋不住的幅度，所以這個 3/5 並不是「差一點」。

這個對照也正是 design §13.4 要求三個 shape 都**同時報告 pinned 與實測兩種 margin** 的理由：
在 medium 上保留 pin **不是**比較保守的選擇。

*此對照先前只存在於已退役的工作筆記，2026-08-13 補回。*

**這四欄的端點在 design §13.3 中被提議為 `NOT_EVALUATED / instrument-invalid`——既非 pass 亦非 fail，
兩個 campaign 皆然。該提議是 `PENDING_HUMAN_DECISION`。** 上表列出是為了完整記錄，
不是為了作為端點使用。

**診斷用（非 gate）**：Gen0 **中心** `generation_Q_median_any_valid`——capped **3/5**、native **5/5**。
此量是對約 510（capped）／約 11,290（native）個有效候選取中位數，因此它是對量測樂透**取平均**，
而不是**穿過它取最大值**；它與最終端點的病理不同（§12）。

---

## 6. 兩次 remeasure campaign，以及它們不一致這件事

### 6.1 時間線（由 raw jsonl 的 `timestamp` 逐筆重建）

| campaign | P0 level | 逐 seed 量測視窗（UTC） | canonical path 狀態 |
|---|---|---|---|
| **C1** | capped | 2026-08-11T08:33:36Z – 08:36:19Z | **2026-08-12 曾被覆寫，2026-08-15 已 revert 回 canonical**；同時保存於 `medium_recheck_control/capped/seed_*/preserved_campaign1_20260812T135613Z/` |
| **C1** | native | 2026-08-12T12:00:26Z – 13:19:17Z¹ | **已被覆寫**（未 revert）；保存於 `medium_recheck_control/native/seed_*/preserved_campaign1_20260812T135613Z/` |
| **C2** | capped | 2026-08-12T14:00:41Z – 14:04:19Z | **2026-08-15 已移離 canonical**；保存於 `medium_recheck_control/capped/seed_*/preserved_campaign2_20260815T000000Z/`（**seed 24004 除外——無 artifact**） |
| **C2** | native | 2026-08-12T14:04:44Z – 14:08:18Z | **仍佔據** `stage5_native_baseline/seed_*/medium/`（**這一列自始至今為真，未變**） |

> **⚠ 更新 2026-08-15（owner 決定）。** 上表 C1-capped 與 C2-capped 兩列已改寫；
> 原文分別記為「**已被覆寫**」與「**佔據** `stage3_baseline/seed_*/medium/`」，
> **兩者自 2026-08-15 起皆不成立**。**C2-native 那一列不受影響，仍然為真。**
>
> **現在的 canonical 狀態是混合的（measured）：**
>
> | canonical 路徑 | 現在放的是 |
> |---|---|
> | `stage3_baseline/seed_*/medium/`（**capped**） | **campaign 1**，五個 seed 全部（mtime 2026-08-11T08:34–08:37Z） |
> | `stage5_native_baseline/seed_*/medium/`（**native**） | **campaign 2**，五個 seed 全部（mtime 2026-08-12T14:04–14:08Z） |
>
> **這個混合狀態是已知、已接受、刻意的**——owner 明示不予調和，理由是**新的 campaign 取代兩者**。
> **不要把它當成待修的不一致。** 兩個 campaign 的 artifact 都仍保存在 canonical 之外，
> **沒有任何資料被刪除或搬走**。

¹ seed 24001–24004 於 12:00–12:03Z；seed 24005 於 13:18–13:19Z（該 seed 的 native 搜尋較晚結束，見 §15.2）。

`medium_recheck_summary.json → finished_utc = 2026-08-12T14:08:19Z`、`card = GPU-4c517496fc501205`、
`hip_index = 5`。

### 6.2 兩者不一致，且 C2 對受測臂更有利

| | capped C1 | capped C2 | native C1 | native C2 |
|---|---:|---:|---:|---:|
| median `F/G` | **0.9971** | **1.0274** | **1.1391** | **1.0041** |
| 為正的 seed 數 | **2/5** | **3/5** | **3/5** | **3/5** |
| 幾何平均 | 0.8931 | 1.0240 | 0.9846 | 0.9115 |
| `mean \|ln(F/G)\|` | 0.4419 | 0.0309 | 0.6666 | 0.1250 |
| dropout 率（< 0.95 × 該臂 max） | **45.7 %** | 24.3 % | **47.1 %** | 31.4 % |

**capped 上，C2 在中位數與為正計數兩項上都比 C1 更有利於受測臂**（1.0274 / 3-of-5 對 0.9971 / 2-of-5）。
**這正是 design §13.3 認定 campaign of record 這件事必須被明確裁決的理由。**

跨 campaign 的 per-seed 一致性（`ln(F/G)` 的 Pearson 相關，n = 5）：
capped C1 vs capped C2 **r = +0.756**；native C1 vs native C2 **r = −0.356**。
⚠ 兩者的離散度相差 19×（capped C1 sd 0.583 vs C2 sd 0.030），故此相關**不可**被讀成重現性度量；
列出僅為記錄。design §13.9 明列「跨 campaign 重現性的對比僅建立在 **n = 2** 個 campaign 上」。

### 6.3 覆寫是**就地**、**在解盲後**、且**未留痕**

- C2 於 2026-08-12 14:01–14:04Z（design §13.3 所記；由 raw timestamp 重建為 14:00:41Z–14:08:18Z 涵蓋兩個
  P0 level）**就地覆寫**了 canonical path 上的 C1 artifact。
- **canonical path 上沒有留下任何 `superseded_*` 標記。** `[CODE AUDIT]` 目錄列表：
  `stage3_baseline/seed_24001/medium/` 只有 `champion_interleaved{,_raw,_status}` 三個 live 檔，
  無任何 `superseded_*`。
- **該慣例是存在的**，所以缺席是有意義的：
  `stage5_native_baseline/seed_24005/medium/` 有
  `champion_interleaved_status.superseded_20260812T131801Z.json` 與
  `…superseded_20260812T131830Z.json`；`stage5_native_baseline/seed_24001/medium/` 有
  `…superseded_20260812T120004Z.json`。**這些標記對應的是 native remeasure 自身的重試，
  不是 14:04Z 的 campaign-2 覆寫**——後者在兩個 canonical path 上**都**沒有留下標記。
- 因此「讀 canonical path」的腳本會**默默回報 canonical 上當時擺著的那個 campaign**，
  而輸出中沒有任何東西說明它讀了哪一個。
  **在 2026-08-12 至 2026-08-15 之間，那就是對受測臂更有利的 C2。**

> **⚠ 更新 2026-08-15：這個危害的方向反轉了，但危害本身沒有消失。**
> canonical capped 現在放的是 **campaign 1**，所以「讀 canonical」的腳本現在
> **默默回報 C1**——**若它把讀到的東西標成 C2，那就是一個無聲的錯標**。
> **這件事已經實際發生過：** `scripts/s14_medium_ratio_analyze.py` 的 `canonical_c2()`
> 讀的正是 canonical，且其 `started_utc >= "2026-08-13"` 的守衛
> **對 campaign 1 永遠不會觸發**（campaign 1 全部 started 於 2026-08-11），
> 所以它**把 campaign 1 的數字當成 campaign 2 回報，沒有任何錯誤訊息**。
> **已於 2026-08-15 修好**：改讀 `preserved_campaign2_20260815T000000Z/`，
> 缺 artifact 時 **fail closed**（非零 exit），並改由腳本自身位置推導 run root。
> **教訓不變：不要用 canonical path 當 campaign 的身分。**

### 6.4 `analyze_medium.py` 現在要求顯式 `--campaign`

`[CODE AUDIT]` `analyze_medium.py:2–33, 41–57, 59–62, 120–124`（**行號已於 2026-08-15 隨檔案更新**；
原引 `5–25, 42–46, 100–105`）：

```
ap.add_argument("--campaign", choices=("1", "2"), required=True, …)
…
except FileNotFoundError:
    sys.exit(f"campaign {ARGS.campaign} artifact missing for seed {s}: {path}\n"
             "refusing to silently fall back to the other campaign")
```

腳本 docstring 明寫其存在理由：*"a script that simply reads the canonical path silently reports
whichever campaign happens to occupy it — between 2026-08-12 and 2026-08-15 that was the campaign
MORE FAVOURABLE to the treated arm — with nothing in its output saying which campaign it read. That
is the exact failure mode the pre-registration exists to prevent, so the choice is now an explicit,
recorded argument rather than a default."* 它**既不預設、也不平均**，並在自己的表頭印出所選 campaign
與解析後的路徑。

> **⚠ 引文更新 2026-08-15。** 本節先前逐字引用的是**舊版 docstring**，其中兩處事實已不成立：
> 它寫 campaign 2「**occupies the canonical path**」，並記 measurement of record 為
> **`PENDING_HUMAN_DECISION`**。**兩者自 2026-08-15 起皆為假。**
> docstring 已就地更正，上方引文取自更正後的版本。
>
> **同時更正的還有兩條路徑常數：** `--campaign 1` 與 `--campaign 2`
> **現在都從明示的 off-canonical 路徑讀取**，這支腳本**不再讀 canonical**——
> 因為 canonical capped 現在放的是 campaign 1，繼續讀它會讓 `--campaign 2`
> 默默回傳 campaign-1 的數字。
> **`--campaign 2` 在 seed 24004 會 fail closed 並以非零 exit 中止，那是正確行為。**

### 6.5 治理狀態

- ~~design §13.3 **提議** campaign 1 為 measurement of record。該提議屬 `PENDING_HUMAN_DECISION`。~~
  **—— 已於 2026-08-15 由 owner 結案，但結案方式不是拔擢 campaign 1，見下。**

> ## **治理狀態更新（owner 決定，2026-08-15）**
>
> - **canonical capped medium 五個 seed 一起 revert 回 campaign 1**；
>   campaign 2 於 revert 前先保存到 `preserved_campaign2_20260815T000000Z/`
>   （**seed 24004 除外——無 artifact，不可回復**）。
> - **canonical native medium 仍為 campaign 2。這個混合狀態刻意不予調和**（§6.1）。
> - **campaign 1 與 campaign 2 都不是 measurement of record。**
>   owner 的立場是**一個新的 campaign 取代兩者**，那才是有意義的量測；
>   該 campaign 目前為 **pilot only**，完整 campaign 延後且以 pilot 結果為條件
>   （`PENDING_HUMAN_DECISION`）。
> - **沒有任何資料被刪除或搬走。**
>
> **本附冊的處置因此完全不變：兩個都報告；不平均；不擇一；兩者皆不產生 tier。**
> **這一點不因 canonical 上擺的是哪一個而改變**——canonical 的位置從來就不是本附冊的判準。

- design §9.3（index 鏡射）第 3 項待裁決事項原文為：*Ratify campaign 1 as the measurement of record,
  and file the operational-correction record for the untracked in-place overwrite*。
  **前半（ratify）已被上述裁決取代（兩者皆非 measurement of record）；
  後半（operational-correction record）狀態未變。**
- **C1 為何比 C2 髒 1.7×：未解釋**（design §13.9 殘餘不確定性）。本附冊亦無法解釋。`NOT_EVALUATED`。

---

## 7. 量測缺陷——症狀

### 7.1 雙峰，而非重尾

對同一個*固定 champion config*、在單一 process、單一張卡、**20.2–26.5 秒**視窗內所做的七次重播，
呈現**雙峰、約 2–6× 的散布**（§3.3、§4.3 的完整表）。

- 每次 launch 的吞吐量在大約 **{~5,000, ~14,000} GFLOP/s** 之間呈雙穩態。
- **這不是順序、warm-up 位置或熱效應的產物**：在 capped C1 seed 24002 arm G 內，模式在 7 次 repeat 間
  翻轉為 `high, high, high, low, high, low, high`，各次間隔約 2 秒，且整個 14 次量測跨度僅約 25 秒。
- **這是 medium 特有的**（同一協定、同一 remeasure 腳本）：

  | shape | 視窗長度 | max÷min 範圍 | dropout（< 0.95 × 該臂 max） | dropout（< 0.80） |
  |---|---|---|---:|---:|
  | **medium** | 20.2–26.5 s | **1.01–6.06×** | 見 §7.2 | 見 §7.2 |
  | large | 102.1–111.3 s | 1.024–1.053× | **1 / 70** | **0 / 70** |
  | tiny | 34.7–38.1 s | 9/10 為 1.002–1.036×，一個 12.737× | **1 / 70** | **1 / 70** |

  *來源：`stage3_baseline/seed_*/{large,tiny}/champion_interleaved_raw.jsonl`。*
  large 在 `< 0.95` 下的那 1/70 是 `min/max = 0.9497` 的邊界點，**不是**模式 dropout；
  在 index §7.1a 使用的 `< 0.80` 門檻下 large 為 **0/70**。
  tiny 的那 1/70 是 `stage3_baseline/seed_24004/tiny` arm G 第 7 次：`0.3013` 對最大值 `3.837`，
  比值 **0.0785**，量於 **hip 7**——**同一簽名的 dropout 在 GPU 5 以外的保存資料中本就已經存在。**

### 7.2 dropout 率——四個資料塊

dropout 定義：**低於該臂 7 次中最大值的 95 %**。

| 資料塊 | dropout | 率 |
|---|---:|---:|
| capped C1 | 32 / 70 | **45.7 %** |
| native C1 | 33 / 70 | **47.1 %** |
| **campaign 1 合計** | **65 / 140** | **46.4 %** |
| capped C2 | 17 / 70 | 24.3 % |
| native C2 | 22 / 70 | 31.4 % |
| **campaign 2 合計** | **39 / 140** | **27.9 %** |
| **四塊全部** | **104 / 280** | **37.1 %** |

*來源：四份 `champion_interleaved_raw*.jsonl` 共 280 筆。*
這與 index §7.1a 的 `CORRECTION 2026-08-13（third pass）` 完全相符：
*"campaign 1 才是記錄在案的量測（§13.3），其汙染率為 46.4 %（capped 45.7 %、native 47.1 %）；
四組全部合併是 104/280 = 37.1 %"*。
> **門檻的敏感度（如實記錄）：** 若改用 `< 0.80 × 該臂 max`，唯一改變的是 native C2 的一個點
> （21 而非 22），合計變為 103/280。其餘三塊在兩種門檻下計數完全相同——這本身就說明分布是**雙峰**，
> 兩個門檻之間幾乎沒有樣本。

### 7.3 `η_medium` 並不描述這些量測

依 Lock A 自己的定義（`P95(|log y − median_r log y|)`，`numpy` percentile `method='linear'`）
直接由 remeasure repeats 重算：

| 資料塊 | 經驗 P95 \|log residual\| | vs 釘住的 `η_medium = 0.0041953` |
|---|---:|---:|
| capped C1 | **1.2098** | **288×** |
| capped C2 | 1.1388 | 271× |
| native C1 | **0.8915** | **213×** |
| native C2 | 0.8522 | 203× |
| pooled C1（140 點） | 0.9990 | 238× |
| pooled C2（140 點） | **1.0503** | 250× |
| **clean mode，C2**（≥ 95 % 該臂 max，**101/140 = 72 %**） | **0.0116** | **2.8×** |
| clean mode，C1（**75/140 = 53.6 %**） | 0.0113 | 2.7× |

capped C1 的 **1.2098** 與 pooled C2 的 **1.0503** 與 index §7.1a 逐位相符；clean-mode 的
**101/140 = 72 %、P95 = 0.0116** 亦逐位相符。

> **與工作筆記的數值調節（必須寫明，因為兩組數字都出現在流通中的文件裡）。**
> 工作筆記記為「native 0.828、capped 1.196」。經核對，那是**同一組殘差**在
> `method='lower'`（取下界序位）下的 P95：native C1 = 0.8282、capped C1 = 1.1964。
> `noise/per_shape_noise.json → eta_s_formula` 明訂 `method='linear'`，故本附冊採用 linear 值
> （0.8915 / 1.2098），並在此保留 lower 值以免工作筆記的數字看起來無來源。
> **兩者都不改變結論**：實現的重複性比 gate 所依據的 η 差約 **200–290×**。

**但「調高 η」是錯的修法。** 那會為了吸收一個汙染物而放寬*所有東西*的容差，毀掉 gate 在那 72 %
正常樣本上的檢定力。缺陷不在 noise margin 估錯，而在於**約 28–46 % 的量測完全來自另一個母體，
而協定沒有任何機制去偵測或排除它們**。

**三個 pin 都是 pilot 的意外，不是雜訊模型**（design §13.4）。本附冊獨立重算 pilot 殘差，逐項確認：

| shape | pilot anchor 中位數（GFLOP/s） | 各 anchor max÷min | pilot dropout（< 0.95） | RBS |
|---|---|---|---:|---:|
| **medium** | 4,629.10 / 3,199.94 / 2,127.04 | 1.009 / 1.003 / 1.004 | **0 / 21** | 4096 |
| large | 213,192 / 180,336 / 62,111.7 | **1.237 / 1.420** / 1.025 | 12 / 21 | 0 |
| tiny | 2.13 / 0.75 / 0.52 | **5.126** / 1.016 / 1.060 | 4 / 21 | 4096 |

*`[CODE AUDIT]` `260807-s14-baseline-run/stage2_noise/raw_repeats.jsonl`
（欄位 `size`、`anchor_index`、`repeat`、`gflops`、`rbs_used`、`client_wall_seconds`）。*

- `η_medium` 來自一批 **0/21 dropout** 的 anchor，且它們比 champion 自己的 clean mode 還**緊 2.8×**。
- `η_tiny = 0.4466` 由 tiny anchor 1 的**單一深度掉點**（0.42 對比 2.13 的模態）製造。
- `η_large = 0.1228` 由兩個 max÷min 為 **1.237** 與 **1.420** 的 anchor 撐著，而 large 的 champion
  remeasure 是 1.024–1.053——**重現不出來**。

這三列與 design §13.4 的表逐項相符，且是本附冊由 primary artifact 獨立重算的。

### 7.4 `RETRACTED`——index §7.1 原有的一句話

index §7.1 原本寫：*"these are genuine champion differences, not measurement noise"*，
理由是 per-seed F/G 的散布（0.36×–2.12×）遠大於 `η_medium = 0.42 %`。

**`RETRACTED 2026-08-12`，與原始 artifact 矛盾。** 同一個 config、同一個 process、同一張卡、約 25 秒內：
capped C1 seed 24001 arm F 的七次為 `13,456 · 2,234 · 13,535 · 13,404 · 13,547 · 13,456 · 13,527`
（max÷min = 6.06×）。**取代它的陳述是：** medium 的 per-seed `F/G` 值**不能**被詮釋為 champion 品質；
7 次的中位數本身就是一個來自寬雙峰分布的抽樣。此撤回在本附冊中維持**同等效力**。

**連帶後果（design §13.6 明列，必須照實記錄）：** design §12.2(B)2 為 native addendum 納入 medium 所給的
理由——*「medium 是唯一兩臂差異可被量測的 shape，per-seed F/G 0.36×–2.12×」*——**作廢**，
因為那些數字正是汙染物。**須以 amendment 更正 design。** 但請注意兩件仍然成立的事：
(a) native medium 的 run 本身有效且乾淨（§1.4）；(b) **Q3（Gen0）完全不依賴 champion 量測，不受影響**
（design §13.6 明文）。

---

## 8. 量測缺陷——根因

**根因是機制性的，已定位，且不是 medium 這個 problem size 的性質。**

> **⚠ 2026-08-18 補記：根因已由一次實際修復示範過，且機制被進一步分離。**
> §8.1–§8.2 用 sweep 論證「warm-up 是以次數而非時間指定」。2026-08-17 的修復把暖機從 321
> 提到 **1400**（`RBS` 同時降到 401 以保住 production 的 `rotatingNum = 320`），
> dropout 從 **39.05 %** 降到 **7.50 %**，per-seed sd 從 0.25–0.43 降到 0.0016–0.0194
> （逐 seed 18.7–99.9 倍）——**根因不只被定位，還被治好了。**
> **而且兩個變因已經分離開：** 只加 `RBS` cap、暖機不動（基準格 B，`321 / 401`）時
> dropout 是 **40.60 %**，**比未修改的 39.05 % 還高 1.55 pp，沒有觀察到任何降低**；
> 反過來把 `RBS` 釘死在 production 的 4096、只提暖機，dropout 從 321 的 **42 %**
> 降到 1400 的 **4.0 %**（n = 50）。
> ⇒ **降噪來自暖機次數，不是 rotating footprint。** 完整證據見 **§18.2**。
> ⚠ 支撐這個機制結論的是**量級差距**（1.55 pp 對 31.55 pp），**不是等價性檢定**；
> 資料未排除 cap 帶來約 3 pp 的降低。

### 8.1 warm-up 是以 **enqueue 次數**、而非**時間**指定

`[CODE AUDIT]` `ClientParameters.ini`——**三個 shape 完全相同**：

```
num-enqueues-per-sync=321
max-enqueues-per-sync=-1
num-warmups=321
sleep-percent=50
rotating-buffer-size=4096     # large 為 0
```

*來源：`stage3_baseline/seed_24001/{medium,large,tiny}/1_BenchmarkProblems/*/00_Final/caches/510d597cb070/source/ClientParameters.ini`，
以及 `…/medium/remeasure_work/{G,F}/…` 下的同名檔（remeasure 路徑用的是同一份設定）。*

但 kernel 時長相差三個數量級，所以同一個**次數**買到的**時間**天差地遠：

| shape | kernel 時長 | warm-up 牆鐘時間 = 321 × kernel | 結果 |
|---|---:|---:|---|
| **medium** | **~9.9 µs**¹ | **~3.2 ms** | 28–47 % dropouts |
| large | ~1.87 ms | ~600 ms | 0/70（< 0.80） |
| tiny | dispatch-bound（~4.1 µs） | ~1.4 ms | 1/70——但**對 clock 不敏感**（§8.4） |

¹ 由 artifact 導出：`TotalFlops = 134,217,728` ÷ 13,500 GFLOP/s（暖機後水準）= **9.94 µs**。
對照同一 CSV 記錄的汙染單次值：`WinnerGFlops = 2961.87`、`WinnerTimeUS = 45.3151`——**約 4.6× 的落差**，
與一張跑在約 450 MHz 的卡一致。
*`[CODE AUDIT]` `stage3_baseline/seed_24001/medium/1_BenchmarkProblems/*/Data/00_Final.csv`。*

**閒置的 MI300X 停在 132–180 MHz，需要數十毫秒的持續工作才會升到約 2100 MHz。** medium 的 3.2 ms
warm-up 在卡還在爬升時就結束了，於是計時視窗打開時 GPU 只升壓到一半；`hipEvent` 計時涵蓋全部 321 次
enqueue，所回報的 GFLOP/s 因此是**對一張部分升頻之卡的平均**。
**爬升是否來得及完成由 power governor 決定——這正是結果呈雙峰、而非重尾的原因。**

DPM 地板的算術與此一致：`180/2100 = 0.086` 是最差可達比值；所有 shape 上觀察到的 dropout 都落在
`[0.0742, 0.7847]` 之內，最深的幾個（medium 0.19–0.24；tiny 0.0742 與 0.0785）恰好坐在該地板上。
> **誠實但書（index §7.1b 所記）：** 下端 0.0742 出自 `tiny_gpu5_probe_summary.json` 中的一個 tiny
> dropout，而**那個點本身就是決定該界線的點**，所以「符合 `~165/2100 = 0.0786`」這個讀法是把 clock
> 比值**夾在中間**，不是證實它。

### 8.2 warm-up sweep——決定性證據，以及**兩項實質 caveat**

獨立 probe：同一個 `tensilelite-client` binary、同一個已編譯的 champion kernel、同一個 problem size，
直接由停放的 `remeasure_work/G` 樹驅動；每個變體改**一個**旋鈕、**25 個全新 process**、GPU 5、idle-gated。

| warm-ups | ≈ 計時前 GPU 工作 | median GFLOP/s | max/min | dropouts |
|---:|---:|---:|---:|---:|
| 321 | 3.2 ms | 14,001.0 | 7.907 | **12/25（48 %）** |
| 642 | 6.4 ms | 14,136.4 | 6.364 | 8/25（32 %） |
| 1,284 | 13 ms | 14,188.6 | 2.449 | 3/25（12 %） |
| 2,568 | 26 ms | 14,331.7 | 1.874 | 2/25（8 %） |
| **5,136** | **51 ms** | **14,328.6** | **1.013** | **0/25（0 %）** |
| 10,272 | 103 ms | 14,362.7 | 1.034 | 0/25（0 %） |
| 20,544 | 205 ms | 14,375.4 | **1.321** | **1/25（4 %）** |

*`[CODE AUDIT]` `medium_mechanism_probe_summary.json → variants.W{321,642,1284,2568,5136,10272,20544}_norot`
（`median`、`max_over_min`、`n_below_0p95`、`overrides`）；`medium_mechanism_probe/sweep_stdout.log`。*
（`medium_remeasure_root_cause.md` §2 的 5,136 列記為 `14,332`；artifact 記為 `14,328.6`。
其餘六列逐位相符。此處採用 artifact 值。）

在 ~50 ms 處有一個乾淨的拐點。**該暫態是一個固定的牆鐘長度（數十毫秒）**——那是 power/DPM
promotion ramp 的簽名，不是任何隨已完成工作量縮放的東西。

> **CAVEAT (i)——sweep 在拐點之上並非單調。** 20,544 次 warm-up（205 ms）仍然回傳 **1/25（4 %）**，
> `max/min = 1.321`。**因此「越長越好」不成立**，而所提出的機制無法解釋這一點。
>
> **CAVEAT (ii)——sweep 的每一個點都跑在 `rotating-buffer-size = 0`，不是釘住的 4096。**
> 光是 RBS 0 就把水準從 12,430 推到 14,153（**+14 %**），所以整個 sweep 量的是**一個不同的 estimand**。
> 而**兩個 RBS-4096 的長 warm-up 變體 25/25 全數 crash**：
>
> ```
> B_longwarmup  (num-warmups=32100,          RBS 4096) : 25/25 rc=-6
> C_longwindow  (num-enqueues-per-sync=32100, RBS 4096) : 25/25 rc=-6
> hipModuleLoad failed: …/client_tree/library/gfx942/Kernels.so-000-gfx942.hsaco error: file not found
> terminate called after throwing an instance of 'std::runtime_error'
>   what():  Insufficient rotating buffer size.
> ```
>
> *`[CODE AUDIT]` `medium_mechanism_probe/stdout.log:25–217`，共 50 次 `rc=-6`。*
> **因此這個修法在 production 設定（RBS = 4096）下未經驗證。**
> design §13.3／§13.7 提議的可行性 probe——**5,136 warm-ups @ 釘住的 RBS = 4096**（≈58 ms，越過拐點）
> ——**⚠ 更正（2026-08-18）：原文寫「從未被嘗試過」與「結果為 `NOT_EVALUATED`」，兩句都是假的，
> 而且寫下時就已經錯了。** 該 probe **已於 2026-08-13 執行**
> （`medium_clockladder/capped/seed_{24001,24004,24005}/s4_warmup5136/probe_20260813T131304Z.log`），
> **三個 seed 全部 `rc = 1`**。**但死因不同，不可寫成同一個機制：** seed **24001 與 24005**
> 走到了那次配置並顯示 `Rotating buffer set to: 4294967296. Rotating num: 3272` 與
> `1312256 * 3272 = -1265664`——**int32 環繞由引擎自己印出的負數確證**；
> seed **24004 在到達該配置之前先中止**（同檔 `:623`，library 連結錯誤），**與溢位無關**。
> ⇒ 正確狀態是 **`EVALUATED / closed by infeasibility`**，與 index §9.5 及 ledger
> `CAPABILITY-ENDPOINT-PACKET-20260813` 的既有記錄一致。
> **本段的結論（此修法在 production 的 RBS = 4096 下未經驗證）仍然成立，錯的只有它給的理由。**
> 另見 §18：2026-08-17 驗證的是 **`RBS = 401`**，不是 4096。
> 兩個 crash 的變體用的都是 32,100。
> *（觀察，非結果：crash 的例外字串是 `Insufficient rotating buffer size.`，而 root-cause memo §4 的算式
> 為「321 個 rotating buffer × ~1.31 MB = ~420 MB」。若逐 enqueue 線性外推，5,136 在 4096 MB 下同樣會
> 超出——**但這是推論、未量測**，不得取代該 probe。）*

單旋鈕變體對照（同一 probe，production 設定為基準）：

| 變體 | 改動 | median GFLOP/s | max/min | dropouts |
|---|---|---:|---:|---:|
| `A_baseline` | production 設定 | 12,430.1 | 5.243 | **12/25（48 %）** |
| `E_nosleep` | `sleep-percent = 0` | 12,465.7 | 2.317 | 10/25（40 %） |
| `D_norotating` | `rotating-buffer-size = 0` | 14,152.8 | 30.603 | 6/25（24 %） |
| `C2_longwindow_norot` | 32,100 計時 enqueue + RBS 0 | 14,172.2 | 1.101 | 2/25（8 %） |
| **`B2_longwarmup_norot`** | **32,100 warm-ups + RBS 0** | **14,333.6** | **1.018** | **0/25（0 %）** |

*`[CODE AUDIT]` `medium_mechanism_probe/stdout.log:5–13`。*

### 8.3 已排除的假說

- **Rotating buffer / cache residency——`ELIMINATED` 為病因。** `rotating-buffer-size = 0` 仍有 24 %
  dropouts，而長 warm-up 的修法在 RBS = 0 下即生效（0 %）——RBS **既非必要亦非充分**。
  它是另一個**純確定性**的效應：RBS 4096 讓 medium 確定性地慢約 12–14 %（12,430 vs 14,153），
  因為 321 個 rotating buffer × ~1.31 MB ≈ 420 MB 的工作集超出 MALL。
- **量測之間的 sleep——`ELIMINATED`。** `sleep-percent = 0` 仍有 40 % dropouts。
- **Config 專屬性——`ELIMINATED`。** 兩臂、全部十個 seed-arm 都掉；獨立 probe 在**單一固定 config**、
  單一目錄下重現 48 % dropouts。
- **Host CPU 負載——已排除、未再爭辯。** 當日 probe 在 224 核的 8–23 % 負載下、通過未修改的
  `require_idle()` gate 執行，並重現了缺陷。
- **卡別——見 §8.4**（論證已被更換）。

### 8.4 卡別平反——`ARGUMENT SUPERSEDED 2026-08-13`

> **原論證（tiny-on-hip-5）已被撤回，其結論由另一條證據承載。必須照實記錄兩者。**

**原論證：** 在 hip 5 上重測 `tiny` 得到 **2/70** dropouts，對照 Lock-A 卡上的 **1/70**，
而 medium 在 hip 5 上是 28 %——故 GPU 5 與其他卡無實質差異。
*`[CODE AUDIT]` `tiny_gpu5_probe_summary.json`（2/70，最低比值 0.0742）；
`stage3_baseline/seed_*/tiny/champion_interleaved_raw.jsonl`（1/70，最低比值 0.0785，於 hip 7）。*

**`ARGUMENT SUPERSEDED 2026-08-13`：** 這一項幾乎沒有內容。tiny 隨後被證明**對整個機制不敏感**——
它的吞吐量對 warm-up 長度**不變**（321 與 20,544 次 warm-up 都是 **4.0 GFLOP/s**），因為在 16,384 FLOP
之下它純粹是 dispatch latency，由 command processor 處理，不受 shader clock 節制。
**因此 hip 5 上 tiny 乾淨，是「不論 hip 5 有沒有 clock 病理都會看到」的結果**；
它只排除了嚴重的卡故障，再細就排除不了了。

| tiny 變體（GPU 5 獨立 probe） | median GFLOP/s | max/min | dropouts |
|---|---:|---:|---:|
| `A_baseline`（321 warm-ups, RBS 4096） | 3.8 | 1.07 | 1/25 |
| `W321_norot` | 4.0 | 1.05 | 0/25 |
| `W5136_norot`（51 ms warm-up） | 4.0 | 1.69 | 1/25 |
| `W20544_norot`（205 ms warm-up） | 4.0 | 1.015 | 0/25 |

*來源：`medium_remeasure_root_cause.md` §3；raw 於 `tiny_mechanism_probe/`。*

**取代它的、承重的證據是「同卡、同 shape」的 within-card pilot contrast：**

| | 卡 | client | RBS | anchor／champion 速度 | warm-up 牆鐘 | dropouts |
|---|---|---|---:|---|---|---:|
| medium **noise pilot** | `HIP_VISIBLE_DEVICES=5` | 同一份 | 4096 | 4,629 / 3,200 / 2,127 GFLOP/s，比 champion **慢 2.9–6.3×** | **≈9.3–20.3 ms**¹ | **0 / 21** |
| medium **remeasure** | hip 5 / `GPU-4c517496fc501205` | 同一份 | 4096 | champion ~13,500 GFLOP/s | **~3.2 ms** | **28–47 %** |

¹ 由 `TotalFlops / GFLOP/s × 321` 導出（29.0 / 41.9 / 63.1 µs × 321）。
`medium_remeasure_root_cause.md` 記為 8.6–21 ms；差異來自所取的 anchor 統計量，區間結論相同。
*`[CODE AUDIT]` `260807-s14-baseline-run/stage2_noise/driver_status.json → HIP_VISIBLE_DEVICES = "5"`；
同目錄 `raw_repeats.jsonl`。*

**同一張卡、同一個 shape、同一個 kernel、同一個 client、同樣 RBS 4096——所以卡不可能是那個具鑑別力的
變數。** 兩者之間唯一不同的是 warm-up 的牆鐘時間，而那正是所提出的機制。**hip 5 獲得平反，
靠的是這第二個測試，不是第一個。**

> **CAVEAT：** 2026-08-10 的重開機改變了 GPU 編號，所以 08-07 的 index 5 未必是 08-12 的同一顆實體晶片。
>
> **CORRECTION（root-cause memo §4 內文）：** *"tiny was never perfectly clean"*——
> `stage3_baseline/seed_24004/tiny` arm G 第 7 次為 `0.3013` 對最大值 `3.837`，比值 **0.079**，
> 量於 **hip 7**。同一簽名的 dropout 在 GPU 5 以外的保存資料中本就已經存在。

### 8.5 鎖頻——`ATTEMPTED, NOT ACHIEVABLE`，且必須記錄

決定性的確認會是用 `rocm-smi --setperflevel high` 把 clock 釘住。
`/sys` 在容器內是**唯讀**、host 上無 sudo，故 `power_dpm_force_performance_level` 始終停在 `auto`，
所謂「pinned」臂**實際上是第二個 control**。

| condition | dropouts（< 0.95 × 該臂 max） |
|---|---:|
| `control_auto` | **24 / 70** |
| `pinned_high` | **23 / 70** |

*`[CODE AUDIT]` `medium_clock_probe_summary.json`（`started_utc = 2026-08-12T14:34:28Z`、
`finished_utc = 14:42:45Z`、`card = GPU-4c517496fc501205`、`hip_index = 5`；
兩個 condition 的 `results.*.spread.{G,F}.repeats` 逐點重算）；驅動程式
`scripts/s14_medium_clock_probe_driver.py`。*

**它的 23/70 是一次複製，不是一次反證。**
> **`CORRECTED 2026-08-13`（root-cause memo §4）：** 該數字先前被寫成 **25/70**；
> 由 `medium_clock_probe_summary.json` 重數為 `control_auto 24/70` 與 `pinned_high 23/70`。
> **本附冊採用更正後的數字，並已獨立重算確認。**

**因此 clock 機制是靠 warm-up sweep、DPM-floor 的算術，以及 tiny 被量到的 clock 不敏感性支撐的
——不是靠直接把 clock 釘住。** 直接鎖頻是唯一未能執行的確認；它需要有特權的容器（`/sys` 可寫）
或 host root，約十分鐘、**零研究 GPU 時數**（design §9.3 第 1 項、§13.7 owner action）。

**兩個誠實 caveat（design §13.7）：** 鎖頻**不是修復**（生產環境不能鎖），故該處為 null 不足以否定
warm-up 說；且先前那次嘗試必須如實報告為**第二個對照組**（`setperflevel high` 後讀回仍是
`Performance Level: auto`，23/70 對 24/70，sclk residency 相同）。

### 8.6 `medium_remeasure_root_cause.md` 上兩個 `CORRECTED 2026-08-13` 區塊——照實搬運

1. **§4 內：** `25/70` → **`23/70`**（見 §8.5）。已採用。
2. **§6 內：** 該段先前把 `2,961.87` 誤認為 champion 的 GA fitness，**由此建立的推論被 struck**。
   - `2,961.87` **不是** GA fitness。它是**單次的 champion-verification 值**，即
     `1_BenchmarkProblems/*/Data/00_Final.csv` 的 `WinnerGFlops`，也就是 resolver 記為
     `selection_candidates[0].original_final_gflops` 的那個值。
   - 該臂真正的 GA fitness 是 `optimization_result.json → best_fitness = 13,679.099609375`
     ——**與 remeasure 及 standalone 同一家族**，不是差 4.5×。
     *`[CODE AUDIT]` `stage3_baseline/seed_24001/medium/optimization_result.json`，本附冊重讀確認。*
   - **被 struck 的推論是：** *"`R_s(medium) = 3199.94` 在 GA 尺度上，所以 GA 路徑與 remeasure 路徑
     各自內部一致但相差約 4.5×"*。**沒有兩個尺度。** `best_fitness` 與 remeasure 一致；
     異常的是**一次在冷卡上取得的單次驗證量測**，即本 memo 所談的那種普通汙染。

---

## 9. Arm-asymmetric 汙染——直接觀測到，而非推論

> **`RETRACTED`：** index 先前主張「既然汙染嚴格是單向的，它也就是 arm-symmetric 的，因此會在配對的
> `F/G` 比值中抵銷」。**該主張不成立。**

`[CODE AUDIT]` 每個 medium 臂的 champion 驗證值 `WinnerGFlops`——同一條 client 路徑，每臂一次量測：

| seed | baseline (G) | guided (F) |
|---|---:|---:|
| 24001 | **2,961.9** | 13,590.7 |
| 24002 | **8,846.0** | 12,773.8 |
| 24003 | **4,210.4** | **8,384.2** |
| 24004 | 12,516.2 | 14,040.5 |
| 24005 | 11,542.6 | 13,359.8 |
| **median** | **8,846.0** | **13,359.8** |

*`[CODE AUDIT]` `stage3_{baseline,guided}/seed_*/medium/1_BenchmarkProblems/Cijk_Ailk_Bljk_BBS_BH_Bias_HA_S_SAV_UserArgs_00/Data/00_Final.csv`
→ `WinnerGFlops`（本附冊由 CSV 逐檔重讀）。*
> **⚠ 不得使用 `**/Data/00_Final.csv` glob**——它也會命中 `remeasure_work/{G,F}/…` 的副本，
> 單是 seed 24001 arm G 就會回傳三個值（2961.87、6195.34、13436.4）而非那一個 champion 驗證值。
> 上表用的是頂層 `1_BenchmarkProblems` 的 CSV，也就是
> `resolution_provenance.selection_sources.candidate_matrix_csv` 所指的同一個檔。

baseline 臂被劣化的頻率遠高於 guided 臂。**此處刻意不給出「被汙染的臂」的計數**：那取決於對單次數值所
假設的乾淨參考值，而 design §13.6 記錄兩位 reviewer 分別數成 3/5 與 4/5。中位數本身已足以說明重點。

**正確的措辭，取代先前的主張：**
- 汙染是**單向的**（暫態只能讓量測變慢，沒有機制讓它變快）。
- **它是否為 arm-symmetric 是 `NOT_EVALUATED`**，且**無法回溯檢查**——per-generation 的 benchmark CSV
  沒有保留（每個 seed 只存活一份 `00_Final.csv`，單一 solution 欄）。
- **`NOT_EVALUATED ≠ arm-symmetric`，也 ≠ 不對稱。** 它就是未評估。

**警告（design §13.6 要求報告必須明說，以免未來讀者去取用）：**
**`original_final_gflops` 絕不可被當成 endpoint。** 以這些數字來看，guided 臂會**純粹因為汙染**
而顯得好得驚人（中位數 13,360 vs 8,846）。它不是 endpoint——endpoint 是 7× interleaved remeasure。

---

## 10. GA 搜尋的曝險——`ARGUMENT REPLACED 2026-08-13`

GA 搜尋期間每一個候選都用同一個 321-enqueue warm-up。若暫態以同樣方式進入搜尋，會遠比一個 remeasure
缺陷嚴重。這個疑慮的處置經過一次論證更換，必須照實記錄。

**原論證（`RETRACTED`）：** 以 `best_fitness` 的落點區間，以及 Gen0→final 的梯度來論證搜尋未受影響。
**兩者都被撤回。** `best_fitness` 是約 8,500–32,000 次評估的*最大值*，恰恰是對單向*向下*汙染最穩健的
統計量——它無法證明個別候選的評估沒有被低估，而被低估的評估正是會敗壞*哪一個*候選勝出的東西；
`best_gflops_so_far` 依構造即為單調，所以模式樂透會預測到同樣的梯度觀察。

**有效的證據（`ARGUMENT REPLACED`）：**

1. **`generation_Q_median_any_valid`**——每代約 510（capped）／約 11,290（native）次評估的中位數，
   一個 28–48 % 的乘性汙染物會壓低它並使它不穩。medium 落在兩個免疫 shape 的區間**之內**：
   代與代之間的平均 |Δ|，medium **5.58 % / 4.61 %**，large 6.98 % / 6.11 %，tiny 6.50 % / 4.21 %。
   *來源：design §13.6 / index §7.1b.1；本附冊未重算此三對數字，標為引用。*
2. **一個機制性的曝險上界**——`cumulative_complete_evals` 在**同一個** client invocation 內每代推進約
   508–512，每個 solution 約 6.4 ms 的 GPU 工作，所以一個約 50 ms 的 ramp **每個 invocation 只付一次**，
   大約只曝險到約 510 個 solution 中的前 8 個（**約 1.6 %**），對比全新 process 之 remeasure 的 28–47 %。

**champion 的*解析*未受汙染，這是紀錄在案的事實，不是推論。**
`selection_candidates` 在 **40/40 個 arm-entry** 中都恰好只有一筆，而解析出的 `canonical_hash` 在
**40/40** 中都落在該臂的 `best_individual_hashes` 裡。

> **`PATH CORRECTED 2026-08-13`。** 較早的草稿引用的是 `optimization_result.json` 的
> `resolution_provenance`。該欄位在**全部 45 個**這類檔案中皆為空（`{}`）——它不在那裡。
> 可重現的路徑是 `champion_interleaved.json → arms.{G,F}.resolution_provenance.selection_candidates`
> （20 檔 × 2 臂 = **40 個 arm-entry**），再與各臂自己 `optimization_result.json` 的
> `best_individual_hashes` 對照。兩個計數在更正後的路徑下維持 **40/40 與 40/40 不變**；錯的只有引用。

那條 selection rule *確實*會讀取已被證明汙染的單次 `original_final_gflops`——但在**每一個實例中都是
空轉的**（唯一候選）。被汙染的數值有被記錄下來，但它**沒有仲裁到任何東西**。

**後果：** champion 的*選擇*與*解析*未受汙染。**搜尋過程中低殘餘率的汙染並未被排除**，
且依 §9，它是否 arm-symmetric 為 `NOT_EVALUATED`。
**這是 residual，不是 live suspicion。** 便宜的定案檢查（保留 per-generation CSV 重跑一代 medium GA，
比對欄位位置與 GFLOP/s）在 design §13.7 中排在**最後**。

**參考——全部 20 個 medium run 的 `best_fitness`（`[CODE AUDIT]`，本附冊重讀）：**

| campaign | per-seed `best_fitness`（GFLOP/s） |
|---|---|
| capped G | 13,679.1 · 12,545.4 · 15,254.5 · 12,606.2 · 13,694.5 |
| capped F | 13,826.4 · 12,815.6 · 15,328.5 · 14,122.2 · 13,448.9 |
| native G | 14,479.0 · 14,194.6 · 14,013.2 · 15,406.7 · 14,523.0 |
| native F | **14,368.7 · 14,177.4 · 14,387.1 · 13,536.1 · 15,166.2** |

*來源：`stage3_{baseline,guided}/`、`stage5_native_{baseline,guided}/seed_*/medium/optimization_result.json
→ best_fitness[0]`。*
二十個全部落在 **12,545.4–15,406.7**。（index §7.1b.1 的表只列了 15 個值，漏了 native F 這一列；
本附冊補齊，計數與該節文字所述的「20 個 run」一致。）
**但依上述 `ARGUMENT REPLACED`，這個區間本身不承載「搜尋未受汙染」的論證**——它只是記錄。

---

## 11. Q1——穩健性：capped-medium 的方向在 native Gen0 下是否成立？

*design §12.1 Q1、§12.4 第 1 點。*

### 11.1 資料

| | capped C1 | native C1 | capped C2 | native C2 |
|---|---:|---:|---:|---:|
| median `F/G` | 0.9971（−0.3 %） | **1.1391（+13.9 %）** | 1.0274（+2.7 %） | 1.0041（+0.4 %） |
| 幾何平均 | 0.8931（−10.7 %） | 0.9846（−1.5 %） | 1.0240（+2.4 %） | 0.9115（−8.9 %） |
| 為正 | 2/5 | 3/5 | 3/5 | 3/5 |
| Gen0 / gen-10 / AUC | **3/5 / 3/5 / 3/5** | **2/5 / 1/5 / 3/5** | （同 capped，與 campaign 無關） | （同 native） |
| 跨 P0 的 per-seed `ln(F/G)` 相關 | — | **r = −0.458** | — | r = −0.904 |

### 11.2 判定，two-sided

- **在 GA trajectory 的三項子判準上（不受汙染）：** capped 3/5 / 3/5 / 3/5 → native 2/5 / 1/5 / 3/5。
  **沒有任何一項在任一 P0 水準下達到 ≥4/5。** 這是可靠的、不受量測缺陷影響的讀數。
- **在 final champion 端點上：** 該端點被**提議**為 `NOT_EVALUATED / instrument-invalid`（PENDING）。
  在可用精確度下，capped-medium 的*方向*在 native Gen0 下**既未獲確認，也未被推翻**。
- **兩個 P0 水準之間的 per-seed 一致性為零。** campaign 1 的五對 `ln(F/G)` 跨 P0 相關為
  **r = −0.458**（campaign 2 為 −0.904）。若 per-seed 的 `F/G` 反映的是 treatment 的某種穩定 seed 層級
  性質，r 應強烈為正。它並非如此——這與「per-seed 數字是一場模式樂透」一致。
- ***確實*被建立的是：** native 的 run 在內部是乾淨的（§1.4），所以這個不確定性是 medium **量測**的
  性質，而不是 native 執行的性質。

**允許的 claim 措辭**（依 design §10.5、§12.5、charter §8.2/§8.5/§8.6）：

> *"On medium, at native Gen0 (11,405) as at P0-capped 512, the amended sparse prior — applied at
> ρ = 0.566 (≈71 % strength) on `DepthU` and ρ = 0.80 (100 %) on `1LDSBuffer`, i.e. over 2 of 29 free
> genes — did not reach the pre-registered ≥4/5 directional threshold on any of the three
> contamination-immune sub-criteria. The final-champion endpoint is proposed as `NOT_EVALUATED /
> instrument-invalid` (PENDING) because the 7× remeasure is not repeatable on this shape."*

**不允許：** 任何聲稱模型的 guidance 沒有幫助（或有幫助）的陳述；任何由該作廢端點導出的 tier。

### 11.3 值得記錄的次要根本原因：prior 指向的方向偏離了勝出的 `DepthU`

兩個 activated gene 的 champion 值。*`[CODE AUDIT]`
`stage{3,5_native}_{baseline,guided}/seed_*/medium/optimization_result.json → best_individuals[0]`。*

| | 24001 | 24002 | 24003 | 24004 | 24005 |
|---|---|---|---|---|---|
| native G（`DepthU`, `1LDSBuffer`） | 128, 1 | 128, 1 | 64, 1 | 128, 1 | 64, 1 |
| native F | 128, 1 | 64, 1 | 128, 1 | 64, 1 | 128, 0 |
| capped G | 64, 0 | 128, 1 | 128, 0 | 64, 0 | 128, 0 |
| capped F | 64, 0 | 64, 1 | 128, 0 | 128, 0 | 64, 1 |

- 在全部 20 個 medium champion 中，`DepthU ∈ {64, 128}`：**11× 128、9× 64、0× 32、0× {256, 512, 1024}**。
- 出貨的 prior 給 `DepthU = 128` 的抽中機率是 **0.0723**——相對於 uniform（0.1667）是 **2.3× 的降權**
  ——同時給 `DepthU = 32` **0.2096**，而該值贏了 **0/20** 次。
- 單看 **prior-free 的 baseline 臂**（對這個 shape 上實際會贏什麼的無偏讀數）：native G 的 champion 是
  `128, 128, 64, 128, 64`，且 `1LDSBuffer = 1` 在 **5/5** 上成立；而 prior 只給 `1LDSBuffer = 1`
  **0.331**、給 `0` **0.669**。
- **所以在 native medium 上，prior 在兩個 activated gene 上都指向偏離眾數勝出值的方向。**
  這不是 pipeline 的缺陷；它是 index §3.4a.2 的預期後果——`DepthU` 的 trusted 集合是 `{32, 64}`
  （其餘四個值在各自 262,144 次 S11 條件抽樣中分別只得到 38、0、0、0 個 accept），
  所以模型全部的偏好質量都被鋪在兩個值上，其中一個從未贏過，而最常贏的那個值則被 entropy floor 壓在
  殘餘的 `(1 − ρ)·p0` 份額上。這正是 index §3.4c.4 所警示、會限縮 medium null 之詮釋的機制。
- **所需的區辨性證據：** `DepthU = 128` 究竟是真的更好，還是只是更可能抽中高量測模式。
  鑑於 §7–§8，從這些 artifact 無法把兩者分開。**`NOT_EVALUATED`。**

---

## 12. Q2——稀釋：P0 = 512 與 P0 = 11,405 下的效應量

*design §12.1 Q2、§12.4 第 2 點、§12.5。*

### 12.1 跨 P0 水準什麼可比、什麼不可比

- **可比：** P0 內部的配對對比 `ln(F/G)`。在每個變體內部，兩臂共用相同的 Gen0 尺寸、相同的 `group_0`
  weights、相同的 seed、相同的 eval 預算，所以該對比在每個水準上都是無偏的。
- **之所以可比，僅因為現在兩邊都採用相同的 7× 協定**（design §12.3 的 `(b)` 補記）。native 每臂多跑約
  3.2× 的評估，其搜尋期 champion 帶有更大的 winner's-curse 偏誤；若 native 從 GA log 讀、capped 從 7×
  remeasure 讀，Q2 就會把真實的 effect-size 變化與量測協定的變化混為一談。兩邊都經過 7× remeasure、
  在同一張卡（GPU 5）、採同一個 `START_ARM = G` counterbalance。
- **不可比：** 跨 P0 水準的 champion 絕對品質（預算不同）；以及在任一水準上從 medium 的 final champion
  `F/G` 讀出的任何*量值*（§7）。

### 12.2 數字（campaign 1；campaign 2 併列）

| 統計量 | capped C1 | native C1 | 變化 | （capped C2 → native C2） |
|---|---:|---:|---|---|
| `F/G` 中位數 | 0.9971 | 1.1391 | +14.2 pp | 1.0274 → 1.0041 |
| `ln(F/G)` 中位數 | −0.0029 | +0.1303 | — | +0.0270 → +0.0041 |
| `ln(F/G)` 平均（⇒ 幾何平均） | −0.1130 (0.8931) | −0.0155 (0.9846) | 趨向 0 | +0.0237 (1.0240) → −0.0927 (0.9115) |
| 為正的 seed 數 | 2/5 | 3/5 | +1 | 3/5 → 3/5 |
| **`\|ln(F/G)\|` 平均（離散度）** | **0.4419** | **0.6666** | **+51 %** | 0.0309 → 0.1250（**+305 %**） |
| `ln(F/G)` 母體標準差 | 0.5827 | 0.7260 | +25 % | 0.0304 → 0.1558 |
| 跨 P0 的 per-seed 相關 | — | — | **r = −0.458** | r = −0.904 |

### 12.3 答案

- **在 final champion 指標上，Q2 於可用精確度下為 `NOT_EVALUATED`。** 集中趨勢朝零移動
  （幾何平均 −10.7 % → −1.5 %），而*離散度卻增加了 51 %*。這是熵更高的樂透的簽名，不是某個 treatment
  效應變小或變大的簽名。**兩個 campaign 都顯示離散度隨 P0 上升而增加，但方向與量值互不一致**
  （C2 的集中趨勢是 +2.4 % → −8.9 %，與 C1 相反）——這本身就是「該指標無法裁決」的直接證據。
  預先登錄的 §12.4 第 2 點稀釋讀法（*native 顯著縮小 ⇒ guidance 價值集中在小 Gen0* vs
  *native 仍維持 ⇒ 更強證據*）**無法**由這個指標裁決。
  **design §13.6 亦明文：§12 Q2 在 medium final 端點上的跨 P0 稀釋比較記為 `NOT_EVALUATED`。**
- **在唯一存活於此量測病理之外的指標上——Gen0 中心——沒有稀釋；若有什麼，也是相反方向。**
  `generation_Q_median_any_valid` 是在 11,261–11,305 個有效候選（native）或 502–509 個（capped）上取
  中位數，所以它是對模式樂透**取平均**，而不是穿過它取最大值：

  | | 中心 `F/G` 中位數 | 為正 | `ln` 平均（⇒ 幾何平均） | per-seed 範圍 |
  |---|---:|---:|---:|---|
  | P0 = 512 | 1.0251（+2.5 %） | 3/5 | +0.0197（+2.0 %） | 0.9873 – 1.0495 |
  | P0 = 11,405 | **1.0331（+3.3 %）** | **5/5** | **+0.0330（+3.4 %）** | 1.0172 – 1.0529 |

  guided 的 Gen0 中心優勢**維持並略微擴大**（log 尺度 +2.0 % → +3.4 %），且變成**跨 seed 一致**
  （3/5 → 5/5）。**機制：** prior 是逐次抽樣套用的，所以期望的中心位移與 pool 大小無關；
  隨著抽樣數多 22× 而改變的是實現中心的*抽樣誤差*，它縮小約 `√22 ≈ 4.7×`。
  一致性的銳化與 per-seed 範圍的收窄（寬度 0.062 → 0.036，1.7× 收窄）都與該預測方向相同。
  這是一個**管路層級的確認**：treatment 在 native 規模下被未經稀釋地遞送（design §12.4 第 3 點）。
- **誠實的界線。** 「Gen0 中心效應沒有稀釋」***不等於***「guidance 對搜尋的價值沒有稀釋」。
  index §7.2.1 的整個重點就是 GA 並不消費那個中心——它讀的是極值。Q2 能說的是：
  *prior 對它直接控制的那個量的掌握，在 22× Gen0 下不會減弱；至於那是否轉化為搜尋價值，
  由 Q3 以及 §7 對最終指標的判定回答。*

---

## 13. Q3——極值機制：三項預先登錄的預測

*design §12.4 第 4 點（`NATIVE-P0-ROBUSTNESS-20260811(b)`，2026-08-12 **執行前**寫定、可否證）。*

**依 design §13.5 的「四列，永不合併」記錄結構呈現。** (ii) 永不被 (iv) 覆寫。

**Q3 完全不依賴 champion 量測**（Gen0 分解讀自 `trajectory.jsonl`），因此**不受 §7–§8 的儀器缺陷影響**
——design §13.6 明文如此。

### 13.1 Gen0 資料（兩個 P0 水準，同一 code path）

Gen0 = 第 1 代紀錄，也就是兩臂依構造唯一有差異的那一代。
中心 = `generation_Q_median_any_valid`；極值 = `best_gflops_so_far`；有效性 = `generation_any_valid_count`。

**Native，P0 = 11,405：**

| seed | 中心 F/G | 極值 G | 極值 F | **極值 F/G** |
|---|---:|---:|---:|---:|
| 24001 | **1.0358** | 10,904.9 | 11,766.3 | **1.0790** |
| 24002 | **1.0172** | 10,996.9 | 11,386.1 | **1.0354** |
| 24003 | **1.0529** | 12,086.8 | 11,904.6 | 0.9849 |
| 24004 | **1.0289** | 11,415.7 | 11,289.9 | 0.9890 |
| 24005 | **1.0331** | 11,622.9 | 11,538.4 | 0.9927 |
| **中位數** | **1.0331** | — | — | **0.9927** |
| **F > G 的 seed 數** | **5/5** | — | — | **2/5** |
| **mean ln（⇒ 幾何平均）** | +0.0330（**+3.4 %**） | — | — | +0.0154（**+1.5 %**） |

**Capped，P0 = 512：**

| seed | 中心 F/G | 極值 F/G |
|---|---:|---:|
| 24001 | 1.0435 | 1.0600 |
| 24002 | 0.9873 | 1.0007 |
| 24003 | 0.9958 | 0.9551 |
| 24004 | 1.0251 | 0.8747 |
| 24005 | 1.0495 | 1.0073 |
| **中位數** | **1.0251** | **1.0007** |
| **F > G 的 seed 數** | **3/5** | **3/5** |
| **mean ln（⇒ 幾何平均）** | +0.0197（+2.0 %） | **−0.0227（−2.2 %）** |

### 13.2 預測 (i)——「guided 的 Gen0 **極值**劣勢應在 11,405 下**擴大**」

**(i) 預測原文與註冊日期。** design §12.4 第 4 點，`NATIVE-P0-ROBUSTNESS-20260811(b)`，
**2026-08-12 寫定，執行前**：*「guided 相對 baseline 的 Gen0 極值劣勢會擴大（而非縮小）」*。

**(ii) 完全照預註冊方式計算的分析，不得更動。**

## ⚠ **在 medium 上被 `REFUTED`。**

- 就 index §5b 的分析量而言，guided 的極值赤字**收窄並翻轉符號**：`ln(extreme F/G)` 的平均從 512 下的
  **−0.0227（−2.2 %）** 變為 11,405 下的 **+0.0154（+1.5 %）**。
- `ln(extreme F/G)` 逐 seed 配對變化，capped → native：
  **+0.0178、+0.0341、+0.0307、+0.1228、−0.0146**。
  **5 個 seed 中有 4 個朝著 guided 極值劣勢*較小*的方向移動**，中位變化 **+0.0307**。
- 只有兩個較弱的統計量朝預測方向移動，且幅度都小於散亂：極值比值中位數 1.0007 → 0.9927（−0.8 pp），
  以及為正的 seed 數 3/5 → 2/5。兩者都不是預先登錄的分析量，而在 n = 5 之下 3/5→2/5 是噪音。

**此處記錄為該機制之預測 (i) 在 medium 上被推翻。它未被事後改寫、軟化或重新推導。**

**(iii) 儀器判定、其證據，以及相對於解盲的發現日期。**
Q3 讀的是 GA trajectory，**不經過** remeasure 路徑，因此 §7–§8 的儀器缺陷**不影響本項**
（design §13.6 明文）。儀器缺陷的發現日期為 **2026-08-12**（index §7.1a 撤回）與 **2026-08-13**
（根因確立、design §13），**晚於** native-medium 的執行（2026-08-12 04:05Z 起）與解盲。

**(iv) 任何修復後的估計。** 無。**`NOT_EVALUATED`。**

**可能成因——預測為何失敗，以及什麼能區辨它。** 該預測假設 Gen0 最大值由*候選品質分布的散布*所支配，
因此集中機率質量會壓縮上尾，而 22× 更多的抽樣會讓這個壓縮咬得更深。native 資料在 medium 上以三個
具體方式與此不一致：

1. **Gen0 極值受限於量測模式，而非候選分布。** native Gen0 的 best 為 **10,904.9–12,086.8**（G）與
   **11,289.9–11,766.3**（F）——十次 run 跨度僅約 ±5 % 的區帶，恰好坐落在 §7.1 所辨識的約 14,000 高模式
   天花板之下。對雙峰噪音分布做 11,283–11,305 次抽樣取最大值，會在*兩臂*都逼近該天花板，
   因此極值比值被 pool 大小推向 1——與預測 (i) 相反。佐證：極值比值的**散布收縮**了，
   從 0.875–1.060（capped）到 0.985–1.079（native）——估計量精確得多，而其中心卻*上移*。
2. **guided 臂從更大的 pool 中獲益更多，而非更少。** Gen0 best 的中位數在 G 中從 10,287.5 → 11,415.7
   （**+11.0 %**），在 F 中從 10,095.9 → 11,538.4（**+14.3 %**）。若上尾被壓縮，應預測 guided 臂從額外
   抽樣中獲益*較少*。它獲益更多。
3. **實現出的 guided Gen0 *更*多樣，而非更少——在兩個 P0 水準上皆然。** 第 1 代的 Hamming diversity
   （`core/population.py:194`）在全部五個 native seed 上為 **G 0.568、F 0.575**
   （capped：G 0.567–0.570、F 0.573–0.576）——guided 臂在**可得的 9 對上都高出 +0.007**
   （seed 24005 native G 沒有 gen-1 log 行，§15.2）。而由出貨 weights 計算出的 prior *名目*效應方向相反、
   大小幾乎相同：`Δ = [(1 − Σq²_DepthU) − 5/6] + [(1 − Σq²_1LDS) − 1/2] = (0.6840 − 0.8333) +
   (0.4428 − 0.5000) = −0.2065`，即 30 個 gene 的平均上 **−0.0069**。
   所以「集中質量會縮小 Gen0 多樣性」這個前提，在這個 shape 上**於實現出的母體中並不成立**。

   **為何實現出的多樣性不遵循名目 prior：** sampler 只接受相異且符合約束可行的個體。從所設定的
   per-gene 分布做獨立、未過濾抽樣，預測第 1 代 diversity 的基準值為 **0.6306**
   （29 個非 `group_0` gene 的 `1 − 1/k` 之和 = 17.9171，加上 `group_0` 的 `1 − Σp² = 0.99982`，÷ 30）；
   觀測值為 **0.568**。因此實現出的 Gen0 在兩臂中都實質上*比*任何 per-gene prior 所要求的更集中——
   主導 Gen0 組成的是**可行性過濾**，而不是 treatment。對 +0.007 這個符號翻轉，一個合理的讀法是：
   把 `DepthU`/`1LDSBuffer` 導向可行的設定會**紓解**其他 28 個 gene 上的聯合約束。
   **這是一個假說，不是結果。** 能夠定案的量測是 engine 自己的 `per_gene_diversity`
   （僅在有 observer 附掛時才於 `ga.py:674–682` 輸出——當時沒有附掛），或是 Gen0 母體的 dump。
   **`NOT_EVALUATED`。**

**對此項推翻的 two-sided 但書。** 推翻 (i) *在 medium 上*並**不**推翻 index §7.2.1 機制的一般性。
§7.2.1 是在 **large** 上推導的，其 Gen0 remeasure 噪音很小（max÷min 1.024–1.053），
且其 treatment 涵蓋 5 個 gene。medium 的雙峰量測很可能完全遮蔽任何尾部效應。
(i) 的乾淨檢定是 native **large** 的 run。

### 13.3 預測 (ii)——「guided 的 Gen0 **中心**優勢應維持或擴大」

**(i) 預測原文與註冊日期。** 同上，2026-08-12 執行前寫定。

**(ii) 分析（照預註冊方式）。**

## **`SUPPORTED`。**

中心 `F/G` 中位數 1.0251 → **1.0331**；`ln` 平均 +0.0197 → **+0.0330**；為正 3/5 → **5/5**；
per-seed 範圍從 0.9873–1.0495 收窄至 1.0172–1.0529。**每一個 native seed 都為正。**

**(iii) 儀器判定。** 同 §13.2——不受影響。
**(iv) 修復後估計。** 無。

**可能成因。** 恰為所述的理由：prior 未變，所以*期望*的中心位移是與 pool 大小無關的逐次抽樣性質；
只有估計量的變異數會改變，而它以 `1/√n` 縮小（`√22 ≈ 4.7×`）。觀測到的範圍寬度 0.062 → 0.036 是
1.7× 的收窄——方向相同，但小於 4.7×，因為殘餘散亂還包含到達的可行區域在 seed 之間的真實差異，
而不只是多項式誤差。**區辨性證據：** 若殘餘純為多項式誤差，native 的範圍應約為 0.013；超出的部分
就是 seed 層級的成分。這與該讀法一致，但並未證明它。

### 13.4 預測 (iii)——「擴大幅度在 **large** 上應大於 **medium**」

## **`REFUTED`**（2026-08-18 更正）。

> **原標為 `NOT_EVALUATED`，理由是「native large 不在本附冊範圍內」——那在撰寫時為真，現已為假。**
> `s14-large-report.md` §10.7a 已於 2026-08-17 由實測 artifact 判讀：
> large **+0.0304**（劣勢**縮小**）對 medium **−0.0080**（略為擴大），
> **兩者方向相反，梯度與預測的正負號相反 ⇒ 推翻。**
> 本附冊仍不代替 large 附冊作此判定；此處僅同步其結論。

**(i) 預測原文與註冊日期。** 同上。
**(ii) 分析。** 跨 shape 梯度只存在 medium 這一半。在本附冊撰寫時，native **large** 不在本附冊範圍內
（其結果由 `s14-large-report.md` 承載）。
**(iii)/(iv)。** 無。

現在能說的是：**該預測梯度的 medium 這一側完全沒有出現擴大——它出現的是收窄與符號翻轉（§13.2）**。
若 large 確實顯示擴大，梯度的排序會成立，而 (i) 在 medium 上仍屬被推翻；若 large 也收窄，
(i) 就是徹底被推翻。**本附冊不代替 large 附冊作此判定。**

### 13.5 已排除的有效率產物

native 每 11,405 個中的有效候選：**G 11,283–11,300（98.93–99.08 %）**、
**F 11,261–11,305（98.74–99.12 %）**。Capped：G 505–508 / 512、F 502–509 / 512。
兩臂在兩個 P0 水準上產生的可執行 config 數在統計上無法區分，
所以 **Gen0 結果沒有任何部分是「guidance 產生了更多不可建構的 kernel」**。
**`ELIMINATED`。**

---

## 14. 額外角度——實現出的 Gen0 分布與所意圖的 `p1`

**直接的 per-value 頻率檢查：`NOT_EVALUATED`，並附理由。** Gen0 中實現出的 `DepthU` / `1LDSBuffer`
值計數**無法從任何 artifact 還原**：`distinct_hashes.jsonl` 只存 hash；`optimization_result.json` 存的是
champion；`step-00__ductile.checkpoint` 是*最後*一代的狀態，不是 Gen0；engine 的 per-gene 統計只在有
observer 附掛時才輸出（`ga.py:674–682`），而當時沒有。重算實現出的計數需要重跑 `space.sample(11405)`，
那是每臂約 2.9 h 的單執行緒 CPU 工作（design §12.6），超出唯讀分析的範圍。

**什麼*是*可量測的。** 第 1 代的整體 Hamming diversity 是實現出的 per-gene 頻率的精確函數，且每次 run
都有記錄：

| | 24001 | 24002 | 24003 | 24004 | 24005 | 全距 |
|---|---:|---:|---:|---:|---:|---:|
| **native G**（n = 11,405） | 0.568 | 0.568 | 0.568 | 0.568 | n/a¹ | **0.000** |
| **native F**（n = 11,405） | 0.575 | 0.575 | 0.575 | 0.575 | 0.575 | **0.000** |
| capped G（n = 512） | 0.568 | 0.567 | 0.570 | 0.567 | 0.569 | 0.003 |
| capped F（n = 512） | 0.574 | 0.575 | 0.573 | 0.576 | 0.573 | 0.003 |

*`[CODE AUDIT]` `stage5_native_{baseline,guided}/`、`stage3_{baseline,guided}/seed_*/medium/*optimization.log`
的 `diversity` 欄，第 1 代（由本附冊以 regex 逐檔重新解析）。*
¹ seed 24005 native G 被 resume 過，其 engine log 從第 2 代開始，沒有 gen-1 的 diversity 行（§15.2）。
它的第 1 代母體在 `trajectory.jsonl` 中完好（11,405 個候選，11,284 個有效）；缺的只是由 log 導出的
diversity 純量。該列 n = 4。

三個讀法：

1. **實現出的組成之抽樣誤差確實如預測般縮小。** 跨 seed 全距在兩臂都從 0.003（P0 = 512）降到
   **低於 log 的 0.001 列印解析度**（P0 = 11,405）——與 22× 更多抽樣所預期的 `√22 ≈ 4.7×` 縮減一致。
2. **但兩個 P0 水準之間的*中心值*未變**（G 兩者皆 0.568、F 兩者皆約 0.575）。實現出的 Gen0 組成
   **在 512 時就已經收斂**。所以 22× 的操作買到的是*精確度*，而不是一個*不同的*實現分布。
   這是對 design §12.1 稀釋框架的一個實質回答：「大型 uniform Gen0 會把 free-gene 的邊際分布填滿」
   這個前提只對了一半——邊際分布在 512 時就已填滿；native 額外提供的是對尾部更深的抽樣。
3. **而且實現出的分布在任一 P0 水準下都*不是*所意圖的那個。** 獨立抽樣預測為 0.6306；觀測值在兩種變體
   中都是 0.568，短少 `30 × 0.0626 = 1.88` 個 gene-unit。介於所設定機率與被接受母體之間的某個環節——
   `space.sample()` 中的相異性加可行性剔除——移除了大約兩個 gene 份量的變異。
   **Treatment 是依規格遞送進 sampler 的**（§1.5 逐位元驗證了 weights，並精確重現了 index §3.4b.3 的
   機率）；**偏離名目 prior 的是*被接受的母體*，且兩臂偏離的方式相同。**

**讀法 1–3 的證偽方式：** 在每個 P0 水準、每一臂各跑一次短的 medium run 並附掛 engine observer，
讀出 `per_gene_diversity`，或 dump 出 Gen0 個體。**建議執行、成本低廉、此處未做。`NOT_EVALUATED`。**

---

## 15. 偏差紀錄

### 15.1 7× remeasure 透過 `--gpu-uuid-override` 在 GPU 5 上執行

`large` 佔用了 Lock-A 的卡（2、3、4、6、7），因此**全部** medium remeasure（capped 與 native、
campaign 1 與 2）都在 GPU 5 上執行。artifact 自身即記錄了這一點：

| 欄位 | 值 |
|---|---|
| `expected_gpu_system_index` | `5` |
| `verified_gpu_uuid` / `gpu_uuid_override` | `GPU-4c517496fc501205` |
| `lock_a_search_card_uuid` | 各 seed 的搜尋卡（例如 24001 → `GPU-8cdaa86f8629c93a`） |
| `run_card_differs_from_search_card` | `true` |
| `same_gpu` / `same_process` | `true` / `true` |
| `start_arm` | `G`（per-shape counterbalance `START_ARM[medium] = G`） |
| `repeats_per_arm` / `single_measurements` | `7` / `14` |
| `taskset` | `96-107` |
| `rotating_buffer_mb` / `num_elements_to_validate` | `4096` / `128` |

*`[CODE AUDIT]` `stage3_baseline/seed_*/medium/champion_interleaved.json`、
`stage5_native_baseline/seed_*/medium/champion_interleaved.json` → `measurement_metadata`。*

理由（index §8.3、`medium_remeasure_deviation.md`）：預先登錄的要求是 G 與 F 必須**在同一個 process、
同一張卡、同一個時間窗內** interleave，而這一點被保留了；判準是 **pair 內部的比值**，
故卡層級的吞吐量偏移對兩臂共通。絕對 GFLOP/s 跨卡不可比；`F/G` 則可比。
實作上使用非封存 copy `remeasure_interleaved_champion__gpu5deviation.py`（加 opt-in `--gpu-uuid-override`；
封存腳本 + Lock A 未變）。
**這使 native 與 capped 的 medium remeasure 具有*完全相同*的偏離，對 Q2 的 cross-P0 比較反而有利。**

⚠ 但請注意 §9：**「卡層級偏移對兩臂共通、故在配對比值中相消」這個論證對*卡別* offset 成立，
對*汙染*不成立**——後者是否 arm-symmetric 為 `NOT_EVALUATED`。

### 15.2 Seed 24005 arm G（native）被 resume 了 3 次；其 degradation marker 是已知 false positive

- `resume_record.json` 顯示在 Lock-A 卡 `GPU-74a77207e38908fb`（hip 6）上有三個 session：
  session 0 起於 `2026-08-12T04:05:40Z`（`resume_requested = false`）、
  session 1 起於 `07:37:56Z`、session 2 起於 `07:48:39Z`，後兩者 `resume_from_generation = 1`。
  *`[CODE AUDIT]` `stage5_native_baseline/seed_24005/medium/resume_record.json`（本附冊重讀）。*
- engine 在 `--resume` 時會覆寫其固定路徑的 log，因此存活下來的 GA log 只涵蓋**第 2–25 代**，
  而 trajectory 則是**完整的 1–25**。remeasure 腳本偵測到並記錄了這件事：

  ```
  RESUMED_RUN_PARTIAL_LOG {"arm": "G", "log_generations": 24, "log_starts_at": 2,
   "note": "engine rewrote its fixed-path log on --resume; trajectory is complete and was
   cross-checked on the overlap", "trajectory_generations": 25}
  ```

  *`[CODE AUDIT]` `stage5_native_remeasure_control/seed_24005/medium.remeasure.log:35`。*

  **該檢查並未被弱化**：腳本斷言 trajectory 是完整的 `1..N`、log 的世代恰為其*後綴*，
  並就 log 涵蓋的每一代以 `cumulative_complete_evals` **逐元素**交叉核對 `n_evals`，任何不符即中止。
  *`[CODE AUDIT]` `scripts/remeasure_interleaved_champion.py:442–465`（工作筆記記為 `:426–455`；
  經核對，逐元素比對位於 `:442–453`，`RESUMED_RUN_PARTIAL_LOG` 的輸出位於 `:457–461`）。*
  **Seed 24005 arm G 通過。**
- 在 2026-08-12T07:37Z 一次刻意的 kill/resume 測試期間寫入此 seed 的 `native_gen0_degraded.json`，
  是**一個已修復之 guard 缺陷所產生的 FALSE POSITIVE**，已 quarantine 於
  `quarantine/native_gen0_guard_false_positive_20260812/`（`native_gen0_degraded.json` +
  `native_gen0_degraded.FALSE_POSITIVE_ANNOTATION.json`），並附四條獨立證據線：
  (1) `observed_gen0 = 5958 = int(512 + (11405 − 512)/2)`，是 law-1 的 **decay** 值，而非 fail-open 值
  `11405 // 2 = 5702`；(2) log 中零行 `Max iterations reached`，故 `ga.py:289–293` 從未執行；
  (3) `trajectory.jsonl` 第 1 代有 `generation_candidate_count = 11405`，其中 11,284 有效；
  (4) 該 marker 自相矛盾（`halved_target 5702` vs `observed_gen0 5958`）。
  **它並未被回報為 design §12.7 的 stock-Ductile fail-open 觀察。沒有任何科學資料遺失。**

### 15.3 Campaign 2 的就地覆寫——一項**未追蹤**的操作性偏差

見 §6.3。這是本附冊記錄的第三項偏差，且**是三項之中唯一沒有在當時留下痕跡的**。
design §9.3 第 3 項待裁決事項要求為此**歸檔一份 operational-correction 紀錄**。**PENDING。**

### 15.4 本附冊相對於工作筆記所做的更正（全部照實記錄）

| 項目 | 工作筆記 | 本附冊（重算） | 影響 |
|---|---|---|---|
| native 7× 表的來源路徑 | `stage5_native_baseline/seed_*/medium/champion_interleaved.json` | 該 path 已被 C2 覆寫；C1 在 `medium_recheck_control/native/…/preserved_campaign1_20260812T135613Z/` | **引用更正**；數值不變 |
| P95 log residual | native 0.828 / capped 1.196 | linear：**0.8915 / 1.2098**（lower：0.8282 / 1.1964） | 方法別差異；結論不變 |
| config diff 行數 | 16 行新增 | **10 行新增**（純新增、零刪除） | 計法差異；實質不變 |
| `s14_native_remeasure_driver.py` 的 "inert here" | `:129` | **`:187`** | 引用更正 |
| `remeasure_interleaved_champion.py` 交叉核對 | `:426–455` | **`:442–465`** | 引用更正 |
| 工作筆記未涵蓋 | — | campaign 2（capped 與 native 兩者）、arm-asymmetry、warm-up 根因、clock probe、pilot 鑑識 | 本附冊新增 |

*工作筆記 `working-notes/s14-native-p0-medium-analysis.md` 為已被取代的工作輸入，
依 `reports/README.md` 規則不得引用；其全部內容已折入本附冊。*

---

## 16. 殘餘不確定性——報告，不求解決

design §13.9 明列「須寫入報告，不求解決」。以下逐項照搬，並附本附冊能／不能補上的部分：

1. **時脈機制是由 warm-up sweep、DPM 算術，以及 tiny 實測到的時脈不敏感性*推論*而來。
   不存在任何直接的鎖頻證據。**（§8.5；design §9.3 第 1 項，約 10 分鐘、零研究 GPU 時數，需 owner。）
2. **任何 shape 都不存在跨視窗或跨日的重複性資料。** 窗內 `η` 是一個**緊度未知的下界**。
   （design §13.7 第 1 項提議的 A/A cross-window 實驗，約 50 GPU-分鐘，**未執行**。）`NOT_EVALUATED`。
3. **tiny 的單一 dropout**（7 次中的第 7 次，落在 37.8 s 視窗的第 34.7 s）為 `NOT_EVALUATED`，
   而且 medium 的機制對它**反證**（tiny 對 warm-up 長度不敏感）。
4. **搜尋期汙染是否 arm-symmetric：`NOT_EVALUATED`，且事後不可查證**（逐代 benchmark CSV 未保留）。
5. **campaign 1 為何比 campaign 2 髒 1.7×：未解釋。**
6. **跨 campaign 的可重現性對比僅建立在 n = 2 個 campaign 之上。**
7. **warm-up sweep 在拐點之上非單調**（20,544 → 4 %）——所提出的機制不解釋這一點。
8. **在釘住的 RBS = 4096 下，修復未經驗證**——**這個結論仍然成立**（2026-08-17 驗證的是
   `RBS = 401`，不是 4096；見 §18.2）。**但原本給的理由是假的（2026-08-18 更正）：**
   `5,136 warm-ups @ RBS 4096` 的可行性 probe **不是「從未被嘗試」，而是 2026-08-13 嘗試過、
   三個 seed 全部 `rc = 1`**（其中 24001 與 24005 因 int32 溢位，24004 因 library 連結錯誤）。
   ⇒ 正確狀態是 **`EVALUATED / closed by infeasibility`，不是 `NOT_EVALUATED`**（見 §9 的更正）。
   **不可行的門檻是 `nw ≥ 1638 @ RBS 4096`，不是「RBS 4096 不可行」**——`1400 @ 4096` 與
   `1637 @ 4096` 都量過，n = 50，dropout 各 **4.0 %**。
9. **雙峰的競爭性物理解釋尚未被完全區分開。** warm-up/DPM 說得到 sweep 的強支持，但下列仍未被
   逐一排除為*殘餘*成分：MI300 上 XCD/CU 分區配置逐次 launch 變動；MALL/L2 駐留（RBS 已被排除為
   *病因*，但其約 12–14 % 的確定性代價是實在的）；`GlobalSplitU`-workspace 或 atomics 競爭。
   `NOT_EVALUATED`。（design §13.8：若鎖頻**未**消除掉點，warm-up 說降級為「未解釋殘差」，
   且必須列出這些仍然存活的替代解釋。）

**`NOT_EVALUATED ≠ 無效果。`** 以上每一項都是「沒有量」，不是「量了沒有」。

---

## 17. 本附冊可說與不可說

| | |
|---|---|
| **可說** | 三項不受汙染的子判準在 capped 下各為 **3/5**、在 native 下為 **2/5 / 1/5 / 3/5**，預註冊要求 ≥4/5；native 執行本身乾淨（10/10 fail-closed 全過）；treatment 在兩個 P0 水準上逐位元同一；Q3 (i) 在 medium 上 `REFUTED`、(ii) `SUPPORTED`、(iii) **`REFUTED`**（2026-08-18 更正；見 `s14-large-report.md` §10.7a）；Gen0 中心效應在 22× Gen0 下未被稀釋（3/5 → 5/5）；量測缺陷的症狀、根因、範圍與所有已排除／未排除的假說；**2026-08-17 儀器修復的前後對照與修復後量到的 final ratio 讀數（§18）** |
| **不可說** | **S14 的 gate 判定**（現由 `staged/s14-guided-results.md` §5.4 承載；原承載者 `full-ga-baseline-vs-guided-outcome-report.md` **已由 owner 於 2026-08-18 解除授權**）；medium 的 final-champion 或 non-regression **通過或未通過**（該端點被提議為 `NOT_EVALUATED / instrument-invalid`，PENDING）；由該作廢端點導出的任何 tier；**「guidance 幫助了／傷害了 medium」作為 gate 層級的裁決**（⚠ **2026-08-18 依 owner 裁決限縮**：原文是無條件禁止該句。gate 層級的判定確實仍不可說——它由 Gen0 / gen-10 / AUC 三項 margin-free 子判準決定，各為 **3/5**，且**不經 7× 量測路徑，本次修復碰不到它們**。但 `ETA-MARGIN-REMOVED-20260814` 的 ledger 明文要求 **final ratio 仍須以方向與效應量報告**，§18 就是照實呈現那個量的讀數，**不構成 gate 判定**）；「模型沒用」；任何 aggregate rescue；任何一般化／部署／加速措辭；以 `original_final_gflops` 作為 endpoint |
| **待 owner 裁決後才能定案** | ~~campaign of record（design §13.3 提議 C1）~~ **——已於 2026-08-15 結案：C1 與 C2 皆非 measurement of record，由一個新 campaign 取代兩者（§6.5）**；估計量是否維持 median-of-7（§13.3 提議維持）；margin 是否維持 pinned `η_s`（§13.4 提議維持，但須雙 margin 揭露）；per-shape claim 階梯（§13.5）；medium 端點是否記為 `NOT_EVALUATED / instrument-invalid` 而非 fail（§9.3 第 9 項）；**`PENDING_HUMAN_DECISION`（新，2026-08-18）：medium 的 final ratio 是否以 pilot401 的 `C03` / `C03CONF` 為 measurement of record**——`PILOT401_MANIFEST.json` 自我標記為 `PILOT -- not an endpoint, not a campaign`，而 §6.5 所稱「取代兩者的新 campaign」（design §A.5 的第五個 campaign）**從未執行**；owner 於 2026-08-18 授權**呈現**該讀數，**未指定其為 record**；**`PENDING_HUMAN_DECISION`（新）：§G.4.0a 第二分支觸發後的處置**——兩批 `k = 8` 的 `P3_pass` 都是 `false`（10.36 % / 8.04 %）。**除已結案者外全部仍為 `PENDING_HUMAN_DECISION`，本附冊照此標記，不代為核准。** |

**Conditional Arm S。** design §10.2 的觸發規則要求 F 在 ≥1 confirmatory shape 通過 per-shape
directional gate。**本附冊不判定該觸發是否成立**——那是跨 shape 的判定，屬 formal report。

---

## 18. 儀器修復（2026-08-17）——前後對照與修復後的讀數

> **這一節記的是 measurement 實驗本身：舊儀器有多不可讀、修了什麼、修完之後量到什麼。**
> **它不是 S14 的 gate 判定**（§17）。跨 shape 的 guided 結果整理在
> `staged/s14-guided-results.md`，本節只負責 medium 的儀器面。
> 設計權威是 `/data1/perlee/measurement_design.md`（判讀規則見其 §G.3.1，
> `NULL-AS-NOISE-BASELINE-20260818`；pilot 結果見其 §E.5）。

### 18.1 前後對照——「之前」用 campaign 1（owner 裁決，2026-08-18）

| | capped | native |
|---|---:|---:|
| **campaign 1** dropout | **45.71 %**（32 / 70） | **47.14 %**（33 / 70） |
| **campaign 1** final champion `F/G > 1` | **2/5** | **3/5** |
| 修復後 dropout | **7.50 %** / **6.43 %**（兩批） | **6.55 %** |
| 修復後 final champion `F/G > 1` | **3/5** | **3/5** |

**三件必須連著讀的事：**

1. **native 的計數修前修後都是 3/5。** 改良的證據是**汙染率**（47.14 % → 6.55 %，約 7.2 倍）
   與**離散度**，**不是計數翻轉**。capped 那邊 2/5 → 3/5 只差一個 seed，也不足以單獨支撐宣稱。
2. **離散度的倍數只適用於 capped。** `LADDER_LOG.md:25` 記錄基準格 A → C03 的逐 seed 改善為
   **50.5× / 51.1× / 99.9× / 18.7× / 72.5×**（seed 24001→24005）。
   **這是 capped 的數字，native 沒有對應的參照格，不可挪用。**
3. **「之前」有兩個值，差 1.9 倍，而原因未解。**
   campaign 1 capped 是 45.71 %，campaign 2 capped 是 **24.29 %**（17 / 70）。
   §16 item 5 的「campaign 1 為何比 campaign 2 髒」至今 `NOT_EVALUATED`。
   **兩個都要擺，只擺一個會把這個未決事項壓掉。**

> **⚠ 基準格 A 不是舊 campaign。** 它是 2026-08-17 08:02–08:12 在**舊設定**（`321 / 4096`）下
> 跑的**參考格**（`LADDER_LOG.md:5`：「Cell A is the reference baseline (unmodified instrument);
> it is never a candidate」）。它在本節唯一的用途，是**補上 campaign 1 給不出的 sd** ——
> C1 與 C2 都是**單一 window、7 次 repeat**，跨窗 `sd(ln(F/G))` 在它們身上沒有定義。
> **使用它需要一句授權**：A 的 **39.05 % / 2-of-5 / 中位 0.9917** 對 C1 的
> **45.71 % / 2-of-5 / 中位 0.9971** ——同量級、同方向、同計數，
> ⇒ **它是舊儀器的忠實重現**，可以用來補那個 sd。

### 18.2 修了什麼——降噪來自暖機次數，不是 rotating footprint

**梯子**（`nw` 由低往高，`RBS` 全部 401；第一個同時通過 P3 與 P4′ 的格子就停）：

| 格 | `nw` | `RBS` | dropout | P3 | P4′ |
|---|---:|---:|---:|---|---|
| A（參考） | 321 | 4096 | 39.05 % | FAIL | FAIL（0/5） |
| B | 321 | **401** | **40.60 %** | FAIL | FAIL（0/5） |
| C01 | 640 | 401 | 31.19 % | FAIL | FAIL（0/5） |
| C02 | 1000 | 401 | 18.81 % | FAIL | FAIL（1/5） |
| **C03** | **1400** | **401** | **7.50 %** | **PASS** | **PASS（4/5）** |

**兩條互相正交的單變因對照，指向同一個結論：**

- **只動 RBS（暖機釘死在 321）：** A → B 是 39.05 % → **40.60 %**，**+1.55 pp，沒有降低**。
- **只動暖機（RBS 釘死在 production 的 4096）：** 獨立的 sweep 探針給出
  321 → **36 %**、640 → **36 %**、1000 → **32 %**、1400 → **8 %**（n = 25）；
  confirm 批次 n = 50 時 `1400 @ 4096` 是 **4.0 %**、`321 @ 4096` 是 **42.0 %**。

⇒ **降噪來自暖機次數，不是 rotating footprint。**

> **⚠ 兩項使用限制。**
> (i) 基準格 B 的證據是**量級差距**（1.55 pp 對 31.55 pp），**不是等價性檢定**；
> 資料未排除 cap 帶來約 3 pp 的降低。
> (ii) 那條 sweep 是**單臂、帶 `overrides` 的探針**（`s14_medium_warmup_rbs4096_probe.py`），
> 不是 7× interleaved harness，**只用一個 champion**（seed 24001 arm-G 的 parked 樹）。
> **它的絕對水準不可轉移**——8 % 不可以拿去跟 C03 的 7.50 % 並排，也不能說「同一儀器」。
> **只取它的斜率與符號。**

### 18.3 修復後的讀數與它的噪音基準

判讀規則見 design §G.3.1：**以 null ratio 當噪音基準，多尺度並列，不合成單一裁決，不設倍數門檻。**

**medium capped，`F/G` 為 gflops 比（> 1 = guided 較快），`C03` 與 `C03CONF` 兩批各 12 window 的平均：**

| seed | `ln(F/G)` | ÷ G/G′ sd | ÷ F/F′ sd | ÷ 跨 session 0.0097 | ÷ 自身 sd |
|---:|---:|---:|---:|---:|---:|
| 24001 | −0.00045 | 0.1 | 0.1 | 0.0 | 0.1 |
| 24002 | **+0.06024** | 25.3 | 35.0 | 6.2 | 14.8 |
| 24003 | +0.01336 | 5.9 | 5.3 | **1.4** | 5.6 |
| 24004 | **+0.06142** | 39.5 | **3.0** | 6.3 | 3.4 |
| 24005 | −0.00257 | 0.5 | 0.9 | 0.3 | 0.7 |

**怎麼讀：**
**24002 在所有尺度下都明顯為正。24003 與 24004 都是正的，但幅度隨尺度而變**
（24003 在跨 session 尺度下只剩 1.4；24004 在 F/F′ 尺度下只剩 3.0）。
**24001 與 24005 在所有尺度下都貼零。沒有任何 seed 在任何尺度下顯示 guided 有害。**
**用哪一把尺會改變答案，這件事本身是結果的一部分，因此不合成單一裁決。**

**四把尺各自的性質與限制：**

| 尺 | 量到什麼 | 限制 |
|---|---|---|
| **G/G′ null** 的 sample sd | 兩臂都是 baseline 樹，真值恰為 1.0 ⇒ **可查偏差**。五個中心全在 **±0.0018** 內 ⇒ **該構型下儀器無偏** | **結構上永遠不載入 arm F 那顆 kernel**。seed 24004 的 G/G′ sd 是 **0.00155**，真實對比自己的 sd 是 **0.01807**——**差 11.6 倍**。⇒ **只用它會系統性高估顯著性** |
| **F/F′ null** 的 sample sd | 兩臂都是 guided 樹 ⇒ **抓得到 arm F 那顆 kernel 的噪音**。24004 的 sd 是 **0.02071**，與真實對比同級 | 註冊角色是**離散度**儀器；拿它的中心當偏差證據是用在註冊角色之外。⚠ **`N7_GVSG` 與 `N7b_FFNULL` 不是同一 session**（13:44–13:55 對 15:29–15:39，中間夾了兩批 campaign），所以 F/F′ ÷ G/G′ = **13.3 倍**這個比值**內含「同一儀器狀態」的假設** |
| **跨 session rms 0.0097** | 換一個 session 還會不會是同一個結論 | ⚠ **取自 design §G.2.4 的 native C1↔C2，也就是舊儀器**（同表記其離散度為 0.3136）。**對修好的儀器是外插——修好的儀器上一組跨 session 資料都沒有** |
| **真實對比自身的跨窗 sd** | 這個效應在這台儀器上解析得多清楚 | 不含 session 間成分 |

**兩批之間的一致性，以及它量到的是什麼：**
`C03` 與 `C03CONF` 逐 seed 的最大差是 **0.00567**（seed 24004）。
⚠ **這兩批不是獨立的**——`C03` 末窗 09:10:33、`C03CONF` 首窗 09:20:37，**相隔 10 分 04 秒，同一批卡、同一 session**。
依 design §G.1 的 `NO-SEPARATION-20260817` 代價條款，**背靠背的 window 只涵蓋 fast 層，
slow 層仍為 `NOT_EVALUATED`**。**所以 0.00567 是 fast 層的重現性，不是效應量的不確定性上界。**
把時間拉到當日 09:10–15:07 的四批（含兩批 `k = 8`），seed 24004 的 `mean_ln` 全距是 **0.01919**，
是 0.00567 的 **3.4 倍**。

### 18.4 順序效應——揭露，不校正

**量測順序是寫死的：** medium 的每一個 window 都是 `('G','F')`（`N7_GVSG` / `N7b_FFNULL` / `C03` /
`STAGE2_NATIVE` 各 420/420），**large 則全部是 `('F','G')`——兩個 shape 方向相反**。
design §G.3 早就寫過：`first_arm` 設在 repeat 迴圈之外，**配對只會把一個順序效應凍結起來，
而不是把它平均掉**。

在 null 裡兩臂裝的是同一顆 kernel（`config_hash` 逐位相同），**唯一的差別就是位置**：

| seed | G/G′ 中心 | F/F′ 中心 |
|---:|---:|---:|
| 24001 | −0.00171 | −0.00216 |
| 24002 | +0.00175 | −0.00090 |
| 24003 | −0.00051 | −0.00115 |
| **24004** | +0.00048 | **−0.02181** |
| 24005 | +0.00051 | −0.00158 |

**F/F′ 五個中心全負，G/G′ 混合近零。**

**不校正，三個理由：**
1. **不是純位置效應。** 兩個 null 的位置構造完全相同，G/G′ 卻沒有這個偏移
   ⇒ 是**位置 × kernel 的交互作用**，不可加、不可轉移。
2. **沒有任何一個 null 複製了真實對比的 slot／kernel 配置**（真實是 slot 1 = baseline、
   slot 2 = guided），所以兩個中心都不是真實對比偏差的無偏估計。
3. **medium 與 large 順序相反**，同一套校正跨 shape 會反號。

**但方向必須寫明（⚠ 僅限 medium capped）：** guided kernel 永遠在第二位、第二位對它偏低
⇒ **未校正的 `F/G` 是向下偏的，對 guided 不利，現行數字是保守的。**
天真校正後 24002 → +0.0611、24003 → +0.0145、24004 → **+0.0832**，全部更正。

> **⚠ 這個結論只涵蓋 medium capped，在 medium native 上反號（2026-08-18 補記）。**
> `N8b_NATIVE_FFNULL` 的五個中心是 **+0.03736 / +0.02205 / −0.00456 / +0.01889 / +0.02512**
> ——**四正一負**，與 capped 的五負相反，而兩者的量測順序完全相同（`('G','F')`）。
> ⇒ **「第二位對 guided kernel 偏低 ⇒ 現行數字保守」不可套用到 medium native。**
> 該塊的 F/F′ 偏移另有兩種未分離的來源：native guided kernel 本身不穩，
> 或該次執行受干擾（其 dropout 18.69 % 對兩者相容）。**本節不裁決。**
**強度照實寫：** 除 24004（`|mean/(sd/√12)|` = 3.65）外，其餘四個量級 ≤ 0.22 %，
只有五個合起來的符號檢定顯著（p ≈ 0.031）。**機制 `NOT_EVALUATED`** ——
要分離位置效應與 kernel 特性，需要一次 `--start-arm F` 的真實對比，本研究沒有跑。

### 18.5 P3 的十個批次——不報 CI

dropout 定義：**單一 repeat 低於同臂、同 window、7 次 repeat 之最大值的 95 %**。

| 批次 | 建構 | m | 母體 | hits | rate | `P3_pass` | 屬 §E.1 的 840 母體 |
|---|---|---:|---:|---:|---:|---|---|
| C03 | F/G 梯子（定案格） | 12 | 840 | 63 | **7.50 %** | true | ✔ |
| C03CONF | F/G 確認批次 | 12 | 840 | 54 | **6.43 %** | true | ✔ |
| CAMPAIGN k8 | F/G（受 I/O 汙染） | 8 | 560 | 58 | **10.36 %** | **false** | ✘ |
| CAMPAIGN2 k8 | F/G（乾淨重跑） | 8 | 560 | 45 | **8.04 %** | **false** | ✘ |
| STAGE2_NATIVE | F/G 階段 2 | 12 | 840 | 55 | **6.55 %** | true | ✔ |
| N7_GVSG | **G/G′ null** | 12 | 840 | 55 | **6.55 %** | true | ✔（非 F/G） |
| N7b_FFNULL | **F/F′ null** | 12 | 840 | 39 | **4.64 %** | true | ✔（非 F/G） |
| SMOKE | 工具驗證 | 3 | 210 | 18 | **8.57 %** | **false** | ✘ |
| **N8_NATIVE_GVSG** | **G/G′ null, native**（2026-08-18） | 12 | 840 | 131 | **15.60 %** | **false** | ✔（非 F/G） |
| **N8b_NATIVE_FFNULL** | **F/F′ null, native**（2026-08-18） | 12 | 840 | 157 | **18.69 %** | **false** | ✔（非 F/G） |

**`CAMPAIGN2` 的 `P3_pass` 是 `false` ⇒ design §G.4.0a 的第二分支已觸發**
（事前註冊：「乾淨重跑仍未通過 ⇒ 汙染假說被推翻，**不得再以環境為由重跑第三次**」）。
**disposition 未決**（§17）。
**SMOKE 依 design §E.3.2 的母體通則排除於 P3 判定之外——排除依據是母體定義，與它的結果無關。**

**不報信賴區間，三個理由：**
1. **840 筆不是 840 次獨立 Bernoulli。** 它是 120 個 `(seed, window, arm)` 群集 × 7，
   而**群集內的最大值依定義永遠不會是 dropout**，所以每群上限是 6 不是 7。
   **這是主要理由。**
2. **計數是方法相依的。**（⚠ 以下兩個區間是**用來示範方法相依性的反例，不是本報告陳述的結果**。
   本報告不報任何 dropout 率的信賴區間。）同一批 `C03CONF` 在 Wilson 下是 [4.96 %, 8.29 %]，**含** 8 %；
   在群集 bootstrap 下是 [4.88 %, 7.98 %]，**不含**。
3. **8 % 這個門檻本身尚未裁決**（§17）。在一個未決門檻周圍架推論機制，
   是把未決事項包裝成統計問題。

> **⚠ 一項自我更正。** 本節早期草稿曾以「artifact 裡沒有任何 CI 工具」當作理由之一。
> **那是假的**：`scripts/s14_medium_ratio_analyze.py:208` 就有 `def wilson(x, n, z=1.96)`，
> `:115` 印的正是 dropout 率的 Wilson CI；`medium_warmup_repair_investigation.md`
> 與 `large_analysis_20260817.md` 也已各自使用 Wilson／Clopper-Pearson 與 bootstrap SE。
> **該理由已刪除**；上列三條與它無關，各自獨立成立。

### 18.6 P1、P1b 與儀器完整性

- **P1**：梯子六格 360 個 window 的 client log 共 **5,760 行 `Rotating num`，全部是 320**；
  **全 campaign 12 個 cell 合計 635 個 window / 10,160 行，同樣全部 320**，
  且與 production 逐位元相同（`ceil(420,478,976 / 1,312,256) = 321`、`rotatingNum = 320`）。
  **兩個母體都成立，引用時必須指明是哪一個。**
- **P1b**：`nw = 1400` 與 `nw = 5136` 兩點對照，皆 `rc = 0`，
  `rotating_num = 320`、`rotating_memory_size = 421234176` 兩點逐字相同，
  `peak_vram_mb` 皆 1682.1（取樣次數 66 vs 67）。
  ⇒ **配置量跟著 capped 的 `rotatingNum` 走，不跟著暖機次數走。**
  ⚠ `rotating_num` 與 `rotating_memory_size` 是逐位元相同；
  **`peak_vram_mb` 是四捨五入的浮點且取樣次數不同，不可宣稱「逐位元相同」。**
- **這是 `5136 @ RBS 401`，不是 `5136 @ RBS 4096`。** 後者見 §16 item 8 的更正。

### 18.7 這一節可說與不可說

**可說：** 舊儀器的 dropout 是 39–47 %、per-seed sd 是 0.25–0.43，**不具可讀性**；
修復後 dropout 降到 **6.4–7.5 %**、sd 降到 0.0016–0.0194（capped 逐 seed 18.7–99.9 倍，A → C03；
A → C03CONF 的中位 sd 改善為 94.9 倍）。
⚠ **這個區間只涵蓋 2026-08-17 那批。** 2026-08-18 在同一台儀器上跑的 medium native 兩個 null 是
**15.60 % 與 18.69 %**（皆不過 P3）、sd 上限 **0.095**；
降噪來自暖機次數；G/G′ null 的中心從舊儀器的 +0.603 % 降到 **±0.0018 以內**；
以及 §18.3 那張表所列的讀數與它們對每一把尺的比值。

**不可說：** 任何 gate 判定（§17）；「這是 medium 的 measurement of record」
（**`PENDING_HUMAN_DECISION`**，§17）；「guided 對 medium 有效／無效」作為**判定**
——gate 現由三項 margin-free 子判準決定（各為 3/5），**本次修復在原理上碰不到它們**；
⚠ 但 `final ratio` **仍是必報量**（ledger 明文「still reported」），其讀數就是 §18.3；
gate 判定見 `s14-guided-results.md` §5.4；
「量測缺陷已經解決」——**修好的儀器上一組跨 session 資料都沒有，slow 層仍為 `NOT_EVALUATED`**。

---

## 附錄 A — Artifact 索引（全部由撰稿者重算或直接讀取）

Run root（host）：`/data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-baseline`
（container：`/src/rocm-libraries/agent_run/260809-s14-pershape-baseline`）。

**GA 搜尋（capped，P0 = 512）**
```
stage3_baseline/seed_{24001..24005}/medium/trajectory.jsonl          Gen0/gen-10/AUC/中心/有效率/母體
stage3_guided/seed_{24001..24005}/medium/trajectory.jsonl
stage3_{baseline,guided}/seed_*/medium/optimization_result.json      best_fitness、best_individuals、best_individual_hashes
stage3_{baseline,guided}/seed_*/medium/driver_status.json            DUCTILE_FORCE_P0=1、RBS、HIP_VISIBLE_DEVICES
stage3_{baseline,guided}/seed_*/medium/s14-pershape-medium-seed_*-optimization.log   diversity、crossover 代
stage3_{baseline,guided}/seed_*/medium/trajectory_metadata.json      η_s / δ_s
```

**GA 搜尋（native，P0 = 11,405）**
```
stage5_native_{baseline,guided}/seed_*/medium/ga_init_evidence.json  §12.3 fail-closed pins、weights_sha256
stage5_native_{baseline,guided}/seed_*/medium/trajectory.jsonl
stage5_native_{baseline,guided}/seed_*/medium/optimization_result.json
stage5_native_{baseline,guided}/seed_*/medium/driver_status.json     （無 DUCTILE_FORCE_P0）
stage5_native_{baseline,guided}/seed_*/medium/*optimization.log      stock warning ×1、Max iterations ×0
stage5_native_baseline/seed_24005/medium/resume_record.json          三個 session
stage5_native_remeasure_control/seed_24005/medium.remeasure.log:35   RESUMED_RUN_PARTIAL_LOG
quarantine/native_gen0_guard_false_positive_20260812/                false-positive degradation marker
```

**7× interleaved remeasure**
```
campaign 1（capped）medium_recheck_control/capped/seed_*/preserved_campaign1_20260812T135613Z/
                      champion_interleaved.campaign1_20260812T135613Z.json
                      champion_interleaved_raw.campaign1_20260812T135613Z.jsonl
campaign 1（native）medium_recheck_control/native/seed_*/preserved_campaign1_20260812T135613Z/  （同上樣式）
campaign 2（capped）stage3_baseline/seed_*/medium/champion_interleaved{,_raw}.json{,l}          canonical path
campaign 2（native）stage5_native_baseline/seed_*/medium/champion_interleaved{,_raw}.json{,l}   canonical path
medium_recheck_summary.json                                          C2 driver summary、finished 14:08:19Z
analyze_medium.py                                                    --campaign 為必填（§6.4）
```

**量測稽核 probe**
```
medium_mechanism_probe_summary.json    warm-up sweep 七個變體（全部 RBS=0）
medium_mechanism_probe/stdout.log      A/D/E/B2/C2 變體；B_longwarmup、C_longwindow 各 25/25 crash
medium_mechanism_probe/sweep_stdout.log
medium_mechanism_probe/ClientParameters_*.ini、result_*.csv
medium_clock_probe_summary.json        control_auto 24/70、pinned_high 23/70、sclk_trace
tiny_gpu5_probe_summary.json           tiny on hip 5：2/70
tiny_mechanism_probe/                  tiny warm-up 不敏感性
medium_remeasure_root_cause.md         根因 memo（含兩個 CORRECTED 2026-08-13 區塊）
medium_remeasure_deviation.md          GPU-5 偏差紀錄
noise/per_shape_noise.json             η_s、δ_s、nonregression_floor、R_s、公式與 method
```

**其他 root**
```
/data1/perlee/rocm-libraries/agent_run/260807-s14-baseline-run/stage2_noise/raw_repeats.jsonl
                                       3-anchor × 7-repeat pilot（medium 0/21 dropouts）
/data1/perlee/rocm-libraries/agent_run/260807-s14-baseline-run/stage2_noise/driver_status.json
                                       HIP_VISIBLE_DEVICES = "5"（within-card contrast 的前提）
/data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-guidance/out-capped/ga-weights-medium.json
                                       Lock B：weights、rho_per_gene、weight_beta、lambda_s
config/s14-pershape-{,guided-}medium-seed_*.yaml                     mtime 2026-08-09 23:07；10 行 diff
```

**Ductile 程式碼參照（`[CODE AUDIT]`）**
```
ga.py:95, 256-273     reduce_fn = np.max；無 Pareto/非支配排序
ga.py:107, 112-119    max_sp_sz、×1.15 膨脹、int(9918×1.15)=11405、<pop_size/5 砍半分支
ga.py:116, 291, 293   decay law 1（floor 512）/ law 2（floor 256）/ 每代套用
ga.py:145-146         w -> exp(-0.25*(w - w.min()))，正規化；weight_beta = 0.25
ga.py:289-293         stock fail-open（Max iterations reached → pop_size // 2）
ga.py:674-682         per_gene_diversity（僅在 observer 附掛時輸出——當時未附掛）
core/population.py:194-205   pairwise Hamming diversity
core/space.py:57, 71  每個個體獨立抽全部 30 個 gene；sizes = 各 gene 候選清單長度
scripts/s14_native_driver.py:473-475          env -u DUCTILE_FORCE_P0
scripts/run_pershape_seed_native.py:139-142   該變數被設定時 hard-fail
scripts/s14_native_remeasure_driver.py:187    "inert here: the remeasure never constructs a GA"
scripts/remeasure_interleaved_champion.py:442-465   逐元素 n_evals 交叉核對 + RESUMED_RUN_PARTIAL_LOG
```

---

## 附錄 B — 一頁摘要（**不是** gate 判定）

| 問題 | 重點 | 狀態 |
|---|---|---|
| native 執行已驗證 | 10/10：`pop_size = 11,405`、`_pop_size = 512`、`large_space`、stock warning ×1、`Max iterations` ×0、`DUCTILE_FORCE_P0` 不存在、weights sha256 = Lock B、0 個 live degradation marker | **PASS** |
| law-1 → law-2 decay | 第 1–9 代 law 1 精確（11,405→554）；law 2 於**第 8–9 代**介入；到第 29 代降至 256–258；兩臂對稱 | **verified** |
| treatment 跨 P0 同一性 | 同一批 config 檔（mtime 2026-08-09）；純新增 10 行；`group_0` 逐位元相同；weights = Lock B | **verified** |
| **Gen0 / gen-10 / AUC**（不受汙染） | capped **3/5 / 3/5 / 3/5**；native **2/5 / 1/5 / 3/5**；要求 ≥4/5 | **MEASURED**（gate 判定見 formal report） |
| **final champion 端點** | C1 2/5·3/5·2/5；C2 3/5·3/5·3/5（capped）／3/5·3/5·3/5（nat C1）／3/5·3/5·2/5（nat C2） | **提議 `NOT_EVALUATED / instrument-invalid`（PENDING）** |
| **兩個 campaign 不一致** | capped median F/G 0.9971（2/5）vs 1.0274（3/5）；C2 於解盲後就地覆寫、無 `superseded_*`、對受測臂更有利 | **兩者皆報告；不平均、不擇一**；**campaign of record 已於 2026-08-15 結案——兩者皆非，由新 campaign 取代（§6.5）** |
| **量測缺陷根因** | `num-warmups = 321` 三 shape 相同 ⇒ medium 只有 ~3.2 ms warm-up，對比 DPM ramp 所需的 ~50 ms | **ESTABLISHED（推論式，無直接鎖頻證據）** |
| warm-up sweep | 48 %→32 %→12 %→8 %→**0 %**（51 ms）→0 %→**4 %**（205 ms） | **拐點清楚，但拐點之上非單調；全部在 RBS=0** |
| 卡別 | tiny-on-hip-5 論證 **SUPERSEDED**；改由 within-card pilot contrast（同卡同 shape，0/21 vs 28–47 %）承載 | **hip 5 平反** |
| **arm-asymmetric 汙染** | `WinnerGFlops` 中位數 G **8,846** vs F **13,360**；「單向 ⇒ 對稱 ⇒ 相消」**不成立** | **arm symmetry `NOT_EVALUATED`，事後不可查證** |
| GA 搜尋曝險 | `best_fitness` 論證 **REPLACED**；有效證據為 `generation_Q_median_any_valid` 與約 1.6 % 的機制上界；champion 解析 40/40 未受汙染 | **residual，非 live suspicion** |
| **Q1 穩健性** | 三項不受汙染子判準在兩個 P0 水準皆未達 ≥4/5；跨 P0 per-seed r = **−0.458** | **方向既未確認也未推翻** |
| **Q2 稀釋** | final 端點 `NOT_EVALUATED`（design §13.6 明文）；Gen0 中心 **+2.0 % → +3.4 %、3/5 → 5/5** | 混合；中心結果穩固 |
| **Q3 (i) 極值擴大** | `ln(extreme F/G)` 平均 **−2.2 % → +1.5 %**；4/5 seed 收窄 | ## **在 medium 上 `REFUTED`** |
| **Q3 (ii) 中心維持／擴大** | 中位數 1.0251 → **1.0331**；**5/5** 為正 | **`SUPPORTED`** |
| **Q3 (iii) large > medium 梯度** | medium 這一側無擴大 | **`REFUTED`**（2026-08-18 更正 —— 原寫 `NOT_EVALUATED`；`s14-large-report.md` §10.7a 已於 2026-08-17 判讀：large **+0.0304**、medium **−0.0080**，兩者方向相反，梯度與預測反號）|
| 有效率產物 | G 98.93–99.08 %、F 98.74–99.12 %（native） | **`ELIMINATED`** |
| 實現 vs 意圖的 Gen0 | 跨 seed 全距 0.003 → <0.001；中心值在 512 與 11,405 之間**未變**；兩者皆 0.568/0.575 vs 預測的 0.6306 | 整體層次已量測；per-value 表 `NOT_EVALUATED` |

---

*本附冊在已完成的 artifact 上以唯讀方式撰寫。沒有任何 run 被啟動、重啟、終止或修改；未執行任何 GPU
工作；未編輯任何其他檔案（formal report、`report-source-index*.md`、design、`working-notes/`、
`staged/` 皆未觸碰）。無 seal、無 commit、無 push。*
