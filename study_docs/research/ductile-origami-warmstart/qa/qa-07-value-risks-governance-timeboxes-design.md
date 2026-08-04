# QA-07 — 價值、風險、治理與 timeboxes

> **文件角色：**這是從 [實驗白話導讀 hub](../../ductile-origami-warmstart-experiment-guide.md) 拆分出來的白話導讀主題檔，方便在單一主題上持續討論。它不是 experiment authority，也不是 contract、lock 或 report，不會取代正式的 charter、experiment plan、checkpoint design、lock 或 report。
>
> **衝突處理：**若本檔與正式文件衝突，以 [research charter](../../surrogate-dse-plan.md)、[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)、[active checkpoint index](../README.md) 及各 checkpoint design 為準。
>
> **2026-08-04 current status override：**S10R3 已 terminal negative；S10R4 已 retired／not evaluated；S11 已 sealed `LOCKED_READY`。沒有 S11/S12 result、effective checkpoint lock、report 或 edge；最新狀態仍須對照 active checkpoint index、formal artifacts 與 Git history。

---

## 18. 實驗價值與主要風險

### 18.1 研究有沒有價值？

有，但範圍狹窄。

它不是首次使用 model 做 tuning，也不是首次有 problem-dependent initialization：

- GEKO 已有 existing group guidance；
- Formocast 已有 whole-config pre-screen。

真正的新問題是：

> Whole-config physics signal 能否透過既有 per-gene hook 保留下來？

這個問題可反證，而且各種 negative 都能定位 engineering failure layer，因此適合作為 bounded mechanism study。

### 18.2 正向成功不是唯一有價值結果

有價值的負結果包括：

- nominal space 和 valid support 嚴重錯位；
- Formocast ranking fail；
- ranking 好但 factorized prior fail；
- oracle 也失敗，表示交互作用太強；
- F 不勝 G，existing guidance 已飽和；
- F 不勝 S，只有 entropy concentration effect；
- offline prior 好，但 sampler/dedup 洗掉；
- Gen0 好，但 H10 washout；
- 兩 held-out clusters 異質。

### 18.3 最大風險

- Valid support 太稀疏；
- 沒有任何 residual gene 通過 S11 criteria；
- Formocast whole-config ranking 不足；
- factorization 丟失交互作用；
- resolved P0 遠大於 requested 64；
- GPU/compile成本超過 timebox；
- 多重 AND gate 導致高 false-negative；
- Stage 4 四-cluster data floor短期內不可達。

---

## 19. 新版 Agent 治理

### 19.1 三種單位

#### Scientific gate

不能合併或繞過的 criterion/edge。

#### Execution tranche

相容相鄰 gates 可共享：

- planner；
- implementer；
- verifier；
- run root；
- repair ledger。

#### Closure unit

共用 terminal report、parent update、staged audit、commit。

共享 tranche 不會刪除 scientific gate。

### 19.2 Tranches

- `T-S10R2`：S10R2 standalone；
- `T-S1-MECHANISM`：S11 → S12 → S13；
- `T-S20`：S20 standalone；
- `T-S3-REPLICATION`：S30 → S31；
- `T-S4-LEARNED-RESIDUAL`：S40 → S41。

### 19.3 Compact gate record

Tranche 中間的 positive gate 只寫小型 machine-readable record，沿 edge繼續，不立即做完整 closeout。

若中途 negative/inconclusive，才寫該 gate terminal report並停止。

最後一關 report 整合前面 compact records。

### 19.4 Resource budgets

以下消耗跨 generation、successor、sibling、replacement、restart、new root 累計：

- wall time；
- CPU/GPU time；
- storage；
- throughput samples；
- pre-empirical engineering；
- repair rounds；
- fresh threads。

不能因換名字或清理磁碟就 reset。

### 19.5 A34／A35

- A34 核准 prospective calibration boundary，要求先量 CPU/GPU/storage成本再 numeric relock。
- A35 將 S10R2 R2 repair round上限從 3 提高到 6，但 rounds 1–3完整 carry over，不能歸零。

---

## 20. Timeboxes

- Stage 1：最多 7 個 hands-on工作日；
- Stage 2：target 4 日、5 日 planning envelope；
- Stage 3：7 日 planning envelope；
- Stage 4：hard cap 5 日，且不是必跑。

Stage2／3的day envelopes是Layer-C record＋notify telemetry，不是scientific停止界線或
完成保證。Operator記錄throughput／projection並通知後繼續完整frozen workload；只有direct
evidence連到unsafe operation、platform／allocation不可用、完整workload／verification／
artifact preservation無法完成、optional stopping、evidence integrity或explicit frozen
scientific resource boundary時才safe-pause。Day count本身不能判negative／inconclusive、
形成edge或授權縮H10／arms／seeds／two-cluster denominator。

下列是 **S10R2 專屬的歷史 numeric caps**（2026-07-29 era），只作歷史紀錄，**不是**目前
S10R3／S11 path 的預算；current 資源邊界以 [experiment plan](../../ductile-origami-warmstart-experiment-plan.md)
與 [active checkpoint index](../README.md) 為準（例如 S10R3 的 caps 與下列不同）：

- wall：11,827 秒；
- CPU：62,396 秒；
- GPU：2,901 秒；
- transient storage：2 GiB；
- safety factor：2.0。

（當時規則）若首 1% reforecast 顯示 projected cost 超過鎖定邊界，必須 safe pause，不能縮
workload 救回。
