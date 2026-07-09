# Difference between Origami and Formocast

> **Source URL:** https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304199634/Difference+between+Origami+and+Formocast
> **pageId:** `1304199634`
> **Space:** MLSE (Machine Learning Software Engineering)
> **Version:** 13
> **Fetched on:** 2026-07-08 (via Atlassian Confluence MCP, `convert_to_markdown=true`)
>
> Origami 與 Formocast 兩個 solution-selection 預測模型的逐項對照與 code review 對比，並含整合計畫。
> Formocast 設計本身見 [formocast-design-rfc.md](./formocast-design-rfc.md)。
> 一張附圖（`image-20251128-031512.png`）未下載，僅保留 Confluence 連結。

---

## 高層對照

| Matrices | Origami | Formocast |
| --- | --- | --- |
| Performance vs Exact tuning | ~90% | ~95% |
| Solution pool | Small pool with MTs combination, Auto WGM | Any set of tensilelite parameters. Trade-off performance and selection time. (in progress) |
| Selection time | fast runtime selection | Not optimized (in progress) |
| Capability of different library | Support Triton based library | Tensilelite only |
| Capability of hipblaslt library | Support StreamK kernels only | Currently non-streamk kernels only. To support StreamK, CMS, DTL… (in progress) |
| Used tensilelite parameters | Macrotile (MT_M, MT_N, MT_K), StreamK, Matrix Instruction (e.g. 16x16x32_bf16, 32x32x16_bf16) | Macrotile (MT0, MT1, DepthU), WorkGroupMapping, CU Occupancy, GSU Method (MultipleBuffer / MultipleBufferSingleKernel), Matrix Instruction (e.g. 16x16x32_bf16, 32x32x16_bf16), PrefetchGlobalRead, VectorWidthA/B, GlobalReadVectorWidthA/B, StoreVectorWidth, DirectToVgprA/B, NumLoadsCoalescedA/B, LocalSplitU, Instruction issued cycles of loop, WaveGroup (Number of waves) |
| Used HW constants | Number of CUs (N_CU), LDS capacity, mem1/mem2/mem3_perf_ratio, L2 Cache capacity, CUs per L2 domain, Compute clock (GHz), Parallel MI/CU, Number of XCDs (NUM_XCD), mem_bw_per_wg_coefficients | L1/L2/L3 CacheCapacity, L1/L2 CacheLineSize, L1/L2 BusWidthPerCU, L1/L2 WriteBusWidthPerCU, maxBandWidthHBM, mem_frequency, hbmBandWidth, L3BandWidth, math_frequency, boost_frequency, initialCost, initialCostHit, flopsPerClk, NumCUs, wavefrontSize, L2ReadArbEff, L2WriteArbEff, NumXCDs |
| Day one effort and Scalability | ?? | ?? |
| hipblaslt tuning | Not related | Help reducing tuning time by adjusting prediction threshold |

## Code Review 對照

| Code Review | Origami | Formocast |
| --- | --- | --- |
| Main function | `rank_configs` → `compute_total_latency` → mapping to predictedPerformance; `get_runtime_options` → auto WGM | `predictedPerformance` |
| input | `const problem_t& problem, const hardware_t& hardware, const std::vector<config_t>& configs` | `SizeMapping sizeMapping; ProblemInfo problem; HardwareConstants hw_consts;` |
| Remove bad solutions | `shortCircuit` | `Early terminate` (in progress) |
| CU Occupancy | `compute_cu_occupancy` | From tensilelite (sizemapping) `Derived Problem/Workgroup Dimensions` |
| loop performance | `compute_timestep_latency`, `compute_tile_latency`, `compute_mt_compute_latency` → math clock; `compute_memory_latency` → `mem_costs` | Unrolled loop performance: `sizeMapping.MathClocksUnrolledLoop`, `mem_costs`, `getLoopOverall` |
| math clock of loop | `compute_mt_compute_latency` — compute from the matrix instruction only | Through the RocIsa API to extract the exact execution cycles, stored in `sizeMapping.MathClocksUnrolledLoop` |
| memory latency of loop | `compute_memory_latency`, `estimate_l2_hit` ← L2 hit from WGM, `compute_l2_hit_rate_global` ← L2 hit from L2 capacity, `estimate_mall_hit` ← similar to L3 hitrate in formocast; use perf_ratio for final memory latency; pick the worst-case bound; some magic numbers: `if (H_mem1 == 0) { H_mem1 = 0.5; }`, `L_mem_MEM += 200; // Load Latency` | `calculateMemoryAccessCosts` from L1/L2/L3 hit rate: `computeL1CacheHitRate`, `computeL2CacheHitRate` (real dispatcher from WGM), `computeL3CacheHitRate` from L1/L2/L3 requests; compute each L1/L2/L3 latency — do not use worst case directly |
| pre loop part | `L_prologue = 1.5 * L_mem; // 1.5 chosen empirically` | initial cost + prefetch: `getPrefetchPerformance` |
| post loop part | `Epilogue`, `compute_mem_bw_from_occupancy`, `L_epilogue += L_compute * effective_tile_penalty;` including the no-load loop | `calculateStorePerformance`, `calculateGSUOverhead`, `calculateLSUOverhead` |
| occupancy | `L_prologue = L_prologue * pow(0.95, real_occupancy);` and `L_epilogue = L_epilogue * pow(0.95, real_occupancy);` (factor chosen empirically) | `resolveOccupancy` |
| TF32 specialized code | `compute_cvt_overhead`, `compute_cvt_overhead_x1` | in Math clock |
| First kernel launch penalty | `Single-tile latency` | `initialCostHit` |
| loop count handle | `num_iter` | `loopCnt` |
| Tail loop handle | `L_epilogue += problem_k_quant * 50000;` | `Handle Tail Loop` |
| Final performance | `double L_tile_total = (L_tile_single * num_iter) + L_prologue + L_epilogue * 2 + L_WG_setup + (500 * num_iter);` (7 instructions × 4 cycles at loop end); `if (MT_K == 1024) { L_prologue = L_prologue * 100; }` | `resolveOccupancy` + LSU + GSU |

## Integration View – Quick Notes

- Origami can serve as an ideal front-end for Formocast since it already provides a complete software infrastructure and APIs. Information can be passed through these APIs.
- For prediction mode:
  - Fastest and lowest modes are straightforward.
  - Consider adding a dynamic mode. Certain problem sizes may require different accuracy levels. For example, small-K problems need higher accuracy for prefetch and store performance because the loop impact is relatively minor.
  - (附圖：[image-20251128-031512.png](https://amd.atlassian.net/wiki/rest/api/content/1304199634/child/attachment/att1304199643/download)，未下載)
- Move TensileLite-specific parts to Formocast and keep general GEMM components in Origami.
  - Example: TensileLite includes multiple split-K algorithms (StreamK, GSU MB, GSU MBSK, LSU, etc.). Keep the most general one in Origami and implement the more complex ones in Formocast.
- WGM is another example where more methods are being added to TensileLite.
- Formocast's key advantage is reducing tuning time (via `PredictionThreshold`).
- Avoid hard-coded magic numbers in both Formocast and Origami. Consider placing them in the HW constants table for better maintainability.

## Actionable Items

- Add an input argument to retrieve compute latency from `MathClocksUnrolledLoop`. If the user sets a custom math clock, use that; otherwise, default to `compute_mt_compute_latency`.
- Call `calculateGSUOverhead` so Origami can support non-StreamK kernels.
- Call `calculateLSUOverhead` to include LSU latency.
- Formocast can leverage Origami's infrastructure to refactor code and reduce duplication.

## Integration plan

The Formocast API with tensilelite tuning flow is in [hcman2/rocm-libraries at users/hcman2/formocast_pr](https://github.com/hcman2/rocm-libraries/tree/users/hcman2/formocast_pr).

### Highlights

1. Place Formocast code in a shared folder as it serves as the backend for both Origami and Tensilelite.
2. Separate Formocast API from Formocast core code.
3. Reuse the `hardware_t` and `config_t` data structures, adding sizemapping info to `config_t`.

### Steps

Since rocm-libraries is a large open source project, avoid pushing all code in one pull request. Push code in sequence.

1. Push Formocast code only. This step won't affect other code.
2. Push and reserve origami prediction mode. Pass sizemapping info through `config_t`. Use an environment variable to switch modes. This step won't affect other code.
3. Push tensilelite code using Formocast API. Run tox tests with prediction threshold to validate results.
4. Push Origami code with Formocast backend. Possibly start with one example.
5. Refine Formocast and Origami to verify API usage and identify functions to move.
6. Test Fast-Slow Hybrid mode.

A quick integration code is in this commit [[DRAFT] og test. · hcman2/rocm-libraries@1682258](https://github.com/hcman2/rocm-libraries/commit/1682258dbb536c8fa21a46076a59879ae74a9b39). Variable names and data structures may change. Initially, separate the libraries with the logic YAML: the one with Prediction is for Origami, the Freesize one is for Formocast. Control the libraries used with an environment variable. There will no longer be any `findTopSolutionsFormoCast` functions.

## Integration plan with better approach

### Highlights

1. Place Formocast code in tensilelite folder to reduce duplicated code.
2. Formocast must open all of the API Origami needs to calculate the performance info. Pass the info to origami in tensilelite.
3. Don't copy datatype and sizemapping which already exist in tensilelite.

### Steps

1. Push Formocast code to the tensilelite folder without affecting other code.
2. Push and reserve origami prediction mode. Add APIs to pass performance metrics via `config_t`. Use an environment variable to switch modes without affecting other code.
3. Push tensilelite code using Formocast API. Run tox tests with prediction threshold to validate results. **This step will enable the quick tuning.**
4. Push Origami code with Formocast backend. **This step will enable the bench with different modes. This step cannot affect Step 3.**
   1. Move prediction code to Origami. Both tensilelite tuning and hipblaslt bench use Origami's solution selection API.
   2. This initiates Origami 2.0 with a different mode.
5. Refine Formocast and Origami to verify API usage and identify functions to move.
   1. Identify functions that provide general GEMM performance metrics to improve Origami as a GEMM backend.
   2. Test Fast-Slow Hybrid mode (future work).

## Integration plan with the final approach

[[Formocast] initial code with tuning enabled by hcman2 · Pull Request #3735 · ROCm/rocm-libraries](https://github.com/ROCm/rocm-libraries/pull/3735)

### Highlights

1. Place Formocast code in an origami subfolder first.
2. Duplicate most of sizeMapping struct on the formocast/origami side.
3. Reuse origami's existing struct and unit test infra.

### Steps

1. Push Formocast code to the origami subfolder. (we are here now)
2. Submit tuning code calling the API of origami.
3. Push and reserve origami prediction mode. Add APIs to pass sizemapping data via `config_t`. Use an environment variable to switch modes without affecting other code.
4. Enable predictionThreshold with tox tests.
5. Push Origami code with Formocast backend. This step will enable the bench with different modes.
6. Refine Formocast and Origami to verify API usage and identify functions to move.
