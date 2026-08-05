# QA-04 — 下游 checkpoints S12–S41

> **文件角色：**這是從 [實驗白話導讀 hub](../../ductile-origami-warmstart-experiment-guide.md) 拆分出來的白話導讀主題檔，方便在單一主題上持續討論。它不是 experiment authority，也不是 contract、lock 或 report，不會取代正式的 charter、experiment plan、checkpoint design、lock 或 report。
>
> **衝突處理：**若本檔與正式文件衝突，以 [research charter](../../surrogate-dse-plan.md)、[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)、[active checkpoint index](../README.md) 及各 checkpoint design 為準。
>
> **2026-08-04 current status override：**S10R3 已 terminal negative；S10R4 已 retired／not evaluated；S11 已 sealed `LOCKED_READY`。沒有 S11/S12 result、effective checkpoint lock、report 或 edge；最新狀態仍須對照 active checkpoint index、formal artifacts 與 Git history。
>
> **本檔定位：**下方 S12–S41 都是**尚未執行**的 checkpoint design 白話說明（S11 之後全部 gated）。這裡講的是「設計上打算怎麼做、想得到什麼、通過後交接什麼」，不代表任何一關已經跑過或有結果。每一關的正式數值、公式與 stop rule 以該關 design doc 與 experiment plan 為準。

---

## 主線與交接總覽

S11 之後是一條「先確認訊號、再逐步放大宣稱」的 gated 主線；每一關只有拿到自己的 positive
criterion，才會把 edge 交給下一關。另有一條**條件式** Stage 4 分支，只有在特定 predictor 失敗
且 oracle 仍正向時才會啟動。

```text
S11  guidance lock        ──S1_GUIDANCE_LOCKED──▶ S12
S12  real-score D5 audit  ──D5_PASS─────────────▶ S13
S13  actual Gen0          ──D6_MECHANISM_POSITIVE▶ S20
S20  H10 persistence      ──S2_..._POSITIVE──────▶ S30
S30  held-out freeze      ──S3_REGISTRY_..._LOCKED▶ S31
S31  bounded replication  ──S3_BOUNDED_..._POSITIVE▶（主線在此結束）

條件式分支（predictor-specific 失敗 + oracle positive 才成立）：
S12（predictor-specific failure + oracle+） ┐
                                            ├─▶ S40 activation ──S4_ACTIVATE──▶ S41 learned residual
S31（predictor heterogeneity + oracle+）    ┘
```

| Checkpoint | 一句話 | positive criterion | 交給下一關 |
| --- | --- | --- | --- |
| S12 | 用真實 GPU 分數審核 S11 的 ranking 與 prior | `D5_PASS` | S13 |
| S13 | 在真正的 Ductile Gen0 裡驗證 guidance 有效 | `D6_MECHANISM_POSITIVE` | S20 |
| S20 | Gen0 優勢能否撐到固定 10 代 | `S2_DIRECTIONAL_PERSISTENCE_POSITIVE` | S30 |
| S30 | 凍結兩個 held-out clusters 與程序（不評分） | `S3_REGISTRY_PROCEDURE_LOCKED` | S31 |
| S31 | 凍結程序能否在兩個新 regime 重現 | `S3_BOUNDED_REPLICATION_POSITIVE` | 主線終點 |
| S40 | 條件式：surrogate 是否有資格被公平測試 | `S4_ACTIVATE` | S41 |
| S41 | learned residual 能否在 held-out frame 勝過 Formocast | `S4_LEARNED_RESIDUAL_POSITIVE` | 終點（無自動 edge） |

每一關的正式規則見對應 design doc；下方逐關以同一套結構說明：**目的 → 假設/反證 → 消費什麼
→ 設計內容 → 想得到什麼結果 → 結果與交接**。

---

## 10. S12 — Real-score D5 audit

正式規則見 [S12 design](../s12-stage1-real-score-ranking-oracle-audit-design.md) 與
[S11／S12 fixed-frame amendment](../s11-s12-fixed-frame-measurement-amendment.md)。

### 10.1 一句話目的

S11 只用 Formocast 的模型分數建 guidance（label-blind）。**S12 是第一關真正拿真實 GPU
GFLOPS 來檢驗**：S11 排出來的順序、以及拆解後的 per-gene prior，到底對不對得上真實高品質
config。

### 10.2 假設 / 反證

- **假設（S12-H1）**：在預鎖的 fixed-256 finite frame 下，Formocast 的 whole-config ranking
  與 factorized prior 能通過 D5，且 factorized 的 directional prior-mass 指標同時**嚴格勝過**
  baseline 與 same-entropy shuffle。
- **反證 / inconclusive**：ranking 或 lift 低於門檻；factorized prior 打不贏 baseline 或
  shuffle；coverage／correctness／ESS／support 不足；cross-fitted oracle 不支持 factorized
  main effect；或任何 D5 label 回洩到 S11 的 gene／weight／shuffle／超參數（label firewall 破
  口）。

### 10.3 消費什麼（來自上游）

- S11 的 `S1_GUIDANCE_LOCKED`：frozen guidance、guidance hash、D5 sample IDs、strata、folds、
  measurement schedule 與 analysis revision——這些**都必須在第一個真實 label 前進入 effective
  lock**。
- S11 的 global `Uexec` catalog（8,192 accepted-occurrence frame 去重後的 executable 身分）。
- `S11-S12-FIXED-FRAME-20260803` amendment：固定 `M_HT` estimator identity 與 raw-denominator
  語意。

### 10.4 實驗設計內容

- 從 `Uexec` **無放回**抽 **恰好 256 個 unique executable 身分**：依 `Fscore` occurrence mass
  分成 **10 個 weighted deciles ＋ 1 個 executable-unscored stratum**（largest-remainder，每個
  非空 stratum 至少 1 個）。
- **分析單位是 config 身分**：同一身分的 3 個 size 是重複觀測、留在同一 block/fold，不當成
  獨立樣本；768（256×3）個 config×size 觀測不是 768 個獨立單位。
- **label firewall（labels 前凍結）**：`T_D5`（真實高品質集合的 cutoff，用 baseline 權重定到
  90th percentile）、strata、folds、all-size quality reducer 全部先鎖；每個被選身分要先通過
  pinned native/runtime conformance、normal generate/compile、correctness、noise readiness，才
  能量 GFLOPS。
- 五-fold config-level cross-fitting；metric 平手用真 midrank，不得用抽樣順序 tie-break。

```text
frame        = fixed 256 unique Uexec 身分（無放回）
strata       = 10 Uscore deciles + 1 executable-unscored
每身分       = 3 sizes（重複觀測，不是獨立 config）
denominator  = 完整 global Fraw raw-occurrence mass（不是只算被選中的）
```

### 10.5 想得到什麼結果 + metric 意義

想確認「Formocast 的相對排名與拆解後的 prior，真的把真實高品質 config 排前面」。各 metric 與
門檻：

| Metric | 意義（高/低） | 門檻 |
| --- | --- | --- |
| aggregate Spearman | whole-config 排名與真實分數的一致度，越高越準 | ≥0.25（borderline `[0.20,0.25)`） |
| top-decile lift | 高品質 config 集中在前段的倍率，越高越好 | ≥2.0（borderline `[1.5,2.0)`） |
| size direction | 3 個 size 方向是否一致 | ≥2/3 |
| `M_HT`（factorized prior-mass） | arm 把多少完整 raw mass 放進真實 top-decile 的 **design-based directional index** | 須同時**嚴格勝** baseline 與 shuffle |
| ESS | design 權重的有效樣本數，太低表示估計不穩 | ≥25（每個相關 arm） |
| coverage | 計畫身分實際拿到真實分數的比例 | ≥0.95 |

`M_HT` 是 `S12-DIRECTIONAL-FINITE-FRAME-HT-EXACT-DENOMINATOR-v1`：它是 **directional index、
可大於 1、不是 bounded probability**；分母用完整 global `Fraw`；禁止 clip／winsorize／post-hoc
normalize 或改用 sampled denominator。oracle（cross-fitted，用 held-out real-score marginals）
只作**診斷**——判斷失敗是「Formocast ranking/marginalization 不行」還是「per-gene hook 表達力
不足」——它**不是 treatment arm，也不能把 fail 改成 pass**。

### 10.6 結果與交接

- **`D5_PASS`**：ranking、`M_HT` dominance、ESS、coverage、correctness、bootstrap/permutation
  與 label firewall 全過 → 交給 **S13**（seal compact gate record）。
- **`D5_BORDERLINE_INCONCLUSIVE` / `D5_FAIL`**：borderline 或明確失敗 → 於 S12 terminal，無
  edge；並可依 §7 taxonomy 定位到 `FT-MODEL-RANK`／`FT-MODEL-MARGINAL`／
  `FT-HOOK-EXPRESSIVENESS`／`FT-HEURISTIC-SATURATION`（shuffle 打平或勝）／`FT-ENTROPY-ONLY`。
- **條件式 → S40**：只有當 S12 的 negative 是**明確的 predictor-specific failure**（例如
  KernelWriter 表達力）**且 oracle positive** 時，才形成通往 S40 的 conditional edge；這**不會**
  解鎖 S13。
- **claim boundary**：`D5_PASS` 只支持「在 fixed-256 finite frame 內有 ranking 與 prior-mass
  方向性訊號、且已準備好測 Gen0」；**不**代表 Gen0 真的變好、不代表能推廣到 `Uexec` 以外、也
  不代表 speedup 或 production readiness。

---

## 11. S13 — Actual Gen0 mechanism

正式規則見 [S13 design](../s13-stage1-actual-gen0-mechanism-design.md)。

### 11.1 一句話目的

把 S11 的 guidance 真的接進 **Ductile 的 Gen0 sampler**，看它在「實際抽出的初始 population」
裡，能不能比既有 guidance 與 shuffle 更集中地抽到高品質 config。這是第一次測「機制真的有作
用」，不只是「模型分數對得上」。

### 11.2 假設 / 反證

- **假設（S13-H1）**：在實際 Gen0 裡，Formocast residual guidance（F arm）的 top-decile 命中
  方向**同時**勝過既有 guidance（G）與 shuffle（S），且 median 品質、correctness、validity、
  sampler realization 都守住 guardrail。
- **反證**：`P0`／proposal 序列化／candidate order／weight order／replay 不可重現；F 打不贏 G；
  F 打不贏 S；median 品質系統性退步；出現 S12 沒有的新 correctness/validity 失敗；replay
  envelope 有系統性異常或結果依賴 set 迭代順序而非 canonical proposal identity。

### 11.3 消費什麼（來自上游）

- S12 的 `D5_PASS` compact gate record（含 frozen `t_D5`／`T_D5`、S11 weights/shuffle bundle、
  noise/correctness 證據）。
- Sampler/validity/mapping revisions；`P0` resolution rule、formal/replay seeds、序列化與 join
  schema——都在產生 proposal 前先鎖。

### 11.4 實驗設計內容

- **四個 arm 都要跑**：U（無 guidance）、G（既有 YAML/GEKO guidance）、F（G + Formocast
  residual guidance）、S（G + same-entropy shuffled residual guidance，控制「只是變集中」的
  效果）。
- **只跑 Gen0（`n_gen=1`）**，不進 crossover/mutation/selection；`period=0`；**3 對 paired
  seeds**。
- `requested pop_size = 64`，但 Ductile constructor 可能依最大 categorical key 放大 resolved
  `P0`；**實際 `P0` 必須在 labels 前鎖定**，若 `P0 != 64` 需先 amendment 再重估成本（不能看到
  結果才改）。
- 所有 arm/seed 的 formal proposal 先鎖再 benchmark；canonical config-set 用 proposal identity
  而非 set 迭代順序；跨 arm/seed 去重後做 multiplicity-aware join。

```text
arms         = U / G / F / S（四臂全跑）
n_gen = 1，period = 0，paired seeds = 3
requested pop_size = 64（resolved P0 需在 labels 前鎖定）
primary endpoint = Gen0 top-decile hit rate
```

### 11.5 想得到什麼結果 + metric 意義

想確認「guidance 這個機制真的把 sampler 導向高品質區，而且是**訊號**在起作用、不只是 entropy
集中」。

- **top-decile hit rate（primary）**：每個 arm 前 10% proposal 落進 `T_D5` 的比例；要求 **F 嚴格
  勝過 G 與 S**。
- **paired deltas**：F−G 至少 2/3 seeds >0（勝既有 guidance）；F−S 至少 2/3 seeds >0（勝
  shuffle → 是訊號不是 entropy）。
- **median-quality guardrail**：至少 2/3，確保沒有系統性退步。
- **一致性/正確性**：proposal hashes/order/weights/space 一致、sampler replay 無系統異常、無
  新增 correctness failure。
- **3 seeds 只支持方向性 mechanism evidence**，不做顯著性宣稱、也不等於 speedup。

### 11.6 結果與交接

- **`D6_MECHANISM_POSITIVE`**：上述全過 → 交給 **S20**（seal compact gate record；此時整個
  `CU-S1-MECHANISM` tranche 才隨 S11/S12/S13 records 一起做 terminal report
  `reports/gen0-factorization-mvp-report.md`）。
- **negative/inconclusive**：`FT-PLUMBING`（可重現性壞）、`FT-GEN0-MECHANISM`（機制無方向性
  增益）、`FT-HEURISTIC-SATURATION`（F 不勝 G）、`FT-ENTROPY-ONLY`（F 不勝 S）、
  `FT-INCONCLUSIVE`——都於 S13 terminal，不能加代數/加 seed/用 oracle 救回。
- **claim boundary**：positive 只代表「Gen0 這一代，guidance 機制有方向性作用」；**不**代表
  能撐到 10 代（S20）、能在新 cluster 重現（S30/S31）、或 speedup/production。

---

## 12. S20 — 固定 10 代 persistence

正式規則見 [S20 design](../s20-stage2-h10-persistence-design.md)。

### 12.1 一句話目的

Gen0 有優勢不代表撐得久。S20 問：在同一個 development cluster、跑滿 **固定 10 代（H10）**，
F 的優勢會不會被後續 mutation/selection 洗掉（washout），最終品質會不會退步。

### 12.2 假設 / 反證

- **假設（S20-H1）**：用全新 paired seeds，F 在 best-so-far log-quality **AUC** 上同時勝 G 與
  S，H10 末端保有優勢，且最終獨立重量後品質不退步（在 noise-derived non-inferiority 界內）。
- **反證**：F−G 或 F−S AUC/方向失敗；H10 末端 retention 失敗；最終重量顯示 regression；formal
  run 沒達到預鎖的共同 support `U_floor`；checkpoint/resume parity、mapping、plumbing 或
  correctness 壞；或 Stage 1 選過的 seed 污染 formal denominator。

### 12.3 消費什麼（來自上游）

- S13 的 `D6_MECHANISM_POSITIVE`：parent 固定的 G/F/S arm 定義、Stage 1 guidance、超參數、
  genes、weights、YAML 空間。
- **全新 paired seed bundle**（不得重用 Stage 1 seeds）。

### 12.4 實驗設計內容

- 三個 arm：G / F / S；**`n_gen=10`、`period=0`、5 對全新 paired seeds**，與 Stage 1 seeds
  完全分離。
- **measurement boundary**：primary x 軸只算 complete-evaluation（完整鎖定的候選評估）；`U_floor`
  在 formal run 前先鎖。
- **H5 blinding**：H5 只是 blinded operational checkpoint，只看運行健康/完整性，**不能看到 H5
  比較結果就決定要不要跑 H10**；必須跑滿 H10，H5-only pilot 不能滿足 S20 或解鎖 S30。

```text
arms = G / F / S；n_gen = 10，period = 0；fresh paired seeds = 5
primary = best-so-far log-quality AUC（積分到預鎖 U_floor）
H5 = blinded operational only；必須完整跑到 H10
```

### 12.5 想得到什麼結果 + metric 意義

- **AUC（primary）**：`AUC_F − AUC_G` 與 `AUC_F − AUC_S`。positive gate：F−G AUC 至少 4/5 為
  正、F−S AUC 至少 4/5 為正。
- **H10 endpoint**：F>G 至少 3/5（末端仍領先）。
- **final non-inferiority**：至少 4/5（最終重量沒退步）。
- 全程無 correctness/plumbing/mapping/systematic-fill failure。

### 12.6 結果與交接

- **`S2_DIRECTIONAL_PERSISTENCE_POSITIVE`**：交給 **S30**；並確認 H10 budget 可行與 fresh-seed
  策略。
- **failure**：`FT-PERSISTENCE-WASHOUT`（AUC/retention 壞）、`FT-SHORT-HORIZON-REGRESSION`
  （AUC 正但末端退步）、`FT-EVALUATION-SUPPORT`（沒達 `U_floor`）、`FT-ENTROPY-ONLY`（F 不勝
  S）——terminal。H5-only/減 seed/減 arm 的提案一律 `blocked-awaiting-user-decision`。
- **claim boundary**：只證「單一 development cluster 的 H10 短程 persistence」，**不**是完整
  convergence 或 system speedup。

---

## 13. S30 — Held-out registry / procedure freeze（不評分）

正式規則見 [S30 design](../s30-stage3-heldout-registry-freeze-design.md)。

### 13.1 一句話目的

要證明「方法能換場地重現」前，得先**公正地選好新場地並凍結程序**。S30 是一道**純 pre-label
凍結關**：它只鎖定兩個 held-out clusters 與整套程序，**完全不跑 score、不看任何 real label**。

### 13.2 假設 / 反證

- **假設（S30-H1）**：能用非 outcome-driven 規則，預先註冊兩個真正獨立、符合 parent scope 的
  primary clusters，並在任何 Formocast score 或 real label 出現前，鎖好 unique procedure、
  reserve cutover 與 two-slot denominator。
- **反證 / blocked**：cluster 身分/選取 provenance 不完整；clusters 不獨立、dtype/layout/arch
  不符或 same-space size 不足；reserve 選取或 cutover 可在看到分數後更改；frozen procedure 含
  cluster-specific 的可調重 tune；或兩 primary slot／two same-space sizes／reserve
  priority-cutover／two-slot denominator／frozen procedure 沒鎖。

### 13.3 消費什麼（來自上游）

- S20 的 `S2_DIRECTIONAL_PERSISTENCE_POSITIVE`：已確認的 frozen Stage 1/2 procedure（genes、
  weights、超參數、algorithm）。
- 候選 cluster inventory 與 access/artifact/mapping 可行性證據（**還沒有任何 score/label**）。

### 13.4 實驗設計內容

- 註冊 **2 個 primary clusters**，每個含 **2 個 same-space size 身分**（dtype/layout/arch 同
  development cluster）；最多 **1 個 optional technical reserve**，priority 與 prelabel cutover
  規則固定。
- **denominator 固定為 two-slot**；reserve 只能因 access/artifact 損壞或 deterministic mapping
  technical failure 替換，且替換必須在該 slot 的**第一個 Formocast score 與第一個 real label
  之前**發生。
- development cluster 排除在 held-out denominator 外。**S30 不跑 D5、不跑 GA。**

### 13.5 想得到什麼結果 + metric 意義

S30 沒有 performance metric——它的「結果」是**鎖定狀態本身**：兩個 primary slot ＋ optional
reserve ＋ cutover 規則 ＋ two-slot denominator ＋ frozen procedure 全部在第一個分數前鎖好。
加上 cluster 相容性（dtype/layout/same-space size）與 access/artifact/mapping 可行性（純技術、
無 outcome 資料）通過。意義：**replication 的分母是預先承諾的，不會 select-on-success**。

### 13.6 結果與交接

- **`S3_REGISTRY_PROCEDURE_LOCKED`**：交給 **S31**（compact gate record）。
- **blocked/inconclusive**：只做得到 single-cluster pilot → `blocked-awaiting-user-decision`
  （不算完成 S30）；資源暫時不可用 → Layer-C record+notify（非科學結果）；若 score/label 提早
  出現 → held-out seal 破，需 fresh registry/new lock；outcome-driven replacement → 禁止。
- **claim boundary**：只證「replication registry 與 procedure 已凍結」，**不**代表 transfer 有
  效。

---

## 14. S31 — Two-cluster bounded replication

正式規則見 [S31 design](../s31-stage3-bounded-replication-design.md)。

### 14.1 一句話目的

在 S30 鎖好的兩個新 cluster 上，用**完全凍結、不再 per-cluster 重 tune**的程序跑一遍，看 F 的
方向性優勢能不能**在兩個新 regime 都重現**。這是主線最後一關。

### 14.2 假設 / 反證

- **假設（S31-H1）**：凍結程序在兩個預註冊 cluster 都通過 D5 audit，且各自的 fresh H10 paired
  seeds 都重現 F 相對 G 與 S 的 AUC、末端 retention 與最終 non-inferiority。
- **反證 / inconclusive**：任一 cluster D5 fail 或 inconclusive；任一 cluster 的 H10 AUC/末端/
  最終 guardrail fail；兩 cluster 方向不一致（一過一敗 → heterogeneity）；mapping/correctness/
  support/plumbing 或 held-out seal 破；或看到分數後替換 cluster、改程序、只報成功那一個。

### 14.3 消費什麼（來自上游）

- S30 的 `S3_REGISTRY_PROCEDURE_LOCKED`：兩個 primary slot、reserve（含預鎖 cutover）、frozen
  Stage 1/2 procedure、two-slot denominator、same-space size 身分。
- 每個 cluster 各自的 fresh paired seeds。

### 14.4 實驗設計內容

每個 cluster 依序：

1. **D5 audit**（model-only、label-blind）：用與 S12 相同的 estimator identity
   `S12-DIRECTIONAL-FINITE-FRAME-HT-EXACT-DENOMINATOR-v1`（`M_HT` 一樣**可大於 1、非 bounded
   probability、禁止 clip/normalize**）。
2. **D5 結果**：`D5_PASS` → 進 conditional H10；`D5_FAIL`/inconclusive → 該 cluster 停 GA，但
   **仍留在 denominator**（不移除、不補償）。
3. **conditional H10**（僅 D5_PASS）：G/F/S、每 cluster fresh paired seeds、程序同 S20，**不做
   cluster-specific 重 tune**。

**two-slot denominator 規則**：兩個 cluster 不論結果都留在分母；**不能只 roll up 成功者、不能
跨 cluster 平均救回**；size 不是額外 cluster。

### 14.5 想得到什麼結果 + metric 意義

- 每 cluster D5：`M_HT` 與 oracle gap（audit 完成即算通過該關；D5 fail 則停該 cluster GA 但留
  分母）。
- 每 cluster H10（若 D5_PASS）：best-so-far log-quality **AUC**（F−G、F−S）、末端 retention、
  最終 non-inferiority。
- **rollup**：2/2 都過才是主線成功；1/2 是 regime heterogeneity；0/2 是 replication 被否證。

### 14.6 結果與交接

- **`S3_BOUNDED_REPLICATION_POSITIVE`（2/2 過）**：**主線在此完成**，沒有自動下游 checkpoint。
- **`FT-REGIME-HETEROGENEITY`（一過一敗）**：只有當 heterogeneity 是 **predictor-specific 且
  oracle positive** 時，才形成通往 **S40** 的 conditional edge（否則就是異質、停）。
- **0/2 或 access/mapping blocked**：replication 被否證 / inconclusive。只完成一個 cluster =
  downgrade pilot，不算 S31 完成。
- **claim boundary**：positive 只證「在同一 gfx942 平台、兩個預鎖 held-out cluster 的 **bounded
  replication**」；**不**能寫成 MI300X workload generalization、convergence 或 speedup。

---

## 15. S40 — Surrogate activation gate（條件式）

正式規則見 [S40 design](../s40-stage4-surrogate-activation-gate-design.md) 與 rebaseline
[§9.2 activation-before-instantiation](../s10r4-retirement-s11-rebaseline-authority.md)。

### 15.1 一句話目的

Stage 4（用 learned residual 補 Formocast）**不是必跑**。S40 是一道嚴格的**啟動閘**：只有當
「Formocast 特有的失敗 + oracle 仍支持 factorized main effect」這個觸發條件成立、**而且**資料
足夠時，才讓 S41 有資格被公平測試。

### 15.2 假設 / 反證

- **假設（S40-H1）**：在合法 predictor-specific + oracle-positive 觸發且資料齊備的前提下，所有
  forbidden causes 都不存在，且能鎖好獨立合格 clusters 與 prospective 測試條件 → S41 有可驗證
  的科學基礎。
- **反證**：真正的原因其實是 access/mapping/hook 表達力/plumbing/Gen0/washout/regression/
  heuristic saturation/純 coverage-noise；oracle 不支持 factorized main effect；宣稱齊備的
  clusters 其實不獨立或未達 data floor；或 prospective 第四 cluster 由結果挑選。

### 15.3 消費什麼（來自上游）

只接受兩種 committed 觸發之一：**S12 的 predictor-specific failure + oracle-positive edge**，或
**S31 的 predictor heterogeneity + oracle-positive edge**；加上合格 cluster 資料。

### 15.4 實驗設計內容（activation before instantiation）

**先有觸發＋資料齊備才「instantiate」，否則什麼都不建立**：

- 無合法觸發 → `not_activated`（不執行、不建立 report/decision/lock/commit）。
- 觸發成立但資料不足 → `data_pending / not_activated / not_evaluated`；`FT-SURROGATE-DATA-INSUFFICIENT`
  只是 operational readiness provenance，**不是科學 negative**；有新的 prelabel-qualified data
  才重評。
- 只有觸發＋資料齊備同時成立才 instantiate，然後才做 forbidden-cause audit、data-floor 確認與
  `S4_ACTIVATE` 判定。

**data floor（無替代、預鎖）**：4 個獨立 cluster；每 cluster ≥256 unique configs 且 ≥2 sizes；
總計 ≥1,024 configs 且 ≥2,048 config-size labels；inclusion/correctness/mapping/coverage/lineage
完整。已有 3 個合格 cluster 時，最多再 prospectively seal 1 個第四 cluster（選取規則在 labels
前鎖）。注意 `qualified_for_stage4_data` 與 `D5_PASS` 是不同欄位。

### 15.5 想得到什麼結果 + metric 意義

S40 的「結果」是一個**資格判定**，不是 performance：`S4_TRIGGER_ELIGIBLE`（predictor-specific
failure 成立且 forbidden patterns 全不在）＋ `S4_DATA_GATE_PASS`（data floor 與 prospective
fourth-cluster 規則過）＝ `S4_ACTIVATE`。positive 只代表「可以公平地測 S41」，**不**代表
surrogate 有效。

### 15.6 結果與交接

- **`S4_ACTIVATE`**：唯一 outgoing edge `S4_ACTIVATE -> S41`（seal compact gate record）。
- **not_activated / data_pending**：不建立 report/lock/commit；只有 instantiated 後的 negative
  才寫 `reports/staged/s40-stage4-activation-report.md`。
- **claim boundary**：S40 positive 只說「S41 有資格被測」，本身不含任何模型係數、預測或 GA 結
  果（那些在 S40 邊界內都禁止）。

---

## 16. S41 — Learned residual analysis（條件式終點）

正式規則見 [S41 design](../s41-stage4-learned-residual-analysis-design.md) 與 rebaseline
[§9.3 claim narrowing](../s10r4-retirement-s11-rebaseline-authority.md)。

### 16.1 一句話目的

在凍結的 finite held-out frame 裡，用**單一預註冊模型**（inclusion-weighted ridge residual
correction）學 Formocast 的殘差，看它在每個 held-out 單位上是否**嚴格勝過** Formocast 的
ranking、prior-mass 與 oracle gap。這是條件式分支的終點——純 offline 分析，不跑真正的 GA。

### 16.2 假設 / 反證

- **假設（S41-H1）**：每個 parent 指定的 primary held-out 單位，learned residual 的 observed
  ranking 點值**嚴格高於** Formocast；factorized `M_HT` 點值**嚴格高於** Formocast-factorized
  與 shuffle；observed oracle-gap 點值**嚴格更小**。
- **反證 / inconclusive**：任一 primary 單位任一 gate 沒嚴格改善；**平手（tie 不算 positive）**；
  support/coverage/mapping/importance 不足；preprocessing/feature/lambda 選取讀到 outer-test
  labels；用了 forbidden feature 或 row-random split；factorization/hook 偏離凍結程序；`M_HT`
  被 clip/normalize 或分母改動。

### 16.3 消費什麼（來自上游）

- S40 的 `S4_ACTIVATE` 與合格 cluster registry（4 clusters／≥256 configs/cluster／≥2 sizes／
  ≥1,024 configs／≥2,048 labels）。
- `S11-S12-FIXED-FRAME` 的 estimator identity 與 S12 的 exact `T_D5`／`rho_j`／aliases／
  all-size aggregate quality／no-clipping 語意（機械繼承）。

### 16.4 實驗設計內容

- **單一模型**：inclusion-weighted ridge residual correction；**target = `log(real latency) −
  log(Formocast latency)`**；ridge grid `{1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100}`；intercept 不
  penalize；preprocessing training-only（含 unknown bucket）。
- **split：cluster-held-out（LOCO），禁止 random row split**——同 cluster 的 sizes/repeats/
  duplicates/derived rows 永遠同 fold；inner selection 只用 outer-training clusters，選 equal-
  cluster mean MSE，平手選較大 `ridge_lambda`。
- feature manifest 必須 label-blind（禁止 real score/oracle/cluster-ID/outcome-derived 欄位）。
- **不跑 actual GA**；若是「3 預鎖 + 1 prospective 第四 cluster」，只有第四 cluster 是 primary
  gate 單位（前三只作 secondary sensitivity）。

### 16.5 想得到什麼結果 + metric 意義

每個 primary held-out 單位的**三道 gate 都要嚴格通過**：

- **ranking**：用 frozen inclusion/design 權重的 aggregate weighted Spearman，learned 嚴格勝
  Formocast。
- **prior-mass `M_HT`**：learned factorized `M_HT` 同時嚴格勝 Formocast-factorized 與 shuffle
  （同樣可大於 1、非 probability、不得 clip）。
- **oracle gap**：`oracle_gap_a = max(0, M_HT,oracle − M_HT,a)`，learned 的嚴格更小。

**tie 不算 positive；support/coverage/ESS 不足算 inconclusive。** 不做 cross-unit averaging 救
回。

### 16.6 結果與交接

- **`S4_LEARNED_RESIDUAL_POSITIVE`**：每個 primary 單位三 gate 全嚴格過 → positive closeout
  （報告 `reports/learned-residual-surrogate-report.md`）。**S41 沒有自動 outgoing edge**——主線
  的終點是 S31 的 `S3_BOUNDED_REPLICATION_POSITIVE`，S41 是條件式分支的分析終點。
- **failure**：`FT-SURROGATE-NO-GAIN`（任一單位 valid negative）、tie（不 positive）、
  `FT-INCONCLUSIVE`（support 不足）、leakage/split 違規（evidence invalid）。
- **claim boundary（重要）**：positive **只**支持「凍結 finite held-out frame 內、觀測到的
  point-direction 比較」；**不**代表 practical effect、stability、statistical significance、
  population generalization、prospective replication、production readiness 或 actual-GA benefit。
  更強的宣稱需要未來另做 prospectively locked design（含 effect margin 與 uncertainty rule）。
