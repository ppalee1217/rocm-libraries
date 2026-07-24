---
name: design-discussion
description: Uses two independent GPT-5.6 Sol subagents to deliberate experiment or implementation design, repeatedly cross-examine assumptions and evidence until both explicitly confirm one consensus, and preserve the resulting decision for the governing design and experiment report. Use for experiment design, architecture or approach selection, hypothesis validation strategy, ambiguous result interpretation, unexpected implementation or verification design issues, and other consequential design-direction decisions. Do not use for lookups, mechanical edits, implementation execution, or choices with an obvious conventional default.
---

# Design Discussion

用兩個彼此獨立的 GPT-5.6 Sol subagents 降低單一觀點的盲點。
Main agent 是 orchestrator：準備共同 prompt、轉交雙方論點、查核證據、判斷是否真正收斂，最後寫回對應文件。

## Model policy

- 每次啟動 fresh subagent 時，明確指定 `model: gpt-5.6-sol-xhigh`。
- A、B 必須使用相同 model 與相同的初始 prompt。
- 若該 model 無法使用，停止並告知使用者；不可靜默換成其他 model。
- Subagent 必須是兩個不同的 fresh threads；不可用同一 thread 扮演雙方。

## 何時使用

使用情境：

- 設計實驗、control、變因、測量方法或 acceptance criteria。
- 選擇實作架構、演算法、研究方法或下一個實驗方向。
- 判斷 hypothesis、assumption、claim 或設計方向是否合理。
- 解讀 ambiguous、negative 或 counterintuitive result。
- 一個決策有數個合理方案，且選錯會造成明顯成本。

不要使用：

- 單純查資料、找 symbol、解釋既有程式或機械式修改。
- 已有唯一慣例答案的小決策。
- 實際執行實作；改用 `implement-verify-loop`。
- 純粹屬於使用者偏好的選擇。

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
5. 不設任意輪數上限。持續交互詰問，直到真正 tension points 已處理且兩方可評估同
   一份 candidate consensus。若同一 factual disagreement 連續兩輪沒有 material
   progress，Main agent 必須先取得新 evidence、縮小可驗證命題或指出缺少的證據，
   不可只重複相同 prompt。

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
2. 將同一份 candidate consensus 與雙方最新 remaining disagreements 並行送回 A、B。
3. 要求每一方只可回覆：
   - `AGREE`，並簡述它為何足以代表自己的立場；或
   - `OBJECT`，列出具體未解決項目與最小修正。
4. 只有兩方都回覆 `AGREE` 才能宣告 unified conclusion。
5. 若有可處理的 objection，修正 candidate、補同一份 evidence給雙方，再次讓兩方
   確認；不可因已討論若干輪就停止。
6. 若 objection 是 factual，繼續查證；若是 scope misunderstanding，回到共同 prompt
   與原 plan澄清；若是 value trade-off，先找出是否能在原 plan boundary內採用更
   嚴格且雙方可接受的設計。
7. 只有當 remaining disagreement 本身證明必須打破或修改使用者原訂 plan，或只能由
   使用者偏好決定，才停止並提交 human review。不得產生假共識，也不得把任一方立場
   寫成已定案計畫。

## User escalation boundary

對 implement/verify 過程中的 unexpected design issue：

- 兩方 `AGREE` 的 consensus若保留 frozen goal、acceptance、planned evidence、
  report target、checkpoint order/gates、approved whitelist/authority invariants與
  claim boundary，Main agent直接寫回並繼續，不需額外詢問使用者。
- 任何時點只要consensus顯示繼續必須打破或修改上述plan/authority，才將change
  packet交給使用者審查；不必等checkpoint完成後才升級。
- Ordinary in-scope repair、fresh rerun、原 plan 已定義的 negative branch、或把
  brittle test harness修成正確表達同一 acceptance，都不是自動 human gate。
- 這個consensus不能擴張frozen delivery whitelist或scoped commit authority，也不能
  授予push、credentials、external-system write、dependency install、container
  mutation或其他尚未取得的platform authority。
- Initial request若沒有唯一 goal、scope或 target，仍須釐清；兩個 agents不能替
  使用者發明原始意圖。

## Step 5：由 Main agent 寫回文件

只有 unified conclusion 成立後才寫回 Step 0 的 target document。

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
  shared consensus與兩個explicit `AGREE`；不要貼raw chat或private chain-of-thought。
- 清楚標示結論是 dual-agent cross-examination 後由 A、B 共同確認。
- 遵守目標文件既有語言、格式與 repo 文件規範。
- 不覆蓋無關的使用者變更。

## 多 checkpoint 實驗的文件生命週期

Canonical execution unit是authoritative parent experiment plan index中的stable
checkpoint；`milestone`/`step`只有指向該indexed checkpoint時才是alias。Parent plan是
規劃階段的target；其明確引用的checkpoint design、report與blocked memo是同一目標的
受控交付物，不需逐一詢問路徑。

1. **規劃階段：每個 checkpoint 各建一份設計文件**
   - parent plan 必須提供文件索引、執行順序、dependency、gate、目前狀態與設計文件連結。
   - 每份設計文件至少要直白說明：
     - 實驗假設是什麼，以及什麼觀察會推翻它。
     - 實驗預期目標是什麼；成功、失敗、降級各代表什麼。
     - 實驗結果能說明什麼、不能說明什麼，避免超出 evidence boundary。
     - 實作範圍、輸入、輸出、變因、control、固定條件與 measurement boundary。
     - 可執行步驟、程式或設定修改點、artifact / logging schema、驗證方法。
     - acceptance criteria、falsification condition、停止條件與下一步決策。
     - 預期可能遇到的狀況、診斷證據、處理方法與無法排除時的降級方案。
   - 尚未執行的實驗只能寫 hypothesis、protocol 與預期判讀；不得捏造數字、結果或已解決狀況。
2. **Technical verification通過後：另建該checkpoint的完整實驗報告**
   - 報告與設計文件分開保存，不用事後結果覆寫 preregistered design。
   - 只有planned execution/evidence完整且independent verifier technical `PASS`才建立
     formal report；`CHECKPOINT_COMPLETE`仍須經parent update、`CLOSEOUT_ACK`、isolated
     commit與post-commit audit。
   - Report除原始假設、目標、環境/revision、偏差、結果、root cause、解法、未解問題、
     commands與artifacts外，還須完整materialize所有影響implementation、verification、
     interpretation、lifecycle或gate的agent adjudication。
   - negative / inconclusive result 也必須建立報告，不可只報成功案例；若證據不足，明確標成 underpowered 或 inconclusive。
   - Durable terminal `BLOCKED`只建立design預先指定的blocker memo；不是formal report或
     completion。`skipped_by_gate`/`not_activated`不建立假report，由上游closeout記錄。
3. **可追溯性**
   - 每份 design 要連回 parent plan，並預先指定未來 report 路徑。
   - 每份 report 要連回對應 design，逐項回答原 acceptance criteria 與 falsification conditions。
   - 若執行中修改 hypothesis、metric 或門檻，保留原設計並在 report 記錄變更時間、理由與影響，不可把事後門檻偽裝成預註冊條件。
   - Tracked report/parent不嵌closure commit自己的SHA、`SELF`或delivery-manifest hash；
     使用stable identity、commit trailers、Git history與post-commit audit關聯。

## 完成條件

只有以下條件全數成立才算完成：

- 兩個 fresh GPT-5.6 Sol subagents 收到相同初始 prompt。
- 雙方至少完成一輪針對彼此實際論點的交互詰問。
- Factual crux 已以可取得的證據查核，或明確列為未驗證。
- A、B 都明確確認同一份 candidate consensus。
- 不得因固定輪數、時間方便或 Main agent 偏好，在兩方尚未 `AGREE` 時假定收斂。
- Main agent 已把 unified design 寫回唯一、正確的 target document。
- 若為多checkpoint實驗，parent plan已建立完整索引，且每個checkpoint都有可執行的
  獨立設計與預先指定的report或terminal blocker path。

最後以繁體中文簡述：

- 統一結論。
- 交互詰問改變或強化了哪些關鍵點。
- 寫回的文件路徑。
- 仍存在的 evidence boundary 與非阻擋風險。
