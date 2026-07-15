# 官方規格文件（本地 PDF）：CDNA3 / CDNA4 白皮書 + ISA

路徑說明：本檔在 `study_docs/isa/`。PDF 放在 repo 外的同層 `/data1/perlee/`（和 `asm/` 同一層），
從本檔連過去用 `../../../<檔名>.pdf`（`isa/` → `study_docs/` → `rocm-libraries/` → `/data1/perlee/`）。

> **一句話定位：** 本 repo 的**實驗 / 研究平台是 MI300（gfx942 / CDNA3）**，所以 **CDNA3 白皮書 + MI300 ISA
> 是主要權威來源**；MI350（gfx950 / CDNA4）是**後續需要時才 migrate 的目標**，CDNA4 的白皮書 + ISA 先當
> migration 參考，不是目前實驗要用的規格。

## 為什麼要這份索引

這幾份是 AMD 官方的**第一手規格文件**（白皮書講架構、ISA 手冊講指令集），
比二手整理更權威。之前 [amd-datacenter-gpu-isa.md](amd-datacenter-gpu-isa.md) 只引用了 ROCm 線上文件與
LLVM backend guide；現在有了官方 PDF，遇到「gfx942 到底支援什麼指令 / MFMA 有哪些型別 / cache 行為」
這類問題，應直接查對應 PDF。這份索引幫你**一眼分清哪份對應現在（MI300）、哪份對應未來（MI350）**。

## 名詞快速對照（同一顆 GPU 的三個名字）

| 產品名 | 架構世代 | LLVM target (gfx) |
|--------|----------|-------------------|
| MI300A / MI300X / MI325X | CDNA3 | `gfx942` |
| MI350X / MI355X | CDNA4 | `gfx950` |

（完整產品線對照見 [amd-datacenter-gpu-isa.md](amd-datacenter-gpu-isa.md)。）

## 主要來源（MI300 / CDNA3 —— 目前的實驗平台）

| 文件 | 類型 | 涵蓋範圍 | 本地 PDF |
|------|------|----------|----------|
| AMD CDNA3 Architecture White Paper | 架構白皮書 | CDNA3 的整體架構：XCD chiplet、CU / Matrix Core、記憶體階層、Infinity Cache、封裝與互連。回答「MI300 這顆硬體長怎樣、為什麼」 | [../../../amd-cdna-3-white-paper.pdf](../../../amd-cdna-3-white-paper.pdf) |
| AMD Instinct MI300 (CDNA3) Instruction Set Architecture | ISA 指令集手冊 | gfx942 的指令集：VALU / SALU、MFMA 變體與型別（含 FP8 FNUZ）、記憶體指令、暫存器（VGPR / AGPR）、`s_waitcnt` 語意。回答「這條指令做什麼、有哪些變體」 | [../../../amd-instinct-mi300-cdna3-instruction-set-architecture.pdf](../../../amd-instinct-mi300-cdna3-instruction-set-architecture.pdf) |

> 這兩份是**現在動手 / 讀組語 / 做 tuning 實驗時的第一手依據**——對應 [amd-datacenter-gpu-isa.md](amd-datacenter-gpu-isa.md)
> 核心對照表裡標「實驗平台」的 gfx942 那列，以及 [gfx942-isa-reference.md](gfx942-isa-reference.md) / [mfma-deep-dive.md](mfma-deep-dive.md) 的權威出處。

## 未來 migration 參考（MI350 / CDNA4 —— 後續需要時才用）

| 文件 | 類型 | 涵蓋範圍 | 本地 PDF |
|------|------|----------|----------|
| AMD CDNA4 Architecture White Paper | 架構白皮書 | CDNA4 相對 CDNA3 的架構變化：更大 LDS（160 KB/CU）、新資料型別、記憶體 / 互連調整。migrate 到 MI350 時先看這份 | [../../../amd-cdna-4-architecture-whitepaper.pdf](../../../amd-cdna-4-architecture-whitepaper.pdf) |
| AMD Instinct CDNA4 Instruction Set Architecture | ISA 指令集手冊 | gfx950 的指令集：新增 MXFP8 / MXFP6 / MXFP4（OCP MX）相關 MFMA、fp8 改 OCP 變體、TF32 軟體模擬等。migrate 時對照 gfx942 差在哪 | [../../../amd-instinct-cdna4-instruction-set-architecture.pdf](../../../amd-instinct-cdna4-instruction-set-architecture.pdf) |

> 這兩份**現在不是實驗規格**，只在規劃「gfx942 → gfx950 migration」或想知道次世代差異時查閱——
> 對應 [amd-datacenter-gpu-isa.md](amd-datacenter-gpu-isa.md) 核心對照表裡標「未來 migration 目標」的 gfx950 那列。
> 再下一代（CDNA5 / gfx1250 / MI450）的斷裂式改動另見 [../gpu_knowledge/cdna5-gfx1250.md](../gpu_knowledge/cdna5-gfx1250.md)（更遠期參考）。

## 交叉連結

- **這幾份 PDF 的實際內容整理**（繁中深入筆記，含架構重點 + MFMA 型別表 + 暫存器 / 記憶體數字）：
  - MI300 / CDNA3（gfx942，實驗平台）：[../internal_docs/cdna3-mi300-architecture-and-isa.md](../internal_docs/cdna3-mi300-architecture-and-isa.md)
  - MI350 / CDNA4（gfx950，migration 目標，含 gfx942→gfx950 遷移對照）：[../internal_docs/cdna4-mi350-architecture-and-isa.md](../internal_docs/cdna4-mi350-architecture-and-isa.md)
- 產品線 ↔ gfx 對照總表：[amd-datacenter-gpu-isa.md](amd-datacenter-gpu-isa.md)
- gfx942 opcode 速查：[gfx942-isa-reference.md](gfx942-isa-reference.md)
- MFMA 指令變體 / register layout（gfx942）：[mfma-deep-dive.md](mfma-deep-dive.md)
- 次世代（CDNA5 / gfx1250）深入：[../gpu_knowledge/cdna5-gfx1250.md](../gpu_knowledge/cdna5-gfx1250.md)
- 頂層學習地圖：[../README.md](../README.md)

## 一句話總結

> 手上 4 份官方 PDF：**CDNA3 白皮書 + MI300 ISA = 現在實驗（gfx942）的第一手規格**；
> CDNA4 白皮書 + ISA = **未來 migrate 到 MI350（gfx950）才需要**的參考。查規格前先認清自己在哪一代。
