---
checkpoint_id: S10R4
title: Stage 1 exact-frame operational entry recovery
stage: 1
design_status: approved
execution_status: not_started
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R3
scientific_gate: S10R4
execution_tranche: T-S10R4
closure_unit: CU-S10R4
hypothesis_id: S10R4-H1
dependencies:
  - checkpoint_id: S10R3
    required_terminal: CHECKPOINT_COMPLETE_negative_edge_null
entry_criteria:
  - committed_S10R4_exact_frame_authority_amendment
  - intact_sealed_S10R3_G3_discovery_frame
  - durable_S10R4_contract_and_effective_lock_before_outcomes
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
terminal_report_integration: standalone_report_integrates_s10r4_gate_record
blocker_path: protocol/v1/evidence/s10r4-operational-blocker.json
future_frozen_contract_path: protocol/v1/s10r4-stage1-exact-frame-entry-contract.yaml
future_effective_lock_path: protocol/v1/locks/s10r4-stage1-exact-frame-entry-lock.json
implementation_boundary_max:
  - protocol/v1/run_s10r4_entry.py
  - protocol/v1/s10r4/**
  - protocol/v1/s10r4-stage1-exact-frame-entry-contract.yaml
  - protocol/v1/schemas/s10r4-entry.schema.json
  - protocol/v1/locks/s10r4-stage1-exact-frame-entry-lock.json
  - protocol/v1/manifests/s10r4-*.json
  - protocol/v1/evidence/s10r4-*.json
  - protocol/v1/evidence/gate-records/s10r4-s1-entry-go-exact-frame.json
  - projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10r4_entry.py
delivery_boundary_max:
  - S10R4 implementation and tests selected by exact-path planning
  - protocol/v1 S10R4-only contract, schema, lock, manifests, evidence, and gate record
  - projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10r4_entry.py
  - reports/staged/s10r4-stage1-exact-frame-entry-report.md
  - ../s10r3-s11-value-level-guidance-amendment-proposal.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - ../surrogate-dse-plan.md
  - README.md
  - s10r4-stage1-exact-frame-operational-entry-design.md
  - s11-stage1-model-only-factorization-design.md
forbidden_downstream_roots:
  - reports/staged/s11-stage1-model-only-factorization-report.md
  - reports/staged/s12-stage1-real-score-audit-report.md
  - reports/gen0-factorization-mvp-report.md
  - reports/short-horizon-persistence-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree_and_user_selected
---

# S10R4 — Stage 1 exact-frame operational entry recovery

導航：[active checkpoint index](../README.md)｜[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)｜[S10R3 terminal report](../reports/staged/s10r3-stage1-bounded-cover-entry-report.md)

## 1. 白話目標與 hypothesis

S10R3的validator接受了114個完整config，但normal Ductile workflow還會把這些solution
交給KernelWriter。KernelWriter無法產生kernel的solution，正常語意是從operational
solution pool移除，不是立刻把整個valid frame判成mapping失敗。S10R3依其當時已鎖定的
contract在第一個required failure停下，因此該negative完全有效且保持immutable；只是它
沒有回答「同一完整sealed frame經normal codegen filter後，剩餘solution能否形成可信的
entry fixture」。

**S10R4-H1：**S10R3 G3完整、sealed、固定schedule產生的114個Ductile-validator accepted
distinct configs，在normal error-tolerant KernelWriter operational filter後，仍包含一個
可重現、bounded `K<=20`、覆蓋該exact frame operationally witnessed atoms的mapping
fixture，且其mapping、native helper conformance、correctness與noise gates全部通過。

Positive只支持：

> 這一個exact sealed frame，在指定source／YAML／toolchain identity及normal codegen
> filter下，包含可重現的bounded Stage-1 entry fixture。

它不支持一般valid support、未觀察candidate不存在、codegen survival probability、獨立
replication、Formocast ranking、factorization efficacy、prior mass、Gen0 improvement或
production readiness。

## 2. Immutable lineage 與允許的窄重用

S10R3固定為：

```text
CHECKPOINT_COMPLETE / negative / S1_ENTRY_BLOCKED /
FT-BLOCKED-MAPPING / edge=null
```

S10R4不得重標、覆寫、補跑或修改S10R3。它是新的R3 sibling scientific gate，使用
`T-S10R4 / CU-S10R4`。

唯一允許的empirical input是S10R3 G3已完整封存的discovery frame：

- 固定512 chunks／262,144 nominal draws的schedule與append-only ledger；
- 114 accepted occurrences及114 distinct canonical config hashes；
- 每個accepted occurrence的stream/chunk/draw provenance；
- fresh S10R3 candidate registry及support-classification identity，僅供重建每個config
  含有哪些prelocked candidate atoms；
- source／actual YAML／groups／weights／candidate order／three-size identities。

在任何S10R4 outcome前，exact-frame registry必須逐child rehash並驗證schedule、ledger
chain、114 config hashes、raw config bytes、occurrence association與上述identities。
完整frame中任一缺失、漂移、無法讀取或association不唯一都是
`CHANGES_REQUIRED / not_evaluated`；不得改用report summary或手抄114 rows。

禁止重用下列S10R3 outcome-bearing interpretation：

- `C_greedy=K=19`與其selected membership/order；
- mapping attempts、slot-5 stopping point、failure signature或terminal decision；
- native、GPU、correctness、noise的缺席或任何diagnostic result；
- S10R3 verifier verdict或formal report作S10R4 PASS evidence。

S10R4不新增draw、不resume discovery、不啟動conditional stream，也不改S10R3 raw tree。

## 3. Frozen identities 與 exact-frame registry

Future contract/effective lock至少綁定：

- Ductile pin `5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39`；
- GEKO pin `d32abacfd13579d1f523f035b7a10b0734c4ac47`；
- actual YAML SHA-256
  `faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36`；
- S10R3 G3 effective lock、candidate registry、support classification及decision raw
  SHA-256；decision只證明immutable predecessor state，不提供S10R4 result；
- S10R3 complete raw-frame root的ordinary-file inventory、relative path、size、mode及
  SHA-256 Merkle/manifest digest；
- 114 rows依`(stream_rank, conditional_priority_rank, chunk_index, draw_index,
  config_hash)`排列的exact-frame registry與registry SHA-256；
- 114 distinct canonical config hashes，且occurrence count與distinct count都exact 114；
- candidate registry、sizes、source blobs、normal workflow entrypoint、KernelWriter及
  error-tolerant removal semantics的exact path/blob hashes；
- host/container mount mapping、Python/toolchain/ROCm identity及所有argv/env allowlist；
- outcome-artifact absence、Plan-B、implementation hashes與exact whitelists。

S10R4不得把S10R3 terminal decision內的reported counts當作完整性證明。Registry builder
必須直接replay/verify raw frame。生成registry是label-blind precondition；其內容不含
S10R4 codegen結果。

## 4. Normal-workflow codegen census

### 4.1 Operational semantics

Pinned normal Ductile benchmark workflow會把validator accepted solutions傳入
`BenchmarkProblems.writeBenchmarkFiles`／`writeSolutionsAndKernels(...,
errorTolerant=True)`；KernelWriter失敗的solutions會被移出後續operational pool。
S10R4必須呼叫與該workflow semantics-equivalent、由future contract綁定的actual native
path。不得以mock、static resource formula或`valid_fn`再次呼叫取代KernelWriter。

### 4.2 兩次完整、隔離、無early-stop的passes

對114個configs各執行Pass A與fresh Pass B：

- 每pass都按exact-frame registry order處理全部114 configs；
- 每config使用獨立cwd/output root，輸入只含該config及pinned generation context；
- 每pass共114個terminal child records，兩pass合計228；
- ordinary nonzero process result及normal error-tolerant removal不是harness exception；
- 不得在已知fail/success後early stop、replacement、reorder、第三次retry或只跑selected
  configs；
- interruption只在完成一個config child後resume；partial child必須fail closed並由
  auditor決定contract-preserving cleanup/replay，不得覆寫成completed；
- 首3個terminal classifications後重估runtime/storage並notify，不能依結果改workload。

每個config只可分類為：

| A/B結果 | 分類 | 後續 |
| --- | --- | --- |
| 兩次都完整產生contract要求的全部kernel artifacts | `operational_codegen_witnessed` | 進survivor pool |
| 兩次都是ordinary normal-filter attrition，且signature/schema皆合法 | `stable_operational_attrition` | 留在exact-frame denominator，不進survivor pool |
| success/fail discordance、exception、timeout、signal、missing/partial child、association/path/toolchain drift或未知result | `CHANGES_REQUIRED / not_evaluated` | fail closed；不是scientific outcome |

Pass B開始前Pass A必須114/114 terminal complete。分類seal必須保存每個config的兩份
child digests、stdout/stderr/artifact inventory、return semantics與final class。Stable
attrition不得被稱為invalid、support absent或validator defect。

## 5. Operational atoms 與 bounded exact-K selection

對每個stable survivor，以fresh replay的candidate registry計算其atom coverage：

```text
operational_codegen_witnessed_atoms
  = union(atoms(config) for config in stable_survivors)

mandatory_mapping_atoms
  = prelocked_candidate_atoms ∩ operational_codegen_witnessed_atoms
```

所有stable attrition configs保留在exact-frame denominator與attrition table，但不提供
mandatory atom witness。不得看到census後人工刪/加atom。

Selector固定為S10R3已定義語意的deterministic greedy set cover，唯inputs換成stable
survivors與上述mandatory set：

1. gain最大的survivor優先；
2. tie依exact-frame first-occurrence order，再依config hash；
3. full cover筆數為`C_greedy`；
4. `K=max(10,C_greedy)`，`K_max=20`；
5. `C_greedy<10`時依first-occurrence order從其餘survivors補到10；
6. final K按config hash排序。

少於10個stable survivors、mandatory set無法cover或`C_greedy>20`，在complete census
成立時是本exact-frame hypothesis的
`negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`。這只說明exact frame
不能形成prelocked fixture；不宣稱完整search space沒有其他survivor/cover。

不得使用S10R3 K=19 membership、replacement、K+1、redraw、conditional extension、
exact solver或看到結果後改cap。

## 6. Fresh mapping 與 native conformance

Final K configs ×三sizes形成每pass exact `3K` rows。Fresh mapping Pass A/B均須全數
成功並在raw config、resolved solution、canonical hash、SizeMapping/Formocast input及
field provenance逐row一致。不得猜required field、proxy、replacement或忽略failure。

因codegen census已證明每個selected config 2/2全-kernel success，後續出現ordinary
mapping/codegen failure時：

- 兩次fresh完整reproduction為相同合法signature，且identity/harness完整：
  `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`；
- failure/success discordance、未知signature、partial/timeout/path drift或harness問題：
  `CHANGES_REQUIRED / not_evaluated`。

Score-blind deterministic native fixture、Formocast predictedPerformance path、guard
order、mapping/runtime helper及runtime checkSolution/queue adapter要求完整沿用S10R3
scientific semantics，但所有S10R4 evidence與bindings必須fresh。Independent oracle只
比較，不取代native path；helper/adapter/source/hash/guard/queue substitution tests均須
fail closed。

## 7. GPU correctness 與 noise

所有GPU/ROCm probe、generation、compile、smoke、correctness與noise只能在既有
`perlee` container內執行。依prelocked rule查看各卡目前資源，直接使用一張free且符合
gfx942 identity的card；不需預約，不宣稱exclusivity。不得start/stop/recreate container
或install dependency。

Final K sorted hashes的anchors固定：

```text
{0, floor((K-1)/2), K-1}
```

- 3 anchors ×3 sizes = 9 generate/compile/smoke/nonzero correctness cells；
- 全部correctness通過後才執行3×3×7 = 63 noise cells；
- `CV P95 <= 0.5%`、parent `delta_noise`及`reduce_fn=max`不變；
- 不得replacement anchor、縮panel或丟棄不利cell。

完整且可重現的correctness failure為
`negative / S1_ENTRY_BLOCKED / FT-BLOCKED-CORRECTNESS / edge=null`。63-cell完整但noise
不穩定為`inconclusive / FT-INCONCLUSIVE / edge=null`。Harness、identity、GPU
association、partial/timeout或resume defect仍是`CHANGES_REQUIRED / not_evaluated`。

## 8. Outcome matrix 與唯一edge

| Frozen terminal condition | Scientific result | Edge |
| --- | --- | --- |
| Exact frame完整；228 census children穩定分類；`10<=K<=20` full cover；mapping A/B、native conformance、9 correctness及63 noise cells全PASS | `positive / S1_ENTRY_GO_EXACT_FRAME` | `S10R4:S1_ENTRY_GO_EXACT_FRAME -> S11` |
| Complete census後stable survivors不足10、無法cover或`C_greedy>20`；或fresh reproducible mapping failure | `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING` | `null` |
| Fresh reproducible generate/compile/smoke/nonzero correctness failure | `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-CORRECTNESS` | `null` |
| 完整63-cell noise不穩定 | `inconclusive / FT-INCONCLUSIVE` | `null` |
| Frame、implementation、schema、association、path、toolchain、timeout、discordance、partial evidence或lineage defect | `CHANGES_REQUIRED / not_evaluated` | `null` |

Positive、negative與inconclusive都需fresh verifier、terminal report、exact-path local
commit與post-commit audit。`CHANGES_REQUIRED`不是scientific report。S11只接受
post-audited qualified edge token；generic/historical `S1_ENTRY_GO`不得代用。

## 9. S11 consumer boundary

S10R4 positive只把exact-K fixture、source/YAML identity、mapping/native/correctness/noise
entry readiness交給S11。它不能替代S11自己的formal population。

S11必須以其預鎖fresh/disjoint seeds建立multiplicity-preserving
`F_valid` accepted-occurrence frame，然後對完整frame執行與S10R4同一normal
KernelWriter filter，得到`F_codegen`：

- 每個validator-accepted occurrence（包括codegen reject）留在`F_valid` denominator；
- 只對`F_codegen` survivors做mapping與Formocast scoring；
- whole-config Formocast coverage仍以完整`F_valid` occurrence mass為分母，門檻仍
  `>=95%`；codegen attrition不能從分母刪除或改報survivor-only coverage；
- conditional streams只進各自cell，不得pool進global denominator；
- whole-gene fail-closed eligibility保持不變；value-level guidance proposal延後，不在
  S10R4/S11 entry amendment採用；
- S10R4 114-row frame、survival rate或selected membership不得用來滿足S11 fresh
  4,096/8,192 accepted-occurrence、128/256 conditional support或model-only criteria。

## 10. Execution governance、resources 與 stop conditions

S10R4是R3。Main依current `implement-verify-loop`建立Plan-B再Plan-A；一位fresh
adversarial auditor在outcomes前審查authority/contract/Plan-B；一位fresh implementer
只讀Plan-A與必要frozen constraints；一位未參與實作的fresh verifier只讀
contract/lock/Plan-B/direct evidence。Main不實作source，也不兼任fresh verifier。

Repair count只作append-only provenance，不是numeric stop cap。Contract-preserving修復
依reviewer結果持續；只有新實驗結果迫使measurement、claim、scientific authority或
方向改變，才另走`design-discussion`並交使用者決定。

Initial planning target：

```text
wall_s:                    21600
cpu_s:                     86400
gpu_s:                      3600
new_transient_storage: 2147483648 bytes
```

Historical Stage-1 usage照實保留但不單獨阻止successor。前3/228 census children、2×
projected cost或internal target crossing時record＋notify並繼續；只有unsafe continuation、
實際資源/平台不可用、完整frozen workload/verification/closure無法完成、optional
stopping風險、evidence不可驗證、需要改scientific workload/claim或外部不可逆權限時才在
safe child/cell boundary暫停。

## 11. Design-consensus record

- Reviewer A（`/root/pipeline_rebaseline_reviewer_a`）與Reviewer B
  （`/root/pipeline_rebaseline_reviewer_b`）先獨立分析normal Ductile workflow及S10R3
  evidence，再完成兩輪cross-examination與一輪evidence-backed final。
- 兩方同意：validator accepted與KernelWriter operational survival是不同層級；normal
  workflow確實會把accepted solutions交給error-tolerant codegen並移除failures。
- 兩方同意：不能重開/重標S10R3，也不能用第一個known failure挑選方便的survivors；必須
  對完整sealed 114-config frame做兩次無early-stop census。
- 兩方同意：stable attrition保留在denominator，mapping mandatory atoms只從stable
  survivors機械計算；`K=max(10,C_greedy)`與`K_max=20`保持。
- 兩方同意：S11必須建立fresh `F_valid -> F_codegen` frame，global coverage denominator
  不得因codegen failure縮水；whole-gene fail-closed仍保留，value-level proposal延後。
- Reviewer A final：`AGREE`。
- Reviewer B final：`AGREE`。
- 使用者已選擇並核准exact-frame S10R4方向，且要求依plan完整實作；不授權push。
