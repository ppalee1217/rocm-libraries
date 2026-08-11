# Formocast 延遲模型：它怎麼「模擬」出一個 microSeconds

路徑說明：本檔在 `study_docs/origami/formocast/`。原始碼連結用 `../../../shared/...`。行號會漂移，以符號名稱為準。實作主體在 [formocast_simulator.cpp](../../../shared/origami/src/simulator/tensilelite/formocast_simulator.cpp) 的 `predictedPerformance()`；更底層的參數換算在 [formocast.hpp](../../../shared/origami/include/origami/simulator/tensilelite/formocast_simulator.hpp)。

> **一句話：**Formocast 把一支 kernel 的執行拆成幾個「階段（phase）」，每個階段用硬體參數算出要花多少時間，再依 compute／memory 誰慢取誰、最後把各階段加總，得到一個 `microSeconds`。

建議先讀 [README.md](README.md) 建立直覺，再讀本檔。若對 GPU 架構不熟、對 cache 階層 / bank conflict / latency hiding 等概念「有看沒有懂」，先讀 [../performance-modeling-concepts.md](../performance-modeling-concepts.md)（GPU 效能建模概念前置教材）再回來。

## 白話總覽：像估算一趟洗衣流程

把一支 GEMM kernel 想成一台洗衣機跑一輪，Formocast 要估「整輪多久」。它不是拍腦袋給一個總數，而是把流程拆段分別估：

- 開機暖機（initialization）
- 先放第一批衣服進去（prefetch，先載第一輪資料）
- 主要洗程（unrolled main loop：一邊搬資料、一邊做矩陣乘加，反覆很多輪）
- 收尾那一小輪（tail loop：K 不能整除 DepthU 時剩下的零頭）
- 脫水／拿出來（store：把結果寫回記憶體）
- 如果多台機器分洗同一批（split-K：GSU/LSU），還要加上「最後把各台結果合起來」的 overhead

每段各算一個時間，加起來就是預測延遲。關鍵直覺有兩個:

- **每一輪主迴圈,「算」和「搬資料」是可以重疊的**,所以那一輪的耗時不是兩者相加,而是**取比較慢的那個**(`max(compute, memory)`)——就像洗衣服時「洗」和「等下一批晾乾」可以同時進行,瓶頸是比較慢的那件事。
- **搬資料要分層**:資料可能在 L1／L2／L3 cache 或 HBM 主記憶體,越後面越慢;Formocast 會估每一層的命中率與頻寬,算出實際搬資料要多少 cycle。

## 七段成本模型（實際加總的東西）

`predictedPerformance()` 把總延遲組成大致如下（來源：codebase `formocast_simulator.cpp`；階段命名也對應內部 Confluence「Formocast High Level Overview」）：

```text
total ≈ doinit + prefetch + loop_overall + tail_overall + store_total
        + gsu_overall + lsu_overall + (CU occupancy 調整)
```

逐段白話說明（每段標明它在估什麼、受哪些參數影響）:

1. **initial cost（`doinit`,初始化)**
   - 估什麼:kernel 啟動到開始做事的固定開銷,會隨 tile 數放大。
   - 概念形式:`initialCost * num_tiles + 1.7 * (num_tiles - 1)`(常數來自 arch 常數表)。
2. **prefetch（預取)**
   - 估什麼:主迴圈開始前,先把第一輪 unroll 需要的 global 資料載進來的成本。
   - 受 global read 次數、vector width、DepthU、PrefetchGlobalRead(PGR)影響。
3. **unrolled main loop（`loop_overall`,主迴圈)**
   - 估什麼:K 方向反覆做的核心迴圈,是大 K 問題的主要耗時。
   - compute 成本:`math_clk / math_frequency * num_tiles`(math_clk 是每輪矩陣指令的 cycle 數)。
   - memory 成本:由各 cache 層的 request 數換算(見下節)。
   - **關鍵**:若 `PrefetchGlobalRead > 1` 且 memory/math 比值 ≥ 1.5,兩者重疊,該輪取 `(math + mem) / 2`;否則取較慢者。這就是「算與搬重疊」的直覺。
4. **memory access（cache 模型,融在 prefetch/loop 裡)**
   - 估什麼:global read 打到 L1/L2/L3/HBM 各層的命中率與頻寬限制。
   - 逐層算 request 數 → `req * element_size / bus_width / frequency` 換成 cycle,再跨兩個 operand(A、B)與各層加總。
   - `hitRate` 就是這裡估出來的整體 L2 命中率(gfx942 的 L1 有特殊處理)。
5. **tail loop（`tail_overall`,尾迴圈)**
   - 估什麼:K 不能被 DepthU 整除時,剩下的零頭那幾輪。
   - 概念:`(mem_overall * K_tail/DepthU + math_overall) * 2 + prefetch * 2`。
6. **store（`store_total`,寫回)**
   - 估什麼:把輸出矩陣 D 寫回記憶體的成本,逐 cache 層算。
   - 受 write bus 寬度與 store vector width(GWVWD)影響。
7. **GSU / LSU overhead（split-K 的合併成本)**
   - **GSU(`gsu_overall`)**:GlobalSplitU>1 時,多個 workgroup 各算部分和再合併;MultipleBuffer 走記憶體頻寬 + buffer copy,MultipleBufferSingleKernel 較省;乘上 tile 數。
   - **LSU(`lsu_overall`)**:LocalSplitU,一個 workgroup 內多 wave 分攤 K 維,依 tile 大小、LSU 因子、thread 數、store vector width 估。
8. **CU occupancy 調整**
   - 估什麼:若 `CUOccupancy ≥ 2`(一個 CU 上塞多個 tile 依序跑),加上每 tile 的排隊懲罰,隨 `loopCnt` 放大。

## compute vs memory:為什麼取 max 而不是相加

這是效能建模的核心觀念,也是 Formocast(與 Origami)共同的骨架:

- GPU 一邊做矩陣乘加(compute)、一邊從記憶體搬資料(memory),兩者可**部分重疊**。
- 若一輪的瓶頸是算力(compute-bound),搬資料的時間被藏在算的時間裡 → 該輪耗時 ≈ compute。
- 若瓶頸是頻寬(memory-bound),反過來 → 該輪耗時 ≈ memory。
- 所以主迴圈單輪取 `max(compute, memory)`,不是 `compute + memory`。**取 max 是「重疊」的數學表達。**

Formocast 比 Origami 細的地方,在於它把「memory」拆到 L1/L2/L3/HBM 逐層、並讀入 DepthU/PGR/DTL 等參數去調整重疊程度,而 Origami estimation 只用粗粒度的 compute/memory roofline。

## 逐段成本要用到哪些輸入

- **problem 面**(來自 `ProblemInfo`):M/N/K、batch、dtype、每元素 byte 數(bpe)、transpose。
- **kernel 面**(來自 `SizeMapping`,約 35 欄):MacroTile、MatrixInstruction、DepthU、GlobalSplitU、LocalSplitU、PrefetchGlobalRead、DirectToVgpr/Lds、NumLoadsCoalesced、VectorWidth、GlobalReadVectorWidth、StoreVectorWidth、WorkGroupMapping、CUOccupancy、MathClocksUnrolledLoop、WaveGroup… 完整欄位見 [api-and-usage.md](api-and-usage.md)。
- **硬體面**(來自 arch 常數表):見下節。

一個關鍵細節(來源:內部 Confluence「Difference between Origami and Formocast」):主迴圈的「每輪 math cycle 數」(`MathClocksUnrolledLoop`)是 TensileLite 用 **rocIsa API 取出實際指令 cycle 數**存進 SizeMapping 的,不是 Formocast 自己從 MI 粗估——這是它比 estimation 準的原因之一。這個「實際指令 cycle 數」正是由 **Path B 逐指令模擬器**(`rocisa/cycle.cpp` 的 `getCycles()`)逐指令、逐 thread 量出來再回填的,完整實作見 [cycle-accurate-path.md](cycle-accurate-path.md)。

## per-arch 硬編常數(`HardwareConstants`)

Formocast 的準度高度依賴一組**每個 GPU 架構各一份的硬編常數**(在 `getHardwareConstants()`,以 binary blob 儲存)。內容包含:

- cache 幾何:L1/L2/L3 容量、line size、每 CU 的 bus 寬度(讀/寫)。
- 記憶體:HBM 頻寬、L3 頻寬、`mem_frequency`、`hbmBandWidth`。
- 頻率:`boost_frequency`、以及**滿載實際頻率** `math_frequency`(硬體無法長時間跑在 boost,要用重載 kernel 量)。
- 規模:`NumCUs`、`NumXCDs`(chiplet 數)、`wavefrontSize`。
- 實驗量得:`L2ReadArbEff`、`L2WriteArbEff`、`initialCost`、`initialCostHit`。

目前支援的架構(硬編於 `getHardwareConstants()`):

| 架構 | NumCUs | NumXCDs | 備註 |
| --- | --- | --- | --- |
| gfx950 | 384（12 XCD × 32） | 12 | 最新 CDNA |
| gfx942 | 192（6 XCD × 32） | 6 | L1 命中率有特殊路徑 |
| gfx1201 | — | 1 | RDNA，單 XCD |

> **重點(也是限制)**:這些常數是 per-arch 硬編、且部分要靠 micro-benchmark 量。上新架構若沒正確填,預測會偏。Formocast 最早在 gfx942 開發、之後才移到 gfx950;gfx9 與 gfx12/13 差異大,per-platform 拆解要小心。填常數的 SOP 見 [debugging-and-calibration.md](debugging-and-calibration.md)。

## early-terminate sentinel:模型主動放棄的情況

不是每組參數都會走完整模擬。遇到某些 guard,`predictedPerformance()` 直接回哨兵值:

```text
microSeconds = 9,999,999.9
hitRate = 0
```

常見 guard(來源:codebase `formocast_simulator.cpp`):

- `GlobalSplitU == 0`(未初始化)。
- MacroTile 相對 M/N 過小(underflow,如 `M < 128 && MT0 - M >= 16`)或過大(oversize,如 `M >= 128 && MT0 - M >= 32`)。
- BF16/Half 的 K / DepthU / MatrixInstruction 組合不相容(如 `K >= 64 && depthU <= 32` 等,再搭配 NumBatches、MI 條件)。
- DirectToLds 與 tile 不相容(`DirectToLdsA && M < MT0` 或 `DirectToLdsB && N < MT1`)。
- derived PLR=0(`loopCnt < LocalSplitU`)。

**關鍵教學點**:`9,999,999.9` 是**有限浮點數**(`isfinite` 為 true),不是 NaN/Inf。它的語意是「模型沒給正常估計、請當成極差」。任何只用「是否非有限」來判斷有無分數的程式,都會**漏掉這個 finite sentinel**——這在研究實驗裡是個真實坑,見 [limitations-and-research-use.md](limitations-and-research-use.md)。而且這些 guard **非窮舉**:有些不理想的組合不會命中 guard、會回一個正常但偏差的預測。

## 交叉連結

- **原始碼全景與兩條模擬路徑（先看這份）** → [source-map.md](source-map.md)
- 七段成本的實際程式碼公式與變數 → [cost-phases-internals.md](cost-phases-internals.md)
- cache 模型/hitRate/request 的實作細節 → [memory-model-internals.md](memory-model-internals.md)
- 主迴圈 `MathClocksUnrolledLoop` 從哪來(Path B 逐指令模擬)→ [cycle-accurate-path.md](cycle-accurate-path.md)
- 介面與資料結構欄位 → [api-and-usage.md](api-and-usage.md)
- 怎麼被 dispatch / 被 client 呼叫 → [integration.md](integration.md)
- 設計目的與限制、研究盲區 → [limitations-and-research-use.md](limitations-and-research-use.md)
- rocprof 對照與新架構常數 SOP → [debugging-and-calibration.md](debugging-and-calibration.md)
- Origami(estimation)的延遲模型對照 → [../latency-model.md](../latency-model.md)
- Formocast 設計 RFC 原文 → [../../internal_docs/formocast-design-rfc.md](../../internal_docs/formocast-design-rfc.md)

## 一句話總結

> **Formocast 把 kernel 拆成 init/prefetch/loop/tail/store/GSU/LSU 幾段,每段用 per-arch 硬編常數 + kernel 參數算 cycle,主迴圈用 `max(compute, memory)` 表達重疊,加總成 microSeconds;命中 guard 時回有限哨兵值 9,999,999.9 表示放棄估計。** 下一篇看 [api-and-usage.md](api-and-usage.md)。
