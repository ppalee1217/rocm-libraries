# LDS 與 bank conflict（最高優先 gap）

> **狀態：outline，待擴充。** 這是現有教材最大的缺口：bank conflict 只在 counter 被提到，
> 但 32-bank 模型、觸發條件、padding 解法都沒寫。對應 roadmap：**P0 / 06-28**（理解 LDS）與
> **P3**（優化）。文件補齊前用下方替代資源。

## 為何重要

LDS 存取若發生 bank conflict，原本一拍的存取會被序列化成多拍，是 GEMM 常見隱形瓶頸。學習者要
能「從 `LDSBankConflict` counter 看出問題 → 用 padding / 改存取 stride 解決」，這是 profiling
驅動優化的關鍵一環。

## 本文件將涵蓋（大綱）

- LDS 結構：32 banks、每 bank 4 bytes 寬、bank = `(byte_addr / 4) % 32`
- 何時衝突：同一 wave 多 lane 落在同 bank 不同 address → N-way conflict 序列化
- 無衝突情形：broadcast（同址）、連續 dword（跨 bank）
- 解法：LDS padding（每列 +1 元素避開對齊衝突）、改 tile 存取 stride、向量化 `ds_read_b128`
- 量測：`LDSBankConflict` counter 怎麼讀（連結 profiling-rocprof.md）
- 在 GEMM 的應用：ex03 為何選用 stride-safe layout（目前範例未明講）

## 目前可先看的替代資源

- `study_docs/hipblaslt/profiling-rocprof.md`：`LDSBankConflict` counter
- `asm/example03_mfma/`：LDS staging（`ds_write`/`ds_read` + `s_barrier`）
