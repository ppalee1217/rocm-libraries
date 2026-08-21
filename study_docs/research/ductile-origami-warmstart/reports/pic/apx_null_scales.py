"""APPENDIX -- one effect, two null scales, and WHY they differ (medium capped, 24004).

Left panel (the mechanism).  A 3 x 2 table of which kernel each arm actually
loads.  This is the whole point of the page and the old version of the figure
did not show it at all: the G/G' null never loads the guided kernel, so it
cannot see that kernel's noise.  It under-measures by construction, not by
chance.  The table is aligned row-for-row with the distributions on its right,
so "the G/G' row has no orange in it" is readable at a glance.

Right panel (the result).  Three distributions of per-window ln(F/G) on one
shared axis --
  * the real contrast   (C03_ + C03CONF_, 24 windows)
  * the F/F' null       (N7b_FFNULL_, both arms load the guided kernel)
  * the G/G' null       (N7_GVSG_,    both arms load the baseline kernel)
Each per-window value is recomputed here from the raw paired arm measurements
(median over the 7 repeats in the window), not read from a summary field.
The single vertical line is the measured effect; it crosses all three rows.

Bottom strip (the co-headline, and it gets its own panel title).  tiny's two
arms are byte-identical, so its true effect is exactly zero -- and it still
measures a 0.1247 envelope.  That is why no replacement threshold was ever
registered: the admissible interval is empty.

Run on the HOST (matplotlib 3.8.2). Idempotent: no timestamps, no randomness.
"""
from __future__ import annotations

import math
from statistics import median, stdev, mean

import numpy as np

import common
from common import ARM_COLOR, C_GREY, C_PURPLE

SEED = 24004
INK = "#2B2B2B"
C_EFFECT = C_PURPLE   # the effect line: not arm-coded, so not an arm colour


# --------------------------------------------------------------------------
# data: per-window ln(F/G) from the raw paired repeats
# --------------------------------------------------------------------------
def window_ln(cell, seed=SEED):
    """[ln(median_F / median_G)] per measurement window, sorted by window."""
    rows = common.cell_repeats(cell, seed)
    by_win = {}
    for r in rows:
        by_win.setdefault(r["window"], {"F": [], "G": []})[r["arm"]].append(r["gflops"])
    return [math.log(median(by_win[w]["F"]) / median(by_win[w]["G"]))
            for w in sorted(by_win)]


REAL = window_ln("C03_") + window_ln("C03CONF_")   # the two repaired capped cells
FF = window_ln("N7b_FFNULL_")                      # F/F' null
GG = window_ln("N7_GVSG_")                         # G/G' null

EFFECT = mean(REAL)
SD = {"real": stdev(REAL), "ff": stdev(FF), "gg": stdev(GG)}
Z_FF = EFFECT / SD["ff"]
Z_GG = EFFECT / SD["gg"]

# tiny: the two arms are byte-identical, so this is a zero-treatment envelope.
TINY = {s: common.canonical_ratio("tiny", s) for s in common.SEEDS}
TINY_LN = [math.log(TINY[s]) for s in common.SEEDS]
TINY_MAX = max(abs(x) for x in TINY_LN)
_TINY_DOC = [0.8828, 1.0350, 0.8841, 0.9953, 0.9690]   # the five documented ratios
_tiny_ok = all(abs(TINY[s] - v) < 5e-5 for s, v in zip(common.SEEDS, _TINY_DOC))

# (y, cell label, values, colour, effect/sd, first arm kernel, second arm kernel)
BASE, GUID = "baseline", "guided"
ROWS = [
    (2, "real contrast\nF vs G", "24 windows", REAL, INK, None, BASE, GUID),
    (1, "F/F′ null", "12 windows", FF, ARM_COLOR["F"], Z_FF, GUID, GUID),
    (0, "G/G′ null", "12 windows", GG, ARM_COLOR["G"], Z_GG, BASE, BASE),
]
KCOL = {BASE: ARM_COLOR["G"], GUID: ARM_COLOR["F"]}

XLIM = (-0.138, 0.138)   # symmetric about 0, and wide enough to show tiny's envelope
YLIM = (-0.72, 3.30)     # shared by the table and the distributions

# --------------------------------------------------------------------------
# figure: [mechanism table | distributions] over [ (blank) | tiny strip ]
# --------------------------------------------------------------------------
fig = common.plt.figure(figsize=(13.6, 7.4))
gs = fig.add_gridspec(2, 2, width_ratios=[1.00, 2.05],
                      height_ratios=[3.05, 1.00])
axk = fig.add_subplot(gs[0, 0])
ax = fig.add_subplot(gs[0, 1])
axt = fig.add_subplot(gs[1, 1], sharex=ax)
fig.subplots_adjust(left=0.030, right=0.985, top=0.850, bottom=0.150,
                    wspace=0.055, hspace=0.40)

ax.set_ylim(*YLIM)


def _yfrac(y0, y1):
    lo, hi = ax.get_ylim()
    return (y0 - lo) / (hi - lo), (y1 - lo) / (hi - lo)


def _stagger(vals, step=0.062):
    """Deterministic vertical spread: cycle offsets in value order."""
    order = np.argsort(vals, kind="stable")
    off = np.zeros(len(vals))
    for rank, idx in enumerate(order):
        off[idx] = ((rank % 5) - 2) * step
    return off


# =========================== the mechanism table ==========================
axk.set_xlim(0, 1)
axk.set_ylim(*YLIM)
axk.axis("off")

COL = {"cell": 0.015, "first": 0.505, "second": 0.815}
axk.text(COL["cell"], 3.02, "cell", ha="left", va="center", fontsize=11,
         weight="bold", color=C_GREY)
axk.text(COL["first"], 3.02, "first arm\nruns", ha="center", va="center",
         fontsize=11, weight="bold", color=C_GREY, linespacing=1.25)
axk.text(COL["second"], 3.02, "second arm\nruns", ha="center", va="center",
         fontsize=11, weight="bold", color=C_GREY, linespacing=1.25)
axk.plot([0.0, 1.0], [2.66, 2.66], color=C_GREY, lw=1.0, alpha=0.6)

for y, name, nwin, vals, colour, z, k1, k2 in ROWS:
    axk.text(COL["cell"], y + 0.10, name, ha="left", va="center", fontsize=12,
             color=INK, linespacing=1.25)
    axk.text(COL["cell"], y - 0.32, nwin, ha="left", va="center", fontsize=10,
             color=C_GREY)
    for cx, kern in ((COL["first"], k1), (COL["second"], k2)):
        axk.add_patch(common.plt.Rectangle(
            (cx - 0.145, y - 0.235), 0.29, 0.47, facecolor=KCOL[kern],
            alpha=0.20, edgecolor=KCOL[kern], lw=1.4, zorder=1))
        axk.text(cx, y, f"{kern}\nkernel", ha="center", va="center",
                 fontsize=11, weight="bold", color=KCOL[kern], zorder=2,
                 linespacing=1.20)
    axk.plot([0.0, 1.0], [y - 0.50, y - 0.50], color="#E4E4E4", lw=0.9,
             zorder=0)

axk.set_title("Why the two nulls disagree", fontsize=14.5, loc="left", pad=10)

# =========================== the distributions ============================
for y, name, nwin, vals, colour, z, k1, k2 in ROWS:
    # null band: +/-2 sd about the construction's true value, which is exactly 0
    if z is not None:
        f0, f1 = _yfrac(y - 0.44, y + 0.44)
        ax.axvspan(-2 * np.std(vals, ddof=1), 2 * np.std(vals, ddof=1),
                   ymin=f0, ymax=f1, color=colour, alpha=0.20, lw=0, zorder=1)
    ax.boxplot([vals], positions=[y], vert=False, widths=0.42,
               showfliers=False, whis=(0, 100), manage_ticks=False,
               medianprops=dict(color=colour, lw=2.4),
               boxprops=dict(color=colour, lw=1.5),
               whiskerprops=dict(color=colour, lw=1.2),
               capprops=dict(color=colour, lw=1.2), zorder=3)
    ax.scatter(vals, y + _stagger(vals), s=26, c=colour, alpha=0.85,
               edgecolors="white", linewidths=0.5, zorder=4)

ax.axvline(0.0, color=C_GREY, lw=1.0, zorder=2)
ax.axvline(EFFECT, color=C_EFFECT, lw=2.6, zorder=6,
           label="measured effect  ln(F/G) = %+.4f  (F/G = %.4f)"
                 % (EFFECT, math.exp(EFFECT)))

for y, name, nwin, vals, colour, z, k1, k2 in ROWS:
    if z is not None:
        ax.text(EFFECT + 0.005, y + 0.28, "effect = %.1f × sd" % z,
                ha="left", va="center", fontsize=12.5, weight="bold",
                color=colour)

# the sd goes INSIDE the axes, at its own row's left edge: as a y tick label it
# landed on top of the mechanism table's right-hand column.
ax.set_yticks([])
for (y, _n, _w, _v, _c, _z, _k1, _k2), k in zip(ROWS, ("real", "ff", "gg")):
    ax.text(XLIM[0] + 0.004, y + 0.30, "sd %.5f" % SD[k], ha="left",
            va="center", fontsize=11, color=C_GREY, zorder=5)
ax.set_xlim(*XLIM)
ax.set_title("medium capped, seed 24004 — the same effect against each null",
             fontsize=14.5, loc="left", pad=10)
ax.legend(fontsize=11, loc="upper left", framealpha=0.95,
          bbox_to_anchor=(0.015, 0.995))
common.plt.setp(ax.get_xticklabels(), visible=False)

# the one sentence the table exists to support
fig.text(0.030, 0.036,
         "G/G′ never loads the guided kernel, so it cannot see that kernel's "
         "noise — it under-measures by construction, not by chance.",
         ha="left", va="bottom", fontsize=12.5, color=INK)

# =========================== tiny: its own panel ==========================
axt.axvspan(-TINY_MAX, TINY_MAX, color=C_GREY, alpha=0.16, lw=0, zorder=1)
axt.axvline(0.0, color=C_GREY, lw=1.0, zorder=2)
axt.axvline(EFFECT, color=C_EFFECT, lw=2.6, alpha=0.55, zorder=3)
axt.scatter(TINY_LN, _stagger(TINY_LN, step=0.13), s=48, c=INK, marker="D",
            edgecolors="white", linewidths=0.7, zorder=5)
axt.text(0.0, 0.46, "true value = 0", ha="center", va="bottom", fontsize=11.5,
         color=INK)
axt.text(0.988, 0.93, "envelope: max |ln(F/G)| = %.4f" % TINY_MAX,
         transform=axt.transAxes, ha="right", va="top", fontsize=11,
         color=C_GREY)
axt.set_ylim(-0.78, 1.02)
axt.set_yticks([0])
axt.set_yticklabels(["5 seeds"], fontsize=11, color=C_GREY)
axt.tick_params(axis="y", length=0)
axt.set_xlabel("ln(F/G)")
axt.set_title("tiny — a known-zero effect, and the instrument still measures "
              "an envelope this wide",
              fontsize=14.5, loc="left", pad=8)

# tiny's row label, in the blank cell to its left
fig.text(0.030, 0.255, "tiny\nboth arms byte-identical", ha="left", va="top",
         fontsize=12, color=INK, linespacing=1.30)

fig.suptitle("Which null? — the same effect is 39.5× one and 3.0× the other",
             x=0.5, y=0.982, va="top", fontsize=18)

common.provenance(fig, "medium_pilot401 raw repeats: C03, C03CONF, N7b_FFNULL, "
                       "N7_GVSG (seed 24004) | stage3_baseline/*/tiny/"
                       "champion_interleaved.json")
common.save(fig, "apx_null_scales.png", tight=False)

# --------------------------------------------------------------------------
# stdout
# --------------------------------------------------------------------------
for name, vals in [("real contrast (C03_+C03CONF_)", REAL), ("F/F' null (N7b)", FF),
                   ("G/G' null (N7)", GG)]:
    print("%-30s n=%2d  mean %+.6f  sd %.6f  min %+.5f  max %+.5f"
          % (name, len(vals), mean(vals), stdev(vals), min(vals), max(vals)))
print("effect (mean of real contrast) = %+.6f   F/G = %.4f" % (EFFECT, math.exp(EFFECT)))
print("effect / sd(G/G') = %.2f x     effect / sd(F/F') = %.2f x" % (Z_GG, Z_FF))
print("sd(real) / sd(G/G') = %.2f x tighter" % (SD["real"] / SD["gg"]))
print("tiny F/G per seed: " + " ".join("%.4f" % TINY[s] for s in common.SEEDS)
      + "   matches documented five: %s" % _tiny_ok)
print("tiny ln(F/G):      " + " ".join("%+.5f" % x for x in TINY_LN)
      + "   max |ln| = %.4f" % TINY_MAX)
