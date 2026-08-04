# QA-01 — 基礎名詞

> **文件角色：**這是從 [實驗白話導讀 hub](../../ductile-origami-warmstart-experiment-guide.md) 拆分出來的白話導讀主題檔，方便在單一主題上持續討論。它不是 experiment authority，也不是 contract、lock 或 report，不會取代正式的 charter、experiment plan、checkpoint design、lock 或 report。
>
> **衝突處理：**若本檔與正式文件衝突，以 [research charter](../../surrogate-dse-plan.md)、[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)、[active checkpoint index](../README.md) 及各 checkpoint design 為準。
>
> **2026-08-04 current status override：**S10R3 已 terminal negative；S10R4 已 retired／not evaluated；S11 已 sealed `LOCKED_READY`。沒有 S11/S12 result、effective checkpoint lock、report 或 edge；最新狀態仍須對照 active checkpoint index、formal artifacts 與 Git history。

---

## 4. 基礎名詞

### 4.1 Whole config

一個 whole config 是一整組 kernel 參數，例如：

```text
{
  group_0: candidate_157,
  DepthU: 64,
  PrefetchGlobalRead: 2,
  WorkGroupMapping: 8,
  DirectToVgprA: false,
  ...
}
```

Formocast 的輸入是這種完整 config 加上 problem size、hardware 等資訊，不是單一 DepthU。

### 4.2 Gene 與 gene value

在 GA 的語境裡：

- gene：一個可調 search-space key；
- gene value：這個 key 的其中一個候選值。

例如：

```text
gene       = DepthU
gene values = [32, 64, 128, 256, 512, 1024]
```

一個 config 就像一條 chromosome，由每個 gene 選出的一個 value 組成。

### 4.3 Group

YAML 中有些參數不是獨立抽樣，而是綁成一整包。

例如一個 grouped candidate 可能同時帶有：

- MatrixInstruction；
- WorkGroup；
- GlobalSplitU；
- MIArchVgpr；
- 其他 tile/solution fields。

Ductile 會把這一整包視為一個 categorical key，例如 `group_0`，一次選一整包，而不是把裡面的欄位拆開抽。

目前 actual YAML 的 `group_0` 有 9,918 個 expanded candidates。

### 4.4 Weight、probability 與 guidance

Ductile 本來就有 generic weighted-sampling 機制。

YAML 若替某個 key 提供 weight vector，Ductile 會轉成 probabilities：

```text
probability ∝ exp(-weight_beta × (weight - minimum_weight))
```

因此：

- weight 越小，通常越常被抽；
- weight 越大，通常越少被抽。

沒有 weight 的 key 使用 uniform sampling。

目前 actual YAML 主要替 `group_0` 提供 9,918 個 weights。這些 problem-dependent weights 是既有的 GEKO/YAML guidance。

「Guidance」在這裡不是保證正確，而是一個非均勻 prior：

> 在尚未做真實 GPU benchmark 前，先告訴 sampler 哪些候選較值得優先嘗試。

### 4.5 Existing guidance

Existing guidance 指 Formocast 介入前，YAML 已經提供的 groups、candidate order 與 weights。

研究明確保護它們：

- 不拆 group；
- 不重排 candidates；
- 不覆蓋 existing weights；
- 不把 group 內欄位再當成獨立 residual genes。

### 4.6 Residual gene

Residual gene 不是「模型殘差」。

它表示：

> 扣掉 existing grouped/weighted guidance 後，剩下尚未被 guidance 處理的可調參數。

一個 gene 要成為 residual guidance 候選，至少必須：

- ungrouped；
- currently unweighted；
- frozen free；
- 有兩個以上候選值；
- mapping 完整；
- support classification 足夠完整。

例如 DepthU 在 actual YAML 中是 ungrouped ForkParameter，且沒有自己的 weight vector，所以它可能是 residual gene。

但如果 S10R2 對 DepthU 的任一 value 只能得到 `support_unobserved` 或 `support_proven_absent`，整個 DepthU gene 就不能進 S11 guidance，仍維持原本 baseline sampling。

### 4.7 Factorization

Factorization 是把：

> 這個完整 config 的 Formocast score

轉成：

> 在其他參數變動時，某個 gene value 平均是否比較有利。

例子：

```text
DepthU=32  出現在很多完整 configs 中 → 平均 model benefit 0.42
DepthU=64  出現在很多完整 configs 中 → 平均 model benefit 0.71
DepthU=128 出現在很多完整 configs 中 → 平均 model benefit 0.58
DepthU=256 出現在很多完整 configs 中 → 平均 model benefit 0.31
```

再把這些平均 benefit 轉成 per-value probabilities。

真正的風險是：效能可能依賴多個參數的交互作用。Factorization 只留下每個 value 的平均效果，可能丟失「DepthU=64 只有搭配某些 MacroTile 才好」的資訊。

### 4.8 Gen0

Gen0 不是 weight。

Gen0 是依 probabilities 抽出的初始完整 configs 集合：

```text
weights
  ↓
probabilities
  ↓
validity filter + dedup + population fill
  ↓
Gen0 initial population
```

它發生在 crossover、mutation、selection/survival 之前。

實驗 requested population size 是 64，但 Ductile constructor 可能依最大 categorical key 擴大 resolved `P0`。正式執行必須記錄實際 `P0`，不能用 nominal 64 假設成本。

### 4.9 Canonical config

Canonical config 是：

> 用固定規則序列化、排序與 hash 的完整 config。

相同語意的 config，即使 Python dict key order 不同，也必須得到相同 canonical bytes 和 SHA-256。

Canonicalization 通常包括：

- 把 numpy／bool／int／list／dict 轉成固定 plain representation；
- 固定 key order；
- 固定 JSON encoding；
- 禁止 NaN／Inf；
- 對固定 bytes 計算 SHA-256。

Canonical 不表示「最好」或「預設」。它的功能是：

- 去重；
- 穩定識別；
- 跨 mapping、correctness、noise、benchmark join；
- 防止中途替換候選；
- 讓 verifier 可重現。

「10 個 canonical configs」表示依預鎖 deterministic 規則選出的 10 個不同合法 configs，並固定它們的 identity。

---

