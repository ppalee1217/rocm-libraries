---
milestone_id: M07
title: EXP-2 A-safe 與 injection B factorial
lifecycle: legacy
design_authority: none
design_status: superseded
execution_status: do_not_execute
outcome: superseded
historical_design_status: draft
historical_execution_status: blocked
historical_outcome: not_available
superseded_by: []
retirement_reason: Injection A and A-safe factorial explicitly excluded from active scope
depends_on: [M04, M06]
cohorts: [nonstreamk, streamk]
planned_report_paths:
  - ../reports/m07-exp2-a-safe-b-factorial-nonstreamk-report.md
  - ../reports/m07-exp2-a-safe-b-factorial-streamk-report.md
---

> ⚠️ **LEGACY／RETIRED／DO NOT EXECUTE：**A-safe／Injection A factorial 已退出 active scope，沒有 replacement。請讀 [design index](README.md) 與現行 parent protocol。

# M07 — EXP-2 A-safe 與 injection B factorial 設計

Parent plan：[Ductile 引入 Origami/Formocast 暖啟動](../../ductile-origami-warmstart-experiment-plan.md)

## 1. 白話目標

M04 只回答「寬域裡有沒有好東西」，M06 只回答「在 V0 裡偏重採樣有沒有幫助」。

M07 把兩者合在同一個 factorial：看 model-selected、widen-only 的 A-safe extras，是否能在 B 已經有效的基礎上再省評估或提高同預算品質，而不是只把空間變大。

## 2. 假設

**假設 M07-H1**：`A-safe+B` 相對 `V0+B`：

- 鎖定的 time-to-target estimand 再改善至少 15%，**或**
- matched-budget verified GFLOPS 至少提高 1%；
- final quality regression 不超過 1%；
- 不增加不可接受的 invalid、dilution、correctness 或 faster-but-worse 問題。

若 M04 已淘汰 A，本 milestone 標 `skipped-by-gate`，不跑 GPU arms、不建立假 report；B-only 可以進 M08。

## 3. 預期目標

1. 分離 A、B 與 A×B interaction。
2. 證明 A-safe 真正 widen-only，沒有偷刪 V0。
3. 量 model-selected extras 是否優於完整 Vwide dilution control。
4. 決定 M08 使用 `A-safe+B` 或 `B`。
5. 以 offline A-hard diagnosis 永久檢查 hard pruning 風險，但不把它變成 GPU treatment。

## 4. 結果能與不能說明什麼

能說明：

- A-safe 在 development factorial 下是否有額外增益；
- 增益來自 search-space extras、B guidance 或 interaction；
- Vwide 稀釋和 A-safe 集中的差別；
- hard deletion 在既有 dev pool 是否已出現明確危險。

不能說明：

- hard pruning 在 holdout 安全；
- M08 multi-shape 或 M09 holdout 一定成功；
- A 失敗會否證 B。

## 5. Eligibility 與 arms

Eligibility：

- M04 保留 A；
- M06 至少一個 model/cohort eligible；
- M02 A-safe helper與space audit通過。

五 arms：

1. `V0 + uniform`
2. `V0 + B`
3. `A-safe + uniform`
4. `A-safe + B`
5. `Vwide + uniform`

固定：

- 相同 paired seeds；
- 相同 complete candidate evaluation cap；
- 同 model/hyperparameters；
- 同 shape、fitness、correctness、measurement；
- arm order 隨機交錯。

## 6. A-safe admission

每個 shape/cluster、gene extra 必須有：

- `V0 ⊆ VA` 的 machine assertion；
- extra 位於 legal domain；
- 足夠 conditional valid completions；
- 相對 V0 mean enrichment 的 bootstrap 95% LCB >1；
- 每 gene extras≤2；
- ε-uniform probability；
- admission source、model revision、contract hash。

多 shape：

- 先按實際 `reduce_fn` 聚合 whole-config utility；
- 再做 cluster-level admission；
- 不做無限制 per-shape extras union。

任何 V0 candidate 消失，該 arm 失效。

## 7. 實作步驟

1. 鎖定 M06 eligible model、hyperparameters、shapes、seeds。
2. 從 M02 artifacts 產 A-safe manifests。
3. 跑 machine checks：
   - V0 subset；
   - extras≤2；
   - legal/support/LCB；
   - ε floor；
   - candidate ordering。
4. 在 1 pilot shape 跑五 arms，驗 actual space與initial frequency。
5. 擴至 preregistered development shapes。
6. Primary 使用 fixed budget；natural-stop另做 faster-but-worse。
7. 每 champion 獨立重測與 correctness。
8. 計算 main effects與 interaction：
   - `B - uniform within V0`；
   - `A-safe - V0 under uniform`；
   - `A-safe+B - V0+B`；
   - `Vwide+uniform - V0+uniform`。
9. 執行 offline A-hard diagnosis。
10. 決定 A 的去留。

## 8. A-hard offline diagnosis

A-hard 只使用 development real-score pool，不跑 GPU arm、不影響 treatment。

程序：

1. 依 model mass 建保留 95% mass 的最小候選集合。
2. 檢查被刪 candidates 是否包含：
   - 任一 remeasured champion；
   - top-1% true configs 的必要值；
   - 對 attainable median 有關鍵貢獻的值。
3. 計算：
   - champion deletion count；
   - attainable median drop；
   - top-1% config deletion fraction。

永久否決 A-hard 的任一條件：

- 刪掉任一 remeasured champion；
- attainable median 掉 >1%；
- 刪掉 >5% top-1% true configs。

即使沒觸發，也只能寫「此 dev pool 未抓到危險」，不能宣稱 held-out 安全或上線。

## 9. Metrics

- M00 鎖定的 time-to-target estimand；
- matched-budget verified GFLOPS；
- final quality ratio；
- per-shape median/P10/worst；
- invalid/duplicate/compile failure；
- candidate eval、candidate×shape samples、wall time；
- champion extra usage；
- main effects／interaction；
- diversity/termination/faster-but-worse；
- correctness。

## 10. 驗收、否證與停止條件

- **M07.ACC.A-SAFE-INVARIANT**：每 run 證明 `V0⊆VA⊆legal domain`、extras≤2、ε floor。
- **M07.ACC.A-INCREMENTAL**：相對 `V0+B`，time-to-target改善≥15%或matched-budget GFLOPS≥1%。
- **M07.ACC.NONINFERIOR**：final verified quality regression≤1%。
- **M07.ACC.OPERATIONAL**：沒有不可接受 invalid/dilution/correctness/faster-worse。
- **M07.GATE.KEEP-A**：以上全部成立，A-safe+B 可進 M08。
- **M07.GATE.DROP-A**：incremental benefit 不成立或 operational 問題，淘汰 A；B 仍可進 M08。
- **M07.FAL.WIDEN-ONLY**：V0 被刪，run 無效。
- **M07.FAL.A-HARD**：offline 任一危險條件成立，永久否決 hard pruning。

## 11. 預期狀況、診斷與解法

### 狀況 A：A-safe+uniform 好，但 A-safe+B 沒更好

- 解讀：A與B可能推薦重疊，或 interaction造成過度集中。
- 解法：依 primary incremental criterion 決定；不能把 A 的單獨效果當 A+B 通過。

### 狀況 B：A-safe+B 好，Vwide+uniform 差

- 解讀：有用 extras 存在，但完整 widening 稀釋；支持 model selection而非無條件擴域。

### 狀況 C：invalid rate 增加

- 診斷：逐 extra/rejection reason。
- 解法：修 conditional admission或淘汰 extra；不能把 invalid 少測造成的低 evaluation 當 speedup。

### 狀況 D：A-safe 使用 model evidence，但 extras 從 judgment/holdout 選

- 解法：判 leakage，run 作廢；只允許 development/guidance evidence。

### 狀況 E：M04 已 drop A

- 解法：M07 execution status=`skipped_by_gate`；parent記 M04 evidence。未執行不得建立 M07 report或填結果。

## 12. 執行完成後的報告

只有實際完成某 cohort 的 factorial 才建立：

- `../reports/m07-exp2-a-safe-b-factorial-nonstreamk-report.md`
- `../reports/m07-exp2-a-safe-b-factorial-streamk-report.md`

報告需列 hypothesis、A-safe admission audit、五 arms、main/interaction effects、A-hard offline 結果、能與不能支持的結論、遇到的 invalid/dilution/leakage/faster-worse 狀況與解法，最後給 `keep-A`、`drop-A`、`blocked` 或 `inconclusive`。
