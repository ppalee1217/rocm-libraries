---
name: learning-roadmap-authoring
description: Use when writing, editing, restructuring, or rescheduling the 8-week internship learning roadmap (study_docs/learning-roadmap.md) or any similar day-by-day, actionable learning plan for this hipBLASLt / TensileLite repo. Defines the canonical/mirror sync rule, the per-day section structure (goal + nested checklists + completion criteria + quiz + note prompts), the read/run/write item conventions, the fact-checking rule, the per-phase depth policy, and how to embed AMD training resources.
---

# Learning Roadmap Authoring

Use this skill when the task is to produce or revise a **day-by-day, executable learning
plan** (the 8-week internship roadmap), not a code-trace report. This skill defines *how to
write the roadmap*, not the content of any one day.

## When to use / not use

- **Use** for `study_docs/learning-roadmap.md` and any similar "what to do each day to learn
  the codebase" schedule with checkable items.
- **Do not use** for prose onboarding / code-trace reports (runtime call-flow, subsystem
  overview, pipeline explainer). Those follow the `hipblaslt-code-trace` skill instead.

## Canonical / mirror sync rule (hard rule)

The roadmap exists in three places. **Only edit the canonical**
`study_docs/learning-roadmap.md`. The others are read-only mirrors:
- `.cursor/learning-roadmap.md`
- the Claude Code plan file `~/.claude/plans/rocm-libraries-repo-familiar-*.md`
  (may not exist on every machine — skip if absent).

Inside Claude Code a PostToolUse hook auto-copies canonical → mirrors on every edit. If the
hook does not fire (editing in Cursor, editing a mirror directly, or hook disabled), manually
sync: `cp study_docs/learning-roadmap.md .cursor/learning-roadmap.md`. Always finish by
`diff`-confirming the `.cursor` mirror matches canonical.

## Per-day section structure

Every working day is one `###` section in this fixed order:

```
### MM-DD（週幾）｜一句話主題
**今日目標**：一句話描述完成後能做到什麼。

- [ ] **搞懂/跑/寫/動手** <主 item＝一個學習目標或一個動手任務>
  - [ ] <可獨立勾選的子步驟 1>
  - [ ] <子步驟 2>
  - ✅ 完成判準：一句可自我驗證「真的懂了/做到了」的標準
  - 📚 參考資源：<現有 doc 節 / asm 行段 / codebase 路徑 / AMD 選做>；對應未來文件用「（待擴充：<doc>）」
- [ ] **（AMD 資源，選做）** <課程/talk + 為何在這天>
- **筆記提示**：今天該記下什麼；指向 `study_docs/notes/MMDD-{主題}.md`（用 learning-notes skill）。
- **快速自測**：題數視內容調整（非固定 2 題），答案放 `<details>`。
  1. <題目>
  ...
  <details><summary>答案</summary>
  1. …
  </details>
```

Rules:
- A non-working day (e.g. charge day) keeps the `###` header + one explanatory line and
  carries **no** `- [ ]` items.
- Keep 今日目標, AMD 選做, 筆記提示, 快速自測 on every working day.

## Item-writing conventions（目的導向）

- **Goal-oriented first**: a main item states **what to understand / what you can then do**
  (動詞用 搞懂 / 能解釋 / 能定位 / 能跑出), NOT "read file X". Docs/asm/codebase are demoted to
  the `📚 參考資源` line — they are the *means*, the understanding is the *goal*. (Reason: current
  teaching docs are thin and will grow; pinning items to today's doc wording rots fast.)
- Hands-on items still use **跑** / **寫** / **動手** with a copy-pasteable command block and the
  **expected output**.
- Expand a main item into **2–4 nested sub-checkboxes** = concrete understanding points (anchored
  to real functions/structs/`.s` line ranges), each independently checkable.
- End every expanded main item with **one** `✅ 完成判準` line + **one** `📚 參考資源` line.
- `📚 參考資源` cites: existing doc + section, asm `.s` line range, codebase path. If a topic maps
  to a planned-but-stub doc, append **（待擴充：<path>）** so the reader knows it will be filled in.
- Sub-items target **learning outcomes**, not memorizing current doc wording.

## 可讀性與排版（hard rule）

讀者最怕一行塞滿、一段到底。每個段落都要為「掃讀」優化。

- **一個 bullet 一個重點**：一條 bullet 若含 ~2 個以上獨立事實，必須拆成 **nested 子 bullet**
  （每個子項一個事實），不要用頓號/分號把多個事實串成一行。
- **清單優先於長句**：並列的多個項目（工具、參數、步驟、產物）一律用 bullet / nested bullet 或
  表格呈現，不要塞進同一句。
- **長 paragraph 要斷點分段**：只有「需要連貫敘述的說明性段落」才用完整 paragraph；即使如此，
  超過 ~3 行就要在語意斷點換段，或改成「一句 lead 句 + bullet list」。
- **`>` callout 要短**：一個 `>` blockquote 只放**一個**短重點；更長的內容改成 lead 句 + bullets，
  不要做多事實 blockquote。
- 階段總覽、風險、策略提醒這類「散文密集」的段落最容易違規，撰寫/重整時優先檢查。

## 檔案/文件引用必連 link（hard rule）

讓讀者在 Cursor 直接點 link 開檔，不必自己找路徑。

- 文中**每一個指向 repo 內實際檔案或目錄的引用**，都要寫成 markdown link，路徑相對本檔
  （roadmap 在 `study_docs/`，故 `projects/` 用 `../projects/...`、`asm/` 用 `../../asm/...`、
  `study_docs/` 內文件用相對檔名）。link 文字用符號/檔名：
  ```md
  入口無邏輯：`hipblasLtMatmul`（[hipblaslt.cpp](../projects/hipblaslt/library/src/amd_detail/hipblaslt.cpp)）只做型別轉換
  ```
- **link 文字不要包 backtick**：`` [`name`](url) `` 在多數 Markdown preview 會渲染成純文字、
  點不開，要寫成 `[name](url)`。backtick 只留給**非 link** 的 inline code。
- **適用對象**：`.py`/`.cpp`/`.s`/`.yaml` 等原始檔、實際產物檔、目錄路徑、`study_docs/` 內其他文件。
- **只連已存在的檔案**：補 link 前先確認檔案存在（`test -e` / `ls`）。**尚未建立的檔案**
  （如多數 `study_docs/notes/MMDD-*.md`）維持純文字或 inline code，待檔案建立後再連，避免死連結。
- **不適用（維持 inline code，不要連）**：副檔名當名詞（載入 `.co`）、env var
  （`HIPBLASLT_TENSILE_LIBPATH`）、CLI flag（`--print_kernel_info`）、指令片段、執行期產物目錄
  （`out/`、`3_LibraryLogic/`）。這些不是可導航的原始檔。
- 行號會漂移：引用前查證，不確定就連檔不加 `#Lx-Ly`（見下方 fact-checking rule）。

## Fact-checking rule (hard rule)

Section names, line numbers, file paths, and CLI flags must be **verified against the current
files before citing** — never invent them. Line numbers drift across commits; re-grep before
referencing. If unsure, cite the file without a line anchor rather than guess. This mirrors the
repo CLAUDE.md code-reference rule.

## Per-phase depth policy

- **P0–P2**: day-by-day detail (which section / which `.s` lines / which command / what you'll
  understand) + daily quiz + note prompt, with nested sub-checkboxes as above.
- **P3–P4**: framework form, not fixed daily steps (P3 is open-ended exploration). Provide a
  milestone list, a **decision tree** (layer-1 config fork → layer-2 codegen → layer-3 rocisa),
  and a **reusable "optimization iteration day" checklist template** (hypothesis → change →
  rebuild → bench median + `-v` → compare counters → log result), plus a progress self-check.

## AMD training resources

Embed company-internal resources as optional items marked **（AMD 資源，選做）** on the day
whose topic matches (e.g. HIP 100 Matrix Transpose on an LDS day; GCN talk #3 Memory/IO/CU on
the buffer day). Keep a summary table at the end of the file mapping each course/talk → 時長 →
對應階段 → 為何在這裡學, with relative links to the two PDFs in the repo root.

## Planned-but-stub docs（hybrid 文件策略）

Existing teaching docs are incomplete. When a goal needs a doc that doesn't fully exist yet,
create an **outline/template stub** rather than leaving a dead reference:
- A stub has: title, a `> 狀態：outline，待擴充` callout, a 「本文件將涵蓋」outline, 「為何重要 /
  對應 roadmap 哪幾天」, and 「目前可先看的替代資源」.
- List every stub in `study_docs/README.md`「規劃中文件（待擴充）」so the whole map is visible.
- Reference a stub from roadmap items via `📚 參考資源 …（待擴充：<path>）`.
- Current stubs: `cuda-to-hip.md`, `glossary.md`, `isa/gfx942-isa-reference.md`,
  `isa/mfma-deep-dive.md`, `isa/lds-bank-conflicts.md`, `hipblaslt/tuning-config-reference.md`,
  `hipblaslt/components-codegen-map.md`, plus a cookbook stub section in `profiling-rocprof.md`.

## Quizzes and notes are separate skills

- **Inline 快速自測** lives in the roadmap (per day, `<details>` answers, learner self-checks,
  flexible question count). Keep authoring these.
- **Deep interactive quizzes** are NOT written into the roadmap — they are generated on request
  by the **`learning-quiz`** skill into `study_docs/quizzes/MMDD-{Description}-quiz.md`.
- **Notes** are written by the learner (not the AI) via the **`learning-notes`** skill into
  `study_docs/notes/MMDD-{Description}.md`. The roadmap's 筆記提示 should point there.
- When authoring/adjusting the roadmap, keep these three in sync: the day's note/quiz filename
  Description should match the day's 主題.

## Language

Follow the repo CLAUDE.md: Traditional Chinese for narrative; keep technical terms, proper
nouns, function names, file names, and tool names in English. Lead with plain-language overview
before detail.

## Verification checklist

1. `diff study_docs/learning-roadmap.md .cursor/learning-roadmap.md` shows no difference.
2. Each working day has 今日目標 + checklist + 筆記提示 + 快速自測(含 `<details>` 答案); each
   expanded main item has nested sub-checkboxes + one `✅ 完成判準` + one `📚 參考資源`.
3. P0~P1 main items are goal-oriented (搞懂/能…), not "read file X"; docs sit on 📚 參考資源.
4. Cited `.s` line ranges fall within the real file length; section names exist; commands run.
5. Stub-doc references use（待擴充：<path>）and every stub is listed in README.
6. Nested checkboxes and `<details>` render correctly in Markdown.
7. 可讀性：無 run-on bullet（多事實已拆 nested 子 bullet）、長段已斷點或改 list、`>` 只放單一短重點。
8. 每個指向**已存在**檔案/目錄的引用都是相對路徑 markdown link；env var / flag / 副檔名名詞 /
   執行期產物目錄 / 尚未建立的檔維持 inline code，未誤連。
