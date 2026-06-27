---
name: hipblaslt-code-trace
description: Use when writing, editing, reviewing, or restructuring an onboarding or code-trace report (a user guide) that helps a reader quickly understand the hipBLASLt / TensileLite repository - its architecture, a specific runtime call flow, the kernel generation/selection pipeline, GEMM optimization entry points, or the profiling workflow. This skill standardizes how such a report explains structure, traces code with linked references, defines terms in plain language, uses diagrams, and stays self-contained for a reader with no prior context.
---

# hipBLASLt Code-Trace Report Writing

Use this skill when the task is to produce or revise a report whose goal is to help a
reader **quickly understand part of this repository** by reading prose next to the code.
Typical reports: a runtime call-flow trace, a subsystem overview, the TensileLite kernel
pipeline, GEMM optimization entry points, or a profiling workflow.

This skill defines *how to write the report*, not the content of any one report. Do not
hardcode "read file X then Y"; instead follow the conventions below for whatever flow the
report covers.

## Core principle

A code-trace report must explain not only **what** the code does, but **how the pieces
connect**. A reader with general GPU / C++ background but **no prior context** (no access
to earlier chats, PRs, or unstated assumptions) should be able to follow one chosen flow
end to end by reading the report alongside the linked code.

The report should make clear:

- What the reader will understand after reading it (the one flow or subsystem in scope).
- The plain-language mental model before any code.
- Each step of the flow, in order, with a link to the exact code.
- What the key data structures are and what role each plays.
- How to build / run something that exercises the flow, when applicable.

## Self-contained rule

The report must be understandable from the report alone.

- Do not rely on the reader having seen prior reports unless you cite and briefly summarize them.
- Do not reference "the function we discussed" or any conversation-only context.
- If background from another report is needed, link it and summarize the dependency in one or two lines.

## Audience and language

- Target reader: a new engineer / intern with limited repo context.
- Write narrative in **Traditional Chinese**; keep technical terms, function names, file
  names, and tool names in **English**. Do not force awkward Chinese translations.
- Tone: explain like onboarding a teammate, not like API reference docs.

## Plain-language rule

- **Overview first.** Open with a plain-language summary or analogy ("像餐廳收單 ->
  派工 -> 出菜") before any code reference.
- **First-use definition.** The first time a project or domain term appears, give a
  3-6 word plain-language gloss inline. Terms that usually need this: `GEMM`, `tile`,
  `MFMA`, `kernel`, `solution`, `heuristic`, `code object (.co)`, `epilogue`,
  `lazy load`, `contraction`, `workgroup`, `occupancy`.
- **Plain language, then term.** Every sentence should be understandable on first read;
  introduce the precise term after the plain wording, not before.

## Readability / formatting rule (important)

Readers bounce off walls of text. Optimise every section for scannability.

- **一個 bullet 一個重點 (one idea per line).** Do not chain multiple facts with 頓號/
  分號 into one run-on bullet. If a bullet carries more than ~two facts, split into
  **nested sub-bullets**, one fact each.
- **清單優先於長句 (list over long sentence).** When you are enumerating parallel things
  (steps, params, products, tools), use a bullet / nested-bullet list or a table — never
  pack them into a single sentence.
- **長 paragraph 要斷點分段.** Reserve full paragraphs for genuinely connected narrative.
  Even then, break at a semantic boundary once a paragraph runs past ~3 lines, or convert
  it to a lead sentence + bullet list.
- **`>` callouts stay short.** A `>` blockquote holds **one** short idea. Anything longer
  becomes a lead line + bullets, not a multi-fact blockquote.

## Code reference rule (important)

This replaces the messy habit of pasting absolute paths into prose.

- Cite every concrete code location as a **markdown link** whose text is the symbol or
  function name and whose URL is a **path relative to the report file** plus a line anchor.
- **Do NOT wrap the link text in backticks** — `` [`name`](url) `` renders as raw text (no
  clickable link) in many Markdown previews. Write `[name](url)`. Backticks are only for
  standalone inline code that is **not** a link.
  Reports live inside the repo at `study_docs/hipblaslt/`, so the path climbs out of
  `study_docs/` back to the repo root and into `projects/`; recompute the `../` depth from
  the actual report location:

```md
[runContractionProblem](../../projects/hipblaslt/library/src/amd_detail/rocblaslt/src/tensile_host.cpp#L3235-L3463)
```

- Do **not** paste bare absolute paths inline; they make the document hard to read.
- **Verify line numbers** against the current code before citing - search by symbol name,
  because line numbers drift across commits. If you cannot confirm the range, link the
  file without a line anchor rather than guess.
- Link the **definition site** of a function or struct, not an arbitrary call site, unless
  the call site is the point being made.
- Present a flow's links **in execution order** so the reader can step through them.
- For a list of structures, prefer a table: name | plain-language role | link.
- **Link every reference to a real file or directory** that exists in the repo, so the
  reader can click straight to it. **Link only files that exist** — verify before linking;
  do not create dead links to not-yet-written files.
- **Do NOT link** (keep as plain `inline code`): a bare extension used as a noun
  (「載入 `.co`」), a C++ type (`const void*`), an env var (`HIPBLASLT_TENSILE_LIBPATH`),
  a CLI flag (`--print_kernel_info`), a command fragment, or a runtime-generated output dir
  (`out/`, `3_LibraryLogic/`). These are not navigable source files.

## Diagram rule

- Use a **mermaid** `flowchart` for any multi-step flow or architecture; a picture of the
  pipeline saves paragraphs of prose.
- Keep node labels short; use `subgraph` to separate phases (e.g. build-time vs runtime).
- Follow mermaid constraints: no spaces in node IDs, quote labels with special characters,
  no custom colors/styling, no `click` events.

## One-topic-per-report scope

- One report covers **one coherent flow or subsystem**. Do not mix unrelated flows.
- If a related flow matters, link to its (separate) report and summarize the connection in
  one line, instead of expanding the current report.

## Required content

A complete code-trace report should contain, in roughly this order:

1. **Plain-language overview** - analogy + a 30-second summary of the flow in scope.
2. **Architecture / flow diagram** - a mermaid flowchart of the steps.
3. **Step-by-step trace** - each step: plain explanation, then linked code reference(s),
   then any key data structures touched.
4. **Key data structures** - a table of the structs/classes the reader keeps seeing.
5. **How to build / run / observe** - the command that exercises this flow, when relevant.
6. **Terminology** - inline first-use glosses, or a short glossary if many terms.
7. **Cross-links** - related reports, and the official `AGENTS.md` for build / PR rules
   (do not duplicate that content here).
8. **One-line takeaway** + a pointer to the logical next report.

## Recommended structure template

Use this skeleton for a new report (section guidance is in Chinese; fill with real content):

````md
# <主題：這份報告帶讀者理解哪一條流程 / 子系統>

> 路徑基準：所有 code 連結為相對於本檔的相對路徑；行號可能隨 commit 漂移，對不上時以符號名稱為準。

## 白話總覽
- 用比喻 + 30 秒摘要說明這條流程在做什麼、為什麼存在。

## 架構 / 流程圖
```mermaid
flowchart TD
    A[Step A] --> B[Step B]
```

## 逐步 trace
1. **<步驟名>** - 白話說明這一步在做什麼。
   - 程式碼：[symbolName](<relative/path>#L起-L迄)
2. ...

## 關鍵資料結構
| 結構 | 角色（白話） | 位置 |
|------|--------------|------|
| `Foo` | 一句話說明 | [Foo](<relative/path>#L..-L..) |

## 如何建置 / 執行以觀察此流程
- 指令與預期輸出（若適用）。

## Terminology
- `term` - 3-6 字白話解釋。

## 交叉連結
- 相關報告：[other-report](<relative/path>)
- build / PR 規範見官方 [AGENTS.md](<relative/path/AGENTS.md>)（本報告不重複）。

## 一句話總結
> ... 下一篇看 [next-report](<relative/path>)。
````

## Anti-patterns

- Pasting bare absolute paths into prose instead of relative markdown links.
- A wall of jargon with no plain-language overview or first-use definitions.
- Mixing several unrelated flows into one report.
- Guessing line numbers without verifying them against the current code.
- Re-explaining build / PR rules already covered by the official `AGENTS.md`.
- Run-on bullets that pack many facts into one line.
- Multi-fact `>` blockquotes; reserve `>` for one short callout idea and split anything longer into a lead line + bullets.

## Self-audit before delivery

Before finalizing a report, confirm:

- [ ] Opens with a plain-language overview or analogy.
- [ ] Has a mermaid flow / architecture diagram for any multi-step flow.
- [ ] Every code reference is a relative-path markdown link, and the line ranges were verified.
- [ ] Each project-specific term is defined on first use.
- [ ] A reader with no prior context can follow the flow from the report alone.
- [ ] The report stays within one topic; related flows are linked, not merged.
- [ ] Ends with a one-line takeaway and a pointer to the next report.
- [ ] No run-on bullets / over-long paragraphs: multi-fact bullets are split into nested
      sub-bullets, long paragraphs are broken at a semantic boundary or turned into lists.
- [ ] Every reference to an existing repo file/directory is a clickable relative-path link;
      extensions/types/env vars/flags/output dirs are left as plain inline code, not linked.
