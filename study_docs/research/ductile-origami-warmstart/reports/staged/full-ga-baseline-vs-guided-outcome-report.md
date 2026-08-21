> **DRAFT — S14 formal outcome `NOT_EVALUATED`。** 本檔是 S14 的**唯一 formal report**(design frontmatter `formal_report_path` 指定),承載 evidence-independent 的方法與 pins、**跨 shape 結論總結**、gate 算術,以及指向三份 per-shape 詳細附冊的 index。逐 seed 的詳細實驗記錄不在本檔,在附冊(§3.0)。凡屬 S14 formal 產物的數字,未經獨立驗證者一律留 `⟨TBD@closeout: … | source: …⟩`。**本檔不主張 S14 走 positive／negative 任一分支,不捏造任何 GPU 數字。**
>
> **2026-08-13 結構變更(owner 決定):** 本檔原名 `s14-stage1-full-ga-baseline-vs-guided-outcome-report.md` 且誤置於 `reports/staged/`,與 design 預註冊的 `formal_report_path` 不符;已移回預註冊路徑。同時新增三份 per-shape 附冊,並把兩份原本錯放在 `reports/staged/` 的 subagent 工作筆記移入 `working-notes/`。命名規則見 [`README.md`](../README.md)。
>
> **目前執行狀態(2026-08-13):** capped(P0=512)三個 shape 全部完成;native(P0=11,405)medium 完成、**large 執行中**(五個 baseline seed 仍在 Gen0 抽樣)。因此本檔與 large 附冊的 native 段落還會變動。
>
> **⚠️ 原列九項 `PENDING_HUMAN_DECISION`** 見 §3.4 與 design §13。裁決前不得改動任何分析、標籤或 claim。
> **(2026-08-15:其中第 3 項 campaign-of-record 已結案,計數已過時 —— 見 §3.4。)**
---
checkpoint_id: S14
title: Stage 1 full-GA baseline-vs-guided real-GPU outcome（per-shape single-objective）
stage: 1
report_status: DRAFT-SCAFFOLD
scientific_outcome: not_evaluated   # capped G+F+remeasure complete on all 3 shapes; native medium complete; native large IN PROGRESS; 9 owner decisions pending (design §13)
criterion_status: DESIGN_APPROVED
positive_criterion: S14_PER_SHAPE_OUTCOME
superseded_criterion: S14_GUIDED_OUTCOME_POSITIVE
failure_ids: [FT-PLUMBING, FT-GEN0-MECHANISM, FT-HEURISTIC-SATURATION, FT-ENTROPY-ONLY, FT-EVALUATION-SUPPORT, FT-BLOCKED-CORRECTNESS, FT-INCONCLUSIVE]
current_artifact_state: RUNNING   # native large GA detached on GPUs 2,3,4,6,7 (Gen0 sampling as of 2026-08-13); all capped work complete
amendments: [RESCOPE-STAGE1-OUTCOME-20260807, PER-SHAPE-SOO-OUTCOME-20260809, ENTROPY-CAP-20260810, CLAIM-SCOPE-S14-20260810, CONDITIONAL-ARM-S-20260810, NATIVE-P0-ROBUSTNESS-20260811, REDUCER-FACT-CORRECTION-20260812, DEVIATION-REMEASURE-STOPLINE-20260812]
pending_amendments: [MEASUREMENT-DEFECT-PACKET-20260813]   # design §13, PENDING_HUMAN_DECISION
per_shape_annexes: [s14-medium-report.md, s14-large-report.md, s14-tiny-report.md]
design_source: ../../s14-stage1-full-ga-outcome-design.md
lock_a_source: ../../../../../agent_run/260809-s14-pershape-baseline/lock
lock_b_source: ../../../../../agent_run/260809-s14-pershape-guidance/lock/lock_b_guided_guidance.json
---

> **Non-authority framing.** 本報告是 checkpoint report，不是 authority。若與 [research charter](../../../surrogate-dse-plan.md)、[experiment plan](../../../ductile-origami-warmstart-experiment-plan.md)、[S14 design §10](../../s14-stage1-full-ga-outcome-design.md)、frozen contract/lock 衝突，一律以後者為準。QA 檔（qa-09）為白話導讀，非 authority。
>
> **Evidence labels（全文一致）：**`[MODEL-ONLY]`＝Formocast 模型空間量；`[BASELINE GPU]`＝baseline 臂真實量測；`[GUIDED GPU]`＝guided 臂真實量測；`[CODE AUDIT]`＝讀 code/artifact 得到的事實，附 file:line／artifact 路徑。**Anti-fabrication：**沒有真實跑出來的數字不編；`not_evaluated ≠ no effect`。

---

## 1. 目的（摘要；完整權威為 S14 design §10）

S14 回答 re-scoped Stage-1 的核心問題：**「Gen0 的權重 bias 是否真的影響 Ductile DSE 的結果（早期與最終）？」** 做法是對每個 problem shape 各跑一條 single-objective Ductile GA，分兩臂比較：**G（baseline，Gen0 對 free genes 用 uniform `p0`）** vs **F（guided，Gen0 對 activated free genes 注入 Formocast 導出的 capped `p1`）**；group_0 兩臂相同、不進入 treatment。medium/large 為 confirmatory、tiny 為探索性；5 對全新 seed 24001–24005。claim 依 charter §8.2 + §8.6a（two-sided、bounded）。

---

## 2. 方法與 pins 的理由（evidence-independent，現在寫定）

### 2.1 Arms

- **G / F** 為正式兩臂（定義如上）。
- **Arm S（same-entropy shuffle 控制）**為 `CONDITIONAL-ARM-S-20260810` pre-registered 條件式：shuffle bundle 先導出並封 Lock C（label firewall），wave-3 GPU 只在「F 於 ≥1 confirmatory shape 過 directional gate 且 deadline budget 足夠」時才跑；physics-direction 僅在 F 同時勝 G 與 S 時就受測 shape 可宣稱，否則 defer 到 S20。

### 2.2 Shapes / seeds / horizon

medium `(256,256,1,1024)`、large `(2304,1024,1,214336)` = confirmatory；tiny `(8,8,1,128)` = 探索性。5 對全新 seed 24001–24005（與 registry 無碰撞）。horizon：`n_gen=30` 上限 + 保留 Ductile 原生早停（period=5）+ 擷取 gen-10 檢查點。

### 2.3 為什麼 Gen0 母體 cap 在 **512**（本節為本次報告新增重點）

S14 把 Ductile 的初始母體（Gen0 population）**固定在 512**，而非讓 constructor 自動膨脹到原生的 **~11,405**。以下說明這不是隨手挑的下限，而是有原理支撐、且不影響 treatment 隔離的選擇。

**(a) 512 是 Ductile 自己的穩態工作族群，不是外加的怪數字。** `[CODE AUDIT]` `projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py`：建構子預設 `pop_size=512`（ga.py:47），且 `config/defaults.yaml:5 pop_size: 512`。原生行為是：當某個變數的候選數 `max_sp_sz` 大於 `pop_size` 時（ga.py:113），**把第 0 代母體灌大到 `int(max_sp_sz * 1.15)`**（ga.py:118），之後**每代用 `decay = _pop_size + (sz − _pop_size)/2` 把「超出的部分」砍半**（ga.py:116、每代套用於 ga.py:293），收斂回 `_pop_size`。而 `_pop_size` 正是膨脹前的 config 值 **512**（ga.py:110）。

  → 換言之 **Ductile 本身就把 512 當成搜尋的穩態族群大小**；~11,405 只是為覆蓋而做的一次性「第 0 代衝刺」，隨即衰減回 512。固定 512 = **跑在 Ductile 自己設定的工作族群大小，只是省略那一次性衝刺**。

  decay 後每代母體（native，供對照）：

  | gen | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8+ |
  |---|---|---|---|---|---|---|---|---|---|
  | pop | 11,405 | 5,958 | 3,235 | 1,873 | 1,192 | 852 | 682 | 597 | →512 |

**(b) 那次膨脹存在的唯一原因，是為了覆蓋 group_0；cap 掉它會縮小 group_0 的搜索，但這個縮小在兩臂完全相同、會在配對比較中抵銷。** `[CODE AUDIT]` 觸發膨脹的 `max_sp_sz` = 各 gene 基數的最大者 = **group_0（MatrixInstruction/WorkGroup 群組）的 9,918 個候選**（`int(9918 × 1.15) = 11,405`，對上 ga.py:118）；group_0 由既有 GEKO 權重提供、不在 Formocast treatment 內（treatment 只重新加權 29 個 ungrouped free genes）。必須**誠實區分兩件事**：

  - **對絕對結果 / 外部效度：有影響。** cap=512 確實少抽 group_0 的候選 → 縮小整體搜索範圍 → 兩臂找到的 champion 絕對品質、搜索難度都會與 native 不同。**這正是為什麼 claim 明確 scope 成「P0-capped=512 Ductile variant」、不宣稱原生 Ductile。**（不可說「cap 不影響實驗結果」——它改變了兩臂共同站的起跑線。）
  - **對 G-vs-F 的 treatment 對比（內部效度）：不偏。** group_0 兩臂都用同一個 `p0`、同一個 512 budget、且 Gen0 用 common uniforms → **兩臂在 Gen0 抽到的 group_0 候選逐一相同**；這個「被縮小的 group_0 覆蓋」是**兩臂共享的邊界條件**，在配對差 (F−G) 中抵銷。treatment（只重新加權 free genes）仍是唯一的外生差異。
  - **caveat：treatment×budget 交互作用。** 因此量到的效應嚴格是「**在 512 預算下**的 guidance 效應」，未必等於 native 預算下的效應（guidance 在小 budget 下可能更/更不顯著）。此為外部效度限制，用 §2.3(f) 的 P0 敏感度檢查界定。

**(c) 512 是「warm-start 問題有意義」的 regime，且對被測維度已足夠。** warm-start prior 的價值只存在於「抽不滿、只能抽一部分」時；512 下 free genes 的**聯合空間確實抽不滿**，prior 才有發揮餘地（native 11,405 會稀釋 treatment 的邊際價值——見 §2.3(e)）。同時 free genes 的基數都很小（如 DepthU 6 個值、PrefetchGlobalRead 2 個值），512 下每個值平均被抽 ~85 次以上，**GA 對被測維度有充分素材**；被 cap 犧牲的只有 group_0（未受測）的覆蓋。

**(d) 內部效度與 512 的絕對值無關。** 兩臂使用**同一個** 512（Lock A 封存；runner 以 `DUCTILE_FORCE_P0=1` 強制、且 `[CODE AUDIT]` engine patch `ga.py:111–117` 設此環境變數時**完全跳過膨脹**、`ga.py:302–304` fail-closed 斷言初始母體恰為 512）。G-vs-F 的比較在任何共用 P0 下都成立；512 只是設定一個可辯護的操作點，不需要是「唯一正確值」。

**(e) 為什麼不用 native 11,405（或更大）。** 見 §2.3(a) 的 decay：全程總評估數 native ≈ 2.4×（30 代）～3.8×（早停 ~15 代）於 capped=512，且**更大的 Gen0 會讓兩臂初始覆蓋都更完整、稀釋 guidance 的邊際價值**（guidance 在 Gen0 小時最明顯）。加上 native 讓 medium 的 Gen0 也膨脹（group_0 與 shape 無關）、large 單次不中斷需求拉到 ~2 天（對中斷更敏感）。故 native 只適合作為**事後的穩健性/對照**（見 §2.3(f)），不適合當主對比的操作點。

**(f) 誠實界線與可信服的補強。** claim 已 scope 成 **「P0-capped=512 Ductile variant」**（charter/design），不宣稱未改動之原生 Ductile。若需堵住「你把它從 native 改小了」的質疑，預留兩個經驗性比較：**(i) P0 敏感度檢查**——在 medium 上以 256/512/1024 各跑少量 seed 的 G/F，若效應（或 null）方向一致即證明結論非 512-artifact；**(ii) native（11,405）穩健性跑**——僅在 capped 顯示效應的 shape 上補，直接消除 cap caveat（成本高）。兩者皆為 optional，是否執行視 capped 結果與 deadline 決定；本節先行 pre-register 以避免 post-hoc。

### 2.4 Guidance（entropy-cap；完整見 design §10.3 / qa-09 §4）

per-shape 由既有 per-size scores out-of-band 重導；`ENTROPY-CAP-20260810` 以 universal per-gene mixture cap `p1_g=(1−ρ)p0+ρ·q_g(λ=8)`、`ρ_g=max{ρ∈[0,0.80]: H_norm≥0.80}` 取代 binary 排除。activated：medium 2（1LDSBuffer、DepthU）、large 5（TransposeLDS、UnrollLoopSwapGlobalReadOrder、GlobalReadVectorWidthA、GlobalReadVectorWidthB、PrefetchGlobalRead）、tiny 0（sentinel-dominated）。封於 Lock B。

### 2.5 Per-shape 噪音 margin η_s

`[CODE AUDIT]` 由現有 3-anchor×7-repeat pilot 殘差逐 shape 導（**不**用 tiny-汙染的 aggregate）：medium η=0.004195（floor e^{−η}=0.9958）、large η=0.122846（floor 0.8844）、tiny η=0.446600（floor 0.6398）。最終非退步門檻 = `e^{−η_s}`。

### 2.6 Claim scope（charter §8.2 + §8.6a）

**two-sided、bounded**：報告 guided 對 (i) early-search（gen-10 + AUC）與 (ii) 最終 tuned 品質的效應（含改善／無變化／退步）；資料支持時**得宣稱受測 shape 最終品質提升**（`CLAIM-SCOPE-S14-20260810`）。**beat-native 已由 §8.6a 2026-08-10(b) owner extension 就 S14 解除為 two-sided、等資料再說**（需實際量測/納入 native 參考並揭露 budget/selection confounding；未量測前不憑空宣稱）。強制標 modest power（5 seeds）+ scope（受測 shape、單一 cluster、不一般化）；不預設結論、不誇大偽造。§8.6 其餘禁詞（generalization/deployment/cross-arch/wall-clock speedup/adopt）不變。

---

## 3. 結果 —— 跨 shape 總結與 per-shape 附冊 index

> **本節只做跨 shape 的總結與 gate 算術。** 逐 seed 數字、trajectory、remeasure 原始重複、
> 量測稽核、偏差與根因,全部寫在三份 per-shape 附冊裡(見 §3.0);本節不重覆它們,只引用結論。
> 這個兩層結構由 owner 於 2026-08-13 決定,規則寫在 [`README.md`](../README.md)。

### 3.0 Per-shape 附冊 index

| shape | 角色 | 附冊 | 狀態 |
|---|---|---|---|
| medium `(256,256,1,1024)` | confirmatory | [`s14-medium-report.md`](s14-medium-report.md) | capped + native 皆完成;**final 端點因量測儀器失效而 `NOT_EVALUATED`**(§3.3) |
| large `(2304,1024,1,214336)` | confirmatory | [`s14-large-report.md`](s14-large-report.md) | capped 完成;**native 執行中**,附冊該半段為 `IN PROGRESS` scaffold |
| tiny `(8,8,1,128)` | 探索性(**不在 gate 內**) | [`s14-tiny-report.md`](s14-tiny-report.md) | 完成;另作為**意外的 null control** |

三份附冊都**不得單獨陳述 S14 outcome**;gate 判定只存在於本檔。

### 3.1 Per-shape directional-consistency 分項計數 `[BASELINE GPU]` `[GUIDED GPU]`

§10.4 的 per-shape gate 是**四個分項的連言**,每項各需 **≥4/5** 對 seed 方向為正。實測:

| shape | Gen0 | gen-10 | AUC | final ratio | gate 要求 |
|---|---:|---:|---:|---:|---|
| **medium**(confirmatory) | **3/5** | **3/5** | **3/5** | `NOT_EVALUATED`(§3.3) | 四項皆 ≥4/5 |
| **large**(confirmatory) | **1/5** | **2/5** | **3/5** | **3/5** | 四項皆 ≥4/5 |
| tiny(不在 gate 內,僅供校準) | 3/5 | 2/5 | 2/5 | 1/5 | — |

*來源:`[CODE AUDIT]` 由 `stage3_{baseline,guided}/seed_*/{shape}/trajectory.jsonl` 與
`stage3_baseline/seed_*/{shape}/champion_interleaved.json` 重算;medium 另見 §3.3 的 campaign 分歧。
AUC 積分到兩臂共同完成預算 `B* = min(cumulative_complete_evals)`。*

**兩個 confirmatory shape 的四項連言都不成立,且是在三個「量測缺陷碰不到」的分項上就不成立。**
Gen0、gen-10、AUC 讀自 GA trajectory,不經 champion 重測,所以 §3.3 那個儀器問題無論最後怎麼
裁決,都改變不了這三項。這件事決定了整份報告該怎麼讀:§3.3 是**紀錄誠實性**的問題,不是
**結論**的問題。

正式的 gate 判定與 outcome label 於 closure 時由 `CU-S14-OUTCOME` 填寫,並須先解決 §3.4 所列
待裁決事項;在此之前 frontmatter 維持 `scientific_outcome: not_evaluated`。

### 3.2 附加分項:non-regression 與 improvement

| shape | non-regression(`F ≥ G·e^{−η_s}`) | improvement(`F > G·(1+δ_s)`) |
|---|---:|---:|
| medium | `NOT_EVALUATED`(§3.3) | `NOT_EVALUATED`(§3.3) |
| large | **5/5** 用 pinned `η_large = 0.1228`;**3/5** 用 large 自身窗內實測重複性 0.0269 | **0/5** |
| tiny | 5/5(在一個**零 treatment** 的對照上;見附冊) | 0/5 |

⚠️ **large 的 5/5 是一個分項,不得單獨引用。** 它同時是 gate 未達成的那個 shape 的分項,而且
它的通過與否取決於採用哪個 margin —— 而 `η_large` 來自兩個 max/min 為 1.24 與 1.42 的 pilot
anchor,champion 重測(1.02–1.05)**重現不出來**。完整討論見 large 附冊。tiny 的 5/5 更要小心:
它的兩臂 config **逐位元相同**,所以那是零效應下的 5/5,量的是 margin 有多鬆,不是 guidance 有效。

### 3.3 ⚠️ medium 的 final 端點:儀器失效,`NOT_EVALUATED / instrument-invalid`

medium 的 7× 交錯 champion 重測**不可重複** —— 同一個固定 config、同一張卡、同一個 process、
~21–25 秒視窗內量 7 次,結果呈雙峰:要嘛落在該臂最大值的 95–100%,要嘛掉到 0.07–0.78。根因是
`ClientParameters.ini` 對**所有 shape** 一律設 `num-warmups=321`,而暖機是**次數不是時間**:
medium 的 9.9 µs kernel 只換到約 3.2 ms 暖機,MI300X 從 132–180 MHz idle 爬到 2100 MHz 需要
約 50 ms。large(~601 ms 暖機)與 tiny(dispatch-bound,對暖機長度不敏感)都逃過。

且 medium 有**兩次互相矛盾的 campaign**:campaign 1 median F/G 0.9971、2/5 為正;campaign 2
為 1.0274、3/5。campaign 2 於 2026-08-12 14:01–14:04Z **在解盲後就地覆寫**了 campaign 1,未留
`superseded_*` 標記,且**對受測臂較有利**。**兩者並列報告,不平均、不擇一。**

> **更新 2026-08-15(owner 決定)。** 本段原記「design §13.3 提議以 campaign 1 為紀錄用量測,
> 但該提議**尚未裁決**」。**該提議已結案,但結案方式不是採用 campaign 1:
> campaign 1 與 campaign 2 皆非紀錄用量測,由一個新的 campaign 取代兩者**
> (目前為 **pilot only**,完整 campaign 延後且以 pilot 結果為條件,`PENDING_HUMAN_DECISION`)。
> 同日 **canonical capped medium 五個 seed 一起 revert 回 campaign 1**,
> 而 **canonical native medium 仍為 campaign 2** —— **該混合狀態刻意不予調和**。
> **本報告的處置不變:兩者並列,不平均、不擇一。**

因此 medium 的 final champion 與 non-regression 端點採第三種狀態 **`NOT_EVALUATED /
instrument-invalid`** —— 既非 pass 亦非 fail。這**不影響** §3.1 的 Gen0/gen-10/AUC。
完整證據鏈、暖機掃描、卡別平反、臂間不對稱污染見 medium 附冊。

### 3.4 待 owner 裁決(`PENDING_HUMAN_DECISION`)

design [§13](../../s14-stage1-full-ga-outcome-design.md) 是一份 design-discussion 產出的
decision packet(兩位獨立 reviewer,兩輪交互詰問,雙方 `AGREE` 無保留異議),其中原列**九項**需要 owner
裁決才能寫進本報告的 outcome。
**⚠ 這個計數自 2026-08-15 起已過時** —— 其中 index §9.3 第 3 項
「ratify campaign 1 為 measurement of record」**已結案**
(結論為:C1 與 C2 皆非 measurement of record,由新 campaign 取代兩者)。
**本檔尚未逐項重數,請以 index §9.3 的逐項狀態為準,不要引用「九項」這個數字。**
摘要鏡射於
[`report-source-index.md` §9](../report-source-index.md)。在裁決之前:

- §10.2 / §10.4 的預註冊估計量與 gate **維持原狀**,不得依 §13 改動任何分析、標籤或 claim。
- 本檔的 `report_status` 維持 `DRAFT-SCAFFOLD`,`scientific_outcome` 維持 `not_evaluated`。

其中唯一需要 owner 親自動手的是 **`rocm-smi --setperflevel high` 鎖頻驗證**(需 `sudo`,約
10 分鐘,零研究 GPU 時數) —— 它是唯一能把 §3.3 的時脈機制從**推論**變成**實證**的檢驗。

### 3.5 Conditional Arm S

**不觸發。** §10.2 的 trigger 要求 F 於 ≥1 個 confirmatory shape 通過 directional gate;
由 §3.1,medium 與 large 皆未通過。physics-direction 歸因依 design 延至 S20。
Lock C(Arm-S shuffle bundle)因此不需要為本 checkpoint 封存。

### 3.6 診斷 / correctness / sampler realization

⟨TBD@closeout:P0=512 realized、size/RBS/UUID 驗證、correctness、validity、failure taxonomy
定位(若 negative,依 charter §8.5 定位到 marginal-loss／epistasis-exceeds-hook／entropy-only)。
逐 shape 的 sampler realization 與 correctness 稽核已寫在三份附冊中,此處於 closeout 時彙整。⟩

### 3.7 NATIVE-P0-ROBUSTNESS addendum(design §12)

native Gen0(`int(9918 × 1.15) = 11,405`,不 cap 在 512)是**同一個 gate 之內**的穩健性
addendum,不是第二個 gate,所以不另立報告。

| shape | 狀態 |
|---|---|
| medium | 5/5 GA + 5/5 remeasure 完成;Q1/Q2/Q3 見 medium 附冊 |
| large | **執行中** —— 2026-08-13 觀測時五個 baseline seed 仍在 Gen0 抽樣,guided 未開始,7× remeasure 已由 cron 待命 |

large native 收斂前,本節與 large 附冊的 native 半段維持 `NOT_EVALUATED`,**不得填入任何推估值**。

---

## 4. Traceability

- Design authority：[S14 design §10](../../s14-stage1-full-ga-outcome-design.md)（per-shape；joint-MOO/aggregate-Q 舊記錄保留於 §1–§9）。
- Amendments：`RESCOPE-STAGE1-OUTCOME-20260807`、`PER-SHAPE-SOO-OUTCOME-20260809`、`ENTROPY-CAP-20260810`、`CLAIM-SCOPE-S14-20260810`（含 2026-08-10(b) beat-native extension）、`CONDITIONAL-ARM-S-20260810`。
- Locks：Lock A（baseline protocol）、Lock B（capped guidance）、Lock C（Arm-S shuffle，conditional，待封）。
- Run-roots：baseline `agent_run/260809-s14-pershape-baseline/`；guidance `agent_run/260809-s14-pershape-guidance/`。
- **Per-shape 附冊(2026-08-13 新增,owner 決定):** [`s14-medium-report.md`](s14-medium-report.md)、
  [`s14-large-report.md`](s14-large-report.md)、[`s14-tiny-report.md`](s14-tiny-report.md)。
  三份都是本檔的附冊,承載詳細實驗記錄;**gate 判定與 S14 outcome 只在本檔**。命名與目錄規則見
  [`README.md`](../README.md)。
- **待裁決:** design [§13](../../s14-stage1-full-ga-outcome-design.md)
  `MEASUREMENT-DEFECT-PACKET-20260813`(`PENDING_HUMAN_DECISION`,原列九項,
  **2026-08-15 起計數已過時,見 §3.4**);摘要鏡射於
  [`report-source-index.md` §9](../report-source-index.md) 與其 zh-Hant 鏡射。
- **工作筆記:** `working-notes/` 內兩份已被本報告體系取代的 subagent 分析,**不得引用**,
  待 owner 於正式報告定稿後確認移除。
- 收尾時本檔由 closure unit `CU-S14-OUTCOME` 補齊 §3 並經獨立 verifier 由 locked artifacts 重算 per-shape 表與 gates。
