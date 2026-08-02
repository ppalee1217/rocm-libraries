---
name: implement-verify-loop
description: >-
  Executes risk-tiered engineering and experiment work from an approved design
  using Main-authored transient implementation and goal-oracle plans, a durable
  machine-readable frozen contract, reviewer-governed uncapped repair, and independent
  verification. Preserves hard scientific gates while allowing compatible
  gates to share an execution tranche and terminal closeout. Use for
  preregistered checkpoints with clear acceptance, evidence, authority, and
  report targets. Do not use to invent an ambiguous design or silently weaken
  a locked protocol.
---

# Implement and Verify Loop

<!-- BEGIN CODEX RUNTIME MAPPINGS -->
## Codex runtime mappings

- Treat `$ARGUMENTS` as the current user request plus any explicitly named design note,
  specification, scope, or report path.
- Treat `AskQuestion` as asking the user through the input mechanism available in the current
  Codex mode.
- Map `model: gpt-5.6-sol-xhigh` to `model: gpt-5.6-sol` with
  `reasoning_effort: xhigh`.
- Main agent must author `plan_b.md` and `plan_a.md` in its own thread. Never call
  `spawn_agent` for either planning role.
- Use `fork_turns: none` for every fresh implementer, verifier, auditor, or reviewer and
  provide the complete role-specific prompt and artifact paths explicitly.
- Create a fresh implementer and fresh verifier for every scientific gate. Treat repair
  `resume` as `followup_task` addressed to that gate's saved role ID.
- When the workflow calls for paired design or operational review, issue both `spawn_agent`
  calls before waiting for either result.
- Record the Codex task name or agent ID wherever the workflow asks for an agent link or ID.
- If the required model or subagent tools are unavailable, stop and report the limitation
  under this workflow's authority rules.
<!-- END CODEX RUNTIME MAPPINGS -->

Main agent 是 orchestrator：解析 authoritative bundle、凍結風險與 outcome contract、
保護 baseline、親自準備 Plan-A 與 Plan-B、管理有界角色與資源，並保存可追溯裁決與
證據。Main agent 不得把兩份 plan 委派給 planner subagent，也不得親自實作 source change。

Verifier `PASS` 只代表 technical verification 通過並進入
`VERIFIED_PENDING_CLOSEOUT`。正式 report、parent update、`CLOSEOUT_ACK`、
授權範圍內的 terminal commit 與 post-commit audit 都完成後，closure unit 才是
`COMPLETE`。Scientific outcome 可在 durable contract seal 後、terminal closeout
前判定；不得為等待文書 closeout 而改寫已觀察 outcome。

## Checkpoint authority and vocabulary

- `scientific_gate` 是預註冊 outcome、claim 或 authority decision 的硬邊；不得合併、
  重排或用共享 closeout 繞過。
- `execution_tranche` 是可共享 Main planning context、environment/setup、run root 與
  repair ledger 的一段相容工作。每個 scientific gate 仍有自己的 Plan-A、frozen
  Plan-B、fresh implementer 與 fresh verifier；只有同一 gate 的 repair 才 resume 原角色。
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
- Main agent 是唯一 Plan-A/Plan-B author；不得建立 planning subagent。R2/R3 另加一個
  fresh adversarial oracle/authority auditor，在 labels 前挑戰 frozen contract、
  Plan-B parity、lineage 與 authority，但 auditor 不得代寫 plan。
- 每個 scientific gate 使用一個 fresh implementer；Main agent 不實作。Repair resume
  同一 implementer，進入另一 gate 時不得沿用該 thread。
- Outcome-bearing R1-R3 必須由未參與該 gate 實作的 fresh verifier 驗證 frozen
  contract與Plan-B。Repair 可 resume 同一 verifier；若更換 verifier，replacement
  必須完整重驗。
- Verifier 依 frozen contract、frozen Plan-B 與 direct evidence 判斷，禁止讀取
  Plan-A，也不得依 implementer 選擇的步驟判斷。

## Unexpected experiment-design issue adjudication

只有執行中出現會實質改變 experiment protocol、measurement／claim boundary、lineage、
stopping rule 或 scientific authority 的 ambiguity，才使用 `design-discussion`。機械
修復、已有唯一 contract-preserving 答案、普通 code choice 或單純資源等待不觸發：

- 以完全相同、自足且不暗示偏好的 prompt，啟動兩個額外的 fresh
  reviewers，並套用該 skill 的 cap。
- 最多兩輪 cross-examination，再加一輪 evidence-backed final positions；全體 reviewer
  累計最多 60 agent wall-minutes。
- 不強迫 `AGREE`。在任一 cap 到達時停止辯論，保存雙方 dissent、共同點、evidence
  boundary 與最小 decision packet，交 human escalation。
- 這兩個 reviewers 不取代 Main plan author、oracle/authority auditor、implementer 或
  verifier，也不得直接修改 plan、implementation 或創造 authority。
- 無論雙方形成 unified conclusion 或 preserved dissent，Main agent 都先建立
  decision packet 並暫停 affected design path，等待使用者決定；雙方同意不能取代
  experiment-design authority。

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

### Experiment-design user-review boundary

- Experiment-design issue 必須把兩位 reviewers 的 unified conclusion 或 preserved
  dissent 交給使用者；在使用者批准前，不得修改或恢復 affected design path。這項
  gate 即使 consensus 保留現有 design 也適用，因為是否接受該 design interpretation
  由使用者決定。
- 任何時點只要 consensus 證明繼續工作必須**打破或修改原訂 plan/authority**，change
  packet 必須明列修改 frozen goal/contract、
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

## Non-design blocker operational adjudication

下列非 experiment-design 狀況若沒有唯一機械答案，且會使工作停止、需要在多個
contract-preserving 修復間選擇，或同一 finding 連續兩輪沒有 material progress，
啟動兩個 independent operational reviewers。Thread budget 有 headroom 時使用 fresh
threads；沒有 headroom 時 resume 兩個未參與該修復實作、彼此獨立的既有角色並揭露
prior roles，不得藉此重設或規避 thread cap：

- 兩方收到相同 neutral prompt、frozen contract、current diff、direct failure evidence
  與明確的 non-design boundary。
- 沿用 `design-discussion` 的最多兩輪 cross-examination、一次 evidence-backed final
  與 60 agent wall-minute 上限，但不得把 operational adjudication 寫成 scientific
  design authority。
- 兩方 `AGREE` 的 non-destructive、contract/authority-preserving action 已由 repository
  owner 預先授權；Main agent 記錄後直接執行，不再等待使用者。
- Responsible verifier／auditor 的具體 finding 若只導出一個 non-destructive、
  contract/authority-preserving 修復，該 finding 本身即是 reviewer support；不需為了
  repair 次數再啟動 dual review。只有多個 consequential 方向、authority 分類歧義或
  兩輪無 material progress 時才需要兩位 operational reviewers。
- 若兩方仍 dissent，Main agent 只能執行 frozen contract 與 direct evidence 唯一要求
  的最小、可逆、非破壞性方案。若沒有這種方案，才依實際性質轉入 experiment-design、
  missing-authority 或 safety gate；不得假造 unified conclusion。
- Ordinary deterministic fix 不需為了形式而啟動雙 reviewer。Operational reviewers
  不取代 fresh verifier。Repair count 只作 append-only provenance；新 thread、
  generation 或 successor 不得刪除歷史，但累計數字不形成 stop 或 approval gate。

## 實驗範圍外的 external workspace drift

Pre-existing path 在 workflow 期間被外部修改、新增或移除時，不以 global worktree
equality 當成實驗 gate。只有 direct evidence 同時證明下列條件，才分類為
`external_unrelated_drift`：

- path 不在 active implementation、execution-artifact、delivery、authority、source/input、
  evidence、lock、report 或 run-root boundary；
- path 未 staged、未進入 current exact commit，且 current workflow 沒有 command
  觸碰它；
- drift 不影響 dependency resolution、reproducibility、evidence、claim 或 closeout；
- 繼續工作不需要 restore、delete、quarantine、overwrite 或其他 path mutation。

符合時保留原 baseline 作歷史證據，append successor observation，記錄 exact path、
known prior state、current `lstat`/Git/index state、`UNKNOWN_EXTERNAL` attribution、
boundary check 與 exact-commit path proof；通知使用者後直接繼續，通知不是 approval
gate。不得更動該 path，也不得把 disappearance 解讀成 owner 已授權刪除。

若存在 scope overlap、current-workflow attribution、index/commit collision、
evidence/reproducibility impact、qualification 不完整，或必須更動該 path 才能繼續，
維持原 human/destructive authority gate。Post-commit audit 只要求 exact commit 與
experiment-relevant protected state 一致，不要求 unrelated external paths 全域不變。

## Scientific gates, execution tranches, and closure units

若 source spec 包含多個 ordered/dependent checkpoints：

1. 先建立 scientific gate DAG、hard edges、execution tranche 與 closure unit mapping。
2. Hard scientific edges 永遠不軟化：dependent gate 只有在 upstream outcome 已依
   frozen contract verified 後才可進入。
3. 相容 adjacent gates 可共享 Main planning context、environment/setup、run root、
   repair ledger，並在一個 terminal closeout 完成；每個 gate 仍保留獨立 Plan-A、
   frozen Plan-B、fresh implementer、fresh verifier、contract criterion、outcome、
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
    plan_a.md
    plan_b.md
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
4. 凍結三個 write boundaries：
   - `implementation_whitelist`：implementer可修改的source/test/config/design deliverables。
   - `execution_artifact_whitelist`：approved commands可建立或更新的exact transient
     build/run/scratch/log/raw/intermediate/final artifact paths；它們不是delivery，
     不得只因被列入此處就stage或commit。
   - `delivery_whitelist`：可在 terminal closeout stage/commit 的 exact durable paths，
     例如 implementation whitelist 中授權的 deliverables、formal report、parent
     checkpoint-specific hunk 及明確授權的 durable amendment/artifact；不得包含只屬於
     execution artifact whitelist 的 transient paths。
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
   - 三個write boundaries、formal report/parent path與禁止接觸的downstream paths。
10. 凍結 resource planning 與 material boundary：
    - 記錄 pre-empirical share、wall-time、CPU/GPU、storage、throughput assumptions、
      first-1% reforecast point、2x variance、預設5 GiB transient target與safe boundaries。
      這些預設是planning targets，不是hard gates。
    - Long-running work開始前通知使用者；planning target跨越時記錄並通知後繼續完整
      frozen workload。通知不是approval gate。
    - 同一scientific gate/lineage的known usage與parent／child／inclusive measurement
      boundary跨generation、successor、replacement role、restart與new root保留作
      best-effort provenance。不得刪除、補造或把`UNKNOWN`寫成0；historical cumulative
      total不單獨debit successor-entry authority。
    - 只有direct或materially indicative operational evidence連到unsafe continuation、
      external／platform／allocation限制、compute／memory／storage不足、完整workload／
      verification／closure／artifact preservation無法完成、label-dependent stopping／
      selection、required workload／claim change、evidence不可驗證，或approved pre-label
      design明確凍結的scientific resource boundary時，才是hard pause gate。Bare
      `UNKNOWN`、2x variance、internal planning-cap crossing或cumulative total不是此類
      evidence。不得只為完善記帳重跑outcome-bearing work。
    - Scientific sample／draw／seed／arm／population／generation／repetition caps、
      thread caps、repair-review gates、downgrade gates與evidence requirements不受本條放寬。
11. 從 approved design 擷取 durable machine-readable frozen contract，至少包含 gate
    ID/tier、labels、criteria、outcome/edge matrix、evidence/measurement/claim boundary、
    fixtures、lineage、implementation/execution-artifact/delivery whitelists、authority、
    repair ledger／reviewer policy、resource planning targets、
    任何explicit hard resource boundary、downgrade gate與lock identity。人工與機器
    表示必須可追溯；不一致時停止。
12. R2/R3 由 adversarial oracle/authority auditor 在 labels 前檢查 contract 完整性、
    post-label invariants、authority 與 claim boundary。修正後重新 hash。
13. Contract 與 lock 經 tracked commit 或 approved immutable mechanism seal 後，才允許
    outcome-bearing command 或 label access。Seal 後只能 escalation；修改需 R3 human gate
    與新 generation/amendment，不得覆寫舊 contract。
14. 保留所有 unrelated user changes與已通過 upstream changes；不可 reset、checkout、
    stash、覆蓋或順手整理。Baseline 是歷史 observation；符合
    `external_unrelated_drift` 的後續變動用 append-only successor observation 保存，
    不覆寫 baseline，也不把全域 equality 當 gate。
15. 每進入新 tranche 或 baseline drift 時重做 relevant capture；共享 tranche 不代表
    可沿用 stale evidence。

## Step 1：Main agent 建立 Plan-B 與 Plan-A

開始本 Step 前，完整讀取並套用
[Main-authored Plan-A / Plan-B contract](references/planning-contract.md)。
Main agent 親自建立兩份 transient artifacts，不得啟動 planner subagent：

1. 先只依 authoritative bundle 與 sealed durable contract 建立 verifier-facing
   `plan_b.md`。它描述 overall verification objective、required end state、acceptance
   evidence boundary、headline reproduction、allowed outcomes/edges 與 unacceptable
   fallbacks，不包含 per-file implementation steps。
2. R0/R1 由 Main agent 檢查 Plan-B 與 contract parity；R2/R3 另由既有 fresh
   adversarial auditor review。通過後記錄 SHA-256 並標示 `FROZEN`，才可開始 Plan-A。
3. Main agent 以 read-only inspection 查明 relevant code、tests、configs、fixtures、
   commands、environment 與 artifacts，建立 implementer-facing `plan_a.md`。
4. Plan-A 必須 decision-complete，並盡可能完整指定每個 code change 與實驗細節；
   不可把可查明的事留給 implementer 猜。沒有適用值的 required field 要寫 `N/A`
   與理由。
5. 只有 Plan-A 預先定義 candidate branches、investigation boundary、deterministic
   decision table、permitted changes 與 escalation triggers 時，implementer 才可執行
   bounded spike。

Plan-B 是 frozen goal/oracle view，Plan-A 是可 version 的 implementation/experiment
plan；兩者都不是 outcome authority，也不得覆蓋 durable frozen contract。

### Main agent plan gate

Main agent：

1. 確認 Plan-A 與 Plan-B 都忠於 frozen contract、whitelists、hard edges、resource
   planning targets 與任何 explicit hard resource boundary。
2. 確認 machine-readable contract 可獨立驗證 objective、positive/negative/inconclusive/
   blocked outcome、criteria、unacceptable fallbacks、evidence 與 next edge；不可把
   authority 只留在 natural-language plans。
3. 確認 Plan-B 在 Plan-A 之前完成 freeze，且沒有 Plan-A implementation choice 污染。
4. 確認 Plan-A 已列 exact implementation instructions、完整適用的 experiment
   parameters、commands、artifacts、self-checks 與 bounded-spike decision table。
5. R2/R3 必須取得 fresh adversarial auditor 的 `AUDIT_PASS`；finding 只可在 labels 前
   以 traceable contract/plan revision 修正。Labels 後只能依既有 R3 gate 處理。
6. 在 `adjudication.md` 記錄 Plan-A revision/hash、frozen Plan-B hash、contract hash、
   lock identity、tier、auditor result 與 `SEALED` state。

## Step 2：Fresh implementer 實作與執行

每個 active scientific gate 都啟動一個 fresh implementer。Main agent 不得親自實作，
另一個 gate 也不得沿用此 implementer；只有同一 gate 的 repair 才 resume 原 thread。
Implementer 收到完整 Plan-A、必要 frozen constraints、baseline 與 artifact paths，
不得讀取或接收 Plan-B，也不得取得修改 contract 或任何 plan 的 authority：

- 在 current workspace 實作 dependency-ready gate 的 Plan-A。
- 只修改 implementation whitelist、execution artifact whitelist 內的 exact paths，
  以及本 run 的 `impl_report.md`。
- 不得修改、補stub、順手抽象化或預建任何downstream checkpoint path/behavior。
- 先檢查檔案 current content，避免覆蓋 baseline 中的 user changes。
- Plan-A 留有 bounded spike 時，只能依其 candidate branches、deterministic decision
  table 與 permitted changes 選擇，並記錄 direct evidence 與理由。
- 遇到 Plan-A 未涵蓋、evidence ambiguous、或會影響 behavior/measurement/evidence/
  claim/contract/authority 的選擇時，不做 speculative change；回覆
  `BLOCKED_PLAN_GAP` 與 evidence。
- 執行 Plan-A 中可執行的 verification commands。
- 不得 commit、push、install dependency、存取 credentials 或做 external writes。
- 將每個 changed file、behavior、command、exit code、artifact、deviation、未完成項目寫入 `impl_report.md`。
- 回覆只包含 terse status、changed-file list 與 report path。
- 追蹤pre-empirical share；完成planned workload最初1%後，以observed throughput重估
  wall-time與storage。20%、2x、5 GiB或其他internal planning target跨越時記錄並通知，
  不等待approval且繼續完整frozen workload。
- Runtime duration、planning variance、missing telemetry或cumulative total本身不得
  optional stop或選擇性保留outcome。只有Step 0列出的material hard-pause evidence
  成立時，才在safe boundary暫停並提交decision packet；packet列live state、
  completed/missing work、projection、storage、可保留evidence、preserve-plan
  alternatives與downgrade impact。

Implementer 回覆後，Main agent：

1. 擷取相對 baseline 的 parent/submodule diff 與 status。
2. 檢查 whitelist、unrelated user changes 與意外 artifact。
3. 若有 whitelist 外 mutation，停止該 role、不得啟動 verifier 並保存 incident manifest：
   - 符合[workspace recovery standing authority](references/authority-gates.md)者，
     automatic 執行 deterministic exact quarantine 與 post-audit，不需 dual reviewers，
     再重做本 Step。
   - 符合[experiment-scoped external drift](references/authority-gates.md)者，不更動該
     path；append successor observation、通知使用者並以 experiment-scoped audit
     繼續本 Step。
   - 其他情況立即向使用者呈現delta；不可單方面revert、delete、stash、覆蓋或擴張whitelist。
4. 若 implementer 自己已知未完成，不啟動假驗證；先在 scope 內 resume implementer 補齊，或誠實升級。
5. `BLOCKED_PLAN_GAP` 時由 Main agent 先查明 evidence；只有能在 unchanged frozen
   contract 內決定時才建立有 revision/hash ledger 的新 Plan-A 並 resume implementer。
   若會改 contract、Plan-B 或 scientific design，改走既有 design/R3 authority gate。
   Plan gap 本身永遠不算 verifier repair round；resume 後若 verifier 產生 finding，
   只有該完整 implement→verify cycle 才追加一筆 repair provenance。同一 Plan-A gap 連續兩次
   沒有 material progress 時，先走 non-design operational adjudication，再決定是否
   還有 authority-preserving path。

## Step 3：Fresh verifier 依 frozen contract 驗證

Outcome-bearing R1-R3 gate 必須啟動未參與該 gate implementation 的 fresh verifier。
R0 可依風險由 Main agent 做 deterministic check。Verifier 收到：

- Durable frozen contract/lock 與 exact seal hash。
- Frozen `plan_b.md` 與 exact SHA-256。
- Baseline references。
- Current implementation diff 與 changed paths。
- Source/test/artifact paths。
- `impl_report.md` 作為待查證的 claim，不是 ground truth。
- 下列 verifier contract。

Verifier 明確禁止讀取或接收 `plan_a.md`。Acceptance 由 frozen contract 決定，Plan-B
只提供 goal/oracle view；不得因 implementer 選擇而改 goal、threshold、evidence
boundary 或 outcome matrix。Plan-B 與 contract 不一致時必須 fail closed。

Verifier contract：

- 不修改 source、tests、configs、approved design、frozen contract 或 lock。
- 只可寫本 run 的 `verify_report.md`、`verdict.json`，以及明確允許且列在
  execution artifact whitelist 的 reproduction artifacts。
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
  完整，且沒有未處理的material hard resource boundary或downgrade。符合Step 0
  resource-materiality條件的non-blocking accounting caveat必須記錄，但不單獨阻止
  technical `PASS`。

## Step 4：Adjudicate 與修正迴圈

Main agent 每輪將以下內容追加到 `adjudication.md`：

- Iteration number、risk tier、Plan-A revision/hash、frozen Plan-B hash 與 frozen
  contract/lock hash。
- Implementer changed paths 與 evidence。
- Verifier verdict、blocking finding IDs 與 evidence requests。
- Main agent 的判斷、下一步與未解風險。

Repair round 是一個 verifier finding 被送修、實作回應並重新驗證的完整 cycle：

- R0、R1、R2、R3 的 repair rounds 全數追加記錄，但沒有 numeric maximum；repair
  count 不得成為 stop、approval、success 或 completion gate。
- Responsible verifier／auditor 已確認且只有一個 contract-preserving 修復時直接執行；
  多個 consequential 方向或 authority 分類歧義由兩位 operational reviewers 裁決。
  兩位同意修復必要且不改 experiment design 時直接執行，不需 human approval。
- 同一 finding 連續 2 rounds 沒有 material progress時，先執行 non-design dual-agent
  operational adjudication，再決定下一個 contract-preserving 修復；不得只因這個訊號終止整體
  goal。
- Generation、successor、renaming、replacement、role/thread restart 或搬到新 run root
  都不能刪除或重寫歷史計數。
- 同一 gate/lineage 累計 fresh role threads 上限：R2 = 5，R3 = 6。Implementer、
  auditor、verifier/replacement 與 design reviewers 都計入；不得用新 thread 規避
  independence 或 reviewer gates。

### Technical PASS

只有 verifier 回覆合格 `PASS` 時：

1. 再次檢查 frozen contract/lock hash 未變。
2. 確認 working tree 沒有 verifier 或其他角色造成的越界 source change。
3. 確認沒有 unresolved experiment-relevant whitelist 外 artifact；曾使用 standing
   recovery 時，其 qualification、quarantine／absence hash、full status 與
   unrelated-change post-audit 必須完整。符合 `external_unrelated_drift` 的 path 必須有
   successor observation 與 experiment-boundary proof，但全域 workspace equality 不是
   PASS 條件。
4. 確認active checkpoint沒有downstream speculative change。
5. 記錄technical `CONSISTENT`、scientific outcome與verified outgoing edges。
6. 將 gate state 設為 `VERIFIED_PENDING_CLOSEOUT`。符合 frozen hard edge 的 adjacent
   gate 可在同一 tranche 繼續；closure unit 尚不可宣告 complete。

### CHANGES_REQUIRED

1. Main agent 依 direct evidence 判斷 findings 是否具體、是否在 scope 內。
2. 若 finding 只有唯一、contract-preserving 的 in-scope 修復，且 responsible
   verifier／auditor 確認需要，直接進入原 implementer/verifier repair loop；不檢查
   numeric repair cap。
3. 若 finding 暴露 material experiment protocol/claim/lineage/stopping-rule/
   scientific-authority ambiguity，先依 `Unexpected experiment-design issue
   adjudication` 完成 dual-agent `design-discussion`，再將結論交使用者；不得先改
   source 或 authority。
4. 若是多個 consequential、contract-preserving 的非設計修復方向，或同一 finding
   已兩輪無 material progress，依 `Non-design blocker operational adjudication`
   取得預授權結論後繼續。
5. 若 required change 需要不同 implementation instructions，Main agent 先依
   [planning contract](references/planning-contract.md)建立 contract-preserving
   Plan-A revision；不得讓 implementer 自行解讀或修改 plan。
6. 將 blocking IDs、`verify_report.md`、current changed paths 與完整 current Plan-A
   resume 給原 implementer；不得提供 Plan-B。
7. Implementer 修正後更新 `impl_report.md`，並只回傳短 status 與 paths。
8. Main agent 再做 whitelist/baseline check。
9. Resume 原 verifier：
   - 提供 addressed finding IDs、new diff、commands/artifacts 與 remaining uncertainties。
   - 提供 frozen Plan-B 與 contract hashes；不得提供 Plan-A 或 Plan-A summary。
   - 要求重新讀 current files 並 fresh rerun relevant checks。
   - 不可只相信 repair summary。
10. 在 thread budget 與 reviewer governance 內重複。不得因 repair 累計數字、普通
   `CHANGES_REQUIRED`、可修復 test failure 或非實質資源記帳問題提前結束；只有沒有
   reviewer-supported authority-preserving path 時才 honest exit，不得自動開 generation
   重算。

修正迴圈期間 active gate 不變；只有邊界完全獨立且 label-blind 的 preparations 可平行。

### BLOCKED 或 evidence request

- Main agent 可執行短、可逆且在授權範圍內的 evidence command，並記錄 exact command、cwd、exit code 與 artifacts，再 resume verifier。
- 遇到 material experiment protocol/claim/lineage/stopping-rule/scientific-authority
  ambiguity，走 bounded dual-agent `design-discussion` 並一律將結論交使用者；
  deterministic disposable artifact recovery 與 qualified `external_unrelated_drift`
  依 reference 自動處理。
- 非設計 blocker 先依 operational adjudication 使用既有 authority 自主解決。只有
  experiment-design decision、缺少 destructive/external/platform authority、hard
  safety/scientific boundary，或 reviewers 確認沒有有效 authority-preserving path
  時才停止 affected path。
- 若環境無法取得必要 evidence，terminal state 是 `BLOCKED`，不是 `PASS`。
- `BLOCKED` 或 evidence request 停止該 dependency path 的 outcome-bearing work；只允許
  邊界不重疊的 independent label-blind preparation。

### Honest exits

Thread cap 已達且現有獨立角色也無法完成 required review、dual-agent operational
adjudication仍找不到 authority-preserving 路徑、experiment-design decision等待使用者、material resource
gate暫停後無approved decision、所需工作／硬體／資料／環境超出scope、現有evidence
無法判定，或只支持inconclusive而不足以支持原claim時，停止affected path並誠實升級，
不假裝完成。Repair 累計數字本身永遠不是 honest-exit 條件；同一finding兩輪無progress
只是強制adjudication訊號，不單獨構成 terminal exit。

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
[authority gates, experiment-scoped drift, and `/data1/perlee` workspace recovery](references/authority-gates.md)。
該reference保存原有human gates，並記錄repository owner已授權的
experiment-scoped external drift 與窄範圍 current-run artifact recovery；不得只讀
本節摘要後擴張其scope。

## 文件與 evidence 規範

### Formal report readability 與 post-closeout editorial revision

Formal report 同時服務第一次閱讀的工程師與需要重現證據的稽核者。證據完整不等於把 execution ledger 當成主敘事；先建立可理解的主線，再保留完整稽核細節：

#### Reader-facing terminology and dataflow contract

這份 clarity contract 不只管 formal report；在本 workflow 產生的 general chat Q&A、
report、guide、review、plan 與 experiment explanation 都適用：

- 中央且非簡單的 term 第一次出現時，必須解釋它指哪個 object、role/purpose、
  inputs/outputs 或 contents、位於 current flow 哪裡、讀者為何需要在意、以及一個
  concrete example；有常見混淆時再給 non-example。只寫 3-6 字 gloss、只展開 acronym，
  或改用另一個 jargon 都不算 definition。Simple term 可以保持簡短。
- Acronym 第一次出現時展開；`R2`、`PASS`、`W7` 等 status/ID 必須另用文字說明意義。
- 使用 `10 configs × 3 sizes = 30 rows` 之類 compact notation 前，先定義 `config`、
  `size`、`row`，給一個 concrete pairing，並說明它們是 independent units 還是同條件
  repetitions；repetition count 另列。
- Central formula 必須定義每個 symbol、unit、higher/lower 哪個較好、constant 的來源，
  並給一個 worked numerical example。
- 對 `mandatory atom`、`fresh witness`、`conditional target`、`valid support` 或任何
  set/classification，說明 membership rule、誰在何時 create/select、哪個 downstream
  actor 如何 consume，以及 membership **不能**支持哪個 conclusion。
- Dataflow 一律寫成 **actor -> action -> input -> output -> next consumer**。明說資訊由誰
  produce，下一階段用它做哪個 lookup、decision、validation 或 transformation；不可停在
  「used downstream」。
- 若使用者說看不懂，回到更簡單的 mental model/analogy 再逐步重建；不可只換句話重複
  同一批 terms。
- 分開標示 planned behavior、live observation 與 committed result；同時分開 technical
  `PASS` 與 positive/negative/inconclusive scientific outcome。
- 當 central terms 多到 inline definitions 會打斷主線時，formal report 必須在 metrics
  之前放一小節讀者導向的「名詞與資料流」。Audit appendix 只有在 main explanation 已
  self-contained 且通過下方 audit 後，才可以維持 technical-only 寫法。

**Anti-pattern：**

```text
10 configs × 3 sizes = 30 rows。Fresh witness 覆蓋 mandatory atom，供 downstream 使用。
```

這段沒有定義計數單位、independence/repetition boundary、classification rule、producer、
consumer、exact use 或不支持的結論。

**Good count example：**

```text
Config 是一組完整的待比較設定；例如 C03 用 256 個 GPU threads 計算
128-by-128 output block。Size 是一組輸入形狀；例如 S02 將 1024-by-512 matrix
與 512-by-1024 matrix 相乘。Row 是一個 config-size pairing 的一筆結果；
例如 R08 記錄 C03 在 S02 的結果。
所以 10 configs × 3 distinct sizes 形成 30 個獨立指定的 pairings，不是同一條件
重複 30 次；每個 pairing 內的 timing repetitions 另外計數。
```

**Good classification/dataflow example：**

```text
以下是 toy protocol，不是 project term 的預設定義：design author 在結果可見前，
把 mandatory atom A 放入 frozen required set。Runner 讀取 A 的 evidence rule，
並在 freeze 後產生 observation W7。只有 W7 未被用來選 A 且符合該 rule 時，
W7 才是 A 的 fresh witness。Run 結束後，verifier 只有在該 rule 通過時才把
W7 classify 為 valid support；claim evaluator 再把 A 計為有合格 evidence。
這只支持 A，不證明整體 hypothesis。Design author 也在結果可見前預先宣告
conditional target T；scheduler consume A 的 verdict，只在 A 通過後啟用 T。
啟用不代表 T 已通過。
```

Reader-facing self-audit：

- [ ] 第一次閱讀者能對每個 central term 回答 what、why、how、example、downstream
      consumer/exact use，以及 not-implied conclusion。
- [ ] 沒有 unexplained acronym、status ID、set membership 或 compact count notation。
- [ ] Central formula 的 symbols、units、direction、constant sources 與 worked example 完整。
- [ ] Main explanation 本身 self-contained；technical appendix 不是用來補救主文缺少的解釋。

- 報告開頭先用繁體中文白話回答五件事：這一關要驗什麼、實際看到什麼、為什麼得到這個判決、證據能與不能支持什麼，以及下一個合法 checkpoint 是什麼。
- 第一個畫面內用表格或短清單分開 technical verification、scientific outcome、checkpoint state、criterion、failure ID 與 outgoing edge。Technical `PASS` 和 scientific positive／negative 不得混為同一件事。
- 有三個以上步驟的流程使用精簡 Mermaid flowchart 或編號流程。
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
Plan-A revision/hash、frozen Plan-B hash、changed files、fresh verifier commands、
technical verdict、scientific outcome、formal report、`CLOSEOUT_ACK`、closure commit
SHA、post-audit、verified edge、evidence boundary 與 risks。只有 required closure
units 經 post-commit audit `COMPLETE`，或 gates 依 verified edge 合法
skip/not-activate，才能宣告整體完成；否則列出 technical/closeout state、blocking
evidence、未開始的 downstream 與需要使用者決定的下一步。

Closure unit 沒有 post-audited terminal commit 時，禁止使用「完成」或同義說法。
Dependent scientific gate 只能在 upstream verified edge 後開始；terminal closeout
可以稍後合併，但不得把 preparation 或 implementation 誤標成 verified outcome。
