---
checkpoint_id: S10R1
title: Stage 1 valid-support entry measurement recovery
stage: 1
design_status: approved
execution_status: cancelled
checkpoint_state: BLOCKED
scientific_outcome: not_evaluated
lock_state: superseded
risk_tier: R2
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S10R1
execution_tranche: T-S10R1-CANCELLED
closure_unit: null
governance_event: A32
operational_block_reason: user_cancelled_at_safe_boundary
superseded_by: S10R2
hypothesis_id: S10R1-H1
dependencies:
  - checkpoint_id: S00
    required_edge: S00_EVIDENCE_READY
  - checkpoint_id: S10
    required_terminal: CHECKPOINT_COMPLETE_negative_at_48c26297fc6815e6edfcc89b8503e47370fedc53
entry_criteria: []
criterion_refs: []
failure_ids: []
allowed_outgoing_edges: []
formal_report_path: null
blocker_path: null
historical_diagnostic_lock_paths:
  - protocol/v1/locks/s10r1-stage1-entry-protocol-lock.json
  - protocol/v1/locks/s10r1-stage1-entry-execution-lock.json
historical_implementation_boundary_max:
  - S10R1-only authority, validity-ledger, selection, mapping, Formocast, runtime-queue, correctness and noise pipeline
  - S10R1-only protocol/v1 schemas, contract, locks, manifests, evidence and tests
historical_delivery_boundary_max:
  - S10R1 implementation and tests formerly selected by exact-path planning
  - protocol/v1/**
  - ../ductile-origami-warmstart-experiment-plan.md
  - README.md
  - s10r1-stage1-valid-support-entry-recovery-design.md
forbidden_report_paths:
  - reports/staged/s10r1-stage1-entry-recovery-report.md
forbidden_historical_roots:
  - protocol/v1/run_s10_entry.py
  - protocol/v1/s10-entry-contract.yaml
  - protocol/v1/locks/s10-stage1-entry-lock.json
  - protocol/v1/manifests/s10-mapping-corpus.json
  - protocol/v1/evidence/s10-decision.json
  - reports/staged/s10-stage1-entry-gate-report.md
  - s10-stage1-entry-access-mapping-gate-design.md
forbidden_downstream_roots:
  - reports/staged/s11-stage1-model-only-factorization-report.md
  - reports/staged/s12-stage1-real-score-audit-report.md
  - reports/gen0-factorization-mvp-report.md
  - reports/short-horizon-persistence-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
---

# S10R1 — Stage 1 valid-support entry measurement recovery（cancelled）

導航：[active checkpoint index](README.md)｜[experiment plan §2](../ductile-origami-warmstart-experiment-plan.md#2-d1d2-entry-gate)｜[historical S10 report](reports/staged/s10-stage1-entry-gate-report.md)

> **Do not execute.** S10R1已依append-only governance chain的user-authorized
> `A32` event在safe boundary取消。以下原設計細節只保留為historical diagnostic
> provenance，不再授權contract、lock、evidence、report或edge。

## 1. 白話目標與目前狀態

原核准目標是重新量一次真正對應Ductile operational domain的Stage 1 entry gate：
候選必須先通過
同一個`valid_fn`，Formocast的finite early-terminate sentinel與runtime queue狀態必須
分開記錄，然後才做原本的mapping、correctness與noise gate。

這不是把S10改判。S10在自己的frozen raw-boundary fixture下仍是完整、有效且不可改寫
的negative。S10R1執行現已`cancelled / BLOCKED`（operational），
`scientific_outcome=not_evaluated`、`edge=null`，不是`CHECKPOINT_COMPLETE`，也不建立
scientific formal report。新的active sibling是
[S10R2](s10r2-stage1-support-aware-entry-recovery-design.md)。

## 2. Hypothesis、範圍與反證

**S10R1-H1（未評估）：**在保持S10 exact source pins、actual YAML bytes、search space、
groups／candidate order／existing weights、三個sizes與全部entry thresholds不變時，
可以從Ductile-valid support預鎖exact 10-config corpus，忠實重現Formocast
model／runtime semantics，並完成correctness與noise gate。

這個hypothesis沒有scientific outcome。Voluntary cancellation與diagnostic
non-discovery都不是negative或inconclusive；S10R1不能回答「可否合法開始S11」。

原設計預定檢查以下狀況，但A32前沒有形成任何scientific判讀：

- exact support proof顯示required coverage atom不存在；
- locked config或anchor可重現地無法完成mapping／codegen／correctness；
- stochastic nominal-draw cap耗盡但不能建立exact-ten coverage（實際diagnostic
  non-discovery不分類為negative或inconclusive）；
- schema、helper、API、guard attribution或bound-byte異常：
  `CHANGES_REQUIRED`，不得冒充scientific outcome；
- source lineage、exact pin或byte-identical YAML parity失敗：停止並另行amend，
  不把source upgrade混入S10R1。

## 3. Historical boundary 與 dependency

- S00已以`S00_EVIDENCE_READY`完成。
- S10已在commit
  `48c26297fc6815e6edfcc89b8503e47370fedc53`完成為
  `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`。
- S10R1引用S10 terminal record只作historical administrative／provenance；
  S10不會補發scientific edge。
- `A32`已固定S10R1為`cancelled / not_evaluated / edge=null`。Generation 0的L0與
  selection tree、generation 1的tracked capsule、pre-L0 implementation、tests、
  caches與verification artifacts都只可作immutable diagnostics。
- S10R1任何empirical、repair或diagnostic artifact都禁止重用為S10R2 gate evidence。
- 只有future post-audited `S10R2:S1_ENTRY_GO`可以啟動S11；S10R1沒有現在或未來
  outgoing edge。
- 不授權proxy、two-size、H5、reduced regime、threshold alteration或其他
  workload／acceptance／claim downgrade。

## 4. Historical source 與 actual-YAML isolation（non-executable）

執行前必須fresh resolve並記錄：

- Ductile authority ref
  `refs/remotes/origin/ductile_integration`；
- GEKO authority ref
  `refs/remotes/origin/users/pkamd/geko_pr`；
- S10 exact Ductile pin
  `5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39`；
- S10 exact GEKO pin
  `d32abacfd13579d1f523f035b7a10b0734c4ac47`；
- S10 actual YAML SHA-256
  `faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36`。

S10R1明確以兩個historical exact pins作controlled inputs，以隔離measurement
變更；current tips只提供authority-lineage證據。Exact objects必須存在於預期lineage，
且fresh regeneration必須byte-identical。任一不成立即停止；不得把current checkout、
cache、build、container或GEKO branch附帶的Ductile files當source authority。

## 5. Historical L0／L1 design（superseded）

### 5.1 L0 protocol lock

L0在任何recovery selection evidence前綁定：

- exact source／YAML hashes與authority-lineage checks；
- actual GA probability construction與float32語意；
- pinned `valid_fn`、seed domain／spawn、stream／chunk order；
- nominal-draw ceilings與final truncated-chunk規則；
- YAML／source-derived coverage atoms；
- selector、tie-break、duplicate／multiplicity規則；
- source-order sentinel guard table；
- status taxonomy、schemas、commands、whitelists與完整stop matrix。

L0之後、L1之前只允許label-blind CPU candidate construction：actual-probability
draws、同一validator，以及建立validity／預註冊coverage所需的deterministic
solution／structural resolution。這個階段禁止：

- `predictedPerformance()`或任何Formocast output；
- GFLOPS／real labels；
- GPU smoke、timing或noise。

### 5.2 L1 execution child lock

L1綁定：

- L0 hash與完整global／conditional ledgers；
- exact 10 configs與sorted-hash indices `0,4,9`三個anchors；
- 原三個same-space sizes；
- resolved mapping inputs、required metadata與field provenance；
- resolved `PredictionThreshold`；
- eligible live `perlee` GPU selection與environment；
- Formocast／runtime semantics；
- smoke、correctness、63-cell noise schedule；
- commands、whitelists與report target。

這些paths與任何已產生generation都已superseded為diagnostic-only。不得建立fresh
S10R1 child、繼續選樣、重跑evidence、in-place edit、混用S10 evidence或替換anchor。

## 6. Historical valid-support selector（diagnostic-only）

### 6.1 Actual probabilities

逐byte／float32重現pinned `GeneticAlgorithm.probs`：

- weighted key使用
  `exp(-weight_beta * (w - w.min()))`後normalize；
- unweighted key維持uniform；
- grouped key保持單一categorical axis與原candidate order；
- 使用pinned `sample_chunk`等價stream及同一
  `_validate_solution`／`valid_fn`。

L0必須獨立驗證：

- configured `pop_size = 512`；
- `group_0`／maximum categorical-axis size `9,918`；
- constructor-resolved initial population
  `int(9,918 * 1.15) = 11,405`；
- `max_iters = 250`。

### 6.2 Bounded streams

- S10R1 ledger chunk固定為512 nominal draws；它來自configured default，
  不是resolved population或accepted target。
- Global與每個必要conditional stream的nominal ceiling都是
  `250 * 11,405 = 2,851,250` draws。
- 每stream最多5,568個完整512-draw chunks；若仍有需要，最後一個chunk固定434
  draws。
- 每個完整或最後truncated chunk後執行exact-ten set-cover檢查；第一次可行即停止。
  Ceiling不是必須耗盡的sample target。
- Global stream使用actual probabilities。
- 只有global缺少的atoms才依canonical token order啟動conditional stream；
  每stream只固定一個預註冊YAML boundary／sentinel token，其他axes仍用原
  probabilities。
- Global與conditional sampling laws、ledgers、multiplicity分開保存，不得混稱
  單一`pi_valid`。

Parent的4,096／8,192 global accepted targets與128／256 conditional accepted
targets仍屬S11 model estimation。S10R1不得提前執行S11 frame或把那些數字當
mapping acceptance。

### 6.3 Ledger、coverage 與 exact ten

每個nominal attempt保存pool、seed／chunk／draw order、raw indices／config、
resolved hash、accept／reject disposition與validity provenance。Accepted occurrence
在dedup前保存，duplicates、multiplicity與所有occurrence IDs不得遺失。

Sampling前由YAML／source預鎖coverage atoms：

- group first／last candidates；
- 每個適用residual first／last candidate；
- 明列的`-1/-2` sentinel values；
- 一個source-derived、score-blind sentinel-risk structural atom。

不得用observed sample minima／maxima事後發明atom。DepthU、GSU、
GRVW／VectorWidth、PGR、occupancy與required metadata是30-row mandatory
mapping／provenance checks；只有能在L0允許的label-blind structural resolution
中deterministically取得時，才同時作selection atom。

每個chunk boundary對first-occurrence unique config hashes執行固定greedy
set-cover：

1. 最大化新增coverage atoms；
2. tie-break為預鎖keyed hash
   `(pool_id, first_occurrence_id, config_hash)`；
3. 再以config hash決定。

若cover少於10筆，以相同first-occurrence／tie-break規則補到exact 10 distinct
valid hashes。Final corpus不得有第11筆、replacement或atom relaxation。

原設計曾預註冊cap耗盡後的inconclusive branch，但該branch從未形成scientific
outcome。A32之後，generation-0／1任何cap或non-discovery observation都只作
diagnostic，明確不是`FT-INCONCLUSIVE`；只有新S10R2 design可規範future support
classification。

先前uniform fixed-seed probe的`6/16 after 1,600 attempts`只作adjudication中的
feasibility warning；它沒有使用actual `group_0` weights，不是L0 input、gate
evidence，也不支持「weighted Gen0無法產生十筆」的claim。

## 7. Historical mapping、Formocast 與 runtime taxonomy

Exact ten ×三sizes的30 rows必須fresh A/B重現，逐欄保存direct／derived path、
round-trip與provenance，且不得猜occupancy、effective GSU、
`MathClocksUnrolledLoop`、未解`-1/-2`或backend metadata。

每row分開記：

1. `ductile_validity_status`：同一pinned validator的結果；
2. `formocast_model_status`：
   - normal finite estimate；或
   - exact finite early-terminate sentinel
     `microSeconds=9999999.9, hitRate=0`，同時保存pinned source-order
     first-taken guard及所有true guards；
   - non-finite、guard無法獨立重算或pair／guard不一致皆為integrity／API anomaly，
     走`CHANGES_REQUIRED`；
3. `runtime_queue_status`：
   - resolved threshold `>1`時為`prediction_disabled`；
   - 否則對完整frozen cohort重現`checkSolution`、stable sort、threshold
     index／value與queue prefix，記`queued`或`excluded_by_threshold`。

單一row不得稱runtime-threshold rejection，不得改threshold製造rejection。
Validity rejection只屬selection diagnostics，不算Formocast rejection。

Amended conformance requirement是：至少一個預鎖、source-guard-targeted、
score-blind的valid config×size實際產生exact model sentinel。

## 8. Historical GPU、correctness 與 noise

- 只使用現有`perlee` container，不建立／停止／重建container；
- 直接檢查可見gfx942 cards，使用當下符合`SPX / NPS1`且有資源的卡，不需預約；
- 記錄visible index、PCI bus、serial／unique ID、ROCm／driver、clock與power policy；
- exact three anchors × three sizes完成generate／compile／smoke與nonzero
  correctness；
- 只有全部correctness通過才執行三anchors ×三sizes ×七repeats，共63 cells；
- 使用parent原`reduce_fn`、iteration escalation cap、`CV P95 <= 0.5%`與
  `delta_noise`定義，不改threshold或刪cell。

## 9. Cancellation matrix

| 狀況 | S10R1分類 | Outgoing edge |
| --- | --- | --- |
| User-authorized safe-boundary cancellation | operational `cancelled / BLOCKED` | `null` |
| Scientific outcome | `not_evaluated` | `null` |
| Generation-0 DepthU=1024或其他stochastic non-discovery | diagnostic only；不是`FT-INCONCLUSIVE`或absence proof | `null` |
| Generation 0／1 implementation、test、cache、lock、selection或verification | superseded／forbidden reuse | `null` |
| 想恢復S10R1或建立successor | forbidden；使用獨立S10R2 authority | `null` |

## 10. Historical maximum implementation 與 delivery boundary

允許：

- 新的S10R1-only runner、contract、schemas、locks、manifests、evidence與tests；
- ignored S10R1 run roots中的source materialization、build、logs與raw evidence；
- L0／L1 lifecycle、validity ledgers、mapping／Formocast/runtime helper、
  correctness與noise pipeline。

禁止：

- 修改或重用任何tracked S10 runner、contract、lock、corpus、decision、report或
  design；
- 修改source pin、actual YAML bytes、candidate space、groups、candidate order、
  existing weights、sizes、thresholds、workload或claim；
- 產生S11+ implementation、evidence或report；
- dependency install、credential／external write、container lifecycle mutation；
- push。

這個maximum boundary不再可供future planning。既有raw／transient evidence只作
immutable diagnostic provenance，不進S10R2 closure commit。

## 11. No scientific report／no checkpoint completion

S10R1沒有scientific formal report path，不建立
`reports/staged/s10r1-stage1-entry-recovery-report.md`。A32 governance event只形成
operational cancellation record，不把S10R1標成`CHECKPOINT_COMPLETE`，也不產生
closure commit或scientific edge。

## 12. Design-consensus record

- Trigger：S10 closeout後確認raw boundary fixture與Ductile valid-support domain錯位，
  且non-finite-only Formocast rejection不重現finite sentinel／runtime queue語意。
- Reviewer A：`/root/s10_postclose_recovery_a`。
- Reviewer B：`/root/s10_postclose_recovery_b`。
- 兩位fresh `gpt-5.6-sol/xhigh` reviewers以相同prompt獨立首輪、交換完整立場、
  交互詰問，並審查同一final candidate。
- 採納：新stable checkpoint、S10 immutable、historical-pin isolation、L0／L1、
  actual weighted valid sampling、bounded exact-ten selector、三層status taxonomy及
  原correctness／noise workload。
- 捨棄：S10 successor、post-hoc重標、invalid-row replacement、第11筆、
  threshold alteration、把S11 accepted targets搬進S10R1，以及把sampling
  non-discovery冒充support不存在。
- Shared resolution：只有post-audited S10R1 positive能產生新的
  entry edge是當時未執行的設計；A32已取消該authority，且不撤銷S10 negative。
- Reviewer A final：`AGREE`。
- Reviewer B final：`AGREE`。
- User-review basis：使用者已明確委派`/data1/perlee`內的此類block由
  design-discussion共識決定，不需再次停下取得核准；不授權push。

### 2026-07-28 A32 cancellation amendment

- 使用者核准在quiescent safe boundary停止S10R1，並建立新的sibling S10R2。
- Generation 0已在atomic boundary退休並sealed；generation 1未建立effective L0、
  selection、mapping、GPU、noise、decision或formal outcome。
- Durable interpretation固定為
  `execution_status=cancelled / checkpoint_state=BLOCKED /
  scientific_outcome=not_evaluated / edge=null`。
- 所有generation 0／1內容只能保留為diagnostic provenance，且禁止重用為S10R2
  evidence。S10R1沒有scientific report，也不是`CHECKPOINT_COMPLETE`。
- Current execution governance floor是
  `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`；累積resource／repair／thread budgets
  不能因S10R2、successor、new root或replacement role歸零。
