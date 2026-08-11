# Formocast 除錯與校正

路徑說明：本檔在 `study_docs/origami/formocast/`。原始碼連結用 `../../../shared/...`、`../../../projects/...`。行號會漂移，以符號名稱為準。

> **一句話：**當 Formocast 選錯、或要上一顆新 GPU 時，怎麼查、怎麼校——用 rocprof counter 對照模型的 cache/memory 假設，逐段 breakdown 找偏差來源，並在新架構填對 `HardwareConstants` 常數。

本檔主要整理自內部 Confluence「Formocast Debugging Guide」與「ROCm Origami + GEMM Solution Selection 生態系整理報告」（連結見 [../ecosystem-and-formocast.md](../ecosystem-and-formocast.md)），並對照 codebase。建議先讀 [model.md](model.md) 知道有哪些階段可對照。

## 白話總覽：分兩種情境

- **情境 A：Formocast 在某些 problem 選錯 kernel** → 通常是「模型某個假設與真實硬體不符」或「solution pool 沒涵蓋更好的參數」。用 rocprof 對照模型 vs 實測,定位是哪一層偏。
- **情境 B：要在新 GPU 上啟用 Formocast** → 通常是 `HardwareConstants` 沒填或填錯。照下面 SOP 逐項量測、填入。

## 用 rocprof counter 驗證模型假設

Formocast 的準度關鍵在「cache 命中率」與「memory request 數」估得對不對。可用 rocprof 的硬體 counter 對照模型輸出:

| 要驗的模型量 | 對照的 rocprof counter | 白話 |
| --- | --- | --- |
| L2 cache 命中率(`hitRate`) | `TCC_HIT_sum` / `TCC_MISS_sum` | 模型估的 L2 命中率 vs 實際命中/未命中次數 |
| L1/L2 request 數 | `TCP_TOTAL_CACHE_ACCESSES_sum`、`TCP_TCC_READ_REQ_sum` | 一次 global read 會打出多次 L1/L2 request(依硬體 pipeline);驗模型的 request 換算 |
| local read latency | 手寫組語量測 | 依 CU-LDS,每平台 cycle 數固定;驗 LDS 讀延遲 |

指引(來源:Formocast Debugging Guide):「若發現 Formocast 少算了某個元素,就要把它實作進去。」也就是**用實測 counter 反推模型缺了哪一塊**。

### 怎麼收集這些 counter

（來源:TensileLite client,PR ROCm/rocm-libraries#4836）

- build 時開 rocprof:`invoke build-client --enable-rocprof`,或 cmake `-DENABLE_ROCPROFSDK=ON`。
- 在 tuning YAML 的 GlobalParameters 加 `RocProfCounter: [TCC_HIT_sum, TCC_MISS_sum]`,或在 `ClientParameters.ini` 用 `rocprof-counter=<name>`。
- 輸出欄位 `rocprof-counters`,格式如 `"TCC_HIT_sum: <value>, TCC_MISS_sum: <value>"`;多維未 reduce 的 counter 會印成 `TCC_HIT(INST=2, XCC=1): ...`。

> 這些是 CLI/YAML 參數與 counter 名稱,屬於操作字串,不是可點的原始碼檔,故保留為 inline code。

## 逐段 breakdown 對照

`PredictedPerformance` 會回 `init / preloop / loop / tail / store / gsu / lsu` 各段耗時(見 [api-and-usage.md](api-and-usage.md))。除錯時把「哪一段佔比異常」和實測對照,能快速縮小問題:

- `loop` 佔比異常高但實測沒那麼慢 → 可能 memory 模型高估(cache 命中率估太低),用 `TCC_*` 對照。
- `store` 異常 → 檢查 write bus 寬度常數與 store vector width。
- `gsu`/`lsu` 異常 → split-K 的合併 overhead 模型或參數不對。
- 整體都偏 → 很可能是 arch 常數(頻率/頻寬)沒校準。

## 上新架構的 bring-up SOP（校 `HardwareConstants`）

（來源:Formocast Debugging Guide「Landing on a New Platform」,常數欄位定義在 [formocast_simulator.hpp](../../../shared/origami/include/origami/simulator/tensilelite/formocast_simulator.hpp) 的 `HardwareConstants`;填入處在 [formocast_simulator.cpp](../../../shared/origami/src/simulator/tensilelite/formocast_simulator.cpp) 的 `getHardwareConstants()`。）

要填的常數分幾類:

- **直接抄硬體規格**:`L1/L2/L3CacheCapacity`、`L1/L2CacheLineSize`、`L1/L2BusWidthPerCU`、`L1/L2WriteBusWidthPerCU`、`maxBandWidthHBM`、`mem_frequency`、`hbmBandWidth`、`L3BandWidth`、`boost_frequency`、`NumCUs`、`wavefrontSize`、`NumXCDs`。
- **要做硬體實驗量**:
  - `L2ReadArbEff` / `L2WriteArbEff`(L2 讀寫仲裁效率)。
  - `math_frequency`:**滿載實際頻率**——硬體無法長時間跑在 `boost_frequency`,要用重載 kernel 實測。
  - `initialCost`:kernel 啟動到第一個 prefetch global read 的時間(rocprof + thread trace viewer 量)。
  - `initialCostHit`:`initialCost` 扣掉指令 fetch 的部分(跑一個「每 CU >1 tile」的 kernel 量)。
- **自動推導**:`flopsPerClk`。

另外要**檢查指令 cycle 數**:TensileLite generator 用 rocIsa 依平台取每條指令的 cycle 數;Formocast 用它模型化 local read latency、LDS bank conflict、VGPR bank conflict(規劃中)。可 uncomment 一段程式,讓組語檔輸出 cycle 標記(例如 `v_mfma_f32_16x16x32_bf16` / `ds_read_b128` 會被標上 cycle)。

> 提醒:Formocast 最早在 gfx942 開發、之後移到 gfx950;gfx9 與 gfx12/13 架構差異大,per-platform 的效能拆解要個別分析,不能直接沿用另一代的常數。

## 已知的 TODO / 弱點（除錯時要有心理準備）

（來源:Formocast Debugging Guide,部分章節仍是 TODO stub）

- 「Solution Pool Selection」「Solving Bad Selections」「Adding a New Tensilelite Parameter」等章節目前是 **TODO**（未寫完）。
- 新增一個 tensilelite 參數(進階排程/記憶體處理)可能**打亂預測準度**——要把它整進 SizeMapping + 預測流程並重新驗證。
- solution pool 可能沒涵蓋最佳 kernel(尤其新參數/新硬體特性),需要擴充(如 CMS、DTL)。

## 相關工具

- **rocprof** + thread-trace viewer:量 `TCC_*`、`TCP_*` counter 與 `initialCost`。
- **rocIsa**:取每平台指令 cycle 數。
- **hipblaslt-bench**:grid sweep 驗證被選中的 kernel 真的跑得出來、且快。
- Origami 端另有 `demystify` Debugging Dashboard(selection 效率分析),見 [../debugging-and-calibration.md](../debugging-and-calibration.md)。

## 交叉連結

- 模型每段在算什麼(對照 breakdown)→ [model.md](model.md)
- 輸出欄位(breakdown / memCosts)→ [api-and-usage.md](api-and-usage.md)
- 怎麼被呼叫、PredictionThreshold → [integration.md](integration.md)
- Origami 的除錯/校正(dashboard、`architecture_constants` SOP、gfx1150 worked example)→ [../debugging-and-calibration.md](../debugging-and-calibration.md)
- 生態報告(KPI、doc 索引)→ [../ecosystem-and-formocast.md](../ecosystem-and-formocast.md)

## 一句話總結

> **除錯:用 rocprof 的 `TCC_*`/`TCP_*` counter 對照模型的 cache/request 假設、看逐段 breakdown 哪段偏;上新架構:照 SOP 量並填 `HardwareConstants`（尤其 `math_frequency`、`initialCost` 要實測）,並確認指令 cycle 數正確。** 回總覽看 [README.md](README.md)。
