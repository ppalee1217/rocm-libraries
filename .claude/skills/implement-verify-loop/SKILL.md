---
name: implement-verify-loop
description: >-
  Orchestrates an experiment implementation with four GPT-5.6 Sol subagents:
  two independent planners produce an implementation plan and a frozen
  goal-based verification plan, then a fresh implementer changes the code and
  a separate verifier repeatedly tests the actual result until every required
  criterion passes. Use when implementing an experiment or scoped milestone
  from a design note or complete specification with acceptance criteria. Do
  not use for design-direction decisions, trivial edits, or tasks whose goal
  is still ambiguous.
argument-hint: "<design-note-or-complete-spec> [scope-or-report-path]"
---

# Implement and Verify Loop

Main agent 是 orchestrator。
Main agent 準備需求、保護 baseline、管理四個 GPT-5.6 Sol subagents、裁決 verifier findings，並保存可追溯證據。

實作只有在獨立 verifier 對 frozen goal plan 回覆完整 `PASS` 後才算完成。
「有改 code」、「implementer 自己測過」或「只剩 verifier 尚未確認」都不是完成。

## Model and independence policy

- 所有 fresh subagents 都明確使用 `model: gpt-5.6-sol-xhigh`。
- 若該 model 無法使用，停止並告知使用者；不可靜默換 model。
- 四個角色使用四個不同的 fresh threads：
  1. Plan-A planner。
  2. Plan-B planner。
  3. Implementer。
  4. Verifier。
- Implementer 與 verifier 在修正迴圈中各自 resume 原 thread，以保留角色脈絡。
- Verifier 永遠不可讀 `plan_a.md`；它依 goal 判斷，不依 implementer 選擇的步驟判斷。
- Plan-B planner 永遠不可讀或接收 Plan-A。

## 何時使用

開始條件：

- 有 design note、milestone spec 或自足的 implementation requirement。
- Scope 與 acceptance criteria 足以判定「真的完成」。
- 使用者要求進行實驗、prototype、功能實作或有驗證要求的 scoped change。

不要使用：

- 還在選方向、方法或實驗設計；先使用 `design-discussion`。
- 單純查詢、code explanation、read-only review 或明顯的微小機械式修改。
- 缺少會實質影響實作的 goal、scope、evidence source 或 acceptance criteria。

## Run directory

每次執行使用 repo root 下的：

```text
agent_run/YYMMDD-{feature-slug}[-N]/
```

`feature-slug` 使用小寫 kebab-case。
同日同名衝突時依序加 `-2`、`-3`。

至少保存：

```text
baseline.md
plan_a.md
plan_b.md
impl_report.md
verify_report.md
verdict.json
adjudication.md
subagents.md
```

- `agent_run/` 是 transient evidence，不得 commit。
- 開始前用 `git check-ignore` 確認它已被忽略。
- 若未被忽略，先取得使用者同意才可新增 ignore rule；不可靜默修改 ignore 設定。
- 不自動刪除舊 run directories。
- 每個 subagent 的 model、role、agent link/ID 與 artifact path 記在 `subagents.md`。
- 完整內容寫入 artifact；subagent 回覆 Main agent 時只回傳短 status、changed files、verdict 與 artifact paths。

## Step 0：解析需求、scope 與 baseline

1. 由 `$ARGUMENTS`、使用者訊息或明確引用解析 design note/spec。
2. 若有零個或多個合理來源，使用 `AskQuestion` 請使用者選擇；不可發明 spec 或 report path。
3. 讀取適用的 repo 規則、source note、相關 code 與既有 tests。
4. 若 goal、scope、acceptance 或長時間實驗邊界仍有實質歧義，先詢問使用者。
5. 建立 run directory。
6. 將以下 baseline 寫入 `baseline.md`：
   - Parent repo 與 relevant submodules 的 current branch/commit。
   - `git status --short`。
   - Existing staged、unstaged 與 untracked paths。
   - 本次可接觸的初步 scope。
7. 保留所有 unrelated user changes；不可 reset、checkout、stash、覆蓋或順手整理。

## Step 1：並行產生兩份獨立計畫

建立一份 `BASE REQUIREMENTS` block，內容包含：

- Repo root、source note/spec 路徑與必要 context。
- Main objective 與 scope。
- Required behavior 與 acceptance criteria。
- Constraints、compatibility boundaries 與禁止事項。
- Known user changes、可用環境、evidence/artifact paths。
- 明確說明只負責 planning，不實作 source change。

Plan-A 與 Plan-B planners 必須收到內容完全相同的 `BASE REQUIREMENTS`。
只有附加在後面的 role instructions 不同。
在同一個並行啟動動作中建立兩個 fresh planners。

### Plan-A planner：implementation plan

只允許寫入本次的 `plan_a.md`。
要求內容：

- Objective 與 scope restatement。
- Exact file whitelist 或清楚的 whitelist scope。
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

Plan-B 是 goal oracle，不得包含 Plan-A 的 file-by-file steps。

### Main agent plan gate

兩個 planners 完成後，Main agent：

1. 讀取兩份計畫，確認都忠於原始需求。
2. 確認 Plan-A 有 whitelist 與可執行自驗。
3. 確認 Plan-B 是 goal-based、可驗證且沒有 Plan-A 污染。
4. 若有缺漏，resume 對應 planner 修正；不得讓兩個 planners 互讀。
5. Plan-B 通過 gate 後，在 `adjudication.md` 記錄其 hash 並標示 `FROZEN`。
6. Frozen 後不可為了讓實作過關修改 Plan-B。
7. 只有證明原始 goal 本身錯誤或矛盾時才可提議改 Plan-B，而且必須先由使用者批准並留下理由。

## Step 2：Fresh implementer 執行 Plan-A

啟動第三個 fresh GPT-5.6 Sol subagent。
它只收到完整 Plan-A 與下列 execution contract，不收到 Plan-B：

- 在 current workspace 實作 Plan-A。
- 只修改 Plan-A whitelist 內的 source/test/doc paths，以及本 run 的 `impl_report.md`。
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

## Step 3：Fresh verifier 依 frozen Plan-B 驗證

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
- 自己 fresh reproduce headline acceptance check，不可只採信 implementer 結果。
- 檢查 regression、compatibility、edge cases、measurement comparability 與 unacceptable fallbacks。
- 若 command 會修改 source 或需權限、network、credentials、dependency install、長時間資源，列為 evidence request，不可自行越權。
- 回覆只包含 `verdict`、`goal_alignment`、blocking count 與 artifact paths。

`verdict.json` 至少使用：

```json
{
  "verdict": "PASS | CHANGES_REQUIRED | BLOCKED",
  "goal_alignment": "FULL | PARTIAL | NONE",
  "acceptance_criteria": [
    {
      "criterion": "required behavior",
      "status": "PASS | FAIL | UNVERIFIED",
      "evidence": ["command, artifact, code path, or observation"]
    }
  ],
  "blocking_findings": [
    {
      "id": "stable-id",
      "severity": "critical | major | moderate",
      "evidence": "specific evidence",
      "required_change": "smallest actionable correction"
    }
  ],
  "commands_run": [
    {
      "command": "exact command",
      "cwd": "working directory",
      "result": "PASS | FAIL | BLOCKED",
      "evidence": "exit code and relevant output"
    }
  ],
  "evidence_requests": [],
  "unverified": [],
  "unacceptable_fallback_triggered": {
    "triggered": false,
    "which": []
  },
  "summary": "bounded conclusion"
}
```

`PASS` 僅在以下條件全數成立時允許：

- `goal_alignment` 是 `FULL`。
- 每個 required criterion 都是 `PASS`。
- `blocking_findings`、`evidence_requests` 與 required `unverified` 都為空。
- 沒有 unacceptable fallback。
- Headline check 已由 verifier fresh reproduce。
- 所有預定 experiment runs 都完整成功，沒有 partial、timeout、killed 或 still-running 結果。

## Step 4：Adjudicate 與修正迴圈

Main agent 每輪將以下內容追加到 `adjudication.md`：

- Iteration number 與 Plan-B frozen hash。
- Implementer changed paths 與 evidence。
- Verifier verdict、blocking finding IDs 與 evidence requests。
- Main agent 的判斷、下一步與未解風險。

### PASS

只有 verifier 回覆合格 `PASS` 時：

1. 再次檢查 Plan-B hash 未變。
2. 確認 working tree 沒有 verifier 或其他角色造成的越界 source change。
3. 記錄 terminal `CONSISTENT`。
4. 才能對使用者宣告 implementation complete。

### CHANGES_REQUIRED

1. Main agent 依 direct evidence 判斷 findings 是否具體、是否在 scope 內。
2. 將 blocking IDs、`verify_report.md`、required changes 與 current changed paths resume 給原 implementer。
3. Implementer 修正後更新 `impl_report.md`，並只回傳短 status 與 paths。
4. Main agent 再做 whitelist/baseline check。
5. Resume 原 verifier：
   - 提供 addressed finding IDs、new diff、commands/artifacts 與 remaining uncertainties。
   - 要求重新讀 current files 並 fresh rerun relevant checks。
   - 不可只相信 repair summary。
6. 重複直到 verifier 給出合格 `PASS`。

### BLOCKED 或 evidence request

- Main agent 可執行短、可逆且在授權範圍內的 evidence command，並記錄 exact command、cwd、exit code 與 artifacts，再 resume verifier。
- 需要 human gate 的操作先詢問使用者。
- 若環境無法取得必要 evidence，terminal state 是 `BLOCKED`，不是 `PASS`。

### Honest exits

下列情況停止並升級給使用者，不假裝完成：

- 最多五次 implement→verify iterations 仍未 PASS。
- 同一 blocking finding 連續兩次出現且沒有 material progress。
- Goal 正確但工作量、硬體、資料或環境超出本次 scope。
- Verifier 與 Main agent 無法依現有 evidence 判定。
- Evidence 只支持 inconclusive result，卻不足以支持原本的成功 claim。

## Human gates

以下操作永遠先取得使用者批准：

- Commit、push、PR、dependency install、network、credentials 或 external-system write。
- Destructive operation，或刪除、移動、重新命名非 run artifact。
- 預估 30 分鐘以上的 command/experiment。
- 修改 Plan-A whitelist 外的檔案。
- 與 unrelated pre-existing user change 重疊。
- 修改 frozen goal、acceptance criterion、evidence source 或 report target。

## 文件與 evidence 規範

- 一個 bullet 一個重點；多部分 claim 使用 nested bullets。
- Command 必須記錄 exact cwd、exit code 與關鍵 observable result。
- Comparative experiment 先確認 metrics 測量同一 quantity、boundary 與 clock/domain。
- Ranking/fidelity 先看實際 decision metric，例如 top-k、best config 或 Pareto；correlation 與 average error 只能作輔助。
- 不從單一 dataset、少數 case、單一 metric 或缺少 mechanism 的結果宣稱普遍勝出。
- Report claim 必須能追到 raw artifact、command 或 code path。
- 不把大篇 report 或完整 JSON 重貼回 parent context；回傳 artifact path 即可。

## 完成輸出

以繁體中文提供精簡摘要：

- Run directory。
- Source/spec 與 frozen Plan-B。
- Changed files 與 behavior。
- Verifier fresh commands 與結果。
- Final verdict 與 acceptance status。
- Evidence boundary 與 remaining non-blocking risks。
- 若未 PASS，明確說明 honest partial、blocking evidence 與需要使用者決定的下一步。

沒有 verifier `PASS` 時，禁止使用「完成」、「驗證無誤」或同義說法。
