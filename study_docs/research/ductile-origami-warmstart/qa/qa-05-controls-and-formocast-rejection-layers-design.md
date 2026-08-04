# QA-05 — Controls 與 Formocast rejection layers

> **文件角色：**這是從 [實驗白話導讀 hub](../../ductile-origami-warmstart-experiment-guide.md) 拆分出來的白話導讀主題檔，方便在單一主題上持續討論。它不是 experiment authority，也不是 contract、lock 或 report，不會取代正式的 charter、experiment plan、checkpoint design、lock 或 report。
>
> **衝突處理：**若本檔與正式文件衝突，以 [research charter](../../surrogate-dse-plan.md)、[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)、[active checkpoint index](../README.md) 及各 checkpoint design 為準。
>
> **2026-08-04 current status override：**S10R3 已 terminal negative；S10R4 已 retired／not evaluated；S11 已 sealed `LOCKED_READY`。沒有 S11/S12 result、effective checkpoint lock、report 或 edge；最新狀態仍須對照 active checkpoint index、formal artifacts 與 Git history。

---

## 9. Same-entropy shuffled control

### 9.1 為什麼需要？

如果 Formocast prior 比 uniform 更集中，F 勝 G 可能只是因為：

- search space 變集中；
- diversity 改變；
- duplicates 改變；
- 更常反覆抽少數 configs。

不一定表示 Formocast 把高機率放到正確 values。

### 9.2 機制

假設 F：

```text
Values: A    B    C    D
F:      55% 25% 15% 5%
```

S 使用完全相同的 probability multiset，但重新貼 labels：

```text
Values: A    B    C    D
S:      15% 55% 5%  25%
```

因此 F、S 有相同：

- entropy；
- concentration；
- epsilon floor；
- cardinality；
- guided gene 數；
- existing group weights。

唯一主要差別是：

- F：高機率放在 Formocast 認為好的 values；
- S：相同機率被 deterministic non-identity permutation 打亂。

Shuffle 必須在 real GFLOPS 前鎖定，不能看結果後挑一個特別差的 shuffle。

### 9.3 解讀

- F > G 且 F > S：有證據支持 Formocast 方向。
- F > G 但 F ≈ S：可能只是 concentration/entropy effect。
- F ≤ S：Formocast 沒證明比亂貼 labels 更好。
- F、S、G 都接近：可能 residual effect 很小、existing guidance 已飽和，或 validity/dedup 把差異洗掉。

Nominal entropy 相同不保證 realized population entropy 完全相同，因此還要報 validity、duplicates、realized frequencies 與 diversity。

---

## 15. Formocast rejection、early termination 與 runtime queue

這裡必須分成三層。

### 15.1 Ductile validity rejection

發生在 Formocast 之前：

- Python `valid_fn` false；
- solution resolution failure；
- C++ `checkSolution` hardware/problem/task predicate false。

這些沒有 Formocast score，不能稱為 Formocast rejection。

### 15.2 Formocast early-terminate sentinel

`predictedPerformance()` 正常回傳：

- predicted `microSeconds`；
- `hitRate`；
- tile、DepthU、GSU、loop、memory、math 等模型資訊。

遇到特定 guard，Formocast 不繼續完整 simulation，而直接回：

```text
microSeconds = 9,999,999.9
hitRate = 0
```

常見 early-terminate guard包括：

- GlobalSplitU=0；
- MacroTile 相對 problem M/N 過大；
- BF16/Half 的 K、DepthU、MatrixInstruction 組合不適合；
- DirectToLds 與 M/N/MT 不相容；
- derived PLR=0。

`9,999,999.9` 是有限浮點數：

```text
isfinite(9999999.9) == true
```

它不是 NaN／Inf／exception，而是一個「模型沒有提供正常估計、請視為極差」的 sentinel。

舊 S10 helper 只用 non-finite 判定，因此會漏掉這種 finite sentinel。

### 15.3 Runtime PredictionThreshold exclusion

Runtime 對通過 `checkSolution` 的 solutions：

1. 呼叫 Formocast；
2. 按 predicted latency stable sort；
3. 依 PredictionThreshold 建 benchmark queue。

Sentinel 通常排在最後，但 sentinel 不等於 runtime exclusion。

如果 threshold >1，prediction filtering 被停用；若 threshold 包含全部候選，sentinel 也不一定被排除。

因此新版必須分欄：

```text
ductile_validity_status
formocast_model_status
runtime_queue_status
```

不能全部叫 rejection。

---

## 16. 為什麼 valid-support discovery 用 CPU，不用 GPU？

目前 discovery 找的是：

> 符合 Ductile 規則的合法 config。

不是：

> 跑得最快的 config。

每個候選要做：

- Python config construction；
- Ductile validation；
- solution resolution；
- object/dict 操作；
- KernelWriter initialization；
- rejection taxonomy；
- ledger/provenance。

這些是大量分支、可變資料結構與 host-side 邏輯，不是 GPU 擅長的同質數值運算。

多數候選若連合法 solution 都建不出來，也不可能直接丟 GPU benchmark。

若要 GPU 化，等於要把完整 Python/Ductile validator 重寫成 GPU kernel，還要證明和 pinned CPU validator完全一致，工程成本很高且可能因 branch divergence 無法加速。

較實際的加速方向是 bounded CPU parallelism，但必須保持 deterministic ledger/order/lock semantics。

---

## 17. 「YAML 合法候選」不等於「一定有 valid config」

合法有多層：

1. 數值在允許範圍內；
2. YAML 把它列為 candidate；
3. 至少存在一個完整 joint config 通過 valid_fn；
4. 能 resolution/generate/compile；
5. GPU correctness 通過；
6. 效能好。

YAML candidate 只直接支持前兩項。

例如 `DepthU=1024` 是 actual YAML 的最大 DepthU 候選，不是隨便選的數字；但它是否能和其他 values 組成 valid config，仍需 joint validation。

舊 conditional stream 每次都固定 DepthU=1024，所以 zero-hit 不是「1024 很少被抽到」，而是「在那些 draws 中，其他參數搭配沒有形成 accepted joint config」。

這仍不能從 stochastic zero 推導 support 為零。

---

