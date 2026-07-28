---
name: implement-verify-loop
description: >-
  Executes risk-tiered engineering and experiment work from an approved design
  using one transient execution plan, a durable machine-readable frozen
  contract, bounded repair, and independent verification. Preserves hard
  scientific gates while allowing compatible gates to share an execution
  tranche and terminal closeout. Use for preregistered checkpoints with clear
  acceptance, evidence, authority, and report targets. Do not use to invent an
  ambiguous design or silently weaken a locked protocol.
---

# Implement and Verify Loop

Main agent 是 orchestrator：解析 authoritative bundle、凍結風險與 outcome contract、保護 baseline、管理有界角色與資源，並保存可追溯裁決與證據。

Verifier `PASS` 只代表 technical verification 通過並進入
`VERIFIED_PENDING_CLOSEOUT`。正式 report、parent update、`CLOSEOUT_ACK`、
授權範圍內的 terminal commit 與 post-commit audit 都完成後，closure unit 才是
`COMPLETE`。Scientific outcome 可在 durable contract seal 後、terminal closeout
前判定；不得為等待文書 closeout 而改寫已觀察 outcome。

## Checkpoint authority and vocabulary

- `scientific_gate` 是預註冊 outcome、claim 或 authority decision 的硬邊；不得合併、
  重排或用共享 closeout 繞過。
- `execution_tranche` 是可共享 planner、implementer、verifier、run root 與 repair
  ledger 的一段相容工作。Fresh implementer 不是必要條件；同一 implementer 可在
  tranche 內延續，但每個 outcome-bearing R1-R3 gate 仍須 fresh verifier。
- `closure_unit` 是一個或多個相容 adjacent gates 的 terminal evidence/report/parent
  update/staging/commit 單位。它不改變 gate order，也不把多個 outcome 混成一個。
- Parent plan index 中的 stable checkpoint 必須明確對應上述三種單位；`step`、
  `milestone`、day、stage 或 subtask 名稱本身不決定其 lifecycle。
- Parent plan與其明確引用的checkpoint design形成authoritative bundle。開始前必須
  唯一解析ID、goal、DAG/gates、acceptance/oracle、evidence/claim boundary、
  report或blocker target、status/outcome vocabulary、implementation whitelist、
  delivery whitelist、resource budget、closure grouping與scoped commit authority。
- 每個 execution tranche 開始時重新讀 current committed general rule 與本 skill
  並記錄 revision hash。Latest rule 是 orchestration/completion floor，但不能靜默改 scientific
  hypothesis或threshold；locked design衝突時先建立traceable amendment或new
  effective lock。
- 缺少或有多個合理parent、checkpoint、report target或其他authority欄位時停止釐清；
  不可由subagent consensus發明使用者意圖。

## Risk tier and frozen state

在任何 outcome label、result interpretation 或 label-revealing command 前，將每個
scientific gate 的 tier 寫入 durable frozen contract：

- `R0 mechanical`：不接觸 outcome 的格式、拼字、確定性搬移或其他機械工作。
- `R1 standard preregistered outcome checkpoint`：依既有設計執行與判讀的標準 outcome gate。
- `R2 material measurement/claim/lineage risk`：會實質影響 measurement、claim boundary、
  provenance、lineage、selection 或 comparability 的工作。
- `R3 authority/destructive/post-label change`：需要新 authority、具破壞性，或在 labels
  可見後改 protocol、contract、lock、fixture、threshold、selection、lineage 或 claim。

Tier 在 labels 前凍結。Labels 後只能 escalation，不能降級；generation、successor、
renaming、replacement 或 fresh thread 都不能重設 tier、repair count 或 authority history。
任何 outcome-bearing action 必須等 durable machine-readable frozen contract 與 lock
以 tracked commit 或同等不可變 authority 完成 seal。Terminal evidence/report closeout
在 outcome 後另行完成，不得把兩者混成同一 gate。

同時維護兩個不同 state：

- `live_run_state`：working tree、正在執行／待驗證 run、partial artifacts 與即時資源狀態。
- `committed_projection_state`：最後已 commit 的 contract、lock、parent projection 與
  terminal state；不可把 partial live result 回填成 committed fact。

## Model and independence policy

- Model pin 是 disclosed preference／capability requirement，不是 R0/R1 的 universal hard
  stop。記錄 requested model、actual model、差異與 capability assessment；不可靜默以
  較弱能力冒充符合需求。只有 approved contract 明定 capability 不可替代時才停止。
- Same-model fresh threads 只提供 process independence，不是 scientific replication；
  報告不得把它當作獨立資料、獨立實驗或統計重現。
- 預設一個 execution planner。R2/R3 另加一個 fresh adversarial oracle/authority
  auditor，在 labels 前挑戰 frozen contract、lineage 與 authority。
- Fresh implementer 不是強制角色；Main agent 或既有 implementer 可在同一 execution
  tranche 內延續。角色延續與變更都記錄在 lineage。
- Outcome-bearing R1-R3 必須由未參與該 gate 實作的 fresh verifier 驗證 frozen
  contract。Repair 可 resume 同一 verifier；若更換 verifier，replacement 必須完整重驗。
- Verifier 依 frozen contract 與 direct evidence 判斷，不依 transient execution plan
  的步驟選擇判斷。

## Unexpected design issue adjudication

只有執行中出現會實質改變 protocol、measurement／claim boundary、lineage 或 authority
的 ambiguity，才使用 `design-discussion`。機械修復、已有唯一 contract-preserving
答案、普通 code choice 或單純資源等待不觸發：

- 以完全相同、自足且不暗示偏好的 prompt，啟動兩個額外的 fresh
  reviewers，並套用該 skill 的 cap。
- 最多兩輪 cross-examination，再加一輪 evidence-backed final positions；全體 reviewer
  累計最多 60 agent wall-minutes。
- 不強迫 `AGREE`。在任一 cap 到達時停止辯論，保存雙方 dissent、共同點、evidence
  boundary 與最小 decision packet，交 human escalation。
- 這兩個 reviewers 不取代 planner、oracle/authority auditor、implementer 或 verifier，
  也不得直接修改 implementation 或創造 authority。
- 若雙方在 cap 內同意且完整保留 frozen contract/authority，Main agent 記錄裁決後可
  繼續；否則保留 dissent，不得把分歧改寫成 consensus。

適用情況包括：

- Verifier finding 暴露 lifecycle、lock、authority、evidence integrity 或 recovery
  protocol 的設計缺口。
- 一個 `CHANGES_REQUIRED` finding 有數個合理修復方向，且選錯會改變 lineage、
  measurement boundary 或後續可接受 claim。
- Checkpoint 的 negative、counterintuitive 或 ambiguous result需要重新判斷原
  hypothesis、gate edge 或 implementation architecture。
- `/data1/perlee`內出現whitelist外artifact時，若可能適用已預授權的workspace
  recovery，先依[authority gates](references/authority-gates.md)分類；符合 deterministic
  disposable recovery 的 case 不需 design discussion。

若 finding 只有一個明確、execution whitelist 內且不改 frozen contract 的機械式修復，直接
resume 原 implementer/verifier，不需啟動 design discussion。

### Consensus 後的 user-review boundary

- 若 consensus 完整保留 approved design、frozen contract、acceptance、evidence source、
  report target、checkpoint DAG/gates、whitelist/authority invariants 與 claim
  boundary，Main agent 記錄裁決後直接繼續，不需再向使用者尋求同意。
- 任何時點只要 consensus 證明繼續工作必須**打破或修改原訂 plan/authority**，才將
  consensus與change packet交給使用者審查。這包括修改frozen goal/contract、
  acceptance/threshold、planned evidence、report target、checkpoint order/gate、
  preregistered fixture/measurement boundary、approved whitelist、immutable
  lock/lifecycle invariant或允許的 claim。
- `CHANGES_REQUIRED` 本身不等於 plan change。保留原 acceptance 的 in-scope repair、
  fresh rerun、同 lineage role resume或原計畫已定義的 negative branch都不需重複
  human approval。
- 若 reviewers 在 round/time cap 仍有 material dissent，或分歧是上述 plan-changing
  trade-off／使用者偏好，保存 dissent 並升級；不可延長辯論或強迫同意。
- 每個agent-decided issue都寫入`adjudication.md`，並在formal report中materialize；
  實際使用 design discussion 時另記雙方 objections、採納/捨棄、consensus 或 preserved
  dissent、round/time usage 與 final responses。不可只連到 transient artifact。
- Consensus不能創造push、credentials、external-system write、dependency install、
  container mutation或其他缺少的platform authority。

## Scientific gates, execution tranches, and closure units

若 source spec 包含多個 ordered/dependent checkpoints：

1. 先建立 scientific gate DAG、hard edges、execution tranche 與 closure unit mapping。
2. Hard scientific edges 永遠不軟化：dependent gate 只有在 upstream outcome 已依
   frozen contract verified 後才可進入。
3. 相容 adjacent gates 可共享 planner、implementer、verifier、run root、repair ledger，
   並在一個 terminal closeout 完成，但每個 gate 保留獨立 contract criterion、outcome、
   evidence lineage 與 verdict。
4. Independent label-blind preparations 可平行，前提是 write、artifact、index、run root、
   evidence 與 authority boundaries 不重疊；任何 outcome reveal 仍受各自 hard edge。
5. Implementer 只可修改 tranche whitelist；future/dependent outcome logic 不可預先
   啟動。共用元件必須能直接追到已 dependency-ready gate。
6. `BLOCKED`、`FAIL`、missing evidence、still-running verification 或 human gate 停止
   該 dependency path，但不阻止邊界完全獨立的 label-blind preparation。
7. Negative/falsified outcome 若 evidence 與 gate decision 正確仍可 technical `PASS`；
   只沿 design 明定 edge 前進。`skipped_by_gate` 由 closure unit report、parent update
   與 terminal commit 保存，不替未執行 gate 建立假 report。

## Run directory

每次執行使用 repo root 下的：

```text
agent_run/YYMMDD-{feature-slug}[-N]/
```

單一 gate 至少保存同等 flat artifacts。多 gate tranche 建議使用：

```text
baseline.md
gate-map.md
adjudication.md
subagents.md
tranche-state.json
gates/
  <gate-id>/
    baseline.md
    execution-plan.md
    frozen-contract.snapshot.json
    impl_report.md
    verify_report.md
    verdict.json
closure/
  closeout.md
  delivery-manifest.txt
```

- `agent_run/` 是 transient evidence，不得 commit。
- 開始前用 `git check-ignore` 確認它已被忽略。
- 若未被忽略，先取得使用者同意才可新增 ignore rule；不可靜默修改 ignore 設定。
- Durable machine-readable frozen contract 必須位於 approved design 指定的 tracked
  protocol/lock path；run directory 只保存其 exact snapshot 與 hash，不得拿 transient
  snapshot 取代 durable seal。
- `gate-map.md` 記錄 DAG、tranche/closure mapping、active gate、verified upstream
  outcomes 與 eligible next edges；不得預先把 future gate 標成 in progress。
- `tranche-state.json` 分開記錄 `live_run_state` 與 `committed_projection_state`。
- 每個 subagent 的 gate、model、role、fresh/resumed lineage、agent link/ID 與 artifact
  path 記在 `subagents.md`。
- 完整內容寫入 artifact；subagent 回覆 Main agent 時只回傳短 status、changed files、verdict 與 artifact paths。

## Step 0：解析需求、scope 與 baseline

1. 由`$ARGUMENTS`與authoritative bundle解析唯一parent plan、gate design與ID；
   不可發明spec、report或blocker path。
2. 讀latest committed repo rule、本skill、parent/design、相關code/tests，記錄revision/hash；
   有locked conflict先traceable alignment。
3. 解析 scientific gate DAG、tranche/closure mapping、acceptance/oracle、
   evidence/claim boundary、status/outcome vocabulary、report/blocker target與
   terminalization policy。
4. 凍結兩層whitelist：
   - `implementation_whitelist`：implementer可修改的source/test/config/design deliverables。
   - `delivery_whitelist`：前者加formal report、parent checkpoint-specific hunk及明確
     授權的durable amendment/artifact。
5. 在 outcome labels 前分類並凍結 R0-R3 tier；R2/R3 預約 adversarial auditor。
6. 確認 scoped authority。只有既有明確 authority 涵蓋時，才可在 terminal closure
   對 exact delivery paths 做 isolated commit；push、PR、credentials、external write、
   dependency install、container mutation 與其他未授權動作仍各自 gated。
7. 建立 scientific gate DAG，選出 dependency-ready gate，並標示可平行的 independent
   label-blind preparations；有實質歧義時先詢問使用者。
8. 建立 run directory、gate evidence directory 與 closure directory。
9. 開始前將以下baseline寫入`baseline.md`：
   - Parent repo 與 relevant submodules 的 current branch/commit。
   - UTC capture time與`git status --short --untracked-files=all`完整結果。
   - Plan commands會觸及的ignored／non-Git roots之targeted absence，或既有path的
     `lstat`／hash inventory。
   - 已完成upstream checkpoints的commit、verdict與report identity。
   - 兩層whitelist、formal report/parent path與禁止接觸的downstream paths。
10. 凍結 resource contract：
    - Pre-empirical engineering 最多使用 stage cap 的 20%。
    - 預設 transient storage cap 是 5 GiB，除非 approved design 明定其他值。
    - 記錄 wall-time、storage、throughput assumptions 與 safe boundaries。
    - 同一 scientific gate/lineage 已消耗的 wall-time、CPU/GPU time、storage、
      throughput samples 與 pre-empirical engineering budget，必須跨 generation、
      successor、replacement role、process restart 與 new run root 累積。除非 human
      明確批准新的 authority/contract，任何一項都不可 reset；新 contract 必須記錄
      prior consumption、carry-over 與明確批准的 reset boundary。
11. 從 approved design 擷取 durable machine-readable frozen contract，至少包含 gate
    ID/tier、labels、criteria、outcome/edge matrix、evidence/measurement/claim boundary、
    fixtures、lineage、whitelists、authority、repair budget、resource cap、downgrade gate
    與 lock identity。人工與機器表示必須可追溯；不一致時停止。
12. R2/R3 由 adversarial oracle/authority auditor 在 labels 前檢查 contract 完整性、
    post-label invariants、authority 與 claim boundary。修正後重新 hash。
13. Contract 與 lock 經 tracked commit 或 approved immutable mechanism seal 後，才允許
    outcome-bearing command 或 label access。Seal 後只能 escalation；修改需 R3 human gate
    與新 generation/amendment，不得覆寫舊 contract。
14. 保留所有 unrelated user changes與已通過 upstream changes；不可 reset、checkout、
    stash、覆蓋或順手整理。
15. 每進入新 tranche 或 baseline drift 時重做 relevant capture；共享 tranche 不代表
    可沿用 stale evidence。

## Step 1：建立一份 transient execution plan

預設只建立一個 execution planner。它收到一份 `BASE REQUIREMENTS` block：

- Repo root、source note/spec 路徑與必要 context。
- Active gate、tranche/closure mapping、risk tier、main objective 與 scope。
- Authoritative parent/design、durable frozen-contract/lock paths 與 hashes、formal report
  path、implementation/delivery whitelists 與 scoped authority。
- Verified upstream gate evidence、允許的 dependency edge 與 downstream exclusion。
- Frozen required behavior、acceptance criteria 與 outcome/next-edge matrix。
- Constraints、compatibility boundaries 與禁止事項。
- Known user changes、resource contract、可用環境、evidence/artifact paths。
- 明確說明只負責 planning，不實作 source change。

Planner 只允許寫 transient `execution-plan.md`。要求內容：

- Objective 與 scope restatement。
- Exact implementation whitelist 或清楚的 whitelist scope。
- Whitelist 只能服務 active/dependency-ready gates；明列 dependent paths 為禁止修改。
- 每個檔案預計修改的 symbol、anchor、behavior 與 reuse pattern。
- 若需 spike，列出 hypotheses、調查位置、decision criteria 與可接受邊界。
- Compatibility、error handling、data/measurement boundary。
- Implementer 可執行的 verification commands 與預期可觀察結果。
- Implementer 不能執行而需 verifier/使用者提供的 evidence。
- `impl_report.md` 必須記錄的內容與 deviation policy。
- Pre-empirical engineering、wall-time、storage、throughput estimates、first-1% reforecast
  point 與 safe pause boundaries。

Execution plan 必須盡量具體，但不可偽造尚未查證的 code path、command 或行號。它可
隨 implementation discovery 修訂並保留 revision ledger，因此不是 outcome authority，
也不得覆蓋 durable frozen contract。

### Main agent plan gate

Planner 完成後，Main agent：

1. 確認 plan 忠於 frozen contract、whitelist、hard edges 與 resource cap。
2. 確認 machine-readable contract 可獨立驗證 objective、positive/negative/inconclusive/
   blocked outcome、criteria、unacceptable fallback、evidence 與 next edge；不可把這些
   authority 留在 natural-language plan。
3. R2/R3 必須取得 fresh adversarial auditor 的 `AUDIT_PASS`；finding 只可在 labels 前
   以 traceable contract revision 修正。Labels 後只能 R3 escalation。
4. 在 `adjudication.md` 記錄 execution-plan revision、contract hash、lock identity、
   tier、auditor result 與 `SEALED` state。

## Step 2：在 execution tranche 實作與執行

Fresh implementer 不是 mandatory。Main agent 可啟動 implementer，或讓同一 implementer
沿用 tranche thread。Implementer 收到 transient execution plan 與必要的 frozen
constraints，但不得取得修改 contract 的 authority：

- 在 current workspace 實作 dependency-ready gate 的 execution plan。
- 只修改 implementation whitelist 內的 paths，以及本 run 的 `impl_report.md`。
- 不得修改、補stub、順手抽象化或預建任何downstream checkpoint path/behavior。
- 先檢查檔案 current content，避免覆蓋 baseline 中的 user changes。
- Plan 留有 spike 時，在 frozen goal、direction 與 decision criteria 內完成探索並記錄選擇理由。
- 執行 execution plan 中可執行的 verification commands。
- 不得 commit、push、install dependency、存取 credentials 或做 external writes。
- 將每個 changed file、behavior、command、exit code、artifact、deviation、未完成項目寫入 `impl_report.md`。
- 回覆只包含 terse status、changed-file list 與 report path。
- Pre-empirical engineering 達 stage cap 20% 時停止增加 scaffolding。
- 完成 planned workload 的最初 1% 後，以 observed throughput 重新預測 wall-time 與
  storage。若 projection 超過原估計 2 倍，或任何 wall-time/storage/throughput budget
  已超限，於 safe boundary 暫停並提交 decision packet。
- Runtime duration 本身不得成為 optional stopping 或選擇性保留 outcome 的理由；但
  已凍結 budget exceed 是硬 gate。Decision packet 必須列 live state、completed/missing
  work、projection、storage、可保留 evidence、preserve-plan alternatives 與 downgrade impact。

Implementer 回覆後，Main agent：

1. 擷取相對 baseline 的 parent/submodule diff 與 status。
2. 檢查 whitelist、unrelated user changes 與意外 artifact。
3. 若有 whitelist 外 mutation，停止該 role、不得啟動 verifier 並保存 incident manifest：
   - 符合[workspace recovery standing authority](references/authority-gates.md)者，
     automatic 執行 deterministic exact quarantine 與 post-audit，不需 dual reviewers，
     再重做本 Step。
   - 其他情況立即向使用者呈現delta；不可單方面revert、delete、stash、覆蓋或擴張whitelist。
4. 若 implementer 自己已知未完成，不啟動假驗證；先在 scope 內 resume implementer 補齊，或誠實升級。

## Step 3：Fresh verifier 依 frozen contract 驗證

Outcome-bearing R1-R3 gate 必須啟動未參與該 gate implementation 的 fresh verifier。
R0 可依風險由 Main agent 做 deterministic check。Verifier 收到：

- Durable frozen contract/lock 與 exact seal hash。
- Baseline references。
- Current implementation diff 與 changed paths。
- Source/test/artifact paths。
- `impl_report.md` 作為待查證的 claim，不是 ground truth。
- 下列 verifier contract。

Verifier 可讀 execution plan 了解路徑，但 acceptance 只由 frozen contract 決定；不得因
plan 或 implementer 選擇而改 goal、threshold、evidence boundary 或 outcome matrix。

Verifier contract：

- 不修改 source、tests、configs、approved design、frozen contract 或 lock。
- 只可寫本 run 的 `verify_report.md`、`verdict.json` 與明確允許的 reproduction artifacts。
- 重新讀 current code 與 surrounding call paths。
- 逐項以 direct evidence 判斷 frozen acceptance criteria。
- 確認diff只包含active checkpoint implementation whitelist，且沒有downstream
  speculative implementation。
- 自己 fresh reproduce headline acceptance check，不可只採信 implementer 結果。
- 檢查 regression、compatibility、edge cases、measurement comparability 與 unacceptable fallbacks。
- 若 command 會修改 source 或需權限、network、credentials、dependency install、長時間資源，列為 evidence request，不可自行越權。
- 回覆只包含 `verdict`、`goal_alignment`、blocking count 與 artifact paths。
- 若 implementation 已 stable 且 complete staged draft 已準備好，同一個 fresh verifier
  pass 可同時完成 technical verification 與 staged closeout audit；兩個 verdict 仍須
  分欄記錄。若 staging 在 technical pass 後改變，必須重做 affected audit。

`verdict.json` 至少使用：

```json
{
  "verdict": "PASS | CHANGES_REQUIRED | BLOCKED",
  "goal_alignment": "FULL | PARTIAL | NONE",
  "acceptance_criteria": [{
    "criterion": "required behavior",
    "status": "PASS | FAIL | UNVERIFIED",
    "evidence": ["direct evidence"]
  }],
  "blocking_findings": [{
    "id": "stable-id", "severity": "critical | major | moderate",
    "evidence": "specific evidence", "required_change": "actionable correction"
  }],
  "commands_run": [{
    "command": "exact command", "cwd": "working directory",
    "result": "PASS | FAIL | BLOCKED", "evidence": "exit code and output"
  }],
  "evidence_requests": [],
  "unverified": [],
  "unacceptable_fallback_triggered": {"triggered": false, "which": []},
  "summary": "bounded conclusion"
}
```

`PASS` 僅在以下條件全數成立時允許：

- `goal_alignment`是`FULL`且每個required criterion都是`PASS`。
- `blocking_findings`、`evidence_requests` 與 required `unverified` 都為空。
- 沒有 unacceptable fallback。
- Headline check 已由 verifier fresh reproduce。
- Active checkpoint所有預定runs都完整結束且可判讀，沒有partial、timeout、killed或
  still-running結果；scientific negative outcome依frozen design記錄，不得偽裝成
  effect success。
- Frozen contract/lock hash、measurement lineage、resource decision 與 label boundary
  完整，且沒有未處理的 budget gate 或 downgrade。

## Step 4：Adjudicate 與修正迴圈

Main agent 每輪將以下內容追加到 `adjudication.md`：

- Iteration number、risk tier 與 frozen contract/lock hash。
- Implementer changed paths 與 evidence。
- Verifier verdict、blocking finding IDs 與 evidence requests。
- Main agent 的判斷、下一步與未解風險。

Repair round 是一個 verifier finding 被送修、實作回應並重新驗證的完整 cycle：

- R0/R1 每個 gate 最多 2 rounds。
- R2 最多 3 rounds。
- R3 最多 3 rounds；超過只能取得 human approval。
- 同一 finding 連續 2 rounds 沒有 material progress，立即停止。
- Generation、successor、renaming、replacement、role/thread restart 或搬到新 run root
  都不能重設計數。
- 同一 gate/lineage 累計 fresh role threads 上限：R2 = 5，R3 = 6。Planner、auditor、
  verifier/replacement 與 design reviewers 都計入；不得用新 thread 規避 repair cap。

### Technical PASS

只有 verifier 回覆合格 `PASS` 時：

1. 再次檢查 frozen contract/lock hash 未變。
2. 確認 working tree 沒有 verifier 或其他角色造成的越界 source change。
3. 確認沒有unresolved whitelist外artifact；曾使用standing recovery時，其qualification、
   quarantine／absence hash、full status與unrelated-change post-audit必須完整。
4. 確認active checkpoint沒有downstream speculative change。
5. 記錄technical `CONSISTENT`、scientific outcome與verified outgoing edges。
6. 將 gate state 設為 `VERIFIED_PENDING_CLOSEOUT`。符合 frozen hard edge 的 adjacent
   gate 可在同一 tranche 繼續；closure unit 尚不可宣告 complete。

### CHANGES_REQUIRED

1. Main agent 依 direct evidence 判斷 findings 是否具體、是否在 scope 內。
2. 若 finding 只有唯一、contract-preserving 的 in-scope 修復，且仍在 repair budget
   內，直接進入原
   implementer/verifier repair loop。
3. 若 finding 暴露 material protocol/claim/authority ambiguity 或多個
   合理方向，先依 `Unexpected design issue adjudication` 完成 dual-agent
   `design-discussion`；不得先改 source 或 authority。
4. Consensus 保留 frozen contract 時，Main agent 記錄後直接執行；任何 preserved
   dissent、cap reached 或 contract/authority change 都提交使用者審查並等待決定。
5. 將 blocking IDs、`verify_report.md`、required changes 與 current changed paths resume 給原 implementer。
6. Implementer 修正後更新 `impl_report.md`，並只回傳短 status 與 paths。
7. Main agent 再做 whitelist/baseline check。
8. Resume 原 verifier：
   - 提供 addressed finding IDs、new diff、commands/artifacts 與 remaining uncertainties。
   - 要求重新讀 current files 並 fresh rerun relevant checks。
   - 不可只相信 repair summary。
9. 在 repair/thread budget 內重複；達 cap 時 honest exit，不得自動開 generation 重算。

修正迴圈期間 active gate 不變；只有邊界完全獨立且 label-blind 的 preparations 可平行。

### BLOCKED 或 evidence request

- Main agent 可執行短、可逆且在授權範圍內的 evidence command，並記錄 exact command、cwd、exit code 與 artifacts，再 resume verifier。
- 遇到 material protocol/claim/authority ambiguity 才走 bounded dual-agent
  `design-discussion`；deterministic disposable artifact recovery 依 reference 自動處理。
- 只有 consensus 顯示繼續必須改 frozen contract/authority、bounded discussion 保留
  material dissent，或操作需要尚未取得的
  external/platform authority，才詢問使用者。
- 若環境無法取得必要 evidence，terminal state 是 `BLOCKED`，不是 `PASS`。
- `BLOCKED` 或 evidence request 停止該 dependency path 的 outcome-bearing work；只允許
  邊界不重疊的 independent label-blind preparation。

### Honest exits

達 risk-tier repair/thread cap、同一 finding 連續兩 rounds 無 progress、resource gate
暫停後無 approved decision、所需工作/硬體/資料/環境超出 scope、現有 evidence 無法
判定，或只支持 inconclusive 而不足以支持原 claim 時，停止並誠實升級，不假裝完成。

## Step 5：Closure-unit report、parent update、closeout 與 commit

Closure unit 內所有 activated gates 都 technical `PASS` 或依 frozen edge 合法
`skipped_by_gate`/terminalized 後，完成一次 terminal closeout：

1. Main agent 依 planned path 建立 self-contained formal report；按 gate 逐項回答
   frozen contract，並將所有 material adjudication 從 transient evidence 整合進 report。
2. 更新 authoritative parent 的 gate outcomes、report link、verified outgoing edges、
   closure state 與 residual risk；不可趁 closeout 改 hypothesis、threshold、DAG、
   contract、lock 或 authority。`committed_projection_state` 只在 commit 成功後更新。
3. 只stage frozen delivery whitelist。Shared parent若含unrelated hunks，安全
   hunk-isolate；無法拆分就停止。不可使用`git add -A`、`git add .`或
   `git commit -a`，也不可alter既有unrelated index entries。
4. 從排序後的staged path、mode與blob OID產生`delivery-manifest.txt`及SHA-256。若
   technical verification 尚未結合 closeout，將 path-limited cached diff、report、
   parent、contract/lock hashes 與 manifest 交 fresh verifier 做 read-only audit。
5. Verifier確認report忠於direct evidence、parent與gate一致、staged bytes等於delivery
   whitelist且無unrelated/downstream內容後，回`CLOSEOUT_ACK`。Verifier不得修改tracked
   files；文書缺漏由Main agent修後重查。
6. 若closeout揭露source/evidence問題，technical `PASS`失效並回原
   implementer/verifier loop。原verifier永久不可resume時，replacement必須從frozen
   contract 完整重驗後才能 audit closeout，且 replacement 計入 fresh-thread cap。
7. 只有 scoped authority 已涵蓋 exact closure unit 時，才使用 exact delivery paths
   做 path-limited terminal commit；commit message含：

   ```text
   Closure-Unit: <stable-id>
   Gate-States: <gate-id=state,...>
   Experiment-Report: <repo-relative-path>
   Frozen-Contract-SHA256: <sha256-or-manifest>
   Delivery-Manifest-SHA256: <sha256>
   ```

8. Commit後用`git show`/`git diff-tree`確認paths與content identity符合manifest，
   unrelated working-tree/index changes仍保留；將actual commit SHA與audit寫入
   transient `closeout.md`及final handoff。
9. 只有 terminal commit 與 post-commit audit 成功才標 closure unit `COMPLETE`。
   Commit 失敗或 audit 不符時留在 `VERIFIED_PENDING_CLOSEOUT`；已 verified scientific
   outcomes 不變，但不得把 `committed_projection_state` 宣告為 complete。

Outcome/document matrix：

- Technical `PASS` 搭配 positive、negative 或 inconclusive outcome 都納入其 closure
  unit 的 Step 5；`PASS` 不代表 scientific positive，也不要求每個 internal gate
  各做一份 terminal closeout。
- Durable terminal `BLOCKED`只有在Step 0預註冊terminalization condition、blocker memo
  path與blocked-state commit policy時，才建立memo與parent blocked update並isolated
  terminal commit。它不是positive report或scientific completion，不解鎖dependent edge。
- Transient evidence request、still-running job或recoverable blocker不terminalize、不
  建memo、不commit completion。
- `skipped_by_gate`/`not_activated` gate 不建自己的 report 或 commit；由 closure unit
  Step 5 持久化。`CHANGES_REQUIRED` 不建 terminal report 或 commit。

## Human review and authority gates

在判斷是否需要human review或處理任何whitelist外mutation前，完整讀取並套用
[authority gates and `/data1/perlee` workspace recovery](references/authority-gates.md)。
該reference保存原有human gates，並記錄repository owner已授權的窄範圍
current-run artifact recovery；不得只讀本節摘要後擴張其scope。

## 文件與 evidence 規範

### Formal report readability 與 post-closeout editorial revision

Formal report 同時服務第一次閱讀的工程師與需要重現證據的稽核者。證據完整不等於把 execution ledger 當成主敘事；先建立可理解的主線，再保留完整稽核細節：

- 報告開頭先用繁體中文白話回答五件事：這一關要驗什麼、實際看到什麼、為什麼得到這個判決、證據能與不能支持什麼，以及下一個合法 checkpoint 是什麼。
- 第一個畫面內用表格或短清單分開 technical verification、scientific outcome、checkpoint state、criterion、failure ID 與 outgoing edge。Technical `PASS` 和 scientific positive／negative 不得混為同一件事。
- 有三個以上步驟的流程使用精簡 Mermaid flowchart 或編號流程。每個 project-specific／domain term 第一次出現時先給一句白話定義，再使用精確術語。
- 主文依「問題 → 方法 → 結果 → 原因 → 限制 → 下一步」組織，不依 agent、command 或 repair 發生時間寫成流水帳。Exact hashes、commands、working directories、exit codes、iterations、repairs、deviations 與 closeout ledger 放入同檔、具名的「稽核附錄」，不可刪除或只改成 transient link。
- 中文與 English、數字、inline code 之間使用半形空格。Identifier、path、hash、command、machine output 與 fenced code block 內部維持原始 bytes，不套用文字間距。
- Prose 不為了固定欄寬在詞組或 inline code 中間硬斷行。每個實體行保留完整句意；主題改變時用空行，enumeration 改用一點一義的 bullet、nested list 或 table。
- Exact command／machine-output blocks 在改寫時保持 byte-for-byte；正文先說明該 evidence 要回答的問題與 observable result，讀者不需要先解讀 command 才知道結論。

原始 closeout report 仍遵守「不嵌入自己尚未存在的 closure commit SHA」。若 closure unit 已完成後，使用者另行明確授權 in-place editorial revision：

- 頁首標示這是 post-closeout editorial revision，列出原始 closure commit 與原始 report SHA-256，並說明 Git history 中的原始 bytes 才是 staged-byte `CLOSEOUT_ACK` 與 historical validator 的重現邊界。
- 新版不得自稱原始 closeout bytes，不得把文字改版描述成重新執行、重新驗證或重新 closeout，也不得改 outcome、gate、claim boundary 或 evidence identity。
- 除非新 authority 明確重開 checkpoint，否則不更新舊 lock、runner、schema 或 downstream binding；需要 historical validation 時在原始 closure commit 重現。

- 一個 bullet 一個重點；多部分 claim 使用 nested bullets。
- Command 必須記錄 exact cwd、exit code 與關鍵 observable result。
- Comparative experiment 先確認 metrics 測量同一 quantity、boundary 與 clock/domain。
- Ranking/fidelity 先看實際 decision metric，例如 top-k、best config 或 Pareto；correlation 與 average error 只能作輔助。
- 不從單一 dataset、少數 case、單一 metric 或缺少 mechanism 的結果宣稱普遍勝出。
- Report claim 必須能追到 raw artifact、command 或 code path。
- Formal report必須durable重述frozen contract/oracle/evidence boundary、每輪findings/repairs/
  deviations與actual outcome/gate。
- 每個agent-decided issue記trigger、affected invariant、alternatives、正反evidence、
  assumptions、roles、decision、rationale/trade-off、impact、resolution、residual
  risk與review basis。只有實際使用`design-discussion`者才另記雙方objections、
  採納/捨棄、consensus 或 preserved dissent、round/time cap 與 final responses。
- 不貼raw chat或private chain-of-thought；不以transient link取代正式report。
- Tracked report/parent不嵌closure commit自己的SHA、`SELF`或delivery-manifest hash；
  用stable identity、commit trailers、Git history與post-audit關聯。
- 不把大篇 report 或完整 JSON 重貼回 parent context；回傳 artifact path 即可。

## 完成輸出

以繁體中文精簡摘要 run directory、risk tiers、gate/tranche/closure mapping、
`live_run_state`、`committed_projection_state`、parent/design 與 frozen-contract/lock hashes、
changed files、fresh verifier commands、technical verdict、scientific outcome、formal
report、`CLOSEOUT_ACK`、closure commit SHA、post-audit、verified edge、evidence boundary
與 risks。只有 required closure units 經 post-commit audit `COMPLETE`，或 gates 依
verified edge 合法 skip/not-activate，才能宣告整體完成；否則列出 technical/closeout state、blocking
evidence、未開始的downstream與需要使用者決定的下一步。

Closure unit 沒有 post-audited terminal commit 時，禁止使用「完成」或同義說法。
Dependent scientific gate 只能在 upstream verified edge 後開始；terminal closeout
可以稍後合併，但不得把 preparation 或 implementation 誤標成 verified outcome。
