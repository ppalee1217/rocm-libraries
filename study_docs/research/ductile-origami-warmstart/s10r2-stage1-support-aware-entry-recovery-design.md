---
checkpoint_id: S10R2
title: Stage 1 support-aware entry recovery
stage: 1
design_status: approved
execution_status: not_started
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R2
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S10R2
execution_tranche: T-S10R2
closure_unit: CU-S10R2
hypothesis_id: S10R2-H1
dependencies:
  - checkpoint_id: S00
    required_edge: S00_EVIDENCE_READY
  - checkpoint_id: S10
    required_terminal: CHECKPOINT_COMPLETE_negative_at_48c26297fc6815e6edfcc89b8503e47370fedc53
  - checkpoint_id: S10R1
    required_operational_state: cancelled_not_evaluated_edge_null_under_A32
entry_criteria:
  - committed_S10R2_authority_amendment
  - exact_S10_source_and_actual_YAML_identity
  - cumulative_resource_preflight_pass
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
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s10r2-s1-entry-go.json
formal_report_path: reports/staged/s10r2-stage1-support-aware-entry-report.md
terminal_report_integration: standalone_report_integrates_s10r2_gate_record
blocker_path: null
future_frozen_contract_path: protocol/v1/s10r2-stage1-support-aware-entry-contract.yaml
future_effective_lock_path: protocol/v1/locks/s10r2-stage1-support-aware-entry-lock.json
future_artifact_paths:
  - protocol/v1/manifests/s10r2-candidate-atom-registry.json
  - protocol/v1/manifests/s10r2-support-classification.json
  - protocol/v1/manifests/s10r2-mapping-corpus.json
  - protocol/v1/manifests/s10r2-sentinel-conformance.json
  - protocol/v1/manifests/s10r2-size-registry.json
  - protocol/v1/evidence/s10r2-smoke-correctness.json
  - protocol/v1/evidence/s10r2-noise-pilot.json
  - protocol/v1/evidence/s10r2-decision.json
implementation_boundary_max:
  - S10R2-only contract, support discovery, mapping, helper conformance, correctness, noise, decision, and tests
  - protocol/v1 schemas, manifests, lock entries, evidence, and gate record required only by S10R2
delivery_boundary_max:
  - S10R2 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/staged/s10r2-stage1-support-aware-entry-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - ../surrogate-dse-plan.md
  - README.md
  - s10r1-stage1-valid-support-entry-recovery-design.md
  - s10r2-stage1-support-aware-entry-recovery-design.md
  - s11-stage1-model-only-factorization-design.md
forbidden_evidence_reuse:
  - every S10R1 generation-0 or generation-1 empirical, repair, cache, test, lock, selection, mapping, and verification artifact
forbidden_downstream_roots:
  - reports/staged/s11-stage1-model-only-factorization-report.md
  - reports/staged/s12-stage1-real-score-audit-report.md
  - reports/gen0-factorization-mvp-report.md
  - reports/short-horizon-persistence-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
---

# S10R2 — Stage 1 support-aware entry recovery

導航：[active checkpoint index](README.md)｜[experiment plan §2](../ductile-origami-warmstart-experiment-plan.md#2-d1d2-entry-gate)｜[historical S10 report](reports/staged/s10-stage1-entry-gate-report.md)

## 1. 白話目標與 claim boundary

S10R2先問「actual Ductile validator真正接受哪些值」，再建立mapping corpus。它不要求
隨機抽樣命中每個YAML名義邊界，也不把抽不到誤寫成不存在。只有CPU validity-only
discovery、exact-ten mapping、獨立sentinel helper conformance、correctness與noise全部
通過，才可進S11。

**S10R2-H1：**在完全保留S10的source pins、actual YAML、groups、candidate order、
weights、三個sizes、correctness與noise要求時，可在**觀察到的operational valid
support**內建立可重現的entry boundary。

S10R2只支持「在本次觀察到的operational valid support內，mapping與measurement
entry完整」。它不證明未觀察值不存在，不回答Formocast ranking、factorization、
prior mass或Gen0效果，也不支持proxy、two-size或workload downgrade。

## 2. A32 cutover與治理單位

S10R1 append-only governance chain的user-authorized `A32` event是本cutover的live
basis：S10R1已在safe boundary停止，operational state為
`execution_status=cancelled / checkpoint_state=BLOCKED`，scientific outcome是
`not_evaluated`、edge是`null`，且不是`CHECKPOINT_COMPLETE`。S10R1 generation 0／1
只保留為immutable diagnostic provenance；其non-discovery不是scientific
inconclusive，且任何artifact都禁止成為S10R2 gate evidence。

S10R2是`risk_tier=R2`、獨立`execution_tranche=T-S10R2`與
`closure_unit=CU-S10R2`。執行治理以commit
`b0561d2c9216a58a9d71b8e839c47efaa51f9c00`為floor：

- outcome evidence前必須先把本design抽成durable machine-readable frozen contract，
  驗證human/machine parity，再seal tracked effective lock；
- wall-time、CPU/GPU time、storage、throughput samples、pre-empirical engineering、
  repair rounds與fresh role threads都按同一Stage-1 lineage累計；generation、
  successor、sibling checkpoint、replacement role、process restart或new root都不能歸零；
- R2最多3個repair rounds、5個fresh role threads；pre-empirical engineering最多使用
  Stage-1 hard cap的20%；首1% planned throughput後重估wall-time與storage；
- projected cost超過原估2倍、任一frozen resource cap超限，或預設5 GiB transient
  storage不足時，必須safe-boundary pause並提交decision packet；本design不授權reset；
- `live_run_state`可記working-tree／partial進度；`committed_projection_state`只有在
  closure commit與post-commit audit後才可更新。

Stage 1仍是最多七個hands-on工作日的hard cap，不是完成承諾。Entry preflight必須
先帶入S10R1及同lineage既有消耗，證明剩餘budget足以完成S10R2、S11–S13所需的
dependency-ready工作與report buffer；不足時停止，不靠縮criteria救回。

## 3. Frozen actual-S10 identity

Future contract必須逐項重驗並綁定下列controlled inputs：

- Ductile：`refs/remotes/origin/ductile_integration` at
  `5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39`；
- GEKO：`refs/remotes/origin/users/pkamd/geko_pr` at
  `d32abacfd13579d1f523f035b7a10b0734c4ac47`；
- actual YAML SHA-256：
  `faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36`；
- 30個ordered axes；candidate-order SHA-256
  `926a6d9502546dda22ea2edc483c0f61ef74b3e378bcf32f222f17130bb668a3`；
- expanded groups SHA-256
  `0526a9b3c1d8a1bbe1db2cb03616bfda6e5a1f2dfad3826c0747d8dcb3ab9140`，
  cardinalities固定為`9,918 / 3 / 2`；
- search-space map SHA-256
  `5785871bc0779fb67627943ef2ed5fde8e96647be7e0bb0db4f770473cd7a1a0`；
- baseline weights SHA-256
  `56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f`：
  只有`group_0`有9,918個positional weights，`weight_beta=0.25`；
- dtype/layout為batched `B/B/S`, `NN`；`soo=false`、resolved `reduce_fn=max`、
  `n_elements_to_validate=128`；
- 三個same-space sizes依`[M,N,batch,K]`固定為
  `[8,8,1,128]`、`[256,256,1,1024]`、`[2304,1024,1,214336]`。

任一identity不符都在evidence前停止並另行amend；不得偷偷升級pin、重生不同YAML、
改group/order/weights/size或從S10R1 capsule補值。

## 4. Pre-Formocast CPU validity-only support discovery

### 4.1 三態分類

在任何Formocast call、GFLOPS、GPU smoke或noise前，以actual float32 GA
probabilities、同一candidate order與pinned `valid_fn`建立ledger。每個candidate
value必須得到且只能得到一個狀態：

- `supported_witnessed`：ledger中至少一個包含該value的完整config被同一validator
  接受，並保存raw indices、resolved config、occurrence ID與validity provenance；
- `support_unobserved`：在預註冊cap內沒有accepted witness，且沒有complete proof；
- `support_proven_absent`：finite exhaustive enumeration、sound constraint proof或
  獨立驗證的等價complete proof證明不存在任何accepted config。

Stochastic non-discovery永遠只能是`support_unobserved`；draw count、seed數或多個
successor都不能把它升格為`support_proven_absent`或scientific inconclusive。

對一個future residual gene，只要任一candidate value是`support_unobserved`或
`support_proven_absent`，整個gene就不得在S11作guidance gene；actual YAML baseline
group／weight／uniform semantics仍原封不動。這不阻止其他support完整的gene，也不
阻止S10R2 entry。Grouped axes永遠保持baseline，不因本分類拆成residual genes。

### 4.2 Complete L0 pre-draw candidate atom registry

L0必須在第一個draw前materialize、validate、hash並seal完整
`protocol/v1/manifests/s10r2-candidate-atom-registry.json`。Registry對30個ordered
axes的**每一個candidate value**
各有一row；grouped axis的value是完整expanded group candidate object，不拆成事後
挑選的field atoms。

每row固定包含：

- `axis_id = "axis/a{axis_index:02d}/{axis_name}"`；
- `atom_id = "cand/a{axis_index:02d}/v{value_index:05d}/{value_sha256[0:16]}"`；
- `axis_index`、`axis_name`、`value_index`、candidate count、grouped／ungrouped、
  free／fixed、currently-weighted／unweighted；
- exact typed value及其S00 canonical-JSON bytes／SHA-256；bool、int、float、string、
  list與object不可互相coerce；
- actual YAML source path
  `protocol/v1/inputs/s10-generated.yaml`、Git blob
  `1fd6fb401d5baebd4665a87e9002687fb725b2dc`、raw SHA-256
  `faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36`
  及exact parsed YAML/JSON pointer；
- pinned candidate-construction source
  `projects/hipblaslt/tensilelite/Tensile/BenchmarkStructs.py` blob
  `4968b29b5eacddc56b20c42cb4b2c1e3d8d6f406`；ungrouped row的
  `source_symbols`固定為`BenchmarkProcess.__init__`與
  `constructLazyForkPermutations`；
- 若為expanded group，`source_symbols`另固定包含
  `_groupedParameterValueOptions`、`_expandGroupedParameters`、
  以及raw-entry到expanded-candidate的deterministic derivation indices；
- pre-draw role flags與下列exact priority tuple。

`value_sha256`是exact typed value的S00 canonical-JSON SHA-256；因此ID不依Python
`repr`、dict iteration order或locale。Registry row count必須等於三個expanded group
cardinalities加全部ungrouped candidate cardinalities，並與30-axis manifest雙向
reconcile；missing、duplicate或extra row在draw前fail closed。

`prelocked_candidate_atoms`在L0機械定義為：

> 每個`ungrouped && currently_unweighted && frozen_free && cardinality>1` residual
> axis的**全部**candidate rows。

`conditional_diagnostic_atoms`則是下列mechanical union：

1. `prelocked_candidate_atoms`；
2. 每個axis的`value_index=0`與`value_index=candidate_count-1` rows；
3. 任一axis中exact typed integer value為`-2`或`-1`的rows。

兩個sets都只依`atom_id` dedup。Bare first／last／sentinel角色只決定diagnostic
priority，不會自行把atom放進mandatory mapping set；只有該row同時因residual-gene
規則屬於`prelocked_candidate_atoms`時，witnessed後才mandatory。本版
`always_required_structural_atoms = []`；future若需要非candidate structural atom，
必須在任何draw前以authority amendment逐一給出ID、witness predicate與source/blob
binding，不能在看到support後新增。

每個prelocked atom的conditional priority固定為：

```text
(
  sentinel_rank,     # exact int -2 => 0; exact int -1 => 1; other => 2
  axis_scope_rank,   # eligible residual => 0; protected grouped => 1; other => 2
  boundary_rank,     # value_index 0 => 0; last => 1; interior => 2
  axis_index,
  value_index,
  atom_id
)
```

這個tuple、exact values與source evidence全部在draw前seal；observed support不能改role、
priority、ID或`prelocked_candidate_atoms`。

### 4.3 固定draw schedule與上限

- Ledger chunk固定512 nominal draws，便於原子保存、resume parity與首1% throughput
  重估；chunk不是accepted target。
- Global stream使用actual joint probabilities，**必須完整執行exact 32 chunks／
  16,384 nominal draws**。即使已取得exact-ten、全部prelocked atoms已有witness或
  intermediate結果看似足夠，也不得early stop。
- 只有global第32個chunk durable完成後，才把
  `conditional_diagnostic_atoms`中final global status仍為`support_unobserved`的rows依
  sealed priority tuple排序，取前15個作activated conditional targets。這是唯一
  derivation；不得使用Formocast、GFLOPS、mapping、noise或人工semantic judgment。
- 每個activated conditional固定該atom的exact typed value，其他axes仍依actual
  probabilities，且**必須完整執行exact 32 chunks／16,384 nominal draws**。Witness
  提前出現也不得early stop；找不到也不得extension。
- Global加全部conditional streams的總上限是512 chunks／262,144 nominal draws。
  因此`16,384 + 15 × 16,384 = 262,144`；沒有第16個conditional stream。
- 未進前15個targets、或完整conditional schedule後仍無witness的value只記
  `support_unobserved`。Interrupted run只能從same sealed ledger補完missing chunks；
  不得重抽已完成chunk、restart schedule、增加stream／seed／chunk／successor／root。

這個上限對七日Stage-1 cap是保守且可稽核的：最壞情況只做262,144次CPU
validity checks，遠小於舊S10R1每stream 2,851,250 draws，而且將昂貴GPU工作保留給
固定mapping/correctness/noise panel。Entry仍須以首1% measured throughput重估並證明
剩餘hard cap可容納完整panel；這個draw ceiling不是完成承諾。它仍只分類「未觀察」，
不提供absence proof。

## 5. Exact-ten mapping corpus

全部global／activated-conditional schedules完成後，mandatory mapping set只能是：

```text
mandatory_mapping_atoms
= (prelocked_candidate_atoms ∩ supported_witnessed)
  ∪ (always_required_structural_atoms ∩ structurally_witnessed)
```

本版第二項是empty set。Intersection只按sealed `atom_id`與final ledger status計算；
不得在看到support後重新判斷「source-semantic重要性」、增刪atom或用sample extrema
建立boundary。

從全部accepted witnesses選exact 10 distinct valid config hashes的規則固定為：

1. 每個config的coverage是它包含的`mandatory_mapping_atoms` atom IDs；
2. First-occurrence total order固定為
   `(stream_rank, conditional_priority_rank, chunk_index, draw_index, config_hash)`，
   其中global `stream_rank=0, conditional_priority_rank=-1`；conditional
   `stream_rank=1`且使用sealed target rank；
3. Greedy每輪選覆蓋最多remaining mandatory atoms的config；tie取較小
   first-occurrence total order，再取較小config hash；
4. mandatory set未全覆蓋，或完成cover需超過10個configs，結果是inconclusive；
5. cover少於10筆時，依同一first-occurrence total order從其餘distinct witnessed
   configs補到exact 10；少於10 distinct witnesses則inconclusive；
6. Final exact-ten按config hash排序，anchors仍固定indices`0,4,9`。不得第11筆、
   replacement、proxy、different-size corpus或post-Formocast selection。

若cap內少於10個distinct valid witnesses，或exact-ten無法覆蓋全部mandatory
operational atoms，結果是`inconclusive / FT-INCONCLUSIVE / edge=null`。若complete
proof顯示整個space少於10個distinct valid configs，也仍是inconclusive，不是mapping
negative；claim必須區分「cap內只觀察到少於10」與「complete proof少於10」。

## 6. Mapping corpus與sentinel conformance分離

### 6.1 Mapping status

Exact ten ×三個locked sizes形成30 rows。兩個fresh A/B passes必須：

- 30/30使用同一pinned Ductile validation／solution resolution；
- raw config、resolved solution、canonical hash、`SizeMapping`／Formocast input一致；
- occupancy、effective GSU、`MathClocksUnrolledLoop`、resolved sentinels與全部required
  backend fields都有direct／derived method、source symbol/blob、round-trip provenance；
- A/B byte／semantic parity，且mapping failure、猜值、unresolved required field、
  correctness substitution與row replacement全部為0。

Mapping status只判mapping。Random corpus不需要、也不允許以「命中sentinel」作
mapping acceptance atom。

### 6.2 Exact native-path score-blind helper conformance

另建立唯一`protocol/v1/manifests/s10r2-sentinel-conformance.json`。它使用L0預鎖的
synthetic whole-cohort fixture，不讀random corpus結果、GFLOPS或relative model
ranking。Conformance與subsequent mapping/runtime interpretation必須呼叫**同一個**
S10R2 native adapter；不得各自實作一份邏輯。

Pinned native path固定並綁定：

- `shared/origami/src/simulator/tensilelite/formocast_simulator.cpp` blob
  `cac2b324984a9fe2e1fadb018702486545e86e80`，symbol
  `origami::Formocast::predictedPerformance() const`；
- `shared/origami/include/origami/simulator/tensilelite/formocast_simulator.hpp` blob
  `96741965d34f2da1b0a08eaecab15e72082a78bc`；
- `projects/hipblaslt/tensilelite/client/src/SolutionIterator.cpp` blob
  `33e86cfc4bf3d4ce8fa8da194b94c024bbb5639f`，symbols
  `SolutionIterator::checkSolution(ContractionSolution&, ContractionProblemGemm&, bool)`
  與`AllSolutionsIterator::preProblem`的Formocast queue path；
- `projects/hipblaslt/tensilelite/client/include/SolutionIterator.hpp` blob
  `bad091c0f299f30c4235bc8313c9e8f134fa66a5`。

Future implementation的唯一native helper source path／symbol預註冊為
`protocol/v1/s10r2/native_formocast_runtime_adapter.cpp`／
`s10r2_native::evaluate_formocast_all_solutions_cohort`；唯一host adapter
source path／symbol為`protocol/v1/s10r2/native_adapter.py`／
`s10r2::PinnedNativeFormocastRuntimeAdapter.evaluate_cohort`。Frozen contract與
effective lock必須綁native Git objects、helper source SHA-256、helper binary
SHA-256、host adapter source SHA-256、symbols、build command/toolchain及invocation
argv；30-row mapping與synthetic conformance必須引用同一binding/hash。

該native adapter必須驗證：

- native Formocast early-terminate pair精確為
  `microSeconds=9999999.9, hitRate=0`；
- pinned source guard的first-true順序精確為：
  `global-split-u-zero`、`small-mn-macro-tile-gap`、
  `large-mn-macro-tile-gap`、`bf16-half-depthu-k-batch-mi`、
  `direct-to-lds-a-small-m`、`direct-to-lds-b-small-n`、
  `derived-plr-zero`；
- runtime先對完整frozen cohort執行`checkSolution`，只對valid rows預測，以原ordinal
  保持ties的stable ascending sort；threshold index為
  `min(n-1, floor(n * PredictionThreshold))`；
- `PredictionThreshold == 0`只queue best；`0 < threshold <= 1` queue到
  `latency <= threshold_value`的完整prefix；`threshold > 1`記
  `prediction_disabled`並走未篩選runtime path；
- synthetic cohort、latencies、validity mask、ties、thresholds、expected sorted
  order、threshold index/value與queue prefix全部在contract內freeze。

Separately implemented oracle只可比較native outputs、guard truth與queue transcript，
標`oracle_only=true`；它不能產生gate row、補native output或替代helper／adapter。
Fresh verifier必須做path-substitution fault injection：至少替換helper binary/path、
`predictedPerformance` source binding、host adapter hash及queue/checkSolution adapter
各一次，並證明contract／lock validation在任何conformance或mapping evidence前
fail closed。接受mock callback、Python-only queue或不同adapter輸出即
`CHANGES_REQUIRED`。

這是technical integrity gate。Helper／schema／guard／queue／path mismatch一律
`CHANGES_REQUIRED`並在R2 repair budget內修復重驗；不得把它冒充scientific
negative，也不得要求random exact-ten corpus實際命中sentinel。

## 7. GPU correctness與noise

- Entry resource preflight通過後才可使用existing `perlee`與符合
  `gfx942 / SPX / NPS1`的eligible device；不建立、停止或重建container。
- Exact-ten依sorted config hash固定indices `0,4,9`為三個anchors。
- 三anchors ×三sizes全部完成generate／compile／smoke與nonzero correctness；
  不得替換anchor。
- Locked generate／compile／smoke或nonzero correctness有可重現failure時，分類為
  `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-CORRECTNESS`；harness／adapter defect仍
  是`CHANGES_REQUIRED`，不可混用。
- Correctness全過後執行三anchors ×三sizes ×七repeats，共63 cells；保留parent
  escalation cap、`CV P95 <= 0.5%`、`delta_noise`公式與`reduce_fn=max`。
- Wall-time、CPU/GPU time、storage與throughput逐chunk／command累計寫入resource
  ledger；restart、successor、new root或S10R2 sibling身分都不重置。

## 8. Outcome matrix與唯一edge

`S1_ENTRY_GO`必須同時有：exact identity、cumulative resource preflight、
durable contract/lock、support classification、exact-ten corpus、30/30 A/B mapping、
helper conformance、三anchors correctness、63-cell noise、fresh independent verifier
PASS、self-contained report、`CLOSEOUT_ACK`、isolated closure commit與post-commit
audit。

| Evidence state | Classification | Report／repair | Edge |
| --- | --- | --- | --- |
| 全部criteria與closeout通過 | `positive / S1_ENTRY_GO` | S10R2 report＋compact gate record | `S11` |
| Valid exact-ten存在，但required mapping／field provenance可重現失敗 | `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING` | S10R2 terminal report | `null` |
| Locked generate／compile／smoke／nonzero correctness可重現失敗 | `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-CORRECTNESS` | S10R2 terminal report | `null` |
| Cap內不足10 witnesses、exact-ten cover不可行、complete proof少於10 overall或63-cell noise不穩定 | `inconclusive / FT-INCONCLUSIVE` | S10R2 terminal report | `null` |
| Harness／schema／API／guard／queue／lineage實作缺陷 | `CHANGES_REQUIRED`，scientific outcome仍`not_evaluated` | 限budget修復並全量重驗；不是terminal scientific report | `null` |
| Resource preflight或frozen budget不通過 | operational `BLOCKED`，scientific outcome仍`not_evaluated` | safe-boundary decision packet | `null` |

S10R2是新的、也是唯一的`S1_ENTRY_GO`來源。S10、S10R1、diagnostic generation、
proxy、two-size、reduced workload、helper-only pass或partial corpus都不能啟動S11。

## 9. Closeout與terminal integration

唯一formal report：

`reports/staged/s10r2-stage1-support-aware-entry-report.md`

Positive另seal compact machine gate record
`protocol/v1/evidence/gate-records/s10r2-s1-entry-go.json`。Negative／inconclusive
使用同一formal report；`CHANGES_REQUIRED`不是scientific terminal outcome。
Technical PASS只到`VERIFIED_PENDING_CLOSEOUT`；只有closure commit與post-commit
audit完成才是`CHECKPOINT_COMPLETE`。目前只核准documentation/authority amendment，
不建立contract、lock、runner、test、artifact、report、commit或push。
