---
name: learning-notes
description: Use when the learner wants to start or update a personal study note for a day of the 8-week internship learning roadmap. Notes live in study_docs/notes/ named MMDD-{Description}.md (Description = that day's main goal). The learner writes the content themselves; the AI only scaffolds from the template and helps add/verify code references and doc links — it does NOT write the learning content for them.
---

# Learning Notes（學習筆記）

協助學習者建立 / 維護每日學習筆記。**筆記內容由學習者親手寫**——這是他自己的學習記錄與理解輸出；
AI 的角色僅限：開檔套 template、依要求補 code reference / doc link、檢查連結與行號正確。

## 核心原則（重要）

- **不代寫學習內容**：不要替學習者填「我學到什麼 / 我的理解」。那是他思考的產物，代寫會破壞學習。
- AI 可做：建立 template 骨架、把學習者口述的重點**格式化**、補上正確的 code/doc 連結、
  檢查他引用的行號/路徑是否正確、指出筆記裡與現況不符之處。
- 若學習者請你「幫我寫筆記」，澄清：你可以幫他整理他講的內容與補連結，但理解要由他自己寫。

## 檔名規範

- 路徑：`study_docs/notes/MMDD-{Description}.md`
- `MMDD`＝該天日期；`{Description}`＝該天 roadmap 的「今日目標 / 主題」精簡化（中文或 kebab 皆可）。
- 範例：`0625-建立全局地圖.md`、`0630-profiling驅動優化.md`、`0703-example03-MFMA-GEMM.md`。
- 與當天 quiz 檔名對齊（`study_docs/quizzes/MMDD-{Description}-quiz.md`）。

## 開新筆記流程

1. 確認日期與當天 roadmap 小節的「今日目標」，據此定 `{Description}`。
2. 複製 `study_docs/notes/_template.md` 成 `study_docs/notes/MMDD-{Description}.md`。
3. 把 template 的「今日目標」「對應 roadmap 主 item」預填好（這是事實，可代填），其餘留空白給學習者。
4. 告訴學習者檔案已開好，請他自行填寫；需要補連結時再找你。

## 協助補引用（AI 可做的部分）

- code reference：用 markdown link + 行錨點，路徑相對該筆記檔，例如
  `[runContractionProblem](../../projects/hipblaslt/.../tensile_host.cpp#L3235-L3463)`。
- doc link：連到 `study_docs/` 內相關文件或 stub。
- **每個指向實際檔案/目錄的引用都要連成 link**，且**只連已存在的檔**（連前確認存在，避免死連結）。
  link 文字**不要包 backtick**（`` [`name`](url) `` preview 會點不開），寫成 `[name](url)`。
  不要連 env var（`HIPBLASLT_*`）、CLI flag、副檔名名詞（`.co`）、執行期產物目錄——這些維持 inline code。
- **行號先查證**再寫；會漂移，不確定就連檔不加行號（遵 repo CLAUDE.md code-reference rule）。

## 可讀性（格式化時遵守）

AI 幫學習者把口述重點格式化時，套用同一套可讀性規範：

- 一個 bullet 一個重點；多事實拆成 nested 子 bullet，不要串成一行。
- 並列項目用 list/表格；長段落超過 ~3 行在語意斷點分段或改成 lead 句 + bullets。

## Template 章節（見 `_template.md`）

今日目標 / 對應 roadmap item → 我學到什麼（自寫）→ 卡關與如何解（自寫）→ code & doc 參考（AI 協助）
→ 待釐清（自寫）→ 隔日 todo（自寫）。

## 語言

遵 repo CLAUDE.md：繁中敘述，技術名詞 / 函式 / 檔名 / 工具名保留英文。

## 驗證

筆記檔名符合 `MMDD-{Description}.md`；template 章節齊全；AI 補的每個連結路徑/行號都經查證
（只連已存在的檔）；AI 協助格式化處遵守可讀性規範（nested bullet 切割、長段斷點）；
學習內容欄位保持由學習者填寫（AI 未代寫）。
