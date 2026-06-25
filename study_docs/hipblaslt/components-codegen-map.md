# Components/ codegen 目錄地圖

> **狀態：outline，待擴充。** 對應 roadmap：**P1 / 07-08** 與 **P3 第 2 層 codegen 優化**。
> 文件補齊前用下方替代資源（`Component.py` 是註冊機制、`kernelBody()` 是組裝點）。

## 為何重要

P3 第 2 層優化要改 codegen，但 `Components/` 有數十個檔。學習者需要一張「想改 X 行為 → 開哪個
Component 檔」的地圖，否則會迷失在數萬行 Python 裡。

## 本文件將涵蓋（大綱）

- 組裝點：`KernelWriter.py::kernelBody()`（約 L5279）如何串起各 Component
- 註冊機制：`Component.py` 的 `ComponentMeta` + `Component.find()`（依 archCaps/kernel partial-match）
- 主要 Component → 職責 一覽：
  - `MAC_*.py`：發 MFMA / FMA（連結 mfma-deep-dive.md）
  - `LocalRead.py` / `TensorDataMover.py`：LDS↔VGPR、global→LDS 搬運
  - `GlobalWriteBatch.py`：輸出 tile 寫回 HBM
  - `SIA.py` / `CustomSchedule.py`：指令排程（prefetch / 交錯）
  - `GSU.py` / `LSU.py` / `StreamK.py`：K 切分與 persistent kernel 排程
- 「我要改 prefetch / 排程 / read-write / MFMA 發射」分別動哪個檔

## 目前可先看的替代資源

- `projects/hipblaslt/tensilelite/Tensile/Components/`（直接看目錄）
- `study_docs/hipblaslt/gemm-optimization.md`「三個調整層級」
- `study_docs/amd-isa-kernel.md`「階段 B」
