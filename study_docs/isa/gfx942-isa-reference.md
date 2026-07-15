# gfx942 / CDNA3 ISA 指令速查表

> **狀態：P1 opcode 字典（已擴充）。** 本文是「讀真實 GEMM 組語時的 opcode 字典」。對應 roadmap：
> **P1 / 07-03、07-07**（讀 ex03 與真實 GEMM kernel）。搭配 [amd-isa-kernel.md](../amd-isa-kernel.md) 的指令家族
> 表（階段 A/B）與 [mfma-deep-dive.md](mfma-deep-dive.md)（矩陣指令詳表）一起看。

## 白話總覽

讀 GPU 組語不是「逐行翻譯」，而是「認得每條指令屬於哪一類、在等哪個 counter」。gfx942 的指令可以粗分成
**五大類**，這張速查表就照這五類編排：

| 類別 | 前綴 | 白話 | 誰在動 |
|------|------|------|--------|
| **Scalar（SALU / SMEM）** | `s_*` | 整個 wave 共用一份的純量運算、控制流、常數載入 | SGPR |
| **Vector ALU（VALU）** | `v_*` | 每個 lane 各算各的算術/邏輯 | VGPR |
| **Global / Buffer 記憶體** | `global_*` / `buffer_*` | 從 HBM 讀寫（GEMM 搬 A/B/C tile 的主力） | VGPR ↔ HBM |
| **LDS（DS）** | `ds_*` | workgroup 內共享 scratchpad 的讀寫 | VGPR ↔ LDS |
| **Matrix（MFMA）** | `v_mfma_*` / `v_smfmac_*` | 矩陣乘加（GEMM 算力核心） | VGPR / AGPR |

最關鍵、最容易卡住的不是「這條指令做什麼」，而是**「為什麼中間插這麼多 `s_waitcnt`」**——因為記憶體指令是
「發出去就往下跑、不等資料回來」，要靠 **counter** 追蹤何時資料到位。所以本文先講 counter 模型，再逐類列指令。

> 平台定位：本表聚焦 **gfx942 / MI300 / CDNA3（本 repo 實驗平台）**。第一手權威是
> [`../../../amd-instinct-mi300-cdna3-instruction-set-architecture.pdf`](../../../amd-instinct-mi300-cdna3-instruction-set-architecture.pdf)
> （指令語意的整理見 [../internal_docs/cdna3-mi300-architecture-and-isa.md](../internal_docs/cdna3-mi300-architecture-and-isa.md) §3）。

## 為何重要

asm 範例（`asm/example0[1-4]_*`）註解清楚，但讀 TensileLite 產出的真實 kernel 時會遇到範例沒出現的指令
（`s_nop`、`s_setprio`、`global_load_dwordx2/x4`、`ds_read_b64/b128`、`v_readlane_b32`、`v_accvgpr_read_b32`、
`s_waitcnt_vscnt` 等）。有一張速查表，就不必每次翻 561 頁的官方 ISA 手冊。本表每條指令給三件事：
**語意一句話 / 相關 counter / 在哪個範例可見**（範例欄以本機 `asm/example0[1-4]_*` 的 `.s` 實際出現為準；
真實 kernel 才會用到的指令標「真實 kernel」）。

---

## 1. Counter 模型（讀 `s_waitcnt` 的核心）

**白話：** GPU 為了掩蓋延遲，記憶體指令「發出去就繼續往下跑」，不等資料回來。硬體用幾個**計數器
（counter）**追蹤「還有幾筆沒完成」；`s_waitcnt` 就是「**等某個 counter 降到某值以下再繼續**」。少數硬體
無法自動解的相依，要程式自己插 `s_waitcnt`，否則會讀到舊值。(ISA p.19)

| Counter | 位寬 | 計的是（哪些指令會讓它 +1，完成時 −1） | `s_waitcnt` 寫法 | 白話 |
|---------|------|------------------------------------------|------------------|------|
| **vmcnt** | 6-bit | VMEM **載入**：`global_load_*`、`buffer_load_*`、`flat_load_*` 的資料回傳 | `s_waitcnt vmcnt(0)` | 等 global/buffer load 的資料回來 |
| **lgkmcnt** | 4-bit | **L**DS（`ds_read/ds_write`）+ **G**DS + **K**（scalar/constant 讀，`s_load_*`）+ **M**essage | `s_waitcnt lgkmcnt(0)` | 等 `ds_read` / `s_load` 完成 |
| **vscnt** | — | VMEM **儲存**：`global_store_*`、`buffer_store_*` 的完成（gfx9 系列獨立計數） | `s_waitcnt_vscnt null, 0` | 等 store 真的寫出去 |
| **expcnt** | 3-bit | export / GDS（compute GEMM 幾乎用不到，多見於圖形） | `s_waitcnt expcnt(0)` | 等輸出完成 |

要點（讀組語時的直覺）：

- **`s_waitcnt lgkmcnt(0)`** 幾乎總是出現在 **`s_load` 之後**（等 kernarg 載完）與 **`ds_read` 之後**
  （等 LDS 資料進 VGPR 才能餵給運算）。範例 ex01/ex02/ex03 到處都是。
- **`s_waitcnt vmcnt(0)`** 出現在 **`global_load` 之後**（等 A/B tile 從 HBM 回來）。
- 一條 `s_waitcnt` 可同時等多個 counter：`s_waitcnt vmcnt(0) lgkmcnt(0)`。括號裡的數字是「**還允許幾筆未完成**」，
  `(0)` = 全部等完；`vmcnt(1)` = 允許還有 1 筆 load 在飛（讓最舊的先用、最新的繼續飛，是 prefetch 常見手法）。
- **loads 走 vmcnt、stores 走 vscnt**（gfx9/CDNA3 把 store 拆出獨立的 vscnt，對應組語 `s_waitcnt_vscnt`）。
  真實 GEMM kernel 寫回 C 時會用 `s_waitcnt_vscnt`；手寫範例 ex01/ex02 為求簡單，store 後直接用 `s_waitcnt vmcnt(0)`。
- **回傳次序**：不同型別的 VMEM 回傳可能亂序，同型別依發出順序回；scalar-memory-read 例外，只能用
  `s_waitcnt 0` 等它。(ISA p.19)
- 到 **CDNA5 / gfx1250** 這套粗粒度 counter 被拆成 `s_wait_loadcnt / storecnt / dscnt / kmcnt / tensorcnt`
  等細粒度計數器（見 [../gpu_knowledge/cdna5-gfx1250.md](../gpu_knowledge/cdna5-gfx1250.md) §5）——本表是 gfx942 的模型。

> MFMA 另有一套**專屬的 wait state**（不是 counter，而是「發完 MFMA 後要隔幾條獨立指令 / `s_nop` 才能碰它的
> 暫存器」），見 [mfma-deep-dive.md §6](mfma-deep-dive.md#6-latency--throughput為何-mfma-後要等怎麼把延遲藏掉)。

---

## 2. Scalar 指令（SALU / SMEM，`s_*`）

整個 wave 共用一份純量；負責控制流、位址計算、常數/kernarg 載入。(ISA Ch.3–5, Ch.8)

| 指令 | 語意 | 相關 counter | 在哪個範例可見 |
|------|------|--------------|----------------|
| `s_load_dword` / `s_load_dwordx2/x4/x8/x16` | 從常數/kernarg 路徑載入 1/2/4/… 個 dword 到 SGPR（讀 kernel 參數、descriptor） | `lgkmcnt`（+1） | ex01/ex02/ex03/ex04（載 kernarg 指標與 M/N/K） |
| `s_waitcnt` | 等指定 counter 降到門檻以下 | 讀 counter | 全部範例 |
| `s_waitcnt_vscnt` | 等 vector store 完成（gfx9 獨立 store 計數） | `vscnt` | 真實 kernel（寫回 C）；範例未用 |
| `s_barrier` | workgroup 內同步（等所有 wave 到齊，常配 LDS staging） | — | ex01/ex02/ex03 |
| `s_nop N` | 空轉 N+1 個 cycle；MFMA 後用來排空 pipeline（見 mfma-deep-dive §6） | — | ex03（`s_nop 15`） |
| `s_setprio N` | 設定本 wave 的排程優先權（0–3）；真實 kernel 用來讓 MFMA wave 優先 | — | 真實 kernel |
| `s_mov_b32` / `s_mov_b64` | 純量搬移（`b64` 常用於還原 `exec`：`s_mov_b64 exec, s[..]`） | — | ex01/ex02/ex04 |
| `s_add_i32` / `s_add_u32` / `s_addc_u32` / `s_sub_u32` | 純量加/減；`s_addc_*`＝帶進位（64-bit 位址前進） | — | ex03（`s_add_i32`）/ ex04（`s_add_u32`+`s_addc_u32`+`s_sub_u32`） |
| `s_mul_i32` / `s_mul_hi_u32` | 純量乘（低 32 位 / 高 32 位） | — | 真實 kernel（stride 計算） |
| `s_lshl_b32` / `s_lshr_b32` | 純量左移 / 右移（`<<` 算 byte offset、`>>` 算 loop count） | — | ex02/ex03/ex04（`lshl`）、ex03（`lshr`） |
| `s_and_b32` / `s_or_b32` / `s_xor_b32` | 純量位元運算 | — | ex04（`s_and_b32`） |
| `s_cmp_lg_u32` / `s_cmp_lt_u32` / `s_cmp_eq_u32` … | 純量比較 → 設 **SCC**（`lg`＝不等、`lt`＝小於、`eq`＝等於） | 設 SCC | ex03（`s_cmp_lg_u32`）/ ex04（`s_cmp_lt_u32`） |
| `s_cselect_b32` | `dst = SCC ? src0 : src1`（依 SCC 二選一） | 讀 SCC | ex04（依邊界選 `num_records`） |
| `s_cbranch_scc1` / `s_cbranch_scc0` | 依 SCC 跳轉（`scc1`＝SCC==1 時跳，迴圈回跳常用） | 讀 SCC | ex03/ex04 |
| `s_cbranch_execz` / `s_cbranch_execnz` | 依 `exec` 是否全 0 跳轉（跳過沒有活躍 lane 的區塊） | 讀 EXEC | ex01/ex02 |
| `s_branch` | 無條件跳轉 | — | 真實 kernel |
| `s_and_saveexec_b64` | `exec &= src`，並把**舊 exec** 存到 dst（進入條件區塊、之後還原）；divergence 核心手法 | — | ex01/ex02 |
| `s_getpc_b64` / `s_setpc_b64` | 讀 / 寫 program counter（位置無關定址、跳 literal pool） | — | 真實 kernel |
| `s_endpgm` | 結束 kernel program | — | 全部範例 |

> `exec` / `SCC` / `VCC` 是控制流的三個關鍵狀態：`exec`＝每 lane 一 bit 的執行遮罩；`SCC`＝純量比較結果
> （1-bit）；`VCC`＝向量比較結果遮罩（64-bit，每 lane 一 bit）。divergence 與 exec mask 的觀念見
> [../gpu_knowledge/execution-model.md](../gpu_knowledge/execution-model.md)。

---

## 3. Vector ALU 指令（VALU，`v_*`）

每個 lane 用自己的 VGPR 各算各的。字尾 `_e32`／`_e64` 是編碼寬度（32/64-bit encoding），語意相同，讀組語時
可忽略。(ISA Ch.6)

| 指令 | 語意 | 相關 counter | 在哪個範例可見 |
|------|------|--------------|----------------|
| `v_mov_b32` | 逐 lane 搬移一個 dword | — | 全部範例 |
| `v_add_u32` / `v_add_u32_e32` | 逐 lane 整數加（算 index / 位址） | — | ex01/ex03/ex04 |
| `v_add_f32` / `v_sub_f32` / `v_mul_f32` | 逐 lane 浮點加 / 減 / 乘 | — | ex01/ex02（`v_add_f32`） |
| `v_fma_f32` | 逐 lane 浮點 fused multiply-add（`a*b+c`，非矩陣） | — | 真實 kernel（非 MFMA 的純量式 FMA） |
| `v_mul_lo_u32` / `v_mul_hi_u32` | 逐 lane 整數乘（低 / 高 32 位） | — | ex03（`v_mul_lo_u32`，算 row×K） |
| `v_lshlrev_b32` / `v_lshrrev_b32` | 逐 lane 左移 / 右移（`rev`＝shift amount 在前）；算 byte offset / 拆 tid | — | 全部（`lshlrev`）、ex03（`lshrrev`） |
| `v_and_b32` / `v_or_b32` / `v_xor_b32` | 逐 lane 位元運算（`and` 常用來取 `tid % 2^n`） | — | ex03（`v_and_b32`） |
| `v_cmp_lt_u32` / `v_cmp_eq_u32` / `v_cmp_*` | 逐 lane 比較 → 寫 **VCC**（或指定 SGPR pair）遮罩 | — | ex01/ex02 |
| `v_cndmask_b32` | `dst = VCC(lane) ? src1 : src0`（依遮罩逐 lane 二選一） | 讀 VCC | 真實 kernel |
| `v_readlane_b32` | 把某一 lane 的 VGPR 值讀到 SGPR（跨 lane） | — | 真實 kernel（reduction / broadcast） |
| `v_writelane_b32` | 把 SGPR 值寫進某一 lane 的 VGPR | — | 真實 kernel |
| `v_readfirstlane_b32` | 讀第一個活躍 lane 的值到 SGPR（把 uniform 值搬回純量域） | — | 真實 kernel |
| `v_accvgpr_read_b32` | 把 **AGPR**（累加器）搬到 arch-VGPR（MFMA epilogue 寫回前必做） | — | 真實 kernel（ex03 刻意只用 arch-VGPR，故未出現） |
| `v_accvgpr_write_b32` | 把 arch-VGPR 搬進 AGPR（初始化累加器等） | — | 真實 kernel |
| `v_pk_add_f32` / `v_pk_mul_f32` / `v_pk_fma_f16` … | packed 運算（一條算兩個 16-bit 或兩個 f32），提升低精度吞吐 | — | 真實 kernel |

> `v_accvgpr_read/write_b32` 是 MFMA kernel 的固定成本：累加器放 AGPR，epilogue 要逐個搬回 arch-VGPR 才能
> `global_store`。原因與 AGPR 模型見 [mfma-deep-dive.md §5](mfma-deep-dive.md#5-accumulator-模型arch-vgpr-vs-agpr)。

---

## 4. Global / Buffer 記憶體指令（`global_*` / `buffer_*`）

GEMM 搬 A/B/C tile 的主力。兩條路線：**Flat/Global**（用 64-bit 位址，Ch.10）與 **Buffer/MUBUF**（透過 128-bit
buffer resource descriptor「V#/SRD」定址，帶硬體邊界檢查，Ch.9）。

| 指令 | 語意 | 相關 counter | 在哪個範例可見 |
|------|------|--------------|----------------|
| `global_load_dword` / `_dwordx2` / `_dwordx4` | 從 global memory 載入 1/2/4 個 dword 到 VGPR（`x4` 向量化＝少發指令、拉滿頻寬） | `vmcnt`（+1） | ex01/ex03（`dword`）、ex02（`dwordx4`，向量化優化） |
| `global_store_dword` / `_dwordx2/x4` | 把 VGPR 寫回 global memory | `vscnt`（store）；範例用 `vmcnt` | ex01/ex02/ex03 |
| `buffer_load_dword{,x2,x4}` | 透過 SRD（V#）載入（帶 range check） | `vmcnt` | 真實 kernel（GEMM 常用 buffer 路線） |
| `buffer_store_dword{,x2,x4}` | 透過 SRD 寫回（帶 range check） | `vscnt` | ex04（`buffer_store_dwordx4 … offen offset:16 nt`） |

**位址修飾符（modifier）**——讀 buffer 指令時要一起看：

| 修飾符 | 意思 | 白話 |
|--------|------|------|
| `offen` | Offset Enable：位址 = SRD base + **per-lane VGPR offset** | 每個 lane 自己一個 offset（ex04 用 v4） |
| `idxen` | Index Enable：加上 per-lane index × stride | 結構化陣列索引（範例未用） |
| `offset:N` | 立即（immediate）byte offset，疊加在上面 | ex04 用 `offset:16`（跳過前 16 bytes） |
| `glc` | Globally Coherent：load 繞過/強制 L1 一致；atomic 回傳運算前的舊值 | 需要跨 wave 看到最新值時用 |
| `slc` | System Level Coherent：視為 non-temporal、略過某些 cache 層 | 大量串流、不想污染 cache |
| `nt` | Non-Temporal：串流提示，資料用一次就走、別留 cache | ex04 的 `nt` |
| `sc0` / `sc1` | scope / temporal 的 cache 控制位（gfx942 的 cache scope 語意） | 精確語意查 ISA 手冊 |

> Buffer 的 **range check**：對 Raw Buffer（stride==0）而言，`out of range iff (inst_offset + (offen ? vgpr_offset : 0)) >= num_records`
> ——比對的是 **offset 對 `num_records`**，不是 base。ex04 就是靠「base 前進時同步遞減 `num_records`」把邊界窗
> 釘在真實配置尾端，示範越界 store 的行為（SRD/V# 的 128-bit 佈局見 ex04 `.s` 檔頭註解）。`buffer_load` 可直接
> 寫進 LDS（繞過 VGPR），是 GEMM prefetch 的常見手法。

---

## 5. LDS 指令（Data Share / DS，`ds_*`）

把 global 載入的 tile 先擺進 LDS、再由各 lane 讀出餵給 MFMA。用**立即 offset** 定址。(ISA Ch.11)

| 指令 | 語意 | 相關 counter | 在哪個範例可見 |
|------|------|--------------|----------------|
| `ds_write_b32` / `_b64` / `_b128` | 寫 1/2/4 個 dword 到 LDS（`b128` 一次搬 16 bytes，向量化更省指令） | `lgkmcnt`（+1） | ex01/ex02/ex03（`b32`）；`b64/b128` 見真實 kernel |
| `ds_read_b32` / `_b64` / `_b128` | 從 LDS 讀 1/2/4 個 dword 到 VGPR | `lgkmcnt`（+1） | ex01/ex02/ex03（`b32`）；`b64/b128` 見真實 kernel |
| `ds_read2_b32` / `ds_write2_b64` … | 一條指令做兩筆帶不同 offset 的 LDS 存取 | `lgkmcnt` | 真實 kernel |

**offset 立即值語意：** `ds_read_b32 v5, v6 offset:512` = 從「`v6` 指的 LDS 位址 + 512 bytes」讀取。offset 是
**byte** 單位的常數，編碼在指令裡（不佔額外指令算位址）。ex01 用 `offset:512 / 256 / 128 …` 做 reduction 的
跨步讀取；ex03 用 `offset:16 / 512 / 1024 / 1536` 讀 A/B 的各 K-slice。

> **LDS bank conflict** 是 LDS 存取的頭號效能陷阱（多個 lane 落在同 bank 不同 address → 序列化）。32-bank 模型、
> 觸發條件與 padding 解法見 [lds-bank-conflicts.md](lds-bank-conflicts.md)。

---

## 6. Matrix 指令（MFMA / SMFMAC）索引

> 只列家族入口，**詳細變體表、register layout、accumulator、latency 全在
> [mfma-deep-dive.md](mfma-deep-dive.md)**，這裡不重複。

| 指令族 | 語意 | 相關 counter | 在哪個範例可見 |
|--------|------|--------------|----------------|
| `v_mfma_f32_*` / `v_mfma_i32_*` / `v_mfma_f64_*` | 矩陣乘加 `D = C + A×B`（dense）；名稱編碼 `Dtype_M×N×K×B_ABtype` | MFMA 專屬 wait state（非 counter） | ex03（`v_mfma_f32_16x16x4_f32`） |
| `v_smfmac_*` | 4:2 結構化稀疏 MFMA（只有 A 稀疏） | 同上 | 真實 kernel（稀疏 GEMM） |
| `v_accvgpr_read/write_b32` | AGPR ↔ arch-VGPR 搬運（餵/取 MFMA 累加器） | — | 真實 kernel（見 §3） |

命名拆解、Cycles、lane↔element 對映、`s_nop` 要插幾個 → 見
[mfma-deep-dive.md §1、§2、§4、§6](mfma-deep-dive.md)。

---

## 7. 讀組語的常見 pattern

真實 GEMM kernel 的指令**不是隨機排列**，而是幾個固定套路。認得套路就能一眼看懂主迴圈在幹嘛：

**（1）Prologue：載入 kernarg**

```asm
s_load_dwordx2  s[4:5], s[0:1], 0x00     ; 載入 A 指標
s_load_dwordx2  s[6:7], s[0:1], 0x08     ; 載入 B 指標
s_load_dword    s12,    s[0:1], 0x20     ; 載入 K
s_waitcnt       lgkmcnt(0)               ; ★ 等所有 scalar load 完成才能用
```

**（2）主迴圈：global → LDS → MFMA（GEMM 核心）**

```asm
global_load_dword v2, v3, s[4:5]         ; 從 HBM 載 A/B tile
s_waitcnt         vmcnt(0)               ; ★ 等 load 資料回來
ds_write_b32      v6, v2                 ; 寫進 LDS staging
s_barrier                                ; ★ 等全 workgroup 都寫完
ds_read_b32       v18, v8                ; 從 LDS 讀回 VGPR
s_waitcnt         lgkmcnt(0)             ; ★ 等 LDS 讀完
v_mfma_f32_16x16x4_f32 v[4:7], v18, v22, v[4:7]  ; 累加進 D（可連發多條）
```

**（3）真實 kernel 的進階手法**（見 [amd-isa-kernel.md](../amd-isa-kernel.md) 階段 B）：

| 在組語裡看到 | 對應手法 |
|--------------|----------|
| 主迴圈前先做一輪 `global_load`（領先一個迭代） | **prefetch**：先載下一塊蓋延遲 |
| 兩組 LDS buffer 輪流讀寫 | **double buffer** |
| 一批 `ds_read` 與一批 `v_mfma` 交錯、中間夾 `s_waitcnt lgkmcnt(N)` | 用 prefetch 填 MFMA 延遲空檔 |
| MFMA 後 `s_nop` 或改讀累加器前的等待 | MFMA wait state（見 mfma-deep-dive §6） |

**（4）Epilogue：寫回 C**

```asm
v_accvgpr_read_b32 v0, a0                ; （真實 kernel）累加器 AGPR → arch-VGPR
...
global_store_dword v3, v2, s[6:7]        ; 寫回 HBM
s_waitcnt_vscnt    null, 0               ; （真實 kernel）等 store 完成
s_endpgm                                 ; 結束
```

---

## 8. 名詞（Terminology）

- **SALU / VALU** — 純量 / 向量算術邏輯單元；`s_*` / `v_*` 指令。
- **SMEM / MUBUF / DS** — scalar memory（`s_load`）/ buffer memory（`buffer_*`）/ data share（`ds_*`）指令類。
- **counter（vmcnt / lgkmcnt / vscnt / expcnt）** — 追蹤未完成記憶體指令的計數器，`s_waitcnt` 依它同步。
- **SCC** — 純量比較結果（1-bit），`s_cmp_*` 設定、`s_cbranch_scc*` / `s_cselect` 讀取。
- **VCC** — 向量比較結果遮罩（64-bit），`v_cmp_*` 設定、`v_cndmask` 讀取。
- **EXEC** — 執行遮罩（每 lane 一 bit），控制哪些 lane 真的執行；`s_and_saveexec` / `s_cbranch_execz` 操作它。
- **SRD / V#（buffer resource descriptor）** — 128-bit 描述子，記 base / stride / `num_records` / format，供 buffer 指令定址與邊界檢查。
- **offen / offset / glc / slc / nt** — buffer 定址與 cache 修飾符（見 §4）。
- **AGPR / arch-VGPR** — 矩陣累加專用 / 一般向量暫存器；`v_accvgpr_read/write` 在兩者間搬運（見 [mfma-deep-dive.md](mfma-deep-dive.md)）。
- **`_e32` / `_e64`** — VALU 指令的 32/64-bit 編碼寬度，語意相同。

---

## 9. 交叉連結

- 指令家族總覽 + 怎麼反組譯 + 階段 A/B：[../amd-isa-kernel.md](../amd-isa-kernel.md)
- MFMA 矩陣指令詳表（變體 / layout / accumulator / latency / 微架構）：[mfma-deep-dive.md](mfma-deep-dive.md)
- WMMA 對照（RDNA / CDNA5）：[wmma-deep-dive.md](wmma-deep-dive.md)
- LDS 32-bank 與 bank conflict：[lds-bank-conflicts.md](lds-bank-conflicts.md)
- 指令語意第一手整理（`s_waitcnt` / counter / 暫存器 / MFMA）：[../internal_docs/cdna3-mi300-architecture-and-isa.md](../internal_docs/cdna3-mi300-architecture-and-isa.md) §3
- 官方 ISA PDF 索引：[spec-sources.md](spec-sources.md)
- 產品線 ↔ gfx 對照：[amd-datacenter-gpu-isa.md](amd-datacenter-gpu-isa.md)
- 執行模型（wave / exec mask / divergence）：[../gpu_knowledge/execution-model.md](../gpu_knowledge/execution-model.md)
- 頂層學習地圖：[../README.md](../README.md)

## 一句話總結

> **讀 gfx942 GEMM 組語＝認五類指令（`s_*` 純量控制流 / `v_*` 逐 lane 算術 / `global_*`·`buffer_*` 讀寫 HBM /
> `ds_*` 讀寫 LDS / `v_mfma_*` 矩陣乘加）＋看懂 `s_waitcnt` 等的是哪個 counter（vmcnt 等 load、lgkmcnt 等
> LDS/scalar、vscnt 等 store）。抓住「prologue 載參數 → 主迴圈 global→LDS→MFMA → epilogue 寫回」這條主幹，
> 再對照本表逐條認指令，任何 TensileLite 產出的 kernel 都讀得動。**
