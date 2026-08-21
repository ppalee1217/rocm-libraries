---
checkpoint_id: S14
title: Stage 1 full-GA baseline-vs-guided real-GPU outcome
stage: 1
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R1
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S14
execution_tranche: T-S14-OUTCOME
closure_unit: CU-S14-OUTCOME
hypothesis_id: S14-H1
authority: RESCOPE-STAGE1-OUTCOME-20260807
pins_authority: RESCOPE-STAGE1-OUTCOME-20260807 + S14 design-discussion 2026-08-07 (two reviewers AGREE) + user pin decisions 2026-08-07 + PER-SHAPE-SOO-OUTCOME-20260809 (two-round design-discussion, user-approved 2026-08-09; SUPERSEDES the joint-MOO/aggregate-Q design — see §10) + CONDITIONAL-ARM-S-20260810 (user-approved 2026-08-10; adds pre-registered conditional Arm S same-entropy shuffle control — see §10.2 arms) + NATIVE-P0-ROBUSTNESS-20260811 (user-directed 2026-08-11; pre-registered native-Gen0 ~11,405 robustness/dilution addendum — see §12; scheduled after capped completes) + NATIVE-P0-ROBUSTNESS-20260811(b) (user-directed 2026-08-12; extends the addendum's shape scope from large-only to large + medium, adds Q3 extreme-value manipulation test with pre-registered directional predictions — see §12.1 Q3, §12.2, §12.4.4) + MEASUREMENT-DEFECT-PACKET-20260813 (**PENDING_HUMAN_DECISION**, not approved; design-discussion 2026-08-13, two reviewers AGREE, no preserved dissent — non-authoritative decision packet on the medium remeasure instrument defect: estimator, margin and claim ladder — see §13. Until owner approval, §10.2/§10.4 stand unchanged.) + CAPABILITY-ENDPOINT-PACKET-20260813 (**PENDING_HUMAN_DECISION**, not approved; design-discussion 2026-08-13 second session, two reviewers AGREE, no preserved dissent — rejects peak-of-7 as medium's endpoint on three independent grounds, and records that §13.2/§13.3's count-invariance claim is FALSE: max moves native non-regression 3/5 -> 4/5 in both campaigns across the §12.3 pre-registered threshold toward the treated arm. Also closes §13.7 item 2 — the 5,136 @ RBS-4096 probe fails on a deterministic int32 overflow, so no clean measurement is attainable at the pinned estimand. See §14. Until owner approval, §10.2/§10.4 stand unchanged.) + REDUCER-FACT-CORRECTION-20260812 (user-directed 2026-08-12; [CODE AUDIT] factual correction — Ductile implements NO Pareto/non-dominated sorting and soo=False DOES reduce to a scalar via np.max (ga.py:95, 256-273), so Q=max_s is Ductile's native fitness, not a post-hoc added step; documentation-only, NO change to decision/pins/gates/claims — see §10.1 correction box)
dependencies:
  - checkpoint_id: S11
    required_edge: S1_GUIDANCE_LOCKED
entry_criteria:
  - S1_GUIDANCE_LOCKED
criterion_refs:
  - S14_PER_SHAPE_OUTCOME   # active (PER-SHAPE-SOO-OUTCOME-20260809; see §10)
  - S14_GUIDED_OUTCOME_POSITIVE   # SUPERSEDED by S14_PER_SHAPE_OUTCOME (joint-MOO/aggregate-Q design retired; §10)
failure_ids:
  - FT-PLUMBING
  - FT-GEN0-MECHANISM
  - FT-HEURISTIC-SATURATION
  - FT-ENTROPY-ONLY
  - FT-EVALUATION-SUPPORT
  - FT-BLOCKED-CORRECTNESS
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S14_GUIDED_OUTCOME_POSITIVE
    target_checkpoint: null   # S20 execution SUSPENDED (RESCOPE-STAGE1-OUTCOME-20260807); re-link only on user un-freeze
formal_report_path: reports/staged/full-ga-baseline-vs-guided-outcome-report.md   # REPORT-LOCATION-20260813
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s14-guided-outcome-positive.json
tranche_final_report_path: reports/staged/full-ga-baseline-vs-guided-outcome-report.md   # REPORT-LOCATION-20260813
terminal_report_integration: integrates_S11_compact_record_and_S14_terminal_evidence
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s14-full-ga-outcome-lock.json
cross_server_reproducibility: required
pre_seal_gate: label_blind_throughput_correctness_noise_preflight_required
consensus_status: approved_two_reviewer_agree
---

# S14 — Stage 1 full-GA baseline-vs-guided real-GPU outcome

導航：[active checkpoint index](README.md)｜[experiment plan §7](../ductile-origami-warmstart-experiment-plan.md#7-d6-actual-gen0-endpoint)｜authority: `RESCOPE-STAGE1-OUTCOME-20260807`

> **狀態：**本 design 依 user-approved `RESCOPE-STAGE1-OUTCOME-20260807` 建立,並經 2026-08-07 兩位獨立 `gpt-5.6-sol/xhigh` reviewer 的 design-discussion（§9）與 user pin 決定收斂。`design_status=approved`、`consensus_status=approved_two_reviewer_agree`。**執行前置硬 gate**：`pre_seal_gate` —— 在 effective lock seal 前,必須在**實際執行 server** 上完成 label-blind 的 throughput + correctness + noise preflight（並產出真實 wall-time 估計與 `delta_noise`）。本 design 尚未執行任何 evidence、未建 lock/report/edge。用語遵循 charter §8.6:本 checkpoint **不**宣稱 convergence 改善或 tuning speedup。

> **⚠️ SUPERSEDED — `PER-SHAPE-SOO-OUTCOME-20260809`（two-round design-discussion,user-approved 2026-08-09）。**
> §1–§9 記錄的是**舊的「單一 joint 多目標 GA(`soo=False`)+ 聚合 `Q=max_s` 單一 champion」設計**,現已**被 §10 的 per-shape 設計取代**(舊記錄保留不刪)。取代原因(詳見 §10 與 `qa/qa-09-…`):(1) Ductile `soo=False` 的原生 fitness 即 `Q=max_s` 跨-size `np.max` 純量縮併(**無** Pareto;`ga.py:95, 256–273`),候選只憑最佳的單一 size 被評分;Tensile 本就輸出 per-size 最佳解,不需跨-size champion(敘述經 `REDUCER-FACT-CORRECTION-20260812` 更正,見 §10.1);(2) `Q=max_s` 被最吵的 tiny 8×8 主導(baseline pilot:seed 14005 champion 在 large 快近 2× 卻拿最低 Q),會用噪音選 champion;(3) 研究問的是「Gen0 bias 是否幫助**每個 shape**」,per-shape 各跑一條 GA 最乾淨且天生「兩邊同設計」。**執行以 §10 為準。** 舊 §6.1/§7/§1–2 僅作歷史記錄。

## 1. 白話目標

S14 回答 re-scoped Stage-1 的核心問題:**「Gen0 的權重 bias 是否真的影響 Ductile DSE 的最終結果？」**做法是把 actual Ductile 基因演算法跑**固定 30 世代**,分兩臂比較:

- **BASELINE(G)**：現行 GEKO guidance = 完整 `pi_nominal`（其中 `group_0` 帶 GEKO 權重,其餘 29 個 ungrouped free genes 為 uniform）。
- **GUIDED(F)**：G 之上,Formocast 只對「ungrouped、目前 unweighted 的 free genes」中 S11 manifest 明列者注入權重（不碰 `group_0`）。

兩臂各跑完 30 世代後,對每臂選出的 **champion kernel** 做**獨立真實 GPU 效能重測**,比較 F 是否在 champion real-GFLOPS 與 search-trajectory AUC 上方向性勝過 G。

## 2. Hypothesis 與 falsification

**S14-H1（directional）：**在 frozen problem set 上的 fixed-30-generation Ductile GA（P0-capped=512 變體）中,GUIDED(F)臂選出的 champion 其真實 GPU 效能,以及 search-trajectory AUC,**方向性勝過** BASELINE(G)臂;同時 correctness、validity 與 sampler realization 不失守。

註（reviewer 採納）：H1 是**單向**假設(F 優於 G)。一個可重現的**負** delta（F 穩定劣於 G）證明「權重有影響」但**不是** H1-positive,依 stop matrix 記為 `FT-HEURISTIC-SATURATION`/`FT-GEN0-MECHANISM`。

反證或 invalidating evidence：champion real-GFLOPS 或 trajectory AUC 未方向性勝出;proposal/candidate/weight/space hash 兩臂不一致或未各自重現其預期值;新增 correctness/validity failure;median/final real-quality 掉到 noise guardrail 以下;results 按 set iteration order join;看到 outcome 後更改任一 arm 定義、GA 參數或 metric。

## 3. Dependencies、entry 與 outgoing edge

- 唯一 entry：S11 完整 locked/verified/committed/post-audited 後的 `S1_GUIDANCE_LOCKED`。S14 消費 S11 交接的 frozen guidance（residual-gene 權重、canonical guidance hash、same-entropy shuffle bundle、noise/correctness evidence、seeds、sampler/mapping revisions）。
- S14 **不** gate 於 S12 `D5_PASS`（S12 FROZEN/DEFERRED）。真實效能改在 Ductile post-GA champion selection 上量測。
- Outgoing edge：`S14_GUIDED_OUTCOME_POSITIVE -> (S20 execution SUSPENDED)`。S20+ 目前 SUSPENDED,S14 positive 不自動解鎖。Negative/inconclusive 不追加 generations/seeds 救回。

### 3.1 Gate／tranche／closure governance
`risk_tier=R1`、`scientific_gate=S14`、`execution_tranche=T-S14-OUTCOME`、`closure_unit=CU-S14-OUTCOME`。Formal execution 前依 `b0561d2c92…` 完成 entry preflight,並 seal durable contract/effective lock。S14 positive 另 seal compact record;positive/negative/inconclusive 都由本 final report 整合 S11 compact record 與 S14 terminal evidence。

## 4. Maximum implementation 與 delivery boundary

允許：constructor `P0` 解析（**capped 至 512**,見 §6 pins）;fixed-30-generation GA 演化含 selection/crossover/mutation/survival;**per-generation 配對 proposal barrier**（見 §6）;BASELINE/GUIDED（及日後 optional S）formal proposal generation、canonical serialization 與 per-generation proposal lock;cross-arm/seed deduplicated benchmark union 與 multiplicity-aware join;post-GA champion 的獨立真實 GPU 重測;trajectory-AUC、champion real-GFLOPS delta、median guardrail、correctness、validity 與 diagnostics。

禁止：修改 S11 guidance/arms 定義/seeds;看到 outcome 後改 `n_gen`/`P0`/metric/`U_floor`/guardrail;用 best 取代已定義 guardrail 或把少數 seeds 包裝成 significance;執行/建立任何 SUSPENDED 下游;使用 legacy M06/S10R* artifacts;cross-generation result cache。

## 5. Future effective lock、inputs 與 outputs

Future lock：`protocol/v1/locks/s14-full-ga-outcome-lock.json`

### 5.1 Inputs（在**第一筆 BASELINE 或 GUIDED real label 前** seal）
S11 `S1_GUIDANCE_LOCKED` 交接物;arm 定義（G=GEKO、F=GEKO+Formocast;S=optional-reserved）;frozen problem set + §6 全部 pins;metric 定義（champion real-GFLOPS、search-trajectory AUC 到 `U_floor`、`delta_noise` guardrail）;per-generation proposal-lock/dedup/join schema、canonical config-set hash 規則。

### 5.2 Cross-server reproducibility pins（re-scope 要求;seal 於 lock,label 前）
toolchain：ROCm/HIP version、hipBLASLt/tensilelite commit SHA、amdclang version、rocisa binary hash、**GEKO↔Ductile integration tree/patch**、client binary（tensilelite-client）hash;GPU：`gfx942`、non-StreamK、device model、driver/KMD/firmware version、PCI BDF;config hashes：frozen YAML、`SearchSpace`/space、size-registry、Formocast residual-weight bundle、GEKO `group_0` weight;seeds（formal + 分離 replay）;bench config（`NumWarmups/EnqueuesPerSync/…`）;environment：container/OS/Python/NumPy/joblib、clock/power policy、`n_jobs=1`（否則 `os.cpu_count()` 會改變 seeded population）;**同一實體 GPU UUID** 跑同一對 G/F、counterbalanced 臂順序;cross-server conformance preflight 記錄於 lock（不可事後編輯）。

### 5.3 GPU 選擇政策（user instruction）
量測時**挑閒置 GPU、絕不用 device index 0**;以 `HIP_VISIBLE_DEVICES` 綁定單一裝置,將 UUID/arch 記入 lock。

### 5.4 Outputs
resolved `P0`;每臂 per-generation replay envelope 與 realization diagnostics;formal proposals + canonical hashes + per-generation proposal lock + dedup union;每臂 champion config + 其獨立真實 GPU 重測;per-slot results/multiplicity;S14 metrics、failure attribution 與 machine decision。

## 6. Controls、measurement boundary 與 frozen pins

> **baseline `pi_nominal` 組成與 treatment 作用範圍（來源 `protocol/v1/inputs/s10-generated.yaml`）：** frozen search space 共 30 個 key。GEKO 實際提供 weight 的**只有 `group_0`**（MatrixInstruction/WorkGroup 群組,9,918 個 joint 候選,依 `weight_beta` 轉成機率）;其餘 **29 個 ungrouped free genes**（DepthU、NonTemporalA/B/C/D、StaggerU、StaggerUStride、WorkGroupMapping、GlobalReadVectorWidthA/B、PrefetchGlobalRead…）在 `pi_nominal` 中為 **uniform**。故 `pi_nominal(config) = P(group_0 | GEKO 加權) × ∏(29 free genes 各自 uniform)`。**BASELINE(G)** 用完整 `pi_nominal`;**GUIDED(F)** 僅對 unweighted free genes 中 manifest 明列者注入 Formocast 權重,**不碰 `group_0`**（§2.2 保護）。`group_0` 兩臂完全相同,不進入 treatment —— S14 隔離的正是「把原本均勻的 free genes 改成 Formocast 加權」的效果。

Controls：arms 完全依 parent §7.1;independent variable 僅 free-gene guidance weighting,其餘跨臂相同;same formal seed 跨 G/F,replay seeds 與 formal seeds 分離;**所有 proposals 於各世代 lock 後才 benchmark**;canonical config identity 不依 set iteration order;deduplicated measurement 按 multiplicity 回填;champion 真實 GPU 重測在同一組 frozen sizes、同一 GPU 時窗;`U_floor` 與 noise-derived `delta_noise` guardrail 於 label 前固定;BASELINE 可先跑但不得重定義任何已 seal 項目;oracle 不進 formal endpoint。

### 6.1 Frozen pins（user + reviewer 收斂,label 前 seal）
- **P0（母體）**：configured `pop_size=512` 且**初始母體 capped=512**（不讓 constructor 自動膨脹到 ~11,405）。此 cap 由 `RESCOPE-STAGE1-OUTCOME-20260807` + **2026-08-07 user-authorized P0 amendment（64→512）** 授權;claim 明列為 **「P0-capped=512 Ductile variant」**,非未改動之原生 Ductile。runner 必須 fail-closed 驗證實際 P0=512。
- **世代**：`n_gen=30`（**最大上限**）,**保留 Ductile 原生早停**（native `period`/`tol`/`div_thr` 預設;low-diversity/收斂時可在 30 代前自然終止）—— 忠於未改動的 Ductile 行為,**不設 `period=0`**（2026-08-07 user-authorized:改回原生早停）。
- **seeds**：**5 對 formal seed**（`14001–14005`;G/F 同 seed 配對）;replay seeds 與 formal 分離。（2026-08-07 user-authorized:3→5,配合 5 張閒置非-0 卡平行,wall-time 不變而更 robust。）
- **arms**：正式跑 **G/F**;**Arm S 宣告為 optional-reserved**（可日後獨立補做,使用相同 seeds 並與 G/F champion 同時窗重測;現在宣告以避免 post-hoc;若不跑 S,`FT-ENTROPY-ONLY` 不適用且 claim 不含 physics-direction 歸因）;Arm U 省略。
- **品質 reducer**：`Q(x) = max_s [ GFLOPS_s(x) / R_s ]`,`R_s` 為 prelocked noise-anchor panel 的 per-size 參考（承襲 S11 sealed `max_s`,但 per-size 正規化以免原始尺度亂比）;三 size 皆需。
- **problem set**：3 個 size `(8,8,1,128)`、`(256,256,1,1024)`、`(2304,1024,1,214336)`,gfx942 non-StreamK,單一 dtype/layout（依 frozen size registry）。
- **`delta_noise`**：執行 server 上 `3 anchors × 3 sizes × 7 repeats`,`delta_noise = exp(P95(|log Q − median_r log Q|)) − 1`,anchors/公式/上限先封、scalar 於 formal label 前封（不由 arm results 導出）。
- **champion（PRIMARY outcome）**：每臂/seed 取 max-`Q` 的候選,tie-break 用 canonical config hash 升序;**獨立重測 7×/size**,G/F 配對隨機序。**這是 S14 的主指標**——對原生早停免疫,直接回答「bias 是否影響最終結果」。
- **search-trajectory AUC（次要診斷,非 gate）**：`A = (1/B*) ∫_0^{B*} log Q(u) du`,積分上限 `B*` = 該 seed 兩臂**共同完成的評估數** `min(evals_G, evals_F)`（因原生早停各臂預算可能不同）;`u`=post-Gen0 累積完成評估,`Q(0)`=Gen0 best,逐世代右連續階梯,multiplicity-aware。僅作方向性佐證,不作硬門檻。
- **support floor（軟;取消硬 `U_floor` gate）**：每臂/seed 只要完成 Gen0 + 其原生終止歷程即為有效;**僅當某臂連 Gen0 都無法完成或產不出有效 champion 時**才記 `FT-EVALUATION-SUPPORT`（尊重原生早停,不再要求固定 U_floor 預算）。
- **correctness**：每次 formal 評估與重測 `NumElementsToValidate=128`（預設 0 不足）。
- **assembly-dropped candidate handling（2026-08-07 pinned;2026-08-08 clarified per user decision A,measurement-correctness rule）**：GA 產生的候選中,若在 KernelWriter/assembly 階段 build 失敗（DID_NOT_SATISFY_ASSERTS／build failure）而被丟棄,則:**存活候選的量測結果按 canonical solIdx 對回其正確候選**;**被丟棄（unbuildable）候選給 invalid fitness = -1,並比照原生 Ductile 對「真跑但 benchmark 失敗」之 invalid(-1) 解的既有處理** —— 即**不另加任何 invalid 過濾機制**（忠於未改動的 Ductile selection）:一個 -1 候選**永不勝過任何正分候選、永不成為 champion**,僅可能在罕見的「整組皆 -1」之 k=2 淘汰賽中勝出該小對戰（其後代反正重抽/突變）。**嚴禁**只放寬對齊檢查而把分數錯配到別的候選;亦**不得**新增偏離原生 Ductile 的 selection 濾除 —— 若要濾除 invalid（讀法 2）屬 measurement-semantics 變更,須另立 amendment 且須一致套用於真-invalid(-1) 解。此為原生 DuctileBackend 在大母體（P0=512）暴露的既有缺陷之正確處置;適用 baseline 與 sealed run。
- **benchmark measurement — per-size rotating policy（2026-08-07 user-authorized,Option C）**：`NumWarmups=321`、`EnqueuesPerSync=321`。**rotating buffer 逐 size 設定**:小/中 size `(8,8,1,128)`、`(256,256,1,1024)` 用 **`RotatingBufferSize=4096` MB（rotating 開＝冷 cache 真實 GFLOPS）**;大 size `(2304,1024,1,214336)` 用 **rotating 關（`RotatingBufferSize=0`）**。理由:大 size working set ~1.34GB **遠超 GPU cache**（幾無 cache 重用可打散,關 rotating 不致 GFLOPS 灌水）,且 client 在該 size 的 rotating 檢查會 **signed-int 溢位**、任何實用 RBS 皆無法完整 rotate。實作:若 client 不支援 per-size RBS,以「小/中 size@RBS=4096 與 大 size@RBS=0 **分別量測、再按 canonical config identity 合併**」達成,確保每候選 3 個 size 皆有 GFLOPS 供 `Q=max_s[GFLOPS_s/R_s]` 計算（合併不改 Q 定義）。
- **per-generation 配對 barrier**：protocol lock 先於任何 formal label;之後每世代:產生 G/F batch → 鎖該世代 → 去重該世代 G/F union → benchmark → multiplicity-aware join → 兩臂同步前進;**不得跨世代 cache**（backend `useCache=False`）。
- **label firewall**：comparison lock 於**第一筆 BASELINE label 之前**封;prelock 跑的 baseline 只能算 pilot、封後重跑;counterbalanced 臂順序。
- **hash 判定**：只對不變基底（base YAML、space、candidate order、GEKO `group_0` 權重、operators、bench config）要求兩臂一致;各臂需重現自己預期的 treatment/proposal hash;F−G 權重差 = 恰為 residual bundle。
- **`n_jobs=1`**;每個 seed 的 G/F 配對用同一實體 GPU UUID（pair-consistency）;**不同 seed 可分別 pin 到不同的閒置非-0 GPU 平行執行**（baseline pilot 僅 G 臂、無配對限制,允許 5-seed 平行（5 張卡）;正式 G/F 時仍須每 seed 的 G 與 F 同卡）。

S14 能回答 single-development-cluster 的「free-gene 權重 bias 是否影響最終 DSE 結果（P0-capped=512 變體）」;**不能**回答 H10 persistence（S20）、held-out replication（S31）、speedup 或 convergence 泛化。

## 7. Acceptance binding 與 stop matrix

唯一 positive criterion `S14_GUIDED_OUTCOME_POSITIVE`（directional,**5 對 seed 中至少 4 對** joint 滿足,無 significance test）:

1. **（PRIMARY）** champion `Q_F*/Q_G* > 1 + delta_noise`,**至少 4/5 seeds**;
2. **（PRIMARY）** final-population median 非劣 `median(Q_F)/median(Q_G) ≥ 1/(1+delta_noise)`,**至少 4/5 seeds**;
3. **（次要診斷,非 PASS 硬條件）** search-trajectory AUC `A_F − A_G > log(1 + delta_noise)`（積分到共同預算 `B*`）作方向性佐證;
4. proposal-set/candidate/weight/space hashes 依 §6.1 hash 判定通過;replay envelope 無 systematic anomaly;無新 validity/correctness failure;reproducibility pins 已 seal 且 preflight 通過。

**PASS = 條件 1、2、4 各至少 4/5 seeds 通過**（AUC 為佐證,不阻擋）。

（若日後補跑 Arm S:另加「F 亦勝 S」方可歸因 physics-direction,否則 claim 限「F 勝 G」。）

| 狀況 | outcome／failure | downstream |
| --- | --- | --- |
| 條件 1/2/4 各至少 4/5 通過（AUC 佐證）| `S14_GUIDED_OUTCOME_POSITIVE` | S20（SUSPENDED,不自動解鎖）|
| Proposal/replay/order/hash mismatch | `FT-PLUMBING`；修復需 new lock/fresh proposals | 無 |
| Realization 正常但最終 champion quality 無方向性增益 | `FT-GEN0-MECHANISM` | 無 |
| F 不勝 G(GEKO) | `FT-HEURISTIC-SATURATION` | 無 |
| （若跑 S）F 不勝 same-entropy shuffle | `FT-ENTROPY-ONLY` | 無 |
| 某臂連 Gen0／有效 champion 都產不出 | `FT-EVALUATION-SUPPORT` | 無 |
| 執行 server 可重現 correctness 失敗 | `FT-BLOCKED-CORRECTNESS` | 無 |
| Noise/support 不足 | `FT-INCONCLUSIVE` | 無 |
| 想用額外 generations/seeds 或看結果後改參數救回 | downgrade/plan change,停止 review | 無 |

## 8. Formal report 與 closeout

唯一 formal report:`reports/staged/full-ga-baseline-vs-guided-outcome-report.md`
(`REPORT-LOCATION-20260813`;另有三份 per-shape 附冊 `reports/staged/s14-{medium,large,tiny}-report.md`,
附冊承載詳細實驗記錄,**gate 判定與 outcome 只在 formal report**),追溯 S11 authority 與 `RESCOPE-STAGE1-OUTCOME-20260807`,整合 S11 compact record 與 S14 machine decision。因 S20+ SUSPENDED,S14 為目前 Stage-1 terminal outcome report;claim boundary 限 **P0-capped 變體、single-cluster directional advantage of F over G**（physics-direction 僅在補跑 S 時)。

## 9. Design-consensus record（2026-08-07 design-discussion）

- 程序：兩位 fresh independent reviewers,`gpt-5.6-sol`（effort `xhigh`,`service_tier=fast`),經 codex MCP bridge 各開 fresh thread（Reviewer A `019fda49-14ef-7a73-b62b-f1cb24da1941`、Reviewer B `019fda53-ef45-7aa3-8251-0f534ed27a0d`）,initial 各一輪 + 一輪 convergence。初判兩方均 `CHANGES_REQUIRED`;下列修正納入後兩方 `AGREE`。Same-model fresh threads 屬 process independence,非 scientific replication。
- 兩方一致 objections（已全數採納入本 design）：
  1. H1 改為單向 F>G directional（負 delta = 有影響但非 positive）。
  2. imported「all-proposals-lock-before-benchmark」對多世代 GA 不可執行 → 改 **per-generation 配對 barrier**、no cross-gen cache。
  3. 「champion」在 `soo=False` 未定義（每 size 各一 best）→ 定**單一 aggregate-Q champion + hash tie-break + 獨立 7×/size 重測**。
  4. hash 判定自相矛盾 → 只對不變基底要求一致,各臂重現自身 treatment hash。
  5. `delta_noise` 須為**勝出門檻**（非僅非劣）。
  6. label firewall 須在**第一筆 BASELINE label 前**封;prelock baseline = pilot 重跑。
  7. charter §8.6 禁 convergence/speedup 用語 → 全面改「fixed-30-generation trajectory outcome / search-trajectory AUC」。
  8. correctness 預設 `NumElementsToValidate=0` 不足 → 設 128 + 執行 server correctness/noise preflight。
  9. cross-server pins 不足 → 補 integration tree/patch、client/rocisa binary、container/OS/Python/NumPy/joblib、firmware/clocks/power、`n_jobs=1`、same GPU UUID、counterbalanced order。
  10. 新增 `FT-EVALUATION-SUPPORT`（charter 已定義）與 `FT-BLOCKED-CORRECTNESS`。
- pins 一致建議（已採納）：`n_gen=30`/`period=0`;reducer `max_s[GFLOPS_s/R_s]` per-size 正規化;3 sizes 如 §6.1;`delta_noise` 3×3×7 pilot;AUC 定義如 §6.1。
- 兩項 user-decided forks（reviewer 提供分支分析,使用者拍板）：
  - **P0**：reviewer 均建議 CAP 以趕 deadline（REAL=11,405 兩週內幾乎不可行）。使用者初選 CAP=64;**2026-08-07 使用者本人授權將 P0 pin 更新為 CAP=512**（仍在 reviewer 分析過的 CAP 分支內,只是 cap 值不同;claim 限「P0-capped=512 變體」）。**注:原先隨此設的 `U_floor=7,680` 已由下方 early-stop amendment 取消硬 gate(見下條),不再適用。** 若日後要對 512 另做兩位 reviewer 複審可再啟動,惟使用者已授權以此進行。
  - **seed 數**：reviewer 一方 3/3、一方 5(4/5);使用者初選 3/3,**2026-08-07 使用者本人授權改為 5 seeds / 4-of-5 joint**（因 5 張閒置非-0 卡可平行、wall-time 不變而更 robust;採 Reviewer B 的 5-seed precedent,容一顆 outlier）。5-seed 平行（每 seed 各 pin 一張閒置非-0 GPU;每 seed 的 G/F 仍同卡）。
  - **early-stop（2026-08-07 user-authorized）**：**保留 Ductile 原生早停**（不設 `period=0`）;`n_gen=30` 為最大上限;主指標改 **champion real-GFLOPS + median 非劣**（primary）,**search-trajectory AUC 降為次要診斷**（積分到兩臂共同預算）,**取消硬 `U_floor` gate**（僅某臂連 Gen0／champion 都產不出才 `FT-EVALUATION-SUPPORT`）。理由:忠於未改動的 Ductile,且 charter §8.6 禁 speedup 宣稱,故以固定-結果品質（champion）而非效率（AUC）當 headline。
  - **Arm S**：**使用者選先只做 G/F、S 宣告 optional-reserved**（日後可獨立補、不重跑 G/F）。
- 未決/前置：seal 前必須通過 label-blind throughput + correctness + noise **preflight**（也產出真實 wall-time 估計與 `delta_noise`)。若 preflight 顯示 CAP=512 仍不可行,回 user decision。
- **Open preflight finding（2026-08-07,使用者選擇「先記錄、延後至 sealed run 前再定」）**:noise pilot 量得 `delta_noise≈1.83（182%）`,主因最小 size `(8,8,1,128)` 被 kernel-launch jitter 主導（重複量 Q 在 ~1.8↔2.8 跳）、且 `Q=max_s` 挑到它。這會使 sealed guided-vs-baseline 的 `Q_F/Q_G>1+delta_noise` 門檻高到無意義。**不影響 baseline pilot**（baseline 不用 delta_noise 判斷,只回報 per-seed champion）。**sealed G/F run 前必須解決**,候選方案:(i) 從 frozen 16-size 換掉 tiny 8×8;(ii) 改 Q 使 tiny 不主導（排除於 Q 或改 per-size gate 取代 max_s）;(iii) 其他。附:size 特性 —— tiny=noisy、huge `(…,214336)`=慢(90% 時間)+client rotating 溢位、僅 `(256,256,1,1024)` 表現穩定。
- Reviewer A final：`AGREE`（conditional on 上述修正 + preflight before seal）
- Reviewer B final：`AGREE`（conditional on 上述修正 + preflight before seal）

## 10. `PER-SHAPE-SOO-OUTCOME-20260809` amendment（two-round design-discussion,user-approved 2026-08-09）— ACTIVE 設計

> **狀態：user-approved(~1.5 週 deadline)。本 amendment 取代 §1–§9 的 joint-MOO/aggregate-Q 設計為 per-shape 設計;為 design/治理文字更新,未執行 evidence、未建 lock/report/edge、不授權 push。舊記錄保留。程序:兩位 fresh independent `gpt-5.6-sol/xhigh` reviewer,經兩輪 design-discussion(A `019fe85b…`、B `019fe85e…`)零分歧收斂;same-model fresh threads 屬 process independence,非 scientific replication。**

### 10.1 為何改（考量→決策）
- **Ductile 的跨-size 縮併方式本身不適合本研究問題**(`REDUCER-FACT-CORRECTION-20260812` 已更正原敘述,見下註)。`[CODE AUDIT]`:Ductile **未實作 Pareto／非支配排序**(全樹 `pareto|non-dominated|nsga|crowding` 零結果);`soo=False` 時 fitness 雖為 per-size `(3,N)` 矩陣,但 **GA 內部即以 `np.max` 縮併為純量**:`ga.py:256–273` `best.F = scores.max(1)`(各 size incumbent,即正規化分母 `R_s`)、`pop.F = self.reduce_fn(scores / best.F[..., None], axis=0)`,而 `reduce_fn` 於 `soo=False` 即 `np.max`(`ga.py:95`)。故 **`Q_c = max_s(GFLOPS_{s,c}/R_s)` 就是 Ductile 的原生 fitness**,並非事後外加。其缺陷在於:候選只憑「表現最好的那**一個** size」被評分,其餘 size 遭丟棄。另一方面 Tensile `3_LibraryLogic` 本就輸出 per-size 最佳解,亦不需要單一跨-size champion。→ 改為 per-shape 後 fitness 成 `(1,N)`、`max` 退化為恆等,**從根本繞開該 reducer**。
- **`Q=max_s[GFLOPS_s/R_s]` 被 tiny 8×8 主導**(per-size 比值:tiny≈4.3–4.9、medium≈2.3–3.0、large≈1.0–1.36),而 tiny 是 latency-bound、量測噪音達 ±40%。baseline pilot 實證:seed 14005 的 champion 在 large 快近 2×(480,141 vs 其餘 ~182k–246k GFLOPS)卻拿**最低** aggregate Q(2.66)→ 用噪音在選 champion。
- **機制約束**:Gen0 bias 是「每個 gene 一個 weight 向量」餵給**單一** GA 的單一初始族群;per-size guidance 只有在「每個 shape 各跑一條 GA」時成立。→ 選 **per-shape 架構**:一 shape 一條 GA(單一 size 於 `ProblemSizes`),guidance/搜尋/評估全部 per-shape;妥協解與 tiny 汙染自然消失(tiny 自成獨立實驗)。三個差異大的 shape 是為 size **多樣性**,非聯合優化。

### 10.2 Active pins（取代 §6.1;label 前 seal）
- **架構**：每個 shape 各一條 GA(單一 size 於 `BenchmarkFinalParameters.ProblemSizes`);純 config,不需改碼(`soo` 對單一 size 為 moot)。
- **shapes**：**medium `(256,256,1,1024)` 與 large `(2304,1024,1,214336)` = confirmatory**;**tiny `(8,8,1,128)` = 探索性**(僅描述,排除於 confirmatory gate)。
- **horizon（H1,user-authorized 2026-08-09）**：`n_gen=30` 上限 + **保留 Ductile 原生早停**(period=5;忠於 Ductile),並從**同一次跑**擷取 **gen-10 檢查點**(gen-10 給 charter §8.2 short-horizon;各臂早停處的 champion 給最終結果)。
- **arms/seeds**：G(`p0`,baseline)/F(`p1_s`,capped guided);**5 對全新 seed `24001–24005`**(先驗證與 registry 無碰撞);replay/量測序另立。
- **Arm S(same-entropy shuffle 控制)——owner 2026-08-10 選定「conditional Arm S」(`CONDITIONAL-ARM-S-20260810`,pre-registered)。** 背景:same-entropy shuffle 的 physics-direction 歸因(F 需同時勝 G 與 S)本是**下游 S20(Stage-2 H10 persistence)的 registered 設計**(S20-H1「F 同時勝 G 與 S」;S20 現 frozen pending S14);且本輪 treatment 稀疏(medium 2/large 5/tiny 0 gene)、經 entropy-cap 溫和(H_norm≥0.80),5 seeds 下 F-vs-S 本就 underpowered。因此**不**做 unconditional 第三波,改採 pre-registered 條件式:
  - **treatment 現在就凍結**:對每個 activated gene 的 capped `q` 做 `deterministic_nonidentity_shuffle`(同 ρ → 同 entropy、僅打散 value↔偏好對應),導出 shuffle bundle 並封 **Lock C**(在看到任何 G/F/S outcome 前封,維持 label firewall)。
  - **觸發規則(pre-registered)**:sealed G/F 分析完成後,**若** F 在 ≥1 confirmatory shape(medium 或 large)通過 per-shape directional-consistency gate(即確有值得歸因的正效應)**且** 剩餘 deadline budget ≥ wave-3 成本(~9–13h,large 為瓶頸),**才**於該(些)shape 補跑 Arm S:相同 seeds、相同 per-seed GPU UUID、7× 交錯 **G/F/S** 重測。
  - **未觸發**(F 對 G 無效應,或 budget 不足):Arm S 不跑;報告記「Arm S pre-registered,trigger 未達」,physics-direction 歸因 defer 到 S20。
  - **歸因規則**:physics-direction 只有在 F **同時**勝 G **與 S**(該 shape directional gate 對 S 亦過)時方可宣稱;否則 F 勝 G 僅歸因「capped factorized initialization bundle vs baseline / 集中效應」。
- **P0**：`pop_size=512` capped(fail-closed 驗證)。`NumElementsToValidate=128`;`n_jobs=1`;per-size rotating(large RBS=0、medium/tiny RBS=4096)。
- **per-shape 噪音 margin**：`η_s = P95(|log y − median_r log y|)`、`δ_s = e^{η_s}−1`,**用現有 3-anchor×7-repeat pilot 殘差、逐 shape 分開算**(**不**用 tiny-汙染的 aggregate delta_noise);最終非退步門檻 = `e^{−η_s} = 1/(1+δ_s)`;label 前封殘差/η_s/δ_s。
- **champion**：per shape 取該 shape 上最佳有效候選(以及 gen-10 檢查點),canonical-hash tie-break;**7×/shape 交錯(G/F 交替)重測**於同一 GPU 時窗。
- **AUC(per shape)**：`A=(1/B*)∫_0^{B*} log(I(u)/R_s) du`,`I(u)`=右連續 incumbent、`u`=post-Gen0 完成評估數、`B*=min(evals_G,evals_F)`;逐 shape,不跨 shape 合併。
- **assembly-dropped / rotating / correctness**：沿用 §6.1 對應規則(dropped=-1 比照原生 invalid、per-size rotating Option C、NEtV=128),但**逐 shape 套用**。
- **RNG**：counter-based streams `(lock_hash, shape, seed, phase∈{gen0,evolution,measurement})`;配對臂共用同一組 Gen0 uniforms、經 `p0` 或 `p1` 映射(只差先驗);Gen0 後重置 evolution stream。**臂順序 counterbalanced**(部分 seed G→F、部分 F→G),同一 seed 的 G/F 用**同一實體 GPU UUID**。
- **GPU 上限**：**最多 6 張、絕不用 index 0**(user 2026-08-09)。

### 10.3 Per-shape S11 guidance（取代跨 size `max` reducer;out-of-band,不改 locked 碼）
從既有 `manifests/s11-native-scores.json` + `s11-registry.json`,重用 sealed 函式(`gene_marginals`/`shrinkage_mean`/`construct_gene_probabilities`/`select_global_lambda`/`float32_inverse_cost_roundtrip`/`deterministic_nonidentity_shuffle`)逐 shape 導出:`b_{c,s}=1−midECDF_s(latency)` → α=32 shrinkage marginal `m_{g,s,v}` → `q_{g,s}=softmax(m/T)`(locked T)。

**啟用關卡(activation gate)**:某 gene 在 shape s 上「合格」須同時滿足 (a) ≥2 trusted 值、(b) `S_g≥0.05`、(c) per-shape direction 為正;不合格則該 gene 回退 `p0`。

**entropy-preserving mixture cap(`ENTROPY-CAP-20260810` amendment,取代原 gate (d) 二元排除;design-discussion 2026-08-09 兩位 reviewer AGREE、user-approved)**:對每個「合格」gene,以既選 `λ_s`(=8)取 `q_{g,s}=q(λ_s)`,並用 **per-gene 混合強度 cap**:`p1_{g,s}=(1−ρ)·p0 + ρ·q_{g,s}`,`ρ_g = max{ρ∈[0,0.80] : H_norm((1−ρ)p0+ρ·q_{g,s}) ≥ 0.80}`;已達標者 `ρ=0.80`(等同原 `0.2p0+0.8q`,現有 active gene 不變)。此為**通用規則、對所有合格 gene 一致套用**(非只救特定 gene)→ 保留 `H_norm≥0.80` 的多樣性約束,同時**納入**原本因高基數/少 trusted 值而被二元排除的最強 gene(medium `DepthU`、large `PrefetchGlobalRead`)。所有候選保正機率。輸出每 gene 的 `p0/q/p1/ρ/entropy/TV/KL` + GA weights(`w(v)=−log(p1(v))/β`,β=contract `native_scoring.weight_beta`);**跑前單元測試** post-transform 機率==p1。

**lineage**:此 capped `p1` 為 **S14 out-of-band treatment artifact**,**非** sealed S11 的 `construct_gene_probabilities` 輸出 → 新 bundle 名、新 hash、**獨立驗證**、**新 Lock B**,於**看任何 guided 結果前先封**;sealed S11(max reducer)與原 per-shape p1 bundle 原封保留,**不**餵 S14。若 amendment 無法在 label 前封 → 退回 A(照原稀疏 guidance 跑);此 out-of-band 導出**不改任何 locked s11/*.py**。整 shape 全回退 = `not activated`。

### 10.4 Acceptance（取代 §7;新 criterion `S14_PER_SHAPE_OUTCOME`）
- **雙向效應估計為骨幹**(不預設 null)。逐 shape、逐維度報 5 對 seed 的:Gen0 增量、gen-10 增量、AUC 差、最終 7×-median log-ratio。
- **Per-shape directional-consistency gate**(預註冊,非顯著性檢定):某 confirmatory shape 需 {Gen0 增量、gen-10 增量、AUC 差} 各 ≥4/5 對為正,且最終 ratio ≥ `e^{−η_s}` 於 ≥4/5 對(median 亦過)。
- **最終品質為 two-sided(`CLAIM-SCOPE-S14-20260810`,owner-approved;不預設 null)**:per shape 報最終 7×-median log-ratio(guided/baseline)的**效應量 + CI + 跨 seed 一致性**,分三檔:**改善**(≥4/5 對 ratio>1 且 median 高於 `e^{+η_s}`)/ **非退步**(median ≥ `e^{−η_s}`)/ **退步**(< `e^{−η_s}`)。**若判定改善,得依 charter §8.6a 宣稱「受測 shape 上 guided initialization 使最終 tuned 品質提升(directional/bounded evidence)」**,並強制標註 power(5 seeds=modest)與 scope(限受測 shape,不一般化)。early-search(Gen0/gen-10/AUC)之改善亦以同樣 two-sided + directional-consistency 呈現。**結論一律等 sealed 分析,嚴禁看資料前預設「有差/沒差」。**
- **combined 措辭需 medium ∧ large 都過各自 gate**(intersection-union,不得用聚合救);只一個過則報 shape-specific + mixed。tiny 探索性(無 gate)。
- **兩段式 lock**:Lock A(協定/seeds/margins/budget/RNG/measurement,baseline 前)、Lock B(per-shape capped guidance/activation,guided 前)。baseline 可於 Lock A 後先跑但輸出隔離不看。

### 10.5 Claim 邊界（charter §8.2/§8.5/§8.6）
- **可宣稱(依 charter §8.6a `CLAIM-SCOPE-S14-20260810`,owner-approved 2026-08-10)**:以 **two-sided、bounded** 報告 guided initialization 對 **early-search(gen-10)quality-vs-evaluations** 與 **最終 tuned 品質(final champion real-GFLOPS)** 的效應 —— 含**改善**、無變化、或退步;**若資料支持,得宣稱「受測 shape 上最終品質提升」**。皆限「single development cluster、5 對全新 seed、固定 horizon、medium+large、**modest power(非統計顯著性證明)**」,並**不得在 sealed 分析前預設結論**。
- **不宣稱(§8.6 未放行部分)**:對 MI300X workloads 一般化、production/deployment ready、跨架構、**end-to-end tuning wall-clock speedup**(未量測)、owner/team 應採用 —— 含軟化說法。(**「勝過 native `PredictionThreshold`」已由 charter §8.6a 2026-08-10(b) owner extension 就 S14 解除為 two-sided、等資料再說**:資料支持且實際量測/納入 native 參考時得宣稱,並如實揭露 budget/selection confounding;未量測 native 前不憑空宣稱勝過或不及。)
- **physics-direction 歸因(conditional Arm S,`CONDITIONAL-ARM-S-20260810`)**:預設兩臂(G/F)只歸因「capped factorized initialization bundle vs baseline」,**不**歸因 Formocast physics 方向。**唯一例外**:conditional Arm S 觸發(§10.2:F 於 ≥1 confirmatory shape 過 gate 且 budget 足)**且** F 於該 shape **同時**勝 G **與 S**,方可就**該受測 shape** 宣稱「效應歸因於 Formocast 偏好的方向,而非任意 entropy 集中」(仍受 5-seed modest power + 不一般化限制)。Arm S 未觸發或 F 未同時勝 S,physics-direction 歸因 defer 到 S20。
- **反造假**:每個結果標 `[MODEL-ONLY]`/`[BASELINE GPU]`/`[GUIDED GPU]`/`[CODE AUDIT]`;seed 為實驗單位(7× 重測只是量噪);絕不用 baseline/model 合成 guided 反事實;`not evaluated` ≠ `無效`;全報 seed/失敗/排除;看 guided 結果前不改任何 pin/margin/seed。

## 11. `APPROVED` — sparse-guidance viability + gate 審查(design-discussion 2026-08-09;user-approved 2026-08-10)

> **狀態:`APPROVED`(user 2026-08-10,選 variant-B/entropy-cap)。** design-discussion:兩位 fresh independent `gpt-5.6-sol/xhigh` reviewer(A `019fe97f…`、B `019fe989…`),initial positions 各一輪 + 一輪 evidence-backed final;兩方均 **`AGREE`**(zero preserved dissent)。已落實:§10.3 entropy-cap(`ENTROPY-CAP-20260810`)、§10.4/§10.5 two-sided claim。
>
> **另:owner 於 2026-08-10 核准 charter §8.6a `CLAIM-SCOPE-S14-20260810`,取代下方 packet item 7 的「不宣稱最終 superiority」** —— S14 改為 **two-sided**、**得在資料支持下宣稱受測 shape 最終品質提升**(bounded/modest power、不一般化、不預設結論、不誇大偽造)。下方 packet 為當時 reviewer 建議之歷史記錄(item 7 已被 owner claim-scope amendment 覆寫)。

**Trigger**:per-shape guidance 極稀疏(medium 1 gene、large 4、tiny 0)。稽核發現根因是 sealed `sensitivity S_g≥0.05` gate:26 個 trusted gene 中僅 aggregate-max 3、medium 2、large 5、tiny 0 過門檻(平均 S_g 0.017–0.028);**連最濃的 aggregate max-reducer 也只 3 個** → 稀疏是**模型本身性質**(~22–24/27 gene 的預測 latency 幾乎不隨其值改變),非 per-shape 產物,亦無法靠放寬 S_g 修正(其餘 gene 真的平)。副作用:entropy floor gate (d) 剛好排除**訊號最強**的 gene(DepthU S_g=0.14 medium、PrefetchGlobalRead S_g=0.19 large;皆因「高基數但僅 2 trusted 值 → 引導後集中 → 熵<0.80」)。

**統一建議(variant of B)**:
1. **可做性**:實驗**可做**,但定位為「**稀疏 Gen0 treatment 的 bounded 測試**」,非「27-gene 廣泛 guidance」。
2. **Gate 1(sensitivity)**:**維持不變**。它是 `[MODEL-ONLY]` 一階相關性篩選 = 各值「平均族群排名」相對 uniform 的離散。失敗 = 「此 factorized 模型-排名主效應不可用」,**非**「真實 GPU/絕對/交互 無效果」。盲點(模型空間排名、忽略交互/confounding/絕對尺度)如實揭露;失敗顯式 `p1=p0`(必要,因 λ=0 的 q 只在 trusted 子集均勻,未必等於 p0)。
3. **Gate 2(0.05)**:**維持不變**。是預註冊的啟發式模型空間相關性下限(≥5 排名百分位點;λ=8 時 ≈1.49× best/worst odds)。**不**與 GPU noise 掛鉤(無 rank→log-GFLOPS 驗證映射);真實噪音留在最終非退步 margin η_s。不放寬。所有連續 S_g(含失敗)都回報。
4. **Gate 3(entropy floor)→ 修訂**:保留 `H_norm≥0.80` 作為**集中度約束**,但把「二元排除 gene」改為**通用 per-gene 混合強度 cap ρ**:對每個過 trust+S_g+direction 的 gene,以既定 `λ_s=8` 取 `p1_g=(1−ρ)p0+ρ·q_g(λ=8)`,`ρ_g=max{ρ∈[0,0.80]:H_norm((1−ρ)p0+ρq_g)≥0.80}`;已達標者 ρ=0.80(現有 active gene 不變)。→ 以較低強度**納入** DepthU(medium)、PrefetchGlobalRead(large);所有候選保正機率。輸出 ρ/entropy/TV/KL/p0/q/p-cap + float32 roundtrip;label 前 fail-closed。
5. **執行**:G/F 跑 **medium+large、5 對 seed**、既有端點(Gen0/gen-10/AUC/final 非退步)。**tiny = `not evaluated / not activated`**(兩臂相同、sentinel 主導),非「無效果」。不為 deadline 減 seed/horizon。
6. **治理/lineage**:此為 **S14 out-of-band treatment amendment,非 sealed S11**(capped p ≠ sealed `construct_gene_probabilities` 輸出)→ 新 bundle 名、新 hash、獨立驗證、新 Lock B,**看任何 guided 結果前先封**;sealed S11(max)與現有 per-shape p1 bundle 原封不動保留。**通用規則(所有合格 gene)→ 非 gate-shopping。** 若 amendment 無法在 label 前封 → 退回 **A(凍結 fallback)**;若 medium+large 塞不進 deadline → charter reduced-scope decision packet(C 不可當靜默替代)。
7. **Claim ladder**:model-only 稀疏 = headline;medium∧large 都過 → §8.2 gen-10 early-search 改善 + final 非退步(single cluster、5 seeds、modest power);一過 → shape-specific + mixed;皆不過 → 「amended sparse prior 未達預註冊 directional gate」(**非**「無效果/模型沒用」);不宣稱 superiority/convergence/speedup/一般化;無 Arm S shuffle 時只歸因「capped factorized initialization bundle vs baseline」,不歸因 Formocast physics 方向。
8. **Acceptance**:per-shape directional-consistency gate(Gen0、gen-10、AUC、final ratio≥e^{−η_s} 各 ≥4/5 對),combined 需 medium∧large。**Residual uncertainty**:無 rank→GFLOPS 映射;per-shape null/bootstrap 缺(4 個 sealed gate 站下 → 屬啟發式 per-shape 訊號);Gen0 bias 可能沖淡或單一 gene 主導;ρ 數值需 artifact 驗證後方可用。

**最小人類決定**:是否核准上述 **variant-B(entropy cap 修訂 + medium/large 5-seed + tiny not-evaluated + 新 Lock B)**?或選 **A(照現有稀疏 guidance 跑、不修 gate)**、或 **C(model-only headline + large-only 最小確認,需 reduced-scope packet)**。核准後才 re-derive capped guidance → 驗證 → 封 Lock B → 跑 guided。

---

## 12. `NATIVE-P0-ROBUSTNESS-20260811` addendum — native Gen0(~11,405)穩健性/稀釋實驗（pre-registered,user-directed 2026-08-11;**shape 範圍於 2026-08-12 經 `NATIVE-P0-ROBUSTNESS-20260811(b)` 擴充為 large + medium**;排入 capped 完成後之後續 wave）

> **狀態:PRE-REGISTERED,尚未執行。** 本節在 owner 指示下撰寫,作為主 S14(P0-capped=512)的**robustness addendum**;不改主 S14 的 G/F 設計、seeds、Lock A/B。排程見 §12.6。所有數字待執行後由 closure 補;本節不捏造結果。

### 12.1 目的與研究問題
主 S14 在 **P0-capped=512** 下跑,claim 限「P0-capped=512 variant」。本 addendum 在 **large shape** 上以 **Ductile 原生 Gen0(~11,405)** 重跑 G/F,回答:
- **Q1(外部效度/穩健性):** capped-512 在 large 上的 F-vs-G 方向/效應,在**原生 Gen0 規模**下是否仍成立? → 消除「你把 P0 改小了」對 large 結論的 caveat。
- **Q3(極值機制檢驗;`(b)` 2026-08-12 新增):** capped 版顯示 guidance 改善 Gen0 **中心**卻惡化 Gen0 **極值**(§7.2.1)。Gen0 池大小是決定 max 統計量取樣深度的直接參數,512→11,405 為 22× 放大 → 本 addendum 同時是該機制的**操縱變因檢驗**,方向性預測見 §12.4 第 4 點。
- **Q2(treatment×budget 交互作用/稀釋量化):** guidance 邊際效應是否在原生大 Gen0 下**縮小**(假說:prior 在小 Gen0 最有效;大 uniform Gen0 把 free-gene marginals 抽滿→稀釋)? 比較 512 vs 11,405 的效應量即量化此稀釋。

### 12.2 Shape 選擇理由(`NATIVE-P0-ROBUSTNESS-20260811(b)`,2026-08-12 擴充為 large + medium)

> **擴充說明(2026-08-12,user-directed)。** 本節原(2026-08-11)訂為 **large-only**,並以「medium treatment
> 薄、問題易(資訊量低)」與「native Gen0 昂貴,三 shape 全做不可行」為由排除 medium。這兩項前提**都已被
> capped 版的實測資料推翻**(當時尚無 remeasure 結果)。原判斷保留於 git history;以下為修訂後理由。

**(A) large 仍納入(原理由不變)**

(1) large 的 treatment 最豐富(5 個 activated gene:`PrefetchGlobalRead`、`TransposeLDS`、
`UnrollLoopSwapGlobalReadOrder`、`GlobalReadVectorWidthA/B`)→ 對稀釋問題最有資訊量;(2) large 最具實務代表性(大 GEMM 是 tuning
成本重心)。

**(B) 新增 medium,三項理由**

1. **成本前提不成立(已量測)。** 原「三 shape 全做不可行」建立在 native 全程評估 ~2.4–3.8× 於 512 的
   倍率估計上,但**沒有比較各 shape 的絕對成本**。實測 seed 24001 的 GPU 評估時間:
   **medium 0.17 h、large 5.61 h、tiny 0.10 h**(`trajectory.jsonl` 的
   `generation_evaluate_seconds` 加總)。medium 比 large 便宜 **~33×**;即便乘上 native 的 2.4–3.8×
   倍率,medium 全 5 seed × 2 arm 的量級仍遠低於單一 large seed-arm。**排入 medium 幾乎不動用預算。**
2. **「medium 資訊量低」被資料推翻,且方向與原判斷相反。** capped 版 7× remeasure 顯示:
   **medium 是唯一兩臂差異可被解析的 shape** —— per-seed F/G 落在 0.36×–2.12×,遠超 η_medium = 0.42 %,
   是真實的 champion 差異(§7.1);而 **large 五個 seed 全落在 η_large = 12.28 % 之內**,兩臂在該 shape
   上根本無法區分(§7.2)。本 addendum 的核心問題 Q2 是「**效應量**如何隨 Gen0 規模改變」——
   在一個效應量本身量不出來的 shape 上,Q2 沒有可讀的訊號。**要量稀釋,必須在有活訊號的 shape 上量,
   而那個 shape 是 medium。** 只跑 large 會讓 Q2 幾乎必然得到「null → null」這種無區辨力的結果。
3. **§7.2.1 的極值機制讓 Gen0 規模成為直接自變數(新的 Q3)。** capped 版證據顯示 guidance 改善 Gen0 的
   **中心**(4/5 seed)卻惡化 Gen0 的**極值**(1/5 seed),機制是「集中機率質量會抬高平均、壓縮上尾,
   而 GA selection 只讀最大值」。**Gen0 池大小正是決定極值統計量往尾部取多深的參數。**
   512 → 11,405 是 **22× 放大**,因此這是該機制最直接的操縱變因,而它**可在任一 shape 上檢驗**,
   不需要 treatment 豐富。medium 與 large 併跑還能給出跨 shape 的梯度(見 §12.4 第 4 點)。

**(C) tiny 仍排除。** tiny 的 Formocast 預測全為哨兵值(30,490/30,490 = 100.00 %),activated gene = 0,
兩臂的 Gen0 分布在建構上完全相同 → native 版無 treatment 可測。

**已驗證的前提(fail-closed 條件之一)。** medium 與 large 的 config 除了四個 `ProblemSizes` 數字外
**逐位元相同**,同樣內嵌 9,918 個 `MatrixInstruction` 項,故 medium 的 `max_sp_sz` 亦為 9,918 > 512,
native 下**同樣膨脹到 `int(9918×1.15) = 11,405`**,不會落入 `ga.py:119` 的
`max_sp_sz < pop_size/5` 砍半分支。兩 shape 的 Gen0 規模自變數因此完全對齊。
*(驗證方式:`diff` 兩份 `config/s14-pershape-{medium,large}-seed_24001.yaml`;`grep -c MatrixInstruction`。)*

**方法學上的誠實揭露(post-hoc scope extension)。** medium 是在**已看過 capped-medium 結果之後**才加入
本 addendum 的,因此 medium 的納入決策**不是盲的**。仍屬有效預註冊的是 **native-P0 的結果本身**——
它尚未執行、亦未被窺視。為使 Q3 成為真正可否證的檢驗,§12.4 第 4 點在執行前明文寫下**方向性預測**;
若結果與預測相反,必須照實記錄為機制假說被推翻,不得事後改寫預測。

### 12.3 實驗設定與逐項理由(pre-registered)
- **shape**:**large** `(2304,1024,1,214336)`(RBS=0)**與 medium** `(256,256,1,1024)`(RBS=4096);tiny 排除(§12.2)。兩 shape 的 `max_sp_sz` 均為 9,918 → native Gen0 均膨脹到 11,405(§12.2 已驗證)。
- **P0**:**原生**——**不設** `DUCTILE_FORCE_P0`,讓 constructor 依 `ga.py:118` 膨脹 Gen0 到 `int(9918×1.15)=11,405`,再每代 decay 回 512(`ga.py:116/293`)。**理由:本實驗唯一自變數就是 Gen0 規模。**
- **其餘 pins 與 512 版完全相同**:`n_gen=30` + 原生早停 `period=5`、`NEtV=128`、`n_jobs=1`、large RBS=0、gen-10 檢查點。**理由:除 P0 外一切不變,才能把差異乾淨歸因到 Gen0 規模單一因子。**
- **arms**:G(native P0,uniform)/ F(native P0,**注入同一份 Lock B capped 權重**:large 用 `ga-weights-large.json`、medium 用 `ga-weights-medium.json`)。**理由:treatment 必須與 512 版完全相同的 guidance,只差 Gen0 大小 → 隔離 P0-scale 軸。** 不做 Arm S(本 addendum 問 P0-scale 軸,非 physics-direction;省成本)。
- **seeds**:**沿用相同 5 seed 24001–24005**,與 512 版**逐 seed 配對**。**deadline fallback**:縮為 3 seed(24001/24003/24005),穩健性檢查重方向一致性、不需緊 power;若降階必明確標註。
- **noise margin**:沿用各 shape 自身的 η —— large **η=0.1228**、medium **η=0.0041953**(pilot 殘差導)。**理由:η 是該 shape 的量測重複性,與 Gen0 規模無關;** 非退步門檻仍 `e^{−η}`。
- **GPU**:同 5 卡 **2,3,4,6,7(never 0/1)**,一 seed 一卡,G 先 F 後(序列;≤6 卡)。**shape 間亦序列**(同一張卡先跑完 medium 再跑 large),避免同卡並跑污染量測。detached、納入 resume 機制。
- **7× 交錯 G/F 重測(`(b)` 2026-08-12 補入預註冊)**:native 的 champion **必須**與 512 版跑**同一套**
  7× 交錯重測協定(同卡、同視窗、G/F 交錯、取中位數;`remeasure_interleaved_champion.py`),
  per-shape 起始臂沿用既有對抗平衡(`START_ARM = {medium: G, large: F}`)。
  **理由(此項原先遺漏,補記):** capped 版 §7.1/§7.2 的數字全部是 7×-重測中位數,其存在目的就是消除
  winner's curse。若 native 只用 GA log 記錄的 champion 分數,兩邊就是**不同量測協定**的產物;
  且偏差方向最不利 —— winner's curse 的量級隨搜過的候選數上升,native 約 30,600 evals 對 capped
  約 7,689(4×),**native 的向上偏差更大**。此時 Q2 比較的會是「真實效應量差異 + 量測協定差異」,
  無法分離。跑同一套重測後,兩邊的 `ln(F/G)` 才是可比的。
- **fail-closed**:注入權重 sha256 == Lock B 對應 shape 權重檔 hash;驗證 P0 實際膨脹到 ~11,405 且 decay 生效(log 檢查 `Increasing pop_size` + 各代 pop 大小);group_0(9918)兩臂一致。

### 12.4 對比 512 版希望得到的 insight / 結論
1. **穩健性判定**:native 的 F-vs-G 方向與 512 **一致** → 結論對 Gen0 規模穩健,large 可去「capped」caveat;若**翻轉/消失** → 512 結論屬 scale-specific(誠實記錄)。
2. **稀釋量化(核心 insight)**:比較 F−G 效應量(log-ratio)於 512 vs native——native **顯著縮小** → 佐證「guidance 價值集中在小 Gen0」的機制敘事;native **仍維持** → 更強證據(即使抽滿仍有效)。
3. **native-scale 行為驗證**:prior 注入原生尺度 Ductile 行為是否正確(膨脹+decay、權重生效)——plumbing/健全性檢查。

4. **極值機制的方向性預測(`(b)` 2026-08-12,執行前寫定,可否證)。** 若 §7.2.1 的「集中機率質量→壓縮上尾→期望最大值下降」機制為真,則 Gen0 池由 512 放大到 11,405 時,抽樣往尾部取得更深、離散程度的影響**更為主導**,因此預測:**(i)** guided 相對 baseline 的 **Gen0 極值劣勢會擴大(而非縮小)**;**(ii)** 同時 guided 的 **Gen0 中心優勢應維持或擴大**(prior 未變,樣本更多 → 中心估計更穩);**(iii)** 跨 shape 梯度:large 有 5 個 activated gene(`PrefetchGlobalRead`、`TransposeLDS`、`UnrollLoopSwapGlobalReadOrder`、`GlobalReadVectorWidthA/B`)、medium 有 2 個(`DepthU`、`1LDSBuffer`),分布收窄幅度 large > medium,故**預測 large 的極值劣勢擴大幅度應大於 medium**。三項預測若被推翻(例如極值劣勢反而縮小),即為該機制假說的反證,須照實記錄,**不得事後改寫預測**。

### 12.5 內部效度與 claim 邊界
- native 版**兩臂共用 P0=11,405** → F-vs-G 對比在 native 內部**乾淨不偏**(同 512 之理,group_0 縮放兩臂抵銷)。
- **cross-P0 比較(512 vs native 效應量)** 是稀釋讀數;絕對 champion 品質跨 P0 不直接比(預算不同)。
- claim 依 charter §8.2/§8.6a:**two-sided**;scope 限「**受測 shape(large、medium)**、native-Gen0 對 P0-capped 結論之穩健性/稀釋(及 Q3 極值機制)」;不新增 §8.6 禁詞;5(或3)seed modest power、single cluster、不一般化。

### 12.6 排程與成本
- **wave**:排在 capped G/F(+conditional S 若觸發)+ 7× remeasure **全部完成、5 卡釋出後**(避免爭卡)。
- **成本 —— 已由 native 實測修正(2026-08-12)。原成本模型有誤,保留於此以資對照。**
  - **原模型的錯誤:** 先前的估算只計入 **GPU 評估時間**(capped seed 24001:medium 0.17 h / large 5.61 h,
    相差 ~33×),據此推得 medium 全程約 3 h。**它完全漏掉了 Gen0 的「抽樣」成本。**
  - **實測發現:** native 啟動後 **GPU 使用率為 0%**,五個 seed 全部卡在 `space.sample(11405)` ——
    這是**單執行緒 CPU 的拒絕抽樣**,速率約 1.1 it/s 且近乎定值(11 分鐘處 1.12 it/s,22 分鐘處 1.08 it/s)。
    抽滿 11,405 個互異合法個體需 **~2.9 h/arm,而且是在任何一次 GPU 評估發生之前**。
  - **修正後的 medium:** ~2.9 h 抽樣 + ~0.9 h GPU 評估 ≈ **3.8 h/arm** → G+F 序列約 7.6 h/seed →
    5 卡平行 **約 6.5–7 h**(原估 ~3 h)。
  - **對 large 的意涵(尚未實測,不得當作已驗證):** 此抽樣成本是**搜尋空間**的性質(30 個變數、
    `group_0` 9,918 值),而該空間 medium 與 large **完全相同**。因此 large 應是**額外增加**約 2.9 h/arm,
    而非按 33× 放大。粗估 large ≈ 2.9 h 抽樣 + ~39 h GPU ≈ 42 h/arm → ~3.5 天(5 卡平行)。
  - **對風險的意涵:** Gen0 全程無 checkpoint 保護(見下),而**無保護窗口 = 抽樣 + Gen0 評估**。
    medium 約 **3.4 h**(非先前所述的 27 分鐘,低估約 6×);large 約 **25.5 h**。
  - *Source:`s14_native_driver.log`;五個 seed 的 `medium.G.log` 進度列;`native_status.json`。*
  - native **large** ~1.5–2 天/seed/arm;5 seed 平行 5 卡、G/F 序列 → **~3–4 天**(3 seed fallback ~2–2.5 天)。
  - native **medium** 依同倍率外推約 **~1–1.5 h/seed/arm**;5 seed 平行 5 卡、G/F 序列 → **~3 h**,對總排程幾乎無影響。
  - **執行順序:medium 先、large 後。** medium 半天內即可得到 Q2/Q3 的首批讀數,可在投入 large 的 3–4 天之前先確認 plumbing(膨脹+decay+權重生效)正確,降低把數天算力花在錯誤設定上的風險。
  - deadline ~1.5 週內可行(估 ~day 6–7 完成)。
- **基礎設施**:沿用 baseline/guided 冪等 driver 模式,新增 **native 變體(不設 `DUCTILE_FORCE_P0`)**;納入 `s14_resume_all.sh` + host cron + supervisor,reboot 可續。**注意:native large 單次不中斷需求 ~2 天,對 reboot 最敏感**(單一 large 被砍從 gen0 重來,無 mid-run checkpoint)。
- **gate**:**照排**。capped-large 已完成且為「兩臂在 η 內無法區分」(§7.2),capped-medium 為「差異真實但方向不一致」(§7.1);兩者都是有效的穩健性/稀釋基線,且 Q3 的檢驗力來自 Gen0 規模這個自變數本身,不取決於 capped 是否顯示方向訊號。

### 12.7 失敗/降階
- **native Gen0 降級(stock Ductile fail-open)的處置 —— 執行前定案,`(b)` 2026-08-12。**
  已查證(2026-08-12):`space.sample()` 抽不滿時丟 `MaxIterationsReached`,`ga.py:289–293` 只記一行
  warning 就以 `pop_size // 2` 重試(`iter_mul=4`、`reuse=True`;僅當 `n_sampled == 0` 才丟掉 prior)。
  此段與 pinned qualification source **逐字相同**(4 份獨立快照,`ga.py` sha256 `32b3ed38fd09…`),
  確認是 **stock AMD Ductile 的刻意 fail-open 設計**,非本研究引入、亦非缺陷 —— 對生產用 tuning
  函式庫而言,「族群小一點但有結果」優於「硬報錯什麼都沒有」。
  - **問題所在:** CAP 版有 `DUCTILE_FORCE_P0` assert(`ga.py:302`)擋住這條路徑,但該 assert 以該
    環境變數為條件,**native 不設它 → 完全沒有防護**。且降級發生在 `__init__` **之後**的抽樣階段,
    建構時的 pin 抓不到。
  - **風險:** 若僅 guided 臂降級而 baseline 未降級,兩臂差的就不只是 prior,還差了族群大小,
    配對比較直接失效。(評估風險偏低:distinctness 由未受 guide 的 `group_0`(9,918 值)主導,
    受 guide 的 gene arity 都很小;較可能綁死的是 validity 而非 distinctness。)
  - **處置(pre-registered):** native runner 在**第一代評估時**檢查族群數;若 `!= 11,405`,
    先寫出 `native_gen0_degraded.json`(記錄 expected/observed、機制、上游驗證、seed/shape/arm),
    **再中止該 run**。
  - **理由:** Q2/Q3 的自變數就是 Gen0 規模,降級後的 run 既不是 512 也不是 11,405,屬**第三種條件**,
    納入會污染配對。
  - **但它不是「跑失敗」:** 降級若真的發生,是**關於 Ductile 原生行為的實質發現**,必須在報告中
    單獨陳述(哪個 shape/arm/seed、實際降到多少、baseline 與 guided 是否對稱),**不得**當成基礎設施
    錯誤吞掉,亦**不得**因此靜默重跑。
- capped 對應 shape 兩臂未能產出 champion → 該 shape 的 native 版無意義,不跑(large 與 medium 各自判定)。
- **deadline 壓縮時的優先序:medium 優先於 large**(成本 ~33× 低,且是唯一有可解析效應量的 shape;large 若不得不砍,記為降階並標註)。
- deadline 不足 → 降 3 seed(標註)或只跑到能判方向一致性。
- native P0 未如期膨脹/decay(fail-closed 失敗)→ 停、報 plumbing,不硬跑。

---

## 12A. `REPORT-LOCATION-20260813` —— 報告檔案位置(bookkeeping amendment,owner 決定)

**變更:** `formal_report_path` 與 `tranche_final_report_path` 由
`reports/full-ga-baseline-vs-guided-outcome-report.md` 改為
`reports/staged/full-ga-baseline-vs-guided-outcome-report.md`;三份 per-shape 附冊同樣置於
`reports/staged/`。

**為什麼這不是「事後修改預註冊以遷就漂移」。** 2026-08-13 稍早,本檔案的 formal report 被發現
誤置於 `reports/staged/` 且改了檔名,與預註冊路徑不符;當時的處置是**搬動檔案去符合預註冊**,
理由是不得為了遷就漂移而改預註冊。owner 隨後決定 S14 的報告應與其餘所有 gate 一致,統一放在
`reports/staged/`(S00 / S10 / S10R2 / S10R3 / S11 的 design 都預註冊該目錄)。

兩者的差別是**誰在決定、以及決定的是什麼**:前者是讓一個意外漂移追認自己,後者是 owner 對
**文件擺放慣例**做出的明示決定。`formal_report_path` 是 bookkeeping pointer,**不是**
scientific criterion —— 它不涉及任何 hypothesis、estimand、metric、threshold、gate、claim 或
measurement boundary,改它不會、也不能改變任何判定。§10 的 acceptance criteria 與 §10.4 的
per-shape gate 一字未動。

**紀錄要求:** 本 amendment 必須與其餘 amendment 一同列於 closure report 的 traceability,並
明載「僅變更檔案位置」。任何未來對 `formal_report_path` 的變動都必須以同樣方式留痕,不得靜默
編輯 frontmatter。

---

---

## 13. `PENDING_HUMAN_DECISION` — medium 重測量測缺陷的處置(design-discussion 2026-08-13,兩位 reviewer AGREE)

> **本節為 non-authoritative decision packet,尚未經 owner 核准。** 在核准之前,§10.2 / §10.4 的
> 預註冊估計量與 gate 一律維持原狀,不得依本節內容改動任何分析、標籤或 claim。核准後才由主
> session 寫回對應的 authority 章節。
>
> **流程紀錄:** 兩位獨立 reviewer(fresh threads,相同初始 prompt,prompt 不含 coordinator 偏好)
> → 2 輪交互詰問 → 1 輪 evidence-backed final positions → **雙方 AGREE,無保留異議**。
> agent wall-time 約 43 分鐘(上限 60)。所有承重事實由 coordinator 獨立複驗。

### 13.1 問題與 scope

S14 的**主要指標** —— 7× 交錯 champion 重測 —— 在 `medium` shape 上被證實不可重複。同一個固定
config、同一張卡、同一個 process、~21–25 秒視窗內量 7 次,結果呈**雙峰**:要嘛落在該臂最大值的
95–100%(乾淨),要嘛掉到 0.07–0.78。

要決定三件耦合的事:**(D1)** 是否更換預註冊的 median-of-7 估計量;**(D2)** gate 由哪個 noise
margin 治理;**(D3)** 由此導出的逐 shape claim 階梯。

### 13.2 決定一切的框架事實 —— 這個決定改變不了任何結論

§10.4 的 per-shape gate 是**四項的連言**(各需 ≥4/5),而它**早已在三個「污染碰不到」的分項上失守**
—— 那三項讀自 GA trajectory,不經重測:

| shape | Gen0 | gen-10 | AUC | 需要 |
|---|---:|---:|---:|---|
| medium | 3/5 | 3/5 | 3/5 | ≥4/5 |
| large | **1/5** | **2/5** | 3/5 | ≥4/5 |

且實際重算證實:median → max **不改變任何 shape、任何 campaign 的 directional count**
(3/5、2/5、3/5、3/5、1/5 兩者相同)。

**因此本節所有決定都是「紀錄的誠實性」問題,不是「結論」問題。** 這一點必須寫進任何 amendment,
它是把一個事後修改從「可疑」轉為「可稽核」的關鍵。

### 13.3 D1 — 估計量:維持 median-of-7,不採用任何次要估計量

**採用:** 三個 shape 一律維持預註冊的 median-of-7。`max` 僅以**標註清楚、三 shape 一致套用的
敏感度列**出現,並必須同時附上不變性證明與其兩個已知失效模式。

**捨棄的方案與理由:**

- **改用 max 為主要估計量** —— 捨棄。它買不到任何結論改變,卻是事後、且對受測臂有利的修改
  (governance §4:「post-label relaxation that could increase the probability of the desired
  outcome」強制 successor)。且有**實際反例**:capped C1 seed 24005 arm F **7 次全部污染**,
  max 給出 10,535,對照同一 config 在 C2 的乾淨值 13,407,**低估 21.4%**。這同時推翻了
  「沒有任何臂 7 次全掉、所以都可救」以及 i.i.d. 的 `0.48⁷ = 0.6%` 計算 —— 同一視窗內的重複
  是**受電源治理器相關的**,不是獨立的。
- **乾淨模態平均(reviewer B 提出後自行撤回)** —— 捨棄。B 驗證後發現它**在紀錄用的 campaign 1
  上會把 non-regression 從 3/5 推到 4/5、正向從 2/5 推到 3/5**,自我否定了「可證明不改變任何判定」
  這個唯一的可採性辯護。B 主動撤回,改列為**有效性分類器**(見下)而非估計量。

**保留的用途:** B 的「≥3 個乾淨重複」規則作為**有效性分類器**,不用來算比值。套用到 campaign 1,
它標出 seed 24004 arm G 與 seed 24005 arm F **無法由任何重新分析救回**,並指出修復後的重測必須
涵蓋哪些 champion。

**Campaign of record:** **campaign 1 為紀錄用量測**。campaign 2 於 2026-08-12 14:01–14:04Z
**在解盲後就地覆寫**了 `stage3_baseline/` 的 campaign 1,且 campaign 2 **對受測臂更有利**
(median F/G 1.0274、3/5 對比 C1 的 0.9971、2/5)。C2 列為**事後診斷性重製**,兩者都報告,
皆不產生 tier,**不得平均、不得擇一**。

- **現存風險(必須處理):** canonical path 未留下任何 `superseded_*` 標記,而
  `analyze_medium.py` 讀的正是 canonical path —— **今天執行它會報出 C2**。所有分析腳本必須改指向
  `medium_recheck_control/.../preserved_campaign1_*` 的保存路徑。
  (2026-08-13 已處理:`analyze_medium.py` 現在**強制**要求 `--campaign {1,2}`,不預設、不平均,
  並在輸出標頭印出實際讀取的路徑;缺少該參數即拒絕執行。)

- **⚠️ 修訂 2026-08-15(owner 裁決)—— 上兩段的 campaign-of-record 與 canonical 事實已變更。**
  **本節預先登錄的文字不改寫,以下為變更紀錄。**

  **(1) Campaign of record:兩者皆非。** 上文「**campaign 1 為紀錄用量測**」這項認定已被
  owner 於 2026-08-15 取代。裁決是**不拔擢任何一個 campaign** ——
  **由一個在修復後儀器上執行的新 campaign 取代兩者**,那才是有意義的量測。
  該新 campaign 目前為 **pilot only**,完整 campaign 延後且**以 pilot 結果為條件**
  (`PENDING_HUMAN_DECISION`)。
  **「兩者都報告、皆不產生 tier、不得平均、不得擇一」這條處置不變。**

  **(2) 「今天執行它會報出 C2」自 2026-08-15 起為假。** 同日 owner 裁定
  **canonical capped medium 五個 seed 一起 revert 回 campaign 1**
  (campaign 2 於 revert 前先保存到
  `medium_recheck_control/capped/seed_*/preserved_campaign2_20260815T000000Z/`;
  **seed 24004 除外 —— 該 seed 的 campaign 2 於 2026-08-13 被就地覆寫且無備份,不可回復**)。
  因此**現在讀 canonical 會報出 C1**,方向與原文相反。
  **危害本身沒有消失,只是換了方向:** 一支讀 canonical 卻自稱在報 C2 的腳本,
  現在會**無聲地把 campaign 1 標成 campaign 2**。
  **這件事已實際發生於 `scripts/s14_medium_ratio_analyze.py`**
  (其 `started_utc >= "2026-08-13"` 守衛對 campaign 1 永不觸發,因 campaign 1 全部 started 於
  2026-08-11),**已於 2026-08-15 修復**:改讀保存路徑、缺 artifact 時以非零 exit **fail closed**、
  並改由腳本自身位置推導 run root。`analyze_medium.py` 亦已改為
  **兩個 campaign 都從明示的 off-canonical 路徑讀,完全不再讀 canonical**。

  **(3) canonical 現況是刻意的混合狀態,不予調和。**
  `stage3_baseline/seed_*/medium/`(**capped**)現為 **campaign 1**;
  `stage5_native_baseline/seed_*/medium/`(**native**)仍為 **campaign 2**。
  **owner 明示此狀態為已知、已接受、刻意 —— 不是疏漏,也不是待辦事項,不要調和它。**
  **沒有任何資料被刪除或搬走**,兩個 campaign 的 artifact 都仍保存在 canonical 之外。

  **(4) 對本設計其餘部分的影響:無。** 上述四點不改動 §10.2 / §10.4 的預註冊估計量與 gate,
  也不改變 medium 端點 `NOT_EVALUATED / instrument-invalid` 的提案狀態。

- **⚠️ 更正 2026-08-13 —— native 也被就地覆寫,原文的對照舉例是錯的。** 上一版以
  「對照 `stage5_native_baseline/seed_24005/medium/` 有兩個 `superseded_*`」暗示 native 側留了痕跡。
  **實際不是。** `[CODE AUDIT]` native medium 的 canonical artifact 於 **2026-08-12 14:05:07–14:08:18Z**
  同樣被 campaign 2 就地覆寫(檔案 mtime),而 `superseded_*` 標記只存在於 seed 24001(1 個)與
  seed 24005(2 個),seeds **24002 / 24003 / 24004 為 0 個** —— 且那些標記是更早的重試殘骸,
  **不是** campaign 覆寫留下的。也就是說 native 與 capped 有**同一個**未追蹤覆寫問題,先前只記錄了
  capped 這一半。

  native 兩個 campaign 的數字(來源:C1 =
  `medium_recheck_control/native/seed_*/preserved_campaign1_20260812T135613Z/`,
  C2 = `stage5_native_baseline/seed_*/medium/champion_interleaved.json`):

  | campaign | median F/G | 逐 seed F/G | 正向(`ratio > 1`) | **正向(預註冊 `> 1+δ_s`)** | non-regression |
  |---|---:|---|---:|---:|---:|
  | native C1 | **1.1391** | 0.4865 / 2.2663 / 0.3735 / 1.1391 / 1.9725 | 3/5 | **3/5** | 3/5 |
  | native C2 | **1.0041** | 1.0041 / 0.8256 / 1.0246 / 0.7029 / 1.0537 | 3/5 | **2/5** | 3/5 |

  **⚠ 更正 2026-08-13(第二次):** 本表初版的「正向」欄用的是 `ratio > 1`,**不是預註冊判準**。
  §10.2 的改善判準是 `F/G > 1 + δ_s`(`δ_s = 0.004204159905590865`,門檻 1.0042042)。兩者在
  native C1 相同(3/5),但在 **native C2 不同:預註冊判準是 2/5,不是 3/5**。差別完全來自
  seed 24001 —— 其 `ratio = 1.004079`,**以 0.0125 個百分點之差落在門檻下方**。
  以 artifact 為準:`stage5_native_baseline/seed_*/medium/champion_interleaved.json →
  F_over_G_gt_one_plus_delta_s` = `False, False, True, False, True`。
  引用任何「正向」計數時**必須指明判準**,否則本表會與 artifact 讀起來互相矛盾。

  順帶:一個預註冊判準竟由 0.0125 pp 的差距決定,本身就是 `η_medium = 0.42 %` 對其所裁量的量
  過緊的第二個獨立佐證(第一個見 §13.4)。

  **方向計數兩者相同(3/5、3/5),所以此更正不改動任何判定。** 但兩點必須入帳:(a) C1 的逐 seed
  離散極大(0.37 倍到 2.27 倍),正是 §13.1 所述雙峰污染的樣態,native 端點因此與 capped 同樣屬於
  `NOT_EVALUATED / instrument-invalid`;(b) 與 capped 不同,native 這裡**較有利的是 C1 而非 C2**,
  所以「覆寫方向一致地偏袒受測臂」的說法**不成立**,不得如此陳述。operational-correction 紀錄
  必須同時涵蓋 capped 與 native 兩側。
- 需要一份 operational-correction 紀錄說明此次未留痕的就地覆寫。

**medium 的 final-champion 與 non-regression 端點設為第三種狀態
`NOT_EVALUATED / instrument-invalid`** —— 既非 pass 亦非 fail,兩個 campaign 皆然。

**真正的修復是儀器而非統計量:** 註冊 `MEASUREMENT-WARMUP-AMENDMENT`(Layer A,R3 權限),把 warm-up
從「次數」改為**牆鐘時間 ≥ 50 ms**,三 shape 一致,**在執行前註冊**,並事先承諾新舊數字並列發表、
新數字標為事後修復。

- **此修復為條件性的。** 兩個 RBS=4096 的長暖機變體**崩潰 25/25**(50 次 `hipModuleLoad rc=-6`),
  而掃描中**所有 0 掉點的點都在 RBS=0**,後者單獨就讓量測水準從 12,430 移到 14,153(+14%),
  **是不同的 estimand**。
- **先跑可行性探測:5,136 次暖機 @ 釘死的 RBS=4096**(在 RBS 4096 下 medium 每次約慢 14%,
  5,136 次 ≈ 58 ms,已過拐點)。**這個組合從未被嘗試過** —— 兩個崩潰的變體都用 32,100。

### 13.4 D2 — Margin:封存的 pinned η_s 治理不變,但必須完整揭露

**採用:** pinned `η_s` 維持治理地位,逐 shape 不變。

**捨棄:** 由重測自身重算的實測 η —— 它**循環**(用被 gate 的那批重複去算 gate 的門檻),而且被
tiny 的 null control **證偽**:在實測 margin 下,一個**逐位元相同、零 treatment** 的對照會被判
**3/5 退步**。一個會把已知的零判成退步的 margin,沒有資格取代。

**必須揭露的事實 —— 三個 pin 都是意外,不是雜訊模型:**

| pin | 來源 | 與被 gate 的量測的關係 |
|---|---|---|
| `η_medium = 0.0042` | anchor 跑在 4,629 / 3,200 / 2,127 GFLOP/s | 比 champion **慢 3–7 倍**(暖機 8.6–21 ms,曝險低得多),pilot **0/21 掉點**;它比 champion 自己的乾淨模態 P95(0.0116)還**緊 2.8 倍** |
| `η_tiny = 0.4466` | pilot tiny anchor 1 的**一個深度掉點**(0.415 對比 2.128 的模態) | 由單一污染點製造 |
| `η_large = 0.1228` | 兩個 max/min 為 1.24 與 1.42 的 anchor | champion 重測(1.02–1.05)**重現不出來** |

- **索引 §7.1a 中「pin 對乾淨的 medium 量測大致正確」一句予以刪除。**
- 三個 shape 都要**同時報告兩種 margin**,並明說:**在 medium 上,保留 pin 並不是比較保守的選擇**
  —— 它比觀測到的 null 離散度緊約 30 倍,所以「保留 pin」是治理決定,不是安全邊界。
- **η 是錯的尺度**:它量的是**同一個 config**的窗內重複性,而 estimand 是**兩個不同 champion**的
  比值。臂間離散度是窗內值的 4.9 倍(tiny)/ 2.0 倍(large)。

**新增:以 tiny 的 null control 作為 large 的參考包絡。** large 每個 seed 的 |ln F/G|(最大 0.0749)
都落在 tiny 零 treatment 包絡(最大 0.1247,sd 0.0715)**之內**。

- **邊界:這是參考包絡,永遠不是門檻**,不得轉成 margin、floor 或 pass/fail。
- 其可轉移性建立在實測的 champion 層級離散度上:**large 1.129、tiny 1.182、medium 1.222**
  —— tiny **並不特別平坦,large 才是最平的**,所以此轉移偏保守。(reviewer B 原本以「過度轉移」
  反對,實測後自行證偽並撤回。)

### 13.5 D3 — 逐 shape claim 階梯

| shape | 可說 | **不可說** |
|---|---|---|
| **medium**(確認性) | gate **未達成**(Gen0/gen-10/AUC 各 3/5,皆為污染碰不到的分項);final 端點 `NOT_EVALUATED / instrument-invalid`,並完整報告缺陷、證據與根因 | 任何 non-regression 通過、任何 improvement、任何由該作廢端點導出的 tier |
| **large**(確認性) | gate **未達成**(1/5、2/5、3/5、3/5)。5/5 non-regression **僅作為一個分項**報告,**不可單獨引用**,並揭露它在窗內 margin 下是 3/5、且 `η_large` 由 champion 重測重現不出來的 pilot anchor 撐著。improvement 0/5。必須附 §7.2.1 的根因 | 「large 通過」、任何優越性主張、把單一通過分項升格為 shape 層級結論 |
| **tiny**(探索性,無 gate) | 雙軌報告:(a) guidance 問題 `not evaluated / not activated`(0/27 gene),且「未評估 ≠ 無效果」;(b) tiny 是**意外的 null control**,校準了 F/G 統計量在真實零效應下的分布。其 pinned margin **結構上空洞**(要失敗需掉 36%、要通過需 +56%,而該 shape 的 champion 全距只有 1.18 倍) | 「tiny 退步」、「guidance 傷害了 tiny」、任何把 tiny 用於確認性陳述 |
| **合併 §8.2** | 修正後的稀疏 capped prior **未達成**兩個確認性 shape 的預註冊 gate | 「無效果」、「模型沒用」、任何 aggregate rescue、任何一般化/部署/加速措辭 |

- **Conditional Arm S 不觸發**(§10.2 要求確認性 shape 通過 gate,兩者皆未通過);physics-direction
  歸因延至 S20。
- **預註冊預測但檢驗儀器已被懷疑時的記錄方式 —— 四列分開,永不合併:**
  (i) 預測原文與註冊日期;(ii) 完全照預註冊方式計算的分析,不得更動;(iii) 儀器判定與其證據,
  以及**相對於解盲的**發現日期;(iv) 任何修復後的估計,明確標為事後。**(ii) 永不被 (iv) 覆寫。**

### 13.6 必須更正的既有紀錄

- **「champion selection 未受污染」現為紀錄事實而非推論**:`selection_candidates`
  在 **40/40 個 arm-entry** 中都只有一個候選,且 resolved `canonical_hash` 與 `best_individual_hashes`
  在 **40/40** 相符。**路徑更正 2026-08-13:** 本節初稿引用 `optimization_result.json` 的
  `resolution_provenance`,但該欄位在**全部 45 個**該類檔案中皆為空 `{}` —— 欄位不在那裡。可重現的
  路徑是 `champion_interleaved.json` → `arms.{G,F}.resolution_provenance.selection_candidates`
  (20 檔 × 2 臂 = 40 個 arm-entry),`best_individual_hashes` 則取自各臂自己的
  `optimization_result.json`。兩個計數已由更正後的路徑重算,維持 40/40 與 40/40 不變;錯的只有引用。那個被污染的單次值(2,961.87 = 45.3 µs,對照全速的 ~9.9 µs)雖被記錄,
  **從未仲裁過任何事**。
- **GA-oracle 疑慮降級為 residual**,且 Gen0 梯度論證**予以撤回**(`best_gflops_so_far` 依定義單調,
  模態樂透會預測同樣的觀察)。有效證據改為:(a) `generation_Q_median_any_valid`(對約 510 次評估
  取中位數),medium 落在兩個免疫 shape 的**範圍之內**(逐代平均 |Δ|:medium 5.58/4.61% vs
  large 6.98/6.11%、tiny 6.50/4.21%);(b) 機制曝險上界 —— 一次 client invocation 內每代約
  508–512 次評估、每次約 6.4 ms,一次約 50 ms 的升頻只曝險**約 8/510 ≈ 1.6%**,對比重測的 28–48%。
- **卡別平反**:tiny-on-hip-5 的論證**撤回**(tiny 是最無法偵測時脈病理的工作負載)。改用**卡內對照**
  —— noise pilot 也跑在 `HIP_VISIBLE_DEVICES=5`、同一 client、同樣 RBS 4096,卻 **0/21 掉點**,
  因為其 anchor 慢 3–7 倍。**caveat:** 2026-08-10 的重開機改變了 GPU 編號,08-07 的 index 5
  未必是 08-12 的同一顆實體晶片。
- **臂間不對稱污染是直接觀測到的,必須報告。** medium 的 champion 驗證值 `WinnerGFlops`:
  G = 2,961.9 / 8,846.0 / 4,210.4 / 12,516.2 / 11,542.6;
  F = 13,590.7 / 12,773.8 / 8,384.2 / 14,040.5 / 13,359.8;**中位數 8,846 對 13,360**。
  (逐臂列出即可,不必認定污染臂數 —— 該數字取決於假設的乾淨基準,兩位 reviewer 分別數為 3/5 與 4/5,
  而中位數已足以承載論點。)
  **後果:「污染是單向且兩臂對稱、所以在配對比值中抵銷」此一說法不成立。** 正確措辭:污染是單向的;
  **是否兩臂對稱為 `NOT_EVALUATED`**,且因逐代 benchmark CSV 未保留而**事後無法查證**。
  報告另須警告:`original_final_gflops` **絕不可**用作終點指標 —— 用它的話 guided 會**純因污染**
  而看起來好得多。
- **§12.2(B)2 為 native addendum 納入 medium 的理由作廢**(「medium 是唯一兩臂差異可量測的 shape,
  0.36×–2.12×」—— 那些數字正是污染物)。須以 amendment 更正。§12 Q2 在 medium **final 端點**上的
  跨 P0 稀釋比較記為 `NOT_EVALUATED`;**Q3(Gen0)不受影響**。
- `medium_remeasure_root_cause.md`:「2,962 = GA fitness」為誤(`best_fitness` 是 13,679.1;
  2,961.87 是 champion 驗證值);「25/70」應為 23/70。
- 索引 §7.1c 為斷鏈參照,須補寫或移除。
- 索引 §7.1a 的若干數字需重新對齊:「140 筆 / 27.9%」是 **campaign 2 單獨**的,而**紀錄用的
  campaign 1 是 46.4%**,四組合計 104/280 = 37.1%;1.2098 是 capped-C1 的子集,140 筆合計為 1.0503;
  large 的視窗約 107 秒而非 27–40 秒;medium 的 run 有 20 個而非 15 個;重複位置的趨勢符號**與子集
  相關**(−0.0059 vs +0.0088),**不得引用為負向趨勢**;掃描在拐點以上**並非單調**(20,544 次暖機
  仍有 4%)。
- 移除殘留的編輯暫存檔 `s14-stage1-full-ga-outcome-design.md.tmp.579306.678ae5c65170`
  (2026-08-10,內容為 §12 出現前的舊版),以免 closeout 封存時被誤認為 authority。

### 13.7 便宜量測 — 收斂後的順序

| # | 項目 | 成本 | 決定什麼 |
|---|---|---|---|
| ~~owner action~~ | ~~**鎖頻驗證**~~ **2026-08-13 降級,不再列為優先。** 直接的 1 kHz 時脈追蹤已**否證**時脈說(見下),鎖頻現在只是在檢驗一個資料已不支持的假說;且 `--setperflevel high` 在此環境**確實不生效**,真正的鎖頻需要對卡的**寫入權限**(`pp_od_clk_voltage` / `amd-smi`),那是 governance escalation,不是十分鐘的 `sudo` 工作 | — | 機制維持 `NOT_EVALUATED`;但**修復路徑(D1)不依賴知道成因** |
| 1 | **合併式跨視窗 / A-A 實驗**:一個 large seed,12–15 個視窗分佈於 12–24 小時,每個視窗量**三臂** —— G、F、以及**第二個獨立的 G 實例** | ~50 分鐘 GPU,**可按視窗中斷** | 同時給出真實 F/G 統計量的跨視窗離散度,以及一個**中心已知為 1.0** 的 G/G′ null,故偏差與離散度都可檢驗 |
| 2 | **可行性探測:5,136 次暖機 @ RBS=4096** | ~5 分鐘 | 決定在釘死的 estimand 下「丟棄重測」這條路是否存在 |
| 3 | 修復後的 medium 重測(**條件於 2 通過**) | — | caveat:32,100 + RBS 0 是**不同的 estimand**;比值可比,絕對水準不可代入紀錄 |
| 4 | 保留逐代 CSV 重跑一代 medium GA | — | 降為最後 |

**⚠ 時脈說已被直接量測否證(2026-08-13)。** 非 sudo 驗證階梯的第 1 步:3 個 seed × 14 筆紀錄,在**實際
進行中的 medium remeasure 上**以 1 kHz 同步採樣 `sclk` 與 `busy`,每次 idle gate 皆乾淨(GPU 0%、host
load 0.031–0.079 / 224 cores),且現象有重現(**25/42 掉點**)。結果:

- 時脈與吞吐量的相關是**負的**(Spearman **−0.32**);
- 掉點那幾次的時脈中位數**更高**(**1798 MHz**),乾淨的反而較低(**1689 MHz**);
- **每一次**重複,不論乾淨與否,都達到 **1512–2065 MHz** —— 沒有任何一次停在 132 或 500 附近;
- 雙向反例:在 2065 MHz 峰值下只有最大值的 0.470;在 1674 MHz 下卻有 0.997;
- 掉點的那幾次**耗時更久** —— kernel 是真的跑得比較慢,不是回報假象。

另兩項附帶更正:(a) GPU 5 在持續負載下只到 **~1770–1810 MHz**,所以「乾淨 = 2100 MHz」這個基準是錯的,
任何對 2100 做的比值算術作廢;(b) sysfs 在負載下回報的是**連續**的當前時脈(500/2100 為界),
**不存在三個離散 DPM 檔位**,所以「卡在低檔位」這個假說在物理上從來就無法被檢驗。

**先前那次鎖頻嘗試的 null 是「無資訊」,不是弱證據** —— `setperflevel high` 根本沒生效(「pinned」臂的
時脈軌跡與 control 完全相同,75% 的採樣低於 200 MHz),因此**兩個方向都不得引用**。

**儀器限制,如實記錄:** 該追蹤的有效解析度約 8 ms(數值每約 8 ms 才更新一次,且看似經 SMU 濾波),
**無法解析 3.2 ms 暖機期間內部**的時脈行為,只能界定 GPU-active 階段的包絡。因此時脈說是**被不利證據
壓低**,而非被排除。

**倖存且不得一併撤回的部分:暖機時間與污染的經驗相關性完全不受影響** —— 掃描(3.2 ms → 48%、
601 ms → 0%)、卡內 pilot 對照(anchor 慢 2.9–6.3 倍、0/21)、以及 tiny 對暖機長度的實測不敏感性,
三者各自成立。**暖機時間可以預測污染;現在沒有依據的是「時脈斜坡是原因」這句話。**
機制現況:`NOT_EVALUATED`。倖存的未檢驗候選:XCD/CU 配置、MALL/L2 residency、GSU-4 workspace 競爭,
以及任何能解釋「時脈更高但 kernel 更慢」的機制。

### 13.8 Acceptance criteria / falsification

- 5,136 / RBS 4096 探測**通過**,且修復後重測的 10 對 medium champion 與 max-of-7 在乾淨模態離散度
  內吻合 → 回復論述獲確認,修復數字可作為**標註清楚的事後修復**報告。
- 探測**崩潰** → 在釘死的 estimand 下**不存在**丟棄重測的路徑;medium 端點維持 `NOT_EVALUATED`,
  報告載明原因。
- A/A 對照顯示 G/G′ null **中心偏離 1.0** → 臂序不對稱為真,交錯設計本身需重新檢視。
- ~~鎖頻**消除掉點** → 機制獲實證~~ **2026-08-13 已由更強的檢驗取代並且結論相反:** 直接時脈追蹤顯示
  掉點發生在**較高**時脈下,時脈說因此**被否證**而非待證。暖機**相關性**仍存活,機制降為
  `NOT_EVALUATED`,替代解釋(XCD/CU 配置、MALL/L2 residency、GSU-4 workspace 競爭)全部未檢驗。

### 13.9 殘餘不確定性(須寫入報告,不求解決)

- **暖機相關性的成因為 `NOT_EVALUATED`。**(2026-08-13 改寫;本條原文為「時脈機制由暖機掃描、DPM 算術
  與 tiny 的實測時脈不敏感性推論而得;無直接鎖頻證據」。)直接的 1 kHz 時脈追蹤已**否證**時脈說,
  見 §13.7。**相關性成立,成因不成立。**
- **任何 shape 都不存在跨視窗 / 跨日的重複性資料**;窗內 η 是一個緊度未知的**下界**。
- tiny 的單一掉點(第 7 次 / 共 7 次,在 37.8 秒視窗的第 34.7 秒;掃描在 5,136 處非單調)
  為 `NOT_EVALUATED`,且 medium 的機制對它**反證**。
- 搜尋期污染是否兩臂對稱:`NOT_EVALUATED`,事後不可查證。
- campaign 1 為何比 campaign 2 髒 1.7 倍:未解釋。
- 跨 campaign 重現性的對比僅建立在 **n = 2** 個 campaign 上。

### 13.10 Reviewer 交鋒紀錄(供稽核)

- **各自反轉一次:** A 原主張「不加任何次要估計量」→ 採納 B 的乾淨模態平均(承認自己對 max 偏差
  的論證未量化);B 原主張乾淨模態平均 → **撤回自己的提案**(驗證後發現它在紀錄用 campaign 上
  favourably 移動計數)。兩次反轉後**回到 A 的原始立場**。此事實須如實記錄為**反轉**,而非
  「一開始就一致」。
- **A 接受的 B 之更正:** pilot-η 鑑識(撤回「pin 對乾淨 medium 大致正確」)、修復在釘死 RBS 下
  未經驗證、Gen0 梯度論證無效、卡別平反需替代論證、A/A 對照優先。
- **B 接受的 A 之更正:** campaign of record 與就地覆寫、不採用任何事後次要估計量(含自己的)、
  卡別平反被高估、tiny 包絡可作為 large 的參考、四列記錄結構、max 反例的框架
  (21.4% 低估比跨 campaign 的 26.4% 更銳利)、i.i.d. `0.48⁷` 無效。
- **B 對自己偏差論證的更正:** 其 +0.43% 是**水準**偏差;進入配對比值的是兩臂乾淨計數的**差額**,
  約 **0.06–0.07%**,比它引用的數字小約 6 倍。candidate 因此**不引用任何偏差數字**;若日後需要,
  措辭應為「典型乾淨計數配對下差額 ≲0.1%,僅在 7-vs-1 的極端情形升至 ~0.43%,而該情形已被
  ≥3-clean 分類器標出」。

---

## 14. `PENDING_HUMAN_DECISION` — peak-of-7 作為 medium 端點的「能力」論證(design-discussion 2026-08-13 第二場,兩位 reviewer AGREE,無保留異議)

> **本節為 non-authoritative decision packet,尚未經 owner 核准。** 核准前,§10.2 / §10.4 的預註冊
> 估計量與 gate 一律維持原狀。reviewer consensus **不授權**任何變更。
>
> **流程紀錄:** 兩位獨立 reviewer(fresh threads,相同初始 prompt,prompt 不含 coordinator 偏好)
> → 1 輪交互詰問 → 1 輪 evidence-backed final positions → **雙方 AGREE,無保留異議**。
> agent wall-time 約 27 分鐘(上限 60),輪次 1+1(上限 2+1)。所有承重事實由 coordinator 獨立複驗;
> 其中兩項由 coordinator 推翻 reviewer 的計算(見 §14.6)。

### 14.1 問題與 scope

owner 提出一個與 §13.3 已駁回者**不同**的論證。§13.3 駁回的是「max 是較好的**估計量**」;
owner 提的是**能力(capability)**框架:

> 既然污染是單向向下的,一次落在乾淨模態的重複就是「這個 config 做得到」的真實觀測。
> 若 medium 被觀測到達到 ~13,500 GFLOP/s,那就證明它做得到。其他 shape 穩定,所以只有 medium
> 需要這樣處理。那麼 peak-of-7 是不是比 median-of-7 更適合當 medium 的端點?

這是**新論證**,不是舊論證換句話說 —— 它主張的是一個關於單臂能力的事實,而非一個估計量的優劣。
因此必須獨立審查。

### 14.2 統一建議:駁回,但 owner 的前提有一半是對的

**必須先承認的部分:peak-of-7 在回復乾淨水準上確實遠優於 median-of-7。** 兩位 reviewer 各自量化
後都確認這一點,不應被辯掉。native C1 的 max-ratio 壓縮到 0.889–1.068,而 median 橫跨 0.37–2.27。

**但它不能轉移到端點上,因為端點不是一個水準,而是「兩個 champion 的比值,對照一條預註冊的容忍帶」。**
三個彼此獨立的否決理由:

| # | 類型 | 內容 | 量級 |
|---|---|---|---|
| 1 | **偏差**,`max` 專屬 | 乾淨模態本身是雙向雜訊;max-of-7 即使在**零污染**下也系統性高估 | +0.51 %(k=7),對照改善門檻 **+0.42 %** |
| 2 | **變異**,與估計量無關 | 跨視窗的水準漂移,存在於非全污染的視窗中 | **0.5–2.8 × η_medium** |
| 3 | **不可證偽性**,結構性 | 能驗證 peak margin 的乾淨模態校準,在釘死的 estimand 下**取得不到** | 見 §14.4 |

**理由 1 是 `max` 專屬的**:乾淨計數在同一視窗內兩臂相差 −3 到 +3,所以那個高估是**臂間不對稱的**,
差額最高 +0.30 % —— 即整條決策邊界的約 71 %,而其**符號未知**(臂間對稱性為 `NOT_EVALUATED` 且
事後不可查證)。median 沒有對應項。

**理由 2 與估計量無關**:它對 median、max、clean-mean、trimmed mean 一視同仁。它否決的是
**「每個 seed 只有一個視窗」這個設計**,而不是某個統計量。即使污染明天完全消失,它依然成立。

**兩者不可互相取代。** 只有理由 2,`max` 仍可作為「反正都很吵,這是另一個視角」的 sensitivity;
只有理由 1,無法否決單視窗設計。**native 的 3/5 → 4/5 位移正是兩者都需要的實證**:理由 2 說明
為什麼什麼都不能下結論,理由 1 說明為什麼 `max` 看起來下的那個結論是估計量假象,而非第二種讀法。

**捨棄的方案:**

- **改用 peak 為主要端點** —— 駁回(上述三項)。
- **只對 medium 套用** —— 駁回。§10.4 的合併主張是 medium ∧ large 的 intersection-union;對其中一個
  shape 換估計量會讓連言的兩半變成不同 estimand。且**沒有必要**:max 在 large(5/5、3/5)與
  tiny(5/5、1/5)上完全不動。一條「除了它會跨過門檻的地方以外,到處都無作用」的規則,正是
  governance §4 所針對的那種鬆綁。
- **保留一列 uniform max sensitivity** —— **駁回(本場相對 §13.3 收緊)**。理由見 §14.3。

### 14.3 ⚠ §13.2 / §13.3 的 count-invariance 主張是**錯的**,且它正是 max 列唯一的可採性依據

§13.2 / §13.3 記載「median → max **不改變任何 shape、任何 campaign 的 directional count**」。
**此陳述為偽。** coordinator 由 `remeasure.{G,F}` 獨立重算全部四個 medium 資料集:

| 資料集 | median 正向 / 非退步 | max 正向 / 非退步 | |
|---|---|---|---|
| capped C1 | 2/5, 3/5 | 2/5, 3/5 | 不變 |
| capped C2 | 3/5, 3/5 | **2/5**, 3/5 | 對 F **不利** |
| native C1 | 3/5, **3/5** | 3/5, **4/5** | **跨過 ≥4/5,對 F 有利** |
| native C2 | 2/5, **3/5** | 2/5, **4/5** | **跨過 ≥4/5,對 F 有利** |

native 的非退步門檻 `e^{−η}` 由 **§12.3 預註冊**。所以 max 在四個資料集上無作用、在一個上對 F 不利、
在**兩個**上把一條預註冊的 ≥4/5 判準往受測臂方向跨過去。**「uniform 套用因此免費」這個可採性論證
不成立。** 一個在四處惰性、在兩處跨越門檻的統計量,不會因為「一致套用」而變得可採。

**跨越的機制必須一併記錄,因為它證實了理由 1:** max 並沒有「發現」F 非劣。它是把原本把中位數壓到
門檻下的向下污染剝掉,而那條門檻又比實測離散度緊 288 倍,於是幾乎什麼都過。這是
**極值統計量對上一條由中央統計量離散度導出的 margin** 所製造出來的通過,不是資料說的。

**因此的發表規則(比 §13.3 更嚴):** 任何 acceptance 或 sensitivity 表格中**都不得出現 `max` 列**,
任何 shape、任何 variant 皆然。`max` 只能出現在**量測缺陷的鑑識段落**中,作為**關於儀器**的證據,
且**必須**在同一段落內明載:「在 max-of-7 下,native-medium 的非退步分項在兩個 campaign 都讀作
4/5,跨過 §12.3 預註冊的 ≥4/5 門檻並偏向受測臂 —— **此位移正是 max 被駁回的理由,不是一項結果**。」
**靜默更正是不可接受的**:§13.2/§13.3 目前斷言其反面,若只是悄悄改掉而不說明真相中不方便的那半,
只會讓紀錄以另一種方式誤導。

**owner 的能力觀察應改以敘述方式報告**(這是該論證真正站得住的內容,且目前**報告不足**):
「medium 的 champion 曾被直接觀測到 11,977–15,067 GFLOP/s;低模態是儀器污染,不是 config 行為。」
—— 不附比值、不進 gate、不產生 tier。

### 14.4 修復路徑:`int32` 溢位,§13.8 的崩潰分支已滿足

5,136 warm-ups @ 釘死的 RBS 4096 於三個 seed 全數崩潰(`Insufficient rotating buffer size.`,
exit 134)。**這不是偶發,是決定性的算術溢位**,兩位 reviewer 各自獨立推導,coordinator 逐位元複驗:

client 於 `DataInitialization.cpp:3213` 以 `int32_t` 計算 `rotatingNum × rotatingSize`。
medium 的 `rotatingSize = 1,312,256 B`,5,136 warm-ups 給出 `rotatingNum = 3272`,
乘積 `4,293,701,632` 溢位為 **`−1,265,664`** —— 與 log 印出的數字**逐位元相符**。
溢位門檻:`rotatingNum ≥ 1637`,即 **`num-warmups ≥ 1638` 必崩**。
可用上限約 **1,637 次 ≈ 16.4–18.6 ms** 暖機,對照 **51 ms** 的拐點。

**結論:釘死的 estimand 下不存在任何「乾淨」的可達組態。** §13.8 的 falsification 條件
(「探測崩潰 → 在釘死的 estimand 下不存在丟棄重測的路徑」)**已滿足**;§13.7 item 2 記為**已結案**,
不再是 pending。修復需要改 client 程式(int32 → int64,或 per-size RBS),那是**新的 estimand**,
須走 successor,不能以 amendment 處理。

**這一點削弱而非強化「以統計量搶救資料」的主張。** 一個統計量之所以可採,前提是原則上存在一個
能證實或推翻它的量測。能驗證 peak-based 估計的乾淨模態校準在此**取得不到**,所以「搶救」等於安裝
一個**在其被套用的設定下不可證偽**的統計量。且 §13.2 的框架事實仍然成立:三個污染碰不到的分項
早已各為 3/5,所以搶救**換不到任何資訊**,只賠上可證偽性。

### 14.5 Acceptance criteria / falsification

- **跨視窗 A/A 實驗(§13.7 item 1)顯示跨視窗底線實質低於 `η_medium`** → 理由 2 被推翻,估計量問題
  在 successor 下重開。
- **client 改為 64-bit 後在 RBS 4096 下量得可證實的乾淨結果** → 理由 3 被推翻,同樣走 successor。
- 兩者皆**不得**以 amendment 處理:governance §4 在 threshold、formal measurement、comparability
  與 claim 任一項變動時即獨立觸發,與是否對受測臂有利無關。

### 14.6 必須更正的既有紀錄(本場新增)

- **§13.2 / §13.3 的 count-invariance 主張為偽**,須依 §14.3 更正並明載 native 位移。
- **§13.3 native 表的「正向」欄判準未標明** —— 初版用 `ratio > 1`。預註冊判準是 `> 1 + δ_s`
  (`δ_s = 0.004204159905590865`)。兩者在 native C1 相同(3/5),在 **native C2 不同(預註冊為 2/5)**。
  已於本次更正並加註判準。
- **`η_medium` 不適任的第二個獨立佐證:** native C2 seed 24001 的 `ratio = 1.004079`,以
  **0.0125 個百分點**之差落在 1.0042042 門檻下方。一條預註冊判準由 0.0125 pp 決定,這件事本身
  就說明該 margin 對它所裁量的量過緊(第一個佐證見 §13.4)。
- **第二個「7 次全污染」的臂**須入帳:capped seed 24004 arm F campaign 2(回復率 85.7–89.4 %,
  視參考基準而定),與已知的 seed 24005 arm F campaign 1(78.6 %)並列。
- **§13.9 須加入跨視窗底線**(0.5–2.8 × η_medium),並記載其僅建立在單一下午的視窗上。
- **ladder 的 idle-gap 趨勢(33 % → 52 %)為「未建立」** —— 經 over-dispersion 調整後 z ≈ 1.40。
  不得作為暖機說的支持證據引用。

### 14.7 殘餘不確定性

- 機制 `NOT_EVALUATED`。時脈說已被否證;暖機**相關性**存活,成因不明。
- 臂間對稱性 `NOT_EVALUATED`,且因逐代 CSV 未保留而事後不可查證。
- 各 config 的真實上限未知;任何 max 都只是**下界**。
- 跨視窗底線僅建立在**一個下午**的視窗上;任何 shape 都不存在跨日重複性資料。
- 兩個 same-model fresh threads 是 **process independence,不是 scientific replication**。
- 64-bit patch 是否真能在 RBS 4096 下給出乾淨的 51 ms 暖機:`NOT_EVALUATED`。它移除了已識別的
  上限,但無法解釋先前 32,100 warm-ups 那批 25/25 的 `hipModuleLoad rc=-6` 失敗(不同 signature)。

### 14.8 Reviewer 交鋒紀錄(供稽核)

- **雙方獨立得到相同結論,但論證不同,且事後證實互補**:A 提出 `max` 專屬的偏差項,B 提出與估計量
  無關的跨視窗底線。交互詰問後雙方都同意**兩者不互相涵蓋**。
- **A 撤回自己的建議 2**(原主張可發表 uniform max sensitivity 列)。撤回原因是 A 的 EVIDENCE F
  **漏檢 native addendum** —— 而 native 正是位移發生處。A 改為主張更嚴的規則並加上「必須揭露」義務。
- **B 撤回自己的 round-1 觀察**「peak 的失敗都落在 F 臂、因此對 H1 保守」。B 在 ladder 中找到
  **baseline 臂**的全失敗視窗(seed 24005 arm G,`s1_trace`,回復率 0.569),自承是從 n=2 過度推論。
- **B 接受 A 的兩項更正**:seed 24003 的 C1 側其實只有 3/7 乾淨,故「零污染」措辭不精確;且 2.3 %
  這個量級隨摘要統計量而變(clean-median 為 1.32 %),故改以 ladder 導出的 0.5–2.8 × η 為錨。
- **B 接受比自己三條件更嚴的發表規則**,並明言不是為了結束流程 —— B 自己就指出其條件 3 掛在一個
  `PENDING_HUMAN_DECISION` 的狀態上,一旦該狀態被回復,保護就會無聲失效。
- **coordinator 推翻了 reviewer 的計算兩次**:(i) A 與 B 起初都主張 count-invariance,B 隨後自行
  更正並被 coordinator 確認;(ii) native C2 正向計數,A 報 3/5(用 `ratio > 1`),由 coordinator 以
  script 自己記錄的 `F_over_G_gt_one_plus_delta_s` 判定為 **2/5**,A 於 final round 接受。
- **最終回應:雙方 AGREE,無保留異議。** B 另提一項非阻擋補充(0.0125 pp 佐證),已納入 §14.6。
