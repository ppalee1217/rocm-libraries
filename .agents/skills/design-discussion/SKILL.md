---
name: design-discussion
description: Uses two independent reviewers for bounded deliberation of material experiment-design ambiguity in protocol, claim, measurement-lineage, stopping rules, or scientific authority. Allows at most two cross-examination rounds plus one evidence-backed final round and 60 total agent wall-minutes, then gives the unified recommendation or preserved dissent to the user for a decision. Never applies an experiment-design decision autonomously. Do not use for lookups, mechanical repairs, ordinary implementation choices, resource waiting, or questions already resolved by a frozen contract.
---

# Design Discussion

<!-- BEGIN CODEX RUNTIME MAPPINGS -->
## Codex runtime mappings

- Treat `$ARGUMENTS` as the current user request plus any explicitly named target document.
- Treat `AskQuestion` as asking the user through the input mechanism available in the current
  Codex mode.
- Map `model: gpt-5.6-sol-xhigh` to `model: gpt-5.6-sol` with
  `reasoning_effort: xhigh`.
- Use `fork_turns: none` for both fresh reviewers and provide the identical, self-contained
  prompt explicitly.
- Issue both `spawn_agent` calls before waiting for either result.
- Treat `resume` as `followup_task` addressed to the same saved reviewer ID; do not replace a
  participant with a new thread.
- Record the Codex task name or agent ID wherever the workflow asks for an agent link or ID.
- If the required model or subagent tools are unavailable, stop and report the limitation
  under this workflow's authority rules.
<!-- END CODEX RUNTIME MAPPINGS -->

用兩個彼此獨立的 reviewers 降低單一觀點的盲點。Main agent 是 orchestrator：準備
共同 prompt、轉交雙方論點、查核證據、執行 round/time cap，最後把 unified
recommendation 或 preserved dissent 整理成 human decision packet。Experiment-design
決定必須由使用者核准，reviewer consensus 本身不授權變更或恢復 affected design path。

## Model policy

- `model: gpt-5.6-sol-xhigh` 是 disclosed preference／capability requirement。記錄
  requested/actual model 與 capability assessment；不可靜默降級。
- Model unavailability 不是 R0/R1 的 universal hard stop。只有 approved design 明定
  不可替代 capability，或替代 model 無法滿足 material R2/R3 review 時才停止。
- A、B 應使用相同 capability class 與相同初始 prompt；差異必須揭露。
- Subagent 必須是兩個不同的 fresh threads；不可用同一 thread 扮演雙方。
- Same-model fresh threads 是 process independence，不是 scientific replication。

## 何時使用

只在下列 material ambiguity 可能改變 frozen boundary 時使用：

- Protocol、control、fixture、acceptance、threshold 或 stopping rule ambiguity。
- Measurement quantity/boundary、claim scope、lineage、selection 或 comparability ambiguity。
- Authority、destructive operation、post-label amendment 或 immutable lock ambiguity。
- Negative/counterintuitive result 暴露多個會改 gate/claim 的合理 interpretation。

不要使用：

- 單純查資料、找 symbol、解釋既有程式或機械式修改。
- 已有唯一 frozen-contract／慣例答案的小決策。
- 實際執行實作；改用 `implement-verify-loop`。
- 純粹屬於使用者偏好的選擇。
- 普通 in-scope repair、deterministic disposable artifact recovery、resource waiting、
  或不影響 protocol/claim/authority 的 implementation choice。

## Step 0：界定問題與目標文件

1. 將 `$ARGUMENTS`、使用者要求、相關設計文件與必要 repo 證據整理成一個自足問題。
2. 在開始討論前解析要寫回的文件，依序採用：
   - 使用者明確指定的 target document。
   - 請求中唯一引用的 design/spec 文件。
   - 當前情境中唯一可合理判定的對應文件。
3. 若沒有唯一目標，使用 `AskQuestion` 請使用者選擇；不可自行發明路徑。
4. 先讀目標文件與適用的 repo 規則，確認應更新的章節、格式與語言。
5. 若問題的 scope、成功條件或不可接受結果仍會實質改變設計，也先詢問使用者。
6. 若由`implement-verify-loop`處理active checkpoint的unexpected issue，target先使用該
   checkpoint的`adjudication.md`；不得為plan-preserving repair改寫locked design。
   Main agent必須在closeout時把material decision完整整合進formal experiment report。
7. 記錄 start time、60 agent wall-minute 總 budget 與最多兩輪 cross-examination；
   A、B 各自消耗的 wall-time 都計入總數。Initial positions 不算 cross-examination，
   evidence-backed final positions 是額外且唯一的一輪。

## Step 1：建立共同 prompt

初始 prompt 必須同時具備：

- repo root 與可讀取的相關文件、code、data 或 artifact 路徑。
- 問題背景、要做的決策及其邊界。
- 已知 constraints、acceptance criteria 與不可接受結果。
- 要求以 repo/data 證據支持 factual claims。
- 要求明確揭露 assumptions、risks、uncertainties 與缺少的 evidence。
- 要求提出一個可辯護的主張，不可只列選項而拒絕判斷。
- 明確說明這一輪只做分析，不修改任何檔案。

要求兩個 subagents 使用相同輸出結構：

```text
POSITION
RECOMMENDATION
KEY ARGUMENTS
ASSUMPTIONS
EVIDENCE
RISKS
UNCERTAINTIES
QUESTIONS FOR THE OTHER VIEW
```

初始 prompt 不可包含 Main agent 的偏好、另一方答案或暗示「預期共識」的措辭。

## Step 2：取得兩個獨立觀點

1. 在同一個並行啟動動作中建立 Agent A 與 Agent B。
2. 兩者都使用 Step 1 的完全相同 prompt。
3. 兩者完成前，不把任何一方的內容提供給另一方。
4. 保留兩個 agent IDs，後續交互詰問必須 `resume` 原 threads，不可另開角色替代。
5. 若任一方未完成、偏離問題或沒有提出可辯護立場，先 resume 該方補齊；不要開始假交鋒。

## Step 3：交互詰問

Main agent 是透明 relay，不得把自己的偏好偽裝成另一方意見。

每一輪：

1. 將 B 的最新完整立場交給 A。
2. 將 A 的最新完整立場交給 B。
3. 並行 resume 兩個原 threads，要求各自：
   - 指出對方最強與最弱的論點。
   - 回答對方的 questions 與 objections。
   - 找出雙方 hidden assumptions。
   - 區分 factual disagreement、value trade-off 與 scope misunderstanding。
   - 說明哪些地方接受對方修正，哪些地方仍反對及其證據。
   - 給出 revised position 與 remaining disagreements。
4. 若分歧取決於可查證事實，先從 repo、data 或 artifact 取得證據，再把同一份證據交給雙方。
5. 最多執行兩輪。每輪後記錄 elapsed agent wall-minutes、resolved crux 與 remaining
   dissent。若同一 factual disagreement 連續兩輪沒有 material progress，直接進 final
   round；不可重複 prompt 或另開 thread 重設 cap。
6. 任一時點達 60 agent wall-minutes，立即停止新 cross-examination，進入可負擔的
   evidence-backed final positions；若連 final round 都無 budget，使用當前 positions。

禁止：

- 只要求雙方「評論一下」，卻沒有逐項回答分歧。
- 因多數、語氣或權威感決定勝負。
- 省略反證、measurement boundary 或 residual uncertainty。
- 為了結束流程要求任一方無條件同意。

## Step 4：確認收斂

1. Main agent 根據雙方最新立場起草一份 candidate consensus，內容包含：
   - 統一 recommendation。
   - 核心理由與可驗證 assumptions。
   - experiment/implementation design。
   - acceptance criteria 與 falsification conditions。
   - risks、evidence boundary 與 residual uncertainty。
2. 在前兩輪取得的 evidence 內，並行送出唯一一次 evidence-backed final round。兩方
   都收到相同 candidate、remaining disagreements、evidence 與剩餘 wall-time。
3. 要求每一方回覆：
   - `AGREE`：簡述 candidate 為何足以代表自己的立場；或
   - `DISSENT`：列出具體未解項、supporting evidence、claim impact 與最小 human choice。
4. 只有兩方都 `AGREE` 才能宣告 unified conclusion；不得再開第四輪要求改口。
5. 任一 `DISSENT`、缺席、timeout、round cap 或 60-minute cap 都建立 preserved-dissent
   packet：共同點、各自立場、factual/value/scope crux、evidence boundary、已嘗試修正、
   最小選項與 recommendation，然後 human escalation。
6. Cap 不是失敗，也不是默認任何一方勝出。不得以多數、語氣、model、Main agent 偏好
   或時間壓力強迫 `AGREE`、刪除 objection 或偽造 consensus。

## User decision boundary

對 implement/verify 過程中的 unexpected design issue：

- 兩方 `AGREE` 時，把 consensus、evidence boundary、risks 與最小 approval question
  交給使用者；即使它保留 frozen goal、acceptance、planned evidence、report target、
  checkpoint order/gates、approved whitelist/authority invariants 與 claim boundary，
  也不得在使用者決定前恢復 affected design path。
- 任一 material `DISSENT` 或 cap reached 都保留原 frozen contract，提交 human decision
  packet；不可在等待期間修改 source、authority、labels 或 claim。
- 任何時點只要consensus顯示繼續必須打破或修改上述plan/authority，change packet
  必須額外列出 exact amendment 與重新 seal／rerun impact；不必等checkpoint完成後才
  升級。
- Ordinary in-scope repair、fresh rerun、原 plan 已定義的 negative branch、或把
  brittle test harness修成正確表達同一 acceptance，都不是自動 human gate。
- 這個consensus不能擴張frozen delivery whitelist或scoped commit authority，也不能
  授予push、credentials、external-system write、dependency install、container
  mutation或其他尚未取得的platform authority。
- Initial request若沒有唯一 goal、scope或 target，仍須釐清；兩個 agents不能替
  使用者發明原始意圖。

## Step 5：由 Main agent 保存 packet，核准後寫回 authority

使用者決定前，unified conclusion 與 dissent 都只能寫成 clearly non-authoritative
decision packet，不得把 reviewer recommendation 標成 approved design。使用者明確
核准後，Main agent 才將 approved decision 寫回 governing design／authority；若使用者
未核准，保留 frozen state 與 packet。

- Main agent 親自整合內容；不可直接貼上任一 subagent 的原始回答。
- 更新文件中最自然的既有章節；只有沒有合適位置時才新增設計決策章節。
- 至少記錄：
  - 要解決的問題與 scope。
  - 統一採用的設計與捨棄方案。
  - 關鍵 reasoning、evidence 與 assumptions。
  - experiment variables、controls、measurement boundary 或 implementation boundaries。
  - acceptance criteria、falsification conditions 與 verification plan。
  - risks、residual uncertainty 與後續工作。
- 對每個agent-decided issue記錄trigger、affected invariant、所有material alternatives、
  supporting/opposing evidence、assumptions、participants、decision、rationale與
  trade-offs、implementation/measurement/gate/claim impact、resolution、remaining
  uncertainty及user-review basis。
- 實際啟動本skill的issue另記兩位reviewers的substantive objections、採納/捨棄方案、
  shared consensus 或 preserved dissent、round/time usage 與 final responses；不要貼
  raw chat 或 private chain-of-thought。
- 只有兩方 `AGREE` 才標示 unified recommendation；在使用者決定前，兩種結果都清楚
  標示 `PENDING_HUMAN_DECISION`。
- 遵守目標文件既有語言、格式與 repo 文件規範。
- 不覆蓋無關的使用者變更。

## 多 gate 實驗的文件生命週期

Parent plan 必須把 indexed checkpoint 明確映射到 `scientific_gate`、`execution_tranche`
與 `closure_unit`。Scientific gate 保留 hard edge；相容 adjacent gates 可共享角色、
run root 與一個 terminal closeout，但不得共享或改寫彼此的 outcome criterion。

1. **規劃階段：每個 scientific gate 各建一份設計／frozen-contract authority**
   - parent plan 必須提供文件索引、gate order/dependency、tranche/closure mapping、
     current state 與設計／machine-readable contract 連結。
   - 每份設計文件至少要直白說明：
     - 實驗假設是什麼，以及什麼觀察會推翻它。
     - 實驗預期目標是什麼；成功、失敗、降級各代表什麼。
     - 實驗結果能說明什麼、不能說明什麼，避免超出 evidence boundary。
     - 實作範圍、輸入、輸出、變因、control、固定條件與 measurement boundary。
     - 可執行步驟、程式或設定修改點、artifact / logging schema、驗證方法。
     - acceptance criteria、falsification condition、停止條件與下一步決策。
     - 預期可能遇到的狀況、診斷證據、處理方法與無法排除時的降級方案。
   - 尚未執行的實驗只能寫 hypothesis、protocol 與預期判讀；不得捏造數字、結果或已解決狀況。
   - Durable machine-readable contract 與 lock 必須在 outcome labels 前 seal；transient
     execution plan 不能取代。
2. **Technical verification 通過後：由 closure unit 建立 terminal 實驗報告**
   - 報告與設計文件分開保存，不用事後結果覆寫 preregistered design。
   - 每個 outcome-bearing R1-R3 gate 必須先有 fresh verifier technical `PASS`。相容
     gates 可在一份 closure report 中各自保留 criterion、outcome、evidence 與 edge，
     再做一次 parent update、`CLOSEOUT_ACK`、授權範圍內的 terminal commit 與
     post-commit audit。
   - Report 除各 gate 的原始假設、目標、環境/revision、偏差、結果、root cause、解法、未解問題、
     commands與artifacts外，還須完整materialize所有影響implementation、verification、
     interpretation、lifecycle或gate的agent adjudication。
   - negative / inconclusive result 也必須建立報告，不可只報成功案例；若證據不足，明確標成 underpowered 或 inconclusive。
   - Durable terminal `BLOCKED`只建立design預先指定的blocker memo；不是formal report或
     completion。`skipped_by_gate`/`not_activated`不建立假report，由上游closeout記錄。
3. **可追溯性**
   - 每份 design/contract 要連回 parent plan，並預先指定未來 closure report 路徑。
   - 每份 closure report 要按 gate 連回對應 design/contract，逐項回答原 acceptance
     criteria 與 falsification conditions。
   - 若執行中修改 hypothesis、metric 或門檻，保留原設計並在 report 記錄變更時間、理由與影響，不可把事後門檻偽裝成預註冊條件。
   - Tracked report/parent不嵌closure commit自己的SHA、`SELF`或delivery-manifest hash；
     使用stable identity、commit trailers、Git history與post-commit audit關聯。

## 完成條件

本 skill 的 deliberation 在「unified recommendation 已保存並提交使用者」或「dissent
已保存並提交使用者」其中一個 terminal state 成立時完成；affected experiment-design
path 仍等待使用者決定：

- 兩個 fresh reviewers 收到相同初始 prompt。
- Budget 允許時，雙方至少完成一輪針對彼此實際論點的交互詰問；若 initial positions
  已耗盡 60-minute cap，直接保存 positions 並升級。
- Factual crux 已以可取得的證據查核，或明確列為未驗證。
- Cross-examination 不超過兩輪，final positions 不超過一輪，且總 agent wall-time
  不超過 60 分鐘。
- A、B 都 `AGREE` 同一 candidate，或 material dissent 已原樣保存。
- Main agent 已把 non-authoritative decision packet 寫回唯一、正確的 target document
  並交使用者；只有取得明確核准後，才可另行寫成 approved design。
- 若為 multi-gate 實驗，parent plan 已建立 gate/tranche/closure mapping，且每個 gate
  都有可執行的獨立設計／contract 與預先指定的 closure report 或 terminal blocker path。

最後以繁體中文簡述：

- 統一結論，或 preserved dissent 與需要的人類決定。
- 交互詰問改變或強化了哪些關鍵點。
- 寫回的文件路徑。
- 仍存在的 evidence boundary 與非阻擋風險。
