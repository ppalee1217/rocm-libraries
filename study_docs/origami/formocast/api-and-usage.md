# Formocast API 與使用方式

路徑說明：本檔在 `study_docs/origami/formocast/`。原始碼連結用 `../../../shared/...`。行號會漂移，以符號名稱為準。介面定義在 [formocast_simulator.hpp](../../../shared/origami/include/origami/simulator/tensilelite/formocast_simulator.hpp)（三個 struct 與四個方法都是 `origami::Formocast` 的巢狀成員）；使用範例見 [test_formocast.cpp](../../../shared/origami/tests/test_formocast.cpp)。

> **一句話：**用 Formocast 就四步——`setProblem`（要算什麼）、`setSolution`（用什麼 kernel 設定）、`setHardware`（哪張卡）、`predictedPerformance()`（拿回預測延遲）。

建議先讀 [model.md](model.md) 知道它在算什麼，再看本檔怎麼呼叫。

## 介面總覽：class `origami::Formocast`

| 方法 | 白話：做什麼 | 輸入 | 位置 |
| --- | --- | --- | --- |
| `setProblem(ProblemInfo p)` | 設定「要算哪個 GEMM」 | 矩陣維度、dtype、transpose | [formocast_simulator.hpp](../../../shared/origami/include/origami/simulator/tensilelite/formocast_simulator.hpp) |
| `setSolution(SizeMapping sm)` | 設定「用哪一組 kernel 參數」 | tile、MI、DepthU、GSU… | 同上 |
| `setHardware(architecture_t arch)` | 設定「哪張 GPU」 | `gfx942` / `gfx950` … | 同上 |
| `predictedPerformance() const` | 跑模擬、回傳預測結果 | （用前面設定的狀態） | 同上 |

呼叫順序固定：先三個 `set*`，再 `predictedPerformance()`。實作主體在 [formocast_simulator.cpp](../../../shared/origami/src/simulator/tensilelite/formocast_simulator.cpp)。

## 輸入 1：`ProblemInfo`（要算哪個 GEMM）

「一個 GEMM 問題」的規格。欄位（來自 header）：

| 欄位 | 型別 | 意義 |
| --- | --- | --- |
| `M`, `N`, `K` | double | 矩陣維度（`D = op(A[M×K]) · op(B[K×N])`） |
| `NumBatches` | double | batch 數 |
| `bpeA`, `bpeB`, `bpeD` | uint32_t | A / B / 輸出 D 每元素 byte 數（bytes-per-element） |
| `bpeCompute` | uint32_t | 計算型別的每元素 byte 數 |
| `transA`, `transB` | bool | A / B 是否轉置 |
| `swizzleTensorA/B` | bool | 記憶體 swizzle 佈局 |
| `dataType` | data_type_t | 計算 dtype（如 `BFloat16`、`Half`） |

## 輸入 2：`SizeMapping`（用哪一組 kernel 設定）

「一支 kernel 的完整參數組合」，約 35 個 TensileLite 參數——這正是 Formocast 比 Origami estimation 看得更細的地方（estimation 不讀這些）。主要欄位：

| 欄位 | 意義 |
| --- | --- |
| `macroTile[3]` | MacroTile `(MT0, MT1, MT_K)`，一個 workgroup 的輸出區塊 |
| `matrixInstruction[4]` | MFMA 指令形狀 |
| `depthU` | K 方向一次 unroll 深度 |
| `globalSplitU` / `LocalSplitU` | 兩種 split-K（跨 workgroup / workgroup 內多 wave） |
| `PrefetchGlobalRead` | 提前載下一輪 global 資料的階數 |
| `DirectToVgprA/B`, `DirectToLdsA/B` | 直送 VGPR / LDS 的最佳化旗標 |
| `NumLoadsCoalescedA/B` | global load 合併數 |
| `grvwA`, `grvwB` | GlobalReadVectorWidth（A/B 載入向量寬度） |
| `VectorWidthA/B`, `gwvwC`, `gwvwD` | register / 寫回向量寬度 |
| `workGroupMapping`, `workGroupMappingXCC(Group)` | tile→CU / 跨 XCD 排布 |
| `CUOccupancy` | 一個 CU 上塞幾個 tile |
| `MathClocksUnrolledLoop` | 主迴圈每輪的實際指令 cycle 數（由 rocIsa 取得） |
| `waveNum`, `waveGroup[2]` | wave 數與佈局 |
| `globalAccumulation`, `globalSplitUCoalesced`, `globalSplitUWorkGroupMappingRoundRobin` | GSU 相關細節 |

> 這裡的欄位和 origami 一般 `config_t` 裡的 `tensile_params_t` 對應。estimation 模式**不讀** `tensile_params_t`，所以兩個只差 `depthU` 的 config 在 estimation 下會「打平」，在 Formocast 下才分得出來。這個差異對研究很關鍵，見 [../ecosystem-and-formocast.md](../ecosystem-and-formocast.md) 與 [limitations-and-research-use.md](limitations-and-research-use.md)。

## 輸出：`PredictedPerformance`

`predictedPerformance()` 回傳的結果。主要欄位：

| 欄位 | 意義 |
| --- | --- |
| `microSeconds` | **預測延遲（微秒）**，越小越快——排序/選型實際用的數字 |
| `hitRate` | 模型估的整體 L2 命中率 |
| `init`, `preloop`, `loop`, `tail`, `store`, `gsu`, `lsu` | 各階段耗時 breakdown（微秒），對照 [model.md](model.md) 七段 |
| `math_overall`, `mem_overall` | 主迴圈 compute / memory 各自成本 |
| `memCosts` | `MemoryAccessCosts`：L1/L2/L3/HBM 的 request 數與命中率明細 |
| `MT0`, `MT1`, `depthU`, `PGR`, `GlobalSplitU`, `LocalSplitU`, `NumCUs`, `WorkGroupMapping`, `CUOccupancy`, `loopCnt`, `num_tiles` | 回填的解讀資訊（方便除錯對照） |

> 注意：從 origami 的通用 `compute_total_latency()` 進入時，外層**只取 `microSeconds`** 做排序，那些 breakdown 欄位不會往外傳（見 [integration.md](integration.md)）。要拿完整 breakdown 必須直接呼叫 `origami::Formocast`。

## C++ 最小範例

改寫自 [test_formocast.cpp](../../../shared/origami/tests/test_formocast.cpp) 的 helper：

```cpp
#include <origami/simulator/tensilelite/formocast_simulator.hpp>
#include <origami/hardware.hpp>
using namespace origami;

// 1) 問題：BF16、M=N=4096、K=4096、transA=true/transB=false
Formocast::ProblemInfo problem;
problem.M = 4096; problem.N = 4096; problem.K = 4096;
problem.NumBatches = 1;
problem.bpeA = 2; problem.bpeB = 2; problem.bpeD = 2; problem.bpeCompute = 2;
problem.transA = true; problem.transB = false;
problem.swizzleTensorA = false; problem.swizzleTensorB = false;
problem.dataType = data_type_t::BFloat16;

// 2) kernel 設定：128x128 tile、DepthU=32、MI 32x32x8、PGR=2
Formocast::SizeMapping sm;
sm.macroTile = {128, 128, 1};
sm.matrixInstruction = {32, 32, 8, 1};
sm.depthU = 32;
sm.waveNum = 4;
sm.globalSplitU = 1;
sm.workGroupMapping = 8;
sm.CUOccupancy = 2;
sm.PrefetchGlobalRead = 2;
sm.MathClocksUnrolledLoop = 2048;   // 通常由 rocIsa 取得
sm.grvwA = 4; sm.grvwB = 4; sm.gwvwD = 4;

// 3) 硬體 + 4) 跑模擬
Formocast fc;
fc.setProblem(problem);
fc.setSolution(sm);
fc.setHardware(hardware_t::architecture_t::gfx942);
auto perf = fc.predictedPerformance();

// perf.microSeconds 是預測延遲；命中 guard 時會是 9999999.9（見 model.md）
```

## 怎麼建置 / 測試

- Formocast 是 origami library 的一部分，**沒有獨立 Python binding**；主要由 origami/gemm 的 C++ 路徑內部使用（見 [integration.md](integration.md)）。
- 單元測試在 [test_formocast.cpp](../../../shared/origami/tests/test_formocast.cpp)（Catch2）；跟著 origami 的測試建置流程跑即可。origami 整體的 build / 測試方式見 [../api-and-usage.md](../api-and-usage.md) 與官方 [../../../shared/origami/README.md](../../../shared/origami/README.md)（本檔不重複 build 細節）。

## 交叉連結

- 模型在算什麼（七段成本、cache、sentinel）→ [model.md](model.md)
- 怎麼被 dispatch / 被 client 呼叫、PredictionThreshold → [integration.md](integration.md)
- 設計目的、限制、研究盲區 → [limitations-and-research-use.md](limitations-and-research-use.md)
- origami 一般 API（`rank_configs` 等）→ [../api-and-usage.md](../api-and-usage.md)

## 一句話總結

> **四步：`setProblem` → `setSolution`（吃約 35 個 TensileLite 參數）→ `setHardware` → `predictedPerformance()`，拿回含 `microSeconds` 與逐段 breakdown 的 `PredictedPerformance`。** 下一篇看 [integration.md](integration.md)。
