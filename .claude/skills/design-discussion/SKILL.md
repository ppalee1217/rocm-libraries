---
name: design-discussion
description: For a research or EXPERIMENT-DESIGN DIRECTION decision that needs genuine reasoning — choosing/designing an experiment, approach/method selection, judging whether a direction or hypothesis is sound, turning an ambiguous/counterintuitive/negative result into a conclusion, deciding the next research step, or evaluating a claim's validity. Claude forms its own view AND delegates the same question to an independent Codex agent, then cross-examines both to a unified conclusion; a real experiment-design change is handed to the user for approval. NOT for lookups, mechanical repairs, ordinary implementation choices, resource/bookkeeping/cleanup decisions, workspace drift, or a choice with an obvious conventional default.
---

# Design Discussion (dual-agent cross-examination)

**Purpose.** A single agent has blind spots and anchoring bias. For research / experiment-design **direction** decisions, don't answer alone: form your own view, get an *independent* Codex view on the **same** question, then cross-examine and debate until you reach a conclusion both would sign off on. The value is each agent catching the other's blind spot — not a rubber-stamp in either direction.

Claude is the orchestrator: it prepares the shared prompt, relays each side's arguments faithfully, checks evidence, and turns the outcome into a decision packet for the user. A real experiment-design change is the user's call — reviewer agreement is analysis, not design authority.

**Codex model policy.** Start Codex threads with `model: gpt-5.6-sol` (or the latest available Codex-capable model) and `reasoning-effort: xhigh`. These are pure-reasoning calls (no GPU / no long campaign), so they return without an idle timeout; keep each prompt focused. If the model is unavailable, escalate rather than silently downgrade.

## Step 0 — Recognize the trigger

Use this only when the delegated thing is a **direction decision requiring reasoning**. Positive triggers:

- which experiment to run / how to design it; what would (in)validate a hypothesis;
- approach or method selection (A vs B, or "is there a better one");
- whether a research direction / framing / assumption is sound;
- interpreting an ambiguous, counterintuitive, or negative result into a conclusion;
- what the next research step should be; whether a claim is valid or over-concluded.

Do **NOT** use it for (this list is deliberate — these misuses are what made the old workflow waste time):

- lookups, finding a symbol, explaining existing code, or mechanical edits;
- code implementation — that is `implement-verify-loop`;
- **operational / bookkeeping decisions**: cleaning up files or old artifacts, resource accounting, disk/storage, telemetry gaps, run scheduling;
- **workspace drift**: an unrelated file appearing or changing outside the experiment;
- a choice with an obvious conventional default, or one that is purely the user's preference to state.

If it isn't a genuine experiment-design ambiguity that would change protocol, claim, measurement, stopping rule, or scientific authority, do not convene a discussion — just decide and move on.

## Step 1 — Form your own view FIRST (independence)

Reason it through yourself and write down a concrete position **before** consulting Codex, so you are not anchored by it: the answer/recommendation, the key arguments, the assumptions it rests on, and your explicit uncertainties.

## Step 2 — Delegate the SAME question to an independent Codex

Start a fresh `mcp__codex__codex` thread. Give it a **self-contained** prompt (Codex does not share your context) with the same background and the same question — but do **NOT** include your own answer; keep its view independent. Give it the repo root and readable paths for the relevant design docs, code, or data so it can ground claims. Ask for its critical, defensible position, its assumptions, and its uncertainties, and tell it you will cross-examine so it should argue, not hedge.

## Step 3 — Cross-examine / debate (the actual work)

Compare the two views. Run 1–3 rounds via `mcp__codex__codex-reply` on the same thread that:

- name the genuine **agreements, disagreements, and gaps** explicitly;
- **push hard on the real tension points** — do not just capitulate to Codex, and do not let Codex rubber-stamp you; probe the disagreements until they resolve;
- **accept the other side's sharpening/correction when it is right**; push back with a reason when you disagree;
- surface each side's **hidden assumptions** and test them against evidence.

Be genuinely critical of **both** positions, including your own. Ground contested points in the repo / data / prior results where the decision depends on facts (Read/Grep/Bash), not vibes. Keep it bounded: if a factual disagreement shows no progress after a couple of exchanges, move to the final positions rather than looping.

## Step 4 — Converge (or honestly diverge)

Converge only after the views actually reconcile: agreements + resolved disagreements + a single position **both would sign off on**. State that unified conclusion explicitly and have Codex confirm it in one line. If the two **genuinely cannot converge**, report the honest disagreement and the reason — never manufacture a fake consensus.

## Step 5 — Hand a real design change to the user

- If the deliberation resolves a genuine experiment-design ambiguity — a change to protocol, claim, measurement/lineage, stopping rule, acceptance threshold, evidence source, or scientific authority — present the unified conclusion (or preserved dissent) to the **user as a decision packet** and pause the affected design path until the user decides. Reviewer agreement, even to keep the current design, does not by itself authorize resuming that path.
- If it is not an experiment-design change (an ordinary in-scope method choice already within the plan), you may act on the unified conclusion directly and record it.

The decision packet states: the problem and its scope; the unified recommendation or the two preserved positions; the core reasoning, evidence, and assumptions; acceptance criteria / falsification conditions where relevant; and the minimal choice the user must make.

## Step 6 — Report (and record if durable)

Give the user the unified conclusion (or the preserved dissent), noting it is the product of dual-agent deliberation and the key points where cross-examination changed either view. If the decision is a durable direction/finding, record it in the governing design/experiment doc under `study_docs/research/` per the repo doc conventions, citing the Codex thread id for provenance. Do not paste raw chat or private chain-of-thought.

## Doc & readability standard

Anything written back follows the repo readability rule: no hard-wrapping for column width; one idea per line; nested bullets for multi-part claims; at most one `（…）` per sentence; Chinese-English half-width spacing, with identifiers/paths/hashes/commands kept byte-for-byte.

## Principles

- **Independence first** — your view before Codex's; never feed Codex your answer up front.
- **Critical, not deferential** — the skill fails the moment it becomes a rubber-stamp either way.
- **Evidence over vibes** — settle factual cruxes against the repo/data/prior results.
- **Honest non-convergence > fake consensus.**
- **Design authority is the user's** — a real experiment-design change waits for the user's decision; consensus cannot invent intent or grant commit/push/credential/external/container authority.
- Do not over-conclude from the debate itself — a two-agent consensus is still bounded by both agents' shared blind spots and the available evidence; mark residual uncertainty.
