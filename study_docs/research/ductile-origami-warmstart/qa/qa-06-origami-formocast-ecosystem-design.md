# QA-06 — Origami／Formocast ecosystem

> **文件角色：**這是從 [實驗白話導讀 hub](../../ductile-origami-warmstart-experiment-guide.md) 拆分出來的白話導讀主題檔，方便在單一主題上持續討論。它不是 experiment authority，也不是 contract、lock 或 report，不會取代正式的 charter、experiment plan、checkpoint design、lock 或 report。
>
> **衝突處理：**若本檔與正式文件衝突，以 [research charter](../../surrogate-dse-plan.md)、[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)、[active checkpoint index](../README.md) 及各 checkpoint design 為準。
>
> **2026-08-04 current status override：**S10R3 已 terminal negative；S10R4 已 retired／not evaluated；S11 已 sealed `LOCKED_READY`。沒有 S11/S12 result、effective checkpoint lock、report 或 edge；最新狀態仍須對照 active checkpoint index、formal artifacts 與 Git history。

---

## 22. Origami library、Origami estimation 與 Formocast

這三個名稱很容易被混在一起。最重要的第一步是把「library」和「library 裡的 prediction backend」分開。

### 22.1 一張圖先看懂三者關係

```text
Origami library（shared/origami）
│
├─ 對外 API／共用基礎設施
│  ├─ problem_t
│  ├─ hardware_t
│  ├─ config_t
│  ├─ rank_configs()
│  └─ select_config()
│
├─ prediction_mode = estimation（預設）
│  └─ Origami 快速 analytical estimation model
│
└─ prediction_mode = simulation
   └─ compute_formocast_latency()
      └─ origami::Formocast::predictedPerformance()
```

因此：

- **Origami library** 是整個軟體套件與 API；
- **Origami estimation** 是這個 library 裡的快速 analytical prediction mode；
- **`origami::Formocast`** 是同一個 library namespace 下、針對 TensileLite 的較細 simulation backend。

把「Origami 沒被選為本研究 primary model」理解成「Origami library 不能整合」是錯的。更精確的說法是：

> 本研究沒有把 **Origami estimation mode** 選成 formal primary treatment；Origami library 的資料結構與 API 仍然存在，而且 Formocast 本身就位於 `origami` namespace／source tree 內。

相關程式：

- [Origami public types](../../../../shared/origami/include/origami/types.hpp)
- [Origami public API](../../../../shared/origami/include/origami/origami.hpp)
- [Origami GEMM estimation/simulation dispatch](../../../../shared/origami/src/origami/gemm.cpp)
- [Formocast simulator](../../../../shared/origami/src/simulator/tensilelite/formocast_simulator.cpp)

### 22.2 Origami library 是什麼？

Origami library 位於 `shared/origami/`，它提供：

- 共用 problem/config/hardware 資料結構；
- C++ 與 Python API；
- GEMM analytical prediction；
- Attention prediction；
- StreamK grid/reduction 選擇；
- WGM／staggerU heuristics；
- config ranking、top-k、best-config selection；
- Formocast simulation backend。

典型 public API 是：

```text
rank_configs(problem, hardware, configs)
select_config(problem, hardware, configs)
select_topk_configs(problem, hardware, configs)
```

它們接受：

```text
problem_t
+ hardware_t
+ 一組 config_t
```

並回傳每個 config 的預估 latency 與排序結果。

白話說：

> Origami library 是「把 problem、hardware、候選 kernels 接進來，再用某種 prediction mode 排名」的完整框架。

官方範例與 API 說明可參考：

- [Origami README](../../../../shared/origami/README.md)
- [Origami API 與資料結構導讀](../../../origami/api-and-usage.md)
- [Origami 生態與 Formocast 關係](../../../origami/ecosystem-and-formocast.md)

### 22.3 Origami estimation mode 是什麼？

`config_t.prediction_mode` 預設是：

```text
prediction_modes_t::estimation
```

Estimation 是快速 analytical model。它不逐指令模擬完整 TensileLite kernel，而是使用較精簡的物理骨架：

1. 依 problem/config/hardware 算 grid、occupancy、workgroup mapping；
2. 估算 compute latency；
3. 估算 L2／MALL／HBM memory latency；
4. 主迴圈取 `max(compute, memory)`；
5. 加上 prologue、epilogue、loop overhead及 reduction；
6. 對全部 configs 排序。

概念公式：

```text
estimated latency
= max(compute latency, memory latency) × loop/timestep count
  + prologue
  + epilogue
  + reduction
  + calibrated overheads
```

Estimation 的優點：

- 快；
- deterministic；
- 適合 runtime selection；
- 支援較通用的 config/backend 模型；
- 不需要 benchmark 每個 config。

限制是：

- 模型較粗；
- 主要依賴 MacroTile、MatrixInstruction、occupancy、WGM、cache hints、vector width、problem/hardware 等通用欄位；
- 不會在 estimation path 讀取 `config.tensile()` 裡的 backend-specific `tensile_params_t`。

詳細模型可參考 [Origami latency model](../../../origami/latency-model.md)。

### 22.4 Formocast simulation mode 是什麼？

若：

```text
config.prediction_mode == prediction_modes_t::simulation
```

Origami 的 `gemm::compute_total_latency()` 會改走：

```text
compute_formocast_latency()
```

這個 adapter 會：

1. 把 `problem_t` 轉成 Formocast `ProblemInfo`；
2. 把 `config_t` 及 `config.tensile()` 轉成 Formocast `SizeMapping`；
3. 設定 hardware architecture；
4. 呼叫 `origami::Formocast::predictedPerformance()`；
5. 取得 `PredictedPerformance`；
6. 將其中的 `microSeconds` 當成 config latency。

Formocast 會比 estimation 模式更細地拆解：

- initial cost；
- prefetch；
- unrolled loop；
- LocalRead／GlobalRead／LocalWrite；
- MFMA／math cycles；
- wait/stall；
- L1/L2/L3/HBM access；
- tail loop；
- GSU／LSU overhead；
- store；
- occupancy。

直接呼叫 `origami::Formocast` 時，輸出不只一個 latency，還包含：

- `microSeconds`；
- `hitRate`；
- MT0／MT1；
- DepthU；
- GSU／LSU；
- loop count；
- memory/math breakdown；
- cache hit information；
- 其他 simulation 中間資訊。

### 22.5 Estimation 與 simulation 的輸入／輸出差異

兩者都需要：

- problem dimensions M/N/K/batch；
- transpose；
- dtype；
- hardware architecture/characteristics；
- MacroTile；
- MatrixInstruction；
- occupancy；
- workgroup mapping；
- global/vector widths。

Estimation 的輸出核心是：

```text
一個預估 latency
```

外層 `rank_configs` 再將 configs 依 latency 排序，輸出：

```text
prediction_result_t {
  latency,
  config
}
```

Formocast simulation 的原生輸出是更完整的：

```text
PredictedPerformance {
  microSeconds,
  hitRate,
  tile/depth/GSU/LSU/loop fields,
  math/memory/cache breakdown,
  ...
}
```

但若從 Origami 的通用 `compute_total_latency()` API 進入 simulation mode，外層目前只取 `microSeconds` 回傳作 ranking。

### 22.6 Estimation 忽略、Formocast 會讀的 Tensile-specific metadata

[types.hpp](../../../../shared/origami/include/origami/types.hpp) 對 `tensile_params_t` 的註解明確指出：

> 這些是 Tensile/TensileLite-specific parameters，供 Formocast simulation model 使用；estimation-based model 會忽略。

目前包含：

- `depth_u`；
- `global_split_u`；
- `global_accumulation`；
- `local_split_u`；
- `direct_to_vgpr_a`／`direct_to_vgpr_b`；
- `direct_to_lds_a`／`direct_to_lds_b`；
- `num_loads_coalesced_a`／`num_loads_coalesced_b`；
- `wave_num`；
- `wave_group_m`／`wave_group_n`；
- `prefetch_global_read`；
- `math_clocks_unrolled_loop`；
- `swizzle_a`／`swizzle_b`；
- `workgroup_mapping_xcc`；
- `workgroup_mapping_xcc_group`；
- `global_split_u_coalesced`；
- `global_split_u_wgm_round_robin`。

Formocast 還會結合 `config_t` 的一般欄位：

- MacroTile；
- MatrixInstruction；
- occupancy；
- WorkGroupMapping；
- GRVWA／GRVWB；
- GWVWD；
- VectorWidthA／B。

這個差異對本研究非常重要。

### 22.7 為什麼 fixed-tile residual-gene 研究選 Formocast primary？

本研究保護 existing `group_0`。很多大範圍幾何資訊，例如：

- MacroTile；
- MatrixInstruction；
- WorkGroup；
- 部分 GSU／tile 組合；

已經被 grouped candidate 和 existing weights 處理。

剩下想研究的 residual genes 常是更細的 TensileLite execution parameters，例如：

- DepthU；
- PrefetchGlobalRead；
- DirectToVgpr／DirectToLds；
- WGM／WGM XCC；
- vector/read widths；
- split-K method；
- wave group；
- load coalescing；
- exact loop math clocks。

如果兩個完整 configs：

- MacroTile 相同；
- MatrixInstruction 相同；
- occupancy 相同；

但只差 `tensile_params_t` 裡的某個 residual value，Origami estimation 可能看不到差異，或把兩者排成 model tie。

Formocast 則會把這些 metadata 放入 `SizeMapping` 和 simulation，因此比較有機會辨識：

> fixed tile 之後，哪個 residual config 比較好。

所以本研究的選擇是：

- Formocast：formal primary whole-config scorer；
- Origami estimation：sensitivity／ranking reference；
- 真實 GPU GFLOPS：最終 judgment。

這不表示 Formocast 一定比較準。它仍必須通過：

- coverage；
- sensitivity；
- D5 real-score ranking；
- prior-mass；
- same-entropy shuffled；
- actual Gen0。

### 22.8 為什麼 Origami estimation 只作 reference？

主要原因不是它「不能接」，而是本研究問題的 discrimination requirement。

當 fixed tile/group 已經鎖住後：

- estimation 最擅長的 MacroTile／MI／粗粒度 compute-memory 訊號可能已被固定；
- residual genes 的變化可能主要落在 estimation 不讀的 `tensile_params_t`；
- 多個不同 residual configs 可能映射成相同 estimation input；
- score ties 會讓 per-gene factorization 沒有可用 sensitivity。

因此將它設成 reference 可以回答：

- 快速 analytical model 是否仍看得到 residual ranking？
- Formocast 的額外 metadata 是否真的提供更多 discrimination？
- 若兩者排序相近，較便宜的 estimation 是否已足夠？

但本輪沒有再增加一個正式 Origami treatment arm，以避免：

- 增加 arms、samples 和 GPU judgment 成本；
- 稀釋主要 Formocast factorization問題；
- 在尚未證明 entry、support、mapping 前擴大 scope。

### 22.9 Origami estimation 能不能接到 Ductile factorization hook？

**技術上可以。**

Ductile per-gene hook 本身不要求 scorer 一定是 Formocast。Factorization 需要的抽象介面只是：

```text
score(full_config, problem, hardware) -> scalar benefit/latency
```

因此可以把 scorer 換成：

```text
Origami estimation:
  problem_t + hardware_t + config_t
      ↓
  compute_total_latency() / rank_configs()
      ↓
  whole-config estimated latency
      ↓
  同一套 per-gene marginalization
      ↓
  per-gene probabilities / Ductile weights
```

換句話說，Origami estimation 完全可以：

1. 對每個 valid full config 產生 latency；
2. 轉成 benefit rank；
3. 計算 `mu_gv`；
4. 通過同一 gene stability gate；
5. 轉成 probabilities；
6. 透過同一 Ductile weights hook 注入 Gen0。

真正的限制是：

> 如果 estimation 根本不讀某個 residual gene 對應的 metadata，那些不同 values 會得到相同或近似 score，factorization 雖然「能跑」，但不會產生有意義的 guidance。

所以：

- **not selected**：本輪基於模型辨識力、scope 與成本，沒有選為 formal primary treatment；
- **cannot integrate**：API／hook 結構上無法接入；

這兩句完全不同。本研究只支持前者，不支持後者。

### 22.10 什麼情況下未來值得把 Origami estimation 變成 formal arm？

例如：

- 研究對象改成 MacroTile／MatrixInstruction／StreamK 等 estimation 可見的 genes；
- Origami estimation 新增並實際使用更多 backend metadata；
- model-only audit證明它在 residual space 有足夠 score diversity；
- 需要測 fast analytical scorer能否以更低成本達到類似 prior；
- 有足夠資源加入另一個 model arm與對應 shuffled control；
- 研究問題改成 Formocast simulation vs Origami estimation 的 cost/accuracy trade-off。

若未來加入，必須在 real labels 前重新預註冊：

- scorer revision；
- input mapping；
- eligibility；
- factorization；
- control；
- sample size；
- claim boundary。

不能看完 Formocast結果後，再用同一 judgment pool臨時增加 Origami arm。

### 22.11 現有 SolutionIterator 已經怎麼整合 Formocast？

[SolutionIterator.cpp](../../../../projects/hipblaslt/tensilelite/client/src/SolutionIterator.cpp) 已直接：

1. include Formocast simulator header；
2. 對 solution 執行 `checkSolution`；
3. 從 problem 建立 `ProblemInfo`；
4. 從 `ContractionSolution::getSizeMapping()` 建立 Formocast `SizeMapping`；
5. 從 hardware 取得 architecture；
6. 呼叫：

   ```text
   formocast.setProblem(...)
   formocast.setSolution(...)
   formocast.setHardware(...)
   formocast.predictedPerformance()
   ```

7. 取 `microSeconds`；
8. stable sort；
9. 依 `PredictionThreshold` 建 benchmark queue。

因此本研究不能宣稱：

> 首次把 Formocast 接到 TensileLite tuning。

現有 integration 已經是 whole-config pre-screen。

本研究真正新增的問題是：

> 能否把現有 whole-config prediction，再 factorize 成 Ductile initial population 的 per-gene residual guidance？

也就是：

```text
既有 SolutionIterator：
whole-config score → benchmark queue

本研究：
whole-config score → per-gene marginals → Ductile Gen0 probabilities
```

兩者使用相近的模型輸入，但 intervention 位置不同。

### 22.12 簡單對照總結

```text
Origami library
= 對外 API、資料結構、ranking/selection infrastructure，以及多個 prediction backends

Origami estimation
= 快速、分析式、較通用；預設模式；不讀 tensile_params_t

origami::Formocast
= 較慢、較細、TensileLite-specific simulation；讀取更多 backend metadata

本研究 primary
= Formocast whole-config score

本研究 reference
= Origami estimation ranking/sensitivity

能否接同一 Ductile hook？
= 兩者都可以；差別在 scorer 看不看得到 residual genes、是否能產生有意義的 score variation
```

延伸閱讀：

- [Origami vs Formocast 內部對照](../../../internal_docs/origami-vs-formocast.md)
- [Origami ecosystem and Formocast](../../../origami/ecosystem-and-formocast.md)
- [Origami API 與使用方式](../../../origami/api-and-usage.md)
- [Origami latency model](../../../origami/latency-model.md)

---

