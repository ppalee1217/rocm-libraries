# `working-notes/` — 已被取代的工作輸入，**不是報告，不得引用**

這個目錄裡的檔案是 subagent 在分析過程中產出的**工作筆記**。它們曾經被錯放在
`reports/staged/`，名字看起來像 closure report，實際上不是。內容已折進正式報告。

**規則**

- **不得在任何報告、authority 文件或對外陳述中引用這裡的檔案。** 要引用就引用正式報告。
- 這裡的內容**可能已經過時**。正式報告持續更新，這裡的不會。
- 這是**暫存**。等 S14 正式報告完成、經 owner 確認後，這些檔案會被移除 —— 移除理由是避免
  後續整理時把過時資訊誤讀為現況。這是 owner 於 2026-08-13 明示的決定，優先於本 study 平常
  的 preserve-never-delete 慣例；在 owner 確認之前不得移除。
- 移除前，任何這裡有、正式報告沒有的事實,都必須先搬進正式報告。移除不得造成證據淨損失。

**⚠ 為什麼現在還不能移除:** native `large` 實驗仍在執行中(2026-08-13 時五個 baseline
seed 仍在 Gen0 抽樣),S14 正式報告的內容還會再變動。要等 large 收斂、報告定稿之後才輪到
這一步。

## 目前內容

| 檔案 | 原本是什麼 | 已折進 |
|---|---|---|
| `s14-native-p0-medium-analysis.md` | `NATIVE-P0-ROBUSTNESS-20260811(b)` 的 native-Gen0 (11,405) medium 分析,Q1/Q2/Q3 | `../staged/s14-medium-report.md` |
| `s14-tiny-remeasure-analysis.md` | tiny `(8,8,1,128)` 7× interleaved remeasure 分析(意外的 null control) | `../staged/s14-tiny-report.md` |

兩份都已於 2026-08-13 由英文改寫為繁體中文,數值與識別字經機械比對驗證無差異
(medium 1514/1514 numeric token、307/307 code span;tiny 1306/1306、265/265)。
