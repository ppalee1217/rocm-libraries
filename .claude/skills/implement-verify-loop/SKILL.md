---
name: implement-verify-loop
description: >-
  Implements, independently verifies, reports, and commits exactly one stable
  checkpoint indexed by an authoritative parent experiment plan, using two
  independent planners, a fresh implementer, and a fresh verifier. Routes
  consequential design issues through two additional fresh design-discussion
  subagents until both confirm one consensus. For a multi-checkpoint
  experiment, repeats the full plan → implement → verify/fix → report → parent
  update → closeout audit → commit loop sequentially; never starts downstream
  work before the active checkpoint is committed and audited. Use for
  experiment checkpoints with complete acceptance criteria and report targets.
  Do not use for initial design, rules maintenance, trivial edits, or ambiguous
  goals.
---

# Implement and Verify Loop

Main agent是orchestrator：從authoritative parent experiment plan選出唯一active checkpoint、保護baseline、管理四個GPT-5.6 Sol subagents並保存可追溯裁決與證據。

Verifier `PASS` 只代表 technical verification 通過並進入
`VERIFIED_PENDING_CLOSEOUT`。正式 report、parent update、`CLOSEOUT_ACK`、
checkpoint-only commit與post-commit audit都完成後，才是 `CHECKPOINT_COMPLETE`。
多 checkpoint request 絕對不是批次實作或批次驗證；前一個未
`CHECKPOINT_COMPLETE` 時不得開始或修改 dependent checkpoint。

## Checkpoint authority and vocabulary

- Canonical execution unit是parent experiment plan index中的stable checkpoint。
  `step`與`milestone`只有指向該indexed checkpoint時才是alias；名稱是day、stage或
  subtask不自動納入或排除。
- Parent plan與其明確引用的checkpoint design形成authoritative bundle。開始前必須
  唯一解析ID、goal、DAG/gates、acceptance/oracle、evidence/claim boundary、
  report或blocker target、status/outcome vocabulary、implementation whitelist、
  delivery whitelist與scoped commit authority。
- 每個checkpoint開始時重新讀current committed general rule與本skill並記錄revision
  hash。Latest rule是orchestration/completion floor，但不能靜默改scientific
  hypothesis或threshold；locked design衝突時先建立traceable amendment或new
  effective lock。
- 缺少或有多個合理parent、checkpoint、report target或其他authority欄位時停止釐清；
  不可由subagent consensus發明使用者意圖。

## Model and independence policy

- 所有 fresh subagents 都明確使用 `model: gpt-5.6-sol-xhigh`。
- 若該 model 無法使用，停止並告知使用者；不可靜默換 model。
- 每個active checkpoint使用四個不同fresh threads：Plan-A planner、Plan-B planner、
  implementer與verifier。
- Implementer 與 verifier 在修正迴圈中各自 resume 原 thread，以保留角色脈絡。
- 進入下一個checkpoint時四個角色全部重建fresh threads；不可沿用上一個checkpoint。
- Verifier 永遠不可讀 `plan_a.md`；它依 goal 判斷，不依 implementer 選擇的步驟判斷。
- Plan-B planner 永遠不可讀或接收 Plan-A。

## Unexpected design issue adjudication

執行中若出現原計畫未預見的 consequential design issue，不要立刻把問題丟回使用者，
也不要由 Main agent 單方面選修復方向。先使用 `design-discussion`：

- 以完全相同、自足且不暗示偏好的 prompt，啟動兩個額外的 fresh
  `gpt-5.6-sol-xhigh` subagents。
- 讓兩個原 threads 獨立提出立場，再互相交互詰問、補 factual evidence、修正立場，
  直到雙方對同一份 candidate consensus 都明確回覆 `AGREE`。
- 這兩個 design reviewers 不取代 Plan-A planner、Plan-B planner、implementer 或
  verifier，也不得直接修改 implementation。
- Main agent 將 consensus、捨棄方案、assumptions、evidence boundary 與 repair
  protocol 寫入 design/adjudication artifact，再判斷是否可繼續。

適用情況包括：

- Verifier finding 暴露 lifecycle、lock、authority、evidence integrity 或 recovery
  protocol 的設計缺口。
- 一個 `CHANGES_REQUIRED` finding 有數個合理修復方向，且選錯會改變 lineage、
  measurement boundary 或後續可接受 claim。
- Checkpoint 的 negative、counterintuitive 或 ambiguous result需要重新判斷原
  hypothesis、gate edge 或 implementation architecture。

若 finding 只有一個明確、Plan-A whitelist 內且不改原計畫語意的機械式修復，直接
resume 原 implementer/verifier，不需啟動 design discussion。

### Consensus 後的 user-review boundary

- 若 consensus 完整保留原訂 plan、frozen Plan-B、acceptance、evidence source、
  report target、checkpoint DAG/gates、whitelist/authority invariants 與 claim
  boundary，Main agent 記錄裁決後直接繼續，不需再向使用者尋求同意。
- 任何時點只要 consensus 證明繼續工作必須**打破或修改原訂 plan/authority**，才將
  consensus與change packet交給使用者審查。這包括修改frozen goal、
  acceptance/threshold、planned evidence、report target、checkpoint order/gate、
  preregistered fixture/measurement boundary、approved whitelist、immutable
  lock/lifecycle invariant或允許的 claim。
- `CHANGES_REQUIRED` 本身不等於 plan change。保留原 acceptance 的 in-scope repair、
  fresh rerun、同 lineage role resume或原計畫已定義的 negative branch都不需重複
  human approval。
- 若兩個 reviewers 的剩餘分歧本質上是上述 plan-changing trade-off，或使用者偏好，
  才升級；不可因討論輪數、agent 語氣或想快速結束而提早詢問使用者。
- 每個agent-decided issue都寫入`adjudication.md`，並在formal report中materialize；
  實際使用design discussion時另記雙方objections、採納/捨棄、consensus與兩個
  `AGREE`。不可只連到transient artifact。
- Consensus不能創造push、credentials、external-system write、dependency install、
  container mutation或其他缺少的platform authority。

## Multi-checkpoint sequencing：hard gate

若 source spec 包含多個 ordered/dependent checkpoints：

1. 先建立dependency DAG與deterministic order，但只選一個dependency-ready
   checkpoint為active。
2. Active checkpoint必須有自己的baseline、Plan-A、frozen Plan-B、implementer、
   verifier、formal report、parent update、delivery manifest、verdict與closeout audit。
3. Implementer只可修改active implementation whitelist；future/downstream source、
   test、schema、runner、analysis或report都不可預先實作。
4. Verifier必須在implementer交付後立刻驗active checkpoint；不可等其他checkpoints
   一起完成才驗。
5. `CHANGES_REQUIRED`時只修active checkpoint，直到verifier technical `PASS`或honest exit。
6. `BLOCKED`、`FAIL`、missing evidence、still-running verification 或 human gate 都會停止該 dependency path；不得以「先做後面可獨立的部分」為由繞過。
7. 只有active checkpoint達到`CHECKPOINT_COMPLETE`後，Main agent才能依verified gate
   outcome選下一個dependency-ready checkpoint並重建四個fresh threads。
8. Negative/falsified outcome若evidence與gate decision正確仍可technical `PASS`；
   只沿design明定edge前進。`skipped_by_gate`由上游report、parent update與closure
   commit保存，不替未執行checkpoint建立假report。

## Run directory

每次執行使用 repo root 下的：

```text
agent_run/YYMMDD-{feature-slug}[-N]/
```

單一 checkpoint 至少保存原有 flat artifacts。多 checkpoint run 則使用：

```text
baseline.md
milestone-order.md
adjudication.md
subagents.md
milestones/
  <milestone-id>/
    baseline.md
    plan_a.md
    plan_b.md
    impl_report.md
    verify_report.md
    verdict.json
    closeout.md
    delivery-manifest.txt
```

- `agent_run/` 是 transient evidence，不得 commit。
- 開始前用 `git check-ignore` 確認它已被忽略。
- 若未被忽略，先取得使用者同意才可新增 ignore rule；不可靜默修改 ignore 設定。
- `milestone-order.md` 記錄 DAG、active checkpoint、verified upstream gates、eligible next edges；不得預先把 future checkpoint 標成 in progress。
- 每個 subagent 的 checkpoint、model、role、agent link/ID 與 artifact path 記在 `subagents.md`。
- 完整內容寫入 artifact；subagent 回覆 Main agent 時只回傳短 status、changed files、verdict 與 artifact paths。

## Step 0：解析需求、scope 與 baseline

1. 由`$ARGUMENTS`與authoritative bundle解析唯一parent plan、checkpoint design與ID；
   不可發明spec、report或blocker path。
2. 讀latest committed repo rule、本skill、parent/design、相關code/tests，記錄revision/hash；
   有locked conflict先traceable alignment。
3. 解析checkpoint DAG、gate branches、acceptance/oracle、evidence/claim boundary、
   status/outcome vocabulary、report/blocker target與terminalization policy。
4. 凍結兩層whitelist：
   - `implementation_whitelist`：implementer可修改的source/test/config/design deliverables。
   - `delivery_whitelist`：前者加formal report、parent checkpoint-specific hunk及明確
     授權的durable amendment/artifact。
5. 確認scoped commit authority。此repository general rule已授權本experiment sequence
   每checkpoint一個isolated closure commit；push仍未授權。
6. 選出唯一dependency-ready active checkpoint並列downstream為out of scope；有實質
   歧義時先詢問使用者。
7. 建立run directory與checkpoint evidence directory。
8. 開始前將以下baseline寫入`baseline.md`：
   - Parent repo 與 relevant submodules 的 current branch/commit。
   - `git status --short`。
   - Existing staged、unstaged 與 untracked paths。
   - 已完成upstream checkpoints的commit、verdict與report identity。
   - 兩層whitelist、formal report/parent path與禁止接觸的downstream paths。
9. 保留所有 unrelated user changes與已通過 upstream changes；不可 reset、checkout、stash、覆蓋或順手整理。
10. 每進入下一個checkpoint都重新執行本Step，不沿用stale baseline。

## Step 1：並行產生兩份獨立計畫

只針對active checkpoint建立一份`BASE REQUIREMENTS` block，內容包含：

- Repo root、source note/spec 路徑與必要 context。
- Active checkpoint ID、main objective 與 scope。
- Authoritative parent/design、formal report path、implementation/delivery whitelists與
  scoped commit authority。
- Verified upstream gate evidence、允許的 dependency edge 與 downstream exclusion。
- Required behavior 與 acceptance criteria。
- Constraints、compatibility boundaries 與禁止事項。
- Known user changes、可用環境、evidence/artifact paths。
- 明確說明只負責 planning，不實作 source change。

Plan-A 與 Plan-B planners 必須收到內容完全相同的 `BASE REQUIREMENTS`。
只有附加在後面的 role instructions 不同。
在同一個並行啟動動作中建立兩個 fresh planners。
Plan-A與Plan-B都不得把future checkpoint納入active checkpoint的implementation或
acceptance；必要共用元件必須能直接追到active checkpoint criterion。

### Plan-A planner：implementation plan

只允許寫入本次的 `plan_a.md`。
要求內容：

- Objective 與 scope restatement。
- Exact implementation whitelist 或清楚的 whitelist scope。
- Whitelist只能服務active checkpoint；明列所有downstream paths為禁止修改。
- 每個檔案預計修改的 symbol、anchor、behavior 與 reuse pattern。
- 若需 spike，列出 hypotheses、調查位置、decision criteria 與可接受邊界。
- Compatibility、error handling、data/measurement boundary。
- Implementer 可執行的 verification commands 與預期可觀察結果。
- Implementer 不能執行而需 verifier/使用者提供的 evidence。
- `impl_report.md` 必須記錄的內容與 deviation policy。

Plan-A 必須盡量具體，但不可偽造尚未查證的 code path、command 或行號。

### Plan-B planner：frozen goal/oracle plan

明確禁止讀取 `plan_a.md`，只允許寫入本次的 `plan_b.md`。
要求內容：

- Main objective：這個 change 根本要達成什麼。
- Desired end-result：使用者可以觀察到的最終狀態。
- Active checkpoint的completion correctness與scientific outcome要分開：
  negative/falsified outcome若符合design，也必須驗evidence與gate decision，不能硬改
  成effect PASS。
- Positive、negative、inconclusive、blocked與gate-skip的預註冊outcome/next-edge matrix。
- Acceptance criteria：
  - 每項 required behavior 的直接 evidence。
  - Headline acceptance check 的 fresh reproduction 方法。
  - Compatibility、regression、edge case 與 reproducibility 要求。
- Unacceptable fallbacks：
  - Partial result 被包裝成 complete。
  - 只相信 implementer report 而未重現。
  - 透過改測試、放寬 threshold 或改 goal 讓結果通過。
  - 使用不相同 measurement boundary 的 metrics 做比較。
  - 從單一、過窄或不完整 evidence 過度下結論。
- 從 current state 到 goal-achieved 的可接受方向，但不可提供逐步實作方案。
- 需要 verifier 自己讀取的 code、test、raw artifact 與 report boundary。

Plan-B是active checkpoint的goal oracle，不得包含Plan-A的file-by-file steps，也不得把
downstream checkpoint outcome當成本checkpoint通過條件。

### Main agent plan gate

兩個 planners 完成後，Main agent：

1. 讀取兩份計畫，確認都忠於原始需求。
2. 確認 Plan-A 有 whitelist 與可執行自驗。
3. 確認 Plan-B 是 goal-based、可驗證且沒有 Plan-A 污染。
4. 若有缺漏，resume 對應 planner 修正；不得讓兩個 planners 互讀。
5. Plan-B 通過 gate 後，在 `adjudication.md` 記錄其 hash 並標示 `FROZEN`。
6. Frozen 後不可為了讓實作過關修改 Plan-B。
7. 只有證明原始 goal 本身錯誤或矛盾時才可提議改 Plan-B，而且必須先由使用者批准並留下理由。

## Step 2：Fresh implementer只執行active checkpoint Plan-A

啟動第三個 fresh GPT-5.6 Sol subagent。
它只收到完整 Plan-A 與下列 execution contract，不收到 Plan-B：

- 在current workspace實作active checkpoint Plan-A。
- 只修改 implementation whitelist 內的 paths，以及本 run 的 `impl_report.md`。
- 不得修改、補stub、順手抽象化或預建任何downstream checkpoint path/behavior。
- 先檢查檔案 current content，避免覆蓋 baseline 中的 user changes。
- Plan-A 留有 spike 時，在 goal、direction 與 decision criteria 內完成探索並記錄選擇理由。
- 執行 Plan-A 中可執行的 verification commands。
- 不得 commit、push、install dependency、存取 credentials 或做 external writes。
- 將每個 changed file、behavior、command、exit code、artifact、deviation、未完成項目寫入 `impl_report.md`。
- 回覆只包含 terse status、changed-file list 與 report path。

Implementer 回覆後，Main agent：

1. 擷取相對 baseline 的 parent/submodule diff 與 status。
2. 檢查 whitelist、unrelated user changes 與意外 artifact。
3. 若有 whitelist 外修改，立即停止並向使用者呈現 delta；不可自動 revert。
4. 若 implementer 自己已知未完成，不啟動假驗證；先在 scope 內 resume implementer 補齊，或誠實升級。

## Step 3：Fresh verifier立刻依active checkpoint frozen Plan-B驗證

啟動第四個 fresh GPT-5.6 Sol subagent。
它只收到：

- Frozen `plan_b.md`。
- Baseline references。
- Current implementation diff 與 changed paths。
- Source/test/artifact paths。
- `impl_report.md` 作為待查證的 claim，不是 ground truth。
- 下列 verifier contract。

明確禁止 verifier 讀取 `plan_a.md`。

Verifier contract：

- 不修改 source、tests、configs、design docs 或 Plan-B。
- 只可寫本 run 的 `verify_report.md`、`verdict.json` 與明確允許的 reproduction artifacts。
- 重新讀 current code 與 surrounding call paths。
- 逐項以 direct evidence 判斷 Plan-B acceptance criteria。
- 確認diff只包含active checkpoint implementation whitelist，且沒有downstream
  speculative implementation。
- 自己 fresh reproduce headline acceptance check，不可只採信 implementer 結果。
- 檢查 regression、compatibility、edge cases、measurement comparability 與 unacceptable fallbacks。
- 若 command 會修改 source 或需權限、network、credentials、dependency install、長時間資源，列為 evidence request，不可自行越權。
- 回覆只包含 `verdict`、`goal_alignment`、blocking count 與 artifact paths。

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

## Step 4：Adjudicate 與修正迴圈

Main agent 每輪將以下內容追加到 `adjudication.md`：

- Iteration number 與 Plan-B frozen hash。
- Implementer changed paths 與 evidence。
- Verifier verdict、blocking finding IDs 與 evidence requests。
- Main agent 的判斷、下一步與未解風險。

### Technical PASS

只有 verifier 回覆合格 `PASS` 時：

1. 再次檢查 Plan-B hash 未變。
2. 確認 working tree 沒有 verifier 或其他角色造成的越界 source change。
3. 確認active checkpoint沒有downstream speculative change。
4. 記錄technical `CONSISTENT`、scientific outcome與verified outgoing edges。
5. 將state設為`VERIFIED_PENDING_CLOSEOUT`並進Step 5；禁止宣告checkpoint完成或選下一個。

### CHANGES_REQUIRED

1. Main agent 依 direct evidence 判斷 findings 是否具體、是否在 scope 內。
2. 若 finding 只有唯一、plan-preserving 的 in-scope 修復，直接進入原
   implementer/verifier repair loop。
3. 若 finding 暴露 consequential design ambiguity、authority/recovery 缺口或多個
   合理方向，先依 `Unexpected design issue adjudication` 完成 dual-agent
   `design-discussion`；不得先改 source 或 authority。
4. Consensus 保留原計畫時，Main agent 記錄後直接執行；consensus 必須打破或修改原
   plan 時，才提交使用者審查並等待決定。
5. 將 blocking IDs、`verify_report.md`、required changes 與 current changed paths resume 給原 implementer。
6. Implementer 修正後更新 `impl_report.md`，並只回傳短 status 與 paths。
7. Main agent 再做 whitelist/baseline check。
8. Resume 原 verifier：
   - 提供 addressed finding IDs、new diff、commands/artifacts 與 remaining uncertainties。
   - 要求重新讀 current files 並 fresh rerun relevant checks。
   - 不可只相信 repair summary。
9. 重複直到 verifier 給出合格 `PASS`。

修正迴圈期間active checkpoint不變；不可一邊修finding，一邊開始下一checkpoint。

### BLOCKED 或 evidence request

- Main agent 可執行短、可逆且在授權範圍內的 evidence command，並記錄 exact command、cwd、exit code 與 artifacts，再 resume verifier。
- 遇到 consequential design/recovery問題先走 dual-agent `design-discussion`；若
  consensus 不修改原 plan，記錄後直接繼續，不把普通 repair 當成 human gate。
- 只有consensus顯示繼續必須改原plan/authority，或操作需要尚未取得的
  external/platform authority，才詢問使用者。
- 若環境無法取得必要 evidence，terminal state 是 `BLOCKED`，不是 `PASS`。
- `BLOCKED`或evidence request停止該dependency path；不可先實作downstream checkpoint。

### Honest exits

五次iterations仍未PASS、同一finding連續兩次無progress、所需工作/硬體/資料/環境超出
scope、現有evidence無法判定，或只支持inconclusive而不足以支持原claim時，停止並誠實
升級，不假裝完成。

## Step 5：Formal report、parent update、closeout 與 commit

Technical `PASS`後依序完成：

1. Main agent依planned path建立self-contained formal report，逐項回答frozen Plan-B，
   並將所有material adjudication從transient evidence整合進report。
2. 只更新authoritative parent的checkpoint status/outcome、report link、verified
   outgoing edges、gate-resolved downstream states與residual risk；不可趁closeout改
   hypothesis、threshold、DAG或authority。
3. 只stage frozen delivery whitelist。Shared parent若含unrelated hunks，安全
   hunk-isolate；無法拆分就停止。不可使用`git add -A`、`git add .`或
   `git commit -a`，也不可alter既有unrelated index entries。
4. 從排序後的staged path、mode與blob OID產生`delivery-manifest.txt`及SHA-256，並將
   path-limited cached diff、report、parent與manifest交原verifier做read-only
   closeout audit。
5. Verifier確認report忠於direct evidence、parent與gate一致、staged bytes等於delivery
   whitelist且無unrelated/downstream內容後，回`CLOSEOUT_ACK`。Verifier不得修改tracked
   files；文書缺漏由Main agent修後重查。
6. 若closeout揭露source/evidence問題，technical `PASS`失效並回原
   implementer/verifier loop。原verifier永久不可resume時，replacement必須從frozen
   Plan-B完整重驗後才能audit closeout。
7. 使用exact delivery paths做path-limited commit；commit message含：

   ```text
   Checkpoint: <stable-id>
   Checkpoint-State: COMPLETE
   Experiment-Report: <repo-relative-path>
   Plan-B-SHA256: <sha256>
   Delivery-Manifest-SHA256: <sha256>
   ```

8. Commit後用`git show`/`git diff-tree`確認paths與content identity符合manifest，
   unrelated working-tree/index changes仍保留；將actual commit SHA與audit寫入
   transient `closeout.md`及final handoff。
9. 只有commit與post-audit成功才標`CHECKPOINT_COMPLETE`。Commit失敗或audit不符時留在
   `VERIFIED_PENDING_CLOSEOUT`，不開始dependent checkpoint。

Outcome/document matrix：

- Technical `PASS`搭配positive、negative或inconclusive outcome都走完整Step 5；
  `PASS`不代表scientific positive。
- Durable terminal `BLOCKED`只有在Step 0預註冊terminalization condition、blocker memo
  path與blocked-state commit policy時，才建立memo與parent blocked update並isolated
  commit。它不是formal experiment report或completion，不解鎖dependent edge。
- Transient evidence request、still-running job或recoverable blocker不terminalize、不
  建memo、不commit completion。
- `skipped_by_gate`/`not_activated` checkpoint不建自己的report或commit；由上游Step 5
  持久化。`CHANGES_REQUIRED`不建terminal report或commit。

## Human review and authority gates

Design/research governance 的預設是 consensus-first，不是 ask-first：

- Unexpected design issue 先完成 dual-agent `design-discussion`。
- Consensus 若保留原 plan，Main agent 自行記錄並繼續。
- 任何時點只有consensus證明必須修改原plan/authority時，才請使用者審查change
  packet；不得為普通repair、重跑、closeout或原plan已授權transition重複詢問。
- Checkpoint commit後不自動要求review；deterministic next edge且無新authority時直接
  進下一checkpoint。

以下情況仍需取得缺少的 authority；它們不是 design consensus 可以代替的權限：

- 本experiment sequence的isolated checkpoint closure commit已由repository owner
  授權，不重複詢問。Push、PR、credentials、external-system write、dependency
  install與container mutation仍需各自authority。
- 原 plan 未明列的 destructive non-run-artifact operation、whitelist 外修改、與
  unrelated user change重疊，或改用 repo rule 禁止的 host/container；這些本身視為
  plan change並提交使用者審查。
- 預估 30 分鐘以上且原 plan 未明確核准 budget 的 command/experiment。
- 開始前無法唯一辨識 source spec、target、scope或使用者偏好；不得用 subagent
  consensus發明使用者原始意圖。

## 文件與 evidence 規範

- 一個 bullet 一個重點；多部分 claim 使用 nested bullets。
- Command 必須記錄 exact cwd、exit code 與關鍵 observable result。
- Comparative experiment 先確認 metrics 測量同一 quantity、boundary 與 clock/domain。
- Ranking/fidelity 先看實際 decision metric，例如 top-k、best config 或 Pareto；correlation 與 average error 只能作輔助。
- 不從單一 dataset、少數 case、單一 metric 或缺少 mechanism 的結果宣稱普遍勝出。
- Report claim 必須能追到 raw artifact、command 或 code path。
- Formal report必須durable重述frozen oracle/evidence boundary、每輪findings/repairs/
  deviations與actual outcome/gate。
- 每個agent-decided issue記trigger、affected invariant、alternatives、正反evidence、
  assumptions、roles、decision、rationale/trade-off、impact、resolution、residual
  risk與review basis。只有實際使用`design-discussion`者才另記雙方objections、
  採納/捨棄、consensus與兩個`AGREE`。
- 不貼raw chat或private chain-of-thought；不以transient link取代正式report。
- Tracked report/parent不嵌closure commit自己的SHA、`SELF`或delivery-manifest hash；
  用stable identity、commit trailers、Git history與post-audit關聯。
- 不把大篇 report 或完整 JSON 重貼回 parent context；回傳 artifact path 即可。

## 完成輸出

以繁體中文精簡摘要run directory、checkpoint order/state、parent/design與Plan-B hash、
changed files、fresh verifier commands、technical verdict、scientific outcome、formal
report、`CLOSEOUT_ACK`、closure commit SHA、post-audit、verified edge、evidence boundary
與risks。只有required checkpoints各自`CHECKPOINT_COMPLETE`或依verified gate合法
skip/not-activate，才能宣告整體完成；否則列出technical/closeout state、blocking
evidence、未開始的downstream與需要使用者決定的下一步。

Active checkpoint沒有post-audited closure commit時，禁止使用「完成」或同義說法，
也禁止把dependent checkpoint標成started/ready/implemented。
