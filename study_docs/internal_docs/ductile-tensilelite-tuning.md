# Ductile 與 TensileLite Tuning 深入比較：設計原理、實作差異與實務策略

> **Source URL:** https://amd.atlassian.net/wiki/spaces/~7120204c779face96d403c9783064701435635/pages/1772982240/Ductile+TensileLite+Tuning
> **pageId:** `1772982240`
> **Space:** personal space `~7120204c779face96d403c9783064701435635`（Lee, Perry；authored via ROVO AI）
> **Version:** 1
> **Fetched on:** 2026-07-08 (via Atlassian Confluence MCP, `convert_to_markdown=true`)
>
> 本頁完整內容。聚焦 Ductile（GA backend）與 TensileLite Grid Search tuning 的設計、差異與實務策略。
> 內文提及的其他 Confluence 頁（GEMM Kernel Optimization、Difference between Origami and Formocast、
> Kernel Generator: TensileLite 等）標題原樣保留，對應 pageId 見 [README.md](./README.md)。

---

## Summary

本文聚焦 **Ductile（Genetic Algorithm backend）** 與 **TensileLite Grid Search tuning** 在 AMD GEMM 優化生態系中的角色與差異，整理設計理念、搜尋行為、優缺點與實務建議，供 GPU/ML 效能工程師與 tuning 工程師在 MI300X、MI350 等新架構上選擇合適的調校工具與流程。核心重點包括：

- 說明 hipBLASLt、Tensile/TensileLite、GEKO、Origami/Formocast 與 Ductile 之間的分工與串接方式。
- 系統解析 **TensileLite** 如何透過 YAML `ForkParameters` 建立參數笛卡爾積做 **窮舉 grid search**，並在 GridBased / Equality library 中產生 solution；說明其在 OOB（out-of-box）效能與 broad coverage 上的優勢。
- 深入介紹 **Ductile** 基於 TensileLite 的 **基因演算法（GA）搜尋框架**：染色體設計、適應度（GFLOPS）計算、`--convert-config` 擴張參數空間，以及在 GEKO 中作為預設 tuning backend 的角色。
- 系統比較兩者在搜尋空間、tuning 時間、達成效能、可重現性與維護成本的 trade-off：Grid Search 具 **決定性與完整覆蓋**，GA 則在大空間與 hot shape 上提供 **更高的效能與更好的可擴展性**。
- 彙整實務策略：新架構 bring-up、library baseline 建立時偏向 TensileLite；針對少量 hot model shapes 追求極致效能時，優先導入 Ductile / GEKO GA；並建議以 Dense Search + bench-driven swap 作為中介層，減少不必要的 kernel 重新產生與維護負擔。

---

## 一、前言與背景脈絡

### 1.1 AMD GEMM kernel 優化生態系概觀

在 ROCm 生態系中，GEMM（General Matrix-Matrix Multiplication）是深度學習與高效能運算的核心算子。AMD 內部為了在不同 GPU 架構與 datatype 上提供高效能 GEMM，逐步發展出一整套由 **函式庫、codegen 與 tuning 工具** 組成的生態系，主要包含：

- **hipBLASLt**：面向使用者的高階 GEMM 函式庫，類似 cuBLASLt，支援多種 precision、豐富的 epilogue（bias、activation、softmax、layernorm 等），並透過 solution selection 機制，在執行時從內建 solution library 中選擇合適 kernel。（Understanding hipBLASLt）
- **Tensile / TensileLite**：GEMM kernel 的產生與 tuning backend。傳統 **Tensile** 主要為 rocBLAS 服務，而 **TensileLite** 是針對 hipBLASLt / hipSPARSELt 設計的輕量 codegen backend，以 YAML 配置描述 tuning 問題與參數空間，透過 Python + `rocisa` 生成組合語言 kernel。（Tensilelite - GEMM kernel generation）
- **Origami / Formocast**：在已有 solution pool 上運作的進階 **solution selection heuristics / 模型**。Origami 以 rule + heuristic 搜尋，Formocast 則使用硬體模擬與模型預測，從 TensileLite 產生的大量 kernel 中預測不同 shapes 的最佳解。（Difference between Origami and Formocast）
- **GEKO（GEMM Kernel Optimization）**：一套 Python framework，從 hipBLASLt log 出發，自動產生 TensileLite config、執行 tuning（可選 Ductile GA 或 Tensile Grid Search）、分析效能並回寫 hipBLASLt library。（GEMM Kernel Optimization）
- **Ductile**：建立在 TensileLite 之上的 **基因演算法（GA）搜尋後端**，透過 GA 在巨大參數空間中尋找對特定 GEMM shapes 更高效的 kernel parameters，而非窮舉所有 YAML grid point。（Ductile (Genetic Algorithm)）

在整條鏈路裡，可以把責任劃分為：

> **TensileLite / Ductile** — 在離線階段產生與調校「什麼 kernels 存在、每個 shape 的最佳 kernel 是誰」。
> **Origami / Formocast / GridBased selection** — 在執行階段或預先建 library 時，決定「對於這個 GEMM 問題該選哪個 solution index」。
> **hipBLASLt** — 對外呈現簡潔 API，並利用上述機制提供接近硬體上限的 GEMM 效能。

### 1.2 為何需要 tuning backend：從 generic 到 shape-specialized kernel

GEMM 效能高度依賴於矩陣尺寸 (M, N, K, Batch)、資料型別、memory hierarchy 以及 GPU 微架構。單一「通用」kernel 幾乎不可能在所有 case 上都接近峰值，因此 AMD 的策略是：

1. 利用 TensileLite 定義一族高度參數化的 GEMM kernel family（MacroTile、DepthU、WorkGroupMapping、VectorWidth、prefetch、LDS 佈局等可以調整）。（Kernel Generator: TensileLite）
2. 針對實際工作負載中常見的 shapes（來自 hipBLASLt log 或標準 benchmark），在參數空間上進行 **系統化搜尋**，為每個 shape 找到效能最好的參數組合，寫入 LibraryLogic YAML。
3. 執行時 hipBLASLt 只需根據 matrix shape / datatype / epilogue 等 key，在 equality 或 grid-based library 中查表拿到 solution index，再啟動相對應 kernel。

在 tuning backend 上，目前主流有兩種：

- **TensileLite Grid Search**：以 `ForkParameters` 定義的參數組合做 **笛卡爾積窮舉**。在每個組合上編譯 kernel、實測效能，選擇 best-of-grid 解。
- **Ductile GA Search**：視參數組合為「染色體」，透過 selection / crossover / mutation 反覆演化，期望在較少試點下找到「接近甚至優於 grid 最佳點」的配置，且能探出 YAML grid 外圍的組合。（Ductile (Genetic Algorithm)）

Grid Search 強項是 **完整性與可重現性**，適合用來建立 baseline library；GA 則在參數空間龐大或最佳區域未知時，更有機會在合理時間內找出高品質解。實務上常見做法是二者搭配：先用 TensileLite 建立 broad coverage，再用 Ductile 對少數 hot shapes 進行深度強化。

### 1.3 本文目標、問題定義與讀者

儘管內部已有大量介紹 TensileLite tuning、hipBLASLt 使用與 Ductile 基礎資訊的文件，針對：

- **TensileLite Grid Search** 與
- **Ductile GA 搜尋**

這兩種 backend 在設計理念、搜尋模式、效能/效率 trade-off、可重現性與維護成本上的 **系統性比較**，資訊仍相對分散在各頁面與簡報中（如 GEMM Kernel Optimization、GEMM Programs Status 等）。

本文的目標是：

1. 釐清 Ductile 與 TensileLite 在 AMD GEMM 生態系中的 **架構定位與關係**。
2. 深入解析二者的 **搜尋模型與 tuning 工作流程**（含 YAML 配置與 GEKO/hipBLASLt pipeline 串接）。
3. 系統性比較其在搜尋空間涵蓋度、tuning 時間與效能提升上的 **優缺點與隱含假設**。
4. 給出針對 **新 GPU 架構 bring-up、hot model shapes 深度優化、既有 library solution 維護** 的 **實務建議與混合策略**。

預期讀者包括：

- 需要提出 tuning 要求與解讀效能報告的 **GPU / ML 效能工程師**。
- 實際編寫 YAML / 操作 TensileLite / GEKO / Ductile 的 **compiler / tuning 工程師**。
- 維護 hipBLASLt solution library 的 **math library maintainer**。

---

## 二、TensileLite Tuning 設計與運作

### 2.1 架構與定位

TensileLite 是從原始 Tensile fork 出來、針對 hipBLASLt / hipSPARSELt 需求精簡後的 **現代化 GEMM codegen backend**。與舊 Tensile 相比，它有幾個關鍵差異：

- 主要服務對象從 rocBLAS 轉為 **hipBLASLt**，更偏重 ML workload 與 Lt API 支援。
- 使用 `rocisa` 與（逐步導入的）**StinkyTofu** 作為組合語言 IR 與排程 backend，讓 kernel 生成更易於優化與驗證。
- 支援 MXFP4/8、FP8、BF16 等 ML 重度使用 datatype，並提供多種 fused epilogue。

在整條 pipeline 中 TensileLite 主要扮演兩個角色：

1. **Code Generator**：根據 YAML 的 ProblemType + ForkParameters 產生多個 candidate kernels，編譯成 code object。
2. **Tuning Engine（Grid Search 模式）**：根據 BenchmarkFinalParameters 定義的 shapes，在每個 candidate kernel 上 benchmark，找出 per-shape best solution，並產出 LibraryLogic YAML 供 hipBLASLt 使用。

在 GEKO workflow 中，TensileLite 的 Grid Search 是其中一個可選 backend（`--backend tensile`），主要用於需要 **完整探索某個參數空間** 或做實驗時。

### 2.2 搜尋模型與演算法

TensileLite tuning 的核心在於 YAML 中的 `ForkParameters`。它描述的是「**要嘗試哪些 kernel 參數組合**」，TensileLite 會對這些參數做 **笛卡爾積**，每一個組合對應到一個 candidate solution。

下表整理常見的 ForkParameters 與其影響：

| 參數名稱 | 作用與影響重點 |
| --- | --- |
| `MatrixInstruction` | 選擇底層 MFMA/WMMA 指令與 block tile 大小。例如 `[32,64,128,...]` 決定 macro tile 基本形狀與 K-unroll。 |
| `DepthU` | 沿 K 維的展開深度；加大可提升運算/記憶體比，但會提高 VGPR 使用量與 register 壓力。常見候選如 `[32, 64, 128, 256]`。 |
| `WorkGroup` | workgroup (block) 的 thread 佈局，影響 occupancy 與 CU granularity。 |
| `WorkGroupMapping` | 控制 workgroup 對 logical tile 的 mapping，影響 cache locality 與 L2/L1 reuse。 |
| `PrefetchGlobalRead` / `PrefetchLocalRead` | 決定 global/local prefetch 階數與時機，影響 memory latency 隱藏程度。 |
| `GlobalSplitU` / `GlobalSplitUAlgorithm` | 決定是否沿 K 維做 split-K / StreamK，增加平行度但需要 merge 或 fix-up overhead。 |
| `VectorWidthA/B`、`GlobalReadVectorWidthA/B` | 控制 vectorized load/store 寬度，影響 memory coalescing 與對齊限制。 |
| `LdsPadA/B`、`TransposeLDS`、`1LDSBuffer` | 控制 LDS 佈局與是否 double-buffer，影響 LDS bank conflict 與 pipeline overlapped 程度。 |

TensileLite tuning 的流程大致如下：

1. **枚舉所有 ForkParameters 笛卡爾積**：產生數十到數百個 candidate solutions。實務上 YAML 會經過規則與經驗強烈裁剪，否則空間會爆炸。
2. **過濾無效 solution**：例如超過 VGPR/LDS 限制的配置，在生成階段就會被標記為 invalid，跳過 benchmark。
3. **對每個 valid solution 進行 benchmark**：對 BenchmarkFinalParameters 中列出的每個 ProblemSize，逐一量測 kernel 的 GFLOPS、時間與帶寬，通常會透過 warmup + 多次 iter 取最好的或中位數值。
4. **選出 per-shape best solution**：將 winning solution 與 shape 關聯起來，寫入 `3_LibraryLogic/*.yaml` 中，供後續 TensileCreateLibrary 或 hipBLASLt 使用。

ProblemSize 本身可以使用 `Exact` 或 `Range` 語法，例如：

- `Exact: [M,N,Batch,K]` — 單一 shape。
- `Range: [[16,48,256],[16,32,512],[1],[32]]` — 透過起點/步長/終點與加速步進語法定義一系列 shapes。

此外，TensileLite client 支援多 GPU 並行調校：當啟用 multi-GPU 執行時，它會將 N 個 benchmark 問題平均切分到 G 張卡，各卡負責不相交的子集合，最終再 merge CSV 結果。

### 2.3 使用方式與配置

在實務 workflow 中，TensileLite tuning 通常是這樣串入 hipBLASLt / GEKO pipeline 的：

1. **收集 GEMM 問題** — 在實際模型或 benchmark 上執行 hipBLASLt，開啟 logging：

```bash
HIPBLASLT_LOG_MASK=64 HIPBLASLT_LOG_FILE=hipblaslt-log.yaml python run_model.py
```

   log 會包含 `function=matmul`、M/N/K/batch_count、datatype、transA/B 等欄位。

2. **利用 config generator 產生 tuning YAML** — 可以使用獨立的 `tensile_config_generator.py` 或 GEKO 的 `config_generator` 子模組，將 log group by GemmType，並依照硬體 profile 為每個群組產生對應的 ForkParameters 範圍與 BenchmarkFinalParameters。

3. **執行 TensileLite tuning** — 直接呼叫 Tensile main：

```bash
cd /path/to/hipBLASLt/tensilelite
./Tensile/bin/Tensile config.yaml output_dir
```

   或透過 GEKO `./bin/geko --tune --backend tensile` 自動執行 configure + optimize。

4. **合併 tuned LibraryLogic 至 hipBLASLt** — 使用 TensileMergeLibrary 或 `Tensile/Utilities/merge.py`：

```bash
python3 tensilelite/Tensile/Utilities/merge.py --no_eff \
  library/.../Equality/ \
  output_dir/3_LibraryLogic/ \
  library/.../Equality/
```

   或 GEKO 產生的 `final_libs/` 再用 TensileMergeLibrary 合併。

5. **重建 hipBLASLt 並驗證效能** — 重新 build：`./install.sh -idc -a gfx9xx`。使用 hipblaslt-bench 驗證 tuned library：

```bash
hipblaslt-bench --yaml hipblaslt-log.yaml --device 0 --print_kernel_info
```

這些步驟目前已經被 GEKO pipeline 自動化：`--tune` 模式會讀取 workload log、產生 TensileLite config、啟動 tuning jobs、分析效能並產出 `final_libs/`，最後再由使用者選擇是否 merge 回 hipBLASLt。

### 2.4 優點、限制與隱含假設

**優點**

1. **搜尋完整性與可重複性強**
   - Grid Search 在給定 YAML `ForkParameters` 下，會遍歷所有有效的參數組合，因此在「定義好的空間」內可以找到真正的 global optimum。
   - tuning 結果 **完全決定於 YAML** 與環境變數，沒有隨機因子；同一 config 在相同硬體與驅動上可完全重現。
2. **適合 broad coverage 與 baseline library 建立**
   - 在新架構 bring-up 時，透過 per-arch 的 ForkParameters profiles（例如 GEKO `fork_params/hw_profiles/gfx942`）設計一組保守而具代表性的 grid，可為 BF16/FP16/FP32 等 datatype 建立穩定的 baseline library。
   - 內部效能評估顯示，透過 GridBased + Origami/Formocast，平均效能可達 **約 98% 的 exact tuned 效率**，最大 gap 約 10–15% 之間。
3. **易於分析與 debug**
   - YAML 完整描述了每個 solution 的所有參數，kernel 名稱也編碼了 MacroTile / MI / WorkGroup 等資訊，方便從 hipblaslt-bench log 反推出 tuning 配置。
   - 配合 characterization tests（目前 TensileLite unit + characterization 測試覆蓋率已達 **約 75%**）可以穩定監控行為變化。

**限制**

1. **搜尋空間容易爆炸，tuning 成本隨維度指數成長**
   - 每增加一個 ForkParameter 或增加其候選值，candidate 數量即等比成長。
   - 即使透過 `SkipSlowSolutionRatio` 等 global parameters 過濾慢解，仍可能導致單個 config 內需要編譯與測試數十甚至上百個 kernels。
2. **YAML 設計高度敏感，錯誤設定可能導致無效 kernel 或 tuning 無法收斂**
   - 例如不合理的 `GlobalReadVectorWidthA/B` 會造成 misaligned load，或過大的 `DepthU` 導致 VGPR 溢出而被過濾，導致實際有效的搜尋空間遠小於預期。
   - 若問題 sizes 與 ForkParameters 不匹配（例如 macro tile 與 M/N 粒度不合），即使 tuning 完成也可能無法達到理想效能。
3. **tuning 時間在大空間下難以接受**
   - 在 GEMM Programs Status 中，Library Creation 專案估計 MI300/MI350 的 library 建立時間約 **20–30 分鐘/arch**，這是在已經設計良好的 grid 下。
   - 若對單一 shape 進行 equality tuning，整個流程從 config 產生、tuning 到 merge/build 通常也在十數分鐘等級，很難對大量 shape 做 full grid equality 搜尋。

**隱含假設**

- YAML grid 已足夠涵蓋「高效 kernel 區域」，也就是說最佳解大致落在少數已知的 MI / MacroTile / DepthU / WGM pattern 附近。
- 使用者能合理收斂參數範圍（例如根據 CU 數限制 `GlobalSplitU`、根據 register 壓力限制 `DepthU` 候選）。
- compile / runtime benchmark 開銷在可接受範圍內；否則需要分割 config（多 YAML、多 GPU）或預先以 heuristic / 模型縮小搜尋空間。

---

## 三、Ductile 設計與運作

### 3.1 工具定位與與 GEKO 的關係

**Ductile** 是一個建立在 TensileLite 之上的 tuning backend，其目標是：

> 在相同或更大的參數空間下，比 Grid Search 以 **更少的 kernel 測試次數** 找到效能更好的 solution，特別針對少數精選的 hot GEMM shapes。

設計上，Ductile：

- 重用 TensileLite 的 YAML 輸入格式與大部分 codegen 能力：ProblemType、ForkParameters、BenchmarkFinalParameters、LibraryLogic 等結構完全相容。
- 將「搜尋所有 ForkParameters 笛卡爾積」替換成基因演算法：每個解即為一組 kernel parameters 的向量（染色體），GA 在此空間中演化以最大化效能。
- 在 GEKO framework 中作為 **預設 tuning backend**：`scripts/configure.py` 有 `--backend ductile|tensile` 選項，CLI `./bin/geko --tune` 預設使用 `ductile`。

也就是說，在 GEKO “GA-based Optimization” workflow 中：

```text
hipBLASLt logs ──► configure (產生 TensileLite YAML)
               └─► optimize (backend = ductile)
                   └─► 實際呼叫 Ductile → GA tuning
```

而 backend = `tensile` 則對應傳統 Grid Search。

Ductile 也可以獨立於 GEKO 使用，只要在 PYTHONPATH 中加入 tensilelite，再直接呼叫 Ductile binary：

```bash
PYTHONPATH=/path/to/hipBLASLt/tensilelite \
/path/to/TuningDriver/Ductile/bin/Ductile --convert-config config.yaml output_dir
```

### 3.2 Genetic Algorithm 架構

Ductile 的 GA 搜尋建立在幾個核心概念之上：

| GA 元素 | 在 Ductile 中的具體對應 |
| --- | --- |
| **染色體（Chromosome）** | 一組完整的 GEMM kernel 參數設定，例如 `DepthU`, `GlobalReadVectorWidthA/B`, `NonTemporalA/B/C/D`, `StaggerU`, `WorkGroupMapping`, `StreamK`, `VectorWidthA/B` 等，每個 gene 對應一個參數或離散選項。 |
| **種群（Population）** | 一批 candidate kernels。初始族群可以由 YAML 內原有的 ForkParameters 產生（含 Groups 中的 MatrixInstruction/WorkGroup 組合）。 |
| **適應度函數（Fitness）** | 對每個 candidate 建 kernel、實際在 GPU 上 benchmark，根據 GFLOPS 或執行時間評分。Ductile 乃是「benchmark-driven backend」——真實效能就是 fitness。 |
| **選擇（Selection）** | 保留效能較佳的 solutions 作為下一代父母；較差者被淘汰。具體策略實作在 Ductile config 中（預設不建議修改）。 |
| **交叉（Crossover）** | 將兩個父代染色體的部分參數交叉組合，形成新的子代配置，例如從父 A 取 `DepthU` / `GRVW`，從父 B 取 `StaggerU` / `NonTemporal*`。 |
| **突變（Mutation）** | 以低機率隨機變更某些參數（例如將 `GlobalReadVectorWidthA` 從 4 改為 8），以避免過早收斂與陷入 local optimum。 |
| **終止條件** | 迭代到固定世代數、效能收斂或時間預算耗盡。 |

Ductile 將這些 GA hyper-parameters（族群大小、交叉/突變率、世代數等）集中在 `~/Ductile/ductile/config/defaults.yaml` 中，並允許在輸入 YAML 內加入一個 `ductile` section 覆寫。不過官方建議 **大多數情境下使用預設值即可**，修改需謹慎。

值得注意的是，若加入 `--convert-config`，Ductile 會先執行一個轉換步驟，將原本 tuning driver 產生的 config 擴張成更大的參數空間。例如：

- 將 `GlobalReadVectorWidthA/B` 從 `[2,8]` 擴張為 `[-1,-2,2,3,4,6,8]`（加入自動決策與更多候選）。
- 將 `NumElementsPerBatchStore`、`NonTemporalA/B/C/D`、`StaggerU`、`WorkGroupMapping/XCC` 等改為更廣泛的離散集合。

這讓 GA 能在遠大於原始 grid 的空間中搜尋，而不必明列所有組合。

### 3.3 使用方式與工作流程

在最基本的使用情境中，Ductile 的輸入就是一份 TensileLite tuning YAML；若加上 `--convert-config` 則會先擴大 ForkParameters：

```bash
/path/to/Ductile/bin/Ductile --convert-config config.yaml output_dir
```

整體 workflow 與 TensileLite 相似，只是「搜尋引擎」從 grid 換成 GA：

1. **準備 YAML**
   - 可以直接使用 TuningDriver 或 GEKO configure phase 產生的 YAML；對使用者而言與 Grid Search 相同。
   - 若希望 Ductile 自動擴展參數空間，加入 `--convert-config`，會產生一份擴張後的新 YAML，裡面 `ForkParameters` 的範圍與值會大幅增加。
2. **執行 Ductile GA tuning**
   - Ductile 根據 YAML 啟動 GA search：
     - 初始族群可以由原始 ForkParameters 隨機採樣而來。
     - 每個個體經過 kernel 生成與 benchmark，計算 fitness（GFLOPS）。
     - 經過多代 selection / crossover / mutation，族群逐漸向高效區域收斂。
3. **產生 LibraryLogic 與 log**
   - 和 TensileLite 一樣，Ductile 最終會在 `output_dir/3_LibraryLogic/` 下產生 logic YAML，可直接透過 TensileMergeLibrary 合併入 hipBLASLt。
4. **在 GEKO 中的整合**
   - GEKO `--tune` + `--backend ductile` 會自動完成上述流程，並在 optimize phase 中對每個 GemmType 產生 `build_*/3_LibraryLogic/*.yaml`，最後統一 merge 為 `final_libs/`。

實務上一個重要細節是：**多 shape 共用同一 config 時，GA 會傾向收斂到對多數 shape 都不太差的「折衷解」**。Ductile 文件建議：

- 若 tuning shapes 差異很大，最好讓 TuningDriver 每個 shape 產生一份獨立 YAML（`MAX_NUM_KERNELS_PER_CONFIG: 1` + `--cluster 0`），讓 GA 專注於單一 shape。
- 否則容易出現某些 shape 被犧牲，而 GA 找到的只是「對全部 shape 還算 OK」但非極致的解。

### 3.4 優點、限制與隱含假設

**優點**

1. **大參數空間下更有效率的搜尋**
   - 當我們允許 `--convert-config` 擴張 ForkParameters（例如 GRVW、NonTemporal、StaggerU、WGM/XCC 等），如果用 Grid Search 幾乎無法窮舉完所有組合；GA 則能以有限的 kernel 測試數量在此空間中找到高效解。
   - 對於單一 shape，GEKO/GA-based tuning + GEMM Tuner 的經驗顯示，平均 uplift 可達 **約 5–10%**，而 tuning 時間約 **15 分鐘/shape**，相較於傳統工具的數天搜尋大幅縮短。
2. **能發現 YAML grid 未明列的組合**
   - 透過自動擴張與突變，GA 可以組合出原本 `ForkParameters` 未明確列出的參數組合（例如某些非直觀的 `NonTemporal*` 或 `NumElementsPerBatchStore` 組合），相當於在「連續化」的配置空間中內插與外插，而不侷限於粗粒度 grid points。
3. **適合 hot shapes 的極致優化**
   - 當已有 OOB/grid-based library 表現已達 **約 0.9–0.98×** 理論最佳時，對某些關鍵 shapes 再額外榨出 **3–10%** 的效能很困難；此時 GA 能在更精細的配置空間中搜尋「非典型」解，獲得額外 uplift。

**限制**

1. **結果具隨機性，可重現性需要額外管理**
   - GA 的演化路徑受初始化隨機種子、突變與交叉策略影響，同一 YAML 可能在不同 run 找到略有差異的解。
   - 若要完全重現結果，必須明確記錄 GA seed、族群大小與演化設定，並在完全相同硬體/驅動環境下重新執行。
2. **需要調整 GA hyper-parameters，在噪音較大的 benchmark 下較敏感**
   - 若族群過小或世代數不夠，容易收斂在 local optimum；過大則 tuning 時間拉長。
   - benchmark 噪音（例如其他作業系統負載、DVFS 波動）會影響適應度排序，使 GA 探索方向受到干擾；通常需要較多 iter 與較嚴的 outlier 過濾。
3. **多 shape 混 tuning 時容易出現 suboptimal**
   - 如前述，若一個 GA 族群同時服務多個差異很大的 shapes，適應度會被綜合評估，GA 傾向挑出「平均還可以」的配置，而不是對每個 shape 都最好的配置。
   - 這在 tuning driver 自動將多個類似 shape 打包為同一 YAML 時特別需要注意，實務上最好將 **最關鍵的 few shapes 拆成獨立 config**。

**隱含假設**

- 性能 landscape 在參數空間中具有一定「平滑性」與局部相關性：小幅變動 gene（例如略調整 GRVW、StaggerU）不會導致表現完全失控，使 GA 能透過局部變異與 recombination 持續改善。
- benchmark 噪音可透過多 iter + 穩定選擇策略控制在可接受範圍內，避免 GA 被 outlier 誤導。
- tuning 的目標硬體與 workload 在一段時間內相對穩定，不會每週更換架構或大幅變動模型，使得 GA 產出的 tuned solution 具備一定壽命。

---

## 四、Ductile vs TensileLite：系統性比較

### 4.1 搜尋策略與參數空間

從搜尋策略的角度看，兩者代表了 **窮舉式（Grid）vs 啟發式（GA）** 兩端：

- **TensileLite Grid Search**
  - 給定 YAML `ForkParameters`，實作上就是產生 **所有合法參數組合的笛卡爾積**，對每個組合建立 kernel 並量測。
  - 搜尋空間完全由使用者手動定義：若未在 ForkParameters 中列出某組合，Grid Search 就永遠不會探索到。
  - 典型用途是：在合理範圍內尋找「某一族預先設計的 MI/MacroTile/DepthU/WGM 組合」中的最佳點。
- **Ductile Genetic Algorithm**
  - 仍以 YAML 提供參數域資訊，但藉由 `--convert-config` 擴張後，GA 能在一個 **遠大於明列 grid** 的離散空間中搜尋。
  - 初始族群會利用 YAML 的參數域，但之後透過突變與交叉，自行「組合」出未在 YAML 條列中的參數排列。
  - 可以視為：ForkParameters 不再是「完全列舉的 grid」，而是「每個 gene 的合法離散值集合」，GA 在此高維離散空間上做啟發式搜尋。

用一個比喻來說：

- Grid Search 好比在一個事先畫好格子的棋盤上，一格一格試；棋盤的格子位置是人畫好的。
- GA 則是先定義棋盤的 **座標範圍與離散刻度**，但不一定每個點都畫格子；演算法在這個座標空間中飛來飛去，透過實驗判斷哪裡有「高地」。

在 GEKO 中，backend 選擇會直接影響 tuning 空間的定義方式：

- `--backend tensile` → 較適合 moderate 大小的 grid、專注於「驗證某組預設 grid 是否足夠好」。
- `--backend ductile` → 較適合 unknown / 超大空間、尋找 grid 外甚至 rule 之外的高效 kernel。

### 4.2 效能、效率與可擴展性

從 tuning 成本與效益角度可以做一個粗略對照（以 MI300/MI350 內部經驗為例）：

| 指標 | TensileLite Grid Search | Ductile GA 搜尋（透過 GEKO / GEMM Tuner） |
| --- | --- | --- |
| 搜尋空間大小 | 受限於 YAML 列出的 ForkParameters 笛卡爾積 | 可透過 `--convert-config` 大幅擴張 gene 值域 |
| 每 shape tuning 時間 | 視 grid 大小而定，Equality full search 可能達 10–30 分鐘甚至更久 | **約 15 分鐘/shape**（典型設定），依 GA config 與硬體而定 |
| 覆蓋多 shape 的成本 | shape 數量 ×（上述時間），不易擴張到數百 shapes | 對中等數量（~百）shapes，可在數小時內完成全集 tuning |
| OOB vs tuned uplift | GridBased + heuristics 平均可達 **~98%** exact，對 hot shapes 再 equality tuning 可有 **數 % 至十數 %** 提升 | GA-based tuning 針對 hot shapes 平均 uplift **約 3–10%**，視原 OOB 與空間大小而定 |
| 對參數維度擴張的可擴展性 | 每加一維或擴大候選數，cost 成倍上升；實務上需嚴格裁剪 | cost 與「族群 × 世代數」成正比，理論上可處理比 Grid 大一兩個數量級的空間 |
| 單 run 可重現性 | 完全決定性 | 有隨機性（可透過固定 seed 與參數降低變異） |

這裡有一個關鍵觀察：**Grid Search 適合 moderate 空間（數十個 candidate）做完備探索**；一旦空間膨脹至數百、上千 candidate 時，即使技術上仍可窮舉，實務上的成本也太高，此時反而要仰賴 GA 或其它啟發式方法。

因此，可以這樣思考兩者的分工：

- 若 ForkParameters 已經由專家嚴格裁剪，grid 小到足以完整搜尋 → Grid Search 是較穩健的選擇。
- 若你懷疑「最佳解不在現有 grid 內」，或希望探索更大/更細的參數空間 → GA（Ductile）較具優勢。

### 4.3 穩定性、可重現性與可維護性

**穩定性與可重現性**

- **TensileLite Grid Search**
  - 完全決定性：同一 YAML、同一硬體/驅動組合下，每次 run 產生的 LibraryLogic 應該 bit-identical（忽略 log timestamp 等）。
  - 適合建立「標準 library」與長期維護：例如官方發行的 hipBLASLt OOB library。
- **Ductile GA**
  - 演化過程本質帶有隨機性，即使固定 seed，也可能因 benchmark 噪音或執行順序差異造成小幅變動。
  - 若要把 GA 結果納入長期維護的 library，必須額外記錄 seed + GA hyper-parameters，並在產出後用 Dense Search 或 bench-driven swap 驗證其確實是現有 solution pool 中的最佳者。

**維護性**

在維護 hipBLASLt library solution 時，兩者產出的 artifacts 形式是一致的：**LibraryLogic YAML + code objects**。差異在於「如何產生這些 logic」：

- Grid Search 產出的 YAML 具有清楚的 grid 結構，對應到 equality 或 GridBased 表格；未來若想做 bench-driven swap，可以直接在現有 grid entries 中交換 solution index，而不改變 solution pool。
- GA 產出的 YAML 通常是 per-shape 的 equality entries，參數可能較為「不規則」；若沒有配套文件紀錄 tuning 的上下文，日後要回顧某個 GA 解是否仍合理會比較困難。

從長期維護角度，合理策略是：

- 用 Grid Search（或 Dense Search）建立 **乾淨的 grid library**，確保 broad coverage 與結構化 YAML。
- 針對極少數 hot shapes 使用 GA 產生額外 equality entries（或 patch library），並用 bench-driven swap / Dense Search 確認其優勢與穩定性。

### 4.4 典型應用情境對照表

下表彙整不同實務場景下適合優先採用的 backend：

| 場景 | TensileLite Grid Search | Ductile GA |
| --- | --- | --- |
| 新架構 bring-up | ◎（全覆蓋、穩定） | △（僅 hot shape） |
| 建立 library baseline | ◎ | △（成本較高） |
| 大規模 shape 覆蓋（數百） | ◎ | △（總時間較長） |
| Hot model shapes 深度優化 | △（需細調參數，成本高） | ◎（極致效能） |
| 客戶特殊需求/快速 patch | △（流程較重） | ◎ |
| 參數空間極大/未知 | △（grid 難以設計） | ◎ |

（◎：強烈推薦；△：可行但非最佳）

這個表格背後的邏輯是：**Grid Search 強於結構化、可重複、寬覆蓋；GA 強於非結構化、未知空間與針對性優化**。真正的 tuning 策略往往是兩者疊加、再加上一層 Dense Search / bench-driven swap。

---

## 五、實務調校策略與建議

### 5.1 何時選擇 Ductile

建議優先考慮 Ductile（或 GEKO 的 GA backend）的情境：

1. **已知明確 hot shapes，需要追求極致效能**
   - 例如大型 LLM 中最關鍵的幾個 GEMM（比如 KV 變換或 FFN up/down），在 OOB library 下已經接近 roofline，但仍存在 **3–10%** 的 headroom，且這些 shapes 在整體 runtime 中佔據高比例。
   - 在這種情況下，投入約 **15 分鐘/shape** 進行 GA tuning 通常是值得的。
2. **參數空間過大，Grid Search 不可行或不確定最佳區域**
   - 當你希望同時優化較多維度（例如多種 `NonTemporal*` / `Stagger*` / `NumElementsPerBatchStore` / `UseSgprForGRO` 等）時，grid 幾乎無法列舉所有合理組合。
   - 此時可以讓 Ductile `--convert-config` 擴大 gene 值域，依賴 GA 在此高維空間中尋找好的解。
3. **需要探索 YAML grid 未涵蓋的非典型解**
   - 例如為了特定 memory hierarchy 特性（某些 cache/NUMA 配置）設計特殊的 `WorkGroupMapping` 或 `StreamKXCCMapping`，這類 pattern 通常難以在 general grid 中自然出現，GA 則可以透過突變與交叉探索這些 corner。

**實務建議**

- **以現有 YAML 為 seed，再交給 Ductile 拓展**：不要空白開始，先利用既有 TensileLite grid 規劃一組合理的 ForkParameters，再讓 Ductile 透過 `--convert-config` 擴張與微調。
- **Hot path 設較高世代數與族群大小**：對關鍵 shapes 可以容忍較長 tuning 時間，將 GA 參數調成偏「探索」以增加找到非典型高效解的機會。
- **保留完整 GA log / seed / hyper-parameters**：將這些資訊與產生的 LibraryLogic 一起存檔，未來若需要回溯或比較可再重跑 GA 或用 Dense Search 驗證。

### 5.2 何時選擇 TensileLite Grid Search

TensileLite Grid Search 仍然是大多數情境下的 **基礎工兵**，尤其在：

1. **新架構 bring-up 或大規模覆蓋**
   - 在 MI350X、MI450 等新 GPU 上，需要對 BF16/FP16/TF32/FP8/MXFP* 等 datatype 建立健全的 baseline library，這時候 Grid Search（加上 per-arch ForkParameters profile）最能保證 coverage 與穩定性。
2. **需要強可重現性與版本管理**
   - 當 tuned library 要成為產品發行版本的一部分時，Grid Search 的 determinism 對除錯與 regression 驗證非常關鍵。
   - 之後若導入 bench-driven swap re-tuning，只需修改 grid table 的 `solution_index`，不需變更 kernel solution pool。
3. **驗證現有 heuristics / grid 是否足夠好**
   - 若你懷疑 OOB library 的 GridBased 選擇在某些區域系統性偏差，可以透過小範圍 Equality grid search 來確認：在周邊 grid points 生成 candidate，實測找出真正最佳者，再更新 grid 表。

**實務建議**

- **先以保守 grid 建立 baseline**：參考 MI300 TensileLite 參數概要文件或 GEKO 的 `fork_params/hw_profiles/`，設定一組較窄但可靠的 ForkParameters 範圍。
- **熱點 shape 再導入 equality / GA tuning**：對於在 baseline 評估中出現效能瓶頸的 shapes，再針對性地啟用 Equality tuning 或交由 Ductile 深度 tuning，而非一開始就對所有 shapes 做 massive equality grid。
- **定期 review YAML 參數範圍，避免空間膨脹**：在每次架構/演算法更新後，根據實測結果收斂 ForkParameters 範圍，移除明顯低效的區域，以降低未來 tuning 成本。

### 5.3 混合與分層策略

根據近年的實務經驗，一套 **分層式 tuning 策略** 通常最具成本效益：

1. **Layer 0 — Dense Search / bench-driven swap（不產生新 kernel）**
   - 先在現有 solution pool 上做 **Dense Search（GEKO `--search`）** 或 hipblaslt-bench `--algo_method all`，確認「selector 是否把 library 用好」。
   - 對於發現 selector consistently 選錯的 grid point，可透過 **bench-driven swap workflow** 更新 grid 表而不動 kernel。
2. **Layer 1 — TensileLite Grid Search / Equality tuning（擴展 kernel pool）**
   - 若 Dense Search 顯示「即使在現有 solutions 中，也找不到滿意解」，說明需要擴展 kernel pool，這時才啟動 TensileLite tuning 產生新 solution。
3. **Layer 2 — Ductile / GA-based tuning（針對 hot shapes 做強化）**
   - 在 Layer 1 建立的 kernel pool 基礎上，針對最關鍵的少數 shapes 啟動 Ductile GA tuning，尋找在更大參數空間中的最佳解，並將這些 GA 解納入 Equality library 或作為 patch。

這樣的流程有幾個好處：

- 把大部分「library 沒被好好用」的問題交給 Dense Search + swap 解決，而不是動輒重建 kernel pool。
- TensileLite tuning 專注於真正需要新 kernel 的區域，減少不必要的 codegen 成本。
- Ductile 聚焦在極少數熱點，最大化「每分鐘 tuning 時間」產出的效益。

### 5.4 Library solution 維護與驗證

不論 backend 使用 Grid 或 GA，最終都回到一個問題：**如何長期維護與驗證 hipBLASLt library solution**。建議做法包括：

1. **定期以 bench-driven swap 檢查 grid point 是否選到最佳 kernel**
   - 對於關鍵 datatype / transpose 類型，例如 MI350 BF16 TN，定期在新的 ROCm 版本、驅動或硬體 stepping 上重新跑 bench-driven swap，確認 grid 表沒有過期或被 regression 影響。
2. **新硬體/新 workload 上先跑 Dense Search/bench 驗證覆蓋率**
   - 在導入任何新的 tuning 前，先用 Dense Search 測試現有 library 在新 workload 上的「選擇效率」（實際 vs best-of-pool），避免誤以為要大量 tuning，其實只需改善 selection heuristic。
3. **合併/更新 logic YAML 時注意 device id 與命名一致性**
   - LibraryLogic YAML 中的 `ScheduleName`、`DeviceNames`、`ArchitectureName` 必須與 hipBLASLt build 路徑與 runtime device id 對應一致，否則會造成 lookup 失敗或使用錯誤 library。
4. **保持 characterization test 覆蓋，避免 tuning regression**
   - TensileLite 的 characterization tests 目前已覆蓋 **約 75%** 的程式碼行數，任何 codegen 或 tuning 相關改動都需通過這些測試，避免在某些 corner case（例如 complex datatype、MXFPx）出現隱性 regression。

---

## 六、結論與未來展望

綜合以上分析，可以將 Ductile 與 TensileLite tuning 的定位簡潔地歸納為：

> **TensileLite Grid Search**：適合用來建立新架構 / 新 datatype 的 **broad coverage baseline library**，提供穩定且可重複的解；搭配 Dense Search 與 bench-driven swap，可以在不新增 kernel 的情況下持續改善 selection 效率。
>
> **Ductile GA（透過 GEKO）**：適合在 baseline library 之上，針對少數 **hot GEMM shapes** 於大型或未知的參數空間中尋找 **更高效的 kernel**，在成本可控的前提下取得額外數 % 到十數 % 的效能 uplift。

最重要的實務建議是：**不要把 tuning 問題直接丟給 GA 或 Grid Search**，而應該採取分層策略：

1. 先以 Dense Search 檢查 selector 是否用好現有 library。
2. 再視需要用 TensileLite 擴展 kernel pool。
3. 最後才對最關鍵的 few shapes 啟用 Ductile / GA，並將 GA 結果納入結構良好的 library 與測試覆蓋之下。

之所以這樣安排，是因為實務經驗顯示，多數「hipBLASLt 效能不好」的 ticket 其實源自 selection 或 shape mapping 問題，而非真正缺 kernel。只有在確認 library 已用好、且仍存在明顯 headroom 時，GA-based tuning 才是最具投報率的投資。

往後隨著新架構（gfx12x、CDNA4 以後）、新 datatype（更豐富的 MX family 與 sparsity 格式）與更複雜的 epilogue 出現，tuning backend 也不可避免會更仰賴 ML／啟發式搜尋。Ductile 代表了一個方向：將傳統 rule-based / grid-based tuning 擴展到演化式搜尋，在不放棄 TensileLite 穩健基礎的前提下，提供更大的探索彈性。若能持續強化 GEKO、Formocast、Origami 與 characterization tests 的整合，AMD 在未來幾代 GPU 上維持高效且可維護的 GEMM 生態系是相當有機會達成的。
