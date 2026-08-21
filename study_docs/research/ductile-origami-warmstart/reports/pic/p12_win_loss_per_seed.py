"""P12 -- how much each seed won or lost by, per criterion, per block.

The gate is scored as counts, which answers "how many seeds" but not "by how
much". This figure answers the second question: one diverging bar per criterion
per seed, zero centred, right = arm F ahead, every value labelled.

Three of the four bars are the gate's sub-criteria (Gen0, gen-10, AUC), all read
off trajectory.jsonl with B* = min of the two arms' final
cumulative_complete_evals. The fourth bar is the final champion ratio. It is set
apart -- own fill, own divider, own shaded row -- because it is *not* a gate
component and it is the only one of the four measured through the 7x champion
remeasure path.

That distinction is what the faint null rule is for. The cross-window G/G' and
F/F' nulls measure the remeasure instrument, so they bound the final-ratio bar
and nothing else; the three trajectory criteria never touch that path. On large
the null sits near +/-1.8 %, which is the size of several of the bars next to it.

Run on the HOST (matplotlib 3.8.2). Idempotent: no timestamps, no randomness.
"""
from __future__ import annotations

import math
from statistics import median

from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import common
from common import CAT_COLOR, C_GREY, C_LIGHT, SEEDS

INK = "#2B2B2B"
C_WIN = CAT_COLOR["better"]
C_LOSS = CAT_COLOR["worse"]

CRIT = ["Gen0", "gen-10", "AUC"]
# y is inverted below, so a larger offset sits lower on the page: the three gate
# rows read top-to-bottom, then the divider, then the non-gate row.
OFFS = [-0.33, -0.11, 0.11]
OFF_RATIO = 0.40
DIVIDER = 0.26
BAR_H = 0.155


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def gate_ratios(level, shape, seed):
    """(Gen0, gen-10, AUC) F/G ratios for one seed."""
    rg = common.traj(level, "G", seed, shape)
    rf = common.traj(level, "F", seed, shape)
    b = min(rg[-1]["cumulative_complete_evals"],
            rf[-1]["cumulative_complete_evals"])
    return (common.gen0(rf) / common.gen0(rg),
            common.gen10(rf) / common.gen10(rg),
            common.auc(rf, b) / common.auc(rg, b)), b


def medium_capped_final():
    a, b = common.cell_per_seed("C03_"), common.cell_per_seed("C03CONF_")
    return {s: 0.5 * (a[s]["mean_ln"] + b[s]["mean_ln"]) for s in SEEDS}


def medium_native_final():
    c = common.cell_per_seed("STAGE2_NATIVE_")
    return {s: c[s]["mean_ln"] for s in SEEDS}


def large_final(cell):
    """large cells carry a different schema -- no ['mean_ln'] here."""
    c = common.cell_per_seed(cell, root=common.XWIN)
    return {s: c[s]["canonical_endpoint_ln_F_over_G"] for s in SEEDS}


def medium_null_sds(gg, ff):
    a, b = common.cell_per_seed(gg), common.cell_per_seed(ff)
    return [a[s]["sample_sd"] for s in SEEDS] + [b[s]["sample_sd"] for s in SEEDS]


def large_null_sds(gg, ff):
    a = common.cell_per_seed(gg, root=common.XWIN)
    b = common.cell_per_seed(ff, root=common.XWIN)
    return ([a[s]["sample_sd_ln_F_over_G"] for s in SEEDS]
            + [b[s]["sample_sd_ln_F_over_G"] for s in SEEDS])


BLOCKS = [
    dict(key="medium capped", title="medium  ·  capped", level="capped",
         shape="medium", truth=(3, 3, 3), final=medium_capped_final(),
         nulls=medium_null_sds("N7_GVSG_", "N7b_FFNULL_")),
    dict(key="large capped", title="large  ·  capped", level="capped",
         shape="large", truth=(1, 2, 3), final=large_final("m6_capped"),
         nulls=large_null_sds("gvsg_capped", "ffnull_capped")),
    dict(key="medium native", title="medium  ·  native", level="native",
         shape="medium", truth=(2, 1, 3), final=medium_native_final(),
         nulls=medium_null_sds("N8_NATIVE_GVSG_", "N8b_NATIVE_FFNULL_")),
    dict(key="large native", title="large  ·  native", level="native",
         shape="large", truth=(3, 1, 2), final=large_final("m6"),
         nulls=large_null_sds("gvsg_native", "ffnull_native")),
]

for b in BLOCKS:
    b["ratios"], b["budget"] = {}, {}
    for s in SEEDS:
        b["ratios"][s], b["budget"][s] = gate_ratios(b["level"], b["shape"], s)
    # percent, exp(ln(F/G)) - 1, which for a ratio r is simply r - 1
    b["pct"] = {s: [100.0 * (r - 1.0) for r in b["ratios"][s]] for s in SEEDS}
    b["final_pct"] = {s: 100.0 * (math.exp(b["final"][s]) - 1.0) for s in SEEDS}
    b["counts"] = tuple(sum(1 for s in SEEDS if b["ratios"][s][j] > 1.0)
                        for j in range(3))
    b["null_pct"] = 100.0 * (math.exp(median(b["nulls"])) - 1.0)


# --------------------------------------------------------------------------
# figure
# --------------------------------------------------------------------------
fig, axes = common.new_fig(2, 2, figsize=(13.6, 12.0))
AX = [axes[0][0], axes[0][1], axes[1][0], axes[1][1]]

BBOX = dict(fc="white", ec="none", alpha=0.90, pad=2.0)

for ax, blk in zip(AX, BLOCKS):
    vals = [v for s in SEEDS for v in blk["pct"][s]] \
        + [blk["final_pct"][s] for s in SEEDS]
    xlim = 1.52 * max(abs(v) for v in vals)

    # null rule: bounds the final-ratio bar only (see module docstring)
    for sign in (-1, +1):
        ax.axvline(sign * blk["null_pct"], color=C_GREY, lw=1.3, alpha=0.60,
                   ls=(0, (4, 3)), zorder=1)
    ax.text(blk["null_pct"], -0.60, "  null ±%.2f%%" % blk["null_pct"],
            ha="left", va="center", fontsize=10.5, color=C_GREY, zorder=8)

    yticks, ylabels = [], []
    for i, s in enumerate(SEEDS):
        # the non-gate row, shaded and fenced off from the three gate rows
        ax.axhspan(i + DIVIDER, i + 0.52, color=C_LIGHT, alpha=0.45, lw=0,
                   zorder=0)
        ax.plot([-xlim, xlim], [i + DIVIDER] * 2, color=C_GREY, lw=1.0,
                ls=(0, (3, 3)), alpha=0.85, zorder=4)
        if i:
            ax.axhline(i - 0.5, color=C_GREY, lw=0.8, alpha=0.30, zorder=1)

        rows = [(OFFS[j], blk["pct"][s][j], CRIT[j], False) for j in range(3)]
        rows.append((OFF_RATIO, blk["final_pct"][s], "final ratio", True))
        for off, v, name, is_ratio in rows:
            y = i + off
            col = C_WIN if v > 0 else C_LOSS
            if is_ratio:
                ax.barh(y, v, height=BAR_H, facecolor="white", edgecolor=col,
                        linewidth=1.4, hatch="///", zorder=5)
            else:
                ax.barh(y, v, height=BAR_H, facecolor=col, alpha=0.92,
                        edgecolor="white", linewidth=0.8, zorder=5)
            pad = 0.016 * xlim
            ax.text(v + (pad if v > 0 else -pad), y, "%+.2f" % v,
                    ha="left" if v > 0 else "right", va="center",
                    fontsize=10.5, color=INK, zorder=6)
            yticks.append(y)
            ylabels.append(name)

    ax.axvline(0.0, color=INK, lw=1.2, alpha=0.8, zorder=5)
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)
    ax.set_xlim(-xlim, xlim)
    ax.set_ylim(4.62, -1.02)          # inverted: 24001 on top, headroom above
    ax.tick_params(axis="both", labelsize=11)
    ax.grid(axis="y", visible=False)
    ax.set_title(blk["title"], pad=9)

    for i, s in enumerate(SEEDS):
        ax.text(-0.248, i, str(s), transform=ax.get_yaxis_transform(),
                ha="left", va="center", fontsize=12.5, color=INK,
                fontweight="bold", clip_on=False)

    ax.text(0.986, 0.985,
            "seeds with F ahead:  Gen0 %d/5 · gen-10 %d/5 · AUC %d/5"
            % blk["counts"], transform=ax.transAxes, ha="right", va="top",
            fontsize=11, color=INK, zorder=8, bbox=BBOX)

AX[2].set_xlabel("F/G − 1  (%)     right = arm F ahead")
AX[3].set_xlabel("F/G − 1  (%)     right = arm F ahead")

handles = [
    Patch(facecolor=C_WIN, alpha=0.92, edgecolor="white"),
    Patch(facecolor=C_LOSS, alpha=0.92, edgecolor="white"),
    Patch(facecolor="white", edgecolor=C_GREY, hatch="///", linewidth=1.4),
    Line2D([], [], color=C_GREY, lw=1.3, ls=(0, (4, 3)), alpha=0.60),
]
labels = [
    "gate bar: F ahead",
    "gate bar: G ahead",
    "final ratio — not a gate component (7× remeasure)",
    "remeasure null ±1 sd — final-ratio bar only",
]
fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.9455),
           ncol=4, frameon=True, framealpha=0.95, fontsize=11,
           handletextpad=0.5, columnspacing=1.1, borderpad=0.55)

fig.suptitle("How much each seed won or lost by", y=0.993, fontsize=19)
fig.text(0.5, 0.9655,
         "Gen0 / gen-10 / AUC come from trajectory.jsonl with "
         "B* = min of the two arms’ final cumulative_complete_evals.  "
         "bars are exp(ln(F/G)) − 1;  x-scale is per panel.",
         ha="center", va="top", fontsize=10.5, color=C_GREY, linespacing=1.4)

common.provenance(fig, "stage3_{baseline,guided} / stage5_native_{baseline,guided} "
                       "trajectory.jsonl  |  medium_pilot401 C03, C03CONF, "
                       "STAGE2_NATIVE + N7/N7b/N8/N8b  |  large_xwindow m6, "
                       "m6_capped + gvsg, ffnull")
fig.subplots_adjust(left=0.112, right=0.988, top=0.884, bottom=0.058,
                    hspace=0.22, wspace=0.32)


# --------------------------------------------------------------------------
# layout check: every text / legend bbox against the canvas and against itself
# --------------------------------------------------------------------------
def _on_view_ticklabels(a):
    """Only the tick labels matplotlib actually draws (the locator can emit
    ticks outside the view limits; those Text objects keep stale positions and
    would show up as phantom collisions)."""
    out = []
    for axis, lim in ((a.xaxis, a.get_xlim()), (a.yaxis, a.get_ylim())):
        lo, hi = sorted(lim)
        for tk in axis.get_major_ticks():
            if lo - 1e-12 <= tk.get_loc() <= hi + 1e-12:
                out.append(tk.label1)
    return out


def _layout_report(figure):
    figure.canvas.draw()
    rend = figure.canvas.get_renderer()
    texts, boxes, ticks = [], [], []
    for t in figure.texts:
        texts.append(t)
    for a in figure.axes:
        texts.append(a.title)
        texts.append(a.xaxis.label)
        texts.append(a.yaxis.label)
        tl = _on_view_ticklabels(a)
        ticks.extend(tl)
        texts.extend(tl)
        texts.extend(a.texts)
        if a.get_legend() is not None:
            boxes.append(a.get_legend())
            texts.extend(a.get_legend().get_texts())
    for lg in figure.legends:
        boxes.append(lg)
        texts.extend(lg.get_texts())
    texts = [t for t in texts if t.get_visible() and t.get_text().strip()]

    small = [t.get_text() for t in ticks
             if t.get_visible() and t.get_text().strip() and t.get_fontsize() < 11]

    canvas = figure.bbox
    ext = []
    for a in texts + boxes:
        try:
            ext.append((a, a.get_window_extent(rend)))
        except TypeError:
            ext.append((a, a.get_window_extent()))
    over = [a for a, bb in ext
            if bb.x0 < canvas.x0 - 0.5 or bb.y0 < canvas.y0 - 0.5
            or bb.x1 > canvas.x1 + 0.5 or bb.y1 > canvas.y1 + 0.5]

    tex = [(t, bb) for t, bb in ext if t in texts]
    pairs = []
    for i in range(len(tex)):
        for j in range(i + 1, len(tex)):
            a, b = tex[i][1], tex[j][1]
            w = min(a.x1, b.x1) - max(a.x0, b.x0)
            h = min(a.y1, b.y1) - max(a.y0, b.y0)
            if w > 1.0 and h > 1.0:
                pairs.append(("%r@(%.0f,%.0f)" % (tex[i][0].get_text()[:30],
                                                  a.x0, a.y0),
                              "%r@(%.0f,%.0f)" % (tex[j][0].get_text()[:30],
                                                  b.x0, b.y0), w * h))
    return over, pairs, small


_over, _pairs, _small = _layout_report(fig)
common.save(fig, "p12_win_loss_per_seed.png", tight=False)

# --------------------------------------------------------------------------
# stdout: every number that reached the figure
# --------------------------------------------------------------------------
print("layout: overflow artists: %d, text-pair overlaps: %d, "
      "tick labels < 11pt: %d" % (len(_over), len(_pairs), len(_small)))
for a in _over:
    print("   OVERFLOW %r" % (getattr(a, "get_text", lambda: a)(),))
for p in _pairs:
    print("   OVERLAP  %s / %s  (%.0f px2)" % p)

print()
print("per-seed margins, percent of arm G  (exp(ln(F/G)) - 1)")
for b in BLOCKS:
    print("  %-14s  B* = %s" % (b["key"], [b["budget"][s] for s in SEEDS]))
    for s in SEEDS:
        print("    %d  Gen0 %+8.4f  gen-10 %+8.4f  AUC %+8.4f | final ratio "
              "%+8.4f  (ln %+.6f)"
              % (s, b["pct"][s][0], b["pct"][s][1], b["pct"][s][2],
                 b["final_pct"][s], b["final"][s]))
    print("    counts (F ahead) Gen0 %d/5  gen-10 %d/5  AUC %d/5   "
          "ground truth %d/%d/%d   %s"
          % (b["counts"] + b["truth"]
             + ("MATCH" if b["counts"] == b["truth"] else "*** DISAGREES ***",)))
    print("    block null: 10 per-seed sds, median %.6f -> +/-%.3f %%"
          % (median(b["nulls"]), b["null_pct"]))

print()
print("cross-check against common.gate_counts()")
for b in BLOCKS:
    gc = common.gate_counts(b["level"], b["shape"])
    mine = dict(zip(("gen0", "gen10", "auc"), b["counts"]))
    print("  %-14s %s vs %s  %s" % (b["key"], mine, gc,
                                    "MATCH" if mine == gc else "*** DIFFERS ***"))
