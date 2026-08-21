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
> `not_evaluated ≠ no effect`。**最後更新 2026-08-18。**
>
> **目前執行實況(2026-08-18):** **capped(P0 = 512)** campaign 在**三個 shape 上全部完成** ——
> baseline 15/15、guided 15/15,medium、large 與 tiny 的 7× interleaved 重測也都做完了。
> **native(P0 = 11,405)** addendum **在 medium 與 large 上都已完成**:native large 於
> **2026-08-17 13:13–13:27** 收工,其 N1–N5 諸表已由實測 artifact 填妥
> (`staged/s14-large-report.md` §7.6)。另有**七個 cell 於 2026-08-17/18 執行** ——
> medium 的儀器修復、六個 null construction,以及 large capped 的一個跨 window 真實對照 ——
> 報告於 **§7.0 – §7.6**。
>
> **⚠ 本段取代了一份 2026-08-14 的快照,那份快照已有四處為偽。** 它先前說 native addendum
> 「large 仍在跑」、說「Gen0 評估進行中」、說 `completion` 「仍是 `{done: 0, total: 10}`」,以及
> 「native large 是否可達仍是待 owner 裁決的開放問題」。這四句在寫下當時都為真,現在沒有一句為真。
> 前一台主機上的重開機歷史(`hostmove_deviation.md` §7:連續六次 Gen0 損失)以及 2026-08-14
> 遷往 `banff-cyxtera-s77-4` 的換機(§8.6),作為紀錄保留。
>
> **⚠ 權威註記。** `staged/full-ga-baseline-vs-guided-outcome-report.md` 已**經 owner
> 撤銷授權(2026-08-18)**。S14 的 gate 判定現在由 `staged/s14-guided-results.md` §5.4 承載,
> 並在本檔 **§7.0.1** 重製。本索引與那四份黃金文件不一致時 ——
> `/data1/perlee/measurement_design.md`、`staged/s14-medium-report.md`、
> `staged/s14-large-report.md`、`staged/s14-guided-results.md` —— **以那四份為準。**
>
> 2026-08-13 有兩件事改變了證據面貌,並已反映在全文各處:**clock-ramp 機制被直接遙測否證**
> (warm-up 的*相關性*成立;*解釋*不成立 —— §7.1b);以及 S14 的各份報告依 `REPORT-LOCATION-20260813`
> 被整併進 `reports/staged/`,成為一份正式報告加三份 per-shape 附冊(§6)。
>
> **不要引用「九項」這個總數 —— 逐項狀態見 §8.7。** 原本那九項 `PENDING_HUMAN_DECISION` 中:
> **第 3 項的 ratify 半已於 2026-08-15 關閉**(owner 裁決 —— 兩個 campaign *皆非* measurement of
> record;§7.1a)、**第 5 項已於 2026-08-14 關閉**(`ETA-MARGIN-REMOVED-20260814`;§7.0.2)、
> **第 2 項的條件因不可行而關閉**(§7.5)。**另於 2026-08-14 新增一項**(§8.7 第 6 項,Lock A 的封存狀態)。
> 合併 claim 的措辭需要 medium ∧ large
> (**charter** §8.2 —— 不是本檔的 §8.2,那是 Checkpointing)。



## Contents

- [§0 Conventions](#0-conventions)
- [§1 實驗一覽](#1-實驗一覽experiments-at-a-glance)
- [§2 Amendment ledger](#2-amendment-ledgertoken--變更--權威來源)
- [§3 設計理由](#3-設計理由報告可直接引用的散文--每條附來源) —— 含 [§3.8.2 tiny 到底控制住了什麼](#382-tiny-到底控制住了什麼--它的包絡裡有搜尋發散不只是量測誤差)
- [§4 Claim 框架](#4-claim-框架什麼能說--不能說)
- [§5 Metrics & acceptance](#5-metrics--acceptance) —— 含 [§5c AUC](#5c-auc-準則是什麼以及為何量測缺陷波及不到它)、[§5d 四個 gate 量實際上怎麼量](#5d-四個-gate-量實際上是怎麼量出來的以及為何其中三個比第四個更耐雜訊)
- [§6 Artifact / file reference](#6-artifact--file-reference)
- [§7 結果](#7-結果--s14-gate-判定與四個被量測的量) —— 含 **[§7.0 gate 判定 + 四個量](#70-s14-gate-判定與四個被量測的量四個-block-全數)**、[§7.4 跨 shape 比較](#74-跨-shape-比較--四個-block-並排)、[§7.5 儀器修復前後對照](#75-儀器修復--前與後medium)、**[§7.6 什麼能說、什麼不能說](#76-什麼能說什麼不能說)**
- [§8 已知 caveat / 限制](#8-已知-caveat--限制供-discussion-章節) —— 含 **§8.5 第三次就地覆寫(TOCTOU)**、**§8.6 2026-08-14 的換機**、**§8.7 2026-08-17/18 campaign 的未結項**
- [§9 已刪除的章節 —— 它們的內容去了哪裡](#9-已刪除的章節--它們的內容去了哪裡)

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


| Experiment                                  | 目的                                                                        | 狀態(2026-08-18)                                                                                                      | 關鍵 artifact / lock                                          | 報告章節                         |
| ------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------- |
| **S11 model-only factorization**            | per-gene Formocast→Gen0 guidance 機制在模型空間是否成立;訊號多稀疏                        | per-size scores **DONE**;max-reducer closeout **無法完成** —— 封存 `analyze` 結構性 assert(見 §7.3),已由經驗證的 out-of-band 平行重製證實 | `s11-native-scores.json`;`parallel-analyze/VERIFICATION.md` | S11 report                   |
| **S14 capped-512 per-shape G/F**(主)         | 在 P0=512 下,Formocast Gen0 prior 是否讓每個 shape 的搜尋/最終品質優於 uniform            | **COMPLETE** —— baseline 15/15、guided 15/15,三個 shape 的 7× 重測皆已完成(`guided_status.json`:`guided_complete: true`) | Lock A + Lock B                                             | `staged/full-ga-baseline-vs-guided-outcome-report.md` §3 |
| **Conditional Arm S**(same-entropy shuffle) | 把 F>G 歸因於 physics *方向* 而非單純集中                                             | **DOES NOT TRIGGER** —— 觸發條件要求 F 在 ≥1 個 confirmatory shape 上過 gate;medium 與 large 都沒有(§7.0.1)。因此本 checkpoint 不需要封 Lock C | Lock C(Arm-S shuffle,不需封存)                                  | `staged/full-ga-baseline-vs-guided-outcome-report.md` §3.5 |
| **Native-P0 ~11,405 addendum —— medium**    | (Q1) capped 方向在原生 Gen0 是否穩健;(Q2) 稀釋;(Q3) Gen0 極值機制                        | **COMPLETE** 5/5 GA + 5/5 重測(另已重測兩次;campaign 更正見 §7.6)。最終端點為 `NOT_EVALUATED / instrument-invalid`                    | 重用 Lock B guidance                                          | `staged/s14-medium-report.md` §4 |
| **Native-P0 ~11,405 addendum —— large**     | 在 large 上問同樣三個問題                                                          | **COMPLETE** —— 於 **2026-08-17 13:13–13:27** 收工;N1–N5 諸表已由實測 artifact 填妥。(2026-08-18 更正:本列先前寫的是 *IN PROGRESS —— Gen0 抽樣完成、Gen0 評估進行中、`completion {done: 0, total: 10}`*,那是 2026-08-13 的快照。在**前一台**主機上被重開機吃掉的**六**次 Gen0,§8.6,作為紀錄保留。)Q3 的預測 (iii) 是 **`REFUTED`**,不是 `NOT_EVALUATED` | 重用 Lock B guidance | `staged/s14-large-report.md` §10 |
| **儀器修復 + null campaign**(2026-08-17/18) | 修復 medium 的 7× 儀器,再為四個 block 全數提供一個雜訊基準 | **COMPLETE** —— 修復已驗證(P1/P1b/P3/P4′);2026-08-18 另有**七個 cell**:六個 null(每個 block 各一組 G/G′ 與 F/F′)加上 large capped 的一個跨 window 真實對照。**剩下的缺口:修復後的儀器沒有任何跨 session 資料** | `medium_pilot401/results/`(17 個 cell)、`large_xwindow/results/`(6 個 tag) | **§7.0 – §7.6**;`/data1/perlee/measurement_design.md` §E.5 |


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
| `CAPABILITY-ENDPOINT-PACKET-20260813` | `PENDING_HUMAN_DECISION` —— 以三項彼此獨立的理由駁回 peak-of-7 作為 medium 的端點;記載 count-invariance 主張為**偽**(`max` 在兩個 native campaign 上都把預註冊的 §12.3 ≥4/5 判準往受測臂方向跨過去);禁止 `max` 出現在任何 acceptance/sensitivity 表格;以一個決定性的 `int32` 溢位結案 §13.7 item 2 | S14 design **§14**;本索引 **§7.5** |
| `MEASUREMENT-DEFECT-PACKET-20260813` | `PENDING_HUMAN_DECISION` —— medium 重測缺陷的處置:估計量(D1)、margin(D2)、逐 shape claim 階梯(D3),共九項待 owner 裁決 **(其中八項仍未結案 —— 第 5 項已於 2026-08-14 裁決;§8.7)** | S14 design **§13**;本索引 **§7.0.1** |
| `REDUCER-FACT-CORRECTION-20260812` | **僅文件層的事實更正** —— Ductile **未實作 Pareto/非支配排序**;`soo=False` 以 `np.max` 縮併為純量(`ga.py:95, 256–273`),故 `Q=max_s` 是 Ductile 的**原生** fitness,不是事後外加的步驟。**決策、pins、gate、claim 一律不變**;per-shape 的實證理由(tiny 主導 Q、seed-14005)不受影響 —— 更正後的論述是「Ductile **內建**的跨-size reducer 本身即缺陷,per-shape 繞開它」。 | S14 §10.1 更正框;qa-09 §2.1/§2.2;本索引 §3.1.2                             |
| —— 2026-08-14 記錄更正(無 token) | **純文件層級。** 撤回 2026-08-13 那個「計數已更正」的框,並恢復 `38 / 140` 與 `39 / 140`(§7.1a);記錄**第三次就地覆寫**及其 TOCTOU 成因(**§8.5**);記錄 **2026-08-14 的換機**(**§8.6**);記錄 Lock A 的**兩次封存後編輯**與目前的 `.sha256`(§6);更正 `group_0` 的逐 entry sha256 歸屬(§3.2c、§3.7)、free-gene 計數(**27**)與基數範圍(**2–18**)(§3.2a、§3.4b.4)、P17 的時脈統計量(§7.1b),以及 diversity 交叉代數的主張(§3.2b)。把 owner 第 2 項重述為**因不可行而關閉**(§7.5)。**不改變任何 hypothesis、estimand、metric、門檻、gate 或 claim。** 新開啟一項 owner 事項(**§8.7 第 6 項**) | 本索引 §7.1a、§8.5、§8.6、§6、§8.7 第 6 項、§7.6 |
| `ETA-MARGIN-REMOVED-20260814` | **經 owner 授權** —— 移除逐 shape 的 noise margin `η_s` 以及第四個 gate 分項 `final ratio ≥ e^{−η_s}` **作為 gate 組成的地位**。final ratio 仍然**照常報告**(方向 + effect size,附既有 caveat);它**不再被 gate**,而且**不登錄任何替代門檻**。依據:在新 host 上重現原始 pilot,結果**只有 `η_large` 重現得出來**。**對判定的影響:無** —— 僅憑三個沒有 margin 的分項,gate 在兩個 confirmatory shape 上都是 NOT MET。取代 §7.6 **D2** 與 §8.7 第 5 項。`δ_s` / improvement 準則**不在範圍內,維持不變** | 本索引 **§7.0.2**;S14 design(由 owner 另行修訂) —— **provenance 終於在 2026-08-18 記錄進 `measurement_design.md` §H.4;在那之前,這個 token 在三份權威文件裡的命中數都是零** |
| `NO-SEPARATION-20260817` | **經 owner 授權** —— 移除量測 window 之間 ≥ 2 小時的間隔;campaign 改為背靠背地跑。**同時登錄的代價:** 背靠背的 window 共享 slow layer,`k_effective` 遠低於 `k`,而且 **slow layer 維持 `NOT_EVALUATED`**。這對每一個 2026-08-17 的結果的後果是:它們只涵蓋 **fast layer** | `measurement_design.md` §G.1(規則本體)、§H.1 row L(登錄) |
| `NULL-AS-NOISE-BASELINE-20260818` | **經 owner 授權** —— `F/G` 的判定規則:直接比較 arm F / arm G,並以 **null ratio 作為雜訊基準**。**把每一個可得的雜訊尺度並列報告;不得把它們收斂成單一判定;不登錄任何倍數門檻。** 填上 `ETA-MARGIN-REMOVED-20260814` 刻意留空的那個位置。**因為它不登錄任何門檻,依 `experiment-artifact-governance.md` §4 它不算 post-label 的門檻變更。** 目前有四個尺度在使用,每一個都附帶明示的限制 —— 特別是 G/G′ 這種 null **在構造上永遠不會載入 arm F 的 kernel**(seed 24004:G/G′ 的 sd 為 `0.00155`,對比真實對照本身的 `0.01807`,相差 **11.6** 倍) | `measurement_design.md` **§G.3.1**(規則本體)、§H.1 row M(登錄);已套用於 `staged/s14-medium-report.md` §18.3 |


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
>    根本不存在,所以那個特定引用必須讀成 **engine** 那一份;在那裡 `DUCTILE_FORCE_P0`
>    **首次出現在 `ga.py:111`**,`:112` 是那個分支判斷。四次出現分別在:**111、117、302、304**。
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
- **(b) 不偏 G-vs-F 配對對比。** 兩臂皆從**同一張機率表**抽 group_0,而該表**不帶任何 treatment** ——
所以被縮小的覆蓋是兩臂共享的邊界條件,在組內差中抵銷,只剩 free-gene 重加權為唯一外生差異。
  > **⚠ 事實更正,純文件層級,2026-08-14。** 本條原文為「兩臂皆以相同 p0、common Gen0 uniforms 抽
  > group_0」。這兩個子句**都**是錯的,兩者皆已移除;**結論不變**。
  > 1. **不是 `p0`。** group_0 的機率表是 **GEKO 導出的非均勻**向量,不是均勻的 `p0`:
  >    `Σp² = 1.753982e-04`,而均勻應為 `1/9,918 = 1.008268e-04`,即**有效基數約 5,701**,不是 9,918。
  >    §3.2a 早就寫過這件事(「GEKO **加權**(非均勻)」),只有 §3.2 沒寫。
  > 2. **不是「common Gen0 uniforms」。** 兩臂**並未**共用 Gen0 抽樣。只要 guidance 有啟動,兩臂的抽樣
  >    stream 從**第一次**抽取就開始發散,因此 group_0 在兩臂是在*不同的 stream 位置*被抽出的(§3.2c)。
  >
  > 真正承重的事實是這張表在**兩臂之間相同** —— 不是它均勻,也不是抽樣共用。已驗證:`group_0` weights
  > 條目的**逐 entry** canonical sha256 在**兩臂**、**三個 shape** 上都是
  > `3c5a30f77ac6531b37ac0cb5573d717e9b82cd83e5414c9be22787ec6630b472`(§3.2c)。
  > ⚠ **2026-08-14 更正** —— 此處先前寫的是
  > `56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f`,那是**整份 `weights` list**
  > 的 hash,只有在該 list 剛好只有一筆記錄時才會與 entry hash 相同。結論不變、而且為真;錯的只是
  > 識別字。這次更正付出的代價只有控制*強度*:對比是**以 seed 配對**,不是以共用亂數配對。

Caveat:量到的是「P0=512 下的效應」(**treatment×budget 交互作用**),由 native addendum(§3.3)探討。

*來源:S14 §6.1/§10.2、S14 report §2.3。*

### §3.2a `9,918` 與 `×1.15` 是怎麼來的

`max_sp_sz` **其實就是「候選清單最長的那個 gene 的長度」。** `space.py:71` 定義
`self.sizes = {k: len(v) for k, v in space.items()}` —— 一個 gene 的「size」字面上就是*它的候選清單有幾個
條目*。`ga.py:112` 再取 `max_sp_sz = max(sz for sz in self.space.sizes.values())`(對全部 30 個 key)。
**27 個 free gene 每個有 2–18 個值**(最大的是 `WorkGroupMapping` 的 18),所以整個空間的最大值由
`group_0` 決定。

> ⚠ **此處於 2026-08-14 更正了兩個錯誤。** 這句話先前寫的是「**29** 個 ungrouped free gene 每個只有
> **2–6** 個值」。兩個數字都錯。是 **27**,不是 29 —— 有三個單值的 `ForkParameters` 條目
> (`PrefetchLocalRead`、`GlobalSplitUAlgorithm`、`DtlPlusLdsBuf`)塌縮成常數,所以
> **宣告的 30 個獨立參數 → 27 個 free gene + 3 個 group = 30 個 key**(§3.7a)。而範圍是 **2–18**,
> 不是 2–6。證據:engine log 那一行
> `GA:INFO SearchSpace(num_vars=30, counts={'WorkGroupMapping': 18, …, 'group_0': 9918, 'group_1': 3,
> 'group_2': 2})`,以及 `guidance-*.json` 的 `n_genes_activated + n_genes_fallback` 在
> medium / large / tiny 上是 2+25 / 5+22 / 0+27。

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

**實際發生了什麼(已量測)。** 法則 2 在每一個 S14 large run 都會啟動,族群往 256 衰減。
**交叉的代數並不是每一個 run 都是 6** —— 這句話較早的版本這樣寫,那是錯的。逐 seed 第一個
`diversity < 0.5` 的代數:

| seed | 24001 | 24002 | 24003 | 24004 | 24005 |
|---|---:|---:|---:|---:|---:|
| 第一個 `diversity < 0.5` 的代數 | **6** | **7** | **8** | **7** | **7** |

**論證真正需要的那個主張是成立的,而且那才是應該講的:交叉代數在每一個 seed 內、兩臂之間都相同,所以它
不是一個臂層級的 confounder。** 逐 seed 的 6–8 差異是 seed 之間的性質,不是兩臂之間的。

⚠ 下面那張 diversity / eval 表**只有 seed 24001** —— 它不是五個 seed 的平均,不可以那樣讀:


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



### §3.2c `seed` 實際控制了什麼 —— 真正實作的 RNG,以及那個從未被建造的 counter-based 設計

> **⚠ 純文件層級的事實更正,2026-08-14。** S14 design §10.2、Lock A 的 `rng` 區塊與 P7 投影片表格所載的
> RNG 描述 ——「counter-based stream,以 `(lock_hash, shape, seed, phase ∈ {gen0, evolution,
> measurement})` 為 key;paired 的兩臂共用同一批 Gen0 uniform,再分別經 `p0` 或 `p1` 映射;evolution
> stream 在 Gen0 之後重置」—— 描述的是一個**只規劃、從未實作**的機制。**沒有任何量測值、pin、seed、
> gate、門檻或 claim 改變。** 改變的是「配對對比被控制得多緊」這件事的敘述。

> **三個經常被混淆的符號 —— 請分清楚。**
> `P0` = **Gen0 族群大小**(capped 512、native 約 11,405)。`p0` = 某個 gene 的**均勻**機率向量。
> `group_0` = 那個**分組後的 MatrixInstruction/WorkGroup gene**(9,918 個候選)。`group_0` 既不是 `P0`
> 也不是 `p0`:它是一個 gene,而且它是從一個**非均勻、GEKO 導出**的向量抽出來的(見下)。

#### 一個整數做了什麼

`[CODE AUDIT]` GA 只在建構子裡、用單一個 Python `int` 播種一次 —— 這就是 Ductile 的原生機制,而且僅止於此:

```python
random.seed(seed)          # engine ga.py:157   | repo ga.py:188
np.random.seed(seed)       # engine ga.py:158   | repo ga.py:189
self.space.seed(seed)      # engine ga.py:159   | repo ga.py:190
```

`SearchSpace.seed` 只有一行 —— `self.seed_seq = np.random.SeedSequence(seed)`(engine
`core/space.py:83-84`,repo `core/space.py:84-85`)。

從這一個整數長出兩個 generator 家族,分別被互不重疊的部分消耗:

| 家族 | 播種於 | 被誰消耗 |
|---|---|---|
| legacy global `random` / `np.random` | engine `ga.py:157-158` | 所有 evolution 運算子 —— selection(`core/selection.py:89, 116, 156, 174, 189, 193, 208, 221`)、crossover(`core/crossover.py:61, 91, 101, 114, 116, 126, 136`)、mutation(`core/mutation.py:52-53`)、洗牌(`core/population.py:235`) |
| `SeedSequence` 子序列 | engine `space.py:83-84` | **只有 Gen0** —— `SearchSpace.sample` 每個 chunk spawn 一個子序列(engine `space.py:137`),`sample_chunk` 再據以建立 `np.random.default_rng(seed)`(engine `space.py:51`) |

`space.sample` 只在初始族群時進入(engine `ga.py:294`,以及 `:299` 的半量 fallback);第 2 代之後永遠
不會再進去。所以 Gen0 與 evolution 運算子確實是從**不同的 generator 物件**抽的 —— 但那個分離是 Ductile
恰好這樣寫的附帶性質,**不是**設計裡那個 `phase` keying,而且從來沒有任何東西被重新 key 或重置。這些 run
也設了 `PYTEST_XDIST_WORKER=gw0`,強制 `JOBLIB_N_JOBS_OVERRIDE = 1` 與 `threading` backend(engine
`space.py:35-41`) —— 每輪抽樣一個子 `SeedSequence`,與 Lock A 的 `n_jobs=1` 吻合。

#### 舊描述的四項主張,對照程式碼

| 舊主張 | 狀態 | 證據 |
|---|---|---|
| 以 `(lock_hash, shape, seed, phase)` 為 key 的 counter-based stream | **不存在** | engine 裡任何地方都沒有這個 key;播種就是上面那三個平凡呼叫 |
| paired 兩臂共用同一批 Gen0 uniform | **只要 guidance 有啟動就是錯的** | 見下方的發散機制與 gen-1 表 |
| 「evolution stream 在 Gen0 之後重置」 | **不存在** | `grep -n "reset\|reseed" algorithm/ga.py core/space.py` → engine 與 repo 兩份**都沒有任何命中**。唯一的 RNG 狀態操作是 checkpoint 存回(engine `ga.py:217-218`、`:267-268`) |
| 一個 `measurement` RNG phase | **不存在** | 量測路徑上唯一的 `seed=` 是 `Tensile/backends/ductile_backend.py:695`,它只是把 seed 直接交給 GA 建構子。這裡的量測變異是**硬體**的,不是偽隨機的 —— 這正是為什麼固定 seed 無法讓 remeasure 可重現(§7.1a、§7.1b) |

#### 記錄本身早就承認這是延後項 —— 而這個延後從未關閉

Lock A(`agent_run/260809-s14-pershape-baseline/lock/lock_a_protocol.json`,key `rng`)用它自己的措辭寫著:

> `"Counter-based (lock_hash,shape,seed,phase) streams with shared Gen0 uniforms mapped by p0/p1 are a
> PAIRED G/F mechanism; not applicable to baseline-only. Baseline uses Ductile native seeded RNG
> (backend seed=formal seed), n_jobs=1 for deterministic seeded population. Paired RNG and
> counterbalanced arm order are sealed at Lock B before any guided run."`

`[CODE AUDIT]` **Lock B 裡完全沒有 `rng` 區塊。**
`agent_run/260809-s14-pershape-guidance/lock/lock_b_guided_guidance.json` 的頂層 key 是 `lock`、
`amendments`、`sealed_by`、`sealed_at_utc`、`purpose`、`capped_bundle_files`、`capped_bundle_sha256`、
`activation_summary`、`sealer_ratifications`、`independent_verification`、`consumption_rule`、
`governance` —— 沒有 RNG,paired 或其他形式的都沒有。這個機制被延後到一個從未封存它的 lock,而 guided
run 就在原生 seeded RNG 上跑掉了。

#### 兩臂的 Gen0 stream 為何發散

抽樣由一行完成 —— engine `core/space.py:56`(repo `:57`):

```python
ind = Individual({k: rng.choice(s, p=p.get(k, None)) for k, s in sizes.items()})
```

`numpy` 的 `Generator.choice` 在**有 `p` 與沒有 `p` 時走不同的程式碼路徑**(有界整數生成 vs. 對均勻 double
做累積和反演),消耗亂數的方式不同。所以兩臂一旦對「哪些 gene 帶 `p` 條目」有分歧,它們的子 stream 位置就
不同,之後每一次抽取 —— 該個體內的、以及其後每一個個體的 —— 都不一樣。

而兩臂的分歧,正好就是 treatment 所規定的那樣。`[CODE AUDIT]` 取自凍結的 run config
(`agent_run/260809-s14-pershape-baseline/config/s14-pershape-{,guided-}{shape}-seed_24001.yaml`,
`Backend.Config.weights`):

| shape | 帶 `weights` 條目的 gene —— Arm G | Arm F |
|---|---|---|
| tiny | `group_0` | `group_0` —— **同一份清單,逐位元相同** |
| medium | `group_0` | `group_0`、`DepthU`、`1LDSBuffer` |
| large | `group_0` | `group_0`、`PrefetchGlobalRead`、`TransposeLDS`、`UnrollLoopSwapGlobalReadOrder`、`GlobalReadVectorWidthA`、`GlobalReadVectorWidthB` |

`DepthU` 是凍結 `ForkParameters` 清單的**第一個**條目(config 第 43 行),所以在 medium 上,發散從第一個
個體的第一次抽取就開始。

#### 實證檢查 —— generation-1 的 valid count

若兩臂共用 Gen0 族群,則每一對在 `gen == 1` 的 `generation_any_valid_count` 都應相同。由
`agent_run/260809-s14-pershape-baseline/stage3_{baseline,guided}/seed_*/{shape}/trajectory.jsonl`
重新推導(`best_hash_so_far` 只顯示前 8 個十六進位字元):

| shape | seed | Gen0 `best_hash` G | Gen0 `best_hash` F | 相同? | valid G | valid F |
|---|---:|---|---|---|---:|---:|
| tiny | 24001 | `167dca0a` | `167dca0a` | 是 | 313 | 313 |
| tiny | 24002 | `8668ec55` | `8668ec55` | 是 | 321 | 321 |
| tiny | 24003 | `9dda5173` | `96d3849a` | **否** | 289 | 289 |
| tiny | 24004 | `90cb5edb` | `90cb5edb` | 是 | 273 | 273 |
| tiny | 24005 | `ab40aa13` | `ab40aa13` | 是 | 308 | 308 |
| medium | 24001 | `1c22d708` | `40f35782` | **否** | 508 | 502 |
| medium | 24002 | `93930ff0` | `8df6d84f` | **否** | 505 | 509 |
| medium | 24003 | `b61dbe6a` | `a9ab25c1` | **否** | 507 | 507 |
| medium | 24004 | `d699802c` | `73c0ff30` | **否** | 508 | 509 |
| medium | 24005 | `39b83c43` | `acf685b1` | **否** | 507 | 507 |
| large | 24001 | `3d591e0e` | `23f0747c` | **否** | 489 | 483 |
| large | 24002 | `599e8118` | `ffc896a6` | **否** | 480 | 488 |
| large | 24003 | `184ca50d` | `0fabdc1c` | **否** | 485 | 487 |
| large | 24004 | `1443f705` | `9abfd4b7` | **否** | 485 | 480 |
| large | 24005 | `d231c9ba` | `da7d4cd9` | **否** | 486 | 491 |

要兩個方向都讀對:

- **count 不等就證明了發散。** medium/large 的 10 對裡有 8 對 valid count 不同,而且 10 對的 `best_hash`
  全都不同。共用族群不可能產生這種結果。
- **count 相等本身什麼也證明不了。** medium 24003 與 24005 都是 507/507,但 champion 不同 —— 是 count
  碰巧撞在一起,族群並沒有共用。不要拿這兩列 `507/507` 當成共用的證據。
- **tiny 相符有一個具體且可查核的理由,不是因為存在什麼共用機制。** tiny 的 27 個 free gene **啟動了
  0 個**,所以 Arm F 的 weights 清單不只是等價於 Arm G,而是*字面上同一份清單*:
  `stage3_guided/seed_*/tiny/ga_init_evidence.json` 記錄的 canonical **整份 list** sha256 是
  `56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f`,與 baseline 組態的相同。
  (在這裡「整份 list」才是正確的對象,正是因為**這份 list 剛好只有一筆記錄** —— 只有 `group_0`;
  至於在 medium 與 large 上為何逐 **entry** 的 hash `3c5a30f7…472` 才是正確的對象,見 §3.2c,那邊
  guided 的 list 更長。)相同的 `p` 映射 ⇒ 相同的呼叫 ⇒ 相同的族群。
- **tiny 24003 是印證 §3.8.2 機制的例外,不是反例。** 它的 valid count 相符(289/289) —— 同一個族群 ——
  但 `best_hash` 不同,因為 champion 是對*量測值*取 argmax。這正是 §3.8.2 分析過的「噪音下的搜尋發散」
  效應,請直接引用該節,不要在這裡重推。

#### `p0` / `p1` 實際做的事 —— 這就是 treatment 本身

還是同一行,engine `core/space.py:56`,其中 `s` 是該 gene 的候選清單,`p` 是它的機率向量:

- **Arm G** —— 被啟動的 gene 在 `weights` 裡沒有條目,所以 `p.get(k, None)` 回傳 `None`,該 gene 以
  **均勻**方式抽取。
- **Arm F** —— 被啟動的 gene 帶著 Formocast 導出、經 entropy cap 的向量 `p1`。在 medium 上,`DepthU`
  (候選 `[32, 64, 128, 256, 512, 1024]`)經 Ductile 自己的 weight→probability 轉換後解析為
  `[0.2096, 0.5011, 0.0723, 0.0723, 0.0723, 0.0723]`,於是 **`DepthU=64` 被抽中的機率約為一半,而不是
  六分之一**。已對照
  `agent_run/260809-s14-pershape-guidance/out-capped/ga-weights-medium.json` 驗證(原始 weights
  `[6.251, 2.764, 10.506, 10.506, 10.506, 10.506]`,`weight_beta = 0.25`),也對照該 shape 記錄於
  `guidance-medium.json` 的 `p1`;完整端到端重播見 §3.4b.3。

效果:Arm F 的 Gen0 集中在 Formocast 預測較好的組態上,Arm G 則均勻散開。**這就是 treatment 的全部** ——
兩臂之間沒有其他差異(§3.4b.4)。

#### group_0 —— 兩臂同一張表,而那張表並不均勻

`group_0` **不帶**任何 treatment,但它也**不是**從 `p0` 抽的。它在**兩臂**都被明確給了一個 **GEKO 導出**
的權重向量:

- **baseline 臂也有。** `[CODE AUDIT]`
  `stage5_native_baseline/seed_*/{medium,large}/ga_init_evidence.json` 為 **baseline** 臂記錄了
  `weights_gene_keys: ["group_0"]` 與 `sampling_prob_genes: ["group_0"]`。一個沒有權重的 gene 會直接
  缺席,並走 `None` / 均勻路徑。
- **可證明為非均勻。** 對 9,918 個出貨權重重播 Ductile 的轉換得到 `Σp² = 1.753982e-04`,而均勻應為
  `1/9,918 = 1.008268e-04` —— **有效基數約 5,701**。原始權重跨越 `1.4618 … 395.6448`;前 1,000 個條目
  佔 **26.8 %** 的機率質量,另有 2 個條目在 `float32` 下下溢為機率恰好 0。
- **兩臂之間相同 —— 這才是承重的事實。** 承重的識別字是 `group_0` 值清單的**逐 entry** canonical
  sha256:**`3c5a30f77ac6531b37ac0cb5573d717e9b82cd83e5414c9be22787ec6630b472`**,在 Arm G 與 Arm F、
  三個 shape 上都相同。它定義於 `scripts/make_guided_config.py:28 GROUP0_SHA`,在 `:117` 被 assert,
  並逐 config 記錄在 `env/config_verification.json` 的 `group_0_canonical_sha256`。正規化方式:
  `hashlib.sha256(json.dumps(rg0, separators=(",",":"), allow_nan=False).encode())`,其中 `rg0` 是那個
  浮點數清單。
  - ⚠ **`56c34446…f34f` 是另一個量** —— 它是**整份 `weights` list** 的 hash —— 只有在該 list 剛好只有
    一筆記錄時,才會等於 group_0 entry 的值。整份 list 的 hash 分別是:baseline 任一 shape / guided
    tiny `56c34446…`(len 1);guided medium `d64ebd34…`(len 3);guided large `753d629c…`(len 6)。
    因為 `weights_sha256` 雜湊的是**整份**清單,所以在 medium 與 large 上 G 與 F 必然不同 —— 真正定案的
    是逐 **entry** 的比較。
  - ⚠ **歸屬已於 2026-08-14 更正。** 本條先前把 `56c34446…` 說成逐 entry 的 hash,兩句之後又同時說它是
    整份清單的 `weights_sha256` —— 除了長度為 1 的情況以外,它不可能兩者都是。**結論不變、而且為真:
    `group_0` 這個 entry 在四個臂上完全相同。** 錯的只是識別字。

所以 §3.2(b) 的論證站在*同一張表、不帶 treatment*上面;即使 group_0 是均勻的、或 GEKO 加權的、或別的什麼,
這個論證都仍然成立 —— 它唯一不能站的地方就是「共用 uniform」。

#### 舊描述掩蓋掉的後果

因為 stream 發散,只要 guidance 有啟動,兩臂探索的就是**真正不同的 Gen0 族群**。因此這個對比是**以 seed
配對** —— 同一個 seed、同一顆 GPU UUID、同一組 pin、除了 `weights` 清單以外樣樣相同 —— 而**不是**以共用
亂數配對。它仍然是一個有效的配對設計,gate 的任何算術都不依賴這個差別;它只是**沒有**「同一副骰子、不同
的查表」所暗示的那麼緊密受控,而且每個 seed 的差值比那句話所暗示的多吸收了一項變異來源。

*來源:*`[CODE AUDIT]` *engine* `algorithm/ga.py:157-159, 217-218, 267-268, 294, 299`*、*
`core/space.py:35-41, 51, 56, 83-84, 137`*、*`core/selection.py`*、*`core/crossover.py`*、*
`core/mutation.py:52-53`*、*`core/population.py:235`*、*`Tensile/backends/ductile_backend.py:695`
*(repo 對應:*`ga.py:188-190`*、*`space.py:57, 84-85`*);*
`agent_run/260809-s14-pershape-baseline/lock/lock_a_protocol.json`*(*`rng`*);*
`agent_run/260809-s14-pershape-guidance/lock/lock_b_guided_guidance.json`*(頂層 key);*
`agent_run/260809-s14-pershape-baseline/config/s14-pershape-*-seed_24001.yaml`*;*
`stage3_{baseline,guided}/seed_*/{shape}/trajectory.jsonl`*;*
`stage3_guided/seed_*/{tiny,large}/ga_init_evidence.json`*;*
`stage5_native_{baseline,guided}/seed_*/{medium,large}/ga_init_evidence.json`*;*
`out-capped/ga-weights-medium.json`*、*`out-capped/guidance-medium.json`*。交互參照:§3.2、§3.2a、*
*§3.4b.3、§3.4b.4、§3.7、§3.8.2、§7.1a、§7.1b。*

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
- **entropy 恰好落在下限上,而且兩個計算完全吻合。** 重算得到 `H(p1)/ln 6 = 0.8001253`,對照 manifest
  記錄的 `normalized_entropy_p1 = 0.8001254` —— **吻合到小數第 6 位**。封頂確實做到它宣稱的事,而且在
  GA 真正消費的那個 artifact 裡就看得見。(⚠ 此處先前讀起來像是不吻合 ——「0.8000 對照 manifest 的
  0.800125」—— 那只是因為重算值寫到小數第 4 位、manifest 寫到第 6 位所致。並不存在任何落差。
  2026-08-14 更正。)
- **未啟用的 gene 解出來是均勻的。** `WaveSeparateGlobalReadA` 恰為 `[0.5, 0.5]`,與 Arm G 相同。
  這證實 treatment 確實只作用在啟用的 gene 上;其餘每個 free gene 在兩臂中的抽樣方式完全一樣。
  - ⚠ **這句話描述的是 artifact,不是實際執行的東西。** Run config 只出貨 `group_0` **加上已啟用
    gene** 的 `weights` —— 在 seed-24001 的 config 上已驗證:baseline medium `['group_0']`;
    guided medium `['group_0', 'DepthU', '1LDSBuffer']`;guided large
    `['group_0', 'PrefetchGlobalRead', 'TransposeLDS', 'UnrollLoopSwapGlobalReadOrder',
    'GlobalReadVectorWidthA', 'GlobalReadVectorWidthB']`;guided tiny `['group_0']`。
    `ga-weights-medium.json` 裡那 25 個 fallback-`p0` 向量(large 是 22 個)**從未被打包進執行**。
    那些 gene 走的是 `core/space.py:56` 的 `p.get(k, None)` → `p = None` 分支。
  - **分布**沒有變 —— 檔案裡的 `p0` 就是均勻的(`StaggerU` `[4.3944]×3`、
    `NonTemporalA` `[2.7726]×2`、`WorkGroupMapping` `[11.5615]×18`),而 `p = None` 同樣是均勻的。
    **程式碼路徑**則不同:`p = None` 與明確給定的均勻 `p` 從 generator 取用的抽樣次數不同,
    這正是 §3.2c 的 Gen0 分岔機制。在這裡無害,因為那些 gene 在**兩臂**都走 `p = None`。
  - 這件事讓 §3.2c 更銳利而非更弱:既然 fallback 向量兩臂都沒出貨、`group_0` 的表兩臂出貨完全相同,
    **Gen0 分岔唯一可能的來源就是已啟用的 gene**。這正是 tiny —— 零個已啟用 gene、兩臂 `weights`
    逐位元相同 —— 在 5 個 seed 中有 4 個相同的原因(§3.8.2)。

反解步驟 (5) 還能還原出 guided 偏好本身:`DepthU` 在 `{32, 64}` 上的 `q ≈ [0.243, 0.757]` ——
模型偏好 `DepthU=64` 約 3:1;經過 `ρ = 0.566` 封頂後變成 0.5011 對 0.2096 的抽取機率,
而仍有 28.9% 的質量被多樣性下限保留在那四個無證據值上。

#### §3.4b.4 這對解讀實驗的意義

- Arm G 與 Arm F 之間**唯一**的差異就是 backend config 裡的 `weights` 清單。其餘一切 —— seed、pin、
  `group_0`、評估方式、早停 —— 完全相同。
- 由於未啟用的 gene 解出來是均勻分布,medium 上的 treatment 是一個作用在 **27 個 free gene 中 2 個**
  上的 prior,large 上是 **27 個中 5 個**。這就是介入的具體規模,任何 null 結果旁邊都值得直白寫出
  (§7.1/§7.2):null 是「**在這種規模的 prior 之下**」的 null。
  (**2026-08-14 更正** —— 本行先前寫的是「29 個中 2 個」/「29 個中 5 個」。**27** 才是權威的 free-gene
  分母;見 §3.5 與 §3.7a。)
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

> **⚠ 稽核註記,2026-08-13 提出、2026-08-14 解決。** 一個問題成立,一個撤回。**(i) 成立:** 上面散文
> 引用的那道 guard(`M < 128 && MT0 − M >= 16`)在 M = N = 256 時是**空轉的**,所以它產生不了 medium 的
> 171/434 —— 那一列來自*下一道* guard(`M >= 128 && MT0 − M >= 32`),它就在同一個 block 裡;散文應該
> 引用實際適用於各列的那一道 guard。**(ii) 撤回 —— 那些計數重現得出來。** 2026-08-13 的稽核以
> `MacroTile` 不是 `s10-generated.yaml` 的欄位為由,把 434 / 171 / 1 標成 **`NOT_EVALUATED` as cited**。
> **三個都能確定性地重現**:由該 YAML 的標註得到 **434 種相異 MacroTile**,再經
> `formocast_simulator.cpp:578`(tiny)與 `:584`(medium)的 guard 過濾 → **tiny 1**、**medium 171**。
> §3.2a 早就把 434 當事實陳述。**這個 hedge 予以移除。** 已在該 YAML 中驗證、且不受影響的是:9,918 條、
> **840** 個相異 `MatrixInstruction` tuple、**262** 個 `WorkGroup:` 覆寫。質性結論 —— tiny 的哨兵值
> 飽和 ⇒ 全部 27 個 gene 的 `S_g = 0.0000` —— 一直都由 activation log 獨立佐證,**不**依賴這三個計數。


| shape           | 池中能通過 guard 的 MacroTile        | 比例        |
| --------------- | ------------------------------ | --------- |
| **tiny(8×8)**   | **434 個中的 1 個**(`:578`) | **0.2 %** |
| medium(256×256) | 434 個中的 171 個(`:584`) | 39.4 %    |


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

group_0(在 `MatrixInstruction` / `GlobalSplitU` / `MIArchVgpr` / `WorkGroup` 上列舉的 9,918 個聯合候選)
為 GEKO 加權、**兩臂都有、treatment 從不碰它**。Formocast treatment 只重加權 ungrouped free gene。

⚠ **正確的檢查是逐 entry,不是逐檔案。** `ga_init_evidence.json` 裡的 `weights_sha256` 雜湊的是
**整份** `weights` 清單(`run_pershape_seed.py:324`),所以在 medium 與 large 上兩臂的雜湊**必然**不同
—— guided 清單還多帶了已啟用的 gene。真正承重的比較是**單獨**取 `group_0` entry:三個 shape 上
Arm G 與 Arm F 的 canonical sha256 都是
**`3c5a30f77ac6531b37ac0cb5573d717e9b82cd83e5414c9be22787ec6630b472`**
(`make_guided_config.py:28 GROUP0_SHA`,在 `:117` 被 assert,並記錄於 `env/config_verification.json`
的 `group_0_canonical_sha256`)。⚠ **2026-08-14 更正** —— 此處原本寫的是 `56c344…`,那是**整份 list**
的 hash,除了 list 剛好只有一筆記錄的情況以外,它*不是* entry hash。本節先前的版本宣稱兩臂的權重檔
逐位元相同;那只在 tiny 與各 baseline 上成立(§3.2c)。

*來源:S14 §6.1 note;`[CODE AUDIT]` `run_pershape_seed.py:324`;§3.2c、§3.4b.3、§3.4b.4。*

#### §3.7a 三個 group —— 內容、參數目的,以及為何它們都不是被 treat 的 gene

`[CODE AUDIT]` 搜尋空間共有 **30 個 key:27 個 free gene + 3 個 group**。group 宣告在 config 的
`ForkParameters → Groups` 區塊,並在 `backends/ductile_backend.py:257-262`
(`fork_params[f"group_{i}"] = group`)被轉成單一搜尋 key;長度為 1 的 group 則塌縮成常數。
另外有三個 `ForkParameters` 條目只有單一值(`PrefetchLocalRead`、`GlobalSplitUAlgorithm`、
`DtlPlusLdsBuf`)而落為常數 —— 這就是 30 個宣告的獨立參數為何只產出 27 個 free gene。

| key | 成員(括號為該 group 中有多少 entry 指名它) | 列舉的 entry 數 |
|---|---|---|
| `group_0` | `MatrixInstruction` 9,918 · `GlobalSplitU` 9,148 · `MIArchVgpr` 5,448 · `WorkGroup` 262 | **9,918** |
| `group_1` | `DirectToLds` 3 · `UseSgprForGRO` 3 | **3** |
| `group_2` | `ClusterLocalRead` 2 · `LDSTrInst` 2 | **2** |

沒有指名某個成員的 entry,該成員就維持它的常數預設值;只有 `MatrixInstruction` 出現在每一個
`group_0` entry 裡。注意 `MIArchVgpr` **同時**是獨立 free gene 與 `group_0` 成員 —— 若有 guidance
權重,那個權重只作用在獨立 key 上。

**`group_1` —— 暫存器路徑的資源爭奪。** 兩個成員都是拿 VGPR 壓力去換另一種資源,因此在搶同一份預算:

- `DirectToLds` —— 把 global load 直送 LDS,**繞過 VGPR**。有效值 `[0, 1, 2, 3]`
  (`1` = A 與 B、`2` = 只 A、`3` = 只 B);*"For an 8x8 TT with PrefetchGlobalRead=1 this can save 33
  VGPRs"*,而 `DirectToLds=1` 需要 `GlobalReadVectorWidth = 1/2/4`,且 `TLU=0` 情況下需要
  `TransposeLDS = 1`。
- `UseSgprForGRO` —— 把 global-read offset 從 VGPR 搬到 SGPR。*"Converting VGPR GRO into SGPR GRO is
  usually a win / However, the mode may exhaust all available SGPR, in particular for large unroll"*;
  `-1` 退回啟發式判斷。

**`group_2` —— LDS 讀取的排程。**

- `ClusterLocalRead` —— *"If set ClusterLocalRead, each iteration dedicated vgprBuffer for localRead / So
  we can schedule these localReads to the front of the loop"*。
- `LDSTrInst` —— *"Enable LDS Transpose Instruction"*,有效值 `[False, True]`。

**它們為何要被分組:成員之間有互斥的有效性約束。** 每個 group 列舉的組合都**少於成員的笛卡兒積**。

- `group_1` 只列 3 個 entry —— `(0,0)`、`(0,1)`、`(1,0)`。`(DirectToLds=1, UseSgprForGRO=1)` **不存在**,
  而且 `DirectToLds` 被限制在 4 個有效值中的 `{0, 1}`。
- `group_2` 只列 2 個 entry —— `(ClusterLocalRead=0, LDSTrInst=true)` 與 `(1, false)`。兩個設定
  **互斥**;4 種組合中有 2 種不合法。

group key 存在的目的,是讓 GA 從**列舉出來的合法集合**抽樣,而不是各成員獨立抽樣後把大部分乘積判掉。
`group_0` 是同一個手法的放大版:9,918 個列舉 entry,而不是四個成員的乘積(§3.2a)。

**它們確實有參與演化 —— 只是沒有被 treat。** 每個 group 都是 `self.space` 裡一個普通的 key,
和其他 gene 一樣會被抽樣、交配、突變。記錄下來的 champion 佐證了這點:整個 campaign 中 `group_1`
的 3 個值全都出現過,`group_2` 的 2 個值也都出現過。它們從未拿到的是 **guidance 權重** —— 出貨的
`weights` 清單在 tiny 與所有 baseline 上是 `['group_0']`,在 guided medium/large 上是
`['group_0'] + 已啟用 gene`。**`group_1` 與 `group_2` 在兩臂的清單裡都不存在。**

不要把它們描述成「凍結」。*沒有被啟用為 guidance* 與 *沒有變動* 是兩個不同的主張,只有前者成立。

原因是結構性的,而不是某個決定:S11 的 per-gene 敏感度分析是在那 **27 個 free gene** 上跑的。
複合 key 沒有單一的候選軸可供 Formocast 評出 per-value benefit,所以 `group_1` 與 `group_2` 從一開始
就沒有被啟用的資格。`group_0` 之所以帶權重,只是因為 Ductile 自己就出貨了一份 —— GEKO 的
analytical model 表,兩臂相同(§3.7)。

*來源:`[CODE AUDIT]` `config/s14-pershape-{,guided-}{tiny,medium,large}-seed_24001.yaml`
的 `BenchmarkProblems[0][1].ForkParameters[30].Groups`(n_groups = 3;成員頻次與 entry 數如上表)
與 `Backend.Config.weights`(出貨的 key 清單);
`backends/ductile_backend.py:257-262`;`BenchmarkStructs.py:88-110`(`_expandGroupedParameters`);
`Common/ValidParameters.py:299-301, 418-427, 474-477, 991-992`(引用的註解);
`core/space.py:56`。互相參照:§3.2a、§3.2c、§3.4b.3、§3.4b.4、§3.7。*

### §3.8 Per-shape η_s(noise margin)

> **⚠ `ETA-MARGIN-REMOVED-20260814` —— `η_s` 已不再是 gate 門檻(經 owner 授權,2026-08-14)。**
> 底下 §3.8 與 §3.8.1 的全部內容都**作為歷史保留**:它們記錄這條 margin 曾經是什麼、怎麼導出來的、
> 以及為何後來不被信任。它們**不再描述一個仍然生效的 gate 分項**。第四個分項 `final ratio ≥ e^{−η_s}`
> 已被移除其 gate 組成的地位,而且**沒有登錄任何替代門檻**;final ratio 只以方向與 effect size 報告。
> 請把 §3.8/§3.8.1 讀成一個**已被移除**機制的 provenance,並到 **§7.0.2** 看這項 amendment、它的依據,
> 以及(未改變的)gate 結果。

非退步門檻使用**per-shape** noise margin `η_s = P95(|log y − median log y|)`,由 pilot 殘差逐 shape 導
(medium η=0.0042、large η=0.1229、tiny η=0.4466),**不**用被 tiny 汙染的 aggregate `delta_noise` ——
因 η 是各 shape 量測重複性的性質。

最終非退步門檻 = `e^{−η_s}`。

*來源:S14 §10.2、baseline run-root 的 per-shape η。*

#### §3.8.1 margin 是什麼,以及為何 medium 的 margin 比 large 緊約 28×

> **⚠ `ETA-MARGIN-REMOVED-20260814`。** 本小節自 2026-08-14 起**屬於歷史**。它的收尾立場 ——
> 「pin 基於治理理由保留,而那個落差以揭露而非填補的方式處理」—— **已被取代**:owner 已授權直接移除
> 這條 margin,所以那個落差現在是靠**刪掉 gate**、而不是靠在兩條 margin 之間選一條來收斂。本小節提出
> 的兩項論證**沒有被撤回**,而且在 §7.0.2 裡是承重的:(a) 由重測自身重算的 margin 是循環的,並被 tiny 的
> null control 證偽;(b) **η 是錯的尺度**。這兩項合起來,正是 §7.0.2 **不登錄任何替代門檻**的理由。底下的
> `η_s` 數值、容忍帶表格與 tiny 比值表格,全部維持原量測結果不變。

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
   此決定的狀態:`PENDING_HUMAN_DECISION`,§5。

**η 是錯的尺度 —— 而且這一點同時限制了*兩個*候選。** η 量的是**單一個固定 config** 的窗內重複性,而
estimand 是**兩個不同 champion** 的比值。臂間離散度在 tiny 上是窗內值的 4.9×、在 large 上是 2.0×。
無論 pinned 還是實測 margin,量到的都不是這個 gate 真正需要的量;pin 是基於治理理由被保留,而那個落差
是被揭露,不是被補上。

*來源:`[CODE AUDIT]` `noise/per_shape_noise.json → shapes.{shape}.eta_s`;
`scripts/compute_per_shape_noise.py:30`;tiny 的比值取自
`stage3_baseline/seed_*/tiny/champion_interleaved.json → F_over_G_median_ratio`;容忍度以
`e^{−η}` 計算。S14 design §10.2、§13.4。*

#### §3.8.2 tiny 到底控制住了什麼 —— 它的包絡裡有搜尋發散,不只是量測誤差

**這一節為什麼存在。** §3.8.1(以及 outline 的 P13)把 tiny 當成**意外得來的 null control**。這個框架是
對的 —— tiny 上的 treatment 確實是零 —— 但**照目前的寫法它是不完整的**,而這個缺口會改變「tiny 的
0.1247 包絡到底是什麼東西的包絡」。把 0.1247 讀成「固定 config 上的量測誤差」的讀者,會從它導出錯誤的
結論。更正寫在這裡。

**第 1 步 —— treatment 是零。三項彼此獨立的檢查,沒有一項是推論。**

| 檢查 | artifact | 結果 |
|---|---|---|
| 兩臂的 config 逐位元相同,全部 5 個 seed | `config/s14-pershape-tiny-seed_{24001…24005}.yaml` 對 `config/s14-pershape-guided-tiny-seed_*.yaml` | sha256 相同 **5/5** |
| 沒有任何 gene 被 activate | `[CODE AUDIT]` `260809-s14-pershape-guidance/out-capped/guidance-tiny.json` → `activated`、`n_genes_activated`、`n_genes_fallback` | `false`、**0**、**27** |
| guided 臂唯一會照權重表抽樣的 gene,正是那個沒被動過的 group | `[CODE AUDIT]` `stage3_guided/seed_*/tiny/ga_init_evidence.json → sampling_prob_genes` | 只有 `["group_0"]` —— GEKO 加權、兩臂相同、treatment 從不碰它(§3.7) |

所以 tiny 的 F-vs-G 對比是一個**被構造出來的零**:同樣的程式碼、同樣的 seed、同樣的抽樣分布。

**第 2 步 —— Gen0 在*族群*層級就是相同的,不只是在 config 檔層級相同。**
`[CODE AUDIT]` `stage3_{baseline,guided}/seed_*/tiny/trajectory.jsonl` 的 `gen: 1` 那一列:

| seed | `generation_candidate_count` | `generation_any_valid_count` G / F | `best_hash_so_far` G / F | `best_gflops_so_far` G / F |
|---|---:|---:|---|---:|
| 24001 | 512 | 313 / 313 | `167dca0a…` / `167dca0a…` —— 相同 | 2.89087 / 2.88921 |
| 24002 | 512 | 321 / 321 | `8668ec55…` / `8668ec55…` —— 相同 | 2.80885 / 2.80201 |
| 24003 | 512 | 289 / 289 | `9dda5173…` / `96d3849a…` —— **不同** | 2.92836 / 3.08467 |
| 24004 | 512 | 273 / 273 | `90cb5edb…` / `90cb5edb…` —— 相同 | 3.04423 / 3.04557 |
| 24005 | 512 | 308 / 308 | `ab40aa13…` / `ab40aa13…` —— 相同 | 2.89055 / 2.90379 |

評估數在**五個 seed 上完全一致** —— 連無效尾巴的形狀都一致(送出 512 個候選,完成 273–321 個),而那是
被抽樣族群的逐候選性質。加上逐位元相同的 config,這就是為什麼這個零在族群層級成立:兩臂抽到的是
**同一個 Gen0**。

**第 3 步 —— 然而這個相同族群被量出來的值,在兩臂之間不一樣,5/5 個 seed 都不一樣。** 再看一次最後一
欄。族群沒有任何東西改變,改變的只有貼在它身上的那個數字。

**seed 24003 用一列就把機制攤開來看。** 那一列裡兩臂連 Gen0 的最佳*個體是哪一個*都不同
(`9dda5173…` 對 `96d3849a…`)。同一個族群、不同的 argmax —— 因為 argmax 取的是**被量測的**值,不是真
值。(給要重新推導這件事的人一個提醒:`best_hash_so_far` 相同只在 **5 個 seed 中的 4 個**成立,不是
5/5;先前非正式陳述這件事時只引用了 seed 24001。)

**第 4 步 —— 最終 champion 在 5/5 個 seed 上都不同。** `[CODE AUDIT]`
`stage3_baseline/seed_*/tiny/champion_interleaved.json → arms.{G,F}.canonical_hash`:五個 seed
**零命中**(`d3af03c7…`/`5b73b1d7…`、`271db9f3…`/`06aa1bfa…`、`ae57d5ca…`/`ea256157…`、
`fa95690a…`/`7449fe0a…`、`42be60d1…`/`fb251b2b…`)。

**把因果鏈直說。** 這四步合成一條機制,而它就是本節的全部重點:

> 相同的 Gen0 族群 → 被**量測**成不同的值(量測雜訊)→ GA 依**被量測的** fitness 做選擇 →
> 選中不同的個體 → 兩條搜尋軌跡發散 → **不同的最終 champion** → 非零的最終 `F/G`。

**因此 tiny 觀測到的包絡並不是「固定 config 上的量測誤差」。** max |ln F/G| = **0.1247**
(表面上約 **13.3 %** 的差異)是*量測雜訊* **加上** *雜訊驅動的搜尋發散*。這兩個成分無法用這裡保留的任何
artifact 拆開,而第二個成分才是概念上比較令人意外的那個:一個**什麼都沒改**的 treatment,仍然會產出兩個
不同的 tuned kernel,因為 GA 是它自己 fitness 讀數裡那些雜訊的混沌放大器。

**為何這讓 tiny 成為*更好*的 null,而不是更差的。** medium 與 large 的真實端點是由完全相同的雙成分過程
產生的 —— 它們的 champion 同樣是依被量測的 fitness 選出來的,也同樣要重測。所以 tiny 的包絡
**與真正 estimand 的結構相符**,而不是量了一個比它更窄的東西。一個純粹的固定 config 重複性數字
(`η_s` 就是這個 —— 見 §3.8.1 結尾那段)並**不**符合那個結構。tiny 是這道 gate 所看的那個量的正確
null 分布。

**那個不舒服的推論,不得被淡化。** 如果一個零 treatment 光靠搜尋發散就能產生約 13 % 的包絡,那麼在
medium 與 large 上,觀測到的 F-vs-G 差異**同樣含有一個雜訊驅動的搜尋發散成分**,並且與任何真實的
guidance 效應混淆在一起。這份研究沒有任何東西能把兩者分開。tiny 的貢獻是它給那個成分定出了一個
**尺度**:在這個 shape、這個 GA、這個預算下是 **~13 %**。任何這個量級的 F-vs-G 差異,單憑它自己並不是
guidance 的證據。這是設計上的限制,不是一項結果,它同時屬於 Discussion(§8)與這裡。

**禁止事項不變 —— 本節不為其中任何一項鬆綁。**

- **絕對不要寫「tiny 退步了」或「guidance 害了 tiny」。** treatment 是零;根本沒有可以退步的對象。tiny
  的逐 seed `F/G` 是從一個零效應包絡裡抽出來的樣本。
- **tiny 不在 gate 裡。** 逐 shape 的方向一致性 gate 涵蓋 medium ∧ large;tiny 只是**描述性的**
  (§5、S14 §10.4)。
- **`NOT_EVALUATED ≠ no effect`。** tiny 的 guidance 問題是*未評估 / 未啟用*(0/27 gene),
  **不是**「guidance 在這個 shape 上沒用」(§7.6 claim ladder;design §13.5)。
- §3.8.1 對 tiny 的兩個既有用法維持不變:它證偽了「重算 η」那條修補路線,並提供一個
  **參考包絡,永遠不是門檻**。

*來源:`[CODE AUDIT]` `config/` 底下成對的 config sha256;
`260809-s14-pershape-guidance/out-capped/guidance-tiny.json`;
`stage3_{baseline,guided}/seed_*/tiny/trajectory.jsonl`(`gen: 1` 那一列);
`stage3_guided/seed_*/tiny/ga_init_evidence.json`;
`stage3_baseline/seed_*/tiny/champion_interleaved.json → arms.{G,F}.canonical_hash`、
`→ F_over_G_median_ratio`。包絡統計量與比值表:§3.8.1。gate 範圍:§5、S14 §10.4。*

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

> **⚠ `ETA-MARGIN-REMOVED-20260814` —— 第四個分項已不再屬於 gate。** 上面的定義是**照預註冊原文**引用,
> 逐字保留,好讓原始措辭存續。自 2026-08-14 起,實際生效的 gate 只有**前三個**連言項 —— {Gen0、gen-10、
> AUC} 各需 ≥4/5 對 seed 為正,而這三項是**不帶任何 margin** 的純方向性比較(§5d.1、§5d.3)。
> `final ratio ≥ e^{−η_s}` **已被移除其 gate 組成的地位**;final ratio 仍然照常報告,以方向與 effect
> size 呈現,但**不對照任何門檻**。`≥4/5`、medium ∧ large 的 intersection-union,以及 tiny 僅描述性的
> 地位,全部**不變**。**判定不變:兩個 confirmatory shape 都是 NOT MET**(medium 3/5、3/5、3/5;
> large 1/5、2/5、3/5)。Amendment 紀錄:**§2 ledger**;判定與逐 seed 比值見 **§7.0.1**。
> `δ_s` improvement 準則(`F > G·(1+δ_s)`)**不在此次 amendment 範圍內,維持不變**。
>
> **⚠ 上面那段話有兩件事不可以被讀成那個意思(2026-08-18)。**
> **(a) 預註冊的 design 檔案本身從來沒有被修訂過** ——
> `s14-stage1-full-ga-outcome-design.md:226` 至今仍寫成四個連言項,而那個 token 在該檔的命中數是 0;
> 本索引的 §2 ledger 註明「由 owner 另行修訂」。要把三連言項的 gate 引述為**實際生效的**版本,
> 並且說明預註冊本身未經修訂。
> **(b) `final ratio` 是被移除其 gate 組成的地位,不是被移除其「必須報告的量」的地位。**
> 自 2026-08-18 起,它的判定方法是 `NULL-AS-NOISE-BASELINE-20260818`:把 arm F / arm G
> 對照 **arm G / arm G′ 的 null ratio** 作為雜訊基準,把每一個可得的尺度並列報告,
> 不得把任何東西收斂成單一判定,而且**不登錄任何倍數門檻**。讀法見 **§7.0.2** 與 **§7.1c – §7.2b**。
> **不對照任何門檻。一個被報告的方向與 effect size 不是通過,而且絕不可以被寫成通過。**

上面那條 gate 定義之前的段落,說明了為何一定要做 7× interleaved 重測。那段理由**不受**
`ETA-MARGIN-REMOVED-20260814` 影響:勝者詛咒、時間漂移與單次雜訊是「要把 final ratio 量準」的理由,
不是「要拿它當 gate」的理由。只有其中「預註冊的最終判準(`final ratio ≥ e^{−η_s}`,以 7× 中位數計算)
在字面上就無法評估」這一句現在讀作歷史 —— 該判準已完全不再是 gate 組成(**§7.0.2**),不過 7× 中位數仍是
被報告的估計量。

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
| **AUC `F/G` —— medium** | 0.9509 – 1.0461(**±5 %**) |
| AUC `F/G` —— large | 0.9176 – 1.0509(**−8.2 % … +5.1 %**) |
| 7× 重測 `F/G` —— medium,**有缺陷的儀器**(campaign 1) | 0.3551 – 2.1175(**0.36× – 2.12×**) |
| 7× 重測 `F/G` —— medium,**修復後的儀器**(2026-08-17,§7.1c) | 0.9996 – 1.0633(**1.00× – 1.06×**) |


⚠ **「±5 %」這個說法是 medium 的,不能一般化** —— large 的 AUC 範圍是 −8.2 % 到 +5.1 %(§7.2)。
兩個 shape 上*確實*都成立的,是這裡要做的那個對比:AUC 的範圍與重測的範圍差了一個數量級。

差了一個數量級。**如果 AUC 也帶著同樣的汙染,它就會帶著同樣的離散度。** 它沒有。

> **⚠ 2026-08-18 —— 修復是佐證了這項論證,不是推翻它。** 差一個數量級的那個對比,是 AUC 對上**有缺陷的**
> 重測。在**修復後的**儀器上,同一個 shape 的重測範圍收縮成 **1.00× – 1.06×**,也就是與 AUC 的 ±5 %
> 同一個數量級。這正是該論證所預測的:離散度來自缺陷,不是來自兩臂。**引用這個對比時,一律對照有缺陷的
> 那一列,絕不對照修復後的那一列。**

這是一項觀察,不是從
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
重測 —— 這就是為什麼 medium 的 gate **不論**最終端點問題最後怎麼裁定都會失敗(§7.0.1)。

#### §5c.3 殘餘風險,明說而非埋起來

有一種失效模式挺過了上面三個論證。一個真正強的候選,如果剛好在它**唯一**一次搜尋內評估被低估,它就
永遠不會成為 incumbent,於是 `best_gflops_so_far` 從來不知道它存在過 —— 而 (2) 的累進最大值論證,對一
個從一開始就沒被納入的值毫無保護作用。這一點無法從保留下來的 artifact 量化,因為逐代的 benchmark CSV
沒有保留(每臂只留下 `00_Final.csv`)。狀態:**`NOT_EVALUATED`**,而且 `NOT_EVALUATED ≠ no effect`。

*來源:`[CODE AUDIT]` `stage3_{baseline,guided}/seed_*/medium/trajectory.jsonl`;階梯保持積分的實作見
`agent_run/260809-s14-pershape-baseline/analyze_medium.py`;重測範圍取自 §7.1a。共同預算的必要性:
§3.2b。*

### §5d 四個 gate 量實際上是怎麼量出來的,以及為何其中三個比第四個更耐雜訊

**這一節為什麼存在。** §5c 把 AUC 記錄得很完整。**Gen0 與 gen-10 則完全沒有被記錄** —— 而這個缺口已經
在對話中製造出一個錯誤的解釋,本節就是為了讓那個錯誤不可能再犯一次而寫的。

> **⚠ 要先堵住的那個錯誤。** 很容易會說 Gen0、gen-10 與 AUC「之所以穩健,是因為它們對數千次評估取平
> 均」。**這對 Gen0 與 gen-10 是錯的。** 兩者都不是平均。兩者都是**對單次量測取最大值**,而許多單次量
> 測的最大值,它自己仍然是對單一個 config 的單次量測。那三個量確實比較耐量測缺陷,理由寫在下面,
> **而其中沒有一項是「取平均」**。

#### §5d.1 四個量各自到底是什麼

| 量 | 定義 | 統計上它是什麼 | 欄位 / artifact |
|---|---|---|---|
| **Gen0 best** | `gen: 1` 那一列的 `best_gflops_so_far` | **對約 508 次單次量測取最大值**,每個候選只被 benchmark **一次** | `trajectory.jsonl` |
| **gen-10** | 同一個累進最大值,讀在第 10 代(最後一列 `gen ≤ 10`) | 一樣 —— 累進最大值,不是平均 | `trajectory.jsonl`;`analyze_medium.py:58` |
| **AUC** | `best_gflops_so_far` 對 `cumulative_complete_evals` 積到共同預算 `B*` 的階梯保持積分 | 真的對整條軌跡積分(**§5c**) | `trajectory.jsonl`;`analyze_medium.py:63` |
| **final ratio** | **一個固定 champion** 的 **7** 次交錯重測取中位數,每一次都在**全新的 client process** 裡 | 7 個單次量測的中位數 | `champion_interleaved.json` |

> **⚠ `ETA-MARGIN-REMOVED-20260814` —— 第四列仍然是一個「被量測的」量,但已不再是一個「gate」量。**
> `final ratio` 仍然完全照這一列的定義計算(一個固定 champion 的 7 次交錯 fresh-client 重測取中位數),
> 也仍然以方向與 effect size **照常報告**。2026-08-14 被移除的是 `final ratio ≥ e^{−η_s}` 這個把它變成
> pass/fail 連言項的比較。第 1–3 列(**Gen0、gen-10、AUC**)**在每一個層面都不變** —— 它們從來沒有帶過
> margin,而現在它們就是 gate 的全部。見 **§7.0.2**。

**Gen0,講具體的。** `[CODE AUDIT]` capped medium seed 24001 的 `gen: 1` 那一列:
`generation_candidate_count` **512**、`generation_complete_eval_count` **508**、
`generation_batch_best_gflops` **10287.5**、`best_gflops_so_far` **10287.5**。所以那個 seed 的 Gen0
best 是 **508** 個值裡最大的一個,而每一個值都是對一個 config 的一次 benchmark。native addendum 的分母
比較大,但結構完全一樣 —— native medium seed 24001 baseline 記錄的是
`generation_candidate_count` **11,405**、`generation_complete_eval_count` **11,285**
(`stage5_native_baseline/seed_24001/medium/trajectory.jsonl`)。

**gen-10,講具體的。** `analyze_medium.py:58-60` 取最後一列 `gen ≤ 10` 的 trajectory,並從它讀
`best_gflops_so_far`。因為 `best_gflops_so_far` 是單調非遞減的,gen-10 就是把 Gen0 的最大值延伸到前十代
的候選上 —— 仍然是對單次量測取最大值,從來不是平均。

**AUC** 已在 §5c 說明,這裡不重述;§5d 只需要它的一個事實:四個量之中,它是**唯一**真的對整段搜尋做積分
的那一個。

**final ratio。** `[CODE AUDIT]` `scripts/remeasure_interleaved_champion.py:990 run_interleaved` 跑
`REPEATS = 7` 輪;每一輪對每一臂各呼叫一次 `measure_once`(`:919`),而每次 `measure_once` 都會叫用
benchmark runner,一路走到 `Tensile/ClientWriter.py:231 runClient`,把 client 執行檔以**新的
subprocess** 啟動。`champion_interleaved.json → measurement_metadata` 記錄
`repeats_per_arm: 7`、`single_measurements: 14`、`same_gpu: true`、`same_process: true` —— 其中
`same_process` 指的是 **Python driver**,它被共用是為了讓兩臂落在同一個視窗裡;**client** 在那 14 次量測
的每一次都是全新的。這與 §7.1b 所說的「在一個全新、短命的 process 裡 benchmark 一個 config,因此每次都
從冷的開始」是同一件事,也是 §7.1b.4 所說的「**fresh clients per repeat**」。

#### §5d.2 前三個之所以耐得住這個缺陷的兩個真正理由 —— 沒有一個是取平均

**(1) 曝險。** 搜尋內的評估在**同一個** client invocation 裡,每代把
`cumulative_complete_evals` 推進約 508–512,每個 solution 約 6.4 ms 的 GPU 工作,所以不論那個短視窗效應
是什麼,它**每個 invocation 只付一次** —— 量級是 warm-up sweep 拐點所隱含的約 50 ms —— 最多只能碰到約
510 個 solution 中的**前 8 個**(**約 1.6 %**)。7× 重測則是**每個 repeat 開一個全新的 client
process**,所以它**每一次都要付**:**28–48 %**。§7.1b.1 已經載有這個上界,也是它的引用來源。

**(2) 單調性。** `best_gflops_so_far` 是累進**最大值**,而汙染是**單向向下的**(§7.1b.2)。一個被低估
的評估**不可能拉低**它,它只可能沒把它拉高。Gen0、gen-10 與 AUC 都建立在那個被積函數上,因此都繼承了
這個保護。單次的中位數**沒有**這種保護:向下的汙染會直接把它移動,而那正是 §7.1a 記錄的 mode-lottery
行為。

**實測佐證 —— 同樣的 champion、同一張卡、同一個 shape、同一個 client**(medium capped;下表就是 §5c.1
的那一張,在這裡重列,因為它同時也是本節主張的證據):

| 量 | 逐 seed 範圍 |
|---|---|
| **AUC `F/G` —— medium** | 0.9509 – 1.0461(**±5 %**) |
| AUC `F/G` —— large | 0.9176 – 1.0509(**−8.2 % … +5.1 %**) |
| 7× 重測 `F/G` —— medium,**有缺陷的儀器**(campaign 1) | 0.3551 – 2.1175(**0.36× – 2.12×**) |
| 7× 重測 `F/G` —— medium,**修復後的儀器**(2026-08-17,§7.1c) | 0.9996 – 1.0633(**1.00× – 1.06×**) |

⚠ **「±5 %」這個說法是 medium 的,不能一般化** —— large 的 AUC 範圍是 −8.2 % 到 +5.1 %。
差一個數量級這個對比在兩個 shape 上都成立;「±5 %」這個措辭則不然。

差了一個數量級。如果從 trajectory 導出的那些量也帶著同樣的汙染,它們就會帶著同樣的離散度。

#### §5d.3 誠實的限制

- **Winner's curse 造成的向上偏誤。** 對約 508 次抽取取最大值,是**向上**偏的:贏家有一部分是最幸運的
  那次量測,不只是最好的那個 config —— 這正是 §5 列為搜尋內 fitness 問題 (i) 的同一個機制。所以 Gen0
  與 gen-10 高估了**水準**。但這個偏誤在**兩臂上是對稱的**(相同的族群大小、相同的 client、相同的
  卡),所以它影響的是水準,**不是** gate 真正在評分的那個配對**方向**。這是「不要把 Gen0 當成絕對能力
  數字去引用」的理由,不是「不要相信 G-vs-F 正負號」的理由。
- **§5c.3 的殘餘同樣適用於這裡,不是只適用於 AUC。** 一個真正強的候選,如果在它**唯一**一次搜尋內評估
  被低估,它就永遠不會成為 incumbent,於是 `best_gflops_so_far` 從來不知道它存在過 —— 而累進最大值的論
  證,對一個從一開始就沒被納入的值毫無保護作用。這一點咬 Gen0 與 gen-10 的力道,跟咬 AUC 完全一樣,因為
  三者讀的是同一個被積函數。它無法從保留下來的 artifact 量化(逐代的 benchmark CSV 沒有保留)。狀態
  **`NOT_EVALUATED`**,而且 `NOT_EVALUATED ≠ no effect`。
- **只有第四個分項用到 `η_s`。** 預註冊的 gate 要求 {Gen0, gen-10, AUC} 每一項都有 ≥4/5 對 seed
  **為正** —— 純粹的**方向性**比較,沒有 margin、沒有容忍帶 —— 並另外要求 `final ratio ≥ e^{−η_s}` 在
  ≥4/5 成立(§5、S14 §10.4)。所以 §3.8.1 與 §5 的整場 `η_s` 爭論,只碰到四個分項裡的**一個**。
  如果讀者以為那條容忍帶四項都適用,他會同時誤讀 medium 的 3/5 不足(那是方向性計數)與 large 的
  non-regression 通過(那才是帶 margin 的那一項)。另外也要注意:沒有 margin 的方向性比較,失效模式與
  margin 相反 —— 任意小、任意雜訊的差異它都會登記出一個正負號,這就是為什麼讀 Gen0/gen-10/AUC 的計數
  時,§3.8.2 那個搜尋發散的尺度很重要。
  **⚠ `ETA-MARGIN-REMOVED-20260814` —— 這一條現在是全部,而不是對它的一個 caveat。** 自 2026-08-14 起,
  帶 margin 的第四個分項**已從 gate 移除**(**§7.0.2**),所以 `η_s` **碰不到**任何一個仍然存在的分項。
  這一條的警告在實質上不變,而且變得更重要而非更不重要:剩下的三個連言項是不帶 margin 的方向性計數,
  對於遠在 §3.8.2 那個約 13 % 零 treatment 包絡之內的差異,它們照樣會登記出正負號。這一條最後那句
  「large 的 non-regression 通過(那才是帶 margin 的那一項)」所指的分項,已經不是一項 gate 陳述 ——
  見 §7.2a。

*來源:`[CODE AUDIT]` `stage3_{baseline,guided}/seed_*/{shape}/trajectory.jsonl`(`gen: 1` 那一列;
`generation_candidate_count`、`generation_complete_eval_count`、`generation_batch_best_gflops`、
`best_gflops_so_far`);`stage5_native_baseline/seed_24001/medium/trajectory.jsonl`;
`agent_run/260809-s14-pershape-baseline/analyze_medium.py:54-73`(`gen0`、`gen10`、`auc`);
`scripts/remeasure_interleaved_champion.py:919 measure_once`、`:990 run_interleaved`;
`projects/hipblaslt/tensilelite/Tensile/ClientWriter.py:231 runClient`;
`stage3_baseline/seed_*/{shape}/champion_interleaved.json → measurement_metadata`。曝險上界:
§7.1b.1。單向性:§7.1b.2。AUC 定義與離散度表:§5c/§5c.1。殘餘:§5c.3。gate 定義:§5、S14 §10.4。*

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
DepthU ∈ {32,64,128,256,512,1024} —— 這是凍結空間,見 §3.2c 與 §3.4a.2 的接受數表。**`16` 不在凍結空間裡**,那是一個抄寫錯誤,已於 2026-08-14 更正)。一個取值算 **trusted** 必須在 S11 抽樣語料中同時滿足(`workflow.py:758–802`;manifest `gate_definition`):

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
  - ⚠ **Lock A 在封存之後被編輯過兩次,`.sha256` 也重新簽發過兩次。** §6 與 outline P7 先前把它呈現成一個
    靜態的封存,所以今天去 checksum 這個檔案的讀者,會得到一個沒有任何文件預告過的值。因此把該值記在
    這裡:**目前為 `e413993e…e016753`**,與檔案相符。那兩次編輯是 **2026-08-10 的 GPU 重新編號**與
    **2026-08-14 的換機**(§8.6)。**hash chain 有被保留,而且可稽核**:
    `lock_hash_pre_hostmove = b6b6bbab…`、`lock_hash_pre_reboot = 0a0972d2…`,再加上兩個
    `gpu.assignment_pre_*` 區塊與 `*_reassignment_note` 欄位。
  - **只有 `gpu.*` 改變。** 已驗證:`per_shape_noise_margin.computed` 仍然給出 medium
    `eta_s 0.004195` / floor `0.9958`、large `0.122846` / `0.8844`,以及 `delta_s 0.004204`。
    **治理是健全的** —— 那些編輯有記錄、有範圍、有鏈結、可重現。缺的只是一個指標,而這就是它。
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
- **三個評估計數器**(`run_pershape_seed_native.py:502-504,524-527`、
  `run_pershape_seed.py:377-379,399-402`)—— 先前只列名稱、沒有定義,
  導致任何依賴它們的論證都不可稽核:
  - `cumulative_complete_evals` = 累計「benchmark 對**每一個** size 都回傳有限且嚴格為正的 GFLOPS」
    的候選數, 亦即 `valid.all(axis=0)`, 其中 `valid = np.isfinite(scores) & (scores > 0)`。
    **它數的是成功量測數, 不是提交數**: `cumulative_candidates_submitted` 比它大
    (build 失敗、非有限值、非正值都會被提交但不會成為 complete)。
  - `cumulative_any_valid_evals` = 同一個累計, 但判準是 `valid.any(axis=0)`。
    **S14 每個 shape 只有單一 size, 所以 `all` 與 `any` 取在長度為 1 的軸上, 兩個計數器恆等。**
    已對十個 native large run 驗證: 每一對逐位元相同。**並排列出兩個名稱並不代表這裡有差別。**
  - `cumulative_distinct_benchmarked` = 至今被 benchmark 過的 `canonical_hash(individual)` 的
    **集合**大小(去重, 帳本另落 `distinct_hashes.jsonl`)。它比 `cumulative_complete_evals` 少掉
    重複重測的部分 —— native large 上是 3.2-3.6 %。
  - **為什麼代數與評估數不可互換。** 母體是幾何衰減的(§3.2b), 所以 native large 的前 20 代
    就吃掉約 92 % 的預算, 之後每一代只加約 250-280 次。**一個停在第 20 代與一個跑到第 30 代的 run,
    `cumulative_complete_evals` 只差約 9 %, 不是差三分之一。**
    **AUC 一律對評估數積分, 絕不對代數積分, 理由正是這個。**
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



## §7 結果 —— S14 gate 判定與四個被量測的量


| 報告需要的數值                                                          | 狀態                                                                                                                                         | 來源路徑                                                                                      |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Baseline per-shape/seed champion GFLOPS + gen-10                 | `NOT_EVALUATED`(baseline champions 已存在;分析前維持 quarantine)                                                                                   | `stage3_baseline/seed_*/{shape}/optimization_result.json` + `trajectory_metadata.json`    |
| Guided per-shape/seed champion GFLOPS + gen-10                   | `NOT_EVALUATED` —— **5 seeds × 3 shapes 全數完成**(quarantined)                                                                                | `stage3_guided/seed_*/{shape}/...`                                                        |
| 7× interleaved G/F remeasure medians — MEDIUM                    | **MEASURED 5/5** —— 見 §7.1                                                                                                                 | `stage3_baseline/seed_*/medium/champion_interleaved.json`;`medium_remeasure_summary.json` |
| 7× interleaved G/F remeasure medians — LARGE                     | **MEASURED 5/5** —— 見 §7.2                                                                                                                 | `stage3_baseline/seed_*/large/champion_interleaved.json`                                  |
| 7× interleaved G/F remeasure medians — tiny                      | **MEASURED 5/5** —— 見 §3.8.1;§1 與 §3.8.1 都已帶著完整的一組。⚠ 這一格在 2026-08-14 之前寫的是「`NOT_EVALUATED`(3/5 已重測;24002/24003 待跑)」,那是陳舊資訊 | 同樣式,逐 shape |
| Per-shape directional-consistency gate 結果(Gen0/gen-10/AUC) | **VERDICT:`NOT MET`** —— 四個 block 全數列於 **§7.0.1**;`final ratio` 另行報告,且不對照任何門檻(**§7.0.2**);tiny `NOT_EVALUATED`                                                                                | S14 分析(run 後)                                                                             |
| Conditional Arm S(是否觸發?F vs S)                                   | `NOT_EVALUATED`(conditional)                                                                                                               | Lock C + Arm-S runs(若觸發)                                                                  |
| Native-P0 11,405 large G/F + 相對 512 的稀釋                          | **MEASURED 5/5**(2026-08-17 13:13–13:27)—— 見 §7.0.1、§7.2b。*(2026-08-18 更正:這一格原本寫的是 `NOT_EVALUATED`(排程中)/ run-root TBD。)*                                                                                                                       | `stage5_native_baseline/seed_*/large/champion_interleaved.json`                                                             |
| S11 gates(7-AND)+ decision + reproduction                        | **無法產出** —— 見 §7.3                                                                                                                         | `protocol/v1/{manifests,evidence}/...`(將維持不存在)                                            |
| S11 per-gene sensitivity 表(稀疏性)+ gate margins                    | AVAILABLE(描述性)—— 3 個 gene 過全部 7 gate:PrefetchGlobalRead(S=0.094, +88%)、UnrollLoopSwapGlobalReadOrder(S=0.090, +80%)、DepthU(S=0.054, +7.4%) | `parallel-analyze/out/passes.w72.json`、`diag-lambda2.w72.json`;qa-09 §4.3b                |




### §7.0 S14 gate 判定與四個被量測的量,四個 block 全數

2026-08-18 新增。來源:四份黃金文件 —— `/data1/perlee/measurement_design.md`、
`staged/s14-medium-report.md`、`staged/s14-large-report.md`、`staged/s14-guided-results.md`。
與本索引其餘部分有任何衝突時,**以那四份為準**。

#### §7.0.1 Gate —— 三個不帶 margin 的連言項,`NOT MET`

預註冊的 gate(`s14-stage1-full-ga-outcome-design.md:226`)是**四項**的連言:
`{Gen0, gen-10, AUC}` 各需 ≥4/5 為正,**且** `final ratio >= e^{-eta_s}` 在 ≥4/5 成立。
`ETA-MARGIN-REMOVED-20260814`(owner,2026-08-14)移除了逐 shape 的 margin `eta_s`
**以及第四個連言項作為 gate 組成的地位**,並且**不登錄任何替代門檻**。
⚠ **那個 token 從來沒有被套用到預註冊的 design 檔案本身**(該檔命中數為 0;
本索引的 §2 ledger 註明「由 owner 另行修訂」),所以那份文件至今仍寫成四項。
**實際生效的 gate:前三項。**

| Sub-criterion | medium capped | medium native | large capped | large native | 要求 |
|---|---:|---:|---:|---:|---|
| Gen0 best | **3/5** | 2/5 | **1/5** | 3/5 | ≥4/5 |
| gen-10 best | **3/5** | 1/5 | **2/5** | 1/5 | ≥4/5 |
| AUC(積到共同 `B*`) | **3/5** | 3/5 | **3/5** | 2/5 | ≥4/5 |

**判定:`NOT MET`。** gate 是定義在兩個 confirmatory shape 的 **capped** 條件上:
medium 3/5、3/5、3/5,large 1/5、2/5、3/5。**十二格裡沒有任何一格達到 ≥4/5。**

**這些計數背後的逐 seed guided/baseline 比值**(比值超過 1.0 該 seed 才記為正;
`B*` 是 AUC 積分所積到的共同完成評估預算,§5c):

| seed | medium Gen0 | medium gen-10 | medium AUC | large Gen0 | large gen-10 | large AUC |
|---|---:|---:|---:|---:|---:|---:|
| 24001 | 1.0600 | 1.0174 | 1.0358 | 0.8299 | 0.9362 | 0.9176 |
| 24002 | 1.0007 | 1.0413 | 1.0210 | 1.0660 | 1.0319 | 1.0214 |
| 24003 | 0.9551 | 0.9812 | 0.9783 | 0.9719 | 1.0563 | 1.0509 |
| 24004 | 0.8747 | 1.0718 | 1.0461 | 0.8440 | 0.9426 | 0.9436 |
| 24005 | 1.0073 | 0.8809 | 0.9509 | 0.9771 | 0.9992 | 1.0076 |

**移除 `eta_s` 並沒有改變這個判定** —— 存活下來的三個分項完全不帶 margin,所以對門檻做修訂
不可能撼動它們。這就是對「事後更動門檻」這個顯而易見的懷疑的回答。

⚠ **native** 那兩欄屬於 `NATIVE-P0-ROBUSTNESS-20260811` 的 robustness addendum,
**不屬於 gate**。列出來只是為了比較。

**唯一被允許的否定式措辭,逐字如下:**
> the amended sparse prior, as configured, **did not meet the pre-registered directional gate**

**絕不可以寫「no effect」。** `NOT MET` 與「no effect」不是同一回事。

**Gate 判定的承載者:** `staged/s14-guided-results.md` §5.4(owner,2026-08-18)。
先前的承載者 `staged/full-ga-baseline-vs-guided-outcome-report.md` 已**經 owner 撤銷授權**;
本索引其他地方對它的每一處 deferral 都失效。

#### §7.0.2 Final ratio —— 一個必須報告的量,而且刻意不設門檻

final ratio 被移除的是*gate 組成*的地位,**不是**被報告的量的地位:§2 ledger 說它
「仍然**照常報告**(方向 + effect size,附既有 caveat)」。它的判定方法是
`NULL-AS-NOISE-BASELINE-20260818`(owner):**把 arm F / arm G 對照 arm G / arm G'
的 null ratio 作為雜訊基準;把每一個可得的尺度並列報告;不得把任何東西收斂成單一判定;
不登錄任何倍數門檻。**

**不對照任何門檻。一個被報告的方向與 effect size 不是通過,而且絕不可以被寫成通過。**

| Block | 中位數 `F/G` | 裸計數 `F/G > 1` | 一致地 BETTER | 一致地 WORSE | 一致地打平 | 隨尺度而異 |
|---|---:|---:|---|---|---|---|
| medium capped | 1.0135 | 3/5 | **24002** | none | 24001, 24005 | 24003, 24004 |
| medium native | 1.0036 | 3/5 | **none** | none | 24001, 24002 | 24003, 24004, 24005 |
| large capped | 1.0006 | 3/5 | **none** | **24001, 24004** | 24002, 24005 | 24003 |
| large native | 0.9970 | 2/5 | **24002** | none | 24001, 24005 | 24003, 24004 |

⚠ **那四個「中位數 `F/G`」不是同一個量。** medium 兩列是**修復後**儀器上的 12-window 跨 window
平均(`nw=1400 / RBS=401`,`start_arm G`);large 兩列是**未改動**儀器上的**單 window** 7 次中位數
(`nw=321 / RBS=0`,`start_arm F`)。**不得把這四者互相比較。**

⚠ **裸計數與雜訊尺度彼此不一致,在 large capped 上最為尖銳:** 它的裸計數是 3/5 為正,
但那三個裡有兩個落在雜訊之內,而兩個負值在三種尺度下全都超過 3x。見 §7.2 與
`staged/s14-guided-results.md` §3。

#### §7.0.3 跨日的尺度 —— §7.1c–§7.2b 的那些比值帶著一個未揭露的假設

每個 cell 自己的 window 都是同一天背靠背跑的(`NO-SEPARATION-20260817`),所以一個 cell 的內部 sd
只涵蓋 fast layer。**但四個 block 裡有三個,效應與它的雜訊尺度並不是同一天量的:**

| Block | 效應 / 端點的量測時間 | 雜訊尺度的量測時間 | 間隔 |
|---|---|---|---|
| medium capped | 2026-08-17 08:59–09:31 | 2026-08-17 13:44–15:39 | **同一天**(只有這一個) |
| medium native | 2026-08-17 15:42–15:52 | 2026-08-18 06:51–07:15 | ~15 h |
| large capped | **2026-08-12 00:22–01:50** | 2026-08-18 07:18–08:20 | **~6 天** |
| large native | 2026-08-17 13:11–13:27 | 2026-08-18 08:24–09:04 | ~20 h |

⇒ 在那三個 block 裡,每一個「÷ 尺度」倍數的分子與分母都來自不同的 session。
**那段間隔期間的漂移無法與 kernel 相依的雜訊分離,所以那些倍數是上界未知,而不只是「少了 slow layer」。**
owner 2026-08-18 裁決:**揭露,不重測。**

---

### §7.1 Medium 7× remeasure —— campaign 1,有缺陷的儀器(保留作為「前」)

> **⚠ 讀下面那張表之前先讀這個橫幅(2026-08-18 新增)。**
>
> 本小節的逐 seed 數字是在**未修復的**儀器上量的(`nw = 321 / RBS = 4096`),而且是 **campaign 1**。
> 它們之所以保留,是因為它們是 **§7.5** 儀器修復對照的「前」側 —— 不是因為它們是現況。
> 修復後的讀數在 **§7.1c**(capped)與 **§7.1d**(native)。
>
> **端點狀態:** medium 的 final-champion 端點是**被提議(PROPOSED)**為
> `NOT_EVALUATED / instrument-invalid` —— 既不是通過也不是失敗 —— 且仍然是
> **`PENDING_HUMAN_DECISION`**。不得寫成已裁定。
>
> **Campaign of record:兩個都不是。** owner 已於 2026-08-15 結案 —— campaign 1 與 campaign 2
> 兩者都要報告,兩者都不產生 tier,而且它們**不得取平均,也不得從中挑一個蓋過另一個**。
> 該裁決所要求的替代 campaign(`measurement_design.md` §A.5 的第五個 campaign)**從來沒有被執行過**;
> 2026-08-17/18 的那些 cell 是 **pilot** 範圍
> (`PILOT401_MANIFEST.json`:`"status": "PILOT -- not an endpoint, not a campaign"`)。
>
> **規範 §7.1 與 §7.1c 關係的報告規則 —— 四列,永不合併:**
> (i) 預測的逐字原文與其登錄日期;(ii) 完全照預註冊、未經更動的分析;
> (iii) 儀器問題的發現,以及它相對於揭盲的時間點;(iv) 任何修復後的估計,明確標示為事後補做。
> **(ii) 永不被 (iv) 覆寫。**

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



#### §7.1a Medium 的量測被汙染 —— campaign-1 的 repeat 有 46.4 % 是 dropout(campaign 2:`< 0.80` 下 27.1 %、`< 0.95` 下 27.9 %)—— 7 次取中位數是一場 mode 樂透

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
| **乾淨**(campaign 2,≥ 該臂最大值的 95 %) | **101 / 140 = 72.1 %** | **0.0116** | **2.8×** —— 同一個數量級 |
| **dropout**(campaign 2,`< 0.95`) | **39 / 140 = 27.9 %** | — | — |
| 合併,campaign 2(capped + native) | 140 | 1.0503 | 250× |
| pooled, **campaign 1** (capped + native) | 140 | **1.2098** | **288×** |


**CORRECTION 2026-08-13(third pass,出自 §13 的 design-discussion)。** 上表的「140」是**campaign 2 內的
capped + native** —— 兩個 *P0 level*,不是兩個 campaign —— 而 27.9 % 的 dropout 率是 campaign 2 的。
**campaign 1 —— 解盲之前的那個 campaign —— 其汙染率為 46.4 %**(capped 45.7 %、native 47.1 %);四組全部
合併是 **104 / 280 = 37.1 %**(campaign 1 的 65 加 campaign 2 的 39,兩者都在 `< 0.95` 下;§7.1a 更正
框)。上面引用的 1.2098 屬於 capped campaign 1 的 70 個點,不屬於那個 140 點的 pool。
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

> **⚠ 對一次更正的更正,2026-08-14 —— 2026-08-13 那個「計數已更正」的框本身才是錯的,現予撤回。**
> 該框主張舊的 `39 / 140` 與另一次獨立稽核的 `38 / 140` 在任一門檻下都重現不出來、並以
> `43 / 140 = 30.7 %` 與 `44 / 140 = 31.4 %` 取代之。**兩個原始數字都精確重現得出來。** 以凍結的
> campaign-2 記錄 `agent_run/260809-s14-pershape-baseline/medium_recheck_summary.json` 重算,定義不變
> —— **一次 repeat 若低於其自身 `(seed, arm)` 最大值的給定比例,即計為 dropout** —— 涵蓋
> 5 seeds × 2 arms × 7 repeats × 2 個 P0 level(medium 的 n = 140,其餘為 70):
>
> | shape | campaign | `< 0.80` | `< 0.95` |
> |---|---|---:|---:|
> | medium | **campaign 1**(解盲之前) | **65 / 140 = 46.4 %** | **65 / 140 = 46.4 %** |
> | medium | campaign 2 | **38 / 140 = 27.1 %** | **39 / 140 = 27.9 %** |
> | tiny | — | **1 / 70** | **1 / 70** |
> | large | — | **0 / 70** | **1 / 70** |
>
> `38 / 140` 與 `39 / 140` 是**同一次重算在兩個門檻下的讀數**,不是兩次互相牴觸的稽核。被撤回那個框的
> 診斷 ——「原始數字的定義從來沒有被釘死」—— 是**錯的**:定義沒有問題,**是 artifact 被動過了**。
> `43 / 140` 與 `44 / 140` 是在 `stage3_baseline/seed_24004/medium/champion_interleaved.json` 於
> 2026-08-13 13:29:14 被第三次、未經記錄地就地覆寫**之後**才算出來的(**§8.5**)。
> **`medium_recheck_summary.json` 是唯一可信的 campaign-2 來源**;就 seed 24004 而言,canonical 的
> 逐 seed 檔案已經不是。campaign 1 不受影響 —— 它讀自被保存的路徑 —— 而且在**兩個門檻下都是
> 65 / 140 = 46.4 %**,因為它的汙染很深:campaign 1 的每一個 dropout 都低於 0.80。campaign 1 依 P0
> level 拆開看也沒變:capped 45.7 %、native 47.1 %。
>
> **以下各項曾被撤回的那個框錯誤地推入懷疑,現一併恢復為正確:**「46.4 % vs 27.9 %」(§7.5、
> outline P18);「campaign 1 比 campaign 2 髒 **1.7×**」(§7.5;成因 `NOT_EVALUATED`);「四組全部合併是
> **104 / 280 = 37.1 %**」(上面的 §7.1a —— campaign 1 的 65 加 campaign 2 的 39,兩者都在 `< 0.95`
> 下);以及 campaign 2 在 `< 0.95` 下 `101 / 140 = 72 %` 的乾淨占比(§7.1a 表),`140 − 101 = 39`
> 是佐證而不是反證。
>
> **由本次事件確立的常設規則:** 引用任何 dropout 比率時,一定要同時說明**門檻與 campaign**。兩者皆無的
> 比率不是一個可引用的數字。


| shape | cards used | dropouts(campaign 2,`< 0.95`) | rate |
|---|---|---:|---:|
| medium | hip 5 only (`--gpu-uuid-override`, §8.3) —— ⚠ **但 seed 24004 除外,它是在 hip 7 上被覆寫的(§8.5)** | **39 / 140** | **27.9 %** |
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
| **medium** | ~10 µs | **~3.2 ms** | **46.4 % dropout(campaign 1);27.1 %(campaign 2,`< 0.80`)** |
| large | ~1.87 ms | ~600 ms | **`< 0.80` 下 0 / 70、`< 0.95` 下 1 / 70** |
| tiny | dispatch-bound | (對 warm-up 長度不變) | **兩個門檻下都是 1 / 70** |


>  ### ⚠ MECHANISM CONTRADICTED 2026-08-13 —— 讀下面那段之前,先讀這一段
>
> 接下來那套時脈斜坡的說法,原本是為 warm-up 相關性所提出的*解釋*。一次直接量測現在已經否證了它,
> 以下保留它,僅僅是作為「曾被檢驗過的假說」,**不是**作為一項發現。
>
> `[GPU]` 非 sudo 驗證階梯的第 1 步:3 個 seed × 14 筆紀錄,在**實際進行中的 medium remeasure** 上、
> 於 GPU 5 以 **1 kHz 採樣 `sclk` + `busy` 軌跡**,每次 idle gate 都乾淨(GPU 0 %,host load
> 0.031–0.079 / 224 cores)。現象有重現 —— **在本文件他處一律使用的 `< 0.80` 定義下是 21/42 dropouts
> (`< 0.95` 下是 25/42)** —— 所以這追蹤到的是真實效應,而不是一張安靜的卡。同樣這 42 次 traced
> repeat 的完整階梯:0.70 → 18、0.80 → **21**、0.90 → 24、0.95 → **25**、0.99 → 28。它發現:
>
> - 在這 42 次 traced repeat 上,**時脈與吞吐量無關** —— Spearman **−0.045**,p ≈ 0.78。
> - **dropout 與乾淨重複之間的時脈中位數差,只有約 1–2 %,而觀測到的跨度是 1585–2065 MHz** ——
>   落在雜訊之內 —— 而且它**會隨 dropout 門檻改變正負號**:在 `< 0.80` 下,dropout n=21 中位數
>   **1985.0 MHz**、乾淨 n=21 中位數 **1949.0 MHz**(**+36**);在 `< 0.95` 下,dropout n=25 中位數
>   **1949.0 MHz**、乾淨 n=17 中位數 **1967.0 MHz**(**−18**)。**從它得不到任何方向性主張。**
> - **時脈說法被否證,不是因為 dropout 跑在高溫高頻,而是因為它所預測的低時脈特徵根本不存在:**
>   每一次重複,不論乾淨或被汙染,都**至少達到 1585 MHz**,而兩個反例是明確的 —— 在 **2065 MHz**
>   的峰值*上*只有最大值的 **0.470**;在 **1674 MHz** 卻有 **0.997**。
> - dropout 那幾次**耗時更久** —— kernel 是真的跑得比較慢,這不是回報上的假象。
>
> **⚠ 統計量已於 2026-08-14 更正。** 這個框先前報告 Spearman **−0.32**、中位數 **1798 MHz**(dropout)
> 對 **1689 MHz**(乾淨),以及一個從 **1512 MHz** 起算的觀測範圍。三者都重現不出來。以
> `medium_clockladder/capped/seed_{24001,24004,24005}/s1_trace/` 裡的 42 筆記錄獨立重算三次,採用
> **逐 repeat 取 max-`sclk`** 的估計法 —— 該估計法之所以可信,是因為它把兩個已發表的反例逐位元重現出來
> (2065.0 MHz 處的 `0.470`、1674.0 MHz 處的 `0.997`)。觀測到的逐 repeat 最大時脈範圍是
> **1585.0 – 2065.0 MHz**,所以 **1512 低於觀測最小值**。`1512` 與 `1689` 是
> `medium_clock_probe_summary.json` 裡的**residency bucket 標籤**,而該檔存的 `sclk_trace` 是
> **逐 run,不是逐 repeat** —— 這就是它們混進本文件的途徑。**否證本身不變,而且如果有變化的話是更強了:**
> 一個不存在的特徵,是比一個方向相反的特徵更乾淨的反駁。
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
所以它是一個*不同的 estimand*;而兩個 RBS-4096 變體**25/25 全數 crash**
(50 × `hipModuleLoad rc=-6`)。⚠ **那兩個當中只有一個是長 *warm-up*** —— `B_longwarmup` 設的是
`num-warmups=32100`,而 `C_longwindow` 設的是 `num-enqueues-per-sync=32100` 搭配 `num-warmups=321`,
也就是**一個長的計時視窗,不是一個長的 warm-up**。25/25 的 `rc=-6` crash 對兩者都成立;錯的是對它們
「變了什麼」的描述。

**能一舉定案的那個組態 —— 5,136 warm-ups at RBS 4096 —— 既不是尚未嘗試,也已經不可得。** 它跑過了,
而且在**三個 seed 上全數 crash**(`Insufficient rotating buffer size.`,exit 134),成因是
`DataInitialization.cpp:3213` 的一個確定性 `int32` 溢位;在這個工作集下 `num-warmups ≥ 1638`
**一定**會 crash,把 warm-up 上限壓在約 16–19 ms,而拐點在 51 ms(**§7.5**)。另有一次獨立的失敗記錄在
`s14_medium_clockladder.log:40-42`(`rc=1` ×3,在被釘住的 RBS 4096 下)。**所以這個修法不只是在
production 設定下未經驗證 —— 它在那裡根本不可行。** 關於 ≈58 ms 這個數字:算術是對的(51 ms 的拐點是在
RBS 0,RBS 4096 慢約 13.9 %,12,430 對 14,153 GFLOP/s,而 5,136 × 9.93 µs × 1.139 ≈ 58 ms),但
「**越過拐點**」是錯的 —— 51 ms 那個 sweep 點**就是** `num-warmups=5136`
(`medium_mechanism_probe/ClientParameters_W5136_norot.ini`),所以它是
**與拐點變體相同的 enqueue 次數,只是在 production RBS 下比較慢**。


| probe 變體 | median GFLOP/s | max/min | dropout |
|---|---:|---:|---:|
| 生產設定 | 12,430 | 5.24 | 48 % |
| `sleep-percent = 0` | 12,466 | 2.32 | 40 % |
| `rotating-buffer-size = 0` | 14,153 | 30.6 | 24 % |
| **32,100 warm-ups + RBS 0** | **14,334** | **1.018** | **0 %** |


所有曾觀察到的 dropout 都落在其臂最大值的 `[0.0742, 0.7847]` 區間內 —— 所以每一個被觀察到的 dropout
在 `< 0.80` 下也都是 dropout,這就是為什麼 `< 0.80` 與 `< 0.95` 的計數在每個 shape 上最多只差一次
repeat(下端是
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
追蹤發現**每一次**重複都在 1585–2065 MHz)—— 在**每一個實例中都是空轉的**。被汙染的數值有被記錄下來,
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
上所做的直接 1 kHz 時脈追蹤,已經徹底否證了時脈說法**(Spearman **−0.045**,p ≈ 0.78 —— 根本沒有相關;
而且該說法所預測的低時脈特徵**不存在**,每一次重複都至少達到 1585 MHz —— 見 §7.1b 開頭的區塊,那個
區塊的統計量本身也已於 2026-08-14 更正)。現在去釘 clock,只是在檢驗一個資料已經不利於它的假說。而且它還
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
   定案的檢驗**曾經**是 5,136 warm-ups @ RBS-4096 的 probe(§13.7 項目 2);它已**因不可行而關閉** ——
   確定性的 `int32` 溢位,在三個 seed 上全數 crash(**§7.5**)。所以這條「出路」不只是 `NOT_EVALUATED`,
   而是**在被釘住的 estimand 下取得不到**。
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

#### §7.1c Medium capped 於修復後的儀器(2026-08-17)

來源:`medium_pilot401/results/{C03,C03CONF}_nw1400_rbs401/`,5 個 seed × 各 12 個 window,
`nw = 1400 / RBS = 401`。數值為兩個 batch 的平均。
⚠ **pilot 範圍**,不是 campaign;未被指定為 measurement of record(§7.1 橫幅)。

| seed | `ln(F/G)` | `F/G` | ÷ G/G' sd | ÷ F/F' sd | ÷ 跨 session 0.0097 | ÷ 自身 sd |
|---|---:|---:|---:|---:|---:|---:|
| 24001 | −0.00045 | 0.9996 | 0.1 | 0.1 | 0.0 | 0.1 |
| 24002 | **+0.06024** | **1.0621** | 25.3 | 35.0 | 6.2 | 14.8 |
| 24003 | +0.01336 | 1.0135 | 5.9 | 5.3 | **1.4** | 5.6 |
| 24004 | **+0.06142** | **1.0633** | 39.5 | **3.0** | 6.3 | 3.4 |
| 24005 | −0.00257 | 0.9974 | 0.5 | 0.9 | 0.3 | 0.7 |

**24002 在四種尺度下都明確為正。24003 與 24004 為正,但它們的餘裕取決於用哪個尺度**
(24003 對跨 session 尺度掉到 1.4;24004 對 F/F' 掉到 3.0)。
**24001 與 24005 在每一種尺度下都落在零。沒有任何 seed 在任何尺度下為負。**

尺度的 caveat:**G/G' 這種 null 在構造上永遠不會載入 arm F 的 kernel**(seed 24004:G/G' 的 sd 為
`0.00155`,對比真實對照本身的 `0.01807` —— 相差 **11.6** 倍),所以單用它會誇大顯著性。
**跨 session 的 0.0097 是從舊儀器外推來的**(design §G.2.4,native C1↔C2)—— 修復後的儀器沒有
自己的跨 session 資料。兩個 batch **並不獨立**:`C03` 在 09:10:33 收工,`C03CONF` 在 **09:19:48**
開始,相隔約 **9 分 15 秒**,同一個 session。

#### §7.1d Medium native 於修復後的儀器 —— 無法判定,而且不是因為資料不足

來源:`STAGE2_NATIVE_nw1400_rbs401/`(效應)、`N8_NATIVE_GVSG_nw1400_rbs401/`(G/G' null)、
`N8b_NATIVE_FFNULL_nw1400_rbs401/`(F/F' null),5 個 seed × 各 12 個 window。
⚠ **效應量測於 2026-08-17 15:42–15:52;兩個 null 都在 2026-08-18 06:51–07:15** —— 因此
「÷ null」那幾欄是**跨日**比值(§7.0.3)。

| seed | `ln(F/G)` | `F/G` | ÷ G/G' sd | ÷ F/F' sd | ÷ 自身 sd |
|---|---:|---:|---:|---:|---:|
| 24001 | −0.00306 | 0.9969 | 0.50 | 0.03 | 0.74 |
| 24002 | +0.00363 | 1.0036 | 0.56 | 0.05 | 1.32 |
| 24003 | +0.02696 | 1.0273 | **18.24** | **1.57** | 17.50 |
| 24004 | **−0.12477** | **0.8827** | **8.27** | **1.84** | 86.68 |
| 24005 | +0.06414 | 1.0662 | **6.39** | **0.73** | 4.20 |

**兩個 null 尺度差了一個數量級,而且給出相反的答案。**

| seed | G/G' 中心 | G/G' sd | F/F' 中心 | F/F' sd | F/F' ÷ G/G' |
|---|---:|---:|---:|---:|---:|
| 24001 | −0.00081 | 0.00609 | **+0.03736** | **0.09531** | **15.7x** |
| 24002 | −0.00107 | 0.00654 | **+0.02205** | **0.07546** | **11.5x** |
| 24003 | −0.00054 | 0.00148 | −0.00456 | 0.01717 | **11.6x** |
| 24004 | +0.00063 | 0.01510 | **+0.01889** | **0.06786** | **4.5x** |
| 24005 | +0.00091 | 0.01003 | **+0.02512** | **0.08779** | **8.8x** |

**G/G' null 是乾淨的**(五個中心全都在 ±0.0011 之內)。**F/F' null 不是**:它的真值正好是 1.0,
但**五個中心裡有四個跑到 +1.9 % 到 +3.7 %**(24003 是 −0.456 %),而且它的 sd 是 **1.7 % 到 9.5 %**,
是 G/G' sd 的 **4.5 到 15.7 倍**。
**在 F/F' 之下沒有任何 seed 超過 2x** —— 包括 24004 那個看起來 −12.5 % 的值(只有 **1.84x**)。
**在 G/G' 之下,同樣那三個 seed 讀出 18.2x、8.3x、6.4x。**
⇒ **答案完全由你挑哪個尺度決定,所以不下任何判定。**

⚠ **F/F' 這個行為有兩種未被分離的解釋**:native guided kernel 可能在這台儀器上真的不穩定,
**或者**那次 run 受到了干擾。它 **18.69 %** 的 dropout 與兩者都相容。**未裁定。**

**dropout:** 效應 cell **6.55 %**(通過 P3);**G/G' null 15.60 %、F/F' null 18.69 %,兩者都沒過
P3** —— 一個完全沒有真實效應的 construction,比效應 cell 髒 2.4–2.9x。成因 `NOT_EVALUATED`。

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


> **⚠ `ETA-MARGIN-REMOVED-20260814`。** 上面這張表**照原量測逐字保留**。自 2026-08-14 起,它的
> **`final non-regression` 那一列已不再是 gate 列**:`η_s` 與 `F ≥ G·e^{−η_s}` 分項已被移除其 gate 組成
> 的地位(**§7.0.2**),所以 5/5 與 3/5 兩種讀法都不是任何東西的通過或失敗 —— 它們現在只是描述 per-seed
> 比值相對於兩個已撤回常數落在哪裡,兩者都不得被引用為 gate 結果。`final improvement` 那一列(`δ_s`)
> **不在此次 amendment 範圍內,維持不變**。前四列 —— Gen0 **1/5**、gen-10 **2/5**、AUC **3/5**、
> final-champion 方向 **3/5** —— 完全未動,而其中前三列就是仍然存在的全部 gate:**large 是 NOT MET**,
> 與先前完全相同。

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

> **⚠ `ETA-MARGIN-REMOVED-20260814` —— 以移除解決,不是以裁決解決(經 owner 授權,2026-08-14)。**
> 本小節問的是兩條 margin 中哪一條該治理,並得出「要在兩者之間裁決,需要一個並不存在的跨視窗重複性
> 量測」。owner 的 amendment 以「把 margin 整個從 gate 移除」來解決它(**§7.0.2**),所以**不需要任何裁決,
> 本文也不宣稱做過裁決**。三項後果,精確陳述:
>
> 1. **已經沒有一個 non-regression gate 可以讓 large 通過或不通過。**「large 的 5/5 non-regression
>    通過」不是被弱化的主張 —— 它**根本不再是一項 gate 陳述**。因此「絕不單獨引用那個 5/5」這條常設
>    規則是變嚴而不是放寬。
> 2. **量測留著。** 底下的 per-seed `F/G` 表、兩條 floor,以及 pinned 與實測不一致這件事,都仍可
>    **作為描述性材料連同 caveat 一併報告**,而保留下來的「可辯護的報告方式」那一段仍然是呈現它們的
>    正確做法 —— 只是不得再有 pass/fail 的措辭。
> 3. **本小節自己的證據是這項 amendment 依據的一部分。**「`η_large` 撐在兩個 max/min 為 **1.24** 與
>    **1.42** 的 pilot anchor 上,而 champion 重測的 **1.02–1.05** 重現不出來」在 §7.0.2 被引用;而
>    2026-08-14 的跨 host 重現發現 `η_large` 是三個 pin 裡**唯一**還重現得出來的一個(比值 **1.070**)
>    —— 一個重現得出來、卻從未對照它所 gate 的量測驗證過的 pin。

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
(§3.4)。資料顯示這個張力是真實的,而且 cap 並未消除它:即使只是一個在 **27 個 gene 中對 5 個**施加、
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

#### §7.2b Large —— 兩個 variant 的跨 window 與 null 尺度(2026-08-18)

上面 §7.2 那五個端點都是**單 window** 的。2026-08-18 執行的七個 cell 補上了缺少的離散度。
全部都在**未改動**的 7× 儀器上(`nw = 321 / RBS = 0`,`--start-arm F`),各 6 個 window × 5 個 seed。
它們的 manifest 帶著 `claim_boundary`:*「do not replace the endpoint of record, **are not averaged
into it**, and do not move any shape's S14 status.」*

**large capped** —— 端點在 2026-08-12,尺度在 2026-08-18(**相隔約 6 天**,§7.0.3):

| seed | 端點 `ln(F/G)` | ÷ G/G' sd | ÷ F/F' sd | ÷ 跨 window sd | 三者一致嗎? |
|---|---:|---:|---:|---:|---|
| 24001 | **−0.07488** | **6.67** | **3.25** | **3.80** | **是 —— WORSE** |
| 24002 | +0.01191 | 0.44 | 0.55 | 0.52 | 是 —— 打平 |
| 24003 | +0.06037 | 2.32 | 3.08 | 4.25 | **否** |
| 24004 | **−0.04853** | **6.04** | **3.57** | **4.06** | **是 —— WORSE** |
| 24005 | +0.00064 | 0.04 | 0.05 | 0.02 | 是 —— 打平 |

**有兩個 seed 在三種尺度下都一致地較慢;沒有任何 seed 一致地較快。**
它的裸 `F/G > 1` 計數是 3/5,但那三個裡有兩個落在雜訊之內 ——
**裸計數與雜訊尺度在這裡給出相反的印象。**
F/F' ÷ G/G' 的 sd 比值為 **0.75–2.05x** —— 沒有數量級的爆增。

⚠ **另一個必須並列報告的尺度:** 在預註冊 pin 住的 `eta_large = 0.12285` 之下,
large capped 的 non-regression 是 **5/5**;在實測的 window 內 `eta = 0.0269` 之下是 **3/5**;
improvement 是 **0/5**。那個 5/5 建立在一個**從未針對它所 gate 的量測做過驗證**的常數上
(`s14-large-report.md` §5.3),而 `eta_s` 已於 2026-08-14 自 gate 退役。**它絕不可以被單獨引用。**

**large native** —— 端點在 2026-08-17 13:13–13:27,null 在 2026-08-18 08:24–09:04:

| seed | 端點 `ln(F/G)` | ÷ G/G' sd | ÷ F/F' sd | ÷ 跨 window sd | 三者一致嗎? |
|---|---:|---:|---:|---:|---|
| 24001 | +0.00670 | 0.76 | 0.91 | 0.31 | 是 —— 打平 |
| 24002 | **+0.15026** | **8.69** | **5.24** | **9.77** | **是 —— BETTER** |
| 24003 | −0.04147 | 2.26 | 1.96 | 3.31 | **否** |
| 24004 | −0.01816 | 2.98 | 1.26 | 0.89 | **否** |
| 24005 | −0.00301 | 0.21 | 0.14 | 0.17 | 是 —— 打平 |

F/F' ÷ G/G' 的 sd 比值為 **0.84–2.36x**(24004 的 2.36x 超過 large capped 的 2.05x 上限,
但兩者都遠低於 medium native 的 4.5–15.7x)。

⚠ **24002 的 +16 % 有一部分來自 baseline 臂,不是 guided 變好。** 那個 seed 的 baseline champion
重測得到 **498,236 GFLOP/s**,而 GA 在搜尋期間記錄的是 **565,845** —— **低了 11.95 %**。
這不是量測失敗:498,236 落在 `m6` 六個 window 的範圍 485,541–499,076 之內
(六 window 中位數 494,971,所以端點落在上緣)。它是 baseline 臂上的勝者詛咒效應。
見 `s14-large-report.md` §7.6b.2。

⚠ **跨 window 那一欄不得被單獨用來把某個 seed 判為「雜訊」。** `m6` 自身的合併 dropout 是 **8.10 %**,
對比 native 端點的 **2 / 70 = 2.86 %** —— **比它所評判的對象髒約 2.8x**,所以作為分母它是保守的,
而且會把真實效應誤判成雜訊(`s14-large-report.md` §7.6b.1)。

**dropout,兩個 variant**(本專案唯一實作的定義,`< 0.95 x 該臂 7 次中的最大值`):

| cell | 真實跨 window | G/G' null | F/F' null | 單 window 端點 |
|---|---:|---:|---:|---:|
| large capped | 24.52 % | 24.05 % | 22.38 % | **1.43 %**(1/70) |
| large native | 8.10 % | 22.14 % | 25.00 % | **2.86 %**(2/70) |

對 **capped** 而言,三種 construction 彼此非常接近,這指向的是六 window 背靠背的作業模式,
而不是任何 kernel 或 construction。**對 native 而言它們並不一致**(8.10 % 對上 22–25 %),
所以那個解釋並不完整。成因 `NOT_EVALUATED`。

⚠ **判準註記。** §7.1a 的表使用 **0.80** 判準,在該判準下 large 是 0/70。
本專案的量測程式只實作了 **0.95**(`medium_pilot401/run_cell.py:13`、
`large_xwindow/run_windows.py:82`),在該判準下是 **1/70 = 1.43 %** —— 唯一那一次命中是
seed 24005 的 arm F,`min 522,984 < 0.95 x 550,706 = 523,171`,一個 0.9497 的邊界案例。
**一律說明某個 dropout 數字用的是哪個判準。**

---

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

### §7.4 跨 shape 比較 —— 四個 block 並排

一致性的那張表在 **§7.0.2**。由它可以得到三項讀法,外加兩項必須隨之同行的限制。

**1. 裸計數與雜訊尺度彼此不一致。** 每個 block 的裸 `F/G > 1` 計數都是 2/5 或 3/5,看起來很一致。
在雜訊尺度之下,這些 block 一點也不像:large capped 是唯一有**一致負值**的(兩個 seed),
而 medium native 產不出**任何**可判定的東西。

**2. 只有一個 seed 在任何地方達到「一致地較好」,而且它出現了兩次 —— 兩次都是 24002。**
在 large native 上,那次勝出有一部分來自 baseline 臂的勝者詛咒(§7.2b)。

**3. 雜訊是 kernel 相依的,不是儀器相依的。** 這是 2026-08-18 這一輪最有實質的發現:

| Block | F/F' sd ÷ G/G' sd | 讀法 |
|---|---|---|
| medium capped | **0.52 – 13.33x** | **只有 seed 24004 的 guided kernel 是吵的**(13.33x);24002 與 24005 的 guided kernel 比 baseline 還*安靜*(0.72x、0.52x) |
| **medium native** | **4.5 – 15.7x** | **五個全部** sd 都升高;**五個裡有四個**中心為正 |
| large capped | 0.75 – 2.05x | 兩臂相當 |
| large native | 0.84 – 2.36x | 兩臂相當;24004 的 2.36x 是兩個 large block 裡最高的 |

⇒ **一個 null 不足以刻畫這台儀器。兩個都需要,而且結論可能完全取決於你用哪一個。**

**限制 1 —— 這四個 block 量的是四組不同的 champion 配對。** 以 seed 24004 為例:medium capped 是
`G = c8db13d2… / F = fa7d6353…`,medium native 是 `G = 397d9f67… / F = 14d7349c…` —— 四個臂全都不同。
capped 與 native 是**兩次不同的 GA run**(P0 = 512 vs 11,405),產出不同的 champion。
**逐 seed 的次序在不同 block 之間對不上,是設計上就預期得到的,不需要任何機制,也不得登錄成一個未解現象。
這些 block 不得合併。**

**限制 2 —— 兩個 shape 的量測順序是相反的。** medium 的 window 全部是 `('G','F')`,
large 全部是 `('F','G')`,而 `first_arm` 位於 repeat 迴圈之外,所以配對是把順序效應**凍結**起來,
而不是把它平均掉。**medium 對順序的觀察不能外推到 large。**

### §7.5 儀器修復 —— 前與後(medium)

來源:`staged/s14-medium-report.md` §18。「前」是 **campaign 1**,也就是被記錄下來的那次量測。

| | capped | native |
|---|---:|---:|
| **campaign 1** dropout | **45.71 %**(32/70) | **47.14 %**(33/70) |
| **campaign 1** final champion `F/G > 1` | **2/5** | **3/5** |
| 修復後 dropout | 7.50 % / 6.43 %(兩個 batch) | 6.55 % |
| 修復後 final champion `F/G > 1` | 3/5 | 3/5 |

**三件必須合起來讀的事:**

1. **native 的計數前後都是 3/5。** 修復移動的是汙染率(47.14 % → 6.55 %,約 7.2x)與離散度 ——
   **不是計數**。capped 的 2/5 → 3/5 只是一個 seed。
2. **那些離散度倍數只適用於 capped。** `LADDER_LOG.md:25` 給出 cell A → C03 的逐 seed 改善為
   **50.5x / 51.1x / 99.9x / 18.7x / 72.5x**;A → C03CONF 的中位數 sd 改善 94.9x。
   **native 沒有參考 cell,所以這些數字不能借用到它身上。**
3. **「前」有兩個值,而且相差 1.9x。** campaign 1 capped 是 45.71 %,campaign 2 capped 是
   **24.29 %**;為什麼 campaign 1 比較髒是 **`NOT_EVALUATED`**(`s14-medium-report.md` §16 第 5 項)。
   **兩個都要呈現 —— 只呈現一個就是把一個未結項埋起來。**

⚠ **basis cell A 不是舊 campaign。** 它是 2026-08-17 08:02–08:12、在舊設定下跑的**參考 cell**
(`LADDER_LOG.md:5`:「Cell A is the reference baseline (unmodified instrument); it is never a
candidate」)。它唯一的角色,是提供 campaign 1 與 campaign 2 給不出來的跨 window sd ——
兩者都是單 window、7 次重複,所以對它們而言 `sd(ln(F/G))` 沒有定義。

⚠ **「修復甚至把方向翻轉過來」已被撤回。** basis cell B(只動 cap,warm-up 不變)是
**4/5 為正、中位數 1.0578**,而 cell A 的 12-window SEM 為 ≈ **0.09**,所以它的中位數 0.9917
無法與 1.0135 區分。

**修復在機制上改變了什麼:** warm-up 次數,不是 rotating footprint。兩組正交的單變數對照:
把 warm-up 固定在 321、只改 RBS(cell A → B),dropout 由 39.05 % 變成 **40.60 %** —— 沒有下降;
把 RBS 固定在生產值 4096、只提高 warm-up,則由 **36 % → 8 %**(n = 25 的探測,兩者都在 `sleep0`);
n = 50 的確認 batch 給出 `1400 @ 4096` = **4.0 %**。
⚠ 那次 sweep 是**單臂、帶 override、只有一個 champion 的探測** —— 取它的斜率與正負號,不要取它的絕對水準。

⚠ **`5,136 warm-ups @ RBS 4096` 不可行,但邊界是 `nw >= 1638`,不是「RBS 4096」。**
該探測於 2026-08-13 執行,三個 seed 全部回 `rc = 1`,但**只有 24001 與 24005 走到配置那一步並撞上
int32 繞回**(`Rotating num: 3272`,`1312256 * 3272 = -1265664`);
**24004 更早就因為 library-linkage 錯誤而中止**,與溢位無關。
`1400 @ 4096` 與 `1637 @ 4096` 都在 n = 50 下量過,各為 4.0 %。
正確狀態:**`EVALUATED / closed by infeasibility`**。

### §7.6 什麼能說,什麼不能說

**可以說:**

- **gate 判定 `NOT MET`**(§7.0.1),以被允許的措辭:*「the amended sparse prior, as configured,
  **did not meet the pre-registered directional gate**」*。
- 各 block 的 `F/G` 讀數,以及它們對照每一個可得尺度的倍數(§7.1c–§7.2b)。
- §7.0.2 的一致性讀法,包含 large capped 那兩個一致較慢的 seed,以及 medium native 的不可判定性。
- 雜訊是 kernel 相依的(§7.4)。
- 修復的前後對照(§7.5)。

**不可以說:**

- **「No effect。」** `NOT MET` 不是「no effect」,`NOT_EVALUATED` 也不是。
- **任何被寫成通過的 `final ratio` 讀數。** 自 2026-08-14 起它**沒有任何門檻**。
  *一個被報告的方向與 effect size 不是通過,而且絕不可以被寫成通過。*
- **任何 shape、任何 variant 的 `max`-of-7 出現在任何 acceptance 或 sensitivity 表格。**
  在 `max` 之下,native 的 non-regression 由 3/5 變成 **4/5** —— 跨過預註冊門檻,而且是往受測臂的方向。
  只能作診斷用途,且必須明確標示。
- **單獨引用 large 的 5/5 non-regression。** 它是本研究唯一在任何地方通過的預註冊分項,
  它建立在一個從未針對它所 gate 的量測做過驗證的常數上,而且那個 margin 已於 2026-08-14 退役。
  這項限制**並沒有因為退役而放鬆 —— 它反而更強了。**
- **任何從 medium 的 final 端點導出的 tier**,該端點是被提議(PROPOSED)為
  `NOT_EVALUATED / instrument-invalid` 且仍 PENDING。
- **任何 aggregate rescue**、任何一般化、部署或加速的措辭,或把 `original_final_gflops` 當端點用。
- **把四個 block 合併**,或用某個 block 的雜訊尺度去評判另一個 block。

**逐 shape claim 階梯**(每個 shape 撐得起的措辭):
**medium** —— gate 未達成;端點被提議為 invalid 且 PENDING;**沒有** non-regression 通過、
沒有 improvement claim,也不得從任一者導出 tier。
**large** —— gate 未達成(1/5、2/5、3/5);那個 5/5 non-regression **只能**作為眾多分項之一出現,
絕不可單獨出現。
**tiny** —— 僅描述性,在 confirmatory gate 之外;它同時也是一個意外得到的 null control。
**合併** —— *「did not meet the pre-registered gate」*,**不是**「no effect」;不得 aggregate rescue。

**一個值得單獨做一張投影片的方法學結果。** 在 **tiny** 上,兩臂是**位元相同**的
(27 個 gene 有 0 個被啟動,所以真實差異正好是零),但這套量測設定仍然產出
**max |ln F/G| = 0.1247 —— 在一個已知的 null 上出現看似 13.3 % 的差異**。
一個低於約 13 % 的門檻會把已知的零判成有效應;高於它的門檻則會吞掉本研究能偵測到的每一個效應。
**可接受門檻的區間是空集合。** 這就是為什麼 `eta_s` 退役時不登錄任何替代門檻。

**跨 host 重現(2026-08-14)。** 原始 pilot 在第二台主機上重跑,三個 anchor hash 全部重現。
**只有 `eta_large` 重現得出來**:large 1.070 / medium 0.335 / tiny **0.0098**,而 `eta_tiny` 的
5.13x —— 可追溯到單一個 anchor —— 在新主機上掉到 **1.23x**。這把原本只是鑑識推論的東西升級成了量測。

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

### §8.5 第三次、未經記錄的 canonical artifact 就地覆寫 —— seed 24004 capped medium,2026-08-13

**覆寫記錄是不完整的。** §7.6 的更正框列出**兩**次就地覆寫事件,兩次都在 2026-08-12
(capped medium 14:01–14:04Z;native medium 14:05:07–14:08:18Z)。**第三次**存在,而且從未被記錄在任何
地方:

`stage3_baseline/seed_24004/medium/champion_interleaved{.json,_raw.jsonl,_status.json}`,mtime
**2026-08-13 13:29:14** —— **unblinding 之後 23 小時**,也是那兩次已記錄事件之後一天。

**成因 —— clock-ladder probe 與 remeasure watchdog 之間的一次 TOCTOU race,證據齊全。**

1. `scripts/s14_medium_clockladder_probe.py` 的 `move_out()` 會**把那三個 canonical `ARTIFACTS`
   rename 移出 seed 目錄**,好讓 probe 能寫進那個路徑。
2. Watchdog 判斷有無工作的述詞是 `todo = [sh for sh in SHAPE_ORDER if not remeasure_done(seed, sh)]`
   (`s14_guided_remeasure_driver.py:184`)—— 這是**對那三個檔案的存在性檢查** —— 而 `--output-dir`
   被寫死成 canonical 目錄(`:127`)。**那次暫存把述詞反轉了:** 檔案被移走的期間,該 seed 讀起來就是
   「尚未重測」。
3. `s14_guided_remeasure_driver.log:372-373` —— `[13:28:24Z] seed 24004: LAUNCHED remeasure shapes
   ['medium'] (pid 163627, hip 7)`。`stage3_baseline/seed_24004/remeasure_chain.log` —— START
   13:28:24Z、END rc=0 **13:29:14Z**,與 mtime 相同。
4. `move_back()` 的守門 `if dest.exists(): raise` 在約 24 秒處**通過了**,因為競爭的寫入者要到約 50 秒
   才落地。**最後寫入者勝出。** 沒有留下任何 `superseded_*` 標記。
5. **只有 seed 24004** 中招,因為只有它的暫存視窗 `[13:28:14, 13:28:38]` 涵蓋到一次 watchdog 輪詢
   (輪詢時點為 13:22:01 與 13:28:24)。

**變成了什麼。**

| | G repeats (GFLOP/s) | F repeats (GFLOP/s) | `F/G` |
|---|---|---|---:|
| **凍結(紀錄用的 campaign 2)** | 12583.8, 12592.5, 6669.5, 4958.4, 12608.3, 12592.2, 9779.9 | 6725.0, 4744.5, 13505.8, 13683.8, 13636.8, 13858.3, 6297.7 | **1.0733** |
| **現行(覆寫後)** | 1284.0, 12551.4, 6530.8, 12447.2, 2310.1, 2309.6, 2178.0 | 1218.5, 11976.5, 4063.5, **96.7**, 2349.4, 2345.1, 2344.9 | **1.0151** |

那個 `96.7` 是**其臂最大值的 0.8 %** —— **整項研究中最極端的 dropout**,而且它就**未加標示地躺在生產
路徑上**。

**除了數字之外,還有兩項來源事實必須入帳。**

- **卡片與綁定改變了。** 執行覆寫的那次 run 用的是 **hip 7 / `GPU-bc724e0cf5b78d17`、taskset 44-55、
  `gpu_uuid_override: null`**。campaign 2 則是**全程透過 `--gpu-uuid-override` 跑在 hip 5 上、taskset
  96-107**。所以 capped medium 的 canonical 集合**已經不再是在同一張卡上量的** —— 而那正是 **§8.3**
  為該項 deviation 所記錄的理由。§8.3 的正當性論證涵蓋不到這個檔案。
- **它的 `status: PASS` 不是一次通過。** 那個旗標是對照 `η_s` 準則評出來的,而
  `ETA-MARGIN-REMOVED-20260814` 此後已把該準則移除(**§7.0.2**)。它是對一個已不存在的準則的通過。

**對分析的後果,講白:** `analyze_medium.py --campaign 2` 目前對 seed 24004 回傳的是
**任何 campaign 都不曾量過的狀態** —— 四個 seed 是 campaign-2 的值,第五個是 2026-08-13 那次 probe race
的產物。**要求 `--campaign` 並不能圍堵這件事**:那個旗標是在兩條*路徑*之間做選擇,而其中一條路徑已經
被改動過。**`medium_recheck_summary.json` 是凍結的 campaign-2 記錄,也是唯一可信的 campaign-2 來源**
(§7.1a)。

#### §8.5.1 這個 race 是休眠,不是關閉 —— 精確的重新開啟條件

排程器是一個**主機層級的 cron**,呼叫 `scripts/s14_resume_all.sh`;該腳本自己在 `:16-18` 的註解就是
這樣寫的。**容器內沒有任何東西排程它** —— `crontab -l` 是空的、沒有 systemd timer,而那個 10 分鐘的
容器內 monitor 已於 2026-08-11T03:30:12Z 死亡。它**每 30 分鐘、在 :28 與 :58 觸發**,以 `flock`
串行化。

**目前它是休眠的。** 15 個 seed × shape 的 canonical 檔案全部存在,所以 `remeasure_done` 到處都為真,
而 `guided_remeasure_status.json`(ts **2026-08-14T16:28:47Z**)對全部五個 seed 都記著
`action: remeasure_complete`。

**這個 race 只在、且只要一個 canonical `champion_interleaved.json` 被 rename 或移除時,就重新開啟** ——
而那正是 `move_out()` 做的事。任何未來會暫存 canonical artifact 的 probe,都必須在其執行期間停掉那個
cron,或改寫到 canonical 目錄以外的路徑。那是一項要由 owner 授權的基礎設施變更,而且
**在有 run 正在進行時不得執行**。

#### §8.5.2 鑑識註記 —— rename 現在是看不見的

2026-08-14 的換機(**§8.6**)**把每一個 inode 的 ctime 都重設為 2026-08-14 03:24–03:25**。rename 會保留
mtime、只改 ctime,所以 **`move_out()` / `move_back()` 的循環現在對檔案系統鑑識而言完全不可見**。
實證:seed 24001 與 24005 在 08-13 確實被暫存又還原過,但兩者讀出來仍然是 08-12。

要據此讀那個否定結果。**「沒有第五次覆寫」** —— 由兩位稽核者橫跨 80 份 GA 輸出、60 個 canonical
artifact 與一次完整視窗掃描獨立驗證 —— 意思是**沒有第五次*寫入*,不是沒有第五次*碰觸***。這個區分不是
在鑽牛角尖:它是「沒有別的東西被改過」與「現在已經無法證明別的東西有沒有被改過」之間的差別。

*來源:`[CODE AUDIT]` `scripts/s14_medium_clockladder_probe.py`(`move_out`/`move_back`、`ARTIFACTS`);
`scripts/s14_guided_remeasure_driver.py:127, :184`;`scripts/s14_resume_all.sh:16-18`;
`s14_guided_remeasure_driver.log:372-373`;`stage3_baseline/seed_24004/remeasure_chain.log`;
`stage3_baseline/seed_24004/medium/champion_interleaved{.json,_raw.jsonl,_status.json}`(mtime、
`gpu_uuid_override`、`status`);`medium_recheck_summary.json`;`guided_remeasure_status.json`。*

### §8.6 2026-08-14 的換機 —— 記在這裡,因為兩份文件先前都沒有提到它

在 2026-08-14 之前,本索引與 `outline.md` 都不含 `banff`、"host move" 或 "hostmove" 這些字串。這次換機
對三項各自獨立的主張都有影響,在此完整記錄。

- **發生了什麼。** 容器於 2026-08-14 **03:35:10Z** 在一台新的實體機器 **`banff-cyxtera-s77-4`** 上被
  重建。前一台主機已連續運行 **169 天**。
- **重新綁定了什麼。** 五顆 GPU 的 UUID 全部重新綁定。工具鏈的 pin 與 client binary 的 sha256 經
  **驗證跨換機完全相同**。
- **被混淆的是什麼 —— 真正重要的那項揭露(Q2)。** native large 現在跑在**新**機器上,而 capped large
  跑在**舊**機器上。主機與*臂***沒有**被混淆(capped large 的兩臂都在舊主機、native large 的兩臂都在
  新主機),但**主機與 P0 level 有**。就 large 而言,實測的跨主機因子是 **1.018 中位數(約 2 %)**,
  所以這是一個**次要**的 confound,而且必須以次要的程度揭露。
- **`2.59×` 是什麼,以及為何不得把它當成跨主機因子引用。** `hostmove_deviation.md` §5.1 記錄了一次
  **smoke test**:在新主機上重跑保存下來的 `config/s14-pershape-smoke.yaml`,在**同樣 35 個候選**上得出
  **同一個勝出 kernel**(`MT192x192x32_MI16x16x1`),但速度是 **2,591.88 → 6,716.68 GFLOP/s = 2.59×**。
  §5.2 接著以兩項獨立量測**撤回了這個一般化**:跨主機的 `large` champion 重測是 **1.018 中位數**
  (幾何平均 1.037,範圍 0.997–1.131),而 noise pilot 自己的 **medium anchor 從 3,199.94 移到
  3,175.53 = 0.992×**,也就是慢了 0.8 %。所以 2.59× 是**特定 shape、特定 kernel 的,不是一個全機層級的
  水準位移**。那一個 GA 搜出來的 smoke kernel 為何在這裡快 2.59×,是 **`NOT_EVALUATED`** —— 該 smoke
  並未被重跑以隔離成因。**large 請引用 1.018;絕不要把 2.59× 當成跨主機因子引用。**

*來源:`hostmove_deviation.md` §§1-7,尤其 §5.1 / §5.2 / §7。*

---
### §8.7 2026-08-17/18 儀器修復與 null campaign 的未結項

2026-08-18 新增。以下全部是尚無 root cause 的觀察;沒有一項是 claim。

1. **為什麼 medium native 的 guided kernel 是吵的。** 它的 F/F' null(真值正好是 1.0)sd 為
   **1.7 % – 9.5 %** —— 是它 G/G' null 的 4.5 到 15.7 倍 —— 而且五個中心裡有四個跑到 +1.9 % 到 +3.7 %。
   **兩種解釋未被分離:** native guided kernel 可能在這台儀器上真的不穩定,**或者**那次 run 受到了干擾。
   它 **18.69 %** 的 dropout 與兩者都相容。⇒ 因此得到的「medium native 無法判定」是一個**現象**,
   不是一個已排除其他可能的結論。`NOT_EVALUATED`。

2. **為什麼跨 window 的 cell 比單 window 的端點髒。** large capped:真實 / G/G' / F/F' 分別是
   24.52 / 24.05 / 22.38 %,對上 **1.43 %** 的單 window 端點 —— 約 17x。三種 construction 彼此一致,
   指向的是六 window 背靠背的作業模式,而不是任何 kernel。**但 large native 並不遵循同一個模式**
   (真實 8.10 % 對上 null 的 22–25 %,只比它 2.86 % 的端點高 2.8x),所以那個解釋並不完整。
   `NOT_EVALUATED`。

3. **同一個 kernel 上出現 12 % 的雙叢集分裂。** 對 seed 24002 的 baseline 臂 champion
   (`config_hash 9908df17…`):canonical 端點讀到 **498,236**,`m6` 的六個 window 讀到
   485,541–499,076,而 `race_m3` 的三個 window 讀到 **558,420 / 559,859 / 569,037**。canonical 值
   由 m6 重現;離群的是 `race_m3` 這個探測,而它不餵給任何端點。**不得主張哪一個叢集是對的,
   也不得把 GA 記錄的 565,845 併進其中任何一個。** `NOT_EVALUATED`。見
   `staged/s14-large-report.md` §7.6b.2。

4. **修復後的儀器沒有任何跨 session 資料,而四個 block 裡有三個仍然跨日計算它們的比值。**
   見 §7.0.3。owner 裁決:揭露,不重測。

5. **tiny 沒有修復後的資料,也沒有 null 資料。** tiny 依設計沒有 native variant
   (`staged/s14-tiny-report.md` §0.3),而它的零處理包絡(§7.6)是在修復前的儀器上量的。
   那個包絡在修復後的儀器上會不會改變,是 `NOT_EVALUATED` —— tiny 對 warm-up 長度不敏感(§8.7),
   但那是推論,不是量測。

6. **Lock A 帶著一個內部矛盾,而且它仍未結案。** 它的 `lock_state` / `note_no_seal` 與它的
   `verifier_record.resolution` 彼此不一致,而 Lock A 是本研究對 `R_s`、`η_s`、seed 與 RNG 的權威來源。
   2026-08-14 開啟;**已記錄,未解決。** 任何外部稽核者第一輪就會找到這一項。

---

## §9 已刪除的章節 —— 它們的內容去了哪裡

2026-08-18,owner 指示已退役的材料應予**刪除**而非加註,因為本檔現在是投影片的來源。
三個章節被移除(`§9 PENDING_HUMAN_DECISION`、`§10 ETA-MARGIN-REMOVED-20260814`、
`§11 2026-08-17 的 campaign 編錄`),約 **830 行**。
**所有承重的內容都是先被搬走**,不是被丟掉:

| 內容 | 現在在哪 |
|---|---|
| gate 是三個連言項;預註冊未經修訂;`final ratio` 仍是必須報告的量 | **§5** gate 框、**§7.0.1**、**§7.0.2** |
| 「不對照任何門檻……絕不可以被寫成通過」 | **§5**、**§7.0.2**、**§7.6** |
| `NOT MET` 判定表**以及其背後的逐 seed 比值** | **§7.0.1** |
| 「did not meet the pre-registered directional gate」—— 絕不是「no effect」 | **§7.0.1**、**§7.6** |
| medium 端點被提議為 `NOT_EVALUATED / instrument-invalid`,PENDING | **§7.1** 橫幅 |
| campaign of record = 兩個都不是;替代 campaign 從來沒有被執行過 | **§7.1** 橫幅 |
| 四列,永不合併 —— (ii) 永不被 (iv) 覆寫 | **§7.1** 橫幅 |
| `nw >= 1638 @ RBS 4096` 的不可行性,範圍正確界定;24004 死於 library linkage,不是溢位 | **§7.5** |
| 「修復甚至把方向翻轉過來」—— 已撤回 | **§7.5** |
| 逐 shape claim 階梯 | **§7.6** |
| `max`-of-7 的刊登禁令 | **§7.6** |
| large 的 5/5 non-regression 絕不單獨引用 | **§7.2b**、**§7.6** |
| tiny 的零處理包絡 —— 可接受門檻的區間是空集合 | **§7.6** |
| 跨 host 重現;只有 `eta_large` 重現得出來;`eta_tiny` 5.13x → 1.23x | **§7.6** |
| Lock A 的內部矛盾,仍未結案 | **§8.7** 第 6 項 |

**編號註記(自已刪除的 §10 搬來)。** 本檔其他地方出現的 `S14 §10.x`、`S14 §11`、`design §10.x` 與
`s14-large-report.md §10.x`,指的是**那些文件自己的章節**,不是本索引的章節。本索引已經沒有 §10 或 §11。

---

*維護:capped G/F、7× remeasure、conditional Arm S、native-P0、S11 closeout 落地時,更新 §1 狀態與 §7 結果
格。本索引維持非權威 —— 任何實質變動先回寫到所引用的權威文件,並同步結構/敘述到英文版*
`report-source-index.md`*(英文為權威)。*
