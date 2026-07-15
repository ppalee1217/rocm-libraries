# Ductile GA 常見疑問澄清（實作深潛的補充 Q&A）

路徑說明：本檔在 `study_docs/geko-ductile/`。是 [ga-algorithm-implementation.md](ga-algorithm-implementation.md)（逐函式實作版）與 [ductile-deep-dive.md](ductile-deep-dive.md)（全景版）的**補充**。行號會隨 commit 漂移，引用時同時標章節符號名稱。

> **這份文件在補什麼？** 前兩份文件把「GA 一代做了什麼、每個 operator 怎麼運作」講得很細；但讀者真正卡住的，往往是一些**觀念性、定位性**的疑問——「survival 取前 k 個那 GA 不就是貪心嗎？」「mutation 保證能跳出 local minimum 嗎？」「跑 GA 前要先做一次 tuning 產生 seed 嗎？」「GA 和訓練一個預測模型差在哪？」這些點在既有文件裡多半沒有**直接、正面**回答（有的只在別處零星帶過）。本檔用 **Q&A** 形式一題一節澄清，每題都交叉引用對應的既有章節，方便對照。既有文件已經講清楚的機制細節，這裡**只引用、不重抄**。

---

## Q1. survival 取前 k 個，那 GA 不就是「貪心（greedy）」嗎？

**先講結論**：**survival 這一步「本身」的確像貪心（top-k），但把整個 GA 當一個系統看，它不是貪心。** 關鍵在 selection 的隨機性 + crossover + mutation。

先釐清一個容易看錯的地方：survival 用的是 **top-k（取前 `pop_size` 個）**，**不是 threshold（設一個分數門檻、過門檻就活）**。細節見 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §7〈`survival`〉的 `Fitness.__call__`（約 378–388 行）：把新舊族群合併 → 依 `F` 由大到小排序 → `pop[:size]` 取前 `size` 個。所以「活幾個」是固定的（= `pop_size`），跟分數絕對值無關，只跟**相對名次**有關。

為什麼「top-k 不是 threshold」很重要？因為 threshold 會有「全部都很爛就全滅」或「全部都很好就爆量」的問題；top-k 則保證**每代存活池大小穩定**，排序又是靠 §5 正規化過的可比較 `F`（見 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §7 末段說明），比較才公平。

那為什麼「整體不是貪心」？先定義貪心：**每步都只往當下看起來最好的方向走，絕不回頭、絕不試次好的**——很容易一路衝進第一個 **local optimum（局部最佳，指某個小範圍內最好、但不是全域最好的點）** 就卡死。GA 的四個 operator 裡，只有 survival 這一步像貪心 top-k；其餘三步都刻意「不那麼貪」：

| 步驟 | 行為 | 是否貪心 | 對照既有章節 |
| --- | --- | --- | --- |
| survival | 新舊合併取前 `pop_size` | 像 greedy top-k | §7 |
| selection | tournament 隨機抓 k 個再取最好 | **不貪**：次強個體有機會當父母（見 Q7） | §10 |
| crossover | 兩父代逐 gene 混出新子代 | **不貪**：產生「沒評估過」的新組合 | §11.1 |
| mutation | 小機率跳去試沒試過的值 | **不貪**：主動探索未知區 | §11.2 |

> 一句話：**survival 保證「已知的好解不會遺失」（這是貪心的優點，也就是 elitism）；但 selection/crossover/mutation 一直在往「還沒試過的地方」撒種子，所以 GA 整體不會像純貪心那樣一頭撞進第一個 local optimum。** 這正是 §4 心智模型「crossover=利用、mutation=探索」（[ga-algorithm-implementation.md](ga-algorithm-implementation.md) 第 40 行）的另一面：探索的存在，就是為了讓它不退化成貪心。

---

## Q2. mutation（突變）能「保證」GA 跳出 local minimum 嗎？

**不能保證。** 這點要誠實講清楚，因為既有文件的語氣容易讓人誤會 mutation 是「跳出局部最佳的解方」。

既有文件講到 mutation 時說它「避免過早收斂與陷入 local optimum」（[ductile-deep-dive.md](ductile-deep-dive.md) 1.3 節 mutation 列、[ga-algorithm-implementation.md](ga-algorithm-implementation.md) §11.2 末段），internal_docs 也提到「族群過小或世代數不夠，容易收斂在 local optimum」（[../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) 3.4 節限制第 2 點，約第 308 行）。這些都對，但都沒有把最關鍵的定位講白：

> **GA 是一種 metaheuristic（啟發式搜尋），它「沒有理論保證」一定能跳出 local minimum、也沒有保證找到全域最佳。** mutation / diversity 監控 / weights 加權 / 族群大小自適應，全部都只是**機率性地「降低卡住的機率」**，不是「保證不卡住」。

用白話拆解「為什麼只能機率性緩解」：

- **mutation 是機率事件**：預設突變率 `1/n_params`（[ga-algorithm-implementation.md](ga-algorithm-implementation.md) §11.2），平均每條子代只動大約一個 gene，而且動去哪也是隨機。它「有機會」把族群推離目前的山頭，但也「有機會」這代誰都沒突變到關鍵維度。
- **就算突變到了，也不一定被留下**：突變產生的探索性子代要先通過 `valid`（能編譯），再在下一輪 survival 裡贏過現有存活者才活得下來（§7）。一個「暫時比較差、但其實在通往更高山頭路上」的解，可能還沒爬上去就被淘汰。
- **緩解手段一覽**（都只是提高機率，不是保證）：mutation（§11.2）、diversity 過低就調整族群（§6.2 的 `low_diversity` decay）、`weights` 對關鍵維度加大探索（§6.4）、族群大小自適應（§6.2）。

那 GA 到底「保證」了什麼？只有一件事——**elitism / survival 的單調性**：透過 survival 取前 k（§7）+ `update` 維護歷代 `best`（§5），**目前找到的最好解永遠不會因為突變或運氣不好而遺失**。也就是「不會愈跑愈差」，但這推不出「一定會跳出 local minimum」。這條性質在 Q4 會再展開。

---

## Q3. 跑 GA 前，要先做一次 offline tuning 產生一個「初始解 seed」嗎？

**不用。** 這是最常見的誤會之一，根源是「seed」這個詞有**兩種完全不同的意思**被混在一起。

**意思一：`seed` = 亂數種子（RNG seed）。** 這是 Ductile 程式裡 `seed` 參數的真正意思。它只固定 Python `random`、`numpy`、以及 `SearchSpace` 內部 `SeedSequence` 的亂數狀態，**只影響「可重現性」**（同 seed + 同硬體環境，演化路徑才可能重來一次一樣）。細節見 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §13.1〈seed 怎麼設〉（約 703–715 行）與 §12 `defaults.yaml` 表（`seed` 預設 `0`，約 687 行）。**它不是「一個初始的 kernel 解」。**

**意思二：「以現有 YAML 為 seed」= 用現有 config 當「參數範圍的起點」。** internal_docs 5.1 節的實務建議「以現有 YAML 為 seed，再交給 Ductile 拓展」（[../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) 約第 426 行）講的是這個。這裡的「seed」是**英文「起點 / 種子」的日常用法**，指「拿既有 `ForkParameters` 當作 `--convert-config` 擴張的基礎值域」，**不是「先跑一次 GA 或 grid 得到一個解」**。

那 GA 真正的初始族群從哪來？——**隨機採樣，完全不需要前置 tuning**。見 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §3.3〈合法性採樣 `sample`〉（約 154–180 行）：它就是「一直亂骰整數組合、把能編譯的留下來，直到湊滿一整批合法初始族群」。第一代族群是骰出來的，不是 tune 出來的。

> 一句話：**Ductile 的 `seed` 是亂數種子（管重現性），不是「初始解」；GA 的初始族群是隨機採樣而來，開跑不需要任何前置 offline tuning。** 讀到 internal_docs「以現有 YAML 為 seed」時，請理解成「用現有 config 當參數值域的起點」，而不是「先產生一個解」。

---

## Q4. GA 有「保證接近全域最佳」（例如 ≥ grid best 的 90%）的理論證明嗎？

**沒有理論證明。** 這點必須誠實，否則會把「經驗數字」誤當成「數學保證」。

既有文件出現過的那些漂亮數字——OOB/grid-based library 已達 **約 0.9–0.98×** 理論最佳、對 hot shape 再榨 **3–10% uplift**、平均 uplift **約 5–10%**（見 [../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) 3.4 節優點、4.2 節比較表）——全部都是 **empirical（經驗、實測統計）數字**，是「在 MI300/MI350 這些機器、這些 workload 上跑出來的平均結果」，**不是「GA 一定能達到 grid best 90%」的證明**。metaheuristic 本質上就沒有「逼近全域最佳」的理論保證。

GA 唯一**有保證性質**的是前面 Q2 提過的**單調性**：

- **`best` 單調不減**：`update` 只在出現更強候選時才更新各 shape 的冠軍（[ga-algorithm-implementation.md](ga-algorithm-implementation.md) §5，`scores.max(1) > best` 才更新，約 270–273 行），所以歷代最佳隨世代**單調不會變差**。
- **不劣於已評估過的候選**：survival 取前 k（§7）保證最終輸出「至少不比演化過程中評估過的任何解差」。

但請注意這條保證的**邊界**：它只說「不比**你已經試過**的解差」，**推不出「接近全域最佳」**——因為全域最佳可能落在 GA 根本沒採樣到的角落。

那實務上「品質」靠什麼兜底？兩件事：

1. **更大的搜尋空間常能超越 grid**：`--convert-config` 讓 GA 去 grid 因太大而不敢畫格子的值域（見 [ductile-deep-dive.md](ductile-deep-dive.md) 三、`--convert-config` 節），headroom 常落在 grid 沒明列的非典型組合上（詳見 Q9）。
2. **事後實測驗證**：GA 產出的少數冠軍會被拿去實測比較、確認確實不劣於現有 pool（詳見 Q10、Q11）。

> 一句話：**GA 保證的是「單調不變差、不劣於已評估過的解」（elitism + survival top-k），不是「接近全域最佳」。文件裡的 0.9–0.98×、3–10% 都是經驗值，不是證明。** 品質靠「更大空間 + 事後實測」在實務上兜底。

---

## Q5. §5 的 `np.max` 正規化，可以給我一個具體數字例子嗎？

可以。這題純粹補一個 **worked example（數字走查）**——機制本身（除以各 shape 冠軍、再用 `reduce_fn` 聚合）在 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §5〈`update`〉（約 257–294 行）已講清楚，這裡不重講原理，只帶數字讓你「看到」`np.max` 與 `np.mean` 選出的贏家不同。

**情境**：一個 config 同時 tune 2 個 shape：

- Shape A：大矩陣，當代冠軍 **1000 GFLOPS**。
- Shape B：小矩陣，當代冠軍 **200 GFLOPS**。

（`best.F = [1000, 200]`，這是 §5 步驟 3 維護的「各 shape 冠軍」。）

**兩個候選**（`scores` 的兩欄，形狀 `[n_sizes=2, ...]`）：

| 候選 | 在 A 的 GFLOPS | 在 B 的 GFLOPS | 白話 |
| --- | --- | --- | --- |
| X | 1000 | 50 | A 的專家（A 跑滿，B 很爛） |
| Y | 600 | 180 | 通才（兩邊都中上） |

**第一步：對各自 shape 的冠軍正規化**（`scores / best.F[..., None]`，§5 步驟 4）：

| 候選 | A 相對比值 | B 相對比值 |
| --- | --- | --- |
| X | 1000/1000 = **1.0** | 50/200 = **0.25** |
| Y | 600/1000 = **0.6** | 180/200 = **0.9** |

**第二步：沿 shape 軸聚合成單一 `F`**：

- **`np.max`（多目標，`soo=False`，預設）**：取每個候選「最擅長那個 shape」的比值。
  - X 的 `F = max(1.0, 0.25) = 1.0` ✅ 贏
  - Y 的 `F = max(0.6, 0.9) = 0.9`
  - → **X 勝**。意義：保住了「A 的專家」，族群不會因為 A、B 混在一起就把 A 的高手淘汰掉。
- **`np.mean`（單目標，`soo=True`）**：取平均，偏好通才。
  - X 的 `F = mean(1.0, 0.25) = 0.625`
  - Y 的 `F = mean(0.6, 0.9) = 0.75` ✅ 贏
  - → **Y 勝**。意義：偏好「兩邊都不錯」的折衷解。

**最關鍵、最容易誤會的一點**：X 用 `np.max` 拿到 `F=1.0` **不是因為它的 GFLOPS 數值大（1000）**，而是因為它在 A 上「相對 A 的冠軍」達到了 1.0 這個**比值**。假設今天 X 在 A 上只有 900（比值 0.9），它的 `F` 就會變 0.9，反而輸給 Y。**`np.max` 得高分 = 它在最擅長那個 shape 上「逼近該 shape 冠軍」的程度高，比的是相對比值，不是絕對 GFLOPS。** 這也正是 §5 末段「為什麼要除以冠軍再聚合」（約 294 行）想避免的事——直接比原始 GFLOPS 會被大矩陣量級主宰。

---

## Q6. 不是在「同一個 problem size」裡搜嗎？為什麼會有大小矩陣衝高、需要正規化？

這題澄清一個常見的直覺衝突：「既然是為某個 GEMM shape 找最快 kernel，那不就是在一個固定 problem size 裡比嗎？哪來的大矩陣小矩陣一起衝高？」

**答案：一個 config 可以同時 tune 多個 problem size；正規化就是為這種「多 size 混一個 config」設計的。** 當一個 config 只含**單一** shape 時，正規化其實**退化成沒作用**（沒有主宰問題）。

機制對照（已在既有文件講清楚，這裡只點出「單 vs 多 size」的差別）：

- 每個候選 kernel 會在 config 列出的**所有** problem size 上「各 benchmark 一次」。所以 fitness 不是一個數字，而是一排——`scores` 形狀是 `[n_sizes, n_ind]`（列 = problem size、欄 = 候選），見 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §8.2〈`_evaluate`〉（約 449–489 行）與 §5 開頭。
- **單 size 時**：`scores` 只有一列，`n_sizes = 1`（程式會 `scores[None, ...]` 補成 2D，見 §4 ① evaluate 說明約 224 行）。這時 `scores / best.F` 就是「除以那唯一一個 shape 的冠軍」，`np.max` / `np.mean` 沿只有一個元素的軸聚合 = 原值。**正規化退化、沒有大小矩陣主宰問題。**
- **多 size 時**：不同 shape 的 GFLOPS 量級天生差很多（大矩陣天生跑得快，見 §5 末段約 294 行）。若直接比原始 GFLOPS，大 shape 會主宰排序、小 shape 被忽略。所以要先各自對「該 shape 的冠軍」正規化成比值再聚合——**正規化在這裡才真正起作用**（數字例子見 Q5）。

> 一句話：**正規化不是「同一個 size 裡的操作」，而是「把多個 size 的分數放到可比較的尺度上」的操作。單 shape 時它自動退化；只有一個 config 混了多個 size，正規化才有意義。** 至於「多 size 混 tune 為什麼可能產生平庸解」，見 Q12。

---

## Q7. selection 的隨機性從哪來？為什麼預設用 tournament(k=2)？

既有文件（[ga-algorithm-implementation.md](ga-algorithm-implementation.md) §10）已列出 tournament 的機制與各策略比較表，但沒白話點出「隨機性到底在哪一步」，也沒解釋「為什麼**預設**挑 tournament(k=2)」。這裡補這兩點。

### 7.1 隨機性在「抓哪 k 個」

tournament（錦標賽）的規則是：**隨機抓 `k` 個個體 → 取其中最好的當一個父母 → 重複到選滿**（見 §10 策略表 `tournament` 列，約 600 行）。隨機性**不在「取最好」那一步**（那步是確定性的：k 個裡誰 `F` 最高就選誰），而在**「隨機抓哪 k 個」**。

走查一個例子（族群依 `F` 排名 1（最強）到 8）：

- 假設某場 k=2 隨機抓到「排名 3」和「排名 6」→ 選出排名 3。
- 下一場隨機抓到「排名 2」和「排名 5」→ 選出排名 2。
- 又一場抓到「排名 4」和「排名 7」→ 選出排名 4。

看出來了嗎？**最強的排名 1 並不是每場都在場上**，所以次強、第三強的個體都有機會被選為父母。這就避免了「最強基因洗版、族群瞬間全變成它的後代」的早熟（premature convergence）。對照 §4 心智模型：selection 決定「誰有資格當父母」，適度的隨機性維持了族群多樣性。

（另註：實際還有 5% elitism 直接保送最強者當父母，見 §10 的 `Selection.__call__`，約 583–589 行；tournament 是處理「其餘 95%」的策略。）

### 7.2 選擇壓力光譜：預設為何是 tournament(k=2)

「**選擇壓力（selection pressure）**」指「愈強的個體，被選為父母的優勢有多大」。壓力太小 → 收斂慢（跟亂選差不多）；壓力太大 → 早熟（強者通吃、多樣性瞬間崩掉）。§10 各策略可以排成一條**由小到大**的壓力光譜：

| 策略 | 選擇壓力 | 白話 |
| --- | --- | --- |
| `random` | 最小（≈0） | 純亂選，沒壓力（對照用） |
| `rank` | 小～中 | 只看名次不看分數大小 |
| `tournament(k)` | 中（隨 k 增大） | 抓 k 個 PK，k 越大壓力越大 |
| `beta` | 中～大 | 偏好排名前段 |
| `roulette_wheel` | 大 | 依分數佔比抽，強者機率高 |
| `truncation` | 最大 | 硬性只讓前段當父母 |

**預設選 tournament(k=2) 的關鍵理由：對 benchmark 噪音穩健。** 這是 Ductile 的 fitness 來自**真實 GPU 實測**（有噪音：DVFS、其他負載、量測抖動，見 [../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) 3.4 節限制第 2 點約 309 行）這個特性決定的：

- tournament **只比「相對勝負」**（A 和 B 誰快），**不看絕對分數**。就算兩者 GFLOPS 都被噪音抬高或壓低，只要相對關係不變，選擇結果就穩。
- 反觀 `roulette_wheel` / `truncation` **直接吃絕對分數**：一個被噪音偶然量到超高分的「假超級個體」，在 roulette 裡會拿到不成比例的高選中機率、在 truncation 裡會硬擠進父母池，把族群往錯的方向帶偏。
- k=2 是「有選擇壓力、但不過大」的甜蜜點：比純隨機有方向性，又不像大 k 或 truncation 那樣壓力過猛導致早熟。

> 一句話：**selection 的隨機性在「隨機抓哪 k 個」，讓次強個體也有機會當父母、避免早熟；預設 tournament(k=2) 是因為它只看相對勝負、對實測噪音穩健，而 roulette/truncation 會被噪音和假超級個體帶偏。**

---

## Q8. GA 和「直接訓練一個 NN 模型 / surrogate」差在哪？該用哪個？

這是既有文件完全沒談的新主題。先給一句話直覺，再展開。

> **GA 是「直接把一組解搜出來」，不是「訓練一個可重用的預測函數」。** 表面上兩者都「迭代 + 有分數（GFLOPS / loss）」，很像 training，但本質不同。

### 8.1 本質差異：搜一組解 vs 學一個函數

- **GA（Ductile 走的路）**：輸出是**一組具體的 kernel 參數**（每個 shape 一個冠軍）。它**沒有權重、不會泛化**——換一個沒 tune 過的 shape，前一個 shape 的 GA 結果幫不上忙，得**重跑一次 GA**。它像「針對這幾個 shape，親手把最快設定挖出來」。
- **Model-based / surrogate（例如 Formocast）**：訓練一個**預測函數**，輸入 (shape, config) → 輸出「預估效能」。訓練好之後可以**對沒見過的 shape 直接預測**、快速給答案，不必每個 shape 都真的上 GPU 搜。生態系裡 **Formocast 就是走這條 surrogate / prediction 路線**（硬體模擬 + 模型預測），見 [../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) 1.1 節（約第 35 行）對 Origami/Formocast 的描述。

所以這**不是二選一，而是互補**：GA 負責「少數 hot shape 榨到極致」，model 負責「對海量 shape 快速給答案」。

### 8.2 為什麼 hot-shape 極致優化選 GA

- **(a) 不用準備 dataset**：要訓練「準」的預測器，得先蒐集大量 `(config, 實測 GFLOPS)` 樣本——而**蒐集實測正是整條鏈路裡最貴的一步**（每筆都要編譯 + 上 GPU 跑）。GA 省掉「先建大 dataset」這關，直接開搜。
- **(b) 直接優化真目標、無 surrogate 誤差**：GA 的 fitness 就是**真實實測 GFLOPS**（見 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §8.2），不像預測模型會有「模型預測 ≠ 真實效能」的誤差。
- **(c) 天生適合離散、不可微、有 valid 約束的空間**：kernel 參數是離散整數 gene、組合合法性要靠 `_initKernel` 才知道（§8.1 的 `valid` 回呼）、效能對參數不可微。GA 本來就在離散空間上操作、用 `valid` 過濾非法解，天生契合；梯度式訓練反而要處理不可微與約束的麻煩。
- **(d) 換架構不用重訓**：新 GPU 出來，GA 直接在新機器上實測重搜即可；預測模型往往得為新架構重新蒐資料、重訓。

### 8.3 GA 的代價，以及分場景結論

- **GA 的代價：sample 效率低**。每一個候選都要**真的編譯 + 上 GPU 跑**（§8.2 的 `_evaluate`），成本高，所以只划算用在**少數 hot shape**。
- **分場景結論**：

| 你的情境 | 建議 |
| --- | --- |
| 少數 shape、要榨極致、評估很貴、空間離散有約束 | **GA（Ductile）** |
| 要對成千上萬 shape 快速給答案、且能攤提訓練成本 | **學 model（Formocast 那種 surrogate）** |

> 一句話：**GA 是「直接搜一組解、直接優化真目標、天生吃離散約束、換架構不用重訓」，代價是 sample 效率低所以只用在少數 hot shape；要對海量 shape 快速回答就交給 Formocast 那種預測模型。兩者互補，不是二選一。**

---

## Q9. 為什麼 GA 會比 grid 好？grid 不是「窮舉、保證找到最佳」嗎？

這題補一個**關鍵 nuance**：既有文件（[ductile-deep-dive.md](ductile-deep-dive.md) 白話總覽、[../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) 4.1 節）講了「GA 搜更大空間」，但沒把「**GA 什麼時候贏、什麼時候絕對贏不了 grid**」講到底。

> **在「同一個小 grid」上，grid 是窮舉、保證找到該 grid 內的最佳解，GA 最多打平、不可能贏。** GA 只在「空間大到 grid 根本無法窮舉」時才贏。

拆開講：

- **grid 在它自己的格子裡是無敵的**：grid 把 `ForkParameters` 笛卡兒積**每一點都踩過**（見 [../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) 2.2 節），所以「這個 grid 內的最佳解」它一定找得到。GA 是**抽樣式**搜尋，只評估其中一小撮，在同一個小 grid 上，GA 最好的情況也只是「剛好也踩到那個最佳點」——**打平，贏不了**。
- **GA 贏在「grid 不敢畫格子的地方」**：當你想同時調很多維度（GRVW、NonTemporal、StaggerU、WGM/XCC…），笛卡兒積會**指數爆炸**，grid 只好把值域畫得很粗、很窄（否則跑不完）。而 GA 靠 `--convert-config` 把值域大幅擴張（例如 `GlobalReadVectorWidthA/B` 從 `[2,8]` → `[-1,-2,2,3,4,6,8]`，見 [ductile-deep-dive.md](ductile-deep-dive.md) 三節），再靠 crossover/mutation 組出 grid **沒明列**的非典型組合。那 **2–10% 的 headroom，常常就落在這些 grid 因為太大而略過的非典型點上**。

用一個比喻收束（延伸 [ductile-deep-dive.md](ductile-deep-dive.md) 的棋盤比喻）：**grid 是在一小塊畫滿格子的棋盤上一格一格踩，格子內它最強；GA 是在一整片大很多、只畫了稀疏刻度的地圖上飛，去 grid 因為太大而沒鋪格子的區域找高地。** 如果地圖就只有那一小塊，別飛了，直接用 grid 踩完最穩。

> 一句話：**同一個能窮舉的小 grid 上，用 grid（GA 贏不了窮舉）；空間大到無法窮舉、或懷疑最佳解不在現有 grid 內，才用 GA。** 這也呼應 internal_docs 4.2 的分工建議（約 364–365 行）。

---

## Q10. runtime 不驗證，那 GA 找到的解到底有沒有被驗證過？

**有，而且驗證早就在 offline tuning 階段做完了。** 這題澄清「兩階段」的時間點，破解「runtime 不驗證 = 沒驗證過」的誤會。

**階段一：offline tuning（跑 GA 時）——這裡才做驗證。**

- GA 追速度時可能把數值驗證放寬（跑更快），所以跑完後 backend 會對 `best` **再 evaluate 一次做數值驗證**（把 `NumElementsToValidate` 調回設定值），只保留「在所有 size 都通過（算得對）」的解，全滅就報錯。見 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §8.4〈post-optimization verification〉（約 515–536 行）。
- 除了數值正確性，還會用 **Dense Search / bench-driven swap** 做效能比較，確認 GA 的解確實不劣於現有 pool（見 [../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) 4.3、5.4 節；細節與成本見 Q11）。
- **只有通過的解才會被寫進 library**（`3_LibraryLogic` YAML）。

**階段二：runtime（每次 `hipblasLtMatmul` 呼叫）——只查表，不再驗證。**

- runtime 只是「拿 shape/dtype/transpose 當 key，在條件樹裡查出一個**已驗證過**的 solution index」，然後啟動對應 kernel。整個過程見 [../hipblaslt/solution-selection.md](../hipblaslt/solution-selection.md)（條件樹 → 尺寸比對層 → 葉子）。它**不做任何驗證或搜尋**，因為驗證早在 tuning 完成時就前置做完、烤進 library 了。

**所以「runtime 不驗證」不代表「沒被驗證過」**——驗證被前置到 tuning 階段了。

順帶講清楚**保證的邊界**（呼應 Q4）：

- **保證的**：這個解「不劣於驗證當下的 solution pool」+「數值正確」。
- **不保證的**：全域最佳（Q4）。而且 runtime 的實際效能會因**輸入資料、GPU 溫度/DVFS、其他負載**而波動——但那是**噪音問題、不是正確性問題**：kernel 選得對、算得對，只是每次跑的 GFLOPS 會有抖動。

> 一句話：**驗證發生在 offline tuning（§8.4 數值驗證 + Dense Search/swap 效能比較），只有通過的解才進 library；runtime 只查表用已驗證的解、不再驗證。runtime 效能波動是噪音，不是沒驗證。**

---

## Q11. 「驗證 GA 解」會不會把 GA 省下的時間又吐回去？Dense Search / bench-driven swap 算 grid search 嗎？

**不會吐回去。** 這題補一個既有文件（[../internal_docs/hipblaslt-tensilelite-reference.md](../internal_docs/hipblaslt-tensilelite-reference.md) B.3 節約 315–323 行）描述了 Dense Search 與 bench-driven swap、但沒點破的**關鍵差異**：**它們不產生也不編譯新 kernel。**

### 11.1 三種東西的成本天差地別

| 動作 | 做什麼 | 貴在哪 | 成本量級 |
| --- | --- | --- | --- |
| **Grid-level search** | 枚舉 `ForkParameters` 笛卡兒積，**每個組合 codegen + 編譯出新 kernel 再測** | 指數爆炸 × 每個都要編譯 | O(指數個編譯) |
| **Dense Search**（GEKO `--search` / `hipblaslt-bench --algo_method all`） | 只跑**已存在、已編譯好**的 solution pool 測速，**不產生新 kernel** | 只有 benchmark，沒有 codegen | O(pool 大小個 benchmark) |
| **bench-driven swap** | 在既有 pool 裡，把 grid 表指向的贏家換掉，**不重新產生 kernel** | 只改 YAML grid 表的 solution index | 極低 |

看出來了嗎？Grid-level search 貴在「**產生 + 編譯**新 kernel」；Dense Search / bench-driven swap **完全不碰 codegen**，只在既有 pool 上測速或換指標。這正是 internal_docs 分層策略（[../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) 5.3 節）主張「先做便宜的 Dense Search / swap，真的需要新 kernel 才上 grid/GA」的原因。

### 11.2 為什麼「驗證 GA 解」很便宜

關鍵在於：**GA 已經把最貴的「大空間探索」做完了**（每個候選都真編譯 + 跑 GPU，見 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §8.2）。驗證階段（Q10）**不重跑搜尋、不重編譯整個空間**，只是拿 GA 找到的**極少數冠軍**（每 shape 幾個）去實測比較：

- 驗證的數量級是 **O(幾個 benchmark)**，不是 O(指數個編譯)。
- 它比較像 Dense Search（在已編譯好的少數解上測速），不是再跑一次 grid。

所以「花時間驗證 GA 解」**不會把 GA 省下的搜尋時間吐回去**——省的是「探索大空間」的成本（已經花掉且值得），驗證只是廉價的收尾實測。

> 一句話：**Dense Search / bench-driven swap 不產生也不編譯新 kernel，成本遠低於 grid-level search；驗證 GA 解只是拿極少數冠軍做廉價實測（O(幾個 benchmark)），不重跑搜尋、不重編譯，所以不會把 GA 省下的時間吐回去。** 搭配「由便宜到貴」的分層策略（Dense Search → bench-driven swap → grid/GA tuning）理解最清楚。

---

## Q12. 多 shape 混 tune 的「平庸解」到底怎麼發生？輸出不是「每個 shape 各一冠軍」嗎？

這題補一個**看似矛盾、需要調和**的 nuance。既有文件有兩句話乍看衝突：

- internal_docs 說多 shape 混 tune 會傾向「對多數 shape 都不差的折衷解」，建議差異大的 shape 拆獨立 config（[../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) 3.3、3.4 節，約 285–288、310–312 行）。
- 但 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §5 明明說多目標下輸出是「**每個 shape 各一個冠軍**」（`best` 是長度 = n_sizes 的 Population，約 285–286 行），不是一個通吃 kernel。

**那平庸解到底哪來的？** 調和的關鍵是：**平庸不是出在「輸出」，而是出在「演化過程共用一個族群」。**

拆解：輸出的確是 per-shape 冠軍（§5），沒有「一個 kernel 通吃所有 shape」這回事。但問題在於**這些冠軍是從「同一個共用族群」演化出來的**，共用族群帶來三個副作用：

1. **selection / survival 用的是「聚合後的單一 `F`」**：每個候選的去留，看的是它跨所有 shape 聚合出的一個 `F`（§5 的 `reduce_fn`），不是「它在某個 shape 上多強」單獨判斷。一個「只專精被冷落 shape」的候選，聚合分數可能不夠高而被淘汰。
2. **crossover 會混不同 shape 專家的基因**：兩個分別擅長不同 shape 的父母配對，子代可能兩邊都不專精（§11.1 逐 gene 混合）。
3. **搜尋預算被瓜分**：固定的族群大小與世代數要同時服務多個 shape，分到「某個被犧牲 shape」的探索量就變少。

結果：**那個「被犧牲 shape 的冠軍」，品質可能比你單獨 tune 它時差**——因為演化過程沒把足夠的族群/預算專注在它身上。

**`np.max` 聚合（Q5）是緩解、不是根治**：`np.max`（保專精者）確實比 `np.mean` 更能保住「至少專精某 shape」的候選，維持族群對各 shape 的覆蓋（§5 步驟 4、§6.3）。但它只是**降低**被犧牲的程度，沒辦法讓「共用一個族群」變成「每個 shape 各有獨立完整的族群與預算」。

**實務處方**（呼應 internal_docs 建議）：

- **相似 shape 可同一 config**：tuning driver 會把相近 shape cluster 在一起，共用族群的副作用小。
- **差異大才拆獨立 config**：`MAX_NUM_KERNELS_PER_CONFIG:1` + `--cluster 0`，讓 GA 專注單一 shape，把整個族群與預算都給它（見 [../internal_docs/ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) 3.3 節，約 287 行）。

> 一句話：**輸出是 per-shape 冠軍沒錯，但這些冠軍是從「共用一個族群」演化來的——聚合成單一 `F` 做去留、crossover 混不同專家基因、預算被瓜分，導致被犧牲 shape 的冠軍品質變差。`np.max` 是緩解、非根治；差異大的 shape 該拆獨立 config。**

---

## Q13. 為什麼所有染色體能「逐位置比對」？每條染色體的 gene 數不會不一樣嗎？

**先講結論**：因為每條染色體都是「**固定長度、每個位置對應一個特定 gene**」的向量，全族群、全程都一樣長、位置一一對齊——這正是 `diversity()` 用 hamming「逐位置比對」能成立的**前提**。gene 數在整個 tuning 過程**不會變**，更不會「這條染色體多一個 gene、那條少一個」。

`diversity()` 的機制（`pdist` + hamming）已在 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §2.3〈深入 `diversity()`〉講清楚；這題補的是它**背後的可比性前提**——為什麼「逐位置比對」在 Ductile 一定成立。拆成四點：

1. **gene 集合開跑就固定**（[ga-algorithm-implementation.md](ga-algorithm-implementation.md) §3.1、§3.5）：這次 tuning 有哪些 gene、順序如何，在建 `SearchSpace` 時就由 config 的 `forkParams`（＋多選項 `paramGroups` 產生的 `group_i`）**定死了**。每條染色體**不是「長度可變的清單」**，而是「**固定長度向量，第 i 格永遠對應同一個 gene**」。
2. **`X` 被 `sorted`，確保順序對齊**（[ga-algorithm-implementation.md](ga-algorithm-implementation.md) §2.1，`Individual.X = dict(sorted(...))`，約 91 行）：所有染色體的 gene **順序一致**，不會發生「A 的第 0 格是 `DepthU`、B 的第 0 格卻是 `GRVW`」這種**欄位錯位**。
3. **沒有任何 operator 會增刪 gene，只改值**：
   - `sample`：對**每個** gene 各骰一個 index（§3.3）。
   - `crossover`（`Uniform.op`）：用 `pa.names` **逐 gene 對齊互換**（§11.1）——兩父代用的是同一組 gene 名。
   - `mutation`：只把某格的 index 換成**同 gene 的其他候選**（§11.2），格子數不變。
   - 所以子代跟父代一樣，永遠是 `n_params` 個 gene，一個不多一個不少。
4. **`load()` 續跑時檢查 `space_map` 一致**（[ga-algorithm-implementation.md](ga-algorithm-implementation.md) §13.3）：若 checkpoint 的 gene 集合跟當前設定不符會直接報錯，避免用「gene 集合不同」的族群硬接。

所以 `self.ary` 攤出來的矩陣**每一列長度都 = `n_params`，完全相同**——才能對第 `i` 欄逐一問「A 和 B 這格一不一樣」去算 hamming。若染色體長度會變、或欄位會錯位，`pdist` 的逐位置比對根本無從談起。

> 一句話：**Ductile 的染色體是「固定長度、欄位對齊」的整數向量（gene 集合開跑固定、`X` 有排序、operator 只改值不增刪 gene、resume 還會檢查一致），所以每列長度都相同，hamming 的逐位置比對才成立。** 「gene 的身份 vs gene 的值」這層區分見 Q15，為何用 hamming 見 Q14。

---

## Q14. `diversity()` 為什麼用 hamming、不用歐氏距離（Euclidean）？

**先講結論**：因為 gene 存的是「**類別的編號（第幾個候選）**」而不是「有大小意義的數值」；hamming 只問「一不一樣」，**語意正確**又讓每個 gene **等權**，而歐氏距離會被「index 範圍大的 gene」主宰、還會誤把「編號」當成有距離的數。

`diversity()` 逐行與 hamming 的定義見 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §2.3；這裡補的是「**為什麼選它**」。兩個理由，第二個更關鍵：

**理由一：避免各維度比重不均。**

- 若改用歐氏：每個 gene 對距離的貢獻 = `(index 差)²`。一個候選數多的 gene（例如某參數有 8 個候選、index `0~7`）差距可以到 7，候選數少的（index `0~2`）最多差 2 → **大範圍 gene 的差異會主宰整條距離，小範圍 gene 幾乎被忽略**，比重嚴重失真。
- hamming：每個 gene 只貢獻 0（相同）或 1（不同），**每個 gene 等權**（各占 `1/n_params`），對「候選數 / index 範圍差異」完全免疫。

**理由二（更關鍵）：gene 是 categorical（類別）的 index，不是 ordinal（有序、有大小）的數值。**

- gene 存的是「**第幾個候選**」的 index，不是有大小意義的量。以 `DepthU` 候選清單 `[16, 32, 64, 128]` 為例：index `0→16`、`1→32`、`2→64`、`3→128`。index「差 3」對應的真實值差是 `16→128`，**既非線性、也沒有「距離」的物理意義**。硬算歐氏等於假設「index 2 跟 index 3 比 index 2 跟 index 5 更接近」——這對**類別型**參數根本不成立。
- 對**複合 gene**（`group_i`，[ga-algorithm-implementation.md](ga-algorithm-implementation.md) §3.4）更是如此：index 選「**第幾套組合**」，純粹是類別編號，套與套之間根本沒有「差幾號」可言。
- 所以語意正確的相似度是「**一樣 / 不一樣**」（hamming），不是「差幾號」（歐氏）。

（旁註：hamming 天生把 diversity 落在 `0~1` 的直覺區間，也方便 §6 用 `div_thr`（預設 `0.5`）之類的門檻判早熟。）

> 一句話：**gene 是「第幾個候選」的類別編號、不是有大小的數值，且各 gene 候選數不同；用歐氏會被大範圍 gene 主宰、又誤把編號當距離。hamming 只看「相不相等」、每個 gene 等權，語意正確又落在 0~1，才是對的相似度。** 這也解釋了 Q13 的「逐位置比對」為何只問「同不同」。

---

## Q15. 演化到底在改「gene」還是「gene 的值」？「同樣的 gene」是什麼意思？

**先講結論**：演化改的是「**每個 gene 格子裡填的值（index）**」，**不是**「有哪些 gene」。全程「有哪些格子」不變，「格子裡填什麼」一直變。把這兩層搞混，就會誤以為不同染色體的 gene 數可能不同（其實不會，見 Q13）。

這是最容易卡住的一點，關鍵在於「gene」這個字**有兩層意思**，借生物學術語最清楚：

- **身份 / 位置（名字）**：例如 `DepthU`、`GRVW`、`WorkGroup`。＝生物學的 **locus（基因座）**，指「染色體上的**哪個位置 / 哪個欄位**」。
- **值**：那一格填的整數 index（例如 `DepthU=2` 代表選第 2 個候選）。＝生物學的 **allele（等位基因）**，指「那個位置上**目前是哪個版本**」。

**「同樣的 gene」＝ 名字 / 位置固定不變；演化改的是「每格填的值」。**

用「**欄位固定的表單**」比喻：

- 想像一張表單，欄位是 `DepthU / GRVW / WorkGroup`（＝ locus，**全族群、全程一模一樣**）。
- 每個個體是「填好的一份表單」，每格填一個 index（＝ allele，**因個體而異、被演化修改**）。
- 演化從頭到尾都在改「每格填什麼」，**從不新增或刪掉欄位**。

**逐操作看**（用一致的 3-gene 例子：`DepthU / GRVW / WorkGroup`）：

- **`sample`**（[ga-algorithm-implementation.md](ga-algorithm-implementation.md) §3.3）：對每個欄位各骰一個合法 index 填滿。例：`A = {DepthU:0, GRVW:2, WG:1}`、`B = {DepthU:1, GRVW:2, WG:0}`。→ **欄位相同，值不同**。
- **`crossover`（Uniform）**（§11.1）：逐欄擲硬幣，決定該格拿父 A 還是父 B 的值。例：子代可能 `= {DepthU: 拿A的0, GRVW: 拿B的2, WG: 拿A的1}`。→ **欄位不變，只是值重新組合**。
- **`mutation`**（§11.2）：先 `copy`，再挑某欄把值換成「同欄的其他候選 index」。例：把 `GRVW` 從 `2` 換成 `0`。→ **欄位一個沒少，只有一格的值變了**。

**表格總結**：

| 操作 | 有哪些 gene（欄位名 / 數量 / 順序） | 每個 gene 的值（index） |
| --- | --- | --- |
| `sample` | 固定（全族群一致） | 隨機骰一個合法值 |
| `crossover` | 固定 | 在父母的值之間重組 |
| `mutation` | 固定 | 某格換成同欄其他候選 |
| **全程** | **永遠不變** | **一直變** |

**收尾**：正因為「有哪些欄位、順序」全族群全程對齊，才能逐欄問「這格 A 和 B 一不一樣」去算 hamming——**欄位固定 = 逐位置可比的前提**（呼應 Q13、Q14）。`diversity()` 的逐行實作與數字例子見 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §2.3。

> 一句話：**gene 有兩層意思——「身份/位置（locus，欄位名如 `DepthU`）」與「值（allele，那格填的 index）」。演化全程只改「值」、不動「有哪些欄位」；`sample`/`crossover`/`mutation` 都在固定欄位上換 index。欄位固定對齊，正是 hamming 能逐位置比對的前提。**

---

## Q16. 有了 diversity 分數之後呢？它是拿來判斷「該停了（收斂）」嗎？

**先講結論，這裡有個關鍵誤會要破除**：**diversity 分數「不」直接拿來決定「要不要停」。** 在 Ductile 裡，diversity 只用在**族群大小自適應**（偵測早熟後把族群縮小）；真正決定「停止 / 收斂」的是 **fitness（`f_avg`/`f_max`）的停滯判斷**，跟 diversity 無關。「早熟」與「收斂停止」是**兩條獨立的邏輯、用不同訊號、觸發不同結果**，很容易被當成同一件事。

機制細節在 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) §6.1（提前終止）與 §6.2（族群自適應）已分別講清楚；這題補的是**「把兩者放在一起對比」**，因為單看很容易誤以為「diversity 低 → 就停」。

| | 判斷「收斂 → 停止」 | 判斷「早熟」 |
| --- | --- | --- |
| 看什麼訊號 | `f_avg` 與 `f_max`（fitness） | `diversity` |
| 判斷標準 | 連續 `period`(預設 5) 代，`f_avg` **和** `f_max` 的移動平均（加容忍 `tol`）都追不上當代 → 停滯 | `diversity < div_thr`（預設 `0.5`） |
| threshold 還 top-k？ | threshold 類（用 `tol` 當容忍門檻） | threshold（固定門檻 `div_thr`） |
| 觸發什麼結果 | `raise StopIteration`──**真正停止** | 切換 `low_diversity` decay──**只是加速縮小族群，不停止** |
| 對應章節 | §6.1 | §6.2 |

幾個要點：

- **「收斂 → 停止」只看 fitness，完全不碰 diversity**。條件是「`f_avg` 和 `f_max` **兩個同時**停滯」——只要還有一個在漲（超過移動平均 + `tol`）就繼續跑。這才是 `StopIteration` 的唯一來源。
- **diversity 的唯一作用是判「早熟」→ 縮族群**。這裡有個反直覺的點：偵測到早熟（`diversity < 0.5`）後，Ductile **不是「加大探索去對抗早熟」，而是「順勢加速把族群縮小」**（既然大家都差不多了，養一大群只是浪費 benchmark）。真正負責「維持探索、對抗早熟」的是 mutation / `weights`（見 Q2），不是這個 diversity 判斷。
- **top-k 完全不在這裡**。top-k 是 survival「誰活下來」的規則（Q1、§7），跟「要不要停 / 要不要縮族群」是不同階段的事，別混。

> 一句話：**diversity 分數只餵給「早熟判斷」——低於 `div_thr=0.5` 就切 `low_diversity` decay 加速縮小族群，但不會停止；真正的「收斂停止」是另一條邏輯，看 `f_avg`/`f_max` 連續 `period` 代是否停滯（用 `tol` 當容忍）。兩者都是 threshold 式、都不是 top-k。**

---

## Q17. GA 會不會演化/突變出「範圍外」的參數值？範圍選太窄會不會只能找到 local minimum？

**先講結論**：**不會超出範圍，而且是「結構上不可能」超出**（不是「機率很低」）。GA 只會在你給定的候選範圍內演化。至於「範圍選太窄」的風險——**GA 自己無法解決，因為範圍是一道硬邊界（hard boundary）**；只能靠「怎麼選範圍」來降低風險。

### 17.1 為什麼結構上不可能超出範圍

關鍵在於 gene 的表示：**gene 值是「候選清單的整數索引」，不是真實數值本身**（[ga-algorithm-implementation.md](ga-algorithm-implementation.md) §3.1）。`SearchSpace` 裡 `self.space[k] = list(range(len(候選)))`，也就是某 gene 的合法值就是 `0..n-1`；真實值要透過 `self.map[k][index]` 才映得出來。

- **`mutation`**（§11.2）：換新值時是 `np.random.choice([v for v in self.space[k] if v != ind[k]])`——**只從該 gene 的合法索引清單裡挑**，不可能挑出清單外的索引。
- **`crossover`**（§11.1）：只把兩父代**現有**的（合法）index 互換重組，當然還在範圍內。
- **`sample`**（§3.3）：也只從 `range(len)` 裡骰。

**最根本的原因：整條演化鏈對 gene 值「沒有任何算術操作」**（不會 `+1`、不內插、不加噪音），它是純粹的**類別選擇（categorical）**——只會「從清單裡挑一個」。所以「超出範圍」在數學上就不存在。（這跟連續值 GA 不同：那種 mutation 加高斯噪音真的可能漂出範圍，但這裡不會。）

### 17.2 一個重要區分：探索新「組合」vs 發明新「值」

- **✅ 新組合**：grid 沒窮舉的參數**排列**，GA 靠 crossover/mutation 能組出來（這是 GA 勝過 grid 的來源，見 Q9）。
- **❌ 新值**：若 `GRVW` 候選只有 `[2, 8]`，GA **永遠不會**試出 `GRVW=4`——`4` 不在清單裡，沒有任何 operator 生得出它。

要讓 `4` 進入搜尋，得靠 **`--convert-config` 在 GA 開跑「之前」把候選清單撐大**（`[2,8]` → `[-1,-2,2,3,4,6,8]`，見 §3.5 / Q9）。**範圍是跑之前就固定的；一旦開跑，GA 就被鎖在這個範圍內。**

### 17.3 範圍太窄怎麼辦：先分清兩種情況

- **情況 A：全域最佳的「值」落在範圍外**——例如真正最快需要 `GRVW=5` 但清單裡沒有。→ **GA 和 grid 都拿不到**，跑再久、mutation 再多都沒用。這**不是 local minimum 問題**，而是「搜尋空間根本不含全域最佳」，**沒有演算法層面的解，只能把範圍撐大**。
- **情況 B：範圍內的 local optimum**——最佳值有在範圍內，但 GA 卡在次佳山頭。這才是 mutation/diversity/`weights` 在緩解的（Q2），但**無保證**。

因此「範圍選太窄」對應的主要是**情況 A**，降低風險靠的是**怎麼選範圍**，不是 GA 本身：

1. **`--convert-config` 刻意把範圍撐得比 grid 大**（加 `-1/-2` 自動決策與更多候選），降低「最佳值在範圍外」的機率。
2. **用硬體知識 / hardware profile 設候選**（依 VGPR/LDS 限制、MI 形狀），讓合理高效區大機率被涵蓋。
3. **以現有 config 為起點再擴張**（Q3 的「以現有 YAML 為起點」），比憑空猜範圍安全。
4. **事後驗證會反過來告訴你範圍夠不夠**：若 GA 相對現有 pool 沒 uplift，往往是訊號——可能範圍太窄，該撐大重跑（Q10/Q11）。

但撐大範圍有 **trade-off**（Q3）：越大越可能涵蓋全域最佳，但也越難收斂、要越多評估。所以是「用知識圈出夠大但不失控的範圍」，不是無腦開最大。

> 一句話：**gene 是候選清單的整數索引、只做類別選擇不做算術，所以結構上永遠在範圍內演化，只會組出新「組合」、不會發明範圍外的新「值」。範圍是硬邊界——若全域最佳的值落在範圍外，GA（和 grid）都拿不到，只能靠 `--convert-config`／硬體知識／現有 config 把範圍圈好，再用事後驗證回饋。範圍內的 local optimum 才是 mutation/diversity 在緩解（且無保證）。**

---

## Q18. 先用分析模型（如 Roofline）預測好範圍、再讓 GA 搜，是不是更好的方向？目前設計有這樣做嗎？

**先講結論**：方向是對的（這是公認的 surrogate/model-assisted DSE、warm-start 思路），也正是本 repo 研究線在規劃的；**但目前 production 設計「沒有」這樣做**——Ductile 的範圍來自靜態規則 + 專家 profile，而現有的分析/模擬模型（Origami/Formocast）只在「選擇層」挑既有 kernel，沒有回饋給 GA 的範圍。

### 18.1 目前設計實際上怎麼定範圍（沒有用分析模型 per-shape 預測）

1. **`--convert-config` 的靜態規則擴張**：按固定規則撐大值域（加 `-1/-2`、加候選），不看 shape、不跑模型（§3.5 / Q9）。
2. **專家設計的 hardware profile**：GEKO configure 階段從 log + `fork_params/hw_profiles/gfx942` 這種人工/經驗 profile 生出範圍，是 **domain-knowledge 先驗**，不是模型即時預測。

那 Origami（分析式延遲模型，精神接近 Roofline）、Formocast（模擬式）呢？**它們是模型，但在「選擇層（selection）」，不在「調校層（tuning）」**——見 [../origami/ecosystem-and-formocast.md](../origami/ecosystem-and-formocast.md)：

- **tuning 層**（決定「有哪些 kernel」）＝ grid / GEKO / **Ductile GA**。
- **selection 層**（從既有 kernel「挑一個」）＝ equality/grid 查表 / **Origami / Formocast**。

也就是說，Origami/Formocast 是在**已生成的 kernel 裡挑最快的**（runtime 或建 library 時預測），**沒有回頭餵 GA「該在哪個範圍搜」**。兩層目前是解耦的。（Formocast 的 `PredictionThreshold` 是「用模型縮短 tuning」的一種，但用在建 library 的 prediction，不是 seeding GA 範圍。）

**而你提的方向，正是研究線在規劃的**——見 [../research/surrogate-dse-plan.md](../research/surrogate-dse-plan.md) 的主線（原切角 #2：surrogate-assisted tuning；predictor → pre-screen candidate → 量省下的 benchmark 次數）。所以：**結論是 production 還沒這樣做，但這是明確的研究方向，你的直覺跟他們吻合。**

### 18.2 若要做，Roofline 的侷限與兩個注入點

**Roofline 的侷限**：它適合建立直覺（判 compute-bound / memory-bound 與效能上界），但**太粗**——抓不到 cache 命中、LDS bank conflict、occupancy 懸崖這些真正決定離散 config 好壞的細節，**沒辦法直接指出「哪組 config 最快」**。要真的縮 config 範圍，得用更細的模型（Origami analytical / Formocast simulation）。Roofline 頂多用來「定 regime、給軟性偏好」。

**兩個把模型接進 GA 的注入點**（直接關係到 Q17 的 hard boundary 陷阱）：

| 注入點 | 做法 | 風險 |
| --- | --- | --- |
| **A. 改每個 gene 的候選清單（硬縮/擴範圍）** | 像「更聰明的 `--convert-config`」，用模型預測後直接砍/加候選值 | **危險**：模型若錯，把真最佳值剪掉 → GA 永遠拿不到（正是 Q17 的「最佳落在範圍外」） |
| **B. 用模型預測設 sampling `weights`/`probs`（軟性偏重）** | 現成 hook：`weights` 經 softmax 轉 `probs` 偏重初始採樣，甚至偏重 mutation（§6.4、§11.2） | **較安全**：只「偏重」不「硬剪」，模型錯了 GA 仍能靠 mutation 逃出 |

**建議 B 優於 A**：metaheuristic 暖啟動的黃金原則是「**biasing 而非 pruning**」——讓模型「指路」但不「封路」。硬縮範圍（A）會把模型偏誤變成 GA 的天花板；軟性加權（B）在「模型看走眼」時仍保留探索能力。而 `weights/weight_beta → probs` 這個 hook **在現有程式碼已經存在**（§6.4），所以「用 Roofline/analytical model 算出 weights 再餵給採樣」是改動最小、最現成的接入方式。這也呼應 Q8「GA 與預測模型互補、不是二選一」。

> 一句話：**「先用模型指向好範圍、再用 GA 搜」方向正確（surrogate-assisted / warm-start），也是研究線（`surrogate-dse-plan` 主線，原切角#2）的規劃；但目前 production 沒這樣做——Ductile 範圍來自 `--convert-config` 靜態規則 + 專家 profile，Origami/Formocast 只在 selection 層挑既有 kernel。真要做，Roofline 太粗（宜用更細模型），且最好透過現成的 `weights/probs` 做「軟性偏重」而非「硬縮範圍」，以免模型出錯把真最佳值剪掉（重蹈 Q17 的 hard boundary）。**

---

## 一句話總結

> 這份 Q&A 補的都是「觀念與定位」層面的澄清：**GA 只有 survival 那步像貪心、整體不是（Q1）；mutation 不保證跳出 local minimum、只機率性緩解（Q2）；`seed` 是亂數種子不是初始解、開跑不用前置 tuning（Q3）；沒有接近全域最佳的理論證明、只有 elitism 的單調性保證（Q4）；`np.max` 比的是相對比值不是絕對 GFLOPS（Q5、Q6）；selection 隨機性在「抓哪 k 個」、預設 tournament(k=2) 是為抗噪音（Q7）；GA 是搜一組解、和 Formocast 那種預測模型互補（Q8）；GA 只在 grid 無法窮舉時才贏（Q9）；驗證在 offline 做完、runtime 只查表（Q10）；驗證 GA 解很便宜、不吐回省下的時間（Q11）；多 shape 平庸解源自共用族群、非輸出（Q12）；染色體固定長度、欄位對齊才能逐位置比對（Q13）；`diversity()` 用 hamming 是因 gene 是類別編號、且各 gene 等權（Q14）；演化只改 gene 的值（allele）、不動 gene 的身份（locus）（Q15）；diversity 只判早熟（縮族群）、不觸發停止，停止是 fitness 停滯（Q16）；GA 結構上只在範圍內演化、範圍是硬邊界（Q17）；用分析模型暖啟動 GA 範圍是研究方向、目前設計未採用，宜軟性偏重而非硬縮（Q18）。** 機制細節請回 [ga-algorithm-implementation.md](ga-algorithm-implementation.md) 與 [ductile-deep-dive.md](ductile-deep-dive.md)。
