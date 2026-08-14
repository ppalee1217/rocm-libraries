> **TERMINAL — S11 as-sealed closeout is NOT PRODUCIBLE (not "pending"). `scientific_outcome: not_evaluated`; the sealed positive criterion `S1_GUIDANCE_LOCKED` is UNREACHABLE-AS-SPECIFIED on this data (neither PASS nor FAIL). S11 did deliver a verified per-size score artifact and a large, reportable model-only result set; those are reported below with per-gene data and root-cause analysis.**
>
> 本檔為 S11 的 **terminal report**。與先前 DRAFT-SCAFFOLD 不同，S11 的 formal `analyze→decide→reproduce` closeout **不是「還在跑」，而是「跑不完」**：sealed `analyze` 在 `protocol/v1/s11/guidance.py:95` 的 `assert chosen is not None and bundles is not None`（`select_global_lambda`）**確定性地終止**，這已由一次 out-of-band parallel 重現以四軸驗證並判定為 **(A) FAITHFUL**（§9.3）。因此 `manifests/s11-analysis.json`、`manifests/s11-guidance.json`、`evidence/s11-decision.json`、`evidence/s11-reproduction.json` **永遠不會存在**——本檔**不留 `TBD@closeout` placeholder**，改為明確標示 `NOT_PRODUCIBLE` 並給出原因。**本檔不為 `S1_GUIDANCE_LOCKED` 捏造 PASS／FAIL。**

---
checkpoint_id: S11
title: Stage 1 model-only factorization／guidance lock
stage: 1
report_status: TERMINAL
scientific_outcome: not_evaluated   # sealed analyze terminates in an AssertionError before emitting s11-analysis.json; no `decide` input exists and none can be produced without owner-level authority. NOT "pending".
criterion_status: UNREACHABLE_AS_SEALED   # S1_GUIDANCE_LOCKED cannot be evaluated: the frozen first-match matrix has no row matching the observed terminal state (§9.7)
positive_criterion: S1_GUIDANCE_LOCKED   # status: NOT_EVALUABLE (neither PASS nor FAIL) — see §9.7
failure_ids: [FT-BLOCKED-MAPPING, FT-INCONCLUSIVE]   # neither is asserted; listed as the contract's declared failure vocabulary only
negative_code: COMPLETE_DETERMINISTIC_NO_GUIDANCE    # NOT asserted — the literal row-6 condition is not satisfied (§9.7)
lock_state: LOCKED_READY   # sealed tree verified unchanged (§9.3(c))
current_artifact_state: CLOSEOUT_NOT_PRODUCIBLE   # global-discovery/conditional-discovery/qualify/score COMPLETE and present; analyze aborts; decide/reproduce unreachable
outgoing_edge: null   # S11:S1_GUIDANCE_LOCKED -> S12 never became valid and cannot become valid from this run
delivered_artifacts: [s11-registry.json, s11-global-prefix.json, s11-conditional-prefixes.json, s11-qualifications.json, s11-native-scores.json]
never_producible_artifacts: [s11-analysis.json, s11-guidance.json, s11-decision.json, s11-reproduction.json, gate-records/s11-s1-guidance-locked.json]
execution_tranche: T-S1-MECHANISM
closure_unit: CU-S1-MECHANISM
design_source: ../../s11-stage1-model-only-factorization-design.md
contract_source: ../../protocol/v1/s11-stage1-model-only-factorization-contract.yaml
effective_lock_source: ../../protocol/v1/locks/s11-stage1-model-only-factorization-lock.json
lock_sha256: 45e77ab4ba8b931aeb929cd1b1a650fb92d3ada6a80830394eecd3d92d7e0321
---

> **Non-authority framing.** 本報告是 checkpoint report，不是 authority。若與 [research charter](../../../surrogate-dse-plan.md)、[experiment plan](../../../ductile-origami-warmstart-experiment-plan.md)、[S11 design](../../s11-stage1-model-only-factorization-design.md)、[S14 design](../../s14-stage1-full-ga-outcome-design.md)、frozen contract/lock 衝突，一律以後者為準。QA 檔（qa-03、qa-09）為白話導讀，非 authority。
>
> **Evidence labels（全文一致）：**`[MODEL-ONLY]`＝Formocast 模型空間量；`[CODE AUDIT]`＝讀 code／sealed artifact 得到的事實，附 `file:line`／artifact 路徑；`[BASELINE GPU]`＝S14 baseline 臂真實量測（**S11 本身沒有任何真實 GPU 結果**）；`[GUIDED GPU]`＝本檔無。
>
> **Anti-fabrication：**沒有真實跑出來的數字不編；`not_evaluated ≠ no effect`；`not_producible ≠ negative`。本檔所有數值均由撰稿者直接對 primary artifact 重算或讀取後才寫入（每處標明來源檔）。
>
> **§8.5 措辭紀律：**本檔的稀疏／阻塞結果一律**定位到層次**（marginal-loss），**絕不**寫「模型沒用」。

---

## 0. 本報告的三層結構

讀者務必分清以下三層，它們的證據地位完全不同：

| 層 | 內容 | 狀態 |
| --- | --- | --- |
| **A｜as-sealed formal closeout** | sealed max-reducer pipeline 的 `analyze→decide→reproduce` 與 `S1_GUIDANCE_LOCKED` 判定 | **NOT PRODUCIBLE**（§9.3、§9.6、§9.7）——確定性 `AssertionError`，非「還在跑」 |
| **B｜S11 實際交付的 model-only 證據** | 27/101 registry replay、三層 population、per-size Formocast 分數（`s11-native-scores.json`）、26-gene aggregate-max gate table、entropy 結構上界 | **DELIVERED & VERIFIED**（§9.1、§9.2、§9.4、§9.5、§10.4、§13） |
| **C｜由 B 觸發、已 user-approved 的 downstream 決策** | max-reducer 建構效度、per-shape 重導、`ENTROPY-CAP-20260810`、sparsity 稽核、Lock B | **已定案**（§10–§13）——皆為 **S14 out-of-band artifact**，不是 S11 formal artifact |

**A 與 B/C 的關係：**A 從未產出 guidance；因此**實際餵給 S14 的 treatment 完全來自 B 的 per-size 分數經 C 的 per-shape 重導**（§12）。S11 對整條研究線的真實貢獻是 **B（per-size 分數 ＋ 模型訊號結構的量化）＋ C 的 Lock B**，不是 A 的 gate。

---

## 1. S11 hypothesis、scope、能與不能宣稱

### 1.1 白話目標與核心問句

S11 是整條研究線第一個真正「動手做 factorization（因子分解）」的 checkpoint，而且**全程 label-blind**：選哪些 gene、給多少權重，只能用 **Formocast**（`origami` 內的 physics/analytical GPU kernel 延遲模擬器，非 ML、非經驗公式；見 [QA-03 §0.1](../../qa/qa-03-s11-factorization-and-metric-design.md)）的預測分數，**絕不能碰真實 GFLOPS**。核心科學問句：

> 把 whole-config 的 Formocast 訊號，拆成 per-gene（逐參數）的抽樣機率後，**還剩多少真正有用的資訊？如果拆完就失真了，訊號消失在哪一層？**

落差在於：Formocast 看**一整組完整 kernel 參數**吐一個預測延遲；Ductile 的 Gen0 抽樣介面只吃「每個 gene 的每個候選值各應多常被抽到」。factorization 就是把「整組分數」拆成「每個參數各自偏好」的動作。S11 只建立 guidance 這個**機制**是否可行、在**模型空間內**是否穩定；它**不**證明 guidance 指向真實高品質 config（那是 S12/S14）。

**本次執行給出的答案（提前劇透，詳見 §9.4／§9.5）：**訊號**確實存在但極稀疏**——26 個可檢定 gene 中恰 **3 個**通過全部七道 model gate，且是以 **1.79×–11.86× 的寬裕邊際**通過，不是勉強擦邊。真正卡死 S11 的**不是訊號不足**，而是最後一步把「證據」轉成「抽樣分布」時，一道與 gene 基數（arity）耦合的固定 entropy floor 在數學上不可能被滿足。

### 1.2 Hypothesis 與 falsification（design §2）

**S11-H1：**依 `S1-REBASELINE-20260803` 與 `S11-S12-FIXED-FRAME-20260803` 的 fresh fixed frames、trusted survivor estimand 及 familywise model-only criteria，Formocast 能對至少一個 `|T_g|>=2` 的 residual gene 產生穩定 prior，並可無損轉成與 `SearchSpace.map` 完全對齊的 weights 與 shuffled control。

反證/inconclusive（design §2）：無 eligible/guidable residual gene、`|T_g|<2`、global lambda 退化、mapping/coverage/support/sensitivity/stability 未過、own-null 或 familywise max-null P95 未 strictly 超過、global cap 未取得 8,192 accepts、occurrence multiplicity 於 dedup 後遺失、round-trip/order/weight sign 錯誤、existing group/weight 被改、或任何 real score/oracle output 參與 gene/weight 選擇。

**觀測到的狀態不落在上列任一項。**H1 的前半（「至少一個 `|T_g|>=2` 的 gene 有穩定 prior」）在**證據層**成立（3 個 gene，寬裕通過；§9.4）；後半（「可無損轉成 weights」）在**建構層**被 entropy floor 阻斷，且該阻斷是 `(n_candidates, k_trusted)` 的結構性質，與 data 無關（§9.5）。H1 因此既未被證實、也未被證偽——**它在這條 sealed 路徑上不可判定**。

### 1.3 唯一 positive criterion 與判定邊界（含已發現的矩陣缺口）

唯一 positive criterion 是 parent 的 `S1_GUIDANCE_LOCKED`；失敗模式 `FT-INCONCLUSIVE`（機制不足以判定）與 `FT-BLOCKED-MAPPING`（`empty-v1` allowlist `entries: []` 下**不可到達**）；complete-bounded negative `COMPLETE_DETERMINISTIC_NO_GUIDANCE`（沒有 gene 通過檢定或 lambda=0）。判定為互斥 first-match precedence（design §7）。

**`[CODE AUDIT]` 已發現的缺口：**觀測到的終止狀態——「**guided set 非空（3 gene 全過七道 gate），但 λ grid 上不存在任何可行 λ**」——**不匹配 design §7 的任一 row**，也不在 contract `outcomes.inconclusive.material_causes`（`support, coverage, precision_or_recurrence, final_half_stability, global_Uexec_below_256`）之內。row-6 的兩個 disjunct（「沒有 gene 通過 effect/permutation/direction/entropy」與「lambda 為 0」）**都不成立**：`UnrollLoopSwapGlobalReadOrder` 在 λ=0 的 `H_norm=1.0` 是通過 entropy 的；而 λ 不是 0，是**不存在**（sealed code 在指派前就 assert）。詳見 §9.7；此缺口需 owner 層級裁決，本報告**不代為填補**。

### 1.4 能宣稱／不能宣稱（scope 摘要，§14 詳述）

**能（本次執行實際成立的）：**在 executable-and-scoreable survivor frame 內、3 個 locked size 上，(i) label-blind 的 per-size Formocast benefit 分數已完整、可重現地產出；(ii) 在最濃的 aggregate-max reducer 下，26 個可檢定 gene 中 3 個帶有**穩定、寬裕通過 permutation／bootstrap 檢定的 per-gene marginal 訊號**；(iii) sealed guidance 建構在這 3 個 gene 上因固定 entropy floor 與 gene arity 的結構衝突而**不可完成**。

**不能：**guidance 指向真實高品質 config（`mu_gv` 是 non-causal、survivor-frame、Formocast-rank 的 conditional association，不是 causal gene effect、不是 real GFLOPS）；real ranking／prior mass／actual Gen0 效果（S12/S14）；跨 shape 複現（S30/S31）；unobserved candidate 是否 absent（stochastic non-discovery ≠ absence proof）。**「模型沒用」不是合格結論**（charter §8.5）；本次的稀疏結果已定位到 **marginal-loss** 層（§15）。物理 epistasis 歸因需 S12/oracle，S11 措辭不可寫「epistasis proven」。

---

## 2. Pipeline ＋ mechanism（sealed statistics）

### 2.1 三層 population：Fraw → Fexec → Fscore（design §6；QA-03 §0.2）

- **Fraw**：sampler 抽中且過 Ductile validator（`valid_fn`）的 raw occurrence multiset；duplicates 保留，accepted 後不因 resolver/generation/compile/score failure 從 raw mass 刪除。
- **Fexec**：在 Fraw 上再過 complete resolver projection、stable semantic identity、normal non-proxy KernelWriter generation、pinned `amdclang++` compile。value preservation 另在 trust gate 判，不是 Fexec membership 條件。
- **Fscore**：Formocast 對全部 3 個 locked sizes 都回傳 finite 正延遲。

**execution attrition**（進 Fraw、卡在 Fexec）記 `Y_exec = |Fexec|/|Fraw|`，**只回報、不 gate**，且**絕不**被當成「Formocast 沒有訊號」——工程層流失與模型缺值嚴格分離（S10R4 的教訓）。每個 semantic identity 恰有 producer ＋ fresh verifier 各一次 complete qualification。觀測值見 §9.2。

**3 個 locked size（`[CODE AUDIT]` sealed contract 釘死）：**`[8,8,1,128]`（tiny）、`[256,256,1,1024]`（medium）、`[2304,1024,1,214336]`（large）。「3 個 size」是決策的條件觀測，**不是** n=3 統計樣本數；真正的樣本數是 config 筆數。

### 2.2 Benefit、marginal `mu_gv`、factorization、guidance（sealed formulas）

```text
r_s(o)   = [W_<(L_s(o)) + 0.5*W_=(L_s(o))] / W
b_s(o)   = 1 - r_s(o)
benefit(o) = max_s { b_s(o) : every locked size s }        # sealed reducer = max
mu_gv    = (sum_b_gv + 32*global_mean_g) / (n_gv + 32)      # shrinkage alpha=32
S_g      = max_{v in T_g}(mu_gv) - min_{v in T_g}(mu_gv)
q_g(v)   = exp(lambda*(mu_gv - min_{u in T_g} mu_gu)) / Z,  v in T_g;  0 otherwise
p1_g(v)  = 0.20*p0_g(v) + 0.80*q_g(v)                       # epsilon = 0.20
```

`[CODE AUDIT]` sealed 位置（撰稿者直接在 `protocol/v1/s11/` 逐行核對）：

| 量 | file:line | 內容 |
| --- | --- | --- |
| per-size mid-ECDF benefit | `statistics.py:90` | `size_benefits = [1.0 - value for value in percentiles]` |
| 跨 size max reducer | `statistics.py:96`（另 `:138` 同式） | `"benefit": max(size_benefits)` |
| reducer 鎖死 | `statistics.py:62` | `raise StatisticsError("S11 actual size reducer must remain exactly max")` |
| shrinkage | `statistics.py:188` | `shrinkage_mean(..., alpha: int = 32)` |
| sensitivity | `statistics.py:1166` | `max(marginals.values()) - min(marginals.values())` |
| aggregate 方向 gate | `statistics.py:1359` | `size_direction(...)`（2-of-3 / 2-of-2） |
| **λ 選擇（阻塞點）** | `guidance.py:77–95` | `select_global_lambda(...)`；`:95` `assert chosen is not None and bundles is not None` |

locked constants（由 `derivation-manifest-capped.json.locked_constants` 獨立確認）：`alpha=32`、`epsilon=0.2`、`weight_beta=0.25`、`support_min_conditional_fraw=128`、`score_coverage_min=0.95`、`sensitivity_min=0.05`、`lambda_entropy_floor=0.8`。

**`mu_gv` 的意義：**「g=v 時、其他參數隨機下的平均 benefit」，帶 shrinkage `alpha=32`（先塞 32 筆等於全域平均的假樣本，避免小樣本偶然高分得極端權重）。global 與 conditional 分數 pool 成一個 multiset、每 occurrence 一票。`T_g` 只含 `support_gv>=128`、`|Dexec_gv|>=1`、unique value-preserving、`Cscore_occ_gv>=0.95` 與 complete statistics 的 values；untrusted values 不是 absent，精確保留 `0.20*p0>0`。lambda 從 grid {0,0.25,…,8}（33 點）取「所有 guided gene 都仍滿足 `H_norm>=0.80` 的最大值」，所有 guided gene 共用。

**抽樣 vs 評分正交（QA-03 §0.11）：**S11 內部**抽樣用 baseline `p0`（固定 seed PCG64），Formocast 只負責打分**；`p1` 是 S11 的**輸出**，不是內部抽樣機率。這保住「其他參數隨機」的邊際前提、避免 circularity、確保罕見值也有樣本。

### 2.3 七項 model-test AND-gate

| gate | 白話 | 門檻 |
| --- | --- | --- |
| `support_gv` | 該值 conditional 樣本數 | `>=128` |
| `Cscore_occ_gv` | 該值可評分覆蓋率 | `>=0.95` |
| `S_g`（sensitivity） | gene 內 best 值與 worst 值的 `mu` 差 | `>=0.05` |
| permutation test | own-null ＋ familywise max-null（各 2,000）| observed `S_g` **strict** > 兩者 P95（ties fail）|
| bootstrap stability | best/worst 排名穩定 | CI 半寬 `<=0.025` **且** recurrence `>=0.90` |
| size direction | 3 個 size 方向一致 | `>=2/3` |
| entropy floor | 引導後分布不塌成獨尊一值 | normalized entropy `>=0.80` |

**關鍵區別（本次結果的樞紐）：**前六道是 **per-gene 證據 gate**，在 `_frame_analysis` 內逐 gene 判；第七道 entropy floor **不是 per-gene 篩選**，而是在 `select_global_lambda` 內作為**跨 gene 共用 λ 的可行性條件**。因此「某 gene 太集中」不會只淘汰那個 gene，而是**讓整個 λ 選擇失敗**（§9.5）。P95 用 Hyndman–Fan Type-7（`n=2,000` → `0.95*x_(1900)+0.05*x_(1901)`）。

### 2.4 七個正式階段與實際到達狀態

`global-discovery → conditional-discovery → qualify → score → analyze → decide → reproduce`，嚴格單向，每階段只讀前一階段封好的產物、只寫自己那份，都要過 `admit_formal_command` 授權。

**`[CODE AUDIT]` 撰稿時 `protocol/v1/manifests/` 與 `protocol/v1/evidence/` 的實際目錄清單：**

| stage | 產物 | 狀態 |
| --- | --- | --- |
| （pre-draw） | `s11-registry.json`、`s11-structural-registry.json`、`s11-implementation.json`、`s11-workload-envelope.json` | **PRESENT** |
| global-discovery | `s11-global-prefix.json` | **PRESENT**（complete） |
| conditional-discovery | `s11-conditional-prefixes.json` | **PRESENT**（`activation_complete: true`） |
| qualify | `s11-qualifications.json` | **PRESENT**（30,802 records） |
| score | `s11-native-scores.json` | **PRESENT**（30,490 records）← **S11 對下游的實際交付物** |
| analyze | `s11-analysis.json`、`s11-guidance.json` | **NOT PRODUCIBLE**（§9.3） |
| decide | `evidence/s11-decision.json` | **NOT PRODUCIBLE**（缺 analyze 輸入） |
| reproduce | `evidence/s11-reproduction.json` | **NOT PRODUCIBLE**（缺 decide 輸入） |
| positive-only | `evidence/gate-records/s11-s1-guidance-locked.json` | **NOT PRODUCIBLE**（positive 分支不可到達） |

### 2.5 §6.4 categorical decision projection（`S11-DIRECTION-METRICFRAME-20260804`）

兩個固定 4,096 halves 是 **disjoint** global occurrence samples；逐位相等於 half-specific 數值 cells 與 float-probability hash 結構上不可達。current 判準：(1) 同一 half replay 要 byte-exact；(2) 兩 disjoint halves 之間只對一個預先列舉的 **categorical decision projection** 要求 exact 相同；(3) half-specific 數值與 float guidance probabilities 是 reported numeric drift，**不 gate**；(4) authoritative guidance hash 只對 terminal full 8,192-occurrence bundle 計算一次；(5) half-stability 取決於該 categorical projection 失敗，非 numeric drift。

**狀態：**此 projection 由 `analyze` 產出，故 **NOT PRODUCIBLE**（§9.6）。

---

## 3. Design 與 pre-registration：fixed-frame ＋ no-optional-stopping

S11 統計正當性建立在**先驗鎖定、事後不可改**的固定 schedule（contract `schedule`/`fixed_frame_analysis`；design §6）：

- **Global inferential frame** 固定 canonical first-**8,192** accepted occurrences；first-4,096 與兩固定 halves 只 read-only。硬上限 **65,536** 個 512-slot chunks ＝ **33,554,432** nominal draws。`target_stop`/`early_stop`/`extension`/`cap_extension` 全 `forbidden`。cap 時取不到 8,192 accepts 即 `FT-INCONCLUSIVE`，禁 reseed/pooling。
- **每 activated conditional value** 固定 **512** chunks ＝ **262,144** draws、target first-**256** accepts；first-128 只 read-only；少於 128 是 support-insufficient。同樣禁 reseed/extension/pooling。
- **Canonical prefix rule**：分析只用 canonical first-8,192／first-256 prefix；之後的 later accepts 是 `append_only_zero_credit_diagnostic`（`boundary_overshoot_credit: 0`）。
- **Registry** 事先凍結：eligible residual gene = **27**、activated conditional value = **101**；`model_ranked_screen: forbidden`，candidate order = actual YAML order。
- **Seed** fresh、與所有 prior checkpoint disjoint 的 PCG64 master nonce `40e06e51…b189c97`，`reseed: forbidden`。

Planning calculation（固定式；historical rows 對 S11 criterion credit 為零）：

```text
p_plan = 114 / 262,144 = 57 / 131,072 ~= 0.00043487548828125
draws_for_8192 = 8,192 / p_plan ~= 18,837,575.85964912
chunks_for_8192 ~= 36,792.14035087719
margin_chunks = 1.5 * chunks_for_8192 ~= 55,188.21052631579
global_cap_chunks = next_power_of_two(margin_chunks) = 65,536
global_cap_draws = 65,536 * 512 = 33,554,432
```

**這個固定 schedule 後來成為阻塞的必要條件之一**——它同時決定了每個 conditional value 只能有 262,144 次 draw 的機會，而這正是高基數 gene 只拿到 2 個 trusted value 的直接原因（§9.5.2）。這是**設計取捨的誠實紀錄，不是事後歸咎**：固定 frame 換來的是「取樣量」與「觀測效果」正交（避免 optional stopping 的 implicit multiple testing），代價是罕見 candidate value 的 support 完全由 validator 的接受率決定、無法補抽。

---

## 4. Validity 與 controls（design §5–§6；QA-03 §0.7/§0.9）

- Trust/mapping/coverage 先凍結 `Gtest`（final testable gene set frozen before `S_g` observed）。2,000 block bootstraps 重建 ECDF/statistics；2,000 permutation replicates（每 replicate 一份 shared-global occurrence permutation；conditional 每 gene pool 恰一份 independently domain-separated permutation，依 fixed observed cell counts 分配；禁 per-conditional-cell permutation）。
- `bias_diagnostics`/`validity_diagnostics` 為 mandatory-compute、原則 report-only，唯一例外是 OPTION_C（§6）。
- same-entropy non-identity shuffle 另作 control（preserves untrusted mass、complete p1 multiset、nominal entropy、candidate order）。

**這些 control 實際上都完整跑完了**：2,000 permutation replicates ＋ 26 個 per-gene bootstrap pass 的結果全部存在於 `parallel-analyze/out/passes.w72.json`（§9.4），且每 replicate 對 sealed O(N²) oracle 逐 bit 相同（§9.3(a)）。**失敗發生在這些 control 之後**——不是 control 沒跑，是 control 通過之後的建構步驟不可行。

**2026-08-04 approved amendments（只改 design/治理措辭，未執行 S11 evidence）：**`S11-DIRECTION-METRICFRAME-20260804`（entry via administrative prerequisite、§2.5 categorical-projection 最小修正、workload-envelope materialize＋branch-stop）與 `S11-METRIC-BIAS-20260804`（四族 label-blind 診斷 additive-rank/emitted-prior/arm-sensitivity/per-size margin，NON-gating、claim-wording-bound；`mu_gv` 為 non-causal conditional association 的 crux；6 項 bias 措施；第 5 項使用者裁決 shrinkage alpha=0 decision-flip gate「先做 decision-loss simulation」）。兩線 reviewers `AGREE/AGREE`。

---

## 5. Coverage／support 與 value-space coverage

Positive 需 `|Uexec_global| >= 256`（unique semantic identities from `Fexec_global` only）；`<256` 直接 `FT-INCONCLUSIVE`。coverage `C_score_occ_global >= 0.95`；per-value trust `Cscore_occ_gv >= 0.95`。value-space：27 eligible residual genes、101 activated conditional values；每 activated value target canonical first-256 accepts，<128 為 support-insufficient。

**觀測值（§9.2）：這兩道門檻都以極大餘裕通過**——`|Uexec_global| = 8,098`（門檻 256，約 31.6×）、global 執行良率 98.85%、可評分覆蓋率 100.0%。**S11 沒有任何 support／coverage 問題。**

---

## 6. Decision-loss simulation 與 OPTION_C shrinkage-robustness gate

BIAS 線第 5 項使用者裁決：先做 prospective label-blind decision-loss simulation（比較 alpha=0 vs alpha=32 的 ordering error）再定 shrinkage decision-flip 是否 gate。依 `OPTION_C_GATE_FLIP`：逐 gene 的 alpha=0 `alpha0_decision_flip` 為 **guided eligibility gate**；若**全部** otherwise-guided gene 皆 decision-flip，整個 S11 判 `FT-INCONCLUSIVE`。

**狀態：NOT PRODUCIBLE。**`[CODE AUDIT]` alpha=0 的兩個 heavyweight pass（`alpha0_joint_permutation_test`、`alpha0_bootstrap_stability`）屬於 `_frame_analysis` **在 λ 選擇之後**才到達的 frame；parallel 重現的 `passes.w72.json` 只含 27 個 entry（1 permutation pass ＋ 26 per-gene bootstrap pass），**alpha0 的兩個 pass 從未被 sealed workflow 請求過**（`VERIFICATION.md` §3 明載）。因此 `alpha0_decision_flip`、alpha0-robust guided count、以及 decision-loss ordering error **都不存在也無法產生**。**這不表示 shrinkage 穩健或不穩健——它是 `not_evaluated`。**

---

## 7. Reproducibility 與 governance

- **Sealed contract**：`protocol/v1/s11-stage1-model-only-factorization-contract.yaml`，`status: frozen_preimplementation`；base_commit `b7f06476…`。
- **Effective lock**：`protocol/v1/locks/s11-stage1-model-only-factorization-lock.json`，`state: LOCKED_READY`，`lock_sha256: 45e77ab4ba8b931aeb929cd1b1a650fb92d3ada6a80830394eecd3d92d7e0321`（schema_version 3）。綁定 pinned toolchain（`amdclang++` AMD clang 22.0.0git roc-7.2.4；`compiler_sha256 ef3c9a02…`）、native helper、qualification worker、fresh disjoint seed、27/101 registry、global 65,536-chunk 與 per-value 512-chunk schedule。
- **Sealed tree 完整性**：`git status --porcelain -- protocol/v1/s11/` 與 `git diff --stat HEAD -- protocol/v1/s11/` 皆為**空**；32 個檔案，全部 `*.py` 之 per-file sha256 排序清單的 sha256 ＝ `1b1be01c982ee72d997ae124d1db61fc827b81c5fc348d5c97b646289c8c9d67`；`git ls-files -s` digest ＝ `34bfa5cb329453054fd56873549dc98c79b0c811478dccf9543bd84737e9dbb0`（`parallel-analyze/VERIFICATION.md` §4）。**沒有任何 sealed code 被修改；阻塞是被 reported，不是被 patched。**
- **Reproduce**：`verify-lock` 仍可執行；但 `evidence/s11-reproduction.json` 需要 `decide` 的產物作為 replay 對象，故 **NOT PRODUCIBLE**。
- **Never-push policy**：本報告與所有 S11 artifacts 一律不 push；本報告不預填自己的 closure commit SHA。

---

## 8. Study modes 與 label firewall

`forbid_real_gflops`／`forbid_s12_d5_labels`／`forbid_gpu_correctness`／`prelabel_absence_required` 原由 fresh verifier PB-S11-V2-C10 於 `decide` 階段稽核並寫入 `evidence/s11-decision.json`。**該 attestation NOT PRODUCIBLE。**

**可獨立陳述的事實（`[CODE AUDIT]`）：**S11 全部已完成階段的輸入只有 sealed registry ＋ sampler ＋ Formocast native helper；`s11-native-scores.json` 的 `native_result.provenance.argv` 指向 sealed native build `s11-native-formocast`，其輸出僅含 `predicted_latency`／`problem_size`／build provenance，**不含任何 real GFLOPS 欄位**；out-of-band parallel 重現亦僅讀取上述 5 個 sealed manifest，**無 GPU、無 S12/D5 label**（`VERIFICATION.md` 首段）。這**不能取代**正式 attestation，只是說明目前沒有已知的 leakage 事證。

---

## 9. Results — S11 實際產出什麼、以及什麼永遠不會產出

> **本節不含任何 placeholder。**每一列若非 verified 觀測值，就明確標 `NOT_PRODUCIBLE` 並給出原因。所有數字由撰稿者直接自 primary artifact 讀取／重算（來源逐列標明）。

### 9.0 一頁摘要

| 面向 | 結果 |
| --- | --- |
| 抽樣 schedule 是否照 pre-registration 完成 | **是**（global 打滿 65,536 chunks；101 條 conditional 各 512 chunks） |
| 是否取得 8,192 credited global accepts | **是**（`accepted_credited = 8192`；`cap_complete = true`） |
| support／coverage／`|Uexec|` 門檻 | **全部大幅通過**（§9.2） |
| 是否有可用的 per-gene 模型訊號 | **有，但極稀疏**：26 個可檢定 gene 中 **3 個**通過全部七道 gate，邊際 1.79×–11.86× |
| sealed guidance 是否能建構 | **否**——`select_global_lambda` 在 `guidance.py:95` 確定性 assert |
| 原因 | 固定 `H_norm>=0.80` floor 對 `(n_candidates, k_trusted)` 低基數 gene **數學上不可達**（§9.5） |
| 是否 parallel 實作缺陷 | **否**——determination **(A) FAITHFUL**，四軸驗證（§9.3） |
| S11 formal outcome | `not_evaluated`；`S1_GUIDANCE_LOCKED` **NOT EVALUABLE**（§9.7） |
| S11 對研究線的實際交付 | `s11-native-scores.json`（per-size 分數）＋ 由它導出、獨立驗證並 **Lock B SEALED** 的 per-shape capped guidance（§11、§12） |

### 9.1 Registry 與 schedule parity（`[CODE AUDIT]`，全部 VERIFIED）

| 項目 | 觀測值 | 來源 |
| --- | --- | --- |
| eligible residual genes | **27**（`eligible_genes` 長度 27；另 `ineligible_free_genes` 3、`protected_groups` 3） | `manifests/s11-registry.json` |
| activated conditional values | **101**（`conditional_streams` 長度 101） | 同上 |
| registry 綁定 | `actual_reducer: max`、`soo: false`、`weight_beta: 0.25`、`problem_sizes` 3 個、`lock_sha256` 相符 | 同上 |
| global target / credited accepts | target **8,192** / credited **8,192**、`complete: true`、`cap_complete: true` | `manifests/s11-global-prefix.json` |
| global chunks / nominal draws | `chunks_observed = 65,536`＝`hard_cap_chunks`；`complete_nominal_draws = 33,554,432` | 同上 |
| global observed accepts（含 zero-credit tail） | `accepted_observed = 90,359`；`zero_credit_occurrence_count = 82,167`（＝ overshoot diagnostic） | 同上 |
| conditional schedule | 101 streams，**每條 `chunks_observed = 512`**（＝262,144 draws），無任何 extension | `manifests/s11-conditional-prefixes.json`（`activation_complete: true`） |
| conditional accepts | **88/101 達到 target 256**；**13 條 <128（support-insufficient）** | 同上 |

**根因分析（為何 global 打滿 cap 仍是「照計畫」）：**pre-registered `p_plan = 114/262,144 ≈ 4.35e-4` 只是保守的 planning 假設；實測 acceptance rate 為 `90,359 / 33,554,432 ≈ 2.69e-3`，約為計畫值的 **6.2×**。因此 8,192 個 credited accepts 遠早於 cap 就達成，其餘 82,167 個 accepts 依 canonical prefix rule 全部記為 **zero-credit diagnostic**。這正是固定 schedule 的預期行為（`early_stop: forbidden`），**不是** overshoot 缺陷：credited frame 仍嚴格是 canonical first-8,192。

**13 條 support-insufficient stream 的逐條紀錄（`[CODE AUDIT]`，這是 §9.5 的關鍵前提）：**

| gene | 該 gene 的 candidate 總數 | 各 stream 的 `accepted_credited` | 達 `>=128` 者（＝`T_g`） |
| --- | --- | --- | --- |
| **DepthU** | 6 | 256, 256, **38, 0, 0, 0** | **2** |
| **PrefetchGlobalRead** | 4 | 256, 256, **2, 0** | **2** |
| GlobalReadVectorWidthA | 7 | 256×4, **2, 0, 0** | 4 |
| GlobalReadVectorWidthB | 7 | 256×4, **0, 0, 0** | 4 |
| **DirectToVgprA** | 2 | 256, **40** | **1** → 不可檢定 |
| （其餘 22 gene） | 2–18 | 全部 256 | ＝ candidate 數 |

**根因：**這 13 條 stream 不是「覆蓋率不足」也不是「評分失敗」，而是**在 262,144 次 draw 內，validator（`valid_fn`）幾乎／完全不接受該 candidate value 與被抽到的 group_0（MatrixInstruction/WorkGroup/MacroTile）組合**——例如 `DepthU` 的四個高值在固定 baseline `p0` 下與絕大多數 MacroTile 不相容，直接得到 0 個 accept。`support_min=128` 與固定 512-chunk schedule 兩者相乘，決定了「高基數 gene 只會留下 2 個 trusted value」這個結構事實。**這一點在 §9.5 直接導致 entropy floor 不可達。**

### 9.2 Population counts（`[CODE AUDIT]`，全部 VERIFIED）

| 量 | 觀測值 | 計算/來源 |
| --- | --- | --- |
| qualification records（unique semantic identities） | **30,802** | `manifests/s11-qualifications.json` `qualification_records` |
| two-attempt parity | `attempt_count == 2` 對全部 30,802 筆成立；`exactly_two_complete_attempts_enforced: true`；`producer_and_fresh_verifier_roots_separate: true` | 同上 |
| producer vs fresh-verifier fingerprint 一致 | **30,802 / 30,802（100%）** `qualification_fingerprint` 完全相同；兩者 result 分佈亦完全相同 | 撰稿者逐筆比對 |
| Fexec（accepted） | **30,490**（reason `complete_normal_generation_and_compile`） | 同上 |
| 執行流失 | **312**（reason **`normal_kernelwriter_reject`**，唯一的 reject reason；佔 1.01%） | 同上 |
| Fscore | **30,490** score records，`all_locked_sizes_required: true`（三個 size 全數有值） | `manifests/s11-native-scores.json` |
| **canonical global frame 上的 `Y_exec`** | **8,098 / 8,192 = 0.98853** | 撰稿者以 `credited_occurrence_ids` 交集 score records 重算 |
| **canonical global frame 上的 `C_score_occ`** | **8,098 / 8,098 = 1.0000**（≥0.95 ✓） | 同上 |
| **`|Uexec_global|`** | **8,098**（門檻 256；約 **31.6×** 餘裕） | 同上 |

**`[MODEL-ONLY]` 誠實註記：**上列 `Y_exec` / `C_score_occ` / `|Uexec_global|` 是**撰稿者自 sealed manifests 重算**的值；sealed `analyze` **從未 emit** 這些欄位（`s11-analysis.json` 不存在）。重算方法完全依 §2.1 的定義，但它**不是** sealed pipeline 的 attested 輸出，因此**不得**被引用為 gate 判定。

**根因分析（流失是工程層、不是模型層）：**312 筆流失**全部**是 `normal_kernelwriter_reject`——即 KernelWriter 在正常（非 proxy）路徑上拒絕生成，屬於 Ductile/Tensile 自身的合法性判斷，與 Formocast 是否有訊號**完全無關**。沒有任何一筆是 compile timeout、resolver 不完整或 scoring 失敗。這正是 S10R4 教訓要求嚴格分離的兩件事，本次資料支持該分離：**工程流失 1.01%，模型評分覆蓋 100%。**

### 9.3 阻塞發現：sealed `analyze` 的 `AssertionError`（determination **(A) FAITHFUL**）

**事實（`[CODE AUDIT]`，`agent_run/260803-ductile-factorized-guidance-s11/parallel-analyze/VERIFICATION.md`）：**sealed `analyze` 在 `protocol/v1/s11/guidance.py:95` 的

```python
assert chosen is not None and bundles is not None
```

確定性終止，因為 **sealed grid {0, 0.25, …, 8.0}（33 點）中不存在任何 λ 能讓每個 guided gene 都維持 `H_norm >= 0.80`**。

**這不是 parallel 實作的缺陷。**out-of-band parallel 重現（只做兩項 in-memory 替換：四個 heavyweight replicate loop 改為跨 process 分塊＋依 replicate index 原序併回；`query_terminal_global_ecdf` 換成同輸出的向量化版本；**不寫入任何 sealed 檔**）以四軸驗證：

| 軸 | 驗證內容 | 結果 |
| --- | --- | --- |
| **(a)** per-replicate bit-equality | 對 sealed O(N²) oracle，4 個 stochastic pass 各抽樣 replicate index，workers=1/3/7；每個 double 以 `float.hex()` 比對（非 tolerance） | **0 failures**；`returned_dict_sha_equal = True` |
| **(b)** partition independence | w40 vs w72 的 `passes.<tag>.json` | **byte-identical**（22,999 bytes，sha256 `d7371242985190b3a94d5112afcba8923fac236d42b3afbe10805ec0521df0ce`；撰稿者重算兩檔 sha256 確認相同）。40 與 72 互不整除且皆不整除 2,000，chunk 邊界確實不同 |
| **(c)** sealed tree unchanged | `git status --porcelain` / `git diff --stat` 對 `protocol/v1/s11/` | **皆空**（§7） |
| **(d) §5.4 決定性測試** | 以 `PA_SEALED_ECDF=1` 完全關閉 fast-ECDF 替換，用 **sealed** `query_terminal_global_ecdf` 重跑整段 deterministic prefix | `guidance_inputs`（sha `11d93fbb…`）、完整 λ×entropy `calls`（sha `e68884a9…`）、`gate_calls`（7 gates × 26 genes，sha `bf53f99c…`）**全部 True／完全相同**；終止狀態兩邊皆 `ASSERTION at call #1` |

⇒ **determination (A) FAITHFUL。**sealed serial `analyze` 在耗時數日後只會撞上**同一個** assertion。parallel 版的價值是把「這條路走不通」從數日縮到 **156.7 s**（w72 compute；端到端 222.3 s），對照 sealed serial 的 oracle 量測（3 個 permutation replicate 就要 1,085 s）。

**治理紀律：**依指示**只回報、不修補**——沒有套用任何 workaround，sealed tree 未動（§7）。是否退役仍在跑的 serial `analyze`，是 owner 的 protocol 決策。

**撰稿者獨立確認的欄位（直接讀 `out/diag-lambda2.w72.json`）：**`status = "ASSERTION at call #1"`、`lock_sha256 = 45e77ab4…`（與 effective lock 相符）、`calls` 長度 1、`guidance_inputs` 3 個 gene、`gate_calls` 26 筆、`entropy_min = 0.8`。

### 9.4 26-gene aggregate-max gate table（**S11 唯一的 sealed 統計結果**，`[MODEL-ONLY]`）

**這是 S11 在 sealed max-reducer frame 下實際算出來的完整 per-gene 檢定結果**，取自 `parallel-analyze/out/diag-lambda2.w72.json` 的 `gate_calls`（26 筆，經 §9.3(d) 證實與 fully-sealed 路徑 bit-identical）。gene 名稱由撰稿者以 `best`/`worst` candidate hash 對 `derivation-manifest-capped.json` 的 `per_shape_activation_log` 反查得到。

`familywise_max_null_p95_type7 = 0.029970398096592576`（26 個 gene 共用同一個 max-null 分布，數值一致）。

| # | gene | `|T_g|` | `S_g`（floor 0.05） | own-null P95 | `S/own` | `S/familywise` | bootstrap CI 半寬（≤0.025） | best/worst recurrence（≥0.90） | direction | **七道全過** |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 1 | **PrefetchGlobalRead** | 2 | **0.094190** | 0.008857 | **10.63×** | **3.14×** | 0.006645 | **1.000** | ✔ | **是** |
| 2 | **UnrollLoopSwapGlobalReadOrder** | 2 | **0.090004** | 0.007588 | **11.86×** | **3.00×** | 0.006784 | **1.000** | ✔ | **是** |
| 3 | **DepthU** | 2 | **0.053698** | 0.009632 | **5.58×** | **1.79×** | 0.008728 | **1.000** | ✔ | **是** |
| 4 | GlobalReadVectorWidthB | 4 | 0.031064 | 0.013147 | 2.36× | 1.04× | 0.010533 | 0.544 | ✔ | 否（`S_g`、recurrence） |
| 5 | GlobalReadVectorWidthA | 4 | 0.027110 | 0.013052 | 2.08× | 0.90× | 0.010379 | 0.698 | ✔ | 否（`S_g`、recurrence、familywise） |
| 6 | 1LDSBuffer | 2 | 0.021046 | 0.007833 | 2.69× | 0.70× | 0.007622 | 1.000 | ✘ | 否（`S_g`、direction、familywise） |
| 7 | WorkGroupMapping | 18 | 0.020231 | 0.029970 | 0.68× | 0.68× | 0.016816 | 0.151 | ✔ | 否（4 道） |
| 8 | TransposeLDS | 4 | 0.016453 | 0.012955 | 1.27× | 0.55× | 0.009953 | 0.467 | ✘ | 否（4 道） |
| 9 | NumElementsPerBatchStore | 8 | 0.014466 | 0.019937 | 0.73× | 0.48× | 0.012891 | 0.294 | ✔ | 否（4 道） |
| 10 | StoreSyncOpt | 3 | 0.010569 | 0.010134 | 1.04× | 0.35× | 0.008560 | 0.576 | ✔ | 否（3 道） |
| 11 | SourceSwap | 2 | 0.010289 | 0.006919 | 1.49× | 0.34× | 0.007292 | 0.999 | ✔ | 否（`S_g`、familywise） |
| 12 | StaggerU | 3 | 0.009538 | 0.010079 | 0.95× | 0.32× | 0.008859 | 0.714 | ✔ | 否（4 道） |
| 13 | WorkGroupMappingXCC | 5 | 0.009125 | 0.014707 | 0.62× | 0.30× | 0.010726 | 0.223 | ✘ | 否（5 道） |
| 14 | NonTemporalD | 2 | 0.006415 | 0.007472 | 0.86× | 0.21× | 0.007160 | 0.957 | ✔ | 否（3 道） |
| 15 | WaveSeparateGlobalReadA | 2 | 0.006320 | 0.007354 | 0.86× | 0.21× | 0.007327 | 0.954 | ✔ | 否（3 道） |
| 16 | StaggerUStride | 4 | 0.005937 | 0.013090 | 0.45× | 0.20× | 0.009764 | 0.285 | ✔ | 否（4 道） |
| 17 | TailloopInNll | 2 | 0.005646 | 0.007137 | 0.79× | 0.19× | 0.007306 | 0.940 | ✔ | 否（3 道） |
| 18 | WaveSeparateGlobalReadB | 2 | 0.004406 | 0.007099 | 0.62× | 0.15× | 0.007428 | 0.891 | ✔ | 否（4 道） |
| 19 | MIArchVgpr | 2 | 0.004342 | 0.007232 | 0.60× | 0.14× | 0.007205 | 0.892 | ✔ | 否（4 道） |
| 20 | ExtraMiLatencyLeft | 2 | 0.003474 | 0.007161 | 0.49× | 0.12× | 0.007122 | 0.839 | ✘ | 否（5 道） |
| 21 | NonTemporalA | 2 | 0.003308 | 0.006913 | 0.48× | 0.11× | 0.006990 | 0.819 | ✘ | 否（5 道） |
| 22 | ScheduleGROverBarrier | 2 | 0.002374 | 0.007170 | 0.33× | 0.08× | 0.007391 | 0.747 | ✔ | 否（4 道） |
| 23 | NonTemporalC | 2 | 0.001267 | 0.007171 | 0.18× | 0.04× | 0.007102 | 0.639 | ✔ | 否（4 道） |
| 24 | NonTemporalB | 2 | 0.000768 | 0.007276 | 0.11× | 0.03× | 0.007253 | 0.582 | ✔ | 否（4 道） |
| 25 | AdaptiveGemm | 2 | 0.000611 | 0.006962 | 0.09× | 0.02× | 0.007181 | 0.569 | ✘ | 否（5 道） |
| 26 | StorePriorityOpt | 2 | 0.000297 | 0.006903 | 0.04× | 0.01× | 0.007261 | 0.525 | ✘ | 否（5 道） |
| — | **DirectToVgprA** | **1** | — | — | — | — | — | — | — | **不可檢定**（`|T_g|=1`） |

**讀法與根因分析：**

1. **訊號是雙峰的，不是連續遞減的。**通過門檻的 3 個 gene 的 `S_g` 是 0.054–0.094；第 4 名 `GlobalReadVectorWidthB` 只有 0.031，第 7 名以後全部 `<0.021`，最後 10 名在 `0.0003–0.0064`（即 best 值與 worst 值在預測延遲排名上只差 **0.03–0.6 個百分位點**）。**這不是「門檻訂太高」——把 `S_g` 門檻放寬到 0.025 只會多納入 `GlobalReadVectorWidthB`（0.0311，recurrence **0.544**）與 `GlobalReadVectorWidthA`（0.0271，recurrence **0.698**），兩者都遠低於 recurrence 門檻 0.90，會立刻被 bootstrap gate 擋掉。**訊號與雜訊之間有真實的間隙。
2. **`recurrence` 與 `S_g` 高度共變，且高基數 gene 系統性偏低。**`WorkGroupMapping`（18 個 trusted value）recurrence 只有 0.151、`StaggerUStride`（4 個）0.285、`NumElementsPerBatchStore`（8 個）0.294。**根因：**`S_g` 定義為 `max_v mu - min_v mu`，是**極值統計**；trusted value 愈多，best/worst 的身分愈容易在 bootstrap 重抽下換人，即使 `S_g` 的量值穩定。這是 estimand 本身的性質，**不是**這些 gene「沒有效果」——它是「哪個 value 最好」這個問題在此樣本量下無法穩定回答。三個通過者的 recurrence 全是 **1.000**，因為它們都只有 2 個 trusted value（best/worst 身分無從變動）。**這個耦合值得記錄：能通過 recurrence gate 的，結構上偏向低基數 gene——而低基數 gene 正是 entropy floor 打不過的那些（§9.5）。兩道 gate 的偏好方向剛好相反。**
3. **familywise gate 才是真正的緊箍咒。**shared max-null P95 = 0.02997，比多數 own-null P95（0.0069–0.0300）高出一個量級。撰稿者逐 gene 統計：**own-null strict pass 的有 9 個**（DepthU、1LDSBuffer、PrefetchGlobalRead、SourceSwap、StoreSyncOpt、TransposeLDS、UnrollLoopSwapGlobalReadOrder、GlobalReadVectorWidthA、GlobalReadVectorWidthB），**familywise strict pass 的只剩 4 個**（DepthU、PrefetchGlobalRead、UnrollLoopSwapGlobalReadOrder、GlobalReadVectorWidthB）。⇒ **多重比較校正單獨淘汰了 5 個 gene**（1LDSBuffer、SourceSwap、StoreSyncOpt、TransposeLDS、GlobalReadVectorWidthA）。這是 pre-registered 嚴格性生效的證據，不是缺陷。（`GlobalReadVectorWidthB` 兩道 null 都過，最後卡在 `S_g` 與 recurrence。）
4. **direction gate 淘汰了 7 個 gene**（`1LDSBuffer`、`TransposeLDS`、`WorkGroupMappingXCC`、`ExtraMiLatencyLeft`、`NonTemporalA`、`AdaptiveGemm`、`StorePriorityOpt`），亦即它們在 aggregate 2-of-3 size 上方向不一致。**這與 §13 的 per-shape 表互相印證**：`1LDSBuffer` 在 medium 的 `S_g=0.113`、`TransposeLDS` 在 large 的 `S_g=0.057` 都相當強，但 max-reducer 把它們的 shape-specific 方向抹平成不一致——這正是 §10 建構效度問題的 per-gene 證據。

### 9.5 為何 sealed guidance 建構不下去：`(n, k)` 與固定 entropy floor 的結構衝突

#### 9.5.1 λ 選擇的實際輸入與 λ×entropy 曲線（`[CODE AUDIT]`，`out/diag-lambda2.w72.json`）

進入 `select_global_lambda` 的 `guidance_inputs` 恰為 §9.4 的 3 個通過者。撰稿者逐一讀取其 33 點 `entropy_by_lambda` 曲線：

| gene | `n_candidates` | `k_trusted` | baseline `p0` | argmax λ | **該 λ 下的 `H_norm`** | `>= 0.80`？ | 全 grid 上的 sup | 對**所有**嚴格正 baseline 取 sup |
| --- | ---: | ---: | --- | ---: | ---: | :---: | ---: | ---: |
| **DepthU** | 6 | 2 | uniform 1/6 | **0.00** | **0.657588974** | **否** | 0.657588974 | **0.743503279**（仍 < 0.80；`structurally_impossible: true`） |
| **PrefetchGlobalRead** | 4 | 2 | uniform 1/4 | **0.00** | **0.734497797** | **否** | 0.734497797 | 0.860964047（`structurally_impossible: false`） |
| UnrollLoopSwapGlobalReadOrder | 2 | 2 | uniform 1/2 | 0.00 | **1.000000000** | 是 | 1.0 | 1.0 |

**三條曲線在 λ 上皆單調遞減**（撰稿者確認 DepthU 由 0.657589 降到 0.648307、PGR 由 0.734498 降到 0.700687、ULSGRO 由 1.0 降到 0.944256）。因此 argmax 一律在 λ=0，且 **λ=0 的值就是全 grid 的上界**——沒有任何 λ 可以救。

#### 9.5.2 根因（兩段式，缺一不可）

**第一段：為什麼 `k=2`。**§9.1 的 stream 表已給出直接證據——`DepthU` 的 6 個 candidate 中 4 個在 262,144 次 draw 內只拿到 38/0/0/0 個 accept；`PrefetchGlobalRead` 的 4 個中 2 個只拿到 2/0。`support_min=128` 於是把它們判為 untrusted。**這不是覆蓋率或評分問題，是 validator 在固定 baseline `p0` 下的組合可行性問題**（高 `DepthU` 與大多數 MacroTile 不相容）。固定 512-chunk schedule 禁止補抽（`extension: forbidden`），所以 `k=2` 是這個 pre-registration 下的必然結果。

**第二段：為什麼 `k=2` ＋ uniform baseline ⇒ `H_norm` 有硬上界。**sealed 建構是 `p1 = 0.20*p0 + 0.80*q`，其中 `q` 只在 `k` 個 trusted candidate 上有質量。在 uniform baseline（`p0 = 1/n`）下，`p1` 最分散的情形出現在 `q` 也 uniform（即 λ=0），此時

```text
untrusted slot : p1 = 0.2/n                      （共 n-k 個）
trusted   slot : p1 = 0.2/n + 0.8/k              （共 k 個）
H_norm_max(n,k) = H(p1) / log(n)
```

代入即得 `(n=6,k=2) → 0.6576`、`(n=4,k=2) → 0.7345`——**與觀測值到小數第七位完全一致**。這是 `parallel-analyze/logs/marginal-independence.log` 用 2,103 個 marginal 向量（observed、equal-marginals、101 點 2-simplex 掃描、2,000 個 uniform 隨機抽樣）× 33 個 λ 掃出的 supremum 所獨立確認的：**observed entropy 就是 supremum**。

**第三段（精確界線，本報告刻意比既有摘要更嚴謹）：**兩個 gene 的「不可達」強度**不同**，不可混為一談：

- **DepthU (6,2)：**即使放寬到**所有**嚴格正 baseline，sup 仍只有 **0.7435 < 0.80** ⇒ `structurally_impossible = true`。**任何資料、任何 λ、任何 baseline 都不可能滿足 0.80。**
- **PrefetchGlobalRead (4,2)：**對所有嚴格正 baseline 取 sup 為 **0.8610 > 0.80** ⇒ `structurally_impossible = false`。它的不可達性是**相對於 sealed registry 所釘死的 uniform baseline (0.25,0.25,0.25,0.25)** 而言的（此時 sup = 0.7345）。換言之，PGR 的阻塞是「sealed baseline ＋ 固定 0.80 floor」的聯合結果，不是純粹的 arity 定理。

**第四段：為什麼移除 DepthU 也救不了。**`VERIFICATION.md` §5.3 指出並經 §9.4 的表確認：**單靠 `PrefetchGlobalRead` 一個 gene 就足以觸發 assert**——它以 `S_g` 超標 **+88.4%**、每道 stochastic gate 皆 ≥3× 邊際通過，是最不可能被質疑的 guided gene，而它單獨把可達 `H_norm` 壓在 0.7345。因此這不是「邊緣 gene 拖累」——**證據最強的 gene 才是阻塞源**。

#### 9.5.3 可轉移的設計教訓（`[CODE AUDIT]`，非 protocol 變更）

固定的 `H_norm >= 0.80` floor **把兩件不同的事混為一談**：

- 它想表達的是「**保留 Gen0 探索多樣性**」（一個關於分布集中度的意圖）；
- 它實際施加的是「**這個 gene 必須有足夠多的 trusted candidate**」（一個關於 `k/n` 的隱含結構要求）。

因為 `H_norm_max` 只是 `(n,k)` 的函數，一個固定 floor 等於**在任何資料、任何證據強度下，無條件禁止引導某些 arity 的 gene**。兩條合理修法：(i) 把 floor 表述為**相對於該 gene 自身可達上界**的比例；(ii) **cap 混合強度而非排除 gene**——後者正是 `ENTROPY-CAP-20260810`（§11.2）。

**這一點的獨立驗證價值：**`ENTROPY-CAP` 是在 **per-shape** 路徑上設計的；本次是在**未修改的 sealed pipeline、不同的 reducer（aggregate max）**上重現了**同一個結構性失效**。因此該修正**修的是一個真實且一般性的缺陷，不是一個方便的障礙**（沒有 gate-shopping）。

### 9.6 NOT PRODUCIBLE 清單（明確、逐項、附原因）

> 以下每一項在舊 DRAFT-SCAFFOLD 中都是 `⟨TBD@closeout⟩`。**它們不會到來。**

| 項目 | 原本的來源 artifact | 為何不可產生 |
| --- | --- | --- |
| terminal global mid-ECDF lineage／digest | `manifests/s11-analysis.json` | `analyze` 在寫出任何 artifact 前 assert |
| per-value `n_gv / Cscore_occ_gv / mu_gv`、`T_g`、`S_g`（**sealed emitted 版**） | 同上 | 同上（診斷值見 §9.4，但那是 out-of-band 讀取，非 sealed emitted artifact） |
| own-null／familywise P95 與 strict-pass flags（**sealed emitted 版**） | 同上 | 同上 |
| bootstrap CI 半寬／recurrence（**sealed emitted 版**） | 同上 | 同上 |
| size direction、entropy、**positive global lambda** | 同上 | λ **不存在**；assert 先於指派 |
| half-stability categorical projection parity ＋ numeric drift | 同上 | 該 projection 由 `analyze` 產出 |
| shrinkage `alpha=0` per-gene decision-flip、OPTION_C 結論、decision-loss ordering error | 同上 | alpha0 的兩個 pass 屬 λ 之後的 frame，**從未被請求**（§6） |
| 四族 validity diagnostics（additive-rank／emitted-prior／arm-sensitivity／per-size margin） | 同上 | 同上 |
| guided gene count、`p1` 向量、untrusted mass、round-trip、candidate-order parity、shuffle mapping、**canonical guidance hash** | `manifests/s11-guidance.json` | guidance bundle 從未建構 |
| scientific outcome／criterion／failure ID／edge | `evidence/s11-decision.json` | 缺 `analyze` 輸入；`decide` 不可執行 |
| independent reproduction status ＋ digest | `evidence/s11-reproduction.json` | 缺 `decide` 輸入 |
| prelabel-absence／forbidden-read attestation（PB-S11-V2-C10） | `evidence/s11-decision.json` | 同上（可獨立陳述的事實見 §8） |
| positive-only compact gate record | `evidence/gate-records/s11-s1-guidance-locked.json` | positive 分支不可到達 |
| S12 handoff（frozen guidance bundle／guidance hash／D5 sample IDs／strata & folds／firewall attestation） | 多個 | 上列皆不存在 |

### 9.7 對 `S1_GUIDANCE_LOCKED` 能與不能下的結論

**能精確陳述的：**

1. contract `outcomes.positive.requirements` 共五項。其中 `global_Uexec_min: 256` **已滿足**（8,098）；`trusted_values_per_guided_gene_min: 2` 對 3 個 guided gene **皆滿足**；`stable_guided_gene_count_min: 1` 在**前六道 gate 的意義下已滿足**（3 個）。
2. `positive_global_lambda: true` **不滿足，且不可能滿足**——不是「λ=0」（那是 row-6 的 negative 條件），而是 λ **未被指派**（`guidance.py:95` 在指派前 assert）。
3. `all_...entropy_roundtrip_shuffle_firewall_replay_fresh_verification_gates: true` **不滿足**：entropy 這一項在 λ 選擇層失敗；round-trip／shuffle／replay／fresh verification 則**根本未被執行**（`not_evaluated`，非 fail）。

⇒ **`S1_GUIDANCE_LOCKED` 為 NOT EVALUABLE。**它既不是 PASS（requirement 4/5 不滿足），也不能被記為 FAIL——因為「FAIL」在本 protocol 中必須經由 `decide` 階段依 first-match 矩陣指派一個 outcome code，而該階段**不可執行**。

**不能陳述的（且本報告拒絕捏造）：**

- **不得**宣稱 S11 是 `COMPLETE_DETERMINISTIC_NO_GUIDANCE`（negative）。design §7 row-6 的文義是「**沒有 gene 通過** effect／permutation／direction／entropy，**或** lambda 為 0」。觀測上：3 個 gene 通過了 effect／permutation／direction；`UnrollLoopSwapGlobalReadOrder` 在 λ=0 的 `H_norm=1.0` 亦通過 entropy；λ 不是 0 而是不存在。**row-6 的任一 disjunct 都不成立。**
- **不得**宣稱 `FT-INCONCLUSIVE`。contract `outcomes.inconclusive.material_causes` 明列為 `support, coverage, precision_or_recurrence, final_half_stability, global_Uexec_below_256`；**觀測到的原因不在其中**（support 與 coverage 都大幅通過，precision/recurrence 對三個 guided gene 皆為滿分）。降級套用等同於事後放寬 taxonomy。
- **不得**宣稱 `FT-BLOCKED-MAPPING`（`empty-v1` allowlist 下結構上不可達）。

**由此暴露的 authority 缺口（需 owner 裁決，本報告不代填）：**frozen first-match 矩陣（design §7 rows 1–6 ＋ contract `outcomes`）**沒有任何一列**描述「guided set 非空、所有 per-gene 證據 gate 通過、但共用 λ 的可行域為空」這個**確定性**終止狀態。這是一個真實的 taxonomy 缺口，而非本次資料的偶然。處理它需要一次 protocol amendment（例如新增一個 `FT-CONSTRUCTION-INFEASIBLE` 類別，或把 entropy floor 改寫為 §9.5.3 的相對式），**其裁決權在 owner。**

---

## 10. RESULT-DRIVEN（C 層）：max-over-sizes reducer 的建構效度疑慮

> **來源：**`[BASELINE GPU]` S14 baseline pilot（[QA-09 §1](../../qa/qa-09-per-shape-soo-redesign-decisions.md)、[S14 design §9 open preflight／§10.1](../../s14-stage1-full-ga-outcome-design.md)）＋ `[CODE AUDIT]` ＋ `[MODEL-ONLY]`。**此為已定案的 downstream 決策依據，非 S11 formal outcome。**

### 10.1 疑慮

S11 sealed benefit 用 `benefit(o)=max_s b_s(o)`（`statistics.py:96`，reducer 鎖死成 `"max"`）。downstream S14 原本沿用同一 `max_s` 精神，以 `Q(x)=max_s[GFLOPS_s(x)/R_s]` 選單一 champion。`[BASELINE GPU]` pilot 揭穿：三個 size 的 per-size ratio 量級天差地遠（tiny≈4.3–4.9、medium≈2.3–3.0、large≈1.0–1.36），`Q=max_s` 幾乎永遠被 **tiny 8×8 主宰**，而 tiny 正是最不可信的 size（絕對 GFLOPS ≈2–4、launch jitter 主導；per-shape 噪音邊際 η_tiny=0.4466 ≈±45%，對比 η_medium=0.0042 ≈±0.4%）。→ Q 量到的是「哪個 kernel 在最吵的 tiny 上剛好高」，不是「哪個 kernel 好」——**建構效度（construct validity）壞掉**。

### 10.2 seed-14005 反例（`[BASELINE GPU]`）

| seed | tiny ratio | medium ratio | large ratio | aggregate `Q=max_s` |
| --- | --- | --- | --- | --- |
| 14001 | ~4.9 | ~2.8 | ~1.26 | 4.965 |
| 14002 | ~4.9 | ~2.5 | ~1.00 | 4.885 |
| 14003 | ~4.3 | ~3.0 | ~1.36 | 4.262 |
| 14004 | ~4.3 | ~2.3 | ~1.01 | 4.289 |
| **14005** | **~2.7** | ~2.1 | **~2.7** | **2.662（最低）** |

seed 14005 的 champion 在 large `[2304,1024,1,214336]` 上跑到 **≈480,141 GFLOPS**（其他 seed 只有 ≈182k–246k），在真正 compute-bound 的大問題上**快近一倍**，卻因 tiny ratio 偏低而拿**最低** aggregate Q。`max_s` 一旦選中 tiny，大 size 快多少都無所謂。這**不是**門檻能救的，是 metric 本身的建構效度問題。

### 10.3 對照 code：缺陷在 Ductile **內建**的 reducer（`REDUCER-FACT-CORRECTION-20260812` 已更正）

> **更正框（`REDUCER-FACT-CORRECTION-20260812`，user-directed 2026-08-12，文件更正、非 protocol 變更）：**本節先前的敘述為「Ductile GA 天生多目標、內部用 Pareto front survival，不會自己壓成純量，所以 aggregation **根本多餘**」——經 `[CODE AUDIT]` 證實**該敘述有誤**，已就地更正。**§10.1／§10.2 的實證缺陷、per-shape 決策、gate 與 claim 一律不變**；更正後的論證**更強**。

`[CODE AUDIT]`（撰稿者於 canonical repo tree 逐行核對）：

- **Ductile 未實作 Pareto／非支配排序。**對 `projects/hipblaslt/tensilelite/Tensile/ductile/` 全樹搜尋 `pareto|non-dominated|nsga|crowding` **零結果**。
- **`soo=False` 會在 GA 內部縮併為純量**：
  - `algorithm/ga.py:95` — `self.reduce_fn = np.mean if self.soo else np.max`
  - `algorithm/ga.py:263` — `best.F = scores.max(1)`（各 size incumbent，即正規化分母 `R_s`）
  - `algorithm/ga.py:269` — `pop.F = self.reduce_fn(scores / best.F[..., None], axis=0)`
- ⇒ **`Q_c = max_s(GFLOPS_{s,c} / R_s)` 就是 Ductile 的原生 fitness**，**不是** pilot 事後外加的一步。所謂「objectives」從未並存：它們被 `mean` 平均掉，或（本例）被 `max` 收成「候選只憑它表現最好的**那一個** size 被評分，其餘 size 直接丟棄」。

**更正後的論證：**問題不在「我們多加了一步 aggregation」，而在 **Ductile 內建的跨-size reducer 本身就是缺陷**。改成 per-shape 後 fitness 變成 `(1,N)`、`max` 退化為**恆等**，因此 per-shape **不是移除一個多餘步驟，而是從根本繞開該 reducer**。另一方面 Tensile `3_LibraryLogic` 本就 **per problem size** 輸出最佳解，下游也不需要跨-size champion——這仍是支持 per-shape 的獨立理由。

同一病根連坐 S11：`statistics.py:96` 的 `max(size_benefits)` ＋ `statistics.py:1359` 的 aggregate 2-of-3 方向 gate，與 `ga.py:95/263/269` 的 `np.max` 是**同一個 reducer 家族**。

### 10.4 S11 自己的資料就能證明這個 reducer 有缺陷（`[MODEL-ONLY]`＋`[CODE AUDIT]`，**新增**）

§10.1–§10.3 的證據是 GPU pilot ＋ code audit。**S11 的 sealed 分數 artifact 本身提供了一個完全 label-blind、不需任何 GPU 的獨立證明。**撰稿者直接從 `manifests/s11-native-scores.json` 重算（方法：對 canonical global frame 的 8,098 個 credited-and-scored occurrence，逐 size 建 occurrence-weighted mid-ECDF，取 `b_s = 1 - midECDF_s`，再取 `max_s`）：

| 觀測 | 值 |
| --- | --- |
| tiny `[8,8,1,128]` 回傳 sentinel `9999999.9` 的比例 | **8,098 / 8,098 ＝ 100.00%**（全語料：30,490 / 30,490） |
| medium `[256,256,1,1024]` sentinel 比例 | **4,424 / 8,098 ＝ 54.63%**（全語料 16,689 / 30,490 ＝ 54.74%） |
| large `[2304,1024,1,214336]` sentinel 比例 | **0 / 8,098 ＝ 0.00%** |
| ⇒ `b_tiny(o)` 的取值集合 | **{0.5}**——**每一個 occurrence 都完全相同** |
| ⇒ aggregate `benefit = max_s b_s` 的值域 | **[0.5, 0.99994]**（下半個尺度結構上不可達） |
| ⇒ 被 tiny 定住（`benefit` 恰為 0.5）的 occurrence | **2,303 / 8,098 ＝ 28.44%** |
| ⇒ global mean aggregate benefit | **0.6941** |

**根因分析：**tiny 的所有 config 都拿到同一個 sentinel 延遲，mid-ECDF 對一個**完全打平**的母體必然給出 `r = 0.5`，故 `b_tiny ≡ 0.5`。由於 reducer 是 `max`，**每個 config 的 aggregate benefit 都被硬性抬到至少 0.5**。後果有二：

1. **判別力被摧毀於下半段。**任何在 medium 與 large **兩邊都落在後半段**的 config（佔 28.44%），其 aggregate benefit **完全相同**（0.5）——reducer 對這近三成的母體**不再排序**。
2. **尺度被壓縮一半。**benefit 名目上是 [0,1] 的 rank 量，實際只用到 [0.5, 1.0]，所有 `mu_gv` 與 `S_g` 都在這個被壓縮的尺度上計算。

**交叉驗證：**這個重算與 sealed 輸出一致——sealed `gate_calls` 給出的 `DepthU` marginals 為 0.68332／0.73702，恰好夾住撰稿者重算的 global mean 0.6941；而 §13.2 的 per-shape `global_mean_s` 皆為 0.5（per-size mid-ECDF benefit 的平均必為 0.5，恆等式），aggregate 卻被抬到 0.694——**這 0.194 的位移就是 tiny sentinel 經由 `max` 注入的量。**

**誠實界線：**上述是撰稿者的重算，**不是** sealed emitted 值（`s11-analysis.json` 不存在）；方法依 §2.1／§2.2 的定義，但 sealed ECDF 在 conditional cell 上的查表細節可能造成第三位小數以下的差異，故本節數字**僅作為機制論證，不作為 gate 值**。`b_tiny ≡ 0.5` 與各 sentinel 計數則是**直接讀檔的精確事實**，無重算誤差。

**這使 §10 的論證不再只依賴 GPU pilot：**同一個 `max` reducer，在 S11 自己的 label-blind 模型空間內，就已經把 28.44% 的母體壓成不可分辨。per-shape 之所以正確，不只因為 tiny 在 GPU 上吵，更因為 **tiny 在模型空間中根本沒有訊號可貢獻，而 `max` 仍讓它設定了所有人的下界。**

---

## 11. RESULT-DRIVEN（C 層）：per-shape 重導、ENTROPY-CAP、SPARSITY

> **來源：**S14 design §10.3／§11、charter §8.6a、`agent_run/260809-s14-pershape-guidance/`。design-discussion 2026-08-09 兩位 fresh reviewer 皆 `AGREE`（zero dissent）→ **user-approved 2026-08-10**。**此為已定案 downstream 決策，非 S11 formal outcome。**

### 11.1 per-shape 重導（`PER-SHAPE-SOO-OUTCOME-20260809`，out-of-band、不改 locked code）

決策：S14 從 joint-MOO/aggregate-Q 改成 **per-shape**（每個 shape 各一條 GA），guidance/search/evaluation 全部 per-shape。上游 S11 因同病連坐，也**從既有 per-size 產物重新導出 per-shape guidance**——**不動 sealed code**，只**重用已封印的函式**（`gene_marginals`/`shrinkage_mean`/`construct_gene_probabilities`/`select_global_lambda`/`float32_inverse_cost_roundtrip`/`deterministic_nonidentity_shuffle`）。

五步重導：`b_{c,s}=1−midECDF_s(latency)`（取 `s11-native-scores.json` 的 `size_benefits[shape_index]`，**跳過 max**）→ α=32 shrinkage marginal `m_{g,s,v}` → `q_{g,s}=softmax(λ·(m−min))`（locked λ）→ per-shape 混合 → per-shape activation gate（不過退回 `p0`）。

**這一步之所以可行，正因為 §9 的 A 層失敗只發生在最後的 λ／guidance 建構層**：`s11-native-scores.json` 是 `score` 階段的完整、已封存產物，**不受** `analyze` 的 assert 影響。**S11 對 S14 的實際交付就是這個檔案**（sha256 `5316bba463ddc0d1fd1844b70006f218e8f10091f129a4ca5eb5a32afb501437`，撰稿者重算確認）。

**獨立驗證（`[CODE AUDIT]`，`verify/verification-report.md`：OVERALL PASS）：**fresh adversarial verifier 直呼 sealed 函式重算，**0 failures** across 3 shapes × 27 genes；p0/q/p1/weights/gate-decisions 全 match emitted（≤1e-9）；5 input sha256 全 match snapshot＋manifest；`p1==0.2*p0+0.8*q` ≤1e-12；roundtrip 162 次全 pass（max_abs_error 1.343e-08）；`git status --porcelain protocol/v1/s11/` = EMPTY；無 GPU/GA artifact。

**Input provenance（`[CODE AUDIT]`，撰稿者逐檔重算 sha256 確認）：**`s11-native-scores.json` `5316bba4…`、`s11-registry.json` `411fed77…`、`s11-global-prefix.json` `e7b00a8a…`、`s11-conditional-prefixes.json` `68927301…`、`s11-qualifications.json` `64b9e17d…`。**OLD binary-exclusion 版 output：**`guidance-medium.json` `b134039e…`、`guidance-large.json` `45e54f1b…`、`guidance-tiny.json` `0acd08b4…`。**capped 版 output（實際使用者）：**`guidance-medium.json` `ab3ff57e…`、`ga-weights-medium.json` `38d7757e…`、`guidance-large.json` `3b62df9c…`、`ga-weights-large.json` `9fcd2517…`、`guidance-tiny.json` `43057c59…`、`ga-weights-tiny.json` `47213c23…`。

**四道 stood-down gate（誠實界線）：**sealed 七項 AND-gate 中的 bootstrap CI、recurrence、own-null、familywise-null 定義在 **MAX-reduced aggregate** benefit ＋ `analyze` 階段的 2,000-permutation joint null／bootstrap 上，**不可 per-shape 從 read-only artifact 重算**，故 per-shape **stood down**。per-shape 實作 gate 只有 (a) ≥2 trusted、(b) `S_g≥0.05`、(c) per-shape 正向 direction，再加 (d) entropy cap（§11.2）。

> **本報告新增的重要註記：**§9 證明那四道 stood-down gate **在 sealed 路徑上也從未成功 emit**（`analyze` assert 於其後）。因此「per-shape 少了四道 gate」與「as-sealed 有那四道 gate」的對比**並不成立**——沒有任何一條路徑取得了它們的 attested 輸出。它們的診斷值僅存在於 out-of-band 的 `passes.w72.json`（§9.4）。這不改變任何決策，但讓 per-shape 的誠實界線敘述更精確：**stood down 的四道 gate，其 sealed 對照組並不存在。**

### 11.2 ENTROPY-CAP-20260810：binary 排除 → per-gene 混合強度 cap ρ

**問題（`[MODEL-ONLY]`）：**原 entropy floor 是**二元**的——某 gene 引導後 `H_norm(p1)<0.80` 就**整個排除**。這剛好砍掉**訊號最強**的 gene：`DepthU`（medium `S_g=0.1424`）與 `PrefetchGlobalRead`（large `S_g=0.1916`），因為它們**高基數但僅 2 個 trusted 值**（§9.5.2 已給出這 2 個 trusted 值的取樣根因）→ 一引導就集中 → `H_norm<0.80`（ent@λ0：DepthU 0.6576、PrefetchGlobalRead 0.7345——**與 §9.5.1 sealed 路徑量到的值完全相同**）。

**修法（S14 §10.3／§11 item 4；user-approved variant-B）：**對**每一個**過 trust+`S_g≥0.05`+正向 direction 的 gene，以已選 `λ_s=8` 取 `q_g=q(λ=8)`，用 **per-gene 混合強度 cap**：

```text
p1_g = (1−ρ)·p0 + ρ·q_g(λ=8)
ρ_g  = max{ ρ ∈ [0, 0.80] : H_norm((1−ρ)·p0 + ρ·q_g) ≥ 0.80 }
```

（`rho_grid_points = 4097`、`rho_step = 0.0001953125`；由 `derivation-manifest-capped.json.locked_constants` 確認。）

本來就達標的 gene `ρ=0.80`（等同舊 `0.2p0+0.8q`，**現有 active gene 一個不變**）；會踩底線的 gene 不再丟掉，而是把 ρ 降到剛好讓 `H_norm≈0.80`、以較低強度**納入**。這是**通用規則、對所有合格 gene 一致套用**（非 gate-shopping）；`H_norm≥0.80` 多樣性底線沒被降低。

**capped 版結果（`[CODE AUDIT]`＋`[MODEL-ONLY]`，撰稿者直接自 `derivation-manifest-capped.json` `per_shape_activation_log` 讀取）：**

| shape | `n_genes_activated` | activated genes（ρ / `S_g` / ent@λ0 / `H_norm(p1)` / TV / KL） | `λ_s` |
| --- | ---: | --- | ---: |
| medium `[256,256,1,1024]` | **2 / 27** | `DepthU` **ρ=0.566016**（**cap 新納入**）`S_g=0.142406`、ent@0 **0.657589**、`H_norm(p1)=0.800125`、TV=0.377344、KL=0.358127；`1LDSBuffer` ρ=0.80、`S_g=0.112716`、ent@0 1.0、`H_norm(p1)=0.915901`、TV=0.169043、KL=0.058293 | 8.0 |
| large `[2304,1024,1,214336]` | **5 / 27** | `PrefetchGlobalRead` **ρ=0.586133**（**cap 新納入**）`S_g=0.191584`、ent@0 **0.734498**、`H_norm(p1)=0.800118`、TV=0.335500、KL=0.277096；`UnrollLoopSwapGlobalReadOrder` ρ=0.80、`S_g=0.164739`、`H_norm(p1)=0.839929`；`GlobalReadVectorWidthB` ρ=0.80、`S_g=0.058021`、`H_norm(p1)=0.844142`；`TransposeLDS` ρ=0.80、`S_g=0.057093`、`H_norm(p1)=0.992663`；`GlobalReadVectorWidthA` ρ=0.80、`S_g=0.051991`、`H_norm(p1)=0.844404` | 8.0 |
| tiny `[8,8,1,128]` | **0 / 27** | —（全部 `S_g=0.0000`；sentinel 主導，見 §11.3） | `na` |

**驗證：**cap 對**每一個** activated gene 都守住 `H_norm(p1) ≥ 0.80`（兩個新納入者分別為 0.800125 / 0.800118，剛好貼齊）；5 個 prior-active gene 的 ρ 精確為 0.80、數值與舊 `0.2p0+0.8q` 相同。`verify-capped/verification-report-capped.md` 獨立驗證 **OVERALL PASS 40/40**；已 **Lock B SEALED**（§11.5）。

**兩個獨立路徑的數值一致性（強交叉驗證）：**per-shape 路徑量到的 `DepthU` ent@λ0 = **0.657589**、`PrefetchGlobalRead` = **0.734498**，與 §9.5.1 中 sealed aggregate-max 路徑量到的 **0.657588974** / **0.734497797** **完全相同到小數第六位**。這正是 §9.5.2 所預測的：`H_norm_max` 只是 `(n, k, uniform baseline)` 的函數，**與 reducer、與 marginals 無關**。兩條完全不同的分析路徑落在同一個數字上，是該結構性解釋的最強證據。

### 11.3 SPARSITY 稽核：activated gene 極少是模型性質，非 per-shape artifact

**觀測（`[MODEL-ONLY]`，capped 版 `per_shape_activation_log`，撰稿者逐 gene 統計）：**

| drop reason | tiny | medium | large |
| --- | ---: | ---: | ---: |
| `sensitivity_below_0_05`（主因） | **26** | **24** | **21** |
| `fewer_than_two_trusted_values` | **1** | **1** | **1** |
| **activated（存活）** | **0** | **2** | **5** |
| 合計 | 27 | 27 | 27 |

**根因一＝sealed `sensitivity S_g≥0.05` gate。**27 個 free gene 中有 **21–26 個近乎完全平坦**（`S_g ≈ 0.0006–0.03`；最極端者 `ScheduleGROverBarrier` medium `S_g=0.000634`、`WaveSeparateGlobalReadA` medium `S_g=0.000958`——best 與 worst 值只差 **0.06–0.1 個 rank-percentile point**）。模型預測某 gene 換值幾乎不改變延遲名次 ⇒ 引導 ≈ uniform ≈ 沒有 treatment。**不能靠放寬門檻修**（那些 gene 是真的平），亦見 §9.4 讀法 1 的獨立佐證。

**根因二＝reducer 無關性。**`analysis/reducer_comparison.txt` 給出四種計量口徑下通過 `S_g≥0.05` 的 gene 數：**aggregate_max = 3、medium = 2、large = 5、tiny = 0**（mean `S_g` 分別 0.0174 / 0.0232 / 0.0280 / 0.0000）。**連訊號最濃的 aggregate max-reducer 也只有 3 個**（此數字由 §9.4 的 sealed `gate_calls` 獨立確認：`S_g ≥ 0.05` 者恰為 PrefetchGlobalRead 0.0942、UnrollLoopSwap 0.0900、DepthU 0.0537）。⇒ 稀疏是**模型本身的性質**，**不是** per-shape 切碎訊號造成的產物。

**根因三＝`fewer_than_two_trusted_values` 恰為 1 個（`DirectToVgprA`）**，且是唯一因 trust 而非 sensitivity 出局者。§9.1 的 stream 表給出精確原因：它的兩個 boolean value 中，第二個在 262,144 次 draw 內只取得 **40** 個 accept（門檻 128）。

**tiny=0 的完整根因鏈（`[CODE AUDIT]`）：**

1. Formocast 的 early-terminate guard，`shared/origami/src/simulator/tensilelite/formocast_simulator.cpp:578`：
   ```cpp
   if ((M < 128 && MT0 - M >= 16) || (N < 128 && MT1 - N >= 16))
   { pp.microSeconds = 9999999.9; pp.hitRate = 0; return pp; }
   ```
   語意是「問題維度小於 128 而 MacroTile 超出它 ≥16 時，拒絕建模」——物理上那是一塊幾乎全在算 padding 的 tile。對 tiny（M=N=8）等於要求 **MT0 ≤ 23 且 MT1 ≤ 23**。
2. **實測後果（撰稿者自 `s11-native-scores.json` 直接統計）：30,490 / 30,490 ＝ 100.00% 的 scored identity 在 tiny 上回傳 sentinel。**（既有索引文件由 MacroTile pool 推估「434 個 MacroTile 中 1 個可過關 ≈0.2% 存活」；那是**候選 MacroTile 形狀**層級的統計，而**實際被抽樣並通過 validator 的語料中存活數為 0**。兩者不矛盾，但**應以實測的 100% 為準**。）
3. 全部打平 ⇒ mid-ECDF 對每個 config 給同一個 `r=0.5` ⇒ 每個 per-value marginal 完全相同 ⇒ **27 個 gene 的 `S_g` 全為 0.0000**，`per_shape_direction_positive` 全 False。

⇒ tiny 是**在 Formocast 的建模範圍之外**，不是「模型試了卻失敗」。故 tiny 定為 **exploratory、`not evaluated / not activated`**，**非**「無效果」。

**medium 與 large 差異（2 vs 5）的機制解釋（`[MODEL-ONLY]`，interpretation 非 proof）：**

- 撰稿者實測 sentinel 比例：**medium 54.74%、large 0.00%**。large 的整個語料都有有效預測，rank 解析度完整；medium 有超過一半的語料**並列在 sentinel 上**，mid-ECDF 對這 54.74% 給出同一個 benefit（0.273680），rank 尺度被壓掉一半以上——**這本身就會系統性壓低 medium 的 `S_g`**。
- 其上再疊加 K 的物理效應：large 的 K=214,336（medium 的 ~209×），main loop 迭代量極大 ⇒ 每次迭代的**記憶體搬運管線主導總時間**，5 個存活者全部是 global-read／LDS／main-loop 資料搬運 gene（PrefetchGlobalRead 0.1916、UnrollLoopSwapGlobalReadOrder 0.1647、GlobalReadVectorWidthB 0.0580、TransposeLDS 0.0571、GlobalReadVectorWidthA 0.0520）；medium 的 K=1,024，main loop 中等，存活者是較粗粒度的**迴圈結構** gene（DepthU 0.1424、1LDSBuffer 0.1127），細粒度記憶體管線 gene 全部沉在門檻下（PGR 0.0235、TransposeLDS 0.0289、GRVWB 0.0392）。
- **最銳利的證據——主導 gene 隨 K 交叉：**`DepthU` medium **0.1424 PASS** vs large 0.0289 FAIL；`PrefetchGlobalRead` medium 0.0235 FAIL vs large **0.1916 PASS**。同兩個 gene 以**相反方向**互換角色。
- **誠實界線：**「K ⇒ 記憶體主導」是與資料一致的**機制解釋**，不是已證因果；而且 medium 的低計數至少有一部分來自上述 sentinel 造成的 rank 壓縮，**兩個原因無法從 S11 分離**。

**`S_g` 的白話與界線：**`S_g` 量「某 gene 的各 value 的『Formocast 預測延遲之 population-rank 平均』彼此散得多開」。`S_g=0` → 換 value 不影響預測名次 → 引導≈baseline。`0.05` 是**預註冊的啟發式 model-space 底線**（≈5 個 rank-percentile point，λ=8 時 ≈1.49× best/worst odds）；它**不**綁 GPU noise、**不**是 power calculation。失敗＝「此 factorized 模型-排名主效應不可用」，**非**「真實 GPU／絕對／交互 無效果」。

**兩道 gate 的分工（務必分清）：**`S_g≥0.05`（sensitivity）評估「這 gene **有沒有**方向可引導」→ 決定**活化**、造成 sparsity（模型性質）；entropy floor（`H_norm≥0.80`）評估「引導後**有多集中**」→ 保住 Gen0 探索多樣性，其二元版**副作用**恰好砍掉最強的 gene，並在 sealed aggregate 路徑上直接造成 §9 的阻塞（§11.2 修之）。

### 11.4 Claim-scope（charter §8.6a `CLAIM-SCOPE-S14-20260810`，two-sided）

owner 2026-08-10 核准 charter §8.6a：S14 以 **two-sided、bounded** 報告 guided initialization 對 (i) early-search（gen-10）quality-vs-evaluations 與 (ii) **最終 tuned 品質（final champion real-GFLOPS）** 的效應（含改善／無變化／退步）。**若資料支持，得宣稱**「受測 shape（medium/large）、單一 development cluster、5 對 paired seed 下，guided initialization 使最終 tuned 品質提升（directional/bounded evidence）」。**強制誠實界線：**必標 power（5 seeds＝bounded/modest，非統計顯著性證明）與 scope（僅受測 shape、單一 cluster、不一般化）；**不得在 sealed 分析前預設任何結論**；每數字標 evidence type、seed 為實驗單位、全報 seed/失敗/排除。**仍禁**：MI300X 一般化、production/deployment ready、beat native `PredictionThreshold`、跨架構、end-to-end wall-clock speedup、owner/team 應採用。

**負向結果（charter §8.5）：**須定位到層次；「模型沒用」不是合格結論。本 S11 報告的定位見 §15。

### 11.5 Lock B SEALED（capped bundle 於任何 guided 結果前先封）

**狀態（`[CODE AUDIT]`，`agent_run/260809-s14-pershape-guidance/lock/lock_b_guided_guidance.json`）：**capped guidance bundle 已由 **Lock B**（`lock: S14_LOCK_B_GUIDED_GUIDANCE`）**SEALED**，於看任何 guided 結果前先封。

- **Lock B 自身 sha256（撰稿者重算）：**`3ac9768768ac088596687c47635bd6b8b5018d67cecc3f08e69ba2857b0ce59b`。
- **獨立驗證：**`verify-capped/verification-report-capped.md` **OVERALL PASS（40/40 checks）**——CAP FORMULA FAITHFUL + UNIVERSAL、`ρ<0.80` 僅新納入者且不 under-cap、prior-active 5 gene ρ==0.80、q 取自 sealed 函式於 `λ_s`、weights/roundtrip/`output_sha256` 全 match。
- **Sealer ratifications：**(1) `gate_d_entropy_cap` **APPROVED**；(2) `lambda_s_reuse` **APPROVED**——`λ_s=8` 於 floor-meeting old gene set 上選定，**newly-capped genes 排除於 λ-selection**；(3) `stood_down_sealed_gates` **ACKNOWLEDGED**；(4) `heuristic_out_of_band` **ACKNOWLEDGED**——capped p1 是 out-of-band S14 treatment artifact（**非** sealed `construct_gene_probabilities` 輸出），`S_g` 是 model-space heuristic，無 rank→GFLOPS 映射。
- **Consumption rule：**GUIDED 臂逐 shape 注入 `ga-weights-<shape>.json`（activated gene 用 p1、fallback 用 p0）；BASELINE 臂 weights=null；same seeds、same per-seed GPU UUID、counterbalanced；**不得在 BASELINE 完成且 Lock B 就位前跑 guided**。

**與 S11 formal outcome 的界線：**Lock B 是 **S14 out-of-band artifact**，**不**是 S11 formal artifact，**不**改變 §9 的 `not_evaluated`。反向亦然：§9 的阻塞**不使 Lock B 失效**——Lock B 的輸入是 `score` 階段的完整產物，與 `analyze` 無關（§11.1）。

---

## 12. as-sealed（max-reducer）S11 ↔ per-shape capped 重導 的關係

| | **as-sealed（max-reducer）S11** | **per-shape capped 重導** |
| --- | --- | --- |
| 原定角色 | 提供 `S1_GUIDANCE_LOCKED` gate ＋ provenance ＋ per-size scores ＋ **reference** guidance | **實際餵給 S14 的 treatment** |
| **實際交付** | **provenance ＋ per-size scores（`s11-native-scores.json`）＋ 26-gene 診斷 gate table**；**guidance 與 gate 從未產出**（§9） | capped `guidance-<shape>.json` ＋ `ga-weights-<shape>.json`，**Lock B SEALED** |
| reducer | 跨 size `max` + aggregate 2-of-3 方向 gate | per-shape、跳過 max、per-shape direction |
| lineage | sealed 函式；LOCKED_READY；tree 已驗證未改動 | out-of-band artifact，**非** sealed 輸出 → 新 bundle 名、新 hash、獨立驗證（40/40 PASS）、Lock B SEALED（`3ac97687…`） |
| 混合 | 固定 `0.2p0+0.8q`（**未曾實際建構**） | per-gene ρ cap（`ENTROPY-CAP-20260810`） |
| entropy floor | **二元、跨 gene 共用 λ 的可行性條件** → 造成 §9 的 assert | **per-gene 強度 cap** → 保住 `H_norm≥0.80` 同時納入最強 gene |
| 是否改動彼此 | per-shape **不取代／不改寫／不回餵** sealed S11 | sealed S11 artifact 原封保留 |

**關鍵澄清（相對於舊稿）：**舊稿寫「兩份 artifact 並存、as-sealed 提供 reference guidance」。**as-sealed 從未產生任何 guidance。**正確的表述是：as-sealed S11 提供的是**分數與 provenance**，per-shape capped 重導是**唯一存在的 guidance bundle**。

**回退規則（S14 §10.3／§11 item 6）：**若 ENTROPY-CAP 無法在 label 前封 → 退回 A（照原稀疏 guidance 跑、不修 gate）；整 shape 全回退＝`not activated`；此 out-of-band 導出**不改任何 locked s11/*.py**（sealed dir 已驗證 clean）。

---

## 13. Gene-selection 完整稽核（benefit → gene selection 全紀錄）

> **來源：**`[CODE AUDIT]`＋`[MODEL-ONLY]`。per-shape 欄位取自 capped 版 `derivation/derivation-manifest-capped.json` 的 `per_shape_activation_log`（撰稿者逐 gene 直接讀取，非轉引）；aggregate-max 欄位取自 `parallel-analyze/out/diag-lambda2.w72.json` 的 `gate_calls`（§9.4），並經 `analysis/reducer_comparison.txt` 交叉核對。此表即 owner 要求保留的「benefit → gene selection」全紀錄。

### 13.1 逐 shape 匯總（capped 版）

| shape | size | activated | activated genes | fallback reason counts | `λ_s` | `global_mean_s` |
| --- | --- | --- | --- | --- | ---: | ---: |
| medium | `[256,256,1,1024]` | **2/27** | `DepthU`(ρ=0.566)、`1LDSBuffer`(ρ=0.80) | {`sensitivity_below_0_05`: 24, `fewer_than_two_trusted_values`: 1} | 8.0 | 0.5 |
| large | `[2304,1024,1,214336]` | **5/27** | `PrefetchGlobalRead`(ρ=0.586)、`UnrollLoopSwapGlobalReadOrder`、`TransposeLDS`、`GlobalReadVectorWidthA`、`GlobalReadVectorWidthB`（後四者 ρ=0.80） | {`sensitivity_below_0_05`: 21, `fewer_than_two_trusted_values`: 1} | 8.0 | 0.5 |
| tiny | `[8,8,1,128]` | **0/27** | —（sentinel 100%） | {`sensitivity_below_0_05`: 26, `fewer_than_two_trusted_values`: 1} | `na` | 0.5 |

> **注意：**capped 版**已移除**舊 binary gate `entropy_floor_unmeetable`；OLD 版 medium 的 `{sens<0.05: 24, entropy_floor_unmeetable: 1, <2 trusted: 1, pass: 1}` 與 large 的 `{21, 1, 1, 4}` 是**歷史紀錄**，不再是現行 activation 依據。

### 13.2 sensitivity 分佈（`analysis/reducer_comparison.txt`，經 §9.4 sealed `gate_calls` 獨立確認 aggregate 列）

| 計量口徑 | #trusted≥2 | #`S_g≥0.05` | mean `S_g`(trusted) |
| --- | ---: | ---: | ---: |
| **aggregate_max（最濃）** | 26 | **3** | 0.0174 |
| tiny (idx0) | 26 | **0** | 0.0000 |
| medium (idx1) | 26 | **2** | 0.0232 |
| large (idx2) | 26 | **5** | 0.0280 |

### 13.3 逐 gene 稽核表（27 genes）

欄位說明：`nt`＝trusted value 數（三個 shape 相同，源自同一 trust 判定）；`cand`＝該 gene 的 activated conditional stream 數（＝candidate 數，源自 `s11-conditional-prefixes.json`）；`S_g(agg)`＝aggregate-max sealed sensitivity（§9.4）；`S_g(med)`／`S_g(lrg)`＝per-shape sensitivity；`ρ`＝capped 混合強度（`—`＝未 activated）；`agg 七道`＝aggregate-max 路徑是否七道全過。tiny 全 gene `S_g=0.0000`、direction 全 False，故不另列欄。

| gene | cand | nt | `S_g(agg)` | `S_g(med)` | `S_g(lrg)` | ρ medium | ρ large | agg 七道 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| **PrefetchGlobalRead** | 4 | 2 | **0.0942** | 0.0235 | **0.1916** | — | **0.586** | **✔** |
| **UnrollLoopSwapGlobalReadOrder** | 2 | 2 | **0.0900** | 0.0336 | **0.1647** | — | **0.800** | **✔** |
| **DepthU** | 6 | 2 | **0.0537** | **0.1424** | 0.0289 | **0.566** | — | **✔** |
| GlobalReadVectorWidthB | 7 | 4 | 0.0311 | 0.0392 | **0.0580** | — | 0.800 | ✘ |
| GlobalReadVectorWidthA | 7 | 4 | 0.0271 | 0.0174 | **0.0520** | — | 0.800 | ✘ |
| 1LDSBuffer | 2 | 2 | 0.0210 | **0.1127** | 0.0223 | **0.800** | — | ✘ |
| WorkGroupMapping | 18 | 18 | 0.0202 | 0.0422 | 0.0222 | — | — | ✘ |
| TransposeLDS | 4 | 4 | 0.0165 | 0.0289 | **0.0571** | — | 0.800 | ✘ |
| NumElementsPerBatchStore | 8 | 8 | 0.0145 | 0.0168 | 0.0227 | — | — | ✘ |
| StoreSyncOpt | 3 | 3 | 0.0106 | 0.0109 | 0.0109 | — | — | ✘ |
| SourceSwap | 2 | 2 | 0.0103 | 0.0221 | 0.0026 | — | — | ✘ |
| StaggerU | 3 | 3 | 0.0095 | 0.0045 | 0.0149 | — | — | ✘ |
| WorkGroupMappingXCC | 5 | 5 | 0.0091 | 0.0240 | 0.0111 | — | — | ✘ |
| NonTemporalD | 2 | 2 | 0.0064 | 0.0106 | 0.0038 | — | — | ✘ |
| WaveSeparateGlobalReadA | 2 | 2 | 0.0063 | 0.0010 | 0.0146 | — | — | ✘ |
| StaggerUStride | 4 | 4 | 0.0059 | 0.0136 | 0.0066 | — | — | ✘ |
| TailloopInNll | 2 | 2 | 0.0056 | 0.0120 | 0.0101 | — | — | ✘ |
| WaveSeparateGlobalReadB | 2 | 2 | 0.0044 | 0.0094 | 0.0075 | — | — | ✘ |
| MIArchVgpr | 2 | 2 | 0.0043 | 0.0019 | 0.0022 | — | — | ✘ |
| ExtraMiLatencyLeft | 2 | 2 | 0.0035 | 0.0055 | 0.0032 | — | — | ✘ |
| NonTemporalA | 2 | 2 | 0.0033 | 0.0111 | 0.0038 | — | — | ✘ |
| NonTemporalB | 2 | 2 | 0.0008 | 0.0029 | 0.0036 | — | — | ✘ |
| NonTemporalC | 2 | 2 | 0.0013 | 0.0016 | 0.0003 | — | — | ✘ |
| ScheduleGROverBarrier | 2 | 2 | 0.0024 | 0.0006 | 0.0063 | — | — | ✘ |
| AdaptiveGemm | 2 | 2 | 0.0006 | 0.0100 | 0.0025 | — | — | ✘ |
| StorePriorityOpt | 2 | 2 | 0.0003 | 0.0038 | 0.0039 | — | — | ✘ |
| **DirectToVgprA** | 2 | **1** | 不可檢定 | 不可檢定 | 不可檢定 | — | — | 不可檢定 |

### 13.4 稽核觀察（誠實記錄，每項附根因）

1. **兩個 reducer 選出同一小組 gene——稀疏訊號是穩定的，不是雜訊。**aggregate-max 的三個存活者 {PrefetchGlobalRead, UnrollLoopSwapGlobalReadOrder, DepthU} **全部**落在 per-shape activated 聯集 {DepthU, 1LDSBuffer} ∪ {PrefetchGlobalRead, TransposeLDS, UnrollLoopSwapGlobalReadOrder, GlobalReadVectorWidthA, GlobalReadVectorWidthB} 之內。兩種完全不同的聚合方式收斂到同一小組，是「有訊號的少數 gene 能被可複現地辨識出來」的**正面證據**。
2. **`S_g` 隨 shape 劇烈變動——這是 max-reducer 建構效度問題的定量體現。**`DepthU` medium 0.1424 / large 0.0289（4.9× 差距）、`PrefetchGlobalRead` large 0.1916 / medium 0.0235（8.2× 差距）、`1LDSBuffer` medium 0.1127 / large 0.0223（5.1×）。aggregate-max 把它們混成 0.0537 / 0.0942 / 0.0210，**系統性地稀釋了每個 gene 在它真正重要的那個 shape 上的訊號**——`1LDSBuffer` 就是被稀釋到 aggregate 路徑上 direction 與 familywise 雙雙不過的例子（§9.4 列 6）。
3. **絕大多數 fallback＝`sensitivity_below_0_05`**（medium 24、large 21、tiny 26）：模型對這些 gene 幾乎完全平坦——sparsity 的模型-性質根因（§11.3）。
4. **`DirectToVgprA` 是唯一因 trust 出局者**，根因是取樣層而非模型層：第二個 boolean value 只取得 40 個 accept（<128）。
5. **tiny 全 0 有精確、可查證的機械原因**（`formocast_simulator.cpp:578` guard ＋ 實測 100% sentinel），**非** per-shape artifact，**非**「無效果」。
6. **能通過 recurrence gate 與能通過 entropy floor 的 gene 集合方向相反**（§9.4 讀法 2 ＋ §9.5）：低基數 gene 容易過 recurrence（best/worst 無從變動）卻過不了 entropy floor；高基數 gene 反之。sealed 七道 gate 因此在 arity 維度上存在**內部張力**——這是本次執行揭露的、可轉移的協定設計發現。
7. `S14_PER_SHAPE_OUTCOME` 定位為「**稀疏 Gen0 treatment 的 bounded 測試**」，非「27-gene 廣泛 guidance」（S14 §11 item 1）。

---

## 14. Scope 與 claim boundary

**S11 是 label-blind／model-only，且本次沒有取得 formal outcome。**

**可以說的：**

- `[CODE AUDIT]` sealed max-reducer `analyze` 在此資料上**確定性不可完成**，原因已定位到 `guidance.py:95` 的 λ 可行域為空，並以四軸驗證排除實作缺陷（§9.3）。
- `[MODEL-ONLY]` 在 aggregate-max frame 下，26 個可檢定 gene 中 **3 個**帶有通過全部七道 per-gene 證據 gate、邊際 1.79×–11.86× 的 marginal 訊號；其餘 gene 的 best/worst rank 差距多在 0.03–3 個百分位點。
- `[MODEL-ONLY]` 固定 `H_norm≥0.80` floor 對 `(n=6,k=2)` 在**任何** baseline 下皆不可達（sup 0.7435）、對 `(n=4,k=2)` 在 **sealed uniform baseline** 下不可達（sup 0.7345）。
- `[CODE AUDIT]` S11 完整交付了 `s11-native-scores.json`，S14 的 per-shape capped guidance **完全由它導出**，並已獨立驗證且 Lock B SEALED。

**不能說的：**

- **不能**說 guidance 指向真實高品質 config（`mu_gv` 是 non-causal、survivor-frame、Formocast-rank 的 conditional association）。
- **不能**說 S11 為 negative／inconclusive／positive 中的任何一個（§9.7）。
- **不能**說「模型沒用」——這在 charter §8.5 下不是合格結論；本次結果的層次定位見 §15。
- **不能**說 real ranking／prior mass／actual Gen0 效果、GPU correctness/noise/performance、跨 shape 一般化、S12/S13/S14 任何結果、或 unobserved candidate 是否 absent。
- **不能**把 §9.4 的 26-gene 表當成 sealed attested gate 輸出——它是 out-of-band 讀取的診斷值（雖已證與 sealed 路徑 bit-identical）。

**C 層決策的 claim 界線：**per-shape capped guidance 是 S14 out-of-band treatment，其效果宣稱受 charter §8.6a `CLAIM-SCOPE-S14-20260810` 約束（§11.4）——two-sided、bounded、5-seed modest power、限受測 shape、看資料前不預設結論。sparsity／max-reducer／entropy-cap 的所有數字皆 `[MODEL-ONLY]` 或 `[CODE AUDIT]`，**不含任何 real GFLOPS**；§10.2 的 `[BASELINE GPU]` 數字僅來自 baseline 臂，**絕不**合成 guided counterfactual。

**Outgoing edge：**唯一 future scientific edge `S11:S1_GUIDANCE_LOCKED -> S12` **從未成立、且不可能由本次執行成立**（positive 分支需要 `evidence/s11-decision.json` 與 positive gate record，兩者皆 NOT PRODUCIBLE）。依 design §8，positive 分支**禁止**產生本 report；本 report 之所以存在，正因為 positive closeout 不可到達——但它**也不是** negative／inconclusive 的 terminal formal report，因為那兩個 code 同樣不可被指派（§9.7）。**本 report 的定位是：一份 terminal 的、對 `not_evaluated` 狀態的完整記錄與根因分析。**

---

## 15. 負向／稀疏結果的層次定位（charter §8.5 強制）

charter §8.5 要求：稀疏或負向結果**必須定位到層次**，且「模型沒用」不是合格結論。本次結果的定位如下。

**定位：`marginal-loss`（per-gene 邊際訊號薄弱）。**理由：

- 訊號**沒有**消失在工程層——執行良率 98.85%、評分覆蓋 100.0%、`|Uexec|` 為門檻的 31.6×（§9.2）。
- 訊號**沒有**消失在統計檢定層——2,000 次 permutation 與 2,000 次 bootstrap 全部完成，且三個 gene 以 1.79×–11.86× 邊際通過（§9.4）。
- 訊號**沒有**因 per-shape 切分而稀釋——最濃的 aggregate-max reducer 也只給出 3 個（§13.2）。
- 訊號的薄弱表現在**每個 gene 單獨的邊際效果**上：21–26/27 個 gene 的 best 值與 worst 值在預測延遲 rank 上只差 0.03–3 個百分位點。

**S11 明確無法區分的三個競爭解釋（需 S12/oracle）：**

1. **genuine insensitivity**——這些 gene 的值在物理上確實幾乎不影響延遲；
2. **epistasis hidden by marginals**——某些值只有在特定組合下才有效果，而 per-gene 邊際（「其他參數隨機」）在定義上對交互作用是盲的；
3. **survivor-frame ／ rank compression**——(a) 統計只建立在通過 validator＋generation＋compile＋scoring 的 survivor 上，是 non-causal 的 conditional association；(b) benefit 是 population **rank** 而非絕對延遲，且本次語料存在大量並列（tiny 100%、medium 54.74% 打平於 sentinel；aggregate 更有 28.44% 被壓在 0.5，§10.4），rank 尺度被實質壓縮——一個在絕對 GFLOPS 上重要、但在被壓縮的 rank 上平坦的 gene，會與「真的平」無法區分。

**這三者在 S11 內部不可分辨**，需要 S12（oracle / D5 label）才能切開。因此本報告**不**宣稱模型無訊號、**不**宣稱這些 gene 無效果、**不**宣稱 epistasis 已被證明。`not_evaluated ≠ no effect`。

**另外定位到協定層（非模型層）的一項獨立發現：**§9.5 的阻塞**不是模型訊號問題**，而是 **guidance 建構規則與 gene arity 的結構衝突**——一個固定的絕對 entropy floor 隱含地對 `k/n` 施加了未言明的要求。這一層與 marginal-loss 完全獨立，且已由 `ENTROPY-CAP-20260810` 在 downstream 路徑上處理（§11.2）；在 sealed 路徑上處理它需要 owner 層級的 protocol amendment（§9.7）。

---

## 附錄 A — Artifact ／ hash 索引（全部由撰稿者重算或直接讀取）

**S11 sealed manifests（PRESENT）**，位於 `protocol/v1/manifests/`：

| 檔案 | 檔案 sha256 | 關鍵內容 |
| --- | --- | --- |
| `s11-registry.json` | `411fed77f735f52e…` | 27 eligible genes / 101 conditional streams / `actual_reducer: max` / `soo: false` |
| `s11-global-prefix.json` | `e7b00a8a16859554…` | credited 8,192 / observed 90,359 / zero-credit 82,167 / 65,536 chunks |
| `s11-conditional-prefixes.json` | `68927301044221aa…` | 101 streams × 512 chunks；88 達 256、13 <128 |
| `s11-qualifications.json` | `64b9e17d838844ff…` | 30,802 records；accepted 30,490 / `normal_kernelwriter_reject` 312 |
| `s11-native-scores.json` | `5316bba463ddc0d1…` | 30,490 score records（3 sizes 皆有值）— **S11 對 S14 的實際交付物** |

**out-of-band parallel `analyze`**，位於 `agent_run/260803-ductile-factorized-guidance-s11/parallel-analyze/`：

| 檔案 | sha256 / 內容 |
| --- | --- |
| `out/passes.w72.json` / `out/passes.w40.json` | `d7371242985190b3a94d5112afcba8923fac236d42b3afbe10805ec0521df0ce`（兩檔 byte-identical，撰稿者重算確認） |
| `out/diag-lambda2.w72.json` | `status = "ASSERTION at call #1"`；`guidance_inputs` sha `11d93fbb…`；`gate_calls` 26 筆 |
| `out/diag-lambda2.w72-sealedecdf.json` | 全 sealed ECDF 路徑；`guidance_inputs`／`calls`／`gate_calls` 與上者 **完全相同** |
| `out/verify-subset.<kind>.json`（4 檔） | per-replicate bit-equality 證據 |
| `VERIFICATION.md` | 四軸驗證與 determination (A) FAITHFUL |
| sealed tree digest | `*.py` sha256 清單之 sha256 `1b1be01c982ee72d…`；`git ls-files -s` digest `34bfa5cb32945305…` |

**S14 out-of-band per-shape guidance**，位於 `agent_run/260809-s14-pershape-guidance/`：

| 檔案 | sha256 / 內容 |
| --- | --- |
| `derivation/derivation-manifest-capped.json` | `per_shape_activation_log`（27 genes × 3 shapes）、`locked_constants`、`gate_definition`、`caveats` |
| capped outputs | `guidance-medium.json` `ab3ff57e…`／`ga-weights-medium.json` `38d7757e…`／`guidance-large.json` `3b62df9c…`／`ga-weights-large.json` `9fcd2517…`／`guidance-tiny.json` `43057c59…`／`ga-weights-tiny.json` `47213c23…` |
| OLD binary-exclusion outputs（保留、未餵 S14） | `b134039e…`／`45e54f1b…`／`0acd08b4…` |
| `verify/verification-report.md` | OVERALL PASS，0 failures across 3 shapes × 27 genes |
| `verify-capped/verification-report-capped.md` | OVERALL PASS 40/40 |
| `lock/lock_b_guided_guidance.json` | Lock B SEALED；檔案 sha256 `3ac9768768ac088596687c47635bd6b8b5018d67cecc3f08e69ba2857b0ce59b`（撰稿者重算） |
| `analysis/reducer_comparison.txt` | 四種 reducer 口徑的 `S_g≥0.05` 計數與 mean |

**Code 引用（`[CODE AUDIT]`，逐行核對）：**

| 位置 | 內容 |
| --- | --- |
| `protocol/v1/s11/statistics.py:62` | reducer 鎖死為 `"max"` |
| `protocol/v1/s11/statistics.py:90 / :96 / :138` | per-size benefit ／ `max(size_benefits)` |
| `protocol/v1/s11/statistics.py:188` | `shrinkage_mean(..., alpha=32)` |
| `protocol/v1/s11/statistics.py:1166` | `sensitivity()` |
| `protocol/v1/s11/statistics.py:1359` | `size_direction()` |
| `protocol/v1/s11/guidance.py:77–95` | `select_global_lambda()`；`:95` 為阻塞 assert |
| `projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py:95 / :263 / :269` | `reduce_fn = np.max`（`soo=False`）／`best.F = scores.max(1)`／`pop.F = reduce_fn(scores / best.F[...,None], axis=0)` |
| `projects/hipblaslt/tensilelite/Tensile/ductile/**` | `pareto|non-dominated|nsga|crowding` 全樹搜尋 **零結果** |
| `shared/origami/src/simulator/tensilelite/formocast_simulator.cpp:578` | tiny sentinel guard |

---

## 附錄 B — 相對於前一版 DRAFT-SCAFFOLD 的變更摘要

| 變更 | 說明 |
| --- | --- |
| frontmatter | `report_status: DRAFT-SCAFFOLD → TERMINAL`；新增 `criterion_status: UNREACHABLE_AS_SEALED`、`delivered_artifacts`、`never_producible_artifacts`；`current_artifact_state: RUNNING → CLOSEOUT_NOT_PRODUCIBLE` |
| §9 | 33 個 `⟨TBD@closeout⟩` placeholder **全部移除**，改為 verified 觀測值（§9.1／§9.2／§9.4／§9.5）或明確的 `NOT_PRODUCIBLE` ＋ 原因（§9.6） |
| §9.3／§9.5（新） | 阻塞發現、四軸驗證、`(n,k)` 結構性根因、trusted-value 取樣飢餓的兩段式因果鏈 |
| §9.7（新） | `S1_GUIDANCE_LOCKED` 為 NOT EVALUABLE 的精確論證，以及 frozen 判定矩陣的 taxonomy 缺口 |
| §10.3 | 依 `REDUCER-FACT-CORRECTION-20260812` **就地更正**：刪去「Ductile 天生多目標、Pareto survival、aggregation 根本多餘」的錯誤敘述，改為「Ductile **內建**的 `np.max` 跨-size reducer 本身即缺陷，per-shape 使其退化為恆等而繞開」 |
| §10.4（新） | 以 S11 自己的 label-blind 分數證明 max reducer 的缺陷（`b_tiny ≡ 0.5`、28.44% 母體被壓成同值） |
| §11.3 | fallback 計數改用 capped 版 manifest（medium 24+1+2、large 21+1+5、tiny 26+1+0）；tiny sentinel 由「≈99.8% 推估」改為**實測 100.00%** |
| §13 | 稽核表加入 aggregate-max sealed `S_g` 與七道 gate 結果欄，並加入 candidate 數欄以支持 §9.5 的 arity 論證 |
| §15（新） | charter §8.5 要求的層次定位（marginal-loss）＋ 三個 S11 不可分辨的競爭解釋 |
| FILL-LIST | 移除（已無 placeholder），改為附錄 A 的 artifact／hash 索引與附錄 B |
