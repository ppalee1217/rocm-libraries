---
historical_milestone_id: M09
title: Overall held-out confirmation
lifecycle: legacy
archive_status: superseded
design_authority: none
execution_status: do_not_execute
historical_design_status: draft
historical_execution_status: blocked
historical_outcome: not_available
topic_successors: [S30, S31]
historical_depends_on: [M08, winner_lock, holdout_seal]
historical_cohorts: [nonstreamk, streamk]
historical_planned_report_paths:
  - ../reports/m09-overall-confirmation-nonstreamk-report.md
  - ../reports/m09-overall-confirmation-streamk-report.md
---

> ⚠️ **LEGACY／DEAD PROTOCOL／DO NOT EXECUTE：**本檔只保留 denominator／negative-reporting／holdout discipline 的歷史脈絡；主題 successors 為 [S30](../../s30-stage3-heldout-registry-freeze-design.md)／[S31](../../s31-stage3-bounded-replication-design.md)，不表示 artifact、criterion 或 outcome migration。請讀唯一 active 入口 [README](../../README.md)。

# M09 — Overall held-out confirmation 設計

Parent plan：[Ductile 引入 Origami/Formocast 暖啟動](../../../ductile-origami-warmstart-experiment-plan.md)

## 1. 白話目標

前面 M03–M08 都是在 development 階段挑方法、調參數、找問題。M09 才使用從未被 guidance、調參或 winner selection 看過的 final holdout，回答整個研究命題是否成立。

這一步不能再換 winner、改門檻、刪難看的 shape，或用「同預算品質變好」冒充「tuning 變快」。

## 2. 假設

**假設 M09-H1（Route 1）**：鎖定 winner 能在保持品質、tail、correctness與 basin 安全的前提下，顯著降低達到 cold 品質所需的 evaluation與 end-to-end wall time。

若 Route 1 未過，才檢查：

**假設 M09-H2（Route 2）**：在相同 budget 下，鎖定 winner 能帶來至少 1% verified GFLOPS uplift，且品質／correctness／basin constraints 仍通過。

若兩 route 都不過，否證「本輪 Origami/Formocast + Ductile 有 measurable improvement」。

## 3. 預期目標

1. 對每 cohort 用 ≥24 final holdout shapes、≥4 multi-shape clusters 完成 paired confirmation。
2. Primary fixed-budget 與 secondary natural-stop 分開。
3. 逐項判定 Route 1/2，不合成單一總分。
4. 產可重現、可 audit 的 final report。
5. 只有兩 cohort 各自通過，才可提出 routed system claim。

## 4. 結果能與不能說明什麼

能說明：

- 鎖定 protocol 在本次 gfx942 holdout distribution 上是否通過研究門檻；
- tuning efficiency、same-budget quality、tail、wall time、correctness與faster-worse；
- non-StreamK與StreamK各自 outcome。

不能說明：

- 未涵蓋 dtype/tile/workload 的普遍效果；
- gfx950/MI350 泛化；
- 未經 owner 批准就等同 team merge/deployment policy；
- sampled correctness 等於數學上完全正確。

## 5. Holdout 與 lock 前置條件

Unseal 前必須已鎖定：

- 每 cohort 唯一 winner；
- model revision、λ、α、ε、`weight_beta`；
- V0/VA、candidate ordering；
- ≥24 shapes、≥4 clusters及strata；
- critical shapes；
- baseline provenance；
- seed list與5→10 escalation rule；
- time-to-target target、censored estimand與bootstrap；
- Route 1/2門檻；
- measurement、correctness與analysis code SHA。

Fail closed：

- final holdout ID 曾出現在 pilot/development/guidance/judgment；
- unseal 後 model/arm/hyperparameter改變；
- baseline provenance仍 unknown；
- parent threshold 未在首次相關 treatment comparison 前鎖定。

## 6. Arms 與 protocol

每 cohort：

- B0 cold baseline；
- M08 鎖定 winner；
- 不重跑已淘汰 arm來挑最好結果。

Primary：

- `period=0`；
- fixed complete candidate evaluation budget；
- 比 matched budget quality與鎖定 time-to-target estimand。

Operational secondary：

- production `period=5`；
- 量 natural termination、actual eval、wall time、faster-but-worse。

Seeds：

- 預設 5 paired；
- 依 M03 在看 warm treatment前鎖定的 CI-width/power rule決定是否升10；
- 不能看 point estimate方向後才選要不要加 seed；
- seed不是獨立shape。

## 7. Route 1 — tuning efficiency

以下全部成立，才能宣稱「暖啟動加速 Ductile tuning」：

- **R1.EVAL**：鎖定 time-to-target estimand point estimate 改善≥20%，shape-clustered bootstrap 95% lower bound 改善≥10%。
- **R1.QUALITY**：final verified GFLOPS geomean ratio 的95% lower bound ≥0.99。
- **R1.TAIL**：每個 preregistered critical shape median regression≤3%，全shape P10 ratio≥0.98。
- **R1.WALLTIME**：包含 model scoring、mapping、validity、codegen、compile、benchmark的end-to-end wall time省≥15%，95% CI lower bound>0。
- **R1.CORRECTNESS**：無新增 correctness failure。
- **R1.BASIN**：natural-stop無confirmed faster-but-worse basin。
- **R1.SHUFFLE**：鎖定 winner 的 development evidence 已勝 same-entropy shuffled；若 confirmation protocol要求重跑control，必須事前鎖定。

任何一條未過，Route 1 失敗或 inconclusive；不能取平均救回。

## 8. Route 2 — same-budget quality

只在 Route 1 speed 未過時判定：

- **R2.QUALITY-UPLIFT**：matched-budget verified GFLOPS uplift≥1%，95% CI lower bound>0。
- 同時仍通過 R1.QUALITY、R1.TAIL、R1.CORRECTNESS、R1.BASIN。

措辭只能是「same-budget quality uplift」，不能稱 tuning speedup。

## 9. 統計與 censoring

每 run 保存：

- `T=min(N@99,B)`；
- `event`；
- target、budget、complete candidate eval；
- paired seed／shape／cluster ID。

規則：

- 不刪 censored run；
- 不把 `event=false` 當在 B 成功；
- 使用 M00 已鎖定的 estimand；若是 `RMST_B`，明確用該名稱；
- hierarchical paired bootstrap 先依真正推論單位 resample shape/cluster，再保留 arm/seed pairing；
- `Q_cold` 在每個 bootstrap replicate 依鎖定規則重算；
- ≥4 clusters 很少，CI 可能寬；不足只能報 underpowered/inconclusive。

Shape 是主要推論單位。若 cluster 是 workload 的真正抽樣單位，不能把同 cluster 的 shapes 假裝完全獨立。

## 10. Correctness 與 champion verification

每個 champion：

- 7 次獨立 performance remeasurement取median；
- 每個 preregistered holdout shape都執行 correctness；
- element全量驗證優先；
- 若全量不可行，使用 M01/owner事前鎖定的 sample count、edge elements、tolerance；
- 檢查 return code、NaN/Inf、reference mismatch；
- 保存 input seed與validator output。

若只做 sampled validation，報告只能寫「在該 protocol 未偵測到錯誤」。研究 Route 可依鎖定 policy判斷，但 deployment可繼續 blocked。

## 11. 執行步驟

1. 驗 `winner-lock.json`、protocol lock與holdout overlap。
2. 產不可變 run schedule，paired block隨機化 arm order。
3. Unseal final holdout，記 timestamp與人員。
4. 執行 primary fixed-budget runs。
5. 執行 secondary natural-stop runs。
6. 重測 champions與correctness。
7. 執行 frozen analysis code，不手動刪 outlier；任何 exclusion依事前規則。
8. 逐項產 Route 1 criteria。
9. Route 1未過才產 Route 2。
10. 分 cohort產 outcome與report。
11. 兩 cohort都完成後，parent才判 routed system outcome。

## 12. 驗收、否證與停止條件

- **M09.ACC.LOCK**：winner/protocol/split/analysis在unseal前鎖定。
- **M09.ACC.POWER**：達≥24 shapes、≥4 clusters與seed rule，或明確 underpowered。
- **M09.ACC.ROUTE1**：R1所有criterion通過。
- **M09.ACC.ROUTE2**：只在R1未過時，R2所有criterion通過。
- **M09.FAL.BOTH**：R1、R2都未過，否證 measurable improvement。
- **M09.FAL.CORRECTNESS**：任一新增correctness regression，阻擋deployment，不論省多少。
- **M09.FAL.BASIN**：confirmed faster-but-worse basin，阻擋deployment。
- **M09.FAL.LEAKAGE**：holdout曾被看過，confirmation失效，不能換名稱繼續宣稱held-out。
- **M09.STOP.BUDGET**：GPU資源不足，報underpowered；不得減shape/cluster後沿用confirmatory claim。

## 13. 預期狀況、診斷與解法

### 狀況 A：evaluation過，但wall time不過

- 解讀：model/mapping/codegen overhead吃掉收益。
- 結論：Route 1失敗；可報演算法sample-efficiency，但不能宣稱end-to-end tuning speedup。

### 狀況 B：geomean非劣，但critical shape regression>3%

- 結論：Route 1/2按tail gate失敗；不能用平均掩蓋。

### 狀況 C：CI很寬

- 依事前seed rule增至10；若變異主要來自shape/cluster，增加seed無效。
- 資源不足標inconclusive，不把point estimate當success。

### 狀況 D：Route 1未過、Route 2過

- 只寫same-budget quality uplift；不把品質提升換算成速度。

### 狀況 E：一cohort通過、另一失敗

- 報cohort-specific結果；不能稱完整routed Origami/Formocast system。

### 狀況 F：unseal後發現analysis bug

- 停止、保存bug與受影響artifact；
- 修正建立新analysis version並公開amendment；
- 若修正帶來研究者選擇空間，結果降級exploratory或需新holdout。

## 14. 執行完成後的報告

實際完成某 cohort 後才建立：

- `../reports/m09-overall-confirmation-nonstreamk-report.md`
- `../reports/m09-overall-confirmation-streamk-report.md`

每份報告要逐項回答 Route 1/2 stable criteria，直白說明假設、預期目標、實際結果、能與不能支持的 claim、censoring/CI/correctness/faster-worse、遇到的執行狀況與解法、remaining risk。Negative與inconclusive一樣必須正式建立報告。
