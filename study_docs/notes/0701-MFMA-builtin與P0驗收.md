<!--
學習筆記。「我學到什麼 / 卡關 / Questions」由你親手寫；AI 只協助補 code/doc 連結與格式化。
對應 roadmap：P0・07-01（✅ 硬截止驗收：MFMA builtin + P0 總驗收）。
-->

# 0701｜MFMA builtin + P0 硬截止驗收

## 今日目標
召喚並反組譯出 MFMA 指令；通過 P0 總驗收。（階段：P0，硬截止）

## 對應 roadmap item
- [ ] 搞懂 MFMA 是什麼、為何用 builtin 召喚
  - MFMA＝矩陣乘累加硬體指令，一條算一整塊 tile（非逐元素）
  - 用 builtin（如 `__builtin_amdgcn_mfma_f32_16x16x16f16`）讓編譯器發 `v_mfma_*`
  - ✅ 完成判準：能說出 MFMA 為何比手寫 FMA 迴圈快（吞吐與 register 重用）
- [ ] 動手 寫 builtin kernel 並反組譯
  - ✅ 完成判準：在 `.s` 指出那條 MFMA，並說出它一次算的矩陣形狀

## P0 總驗收（自我檢核，全部要能做到）
- [ ] 對人講清楚 build-time / runtime 兩階段如何交接
- [ ] 跑過 `hipblaslt-bench` + rocprof-compute 並能解讀輸出
- [ ] 自寫 HIP kernel 並反組譯對照預期指令
- [ ] 逐行讀懂 ex01（手寫 reduce）與 ex02（向量化 + profiling）
- ✅ 完成判準：四項全部打勾＝通過 P0 硬截止

## 反組譯記錄
- 找到的 MFMA 指令（`v_mfma_*`）：
- 它一次算的矩陣形狀：

## 我學到什麼（自己寫）
<!-- 用自己的話寫懂了什麼；越白話越好。這是學習的核心，不要讓 AI 代寫。 -->
-

## 卡關與如何解（自己寫）
<!-- 今天哪裡卡住、怎麼查到答案、最後怎麼解 -->
-

## P0 驗收證據（各寫 2–3 句「我能做到」的證據：截圖/指令/數字）
- (a) build/runtime 兩階段交接：
- (b) bench + rocprof 解讀：
- (c) 自寫 kernel 反組譯：
- (d) 讀懂 ex01/ex02：

## 快速自測（先自答再核對）
1. MFMA 指令 `v_mfma_f32_16x16x4_f32` 一次算的是什麼形狀的矩陣乘累加？
2. 若 06-30 還沒跑通 profiling，今天該優先補哪一項、捨哪一項？
<details><summary>參考答案（roadmap）</summary>
1. 一個 wave（64 lane）算 `D[16x16] += A[16x4] * B[4x16]`，累加在每 lane 的 4 個 VGPR。
2. 優先補 ex02 的 profiling 迴圈（研究線關鍵）；A-3 可壓縮到「找到 `v_mfma_*` 即可」。
</details>

## code & doc 參考
- MFMA（A-3）：[amd-isa-kernel.md](../amd-isa-kernel.md)「階段 A-3」
- （MFMA 變體/latency 深潛 isa/mfma-deep-dive.md 為待擴充 stub）

## Questions 整理（自己寫）
-
