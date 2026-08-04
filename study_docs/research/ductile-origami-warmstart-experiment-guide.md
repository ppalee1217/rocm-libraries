# Ductile Factorized Guidance 實驗白話導讀與問答（hub）

> **文件角色：**這是一份給第一次閱讀者使用的白話導讀與 FAQ hub。它不是 experiment authority，也不會取代正式的 charter、experiment plan、checkpoint design、lock 或 report。
>
> **已重整為 slim hub（2026-08-04）：**原本的長篇正文已依主題拆分到 [`ductile-origami-warmstart/qa/`](ductile-origami-warmstart/qa/)。本檔只保留角色宣告、一段 overview 與下方 qa/ 連結目錄；細節請進各主題檔。
>
> **衝突處理：**若本文件和正式文件衝突，以 [research charter](surrogate-dse-plan.md)、[experiment plan](ductile-origami-warmstart-experiment-plan.md)、[active checkpoint index](ductile-origami-warmstart/README.md) 及各 checkpoint design 為準。
>
> **歷史快照：**原 §§1–22 最初依 2026-07-29 的 S10R2 狀態整理（HEAD `51c7667212bf40f0e893fc026ee65450d06d72ff`）。S10R2 後來以 inconclusive／edge null 結束；相關歷史內容已集中到 [qa-08](ductile-origami-warmstart/qa/qa-08-faq-and-historical-snapshots.md)。
>
> **2026-08-04 current status override：**S10R3 已 terminal negative；S10R4 已 retired／not evaluated；S11 已 sealed `LOCKED_READY`（尚無 S11/S12 result、report 或 edge）。§23 的 S10R3 專題問答只保留 historical explanation，不是 current entry；最新狀態以 [active checkpoint index](ductile-origami-warmstart/README.md)、formal artifacts 與 Git history 為準。

---

## Overview（一段看懂）

本研究要檢驗：Formocast 對「一整組」kernel config 的 physics 效能評分，經 **per-gene factorization（邊際化）** 後，能否為 frozen gfx942 non-StreamK Ductile search space 中「尚未加權的 residual genes」提供有用的第 0 代（Gen0）抽樣偏好；若不能，訊號消失在哪一層。這是 stage-gated mechanism study（S00→S10 系列 entry→S11 factorization→S12 real-score→S13 Gen0→S20 persistence→S30/S31 replication→條件式 S40/S41），不是完整 tuning speedup 或 deployment。目前狀態：S11 已 sealed `LOCKED_READY`、S12 以下 gated；細節與問答見下方各主題檔。

## 主題目錄（qa/）

- [QA-00 — 總覽、閱讀順序與來源](ductile-origami-warmstart/qa/qa-00-overview-reading-order-sources.md)
- [QA-01 — 基礎名詞](ductile-origami-warmstart/qa/qa-01-terminology-design.md)
- [QA-02 — Ductile Gen0 與 nominal／valid support](ductile-origami-warmstart/qa/qa-02-ductile-gen0-and-nominal-valid-support-design.md)
- [QA-03 — S11 factorization 與 metric（含 2026-08-04 current sealed 機制）](ductile-origami-warmstart/qa/qa-03-s11-factorization-and-metric-design.md)
- [QA-04 — 下游 checkpoints S12–S41](ductile-origami-warmstart/qa/qa-04-downstream-checkpoints-s12-s41-design.md)
- [QA-05 — Controls 與 Formocast rejection layers](ductile-origami-warmstart/qa/qa-05-controls-and-formocast-rejection-layers-design.md)
- [QA-06 — Origami／Formocast ecosystem](ductile-origami-warmstart/qa/qa-06-origami-formocast-ecosystem-design.md)
- [QA-07 — 價值、風險、治理與 timeboxes](ductile-origami-warmstart/qa/qa-07-value-risks-governance-timeboxes-design.md)
- [QA-08 — FAQ 與歷史快照（S10R2／S10R3）](ductile-origami-warmstart/qa/qa-08-faq-and-historical-snapshots.md)

## Authority（正式文件，衝突時以這些為準）

- [Research charter](surrogate-dse-plan.md)
- [Experiment plan](ductile-origami-warmstart-experiment-plan.md)
- [Active checkpoint index](ductile-origami-warmstart/README.md)
