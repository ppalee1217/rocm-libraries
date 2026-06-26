<!--
學習筆記。「我學到什麼 / 卡關 / 待釐清 / 隔日 todo」由你親手寫；
AI 只協助補 code/doc 連結與格式化。對應 quiz：study_docs/quizzes/0626-跑通第一次bench-quiz.md
-->

# 0626｜跑通第一次 bench + 看懂 build/runtime 接點

## 今日目標
完整跑通一次 `hipblaslt-bench` 並看懂輸出欄位；說清楚磁碟上的兩階段接點。（階段：P0）

## 對應 roadmap item
- [ ] 搞懂磁碟上的兩階段接點：build 產物（`.dat` 選擇表 / `.co` kernel）如何被 runtime lazy load
  - ✅ 完成判準：能畫出「build 產物 → 磁碟（`.dat`/`.co`）→ runtime lazy load」的接點圖
- [ ] 搞懂 build-time 三階段 pipeline（BenchmarkProblems → LibraryLogic → ClientWriter）各自產出什麼
  - ✅ 完成判準：能說出三階段各自的輸入與輸出、以及 `0_`~`4_` 目錄對應哪階段
- [ ] 跑既有 bench，把抽象呼叫鏈對應到真實輸出
  - ✅ 完成判準：能對照輸出講出「這次 heuristic 選了哪個 solution、跑多快」

## 我學到什麼（自己寫）
<!-- 用自己的話寫懂了什麼；越白話越好。這是學習的核心。 -->
-

## 卡關與如何解（自己寫）
<!-- 今天哪裡卡住、怎麼查到答案、最後怎麼解 -->
-

## bench 實測記錄（記下來，P2 調參會回頭對照）
- 指令：`./build/release/clients/hipblaslt-bench -m 4096 -n 4096 -k 4096 -r f16_r --print_kernel_info`
- solution name：
- solution index：
- Gflops：

## code & doc 參考（可請 AI 協助補連結）
- [hipblaslt/README.md](../hipblaslt/README.md)（建置產出 / runtime 載入兩節）
- [hipblaslt/tensilelite-pipeline.md](../hipblaslt/tensilelite-pipeline.md)
- [clients/bench/README.md](../../projects/hipblaslt/clients/bench/README.md)（bench 旗標）

## 待釐清（自己寫）
-

## 隔日 todo（自己寫）
-
