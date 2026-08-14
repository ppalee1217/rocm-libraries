# S14 `NATIVE-P0-ROBUSTNESS-20260811(b)` — native-Gen0（11,405）**medium** 分析

> **狀態：MEASURED 5/5，quarantined 分析。Two-sided；不作任何超出資料所能支持的結論。**
> 本檔為 staged checkpoint 分析，**不是 authority document**。若與 research charter、experiment plan 或
> `s14-stage1-full-ga-outcome-design.md` §12 衝突，一律以後者為準。
> 本檔內容尚未寫入 `report-source-index.md` 或任何 authority doc；authority doc 可能需要的項目集中於
> **§9（給 main session）**。
>
> **Anti-fabrication。** 以下每個數字後面都附其來源路徑。未量測的量標為 `NOT_EVALUATED`；
> `NOT_EVALUATED ≠ no effect`。
>
> **Run root（host）：** `/data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-baseline`
> （container：`/src/rocm-libraries/agent_run/260809-s14-pershape-baseline`）。以下所有相對路徑除另有說明外
> 皆位於該 root 之下。Authority：`s14-stage1-full-ga-outcome-design.md` §12
> （`NATIVE-P0-ROBUSTNESS-20260811` + `(b)` 2026-08-12）。
>
> **兩臂的範圍。** `G` = Arm G = BASELINE（所有 free genes 使用 uniform `p0`）。
> `F` = Arm F = GUIDED（在兩個 activated genes 上使用 Lock-B capped `p1`）。`+ve % = guided faster.`

---

## 1. 驗證這些確實是 native-Gen0 的 run

五個 seed × 兩臂全部通過 §12.3 預先登錄的每一項 fail-closed 條件。

### 1.1 建構期的 pins（`ga_init_evidence.json`）

*來源：`stage5_native_{baseline,guided}/seed_{24001..24005}/medium/ga_init_evidence.json`（10 個檔案）。*

| 欄位 | 要求（§12.3） | 觀測值 | 通過的 seed／臂 |
|---|---|---|---|
| `pop_size_at_construction` | `11405` | `11405` | **10/10** |
| `_pop_size_at_construction` | `512` | `512` | **10/10** |
| `decay_type_at_construction` | `large_space` | `large_space` | **10/10** |
| `native_p0_variant` | `true` | `true` | **10/10** |
| `n_gen` / `period` | `30` / `5` | `30` / `5` | **10/10** |

`_pop_size_at_construction == 512` 與 `pop_size_at_construction == 11405` 同時出現，正是 `ga.py:113–118`
膨脹分支的確切簽名（`int(9918 × 1.15) = 11405`），而 `decay_type == "large_space"` 是安裝於 `ga.py:116`
的 law-1 decay。這正是 capped run 以 `DUCTILE_FORCE_P0` 刻意抑制掉的建構狀態。

### 1.2 stock warning 存在；`DUCTILE_FORCE_P0` 不存在於 GA 環境中

十份 GA log 每一份都含**恰好一次**的 stock 行：

```
GA:WARNING Some variables have a larger search space than pop_size. Increasing pop_size for the first generations.
GA:INFO GeneticAlgorithm(pop_size=11405, n_gen=30, period=5, tol=0.0008, div_thr=0.5, soo=False)
```

*來源：`stage5_native_{baseline,guided}/seed_*/medium/*optimization.log`，第 1 與第 3 行。*

`DUCTILE_FORCE_P0` 在全部十次 run 所記錄的搜尋環境中**不存在**
（`driver_status.json → environment` 只含 `CMAKE_BUILD_PARALLEL_LEVEL`、`DUCTILE_PERSIZE_RBS`、
`HIP_VISIBLE_DEVICES`、`PYTEST_XDIST_WORKER`、`PYTHONPATH`）。
*來源：`stage5_native_{baseline,guided}/seed_*/medium/driver_status.json`。*
上游以結構性方式強制：launcher 透過 `env -u DUCTILE_FORCE_P0` spawn
（`scripts/s14_native_driver.py:473–475`），而 runner 在該變數被設定時直接 hard-fail
（`scripts/run_pershape_seed_native.py:139–142`）。

**有一件事絕不可誤讀。** `DUCTILE_FORCE_P0=1` *確實*出現在
`champion_interleaved.json → measurement_metadata.environment` 之中。那是 **remeasure** 程序，不是搜尋。
remeasure 只重播兩個固定的 champion config，從不建構 `GeneticAlgorithm`；該變數在那裡行為上是惰性的，
之所以設定它，只是為了讓 remeasure 環境與 capped remeasure 保持逐位元可比
（`scripts/s14_native_remeasure_driver.py:129`，註解為 "inert here"）。
*來源：`stage5_native_baseline/seed_24001/medium/champion_interleaved.json`。*

### 1.3 Treatment 內容 — 與 capped 實驗完全相同，且侷限於 2 個 gene

- Guided 的 `weights_gene_keys` 在 **5/5** 個 seed 上恰為 `["group_0", "DepthU", "1LDSBuffer"]`；
  `sampling_prob_genes` 恰為 `["1LDSBuffer", "DepthU", "group_0"]`。
  Baseline 的 `weights_gene_keys` 在 **5/5** 上恰為 `["group_0"]`。
  *來源：同樣那十份 `ga_init_evidence.json`。*
- `weights_sha256` 在五個 guided seed 之間完全相同（`d64ebd349b0492b1092beadca16f8084…`），
  在五個 baseline seed 之間亦然（`56c34446385e93138944082b1801649…`）。
- guided config 與 baseline config 的差異**只有**兩筆追加的 weight entry。將
  `config/s14-pershape-medium-seed_24001.yaml` 與
  `config/s14-pershape-guided-medium-seed_24001.yaml` 做正規化 diff，恰得 16 行新增：`DepthU` 與
  `1LDSBuffer` 的 weight 向量。`group_0` 的 9,918 個 GEKO weight 在兩臂中**逐位元相同**。
- 那兩個向量與 Lock B **逐位元組相等**：
  `agent_run/260809-s14-pershape-guidance/out-capped/ga-weights-medium.json`
  （`DepthU = [6.250864028930664, 2.7637107372283936, 10.506025314331055 ×4]`、
  `1LDSBuffer = [1.6076256036758423, 4.42307186126709]`；`rho_per_gene = {DepthU: 0.566015625,
  1LDSBuffer: 0.8}`）。
- 重放 Ductile 自身的變換 `exp(−0.25·(w − min w))` 並正規化（`ga.py:145–146`），精確重現
  §3.4b.3：`DepthU → [0.2096, 0.5011, 0.0723, 0.0723, 0.0723, 0.0723]`、
  `1LDSBuffer → [0.6690, 0.3310]`、`group_0 → Σp² = 1.754e-4`，兩臂相同。
- **native 與 capped 的 run 在磁碟上消費的是同一批 config 檔**（`config/…medium-seed_*.yaml`，
  mtime 2026-08-10，即在 native 波次之前）。因此在兩個 P0 水準上，treatment *字面上*是同一個物件，
  這正是 Q2 所需的前提條件。

### 1.4 沒有 `native_gen0_degraded.json` — 已再次驗證

全 repository 搜尋（`find /data1/perlee/rocm-libraries -name 'native_gen0_degraded*'`）回傳
**恰好兩個**路徑，兩者都在 quarantine 目錄內：

```
quarantine/native_gen0_guard_false_positive_20260812/native_gen0_degraded.json
quarantine/native_gen0_guard_false_positive_20260812/native_gen0_degraded.FALSE_POSITIVE_ANNOTATION.json
```

`stage5_native_baseline/` 或 `stage5_native_guided/` 之下存在**零**個 live 的 degradation marker。
被 quarantine 的那一對是**已知的 false positive**，且**不**作為 §12.7 的觀察回報 —— 見下方 §2.2。
佐證「從未發生 stock fail-open」的正面證據：十份 GA log 每一份都含**零**行 `Max iterations reached`，
且每一條 trajectory 的第 1 代紀錄都有 `generation_candidate_count == 11405`。
*來源：`stage5_native_{baseline,guided}/seed_*/medium/trajectory.jsonl`（gen-1 紀錄）；
`*optimization.log`。*

### 1.5 觀測到的每代母體，以及 decay law 的切換點

觀測到的 `generation_candidate_count`，seed 24001 arm G（在 **10/10** 次 run 中，第 1–9 代皆相同）：

| gen | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | … | 29 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 母體 | **11,405** | 5,958 | 3,235 | 1,873 | 1,192 | 852 | 682 | 597 | 554 | **494** | 446 | 408 | … | 258 |

*來源：`stage5_native_baseline/seed_24001/medium/trajectory.jsonl`。*

- 第 1→9 代精確依循 **law 1**（`ga.py:116`，`int(512 + (sz−512)/2)`）：
  `11405 → 5958 → 3235 → 1873 → 1192 → 852 → 682 → 597 → 554`。在每一個 seed 與每一臂中，
  預測值與觀測值每一步都精確到整數相符。因此 law 1 確實已安裝且生效，如 §12.3 所要求。
- **law 2 確實有介入**，但比 capped run 更晚。第一個 post-crossover 尺寸是 `494`，
  即 `int(256 + (554−256)/1.25) = 494` —— 這是 `ga.py:291` 的 law，而非 law 1 的 `533`。所以這個切換
  在母體數列本身就看得見，不只出現在 diversity 欄位。
- Crossover 代數（`diversity < div_thr = 0.5`），取自 GA-log 的統計表：

  | | 24001 | 24002 | 24003 | 24004 | 24005 |
  |---|---:|---:|---:|---:|---:|
  | native G | 9 | 9 | 9 | **8** | 9 |
  | native F | **8** | 9 | 9 | 9 | **8** |
  | capped G（參考） | 7 | **6** | 9 | 8 | 10 |
  | capped F（參考） | 9 | 8 | 8 | 8 | 8 |

  *來源：`stage5_native_{baseline,guided}/seed_*/medium/*optimization.log` 與
  `stage3_{baseline,guided}/seed_*/medium/*optimization.log` 的 `diversity` 欄位。*

  §3.2b 記錄 capped **large** run 的 crossover 在**第 6 代**。在 **medium** 上兩種變體都更晚：
  capped medium 6–10（中位數 8），native medium 8–9（中位數 9）。

  **機制。** Diversity 是 30 個 gene 上的平均 pairwise Hamming mismatch
  （`core/population.py:194–205`）。在 native 之下，第 1–8 代仍在跑 law-1 的母體 11,405→597，
  即遠多於 mating operator 所調校的 512 個個體；較大的母體每代流失 Hamming diversity 的速度較慢，
  因為 `ratio=0.5, elitism=0.05` 的 tournament selection 移除的是固定的*比例*，而較大 pool 的存活集合
  保留更多相異 allele。所以 **law 1 延後了 law 2 能夠介入的時點** —— 這恰恰是 §3.2b 的預測，而它成立。
  一旦介入，law 2 就具黏著性，母體到第 29 代降至 256–258。
- **兩臂的對稱性。** 在 5 個 seed 中有 4 個，兩臂的 crossover 代數相同或相差一代；而在 gen-1 log 行仍
  存在的那四個 seed 上，gen-1 diversity 差異是固定的 +0.007，有利於 guided 臂（seed 24005 arm G 的 log
  從第 2 代開始 —— §2.2）。因此 decay 行為是**協定層級的共有性質，而非臂層級的 confounder**
  （與 §3.2b 對 large 的結論相同）。
- 實際消耗的總評估預算：native G 中位數 **32,211** 次完整 eval（範圍
  31,284–32,435），native F 中位數 **31,547**（30,876–32,444），相對於 capped G 中位數 **10,011** 與
  capped F 中位數 **10,473**。native 每臂多跑了 **≈3.2×** 的評估數。
  *來源：各 `trajectory.jsonl` 的最後一筆紀錄，欄位 `cumulative_complete_evals`。*
- 每個 seed-臂的 GPU 評估時間：native **0.99–1.11 h**，capped **0.16–0.21 h**
  （`generation_evaluate_seconds` 之和）。這只是 GPU 時間，不含 §12.6 所記錄的約 2.9 h 單執行緒
  `space.sample(11405)` 成本。

---

## 2. 偏離 —— 屬於已記錄項，非新發現

兩項在本分析開始前就已知且在預期之內。此處列出僅為存證，且**不**被視為異常。

### 2.1 7× remeasure 透過 `--gpu-uuid-override` 在 GPU 5 上執行

`large` 佔用了 Lock-A 的卡（2、3、4、6、7），因此五個 native-medium remeasure 全部在唯一空閒的卡
GPU 5 上執行。artifact 自身即記錄了這一點：

| 欄位 | 值（全部 5 個 seed） |
|---|---|
| `expected_gpu_system_index` | `5` |
| `verified_gpu_uuid` / `gpu_uuid_override` | `GPU-4c517496fc501205` |
| `lock_a_search_card_uuid` | 各 seed 的搜尋卡（例如 24001 → `GPU-8cdaa86f8629c93a`） |
| `run_card_differs_from_search_card` | `true` |
| `same_gpu` / `same_process` | `true` / `true` |
| `start_arm` | `G`（per-shape counterbalance `START_ARM[medium] = G`） |
| `repeats_per_arm` / `single_measurements` | `7` / `14` |

*來源：`stage5_native_baseline/seed_*/medium/champion_interleaved.json → measurement_metadata`。*

理由與 capped medium remeasure 相同（index §8.3、`medium_remeasure_deviation.md`）：預先登錄的要求是
G 與 F 必須**在同一個 process、同一張卡、同一個時間窗內** interleave，而這一點被保留了；判準是
**pair 內部的比值**，因此卡層級的吞吐量偏移對兩臂是共通的、會相消。絕對的 GFLOP/s 跨卡不可比；
`F/G` 則可比。
請注意這使得 native 與 capped 的 medium remeasure 具有*完全相同*的偏離（都在 GPU 5 上），
對 Q2 的 cross-P0 比較而言反而是較有利的情況。

### 2.2 Seed 24005 arm G 被 resume 了 3 次；其較早的 degradation marker 是已知的 false positive

- `resume_record.json` 顯示在 Lock-A 卡 `GPU-74a77207e38908fb`（hip 6）上有三個 session：
  session 0 為 07:37:56Z 之前的全新起跑，session 1 與 2 帶有 `resume_from_generation = 1`。
  *來源：`stage5_native_baseline/seed_24005/medium/resume_record.json`。*
- engine 在 `--resume` 時會覆寫其固定路徑的 log，因此存活下來的 GA log 只涵蓋**第 2–25 代**，
  而 trajectory 則是**完整的 1–25**。remeasure 腳本偵測到並記錄了這件事：

  ```
  RESUMED_RUN_PARTIAL_LOG {"arm": "G", "log_generations": 24, "log_starts_at": 2,
   "trajectory_generations": 25, "note": "engine rewrote its fixed-path log on --resume;
   trajectory is complete and was cross-checked on the overlap"}
  ```

  *來源：`stage5_native_remeasure_control/seed_24005/medium.remeasure.log:35`。*

  該檢查**並未被弱化**：腳本會斷言 trajectory 是完整的 `1..N`、log 的世代恰為其*後綴*，並就 log 所
  涵蓋的每一代，以 `cumulative_complete_evals` **逐元素**交叉核對 `n_evals`，任何不符即中止
  （`scripts/remeasure_interleaved_champion.py:426–455`）。Seed 24005 arm G 通過。
- 在 2026-08-12T07:37Z 一次刻意的 kill/resume 測試期間寫入此 seed 的 `native_gen0_degraded.json`，
  是**一個已修復之 guard 缺陷所產生的 FALSE POSITIVE**，已 quarantine 於
  `quarantine/native_gen0_guard_false_positive_20260812/`，並附四條獨立證據線：
  (1) `observed_gen0 = 5958 = int(512 + (11405−512)/2)`，是 law-1 的 **decay** 值，而非 fail-open 值
  `11405 // 2 = 5702`；(2) log 中有零行 `Max iterations reached`，故 `ga.py:289–293` 從未執行；
  (3) `trajectory.jsonl` 第 1 代有 `generation_candidate_count = 11405`，其中 11,284 有效；
  (4) 該 marker 自相矛盾（`halved_target 5702` vs `observed_gen0 5958`）。
  **它並未被回報為 §12.7 的 stock-Ductile fail-open 觀察。** 沒有任何科學資料遺失。

---

## 3. 結果 —— native-Gen0 medium，最終 champion，7× interleaved remeasure

各臂最終 champion 的 7× 中位數 real-GFLOP/s，以及 F-vs-G 對比。格式對齊 index §7.1/§7.2；
分析量為 `ln(F/G)`（§5b）。

| seed | G 中位數（GFLOP/s） | F 中位數（GFLOP/s） | **F/G ratio** | **% 變化** | log-ratio `ln(F/G)` |
|---|---:|---:|---:|---:|---:|
| 24001 | 13,980.8 | 6,802.0 | 0.4865 | −51.3 % | −0.7205 |
| 24002 | 6,187.4 | 14,022.7 | 2.2663 | +126.6 % | +0.8182 |
| 24003 | 13,607.9 | 5,082.6 | 0.3735 | −62.6 % | −0.9848 |
| 24004 | 11,531.8 | 13,136.2 | 1.1391 | +13.9 % | +0.1303 |
| 24005 | 7,516.3 | 14,826.2 | 1.9725 | +97.3 % | +0.6793 |
| **中位數** | 11,531.8 | 13,136.2 | **1.1391** | **+13.9 %** | **+0.1303** |
| ⚠ *（原始比值的算術平均 —— **具誤導性**，見 §5b）* | *10,564.8* | *10,773.9* | *1.2476* | *+24.8 %* | *（mean log −0.0155 ⇒ **幾何平均 0.9846，−1.5 %**）* |

*來源：`stage5_native_baseline/seed_{24001..24005}/medium/champion_interleaved.json`
（`median_gflops.G`、`median_gflops.F`、`F_over_G_median_ratio`、`F_over_G_median_log_ratio`），
以與 `gap_large.py` / `gap_medium.py` 相同的邏輯計算。*

⚠ **「原始比值算術平均」那一列已被標記，不得被引用為效應量。** 它讀起來是 +24.8 %，而幾何平均 ——
正確的乘法型集中趨勢 —— 是 **−1.5 %**。這是 §5b 所述偏誤的更尖銳版本，比 capped 表格（+5.0 % vs
−10.7 %）更甚，因為 native 有兩個比值高於 1.97。

門檻（兩者皆取自 `trajectory_metadata.json`，與 capped 實驗相同未變）：
`η_medium = 0.0041953` ⇒ 非退步下限 `F/G ≥ 0.995813`；`δ_medium = 0.0042042` ⇒ 改善門檻
`F/G > 1.004204`。

### 3.1 預先登錄的方向一致性成分（每項要求 ≥4/5 為正）

| 成分 | native P0 = 11,405 | capped P0 = 512（此處重算） | 判定（native） |
|---|---:|---:|---|
| Gen0 best（`best_gflops_so_far`，gen-1 紀錄） | **2/5** | 3/5 | fail |
| gen-10 best | **1/5** | 3/5 | fail |
| AUC（best-so-far 對共同累積 eval 預算） | **3/5** | 3/5 | fail |
| 最終 champion（7× 中位數） | **3/5** | 2/5 | fail |
| 最終**非退步** `F ≥ G·e^{−η_s}` | **3/5** | 3/5 | fail |
| 最終**改善** `F > G·(1+δ_s)` | **3/5** | 2/5 | fail |
| Gen0 **中心**（`generation_Q_median_any_valid`） | **5/5** | 3/5 | —（診斷用，非 gate） |

*來源：Gen0/gen-10/AUC 取自 `stage5_native_{baseline,guided}/seed_*/medium/trajectory.jsonl`；
最終各列取自 `stage5_native_baseline/seed_*/medium/champion_interleaved.json`。AUC 以 step-hold 對
`cumulative_complete_evals` 積分至兩臂總量的 `min`，即完全依照 `analyze_large.py` 的程序。capped 欄位
以相同的 code path 由 `stage3_{baseline,guided}/seed_*/medium/…` 重算。*

**沒有任何成分達到 ≥4/5 的 gate。** 在 capped large 上以 5/5 通過的非退步項，在此只有 3/5 ——
因為在 medium 上 `η = 0.42 %` 是遠比 large 的 12.28 % 更緊的下限，且有兩個 seed 退步超過 50 %。

### 3.2 ⚠ 根本原因：在 **medium** 上，per-seed 的 F/G 是量測模式的樂透，而非 champion 的差異

這是整份分析最主要的發現，並支配 §3 與 §4 可以被如何解讀。

**證據。** 7× interleaved remeasure 會寫下每一次個別量測。對 medium 而言，對同一個*固定 champion
config* 在單一 process、單一張卡、**27 秒**的時間窗內所做的七次重播，呈現**雙峰、2–6× 的散布**：

| | native G（min / median / max，max÷min） | native F | capped G | capped F |
|---|---|---|---|---|
| 24001 | 6,107 / **13,981** / 14,194 — 2.32× | 3,609 / **6,802** / 14,165 — 3.93× | 3,771 / 13,495 / 13,598 — 3.61× | 2,234 / 13,456 / 13,547 — 6.06× |
| 24002 | 4,630 / **6,187** / 13,959 — 3.01× | 4,482 / **14,023** / 14,079 — 3.14× | 5,255 / 12,350 / 12,420 — 2.36× | 5,852 / 8,711 / 12,784 — 2.18× |
| 24003 | 6,986 / **13,608** / 13,784 — 1.97× | 3,516 / **5,083** / 14,013 — 3.99× | 4,712 / 6,137 / 15,067 — 3.20× | 4,478 / 6,595 / 14,800 — 3.31× |
| 24004 | 4,490 / **11,532** / 14,945 — 3.33× | 6,394 / **13,136** / 13,286 — 2.08× | 4,988 / 6,283 / 12,504 — 2.51× | 3,925 / 13,304 / 13,400 — 3.41× |
| 24005 | 3,755 / **7,516** / 13,927 — 3.71× | 9,182 / **14,826** / 14,869 — 1.62× | 3,808 / 13,192 / 13,539 — 3.56× | 2,166 / 4,685 / 10,535 — 4.86× |

*來源：`stage5_native_baseline/seed_*/medium/champion_interleaved_raw.jsonl` 與
`stage3_baseline/seed_*/medium/champion_interleaved_raw.jsonl`（各 14 筆紀錄：`arm`、`gflops`、
`repeat`、`position_in_repeat`、`timestamp`）。*

- 在全部 70 個 native-medium remeasure 點上，經驗 `P95(|log y − median log y|)` = **0.828**；在全部
  70 個 capped-medium 點上為 **1.196**。預先登錄的 `η_medium = 0.0041953`。因此 medium 實現的
  重複性**比 gate 所依據的 η 差約 200–285×。**
- 這是 **medium 特有的。** 同一統計量在 capped **large** 的 remeasure 上，全部十個臂-seed 的 max÷min
  為 **1.024–1.053**；在 **tiny** 上，9/10 為 **1.002–1.036**（有一個 12.7× 的離群值）。
  *來源：`stage3_baseline/seed_*/{large,tiny}/champion_interleaved_raw.jsonl`。*
- 這**不是**順序、warm-up 或熱效應的產物：在 seed 24002 arm G 內，模式在第 1–7 次 repeat 之間翻轉為
  `low, low, low, high, high, low, low`，各次間隔約 2 秒，全都在
  `position_in_repeat = 1`，而整個 14 次量測的時間窗跨度為 27 秒。

**這一路串起來的機制。**

1. medium 的每次 launch 吞吐量在大約 **{~5,000, ~14,000} GFLOP/s** 之間呈雙穩態，兩者機率各約 0.5。
2. GA 對每個候選只評分**一次**。它的 champion 是 10 k（capped）到 32 k（native）次單發量測的 `max`，
   所以該 champion *幾乎必然*是一個剛好抽中高模式的 config。佐證：搜尋期最終的 `best_gflops_so_far`
   在兩個 P0 水準與兩臂的**全部 20 個**臂-seed 上都落在 **12,545–15,407** —— 在 3× 的底層散布下這是一個
   不合理地緊密的區間，正是「對雙峰噪音分布取 `max`」的簽名。
   *來源：各 `trajectory.jsonl` 的最後一筆紀錄。*
3. 7× remeasure **重新擲骰**。7 次的中位數落在高模式，當且僅當 7 次抽樣中有 ≥4 次落在高模式，
   對公平硬幣而言這恰為 p = 0.5。觀測到的 7 次中高模式（>10,000 GFLOP/s）計數：

   | | 24001 | 24002 | 24003 | 24004 | 24005 |
   |---|---|---|---|---|---|
   | native G / F | 4 / 3 | 2 / 4 | 5 / 2 | 5 / 5 | 3 / 6 |
   | capped G / F | 6 / 6 | 5 / 3 | 3 / 3 | 2 / 5 | 4 / 1 |

   在 **10/10** 個臂-seed 中，回報的中位數為高值當且僅當計數 ≥4 —— 也就是說，回報的數字純粹是一個
   模式選擇器。
4. 因此 `F/G` 依構造只會取三個值之一：≈1（兩臂落在同一模式）、≈14,000/6,000 ≈ **2.3**（F 高、G 低），
   或 ≈ **0.43**（F 低、G 高）。觀測到的 native 比值為
   **0.4865、2.2663、0.3735、1.1391、1.9725**，capped 的則為 **0.9971、0.7053、1.0746、2.1175、
   0.3551** —— 這十個之中每一個都落入上述三個預測群集之一。
5. 搜尋期 champion 分數對 7× remeasure 中位數的比值：在 20 個臂-seed 上為 0.35–0.99，其中
   **10/20 低於 0.8** —— G 中 5 個、F 中 5 個、native 5 個、capped 5 個。這個失效是**臂對稱且
   P0 對稱的**，所以它不會讓 `F/G` 朝某個方向偏；它摧毀的是其**精確度**。

**這意味著什麼。** medium 的最終 champion `F/G` 是一個 Bernoulli(½)/Bernoulli(½) 的商。它在 5 個 seed
上的中位數是擲硬幣；**3/5 為正恰好就是機遇期望值。** 方向一致性 gate 在 medium 上、在任一 P0 水準下，
基本上**沒有統計檢定力**。

**競爭性解釋，以及如何區分它們。** 雙穩態的候選物理成因：
(a) 每次 launch 的 clock/DPM 狀態 —— medium kernel 在高模式下約 10 µs，而空檔約 2 秒，因此
GPU 可能尚未 boost；(b) MI300 上 XCD/CU 分區配置逐次 launch 變動；
(c) 在 `DUCTILE_PERSIZE_RBS = 4096 MB` 輪替 buffer 之下，約 2.3 MB 工作集的 MALL/L2 駐留情形；
(d) champion kernel 中的 `GlobalSplitU`-workspace 或 atomics 競爭（medium 的 champion 使用
`GSU = 4`）。**(a) 目前仍無法與 (c) 區分**；並請注意 (c) 本身並不明顯地解釋為何 tiny —— 同樣是
4,096 MB RBS —— 卻很緊密。具決定性的量測（此處一項都未執行）為：以 `rocm-smi` 逐次量測記錄 SCLK；
把計時區間拉長到 ≥100 ms 使任何 ramp 被攤平；掃描 `DUCTILE_PERSIZE_RBS`；以及釘住 CU/XCD 分區。
**`NOT_EVALUATED`。**

**另請注意這對 capped 紀錄的誠實後果。** Index §7.1 對 capped medium 的散布陳述為：
*"these are genuine champion differences, not measurement noise"*。上方 capped remeasure 的原始點
（同一個 config，seed 24001 arm G/F，2,234–13,598 GFLOP/s）**與該句相矛盾**。此事已於 §9 標記給
main session；本分析不編輯 index。

---

## 4. Q1 —— 穩健性：capped-medium 的方向在 native Gen0 下是否成立？

**Capped 參考（index §7.1）：** per-seed F/G 為 0.9971 / 0.7053 / 1.0746 / 2.1175 / 0.3551；中位數
**0.9971**（−0.3 %）；2/5 為正；幾何平均 0.893。
**Native（本分析）：** 0.4865 / 2.2663 / 0.3735 / 1.1391 / 1.9725；中位數 **1.1391**（+13.9 %）；
3/5 為正；幾何平均 **0.9846**。

**答案，two-sided。**

- 就**中位數**而言，符號翻轉：−0.3 % → +13.9 %。就**幾何平均**（§5b 的分析量）而言，兩者都很小且介於
  負值到中性之間：−10.7 % → −1.5 %。就**方向一致性**而言，2/5 → 3/5 —— 兩者都未達 ≥4/5 的 gate，
  且兩者都無法與擲硬幣區分。
- **兩個 P0 水準之間的 per-seed 一致性為零。** 五對 `ln(F/G)` 值在 capped 與 native 之間的 Pearson
  相關為 **r = −0.458**。若 per-seed 的 F/G 反映的是 treatment 的某種穩定 seed 層級性質，r 應強烈為正。
  它並非如此。
- **誠實的解讀是：兩種變體在 medium 上都沒有產生可解析的方向**，而 §3.2 解釋了原因：在兩個 P0 水準下，
  per-seed 的數字都是一場模式樂透，其 ±100 % 量級的散亂淹沒了任何合理的 treatment 效應。促成 §12.2
  「medium 是唯一具有可解析 effect size 的 shape」的那個 capped-medium 主張，是建立在把該散亂與
  `η_medium = 0.42 %` 相比之上，而原始 remeasure 點顯示，對這些 champion 而言 `η_medium` 並不是正確的
  量尺。
- **判定：** capped-medium 的*方向*在 native Gen0 下**既未獲確認，也未被推翻** ——
  在最終 champion 指標上，於可用精確度下為 `NOT_EVALUATED`。*確實*被建立的是：native 的 run 在內部
  是乾淨的（§1），所以這個不確定性是 medium **量測**的性質，而非 native 執行的性質。

**允許的 claim 措辭**（依 §3.4c.4、§12.5、charter §8.2/§8.5/§8.6）：*"On medium, at native Gen0
(11,405) as at P0-capped 512, the amended sparse prior — applied at ρ = 0.566 (≈71 % strength) on
`DepthU` and ρ = 0.80 (100 %) on `1LDSBuffer`, i.e. over 2 of 29 free genes — did not meet the
pre-registered ≥4/5 directional gate on any component. The per-seed contrast is dominated by a bimodal
measurement mode on this shape, so the result does not resolve the sign."* **不允許：** 任何聲稱
模型的 guidance 沒有幫助的陳述。

### 4.1 值得記錄的次要根本原因：prior 指向的方向偏離了勝出的 `DepthU`

兩個 activated gene 的 champion 值：

| | 24001 | 24002 | 24003 | 24004 | 24005 |
|---|---|---|---|---|---|
| native G（`DepthU`, `1LDSBuffer`） | 128, 1 | 128, 1 | 64, 1 | 128, 1 | 64, 1 |
| native F | 128, 1 | 64, 1 | 128, 1 | 64, 1 | 128, 0 |
| capped G | 64, 0 | 128, 1 | 128, 0 | 64, 0 | 128, 0 |
| capped F | 64, 0 | 64, 1 | 128, 0 | 128, 0 | 64, 1 |

*來源：`stage5_native_{baseline,guided}/seed_*/medium/optimization_result.json → best_individuals[0]`；
`stage3_*` 亦同。*

- 在全部 20 個 medium champion 中，`DepthU ∈ {64, 128}`：**11× 128、9× 64、0× 32、
  0× {256, 512, 1024}**。
- 出貨的 prior 給 `DepthU = 128` 的抽中機率是 **0.0723** —— 相對於 uniform（0.1667）是
  **2.3× 的降權** —— 同時給 `DepthU = 32` **0.2096**，而該值贏了 **0/20** 次。
- 單看 **prior-free 的 baseline 臂**（對這個 shape 上實際會贏什麼的無偏讀數），native G 的 champion 是
  `128, 128, 64, 128, 64`，且 `1LDSBuffer = 1` 在 **5/5** 上成立；而 prior 只給
  `1LDSBuffer = 1` **0.331**，給 `0` 則是 **0.669**。
- **所以在 native medium 上，prior 在兩個 activated gene 上都指向偏離眾數勝出值的方向。**
  這不是 pipeline 的缺陷；它是 §3.4a.2 的預期後果 —— `DepthU` 的「trusted」集合是 `{32, 64}`，
  所以模型全部的偏好質量都被鋪在兩個值上，其中一個從未贏過，而最常贏的那個值則被 entropy floor
  壓在殘餘的 `(1−ρ)·p0` 份額上。這正是 §3.4c.4 所警示、會限縮 medium null 之詮釋的機制。
- **所需的區辨性證據：** `DepthU = 128` 究竟是真的更好，還是只是更可能抽中高量測模式。鑑於 §3.2，
  從這些 artifact 無法把兩者分開。`NOT_EVALUATED`。

---

## 5. Q2 —— 稀釋：P0 = 512 與 P0 = 11,405 下的效應量

### 5.1 跨 P0 水準什麼可比、什麼不可比（§12.5）

- **可比：** P0 內部的配對對比 `ln(F/G)`。在每個變體內部，兩臂共用相同的 Gen0 尺寸、相同的 `group_0`
  weights、相同的 seed 與相同的 eval 預算，所以該對比在每個水準上都是無偏的，兩個對比可以並列。
- **之所以可比，僅因為現在兩邊都採用相同的 7× 協定（§12.3）。** native 每臂多跑約 3.2× 的評估
  （中位數 32,211 vs 10,011 次完整 eval），所以其搜尋期 champion 帶有更大的 winner's-curse 偏誤。
  若 native 是從 GA log 讀出、而 capped 是從 7× remeasure 讀出，Q2 的比較就會把真實的 effect-size 變化
  與量測協定的變化混為一談，且方向會膨脹 native。兩邊都經過 7× remeasure，在同一張卡（GPU 5）上，
  採同一個 `START_ARM = G` counterbalance。這才是讓此比較具有任何意義的原因。
- **不可比：** 跨 P0 水準的 champion 絕對品質（預算不同），以及 —— 因為 §3.2 —— 在任一水準上從 medium
  的最終 champion `F/G` 讀出的任何*量值*。

### 5.2 數字

| 統計量 | P0 = 512（capped） | P0 = 11,405（native） | 變化 |
|---|---:|---:|---|
| `F/G` 中位數 | 0.9971 | 1.1391 | +14.2 pp |
| `ln(F/G)` 中位數 | −0.0029 | +0.1303 | — |
| `ln(F/G)` 平均（⇒ 幾何平均） | −0.1130 (0.893) | −0.0155 (0.9846) | 趨向 0 |
| 為正的 seed 數 | 2/5 | 3/5 | +1 |
| **`\|ln(F/G)\|` 平均（離散度）** | **0.4419** | **0.6666** | **+51 %** |
| `ln(F/G)` 的母體標準差 | 0.583 | 0.726 | +25 % |
| 跨 P0 的 per-seed 相關 | — | — | **r = −0.458** |

*來源：`stage3_baseline/seed_*/medium/champion_interleaved.json`（capped）與
`stage5_native_baseline/seed_*/medium/champion_interleaved.json`（native）。*

### 5.3 答案

- **在最終 champion 指標上，Q2 於可用精確度下為 `NOT_EVALUATED`。** 集中趨勢朝零移動
  （幾何平均 −10.7 % → −1.5 %），而*離散度卻增加了 51 %*。這是熵更高的樂透的簽名，而不是某個
  treatment 效應變小或變大的簽名。§3.2 說明了原因：在兩個水準上，該估計量都是擲硬幣的比值。
  預先登錄的 §12.4.2 稀釋讀法（*"native significantly smaller ⇒ guidance value concentrates at small
  Gen0"* vs *"native maintained ⇒ stronger evidence"*）**無法**由這個指標裁決。
- **在唯一存活於此量測病理之外的指標上 —— Gen0 中心 —— 沒有稀釋；若有什麼，也是相反方向。**
  `generation_Q_median_any_valid` 是在 11,285–11,305 個有效候選（native）或 502–509 個（capped）上的
  中位數，所以它是對模式樂透取平均，而不是穿過它取最大值：

  | | 中心 `F/G` 中位數 | 為正的 seed 數 | `ln` 平均（⇒ 幾何平均） | per-seed 範圍 |
  |---|---:|---:|---:|---|
  | P0 = 512 | 1.0251 (+2.5 %) | 3/5 | +0.0197 (+2.0 %) | 0.9873 – 1.0495 |
  | P0 = 11,405 | **1.0331 (+3.3 %)** | **5/5** | **+0.0330 (+3.4 %)** | 1.0172 – 1.0529 |

  guided 的 Gen0 中心優勢**維持並略微擴大**（在 log 尺度上 +2.0 % → +3.4 %），且變成
  **跨 seed 一致**（3/5 → 5/5）。**機制：** prior 是逐次抽樣套用的，所以期望的中心位移與 pool 大小無關；
  隨著抽樣數多 22× 而改變的是實現中心的*抽樣誤差*，它縮小約 √22 ≈ 4.7×。一致性的銳化與 per-seed 範圍
  約 4.7× 的收窄，兩者都正是該預測（見 §7）。這是一個**管路層級的確認**：treatment 在 native 規模下
  被未經稀釋地遞送 —— §12.4.3。
- **誠實的界線。** 「Gen0 中心效應沒有稀釋」*不等於*「guidance 對搜尋的價值沒有稀釋」。§7.2.1 的整個
  重點就是 GA 並不消費那個中心。Q2 能說的是：*prior 對它直接控制的那個量的掌握，在 22× Gen0 下不會
  減弱；至於那是否轉化為搜尋價值，則由 Q3 以及 §3.2 對最終指標的判定來回答。*

---

## 6. Q3 —— 極值機制：三項預先登錄的預測

§12.4.4 / index §3.3 在執行**之前**就固定了三項可證偽的預測。此處完全按其原文評估；沒有任何一項被改寫。

### 6.1 資料

Gen0 = `trajectory.jsonl` 的第 1 代紀錄，也就是兩臂依構造唯一有差異的那一代。中心 =
`generation_Q_median_any_valid`；極值 = `best_gflops_so_far`；有效性 = `generation_any_valid_count`。

**Native，P0 = 11,405：**

| seed | centre G | centre F | **centre F/G** | extreme G | extreme F | **extreme F/G** | valid G | valid F |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 24001 | 1.3567 | 1.4053 | **1.0358** | 10,904.9 | 11,766.3 | **1.0790** | 11,285 / 11,405 | 11,289 / 11,405 |
| 24002 | 1.3570 | 1.3803 | **1.0172** | 10,996.9 | 11,386.1 | **1.0354** | 11,293 | 11,294 |
| 24003 | 1.3335 | 1.4040 | **1.0529** | 12,086.8 | 11,904.6 | 0.9849 | 11,300 | 11,304 |
| 24004 | 1.3622 | 1.4016 | **1.0289** | 11,415.7 | 11,289.9 | 0.9890 | 11,283 | 11,261 |
| 24005 | 1.3543 | 1.3992 | **1.0331** | 11,622.9 | 11,538.4 | 0.9927 | 11,284 | 11,305 |
| **中位數** | — | — | **1.0331** | — | — | **0.9927** | — | — |
| **F > G 的 seed 數** | — | — | **5/5** | — | — | **2/5** | — | — |
| **mean ln（幾何平均）** | — | — | +0.0330 (**+3.4 %**) | — | — | +0.0154 (**+1.5 %**) | — | — |

**Capped，P0 = 512（此處以相同 code path 重算，供配對比較）：**

| seed | centre F/G | extreme F/G | valid G / F（共 512） |
|---|---:|---:|---|
| 24001 | 1.0435 | 1.0600 | 508 / 502 |
| 24002 | 0.9873 | 1.0007 | 505 / 509 |
| 24003 | 0.9958 | 0.9551 | 507 / 507 |
| 24004 | 1.0251 | 0.8747 | 508 / 509 |
| 24005 | 1.0495 | 1.0073 | 507 / 507 |
| **中位數** | **1.0251** | **1.0007** | — |
| **F > G 的 seed 數** | **3/5** | **3/5** | — |
| **mean ln（幾何平均）** | +0.0197 (+2.0 %) | **−0.0227 (−2.2 %)** | — |

*來源：`stage5_native_{baseline,guided}/seed_*/medium/trajectory.jsonl` 與
`stage3_{baseline,guided}/seed_*/medium/trajectory.jsonl` 的第 1 代紀錄。*

### 6.2 預測 (i) —— 「guided 的 Gen0 **極值**劣勢應在 11,405 下**擴大**」

## ⚠ **在 medium 上被 REFUTED。**

- 就 §5b 的分析量而言，guided 的極值赤字**收窄並翻轉符號**：`ln(extreme F/G)` 的平均從 512 下的
  **−0.0227（−2.2 %）** 變為 11,405 下的 **+0.0154（+1.5 %）**。
- `ln(extreme F/G)` 逐 seed 配對變化，capped → native：**+0.0177、+0.0341、+0.0307、+0.1228、
  −0.0146**。**5 個 seed 中有 4 個朝著 guided 極值劣勢*較小*的方向移動**，中位變化為
  **+0.0307**。
- 只有兩個較弱的統計量朝預測方向移動，且幅度都小於散亂：極值比值的中位數 1.0007 → 0.9927
  （−0.8 pp），以及為正的 seed 數 3/5 → 2/5。兩者都不是預先登錄的分析量，而在 n = 5 之下，
  3/5→2/5 的變化是噪音。
- **此處記錄為該機制之預測 (i) 在 medium 上被推翻。它未被事後改寫、軟化或重新推導。**

**可能成因 —— 預測為何失敗，以及什麼能區辨它。** 該預測假設 Gen0 最大值是由*候選品質分布的散布*所
支配，因此集中機率質量會壓縮上尾，而 22× 更多的抽樣會讓這個壓縮咬得更深。native 資料在 medium 上
以三個具體方式與此不一致：

1. **Gen0 極值受限於量測模式，而非候選分布。** native Gen0 的 best 為 **10,905–12,087**（G）與
   **11,290–11,766**（F）—— 十次 run 跨度僅 ±5 % 的區帶，恰好坐落在 §3.2 所辨識的約 14,000 高模式
   天花板之下。對雙峰噪音分布做 11,285 次抽樣取最大值，會在*兩臂*都逼近該天花板。因此極值比值被 pool
   大小推向 1，這與預測 (i) 相反，且是 §3.2 病理的直接後果。佐證：極值比值的**散布收縮**了，從
   0.875–1.060（capped）到 0.985–1.079（native）—— 估計量精確得多，而其中心卻*上移*。
2. **guided 臂從更大的 pool 中獲益更多，而非更少。** Gen0 best 的中位數在 G 中從 10,288 →
   11,416（**+11.0 %**），在 F 中從 10,096 → 11,538（**+14.3 %**）。若上尾被壓縮，應該預測 guided 臂
   從額外抽樣中獲益*較少*。它獲益更多。
3. **實現出的 guided Gen0 *更*多樣，而非更少 —— 在兩個 P0 水準上皆然。** 第 1 代的 Hamming
   diversity（`core/population.py:194`）在全部五個 native seed 上為 **G 0.568、F 0.575**
   （capped：G 0.567–0.570、F 0.573–0.576）—— guided 臂在**可得的 9/9 對上都高出 +0.007**
   （seed 24005 native G 沒有 gen-1 log 行，§2.2）。而由出貨 weights 計算出的
   prior *名目*效應方向相反、大小幾乎相同：`Δ = [(1 − Σq²_DepthU) − 5/6] + [(1 − Σq²_1LDS) − 1/2] =
   (0.6840 − 0.8333) + (0.4428 − 0.5000) = −0.2065`，即 30 個 gene 的平均上 **−0.0069**。所以該機制
   「集中質量會縮小 Gen0 多樣性」的前提，在這個 shape 上**於實現出的母體中並不成立**。

   **為何實現出的多樣性不遵循名目 prior：** sampler 只接受相異且符合約束可行的個體。從所設定的
   per-gene 分布做獨立、未過濾抽樣，預測第 1 代 diversity 的基準值為 **0.6306**
   （29 個非 `group_0` gene 的 `1 − 1/k` 之和 = 17.9171，加上 `group_0` 的 `1 − Σp² = 0.99982`，
   ÷ 30）；觀測值為 **0.568**。因此實現出的 Gen0 在兩臂中都實質上*比*任何 per-gene prior 所要求的
   更集中 —— 主導 Gen0 組成的是可行性過濾，而不是 treatment。對 +0.007 這個符號翻轉，一個合理的
   讀法是：把 `DepthU`/`1LDSBuffer` 導向可行的設定會**紓解**其他 28 個 gene 上的聯合約束，因此它們
   實現出的邊際分布更接近 uniform，總量的上升超過了直接的集中成本。**這是一個假說，不是結果。**
   能夠定案的量測是 engine 自己的 `per_gene_diversity`（僅在有 observer 附掛時才於 `ga.py:674–682`
   輸出 —— 當時沒有附掛），或是 Gen0 母體的 dump。**`NOT_EVALUATED`。**

**對此項推翻的 two-sided 但書。** 推翻 (i) *在 medium 上*並**不**推翻 §7.2.1 機制的一般性。§7.2.1 是在
**large** 上推導的，其 Gen0 remeasure 噪音很小（max÷min 1.02–1.05），且其 treatment 涵蓋 5 個 gene。
medium 的雙峰量測很可能完全遮蔽任何尾部效應。(i) 的乾淨檢定是 native **large** 的 run。

### 6.3 預測 (ii) —— 「guided 的 Gen0 **中心**優勢應維持或擴大」

## **SUPPORTED。**

中心 `F/G` 中位數 1.0251 → **1.0331**；`ln` 平均 +0.0197 → **+0.0330**；為正的 seed 數 3/5 → **5/5**；
per-seed 範圍從 0.9873–1.0495 收窄至 1.0172–1.0529。每一個 native seed 都為正。

**可能成因。** 恰為所述的理由：prior 未變，所以*期望*的中心位移是與 pool 大小無關的逐次抽樣性質；
只有估計量的變異數會改變，而它以 `1/√n` 縮小，`√22 ≈ 4.7×`。觀測到的範圍寬度 0.062 → 0.036 是
1.7× 的收窄 —— 方向相同，但小於 4.7×，因為殘餘散亂還包含到達的可行區域在 seed 之間的真實差異，
而不只是多項式誤差。**區辨性證據：** 若殘餘純為多項式誤差，native 的範圍應約為 0.013；超出的部分
（0.036）就是 seed 層級的成分。這與該讀法一致，但並未證明它。

### 6.4 預測 (iii) —— 「擴大幅度在 **large** 上應大於 **medium**」

## `NOT_EVALUATED`.

在本分析進行時，native **large** 仍在 GPU 2/4/6/7 上執行，不在此處的範圍內（本 agent 為唯讀，
且未觸碰它）。跨 shape 梯度只存在 medium 這一半。現在能說的是：**該預測梯度的 medium 這一側完全
沒有出現擴大 —— 它出現的是收窄與符號翻轉（§6.2）**，因此若 large 確實顯示擴大，梯度的排序會成立，
而 (i) 在 medium 上仍屬被推翻；若 large 也收窄，(i) 就是徹底被推翻。

### 6.5 已排除的有效率產物

native 每 11,405 個中的有效候選：**G 11,283–11,300（98.93–99.08 %）**、**F 11,261–11,305
（98.74–99.12 %）**。Capped：G 505–508 / 512、F 502–509 / 512。兩臂在兩個 P0 水準上產生的可執行 config
數在統計上無法區分，所以 **Gen0 結果沒有任何部分是「guidance 產生了更多不可建構的 kernel」**
—— 與 §7.2.1 在 large 上得到的結論相同。

---

## 7. 額外角度 —— 在 22× 的抽樣數下，實現出的 Gen0 分布是否更接近所意圖的 `p1`？

**直接的 per-value 頻率檢查：`NOT_EVALUATED`，並附理由。** Gen0 中實現出的 `DepthU` /
`1LDSBuffer` 值計數**無法從任何 artifact 還原**。`distinct_hashes.jsonl` 只存 hash；
`optimization_result.json` 存的是 champion；`step-00__ductile.checkpoint` 是*最後*一代的狀態
（`gen = 30`），不是 Gen0；engine 的 per-gene 統計只在有 observer 附掛時才輸出（`ga.py:674–682`），
而當時沒有。重算實現出的計數需要重跑 `space.sample(11405)`，那是每臂約 2.9 h 的單執行緒 CPU 工作
（§12.6），且會與進行中的 `large` run 競爭資源 —— 超出唯讀分析的範圍。

**什麼*是*可量測的，而且它回答了底層問題。** 第 1 代的整體 Hamming diversity 是實現出的 per-gene
頻率的精確函數，而且每次 run 都有記錄：

| | seed 24001 | 24002 | 24003 | 24004 | 24005 | 全距 |
|---|---:|---:|---:|---:|---:|---:|
| **native G**（n = 11,405） | 0.568 | 0.568 | 0.568 | 0.568 | n/a¹ | **0.000** |
| **native F**（n = 11,405） | 0.575 | 0.575 | 0.575 | 0.575 | 0.575 | **0.000** |
| capped G（n = 512） | 0.568 | 0.567 | 0.570 | 0.567 | 0.569 | 0.003 |
| capped F（n = 512） | 0.574 | 0.575 | 0.573 | 0.576 | 0.573 | 0.003 |

*來源：`stage5_native_{baseline,guided}/seed_*/medium/*optimization.log` 與
`stage3_{baseline,guided}/seed_*/medium/*optimization.log` 的 `diversity` 欄位，第 1 代。*
¹ *seed 24005 native G 被 resume 過，所以其 engine log 從第 2 代開始，沒有 gen-1 的 diversity 行
（§2.2）。它的第 1 代母體在 `trajectory.jsonl` 中完好（11,405 個候選，11,284 個
有效）；缺的只是由 log 導出的 diversity 純量。該列的 n = 4。*

三個讀法，皆由這些數字支持：

1. **實現出的組成之抽樣誤差確實如預測般縮小。** 整體量的跨 seed 全距在兩臂都從 0.003（P0 = 512）
   降到 **低於 log 的 0.001 列印解析度**（P0 = 11,405）—— 與 22× 更多抽樣所預期的 √22 ≈ 4.7× 縮減
   一致。Gen0 的抽樣確實成為它所抽樣之分布（無論那是什麼）的更忠實實現。
2. **但兩個 P0 水準之間的*中心值*未變**（G 兩者皆 0.568、F 兩者皆約 0.575）。實現出的 Gen0 組成
   **在 512 時就已經收斂**。所以 22× 的操作買到的是*精確度*，而不是一個*不同的*實現分布。這是對
   §12.1 稀釋框架的一個實質回答：「大型 uniform Gen0 會把 free-gene 的邊際分布填滿」這個前提只對了
   一半 —— 邊際分布在 512 時就已填滿；native 額外提供的是對尾部更深的抽樣。
3. **而且實現出的分布在任一 P0 水準下都*不是*所意圖的那個。** 從所設定的 per-gene 分布做獨立抽樣
   預測為 0.6306；觀測值在兩種變體中都是 0.568，短少 `30 × 0.0626 = 1.88` 個 gene-unit。介於所設定
   機率與被接受母體之間的某個環節 —— `space.sample()` 中的相異性加可行性剔除 —— 移除了大約兩個
   gene 份量的變異。**Treatment 是依規格遞送進 sampler 的（§1.3 逐位元驗證了 weights，並精確重現了
   §3.4b.3 的機率）；偏離名目 prior 的是*被接受的母體*，且兩臂偏離的方式相同。** 兩臂差為 +0.007，
   而名目 prior 預測為 −0.0069（§6.2 第 3 點）。

**讀法 1–3 的證偽方式：** 在每個 P0 水準、每一臂各跑一次短的 medium run 並附掛 engine observer，
讀出 `per_gene_diversity`，或 dump 出 Gen0 個體。那會把上述全部從整體推論轉為 §12.4 所要的直接頻率表。
**建議執行、成本低廉、此處未做。**

---

## 8. 答案彙總表

| 問題 | 重點結論 | 狀態 |
|---|---|---|
| Native 執行已驗證 | 10/10 次 run：`pop_size = 11,405`、`_pop_size = 512`、`large_space`、stock warning 存在、`DUCTILE_FORCE_P0` 不存在、weights = Lock B、0 個 live degradation marker | **PASS** |
| Law-1 → law-2 decay | 第 1–9 代 law 1 精確（11,405→554）；law 2 在**第 8–9 代**介入（capped large：第 6 代）；到第 29 代降至下限 256–258；兩臂對稱 | **verified** |
| **Q1 穩健性** | 中位數 F/G 0.9971 → **1.1391**；幾何平均 0.893 → **0.9846**；為正 2/5 → 3/5；跨 P0 的 per-seed r = **−0.458**；無任何成分 ≥4/5 | **在可用精確度下不確定** —— 方向既未確認也未推翻 |
| **Q2 稀釋** | 最終 champion：集中趨勢趨向 0、離散度 **+51 %** ⇒ 無法裁決。Gen0 中心：**+2.0 % → +3.4 %、3/5 → 5/5** ⇒ 所遞送之 prior **無稀釋** | 混合；中心結果穩固 |
| **Q3 (i) 極值擴大** | `ln(extreme F/G)` 平均 **−2.2 % → +1.5 %**；4/5 個 seed 收窄 | ## **在 medium 上被 REFUTED** |
| **Q3 (ii) 中心維持／擴大** | 中位數 1.0251 → **1.0331**；**5/5** 為正 | **SUPPORTED** |
| **Q3 (iii) large > medium 梯度** | native large 仍在跑 | `NOT_EVALUATED` |
| 有效率產物 | 佔 11,405 的 G 98.93–99.08 %、F 98.74–99.12 % | **已排除** |
| 實現 vs 意圖的 Gen0 | 跨 seed 全距 0.003 → <0.001（精確度 ↑ 為 √22）；中心值在 512 與 11,405 之間**未變**；兩者皆 **0.568/0.575 vs 預測的 0.6306** | 已於整體層次量測；per-value 表 `NOT_EVALUATED` |
| **主導 confound** | medium 的 7× remeasure 呈**雙峰，在單一 27 s 窗內 2–6×**；經驗 P95 log 殘差 **0.83–1.20 vs η_medium = 0.0042** | **新增、具決定性** |

---

## 9. 給 main session —— authority document 可能需要的項目（此處未編輯任何東西）

1. **`η_medium = 0.0041953` 並不描述實際量測到的那些 medium champion。** 70 個 native-medium
   remeasure 點的經驗 P95 `|log residual|` 為 **0.828**，70 個 capped-medium 點為 **1.196** ——
   是釘死值的 200–285×。Large（max÷min 1.024–1.053）與 tiny（9/10 為 1.002–1.036）不受影響。
   來源：三個 shape 的 `champion_interleaved_raw.jsonl`。
   後果：medium 的非退步下限 `F/G ≥ 0.9958` 與改善門檻
   `F/G > 1.0042` 正被套用在一個誤差超過兩個數量級的噪音模型上，而 ≥4/5 的方向性 gate 在這個 shape
   上沒有檢定力。
2. **Index §7.1 含有一句與原始資料相矛盾的話：** *"these are genuine champion differences,
   not measurement noise"*。對 seed-24001 arm-F capped champion 的七次重播，同一個 process、同一張卡、
   27 s：2,234 … 13,547 GFLOP/s。建議由 main session 決定 §7.1 應如何更正；本分析刻意未編輯它。
3. **§12.4.4 的預測 (i) 在 medium 上被推翻**（§6.2）。預測 (ii) 獲支持（§6.3）。
   預測 (iii) 待 native large。依 §12.2 的誠實條款，該推翻必須按原文記錄，且 medium 特有的但書
   （雙峰量測可能遮蔽尾部效應）須與其並列陳述，而非取代它。
4. **名目 vs 實現的 Gen0 diversity 落差（§7 讀法 3）。** 被接受的 Gen0 母體比「從所設定 prior 做獨立
   抽樣」所預測的少約 1.88 個 gene-unit 的多樣性，兩臂相同；而 guided 臂實現出的 diversity 比
   baseline **高出** +0.007，prior 預測的卻是 −0.0069。這是關於 `space.sample()` 之
   相異性＋可行性剔除的管路層級事實，目前並未在 §3.2b/§3.4b 中描述。低成本修法：
   每個 P0 水準、每一臂各跑一次啟用 observer 的短 run，以擷取 `per_gene_diversity`。
5. **medium null 的次要根本原因（§4.1）：** 出貨的 medium prior 給 `DepthU = 128` ——
   眾數 champion 值（跨兩臂與兩個 P0 水準為 11/20，在 native 的 *prior-free* baseline 臂為 3/5）——
   只有 0.0723 的抽中機率，卻給 `DepthU = 32`（0/20 個 champion）0.2096；且它偏好
   `1LDSBuffer = 0`（0.669），而 5/5 個 native baseline champion 使用 `1`。值得與
   §3.4c.4 的 ρ 但書並列陳述：在 medium 上，prior 不只是被削弱，它在兩個 activated gene 上都指向
   偏離實現出的最佳值。
6. **偏離紀錄已確認，未發現新的偏離：** GPU-5 remeasure（index §8.3 的理由原封適用；兩個 P0 水準
   現在共享同一項偏離，這對 Q2 *有幫助*），以及 seed-24005 arm-G 的
   `RESUMED_RUN_PARTIAL_LOG` 且逐元素 `n_evals` 交叉核對通過。該 seed 上被 quarantine 的
   `native_gen0_degraded.json` 是 false positive，且**不是** §12.7 的觀察。

---

*本分析在已完成的 artifact 上以唯讀方式進行。沒有任何 run 被啟動、重啟、終止或修改；
GPU 2/3/4/6/7 上進行中的 native `large` run 未被觸碰。未編輯任何 authority document。
無 seal、無 commit、無 push。*
