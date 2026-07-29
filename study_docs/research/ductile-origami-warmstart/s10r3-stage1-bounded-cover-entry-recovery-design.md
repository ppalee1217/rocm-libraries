---
checkpoint_id: S10R3
title: Stage 1 bounded-cover entry recovery
stage: 1
design_status: approved
execution_status: not_started
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R3
governance_baseline: d0d6fb11c5e000a90acc03567e2339bd506fefbe
scientific_gate: S10R3
execution_tranche: T-S10R3
closure_unit: CU-S10R3
hypothesis_id: S10R3-H1
dependencies:
  - checkpoint_id: S00
    required_edge: S00_EVIDENCE_READY
  - checkpoint_id: S10
    required_terminal: CHECKPOINT_COMPLETE_negative
  - checkpoint_id: S10R1
    required_operational_state: cancelled_not_evaluated_edge_null_under_A32
  - checkpoint_id: S10R2
    required_terminal: CHECKPOINT_COMPLETE_inconclusive_edge_null
entry_criteria:
  - committed_A38_S10R3_authority_amendment
  - exact_S10_source_and_actual_YAML_identity
  - no_S10R1_or_S10R2_empirical_reuse
  - durable_S10R3_contract_and_effective_lock_before_labels
criterion_refs:
  - S1_ENTRY_GO
  - S1_ENTRY_BLOCKED
failure_ids:
  - FT-BLOCKED-MAPPING
  - FT-BLOCKED-CORRECTNESS
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S1_ENTRY_GO
    target_checkpoint: S11
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s10r3-s1-entry-go.json
formal_report_path: reports/staged/s10r3-stage1-bounded-cover-entry-report.md
terminal_report_integration: standalone_report_integrates_s10r3_gate_record
blocker_path: null
future_frozen_contract_path: protocol/v1/s10r3-stage1-bounded-cover-entry-contract.yaml
future_effective_lock_path: protocol/v1/locks/s10r3-stage1-bounded-cover-entry-lock.json
future_artifact_paths:
  - protocol/v1/manifests/s10r3-candidate-atom-registry.json
  - protocol/v1/manifests/s10r3-support-classification.json
  - protocol/v1/manifests/s10r3-mapping-corpus.json
  - protocol/v1/manifests/s10r3-sentinel-conformance.json
  - protocol/v1/manifests/s10r3-size-registry.json
  - protocol/v1/evidence/s10r3-smoke-correctness.json
  - protocol/v1/evidence/s10r3-noise-pilot.json
  - protocol/v1/evidence/s10r3-decision.json
implementation_boundary_max:
  - protocol/v1/run_s10r3_entry.py
  - protocol/v1/s10r3/**
  - protocol/v1/s10r3-stage1-bounded-cover-entry-contract.yaml
  - protocol/v1/schemas/s10r3-entry.schema.json
  - protocol/v1/locks/s10r3-stage1-bounded-cover-entry-lock.json
  - protocol/v1/manifests/s10r3-*.json
  - protocol/v1/evidence/s10r3-*.json
  - protocol/v1/evidence/gate-records/s10r3-s1-entry-go.json
  - projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10r3_entry.py
delivery_boundary_max:
  - S10R3 implementation and tests selected by future exact-path planning
  - protocol/v1 S10R3-only contract, schema, lock, manifests, evidence, and gate record
  - projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10r3_entry.py
  - reports/staged/s10r3-stage1-bounded-cover-entry-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - ../surrogate-dse-plan.md
  - README.md
  - s10r3-stage1-bounded-cover-entry-recovery-design.md
  - s11-stage1-model-only-factorization-design.md
forbidden_evidence_reuse:
  - every S10R1 generation-0 or generation-1 artifact
  - S10R2 accepted rows, support states, activated targets, cover membership, seeds, decision, mapping, correctness, noise, and verifier outcome
forbidden_downstream_roots:
  - reports/staged/s11-stage1-model-only-factorization-report.md
  - reports/staged/s12-stage1-real-score-audit-report.md
  - reports/gen0-factorization-mvp-report.md
  - reports/short-horizon-persistence-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
---

# S10R3 — Stage 1 bounded-cover entry recovery

導航：[active checkpoint index](README.md)｜[experiment plan §2](../ductile-origami-warmstart-experiment-plan.md#2-d1d2-entry-gate)｜[S10R2 terminal report](reports/staged/s10r2-stage1-support-aware-entry-report.md)

## 1. 白話目標與 claim boundary

S10R2已證明固定十筆的mapping corpus不足以覆蓋該次fresh run觀察到的mandatory
valid-support atoms；它因此依原contract正確結束為inconclusive。S10R3不改寫這個
結果，也不刪除mandatory atoms。它重新做一份完全fresh的support discovery，然後用
事前固定的deterministic greedy selector決定需要多少筆mapping configs：

```text
C_greedy = frozen greedy selector建立full cover所用的configs數
K        = max(10, C_greedy)
K_max    = 20
```

只有`K <= 20`且所有mapping、native helper conformance、correctness與noise criteria
都通過，S10R3才可產生`S1_ENTRY_GO`。`C_greedy`不是數學上的minimum cover；
S10R3不宣稱找到最小解。

**S10R3-H1：**在保留S10 actual source/YAML identity、groups、candidate order、
weights、三個sizes、validity、correctness與noise要求時，fresh operational valid
support可由事前有界、可重現且最多20筆的greedy mapping corpus完整覆蓋，並建立可信的
Stage-1 entry boundary。

S10R3只回答entry mapping與measurement boundary是否完整。它不回答Formocast ranking、
factorization、prior mass、Gen0或production readiness，也不證明未觀察candidate不存在。

## 2. Immutable lineage 與 A38 cutover

下列歷史狀態全部immutable：

- S10：`CHECKPOINT_COMPLETE / negative / S1_ENTRY_BLOCKED /
  FT-BLOCKED-MAPPING / edge=null`；
- S10R1：A32固定為
  `cancelled / BLOCKED / not_evaluated / edge=null / lock superseded`；
- S10R2：`CHECKPOINT_COMPLETE / inconclusive / FT-INCONCLUSIVE / edge=null`。

S10R2的`448 chunks / 229,376 draws / 156 fresh distinct valid configs /
90 witnessed mandatory atoms / C_greedy=18`只可說明A38為何建立`K_max=20`。它是
post-label design diagnostic，不是S10R3 formal evidence、expected result、coverage
guarantee或可重用row。

S10R3是新的`R3` scientific gate、standalone
`execution_tranche=T-S10R3`與`closure_unit=CU-S10R3`。只有post-audited
`S10R3:S1_ENTRY_GO -> S11`存在；S10、S10R1與S10R2都沒有可轉移edge。

### 2.1 Fresh-evidence boundary

S10R3在第一筆draw前必須建立：

- fresh candidate-atom registry與registry hash；
- 與S10R1／S10R2 disjoint的seed namespace；
- fresh append-only ledger與new run identity；
- fresh support classification、mapping corpus、helper conformance、GPU correctness、
  noise、decision、reproduction與verification evidence。

禁止讀取、匯入或複製S10R1 empirical／repair artifacts，以及S10R2 accepted rows、
support status、activated conditional targets、cover membership、seed values、mapping
results、GPU/noise results或decision來形成S10R3 gate evidence。S10R2 report與identities
只作authority/provenance input。

Pure、semantics-identical helper source只有在future frozen contract逐一綁定exact
source path/blob/SHA-256、證明不讀S10R1/S10R2 artifact state、由S10R3 tests獨立重驗，
且pre-label auditor接受時才可重用。Support selection、bounded-K decision與S10R3
evidence writer必須是S10R3-scoped implementation。

## 3. Frozen actual identity

Future contract必須fresh驗證並綁定：

- Ductile：`refs/remotes/origin/ductile_integration` at
  `5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39`；
- GEKO：`refs/remotes/origin/users/pkamd/geko_pr` at
  `d32abacfd13579d1f523f035b7a10b0734c4ac47`；
- actual YAML SHA-256：
  `faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36`；
- 30個ordered axes與candidate-order SHA-256
  `926a6d9502546dda22ea2edc483c0f61ef74b3e378bcf32f222f17130bb668a3`；
- expanded groups SHA-256
  `0526a9b3c1d8a1bbe1db2cb03616bfda6e5a1f2dfad3826c0747d8dcb3ab9140`，
  cardinalities `9,918 / 3 / 2`；
- search-space map SHA-256
  `5785871bc0779fb67627943ef2ed5fde8e96647be7e0bb0db4f770473cd7a1a0`；
- baseline weights SHA-256
  `56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f`，
  `group_0`的9,918 positional weights與`weight_beta=0.25`；
- dtype/layout：batched `B/B/S`, `NN`；`soo=false`；
  resolved `reduce_fn=max`；`n_elements_to_validate=128`；
- sizes依`[M,N,batch,K]`固定為
  `[8,8,1,128]`、`[256,256,1,1024]`、`[2304,1024,1,214336]`。

任一identity drift都必須在labels前停止，做bounded label-blind reconciliation或另行
authority amendment；不得偷偷升級pin、重生YAML、改groups/order/weights/sizes或用
retired capsule補值。

## 4. Pre-draw registry 與三態support

第一筆draw前，L0必須seal完整candidate-atom registry。Registry沿用S10R2已核准的
typed-value、axis/value ID、YAML pointer、source symbol/blob、role flags與priority
語意，但必須由current authoritative bytes fresh重建並使用S10R3 identity。

`prelocked_candidate_atoms`固定為每個
`ungrouped && currently_unweighted && frozen_free && cardinality>1` residual axis的
全部candidate rows。`conditional_diagnostic_atoms`固定為：

1. 全部`prelocked_candidate_atoms`；
2. 每axis的first／last candidate rows；
3. exact typed integer `-2`或`-1` rows。

Conditional priority仍固定為：

```text
(
  sentinel_rank,
  axis_scope_rank,
  boundary_rank,
  axis_index,
  value_index,
  atom_id
)
```

每個candidate value只能分類為：

- `supported_witnessed`：fresh S10R3 ledger至少一個完整accepted config包含該value；
- `support_unobserved`：fixed stochastic schedule沒有fresh witness，且無complete proof；
- `support_proven_absent`：finite exhaustive、sound constraint或獨立驗證的等價complete
  proof證明不存在accepted config。

`stochastic zero -> support_proven_absent`永遠禁止。Residual gene只要任何value不是
`supported_witnessed`，整個gene就不具S11 guidance eligibility；actual YAML baseline
semantics保持不變，且不阻止其他support-complete genes或S10R3 entry。

## 5. Fixed fresh discovery schedule

- Chunk size固定`512` nominal draws。
- Global stream固定完整`32 chunks / 16,384 draws`，不得early stop。
- Global完成後，才從sealed registry中對仍`support_unobserved`的diagnostic atoms依
  prelocked priority機械取最多15個conditional targets。
- 每個activated conditional固定完整
  `32 chunks / 16,384 draws`，不得early stop或extension。
- 總上限固定`512 chunks / 262,144 draws`。
- 不得因support、cover、Formocast、GFLOPS或希望形成GO而改priority、target、seed、
  chunk、cap或stream order。
- 不得seed retry、target replacement、old-row reuse、successor extension或重抽已完成
  chunk。
- Interrupted run只能由same sealed contract與append-only ledger在atomic chunk
  boundary補完尚未完成的chunks。

這些draw／chunk／stream上限是scientific execution caps，不受A37 resource-planning
放寬影響。

## 6. Mandatory atoms 與 bounded exact-K selector

Fresh discovery完成後：

```text
mandatory_mapping_atoms
= prelocked_candidate_atoms ∩ supported_witnessed
```

本版`always_required_structural_atoms=[]`。不得在看到support後人工刪除、添加或重分類
mandatory atoms。

Selector固定為`deterministic_greedy_set_cover_v2_bounded_k20`：

1. 每個fresh accepted config的coverage是其包含的mandatory atom IDs；
2. First-occurrence order固定為
   `(stream_rank, conditional_priority_rank, chunk_index, draw_index, config_hash)`；
3. 每輪選擇對remaining mandatory atoms gain最大的config；
4. Tie依first-occurrence order，再依config hash；
5. Full cover所用筆數記為`C_greedy`；
6. `K=max(10,C_greedy)`，`K_max=20`；
7. `C_greedy<10`時依同一first-occurrence order從其餘fresh distinct witnesses補到
   exact ten；
8. Final K configs按config hash排序。

下列任一成立即
`inconclusive / FT-INCONCLUSIVE / edge=null`：

- fresh distinct valid witnesses少於10；
- greedy無法cover全部mandatory atoms；
- `C_greedy > 20`。

看到fresh labels後不得新增exact solver、增加draws、重試seeds、改selector、
提高`K_max`或改mandatory set。`C_greedy`不得稱作minimum cover。

### 6.1 Non-gating lower-bound audit

可機械計算：

```text
L_axis = max(
  一個residual axis上fresh witnessed mandatory values的數量
)
```

一個config在同一axis最多覆蓋一個value，所以`L_axis>20`可證明任何cover都超過cap。
若`L_axis<=20`而greedy超過20，report必須明寫：global minimum-cover feasibility沒有
被評估，未排除存在另一個20筆以內cover。此audit不改selector或outcome matrix。

## 7. Mapping 與native helper conformance

### 7.1 Mapping A/B

Final K configs ×三sizes形成每pass恰好`3K` rows：

- Pass A必須`3K/3K`成功；
- fresh Pass B必須`3K/3K`成功；
- `K=20`時是每pass60 rows、combined 120 rows；
- raw config、resolved solution、canonical hash、`SizeMapping`／Formocast input與全部
  required field provenance在A/B一致；
- guessed field、unresolved field、mapping failure、row replacement、proxy或第K+1筆
  全部禁止。

### 7.2 Score-blind native conformance

Mapping corpus不需要碰巧命中sentinel。獨立、prelocked、score-blind deterministic
fixture必須呼叫並綁定同一native path：

- `origami::Formocast::predictedPerformance() const`；
- pinned source guard order；
- mapping/runtime interpretation使用的helper；
- `SolutionIterator::checkSolution`與`AllSolutionsIterator::preProblem` queue path；
- exact source/blob/helper binary/host adapter hashes、build toolchain與argv。

Early-terminate pair、guard first-true order、stable sort、ties、threshold index/value與
queue prefix語意完全沿用S10R2 approved design。Separate oracle只能比較，不得取代
native output。Fresh verifier必須fault-inject並證明以下替換全部fail closed：

- native helper/binary/path；
- source/blob/hash或guard order；
- host adapter；
- runtime checkSolution/queue semantics。

Harness、schema、adapter、guard或queue defect是`CHANGES_REQUIRED`，不是scientific
negative。

## 8. GPU correctness、noise 與free-card policy

所有GPU／ROCm probe、generate、compile、smoke、correctness與noise command只能在
existing Docker container `perlee`內執行。不得probe或操作其他container，也不得
start、stop、restart、recreate或install dependency。

每個GPU phase開始時可直接選一張目前free、identity符合frozen gfx942條件的card：

- 不需要reservation，也不宣稱exclusivity；
- 在labels前鎖定card-selection rule、device identity capture、foreign-PID rejection、
  environment identity、atomic cell boundary、interruption outcome與append-only resume；
- 發現foreign workload時不得搶用該card；等待或選另一張符合規則的free eligible
  card；
- interruption只能在safe cell boundary保存已完成cells；不得丟棄不利結果、
  replacement anchor、縮panel或fabricate completion。

Final K sorted hashes的anchors固定為：

```text
{0, floor((K-1)/2), K-1}
```

- 三anchors ×三sizes共9 cells全部完成generate／compile／smoke與nonzero correctness；
- correctness全過後才執行三anchors ×三sizes ×七repeats，共63 noise cells；
- `CV P95 <= 0.5%`、`delta_noise`與`reduce_fn=max`保持parent定義；
- anchor不得replacement。

Locked generate／compile／smoke／nonzero correctness可重現失敗，且harness與identity
完整時，分類為
`negative / S1_ENTRY_BLOCKED / FT-BLOCKED-CORRECTNESS / edge=null`。

## 9. Resource planning 與role governance

A37是prospective floor。Historical known usage與`UNKNOWN` measurement boundaries保留
作provenance，但不debit S10R3 entry，也不把`UNKNOWN`補成0。

Initial planning estimates：

```text
wall_s:                    12669
cpu_s:                     65285
gpu_s:                      2901
transient_storage_bytes: 2147483648
```

它們不是scientific estimand或hard acceptance criterion。Long-running work開始前通知；
首1%、2x或internal planning target crossing時record＋notify並繼續完整frozen workload。
只有A37 material condition才在safe boundary pause：unsafe continuation、external／
platform／allocation限制、實際compute/memory/storage不足、完整workload／verification／
closure／artifact preservation無法完成、label-dependent stopping／selection、required
workload/claim change、evidence不可驗證，或pre-label明確凍結的scientific resource
boundary。

R3 governance固定：

- 兩位已完成A38 design discussion的reviewers；
- Codex adapter要求的兩位fresh independent execution planners；
- 一位fresh adversarial authority auditor，在labels前審查contract；
- Main agent實作，不另開implementer thread；
- 一位未參與實作的fresh verifier；
- 合計`6/6` fresh role threads，沒有pre-authorized replacement；
- R3 repair最多3 rounds；同一finding連續兩輪無material progress即停止。

需要第七個fresh thread或第四個repair round時必須取得新的human authority；不得用
generation、successor、restart或new root重置。

## 10. Contract、seal 與formal evidence order

Future exact planning必須把maximum boundary縮成exact implementation/delivery
whitelists。任何outcome label前：

1. 建立durable machine-readable frozen contract；
2. 綁定authorities、criteria、outcome matrix、fresh seed namespace、registry、
   selector、fixtures、implementation hashes、resource semantics與whitelists；
3. 由fresh adversarial auditor取得`AUDIT_PASS`；
4. 以tracked commit或approved immutable mechanism seal contract與effective lock；
5. post-seal audit確認outcome artifacts仍不存在、hash與authority parity正確。

之後formal order固定：

1. CPU support discovery；
2. support classification seal；
3. bounded exact-K selection；
4. mapping A/B；
5. native sentinel/runtime conformance；
6. GPU environment identity；
7. smoke/correctness；
8. noise；
9. decision；
10. independent reproduction與fresh verification。

任何gate不通過立即依frozen outcome matrix停止；不得先執行後段補資料。

## 11. Outcome matrix 與唯一edge

| Evidence state | Classification | Report／repair | Edge |
| --- | --- | --- | --- |
| 全部criteria與closeout通過 | `positive / S1_ENTRY_GO` | S10R3 report＋compact gate record | `S11` |
| Valid bounded-K存在，但required mapping／field provenance可重現失敗 | `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING` | S10R3 terminal report | `null` |
| Locked generate／compile／smoke／nonzero correctness可重現失敗 | `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-CORRECTNESS` | S10R3 terminal report | `null` |
| 少於10 fresh witnesses、greedy cover不可行／超過20，或63-cell noise不穩定 | `inconclusive / FT-INCONCLUSIVE` | S10R3 terminal report | `null` |
| Harness／schema／API／guard／queue／lineage實作缺陷 | `CHANGES_REQUIRED / not_evaluated` | R3 budget內修復並重驗 | `null` |
| A37 material operational condition成立 | operational `BLOCKED / not_evaluated` | safe-boundary decision packet | `null` |

只有post-audited positive可以產生
`protocol/v1/evidence/gate-records/s10r3-s1-entry-go.json`並啟動S11。Partial evidence、
diagnostic、proxy、two-size、old result或helper-only PASS都沒有edge。

## 12. Formal report、closeout 與 approval record

唯一formal report：

`reports/staged/s10r3-stage1-bounded-cover-entry-report.md`

Positive、negative與inconclusive都要self-contained terminal report、fresh verifier
technical verdict、parent/index projection、`CLOSEOUT_ACK`、exact-path closure commit與
post-commit audit。`CHANGES_REQUIRED`不是scientific report；operational BLOCKED只依
future contract的terminalization policy處理。

A38 design discussion使用兩位fresh `gpt-5.6-sol / xhigh` reviewers，完成兩輪
cross-examination與一輪evidence-backed final。兩方對scientific bounded-K package
一致，只在planner count、resource projection與GPU availability authority保留dissent。
使用者於2026-07-29以「全部核准」核准完整package：

- Codex adapter的two-planner配置與R3 `6/6` thread boundary；
- A37的record＋notify resource semantics；
- 只在existing `perlee`內使用目前free eligible gfx942、不需reservation；
- 本五路徑authority amendment、其exact-path local commit及後續
  `implement-verify-loop`；
- 明確不授權push。

本核准建立合法研究路徑，不保證S10R3 positive，也不預先啟動S11。
