---
name: learning-quiz
description: Use when the learner has finished a day's items in the 8-week internship learning roadmap (study_docs/learning-roadmap.md) and asks to be quizzed / tested on that day's material. Generates an interactive quiz file under study_docs/quizzes/, grades the learner's answers, judges whether understanding is correct, and points to exactly what to review. The number of questions adapts to the day's content — it is NOT fixed.
---

# Learning Quiz（互動深度測驗）

<!-- BEGIN CODEX RUNTIME MAPPINGS -->
## Codex runtime mappings

- Treat references to `CLAUDE.md` as references to the applicable root and nested
  `AGENTS.md` guidance already loaded by Codex.
- Treat Cursor Markdown preview and navigation as the equivalent behavior in the current
  Codex client.
<!-- END CODEX RUNTIME MAPPINGS -->

當學習者完成 roadmap 某天的 item 並要求測驗時使用。這個 skill 比 roadmap 內嵌的「快速自測」更深：
生成獨立測驗檔、讓學習者作答、逐題批改、指出要回去補強什麼。

## 何時用 / 不用

- **用**：學習者說「我做完今天的了，幫我出測驗 / 考我 / 測一下 0628」這類請求。
- **不用**：roadmap 內每天的 `<details>` 快速自測由學習者自行核對，不需要這個 skill。本 skill 是
  「要求才啟動」的深度互動測驗。

## 流程（兩階段：出題 → 批改）

### 階段 1：出題
1. 確認是哪一天（學習者給 MMDD，或用「今天」對照 roadmap 當前階段）。
2. 讀該天 roadmap 小節的「今日目標 / 主 item / ✅ 完成判準 / 📚 參考資源」，並實際讀對應的
   codebase / asm `.s` / study_docs 段落（**先查證再出題，行號/節名不可杜撰**；行號會漂移，引用前確認）。
3. 依當天內容**決定題數（不固定）**：概念輕的日子 3~4 題、組語/實作重的日子 6~8 題。題型混用：
   - **概念題**：解釋名詞 / 因果（為何要 `s_barrier`、vmcnt vs lgkmcnt）。
   - **讀組語題**：給一小段 `.s`（從實際範例節錄、標來源行段），問它在做什麼 / 哪裡是瓶頸。
   - **情境判斷題**：給一個 profiling 數字或修改情境，問該往哪個方向調 / 會發生什麼。
   - **動手覆核題**：請學習者貼出他跑出的輸出 / 反組譯片段，核對是否符合預期。
4. 標每題難度（基礎 / 進階 / 挑戰）與對應的 ✅ 完成判準。
5. 寫成測驗檔 `study_docs/quizzes/MMDD-{Description}-quiz.md`（Description 同當天主題）：
   - 開頭：對應日期、今日目標、題數、難度分布。
   - 「題目」區：逐題編號 + 難度標籤 + 「我的作答：____」空白行。
   - 「參考答案」區：放 `<details>` 摺疊，每題附答案 + 為何 + 對應 📚 參考資源。
6. 告訴學習者測驗檔路徑，請他在「我的作答」填答後回來。

### 階段 2：批改
1. 讀學習者填好的測驗檔（或他直接貼上的答案）。
2. **逐題批改**：標 ✅ 正確 / ⚠️ 部分正確 / ❌ 錯誤；簡述哪裡對、哪裡缺。
3. 對 ⚠️/❌ 題：指出**具體要回去補強的主題**，連回該天 roadmap 的 📚 參考資源與（待擴充）stub 文件，
   或對應 asm 範例行段 / codebase 路徑。
4. 收尾：一句「今天理解程度」總評 + 「建議下一步」（可進下一天 / 需補哪幾個點再進）。
   若多題集中在同一主題，明確建議回看該主題。

## 批改 rubric

- ✅ 正確：抓到核心因果，用詞可不精確但概念對。
- ⚠️ 部分正確：方向對但漏關鍵條件（如只說「等記憶體」沒分 vmcnt/lgkmcnt）。
- ❌ 錯誤：概念誤解，給正解 + 最小可讀的補強資源（優先指向 asm 範例的具體行段或 study_docs 節名）。

## 與 roadmap 內嵌快速自測的分工

- 內嵌快速自測：每天 3~? 題、`<details>` 自核、學習者自己做，**不寫檔**。
- 本 skill：要求才啟動、**寫測驗檔**、AI 批改、給補強路徑。兩者題目可不同、互補。

## 檔名與語言規範

- 測驗檔：`study_docs/quizzes/MMDD-{Description}-quiz.md`（Description 用當天主題的精簡 kebab/中文皆可，
  與 notes 當天檔名對齊）。
- 語言遵 repo CLAUDE.md：繁中敘述，技術名詞 / 函式 / 檔名 / 工具名保留英文。
- 引用 codebase 用 markdown link + 行錨點，行號先查證；不確定就連檔不加行號。
- **每個指向實際檔案/目錄的引用都要連成 link，且只連已存在的檔**（避免死連結）；env var / CLI flag /
  副檔名名詞 / 執行期產物目錄維持 inline code，不要連。link 文字**不要包 backtick**
  （`` [`name`](url) `` preview 會點不開），寫成 `[name](url)`。
- 可讀性：題目與批改敘述也套同一套規範——一個 bullet 一個重點、多事實拆 nested 子 bullet、
  長段斷點分段，避免擠成一行。

## 驗證

出題前已讀過當天對應的真實檔案；測驗檔結構含題目區（含「我的作答」空白）+ 摺疊參考答案；
批改後每個 ⚠️/❌ 都連回一個具體可看的資源（指向已存在檔的引用皆為 link）；
題目/批改敘述遵守可讀性規範（nested bullet 切割、長段斷點、不擠一行）。
