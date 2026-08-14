# 報告來源索引(繁中鏡像)— Formocast Factorized Gen0 Guidance study(S11 + S14)

> **同步規則(SYNC):** 本檔是 `[report-source-index.md](report-source-index.md)` 的**繁體中文鏡像**。
> **英文版為權威**;任一版變動時兩份必須同步(維護者每次編輯英文版即同步更新本鏡像)。翻譯只針對
> 敘述文字;**專有名詞、程式碼識別字、檔案路徑、§ 章節編號、數字、表格結構、amendment token、gene
> 名稱、evidence label、sha256 一律保留英文原樣**。若兩版衝突,以英文版為準。

> **非權威、live 參考文件。** 本檔存在的目的,是讓 closing report 能從**單一地方**起草。它**彙整並交叉
> 引用**權威文件;**不自行制定任何 policy**。任何衝突以權威來源為準
> (順序:**charter > experiment-plan > design > 本索引 / report > qa**)。以下所有實驗規劃理由
> **都已存在於某份權威文件**(逐條標註來源)—— 本檔不新增 policy。
>
> **反捏造:** 每個結果數值在該 run 完成、並經獨立 verifier 填入前,一律為 `NOT_EVALUATED` 並附來源路徑。
> `not_evaluated ≠ no effect`。**最後更新 2026-08-13。**
>
> **目前執行實況(2026-08-13):** **capped(P0 = 512)** campaign 在**三個 shape 上全部完成** ——
> baseline 15/15、guided 15/15,medium、large 與 tiny 的 7× interleaved 重測也都做完了。
> **native(P0 = 11,405)** addendum 在 **medium** 上已完成(5/5 GA + 5/5 重測),**large 仍在跑**:
> 五個 baseline seed 都還在 Gen0 抽樣階段,尚未產出任何一列 trajectory。native large 的 Gen0 已經連續
> 四次被整機重開機吃掉 —— Ductile 要等 generation 1 完成才會寫 checkpoint,而 11,405 樣本的 Gen0 從來
> 沒有塞進任何一個重開機之間的視窗(~4–5.5 h)—— 所以它在這台機器上是否可達,是一個待 owner 裁決的
> 開放問題。
>
> 2026-08-13 有兩件事改變了證據面貌,並已反映在全文各處:**clock-ramp 機制被直接遙測否證**
> (warm-up 的*相關性*成立;*解釋*不成立 —— §7.1b);以及 S14 的各份報告依 `REPORT-LOCATION-20260813`
> 被整併進 `reports/staged/`,成為一份正式報告加三份 per-shape 附冊(§6)。
>
> 尚有九項維持 `PENDING_HUMAN_DECISION`(§9.3)。合併 claim 的措辭需要 medium ∧ large
> (**charter** §8.2 —— 不是本檔的 §8.2,那是 Checkpointing)。



## Contents

- [§0 Conventions](#0-conventions)
- [§1 實驗一覽](#1-實驗一覽experiments-at-a-glance)
- [§2 Amendment ledger](#2-amendment-ledgertoken--變更--權威來源)
- [§3 設計理由](#3-設計理由報告可直接引用的散文--每條附來源)
- [§4 Claim 框架](#4-claim-框架什麼能說--不能說)
- [§5 Metrics & acceptance](#5-metrics--acceptance) —— 含 [§5c AUC](#5c-auc-準則是什麼以及為何量測缺陷波及不到它)
- [§6 Artifact / file reference](#6-artifact--file-reference)
- [§7 結果 placeholder](#7-結果-placeholderrun-完成--獨立驗證後才填--切勿捏造)
- [§8 已知 caveat / 限制](#8-已知-caveat--限制供-discussion-章節)
- [§9 PENDING_HUMAN_DECISION —— medium 量測缺陷](#9-pending_human_decision--medium-重測量測缺陷的處置) —— 含 [§9.5 peak-of-7](#95-pending_human_decision--peak-of-7-作為-medium-端點的能力論證)

---



## §0 Conventions

- **Evidence labels**(報告全文一致使用):
  - `[MODEL-ONLY]` = Formocast 模型空間量(S11 scores、per-shape `S_g`);
  - `[BASELINE GPU]` = Arm G 真實量測;
  - `[GUIDED GPU]` = Arm F 真實量測;
  - `[CODE AUDIT]` = 讀 code/artifact 得到的事實(附 file:line / path)。
- **Seeds 是實驗單位**(5 對 paired seed 24001–24005)。切勿把少數 seed 包裝成統計顯著性。

---



## §1 實驗一覽(Experiments at a glance)


| Experiment                                  | 目的                                                                        | 狀態(2026-08-11)                                                                                                      | 關鍵 artifact / lock                                          | 報告章節                         |
| ------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------- |
| **S11 model-only factorization**            | per-gene Formocast→Gen0 guidance 機制在模型空間是否成立;訊號多稀疏                        | per-size scores **DONE**;max-reducer closeout **無法完成** —— 封存 `analyze` 結構性 assert(見 §7.3),已由經驗證的 out-of-band 平行重製證實 | `s11-native-scores.json`;`parallel-analyze/VERIFICATION.md` | S11 report                   |
| **S14 capped-512 per-shape G/F**(主)         | 在 P0=512 下,Formocast Gen0 prior 是否讓每個 shape 的搜尋/最終品質優於 uniform            | **COMPLETE** —— baseline 15/15、guided 15/15,三個 shape 的 7× 重測皆已完成(`guided_status.json`:`guided_complete: true`) | Lock A + Lock B                                             | `staged/full-ga-baseline-vs-guided-outcome-report.md` §3 |
| **Conditional Arm S**(same-entropy shuffle) | 把 F>G 歸因於 physics *方向* 而非單純集中                                             | **DOES NOT TRIGGER** —— 觸發條件要求 F 在 ≥1 個 confirmatory shape 上過 gate;medium 與 large 都沒有(§9.1)。因此本 checkpoint 不需要封 Lock C | Lock C(Arm-S shuffle,不需封存)                                  | `staged/full-ga-baseline-vs-guided-outcome-report.md` §3.5 |
| **Native-P0 ~11,405 addendum —— medium**    | (Q1) capped 方向在原生 Gen0 是否穩健;(Q2) 稀釋;(Q3) Gen0 極值機制                        | **COMPLETE** 5/5 GA + 5/5 重測(另已重測兩次;campaign 更正見 §9.2)。最終端點為 `NOT_EVALUATED / instrument-invalid`                    | 重用 Lock B guidance                                          | `staged/s14-medium-report.md` §4 |
| **Native-P0 ~11,405 addendum —— large**     | 在 large 上問同樣三個問題                                                          | **IN PROGRESS** —— 5 個 baseline seed 在 Gen0 抽樣中,尚無 trajectory 列;Gen0 已連續四次被整機重開機吃掉                                  | 重用 Lock B guidance                                          | `staged/s14-large-report.md` §10(scaffold) |


---



## §2 Amendment ledger(token → 變更 → 權威來源)


| Token                              | 變更了什麼                                                                                                                                                                                                                                                                                | 權威文件                                                                 |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| `RESCOPE-STAGE1-OUTCOME-20260807`  | 凍結 S12+;唯一 active edge S11→S14;P0 64→512;保留原生早停;移除 U_floor 硬 gate                                                                                                                                                                                                                    | experiment-plan active-projection;S14 §6                             |
| `PER-SHAPE-SOO-OUTCOME-20260809`   | Joint-MOO + aggregate `Q=max_s` → **逐 shape 單目標**(每個 shape 各自的 GA／guidance／評估;medium+large 為 confirmatory、tiny 為探索性;5 對全新 seed;雙向;逐 shape gate)                                                                                                       | S14 design **§10**;experiment-plan criterion `S14_PER_SHAPE_OUTCOME` |
| `ENTROPY-CAP-20260810`             | Binary gene exclusion → **universal per-gene mixture cap** `p1=(1−ρ)p0+ρ·q(λ=8)`、`ρ=max{ρ∈[0,0.80]:H_norm≥0.80}`;以較低強度納入 DepthU/PrefetchGlobalRead                                                                                                                                   | S14 §10.3;qa-09 §4.3a                                                |
| `CLAIM-SCOPE-S14-20260810`         | S14 claim **two-sided**;資料支持時**得宣稱最終 tuned 品質提升**(bounded/modest power、限受測 shape、不預設結論、不捏造)                                                                                                                                                                                          | charter **§8.6a**                                                    |
| — 2026-08-10(b) extension          | **beat-native** 由絕對禁止改為 **two-sided / 等資料再說**(需實際量測 native 且揭露 confounding)                                                                                                                                                                                                          | charter §8.6a 2026-08-10(b);§8.6 note                                |
| `CONDITIONAL-ARM-S-20260810`       | Arm S pre-register 為 **conditional**(觸發 + 歸因規則;S20 為其主要 home)                                                                                                                                                                                                                        | S14 §10.2                                                            |
| `NATIVE-P0-ROBUSTNESS-20260811`    | Pre-register **native-Gen0(~11,405)** robustness/稀釋 addendum                                                                                                                                                                                                              | S14 **§12**;experiment-plan criterion note                           |
| `NATIVE-P0-ROBUSTNESS-20260811(b)` | 將該 addendum 由 **large-only 擴充為 large + medium**;新增 **Q3** 極值機制操縱檢驗與預註冊方向性預測 | S14 **§12.1 Q3、§12.2、§12.4.4、§12.6** |
| `DEVIATION-REMEASURE-STOPLINE-20260812` | 在 remeasure 的 pre-flight 守門連續拒絕三個符合設計的 run 之後,把它放寬為真正該成立的不變量(stop 行**至多一行**;run **不得超過**第 30 代);量測邏輯未動 | 本索引 §8.4 |
| `REPORT-LOCATION-20260813` | **僅為簿記** —— `formal_report_path` 移到 `reports/staged/…`;新增三份 per-shape 附冊。**不改動**任何 hypothesis、estimand、metric、threshold、gate 或 claim | S14 design **§12A** |
| `CAPABILITY-ENDPOINT-PACKET-20260813` | `PENDING_HUMAN_DECISION` —— 以三項彼此獨立的理由駁回 peak-of-7 作為 medium 的端點;記載 count-invariance 主張為**偽**(`max` 在兩個 native campaign 上都把預註冊的 §12.3 ≥4/5 判準往受測臂方向跨過去);禁止 `max` 出現在任何 acceptance/sensitivity 表格;以一個決定性的 `int32` 溢位結案 §13.7 item 2 | S14 design **§14**;本索引 **§9.5** |
| `MEASUREMENT-DEFECT-PACKET-20260813` | `PENDING_HUMAN_DECISION` —— medium 重測缺陷的處置:估計量(D1)、margin(D2)、逐 shape claim 階梯(D3),共九項待 owner 裁決 | S14 design **§13**;本索引 **§9** |
| `REDUCER-FACT-CORRECTION-20260812` | **僅文件層的事實更正** —— Ductile **未實作 Pareto/非支配排序**;`soo=False` 以 `np.max` 縮併為純量(`ga.py:95, 256–273`),故 `Q=max_s` 是 Ductile 的**原生** fitness,不是事後外加的步驟。**決策、pins、gate、claim 一律不變**;per-shape 的實證理由(tiny 主導 Q、seed-14005)不受影響 —— 更正後的論述是「Ductile **內建**的跨-size reducer 本身即缺陷,per-shape 繞開它」。 | S14 §10.1 更正框;qa-09 §2.1/§2.2;本索引 §3.1.2                             |


---



## §3 設計理由(報告可直接引用的散文 — 每條附來源)

> **⚠ `ga.py:NNN` 這些引用指的是哪一份 `ga.py` —— 2026-08-13 稽核後補上。** 這個 repo 裡有**兩份
> `ga.py`,而且它們不是同一個檔案**:
>
> | copy | path | lines | `DUCTILE_FORCE_P0` |
> |---|---|---:|---:|
> | **repo**(以下的行號解析到這裡) | `projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py` | 756 | **0 occurrences** |
> | **engine —— 實際執行這些 run 的那一份** | `agent_run/260807-s14-baseline-run/engine/projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py` | 346 | 4 occurrences |
>
> 本文件中每一個 `ga.py:NNN` 引用都已驗證能**解析到 repo 那一份**,而且那些行號在那裡是正確的。但
> **實驗跑的是 engine 那一份**,它在上述每一個行號上的內容都不一樣。讀者必須避免踩到的兩個後果:
>
> 1. **以 `ga.py:NNN` 引用的機制主張,描述的是 repo 樹裡的演算法。** 兩份行為一致的地方,這無害;
>    兩份不一致的地方,以 engine 那一份為準,因為那才是實際發生的事。
> 2. **§3.2b 的 `DUCTILE_FORCE_P0` 主張只對 engine 那一份成立** —— 這個環境變數在 repo 那一份裡
>    根本不存在,所以那個特定引用必須讀成 `engine .../ga.py:112`,而不是 repo 的行號。
>
> `NOT_EVALUATED`:兩份之間逐行的差異對照表。目前只查核過 `DUCTILE_FORCE_P0` 這個分支。



### §3.1 Per-shape single-objective(為何不用 joint-MOO / aggregate-Q)



#### §3.1.1 名詞

- **candidate(候選)** —— 一個完整的 30-gene kernel config;GA 族群的一員。
- **champion(冠軍)** —— *被選為該次 run 答案的那「一個」candidate*:整條 run 中最佳的有效候選
(final incumbent),以 canonical-hash 遞增 tie-break。所以 champion **就是**一個 candidate —— 勝出的
那個。報告比較的一切(`best_fitness`、7× remeasure)都是這一個 config 的性質。
- `GFLOPS_s` —— 某候選**在 problem size** `s` **上**量到的真實吞吐量。有 3 個 size,每個候選就有 3 個。
- `R_s` —— **per-size 參考 GFLOPS,作為正規化分母**:`[CODE AUDIT]` runner 文件寫明
*「R_s = pilot per-size median GFLOPS」*,取自重用的 3-anchor × 7-repeat 噪音 pilot
(medium 3,199.94 / large 180,336.00 / tiny 0.75)。它的作用是讓不同 size **可比**:tiny→large 的原始
GFLOPS 相差約 5 個數量級(§3.6.1),`GFLOPS_s / R_s` 把每個 size 轉成無因次的「該 size 參考值的幾分之
幾」,才能互相比較或合併。
- `Q` —— GA 為候選最大化的**純量 fitness**,由「把該候選的 per-size 正規化分數縮併成一個數」而來。



#### §3.1.2 `soo=False` 實際上怎麼運作 —— 它是 `max` 縮併,**不是** Pareto front

**更正一個常見描述**(包括本索引的早期草稿):雖然 `soo=False` 被稱作「多目標」,**Ductile 並未做任何
Pareto / 非支配排序**。`[CODE AUDIT]` 對全樹搜尋 `pareto|non-dominated|nsga|crowding` **查無任何結果**。
實際發生的是(`ga.py:256–273`):

```python
best.F = scores.max(1)                                   # per-size incumbent:各 size 上的最佳分數
pop.F  = self.reduce_fn(scores / best.F[..., None], 0)   # reduce_fn = np.max  (soo=False)
                                                         #           = np.mean (soo=True)
```

- `scores` 是一個 **(n_sizes × N) 矩陣** —— 一列一個 problem size,一行一個候選。
- 每個候選的 per-size 分數先除以該 size 的參考值,然後把各列**縮併成每個候選一個純量**。
- `soo=False` ⇒ 縮併用 `np.max` ⇒ `Q_c = max_s ( GFLOPS_{s,c} / R_s )`;
`soo=True` ⇒ 用 `np.mean`。

所以那些「目標」從未並存:它們被平均(`mean`),或在此處 —— **一個候選只用它表現最好的那一個 size 來
評分**(`max`)。沒有前緣、沒有支配關係,因此也沒有保留任何多目標取捨。

#### §3.1.3 為什麼一定要收成單一 champion

GA 必須能對候選**排序**才能做 selection,而一次 run 結束時必須交出**一個** config 去 benchmark、重測、
寫進報告。集合形式的答案(front)既餵不進 selection,也無法做配對的 G-vs-F 比較。所以要縮併成一個純量
`Q`,再縮成一個 champion。

#### §3.1.4 為何 `Q = max_s` 有缺陷

對正規化後的 size 取**最大值**,意味著一個候選是用**它剛好看起來最好的那一個 size** 來評分 —— 另外兩個
size 被丟棄。而 tiny 是雜訊遠大於其他的 shape(η_tiny = 0.4466 ≈ ±45%,對比 η_medium = 0.0042 ≈ ±0.4%;
§3.6.1),因此一次幸運的 tiny 量測就能主導整個分數。

pilot 中觀察到的後果:**seed-14005 的 champion 在 large 快近 2×,卻拿到*最低*的 Q** —— 這個 metric 用最
吵的那個維度挑出了它的贏家。

#### §3.1.5 修法

**每個 shape 各跑一條 single-objective GA**,per-shape guidance、per-shape evaluation。如此就完全不需要
跨 size 縮併:fitness 矩陣是 (1 × N),對單一列取 `max` 即恆等,所以 `Q = GFLOPS / R_s` 就只是「在被最佳化
的那個 shape 上的(正規化)真實吞吐量」。

三個發散 shape 於是回歸其真正用途 —— 作為**尺寸多樣性**,用來檢查 guidance 效應是否可重現 —— 而不是被
共同最佳化成一個折衷答案。

*來源:*`[CODE AUDIT]` **`algorithm/ga.py:95, 256–273`*(reduce_fn、無 Pareto 機制);*
`scripts/run_pershape_seed.py`*(R_s 定義、*`(1,N)` *fitness);Lock A(*`champion_per_shape`*、*
*per-shape η_s);S14 §10.1;qa-09。*

### §3.2 為何 P0=512(以及誠實的外部效度更正)

512 不是隨手挑的下限:它是 Ductile **自己的穩態族群** —— config 預設值(`ga.py:47`、`defaults.yaml`),
也是 native Ductile 收斂到的 **decay target** `_pop_size`(`ga.py:110`)。Native 會把 Gen0 灌大到
`int(max_sp_sz×1.15)=int(9,918×1.15)=11,405`(`ga.py:118`),之後每代把超出部分砍半、收回 512
(`ga.py:116`,套用於 `:293`)。

這個膨脹**存在的唯一原因是覆蓋 group_0**(9,918 候選的 MatrixInstruction/WorkGroup gene),而 group_0
**不在 Formocast treatment 內、兩臂相同**。

誠實的兩段式框架:

- **(a) 影響絕對結果 / 外部效度。** cap 到 512 **確實**縮小 group_0 / 整體搜尋 → 影響絕對 champion
品質 —— **故 claim 限定為「P0-capped=512 Ductile variant」,非 native Ductile**。
- **(b) 不偏 G-vs-F 配對對比。** 兩臂皆以相同 p0、common Gen0 uniforms 抽 group_0,被縮小的覆蓋是兩臂
共享的邊界條件,在組內差中抵銷,只剩 free-gene 重加權為唯一外生差異。

Caveat:量到的是「P0=512 下的效應」(**treatment×budget 交互作用**),由 native addendum(§3.3)探討。

*來源:S14 §6.1/§10.2、S14 report §2.3。*

### §3.2a `9,918` 與 `×1.15` 是怎麼來的

`max_sp_sz` **其實就是「候選清單最長的那個 gene 的長度」。** `space.py:71` 定義
`self.sizes = {k: len(v) for k, v in space.items()}` —— 一個 gene 的「size」字面上就是*它的候選清單有幾個
條目*。`ga.py:112` 再取 `max_sp_sz = max(sz for sz in self.space.sizes.values())`(對全部 30 個 gene)。
29 個 ungrouped free gene 每個只有 2–6 個值,所以最大值由 `group_0` 決定。

`group_0` **= 9,918,是因為 frozen YAML 字面上就列了 9,918 條。** `[CODE AUDIT]`
`grep -c "MatrixInstruction:" protocol/v1/inputs/s10-generated.yaml` → **9918**(精確吻合),與 registry
記錄的 expanded group cardinalities `9918 / 3 / 2` 一致。所以 9,918 **不是由軸範圍相乘算出來的** ——
它是**列舉長度**:GEKO 產生的候選 kernel macro-shape 池。

這 9,918 條具體是什麼:

- 每條是一個完整的 **MatrixInstruction 9-tuple**(外加可選的 `WorkGroup:` 覆寫 —— 262 條有),並標註其
MacroTile / ThreadTile / WorkGroup / GSU / LSU / occupancy 等 metadata;
- 它們橫跨 **434 種相異 MacroTile 形狀**,並標註了 **13 個相異 problem size**(GEKO 為之產生的 size);
- 其中 MatrixInstruction tuple **只有 840 個相異** —— 條目會重複,靠隨附的 WorkGroup/其他欄位以及「為哪個
size 產生」來區分。

所以 group_0 最好理解成 **「GEKO 認為值得一試的 kernel 形狀池,跨 problem size 累積而成」** ,而 `9,918` 就是
這個池的大小 —— 它是 frozen 輸入 YAML 的性質,不是 GA 的性質。

**9,918 有兩件事「不是」:**

- **不是 Ductile 的設計上限。** Ductile 對 gene 基數**沒有任何上限**:`space.py` 只拒絕*空*清單
(`if any(v == 0 …): raise`),`ga.py:107` 只要求 `n_perms ≥ pop_size`。一個有一百萬個候選的 gene 也會
被接受。
- **不是 MatrixInstruction × WorkGroup 組合的理論最大值。** 它是*精選的列舉*,不是笛卡兒積 —— 9,918 條
裡只有 **840 個相異的 MatrixInstruction tuple**,靠不同的 WorkGroup / 目標 size 情境重複出現。換一份
輸入 YAML,這個數字就變了。

`×1.15` **是一個沒有文件的 magic constant。** `[CODE AUDIT]` 整個 ductile 樹**沒有任何註解或文件**解釋它;
唯一相關的文字是 `ga.py:114` 的警告字串(「Some variables have a larger search space than pop_size.
Increasing pop_size for the first generations.」)。

它的*功能*意圖可以推得:當 `pop_size=512` 而某個 gene 有 9,918 條時,Gen0 最多只能出現其中 512 個形狀(約 95% 的池從未被看到),所以 constructor 把 pop_size 拉高到 **大約每個候選一次抽樣、再加 15% 餘裕**。

`11,405` **究竟是什麼 —— 一個常見誤讀,值得明講。** 它是 **Gen0 的個體(individual)數量**,也就是族群
大小。它**不是**「從 group_0 挑 9,918 條、再混搭約 15% 的其他 gene」。`[CODE AUDIT]` `space.py:57` 產生
每個個體的方式是:

```python
ind = Individual({k: rng.choice(s, p=p.get(k, None)) for k, s in sizes.items()})
```

—— 亦即**每個個體都獨立地對全部 30 個 gene 各抽一個值**,構成一個*完整*的 kernel config。所以 Gen0 是
一張 11,405 列的完整 config 表:


|           | group_0     | DepthU | 1LDSBuffer | PrefetchGlobalRead | …(共 30 欄) |
| --------- | ----------- | ------ | ---------- | ------------------ | --------- |
| 個體 1      | shape #4172 | 64     | 0          | 2                  | …         |
| 個體 2      | shape #883  | 128    | 1          | 1                  | …         |
| …         | …           | …      | …          | …                  | …         |
| 個體 11,405 | shape #4172 | 32     | 0          | 2                  | …         |


- **列數 = 11,405** ← 這才是 ×1.15 設定的東西;
- **每一列都是完整 config**,不是只挑 group_0;
- `group_0` 那一**欄**從 9,918 個選項抽 11,405 次 ⇒ **平均每個選項約 1.15 次** —— 這才是 1.15 的真正
含義(也是下方覆蓋率算式適用的理由)。

**但它並沒有達成覆蓋 —— 這點值得誠實寫明:**


| 量                                     | 值                             |
| ------------------------------------- | ----------------------------- |
| 膨脹後 Gen0 `int(9,918 × 1.15)`          | **11,405**                    |
| 每個 group_0 候選的平均抽到次數                  | 1.150                         |
| 均勻抽樣下被抽到 ≥1 次的候選比例                    | **≈ 68.3 %**(`1 − e^{−1.15}`) |
| 近乎全覆蓋所需抽樣數(coupon collector,`n·ln n`) | **≈ 91,266**                  |


所以 `1.15` 買到的是「平均每個候選約一次抽樣」,**不是**「看遍每個形狀」—— 即使在原生 Gen0 下仍約有 32%
的池沒被抽到;而且因為 group_0 是 GEKO **加權**(非均勻),實際覆蓋會更偏向高權重形狀。這個膨脹也是
**短暫的**:decay 每代把超出部分砍半、收回 512(§3.2),所以它只形塑最前面幾代。

*來源:*`[CODE AUDIT]` `core/space.py:71`*、*`algorithm/ga.py:112/114/118`*;**
`protocol/v1/inputs/s10-generated.yaml`**;s10 entry-gate report(expanded group cardinalities)。*

### §3.2b Population decay —— 512 不是 floor,256 才是

§3.2a 的 `×1.15` 膨脹並非永久:Ductile 每代結束後都會把族群衰減回去。這裡有**兩條不同的 decay 法則**,
而哪一條生效會改變 floor。

```python
# ga.py:116 —— 只在 max_sp_sz > pop_size(膨脹情境)才安裝
self.decay = lambda sz: int(self._pop_size + (sz - self._pop_size) / 2)          # -> floor 512

# ga.py:291 —— 只要任一代回報 diversity < div_thr(0.5),就把上面那條「覆寫」掉
self.decay = lambda sz: int(self._pop_size / 2 + (sz - self._pop_size / 2) / 1.25)  # -> floor 256

# ga.py:293 —— 每代結束時套用
self.pop_size = self.decay(self.pop_size) if hasattr(self, "decay") else self.pop_size
```

三個對解讀我們數字有影響的後果:

- **這不是「每代把族群砍半」。** 法則 1 砍的只是*超出* `_pop_size` 的部分,所以尺寸是幾何式收斂到 512:
`11,405 → 5,958 → 3,235 → 1,873 → 1,192 → 852 → 682 → 597 → 554 → 533 → 522 → 517 → 514 → 513 → 512`。
約 14 代後貼齊 floor —— 也就是在原生設定下,**30 代 horizon 大約有一半是花在把膨脹的 Gen0 收回來**。
- **法則 2 的目標是 256 而不是 512,而且是不可逆的。** 一旦 diversity 跌破 `div_thr=0.5`,`decay`
attribute 就被永久覆寫,沒有路徑回到法則 1。
- **在我們的 P0-capped run 中,法則 1 根本從未被安裝。** 因為 `DUCTILE_FORCE_P0=1` 跳過了
`max_sp_sz > pop_size` 分支,`hasattr(self, "decay")` 為 False,族群本應永遠固定在 512 ——
*除非* diversity 跌破 0.5,而那會安裝法則 2。

**實際發生了什麼(已量測)。** 在每一個 S14 large run、兩個臂中,diversity 都在第 6 代跨過 0.5,
因此法則 2 確實啟動,族群往 256 衰減:


| gen                             | 1     | 5     | **6**     | 10    | 15    | 21    |
| ------------------------------- | ----- | ----- | --------- | ----- | ----- | ----- |
| diversity(baseline, seed 24001) | 0.568 | 0.515 | **0.492** | 0.417 | 0.345 | 0.322 |
| diversity(guided, seed 24001)   | 0.560 | 0.508 | **0.491** | 0.412 | 0.329 | 0.316 |
| 該代 evals                        | 489   | 507   | 507       | 349   | 277   | 252   |


第 6 代之後實測的每代 eval 數(457、418、384、349、…、252)與法則 2 的序列
`256 + (sz−256)/1.25` = 460、419、386、360、… 在有效候選率的誤差內吻合。

*Source:*`ga.py:116, 291, 293`*;*`stage3_{baseline,guided}/seed_24001/large/*optimization.log`*。*

分析上的兩點註記:

- 此 decay 在**兩臂的同一代**啟動,diversity 軌跡幾乎重疊,因此它是**協定的共同性質、不是 arm 層級的
confounder** —— 它影響的是絕對 eval 預算,不影響配對的 G-vs-F 對比。
- 由於每代的評估次數並非定值,**AUC 必須對「共同的累積評估預算」積分,而不是對代數積分** ——
§7.1/§7.2 正是這樣算的(取兩臂最終 `cumulative_complete_evals` 的 `min`)。



### §3.3 Native-11,405 addendum(large + medium)

在 native Gen0 下跑 G/F,其餘設定與 512 版完全相同。原(2026-08-11)預註冊為 **large-only**;
2026-08-12 經 `NATIVE-P0-ROBUSTNESS-20260811(b)` 擴充為 **large + medium**。

它回答三個問題:

- **(Q1)穩健性。** capped-512 的結論對 Gen0 規模是否穩健(消除「你把 P0 改小了」的 caveat)?
- **(Q2)稀釋。** guidance 效應在原生規模下是否縮小(假說:prior 在小 Gen0 最有效)?
- **(Q3)極值機制**(由 `(b)` 新增)。§7.2.1 發現 guidance 改善 Gen0 的**中心**卻惡化 Gen0 的**極值**,
  因為 GA selection 讀的是最大值,而最大值由離散程度而非中心位置決定。Gen0 池大小正是控制該最大值
  往尾部取多深的直接參數,512 → 11,405 就是對這個變因的 **22× 操縱**。

為何加入 medium(§12.2 原本排除它;兩項原始前提都被 capped remeasure 資料推翻,而該資料在
2026-08-11 時尚不存在):

- **成本。** 實測 GPU 評估時間(seed 24001):medium **0.17 h** vs large **5.61 h** —— 便宜約 33×。
  native medium 全 5 seed × 2 arm 的成本遠低於單一 native large 的 seed-arm。
- ~~**資訊量 —— 原判斷方向反了。** medium 是*唯一*兩臂差異可被量測的 shape(per-seed F/G 0.36×–2.12×,
  對比 η_medium = 0.42 %,§7.1);large 的五個 seed 全落在 η_large = 12.28 % 之內(§7.2)。Q2 問的是
  效應量如何隨 Gen0 規模改變,因此需要一個效應量本身量得出來的 shape。~~
  **RETRACTED 2026-08-13。** 這曾是把 medium 加進 native addendum 的既述理由,而它的前提**作廢**:
  0.36×–2.12× 的離散是量測缺陷(§7.1a/§7.1b),不是兩臂差異,所以 medium 並不是「效應量量得出來的
  shape」—— 它是儀器失效的那個 shape。§7.1a 已經記載這條理由必須更正;這裡就是那次更正,補得很晚
  (2026-08-13 稽核時發現,它躲過了先前那一輪撤回)。
  **改為支持納入 medium 的理由:** Q3,也就是 Gen0 極值機制的問題,它讀的是 GA trajectory,
  **完全不依賴 champion 重測**。medium 最終端點上的 Q2 效應量比較是 `NOT_EVALUATED`(design §13.6)。
- **Q3 需要的是池大小、不是豐富的 treatment**,所以在 medium 上同樣可測;兩個 shape 併跑還能得到
  跨 shape 梯度(large 有 5 個 activated gene、medium 有 2 個)。

已驗證的前提:medium 與 large 的 config 除四個 `ProblemSizes` 數字外逐位元相同,且同樣內嵌 9,918 個
`MatrixInstruction` 項,故 medium 的 `max_sp_sz` 亦為 9,918,native Gen0 同樣膨脹到 11,405 ——
不會落入 `ga.py:119` 的 `max_sp_sz < pop_size/5` 砍半分支。

Q3 的預註冊方向性預測(執行前寫定、可否證):guided 的 Gen0 **極值**劣勢在 11,405 下應**擴大**;
guided 的 Gen0 **中心**優勢應維持或擴大;且**擴大幅度 large 應大於 medium**。若結果相反,必須記錄為
該機制被推翻。

排程:**medium 先、large 後** —— medium 數小時內即可給出 Q2/Q3 首批讀數,並在投入 large 的 3–4 天
之前先驗證 plumbing(膨脹 + decay + 權重生效)正確。

誠實 caveat:medium 是在**看過其 capped 結果之後**才加入的,因此其納入決策並非盲的;仍屬真正預註冊的
是 native-P0 的結果本身。

*Source:S14 §12(§12.1 Q3、§12.2、§12.3、§12.4.4、§12.6)。*

### §3.4 Entropy-cap ρ —— 它是什麼、為何存在

**涉及的物件。** 對單一 gene *g*,Gen0 sampler 需要一個「該 gene 各候選值的抽樣機率」:

- `p0` = **baseline** 分布 —— 對該 gene 候選值均勻(這就是 Arm G 用的,即「沒有引導」)。
- `q` = **Formocast 偏好** —— 對 *trusted* 值取 softmax,`q ∝ exp(λ·(m_gv − min_v m_gv))`
(封存 `construct_gene_probabilities`)。`λ` 控制偏好多尖銳(λ=0 → 在 trusted 值上平坦;λ 越大 → 越
集中在最佳值)。此處 medium 與 large 的 `λ_s = 8`。
- `p1` = Arm F 實際抽樣所用的分布 —— 上述兩者的**混合**。
- `H_norm` = `p1` 的*正規化熵*:其 Shannon entropy 除以最大可能值(`log n`)。`H_norm = 1.0` 代表
完全均勻(最大多樣性);越小代表越集中。

**這個 floor 要解決的問題。** 把 Gen0 集中到模型偏好的值,有可能摧毀 GA 需要的探索多樣性。故封存協定
要求 `H_norm(p1) ≥ 0.80` —— 「guided Gen0 必須至少保有均勻分布 80% 的多樣性」。

**為何「原本的 binary 形式」失敗。** 舊 gate 問的是是非題:*在全強度(*`p1 = 0.2·p0 + 0.8·q`*)下,這個
gene 是否達到 0.80?* 若否,該 gene **整個被排除**(退回 p0)。這條規則反過來**恰好刪掉訊號最強的
gene** —— gene 資訊量越大 → 其 `q` 越集中 → 越可能過不了 floor。**完整的白話推導(什麼是可信值、0.6576 從哪來、為何一個 gene 就能停掉整條管線、`ρ` 在調什麼、為何不乾脆拿掉下限)見 §3.4a。** 更糟的是(見 §7.3),對低基數 gene 而言
`H_norm` 的上限只由 arity 決定,所以有些 gene **在任何 λ 下都永遠**達不到 0.80。

**修法(**`ENTROPY-CAP-20260810`**)—— 改成限制強度,而非丟掉 gene。** 引入 per-gene 混合強度 `ρ`:

```
p1_g = (1 − ρ_g)·p0  +  ρ_g·q_g(λ_s)
ρ_g  = max{ ρ ∈ [0, 0.80] : H_norm(p1_g) ≥ 0.80 }
```

- `ρ = 0` → `p1 = p0`(完全不引導);`ρ = 0.80` → `p1 = 0.2·p0 + 0.8·q`(**與舊的全強度混合完全相同**,
故原本就通過的 gene 不變)。
- 因為 `H_norm` 對 ρ **單調遞減**,可行集是區間 `[0, ρ*]`,`ρ_g` 以**決定性的由上而下網格掃描**求得
(步長 `0.80/4096 = 0.0001953125`,4097 個點)—— 可重現、不需 solver。
- 這是**套用到所有通過 gate (a)/(b)/(c) 之 gene 的通用規則** —— 不是為那兩個被救回的 gene 開特例,故
非 gate-shopping。未過 (a)/(b)/(c) 的 gene 仍退回 `p0`。

**medium 上的對照實例**(兩者皆 activated,取自封存的 derivation manifest):


| gene           | n_trusted | S_g   | 全強度下的 H_norm         | ρ_g            | 結果 H_norm(p1)    | 舊 binary gate    |
| -------------- | --------- | ----- | -------------------- | -------------- | ---------------- | ---------------- |
| **1LDSBuffer** | 2         | 0.113 | 1.0000(本來就沒問題)       | **0.80**(全強度)  | 0.9159           | PASS(不變)         |
| **DepthU**     | 2         | 0.142 | **0.6576**(低於 floor) | **0.566**(降強度) | **0.8001**(剛好達標) | **FAIL → 原本被排除** |


DepthU —— medium **最強**的 gene —— 原本被 binary 規則丟掉;cap 讓它以約 71% 的引導強度保留
(ρ 0.566 vs 0.80),同時剛好落在多樣性 floor 上。此時它與 baseline 的距離為 TV(p1,p0)=0.377、KL=0.358。

*來源:S14 §10.3、qa-09 §4.3a;*`derivation-manifest-capped.json`*(locked_constants、locked_formulas、
gate_definition.entropy_cap_amendment_ENTROPY_CAP_20260810、per_shape_activation_log)。*

### §3.4a 白話推導 —— 為什麼封存的 max-reducer 管線產不出東西

*(§3.4 與 §7.3 內容正確但太密。本節從第一原理重推同一結果,不提出任何新主張;每個數字都標註封存來源。)*

#### §3.4a.1 S11 想建的東西:每個 gene 一顆加權骰子

每個可調 gene 都有一串候選值。S11 的工作是看 Formocast 的預測延遲,把「哪些值看起來好」變成一顆
**加權骰子** —— 產生 Gen0 個體時,用它來抽該 gene 的值。Arm G 擲公平骰(`p0`,均勻),Arm F 擲加權骰(`p1`)。

#### §3.4a.2 這個抽樣到底在抽什麼、可信值是什麼意思

**哪個階段。** 這是 S11 的**條件抽樣**階段 —— 在任何分析之前,而且完全不動用 GPU。對每一組
(gene, 候選值) 開一條 **stream**,把**該 gene 釘死在該值**,其餘 29 個 gene 隨機抽,組成完整 config。
每個抽出的 config 必須**合格**:能被 KernelWriter build 出來,且能被 Formocast 評分。合格者稱為
「accept」;累積 **256** 個採計後該 stream 停止,或抽滿硬上限 **512 chunks × 512 nominal slots =
262,144 次**為止。

**抽出來的結果代表什麼。** 一條 stream 的 accept 數回答的是:*「把這個 gene 固定成這個值、其餘 29 個
隨機抽,我有多常拿到一個真的能 build 且能評分的 config?」* 它就是該值 marginal 的經驗證據基礎 ——
沒有 accept 就沒有東西可以平均,marginal 也就算不出來。

**每個值拿到的預算完全相同。** `[CODE AUDIT]` `s11-conditional-prefixes.json` 對**每一條** stream 都
記錄 `hard_cap_chunks = 512`、`nominal_slots_per_chunk = 512`、`complete_nominal_draws = 262144`、
`ledger_replay.event_count = 512`、`cap_complete = true`。*(欄位名已於 2026-08-13 更正:早期草稿引用的 `chunks_observed` 在該檔案中並不存在;實際記錄的對應欄位是 `ledger_replay.event_count` 與 `ledger_replay.per_stream_next_chunk.<stream>`,兩者皆為 512。)* 排程並不偏心 —— 差別在結果:

> **⚠ SOURCE GAP,2026-08-13 稽核發現。** **採計**那一欄可以逐格對照
> `s11-conditional-prefixes.json → streams[].credited_rows` 精確驗證(DepthU 256/256/38/0/0/0;
> PGR 256/256/2/0)。**「觀察到的 accept」**那一欄則不行:該欄位在所引 artifact 中被封頂在 256,
> 不可能給出 3,513 或 723,而這兩個數值在 `s11-registry.json`、各份 manifest 或
> `parallel-analyze/out/*` 中都找不到 —— 它們只出現在 `.pkl` payload 裡面。所以未封頂的 accept 計數
> 是 **`NOT_EVALUATED` as cited**:這些數字很可能是對的,但沒有任何被引用的 artifact 記錄它們。
> 請注意下面 `PrefetchGlobalRead` 那張表對同一個量誠實地寫成「≥256(達標)」—— 兩張表應該一致,
> 做法是引用 payload,或把兩張都下修為「≥256」。**倚賴這一欄的單調下降論證
> (3,513 → 723 → 38 → 0 → 0 → 0)也繼承了這個缺口**:它的後四個值已驗證,前兩個沒有。

| `DepthU` 值 | 262,144 次抽樣中觀察到的 accept | 採計 | 可信(support ≥ 128)? |
|---:|---:|---:|---|
| **32** | **3,513** ⚠ unsourced | 256(達標封頂) | ✓ |
| **64** | **723** ⚠ unsourced | 256(達標封頂) | ✓ |
| **128** | **38** | 38 | ✗ |
| **256** | **0** | 0 | ✗ |
| **512** | **0** | 0 | ✗ |
| **1024** | **0** | 0 | ✗ |

| `PrefetchGlobalRead` 值 | 觀察到的 accept | 採計 | 可信? |
|---:|---:|---:|---|
| **1** | ≥256(達標) | 256 | ✓ |
| **2** | ≥256(達標) | 256 | ✓ |
| **3** | **2** | 2 | ✗ |
| **4** | **0** | 0 | ✗ |

**那些 0 不是「沒抽到」,是「抽了 262,144 次、沒有任何一個存活」。** 這是完全不同的事實,而且是真正
重要的那個。

**而且這個模式是單調的,不是隨機的。** 兩個 gene 的 accept 數都隨值增大而單調下降:
`DepthU` 3,513 → 723 → 38 → 0 → 0 → 0;`PrefetchGlobalRead` 256+ → 256+ → 2 → 0。這是**聯合可行性**
約束的特徵,不是抽樣運氣。兩個 gene 都是靠消耗晶片上資源來換效能的 —— `DepthU` 是 unroll 深度
(每次主迴圈迭代消耗多少 K,決定 LDS tile 大小),`PrefetchGlobalRead` 是同時在途的 global load 數量
(消耗暫存器與 buffer)。設定越深,越多 MacroTile / MatrixInstruction 搭檔會超出硬體限制而 build 失敗。
到了 `DepthU ≥ 256`,整個空間裡幾乎**沒有任何**搭檔能存活。

*(資源壓力這個說法是與單調模式一致的機制性詮釋;封存產物只記錄計數、不記錄拒絕原因,故此處未經證明。)*
**用詞更正(經 review 後補)。** 封存 ledger `s11-conditional-prefixes.json` 只記錄
`disposition: "accepted"` 的列,所以「0 個 credited」嚴格來說是指*在 S11 條件抽樣的接受帳本下,
沒有任何帶該值的 config 被接受* —— 它**本身並不能**證明拒絕的原因是 KernelWriter build 失敗。
兩件事讓這個判讀維持誠實:計數隨值單調下降(3,513 → 723 → 38 → 0 → 0 → 0),這正是聯合可行性
約束的樣子;但 §7.2.1 在 large 上實測的 Gen0 有效率是 480–489(G)對 480–491(F),統計上無法區分,
這與「guided 臂把某個 gene 約 10–21% 的質量放在完全不能執行的值上」並不相容。(部分解釋:§7.2.1 是
*large*,那裡被封頂的 gene 是 `PrefetchGlobalRead` 而非 `DepthU`。)在拒絕原因被另外查明之前,
報告應說「沒有被接受的 config」,而不是「build 不出來」。

**於是「可信」是什麼意思。** 一個值要在加權骰上占位,必須通過 `support ≥ 128` 個 accept,外加
可執行 / coverage ≥ 0.95 / 無 collision(§5a)。所以 `DepthU` 只留下 **6 個中的 2 個**、
`PrefetchGlobalRead` 留下 **4 個中的 2 個** —— 其餘沒有可用證據。`1LDSBuffer`(2 個值,256 / 256)
兩個都留下,這正是它能以全強度通過的原因(§3.4)。

這就是「六面骰只有兩面有證據支撐」的字面意思。而且它讓 §3.4a.3 的問題更尖銳:多樣性下限接下來會
要求這顆骰子**在全部六面上都顯得分散** —— 包括三個「經驗上一個 accept 都拿不到」的面。

#### §3.4a.3 多樣性下限,以及為何這些 gene 永遠過不了

封存規則是 `H_norm(p1) ≥ 0.80` —— 加權骰的分散程度至少要有公平骰的 80%(§3.4)。現在算算
`DepthU` 實際能達到多少。封存路徑把混合比例固定在全強度(`p1 = 0.2·p0 + 0.8·q`),只讓 `λ` 變動。
最分散的情況是 `λ = 0`,此時 `q` 在兩個可信值上是平的:

```
p0 = 6 個值各 1/6
q  = 2 個可信值各 1/2,4 個不可信值為 0

p1 = 0.2·p0 + 0.8·q
   = 0.0333  於 4 個不可信值   (只有 baseline 質量)
   = 0.4333  於 2 個可信值     (baseline + guided 質量)

H_norm = H(p1) / ln 6 = 0.6576
```

**0.6576 < 0.80。** 而這已經是**最分散**的設定 —— 其他任何 `λ` 只會更集中。封存診斷獨立佐證了這點:
`max_entropy_over_grid = 0.6575889744675268`、`argmax_lambda = 0.00`、`passes_floor_at_any_lambda = false`
(`parallel-analyze/out/diag-lambda2.w72.json`)。`PrefetchGlobalRead`(4 值 / 2 可信)上限為
`0.7345`,同樣在任何 `λ` 下都低於下限。

所以這兩個 gene 過不了下限**不是因為證據薄弱** —— 它們的敏感度餘裕是所有 gene 中最寬的
(§7.3.1 第 3 點:超出 `S_g` 下限 +88% 與 +7.4%,每個隨機 gate 都以 1.79×–11.86× 通過) ——
而是因為**它們被抽到的值太少,任何合法的骰子都不可能顯得分散**。

#### §3.4a.4 為何一個 gene 失敗會讓整條管線停擺

這一步把「單一 gene 的問題」變成「全面停止」:**`λ` 是全域的**。所有 guided gene **共用一個** `λ`,
而封存規則要求在那個共用 `λ` 之下,每一個 guided gene 都必須通過下限。

比喻:一個委員會只有一個共用的「激進程度」旋鈕,每位成員都必須低於同一條安全線。現在有兩位成員
**即使旋鈕轉到 0 都超標**。於是**沒有任何旋鈕位置能同時滿足所有人** —— 可行集合是空的。

負責挑選那個旋鈕位置的函式就是 `select_global_lambda`(封存 `s11/guidance.py:95`)。它發現可行集合
為空,於是 assert。`[CODE AUDIT]` 診斷記錄 `status = "ASSERTION at call #1"` —— 第一次呼叫就失敗。

其餘是機械性的連鎖:

```
analyze  --assert-->  s11-analysis.json 從未被寫出
                       └-> decide     無法執行(輸入不存在)
                            └-> reproduce 無法執行
```

因此三個 closeout artifact 是 **NOT_PRODUCIBLE,而非待產出**(§7 表、§7.3)。這也是序列版 `analyze`
在 2026-08-12 跑了 14 小時 31 分後被停止的原因:它是以約 330 倍的成本,重新導出一個經驗證的平行
重製已在 156.7 秒內確立的結果 —— 而且它再跑多久都會撞上同一個 assert。

#### §3.4a.5 「那為什麼不乾脆讓 max-reducer 版先不管 entropy 就好?」

很自然的疑問,有三個各自獨立的答案 —— 第一個單獨就已足夠。

**(1) 治理:那個下限是封存常數。** 0.80 這個值位於封存的 S11 管線內部。改它就是改封存碼,而本研究
禁止這麼做。更重要的是,這樣做會摧毀那次 run 的意義:封存路徑的存在**就是為了成為「如註冊般」的
產物**。被 patch 過的管線就不再是 as-sealed 的 S11,而是一個全新、未註冊的變體,它的輸出在任何
誠實的解讀下都不能被標為「S11 closeout」。依治理原則,該 assertion 是**回報而非修補**,封存樹未被
觸碰(§7.3)。

**(2) 科學:拿掉下限不是免費的。** 那個下限不是官僚累贅 —— 它保護 Gen0 的探索多樣性。
(順帶一提,在本案中該下限的要求**原則上也無法被滿足**:§3.4a.2 顯示 `DepthU` 六個值中有三個在各自
262,144 次抽樣中產出零個被接受的 config,所以要求骰子把質量攤到
全部六面,等於要求它押注在抽樣語料拿不到證據的值上。拿掉下限仍然是錯的修法,但值得記錄:該下限
當時要求的是這批資料無法提供的東西。)刪掉它會讓
`DepthU` 的 prior 把 80% 的質量壓在 6 個值中的 2 個上,而沒有任何東西攔著。§7.2.1 顯示這個風險
**真實且已被量到**:在 large 上,即使是**已封頂**的 prior 也讓 Gen0 中心變好(4/5 seed)、卻讓
Gen0 極值變差(1/5 seed),而 GA selection 讀的正是極值。「先不管 entropy」不是一個中性的改動,
它是另一個實驗,而且方向正是資料已標示為有害的那一邊。

**(3) 沒有必要 —— 答案在不 patch 任何東西的情況下就拿到了。** per-shape 導出
(`ENTROPY-CAP-20260810`)在**保留** 0.80 下限的前提下,讓兩個 gene 都得到 guidance,做法是改變
「調整什麼」而不是改變「要求什麼」。所以從來不需要在「尊重封存下限」與「guide 強訊號 gene」之間
二選一。

可移轉的教訓(§7.3.1 第 4 點)不是「下限錯了」,而是「**固定下限混淆了兩件不同的事**」:
*保持多樣性* 與 *有足夠的已抽樣候選值*。有原則的修法是把下限改成**相對於各 gene 可達到的最大值**,
或**封頂強度而非排除 gene**。

#### §3.4a.6 `ρ` 到底在調什麼

`ρ` 是**公平骰與加權骰之間的混合權重**,僅此而已。它不改變資料、不改變敏感度、不改變哪些值可信、
也不改變 0.80 下限。

```
p1 = (1 − ρ)·p0  +  ρ·q          p0 = 公平骰(均勻)
                                  q  = Formocast 對可信值的偏好
ρ = 0     ->  p1 = p0            完全不 guide(與 Arm G 相同)
ρ = 0.80  ->  p1 = 0.2·p0 + 0.8·q   封存的全強度(舊二元規則所測試的)
```

兩套規則的差別只在**允許什麼變動**:

| | 封存 / 二元規則 | `ENTROPY-CAP-20260810` |
|---|---|---|
| 混合權重 | **固定為 0.80** | **可搜尋,`ρ ∈ [0, 0.80]`** |
| `λ`(`q` 的尖銳度) | 可搜尋,但**全域共用** | 固定 `λ_s = 8`,**逐 shape** |
| 低於下限的 gene | **整個排除**(退回 `p0`) | **保留,降低強度** |
| 某個 gene 不可行 | **整條管線 assert** | 只是該 gene 的 `ρ` 較小 |

因為 `p0` 是均勻的(`H_norm = 1.0`),而 `H_norm(p1)` 對 `ρ` **單調遞減**,把 `ρ` 調小永遠會把 `p1`
拉回最大多樣性。所以可行的 `ρ` 一定存在 —— 最差就是 `ρ = 0`。規則取的是**仍能通過下限的最大** `ρ`,
以確定性的向下網格掃描找出(步長 `0.80/4096`,4097 個點 —— 可重現、不需 solver)。

**實測結果 —— 讓封存路徑不可能的那兩個 gene,此刻正在 S14 中被 guide**
(`derivation-manifest-capped.json` → `per_shape_activation_log`):

| gene / shape | 封存全強度下的 `H_norm` | 封存判定 | `ρ_g` | 結果 `H_norm(p1)` | per-shape 判定 |
|---|---:|---|---:|---:|---|
| `DepthU` / medium | **0.6576** | 排除 | **0.566** | **0.8001** | **啟用** |
| `PrefetchGlobalRead` / large | **0.7345** | 排除 | **0.586** | **0.8001** | **啟用** |

注意 `H_norm` 那一欄:`0.6575889744675268` 與 `0.7344977967946407`,與封存診斷的數值
**到小數第七位完全相同**。兩條獨立的程式路徑落在同一組數字上,是「上述結構性解釋確為實際機制、
而非一個聽起來合理的故事」的最強佐證。

兩者都落在 `0.8001` —— 剛好在下限之上 —— 因為規則就是在通過下限的前提下最大化 `ρ`。
同一個 gene、同一批資料、同一條 0.80 下限:封存規則把它丟掉,修正後的規則以約 57–59% 的強度 guide 它。

#### §3.4a.7 為何 per-shape 不存在共用 `λ` 的死結

兩個各自獨立的理由,任一個單獨成立即可:

- **逐 gene 的強度。** 每個 gene 有自己的 `ρ_g`。`DepthU` 不再需要與其他所有 gene 同時被滿足 ——
  它把自己的旋鈕調小直到通過為止,其他 gene 不受影響。
- **不存在全域可行性要求。** `λ_s` 是逐 shape 固定的,不是去搜尋一個必須同時對所有 gene 成立的值,
  所以根本沒有一個「可能為空」的共用可行集合。

§3.4a.4 的阻塞條件從來不是資料的問題。它是「要求單一共用參數同時滿足每個 gene」所製造出來的
**耦合**。移除該耦合就移除死結,而且不削弱多樣性保證 —— 每個啟用的 gene 仍然滿足
`H_norm(p1) ≥ 0.80`。

#### §3.4a.8 值得寫進報告的反諷

被封存規則丟掉的 gene,系統性地正是**帶有最多訊號的那些**。因果鏈很短,而且只有一個方向:

```
模型訊號越強  ->  偏好 q 越尖銳  ->  entropy 越低  ->  越可能過不了固定下限
```

`DepthU` 是 medium 的首要 gene(`S_g = 0.142`);`PrefetchGlobalRead` 是 large 的(`S_g = 0.192`)。
兩者都被排除。所以二元下限的實際效果不是「濾掉雜訊」,而是**「系統性地丟棄最有資訊量的 gene」** ——
而且因為 `λ` 是共用的,單單一個這樣的 gene 就足以讓整條管線停止。

同一批資料裡還看得到第二個、相互加乘的缺陷。下限是對 gene 的**完整 arity** 計算的
(`H_norm = H(p1)/ln n`,`DepthU` 的 `n = 6`),但 guided 質量永遠只能落在**可信值**上(`k = 2`)。
§3.4a.2 顯示那些不可信值之所以不可信,是因為其中三個**各自在 262,144 次抽樣中產出零個被接受的
config**(第四個 `DepthU=128` 只抽到 38 個)—— 它們不只是觀測不足,而是看起來聯合不可行。於是分母 `ln n` 把抽樣
無法實現的候選值也算了進去,下限實際上是在懲罰一個 gene「沒能把機率攤到拿不到證據的值上」。把下限改成相對於各 gene
**可達到**的最大值(§7.3.1 第 4 點修法 (i)),可以同時消除第二個與第一個缺陷。

這是關於協定的設計發現,不是實驗失敗,而且在兩個不同的 reducer 上獨立重現(§7.3.1 第 5 點)。

*Source:`[CODE AUDIT]` `s11-conditional-prefixes.json` `streams[].credited_rows`(逐值 support);
`parallel-analyze/out/diag-lambda2.w72.json`(`max_entropy_over_grid`、`argmax_lambda`、
`passes_floor_at_any_lambda`、`structural_sup_over_all_baselines_and_lambda`、`status`);
封存 `s11/guidance.py:95`(`select_global_lambda`);`derivation-manifest-capped.json`
`per_shape_activation_log`(`rho`、`entropy_at_lambda0`、`normalized_entropy_p1`);§3.4、§5a、§7.2.1、§7.3。*

#### §3.4a.9 那條 0.80 的線實際上量的是什麼 —— 而它量的不是「集中程度」

這條下限的說法是「讓 guided Gen0 至少保有均勻分布 80% 的分散度」。但資料顯示它量的不是這個。三個
gene **被施加完全相同的 guidance 強度**(封存的全強度混合 `0.2·p0 + 0.8·q`),判定結果卻天差地別:

| gene | 候選值 `n` | 可信值 `k` | 可達到的 `H_norm` | 對照 0.80 這條線 |
|---|---:|---:|---:|---|
| `1LDSBuffer` | 2 | 2 | **1.0000** | 輕鬆通過 |
| `PrefetchGlobalRead` | 4 | 2 | **0.7345** | **任何 λ 都不可達** |
| `DepthU` | 6 | 2 | **0.6576** | **任何 λ 都不可達** |

同樣的處理強度,相反的結果。差別完全來自 `k/n`。所以這道 gate 擋掉的不是「壓得太集中的 prior」,
而是**「候選值多、但只有兩個抽得到足夠證據的 gene」** —— 那是抽樣結果的性質,不是所施加 guidance 的性質。

封存診斷還區分了兩種不同性質的失敗,這本身就說明這條線不是一個乾淨的判準:

- `DepthU` —— `structurally_impossible: true`。它跨**所有**嚴格正的 baseline 與所有 λ 的上界是
  `0.7435`,仍低於 0.80。換任何 baseline 都救不回來。
- `PrefetchGlobalRead` —— `structurally_impossible: false`。它跨所有 baseline 的上界是 `0.8610`,
  **高於** 0.80。它之所以不可達,**只是因為封存選了均勻 baseline**。

兩個 gene 敗在同一條線上,原因性質卻不同:一個是算術,一個是特定建模選擇的後果。

再結合 §3.4a.2,這個要求比表面上更嚴苛。`DepthU` 的分母是 `ln 6`,但那六個值中有三個
**各自在 262,144 次抽樣中產出零個被接受的 config**。所以這條線要求骰子把機率攤到抽樣無法實現的
候選值上,然後因為它做不到而懲罰它。§7.3.1 第 4 點的兩種修法 —— 把下限改成**相對於各 gene 可達到的
最大值**,或**封頂強度而非排除** —— 都能消除這點,因為兩者都不再在「`n` 個值中只有 `k` 個可達」時
仍拿 `ln n` 當基準。

### §3.4b S11 的分數如何變成 Ductile 實際抽樣所用的權重

*(端到端的 treatment 路徑。這是報告必須交代的「treatment 究竟如何實際進入 GA」那條鏈;每一步都是
`derivation-manifest-capped.json` → `locked_formulas` / `locked_constants` 中的 locked 公式,
最後一步已對出貨檔案逐項驗證於下。)*

#### §3.4b.1 五個步驟

```
s11-native-scores.json                     30,490 筆 Formocast 預測延遲
      │  (1) per-size benefit
      ▼   b_{c,s} = 1 − midECDF_s(predicted_latency)          是排名,不是絕對延遲
      │  (2) 逐 (gene, value) 的 shrinkage marginal
      ▼   m_{g,s,v} = (Σb + α·global_mean_s)/(n + α),  α = 32
      │  (3) 只在「可信值」上做 softmax
      ▼   q = normalize( exp( λ_s·(m − min m) ) ),  λ_s = 8
      │  (4) entropy 封頂混合                                  [ENTROPY-CAP-20260810]
      ▼   p1 = (1 − ρ_g)·p0 + ρ_g·q,   ρ_g = max{ρ ≤ 0.80 : H_norm(p1) ≥ 0.80}
      │  (5) 反解 Ductile 的權重轉換
      ▼
ga-weights-{shape}.json                    Arm F 注入 GA config 的東西
```

步驟 (1)–(3) 是封存的 S11 程式碼;(4) 是修正案;**(5) 是最容易做錯的一步,也是報告不能略過的一步。**

#### §3.4b.2 步驟 5 —— Ductile 的 `weights` 不是機率,而且轉換是反向的

`[CODE AUDIT]` `ga.py:145–146`:

```python
w = np.exp(-weight_beta * (w - w.min()))     # weight_beta = 0.25
self.probs[k] = w / w.sum()
```

兩個後果:

- **符號是負的。** 權重**越低**,抽樣機率**越高**。這個欄位帶的是 cost 語意,不是偏好語意。
  若把 `p1` 直接寫進去,guidance 會整個顛倒 —— 模型最看好的值會變成最不可能被抽到的。
- **因此導出端必須反解這個轉換**,產生一組權重 `w`,使得 Ductile 自己的
  `exp(−0.25·(w − min w))` 正規化後恰好還原出預期的 `p1`。在 `− w.min()` 會抵銷的加法常數之下,
  也就是 `w ∝ −4·ln(p1)`。

封存導出對每個 gene 都明確記錄了這個 round-trip —— `per_shape_activation_log` 中的
`roundtrip_p0_pass`、`roundtrip_p1_pass`、`roundtrip_p0_max_abs_error`、`roundtrip_p1_max_abs_error`。

#### §3.4b.3 對出貨檔案的端到端驗證

`[CODE AUDIT]` 直接取 `out-capped/ga-weights-medium.json` 現況,重放 Ductile 自己的轉換:

| gene | 檔案中的權重 | ⇒ Ductile 的抽樣機率 |
|---|---|---|
| `DepthU`(6 值) | `[6.251, 2.764, 10.506, 10.506, 10.506, 10.506]` | `[0.2096, 0.5011, 0.0723, 0.0723, 0.0723, 0.0723]` |
| `1LDSBuffer`(2) | `[1.608, 4.423]` | `[0.6690, 0.3310]` |
| `WaveSeparateGlobalReadA`(2,**未啟用**) | `[2.773, 2.773]` | `[0.5000, 0.5000]` |

三項獨立檢查全部通過:

- **不可信值拿到的質量剛好是 baseline 份額。** `DepthU` 的四個不可信值各得 `0.0723`,而
  `(1 − ρ)·p0 = (1 − 0.566015625)/6 = 0.0723`。步驟 (4) 的混合被出貨權重完全還原。
- **entropy 恰好落在下限上。** `H(p1)/ln 6 = 0.8000`,對照 manifest 記錄的
  `normalized_entropy_p1 = 0.800125` —— 封頂確實做到它宣稱的事,而且在 GA 真正消費的那個 artifact 裡
  就看得見。
- **未啟用的 gene 解出來是均勻的。** `WaveSeparateGlobalReadA` 恰為 `[0.5, 0.5]`,與 Arm G 相同。
  這證實 treatment 確實只作用在啟用的 gene 上;其餘每個 free gene 在兩臂中的抽樣方式完全一樣。

反解步驟 (5) 還能還原出 guided 偏好本身:`DepthU` 在 `{32, 64}` 上的 `q ≈ [0.243, 0.757]` ——
模型偏好 `DepthU=64` 約 3:1;經過 `ρ = 0.566` 封頂後變成 0.5011 對 0.2096 的抽取機率,
而仍有 28.9% 的質量被多樣性下限保留在那四個無證據值上。

#### §3.4b.4 這對解讀實驗的意義

- Arm G 與 Arm F 之間**唯一**的差異就是 backend config 裡的 `weights` 清單。其餘一切 —— seed、pin、
  `group_0`、評估方式、早停 —— 完全相同。
- 由於未啟用的 gene 解出來是均勻分布,medium 上的 treatment 是一個作用在 **29 個 free gene 中 2 個**
  上的 prior,large 上是 **5 個**。這就是介入的具體規模,任何 null 結果旁邊都值得直白寫出
  (§7.1/§7.2):null 是「**在這種規模的 prior 之下**」的 null。
- `group_0` 權重在兩臂的 config 中都存在,且彼此逐位元相同 —— 它們是 GEKO 權重,不是 treatment(§3.7)。

*Source:`[CODE AUDIT]` `algorithm/ga.py:145–146`(權重→機率轉換,`weight_beta = 0.25`);
`derivation-manifest-capped.json` `locked_formulas`(`per_size_benefit`、`shrinkage_marginal`、
`softmax_q`、`p1_mix_capped`)、`locked_constants`(`alpha = 32`、`lambda`、`rho_max = 0.80`、
`rho_step = 0.0001953125`、`entropy_floor = 0.80`)、`per_shape_activation_log`(`rho`、roundtrip 檢查);
`out-capped/ga-weights-medium.json`(`weight_beta`、`weights`、`rho_per_gene`、`note`);§3.4、§3.4a、§5a。*

### §3.4c entropy 下限的稽核 —— 它在流程的哪個位置、0.80 從哪來、以及它對 S14 做了什麼

*(回答報告一定會被問到的三件事:0.80 有沒有依據;這個機制有沒有做到它宣稱的事;以及這些是否折損了
S14 的結果。)*

#### §3.4c.1 這條線在流程的位置 —— 它是護欄,不是篩選器

```
挑 gene:      S_g ≥ 0.05  且  ≥2 個可信值               <- 這是「選擇」的判準
                        │
建 prior:     q = 在可信值上做 softmax(λ_s = 8)          <- 這是「內容」
                        │
安全檢查:     H_norm(p1) ≥ 0.80                          <- entropy 下限在這裡
```

這條下限**不參與**「哪些 gene 有訊號」的判斷,也**不參與**「gene 的哪個值比較好」的判斷。它在之後才執行,
只問一句:*這個 prior 會不會太窄?* 因此它出錯**不可能讓錯的 gene 被選中,也不可能把偏好的方向弄反** ——
它只能改變一個既已選定的偏好**被施加得多強**(per-shape 路徑),或**是否被施加**(封存的二元路徑)。

#### §3.4c.2 0.80 從哪來:沒有任何地方記錄

`[CODE AUDIT]` 全樹搜尋找不到 0.80 的**任何推導、noise model、power analysis 或參考來源**。它在 S11
design 中只以一句要求出現(*「entropy `>=0.80`」*),並在封存碼中被硬釘死 —— 該函式甚至**拒絕接受
其他數值**:

```python
# protocol/v1/s11/guidance.py:78-83
def select_global_lambda(gene_inputs, *, entropy_min: float = 0.80):
    if not gene_inputs or entropy_min != 0.80:
        raise GuidanceError("global lambda requires guided genes and entropy floor 0.80")
```

所以 0.80 與 §3.2a 的 `×1.15` Gen0 膨脹屬於同一類:**未記錄的 magic constant**。報告中值得與 §5a 已標註
的 `S_g ≥ 0.05` heuristic 並列陳述 —— **這條管線的三個門檻中有兩個是無依據的常數**。
(第三個 `support ≥ 128` 至少有「證據筆數」這個明確意義。)

另外,這種釘死也強化了 §3.4a.5 第 (1) 點:即使想換一個下限,也等於要改封存碼,因為封存函式拒絕其他引數。

#### §3.4c.3 這個機制有做到它宣稱的事嗎?沒有

它宣稱限制集中程度,實際限制的是 `k/n`。在**相同**的 guidance 強度(封存的全強度混合)之下,
判定完全由「這個 gene 有幾個值拿得到證據」決定:

| gene | `n` | 可信 `k` | `k/n` | 可達到的 `H_norm` | 對 0.80 的判定 |
|---|---:|---:|---:|---:|---|
| `1LDSBuffer` | 2 | 2 | 1.00 | 1.0000 | 輕鬆通過 |
| `PrefetchGlobalRead` | 4 | 2 | 0.50 | 0.7345 | 任何 λ 都不可達 |
| `DepthU` | 6 | 2 | 0.33 | 0.6576 | 任何 λ 都不可達 |

另有兩點讓問題更明確:

- **兩個失敗甚至不是同一種失敗。** `DepthU` 是 `structurally_impossible: true`
  (跨**所有** baseline 的上界 = 0.7435 < 0.80);`PrefetchGlobalRead` 是 `false`(上界 0.8610 > 0.80,
  所以它只是被封存選的**均勻** baseline 擋住)。同一條線,兩種不同的底層原因 —— 這正說明它不是一個
  乾淨的判準。
- **分母把硬體拒絕的值也算了進去。** `DepthU` 的 `ln 6` 包含三個**各自在 262,144 次抽樣中產出零個
  被接受 config** 的值,以及第四個只有 38 個的 `DepthU=128`(§3.4a.2)。這條下限是在要求 prior 把機率
  攤到語料幾乎沒有證據的值上。

#### §3.4c.4 這對 S14 結果造成什麼 —— 以及不會造成什麼

**它不可能讓實驗選出錯的 champion。** 這條下限只塑造 Gen0 的**抽樣分布**,也就是哪些候選會被試到。
champion 是由 **GPU 實測吞吐量**選出的,之後再做 7× 交錯重測(§5)。被扭曲的 prior 會損失搜尋效率,
**不可能讓較慢的 config 勝過較快的**。

**它真正做的,是恰好在模型最有把握的地方削弱了 treatment。** Lock B 實際出貨的逐 gene 強度:

| shape | gene | `S_g` | 可信 `k` | `ρ_g` | 相對滿強度 |
|---|---|---:|---:|---:|---:|
| large | **PrefetchGlobalRead** | **0.192** *(large 最強)* | 2 | **0.586** | **73 %** |
| large | UnrollLoopSwapGlobalReadOrder | 0.165 | 2 | 0.800 | 100 % |
| medium | **DepthU** | **0.142** *(medium 最強)* | 2 | **0.566** | **71 %** |
| medium | 1LDSBuffer | 0.113 | 2 | 0.800 | 100 % |
| large | GlobalReadVectorWidthB | 0.058 | 4 | 0.800 | 100 % |
| large | TransposeLDS | 0.057 | 4 | 0.800 | 100 % |
| large | GlobalReadVectorWidthA | 0.052 | 4 | 0.800 | 100 % |

**被削弱的兩個,恰好是各 shape 上敏感度最高的那一個;五個較弱的 gene 全部滿強度。** 機制不是
「因為強所以被罰」,而是共同成因:`k/n` 低是因為該 gene 的深層設定聯合不可行(§3.4a.2),
而深層設定會耗盡晶片資源的 gene,正是對效能影響最大的 gene。低 `k/n` 與高 `S_g` 同源:
這個 gene 掌管的是資源與效能的取捨。

**對 claim 措辭的影響。** medium 或 large 上的 null,是「**在一個對該 shape 最強 gene 只施加約
71–73% 強度、對最弱 gene 卻施加 100% 的 prior 之下**」的 null。這是真實的解讀限制,必須寫在
§7.1/§7.2 旁邊:

> 可以說:「這個修正後的稀疏 prior,在當前配置下,未達到預註冊的方向性門檻」
>
> **不可以說**:「模型的 guidance 沒有幫助」—— 現有最強的 guidance 是被一個無記錄依據的常數
> 降低強度後才施加的。

#### §3.4c.5 per-shape 如何在同一條 0.80 之下運作 —— 以及結果如何

per-shape 路徑**沒有放寬**下限。它改的是*什麼東西可以調*:

| | 封存 / 二元 | per-shape(`ENTROPY-CAP-20260810`) |
|---|---|---|
| 混合權重 | 固定 0.80 | **逐 gene 搜尋**,`ρ_g ∈ [0, 0.80]` |
| `λ` | 可搜尋,但**所有 gene 共用一個值** | 固定 `λ_s = 8`,逐 shape |
| 下限 | `H_norm ≥ 0.80` | `H_norm ≥ 0.80` **(完全相同)** |
| 低於下限的 gene | 整個排除 | 以較小的 `ρ_g` 保留 |
| 某個 gene 不可行 | **整條管線 assert** | 只是該 gene 的 `ρ_g` 較小 |

`ρ_g` 以確定性的向下網格掃描找出(步長 `0.80/4096 = 0.0001953125`,4097 點),取**仍能通過下限的
最大** `ρ` —— 所以每個啟用的 gene 依建構必然落在 `H_norm = 0.8001` 或剛好之上。

以同一批讓封存路徑當場停止的資料,結果是:

- **7 個 gene 啟用**(medium 2、large 5),而不是整條管線 assert;
- **2 個降強度、5 個滿強度**(表見 §3.4c.4);
- 多樣性保證**未改變** —— 每個啟用的 gene 仍滿足 `H_norm(p1) ≥ 0.80`;
- `DepthU` 與 `PrefetchGlobalRead`,也就是讓封存路徑不可行的那兩個 gene,都得到了 guidance。

所以這個修正案並沒有拿多樣性換覆蓋率。它移除的是一個**耦合** —— 「單一共用參數必須同時滿足每個
gene」的要求 —— 而那才是死結的真正成因(§3.4a.7)。

*Source:`[CODE AUDIT]` `protocol/v1/s11/guidance.py:78–83`(下限硬釘死、拒絕其他數值);
S11 design(僅有 `entropy>=0.80` 的要求,無推導);`parallel-analyze/out/diag-lambda2.w72.json`
(`max_entropy_over_grid`、`structural_sup_over_all_baselines_and_lambda`、`structurally_impossible`);
`derivation-manifest-capped.json` `per_shape_activation_log`(`sensitivity`、`rho`、`n_trusted`)、
`locked_constants`(`rho_max`、`rho_step`、`rho_grid_points`、`entropy_floor`);§3.4、§3.4a、§3.4b、§5a。*

#### §3.4c.6 給那兩個未記錄常數一個可解釋的意義

`S_g ≥ 0.05` 與 `H_norm ≥ 0.80` 都沒有推導(§3.4c.2、§5a)。但這不代表無法在報告中交代 ——
兩者都能被賦予意義,其中一個還能給出經驗上的辯護。

**`S_g ≥ 0.05` —— 它落在觀測資料的自然斷層裡。** `S_g` 是一個 gene 的最佳值與最差值之間、
以 population rank-percentile 計的差距。把所有可測 gene 的 `S_g` 排序:

| shape | 最大的**未通過** `S_g` | 最小的**通過** `S_g` | 空隙 |
|---|---:|---:|---:|
| medium | 0.0422 | 0.1127 | **0.0705** |
| large | 0.0289 | 0.0520 | **0.0231** |

**門檻只要落在 (0.0422, 0.0520] 之間,兩個 shape 選出的 gene 完全相同。** 0.05 正在這個區間內。
所以這個常數雖然沒有記錄依據,但在這批資料上**結果對它明顯不敏感** —— 觀測到的敏感度是雙峰的
(平坦群 ≤ 0.042、訊號群 ≥ 0.052),不是一條被門檻任意切開的連續分布。這是**事後的穩健性檢核,
不是原始依據**,必須如此標註。

**`H_norm ≥ 0.80` —— 它的意思是「至少保留 `n^0.8` 個有效選項」。** normalized entropy 不好直讀,
但 `exp(H)` 是 *perplexity*:一個分布「實質上」攤在幾個選項上。由於 `H_norm = H / ln n`:

> `H_norm ≥ 0.80`  ⟺  `perplexity ≥ n^0.8`  ⟺  **加權後的 prior 必須維持得像「均勻分布在該 gene
> `n` 個值中的 `n^0.8` 個」那樣分散。**

| gene | `n` | 下限要求 | 該 gene 最多能提供 | 判定 |
|---|---:|---:|---:|---|
| `DepthU` | 6 | **4.19** 個有效選項 | 3.25 | 不通過 |
| `PrefetchGlobalRead` | 4 | **3.03** | 2.77 | 不通過 |
| `1LDSBuffer` | 2 | **1.74** | 2.00 | 通過 |

這讓失敗一眼可讀:`DepthU` 只有 2 個值有證據,無論偏好施加得多輕,都湊不出 4.19 個有效選項。
(這些上限是實測的 `max_entropy_over_grid`,不是 `(n, k)` 的封閉式函數 —— 不可信值仍保有 baseline
質量,所以簡單的 `k/n` 公式預測不了它們。)

#### §3.4c.7 「削弱」對 Gen0 具體做了什麼

`ρ` 是抽樣分布中取自模型意見的比例,其餘來自均勻分布。以 medium 上的 `DepthU` 為例
(模型偏好 64 勝過 32,約 3:1):

| | `ρ = 0.80`(滿強度,二元規則所測的) | `ρ = 0.566`(實際出貨) |
|---|---:|---:|
| P(`DepthU=64`)—— 模型首選 | **0.6393** | **0.5011** |
| P(`DepthU=32`) | 0.2273 | 0.2096 |
| 四個無證據值(各) | 0.0333 | **0.0723** |
| 有效選項數(perplexity) | 2.93 / 6 | 4.19 / 6 |
| `H_norm` | 0.6007 | **0.8001** |

換成個體數而非機率來讀 —— **512 個 Gen0 個體中,滿強度下約 327 個會帶著模型首選值,實際出貨則是
約 257 個:少了約 71 個。** 同時,被交還給那四個無證據值的機率從 13.3% 上升到 28.9% —— 其中三個是
**零**個 accept,一個(`DepthU=128`)只有 38 個,低於 `support ≥ 128` 門檻。

所以「削弱」不是比喻,而是實實在在的:**更少的 Gen0 個體帶著模型評價最高的組態,更多的個體帶著
抽樣語料幾乎或完全沒有證據的值。**

#### §3.4c.8 兩個旋鈕 —— 為何「什麼可以調」就是全部差異

只有兩個量在控制最終 Gen0 分布有多集中:

```
旋鈕 A — λ:模型自己的意見 q 有多尖銳
             λ 小 -> 「64 和 32 差不多」        λ 大 -> 「非 64 不可」

旋鈕 B — ρ:這個意見用多大音量播放
             ρ 小 -> 幾乎聽不見(≈ 均勻)       ρ 大 -> 幾乎完全照模型走
```

封存規則與修正案的差別,**只在於哪個旋鈕能轉、以及誰擁有它**:

| | 封存 / 二元 | per-shape(`ENTROPY-CAP-20260810`) |
|---|---|---|
| 旋鈕 A(`λ`) | 可轉,但**所有 gene 共用一個設定** | 固定在 8 |
| 旋鈕 B(`ρ`) | **焊死在 0.80** | **可轉,每個 gene 各有一個** |
| 安全線 | `H_norm ≥ 0.80` | `H_norm ≥ 0.80`(**完全相同**) |

**封存規則為何死結。** 音量鈕焊死在 80%,唯一的補救是把意見鈍化 —— 而那個刻度盤是全體共用的。
即使 `λ = 0`(「64 和 32 一樣好」),80% 的音量仍把 `DepthU` 的六個選項壓成 3.25 個有效選項,
低於要求的 4.19。**共用刻度盤上沒有任何一格對它是合格的。** 而因為刻度共用,一個成員不合格就等於
**沒有任何設定能滿足全體** —— 主持人挑不出值,會議只能取消(`select_global_lambda` assert,§3.4a.4)。

**修正案為何不會。** 把尖銳度對全體固定,改成每個 gene 各有自己的音量鈕。`DepthU` 把自己的
轉到 56.6%,剛好落在線上(`H_norm = 0.8001`,4.19 個有效選項)。其他人完全不受影響 ——
`1LDSBuffer` 維持 80%。

同一批資料、同一條安全線,結果相反:封存路徑**整條停止**;per-shape 路徑**啟用全部 7 個 gene**
(2 個降音量、5 個滿音量)。修正案沒有放寬任何安全要求,它移除的是**耦合** ——
「單一共用參數必須同時滿足每個 gene」這個要求 —— 而那才是死結的成因,不是下限本身。

*Source:`[CODE AUDIT]` `derivation-manifest-capped.json` `per_shape_activation_log`(逐 gene 的
`sensitivity`、`rho`、`n_trusted`);`parallel-analyze/out/diag-lambda2.w72.json`
(`max_entropy_over_grid`);`out-capped/ga-weights-medium.json`(出貨權重,反解見 §3.4b.3);
`protocol/v1/s11/guidance.py:78–83`;§3.4、§3.4a、§3.4b、§5a。*

### §3.5 稀疏性發現(model-only headline)— gene-selection 漏斗

在 **27 個 free gene**(30 個 search-space key 減去三個 GEKO group group_0/1/2;group_0 為 GEKO 加權、
在 Formocast treatment 之外)中,每個 shape 可引導的數量是 **tiny 0 / medium 2 / large 5**:

- medium 啟用 {DepthU(S_g=0.142, ρ=0.566)、1LDSBuffer(S_g=0.113, ρ=0.80)};
- large 啟用 {PrefetchGlobalRead、TransposeLDS、UnrollLoopSwapGlobalReadOrder、GlobalReadVectorWidthA、
GlobalReadVectorWidthB};
- tiny 全不啟用(模型對 8×8 回傳哨兵值 9,999,999.9 → 所有 S_g≈0)。

淘汰(為何 27 → 剩一小把),取自封存的 per-gene log(`derivation-manifest-capped.json` →
`per_shape_activation_log`):


| 淘汰原因                         | tiny  | medium | large |
| ---------------------------- | ----- | ------ | ----- |
| sensitivity `S_g < 0.05`(主要) | 26    | 24     | 21    |
| trusted 候選值少於 2 個            | 1     | 1      | 1     |
| **activated(存活)**            | **0** | **2**  | **5** |


根本原因 = sensitivity gate `S_g = max_v(m_gv) − min_v(m_gv) ≥ 0.05`:**27 個 gene 中有 21–26 個近乎平**
(S_g ~0.001–0.03,例:WaveSeparateGlobalReadA 在 medium 的 S_g=0.00096)—— 模型預測改變該 gene 的值
幾乎不影響預測延遲,故引導它 ≈ uniform ≈ 無 treatment。這**無法**靠放寬門檻解決(平的 gene 是真的平)。

次要:每個 shape 恰有 1 個 gene 湊不到 ≥2 個 trusted 候選值(support≥128、coverage≥0.95、可執行、無碰撞)。

補充:

- **(i) sensitivity 是 shape-dependent** —— 同一 gene 在不同 shape 過/不過(DepthU:medium S_g=0.142
過 vs large 0.029 不過;PrefetchGlobalRead 相反)。
- **(ii) entropy floor 不是 per-shape 的淘汰原因** —— `ENTROPY-CAP-20260810` 已把它改成 per-gene cap ρ
(故 DepthU 以 ρ=0.566 保留),而 binary floor 造成的全滅正是封存 aggregate max-reducer `analyze`
撞到的那個(`select_global_lambda` assertion,§7.3)。

這是**模型本身的性質,不是 per-shape artifact**(即使最豐富的 max reducer 也只浮現 3 個 gene)。依
charter §8.5,稀疏/微弱的 per-gene **marginal** 訊號必須**定位到層次** —— 它屬 marginal-loss(per-gene
marginal 弱);至於根因是真的不敏感、還是 epistasis 被 marginal 遮蔽、還是 survivor-frame/rank 壓縮,
**S11 無法分辨**(需 S12/oracle)—— 切勿寫「model useless」。

*來源:*`derivation-manifest-capped.json` *per_shape_activation_log;qa-09 §4.3b;S11 report §13;
parallel-analyze/VERIFICATION.md §5。*

### §3.6 為何三個 shape 可引導 gene 數不同(0 / 2 / 5)



#### §3.6.1 三個 locked problem size

三者皆為 BFloat16、non-StreamK、單一 dtype/layout,跑在 gfx942/MI300X。4-tuple 是
`(M, N, batch, K)` —— M×N 是輸出 tile,K 是 contraction(reduction)深度。


| shape      | M     | N     | batch | K       | 輸出元素數(M·N) | FLOPs(2·M·N·K·B)  | R_s(GFLOP/s 參考) | η_s    |
| ---------- | ----- | ----- | ----- | ------- | ---------- | ----------------- | --------------- | ------ |
| **tiny**   | 8     | 8     | 1     | 128     | 64         | 16,384            | 0.75            | 0.4466 |
| **medium** | 256   | 256   | 1     | 1,024   | 65,536     | 134,217,728       | 3,199.94        | 0.0042 |
| **large**  | 2,304 | 1,024 | 1     | 214,336 | 2,359,296  | 1,011,364,134,912 | 180,336.00      | 0.1229 |


相對尺度:**K** 由 128 → 1,024 → 214,336(×8,再 ×209);總工作量成長約 8×10³ 再 7.5×10³。三者是刻意
選的*發散 regime*,不是平滑掃描:一個退化的玩具、一個中型方陣、一個極深 K 的生產級 GEMM。

*來源:*`[CODE AUDIT]` *封存 contract* `s11/contract.py:674` *釘住*
`problem_sizes == [[8,8,1,128],[256,256,1,1024],[2304,1024,1,214336]]`*;per-shape R_s/η_s 來自 Lock A。*

#### §3.6.2 為何 Formocast 對每個 tiny config 都回哨兵值

這**不是**模型的 bug —— 它是一個明確的 *early-terminate guard*。`[CODE AUDIT]`
`formocast_simulator.cpp:578`:

```cpp
if ((M < 128 && MT0 - M >= 16) || (N < 128 && MT1 - N >= 16))
{ pp.microSeconds = 9999999.9; pp.hitRate = 0; return pp; }   // 「MacroTile 遠大於問題本身」
```

這個 guard 的意思是:*若問題維度很小(<128)而 kernel 的 MacroTile 超出它 ≥16,就拒絕為這個 config
建模。* 物理上那是一個**大部分在算 padding** 的 tile —— 例如 4×512 的 tile 用在 8×8 的輸出上,會計算
512 個 column 但實際只有 8 個(約 98% 浪費)。Formocast 選擇不估這種 regime,而不是吐出一個無意義的數字。

因此對 **tiny(M=8, N=8)**,guard 要求 **MT0 ≤ 23 且 MT1 ≤ 23**。對實際候選池實測:

> **⚠ DERIVATION NOT CITED,2026-08-13 稽核發現。** 有兩個問題。(i) 上面散文引用的那道 guard
> (`M < 128 && MT0 − M >= 16`)在 M = N = 256 時是**空轉的**,所以它產生不了 medium 的 171/434 ——
> 那一列必須來自*下一道* guard(`M >= 128 && MT0 − M >= 32`),它就在同一個 block 裡;散文應該引用
> 實際適用於各列的那一道 guard。(ii) `MacroTile` **不是** `s10-generated.yaml` 裡的**欄位**
> (該檔載的是 `MatrixInstruction`、`WorkGroup`、`GlobalSplitU`、`MIArchVgpr`、`UseSgprForGRO`、
> `LDSTrInst`),所以 434 / 171 / 1 是**導出**的量,而且沒有引用任何導出過程 →
> **`NOT_EVALUATED` as cited**。已在該 YAML 中驗證、且不受影響的是:9,918 條、**840** 個相異
> `MatrixInstruction` tuple、**262** 個 `WorkGroup:` 覆寫。質性結論 —— tiny 的哨兵值飽和 ⇒ 全部
> 27 個 gene 的 `S_g = 0.0000` —— 由 activation log 獨立佐證,**不**依賴這三個計數。


| shape           | 池中能通過 guard 的 MacroTile        | 比例        |
| --------------- | ------------------------------ | --------- |
| **tiny(8×8)**   | **434 個中的 1 個** ⚠ derivation uncited | **0.2 %** |
| medium(256×256) | 434 個中的 171 個 ⚠ derivation uncited | 39.4 %    |


所以 tiny 有約 99.8% 的搜尋空間回傳 `microSeconds = 9,999,999.9`。當幾乎每個 config 都在哨兵值上打平,
midECDF 會給每個 config 相同的 benefit ⇒ 每個取值的 marginal 都一樣 ⇒ **27 個 free gene 的 S_g 全部
= 0.0000**,與觀察完全一致。少數存活者共用同一個 MacroTile(那是 `group_0` 的性質,不在 treatment 內),
且數量遠不足以讓任何 free gene 湊到 ≥2 個 support ≥128 的 trusted 值。

**詮釋:** tiny **落在 Formocast 建模範圍之外**,不是「模型試了但失敗」。這正是設計中把 tiny 定為
**僅探索性**的原因 —— 它永遠不可能承載 guidance。

*來源:*`[CODE AUDIT]` `formocast_simulator.cpp:568–645`*(全部六道哨兵 guard);**
`protocol/v1/inputs/s10-generated.yaml`**(434 種相異 MacroTile);*
`derivation-manifest-capped.json` *per_shape_activation_log(tiny:所有 S_g = 0.0000)。*

#### §3.6.3 medium 與 large:數量追蹤「主迴圈主導程度」

對於 Formocast *確實有建模*的兩個 shape,可引導 gene 數追蹤的是**主迴圈主導執行時間的程度**,而它主要
由 K 決定。

**large(K=214,336 —— 約 medium 的 209 倍)→ 5 個 gene,最多。**
主迴圈跑極多輪,故每輪的**記憶體搬運管線主導總時間**。因此 5 個存活者全是 global-read / LDS / 主迴圈
資料搬運類 gene,且其 sensitivity 是所有 shape 中最大的:


| gene                          | S_g   | 作用                              |
| ----------------------------- | ----- | ------------------------------- |
| PrefetchGlobalRead            | 0.192 | global load 提前多久發出              |
| UnrollLoopSwapGlobalReadOrder | 0.165 | unrolled loop 內 global read 的順序 |
| GlobalReadVectorWidthB        | 0.058 | B operand global load 的寬度       |
| TransposeLDS                  | 0.057 | 轉置 operand 的 LDS 排列             |
| GlobalReadVectorWidthA        | 0.052 | A operand global load 的寬度       |


**medium(K=1,024)→ 2 個 gene。**
主迴圈中等:細部記憶體管線 gene 仍在門檻下(GRVWB / PGR / TransposeLDS ≈ 0.02–0.04),存活的是粗粒度的
**迴圈結構** gene:


| gene       | S_g   | 作用                  |
| ---------- | ----- | ------------------- |
| DepthU     | 0.142 | unroll 深度(每輪消耗多少 K) |
| 1LDSBuffer | 0.113 | LDS 單緩衝 vs 雙緩衝      |




#### §3.6.4 最有力的證據:主導 gene 隨 K 交叉


| gene                   | medium S_g         | large S_g          | 判讀                      |
| ---------------------- | ------------------ | ------------------ | ----------------------- |
| **DepthU**             | **0.142(PASS,最高)** | 0.029(FAIL)        | 迴圈結構類 gene —— 在中等 K 才重要 |
| **PrefetchGlobalRead** | 0.024(FAIL)        | **0.192(PASS,最高)** | 記憶體管線類 gene —— 在深 K 才重要 |


同樣兩個 gene 以相反方向互換角色。K 越大,主導 gene 就從*迴圈結構*(DepthU、LDS 緩衝)移向
*記憶體讀取管線*(prefetch、讀取順序、vector width)—— 這正是 GEMM 越來越 memory-pipeline-bound 時該有
的現象。

#### §3.6.5 Insight(報告可引用)

稀疏性**不是隨機雜訊,而是 shape-appropriate**:對每個問題,只有少數 gene 主宰其主導成本階段,而
Formocast 恰好把可偵測的 per-gene sensitivity 定位到那幾個 gene 上。

這是模型的一個**正向 validity 訊號** —— 它區分 gene 的方式符合 GEMM 物理(K 越大 ⇒ 越
memory-pipeline-bound ⇒ 記憶體類 gene 越敏感),而且它對退化的 shape 正確地選擇拒絕建模,而非捏造數字。
guidance「薄」主要是因為**多數 gene 對某 shape 的主導成本真的沒影響**,而非模型壞掉。

*誠實界線(§8.5):這是模型空間 sensitivity(Formocast 自身歸因,尚未真實 GPU 驗證),且為 per-gene*
*marginal(看不到 epistasis);「K ⇒ 記憶體主導」是與資料一致的機制詮釋,非已證因果。*

*來源:*`derivation-manifest-capped.json` *per_shape_activation_log(per-gene S_g);S11 report §13。*

### §3.7 group_0 vs free gene

group_0(MatrixInstruction/WorkGroup,9,918 joint 候選)為 GEKO 加權、**兩臂相同、treatment 從不碰它**
(已驗證兩臂的權重檔逐位元相同,§3.4b.4)。Formocast treatment 只重加權 ungrouped free gene。

*來源:S14 §6.1 note。*

### §3.8 Per-shape η_s(noise margin)

非退步門檻使用**per-shape** noise margin `η_s = P95(|log y − median log y|)`,由 pilot 殘差逐 shape 導
(medium η=0.0042、large η=0.1229、tiny η=0.4466),**不**用被 tiny 汙染的 aggregate `delta_noise` ——
因 η 是各 shape 量測重複性的性質。

最終非退步門檻 = `e^{−η_s}`。

*來源:S14 §10.2、baseline run-root 的 per-shape η。*

#### §3.8.1 margin 是什麼,以及為何 medium 的 margin 比 large 緊約 28×

**為什麼一定需要一條容忍帶。** 端點是一個比值 `F/G`。兩個*完全相同*的臂不會量出剛好 1.0 —— 量測抖動
保證它們不會。所以「`F/G < 1` 就代表 guided 臂退步了」這種規則,會把每一次雜訊閃動都變成一項發現。
`η_s` 就是把抖動與真實退步分開的容忍帶:

```
non-regression  ⟺  F ≥ G · e^{−η_s}
```

**每個 pin 實際允許什麼。** 這是讀者能據以推理的形式,而且它把 shape 之間的落差呈現得比原始 η 值清楚:


| shape | `η_s` | F 至少要是 G 的這個比例 | 容忍的退步幅度 |
|---|---:|---:|---:|
| **medium** | 0.0041953 | **99.58 %** | **0.42 %** |
| large | 0.1228459 | 88.44 % | 11.56 % |
| tiny | 0.4465998 | 63.98 % | 36.02 % |


**medium 是在一條比 large 窄約 27.6× 的帶上被判定的。** 這一個事實就是算術上的原因,說明為何*同一條*
非退步準則在 large 上回傳 5/5、在 medium 上卻只有 3/5 —— 這還沒談到任何關於汙染的論點。large 的 5/5
為何仍然是有條件的,見 §7.2a;medium 的量測缺陷見 §7.1b。

**medium 的 pin 是怎麼來的。** 一次 3-anchor × 7-fresh-client-repeat 的 pilot,其 anchor 跑在
4,629 / 3,200 / 2,127 GFLOP/s —— **比這個 pin 所治理的 champion 慢 2.9–6.3×** —— 因此這些 anchor 拿到
9.31 / 13.46 / 20.26 ms 的 warm-up,對比 champion 的 3.19 ms,而且 **0/21 dropouts**。完整的
provenance、被排除的 confounder,以及 warm-up 說法*無法*解釋的一個殘留:**§7.1b.4**。

**保留這個 pin 是治理決定,不是安全邊界。** 這個區別很重要,而且很容易搞反。保留一個預註冊、比較窄的
門檻*聽起來*像是謹慎的選擇 —— 但窄的帶會讓**宣告退步變容易、宣告非退步變困難**。那對受測臂是嚴苛,
不是安全。這個 pin 偏離現實有多遠,本檔案其他地方有兩個獨立的量度:

- 它比 champion 自己乾淨模態的 P95 值 0.0116(§7.1a)還**低 2.8×** —— 即使把每一個 dropout 都排除掉,
  它仍然比現實更緊;
- 它比 tiny 觀測到的零 treatment 包絡**低約 30×**(max |ln F/G| = **0.1247**;**樣本(sample)**標準差
  = **0.0715**,母體(population)標準差 0.0639 —— 文件引用的是 sample sd,而這兩者先前曾被誤認為彼此
  矛盾,所以這裡把估計量講明)。

所以保留它的理由是**「預註冊的門檻不會在看過資料之後才修訂」**,不是「這個門檻很保守」。任何暗示後者
的報告都是錯的。

**為何捨棄實測 margin —— 用展示的,不是斷言的。** 替代方案是從重測本身重算 η。有兩點反對意見,第二點
是決定性的:

1. **循環。** 正在被 gate 的那些 repeat 會反過來設定 gate。
2. **被 tiny 的 null control 證偽。** tiny 的兩臂逐位元相同(同一個 sha256,全部 5 個 seed),且
   **0/27 gene 被啟用** —— 保證是零效應。把 tiny 自己的窗內重複性(0.0145 → 門檻 `e^{−0.0145}` =
   98.56 %)套用到 tiny 自己的結果上:

   | seed | tiny `F/G` | 在實測 margin 下的判定 |
   |---|---:|---|
   | 24001 | 0.8828 | **退步** |
   | 24002 | 1.0350 | pass |
   | 24003 | 0.8841 | **退步** |
   | 24004 | 0.9953 | pass |
   | 24005 | 0.9690 | **退步** |

   一個會把已知、人為構造出來的零判成 **3/5 退步**的 margin,沒有資格取代一個不會這樣做的 margin。
   此決定的狀態:`PENDING_HUMAN_DECISION`,§9.2 D2。

**η 是錯的尺度 —— 而且這一點同時限制了*兩個*候選。** η 量的是**單一個固定 config** 的窗內重複性,而
estimand 是**兩個不同 champion** 的比值。臂間離散度在 tiny 上是窗內值的 4.9×、在 large 上是 2.0×。
無論 pinned 還是實測 margin,量到的都不是這個 gate 真正需要的量;pin 是基於治理理由被保留,而那個落差
是被揭露,不是被補上。

*來源:`[CODE AUDIT]` `noise/per_shape_noise.json → shapes.{shape}.eta_s`;
`scripts/compute_per_shape_noise.py:30`;tiny 的比值取自
`stage3_baseline/seed_*/tiny/champion_interleaved.json → F_over_G_median_ratio`;容忍度以
`e^{−η}` 計算。S14 design §10.2、§13.4。*

### §3.9 Conditional Arm S —— 它能做什麼、為什麼

**它是什麼。** 拿 Arm F 的 capped guidance,對每個 activated gene **打散「哪個候選值拿到哪個機率」**
(封存的 `deterministic_nonidentity_shuffle`),但保持 `ρ_g` —— 因而 `H_norm` —— **完全相同**。所以 Arm S
與 F **集中程度一樣**,只是指向別處。

**它回答什麼問題。** 若 F 勝過 G,有兩個互相競爭的解釋,而單看 F-vs-G 無法分辨:

- **(a) 方向** —— Formocast *特定的*偏好(把機率押在 DepthU=64、PrefetchGlobalRead=2 …)真的指向空間中
更好的區域。
- **(b) 只是集中** —— *任何*非均勻的 Gen0 都有幫助,與機率押在哪無關(例如集中會改變重複率、有效多樣性,
或讓 selection 更快拿到同一區域的多個副本去精修)。

Arm S 固定住 (b)、破壞 (a)。因此它是一個 **matched control**:F 與 S 之間唯一變動的,就是*機率押在哪些值*。

**三臂結果怎麼讀:**


| 觀察                | 結論                                                  |
| ----------------- | --------------------------------------------------- |
| F > G **且** F > S | **方向**有作用 → 可歸因於 Formocast physics                  |
| F > G **但** F ≈ S | **只有集中**在起作用;模型的特定偏好沒幫上忙 → 即 `FT-ENTROPY-ONLY` 失敗型態 |
| F ≈ S ≈ G         | 方向與集中都沒有產生效應                                        |


沒有 Arm S 時,正向的 F>G 只能歸因於「capped factorized initialization bundle vs baseline」—— 也就是
*整包 bundle*,而非模型的 physics。

**為何在此維持 conditional**(不無條件跑):

- (i) physics-direction 歸因是**下游 S20 的 registered 職責**(S20-H1 字面上就是「F 同時勝 G 與 S」);
在此跑等於重複一個已凍結的下游設計;
- (ii) 若 F 沒有勝過 G,就**沒有東西可歸因**,這臂買不到任何資訊;
- (iii) 5 對 paired seed 對**三方對比 underpowered**(F-vs-S 是在同一小樣本上的第二次比較);
- (iv) treatment 刻意**溫和**(每個 gene 都被 cap 到 `H_norm ≥ 0.80`),故它要控制的集中 confounder
*先驗上*就很弱。

因此採預註冊觸發(`CONDITIONAL-ARM-S-20260810`):**現在**就導出並封存 shuffle bundle(Lock C,在看到任何
outcome 之前,以維持 label firewall),但只有在 F 於 ≥1 confirmatory shape 過 directional gate **且**
budget 足夠時,才花 GPU 時間去跑。

**Arm S 不能做什麼。** 它不驗證 Formocast 的絕對準確度;它對 epistasis 毫無著墨(shuffle 一樣是 per-gene
marginal);5 seeds 下的 F-vs-S 虛無結果**不是**「無效應」的證據;而且它只能談論實際 activated 的
gene/shape。

*來源:S14 §10.2/§10.5;failure taxonomy* `FT-ENTROPY-ONLY`*;S20-H1。*

### §3.10 beat-native 兩側化放行

原本「不得宣稱勝過 native `PredictionThreshold`」的絕對禁令,就 S14 放寬為 two-sided/等資料再說:
**唯有**實際量測 native 並揭露任何 budget/selection confounding 時,方可宣稱相對 native 的價值;不捏造、
任一方向皆不預設結論。

*來源:charter §8.6a 2026-08-10(b)。*

---



## §4 Claim 框架(什麼能說 / 不能說)

- **Two-sided。** 報告 guided 對 early-search(gen-10、AUC)與**最終 tuned 品質**的效應(改善 / 無變化 /
退步),以 per-shape 效應量 + 區間 + 跨 seed 方向一致性呈現。資料支持時**得宣稱最終品質提升**
(`CLAIM-SCOPE-S14-20260810`)。
- **強制 caveat:** modest power(5 seeds,非顯著性)、scope(限受測 shape、單一 development cluster、
不一般化)、sealed 分析前不預設結論、不誇大。
- **Claim ladder:** model-only 稀疏 = headline;medium∧large 都過 per-shape gate → §8.2 early-search +
final 措辭;一過 → shape-specific / mixed;皆不過 → 「amended sparse prior 未達預註冊 directional gate」
(**非**「no effect / model useless」)。*來源:S14 §11 item 7 / §10.5。*
- **Physics-direction** 只有在 Arm S 有跑、且 F **同時**勝 G 與 S 時才可宣稱(否則歸因限「capped
factorized initialization bundle vs baseline」)。
- **仍然禁止(§8.6,不變):** 對 MI300X workloads 一般化、production/deployment ready、跨架構、
end-to-end tuning wall-clock speedup(未量測)、owner/team 應採用。

---



## §5 Metrics & acceptance

**主指標。** champion **real-GFLOPS**,配 **7× interleaved G/F(/S) remeasure**(同一 GPU)。

為何必要(報告可引用)—— 它對抗三個 in-search fitness 無法處理的問題:

- **(i) 勝者詛咒** —— GA 選出 champion 正是因為它「測起來最快」,幸運快值被過度代表;in-search 數字
系統性偏樂觀,且兩臂偏誤未必相等(評估過越多相異候選的臂,幸運抽樣越多)。
- **(ii) 時間漂移** —— baseline 比 guided 早跑數小時/數天,未受控比較會把*臂別*與*時間*(時脈、溫度、
機器狀態)混淆;把 G/F 交錯在同一窗口可抵銷。
- **(iii) 單次雜訊** —— per-shape 重複性 η_medium=0.0042(±0.42%),但 η_large=0.1229(±12.3%),large
單次量測無法分辨兩個接近的 champion。

取 7 次交錯重測的中位數可同時處理三者。**若不做**,預註冊的最終判準(`final ratio ≥ e^{−η_s}`,以 7×
中位數計算)在字面上**就無法評估** —— 那是 protocol deviation,最終品質 claim 會弱化成未受控的 in-search
觀察。*來源:S14 §10.2/§10.4。*

**次要/診斷。** gen-10 checkpoint、search-trajectory **AUC**(積分至兩臂共同完成預算)、`generations_run`。

**Per-shape directional-consistency gate**(預註冊,非顯著性檢定):對 confirmatory shape,{Gen0、gen-10、
AUC} 各需 ≥4/5 對 seed 為正,且 final ratio ≥ `e^{−η_s}` 於 ≥4/5(中位亦需在其上)。**合併 §8.2 措辭需
medium ∧ large**(intersection-union;不得用 aggregate 補救)。Tiny 僅描述性。*來源:S14 §10.4。*

**Assembly-dropped candidate handling(Reading 1):** 在 KernelWriter/assembly 階段 build 失敗的候選,
給 invalid fitness = −1,並比照 native Ductile 對「真跑但 benchmark 失敗」的 −1 處理(永不勝過正分、
永不成為 champion)—— **不另加 invalid 過濾**。*來源:S14 §6.1。*

### §5b 為何 F-vs-G 比較要取 **log**

原始比值 `F/G` 也會一併呈現(§7.1),因為它最直觀;但**分析用的量是** `ln(F/G)`,理由有四:

**(1) 對稱性 —— 原始比值不是公平的尺度。** 「快兩倍」是 `2.0`(距 1 有 1.0),「慢一半」卻是 `0.5`
(距 1 只有 0.5)。所以在原始尺度上,改善看起來比同等程度的退步更大,而且兩者無法相消。取 log 後完全
對稱:`ln 2 = +0.693`、`ln 0.5 = −0.693`。

**(2) 我們自己的資料就示範了這個偏誤。** 5 個 medium seed:


| 統計量               | 值                                 | 說明                                 |
| ----------------- | --------------------------------- | ---------------------------------- |
| 原始比值的算術平均         | 1.0499(**+5.0 %**)                | 看起來像有改善 —— 其實是被單一個 2.12× 的 seed 拉高 |
| 原始比值的中位數          | 0.9971(−0.3 %)                    |                                    |
| **log-ratio 中位數** | **−0.0029**(⇒ ratio 0.9971)       | 報告採用的中心趨勢                          |
| log-ratio 平均      | −0.1130(⇒ **幾何平均 0.893**,−10.7 %) | 正確的「平均乘性效應」                        |


用原始比值取平均會得到 **+5 % 的改善**,但幾何平均其實是 **−10.7 %**。對比值型資料,幾何平均
(= log 平均取 exp)才是正確的中心趨勢。

**(3) 預註冊的門檻本來就*定義在 log 空間*。** `η_s = P95(|log y − median log y|)`(§3.8)是在 log 殘差上
計算的,非退步門檻為 `e^{−η_s}`。所以檢定 `ln(F/G) ≥ −η_s` 是同單位的直接比較;用原始比值反而要來回換算。

**(4) GPU 吞吐量的雜訊是乘性的。** 每次執行的變異隨量測量級縮放(是 ±1% 這種效應,不是 ±X GFLOP/s)。
取 log 把乘性雜訊轉成加性雜訊 —— 這正是為什麼單一個 per-shape `η_s` 能在這些跨約 5 個數量級的 shape 上
(§3.6.1)有意義。

*來源:S14 §10.2/§10.4(gate 定義、η_s 定義於 log 空間);Lock A per-shape 噪音 artifact。*

### §5c AUC 準則是什麼,以及為何量測缺陷波及不到它

**定義。** AUC 是 `best_gflops_so_far` 對 `cumulative_complete_evals` 的**階梯保持積分**
(step-hold integral),積到兩臂最終完成評估數的共同預算 `B* = min` 為止。`best_gflops_so_far` 是一個
階梯函數(只有出現新的 incumbent 時才變動),所以這個積分就是一堆矩形的和,每個矩形從某一代的累積評估
數跨到下一代,高度取*前一個*高度。

**為何用共同預算、又為何不用代數作為橫軸。** 每代的評估數**並非固定** —— population decay 會在
diversity 觸發的那一代把族群砍半(§3.2b),所以某一臂的第 20 代所代表的評估量,可能遠少於另一臂的第
20 代。以代數為橫軸積分,等於在比較不等量的搜尋。`B*` 讓兩臂回答的是*「在相同的評估次數下,哪一臂的
best-so-far 曲線位置比較高?」*

**背後的資料。** `trajectory.jsonl`,每代一列(medium seed 24001 baseline 有 23 列),攜帶:


| 欄位 | 意義 |
|---|---|
| `best_gflops_so_far` | 累進最大值 —— **AUC 的被積函數** |
| `cumulative_complete_evals` | 橫座標 |
| `generation_batch_best_gflops` | 該代自己的峰值 |
| `generation_Q_median_any_valid` | 該代約 510 次評估的中位數 |


#### §5c.1 這項質疑,以及 AUC 為何挺得過它

**這項質疑是正當的,必須先講清楚再回答:** AUC 是由搜尋過程中的量測建構出來的,而那些量測走的是**同一個
client**、用的是**同樣的 321 次 warm-up**,正是產出被汙染重測的那條路徑(§7.1b)。如果那條路徑不可靠,
AUC 憑什麼不是一樣不可靠?

三個回答,由弱到強:

**(1) 曝險程度差約 30×。** `cumulative_complete_evals` 在**同一個** client invocation 內每代推進約
508–512、每個 solution 約 6.4 ms 的 GPU 工作。不論那個短視窗效應是什麼,它**每個 invocation 只付一
次**,量級是 sweep 拐點所隱含的約 50 ms —— 所以它最多只能碰到約 510 個 solution 中的前 8 個
(**約 1.6 %**),對比全新 process 之重測的 **28–48 %**,後者每抽一次就把時鐘重新歸零。(§7.1b.1。)

**(2) 被積函數是累進最大值,而汙染是單向向下的。** 一個被低估的評估**不可能拉低** `best_gflops_so_far`,
它只可能沒把它拉高。這條曲線在結構上就對這個失效模式有抵抗力,而單次的中位數沒有。

**(3) 實測的離散度定案。** 同樣的 champion、同一張卡、同一個 shape、同一個 client:


| 量 | 逐 seed 範圍 |
|---|---|
| **AUC `F/G`** | 0.9509 – 1.0461(**±5 %**) |
| 7× 重測 `F/G` | 0.3551 – 2.1175(**0.36× – 2.12×**) |


差了一個數量級。**如果 AUC 也帶著同樣的汙染,它就會帶著同樣的離散度。** 它沒有。這是一項觀察,不是從
機制出發的論證 —— 因此它挺得過 2026-08-13 對時脈說法的撤回(§7.1b):那次撤回改變的是「什麼造成重測
缺陷」,而不是「AUC 未被它波及」這個事實。

#### §5c.2 medium capped —— 逐 seed 的 AUC 值


| seed | AUC `F/G` | 變化 | `B*` |
|---|---:|---:|---:|
| 24001 | 1.0358 | +3.58 % | 8,522 |
| 24002 | 1.0210 | +2.10 % | 10,011 |
| 24003 | 0.9783 | −2.17 % | 10,592 |
| 24004 | 1.0461 | +4.61 % | 10,469 |
| 24005 | 0.9509 | −4.91 % | 9,837 |
| **為正** | **3/5** | | 要求 ≥4/5 |


**這個 3/5 是真正的不足,不是差一點。** 兩個負值是 −2.17 % 與 −4.91 %,遠遠超出一個全距只有 ±5 % 的量
上任何合理的抖動。加上 Gen0 的 3/5 與 gen-10 的 3/5 —— 三者都是從 GA trajectory 讀出來的,沒有一個經過
重測 —— 這就是為什麼 medium 的 gate **不論**最終端點問題最後怎麼裁定都會失敗(§9.1)。

#### §5c.3 殘餘風險,明說而非埋起來

有一種失效模式挺過了上面三個論證。一個真正強的候選,如果剛好在它**唯一**一次搜尋內評估被低估,它就
永遠不會成為 incumbent,於是 `best_gflops_so_far` 從來不知道它存在過 —— 而 (2) 的累進最大值論證,對一
個從一開始就沒被納入的值毫無保護作用。這一點無法從保留下來的 artifact 量化,因為逐代的 benchmark CSV
沒有保留(每臂只留下 `00_Final.csv`)。狀態:**`NOT_EVALUATED`**,而且 `NOT_EVALUATED ≠ no effect`。

*來源:`[CODE AUDIT]` `stage3_{baseline,guided}/seed_*/medium/trajectory.jsonl`;階梯保持積分的實作見
`agent_run/260809-s14-pershape-baseline/analyze_medium.py`;重測範圍取自 §7.1a。共同預算的必要性:
§3.2b。*

### §5a S11 gene-selection 量的計算方式(報告可引用;全部 sealed)

**sensitivity 到底在量什麼。** 一句話:*「在被抽樣的 config 母體中,這個 gene 的最佳取值看起來比最差
取值好多少 —— 以 Formocast 預測延遲的族群 rank 百分位點為單位。」* 全程沒有任何東西在 GPU 上跑;以下
每個量都是從 S11 抽樣語料上 Formocast 的**預測**延遲算出來的。

`S_g ≥ 0.05` **— 完整計算鏈**(全在模型空間;非真實 GPU):

1. **benefit**(`statistics.py:102/137`):每個 config 的 Formocast *預測延遲* → 在所有 config 中的
  **percentile rank**(midrank ECDF)→ `benefit = 1 − percentile` ∈ [0,1](越快 ⇒ 越高)。是族群
   **rank**,非絕對延遲。封存形式:`b_{c,s} = 1 − midECDF_s(predicted_latency)`。
2. **cells**:依 gene *g* 的取值分組(例:所有 `DepthU=64` 的 config 構成一個 cell),收集該 cell 的
  benefit。只有 **trusted** 的取值才會有 cell(見下)。
3. **shrinkage marginal** `m_gv`(`statistics.py:188 shrinkage_mean`):
  `m_gv = (Σbenefit + α·global_mean) / (n + α)`、**α = 32**。
   *為何要收縮:* 出現次數少的取值否則會產生極端平均值;α=32 把它拉向全域平均,所以一個取值要有真實
   support 才能推動它的 marginal。
4. **sensitivity**(`statistics.py:1166`):`S_g = max_v(m_gv) − min_v(m_gv)` —— 該 gene 最好與最差取值的
  收縮平均 benefit 之差。
5. **gate**:`S_g ≥ 0.05` —— 最好與最差取值需差 ≥ 5 個 rank 百分位點,否則判定該 gene 無可用訊號。

**這個數字怎麼讀。** `S_g = 0.142`(medium 的 DepthU)代表:使用 DepthU 最佳取值的 config,在預測延遲
排名中平均**高出約 14 個百分位點**(相對於使用其最差取值者)。`S_g = 0.00096`(medium 的
WaveSeparateGlobalReadA)代表最佳與最差取值只差**約 0.1 個百分位點** —— 無從分辨,亦即引導它與均勻抽樣
沒有差別。這個落差就是整個稀疏性故事(§3.5)。

**為何隱含基準是「均勻」。** `S_g = 0` 代表該 gene 每個取值的平均 benefit 都一樣 ⇒ 你在它上面建立的任何
偏好都是任意的 ⇒ 引導抽樣 ≡ 均勻抽樣 ⇒ 該 gene 不構成 treatment。所以這個 gate 問的是「有沒有東西值得
被引導**過去**?」。

誠實界線(charter §8.5):

- 它是**模型 rank 空間**(非真實 GPU)—— 在 rank 上平的 gene,在絕對 GFLOPS 上仍可能重要;
- 它是**per-gene marginal** —— 看不到 epistasis(只在組合下才有效的取值是隱形的);
- 它是 **survivor-frame / non-causal** —— 是「有進到評分」的 config 上的關聯,不是 causal gene effect;
- **0.05 門檻是啟發式**(5 個百分位點),**非**由噪音模型或 power analysis 導出(2026-08-09
design-discussion 已明確標註)。**0.80 的 entropy floor 是同一類未記錄常數** —— 其(缺席的)推導見
§3.4c.2。

*來源:statistics.py;*`derivation-manifest-capped.json` *locked_formulas/locked_constants;qa-03 §0.11。*

**「Fewer than 2 trusted values」是什麼意思。** 一個 gene 有多個候選值(例:DirectToVgprA ∈ {True,False};
DepthU ∈ {16,32,64,128,256,512})。一個取值算 **trusted** 必須在 S11 抽樣語料中同時滿足(`workflow.py:758–802`;manifest `gate_definition`):

- **support ≥ 128**(`support_min_conditional_fraw` — 至少 128 個合格 config 用了該值);
- **executable**(`Dexec` 非空 — 至少 1 個該值 config 編譯+執行成功);
- **coverage** `Cscore_occ_gv` **≥ 0.95**(其出現的 ≥95% 有被評分);
- **no** `collision_confounded`(canonical 身分未被 hash 碰撞混淆)。

要算 sensitivity(取值間的差)需**至少 2 個 trusted 值來比較**;少於 2 個的 gene **不可測**,直接淘汰。
三個 shape 都因此被砍的 gene 是 `DirectToVgprA`(`n_trusted = 1`)—— 其兩個布林值只有一個達到 ≥128 的
trusted-support 門檻(另一值的 config 太少 / 大多 build 或評分失敗)。*來源:derivation-manifest-capped.json
per_shape_activation_log;workflow.py trusted-set builder。*

---



## §6 Artifact / file reference



### Locks

- Lock A(baseline protocol):`agent_run/260809-s14-pershape-baseline/lock/lock_a_protocol.json`,
checksum 在同層的 `lock/lock_a_protocol.sha256`(**不是** `lock_a_protocol.json.sha256`)
(+`.sha256`)
- Lock B(capped guidance):`agent_run/260809-s14-pershape-guidance/lock/lock_b_guided_guidance.json`
—— `lock` id `S14_LOCK_B_GUIDED_GUIDANCE`,
sha `3ac9768768ac088596687c47635bd6b8b5018d67cecc3f08e69ba2857b0ce59b`
- Lock C(Arm-S shuffle):**待封**(bundle 已導出;看到任何 Arm-S outcome 前先封)



### Treatment inputs

- Capped guidance weights(F 注入的):
`agent_run/260809-s14-pershape-guidance/out-capped/ga-weights-{medium,large,tiny}.json`
- S11 per-size scores(guidance 的來源):
`study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-native-scores.json`(68 MB)
- 已啟用的 gene:medium={1LDSBuffer, DepthU};large={TransposeLDS, UnrollLoopSwapGlobalReadOrder,
GlobalReadVectorWidthA, GlobalReadVectorWidthB, PrefetchGlobalRead};tiny=無。



### Run outputs

- Baseline champions/trajectory:
`agent_run/260809-s14-pershape-baseline/stage3_baseline/seed_<S>/<shape>/{optimization_result.json,trajectory_metadata.json}`
- Guided:`.../stage3_guided/seed_<S>/<shape>/...` *(與 `stage3_baseline/` 同層,不是巢狀 —— 路徑已於 2026-08-13 更正)*
- 7× remeasure:driver `scripts/s14_guided_remeasure_driver.py`(interleaved G/F、counterbalanced
start-arm)
- Status:`resume_status.json`(baseline)、`guided_status.json`(guided)



### `optimization_result.json` schema(每個 GA champion)

- `best_individuals` = 30-gene champion kernel config(含 `group_0`);
- `best_individual_hashes` = canonical sha256;
- `best_fitness` = champion 真實 GPU 效能(GFLOPS 級,GA 最大化的值);
- `generations_run`(含早停);
- `cumulative_any_valid_evals` / `cumulative_complete_evals` / `cumulative_distinct_benchmarked`;
- `seed`、`shape`、`size`。



### Authority docs

- Charter:`study_docs/research/surrogate-dse-plan.md`(§8.2、§8.5、§8.6、§8.6a)
- Experiment plan:`study_docs/research/ductile-origami-warmstart-experiment-plan.md`(criteria + DAG)
- S14 design:`.../ductile-origami-warmstart/s14-stage1-full-ga-outcome-design.md`(§6、§10、§11、§12)
- S11 design:`.../s11-stage1-model-only-factorization-design.md`
- QA readers:`.../qa/qa-09-per-shape-soo-redesign-decisions.md`、
`.../qa/qa-03-s11-factorization-and-metric-design.md`
- Gate closure report:`.../reports/staged/s11-...report.md`(S00/S10/S10R2/S10R3/S11 的 design 各自
  預註冊 `staged/` 路徑);S14 現在也放在同一個目錄(`REPORT-LOCATION-20260813`,design §12A):
  `.../reports/staged/full-ga-baseline-vs-guided-outcome-report.md`,另有三份 per-shape 附冊
  `.../reports/staged/s14-{medium,large,tiny}-report.md`。命名規則見 `reports/README.md`。
- Reboot/resume + Claude 監督基礎設施(methods):`/data1/perlee/S14_RESUME_MECHANISM.md`

---



## §7 結果 placeholder(run 完成 + 獨立驗證後才填 — 切勿捏造)


| 報告需要的數值                                                          | 狀態                                                                                                                                         | 來源路徑                                                                                      |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Baseline per-shape/seed champion GFLOPS + gen-10                 | `NOT_EVALUATED`(baseline champions 已存在;分析前維持 quarantine)                                                                                   | `stage3_baseline/seed_*/{shape}/optimization_result.json` + `trajectory_metadata.json`    |
| Guided per-shape/seed champion GFLOPS + gen-10                   | `NOT_EVALUATED` —— **5 seeds × 3 shapes 全數完成**(quarantined)                                                                                | `stage3_guided/seed_*/{shape}/...`                                                        |
| 7× interleaved G/F remeasure medians — MEDIUM                    | **MEASURED 5/5** —— 見 §7.1                                                                                                                 | `stage3_baseline/seed_*/medium/champion_interleaved.json`;`medium_remeasure_summary.json` |
| 7× interleaved G/F remeasure medians — LARGE                     | **MEASURED 5/5** —— 見 §7.2                                                                                                                 | `stage3_baseline/seed_*/large/champion_interleaved.json`                                  |
| 7× interleaved G/F remeasure medians — tiny                      | `NOT_EVALUATED`(3/5 已重測;24002/24003 待跑)                                                                                                    | 同樣式,逐 shape                                                                               |
| Per-shape directional-consistency gate 結果(Gen0/gen-10/AUC/final) | medium 已算(見 §7.1);**large 已算(見 §7.2)**;tiny `NOT_EVALUATED`                                                                                | S14 分析(run 後)                                                                             |
| Conditional Arm S(是否觸發?F vs S)                                   | `NOT_EVALUATED`(conditional)                                                                                                               | Lock C + Arm-S runs(若觸發)                                                                  |
| Native-P0 11,405 large G/F + 相對 512 的稀釋                          | `NOT_EVALUATED`(排程中)                                                                                                                       | native addendum run-root(TBD)                                                             |
| S11 gates(7-AND)+ decision + reproduction                        | **無法產出** —— 見 §7.3                                                                                                                         | `protocol/v1/{manifests,evidence}/...`(將維持不存在)                                            |
| S11 per-gene sensitivity 表(稀疏性)+ gate margins                    | AVAILABLE(描述性)—— 3 個 gene 過全部 7 gate:PrefetchGlobalRead(S=0.094, +88%)、UnrollLoopSwapGlobalReadOrder(S=0.090, +80%)、DepthU(S=0.054, +7.4%) | `parallel-analyze/out/passes.w72.json`、`diag-lambda2.w72.json`;qa-09 §4.3b                |




### §7.1 Medium 7× remeasure(已量測、quarantined)

已量測 5/5;**尚未過完整 per-shape gate;two-sided,不下結論。**

Final-champion 各臂的 7×-median real-GFLOPS,以及 F-vs-G 對比(為何以 log-ratio 為分析量見 §5b):


| seed                      | G 中位數(GFLOP/s) | F 中位數(GFLOP/s) | **F/G ratio** | **變化率**    | log-ratio `ln(F/G)`    |
| ------------------------- | -------------- | -------------- | ------------- | ---------- | ---------------------- |
| 24001                     | 13,495.3       | 13,456.3       | 0.9971        | −0.3 %     | −0.0029                |
| 24002                     | 12,349.9       | 8,710.9        | 0.7053        | −29.5 %    | −0.3491                |
| 24003                     | 6,137.5        | 6,595.3        | 1.0746        | +7.5 %     | +0.0719                |
| 24004                     | 6,283.1        | 13,304.5       | 2.1175        | +111.8 %   | +0.7502                |
| 24005                     | 13,192.3       | 4,684.9        | 0.3551        | −64.5 %    | −1.0353                |
| **中位數**                   | —              | —              | **0.9971**    | **−0.3 %** | **−0.0029**            |
| *(原始比值的平均 —— 有誤導性,見 §5b)* | —              | —              | *1.0499*      | *+5.0 %*   | *(幾何平均 0.893,−10.7 %)* |


- **2/5 為正、中位 ≈ −0.3 %** → final-champion 這一項未達預註冊 ≥4/5 正向門檻(Gen0/gen-10/AUC 另行分析;
皆 2–3/5)。
- ~~per-seed 變異大(F = G 的 0.36×–2.12×)vs η_medium = 0.42 % → 這些是真實的 champion 差異、不是
量測雜訊~~ —— **RETRACTED 2026-08-12,與原始 artifact 矛盾。** 見 §7.1a。釘住的 `η_medium = 0.0042`
並不描述這些量測:**7× repeats 的經驗 P95 log-residual 為 1.2098,即釘住值的 288×**。medium 的
per-seed F/G 差異**無法**在量測離散之上被解析出來,而各 seed 之間的方向不一致,正是「7 次取中位數本身
就是一場樂透」時會預期看到的現象。
- 注意 baseline 臂自己就橫跨 6,137–13,495 GFLOP/s —— 此 shape 上 GA 的收斂高度依賴 seed,guided 的效應被埋在這個更大的變異裡。
- **Deviation:** 於 GPU 5 執行(非各 seed 的 Lock-A 搜尋卡),透過非封存 copy
`remeasure_interleaved_champion__gpu5deviation.py`(加 opt-in `--gpu-uuid-override`;封存腳本 + Lock A
未變;組內比值抵銷卡別 offset)。見 `medium_remeasure_deviation.md`。



#### §7.1a Medium 的量測被 ~28 % dropout 汙染 —— 7 次取中位數是一場 mode 樂透

**RETRACTION AND CORRECTION(2026-08-12)。** 上面那條 bullet 原先主張 medium 的 per-seed F/G 差異是
真實的 champion 差異、而非量測雜訊,理由是它們相對於 `η_medium = 0.0041953` 很大。`[CODE AUDIT]`
原始的 remeasure repeats 與此矛盾。

7× interleaved 協定量的是**同一個固定的 champion config**,量七次,在**同一張卡、同一個 process 內、
約 27 秒的視窗中**完成。它理應是本研究中最可重複的數字。在 medium 上並非如此:


| seed / arm | 量到的 7 個 GFLOP/s | max/min |
|---|---|---:|
| 24001 G | 13,561 · **3,771** · 13,495 · 13,598 · 13,454 · 13,549 · 13,487 | **3.61×** |
| 24001 F | 13,456 · **2,234** · 13,535 · 13,404 · 13,547 · 13,456 · 13,527 | **6.06×** |
| 24002 G | 12,420 · 12,356 · 12,325 · **6,218** · 12,371 · **5,255** · 12,350 | 2.36× |
| 24005 F | 4,685 · 7,164 · 2,944 · 2,870 · 10,535 · 2,166 · 5,456 | 4.86× |


依 Lock A 自己的定義(`P95(|log y − median log y|)`)直接由這些 repeats 重算 noise margin,逐 shape、
跨所有 seed 與兩臂:


| shape | 釘住的 `η_s` | **經驗 P95 log-residual** | 比值 |
|---|---:|---:|---|
| **medium** | 0.0041953 | **1.2098** | **288×** |
| large | 0.1228459 | 0.0269 | 4.6× conservative |
| tiny | 0.4466 | 0.0145 | 31× conservative |


**CORRECTION 2026-08-12(second pass)。** 上面那個「288×」的讀法*算術上正確、但診斷上具誤導性*,而這個
更正很重要,因為它改變了「該修什麼」。第二輪診斷 campaign(§7.1b)顯示 medium 的 repeats 是**兩個母體
的混合**,把它們合併起來的統計量哪一個母體都不描述:


| 母體 | 占比 | P95 log-residual | 對照 pinned `η_medium` |
|---|---:|---:|---|
| **乾淨**(≥ 該臂最大值的 95 %) | **101 / 140 = 72 %** | **0.0116** | **2.8×** —— 同一個數量級 |
| **dropout** | 39 / 140 = 28 % | — | — |
| 合併,campaign 2(capped + native) | 140 | 1.0503 | 250× |
| pooled, **campaign 1** (capped + native) | 140 | **1.2098** | **288×** |


**CORRECTION 2026-08-13(third pass,出自 §13 的 design-discussion)。** 上表的「140」是**campaign 2 內的
capped + native** —— 兩個 *P0 level*,不是兩個 campaign —— 而 27.9 % 的 dropout 率是 campaign 2 的。
**campaign 1 才是記錄在案的量測(§13.3),其汙染率為 46.4 %**(capped 45.7 %、native 47.1 %);四組全部
合併是 104/280 = 37.1 %。上面引用的 1.2098 屬於 capped campaign 1 的 70 個點,不屬於那個 140 點的 pool。
**主要結果集的汙染程度,比本節原先陳述的要嚴重得多。**

~~所以 `η_medium = 0.0042` 對一次乾淨的 medium 量測而言大致正確 —— 產生它的 pilot 顯然抽到的都是乾淨
的 draw。~~ **STRUCK 2026-08-13(§13.4)。** 對 `260807-s14-baseline-run/stage2_noise/raw_repeats.jsonl`
的鑑識顯示,pilot 的 medium anchors 跑在 4,629 / 3,200 / 2,127 GFLOP/s —— **比 champion 慢 2.9–6.3×**,
亦即 9.31 / 13.46 / 20.26 ms 的 warm-up(由 artifact 導出;§7.1b.4),一個曝險低得多的區間 —— 且
**0/21 pilot dropouts**,而且它們比 champions
自己的 clean mode 還*更緊*(η_medium 比 clean-mode 的 P95 0.0116 還**低** 2.8×)。這個 pin 量到的是一個
從未抽到汙染物的 workload 的可重複性,不是對「乾淨 champion 量測」的描述。三個 pin 都是 pilot 的無關
意外(§13.4)。這個缺陷仍然**不是 noise margin 估錯**。缺陷在於
28 % 的量測完全來自另一個母體,而協定**沒有任何機制去偵測或排除它們**。調高 `η` 是錯誤的修法:那會為了
吸收一個汙染物而放寬*所有東西*的容差,毀掉 gate 在那 72 % 正常樣本上的檢定力。

**只有 medium 受影響,而且它壞在危險的方向** —— 一個緊了 288× 的 margin 會把純粹的離散判成真實效應,
而這正是被撤回的那條 bullet 做的事。large 與 tiny 則偏保守(它們的真實量測比 pin 假設的*更*可重複),
那是安全的方向,並讓 §7.2 的結論維持不變甚至更強。

**必須帶進報告的後果:**

- **medium 的 per-seed F/G 值不能被詮釋為 champion 品質。** 視窗內的變異達 2–6×,7 次的中位數本身就是
  一個來自寬分布的抽樣,所以 seed 層級的「效應」(0.36×、2.12×、…)大半是量測樂透。medium 的
  directional-consistency gate 檢定力極低。
- **`η_s` 是 pilot 推導出來的,而且從未針對真正的 remeasure repeats 重新驗證。** `η_s` 來自 3-anchor ×
  7-repeat 的 noise pilot(§3.8)。這是它第一次被拿來對照它所適用的量測本身。在 medium 上這個 pin
  *對乾淨 draw* 是站得住的(2.8×),但協定從未檢查 draw 是否乾淨 —— 那才是缺口,而且它適用於每一個 shape。
- **§3.3 / S14 §12.2 把 medium 加進 native addendum 的理由被削弱。** 那個理由是「medium 是唯一兩臂差異
  可被量測到的 shape」。若 medium 的差異其實是量測離散,前提就不成立。native-medium 的 run 仍然有效且
  有用 —— Gen0 分解(Q3)完全不依賴 champion 量測 —— 但納入該 shape 的既述理由必須更正。
- **large 不受影響,而且立場更穩。** 它的經驗離散(0.0269)遠低於它釘住的 margin,所以「五個 seed 全部
  落在 η_large 之內」不是 pin 過鬆造成的 artifact。

**Root cause: NOT_EVALUATED。** 這個雙峰性在單一張卡、單一 process 內可重現,因此排除了 run 之間的
drift、跨 session 的熱效應,以及卡與卡之間的差異。候選解釋。*(2026-08-13 更新 —— 本條先前把
clock/power-state 轉換列為一個尚未被區分開的候選,並說那個能區分的量測「**尚未**」進行。
**這兩句話現在都是錯的。** 那個量測做了 —— 3 個 seed × 14 筆、在實際進行中的 remeasure 上以 1 kHz
採樣 `sclk` + `busy` 的遙測 —— 而且它**否證**了時脈這個候選,這就是為什麼下面的清單裡已經沒有時脈。
見 §7.1b 開頭的區塊。)* 倖存、且仍未被區分開的候選是:rotating-buffer / cache-residency 狀態在
repeats 之間不同(medium 用 `RBS = 4096`、large 用 `0`);在 medium 約 134 MFLOP 的問題規模下由
launch overhead 形成的地板;XCD/CU 配置;MALL/L2 residency;GSU-4 workspace 競爭;以及任何能解釋
所觀察到的*時脈更高、kernel 卻更慢*的機制。Root cause:**`NOT_EVALUATED`**。

*來源:`[CODE AUDIT]` **第一次 campaign** 的 medium 重複值,保存於
`medium_recheck_control/{capped,native}/seed_*/preserved_campaign1_20260812T135613Z/champion_interleaved.campaign1_*.json`
→ `remeasure.{G,F}`。**引用已於 2026-08-12 改指:** canonical 的
`stage3_baseline/seed_*/medium/champion_interleaved.json` 在 14:01–14:04 被第二次診斷性 campaign
(§7.1b)取代,已不再含有上表所引的數值;資料並未遺失(由保存路徑可逐格重現本表)。large 與
tiny 的重複值仍在 `stage3_baseline/seed_*/{large,tiny}/champion_interleaved.json`。pinned `η_s`
與其公式見 `noise/per_shape_noise.json`。*

(在 native-medium 分析中被獨立重新發現;該分析現在收在 `reports/staged/s14-medium-report.md`。
它那份已被取代的工作筆記保留在 `reports/working-notes/` 之下、不得引用,因此**刻意不**在此處列為
來源 —— 見該目錄的 README。)

**dropout 不是 medium 獨有,也不是單一張卡獨有。** `[CODE AUDIT]` 對每個 shape 的每一次 repeat 稽核,
凡低於該臂最大值 80 % 者計為 dropout:

> **⚠ COUNTS CORRECTED AND THRESHOLD PINNED DOWN,2026-08-13。** 這張表先前把 medium 記成
> `39 / 140 = 27.9 %`、large 記成 `0 / 70` —— **同一條敘述的規則底下混用了兩個不同門檻**,而且 medium
> 那個數字重現不出來。以明確定義從原始 repeats 重算 —— **一次 repeat 若低於其自身 `(seed, arm)` 最大值
> 的給定比例,即計為 dropout** —— 涵蓋全部 5 seeds × 2 arms × 7 repeats × 2 個 P0 level
> (medium 的 n = 140,其餘為 70):
>
> | shape | campaign | `< 0.80` | `< 0.95` |
> |---|---|---:|---:|
> | medium | **campaign 1**(擬定為紀錄用量測) | **65 / 140 = 46.4 %** | **65 / 140 = 46.4 %** |
> | medium | campaign 2 | **43 / 140 = 30.7 %** | **44 / 140 = 31.4 %** |
> | tiny | — | 0 / 70 | **1 / 70** |
> | large | — | **0 / 70** | 1 / 70 |
>
> campaign 1 在兩個門檻下完全相同,因為它的汙染很深 —— 每一個 dropout 都低於 0.80。**舊的
> `39 / 140` 與另一次獨立稽核的 `38 / 140`,在現有 artifact 上、在任一門檻下都重現不出來**;兩次重算
> 既與文件不合、彼此也不合,代表原始數字的定義從來沒有被釘死。請改用上表,並在引用任何比率時說明門檻。
> §7.1a 那個 `101 / 140 = 72 %` 的乾淨值繼承同一個缺陷(`140 − 101 = 39`),已由此處 campaign 2 的
> `< 0.95` 那一列取代。


| shape | cards used | dropouts(campaign 2,`< 0.95`) | rate |
|---|---|---:|---:|
| medium | hip 5 only (`--gpu-uuid-override`, §8.3) | 44 / 140 | **31.4 %** |
| tiny | hip 2, 3, 4, 6, 7 | **1 / 70** | 1.4 % |
| large | hip 2, 3, 4, 6, 7 | **1 / 70** | 1.4 % |


唯一那個 tiny dropout 是 **hip 7** 上的 `seed 24004 arm G`:`3.82, 3.81, 3.78, 3.84, 3.79, 3.80, **0.30**`
—— 其中一次只有其他次的 8 %,變異 12.74×,與 medium 的質性特徵相同。所以這個機制**不是 GPU 5 獨有**;
各 shape 之間不同的是它的*發生率*。另外要注意,P95 統計量看不見 1/70 的事件(那是第 98.6 百分位),
這就是為什麼 §7.1a 的 per-shape P95 表把 tiny 列為乾淨 —— 那張表量的是*主體*,不是尾巴。

**卡別與 shape 在這裡是混淆的 —— 已在 §7.1b 拆開。** 每一次 medium 量測都在 hip 5 上;沒有任何其他
shape 曾在該卡上量過。*(本段先前寫著那個能區分兩者的測試「進行中」、且兩個假說都未被確立;該測試此後
已經回來,結果由 §7.1b 陳述。2026-08-13 更正 —— 這兩段先前彼此矛盾。)* 結果見 **§7.1b**,但要帶上一個
重要的 caveat:它跨 shape 的那一半很弱 —— hip 5 獲得平反,靠的是**同卡**的 pilot 對照,不是
tiny-on-hip-5 那個結果。

#### §7.1b Root cause —— client 的 warm-up 是以 enqueue *次數*、而非*時間*指定

**這是 §7.1a 的解釋,同時它也框住了損害範圍:此缺陷侷限在 remeasure 路徑,並未波及 GA 搜尋。**

`[CODE AUDIT]` `ClientParameters.ini` 設定 `num-warmups=321` 與 `num-enqueues-per-sync=321`
(另外還有 `max-enqueues-per-sync=-1`)—— **三個 shape 完全相同**。但 kernel 時長相差三個數量級,
所以同一個次數買到的*時間*天差地遠:


| shape | kernel 時長 | 暖機牆鐘時間 | 結果 |
|---|---:|---:|---|
| **medium** | ~10 µs | **~3.2 ms** | 28 % dropout |
| large | ~1.87 ms | ~600 ms | 0 / 70 dropout |
| tiny | dispatch-bound | (對 warm-up 長度不變) | 1 / 70 |


>  ### ⚠ MECHANISM CONTRADICTED 2026-08-13 —— 讀下面那段之前,先讀這一段
>
> 接下來那套時脈斜坡的說法,原本是為 warm-up 相關性所提出的*解釋*。一次直接量測現在已經否證了它,
> 以下保留它,僅僅是作為「曾被檢驗過的假說」,**不是**作為一項發現。
>
> `[GPU]` 非 sudo 驗證階梯的第 1 步:3 個 seed × 14 筆紀錄,在**實際進行中的 medium remeasure** 上、
> 於 GPU 5 以 **1 kHz 採樣 `sclk` + `busy` 軌跡**,每次 idle gate 都乾淨(GPU 0 %,host load
> 0.031–0.079 / 224 cores)。現象有重現 —— **25/42 dropouts** —— 所以這追蹤到的是真實效應,而不是一張
> 安靜的卡。它發現:
>
> - 時脈與吞吐量的相關是**負的**,Spearman **−0.32**;
> - dropout 那幾次的時脈中位數**更高**(**1798 MHz**),乾淨的重複反而較低(**1689 MHz**);
> - **每一次**重複,不論乾淨或被汙染,都達到 **1512–2065 MHz** —— 沒有任何一次停在 132 或 500 附近;
> - 雙向都有反例:在 2065 MHz 的峰值下只有最大值的 0.470;在只有 1674 MHz 時卻有 0.997;
> - dropout 那幾次**耗時更久** —— kernel 是真的跑得比較慢,這不是回報上的假象。
>
> **附帶更正。**(a) GPU 5 在持續負載下最高只到 **~1770–1810 MHz**,所以「乾淨 = 2100 MHz」是錯的
> 基準,任何對 2100 做的比值算術都作廢。(b) sysfs 節點**並不**暴露三個離散的 DPM 檔位:閒置時讀到
> `S: 131Mhz *`,但在負載下它回報的是一個以 500/2100 為界的*連續*當前時脈 —— 所以「卡在低 DPM 檔位」
> 這個假說在物理上從來就無法被檢驗。(c) 2026-08-12 那次時脈 probe 的 null 是**無資訊,不是弱證據**:
> `--setperflevel high` 從未生效,而那個「pinned」臂的軌跡與 control 完全相同(75 % 的採樣低於
> 200 MHz)。它必須停止被引用,兩個方向都不得引用。
>
> **儀器限制,如實載明:** 在約 8 ms 的有效解析度下(數值每約 8 ms 才更新一次,且看似經過 SMU 濾波),
> 該追蹤**無法**解析 3.2 ms warm-up 期間內部的時脈行為。它只界定了 GPU-active 階段的包絡。因此時脈
> 說法**並未被排除** —— 而是在現有解析度下缺乏支持,同時可觀測到的時脈行為指向相反方向。
>
> **狀態:機制 `NOT_EVALUATED`。** 倖存的候選解釋,全部未經檢驗:XCD/CU 配置、MALL/L2 residency、
> GSU-4 workspace 競爭 —— 以及任何能解釋「時脈更高、kernel 卻更慢」的機制。

**倖存、且不得被過度撤回的部分:** warm-up 的**經驗**相關性完全不受影響。下面那個 sweep、卡內的 pilot
對照(§7.1b.4),以及 tiny 對 warm-up 長度被量到的不敏感性,三者各自成立。**warm-up 時間可以預測汙染;
現在沒有依據的是「時脈斜坡就是原因」這句話。**

*(以下為原本陳述的假說,留存備查:)* 閒置的 MI300X 停在 132–180 MHz,需要數十毫秒的持續工作才會升到
2100 MHz;medium 的 3.2 ms warm-up 在卡還在爬升時就結束了,於是計時視窗打開時 GPU 只升壓到一半,而爬升
是否來得及完成由 power governor 決定 —— 這會解釋為什麼結果是雙峰、而不是重尾。

**決定性的證據是一次 warm-up sweep**(獨立 probe:同一個 client binary、同一個已編譯的 champion、只變
一個旋鈕、每個變體 25 個全新 process、idle-gated)。它給出乾淨的單調拐點:


| warm-up wall time | 3.2 ms | 6.4 ms | 13 ms | 26 ms | **51 ms** | 103 ms | 205 ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| dropout rate | **48 %** | 32 % | 12 % | 8 % | **0 %** | 0 % | **4 %** |


**2026-08-13 補上兩點 caveat(§13.3),都是實質的。**(i) 這個 sweep 在拐點之上**並非單調** ——
20,544 次 warm-up(205 ms)仍然回傳 1/25。(ii) **這個 sweep 的每一個點都跑在
`rotating-buffer-size = 0`,而不是釘住的 4096。** 光是 RBS 0 就把水準從 12,430 推到 14,153(+14 %),
所以它是一個*不同的 estimand*;而兩個 RBS-4096 的長 warm-up 變體**25/25 全數 crash**
(50 × `hipModuleLoad rc=-6`)。**因此這個修法在 production 設定下未經驗證。** 能一舉定案、卻尚未嘗試的
組態是 **5,136 warm-ups at RBS 4096**(≈58 ms,越過拐點);兩個 crash 的變體用的都是 32,100。


| probe 變體 | median GFLOP/s | max/min | dropout |
|---|---:|---:|---:|
| 生產設定 | 12,430 | 5.24 | 48 % |
| `sleep-percent = 0` | 12,466 | 2.32 | 40 % |
| `rotating-buffer-size = 0` | 14,153 | 30.6 | 24 % |
| **32,100 warm-ups + RBS 0** | **14,334** | **1.018** | **0 %** |


所有曾觀察到的 dropout 都落在其臂最大值的 `[0.0742, 0.7847]` 區間內(下端是
`tiny_gpu5_probe_summary.json` 裡的一個 tiny dropout;較早的草稿引用 0.0785,而那本身就是決定該界線的
那個點)。**STRUCK 2026-08-13:** 這裡原本有兩句話寫著「一個數十毫秒、固定牆鐘長度的暫態正是 DPM-ramp
的特徵」,並提出 `~165/2100 = 0.0786` 作為相符的時脈比值。兩句都撤回 —— 165 MHz 不是這張卡在負載下會
回報的時脈,2100 MHz 也不是它會達到的水準,而且直接追蹤顯示 dropout 發生在*高*時脈下。這個區間仍然是
關於 dropout 分布的真實觀察;它不再是時脈成因的證據。

**兩個乾淨的 shape 為什麼乾淨 —— 是測過的,不是假設的。** large 的 warm-up 約 600 ms,是爬升所需時間的
12 倍。tiny 則直接量過:它的吞吐量**對 warm-up 長度不敏感**(321 與 20,544 次 warm-up 都是
4.0 GFLOP/s),而 medium 則從 14,001 升到 14,375。在 16,384 FLOP 之下,tiny 純粹是 dispatch latency,
由 command processor 處理。要曝險必須**同時**具備短牆鐘視窗,**以及**對「短視窗沒能建立起來的那個東
西」敏感;只有 medium 兩者兼具。*(這句話原本把第二個因素稱為「clock 敏感性」;依 §7.1b 開頭的區塊,
時脈歸因已撤回。不論底層那個量最後是什麼,tiny 對 warm-up 長度被量到的不敏感性都成立。)*

**已被排除的假說:**

- **卡本身。** medium 只在 hip 5 上量過,所以卡別與 shape 完全混淆(§7.1a)。有兩個測試能拆開這個混淆,
  而且**順序很重要**:

  - *跨 shape(比看起來弱)。* 在 hip 5 上重測 tiny 得到 **hip 5 上 2/70 dropouts、Lock-A 卡上 1/70**,
    對比 medium 的 28 %。**2026-08-13 補上 CAVEAT:** 單看這一項幾乎沒有內容。前兩段已經證明 tiny
    *對整個機制不敏感*(對 warm-up 長度不變、dispatch-bound),所以 hip 5 上 tiny 乾淨,是**不論** hip 5
    有沒有 clock 問題**都會**看到的結果。它只排除了嚴重的卡故障,再細就排除不了了。
  - *同卡、同 shape(決定性)。* medium 自己的 **pilot** 就跑在 hip 5 上,記錄到 **0/21 dropouts**,而
    medium 在同一張 hip 5 上的 remeasure 卻是 28 %。同一張卡、同一個 shape、同一個 kernel —— 所以卡不
    可能是那個具鑑別力的變數。兩者之間不同的是 warm-up 的牆鐘時間(pilot 的 anchors 是慢 2.9–6.3× 的
    config,給出 9.31–20.26 ms 的 warm-up,對比 medium champion 的 3.2 ms),而那正是所提出的機制。

  **hip 5 獲得平反** —— 靠的是第二個測試,不是第一個。
- **Host CPU 負載。** 在 224 核的 2.6–5.9 % 負載、其餘 GPU 閒置的情況下重現(§7.1b campaign)。
- **Rotating buffer。** 既非必要也非充分 —— 但它確實讓 medium 確定性地付出約 12 % 的代價(420 MB 的
  working set 超出 MALL),那是另一個獨立、非隨機的效應。
- **量測之間的 sleep,以及 config 專屬性。** 兩者都被 probe 排除。

#### §7.1b.1 GA 搜尋未受影響 —— 已查核,機制也解釋了原因

調查的 agent 提出過一個疑慮:GA 搜尋期間每一個候選都用同一個 321-enqueue warm-up,若成立會遠比一個
remeasure 缺陷嚴重。**artifact 推翻了它。** `[CODE AUDIT]` medium 在全部 **20** 個已完成 run
(2 arms × 5 seeds × 2 P0 levels;較早的草稿寫 15,漏掉四個 arm×level 區塊中的一個)裡的 `best_fitness`:


| campaign | per-seed `best_fitness` (GFLOP/s) |
|---|---|
| capped G | 13,679 · 12,545 · 15,255 · 12,606 · 13,695 |
| capped F | 13,826 · 12,816 · 15,329 · 14,122 · 13,449 |
| native G | 14,479 · 14,195 · 14,013 · 15,407 · 14,523 |
| native F | 14,369 · 14,177 · 14,387 · 13,536 · 15,166 |


二十個全部落在 12,545–15,407,與 ~14,350 這個**完全暖機**的數字、以及 remeasure 的 clean mode 一致。
沒有任何一個顯示劣化的特徵。

這正是 §7.1b 的機制所預測的。GA 在單一個長壽命的 invocation 內 benchmark 數千個候選,所以**卡全程都是
熱的**;remeasure 則是在一個全新、短命的 process 裡 benchmark 一個 config,因此**每次都從冷開始**。

**ARGUMENT REPLACED 2026-08-13(§13.6)。** 光靠 `best_fitness` 的落點區間**並不能**確立這一點:
`best_fitness` 是約 8,500 次評估的*最大值*,因此恰恰是對單向*向下*汙染最穩健的統計量 —— 它無法證明
個別候選的評估沒有被低估,而被低估的評估正是會敗壞*哪一個*候選勝出的東西。較早的草稿曾以 Gen0 到
final 的梯度來論證;該論證**已撤回**(`best_gflops_so_far` 依構造即為單調,所以 mode 樂透會預測到同樣
的觀察)。有效的證據是:

- **`generation_Q_median_any_valid`** —— 每代約 510 次評估的中位數,一個 28–48 % 的乘性汙染物會壓低它
  並使它不穩。medium 落在兩個免疫 shape 的區間**之內**:代與代之間的平均 |Δ| medium 為 5.58 % /
  4.61 %,large 為 6.98 % / 6.11 %,tiny 為 6.50 % / 4.21 %。
- **一個由 warm-up 時間導出的曝險上界** —— `cumulative_complete_evals` 在**同一個** client invocation
  內每代推進約 508–512、每個 solution 約 6.4 ms 的 GPU 工作。不論那個短視窗效應是什麼,它**每個
  invocation 只付一次**,持續時間量級是 sweep 拐點所隱含的約 50 ms,所以它大約只能碰到約 510 個
  solution 中的前 8 個(**約 1.6 %**),對比全新 process 之 remeasure 的 28–48 %。*(2026-08-13 改寫:
  算術不變,但不再預設有時脈斜坡 —— 見 §7.1b 開頭的區塊。它靠的是 sweep 實測到的約 50 ms 拐點,不是
  DPM 模型。)*

**champion 的*解析*未受汙染,這是記錄在案的事實,不是推論。** `[CODE AUDIT]`
`selection_candidates` 在 **40/40 個 arm-entry 中都恰好只有一筆**,而解析出的 `canonical_hash` 在
**40/40** 中都落在該臂的 `best_individual_hashes` 裡。

> **PATH CORRECTED 2026-08-13。** 較早的草稿引用的是 `optimization_result.json` 的
> `resolution_provenance`。該欄位在**全部 45 個**這類檔案中**根本不存在**(不是「存在但為空」,較早的
> 寫法是那樣說的),所以當時寫下的主張無法由它所指的路徑重現。可重現的路徑是
> `champion_interleaved.json` → `arms.{G,F}.resolution_provenance.selection_candidates`
> (20 檔 × 2 臂 = **40 個 arm-entry**,分母就是這樣來的),再與各臂自己 `optimization_result.json` 裡的
> `best_individual_hashes` 對照。兩個計數都已由更正後的路徑重新推導,維持 **40/40 與 40/40 不變**;
> 錯的只有引用。

那條 selection
rule —— 它*確實*會讀取已被證明汙染的單次 `original_final_gflops`(seed 24001 medium G 記錄的是
**2,961.87 GFLOP/s / 45.3 µs**,而該 config 的暖機值約 9.9 µs,約 4.6× 的落差,其成因為
`NOT_EVALUATED` —— 較早的草稿讀作「與一張跑在約 450 MHz 的卡一致」,已於 2026-08-13 刪去,因為直接
追蹤發現**每一次**重複都在 1512–2065 MHz)—— 在**每一個實例中都是空轉的**。被汙染的數值有被記錄下來,
但它沒有仲裁到任何東西。

**後果:** champion 的*選擇*與*解析*未受汙染。搜尋過程中低殘餘率的汙染並未被排除,另見 §7.1b.3 說明
它為何可能不是 arm-symmetric。

#### §7.1b.2 可救性 —— 汙染是單向的,資料可回復

上述每一個機制都只能讓量測**太慢**,絕不會太快。在 warm-up sweep 中,**25 次短 warm-up run 的最大值,
與完全暖機 run 的中位數相差在 0.5 % 以內**。所以能回復真值的估計量是在形成 F/G 之前,逐臂取
**repeats 的最大值**。

- ~~在觀察到最糟的 dropout 率(48 %)下,P(7 次 repeat 全部 dropout)= 0.6 %;現有的臂沒有任何一個是
  7 次全 dropout,所以每一臂都可回復。~~ **RETRACTED 2026-08-13(§13.3)。** 兩半都是錯的。
  **反例:** capped campaign 1、seed 24005 arm F 是
  `4685, 7164, 2944, 2870, 10535, 2166, 5456` —— **七次全部被汙染**;`max` 給出 10,535,對照同一個
  config 在 campaign 2 的乾淨值 13,407,**回復不足 21.4 %**。而且那個 i.i.d. 的
  `0.48⁷ = 0.6 %` 計算並不適用:同一視窗內的 repeats 是 **governor-correlated** 的,所以 governor
  可以在整個視窗裡都維持在低狀態。
- 這是**純粹對已收集資料的再分析** —— 不需要 GPU 時間、不需要重跑。
- 交叉檢核:把 max 估計量套用到原始 campaign,會把 medium 的 per-seed F/G 從 0.36×–2.12× 收斂到 ±7 %
  以內(見 S14 design §13.3 的 cross-campaign 表),而第二次獨立 campaign 以預註冊的中位數量測也得到
  相同結論。兩條不同的路徑一致。

**但它取代了預註冊的 median-of-7,因此在套用之前需要 owner 決策與一份記錄在案的 deviation ——
而且屆時必須一致地套用到全部三個 shape**,不能只套在數字會變好看的那個 shape 上。

長期而言更好的修法是把 warm-up 以**牆鐘時間**指定(或對 10 µs 的 kernel 用 ≥ ~5,000 次 enqueue)。那會
動到 hash-locked 的 config,所以屬於協定變更,不在本批資料再分析的範圍內。

**什麼是無法被測試的(明說,不含糊)—— SUPERSEDED 2026-08-13。** 這一段原本寫的是:決定性的確認會是
用 `rocm-smi --setperflevel high` 把 clock 釘住,而該指令靜默地變成 no-op(容器內 `/sys` 唯讀、沒有
host root),使得原本預期的「pinned」臂實際上只是第二個 control,它的 23/70 dropouts 是一次複製,不是
一次反證。**這個框架現在有兩處是錯的。** 第一,那個變成 no-op 的 probe,其 null 不是弱證據,而是
**無資訊**:它的時脈軌跡與 control 完全相同,75 % 的採樣低於 200 MHz,所以什麼都沒被釘住,也就無法從
中往任一方向讀出任何東西。第二,釘住 clock 已不再是決定性的檢驗,因為**一次在實際進行中的 remeasure
上所做的直接 1 kHz 時脈追蹤,已經徹底否證了時脈說法**(Spearman −0.32,dropout 的時脈中位數比乾淨的
重複*更高* —— 見 §7.1b 開頭的區塊)。現在去釘 clock,只是在檢驗一個資料已經不利於它的假說。而且它還
需要透過 `pp_od_clk_voltage` / `amd-smi` 取得對卡的**寫入權限**,那是一次 governance escalation,不是
先前所描述的十分鐘 `sudo` 工作。

*Source: `[CODE AUDIT]` `ClientParameters.ini` (`num-warmups`, `enqueues-per-sync`, `sleep-percent`,
`rotating-buffer-size`, all three shapes); `medium_remeasure_root_cause.md` (full write-up, probe drivers
and raw sweep data); `stage3_*/stage5_*/seed_*/medium/optimization_result.json` (`best_fitness`);
`champion_interleaved.json` → `remeasure.{G,F}` (dropout ratio range, all shapes).*

#### §7.1b.3 Arm-asymmetric 汙染 —— 「配對比值會抵銷」的辯護不成立

**2026-08-13 新增(§13.6)。本節撤回本索引先前所做的一項主張。**

較早的草稿論稱:既然汙染嚴格是單向的,它也就是 arm-symmetric 的,因此會在配對的 `F/G` 比值中抵銷。
`[CODE AUDIT]` champion 驗證的數字直接與此矛盾。以下是每個 medium 臂的 `Data/00_Final.csv` 裡的
`WinnerGFlops` —— 同一條 client 路徑,每臂一次量測:


| seed | baseline (G) | guided (F) |
|---|---:|---:|
| 24001 | **2,961.9** | 13,590.7 |
| 24002 | **8,846.0** | 12,773.8 |
| 24003 | **4,210.4** | **8,384.2** |
| 24004 | 12,516.2 | 14,040.5 |
| 24005 | 11,542.6 | 13,359.8 |
| **median** | **8,846.0** | **13,359.8** |


baseline 臂被劣化的頻率遠高於 guided 臂。(此處刻意不給出「被汙染的臂」的計數:那取決於對單次數值所
假設的乾淨參考值,而兩位 reviewer 分別數成 3/5 與 4/5。中位數本身已足以說明重點,不需要那個判斷。)

**正確的措辭,取代先前的主張:** 汙染是**單向的**;它**是否為 arm-symmetric 則是 `NOT_EVALUATED`**,
而且無法回溯檢查,因為 per-generation 的 benchmark CSV 沒有保留(只有 `00_Final.csv`)。

**給任何要依本索引起草的人的警告:** `original_final_gflops` **絕不可**被當成 endpoint。以這些數字來看,
guided 臂會純粹因為汙染而顯得好得驚人(中位數 13,360 vs 8,846)。它不是 endpoint —— endpoint 是 7×
interleaved remeasure —— 而 §13.6 要求報告必須明說這一點,以免未來有讀者去取用它。

*Source: `[CODE AUDIT]`
`stage3_{baseline,guided}/seed_*/medium/1_BenchmarkProblems/*/Data/00_Final.csv` → `WinnerGFlops`;
S14 design §13.6。**不要用 `**/Data/00_Final.csv` 這種 glob** —— 它會一併命中
`remeasure_work/{G,F}/…` 的副本,單是 seed 24001 arm G 就會回傳三個值(2961.87、6195.34、
13436.4),而不是那一個 champion 驗證值。上表用的是最上層的 `1_BenchmarkProblems` CSV,
也就是 `resolution_provenance.selection_sources.candidate_matrix_csv` 所指的同一個檔案。*

#### §7.1b.4 `η_medium` 的完整 provenance,以及 warm-up 機制**無法**解釋的一個殘留

**2026-08-13 新增,同日重新定框。** §13.4 說三個 `η_s` pin 都是「pilot 意外」。本小節給出 medium 這一
側的原始 artifact 細節,並記錄一項**不利於** warm-up 說法完整性的落差。⚠ **重新定框的部分:** 當初寫下
時,這個殘留看起來像是一個原本運作良好的時脈斜坡說法裡的單一異常。§7.1b 開頭的直接時脈追蹤此後已
**否證了那套說法**,所以下面這個殘留不再是一個孤立的謎題 —— 它是好幾個彼此獨立、指向「成因不是時脈」
的訊號之一。它所檢驗的 *warm-up 時間*相關性則不受影響。之所以寫在這裡,是因為它目前是本檔案中最強的
反證,不能只留在對話裡。

**Provenance。** `[CODE AUDIT]` `agent_run/260807-s14-baseline-run/stage2_noise/computed.json`,產生於
2026-08-07T23:57:03Z–2026-08-08T00:06:21Z(牆鐘 558 s),來自 `config/s14-smoke.yaml`,跑在
`HIP_VISIBLE_DEVICES=5`。由 `scripts/compute_per_shape_noise.py:30` 計算。

**pilot 的設計:3 anchors × 7 repeats = 21 次量測。** 殘差是**在 anchor 之內**取
`|log y − median_r log y|`,匯集成 21 筆,再取 `P95(..., method='linear')`。


| anchor | hash | medium GFLOP/s(7 次的中位數) | 自身 max/min | kernel | 321 × kernel |
|---|---|---:|---:|---:|---:|
| 1 | `14477b97…` | 4,629.1 | 1.0089 | 29.0 µs | **9.31 ms** |
| 2 | `31a76db9…` | 3,199.9 | 1.0028 | 41.9 µs | **13.46 ms** |
| 3 | `dbe08bc4…` | 2,127.0 | 1.0040 | 63.1 µs | **20.26 ms** |
| *(champion,供對照)* | — | *~13,500* | *0.36×–2.12×* | *9.9 µs* | ***3.19 ms*** |


anchor 2 的原始七筆:`3195.3, 3200.6, 3199.5, 3199.9, 3198.7, 3200.3, 3204.4`。

**三個 confounder 是由 artifact 排除的,不是假設的。** 這個 pilot 用的是 (i) **同一張卡**,GPU 5;
(ii) medium 用的是與 production **相同**的 `rotating-buffer-size = 4096`
(`driver_status.json → environment.DUCTILE_PERSIZE_RBS`);以及 (iii) **每次 repeat 都是全新的
client** —— `computed.json → R_s_formula` 寫的是*「median of all 21 GFLOPS values from 3 anchors x 7
**fresh-client** repeats」*。最後這一點,殺掉了那個原本很自然的假說:pilot 在各次 repeat 之間一直是熱
的,而 remeasure 每次都重新冷啟動。它不是這樣。**乾淨的 pilot 與被汙染的 remeasure 之間,唯一受控的
差異就是 config 的快慢,也就是 warm-up 的牆鐘時間。**

**⚠ 機制無法解釋的那個殘留。** 把 warm-up sweep(§7.1b)內插到這些 anchor 的 warm-up 時間上,預測
pilot **不應該**是乾淨的:


| anchor 的 warm-up | sweep 推得的 dropout 率 | 7 次中的期望 dropout 數 | 實際觀察 |
|---:|---:|---:|---:|
| 9.31 ms | ~23 % | 1.6 | **0** |
| 13.46 ms | ~12 % | 0.8 | **0** |
| 20.26 ms | ~10 % | 0.7 | **0** |
| **合計** | | **≈3.1 / 21** | **0 / 21** |


在 Poisson 近似下 `P(0 | λ = 3.1) ≈ 4.3 %`。不太可能,但並非不可能 —— 不過這意味著 warm-up 說法解釋了
這個效應的*方向與主體*,卻在 **9–20 ms 這一段過度預測了 dropout**。有兩個可能的出路,**兩者都是
`NOT_EVALUATED`**:

1. **sweep 是在 `RBS = 0` 下做的;pilot 與 production 都在 `RBS = 4096`。** 光是 RBS 0 就把水準從
   12,430 推到 14,153(+14 %),所以這個 sweep 是一條在*不同 estimand* 上的曲線,未必能轉移。能一舉
   定案的檢驗是 5,136 warm-ups @ RBS-4096 的 probe(§13.7 項目 2)。
2. **這些 anchor 是不同的 config,不只是比較慢的 config**,它們可能在 kernel 時長以外的軸上也不同。

**這一點該怎麼報告:** warm-up **相關性**在方向上、以及在兩個極端(3.2 ms → 48 %、601 ms → 0 %)上,
再加上卡內對照,都獲得良好支持,但它在中段**並沒有**經過量化校準。不要把這個 sweep 當成預測模型呈現。
對 9–20 ms 這一段,`NOT_EVALUATED` 才是誠實的狀態 —— 而自 2026-08-13 起,對曲線上*每一點*的**成因**
也是如此。

**不論如何都倖存的部分:** `η_medium = 0.42 %` 是在比它所治理的那個 champion 慢 2.9–6.3× 的 config 上
量出來的,而且比該 champion 自己乾淨模態的 P95(0.0116)還緊 2.8×。不論 9–20 ms 那一段的解釋是什麼,
這一點都成立。

*來源:`[CODE AUDIT]` `agent_run/260807-s14-baseline-run/stage2_noise/{computed.json,driver_status.json,raw_repeats.jsonl}`;
`scripts/compute_per_shape_noise.py:30`;sweep 取自 §7.1b。kernel 時間由
`2·256·256·1024 FLOP ÷ GFLOP/s` 導出。*


### §7.2 Large 7× remeasure(已量測、quarantined)

已量測 5/5;**尚未過完整 per-shape gate;two-sided,不下結論。**

Final-champion 各臂的 7×-median real-GFLOPS,以及 F-vs-G 對比(為何以 log-ratio 為分析量見 §5b):


| seed                      | G 中位數(GFLOP/s) | F 中位數(GFLOP/s) | **F/G ratio** | **變化率**    | log-ratio `ln(F/G)`    |
| ------------------------- | -------------- | -------------- | ------------- | ---------- | ---------------------- |
| 24001                     | 575,916.0      | 534,364.0      | 0.9279        | −7.2 %     | −0.0749                |
| 24002                     | 539,476.0      | 545,938.0      | 1.0120        | +1.2 %     | +0.0119                |
| 24003                     | 527,060.0      | 559,859.0      | 1.0622        | +6.2 %     | +0.0604                |
| 24004                     | 537,433.0      | 511,975.0      | 0.9526        | −4.7 %     | −0.0485                |
| 24005                     | 535,467.0      | 535,810.0      | 1.0006        | +0.1 %     | +0.0006                |
| **中位數**                   | —              | —              | **1.0006**    | **+0.1 %** | **+0.0006**            |
| *(原始比值的平均 —— 有誤導性,見 §5b)* | —              | —              | *0.9911*      | *−0.9 %*   | *(幾何平均 0.9900,−1.0 %)* |


預註冊的 directional-consistency 各分項(每項都要求 ≥4/5 為正):


| 分項                                        | 為正的 seed 數 | 判定   |
| ----------------------------------------- | ---------- | ---- |
| Gen0 best                                 | 1/5        | fail |
| gen-10 best                               | 2/5        | fail |
| AUC(best-so-far,共同 eval budget)           | 3/5        | fail |
| final champion(7× median)                 | 3/5        | fail |
| final **non-regression** `F ≥ G·e^{−η_s}` | 用 pinned `η` 為 **5/5**;用 large 自身的窗內實測重複性為 **3/5** —— 見 **§7.2a** | **conditional —— 未解決** |
| final **improvement** `F > G·(1+δ_s)`     | 0/5        | fail |


- **3/5 為正、中位 ≈ +0.1 %** → final-champion 這一項未達預註冊 ≥4/5 正向門檻。所有分項皆未達;
non-regression 則五個 seed 全數通過。
- per-seed 變異為 **0.93×–1.06×**,亦即**每一個 seed 都落在 η_large = 12.28 % 之內**
(non-regression floor `F/G ≥ 0.8844`)。與 medium 不同 —— medium 的 per-seed 差異是 instrument-invalid
而非真實的(§7.1a)—— **large 的 per-seed 差異沒有任何一個能在該 shape 自身的雜訊邊界之上被解析出來**
—— 在 n=5 下兩臂是「無法區分」,而不是「方向不一致」。
- baseline 臂自己只橫跨 527,060–575,916 GFLOP/s(相對中位數約 ±4.4 %),對比 medium 的
6,137–13,495(2.2× 幅度)。原因:large(2304×1024×214336)是 **main-loop dominated**,GA 幾乎不論
seed 都落進同一個效能 basin。seed 之間本來就沒有多少空間留給 Gen0 prior 去移動,這也框住了 guided
效應的可能上限。
- large 是所有 shape 中 activated gene **最多**的(5 個:`PrefetchGlobalRead`、`TransposeLDS`、
`UnrollLoopSwapGlobalReadOrder`、`GlobalReadVectorWidthA/B`;見 §3.5/§3.6),結果淨效應仍 ≈ 0。這正是 sparsity finding 的實務
後果:即使是訊號供給最充足的 shape,模型訊號也不足以改變結果。



#### §7.2a Large 的 non-regression 通過,條件建立在一個未驗證的 margin 上

**這牽涉到本研究中唯一在任何地方通過的預註冊分項,而且它尚未解決。引用那個 5/5 pass 時,絕不可略去它
所條件依賴的 margin。**

`[CODE AUDIT]` `η_s` 是 pilot 推導出來的(3-anchor × 7-repeat,§3.8),而且**從未針對它實際在 gate 的
那些 remeasure repeats 重新檢查**。§7.1a 由那些 repeats 重算了它們。把兩個 margin 分別套用到 large 的
non-regression 判準 `F/G ≥ e^{−η}`:


| seed | F/G | pinned `η = 0.1228` → floor 0.8844 | empirical `η = 0.0269` → floor 0.9735 |
|---|---:|---|---|
| 24001 | 0.9279 | PASS | **FAIL** |
| 24002 | 1.0120 | PASS | PASS |
| 24003 | 1.0622 | PASS | PASS |
| 24004 | 0.9526 | PASS | **FAIL** |
| 24005 | 1.0006 | PASS | PASS |
| | | **5/5 PASS** | **3/5 — gate not met** |


**為什麼這不是「換上比較好的那個數字」就好。** 這兩個估計量量的是*不同的變異成分*,而且哪一個才對並不
顯然:

- **經驗值** 0.0269 來自同一個 process、同一張卡上的 7 次 repeat,整個 interleaved 視窗**橫跨約 106 s**
  (`[CODE AUDIT]` `stage3_baseline/seed_24001/large/champion_interleaved_raw.jsonl` 中首末時間戳,
  14 筆記錄 —— 相鄰兩次抽樣間隔約 15 s;較早的草稿寫「相隔約 27 s」,那是 medium 的視窗、不是 large 的)。
  這些 repeats 是**相關的**:它們排除了視窗之間的 drift、跨數小時的熱狀態變化,以及跨日的變異。因此它
  很可能是真實量測雜訊的**下界** —— 這會讓 3/5 的判定過於嚴苛。
- **釘住值** 0.1228 來自一個 3-anchor × 7-repeat 的 pilot,其設計或許涵蓋了視窗內 repeats 看不見的來源
  —— 但它是在不同的量測上擬合出來的,而且從未對照這些量測驗證過。

要在兩者之間裁決,需要一個**並不存在的、跨視窗的可重複性量測**。

**站得住的報告方式(建議,待 owner 決策):** 在**兩個 margin 之下**同時陳述 gate 結果,揭露兩者判定不
一致,並明白指出預註冊的 margin 從未對照它所 gate 的量測驗證過。只報 5/5 pass,會把一個建立在未驗證常數
之上的結果呈現得像已成定論;只報 3/5,則會把一個雜訊的下界當成雜訊本身。

**注意它與 medium 的不對稱。** 在 medium 上 pin **緊了 288×**(§7.1a),那會製造 false positive;在 large
上它 **鬆了 4.6×**,那會製造 false pass。同一道預註冊 gate、在兩個 confirmatory shape 上,同時出現兩個
方向的誤差,原因相同:`η_s` 從未對照它所 gate 的量測驗證過。

*Source: `[CODE AUDIT]` `stage3_baseline/seed_*/large/champion_interleaved.json`
(`F_over_G_median_ratio`, `remeasure.{G,F}` raw repeats); `noise/per_shape_noise.json`;
recomputation of `P95(|log y − median log y|)` per §3.8's own formula.*


#### §7.2.1 Gen0 分項(1/5)的 root cause —— guidance 移動的是中心,GA 讀的是極值

Gen0 這一項最具診斷價值,因為 Gen0 **正是**處理介入的位置 —— guided 臂與 baseline 的差異**只有**
Gen0 的抽樣分布。它得到 1/5,也就是五個 seed 中有四個 guided Gen0 反而較差。把 Gen0 拆成**中心**
統計量與**極值**統計量就能解釋:


| seed               | Gen0 median Q — G | Gen0 median Q — F | **中心 F/G** | Gen0 best GFLOP/s — G | Gen0 best GFLOP/s — F | **極值 F/G** | valid/512 G | valid/512 F |
| ------------------ | ----------------- | ----------------- | ---------- | --------------------- | --------------------- | ---------- | ----------- | ----------- |
| 24001              | 0.8887            | 0.9052            | **1.0186** | 464,638               | 385,612               | 0.8299     | 489         | 483         |
| 24002              | 0.8797            | 0.8970            | **1.0197** | 411,852               | 439,016               | 1.0660     | 480         | 488         |
| 24003              | 0.9290            | 0.8799            | 0.9471     | 409,646               | 398,118               | 0.9719     | 485         | 487         |
| 24004              | 0.8883            | 0.9087            | **1.0229** | 449,519               | 379,399               | 0.8440     | 485         | 480         |
| 24005              | 0.8841            | 0.9187            | **1.0390** | 435,831               | 425,865               | 0.9771     | 486         | 491         |
| **中位數**            | —                 | —                 | **1.0197** | —                     | —                     | **0.9719** | —           | —           |
| **F > G 的 seed 數** | —                 | —                 | **4/5**    | —                     | —                     | **1/5**    | —           | —           |


*Source:*`stage3_{baseline,guided}/seed_*/large/trajectory.jsonl` *的 generation-1 record
(*`generation_Q_median_any_valid`*、*`best_gflops_so_far`*、*`generation_any_valid_count`*)。*

兩欄的方向**穩定地相反**:

- **guidance 對它被設計要移動的量確實有效。** guided 臂在 4/5 個 seed 上讓*典型的* Gen0 候選變好
(中位 +2.0 %)。prior 做到了 prior 該做的事:把機率質量往 S11 模型評價好的 configuration 移。
- **但 GA 不消費這個量。** selection 讀的是*上尾* —— Gen0 的 `best_gflops_so_far` 是**約 485 個有效
抽樣的最大值**,一個極值統計量。極值主要由抽樣分布的**離散程度**決定,而非其中心位置。集中機率質量
(任何非均勻 prior 都會這麼做)會抬高平均、同時壓縮上尾,於是即便中位數上升,期望最大值仍可能下降。
guided 的 Gen0 best 在 4/5 個 seed 上較差(中位 −2.8 %)。
- **這不是 validity-rate 造成的假象。** 每 512 抽樣的有效候選數為 480–489(baseline)vs 480–491
(guided) —— 兩臂產生的可執行 config 數在統計上無法區分,所以差異不是「guidance 產生了更多無法
build 的 kernel」。
- **這正是 entropy cap 當初要框住的機制,而且它正往當初預期要防的方向作用。**
`ENTROPY-CAP-20260810` 把 ρ 上限訂在使 `H_norm(p1) ≥ 0.80`,目的就是阻止 prior 壓垮 Gen0 多樣性
(§3.4)。資料顯示這個張力是真實的,而且 cap 並未消除它:即使只是一個在 29 個 gene 中對 5 個施加、
且 entropy 損失 ≤20 % 的 prior,也足以在 Gen0 最大值上付出約 2.8 % 的代價、換到中位數約 +2.0 %。

**這個 root cause 的誠實界線。** 在 n=5 之下,4/5 與 1/5 個別都不顯著(公正硬幣得到 ≥4/5 的機率為
3/16 ≈ 0.19)。真正站得住的是**配對對比**:在同一批 run 上,中心與極值往相反方向移動,方向與極值論證
的預測一致,且兩個統計量各自都在 5 個 seed 中的 4 個成立。此外 Gen0 數值是單次、未重測的數字,因此
帶有 §5 所述的 winner's-curse 偏差 —— 其量級不可與上表 7×-remeasured 的 final-champion 數字直接
相比。要正式確認此機制需要針對性的量測(例如逐臂的完整 Gen0 fitness 分布,或 Arm-S shuffle control,
§3.9),此處為 **not evaluated**。

**這對設計的意涵。** 若此機制成立,則 per-gene 的 Gen0 prior 正在被一個它並不優化的指標評分:它改善
*平均*抽樣,而 GA 只保留*最好*的那一個抽樣。這是關於 guidance 與 GA selection rule 之間耦合關係的
陳述,而不是關於 S11 模型對不對的陳述 —— 而且它可以獨立於「guidance 訊號是否稀疏」之外被檢驗。

### §7.3 S11 finding —— 封存的 max-reducer `analyze` 無法對這批資料 emit locked guidance

*(已驗證、報告可引用。下述機制的第一原理走查見 §3.4a。)*

一份 out-of-band 平行重製(`agent_run/260803-…/parallel-analyze/`,VERIFICATION.md)在三個驗證軸上證明
與封存序列路徑逐位元一致,且快約 3 個數量級(156.7 s vs 數天):

- **(a)** 對封存 O(N²) oracle 的 per-replicate 位元一致(4 個 stochastic pass、workers 1/3/7、0 失敗);
- **(b)** partition-independence —— `agent_run/260803-ductile-factorized-guidance-s11/parallel-analyze/out/passes.w40.json`
  與 `passes.w72.json` 逐位元相同(`[CODE AUDIT]` 兩者 md5 皆為
  `ef6a016a688512f4f9ad0ad6cb660340`,2026-08-13 重新驗證)。舊稿引用的檔名 `passes.json` 並不存在;
- **(c)** 封存樹未變。

它到達**相同的終端** `AssertionError`**,位於封存** `s11/guidance.py:95`**(**`select_global_lambda`**)**。決定性
判定 = **(A) FAITHFUL**(VERIFICATION.md §5.4:完全走封存 ECDF 的路徑產生逐位元相同的
`guidance_inputs`/`gate_calls`/λ 曲線與同一 assertion —— 非平行端瑕疵)。

根因:只有 3 個 gene 通過 7 道 model gate,但封存的 **0.80 normalized-entropy floor 對帶訊號的低基數
gene 結構性不可達** —— PrefetchGlobalRead(4 候選 / 2 trusted → 熵上限 0.7345)與 DepthU(6/2 → 0.6576)
—— 在**任何 λ、任何資料下**皆然(這是「候選少 / trusted 少 + uniform baseline」的數學性質;光
PrefetchGlobalRead 一個,在 +88% sensitivity margin、每道 stochastic gate 以 ≥3× 通過的情況下,就把熵
卡在 0.7345 < 0.80 而強制 assert)。

**這正是促成** `ENTROPY-CAP-20260810` **的 entropy-floor/稀疏性張力**(binary floor → per-gene mixture cap
ρ),用於 per-shape S14 路徑 —— 此處由封存 pipeline 本身獨立證實。

依 governance,此 assertion **回報、不修補**;封存樹未動。意涵:序列 `analyze`(跑了數天)會撞上完全相同的
assertion 且一無所獲 —— 平行版在幾分鐘內就確立了此結局。

#### §7.3.1 max-reducer 的結果告訴我們什麼(insights)

這次 run **沒有產出 guidance artifact**,但它遠非沒有資訊 —— 它是一次乾淨的、走封存 pipeline 的模型訊號
探測。可得出五點。

**(1) 稀疏性與 reducer 無關 —— 不是「per-shape 切分」造成的 artifact。**
aggregate **max** reducer 匯集全部三個 size(每個 config 以其*最佳* size 計分),是本協定能建構的最豐富
訊號。它仍然只浮現 **26 個可測 gene 中的 3 個**。per-shape 則是 0/2/5。這先行擋掉了一個自然的質疑
——「你們切 per-shape 把訊號稀釋了」:稀疏性在**最未被稀釋**的 reducer 下依然存在。

**(2) 兩個獨立 reducer 選出同一批 gene —— 稀疏訊號是穩定的,不是雜訊。**
max-reducer 的存活者 {PrefetchGlobalRead, UnrollLoopSwapGlobalReadOrder, DepthU} **全部**落在 per-shape
的 activated 聯集 {DepthU, 1LDSBuffer} ∪ {PrefetchGlobalRead, TransposeLDS, UnrollLoopSwapGlobalReadOrder,
GlobalReadVectorWidthA, GlobalReadVectorWidthB} 之內。兩種不同的匯總方式收斂到同一小群 gene,是
**「少數有訊號的 gene 能被可重現地辨識出來」的正向證據**。(3 個中有 2 個是 large 的頂尖 gene、1 個是
medium 的 —— 與「最強的 per-gene 對比來自 large」一致;此機制屬詮釋,非證明。)

**(3) 失敗的原因不是證據薄弱 —— 存活的 gene 以很寬的 margin 通過。**


| gene                          | S_g(floor 0.05) | S / own-null p95 | S / familywise p95 | bootstrap CI half-width(上限 0.025) | best/worst recurrence(下限 0.90) |
| ----------------------------- | --------------- | ---------------- | ------------------ | --------------------------------- | ------------------------------ |
| PrefetchGlobalRead            | 0.0942(+88%)    | 10.63×           | 3.14×              | 0.0066                            | 1.000                          |
| UnrollLoopSwapGlobalReadOrder | 0.0900(+80%)    | 11.86×           | 3.00×              | 0.0068                            | 1.000                          |
| DepthU                        | 0.0537(+7.4%)   | 5.58×            | 1.79×              | 0.0087                            | 1.000                          |


每一道 stochastic gate 都以 **1.79×–11.86×** 通過,CI half-width 在上限內 3–4 倍,recurrence 完美。所以
pipeline 不是因為沒訊號而停 —— 它停在**最後一步**:把證據轉換成抽樣分布的時候。

**(4) 可移轉的設計教訓:固定的 entropy floor 與低 arity 的 gene 天生不相容。**
在 `n` 個候選、`k` 個 trusted 值、baseline 為均勻的情況下,最發散的可行 `p1`(λ=0、全強度)其 `H_norm`
存在一個**只由** `(n,k)` **決定的上限** —— (4,2) 是 `0.7345`、(6,2) 是 `0.6576`;即使對 (6,2) 取遍*所有*
嚴格正的 baseline 求上確界,也只到 `0.7435`。因此固定 floor 0.80 **等於默默禁止引導任何該 arity 的 gene
—— 在任何 λ、任何資料下,無論其證據多強**。這道 gate 把「保留多樣性」和「候選值要夠多」混為一談:它對
`k/n` 施加了一個未載明的隱含要求。修法只有兩條:(i) 讓 floor **相對於各 gene 可達到的最大值**表示,或
(ii) 限制*強度*而非排除 gene —— 後者正是 `ENTROPY-CAP-20260810`(§3.4)。

**(5) 它獨立驗證了 ENTROPY-CAP 是必要的、不是投機的。**
該 amendment 是在 per-shape 路徑上設計的。這次 run 以**未修改的封存 pipeline、在不同的 reducer 上**重現
了同一個結構性失敗 —— 所以該 amendment 修的是一個真實、通用的缺陷,而非閃避一個方便的障礙
(非 gate-shopping)。

**它不能告訴我們什麼(誠實界線)。** 它不產出 locked guidance,故無法作為 S14 的替代 guidance 來源;
它對真實 GPU 效應毫無著墨;且其 3-gene 集仍是模型空間、per-gene marginal 的量(epistasis-blind、
survivor-frame),故依 charter §8.5 只能把 negative 定位到 *marginal-loss*,而非「模型沒用」。

*來源:*`parallel-analyze/VERIFICATION.md` *§5.1–§5.5;*`out/passes.w72.json`*;*`out/diag-lambda2.w72.json`*;*
`derivation-manifest-capped.json` *per_shape_activation_log。*

---



## §8 已知 caveat / 限制(供 Discussion 章節)

- **Modest power**(5 對 paired seed;非顯著性)、**單一 development cluster**、**限受測 shape** —— 不一般化。
- **「P0-capped=512 variant」** 界定;效應是在 P0=512 下量的(**treatment×budget 交互作用**)——
native-11,405 addendum 量化其稀釋 / 穩健性。
- **Max-reducer S11** 帶 **construct-validity caveat**(這是為何 per-shape guidance 改由 per-size scores
重導、繞過 aggregate max reducer);reducer-version closeout 報告時附此 caveat,且**不餵 S14**。
- **順序 confound:** baseline(G)對所有 seed 都先於 guided(F)跑;**interleaved 7× remeasure** 才是控制
漂移的 champion real-GFLOPS 比較。報告要明講。
- **Physics-direction 不歸因**,除非 conditional Arm S 觸發且 F 同時勝 G 與 S;否則歸因限「capped
factorized initialization bundle vs baseline」(完整 physics-direction 歸因是下游 S20 的 registered 職責,
目前 frozen)。



### §8.1 Host-reset / 機房供電故障(2026-08-11,實質限制 scope)

自 03:37 UTC 起,機器每 **57–58 分** 硬重置一次(其後 12 小時約 11 次),先前間隔以天計。

原因 —— **外部 AC 斷電,與本工作負載無關**(證據):

- BMC:`Last Power Event: ac-failed`;`restart_cause: power-up due to always-restore power policy`;
watchdog **Stopped**。
- 兩次重置(11:18、14:22)發生在 **large 沒在跑時**(GPU 閒置 / 只有 CPU 的 S11)—— 直接反證負載造成。
且 baseline 先前曾用同樣 5-GPU large 負載連續跑 20 小時、零重置。
- 無關機程序 / 無 reboot 指令 / 無 OS watchdog / 無 kernel panic;**其他所有使用者的容器也一起重啟**。
- 伴隨 `0000:35:05.0`(Intel PCIe Gen5 Port C)的 PCIe RxErr correctable 錯誤風暴。

對實驗的後果:

- `large` 第一代需 ~60–70 分 > ~56 分窗口,故有數小時 guided `large` 連第一個 checkpoint 都寫不出、每
週期從 gen 0 重來。
- 序列 S11 `analyze`(數天)同理跑不完。medium/tiny 不受影響(快、已完成)。
- **解決:** 供電轉穩後(出現 >70 分窗口),5 個 guided `large` seed 全部寫出第一個 checkpoint,現已能累積
進度。這是硬體/機房故障,需回報機器維運方;不是實驗設計或軟體缺陷。



### §8.2 Checkpointing(更正後的理解)

per-generation GA checkpointing 在 engine 中對**兩臂本就 native 且已啟用**(`ductile_backend.py` 設
`checkpoint_path` 並自動載入)—— 故啟用它**不造成 arm 不對稱**。

真正造成 gen-0 重來的是我方 resume driver 刪掉 shape 目錄(連 checkpoint 一起);已修(保留 + `--resume`,
真 GPU 上驗證:中途 kill → 「Resuming optimization from generation N」→ 以 pop_size 512、相同 weights
hash 完成)。

記錄哪些 seed 實際 resume 過。⚠️ **`checkpoint_resume_ledger.json` 並不存在** —— 2026-08-13 在
repo 與 container 內重新查核,從未有過這個檔名的檔案。這一行原本是寫給未來自己的**指示**,卻長得
像**引用**,而那比兩者都糟:它會讓讀者以為 resume 紀錄有被保留下來。實際存在的只有 deviation note
`agent_run/260809-s14-pershape-baseline/checkpoint_deviation.md`,那是唯一的書面紀錄。
**因此「哪些 seed 實際 resume 過」作為一份持久 artifact 是 `NOT_EVALUATED`**,必須在 closeout 前
由 run log 重建,否則報告必須明說這件事沒有被追蹤。atomic checkpoint 寫檔是我方 runner 內的 monkey-patch,**非** engine 編輯
(engine sha256 已驗證未變)。

### §8.3 Medium remeasure 於單一專用卡(GPU 5)執行

非各 seed 原始搜尋卡(2,3,4,6,7 當時被進行中的 guided `large` 佔用)。方法學成立,因預註冊要求 —— G 與 F
在**同一窗口、同一張卡**交錯 —— 已保留,且最終判準是**組內比值**,卡別 offset 抵銷。另:medium 是
**per shape**(每對完成即重測)而非 per seed 重測。記錄於 `medium_remeasure_deviation.md`。

### §8.4 Remeasure 驗證修正(`DEVIATION-REMEASURE-STOPLINE-20260812`)

`remeasure_interleaved_champion.py`(我們 run-root 下的腳本,**非**封存碼、**非** Lock A)原本斷言
「跑到 `n_gen=30` horizon」與「log 中含原生 early-stop 行」兩者互斥。實際上並不互斥:Ductile 在
`n_gen: 30` 上限**之外仍保留** `period: 5` 早停(`ductile/config/defaults.yaml`),因此停止條件可能
恰好在最後一代觸發。

三個 large/tiny remeasure 因此在**符合設計**的 run 上被拒(`generations_run=30` 且有一行 stop):
seed 24002(large、tiny)與 24005(large)。接著出現次生效應堵死所有重試 —— 第一次失敗寫下了
`champion_interleaved_status.json` 的 FAIL 紀錄,腳本的「artifact 已存在」守門於是拒絕了其後每一次
嘗試(seed 24005 large:00:37 至 01:45 之間 7 次重試全部死在這個殘留檔案,而非原本的 bug)。

修正內容(量測邏輯未動,只改 pre-flight 斷言):

- 守門改為檢查真正該成立的不變量 —— stop 行**至多一行**,且 run **不得超過**第 30 代 ——
而不是禁止該邊界情況;
- artifact 新增記錄 `stopped_at_horizon` 使邊界情況可稽核,`termination_reason` 同時陳述 horizon
與同時發生的早停;
- 腳本 sha256 `f2d11974…` → `040db9cd5978f1b528f1acf8cf3460366f0c4c761b2443163be46bc69dc82b95`;

> **HASH CHAIN COMPLETED 2026-08-13。** 該檔案目前的 sha256 是
> `5da5a7a27581af55…`,它與上面**兩個 hash 都不相符** —— 紀錄停在 08-12 那次修正,而腳本其後又被
> 改過三次。那三次修改全都動在參數處理與 pre-flight 驗證,**沒有一次動到量測邏輯**,分別是:
> (i) 新增 `--stage-variant {capped,native}`,讓 native 的 run 解析到自己的 stage root
> (預設為 `capped`,所以先前的呼叫不受影響);
> (ii) 從 `__gpu5deviation` 副本移植進 `--gpu-uuid-override`,讓閒置卡 deviation 走同一支腳本,
> 而不是走一份 fork;
> (iii) `parse_ga_stats` 不再要求 GA log 必須從第 1 代開始 —— 在 resumed run 上 log 是一段*後綴*,
> 因此連續性檢查現在以 log 自身的第一代為錨點,而呼叫端另外要求**軌跡**必須完整為 `1..N`、且 log
> 必須是它的後綴,並在重疊區逐元素比對 `n_evals`、印出 `RESUMED_RUN_PARTIAL_LOG`。
>
> 若把這段空缺留著不記,等於留下一支 provenance chain 接不到自己所產出 artifact 的量測腳本。
> 未來任何修改都必須在同一處延續這條鏈。
- 三份 FAIL 紀錄已(經使用者授權)移至 `quarantine/stopline_bug_20260812/`,並附 README 說明成因;
未覆寫任何成功 artifact(那些目錄中原本就不存在成功結果)。

修正後五個 large remeasure 全數完成。interleave 起始臂是逐 shape 的確定性對抗平衡 ——
`START_ARM = {medium: G, large: F, tiny: G}` —— 因此 large 由 F 起始是設計如此,不是 deviation。

---

## §9 `PENDING_HUMAN_DECISION` —— medium 重測量測缺陷的處置

> **本節是 MIRROR,不是紀錄本身。** 權威是 `s14-stage1-full-ga-outcome-design.md` **§13**
> (2026-08-13 新增)。此處沒有任何東西是已核准的。在 owner 裁決之前,該 design §10.2 / §10.4 的預註冊
> 估計量與 gate 一律維持原狀,且**不得依本節內容改動任何分析、標籤或 claim**。請把它讀成「正在被提出
> 的是什麼、理由為何」,絕不可讀成「已經決定了什麼」。
>
> **流程紀錄。** 由 `design-discussion` 協定產出:兩位獨立 reviewer 於 fresh thread,收到相同、且不含
> coordinator 偏好的初始 prompt;兩輪交互詰問;一輪 evidence-backed final。**雙方皆回傳 `AGREE`,
> 無保留異議。** 用掉 60 分鐘 agent wall-time 上限中的約 43 分鐘。所有承重事實均由 coordinator 對照
> artifact 獨立複驗。

### §9.1 決定一切的框架事實 —— 這個決定改變不了任何結論

先讀這一節,因為它決定了底下所有內容該被賦予多少權重。

per-shape gate 是**四個子判準的連言**,每一項都需要 ≥4/5 個 seed。它**已經在其中三項上失守** ——
而那三項讀自 GA trajectory、從不經過 remeasure,所以汙染碰不到它們:


| shape | Gen0 | gen-10 | AUC | required |
|---|---:|---:|---:|---|
| medium | 3/5 | 3/5 | 3/5 | ≥4/5 |
| large | **1/5** | **2/5** | 3/5 | ≥4/5 |


~~而且改用 `max` 而非 `median` 重算,不改變任何 shape、任何 campaign 的方向性計數。~~
**RETRACTED 2026-08-13 —— 此陳述為偽,而它正是「報一列 `max`」唯一的可採性依據。** 由
`remeasure.{G,F}` 對全部四個 medium 資料集重算:


| dataset | median pos / non-reg | max pos / non-reg | |
|---|---|---|---|
| capped C1 | 2/5, 3/5 | 2/5, 3/5 | 不變 |
| capped C2 | 3/5, 3/5 | 2/5, 3/5 | 對 F **不利** |
| native C1 | 3/5, **3/5** | 3/5, **4/5** | **跨過 ≥4/5,對 F 有利** |
| native C2 | 2/5, **3/5** | 2/5, **4/5** | **跨過 ≥4/5,對 F 有利** |


native 的非退步門檻 `e^{−η}` 由 **design §12.3 預註冊**。所以 `max` 在四個資料集上惰性、在一個上
對 F 不利,並在**兩個**上把一條預註冊的 ≥4/5 判準往受測臂方向跨過去。完整處理,包括跨越的機制與
由此而來的發表禁令:**design §14 / 下方 §9.5。**

**因此 §13 裡的每一個決定,都是關於紀錄誠實性的問題,不是關於結果的問題。** 這個框架必須出現在任何
amendment 裡 —— 它正是把一個事後修改從「可疑」轉為「可稽核」的關鍵。

### §9.2 三項決定

**D1 —— 估計量:三個 shape 一律維持預註冊的 median-of-7。**
~~`max` 只以標註清楚的敏感度列出現,三個 shape 一致套用,並且永遠附上不變性證明與其兩個已知失效
模式。~~ **SUPERSEDED 2026-08-13 —— 由 §9.5 / design §14 取代:不存在不變性證明 —— 它所倚賴的
主張為偽 —— 而且 `max` 現已被禁止出現在任何 acceptance 與 sensitivity 表格。** 捨棄:把 `max` 升為主要估計量(它買不到任何結論改變、是事後的,而且對受測臂有利 ——
governance §4 會強制 successor;而且有**反例**:capped campaign-1 seed 24005 arm F **7 次重複全部**
被汙染,所以 `max` 給出 10,535,對照同一 config 的乾淨值 13,407,**低估 21.4 %** —— 這同時也推翻了
「沒有任何臂 7 次全掉」以及 i.i.d. 的 `0.48⁷ = 0.6 %` 算術,因為同一視窗內的重複是
**受電源治理器相關的,並非獨立**)。同樣捨棄:乾淨模態平均(reviewer B 提出後,在驗證到它會把
campaign 1 的 non-regression 從 3/5 推到 4/5、正向從 2/5 推到 3/5、從而摧毀自己的可採性論證之後,
自行撤回)。B 的「≥3 個乾淨重複」規則**保留為有效性分類器**,而非估計量;套用到 campaign 1,它標出
seed 24004 arm G 與 seed 24005 arm F 無法由任何重新分析救回。

**Campaign of record = campaign 1。** campaign 2 於 2026-08-12 14:01–14:04Z **在解盲後就地覆寫**了
campaign 1,而且**對受測臂更有利**(median F/G 1.0274、3/5,對比 C1 的 0.9971、2/5)。C2 是事後的
診斷性重製。兩者都要報告;都不產生 tier;而且**不得平均,也不得擇一取用**。⚠️ **現存風險
(2026-08-13 已解除):** `analyze_medium.py` 原本讀的是 canonical path,所以執行它會報出 C2,而輸出
裡沒有任何地方說明這一點。它現在**強制**要求明示 `--campaign {1,2}`,沒有該參數即拒絕執行,
既不預設也不平均,並在標頭印出實際解析到的路徑。

> **⚠️ CORRECTION 2026-08-13 —— 同一次覆寫也發生在 `native` 上,而且先前沒有被記錄。**
> `[CODE AUDIT]` native medium 的 canonical artifact 於 2026-08-12 **14:05:07–14:08:18Z** 同樣被就地
> 覆寫(檔案 mtime)。`superseded_*` 標記只存在於 seed 24001(1 個)與 24005(2 個),
> **seeds 24002 / 24003 / 24004 一個都沒有** —— 而且那些標記是更早的重試殘骸,不是 campaign 標記。
> 前一版草稿曾引 `stage5_native_baseline/seed_24005/medium/` 作為*確實*留下痕跡的對照案例;
> 那個讀法是錯的。兩個 P0 層級共有同一個未追蹤覆寫問題。
>
> | campaign | median F/G | 逐 seed F/G | 正向(`ratio > 1`) | **正向(預註冊 `> 1+δ_s`)** | non-regression |
> |---|---:|---|---:|---:|---:|
> | native C1 | **1.1391** | 0.4865 / 2.2663 / 0.3735 / 1.1391 / 1.9725 | 3/5 | **3/5** | 3/5 |
> | native C2 | **1.0041** | 1.0041 / 0.8256 / 1.0246 / 0.7029 / 1.0537 | 3/5 | **2/5** | 3/5 |
>
> **⚠ CORRECTED 2026-08-13(第二輪)。** 這張表「正向」欄的第一版用的是 `ratio > 1`,而那**不是**
> 預註冊判準。§10.2 把 improvement 定義為 `F/G > 1 + δ_s`
> (`δ_s = 0.004204159905590865`,門檻 1.0042042)。兩者在 native C1 相同(3/5),但**在 native C2
> 不同:預註冊計數是 2/5,不是 3/5**,原因完全在於 seed 24001 的比值 1.004079
> **以 0.0125 個百分點之差落在門檻外**。權威來源是量測 script 自己記下的旗標,
> `stage5_native_baseline/seed_*/medium/champion_interleaved.json →
> F_over_G_gt_one_plus_delta_s` = `False, False, True, False, True`。**引用「正向」計數時務必指明
> 判準**,否則這張表讀起來會像是與 artifact 互相矛盾。
>
> 一條預註冊判準竟由 0.0125 pp 決定,這件事本身就是第二個、且獨立的佐證,說明
> `η_medium = 0.42 %` 對它所裁量的量而言過緊(第一個在 §3.8.1)。
>
> **方向計數兩者相同(3/5、3/5),所以下游不會有任何東西改動。** 但仍有兩件事必須入帳:C1 的逐 seed
> 離散從 0.37× 到 2.27×,正是同一種雙峰樣態,所以 native 的端點與 capped 一樣是
> `NOT_EVALUATED / instrument-invalid`;以及與 capped 不同,**這裡較有利的 campaign 是 C1 而不是 C2**
> —— 所以「覆寫方向一致地偏袒受測臂」**不是**一個站得住腳的說法,不得如此陳述。
>
> *來源:`[CODE AUDIT]` `medium_recheck_control/native/seed_*/preserved_campaign1_20260812T135613Z/`
> 對比 `stage5_native_baseline/seed_*/medium/champion_interleaved.json`;S14 design §13.3。*

medium 的 final-champion 與 non-regression 端點採取第三種狀態 ——
**`NOT_EVALUATED / instrument-invalid`** —— 在兩個 campaign 皆然。既非 pass 亦非 fail。

**真正的修復是儀器,不是統計量:** 註冊 `MEASUREMENT-WARMUP-AMENDMENT`(Layer A,R3 權限),把 warm-up
由**次數**改為**牆鐘時間 ≥ 50 ms**,三個 shape 一致,**在執行前**註冊,並事先承諾新舊數字並列發表。
這是**條件性的** —— 見 §7.1b 的 RBS caveat —— 並以尚未嘗試過的
**5,136 warm-ups at the pinned RBS = 4096** 可行性探測為前提。

**D2 —— Margin:封存的 pinned `η_s` 治理地位不變,但必須完整揭露。**
捨棄:由重測自身重算 η —— 它**循環**(被 gate 的那批重複自己去設定 gate),而且被 **tiny 的 null
control 證偽**:在實測 margin 下,一個**逐位元相同、零 treatment** 的對照會被判成 **3/5 退步**。一個
會把已知的零判成退步的 margin,沒有資格取代一個不會這麼做的。但三個 pin 都是**意外,不是雜訊模型**
(見 §7.1a 更正後的表),所以三個 shape 都必須同時報告兩種 margin,並明白陳述:**在 medium 上,保留
pin 並不是比較保守的選擇** —— 它比觀測到的 null 離散度緊約 30×,所以那是一個治理決定,不是安全邊界。
而且 **η 是錯的尺度**:它量的是*一個* config 的窗內重複性,而 estimand 是*兩個不同 champion* 的比值。
新增:以 tiny 的 null 包絡作為 large 的**參考包絡**(large 每個 seed 的 |ln F/G| ≤ 0.0749 都落在 tiny
零 treatment 包絡之內,最大 0.1247)—— 那是參考包絡、**永遠不是門檻**,而且偏保守,因為 large 是最平
的 shape(champion 層級離散度:large 1.129、tiny 1.182、medium 1.222)。

> **WHICH STATISTIC —— 2026-08-13 釐清。** 那三個數字是 **`best_fitness`** 的跨幅
> (`optimization_result.json`,取該 shape 10 個臂的 max/min):`[CODE AUDIT]` large **1.1294**、
> tiny **1.1823**、medium **1.2218**。**重測中位數**的跨幅則是另一個、而且略緊一些的統計量:
> large **1.1249**、tiny **1.1705**、medium **1.2205**。兩者的排序與結論完全相同,所以下游不會有
> 任何東西改動 —— 但有兩位獨立讀者各自重推出重測中位數那組數字,並把它當成與 design 不一致回報,
> 所以現在把統計量講明。同一個歧義也影響 §9.2 與 design §13.5 中 tiny 的「champion range 1.18×」:
> 那是 `best_fitness` 的跨幅 1.1823;重測中位數的跨幅是 1.1705。

**D3 —— 逐 shape claim 階梯。** 見 §4 若獲核准後將被修訂的表;簡述如下 ——
medium:gate **未達成**,端點 `NOT_EVALUATED / instrument-invalid`,完整揭露缺陷,且**沒有**任何
non-regression 通過、improvement 或導出的 tier。large:gate **未達成**(1/5、2/5、3/5、3/5);
5/5 non-regression **僅能作為一個子判準**報告、**絕不可單獨引用**,並揭露它在窗內 margin 下是 3/5、
且 `η_large` 撐在 champion 重測重現不出來的 pilot anchor 上;improvement 0/5。tiny:雙軌 —— guidance
問題為 `not evaluated / not activated`(0/27 genes),並附 `NOT_EVALUATED ≠ no effect`,外加它作為
意外 null control 的角色;它的 pinned margin **結構上空洞**。合併:修正後的稀疏 capped prior
**未達成**兩個 confirmatory shape 的預註冊 gate —— 而*不是*「無效果」,沒有 aggregate rescue,
沒有一般化或部署措辭。**Conditional Arm S 不觸發**(§10.2 要求 confirmatory shape 通過);
physics-direction 歸因延至 S20。

在報告一個預註冊預測、但其儀器已受質疑時,**四列,永不合併**:
(i) 預測原文與其註冊日期;(ii) 完全照預註冊方式計算的分析,不得更動;(iii) 儀器判定、其證據,以及
**相對於解盲的**發現日期;(iv) 任何修復後的估計,明確標示為事後。**(ii) 永不被 (iv) 覆寫。**

### §9.3 九項待 owner 裁決的事項


| # | 待裁決事項 | 不裁決的後果 |
|---|---|---|
| 1 | ~~**執行約 10 分鐘的鎖頻驗證**~~ **DOWNGRADED 2026-08-13 —— 不再列為優先。** 此後一次直接的 1 kHz 時脈追蹤已**否證**時脈說法(§7.1b),所以鎖頻只會是在檢驗一個資料已經不利於它的假說;而且 `--setperflevel high` 在此環境明顯不生效,真正的鎖頻需要對卡的**寫入權限**(`pp_od_clk_voltage` / `amd-smi`)—— 那是一次 governance escalation,不是十分鐘的 `sudo` 工作。機制這個未解的問題,現在由 §13.7 的項目 1–2、以及那個尚未嘗試的 5,136 @ RBS-4096 probe 來處理會更好。 | 機制維持 `NOT_EVALUATED`;但請注意*修復*路徑(§9.2 D1)**不**依賴於知道成因 |
| 2 | 核准 `MEASUREMENT-WARMUP-AMENDMENT`,**條件於** 5,136 @ RBS-4096 探測通過 | 不可能產生任何修復後的 medium 重測 |
| 3 | 追認 **campaign 1 為紀錄用量測**,並為那次未留痕的就地覆寫建立 operational-correction 紀錄 | `analyze_medium.py` 會持續報出較有利的 C2 |
| 4 | 確認 **維持 median-of-7**(D1) | 估計量的歧義會一路帶進報告 |
| 5 | 確認 **由 pinned η_s 治理**(D2),並雙 margin 揭露 | gate 的算術無法定案 |
| 6 | 核准 **逐 shape claim 階梯**(D3) | §4 無法定稿 |
| 7 | 核准 **A/A 跨視窗實驗**(約 50 GPU 分鐘,可按視窗中斷) | 任何 shape 都沒有跨視窗重複性資料;窗內 η 維持為一個緊度未知的下界 |
| 8 | 核准 §13.6 的**紀錄更正**(各項撤回、臂間不對稱、§12.2(B)2 理由作廢) | 索引與 root-cause memo 會持續帶著已知為錯的陳述 |
| 9 | 確認 **medium 的端點為 `NOT_EVALUATED / instrument-invalid`** 而非 fail | medium 有被報成「測了但失敗」而非「量測無效」的風險 |


### §9.4 殘餘不確定性(須寫入報告,不求解決)

- **warm-up 相關性背後的機制是 `NOT_EVALUATED`。** *(2026-08-13 改寫;本條原文寫的是時脈機制乃「推論
  而來……不存在任何直接的鎖頻證據」。)* 一次在實際進行中的 remeasure 上所做的直接 1 kHz 時脈追蹤
  **否證**了時脈說法 —— 時脈與吞吐量的相關為負、dropout 那幾次的時脈中位數比乾淨的重複更高、每一次
  重複都達到 1512–2065 MHz(§7.1b)。**與 warm-up 時間的相關性成立**;它的成因不成立。倖存的未檢驗
  候選:XCD/CU 配置、MALL/L2 residency、GSU-4 workspace 競爭,以及任何能解釋「時脈更高、kernel 卻更
  慢」的機制。該追蹤約 8 ms 的解析度看不進 3.2 ms warm-up 的內部,所以時脈說法是被不利證據壓低,而不
  是被排除。
- **任何 shape 都不存在跨視窗或跨日的重複性資料。** 窗內 η 是一個緊度未知的**下界**。
- tiny 的單一 dropout(7 次中的第 7 次,落在 37.8 s 視窗的第 34.7 s)為 `NOT_EVALUATED`,而且 tiny
  對 warm-up 長度被量到的不敏感性對它**反證** *(2026-08-13 改寫:本條先前寫的是「medium 的機制對它
  反證」,而 medium 的機制正是被撤回的那個)*。
- 搜尋期汙染是否 arm-symmetric:`NOT_EVALUATED`,而且**事後不可查證**(逐代 benchmark CSV 未保留)。
- campaign 1 為何比 campaign 2 髒 1.7×:未解釋。
- 跨 campaign 的可重現性對比僅建立在 **n = 2** 個 campaign 之上。

*Source: `s14-stage1-full-ga-outcome-design.md` §13 (§13.1–§13.10), 2026-08-13. Mirror only — amend the
authority first.*

### §9.5 `PENDING_HUMAN_DECISION` —— peak-of-7 作為 medium 端點的「能力」論證

> **MIRROR,不是紀錄本身。** 權威是 `s14-stage1-full-ga-outcome-design.md` **§14**
> (`CAPABILITY-ENDPOINT-PACKET-20260813`,2026-08-13 新增)。此處沒有任何東西是已核准的;在 owner
> 裁決之前,§10.2 / §10.4 一律維持原狀。
>
> **流程紀錄。** `design-discussion` 第二場:兩位獨立 reviewer,fresh thread,收到相同、且不含
> coordinator 偏好的 prompt;一輪交互詰問;一輪 evidence-backed final。**雙方 `AGREE`,無保留異議。**
> 用掉 60 分鐘 agent wall-time 上限中的約 27 分鐘。所有承重事實均由 coordinator 複驗,而且
> **兩度推翻 reviewer 的計算**。

**問題本身 —— 以及它為何不是 §9.2 D1 已經駁回的那一個。** D1 駁回的是「`max` 是較好的*估計量*」。
owner 提出的是另一種論證:**能力(capability)**。汙染是單向向下的,所以一次落在乾淨模態的重複,
就是這個 config *做得到什麼*的真實觀測;若 medium 被看到達到 ~13,500 GFLOP/s,它就做得到。那是一個
關於單一臂的主張,不是關於估計量的主張,所以它被獨立審查。

**判定:駁回 —— 但前提有一半是對的,必須承認,不能辯掉。**
peak-of-7 在回復一個 config 的乾淨水準上,確實遠優於 median-of-7(native C1 的 max-ratio 壓縮到
0.889–1.068,而 median 橫跨 0.37–2.27)。它之所以失敗,是因為**端點不是一個水準 —— 它是一個比值,
而且要對照一條預註冊的 margin 來裁量。** 三個彼此獨立的否決理由:


| # | 類型 | 內容 | 量級 |
|---|---|---|---|
| 1 | **偏差**,`max` 專屬 | 乾淨模態本身是雙向雜訊,所以 max-of-7 即使在**零**汙染下也會高估 —— 而且因為同一視窗內兩臂的乾淨計數相差 −3 到 +3,那個高估是**臂間不對稱的**,且符號未知 | +0.51 %,對照 **+0.42 %** 的改善門檻;差額 +0.30 %,約為決策邊界的 71 % |
| 2 | **變異**,與估計量無關 | 跨視窗的水準漂移,存在於非全汙染的視窗中 | **0.5–2.8 × η_medium** |
| 3 | **不可證偽性**,結構性 | 能驗證 peak margin 的乾淨模態校準,在釘死的 estimand 下**取得不到** | 見下 |


否決理由 2 指控的是**每個 seed 只有一個視窗**的設計,不是統計量,而且就算汙染明天被修好,它依然
成立。否決理由 1 是唯一針對 `max` 本身的。**兩者不可互相涵蓋:** 沒有 2,就沒有東西能解釋為什麼
什麼結論都下不了;沒有 1,底下那個 native 的 4/5 會被讀成一種正當的替代分析,而不是一個可診斷的
假象。

**為何這個修復是結構上不可能,而不只是還沒試。** 5,136 warm-ups @ RBS-4096 探測在三個 seed 上全數
崩潰(`Insufficient rotating buffer size.`,exit 134)。`[CODE AUDIT]` 成因是一個決定性的
**帶號 32 位元溢位**:`DataInitialization.cpp:3213` 以 `int32_t` 計算 `rotatingNum × rotatingSize`,
而 `1,312,256 × 3,272 = 4,293,701,632` 繞回 **−1,265,664** —— 與 log 逐位元相符。溢位門檻
`rotatingNum ≥ 1637`,所以在這個 working set 下 **`num-warmups ≥ 1638` 必崩**,暖機因此被封在約
1,637 次 enqueue ≈ **16–19 ms**,對照 sweep 的 **51 ms** 拐點。**因此釘死的 estimand 下根本不存在
任何乾淨的量測。** 這滿足 design §13.8 的崩潰分支,並**結案 §13.7 item 2**;真要修需要改 client
程式(`int32` → `int64`),那是一個新的 estimand、一個 successor 問題,不是 amendment。請注意這個
推論是*不利於*搶救的:一個其驗證量測取得不到的統計量,在它被套用的設定下就是不可證偽的。

**發表規則 —— 比 §9.2 D1 更嚴。** **任何 acceptance 或 sensitivity 表格中都不得出現 `max` 列,
任何 shape、任何 variant 皆然。** `max` 只能出現在量測缺陷的鑑識段落中,作為關於儀器的證據,而且
必須在同一處載明:*在 max-of-7 下,native-medium 的非退步分項在兩個 campaign 都讀作 4/5,跨過
§12.3 預註冊的門檻並偏向受測臂 —— 此位移正是 max 被駁回的理由,不是一項結果。* 靜默更正不可接受,
因為 §9.1/§9.2 先前斷言的正是其反面。owner 的能力觀察改以**敘述方式**報告 ——「medium 的 champion
曾被直接觀測到 11,977–15,067 GFLOP/s;低模態是儀器汙染,不是 config 行為」—— 不附比值、不進 gate、
不產生 tier。

**跨越的機制,也就是它為何是可診斷的而非一項發現。** `max` 並沒有發現 F 非劣。它是把原本把中位數
壓到門檻下的向下汙染剝掉,而那條門檻又比實測離散度緊約 288×,於是幾乎什麼都過。這個通過是
**一個極值統計量對上一條由中央統計量離散度導出的 margin** 所製造出來的 —— 即 §3.8.1 的錯配,成真。

**其他必須更正的既有紀錄(design §14.6)。**

- §9.1 / §9.2 的 count-invariance 主張為偽 —— 已於上方更正。
- §13.3 native 表的「正向」欄未標明判準。它用的是 `ratio > 1`;預註冊規則是 `> 1 + δ_s`
  (`δ_s = 0.004204159905590865`)。兩者在 native C1 相同(3/5),但**在 native C2 不同:預註冊計數
  是 2/5**。seed 24001 的 `ratio = 1.004079` **以 0.0125 個百分點之差落在門檻外** —— 這本身就是
  `η_medium` 對它所裁量的量而言過緊的第二個、且獨立的佐證(第一個是 §3.8.1)。
- **第二個**七次全汙染的臂必須入帳:capped seed 24004 arm F campaign 2(視參考基準而定,回復率
  85.7–89.4 %),與已知的 seed 24005 arm F campaign 1(78.6 %)並列。
- 跨視窗底線(0.5–2.8 × η_medium)加入 §9.4,並註明它僅建立在單一個下午上。
- ladder 的 idle-gap 趨勢(33 % → 52 %)**未建立** —— 經 over-dispersion 調整後 z ≈ 1.40。
  不得作為暖機說法的支持證據引用。

**Acceptance / falsification。** 由一個跨視窗 A/A 實驗顯示底線實質低於 `η_medium`,或由一個 64-bit
client patch 在 RBS 4096 下量得可證實的乾淨結果,即可重開 —— 兩者都必須走 **successor**,不是
amendment,因為 governance §4 在 threshold、measurement、comparability 與 claim 任一項變動時即獨立
觸發,與是否對受測臂有利無關。

**殘餘不確定性。** 機制 `NOT_EVALUATED`。臂間對稱性 `NOT_EVALUATED`,且事後不可查證。各 config 的
真實上限未知 —— 任何 `max` 都只是**下界**。底線僅建立在一個下午上;任何 shape 都不存在跨日重複性
資料。兩個 same-model fresh thread 是 **process independence,不是 scientific replication**。

*Source: `s14-stage1-full-ga-outcome-design.md` §14 (§14.1–§14.8), 2026-08-13. Mirror only — amend the
authority first.*

---

*維護:capped G/F、7× remeasure、conditional Arm S、native-P0、S11 closeout 落地時,更新 §1 狀態與 §7 結果
格。本索引維持非權威 —— 任何實質變動先回寫到所引用的權威文件,並同步結構/敘述到英文版*
`report-source-index.md`*(英文為權威)。*