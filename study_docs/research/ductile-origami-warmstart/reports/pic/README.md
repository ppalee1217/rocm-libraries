# Figures for the S14 closeout deck

Fifteen deck figures plus seven appendix figures. Every number in every figure is **computed from
an artifact at render time** — nothing is transcribed from a document.

`outline_compact.md` carries no source citations at all (it is generated from `outline.md`'s
"On the slide" blocks). **This file is where that traceability went.** Each figure also stamps a
short data-source tag in its own bottom-right corner, so it stays traceable if lifted out of the deck.

## 🔴 The retired metric

The per-shape noise constant that used to gate the fourth conjunct was **retired on 2026-08-14**
and, by owner ruling of 2026-08-18, retired material is **deleted, not annotated**. Two figures
existed only to display it and have been removed. Nothing in this directory — code, labels, titles,
comments, provenance strings, or this README — may reintroduce it, its values, its derived
multiples, or the paraphrases that restate it without naming it.

**The gate is a script, not a paragraph.** The forbidden pattern lives in exactly one place so that
documents can describe the rule without tripping it:

```sh
sh pic/check_retired.sh        # run from reports/ ; exit 0 = clean
```

It scans `outline.md`, `outline_compact.md`, `pic/README.md` and `pic/*.py`, and excludes itself.
Run it before shipping any revision of the deck.

## Running

Run on the **host**, not in the container — these are host paths, and container-created files come
out root-owned.

```sh
cd reports/pic
python3 p02_gate_matrix.py             # one figure
for f in p*.py apx_*.py; do python3 "$f"; done   # all of them
```

Scripts are **idempotent**: re-running overwrites the same `.png`, no timestamps, no randomness.
Re-running the whole set must leave every checksum unchanged.

`common.py` holds the shared style (Okabe-Ito colour-blind-safe palette) and all data loaders. Its
`traj` / `gen0` / `gen10` / `auc` helpers mirror `analyze_large.py:10-34`, so the figures score the
gate exactly the way the analysis does.

## Deck figures

| figure | page | what it shows |
|---|---|---|
| `p02_gate_matrix.png` | P2 | 4 blocks × 3 sub-criteria counts against the ≥4/5 line; capped banded as gate, native as addendum |
| `p04_population_decay.png` | P4 | measured population vs generation, both decay laws, capped and native |
| `p08_shape_regimes.png` | P8 | the three shapes by K, FLOPs and measured throughput; which quantity spans five orders |
| `p09_gene_sensitivity.png` | P9 | per-gene sensitivity for all 27 free genes across three shapes; activation 0 / 2 / 5 |
| `p10_weight_inversion.png` | P10 | prior → emitted weight → realised sampling probability, plus the un-inverted counterfactual |
| `p11_gen0_pools.png` | P11 | Gen0 at 512 vs 11,405, with decay curves and total evaluation spend |
| `p12_win_loss_per_seed.png` | P12 | **how much each seed won or lost by** — diverging bars, 3 gate criteria + final ratio banded separately |
| `p13_four_quantities.png` | P13 | the same comparison as raw GFLOP/s → `F/G` → `ln(F/G)` → against a null baseline |
| `p15_search_budget.png` | P15 | where the gains come from, where the budget goes, and that the searches had not converged |
| `p16_medium_three_states.png` | P16 | medium: trajectory criteria, then the same quantity on defective / repaired-capped / repaired-native instruments |
| `p16_evolution_medium.png` | P16 | medium: per-seed `ln(F_bsf/G_bsf)` vs cumulative evaluations, signed fill |
| `p17_centre_extreme.png` | P17 | Gen0 centre vs extreme slope chart at `P0 = 512` and `P0 = 11,405` |
| `p17_evolution_large.png` | P17 | large: same difference encoding as p16 |
| `p18_effect_vs_noise.png` | P18 | per-seed effect against that seed's **own** two nulls, drawn side by side; only what clears both is called |
| `p20_repair_dumbbell.png` | P20 | before/after twice over: panel 1 the per-seed cross-window sd of `ln(F/G)` on a log axis (19×–100× tighter), panel 2 the dropout rate for every measured cell |

## Appendix figures

`apx_auc_medium_capped.png` · `apx_auc_medium_native.png` · `apx_auc_large_capped.png` ·
`apx_auc_large_native.png` — five panels each, both arms' absolute best-so-far curves with the
signed area between them and the `B*` cutoff marked. Backup slides for AUC questions.

`apx_clock_disconfirmation.png` — the clock-ramp hypothesis we proposed for P19's defect and then
disconfirmed ourselves: per-repeat max sclk against throughput over 42 traced repeats, Spearman
−0.045, p ≈ 0.78. Backup slide for P19. It imports its loaders from `p19_defect_storyboard.py`.

`p19_defect_storyboard.png` — **P19 carries no figure on the slide**, so this is a backup too: one
window's 14 bimodal repeats with **dropout** defined on the 0.95 line, then the warm-up sweep with
all seven points including the turn-up above the knee.

`apx_null_scales.png` — which kernel each arm loads, then one seed / one effect / two nulls —
39.5× against one, 3.0× against the other, plus tiny's known-zero envelope. Backup slide for P21's
fifth insight.

## Pages with no generated figure

P1, P3, P6, P7, P14, P19 and P21 are conceptual or narrative pages (status strips, input-format cards, inventory
tables, a window timeline; P19 and P21 are prose, each with a backup figure). They are described in one line in `outline_compact.md`
and drawn in the slide tool.

**P5 is the exception:** its end-to-end pipeline flowchart is carried as a `mermaid` block inside
`outline.md` / `outline_compact.md` rather than as a rendered `.png`, so the slide is built by
pasting the diagram source, not an image from this directory.

## Ground truth for spot-checks

If a figure disagrees with any of these, the figure is wrong:

- **gate counts** — medium capped `3/5 3/5 3/5`, large capped `1/5 2/5 3/5`,
  medium native `2/5 1/5 3/5`, large native `3/5 1/5 2/5`
- **median `F/G`** — medium capped `1.0135`, medium native `1.0036`,
  large capped `1.0006`, large native `0.9970`
- **dropout** — before `45.71 % / 24.29 %` (capped C1/C2), `47.14 %` (native C1);
  after `7.50 % / 6.43 %` (capped), `6.55 %` (native); campaign-scale `10.36 % / 8.04 %`
- **single-variable controls** — buffer size only (cells `A` → `B`, 328/840 → 341/840)
  `39.05 % → 40.60 %`; warm-up only (`w321_sleep50` → `w1400_sleep50`, 21/50 → 0/50)
  `42.00 % → 0.00 %`
- **seed 24004, medium capped** — real-contrast sd `0.01796`, F/F′ `0.02071`, G/G′ `0.00155`;
  effect `39.5×` one null and `3.0×` the other
- **Gen0 centre / extreme, large** — capped `1.0197 (4/5)` / `0.9719 (1/5)`;
  native centre `1.0208 (5/5)`, native extreme `1.0023 (3/5)`
- **search budget** — Gen0→gen10 `+22.8 / +25.6 / +20.9 / +11.8 %`;
  gen10→end `+4.9 / +2.7 / +3.8 / +2.9 %`; Gen0 share `4.9 / 5.3 / 35.7 / 33.9 %`
- **power** — `≥4/5` fires `6/32 = 18.75 %` under a coin-flip null; 80 % power needs `p ≈ 0.83`
- **Spearman, clock vs throughput** — `−0.045`, p ≈ `0.78`, n = 42
- **weight inversion** — max deviation intended vs realised probability `1.5e-08`

## Corrections found while building these figures

Each contradicts something a source document said; the figures follow the artifact.

1. **The warm-up sweep has seven points, not five**, and turns back up to **4 %** at 205 ms. It
   lives in `medium_mechanism_probe_summary.json`, not the similarly-named ratio probe.
2. **The 1 kHz clock telemetry is in `medium_clockladder/capped/seed_*/s1_trace/`** — the other
   trace samples at ~96 Hz whole-run. The null reproduces only against per-repeat **max** sclk;
   the alternative estimators reproduce the two already-retired figures, so it self-validates.
3. **The remeasure window is ~22 s, not ~27 s** (measured 21.5–25.4 s across the five seeds).
4. **The law-1 → law-2 crossover is arm-identical on large only.** On capped medium the arms differ
   on 4/5 seeds by up to 2 generations. `outline.md` had generalised a large-only result.
5. **"Warm-up only: 42 % → 4 %" was not single-variable** — `sleep-percent` changed 50→0 as well.
   The genuine matched pair is `w321_sleep50` → `w1400_sleep50`, i.e. **42 % → 0 %**.
6. **K spans 3.2 orders, not five.** The five orders are in measured throughput.
7. 🔴 **Native large's AUC cell is decided by an integration-start artifact.** `auc()` starts each
   arm's integral at that arm's *own* Gen0 completion point, and the arms do not finish Gen0 at the
   same evaluation count. On seed 24001 arm G's integral covers **17 evaluations more** than arm
   F's, which is what makes the seed score AUC-negative. Starting both at a common lower bound
   gives native large **3/5 rather than 2/5**. No other cell in any block changes, and the verdict
   is unaffected (both below 4/5). The deck reports the pre-registered analysis as implemented and
   discloses this in P17's notes.
8. **`B*` truncation discards 20–24 % of one arm's evaluations** on large capped seeds
   24003/24004/24005, because the arms early-stop at different generations.
