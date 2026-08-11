# Origami 的 API、資料結構與實際使用

路徑說明：本檔在 `study_docs/origami/`。原始碼連結用 `../../shared/...`。行號會漂移，以符號名稱為準。建議先讀 [README.md](README.md) 與 [latency-model.md](latency-model.md)。

> 這篇是「操作手冊」：Origami 對外提供哪些函式、要餵它什麼資料、怎麼在 Python / C++ 用、怎麼 build / 測試、怎麼把模型內部值 dump 出來除錯。

## 一句話總結

> **Origami 的對外介面很小：把「問題（problem_t）+ 硬體（hardware_t）+ 一堆候選設定（config_t）」餵給 `rank_configs` / `select_config`，就拿回「排好序的候選 + 每個的預估延遲」；另外還有兩個輔助函式選 StreamK 的 launch 參數（WGM / staggerU）。**

## 三個核心輸入：problem / hardware / config

用一句話記住三者分工：

- **`problem_t`＝「要算什麼」**（矩陣多大、什麼型別）。
- **`hardware_t`＝「在哪張卡上算」**（這張 GPU 的算力、cache、頻寬）。
- **`config_t`＝「用哪支 kernel 算」**（tile 大小、矩陣指令、occupancy…）——通常一次給一整包候選清單。

Origami 的工作就是：固定 problem 與 hardware，從 config 清單裡挑最快的。

### `problem_t`——問題描述（[types.hpp](../../shared/origami/include/origami/types.hpp)）

| 欄位 | 意義 |
|------|------|
| `size`（`dim3_t`） | 問題尺寸 M, N, K。 |
| `batch` | 批次數（預設 1）。 |
| `q_heads` | query head 數（attention 模型用，預設 32）。 |
| `a_transpose` / `b_transpose` | A / B 是否轉置（`transpose_t::T` 或 `N`）。 |
| `a_dtype` / `b_dtype` / `c_dtype` / `d_dtype` | A / B / C / D 各自的資料型別。 |
| `mi_dtype` | 矩陣指令的計算型別（決定查哪條 MI 的 cycle 數）。 |
| `a_mx_block_size` / `b_mx_block_size` | MX 區塊縮放大小（FP4 / FP6 / FP8 才用，一般 0）。 |

### `config_t`——kernel 設定（[types.hpp](../../shared/origami/include/origami/types.hpp)）

這是最重要、欄位最多的結構。挑重點：

| 欄位 | 意義 |
|------|------|
| `mt`（`dim3_t`） | **macro tile**：一個 workgroup 一次算的輸出區塊 `(MT_M, MT_N, MT_K)`。最關鍵的可調參數。 |
| `mi`（`dim3_t`） | **matrix instruction**：一條硬體矩陣指令算的小塊 `(MI_M, MI_N, MI_K)`。 |
| `occupancy` | 每個 CU 常駐幾個 wavefront（**必須 > 0**，否則 `is_valid()` 失敗）。 |
| `workgroup_mapping` | WGM 提示（此欄是舊式固定值；auto 選 WGM 走 `select_workgroup_mapping`）。 |
| `cache_hints_a` / `cache_hints_b` | 對 A / B 的 cache 政策（`4` = non-temporal，不佔 cache）。 |
| `reduction_strategy` | split-K 的合併策略（`reduction_t`：spinlock / tree / parallel / atomic）。 |
| `prediction_mode` | `estimation`（快速公式，預設）或 `simulation`（走 Formocast）。 |
| `target` | 後端（`tensilelite` / `rocroller` / `triton` …）。 |
| `grid_selection` | StreamK 的 grid 選擇演算法（預設 `k_split_aware`）。 |
| `index` | 使用者自訂索引，Origami 不使用——但呼叫端常拿它**對回自己的 solution 清單**（見 [hipblaslt-integration.md](hipblaslt-integration.md)）。 |
| `grvw_a` / `grvw_b` / `gwvw_d` | global 讀 / 寫的向量寬度（一次載幾個元素）。 |
| `backend` | 後端專屬參數（`std::variant`）；TensileLite 用 `config.tensile()` 取 `tensile_params_t`。 |

> **`tensile_params_t`**（透過 `config.tensile()`）是給 **Formocast 模擬模式**用的更細參數：`depth_u`、`global_split_u`、`local_split_u`、`direct_to_vgpr/lds`、`wave_num`、`wave_group_m/n`、`prefetch_global_read`、`swizzle_a/b`、WGM XCC 欄位等。**estimation 模式會忽略這些**——它們只在 simulation（Formocast）時才被讀。

### `hardware_t`——GPU 描述（[hardware.hpp](../../shared/origami/include/origami/hardware.hpp)）

一般不用手填，用工廠函式取（見下）。重要欄位：

| 欄位 | 意義 |
|------|------|
| `arch` | 架構（gfx942 / gfx950 / gfx1100 …）。 |
| `N_CU` | 運算單元（CU）數量。 |
| `lds_capacity` / `rf_capacity` | 片上共享記憶體 / 暫存器檔容量（用於容量淘汰）。 |
| `mem1/mem2/mem3_perf_ratio` | L2 / MALL / DRAM 的頻寬比例（記憶體模型用）。 |
| `L2_capacity` / `CU_per_L2` | 每個 L2 domain 的容量 / 掛幾個 CU。 |
| `compute_clock_ghz` | 計算時脈（`compute_perf_gflops` 換算 GFLOPS 用）。 |
| `parallel_mi_cu` | 每個 CU 能並行幾條 MFMA / WMMA。 |
| `NUM_XCD` | 晶粒（XCD）數（多晶粒 GPU 如 MI300）。 |

**取得方式**（工廠方法）：
- `hardware_t::get_hardware_for_device(id)`——依裝置 id（會查 HIP）。
- `hardware_t::get_hardware_for_arch(...)`——依架構列舉。
- `hardware_t::get_hardware_for_properties(hipDeviceProp_t)`——依 HIP 屬性。

> **`architecture_constants` 與 `get_arch_constants`（新架構的關鍵）**：工廠方法背後靠 `get_arch_constants(architecture_t)` 提供每個架構的**原始硬體常數**——`num_xcds`、`mem1/2/3_perf_ratio`（L2 / MALL / HBM 峰值頻寬 TB/s）、`parallel_mi_cu`（每 CU 並行 MI 數）、`mem_bw_per_wg_coefficients`、`mem_clock_ratio`。例如 gfx942 約 `{8, 17, 1.21875*6, 4, 4, (0,0.015,0), 1.5}`（8 XCD、L2~17 TB/s、MALL~6 TB/s、HBM~4 TB/s、每 CU 4 條 MI）。沒有 MALL 的架構（如 gfx1150 iGPU）用 `NO_MALL_AVAILABLE` sentinel 讓模型跳過該層、`num_xcds=1`。注意 `hardware_t` **實例上存的是換算後的值**（建構子會依 compute clock 轉換），要看原始常數請查 `get_arch_constants` 的 case 分支。**為新 GPU 填這組常數的 micro-benchmark SOP 見 [debugging-and-calibration.md](debugging-and-calibration.md) 第四節。**

## 七個公開函式（[origami.hpp](../../shared/origami/include/origami/origami.hpp)）

| 函式 | 做什麼 | 白話 |
|------|--------|------|
| `select_config(problem, hardware, configs, model)` | 回傳**單一**最佳 config + 其延遲。 | 「幫我選最快的那個」。內部就是 `rank_configs` 取第一名。 |
| `rank_configs(problem, hardware, configs, model)` | 回傳**全部**候選依延遲排序（最佳在前）。 | 「把全部候選排好名次給我」。核心函式，其他多半包它。 |
| `select_topk_configs(problem, hardware, configs, topk, model)` | 回傳前 K 名。 | 「給我前 K 名就好」。 |
| `select_config_mnk(M, N, K, hardware, configs)` | 只給 M/N/K，其餘用預設（fp16、a 轉置 b 不轉置）。 | 快速試用 / 測試用的便捷版。 |
| `select_workgroup_mapping(problem, hardware, config, skGrid)` | 選最佳 `(wgmxccchunk, wgmxcc, wgm)`。 | StreamK kernel launch 時「workgroup 怎麼排最省 cache」。 |
| `select_staggerU(problem, hardware, config, skGrid, wgm)` | 選最佳 `(staggerUMapping, staggerU, staggerUStrideShift)`。 | 「各 workgroup 從 K 的哪裡起跑，避免搶同一塊資料」。 |
| `compute_perf_gflops(hardware, problem, latency)` | 把 cycle 延遲換算成 GFLOPS。 | `2·M·N·K / (latency / clock)`，給人看的吞吐量。 |

> 參數 `model`（`model_t`）預設 `gemm`，也可選 `attention`（走 `attention.cpp` 的注意力延遲模型）。

### 回傳型別

- **`prediction_result_t`**＝`{ double latency; config_t config; }`（延遲 + 對應設定）。
- **`workgroup_mapping_t`**＝`{ wgmxccchunk, wgmxcc, wgm }`。`wgm` 正值 = row-major N-slab、負值 = column-major M-slab。
- **`staggerU_t`**＝`{ staggerUMapping, staggerU, staggerUStrideShift }`。`staggerUMapping` 0=分散 B、1=分散 A；`staggerU` 是 K 偏移位置數（2 的冪、≤ 32）。

## Python 最小範例

（改寫自官方 [../../shared/origami/README.md](../../shared/origami/README.md)）

```python
import origami

# 1) 取硬體資訊（裝置 0）
hardware = origami.get_hardware_for_device(0)

# 2) 描述問題：2048^3 的 fp16 GEMM
problem = origami.problem_t()
problem.size = origami.dim3_t(2048, 2048, 2048)   # M, N, K
problem.batch = 1
problem.a_transpose = origami.transpose_t.T
problem.b_transpose = origami.transpose_t.N
problem.a_dtype = problem.b_dtype = origami.data_type_t.Half
problem.c_dtype = problem.d_dtype = origami.data_type_t.Half
problem.mi_dtype = origami.data_type_t.Half

# 3) 一堆候選 config
configs = []
c = origami.config_t()
c.mt = origami.dim3_t(256, 256, 64)   # macro tile
c.mi = origami.dim3_t(16, 16, 32)     # matrix instruction
c.occupancy = 4
configs.append(c)
# ... 通常會塞很多個不同 mt / mi 的候選 ...

# 4) 選最快的
best = origami.select_config(problem, hardware, configs)
print("best latency:", best.latency)
print("best MT:", best.config.mt.m, best.config.mt.n, best.config.mt.k)
```

`selector.py` 還提供 PyTorch / Triton 導向的包裝 `OrigamiMatmulSelector`（吃 Triton 風格的 `BLOCK_M/N/K`、`waves_per_eu`，自動對映 torch dtype 後呼叫 `rank_configs`）與 `OrigamiAttentionSelector`。

## C++ 最小範例

```cpp
#include "origami/origami.hpp"
#include "origami/types.hpp"

auto hardware = origami::hardware_t::get_hardware_for_device(0);

origami::problem_t problem;
problem.size = {2048, 2048, 2048};        // M, N, K
problem.batch = 1;
problem.a_transpose = origami::transpose_t::T;
problem.b_transpose = origami::transpose_t::N;
problem.a_dtype = problem.b_dtype = origami::data_type_t::Half;
problem.c_dtype = problem.d_dtype = origami::data_type_t::Half;
problem.mi_dtype = origami::data_type_t::Half;

std::vector<origami::config_t> configs;
origami::config_t c;
c.mt = {256, 256, 64};
c.mi = {16, 16, 32};
c.occupancy = 4;
configs.push_back(c);

auto best = origami::select_config(problem, hardware, configs);
double gflops = origami::compute_perf_gflops(hardware, problem, best.latency);
```

> 注意 `config` 的 `is_valid()` 要求 `mt`、`mi` 各維 > 0 且 `occupancy > 0`；無效 config 會在 `rank_configs` 被擋掉或丟例外。

## Build 與測試

Origami 是 `shared/origami/` 底下自成一格的 CMake 專案（需要 ROCm / HIP）。

```bash
cd shared/origami
cmake -S . -B build/ \
  -DCMAKE_PREFIX_PATH=/opt/rocm \
  -DCMAKE_CXX_COMPILER=/opt/rocm/bin/amdclang++ \
  -DORIGAMI_ENABLE_PYTHON=ON \
  -DORIGAMI_BUILD_TESTING=ON
cmake --build build/ --parallel
ctest --test-dir build/ --output-on-failure
```

**CMake 選項**：

| 選項 | 預設 | 說明 |
|------|------|------|
| `ORIGAMI_BUILD_SHARED_LIBS` | 獨立建置 ON / 併入 rocm-libraries 時 OFF | 共享 vs 靜態庫。 |
| `ORIGAMI_ENABLE_PYTHON` | OFF | 是否 build Python bindings（nanobind）。 |
| `ORIGAMI_BUILD_TESTING` | OFF | 是否 build C++ / Python 測試。 |
| `ORIGAMI_ENABLE_FETCH` | ON | 用 FetchContent 自動抓 Catch2 / rocm-cmake。 |

**Python 安裝**（scikit-build-core，內部走 CMake）：

```bash
pip install git+https://github.com/ROCm/rocm-libraries.git#subdirectory=shared/origami/python
# 或本地：cd shared/origami/python && pip install -e .
```

**測試涵蓋**：C++ 測試在 `tests/`（`test_origami.cpp` 驗排序遞增、決定性 tie-break、WGM / staggerU 規則、Formocast 模式、hash…），Python 測試在 `python/tests/`（含 `test_ranking_regression.py`，比對各架構 `baselines/rankings/gfx*.yaml` 的 golden 排名）。當作**跨 build 迴歸網**：改了模型後看排名有沒有跑掉。

## Debug logging：把模型內部值 dump 出來

想知道模型「怎麼算出這個延遲」，開 debug logging（見官方 README「Debug Logging」段）：

```bash
export ANALYTICAL_GEMM_DEBUG=1        # 打開 debug code path（必要）
export ORIGAMI_LOG_FILE=/tmp/origami.log      # .log/.txt → 人類可讀
# 或：
export ORIGAMI_LOG_FILE=/tmp/origami.csv      # .csv → 每次 GEMM 評估一列，適合批次分析
```

- 副檔名決定格式：`.csv` 走 CSV（欄位含 `M, N, K, L_mem, L_compute, H_mem_l2_A, total_latency` …），其餘走文字。
- CSV 模式一次評估一列，很適合把「不同問題 / config 下模型的各項中間值」倒出來畫圖分析（例如驗證 cache 命中率估得對不對）。

**相關環境變數**：

| 變數 | 作用 |
|------|------|
| `ANALYTICAL_GEMM_DEBUG` | 設 `1` 打開 debug code path。 |
| `ORIGAMI_LOG_FILE` | 日誌路徑；`.csv` → CSV，其他 → 文字。 |
| `ANALYTICAL_GEMM_HEURISTICS_VARIANCE` | 調 tie-break 的「算平手」相對容差（預設約 1%，見 [latency-model.md](latency-model.md)）。 |
| `ANALYTICAL_GEMM_HEURISTICS` | 是否啟用 heuristics。 |

## 一句話總結

> **餵 `rank_configs`「problem + hardware + 候選 configs」拿回排序好的結果；`config_t.index` 讓你把結果對回自己的 solution；`estimation`（預設，快）忽略 `tensile_params_t`，`simulation` 才走 Formocast 讀它。** 需要看模型內部就開 `ANALYTICAL_GEMM_DEBUG=1` + `ORIGAMI_LOG_FILE=*.csv`。它怎麼被 hipBLASLt 呼叫見 [hipblaslt-integration.md](hipblaslt-integration.md)；這些型別 / 函式在原始碼的位置與呼叫圖見 [source-map.md](source-map.md)。
