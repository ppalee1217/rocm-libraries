---
historical_milestone_id: M06
title: EXP-1 injection B 小型暖啟動
lifecycle: legacy
archive_status: superseded
design_authority: none
execution_status: do_not_execute
historical_design_status: draft
historical_execution_status: blocked
historical_outcome: not_available
topic_successors: [S13, S20]
historical_depends_on: [M02.COST, M03, M05]
historical_cohorts: [nonstreamk, streamk]
historical_planned_report_paths:
  - ../reports/m06-exp1-injection-b-nonstreamk-report.md
  - ../reports/m06-exp1-injection-b-streamk-report.md
---

> ⚠️ **LEGACY／DEAD PROTOCOL／DO NOT EXECUTE：**本檔的 initial-weight／shuffled主題 successor 是 [S13](../../s13-stage1-actual-gen0-mechanism-design.md) 與 [S20](../../s20-stage2-h10-persistence-design.md)；這不表示 artifact、criterion 或 outcome migration。請讀唯一 active 入口 [README](../../README.md)。

# M06 — EXP-1 injection B 小型暖啟動設計

Parent plan：[Ductile 引入 Origami/Formocast 暖啟動](../../../ductile-origami-warmstart-experiment-plan.md)

## 1. 白話目標

這是第一次直接比較「均勻 cold start」和「模型偏重 initial population」。

關鍵不只看暖啟動是不是比較早停，而是它能否用較少的**完整 candidate evaluation**達到 cold 最終品質的 99%，同時 final verified GFLOPS 不退步，並且真的贏過「相同集中程度、但方向被打亂」的 shuffled control。

## 2. 假設

**假設 M06-H1**：通過 M05 ranking gate 的 model weights，能相對 B0：

- 依 M00 在首次 treatment 比較前鎖定的 censored time-to-target estimand 改善至少 15%；
- final verified GFLOPS 至少是 B0 的 99%；
- 優於 same-entropy shuffled control；
- 沒有 correctness failure 或 confirmed faster-but-worse basin。

若 M03 判 low headroom，本 milestone 只做 plumbing smoke，不用低 power 結果宣稱失敗或成功。

## 3. 預期目標

1. 驗證 weights 實際進入 initial sampling，且不影響 mutation/operator。
2. 建立 1→3 development shapes 的第一條 warm-start anytime curve。
3. 分辨「模型方向有效」和「任意降低 entropy 都會更快」。
4. 實測 Ductile low-diversity/early-stop 是否造成更快但更差。
5. 決定哪些 model/cohort 可以進 M07/M08。

## 4. 結果能與不能說明什麼

能說明：

- injection B 在小型 development scope 是否有初步 sample-efficiency；
- model guidance 是否勝過 uniform 與 shuffled；
- natural-stop 下是否有 premature convergence；
- λ/α/ε 的 development tuning 方向。

不能說明：

- holdout 或 production speedup；
- injection A 有用；
- 1–3 shapes 的結果能代表完整 workload；
- development 調過的 hyperparameters 可在看 M09 後再改。

## 5. Eligibility 與 arms

Eligibility：

- M02.FUNCTIONAL 通過；
- M02.COST 將 model 標 formal；
- M03 未觸發 low-headroom，或只執行 smoke；
- M05 對應 model/cohort 通過。

Arms：

- `B0`: V0 + uniform；
- `B-shuffled`: V0 + same-entropy shuffled weights；
- `Origami-B`: 適用 cohort；
- `Formocast-B`: non-StreamK only。

Shuffled control：

- 對每個 gene 在 candidate 間 permutation；
- 保持 probability multiset 與 entropy 完全相同；
- permutation seed 從 paired run seed 派生；
- 不跨 gene 混值，不破壞 candidate cardinality。

## 6. Hyperparameter policy

Development grid：

- `λ ∈ {2,4,8}`
- `ε ∈ {0.1,0.2,0.3}`
- `α ∈ {1..16}` 的 preregistered subset／search rule

規則：

- 先鎖定 search rule，再看 treatment；
- 每次 amendment 保存時間、理由與已看資料；
- M08 winner lock 前凍結最終 model、λ、α、ε、`weight_beta`；
- M09 holdout unseal 後不得再調。

## 7. 目標與 censoring

`Q_cold,s`：

- shape `s` 的 B0 在相同最大預算下，final champion 獨立重測 GFLOPS 的跨 seed median。

Time-to-target：

- 首次達到 `0.99 * Q_cold,s` 的 complete candidate evaluation；
- 未達保存 `T=min(N,B)` 與 `event=false`；
- 不排除 censored runs；
- 正式 point estimate、CI、bootstrap與未達標處理由 M00 在第一次 treatment 比較前鎖定。

若最終採 RMST through budget B，才使用 `RMST_B` 名稱；不能把普通 capped mean 冒稱原始 `N@99`。

## 8. 執行步驟

### 8.1 Plumbing smoke

- `pop=64`
- `n_gen=5`
- `period=0`
- 1 shape
- 每 arm 至少 1 seed

檢查：

- weights/search-space hash；
- initial empirical frequencies 對齊目標 `p`；
- shuffled entropy 相同；
- mutation distribution 未改；
- telemetry/correctness/artifacts 完整。

Smoke 不作效能結論。

### 8.2 Full development run

1. 選 1 個 preregistered shape，通過後擴至 3 個。
2. 每 arm ≥5 paired seeds。
3. 以 paired block 隨機化執行順序。
4. Primary：`period=0` fixed budget。
5. Secondary：`period=5` natural-stop，專門量 faster-but-worse。
6. 產 anytime curve、time-to-target、final champion。
7. 每個 final champion 7 次獨立重測並做 correctness。
8. 比較 B0、shuffled、model arm。

## 9. Faster-but-worse subprotocol

每個 warm arm必記：

- per-generation diversity；
- 第一次跌破 `div_thr=0.5` 的 generation/evaluation；
- population size 與 decay mode；
- `f_avg`、`f_max`；
- termination generation/reason；
- final verified quality；
- fully resolved categorical champion。

Config cluster：

- normalized Hamming 只作粗略分群；
- 沒有 one-gene neighborhood benchmark + deterministic local ascent，只能稱不同 config cluster。

Confirmed worse basin：

1. warm champion 與 B0 champion 落不同 cluster；
2. warm final verified GFLOPS 顯著較差；
3. 對去重 champion 做 one-gene neighborhood 實測；
4. deterministic local ascent 後仍落在不同且較差的局部 optimum。

沒有足夠預算完成 3–4，只能標 suspected faster-but-worse，不得稱 basin。

## 10. Metrics

- M00 鎖定的 censored time-to-target estimand；
- target achievement probability；
- final verified GFLOPS ratio；
- matched-budget best GFLOPS；
- anytime curve；
- initial entropy 與 empirical candidate frequency；
- diversity/population/termination；
- candidate eval、candidate×shape samples、wall time；
- invalid/duplicate/compile failure；
- correctness。

## 11. 驗收、否證與停止條件

- **M06.ACC.PLUMBING**：initial frequency、weights ordering、shuffled entropy與mutation boundary通過。
- **M06.ACC.SPEED-DEV**：相對 B0，鎖定的 censored estimand改善≥15%。
- **M06.ACC.QUALITY-DEV**：final verified GFLOPS ratio ≥0.99。
- **M06.ACC.SHUFFLE**：model arm 優於 shuffled control。
- **M06.ACC.CORRECTNESS**：沒有新增 correctness failure。
- **M06.FAL.MODEL-DIRECTION**：model 不優於 shuffled，不能把「集中」效果歸因於 model ranking。
- **M06.FAL.FASTER-WORSE**：confirmed faster-but-worse basin，阻擋該 arm。
- **M06.GATE.ELIGIBLE**：同時通過 speed、quality、shuffle、correctness 才進後續。
- **M06.STOP.LOW-HEADROOM**：M03 觸發降級時，smoke 完成後停止，不宣稱 powered comparison。

## 12. 預期狀況、診斷與解法

### 狀況 A：model 和 shuffled 都比 uniform 快

- 解讀：低 entropy 可能觸發更快收斂，尚不能證明 model direction。
- 解法：要求 model 明確勝 shuffled；否則不通過。

### 狀況 B：較早達 target，但 final quality <99%

- 解讀：速度和品質交換，M06 主 route 不通過。
- 解法：development 可提高 ε或降低 guidance strength後依既定 search rule重跑；所有 amendment 要保留。

### 狀況 C：自然早停省很多 evaluation

- 解法：先看 final quality與 basin diagnosis。不能把提前鎖進差解當 speedup。

### 狀況 D：部分 run 未達 target

- 解法：保留 censoring，使用鎖定 estimator；不能只分析成功 run。

### 狀況 E：model weights empirical frequency 不符

- 診斷：candidate order、cost sign、`weight_beta`、normalization。
- 解法：回 M02；該 run 無效，不用 performance 結果補救 plumbing bug。

## 13. 執行完成後的報告

實際完成某 cohort 後才建立：

- `../reports/m06-exp1-injection-b-nonstreamk-report.md`
- `../reports/m06-exp1-injection-b-streamk-report.md`

報告需列出 hypothesis、locked estimator/contract、每 arm 的結果、結果能與不能支持、censored runs、shuffled 判讀、faster-but-worse 證據、遇到的 plumbing/noise/termination 狀況與解法，最後逐 model 給 `eligible`、`failed`、`blocked` 或 `underpowered`。
