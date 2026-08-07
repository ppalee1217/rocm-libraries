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
pins_authority: RESCOPE-STAGE1-OUTCOME-20260807 + S14 design-discussion 2026-08-07 (two reviewers AGREE) + user pin decisions 2026-08-07
dependencies:
  - checkpoint_id: S11
    required_edge: S1_GUIDANCE_LOCKED
entry_criteria:
  - S1_GUIDANCE_LOCKED
criterion_refs:
  - S14_GUIDED_OUTCOME_POSITIVE
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
formal_report_path: reports/full-ga-baseline-vs-guided-outcome-report.md
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s14-guided-outcome-positive.json
tranche_final_report_path: reports/full-ga-baseline-vs-guided-outcome-report.md
terminal_report_integration: integrates_S11_compact_record_and_S14_terminal_evidence
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s14-full-ga-outcome-lock.json
cross_server_reproducibility: required
pre_seal_gate: label_blind_throughput_correctness_noise_preflight_required
consensus_status: approved_two_reviewer_agree
---

# S14 — Stage 1 full-GA baseline-vs-guided real-GPU outcome

導航：[active checkpoint index](README.md)｜[experiment plan §7](../ductile-origami-warmstart-experiment-plan.md#7-d6-actual-gen0-endpoint)｜authority: `RESCOPE-STAGE1-OUTCOME-20260807`

> **狀態：**本 design 依 user-approved `RESCOPE-STAGE1-OUTCOME-20260807` 建立,並經 2026-08-07 兩位獨立 `gpt-5.6-sol/xhigh` reviewer 的 design-discussion（§9）與 user pin 決定收斂。`design_status=approved`、`consensus_status=approved_two_reviewer_agree`。**執行前置硬 gate**：`pre_seal_gate` —— 在 effective lock seal 前,必須在**實際執行 server** 上完成 label-blind 的 throughput + correctness + noise preflight（並產出真實 wall-time 估計與 `delta_noise`）。本 design 尚未執行任何 evidence、未建 lock/report/edge。用語遵循 charter §8.6:本 checkpoint 是 **fixed-30-generation search-trajectory outcome** 研究,**不**宣稱 convergence 改善或 tuning speedup。

## 1. 白話目標

S14 回答 re-scoped Stage-1 的核心問題:**「Gen0 的權重 bias 是否真的影響 Ductile DSE 的最終結果？」**做法是把 actual Ductile 基因演算法跑**固定 30 世代**,分兩臂比較:

- **BASELINE(G)**：現行 GEKO guidance = 完整 `pi_nominal`（其中 `group_0` 帶 GEKO 權重,其餘 29 個 ungrouped free genes 為 uniform）。
- **GUIDED(F)**：G 之上,Formocast 只對「ungrouped、目前 unweighted 的 free genes」中 S11 manifest 明列者注入權重（不碰 `group_0`）。

兩臂各跑完 30 世代後,對每臂選出的 **champion kernel** 做**獨立真實 GPU 效能重測**,比較 F 是否在 champion real-GFLOPS 與 search-trajectory AUC 上方向性勝過 G。

## 2. Hypothesis 與 falsification

**S14-H1（directional）：**在 frozen problem set 上的 fixed-30-generation Ductile GA（P0-capped=64 變體）中,GUIDED(F)臂選出的 champion 其真實 GPU 效能,以及 search-trajectory AUC,**方向性勝過** BASELINE(G)臂;同時 correctness、validity 與 sampler realization 不失守。

註（reviewer 採納）：H1 是**單向**假設(F 優於 G)。一個可重現的**負** delta（F 穩定劣於 G）證明「權重有影響」但**不是** H1-positive,依 stop matrix 記為 `FT-HEURISTIC-SATURATION`/`FT-GEN0-MECHANISM`。

反證或 invalidating evidence：champion real-GFLOPS 或 trajectory AUC 未方向性勝出;proposal/candidate/weight/space hash 兩臂不一致或未各自重現其預期值;新增 correctness/validity failure;median/final real-quality 掉到 noise guardrail 以下;results 按 set iteration order join;看到 outcome 後更改任一 arm 定義、GA 參數或 metric。

## 3. Dependencies、entry 與 outgoing edge

- 唯一 entry：S11 完整 locked/verified/committed/post-audited 後的 `S1_GUIDANCE_LOCKED`。S14 消費 S11 交接的 frozen guidance（residual-gene 權重、canonical guidance hash、same-entropy shuffle bundle、noise/correctness evidence、seeds、sampler/mapping revisions）。
- S14 **不** gate 於 S12 `D5_PASS`（S12 FROZEN/DEFERRED）。真實效能改在 Ductile post-GA champion selection 上量測。
- Outgoing edge：`S14_GUIDED_OUTCOME_POSITIVE -> (S20 execution SUSPENDED)`。S20+ 目前 SUSPENDED,S14 positive 不自動解鎖。Negative/inconclusive 不追加 generations/seeds 救回。

### 3.1 Gate／tranche／closure governance
`risk_tier=R1`、`scientific_gate=S14`、`execution_tranche=T-S14-OUTCOME`、`closure_unit=CU-S14-OUTCOME`。Formal execution 前依 `b0561d2c92…` 完成 entry preflight,並 seal durable contract/effective lock。S14 positive 另 seal compact record;positive/negative/inconclusive 都由本 final report 整合 S11 compact record 與 S14 terminal evidence。

## 4. Maximum implementation 與 delivery boundary

允許：constructor `P0` 解析（**capped 至 64**,見 §6 pins）;fixed-30-generation GA 演化含 selection/crossover/mutation/survival;**per-generation 配對 proposal barrier**（見 §6）;BASELINE/GUIDED（及日後 optional S）formal proposal generation、canonical serialization 與 per-generation proposal lock;cross-arm/seed deduplicated benchmark union 與 multiplicity-aware join;post-GA champion 的獨立真實 GPU 重測;trajectory-AUC、champion real-GFLOPS delta、median guardrail、correctness、validity 與 diagnostics。

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
- **P0（母體）**：configured `pop_size=64` 且**初始母體 capped=64**（不讓 constructor 自動膨脹到 ~11,405）。此 cap 由 `RESCOPE-STAGE1-OUTCOME-20260807` + 本設計授權;claim 明列為 **「P0-capped Ductile variant」**,非未改動之原生 Ductile。runner 必須 fail-closed 驗證實際 P0=64。
- **世代**：`n_gen=30`、`period=0`（關閉 outcome-dependent early stop,使兩臂 budget 可比）;`tol=0.0008` 僅記錄為 inactive metadata。
- **seeds**：**3 對 formal seed**（G/F 同 seed 配對）;replay seeds 與 formal 分離。
- **arms**：正式跑 **G/F**;**Arm S 宣告為 optional-reserved**（可日後獨立補做,使用相同 seeds 並與 G/F champion 同時窗重測;現在宣告以避免 post-hoc;若不跑 S,`FT-ENTROPY-ONLY` 不適用且 claim 不含 physics-direction 歸因）;Arm U 省略。
- **品質 reducer**：`Q(x) = max_s [ GFLOPS_s(x) / R_s ]`,`R_s` 為 prelocked noise-anchor panel 的 per-size 參考（承襲 S11 sealed `max_s`,但 per-size 正規化以免原始尺度亂比）;三 size 皆需。
- **problem set**：3 個 size `(8,8,1,128)`、`(256,256,1,1024)`、`(2304,1024,1,214336)`,gfx942 non-StreamK,單一 dtype/layout（依 frozen size registry）。
- **`delta_noise`**：執行 server 上 `3 anchors × 3 sizes × 7 repeats`,`delta_noise = exp(P95(|log Q − median_r log Q|)) − 1`,anchors/公式/上限先封、scalar 於 formal label 前封（不由 arm results 導出）。
- **search-trajectory AUC**：`A = (1/U_floor) ∫_0^{U_floor} log Q(u) du`,`u` = post-Gen0 累積完成評估數,`Q(0)`=Gen0 best,逐世代右連續階梯,multiplicity-aware,無 within-batch 排序 credit。
- **`U_floor`**：`960` post-Gen0 完成評估/臂/seed（CAP=64 分支）。任一 formal run 未達即 `FT-EVALUATION-SUPPORT`,不得事後下修。
- **champion**：每臂/seed 取 max-`Q` 的候選,tie-break 用 canonical config hash 升序;**獨立重測 7×/size**,G/F 配對隨機序。
- **correctness**：每次 formal 評估與重測 `NumElementsToValidate=128`（預設 0 不足）。
- **per-generation 配對 barrier**：protocol lock 先於任何 formal label;之後每世代:產生 G/F batch → 鎖該世代 → 去重該世代 G/F union → benchmark → multiplicity-aware join → 兩臂同步前進;**不得跨世代 cache**（backend `useCache=False`）。
- **label firewall**：comparison lock 於**第一筆 BASELINE label 之前**封;prelock 跑的 baseline 只能算 pilot、封後重跑;counterbalanced 臂順序。
- **hash 判定**：只對不變基底（base YAML、space、candidate order、GEKO `group_0` 權重、operators、bench config）要求兩臂一致;各臂需重現自己預期的 treatment/proposal hash;F−G 權重差 = 恰為 residual bundle。
- **`n_jobs=1`**;same physical GPU UUID per G/F pair。

S14 能回答 single-development-cluster 的「free-gene 權重 bias 是否影響最終 DSE 結果（P0-capped 變體）」;**不能**回答 H10 persistence（S20）、held-out replication（S31）、speedup 或 convergence 泛化。

## 7. Acceptance binding 與 stop matrix

唯一 positive criterion `S14_GUIDED_OUTCOME_POSITIVE`（directional,3 對 seed 全數 joint 滿足,無 significance test）:

1. champion `Q_F*/Q_G* > 1 + delta_noise`,**3/3 seeds**;
2. search-trajectory AUC `A_F − A_G > log(1 + delta_noise)`,**3/3 seeds**;
3. final-population median 非劣 `median(Q_F)/median(Q_G) ≥ 1/(1+delta_noise)`,**3/3 seeds**;
4. proposal-set/candidate/weight/space hashes 依 §6.1 hash 判定通過;replay envelope 無 systematic anomaly;無新 validity/correctness failure;cross-server pins 已 seal 且 preflight 通過。

（若日後補跑 Arm S:另加「F 亦勝 S」方可歸因 physics-direction,否則 claim 限「F 勝 G」。）

| 狀況 | outcome／failure | downstream |
| --- | --- | --- |
| 全部 4 條、3/3 通過 | `S14_GUIDED_OUTCOME_POSITIVE` | S20（SUSPENDED,不自動解鎖）|
| Proposal/replay/order/hash mismatch | `FT-PLUMBING`；修復需 new lock/fresh proposals | 無 |
| Realization 正常但最終 quality/AUC 無方向性增益 | `FT-GEN0-MECHANISM` | 無 |
| F 不勝 G(GEKO) | `FT-HEURISTIC-SATURATION` | 無 |
| （若跑 S）F 不勝 same-entropy shuffle | `FT-ENTROPY-ONLY` | 無 |
| 任一 formal run 未達 `U_floor` | `FT-EVALUATION-SUPPORT` | 無 |
| 執行 server 可重現 correctness 失敗 | `FT-BLOCKED-CORRECTNESS` | 無 |
| Noise/support 不足 | `FT-INCONCLUSIVE` | 無 |
| 想用額外 generations/seeds 或看結果後改參數救回 | downgrade/plan change,停止 review | 無 |

## 8. Formal report 與 closeout

唯一 formal report：`reports/full-ga-baseline-vs-guided-outcome-report.md`,追溯 S11 authority 與 `RESCOPE-STAGE1-OUTCOME-20260807`,整合 S11 compact record 與 S14 machine decision。因 S20+ SUSPENDED,S14 為目前 Stage-1 terminal outcome report;claim boundary 限 **P0-capped 變體、single-cluster directional advantage of F over G**（physics-direction 僅在補跑 S 時)。

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
  - **P0**：reviewer 均建議 CAP 以趕 deadline（REAL=11,405 兩週內幾乎不可行）。**使用者選 CAP=64**;claim 限「P0-capped 變體」,並授權 constructor-cap。
  - **seed 數**：reviewer 一方 3/3、一方 5(4/5);**使用者選 3 seeds / 3-of-3 joint**（趕 deadline;判定較嚴但無容錯）。`U_floor=960`。
  - **Arm S**：**使用者選先只做 G/F、S 宣告 optional-reserved**（日後可獨立補、不重跑 G/F）。
- 未決/前置：seal 前必須通過 label-blind throughput + correctness + noise **preflight**（也產出真實 wall-time 估計與 `delta_noise`)。若 preflight 顯示 CAP=64 仍不可行,回 user decision。
- Reviewer A final：`AGREE`（conditional on 上述修正 + preflight before seal）
- Reviewer B final：`AGREE`（conditional on 上述修正 + preflight before seal）
