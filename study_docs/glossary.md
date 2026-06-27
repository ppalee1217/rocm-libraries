# 名詞彙總 Glossary（跨文件）

> **狀態：outline，待擴充。** 目前各 study_docs 末尾都有自己的 Terminology 區；本文要把它們
> 彙整成單一查詢點。對應 roadmap：**P0 全程**（隨時查名詞）。

## 為何重要

名詞散在各文件，查一個詞要翻多檔。這份彙總把核心名詞集中一處，新名詞第一次出現時也統一在此定義。

## 硬體 / ISA（待逐條補定義）

仍待補；先以 [gpu_knowledge/](gpu_knowledge/) 與 [amd-isa-kernel.md](amd-isa-kernel.md) 為準
（內部文件無 ISA 實質內容，這兩段不從內部借力）。

- 硬體：wave / lane、VGPR / SGPR / AGPR、CU、XCD、LDS、HBM、L2、occupancy
- ISA：exec mask、`s_waitcnt`（vmcnt / lgkmcnt）、MFMA、buffer SRD / `num_records`、bank conflict

## GEMM / Tensile

> 以下定義 summary 自 [internal_docs/hipblaslt-tensilelite-reference.md](internal_docs/hipblaslt-tensilelite-reference.md)
> Module A/B/C 與 [internal_docs/tensilelite-kernel-generator.md](internal_docs/tensilelite-kernel-generator.md)。

- **GEMM** — 一般化矩陣乘法 `D = Activation(α·op(A)·op(B) + β·op(C) + bias)`。
- **hipBLASLt** — AMD 的 HIP GEMM library（對標 cuBLASLt），focus GEMM + epilogue fusion（bias/
  activation/scaling…）+ 混合精度；新架構上由它接手 rocBLAS 的 GEMM。
- **solution** — 一個完整 kernel 設定組合（macro tile、wave 大小、unroll、指令變體、LDS 用量、排程）。
- **solution index** — solution 在 library 中的編號；跨 build 漂移會打壞已存的 tuning 結果（穩定性是已知痛點）。
- **solution selection（兩層）** — 把 runtime 問題 `(M,N,B,K,型別,layout,epilogue)` 映射到 solution：
  ① **Equality** 查精確 M,N,K 命中就用；② 查不到走 **grid-based** 取最近代表點。grid 相對「逐尺寸窮舉
  調」平均效率差約 1–2%（最差 ~15%）。
- **StreamK / Origami / Formocast** — 疊在 equality+grid 之上的進階啟發式：StreamK 偏並行排程（需開 env）；
  Origami 用結構化搜尋；Formocast 用模擬式效能模型預測候選 kernel 表現。
- **MatrixInstruction** — 9 元素 `[M,N,K,B,MIBlockM,WaveTileM,WaveTileN,WaveM,WaveN]`，決定 tile 幾何。
- **MacroTile / WaveTile / MI tile** — 三層 tile：workgroup 級 / 單 wave 級 / 單硬體指令（16×16）級。
- **DepthU** — K 方向 unroll 深度（大 K 用大值，小 K 用小值）。
- **GlobalSplitU（GSU）/ LocalSplitU** — 把 K 切給多 workgroup / wave，輸出端需 reduction/atomic。
- **ProblemType vs Problem** — `ProblemType` 是問題「規格」（op/型別/transpose/bias…）；`Problem` 是一組
  具體 `[M,N,Batch,K]`。
- **epilogue** — GEMM 主乘累加後融合的尾段運算（bias、GELU/ReLU/Swish、scaling 等），會選到不同 solution family。
- **TensileLite** — hipBLASLt 內建的 GEMM kernel 產生器 + runtime library（由 Tensile 演進而來，現為主力）；
  build 時產 code object + solution logic，runtime 回應選擇查詢。
- **rocisa** — 以 C++ 程式化組裝 AMDGPU 指令的工具；`KernelWriter.py` 用它「寫組語」。
- **GEKO（GEMM Kernel Optimization）** — 上層 Python 套件，串接 TensileLite tuning、benchmark 分析、
  library 整合（GA / dense 搜尋）。
- **bench-driven swap** — kernel pool 夠用但 grid 選得不好時，直接在 grid 表換贏家、不重產 kernel。
- **characterization tests** — ~99 個 `.ambr` golden 檔覆蓋 ~29 個 codegen/config/solution 模組；改變
  行為的 PR 未同步更新對應 golden 會卡 required CI。
- **snippet architecture / StinkyTofu** — 把舊 14k 行 `KernelWriterAssembly` 巨石重構成可組合 snippet +
  pass-based IR 優化器（DAG 排程、waitcnt 插入、peephole）。
- **code object（`.co`）** — 編譯好的 GPU 機器碼檔。
- **選擇表（`.dat`，MessagePack）** — runtime 載入的二進位 solution library（`3_LibraryLogic` 的 YAML 是
  可讀中間產物）。
- **lazy load** — 用到某 size 才載對應 shard / `.co`，非一次全載。

## 系統（待逐條補定義）

- build-time vs runtime、heuristic、nearest-neighbor（部分已散見於 `hipblaslt/*.md`，待彙整）。

## 目前可先看的替代資源

- `study_docs/gpu_knowledge/`：GPU 通用名詞的**概念性解釋**來源（grid/block/warp/SM/CU、CUDA↔HIP 對照）
- 各 study_docs 檔末「Terminology」段（`README.md`、`hipblaslt/*.md`、`amd-isa-kernel.md`）
- 公司內部文件：[internal_docs/](internal_docs/)（GEMM/Tensile 名詞的權威來源）
