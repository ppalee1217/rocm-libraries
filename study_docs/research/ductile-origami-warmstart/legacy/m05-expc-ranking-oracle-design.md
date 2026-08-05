---
historical_milestone_id: M05
title: EXP-C 模型 ranking 與 oracle marginals gate
lifecycle: legacy
archive_status: superseded
design_authority: none
execution_status: do_not_execute
historical_design_status: draft
historical_execution_status: blocked
historical_outcome: not_available
topic_successors: [S12]
historical_depends_on: [M00, M01.ALL, M02.FUNCTIONAL]
historical_cohorts: [nonstreamk, streamk]
historical_planned_report_paths:
  - ../reports/m05-expc-ranking-oracle-nonstreamk-report.md
  - ../reports/m05-expc-ranking-oracle-streamk-report.md
---

> ⚠️ **LEGACY／DEAD PROTOCOL／DO NOT EXECUTE：**本檔是 pre-pivot ranking／oracle設計，不具執行權威。主題 successor：[S12](../s12-stage1-real-score-ranking-oracle-audit-design.md)。請先讀唯一 active 入口 [README](../README.md)。

# M05 — EXP-C 模型 ranking 與 oracle marginals gate 設計

Parent plan：[Ductile 引入 Origami/Formocast 暖啟動](../../ductile-origami-warmstart-experiment-plan.md)

## 1. 白話目標

在花完整 GA 預算前，先問最基本的問題：模型能不能把快的 whole config 排在前面？

再用真實分數建立只供診斷的 oracle marginals，分辨失敗到底來自模型、whole-config→per-gene 邊際化，還是 factorized hook 本身表達力不足。

## 2. 假設

**假設 M05-H1**：適用模型在 development shapes 上的 whole-config ranking，median Spearman ≥0.25，且 top-decile lift ≥2× random。

適用模型：

- non-StreamK：Formocast primary、Origami comparator；
- StreamK：Origami only。

反證：

- non-StreamK 的 Origami 與 Formocast 都未過 gate：停止該 cohort 的 model-guided thesis；
- StreamK 的 Origami 未過：停止 StreamK thesis；
- 兩 cohort 都停止：整體 thesis 停止，不進完整 M06。

## 3. 預期目標

1. 建立每 shape 256 個 `_initKernel-valid` whole configs 的 prediction + ground truth dataset。
2. 量 Spearman、Kendall、top-10% recall、top-decile lift。
3. 產 model marginals 與 dev-only oracle marginals。
4. 把失敗定位成：
   - model ranking failure；
   - marginalization failure；
   - factorized hook expressiveness failure。

## 4. 結果能與不能說明什麼

能說明：

- 模型在 sampled dev pool 上是否有足夠排序訊號；
- 哪個 cohort/regime 可進 M06；
- model marginals 與 oracle marginals 的差距；
- factorized representation 是否有基本可用性。

不能說明：

- 通過 ranking gate 就一定能讓 GA 更快；
- sample pool 外的完整搜尋空間排名；
- holdout 的最終 speedup；
- oracle marginals 可以拿來當正式 treatment。

## 5. Sampling 與 leakage 防線

每個 development shape：

1. 從 V0 或 preregistered applicable space 非模型式抽樣；
2. 經 `_initKernel` validity；
3. 去除 exact duplicate；
4. 固定 256 whole configs；
5. 抽樣 seed、rejection 與 replacement 全部保存。

禁止：

- 按 Origami/Formocast 分數挑 256 個；
- 用 M08 development judgment 或 M09 final holdout；
- 只保留 model 能成功評分的 configs；
- 以 oracle truth 回頭改 model threshold 後仍稱原 gate。

## 6. Ground truth 與 predictions

Ground truth：

- 每 config 使用相同 benchmark protocol；
- 保存 GFLOPS、latency、correctness、noise；
- correctness failure 不得列為高品質 config；
- partial／failed measurement 保留 status，不靜默刪除。

Prediction：

- Origami、Formocast 使用 M02 canonical mapping；
- 保存 raw latency、status、model revision、sample ID；
- model rejection 單獨報 coverage；
- ranking 用：

```text
Spearman(-predicted_latency, measured_GFLOPS)
Kendall(-predicted_latency, measured_GFLOPS)
```

## 7. Metric 定義

### 7.1 Top-decile

在第一次執行前於 contract 鎖定：

- percentile method；
- ties 處理；
- exactly 10% 無法整除時的規則；
- missing/rejected predictions 的處理。

### 7.2 Top-decile lift

```text
lift =
P(real top 10% | predicted top 10%)
/ 0.10
```

同時報：

- top-10% recall；
- precision；
- model coverage；
- bootstrap CI。

### 7.3 Gate

逐 model、逐 cohort 判定：

- median Spearman ≥0.25；
- median top-decile lift ≥2；
- 兩條都要過。

不跨 model 或 cohort pooling 來湊門檻。

## 8. Oracle marginals 診斷

Oracle 只用 development real scores，標 `diagnostic_only=true`。

執行：

1. 用相同 marginalization code 分別產 model marginals 與 oracle marginals。
2. 比 per-gene candidate ordering、mass、stability。
3. 用小型 deterministic／replay evaluator或 M06 smoke，比較：
   - uniform；
   - model factorized；
   - oracle factorized。
4. 判讀：
   - whole-config ranking 差：model failure；
   - ranking 過、model marginal 差、oracle marginal 好：marginalization/model calibration failure；
   - oracle factorized 也無法優於 uniform：factorized hook expressiveness failure。

Oracle artifact 不得被正式 M06 runner接受。

## 9. 執行步驟

1. 鎖定 shapes、256-config sampling、metric/tie/missing rules。
2. 產 valid config pool 與 exact manifests。
3. 以 M02 pipeline 批次 score。
4. 在 gfx942 上取得真實 benchmark與correctness。
5. 計算 per-shape metrics與coverage。
6. 以 shape 為主要 summary unit，分 regime 報告。
7. 產 model/oracle marginals與 bootstrap stability。
8. 做 oracle diagnosis，不調整 formal gate。
9. 逐 model/cohort輸出 `pass`、`fail`、`inconclusive`、`blocked`。

## 10. 驗收、否證與停止條件

- **M05.ACC.DATASET**：每 shape 有 256 個非模型式抽樣、valid、可追溯 configs，或明確 underpowered。
- **M05.ACC.COVERAGE**：model rejection/coverage 完整報告，沒有 silent drop。
- **M05.ACC.RANK**：適用 model 同時達 Spearman≥0.25 與 lift≥2。
- **M05.ACC.ORACLE-GUARD**：oracle artifact 無法進正式 arm。
- **M05.FAL.MODEL**：model marginals fail、oracle成功，否證該 model guidance，不否證 hook。
- **M05.FAL.HOOK**：oracle factorized 也 fail，否證現有 injection-B hook。
- **M05.STOP.COHORT**：該 cohort 沒有任何適用 model 通過，不進完整 M06。
- **M05.STOP.ALL**：兩 cohort 都沒有通過，停止本輪 thesis。

## 11. 預期狀況、診斷與解法

### 狀況 A：相關係數尚可，但 top-decile lift 不過

- 解讀：模型會粗略排序，但不能可靠集中到真正 top region。
- 解法：依雙門檻判 fail；不能只挑相關係數宣稱通過。

### 狀況 B：大量 model rejection

- 診斷：按 metadata、dtype、StreamK、parameter regime 分組。
- 解法：修 mapping或縮小「適用 regime」並在 treatment 前 preregister；不能刪 rejected rows 後重算漂亮指標。

### 狀況 C：ties 很多

- 解法：使用事前鎖定 tie method；報有效 distinct score 數。模型完全不敏感的 gene 回 uniform。

### 狀況 D：oracle 成功、model 失敗

- 解讀：hook 有腿，模型不適合。
- 解法：只淘汰失敗 model；另一 model/cohort 可繼續。

### 狀況 E：oracle 也失敗

- 解讀：per-gene 獨立 marginals 無法表達重要 epistasis。
- 解法：停止本輪 factorized injection B；whole-individual pre-screening 是新 scope，不可偷渡。

## 12. 執行完成後的報告

實際完成某 cohort 後才建立：

- `../reports/m05-expc-ranking-oracle-nonstreamk-report.md`
- `../reports/m05-expc-ranking-oracle-streamk-report.md`

報告要直白列出原假設、模型各 metric/coverage、結果能與不能證明、oracle diagnosis、遇到的 rejection/tie/noise 狀況與處置，最後逐 model 給 `eligible-for-M06`、`failed`、`blocked` 或 `inconclusive`。
