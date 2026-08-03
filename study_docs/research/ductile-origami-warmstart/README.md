# Ductile Factorized Guidance — Active Checkpoint Index

> **Active-state authority banner：**本研究目前是
> `post_empirical / s10r4_design_approved`。S00是durable positive，
> S10是durable `negative / S1_ENTRY_BLOCKED / edge=null`，兩者不變。User-authorized
> A32已在safe boundary取消S10R1：operational
> `cancelled / BLOCKED`、scientific `not_evaluated`、`edge=null`，沒有scientific
> report且不是`CHECKPOINT_COMPLETE`；generation 0／1只作diagnostic lineage並
> 禁止重用。A33另授權identity-only retirement；bulk artifacts不再保留。新的
> sibling S10R2已由fresh verifier technical `PASS`，scientific outcome為
> `inconclusive / FT-INCONCLUSIVE / edge=null`；本次closure commit與post-audit後
> projection為`CHECKPOINT_COMPLETE`。A33 retirement
> post-audit已通過；A34核准prospective calibration boundary，A35再將R2 repair
> round上限由3提高為6且不重置已消耗rounds；A36另將不影響workload、stopping、
> evidence integrity或scientific result的resource-accounting缺口定為non-blocking
> caveat，不要求resource-only rerun；A37 prospectively取消internal resource target
> 與cumulative ledger作blanket hard gate，改為record＋notify＋continue，只有
> material safety／availability／completion／evidence boundary才暫停。A38當時核准
> R3 sibling S10R3，S10R2保持immutable inconclusive/null；該historical
> `S1_ENTRY_GO`沒有形成。A44把所有prospective R0–R3 repair cap統一為6 rounds，
> 並把experiment-design user gate與非設計dual-agent預授權分開。A45以clean
> execution baseline與雙seal lifecycle對齊current `.agents` workflow；S10R3保持
> `not_evaluated / edge=null`、threads `9/9`，scientific plan不變。A46取消numeric
> repair stop cap；reviewer支持的plan-preserving修復可直接進行。A46.5 G3現已完成
> fresh 512-chunk schedule、`C_greedy=K=19`與兩次可重現required mapping failure；
> independent reproduction及fresh verification PASS，terminal closeout為
> `CHECKPOINT_COMPLETE / negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING /
> edge=null`。A47已由兩位fresh reviewers形成`AGREE`並由使用者核准exact-frame
> S10R4；它對S10R3完整sealed 114-config frame執行normal codegen census，不重開draws
> 或改寫S10R3。A47核准當時S10R4為`DESIGN_APPROVED / not_started / not_evaluated / edge=null`；
> 只有post-audited `S10R4:S1_ENTRY_GO_EXACT_FRAME`可啟動S11。A48核准的
> [binding-02](s10r4-binding-02-execution-recovery-authority.md)曾完成seal與
> `LOCKED_READY`，但第一個Census-A child留下partial後fail closed，現為
> `cancelled / BLOCKED / not_evaluated / edge=null / lock=superseded`。A50核准的
> [binding-03](s10r4-binding-03-census-backend-recovery-authority.md)則在prelock
> diagnostic發現新的workflow-boundary缺陷，現為
> `binding_status=superseded_prelock / execution_status=cancelled /
> checkpoint_state=BLOCKED / criterion_status=CHANGES_REQUIRED /
> scientific_outcome=not_evaluated / edge=null / lock_state=absent /
> lock_never_created=true`。兩者都沒有scientific formal outcome。A51曾核准
> [binding-04 dual-lineage recovery](s10r4-binding-04-resolver-effective-recovery-authority.md)：
> 它固定raw occurrence denominator，另將resolver-effective semantics綁成normal
> KernelWriter workflow實際消費的operational measurement boundary。其prelock source
> closure後來發現`MacroTile{ti}`的`ti`來自`ProblemType.Index{tensorIdx}`，不能只證明
> literal `tensorIdx`；因此binding-04現為
> `superseded_prelock / cancelled / BLOCKED / CHANGES_REQUIRED / not_evaluated /
> edge=null / lock=absent / lock_never_created=true`。Binding-05完整保留這個science，
> 但其ignored ledger在implementation前發生canonical hash-chain failure，因此同樣固定為
> `superseded_prelock / cancelled / BLOCKED / CHANGES_REQUIRED / not_evaluated /
> edge=null / lock=absent / lock_never_created=true`，且提供zero gate credit。Current
> user-approved authority是
> [binding-06 provenance recovery](s10r4-binding-06-provenance-recovery-authority.md)：
> 它在fresh clean worktree/root中以exact one relational rule與兩份獨立whole-subtree closure
> 關閉exact 89 dynamic accesses（68 direct＋21 `tP["mt"]` carrier consumers），要求
> terminal unresolved exact 0，再允許任何formal row。
> 目前`DESIGN_APPROVED / not_started / not_evaluated / edge=null`，binding-06 lock absent。
>
> **唯一 active 導航入口：**本 README。`legacy/` 內的 M00–M09 仍是 dead-protocol archive，不能提供 schema、hash、lock、registry、criterion、fixture、test或 PASS evidence；S00 positive只支持CPU-only evidence foundation。
>
> **S00 execution／closeout視圖：**`protocol/v1/README.md`只描述immutable
> execution-authority view（E）：baseline
> `60775f12843bee9f95cb0bef4e91de8bc4dc9dc3`＋exact 29 implementation
> blobs＋exact兩份Plan-B，三份authority projection使用baseline bytes。本頁則是
> post-PASS closeout-projection view（C）之一；不要在C直接呼叫historical outcome
> writers，它們必須在任何寫入前以`bound_hash_mismatch`拒絕。請依
> [S00 formal report](reports/staged/s00-foundation-verification-report.md)重建E並
> 執行green verification；該重建依賴baseline Git object與兩份exact ignored
> Plan-B，不保證standalone source-tarball portability。

## 1. Authority order

1. [Research charter](../surrogate-dse-plan.md)：scope、claim ladder、non-goals、failure taxonomy。
2. [Experiment plan](../ductile-origami-warmstart-experiment-plan.md)：公式、samples、seeds、thresholds、data floors、splits、time caps、checkpoint DAG與acceptance IDs。
3. 本頁索引的 checkpoint design：implementation handoff、maximum boundary、artifact/evidence binding。
4. Durable machine-readable frozen contract與checkpoint effective lock：在evidence前把
   committed authorities、criteria/matrix、resources、Plan-B、exact whitelists、
   inputs、fixtures與seeds綁成不可變執行實例。S10R3依A45先seal
   scientific/oracle contract，再於fresh label-blind implementation後seal exact
   effective execution lock；第二seal前`outcome_access=false`。
5. Compact positive gate record或terminal formal report：只記verified evidence、
   outcome、edge與closeout，不得反向修改前四層。

Execution governance另以commit
`b0561d2c9216a58a9d71b8e839c47efaa51f9c00`為mandatory floor；它規範risk tier、
tranche／closure、cumulative budgets與state projection，但不能靜默改上列scientific
hypothesis、criterion、edge或timebox。

任何下層衝突都由較高層決定。`milestone`／`step` 只有在指向本頁 checkpoint ID 時才是 alias，不會形成另一套 lifecycle。

## 2. Active checkpoint index

| ID | Responsibility | Design | Execution | Checkpoint | Scientific outcome | Lock | Formal report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S00 | Evidence／lineage／checkpoint-resume foundation | `approved` | `completed` | `CHECKPOINT_COMPLETE` | `positive` | `effective (successor-001)` | [report](reports/staged/s00-foundation-verification-report.md) |
| S10 | Stage 1 access／artifact／mapping／noise gate | `approved` | `completed` | `CHECKPOINT_COMPLETE` | `negative` | `effective (successor-003)` | [report](reports/staged/s10-stage1-entry-gate-report.md) |
| S10R1 | Cancelled nominal-boundary recovery diagnostics | `approved` | `cancelled` | `BLOCKED` | `not_evaluated` | `superseded` | none (A32 operational record only) |
| S10R2 | Stage 1 support-aware entry recovery | `approved` | `completed` | `CHECKPOINT_COMPLETE` | `inconclusive` | `effective` | [report](reports/staged/s10r2-stage1-support-aware-entry-report.md) |
| S10R3 | Stage 1 bounded-cover entry recovery | `approved` | `completed` | `CHECKPOINT_COMPLETE` | `negative` | `effective (S10R3-A46.5-G3)` | [report](reports/staged/s10r3-stage1-bounded-cover-entry-report.md) |
| S10R4 | Stage 1 relational-selector exact-frame operational entry recovery | `approved` | `not_started` | `DESIGN_APPROVED` | `not_evaluated` | `binding-01/02/03/04/05 superseded; binding-06 absent` | `reports/staged/s10r4-stage1-relational-selector-entry-report.md` |
| S11 | Stage 1 model-only factorization／guidance lock | `approved` | `gated` | `DESIGN_APPROVED` | `not_activated` | `absent` | `reports/staged/s11-stage1-model-only-factorization-report.md` |
| S12 | Stage 1 real-score／ranking／oracle audit | `approved` | `gated` | `DESIGN_APPROVED` | `not_evaluated` | `absent` | `reports/staged/s12-stage1-real-score-audit-report.md` |
| S13 | Stage 1 actual Gen0 mechanism | `approved` | `gated` | `DESIGN_APPROVED` | `not_evaluated` | `absent` | `reports/gen0-factorization-mvp-report.md` |
| S20 | Stage 2 fixed H10 persistence | `approved` | `gated` | `DESIGN_APPROVED` | `not_evaluated` | `absent` | `reports/short-horizon-persistence-report.md` |
| S30 | Stage 3 held-out registry／procedure freeze | `approved` | `gated` | `DESIGN_APPROVED` | `not_evaluated` | `absent` | `reports/staged/s30-heldout-registry-freeze-report.md` |
| S31 | Stage 3 two-cluster bounded replication | `approved` | `gated` | `DESIGN_APPROVED` | `not_evaluated` | `absent` | `reports/bounded-regime-replication-report.md` |
| S40 | Stage 4 trigger／data-sufficiency gate | `approved` | `gated` | `DESIGN_APPROVED` | `not_evaluated` | `absent` | `reports/staged/s40-stage4-activation-report.md` |
| S41 | Stage 4 learned residual analysis | `approved` | `gated` | `DESIGN_APPROVED` | `not_evaluated` | `absent` | `reports/learned-residual-surrogate-report.md` |

Designs：

- [S00 — Evidence contract、lineage 與 observability](s00-evidence-contract-lineage-observability-design.md)
- [S10 — Stage 1 entry access／mapping gate](s10-stage1-entry-access-mapping-gate-design.md)
- [S10R1 — Cancelled recovery diagnostic record](s10r1-stage1-valid-support-entry-recovery-design.md)
- [S10R2 — Stage 1 support-aware entry recovery](s10r2-stage1-support-aware-entry-recovery-design.md)
- [S10R3 — Stage 1 bounded-cover entry recovery](s10r3-stage1-bounded-cover-entry-recovery-design.md)
- [S10R4 — Stage 1 exact-frame operational entry recovery](s10r4-stage1-exact-frame-operational-entry-design.md)
- [S10R4 binding-02 — Execution recovery authority](s10r4-binding-02-execution-recovery-authority.md)
- [S10R4 binding-03 — Census backend recovery authority](s10r4-binding-03-census-backend-recovery-authority.md)
- [S10R4 binding-04 — Resolver-effective recovery authority](s10r4-binding-04-resolver-effective-recovery-authority.md)
- [S10R4 binding-04 — Resolver-effective operational entry design](s10r4-stage1-resolver-effective-operational-entry-design.md)
- [S10R4 binding-05 — Relational-selector recovery authority](s10r4-binding-05-relational-selector-recovery-authority.md)
- [S10R4 binding-05 — Relational-selector operational entry design](s10r4-stage1-relational-selector-operational-entry-design.md)
- [S10R4 binding-06 — Provenance-recovery authority](s10r4-binding-06-provenance-recovery-authority.md)
- [S10R4 binding-06 — Clean successor design](s10r4-stage1-relational-selector-binding-06-clean-successor-design.md)
- [S11 — Stage 1 model-only factorization](s11-stage1-model-only-factorization-design.md)
- [S12 — Stage 1 real-score audit](s12-stage1-real-score-ranking-oracle-audit-design.md)
- [S13 — Stage 1 actual Gen0](s13-stage1-actual-gen0-mechanism-design.md)
- [S20 — Stage 2 H10 persistence](s20-stage2-h10-persistence-design.md)
- [S30 — Stage 3 registry freeze](s30-stage3-heldout-registry-freeze-design.md)
- [S31 — Stage 3 bounded replication](s31-stage3-bounded-replication-design.md)
- [S40 — Stage 4 activation gate](s40-stage4-surrogate-activation-gate-design.md)
- [S41 — Stage 4 learned residual](s41-stage4-learned-residual-analysis-design.md)

## 3. Strict dependency DAG

```mermaid
flowchart TD
  s00["S00 Evidence foundation"]
  s10["S10 Stage 1 entry"]
  s10r1["S10R1 Cancelled diagnostics"]
  s10r2["S10R2 Support-aware entry"]
  s10r3["S10R3 Bounded-cover entry"]
  s10r4["S10R4 Exact-frame operational entry"]
  s11["S11 Model-only factorization"]
  s12["S12 Real-score audit"]
  s13["S13 Actual Gen0"]
  s20["S20 H10 persistence"]
  s30["S30 Registry freeze"]
  s31["S31 Bounded replication"]
  s40["S40 Activation gate"]
  s41["S41 Learned residual"]

  s00 -->|"S00_EVIDENCE_READY"| s10
  s00 -. "administrative readiness" .-> s10r2
  s10 -. "terminal provenance only; no scientific edge" .-> s10r2
  s10r1 -. "A32 status only; evidence reuse forbidden" .-> s10r2
  s10r2 -. "terminal inconclusive provenance; evidence reuse forbidden" .-> s10r3
  s10r3 -. "terminal negative provenance + sealed frame only" .-> s10r4
  s10r4 -->|"S1_ENTRY_GO_EXACT_FRAME"| s11
  s11 -->|"S1_GUIDANCE_LOCKED"| s12
  s12 -->|"D5_PASS"| s13
  s13 -->|"D6_MECHANISM_POSITIVE"| s20
  s20 -->|"S2_DIRECTIONAL_PERSISTENCE_POSITIVE"| s30
  s30 -->|"S3_REGISTRY_PROCEDURE_LOCKED"| s31
  s12 -.->|"predictor-specific failure + oracle positive"| s40
  s31 -.->|"predictor heterogeneity + oracle positive"| s40
  s40 -->|"S4_ACTIVATE"| s41
```

- S00的post-audited positive closeout已驗證`S00_EVIDENCE_READY -> S10`。S10已完成
  actual-guidance／live-unreserved H4／mapping boundary，並以完整可重現的
  `FT-BLOCKED-MAPPING` negative branch形成`S1_ENTRY_BLOCKED`。沒有outgoing edge；
  Direct evidence、successor lifecycle與claim boundary見
  [S10 formal report](reports/staged/s10-stage1-entry-gate-report.md)；早期
  [blocker memo](reports/gen0-factorization-blocker-memo.md)只保留為historical
  recovery evidence。
- R12曾核准S10R1；A32後續在quiescent safe boundary取消該execution。
  [S10R1 record](s10r1-stage1-valid-support-entry-recovery-design.md)固定為
  `cancelled / BLOCKED / not_evaluated / edge=null`，不建立report或completion；
  stochastic non-discovery不是scientific inconclusive或absence proof。A33只把
  physical artifacts改為identity-only retention；tombstone與
  [retirement manifest](retirements/s10r1-diagnostic-retirement.json)保留lineage。
- 新[S10R2 design](s10r2-stage1-support-aware-entry-recovery-design.md)是sibling，不是
  S10R1 successor。S00 readiness、S10 terminal provenance與A32 status只作
  administrative prerequisites；虛線不是scientific edge，且S10R1 evidence reuse
  forbidden。S10R2已closeout為inconclusive/null。A38新增
  [S10R3](s10r3-stage1-bounded-cover-entry-recovery-design.md)；S10R2對它只提供
  immutable terminal provenance，不提供formal evidence。S10R3已closeout為
  negative/null。A47新增[S10R4](s10r4-stage1-exact-frame-operational-entry-design.md)，
  只窄重用S10R3完整sealed raw frame，不重用其selection/mapping/outcome。A51進一步
  以fresh binding-04固定`F_valid(raw) -> F_effective -> F_codegen`的dual-lineage
  measurement science，但B04 execution已immutable prelock superseded且不能產生
  qualified evidence。Binding-05亦因preimplementation provenance-chain failure
  immutable superseded。Current binding-06 clean successor保留該science，並是
  S10R4唯一可產生新的qualified `S1_ENTRY_GO_EXACT_FRAME` evidence之來源。
- `S1_ENTRY_DEGRADED_PROXY`、two-size mode、H5 pilot、single-cluster pilot或任何縮減不會自動形成 outgoing edge；必須先停在 `blocked-awaiting-user-decision`。
- S12／S31 只有 parent 明列的 predictor-specific、oracle-positive evidence可送入 S40。
- S40 沒有合法 trigger時不執行，由上游 report記 `not_activated`；不替 S40 建假 report或commit。

## 4. 分離的狀態詞彙

`design_status` 只描述設計：`draft | approved | superseded`。

`execution_status` 只描述執行：`not_started | gated | ready | running | blocked | completed | cancelled`。

`checkpoint_state` 描述 orchestration／closeout：`DESIGN_APPROVED | LOCKED_READY | RUNNING | VERIFIED_PENDING_CLOSEOUT | CHECKPOINT_COMPLETE | BLOCKED`。

`scientific_outcome` 只描述科學判讀：`not_evaluated | positive | negative | inconclusive | blocked | not_activated | skipped_by_gate`。

`lock_state` 只描述 effective lock：`absent | effective | superseded`。

這些欄位不可互相代用。Technical `PASS` 只會進入 `VERIFIED_PENDING_CLOSEOUT`；只有 formal report、parent hunk、`CLOSEOUT_ACK`、isolated commit與post-commit audit全過，才是 `CHECKPOINT_COMPLETE`。

`scientific_gate`是不能合併或繞過的outcome／claim／authority edge；
`execution_tranche`可讓相容adjacent gates共享Main planning context、environment、
run root與repair ledger；每個scientific gate仍有自己的Plan-B、Plan-A、fresh
implementer與fresh verifier。`closure_unit`可共享terminal
report/update/staged audit/commit，但
不能改gate order或把outcomes混成一個。`live_run_state`保存working-tree／partial
進度；`committed_projection_state`只在closure commit與post-commit audit後更新。

## 5. Governance tranches與future lifecycle

| Execution tranche | Risk tiers | Scientific gates | Closure unit |
| --- | --- | --- | --- |
| `T-S10R2` | S10R2=`R2` | S10R2 | `CU-S10R2` standalone |
| `T-S10R3` | S10R3=`R3` | S10R3 | `CU-S10R3` standalone |
| `T-S10R4-B06` | S10R4 binding-06=`R3`；binding-01/02/03/04/05 superseded non-scientific history | S10R4 | `CU-S10R4` standalone |
| `T-S1-MECHANISM` | S11/S12=`R2`, S13=`R1` | S11 → S12 → S13 | `CU-S1-MECHANISM` |
| `T-S20` | S20=`R1` | S20 | `CU-S20` standalone |
| `T-S3-REPLICATION` | S30=`R2`, S31=`R1` | S30 → S31 | `CU-S3-REPLICATION` |
| `T-S4-LEARNED-RESIDUAL` | S40=`R2`, S41=`R1` | S40 → S41 | `CU-S4-LEARNED-RESIDUAL` |

每個tranche依序處理dependency-ready scientific gates：

1. 讀取 committed repository rule、skill、charter、parent plan與checkpoint design revisions。
2. 將 design 的 maximum boundary縮成 exact path/symbol implementation whitelist與delivery whitelist。
3. 在任何outcome evidence前建立durable machine-readable frozen contract、驗證
   human/machine parity並seal effective lock。
4. 依`10b7d10ca7`治理floor鎖risk tier與thread hard cap；repair cycle依A46只作
   append-only provenance。Resource planning依A37保留known usage及measurement
   boundary，跨generation、successor、replacement、new root不刪除／補造，但不單獨
   debit successor entry。
5. Main依序建立goal/oracle Plan-B與decision-complete Plan-A；fresh implementer與
   fresh verifier依visibility boundary、risk tier與frozen contract執行。
6. `CHANGES_REQUIRED`只修 active checkpoint並重驗；consequential design issue先走 `design-discussion`。
7. Technical `PASS`只進入`VERIFIED_PENDING_CLOSEOUT`。
8. Internal positive gate只seal其design指定的compact durable gate record，依verified
   frozen edge在同tranche繼續；它不刪除scientific gate，也不提前把closure unit標
   `COMPLETE`。
9. Internal negative／inconclusive立即產生該gate planned terminal report並停止；
   final gate report整合所有先前compact records。
10. Terminal staged audit、`CLOSEOUT_ACK`、exact-path isolated commit與post-commit
    audit全過後，才更新`committed_projection_state`與closure unit。

Verified projection只可更新terminal record直接解析的rows／edges與事實性banner；
不得預寫下游結果或修改criteria。Durable operational`BLOCKED`不是scientific
completion；`skipped_by_gate`／`not_activated`不建立假report。

## 6. Report、blocker與skip policy

- 每份 active design只有一個 formal report path。
- S10的`reports/gen0-factorization-blocker-memo.md`仍是唯一scientific-entry
  blocker memo，只用於該checkpoint的hard access／artifact／mapping blocker。
- S10R3另有唯一non-scientific operational lifecycle packet
  `protocol/v1/evidence/s10r3-operational-blocker.json`；它只依A45/A37 policy保存
  durable `BLOCKED`／resume，不是formal report或scientific completion。
- S10R1依A32取消，沒有scientific report、blocker memo或completion；舊planned report
  path不得建立。
- S10R2唯一formal report是
  `reports/staged/s10r2-stage1-support-aware-entry-report.md`，且不覆寫S10 report。
- S10R3唯一formal report是
  [S10R3 Stage 1 bounded-cover entry report](reports/staged/s10r3-stage1-bounded-cover-entry-report.md)。
  它記錄sealed G3 formal execution的
  `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`，不建立positive edge。
- S10R4 positive、negative或inconclusive的唯一formal report是
  `reports/staged/s10r4-stage1-relational-selector-entry-report.md`；在正式outcome前不得建立
  placeholder。Operational blocker只可寫
  `protocol/v1/evidence/s10r4-operational-blocker.json`，不是scientific completion。
- S40 data insufficiency是科學 negative，寫入 S40 formal report；不使用 data-insufficiency blocker memo。
- Outcome evidence已開始後，即使中途失敗，也不得退回 blocker memo來避開 formal negative／inconclusive report。
- S11／S12／S30／S40 internal positive使用各design指定compact gate record；若
  internal terminal negative／inconclusive，使用各自planned report；S13／S31／S41
  final report整合prior records。
- 現在不建立任何空白 report、placeholder lock、假 hash或compatibility stub。

### 6.1 2026-07-28 A32／S10R2 authority amendment

- Append-only S10R1 governance chain的user-authorized A32 event是live basis；本次不
  修改該chain或任何`agent_run`內容。
- A32在quiescent safe boundary取消S10R1。Generation 0已atomic retire／seal；
  generation 1未建立effective L0、selection、mapping、GPU、noise、decision或formal
  outcome，且沒有相關writer／flock。
- S10R1固定為`cancelled / BLOCKED / not_evaluated / edge=null`，沒有scientific
  report、completion或reuse authority。
- 新sibling S10R2是R2 standalone tranche／closure；S11 dependency重指唯一
  `S10R2:S1_ENTRY_GO`。
- S11–S41 scientific gates、edges、criteria與numerical timeboxes完整保留；execution
  tranches新增tiered governance與cumulative resource accounting。
- 本次只修改列名的documentation／authority files，不建立protocol code／tests、
  report、commit或push。Working-tree projection是`live_run_state`；future exact-path
  authority commit與post-audit前，`committed_projection_state`仍以
  `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`為baseline。

### 6.2 2026-07-28 A33 S10R1 artifact retirement

- 兩位fresh `gpt-5.6-sol/xhigh` reviewers經獨立首輪、一輪cross-examination與同一
  final candidate後均`AGREE`：S10R1約34 GB ignored tree與19個untracked old-code
  paths沒有合法S10R2／S11 consumer，應由compact identity tombstone取代。
- 第一階段先commit
  [retirement manifest](retirements/s10r1-diagnostic-retirement.json)的
  `authorized_pending_cleanup`與本authority；第二階段只按exact allowlist清理並將
  manifest更新為`retired_post_audited`。不使用broad cleanup，也不碰S00／S10、
  actual YAML、source objects、S10R2+ authority或unrelated worktree changes。
- Cleanup不改S10R1 state／outcome／edge，也不reset歷史resource accounting。
  S10R2在新的resource decision明列carry-over／reset／cap前保持operational
  `BLOCKED / not_evaluated / edge=null`。
- 後續strict順序是：
  `resource relock -> S10R2 -> S11 -> S12 -> S13 -> S20 -> S30 -> S31`；
  S40／S41仍只在既定trigger與data gate成立時啟動。

### 6.3 2026-07-28 A34 prospective resource boundary

- Fresh reviewers`/root/s10r2_next_plan_a`與`/root/s10r2_next_plan_b`以相同
  `gpt-5.6-sol / xhigh` evidence完成獨立首輪、一輪cross-examination與同一final
  candidate，兩方均`AGREE`。
- Historical cutoff固定為`d66edf7ac81cb76825b988e1ea9a65264dfeb0f6`；
  3151 chunks、threads`>=10`、repairs`>=11`與其餘resource `UNKNOWN`全部保留。
  A33釋放空間不是historical reset。
- Authority commit post-audit後，`T-S10R2`取得prospective 5 new threads／3 new
  repairs；`T-S1-MECHANISM`先reserve同樣5/3，只有S10R2 GO後activate，S11→S13內
  不再reset，且S13仍受R1最多2 repairs。這是A34 historical boundary；prospective
  repair caps後由A44統一supersede為6。
- S10R2→S13共享新的prospective 7 hands-on days、1.4 pre-empirical days與5 GiB
  transient ceiling。先做outcome-blind calibration；具單位wall／CPU／GPU caps、
  confirmed GPU allocation、buffer、contract parity與effective lock全數成立後才
  `LOCKED_READY`。
- Numeric relock前S10R2仍是`BLOCKED / not_evaluated / edge=null`。本authority不改
  workload、criteria、outcome matrix、claim或DAG，也不授權formal evidence、push、
  dependency install、container lifecycle mutation或downgrade。

### 6.4 2026-07-29 A36 resource-accounting materiality

- Resource telemetry預設是operational safety／planning control，不是scientific
  outcome criterion。只有direct cap-exceed／safety evidence、label-dependent
  stopping／selection、required workload不完整或scientific evidence不可驗證時才
  blocking。
- S10R2 fixed schedule與append-only evidence完整，headline
  `inconclusive / FT-INCONCLUSIVE`已由fresh independent process重現；沒有early
  stop、schedule drift、label-driven selection或direct cap-exceed evidence。
  Validator-child以外的wall／CPU缺口因此依A36列non-blocking caveat，不要求只為
  資源記帳重跑。
- 既有contract、lock、terminal ledger、support classification與decision保持
  immutable；fresh verifier需依A36重新出具technical verdict，formal report需揭露
  caveat與measurement boundary。
- A36不創造scientific edge。S10R2仍為
  `inconclusive / FT-INCONCLUSIVE / edge=null`，不能啟動S11；後續正式研究需新的
  entry recovery authority。

### 6.5 2026-07-29 A37 prospective resource-progress priority

- 使用者明確要求resource ledger若不影響整體實驗，就不要過度在意並以完整研究進度
  為優先。Fresh reviewers`/root/resource_rule_review_a`與
  `/root/resource_rule_review_b`以相同`gpt-5.6-sol / xhigh`及repo evidence完成
  獨立立場、一輪cross-examination與一輪final；雙方均`AGREE`。
- Resource usage預設是operational planning metadata，不是scientific estimand、
  acceptance criterion或successor-entry debit。Known usage及parent／child／inclusive
  boundary以best effort保留；`UNKNOWN`不補造、不寫成0。
- Missing telemetry、`>2x` projection、internal day／wall／CPU／GPU／storage／
  throughput／pre-empirical target crossing與historical cumulative consumption只需
  record＋notify。Long-running work開始前通知，但通知不是approval gate；完整frozen
  workload繼續。
- 只有direct或materially indicative evidence連到unsafe continuation、external／
  platform／allocation限制、實際資源不足、完整workload／verification／closure／
  artifact preservation無法完成、optional／label-dependent stopping、workload／
  claim change、evidence不可驗證，或labels前明確凍結的scientific resource boundary
  時，才safe-boundary pause。Bare `UNKNOWN`、internal target或cumulative total不是
  material evidence。
- A37 prospectively supersedes internal resource planning target作blanket hard pause及
  cumulative successor debit的舊文字；scientific sample／execution與thread caps、
  downgrade／evidence／claim gates不變，repair count依A46只作provenance。Future
  machine contract必須採相同語意。
- S10R2 A36、contract、lock、ledger、artifacts、formal report及
  `inconclusive / FT-INCONCLUSIVE / edge=null`完全immutable；不做resource-only
  rerun，也不因此啟動S11。

### 6.6 2026-07-29 A38 S10R3 bounded-cover entry

- S10R2以frozen exact-ten selector觀察到90個mandatory atoms、greedy cover 18，
  因而正確closeout為`inconclusive / FT-INCONCLUSIVE / edge=null`。A38不重開或
  重標它；舊18只作design diagnostic。
- Fresh reviewers`/root/s1_recovery_design_a`與`/root/s1_recovery_design_b`完成兩輪
  cross-examination及一輪evidence-backed final。使用者以「全部核准」核准共同的
  bounded-K scientific package、三項execution-authority解析、五路徑authority
  commit與後續`implement-verify-loop`；不授權push。
- 新S10R3固定fresh registry、disjoint seeds與append-only ledger。S10R1 artifacts及
  S10R2 rows／support／targets／cover／seeds／mapping／GPU／noise／decision全部禁止
  作formal evidence。
- Discovery仍是global `32×512`加最多15個conditional targets各`32×512`，
  total max `512 chunks / 262,144 draws`；無early stop、extension或seed retry。
- Mandatory set仍是
  `prelocked_candidate_atoms ∩ supported_witnessed`。Selector固定：

  ```text
  C_greedy = deterministic_greedy_set_cover_v2_bounded_k20的full-cover cardinality
  K        = max(10, C_greedy)
  K_max    = 20
  ```

  `C_greedy`不稱minimum。Fresh witnesses少於10或`C_greedy>20`即
  inconclusive/null，不得labels後改solver、draw、seed或cap。
- Mapping A/B各exact `3K` rows，最多60 rows/pass；anchors為sorted hashes的
  `{0,floor((K-1)/2),K-1}`。Correctness仍9 cells、noise仍63 cells，S11–S13
  scientific workload、threshold、claim與internal edges不變。
- R3角色配置為two planners、one adversarial auditor、Main implementation與one
  fresh verifier；連同兩位design reviewers為`6/6` threads，沒有replacement
  headroom。A44後repair最多6 rounds，rounds 1–3完整carry over。
- `12669 wall-s / 65285 CPU-s / 2901 GPU-s / 2 GiB`只作A37 planning estimates。
  GPU／ROCm command只在existing `perlee`；每phase直接選目前free eligible gfx942，
  不需reservation或exclusivity，但必須鎖定identity、foreign-PID rejection、
  interruption與append-only resume。
- 只有post-audited `S10R3:S1_ENTRY_GO`啟動S11；其他outcome都保持edge null。

### 6.7 2026-07-30 A44 universal six-round repair與goal persistence

- 所有prospective R0–R3 repair cap都是6 rounds；已消耗rounds不重置，第7輪仍需
  新human authority。S10R3因此由`3/3`改為`3/6`。
- Experiment-design ambiguity仍由兩個獨立agents完成bounded cross-examination，
  並將unified recommendation或dissent交使用者決定後才恢復affected path。
- 非設計阻塞、多個contract-preserving repairs或同一finding兩輪無material progress，
  可由兩個獨立agents裁決；共同non-destructive、contract/authority-preserving
  結論已預授權直接執行。沒有thread headroom時resume既有獨立non-implementer roles。
- 普通`CHANGES_REQUIRED`、可修復test/process failure與nonmaterial resource-accounting
  variance不再提前terminalize可完成的goal。本authority不改scientific criteria、
  schedule、outcome／edge、claim，也不授權push、downgrade、destructive operation、
  dependency install或container mutation。

### 6.8 2026-07-30 A45 S10R3 clean restart與雙seal alignment

- 使用者要求刪除全部未提交S10R3 implementation、tests、manifests、contract draft、
  cache與舊run artifacts，只保留committed scientific design／parent authority，再依
  current `.agents` workflow從clean execution baseline重啟。Cleanup時沒有effective
  lock、formal evidence、outcome、report或edge；S10R3仍是
  `not_evaluated / edge=null`。
- Fresh reviewers`/root/s10r3_restart_design_a`與
  `/root/s10r3_restart_design_b`完成一輪cross-examination及一輪evidence-backed
  final，兩方都`AGREE`：以同一scientific contract的Phase 1 seal加既有
  effective-lock path的Phase 2 binding解除sequencing cycle，完全不改scientific
  plan。
- Phase 1 contract凍結完整scientific/oracle projection、三個exact write boundaries、
  role visibility、`4/6` repair、`7/9` threads、final-binding schema及prelocked
  invalidation matrix；implementation binding保持fail-closed
  `required_pending`，`outcome_access=false`。Current workflow bytes只綁content
  identity與honest Git state，不stage。
- Execution-artifact boundary不遞迴授權整個run root：control-plane逐path列出，
  artifact-only子目錄才可用明確descendant semantics，且不得成為delivery。Phase 1
  同時固定Phase 2 lock的完整property／type／cardinality／null／unknown-field
  rejection、path-mode-hash record、state／audit與canonical self-hash schema。
- Phase 1 exact-path local commit與post-audit後，Main先freeze Plan-B，再建立Plan-A；
  Main不實作。Fresh implementer只讀Plan-A及必要frozen constraints，建立fresh
  label-blind implementation、tests、build、registry與fixture。
- Phase 2 existing effective lock綁定Phase 1、Plan hashes、所有pre-label source／test／
  schema／adapter／native binary／toolchain／argv／registry／fixture identities，
  並證明outcome artifacts absent。Existing auditor pass、lock exact-path local commit
  與post-seal audit全過後才是`LOCKED_READY`，在此之前不得執行formal evidence。
- Bound-byte repair必須建立append-only successor lock；labels後依prelocked
  invalidation matrix從最早受影響phase重跑，無證明時full rerun。Source／seed／
  registry／ledger／discovery semantics改變時從first draw重跑，不得依outcome挑suffix。
- Cleanup不重置lineage。歷史threads `5`加兩位reviewers為`7/9`，僅保留fresh
  implementer與fresh verifier；repair為`4/6`。Deleted S10R3 bytes／verdicts／plans與
  S10R1／S10R2 empirical evidence全部禁止重用。
- Phase 1首次audit後以cycle 5補齊machine-contract boundary/schema/blocker policy；
  fresh re-audit關閉artifact boundary，但反例仍要求補強audit cross-field、fixed
  source/projection digest、formal-scope absence與resume lineage。Cycle 5以
  `CHANGES_REQUIRED`完成；最後cycle 6 fresh re-audit通過時seal為`6/6`，scientific
  projection不變。
- 使用者澄清，只有實驗結果導致必須更動原實驗計畫並選擇新scientific方向時才需要
  中斷決定；同一commit／feature內、pre-evidence且plan-preserving的implementation／
  verification／lifecycle alignment與non-destructive、contract-preserving blocker
  均預授權直接完成。
- A45不改hypothesis、search space、draw／seed／cell schedule、selector／`K_max`、
  mapping、correctness／noise threshold、outcome matrix、claim、report或唯一positive
  edge，也不授權push、downgrade、dependency install或額外container mutation。
- S10R3唯一operational blocker packet為
  `protocol/v1/evidence/s10r3-operational-blocker.json`，只在A37 material condition
  於safe boundary成立時建立。它是可恢復的durable lifecycle state，不是scientific
  report／completion／edge；Main以append-only events保存`blocked`／`resumed`，
  blocked與resume都使用contract預鎖的exact parent projection與isolated commit policy。

### 6.9 2026-07-30 A46 reviewer-governed uncapped repair

- 所有R0–R3 repair cycle仍append-only記錄finding、修復、驗證與結果，但沒有numeric
  maximum；count只作provenance，不是stop、approval、success或completion gate。
- Responsible verifier／auditor提出唯一non-destructive、contract／authority-
  preserving修復時可直接進行。有多個consequential choices、authority
  classification歧義或同一finding兩輪無material progress時，由兩個獨立operational
  reviewers交互檢查；共同結論不需再次向使用者取得核准。
- 只有實驗結果迫使原實驗計畫的measurement、claim、scientific authority或方向改變
  才回到user decision。Scientific sample／draw／seed／cell／repetition、thread、
  downgrade、evidence、safety、external／destructive／container與push gates不變。
- S10R3 cycles 1–6保留。`S10R3-P2-AUD-001`為cycle 7，唯一修復是threshold `0.0`
  native queue oracle／fixture parity及受影響binding；formal evidence尚未開始，
  state保持`not_evaluated / edge=null`。Durable workflow baseline為
  `10b7d10ca7e197f7d93e1afd821805d4a65b1684`。

### 6.10 2026-07-30 A46.1 uncapped plan-revision lifecycle

- Fresh auditor在Plan-A Revision 6確認effective-lock schema的`maximum: 6`會把plan
  revision變相當成repair stop cap。
- A46.1移除該numeric maximum，但保留`revision >= 1`、current plan exact
  path/hash/size/freeze、append-only predecessor與fresh parity checks。
- Future lock的`repair_rounds_used`必須等於建立當下完整repair provenance；schema
  floor `>=9`不是live count或maximum。
- Scientific/oracle projection保持不變；formal evidence仍未啟動，outcome維持
  `not_evaluated / edge=null`。

### 6.11 2026-07-30 A46.2 experiment-scoped external workspace drift

- Workspace audit改為只檢查exact current-workflow writes、index／commit paths與
  experiment-relevant protected state；unrelated external paths不需全域byte equality。
- 只有path完全位於S10R3 implementation／execution／delivery／authority／source／
  input／evidence／lock／report／run boundaries之外、未被current workflow觸碰、
  未進index／commit、不影響reproducibility或claim，且不需對該path做任何mutation，
  才可記為`external_unrelated_drift`並notification後繼續。
- Original baseline維持immutable historical observation；successor observation記錄
  prior/current state、`UNKNOWN_EXTERNAL` attribution與boundary proof。不得restore、
  delete、quarantine、stage、commit或把absence當作刪除授權。
- Current S10R3 incident的三個`implement-verify-loop-origin/` untracked files符合此
  分類：它們與S10R3 scope／evidence無重疊，A46.1 exact-five commit未觸碰，且workflow
  不需要其bytes。保存successor observation後，fresh Phase-1 audit可繼續。
- 本治理修正不改science；S10R3保持`not_evaluated / edge=null`，只有post-audited
  `S10R3:S1_ENTRY_GO`可啟動S11。

### 6.12 2026-07-31 A46.3 predecessor-capsule recovery

- Predecessor execution完成固定512個CPU chunks；Mapping A在產生任何corpus前因
  bound state-method serializer defect fail closed。Current lifecycle是
  `CHANGES_REQUIRED / not_evaluated / edge=null`，沒有formal scientific report。
- Reviewer A與independent adversarial auditor完成一輪cross-examination及一輪final，
  對A46.3 A+皆`AGREE`。使用者授權S10R3 blocker在兩位reviewers無重大異議後由Main
  直接核准，不再逐案回user；scientific change、push與scope外不可逆操作不在其中。
- A46.3新增唯一full-lock-digest predecessor capsule、staging／journal、stable admission
  lock、四項no-replace relocation與Git-tracked lineage seal。Canonical active paths保持
  不變；舊raw evidence與`K=19`只作diagnostic，successor不得讀取或重用。
- Future successor generation固定為`S10R3-A46.3-G2`。完成fresh authority／plan／
  implementation／lineage／lock audits並重新取得`LOCKED_READY`後，從draw 0完整重跑。
  Scientific projection仍精確為`185c6ae6…e1e`。
- Pre-seal雙reviewer發現並一致要求role isolation、9-check audit parity、exact capsule
  inventory、合法journal／seal、stable admission inode及cumulative resource lineage。
  使用者已追認本輪所有必要authority；實際fresh-role lineage固定`11/11`，不再建立新
  role，只resume既有roles。以上只強化execution provenance，不改scientific gate。

### 6.13 2026-07-31 A46.4 one-time staging-manifest repair

- A46.3的四項relocation已完成，但journal仍停在合法五事件`MOVING`；既有staging
  manifest尚未`staging_verified`，其core／entries正確但漏寫frozen auxiliary digests。
- 兩位既有independent reviewers最終一致：unchanged A46.3不允許直接replace或
  quarantine；唯一合法路徑是先seal A46.4 exact one-time lifecycle amendment。使用者
  已預先核准本輪S10R3 reviewer-agreed blocker authority。
- A46.4只允許在exact old manifest、journal、stable admission inode與四份fresh
  inventory全部相符時，於同parent以exclusive temp／fsync執行一次atomic replacement；
  corrected identity驗證後才可沿原journal追加`staging_verified`。任何drift都fail
  closed，禁止rollback、重做relocation、quarantine或第二次replacement。
- Lineage seal與successor lock必須綁old/new manifest repair identities。Scientific
  projection、`S10R3-A46.3-G2`、fresh draw 0、outcome matrix與唯一S11 edge均不變。

### 6.14 2026-07-31 A46.5 reproducible mapping-failure recovery

- G2完成固定512 chunks、fresh classification及`K=C_greedy=19`selection後，Mapping A
  第六個required config `4ffcecf6…`在pinned KernelWriter重現resource error 5。
  Attempt 1是formal fail-closed；誤建立並立即中止的fresh diagnostic thread在attempt 2
  前把實際role usage變成`12/11`，所以attempt 2只保留為diagnostic。
- G2固定為`CHANGES_REQUIRED / not_evaluated / edge=null`，沒有scientific report或
  reusable outcome。使用者明確指定的新建independent Reviewer A
  `/root/s10r3_a46_5_reviewer_a`與既有independent adversarial auditor
  `/root/s10r3_a46_3_reviewer_a`完成pre-seal cross-examination與evidence-backed final；
  兩者一致`AGREE`且沒有material dissent。Implementer不計入reviewers。這個exact新role
  使累積provenance成為`13/13`，不得再新建role。Successor runner
  只允許兩個獨立cwd、append-only的full-K attempts；同一required config與signature
  連續兩次hard failure才建立正式mapping-failure corpus及
  `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`。禁止第三次retry、
  replacement、後續K掃描、Pass B及GPU。
  Allowlist固定為`KernelWriterAssembly_overflowedResources`、error code `5`、worker
  return code `23`與`processKernelSource` result `-2`；failure→success、success→failure、
  signature不同、missing／partial／timeout、其他code或unknown field一律
  `CHANGES_REQUIRED / not_evaluated / edge=null`。
- A46.5以新的journal/capsule/seal forward-only退役G2四項component；舊G1 lineage逐
  位元不變。Future generation固定`S10R3-A46.5-G3`，effective lock須綁G2 capsule、
  實際`13/13`role provenance、resource lineage與outcome absence，並從draw 0完整重跑。
- Scientific/oracle projection保持`185c6ae6…e1e`；search space、schedule、selector、
  mapping/correctness/noise criteria、outcome matrix、claim、唯一S11 edge與no-push
  boundary全部不變。

### 6.15 2026-08-01 S10R3 G3 terminal closeout

- G3 effective lock commit
  `6ac2f8541d1eb819caae634d087b664d15bf098d`通過post-commit audit後，formal discovery
  從draw 0完成global 32 chunks與15條conditional streams各32 chunks；總數固定為
  512 chunks／262,144 draws，114個accepted occurrences皆為distinct configs。
- Support classification為205個`supported_witnessed`、9,819個
  `support_unobserved`、0個`support_proven_absent`。`DepthU=1024`仍是unobserved，
  不是absence proof；actual YAML與baseline semantics未改。
- Deterministic selector得到90個mandatory atoms、`C_greedy=K=19<=20`與
  `L_axis=18`。Mapping Pass A在slot 5／config `4ffcecf6…`兩次完整重現A46.5
  allowlisted resource-overflow signature，故依法terminalize為
  `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`。Pass B、native、GPU、
  correctness與noise為`NOT_REACHED_BY_FROZEN_GATE`。
- Independent reproduction與Plan-A-blind fresh verifier皆PASS；B01–B21、C01–C09通過，
  C10由exact staged audit、`CLOSEOUT_ACK`、local commit及post-commit audit完成。
  S10R3 committed projection為`CHECKPOINT_COMPLETE`，S11維持`not_activated`，沒有
  positive gate record或push。

### 6.16 2026-08-02 A47 S10R4 exact-frame authority

- Fresh reviewers `/root/pipeline_rebaseline_reviewer_a`與
  `/root/pipeline_rebaseline_reviewer_b`完成兩輪cross-examination及一輪
  evidence-backed final，均`AGREE`；使用者選擇並核准exact-frame S10R4。
- S10R3 terminal negative/null及所有artifacts保持immutable。S10R4不redraw、不開
  conditional stream；只在pre-outcome逐child rehash成功後窄重用完整sealed
  114-config frame。S10R3 K=19 membership、mapping attempt/decision及verifier verdict
  不可作S10R4 result evidence。
- 全部114 configs各跑兩次normal KernelWriter filter。2/2 success進stable survivor
  pool；2/2 ordinary attrition保留在exact-frame denominator；discordance、exception、
  timeout、partial或identity/path drift為`CHANGES_REQUIRED / not_evaluated`。
- Complete census後才計算
  `mandatory = prelocked_candidate_atoms ∩ operational_codegen_witnessed_atoms`及
  `K=max(10,C_greedy)`, `K_max=20`。Fresh mapping/native/correctness/noise gates保持，
  禁止replacement、K+1、redraw或人工atom selection。
- 唯一positive edge是`S10R4:S1_ENTRY_GO_EXACT_FRAME -> S11`；claim只限exact sealed
  frame含bounded reproducible fixture。
- A47當時要求S11 fresh建立multiplicity-preserving `F_valid -> F_codegen` frame；該
  projection後由A51擴充為`F_valid(raw) -> F_effective -> F_codegen`。Codegen rejects
  保留在global `F_valid` occurrence-mass coverage denominator，conditional streams不
  pooled。Whole-gene fail-closed保持；value-level proposal延後。
- A47/A48當時的execution projection是R3 standalone
  `T-S10R4-B02 / CU-S10R4`，binding-01 retired且binding-02 lock absent；該historical
  projection後由A50/A51 supersede。沒有push授權。

### 6.17 2026-08-02 A51 S10R4 binding-04 dual-lineage authority

- Binding-02在effective lock及`LOCKED_READY`後的第一個formal child證明singleton使用
  `Backend.Name: Exhaustive`會在backend factory拒絕，留下partial且沒有到達normal
  Tensile/KernelWriter path；它已退休為
  `cancelled / BLOCKED / not_evaluated / edge=null / lock=superseded`。A50 binding-03只
  授權`Exhaustive -> Tensile`與完整Tensile source closure；它在pre-KernelWriter
  sentinel觀察到raw declaration經normal resolver轉成不同effective state，因而在
  lock前fail closed並成為
  `binding_status=superseded_prelock / execution_status=cancelled /
  checkpoint_state=BLOCKED / criterion_status=CHANGES_REQUIRED /
  scientific_outcome=not_evaluated / edge=null / lock_state=absent /
  lock_never_created=true`。兩者都沒有scientific formal result。
- 已知row 0的MI9→MI4可由完整derived MI fields精確反演；
  `ScheduleGROverBarrier=1->0`、`StaggerU=16->0`及
  `StaggerUStride=256->0`是behavior-changing resolution。原始write、KernelWriter、
  GPU與GFLOPS皆未到達，不能把這次failure稱為KernelWriter attrition。
- 兩位fresh independent reviewers以同一evidence完成一輪cross-examination及一輪
  evidence-backed final，均`AGREE`；使用者於`2026-08-02T17:13:10Z`核准pending
  binding-04 dual-lineage amendment及本輪reviewer-supported in-scope decisions。
- A51保持exact 114 raw occurrences／hashes及全部multiplicity作sampling population與
  denominator，另在剩餘113 rows尚未檢查前prelock closed
  `declaration -> resolver -> atom -> codegen -> mapping` identity stack。Formal
  execution仍是完整Census A 114 + Census B 114，不dedup、不early stop、不繼承prefix。
- Operational atom、collision、selection及mapping使用stable resolver-effective/codegen
  identity；normalized-away raw value不取得raw-value／controllability／guidance credit。
  `K=max(10,C_greedy)<=20`、mapping A/B exact `3K`、correctness/noise gates及唯一
  `S10R4:S1_ENTRY_GO_EXACT_FRAME -> S11` edge不變。
- S11 future lineage改為fresh multiplicity-preserving
  `F_valid(raw) -> F_effective -> F_codegen`。Positive claim只限固定raw frame經pinned
  resolver與normal KernelWriter workflow形成bounded reproducible distinct-effective-state
  entry fixture；不主張raw injectivity、value-level causal effect、general support、
  ranking或production readiness。
- Binding-04在prelock source closure因derived `ProblemType.Index{tensorIdx}` relation未關閉
  而固定為`superseded_prelock / CHANGES_REQUIRED / not_evaluated / edge=null /
  lock=absent`。Binding-05保留該science，但在implementation前因ignored ledger
  canonical hash-chain failure固定為相同non-scientific null-edge狀態。Current binding-06
  是R3 standalone `T-S10R4-B06 / CU-S10R4`；目前
  `DESIGN_APPROVED / not_started / not_evaluated / edge=null`，fresh contract與lock absent。
- B06以exact one relational rule與兩份independently authored exact-89-node closure要求
  unresolved exact 0。Committed machine contract須在Plan-B/Plan-A前凍結exact
  implementation、execution-artifact與delivery lists。S10R4 cumulative role cap exact 9：
  historical 7、clean successor Main第8、唯一剩餘slot保留fresh terminal verifier；其他
  工作resume既有implementer/auditor/reviewers。

## 7. Downgrade review gate

以下狀況一律先產生decision packet並停在`blocked-awaiting-user-decision`：

- `DEGRADED_PROXY`；
- two-size／reduced-regime mode；
- `S2_H5_RESOURCE_BOUNDED_PILOT`；
- single-cluster Stage 3 pilot；
- 任何減少workloads、runs、seeds、metrics、validation、acceptance或scope的替代方案。

Decision packet必須列出原設計、目標證據、已完成／缺失工作、root cause、downgrade對power／comparability／claim的影響、保留原設計的替代方案與建議。Diagnostic partial run不會完成checkpoint或解鎖下游。

## 8. From-scratch S00 bootstrap

本設計 bundle不建立`protocol/`。未來只有 S00 execution可首次建立：

```text
protocol/
└── v1/
    ├── README.md
    ├── study-contract.yaml
    ├── amendment-ledger.jsonl
    ├── schemas/
    └── locks/
        └── s00-foundation-lock.json
```

- Genesis使用全新identity，`parent_lock: null`。
- 不得包含 M00 version、hash、criterion、registry、path或migration provenance。
- 先實作schema／validator／lock writer與fresh deterministic fixtures，但在lock生效前不產生outcome evidence。
- S00 lock綁定committed charter、parent plan、S00 design、rule/skill revisions、Plan-B、exact whitelists、fixtures/seeds與report target。
- Evidence開始後若schema、fixture或whitelist改變，必須append amendment／建立新lock並重跑，不能覆寫。
- Git history中的舊`protocol/`內容不能作template、compatibility target或PASS evidence。

S00開始前仍需另行取得ordinary baseline commit授權，把本次intentional protocol deletions與authority/design bundle固定為stable committed baseline；那個baseline commit不是S00 closure。

## 9. Legacy archive

`legacy/`保留M00–M09歷史正文，但所有active-looking metadata都已改成`historical_*`。Successor只表示主題關聯，不表示artifact、criterion、schema、lock、hash、registry、test或outcome migration。

- [M00](legacy/m00-study-contract-observability-design.md)
- [M01](legacy/m01-step0-integration-gate-design.md)
- [M02](legacy/m02-guidance-plumbing-design.md)
- [M03](legacy/m03-exp0a-cold-headroom-design.md)
- [M04](legacy/m04-exp0b-widening-gate-design.md)
- [M05](legacy/m05-expc-ranking-oracle-design.md)
- [M06](legacy/m06-exp1-injection-b-design.md)
- [M07](legacy/m07-exp2-a-safe-b-factorial-design.md)
- [M08](legacy/m08-exp3-multishape-design.md)
- [M09](legacy/m09-overall-confirmation-design.md)

任何從legacy URL進入的讀者都必須返回本README，再由active checkpoint index取得權威。
