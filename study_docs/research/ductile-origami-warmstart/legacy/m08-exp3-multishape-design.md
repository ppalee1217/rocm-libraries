---
historical_milestone_id: M08
title: EXP-3 multi-shape 擴張與 winner lock
lifecycle: legacy
archive_status: superseded
design_authority: none
execution_status: do_not_execute
historical_design_status: draft
historical_execution_status: blocked
historical_outcome: not_available
topic_successors: [S30, S31]
historical_depends_on: [M07_or_B_only_lock]
historical_cohorts: [nonstreamk, streamk]
historical_planned_report_paths:
  - ../reports/m08-exp3-multishape-nonstreamk-report.md
  - ../reports/m08-exp3-multishape-streamk-report.md
---

> ⚠️ **LEGACY／DEAD PROTOCOL／DO NOT EXECUTE：**本檔只保留 freeze／held-out hygiene 的歷史脈絡；主題 successors 為 [S30](../s30-stage3-heldout-registry-freeze-design.md)／[S31](../s31-stage3-bounded-replication-design.md)，不表示 artifact、criterion 或 outcome migration。請讀唯一 active 入口 [README](../README.md)。

# M08 — EXP-3 multi-shape 擴張與 winner lock 設計

Parent plan：[Ductile 引入 Origami/Formocast 暖啟動](../../ductile-origami-warmstart-experiment-plan.md)

## 1. 白話目標

前面只在少量 shapes 上證明方法「有腿」。M08 要把它放進更接近團隊 workflow 的 multi-shape tuning：一個 kernel 同時服務多個 guidance sizes，然後用另一批完全不參與 tuning 的 development-judgment sizes 檢查平均、尾端與 regression。

最後在看 M09 final holdout 前，鎖定唯一 winner。

## 2. 假設

**假設 M08-H1**：M06/M07 選出的 warm-start arm，在固定 macro tile 的 15 個 guidance sizes 上仍保持 sample-efficiency與品質，擴到 3 tiles 後，對 100 個獨立 development-judgment sizes 沒有不可接受的 P10、worst-case、critical-shape 或 correctness regression。

反證／停止：

- multi-shape 下品質、tail 或 correctness 明顯失守；
- faster-but-worse 在自然早停中重現；
- guidance 與 judgment shapes 有 leakage；
- 需要看 M09 final holdout 才能選 winner。

## 3. 預期目標

1. 從 1 tile ×15 guidance sizes 擴到 3 tiles。
2. 每個 tuned kernel 在 100 個 development-judgment sizes 驗證。
3. 分開報 geomean、P10、worst、critical regression，不只報平均。
4. 比較 B 與 A-safe+B（若 A 仍 eligible）。
5. 鎖定 M09 唯一 winner、model、hyperparameters、space與analysis。

## 4. 結果能與不能說明什麼

能說明：

- 方法在 development multi-shape workflow 是否仍可用；
- 同一 tuned kernel 的 cross-size generalization；
- A-safe+B 是否值得相對 B 保留；
- 哪些 strata 出現 tail regression。

不能說明：

- final holdout success；
- production deployment；
- judgment sizes 可再拿來當 M09 holdout；
- 3 tiles 能代表所有 gfx942 tile。

## 5. Data roles

### 5.1 `development_guidance`

- 每 tile 15 sizes；
- 用於 GA fitness、model marginalization 與 arm selection；
- selection rule 在執行前鎖定；
- 不得來自 M09 final holdout。

### 5.2 `development_judgment`

- 每個 tuned kernel 100 個獨立真實 sizes；
- 不參與 tuning、weights、hyperparameter selection前的任何 guidance；
- 可用於 M08 winner selection，因此**不能**重用為 M09 final holdout；
- shape/cluster ID 與 final holdout 完全不重疊。

## 6. Tiles、arms 與順序

階段：

1. 1 macro tile ×15 guidance sizes；
2. 通過後擴到 3 tiles；
3. 每 tile 的 champion 在 100 judgment sizes 驗證。

Arms：

- `B`：M06 eligible model + V0；
- `A-safe+B`：只有 M07 keep-A 時；
- paired cold B0 作 reference；
- 不再重開已淘汰的 model/A。

所有 arms：

- 同 guidance/judgment registry；
- 同 `reduce_fn`；
- 同 complete candidate eval budget；
- 同 seeds與randomized blocks；
- 同 correctness與measurement。

## 7. Multi-shape fitness 與 guidance

1. 從實際 generated YAML 讀 `soo/reduce_fn`。
2. Model whole-config utility 先 per guidance size 計算。
3. 依同一 `reduce_fn` 聚合後再 marginalize。
4. GA 真實 fitness 用相同 shape set與aggregation。
5. 一次 candidate evaluation 只有取得全部15 sizes 的完整 fitness vector才算 complete。
6. candidate×shape benchmark samples 另記，不能用 candidate eval 隱藏15倍量測成本。

## 8. 執行步驟

1. 鎖定 tile、guidance、judgment registry與strata。
2. 驗證 guidance/judgment/final-holdout overlap=0。
3. 在第一 tile 產 model weights、space manifest、run plan。
4. 跑 B0、B、適用時 A-safe+B：
   - primary fixed budget；
   - secondary natural stop。
5. 重測 champions並做 correctness。
6. 在100 judgment sizes執行固定驗證，不用結果回頭 retune同一 winner。
7. 檢查 geomean、P10、worst、critical regressions。
8. 第一 tile通過後，以完全相同 protocol擴到3 tiles。
9. 做 tile/shape strata與heterogeneity分析。
10. 套 winner rule並產 `winner-lock.json`。
11. 保存所有 model/hyperparameter/space/split/analysis hashes，之後才能申請 M09 unseal。

## 9. Winner rule

在看 final holdout 前：

- 若 `A-safe+B` 相對 `B` 再省 ≥5% evaluation，且無品質、invalid、correctness、faster-worse問題，選 `A-safe+B`；
- 否則選 `B`，結論「A 無足夠增益」；
- 每 cohort 分開鎖 model/arm；
- 不允許 M09 看結果後在 B 與 A-safe+B 間切換。

## 10. Metrics

Tuning：

- 鎖定的 time-to-target estimand；
- matched-budget verified GFLOPS；
- complete candidate eval；
- candidate×shape samples；
- end-to-end wall time；
- invalid/duplicate/compile failure；
- faster-but-worse telemetry。

Judgment：

- per-shape efficiency；
- geomean ratio；
- P10 ratio；
- worst-case ratio；
- preregistered critical-shape regression；
- regression count與magnitude；
- correctness failures。

不得只用 geomean 掩蓋 tail。

## 11. 驗收、否證與停止條件

- **M08.ACC.SPLIT**：guidance、judgment、final holdout 無重疊。
- **M08.ACC.ONE-TILE**：第一 tile 通過 preregistered quality/correctness/faster-worse gate。
- **M08.ACC.THREE-TILE**：三 tiles 都完成且 artifacts 可追溯。
- **M08.ACC.TAIL**：P10、worst、critical regressions 滿足 parent／contract boundary。
- **M08.ACC.WINNER-LOCK**：唯一 winner及所有 hashes 在 holdout unseal 前鎖定。
- **M08.FAL.LEAKAGE**：judgment 進入 guidance或 retuning，該 judgment set 作廢並換全新 sealed set。
- **M08.FAL.MULTISHAPE**：development multi-shape 無法維持品質／correctness，停止原 scoped confirmation。
- **M08.STOP.BUDGET**：資源不足時標 underpowered，不縮 judgment set後仍宣稱通過。

## 12. 預期狀況、診斷與解法

### 狀況 A：geomean 好，但 P10/worst 很差

- 解讀：平均改善掩蓋 regression。
- 解法：依 tail gate阻擋，不用平均救回；按shape strata找原因。

### 狀況 B：15-size fitness讓 candidate eval 看似相同但 wall time暴增

- 解法：同時報 candidate×shape samples與end-to-end wall time；Route 1不能只靠candidate eval。

### 狀況 C：judgment 發現問題後想改 hyperparameter

- 解法：允許 development amendment與重新執行 M08，但原 judgment已被看過，不能再當同一版本的 independent judgment；需新 sealed set。

### 狀況 D：A-safe+B只在一 tile 有效

- 解法：依 preregistered winner rule與heterogeneity分析；不可事後 per-tile挑不同 arm，除非另開 routed-by-tile protocol。

### 狀況 E：A 已淘汰

- 解法：記 B-only path；M07 skip不阻擋 M08。

## 13. 執行完成後的報告

實際完成某 cohort 後才建立：

- `../reports/m08-exp3-multishape-nonstreamk-report.md`
- `../reports/m08-exp3-multishape-streamk-report.md`

報告需列 hypothesis、15/100 split、3 tiles、tuning與judgment結果、tail、leakage檢查、faster-worse、遇到的multi-shape成本／regression與解法，並附唯一 winner lock。它只能支持「development winner」，不能寫 final holdout success。
