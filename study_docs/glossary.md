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

核心矩陣 / 暫存器名詞（完整見 [isa/mfma-deep-dive.md](isa/mfma-deep-dive.md)、[isa/wmma-deep-dive.md](isa/wmma-deep-dive.md)）：

- **MFMA（Matrix Fused-Multiply-Add）** — CDNA GPU 的矩陣乘加指令 `v_mfma_*`（`D = C + A×B`），gfx942 GEMM 的核心算力來源；變體表 / layout / latency 見 [isa/mfma-deep-dive.md](isa/mfma-deep-dive.md)。
- **WMMA（Wave Matrix Multiply-Accumulate）** — RDNA 與 CDNA5（gfx1250）用的矩陣指令 `v_wmma_*`，功能等同 MFMA 但累加器放 VGPR、wave32、可與 VALU 並行；**CDNA3/4 不用**，見 [isa/wmma-deep-dive.md](isa/wmma-deep-dive.md)。
- **Matrix Core**（miSIMD / XDL） — CU 內執行 MFMA/WMMA 的矩陣引擎；最小硬體原語是 4×1 × 1×4 外積（一次產生 16 個乘積）。
- **AGPR / AccVGPR（Accumulation VGPR）** — Matrix Core 專屬、獨立於一般 VGPR 的累加暫存器（gfx942/gfx950 各 256 個）；真實 GEMM 把累加器放這裡，epilogue 再 `v_accvgpr_read` 搬回 VGPR。CDNA5（gfx1250）起併入單一 VGPR 檔、不再有 AGPR。
- **XCD（Accelerator Complex Die）** — 裝 CU + L2 的加速器小晶粒（CDNA3 起），一顆 GPU 由多個 XCD 拼成；記憶體階層意義見下方與 [gpu_knowledge/memory-hierarchy-and-chiplet.md](gpu_knowledge/memory-hierarchy-and-chiplet.md)。

記憶體階層與晶粒組織（完整解釋見 [gpu_knowledge/memory-hierarchy-and-chiplet.md](gpu_knowledge/memory-hierarchy-and-chiplet.md)）：

- **XCD**（Accelerated Compute Die，加速運算晶粒）— AMD 把一顆 GPU 切成的小晶粒，每塊含一堆 CU + 一份私有 L2；CDNA3（MI300）引入，MI300/MI350 各有 8 個。L2 按 XCD 私有分割是 WGM / Origami L2 命中率估算的關鍵前提。
- **L2** — 每個 XCD 私有的快取（MI300 約 4 MB/XCD），**非全 GPU 統一**。
- **MALL / Infinity Cache / LLC** — Memory Attached Last-Level cache，夾在 L2 與 HBM 之間、8 個 XCD 共用的末級快取（MI300X/MI350X 為 **256 MB**），扮演 L2 的 victim cache；「Infinity」是 AMD 架構品牌命名，非指容量無限。
- **HBM / DRAM** — GPU 主記憶體（MI300X 192 GB HBM3 / MI350X 288 GB HBM3E），階層最外、最大最慢。
- **LDS / shared memory** — 每個 CU 一塊、block 內共用的 **scratchpad（程式手動管理）**；與 L2/MALL 這類「硬體自動管理的 cache」性質不同（cache 命中率只能估、scratchpad 用量算得準）。

## GEMM / Tensile

> 以下定義 summary 自 [internal_docs/hipblaslt-tensilelite-reference.md](internal_docs/hipblaslt-tensilelite-reference.md)
> Module A/B/C 與 [internal_docs/tensilelite-kernel-generator.md](internal_docs/tensilelite-kernel-generator.md)。

- **GEMM** — 一般化矩陣乘法 `D = Activation(α·op(A)·op(B) + β·op(C) + bias)`。
- **hipBLASLt** — AMD 的 HIP GEMM library（對標 cuBLASLt），focus GEMM + epilogue fusion（bias/
activation/scaling…）+ 混合精度；新架構上由它接手 rocBLAS 的 GEMM。
- **solution** — 一個完整 kernel 設定組合（macro tile、wave 大小、unroll、指令變體、LDS 用量、排程）。
- **solution index** — solution 在 library 中的編號；跨 build 漂移會打壞已存的 tuning 結果（穩定性是已知痛點）。
- **solution selection（兩層）** — 把 runtime 問題 `(M,N,B,K,型別,layout,epilogue)` 映射到 solution：  
  1. **Equality** 查精確 M,N,K 命中就用
  2. 查不到走 **grid-based** 取最近代表點。grid 相對「逐尺寸窮舉調」平均效率差約 1–2%（最差 ~15%）。
- **StreamK / Origami / Formocast** — 疊在 equality+grid 之上的進階啟發式：StreamK 偏並行排程（需開 env）；
Origami 用分析式延遲模型「不跑就估」挑最快 config；Formocast 用更精細的模擬式效能模型預測候選 kernel 表現
（內嵌於 Origami）。Origami 白話導讀見 [origami/README.md](origami/README.md)。
- **MatrixInstruction** — 9 元素 `[M,N,K,B,MIBlockM,WaveTileM,WaveTileN,WaveM,WaveN]`，決定 tile 幾何。
- **MacroTile / WaveTile / MI tile** — 三層 tile：workgroup 級 / 單 wave 級 / 單硬體指令（16×16）級。
- **DepthU** — K 方向 unroll 深度（大 K 用大值，小 K 用小值）。LDS 一次只放 DepthU 深的 K 切片，不是整條 K。
- **bpe（bytes per element）** — 每個元素的位元組數：FP32=4、FP16/BF16=2、FP8/BF8=1、FP4=0.5。用來把「元素數」換算成「byte 數」（如 `LDS ≈ DepthU × MacroTile × bpe`）；型別越小佔的 LDS/VGPR/頻寬越少。
- **GlobalSplitU（GSU）/ LocalSplitU** — 把 K 切給多 workgroup / wave，輸出端需 reduction/atomic。GSU 用於 M/N 太小、平面切不出足夠 workgroup（瘦長矩陣、K 很大）時，靠拆 K 產生更多平行塊鋪滿 CU。詳見 [hipblaslt/tensilelite-pipeline.md](hipblaslt/tensilelite-pipeline.md) 的 GSU Q&A。
- **ProblemType vs Problem** — `ProblemType` 是問題「規格」（op/型別/transpose/bias…）；`Problem` 是一組
具體 `[M,N,Batch,K]`。
- **epilogue** — GEMM 主乘累加後融合的尾段運算（bias、GELU/ReLU/Swish、scaling 等），會選到不同 solution family。它不是某種特殊模式，而是**任何 GEMM kernel 本來就有的尾段**：主迴圈在暫存器累加出純 `A*B` 後，epilogue 在把結果寫回 global memory「之前」順手做 `α·acc + β·C`、加 bias、套 activation、型別轉換，全程只花一趟記憶體來回（`β=0` 還會直接跳過讀舊 C）。深入白話推導見 [hipblaslt/gemm-optimization.md](hipblaslt/gemm-optimization.md) 的〈GEMM 公式語意〉。
- **alpha / beta** — GEMM 公式 `D = α·op(A)·op(B) + β·op(C)` 裡的兩個純量係數：`alpha` 縮放矩陣乘積 `op(A)*op(B)`，`beta` 縮放輸出位置原有的舊 `C`。常見特例：`beta=0` 完全忽略舊 C（純 `D=A*B`）、`beta=1` 把乘積累加到舊 C。它們讓「縮放後再累加到既有結果」一步完成（分塊 K 累加、迭代解法、量化反量化、EMA/momentum 都會用到），且通常摺進 epilogue 幾乎零成本。完整白話推導（為何迭代/tiling 需要、何時 ≠1、為何摺進 epilogue）見 [hipblaslt/gemm-optimization.md](hipblaslt/gemm-optimization.md) 的〈GEMM 公式語意〉。
- **leading dimension（`ld`）** — 矩陣在記憶體裡是攤平成「一條線」存的；`ld` 告訴 kernel「在這條線上，跨到下一欄（column-major）或下一列（row-major）要往前跳幾個元素」。它是決定記憶體佈局的「主導（leading）維度」，故名。用途是把**邏輯形狀**與**實體儲存排列**解耦：例如底層配置的是 5×5 buffer 但只想用左上角 3×3 邏輯矩陣時，`ld=5`（buffer 欄高）而非 3，讀第 j 欄第 i 列 = `base + j*ld + i`。最典型好處是**直接對大矩陣取子區塊（sub-matrix）運算而不必複製資料**。一句話：`ld` = 記憶體裡「跨一欄／一列要走幾格」的步長，通常 `ld ≥ 該維度的邏輯長度`。
- **batch_stride** — batched GEMM（一次呼叫算好幾個矩陣）裡，「從第 i 個矩陣起點跳到第 i+1 個矩陣起點要走幾個元素」的位址步長。例：每個 A 是 128×128=16384 個元素、8 個緊密相接，則 `batch_stride_A=16384`，讀第 i 個矩陣起點 = `base + i*batch_stride`。它管的是**怎麼找到資料（定址）**，不是**多快讀到資料**；只有當 stride 造成的存取樣式影響到記憶體區域性/對齊時，才會**間接**影響效能（副作用，非其用途）。
- **TensileLite** — hipBLASLt 內建的 GEMM kernel 產生器 + runtime library（由 Tensile 演進而來，現為主力）；
build 時產 code object + solution logic，runtime 回應選擇查詢。
- **rocisa** — 以 C++ 程式化組裝 AMDGPU 指令的工具（Nanobind 綁定給 Python）；`KernelWriter.py` 用它「寫組語」。一個 Python 物件 = 一條指令的積木，`Module` 串成 kernel 樹。專篇（是什麼/目錄結構/怎麼加指令/與 StinkyTofu 介面）見 [hipblaslt/rocisa.md](hipblaslt/rocisa.md)。
- **GEKO（GEMM Kernel Optimization）** — 上層 Python 套件，串接 TensileLite tuning、benchmark 分析、
library 整合（GA / dense 搜尋）。
- **bench-driven swap** — kernel pool 夠用但 grid 選得不好時，直接在 grid 表換贏家、不重產 kernel。
- **characterization tests** — ~99 個 `.ambr` golden 檔覆蓋 ~29 個 codegen/config/solution 模組；改變
行為的 PR 未同步更新對應 golden 會卡 required CI。
- **snippet architecture / StinkyTofu** — 把舊 14k 行 `KernelWriterAssembly` 巨石重構成可組合 snippet +
pass-based IR 優化器（DAG 排程、waitcnt 插入、peephole）。StinkyTofu 白話整理見
[stinkytofu/README.md](stinkytofu/README.md)。
- **code object（**`.co`**）** — 編譯好的 GPU 機器碼檔（AMDGPU ELF，含機器碼 + metadata），本身即可執行的 kernel 二進位；但 launch 前需先 `hipModuleLoad` 載入成 HIP module、解析出 kernel 符號才拿得到可呼叫 handle。
- **選擇表（**`.dat`**，MessagePack）** — runtime 載入的二進位 solution library（`3_LibraryLogic` 的 YAML 是
可讀中間產物）。
- **shard** — 選擇表 + solution metadata 太大時被切開的**子表分片**；另有 `..._Mapping.dat` 記錄「solution index → 在哪個 shard」，runtime 用到某 solution 才載對應 shard（lazy）。
- **lazy load** — 用到某 size 才載對應 shard / `.co`，非一次全載。
- **adapter（**`SolutionAdapter`**）** — HIP 層的執行代理：持有已載入的 code object module、維護「kernel 名 → `hipFunction_t`」對應、負責 `.co` 的 lazy 載入並最終發出 `hipModuleLaunchKernel`；每張 GPU 一個（per-device 單例）。是抽象 `KernelInvocation` 與底層 HIP driver 呼叫之間的橋。深入見 [hipblaslt/runtime-flow.md](hipblaslt/runtime-flow.md)。
- **rocblaslt_handle** — rocBLASLt 的 opaque 內部 context/session handle，承載 device id、stream、device properties 與對已載入 library / adapter 的存取；是對外 `hipblasLtHandle_t` 的內部對應物。
- **Predicate** — 條件樹（solution selection）裡一個回傳 true/false 的條件判斷函式，形式像 `predicate(problem, hardware) → 成立/不成立`（如「GPU 是不是 AMDGPU？」「dtype 是不是 fp16？」「A 有沒有轉置？」）。詳見 [hipblaslt/solution-selection.md](hipblaslt/solution-selection.md)。



## 系統（待逐條補定義）

- build-time vs runtime、heuristic、nearest-neighbor（部分已散見於 `hipblaslt/*.md`，待彙整）。



## 目前可先看的替代資源

- `study_docs/gpu_knowledge/`：GPU 通用名詞的**概念性解釋**來源（grid/block/warp/SM/CU、CUDA↔HIP 對照）
- 各 study_docs 檔末「Terminology」段（`README.md`、`hipblaslt/*.md`、`amd-isa-kernel.md`）
- 公司內部文件：[internal_docs/](internal_docs/)（GEMM/Tensile 名詞的權威來源）

