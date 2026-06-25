# Tuning config 參數速查（ForkParameters）

> **狀態：outline，待擴充。** 對應 roadmap：**P1 / 07-06、07-08** 與 **P2~P3**（調參）。
> 文件補齊前用下方替代資源（`ValidParameters.py` 有定義與註解、`f32_gsu.yaml` 是最小範例）。

## 為何重要

調 tuning config 是「被 tensilelite 採用」最低風險的優化路徑（第 1 層）。學習者編輯 YAML 時需要
一張「參數 → 控制什麼硬體行為 → 合法範圍」的本地速查表，不必每次翻 Python 原始碼。

## 本文件將涵蓋（大綱）

- config YAML 骨架：`GlobalParameters` / `BenchmarkProblems`（ProblemType + ForkParameters）/
  `BenchmarkFinalParameters`
- 核心 fork 參數表（每個：作用、合法範圍、對 kernel 的影響）：
  - `MatrixInstruction` {M,N,K,B}、`WorkGroup`、`DepthU`
  - `GlobalReadVectorWidthA/B`、`LocalReadVectorWidth`
  - `GlobalSplitU`、`LocalSplitU`、`WorkGroupMapping`
  - `PrefetchGlobalRead`、`ScheduleIterAlg`、`1LDSBuffer`、`TransposeLDS`
- 衍生關係：`MacroTile0 = WaveM*WaveTileM*M` 等（連結 Solution.py::assignDerivedParameters）
- 量測對照：改參數後看 `2_BenchmarkData/*.csv` 的 Gflops

## 目前可先看的替代資源

- `projects/hipblaslt/tensilelite/Tensile/Common/ValidParameters.py`（定義 + 註解）
- `projects/hipblaslt/tensilelite/Tensile/Tests/common/gsu/f32_gsu.yaml`（最小範例）
- `study_docs/hipblaslt/gemm-optimization.md`「三個調整層級」
