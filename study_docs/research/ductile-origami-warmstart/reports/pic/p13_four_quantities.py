"""P13 -- one comparison, four ways of reporting it.

Medium, capped, five seeds. Every panel shows the SAME five paired
measurements; only the reported quantity changes.

  1. raw GFLOP/s per arm       -- answers "how fast", not "did F beat G", and is
                                  not comparable across shapes at all
  2. F/G per seed              -- comparable, but multiplicative, so an
                                  arithmetic mean over it is not a central tendency
  3. ln(F/G) per seed          -- additive and symmetric; its mean exponentiates
                                  to the geometric mean of the ratios
  4. ln(F/G) against the null  -- how big the effect is in units of the
                                  instrument's own measured noise

The load-bearing content is the reversal between 2 and 3. One seed lands at
2.12x; the arithmetic mean of the five raw ratios is dragged to 1.0499, which
would be reported as a +5.0 % gain. The mean log-ratio is -0.1130 -- geometric
mean 0.893, a -10.7 % regression. Same five numbers, opposite sign. That is why
the study reports log-ratios.

Panel 4's baseline is a null cell's own sd (N7_GVSG_, both arms the baseline
kernel; N7b_FFNULL_, both arms the guided kernel), taken conservatively as the
worst seed's sample_sd in each cell.

Run on the HOST (matplotlib 3.8.2). Idempotent: no timestamps, no randomness.
"""
from __future__ import annotations

import math
from statistics import mean

import numpy as np
from matplotlib.transforms import Bbox

import common
from common import ARM_COLOR, C_GREY, C_PURPLE, C_RED, C_SKY

INK = "#2B2B2B"
SHAPE = "medium"
SEEDS = common.SEEDS
ARM_DIR = "stage3_baseline"

# --------------------------------------------------------------------------
# data -- the same five paired measurements, read once
# --------------------------------------------------------------------------
RATIO = {s: common.canonical_ratio(SHAPE, s, ARM_DIR) for s in SEEDS}
LN = {s: math.log(RATIO[s]) for s in SEEDS}
RAW = {s: common.champion(
    f"{common.BASE}/{ARM_DIR}/seed_{s}/{SHAPE}/champion_interleaved.json"
)["median_gflops"] for s in SEEDS}

ARITH = mean(RATIO[s] for s in SEEDS)          # the wrong central tendency
MEAN_LN = mean(LN[s] for s in SEEDS)           # the right one
GEO = math.exp(MEAN_LN)
DRAGGER = max(SEEDS, key=lambda s: RATIO[s])   # the 2.12x seed

# raw medians on the other two shapes, to show raw GFLOP/s is shape-scoped
OTHER_RAW = {
    sh: [common.champion(
        f"{common.BASE}/{ARM_DIR}/seed_{s}/{sh}/champion_interleaved.json"
    )["median_gflops"]["G"] for s in SEEDS]
    for sh in ("tiny", "medium", "large")
}

# null-cell noise baseline: the worst seed's sd in each null construction
NULL = {}
for cell, label in (("N7_GVSG_", "G/G' null"), ("N7b_FFNULL_", "F/F' null")):
    per = common.cell_per_seed(cell)
    NULL[cell] = {"label": label,
                  "sd_max": max(v["sample_sd"] for v in per.values()),
                  "sd_med": float(np.median([v["sample_sd"] for v in per.values()])),
                  "n": len(per)}
BASE_SD = max(v["sd_max"] for v in NULL.values())   # most conservative null sd

X = np.arange(len(SEEDS))

# --------------------------------------------------------------------------
# figure
# --------------------------------------------------------------------------
fig, ((ax1, ax2), (ax3, ax4)) = common.new_fig(2, 2, figsize=(13.6, 8.6))

# ---- 1. raw GFLOP/s -------------------------------------------------------
w = 0.38
ax1.bar(X - w / 2, [RAW[s]["G"] for s in SEEDS], w, color=ARM_COLOR["G"],
        label="G (baseline)", zorder=3)
ax1.bar(X + w / 2, [RAW[s]["F"] for s in SEEDS], w, color=ARM_COLOR["F"],
        label="F (guided)", zorder=3)
ax1.set_xticks(X)
ax1.set_xticklabels([str(s) for s in SEEDS], fontsize=11.5)
ax1.set_ylabel("median GFLOP/s", fontsize=13)
ax1.set_ylim(0, max(max(v.values()) for v in RAW.values()) * 1.78)
ax1.set_title("1.  raw GFLOP/s per arm\n“how fast”, not “did F beat G”",
              fontsize=14, pad=8)
ax1.legend(fontsize=11.5, loc="upper left", ncol=2, framealpha=0.95)
ax1.text(0.5, 0.855,
         "and not comparable across shapes:\nG median ≈ %.1f (tiny), %s (medium), "
         "%s (large)"
         % (float(np.median(OTHER_RAW["tiny"])),
            "{:,.0f}".format(float(np.median(OTHER_RAW["medium"]))),
            "{:,.0f}".format(float(np.median(OTHER_RAW["large"])))),
         transform=ax1.transAxes, ha="center", va="top", fontsize=11,
         color=C_GREY)
ax1.grid(axis="x", visible=False)

# ---- 2. F/G per seed ------------------------------------------------------
ax2.axhline(1.0, color=C_GREY, lw=1.4, ls=(0, (5, 3)), zorder=2)
for i, s in enumerate(SEEDS):
    ax2.vlines(i, 1.0, RATIO[s], color=C_GREY, lw=1.2, zorder=2)
ax2.plot(X, [RATIO[s] for s in SEEDS], "o", ms=12, mfc="white",
         mec=INK, mew=2.2, linestyle="none", zorder=5)
ax2.axhline(ARITH, color=C_RED, lw=2.6, zorder=4,
            label="arithmetic mean of raw ratios = %.4f" % ARITH)
for i, s in enumerate(SEEDS):
    ax2.text(i, RATIO[s] + 0.075, "%.4f" % RATIO[s], ha="center", va="bottom",
             fontsize=11, color=INK)
ax2.set_xticks(X)
ax2.set_xticklabels([str(s) for s in SEEDS], fontsize=11.5)
ax2.set_ylim(0.0, 3.02)
ax2.set_xlim(-0.62, 4.62)
ax2.set_ylabel("F / G", fontsize=13)
ax2.set_title("2.  F/G per seed  →  arithmetic mean says %+.1f %%"
              % ((ARITH - 1) * 100), fontsize=14, color=C_RED, pad=8)
ax2.legend(fontsize=11, loc="upper left", framealpha=0.95)
i_drag = SEEDS.index(DRAGGER)
ax2.annotate("one seed at %.2f×\ndrags the mean up" % RATIO[DRAGGER],
             xy=(i_drag + 0.16, RATIO[DRAGGER]),
             xytext=(i_drag - 1.95, 1.80), fontsize=11.5, color=C_RED,
             ha="left", va="center",
             arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.8))
ax2.grid(axis="x", visible=False)

# ---- 3. ln(F/G) per seed --------------------------------------------------
ax3.axhline(0.0, color=C_GREY, lw=1.4, ls=(0, (5, 3)), zorder=2)
for i, s in enumerate(SEEDS):
    ax3.vlines(i, 0.0, LN[s], color=C_GREY, lw=1.2, zorder=2)
ax3.plot(X, [LN[s] for s in SEEDS], "o", ms=12, mfc="white",
         mec=INK, mew=2.2, linestyle="none", zorder=5)
ax3.axhline(MEAN_LN, color=C_PURPLE, lw=2.6, zorder=4,
            label="mean log-ratio = %+.4f" % MEAN_LN)
for i, s in enumerate(SEEDS):
    above = LN[s] >= MEAN_LN      # keep the label clear of the mean line
    ax3.text(i, LN[s] + (0.075 if above else -0.075), "%+.4f" % LN[s],
             ha="center", va=("bottom" if above else "top"), fontsize=11,
             color=INK)
ax3.set_xticks(X)
ax3.set_xticklabels([str(s) for s in SEEDS], fontsize=11.5)
ax3.set_ylim(-1.42, 1.42)
ax3.set_xlim(-0.62, 4.62)
ax3.set_ylabel("ln(F / G)", fontsize=13)
ax3.set_title("3.  ln(F/G) per seed  →  geometric mean %.4f = %+.1f %%"
              % (GEO, (GEO - 1) * 100), fontsize=14, color=C_PURPLE, pad=8)
ax3.legend(fontsize=11, loc="upper left", framealpha=0.95)
ax3.text(0.015, 0.035,
         "exp(%+.4f) = %.4f\nthe same five numbers, opposite sign"
         % (MEAN_LN, GEO),
         transform=ax3.transAxes, ha="left", va="bottom", fontsize=11.5,
         color=C_PURPLE)
ax3.grid(axis="x", visible=False)

# ---- 4. against the null-cell noise baseline ------------------------------
ABS = [abs(LN[s]) for s in SEEDS]
ax4.set_yscale("log")
ax4.bar(X, ABS, 0.52, color=C_SKY, zorder=3)
for i, s in enumerate(SEEDS):
    mult = ABS[i] / BASE_SD
    ax4.text(i, ABS[i] * 1.18, ("%.1f× sd" if mult < 10 else "%.0f× sd") % mult,
             ha="center", va="bottom", fontsize=11, color=INK)
styles = [("N7_GVSG_", C_GREY, "-"), ("N7b_FFNULL_", C_RED, "--")]
for cell, colour, ls in styles:
    y = 2 * NULL[cell]["sd_max"]
    ax4.axhline(y, color=colour, lw=2.0, ls=ls, zorder=4,
                label="2 × sd of %s (worst of %d seeds) = %.4f"
                      % (NULL[cell]["label"], NULL[cell]["n"], y))
ax4.set_xticks(X)
ax4.set_xticklabels([str(s) for s in SEEDS], fontsize=11.5)
ax4.set_ylim(1.4e-3, 260.0)
ax4.set_xlim(-0.62, 4.62)
ax4.set_ylabel("|ln(F/G)|   (log scale)", fontsize=13)
ax4.set_title("4.  the same log-ratios against a measured null",
              fontsize=14, pad=8)
ax4.legend(fontsize=10.5, loc="upper left", framealpha=0.95)
n_out = sum(1 for a in ABS if a > 2 * BASE_SD)
ax4.text(0.985, 0.755,
         "%d of %d seeds sit outside the widest null band –\nthe seed spread is "
         "real dispersion, not instrument noise" % (n_out, len(SEEDS)),
         transform=ax4.transAxes, ha="right", va="top", fontsize=11,
         color=INK)
ax4.grid(axis="x", visible=False)

fig.suptitle("One comparison, four quantities – %s capped, %d seeds"
             % (SHAPE, len(SEEDS)), fontsize=16.5, y=0.986)
fig.text(0.5, 0.944,
         "averaging the raw ratios reports %+.1f %%;  the geometric mean of the "
         "same five numbers is %+.1f %%"
         % ((ARITH - 1) * 100, (GEO - 1) * 100),
         ha="center", va="center", fontsize=13, color=INK)
common.provenance(fig, "stage3_baseline/seed_*/%s/champion_interleaved.json "
                       "(F_over_G_median_ratio, median_gflops) | "
                       "medium_pilot401 N7_GVSG_, N7b_FFNULL_ summary.json "
                       "(sample_sd)" % SHAPE)
fig.subplots_adjust(left=0.075, right=0.985, top=0.845, bottom=0.075,
                    hspace=0.42, wspace=0.19)


# --------------------------------------------------------------------------
# programmatic layout check
# --------------------------------------------------------------------------
def layout_report(figure):
    figure.canvas.draw()
    rend = figure.canvas.get_renderer()
    w_px, h_px = figure.canvas.get_width_height()
    items, smallest = [], None
    for ax in figure.axes:
        # only ticks actually inside the view -- matplotlib keeps locator
        # labels for off-view ticks, and those are not drawn
        x0, x1 = sorted(ax.get_xlim())
        y0, y1 = sorted(ax.get_ylim())
        xt = [t for v, t in zip(ax.get_xticks(), ax.get_xticklabels())
              if x0 <= v <= x1]
        yt = [t for v, t in zip(ax.get_yticks(), ax.get_yticklabels())
              if y0 <= v <= y1]
        groups = [("title", [ax.title]), ("xlabel", [ax.xaxis.label]),
                  ("ylabel", [ax.yaxis.label]), ("text", list(ax.texts)),
                  ("xtick", xt), ("ytick", yt)]
        for kind, arts in groups:
            for t in arts:
                if not t.get_visible() or not t.get_text().strip():
                    continue
                items.append(("%s:%r" % (kind, t.get_text()[:26]),
                              t.get_window_extent(rend)))
                if kind.endswith("tick"):
                    smallest = min(t.get_size(), smallest or 99)
        if ax.get_legend() is not None:
            items.append(("legend@" + (ax.get_title()[:12] or "?"),
                          ax.get_legend().get_window_extent(rend)))
    for t in figure.texts:
        if t.get_visible() and t.get_text().strip():
            items.append(("figtext:%r" % t.get_text()[:26],
                          t.get_window_extent(rend)))

    over = [n for n, b in items
            if b.x0 < -0.5 or b.y0 < -0.5 or b.x1 > w_px + 0.5 or b.y1 > h_px + 0.5]
    pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]
            ix = min(a.x1, b.x1) - max(a.x0, b.x0)
            iy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ix > 1.0 and iy > 1.0:
                pairs.append((items[i][0], items[j][0], ix * iy))
    print("layout: canvas %dx%d px, %d text/legend artists"
          % (w_px, h_px, len(items)))
    print("        smallest tick label: %.1f pt (floor 11 pt) -> %s"
          % (smallest, "OK" if smallest >= 11 else "FAIL"))
    print("overflow artists: %d, text-pair overlaps: %d" % (len(over), len(pairs)))
    for n in over:
        print("        OVERFLOW %s  (canvas %s)"
              % (n, Bbox.from_bounds(0, 0, w_px, h_px)))
    for a, b, area in pairs:
        print("        OVERLAP  %s <-> %s  (%.0f px^2)" % (a, b, area))
    return len(over), len(pairs)


layout_report(fig)
common.save(fig, "p13_four_quantities.png", tight=False)

# --------------------------------------------------------------------------
# stdout
# --------------------------------------------------------------------------
print()
print("%s capped, %s" % (SHAPE, ARM_DIR))
print("%-7s %-11s %-11s %-10s %-11s" % ("seed", "G GFLOP/s", "F GFLOP/s",
                                        "F/G", "ln(F/G)"))
for s in SEEDS:
    print("%-7d %-11.2f %-11.2f %-10.6f %+.6f"
          % (s, RAW[s]["G"], RAW[s]["F"], RATIO[s], LN[s]))
print()
print("arithmetic mean of raw ratios  = %.6f   -> reported as %+.4f %%"
      % (ARITH, (ARITH - 1) * 100))
print("mean log-ratio                 = %+.6f" % MEAN_LN)
print("geometric mean = exp(mean ln)  = %.6f   -> the correct central tendency "
      "%+.4f %%" % (GEO, (GEO - 1) * 100))
print("REVERSAL: raw-ratio average %+.1f %% vs geometric mean %+.1f %% "
      "(same five numbers)" % ((ARITH - 1) * 100, (GEO - 1) * 100))
print("dragger: seed %d at %.4f× (%.1f %% of the raw-ratio sum from one seed)"
      % (DRAGGER, RATIO[DRAGGER], 100 * RATIO[DRAGGER] / sum(RATIO.values())))
print("drop that one seed: raw mean %.6f (%+.2f %%), geometric mean %.6f (%+.2f %%)"
      % (mean(RATIO[s] for s in SEEDS if s != DRAGGER),
         (mean(RATIO[s] for s in SEEDS if s != DRAGGER) - 1) * 100,
         math.exp(mean(LN[s] for s in SEEDS if s != DRAGGER)),
         (math.exp(mean(LN[s] for s in SEEDS if s != DRAGGER)) - 1) * 100))
print()
print("raw GFLOP/s is shape-scoped -- median G across the five seeds:")
for sh in ("tiny", "medium", "large"):
    print("   %-7s %12.4f" % (sh, float(np.median(OTHER_RAW[sh]))))
print()
print("null-cell noise baseline (medium_pilot401):")
for cell in ("N7_GVSG_", "N7b_FFNULL_"):
    v = NULL[cell]
    print("   %-13s %-11s n=%d  sd median %.6f  sd worst-seed %.6f  "
          "2×worst = %.6f" % (cell, v["label"], v["n"], v["sd_med"],
                              v["sd_max"], 2 * v["sd_max"]))
print("   conservative baseline sd = %.6f; %d of %d seeds exceed 2× it"
      % (BASE_SD, n_out, len(SEEDS)))
for s in SEEDS:
    print("   seed %d  |ln(F/G)| = %.6f = %8.1f × baseline sd"
          % (s, abs(LN[s]), abs(LN[s]) / BASE_SD))
