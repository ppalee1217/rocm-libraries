# QA-09 — per-shape 重設計：為什麼從「一個 joint GA」改成「每個 shape 一個 GA」

> **文件角色：**這是從 [實驗白話導讀 hub](../../ductile-origami-warmstart-experiment-guide.md) 拆分出來的白話導讀主題檔，方便在單一主題上持續討論。它不是 experiment authority，也不是 contract、lock 或 report，不會取代正式的 charter、experiment plan、checkpoint design、lock 或 report。
>
> **衝突處理：**若本檔與正式文件衝突，以 [research charter](../../surrogate-dse-plan.md)、[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)、[active checkpoint index](../README.md) 及各 checkpoint design（尤其 [S14 design](../s14-stage1-full-ga-outcome-design.md) 與 [S11 design](../s11-stage1-model-only-factorization-design.md)）為準。本檔敘述的是 **2026-08-09 的 per-shape 重設計思路**，其正式化與封印仍以 S14 design 及未來 lock/report 為準。
>
> **2026-08-09 current status note：**本檔記錄的是「發現 aggregate-Q 缺陷 → 決定改 per-shape」的**推理過程**，含被否決的替代方案。它是 QA（由 charter／experiment-plan／README／designs 裁決），**不是** authority、contract、lock 或 report。文中所有 pilot 數字都是 **[BASELINE GPU]** pilot（見 §1），**不是** committed S14 result；最新狀態仍須對照 active checkpoint index、formal artifacts 與 Git history。
>
> **2026-08-10 後續 amendment note（本檔部分敘述已被下列 owner-approved 決定更新,以 charter/S14 design 為準）：**(1) **`ENTROPY-CAP-20260810`** —— per-shape guidance 的 entropy floor 由「二元排除 gene」改為「per-gene 混合強度 cap ρ(H_norm≥0.80 下納入最強的 DepthU/PrefetchGlobalRead)」(design-discussion 兩位 reviewer AGREE;S14 §10.3)。(2) **`CLAIM-SCOPE-S14-20260810`** —— charter §8.6a 放行 S14 **two-sided** 宣稱:資料支持時**得宣稱受測 shape 最終 tuned 品質提升**(bounded/modest power、不一般化、不預設結論、不誇大偽造),取代本檔敘述的「僅非退步/不宣稱 final superiority」。詳見 S14 design §10.3–§11 與 charter §8.6a。
>
> **2026-08-12 事實更正 `REDUCER-FACT-CORRECTION-20260812`(user-directed;文件更正,非 protocol 變更):** 本檔 §2.1／§2.2 對 **Ductile 多目標機制**的敘述有誤。`[CODE AUDIT]`:**Ductile 未實作 Pareto／非支配排序**(全樹 `pareto|non-dominated|nsga|crowding` 零結果),且 **`soo=False` 會內部縮併為純量**(`ga.py:95` `reduce_fn=np.max`;`ga.py:256–273` `pop.F = reduce_fn(scores / best.F, axis=0)`)。故 **`Q=max_s(GFLOPS_s/R_s)` 是 Ductile 的原生 fitness,不是 pilot 事後外加的步驟**。**§1 的實證缺陷、per-shape 決策、gate 與 claim 一律不變**;更正後論述為「Ductile **內建**的跨-size reducer 本身即缺陷所在,per-shape 使其退化為恆等而繞開」。詳見本檔 §2.1／§2.2 更正框、S14 design §10.1 更正框、`reports/report-source-index.md` §3.1.2。

---

## 前言：這份文件在回答什麼

到了 S14（Stage-1 的 full-GA outcome checkpoint，見 [QA-04](qa-04-downstream-checkpoints-s12-s41-design.md)），研究第一次要真的把 S11 交棒的 guidance 拿去跑**真正的 Ductile 基因演算法**，用真實 GPU 效能去回答那個核心問題：

> Gen0 的權重 bias，到底會不會影響 Ductile DSE 的最終結果？

S14 原本（見 [S14 design §6.1](../s14-stage1-full-ga-outcome-design.md)）的做法是：**跑一個 joint 的多目標 Ductile GA**，三個 problem size 一起演化，最後由 Ductile `soo=False` 的原生跨-size reducer 產生一個 aggregate 品質分數 `Q` 作為單一 champion 的依據。2026-08-09 的 pilot 資料一攤開，這個 `Q` 被發現有一個嚴重的**建構效度（construct validity）**缺陷——它會**獎勵雜訊、甚至把真正最好的 kernel 排到最後**。

這份文件白話講清楚：這個缺陷是什麼、pilot 資料怎麼揭穿它、為什麼「對照 code facts 才發現缺陷出在 Ductile 內建的跨-size reducer」、最後為什麼決定改成 **每個 problem shape 各跑一個 GA（per-shape）**，以及沿路上每一個「考慮過但沒採用」的替代方案為什麼被丟掉。目的是把**推理**留下來，不是把結論當權威。

---

## 1. 缺陷：aggregate-Q 會獎勵雜訊、把最好的 kernel 排最後

### 1.1 原本的 pilot 怎麼跑

原 S14 pilot 跑的是**一個** joint 多目標 Ductile GA。Ductile 預設就是多目標（`soo=False`），所以三個 locked size `(8,8,1,128)`、`(256,256,1,1024)`、`(2304,1024,1,214336)` 是**一起**被演化的；而 GA 內部就用一個 cross-size reducer 把三個 size 的表現壓成一個數字作為 fitness（見 §2）：

```text
Q(x) = max_s [ GFLOPS_s(x) / R_s ]
```

- `GFLOPS_s(x)`：kernel `x` 在 size `s` 上的真實 GPU 效能（越高越好）。
- `R_s`：該 size 的 noise-anchor 參考值（per-size 正規化，避免三個 size 的原始尺度亂比）。pilot 實測 `R = {tiny: 0.751728, medium: 3199.94, large: 180336.0}`（`[BASELINE GPU]`，noise anchors 3×3×7）。
- `max_s`：跨 size 取最大——**這正是缺陷的來源**。用 `max` 是刻意「承襲 S11 sealed `max_s`」（見 [QA-03 §0.3](qa-03-s11-factorization-and-metric-design.md)：一筆 config 的 benefit 用 `max` reducer 收）。

### 1.2 為什麼 `max_s` 是壞的：tiny 8×8 主宰一切

`max_s` 的意思是「只要在**任一個** size 上分數最高，整個 Q 就由那個 size 決定」。問題是三個 size 的 per-size ratio 量級**天差地遠**。把 pilot 五個 baseline seed 的 champion 逐 size ratio 攤開（`[BASELINE GPU]`，champion 獨立重測，數字為近似）：

| seed | tiny `(8,8,1,128)` ratio | medium `(256,256,1,1024)` ratio | large `(2304,1024,1,214336)` ratio | **aggregate `Q=max_s`** |
| --- | --- | --- | --- | --- |
| 14001 | ~4.9 | ~2.8 | ~1.26 | **4.965** |
| 14002 | ~4.9 | ~2.5 | ~1.00 | **4.885** |
| 14003 | ~4.3 | ~3.0 | ~1.36 | **4.262** |
| 14004 | ~4.3 | ~2.3 | ~1.01 | **4.289** |
| 14005 | ~2.7 | ~2.1 | ~2.7 | **2.662** |

看出來了嗎？**tiny 的 ratio 幾乎永遠是三者中最大的（≈4.3–4.9）**，所以 `Q=max_s` 幾乎總是被 tiny 8×8 綁架。而 tiny 8×8 正好是**最不可信**的那個 size：它的絕對 GFLOPS 只有 ≈2–4（launch jitter 主宰），S14 design §9 的 open preflight 早就記錄過它「重複量 Q 在 ~1.8↔2.8 跳」、`delta_noise≈1.83（182%）`主因就是它。換句話說：

> **Q 是被「量級最大、但雜訊也最大」的 size 決定的。** 它量到的與其說是「哪個 kernel 好」，不如說是「哪個 kernel 在那次量測剛好抽到 tiny 8×8 的高點」。

### 1.3 反例：seed 14005 的 champion 大 size 快一倍，卻拿最低分

最能戳破 `Q` 的，是 seed **14005** 這個反例。它選出的 champion 在**大 size** `(2304,1024,1,214336)` 上跑到 **≈480,141 GFLOPS**，其他 seed 的 champion 只有 **≈180k–246k**——它在真正 compute-bound、真正有工程意義的大問題上**快了將近一倍**。

然而它的 aggregate `Q = 2.662`，是五個 seed 裡**最低的**。為什麼？因為它的 tiny 8×8 ratio 剛好偏低（≈2.7），而 `Q=max_s` 只看那個被 tiny 主宰的最大值。它在大 size 的壓倒性優勢**完全沒有被計入**——`max_s` 一旦選中 tiny，大 size 快多少都無所謂。

**誤解 vs 正解：**

> ❌ 誤解：「aggregate Q 選出來的 champion，就是三個 size 綜合最好的那個。」
>
> ✅ 正解：pilot 直接反證。`Q=max_s` 選中的是「在最吵的 tiny size 上剛好高」的 kernel；一個在大 size 快一倍的**真正好** kernel（seed 14005），反而因為 tiny 分數低而被排到最後。**Q 不是在選好 kernel，它在選 tiny 8×8 的雜訊贏家。**

這不是「門檻調一調」能救的。這是 metric 本身的**建構效度**壞掉：它獎勵的東西（tiny 的噪音高點）不是它宣稱要衡量的東西（kernel 品質）。

---

## 2. 對照 code facts：缺陷出在 Ductile 內建的跨-size reducer

發現缺陷後，回頭看 code 才意識到：**問題不只是「`max` 這個選擇不好」，而是「把三個發散 size 綁在一條 GA 上、再用任何單一純量去排序它們」這個框架本身，就不適合本研究的問題。** 三個 code fact 把整件事重新框住。

### 2.1 Ductile GA 本來就是多目標的（`soo=False`）

Ductile GA 的建構子預設 `soo=False`（single-objective off），意思是它**天生就是多目標**：

- `ga.py:49`：`soo: bool = False`
- `ga.py:95`：`self.reduce_fn = np.mean if self.soo else np.max`

在 `soo=False` 下，每個 config 的 fitness 起初是一個 **`(3, N)` 的矩陣**（3 個 size × N 個候選）——但 **GA 內部就會把它壓成一個純量**，並不保留 per-size 的專精者。`ga.py:256–273`：

```python
best.F = scores.max(1)                                   # 每個 size 的 incumbent（即正規化分母 R_s）
pop.F  = self.reduce_fn(scores / best.F[..., None], 0)   # soo=False → np.max
```

也就是說，那個 `else np.max` **正是**把跨 size 壓成單一分數的地方：**`Q_c = max_s(GFLOPS_{s,c} / R_s)` 就是 Ductile `soo=False` 的原生 fitness**，不是 pilot 事後外加的一步。

而且 **Ductile 並未實作 Pareto／非支配排序** —— 對整個 ductile 樹搜尋 `pareto|non-dominated|nsga|crowding`，**零結果**。所以並不存在一條可以被「壓縮」的 Pareto front；`soo=False` 的「多目標」只是「先分 size 評分、再取最大值」而已。

**真正的缺陷因此是**：`max` 讓一個候選只憑**它剛好表現最好的那一個 size** 被評分，其餘兩個 size 直接丟棄 —— 而 tiny 是雜訊最大的 shape（±40–45%），於是一次幸運的 tiny 量測就能主導 champion 選擇（§1 的實證）。

> **更正註記 `REDUCER-FACT-CORRECTION-20260812`（2026-08-12，user-directed）：** 本節原先敘述為「GA 用 Pareto 前緣做 survival、不會自己壓成純量，`Q=max_s` 是 pilot 事後外加」——經 `[CODE AUDIT]` 證實有誤，已依上文**直接更正**（原文可於 Git history 追溯）。**§1 的實證缺陷、per-shape 決策、gate 與 claim 均不受影響**；更正後理由更強：問題出在 Ductile **內建**的跨-size reducer，而非我們多加的步驟。詳見 S14 design §10.1、`reports/report-source-index.md` §3.1.2。

### 2.2 單一跨-size champion 不符下游語意——Tensile 早就 per-size 選解了

這才是關鍵領悟：Tensile 的三階段 pipeline（見 [tensilelite guide](../../../../projects/hipblaslt/tensilelite/CLAUDE.md)）裡，`3_LibraryLogic`（`LibraryLogic.py`）本來就會**逐 size（per problem size）挑出各自最好的 solution**——production 的 heuristic selection 本來就是「每個 shape 各配一顆 kernel」，從來不是「用一顆 kernel 打天下」。

所以「用一個跨 size 的 aggregate champion 來做這個研究」**不符 Tensile 下游語意（per-size 選解）**，而 Ductile 用來產生它的 `max_s` 縮併方式本身，正是 §1 所有毛病的來源。

**誤解 vs 正解：**

> ❌ 誤解：「跨 size 的 aggregate champion 是 pilot 事後多加的一步，拿掉就好。」
>
> ✅ 正解：`Q=max_s` **就是 Ductile `soo=False` 的原生 fitness**（`ga.py:95, 256–273`；全樹無 Pareto／非支配排序）。真正的問題是**這個原生縮併方式不適合本研究問題** —— 它讓候選只憑「表現最好的那一個 size」被評分，於是最吵的 tiny 主導了 champion 選擇。per-shape 讓 fitness 變成 `(1,N)`、`max` 退化為恆等，**從根本繞開**該 reducer；Tensile `3_LibraryLogic` 本來也是 per-size 選解，所以這才是與上下游語意一致的做法。

### 2.3 guidance 機制本身是「一個 weight-vector 餵一個初始 population」

再看引導是怎麼進去的。Ductile 的 Gen0 引導介面（見 [QA-02](qa-02-ductile-gen0-and-nominal-valid-support-design.md)、[QA-06](qa-06-origami-formocast-ecosystem-design.md)）吃的是**每個 gene 一組 per-value 權重**，餵成**一個**初始 population：

- `ga.py:57`：`weights: list[dict[str, list[float]]]`——每個 gene 給一串 per-value 權重。
- `ga.py:58,145`：`weight_beta: float = 0.25`；權重轉機率是 `w = np.exp(-weight_beta * (w - w.min()))` 再正規化。

也就是說，**一次 GA 只吃一組 weight-vector、產一個 initial population**。在 joint 模式下，這一組 weight 必須「同時對三個 size 都合理」——它被迫變成一個**跨 size 的妥協解（compromise）**。這正是下一節要拆掉的東西。

---

## 3. 決定：每個 problem shape 各跑一個 GA（per-shape）

### 3.1 白話說改了什麼

把「一個 joint 多目標 GA 打三個 size」改成：**對 `ProblemSizes` 裡的每一個 shape（單一 size）各跑一個獨立的 GA。** 於是：

- **guidance 變 per-shape**：每個 shape 用它自己那組 weight-vector，不再被迫當跨 size 妥協解。
- **search 變 per-shape**：每個 shape 有自己的 GA 演化軌跡、自己的 early-stop。
- **evaluation 變 per-shape**：每個 shape 有自己的 champion，用自己的 per-size ratio 判定，**不再有 `max_s` 跨 size 聚合這一步**。

### 3.2 為什麼這樣一改，兩個病都消失

- **「妥協解」問題消失**：§2.3 那組被迫同時討好三個 size 的 weight-vector 不存在了。每個 shape 的引導只需對自己負責。
- **tiny 8×8 污染消失**：§1 的病根是「tiny 的量級主宰跨 size 的 `max`」。per-shape 之後根本沒有「跨 size」這回事——**8×8 變成一個自己獨立的實驗**，它的雜訊只污染它自己，永遠不會再拖累 large 或 medium 的判定。seed 14005 那種「大 size 快一倍卻被 tiny 拉低」的事，結構上不可能再發生。

### 3.3 誠實記一筆代價：三個 shape 是為了「多樣性」，不是為了 joint 協同

要老實說 per-shape 換到了什麼、放棄了什麼。

- **為什麼原本選這三個 shape？**（見 [QA-03 §0.1](qa-03-s11-factorization-and-metric-design.md)、S14 design §6.1）它們是刻意選**跨度極大**的小/中/大——tiny memory-bound、medium 穩定方陣、large compute-bound。選它們是為了在有限預算內涵蓋**不同效能 regime（size DIVERSITY）**，**不是**為了讓它們互相 co-optimize。
- **放棄了什麼？** joint GA 理論上能做**跨 size 的基因轉移（genetic transfer）**：在 size A 上被 crossover 發現的好搭配，可能對 size B 也有用。per-shape 把這條路切掉了。
- **為什麼放棄得起？** 正因為這三個 shape 是**刻意分歧（divergent）**的。對量級與 bound 特性差這麼多的 shape，一個 size 的好基因對另一個 size**是助力還是干擾，機率各半**——「co-optimization 帶來的 interference」和「帶來的 benefit」一樣可能。既然如此，為了保留一個「可能有、也可能有害」的跨 size 轉移，而付出 §1 那個「確定會壞掉」的 aggregation，划不來。

**誤解 vs 正解：**

> ❌ 誤解：「三個 size 一起演化，GA 能學到跨 size 通用的好 kernel。」
>
> ✅ 正解：這三個 shape 是為 diversity 選的、彼此分歧。跨 size 轉移在分歧 shape 上**同樣可能是干擾**。放棄它換來乾淨的 per-shape 判定，是有意識的取捨，不是疏忽。

---

## 4. S11 的建構效度連坐：per-shape guidance 也要重新導出

per-shape 決定會回頭牽動上游的 S11。因為——**S11 的 gene benefit 也是用 `max` 跨 size 壓的**，跟 §1 是**同一個缺陷家族**。

### 4.1 S11 的 max-reducer 同病

回顧 [QA-03 §0.3](qa-03-s11-factorization-and-metric-design.md)：S11 每筆 config 對 3 個 size 各算一個 `size_benefit`，再用**寫死不可改的 `max` reducer** 收成單一 benefit：

- `statistics.py:90`：`size_benefits = [1.0 - value for value in percentiles]`（per-size mid-ECDF benefit）
- `statistics.py:96`：`"benefit": max(size_benefits)`
- `statistics.py:61–62`：`if reducer != "max": raise StatisticsError("S11 actual size reducer must remain exactly max")`——reducer 被**鎖死**成 `"max"`。

而 gene 能不能引導，還有一道 **aggregate 的 2-of-3 方向一致性 gate**（[QA-03 §0.7](qa-03-s11-factorization-and-metric-design.md) 的 `size direction ≥2/3`；`statistics.py:1359` `size_direction`）。所以 S11 交出去的 per-value 偏好，本身就是**「跨 size 用 max 壓、再用 aggregate 方向 gate」**的產物——跟 §1 是同一種「把 per-size 訊號用 max 混成一鍋」的建構效度問題。

### 4.2 修法：不動 sealed code，從既有 per-size 產物重新導出 per-shape guidance

S11 已 sealed `LOCKED_READY`（見 [QA-00](qa-00-overview-reading-order-sources.md)），**不能改 locked code**。好消息是：per-size 的原料**早就存在**——S11 `score` 階段的產物 `s11-native-scores.json`（[QA-03 §0.10](qa-03-s11-factorization-and-metric-design.md)）裡，**每筆 occurrence 對每個 size 的分數都留著**（`size_benefits` 是 per-size 的，`max` 只是最後一步）。所以可以**不碰 locked code**，只**重用已封印的函式**，從既有 per-size artifact 重新導出 per-shape 的引導：

對每一個 shape `s` 各做一次：

1. **per-size benefit**：`benefit_s = 1 − mid-ECDF percentile`（就是 `s11-native-scores.json` 裡那一個 size 的 `size_benefits[s]`，跳過 `max`）。
2. **per-shape marginal + shrinkage**：沿用 `alpha=32` 的收縮平均（[QA-03 §0.4](qa-03-s11-factorization-and-metric-design.md)），得每個 gene value 的 per-shape `mu`。
3. **per-shape softmax**：`q_s = softmax(lambda × mu_s)`，得該 shape 的 per-value 偏好（已選 `λ_s=8`）。
4. **per-shape 混合（entropy-cap，見 §4.3a）**：對每個「合格」gene，`p1_s = (1−ρ)·p0 + ρ·q_s`；混合強度 `ρ` 由 entropy-cap 規則決定，不再是固定 `0.2p0+0.8q`（[QA-03 §0.8](qa-03-s11-factorization-and-metric-design.md) 的舊固定混合已被 §4.3a 的 per-gene cap 取代）。
5. **per-shape activation gate**：每個 shape 各有自己的 trust + `S_g≥0.05` sensitivity + 方向一致性啟動 gate；**不過就退回 `p0` fallback**（該 shape、該 gene 維持 baseline，不引導）。

因為只是**讀 sealed 的 per-size 分數 + 重跑 sealed 的 marginal/softmax/mix 函式**，這是 re-derivation，不是改 locked code。

### 4.3a `ENTROPY-CAP-20260810`：entropy floor 從「二元排除 gene」改成「per-gene 混合強度 cap」

> **來源標籤：**`[CODE AUDIT]`（gate 定義、sealed 函式）＋ design-discussion 2026-08-09（兩位 fresh independent reviewer 皆 `AGREE`、zero dissent）→ **user-approved 2026-08-10**。正式化見 [S14 design §10.3 與 §11](../s14-stage1-full-ga-outcome-design.md)。本節為 QA 白話，非 authority；以 S14 design／未來 lock 為準。

**先講 entropy floor 原本在做什麼、又踩到什麼。** re-derivation 有一道 **entropy floor gate**：它評估的是「引導後的 per-gene 混合機率 `p1` 有多集中」——用 normalized entropy `H_norm(p1)` 衡量。要求 `H_norm ≥ 0.80` 的用意是**保住 Gen0 的探索多樣性**：不要讓引導把 Gen0 initial population 幾乎全塞進少數幾個 value，否則 GA 一開跑就先失去 diversity。原本的做法是**二元的**——某個 gene 引導後 `H_norm < 0.80` 就**整個排除**該 gene（退回 `p0`、不引導）。

**問題（為什麼要改）：**這個二元 floor 剛好把**訊號最強**的 gene 砍掉。具體反例（`[MODEL-ONLY]`）：

| gene | shape | `S_g` | 為什麼被二元 floor 排除 |
| --- | --- | --- | --- |
| `DepthU` | medium | 0.14 | 高基數 gene，但只有 **2 個 trusted value** → 引導質量集中到那 2 值 → `H_norm < 0.80` → 被排除 |
| `PrefetchGlobalRead` | large | 0.19 | 同上：高基數但僅 2 trusted 值 → 集中 → 熵過低 → 被排除 |

白話講：**cardinality 高、但只有兩個值可信** 的 gene，只要一引導，機率就會擠向那兩個值、熵自然掉到 0.80 以下——而這種 gene 恰恰是 `S_g` 最高（訊號最強）的那幾個。二元 floor 於是**專門淘汰掉最該引導的 gene**，這是它的建構效度副作用。

**修法（`ENTROPY-CAP-20260810`）：把「排除」換成「降強度納入」。** 對**每一個**通過 trust + `S_g≥0.05` + 正向 direction 的 gene，以已選 `λ_s=8` 取 `q_g = q(λ=8)`，用 **per-gene 混合強度 cap**：

```text
p1_g = (1−ρ)·p0 + ρ·q_g(λ=8)
ρ_g  = max{ ρ ∈ [0, 0.80] : H_norm((1−ρ)·p0 + ρ·q_g) ≥ 0.80 }
```

- 對**本來就達標**的 gene（引導後仍 `H_norm ≥ 0.80`），`ρ = 0.80` → `p1 = 0.2·p0 + 0.8·q`，**與舊的固定混合完全相同**（現有 active gene 一個都不變）。
- 對**會踩到 floor** 的 gene（如 `DepthU`、`PrefetchGlobalRead`），不再整個丟掉，而是**把 ρ 降到剛好讓 `H_norm = 0.80`**——用較低強度**納入**它、同時仍守住 `H_norm ≥ 0.80` 的多樣性約束。所有候選保正機率。

**為什麼這不是 gate-shopping（挑門檻圖利）：**這是**通用規則、對所有合格 gene 一致套用**——每個 gene 都用同一條 `ρ_g` 公式，不是為了救某兩個特定 gene 才臨時放寬門檻。`H_norm ≥ 0.80` 這個多樣性底線**沒有被降低**；改的只是「碰到底線時是排除、還是降強度到剛好貼齊底線」。輸出每 gene 的 `p0/q/p1/ρ/entropy/TV/KL` + GA weights（`w(v) = −log(p1(v))/β`），跑前單元測試 post-transform 機率 == `p1`。

**誤解 vs 正解：**

> ❌ 誤解：「entropy floor 排除低熵 gene，是在濾掉沒用的雜訊 gene。」
>
> ✅ 正解：剛好相反。低熵是因為 gene **高基數但只有 2 個 trusted 值**、一引導就集中——這種 gene 往往 `S_g` 最高、訊號最強（`DepthU`、`PrefetchGlobalRead`）。二元 floor 把最強訊號砍掉；entropy-cap 改成**降強度納入**，兩全其美。

### 4.3b sparsity 調查：activated gene 極少，是模型性質、不是 per-shape 產物

> **來源標籤：**`[CODE AUDIT]`（26 個 trusted gene 的 `S_g`、sealed gate 定義）＋ `[BASELINE GPU]` pilot（activated 計數）。design-discussion 2026-08-09 → user-approved 2026-08-10（見 [S14 design §11](../s14-stage1-full-ga-outcome-design.md)）。

**觸發：**re-derivation 跑出來，per-shape 的 activated gene **極稀疏**——**medium = 1、large = 4、tiny = 0**。第一直覺是「per-shape 是不是把訊號切碎了」或「`S_g≥0.05` 門檻是不是太嚴」。稽核把根因釘死，兩個直覺都**不對**。

**根因 = sealed 的 `sensitivity S_g ≥ 0.05` gate。** 把 26 個 trusted gene 各自的 `S_g` 攤開，過 `S_g≥0.05` 門檻的數目：

| 計量口徑 | 過 `S_g≥0.05` 的 gene 數 | 平均 `S_g` |
| --- | --- | --- |
| aggregate max-reducer（**最濃**的口徑） | 3 | ~0.017–0.028 |
| medium | 2 | ~0.017–0.028 |
| large | 5 | ~0.017–0.028 |
| tiny | 0 | —（見下） |

**關鍵領悟：連最濃的 aggregate max-reducer 也只有 3 個 gene 過門檻。** aggregate max-reducer 是「把 per-size 訊號用 max 混到最濃」的口徑（見 §4.1），它都只活化 3 個 → **稀疏是模型本身的性質，不是 per-shape 切出來的 artifact**。而且**也不能靠放寬 `S_g` 來救**：其餘 ~22 個 trusted gene 的 `S_g` 只有 ~0.01–0.02，是**真的平**——Formocast 預測的 latency 幾乎不隨這些 gene 的值而變，引導它們 ≈ 均勻分布 ≈ baseline，等於白引導。

**`S_g` 到底是什麼（白話）：**`S_g` 量的是「某個 gene 的**各 value** 的『Formocast 預測 latency 之 population-rank 平均』彼此散得多開」。

- `S_g = 0` → 這個 gene 每個 value 的平均 rank 都一樣 → 換 value 不影響預測名次 → **引導它 ≈ baseline**（給不出方向）。
- `S_g` 大 → 不同 value 的預測名次差很多 → 這個 gene **有方向可引導**。
- `0.05` 是一個 **heuristic 的 model-space 底線**（≈ 至少 5 個 rank-percentile point 的散布）；它**不是**綁 GPU 量測噪音、**也不是** power calculation 算出來的樣本量門檻——純粹是「模型空間裡訊號要夠大才值得引導」的啟發式。

**tiny = 0 的特殊原因：**tiny `(8,8,1,128)` 過門檻 gene 數是 0，**不是**因為它訊號被 max 稀釋，而是因為**模型對 8×8 根本不出預測**——Formocast 對 8×8 回傳一個 sentinel latency `9999999.9`（哨兵值，代表 no prediction）。沒有有效預測，自然沒有任何 gene 的 `S_g` 能成形。這也呼應 §1 與 §5.3 把 tiny 定為 exploratory 的處置。

**entropy floor 與 sparsity 的關係（把 §4.3a 串起來）：**注意這裡有兩道**不同**的 gate，別混淆：

- `S_g≥0.05`（sensitivity）評估的是「這個 gene **有沒有**方向可引導」——決定 gene 過不過**活化**門檻。它造成了 sparsity（模型性質）。
- entropy floor（`H_norm≥0.80`）評估的是「引導後的機率**有多集中**」——保住 Gen0 探索多樣性。它的二元版**副作用**恰好又砍掉了通過 `S_g` 的最強 gene（`DepthU`、`PrefetchGlobalRead`），這正是 §4.3a 的 entropy-cap 要修的。

**誤解 vs 正解：**

> ❌ 誤解：「activated gene 這麼少，是 per-shape 把訊號切碎、或 `S_g` 門檻訂太高，放寬就好。」
>
> ✅ 正解：連最濃的 aggregate max-reducer 也只活化 3 個 → sparsity 是**模型本身**的性質，不是 per-shape 產物；放寬 `S_g` 也救不了，因為其餘 ~22 個 gene 是**真的平**（引導≈baseline）。tiny=0 是因為模型對 8×8 回 sentinel `9999999.9`、根本沒預測。

### 4.3 as-implemented S11 仍是一個獨立可報告的 artifact（附 caveat）

要講清楚界線：**as-implemented 的 max-reducer S11**（那個 sealed `LOCKED_READY` 的版本）**仍然是一個獨立、可報告的 artifact**。per-shape re-derivation **不取代**它、也不改寫它的封印；它以自己的 caveat（「gene benefit 跨 size 用 max 壓、aggregate 方向 gate，與 per-shape 判定不同」）留在紀錄裡。這是「as-implemented」與「re-derived-for-per-shape」兩份東西**並存**，不是後者把前者抹掉。

---

## 5. Claim framing：這個實驗**能**宣稱什麼、**不能**宣稱什麼

per-shape 重設計同時收斂了「我們到底在宣稱什麼」。以下框架來自兩輪 design-discussion（見 [S14 design §9](../s14-stage1-full-ga-outcome-design.md)）。

### 5.1 雙邊估計，不預設 null

估計效果時採**雙邊（two-sided）**：**不預設** Gen0 bias「沒有影響」的 null。理由很直接——**整個研究的前提就是「Gen0 的 bias *有可能* 影響結果」**（S14 的核心問句就是這個）。若一開始就假設 null，等於否定研究前提。所以「F 穩定劣於 G」也是一個**有意義的發現**（證明 bias 有影響、只是方向相反），不會被當成「沒差」。

### 5.2 per-dimension gate：哪些維度可以宣稱 improvement、哪些只能宣稱 non-regression

- **early-search 維度**（early-search quality-vs-evaluations + gen-10 checkpoint）：依 charter §8.2，這個維度**可以宣稱 improvement**。
- **final champion 維度**：**已由 charter §8.6a `CLAIM-SCOPE-S14-20260810`（owner-approved 2026-08-10）放行為 two-sided。**

> **2026-08-10 amendment（本小節原措辭「final champion 只能 NI、不宣稱 superiority、需 charter amendment 而我們不做」已被 owner 覆寫）：**owner 於 2026-08-10 核准 charter §8.6a `CLAIM-SCOPE-S14-20260810`——S14 的 final champion 維度改為 **two-sided**：以 per-shape 效應量 + CI/不確定區間 + 跨 seed directional consistency 報告 guided initialization 對**最終 tuned 品質（final champion real-GFLOPS）**的效應，**含改善、無變化、或退步**。**若資料支持**，study **得宣稱**「在受測 shape（medium/large）、單一 development cluster、5 對 paired seed 下，guided initialization 使**最終 tuned 品質提升**（directional/bounded evidence）」。原本「final 只能 NI」正是被否決的過度保守（見 §6 option F）。
>
> **強制誠實界線（不可違反，來自 §8.6a）：**必須標註 **power（5 seeds = bounded/modest，非統計顯著性證明）** 與 **scope（僅限受測 shape、單一 cluster，不一般化）**；**不得在 sealed 分析出爐前預設任何結論**（禁寫「對最終結果沒差」「預期 null」等 pre-conclusion）；不得誇大或偽造；每個數字標 evidence type、seed 為實驗單位、全報 seed/失敗/排除。若最終無可偵測差異或退步，如實報「在此 bounded 設定下未偵測到最終差異／觀察到退步」，**不**外推為「guidance 普遍無效」。

### 5.3 Horizon 與 gate

- **Horizon**：`n_gen=30` 為**最大上限**，且**保留 Ductile 原生 early-stop**（忠於未改動的 Ductile 行為，見 [S14 design §6.1](../s14-stage1-full-ga-outcome-design.md)）；另從**同一次 run** 抽出一個 **gen-10 checkpoint**（不另跑）。
- **per-shape directional-consistency gate**：每個 shape 看 **5 對 seed 中 ≥4/5** 同時滿足 `{Gen0, gen-10, AUC, final ratio ≥ e^(−η_s)}` 四個面向的方向一致。
- **confirmatory vs exploratory**：**medium 與 large 是 confirmatory（兩個都必須過）**；**tiny 是 exploratory**（因為它就是那個 noisy 8×8，見 §1）。
- **seeds / 資源**：**5 對 fresh paired seed**；**≤6 GPU**。

### 5.4 charter §8.6 的禁用措辭

以下 charter §8.6 forbidden wordings **仍絕不可出現**（§8.6a 未放行的部分）：對 MI300X workloads 一般化（generalization）、production／deployment ready、勝過 native `PredictionThreshold`（beat native）、跨架構（cross-arch）、**end-to-end tuning wall-clock speedup**（本實驗不量測 tuning 時間）、owner／team 應採用（adopt）。S14 是 **fixed-30-generation search-trajectory outcome**（見 [S14 design §1](../s14-stage1-full-ga-outcome-design.md)），不宣稱 tuning speedup。

> **2026-08-10 amendment：**charter §8.6a `CLAIM-SCOPE-S14-20260810`（owner-approved）就 **S14 範圍**放行了原 §8.6 「改善 GA convergence」與原 §8.2「final quality 僅能非退步」——S14 現得以 two-sided、bounded 方式報告（並在資料支持時宣稱）**受測 shape 上最終 tuned 品質提升**（見 §5.2）。**上列其餘 §8.6 禁詞不變**，仍不可出現。

### 5.5 反捏造紀律（anti-fabrication）

- 所有證據都要**貼標籤**：`[MODEL-ONLY]`（Formocast 模型空間，如 S11）／`[BASELINE GPU]`（baseline pilot 或 baseline 臂）／`[GUIDED GPU]`（guided 臂真實量測）／`[CODE AUDIT]`（讀 code 得到的事實）。本檔 §1 的 pilot 數字全是 `[BASELINE GPU]`；§2、§4 的 reducer/soo 事實是 `[CODE AUDIT]`。
- **seeds 是實驗單位（experimental units）**。
- **絕不**合成一個 guided 的 counterfactual——沒真的用 GUIDED 臂在 GPU 上跑出來的數字，不准編。
- **「not evaluated」≠「no effect」**：沒量到不等於沒影響。
- **modest power（5 seeds）要誠實揭露**：5 對 seed 的統計 power 有限，不能把少數 seed 包裝成 significance。

---

## 6. 考慮過但被否決的替代方案（逐一講為什麼丟掉）

發現 §1 缺陷後，per-shape 不是第一個、也不是唯一被想到的解法。下面把每一個「考慮過但沒採用」的方案，連同**否決理由**記下來——這才是誠實的推理紀錄。

| 考慮過的方案 | 它想解決什麼 | 為什麼被否決 |
| --- | --- | --- |
| **A. 保留 `max_s`（維持現狀）** | 承襲 S11 sealed `max`、最省事 | §1 已直接反證：`max_s` 被 tiny 8×8 的量級主宰，獎勵雜訊、把 seed 14005（大 size 快一倍）排最後。建構效度壞掉，不能留。 |
| **B. runtime-weighted aggregate Q**（用執行時間加權） | 讓「跑比較久、比較重要」的 size 權重高，壓低 tiny | 仍是**單一 aggregate 純量**——還是把 per-size 訊號混成一鍋，只是換個混法；tuning 權重本身又引入新的自由度與事後合理化風險。治標不治本。 |
| **C. geometric-mean aggregate Q**（幾何平均） | 幾何平均對極端值較不敏感，或許能壓 tiny | 一樣是**單一 aggregate**，一樣抹掉 per-size 語意；而且 tiny 的絕對 GFLOPS ≈2–4、雜訊 ±40%，幾何平均照樣會被它的相對抖動污染。沒解決根因（aggregation 本身）。 |
| **D. 單一 MOO GA + per-size champion 抽取**（保留 joint 演化，但最後每個 size 各抽一個 champion，不做 aggregate） | 保住跨 size 基因轉移，同時避開 aggregate | 這解掉了「aggregate champion」，但**沒解掉「guidance 被迫跨 size 妥協」**（§2.3）：仍是一組 weight-vector 餵一個 joint population，引導依舊被迫討好三個 size。per-shape 才連 guidance 一起 per-shape。 |
| **E. cross-size prior：average-marginals-then-softmax vs softmax-then-mix** | 若要保留 joint，該怎麼把三個 size 的 marginal 併成一個跨 size prior | 這整組討論**在選了 per-shape 之後就變 moot（無實益）**——per-shape 根本不需要跨 size prior，每個 shape 用自己的 marginal 就好。是被更上位的決定架空的分支。 |
| **F. 把所有維度都 cap 成 NI（non-inferiority）** | 保守、不會過度宣稱 | **錯在它預先判定了 null**（假設 bias 沒影響、只求「別更差」）。這**掏空了研究前提**（§5.1：前提就是 bias *可能* 有影響）。當初的折衷是 per-dimension gate（early-search 可 improvement、final champion cap 在 NI）——但 **NI-only 仍太保守**：**owner 於 2026-08-10 明確修訂 charter §8.6a `CLAIM-SCOPE-S14-20260810`，把 final champion 也放行為 two-sided**，資料支持時**得宣稱最終品質提升**（見 §5.2）。所以 F 這條「一律 NI」被**雙重否決**：既預判 null，方向上又比 owner 最終核准的 claim-scope 更緊。 |
| **G. 現在就換掉 tiny size** | tiny 8×8 是雜訊源，直接換掉一了百了 | 換 frozen size registry 是**改實驗定義**、需要正式 amendment，且會失去「涵蓋 memory-bound 極小 regime」的 diversity。per-shape 讓 8×8 **變成自己的孤立實驗**（tiny 標為 exploratory，§5.3），雜訊只污染自己——不必動 registry 就解決了污染。 |

**共同的教訓**：A、B、C、E 都是在「aggregation 這一步」裡打轉，而根因正是 aggregation 本身多餘（§2）；D 少 per-shape 化了 guidance；F 預判了 null；G 動到不必動的實驗定義。per-shape 一次把「aggregate 多餘」「guidance 被迫妥協」「tiny 污染」三件事一起拆掉，同時讓 claim framing（§5）自然落位。

---

## 7. 一句話總結

pilot 資料（`[BASELINE GPU]`）揭穿了 `Q=max_s` 這個 aggregate metric 的建構效度缺陷——它被最吵的 tiny 8×8 主宰、獎勵雜訊、把在大 size 快一倍的 seed 14005 champion 排到最後（`[CODE AUDIT]` 確認 `ga.py:95` 的 `np.max` 與 `statistics.py:96` 的 `max(size_benefits)` 是同一病根）。對照 code 才發現 `soo=False` 並非多目標／Pareto——它是 Ductile **內建的 `np.max` 跨 size reducer**（`ga.py:95, 256–273`；全樹無 Pareto／非支配排序），也就是 `Q=max_s` 本身就是原生 fitness，缺陷出在這個原生縮併方式不適合本研究問題；而 Tensile `3_LibraryLogic` 本就 per-size 選解，因此把 fitness 變成 per-shape 可讓 `max` 退化為恆等、從根本繞開該 reducer（`REDUCER-FACT-CORRECTION-20260812`）。於是改成 **per-shape**（每個 shape 一個 GA），guidance／search／evaluation 全部 per-shape，tiny 污染與妥協解一起消失；S11 也同步從既有 per-size 產物重新導出 per-shape guidance（不動 sealed code）；claim 全程雙邊估計、反捏造、誠實揭露 5-seed 的有限 power——且 **owner 於 2026-08-10 核准 charter §8.6a `CLAIM-SCOPE-S14-20260810`，把 final champion 維度也放行為 two-sided**，資料支持時得宣稱受測 shape 最終 tuned 品質提升（bounded/modest power、限受測 shape、不一般化、不預設結論）；S11 的 per-shape guidance 另以 `ENTROPY-CAP-20260810` 把 entropy floor 從「二元排除最強 gene」改為「per-gene 混合強度 cap」，並經 sparsity 稽核確認 activated gene 稀少是模型性質、非 per-shape 產物。
