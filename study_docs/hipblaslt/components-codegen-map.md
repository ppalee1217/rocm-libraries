# Components/ codegen 目錄地圖

> **狀態：outline，待擴充。** 對應 roadmap：**P1 / 07-08** 與 **P3 第 2 層 codegen 優化**。
> 文件補齊前用下方替代資源（`Component.py` 是註冊機制、`kernelBody()` 是組裝點）。
> **KernelWriter 骨架與「base→asm→Components」分工的導讀已在 [kernelwriter-implementation.md](kernelwriter-implementation.md)**，本文件聚焦在 `Components/` 的檔案級職責地圖。

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

- `projects/hipblaslt/tensilelite/Tensile/Components/`（直接看目錄——檔案級職責對應仍以原始碼為準）
- `study_docs/hipblaslt/gemm-optimization.md`「三個調整層級」
- `study_docs/amd-isa-kernel.md`「階段 B」
- KernelWriter 實作導讀（`kernelBody()` 骨架、兩層排程、抽象→asm 對應表）：[kernelwriter-implementation.md](kernelwriter-implementation.md)
- 內部參考（架構脈絡，非檔案級地圖）：[internal_docs/hipblaslt-tensilelite-reference.md](../internal_docs/hipblaslt-tensilelite-reference.md)
  Module C.2（codegen pipeline、snippet architecture / StinkyTofu）；
  [internal_docs/tensilelite-kernel-generator.md](../internal_docs/tensilelite-kernel-generator.md)（參數→kernel 的產生流程）
