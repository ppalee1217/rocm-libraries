---
checkpoint_id: S10R4
binding_id: binding-04
title: Stage 1 resolver-effective dual-lineage operational entry recovery
stage: 1
design_status: approved
authority_projection: approved_pending_exact_commit_and_postcommit_audit
execution_status: not_started
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R3
scientific_gate: S10R4
execution_tranche: T-S10R4-B04
closure_unit: CU-S10R4
hypothesis_id: S10R4-H1E
dependencies:
  - checkpoint_id: S10R3
    required_terminal: CHECKPOINT_COMPLETE_negative_edge_null
entry_criteria:
  - committed_A51_binding_04_authority
  - intact_sealed_S10R3_G3_raw_occurrence_frame
  - closed_layered_resolver_identity_before_remaining_row_evidence
  - durable_binding_04_contract_and_effective_lock_before_outcomes
criterion_refs:
  - S1_ENTRY_GO_EXACT_FRAME
  - S1_ENTRY_BLOCKED
failure_ids:
  - FT-BLOCKED-MAPPING
  - FT-BLOCKED-CORRECTNESS
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S1_ENTRY_GO_EXACT_FRAME
    target_checkpoint: S11
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s10r4-s1-entry-go-exact-frame.json
formal_report_path: reports/staged/s10r4-stage1-exact-frame-entry-report.md
future_frozen_contract_path: protocol/v1/s10r4-stage1-resolver-effective-entry-binding-04-contract.yaml
future_effective_lock_path: protocol/v1/locks/s10r4-stage1-resolver-effective-entry-binding-04-lock.json
implementation_boundary_max:
  - protocol/v1/run_s10r4_entry.py
  - protocol/v1/s10r4/**
  - protocol/v1/s10r4-stage1-resolver-effective-entry-binding-04-contract.yaml
  - protocol/v1/schemas/s10r4-entry.schema.json
  - protocol/v1/locks/s10r4-stage1-resolver-effective-entry-binding-04-lock.json
  - protocol/v1/manifests/s10r4-*.json
  - protocol/v1/evidence/s10r4-*.json
  - protocol/v1/evidence/gate-records/s10r4-s1-entry-go-exact-frame.json
  - projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10r4_entry.py
delivery_boundary_max:
  - binding-04 implementation and tests selected by exact-path planning
  - protocol/v1 S10R4-only contract, schema, lock, manifests, evidence, and gate record
  - projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10r4_entry.py
  - reports/staged/s10r4-stage1-exact-frame-entry-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - ../surrogate-dse-plan.md
  - README.md
  - s10r4-binding-04-resolver-effective-recovery-authority.md
  - s10r4-stage1-resolver-effective-operational-entry-design.md
  - s11-stage1-model-only-factorization-design.md
forbidden_downstream_roots:
  - reports/staged/s11-stage1-model-only-factorization-report.md
  - reports/staged/s12-stage1-real-score-audit-report.md
  - reports/gen0-factorization-mvp-report.md
  - reports/short-horizon-persistence-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_fresh_reviewer_agree_and_user_auto_approved
---

# S10R4 — Resolver-effective dual-lineage operational entry recovery

導航：[checkpoint index](README.md)｜[A51 authority](s10r4-binding-04-resolver-effective-recovery-authority.md)｜[original S10R4 design](s10r4-stage1-exact-frame-operational-entry-design.md)｜[S11](s11-stage1-model-only-factorization-design.md)

## 1. 白話目標與 hypothesis

S10R3保存的是「抽到並被Ductile接受的raw config」。正常workflow在KernelWriter前還會
建立resolver-effective `Solution`；有些raw值會被轉成等價表示，有些則會因guard被真正
關掉。Raw config回答「抽到什麼」，effective state回答「實際交給codegen什麼」，不能再
把兩者混成同一個hash或atom witness。

**S10R4-H1E：**固定的114-occurrence raw frame經pinned shared resolver與normal
error-tolerant KernelWriter後，存在一個由frozen deterministic selector產生、
`10 <= K <= 20`的distinct stable operational-identity fixture，能覆蓋其真正realized的
prelocked candidate atoms，並通過mapping、native conformance、correctness與noise gates。
完整stable survivor pool可以大於20；上限只約束`C_greedy`／selected `K`。

可推翻H1E的完整科學觀察是：完整114x2 census後少於10個unique stable operational
survivors、realized mandatory atoms無法cover、`C_greedy>20`、reproducible mapping或
correctness failure。完整noise criterion失敗會阻止positive，但依frozen outcome matrix只能是
`inconclusive / FT-INCONCLUSIVE`，不是H1E的scientific falsification。Projection未知、pass
discordance、partial child或lineage錯誤也不是科學反證，而是
`CHANGES_REQUIRED / not_evaluated`。

Positive只支持：

> 固定的114-occurrence raw frame，在指定source、YAML、resolver、KernelWriter與toolchain
> 下，能形成可重現、bounded的distinct-effective-state Stage-1 entry fixture。

它不支持raw declaration逐值實現、raw→effective injective、value-level causal effect、
一般support/survival probability、ranking/factorization efficacy或production readiness。

## 2. Trigger、lineage 與 amendment 時點

Binding-03在任何lock/formal evidence前，以預先固定的row0 diagnostic發現MI表示轉換與三個
behavior-changing resolver overwrites。兩位fresh reviewers在一輪交叉詰問後一致採用
dual-lineage方案，使用者隨後核准。這是post-observation但pre-outcome amendment；最終報告
必須揭露trigger、時間、已知row0資訊與未讀取其餘113 rows的事實。

Binding-03固定為
`execution_status=cancelled / checkpoint_state=BLOCKED /
criterion_status=CHANGES_REQUIRED / scientific_outcome=not_evaluated / edge=null /
lock_state=absent / lock_never_created=true`。
Binding-02與binding-03所有bytes只作immutable diagnostic provenance，不提供B04 empirical
credit。S10R3 terminal negative/null完全不變；允許重用的唯一empirical population仍是其
sealed 114-occurrence raw frame，且每次都需fresh direct replay/rehash。

## 3. 五層 identity 與 measurement boundary

### 3.1 Declaration layer

對每個registry occurrence保存raw bytes、raw hash、ForkParameters bytes、stream/chunk/draw
association與prelocked candidate membership。Occurrence count與raw-distinct count都必須
exact 114。這一層是sampling denominator，不因resolver collision或codegen attrition縮小。

### 3.2 Resolver layer

在normal shared builder產生一個accepted `Solution`時、進入original write前，保存closed
canonical projection。Resolver semantic identity只含consumer-relevant effective fields；
resolver evidence identity另保存raw link與轉換過程：

- 所有prelocked candidate axes的resolved值與exact types；
- MatrixInstruction及其完整derived MI state；
- pinned source audit認定為KernelWriter/mapping semantic input的derived fields；
- semantic identity保存projection schema/version、全部effective fields/exact types、
  frozen source-schema identity與canonical effective bytes/hash；
- evidence identity保存每個raw field的
  `identity | reversible_representation | behavior_changing_resolution` classification、
  before/after canonical bytes、guard operands、source path/blob/symbol/rule identity與raw
  occurrence/pass association。

Contract必須在讀取其餘113 rows前，用pinned-source static audit、synthetic fixtures與fault
tests鎖定closed schema。除了source-proven exact inverse（初始唯一允許MI9 inverse）外，
任何不同值都機械式標為behavior-changing，不靠observed-field allowlist。Missing、unknown、
type drift、ambiguous serialization或source drift一律fail closed。

### 3.3 Atom layer

`realized_prelocked_atoms`只包含effective projection中實現、且能機械對應到prelocked
candidate universe的axis/value。Normalized-away raw值不提供raw-value witness；同一row其他
未變atoms仍可提供operational witness。Resolver產生但不在prelocked universe的值不會成為
mandatory atom。Grouped/compound candidate需完整tuple value-preserving或approved
reversible才count。

Effective realization與raw intervention evidence分開。例：raw `StaggerU=16`若effective為0，
可在effective namespace證明該operational state使用0（若0本來就在prelocked universe），
但不能證明raw 0被抽到、raw 16被實現或任一raw value有可guidance的獨立效果。

### 3.4 Codegen layer

每個child仍走original error-tolerant path，分開保存：

- `codegen_semantic_identity`：canonical `getKeyNoInternalArgs`、required assembly/helper
  semantic sets、normalized artifact semantics與post-filter membership class；
- `codegen_evidence_identity`：raw occurrence/pass、cwd/path、inventories、artifact digests及
  structured terminal records。

Raw hash、pass、cwd、path、timestamp或evidence digest不得進semantic identity。Resolver hash
相同但codegen semantic identity不同代表projection不完整，必須`CHANGES_REQUIRED`，不得硬拆
成兩個collision classes掩蓋問題。

`operational_identity`精確等於只有三個sorted-key members的canonical JSON object：
`resolver_semantic_identity`、`atom_identity`、`codegen_semantic_identity`。Serialization為
UTF-8、recursive key sort、compact、finite-number-only且type preserving；
`operational_hash=SHA256(exact canonical bytes)`。比較必須先比exact bytes，digest只作索引。

### 3.5 Mapping layer

對每個selected operational identity與三個sizes保存`(operational_hash,size_id)`、deterministic
raw representative、全部aliases/multiplicity、resolver semantic/evidence identities、codegen
semantic/evidence identities、SizeMapping、Formocast/runtime input與required-field provenance。
Mapping A/B逐層byte parity；digest只作索引，不能取代bytes。

## 4. Prelock source schema 與 information firewall

Authority/contract/Plan、source schema與synthetic diagnostics seal前，禁止解析其餘113 rows的
resolved state、collision、coverage或K feasibility。允許：

- 讀pinned source與symbol/blob chain；
- 由actual YAML讀candidate axis名稱/型別/universe，但不執行frame rows；
- synthetic values與known row0 regression；
- 測試MI inverse、generic behavior-changing classification、unknown-field fail-closed、atomic
  staging與consumer identity capture。

禁止：full-frame prelabel resolver scan、survivor預測、collision count、realized atom union、
cover或K計算。這避免看到可行性後挑boundary。

## 5. Formal 114×2 census

Effective lock與ordinal-0 activation通過後：

1. Pass A按registry 0–113完整執行；
2. 每child先驗raw/ForkParameters identity；
3. shared resolver產生exactly one Solution並封存resolver/atom projection；
4. 同一child繼續original write/KernelWriter，封存codegen identity與terminal result；
5. Pass A 114/114 terminal後才開始fresh Pass B 0–113；
6. 不early-stop、dedup、replacement、reorder、third pass或繼承舊prefix。

只有兩pass resolver projection與terminal codegen semantics都stable的success才是stable
operational survivor；兩pass合法ordinary filter attrition是stable attrition。任何discordance、
exception、timeout、signal、partial/missing、unknown transform、association/source/tool drift為
`CHANGES_REQUIRED`。

## 6. Collision、multiplicity 與 selection

Raw denominator固定114。先依resolver semantic bytes形成涵蓋全部114 raw occurrences的
resolver-effective partition；每group保存所有raw aliases，所有group multiplicity總和exact
114。每group再依所有aliases及A/B結果分類為stable-survivor或stable-attrition。若同一
resolver-effective group混有success/attrition、terminal semantics不同或codegen semantic
identity不同，視為projection falsification並fail closed。Survivor selection只取
stable-survivor groups；其multiplicity總和等於survivor raw mass，不要求等於114。每個raw
occurrence的evidence identity仍完整保存。

Selection unit是unique stable operational identity：

```text
mandatory_atoms = prelocked_candidate_atoms ∩ realized_atoms(stable operational groups)
C_greedy = deterministic greedy cover size
K = max(10, C_greedy)
K <= 20
```

gain tie依group first registry occurrence、再raw hash；不足10時同序padding；final order依
operational hash再representative raw hash。少於10 groups、cover impossible或`C_greedy>20`在
complete census後是`negative / FT-BLOCKED-MAPPING`，不代表support不存在。

## 7. Mapping、native、correctness 與 noise

Mapping A與B各exact `3K` rows、不得replacement或第`K+1`筆。每row含完整五層identity與
provenance，且只使用下列唯一decision table：

- required field猜測、consumer/projection mismatch、A/B identity drift、partial或unknown：
  `CHANGES_REQUIRED`；
- 第一次complete attempt success：PASS，禁止retry；
- exact same prelocked allowlisted native mapping failure在exactly兩次complete attempts重現：
  `negative / FT-BLOCKED-MAPPING`；
- failure→success、signature不同或第三次attempt：`CHANGES_REQUIRED`。

Native sentinel/runtime conformance維持actual pinned Formocast、guard order、shared helper與
runtime queue adapter及fault substitutions。Correctness anchors仍為sorted operational K的
indices `{0,floor((K-1)/2),K-1}` × three sizes，9 cells全過後才跑63-cell noise；`CV P95<=0.5%`
與原`delta_noise`不變。不得因alias/collision替換anchor。

## 8. Outcome matrix、stopping 與 falsification

- `CHANGES_REQUIRED/not_evaluated`: identity/schema/source/lineage/partial/unknown/discordance/
  nonunique decision；無formal scientific report。
- operational `BLOCKED/not_evaluated`: only material external safety/capacity/preservation/
  authority boundary。
- mapping negative: complete census後unique stable groups<10、cover impossible、
  `C_greedy>20`或frozen reproducible mapping failure。
- correctness negative: frozen reproducible correctness failure。
- inconclusive: complete63 noise cells但criterion fail。
- positive:所有gates與reproduction/fresh verification通過。

任何terminal branch停止後續scientific stage。Runtime本身不作optional stopping理由；interrupt只
在atomic unit boundary resume。只有post-audited positive產生
`S10R4:S1_ENTRY_GO_EXACT_FRAME -> S11`。

## 9. S11 consumer contract

S11仍需fresh/disjoint seeds建立自己的occurrence population，不能重用S10R4的114 rows或K。
其lineage改為：

```text
F_valid(raw occurrence mass) -> F_effective -> F_codegen
```

所有raw occurrences與codegen rejects保留在`F_valid` denominator。Model/mapping features使用
effective semantics；raw value只有在frozen relation中實現且不被behavior-changing overwrite
時才取得raw-value guidance evidence。Context-dependent、normalized-away或collision-confounded
values不得取得value-level credit。Whole-gene fail-closed eligibility與value-level guidance
deferred不變。

## 10. Implementation、evidence 與 verification

Pre-evidence implementation需提供：closed resolver-schema record、atomic diagnostic staging、
five-layer schemas、source/consumer closure、two-pass child capture、collision reconciliation、
effective selector/mapping、state machine、reproduction與negative/fault tests。Committed B04
machine contract必須在Plan-B/Plan-A前鎖定exact implementation、execution-artifact及delivery
path lists；Plan-A只提供與contract一致的decision-complete instructions，不得創造或擴張
authority。不得用generation/root重置resource、repair或role-thread history。

S10R4 R3 lineage的fresh-role cap依A51由6一次性提高為8：既有五個pre-A51 spawned
roles、兩個A51 design reviewers合計七個；唯一剩餘slot保留給未參與implementation的fresh
terminal verifier。B04 implementer、adversarial auditor與ordinary reviewers必須resume既有
roles，不能再spawn replacement來重置獨立性或歷史。

Fresh verifier不得參與implementation或prebinding audit，且需從raw children重新計算：114
denominator、每occurrence transform、A/B parity、collision/multiplicity、realized atom universe、
greedy trace/K、mapping rows、所有reached downstream gates、unique outcome與claim boundary。

Positive、negative或inconclusive都需truthful terminal report；report必須materializeA51 trigger、
row0已知資訊、amendment timing、未在freeze前讀剩餘rows、所有agent adjudication與residual
uncertainty。Exact-path local commits與postcommit audit required；不push。
