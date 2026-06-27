# Tuning config 參數速查（ForkParameters）

**內容主要 summary 自公司內部文件**，非從零整理。權威敘述來源：
- [internal_docs/tensilelite-kernel-generator.md](../internal_docs/tensilelite-kernel-generator.md)（Kernel Generator: TensileLite）
- [internal_docs/hipblaslt-tensilelite-reference.md](../internal_docs/hipblaslt-tensilelite-reference.md) Module C.3
- 具體參數範例見 [internal_docs/tensilelite-yaml-config-kernel-a-e.md](../internal_docs/tensilelite-yaml-config-kernel-a-e.md)

**合法值的最終真相仍以原始碼為準**（[ValidParameters.py](../../projects/hipblaslt/tensilelite/Tensile/Common/ValidParameters.py) / [GlobalParameters.py](../../projects/hipblaslt/tensilelite/Tensile/Common/GlobalParameters.py)）。對應 roadmap：**P1 / 07-06、07-08** 與 **P2~P3**（調參）。

> ⚠️ **架構差異**：內部 guide 的 worked example 多為 **gfx1150 / WMMA（`WavefrontSize 32`）**；我們的 target 是 **gfx942 / MFMA（wave 64）**——參數「概念」一致，但指令形狀、`WavefrontSize`、device ID 不同，數值請以本機 [f32_gsu.yaml](../../projects/hipblaslt/tensilelite/Tensile/Tests/common/gsu/f32_gsu.yaml) 與 [ValidParameters.py](../../projects/hipblaslt/tensilelite/Tensile/Common/ValidParameters.py) 為準。

## 為何重要

調 tuning config 是「被 tensilelite 採用」最低風險的優化路徑（第 1 層）。編輯 YAML 時需要一張
「參數 → 控制什麼硬體行為 → 合法範圍」速查表，不必每次翻 Python 原始碼。

## config YAML 骨架

一份 config 有三大區段（完整註解範例見內部 guide §1.1）：

- **`GlobalParameters`** — 整體 benchmark 行為：`PerformanceMetric`（`DeviceEfficiency`/`CUEfficiency`）、
  `NumWarmups`、`SleepPercent`（降溫，避免熱節流）、`EnqueuesPerSync`、`NumElementsToValidate`
  （`-1`=全驗 / `0`=不驗，探索期設 0 加速）、`SkipSlowSolutionRatio`、`KernelTime`。
- **`BenchmarkProblems`** = `ProblemType`（op / 型別 `DataType`/`DestDataType`/`ComputeDataType` /
  layout `TransposeA`/`TransposeB` / bias / activation / batched）+ **`ForkParameters`**（搜尋空間，
  各參數值取**笛卡兒積**，每組合產一個候選 kernel）+ **`BenchmarkFinalParameters`**
  （`ProblemSizes`，每個 `Exact: [M, N, Batch, K]`）。
- **`LibraryLogic`**（選填）— 有才會產 `3_LibraryLogic/`（可整合進 hipBLASLt 的 YAML）。可拆成獨立
  YAML，把「慢的 kernel 探索」與「快的 library 產生」分兩步（同一 output 目錄，步驟 2 讀步驟 1 結果）。

## 核心 fork 參數速查

| 參數 | 作用 | 常見值 / 備註 |
|---|---|---|
| `MatrixInstruction` | 9 元素 `[M,N,K,B,MIBlockM,WaveTileM,WaveTileN,WaveM,WaveN]`，決定 tile 幾何（最關鍵） | 見下節 |
| `DepthU` | K 方向 unroll 深度 | 大 K/compute-bound 用大值（128,160）；小 K/memory-bound 用小值（32,64） |
| `WavefrontSize` | wave 大小 | gfx942=64；內部 WMMA 範例=32 |
| `PrefetchGlobalRead`（`PGR`） | 提前載入下一輪 global 資料（延遲掩蓋） | 0/1/2 都試 |
| `PrefetchLocalRead`（`PLR`） | 提前 LDS→VGPR | 0/1（`2` 在某些組合會產錯誤 kernel） |
| `ScheduleIterAlg`（`SIA`） | 指令排程策略 | 通常 `1` 或 `3` 最好 |
| `TransposeLDS` / `LdsPadA` / `LdsPadB` | 控 LDS bank conflict | **對效能影響大**，務必掃 |
| `GlobalReadVectorWidthA/B` / `LocalReadVectorWidth` | 向量化載入寬度（coalescing） | 連結 ex02 的 `dwordx4` 概念 |
| `GlobalSplitU`（`GSU`） / `LocalSplitU` | 把 K 切給多 workgroup/wave，輸出端需 reduction/atomic | K 很大時受益 |
| `WorkGroupMapping`（`WGM`） / `WorkGroupMappingXCC` | tile→CU/XCD 的排序（L2 局部性） | 進階；搭 `ClusterDim` |
| `1LDSBuffer` | 單/雙 LDS buffer | 0/1 |

## MatrixInstruction 與 tile 階層

9 元素中，前段（`M,N,K,B,MIBlockM`）多由硬體 + 型別固定，**真正自由的常是後四個**
`WaveTileM/WaveTileN/WaveM/WaveN`：

```
Macro tile (一個 workgroup 全部 wave)   (16*WTM*WM) x (16*WTN*WN)
   ^  x WaveM x WaveN
Wave tile  (一個 wave 跑的所有 MI)       (16*WTM) x (16*WTN)
   ^  x WaveTileM x WaveTileN
MI tile    (一條硬體指令)                16 x 16
```

- `WaveTileM/N`：一個 wave 沿 M/N 重複幾條矩陣指令（重複越多→LDS 重用越多，但吃越多 VGPR）。
- `WaveM/N`：一個 workgroup 沿 M/N 疊幾個 wave（共用 LDS）；總 thread = `WaveM*WaveN*WavefrontSize`。
- 衍生關係（連結 [Solution.py::assignDerivedParameters](../../projects/hipblaslt/tensilelite/Tensile/SolutionStructs/Solution.py)）：`MacroTile = (16*WTM*WM) x (16*WTN*WN)`。

## Solution / kernel 命名（反推 YAML 參數）

名稱把完整 config 編進去，可從一個 kernel 名反推它的參數（片段對照見內部 guide §1.3）：

`MT128x96x64`=MacroTile 128×96 + DepthU 64、`MI16x16x1`=矩陣指令、`MIWT2_6`=WaveTileM/N、
`WS32`=WavefrontSize、`WG64_2_1`=WorkGroup、`PGR2`/`PLR1`=prefetch 深度、`SIA1`=排程、
`DU64`=DepthU、`ISA1150`=目標架構。

## 量測對照與整合

- 改參數後看 `2_BenchmarkData/*.csv` 的 `WinnerGFlops` 與各候選 GFlops（fastest→slowest）。
- 預期會看到大量「VGPR > 256 / LDS 超限」的 kernel 被靜默淘汰，以及 FP16 飽和造成的假 `FAILED`
  （`65504 != inf`），這些都是正常的（見內部 guide §3）。
- 整合：`TensileMergeLibrary` 併入既有 library → `ninja ... hipBLASLt+expunge && ninja ... hipBLASLt`
  → 用 `hipblaslt-bench --algo_method all --print_kernel_info` 確認新 kernel 名出現（內部 guide §4）。

## 目前可先看的替代資源（本機原始碼＝合法值真相）

- [ValidParameters.py](../../projects/hipblaslt/tensilelite/Tensile/Common/ValidParameters.py)（合法值定義 + 註解）
- [GlobalParameters.py](../../projects/hipblaslt/tensilelite/Tensile/Common/GlobalParameters.py)（GlobalParameters 預設值）
- [f32_gsu.yaml](../../projects/hipblaslt/tensilelite/Tensile/Tests/common/gsu/f32_gsu.yaml)（最小範例）
- [gemm-optimization.md](gemm-optimization.md)「三個調整層級」
