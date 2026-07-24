---
milestone_id: M03
title: EXP-0a cold baseline 與 headroom
lifecycle: legacy
design_authority: none
design_status: superseded
execution_status: do_not_execute
outcome: superseded
historical_design_status: draft
historical_execution_status: blocked
historical_outcome: not_available
superseded_by: []
retirement_reason: cold-headroom and long-horizon convergence thesis removed from active internship scope
depends_on: [M00, M01.ALL]
cohorts: [nonstreamk, streamk]
planned_report_paths:
  - ../reports/m03-exp0a-cold-headroom-nonstreamk-report.md
  - ../reports/m03-exp0a-cold-headroom-streamk-report.md
---

> ⚠️ **LEGACY／RETIRED／DO NOT EXECUTE：**本檔的 cold-headroom／30→90 generation thesis 已退出 active scope，沒有直接 replacement。請讀 [design index](README.md) 與現行 parent protocol。

# M03 — EXP-0a cold baseline 與 headroom 設計

Parent plan：[Ductile 引入 Origami/Formocast 暖啟動](../../ductile-origami-warmstart-experiment-plan.md)

## 1. 白話目標

先確認 cold GA 真的還有「可以被暖啟動省下來的浪費」。

如果不同 seed 都穩定找到差不多的結果，而且把預算加到 3 倍也幾乎不再變好，那暖啟動能改善的空間很小；此時不應直接投入完整 EXP-1。

## 2. 假設

**假設 M03-H1**：在固定約 1.5 萬 candidate evaluation 的 cold GA 中，至少一部分 hot shapes 有明顯 seed 不穩定，或 30→90 generations 仍有可取得的品質 headroom。

反證：

- 各 cohort 中至少 80% development shapes 同時滿足：
  - final champion 獨立重測後的跨 seed CV <1%；
  - 90-generation 相對 30-generation 的 median GFLOPS uplift <1%。

若反證成立，不代表 guidance plumbing 錯，只表示可利用 headroom 太低；M06 降級為最小 smoke。

## 3. 預期目標

1. 建立可重現的 cold baseline anytime curves。
2. 把「seed spread」「預算延伸」「浪費評估」變成明確可計算指標。
3. 量出 M02 Formocast cost feasibility 需要的 cold end-to-end cost。
4. 用 baseline variance 在看 warm treatment 前，提出並鎖定：
   - 5→10 seeds 的 CI-width trigger；
   - M06/M09 censored time-to-target estimand 與 analysis rule。

## 4. 結果能與不能說明什麼

能說明：

- cold GA 在目前 workload、V0、fitness 與 budget 下有沒有 headroom；
- seed 與 budget 對 final quality 的影響；
- 搜尋何時最後一次顯著改善、之後花掉多少評估；
- baseline 的 natural-stop 行為與成本。

不能說明：

- Origami/Formocast guidance 是否有效；
- V0 是否漏掉合法好值；由 M04 判斷；
- headroom 的原因一定是初始採樣；可能來自 operator、space 或噪音。

## 5. 資料選擇

### 5.1 Shape 數

- pilot：每 cohort 3 個；
- development：每 cohort 最多 12 個；
- 若某 cohort 沒有足夠合法 workload，單獨標 underpowered，不用另一 cohort 補數。

### 5.2 選擇規則

只能依真實 `summary.csv` runtime contribution 與預先定義 strata：

- compute-bound／memory-bound；
- small-K；
- transpose；
- skinny／square；
- dtype 與 batch。

禁止：

- 用 Origami/Formocast prediction 選 shapes；
- 從 M09 final holdout 借 shapes；
- 看完 cold 結果後替換「難看」的 shapes。

Shape registry、role 與 selection provenance 由 M00 鎖定。

## 6. Arms 與固定條件

### 6.1 Operational cold baseline

- `weights=None`
- `V0`
- parent/default search：`pop=512`、`n_gen=30`、`period=5`、`div_thr=0.5`
- ≥5 paired seeds
- actual generated YAML 的固定 `soo/reduce_fn`

### 6.2 Fixed-horizon diagnosis

- `weights=None`
- `V0`
- `period=0`
- `n_gen=30/60/90`
- 相同 paired seeds

Fixed-horizon arm 是 headroom diagnosis，不得冒充 production baseline。

## 7. Measurement boundary

每 run 同時報：

- proposals；
- invalid／duplicate；
- complete candidate evaluations；
- candidate×shape benchmark samples；
- compile attempts/failures；
- generation；
- end-to-end wall time；
- final champion 的 7 次獨立重測 median 與 correctness。

`seed spread` 定義：

1. 每 seed 取 final champion；
2. 對 champion 做規定的獨立重測；
3. 先取該 seed champion 的 median GFLOPS；
4. 再對 seeds 計算 sample CV 與 IQR。

不能直接拿 noisy last observation 算 CV。

## 8. 執行步驟

1. 凍結 cohort、shape registry、V0、fitness、seed list、run-order randomization。
2. 在 3 pilot shapes 跑 operational baseline，驗 artifact 與 noise。
3. 跑 pilot 的 fixed-horizon 30/60/90。
4. 若 telemetry、correctness、noise 通過，擴到 12 development shapes。
5. 以 paired block 隨機化 run order，避免某 arm 固定在機器較熱／較冷時執行。
6. 每 run 產 anytime curve：best verified GFLOPS vs complete candidate evaluations。
7. 計算：
   - final seed CV/IQR；
   - 30→60、60→90、30→90 uplift；
   - 最後一次 ≥1% 改善的 evaluation；
   - 之後浪費的 evaluation 比例；
   - invalid/duplicate rate；
   - diversity/population/termination trajectory。
8. 對 right-censored time-to-target 只保存 `(T,event)`；正式 estimand 依 M00 在第一次 warm treatment 比較前鎖定。
9. 用 observed baseline variance 做 paired bootstrap/power simulation，提出 5→10 seeds trigger；shape 數仍是主要推論單位。
10. 將 cold cost 提供給 M02.COST 做 Formocast optimistic feasibility bound。

## 9. Metrics

- final champion GFLOPS 的 seed CV、IQR；
- fixed-horizon anytime AUC（只作 diagnosis）；
- 30→90 median uplift；
- last ≥1% improvement evaluation；
- post-improvement evaluation fraction；
- invalid/duplicate/compile-failure rate；
- termination reason 與 generation；
- candidate eval、benchmark sample、wall time；
- correctness failures。

所有 ratio 先 per shape 計算，再做 shape-level summary；seed 不能假裝成獨立 shape。

## 10. 驗收、否證與停止條件

- **M03.ACC.BASELINE-REPRO**：所有 run 有完整 manifest/artifacts，paired seeds 與 arm order 可重建。
- **M03.ACC.NOISE**：champion remeasurement 按 M01 policy 通過。
- **M03.ACC.HEADROOM**：超過 20% development shapes 不同時滿足「CV<1% 且 30→90 uplift<1%」。
- **M03.GATE.LOW-HEADROOM**：至少 80% shapes 同時雙低，M06 只允許 plumbing smoke，不投入完整 factorial。
- **M03.ACC.STATS-LOCK**：在看 M06 treatment 前鎖定 censored estimand、bootstrap 與 seed-escalation rule。
- **M03.FAL.CORRECTNESS**：baseline champion 有 correctness failure，先修 pipeline；不能拿錯誤 kernel 當品質基準。
- **M03.STOP.NOISE**：noise 超過 M01 上限且無法排除，該 cohort blocked。

## 11. 預期狀況、診斷與解法

### 狀況 A：30-generation run natural-stop，無法直接和固定 horizon 比

- 解法：operational baseline 與 `period=0` diagnosis 分開報；不把早停少跑的 evaluation 填成 fixed horizon。

### 狀況 B：部分 run 永遠達不到 target

- 解法：保存 `(T=min(N,B), event=false)`；不可刪除、不可當成 budget 點剛好成功。使用 M00 鎖定的 censored estimand。

### 狀況 C：seed CV 高，但其實是 benchmark noise

- 診斷：比較 champion 獨立重測 within-config variance 與 across-seed variance。
- 解法：先依 M01 增加 iterations；只有重測穩定後才解讀為 search instability。

### 狀況 D：large-space／low-diversity 讓實際 population 改變

- 解法：以 actual complete candidate eval 與 realized population 比，不只比較 generation。

### 狀況 E：5→10 seeds 幾乎不縮 CI

- 原因：主要變異來自 shape heterogeneity。
- 解法：不能用更多 seeds 代替更多 shapes；報 underpowered 或調整 shape budget，但不可降低門檻。

## 12. 報告與結論措辭

實際完成某 cohort 後才建立：

- `../reports/m03-exp0a-cold-headroom-nonstreamk-report.md`
- `../reports/m03-exp0a-cold-headroom-streamk-report.md`

每份報告必須直白回答：

- 原假設是否被支持；
- cold baseline 有多少 headroom；
- 結果只支持「值得／不值得繼續完整 warm-start 實驗」，不支持 model uplift；
- 遇到的 noise、censoring、termination 或 correctness 狀況及解法；
- M06 是 full、smoke、blocked 或 underpowered。
