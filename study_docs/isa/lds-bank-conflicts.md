# LDS 與 bank conflict（gfx942 / CDNA3）

> **狀態：P0 / P3 深入文件（已擴充）。** 這曾是現有教材最大的缺口——bank conflict 過去只在 counter 被提到，
> 32-bank 模型、觸發條件、padding 解法都沒寫。本文補齊：從 LDS 的 32-bank 硬體結構講起，推導何時會衝突，
> 用 `asm/example03_mfma/` 的實際 `ds_read` 位址做 worked example，再給 padding / 向量化 / TensileLite 旋鈕的解法。
> 對應 roadmap：**P0 / 06-28**（搞懂 LDS 與 bank conflict）與 **P3**（profiling 驅動優化）。
>
> 平台定位：本文聚焦 **gfx942 / MI300 / CDNA3（實驗平台）**，32 banks。CDNA4（gfx950，64 banks）與 CDNA5
> （gfx1250，LDS 併入 WGP$）的差異在 §7 標明作 migration 參考。第一手規格出處是
> [../internal_docs/cdna3-mi300-architecture-and-isa.md](../internal_docs/cdna3-mi300-architecture-and-isa.md)
> §3.5（整理自 MI300 ISA Ch.11 Data Share）。

## 白話總覽（先建立直覺）

**一句話：** LDS（Local Data Share，就是 CUDA 的 shared memory）在硬體上不是「一整塊記憶體」，而是被切成
**32 個可以同時工作的小倉庫（bank）**。一個 wave 的很多 lane 同一拍要讀 LDS 時，只要它們讀的位址**分散在
不同 bank**，硬體就能「一拍全部吐出來」；但只要有多個 lane 擠到**同一個 bank 的不同格子**，硬體只好**排隊
一個一個來（序列化）**——這就是 bank conflict，原本一拍的事被拉成好幾拍。

用一個生活類比理解「為什麼會排隊」：

> 把 LDS 想成一間有 **32 個結帳櫃台** 的超市，每個櫃台一次只能服務一位客人（一拍吐一個 dword）。
>
> - 32 位客人剛好分到 32 個不同櫃台 → **一次結完**（無衝突，滿頻寬）。
> - 8 位客人全擠到同一個櫃台（但要買不同東西）→ 得**排 8 次隊**（8-way conflict，頻寬只剩 1/8）。
> - 一群客人要買**同一樣東西**（同一個位址）→ 櫃台**廣播一次大家都拿到**（broadcast，不算衝突）。

所以 bank conflict 的整個故事只有三種結局：**分散（快）、撞同 bank 不同址（慢，序列化）、撞同址（廣播，快）**。
學會判斷一段 `ds_read` 屬於哪一種，就掌握了 LDS 效能的一半。

## 為何重要

GEMM 把 A/B tile 從 HBM 搬進 LDS 後，會**重複讀很多次**餵給 MFMA（見
[mfma-deep-dive.md §6.2](mfma-deep-dive.md)）。如果這些 `ds_read` 有 bank conflict，本來該滿頻寬的 LDS 讀取
被序列化，就會**餓著矩陣單元**——一個看不見的隱形瓶頸：算力明明沒滿，時間卻下不來。

這正是 profiling 驅動優化的關鍵一環：學習者要能走完
**「從 `LDSBankConflict` counter 看出問題 → 用 padding / 改存取 stride 解決 → 再量一次確認」** 這個閉環（§5）。
在 hipBLASLt / TensileLite 這邊，對應的就是 `TransposeLDS` / `LdsPad*` 這幾個「務必掃」的 tuning 旋鈕（§6）。

---

## 1. LDS 的 32-bank 結構（gfx942）

**核心事實：** gfx942 的 LDS 是 **64 KB / CU**，切成 **32 個 bank**，每個 bank 寬 **4 bytes（1 dword）**，
每個 bank 有 **512 個 entry**（`64KB ÷ 32 banks ÷ 4B = 512`）。位址落在哪個 bank 由這條公式決定：

```text
bank(byte_addr) = (byte_addr / 4) mod 32
                = dword_index mod 32          （因為 1 dword = 4 bytes）
```

| 面向 | gfx942 / CDNA3 值 | 說明 |
|------|-------------------|------|
| LDS 容量 | **64 KB / CU** | 與 CDNA2 相同（[cdna3 §3.1](../internal_docs/cdna3-mi300-architecture-and-isa.md) L78） |
| bank 數 | **32** | 一拍最多 32 個獨立存取 |
| bank 寬度 | **4 bytes（1 dword）** | 連續的 dword 會落在連續的 bank |
| 每 bank entries | **512** | `32 banks × 512 entries × 4B = 64 KB` |
| bank 公式 | `(byte_addr / 4) % 32` | 相鄰 dword → 相鄰 bank；每隔 **128 bytes（32 dword）** 繞回同一 bank |

要記住的兩個直覺數字：

- **相鄰 dword 落在相鄰 bank**：`v[0]`→bank0、`v[1]`→bank1……`v[31]`→bank31、`v[32]`→bank0（繞回）。
- **同一 bank 的位址間距是 128 bytes（32 dword）**：任何相差 128 bytes 整數倍的兩個位址一定同 bank。
  這就是 §3 會看到的「row stride 是 2 的次方（16 或 32 dword）時特別容易撞 bank」的根源。

### wave64 的「半波」存取（32 banks vs 64 lanes 的落差）

一個 wave 有 **64 個 lane**，但 LDS 只有 **32 個 bank**。所以 gfx942 對 wave64 的一條 `ds_*` 指令是**分兩個相位
（phase）**處理的：先服務 lane 0–31，再服務 lane 32–63（每相位 32 個 lane 對上 32 個 bank）。

> 這件事的實務含意：**bank conflict 是「在同一相位的 32 個 lane 之間」判定的**。判斷一段 `ds_read` 有沒有衝突，
> 要看「同一相位內、要讀 LDS 的那 32 個 lane，它們的位址是否撞在同一個 bank 的不同格子」。§3 的 example03
> 分析就是照這個規則算的。

---

## 2. 何時衝突、何時不衝突

一條 `ds_read` / `ds_write` 發出時，硬體看**同一相位內每個 lane 要碰的位址落在哪個 bank**，然後分成三種結局：

| 情境 | 條件 | 結果 | 拍數 |
|------|------|------|------|
| **分散（無衝突）** | 各 lane 落在**不同 bank** | 一拍全部完成 | 1 |
| **broadcast（無衝突）** | 多個 lane 落在**同一個位址（同 bank 同 address）** | 硬體廣播，一拍給所有人 | 1 |
| **N-way conflict** | 多個 lane 落在**同 bank 但不同 address** | 硬體**序列化**，一個一個來 | N |

關鍵是第三種與第二種的差別：**撞同 bank「不同址」才是衝突；撞同 bank「同址」是 broadcast，反而免費。**

用一張圖看「連續 dword（無衝突）」vs「間距 32 dword（32-way 最糟）」：

```text
無衝突（連續 dword，跨滿 32 banks）：
  lane :  0    1    2    3   ...  31
  dword:  0    1    2    3   ...  31
  bank :  0    1    2    3   ...  31      ← 32 lane 落 32 個不同 bank，一拍完成

32-way conflict（每個 lane 間距 32 dword = 128 bytes）：
  lane :  0    1    2    3   ...  31
  dword:  0   32   64   96   ...  992
  bank :  0    0    0    0   ...   0      ← 全撞 bank 0 的不同格子，序列化成 32 拍

broadcast（所有 lane 讀同一位址）：
  lane :  0    1    2    3   ...  31
  dword:  5    5    5    5   ...   5
  bank :  5    5    5    5   ...   5      ← 同 bank「同址」→ 廣播，一拍完成（不算衝突）
```

> 白話總結判斷法：**看「同一相位的 lane 之間，位址差是不是 128 bytes 的整數倍」**。是（且不是同一個位址）→ 撞 bank
> → 衝突；差得剛好能鋪滿 32 個 bank → 無衝突；根本同一個位址 → broadcast。GEMM 裡最常見的衝突來源，就是
> **把二維 tile 攤平存進 LDS 時，選了「一列 = 2 的次方個元素」的 row stride**（下一節實例）。

---

## 3. Worked example：讀出 example03 的 bank 行為

[asm/example03_mfma](../../../asm/example03_mfma) 是本 repo 的 MFMA GEMM 教學 kernel。它把 A/B tile staging 進 LDS 再讀出餵
`v_mfma_f32_16x16x4_f32`。我們直接拿它 `.s` 裡**實際的 `ds_read` 位址**來算 bank——會發現這個教學 kernel
其實**照 bank 公式是有 conflict 的**，正好示範「為什麼要 padding」。

### 3.1 example03 的 LDS 佈局

（見 [mfma_gemm_f32_gfx942.s](../../../asm/example03_mfma/mfma_gemm_f32_gfx942.s) L81-113、L206）

| buffer | LDS 起點 | 形狀 | row stride | 說明 |
|--------|----------|------|------------|------|
| `As` | byte 0 | 32 列 × 16 欄 float | **16 dword（64 bytes）** | 一列 = 16 個 float |
| `Bs` | byte 2048 | 16 列 × 32 欄 float | **32 dword（128 bytes）** | 一列 = 32 個 float |

兩個 row stride（16、32）都是 **2 的次方**——這正是 §2 說「最容易撞 bank」的設定。

### 3.2 A 讀取的 bank 分析（`.s` L141-144）

A 讀位址 `v8`（L90-99）攤開是：

```text
v8 (byte) = row_in_block * 64 + k_local * 4
          = row_in_block * (16 dword) + k_local * (1 dword)
其中 row_in_block = wr*16 + (lane%16) ,  k_local = lane/16   （wr 為此 wave 的 row-band）
```

換成 bank：

```text
bank = (dword_index) % 32
     = (row_in_block * 16 + k_local) % 32
     = { k_local        , 若 row_in_block 為偶數     （16 × 偶 = 32 的倍數 → 0）
       { 16 + k_local   , 若 row_in_block 為奇數     （16 × 奇 → 16）
```

**問題出在 `row_in_block * 16`**：相鄰的 m（`lane%16`）位址差 16 dword，而 `16 % 32` 讓 bank 只在兩個值間跳。
也就是說，本該分散到 16 個 bank 的 16 個 m，全被壓進**只有 2 個 bank**：

| m（`lane%16`） | 0 | 1 | 2 | 3 | 4 | 5 | … | 14 | 15 |
|----------------|---|---|---|---|---|---|---|----|----|
| bank（k_local=0，**stride 16**） | 0 | 16 | 0 | 16 | 0 | 16 | … | 0 | 16 |
| bank（k_local=0，**stride 17，padding 後**） | 0 | 17 | 2 | 19 | 4 | 21 | … | 28 | 15 |

stride 16 那列：8 個偶 m 全撞 bank 0、8 個奇 m 全撞 bank 16 → **同一相位內對 A 的讀取是 bank conflict**
（多個 lane 同 bank 不同址，被序列化）。

### 3.3 B 讀取的 bank 分析（`.s` L145-148）

B 讀位址 `v9 = 2048 + (k_local*128 + wc*64 + n_local*4)` bytes（L101-113）。因為 `2048/4 = 512` 是 32 的倍數、
`k_local*128/4 = k_local*32` 也是 32 的倍數：

```text
bank = (512 + k_local*32 + wc*16 + n_local) % 32
     = (wc*16 + n_local) % 32        ← 完全與 k_local 無關！
```

`k_local` 對 bank 沒有影響，代表**同一個 n_local、不同 k_local 的 lane（B tile 的不同「列」）會落到同一個 bank 的
不同位址** → 一樣是 conflict。根源同樣是 `Bs` 的 row stride = 32 dword（`32 % 32 = 0`，讀不同列 bank 不動）。

### 3.4 為什麼 example03 沒有把它 optimize 掉

example03 是**教學 kernel，明講「correctness over speed」**（`.s` L166-167 用兩個 `s_nop 15` 直接排空 MFMA
pipeline，不追求填滿延遲）。它的目標是把「global → LDS → MFMA」的資料流講清楚，所以選了最直觀的
「一列剛好放一列元素」的緊湊佈局，沒有為了避 bank conflict 而 padding。**真實高效 GEMM / TensileLite 產出的
kernel 會做相反的選擇**——寧可多花一點 LDS 容量做 padding，也要把 bank conflict 消掉（§4、§6）。

### 3.5 padding 怎麼修

把每列多留 1 個 dword 當「墊片」，讓 row stride 從 2 的次方變成**與 32 互質**：

| buffer | 原 stride | padding 後 stride | 效果 |
|--------|-----------|-------------------|------|
| `As` | 16 dword | **17 dword** | `gcd(17,32)=1` → 16 個 m 映射到 16 個相異 bank（見 §3.2 表下列） |
| `Bs` | 32 dword | **33 dword** | 讀不同 k 列時 bank 每次 +1 → 不再全撞同 bank |

只多用 `1 dword × 列數` 的 LDS，就把「16 個 lane 擠 2 個 bank」變成「16 個 lane 鋪滿 16 個 bank」，衝突消失。
下一節把這個手法一般化。

---

## 4. 解法

### 4.1 LDS padding（最常用）

**做法：** 二維 tile 存進 LDS 時，把每列的 stride 從「剛好等於一列元素數」多加一點點（通常 +1 個元素或 +1 個
dword），讓相鄰列的起點錯開 bank。

**為什麼有效（通則）：** 設你沿某方向存取的位址間距是 `S` dword，那麼這些存取用到的 bank 數 = `32 / gcd(S, 32)`。

- `S` 是 **2 的次方（1,2,4,8,16,32…）** → `gcd(S,32)` 很大 → 只用到少少幾個 bank → **最糟**（`S=32` 時全撞 1 個 bank）。
- `S` 與 32 **互質（奇數，如 17、33）** → `gcd(S,32)=1` → 鋪滿 32 個 bank → **最好**。

所以「+1」的精髓不是那 1 個元素本身，而是**把 stride 從偶數推成奇數 / 與 32 互質**，順手把 bank 打散。

> 代價：padding 會多吃 LDS（每列 +1 元素 × 列數），可能壓低 occupancy。所以是「用一點容量換頻寬」的取捨，
> 要不要 pad、pad 多少，交給 tuning 掃（§6）。

### 4.2 改存取 stride / swizzle

如果不想加 padding（想省 LDS），也可以改「怎麼把 tile 攤進 LDS」或「用什麼順序讀」，讓同一相位的 lane 天然落
在不同 bank——例如把要一起讀的元素**沿 bank 方向連續擺**，或對位址做 XOR swizzle（`addr ^= (row & mask) << k`）
把每列打散。概念和 padding 一樣：**破壞「stride 是 32 的因數」這個壞條件**。

### 4.3 向量化 `ds_read_b64 / b128`

用 `ds_read_b128`（一條讀 4 個連續 dword）取代 4 條 `ds_read_b32`，除了**少發指令**，還讓每個 lane 一次拿一段
連續位址（跨 4 個連續 bank）。但**向量化本身不會自動消除 bank conflict**——若不同 lane 的「起點」仍撞同 bank，
還是會序列化。所以實務上是 **padding（打散起點）＋ 向量化（減少指令、拉滿每次傳輸寬度）** 一起用。

### 4.4 CDNA4 的 transpose load（硬體幫你喬 layout）

CDNA4 新增 `DS_READ_B64_TR_B16 / _B8 / _B4`、`DS_READ_B96_TR_B6`：**從 LDS 載到 VGPR 時順手做矩陣轉置**
（見 §7）。GEMM 常遇到「A 是 column-major、B 是 row-major」而要在 LDS 裡喬 layout；transpose load 讓硬體直接
用適合 MFMA 的順序讀出，少一輪為了避 conflict / 喬 layout 而做的位址搬弄。**這是 gfx950-only**，gfx942 沒有。

---

## 5. 量測：`LDSBankConflict` counter

判斷「到底有沒有 bank conflict、pad 完有沒有改善」不能用猜的，要看 rocprof 的硬體 counter。

- **抓法**：把 `LDSBankConflict` 放進 rocprof 的 metrics 清單，包住 `hipblaslt-bench` 跑目標 GEMM（完整步驟見
  [../hipblaslt/profiling-rocprof.md](../hipblaslt/profiling-rocprof.md)「第二步」）：

```text
# metrics.txt
pmc: VALUUtilization VALUBusy MemUnitBusy MemUnitStalled LDSBankConflict Wavefronts
```

- **怎麼讀**（[profiling-rocprof.md](../hipblaslt/profiling-rocprof.md) 第三步的對照表）：`LDSBankConflict` 偏高 =
  shared memory 存取衝突，通常代表 LDS 讀寫序列化在拖時間 → 往「調整 LDS padding / 存取 pattern」方向修。
- **閉環用法**：pad 前量一次、pad 後量一次，看 `LDSBankConflict` 有沒有降、kernel 時間 / Gflops 有沒有升——
  這就是 §為何重要 講的 profiling 驅動優化閉環。

> 提醒：bank conflict 只是 LDS 效能的一面；同時也要看 `MemUnitBusy/Stalled`（是不是 HBM 頻寬瓶頸）與
> occupancy。padding 若把 LDS 用量推高、擠掉 wave，反而可能得不償失——所以要**量**，不要只憑公式。

---

## 6. 在 GEMM / TensileLite 裡怎麼處理

hipBLASLt 的 kernel 由 TensileLite 產生，避 bank conflict 的手段被包成幾個 tuning 參數，是「對效能影響大、
**務必掃**」的旋鈕（[../hipblaslt/tuning-config-reference.md](../hipblaslt/tuning-config-reference.md) L41）：

| 參數 | 作用 | 對應本文哪一節 |
|------|------|----------------|
| `LdsPadA` / `LdsPadB` | 給 A / B 在 LDS 的每個 block 加 padding，錯開 bank | §4.1 padding |
| `LdsBlockSizePerPadA/B` | 每隔多大一塊 LDS 就插一次 pad（控制 pad 的粒度） | §4.1 padding |
| `TransposeLDS` | 改變 tile 進 LDS 的擺法（配合 MFMA 讀取方向、避 conflict） | §4.2 改 stride / §4.4 transpose |
| `1LDSBuffer` | 是否只用單一 LDS buffer（省容量 vs double-buffer overlap） | 與 occupancy 取捨相關 |

LDS 容量會把 padding 算進去（[../hipblaslt/macrotile-tuning.md](../hipblaslt/macrotile-tuning.md) L170-181）：

```text
LDS bytes ≈ DepthU × MacroTile × bpe          （A、B 各一份，另加 pad）
ldsNumBytes = int((DepthU + ldsPad) × MacroTile × bpe)
```

> 也就是說：**pad 越多 → LDS 用量越大 → 可能塞不下更大的 tile / 擠掉 wave**。所以 TensileLite 把 `LdsPad*` 當成
> 要掃的維度，讓 benchmark 自己找「消 conflict 的收益 vs 多吃 LDS 的代價」的甜蜜點——正是 §5 說的「用量算得準、
> 但收益要量」。相關程式職責見 [../hipblaslt/kernelwriter-implementation.md](../hipblaslt/kernelwriter-implementation.md)
> 與 [../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) L116；
> 參數的實際掃描值範例見 [../internal_docs/tensilelite-kernel-generator.md](../internal_docs/tensilelite-kernel-generator.md) L96-98。

---

## 7. CDNA4 / CDNA5 差異（migration 參考）

> ⚠️ 以下是**別代的規格**，列出來是為了 migration 時認得差異；gfx942（本文主軸）就是 32 banks / 64 KB。

| 面向 | CDNA3 / gfx942（本文） | CDNA4 / gfx950 | CDNA5 / gfx1250 |
|------|------------------------|----------------|-----------------|
| LDS 容量 | **64 KB / CU** | **160 KB / CU** | 最多 **320 KB**（WGP 統一、可配置） |
| bank 組織 | **32 banks × 512 entries × 4B** | **64 banks × 640 entries × 4B** | 併入統一的 **WGP$**（LDS + L0 cache = 384 KB） |
| 讀頻寬 | 基準 | **×2（256 bytes/clock）** | 進一步變化（見 cdna5 文件） |
| 從 L1 直載 LDS | 無 | **可**（省一次「先進 VGPR 再寫 LDS」） | TDM（async global↔LDS DMA） |
| transpose load | 無 | **`DS_READ_*_TR`**（載入順手轉置餵 MFMA） | — |
| bank 公式 | `(byte_addr/4) % 32` | `(byte_addr/4) % 64`（bank 變 64，衝突條件要重算） | 依 WGP$ 組織 |

要點：

- **CDNA4 把 bank 從 32 變 64**：等於「櫃台變兩倍」，同一段存取的衝突程度通常降低，但**衝突條件要用 `%64`
  重算**——gfx942 pad 到 17/33 的參數搬到 gfx950 不一定最佳，所以 LDS 一改（64→160 KB）**tuning 必須重跑**
  （[../internal_docs/cdna4-mi350-architecture-and-isa.md](../internal_docs/cdna4-mi350-architecture-and-isa.md) §2.3、§6）。
- **CDNA5** 把 LDS 與 L0 cache 合併成統一的 **WGP$**，資源與排程單位從 CU 變 WGP（見
  [../gpu_knowledge/cdna5-gfx1250.md](../gpu_knowledge/cdna5-gfx1250.md) L213-214），bank conflict 的思考框架仍在，
  但底層記憶體組織已換代。

---

## 8. 名詞（Terminology）

- **LDS（Local Data Share）**：每個 CU 一塊、workgroup 內共享的 scratchpad（≈ CUDA 的 shared memory）；程式手動
  管理，用量算得準（對比 L2/MALL 這類硬體自動 cache，見 [../gpu_knowledge/memory-hierarchy-and-chiplet.md](../gpu_knowledge/memory-hierarchy-and-chiplet.md)）。
- **bank**：LDS 內可獨立同時存取的小記憶體單位；gfx942 有 32 個，各寬 4 bytes（1 dword）。
- **bank conflict**：同一相位內多個 lane 落在**同 bank 不同 address**，被硬體序列化成多拍。
- **N-way conflict**：撞同一 bank 的 lane 有 N 個 → 該次存取要 N 拍。
- **broadcast**：多個 lane 讀**同一個位址**（同 bank 同 address）→ 硬體一拍廣播，**不算衝突**。
- **row stride**：二維 tile 攤平進 LDS 時「相鄰列起點的位址間距」；是 2 的次方時最容易撞 bank，與 32 互質時最好。
- **padding**：每列多留 1 個元素/dword，把 row stride 推成與 32 互質，藉此打散 bank。
- **phase（半波）**：wave64 的一條 `ds_*` 分兩相位處理（各 32 lane 對 32 bank）；conflict 在相位內判定。
- **`LDSBankConflict`**：rocprof 硬體 counter，量 LDS 存取衝突程度。
- **`LdsPadA/B` / `TransposeLDS` / `LdsBlockSizePerPad*`**：TensileLite 控 LDS 佈局 / bank conflict 的 tuning 旋鈕。

---

## 9. 目前可先看的替代資源

- `asm/example03_mfma/`：`.s` L81-113（LDS 讀寫位址計算）、L133-150（`ds_write`/`ds_read` + `s_barrier` staging）、
  L206（`.amdhsa_group_segment_fixed_size 4096`＝As+Bs 的 LDS 用量）。
- [../hipblaslt/profiling-rocprof.md](../hipblaslt/profiling-rocprof.md)：`LDSBankConflict` counter 怎麼抓、怎麼讀。
- 第一手規格整理：[../internal_docs/cdna3-mi300-architecture-and-isa.md](../internal_docs/cdna3-mi300-architecture-and-isa.md) §3.5（Data Share / LDS 指令）。

---

## 10. 交叉連結

- MFMA 為何依賴 LDS 餵料、怎麼用 prefetch 藏延遲：[mfma-deep-dive.md](mfma-deep-dive.md)（§6、§7）
- LDS（DS）指令速查（`ds_read/write_b32/b64/b128`、offset 語意）：[gfx942-isa-reference.md](gfx942-isa-reference.md) §5
- LDS 在記憶體階層的定位（scratchpad vs cache）：[../gpu_knowledge/memory-hierarchy-and-chiplet.md](../gpu_knowledge/memory-hierarchy-and-chiplet.md)
- rocprof 量測 `LDSBankConflict` 的完整流程：[../hipblaslt/profiling-rocprof.md](../hipblaslt/profiling-rocprof.md)
- TensileLite 的 `LdsPad*` / `TransposeLDS`（macro tile ↔ LDS 用量）：[../hipblaslt/macrotile-tuning.md](../hipblaslt/macrotile-tuning.md)、[../hipblaslt/tuning-config-reference.md](../hipblaslt/tuning-config-reference.md)
- CDNA3 / MI300 架構與 ISA（LDS 64 KB / 第一手規格）：[../internal_docs/cdna3-mi300-architecture-and-isa.md](../internal_docs/cdna3-mi300-architecture-and-isa.md)
- CDNA4 / MI350（LDS 160 KB / 64 banks / transpose load / migration）：[../internal_docs/cdna4-mi350-architecture-and-isa.md](../internal_docs/cdna4-mi350-architecture-and-isa.md)
- CDNA5 / gfx1250（LDS 併入 WGP$）：[../gpu_knowledge/cdna5-gfx1250.md](../gpu_knowledge/cdna5-gfx1250.md)
- 官方 PDF 索引：[spec-sources.md](spec-sources.md)
- 頂層學習地圖：[../README.md](../README.md)

## 一句話總結

> **LDS 在 gfx942 上是 32 個各寬 4 bytes 的 bank，`bank = (byte_addr/4) % 32`；一個 wave 的多個 lane 只要落在
> 不同 bank（或同一個位址＝broadcast）就一拍完成，一旦擠到「同 bank 不同址」就被序列化成 N 拍——這就是 bank
> conflict。最常見的元凶是「把二維 tile 用 2 的次方 row stride 攤進 LDS」（example03 的 As=16、Bs=32 就是活教材），
> 解法是 padding（每列 +1，把 stride 推成與 32 互質，順手打散 bank）＋向量化，靠 `LDSBankConflict` counter 量前
> 後、在 TensileLite 用 `LdsPad*` / `TransposeLDS` 掃出甜蜜點。migrate 到 gfx950（64 banks、160 KB）要用 `%64`
> 重算、tuning 重跑。**
