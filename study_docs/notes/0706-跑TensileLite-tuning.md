<!--
學習筆記。「我學到什麼 / 卡關 / Questions」由你親手寫；AI 只協助補 code/doc 連結與格式化。
對應 roadmap：P1・07-06（實跑一次 TensileLite tuning）。
-->

# 0706｜實跑一次 TensileLite tuning

## 今日目標
親手跑完一次 tuning，看到 `0_`~`4_` 輸出目錄生成。（階段：P1）
（研究線意義：這條 grid search 就是研究主線要用 surrogate / prediction 降成本的對象；`2_BenchmarkData`
的 CSV 是之後 predictor 的第一批訓練資料。）

## 對應 roadmap item
- [ ] 讀 [tensilelite-pipeline.md](../hipblaslt/tensilelite-pipeline.md)「如何建置 / 執行以觀察此流程」
  - 看懂 `invoke rocisa` / `invoke build-client` / `Tensile/bin/Tensile` 各做什麼
  - ✅ 完成判準：能說出跑一次 tuning 需要哪幾個前置步驟
- [ ] 跑 一次完整 tuning（小 config 練手）
  - ✅ 完成判準：五個輸出目錄都生成，且能說出每個放什麼
  - 📚 參考資源：[hipblaslt/tensilelite-pipeline.md](../hipblaslt/tensilelite-pipeline.md)、[f32_gsu.yaml](../../projects/hipblaslt/tensilelite/Tensile/Tests/common/gsu/f32_gsu.yaml)（待擴充 hipblaslt/tuning-config-reference.md）

## 操作記錄
```bash
cd projects/hipblaslt/tensilelite
invoke rocisa            # 首次或改過 rocisa 後才需要
invoke build-client
Tensile/bin/Tensile Tensile/Tests/common/gsu/f32_gsu.yaml out/
ls out/                  # 應見 0_Build 1_BenchmarkProblems 2_BenchmarkData 3_LibraryLogic 4_LibraryClient
```
- `invoke rocisa` / `build-client` 結果：
- `Tensile/bin/Tensile` 是否跑完不報錯：
- `ls out/` 看到的目錄：

## 五個輸出目錄各放什麼（對照 pipeline 文件）
- `0_Build`：
- `1_BenchmarkProblems`：
- `2_BenchmarkData`（研究資料集雛形：每列 = 候選 kernel 的 (gene 參數, shape, GFLOPS)）：
- `3_LibraryLogic`：
- `4_LibraryClient`：

## 我學到什麼（自己寫）
<!-- 用自己的話寫懂了什麼；越白話越好。這是學習的核心，不要讓 AI 代寫。 -->
-

## 卡關與如何解（自己寫）
<!-- 今天哪裡卡住、怎麼查到答案、最後怎麼解 -->
-

## 快速自測（先自答再核對）
1. `3_LibraryLogic/` 與 `2_BenchmarkData/` 內容差在哪？
2. 改了 config 一定要重跑整條 pipeline 嗎？
<details><summary>參考答案（roadmap）</summary>
1. `2_BenchmarkData` 是每個 size 所有候選的計時 CSV；`3_LibraryLogic` 是挑完贏家後的選擇邏輯 YAML（出貨用）。
2. 不一定，視改動而定（可用 `--build-only` / cache 等避免全跑）；詳見 pipeline 文件「何時要重跑」。
</details>

## 研究線連結（自己補）
<!-- 這批 2_BenchmarkData CSV 之後如何變成 dataset.csv：欄位 = (gene..., M,N,K,batch,dtype, GFLOPS[,counters]) -->
- 參見 [research/surrogate-dse-plan.md](../research/surrogate-dse-plan.md)「資料集 schema」

## code & doc 參考
- pipeline：[hipblaslt/tensilelite-pipeline.md](../hipblaslt/tensilelite-pipeline.md)
- 最小 config：[f32_gsu.yaml](../../projects/hipblaslt/tensilelite/Tensile/Tests/common/gsu/f32_gsu.yaml)
- fork 參數速查：[hipblaslt/tuning-config-reference.md](../hipblaslt/tuning-config-reference.md)

## Questions 整理（自己寫）
-
