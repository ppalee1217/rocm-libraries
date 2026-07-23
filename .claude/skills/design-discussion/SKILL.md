---
name: design-discussion
description: Uses two independent GPT-5.6 Sol subagents to deliberate experiment or implementation design, cross-examine each other's assumptions and evidence, and confirm a shared conclusion before the main agent records the resulting plan in the corresponding document. Use for experiment design, architecture or approach selection, hypothesis validation strategy, ambiguous result interpretation, and other consequential design-direction decisions. Do not use for lookups, mechanical edits, implementation execution, or choices with an obvious conventional default.
argument-hint: "<design-question-or-spec> [target-document]"
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
5. 執行 1–3 輪；只在真正 tension points 已處理後進入收斂確認。

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
5. 若有可處理的 objection，在三輪總上限內修正並再次讓雙方確認。
6. 若仍無法收斂，停止：
   - 向使用者呈現 agreements、disagreements、證據與需要人類決定的 trade-off。
   - 不產生假共識，也不把任一方立場寫成已定案的實作計畫。

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
- 清楚標示結論是 dual-agent cross-examination 後由 A、B 共同確認。
- 遵守目標文件既有語言、格式與 repo 文件規範。
- 不覆蓋無關的使用者變更。

## 完成條件

只有以下條件全數成立才算完成：

- 兩個 fresh GPT-5.6 Sol subagents 收到相同初始 prompt。
- 雙方至少完成一輪針對彼此實際論點的交互詰問。
- Factual crux 已以可取得的證據查核，或明確列為未驗證。
- A、B 都明確確認同一份 candidate consensus。
- Main agent 已把 unified design 寫回唯一、正確的 target document。

最後以繁體中文簡述：

- 統一結論。
- 交互詰問改變或強化了哪些關鍵點。
- 寫回的文件路徑。
- 仍存在的 evidence boundary 與非阻擋風險。
