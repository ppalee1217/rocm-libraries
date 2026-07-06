# TensileLite 三階段：kernel 是怎麼產生與挑選的

路徑說明：本檔在 repo 內的 `study_docs/hipblaslt/`，code 連結為相對路徑（`../../projects/...`，先回到 repo root 再進 `projects/`）。行號可能隨 commit 漂移，對不上時以符號名稱為準。建議先讀 [runtime-flow.md](runtime-flow.md)。

**權威內部來源**：

- tune→merge→rebuild→verify 完整流程與輸出目錄（`1_`~`3_`）見 [internal_docs/tensilelite-kernel-generator.md](../internal_docs/tensilelite-kernel-generator.md)。
- 架構脈絡見 [internal_docs/hipblaslt-tensilelite-reference.md](../internal_docs/hipblaslt-tensilelite-reference.md) Module C.2。

## 白話總覽

[runtime-flow.md](runtime-flow.md) 講的是「執行時查表選 kernel」。那張表和那些 kernel，是 TensileLite
在**建置時**做出來的。TensileLite 做三件事，像出一本食譜：

1. **BenchmarkProblems（試做與試吃）** — 依 YAML 設定產生大量候選 kernel，編譯、在真實 GPU 上 benchmark。
2. **LibraryLogic（寫食譜）** — 分析 benchmark 數據，挑出「哪種矩陣大小該用哪個 kernel」。
3. **ClientWriter（裝訂出版）** — 把選出的 kernel 包成可用的 library 與 benchmark client。

> 名詞：**tuning** = 試很多種 kernel 設定、比較效能、挑最快的過程。



## 架構 / 流程圖

```mermaid
flowchart LR
    cfg["config.yaml (tuning 設定)"] --> p1["1_BenchmarkProblems：候選 kernel 原始碼/.co + 各步 CSV"]
    p1 --> p2["2_BenchmarkData：彙整後的效能 csv/yaml"]
    p2 --> p3["3_LibraryLogic：選擇邏輯 (哪個 size 配哪個 solution)"]
    p3 --> p4["4_LibraryClient：可出貨的 library + client"]
```





## 逐步 trace



### 入口

命令列入口 `Tensile/bin/Tensile` 呼叫 `Tensile()`，再由 `executeStepsInConfig()` 依 config 內容依序觸發三階段。它會檢查 `config` 裡有沒有 `BenchmarkProblems` / `LibraryLogic` / `LibraryClient` 這三個 key，有哪個就跑哪個，並把「用什麼工具鏈編、輸出到哪、目標是哪張 GPU」這些共用資訊一路往下傳。

- 頂層驅動：[Tensile()](../../projects/hipblaslt/tensilelite/Tensile/Tensile.py#L478)
- 三階段分派：[executeStepsInConfig()](../../projects/hipblaslt/tensilelite/Tensile/Tensile.py#L71)

`executeStepsInConfig()` 的主要參數（三階段共用的「環境與設定」）：


| 參數                              | 型別 / 來源                                 | 功能（白話）                                                                   |
| ------------------------------- | --------------------------------------- | ------------------------------------------------------------------------ |
| `config`                        | `dict`                                  | 解析後的 tuning YAML；用它的 key 決定要跑哪幾個階段。                                      |
| `outputPath`                    | `Path`                                  | 最上層輸出目錄；三階段的 `1_`~ `4_` 子目錄都建在這底下。                                       |
| `asmToolchain` / `srcToolchain` | `AssemblyToolchain` / `SourceToolchain` | 組譯 / 編譯 kernel 用的工具鏈（assembler、compiler 路徑等）。                            |
| `cCompiler`                     | `str`                                   | 編 client / helper 用的 C 編譯器。                                              |
| `isaInfoMap`                    | `Dict[str, IsaInfo]`                    | 目標 GPU 架構資訊（gfx 版本、硬體能力）；決定 `.co` 是給哪個 arch。                             |
| `debugConfig`                   | `DebugConfig`                           | 除錯開關（`splitGSU`、印出 solution 被拒原因等）。                                      |
| `deviceId`                      | `int`                                   | benchmark 要用哪張實體 GPU。                                                    |
| `probSolDict`                   | `dict`                                  | problem→solution 的對照資料，往下傳給各階段。                                          |
| `buildOnly`                     | `bool`                                  | 只「產生 + 編譯」kernel，跳過 benchmark 與後兩階段（LibraryLogic / LibraryClient）。       |
| `solutionPoolFiles`             | `list`                                  | 若非空，改用既有的 library logic YAML 當 solution 來源，而不是從 `ForkParameters` 重新展開生成。 |




### 階段 1：BenchmarkProblems（產生 + 編譯 + benchmark）

依 YAML 把參數「fork」成很多組合，每組變成一個候選 kernel，編譯成 `.co`，再跑 benchmark 量速度。

- 入口：[BenchmarkProblems.main()](../../projects/hipblaslt/tensilelite/Tensile/BenchmarkProblems.py#L818)
- 單一 problem-type 的 generate→build→benchmark 迴圈：[_benchmarkProblemType()](../../projects/hipblaslt/tensilelite/Tensile/BenchmarkProblems.py#L557)

> 名詞：**fork** = 把一個參數的多個可能值展開成多組設定（例如 tile 試 64/128/256），形成多個候選 kernel。

`BenchmarkProblems.main()` 除了沿用入口傳下來的工具鏈/裝置資訊外，關鍵是這幾個：


| 參數                            | 型別 / 來源 | 功能（白話）                                                                          |
| ----------------------------- | ------- | ------------------------------------------------------------------------------- |
| `config`                      | `dict`  | YAML 的 `BenchmarkProblems` 段：列出要試哪些 problem type、要 fork 哪些參數、benchmark 哪些 size。 |
| `useCache`                    | `bool`  | 若之前編過且參數沒變，直接重用快取的 `.co`，跳過重新編譯。                                                |
| `outputPath` / `buildTmpPath` | `Path`  | 分別是最終輸出目錄與編譯暫存目錄。                                                               |
| `gfxName`                     | `str`   | 目標 GPU 架構名（如 `gfx942`），決定 `.co` 編給哪個 arch。                                      |
| `probSolMap`                  | `dict`  | problem→solution 對照資料。                                                          |
| `buildOnly`                   | `bool`  | 只產生+編譯、跳過 benchmark。                                                            |
| `solutionPoolFiles`           | `list`  | 非空時改從既有 library logic 載入 solution，不從 `ForkParameters` 生成。                       |


`main()` 對每個 problem type 呼叫 `_benchmarkProblemType()`，帶入 `problemTypeConfig`（這批要算的問題型別：型別、轉置、index 配置）與 `problemSizeGroupConfig`（含 `ForkParameters` 與要 benchmark 的 size 清單）。它內部把一個 benchmark step 拆成 **generate → build → benchmark** 三小步，各自呼叫的 API 與傳入內容如下：


| 小步        | 主要 API（args）                                                                                                                                                                                                                                                                       | 這一步在做什麼                                                                                                                                                              |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| generate  | `[constructForkPermutations(forkParams, paramGroups)](../../projects/hipblaslt/tensilelite/Tensile/BenchmarkStructs.py#L336)`                                                                                                                                                      | 把 `forkParams`（每個參數的多個候選值）展開成所有組合，每個組合就是一個候選 kernel 設定。                                                                                                              |
| generate  | `[_generateForkedSolutions(problemType, constantParams, forkPermutations, assembler, debugConfig, isaInfoMap)](../../projects/hipblaslt/tensilelite/Tensile/BenchmarkProblems.py#L241)`                                                                                            | 把上面的組合 + `constantParams`（所有候選共用的固定參數）組成一批 solution 物件；無效組合會在這裡被剔除。                                                                                                  |
| build     | `[writeBenchmarkFiles(stepBaseDir, solutions, problemSizes, biasTypeArgs, factorDimArgs, activationArgs, icacheFlushArgs, …, asmToolchain, srcToolchain, sourcePath, …, gfxName, isaInfoMap, probSolMap)](../../projects/hipblaslt/tensilelite/Tensile/BenchmarkProblems.py#L414)` | 把每個 solution 產出 kernel source（呼叫 KernelWriter）並編成 `.co`，同時寫出這一步 benchmark client 需要的檔案。`problemSizes` 是要測的 size；`biasTypeArgs / activationArgs` 等是要一起掃的 epilogue 變體。 |
| benchmark | `[runClient(libraryLogicPath, forBenchmark, enableTileSelection, cxxCompiler, cCompiler, outputPath, configPaths)](../../projects/hipblaslt/tensilelite/Tensile/ClientWriter.py#L231)`                                                                                             | 用上一步編好的 `.co` 在 `deviceId` 指定的 GPU 上實跑，量每個候選在每個 size 的速度，輸出成 CSV。`configPaths` 指向剛寫好的 `ClientParameters.ini`。                                                        |


> 名詞：**constantParams** = 所有候選共用、不參與 fork 的固定參數；**forkParams** = 會展開成多組候選的參數。



### 階段 2：LibraryLogic（挑每個 size 的最佳解）

讀 `2_BenchmarkData/` 的效能數據，對每種矩陣大小挑最快的 solution，寫成一棵「選擇邏輯」輸出到 `3_LibraryLogic/`。

- 入口：[LibraryLogic.main()](../../projects/hipblaslt/tensilelite/Tensile/LibraryLogic.py#L1591)
- 主流程：[generateLogic()](../../projects/hipblaslt/tensilelite/Tensile/LibraryLogic.py#L1427)
- 單一 problem-type 分析：[analyzeProblemType()](../../projects/hipblaslt/tensilelite/Tensile/LibraryLogic.py#L48)

> 這一步產出的 YAML，就是 runtime 在 [runtime-flow.md](runtime-flow.md) 關卡 4 讀進去查表用的東西。

`main()` 幾乎原樣把參數轉給 `generateLogic()`，兩者的關鍵參數是「讀哪、寫哪、怎麼分析」：


| 參數                             | 型別 / 來源              | 功能（白話）                                                                           |
| ------------------------------ | -------------------- | -------------------------------------------------------------------------------- |
| `config`                       | `dict`               | YAML 的 `LibraryLogic` 段：分析參數（如 `SolutionImportanceMin`＝一個 solution 至少要贏多少比例才留下）。 |
| `benchmarkDataPath`            | `Path`               | 讀入的來源：階段 1 彙整出的 `2_BenchmarkData/`（`*.csv` 效能 + `*.yaml` solution 清單）。           |
| `libraryLogicPath`             | `Path`               | 輸出目的地：`3_LibraryLogic/`，寫出選擇邏輯 YAML。                                             |
| `cxxCompiler`                  | `str`                | 重建/驗證 solution 時要用的 C++ 編譯器。                                                     |
| `splitGSU`                     | `bool`               | 是否把 GSU（Global Split-U）拆開處理，影響 solution 命名與分析。                                   |
| `printSolutionRejectionReason` | `bool`               | 印出某個 solution 為何被淘汰，方便除錯。                                                        |
| `printIndexAssignmentInfo`     | `bool`               | 印出張量 index（free/batch/bound）的配置資訊。                                               |
| `isaInfoMap`                   | `Dict[str, IsaInfo]` | 目標 arch 資訊。                                                                      |


`generateLogic()` 掃 `2_BenchmarkData/` 底下每個 problem type 的 `.csv`/`.yaml`，再對每個 type 呼叫 `analyzeProblemType()` 做真正的「挑贏家」：


| 參數                  | 型別 / 來源 | 功能（白話）                                                                                                                      |
| ------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------- |
| `problemType`       | `dict`  | 這批要分析的問題型別（型別、轉置、`TileAwareSelection` 等）。                                                                                   |
| `problemSizeGroups` | `list`  | 每個 entry 是 `(problemSizes, dataFileName, solutionsFileName, [selectionFileName], solutions)`：測過的 size、對應效能檔、候選 solution 清單。 |
| `inputParameters`   | `dict`  | 分析參數（由 `config` 補上預設值而來）。                                                                                                   |
| `libraryLogicPath`  | `Path`  | 輸出目錄。                                                                                                                       |
| `splitGSU`          | `bool`  | 同上，影響 solution 命名。                                                                                                          |


它會建一個 `LogicAnalyzer`，比對「每個 size 上哪個 solution 最快」，最後輸出成 runtime 查表用的選擇邏輯樹。

### 階段 3：ClientWriter（打包成 library / client）

讀 `3_LibraryLogic/` 的選擇邏輯，重建 solutions、編出最終 library（`.co` + 索引），並產生 benchmark client。

- 入口：[ClientWriter.main()](../../projects/hipblaslt/tensilelite/Tensile/ClientWriter.py#L92)

`ClientWriter.main()` 的參數：


| 參數           | 型別 / 來源     | 功能（白話）                                                                                                 |
| ------------ | ----------- | ------------------------------------------------------------------------------------------------------ |
| `config`     | `dict`      | YAML 的 `LibraryClient` 段：`ActivationArgs`（要支援哪些 activation）、`FactorDimArgs`、`ICacheFlush` 等 client 選項。 |
| `assembler`  | `Assembler` | 重建 solution 時組譯 kernel 用。                                                                              |
| `cCompiler`  | `str`       | 編 client 程式用的 C 編譯器。                                                                                   |
| `isaInfoMap` | —           | 目標 arch 資訊；決定要 union 哪些 arch 的 `.co`/yaml。                                                             |
| `outputPath` | `Path`      | 讀 `3_LibraryLogic/`、寫 `4_LibraryClient/` 的根目錄。                                                         |
| `deviceId`   | `int`       | client 預設在哪張 GPU 上跑。                                                                                   |
| `gfxName`    | `str`       | 目標 GPU 架構名。                                                                                            |


它讀 `3_LibraryLogic/` 的每個 logic YAML（`parseLibraryLogicFile`），rebuild 出被選中的 solution，編出最終 library 的 `.co` + 索引，放到 `4_LibraryClient/`，並產生可直接跑的 benchmark client。

### kernel 組合語言怎麼吐出來：KernelWriter + rocisa

候選 kernel 的 GPU 組合語言由 [KernelWriter.py](../../projects/hipblaslt/tensilelite/Tensile/KernelWriter.py) 產生，它呼叫 C++ 模組 [rocisa](../../projects/hipblaslt/tensilelite/rocisa)（Nanobind 綁定）逐條產生指令。
一開始不用全懂，先記住入口。這條路是階段 1 build 小步（`writeBenchmarkFiles`）內部呼叫的：每個 solution 都會走一次，把抽象的 solution 參數變成一支 kernel 的原始碼。

- kernel 主體建構：[kernelBody()](../../projects/hipblaslt/tensilelite/Tensile/KernelWriter.py#L5279)
- 產生 source 的入口：[_getKernelSource()](../../projects/hipblaslt/tensilelite/Tensile/KernelWriter.py#L10602)

`_getKernelSource(kernel)` 是外部入口，內部再把張量參數備好後轉呼叫 `kernelBody(kernel, tensorParametersA, tensorParametersB)`：


| 參數                                        | 型別 / 來源               | 功能（白話）                                                                           |
| ----------------------------------------- | --------------------- | -------------------------------------------------------------------------------- |
| `kernel`                                  | `Solution`（dict-like） | 一組 solution 參數（tile 大小、`ExpandPointerSwap`、`UseSubtileImpl` 等）；決定要吐出哪支 kernel。   |
| `tensorParametersA` / `tensorParametersB` | `dict`                | A / B 張量的排列/型別/是否 sparse 等資訊，由 `_initKernel()` 依 `kernel` 算出，供產生 load/store 指令用。 |


`_getKernelSource()` 回傳這支 kernel 的組合語言字串；出錯時除非開了 `forceGenerateKernel` 否則會 raise。`kernelBody()` 則是實際一段段組出函式簽章、資源配置與主迴圈的地方。

名詞：

- **rocisa** = 專門「組裝 AMDGPU 指令」的 C++ 工具庫。
- [KernelWriter.py](../../projects/hipblaslt/tensilelite/Tensile/KernelWriter.py) 像在用 rocisa 寫組合語言。

想深入 `kernelBody()` 的組裝骨架、兩層排程，以及 `KernelWriter.py`（排程/骨架）與 `KernelWriterAssembly.py`（逐條發指令）的分工：見 [kernelwriter-implementation.md](kernelwriter-implementation.md)。

## 一次 build 涵蓋什麼？候選 vs 出貨、size 範圍、何時要重跑

這節回答三個常見但文件易略過的疑問：build 出來的 `.co` 是不是一大堆、有限的 kernel 怎麼涵蓋無限大的矩陣、以及什麼時候需要重跑。

### 候選 `.co` 很多，但「出貨」的只留贏家

「一大堆 `.co`」其實分兩種，數量天差地別，別混在一起：

- **候選（大量、暫時）**：階段 1 把參數 fork 成很多組合，每組編成一個候選 `.co` 拿去 benchmark；大多數最後都用不到。它們是 `1_BenchmarkProblems/` 裡的**離線中間產物**，benchmark 完即可清掉。
- **出貨（精簡、被 runtime 用）**：階段 2 對每個 size 只挑最快的 solution，階段 3 只把**被選中的** solution 打包進最終 library。所以出貨那批 `.co` 是挑選後的集合，不是全部候選。



### 有限的 kernel 如何涵蓋無限大的 problem size

關鍵設計是把「能不能算」和「算得快不快」拆開：

- **kernel 對 size 通用**：solution 用 **tiling**（把輸出切成固定大小的 tile 分塊掃過）寫成，同一個 `.co` 算 `512×512` 或 `8192×8192` 只是 tile 數不同。能不能用由 kernel 的 predicate / assertion（如「K 要是某數的倍數」「需要多少 workspace」）決定，**不是 size 上限**。
- **tuning 只挑代表性 size**：要 benchmark 哪些 size 是在 tuning config（YAML）裡**人工列出**的有限清單，通常對齊真實負載（例如常見的 LLM GEMM shape），不窮舉。測得越廣，對那些 size 越準。
- **沒測過的 size 用最近鄰補**：runtime 對沒 tune 過的 M/N/K，用距離函數找「最接近的 benchmark 點」，套用那個點的贏家。見 [ProblemMatchingLibrary](../../projects/hipblaslt/tensilelite/include/Tensile/MatchingLibrary.hpp#L44-L47)（"find the benchmarked size that is closest to the size asked for"）與 [ProblemFreeSizeLibrary](../../projects/hipblaslt/tensilelite/include/Tensile/FreeSizeLibrary.hpp#L46-L49)。

> 名詞：**tiling** = 把大矩陣切成固定大小的小塊（tile），kernel 用迴圈逐塊計算，因此同一支 kernel 不綁定特定矩陣大小。

結論：size 可以無限大但 `.co` 數量有限——代價只是離 tuning 點越遠的 size，選到的 kernel 可能不是絕對最佳，而**不是算不出來**。

### 什麼時候要重跑 build、什麼時候不用

- **不用重跑**：使用既有 kernel，包含「為不同矩陣大小換用不同 kernel」。runtime 只是查表 + lazy load，**全程不編譯**，同一份 build 產物可重複用無數次。
- **需要重跑 TensileLite**：
  - 換 GPU 架構（`.co` 是 per-arch，例如 `gfx942` 的檔不能給別的架構用）。
  - 想要目前沒有的新調校點或新功能（為某個 shape 追求更快、支援新型別/epilogue）→ 改 config 重跑三階段。
  - 改了 kernel 產生邏輯或參數（[KernelWriter.py](../../projects/hipblaslt/tensilelite/Tensile/KernelWriter.py)、[rocisa](../../projects/hipblaslt/tensilelite/rocisa)、tile 設定）→ 重跑才會反映到新的 `.co`。



## 關鍵資料結構 / 輸出目錄


| 目錄                     | 內容（白話）                                   | 定義                                                                                   |
| ---------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------ |
| `1_BenchmarkProblems/` | 候選 kernel 原始碼、`.co`、各步 CSV               | [Constants.py](../../projects/hipblaslt/tensilelite/Tensile/Common/Constants.py#L13) |
| `2_BenchmarkData/`     | 彙整後效能 `*.csv` / `*.yaml`（給 LibraryLogic） | [Constants.py](../../projects/hipblaslt/tensilelite/Tensile/Common/Constants.py#L13) |
| `3_LibraryLogic/`      | 選擇邏輯 YAML（哪個 size 配哪個 solution）          | [Constants.py](../../projects/hipblaslt/tensilelite/Tensile/Common/Constants.py#L15) |
| `4_LibraryClient/`     | 最終 library `.co`、client                  | [Constants.py](../../projects/hipblaslt/tensilelite/Tensile/Common/Constants.py#L15) |




## 如何建置 / 執行以觀察此流程

```bash
cd /data1/perlee/rocm-libraries/projects/hipblaslt/tensilelite
pip3 install invoke
invoke rocisa          # 安裝 rocisa Python 模組（首次或改 rocisa 後）
invoke build-client    # 編出 tensilelite-client

# 跑一個 config，輸出到 out/（會依序產生 1_~4_ 目錄）
Tensile/bin/Tensile <config.yaml> out/
```

可拆兩步：先 `--build-only`（只產生+編譯），再 `--use-cache`（跑 benchmark + 後續階段）。範例 config 見
[Tensile/Tests/](../../projects/hipblaslt/tensilelite/Tensile/Tests/)。

## Terminology

- `tuning` - 試多種 kernel 設定、比較效能、挑最快的過程。
- `fork` - 把參數的多個值展開成多組候選設定。
- [rocisa](../../projects/hipblaslt/tensilelite/rocisa) - 組裝 AMDGPU 指令的 C++ 工具庫。
- `library logic` - 「哪種 size 配哪個 solution」的選擇邏輯（YAML/MsgPack）。



## 交叉連結

- 上一層全局：[README.md](README.md)
- 這些產物在執行期怎麼被用：[runtime-flow.md](runtime-flow.md)
- 想動手改 kernel / 調參數：[gemm-optimization.md](gemm-optimization.md)
- build / PR 規範見官方 [tensilelite/AGENTS.md](../../projects/hipblaslt/tensilelite/AGENTS.md)（本文件不重複）。



## 一句話總結

> 三階段 = 試做 + 評分 + 出版食譜。最終的 `.co` 與選擇邏輯，就是 runtime 拿來查表用的。
> 想動手最佳化，下一篇 [gemm-optimization.md](gemm-optimization.md)。

