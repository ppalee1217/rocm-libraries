# `reports/` — 檔案配置與命名規則

2026-08-13 訂定。訂定原因:S14 一度出現三個檔名不一致的「報告」,其中兩個其實是工作筆記,
而 pre-registration 指定的正式報告路徑上**沒有檔案**。以下規則存在的目的是讓這種漂移
無法再次悄悄發生。

## 規則

1. **一個 `scientific_gate` 一份 closure report。** gate 是科學單位,報告是它的終端產物。
2. **closure report 的檔名 == 該 gate design 的 `formal_report_path`。** 兩者不一致時,
   **改檔案,不改 design**。為了遷就漂移掉的檔案去修改 pre-registration,等於事後修改預註冊。
3. **除 closure report 外,`reports/` 底下任何地方都不得使用 `*-report.md` 以外會被誤認為
   正式報告的命名**;per-shape 附冊是唯一例外,且必須帶上 §0 的附冊 banner(見下)。
4. **設計文件與報告永遠分開。** 結果不寫進 design;design 是 pre-registration,它的證據價值
   來自「gate 的文字早於資料存在」這件事可被檢驗。
5. **工作筆記不放在報告目錄。** 放 `working-notes/`,並照該目錄 README 的規則處理。

## 目前配置

```
reports/
  report-source-index.md / .zh-Hant.md            跨 gate 的 non-authority 參考索引(雙語鏡射)
  gen0-factorization-blocker-memo.md              design 預先指定的 terminal blocker memo
  README.md                                       本檔:命名與擺放規則
  staged/                                         所有 gate 的 closure report 都在這裡
    s00-foundation-verification-report.md
    s10-stage1-entry-gate-report.md
    s10r2-stage1-support-aware-entry-report.md
    s10r3-stage1-bounded-cover-entry-report.md
    s11-stage1-model-only-factorization-report.md
    full-ga-baseline-vs-guided-outcome-report.md  S14 唯一 formal report(結論總結 + index)
    s14-medium-report.md                          └ per-shape 附冊:medium(confirmatory)
    s14-large-report.md                           └ per-shape 附冊:large(confirmatory)
    s14-tiny-report.md                            └ per-shape 附冊:tiny(探索性)
  working-notes/                                  已被取代的工作輸入,不得引用
```

## S14 的兩層結構(2026-08-13 由 owner 決定)

- **`full-ga-baseline-vs-guided-outcome-report.md` 是唯一 formal report。** 它承載
  evidence-independent 的方法與 pins、**跨 shape 的結論總結**、gate 判定、claim ladder,
  以及指向三份 per-shape 附冊的 index。gate 是跨 shape 的**連言**,所以只有這一份能陳述
  「S14 過了沒有」。
- **三份 per-shape 附冊承載詳細實驗記錄** —— 逐 seed 數字、trajectory、remeasure、偏差、
  量測稽核、根因。每份都同時涵蓋 capped(P0=512)與 native(P0=11,405),因為 native 是
  design §12 的 robustness addendum,屬於**同一個 gate 之內**,不是第二個 gate。
- 附冊**不得單獨陳述 S14 outcome**,每份開頭必須帶 banner 指回 formal report。

## `staged/` 是什麼

**所有 gate 的 closure report 一律放這裡。** S00/S10/S10R2/S10R3/S11 的 design frontmatter
本來就把 `formal_report_path` 預註冊成 `reports/staged/…`。S14 原本預註冊的是 `reports/…`
(無 `staged/`),owner 於 2026-08-13 決定統一,已以 `REPORT-LOCATION-20260813` 修改 S14 design
的 `formal_report_path` 並留下 amendment 紀錄(design §12A)。

目錄名稱**不代表狀態** —— `staged` 是歷史命名,不是「未定稿」的意思;各報告的狀態看自己的
`report_status` frontmatter。規則 2 仍然成立:檔名與位置以各 gate design 的 `formal_report_path`
為準,兩者不一致時**先確認是漂移還是 owner 決定**:漂移就搬檔案,owner 決定就改 design 並留痕。
