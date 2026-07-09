<!--
學習筆記。「我學到什麼 / 卡關 / 待釐清 / 隔日 todo」由你親手寫；
AI 只協助補 code/doc 連結與格式化。對應 quiz：study_docs/quizzes/0628-tiled-matmul與LDS-quiz.md
-->

# 0628｜HIP A-2：tiled matmul + LDS

## 今日目標
寫 tiled matmul，反組譯確認 LDS 指令出現。（階段：P0，彈性日）

## 對應 roadmap item
- [ ] 搞懂 LDS（shared memory）的角色與 `ds` + `s_barrier` 協作模式
  - LDS 指令家族 `ds_write_b*` / `ds_read_*`（由 `lgkmcnt` 追蹤）；tiling 先把 HBM staging 進 LDS 再重複使用
  - ✅ 完成判準：能說出 LDS 在 matmul tiling 裡的角色與 barrier 為何不可省
- [ ] 認識 LDS bank conflict（現有教材最大缺口，先建立概念）
  - 32 banks、每 bank 4 bytes、`bank = (byte_addr/4) % 32`
  - ✅ 完成判準：能說出何時會 bank conflict、`LDSBankConflict` counter 看哪裡
- [ ] 動手 寫 tiled matmul（用 shared memory），反組譯確認 LDS 指令出現
  - ✅ 完成判準：能解釋「為什麼 tile 載入後、計算前需要 `s_barrier`」
- [ ] （AMD 資源，選做）HIP 100「Fundamentals」的 Matrix Transpose naive→LDS 優化段（與 A-2 同主題的官方教材）
  - 📚 參考資源：[internal_docs/hip-training-at-amd.md](../internal_docs/hip-training-at-amd.md#hip-100-fundamentals-of-hip-programming)

## 我學到什麼（自己寫）
<!-- 用自己的話寫懂了什麼；越白話越好。這是學習的核心，不要讓 AI 代寫。 -->
-

## 卡關與如何解（自己寫）
<!-- 今天哪裡卡住、怎麼查到答案、最後怎麼解 -->
-

## 反組譯記錄（填你在 .s 找到的指令）
- `ds_write_b*`（寫 LDS）：
- `ds_read_b*`（讀 LDS）：
- `s_barrier`（出現在 tile 載入後、計算前）：

## code & doc 參考（可請 AI 協助補連結）
- LDS / barrier（A-2）：[amd-isa-kernel.md](../amd-isa-kernel.md)「階段 A-2」
- 真實 LDS staging 範例：[asm/example03_mfma](../../../asm/example03_mfma)
- bank conflict counter：[hipblaslt/profiling-rocprof.md](../hipblaslt/profiling-rocprof.md) 的 `LDSBankConflict`
  （概念深潛文件 isa/lds-bank-conflicts.md 為待擴充 stub）
- AMD 課程（選做）：[HIP 100 Fundamentals](../internal_docs/hip-training-at-amd.md#hip-100-fundamentals-of-hip-programming)（Matrix Transpose naive→LDS）

## Questions 整理（自己寫）
