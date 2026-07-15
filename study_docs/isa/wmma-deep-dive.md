# WMMA 深入（Wave Matrix Multiply-Accumulate，RDNA / CDNA5 對照）

> **狀態：P1 深入文件（migration / 對照用）。** 對應 roadmap：**P1**（認矩陣指令家族）與未來 migration 參考。
>
> **本 repo 的實驗平台 CDNA3/4（MI300 / MI350、gfx942 / gfx950）不使用 WMMA；此文件供 migration /
> 對照理解，主要對應 RDNA 與 CDNA5（gfx1250 / MI450）。** 現在動手的矩陣指令請看
> [mfma-deep-dive.md](mfma-deep-dive.md)。

## 白話總覽：WMMA 是什麼、跟 MFMA 差在哪

**一句話：** WMMA（**W**ave **M**atrix **M**ultiply-**A**ccumulate）和 MFMA 做的事一樣——都是「一條指令算一整塊
小矩陣乘加 `D = C + A × B`」——但**它是 AMD 另一條產品線（RDNA 消費級 GPU）用的矩陣指令**，而且從 **CDNA5
（gfx1250）** 起，資料中心線也改用 WMMA 取代 MFMA。

為什麼會有兩套名字做同一件事？因為歷史上 AMD 有兩條 ISA：

- **CDNA**（資料中心 / Instinct MI 系列，`gfx9xx`）：矩陣指令是 **MFMA**（`v_mfma_*`）。
- **RDNA**（消費級 Radeon，`gfx10xx / 11xx / 12xx`）：矩陣指令是 **WMMA**（`v_wmma_*`），從 RDNA3 開始有。

AMD 的長期戰略 **UDNA** 要把這兩條線統一成同一套 ISA。交叉點就是 **gfx1250（CDNA5 / MI450）**——它雖然是
資料中心 GPU，卻採用 RDNA 那條線的 **GFX12 指令編碼**，於是矩陣指令也跟著從 MFMA 換成 WMMA。所以理解 WMMA
對本 repo 有兩個用途：(1) 讀 RDNA 的矩陣程式；(2) 規劃 gfx942/gfx950 → gfx1250 的 migration。

> 本文 gfx1250 側的事實整理自 [../gpu_knowledge/cdna5-gfx1250.md](../gpu_knowledge/cdna5-gfx1250.md)（其數字
> 來自 AMD 內部文件）；RDNA3/RDNA4 的逐項 opcode / 形狀表**本 repo 尚未鏡像官方規格**，凡未在 repo 內有
> 第一手依據者，本文會明確標示「（本 repo 未收錄，需查 RDNA ISA）」而不臆造。

## 為何重要

本 repo 的 ISA 實作層目標仍是 **gfx942（CDNA3，wave64、MFMA、AGPR）**。但 AMD 下一代資料中心 GPU
（MI450 / gfx1250）已走到 **CDNA5 / GFX12**，矩陣算力整個換成 WMMA。如果之後要把 hipBLASLt / TensileLite
的 kernel 遷過去，就得先把「MFMA 的直覺」對映到「WMMA 的模型」——否則會用 gfx942 的假設去讀 gfx1250 的程式而
處處誤解（累加器位置、wave 大小、能不能跟 VALU 並行都不一樣）。

---

## 1. MFMA vs WMMA 對照表

這是全文最該記住的一張表（gfx942 側見 [mfma-deep-dive.md](mfma-deep-dive.md)、gfx1250 側整理自
[../gpu_knowledge/cdna5-gfx1250.md §3](../gpu_knowledge/cdna5-gfx1250.md)）：

| 面向 | MFMA | WMMA |
|------|------|------|
| 指令前綴 | `V_MFMA_*`（稀疏 `V_SMFMAC_*`） | `V_WMMA_*`（稀疏 `V_SWMMAC_*`） |
| 所屬 ISA 家族 | CDNA（GFX9，`gfx908`–`gfx950`） | RDNA（GFX10/11/12）＋ CDNA5（`gfx1250`，GFX12 編碼） |
| 用在哪些產品 | Instinct MI 系列（資料中心） | Radeon（RDNA3/4 消費級）＋ Instinct MI450（CDNA5） |
| 累加器暫存器檔 | **AGPR**（獨立於 VGPR，需 `v_accvgpr_read/write` 搬運） | **VGPR**（無獨立 AGPR，累加器直接寫 VGPR、零搬運） |
| wave 大小 | wave64（CDNA 一律 64） | **wave32**（RDNA 常見 32；gfx1250 為 wave32。RDNA 亦可 wave64） |
| 與 VALU 的關係 | MFMA 佔 VALU issue port → **擋住 VALU** | **可與 VALU co-execution**（獨立 issue port） |
| 指令編碼 | VOP3P（64-bit） | **VOP3PX2（128-bit，可融合 `LD_SCALE` + WMMA）** |
| 常見資料型別 | F32/F16/BF16/I8/FP8(FNUZ)/TF32/F64 | F16/BF16/I8 ＋（gfx1250）FP8/BF8/FP6/FP4 ＋ 微縮放 |
| K 維度深度 | 4 / 8 / 16 / 32（gfx950 更深） | **32 / 64 / 128**（每條算更深，見 gfx1250） |
| 矩陣重用修飾符 | 無 | **`matrix_a_reuse` / `matrix_b_reuse`**（減少 A/B 的 LDS 讀取） |

三個最關鍵、migrate 時最容易踩的差異：

1. **累加器從 AGPR 搬到 VGPR**：MFMA 的累加器在獨立的 AGPR 檔，epilogue 要 `v_accvgpr_read` 逐個搬回 VGPR；
   WMMA 直接寫 VGPR，**這整類搬運開銷消失**。（gfx1250 把 AGPR 併進單一大 VGPR 檔，每 wave 最多 1024 個。）
2. **wave64 → wave32**：一個 wave 的 lane 數從 64 變 32，register layout（哪個 lane 拿哪個元素）整個要重算。
3. **WMMA 可與 VALU 並行**：MFMA 會擋 VALU（gfx942 XDL 利用率宣稱僅 ~62%），WMMA 有獨立 issue port 可
   co-execution（宣稱 ~92%），排程模型不同。

---

## 2. WMMA 指令與變體

### 2.1 指令族

- **Dense**：`V_WMMA_*`（對應 MFMA 的 `V_MFMA_*`）。
- **Sparse（2:4 結構化稀疏）**：`V_SWMMAC_*`（對應 MFMA 的 `V_SMFMAC_*`）。

命名直覺與 MFMA 類似：編碼「輸出型別 + M×N×K + 輸入型別」。因為 WMMA 是 wave32，同一個「M×N 輸出 tile」攤在
32 個 lane（而非 64）上，register layout 與 MFMA 不同。

### 2.2 常見形狀與型別支援

| 項目 | 值 | 依據 |
|------|-----|------|
| RDNA3/RDNA4 最常被引用的形狀 | **`16x16x16`**（M=N=K=16） | 業界常引用的 RDNA WMMA 基本形狀；**逐項 variant 表本 repo 未收錄，需查 RDNA ISA** |
| gfx1250（CDNA5）K 深度 | **32 / 64 / 128**（比 MFMA 更深） | [../gpu_knowledge/cdna5-gfx1250.md §3](../gpu_knowledge/cdna5-gfx1250.md) |
| 輸入型別（RDNA3 起） | FP16 / BF16 / INT8（部分 INT4） | RDNA WMMA 一般支援；**精確清單本 repo 未收錄** |
| 輸入型別（gfx1250 新增） | ＋ FP8 / BF8 / FP6 / FP4 ＋ 微縮放（microscaling） | [../gpu_knowledge/cdna5-gfx1250.md §3](../gpu_knowledge/cdna5-gfx1250.md) |
| 輸出/累加型別 | 通常 F32（浮點）/ I32（整數） | 同 MFMA 慣例 |

> ⚠️ 誠實邊界：RDNA3 / RDNA4 的**完整 WMMA variant 表（每個形狀的 cycle 數、逐型別支援、lane↔element 公式）
> 目前不在本 repo 的第一手資料裡**（本 repo 只鏡像了 CDNA3/CDNA4 的官方 PDF，見
> [spec-sources.md](spec-sources.md)）。要精確資訊請查 AMD RDNA3/RDNA4 ISA 手冊。本文只給「已在 repo 內有
> 依據」的 gfx1250 事實與業界通用的 `16x16x16` 概念，不臆造其餘數字。

### 2.3 Register layout 直覺（與 MFMA 的關鍵差別）

- 和 MFMA 一樣，矩陣元素攤在 **lane × VGPR** 二維座標上；但 WMMA 是 **wave32**，所以「同一個 16×16 輸出 tile」
  由 **32 個 lane** 分擔（MFMA 是 64 個 lane），每 lane 分到的元素數、打包方式都不同。
- **累加器直接在 VGPR**：不像 MFMA 要區分 Arch VGPR / AGPR，WMMA 的 D/C 就放在一般 VGPR，layout 推導少一層
  「搬回 VGPR」的步驟。
- **`matrix_a_reuse` / `matrix_b_reuse`** 修飾符讓連續的 WMMA 重用上一條已載入的 A 或 B 運算元，減少重複的
  LDS 讀取——這是 MFMA 沒有的、專為降低餵料頻寬壓力設計的機制。

> gfx1250 精確的 WMMA lane↔element 對映本 repo 未收錄；migrate 時以 AMD gfx1250 ISA 為準。

---

## 3. gfx1250 為什麼「一定」要用 WMMA（migration 角度）

在 gfx1250 上，**MFMA 的 opcode 在 GFX12 編碼裡根本不存在**——不是被標記淘汰，而是直接移除。所有矩陣 GEMM
都必須改用 WMMA。原因是 UDNA ISA 統一：gfx1250 採 GFX12 編碼（RDNA 那條線），就得跟隨 RDNA 的 `V_WMMA_*`。
（MFMA 在舊平台 gfx908–gfx950 仍完整支援；這是「跨 ISA 家族的替換」，不是同家族內漸進淘汰。）

對本 repo 的直接意義：現在的算力來源 `v_mfma_*`（見 [../amd-isa-kernel.md](../amd-isa-kernel.md)）遷到 gfx1250
要**整段改寫成 `v_wmma_*`**，且 operand layout、累加器位置（AGPR→VGPR）、wave 大小（64→32）、排程模型
（能與 VALU 並行）全都不同——不是換個指令名字而已。完整的六點斷裂（AGPR 移除、CU→WGP、MFMA→WMMA、
dual-issue、wait counter 拆分、零二進位相容）見 [../gpu_knowledge/cdna5-gfx1250.md](../gpu_knowledge/cdna5-gfx1250.md)。

---

## 4. 名詞（Terminology）

- **WMMA（Wave Matrix Multiply-Accumulate）**：RDNA / CDNA5 的矩陣乘加指令（`V_WMMA_*`），對應 CDNA 的 MFMA。
- **`V_SWMMAC_*`**：WMMA 的 2:4 稀疏版本，對應 MFMA 的 `V_SMFMAC_*`。
- **RDNA**：AMD 消費級 GPU 架構家族（Radeon），`gfx10xx/11xx/12xx`；矩陣指令用 WMMA。
- **UDNA**：AMD 把 RDNA（遊戲）與 CDNA（資料中心）統一成同一套 ISA 的長期戰略；gfx1250 是交叉點。
- **VOP3PX2**：WMMA 用的 128-bit 指令編碼，可融合 `LD_SCALE` + WMMA（MFMA 用的是 64-bit 的 VOP3P）。
- **`matrix_a_reuse` / `matrix_b_reuse`**：WMMA 的修飾符，重用上一條的 A/B 運算元以減少 LDS 讀取。
- **co-execution**：WMMA 在矩陣單元執行的同時，VALU 可在同 cycle 並行發射（MFMA 做不到）。

## 5. 交叉連結

- 現用矩陣指令（本 repo 實驗平台）：[mfma-deep-dive.md](mfma-deep-dive.md)
- CDNA5 / gfx1250 深入（AGPR 移除、MFMA→WMMA、dual-issue、UDNA）：[../gpu_knowledge/cdna5-gfx1250.md](../gpu_knowledge/cdna5-gfx1250.md)
- 產品線 ↔ CDNA/RDNA ↔ gfx 對照（CDNA vs RDNA 段）：[amd-datacenter-gpu-isa.md](amd-datacenter-gpu-isa.md)
- 官方 PDF 索引（本 repo 只收 CDNA3/CDNA4，未收 RDNA）：[spec-sources.md](spec-sources.md)
- 執行模型（wave32 vs wave64、WGP vs CU）：[../gpu_knowledge/execution-model.md](../gpu_knowledge/execution-model.md)
- 頂層學習地圖：[../README.md](../README.md)

## 一句話總結

> **WMMA 和 MFMA 做同一件事（矩陣乘加），但 WMMA 是 RDNA 那條線的指令，並從 CDNA5（gfx1250）起取代 MFMA：
> 累加器改放 VGPR（無 AGPR、零搬運）、wave 從 64 變 32、可與 VALU 並行、K 更深、還有 `matrix_reuse` 修飾符。
> 本 repo 的實驗平台 CDNA3/4 仍用 MFMA、不用 WMMA；這份文件是給 RDNA 對照與 gfx1250 migration 用的——RDNA3/4
> 的逐項規格本 repo 未收錄，需要精確數字請查 AMD RDNA ISA。**
