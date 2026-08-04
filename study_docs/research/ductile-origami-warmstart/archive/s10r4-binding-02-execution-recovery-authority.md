---
authority_id: S10R4-BINDING-02-RECOVERY
checkpoint_id: S10R4
authority_status: approved
authority_scope: execution_binding_lifecycle_and_measurement_lineage_only
scientific_design_changed: false
scientific_outcome: not_evaluated
edge: null
binding_01_state: retired_diagnostic_in_place
binding_02_state: design_approved_not_yet_sealed
user_decision: approved
risk_tier: R3
scientific_gate: S10R4
execution_tranche: T-S10R4-B02
closure_unit: CU-S10R4
push_authorized: false
---

# S10R4 binding-02 execution recovery authority

導航：[S10R4 scientific design](s10r4-stage1-exact-frame-operational-entry-design.md)｜[active checkpoint index](../README.md)｜[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)

## 1. 白話結論

S10R4 binding-01 的第一個 census child 沒有進入 Ductile、Tensile 或 KernelWriter。
Parent 依 frozen design 在 child 專屬目錄啟動 worker，但 runner 在解析 command 前錯誤地
要求所有命令都必須從 repository root 執行，因此 worker 立即 fail closed。另有一個尚未
觸發但已由 code path 證實的 lifecycle defect：lock verifier 把 activation 當下的
formal-evidence absence 誤當成後續每個 command admission 都必須持續成立；即使 Pass A
成功，Pass B 也會被現存 raw scope 阻止。

這兩項是 execution harness／binding lifecycle 缺陷，不是 config、validator、
KernelWriter 或科學結果。Binding-01 退役為原地 immutable diagnostic；S10R4 的 hypothesis、
114×2 census、selection、mapping、native conformance、correctness、noise、outcome matrix、
claim 與唯一 outgoing edge 全部不變。Binding-02 使用全新的 execution namespace、contract
supplement、lock 與 audit ledgers，在 fresh seal 後從 config 0 重新執行完整 workload。

## 2. Authority order 與不變的科學邊界

Binding-02 必須依序服從：

1. `study_docs/research/surrogate-dse-plan.md`；
2. `study_docs/research/ductile-origami-warmstart-experiment-plan.md`；
3. `study_docs/research/ductile-origami-warmstart/s10r4-stage1-exact-frame-operational-entry-design.md`，raw SHA-256 `b63cff6fe0f7f03d2a69c6cb41b7b137fa373d8935fdf8c2283ee173e692c027`；
4. 原 scientific contract `protocol/v1/s10r4-stage1-exact-frame-entry-contract.yaml`，raw SHA-256 `be79e72f0eb7d54a6457eb5fabcdcd64b67523966300597efb0877e0fb82eeba`；
5. 本 recovery authority；
6. 新的 machine-readable binding-02 contract supplement 與 post-audited effective lock。

本 authority 只取代原 contract 中無法容納 successor execution binding 的 path、seal、
ledger、activation-absence 與 implementation identity；任何未明確取代的 scientific
欄位仍由原 contract 控制。禁止修改或事後放寬：

- exact sealed 114-config frame 與 registry order；
- 兩個完整、隔離、無 early stop 的 114-child census passes；
- stable survivor／stable attrition／discordance classification；
- `mandatory = prelocked_candidate_atoms ∩ operational_codegen_witnessed_atoms`；
- deterministic set cover、`K=max(10,C_greedy)`、`K_max=20`；
- mapping A/B、native conformance、3 anchors×3 sizes correctness、63-cell noise；
- outcome priority、failure IDs、claim boundary；
- 唯一 positive edge `S10R4:S1_ENTRY_GO_EXACT_FRAME -> S11`。

不得把 binding-01 partial、修復本身或 binding-02 的 fresh rerun描述成 independent
scientific replication。

## 3. Binding-01 immutable retirement

Binding-01 的正式 lifecycle 投影固定為：

- execution status：`retired_after_preterminal_changes_required`；
- checkpoint state：`BLOCKED`；
- scientific outcome：`not_evaluated`；
- edge：`null`；
- lock state：`superseded`；
- completed terminal census prefix：`0`；
- scientific report／decision／gate record：不得建立。

必須原地保留且不得搬移、刪除、覆寫、補 completion 或供 binding-02 讀取：

- Phase-2 commit `95e29a8618a4cf6bab1addb26376b1917ddb8404`，parent `9e10067d6ea7ae6b979cf99d97ebee007d1ceec6`；
- lock raw SHA-256 `168c5dd6b24b7843131c3ef32645ab1518aa4233b25aef918d41ab273af9abc4`，canonical self SHA-256 `8fa4973790170c471df52f1551a10885b4a6344d9e75ac676a5ac600c0e72853`；
- prebinding ledger raw SHA-256 `032b80e1de6c2d49101562a186dec20edc282438583940eb4928af8e26e18162`，ledger digest `3efbf295227089c17045a197ee56ea36a0d4cee5423341e4f03b89362d46c80a`；
- postbinding ledger raw SHA-256 `0eee0af8f9a77018d01b9dd0f93b85e9d0820ef4dead6fbcf5cf2723a547f756`，ledger digest `e02404f24b72a87b606cf7fc5a5bea9db0d8194f7481d917e88d7a53b4c2138d`，event digest `d593d13fddd9423077a2e11f56dc3808087c5afbbae8a3783a3f9f8f90863545`；
- run root `agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame/` 的所有 Plan、audit、prelabel、incident 與 governance bytes；
- partial child `artifacts/formal-codegen/pass-A/000-72dec49998a8db0bb51fcc723e5585925a7ec87906e61c149a7754d4c9b9ae0b/`；
- partial request SHA-256 `a69c04a12620cba5d6cdf28baf07b44df09b88cd8adcb16ce6dfa43052c34c24`、stderr SHA-256 `c847d187fdc7abeac3c6e703b6e95fb3b0ac3ddd32d82ecb6d1b519bbb03a328`、empty stdout SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；
- existing zero-byte writer-lock inode/path；它不代表 active flock，亦不得成為 binding-02 admission evidence。

Binding-01 的 `result.json`、`process-completion.json` 與 native artifacts 均不存在。
不得把 return code 2 轉成 ordinary attrition、KernelWriter failure、terminal child 或
resumable zero prefix。

## 4. Confirmed defects and required repairs

### B02-H1：worker cwd admission

Top-level commands仍必須從 `/src/rocm-libraries` 執行。Internal
`_census-child`、`_mapping-child`、`_correctness-build-child` 則必須在 parse 後依 exact
request／materialized command template綁定其 child／attempt root，並由 worker handler
再次驗證 cwd、request/result association與完整 environment。不得以跳過 cwd guard、
接受任意 cwd或弱化 argv validation修復。

### B02-H2：historical activation absence

Postbinding event 必須證明 binding-02 activation 當下所有 binding-02 formal／outcome／
raw scopes absent。後續 command admission 只驗證該 immutable historical event 的 schema、
paths、booleans、digest、commit及lock identity，不得以 live absence 重算歷史條件。Live
formal state 必須改由 artifact-derived state machine驗證 exact prefix、stage order、terminal
branch及forbidden future paths。

至少新增下列 regression coverage：

- real CLI subprocess從 config-specific cwd通過入口 guard並到達 exact internal handler；
- top-level command從非-repository cwd仍 fail closed；
- wrong request parent／result parent／cwd／environment／argv仍 fail closed；
- binding-02 raw child出現後，第二次 top-level formal admission仍可驗證 historical
  activation absence並交由 state machine決定 stage；
- forged activation record、pre-activation raw、foreign binding-01 path、partial／unknown
  binding-02 child仍 fail closed；
- tests不得讀 frozen Plan-B，也不得啟動正式 Ductile、Formocast、GPU或 outcome work。

## 5. Binding-02 frozen namespaces and whitelist

Binding-02 使用以下新 identity；不得 alias 或 fallback 至 binding-01：

- run root：`agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/`；
- machine-readable supplement：`study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4-stage1-exact-frame-entry-binding-02-contract.yaml`；
- effective lock：`study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s10r4-stage1-exact-frame-entry-binding-02-lock.json`；
- Plan／audit root：`agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/gates/s10r4/`；
- postcommit root：`agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/closure/`；
- prelabel roots：binding-02 run root下的`artifacts/prelabel-build/`、`artifacts/prelabel-fixtures/`與`artifacts/prelabel-tests/`；
- formal raw roots：binding-02 run root下的`artifacts/formal-codegen/`、`formal-mapping/`、`formal-native/`、`formal-gpu/`與`reproduction/`。

Canonical governance／ledger roles只有以下一條路徑，不得 alias、fallback、mirror、覆寫
或以binding-01同名檔案替代：

- Plan-B：`agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/gates/s10r4/plan_b.md`；
- Plan-B freeze：`agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/gates/s10r4/plan_b.freeze.json`；
- Plan-A：`agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/gates/s10r4/plan_a.md`；
- Plan-A revisions：`agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/gates/s10r4/plan_a-revisions.jsonl`；
- prebinding audit ledger：`agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/gates/s10r4/audit-verdict.json`；
- postcommit audit ledger：`agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/closure/post-commit-audit.json`，ordinal 0只可為binding-02 activation，ordinal 1只可為terminal closeout；
- authority precommit audits：`agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-02/authority/`；
- implementer／auditor reports：binding-02 `gates/s10r4/`下由supplement逐一指定的唯一檔案。

Existing binding-01 ledgers remain canonical only for retired binding-01 provenance；binding-02
code、lock、decision與reproduction不得開啟、解析或接受它們。Append-only要求適用於每個
binding自己的canonical ledger；不得把binding-01 ordinal接到binding-02，也不得在同一路徑
重建新的ordinal 0。

The supplement must freeze every exact descendant path, ledger path, command template, source
pin, manifest, test, implementation hash and absence set before evidence. It must expressly reject
all reads from the binding-01 run root during build-lock, formal execution, decision and
reproduction. Read-only audit of binding-01 identities is allowed only while constructing or
verifying the recovery authority／supplement boundary; it is never an empirical input.

Phase-1 for binding-02 commits only the new machine-readable supplement. Phase-2 exact-19 is the
same 15 implementation/schema/test files and three freshly regenerated registry／fixture files as
binding-01, with only the lock entry changed to the revisioned binding-02 lock path. The original
scientific contract is not modified or recommitted.

The three registry／fixture files may be byte-identical to binding-01 only because fresh binding-02
double replay independently reproduces them from the sealed S10R3 frame and source pins. They must
not be copied from or justified by binding-01 prelabel outputs.

## 6. Required history-preserving sequence

1. Commit and independently post-audit exactly these four recovery-authority paths, with no other staged path: `study_docs/research/surrogate-dse-plan.md`, `study_docs/research/ductile-origami-warmstart-experiment-plan.md`, `study_docs/research/ductile-origami-warmstart/README.md`, and `study_docs/research/ductile-origami-warmstart/s10r4-binding-02-execution-recovery-authority.md`.
2. Commit and post-audit the binding-02 machine-readable contract supplement before Plan-B.
3. Preserve the complete binding-01 run root in place. Do not stash, clean, amend, reset or rewrite commit `95e29a…`.
4. Create one ordinary history-preserving revert commit whose diff is the old exact-19 paths; no unrelated path may enter it.
5. Freeze a new binding-02 Plan-B, then Main authors Plan-A revision 13 or later without exposing Plan-B to the implementer.
6. Reuse the existing implementer thread for H1/H2 and binding-02 path implementation; repair count and resource use carry forward.
7. Freshly materialize and verify binding-02 prelabel/source/registries without reading binding-01 formal or prelabel artifacts.
8. The existing independent adversarial auditor reviews implementation parity, fresh prebinding and binding-02 postbinding. No outcome command may run first.
9. Commit the fresh binding-02 exact-19 set and obtain `AUDIT_PASS_POST_BINDING`／`LOCKED_READY`.
10. From config 0 run the complete 114×2 census and the remaining frozen stages in order. No binding-01 child counts.
11. Use the still-uninvolved fresh verifier for outcome verification and normal `CU-S10R4` closeout.

Successor／new root does not reset role, repair, wall, CPU/GPU, storage or throughput provenance.
Known binding-01 pre-empirical storage was 12,248,570,487 bytes before final reports and observed
activity lower bound was 15,842 seconds; whole-role CPU/wall remain `UNKNOWN`. Binding-02 records
these values and continues. Resource variance is notify-and-continue unless it reaches the existing
material safety／availability／completion／evidence boundary.

## 7. Outcome and stop semantics

Binding-02 may produce only the original S10R4 canonical outcomes. The first three complete census-A
children still trigger the prelocked runtime/storage reforecast, but do not change workload. Partial,
timeout, signal, unknown result, association drift, implementation defect or binding mismatch remains
`CHANGES_REQUIRED / not_evaluated / edge=null`; it must not become a scientific negative.

Only a post-audited positive S10R4 decision may activate S11. Binding-01 retirement, binding-02 seal,
repair PASS or completion of the census is not itself an outgoing edge. Push remains unauthorized.

## 8. Approval and reviewer record

Fresh Reviewer A `/root/s10r4_failure_reviewer_a` and independent adversarial auditor
`/root/s10r4_adversarial_auditor` inspected the same raw attempt, code, design, contract, lock and
Git lineage. They agreed that H1/H2 are harness defects; binding-01 evidence is inadmissible; commit
rewrite and descendant overlay are unacceptable; and a revisioned sibling binding is the sole
preserving recovery. The user explicitly approved establishing S10R4 binding-02 recovery authority
and continuing the full experiment. This file makes that decision authoritative without changing
the scientific estimand.
