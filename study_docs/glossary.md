# 名詞彙總 Glossary（跨文件）

> **狀態：outline，待擴充。** 目前各 study_docs 末尾都有自己的 Terminology 區；本文要把它們
> 彙整成單一查詢點。對應 roadmap：**P0 全程**（隨時查名詞）。

## 為何重要

名詞散在各文件，查一個詞要翻多檔。這份彙總把核心名詞集中一處，新名詞第一次出現時也統一在此定義。

## 本文件將涵蓋（大綱，待逐條補定義）

- 硬體：wave / lane、VGPR / SGPR / AGPR、CU、XCD、LDS、HBM、L2、occupancy
- ISA：exec mask、`s_waitcnt`（vmcnt / lgkmcnt）、MFMA、buffer SRD / `num_records`、bank conflict
- GEMM/Tensile：tile（MacroTile）、DepthU、GlobalSplitU（GSU）、LocalSplitU、MatrixInstruction、
  solution / solution index、ProblemType、SizeMapping、epilogue
- 系統：build-time vs runtime、code object（`.co`）、選擇表（`.dat`，MessagePack）、lazy load、
  heuristic、nearest-neighbor

## 目前可先看的替代資源

- 各 study_docs 檔末「Terminology」段（`README.md`、`hipblaslt/*.md`、`amd-isa-kernel.md`）
