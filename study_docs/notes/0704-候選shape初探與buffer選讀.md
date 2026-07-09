<!--
學習筆記。「我學到什麼 / 卡關 / Questions」由你親手寫；AI 只協助補 code/doc 連結與格式化。
對應 roadmap：P1・07-04（候選 shape / baseline 資料初探；ex04 buffer 改選讀）。
-->

# 0704｜候選 shape / baseline 資料初探（ex04 buffer 選讀）

## 今日目標
把彈性日用在離研究線最近的事——對幾個候選 shape 做初步 bench、預習 baseline 數字（之後研究資料集的
第一手素材），並補前面落後項。ex04（buffer 邊界）降為選讀。（階段：P1，彈性日）

## 對應 roadmap item
- [ ] ⭐候選 shape / baseline 資料初探（為 07-08 收斂研究切角、P2 資料 pipeline 暖身）
  - 對 2~3 個候選 shape 各跑一次 `hipblaslt-bench`，記下 Gflops 與選到的 solution
  - 粗判每個候選偏 compute- 還是 memory-bound（沿用 06-30 判讀法）
  - ✅ 完成判準：每個候選 shape 都有一行 baseline 數字 + 一句瓶頸初判
  - 📚 參考資源：[clients/bench/README.md](../../projects/hipblaslt/clients/bench/README.md)（bench 旗標）、[hipblaslt/profiling-rocprof.md](../hipblaslt/profiling-rocprof.md)（compute/memory-bound 判讀法）
- [ ] （彈性，補 07-03）選做 補讀 ex03 `.s` L6–119 未消化的部分（tiling / MFMA register layout）
  - 📚 參考資源：[asm/example03_mfma](../../../asm/example03_mfma)
- [ ] （選讀／按需，非必修）讀 [asm/example04_global_mem_oob/README.md](../../../asm/example04_global_mem_oob/README.md) 四節——研究線不需要，純 ISA 完整性，掃過建立印象即可
  - 「The store loop」：這支 kernel 只用單 lane 反覆 store 的設計
  - 「The kinds of global-memory OOB」表：5 類越界的差別（丟棄/fault/corruption）
  - 「Kernel argument layout」：kernarg 怎麼擺
  - safe / fault 兩節：兩種 `num_records` 設定造成的不同結果
  - ✅ 完成判準：能講出 5 類 OOB 中哪些會 fault、哪些靜默
- [ ] （選讀／按需）讀 `.s`（[oob_store_gfx942.s](../../../asm/example04_global_mem_oob/oob_store_gfx942.s)，161 行）L62–113
  - SRD（V#）在 `s[4:7]` 的構造（`s_and_b32` 遮罩 + `s_mov_b32` 設 word3）
  - `.Lloop` 的 `buffer_store_dwordx4 ... offen offset:N nt`
  - 64-bit base 進位（`s_add_u32` + `s_addc_u32`）與 `num_records` 夾擠遞減（`s_cselect_b32`）
- [ ] （選讀／按需）跑 safe 與 fault 兩模式
  - safe 模式：無 fault、越界寫入被丟棄
  - fault 模式：出現 GPU memory access fault（SIGABRT）
  - ✅ 完成判準：能對應「兩次 `num_records` 設定差異 → 為何一個安全一個 fault」
  - 📚 參考資源：[asm/example04_global_mem_oob](../../../asm/example04_global_mem_oob)（README + `.s`；待擴充 isa/gfx942-isa-reference.md）
- [ ] （AMD 資源，選做）GCN talk #3「Memory, IO, and CU Architecture on gfx9」
  - 📚 參考資源：[internal_docs/gcn-architecture-training-resources.md](../internal_docs/gcn-architecture-training-resources.md)

## baseline 初探表（研究資料集的第一手素材）
| 候選 shape (M,N,K,batch) | dtype | Gflops | 選到的 solution | 瓶頸初判 (compute/memory) |
|---|---|---|---|---|
| | | | | |
| | | | | |

## 我學到什麼（自己寫）
<!-- 用自己的話寫懂了什麼；越白話越好。這是學習的核心，不要讓 AI 代寫。 -->
-

## 卡關與如何解（自己寫）
<!-- 今天哪裡卡住、怎麼查到答案、最後怎麼解 -->
-

## 快速自測（ex04 選讀者再答；先自答再核對）
1. 為什麼 `flat` / `global_*` 指令沒有 `num_records` 邊界保護，`buffer_*` 有？
2. safe 模式為何不會 fault？
<details><summary>參考答案（roadmap）</summary>
1. 邊界檢查是 buffer（MUBUF）指令透過 SRD 的 `num_records` 硬體做的；flat/global 走平坦定址，無此欄位。
2. 越界的 store 其 offset ≥ `num_records`，硬體直接丟棄該 lane 的寫入，不觸發 fault。
</details>

## code & doc 參考
- bench 旗標：[clients/bench/README.md](../../projects/hipblaslt/clients/bench/README.md)
- 判讀法：[hipblaslt/profiling-rocprof.md](../hipblaslt/profiling-rocprof.md)
- ex04（選讀）：[asm/example04_global_mem_oob](../../../asm/example04_global_mem_oob)（README + [oob_store_gfx942.s](../../../asm/example04_global_mem_oob/oob_store_gfx942.s)）
- GCN talk #3（選做）：[internal_docs/gcn-architecture-training-resources.md](../internal_docs/gcn-architecture-training-resources.md)
- 研究線背景：[research/ductile-geko-notes.md](../research/ductile-geko-notes.md)

## Questions 整理（自己寫）
-
