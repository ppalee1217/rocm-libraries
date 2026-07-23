---
milestone_id: M04
title: EXP-0b static profile 與 widen-only headroom
design_status: draft
execution_status: blocked
outcome: not_available
depends_on: [M00, M01.ALL]
cohorts: [nonstreamk, streamk]
planned_report_paths:
  - ../reports/m04-exp0b-widening-gate-nonstreamk-report.md
  - ../reports/m04-exp0b-widening-gate-streamk-report.md
---

# M04 — EXP-0b static profile 與 widen-only gate 設計

Parent plan：[Ductile 引入 Origami/Formocast 暖啟動](../../ductile-origami-warmstart-experiment-plan.md)

## 1. 白話目標

確認現有 V0 候選清單外，是否真的還有合法且有用的值。

「合法值比較多」不等於「搜尋會更好」：空間加寬會稀釋固定預算，還可能讓 population 變大。因此要一次只擴一個 family，直接量新增值帶來的品質，是否大於空間變大的成本。

## 2. 假設

**假設 M04-H1**：V0 漏掉至少一組對 gfx942 hot shapes 有用的合法 GRVW、DepthU 或 WGM 值；在相同實際 evaluation budget 下，加寬後的 median verified GFLOPS 至少提高 1%。

反證：

- 所有單 family 與 union widening 都沒有 ≥1% median uplift；
- 同時只增加 invalid、duplicate、population 或稀釋成本。

反證只淘汰 injection A，不否決 injection B。

## 3. 預期目標

1. 建立 V0、每個 family widening、Vwide union 的 exact search-space manifest。
2. 分辨「新增值沒有用」和「有用但固定預算被稀釋」。
3. 決定 M07 是否執行 A-safe factorial；若淘汰 A，記 `skipped-by-gate` 並允許 B-only 進 M08。

## 4. 結果能與不能說明什麼

能說明：

- V0 是否漏掉對 development workload 有用的合法值；
- 哪個 gene family 有 headroom；
- widening 對 invalid、duplicate、population、evaluation 與 wall time 的影響。

不能說明：

- model 能否正確挑出 A-safe extras；
- hard pruning 安全；
- B guidance 有效。

## 5. Search-space 定義

- `V0`：鎖定 baseline profile 的實際 candidate lists。
- `V_GRVW`：只擴 GRVW family。
- `V_DepthU`：只擴 DepthU family。
- `V_WGM`：只擴 WorkGroupMapping／WGM family。
- `Vwide`：通過 generator validity 流程的 union。

硬規則：

- 每個 widening 都必須滿足 `V0 ⊂ Varm`；
- `ValidParameters` 只表示候選母集合，不是特定 dtype/shape/config 的合法證明；
- 每個新增值都必須通過 `_initKernel` conditional completions；
- 不能刪 V0，不能把 compile failure 當作合法值；
- 每個 run 保存 candidate value 與 integer index 的 exact map。

## 6. 資料、arms 與 controls

資料：

- 使用 M03 相同的 pilot/development hot-shape registry；
- 不新增 model-selected shape；
- cohort 分開。

Arms：

1. `V0 + uniform`
2. `V_GRVW + uniform`
3. `V_DepthU + uniform`
4. `V_WGM + uniform`
5. `Vwide + uniform`

Controls：

- `weights=None`；
- 相同 paired seeds；
- 相同 complete candidate evaluation cap；
- 相同 generated YAML fitness、correctness、measurement；
- arm order 隨機交錯；
- 不以 generation 作公平預算。

## 7. 實作步驟

1. 從鎖定 revision 匯出 V0。
2. 從 generator legal-domain source 產生 candidate extras。
3. 對每個 `(gene,value)` 做 conditional validity pilot：
   - 固定該值；
   - 其餘 genes 按 V0／適用空間抽樣；
   - 執行 `_initKernel`；
   - 保存 valid/rejection reason。
4. 產生各 arm 的 `space-manifest.json`：
   - V0、extras、candidate index；
   - cardinality；
   - estimated/realized valid rate；
   - profile/revision hash。
5. 先跑 3 pilot shapes，確認 widening 沒有 silent mapping error。
6. 擴到 development shapes 與 ≥5 paired seeds。
7. 對每個 arm 以相同 actual complete candidate evaluation cap 比較：
   - anytime quality；
   - final remeasured GFLOPS；
   - invalid/duplicate；
   - realized population/decay；
   - candidate×shape samples、wall time。
8. 分析新增值是否出現在 champion 或 one-gene improvement 中。
9. 依 gate 決定 A 的狀態。

## 8. Metrics

- per-shape verified GFLOPS ratio vs V0；
- median、P10、worst ratio；
- complete candidate eval to matched quality；
- invalid、duplicate、compile failure rate；
- realized population size 與 decay mode；
- search-space cardinality delta；
- champion 使用新增值的比例；
- end-to-end wall time。

## 9. 判讀矩陣

- 有 ≥1% median uplift，成本可接受：A 有 headroom，進 M07。
- 有 ≥1% uplift，但 invalid／wall time 大增：M07 只允許 model-selected A-safe，Vwide 保留 dilution control。
- 無 median uplift，但少數 critical shape 明顯改善：標 heterogeneity；是否保留 A 需依 preregistered critical-shape policy，不能事後挑案例。
- 所有 family/union 無 ≥1% uplift且只稀釋：淘汰 A，M07 skip。
- correctness failure：先阻擋該 family；不能把錯誤高 GFLOPS 當 uplift。

## 10. 驗收、否證與停止條件

- **M04.ACC.SPACE-AUDIT**：每個 arm 有 exact V0/extras/index/validity manifest。
- **M04.ACC.BUDGET**：所有比較使用相同 complete candidate eval cap。
- **M04.ACC.A-HEADROOM**：至少一個 preregistered family 或 union 的 median verified uplift ≥1%，且不是 correctness／noise 假象。
- **M04.GATE.DROP-A**：全部 <1% 且只增加 dilution/invalid，A 永久退出本輪 GPU treatments。
- **M04.FAL.WIDEN-ONLY**：任一 arm 刪除 V0，該 run 無效並重做。
- **M04.STOP.INVALID**：新增 family 的合法 support 無法達到預先要求，該 family 不進 A-safe admission。

## 11. 預期狀況、診斷與解法

### 狀況 A：`ValidParameters` 有值，但 `_initKernel` 大量拒絕

- 解法：以 `_initKernel` 為準，保存 rejection reason；不把母集合存在當合法證據。

### 狀況 B：Vwide generation 較少但 evaluation 相同

- 原因：adaptive population/cardinality。
- 解法：以 complete candidate eval 與 benchmark samples比較；generation只作 trajectory。

### 狀況 C：新增值偶爾成 champion，但 median 無 uplift

- 解法：報分布與 preregistered strata，不因單一案例保留 A；A-safe admission仍需 M02/M07 的 model evidence。

### 狀況 D：widening 增加 compile failures

- 診斷：區分 `_initKernel` invalid、codegen failure、compile failure。
- 解法：修 generator validity gap或淘汰該 extra；不能將 failure 少測的成本算 speedup。

### 狀況 E：A 被淘汰

- 解法：M07 標記 `skipped-by-gate`，不建立假實驗報告；parent 記 gate evidence，B-only 可進 M08。

## 12. 執行完成後的報告

實際完成某 cohort 後才建立：

- `../reports/m04-exp0b-widening-gate-nonstreamk-report.md`
- `../reports/m04-exp0b-widening-gate-streamk-report.md`

報告需逐 family 列 hypothesis、space delta、actual budget、結果能支持的範圍、invalid/dilution 狀況與解法，最後明確給 `keep-A`、`drop-A`、`blocked` 或 `inconclusive`。不能把「寬域有 headroom」寫成「模型已能安全擴域」。
