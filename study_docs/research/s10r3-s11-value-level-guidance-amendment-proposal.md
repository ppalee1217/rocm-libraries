---
document_type: experiment_change_proposal
proposal_id: S10R3-S11-VALUE-LEVEL-GUIDANCE
status: DEFERRED_BY_APPROVED_S10R4_EXACT_FRAME_DECISION
authority_effect: historical_proposal_plus_decision_record
affected_checkpoints:
  - S10R3
  - S10R4
  - S11
created_date: 2026-08-01
---

# S10R3 → S11 value-level bounded guidance 實驗變更建議

## 0. 文件狀態

本文件前半保留原始**非權威實驗變更草案**，後面的§11記錄2026-08-02正式
design discussion結論。Value-level guidance本身仍未核准並已延後；核准的方向是新增
exact-frame S10R4，authority見
[S10R4 design](ductile-origami-warmstart/s10r4-stage1-exact-frame-operational-entry-design.md)。
本文件不得單獨被runner、verifier或report當成execution authority。

提出本草案的直接原因是：目前規則只要 residual gene 中任何一個 candidate value 沒有
fresh valid witness，就禁止整個 gene 接受 S11 Formocast guidance。這個規則安全但粗糙，
可能因一個極罕見 value 浪費同一 gene 其他已有 support values 的資訊。

## 1. 白話摘要

以 `DepthU = [32, 64, 128, 256, 512, 1024]` 為例：如果只有 `1024` 沒找到合法完整
config，現行規則會凍結整個 `DepthU` gene，連已有 witness 的 `32` 到 `512` 都不能由
Formocast 調整機率。

本草案建議改成 value-level bounded guidance：

- 已找到合法 witness 的 values 可以接受有上限的 Formocast guidance；
- 沒找到 witness、但也沒有不存在證明的 values 保留非零機率，且不得被 Formocast
  增權；
- 只有 complete absence proof 才能考慮把 value 從 guided arm 設為零；
- original YAML baseline/control 完整保持不變；
- 所有 mixture、floor、cap 與 sensitivity 規則必須在新的 S11 outcome evidence 前鎖定。

這個方案不是宣稱 `DepthU=1024` 不存在，也不是把它從 Ductile search space 刪掉；它只
限制模型在證據不足時能對該 value 施加多大的影響。

## 2. 中央名詞與資料流

### 2.1 Residual gene 與 candidate value

Residual gene 是 actual YAML 中一個尚未受既有 `group_0` positional weights 保護、可由
後續 factorization 個別建模的參數軸。Candidate value 是該軸列出的其中一個選項。
例如 `DepthU` 是 gene，`1024` 是其中一個 value。

Actual YAML 目前列出六個 `DepthU` values，但 `weights` 區塊只提供 `group_0` 的 9,918
筆 positional weights，沒有提供 `DepthU` 六個 values 各自的 GEKO 機率。因此把
`DepthU=1024` 設成低機率或零不是單純沿用 GEKO；那會是研究者新增的 sampling policy。

### 2.2 Fresh valid witness

Fresh valid witness 是在目前 checkpoint 預先鎖定的 source、YAML、seed 與 validator 下，
新產生且通過 Ductile/Tensile validation 的完整 joint config。一個 config 同時包含
`DepthU`、MacroTile、vector width 與其他設定；單獨在 YAML 看到 `1024` 不是 witness。

### 2.3 Support 三態

- `supported_witnessed`：至少一個 fresh accepted joint config 包含該 value。
- `support_unobserved`：固定 stochastic schedule 內沒有 witness，且沒有 complete absence
  proof。它支持「在該 sampling law 與 cap 中未觀察到」，不支持「不存在」。
- `support_proven_absent`：finite exhaustive search、sound constraint proof 或經獨立驗證的
  complete equivalent proof 證明沒有 accepted joint config。

S10R3 runner 產生完整 configs，pinned validator 產生 accept/reject evidence，support
classifier 產生上述狀態；S11 guidance builder 才消費這些狀態決定可否以及如何調整機率。

### 2.4 Baseline probability 與 guidance probability

Baseline probability `p0(v)` 是不使用新 Formocast guidance 時，candidate value `v` 在
原始 sampling semantics 下的機率。Guidance probability `p1(v)` 是實驗 treatment arm
實際使用的機率。兩者必須分開保存；改變 `p1` 不得回寫或冒充原始 YAML `p0`。

## 3. 現行設計與問題

S10R3 current authority 規定：任何 residual gene 只要有一個 value 不是
`supported_witnessed`，整個 gene 都沒有 S11 guidance eligibility；actual YAML baseline
保持不變。

這個 all-or-nothing 規則的優點是：

- fail closed，避免模型對缺少 mapping/support evidence 的 value 自由增權；
- eligibility 判斷機械且容易 audit；
- 不會把 stochastic zero 偽裝成 support absence；
- 降低研究者看到結果後只挑有利 values 的自由度。

但它有三個重要代價：

1. 一個極罕見 value 可以讓整個 gene 的已知資訊失效。
2. 「不得增權證據不足的 value」被擴張成「完全不得調整同 gene 的其他 values」。
3. S11 可能因 `無 guidable gene` 直接 negative，即使多數 values 已有合法 support 與可用
   mapping evidence。

因此現行規則是保守的 claim policy，不是由 Ductile 或 Formocast 技術限制必然導出的唯一
方案。

## 4. 建議的新 policy

### 4.1 Recommendation

將 S11 的 eligibility 單位由「整個 gene 必須 support-complete」改為「value-level
eligibility + gene-level bounded activation」。至少有兩個 `supported_witnessed` values
且通過 mapping、score coverage、stability 與 round-trip criteria 的 gene，可以成為
partially guided gene。

對每個 value：

| support state | guided component | final probability 約束 | 可否宣稱不存在 |
| --- | --- | --- | --- |
| `supported_witnessed` | 可使用 Formocast score | 可在預鎖 trust region 內增減 | 否 |
| `support_unobserved` | 不可由 Formocast score 增權 | 必須非零，且不得高於預鎖上限 | 否 |
| `support_proven_absent` | 不納入 guided component | 是否設零須由獨立 search-space authority 決定 | 只有 proof scope 內可以 |

`support_proven_absent` 不應自動改寫 baseline control。即使 guided arm 將它設零，原始
YAML/control 是否仍保留該 value 也要在新 contract 中明確區分。

### 4.2 建議的 trust-region mixture

推薦以 mixture 實作有限幅度的 guidance，而不是 hardcode 任意低機率：

```text
p1(v) = (1 - alpha) * p0(v) + alpha * gW(v)
```

其中：

- `v` 是一個 candidate value；
- `p0(v)` 是 baseline probability；
- `gW(v)` 是只在 `supported_witnessed` 集合 `W` 上正規化的 Formocast guidance
  distribution；`v` 不在 `W` 時 `gW(v)=0`；
- `alpha` 是零到一之間、在 outcome evidence 前鎖定的 guidance strength；越大代表
  Formocast 影響越強；
- `p1(v)` 是 treatment arm 最終使用的 probability，所有 values 合計必須等於一。

例如先只為說明取 uniform `p0(1024)=1/6` 且 `alpha=0.5`，如果 `1024` 是
`support_unobserved`，則：

```text
p1(1024) = (1 - 0.5) * (1/6) + 0.5 * 0 = 1/12
```

它從約 `16.7%` 降為約 `8.3%`，但不會歸零。這個數字只是公式示例，不是建議鎖定
`alpha=0.5`；正式值必須由 label-blind design discussion、existing S11 shrinkage semantics
與 sensitivity plan 決定。

### 4.3 為什麼不直接設成零

把 `support_unobserved` 設為零會把「固定樣本內沒看到」變成 operational pruning。這會：

- 可能排除極稀有但合法、甚至在特定 joint context 有價值的 configs；
- 改變 search-space sampling mass 與研究 estimand；
- 讓 post-observation policy 有 outcome-dependent relaxation 的風險；
- 需要新的 search-space/guidance identity、contract、lock 與 comparability 說明。

只有 complete absence proof，或使用者明確核准「研究 operational mass 而非完整 nominal
space」的新設計，才適合考慮 hard zero。

### 4.4 為什麼單一 value 機率仍不完整

Ductile validity 是完整 joint config 的性質。`DepthU=1024` 可能只在很窄的 MacroTile、
vector width 或其他組合下有效。Value-level mixture 是比 whole-gene freeze 更細緻的第一步，
但仍不等於完整的 conditional validity model。

若後續 evidence 顯示 marginal policy 仍大量產生 invalid configs，應另開研究比較：

- value-level bounded guidance；
- context-conditional guidance；
- constraint-aware proposal sampler。

不得在本 amendment 中把三者混成同一 estimand。

## 5. 建議的修改位置與 lineage

### 5.1 不回溯修改 S10R3

本提案不建議修改正在執行或已鎖定的 S10R3：

- fixed discovery schedule、seeds、target selection 與 support classification 不變；
- mapping/native conformance、GPU correctness、noise 與 outcome matrix 不變；
- S10R3 只回答自己的 entry boundary，結果保持 immutable；
- 不因本提案重標既有 outcome 或產生新的 S10R3 edge。

### 5.2 Prospectively 修改 S11

若核准，主要 amendment 應寫入 S11 design 與新的 durable frozen contract：

- 修改 eligible-gene criterion，允許 partially guided gene；
- 新增 value-level support mask；
- 鎖定 `alpha`、probability floor/cap、normalization 與 tie behavior；
- 鎖定 baseline/control 與 treatment distributions 的 identity；
- 更新 same-entropy shuffle，使 control 對應新的 treatment mass；
- 更新 outcome matrix，區分 `無 supported values`、`partial guidance unstable` 與真正的
  mapping failure；
- 新增 value-level round-trip、candidate-order、fault injection 與 replay tests。

這會改變 S11 scientific estimand：從「只評估 support-complete genes」變為「評估有界、
部分 support-aware guidance」。因此不得把它當成 ordinary implementation repair。

## 6. Evidence reuse 與 post-observation 風險

本提案是在已知 `DepthU=1024` 曾長時間 stochastic non-discovery 後提出，必須明示這是
post-observation design motivation。不能把同一份 evidence 同時當成選擇政策的理由，
又當成完全獨立的 confirmatory proof。

正式 design discussion 必須從下列方案選一個並說明 comparability：

1. S10R3 support states 只作 entry provenance；S11 使用自己預鎖、fresh、disjoint seeds 的
   occurrence/conditional frame 建立正式 value-level mask。
2. S10R3 support states 可機械重用，但 S11 對 mixture policy 使用 fresh sensitivity 與
   stability evidence；claim 限制為同一 source/YAML identity 下的 support-aware guidance。
3. 另建 confirmatory support checkpoint，避免 discovery evidence 同時負責設計與確認；
   代價是新增 CPU 成本與 checkpoint lineage。

在 reviewer 與使用者選定前，本草案不預設哪一方案已獲授權。

## 7. Controls、acceptance criteria 與 falsification

### 7.1 必要 controls

- Baseline arm 必須使用原始 YAML、candidate order、groups 與 weights，byte identity 不變。
- Guided arm 只能讀 model-only evidence；不得讀 real GFLOPS 或後續 outcome labels。
- `support_unobserved` value 不得因 Formocast score 取得高於 frozen cap 的 probability。
- Validity filter、mapping path、problem sizes 與 runtime semantics不得因 arm 改變。
- Same-entropy shuffle 必須以 treatment distribution 為來源建立 non-identity control。
- 所有 value-level probabilities、normalization residual 與 rejected joint configs 都要可 replay。

### 7.2 建議 acceptance criteria

核准 amendment 時應把下列條件轉成 machine-readable exact thresholds：

1. 每個 activated gene 至少有預鎖數量的 `supported_witnessed` values，且 score/mapping
   coverage 完整。
2. 每個 `support_unobserved` value 的 `p1(v)` 大於零，且不高於 frozen cap。
3. `sum_v p1(v)=1`，candidate order 與 probability-to-hook-cost round-trip exact parity。
4. Baseline arm identity 未變；guided arm 與 shuffle control 有不同且可重現的 identity。
5. 在預鎖 `alpha`/floor sensitivity grid 上，gene decision 與主要 model-only conclusion
   不因單一任意常數翻轉；若翻轉則降級為 inconclusive。
6. Joint-config invalid rate、effective accepted mass 與每個 value 的 realized frequency 完整
   報告，但不得用 real GFLOPS 回頭選 `alpha` 或 floor。

### 7.3 Falsification／停止條件

出現下列任一狀況，不得 seal S11 guidance：

- unobserved value 被增權或意外歸零；
- probability normalization、candidate order 或 hook-cost round-trip 不一致；
- mapping/score coverage 不足，必須猜值或以 proxy 替代；
- 合理 sensitivity grid 讓 eligible-gene decision 不穩定；
- baseline YAML、groups 或既有 weights 被 treatment implementation 改寫；
- support evidence 與 S10R3/S11 source、YAML、validator identity 無法對齊；
- 使用 real GFLOPS、GPU ranking 或後續 label 選擇 mixture constants。

## 8. 方案比較

| 方案 | 優點 | 主要風險 | 建議 |
| --- | --- | --- | --- |
| 維持 whole-gene freeze | 最保守、容易 audit | 浪費 witnessed values；可能無 guidable gene | 保留作 fallback/control |
| `support_unobserved -> 0` | 最省 invalid sampling | 把 non-discovery 變成 pruning；可能排除 rare valid support | 不建議，除非有 proof/新 estimand |
| 固定 unobserved 在 baseline mass | 不增權且最少改 baseline | 無法降低該 value 的 sampling waste | 可作保守 sensitivity arm |
| Value-level trust-region mixture | 利用 witnessed values並保留非零 floor | 需鎖定 `alpha`、重新定義 S11 estimand | **主要建議** |
| Context-conditional guidance | 最符合 joint validity | 複雜、形成另一個研究問題 | 建議另立後續 checkpoint |

## 9. 採用前需要的正式決策

這是一個會改 measurement boundary、selection policy 與 claim 的 material design issue。
採用前至少需要：

1. 兩個 fresh independent reviewers 依 `design-discussion` 做有界交互詰問；
2. 決定正式 evidence reuse 方案；
3. 決定 `alpha`、floor/cap、minimum witnessed-values、sensitivity grid 與 exact outcome
   matrix；
4. 使用者明確核准 amendment；
5. 在任何 S11 outcome evidence 前更新 governing design、machine-readable contract、tests、
   implementation hashes與 lock，並由 fresh auditor/verifier 檢查；
6. 若 S11 outcome evidence 已開始，停止 affected path，建立新 lineage 並依新 lock fresh
   rerun，不得事後套用。

這段是草案建立時的歷史狀態。後續雙reviewer deliberation已完成，但沒有核准本節的
value-level policy；正式結論見§11。

## 10. 建議 decision packet 摘要

- **問題：**一個 `support_unobserved` value 使整個 residual gene 失去 guidance eligibility，
  是否過度保守？
- **主要建議：**改用 value-level trust-region mixture；witnessed values 可有界調權，
  unobserved values 保留非零 baseline floor且不得增權。
- **拒絕直接 hard zero 的理由：**stochastic non-discovery 不是 absence proof，hard zero 會
  改變 operational search space 與 estimand。
- **不變事項：**S10R3 frozen execution/outcome、original YAML baseline、groups、existing
  weights、validator、mapping/native/GPU criteria與 S10 immutability。
- **主要變更：**S11 eligible-gene criterion、guided distribution、shuffle control、
  sensitivity 與 outcome matrix。
- **最大未知：**正式 value-level mask 是否重用 S10R3 states，或需要 fresh confirmatory
  support evidence。
- **目前狀態：**value-level方案`DEFERRED`；已核准的exact-frame方向見§11與S10R4
  design。

## 11. 2026-08-02 design discussion 決議

### 11.1 重新界定問題

兩位fresh independent reviewers先回答使用者提出的workflow問題：normal Ductile
workflow確實會先由validator接受完整config，再把solutions交給KernelWriter code
generation；以`errorTolerant=True`執行時，codegen失敗的solution會從operational pool
移除。因此：

- validator acceptance證明config進入Ductile-valid frame；
- KernelWriter success才證明它能進入當次operational generated-kernel pool；
- 兩者不等價；normal codegen attrition不表示validator defect；
- S10R3依已鎖定的first-required-failure rule停下是合法negative，但不能回答完整frame
  經normal filter後還剩多少可用configs。

### 11.2 Reviewer程序與共同結論

Reviewer A `/root/pipeline_rebaseline_reviewer_a`與Reviewer B
`/root/pipeline_rebaseline_reviewer_b`以相同current bytes與S10R3 direct evidence獨立
分析，完成兩輪cross-examination及一輪evidence-backed final，最後均`AGREE`：

1. S10R3保持immutable negative/null，不重標、不補跑。
2. 新增sibling S10R4；不重新draw、不啟動conditional stream，窄重用S10R3完整sealed
   512-chunk／262,144-draw frame的114個accepted distinct configs。
3. 對全部114 configs做兩次完整、隔離、無early-stop的normal-workflow codegen census。
   2/2 success是stable survivor；2/2 ordinary attrition保留在原frame denominator但排除
   survivor pool；任何discordance/exception/timeout/partial/identity drift都是
   `CHANGES_REQUIRED / not_evaluated`。
4. Census完成後才機械計算
   `mandatory = prelocked_candidate_atoms ∩ operational_codegen_witnessed_atoms`，並用
   frozen greedy selector建立`K=max(10,C_greedy)`, `K_max=20` fixture；禁止replacement、
   K+1、redraw或人工挑atom。
5. Fresh mapping A/B、native conformance、9 correctness cells及63 noise cells維持。
6. 唯一qualified edge是`S10R4:S1_ENTRY_GO_EXACT_FRAME -> S11`；claim只限exact sealed
   frame含bounded reproducible fixture，不宣稱general support或independent replication。
7. S11仍須用disjoint seeds建立fresh multiplicity-preserving `F_valid`，再經同一normal
   filter形成`F_codegen`；codegen rejects保留在`F_valid` occurrence-mass coverage分母，
   只對survivors mapping/scoring，conditional streams不pool進global denominator。
8. Whole-gene fail-closed eligibility保持；本文件原提議的value-level guidance延後，
   不在這次amendment採用。

### 11.3 使用者決定與authority effect

使用者在收到共同結論後明確選擇exact-frame S10R4並要求「Implement the plan」。因此
§11只作decision provenance；數值、outcome matrix、artifact boundary與execution
authority以S10R4 design、parent plan、durable contract及effective lock為準。沒有push
授權。
