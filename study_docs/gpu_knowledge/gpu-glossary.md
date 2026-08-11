# GPU 硬體 / 軟體架構名詞速查字典

> 路徑說明：本檔在 `study_docs/gpu_knowledge/`。同資料夾文件用檔名；origami 用 `../origami/xxx.md`；頂層彙總用 `../glossary.md`。行號會漂移，以符號名稱為準。

## 白話總覽

GPU 的縮寫多、還常有「同一個東西不同名字」（SM=CU、warp=wavefront、shared memory=LDS、MALL=Infinity Cache=LLC），很容易搞混。這份文件就是**遇到看不懂的縮寫時來查的字典**：

- 每條只給**一句定義 + 對應別名（NVIDIA/AMD）+ 深入連結**——想深入就點連結去 [execution-model.md](execution-model.md) / [memory-hierarchy-and-chiplet.md](memory-hierarchy-and-chiplet.md) / [cdna5-gfx1250.md](cdna5-gfx1250.md)，本文**不重講**。
- 平台基準：本 repo 是 **MI300（gfx942 / CDNA3）**；數字若分架構，會標出 gfx942 vs gfx950(MI350) vs gfx1250(MI450)。

**和鄰近文件的分工**（別找錯地方）：

| 想找什麼 | 去哪 |
|---|---|
| GPU 硬體/軟體**名詞定義**（含 AMD-only：MALL/AGPR/XCD…） | **本檔** |
| CUDA↔HIP 完整 **API/函式對照**（cudaMalloc→hipMalloc…） | [cuda-hip-terminology.md](cuda-hip-terminology.md) |
| 跨專案彙總（含 GEMM/TensileLite/工具鏈/build 名詞） | [../glossary.md](../glossary.md) |
| 每個名詞**怎麼被效能模型使用** | [../origami/performance-modeling-concepts.md](../origami/performance-modeling-concepts.md) |

> 用法：先看下面「⚡ A-Z 縮寫速查」對到分類；還是混淆就看最後「⚠️ 最容易搞混的名詞群」。

---

## ⚡ A-Z 縮寫速查索引

> 「對應」欄放 NVIDIA 對照或常見別名。分類欄對到下方第幾類詳表。

| 縮寫 | 全名 | 中文一句 | 分類 | 對應 / 別名 |
|---|---|---|---|---|
| ACE | Asynchronous Compute Engine | 命令前端，讀 queue 派 workgroup（每 XCD 4 個） | ②硬體 | ≈ NVIDIA GigaThread 前端 |
| AGPR | Accumulator VGPR | MFMA 專用累加暫存器（gfx942 有、gfx1250 併入 VGPR） | ③暫存器 | — |
| AI | Arithmetic Intensity | 計算密度＝FLOPs/byte，決定 compute/memory-bound | ⑧建模 | — |
| CDNA | Compute DNA | AMD 資料中心 GPU 架構線（CDNA1–5） | ⑥架構 | ≈ NVIDIA 資料中心世代 |
| CU | Compute Unit | AMD 基本運算單元（gfx942：4×SIMD16） | ②硬體 | = NVIDIA SM |
| DPP | Data Parallel Primitives | wave 內跨 lane 洗牌 | ⑤ISA | ≈ warp shuffle |
| DepthU | Depth-U | 主迴圈一次處理的 K 深度 | ⑧建模 | — |
| GCD | Graphics Compute Die | CDNA2 的計算晶粒（MI200/250X） | ⑥架構 | — |
| GSU | GlobalSplitU | 跨 workgroup 切 K、經 global memory 合併 | ⑧建模 | ≈ split-K（跨 block） |
| HBM | High Bandwidth Memory | GPU 主記憶體（最大最慢） | ④記憶體 | = DRAM/VRAM |
| IOD | I/O Die | 放記憶體控制器 + MALL + 對外互連的晶粒 | ②硬體 | — |
| LDS | Local Data Share | workgroup 內共用的高速 scratchpad | ③/④ | = CUDA shared memory |
| LLC | Last-Level Cache | 末級快取（此處＝MALL） | ④記憶體 | = MALL/Infinity Cache |
| LSU | LocalSplitU | 同 workgroup 內多 wave 切 K、經 LDS 合併 | ⑧建模 | ≈ split-K（block 內） |
| MALL | Memory Attached Last Level | 末級快取，256MB、8 XCD 共用 | ④記憶體 | = Infinity Cache/LLC |
| MFMA | Matrix Fused Multiply-Add | gfx942 矩陣乘加指令族 | ②/⑤ | ≈ NVIDIA Tensor Core 指令 |
| MI | Matrix Instruction | 一條矩陣指令算的小塊 `(MI_M,MI_N,MI_K)` | ⑧建模 | — |
| MT | MacroTile | 一個 workgroup 負責的輸出區塊 | ⑧建模 | — |
| PC | Program Counter | 每 wave 一個的程式計數器 | ③暫存器 | — |
| PGR | PrefetchGlobalRead | 提前預取幾輪 global 資料 | ⑧建模 | ≈ software pipelining depth |
| RDNA | Radeon DNA | AMD 遊戲 GPU 架構線 | ⑥架構 | — |
| SALU | Scalar ALU | 純量運算 / 控制流（whole-wave 共用） | ②硬體 | — |
| SE | Shader Engine | 把 CU 分組的後端分群單元 | ②硬體 | ≈ NVIDIA GPC |
| SGPR | Scalar GPR | per-wave 共用的純量暫存器（gfx942：104） | ③暫存器 | — |
| SIMD | Single Instruction Multiple Data | 向量執行通道（gfx942：SIMD16×4/CU） | ②硬體 | ≈ NVIDIA SM sub-partition |
| SIMT | Single Instruction Multiple Threads | 一條指令、多 thread 同步執行的模型 | ①軟體 | NVIDIA 用語 |
| SM | Streaming Multiprocessor | NVIDIA 基本運算單元 | ②硬體 | = AMD CU/WGP |
| SPI | Shader Processor Input | workgroup 派工器（每 SE 一個） | ②硬體 | — |
| SQ | Sequencer | CU 內每 cycle 挑 ready wave 發指令 | ②硬體 | ≈ warp scheduler |
| StreamK | Stream-K | 動態把 K 切分給 CU、再 reduce 的排程法 | ⑧建模 | — |
| TDM | Tensor Data Mover | gfx1250 的非同步 tile 搬移 DMA 引擎 | ⑤ISA | ≈ NVIDIA TMA |
| UDNA | Unified DNA | CDNA+RDNA 收斂的統一 ISA 戰略 | ⑥架構 | — |
| VALU | Vector ALU | 逐 lane 向量算術（`v_add`/`v_fma`…） | ②硬體 | ≈ CUDA core 運算 |
| VGPR | Vector GPR | per-lane 向量暫存器（gfx942：256） | ③暫存器 | ≈ NVIDIA register |
| VMEM | Vector Memory | 走 global/buffer 的向量記憶體存取 | ⑤ISA | — |
| VOPD | Vector OP Dual | 一條指令打包兩個 32-bit 運算（雙發射） | ⑤ISA | — |
| WGM | WorkGroup Mapping | 重排 workgroup 以提高 L2 重用 | ⑧建模 | ≈ CTA swizzling |
| WGP | WorkGroup Processor | gfx1250 排程單位（＝2 CU 融合） | ②硬體 | = NVIDIA SM(概念) |
| WMMA | Wave Matrix Multiply-Accumulate | gfx1250 的矩陣乘加指令族（取代 MFMA） | ②/⑤ | ≈ NVIDIA `wmma` |
| XCD | Accelerated Compute Die | CDNA 計算晶粒（含 CU + 私有 L2） | ②/⑥ | — |
| XDL | (Matrix core datapath) | Matrix Core 的內部資料通道別名 | ②硬體 | — |
| wave/warp | wavefront / warp | 一次 lockstep 發射的一排 lane | ①軟體 | wavefront=AMD、warp=NVIDIA |
| lane | lane | wave 內單一 work-item 的通道 | ①軟體 | ≈ CUDA thread lane |
| vmcnt/lgkmcnt | wait counters | 等記憶體完成的計數器（gfx9） | ⑤ISA | — |
| WaveTile | Wave Tile | 單一 wave 負責的 tile（tile 三層中層） | ⑧建模 | — |
| MI tile | Matrix-Instruction tile | 一條 MI 算出的輸出塊（如 16×16，tile 三層最底） | ⑧建模 | — |
| GRVW | GlobalReadVectorWidth | 一次 global 讀幾個元素（A/B 載入粒度） | ⑧建模 | — |
| GWVWD | Global Write Vector Width (D) | 一次 store 幾個元素（輸出粒度） | ⑧建模 | — |
| VW | VectorWidth | 暫存器/LDS 運算的向量寬度 | ⑧建模 | — |
| NLC | NumLoadsCoalesced | 一輪合併幾筆 global load | ⑧建模 | — |
| DTV | DirectToVgpr | 直接載到 VGPR（略過 LDS） | ⑧建模 | — |
| DTL | DirectToLds | 直接載到 LDS | ⑧建模 | — |
| CUOccupancy | — | 一個 CU 上依序跑幾個 tile | ⑧建模 | — |
| MathClocksUnrolledLoop | — | 主迴圈每輪實測 cycle 數（rocIsa 量、回填給 Formocast） | ⑧建模 | — |
| transpose | transA/transB | 矩陣是否轉置 | ⑧建模 | 同名 |
| TN/NN/NT | — | A/B 轉置組合（T=轉置、N=不轉置） | ⑧建模 | — |
| swizzle | swizzle | 非標準的張量記憶體排列 | ⑧建模 | — |
| leading dimension | lda/ldb | 記憶體中換到下一行/列的跨步 | ⑧建模 | 詳見 ../glossary.md |
| batch_stride | batch stride | 跳到下一個 batch 矩陣的位址步長 | ⑧建模 | 詳見 ../glossary.md |
| shortCircuit | — | Origami 早期淘汰不合理 config 的規則 | ⑧建模 | — |
| XCC/XCCG | — | workgroup 對 XCD 的映射拓撲參數 | ⑧建模 | — |
| bpe | bytes per element | 每個元素幾 bytes（BF16=2、FP8=1…） | ⑨型別 | — |
| FP8/BF8 | 8-bit float | 低精度浮點（AMD gfx942 用 FNUZ 變體） | ⑨型別 | ≈ NVIDIA FP8 |
| FP6/FP4 | 6/4-bit float | 極低精度浮點（gfx950+，配微縮放） | ⑨型別 | — |
| MXFP | Micro-scaled FP (OCP MX) | 帶區塊縮放因子的低精度格式（gfx950+） | ⑨型別 | — |
| TF32 | TensorFloat-32 | 混精度格式（gfx950 改軟體模擬） | ⑨型別 | NVIDIA 用語 |
| FNUZ | — | AMD FP8/BF8 的編碼變體（無 inf/NaN 專用碼） | ⑨型別 | — |
| Dot2 | Dot2 | 特殊 MI（1×1×64），只適合極瘦問題 | ⑤ISA | — |
| miSIMD/shSIMD | matrix / shader SIMD | CU 內矩陣路徑（配 AGPR）vs 一般向量路徑 | ②硬體 | — |
| SRD | Scalar Resource Descriptor | buffer 描述子（含 num_records 等欄位） | ⑤ISA | — |
| VOP3PX2 | — | gfx1250 128-bit 編碼，可把兩指令融成一條 | ⑤ISA | — |
| WGP$ | WGP cache | gfx1250 統一的 LDS+cache（最多 320KB 當 LDS） | ③暫存器 | — |

---

## ① 軟體執行模型

深入：[execution-model.md](execution-model.md)、[kernel-launch.md](kernel-launch.md)

| 名詞 | 中文 / 一句定義 | 對應 / 別名 |
|---|---|---|
| kernel | 一次丟上 GPU 執行的函式 | 同名（CUDA/HIP） |
| grid | 一次 launch 的全部 workgroup | 同名 |
| block / workgroup | 會放在同一個 CU、能互相合作+同步的一群 thread | block=CUDA、workgroup=AMD |
| thread / work-item | 最小的邏輯執行單位 | thread=CUDA、work-item=AMD |
| warp / wavefront | 硬體一次發令的一排 lane；**CDNA=64、gfx1250=32** | warp=NVIDIA(32)、wavefront=AMD |
| lane | wave 內單一 work-item 的通道（邏輯單位，非一顆運算單元） | — |
| SIMT | 一條指令、多 thread 同步執行的模型 | NVIDIA 用語 |
| launch | CPU 透過 doorbell/command processor 把工作送上 GPU | 同名 |
| stream | 有序的命令佇列（FIFO）；default stream 有全域柵欄行為 | stream=CUDA、queue=HIP |
| occupancy | 一個 CU 上同時常駐幾個 wave（取 VGPR/LDS/wave slot 等上限的最小值） | 同名 |
| wave slot | 硬體可常駐一個 wave 的位置（gfx942：8/SIMD、gfx1250：16/SIMD32） | — |

## ② 硬體運算單元

深入：[execution-model.md](execution-model.md)、[memory-hierarchy-and-chiplet.md](memory-hierarchy-and-chiplet.md)、[cdna5-gfx1250.md](cdna5-gfx1250.md)

| 名詞 | 中文 / 一句定義 | 對應 / 別名 |
|---|---|---|
| SM | NVIDIA 基本運算單元 | = AMD CU/WGP |
| CU | AMD 基本運算單元；gfx942＝4×SIMD16 + 64KB LDS | = NVIDIA SM |
| WGP | gfx1250 排程單位，概念上＝**2 個 CU 融合**（4×SIMD32、統一 WGP$） | ≈ SM |
| SIMD | 向量執行通道；gfx942 為 SIMD16（邏輯 64 lane 跑 4 cycle） | ≈ SM sub-partition |
| VALU | 逐 lane 向量算術單元（`v_*`） | ≈ CUDA core |
| SALU | 純量運算 + 控制流單元（`s_*`，whole-wave 一個值） | — |
| Matrix Core | 做矩陣乘加的單元（發 MFMA/WMMA） | ≈ NVIDIA Tensor Core |
| XDL | Matrix Core 的對外名（＝ miSIMD 這條矩陣路徑） | — |
| miSIMD / shSIMD | CU 內兩條路徑：miSIMD 跑 MFMA（配 AGPR）、shSIMD 跑一般 VALU（配 VGPR） | — |
| Tensor Core | NVIDIA 的矩陣單元（與 Matrix Core 非 1:1 可比） | = AMD Matrix Core |
| CUDA core / Stream Processor | 單一向量運算 lane | CUDA core=NVIDIA、SP=AMD |
| XCD | CDNA 計算晶粒，含一群 CU + **私有 4MB L2**；MI300X 有 8 個 | — |
| SE (Shader Engine) | 把 CU 分成幾組的後端分群單元 | ≈ NVIDIA GPC |
| IOD | I/O 晶粒：記憶體控制器 + MALL + 對外互連 | — |
| ACE | 非同步命令前端，讀 queue 派工（每 XCD 4 個） | — |
| SPI | workgroup 派工器（每 SE 一個），檢查資源後把 workgroup 放進 CU | — |
| SQ (Sequencer) | CU 內每 cycle 從常駐 wave 挑 ready 的發指令 | ≈ warp scheduler |
| issue port | 「發射閘門」；共用 port ≠ 共用運算電路（見易混區） | — |

## ③ 暫存器與晶片內儲存

深入：[execution-model.md](execution-model.md)（「一個 lane 裡有什麼」）、[cdna5-gfx1250.md](cdna5-gfx1250.md)（AGPR）

| 名詞 | 中文 / 一句定義 | 對應 / 別名 |
|---|---|---|
| VGPR | **per-lane** 向量暫存器（gfx942：256 個；gfx1250：最多 1024） | ≈ NVIDIA register |
| SGPR | **per-wave** 共用的純量暫存器（gfx942：104 usable） | — |
| AGPR | MFMA 累加專用暫存器（gfx942/950：256）；**gfx1250 拿掉、併入統一 VGPR** | — |
| register file | 每 SIMD 私有的暫存器實體儲存（預先分給常駐 wave） | — |
| LDS | workgroup 內共用 scratchpad（gfx942：64KB/CU；gfx1250：WGP 統一最多 320KB） | = CUDA shared memory |
| WGP$ | gfx1250 把 LDS + cache 合成一塊統一儲存（最多 320KB 配為 LDS） | — |
| EXEC | 64-bit 執行遮罩（哪些 lane 這條有效） | — |
| VCC | 向量條件碼（每 lane 1 bit） | — |
| SCC | 純量條件碼（1 bit） | — |
| M0 | 記憶體描述暫存器（LDS/buffer op 用） | — |
| PC | 每 wave 的程式計數器 | — |

## ④ 記憶體階層

深入：[memory-hierarchy-and-chiplet.md](memory-hierarchy-and-chiplet.md)；cache line/coalescing/bank conflict 的建模用途見 [../origami/performance-modeling-concepts.md](../origami/performance-modeling-concepts.md)

| 名詞 | 中文 / 一句定義 | 對應 / 別名 |
|---|---|---|
| L1 | 每個 CU 私有的向量快取（硬體自動） | 同名 |
| L2 | **每個 XCD 私有** 4MB 快取（不跨 XCD 共用） | 同名 |
| MALL | 末級快取，256MB、8 XCD 共用，位在 IOD | = Infinity Cache/LLC |
| Infinity Cache | MALL 的行銷名 | = MALL/LLC |
| HBM | GPU 主記憶體（MI300X:192GB HBM3、MI350X:288GB HBM3E） | = DRAM/VRAM |
| cache line | cache 搬資料的最小單位（常見 64/128 bytes） | 同名 |
| bus width (per CU) | 每 CU 每 cycle 能從某層搬幾 bytes | 同名 |
| cache vs scratchpad | cache 硬體自動管（只能估命中率）；scratchpad(LDS) 程式手動管（用量確定） | — |
| coalescing | 相鄰 thread 讀連續位址時合併成少數大 transaction | 同名 |
| bank conflict | 多 thread 同拍打同一個 LDS bank 要排隊變慢（深入 [../isa/lds-bank-conflicts.md](../isa/lds-bank-conflicts.md)） | 同名 |
| arbitration efficiency | 多 CU 搶同層時實際能達到的頻寬占比（<100%） | 同名 |
| Infinity Fabric | 串接晶粒 chiplet 間、多 GPU 間的高速互連 | ≈ NVLink(概念) |

## ⑤ ISA / 指令層

深入：[cdna5-gfx1250.md](cdna5-gfx1250.md)（gfx9↔gfx12 差異）；gfx942 組語入門見 [../amd-isa-kernel.md](../amd-isa-kernel.md)

| 名詞 | 中文 / 一句定義 | 對應 / 別名 |
|---|---|---|
| MFMA | gfx942 矩陣乘加指令族（`v_mfma_*`） | ≈ Tensor Core 指令 |
| WMMA | gfx1250 矩陣乘加指令族（`v_wmma_*`，取代 MFMA） | ≈ NVIDIA `wmma` |
| VOPD | 一條指令打包兩個 32-bit 運算（雙發射） | — |
| VOP3PX2 | gfx1250 的 128-bit 編碼，可把兩條指令（如 LD_SCALE+WMMA）融成一條 | — |
| Dot2 | 特殊 MFMA 變體（MI=1×1×64），只適合極瘦（M<3）問題 | — |
| SRD / num_records | buffer 資源描述子（Scalar Resource Descriptor），含起址/長度 num_records 等欄位 | — |
| DPP / v_permlane | wave 內跨 lane 資料洗牌 | ≈ warp shuffle |
| ds_* | LDS 讀寫指令（`ds_read`/`ds_write`） | — |
| buffer_* / VMEM | global/buffer 記憶體讀寫 | — |
| wait counter | 等記憶體完成的計數器；**gfx9：vmcnt/lgkmcnt/expcnt** | — |
| loadcnt/storecnt/dscnt/kmcnt/tensorcnt | **gfx12** 把 wait counter 拆更細（load/store/LDS/scalar/TDM 各一） | — |
| s_barrier | workgroup 同步柵欄（gfx9：signal+wait 合一） | ≈ `__syncthreads()` |
| named barrier | gfx12 每 workgroup 16 個具名柵欄（signal/wait 分離） | — |
| cluster barrier | gfx12 跨 WGP 的 4 個柵欄 | — |
| issue port | 指令發射閘門（共用 port 會互擋） | — |
| dual-issue | 同拍發兩條（WMMA+VALU 並行 / 雙 VALU / VOPD） | — |
| TDM | gfx1250 非同步 tile 搬移 DMA 引擎（global↔LDS） | ≈ NVIDIA TMA |
| GFX9 / GFX10 / GFX12 | ISA 編碼世代；**GFX9↔GFX12 二進位零相容** | — |

## ⑥ 架構與產品命名

深入：[memory-hierarchy-and-chiplet.md](memory-hierarchy-and-chiplet.md)（世代表）、[cdna5-gfx1250.md](cdna5-gfx1250.md)

| 世代 | 產品（例） | gfx ISA | 備註 |
|---|---|---|---|
| CDNA1 | MI100 | gfx908 | monolithic（無 chiplet） |
| CDNA2 | MI200 / MI250X | gfx90a | GCD 晶粒；wave64 |
| CDNA3 | MI300X | **gfx942** | 8 XCD；**本 repo 平台** |
| CDNA4 | MI350X | gfx950 | 8 XCD；HBM3E |
| CDNA5 | MI450 | gfx1250 | WGP/wave32；GFX12 編碼 |
| RDNA | Radeon 遊戲卡 | gfx10/11/12 | 遊戲線；引入 WGP |
| — | Strix Point iGPU | gfx1150 | **無 MALL**（`NO_MALL_AVAILABLE`）、單 XCD |

其他：**chiplet/die**＝一小片矽晶（模組化封裝）；**monolithic**＝單一大晶片；**3D stacking**＝把 XCD 疊在 IOD 上；**UDNA**＝CDNA+RDNA 未來收斂的統一 ISA。

## ⑦ CUDA ↔ HIP ↔ AMD 跨廠對照（精簡）

> 只放最容易混的同義詞；**完整 API / 生態系對照表**見 [cuda-hip-terminology.md](cuda-hip-terminology.md)。

| NVIDIA / CUDA | AMD / HIP | 一句 |
|---|---|---|
| SM | CU / WGP | 基本運算單元 |
| warp（32） | wavefront（64；gfx1250 為 32） | 一次發令的一排 lane |
| CUDA core | Stream Processor / SIMD lane | 單一向量 lane |
| Tensor Core | Matrix Core（MFMA/WMMA） | 矩陣單元 |
| shared memory | LDS | block/workgroup 內 scratchpad |
| registers | VGPR / SGPR | 暫存器 |
| `__syncthreads()` | `__syncthreads()` / `s_barrier` | block 柵欄 |
| warp scheduler | wavefront scheduler / SQ | 挑 wave 發指令 |
| copy engine / DMA | SDMA | 資料搬移引擎 |

## ⑧ GEMM / 效能建模（GPU-arch 相鄰）

深入：[../origami/performance-modeling-concepts.md](../origami/performance-modeling-concepts.md)、[../origami/latency-model.md](../origami/latency-model.md)；GEMM 建構細節（solution/bpe/leading dimension…）見 [../glossary.md](../glossary.md)

| 名詞 | 中文 / 一句定義 |
|---|---|
| tile 三層：MacroTile → WaveTile → MI tile | **MacroTile(MT)**＝一個 workgroup 的輸出區塊；**WaveTile**＝其中單一 wave 負責的塊；**MI tile**＝一條矩陣指令算出的最底層塊（如 16×16） |
| MacroTile (MT) | tile 三層最上層：一個 workgroup 負責的輸出區塊 `(MT_M,MT_N,MT_K)` |
| WaveTile | tile 三層中層：MacroTile 內單一 wave 負責的塊 |
| MI tile | tile 三層最底層：一條 MI 指令算出的輸出塊（如 16×16） |
| MI (Matrix Instruction) | 一條矩陣指令本身，算一個小塊 `(MI_M,MI_N,MI_K)`（注意：指令 vs 上面「MI tile」是它的產出） |
| DepthU | 主迴圈一次處理的 K 深度 |
| GRVW (GlobalReadVectorWidth) | 一次 global read 讀幾個元素（A/B 載入粒度） |
| GWVWD (Global Write Vector Width) | 一次 store 寫幾個元素（輸出 D 的粒度；太窄效率差） |
| VW (VectorWidth) | 暫存器/LDS 運算的向量寬度 |
| NLC (NumLoadsCoalesced) | 一輪合併幾筆 global load |
| DTV (DirectToVgpr) / DTL (DirectToLds) | 載入直送 VGPR / 直送 LDS 的最佳化旗標 |
| CUOccupancy | 一個 CU 上依序跑幾個 tile（≥2 有排隊懲罰） |
| MathClocksUnrolledLoop | 主迴圈每輪的實測 cycle 數（rocIsa 逐指令量、回填給 Formocast） |
| waveNum / waveGroup | 一個 workgroup 幾個 wave / wave 在 M×N 的排法 |
| transpose (transA/transB) | 矩陣是否轉置；組合以 **TN / NN / NT** 表示（T=轉置、N=不轉置） |
| swizzle | 非標準的張量記憶體排列（swizzleTensorA/B） |
| leading dimension (lda/ldb) / batch_stride | 換行/列的跨步 / 跳到下個 batch 的步長（詳見 [../glossary.md](../glossary.md)） |
| shortCircuit | Origami 不用算完整模型就淘汰不合理 config 的早期規則（見 [../origami/latency-model.md](../origami/latency-model.md)） |
| XCC / XCCG | workgroup 對 XCD 的映射拓撲參數（影響 L2 命中模擬） |
| GSU (GlobalSplitU) | 跨 workgroup 切 K，部分和經 **global memory** 合併 |
| LSU (LocalSplitU) | 同 workgroup 內多 wave 切 K，部分和經 **LDS** 合併 |
| StreamK | 動態把 K 切分給 CU、再 reduce 的排程法 |
| WGM (WorkGroup Mapping) | 重排 workgroup 編號以提高 L2 重用 |
| staggerU | 讓不同 workgroup 從 K 不同位置起跑，避免搶同塊資料 |
| PGR (PrefetchGlobalRead) | 提前預取幾輪 global 資料（實現 compute/memory 重疊） |
| arithmetic intensity (AI) | FLOPs/byte，決定 compute-bound 或 memory-bound |
| roofline | 用 AI 判斷瓶頸落在算力還是頻寬的模型 |
| compute-bound / memory-bound | 瓶頸在算力 / 在搬資料 |
| latency hiding | 用 wave 切換把等待藏進運算（`max(compute,memory)` 的由來） |
| timestep / num_tiles | 所有 tile 分幾「波」跑（tile 數 ÷ CU 數） |
| prologue / epilogue | kernel 的開頭載入 / 結尾寫回固定成本 |

## ⑨ 資料型別（精度）

深入：世代支援哪些型別見 [../isa/amd-datacenter-gpu-isa.md](../isa/amd-datacenter-gpu-isa.md)；MFMA/WMMA 各型別見 [../isa/wmma-deep-dive.md](../isa/wmma-deep-dive.md)

| 型別 | 中文 / 一句定義 | 對應 / 別名 |
|---|---|---|
| FP32 / FP16 / BF16 | 32/16-bit 浮點；BF16＝指數同 FP32、尾數較短 | 同名 |
| INT8 | 8-bit 整數（量化推論常用） | 同名 |
| TF32 | 混精度格式（gfx942 有原生、gfx950 改軟體模擬） | NVIDIA 用語 |
| FP8 / BF8 | 8-bit 浮點兩種（E4M3/E5M2 概念）；**gfx942 用 AMD 的 FNUZ 變體** | ≈ NVIDIA FP8 |
| FNUZ | AMD 的 FP8/BF8 編碼變體（拿掉 inf/NaN 專用碼、多表示有限值） | — |
| FP6 / FP4 | 6/4-bit 極低精度浮點（gfx950+ 才有） | — |
| MXFP（OCP MX） | 帶「區塊縮放因子」的微縮放低精度格式（MXFP8/6/4，gfx950+） | Micro-scaling FP |
| bpe (bytes per element) | 每個元素幾 bytes（FP32=4、BF16/FP16=2、FP8=1…）；記憶體量算的基礎 | — |

---

## ⚠️ 最容易搞混的名詞群

逐組把最常混淆的釐清（層級 / 廠牌 / 世代不同）：

- **CU vs WGP vs SIMD vs lane**：
  - CU＝AMD 一個運算單元（gfx942）；**WGP**＝gfx1250 的單位，概念上＝2 個 CU 融合；**SIMD**＝CU/WGP 內的向量通道（gfx942 一 CU 有 4 個 SIMD16）；**lane**＝SIMD 內單一 work-item 的通道。層級：CU/WGP ⊃ SIMD ⊃ lane。
- **VGPR vs AGPR vs SGPR**：
  - **VGPR**＝per-lane 向量暫存器；**AGPR**＝MFMA 累加專用（gfx942 有、gfx1250 併回 VGPR）；**SGPR**＝per-wave 共用純量暫存器（整個 wave 一個值）。
- **LDS vs L1 vs shared memory**：
  - **LDS**＝程式手動管理的 scratchpad；**L1**＝硬體自動管理的 cache；兩者都在 CU 內但角色不同。**shared memory** 只是 LDS 的 CUDA 名字。
- **MALL vs L2 vs Infinity Cache vs LLC**：
  - **L2**＝每個 XCD 私有 4MB；**MALL**＝跨 8 XCD 共用的 256MB 末級快取，**Infinity Cache 與 LLC 都是 MALL 的別名**。順序：L1→L2→MALL→HBM。
- **GSU vs LSU vs StreamK**（三種切 K）：
  - **GSU**＝跨 workgroup 切 K、走 global memory 合併；**LSU**＝同 workgroup 內多 wave 切 K、走 LDS 合併；**StreamK**＝更動態的 K 切分排程（見 [../origami/performance-modeling-concepts.md](../origami/performance-modeling-concepts.md)）。
- **MFMA vs WMMA vs Tensor Core**：
  - **MFMA**＝gfx942 的矩陣指令；**WMMA**＝gfx1250 取代 MFMA 的新指令族；**Tensor Core**＝NVIDIA 對應物。gfx942 上 MFMA 會擋 VALU（共用 issue port）；gfx1250 的 WMMA 可與 VALU 並行。
- **warp vs wavefront vs wave32**：
  - **warp**＝NVIDIA（32）；**wavefront**＝AMD（CDNA 為 64）；**gfx1250** 改用 **wave32**（32）——所以看到「wave 大小」要先確認架構。
- **wait counter：gfx9 vs gfx12**：
  - gfx9 用粗的 `vmcnt/lgkmcnt/expcnt`（一個 counter 混多種操作）；gfx12 拆成 `loadcnt/storecnt/dscnt/kmcnt/tensorcnt` 更細，減少不必要的等待。
- **MacroTile vs WaveTile vs MI tile（tile 三層，最常被漏）**：
  - **MacroTile(MT)**＝一個 **workgroup** 負責的輸出區塊 → **WaveTile**＝其中單一 **wave** 負責的塊 → **MI tile**＝一條 **矩陣指令** 算出的最底層塊（如 16×16）。由大到小、層層包含。
- **MI（指令）vs MI tile（產出）**：
  - **MI**＝Matrix Instruction，指令本身 `(MI_M,MI_N,MI_K)`；**MI tile**＝這條指令算出來的那個輸出塊。一個是「動作」、一個是「結果」。
- **GRVW vs VW vs GWVWD（三種 vector width）**：
  - **GRVW**＝global **讀** 的向量寬（載 A/B）；**GWVWD**＝global **寫** 的向量寬（存 D）；**VW**＝暫存器/LDS 內部運算的向量寬。讀/寫/內部各一個，別混。
- **miSIMD vs shSIMD（CU 內兩條路）**：
  - **miSIMD**＝矩陣路徑（跑 MFMA、配 AGPR，對外叫 XDL/Matrix Core）；**shSIMD**＝一般向量路徑（跑 VALU、配一般 VGPR）。gfx942 上兩者共用發射 port（MFMA 會擋 VALU）。

---

## 交叉連結

- 執行模型/占用率深入 → [execution-model.md](execution-model.md)
- 記憶體階層/XCD/MALL 深入 → [memory-hierarchy-and-chiplet.md](memory-hierarchy-and-chiplet.md)
- CDNA5/gfx1250 微架構（WGP/WMMA/wait counter…）→ [cdna5-gfx1250.md](cdna5-gfx1250.md)
- kernel launch/stream → [kernel-launch.md](kernel-launch.md)
- CUDA↔HIP 完整 API 對照 → [cuda-hip-terminology.md](cuda-hip-terminology.md)
- 這些名詞怎麼被效能模型使用 → [../origami/performance-modeling-concepts.md](../origami/performance-modeling-concepts.md)
- 跨專案彙總（含 GEMM/工具鏈）→ [../glossary.md](../glossary.md)

## 一句話總結

> **這是 GPU 硬體/軟體架構名詞的速查字典：先用 A-Z 縮寫索引定位、看分類表的一句定義與 NVIDIA 對應、想深入再點連結；還是混淆就看「最容易搞混的名詞群」。** 完整 API 對照在 [cuda-hip-terminology.md](cuda-hip-terminology.md)、跨專案名詞在 [../glossary.md](../glossary.md)。
