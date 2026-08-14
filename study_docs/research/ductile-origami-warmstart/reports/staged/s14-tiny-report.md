> **PER-SHAPE 附冊 —— 本檔不陳述 S14 outcome。** 本檔是 S14 formal report
> [`full-ga-baseline-vs-guided-outcome-report.md`](full-ga-baseline-vs-guided-outcome-report.md)
> 的 **per-shape 附冊(tiny `(8,8,1,128)`)**,只承載該 shape 的詳細實驗記錄 —— 逐 seed 數字、
> trajectory、remeasure 原始重複、量測稽核、偏差與根因。**S14 過了沒有,只有 formal report 能說。**
> gate 是跨 shape 的連言,而 **tiny 根本不在 gate 之內**(S14 design §10.2:*"tiny `(8,8,1,128)` =
> 探索性(僅描述,排除於 confirmatory gate)"*;§10.4:*"tiny 探索性(無 gate)"*)。任何把本檔讀成
> 「S14 的結果」的讀法都是誤讀。目錄與命名規則見 [`README.md`](../README.md)。
>
> **Non-authority framing。** 本附冊不是 authority。若與 [research charter](../../../surrogate-dse-plan.md)、
> [experiment plan](../../../ductile-origami-warmstart-experiment-plan.md)、
> [`../../s14-stage1-full-ga-outcome-design.md`](../../s14-stage1-full-ga-outcome-design.md) 衝突,
> **一律以後三者為準**。凡引自 design **§13**(`MEASUREMENT-DEFECT-PACKET-20260813`)者,一律標
> `PENDING_HUMAN_DECISION` —— 那是**被提出的**,不是**被決定的**。
>
> **Evidence labels(全文一致):** `[MODEL-ONLY]` = Formocast 模型空間量;`[BASELINE GPU]` = Arm G
> 真實量測;`[GUIDED GPU]` = Arm F 真實量測;`[CODE AUDIT]` = 讀 code／sealed artifact 得到的事實,
> 附 `file:line` 或 artifact 路徑。
>
> **Anti-fabrication。** 每個數字後面都附來源路徑,且都由撰稿者直接對 primary artifact 重算或讀取後
> 才寫入。未量測的量一律標 `NOT_EVALUATED`;**`NOT_EVALUATED ≠ 無效果**。
>
> **Two-sided。** 本檔不預設任何結論;敘述順序是「先驗證前提 → 再報數字 → 最後才詮釋」。
>
> **Run root(host):** `/data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-baseline`
> (container 內為 `/src/rocm-libraries/agent_run/260809-s14-pershape-baseline`;artifact 內記錄的
> 是 container 路徑)。除另有說明外,相對路徑皆以該 root 為基準;guidance 導出物則以
> `agent_run/260809-s14-pershape-guidance/` 為基準。
> **`G` = Arm G = BASELINE,`F` = Arm F = GUIDED,`+ve % = guided faster`。**

---

## 0. 本附冊的定位、以及必須雙軌閱讀的理由

### 0.1 tiny 在 S14 裡的角色,以及它實際變成了什麼

tiny 依 `PER-SHAPE-SOO-OUTCOME-20260809` amendment 被指定為**探索性(exploratory)**:僅描述、
排除於 confirmatory gate 之外。指定的理由是 `[MODEL-ONLY]` 的:Formocast 對 tiny 的**全部**
config 都回傳 sentinel 延遲(`30,490 / 30,490 = 100.00 %`,見
[`staged/s11-stage1-model-only-factorization-report.md:501`](s11-stage1-model-only-factorization-report.md)),
所以 tiny **永遠不可能承載 guidance**。這在跑之前就知道了。

跑完之後出現的是一件設計時**沒有預期**的事:因為 tiny 的 activated gene 數為 0,兩臂實際消耗的
GA config **逐位元完全相同**,於是 tiny 變成了一個**零 treatment 的對照組** —— 一個可以直接觀察
「這條 pipeline 在真實效應恰為零時,F/G 統計量長什麼樣子」的窗口。本研究中沒有其他 shape 有這個性質。

**「意外」這兩個字是承重的。** tiny **不是**被設計成 null control 的:它沒有預先登記的 null 假設、
沒有為此挑選的樣本數、沒有 A/A 協定、沒有第二個獨立的 baseline 實例。它是**事後才被辨認出**具有
null-control 結構的。這件事嚴格限制了它能授權什麼(§7.3、§7.4、§8)。把它當成一個預先設計的
null control 來引用,會是對證據等級的膨脹。

### 0.2 雙軌報告 —— 兩條軌都必須明說,不得只講一條

design **§13.5**(`PENDING_HUMAN_DECISION`)提出的 tiny claim 階梯是**雙軌**的。本附冊照此組織:

| 軌 | 內容 | 狀態 |
|---|---|---|
| **軌 (a) —— guidance 問題** | 「Formocast 導出的 capped prior 對 tiny 的搜尋/最終品質有沒有效?」 | **`not evaluated / not activated`(0/27 gene)**。這個問題在 tiny 上**從未被提出過**,因為從未有 treatment 被施加。**`NOT_EVALUATED ≠ 無效果`** —— 它連「無效果」都不是,它是「沒有問過」。 |
| **軌 (b) —— null-control 問題** | 「當真實效應可證明恰為零時,這條 pipeline 的 F/G 統計量長什麼樣子?」 | **MEASURED 5/5**(capped campaign)。這是本附冊真正有內容的部分,見 §3、§6。 |

兩軌**不可互相替代**。軌 (b) 有結果,**不代表**軌 (a) 有結果;軌 (a) 是 `NOT_EVALUATED`,
**不代表**可以說 guidance 對 tiny 沒用。

### 0.3 Scope note —— tiny 不在 native-P0 addendum 內

`NATIVE-P0-ROBUSTNESS-20260811` addendum(design §12,2026-08-12 經 `(b)` 擴充為 large + medium)
**明文排除 tiny**。design §12.2 (C):*"tiny 仍排除。tiny 的 Formocast 預測全為哨兵值
(30,490/30,490 = 100.00 %),activated gene = 0,兩臂的 Gen0 分布在建構上完全相同 → native 版
無 treatment 可測。"* `[CODE AUDIT]` 直接核對目錄:
`stage5_native_baseline/seed_24001/` 與 `stage5_native_guided/seed_24001/` **只含 `large/` 與
`medium/`**,無 `tiny/`。

因此 tiny **只有** capped(`DUCTILE_FORCE_P0=1`、`pop_size=512`)campaign,**不存在** native-P0
交叉核對。這是 `NOT_EVALUATED`,不是「no effect」。(附冊之所以仍要同時涵蓋 capped 與 native,
是 README 對 medium/large 的要求;tiny 的 native 半段依 design 為結構性不存在。)

### 0.4 三條禁止事項(先講,理由在 §7.4)

- ❌ 不得寫「**tiny 退步**」。
- ❌ 不得寫「**guidance 傷害了 tiny**」。
- ❌ 不得把 tiny 用於**任何 confirmatory 陳述**,任何方向皆然。

---

## 1. 配置、臂、seed、以及釘死了什麼

### 1.1 shape 與釘死的常數

| 項目 | 值 | 來源 |
|---|---|---|
| shape / size | **tiny `(M, N, batch, K) = (8, 8, 1, 128)`** | `s11/contract.py:674`(sealed);`champion_interleaved.json → size` |
| FLOPs(`2·M·N·K·B`) | **16,384** | 由 size 算出;`report-source-index.zh-Hant.md` §3.6.1 |
| 輸出元素數 | 64 | 同上 |
| `R_s`(正規化參考 GFLOP/s) | **0.751728** | `stage3_baseline/seed_*/tiny/champion_interleaved.json → R_s` |
| `η_tiny`(noise margin) | **0.44659979255188964** | 同上 → `eta_s`;Lock A `noise/per_shape_noise.json` |
| `δ_tiny` | **0.5629886544000939** | 同上 → `delta_s` |
| 非退步 floor `e^{−η}` | **0.6397999097337145** | 同上 → `nonregression_floor` |
| shape role | `exploratory` | `derivation-manifest-capped.json → per_shape_activation_log.tiny.shape_role` |

### 1.2 兩臂、seed、horizon

- **臂**:`G` = BASELINE(Gen0 對 free gene 用 uniform `p0`);`F` = GUIDED(Gen0 對 activated free
  gene 注入 capped `p1`)。**在 tiny 上 activated free gene 為 0,所以 F 退化為 G**(§2)。
- **seed**:5 對全新 seed **`24001–24005`**。
- **horizon**:`n_gen: 30` 上限 + 保留 Ductile 原生早停(`period: 5`);另從同一次跑擷取 gen-10
  檢查點。實際各 seed 的執行代數見 §6.4 Step 4。
- **Gen0**:`pop_size: 512` capped,以 `DUCTILE_FORCE_P0=1` fail-closed 強制。
  `[CODE AUDIT]` `champion_interleaved.json → measurement_metadata.environment.DUCTILE_FORCE_P0 = "1"`
  (五個 seed 皆然)。

### 1.3 量測協定(remeasure)

`[CODE AUDIT]` `stage3_baseline/seed_*/tiny/champion_interleaved.json → measurement_metadata`,
五個 seed 逐欄一致:

| 欄位 | 值 |
|---|---|
| `repeats_per_arm` | **7** |
| `single_measurements` | 14(= 7 × 2 臂) |
| `same_gpu` / `same_process` | `true` / `true` |
| `rotating_buffer_mb`(RBS) | **4096** |
| `DUCTILE_PERSIZE_RBS_expected` | `{"4096": [[8, 8, 1, 128]]}` |
| `num_elements_to_validate` | 128 |
| `start_arm` | **`G`**(五個 seed 全部) |

`START_ARM = {medium: G, large: F, tiny: G}` 是**逐 shape 的確定性 counterbalance**,
記載於 `report-source-index.zh-Hant.md` §8.4(`DEVIATION-REMEASURE-STOPLINE-20260812`)。
其對 tiny 的後果見 §8 威脅 3。

### 1.4 卡片配置與 remeasure 執行狀態

`[CODE AUDIT]` `stage3_baseline/seed_*/tiny/champion_interleaved_status.json`:

| seed | hip index | `verified_gpu_uuid` | `lock_a_expected_gpu_uuid` | 相符 | `status` | `exit_code` | `started_utc` – `finished_utc` |
|---|---:|---|---|:--:|---|---:|---|
| 24001 | 2 | `GPU-8cdaa86f8629c93a` | `GPU-8cdaa86f8629c93a` | ✔ | `PASS` | 0 | `2026-08-12T00:24:32.839999Z` – `00:25:32.959860Z` |
| 24002 | 3 | `GPU-eebf31642af31b3b` | `GPU-eebf31642af31b3b` | ✔ | `PASS` | 0 | `2026-08-12T01:50:30.902401Z` – `01:51:31.082454Z` |
| 24003 | 4 | `GPU-ac9e2fc9e28ca2fb` | `GPU-ac9e2fc9e28ca2fb` | ✔ | `PASS` | 0 | `2026-08-12T01:48:20.183011Z` – `01:49:20.196559Z` |
| 24004 | 7 | `GPU-bc724e0cf5b78d17` | `GPU-bc724e0cf5b78d17` | ✔ | `PASS` | 0 | `2026-08-12T00:54:35.313900Z` – `00:55:37.282260Z` |
| 24005 | 6 | `GPU-74a77207e38908fb` | `GPU-74a77207e38908fb` | ✔ | `PASS` | 0 | `2026-08-12T00:29:17.676534Z` – `00:30:22.985649Z` |

`lock_a_expected_gpu_uuid` 取自 `champion_interleaved.json → measurement_metadata`;
`verified_gpu_uuid` 取自同檔與 status 檔,兩者五個 seed 全部相符。**GPU 0 完全未使用**
(design §10.2:*"最多 6 張、絕不用 index 0"*);**GPU 5 從未用於 tiny 的 Lock-A remeasure**
—— hip 5 只出現在 §5、§6 的兩個 probe 中,那是**另外**的量測。

### 1.5 一個必須記錄的執行偏差(已修正)

`DEVIATION-REMEASURE-STOPLINE-20260812`:`remeasure_interleaved_champion.py`(run-root 下的腳本,
**非** sealed 碼、**非** Lock A)原本斷言「跑到 `n_gen=30` horizon」與「log 中含原生 early-stop 行」
互斥,實際不互斥。**seed 24002 的 tiny remeasure 因此在一次符合設計的 run 上被拒**,並因殘留的 FAIL
`champion_interleaved_status.json` 觸發次生的「artifact 已存在」阻擋。修正只動 pre-flight 斷言、
未動量測邏輯;腳本 sha256 `f2d11974…` →
`040db9cd5978f1b528f1acf8cf3460366f0c4c761b2443163be46bc69dc82b95`;FAIL 紀錄經使用者授權移至
`quarantine/stopline_bug_20260812/`。修正後 5/5 全部完成(見 §1.4 的時間戳:24002 完成於
01:51:31Z,晚於其餘四個)。*來源:`report-source-index.zh-Hant.md` §8.4。*

---

## 2. Null-control 主張 —— 在任何推論建立於其上之前先行驗證

本附冊 §6 之後的全部科學價值,都繫於一個主張:

> **在 tiny 上,Arm F 與 Arm G 是從相同分布抽 Gen0,因此真實 treatment effect 依構造恰為零。**

這個主張**不被斷言,只被檢查**。以下四份彼此獨立的 sealed artifact 全部一致,而且其中一份
(§2.3)給出的結論比主張所需的**更強**。

### 2.1 `[CODE AUDIT]` guidance 導出過程沒有啟動任何東西

*來源:`agent_run/260809-s14-pershape-guidance/derivation/derivation-manifest-capped.json`
(檔案 sha256 `ca310139040298af623acecb415b1f9ac87ecfa3845e899a3987e0d7d38ab8f7`,撰稿者重算)
→ `per_shape_activation_log.tiny`。*

| field | value |
|---|---|
| `shape_index` / `problem_size` | `0` / `[8, 8, 1, 128]` |
| `shape_role` | `exploratory` |
| `activated` | **`false`** |
| `n_genes_activated` | **0** |
| `n_genes_fallback` | **27**(全部 free gene) |
| `lambda_s` / `global_lambda` | `"na"` / `"na"` |
| `global_mean_s` | `0.5` |

逐 gene(全部 27 個 free gene,撰稿者逐鍵重算):

| 性質 | 觀測 |
|---|---|
| `activated` | **27/27 為 `false`** |
| `rho` | **27/27 為 `0.0`** |
| `TV_p1_vs_p0` / `KL_p1_p0` | **27/27 皆為 `0.0` / `0.0`** |
| `normalized_entropy_p0` / `_p1` | 24/27 恰為 `1.0`;其餘 3 個(`StaggerU`、`StoreSyncOpt`、`WorkGroupMappingXCC`)為 `0.9999999999999998` / `1.0000000000000002`,即浮點意義下的 1.0,且 `p0` 與 `p1` **完全相同** |
| `best` 與 `worst` value hash | **27/27 相同**(26 個為同一個非空字串;`DirectToVgprA` 兩者皆為 `null`) |
| `fallback_reason` | **26 個** `sensitivity_below_0_05`(且 `sensitivity` 恰為 `0.0`);**1 個**(`DirectToVgprA`)`fewer_than_two_trusted_values`(`n_trusted = 1`,`sensitivity` 為 `null`) |

> **相對於工作筆記的精確化(不是反駁)。** 已被本附冊取代的工作筆記
> `working-notes/s14-tiny-remeasure-analysis.md` §1.1 把逐 gene `sensitivity` 一律寫成 `0.0`。
> 重算顯示應為 **26 個 `0.0` + 1 個 `null`**(該 gene 連 sensitivity 都算不出來,因為 trusted 值
> 不足 2 個)。這與 `report-source-index.zh-Hant.md` §3.5 的淘汰表**完全吻合**
> (tiny:`S_g < 0.05` 26 個、trusted 值 < 2 者 1 個、activated 0 個),故為精確化而非矛盾。
> 兩種寫法對結論(0 個 gene 通過 activation gate)沒有任何影響。

**逐 gene `best == worst` 是 §6.4 那個機制的算術指紋。** Formocast 對 **100 %** 的 tiny config
回傳 sentinel `9,999,999.9`(`30,490 / 30,490`,由
`protocol/v1/manifests/s11-native-scores.json` 直接量得 ——
[`staged/s11-stage1-model-only-factorization-report.md:501`](s11-stage1-model-only-factorization-report.md))。
mid-ECDF 對一個**完全打平**的母體必然回傳 `r ≡ 0.5`,於是每個 config 得到相同 benefit、每個
per-value marginal 相同、27 個 free gene 的 `S_g = 0.0000`。沒有任何 gene 通過 activation gate
`(a) ≥2 trusted 值 ∧ (b) S_g ≥ 0.05 ∧ (c) per-shape direction 為正`(design §10.3)。

根因是一個明確的 early-terminate guard,不是模型 bug:`[CODE AUDIT]`
`shared/origami/src/simulator/tensilelite/formocast_simulator.cpp:578` 對 `M < 128 且
MT0 − M ≥ 16`(N 同理)的 config 直接回傳 `microSeconds = 9999999.9`。對 tiny(M=N=8)這要求
`MT0 ≤ 23 且 MT1 ≤ 23`,而實際候選池中 **434 個 MacroTile 只有 1 個**(`MT 16x16`)符合。
**詮釋:tiny 落在 Formocast 的建模範圍之外,不是「模型試了但失敗」。**
*來源:`report-source-index.zh-Hant.md` §3.6.2。*

### 2.2 `[CODE AUDIT]` weights 檔是均勻的 —— 沒有任何 gene 被引導

*來源:`agent_run/260809-s14-pershape-guidance/out-capped/ga-weights-tiny.json`
(sha256 `47213c239b38c5860602f50b3ab4df3ab03c1a220874ad37d6885bd1aa1e3939`,撰稿者重算)。*

- `activated: false`;`lambda_s: "na"`;`weight_beta: 0.25`。
- `weights_source_per_gene` 對 **全部 27 個 gene 都是 `"p0"`**(對照:medium 有 2 個 `"p1"`、
  large 有 5 個)。
- `rho_per_gene` 對 **全部 27 個 gene 都是 `0.0`**。
- `weights` → **27/27 個 per-gene weight vector 都是常數**(撰稿者逐 gene 檢查 `len(set(v)) == 1`,
  無一例外)。逐值重算:`DepthU` 為 `[7.1670379638671875] × 6`、`1LDSBuffer` 為
  `[2.7725887298583984] × 2`、`WorkGroupMapping` 為 `[11.561487197875977] × 18`,其餘依此類推。
  這些恰好是 `w(v) = −log(1/|V_g|)/β`(`β = 0.25`)—— 也就是把 **uniform 的 `p0` prior** 表達成
  Ductile 的 inverse-cost weight 單位。**常數 weight vector 在資訊上等同於沒有 weight vector。**

> **澄清,不是反駁。** 早期 brief 預期 `ga-weights-tiny.json` 會 *"carry only `group_0`"*。事實並非
> 如此:它帶了**全部 27 個 free gene**,皆為 uniform `p0`。「only `group_0`」這個性質屬於**被注入
> 的 GA config**(§2.3),不是這個檔案。`report-source-index.zh-Hant.md` §6 的
> *"Activated genes: … tiny=none"* 照字面**是正確的**。

### 2.3 `[CODE AUDIT]` 兩臂的 GA config **byte-identical** —— 這比主張本身更強

*來源:`config/s14-pershape-tiny-seed_2400{1..5}.yaml`(Arm G)與
`config/s14-pershape-guided-tiny-seed_2400{1..5}.yaml`(Arm F);撰稿者以 `sha256sum` 與 `diff`
逐對重算。*

| seed | sha256(**兩臂相同**) | `diff` |
|---|---|---|
| 24001 | `09b11a3b51259a6a3826b4f044309d90d59f4ca3249c144b2c776f52f57880eb` | 空 |
| 24002 | `8771d87b0dd5477e306deeed0d0a10196d880b48348efae26d8d2024ffcde55e` | 空 |
| 24003 | `7c438b4c68fed34ca4bc64545580a1559072b0cfa6fd1caa0a36a8a7422d99e6` | 空 |
| 24004 | `fbfa3ebd1ca53a887ef4b74c1beab3dd93728bd6e128997d56a97ba4be9e6676` | 空 |
| 24005 | `0c13a7c811f42659c39274f45acd5aaffc487b36c650e7a0dc3c2d9e7b058466` | 空 |

`Backend.Config.weights` 在兩臂中都**恰好只有一個 entry,`group_0`**(撰稿者掃描該 YAML 區塊,
`^    - <key>:` 層級只出現一次,即第 115034 行的 `- group_0:`,其下為 9,918 個候選權重值)。
group_0 = MatrixInstruction/WorkGroup 的 GEKO 加權群組,`report-source-index.zh-Hant.md` §3.7
記載其為 *"兩臂相同、treatment 從不碰它"*。同檔的 GA pins 亦逐行相同:
`pop_size: 512`、`n_gen: 30`、`max_iters: 437`、`period: 5`、`seed: <該 seed>`。

**對照組(證明這個 `diff` 有鑑別力):** 在受 treatment 的 shape 上,同樣的 `diff` 回傳真實差異 ——
`s14-pershape-medium-seed_24001.yaml` vs 其 guided 版新增 **10 行**(一個 `DepthU` + `1LDSBuffer`
weight 區塊);large 對應的 `diff` 新增 **29 行**。撰稿者以 `diff | wc -l` 重算(medium 11 行輸出
含 1 行 hunk header,large 30 行含 1 行 header)。

> **所以在 tiny 上,「F 與 G 從相同分布抽 Gen0」其實還說輕了:兩臂消耗的是字面上完全相同的檔案內容,
> 而且用同一個 GA seed。** 在 design §10.2 的 RNG pin(*"配對臂共用同一組 Gen0 uniforms、經 `p0` 或
> `p1` 映射(只差先驗)"*)之下,相同 uniforms + 相同 prior ⇒ **相同的 Gen0 母體**,而不只是同分布。

### 2.4 `[GUIDED GPU]` 建構期與執行期的佐證

*來源:`stage3_guided/seed_{24001..24005}/tiny/ga_init_evidence.json`;
`stage3_{baseline,guided}/seed_*/tiny/trajectory.jsonl` 的第一列(`gen == 1`)。*

五個 guided seed 的 `ga_init_evidence.json` **逐欄相同**(除 `seed` 與 `checkpoint_path`):
`weights_gene_keys: ["group_0"]`、`sampling_prob_genes: ["group_0"]`、
`weights_sha256: "56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f"`(跨 seed 相同)、
`pop_size_at_construction: 512`、`decay_type_at_construction: "none"`、`n_gen: 30`、`period: 5`、
`resume_requested: false`。Arm G 早於這項 instrumentation,**沒有**對應檔案 —— 由 §2.3 的
byte-identity 涵蓋(此不對稱記入 §8 威脅 5)。

Gen0 的 trajectory 列則從**經驗上**佐證母體同一性:

| seed | Gen0 best-config hash G == F | Gen0 valid / 512 (G / F) | Gen0 median-Q (G / F) | Gen0 best GFLOP/s (G / F) | Gen0 F/G |
|---|:--:|---|---|---|---:|
| 24001 | **YES**(`167dca0a…`) | 313 / 313 | 1.723722 / 1.733140 | 2.89087 / 2.88921 | 0.99943 |
| 24002 | **YES**(`8668ec55…`) | 321 / 321 | 1.668768 / 1.663807 | 2.80885 / 2.80201 | 0.99756 |
| 24003 | **no** | 289 / 289 | 1.698992 / 1.679690 | 2.92836 / 3.08467 | 1.05338 |
| 24004 | **YES**(`90cb5edb…`) | 273 / 273 | 1.762965 / 1.743955 | 3.04423 / 3.04557 | 1.00044 |
| 24005 | **YES**(`ab40aa13…`) | 308 / 308 | 1.681566 / 1.658752 | 2.89055 / 2.90379 | 1.00458 |

`generation_any_valid_count` —— 512 個 Gen0 個體中通過 KernelWriter／assembly build 並完成
benchmark 的數量 —— 在五個 seed 中**兩臂完全相等**(313、321、289、273、308)。該計數是抽出母體
的決定性性質;在 512 候選的抽樣上出現**五次精確一致**,不是兩個不同分布能碰巧達成的。

**唯一的例外 seed 24003 是被解釋,不是被辯護掉的。** Gen0 的 *best* 不同,但 valid count 相同。
Gen0 的 `best_hash_so_far` 是對*同樣*那 289 個候選、289 次**帶噪音的單次 GPU 量測**取 `argmax`。
兩個接近平手的候選加上一次帶噪音的抽樣就會翻轉 `argmax`;F 臂的 Gen0 best 量到高 5.34 %。
這是驅動整個結果的機制(§6.4)第一次現身:**在 tiny 上,selection 是由量測噪音決定的。**
這**不是** Gen0 分布不同的證據。

### 2.5 判定

> **判定:null-control 主張成立。** 在 tiny 上,沒有任何會影響 Gen0 抽樣的東西在兩臂間有差異
> —— 不在 guidance 導出層(§2.1)、不在 weights 檔層(§2.2)、不在被注入的 GA config 層(§2.3)、
> 也不在建構期與 Gen0 執行期的證據裡(§2.4)。
> **底下量到的任何 F/G 差異,其真值已知恰為零。** 本研究中沒有其他 shape 能這樣說。

---

## 3. 結果 —— 逐 seed、逐臂、完整

計算方式與 medium、large 相同:以 run-root 的 `gap_large.py` 邏輯(per-seed 表、median 列、
標記為誤導的 mean-of-raw-ratios 列)與 `analyze_large.py`(directional-consistency 各分量)
產出,另以 design §10.2 釘死的 AUC 公式交叉核對(§3.3)。撰稿者以 tiny 路徑重跑同一套邏輯。

### 3.1 Final-champion 7×-median 真實 GFLOPS

*來源:`stage3_baseline/seed_{24001..24005}/tiny/champion_interleaved.json` →
`median_gflops.{G,F}`、`F_over_G_median_ratio`、`F_over_G_median_log_ratio`、
`F_median_ge_G_median_times_exp_neg_eta_s`、`F_over_G_gt_one_plus_delta_s`。*

| seed | G median (GFLOP/s) | F median (GFLOP/s) | **F/G ratio** | **% change** | log-ratio `ln(F/G)` | card |
|---|---:|---:|---:|---:|---:|---|
| 24001 | 4.13644 | 3.65146 | 0.882754 | **−11.72 %** | −0.124708 | hip 2 |
| 24002 | 3.83508 | 3.96923 | 1.034980 | +3.50 % | +0.034382 | hip 3 |
| 24003 | 3.99704 | 3.53391 | 0.884132 | **−11.59 %** | −0.123149 | hip 4 |
| 24004 | 3.80317 | 3.78539 | 0.995325 | −0.47 % | −0.004686 | hip 7 |
| 24005 | 3.79733 | 3.67943 | 0.968952 | −3.10 % | −0.031540 | hip 6 |
| **median** | **3.83508** | **3.67943** | **0.968952** | **−3.10 %** | **−0.031540** | — |
| *(mean of raw ratios —— **誤導**)* | *3.913812* | *3.723884* | *0.953229* | *−4.68 %* | *(geo-mean 0.951286,−4.87 %)* | — |

**關於「mean of raw ratios」為何標為誤導。** `report-source-index.zh-Hant.md` §5b 給了四個理由:
(1) 原始比值不對稱(「快兩倍」= 2.0 距 1 有 1.0,「慢一半」= 0.5 距 1 只有 0.5);
(2) 本研究自己的 medium 資料就示範過這個偏誤;(3) 預註冊門檻本來就定義在 log 空間
(`η_s = P95(|log y − median log y|)`,floor `e^{−η_s}`);(4) GPU 吞吐量噪音是乘性的。
**分析用的量是 `ln(F/G)`**,原始比值僅因直觀而並列。

散布統計(撰稿者由上表重算):

- Raw-ratio 跨度 **0.882754 … 1.034980**(**1.1724×**)。
- `max |ln(F/G)| = 0.124708`;**`sd(ln(F/G)) = 0.071496`**。
- **1/5 為正;median −3.10 %。** 在預先登記的 ≥4/5 門檻下,final-champion 分量會不通過 —— 但
  **tiny 沒有 gate**,而且更重要的是**真實效應為零**,所以「1/5」量到的是這套機器在 n=5 下的
  方向性偏差,不是 treatment(§7.4)。
- n=5 的**精確雙尾符號檢定**:1/5 ⇒ **p = 0.375**(`2 × (C(5,0)+C(5,1)) / 2^5 = 12/32`)。
  在 n=5 下**沒有任何**分割能達到 p < 0.05;最極端的 5/5 或 0/5 給出 **p = 0.0625**。
  power 依構造就不高,而這**也不是**顯著性檢定(design §10.4:*"預註冊,非顯著性檢定"*)。

### 3.2 Directional-consistency 各分量

| component | positive seeds | 判定(僅供參考 —— **tiny 無 gate**) |
|---|---:|---|
| Gen0 best | **3/5** | 低於 4/5 |
| gen-10 best | **2/5** | 低於 4/5 |
| AUC(best-so-far,共同評估預算) | **2/5** | 低於 4/5 |
| final champion(7× median) | **1/5** | 低於 4/5 |
| final **non-regression** `F ≥ G·e^{−η_s}` | **5/5** 在釘死的 η = 0.4466 下;**2/5** 在 tiny 自身經驗重複性下 | **完全取決於 margin** —— 見 §3.4、§4.4 |
| final **improvement** `F > G·(1+δ_s)` | **0/5** 在釘死的 δ = 0.5630 下;1/5 在經驗 δ = 0.014574 下 | — |

逐 seed 明細(`analyze_large.py` 版面,套用於 tiny 路徑):

| seed | Gen0 G / F | d | gen-10 G / F | d | AUC F/G | d | final F/G | d |
|---|---|:--:|---|:--:|---:|:--:|---:|:--:|
| 24001 | 2.89087 / 2.88921 | − | 4.12421 / 3.58207 | − | 0.8967 | − | 0.8828 | − |
| 24002 | 2.80885 / 2.80201 | − | 3.64123 / 3.64811 | + | 0.9835 | − | 1.0350 | + |
| 24003 | 2.92836 / 3.08467 | + | 3.50418 / 3.50100 | − | 1.0106 | + | 0.8841 | − |
| 24004 | 3.04423 / 3.04557 | + | 3.79700 / 3.82234 | + | 1.0022 | + | 0.9953 | − |
| 24005 | 2.89055 / 2.90379 | + | 3.75903 / 3.67386 | − | 0.9850 | − | 0.9690 | − |

*來源:`stage3_{baseline,guided}/seed_*/tiny/trajectory.jsonl`(`best_gflops_so_far`、
`cumulative_complete_evals`、`gen`);final 欄取自 `champion_interleaved.json`。*

### 3.3 AUC 穩健性檢查 —— 兩個口徑都算了

`analyze_large.py` 是從 trajectory 的**第一列**起,對原始的 `best_gflops_so_far` 做 step-hold 積分。
design §10.2 釘死的卻是另一個 AUC:

```text
A = (1/B*) ∫_0^{B*} log( I(u) / R_s ) du
```

其中 `I(u)` = 右連續 incumbent、`u` = **post-Gen0** 的完成評估數、`B* = min(evals_G, evals_F)`
(同樣扣掉 Gen0)。**tiny 兩者都算了**(撰稿者實作釘死公式並重跑):

| seed | `B*`(post-Gen0) | `A_F − A_G`(釘死公式) | 方向 | `analyze_large.py` 形式 AUC F/G | 方向 |
|---|---:|---:|:--:|---:|:--:|
| 24001 | 7,356 | **−0.1051** | − | 0.8967 | − |
| 24002 | 8,121 | **−0.0167** | − | 0.9835 | − |
| 24003 | 7,808 | **+0.0109** | + | 1.0106 | + |
| 24004 | 7,297 | **+0.0023** | + | 1.0022 | + |
| 24005 | 7,649 | **−0.0141** | − | 0.9850 | − |
| **計數** | — | **2/5 為正** | | **2/5 為正** | |

**兩個公式在 tiny 上逐 seed 方向完全一致,所以 tiny 的 AUC 結論對採用哪一個公式並不敏感。**
不過「兩個公式竟然不同」這件事本身是一個對 formal report 有影響的發現(§9 項 5),因為
`report-source-index.zh-Hant.md` §7.1／§7.2 中 medium 與 large 的 AUC 判定是用**非釘死**的形式算的。

### 3.4 tiny 釘死的 margin 在結構上是空洞的 —— 凡引用「5/5 PASS」處都須註明

`η_tiny = 0.4466` ⇒ 非退步 floor `e^{−η} = 0.639800`。
`δ_tiny = 0.5630` ⇒ 改善 gate `F/G > 1.562989`。
實際觀測到的跨度是 **0.882754 … 1.034980**。

於是:

- 要**不通過**非退步,guided champion 得比 baseline **慢 36.0 %**;
- 要**通過**改善,得比 baseline **快 56.3 %**。

而 tiny 這個 shape 的**十個** champion(兩臂 × 五 seed)全部落在 **3.53391 – 4.13644 GFLOP/s**,
整個帶寬只有 **1.1705×**(`champion_interleaved.json → median_gflops`,撰稿者重算)。
以搜尋期 `best_fitness` 衡量則為 **3.61923 – 4.27906**,即 **1.1823×**
(`optimization_result.json → best_fitness[0]`,十次執行全部;
`report-source-index.zh-Hant.md` §9.2 引用的 *"tiny 1.182"* 對應的正是這個口徑,
而 design §13.5 所說的 *"champion 全距只有 1.18 倍"* 亦然)。

> **因此 tiny 的非退步結果不可能是 5/5 PASS 以外的任何結果,改善結果也不可能是 0/5 以外的任何結果。
> 這兩格帶有零資訊量,不得當作有資訊來報告。**

**根因。** `η_s` 是以 3-anchor × 7-repeat pilot 擬合的**量測重複性** margin
(`report-source-index.zh-Hant.md` §3.8),而 tiny 的 pilot 殘差極大。這裡有一個值得寫進報告的
**諷刺**:design §10.2 明文拒絕讓 tiny 汙染進入 aggregate(*"不用 tiny-汙染的 aggregate
delta_noise"*),但同一個汙染**仍然留在 tiny 自己的 per-shape margin 裡**。

---

## 4. 量測品質稽核(在任何詮釋**之前**完成)

`report-source-index.zh-Hant.md` §7.1a／§7.1b 已確立 7× remeasure 受到**單邊 dropout** 汙染:
medium 約 24–47 %(逐 campaign,見 §6.5)、large **0/70**。本節以原始重複值對 tiny 重做同一份稽核。

### 4.1 臂內散布與 dropout 普查 —— 全部 10 個臂

*來源:`stage3_baseline/seed_*/tiny/champion_interleaved.json` → `remeasure.{G,F}`;
原始順序與時間戳來自 `champion_interleaved_raw.jsonl`。dropout 定義同 §7.1a:**< 該臂最大值的 80 %**。*

| seed / arm | 7 次量測的 GFLOP/s(依量測順序) | max/min | dropouts |
|---|---|---:|---:|
| 24001 G | 4.12305 · 4.12149 · 4.13644 · 4.12188 · 4.15386 · 4.26820 · 4.15136 | 1.036× | 0 |
| 24001 F | 3.63427 · 3.64720 · 3.65146 · 3.65452 · 3.65625 · 3.64832 · 3.65645 | 1.006× | 0 |
| 24002 G | 3.83172 · 3.83508 · 3.83755 · 3.83564 · 3.83665 · 3.83295 · 3.83183 | 1.002× | 0 |
| 24002 F | 3.98333 · 3.93813 · 3.97078 · 3.96923 · 3.96143 · 3.97331 · 3.96048 | 1.011× | 0 |
| 24003 G | 3.97874 · 3.99631 · 4.01097 · 4.01012 · 3.97488 · 3.99704 · 4.01392 | 1.010× | 0 |
| 24003 F | 3.48778 · 3.54050 · 3.53391 · 3.51969 · 3.55056 · 3.54222 · 3.47936 | 1.020× | 0 |
| **24004 G** | 3.82056 · 3.80946 · 3.78233 · 3.83732 · 3.79491 · 3.80317 · **0.301263** | **12.737×** | **1** |
| 24004 F | 3.81234 · 3.81689 · 3.78255 · 3.77341 · 3.78539 · 3.77504 · 3.78659 | 1.012× | 0 |
| 24005 G | 3.79788 · 3.79119 · 3.79766 · 3.79722 · 3.79602 · 3.79755 · 3.79733 | 1.002× | 0 |
| 24005 F | 3.68397 · 3.67839 · 3.55749 · 3.67943 · 3.68221 · 3.68232 · 3.67839 | 1.036× | 0 |

**十個臂中有九個重複性極佳(max/min ≤ 1.036×)。** dropout 總計 **1 / 70 = 1.43 %**,與
`report-source-index.zh-Hant.md` §7.1a 的 tiny 列完全一致。`0.301263` 逐字元確認無誤,發生在
**hip 7**、seed 24004、**Arm G**。

### 4.2 這唯一一次 dropout 對 median 與對 P95 各造成什麼影響

| statistic | 實測(7 次重複) | 移除 dropout(6 次重複) | **納入** dropout 的影響 |
|---|---:|---:|---|
| seed-24004 Arm-G median | **3.803170** | 3.806315 | **−0.083 %** |
| seed-24004 F/G ratio | **0.995325** | 0.994503 | **+0.083 %** |
| P95 of \|log residual\|,**僅** seed-24004 Arm G(n=7) | **1.777606** | 0.007665 | **膨脹 232×** |
| P95 of \|log residual\|,pooled 於全部 70 次 tiny 重複 | **0.014469** | 0.012654 *(整臂完全排除,n=63)* | **+14 %** |

*撰稿者以 numpy `percentile`(linear／Hyndman–Fan Type-7)重算。*

- **median 紋風不動,正如預先登記的設計所意圖。** 七次中出現一次 dropout 只會讓 median 位移一個
  order statistic;第 4 個(共 7 個)值從第 3 與第 4 個乾淨值的中點移到第 3 個乾淨值。位移為
  **−0.083 %**,比它所吸收的擾動小三個數量級(該 dropout 讀值低了 **92.15 %**)。形式上,7 個值的
  median 可容忍最多 3 個 dropout(breakdown point `⌊(7−1)/2⌋ = 3`);7 取 1 離過半數還很遠。
  **這是 design §13.3 維持預註冊 median-of-7 的具體算術支撐(該決定仍為 `PENDING_HUMAN_DECISION`)。**
- **P95 的行為則相反,而且方向取決於 pool。** 在*那單一臂內*計算(n = 7)時,第 95 百分位落在該
  離群值上,讀出 **1.777606** —— 是同一臂無 dropout 值(0.007665)的 **232×**,也是 pooled tiny 值
  的 **123×**。若在整個 70 次重複的 pool 上計算,第 95 百分位大約是第 4 大的殘差,單一離群值搆不到
  它,該統計量只從 0.012654 移到 0.014469。
- **這正是 §7.1a 那句「P95 統計量看不見 1/70 的事件(那是第 98.6 百分位)」背後的具體算術。**
  其推論對本研究很重要:以 70 次重複擬合的 per-shape P95 **在結構上對罕見汙染是盲的**,所以
  「per-shape P95 說 tiny 是乾淨的」與「tiny 有一個 12.7× 的離群值」**兩句話都成立,彼此並不矛盾**。

### 4.3 這次 dropout 的根因是 `NOT_EVALUATED` —— 而且 medium 的機制**對它反證**

`report-source-index.zh-Hant.md` §7.1b 對 medium 的根因是:**warm-up 以 enqueue 次數而非時間指定**
(`ClientParameters.ini` 對三個 shape 一律 `num-warmups = 321`),在一個 ~10 µs 的 kernel 上只買到
約 3.2 ms,計時視窗在 DPM 狀態仍在爬升(idle 132–180 MHz → 2100 MHz 需數十毫秒)時就打開,結果由
power governor 的競速決定 —— 故為雙峰而非重尾。同一節也**直接量過 tiny**,發現其吞吐量
**對 warm-up 長度不變**,因此 medium 的機制不該適用於此(§5)。以下就 tiny 自身的證據檢視。

**與 clock-floor 事件(量級上)相符的證據:**

- 該 dropout 位於**其臂最大值的 0.078509**(`0.301263 / 3.83732`)。MI300X 的 DPM-floor 對峰值時脈比
  為 `165 / 2100 = 0.0786` —— 吻合到 0.1 %。散布 **12.737×** 與 `2100 / 165 = 12.727×` 吻合到 0.08 %。
- ⚠️ **但這個吻合必須以 `report-source-index.zh-Hant.md` §7.1b 已登錄的更正來讀。** 較早的草稿寫
  *"every dropout ever observed lies within `[0.0785, 0.7847]` … and the lower end matches the clock
  ratio"*;該下界**正是由這一次量測本身決定的**,所以「它落在觀測區間內」是**循環論證**。索引已把
  區間放寬為 **`[0.0742, 0.7847]`**(新下界來自 `tiny_gpu5_probe_summary.json`,見 §4.5),並把推論
  由 *matches* **弱化為 brackets**(把 clock 比值**夾在中間**,而非證實它)。**本附冊沿用弱化後的
  措辭。** 單一點與單一比值吻合,仍是薄弱的證據。

**反對 §7.1b warm-up 觸發機制的證據(三條獨立線索):**

1. **在 session 中的位置。** 該 dropout 是**第 7 次(共 7 次)重複**、位置 1(Arm G),時間戳
   `2026-08-12T00:55:34.178713Z`,即**一個 37.825 s 視窗中的第 34.729 s**;該卡在此期間已連續跑了
   **12 個** benchmark process,節奏 2.484–3.448 s。第 1–6 次重複 —— **包含真正冷啟動的第 1 次** ——
   **全部乾淨**。warm-up 太短會把風險集中在冷啟動;觀測到的模式**恰恰相反**。失敗那次重複之前的
   量測間隔(3.020 s)相對於該視窗的間隔範圍毫無異常。
   *來源:`stage3_baseline/seed_24004/tiny/champion_interleaved_raw.jsonl`,撰稿者逐列解析時間戳。*
2. **tiny 的 dropout 發生率不隨 warm-up 長度而下降。** `[GPU]` `tiny_mechanism_probe/summary.json`
   (卡 `GPU-4c517496fc501205` = hip 5;`started_utc 2026-08-12T14:58:51Z`、
   `finished_utc 15:00:41Z`;每個 variant **25 個全新 process**、idle-gated):

   | variant | overrides | median GFLOP/s | max/min | dropouts(< 最大值的 80 %) | wall median |
   |---|---|---:|---:|---:|---:|
   | `A_baseline` | production 設定(321 次 warm-up、RBS 4096) | 3.8 | 1.072 | **0 / 25** | 2.09 s |
   | `W321_norot` | 321 次 warm-up、RBS 0 | 4.0 | 1.046 | **0 / 25** | 0.62 s |
   | `W5136_norot` | **5,136** 次 warm-up(production 的 16×)、RBS 0 | 4.0 | **1.688** | **1 / 25**(第 19 次,位於最大值的 **0.60**) | 0.68 s |
   | `W20544_norot` | 20,544 次 warm-up、RBS 0 | 4.0 | 1.015 | **0 / 25** | 0.88 s |

   這 100 次掃描中**唯一**的 dropout 發生在 **production warm-up 的 16×**,而在 production warm-up
   下**一次都沒發生**。在 medium 上同一個旋鈕產生了乾淨的**單調膝點**(48 % → 32 % → 12 % → 8 % →
   0 %,§7.1b)。**§7.1b 的 warm-up 掃描是 medium 的結果,不能外推到 tiny。**
   (`A_baseline` 另有 1 次落在最大值的 0.933,低於 0.95 但**高於** 0.80,故依 §7.1a 的定義不計為
   dropout;此處如實揭露。)
3. **失敗的那個 process 並未卡住。** `W5136_norot` 離群值的 wall time 為 **0.65 s**,相對於該
   variant 的 **0.68 s** median —— 正常。*量到的 kernel rate* 偏低而 wall time **沒有**偏高,這與
   host 端 hang 或排程停滯**不一致**,卻與「GPU 在約 1.3 ms 的計時視窗中確實跑得很慢」一致。

**反對單純「全有全無 floor」讀法的證據。** 把所有曾經做過的 tiny 重複匯總 —— 70 次 Lock-A
(`champion_interleaved.json`)、70 次 hip-5 replication(`tiny_gpu5_probe_summary.json`)、
100 次 mechanism-probe(`tiny_mechanism_probe/summary.json`)= **240 次量測、4 次 dropout
(1.67 %)** —— 這些 dropout 的深度分別是其臂最大值的 **0.078509、0.074248、0.554416、0.60**。
**兩個在時脈 floor 附近、兩個在中段**,分布於**兩張不同的卡**(hip 7 與 hip 5),重複位置分別為
**7、1、5、19**。所以 tiny 也會產生*漸進式*的 dropout,而不只是 floor 式的;那個誘人的
「medium 是漸進式 / tiny 是二元」故事**並不成立**。

> **判定:`NOT_EVALUATED` —— tiny 的 dropout 機制未獲解釋。** 其**量級**與完整的 DPM-floor 時脈
> 狀態相容,但 §7.1b 的**觸發機制**(冷卡上 warm-up 太短)被位置、被 warm-up 掃描、被 wall-time
> 證據**反證**。任何已做的量測都無法區分的候選觸發機制包括:計時視窗*內部*的暫時性 governor 降頻;
> driver/queue 事件;firmware 功耗突波。要區分它們需要在計時視窗期間取樣時脈遙測,而 §7.1b.2 記載
> 此事在本 container 中不可能(`/sys` 唯讀、無 host root)。**本附冊不主張任何機制。**
> *已*確立的是其**後果**:該事件是**單邊的**(只會太慢,不會太快)、發生率介於 1/70 到 1/240 之間,
> 而且**不會移動 7 個值的 median**(§4.2)。
>
> design **§13.9**(`PENDING_HUMAN_DECISION`)已把這一項列入「須寫入報告、不求解決」的殘餘不確定性:
> *"tiny 的單一掉點(第 7 次 / 共 7 次,在 37.8 秒視窗的第 34.7 秒;掃描在 5,136 處非單調)為
> `NOT_EVALUATED`,且 medium 的機制對它反證。"*
> **⚠️ 因此不得把這次 dropout 悄悄歸因於 warm-up 機制。**

### 4.4 釘死的 η 對上 tiny 自身的經驗重複性 —— 以及兩者下的 gate 結果

依 Lock A 自己的定義 `η = P95(|log y − median_r log y|)` 重算噪音 margin,直接取自 tiny 自己的
70 次 remeasure 重複(撰稿者重算):

| estimate | value | 對比釘死的 η_tiny = 0.4466 |
|---|---:|---|
| **釘死值**(3-anchor × 7-repeat pilot;`noise/per_shape_noise.json`;design §10.2) | **0.44659979** | — |
| **經驗值**,pooled 於全部 70 次重複(median 取自各臂全部 7 值) | **0.01446886** | 釘死值保守 **30.9×** |
| 經驗值,僅乾淨重複(69 次,排除該 dropout,median 於乾淨子集內重算) | **0.01119850** | 釘死值保守 39.9× |
| 經驗值,排除整個 seed-24004-G 臂(63 次) | **0.01265423** | 釘死值保守 35.3× |

pooled 的 `0.014469` 與 `report-source-index.zh-Hant.md` §7.1a 的 tiny 列(`0.0145`,
*"31× conservative"*)到小數三位皆一致 —— 這是一次**獨立重算,與紀錄相符**。

**兩種 margin 下的 gate 結果**(兩種都報,如 §7.2a 對 large 的規定;design §13.4 亦要求
「pinned 治理不變、但必須完整揭露」,該決定為 `PENDING_HUMAN_DECISION`):

| seed | F/G | 釘死 η = 0.4466 → floor **0.639800** | 經驗 η = 0.014469 → floor **0.985635** |
|---|---:|---|---|
| 24001 | 0.882754 | PASS | **FAIL** |
| 24002 | 1.034980 | PASS | PASS |
| 24003 | 0.884132 | PASS | **FAIL** |
| 24004 | 0.995325 | PASS | PASS |
| 24005 | 0.968952 | PASS | **FAIL** |
| **median** | **0.968952** | **PASS**(0.968952 ≥ 0.639800) | **FAIL**(0.968952 < 0.985635) |
| | | **5/5 PASS** | **2/5 —— 未達成** |

改善 gate:釘死 δ = 0.5630(需 F/G > 1.562989)⇒ **0/5**;經驗 δ = `e^{0.014469} − 1 = 0.014574`
(需 F/G > 1.014574)⇒ **1/5**(僅 seed 24002)。

> **兩個判定都不是關於 treatment 的事實**,因為在 tiny 上 treatment 為零。它們量的是 **margin 有多鬆
> 或多緊**,不是 guidance 有沒有效。§7.3 會推導這對 large 上同樣的 margin 爭議意味著什麼。

### 4.5 GA 搜尋本身未受汙染 —— tiny 的證據

`report-source-index.zh-Hant.md` §7.1b.1 已對 medium 確立:缺陷侷限在 remeasure 路徑,未波及 GA 搜尋
(在一次長時間存活的搜尋 invocation 中,卡片全程都是暖的;只有短促而孤立的 remeasure session 會冷啟動)。
tiny 自身的一致性檢查:

- 搜尋期 `best_fitness` 值(十次執行)落在 **3.61923 – 4.27906**,與 remeasure 的 median 帶
  **3.53391 – 4.13644** 同一量級、逐臂對應,並帶有 §6.4 所述那個**小的單邊 winner's-curse 落差**,
  沒有退化的特徵。**champion 的*選擇*未受汙染。**
  > **相對於工作筆記的更正。** 工作筆記 §6.6 把該帶寫成 *"十次執行全部落在 3.81–4.28"*。撰稿者逐檔
  > 重算 `stage3_{baseline,guided}/seed_*/tiny/optimization_result.json → best_fitness[0]`,實際下界為
  > **3.61923**(seed 24003 Arm F),非 3.81。**正確帶寬為 3.61923 – 4.27906。** 結論(同一量級、
  > 無退化)不受影響。
- `report-source-index.zh-Hant.md` §9.2 / design §13.6 另記載:GA-oracle 疑慮已**降級為 residual**,
  且原本的 **Gen0 梯度論證予以撤回**(理由:`best_gflops_so_far` 依定義單調,模態樂透會預測同樣的
  觀察)。**取而代之**的有效證據之一,正是 tiny 這個「免疫 shape」提供的參照:
  `generation_Q_median_any_valid` 的逐代平均 |Δ| 在 **tiny 為 6.50 % / 4.21 %**、large 為
  6.98 % / 6.11 %,而 medium 的 5.58 % / 4.61 % 落在**兩者範圍之內**。

---

## 5. 為什麼 tiny 逃過了打中 medium 的量測缺陷 —— 這是一個**實測結果**,不是「沒發生」

這一節必須被讀成**正面結果**。tiny 沒有出現 medium 那種 24–47 % 的雙峰汙染,**不是**因為運氣好、
也**不是**因為「沒觀察到」;是因為 tiny 在物理上**對那個機制不敏感**,而且這件事**被直接量過**。

### 5.1 曝險需要**兩個**條件同時成立

`report-source-index.zh-Hant.md` §7.1b 的結論(直接引用其結構):

> *"要曝險必須**同時**具備短牆鐘視窗**與** clock 敏感性;只有 medium 兩者兼具。"*

| shape | kernel duration | 321 次 warm-up 的牆鐘時間 | clock 敏感性 | dropouts |
|---|---:|---:|---|---:|
| **medium** | ~10 µs | **~3.2 ms** | 敏感(14,001 → 14,375,隨 warm-up 上升) | 24–47 %(逐 campaign) |
| large | ~1.87 ms | ~600 ms(爬升所需時間的約 12 倍) | (視窗夠長,未曝險) | **0 / 70** |
| **tiny** | dispatch-bound | (視窗短) | **不敏感 —— 已實測** | **1 / 70** |

### 5.2 tiny 的 clock 不敏感性是量出來的

`[GPU]` `tiny_mechanism_probe/summary.json`:tiny 的吞吐量在
**321 次 warm-up 下為 4.0 GFLOP/s**(`W321_norot`),在 **20,544 次 warm-up 下仍為 4.0 GFLOP/s**
(`W20544_norot`)—— **warm-up 拉長 64 倍,測到的吞吐量不動**。同一個旋鈕在 medium 上把讀數從
14,001 推到 14,375。

**機制:** 在 **16,384 FLOP** 之下,tiny 的 kernel 時間幾乎全部是 **dispatch latency**,由
command processor 處理,**不受 shader clock 節制**。所以即使 GPU 停在 DPM floor,tiny 量到的數字
也幾乎不變 —— 它**看不見**時脈狀態。

### 5.3 這個結論的推論會**傷害一個較早的論證** —— 該論證已被撤回

較早的紀錄曾用「在 hip 5 上重測 tiny → hip 5 上 2/70、Lock-A 卡上 1/70,對比 medium 的 28 %」
來為 **hip 5 這張卡平反**(即:問題不是卡,是 shape)。

> **⚠️ 該論證已於 2026-08-13 撤回,並以另一個論證取代。撤回維持原有效力。**
>
> - **撤回內容(design §13.6「卡別平反」;`report-source-index.zh-Hant.md` §7.1b 的 CAVEAT):**
>   *"tiny-on-hip-5 的論證**撤回**(tiny 是最無法偵測時脈病理的工作負載)。"* 理由正是 §5.2:
>   既然 tiny **對整個機制不敏感**,那麼「hip 5 上 tiny 乾淨」是**不論** hip 5 有沒有時脈問題
>   **都會**看到的結果。它只排除了**嚴重的卡故障**,再細就排除不了了。
> - **取代它的論證(**卡內對照**,具決定性):** medium 自己的 **noise pilot 也跑在
>   `HIP_VISIBLE_DEVICES=5`**、同一 client、同樣 RBS 4096,卻是 **0/21 掉點**,而 medium 在**同一張
>   hip 5** 上的 remeasure 是 28 %。**同一張卡、同一個 shape、同一個 kernel** —— 所以卡不可能是那個
>   具鑑別力的變數;差別在於 pilot 的 anchor 慢 3–7 倍,因而牆鐘 warm-up 長得多。
> - **該取代論證自帶的 caveat(必須一併保留):** 2026-08-10 的重開機**改變了 GPU 編號**,
>   08-07 的 index 5 未必是 08-12 的同一顆實體晶片。

**因此本附冊的措辭紀律是:** tiny 的乾淨可以說明 **tiny 為什麼乾淨**;它**不能**為任何**對時脈敏感
的 workload** 的任何一張卡除罪。凡在報告中出現「tiny 在該卡上乾淨」時,必須同時出現這個限制。

### 5.4 附帶產出:一個被登錄的區間更正

`tiny_gpu5_probe_summary.json` 中 seed 24003 Arm F 第 1 次重複的讀值為
`0.267398`,其臂最大值為 `3.60144`,比值 **0.074248** —— **低於**較早草稿所述的下界 `0.0785`。
索引已據此把「所有曾觀察到的 dropout」區間放寬為 **`[0.0742, 0.7847]`**,並把
「lower end **matches** the clock ratio」弱化為 **brackets**(§4.3)。這是一個由 tiny 資料觸發、
且已寫進索引的更正。

---

## 6. 中心發現 —— 零 treatment 的對比仍然產生非零離散度

這是讓 tiny 值得寫一份附冊的發現。它必須自成一節,因為它**排除了那個顯而易見的緊縮式讀法**
(「tiny 的 ±12 % 只是量測樂透,跟 medium 一樣」)。

### 6.1 跨卡、跨 session 的獨立 replication

`[GPU]` `tiny_gpu5_probe_summary.json` 對**同樣五對 champion**重跑了**同一份 sealed remeasure 協定**,
在**不同的卡**(`card: "GPU-4c517496fc501205"`,`hip_index: 5`)、在**約 13.5 小時後的不同 session**
(`finished_utc: "2026-08-12T14:33:40Z"`,對比 Lock-A remeasure 的 00:24–01:51Z),過程中先擱置
(`held_aside`)再還原(`restored`)原始 artifact,`rc: 0`、`verified_gpu_uuid` 相符、idle-gated。

它原本是作為 §7.1b 的**卡片混淆控制**而跑的;其對 **F/G 統計量的 replication 價值,似乎在紀錄中
從未被使用過**(§9 項 9)。

| seed | Lock-A 卡上的 F/G | hip 5 上的 F/G | `ln` 差 | % 差 |
|---|---:|---:|---:|---:|
| 24001 | 0.882754 (hip 2) | 0.880834 | −0.00218 | −0.217 % |
| 24002 | 1.034980 (hip 3) | 1.035487 | +0.00049 | +0.049 % |
| 24003 | 0.884132 (hip 4) | 0.899425 | +0.01715 | **+1.730 %** |
| 24004 | 0.995325 (hip 7) | 0.999070 | +0.00376 | +0.376 % |
| 24005 | 0.968952 (hip 6) | 0.971117 | +0.00223 | +0.224 % |

`sd(ln difference) = 0.007519`;`max |ln difference| = 0.017150`。

**注意這次 replication 本身也對 dropout 穩健:** hip-5 的執行帶有 **2/70** 個 dropout
(seed 24003 Arm F 第 1 次重複,在最大值的 **0.074248**;seed 24004 Arm G 第 5 次重複,在最大值的
**0.554416**),**仍將每個 ratio 重現到 1.73 % 以內**。

### 6.2 log 空間中的變異數分解

| component | sd | 變異數占比 |
|---|---:|---:|
| 觀測到的跨 seed `ln(F/G)` 散布(Lock-A 卡) | **0.071496** | 100 % |
| *同一個* `ln(F/G)` 在**獨立卡 + 獨立 session** 上的可重現性 | **0.007519** | **1.11 %** |
| ⇒ 可歸因於**真實 champion 差異** | — | **98.89 %** |

> **tiny 的各 seed F/G 值不是量測樂透。它們是兩個真正不同的 kernel 之間真實、可重現的效能差異
> —— 而且是在可證明為零的 treatment 下產生的。**

### 6.3 佐證:兩臂的 champion 確實是不同的物件

*來源:`stage3_baseline/seed_*/tiny/champion_interleaved.json → arms.{G,F}`
(`canonical_hash`、`kernel_name`、`champion_kernel_params`);撰稿者逐 gene 比對 30 個 search-space key。*

| seed | `canonical_hash` G == F | Arm G MacroTile | Arm F MacroTile | 相異 gene 數 / 30 | 相異項是否含 `group_0` |
|---|:--:|---|---|---:|:--:|
| 24001 | **no** | `MT16x64x64_MI16x16x1` | `MT64x64x64_MI16x16x1` | **11** | ✔ |
| 24002 | **no** | `MT32x96x64_MI16x16x1` | `MT16x128x64_MI16x16x1` | **10** | ✔ |
| 24003 | **no** | `MT16x64x128_MI16x16x1` | `MT128x32x64_MI32x32x1` | **14** | ✔(另含 `group_1`) |
| 24004 | **no** | `MT32x96x64_MI16x16x1` | `MT32x96x64_MI16x16x1` | **11** | ✘(`group_0` 相同;相異的是 `group_1`) |
| 24005 | **no** | `MT64x48x64_MI16x16x1` | `MT64x64x64_MI32x32x1` | **9** | ✔ |

> **相對於工作筆記的更正。** 工作筆記 §4 寫 *"其中包含 `group_0` 的 `MatrixInstruction`,因而也包含
> MacroTile"*,語氣涵蓋全部五個 seed。逐 seed 重算顯示:**4/5 成立**(24001、24002、24003、24005);
> **seed 24004 的 `group_0` 兩臂完全相同、MacroTile 字串亦相同**(`MT32x96x64_MI16x16x1`),相異的是
> `group_1` 與另外 10 個 free gene。**兩臂 champion 在五個 seed 中全部不同**這個結論不受影響
> (`canonical_hash` 5/5 不同),但「一定包含 MacroTile」的說法必須收斂為 4/5。

**這件事本身是機制的一部分:** treatment 從不碰 `group_0`,但兩臂的 champion 仍在 `group_0` 上分歧
(4/5)。這只可能來自 **selection 路徑的分歧**(§6.4),不可能來自 prior。

### 6.4 根因 —— 相同的輸入如何產生 12 % 的輸出差異

以下每一步都是一個**機制**,不是把表格再講一次。

**Step 1 —— Gen0 完全相同(§2)。** 同一個檔案、同一個 seed、同一組 uniforms、同一個 prior。
同樣的 512 個個體;artifact 確認五個 seed 的 valid count 都相同(313/321/289/273/308,兩臂相等)。

**Step 2 —— Gen0 的 *fitness* 並不相同,因為 fitness 是 GPU 量測。** 在**個體完全相同**的母體上,
兩臂的 Gen0 median-Q 相差 **0.30 %–1.36 %**、Gen0 best-GFLOP/s 相差 **0.04 %–5.34 %**(§2.4 表)。
**這些差異就是量測噪音,而它們是唯一有差異的東西。**

**Step 3 —— 在 tiny 上那個噪音是決定性的,因為 fitness landscape 幾乎是平的。**
在 16,384 FLOP 下 tiny 是 **dispatch-latency-bound**(§5.2,由 probe 的 warm-up 不變性直接確認):
kernel 的時間都花在啟動額外負擔上,所以 kernel *configuration* 幾乎不重要。證據:

- 兩臂、五 seed 的**十個 champion 全部落在 3.53391 – 4.14 GFLOP/s** —— 一個 **1.1705×** 的帶;
- Gen0 的 best 已經是 **2.80201 – 3.08467**;
- 也就是說,GA 整整 **7,570 – 9,982 次評估**的搜尋,相對於自己的隨機起點只買到
  **+14.56 % 到 +43.09 %(median +29.04 %)**
  (撰稿者由 `champion_interleaved.json → median_gflops` 與各臂 trajectory 第一列重算,n=10)。

當候選之間的差距**小於量測噪音**時,`argmax` 就是在**對噪音做選擇**。這正是
`report-source-index.zh-Hant.md` §3.6.2 從**建模面**所描述的 regime(*"tiny 落在 Formocast 建模範圍
之外"*)在**量測面**的顯現 —— 同一個 regime,兩個獨立的面向。

**Step 4 —— 分歧不可逆且會累積。** design §10.2 在 Gen0 之後**重置**演化 RNG stream,但 selection 的
*輸入*(量到的 fitness)已經不同,所以**從第 1 代起 parent set 就不同**。兩臂接著在不同時點觸發
Ductile 原生的早停(`period: 5`、diversity floor):

| seed | 24001 | 24002 | 24003 | 24004 | 24005 |
|---|---:|---:|---:|---:|---:|
| Arm G 代數 | 20 | 24 | **30** | 22 | 23 |
| Arm F 代數 | 21 | **30** | 23 | 21 | 23 |
| Arm G 完成評估數 | 7,669 | 8,442 | 9,969 | 7,853 | 7,957 |
| Arm F 完成評估數 | 7,755 | 9,982 | 8,097 | 7,570 | 8,004 |
| 釘死的 post-Gen0 共同預算 `B*` | 7,356 | 8,121 | 7,808 | 7,297 | 7,649 |

*來源:`trajectory.jsonl` 末列的 `gen` 與 `cumulative_complete_evals`;
`optimization_result.json → generations_run` 交叉核對。*
**兩臂甚至拿到不同的評估預算** —— 這也是 AUC 必須積分到共同預算 `B*` 的原因(§3.3)。

**Step 5 —— 終點是兩個真正不同的 kernel,其真實效能差異最多達 12 %,且可重現(§6.1–§6.3)。**
champion 帶寬 **1.1705×** 與 F/G 散布跨度 **1.1724×** 幾乎相同 —— 也就是說,**tiny 的表觀 treatment
效應無非就是「從 GA 自身結果分布中抽兩次獨立樣本」**,而在這個 shape 上該分布寬約 1.17 倍。

**次要觀察 —— winner's curse 存在且很小。** 搜尋期的 `best_fitness` 在 **10/10 個臂**都高於
7×-median 的 remeasure,高出 **+0.34 % 到 +3.45 %**(以 remeasure median 為分母;若以 `best_fitness`
為分母則為 +0.34 % 到 +3.33 %)。這就是 remeasure 存在的理由之一(單次搜尋期讀值有樂觀偏差)。
它**不是** F/G 散布的來源 —— 該偏差是單邊的、且兩臂相近,所以在比值中大致抵銷。
*來源:`optimization_result.json → best_fitness[0]` 對比 `champion_interleaved.json → median_gflops`。*

### 6.5 本節貢獻的那個數字 —— 「零 treatment 下的表觀效應」的經驗下界

| shape | activated genes | true effect | median F/G | span | `sd(ln F/G)` | `max abs ln(F/G)` | positive | dropouts |
|---|---:|---|---:|---|---:|---:|---:|---:|
| **tiny**(null control) | **0** | **恰為 0** | **0.9690**(−3.10 %) | 0.8828–1.0350(**1.1724×**) | **0.0715** | **0.1247** | **1/5** | 1/70 |
| medium —— live campaign-2 | 2 | **未知** | 1.0274(+2.74 %) | 0.9884–1.0733(1.0858×) | 0.0340 | 0.0707 | 3/5 | 17/70(24.3 %) |
| medium —— campaign-1(**紀錄用**,design §13.3 提議,`PENDING_HUMAN_DECISION`) | 2 | **未知** | 0.9971(−0.29 %) | 0.3551–2.1175(5.9627×) | 0.6515 | 1.0354 | 2/5 | 32/70(45.7 %) |
| large | 5 | **未知** | 1.0006(+0.06 %) | 0.9279–1.0622(1.1448×) | 0.0530 | 0.0749 | 3/5 | **0/70** |

*來源(全部由撰稿者以同一段程式重算):tiny 與 large 取自
`stage3_baseline/seed_*/{tiny,large}/champion_interleaved.json`;medium campaign-2 取自 live 的
`stage3_baseline/seed_*/medium/champion_interleaved.json`;medium campaign-1 取自
`medium_recheck_control/capped/seed_*/preserved_campaign1_20260812T135613Z/champion_interleaved.campaign1_*.json`。
兩個 medium campaign **並列報告,不平均、不擇一**(design §13.3,`PENDING_HUMAN_DECISION`);
campaign 2 於 2026-08-12 14:01–14:04Z 在解盲後就地覆寫了 campaign 1,且對受測臂較有利。*

> **重點:在 treatment 可證明為零的那個 shape 上,這條 pipeline 產生的各 seed 表觀效應,
> 比兩個有 treatment 的 shape 都要大。**
> tiny 的 `sd(ln F/G) = 0.0715`,對比 large 的 **0.0530** 與 medium 乾淨 campaign-2 的 **0.0340**;
> `max |ln(F/G)|` 在 tiny 是 **0.1247**,對比 **0.0749** 與 **0.0707**。tiny 五個 seed 中有兩個
> 顯示 **−11.6 %** 與 **−11.7 %** 的「效應」。

**那個排序的根因(同樣是機制,不是裸事實):** 純機器效應的大小,由 **GA 在給定 shape 上自身結果
分布有多寬**決定,而後者又由 **fitness landscape 相對於噪音有多獎勵 configuration** 決定。

- tiny 的 landscape **是平的、由噪音主導** → 結果分布很寬(1.17×)。
- large 的則**由 main loop 主導、盆地很緊** —— `report-source-index.zh-Hant.md` §7.2 指出其 baseline
  臂跨 seed 只有 ±4.4 % 的跨度 → 結果分布很窄(1.13× 於 `best_fitness` 口徑)。

**有 treatment 的 shape 之所以比沒有 treatment 的機器噪音更小,是因為它們的物理特性,不是因為
treatment。**(這句話**兩個方向**都要讀:它既不支持也不反對 medium/large 上有效應。)

---

## 7. 雙軌結論 —— 能說什麼、不能說什麼,以及為什麼

### 7.1 軌 (a):guidance 問題 —— `not evaluated / not activated`

**可說(逐字):**

> **在 tiny `(8,8,1,128)` 上,Formocast 導出的 capped prior 未被啟用(0/27 free gene),
> 因此「guided initialization 對 tiny 有何效應」這個問題 `NOT_EVALUATED`。**
> 未啟用的原因是 `[MODEL-ONLY]` 且在跑之前就已知:Formocast 對 100 % 的 tiny config 回傳 sentinel
> 值,故所有 `S_g = 0.0000`,沒有 gene 能通過 activation gate。

**必須同時出現的但書:** **`NOT_EVALUATED ≠ 無效果`。** 而且在 tiny 上這句話比平常更強 ——
它連「試過但沒效」都不是,它是「**從未施加過 treatment**」。此外,依 charter §8.5,稀疏/微弱的
per-gene marginal 訊號必須**定位到層次**:tiny 的情形定位在 **模型建構範圍之外(out-of-modelled-regime)**,
**不得**寫成「模型沒用」。

### 7.2 軌 (b):null-control 問題 —— MEASURED,但 accidental

**可說(逐字):**

> **tiny 是一個意外的(accidental)null control。** 兩臂的 GA config byte-identical、0/27 gene 啟用,
> 因此真實效應依構造恰為零;在這個已知為零的對比上,這條 pipeline 仍產生 median −3.10 %、
> 各 seed 最高 −11.72 %、`sd(ln F/G) = 0.0715` 的**表觀效應**,且該效應在獨立卡與獨立 session 上
> **可重現**(變異數的 98.89 % 仍然存在)。

**「accidental」為何承重(必須一併陳述):**

1. **它不是被設計出來的。** 沒有預先登記的 null 假設、沒有為 null 挑選的 n、沒有 A/A 協定。
   把它當成 pre-registered null control 引用,是**證據等級的膨脹**。
2. **它的 n 是 5,而且形狀未知。** 五對配對樣本不足以構成 null distribution(§7.4)。
3. **它只涵蓋一個 shape、一個 regime。** tiny 是三個**刻意發散**的 regime 中的一個(§7.4)。
4. **它的存在來自一個 model-side 的失效(sentinel 主導),不是來自一個 control 設計。**
   同一個原因既給了我們 null,也讓這個 null 落在最極端的 landscape 上。

### 7.3 這允許什麼

- **給出這條 pipeline 在 n=5 下「無 treatment 之表觀效應」的經驗下界。** 在一個已知為 null 的
  shape 上:median |表觀效應| ≈ **3.1 %**、各 seed |表觀效應| 最高 **11.7 %**、
  `sd(ln) = 0.0715`、方向分割 **1/5**(`p = 0.375`)。日後任何在這條 pipeline 上宣稱**該量級**的
  各 seed 效應,都必須面對「零 treatment 在此就產生了它」這個事實。
- **一次同時打掉一個緊縮論證與一個膨脹論證。** 這個表觀效應**不是**量測樂透(§6.2:其變異數的
  98.89 % 在獨立卡與獨立 session 上仍然存在);所以在這條 pipeline 上,
  **「跨卡可重現 ⇒ 它是 treatment 效應」是無效的推理**。在不同隨機 stream 下的 GA 隨機性同樣可
  重現,因為它終止於**不同的 kernel**,而 kernel 的效能是穩定的。
- **補上 margin 爭議所缺的經驗資料點。** `report-source-index.zh-Hant.md` §7.2a 未解決 large 的
  非退步該以釘死的 η(5/5 PASS)或以經驗的 within-window η(3/5)來判定。tiny 回答的是
  **經驗 margin 對一個已知 null 會做什麼**:在 η_empirical = 0.014469 下,
  **null control 在 5 個 seed 中有 3 個被讀成退步,且在 median 上不通過**(§4.4)。
  理由是**結構性的,不是 tiny 的怪癖**:`η_s` 量的是量測**一個固定 config** 的重複性,而 `F/G`
  比較的是隨機搜尋產生的**兩個不同 config**。臂間離散度 ÷ within-window 重複性:
  **tiny 為 4.9×**(0.0715 / 0.014469)、**large 為 2.0×**(0.0530 / 0.0269)。在兩個 shape 上,
  `F/G` 的主導項都是 **GA 結果的變異性**,而量測重複性 margin **對它在任何方向上都沒有描述力**。
  design §13.4(`PENDING_HUMAN_DECISION`)已據此提議「維持 pinned η 治理、但雙 margin 完整揭露」,
  並明言 *"η 是錯的尺度"*。
- **顯示 tiny 釘死的 margin 是空洞的**(§3.4),使讀者不會把「tiny:5/5 非退步 PASS」誤當成一個結果。
- **作為 large 的參考包絡(**永遠不是門檻**)。** `report-source-index.zh-Hant.md` §9.2 記載此為
  design §13.4 的新增提議:large 每個 seed 的 `|ln F/G| ≤ 0.0749` 都落在 tiny 的零 treatment 包絡
  (最大 0.1247)之內。**但該包絡偏保守**,因為 large 是最平的 shape(`best_fitness` 口徑的
  champion 層級離散度:large 1.129、tiny 1.182、medium 1.222,撰稿者重算確認)。
  **這是參考包絡,不是 gate,也不是檢定。**(`PENDING_HUMAN_DECISION`。)

### 7.4 這**不**允許什麼 —— 以及為什麼

- **❌ 不得在數值上轉移到 medium 或 large。**
  *理由:* 三個 shape 是**刻意分歧的 regime**,不是平滑掃描(`report-source-index.zh-Hant.md` §3.6.1)。
  `η_tiny = 0.4466` 對 `η_medium = 0.0042`(**106×**)、`η_large = 0.1229`。tiny 是
  dispatch-latency-bound、0 個 activated gene;medium 是 loop-structure-bound、2 個;large 是
  memory-pipeline-bound、5 個,且不論 seed 為何基本上落在同一個盆地。GA 動態、噪音 margin、
  landscape 曲率與問題 regime 全都不同。**tiny 的 0.0715 不是其他 shape 的校正常數;把它從那些數字
  中扣掉的做法都站不住腳。**
- **❌ 不得構成一個 null distribution。**
  *理由:* 從形狀未知的分布中抽 **5 對**配對樣本,不足以支撐「零 treatment 有多常看起來像 X」的
  **分位數、CI 或 p 值**。以上全部都是**描述性**的。
- **❌ 不得據此說「medium 與 large 的效應只是機器」。**
  *理由:* §6.5 的比較是**啟發式的並列,不是檢定**。它說的是:large 觀測到的離散度*不大於*零 treatment
  在**另一個** shape 上所產生的。這值得一提且值得報告,但它**不是** large 效應為零的證據 ——
  **large 自身的機器變異從未被量測,因為 large 沒有 null 臂**。要量它需要在 large 上做一次
  **G-vs-G(A/A)replication**,而那**沒有跑**:`NOT_EVALUATED`(§9 項 10)。
- **❌ 不得寫「tiny 退步」。**
  *理由:* 「退步」是一個**因果詞**,它蘊含「有東西被施加了,而結果變差」。在 tiny 上**沒有東西被施加**
  (0/27 gene,config byte-identical)。把 −3.10 % 稱作「退步」,是把**兩次獨立的 GA 抽樣**誤述成
  **一個 treatment 的後果**。正確措辭是:「**在零 treatment 的對照上,量到 median F/G = 0.9690**」。
- **❌ 不得寫「guidance 傷害了 tiny」。**
  *理由:* 更強的同一個問題。這句話斷言了一個**不存在的 treatment 的方向性效應**。§2 的四份 artifact
  一致顯示 tiny 的 Arm F 就是 Arm G;說 guidance 傷害了它,在字面上等同於說 baseline 傷害了 baseline。
- **❌ 不得把 tiny 用於任何 confirmatory 陳述(任何方向)。**
  *理由(兩重):* (i) **治理上**,design §10.2/§10.4 依設計排除 tiny,並要求 medium ∧ large 的
  intersection-union(**不得用 aggregate 救**);把 tiny 帶進來就是事後改動預註冊的 gate。
  (ii) **科學上**,tiny 的軌 (a) 是 `NOT_EVALUATED` —— 一個從未施加 treatment 的臂,對
  「treatment 有沒有效」在**任何方向上**都不能貢獻證據。
- **❌ 不得把 tiny 的「5/5 非退步 PASS」當成正面結果。**
  *理由:* §3.4 —— 在 0.6398 的 floor 與 1.5630 的改善 gate 下,觀測跨度 0.8828–1.0350 **不可能**
  給出其他結果。那兩格帶有零資訊量。

### 7.5 tiny 對 conditional Arm S 的關係

**無。** `CONDITIONAL-ARM-S-20260810` 的 trigger 要求 **F 於 ≥1 個 confirmatory shape 通過
directional gate**(design §10.2)。tiny **不是** confirmatory shape,所以 tiny 在任何情況下都
**不能**觸發 Arm S,也不能阻止它。Arm S 是否觸發、以及 physics-direction 歸因是否 defer 到 S20,
**只由 formal report 依 medium 與 large 判定**。

---

## 8. 對 null-control 讀法的威脅 —— 明說而非帶過

1. **n = 5。** 在 n = 5 下,精確雙尾符號檢定在**任何**分割都達不到 p < 0.05(5/5 或 0/5 給出
   p = 0.0625;觀測到的 1/5 給出 p = 0.375)。**一切皆為描述性。**
2. **資料中含有一次 dropout。** 它對所報 median 的影響是 **−0.083 %**(§4.2),因此不改變任何結論,
   但該臂**並非純淨無瑕** —— 此處是**揭露而非修補**。
3. **起始臂在 shape *內部*未做 counterbalance。** 五個 tiny seed **全部從 G 起始**
   (`START_ARM[tiny] = G`);design §10.2 的 pin 寫的是 *"臂順序 counterbalanced(部分 seed G→F、
   部分 F→G)"*。實作是**跨 shape** 做 counterbalance(`{medium: G, large: F, tiny: G}`),
   `report-source-index.zh-Hant.md` §8.4 記載此為**刻意設計**。
   對 tiny 的後果:在每一次重複中,**Arm G 永遠占據冷的第 1 個位置**。因此任何 position-1 的懲罰
   都是**不利於 Arm G、有利於 Arm F** —— 而量到的 tiny 結果卻是 **F 為負**。
   **順序上的不對稱不可能製造出 tiny 的負向結果;若有影響,反而是遮蔽了一部分。**
   儘管如此,這仍是相對於 pin 字面規定的**殘餘偏離**,如實記錄。
4. **dropout 機制未獲解釋**(§4.3),原則上可能以 240 次重複普查無法解析的比率再次發生。
   它是**單邊的**(只會太慢),所以它對 median-of-7 估計量的最壞影響是**有界且很小**的。
5. **`ga_init_evidence.json` 只存在於 guided 臂。** baseline 臂的建構狀態是由 config 的 byte-identity
   (§2.3)涵蓋,**不是**由它自己的證據檔。這是一個**臂間的證據不對稱**,如實揭露。
6. **不存在任何跨視窗 / 跨日的重複性資料 —— 對任何 shape 皆然。** 因此**窗內 η 是一個緊度未知的
   下界**(design §13.9,`PENDING_HUMAN_DECISION`)。tiny 的 hip-5 replication(§6.1)是本研究中
   **最接近**跨 session 資料的東西,但它只有 **1 個額外 session、1 張額外的卡**,不構成跨視窗
   repeatability 研究。
7. **時脈機制整體上是被*推論*出來的,不是被鎖頻證實的。** design §13.9:*"時脈機制由暖機掃描、
   DPM 算術與 tiny 的實測時脈不敏感性**推論**而得;**無直接鎖頻證據**。"* 唯一能把它從推論變成
   實證的檢驗(`rocm-smi --setperflevel high`,需 `sudo`,約 10 分鐘、零研究 GPU 時數)列為
   design §13.7 的 **owner action**,`PENDING_HUMAN_DECISION`。
   另兩個誠實 caveat 必須一併保留:**鎖頻不是修復**(生產環境不能鎖),故該處為 null 不足以否定
   warm-up 說;且**先前那次嘗試必須如實報告為第二個對照組**(`setperflevel high` 後讀回仍是
   `Performance Level: auto`)。
8. **`replication` 的方向性尚未被檢驗。** §6.1 顯示 F/G 在跨卡下重現到 1.73 % 以內,但那是**同一對
   已固定的 champion** 的重現。「**重跑一次 GA** 會不會得到同樣的 F/G」是完全不同的問題,
   **`NOT_EVALUATED`** —— 而 §6.4 的機制**預測它不會**。
9. **medium 的量測缺陷處置整體上仍是 `PENDING_HUMAN_DECISION`**(design §13,九項)。本附冊凡引用
   §13 者皆已標註;若 owner 的裁決與 §13 的提議不同,本附冊中所有標 `PENDING_HUMAN_DECISION`
   的段落都須重讀。**tiny 自身的量測結果(§3、§4)不依賴那些裁決。**

---

## 9. 向 formal report 提報的事項 —— **尚未寫入任何 authority document**

依對現有紀錄改動幅度排序。**以下沒有任何一項已寫入 charter、experiment plan、S14 design、
`protocol/`、qa 檔,或 `report-source-index*.md`。** 本附冊**不代為修改**任何一份;
這是提報清單,不是變更紀錄。

1. **索引 §7 的 status 表已過期。** 它寫的是 *"7× interleaved G/F remeasure medians — tiny:
   `NOT_EVALUATED`(3/5 已重測;24002/24003 待跑)"* 與 *"Per-shape directional-consistency gate 結果
   … tiny `NOT_EVALUATED`"*。實際上 **5/5 全部完成且 `status: PASS`**
   (`champion_interleaved_status.json`,完成於 2026-08-12T00:25–01:51Z;seed 24002 是在
   `DEVIATION-REMEASURE-STOPLINE-20260812` 修正之後)。結果見本附冊 §3。
2. **§7.1a 的 dropout 區間已被 run root 中既有的資料推翻,且索引已登錄該更正。**
   舊敘述 *"every dropout ever observed lies within `[0.0785, 0.7847]` … the lower end matches the
   clock ratio `~165/2100 = 0.0786`"*;`tiny_gpu5_probe_summary.json` 含有一個位於 **0.074248** 的
   dropout(seed 24003 Arm F 第 1 次重複:`0.267398 / 3.60144`)。區間應為 **`[0.0742, 0.7847]`**,
   且推論由 *matches* 弱化為 **brackets**。**本附冊沿用更正後版本**(§4.3、§5.4)。
3. **§7.1b 的 warm-up 機制應限縮到 medium;tiny 的 dropout 成因是 `NOT_EVALUATED`。**
   `tiny_mechanism_probe/summary.json` 顯示 tiny 在掃描中唯一的 dropout 發生在 **5,136** 次 warm-up
   (production 的 16×),而在 321 次是 **0/25**、20,544 次也是 **0/25** —— **不隨 warm-up 長度單調
   變化**。加上 Lock-A 那次 dropout 是在**持續負載 34.729 s 之後的第 7 次(共 7 次)重複**,
   medium 的機制**對 tiny 被反證**。§7.1b 的單調膝點表格是 **medium 的結果**。見 §4.3。
   (design §13.9 已把此列為殘餘不確定性,但**索引 §7.1b 的表格本身尚未限縮**。)
4. **§7.2a 應引用 tiny。** 尚未解決的「釘死 vs 經驗」margin 問題,現在有了一個**已知為 null** 的
   資料點:在經驗 within-window η 下,tiny null control 讀出 **2/5 PASS、median FAIL**,亦即
   **經驗 margin 在真實效應恰為零之處宣告了退步**。根因:η 量的是**一個固定 config** 的重複性;
   `F/G` 比較的是**兩個不同的 champion**。見 §4.4、§7.3。
   (design §13.4 已採納此論證;`report-source-index.zh-Hant.md` §9.2 已鏡射;
   但兩者皆為 `PENDING_HUMAN_DECISION`,**索引 §7.2a 本文尚未更新**。)
5. **`analyze_large.py` 的 AUC 不是 design §10.2 釘死的 AUC。** pin 是
   `A = (1/B*)∫_0^{B*} log(I(u)/R_s) du`,積分於 **post-Gen0** 的評估;而該 script 是從 Gen0 那一列
   起積分**原始的** `best_gflops_so_far`。**在 tiny 上兩者都給 2/5**,所以 tiny 不受影響 ——
   但索引 §7.1／§7.2 中 **medium 與 large 的 AUC 分量是用非釘死的形式算的**,應在 formal report
   定稿前重新推導。見 §3.3。
6. **凡提及 tiny 的「5/5 非退步」之處,都要記載其釘死 margin 是空洞的**(§3.4):floor 0.639800 與
   改善 gate 1.562989,對上 0.882754–1.034980 的觀測跨度,意味著這兩格**不可能有別的結果**。
   另有一個值得寫一句的**諷刺**:design §10.2 拒絕使用 *"tiny-汙染的 aggregate delta_noise"*,
   但 tiny 自己的 per-shape `η_tiny` 卻帶著同樣的汙染。
7. **`§7.1c` 是一個懸空的 cross-reference。** `report-source-index.md` 為「max estimator 把 medium
   各 seed 的 F/G 收斂到 ±7 % 以內」一事引用了 *"(§7.1c)"*,但檔案中**不存在 §7.1c**。
   design §13.6 已把「索引 §7.1c 為斷鏈參照,須補寫或移除」列入必須更正的既有紀錄
   (`PENDING_HUMAN_DECISION`)。
8. **澄清,不是反駁:** `out-capped/ga-weights-tiny.json` 帶的是**全部 27 個 free gene、皆為 uniform
   `p0`**,不是「only `group_0`」。「only `group_0`」這個性質屬於 GA config 中被注入的
   `Backend.Config.weights` 區塊。索引 §6 的 *"Activated genes: … tiny=none"* **是正確的**。見 §2.2。
9. **目前未被使用的新證據:** `tiny_gpu5_probe_summary.json` 在 §7.1b 中**只**因其 dropout 計數
   (2/70,為 hip 5 除罪)而被引用 —— 而那個除罪論證本身**已被撤回**(§5.3)。同一份 artifact 同時
   也是**對全部五個 tiny F/G ratio 的獨立跨卡、跨 session replication**,誤差在 0.049 %–1.730 % 以內
   (§6.1)。**這正是把 tiny 從「有噪音的探索性 shape」升級為「帶有可重現非零表觀效應的 null
   control」的關鍵**,也是本附冊中最值得引用的一點。
10. **large 上的 A/A control 是 `NOT_EVALUATED`。** 要把 §6.5 的跨 shape 比較從**啟發式**變成**檢定**,
    最乾淨的做法是在 large 上做一次 **G-vs-G replication**(兩次 baseline 執行、不同 RNG stream、
    相同協定)。**它沒有跑,本附冊也不提議跑**;記下這個缺口,是為了確保「tiny 為 large 的機器變異
    定界」這句話**絕不會**在缺少它的情況下被主張。
    (design §13.7 項 1 提出的「合併式跨視窗 / A-A 實驗」與此重疊,`PENDING_HUMAN_DECISION`。)
11. **相對於已被本附冊取代的工作筆記,有三處數值精確化 / 更正**(每處都已在本文標註):
    (i) 逐 gene `sensitivity` 應為 26 個 `0.0` + 1 個 `null`,非 27 個 `0.0`(§2.1);
    (ii) 搜尋期 `best_fitness` 帶寬應為 **3.61923 – 4.27906**,非 3.81–4.28(§4.5);
    (iii) 「兩臂 champion 相異項包含 `group_0`／MacroTile」應為 **4/5 seed**,seed 24004 的 `group_0`
    與 MacroTile 兩臂相同(§6.3)。三處都**不改變**任何結論。

---

## 附錄 A —— Artifact ／ hash 索引(全部由撰稿者重算或直接讀取)

**Run root(baseline campaign):** `agent_run/260809-s14-pershape-baseline/`

| 路徑 | 內容 |
|---|---|
| `config/s14-pershape-tiny-seed_2400{1..5}.yaml` | Arm G 的 GA config;sha256 見 §2.3 |
| `config/s14-pershape-guided-tiny-seed_2400{1..5}.yaml` | Arm F 的 GA config;**與上者 byte-identical** |
| `stage3_baseline/seed_2400{1..5}/tiny/champion_interleaved.json` | 7× 交錯 remeasure、`median_gflops`、`F_over_G_*`、`eta_s`／`delta_s`／`nonregression_floor`、`arms.{G,F}`、`measurement_metadata` |
| `stage3_baseline/seed_2400{1..5}/tiny/champion_interleaved_raw.jsonl` | 14 列逐次量測(`arm`／`repeat`／`position_in_repeat`／`gflops`／`timestamp`)—— §4.3 的時序分析來源 |
| `stage3_baseline/seed_2400{1..5}/tiny/champion_interleaved_status.json` | `status: PASS`、`exit_code: 0`、`verified_gpu_uuid`、時間戳(§1.4) |
| `stage3_{baseline,guided}/seed_2400{1..5}/tiny/trajectory.jsonl` | 逐代 `best_gflops_so_far`／`best_hash_so_far`／`generation_any_valid_count`／`generation_Q_median_any_valid`／`cumulative_complete_evals` |
| `stage3_{baseline,guided}/seed_2400{1..5}/tiny/optimization_result.json` | `best_fitness[0]`、`best_individual_hashes`、`generations_run`、`cumulative_*` |
| `stage3_guided/seed_2400{1..5}/tiny/ga_init_evidence.json` | `weights_gene_keys: ["group_0"]`、`weights_sha256: 56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f`、`pop_size_at_construction: 512` |
| `tiny_gpu5_probe_summary.json` | hip 5(`GPU-4c517496fc501205`)跨卡跨 session replication;`finished_utc: 2026-08-12T14:33:40Z`;5 seeds × 2 arms × 7 repeats |
| `tiny_mechanism_probe/summary.json` | 4 variants × 25 process 的 warm-up 掃描;`2026-08-12T14:58:51Z` – `15:00:41Z` |
| `tiny_mechanism_probe/ClientParameters_{A_baseline,W321_norot,W5136_norot,W20544_norot}.ini` | 各 variant 的 override(可稽核) |
| `noise/per_shape_noise.json` | 釘死的 per-shape `η_s`／`δ_s` 來源(Lock A) |
| `quarantine/stopline_bug_20260812/` | §1.5 三份被移出的 FAIL 紀錄與其 README |
| `medium_recheck_control/capped/seed_*/preserved_campaign1_20260812T135613Z/` | §6.5 medium campaign-1(紀錄用)的保存路徑 |
| `stage5_native_{baseline,guided}/seed_*/` | **只含 `large/` 與 `medium/`** —— tiny 不在 native addendum 內(§0.3) |

**Guidance 導出(out-of-band,Lock B):** `agent_run/260809-s14-pershape-guidance/`

| 路徑 | sha256 / 內容 |
|---|---|
| `derivation/derivation-manifest-capped.json` | `ca310139040298af623acecb415b1f9ac87ecfa3845e899a3987e0d7d38ab8f7`;`per_shape_activation_log.tiny`(27 gene 逐一) |
| `out-capped/ga-weights-tiny.json` | `47213c239b38c5860602f50b3ab4df3ab03c1a220874ad37d6885bd1aa1e3939`;27 gene 全 uniform `p0` |
| `out-capped/guidance-tiny.json` | `43057c5942059a5a8eb3c528358092f0f8e3b1c6fca2971eb3254e06e2df46f5` |
| `lock/lock_b_guided_guidance.json` | `3ac9768768ac088596687c47635bd6b8b5018d67cecc3f08e69ba2857b0ce59b`(Lock B SEALED) |
| `verify-capped/verification-report-capped.md` | OVERALL PASS 40/40 |

**Code 引用(`[CODE AUDIT]`):**

| 位置 | 內容 |
|---|---|
| `shared/origami/src/simulator/tensilelite/formocast_simulator.cpp:578` | tiny sentinel guard(`microSeconds = 9999999.9`) |
| `protocol/v1/manifests/s11-native-scores.json` | tiny sentinel 比例 `30,490 / 30,490 = 100.00 %` |
| `protocol/v1/s11/contract.py:674` | 三個 locked problem size,含 `[8,8,1,128]` |
| `projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py:95, 110–118, 256–273, 293, 302–304` | `reduce_fn = np.max`;native Gen0 膨脹與 decay;`DUCTILE_FORCE_P0` 跳過膨脹並 fail-closed 斷言 |
| `ductile/config/defaults.yaml` | `pop_size: 512`;`period: 5`(早停於 `n_gen` 上限之外仍保留) |

**上游／同層文件:**

| 文件 | 用途 |
|---|---|
| [`full-ga-baseline-vs-guided-outcome-report.md`](full-ga-baseline-vs-guided-outcome-report.md) | **S14 唯一 formal report** —— gate 判定與 outcome 只在該檔 |
| [`../../s14-stage1-full-ga-outcome-design.md`](../../s14-stage1-full-ga-outcome-design.md) | **authority**;§10(ACTIVE 設計)、§12(native addendum)、§13(`PENDING_HUMAN_DECISION`) |
| [`report-source-index.md`](../report-source-index.md) / [`report-source-index.zh-Hant.md`](../report-source-index.zh-Hant.md) | **non-authority** 參考索引(雙語鏡射);本附冊優先引用 zh-Hant 鏡射的措辭 |
| [`staged/s11-stage1-model-only-factorization-report.md`](s11-stage1-model-only-factorization-report.md) | S11 terminal report;§10.4 為 tiny sentinel 的一手證據 |
| [`s14-medium-report.md`](s14-medium-report.md) / [`s14-large-report.md`](s14-large-report.md) | 另兩份 per-shape 附冊(confirmatory) |
| `working-notes/s14-tiny-remeasure-analysis.md` | **已被本附冊取代的工作輸入,不得引用**;其全部內容已折入本檔 |

---

## 附錄 B —— 一頁摘要(給趕時間的讀者)

| 問題 | 答案 |
|---|---|
| tiny 在 S14 的 gate 裡嗎? | **不在。** 探索性,design §10.2/§10.4 明文排除。 |
| guided prior 對 tiny 有效嗎? | **`NOT_EVALUATED / not activated`(0/27 gene)。`NOT_EVALUATED ≠ 無效果`。** |
| 為什麼一個 gene 都沒啟用? | Formocast 對 100 % 的 tiny config 回 sentinel 值 ⇒ 全部 `S_g = 0.0000`。tiny **落在模型建模範圍之外**,不是「模型試了但失敗」。 |
| 那兩臂差在哪裡? | **哪裡都不差。** 5/5 seed 的 GA config **byte-identical**(sha256 相同、`diff` 空),同一個 GA seed。 |
| 那為什麼 F/G 不是 1? | 因為 Gen0 的 **fitness 是 GPU 量測**,而 tiny 的 landscape 平到 `argmax` 是在選噪音;分歧自第 1 代起累積,終點是兩個真正不同的 kernel。 |
| 那個差異是量測噪音嗎? | **不是。** 跨卡、跨 session replication 顯示其變異數的 **98.89 %** 可重現。 |
| 最重要的一個數字 | **`sd(ln F/G) = 0.0715` 於零 treatment** —— 大於 large 的 0.0530、大於 medium 乾淨 campaign 的 0.0340。 |
| tiny 的「5/5 非退步 PASS」是好消息嗎? | **不是任何消息。** 要 FAIL 得慢 36 %、要 improve 得快 56 %,而整個 champion 帶只有 1.17–1.18×。**零資訊量。** |
| tiny 為什麼沒被 medium 的量測缺陷打到? | **實測**它 dispatch-bound、對 warm-up 長度不敏感(321 與 20,544 次都是 4.0 GFLOP/s)。曝險需要**短視窗 ∧ clock 敏感性**,tiny 缺後者。 |
| 那能不能用 tiny 幫某張卡除罪? | **不能,而且該論證已被撤回。** 正因為 tiny 對機制不敏感,「tiny 在該卡上乾淨」不論該卡有沒有問題都會發生。已改用**卡內對照**(medium 自己的 pilot 在同一張 hip 5 上 0/21)。 |
| tiny 自己那一次 dropout 呢? | **`NOT_EVALUATED`**;量級與 DPM floor 相容,但 medium 的觸發機制被位置(37.8 s 視窗的第 34.7 s、第 7/7 次)、warm-up 掃描與 wall-time 三條線索**反證**。**不得悄悄歸因。** |
| 一句話的禁令 | 不寫「tiny 退步」、不寫「guidance 傷害了 tiny」、不把 tiny 放進任何 confirmatory 陳述。 |

---

*本附冊於 2026-08-13 以**唯讀**方式對 sealed artifact 執行。未啟動任何實驗、未取得任何量測、
未修改任何 artifact,亦未修改本檔以外的任何文件。重算使用 run root 中 `gap_large.py` 與
`analyze_large.py` 的邏輯(套用於 tiny 路徑),另以 design §10.2 釘死的 AUC 公式獨立實作交叉核對。
無 seal、無 commit、無 push。*
