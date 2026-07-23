# Kernel Generator: TensileLite (GEMM Kernel Tuning Guide)

> **Source URL:** https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119/Kernel+Generator+TensileLite
> **pageId:** `1405870119`
> **Space:** MLSE · parent "GEMM Active Programs" (`1387220065`)
> **Version:** 13 (last updated 2026-06-16)
> **Fetched on:** 2026-06-27 (via Atlassian Confluence MCP, `contentFormat=markdown`)
>
> TensileLite tuning 設定的權威內部指南(GlobalParameters /
> BenchmarkProblems / ForkParameters / LibraryLogic)、`MatrixInstruction` 的 9 元素
> 格式、solution 命名慣例,以及端到端的 tune → merge → rebuild → verify
> 工作流程。注意:文中的實作範例使用 **gfx1150 / WMMA (WavefrontSize 32)**;對於我們的
> 目標 **gfx942 / MFMA (wave 64)**,參數*概念*可沿用,但確切的 instruction
> shape、`WavefrontSize` 與 device ID 都不同。

---

## 1. 什麼是 TensileLite

TensileLite 是嵌入在 AMD [hipBLASLt](https://github.com/ROCm/rocm-libraries/tree/develop/projects/hipblaslt/tensilelite) 函式庫中的 GEMM kernel 產生與 benchmarking 引擎。它透過探索使用者定義的參數空間、在真實硬體上 benchmark 每個候選,並選出勝出者,來為矩陣乘法產生 GPU 專屬的 assembly kernels。在高層次上,它會:

1. 從組合式的參數 grid(YAML)**產生**數百/數千個候選 GEMM kernels。
2. 把每個候選**編譯**成 GPU assembly(過濾掉無效者,例如超出 register 上限的)。
3. 為每個問題 size(矩陣 shape)在目標 GPU 上**benchmark**每個有效的 kernel。
4. **產出**一份 CSV,列出每個 shape 的勝出 kernel + GFlops,並選擇性地產出一份可整合回 hipBLASLt 的 library-logic YAML。

### 1.1 輸入設定 YAML

三個主要區段:**GlobalParameters**、**BenchmarkProblems**(ProblemType +
ForkParameters + BenchmarkFinalParameters),以及一個選用的 **LibraryLogic** 區段。

附註解的範例:

```yaml
GlobalParameters:
  PerformanceMetric: DeviceEfficiency   # or CUEfficiency
  DataInitTypeAB: 3                      # 3 = trigsin/trigcos (good for validation)
  DataInitTypeC: 3
  DataInitTypeBeta: 0                    # init beta with zeros
  DataInitTypeAlpha: 1                   # init alpha with ones
  NumWarmups: 10
  NumBenchmarks: 1
  SleepPercent: 25                       # cool-down between benchmarks (% of solution time)
  EnqueuesPerSync: 20
  SyncsPerBenchmark: 1
  MaxEnqueuesPerSync: -1
  SkipSlowSolutionRatio: 0.50            # skip solutions slower than 50% of current best during warmup
  KernelTime: True                       # kernel-level timing (more accurate than wall-clock)
  NumElementsToValidate: -1              # -1 = all, 0 = none
  CSVExportWinner: True
  CSVMergeSameProblemID: True
  ValidationPrintValids: False
  PrintSolutionRejectionReason: False
  ClientLogLevel: 2                      # 0=Error 1=Terse 2=Verbose 3=Debug

BenchmarkProblems:
  - # GEMM HHS TN
    - # ProblemType
      OperationType: GEMM
      DataType: h            # FP16 input
      DestDataType: h        # FP16 output
      ComputeDataType: s     # FP32 accumulation
      HighPrecisionAccumulate: True
      TransposeA: 1          # TN layout
      TransposeB: 0
      UseBeta: True
      UseBias: 0
      BiasDataTypeList: ['h']
      BiasTypeArgs: ['h']
      UseScaleAlphaVec: 1
      Batched: True
      Activation: True
      ActivationFuncCall: True
      ActivationType: hipblaslt_all

    - # ForkParameters (the search space)
      BenchmarkCommonParameters:
        - KernelLanguage: ['Assembly']
      ForkParameters:
        - MatrixInstruction:
          - [16, 16, 16, 1, 1, 2, 2, 2, 2]
          - [16, 16, 16, 1, 1, 2, 5, 4, 1]
          - [16, 16, 16, 1, 1, 3, 3, 2, 2]
          - [16, 16, 16, 1, 1, 8, 1, 2, 2]
        - WavefrontSize: [32]
        - DepthU: [64, 128]
        - VectorWidthA: [1]
        - VectorWidthB: [1]
        - LocalReadVectorWidth: [16]
        - ScheduleIterAlg: [1, 3]
        - PrefetchGlobalRead: [0, 2]
        - PrefetchLocalRead: [0, 1]
        - ClusterLocalRead: [0]
        - ExpandPointerSwap: [0]
        - TransposeLDS: [1]
        - LdsBlockSizePerPadA: [-1]
        - LdsBlockSizePerPadB: [-1]
        - LdsPadA: [8, 16]
        - LdsPadB: [8]
        - 1LDSBuffer: [0, 1]
        - SourceSwap: [1]

      BenchmarkFinalParameters:
        - ProblemSizes:
          - Exact: [19456, 1322, 1, 2560]    # each Exact is [M, N, Batch, K]
          - Exact: [2560, 1322, 1, 9728]
          - Exact: [3584, 4096, 1, 18944]
          # ... (more shapes)
        - BiasTypeArgs: ['h']
        - ActivationArgs:
          - [Enum: none]
```

**各區段拆解:**

- **GlobalParameters** — 整體的 benchmarking 行為(data init、warmup/benchmark 迭代次數、sleep、validation 深度、輸出格式)。定義位於原始碼中:
  - [GlobalParameters.py](https://github.com/ROCm/rocm-libraries/blob/develop/projects/hipblaslt/tensilelite/Tensile/Common/GlobalParameters.py) — 預設值 + 說明。
  - [ValidParameters.py](https://github.com/ROCm/rocm-libraries/blob/develop/projects/hipblaslt/tensilelite/Tensile/Common/ValidParameters.py) — 每個參數的有效值列舉。

  常被 tune 的 GlobalParameters:

  | 參數 | 說明 | 範例值 |
  | --- | --- | --- |
  | `PerformanceMetric` | 最佳化目標 | `DeviceEfficiency`、`CUEfficiency` |
  | `NumWarmups` | 量測前的 warmup 迭代次數 | `0`、`10`、`50` |
  | `SleepPercent` | 每次執行之間的 cool-down(kernel 時間的百分比) | `0`、`25`、`50` |
  | `EnqueuesPerSync` | 每次 GPU sync 之間的 kernel 啟動次數 | `1`、`20`、`1000` |
  | `NumElementsToValidate` | 要 validate 的元素數(`-1` 全部,`0` 不驗證) | `-1`、`0` |
  | `SkipSlowSolutionRatio` | 跳過比目前最佳慢於此比例的 kernels | `0.0`、`0.5` |

- **BenchmarkProblems** — 設定的核心:
  - **ProblemType**:要 benchmark 的運算 — 資料型別(`DataType`、`DestDataType`、`ComputeDataType`)、layout(`TransposeA`、`TransposeB`)、bias/activation/batching。
  - **ForkParameters**:搜尋空間。TensileLite 會產生所有列出值的笛卡兒積,每個組合對應一個候選 kernel。關鍵參數:`MatrixInstruction`、`DepthU`、`WavefrontSize`、`PrefetchGlobalRead`、`PrefetchLocalRead`、`TransposeLDS`、`LdsPadA`/`LdsPadB`、`ScheduleIterAlg` 等。
  - **BenchmarkFinalParameters**:具體的 shape(`ProblemSizes`)。每個 `Exact` 條目為 `[M, N, Batch, K]`。

- **LibraryLogic**(選用) — 存在時會產生 `3_LibraryLogic/`(一份可整合進 hipBLASLt 的 YAML)。若沒有它,則只產生 benchmark CSV。它可以放在一份**獨立的** YAML 中,以將 kernel 探索(慢)與 library 產生(快)解耦:

```yaml
GlobalParameters:
  # (values here are not critical)
  PerformanceMetric: DeviceEfficiency
  NumElementsToValidate: -1
  # ...
LibraryLogic:
    ScheduleName: "gfx1150"
    ArchitectureName: "gfx1150"
    LibraryType: "Equality"
```

兩步驟工作流程(兩個指令使用**同一個 output dir**;步驟 2 讀取步驟 1 的資料):

```bash
# Step 1: generate kernels + benchmark -> 1_BenchmarkProblems/ and 2_BenchmarkData/
./run_tensile.sh <yaml_with_benchmark_problems> ./output
# Step 2: generate library logic from results -> 3_LibraryLogic/
./run_tensile.sh <yaml_with_library_logic> ./output
```

### 1.2 深入 MatrixInstruction

最關鍵的 tuning 旋鈕。9 元素格式:

```
[M, N, K, B, MIBlockM, WaveTileM, WaveTileN, WaveM, WaveN]
```

許多值由硬體 + 資料型別固定。範例(RDNA3.5、WMMA、HHS、TN):instruction
為 `[16,16,16,1]`,`MIBlockM=1`(B=1),`WavefrontSize=32`,所以只有最後四個是自由的:

- **WaveTileM (WTM, idx 5)** — 每個 wave 沿 M 方向重複多少個 WMMA/MFMA instruction;每個 instruction 產生一個 16×16 的 C tile,所以一個 wave 涵蓋 `16*WTM` 列。從 LDS 得到更多重用,但需要更多 VGPR。
- **WaveTileN (WTN, idx 6)** — 沿 N 方向同理;wave 涵蓋 `16*WTN` 行。
- 單一 wave 藉由執行 `WTM*WTN` 個 instruction,計算出一個 `(16*WTM) × (16*WTN)` 的 sub-tile。
- **WaveM (WM, idx 7)** / **WaveN (WN, idx 8)** — 一個 workgroup 內有多少 wave 沿 M / N 方向堆疊(它們共享 LDS)。一個 workgroup 有 `WaveM*WaveN` 個 wave = `WaveM*WaveN*WavefrontSize` 個 thread。

由此得到的階層:

```
Macro tile  (all waves in a workgroup)   (16*WTM*WM) x (16*WTN*WN)
   ^  x WaveM x WaveN
Wave tile   (all MIs one wave executes)  (16*WTM) x (16*WTN)
   ^  x WaveTileM x WaveTileN
MI tile     (one hardware instruction)   16 x 16
```

實作範例 `[16,16,16,1,1,1,16,4,1]` 套用於 shape `[37888,1541,1,3584]`:macro tile 64×256、
128 個 thread(4 個 wave × 32)、`WorkGroup [64,2,1]`、ThreadTile 8×16、每個 K-step 每個
workgroup 有 64 個 WMMA op;對整個 GEMM 進行 tiling ⇒ `ceil(37888/64)=592` × `ceil(1541/256)=7` ≈ 4144 個 workgroup。

### 1.3 Solution 命名慣例

每個產生的 kernel 都有一個確定性的名稱,編碼其完整設定,例如:

```
Cijk_Alik_Bljk_HHS_BH_HA_S_SAV_UserArgs_MT128x96x64_MI16x16x1_SN_..._MIWT2_6_..._WS32_WG64_2_1_WGM8_...
```

| 片段 | 意義 |
| --- | --- |
| `Cijk_Alik_Bljk` | Index 指派 C[i,j,k]、A[l,i,k]、B[l,j,k](TN layout) |
| `HHS` | 資料型別:Half 輸入、Half 輸出、Single (FP32) compute |
| `MT128x96x64` | Macro Tile 128 × 96,DepthU=64 |
| `MI16x16x1` | Matrix Instruction 16×16,1 block |
| `MIWT2_6` | WaveTileM=2、WaveTileN=6 |
| `WS32` | WavefrontSize=32 |
| `WG64_2_1` | WorkGroup=[64, 2, 1] |
| `PGR2` | PrefetchGlobalRead=2 |
| `PLR1` | PrefetchLocalRead=1 |
| `SIA1` | ScheduleIterAlg=1 |
| `DU64` | DepthU=64 |
| `ISA1150` | 目標 ISA gfx1150 |

這讓你能把任何勝出的 kernel 追溯回產生它的確切 YAML 參數。

## 2. 如何執行 TensileLite

- **2.1 先決條件** — 一個可運作的 TheRock build,並已 cherry-pick PR [#3390](https://github.com/ROCm/TheRock/pull/3390)(新增 `tensilelite-client` build target);在 TheRock 內 clone 了 `rocm-scripts` repo(提供 `run_on_board.sh`)。
- **2.2 同步到 board** — `./rocm-scripts/run_on_board.sh --board <name> --build-dir <dir> tensilelite-sync`(鎖定 board、rsync Tensile 套件、`rocisa` 與 `tensilelite-client`,並建立 `run_tensile.sh`/`setup_env.sh`)。
- **2.3 在 board 上執行** — SSH 進入;一次性執行 `python -m venv .venv` + `pip install -r requirements.txt` + `pip install rocm --index-url ...`;接著 `./run_tensile.sh /path/to/config.yaml ./output`。`run_tensile.sh` 會傳入 `--library-format=msgpack`(必須與產生的 `ClientParameters.ini` 中的 `library-file` 相符:`TensileLibrary.dat`=msgpack、`TensileLibrary.yaml`=yaml;msgpack 較快且為建議選項)。
- **2.4 輸出目錄** —
  - `1_BenchmarkProblems/` — 每個候選產生的 asm 原始碼、編譯後的 code objects 與 build artifacts。
  - `2_BenchmarkData/` — benchmark 結果;關鍵檔案是 `..._CSVWinner.csv`,其欄位描述 shape、標明 `WinnerGFlops/WinnerTimeUS/WinnerIdx/WinnerName`,再列出其餘每個候選的 GFlops(最快→最慢)。
  - `3_LibraryLogic/`(僅在有 `LibraryLogic` 時) — 要整合的最終 YAML。**後處理:**(1) 修正 `HA_S`→`HAS` 命名 bug;(2) 把 `- fallback` 替換為 `- [Device XXXX]`(例如 gfx1150 ⇒ `150e`;從你的架構既有的 solution 檔中複製該值)。

## 3. 如何解讀結果

- **3.1 終端機輸出** — 每個 (problem, solution, iteration) 一行 CSV:欄位包含 `run`、`problem-progress`(例如 `0/13`)、`solution-progress`(`0/151`)、`operation`、`problem-sizes` `(M,N,Batch,K)`、完整的 `solution` 名稱、`validation`(`PASSED`/`FAILED`/`NO_CHECK`)、`time-us`、`gflops`、`total-gran`、`tiles-per-cu`、`num-cus`、`temp-edge`(°C)等。讓你能即時發現失敗、低 GFlops 或 thermal throttling。
- **3.2 GPU 能力探測(預期內)** — 啟動時出錯的 `Testing instruction: ...` 行是**無害的**:TensileLite 探測 GPU 支援哪些 instruction,並排除失敗者。
- **3.3 Assembly 產生失敗(預期內)** — `Failed to generate assembly ... total vgpr: 291 not in [0, 256]` 等是**預期內的**:無效的參數組合(超出 VGPR/LDS 上限)會被靜默跳過;只有有效的存活者會被 benchmark。
- **3.4 極端值的 validation 失敗(已知問題)** — 在 `NumElementsToValidate: -1` 下,FP16 的飽和處理與 CPU 參考不同(`65504 != inf`、`-65504 != -inf`)。GPU 的結果(飽和到 ±65504,即 FP16 的最大值)**其實是正確的**;僅因此原因被標為 `FAILED` 的 solution 是安全的。

## 4. 如何整合新的結果

1. **4.1 Rsync 既有 library** 到遠端機器(例如 `.../Tensile/Logic/asm_full/gfx1150/Equality`)。
2. **4.2 Merge** 使用 `Tensile/bin/TensileMergeLibrary <existing_folder> <3_LibraryLogic_folder> <existing_folder>`(在套用 `HA_S`→`HAS` 與 `fallback`→`[Device XXXX]` 修正之後)。
3. **4.3 把 merge 後的 library rsync 回**到 build host。
4. **4.4 Rebuild** `ninja -C <build> hipBLASLt+expunge && ninja -C <build> hipBLASLt`(`+expunge` 會從更新後的 logic 強制乾淨地重新產生)。
5. **4.5 以 hipblaslt-bench 驗證** — 關鍵旗標:`--algo_method all`(列舉每個 solution,而非只有勝出者)、`--print_kernel_info`(印出 solution/kernel 名稱 — **至關重要**)、`--cold_iters 1 --iters 1`(只確認存在),外加對應某個已 tune shape 的 `-m/-n/-k/--transA/--transB`/型別旗標。在輸出的 `--Solution name:` 行中搜尋你在 `2_BenchmarkData` CSV 裡的 `WinnerName`;若存在,表示該 kernel 已被 merge 且可在執行期被選用。

## 附錄:有效 Tuning 的技巧

- **從小規模開始** — 一小組 `MatrixInstruction` 設定 + 少數幾個 shape;找到有潛力的區域後再擴大。
- **為求速度停用 validation** — 探索期間用 `NumElementsToValidate: 0`;只有在最終驗證時才用 `-1`。
- **依你的 K 調整 `DepthU`** — compute-bound / 大 K 用較大值(128、160);memory-bound / 小 K 用較小值(32、64)。
- **`TransposeLDS` 與 `LdsPadA`/`LdsPadB` 至關重要** — 它們控制 LDS bank conflict,影響很大。
- **`PrefetchGlobalRead` / `PrefetchLocalRead`** — 試試 0/1/2(注意 `PrefetchLocalRead: 2` 在某些設定下可能產生不正確的 kernels)。
- **`ScheduleIterAlg`** — 通常 `1` 與 `3` 最佳。SIA=0/1/2/3 各自在 codegen 端排出什麼、以及它怎麼與 PGR/PLR 一起驅動兩層排程器，見 [../hipblaslt/instruction-scheduling-and-latency.md](../hipblaslt/instruction-scheduling-and-latency.md)。
- **監控溫度** — 使用 `SleepPercent`(25–50)+ `NumWarmups`,以避免長時間執行時因 throttling 造成的偏差。

### People / contact(相關人員 / 聯絡人)

`KKyang`(Huang, YangWen)負責審查 Grid/Solutions 的 tuning 變更;可在 GEMM Optimization Teams 頻道上 ping 他。
