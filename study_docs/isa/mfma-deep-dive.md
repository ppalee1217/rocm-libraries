# MFMA 深入（gfx942 / CDNA3 矩陣引擎）

> **狀態：P1 深入文件（已擴充）。** 對應 roadmap：**P1 / 07-01、07-03、07-07**（召喚 MFMA、讀 MFMA
> GEMM、認 MFMA 排程）。本文以 `asm/example03_mfma/` 的 `.s` 為起點（layout 見 L37-41、4 條 MFMA 見
> L153-156），推廣到整個 MFMA 指令家族、register layout、accumulator 模型、latency 與 Matrix Core 微架構。

## 白話總覽（先建立直覺）

**一句話：** MFMA（**M**atrix **F**used-**M**ultiply-**A**dd）就是 CDNA GPU 上「一條指令算一整塊小矩陣乘加」
的指令家族——`D = C + A × B`，由 CU 裡的專屬硬體 **Matrix Core** 執行。GEMM（矩陣乘法）之所以能在 MI300 上
跑出高吞吐，全靠這一條條 MFMA。

用大白話拆解它跟你熟悉的東西差在哪：

- 一般的 `v_fma_f32` 是「**一個 lane 算一個** 乘加」（純量式，只是 64 個 lane 各算各的）。
- 一條 MFMA 是「**整個 wave 的 64 個 lane 合起來算一塊矩陣**」——例如 `16x16x16` 一次就把
  「16×16 的 A tile」乘「16×16 的 B tile」累加進「16×16 的 D tile」。同樣一條指令，做的乘加多了幾百倍。

因為「一條指令做很多事」，帶來三個學習者一定要搞懂的連帶問題，本文逐一回答：

1. **有哪些變體？** 形狀（M×N×K）× 型別（f32/f16/bf16/i8/fp8…）組合出一大張表，GEMM 到底該用哪幾個。
2. **資料放哪？** 64 個 lane 怎麼分工持有 A/B/D 的元素（register layout）；累加器放 Arch VGPR 還是 AGPR。
3. **延遲多大？** 一條 MFMA 要跑好幾個 cycle 才算完，發完不能馬上讀結果——這決定要連發幾條、怎麼穿插
   prefetch 才能把延遲藏掉。

## 為何重要

MFMA 是 GEMM 效能的核心。學習者需要超出單一範例的全貌：有哪些指令變體、accumulator 放哪、
延遲多大（決定要發幾條 MFMA 才能掩蓋 LDS read 延遲）。這直接關係 P3 的 codegen 優化——讀 TensileLite
產出的 `.s` 時，滿螢幕的 `v_mfma_*` + `s_nop` + `ds_read` 交錯，看懂它們在做什麼就是靠本文這幾張表。

> 平台定位：本文聚焦 **gfx942 / MI300 / CDNA3（實驗平台）**。CDNA4（gfx950）的新增指令另闢一節標明
> **CDNA4-only**，作為 migration 參考；WMMA（RDNA / CDNA5 那條線）另見
> [wmma-deep-dive.md](wmma-deep-dive.md)。第一手規格出處是
> [../internal_docs/cdna3-mi300-architecture-and-isa.md](../internal_docs/cdna3-mi300-architecture-and-isa.md)
> §3（整理自 MI300 ISA 手冊 Ch.7）。

---

## 1. 指令命名拆解

MFMA 指令名字本身就編碼了「做什麼」，一定要會拆：

```text
V_MFMA_<Dtype>_<M>x<N>x<K>[_<B>B]_<ABtype>
        │       │  │  │      │      └ 輸入型別（A、B 矩陣的資料型別）
        │       │  │  │      └ blocks：一次算幾個 block（沒寫 = 1）
        │       │  │  └ K：A 的寬 / B 的高（縮並維度）
        │       │  └ N：B 的寬 / D 的寬
        │       └ M：A 的高 / D 的高
        └ Dtype：輸出/累加型別（通常是 F32 或 I32）
```

- `M × N × K`：每個 block 的矩陣維度——**A 是 M×K、B 是 K×N、C/D 是 M×N**。
- `B`（`_2B` / `_4B` / `_16B`）：一次平行算幾個獨立 block；沒標就是 1 個 block。
- 語意（每個 block 各自）：`D[b,i,j] = C[b,i,j] + Σ_k A[b,i,k] × B[b,k,j]`。(ISA p.46)

### 具體例子（worked example）

`V_MFMA_F32_16x16x16_F16`：

| 欄位 | 值 | 意思 |
|------|-----|------|
| Dtype | `F32` | 累加/輸出是 FP32（低精度乘、高精度累加，避免累加誤差） |
| M×N×K | `16×16×16` | A 是 16×16、B 是 16×16、D 是 16×16 |
| B | （無） | 單一 block |
| ABtype | `F16` | A、B 的輸入資料是 FP16 |

→ 這條指令讓一個 wave 一次算完 `D(16×16) += A(16×16) × B(16×16)`，A/B 讀 FP16、累加成 F32。這正是
FP16 GEMM 最常用的主力指令之一。

範例 `asm/example03_mfma` 用的是更基礎的 `V_MFMA_F32_16x16x4_F32`（K=4、F32 輸入），K 較小所以一個 K=16
的區塊要**連發 4 條** MFMA 累加（見 L153-156），正好示範「大 K 變體 = 一條抵多條」的概念。

---

## 2. Dense MFMA 變體表（CDNA3 / gfx942）

下表整理 gfx942 常用的 dense MFMA（來源：MI300 ISA Table 28, ISA p.42；已彙整於
[cdna3 內部筆記 §3.3](../internal_docs/cdna3-mi300-architecture-and-isa.md)）。`Cycles` 是該變體的執行
pass 數——**數字越大延遲越高**，排程時要用更多獨立指令去掩蓋（見 §6）。

| 指令族 | 常見形狀（Variants） | Blocks | Cycles | 說明 |
|--------|----------------------|--------|--------|------|
| `V_MFMA_F32_*_F32` | 32x32x1_2B / 16x16x1_4B / 4x4x1_16B / 32x32x2 / **16x16x4** | 2/4/16/1/1 | 64/32/8/64/32 | F32 A&B 矩陣乘（FMA） |
| `V_MFMA_F32_*_F16` | 32x32x4_2B / 16x16x4_4B / 4x4x4_16B / **32x32x8** / **16x16x16** | 2/4/16/1/1 | 64/32/8/32/16 | F16 A&B 矩陣乘 |
| `V_MFMA_F32_*_BF16` | 32x32x4_2B / 16x16x4_4B / 4x4x4_16B / **32x32x8** / **16x16x16** | 2/4/16/1/1 | 64/32/8/32/16 | BF16 A&B 矩陣乘 |
| `V_MFMA_I32_*_I8` | 32x32x4_2B / 16x16x4_4B / 4x4x4_16B / **32x32x16** / **16x16x32** | 2/4/16/1/1 | 64/32/8/32/16 | I8 A&B（輸出 I32） |
| `V_MFMA_F32_*_XF32` | 16x16x8 / 32x32x4 | 1 | 16/32 | TF32（F32 資料、尾數取 10-bit 降精度乘） |
| `V_MFMA_F64_*_F64` | 16x16x4 / 4x4x4_4B | 1/4 | 32/16 | F64 矩陣乘（DGEMM） |
| `V_MFMA_F32_*_{BF8/FP8}_{BF8/FP8}` | **16x16x32** / **32x32x16** | 1 | 16/32 | FP8/BF8 矩陣乘（A、B 可各自選 FP8 或 BF8） |

### 哪幾個是「GEMM 要先認得」的重要變體

上表**粗體**的都是「單 block、大 K」的變體——實務 GEMM 最常用：

| 型別 | 首選變體 | 為什麼 |
|------|----------|--------|
| FP16 / BF16 | `16x16x16`、`32x32x8` | K 大 → 每條 MFMA 攤到的 A/B 搬運最划算 |
| INT8 | `16x16x32`、`32x32x16` | 同上，且 I8 的 K 可以更深 |
| FP8 / BF8 | `16x16x32`、`32x32x16` | LLM 推論/訓練低精度主力 |
| F32 | `16x16x4`、`32x32x8` | 精度優先場景；example03 用 `16x16x4` |
| F64 | `16x16x4` | HPC / DGEMM |

> 直覺：**K 越大，一條 MFMA 攤到的「把 A/B 從 LDS 讀進 lane」的成本越低**。所以 tuning 時同型別偏好挑 K 最深
> 的那個變體，再用 `32x32` vs `16x16` 去換 tile 幾何與 occupancy。TensileLite 的 `MatrixInstruction`
> 9-element 就是在這張表裡挑一列（見 [glossary](../glossary.md) 的 MatrixInstruction）。

### 稀疏 MFMA：`V_SMFMAC_*` 家族（Table 32, ISA p.52）

做 **4:2 結構化稀疏**的 `D = C + A × B`，其中**只有 A 稀疏**（每 4 個沿 K 方向的值有 2 個為 0），非零值
壓緊成 2:1，另用一個 VGPR 存「哪兩個非零」的 2-bit 索引。

| 指令 | 形狀 | Cycles | 說明 |
|------|------|--------|------|
| `V_SMFMAC_F32_*_F16` | 16x16x32 / 32x32x16 | 16/32 | 稀疏 F16 |
| `V_SMFMAC_F32_*_BF16` | 16x16x32 / 32x32x16 | 16/32 | 稀疏 BF16 |
| `V_SMFMAC_I32_*_I8` | 16x16x64 / 32x32x32 | 16/32 | 稀疏 I8 |
| `V_SMFMAC_F32_*_{BF8/FP8}_{BF8/FP8}` | 16x16x64 / 32x32x32 | 16/32 | 稀疏 FP8/BF8 |

> 稀疏版的 K 是稠密版的 2 倍（F16 稠密 `16x16x16` → 稀疏 `16x16x32`），對應「A 壓掉一半、吞吐翻倍」。
> SMFMAC 是 accumulate 型（C 與 D 同一 VGPR，Src2 改放索引）。ROCm 6 起搭配 hipSparseLt 使用。

---

## 3. CDNA4 / gfx950 新增指令（**CDNA4-only，migration 參考**）

> ⚠️ 以下指令**只在 gfx950（MI350 / CDNA4）上存在**，gfx942 沒有。列在這裡是為了認得 migration 時的差異；
> 完整整理見 [cdna4 內部筆記 §3.3–3.5](../internal_docs/cdna4-mi350-architecture-and-isa.md)。

### 3.1 混合精度 `V_MFMA_F8F6F4`

CDNA4 新增可以「A、B 各自獨立選 FP8 / FP6 / FP4 型別」的 MFMA：

| 指令 | 形狀 | 輸入型別 | Cycles |
|------|------|----------|--------|
| `V_MFMA_F32_16x16x128_F8F6F4` | 16x16x128 | FP4 / FP6 / FP8 混合 | A 或 B 為 F8 → 32，否則 16 |
| `V_MFMA_F32_32x32x64_F8F6F4` | 32x32x64 | FP4 / FP6 / FP8 混合 | A 或 B 為 F8 → 64，否則 32 |

A/B 型別用 **CBSZ[2:0] 指定 A、BLGP[2:0] 指定 B**（本來是 broadcast 控制欄位，這裡被重新定義）：

| 編碼 | 格式 |
|------|------|
| `000` | E4M3（FP8） |
| `001` | E5M2（BF8） |
| `010` | E2M3（FP6） |
| `011` | E3M2（BF6） |
| `100` | E2M1（FP4） |

### 3.2 MXFP 的硬體入口 `V_MFMA_SCALE_*`

`V_MFMA_SCALE_F32_16X16X128_F8F6F4` / `V_MFMA_SCALE_F32_32X32X64_F8F6F4` 把「載入 block scale」與「MFMA」
融合成一條指令，實作 **OCP MX microscaling**：沿 K 每 32 個元素共用一個 **E8M0**（8-bit 純指數）scale。
這是 CDNA4 最重要的新賣點，也是 CDNA3 完全沒有的。細節（block scaling 流程、`CVT_SCALE_*` 打包）見
[cdna4 §3.4](../internal_docs/cdna4-mi350-architecture-and-isa.md)。

### 3.3 FP8 的 FNUZ → OCP 改變（重要相容性陷阱）

| 面向 | CDNA3 / gfx942 | CDNA4 / gfx950 |
|------|----------------|----------------|
| FP8 標準 | **FNUZ**（E4M3FNUZ / E5M2FNUZ） | **OCP OFP8**（E4M3 bias7/max448、E5M2 有 INF） |
| E4M3 特性 | 無 INF、單一 NaN、單一無號零、max≈240 | 無 INF、`0x7F/0xFF` NaN、max=448 |

**同一批 fp8 bit pattern 在兩代的數值意義不同**——所以在 gfx942 上做 FP8 GEMM/tuning 要用 `*_fnuz` 型別，
migrate 到 gfx950 時型別、scale、校正流程都要按 OCP 重做，不能直接沿用。FNUZ 是什麼、為何存在，見
[cdna3 §3.4](../internal_docs/cdna3-mi300-architecture-and-isa.md)。

> CDNA4 另新增 `DS_READ_B64_TR_B16/_B8/_B4`、`DS_READ_B96_TR_B6`（LDS transpose load，載入時順手轉置餵
> MFMA）與更深 K 的 `V_SMFMAC_*`；同屬 CDNA4-only，見 [cdna4 §3.8–3.9](../internal_docs/cdna4-mi350-architecture-and-isa.md)。

---

## 4. Register layout：64 個 lane 怎麼持有 A/B/D

**核心觀念（白話）：** 矩陣的元素不是「整塊放在某一處」，而是**攤在「lane × VGPR」這個二維座標上**——
每個 lane（0..63）拿矩陣的一部分，一個 lane 內若要放多個元素就用多個 VGPR。這是 Matrix Core 內部結構
（4×N tile 打包）決定的。要正確餵資料/取結果，就得知道「哪個 lane 的哪個 VGPR 對應矩陣的哪個 `[i][j]`」。

### 4.1 從 example03 的 `16x16x4_F32` 看最小情況

`asm/example03_mfma` 的 `.s`（L37-41）把 layout 講得最白：

```text
V_MFMA_F32_16x16x4_F32（lane l = 0..63）：
  A operand (16×4)  : lane l 持有 A[l%16][l/16]     （每 lane 1 個 f32）
  B operand (4×16)  : lane l 持有 B[l/16][l%16]     （每 lane 1 個 f32）
  D/C result (16×16): 每 lane 4 個 VGPR；vgpr d 持有 D[(l/16)*4 + d][l%16]
```

怎麼讀這三行：

- **A 是 16×4**：共 64 個元素，剛好 64 個 lane 各拿 1 個。`lane l` 拿第 `l%16` 列、第 `l/16` 行——
  也就是行方向（K=4）由 `l/16`（0..3）決定、列方向（M=16）由 `l%16` 決定。
- **B 是 4×16**：同樣 64 個元素、每 lane 1 個，但列（K）由 `l/16`、行（N）由 `l%16`。
- **D 是 16×16**：共 256 個元素 = 64 lane × 4 個 → **每 lane 要 4 個 VGPR**（所以 example03 用 `v[4:7]`
  這連續 4 個 VGPR 當一個 lane 的累加器）。`vgpr d`（d=0..3）持有 `D[(l/16)*4 + d][l%16]`——
  即 4 個 VGPR 沿著「輸出的列（row）」方向，以 4 為一組打包。

> 為什麼是「4 個一組」：Matrix Core 的原始輸出單位就是 **4×N 的 tile**（見 §7 微架構），所以輸出永遠以 4 列
> 為一包攤進 VGPR。這也是為什麼 MFMA 的暫存器要求「連續且對齊到所需暫存器數」——4 個輸出就得從能被 4 整除
> 的 VGPR 起點開始（ISA p.42）。

### 4.2 推廣到 `16x16x16` 與 `32x32x8`

同一套原則（元素攤在 lane × VGPR、輸出 4 列一包）推廣到更大的 K 與更大的 tile：

| 變體 | A 每 lane 幾個輸入 | B 每 lane 幾個輸入 | D 每 lane 幾個 VGPR | 直覺 |
|------|------|------|------|------|
| `16x16x4_F32` | 1（K=4，64 元素/64 lane） | 1 | **4**（256/64） | example03 的情況 |
| `16x16x16_F16` | K=16 → 每 lane 沿 K 拿多個（FP16 兩個打包進一個 32-bit） | 同左 | **4**（輸出仍 16×16=256/64） | 輸出 layout 與 `16x16x4` 相同，只是 A/B 沿 K 更長 |
| `32x32x8_F16` | 沿 K 拿多個 | 沿 K 拿多個 | **16**（32×32=1024/64） | 輸出更大 → 每 lane 要 16 個 VGPR，佔用暴增 |

要點：

- **輸出 tile 越大（32×32），每個 lane 需要的累加器 VGPR 越多**（16 個 vs 16×16 的 4 個）——這直接吃掉暫存器
  預算、壓低 occupancy。這就是為什麼「大 tile 高吞吐 vs 小 tile 高 occupancy」永遠是 tuning 的取捨。
- **輸入沿 K 打包**：低精度型別（FP16/BF16 兩個、FP8 四個）會 pack 進一個 32-bit VGPR，所以 K 變深不必然
  等比增加輸入 VGPR 數。
- 精確的 lane↔element 公式（形如 `l = j + 32*((i/4)%2)` 這類）逐變體不同，完整列在 MI300 ISA p.43-47；
  平常讀 kernel 時抓住「元素攤在 lane×VGPR、輸出 4 列一包」的直覺即可，需要精確對位再回查 ISA。

---

## 5. Accumulator 模型：Arch-VGPR vs AGPR

### 5.1 兩種暫存器檔

gfx942 每個 wave 有**兩池**向量暫存器（見 [cdna3 §3.2](../internal_docs/cdna3-mi300-architecture-and-isa.md)）：

| 暫存器 | 數量 | 誰用 |
|--------|------|------|
| **Arch VGPR**（V0–V255） | 256 × 32-bit | 一般 SIMD / VALU（`v_add`、`v_fma`、位址計算、A/B 載入…） |
| **AGPR / AccVGPR**（AV0–AV255） | 256 × 32-bit | **Matrix Core 專屬的累加暫存器** |

MFMA 用一個 **ACC bit** 決定 A/B 走 Arch 還是 Acc VGPR，用 **ACC_CD bit** 決定 C/D 走哪池；兩池之間用
`V_ACCVGPR_READ` / `V_ACCVGPR_WRITE` 搬資料。(ISA p.40)

### 5.2 什麼時候用哪個、為什麼

- **真實 GEMM kernel**：累加器（C/D）放 **AGPR**，把 256 個 Arch VGPR 留給 A/B 載入、位址計算、prefetch
  buffer 等，藉此塞下更多 wave（提高 occupancy）。代價是 epilogue 要寫回 global / 做 activation 前，得先用
  `v_accvgpr_read` 把累加器逐個搬回 Arch VGPR（AGPR 連接性受限，不能被 `buffer_store` / `ds_write` /
  一般 VALU 直接讀）——這是 CDNA 舊世代 GEMM 的一個固定成本。AGPR 的來龍去脈（miSIMD / XDL、為何存在、
  為何要搬回）詳見 [../gpu_knowledge/cdna5-gfx1250.md §1](../gpu_knowledge/cdna5-gfx1250.md)。
- **example03 刻意只用 Arch VGPR**（累加器就是 `v[4:7]`，不碰 AGPR）：因為它是**教學範例**，目標是把 MFMA 的
  資料流講清楚，不想引入 `v_accvgpr_read/write` 的搬運雜訊；且 tile 小（單 wave 16×16、每 lane 4 個累加器）
  用 Arch VGPR 綽綽有餘，不需要靠 AGPR 分流去搶 occupancy。真實 kernel 因為 tile 大、要拼 occupancy，才會
  改用 AGPR。

> migration 註記：AGPR 在 CDNA3、CDNA4 都存在；要到 **CDNA5 / gfx1250** 才被併進單一大 VGPR 檔（WMMA 累加器
> 直接寫 VGPR，省掉搬運）。對照見 [wmma-deep-dive.md](wmma-deep-dive.md) 與
> [../gpu_knowledge/cdna5-gfx1250.md](../gpu_knowledge/cdna5-gfx1250.md)。

---

## 6. Latency / throughput：為何 MFMA 後要等、怎麼把延遲藏掉

### 6.1 為什麼發完 MFMA 不能馬上讀結果

MFMA **不是單一 cycle 完成**（見 §2 的 Cycles 欄，一條要 8~64 個 pass），而且中間結果可被觀察到。所以在
「發出 MFMA」與「讀它的結果 / 改它的輸入暫存器」之間，**必須插入一定數量的獨立指令或 `s_nop`**，否則會讀到
還沒算完的舊值。這套「要等幾拍」的規則是 MFMA 專屬的相依表（ISA Ch.7.5, Table 37, ISA p.55-58）。

需要等多少，取決於**前一條 MFMA 是幾 pass**、以及**第二條指令怎麼用那個暫存器**（大致方向，精確值查 Table 37）：

| 情境 | 大致需要的 wait |
|------|------|
| 非 DL VALU 寫 VGPR → 緊接著 MFMA 讀該 VGPR（當輸入 A/B） | 約 2 個 wait state |
| MFMA 寫累加器 → 後續一般 VALU / VMEM 讀該結果 | 依前一條 MFMA 的 pass 數，約 **5 / 7 / 11 / 19** |
| MFMA 寫 → 下一條 MFMA 用同一累加器當 SrcC 繼續累加 | 可 0 等待（累加鏈是硬體支援的常見模式） |

example03 的做法最保守：K 迴圈結束後直接 `s_nop 15` 兩次（L166-167），純等 MFMA pipeline 排空再讀累加器
寫回 C——「correctness over speed」，教學範例不追求填滿延遲。

### 6.2 真實 kernel 怎麼把延遲藏掉

上一條 MFMA 的累加鏈可以 0 等待連發（SrcC → 下一條），這正是 example03 連發 4 條 `16x16x4` 的原因
（L153-156）——**它們共用累加器 `v[4:7]`，形成累加鏈，不必彼此空等**。真實高效 GEMM 更進一步：

- **連發多條 MFMA**（不同累加器或累加鏈）填滿矩陣單元；
- 在 MFMA 執行的空檔**穿插 LDS `ds_read` / global prefetch**——因為 VMEM / LDS 走的是**別的 pipe**，
  在 MFMA 佔用期間仍可發射（見 §7 issue port）；
- 用「有用的獨立工作」取代空 `s_nop`，把下一塊 tile 的資料先搬進來（double buffer / software pipeline）。

> 這就是讀 TensileLite `.s` 時看到「一批 `ds_read` → 一批 `v_mfma` → 又一批 `ds_read`」交錯的原因：不是隨機
> 排列，而是刻意用 prefetch 去蓋 MFMA 的延遲。`s_waitcnt`（vmcnt / lgkmcnt）與計數器語意見
> [cdna3 §3.6](../internal_docs/cdna3-mi300-architecture-and-isa.md) 與 [gfx942-isa-reference.md](gfx942-isa-reference.md)。

---

## 7. Matrix Core 微架構與 dataflow

前面幾節談「指令長怎樣、資料放哪、要等多久」；這一節往下鑽一層，講 **Matrix Core 這顆硬體引擎內部怎麼把
運算元流過去、算完塞回累加器**，以及它在 CU 的指令發射管線裡佔什麼位置。這是理解「為什麼 MFMA 會擋 VALU、
為什麼能用 prefetch 藏延遲」的根。

### 7.1 最小運算原語：4×1 × 1×4 外積

Matrix Core（在微架構文件裡也叫 **miSIMD / XDL**，內部由大量 DOT 單元組成）的**基本硬體單元是
「4×1 乘 1×4 的外積（outer product）」，一次產生 16 個輸出值**。(ISA p.40；亦見
[../gpu_knowledge/cdna5-gfx1250.md §1](../gpu_knowledge/cdna5-gfx1250.md))

用白話理解外積：拿 A 的一個 4×1 直行、乘上 B 的一個 1×4 橫列，得到一個 4×4=16 的小方塊：

```text
        b0  b1  b2  b3          （B 的 1×4 橫列）
  a0 [ a0b0 a0b1 a0b2 a0b3 ]
  a1 [ a1b0 a1b1 a1b2 a1b3 ]    ← 一次外積 = 16 個乘積，直接累加進 16 個累加器格子
  a2 [ a2b0 a2b1 a2b2 a2b3 ]
  a3 [ a3b0 a3b1 a3b2 a3b3 ]
（A 的 4×1 直行）
```

**所有 MFMA / SMFMAC 指令都是把這個 4×1×4 外積「在空間上平鋪、在時間上串接」組合出來的。** 例如
`16x16x4` 就是把外積沿 M、N 方向鋪成 16×16、沿 K 累加 4 次；`16x16x16` 則沿 K 串更多次（所以 cycle 更多）。
這也解釋了 §4 為何輸出永遠「4 列一包」——因為原始輸出就是 4 高的方塊。

### 7.2 運算元 dataflow：從暫存器到累加器

一條 MFMA 執行時，資料在 CU 內部的流向大致是：

```text
  A/B 輸入            Matrix Core（miSIMD / XDL）                累加器
 ┌─────────┐        ┌──────────────────────────────┐        ┌──────────┐
 │ Arch    │  讀 A  │  DOT / 外積陣列                │  累加  │ AGPR     │
 │ VGPR    │───────▶│  4×1 × 1×4 → 16 乘積           │───────▶│ (或 Arch │
 │ (A、B)  │  讀 B  │  沿 K 串接、沿 M/N 平鋪         │  寫回  │  VGPR)   │
 └─────────┘        └──────────────────────────────┘        └──────────┘
      ▲                                                            │
      │  A/B 由 LDS ds_read 或 global_load 先載入 Arch VGPR         │ SrcC 回讀形成累加鏈
      └────────────────────────────────────────────────────────────┘
```

- **A、B 一定從 VGPR 讀**（Src0/Src1 只能是 VGPR，ISA p.42）；資料通常是先 `global_load` 進 VGPR、或先
  staging 到 LDS 再 `ds_read` 進 VGPR（example03 走 LDS 路線）。
- **C（SrcC）與 D（輸出）**：由 ACC_CD bit 決定走 Arch VGPR 還是 AGPR；真實 kernel 放 AGPR。
- **累加鏈**：D 寫回後可當下一條 MFMA 的 SrcC 繼續累加（`v[4:7] → v[4:7]`），硬體對這條路徑優化過，可 0 等待
  連發——這是 §6.2「連發 MFMA」的硬體基礎。

### 7.3 issue port：為什麼 MFMA 擋 VALU、卻不擋 LDS/VMEM

關鍵不在 Matrix Core 本身，而在 **CU 的 sequencer（SQ）有幾個指令發射端口（issue port）**
（整理自 [../gpu_knowledge/cdna5-gfx1250.md §4](../gpu_knowledge/cdna5-gfx1250.md)，該處以 gfx942 為對照基準）：

- 在 **gfx942（CDNA3）**，**VALU 與 MFMA 共用同一個 VALU issue port**。MFMA 佔住這個 issue 視窗時，一般
  VALU（`v_add` / `v_fma` 等）就**發不出去（被擋）**。
- 但 **VMEM load / LDS `ds_read` / SALU 走的是別的 pipe**，在 MFMA 執行期間**仍可發射**。

這正好解釋兩件本文前面提到的事：

1. **為什麼能用 prefetch 藏延遲（§6.2）**：因為 `ds_read` / `global_load` 不跟 MFMA 搶同一個 port，可以塞在
   MFMA 執行的空檔——這是 CK 的 `sched_group_barrier` 能在 MFMA 之間插 DS/VMEM、**卻插不了 VALU** 的原因。
2. **為什麼位址計算/scale 會形成 pipeline bubble**：GEMM 的位址計算、scale 是 VALU，被 MFMA 擋著只能硬排在
   MFMA 之間。內部文件宣稱 gfx942 的矩陣單元（XDL）利用率因此只有約 **62%**（HGEMM 128×64 steady state；
   數字為 AMD 內部量測，非本 repo 實測），CK 團隊得靠複雜的 **ping-pong scheduling**（兩個 wave 交替，一個
   load、一個 MFMA）去遮掩。

### 7.4 CDNA3 vs CDNA4 在這一層的差異

在**指令發射模型**這一層，CDNA3 與 CDNA4 **相同**——都是 GFX9 家族、wave64、MFMA 與 VALU 共用 issue port
（MFMA 仍會擋 VALU）、累加器仍用 AGPR。CDNA4 的差別是**每 CU 的矩陣資源與吞吐**，不是發射模型：

| 面向 | CDNA3 / gfx942 | CDNA4 / gfx950 |
|------|----------------|----------------|
| 發射模型 | MFMA 佔 VALU issue port（擋 VALU），VMEM/LDS 可並行 | **相同** |
| 累加器 | AGPR（256）+ Arch VGPR（256） | **相同**（AGPR 仍在） |
| wave / SIMD | wave64、SIMD16×4（4-cycle issue） | **相同** |
| 16-bit 以下矩陣吞吐 | 基準 | **每 CU ×2**（靠 N3P 製程多出的電晶體） |
| block-scale 資料路徑 | 無 | **新增**（`V_MFMA_SCALE_*` 融合 scale 載入，見 §3.2） |
| LDS 餵料頻寬 | 64 KB/CU | **160 KB/CU、讀頻寬 ×2、可從 L1 直載**（更不容易餓著矩陣單元） |

> 一句話：**gfx942 → gfx950 在微架構層是「同一套發射模型、把矩陣單元加寬、把 LDS 餵料加粗」**，不是換管線。
> 真正把「MFMA 擋 VALU」這個 issue-port 痛點解掉，要到 CDNA5 / gfx1250 改用 WMMA + 獨立 issue port + VALU
> co-execution（XDL 利用率宣稱 62% → 92%）——那已是換 ISA 家族，見 [wmma-deep-dive.md](wmma-deep-dive.md) 與
> [../gpu_knowledge/cdna5-gfx1250.md §3-4](../gpu_knowledge/cdna5-gfx1250.md)。

---

## 8. 對應 codegen（TensileLite）

TensileLite 產生 GEMM kernel 時，發 MFMA 的邏輯集中在 `Components/MAC_*.py`（依 kernel 型別/形狀選對應
Component）。概念上：

- `MatrixInstruction` 9-element 決定要用哪個 M×N×K×B 變體（就是 §2 那張表的一列）；
- 對應的 Component 負責發出 `v_mfma_*` intrinsic（如 `__builtin_amdgcn_mfma_f32_16x16x16f16`）、安排累加器
  暫存器（AGPR）、並在 MFMA 之間插入 `ds_read` prefetch 與必要的 wait（§6）。

> 檔案級職責地圖與「想改 MFMA 發射動哪個檔」見 [../hipblaslt/components-codegen-map.md](../hipblaslt/components-codegen-map.md)
> （`MAC_*.py` 那列）。確切檔名/行號以原始碼為準。

---

## 9. 目前可先看的替代資源

- `asm/example03_mfma/`：README + `.s` L37-41（layout）、L153-156（4 條 MFMA 累加鏈）、L166-167（`s_nop` drain）
- `study_docs/amd-isa-kernel.md`「階段 A-3 / 階段 B」
- 第一手規格整理：[../internal_docs/cdna3-mi300-architecture-and-isa.md](../internal_docs/cdna3-mi300-architecture-and-isa.md) §3（MFMA / 暫存器 / 同步）

---

## 10. 名詞（Terminology）

- **MFMA（Matrix Fused-Multiply-Add）**：`D = C + A×B` 的矩陣指令家族（`V_MFMA_*`），CDNA GPU 的 GEMM 算力來源。
- **SMFMAC**：4:2 結構化稀疏版 MFMA（只有 A 稀疏，`V_SMFMAC_*`）。
- **Matrix Core / miSIMD / XDL**：CU 內執行 MFMA 的矩陣引擎；最小原語是 4×1 × 1×4 外積。
- **M / N / K / B**：MFMA 的 block 維度（A=M×K、B=K×N、D=M×N）與 blocks 數。
- **Arch VGPR**：一般向量暫存器（V0–V255，256 個），A/B 載入與 VALU 用。
- **AGPR / AccVGPR**：Matrix Core 專屬累加暫存器（AV0–AV255，256 個），真實 GEMM 放累加器；CDNA5 才併入 VGPR。
- **ACC / ACC_CD bit**：MFMA 用來指定 A/B、C/D 走 Arch 還是 Acc VGPR 的欄位。
- **CBSZ / BLGP**：CDNA4 `F8F6F4` 指令中被重新定義來指定 A / B 矩陣型別的欄位。
- **XF32 / TF32**：F32 資料、尾數取 10-bit 的降精度矩陣乘（ISA 稱 XF32）；CDNA4 改軟體模擬。
- **FNUZ / OCP**：兩種 fp8 標準；gfx942 用 FNUZ、gfx950 用 OCP OFP8，數值意義不同。
- **issue port**：CU sequencer 的指令發射端口；gfx942 MFMA 與 VALU 共用同一個（故 MFMA 擋 VALU）。
- **wait state / `s_nop`**：MFMA 後為等結果算完而插入的等待（Table 37）。

---

## 11. 交叉連結

- WMMA 對照（RDNA / CDNA5，MFMA→WMMA migration）：[wmma-deep-dive.md](wmma-deep-dive.md)
- CDNA3 / MI300 架構與 ISA（第一手規格、MFMA 表出處）：[../internal_docs/cdna3-mi300-architecture-and-isa.md](../internal_docs/cdna3-mi300-architecture-and-isa.md)
- CDNA4 / MI350 架構與 ISA（gfx950 新增指令、migration）：[../internal_docs/cdna4-mi350-architecture-and-isa.md](../internal_docs/cdna4-mi350-architecture-and-isa.md)
- CDNA5 / gfx1250（AGPR 移除、MFMA→WMMA、issue port 對照）：[../gpu_knowledge/cdna5-gfx1250.md](../gpu_knowledge/cdna5-gfx1250.md)
- gfx942 opcode 速查字典（五類指令表 + `s_waitcnt` counter 模型 + 常見組語 pattern）：[gfx942-isa-reference.md](gfx942-isa-reference.md)
- LDS 與 bank conflict（MFMA 餵料的瓶頸）：[lds-bank-conflicts.md](lds-bank-conflicts.md)
- 官方 PDF 索引：[spec-sources.md](spec-sources.md)
- 產品線 ↔ gfx 對照：[amd-datacenter-gpu-isa.md](amd-datacenter-gpu-isa.md)
- TensileLite MFMA codegen：[../hipblaslt/components-codegen-map.md](../hipblaslt/components-codegen-map.md)
- 執行模型（wave / CU / occupancy）：[../gpu_knowledge/execution-model.md](../gpu_knowledge/execution-model.md)
- 頂層學習地圖：[../README.md](../README.md)

## 一句話總結

> **MFMA 是 gfx942 上「一條指令算一整塊小矩陣乘加」的家族：名字編碼 `Dtype_M×N×K×B_ABtype`，GEMM 主力是
> 大 K 的單 block 變體（`16x16x16` / `32x32x8` / `16x16x32`…）；資料攤在 lane×VGPR 上、輸出 4 列一包，累加器
> 真實 kernel 放 AGPR；因為一條要跑好幾拍且與 VALU 共用 issue port，得靠連發 MFMA + 穿插 LDS/global
> prefetch 來藏延遲。Matrix Core 內部是 4×1×4 外積的平鋪串接——認清這幾件事，就能讀懂任何 gfx942 GEMM 的
> 組語，也知道 migrate 到 gfx950（加寬/加深、fp8 改 OCP、加 MXFP）與 gfx1250（換 WMMA）各差在哪。**
