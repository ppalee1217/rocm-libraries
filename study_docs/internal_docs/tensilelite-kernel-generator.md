# Kernel Generator: TensileLite (GEMM Kernel Tuning Guide)

> **Source URL:** https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119/Kernel+Generator+TensileLite
> **pageId:** `1405870119`
> **Space:** MLSE · parent "GEMM Active Programs" (`1387220065`)
> **Version:** 13 (last updated 2026-06-16)
> **Fetched on:** 2026-06-27 (via Atlassian Confluence MCP, `contentFormat=markdown`)
>
> Authoritative internal guide for the TensileLite tuning config (GlobalParameters /
> BenchmarkProblems / ForkParameters / LibraryLogic), the `MatrixInstruction` 9-element
> format, the solution-naming convention, and the end-to-end tune → merge → rebuild → verify
> workflow. NOTE: the worked examples use **gfx1150 / WMMA (WavefrontSize 32)**; for our
> target **gfx942 / MFMA (wave 64)** the parameter *concepts* carry over but exact instruction
> shapes, `WavefrontSize`, and device IDs differ.

---

## 1. What Is TensileLite

TensileLite is the GEMM kernel generation and benchmarking engine embedded within AMD's
[hipBLASLt](https://github.com/ROCm/rocm-libraries/tree/develop/projects/hipblaslt/tensilelite)
library. It generates GPU-specific assembly kernels for matrix multiplication by exploring a
user-defined parameter space, benchmarking every candidate on real hardware, and selecting
the winners. At a high level it:

1. **Generates** hundreds/thousands of candidate GEMM kernels from a combinatorial parameter grid (YAML).
2. **Compiles** each candidate into GPU assembly (filtering invalid ones, e.g. exceeding register limits).
3. **Benchmarks** every valid kernel on the target GPU for each problem size (matrix shape).
4. **Reports** a CSV with the winning kernel + GFlops per shape, and optionally a library-logic YAML to integrate back into hipBLASLt.

### 1.1 The Input Configuration YAML

Three major sections: **GlobalParameters**, **BenchmarkProblems** (ProblemType +
ForkParameters + BenchmarkFinalParameters), and an optional **LibraryLogic** section.

Annotated example:

```yaml
GlobalParameters:
  PerformanceMetric: DeviceEfficiency   # or CUEfficiency
  DataInitTypeAB: 3                      # 3 = trigsin/trigcos (good for validation)
  DataInitTypeC: 3
  DataInitTypeBeta: 0                    # init beta with zeros
  DataInitTypeAlpha: 1                   # init alpha with ones
  NumWarmups: 10
  NumBenchmarks: 1
  SleepPercent: 25                       # cool-down between benchmarks (% of solution time)
  EnqueuesPerSync: 20
  SyncsPerBenchmark: 1
  MaxEnqueuesPerSync: -1
  SkipSlowSolutionRatio: 0.50            # skip solutions slower than 50% of current best during warmup
  KernelTime: True                       # kernel-level timing (more accurate than wall-clock)
  NumElementsToValidate: -1              # -1 = all, 0 = none
  CSVExportWinner: True
  CSVMergeSameProblemID: True
  ValidationPrintValids: False
  PrintSolutionRejectionReason: False
  ClientLogLevel: 2                      # 0=Error 1=Terse 2=Verbose 3=Debug

BenchmarkProblems:
  - # GEMM HHS TN
    - # ProblemType
      OperationType: GEMM
      DataType: h            # FP16 input
      DestDataType: h        # FP16 output
      ComputeDataType: s     # FP32 accumulation
      HighPrecisionAccumulate: True
      TransposeA: 1          # TN layout
      TransposeB: 0
      UseBeta: True
      UseBias: 0
      BiasDataTypeList: ['h']
      BiasTypeArgs: ['h']
      UseScaleAlphaVec: 1
      Batched: True
      Activation: True
      ActivationFuncCall: True
      ActivationType: hipblaslt_all

    - # ForkParameters (the search space)
      BenchmarkCommonParameters:
        - KernelLanguage: ['Assembly']
      ForkParameters:
        - MatrixInstruction:
          - [16, 16, 16, 1, 1, 2, 2, 2, 2]
          - [16, 16, 16, 1, 1, 2, 5, 4, 1]
          - [16, 16, 16, 1, 1, 3, 3, 2, 2]
          - [16, 16, 16, 1, 1, 8, 1, 2, 2]
        - WavefrontSize: [32]
        - DepthU: [64, 128]
        - VectorWidthA: [1]
        - VectorWidthB: [1]
        - LocalReadVectorWidth: [16]
        - ScheduleIterAlg: [1, 3]
        - PrefetchGlobalRead: [0, 2]
        - PrefetchLocalRead: [0, 1]
        - ClusterLocalRead: [0]
        - ExpandPointerSwap: [0]
        - TransposeLDS: [1]
        - LdsBlockSizePerPadA: [-1]
        - LdsBlockSizePerPadB: [-1]
        - LdsPadA: [8, 16]
        - LdsPadB: [8]
        - 1LDSBuffer: [0, 1]
        - SourceSwap: [1]

      BenchmarkFinalParameters:
        - ProblemSizes:
          - Exact: [19456, 1322, 1, 2560]    # each Exact is [M, N, Batch, K]
          - Exact: [2560, 1322, 1, 9728]
          - Exact: [3584, 4096, 1, 18944]
          # ... (more shapes)
        - BiasTypeArgs: ['h']
        - ActivationArgs:
          - [Enum: none]
```

**Section breakdown:**

- **GlobalParameters** — overall benchmarking behavior (data init, warmup/benchmark iters, sleep, validation depth, output format). Definitions live in source:
  - [GlobalParameters.py](https://github.com/ROCm/rocm-libraries/blob/develop/projects/hipblaslt/tensilelite/Tensile/Common/GlobalParameters.py) — default values + descriptions.
  - [ValidParameters.py](https://github.com/ROCm/rocm-libraries/blob/develop/projects/hipblaslt/tensilelite/Tensile/Common/ValidParameters.py) — enumeration of valid values per parameter.

  Commonly tuned GlobalParameters:

  | Parameter | Description | Example Values |
  | --- | --- | --- |
  | `PerformanceMetric` | Optimization target | `DeviceEfficiency`, `CUEfficiency` |
  | `NumWarmups` | Warmup iterations before measurement | `0`, `10`, `50` |
  | `SleepPercent` | Cool-down between runs (% of kernel time) | `0`, `25`, `50` |
  | `EnqueuesPerSync` | Kernel launches per GPU sync | `1`, `20`, `1000` |
  | `NumElementsToValidate` | Elements to validate (`-1` all, `0` none) | `-1`, `0` |
  | `SkipSlowSolutionRatio` | Skip kernels slower than this ratio of current best | `0.0`, `0.5` |

- **BenchmarkProblems** — the heart of the config:
  - **ProblemType**: operation to benchmark — data types (`DataType`, `DestDataType`, `ComputeDataType`), layout (`TransposeA`, `TransposeB`), bias/activation/batching.
  - **ForkParameters**: the search space. TensileLite generates the Cartesian product of all listed values, one candidate kernel per combination. Key: `MatrixInstruction`, `DepthU`, `WavefrontSize`, `PrefetchGlobalRead`, `PrefetchLocalRead`, `TransposeLDS`, `LdsPadA`/`LdsPadB`, `ScheduleIterAlg`, and more.
  - **BenchmarkFinalParameters**: the specific shapes (`ProblemSizes`). Each `Exact` entry is `[M, N, Batch, K]`.

- **LibraryLogic** (optional) — when present, produces `3_LibraryLogic/` (a YAML ready to integrate into hipBLASLt). Without it, only benchmark CSV is produced. It can live in a **separate** YAML to decouple kernel exploration (slow) from library generation (fast):

```yaml
GlobalParameters:
  # (values here are not critical)
  PerformanceMetric: DeviceEfficiency
  NumElementsToValidate: -1
  # ...
LibraryLogic:
    ScheduleName: "gfx1150"
    ArchitectureName: "gfx1150"
    LibraryType: "Equality"
```

Two-step workflow (both commands use the **same output dir**; step 2 reads step 1's data):

```bash
# Step 1: generate kernels + benchmark -> 1_BenchmarkProblems/ and 2_BenchmarkData/
./run_tensile.sh <yaml_with_benchmark_problems> ./output
# Step 2: generate library logic from results -> 3_LibraryLogic/
./run_tensile.sh <yaml_with_library_logic> ./output
```

### 1.2 MatrixInstruction In Depth

The most critical tuning knob. 9-element format:

```
[M, N, K, B, MIBlockM, WaveTileM, WaveTileN, WaveM, WaveN]
```

Many values are fixed by hardware + data type. Example (RDNA3.5, WMMA, HHS, TN): the instruction
is `[16,16,16,1]`, `MIBlockM=1` (B=1), `WavefrontSize=32`, so only the last four are free:

- **WaveTileM (WTM, idx 5)** — how many WMMA/MFMA instructions each wave repeats along M; each instruction makes a 16×16 C tile, so a wave covers `16*WTM` rows. More reuse from LDS, but more VGPRs.
- **WaveTileN (WTN, idx 6)** — same along N; wave covers `16*WTN` cols.
- A single wave computes a `(16*WTM) × (16*WTN)` sub-tile by executing `WTM*WTN` instructions.
- **WaveM (WM, idx 7)** / **WaveN (WN, idx 8)** — how many waves stack along M / N within one workgroup (they share LDS). Workgroup has `WaveM*WaveN` waves = `WaveM*WaveN*WavefrontSize` threads.

Resulting hierarchy:

```
Macro tile  (all waves in a workgroup)   (16*WTM*WM) x (16*WTN*WN)
   ^  x WaveM x WaveN
Wave tile   (all MIs one wave executes)  (16*WTM) x (16*WTN)
   ^  x WaveTileM x WaveTileN
MI tile     (one hardware instruction)   16 x 16
```

Worked example `[16,16,16,1,1,1,16,4,1]` on shape `[37888,1541,1,3584]`: macro tile 64×256,
128 threads (4 waves × 32), `WorkGroup [64,2,1]`, ThreadTile 8×16, 64 WMMA ops/workgroup per
K-step; tiling the full GEMM ⇒ `ceil(37888/64)=592` × `ceil(1541/256)=7` ≈ 4144 workgroups.

### 1.3 Solution Naming Convention

Every generated kernel has a deterministic name encoding its full config, e.g.:

```
Cijk_Alik_Bljk_HHS_BH_HA_S_SAV_UserArgs_MT128x96x64_MI16x16x1_SN_..._MIWT2_6_..._WS32_WG64_2_1_WGM8_...
```

| Fragment | Meaning |
| --- | --- |
| `Cijk_Alik_Bljk` | Index assignments C[i,j,k], A[l,i,k], B[l,j,k] (TN layout) |
| `HHS` | Data types: Half in, Half out, Single (FP32) compute |
| `MT128x96x64` | Macro Tile 128 × 96 with DepthU=64 |
| `MI16x16x1` | Matrix Instruction 16×16, 1 block |
| `MIWT2_6` | WaveTileM=2, WaveTileN=6 |
| `WS32` | WavefrontSize=32 |
| `WG64_2_1` | WorkGroup=[64, 2, 1] |
| `PGR2` | PrefetchGlobalRead=2 |
| `PLR1` | PrefetchLocalRead=1 |
| `SIA1` | ScheduleIterAlg=1 |
| `DU64` | DepthU=64 |
| `ISA1150` | Target ISA gfx1150 |

This lets you trace any winning kernel back to the exact YAML parameters that produced it.

## 2. How to Run TensileLite

- **2.1 Prerequisites** — a working TheRock build with PR [#3390](https://github.com/ROCm/TheRock/pull/3390) cherry-picked (adds the `tensilelite-client` build target); the `rocm-scripts` repo cloned inside TheRock (provides `run_on_board.sh`).
- **2.2 Sync to board** — `./rocm-scripts/run_on_board.sh --board <name> --build-dir <dir> tensilelite-sync` (locks the board, rsyncs the Tensile package, `rocisa`, and `tensilelite-client`, creates `run_tensile.sh`/`setup_env.sh`).
- **2.3 Run on board** — SSH in; one-time `python -m venv .venv` + `pip install -r requirements.txt` + `pip install rocm --index-url ...`; then `./run_tensile.sh /path/to/config.yaml ./output`. `run_tensile.sh` passes `--library-format=msgpack` (must match `library-file` in the generated `ClientParameters.ini`: `TensileLibrary.dat`=msgpack, `TensileLibrary.yaml`=yaml; msgpack is faster and recommended).
- **2.4 Output dirs** —
  - `1_BenchmarkProblems/` — generated asm source, compiled code objects, build artifacts per candidate.
  - `2_BenchmarkData/` — benchmark results; key file is the `..._CSVWinner.csv` whose columns describe the shape, identify `WinnerGFlops/WinnerTimeUS/WinnerIdx/WinnerName`, then list every other candidate's GFlops (fastest→slowest).
  - `3_LibraryLogic/` (only if `LibraryLogic` present) — final YAML to integrate. **Post-processing:** (1) fix `HA_S`→`HAS` naming bug; (2) replace `- fallback` with `- [Device XXXX]` (e.g. gfx1150 ⇒ `150e`; copy the value from existing solution files for your arch).

## 3. How to Interpret the Results

- **3.1 Terminal output** — one CSV line per (problem, solution, iteration): fields include `run`, `problem-progress` (e.g. `0/13`), `solution-progress` (`0/151`), `operation`, `problem-sizes` `(M,N,Batch,K)`, full `solution` name, `validation` (`PASSED`/`FAILED`/`NO_CHECK`), `time-us`, `gflops`, `total-gran`, `tiles-per-cu`, `num-cus`, `temp-edge` (°C), etc. Lets you spot failures, low GFlops, or thermal throttling live.
- **3.2 GPU capability probing (expected)** — startup `Testing instruction: ...` lines that error out are **harmless**: TensileLite probes which instructions the GPU supports and excludes the failures.
- **3.3 Assembly generation failures (expected)** — `Failed to generate assembly ... total vgpr: 291 not in [0, 256]` etc. are **expected**: invalid parameter combos (over VGPR/LDS limits) are silently skipped; only valid survivors are benchmarked.
- **3.4 Validation failures at extreme values (known issue)** — with `NumElementsToValidate: -1`, FP16 saturation differs from the CPU reference (`65504 != inf`, `-65504 != -inf`). The GPU result (saturating to ±65504, the max FP16) is **actually correct**; solutions marked `FAILED` only for this reason are safe.

## 4. How to Integrate the New Results

1. **4.1 Rsync existing library** to the remote machine (e.g. `.../Tensile/Logic/asm_full/gfx1150/Equality`).
2. **4.2 Merge** with `Tensile/bin/TensileMergeLibrary <existing_folder> <3_LibraryLogic_folder> <existing_folder>` (after applying the `HA_S`→`HAS` and `fallback`→`[Device XXXX]` fixes).
3. **4.3 Rsync merged library back** to the build host.
4. **4.4 Rebuild** `ninja -C <build> hipBLASLt+expunge && ninja -C <build> hipBLASLt` (`+expunge` forces clean re-generation from updated logic).
5. **4.5 Verify with hipblaslt-bench** — key flags: `--algo_method all` (enumerate every solution, not just winner), `--print_kernel_info` (print solution/kernel names — **critical**), `--cold_iters 1 --iters 1` (just confirm existence), plus `-m/-n/-k/--transA/--transB`/type flags matching a tuned shape. Search the output's `--Solution name:` lines for your `WinnerName` from the `2_BenchmarkData` CSV; if present, the kernel was merged and is selectable at runtime.

## Appendix: Tips for Effective Tuning

- **Start small** — a subset of `MatrixInstruction` configs + a few shapes; expand once promising regions are found.
- **Disable validation for speed** — `NumElementsToValidate: 0` during exploration; `-1` only for final verification.
- **Tune `DepthU` for your K** — larger (128, 160) for compute-bound / large K; smaller (32, 64) for memory-bound / small K.
- **`TransposeLDS` and `LdsPadA`/`LdsPadB` are critical** — they control LDS bank conflicts and make a large difference.
- **`PrefetchGlobalRead` / `PrefetchLocalRead`** — try 0/1/2 (note `PrefetchLocalRead: 2` may produce incorrect kernels in some configs).
- **`ScheduleIterAlg`** — values `1` and `3` typically best.
- **Monitor thermals** — use `SleepPercent` (25–50) + `NumWarmups` to avoid throttling skew on long runs.

### People / contact

`KKyang` (Huang, YangWen) reviews Grid/Solutions tuning changes; ping on the GEMM Optimization Teams channel.
