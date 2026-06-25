# MFMA 深入（gfx942 / CDNA3 矩陣引擎）

> **狀態：outline，待擴充。** 對應 roadmap：**P1 / 07-01、07-03、07-07**（召喚 MFMA、讀 MFMA
> GEMM、認 MFMA 排程）。文件補齊前用下方替代資源（ex03 的 `.s` L37-41 是目前最精準的 layout 說明）。

## 為何重要

MFMA 是 GEMM 效能的核心。學習者需要超出單一範例的全貌：有哪些指令變體、accumulator 放哪、
延遲多大（決定要發幾條 MFMA 才能掩蓋 LDS read 延遲）。這直接關係 P3 的 codegen 優化。

## 本文件將涵蓋（大綱）

- 指令命名解讀：`v_mfma_<D>_<M>x<N>x<K>_<AB型別>`，{M,N,K,B} 的意義
- 變體表：常見 shape（4x4 / 16x16 / 32x32）× 型別（f32 / f16 / bf16 / i8 / fp8）
- Register layout：一個 wave 64 lane 如何持有 A/B/D（以 ex03 `.s` L37-41 為起點推廣）
- Accumulator 模型：arch-VGPR vs AGPR（ex03 刻意只用 arch-VGPR，真實 kernel 會用 AGPR）
- Latency / throughput：為何 MFMA 後需要 `s_nop`；如何用多條 MFMA + prefetch 掩蓋延遲
- 對應 codegen：`Components/MAC_*.py` 怎麼發 MFMA（連結 components-codegen-map.md）

## 目前可先看的替代資源

- `asm/example03_mfma/`：README + `.s` L37-41（layout）、L153-156（4 條 MFMA）
- `study_docs/amd-isa-kernel.md`「階段 A-3 / 階段 B」
