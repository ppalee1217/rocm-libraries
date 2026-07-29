# Formocast-Factorized Ductile Guidance — Stage-Gated Internship Research Charter

> **文件角色：**研究 charter（研究問題、範圍、證據邊界與可宣稱結論的唯一權威）。
>
> **設計核准基線（2026-07-24）：**`stage_gated_roadmap_approved / pre_empirical / zero_lock / zero_completion`。當時十份checkpoint design已完成設計審查；S00尚未開始，其餘全部dependency-gated，且沒有active runtime protocol、effective lock、formal report或empirical outcome。
>
> **Current lifecycle：**以[active checkpoint index](ductile-origami-warmstart/README.md)與[experiment plan](ductile-origami-warmstart-experiment-plan.md)為準；本charter不重複維護易變的checkpoint current state。
>
> **檔名說明：**`surrogate-dse-plan.md` 是為維持既有連結而保留的歷史檔名。Stage 1–3不訓練 self-trained surrogate；主要模型是 **Formocast**。Learned residual只有 Stage 4 trigger與data gate同時通過才啟動。
>
> **執行規格：**所有sample counts、公式、門檻、seeds、artifacts與Stage 1–4 stop rules只以[ductile-origami-warmstart-experiment-plan.md](ductile-origami-warmstart-experiment-plan.md)為準。若兩份文件衝突，本charter決定研究scope／claim，experiment plan決定數值與checkpoint DAG。
>
> **Legacy override：**`ductile-origami-warmstart/legacy/`下的M00–M09全部是dead-protocol archive，統一為`legacy / design_authority:none / do_not_execute`。任何active-looking欄位都只保留為`historical_*`；不得重用其artifact、schema、hash、lock、registry、criterion、fixture或test。

---

## 0. 一句話定位與 north star

先在一個由 **frozen generated YAML** 鎖定的 gfx942 non-StreamK Ductile residual search space 中，檢驗：

> **Formocast 對 whole config 的 physics-based 效能訊號，經過 per-gene factorization 後，能否在保留既有 YAML groups／weights 的前提下，為尚未加權的 residual genes 提供額外的第 0 代（Gen0）候選品質；若不能，訊號究竟消失在哪一層？**

Stage 1 回答上述 **factorization／initialization mechanism**。只有它通過後，研究才依序擴張到：

1. **Stage 2 — short-horizon persistence：**Gen0 優勢能否保留到固定 10-generation horizon；
2. **Stage 3 — bounded held-out replication：**凍結的 guidance procedure 能否在兩個新 fixed-tile regimes重現；
3. **Stage 4 — conditional learned residual surrogate：**只有 predictor-specific failure、oracle-positive 且資料足夠時，才研究 learned residual能否補足 Formocast。

因此完整研究不是只做 Gen0，但也不是完整 GA speedup、production integration 或 deployment 專案。

白話說：Formocast 會替「整組 kernel 參數」打分，但 Ductile 現成 hook 只能分別替「每個 gene 的每個值」設定初始抽樣機率。本研究要回答的是：**把整體評分拆成各 gene 偏好後，還剩多少真的有用的資訊？**

---

## 1. Pivot 與 supersession record

### 1.1 被取代的舊命題

本檔舊版與舊實驗計畫曾同時包含：

- self-trained surrogate／Origami／Formocast 暖啟動 GA；
- Injection A 候選範圍 widening；
- non-StreamK 與 StreamK 雙 cohort；
- 完整 GA headroom、長 horizon、multi-tile 與 held-out confirmation；
- 「減少 tuning evaluations／端到端 speedup」作主要成果。

這些方向不是都沒有研究價值，而是**對短期 internship 過大，且其中數項已與核心團隊既有或正在規劃的工作相鄰**。繼續把它們包成單一主線，會讓研究問題、baseline 與可宣稱結果失真。

### 1.2 促成 pivot 的新證據

1. **GEKO 已有 problem-dependent Gen0 heuristic**
   - `origin/users/pkamd/geko_pr` 的 pinned commit `ce7b5e7754a342c464cd0470a9a3c9009b9a8fe4` 中，`config_sections_generator.py::_build_ductile()` 已依 problem sizes、TilesPerCU、granularity 與 GSU 產生 `group_0` costs，寫入 Ductile `weights`。
   - 這證明「problem-dependent initial guidance」已存在；但 branch code 存在**不等於**目標 gfx942 workflow 已部署。

2. **Formocast whole-config pre-screen 已存在**
   - `SolutionIterator.cpp` 已用 Formocast ranking 與 `PredictionThreshold` 決定哪些 solutions 進入 benchmark。
   - 因此本研究不能再宣稱「首次用模型降低 tuning 成本」。

3. **核心團隊另有 active GA 改善項目**
   - [AIHPBLAS-2810](https://amd-hub.atlassian.net/browse/AIHPBLAS-2810)：Open/P1，size sampling 與 multiple-size iteration allocation。
   - [AIHPBLAS-2791](https://amd-hub.atlassian.net/browse/AIHPBLAS-2791)：Open/P1，hierarchical／iterative MT/CMS tuning。
   - 它們不是本研究的 factorized residual guidance，但構成必須避開的 scope boundary。

4. **舊完整驗證超出目前 access 與時間條件**
   - 目前尚未由本研究 artifact 證明可用 gfx942 slot、actual generated YAML 與完整 Formocast mapping。
   - 在這些 gate 未過前，24 shapes、multi-seed confirmation 與 deployment claim 都不合理。

### 1.3 新決策

本研究保留「physics model 能否幫助 Ductile initialization」的核心興趣，並採 stage-gated 擴張：

- Stage 1：一個 gfx942、non-StreamK、單一 dtype/layout 的 bounded residual space；
- Stage 2：同一 development cluster 的 10-generation persistence；
- Stage 3：兩個預註冊新 clusters 的 bounded replication；
- Stage 4：嚴格條件式 predictor-substitution branch；
- 每一階段都有獨立 stop、failure 與 mentor-facing claim，不把後續 stages 當無條件承諾。

### 1.4 決策產生方式

2026-07-24 依 `/design-discussion` 進行：

1. 兩個 fresh GPT-5.6 Sol subagents 以相同 prompt 獨立提案；
2. 三輪交互詰問，處理文件 authority、sampling estimand、leakage、oracle 與 Gen0 重現性；
3. 修正 set-backed population 不應依賴 iteration order 的問題；
4. 兩方對同一份 candidate consensus 明確 `AGREE`。

代理共識是降低盲點的 process metadata；技術權威仍來自 repo code、frozen artifacts、真實 benchmark 與預註冊 protocol。

### 1.5 Scope expansion review

同日再次依 `/design-discussion` 檢討「七日 MVP 是否被誤寫成整個 internship 終點」：

1. 兩個 fresh subagents 獨立提出完整 staged roadmap；
2. 交互詰問 5 vs 10 generations、fresh-seed conditioning、held-out denominator 與 surrogate data floor；
3. 統一採用 Stage 1 → Stage 2 → Stage 3 主線，以及 oracle-positive 才能啟動的 Stage 4；
4. 兩方對修正後共識明確 `AGREE`。

這次修正不推翻 Stage 1 嚴謹性，而是把它恢復成**第一道 gate**，不再當成整份研究的天花板。

### 1.6 From-scratch governance reset

同日的最新bundle-level`design-discussion`對十個checkpoint做完整交叉詰問，兩位reviewers對同一份S00／S10–S13／S20／S30–S31／S40–S41方案明確`AGREE`。本次reset：

- 退役舊`protocol/`而不做migration；
- 一次建立十份`approved` design，不保留planned-but-missing slots；
- 採strict S00→S10→S11→S12→S13→S20→S30→S31主線與S12/S31→S40→S41條件分支；
- 將design、execution、checkpoint、scientific outcome與lock狀態分離；
- 把technical PASS與formal report、closeout、isolated commit明確分開；
- 將S41固定為單一ridge residual analysis與cluster-held-out strict gates。

各checkpoint的objections、採納／捨棄方案、理由與雙方`AGREE`保存在其active design。這是design approval，不是effective lock或empirical outcome。

### 1.7 Post-closeout Stage 1 entry recovery

2026-07-26，S10已durable closeout為frozen raw-boundary fixture下的
`negative / S1_ENTRY_BLOCKED / edge=null`後，唯讀diagnostics確認兩個新的
measurement-design問題：

- 十組fixture未先對齊Ductile operational `valid_fn` accepted support；
- non-finite-only Formocast rejection沒有區分finite early-terminate sentinel與
  whole-cohort runtime threshold queue。

兩個fresh GPT-5.6 Sol/xhigh reviewers依`design-discussion`獨立判讀、交換完整
立場並交互詰問，最後共同核准獨立S10R1 checkpoint。S10及其negative保持
immutable；S10R1只在相同source pins、byte-identical YAML、space／groups／weights、
三sizes、correctness與noise要求下修正selection及measurement semantics。這是當時的
approved design；後續A32已取消其execution，沒有產生scientific edge。

### 1.8 A32 diagnostic cancellation與S10R2

2026-07-28，使用者依append-only S10R1 governance chain的A32 event核准在safe
boundary停止S10R1：

- operational state固定為`cancelled / BLOCKED`，scientific outcome為
  `not_evaluated`、edge為`null`，不是`CHECKPOINT_COMPLETE`；
- 不建立S10R1 scientific report；generation 0／1只作diagnostic lineage，
  所有empirical／repair artifacts禁止重用；
- stochastic non-discovery（包含DepthU=1024 diagnostic）不證明support absent，
  也不是scientific inconclusive；
- 新建sibling S10R2，在actual S10 pins／YAML／groups／weights／三sizes不變下，
  先做CPU validity-only support classification，再分離exact-ten mapping與
  deterministic sentinel/helper conformance；
- 只有post-audited `S10R2:S1_ENTRY_GO`可進S11。S11–S41 roadmap、criteria、
  numerical timeboxes與claim ladder全部保留。

Execution治理以commit
`b0561d2c9216a58a9d71b8e839c47efaa51f9c00`為floor；S10R2是R2 standalone
tranche／closure，後續tranches為S11+S12+S13、S20、S30+S31、S40+S41。這只改
authority／orchestration，不改scientific gates。

### 1.9 A33 identity-only diagnostic retirement

2026-07-28，使用者要求只保留新版研究真正需要的內容並清除S10R1 bulk artifacts。
兩位fresh reviewers完成一輪交互詰問並共同`AGREE`：

- S10R1約34 GB ignored run tree與19個untracked implementation／protocol／test paths
  對S10R2／S11沒有合法consumer，且明文禁止作gate evidence；
- current S10R1文件壓縮為取消tombstone，A30–A32、source／YAML／L0／selection
  identities、resource known／unknown與清理稽核由
  [retirement manifest](ductile-origami-warmstart/retirements/s10r1-diagnostic-retirement.json)
  保存；完整舊protocol只留在Git history；
- physical bytes可依exact allowlist退休；immutable的是lifecycle、outcome、edge與
  digest-level lineage，不是bulk copies；
- cleanup不改S10R1的`cancelled / not_evaluated / edge=null`，也不reset任何歷史
  resource消耗。

S10R2在retirement post-audit及durable resource relock前保持operational
`BLOCKED / not_evaluated / edge=null`。本次沒有降低任何scientific workload、
threshold、gate、claim或downstream dependency。

### 1.10 A34 prospective resource boundary

2026-07-28，使用者要求resource relock先由`design-discussion`形成統一共識，再以
`implement-verify-loop`執行S10R2。兩位fresh `gpt-5.6-sol / xhigh` reviewers
`/root/s10r2_next_plan_a`與`/root/s10r2_next_plan_b`完成獨立審查、一輪
cross-examination與一輪final positions，兩方均`AGREE`：

- historical resource record不重寫：cutoff
  `d66edf7ac81cb76825b988e1ea9a65264dfeb0f6`前的3151 chunks、
  threads`>=10`、repairs`>=11`與其餘`UNKNOWN`全部保留；
- authority commit post-audit後，只向前建立`T-S10R2`與reserved
  `T-S1-MECHANISM`各5 new threads／3 new repairs的enforcement counters；
  S13仍受R1最多2 repairs，internal edges與new roots都不再reset；
- S10R2→S13共享新的prospective 7 hands-on days、最多1.4 pre-empirical days與
  5 GiB transient ceiling；
- 先做不接觸actual validity/support、Formocast、GFLOPS、correctness/noise labels或
  S10R1 artifacts的outcome-blind calibration，再把具單位wall／CPU／GPU caps、
  confirmed allocation與buffer seal進durable contract／lock；
- final numeric relock與preflight完成前，S10R2仍是
  `BLOCKED / not_evaluated / edge=null`。

本決策只修resource authority，不改research question、scientific criteria、
samples、sizes、DAG、claim或downgrade gate；A33釋放的physical capacity仍不是
historical accounting reset。

### 1.11 A36 resource-accounting materiality amendment

2026-07-29，使用者明確要求不要讓對整體科學實驗沒有實質影響的resource-accounting
缺口阻礙研究進度。此R3 post-label authority將resource telemetry重新釐清為
operational safety／planning control，而不是默認scientific estimand：

- 只有direct evidence顯示或實質指向frozen cap exceed、unsafe continuation、
  label-dependent stopping／selection、required workload不完整或scientific evidence
  不可驗證時，resource-accounting finding才是blocking；
- fixed workload完整、schedule／append-only evidence chain通過、headline result由
  independent process重現、沒有label-driven stopping且沒有direct cap-exceed evidence
  時，缺少fine-grained或parent-process telemetry只記non-blocking technical caveat；
- 不得只為完善資源記帳重跑outcome-bearing workload；後續在真正
  resource-critical的run中prospective改善telemetry；
- 本amendment不能創造或改寫scientific outcome／edge。S10R2的
  `inconclusive / FT-INCONCLUSIVE / edge=null`仍不啟動S11。

---

## 2. 研究問題與假設

### RQ1 — Whole-config model signal 是否存在？

在 frozen residual space 與指定 sizes 上，Formocast ranking 是否和真實 GFLOPS ranking 有足夠一致性，值得繼續做 factorization？

### RQ2 — Factorization 保留了多少訊號？

將 whole-config model benefit 邊際化成 per-gene probabilities 後，是否仍能提高真實高品質 config 的 prior mass？

### RQ3 — 是否有超越 existing heuristic 的增量？

在所有 existing YAML `group_i` 結構與 weights 完全保留時，只對 ungrouped、currently-unweighted residual genes 加 Formocast guidance，是否優於：

- existing guidance 本身；
- 相同 entropy、但 candidate labels 被打亂的 control？

### RQ4 — Offline prior 能否穿過真實 sampler？

即使 offline factorized prior 對準高品質區，經過 validity rejection、population 內去重與有限 `pop=64` 抽樣後，actual Gen0 是否仍有方向性改善？

### RQ5 — Gen0 訊號是否具有短期 persistence？

在同一 development cluster、固定 candidate space 與五個全新 paired seeds 下，Formocast residual guidance 是否能改善 Gen0 後固定 10 generations 的 quality-vs-complete-evaluations，而不被 existing guidance迅速追平？

### RQ6 — Frozen procedure 是否能 bounded replication？

不改 eligibility、hyperparameters、factorization、metrics 與 gates，只讓 label-blind algorithm在新 cluster產生自己的 genes／weights時，能否在兩個預註冊 held-out fixed-MT／MTDU regimes重現 short-horizon directional benefit？

### RQ7 — Predictor failure 是否可由 learned residual補足？

只有當 cross-fitted oracle證明 factorized main effects存在、但 Formocast predictor未捕捉時，cluster-held-out learned residual是否能縮小與 oracle的差距？

### 假設階梯

> 在至少一個 bounded gfx942 non-StreamK residual space 中，Formocast whole-config signal 能經 factorization 與 actual Ductile Gen0 sampler 保留，並提供超越 existing guidance 與 same-entropy shuffled control 的候選品質訊號。

若上述 Stage 1 假設成立，再依序檢驗：

- 訊號可保留到10-generation early-search horizon；
- 凍結後 procedure 可在兩個新 regimes重現；
- predictor-specific failure可由 learned residual補足。

每一層都是獨立假設，不是預期結果；上層失敗時不得直接沿用下層 claim。

---

## 3. 機制與模型角色

```mermaid
flowchart LR
  yaml["Frozen generated YAML\nspace / groups / weights / reduce_fn"]
  draw["Valid accepted occurrences"]
  model["Formocast whole-config scores"]
  marginal["Residual-gene factorization"]
  weights["Existing groups preserved\n+ residual weights"]
  gen0["Actual Ductile Gen0\npop=64"]
  judge["Real GFLOPS judgment"]

  yaml --> draw --> model --> marginal --> weights --> gen0 --> judge
  yaml --> weights
```

### 3.1 Formocast

- **Primary physics model**。
- 適用 non-StreamK。
- 可見較多 Tensile-specific metadata，因此有機會區分 fixed tile 後的 residual configs。
- 「看得到欄位」不代表 ranking 必然準；必須通過 model coverage、sensitivity 與 real-score gate。

### 3.2 Origami estimation

- 只作 sensitivity／ranking reference。
- estimation model 忽略多個 `tensile_params_t` backend-specific fields；fixed tile 後可能缺乏 residual-gene 辨識力。
- 本輪不替 Origami 建正式 treatment arm。

### 3.3 GEKO／actual YAML guidance

- 所有 existing `group_i` 結構、candidate order 與 YAML-provided weights 都是受保護 baseline。
- 本研究不拆 group、不重排、不覆寫 existing weights。
- Formocast 只可新增 manifest 明列的 ungrouped、currently-unweighted residual-gene entries。

### 3.4 Self-trained surrogate

- 不是 Stage 1–3 treatment，只保留為嚴格條件式 Stage 4。
- 原因是短期內還沒有足夠 gfx942 labels、shape-level holdout 與 leakage 防線。
- 只有 Formocast predictor失敗、cross-fitted oracle顯示 factorized main effects存在，且四-cluster data floor可滿足時，learned residual才成為有證據支持的分支。

### 3.5 Guidance 與 judgment 分離

- Formocast 與 model-only samples只能建立 guidance。
- 真實 GFLOPS 只用於 D5 judgment、cross-fitted diagnostic oracle 與 D6 evaluation。
- 一旦 real-score pool 建立或解封，gene list、hyperparameters 與 weights 都不得修改；否則必須開新 protocol version 與獨立 judgment pool。

---

## 4. Scope 與 non-goals

### 4.1 In scope

- gfx942／MI300X。
- non-StreamK。
- 一種由 frozen YAML 決定的 dtype/layout。
- 同一 frozen search space 中兩或三個 sizes。
- Whole-config Formocast ranking。
- Per-gene factorization。
- Existing heuristic + residual guidance。
- Stage 1：`n_gen=1` actual Gen0 directional pilot。
- Stage 2：同一 development cluster、`n_gen=10` 的 short-horizon persistence。
- Stage 3：兩個新 fixed-MT／MTDU clusters 的 bounded held-out replication。
- Stage 4：oracle-positive、data-sufficient 時的 learned residual predictor analysis。
- Failure mechanism localization。

### 4.2 Explicitly out of scope

- Injection A、候選 widening／hard pruning。
- StreamK cohort。
- 跨 codegen／跨架構 transfer。
- Fitness、mutation、selection、survival 或 GA core 修改。
- Kernel、codegen、IR 修改。
- Natural-stop formal panel、basin 或完整 convergence study。
- 24-shape／production-scale multi-cluster confirmation。
- Production deployment、owner adoption 或 merge 建議。
- Regression tier policy、tile-selection policy 或 Origami heuristic 修改。

### 4.3 Stage-gated timeboxes

- Stage 1：exact hard cap為最多七個hands-on工作日。
- Stage 2：target四日、exact hard cap五日。
- Stage 3：exact hard cap七日。
- Stage 4：exact hard cap五日，且不是必跑stage。
- Target與hard cap都不是完成承諾；entry resource preflight無法證明完整panel、
  report與buffer可在剩餘cap內完成時必須停止。
- 每個 stage entry前必須確認能完成完整 arms／seeds／clusters，並保留至少一個 report工作日與 failure buffer。
- 資源不足時輸出 partial／inconclusive，不靠縮 seeds、arms、horizon或clusters保留原 claim。
- D1–D2 access／artifact／mapping gate 未過：停止 empirical work，不以 CPU-only 結果冒充效能研究。
- 同stage／gate lineage的wall-time、CPU/GPU time、storage、throughput samples、
  pre-empirical engineering、repair rounds與fresh role threads跨generation、
  successor、sibling、replacement與new root累計；沒有human明列authority不得reset。
- Governance baseline `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`要求
  pre-empirical engineering最多20% stage cap、首1% throughput後重估；projection
  超過2倍或frozen budget exceed時safe-boundary pause。

---

## 5. 與核心團隊工作的邊界

### 5.1 Active scope boundaries

- [AIHPBLAS-2810](https://amd-hub.atlassian.net/browse/AIHPBLAS-2810)：size sampling、minimum set、multiple-size iteration allocation。
- [AIHPBLAS-2791](https://amd-hub.atlassian.net/browse/AIHPBLAS-2791)：hierarchical／iterative MT/CMS tuning。

本研究固定這些搜尋策略，不重作其 intervention；只問 residual-gene physics prior 是否能穿過現成 Gen0 hook。

### 5.2 Existing／historical related work

- [AIHPBLAS-1922](https://amd-hub.atlassian.net/browse/AIHPBLAS-1922)：Done，`PredictionThreshold`。
- [Tuning with Formocast](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1308395122)：TensileLite whole-config model-assisted tuning 流程。
- [Difference between Origami and Formocast](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304199634)：Formocast／Origami 模型角色與 integration。
- [AIHPBLAS-2572](https://amd-hub.atlassian.net/browse/AIHPBLAS-2572)：Discarded，Ductile tile prioritization during initialization。
- [AIHPBLAS-2864](https://amd-hub.atlassian.net/browse/AIHPBLAS-2864)：Discarded，MTTuning initial population sampling flexibility。

Discarded 不等於 active plan；Done 不應由本研究重新實作。

### 5.3 Bounded absence

- [NA GEMM Tech Exchange/Sync](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1694009253)、[Q2 Roadmap](https://amd.atlassian.net/wiki/spaces/AIG/pages/1687743031) 與 [meeting 摘要](../meeting_notes/GEMM-Optimization-Roadmap-Origami-Tile-Selection-摘要.md) 在已檢查內容中未明列「Formocast whole-config score → residual-gene factorization → Ductile Gen0」。
- 這只能寫成「在已審查 artifacts 中未明列」，不能推導「核心團隊絕對沒有人做」。

---

## 6. Stage-gated internship roadmap

數值與公式只以[experiment plan](ductile-origami-warmstart-experiment-plan.md)為準。

```mermaid
flowchart TD
  s1["Stage 1\nGen0 mechanism"]
  s2["Stage 2\n10-gen persistence"]
  s3["Stage 3\n2 held-out clusters"]
  s4["Stage 4\nlearned residual"]
  report["Mentor report"]
  block["Blocker memo"]

  s1 -->|"mechanism positive"| s2
  s1 -->|"blocked"| block
  s1 -->|"predictor failure + oracle positive + data gate"| s4
  s1 -->|"other negative / inconclusive"| report
  s2 -->|"persistence positive"| s3
  s2 -->|"washout / regression / inconclusive"| report
  s3 --> report
  s3 -.->|"predictor heterogeneity + oracle positive + data gate"| s4
  s4 --> report
```

### 6.1 Stage 1 — Gen0 mechanism

- 保留現有七日 D1–D7 exact protocol。
- 回答 model signal、factorization 與 actual Gen0。
- 只有 `D6_MECHANISM_POSITIVE` 可進 Stage 2。

### 6.2 Stage 2 — Short-horizon persistence

- 同一 development cluster，G／F／S 三臂。
- 固定 `n_gen=10, period=0`。
- 五個全部 fresh paired seeds；Stage 1 seeds只作 selected-seed diagnostic。
- Primary 是 Gen0 後、事前固定 complete-evaluation support上的 best-so-far log-quality AUC。
- 第五代只作 blinded operational checkpoint；不依結果決定是否延長到第十代。

### 6.3 Stage 3 — Bounded held-out replication

- 兩個預註冊新 fixed-MT／MTDU clusters，每 cluster兩個 sizes。
- Stage 1／2 cluster是 development，不進 held-out denominator。
- Guidance algorithm與所有 thresholds凍結；只允許 label-blind deterministic output隨 cluster改變。
- 每 cluster先做 D5-equivalent audit，通過才跑10-generation G／F／S。
- 兩個 clusters都保留在成功分母，不能只報通過者。

### 6.4 Stage 4 — Conditional learned residual

只在以下條件同時成立時啟動：

- Formocast predictor failure；
- cross-fitted oracle穩定支持 factorized main effects；
- existing／shuffled controls顯示仍有可學增量；
- 已有至少三個合格 clusters，且能在五日 cap內取得一個 prospective sealed fourth cluster。

預設只做 cluster-held-out ranking／factorization，不跑 actual GA。若不足四 clusters，直接記 `FT-SURROGATE-DATA-INSUFFICIENT`。

任何 stage失敗都停止該 branch；只有明確的 oracle-positive predictor failure可轉 Stage 4。不得靠降低門檻、改 genes或重調 weights重用同一 judgment pool。

---

## 7. Canonical failure taxonomy

以下 ID 與語意由本 charter 唯一定義；experiment report 必須選用，而不可自行改名。

### `FT-BLOCKED-ACCESS`

無已排定 gfx942 slot、可信 frozen YAML 或可執行環境。這是 blocker，不是模型失敗。

### `FT-BLOCKED-MAPPING`

必要 metadata 只能靠猜、sentinel 未解析、candidate order／field parity 無法確認。這是 mapping blocker。

### `FT-BLOCKED-CORRECTNESS`

在frozen valid corpus、source／mapping identity、environment與measurement contract都
完整時，locked generate、compile、smoke或nonzero correctness可重現失敗。這是
correctness entry blocker／scientific negative，形成`S1_ENTRY_BLOCKED`與
`edge=null`；若根因是harness、adapter、schema或path substitution defect，必須走
`CHANGES_REQUIRED`，不得誤用本ID。

### `FT-MODEL-RANK`

Whole-config Formocast ranking 無法通過 bounded real-score gate。結論只限該 frozen regime。

### `FT-MODEL-MARGINAL`

Whole ranking 有訊號，model marginals 失敗，但 cross-fitted oracle marginals成功：模型 attribution／marginalization 沒有保留真實 main effects。

### `FT-HOOK-EXPRESSIVENESS`

Cross-fitted oracle factorized marginals也失敗：真實優勢可能主要來自 epistasis，現有獨立 per-gene hook 表達力不足。

### `FT-PLUMBING`

Target weights 與 actual realized frequencies／canonical proposal set 不一致，或 `SearchSpace.map` 與 weight vector 對齊錯誤。

### `FT-GEN0-MECHANISM`

Sampler realization 正常、offline gate也通過，但 actual Gen0 品質沒有改善。這是有限抽樣或 Gen0 mechanism failure，不自動歸因 plumbing。

### `FT-HEURISTIC-SATURATION`

Formocast residual guidance 不勝 existing YAML guidance／GEKO branch proxy：既有 heuristic 已捕捉主要訊號，額外模型沒有增量。

### `FT-ENTROPY-ONLY`

Formocast 不勝 same-entropy shuffled：效果只能歸因於集中機率，而非 physics direction。

### `FT-WASHOUT-UNTESTED`

Stage 1 Gen0 有改善，但 Stage 2 尚未完成。這是暫態狀態，Stage 2結束後必須改成更具體結果。

### `FT-PERSISTENCE-WASHOUT`

Stage 1 Gen0 positive，但 Stage 2 的 post-Gen0 AUC、late retention或 Formocast-vs-shuffled gate失敗。

### `FT-SHORT-HORIZON-REGRESSION`

Stage 2 early-search AUC正向，但第十代獨立重測品質未通過 noise-derived non-inferiority。

### `FT-EVALUATION-SUPPORT`

Stage 2／3 formal run無法達到事前鎖定的 complete-evaluation support，且不符合 technical replacement規則。

### `FT-REGIME-HETEROGENEITY`

Stage 3兩個 held-out clusters結果不一致；只能報適用邊界，不能平均成 replication success。

### `FT-BOUNDED-REPLICATION`

Stage 3凍結 procedure在兩個預註冊 clusters均重現 short-horizon directional benefit。

### `FT-SURROGATE-DATA-INSUFFICIENT`

Stage 4少於四個合格 independent clusters，或 prospective fourth cluster無法在 cap內取得。

### `FT-SURROGATE-NO-GAIN`

Nested cluster-held-out learned residual未穩定優於 Formocast／shuffled，或未縮小與 oracle的差距。

### `FT-INCONCLUSIVE`

Noise、support、coverage、importance ESS、unique configs 或兩-regime evidence 不足。不得用 point estimate 強判。

---

## 8. Claim ladder、success 與 falsification

### 8.1 Stage 1 — Gen0 mechanism

只有全部 pre-registered gates 通過，才能寫：

> 在指定 frozen YAML、gfx942 non-StreamK、一種 dtype/layout、指定 sizes、bounded real-score pool 與三個 paired sampler seeds 下，Formocast-factorized residual prior 對 Gen0 candidate quality 提供超越 existing guidance／proxy 與 same-entropy shuffled control 的方向性增量，值得進一步驗證。

### 8.2 Stage 2 — Short-horizon persistence

只有 Stage 2 gate通過，才能寫：

> 在同一 development cluster與五個全新 paired seeds下，Formocast-factorized initialization的增量保留到固定10-generation horizon，並改善 Gen0後 early-search quality-vs-complete-evaluations，且 final quality未超出 noise-based退步界線。

這仍不是 system speedup或 convergence confirmation。

### 8.3 Stage 3 — Bounded replication

只有兩個預註冊 held-out clusters都通過，才能寫：

> 凍結後的 guidance procedure在兩個新 gfx942 non-StreamK fixed-tile regimes中重現方向性 short-horizon benefit。

必須使用「bounded replication」，不得寫成 MI300X workload generalization。

### 8.4 Stage 4 — Predictor substitution

只有 prospective fourth-cluster或合格 nested cluster-held-out結果通過，才能寫：

> Learned residual predictor在 cluster-held-out judgment中，比 Formocast更能恢復 oracle顯示可 factorize的效能訊號。

### 8.5 允許的負向結論

負向結果必須指出 §7 中的層次，例如：

- 模型 ranking 不足；
- factorization 丟失 main effect；
- epistasis 超出 hook 表達力；
- GEKO heuristic 已飽和；
- 模型效果只是 entropy concentration。

「模型沒用」不是合格結論。

### 8.6 禁止的措辭

本 internship roadmap 不得宣稱：

- 加速 Ductile tuning；
- 改善 GA convergence；
- production／deployment ready；
- 對 MI300X workloads 一般化；
- 勝過 native `PredictionThreshold`；
- 跨架構有效；
- owner／核心團隊應採用。

### 8.7 Study modes 對 claim 的限制

- `ready_actual_yaml_guidance`：可回答完整 bounded RQ，但仍不得稱 deployed incumbent，除非另有部署證據。
- `degraded_branch_proxy_only`：只能寫 branch-proxy mechanism evidence；完整 RQ 記為 `not evaluated under actual YAML`。
- `blocked_no_comparable_heuristic`：不可判 `FT-HEURISTIC-SATURATION`。

---

## 9. Evidence boundary 與 open dependencies

尚未由 empirical artifacts 解決：

- actual generated YAML 的位置、hash、來源與 generator revision；
- actual weights 是否存在及其 provenance；
- fixed MT 還是 MTDU、DepthU 是否自由；
- dtype/layout 與可共用同一 search space 的 sizes；
- Formocast mapping coverage、score ties 與 throughput；
- `F_valid` 在 cap 內的 unique catalog 大小與 multiplicity concentration；
- gfx942 slot、measurement noise 與可用 GPU-hours；
- branch proxy 是否能只改 weights、不改 candidate space；
- Stage 2十代完整 panel的實際 evaluation／GPU成本；
- 兩個同 dtype/layout、可預註冊且真正不同的 held-out clusters；
- Stage 4是否已有三個具 inclusion metadata的合格 clusters；
- 剩餘 internship工作日是否足以完成下一個完整 stage；
- 核心團隊是否有未公開的相同 prototype。

所有未解項都必須由 D1–D2 contract 決定；不得由舊文件 defaults 或研究者猜測代填。

---

## 10. Active checkpoint authority 與 legacy archive

唯一active入口是[checkpoint index](ductile-origami-warmstart/README.md)。2026-07-24設計核准時，十份design全部是`approved / lock_state:absent / scientific_outcome:not_evaluated`；只有S00是`execution_status:not_started`，其餘都是`gated`。後續current lifecycle只由active index與experiment plan的verified closeout projection維護。

Current strict scientific DAG與administrative recovery prerequisites：

```text
S00 -> S10 [terminal negative; edge=null]
  \          \
   +----------+-- administrative/provenance only --> S10R2
                                                     |
                                                     +-- S1_ENTRY_GO --> S11 -> S12 -> S13 -> S20 -> S30 -> S31
                                                                                 \                         \
                                                                                  +---- conditional ------> S40 -> S41

S10R1 [A32 cancelled; A33 identity-only tombstone; edge=null; reuse forbidden]
```

S00／S10到S10R2的關係不是scientific outgoing edge。S10R1是sibling diagnostic
record，不是S10R2 parent或evidence source；A32固定它為
`cancelled / not_evaluated / edge=null`，A33只退休physical artifacts。
S10R2 negative、inconclusive、
`CHANGES_REQUIRED`或未完成都不會啟動S11。

M00–M09移入`ductile-origami-warmstart/legacy/`，只保留歷史正文：

- [M00](ductile-origami-warmstart/legacy/m00-study-contract-observability-design.md)
- [M01](ductile-origami-warmstart/legacy/m01-step0-integration-gate-design.md)
- [M02](ductile-origami-warmstart/legacy/m02-guidance-plumbing-design.md)
- [M03](ductile-origami-warmstart/legacy/m03-exp0a-cold-headroom-design.md)
- [M04](ductile-origami-warmstart/legacy/m04-exp0b-widening-gate-design.md)
- [M05](ductile-origami-warmstart/legacy/m05-expc-ranking-oracle-design.md)
- [M06](ductile-origami-warmstart/legacy/m06-exp1-injection-b-design.md)
- [M07](ductile-origami-warmstart/legacy/m07-exp2-a-safe-b-factorial-design.md)
- [M08](ductile-origami-warmstart/legacy/m08-exp3-multishape-design.md)
- [M09](ductile-origami-warmstart/legacy/m09-overall-confirmation-design.md)

它們統一是`design_authority:none / lifecycle:legacy / do_not_execute`。Successor只表示主題關聯，不表示artifact、criterion、schema、hash、lock、registry、fixture、test或outcome migration。

---

## 11. Document、lock、report 與 closeout lifecycle

- 本charter是研究scope／claim唯一權威。
- [Experiment plan](ductile-origami-warmstart-experiment-plan.md)是數值、DAG、criteria與stop rules唯一權威。
- Checkpoint design只給maximum boundary與evidence binding；future planning必須縮成exact whitelists。
- Governance baseline
  `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`是risk、resource、tranche與closure
  floor，但不能改scientific authority。
- Future outcome evidence前必須先建立durable machine-readable frozen contract、
  驗證human/machine parity並seal effective lock。
- S10 hard access／artifact／mapping blocker才使用：
  - `ductile-origami-warmstart/reports/gen0-factorization-blocker-memo.md`
- S10R1沒有scientific report；current bytes只保留A32 cancellation tombstone與A33
  retirement manifest。
- S10R2唯一formal report是
  [S10R2 Stage 1 support-aware entry report](ductile-origami-warmstart/reports/staged/s10r2-stage1-support-aware-entry-report.md)。
  S10R2 technical verification為`PASS`，scientific outcome為
  `inconclusive / FT-INCONCLUSIVE / edge=null`；不覆寫S10 report，也不啟動S11。
- S40 data insufficiency是formal scientific negative，寫入`reports/staged/s40-stage4-activation-report.md`；不建立data-insufficiency blocker memo。
- `skipped_by_gate`／`not_activated`由上游report與closeout記錄，不建立自己的report或commit。
- Internal positive scientific gate使用compact durable record並在同tranche繼續；
  internal terminal negative／inconclusive產生planned report；final gate report整合
  prior records。Tranches固定為S10R2、S11+S12+S13、S20、S30+S31、S40+S41。
- Positive、negative與inconclusive在evidence integrity完整時都需durable outcome
  closure、parent update、`CLOSEOUT_ACK`、isolated commit與post-commit audit。
- Technical`PASS`只是`VERIFIED_PENDING_CLOSEOUT`；完成全部closeout後才是`CHECKPOINT_COMPLETE`。
- `live_run_state`與`committed_projection_state`分離；只有closure commit與
  post-commit audit後才更新後者。
- 現在不建立空白report、placeholder lock、fake hash或compatibility stub。

任何`DEGRADED_PROXY`、two-size／reduced-regime、H5 pilot、single-cluster pilot或其他縮減workloads/runs/seeds/metrics/validation/acceptance/scope的方案，必須先產生decision packet並停在`blocked-awaiting-user-decision`。Diagnostic partial run不會完成checkpoint或解鎖下游。

---

## 12. 設計核准時的下一步與 current lifecycle

2026-07-24設計核准時不是執行Stage 1 D1–D2；第一個可開始的checkpoint是S00。
2026-07-25 authority amendment與後續S00／S10 durable closeout保持有效。
2026-07-26 R12曾核准S10R1，但2026-07-28 user-authorized A32已在safe boundary取消
該execution，沒有scientific outcome或edge。S10R2完成固定support discovery後，
exact-ten cover需要18 configs，故terminalize為
`inconclusive / FT-INCONCLUSIVE / edge=null`。A36只把non-material resource
accounting缺口降為technical caveat，不改scientific result。Closure commit與
post-audit完成後，S10R2 projection為`CHECKPOINT_COMPLETE`；因沒有positive edge，
S11維持`not_activated`。本closeout不授權push。
