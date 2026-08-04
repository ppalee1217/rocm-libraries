# QA-02 — Ductile Gen0 與 nominal／valid support

> **文件角色：**這是從 [實驗白話導讀 hub](../../ductile-origami-warmstart-experiment-guide.md) 拆分出來的白話導讀主題檔，方便在單一主題上持續討論。它不是 experiment authority，也不是 contract、lock 或 report，不會取代正式的 charter、experiment plan、checkpoint design、lock 或 report。
>
> **衝突處理：**若本檔與正式文件衝突，以 [research charter](../../surrogate-dse-plan.md)、[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)、[active checkpoint index](../README.md) 及各 checkpoint design 為準。
>
> **2026-08-04 current status override：**S10R3 已 terminal negative；S10R4 已 retired／not evaluated；S11 已 sealed `LOCKED_READY`。沒有 S11/S12 result、effective checkpoint lock、report 或 edge；最新狀態仍須對照 active checkpoint index、formal artifacts 與 Git history。

---

## 5. Ductile 實際建立 Gen0 的流程

### Step 1：解析 YAML

讀入：

- problem type；
- sizes；
- ForkParameters；
- Groups；
- candidate order；
- weights；
- validation 設定。

### Step 2：建立 SearchSpace

每個 search-space key 可能是：

- ungrouped gene，例如 DepthU；
- grouped categorical key，例如 `group_0`。

SearchSpace 內部先保存 candidate indices，再用 map 轉回實際 values。

### Step 3：weights 轉 probabilities

有 weight vector 的 key：

```text
p = exp(-weight_beta × normalized_weight)
p = p / sum(p)
```

沒有 weight 的 key：

```text
uniform
```

### Step 4：解析 initial population size

GA 先接收 requested `pop_size`，再依 search-space cardinality 決定 resolved population。

如果最大 key 的候選數比 requested population 大，Ductile 可能增加 early-generation population。

### Step 5：Nominal draw

每次抽樣為每個 key 選一個 index：

```text
group_0             選一個 candidate
DepthU              選一個 value
PrefetchGlobalRead  選一個 value
WorkGroupMapping    選一個 value
...
```

這形成一個 nominal full config。

### Step 6：valid_fn

SearchSpace 將 indices 轉成實際 values，呼叫 `valid_fn(full_config)`。

- `true`：保留；
- `false`：丟棄並繼續抽。

### Step 7：去重與填滿 population

合法 config 仍可能被重複抽到。

Ductile 使用 `IndividualSet` 去重，直到收集足夠多不同合法 configs，或到達 max iterations。

### Step 8：形成 Gen0

收集到的合法且不重複完整 configs 形成 initial population。

### Step 9：評估

將 configs 交給 evaluator：

- generate kernel；
- compile；
- correctness；
- GPU benchmark；
- 計算 fitness。

### Step 10：後續世代

若 `n_gen > 1`，才繼續：

- survival；
- selection；
- mating；
- mutation；
- 下一代評估。

---

## 6. Nominal space、valid support 與 operational Gen0

### 6.1 Nominal search space

YAML 中所有候選值的 Cartesian product：

```text
NominalSpace
= 所有 YAML candidate combinations
```

YAML 列出某個 value，只表示它是名義候選，不保證它能和其他 values 組成合法 solution。

### 6.2 Valid support

```text
ValidSupport
= { x ∈ NominalSpace | valid_fn(x) == true }
```

它是 nominal space 中 Ductile 真正可能接受的子集合。

組合可能因以下原因失效：

- MacroTile／WorkGroup 不相容；
- DepthU 與 K／MatrixInstruction 不相容；
- vector width 不符合資料排列；
- LDS／VGPR／occupancy 限制；
- GSU／LSU／prefetch 約束；
- dtype／transpose／architecture 限制；
- solution resolution 無法完成。

### 6.3 `pi_nominal`

YAML 和 weights 定義的原始抽樣分布，尚未考慮 validity。

### 6.4 `pi_valid`

```text
pi_valid(x)
= pi_nominal(x | valid_fn(x)=true)
```

也就是從 nominal distribution 抽樣後，只看被 validator 接受的 occurrences。

Validity rejection 會改變實際 frequencies。即使兩個 values 的 nominal probability 相同，如果其中一個 value 幾乎都搭配成無效 config，它在 valid support 中就很少出現。

### 6.5 `Pi_gen0,P0`

真正 Gen0 不是 P0 個完全獨立的 `pi_valid` draws，因為還有：

- duplicate removal；
- population fill；
- max iterations；
- fallback sampling；
- joint population effects。

所以研究分開處理：

- 用 `pi_valid` 建 model marginals；
- 用 exact `SearchSpace.sample(P0)` replay 看 operational sampler；
- 用正式 Gen0 populations 測真實 endpoint。

---

