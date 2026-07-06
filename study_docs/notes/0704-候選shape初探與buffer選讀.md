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
- [ ] （彈性，補 07-03）選做 補讀 ex03 `.s` L6–119 未消化的部分（tiling / MFMA register layout）
- [ ] （選讀／按需，非必修）ex04 buffer 邊界——研究線不需要，純 ISA 完整性，掃過即可

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
- ex04（選讀）：[asm/example04_global_mem_oob](../../../asm/example04_global_mem_oob)
- 研究線背景：[research/ductile-geko-notes.md](../research/ductile-geko-notes.md)

## Questions 整理（自己寫）
-
