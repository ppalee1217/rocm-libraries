# gfx942 / CDNA3 ISA 指令速查表

> **狀態：outline，待擴充。** 本文要當「讀真實 GEMM 組語時的 opcode 字典」。對應 roadmap：
> **P1 / 07-03、07-07**（讀 ex03 與真實 GEMM kernel）。文件補齊前用下方替代資源。

## 為何重要

asm 範例註解清楚，但讀 TensileLite 產出的真實 kernel 時會遇到範例沒出現的指令
（`s_nop`、`s_setprio`、`global_load_dwordx2/x4`、`ds_read_b64/b128`、`v_readlane_b32`、
`s_waitcnt_vscnt` 等）。需要一張速查表，不必每次翻官方 ISA 手冊。

## 本文件將涵蓋（大綱）

- Scalar：`s_load_*`、`s_waitcnt`（vmcnt/lgkmcnt/vscnt）、`s_barrier`、`s_nop`、`s_setprio`、
  `s_branch/s_cbranch_*`、`s_and_saveexec_b64`、`s_cselect_b32`
- Vector ALU：`v_add/mul/fma_f32`、`v_mov_b32`、`v_cmp_*`、`v_readlane/writelane`
- Global/Buffer memory：`global_load/store_dword{,x2,x4}`、`buffer_load/store_* offen offset nt`
- LDS：`ds_read/write_b32/b64/b128`、offset 立即值語意
- Matrix：`v_mfma_*` 家族索引（詳細表在 mfma-deep-dive.md）
- 每條：語意一句、用到的 counter、在哪個 asm 範例可見

## 目前可先看的替代資源

- `asm/example0[1-4]_*` 的 `.s` 註解與 README
- `study_docs/amd-isa-kernel.md` 的指令家族表
- 連結：mfma-deep-dive.md、lds-bank-conflicts.md
