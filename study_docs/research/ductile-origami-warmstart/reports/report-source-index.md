# Report Source Index — Formocast Factorized Gen0 Guidance study (S11 + S14)

> **SYNC:** authoritative English source. A Traditional-Chinese mirror is kept at
> [`report-source-index.zh-Hant.md`](report-source-index.zh-Hant.md); **any edit here must be mirrored
> there** (translate prose only; keep proper nouns / code / paths / § numbers / numbers / tables /
> amendment tokens / gene names / evidence labels / sha256 in English). On conflict, this English file wins.

> **Non-authority, living reference.** This document exists so the closing report can be drafted from ONE
> place. It **consolidates and cross-references** the authoritative docs; it does **not** create policy.
> On any conflict, the authoritative source wins (order: **charter > experiment-plan > design > this
> index / report > qa**). All experiment-planning rationales below already live in an authoritative doc
> (cited inline) — nothing here is new policy.
>
> **Anti-fabrication:** every result value is `NOT_EVALUATED` with a source path until the run finishes
> and an independent verifier fills it. `not_evaluated ≠ no effect`. **Last updated 2026-08-13.**
>
> **Current execution reality (2026-08-13):** the **capped (P0 = 512)** campaign is **complete on all
> three shapes** — baseline 15/15, guided 15/15, and 7× interleaved remeasures done for medium, large and
> tiny. The **native (P0 = 11,405)** addendum is complete for **medium** (5/5 GA + 5/5 remeasure) and
> **still running for large**: five baseline seeds are in Gen0 sampling and have not yet produced a
> trajectory row. Native large has now lost its Gen0 to four consecutive host reboots — Ductile writes no
> checkpoint until generation 1 completes, and Gen0 at 11,405 samples has not fit inside any inter-reboot
> window (~4–5.5 h) — so whether it is reachable on this host is an open owner decision.
>
> Two things changed the evidential picture on 2026-08-13 and are reflected throughout: the **clock-ramp
> mechanism was disconfirmed** by direct telemetry (the warm-up *correlation* survives; the *explanation*
> does not — §7.1b), and the S14 reports were consolidated under `REPORT-LOCATION-20260813` into
> `reports/staged/` as one formal report plus three per-shape annexes (§6).
>
> Nine items remain `PENDING_HUMAN_DECISION` (§9.3). The combined claim wording requires medium ∧ large
> (**charter** §8.2 — not this file's §8.2, which is Checkpointing).

## Contents

- [§0 Conventions](#0-conventions)
- [§1 Experiments at a glance](#1-experiments-at-a-glance)
- [§2 Amendment ledger](#2-amendment-ledger-token--change--authority)
- [§3 Design rationale](#3-design-rationale-report-ready-prose--each-with-source)
- [§4 Claim framework](#4-claim-framework-what-can--cannot-be-said)
- [§5 Metrics & acceptance](#5-metrics--acceptance) — incl. [§5c AUC](#5c-what-the-auc-criterion-is-and-why-the-measurement-defect-does-not-reach-it)
- [§6 Artifact / file reference](#6-artifact--file-reference)
- [§7 Results placeholders](#7-results-placeholders-fill-after-runs--independent-verification--do-not-fabricate)
- [§8 Known caveats / limitations](#8-known-caveats--limitations-for-the-discussion-section)
- [§9 PENDING_HUMAN_DECISION — medium measurement defect](#9-pending_human_decision--disposition-of-the-medium-remeasure-measurement-defect) — incl. [§9.5 peak-of-7](#95-pending_human_decision--peak-of-7-as-mediums-endpoint-the-capability-argument)

---

## §0 Conventions

- **Evidence labels** (use consistently in the report):
  - `[MODEL-ONLY]` = Formocast model-space quantity (S11 scores, per-shape `S_g`);
  - `[BASELINE GPU]` = Arm G real measurement;
  - `[GUIDED GPU]` = Arm F real measurement;
  - `[CODE AUDIT]` = fact read from code/artifact (cite file:line / path).
- **Seeds are the experimental units** (5 paired seeds 24001–24005). Never repackage a few seeds as
  statistical significance.

---

## §1 Experiments at a glance

| Experiment | Purpose | Status (2026-08-11) | Key artifact / lock | Report section |
|---|---|---|---|---|
| **S11 model-only factorization** | Is the per-gene Formocast→Gen0 guidance mechanism sound in model space; how sparse is the signal | per-size scores **DONE**; max-reducer closeout **CANNOT COMPLETE** — sealed `analyze` structurally asserts (see §7.3), proven via a verified out-of-band parallel reproduction | `s11-native-scores.json`; `parallel-analyze/VERIFICATION.md` | S11 report |
| **S14 capped-512 per-shape G/F** (primary) | Does a Formocast Gen0 prior improve per-shape search/final quality vs uniform, at P0=512 | **COMPLETE** — baseline 15/15, guided 15/15, 7× remeasure done on all three shapes (`guided_status.json`: `guided_complete: true`) | Lock A + Lock B | `staged/full-ga-baseline-vs-guided-outcome-report.md` §3 |
| **Conditional Arm S** (same-entropy shuffle) | Attribute any F>G to physics *direction* vs mere concentration | **DOES NOT TRIGGER** — the trigger requires F to clear the gate on ≥1 confirmatory shape; neither medium nor large does (§9.1). Lock C therefore does not need sealing for this checkpoint | Lock C (Arm-S shuffle, seal not required) | `staged/full-ga-baseline-vs-guided-outcome-report.md` §3.5 |
| **Native-P0 ~11,405 addendum — medium** | (Q1) robustness of the capped direction at native Gen0; (Q2) dilution; (Q3) Gen0 extreme mechanism | **COMPLETE** 5/5 GA + 5/5 remeasure (also remeasured twice; see the campaign correction in §9.2). Final endpoint `NOT_EVALUATED / instrument-invalid` | reuses Lock B guidance | `staged/s14-medium-report.md` §4 |
| **Native-P0 ~11,405 addendum — large** | same three questions at large | **IN PROGRESS** — 5 baseline seeds in Gen0 sampling, no trajectory rows yet; four consecutive Gen0 losses to host reboots | reuses Lock B guidance | `staged/s14-large-report.md` §10 (scaffold) |

---

## §2 Amendment ledger (token → change → authority)

| Token | What it changed | Authority doc |
|---|---|---|
| `RESCOPE-STAGE1-OUTCOME-20260807` | S12+ frozen; only active edge S11→S14; P0 64→512; native early-stop kept; U_floor hard-gate removed | experiment-plan active-projection; S14 §6 |
| `PER-SHAPE-SOO-OUTCOME-20260809` | Joint-MOO + aggregate `Q=max_s` → **per-shape single-objective** (per-shape GA/guidance/eval; medium+large confirmatory, tiny exploratory; 5 fresh seeds; two-sided; per-shape gate) | S14 design **§10**; experiment-plan criterion `S14_PER_SHAPE_OUTCOME` |
| `ENTROPY-CAP-20260810` | Binary gene exclusion → **universal per-gene mixture cap** `p1=(1−ρ)p0+ρ·q(λ=8)`, `ρ=max{ρ∈[0,0.80]:H_norm≥0.80}`; includes DepthU/PrefetchGlobalRead at reduced strength | S14 §10.3; qa-09 §4.3a |
| `CLAIM-SCOPE-S14-20260810` | S14 claims **two-sided**; a **final tuned-quality improvement IS claimable** if data supports (bounded/modest power, tested shapes, no pre-conclusion, no fabrication) | charter **§8.6a** |
| — 2026-08-10(b) extension | **beat-native** released from absolute prohibition to **two-sided / wait-for-data** (needs actual native measurement + confounding disclosure) | charter §8.6a 2026-08-10(b); §8.6 note |
| `CONDITIONAL-ARM-S-20260810` | Arm S pre-registered as **conditional** (trigger + attribution rule; S20 is its primary home) | S14 §10.2 |
| `NATIVE-P0-ROBUSTNESS-20260811` | Pre-registered **native-Gen0 (~11,405)** robustness/dilution addendum | S14 **§12**; experiment-plan criterion note |
| `NATIVE-P0-ROBUSTNESS-20260811(b)` | Extends that addendum from **large-only to large + medium**; adds **Q3** extreme-value manipulation test with pre-registered directional predictions | S14 **§12.1 Q3, §12.2, §12.4.4, §12.6** |
| `DEVIATION-REMEASURE-STOPLINE-20260812` | Remeasure pre-flight guard relaxed to the invariants that actually matter (**at most one** stop line; run must **not exceed** gen 30) after it rejected three design-conformant runs; measurement logic unchanged | this index §8.4 |
| `REPORT-LOCATION-20260813` | **Bookkeeping only** — `formal_report_path` moved to `reports/staged/…`; three per-shape annexes added. Changes **no** hypothesis, estimand, metric, threshold, gate or claim | S14 design **§12A** |
| `CAPABILITY-ENDPOINT-PACKET-20260813` | `PENDING_HUMAN_DECISION` — rejects peak-of-7 as medium's endpoint on three independent grounds; records that the count-invariance claim is **false** (`max` crosses the pre-registered §12.3 ≥4/5 line toward the treated arm on both native campaigns); bars `max` from every acceptance/sensitivity table; closes §13.7 item 2 via a deterministic `int32` overflow | S14 design **§14**; this index **§9.5** |
| `MEASUREMENT-DEFECT-PACKET-20260813` | `PENDING_HUMAN_DECISION` — disposition of the medium remeasure defect: estimator (D1), margin (D2), per-shape claim ladder (D3), nine owner items | S14 design **§13**; this index **§9** |
| `REDUCER-FACT-CORRECTION-20260812` | **Documentation-only factual correction** — Ductile implements **no Pareto/non-dominated sorting**; `soo=False` reduces to a scalar via `np.max` (`ga.py:95, 256–273`), so `Q=max_s` is Ductile's **native** fitness, not a post-hoc added step. **No change to decision, pins, gates or claims**; the empirical case for per-shape (tiny-dominated Q, seed-14005) is unaffected — the corrected argument is that Ductile's *built-in* cross-size reducer is itself the defect, which per-shape bypasses. | S14 §10.1 correction box; qa-09 §2.1/§2.2; this index §3.1.2 |

---

## §3 Design rationale (report-ready prose — each with source)

> **⚠ Which `ga.py` the `ga.py:NNN` citations index — added 2026-08-13 after audit.** There are **two
> copies of `ga.py` in this repo and they are not the same file**:
>
> | copy | path | lines | `DUCTILE_FORCE_P0` |
> |---|---|---:|---:|
> | **repo** (line numbers below resolve here) | `projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py` | 756 | **0 occurrences** |
> | **engine — the copy the runs actually executed** | `agent_run/260807-s14-baseline-run/engine/projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py` | 346 | 4 occurrences |
>
> Every `ga.py:NNN` citation in this document has been verified to resolve **against the repo copy**, and
> those line numbers are correct there. But the **experiments ran the engine copy**, whose content at
> every one of those line numbers is different. Two consequences a reader must not trip over:
>
> 1. **Mechanism claims cited to `ga.py:NNN` describe the algorithm as it exists in the repo tree.** Where
>    the two copies agree on behaviour that is harmless; where they do not, the engine copy governs what
>    actually happened.
> 2. **The `DUCTILE_FORCE_P0` claim in §3.2b is true only of the engine copy** — the env var does not
>    appear in the repo copy at all, so that particular citation must be read against
>    `engine .../ga.py:112`, not the repo line.
>
> `NOT_EVALUATED`: a line-by-line divergence map between the two copies. Only the `DUCTILE_FORCE_P0`
> branch has been checked.


### §3.1 Per-shape single-objective (not joint-MOO / aggregate-Q)

#### §3.1.1 Vocabulary

- **candidate** — one complete 30-gene kernel config; a member of the GA population.
- **champion** — *the single candidate selected as the run's answer*: the best valid candidate seen
  through the whole run (final incumbent), canonical-hash ascending tie-break. So a champion **is** a
  candidate — the winning one. Everything the report compares (`best_fitness`, the 7× remeasure) is a
  property of that one config.
- **`GFLOPS_s`** — a candidate's measured real throughput **on problem size `s`**. With 3 sizes, each
  candidate has 3 such numbers.
- **`R_s`** — a **per-size reference GFLOPS used as a normalizer**: `[CODE AUDIT]` the runner documents
  it as *"R_s = pilot per-size median GFLOPS"*, taken from the reused 3-anchor × 7-repeat noise pilot
  (medium 3,199.94 / large 180,336.00 / tiny 0.75). Its job is to make sizes **commensurable**: raw
  GFLOPS differ by ~5 orders of magnitude across tiny→large (§3.6.1), so `GFLOPS_s / R_s` converts each
  size to a dimensionless "fraction of that size's reference", which can then be compared or combined.
- **`Q`** — the **scalar fitness** the GA maximizes for a candidate, obtained by reducing its per-size
  normalized scores into one number.

#### §3.1.2 How `soo=False` actually works — it is a `max` reduction, NOT a Pareto front

**Correction of a common description** (including an earlier draft of this index): although `soo=False`
is called "multi-objective", **Ductile performs no Pareto / non-dominated sorting**. `[CODE AUDIT]` a
tree-wide search for `pareto|non-dominated|nsga|crowding` returns **nothing**. What actually happens
(`ga.py:256–273`):

```python
best.F = scores.max(1)                                   # per-size incumbent: best score on each size
pop.F  = self.reduce_fn(scores / best.F[..., None], 0)   # reduce_fn = np.max  (soo=False)
                                                         #           = np.mean (soo=True)
```

- `scores` is a **(n_sizes × N) matrix** — one row per problem size, one column per candidate.
- Each candidate's per-size score is divided by that size's reference, then the rows are **collapsed
  into one scalar** per candidate.
- `soo=False` ⇒ the collapse is **`np.max`** ⇒ `Q_c = max_s ( GFLOPS_{s,c} / R_s )`;
  `soo=True` ⇒ it is `np.mean`.

So the "objectives" never coexist: they are averaged (`mean`) or, here, **a candidate is judged solely
by its single best size** (`max`). There is no front, no dominance relation, and therefore no
multi-objective trade-off preserved.

#### §3.1.3 Why a single champion is needed at all

The GA must rank candidates to do selection, and the run must end with **one** config to benchmark,
remeasure and report. A set-valued answer (a front) cannot be fed to selection or to a paired G-vs-F
comparison. Hence the reduction to one scalar `Q`, and then to one champion.

#### §3.1.4 Why `Q = max_s` is defective

Taking the **maximum** over normalized sizes means a candidate is scored by **whichever single size it
happens to look best on** — the other two sizes are discarded. Because tiny is the noisiest shape by far
(η_tiny = 0.4466 ≈ ±45 %, vs η_medium = 0.0042 ≈ ±0.4 %; §3.6.1), a lucky tiny measurement can dominate
the whole score.

Observed consequence in the pilot: **seed-14005's champion was ~2× faster on large yet received the
*lowest* Q** — the metric picked its winner using the noisiest dimension.

#### §3.1.5 The fix

Run **one single-objective GA per shape**, with per-shape guidance and per-shape evaluation. Then no
cross-size reduction is needed at all: the fitness matrix is (1 × N) and `max` over one row is the
identity, so `Q = GFLOPS / R_s` is just the (normalized) real throughput on the shape being optimized.

The 3 divergent shapes then serve their real purpose — **size diversity** across which to check whether
the guidance effect reproduces — rather than being co-optimized into a single compromise answer.

*Source: `[CODE AUDIT]` `algorithm/ga.py:95, 256–273` (reduce_fn, no Pareto machinery);
`scripts/run_pershape_seed.py` (R_s definition, `(1,N)` fitness); Lock A (`champion_per_shape`,
per-shape η_s); S14 §10.1; qa-09.*

### §3.2 Why P0=512 (and the honest external-validity correction)

512 is not an arbitrary floor: it is Ductile's **own steady-state population** — the config default
(`ga.py:47`, `defaults.yaml`) and the **decay target** `_pop_size` (`ga.py:110`) that native Ductile
converges to. Native inflates Gen0 to `int(max_sp_sz×1.15)=int(9,918×1.15)=11,405` (`ga.py:118`) then
halves the excess back toward 512 each generation (`ga.py:116` applied at `:293`).

That inflation exists **solely to cover group_0** (the 9,918-candidate MatrixInstruction/WorkGroup
gene), which is **outside the Formocast treatment** and **identical in both arms**.

Honest two-part framing:

- **(a) Affects absolute results / external validity.** Capping to 512 **does** shrink the group_0 /
  overall search → it affects absolute champion quality — **hence the claim is scoped to
  "P0-capped=512 Ductile variant", not native Ductile**.
- **(b) Does NOT bias the G-vs-F paired contrast.** Both arms sample group_0 from the same p0 with
  common Gen0 uniforms, so the reduced coverage is a shared boundary condition that cancels in the
  within-pair difference, leaving the free-gene reweighting as the sole exogenous difference.

Caveat: the measured effect is "the effect at P0=512" (**treatment×budget interaction**), which the
native addendum (§3.3) probes.

*Source: S14 §6.1/§10.2, S14 report §2.3.*

### §3.2a Where `9,918` and the `×1.15` come from

**`max_sp_sz` is just the largest gene's candidate-list length.** `space.py:71` defines
`self.sizes = {k: len(v) for k, v in space.items()}` — a gene's "size" is literally *how many entries
its candidate list has*. `ga.py:112` then takes `max_sp_sz = max(sz for sz in self.space.sizes.values())`
over all 30 genes. The 29 ungrouped free genes have only 2–6 values each, so the maximum is set by
`group_0`.

**`group_0` = 9,918 because the frozen YAML literally lists 9,918 entries.** `[CODE AUDIT]`
`grep -c "MatrixInstruction:" protocol/v1/inputs/s10-generated.yaml` → **9918** (exactly), matching the
registry's recorded expanded group cardinalities `9918 / 3 / 2`. So 9,918 is **not a computed product of
axis ranges** — it is an **enumeration length**: GEKO's generated pool of candidate kernel macro-shapes.

What those 9,918 entries are, concretely:

- each entry is a full **MatrixInstruction 9-tuple** (plus an optional `WorkGroup:` override — 262
  entries carry one), annotated with its MacroTile / ThreadTile / WorkGroup / GSU / LSU / occupancy
  metadata;
- they span **434 distinct MacroTile shapes** and are annotated against **13 distinct problem sizes**
  (the sizes GEKO generated them for);
- only **840 of the MatrixInstruction tuples are distinct** — entries repeat, distinguished by the
  accompanying WorkGroup/other fields and by the size they were generated for.

So group_0 is best read as *"the pool of kernel shapes GEKO considers worth trying, accumulated across
problem sizes"*, and `9,918` is the size of that pool — a property of the frozen input YAML, not of the
GA.

**Two things 9,918 is NOT:**

- **Not a Ductile design limit.** Ductile imposes **no upper bound on a gene's cardinality**: `space.py`
  only rejects an *empty* list (`if any(v == 0 …): raise`), and `ga.py:107` only requires
  `n_perms ≥ pop_size`. A gene with a million candidates would be accepted.
- **Not a theoretical maximum number of MatrixInstruction × WorkGroup combinations.** It is a *curated
  enumeration*, not a Cartesian product — 9,918 entries contain only **840 distinct MatrixInstruction
  tuples**, repeating with different WorkGroup / target-size context. Swap the input YAML and the number
  changes.

**The `×1.15` is an undocumented magic constant.** `[CODE AUDIT]` There is **no comment and no doc**
anywhere in the ductile tree explaining it; the only related text is the warning string at `ga.py:114`
("Some variables have a larger search space than pop_size. Increasing pop_size for the first
generations."). Its *functional* intent is inferable: with `pop_size=512` and a 9,918-entry gene, at most
512 of those shapes could ever appear in Gen0 (≈95 % of the pool unseen), so the constructor raises
pop_size to roughly **one draw per candidate plus 15 % slack**.

**What `11,405` actually is — a common misreading, worth stating explicitly.** It is the **number of
individuals in Gen0**, i.e. the population size. It is **not** "take 9,918 group_0 entries and blend in
~15 % of some other genes". `[CODE AUDIT]` `space.py:57` builds each individual as

```python
ind = Individual({k: rng.choice(s, p=p.get(k, None)) for k, s in sizes.items()})
```

— i.e. **every individual independently draws a value for all 30 genes**, producing a *complete* kernel
config. So Gen0 is a table of 11,405 complete configs:

| | group_0 | DepthU | 1LDSBuffer | PrefetchGlobalRead | … (30 columns) |
|---|---|---|---|---|---|
| individual 1 | shape #4172 | 64 | 0 | 2 | … |
| individual 2 | shape #883 | 128 | 1 | 1 | … |
| … | … | … | … | … | … |
| individual 11,405 | shape #4172 | 32 | 0 | 2 | … |

- **rows = 11,405** ← this is what the ×1.15 sets;
- **every row is a full config**, not a group_0-only pick;
- the `group_0` *column* takes 11,405 draws from 9,918 options ⇒ **~1.15 draws per option on average** —
  that is the real meaning of the 1.15 (and why the coverage arithmetic below applies).

**But it does not deliver coverage — worth stating honestly:**

| quantity | value |
|---|---|
| inflated Gen0 `int(9,918 × 1.15)` | **11,405** |
| average draws per group_0 candidate | 1.150 |
| fraction of candidates drawn ≥1× (uniform sampling) | **≈ 68.3 %** (`1 − e^{−1.15}`) |
| draws needed for near-full coverage (coupon collector, `n·ln n`) | **≈ 91,266** |

So `1.15` buys "about one draw per candidate on average", **not** "see every shape" — ~32 % of the pool
still goes unsampled even at native Gen0, and because group_0 is GEKO-*weighted* (not uniform) the actual
coverage is skewed further toward high-weight shapes. The inflation is also **transient**: the decay
halves the excess each generation back toward 512 (§3.2), so it only shapes the first few generations.

*Source: `[CODE AUDIT]` `core/space.py:71`, `algorithm/ga.py:112/114/118`;
`protocol/v1/inputs/s10-generated.yaml`; s10 entry-gate report (expanded group cardinalities).*

### §3.2b Population decay — 512 is not the floor; 256 is

The `×1.15` inflation of §3.2a is not permanent: Ductile decays the population back down after each
generation. There are **two different decay laws**, and which one is active changes the floor.

```python
# ga.py:116 — installed ONLY when max_sp_sz > pop_size (the inflation case)
self.decay = lambda sz: int(self._pop_size + (sz - self._pop_size) / 2)          # -> floor 512

# ga.py:291 — OVERWRITES the above as soon as any generation reports diversity < div_thr (0.5)
self.decay = lambda sz: int(self._pop_size / 2 + (sz - self._pop_size / 2) / 1.25)  # -> floor 256

# ga.py:293 — applied at the end of every generation
self.pop_size = self.decay(self.pop_size) if hasattr(self, "decay") else self.pop_size
```

Three consequences that matter for reading our numbers:

- **It is not "halve the population each generation."** Law 1 halves only the *excess above* `_pop_size`,
  so the size converges geometrically onto 512:
  `11,405 → 5,958 → 3,235 → 1,873 → 1,192 → 852 → 682 → 597 → 554 → 533 → 522 → 517 → 514 → 513 → 512`.
  It reaches the floor after ~14 generations — i.e. under the native settings roughly **half of the
  30-generation horizon is spent unwinding the inflated Gen0**.
- **Law 2 targets 256, not 512, and it is sticky.** Once diversity drops below `div_thr=0.5` the `decay`
  attribute is overwritten permanently; there is no path back to law 1.
- **In our P0-capped runs law 1 is never installed at all.** With `DUCTILE_FORCE_P0=1`,
  `max_sp_sz > pop_size` is skipped, so `hasattr(self, "decay")` is False and the population would stay
  fixed at 512 forever — *unless* diversity falls below 0.5, which installs law 2.

**What actually happened (measured).** Diversity crosses 0.5 at generation 6 in every S14 large run, in
both arms, so law 2 does engage and the population decays toward 256:

| gen | 1 | 5 | **6** | 10 | 15 | 21 |
|---|---:|---:|---:|---:|---:|---:|
| diversity (baseline, seed 24001) | 0.568 | 0.515 | **0.492** | 0.417 | 0.345 | 0.322 |
| diversity (guided, seed 24001) | 0.560 | 0.508 | **0.491** | 0.412 | 0.329 | 0.316 |
| evals in that generation | 489 | 507 | 507 | 349 | 277 | 252 |

The observed per-generation eval counts after gen 6 (457, 418, 384, 349, …, 252) track the law-2
sequence `256 + (sz−256)/1.25` = 460, 419, 386, 360, … to within the valid-candidate rate.

*Source: `ga.py:116, 291, 293`; `stage3_{baseline,guided}/seed_24001/large/*optimization.log`.*

Two notes for the analysis:

- The decay engages at the **same generation in both arms**, with near-identical diversity trajectories,
  so it is a **shared property of the protocol and not an arm-level confounder** — it affects the
  absolute eval budget, not the paired G-vs-F contrast.
- Because the number of evaluations per generation is not constant, **AUC must be integrated against a
  common cumulative-evaluation budget, not against generation index** — which is how §7.1/§7.2 compute
  it (`min` of the two arms' final `cumulative_complete_evals`).

### §3.3 Native-11,405 addendum (large + medium)

Runs G/F at native Gen0 with everything else identical to the 512 version. Originally pre-registered as
**large-only** (2026-08-11); extended to **large + medium** on 2026-08-12 by
`NATIVE-P0-ROBUSTNESS-20260811(b)`.

It answers three questions:

- **(Q1) Robustness.** Is the capped-512 finding robust to Gen0 scale (removes the "you capped it"
  caveat)?
- **(Q2) Dilution.** Does the guidance effect shrink at native scale (hypothesis: the prior matters most
  at small Gen0)?
- **(Q3) Extreme-value mechanism** *(added by `(b)`)*. §7.2.1 found that guidance improves the Gen0
  **centre** but degrades the Gen0 **extreme**, because GA selection reads a maximum and maxima are
  driven by spread rather than centre. Gen0 pool size is the direct handle on how far into the tail that
  maximum reaches, and 512 → 11,405 is a **22× manipulation** of exactly that variable.

Why medium was added, against §12.2's original exclusion (both original premises were falsified by the
capped remeasure data, which did not exist on 2026-08-11):

- **Cost.** Measured GPU evaluation time, seed 24001: medium **0.17 h** vs large **5.61 h** — ~33×
  cheaper. All 5 seeds × 2 arms of native medium cost far less than a single native large seed-arm.
- ~~**Information content — the original judgement was backwards.** medium is the *only* shape whose arms
  differ measurably (per-seed F/G 0.36×–2.12× against η_medium = 0.42 %, §7.1); large's five seeds all
  sit inside η_large = 12.28 % (§7.2). Q2 asks how the effect size changes with Gen0 scale, so it needs a
  shape where an effect size is measurable at all.~~
  **RETRACTED 2026-08-13.** This was the stated reason for adding medium to the native addendum and its
  premise is **void**: the 0.36×–2.12× spread is the measurement defect (§7.1a/§7.1b), not an arm
  difference, so medium is not "the shape where an effect size is measurable" — it is the shape where the
  instrument failed. §7.1a already recorded that this rationale must be corrected; this is that
  correction, applied late (found by audit 2026-08-13, having survived the earlier retraction pass).
  **What justifies medium's inclusion instead:** Q3, the Gen0 extreme-mechanism question, which reads
  from the GA trajectory and **does not depend on champion remeasurement at all**. The Q2 effect-size
  comparison on medium's final endpoint is `NOT_EVALUATED` (design §13.6).
- **Q3 needs pool size, not a rich treatment**, so it is testable on medium; running both shapes also
  yields a cross-shape gradient (large has 5 activated genes, medium 2).

Verified precondition: the medium and large configs are byte-identical apart from the four
`ProblemSizes` numbers and both embed the same 9,918 `MatrixInstruction` entries, so medium's
`max_sp_sz` is also 9,918 and its native Gen0 inflates to the same 11,405 — it does not fall into the
`max_sp_sz < pop_size/5` halving branch at `ga.py:119`.

Pre-registered directional predictions for Q3 (written before execution, falsifiable): the guided Gen0
**extreme** disadvantage should **widen** at 11,405; the guided Gen0 **centre** advantage should hold or
widen; and the widening should be **larger on large than on medium**. A contrary result must be recorded
as refutation of the mechanism.

Scheduling: **medium first, large second** — medium returns Q2/Q3 readings within hours and validates
the plumbing (inflation + decay + weights active) before committing 3–4 days to large.

Honest caveat: medium was added *after* its capped result was seen, so its inclusion is not blind; what
remains genuinely pre-registered is the native-P0 outcome itself.

*Source: S14 §12 (§12.1 Q3, §12.2, §12.3, §12.4.4, §12.6).*

### §3.4 Entropy-cap ρ — what it is and why it exists

**The objects involved.** For one gene *g* the Gen0 sampler needs a probability over that gene's
candidate values:

- **`p0`** = the **baseline** distribution — uniform over the gene's candidates (this is what Arm G
  uses, i.e. "no guidance").
- **`q`** = the **Formocast preference** — a softmax over the *trusted* values,
  `q ∝ exp(λ·(m_gv − min_v m_gv))` (sealed `construct_gene_probabilities`). `λ` controls how peaked the
  preference is (λ=0 → flat over trusted values; larger λ → more concentrated on the best value). Here
  `λ_s = 8` for medium and large.
- **`p1`** = what Arm F actually samples from — a **mixture** of the two.
- **`H_norm`** = *normalized entropy* of `p1`: its Shannon entropy divided by the maximum possible
  (`log n`). `H_norm = 1.0` means perfectly uniform (maximum diversity); smaller means more concentrated.

**The problem the floor solves.** Concentrating Gen0 on the model's favourite values risks destroying
the exploration diversity a GA needs. The sealed protocol therefore requires **`H_norm(p1) ≥ 0.80`** —
"the guided Gen0 must remain at least 80 % as diverse as uniform".

**Why the ORIGINAL (binary) form failed.** The old gate asked a yes/no question: *at full strength
(`p1 = 0.2·p0 + 0.8·q`), does this gene clear 0.80?* If not, the gene was **excluded entirely**
(fell back to p0). That rule perversely **deleted exactly the strongest-signal genes** — the more
informative the gene, the more concentrated its `q`, the more likely it was to fail the floor.
Worse (see §7.3), for a low-cardinality gene the ceiling on `H_norm` is a function of arity alone, so
some genes could **never** clear 0.80 at any λ. **A step-by-step, plain-language derivation of this
whole failure — what a "trusted value" is, why the ceiling is 0.6576, why one gene stops the entire
pipeline, what `ρ` adjusts, and why the floor was not simply removed — is in §3.4a.**

**The fix (`ENTROPY-CAP-20260810`) — cap the strength instead of dropping the gene.** Introduce a
per-gene mixture strength `ρ`:

```
p1_g = (1 − ρ_g)·p0  +  ρ_g·q_g(λ_s)
ρ_g  = max{ ρ ∈ [0, 0.80] : H_norm(p1_g) ≥ 0.80 }
```

- `ρ = 0` → `p1 = p0` (no guidance at all); `ρ = 0.80` → `p1 = 0.2·p0 + 0.8·q` (**identical to the old
  full-strength mix**, so previously-passing genes are unchanged).
- Because `H_norm` is **monotone-decreasing in ρ**, the feasible set is an interval `[0, ρ*]`, and `ρ_g`
  is found by a **deterministic downward grid scan** (step `0.80/4096 = 0.0001953125`, 4097 points) —
  reproducible, no solver.
- It is a **universal rule applied to every gene** passing gates (a)/(b)/(c) — not a special case for
  the two genes it rescues, hence not gate-shopping. Genes failing (a)/(b)/(c) still fall back to `p0`.

**Worked contrast on medium** (both activated, from the sealed derivation manifest):

| gene | n_trusted | S_g | H_norm at full strength | ρ_g | resulting H_norm(p1) | old binary gate |
|---|---|---|---|---|---|---|
| **1LDSBuffer** | 2 | 0.113 | 1.0000 (already fine) | **0.80** (full) | 0.9159 | PASS (unchanged) |
| **DepthU** | 2 | 0.142 | **0.6576** (below floor) | **0.566** (reduced) | **0.8001** (just clears) | **FAIL → was excluded** |

DepthU — medium's *strongest* gene — was being thrown away by the binary rule; the cap keeps it at
~71 % of full guidance strength (ρ 0.566 vs 0.80) while landing exactly on the diversity floor. Its
distance from baseline is then TV(p1,p0)=0.377, KL=0.358.

*Source: S14 §10.3, qa-09 §4.3a; `derivation-manifest-capped.json` (locked_constants, locked_formulas,
gate_definition.entropy_cap_amendment_ENTROPY_CAP_20260810, per_shape_activation_log).*

### §3.4a Plain-language walkthrough — why the sealed max-reducer pipeline produces nothing

*(Written because §3.4 and §7.3 are correct but dense. This subsection re-derives the same result from
first principles with no new claims; every number is cited to a sealed artifact.)*

#### §3.4a.1 What S11 was building: a loaded die per gene

Each tunable gene has a list of candidate values. S11's job was to look at Formocast's predicted
latencies and turn "which values look good" into a **loaded die** — a probability distribution used when
drawing that gene's value for each Gen0 individual. Arm G rolls a fair die (`p0`, uniform); Arm F rolls
the loaded one (`p1`).

#### §3.4a.2 What the sampling actually sampled, and what a "trusted value" is

**Which stage.** This is S11's **conditional sampling** stage — before any analysis, and with no GPU
involved. For each (gene, candidate value) pair the protocol opens one **stream** that **pins that gene
to that value** and then draws otherwise-random complete 30-gene configs. Each drawn config must
*qualify*: it has to be built by KernelWriter and be scoreable by Formocast. Qualifying configs are
"accepted"; the stream stops once **256** are credited, or when it exhausts its hard cap of **512 chunks
× 512 nominal slots = 262,144 draws**.

**What the result means.** A stream's accept count answers: *"if I fix this gene to this value and draw
the other 29 genes at random, how often do I get a config that actually builds and can be scored?"* It is
the empirical evidence base for that value's marginal — with no accepted configs there is nothing to
average, so no marginal can be computed.

**Every value received an identical budget.** `[CODE AUDIT]` `s11-conditional-prefixes.json` records
`hard_cap_chunks = 512`, `nominal_slots_per_chunk = 512`, `complete_nominal_draws = 262144`,
`ledger_replay.event_count = 512`, `cap_complete = true` for **every** stream. *(Key corrected 2026-08-13: an earlier draft cited `chunks_observed`, which does not exist in that file; the recorded equivalents are `ledger_replay.event_count` and `ledger_replay.per_stream_next_chunk.<stream>`, both 512.)* The schedule was not unfair — the
outcomes were:

> **⚠ SOURCE GAP, found by audit 2026-08-13.** The **credited** column is verified exactly against
> `s11-conditional-prefixes.json → streams[].credited_rows` (DepthU 256/256/38/0/0/0; PGR 256/256/2/0).
> The **"accepts observed"** column is **not**: that field is capped at 256 in the cited artifact and
> cannot yield 3,513 or 723, and those two values could not be located in `s11-registry.json`, the
> manifests, or `parallel-analyze/out/*` — they appear only inside `.pkl` payloads. So the uncapped
> accept counts are **`NOT_EVALUATED` as cited**: the numbers may well be right, but no cited artifact
> records them. Note the `PrefetchGlobalRead` table below honestly writes "≥256 (target hit)" for the
> same quantity — the two tables should be made consistent, either by citing the payload or by
> down-stating both to "≥256". **The monotone-decline argument that rests on this column
> (3,513 → 723 → 38 → 0 → 0 → 0) inherits the gap**; its last four values are verified, its first two
> are not.

| `DepthU` value | accepts observed in 262,144 draws | credited | trusted (support ≥ 128)? |
|---:|---:|---:|---|
| **32** | **3,513** ⚠ unsourced | 256 (target hit, capped) | ✓ |
| **64** | **723** ⚠ unsourced | 256 (target hit, capped) | ✓ |
| **128** | **38** | 38 | ✗ |
| **256** | **0** | 0 | ✗ |
| **512** | **0** | 0 | ✗ |
| **1024** | **0** | 0 | ✗ |

| `PrefetchGlobalRead` value | accepts observed | credited | trusted? |
|---:|---:|---:|---|
| **1** | ≥256 (target hit) | 256 | ✓ |
| **2** | ≥256 (target hit) | 256 | ✓ |
| **3** | **2** | 2 | ✗ |
| **4** | **0** | 0 | ✗ |

**The zeros are not "unsampled" — they are "sampled 262,144 times and nothing survived".** That is a very
different fact, and it is the one that matters.

**And the pattern is monotone, not random.** For both genes the accept count falls monotonically as the
value grows: `DepthU` 3,513 → 723 → 38 → 0 → 0 → 0; `PrefetchGlobalRead` 256+ → 256+ → 2 → 0. That is the
signature of a **joint-feasibility** constraint, not of sampling luck. Both genes buy performance by
consuming on-chip resources — `DepthU` is the unroll depth (how much of K each main-loop iteration
consumes, which sizes the LDS tile), and `PrefetchGlobalRead` is how many global loads are kept in flight
(which costs registers and buffers). The deeper the setting, the more MacroTile / MatrixInstruction
partners exceed a hardware limit and fail to build. At `DepthU ≥ 256`, essentially **no** partner in the
whole space survives.

*(That resource-pressure account is a mechanistic interpretation consistent with the monotone pattern;
the sealed artifacts record the counts, not the rejection reasons, so it is not proven here.)*
**Terminology caveat (added after review).** The sealed ledger
`s11-conditional-prefixes.json` records only rows with `disposition: "accepted"`, so "zero credited"
strictly means *no config with that value was accepted under the S11 conditional-prefix acceptance
ledger* — it does **not** by itself establish that the rejection was a KernelWriter build failure. Two
things keep this honest: the counts fall monotonically with the value (3,513 → 723 → 38 → 0 → 0 → 0),
which is what a joint-feasibility constraint looks like; but §7.2.1's measured Gen0 validity rates on
large are 480–489 (G) vs 480–491 (F), statistically indistinguishable, which sits awkwardly with the
guided arm placing ~10–21 % of one gene's mass on values that cannot execute at all. (Partial
resolution: §7.2.1 is *large*, where the capped gene is `PrefetchGlobalRead`, not `DepthU`.) The report
should say "no accepted config", not "unbuildable", unless the rejection reasons are separately
established.

**What "trusted" then means.** A value earns a place in the loaded die only if it clears
`support ≥ 128` accepted configs, plus executable / coverage ≥ 0.95 / no collision (§5a). So
`DepthU` keeps **2 of 6** and `PrefetchGlobalRead` keeps **2 of 4** — the rest have no usable evidence.
`1LDSBuffer` (2 values, 256 / 256) keeps both, which is why it alone passes at full strength (§3.4).

This is what "a six-sided die with only two faces backed by evidence" means, literally. And it sharpens
the problem in §3.4a.3: the diversity floor will shortly demand that this die look *spread out across all
six faces* — including three faces that correspond to configurations which, empirically, **cannot be
built at all**.

#### §3.4a.3 The diversity floor, and why those genes can never clear it

The sealed rule is `H_norm(p1) ≥ 0.80` — the guided die must stay at least 80 % as spread out as a fair
die (§3.4). Now compute what `DepthU` can actually reach. The sealed path fixes the mixture at full
strength (`p1 = 0.2·p0 + 0.8·q`) and lets only `λ` vary. The most diffuse case is `λ = 0`, where `q` is
flat across the two trusted values:

```
p0 = 1/6 on each of 6 values
q  = 1/2 on each of the 2 trusted values, 0 on the 4 untrusted

p1 = 0.2·p0 + 0.8·q
   = 0.0333  on each of the 4 untrusted values   (baseline mass only)
   = 0.4333  on each of the 2 trusted values     (baseline + guided mass)

H_norm = H(p1) / ln 6 = 0.6576
```

**0.6576 < 0.80.** And this is the *most diffuse* setting available — every other `λ` concentrates
further. The sealed diagnostic confirms it independently: `max_entropy_over_grid = 0.6575889744675268`
at `argmax_lambda = 0.00`, `passes_floor_at_any_lambda = false`
(`parallel-analyze/out/diag-lambda2.w72.json`). `PrefetchGlobalRead` (4 values, 2 trusted) tops out at
`0.7345`, likewise below the floor at every `λ`.

So these two genes fail the floor **not because the evidence is weak** — their sensitivity margins are
the widest of any gene (§7.3.1 item 3: +88 % and +7.4 % over the `S_g` floor, every stochastic gate
clearing by 1.79×–11.86×) — but because **they do not have enough sampled values for any admissible die
to look spread out**.

#### §3.4a.4 Why one gene failing kills the whole pipeline

This is the step that turns a per-gene problem into a total stop: **`λ` is global**. One single `λ` is
chosen for *all* guided genes at once, and the sealed rule requires every guided gene to clear the floor
at that shared `λ`.

Analogy: a committee with a single shared "aggressiveness" dial, where every member must stay under the
same safety line. Two members are over the line **even with the dial at zero**. There is therefore no
dial setting that satisfies everyone — the feasible set is empty.

The function whose job is to pick that dial setting is `select_global_lambda`
(sealed `s11/guidance.py:95`). It finds the feasible set empty and asserts. `[CODE AUDIT]` the
diagnostic records `status = "ASSERTION at call #1"` — it fails on the very first call.

The rest follows mechanically:

```
analyze  --asserts-->  s11-analysis.json never written
                        └-> decide     cannot run (its input does not exist)
                             └-> reproduce cannot run
```

Hence the three closeout artifacts are **NOT_PRODUCIBLE, not pending** (§7 table, §7.3). This is also why
the serial `analyze` was stopped after 14 h 31 m on 2026-08-12: it was re-deriving, at roughly 330× the
cost, an outcome the verified parallel reproduction had already established in 156.7 s — and it would
have hit the identical assertion no matter how long it ran.

#### §3.4a.5 "Why not just ignore the entropy floor for the max-reducer run?"

A natural question, with three separate answers — the first is decisive on its own.

**(1) Governance: the floor is a sealed constant.** The value 0.80 lives inside the sealed S11 pipeline.
Editing it is editing sealed code, which the study forbids. More importantly it would defeat the purpose
of that run: the sealed path exists precisely to be the **as-registered** artifact. A patched pipeline is
no longer S11-as-sealed — it is a new, unregistered variant, and its output could not be labelled "the
S11 closeout" under any honest reading. Per governance the assertion was therefore **reported, not
patched**, and the sealed tree was left untouched (§7.3).

**(2) Science: removing the floor is not free.** The floor is not bureaucratic overhead — it protects
Gen0 exploration diversity. (Note the floor's demand is also, in this instance, *unsatisfiable in
principle*: §3.4a.2 shows three of `DepthU`'s six values produced zero accepted configs in 262,144
draws each, so asking the die to spread mass across all six is asking it to bet on kernels that do not
exist. Removing the floor is still the wrong repair, but it is worth recording that the floor was
demanding something the hardware cannot supply.) Deleting it would let `DepthU`'s prior concentrate 80 % of its mass on 2 of 6
values with nothing holding it back. §7.2.1 shows that risk is **real and measured**: on large, even the
*capped* prior improved the Gen0 centre (4/5 seeds) while degrading the Gen0 extreme (1/5 seeds), and it
is the extreme that GA selection actually reads. "Just ignore entropy" is not a null change; it is a
different experiment, in the direction the data already flags as harmful.

**(3) It was unnecessary — the answer was obtained without patching anything.** The per-shape derivation
(`ENTROPY-CAP-20260810`) reaches guidance for both genes while *keeping* the 0.80 floor, by changing what
is adjusted rather than what is required. So there was never a need to choose between "respect the
sealed floor" and "guide the strong genes".

The transferable lesson (§7.3.1 item 4) is not "the floor is wrong" but "**a constant floor conflates
two different things**": *preserve diversity* and *have enough sampled candidate values*. The principled
repairs are to make the floor **relative to each gene's attainable maximum**, or to **cap the strength
instead of excluding the gene**.

#### §3.4a.6 What `ρ` actually adjusts

`ρ` is the **mixing weight between the fair die and the loaded die** — nothing else. It does not change
the data, the sensitivity, which values are trusted, or the 0.80 floor.

```
p1 = (1 − ρ)·p0  +  ρ·q          p0 = fair die (uniform)
                                  q  = Formocast's preference over trusted values
ρ = 0     ->  p1 = p0            no guidance at all (identical to Arm G)
ρ = 0.80  ->  p1 = 0.2·p0 + 0.8·q   the sealed full strength (what the old binary rule tested)
```

The two rules differ only in **what is allowed to vary**:

| | sealed / binary rule | `ENTROPY-CAP-20260810` |
|---|---|---|
| mixing weight | **fixed at 0.80** | **searchable, `ρ ∈ [0, 0.80]`** |
| `λ` (peakedness of `q`) | searchable, but **shared globally** | fixed at `λ_s = 8`, **per shape** |
| gene below the floor | **excluded entirely** (falls back to `p0`) | **kept, at reduced strength** |
| one gene infeasible | **whole pipeline asserts** | only that gene's `ρ` is smaller |

Because `p0` is uniform (`H_norm = 1.0`) and `H_norm(p1)` is **monotone-decreasing in `ρ`**, dialling `ρ`
down always moves `p1` back toward maximum diversity. So a feasible `ρ` always exists — at worst `ρ = 0`.
The rule takes the **largest** `ρ` that still clears the floor, found by a deterministic downward grid
scan (step `0.80/4096`, 4097 points — reproducible, no solver).

**Measured result — the same two genes that made the sealed path impossible are guided in S14 right now**
(`derivation-manifest-capped.json` → `per_shape_activation_log`):

| gene / shape | `H_norm` at sealed full strength | sealed verdict | `ρ_g` | resulting `H_norm(p1)` | per-shape verdict |
|---|---:|---|---:|---:|---|
| `DepthU` / medium | **0.6576** | excluded | **0.566** | **0.8001** | **activated** |
| `PrefetchGlobalRead` / large | **0.7345** | excluded | **0.586** | **0.8001** | **activated** |

Note the `H_norm` column: `0.6575889744675268` and `0.7344977967946407` are **identical to the seventh
decimal** to the values in the sealed diagnostic. Two independent code paths landing on the same numbers
is the strongest available confirmation that the structural account above is the actual mechanism, not a
plausible story.

Both land at `0.8001` — just above the floor — because the rule maximizes `ρ` subject to clearing it.
Same gene, same data, same 0.80 floor: the sealed rule throws the gene away, the amended rule guides it
at ~57–59 % strength.

#### §3.4a.7 Why the shared-`λ` deadlock does not exist per-shape

Two independent reasons, and either alone is sufficient:

- **Per-gene strength.** Each gene gets its own `ρ_g`. `DepthU` no longer has to be satisfiable
  simultaneously with everything else — it turns its own dial down until it clears, and no other gene is
  affected.
- **No global feasibility requirement.** `λ_s` is fixed per shape rather than searched for a value that
  must work for all genes at once, so there is no shared feasible set that can be empty.

The blocking condition in §3.4a.4 was never about the data. It was a **coupling** created by requiring
one shared parameter to satisfy every gene simultaneously. Removing that coupling removes the deadlock,
without weakening the diversity guarantee — `H_norm(p1) ≥ 0.80` still holds for every activated gene.

#### §3.4a.8 The irony worth stating in the report

The genes the sealed rule discards are, systematically, **the ones carrying the most signal**. The causal
chain is short and runs in one direction:

```
stronger model signal  ->  more peaked preference q  ->  lower entropy  ->  more likely to fail a fixed floor
```

`DepthU` is medium's top gene (`S_g = 0.142`); `PrefetchGlobalRead` is large's (`S_g = 0.192`). Both were
excluded. So the binary floor's practical effect is not "filter out noise" but **"systematically discard
the most informative genes"** — and, because `λ` is shared, a single such gene is enough to stop the
entire pipeline.

There is a second, compounding defect visible in the same data. The floor is computed over a gene's
**full arity** (`H_norm = H(p1)/ln n`, `n = 6` for `DepthU`) while guided mass can only ever sit on its
**trusted** values (`k = 2`). §3.4a.2 shows the untrusted values are untrusted because they produced
**zero accepted configs in 262,144 draws each** (a fourth, `DepthU=128`, drew only 38) — they are not
merely lightly observed, they appear to be jointly infeasible. So the denominator `ln n` prices in
candidate values the sampler could not realise,
and the floor is effectively penalising a gene for failing to spread probability over kernels that
it could not obtain evidence for. A floor expressed relative to each gene's *attainable* maximum (§7.3.1 item 4, repair
(i)) removes this second defect as well as the first.

This is a design finding about the protocol, not a failure of the experiment, and it is reproduced
independently on two different reducers (§7.3.1 item 5).

*Source: `[CODE AUDIT]` `s11-conditional-prefixes.json` `streams[].credited_rows` (per-value support);
`parallel-analyze/out/diag-lambda2.w72.json` (`max_entropy_over_grid`, `argmax_lambda`,
`passes_floor_at_any_lambda`, `structural_sup_over_all_baselines_and_lambda`, `status`);
sealed `s11/guidance.py:95` (`select_global_lambda`); `derivation-manifest-capped.json`
`per_shape_activation_log` (`rho`, `entropy_at_lambda0`, `normalized_entropy_p1`); §3.4, §5a, §7.2.1, §7.3.*

#### §3.4a.9 What the 0.80 line actually measures — and why it is not "concentration"

The floor is described as "keep the guided Gen0 at least 80 % as diverse as uniform". The data show it
does not measure that. Three genes, **all given the same guidance strength** (the sealed full-strength
mix `0.2·p0 + 0.8·q`), get completely different verdicts:

| gene | candidates `n` | trusted `k` | attainable `H_norm` | vs the 0.80 line |
|---|---:|---:|---:|---|
| `1LDSBuffer` | 2 | 2 | **1.0000** | clears trivially |
| `PrefetchGlobalRead` | 4 | 2 | **0.7345** | **unreachable at any λ** |
| `DepthU` | 6 | 2 | **0.6576** | **unreachable at any λ** |

Same treatment strength, opposite outcomes. The difference is entirely `k/n`. So the gate is not
rejecting "priors that concentrate too much" — it is rejecting **genes that have many candidate values
but only two with enough sampled evidence**. That is a property of the sampling outcome, not of the
guidance being applied.

The sealed diagnostic distinguishes two flavours of failure, which is itself evidence the line is not a
clean criterion:

- `DepthU` — `structurally_impossible: true`. Its supremum over **all** strictly-positive baselines and
  all λ is `0.7435`, still under 0.80. No baseline choice could rescue it.
- `PrefetchGlobalRead` — `structurally_impossible: false`. Its supremum over all baselines is `0.8610`,
  **above** 0.80. It is unreachable *only* under the sealed uniform baseline.

Two genes fail the same line for materially different reasons; one is arithmetic, the other is a
consequence of a specific modelling choice.

Combined with §3.4a.2, the demand is stricter than it looks. `DepthU`'s denominator is `ln 6`, but three
of those six values produced **zero accepted configs in 262,144 draws each**. So the line asks the die
to spread probability across candidate values the sampler could never realise, and then penalises the gene
for not doing so. Both repairs in §7.3.1 item 4 — express the floor **relative to each gene's attainable
maximum**, or **cap strength instead of excluding** — remove this, because both stop treating `ln n` as
the reference when only `k` of the `n` values are reachable.

### §3.4b How S11's scores become the weights Ductile actually samples from

*(The end-to-end treatment path. This is the "how does the treatment physically enter the GA" chain the
report must state; each step is a locked formula in `derivation-manifest-capped.json` →
`locked_formulas` / `locked_constants`, and the final step is verified below against the shipped file.)*

#### §3.4b.1 The five steps

```
s11-native-scores.json                     30,490 Formocast predicted latencies
      │  (1) per-size benefit
      ▼   b_{c,s} = 1 − midECDF_s(predicted_latency)          rank, not absolute latency
      │  (2) shrinkage marginal per (gene, value)
      ▼   m_{g,s,v} = (Σb + α·global_mean_s)/(n + α),  α = 32
      │  (3) softmax over TRUSTED values only
      ▼   q = normalize( exp( λ_s·(m − min m) ) ),  λ_s = 8
      │  (4) entropy-capped mixture                            [ENTROPY-CAP-20260810]
      ▼   p1 = (1 − ρ_g)·p0 + ρ_g·q,   ρ_g = max{ρ ≤ 0.80 : H_norm(p1) ≥ 0.80}
      │  (5) INVERT Ductile's weight transform
      ▼
ga-weights-{shape}.json                    what Arm F injects into the GA config
```

Steps (1)–(3) are sealed S11 code; (4) is the amendment; **(5) is the step most likely to be got wrong,
and it is the one the report must not skip.**

#### §3.4b.2 Step 5 — Ductile's `weights` are NOT probabilities, and the transform is inverted

`[CODE AUDIT]` `ga.py:145–146`:

```python
w = np.exp(-weight_beta * (w - w.min()))     # weight_beta = 0.25
self.probs[k] = w / w.sum()
```

Two consequences:

- **The sign is negative.** A *lower* weight yields a *higher* sampling probability. The field carries
  cost-like semantics, not preference-like. Emitting `p1` directly into that field would invert the
  guidance — the model's best value would become the least likely draw.
- **Therefore the derivation must invert the transform**, emitting weights `w` such that Ductile's own
  `exp(−0.25·(w − min w))`, renormalised, reproduces the intended `p1`. Up to the additive constant that
  `− w.min()` cancels, that is `w ∝ −4·ln(p1)`.

The sealed derivation records this round-trip explicitly per gene — `roundtrip_p0_pass`,
`roundtrip_p1_pass`, `roundtrip_p0_max_abs_error`, `roundtrip_p1_max_abs_error` in
`per_shape_activation_log`.

#### §3.4b.3 Verified end-to-end on the shipped file

`[CODE AUDIT]` Taking `out-capped/ga-weights-medium.json` as it stands and replaying Ductile's own
transform:

| gene | weights in the file | ⇒ Ductile sampling probs |
|---|---|---|
| `DepthU` (6 values) | `[6.251, 2.764, 10.506, 10.506, 10.506, 10.506]` | `[0.2096, 0.5011, 0.0723, 0.0723, 0.0723, 0.0723]` |
| `1LDSBuffer` (2) | `[1.608, 4.423]` | `[0.6690, 0.3310]` |
| `WaveSeparateGlobalReadA` (2, **not activated**) | `[2.773, 2.773]` | `[0.5000, 0.5000]` |

Three independent checks, all passing:

- **The untrusted mass is exactly the baseline share.** `DepthU`'s four untrusted values each get
  `0.0723`, and `(1 − ρ)·p0 = (1 − 0.566015625)/6 = 0.0723`. The mixture in step (4) is reproduced
  exactly by the shipped weights.
- **The entropy lands on the floor.** `H(p1)/ln 6 = 0.8000`, against the manifest's recorded
  `normalized_entropy_p1 = 0.800125` — the cap did what it claims, and it is visible in the artifact the
  GA actually consumes.
- **Non-activated genes come out uniform.** `WaveSeparateGlobalReadA` resolves to exactly `[0.5, 0.5]`,
  i.e. identical to Arm G. This confirms the treatment is confined to activated genes; every other free
  gene is sampled the same way in both arms.

Inverting step (5) also recovers the guided preference itself: for `DepthU`,
`q ≈ [0.243, 0.757]` over `{32, 64}` — i.e. the model prefers `DepthU=64` by about 3:1, and after the
`ρ = 0.566` cap that becomes a 0.5011 vs 0.2096 draw probability, with 28.9 % of the mass still held back
on the four evidence-less values by the diversity floor.

#### §3.4b.4 What this means for reading the experiment

- The **only** difference between Arm G and Arm F is the `weights` list in the backend config. Everything
  else — seeds, pins, `group_0`, evaluation, early stop — is identical.
- Because non-activated genes resolve to uniform, the treatment on medium is a prior over **2 of 29** free
  genes, and on large **5 of 29**. That is the concrete size of the intervention, and it is worth stating
  plainly next to any null result (§7.1/§7.2): a null is a null *for a prior of that size*.
- `group_0` weights are present in both arms' configs and are byte-identical between them — they are GEKO
  weights, not treatment (§3.7).

*Source: `[CODE AUDIT]` `algorithm/ga.py:145–146` (weight→prob transform, `weight_beta = 0.25`);
`derivation-manifest-capped.json` `locked_formulas` (`per_size_benefit`, `shrinkage_marginal`,
`softmax_q`, `p1_mix_capped`), `locked_constants` (`alpha = 32`, `lambda`, `rho_max = 0.80`,
`rho_step = 0.0001953125`, `entropy_floor = 0.80`), `per_shape_activation_log` (`rho`, roundtrip checks);
`out-capped/ga-weights-medium.json` (`weight_beta`, `weights`, `rho_per_gene`, `note`); §3.4, §3.4a, §5a.*

### §3.4c Audit of the entropy floor — where it sits, where 0.80 came from, and what it does to S14

*(Answers three questions the report will be asked: is the 0.80 justified; does the mechanism do what it
claims; and does any of this compromise the S14 result.)*

#### §3.4c.1 Where the floor sits — it is a guard, not a selector

```
select genes:   S_g ≥ 0.05  AND  ≥2 trusted values        <- the SELECTION criteria
                        │
build prior:    q = softmax over trusted values (λ_s = 8)  <- the CONTENT
                        │
safety check:   H_norm(p1) ≥ 0.80                          <- the entropy floor lives HERE
```

The floor takes no part in deciding **which** genes carry signal, nor in deciding **which value** of a
gene is better. It runs afterwards and asks one question: *is the resulting prior too narrow?* Getting it
wrong therefore cannot select the wrong genes and cannot reverse the direction of the preference — it can
only change **how strongly** an already-chosen preference is applied (per-shape path), or **whether it is
applied at all** (sealed binary path).

#### §3.4c.2 Where 0.80 came from: nowhere documented

`[CODE AUDIT]` A tree-wide search finds **no derivation, no noise model, no power analysis and no
reference** for the value 0.80. It appears as a bare requirement in the S11 design
(*"entropy `>=0.80`"*), and it is hard-pinned in the sealed code — which will not even accept a
different value:

```python
# protocol/v1/s11/guidance.py:78-83
def select_global_lambda(gene_inputs, *, entropy_min: float = 0.80):
    if not gene_inputs or entropy_min != 0.80:
        raise GuidanceError("global lambda requires guided genes and entropy floor 0.80")
```

So 0.80 belongs in the same category as the `×1.15` Gen0 inflation (§3.2a): an **undocumented magic
constant**. It is worth stating in the report alongside the `S_g ≥ 0.05` heuristic already flagged in
§5a — two of the pipeline's three thresholds are unjustified constants. (The third, `support ≥ 128`, at
least has an evidence-count meaning.)

Note the pinning also reinforces §3.4a.5 point (1): even if one wanted a different floor, changing it
means editing sealed code, because the sealed function rejects any other argument.

#### §3.4c.3 Does the mechanism do what it claims? No

It claims to bound concentration. It actually bounds `k/n`. Given the **same** guidance strength (the
sealed full-strength mix), the verdict is decided entirely by how many of the gene's values have
evidence:

| gene | `n` | trusted `k` | `k/n` | attainable `H_norm` | verdict at 0.80 |
|---|---:|---:|---:|---:|---|
| `1LDSBuffer` | 2 | 2 | 1.00 | 1.0000 | clears trivially |
| `PrefetchGlobalRead` | 4 | 2 | 0.50 | 0.7345 | unreachable at any λ |
| `DepthU` | 6 | 2 | 0.33 | 0.6576 | unreachable at any λ |

Two further observations sharpen this:

- **The two failures are not even the same kind of failure.** `DepthU` is `structurally_impossible: true`
  (supremum over *all* baselines = 0.7435 < 0.80); `PrefetchGlobalRead` is `false` (supremum 0.8610 >
  0.80, so it is blocked only by the sealed *uniform* baseline choice). One line, two different
  underlying reasons — a sign it is not a clean criterion.
- **The denominator counts values the sampler could not realise.** `DepthU`'s `ln 6` includes three values
  that produced **zero accepted configs in 262,144 draws each**, and a fourth (`DepthU=128`) that produced
  only 38 (§3.4a.2). The floor is asking the prior to spread probability over values for which the corpus
  holds little or no evidence.

#### §3.4c.4 What this does — and does NOT do — to the S14 result

**It cannot make the experiment select a wrong champion.** The floor only shapes the Gen0 *sampling
distribution*, i.e. which candidates get tried. The champion is chosen by **measured real-GPU
throughput** and then re-measured 7× interleaved (§5). A distorted prior can cost search efficiency; it
cannot promote a slower config over a faster one.

**What it does do is de-weight the treatment exactly where the model is most confident.** Measured
per-gene strengths actually shipped in Lock B:

| shape | gene | `S_g` | trusted `k` | `ρ_g` | strength vs full |
|---|---|---:|---:|---:|---:|
| large | **PrefetchGlobalRead** | **0.192** *(large's top)* | 2 | **0.586** | **73 %** |
| large | UnrollLoopSwapGlobalReadOrder | 0.165 | 2 | 0.800 | 100 % |
| medium | **DepthU** | **0.142** *(medium's top)* | 2 | **0.566** | **71 %** |
| medium | 1LDSBuffer | 0.113 | 2 | 0.800 | 100 % |
| large | GlobalReadVectorWidthB | 0.058 | 4 | 0.800 | 100 % |
| large | TransposeLDS | 0.057 | 4 | 0.800 | 100 % |
| large | GlobalReadVectorWidthA | 0.052 | 4 | 0.800 | 100 % |

**The only two genes de-weighted are the top-sensitivity gene on each shape; the five weaker genes all
run at full strength.** The mechanism is not "penalised for being strong" — it is a shared cause: low
`k/n` arises because the gene's deeper settings are jointly infeasible (§3.4a.2), and genes whose deep
settings exhaust on-chip resources are exactly the genes that move performance most. Low `k/n` and high
`S_g` have the same origin: the gene governs a resource-versus-performance trade-off.

**Consequence for claim wording.** A null on medium or large is a null *for a prior that was applied at
~71–73 % strength on the shape's strongest gene and 100 % on its weakest*. That is a real interpretation
limit and must be stated next to §7.1/§7.2:

> permissible: "the amended sparse prior, as configured, did not meet the pre-registered directional gate"
>
> NOT permissible: "the model's guidance does not help" — the strongest available guidance was applied at
> reduced strength by a constant with no documented derivation.

#### §3.4c.5 How the per-shape path complies with the same 0.80 — and what came out

The per-shape route does **not** relax the floor. It changes *what is adjustable*:

| | sealed / binary | per-shape (`ENTROPY-CAP-20260810`) |
|---|---|---|
| mixing weight | fixed at 0.80 | **searched per gene**, `ρ_g ∈ [0, 0.80]` |
| `λ` | searched, **one shared value for all genes** | fixed `λ_s = 8`, per shape |
| floor | `H_norm ≥ 0.80` | `H_norm ≥ 0.80` **(identical)** |
| gene below floor | excluded entirely | kept at reduced `ρ_g` |
| one gene infeasible | **entire pipeline asserts** | only that gene's `ρ_g` is smaller |

`ρ_g` is found by a deterministic downward grid scan (step `0.80/4096 = 0.0001953125`, 4097 points),
taking the **largest** `ρ` that still clears the floor — so every activated gene lands at or just above
`H_norm = 0.8001`, by construction.

Outcome, from the same data that stopped the sealed path dead:

- **7 genes activated** (medium 2, large 5) instead of a pipeline-wide assertion;
- **2 genes de-weighted, 5 at full strength** (table in §3.4c.4);
- the diversity guarantee is **unchanged** — every activated gene still satisfies `H_norm(p1) ≥ 0.80`;
- `DepthU` and `PrefetchGlobalRead`, the two genes that made the sealed path infeasible, are guided.

So the amendment did not trade diversity for coverage. It removed a **coupling** — the requirement that
one shared parameter satisfy every gene simultaneously — which was the actual cause of the deadlock
(§3.4a.7).

*Source: `[CODE AUDIT]` `protocol/v1/s11/guidance.py:78–83` (floor hard-pinned, other values rejected);
S11 design (bare `entropy>=0.80` requirement, no derivation); `parallel-analyze/out/diag-lambda2.w72.json`
(`max_entropy_over_grid`, `structural_sup_over_all_baselines_and_lambda`, `structurally_impossible`);
`derivation-manifest-capped.json` `per_shape_activation_log` (`sensitivity`, `rho`, `n_trusted`),
`locked_constants` (`rho_max`, `rho_step`, `rho_grid_points`, `entropy_floor`); §3.4, §3.4a, §3.4b, §5a.*

#### §3.4c.6 Giving the two undocumented constants an interpretable meaning

Neither `S_g ≥ 0.05` nor `H_norm ≥ 0.80` has a derivation (§3.4c.2, §5a). That does not make them
unreportable — each can be given a meaning, and one of them can be given an empirical defence.

**`S_g ≥ 0.05` — it lands in a natural gap in the observed data.** `S_g` is the spread, in population
rank-percentile points, between a gene's best and worst value. Sorting every testable gene's `S_g`:

| shape | largest FAILING `S_g` | smallest PASSING `S_g` | gap |
|---|---:|---:|---:|
| medium | 0.0422 | 0.1127 | **0.0705** |
| large | 0.0289 | 0.0520 | **0.0231** |

Any threshold in **(0.0422, 0.0520]** selects exactly the same genes on **both** shapes. 0.05 sits inside
that window. So while the constant is undocumented, the *result is demonstrably insensitive to it* on this
data — the observed sensitivities are bimodal (a flat cluster ≤ 0.042 and a signal cluster ≥ 0.052), not a
continuum that a threshold arbitrarily bisects. This is a **post-hoc robustness check, not the original
justification**, and must be labelled as such.

**`H_norm ≥ 0.80` — it means "keep at least `n^0.8` effective choices".** Normalised entropy is hard to
read directly, but `exp(H)` is *perplexity*: the number of options a distribution is "effectively" spread
over. Since `H_norm = H / ln n`:

> `H_norm ≥ 0.80`  ⟺  `perplexity ≥ n^0.8`  ⟺  **the guided prior must stay as diverse as being uniform
> over `n^0.8` of the gene's `n` values.**

| gene | `n` | floor requires | gene can offer at most | verdict |
|---|---:|---:|---:|---|
| `DepthU` | 6 | **4.19** effective choices | 3.25 | fails |
| `PrefetchGlobalRead` | 4 | **3.03** | 2.77 | fails |
| `1LDSBuffer` | 2 | **1.74** | 2.00 | passes |

This makes the failure immediately legible: `DepthU` has only 2 values with evidence, so it cannot
manufacture 4.19 effective choices no matter how gently the preference is applied. (The ceilings are the
measured `max_entropy_over_grid` values, not a closed-form function of `(n, k)` — untrusted values retain
baseline mass, so a simple `k/n` formula does not predict them.)

#### §3.4c.7 What "de-weighting" concretely does to Gen0

`ρ` is the fraction of the sampling distribution taken from the model's opinion; the remainder is
uniform. For `DepthU` on medium (model prefers 64 over 32 by about 3:1):

| | `ρ = 0.80` (full strength, what the binary rule tested) | `ρ = 0.566` (what actually shipped) |
|---|---:|---:|
| P(`DepthU=64`) — model's top pick | **0.6393** | **0.5011** |
| P(`DepthU=32`) | 0.2273 | 0.2096 |
| each of the 4 evidence-less values | 0.0333 | **0.0723** |
| effective choices (perplexity) | 2.93 / 6 | 4.19 / 6 |
| `H_norm` | 0.6007 | **0.8001** |

Read in individuals rather than probabilities — **in a 512-strong Gen0, ~327 individuals would carry the
model's top value at full strength, versus ~257 as shipped: about 71 fewer.** Meanwhile the probability
handed back to the four evidence-less values rises from 13.3 % to 28.9 % — of which three drew **zero**
accepted configs and one (`DepthU=128`) drew only 38, below the `support ≥ 128` bar.

So "de-weighted" is not a metaphor: it is *fewer Gen0 individuals carrying the configuration the model
rates highest, and more carrying values the sampling corpus has little or no evidence for*.

#### §3.4c.8 The two knobs — why "what is adjustable" is the whole difference

Only two quantities control how peaked the final Gen0 distribution is:

```
knob A — λ : how sharp the model's own opinion q is
             small λ -> "64 and 32 are about equal"     large λ -> "it must be 64"

knob B — ρ : how loudly that opinion is played
             small ρ -> nearly inaudible (≈ uniform)    large ρ -> almost entirely the model
```

The sealed rule and the amendment differ **only in which knob turns, and who owns it**:

| | sealed / binary | per-shape (`ENTROPY-CAP-20260810`) |
|---|---|---|
| knob A (`λ`) | turnable, but **one shared setting for every gene** | fixed at 8 |
| knob B (`ρ`) | **welded at 0.80** | **turnable, one per gene** |
| safety line | `H_norm ≥ 0.80` | `H_norm ≥ 0.80` (**identical**) |

**Why the sealed rule deadlocks.** The volume knob is welded at 80 %, so the only remedy is to blunt the
opinion — and that dial is shared by everyone. Even at `λ = 0` ("64 and 32 are equally good"), 80 % volume
still collapses `DepthU`'s six options to 3.25 effective choices, below the required 4.19. **No position on
the shared dial is admissible for it.** And because the dial is shared, one member being inadmissible means
*no* setting satisfies the group — the chair cannot pick a value, so the meeting is cancelled
(`select_global_lambda` asserts, §3.4a.4).

**Why the amendment does not.** Fix the sharpness for everyone and give each gene its own volume knob.
`DepthU` turns its own down to 56.6 %, landing exactly on the line (`H_norm = 0.8001`, 4.19 effective
choices). Nobody else is touched — `1LDSBuffer` stays at 80 %.

Same data, same safety line, opposite outcomes: the sealed path **stops entirely**; the per-shape path
**activates all 7 genes** (2 at reduced volume, 5 at full). The amendment relaxed no safety requirement.
What it removed was the **coupling** — the demand that a single shared parameter satisfy every gene at
once — and that coupling, not the floor itself, was the cause of the deadlock.

*Source: `[CODE AUDIT]` `derivation-manifest-capped.json` `per_shape_activation_log` (per-gene `sensitivity`,
`rho`, `n_trusted`); `parallel-analyze/out/diag-lambda2.w72.json` (`max_entropy_over_grid`);
`out-capped/ga-weights-medium.json` (shipped weights, inverted in §3.4b.3);
`protocol/v1/s11/guidance.py:78–83`; §3.4, §3.4a, §3.4b, §5a.*

### §3.5 Sparsity finding (the model-only headline) — gene-selection funnel

Of **27 free genes** (the 30 search-space keys minus the three GEKO groups group_0/1/2; group_0 is
GEKO-weighted and outside the Formocast treatment), the number that can be guided per shape is
**tiny 0 / medium 2 / large 5**:

- medium activates {DepthU (S_g=0.142, ρ=0.566), 1LDSBuffer (S_g=0.113, ρ=0.80)};
- large activates {PrefetchGlobalRead, TransposeLDS, UnrollLoopSwapGlobalReadOrder,
  GlobalReadVectorWidthA, GlobalReadVectorWidthB};
- tiny activates none (model returns the sentinel 9,999,999.9 for 8×8 → all S_g≈0).

Attrition (why 27 → a handful), from the sealed per-gene log (`derivation-manifest-capped.json` →
`per_shape_activation_log`):

| drop reason | tiny | medium | large |
|---|---|---|---|
| sensitivity `S_g < 0.05` (dominant) | 26 | 24 | 21 |
| fewer than 2 trusted candidate values | 1 | 1 | 1 |
| **activated (survives)** | **0** | **2** | **5** |

Root cause = the sensitivity gate `S_g = max_v(m_gv) − min_v(m_gv) ≥ 0.05`: **21–26 of 27 genes are
near-flat** (S_g ~0.001–0.03, e.g. WaveSeparateGlobalReadA S_g=0.00096 on medium) — the model predicts
a gene's value barely changes predicted latency, so guiding it ≈ uniform ≈ no treatment. It is **not**
fixable by loosening the threshold (the flat genes are genuinely flat).

Secondary: exactly one gene per shape lacks ≥2 trusted candidate values (support≥128, coverage≥0.95,
executable, no collision).

Notes:

- **(i) sensitivity is shape-dependent** — the same gene can pass on one shape and fail on another
  (DepthU: medium S_g=0.142 PASS vs large 0.029 FAIL; PrefetchGlobalRead is the reverse).
- **(ii) the entropy floor is NOT a per-shape drop reason** — `ENTROPY-CAP-20260810` turned it into a
  per-gene cap ρ (so DepthU is kept at ρ=0.566), whereas the binary floor caused the total wipe-out that
  the sealed aggregate max-reducer `analyze` hits (the `select_global_lambda` assertion, §7.3).

This is a genuine **model property, not a per-shape artifact** (even the richest max reducer surfaces
only 3 genes). Per charter §8.5 the sparse/weak per-gene **marginal** signal must be **localized to a
layer** — it is marginal-loss (weak per-gene marginals); whether the underlying cause is genuine
insensitivity vs epistasis-hidden-by-marginals vs survivor-frame/rank compression is **not resolvable
from S11** (needs S12/oracle) — do NOT state "model useless".

*Source: `derivation-manifest-capped.json` per_shape_activation_log; qa-09 §4.3b; S11 report §13;
parallel-analyze/VERIFICATION.md §5.*

### §3.6 Why the guidable-gene count differs across shapes (0 / 2 / 5)

#### §3.6.1 The three locked problem sizes

All three are BFloat16, non-StreamK, single dtype/layout, on gfx942/MI300X. The 4-tuple is
**`(M, N, batch, K)`** — M×N is the output tile, K the contraction (reduction) depth.

| shape | M | N | batch | K | output elements (M·N) | FLOPs (2·M·N·K·B) | R_s (GFLOP/s ref) | η_s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **tiny** | 8 | 8 | 1 | 128 | 64 | 16,384 | 0.75 | 0.4466 |
| **medium** | 256 | 256 | 1 | 1,024 | 65,536 | 134,217,728 | 3,199.94 | 0.0042 |
| **large** | 2,304 | 1,024 | 1 | 214,336 | 2,359,296 | 1,011,364,134,912 | 180,336.00 | 0.1229 |

Relative scale: **K** grows 128 → 1,024 → 214,336 (×8, then ×209); total work grows ~8×10³ then ~7.5×10³.
The three are deliberately *divergent regimes*, not a smooth sweep: a degenerate toy, a mid-size square,
and a very deep-K production-scale GEMM.

*Source: `[CODE AUDIT]` sealed contract `s11/contract.py:674` pins
`problem_sizes == [[8,8,1,128],[256,256,1,1024],[2304,1024,1,214336]]`; per-shape R_s/η_s from Lock A.*

#### §3.6.2 Why Formocast returns the sentinel for every tiny config

This is **not** a model bug — it is an explicit *early-terminate guard*. `[CODE AUDIT]`
`formocast_simulator.cpp:578`:

```cpp
if ((M < 128 && MT0 - M >= 16) || (N < 128 && MT1 - N >= 16))
{ pp.microSeconds = 9999999.9; pp.hitRate = 0; return pp; }   // "MacroTile far larger than the problem"
```

The guard says: *if the problem dimension is small (<128) and the kernel's MacroTile overshoots it by
≥16, refuse to model this config.* Physically that is a tile computing mostly padding — e.g. a 4×512
tile on an 8×8 output evaluates 512 columns where only 8 exist (~98 % waste). Formocast declines to
estimate that regime rather than emit a meaningless number.

For **tiny (M=8, N=8)** the guard therefore requires **MT0 ≤ 23 AND MT1 ≤ 23**. Measured against the
actual candidate pool:

> **⚠ DERIVATION NOT CITED, found by audit 2026-08-13.** Two problems. (i) The guard quoted in the prose
> above (`M < 128 && MT0 − M >= 16`) is **vacuous at M = N = 256**, so it cannot produce medium's 171/434
> — that row must come from the *next* guard (`M >= 128 && MT0 − M >= 32`), which is present in the same
> block; the prose should quote the guard that actually applies to each row. (ii) `MacroTile` is **not a
> field** in `s10-generated.yaml` (which carries `MatrixInstruction`, `WorkGroup`, `GlobalSplitU`,
> `MIArchVgpr`, `UseSgprForGRO`, `LDSTrInst`), so 434 / 171 / 1 are **derived** quantities with no cited
> derivation → **`NOT_EVALUATED` as cited**. Verified in that YAML and unaffected: 9,918 entries,
> **840** distinct `MatrixInstruction` tuples, **262** `WorkGroup:` overrides. The qualitative conclusion
> — tiny's sentinel saturation ⇒ `S_g = 0.0000` for all 27 genes — is independently confirmed by the
> activation log and does **not** depend on these three counts.

| shape | MacroTiles in pool that survive the guard | share |
|---|---|---|
| **tiny (8×8)** | **1 of 434** ⚠ derivation uncited | **0.2 %** |
| medium (256×256) | 171 of 434 ⚠ derivation uncited | 39.4 % |

So ~99.8 % of the search space returns `microSeconds = 9,999,999.9` for tiny. With virtually every config
tied at the sentinel, the midECDF gives every config the same benefit ⇒ every per-value marginal is
identical ⇒ **S_g = 0.0000 for all 27 free genes**, exactly as observed. The surviving sliver shares a
single MacroTile (a `group_0` property, outside the treatment) and is far too small to give any free gene
≥2 trusted values with support ≥128.

**Interpretation:** tiny is *outside Formocast's modelled regime*, not a shape where the model tried and
failed. This is why tiny is **exploratory only** in the design — it can never carry guidance.

*Source: `[CODE AUDIT]` `formocast_simulator.cpp:568–645` (all six sentinel guards);
`protocol/v1/inputs/s10-generated.yaml` (434 distinct MacroTile shapes);
`derivation-manifest-capped.json` per_shape_activation_log (tiny: all S_g = 0.0000).*

#### §3.6.3 medium and large: the count tracks main-loop dominance

For the two shapes Formocast *does* model, the guidable-gene count tracks **how strongly the steady-state
main loop dominates runtime**, which is driven mainly by K.

**large (K=214,336 — ~209× medium's K) → 5 genes, the most.**
The main loop runs an enormous number of iterations, so the per-iteration **memory-movement pipeline
dominates total time**. Accordingly all 5 survivors are global-read / LDS / main-loop data-movement genes,
and they carry the largest sensitivities of any shape:

| gene | S_g | role |
|---|---:|---|
| PrefetchGlobalRead | 0.192 | how far ahead global loads are issued |
| UnrollLoopSwapGlobalReadOrder | 0.165 | ordering of global reads within the unrolled loop |
| GlobalReadVectorWidthB | 0.058 | width of B-operand global loads |
| TransposeLDS | 0.057 | LDS layout for the transposed operand |
| GlobalReadVectorWidthA | 0.052 | width of A-operand global loads |

**medium (K=1,024) → 2 genes.**
A moderate main loop: the fine memory-pipeline genes are still sub-threshold
(GRVWB / PGR / TransposeLDS ≈ 0.02–0.04), and the survivors are the coarse **loop-structure** genes:

| gene | S_g | role |
|---|---:|---|
| DepthU | 0.142 | unroll depth (how much K is consumed per iteration) |
| 1LDSBuffer | 0.113 | single vs double LDS buffering |

#### §3.6.4 The sharpest evidence: the dominant gene crosses over with K

| gene | medium S_g | large S_g | verdict |
|---|---:|---:|---|
| **DepthU** | **0.142 (PASS, top)** | 0.029 (FAIL) | loop-structure gene — matters at moderate K |
| **PrefetchGlobalRead** | 0.024 (FAIL) | **0.192 (PASS, top)** | memory-pipeline gene — matters at deep K |

The same two genes swap roles in opposite directions. As K grows, the dominant genes shift from
*loop structure* (DepthU, LDS buffering) to *memory-read pipeline* (prefetch, read order, vector width) —
exactly what one expects as a GEMM becomes more memory-pipeline-bound.

#### §3.6.5 Insight (report-ready)

The sparsity is **not random noise but shape-appropriate**: for each problem only a handful of genes
govern its dominant cost phase, and Formocast localizes the detectable per-gene sensitivity onto exactly
those genes.

That is a **positive validity signal** for the model — its gene differentiation tracks GEMM physics
(larger K ⇒ more memory-pipeline-bound ⇒ memory genes more sensitive), and it correctly refuses to model
a degenerate shape rather than inventing numbers. The guidance is "thin" mainly because **most genes
genuinely do not affect a given shape's dominant cost**, not because the model is broken.

*Honest limits (§8.5): this is model-space sensitivity (Formocast's own attribution, not yet
real-GPU-verified) and a per-gene marginal (epistasis-blind); the "K ⇒ memory-dominance" account is a
mechanistic interpretation consistent with the data, not a proven cause.*

*Source: `derivation-manifest-capped.json` per_shape_activation_log (per-gene S_g); S11 report §13.*

### §3.7 group_0 vs the free genes

group_0 (MatrixInstruction/WorkGroup, 9,918 joint candidates) is GEKO-weighted, **identical in both
arms, never touched** by the treatment (verified byte-identical between the two arms' weight files, §3.4b.4). The Formocast treatment only reweights the ungrouped free genes.

*Source: S14 §6.1 note.*

### §3.8 Per-shape η_s (noise margin)

The non-regression threshold uses **per-shape** noise margins `η_s = P95(|log y − median log y|)` from
the pilot residuals (medium η=0.0042, large η=0.1229, tiny η=0.4466), **not** the tiny-dominated
aggregate `delta_noise` — because η is a property of each shape's measurement repeatability.

Final non-regression threshold = `e^{−η_s}`.

*Source: S14 §10.2, baseline run-root per-shape η.*

#### §3.8.1 What a margin is, and why medium's is ~28× tighter than large's

**Why a tolerance band is needed at all.** The endpoint is a ratio `F/G`. Two *identical* arms do not
measure to exactly 1.0 — measurement jitter guarantees they will not. So a rule of the form "`F/G < 1`
means the guided arm regressed" would convert every flicker of noise into a finding. `η_s` is the
tolerance band that separates jitter from a real regression:

```
non-regression  ⟺  F ≥ G · e^{−η_s}
```

**What each pin actually permits.** This is the form a reader can reason about, and it makes the
disparity between shapes legible in a way the raw η values do not:

| shape | `η_s` | F must be ≥ this fraction of G | tolerated regression |
|---|---:|---:|---:|
| **medium** | 0.0041953 | **99.58 %** | **0.42 %** |
| large | 0.1228459 | 88.44 % | 11.56 % |
| tiny | 0.4465998 | 63.98 % | 36.02 % |

**medium is judged on a band ~27.6× narrower than large's.** That single fact is the arithmetic reason
the *same* non-regression criterion returns 5/5 on large and 3/5 on medium — before any argument about
contamination. See §7.2a for why large's 5/5 is nonetheless conditional, and §7.1b for medium's
measurement defect.

**Where medium's pin came from.** A 3-anchor × 7-fresh-client-repeat pilot whose anchors ran at
4,629 / 3,200 / 2,127 GFLOP/s — **2.9–6.3× slower than the champion the pin governs** — giving those
anchors 9.31 / 13.46 / 20.26 ms of warm-up against the champion's 3.19 ms, and **0/21 dropouts**. Full
provenance, the ruled-out confounders, and a residual the warm-up account does *not* explain: **§7.1b.4**.

**Keeping the pin is a governance decision, not a safety margin.** This distinction matters and is easy
to get backwards. Retaining a pre-registered, narrower threshold *sounds* like the cautious choice — but
a narrow band makes it **easy to declare regression and hard to declare non-regression**. That is harsh
on the treated arm, not safe. Two independent measures of how far off the pin is, both from elsewhere in
this file:

- it sits **2.8× below** the champion's own clean-mode P95 of 0.0116 (§7.1a) — tighter than the reality
  even after every dropout is excluded;
- it sits **~30× below** tiny's observed zero-treatment envelope (max |ln F/G| = **0.1247**; **sample**
  sd = **0.0715**, population sd 0.0639 — the documents quote the sample sd, and the two have been
  mistaken for a discrepancy before, so the estimator is named here).

So the reason to keep it is **"pre-registered thresholds are not revised after seeing the data"**, not
"this threshold is conservative". Any report that implies the latter is wrong.

**Why the empirical margin was rejected — shown, not asserted.** The alternative was to recompute η from
the remeasures themselves. Two objections, the second decisive:

1. **Circular.** The very repeats being gated would set the gate.
2. **Falsified by tiny's null control.** tiny's two arms are byte-identical (same sha256, all 5 seeds)
   with **0/27 genes activated** — a guaranteed zero effect. Applying tiny's own within-window
   repeatability (0.0145 → threshold `e^{−0.0145}` = 98.56 %) to tiny's own results:

   | seed | tiny `F/G` | verdict under the empirical margin |
   |---|---:|---|
   | 24001 | 0.8828 | **regressed** |
   | 24002 | 1.0350 | pass |
   | 24003 | 0.8841 | **regressed** |
   | 24004 | 0.9953 | pass |
   | 24005 | 0.9690 | **regressed** |

   A margin that scores a known, constructed zero as **3/5 regressed** is not fit to replace one that
   does not. Status of the decision: `PENDING_HUMAN_DECISION`, §9.2 D2.

**η is the wrong scale — and this limits *both* candidates.** η measures the within-window repeatability
of **one fixed config**. The estimand is a ratio of **two different champions**. Between-arm dispersion
is 4.9× the within-window value on tiny and 2.0× on large. Neither the pinned nor the empirical margin
is measuring the quantity the gate actually needs; the pin is retained on governance grounds while that
gap is disclosed rather than closed.

*Source: `[CODE AUDIT]` `noise/per_shape_noise.json → shapes.{shape}.eta_s`;
`scripts/compute_per_shape_noise.py:30`; tiny ratios from
`stage3_baseline/seed_*/tiny/champion_interleaved.json → F_over_G_median_ratio`; tolerances computed as
`e^{−η}`. S14 design §10.2, §13.4.*

### §3.9 Conditional Arm S — what it can do and why

**What it is.** Take Arm F's capped guidance and, for each activated gene, **shuffle which candidate
value receives which probability** (sealed `deterministic_nonidentity_shuffle`), keeping `ρ_g` — and
therefore `H_norm` — **exactly the same**. Arm S is thus *equally concentrated* as F but points
somewhere else.

**The question it answers.** If F beats G, there are two rival explanations, and F-vs-G alone cannot
separate them:

- **(a) Direction** — Formocast's *specific* preference (put mass on DepthU=64, PrefetchGlobalRead=2, …)
  really does point at better regions of the space.
- **(b) Concentration alone** — *any* non-uniform Gen0 helps, regardless of where the mass goes (e.g.
  concentrating changes duplicate rate, effective diversity, or how quickly selection gets multiple
  copies of a region to refine).

Arm S holds (b) fixed and destroys (a). That makes it a **matched control**: the only thing varying
between F and S is *which values* the probability sits on.

**How to read the three-arm outcome:**

| observation | conclusion |
|---|---|
| F > G **and** F > S | the **direction** matters → attribute to Formocast physics |
| F > G **but** F ≈ S | **concentration alone** explains it; the model's specific preference did not help → the `FT-ENTROPY-ONLY` failure mode |
| F ≈ S ≈ G | neither direction nor concentration produced an effect |

Without Arm S, a positive F>G can only be attributed to "the capped factorized initialization bundle vs
baseline" — i.e. the *bundle as a whole*, not the model's physics.

**Why it is kept conditional here** (not run unconditionally):

- (i) physics-direction attribution is the **registered job of the downstream S20** stage (S20-H1 is
  literally "F beats both G and S"); running it here duplicates a frozen downstream design;
- (ii) if F does not beat G there is **nothing to attribute**, so the arm buys nothing;
- (iii) 5 paired seeds are **underpowered for a 3-way contrast** (F-vs-S is a second comparison on the
  same small sample);
- (iv) the treatment is deliberately **mild** (every gene capped to `H_norm ≥ 0.80`), so the
  concentration confound it controls for is weak *a priori*.

Hence the pre-registered trigger (`CONDITIONAL-ARM-S-20260810`): derive + seal the shuffle bundle now
(Lock C, before any outcome is seen, to preserve the label firewall), but only spend GPU time on it if
F clears the directional gate on ≥1 confirmatory shape **and** budget allows.

**What Arm S cannot do.** It does not validate Formocast's absolute accuracy; it says nothing about
epistasis (the shuffle is per-gene marginal too); a null F-vs-S at 5 seeds is **not** evidence of
absence; and it only speaks to the genes/shapes actually activated.

*Source: S14 §10.2/§10.5; failure taxonomy `FT-ENTROPY-ONLY`; S20-H1.*

### §3.10 Beat-native two-sided release

The absolute "may not claim beating native `PredictionThreshold`" prohibition is lifted for S14 to
two-sided/wait-for-data: a value-vs-native claim is permissible **iff** native is actually measured and
any budget/selection confounding is disclosed; no fabrication, no pre-conclusion either way.

*Source: charter §8.6a 2026-08-10(b).*

---

## §4 Claim framework (what can / cannot be said)

- **Two-sided.** Report guided effect on early-search (gen-10, AUC) and **final tuned quality** as
  improvement / no-change / regression with per-shape effect size + interval + cross-seed direction. A
  **final-quality improvement claim IS allowed if data supports it** (`CLAIM-SCOPE-S14-20260810`).
- **Mandatory caveats:** modest power (5 seeds, not significance), scope (tested shapes, single
  development cluster, no generalization), no pre-conclusion before sealed analysis, no exaggeration.
- **Claim ladder:** model-only sparsity = headline; medium∧large both pass the per-shape gate → §8.2
  early-search + final wording; one passes → shape-specific / mixed; none pass → "amended sparse prior
  did not meet the pre-registered directional gate" (**NOT** "no effect / model useless").
  *Source: S14 §11 item 7 / §10.5.*
- **Physics-direction** only if Arm S runs and F beats **both** G and S (else attribute to "capped
  factorized initialization bundle vs baseline").
- **Still forbidden (§8.6, unchanged):** generalization to MI300X workloads, production/deployment ready,
  cross-architecture, end-to-end tuning wall-clock speedup (not measured), owner/team-should-adopt.

---

## §5 Metrics & acceptance

**Primary metric.** Champion **real-GFLOPS** with **7× interleaved G/F(/S) remeasure** on the same GPU.

Why it is required (report-ready) — it defends against three distinct problems that the in-search
fitness cannot:

- **(i) Winner's curse** — the GA selected the champion *because* it measured fastest, so a lucky-fast
  measurement is over-represented; the in-search number is systematically optimistic, and the bias need
  not be equal across arms (the arm that benchmarked more distinct candidates gets more lucky draws).
- **(ii) Temporal drift** — baseline ran hours/days before guided, so an uncontrolled comparison
  confounds *arm* with *time* (clocks, thermals, machine state); interleaving G/F in one window cancels
  it.
- **(iii) Single-shot noise** — per-shape repeatability is η_medium=0.0042 (±0.42%) but η_large=0.1229
  (±12.3%), so for large a single measurement cannot separate two close champions.

Taking the median of 7 interleaved repeats addresses all three. **Without it**, the pre-registered final
criterion (`final ratio ≥ e^{−η_s}` computed on the 7×-median) literally cannot be evaluated as
registered — that would be a protocol deviation and the final-quality claim would weaken to an
uncontrolled in-search observation. *Source: S14 §10.2/§10.4.*

**Secondary/diagnostic.** gen-10 checkpoint, search-trajectory **AUC** (integrated to the common
completed budget), `generations_run`.

**Per-shape directional-consistency gate** (pre-registered, not a significance test): for a confirmatory
shape, ≥4/5 seed-pairs positive on each of {Gen0, gen-10, AUC} and final ratio ≥ `e^{−η_s}` in ≥4/5
(median also above). **Combined §8.2 wording requires medium ∧ large** (intersection-union; no aggregate
rescue). Tiny is descriptive only. *Source: S14 §10.4.*

**Assembly-dropped candidate handling (Reading 1):** a candidate that fails KernelWriter/assembly build
is given invalid fitness = −1 and treated exactly as native Ductile treats a real benchmark-failed −1
(never beats a positive score, never champion) — **no added invalid filter**. *Source: S14 §6.1.*

### §5b Why the F-vs-G comparison uses the **log**-ratio

The raw ratio `F/G` is reported too (§7.1) because it is the intuitive number, but the **analysis
quantity is `ln(F/G)`**, for four reasons:

**(1) Symmetry — the raw ratio is not a fair scale.** "Twice as fast" is `2.0` (distance 1.0 above 1)
while "half as fast" is `0.5` (distance only 0.5 below 1). So on the raw scale, improvements look bigger
than equal-and-opposite regressions, and they do not cancel. In log space they are exactly symmetric:
`ln 2 = +0.693`, `ln 0.5 = −0.693`.

**(2) Our own data shows the bias this causes.** Across the 5 medium seeds:

| statistic | value | comment |
|---|---|---|
| arithmetic mean of raw ratios | 1.0499 (**+5.0 %**) | looks like a gain — but it is one 2.12× seed dragging the mean up |
| median of raw ratios | 0.9971 (−0.3 %) | |
| **median log-ratio** | **−0.0029** (⇒ ratio 0.9971) | the reported central tendency |
| mean log-ratio | −0.1130 (⇒ **geometric mean 0.893**, −10.7 %) | the correct "average multiplicative effect" |

Averaging raw ratios would have suggested a **+5 % improvement** where the geometric mean is actually
**−10.7 %**. For ratio data the geometric mean (= exp of the mean log) is the right central tendency.

**(3) The pre-registered threshold is *defined* in log space.** `η_s = P95(|log y − median log y|)`
(§3.8) is computed on log-residuals, and the non-regression floor is `e^{−η_s}`. Testing
`ln(F/G) ≥ −η_s` is therefore a direct comparison in the same units; using the raw ratio would require
converting back and forth.

**(4) GPU throughput noise is multiplicative.** Run-to-run variation scales with the magnitude of the
measurement (a ±1 % effect, not a ±X GFLOP/s effect). Taking logs turns multiplicative noise into
additive noise, which is what makes a single per-shape `η_s` meaningful across the ~5-orders-of-magnitude
range of these shapes (§3.6.1).

*Source: S14 §10.2/§10.4 (gate definition, η_s in log space); Lock A per-shape noise artifact.*

### §5c What the AUC criterion is, and why the measurement defect does not reach it

**Definition.** AUC is the **step-hold integral of `best_gflops_so_far` against
`cumulative_complete_evals`**, evaluated up to a common budget `B* = min` of the two arms' final
completed-evaluation counts. `best_gflops_so_far` is a step function (it only changes when a new
incumbent appears), so the integral is a sum of rectangles, each spanning from one generation's
cumulative-eval count to the next at the *previous* height.

**Why the common budget, and why not generation index.** Evaluations per generation are **not constant**
— population decay halves the population at a diversity-triggered generation (§3.2b), so generation 20
of one arm may represent far fewer evaluations than generation 20 of the other. Integrating against
generation index would therefore compare unequal amounts of search. `B*` makes the two arms answer the
question *"given the same number of evaluations, which arm's best-so-far curve sat higher?"*

**The backing data.** `trajectory.jsonl`, one row per generation (23 rows for medium seed 24001
baseline), carrying:

| field | meaning |
|---|---|
| `best_gflops_so_far` | running maximum — **the AUC integrand** |
| `cumulative_complete_evals` | the abscissa |
| `generation_batch_best_gflops` | that generation's own peak |
| `generation_Q_median_any_valid` | median over that generation's ~510 evaluations |

#### §5c.1 The objection, and why AUC survives it

**The objection is legitimate and must be stated before it is answered:** AUC is built from in-search
measurements taken through the **same client** with the **same 321 warm-ups** that produced the
contaminated remeasures (§7.1b). If that path is unreliable, why is AUC not equally unreliable?

Three answers, weakest to strongest:

**(1) Exposure differs by roughly 30×.** `cumulative_complete_evals` advances ~508–512 per generation
inside **one** client invocation at ~6.4 ms of GPU work per solution. Whatever the short-window effect
is, it is paid **once per invocation**, on the order of the ~50 ms implied by the sweep's knee — so it
can touch only about the first 8 of ~510 solutions (**~1.6 %**), against **28–48 %** for the
fresh-process remeasure, which restarts the clock on every single draw. (§7.1b.1.)

**(2) The integrand is a running maximum, and the contamination is one-sided downward.** An understated
evaluation **cannot lower** `best_gflops_so_far`; it can only fail to raise it. The curve is
structurally resistant to precisely this failure mode, in a way a single-shot median is not.

**(3) The empirical spread settles it.** Same champions, same card, same shape, same client:

| quantity | per-seed range |
|---|---|
| **AUC `F/G`** | 0.9509 – 1.0461 (**±5 %**) |
| 7× remeasure `F/G` | 0.3551 – 2.1175 (**0.36× – 2.12×**) |

An order of magnitude apart. **If AUC shared the contamination, it would share the spread.** It does
not. This is an observation, not an argument from mechanism — and it therefore survives the 2026-08-13
retraction of the clock account (§7.1b), which changed what causes the remeasure defect but not the fact
that AUC is untouched by it.

#### §5c.2 medium capped — the per-seed AUC values

| seed | AUC `F/G` | change | `B*` |
|---|---:|---:|---:|
| 24001 | 1.0358 | +3.58 % | 8,522 |
| 24002 | 1.0210 | +2.10 % | 10,011 |
| 24003 | 0.9783 | −2.17 % | 10,592 |
| 24004 | 1.0461 | +4.61 % | 10,469 |
| 24005 | 0.9509 | −4.91 % | 9,837 |
| **positive** | **3/5** | | required ≥4/5 |

**The 3/5 is a real shortfall, not a near-miss.** The two negatives are −2.17 % and −4.91 %, far outside
any plausible jitter on a quantity whose whole range here is ±5 %. Together with Gen0 3/5 and gen-10 3/5
— all three read from the GA trajectory, none of them through the remeasure — this is why the medium
gate fails **regardless** of how the final-endpoint question is eventually adjudicated (§9.1).

#### §5c.3 The residual risk, stated not buried

One failure mode survives all three arguments above. A genuinely strong candidate that happened to be
understated at its **single** in-search evaluation never becomes the incumbent, so `best_gflops_so_far`
never learns it existed — and the running-maximum argument in (2) gives no protection against a value
that was never admitted in the first place. This cannot be quantified from retained artifacts, because
per-generation benchmark CSVs are not kept (only `00_Final.csv` survives per arm). Status:
**`NOT_EVALUATED`**, and `NOT_EVALUATED ≠ no effect`.

*Source: `[CODE AUDIT]` `stage3_{baseline,guided}/seed_*/medium/trajectory.jsonl`; step-hold integral as
implemented in `agent_run/260809-s14-pershape-baseline/analyze_medium.py`; remeasure range from
§7.1a. Common-budget requirement: §3.2b.*

### §5a How the S11 gene-selection quantities are computed (report-ready; all sealed)

**What sensitivity actually measures.** In one sentence: *"across the sampled config population, how
much better does this gene's best value look than its worst value — measured in population
rank-percentile points of Formocast-predicted latency."* Nothing is run on a GPU; every quantity below
is computed from Formocast's **predicted** latencies over the S11 sampling corpus.

**`S_g ≥ 0.05` — full chain** (all model-space; NOT real GPU):

1. **benefit** (`statistics.py:102/137`): each config's Formocast *predicted latency* → its **percentile
   rank** among all configs (midrank ECDF) → `benefit = 1 − percentile` ∈ [0,1] (faster ⇒ higher). It is
   a population **rank**, not absolute latency. Sealed form:
   `b_{c,s} = 1 − midECDF_s(predicted_latency)`.
2. **cells**: group configs by the value gene *g* takes (e.g. all configs with `DepthU=64` form one
   cell), and collect that cell's benefits. Only **trusted** values get a cell (see below).
3. **shrinkage marginal `m_gv`** (`statistics.py:188 shrinkage_mean`):
   `m_gv = (Σbenefit + α·global_mean) / (n + α)`, **α = 32**.
   *Why shrinkage:* a value seen in few configs would otherwise produce a wild mean; α=32 pulls it
   toward the global mean, so a value needs real support to move its marginal.
4. **sensitivity** (`statistics.py:1166`): `S_g = max_v(m_gv) − min_v(m_gv)` — the spread between the
   gene's best and worst value's shrunk mean benefit.
5. **gate**: `S_g ≥ 0.05` — best and worst value must differ by ≥ 5 rank-percentile points, else the gene
   is deemed to carry no usable signal.

**How to read the number.** `S_g = 0.142` (DepthU on medium) means: configs using DepthU's best value
sit, on average, **~14 percentile points higher** in the predicted-latency ranking than configs using
its worst value. `S_g = 0.00096` (WaveSeparateGlobalReadA on medium) means the best and worst values are
separated by **~0.1 of a percentile point** — indistinguishable, i.e. guiding it would be
indistinguishable from uniform. That asymmetry is the entire sparsity story (§3.5).

**Why the implicit baseline is "uniform".** `S_g = 0` means every value of the gene has the same mean
benefit ⇒ any preference you build over it is arbitrary ⇒ guided sampling ≡ uniform sampling ⇒ the gene
contributes no treatment. The gate is therefore asking "is there anything to guide *toward*?".

Honest limits (charter §8.5):

- it is **model rank space** (not real GPU) — a gene flat in rank could still matter in absolute GFLOPS;
- it is a **per-gene marginal** — blind to epistasis (a value that only helps in combination is invisible);
- it is **survivor-frame / non-causal** — an association over configs that reached scoring, not a causal
  gene effect;
- the **0.05 threshold is a heuristic** (5 percentile points), NOT derived from a noise model or power
  analysis (explicitly flagged in the 2026-08-09 design-discussion). The **0.80 entropy floor is the
  same kind of undocumented constant** — see §3.4c.2, which audits its (absent) derivation.

*Source: statistics.py; `derivation-manifest-capped.json` locked_formulas/locked_constants; qa-03 §0.11.*

**"Fewer than 2 trusted values" — what it means.** A gene has several candidate values (e.g.
DirectToVgprA ∈ {True,False}; DepthU ∈ {16,32,64,128,256,512}). A value counts as **trusted** only if, in
the S11 sampling corpus, it meets ALL of (`workflow.py:758–802`; manifest `gate_definition`):

- **support ≥ 128** (`support_min_conditional_fraw` — ≥128 qualified configs actually used that value);
- **executable** (`Dexec` non-empty — ≥1 config with that value compiled+ran);
- **coverage `Cscore_occ_gv` ≥ 0.95** (≥95% of its occurrences were scored);
- **no `collision_confounded`** (canonical identity not confounded by hash collisions).

Computing a sensitivity needs **≥2 trusted values to compare**; a gene with <2 is **not testable** and is
dropped. The gene that fails this on all three shapes is **`DirectToVgprA`** (`n_trusted = 1`) — only one
of its two boolean values reached the ≥128 trusted-support bar (the other value's configs were too few /
mostly failed to build or score). *Source: derivation-manifest-capped.json per_shape_activation_log;
workflow.py trusted-set builder.*

---

## §6 Artifact / file reference

### Locks

- Lock A (baseline protocol): `agent_run/260809-s14-pershape-baseline/lock/lock_a_protocol.json`,
  checksum at the sibling `lock/lock_a_protocol.sha256` (**not** `lock_a_protocol.json.sha256`)
  (+`.sha256`)
- Lock B (capped guidance): `agent_run/260809-s14-pershape-guidance/lock/lock_b_guided_guidance.json`
  — `lock` id `S14_LOCK_B_GUIDED_GUIDANCE`,
  sha `3ac9768768ac088596687c47635bd6b8b5018d67cecc3f08e69ba2857b0ce59b`
- Lock C (Arm-S shuffle): **pending seal** (bundle derived; seal before any Arm-S outcome viewed)

### Treatment inputs

- Capped guidance weights (what F injects):
  `agent_run/260809-s14-pershape-guidance/out-capped/ga-weights-{medium,large,tiny}.json`
- S11 per-size scores (what the guidance was derived from):
  `study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s11-native-scores.json` (68 MB)
- Activated genes: medium={1LDSBuffer, DepthU}; large={TransposeLDS, UnrollLoopSwapGlobalReadOrder,
  GlobalReadVectorWidthA, GlobalReadVectorWidthB, PrefetchGlobalRead}; tiny=none.

### Run outputs

- Baseline champions/trajectory:
  `agent_run/260809-s14-pershape-baseline/stage3_baseline/seed_<S>/<shape>/{optimization_result.json,trajectory_metadata.json}`
- Guided: `.../stage3_guided/seed_<S>/<shape>/...` *(sibling of `stage3_baseline/`, not nested — path corrected 2026-08-13)*
- 7× remeasure: driver `scripts/s14_guided_remeasure_driver.py` (interleaved G/F, counterbalanced
  start-arm)
- Status: `resume_status.json` (baseline), `guided_status.json` (guided)

### `optimization_result.json` schema (per GA champion)

- `best_individuals` = the 30-gene champion kernel config (incl. `group_0`);
- `best_individual_hashes` = canonical sha256;
- `best_fitness` = champion real-GPU performance (GFLOPS-scale, the value the GA maximized);
- `generations_run` (early-stop-aware);
- `cumulative_any_valid_evals` / `cumulative_complete_evals` / `cumulative_distinct_benchmarked`;
- `seed`, `shape`, `size`.

### Authority docs

- Charter: `study_docs/research/surrogate-dse-plan.md` (§8.2, §8.5, §8.6, §8.6a)
- Experiment plan: `study_docs/research/ductile-origami-warmstart-experiment-plan.md` (criteria + DAG)
- S14 design: `.../ductile-origami-warmstart/s14-stage1-full-ga-outcome-design.md` (§6, §10, §11, §12)
- S11 design: `.../s11-stage1-model-only-factorization-design.md`
- QA readers: `.../qa/qa-09-per-shape-soo-redesign-decisions.md`,
  `.../qa/qa-03-s11-factorization-and-metric-design.md`
- Gate closure reports: `.../reports/staged/s11-...report.md` (S00/S10/S10R2/S10R3/S11 pre-register the
  `staged/` path); S14 now also uses that directory (`REPORT-LOCATION-20260813`, design §12A):
  `.../reports/staged/full-ga-baseline-vs-guided-outcome-report.md`, with three per-shape annexes
  `.../reports/staged/s14-{medium,large,tiny}-report.md`. Naming rule: `reports/README.md`.
- Reboot/resume + Claude supervision infra (methods): `/data1/perlee/S14_RESUME_MECHANISM.md`

---

## §7 Results placeholders (fill after runs + independent verification — DO NOT fabricate)

| Number the report needs | Status | Source path |
|---|---|---|
| Baseline per-shape/seed champion GFLOPS + gen-10 | `NOT_EVALUATED` (baseline champions exist; keep quarantined until analysis) | `stage3_baseline/seed_*/{shape}/optimization_result.json` + `trajectory_metadata.json` |
| Guided per-shape/seed champion GFLOPS + gen-10 | `NOT_EVALUATED` — **all 5 seeds × 3 shapes complete** (quarantined) | `stage3_guided/seed_*/{shape}/...` |
| 7× interleaved G/F remeasure medians — MEDIUM | **MEASURED 5/5** — see §7.1 | `stage3_baseline/seed_*/medium/champion_interleaved.json`; `medium_remeasure_summary.json` |
| 7× interleaved G/F remeasure medians — LARGE | **MEASURED 5/5** — see §7.2 | `stage3_baseline/seed_*/large/champion_interleaved.json` |
| 7× interleaved G/F remeasure medians — tiny | `NOT_EVALUATED` (3/5 remeasured; 24002/24003 pending) | same pattern, per shape |
| Per-shape directional-consistency gate outcome (Gen0/gen-10/AUC/final) | medium computed (see §7.1); **large computed (see §7.2)**; tiny `NOT_EVALUATED` | S14 analysis (post-run) |
| Conditional Arm S (triggered? F vs S) | `NOT_EVALUATED` (conditional) | Lock C + Arm-S runs (if triggered) |
| Native-P0 11,405 large G/F + dilution vs 512 | `NOT_EVALUATED` (scheduled) | native addendum run-root (TBD) |
| S11 gates (7-AND) + decision + reproduction | **NOT PRODUCIBLE** — see §7.3 | `protocol/v1/{manifests,evidence}/...` (will remain absent) |
| S11 per-gene sensitivity table (sparsity) + gate margins | AVAILABLE (descriptive) — 3 genes survive all 7 gates: PrefetchGlobalRead (S=0.094, +88%), UnrollLoopSwapGlobalReadOrder (S=0.090, +80%), DepthU (S=0.054, +7.4%) | `parallel-analyze/out/passes.w72.json`, `diag-lambda2.w72.json`; qa-09 §4.3b |

### §7.1 Medium 7× remeasure (measured, quarantined)

Measured 5/5; **not yet run through the full per-shape gate; two-sided, no conclusion drawn.**

Final-champion 7×-median real-GFLOPS per arm, and the F-vs-G contrast (see §5b for why the log-ratio is
the analysis quantity):

| seed | G median (GFLOP/s) | F median (GFLOP/s) | **F/G ratio** | **% change** | log-ratio `ln(F/G)` |
|---|---:|---:|---:|---:|---:|
| 24001 | 13,495.3 | 13,456.3 | 0.9971 | −0.3 % | −0.0029 |
| 24002 | 12,349.9 | 8,710.9 | 0.7053 | −29.5 % | −0.3491 |
| 24003 | 6,137.5 | 6,595.3 | 1.0746 | +7.5 % | +0.0719 |
| 24004 | 6,283.1 | 13,304.5 | 2.1175 | +111.8 % | +0.7502 |
| 24005 | 13,192.3 | 4,684.9 | 0.3551 | −64.5 % | −1.0353 |
| **median** | — | — | **0.9971** | **−0.3 %** | **−0.0029** |
| *(mean of raw ratios — misleading, see §5b)* | — | — | *1.0499* | *+5.0 %* | *(geo-mean 0.893, −10.7 %)* |

- **2/5 positive, median ≈ −0.3 %** → the final-champion component does NOT meet the pre-registered
  ≥4/5-positive threshold (Gen0/gen-10/AUC components analysed separately; all 2–3/5).
- ~~Per-seed spread is large (F = 0.36×–2.12× of G) vs η_medium = 0.42 % → these are genuine champion
  differences, not measurement noise~~ — **RETRACTED 2026-08-12, contradicted by the raw artifacts.**
  See §7.1a. The pinned `η_medium = 0.0042` does not describe these measurements: the **empirical P95
  log-residual across the 7× repeats is 1.2098, i.e. 288× the pinned value**. Medium's per-seed F/G
  differences are **not** resolvable above measurement dispersion, and the sign inconsistency across
  seeds is what one expects when the median of 7 is itself a lottery.
- Note the baseline arm itself spans 6,137–13,495 GFLOP/s across seeds — GA convergence on this shape is
  highly seed-dependent, and the guided effect sits inside that much larger variance.
- **Deviation:** ran on GPU 5 (not each seed's Lock-A search card) via a non-sealed copy
  `remeasure_interleaved_champion__gpu5deviation.py` adding an opt-in `--gpu-uuid-override` (sealed
  script + Lock A unchanged; within-pair ratio cancels card offset). See `medium_remeasure_deviation.md`.

#### §7.1a Medium's measurement is contaminated by ~28 % dropouts — and the median of 7 is a mode-lottery

**RETRACTION AND CORRECTION (2026-08-12).** The bullet above previously asserted that medium's per-seed
F/G differences were genuine champion differences rather than measurement noise, on the grounds that they
were large relative to `η_medium = 0.0041953`. `[CODE AUDIT]` The raw remeasure repeats contradict this.

The 7× interleaved protocol measures **one fixed champion config**, seven times, on **one card, inside one
process, within a ~27-second window**. It should be the most repeatable number in the study. On medium it
is not:

| seed / arm | the 7 measured GFLOP/s | max/min |
|---|---|---:|
| 24001 G | 13,561 · **3,771** · 13,495 · 13,598 · 13,454 · 13,549 · 13,487 | **3.61×** |
| 24001 F | 13,456 · **2,234** · 13,535 · 13,404 · 13,547 · 13,456 · 13,527 | **6.06×** |
| 24002 G | 12,420 · 12,356 · 12,325 · **6,218** · 12,371 · **5,255** · 12,350 | 2.36× |
| 24005 F | 4,685 · 7,164 · 2,944 · 2,870 · 10,535 · 2,166 · 5,456 | 4.86× |

Recomputing the noise margin the way Lock A defines it (`P95(|log y − median log y|)`) directly from these
repeats, per shape, across all seeds and both arms:

| shape | pinned `η_s` | **empirical P95 log-residual** | ratio |
|---|---:|---:|---|
| **medium** | 0.0041953 | **1.2098** | **288×** |
| large | 0.1228459 | 0.0269 | 4.6× conservative |
| tiny | 0.4466 | 0.0145 | 31× conservative |

**CORRECTION 2026-08-12 (second pass).** The "288×" reading above is *arithmetically right but
diagnostically misleading*, and the correction matters because it changes what has to be fixed. A second
diagnostic campaign (§7.1b) shows medium's repeats are a **mixture of two populations**, and pooling them
describes neither:

| population | share | P95 log-residual | vs pinned `η_medium` |
|---|---:|---:|---|
| **clean** (≥ 95 % of the arm's max) | **101 / 140 = 72 %** | **0.0116** | **2.8×** — same order of magnitude |
| **dropouts** | 39 / 140 = 28 % | — | — |
| pooled, campaign 2 (capped + native) | 140 | 1.0503 | 250× |
| pooled, **campaign 1** (capped + native) | 140 | **1.2098** | **288×** |

**CORRECTION 2026-08-13 (third pass, from the design-discussion of §13).** The "140" above is
**capped + native within campaign 2** — two *P0 levels*, not two campaigns — and the 27.9 % dropout rate
is campaign 2's. **Campaign 1, which is the measurement of record (§13.3), is 46.4 % contaminated**
(capped 45.7 %, native 47.1 %); all four sets pooled are 104/280 = 37.1 %. The 1.2098 figure quoted
above belongs to capped campaign 1's 70 points, not to the 140-point pool. **The contamination in the
primary result set is materially worse than this section originally stated.**

~~So `η_medium = 0.0042` is approximately correct for a clean medium measurement — the pilot that
produced it evidently sampled clean draws.~~ **STRUCK 2026-08-13 (§13.4).** Forensics on
`260807-s14-baseline-run/stage2_noise/raw_repeats.jsonl` show the pilot's medium anchors ran at
4,629 / 3,200 / 2,127 GFLOP/s — **2.9–6.3× slower than the champion**, i.e. 9.31 / 13.46 / 20.26 ms of
warm-up (artifact-derived; §7.1b.4), a far
less exposed regime — with **0/21 pilot dropouts**, and they are *tighter* than the champions' own clean
mode (η_medium is 2.8× **below** the clean-mode P95 of 0.0116). The pin is the repeatability of a
workload that never sampled the contaminant, not a description of clean champion measurement. All three
pins are unrelated accidents of the pilot (§13.4). The defect is still **not a mis-estimated noise
margin**. It is that
28 % of measurements come from a different population entirely, and the protocol has **no mechanism to
detect or exclude them**. Raising `η` would be the wrong repair: it would widen the tolerance for
*everything* in order to absorb a contaminant, destroying the gate's power on the 72 % that are fine.

**Only medium is affected, and it fails in the dangerous direction** — a margin 288× too tight will
classify pure dispersion as a real effect, which is exactly what the retracted bullet did. Large and tiny
are conservative (their real measurements are *more* repeatable than the pin assumes), which is the safe
direction and leaves §7.2's conclusion intact or strengthened.

**Consequences that must be carried into the report:**

- **Medium's per-seed F/G values are not interpretable as champion quality.** With a within-window spread
  of 2–6×, the median of 7 is itself a draw from a wide distribution, so the seed-level "effects"
  (0.36×, 2.12×, …) are largely a measurement lottery. The medium directional-consistency gate has
  little power.
- **The `η_s` values are pilot-derived and were never re-validated against the actual remeasure repeats.**
  `η_s` comes from the 3-anchor × 7-repeat noise pilot (§3.8). This is the first time it has been checked
  against the measurements it is applied to. On medium the pin survives *for clean draws* (2.8×) but the
  protocol never checked whether the draws were clean — that is the gap, and it applies to every shape.
- **§3.3 / S14 §12.2's justification for adding medium to the native addendum is undermined.** That
  justification was "medium is the only shape whose arms differ measurably". If medium's differences are
  measurement dispersion, the premise is void. The native-medium runs remain valid and useful — the Gen0
  decomposition (Q3) does not depend on champion measurement at all — but the stated reason for including
  the shape must be corrected.
- **Large is unaffected and its standing improves.** Its empirical dispersion (0.0269) is well below its
  pinned margin, so "all five seeds inside η_large" is not an artifact of a loose pin.

**Root cause: NOT_EVALUATED.** The bimodality is reproducible within a single process on a single card,
which rules out inter-run drift, thermals across sessions, and card-to-card variation. Candidate
explanations. *(Updated 2026-08-13 — this bullet previously listed clock/power-state transitions as an
undistinguished candidate and said the separating measurement "has **not** been done". **Both statements
are now wrong.** The measurement was done — 3 seeds × 14 records of 1 kHz `sclk` + `busy` telemetry during
a live remeasure — and it **disconfirmed** the clock candidate, which is why clock no longer appears in
the list below. See the block at the head of §7.1b.)* The surviving, still-undistinguished candidates
are: rotating-buffer / cache-residency state differing between repeats (medium uses `RBS = 4096`, large
uses `0`); a launch-overhead floor that dominates at medium's ~134 MFLOP problem size; XCD/CU assignment;
MALL/L2 residency; GSU-4 workspace contention; and whatever accounts for the observed *slower kernel at a
higher clock*. Root cause: **`NOT_EVALUATED`**.

*Source: `[CODE AUDIT]` **the FIRST campaign's** medium repeats, preserved at
`medium_recheck_control/{capped,native}/seed_*/preserved_campaign1_20260812T135613Z/champion_interleaved.campaign1_*.json`
→ `remeasure.{G,F}`. **Citation repointed 2026-08-12:** the live
`stage3_baseline/seed_*/medium/champion_interleaved.json` files were superseded at 14:01–14:04 by the
second diagnostic campaign (§7.1b), so they no longer contain the values quoted above; nothing was lost
(the originals reproduce this table exactly from the preserved path). Large and tiny repeats are still
live at `stage3_baseline/seed_*/{large,tiny}/champion_interleaved.json`. Pinned `η_s` and its formula:
`noise/per_shape_noise.json`.*

(Independently rediscovered during the native-medium analysis; that analysis now lives in
`reports/staged/s14-medium-report.md`. Its superseded working note is retained un-citable under
`reports/working-notes/` and is deliberately **not** given as a source here — see that directory's
README.)

**Dropouts are not exclusive to medium, and not exclusive to one card.** `[CODE AUDIT]` Auditing every
repeat of every shape for values below 80 % of their arm's maximum:

> **⚠ COUNTS CORRECTED AND THRESHOLD PINNED DOWN, 2026-08-13.** This table previously reported medium as
> `39 / 140 = 27.9 %` and large as `0 / 70` — **two different thresholds under one stated rule**, and the
> medium figure does not reproduce. Recomputed from the raw repeats with an explicit definition —
> **a repeat is a dropout when it falls below the given fraction of its own `(seed, arm)` maximum**, over
> all 5 seeds × 2 arms × 7 repeats × 2 P0 levels (n = 140 for medium, 70 for the others):
>
> | shape | campaign | `< 0.80` | `< 0.95` |
> |---|---|---:|---:|
> | medium | **campaign 1** (proposed measurement of record) | **65 / 140 = 46.4 %** | **65 / 140 = 46.4 %** |
> | medium | campaign 2 | **43 / 140 = 30.7 %** | **44 / 140 = 31.4 %** |
> | tiny | — | 0 / 70 | **1 / 70** |
> | large | — | **0 / 70** | 1 / 70 |
>
> Campaign 1 is identical under both thresholds because its contamination is deep — every dropout is
> below 0.80. **Neither the old `39 / 140` nor an independent audit's `38 / 140` reproduces** from the
> current artifacts under either threshold; two recomputations disagreeing with the document and with
> each other means the original number's definition was never pinned down. Use the table above and state
> the threshold whenever quoting a rate. The `101 / 140 = 72 %` clean figure in §7.1a inherits the same
> defect (`140 − 101 = 39`) and is superseded by the campaign-2 `< 0.95` row here.

| shape | cards used | dropouts (campaign 2, `< 0.95`) | rate |
|---|---|---:|---:|
| medium | hip 5 only (`--gpu-uuid-override`, §8.3) | 44 / 140 | **31.4 %** |
| tiny | hip 2, 3, 4, 6, 7 | **1 / 70** | 1.4 % |
| large | hip 2, 3, 4, 6, 7 | **1 / 70** | 1.4 % |

The single tiny dropout is `seed 24004 arm G` on **hip 7**: `3.82, 3.81, 3.78, 3.84, 3.79, 3.80, **0.30**`
— one repeat at 8 % of the others, a 12.74× spread, the same qualitative signature as medium's. So the
mechanism is **not unique to GPU 5**; what differs across shapes is its *rate*. Note also that a P95
statistic cannot see a 1-in-70 event (it is the 98.6th percentile), which is why §7.1a's per-shape P95
table reports tiny as clean — that table measures the *bulk*, not the tail.

**Card and shape were confounded here — resolved in §7.1b.** Every medium measurement was on hip 5 and no
other shape was ever measured there. *(This paragraph previously said the separating test "is in
progress" and that neither hypothesis was established; the test has since returned and §7.1b reports it.
Corrected 2026-08-13 — the two passages had been contradicting each other.)* The outcome, with the
important caveat that the cross-shape arm of it is weak: see **§7.1b**, where hip 5 is exonerated on the
**within-card** pilot contrast, not on the tiny-on-hip-5 result.

#### §7.1b Root cause — the client's warm-up is specified in enqueue *count*, not in *time*

**This is the explanation for §7.1a, and it also bounds the damage: the defect is confined to the
remeasure path and does not reach the GA search.**

`[CODE AUDIT]` `ClientParameters.ini` sets `num-warmups=321` and `num-enqueues-per-sync=321` (there is
also `max-enqueues-per-sync=-1`) — **identical
for all three shapes**. But kernel duration differs by three orders of magnitude, so the same count buys
wildly different amounts of *time*:

| shape | kernel duration | warm-up wall time | outcome |
|---|---:|---:|---|
| **medium** | ~10 µs | **~3.2 ms** | 28 % dropouts |
| large | ~1.87 ms | ~600 ms | 0 / 70 dropouts |
| tiny | dispatch-bound | (invariant to warm-up length) | 1 / 70 |

>  ### ⚠ MECHANISM CONTRADICTED 2026-08-13 — read this before the paragraph below
>
> The clock-ramp account that follows was the proposed *explanation* for the warm-up correlation. A
> direct measurement has now disconfirmed it, and it is retained below only as the hypothesis that was
> tested, **not** as a finding.
>
> `[GPU]` Step 1 of the non-sudo verification ladder: 3 seeds × 14 records, **1 kHz `sclk` + `busy`
> trace sampled during a live medium remeasure** on GPU 5, idle gate clean each time (GPU 0 %, host load
> 0.031–0.079 of 224 cores). The phenomenon reproduced — **25/42 dropouts** — so this traces the real
> effect, not a quiet card. It found:
>
> - clock↔throughput correlation is **negative**, Spearman **−0.32**;
> - dropouts ran at a **higher** median clock (**1798 MHz**) than clean repeats (**1689 MHz**);
> - **every** repeat, clean or contaminated, reached **1512–2065 MHz** — none sat near 132 or 500;
> - counterexamples in both directions: 0.470 of max *at* a 2065 MHz peak; 0.997 of max at only 1674 MHz;
> - dropouts take **longer** — the kernel genuinely runs slower; this is not a reporting artefact.
>
> **Collateral corrections.** (a) GPU 5 tops out at **~1770–1810 MHz** under sustained load, so "clean =
> 2100 MHz" is the wrong reference and any ratio arithmetic against 2100 is void. (b) The sysfs node does
> **not** expose three discrete DPM levels: idle reads `S: 131Mhz *`, but under load it reports a
> *continuous* current clock with 500/2100 as bounds — so a "stuck at a low DPM level" hypothesis was
> never physically available to test. (c) The 2026-08-12 clock probe's null is **uninformative, not weak
> evidence**: `--setperflevel high` never took effect, and the "pinned" arm's trace is identical to
> control (75 % of samples below 200 MHz). It must stop being cited in either direction.
>
> **Instrument limit, stated:** at ~8 ms effective resolution (the value updates every ~8 ms and appears
> SMU-filtered), the trace **cannot** resolve what the clock did inside the 3.2 ms warm-up. It bounds the
> envelope over the GPU-active phase only. The clock story is therefore **not excluded** — it is
> unsupported at the available resolution while the observable clock behaviour points the other way.
>
> **Status: mechanism `NOT_EVALUATED`.** Surviving candidate explanations, none tested: XCD/CU
> assignment, MALL/L2 residency, GSU-4 workspace contention — plus whatever accounts for *a slower kernel
> at a higher clock*.

**What survives, and must not be over-retracted:** the **empirical** warm-up correlation is unaffected.
The sweep below, the within-card pilot contrast (§7.1b.4), and tiny's measured invariance to warm-up
length all stand on their own. **Warm-up duration predicts contamination; what is now unsupported is the
claim that the clock ramp is why.**

*(Hypothesis as originally stated, retained for the record:)* An idle MI300X sits at 132–180 MHz and
needs tens of milliseconds of sustained work to promote to 2100 MHz; medium's 3.2 ms warm-up ends while
the card is still ramping, so the timed window opens on a partially-promoted GPU, and whether the ramp
completed in time is decided by the power governor — which would explain why the result is bimodal
rather than heavy-tailed.

**The decisive evidence is a warm-up sweep** (standalone probe: same client binary, same compiled
champion, one knob varied, 25 fresh processes per variant, idle-gated). It gives a clean monotone knee:

| warm-up wall time | 3.2 ms | 6.4 ms | 13 ms | 26 ms | **51 ms** | 103 ms | 205 ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| dropout rate | **48 %** | 32 % | 12 % | 8 % | **0 %** | 0 % | **4 %** |

**Two caveats added 2026-08-13 (§13.3), both material.** (i) The sweep is **not monotone above the
knee** — 20,544 warm-ups (205 ms) still returned 1/25. (ii) **Every point in this sweep runs at
`rotating-buffer-size = 0`, not the pinned 4096.** RBS 0 alone moves the level 12,430 → 14,153 (+14 %),
so it is a *different estimand*; and the two RBS-4096 long-warm-up variants **crashed 25/25**
(50 × `hipModuleLoad rc=-6`). **The repair is therefore unvalidated at production settings.** The
untried configuration that would settle it is **5,136 warm-ups at RBS 4096** (≈58 ms, past the knee);
both crashed variants used 32,100.

| probe variant | median GFLOP/s | max/min | dropouts |
|---|---:|---:|---:|
| production settings | 12,430 | 5.24 | 48 % |
| `sleep-percent = 0` | 12,466 | 2.32 | 40 % |
| `rotating-buffer-size = 0` | 14,153 | 30.6 | 24 % |
| **32,100 warm-ups + RBS 0** | **14,334** | **1.018** | **0 %** |

Every dropout ever observed lies within `[0.0742, 0.7847]` of its arm's maximum (the lower end is a tiny
dropout in `tiny_gpu5_probe_summary.json`; earlier drafts quoted 0.0785, which was itself the
bound-setting point). **STRUCK 2026-08-13:** two sentences here previously read "a fixed wall-clock
transient of tens of ms is a DPM-ramp signature" and offered `~165/2100 = 0.0786` as a matching clock
ratio. Both are withdrawn — 165 MHz is not a clock this card reports under load, 2100 MHz is not the
level it reaches, and the direct trace shows dropouts at *high* clock. The interval is still a real
observation about the dropout distribution; it is no longer evidence for a clock cause.

**Why the two clean shapes are clean — tested, not assumed.** large's warm-up is ~600 ms, 12× longer than
the ramp needs. tiny was measured directly: its throughput is **invariant to warm-up length** (4.0 GFLOP/s
at both 321 and 20,544 warm-ups) whereas medium's rises 14,001 → 14,375. At 16,384 FLOP tiny is pure
dispatch latency, handled by the command processor. Exposure requires **both** a short wall-clock window
**and** sensitivity to whatever the short window fails to establish; only medium has both. *(This
sentence previously named that second factor as "clock sensitivity"; per the block at the head of
§7.1b, the clock attribution is withdrawn. tiny's measured invariance to warm-up length stands
regardless of what the underlying quantity turns out to be.)*

**Hypotheses eliminated:**

- **The card.** Medium was measured only on hip 5, so card and shape were perfectly confounded (§7.1a).
  Two tests break the confound, and **the order matters**:

  - *Cross-shape (weaker than it looks).* Re-measuring tiny on hip 5 gives **2/70 dropouts on hip 5 vs
    1/70 on the Lock-A cards**, against medium's 28 %. **CAVEAT added 2026-08-13:** on its own this is
    close to vacuous. tiny was shown two paragraphs above to be *insensitive to the whole mechanism*
    (invariant to warm-up length, dispatch-bound), so a clean tiny result on hip 5 is what you would
    observe **whether or not** hip 5 has a clock problem. It rules out a gross card fault, nothing finer.
  - *Within-card, within-shape (decisive).* medium's own **pilot** ran on hip 5 and recorded **0/21
    dropouts**, while medium's remeasure on the same hip 5 records 28 %. Same card, same shape, same
    kernel — so the card cannot be the discriminating variable. What differs between the two is the
    warm-up wall time (pilot anchors were 2.9–6.3× slower configs, giving 9.31–20.26 ms of warm-up, vs medium's
    champion at 3.2 ms), which is exactly the proposed mechanism.

  **hip 5 is exonerated** — on the second test, not the first.
- **Host CPU load.** Reproduced at 2.6–5.9 % of 224 cores with GPUs otherwise idle (§7.1b campaign).
- **Rotating buffer.** Neither necessary nor sufficient — but it does cost medium ~12 % deterministically
  (a 420 MB working set exceeding the MALL), which is a separate, non-random effect.
- **Inter-measurement sleep, and config-specificity.** Both ruled out by the probe.

#### §7.1b.1 The GA search is NOT affected — checked, and the mechanism explains why

The investigating agent flagged a concern that the same 321-enqueue warm-up was used for every candidate
during the GA search, which would be far more serious than a remeasure defect. **The artifacts refute
it.** `[CODE AUDIT]` medium `best_fitness` across all **20** completed runs (2 arms × 5 seeds × 2 P0 levels;
an earlier draft said 15, which omitted one of the four arm×level blocks):

| campaign | per-seed `best_fitness` (GFLOP/s) |
|---|---|
| capped G | 13,679 · 12,545 · 15,255 · 12,606 · 13,695 |
| capped F | 13,826 · 12,816 · 15,329 · 14,122 · 13,449 |
| native G | 14,479 · 14,195 · 14,013 · 15,407 · 14,523 |
| native F | 14,369 · 14,177 · 14,387 · 13,536 · 15,166 |

All twenty sit in 12,545–15,407, consistent with the **fully warm** figure of ~14,350 and with the clean
mode of the remeasure. None shows the degraded signature.

This is exactly what §7.1b's mechanism predicts. The GA benchmarks thousands of candidates inside one
long-lived invocation, so **the card is warm throughout**; the remeasure benchmarks one config in a fresh,
short process and therefore **starts cold every time**.

**ARGUMENT REPLACED 2026-08-13 (§13.6).** The `best_fitness` band alone does **not** establish this:
`best_fitness` is a *maximum* over ~8,500 evaluations and is therefore precisely the statistic most
robust to one-sided *downward* contamination — it cannot evidence that individual candidate evaluations
were not understated, and understated evaluations are what would corrupt *which* candidate won. An
earlier draft argued from the Gen0-to-final gradient; that argument is **withdrawn**
(`best_gflops_so_far` is monotone by construction, so a mode lottery predicts the same observation).
The valid evidence is:

- **`generation_Q_median_any_valid`** — a median over ~510 evaluations per generation, which a 28–48 %
  multiplicative contaminant would depress and destabilise. Medium sits **inside** the range of the two
  immune shapes: gen-to-gen mean |Δ| medium 5.58 % / 4.61 % vs large 6.98 % / 6.11 % and tiny 6.50 % /
  4.21 %.
- **An exposure bound from warm-up duration** — `cumulative_complete_evals` advances ~508–512 per
  generation inside **one** client invocation at ~6.4 ms of GPU work per solution. Whatever the
  short-window effect is, it is paid **once per invocation** and lasts on the order of the ~50 ms implied
  by the sweep's knee, so it can touch only roughly the first 8 of ~510 solutions (**~1.6 %**), versus
  28–48 % for the fresh-process remeasure. *(Reworded 2026-08-13: the arithmetic is unchanged but no
  longer presumes a clock ramp — see the block at the head of §7.1b. It rests on the sweep's measured
  ~50 ms knee, not on a DPM model.)*

**Champion *resolution* is uncontaminated as a matter of record, not inference.** `[CODE AUDIT]`
`selection_candidates` has **exactly one entry in 40/40 arm-entries**, and the resolved `canonical_hash`
is in that arm's `best_individual_hashes` in **40/40**.

> **PATH CORRECTED 2026-08-13.** An earlier draft cited `optimization_result.json`'s
> `resolution_provenance`. That key is **absent entirely from all 45** of those files (not present-and-empty, as an earlier wording had it), so
> the claim as written was not reproducible from the path it named. The reproducible path is
> `champion_interleaved.json` → `arms.{G,F}.resolution_provenance.selection_candidates`
> (20 files × 2 arms = **40 arm-entries**, which is where the denominator comes from), checked against
> `best_individual_hashes` in each arm's own `optimization_result.json`. Both counts were re-derived from
> the corrected path and are **unchanged at 40/40 and 40/40**; only the citation was wrong.

The
selection rule — which *does* read the demonstrably contaminated single-shot `original_final_gflops`
(seed 24001 medium G records **2,961.87 GFLOP/s / 45.3 µs** for a config whose warm value is ~9.9 µs,
a ~4.6× deficit whose cause is `NOT_EVALUATED` — an earlier draft read "consistent with a card near 450 MHz", struck 2026-08-13 because the direct trace found **every** repeat at 1512–2065 MHz) — was **vacuous in every instance**. The
contaminated value is recorded but arbitrated nothing.

**Consequence:** champion *selection* and *resolution* are not contaminated. In-search contamination at
a low residual rate is not excluded, and see §7.1b.3 for why it may not be arm-symmetric.

#### §7.1b.2 Salvageability — the contamination is one-sided, so the data is recoverable

Every mechanism above can only make a measurement **too slow**, never too fast. In the warm-up sweep the
**max of 25 short-warm-up runs is within 0.5 % of the median of fully-warm runs**. So the estimator that
recovers the true value is the **maximum over repeats**, per arm, before forming F/G.

- ~~At the worst observed dropout rate (48 %), P(all 7 repeats dropped) = 0.6 %; no existing arm has all
  7 dropped, so every arm is recoverable.~~ **RETRACTED 2026-08-13 (§13.3).** Both halves are false.
  **Counterexample:** capped campaign 1, seed 24005 arm F is
  `4685, 7164, 2944, 2870, 10535, 2166, 5456` — **all seven contaminated**; `max` returns 10,535 against
  the same config's clean 13,407 in campaign 2, **under-recovering by 21.4 %**. And the i.i.d.
  `0.48⁷ = 0.6 %` calculation does not apply: repeats inside one window are **governor-correlated**, so
  the governor can hold a low state for a whole window.
- This is **pure re-analysis of data already collected** — no GPU time, no re-run.
- Cross-check: the max estimator applied to the original campaign collapses medium's per-seed F/G from
  0.36×–2.12× to within ±7 % (see the cross-campaign table in §13.3 of the S14 design), and a second independent campaign measured with the pre-registered
  median reached the same conclusion. Two different routes agree.

**But it replaces the pre-registered median-of-7 and therefore requires an owner decision and a recorded
deviation before it is applied — and it must then be applied uniformly to all three shapes**, not only to
the shape whose numbers it improves.

The better long-run fix is to specify warm-up in **wall time** (or ≥ ~5,000 enqueues for a 10 µs kernel).
That edits hash-locked configs, so it is a protocol change and out of scope for re-analysis of this data.

**What could NOT be tested (stated, not glossed) — SUPERSEDED 2026-08-13.** This paragraph read that the
decisive confirmation would be a `rocm-smi --setperflevel high` pin, which silently no-op'd (`/sys`
read-only in the container, no host root), leaving the intended "pinned" arm as a second control whose
23/70 dropouts replicate rather than refute. **That framing is now wrong in two ways.** First, the
no-op'd probe's null is not weak evidence but **uninformative**: its clock trace is identical to control,
75 % of samples below 200 MHz, so nothing was pinned and nothing can be read from it in either direction.
Second, a pin is no longer the decisive test, because a **direct 1 kHz clock trace during a live
remeasure has since disconfirmed the clock account outright** (Spearman −0.32, dropouts at a *higher*
median clock than clean repeats — see the block at the head of §7.1b). A pin would now test a hypothesis
the data already disfavour. It also requires **write access to the card** via `pp_od_clk_voltage` /
`amd-smi`, which is a governance escalation, not the ten-minute `sudo` task described earlier.

*Source: `[CODE AUDIT]` `ClientParameters.ini` (`num-warmups`, `enqueues-per-sync`, `sleep-percent`,
`rotating-buffer-size`, all three shapes); `medium_remeasure_root_cause.md` (full write-up, probe drivers
and raw sweep data); `stage3_*/stage5_*/seed_*/medium/optimization_result.json` (`best_fitness`);
`champion_interleaved.json` → `remeasure.{G,F}` (dropout ratio range, all shapes).*

#### §7.1b.3 Arm-asymmetric contamination — the "it cancels in the paired ratio" defence does not hold

**Added 2026-08-13 (§13.6). This retracts a claim made earlier in this index.**

Earlier drafts argued that because the contamination is strictly one-sided, it is also arm-symmetric and
therefore cancels in the within-pair `F/G` ratio. `[CODE AUDIT]` The champion-verification numbers
contradict that directly. `WinnerGFlops` from each medium arm's `Data/00_Final.csv` — the same client
path, one measurement per arm:

| seed | baseline (G) | guided (F) |
|---|---:|---:|
| 24001 | **2,961.9** | 13,590.7 |
| 24002 | **8,846.0** | 12,773.8 |
| 24003 | **4,210.4** | **8,384.2** |
| 24004 | 12,516.2 | 14,040.5 |
| 24005 | 11,542.6 | 13,359.8 |
| **median** | **8,846.0** | **13,359.8** |

The baseline arm is degraded far more often than the guided arm. (Deliberately no count of "contaminated
arms" is given: it depends on the assumed clean reference for a single-shot value, and the two reviewers
counted 3/5 and 4/5 respectively. The medians carry the point without that judgement.)

**Correct wording, which supersedes the earlier claim:** the contamination is **one-sided**; whether it
is **arm-symmetric is `NOT_EVALUATED`**, and it cannot be checked retrospectively because per-generation
benchmark CSVs are not retained (only `00_Final.csv`).

**Warning for anyone drafting from this index:** `original_final_gflops` must **never** be used as an
endpoint. On these numbers the guided arm would look dramatically better (median 13,360 vs 8,846) purely
from contamination. It is not the endpoint — the endpoint is the 7× interleaved remeasure — and §13.6
requires the report to say so explicitly so no future reader reaches for it.

*Source: `[CODE AUDIT]`
`stage3_{baseline,guided}/seed_*/medium/1_BenchmarkProblems/*/Data/00_Final.csv` → `WinnerGFlops`;
S14 design §13.6. **Do not use a `**/Data/00_Final.csv` glob** — it also matches the
`remeasure_work/{G,F}/…` copies, so seed 24001 arm G alone returns three values (2961.87, 6195.34,
13436.4) instead of the one champion-verification value. The table above uses the top-level
`1_BenchmarkProblems` CSV, which is the same file `resolution_provenance.selection_sources.candidate_matrix_csv`
names.*

#### §7.1b.4 Full provenance of `η_medium`, and a residual the warm-up mechanism does NOT explain

**Added 2026-08-13, reframed the same day.** §13.4 states that all three `η_s` pins are "pilot
accidents". This subsection gives the primary-artifact detail behind that for medium, and records a
discrepancy that argues **against** the completeness of the warm-up account. ⚠ **The reframing:** when
written, this residual looked like one anomaly inside an otherwise working clock-ramp account. The
direct clock trace at the head of §7.1b has since **disconfirmed that account**, so the residual below
is no longer an isolated puzzle — it is one of several independent signals against a clock cause. The
*warm-up-duration* correlation it tests is unaffected. It is written here because it is currently the
strongest disconfirming evidence in the file and must not live only in conversation.

**Provenance.** `[CODE AUDIT]` `agent_run/260807-s14-baseline-run/stage2_noise/computed.json`, produced
2026-08-07T23:57:03Z–2026-08-08T00:06:21Z (558 s wall) from `config/s14-smoke.yaml`, on
`HIP_VISIBLE_DEVICES=5`. Computed by `scripts/compute_per_shape_noise.py:30`.

**Design of the pilot: 3 anchors × 7 repeats = 21 measurements.** Residuals are
`|log y − median_r log y|` taken **within anchor**, pooled to 21, then `P95(..., method='linear')`.

| anchor | hash | medium GFLOP/s (median of 7) | own max/min | kernel | 321 × kernel |
|---|---|---:|---:|---:|---:|
| 1 | `14477b97…` | 4,629.1 | 1.0089 | 29.0 µs | **9.31 ms** |
| 2 | `31a76db9…` | 3,199.9 | 1.0028 | 41.9 µs | **13.46 ms** |
| 3 | `dbe08bc4…` | 2,127.0 | 1.0040 | 63.1 µs | **20.26 ms** |
| *(champion, for contrast)* | — | *~13,500* | *0.36×–2.12×* | *9.9 µs* | ***3.19 ms*** |

Anchor 2's raw seven: `3195.3, 3200.6, 3199.5, 3199.9, 3198.7, 3200.3, 3204.4`.

**Three confounders are ruled out by the artifact, not assumed.** The pilot used (i) the **same card**,
GPU 5; (ii) the **same** `rotating-buffer-size = 4096` for medium as production
(`driver_status.json → environment.DUCTILE_PERSIZE_RBS`); and (iii) **fresh clients per repeat** —
`computed.json → R_s_formula` reads *"median of all 21 GFLOPS values from 3 anchors x 7 **fresh-client**
repeats"*. That last one kills the otherwise-natural hypothesis that the pilot stayed warm across its
repeats while the remeasure restarts cold. It does not. **The only controlled difference between the
clean pilot and the contaminated remeasure is config speed, hence warm-up wall time.**

**⚠ The residual the mechanism does not explain.** Interpolating the warm-up sweep (§7.1b) onto the
anchors' warm-up times predicts the pilot should **not** have been clean:

| anchor warm-up | sweep-implied dropout rate | expected dropouts in 7 | observed |
|---:|---:|---:|---:|
| 9.31 ms | ~23 % | 1.6 | **0** |
| 13.46 ms | ~12 % | 0.8 | **0** |
| 20.26 ms | ~10 % | 0.7 | **0** |
| **total** | | **≈3.1 / 21** | **0 / 21** |

Under a Poisson approximation `P(0 | λ = 3.1) ≈ 4.3 %`. Unlikely, not impossible — but it means the
warm-up account explains the *direction and the bulk* of the effect while **over-predicting dropouts in
the 9–20 ms band**. Two candidate outs, **both `NOT_EVALUATED`**:

1. **The sweep is at `RBS = 0`; the pilot and production are at `RBS = 4096`.** RBS 0 alone moves the
   level 12,430 → 14,153 (+14 %), so the sweep is a curve over a *different estimand* and may not
   transfer. The 5,136-warm-ups @ RBS-4096 probe (§13.7 item 2) is the test that would settle it.
2. **The anchors are different configs, not merely slower ones**, and may differ on axes other than
   kernel duration.

**How to report this:** the warm-up **correlation** is well supported in direction and at the extremes
(3.2 ms → 48 %, 601 ms → 0 %) and by the within-card contrast, but it is **not** quantitatively
calibrated in the middle of the range. Do not present the sweep as a predictive model. `NOT_EVALUATED`
is the honest status of the 9–20 ms band — and, since 2026-08-13, of the *cause* at every point on the
curve.

**What survives regardless:** `η_medium = 0.42 %` was measured on configs 2.9–6.3× slower than the
champion whose gate it governs, and is tighter than that champion's own clean-mode P95 (0.0116) by 2.8×.
That is true whatever explains the 9–20 ms band.

*Source: `[CODE AUDIT]` `agent_run/260807-s14-baseline-run/stage2_noise/{computed.json,driver_status.json,raw_repeats.jsonl}`;
`scripts/compute_per_shape_noise.py:30`; sweep from §7.1b. Kernel times derived as
`2·256·256·1024 FLOP ÷ GFLOP/s`.*

### §7.2 Large 7× remeasure (measured, quarantined)

Measured 5/5; **not yet run through the full per-shape gate; two-sided, no conclusion drawn.**

Final-champion 7×-median real-GFLOPS per arm, and the F-vs-G contrast (see §5b for why the log-ratio is
the analysis quantity):

| seed | G median (GFLOP/s) | F median (GFLOP/s) | **F/G ratio** | **% change** | log-ratio `ln(F/G)` |
|---|---:|---:|---:|---:|---:|
| 24001 | 575,916.0 | 534,364.0 | 0.9279 | −7.2 % | −0.0749 |
| 24002 | 539,476.0 | 545,938.0 | 1.0120 | +1.2 % | +0.0119 |
| 24003 | 527,060.0 | 559,859.0 | 1.0622 | +6.2 % | +0.0604 |
| 24004 | 537,433.0 | 511,975.0 | 0.9526 | −4.7 % | −0.0485 |
| 24005 | 535,467.0 | 535,810.0 | 1.0006 | +0.1 % | +0.0006 |
| **median** | — | — | **1.0006** | **+0.1 %** | **+0.0006** |
| *(mean of raw ratios — misleading, see §5b)* | — | — | *0.9911* | *−0.9 %* | *(geo-mean 0.9900, −1.0 %)* |

Pre-registered directional-consistency components (≥4/5 positive required on each):

| component | positive seeds | verdict |
|---|---:|---|
| Gen0 best | 1/5 | fail |
| gen-10 best | 2/5 | fail |
| AUC (best-so-far, common eval budget) | 3/5 | fail |
| final champion (7× median) | 3/5 | fail |
| final **non-regression** `F ≥ G·e^{−η_s}` | **5/5** under the pinned `η`; **3/5** under large's empirical repeatability — see **§7.2a** | **conditional — unresolved** |
| final **improvement** `F > G·(1+δ_s)` | 0/5 | fail |

- **3/5 positive, median ≈ +0.1 %** → the final-champion component does NOT meet the pre-registered
  ≥4/5-positive threshold. No component does; non-regression passes on all five seeds.
- Per-seed spread is **0.93×–1.06×**, i.e. every seed lies inside η_large = 12.28 %
  (non-regression floor `F/G ≥ 0.8844`). Unlike medium — whose per-seed differences are
  instrument-invalid rather than real (§7.1a) — **none of the large per-seed differences is
  resolvable above the shape's own noise margin** — the arms are indistinguishable on this shape at
  n=5, rather than differing inconsistently.
- The baseline arm itself spans only 527,060–575,916 GFLOP/s (±4.4 % about its median), versus medium's
  6,137–13,495 (a 2.2× spread). Root cause: large (2304×1024×214336) is **main-loop dominated**, so the
  GA lands in essentially the same performance basin regardless of seed. There is little seed-to-seed
  headroom for a Gen0 prior to move, which bounds how large any guided effect could have been.
- Large carries the **most** activated genes of any shape (5: `PrefetchGlobalRead`, `TransposeLDS`,
  `UnrollLoopSwapGlobalReadOrder`, `GlobalReadVectorWidthA/B`; see §3.5/§3.6) and still shows ≈0 net effect. This is the practical
  consequence of the sparsity finding: even the best-supplied shape does not carry enough model signal
  to move the outcome.

#### §7.2a The large non-regression pass is conditional on an unvalidated margin

**This affects the only pre-registered component that passed anywhere in this study, and it is
unresolved. Do not quote the 5/5 pass without the margin it is conditional on.**

`[CODE AUDIT]` The `η_s` values are pilot-derived (3-anchor × 7-repeat, §3.8) and were **never re-checked
against the remeasure repeats they actually gate**. §7.1a recomputes them from those repeats. Applying
both margins to large's non-regression criterion `F/G ≥ e^{−η}`:

| seed | F/G | pinned `η = 0.1228` → floor 0.8844 | empirical `η = 0.0269` → floor 0.9735 |
|---|---:|---|---|
| 24001 | 0.9279 | PASS | **FAIL** |
| 24002 | 1.0120 | PASS | PASS |
| 24003 | 1.0622 | PASS | PASS |
| 24004 | 0.9526 | PASS | **FAIL** |
| 24005 | 1.0006 | PASS | PASS |
| | | **5/5 PASS** | **3/5 — gate not met** |

**Why this is not simply a matter of swapping in the better number.** The two estimates measure
*different variance components*, and neither is obviously the right one:

- The **empirical** 0.0269 comes from 7 repeats in one process, on one card, the whole interleaved
  window **spanning ~106 s** (`[CODE AUDIT]` first-to-last timestamp in
  `stage3_baseline/seed_24001/large/champion_interleaved_raw.jsonl`, 14 records — ~15 s between adjacent
  draws; an earlier draft said "~27 s apart", which was medium's window, not large's). Those repeats
  are **correlated**: they exclude between-window drift, thermal state changes across hours, and
  between-day variation. It is therefore plausibly a **lower bound** on true measurement noise — which
  would make the 3/5 verdict too harsh.
- The **pinned** 0.1228 comes from a 3-anchor × 7-repeat pilot whose design may capture sources the
  within-window repeats cannot see — but it was fitted on different measurements and never validated
  against these.

Adjudicating between them requires a **between-window repeatability measurement that does not exist**.

**Defensible reporting (recommended, pending owner decision):** state the gate outcome **under both
margins**, disclose that they disagree on the verdict, and state plainly that the pre-registered margin
was never validated against the measurements it gates. Reporting only the 5/5 pass would present as
settled a result that rests on an unvalidated constant; reporting only the 3/5 would present a lower
bound on noise as if it were the noise.

**Note the asymmetry with medium.** On medium the pin is **288× too tight** (§7.1a), which manufactures
false positives; on large it is **4.6× too loose**, which manufactures false passes. Both directions of
error are present in the same pre-registered gate, on the two confirmatory shapes, for the same reason:
`η_s` was never validated against the gating measurement.

*Source: `[CODE AUDIT]` `stage3_baseline/seed_*/large/champion_interleaved.json`
(`F_over_G_median_ratio`, `remeasure.{G,F}` raw repeats); `noise/per_shape_noise.json`;
recomputation of `P95(|log y − median log y|)` per §3.8's own formula.*

#### §7.2.1 Root cause of the Gen0 component (1/5) — guidance moves the centre, GA reads the extreme

The Gen0 result is the most diagnostic, because Gen0 is *exactly* where the treatment is applied — the
guided arm differs from baseline **only** in the Gen0 sampling distribution. It scored 1/5, i.e. guided
Gen0 was worse on four of five seeds. Splitting Gen0 into a **centre** statistic and an **extreme**
statistic explains why:

| seed | Gen0 median Q — G | Gen0 median Q — F | **centre F/G** | Gen0 best GFLOP/s — G | Gen0 best GFLOP/s — F | **extreme F/G** | valid/512 G | valid/512 F |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 24001 | 0.8887 | 0.9052 | **1.0186** | 464,638 | 385,612 | 0.8299 | 489 | 483 |
| 24002 | 0.8797 | 0.8970 | **1.0197** | 411,852 | 439,016 | 1.0660 | 480 | 488 |
| 24003 | 0.9290 | 0.8799 | 0.9471 | 409,646 | 398,118 | 0.9719 | 485 | 487 |
| 24004 | 0.8883 | 0.9087 | **1.0229** | 449,519 | 379,399 | 0.8440 | 485 | 480 |
| 24005 | 0.8841 | 0.9187 | **1.0390** | 435,831 | 425,865 | 0.9771 | 486 | 491 |
| **median** | — | — | **1.0197** | — | — | **0.9719** | — | — |
| **seeds F > G** | — | — | **4/5** | — | — | **1/5** | — | — |

*Source: `stage3_{baseline,guided}/seed_*/large/trajectory.jsonl`, generation-1 record
(`generation_Q_median_any_valid`, `best_gflops_so_far`, `generation_any_valid_count`).*

The two columns point in **opposite directions, consistently**:

- **The guidance works on the quantity it was designed to move.** The *typical* Gen0 candidate is better
  in the guided arm on 4/5 seeds (median +2.0 %). The prior is doing what a prior should do: it shifts
  probability mass toward configurations the S11 model rates well.
- **The GA does not consume that quantity.** Selection reads the *top tail* — `best_gflops_so_far` at
  Gen0 is a **maximum over ~485 valid draws**, an extreme-value statistic. Extreme values are governed
  mainly by the **spread** of the sampling distribution, not its centre. Concentrating probability mass
  (which is what any non-uniform prior does) raises the mean while shrinking the upper tail, so the
  expected maximum can fall even as the median rises. Guided Gen0 best is worse on 4/5 seeds
  (median −2.8 %).
- **It is not a validity-rate artifact.** Valid candidates per 512 are 480–489 (baseline) vs 480–491
  (guided) — the arms produce statistically indistinguishable numbers of executable configs, so the
  difference is not "guidance generated more unbuildable kernels".
- **This is the mechanism the entropy cap was built to bound, operating in the direction it was meant to
  protect.** `ENTROPY-CAP-20260810` caps ρ so that `H_norm(p1) ≥ 0.80` precisely to stop the prior from
  collapsing Gen0 diversity (§3.4). The data show the tension is real and that the cap did not eliminate
  it: even a ≤20 %-entropy-loss prior over 5 of 29 genes is enough to cost ~2.8 % of the Gen0 maximum
  while gaining ~2.0 % on the median.

**Honest limits on this root cause.** With n=5 neither 4/5 nor 1/5 is individually significant (a fair
coin gives ≥4/5 with probability 3/16 ≈ 0.19). The claim that survives is the **paired contrast**: the
centre and the extreme move in opposite directions on the same runs, in the direction the extreme-value
argument predicts, on 4 of the 5 seeds for both statistics. Gen0 values are also single-run,
non-remeasured numbers and therefore carry the winner's-curse bias described in §5 — they are not
directly comparable in magnitude to the 7×-remeasured final-champion figures above. Confirming this
mechanism properly needs a targeted measurement (e.g. the full Gen0 fitness distribution per arm, or an
Arm-S shuffle control, §3.9), which is **not evaluated** here.

**Why this matters for the design.** If the mechanism holds, then a per-gene Gen0 prior is being scored
by a metric it does not optimise: it improves the *average* draw while the GA keeps only the *best*
draw. That is a statement about the coupling between guidance and the GA's selection rule, not about
whether the S11 model is right — and it is testable independently of whether the guidance signal is
sparse.

### §7.3 S11 finding — the sealed max-reducer `analyze` cannot emit locked guidance on this data

*(verified, report-ready. For a from-first-principles walkthrough of the mechanism below, see §3.4a.)*

An out-of-band parallel reproduction (`agent_run/260803-…/parallel-analyze/`, VERIFICATION.md) proved
bit-identical to the sealed serial path on all three verified axes, at ~3 orders of magnitude speed
(156.7 s vs days):

- **(a)** per-replicate bit-equality vs the sealed O(N²) oracle for all 4 stochastic passes
  (workers 1/3/7, 0 failures);
- **(b)** partition-independence — `agent_run/260803-ductile-factorized-guidance-s11/parallel-analyze/out/passes.w40.json`
  and `passes.w72.json` are byte-identical (`[CODE AUDIT]` md5 `ef6a016a688512f4f9ad0ad6cb660340` for both,
  re-verified 2026-08-13). An earlier draft cited a file named `passes.json`, which does not exist;
- **(c)** sealed tree unchanged.

It reaches the **same terminal `AssertionError` at sealed `s11/guidance.py:95` (`select_global_lambda`)**.
Decisive determination = **(A) FAITHFUL** (§5.4 of VERIFICATION.md: the fully-sealed-ECDF path yields
bit-identical `guidance_inputs`/`gate_calls`/λ-curves and the same assertion — not a parallel-side
defect).

Root cause: only 3 genes survive the 7 model gates, but the sealed **0.80 normalized-entropy floor is
structurally unreachable** for the signal-bearing low-cardinality genes — PrefetchGlobalRead
(4 candidates / 2 trusted → max attainable H_norm = 0.7345) and DepthU (6/2 → 0.6576) — at **any λ, for
any data** (a math property of few-candidate/few-trusted genes with a uniform baseline; PrefetchGlobalRead
alone, at +88% sensitivity margin with every stochastic gate passing ≥3×, caps H at 0.7345 < 0.80 and
forces the assertion).

**This is exactly the entropy-floor/sparsity tension that motivated `ENTROPY-CAP-20260810`** (binary
floor → per-gene mixture cap ρ) for the per-shape S14 path — independently confirmed here from the sealed
pipeline itself.

Per governance the assertion was **reported, not patched**; sealed tree untouched. Implication: the
serial `analyze` (running for days) will hit the identical assertion and produce nothing — the parallel
run established this in minutes.

#### §7.3.1 What the max-reducer result tells us (insights)

The run emits **no guidance artifact**, but it is far from uninformative — it is a clean,
sealed-pipeline probe of the model's signal. Five things follow.

**(1) The sparsity is reducer-independent — not an artifact of splitting per shape.**
The aggregate **max** reducer pools all three sizes (each config is credited with its *best* size), so
it is the richest signal the protocol can construct. It still surfaces only **3 of 26 testable genes**.
Per-shape gave 0/2/5. This pre-empts the natural objection "you diluted the signal by going per-shape":
the sparsity survives the least-diluted reducer available.

**(2) Two independent reducers select the same genes — the sparse signal is stable, not noise.**
Max-reducer's survivors {PrefetchGlobalRead, UnrollLoopSwapGlobalReadOrder, DepthU} are **all** inside
the per-shape activated union {DepthU, 1LDSBuffer} ∪ {PrefetchGlobalRead, TransposeLDS,
UnrollLoopSwapGlobalReadOrder, GlobalReadVectorWidthA, GlobalReadVectorWidthB}. Two different
aggregation schemes converging on the same small gene set is **positive evidence that the few genes with
signal are reproducibly identified**. (2 of the 3 are large's top genes and 1 is medium's — consistent
with the strongest per-gene contrasts coming from large; that mechanism is interpretation, not proof.)

**(3) The failure is NOT weak evidence — the surviving genes pass with wide margins.**

| gene | S_g (floor 0.05) | S / own-null p95 | S / familywise p95 | bootstrap CI half-width (max 0.025) | best/worst recurrence (min 0.90) |
|---|---|---|---|---|---|
| PrefetchGlobalRead | 0.0942 (+88%) | 10.63× | 3.14× | 0.0066 | 1.000 |
| UnrollLoopSwapGlobalReadOrder | 0.0900 (+80%) | 11.86× | 3.00× | 0.0068 | 1.000 |
| DepthU | 0.0537 (+7.4%) | 5.58× | 1.79× | 0.0087 | 1.000 |

Every stochastic gate clears by **1.79×–11.86×**, CI half-widths are 3–4× inside the limit, recurrence is
perfect. So the pipeline does not stop for lack of signal — it stops at the **last** step, turning
evidence into a sampling distribution.

**(4) The transferable design lesson: a constant entropy floor is incompatible with low-arity genes.**
With a uniform baseline over `n` candidates and `k` trusted values, the most diffuse admissible `p1`
(λ=0, full strength) has a **ceiling** on `H_norm` that depends only on `(n,k)` — `0.7345` for (4,2),
`0.6576` for (6,2); taking the supremum over *all* strictly-positive baselines for (6,2) still only
reaches `0.7435`. A fixed floor of 0.80 therefore **silently forbids guiding any gene of that arity, at
any λ, for any data, however strong its evidence**. The gate conflates "preserve diversity" with "have
enough candidate values": it imposes an undocumented implicit requirement on `k/n`. The fix is either
(i) express the floor **relative to each gene's attainable maximum**, or (ii) cap the *strength* rather
than exclude the gene — which is exactly `ENTROPY-CAP-20260810` (§3.4).

**(5) It independently validates that ENTROPY-CAP was necessary, not opportunistic.**
The amendment was designed on the per-shape path. This run reproduces the same structural failure
through the **unmodified sealed pipeline on a different reducer** — so the amendment fixed a real,
general defect rather than a convenient obstacle (no gate-shopping).

**What it cannot tell us (honest limits).** It yields no locked guidance, so it cannot serve as an
alternative guidance source for S14; it says nothing about real-GPU effect; and its 3-gene set is still
a model-space, per-gene marginal quantity (epistasis-blind, survivor-frame), so per charter §8.5 it
localizes the negative to *marginal-loss*, not to "the model is useless".

*Source: `parallel-analyze/VERIFICATION.md` §5.1–§5.5; `out/passes.w72.json`; `out/diag-lambda2.w72.json`;
`derivation-manifest-capped.json` per_shape_activation_log.*

---

## §8 Known caveats / limitations (for the Discussion section)

- **Modest power** (5 paired seeds; not significance), **single development cluster**, **tested shapes
  only** — no generalization.
- **"P0-capped=512 variant"** scoping; the effect is measured at P0=512 (**treatment×budget
  interaction**) — the native-11,405 addendum quantifies dilution / robustness.
- **Max-reducer S11** carries a **construct-validity caveat** (why the per-shape guidance was re-derived
  off the per-size scores, bypassing the aggregate max reducer); the reducer-version closeout is reported
  with that caveat and **does not feed S14**.
- **Order confound:** baseline (G) ran for all seeds before guided (F); the **interleaved 7× remeasure**
  is the controlled champion real-GFLOPS comparison for drift. State this explicitly.
- **Physics-direction not attributed** unless conditional Arm S is triggered and F beats both G and S;
  otherwise attribution is limited to "capped factorized initialization bundle vs baseline" (full
  physics-direction attribution is the registered job of downstream S20, currently frozen).

### §8.1 Host-reset / facility power fault (2026-08-11, materially limited scope)

From 03:37 UTC the machine began hard-resetting every **57–58 min** (≈11 resets in the following 12 h),
where it had previously stayed up for days.

Cause — **external AC power loss, unrelated to this workload** (evidence):

- BMC: `Last Power Event: ac-failed`; `restart_cause: power-up due to always-restore power policy`;
  watchdog **Stopped**.
- Two resets (11:18, 14:22) occurred with **large NOT running** (GPU idle / only CPU S11) — direct
  disproof of workload causation. baseline had earlier run the same 5-GPU large load for 20 h with zero
  resets.
- No OS shutdown sequence / reboot command / OS watchdog / kernel panic; **all other users' containers
  restart too**.
- Accompanied by a PCIe RxErr correctable-error storm on `0000:35:05.0` (Intel PCIe Gen5 Port C).

Consequence for the experiment:

- `large` needs ~60–70 min for generation 1 > the ~56 min window, so for hours guided `large` could not
  write even its first checkpoint and restarted from gen 0 each cycle.
- Serial S11 `analyze` (days) likewise could not finish. medium/tiny were unaffected (fast, already
  complete).
- **Resolution:** after power stabilised (a >70 min window) all 5 guided `large` seeds wrote their first
  checkpoint and now accumulate progress. This is a hardware/facility fault to report to the machine's
  operators; it is not an experiment-design or software defect.

### §8.2 Checkpointing (corrected understanding)

Per-generation GA checkpointing was **already native and already enabled** in the engine for BOTH arms
(`ductile_backend.py` sets `checkpoint_path` and auto-loads it) — so enabling it creates **no arm
asymmetry**.

What actually caused gen-0 restarts was our own resume driver deleting the shape dir (checkpoint
included); that is fixed (preserve + `--resume`, verified on real GPU: kill mid-run → "Resuming
optimization from generation N" → completes with pop_size 512 and identical weights hash).

Record which seeds ACTUALLY resumed. ⚠️ **`checkpoint_resume_ledger.json` does not exist** —
re-checked 2026-08-13 across the repo and inside the container, no file of that name was ever created.
This line was an instruction to future-me that reads like a citation, which is worse than either: it
would let a reader believe the resume record had been kept. The deviation note
`agent_run/260809-s14-pershape-baseline/checkpoint_deviation.md` **does** exist and is the only written
record. **Which seeds actually resumed is therefore `NOT_EVALUATED` as a durable artifact**; it must be
reconstructed from run logs before closeout, or the report must say it was not tracked. The atomic checkpoint write is a monkey-patch in our runner, **not** an
engine edit (engine sha256 verified unchanged).

### §8.3 Medium remeasure ran on a dedicated card (GPU 5)

Not each seed's original search card (2,3,4,6,7 were occupied by the in-flight guided `large`). Sound
because the pre-registered requirement — G and F interleaved in the **same window on the same card** — is
preserved, and the final criterion is a **within-pair ratio**, so any card-level offset cancels. Also:
medium was remeasured **per shape** (as each pair completed) rather than per seed. Recorded in
`medium_remeasure_deviation.md`.


### §8.4 Remeasure validation fix (`DEVIATION-REMEASURE-STOPLINE-20260812`)

`remeasure_interleaved_champion.py` (our run-root script, **not** sealed code and **not** Lock A) asserted
that "reached the `n_gen=30` horizon" and "the log contains a native early-stop line" were mutually
exclusive. They are not: Ductile keeps `period: 5` early stop **alongside** the `n_gen: 30` cap
(`ductile/config/defaults.yaml`), so the stop criterion can fire exactly on the final generation.

Three large/tiny remeasures were rejected by this guard on design-conformant runs (`generations_run=30`
with one stop line): seeds 24002 (large, tiny) and 24005 (large). A secondary effect then blocked all
retries — the first failure wrote a `champion_interleaved_status.json` FAIL record, and the script's
"artifact already exists" guard rejected every subsequent attempt (seed 24005 large: 7 retries between
00:37 and 01:45 all died on the stale file, not on the original bug).

Fix (measurement logic unchanged; only the pre-flight assertion):

- the guard now checks the invariants that actually matter — **at most one** stop line, and the run must
  **not exceed** generation 30 — instead of forbidding the boundary case;
- the artifact now records `stopped_at_horizon` so the boundary case is auditable, and
  `termination_reason` states both the horizon and the coincident early stop;
- script sha256 `f2d11974…` → `040db9cd5978f1b528f1acf8cf3460366f0c4c761b2443163be46bc69dc82b95`;

> **HASH CHAIN COMPLETED 2026-08-13.** The file's current sha256 is
> `5da5a7a27581af55…`, which matches **neither** hash above — the record stopped at the 08-12 fix while
> the script was edited three more times afterwards. Those edits, all to argument handling and
> pre-flight validation and **none to measurement logic**, are:
> (i) `--stage-variant {capped,native}` added so the native runs resolve their own stage roots
> (defaults to `capped`, so prior invocations are unaffected);
> (ii) `--gpu-uuid-override` ported in from the `__gpu5deviation` copy, so the idle-card deviation
> runs through the same script instead of a fork;
> (iii) `parse_ga_stats` no longer requires the GA log to begin at generation 1 — on a resumed run the
> log is a *suffix*, so the contiguity check now anchors on the log's own first generation, and the
> caller separately requires the **trajectory** to be complete `1..N` and the log to be a suffix of it,
> comparing `n_evals` element-wise on the overlap and printing `RESUMED_RUN_PARTIAL_LOG`.
>
> Leaving this gap unrecorded would have meant a measurement script whose provenance chain does not
> reach the artifacts it produced. Any future edit must extend this chain in the same place.
- the three FAIL records were moved (user-authorised) to
  `quarantine/stopline_bug_20260812/` with a README stating the cause; no successful artifact was
  overwritten (none existed in those directories).

All five large remeasures completed after the fix. The interleave start-arm is a deterministic per-shape
counterbalance — `START_ARM = {medium: G, large: F, tiny: G}` — so large starting on F is by design, not a
deviation.

---

## §9 `PENDING_HUMAN_DECISION` — disposition of the medium remeasure measurement defect

> **This section is a MIRROR, not the record.** The authority is
> `s14-stage1-full-ga-outcome-design.md` **§13** (added 2026-08-13). Nothing here is approved. Until the
> owner rules, the pre-registered estimator and gates in that design's §10.2 / §10.4 stand unchanged, and
> **no analysis, label, or claim may be altered on the strength of this section.** Read it as "what is
> being proposed and why", never as "what was decided".
>
> **Provenance.** Produced by the `design-discussion` protocol: two independent reviewers in fresh
> threads, given an identical initial prompt containing no coordinator preference; two rounds of
> cross-examination; one evidence-backed final round. **Both returned `AGREE` with no preserved
> dissent.** ~43 of the 60 permitted agent wall-minutes. Every load-bearing fact was re-verified by the
> coordinator against artifacts.

### §9.1 The framing fact — this decision cannot change any conclusion

Read this before the rest, because it determines how everything below should be weighted.

The per-shape gate is a **conjunction of four sub-criteria**, each needing ≥4/5 seeds. It has **already
failed on three of them** — and those three are read from the GA trajectory, never from the remeasure,
so contamination cannot reach them:

| shape | Gen0 | gen-10 | AUC | required |
|---|---:|---:|---:|---|
| medium | 3/5 | 3/5 | 3/5 | ≥4/5 |
| large | **1/5** | **2/5** | 3/5 | ≥4/5 |

~~And recomputing with `max` instead of `median` changes no directional count for any shape in any
campaign.~~ **RETRACTED 2026-08-13 — this claim is FALSE, and it was the sole admissibility basis for
reporting a `max` row at all.** Recomputed from `remeasure.{G,F}` across all four medium datasets:

| dataset | median pos / non-reg | max pos / non-reg | |
|---|---|---|---|
| capped C1 | 2/5, 3/5 | 2/5, 3/5 | invariant |
| capped C2 | 3/5, 3/5 | 2/5, 3/5 | moves **against** F |
| native C1 | 3/5, **3/5** | 3/5, **4/5** | **crosses ≥4/5 toward F** |
| native C2 | 2/5, **3/5** | 2/5, **4/5** | **crosses ≥4/5 toward F** |

The native non-regression threshold `e^{−η}` is **pre-registered at design §12.3**. So `max` is inert on
four datasets, unfavourable on one, and crosses a pre-registered ≥4/5 line toward the treated arm on
**two**. Full treatment, including the mechanism of the crossing and the resulting publication ban:
**design §14 / §9.5 below.**

**So every decision in §13 is a question about the honesty of the record, not about the result.** That
framing must appear in any amendment — it is what turns a post-hoc change from suspicious into auditable.

### §9.2 The three decisions

**D1 — Estimator: keep the pre-registered median-of-7 for all three shapes.**
~~`max` appears only as a clearly-labelled sensitivity row, applied identically to all three shapes,
always accompanied by the invariance proof and its two known failure modes.~~ **SUPERSEDED 2026-08-13 by
§9.5 / design §14: there is no invariance proof — the claim it rested on is false — and `max` is now
barred from every acceptance and sensitivity table.** Rejected: promoting `max` to primary
(buys no change in conclusion, is post-hoc, and favours the treated arm — governance §4 forces a
successor; and there is a **counterexample**: capped campaign-1 seed 24005 arm F is contaminated in
**all 7** repeats, so `max` returns 10,535 against the same config's clean 13,407, **under-recovering
21.4 %** — which also refutes both "no arm has all 7 dropped" and the i.i.d. `0.48⁷ = 0.6 %` arithmetic,
since repeats inside one window are **power-governor-correlated, not independent**). Also rejected:
a clean-mode mean (reviewer B proposed it, then withdrew it after verifying it moves campaign-1
non-regression 3/5 → 4/5 and positive 2/5 → 3/5, destroying its own admissibility argument). B's
"≥3 clean repeats" rule is **retained as a validity classifier**, not an estimator; applied to campaign 1
it flags seed 24004 arm G and seed 24005 arm F as unrecoverable by any re-analysis.

**Campaign of record = campaign 1.** Campaign 2 overwrote campaign 1 **in place, after unblinding**, on
2026-08-12 14:01–14:04Z, and is **more favourable to the treated arm** (median F/G 1.0274, 3/5 vs C1's
0.9971, 2/5). C2 is a post-hoc diagnostic replication. Both are reported; neither produces a tier; they
**must not be averaged, and neither may be selected over the other.** ⚠️ **Live hazard (resolved 2026-08-13):**
`analyze_medium.py` read the canonical path, so running it reported C2 with nothing in its output saying
so. It now **requires** an explicit `--campaign {1,2}`, refuses to run without one, neither defaults nor
averages, and prints the resolved path in its header.

> **⚠️ CORRECTION 2026-08-13 — the same overwrite happened to `native`, and had not been recorded.**
> `[CODE AUDIT]` the native medium canonical artifacts were overwritten in place at **14:05:07–14:08:18Z**
> on 2026-08-12 (file mtimes). `superseded_*` markers exist only on seeds 24001 (1) and 24005 (2);
> **seeds 24002 / 24003 / 24004 have none** — and those markers are earlier retry debris, not campaign
> markers. An earlier draft cited `stage5_native_baseline/seed_24005/medium/` as the contrasting case
> that *did* leave a trace; that reading was wrong. Both P0 levels share one untracked-overwrite problem.
>
> | campaign | median F/G | per-seed F/G | positive (`ratio > 1`) | **positive (registered `> 1+δ_s`)** | non-regression |
> |---|---:|---|---:|---:|---:|
> | native C1 | **1.1391** | 0.4865 / 2.2663 / 0.3735 / 1.1391 / 1.9725 | 3/5 | **3/5** | 3/5 |
> | native C2 | **1.0041** | 1.0041 / 0.8256 / 1.0246 / 0.7029 / 1.0537 | 3/5 | **2/5** | 3/5 |
>
> **⚠ CORRECTED 2026-08-13 (second pass).** The first version of this table's "positive" column used
> `ratio > 1`, which is **not** the registered criterion. §10.2 defines improvement as `F/G > 1 + δ_s`
> (`δ_s = 0.004204159905590865`, threshold 1.0042042). The two agree on native C1 (3/5) but **differ on
> native C2: the registered count is 2/5, not 3/5**, entirely because seed 24001's ratio of 1.004079
> **misses the threshold by 0.0125 percentage points**. Authoritative source: the flag the measurement
> script itself recorded, `stage5_native_baseline/seed_*/medium/champion_interleaved.json →
> F_over_G_gt_one_plus_delta_s` = `False, False, True, False, True`. **Always name the criterion when
> quoting a "positive" count**, or this table reads as contradicting the artifact.
>
> That a pre-registered criterion turns on 0.0125 pp is itself a second, independent demonstration that
> `η_medium = 0.42 %` is too tight for the quantity it gates (the first is in §3.8.1).
>
> **Directional counts are identical (3/5, 3/5), so nothing downstream moves.** Two things must still be
> booked: C1's per-seed spread runs 0.37× to 2.27×, the same bimodal signature, so native's endpoints are
> `NOT_EVALUATED / instrument-invalid` alongside capped's; and unlike capped, **here the more favourable
> campaign is C1, not C2** — so "the overwrite consistently favoured the treated arm" is **not** a
> supportable statement and must not be written.
>
> *Source: `[CODE AUDIT]` `medium_recheck_control/native/seed_*/preserved_campaign1_20260812T135613Z/`
> vs `stage5_native_baseline/seed_*/medium/champion_interleaved.json`; S14 design §13.3.*

medium's final-champion and non-regression endpoints take a third state —
**`NOT_EVALUATED / instrument-invalid`** — in both campaigns. Neither pass nor fail.

**The real fix is the instrument, not the statistic:** register `MEASUREMENT-WARMUP-AMENDMENT` (Layer A,
R3 authority) redefining warm-up from a **count** to a **wall-clock time ≥ 50 ms**, uniformly across all
three shapes, **before execution**, with a prior commitment to publish old and new side by side. This is
**conditional** — see the RBS caveat in §7.1b — and gated on the untried **5,136 warm-ups at the pinned
RBS = 4096** feasibility probe.

**D2 — Margin: the sealed pinned `η_s` keeps governing, but must be fully disclosed.**
Rejected: recomputing η from the remeasures themselves — it is **circular** (the same repeats being gated
set the gate), and it is **falsified by tiny's null control**: under the empirical margin a
**byte-identical, zero-treatment** control is scored **3/5 regressed**. A margin that calls a known zero
a regression cannot replace one that does not. But all three pins are **accidents, not noise models**
(see the table in §7.1a as corrected), so both margins must be reported for all three shapes, with the
explicit statement that **on medium, keeping the pin is not the conservative choice** — it is ~30× tighter
than the observed null spread, making it a governance decision rather than a safety margin. And **η is
the wrong scale**: it measures within-window repeatability of *one* config, while the estimand is a ratio
of *two different champions*. New: tiny's null envelope is offered as a **reference envelope** for large
(every large seed's |ln F/G| ≤ 0.0749 sits inside tiny's zero-treatment envelope, max 0.1247) — a
reference envelope **never a threshold**, and conservative because large is the flattest shape
(champion-level spread: large 1.129, tiny 1.182, medium 1.222).

> **WHICH STATISTIC — disambiguated 2026-08-13.** Those three figures are spans of **`best_fitness`**
> (`optimization_result.json`, max/min over the shape's 10 arms): `[CODE AUDIT]` large **1.1294**,
> tiny **1.1823**, medium **1.2218**. The span of **remeasure medians** is a different and slightly
> tighter statistic: large **1.1249**, tiny **1.1705**, medium **1.2205**. Ordering and conclusion are
> identical under both, so nothing downstream moves — but two independent readers each re-derived the
> remeasure-median figures and reported them as a discrepancy against the design, so the statistic is
> now named. The same ambiguity affects tiny's "champion range 1.18×" in §9.2 and design §13.5: that
> is the `best_fitness` span 1.1823; the remeasure-median span is 1.1705.

**D3 — Per-shape claim ladder.** See the table in §4 as it will be amended if approved; in brief —
medium: gate **not met**, endpoints `NOT_EVALUATED / instrument-invalid`, full defect disclosure, and
**no** non-regression pass, improvement, or derived tier. large: gate **not met** (1/5, 2/5, 3/5, 3/5);
the 5/5 non-regression is reportable **only as one sub-criterion, never quoted alone**, with disclosure
that it is 3/5 under the within-window margin and that `η_large` rests on pilot anchors the champion
remeasure does not reproduce; improvement 0/5. tiny: dual-track — guidance question
`not evaluated / not activated` (0/27 genes) with `NOT_EVALUATED ≠ no effect`, plus its role as the
accidental null control; its pinned margin is **structurally vacuous**. Combined: the corrected sparse
capped prior **did not meet** the pre-registered gate on either confirmatory shape — and *not* "no
effect", no aggregate rescue, no generalisation or deployment wording. **Conditional Arm S does not
trigger** (§10.2 requires a confirmatory shape to pass); physics-direction attribution defers to S20.

Where a pre-registered prediction is reported but its instrument is in doubt, **four rows, never merged**:
(i) the prediction verbatim with its registration date; (ii) the analysis computed exactly as
pre-registered, unaltered; (iii) the instrument verdict, its evidence, and its discovery date **relative
to unblinding**; (iv) any repaired estimate, explicitly post-hoc. **(ii) is never overwritten by (iv).**

### §9.3 Nine items awaiting the owner

| # | decision | consequence if deferred |
|---|---|---|
| 1 | ~~**Run the ~10-minute clock pin**~~ **DOWNGRADED 2026-08-13 — no longer recommended as the priority.** A direct 1 kHz clock trace has since **disconfirmed** the clock account (§7.1b), so a pin would test a disfavoured hypothesis; and `--setperflevel high` demonstrably does not take effect here, so a real pin needs **write access to the card** (`pp_od_clk_voltage` / `amd-smi`) — a governance escalation, not a ten-minute `sudo` task. The open mechanism question is now better served by items 1–2 of §13.7 and by the untried 5,136 @ RBS-4096 probe. | mechanism stays `NOT_EVALUATED`; but note the *repair* path (§9.2 D1) does **not** depend on knowing the cause |
| 2 | Approve `MEASUREMENT-WARMUP-AMENDMENT`, **conditional** on the 5,136 @ RBS-4096 probe | no repaired medium remeasure is possible |
| 3 | Ratify **campaign 1 as the measurement of record**, and file the operational-correction record for the untracked in-place overwrite | `analyze_medium.py` keeps reporting the more favourable C2 |
| 4 | Confirm **median-of-7 stands** (D1) | estimator ambiguity persists into the report |
| 5 | Confirm **pinned η_s governs** (D2), with dual-margin disclosure | gate arithmetic is unfixed |
| 6 | Approve the **per-shape claim ladder** (D3) | §4 cannot be finalised |
| 7 | Approve the **A/A cross-window experiment** (~50 GPU-minutes, interruptible per window) | no cross-window repeatability data exists for any shape; within-window η stays a bound of unknown tightness |
| 8 | Approve the **record corrections** in §13.6 (retractions, arm-asymmetry, §12.2(B)2 rationale void) | the index and the root-cause memo carry known-wrong statements |
| 9 | Confirm **medium's endpoints as `NOT_EVALUATED / instrument-invalid`** rather than fail | medium risks being reported as a failed test rather than an invalid one |

### §9.4 Residual uncertainty (to be reported, not resolved)

- **The mechanism behind the warm-up correlation is `NOT_EVALUATED`.** *(Rewritten 2026-08-13; this
  bullet previously read that the clock mechanism was "inferred … no direct clock-pin evidence exists".)*
  A direct 1 kHz clock trace during a live remeasure **disconfirmed** the clock account — negative
  clock↔throughput correlation, dropouts at a higher median clock than clean repeats, every repeat
  reaching 1512–2065 MHz (§7.1b). The **correlation with warm-up duration stands**; its cause does not.
  Surviving untested candidates: XCD/CU assignment, MALL/L2 residency, GSU-4 workspace contention, and
  whatever explains a slower kernel at a higher clock. The trace's ~8 ms resolution cannot see inside the
  3.2 ms warm-up, so the clock story is disfavoured rather than excluded.
- **No cross-window or cross-day repeatability data exists for any shape.** Within-window η is a **lower
  bound** of unknown tightness.
- tiny's single dropout (repeat 7 of 7, at 34.7 s into a 37.8 s window) is `NOT_EVALUATED`, and tiny's
  measured invariance to warm-up length argues against it *(reworded 2026-08-13: this previously read
  "medium's mechanism argues against it", and medium's mechanism is precisely what was retracted)*.
- Whether in-search contamination is arm-symmetric: `NOT_EVALUATED`, and **not retrospectively checkable**
  (per-generation benchmark CSVs are not retained).
- Why campaign 1 is 1.7× dirtier than campaign 2: unexplained.
- The cross-campaign reproducibility contrast rests on **n = 2** campaigns.

*Source: `s14-stage1-full-ga-outcome-design.md` §13 (§13.1–§13.10), 2026-08-13. Mirror only — amend the
authority first.*

### §9.5 `PENDING_HUMAN_DECISION` — peak-of-7 as medium's endpoint: the "capability" argument

> **MIRROR, not the record.** Authority is `s14-stage1-full-ga-outcome-design.md` **§14**
> (`CAPABILITY-ENDPOINT-PACKET-20260813`, added 2026-08-13). Nothing here is approved; §10.2 / §10.4 stand
> unchanged until the owner rules.
>
> **Provenance.** `design-discussion`, second session: two independent reviewers, fresh threads, identical
> prompt containing no coordinator preference; one cross-examination round; one evidence-backed final
> round. **Both `AGREE`, no preserved dissent.** ~27 of 60 permitted agent wall-minutes. Every
> load-bearing fact re-verified by the coordinator, who **overturned reviewer arithmetic twice**.

**The question — and why it is not the one §9.2 D1 already rejected.** D1 rejected "`max` is a better
*estimator*". The owner raised a **capability** argument instead: contamination is one-sided downward, so
a repeat landing in the clean mode is a genuine observation of what the config *can* do; if medium is
seen reaching ~13,500 GFLOP/s, it can reach it. That is a claim about a single arm, not about an
estimator, so it was reviewed independently.

**Verdict: rejected — but half the premise is correct and must be conceded, not argued away.**
Peak-of-7 genuinely *is* a far better recoverer of a config's clean level than median-of-7 (native C1
max-ratios compress to 0.889–1.068 against medians spanning 0.37–2.27). It fails because **the endpoint
is not a level — it is a ratio judged against a pre-registered margin.** Three independent defeaters:

| # | type | what it says | magnitude |
|---|---|---|---|
| 1 | **bias**, specific to `max` | the clean mode is itself two-sided noise, so max-of-7 overstates even at **zero** contamination — and because within-window clean counts differ between arms by −3 to +3, the overstatement is **arm-differential** with unknown sign | +0.51 % vs a **+0.42 %** improvement threshold; differential +0.30 %, ≈71 % of the decision margin |
| 2 | **variance**, estimator-agnostic | between-window level drift, present in windows that are not all-contaminated | **0.5–2.8 × η_medium** |
| 3 | **unfalsifiability**, structural | the clean-mode calibration that would validate a peak margin **cannot be obtained** at the pinned estimand | see below |

Defeater 2 indicts the **one-window-per-seed design**, not the statistic, and would survive the
contamination being fixed tomorrow. Defeater 1 is the only one that indicts `max` specifically. **Neither
subsumes the other:** without 2 nothing explains why no conclusion is available; without 1 the native
4/5 (below) reads as a legitimate alternative analysis rather than a diagnosable artefact.

**Why the repair is structurally impossible, not merely unattempted.** The 5,136-warm-ups @ RBS-4096
probe crashed on all three seeds (`Insufficient rotating buffer size.`, exit 134). `[CODE AUDIT]` The
cause is a deterministic **signed-32-bit overflow**: `DataInitialization.cpp:3213` computes
`rotatingNum × rotatingSize` in `int32_t`, and `1,312,256 × 3,272 = 4,293,701,632` wraps to
**−1,265,664** — matching the log digit-for-digit. Overflow threshold `rotatingNum ≥ 1637`, so
**`num-warmups ≥ 1638` always crashes** at this working set, capping warm-up at ~1,637 enqueues
≈ **16–19 ms** against the sweep's **51 ms** knee. **The pinned estimand therefore admits no clean
measurement at all.** This satisfies design §13.8's crash branch and **closes §13.7 item 2**; a fix needs
a client code change (`int32` → `int64`), which is a new estimand and a successor question, not an
amendment. Note the inference runs *against* salvage: a statistic whose validating measurement is
unobtainable is unfalsifiable at the settings it is applied to.

**Publication rule — stricter than §9.2 D1.** **No `max` row in any acceptance or sensitivity table, for
any shape or variant.** `max` appears only inside the measurement-defect forensics, as evidence about the
instrument, and must carry inline: *under max-of-7 the native-medium non-regression sub-criterion reads
4/5 in both campaigns, crossing the pre-registered §12.3 threshold toward the treated arm — this movement
is why max is rejected, not a result.* Silent correction is not acceptable, because §9.1/§9.2 previously
asserted the opposite. The owner's capability observation is reported **descriptively** — "medium's
champions were directly observed at 11,977–15,067 GFLOP/s; the low mode is instrument contamination, not
configuration behaviour" — with no ratio, no gate, no tier.

**Mechanism of the crossing, which is what makes it diagnosable rather than a finding.** `max` does not
discover that F is non-inferior. It strips the downward contamination that had been pushing medians below
a floor set ~288× tighter than the observed dispersion, so nearly everything passes. The pass is
manufactured by an **extreme-value statistic judged against a margin derived from the dispersion of a
central statistic** — the §3.8.1 mismatch, realised.

**Further record corrections required (design §14.6).**

- §9.1 / §9.2's count-invariance claim is false — corrected above.
- The §13.3 native table's "positive" column did not name its criterion. It used `ratio > 1`; the
  registered rule is `> 1 + δ_s` (`δ_s = 0.004204159905590865`). They agree on native C1 (3/5) but **not
  on native C2: the registered count is 2/5**. Seed 24001's `ratio = 1.004079` **misses by 0.0125
  percentage points** — itself a second, independent demonstration that `η_medium` is too tight for what
  it gates (the first is §3.8.1).
- A **second** all-contaminated arm must be booked: capped seed 24004 arm F campaign 2 (85.7–89.4 %
  recovery depending on reference), alongside the known seed 24005 arm F campaign 1 (78.6 %).
- The between-window floor (0.5–2.8 × η_medium) joins §9.4, noting it rests on a single afternoon.
- The ladder's idle-gap trend (33 % → 52 %) is **not established** — adjusted z ≈ 1.40 after
  over-dispersion correction. It must not be cited as supporting the warm-up account.

**Acceptance / falsification.** Reopened by a cross-window A/A experiment showing the floor is materially
below `η_medium`, or by a 64-bit client patch yielding a demonstrably clean measurement at RBS 4096 —
either via a **successor**, not an amendment, since governance §4 is triggered independently by threshold,
measurement, comparability and claim changes regardless of directional favourability.

**Residual uncertainty.** Mechanism `NOT_EVALUATED`. Arm-symmetry `NOT_EVALUATED` and not retrospectively
checkable. True per-config ceilings unknown — every `max` is a **lower bound**. The floor rests on one
afternoon; no cross-day repeatability data exists for any shape. Two same-model fresh threads are
**process independence, not scientific replication**.

*Source: `s14-stage1-full-ga-outcome-design.md` §14 (§14.1–§14.8), 2026-08-13. Mirror only — amend the
authority first.*

---

*Maintenance: update §1 statuses and §7 result cells as capped G/F, 7× remeasure, conditional Arm S,
native-P0, and S11 closeout land. This index stays non-authority — mirror any material change back to the
cited authoritative doc first, and mirror structure/prose into `report-source-index.zh-Hant.md`.*
