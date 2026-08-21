#!/usr/bin/env python3
"""P16 -- medium: the *difference* between the two arms' best-so-far curves.

Why a difference and not two curves
-----------------------------------
On capped medium the best-so-far rises about +29 % from Gen0 to the end of the
run, while the two arms end a median of only ~+1 % apart.  Two absolute curves
1 % apart drawn on a 29 % y-range are one line, and shading between them is a
hairline.  So each panel plots

    d(x) = ln( F_bestsofar(x) / G_bestsofar(x) )

against x = cumulative completed evaluations, with a zero reference and the
signed region between the curve and zero shaded.  Then the *vertical extent is
the effect* and the *shaded area is the AUC difference* -- the two things the
gate actually scores.

Why the x-axis is evaluations, not generation index
---------------------------------------------------
The gate's AUC is an integral against completed evaluations, and the two arms
do not reach a given generation at the same evaluation count (they early-stop
at different generations and their per-generation batches complete at
different rates).  Generation index would therefore compare the arms at two
different budgets.  Because generation 10 is itself one of the three gate
criteria and is invisible on an evaluation axis, each arm's gen-10 evaluation
position is marked under the axis.

Interpolation
-------------
Both arms' best-so-far are *monotone step functions* of
``cumulative_complete_evals``: the value recorded at a generation's evaluation
count holds until the next generation's count.  They are put on the union of
the two arms' evaluation knots and evaluated by previous-value hold -- exactly
the zero-order interpolation that ``common.auc`` integrates.  Linear
interpolation is deliberately not used: it would invent intermediate
improvements the run never made and would soften the jumps that carry the
signal.

B*
--
``B* = min`` of the two arms' final ``cumulative_complete_evals``.  Scoring
past B* would compare an arm against a stopped opponent, so everything beyond
B* is faded and the discarded band is shaded and labelled with the fraction of
the longer arm's evaluations it throws away.

Run on the HOST:  python3 p16_evolution_medium.py
"""
from __future__ import annotations

import bisect
import math
from statistics import median

import matplotlib.lines as mlines
import matplotlib.patches as mpatches

import common
from common import ARM_COLOR, C_GREY

SHAPE = "medium"
FIGNAME = "p16_evolution_medium"
ROWS = [("capped", "$P_0$ = 512"), ("native", "$P_0$ = 11,405")]

INK = "#1F1F1F"          # curve + text ink; never a series colour
ZERO = "#4D4D4D"         # the "arms tied" reference
BSTAR = "#333333"         # B* rule
DISCARD = "#BFBFBF"      # the band B* throws away
FILL_ALPHA = 0.48
GHOST_ALPHA = 0.30


# --------------------------------------------------------------------------
# step-function machinery
# --------------------------------------------------------------------------
def knots(rows):
    """(evaluation counts, best-so-far) for one arm, as recorded."""
    return ([r["cumulative_complete_evals"] for r in rows],
            [r["best_gflops_so_far"] for r in rows])


def hold(xs, ys, x):
    """Previous-value hold: the step function's value at x."""
    return ys[max(bisect.bisect_right(xs, x) - 1, 0)]


def gen10_eval(rows):
    """Cumulative completed evaluations at the end of generation 10."""
    c = [r for r in rows if r["gen"] <= 10]
    return (c[-1] if c else rows[-1])["cumulative_complete_evals"]


def xticks_for(xlim):
    """Ticks strictly inside the view, so no label hangs off the canvas."""
    span = xlim[1] - xlim[0]
    step = 5000 if span > 15000 else 2000
    lo = int(math.ceil(xlim[0] / step) * step)
    return [t for t in range(lo, int(xlim[1]) + 1, step)
            if t <= xlim[1] - 0.03 * span]


def stepify(xs, ys):
    """Piecewise-constant polyline; jumps are zero-width so signed fills
    split exactly at the sign change with no gap and no interpolation."""
    px, py = [], []
    for i in range(len(xs) - 1):
        px += [xs[i], xs[i + 1]]
        py += [ys[i], ys[i]]
    return px, py


def difference(rg, rf):
    """The whole per-seed record the panel needs."""
    xg, yg = knots(rg)
    xf, yf = knots(rf)
    start = max(xg[0], xf[0])            # both arms defined only from here
    bstar = min(xg[-1], xf[-1])
    end = max(xg[-1], xf[-1])
    grid = sorted({x for x in xg + xf if start <= x <= end} | {start, bstar, end})
    d = [math.log(hold(xf, yf, x) / hold(xg, yg, x)) for x in grid]

    ins = [i for i, x in enumerate(grid) if x <= bstar]
    aucg, aucf = common.auc(rg, bstar), common.auc(rf, bstar)
    long_arm = "G" if xg[-1] > xf[-1] else ("F" if xf[-1] > xg[-1] else None)
    dropped = 0.0 if long_arm is None else 1.0 - bstar / max(xg[-1], xf[-1])
    return {
        "grid": grid, "d": d,
        "in": (grid[:ins[-1] + 1], d[:ins[-1] + 1]),
        "past": (grid[ins[-1]:], d[ins[-1]:]),
        "start": start, "bstar": bstar, "end": end,
        "auc_ratio": aucf / aucg, "auc_pos": aucf > aucg,
        "g10": {"G": gen10_eval(rg), "F": gen10_eval(rf)},
        "long_arm": long_arm, "dropped": dropped,
    }


def framing(level):
    """(median Gen0->end rise, median end-of-run F/G) -- the two numbers that
    justify plotting a difference instead of two curves. Computed here, not
    transcribed, so the subtitle can never drift from the artifacts."""
    rises, gaps = [], []
    for s in common.SEEDS:
        rg = common.traj(level, "G", s, SHAPE)
        rf = common.traj(level, "F", s, SHAPE)
        for r in (rg, rf):
            rises.append(r[-1]["best_gflops_so_far"]
                         / r[0]["best_gflops_so_far"] - 1.0)
        gaps.append(rf[-1]["best_gflops_so_far"]
                    / rg[-1]["best_gflops_so_far"])
    return median(rises), median(gaps)


def block(level):
    return {s: difference(common.traj(level, "G", s, SHAPE),
                          common.traj(level, "F", s, SHAPE))
            for s in common.SEEDS}


# --------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------
def panel(ax, seed, rec, lim, xlim):
    px, py = stepify(*rec["in"])
    ax.fill_between(px, py, 0, where=[v >= 0 for v in py],
                    color=ARM_COLOR["F"], alpha=FILL_ALPHA, lw=0, zorder=2)
    ax.fill_between(px, py, 0, where=[v <= 0 for v in py],
                    color=ARM_COLOR["G"], alpha=FILL_ALPHA, lw=0, zorder=2)
    ax.plot(px, py, color=INK, lw=1.3, zorder=4, solid_joinstyle="miter")

    # Which left corner does the curve leave free? Everything else -- the info
    # box and the "B*" label -- is placed against that answer so nothing has to
    # be nudged by hand when the data changes.
    cut = xlim[0] + 0.48 * (xlim[1] - xlim[0])
    left = [v for x, v in zip(px, py) if x <= cut] or [0.0]
    top = (lim - max(left)) >= (min(left) + lim)

    # everything past B* is not scored: shade the band, ghost the curve
    if rec["end"] > rec["bstar"]:
        ax.axvspan(rec["bstar"], rec["end"], color=DISCARD, alpha=0.45,
                   lw=0, zorder=1)
        gx, gy = stepify(*rec["past"])
        ax.plot(gx, gy, color=INK, lw=1.1, alpha=GHOST_ALPHA, zorder=3)
        # when B* throws away a serious slice of a run, say so inside the band
        if rec["dropped"] >= 0.10:
            ax.text(0.5 * (rec["bstar"] + rec["end"]), 0.0,
                    f"unscored: {rec['dropped'] * 100:.1f} % of {rec['long_arm']}",
                    rotation=90, ha="center", va="center", fontsize=11,
                    color="#4A4A4A", zorder=6,
                    bbox=dict(fc="white", ec="none", alpha=0.55, pad=1.0))

    ax.axhline(0, color=ZERO, lw=1.2, zorder=3.5)
    ax.axvline(rec["bstar"], color=BSTAR, lw=1.5, zorder=5)
    ax.text(rec["bstar"], -lim * 0.955 if top else lim * 0.955, " B*",
            color=BSTAR, fontsize=11, ha="left",
            va="bottom" if top else "top", zorder=6)

    # gen 10: a gate criterion, and otherwise invisible on an evaluation axis.
    # The arms often reach it within a few dozen evaluations of each other, so
    # G is drawn wide underneath and F narrow on top: coincident marks read as
    # an orange pip inside a blue one rather than as a single arm.
    tr = ax.get_xaxis_transform()
    for arm, lw, ms in (("G", 3.4, 10.0), ("F", 1.3, 5.5)):
        x = rec["g10"][arm]
        ax.plot([x, x], [0, 0.085], transform=tr, color=ARM_COLOR[arm],
                lw=lw, alpha=0.55 if arm == "G" else 0.95, zorder=6,
                clip_on=False, solid_capstyle="butt")
        ax.plot([x], [0.0], transform=tr, marker="^", ms=ms,
                mfc=ARM_COLOR[arm], mec="white", mew=0.9,
                zorder=6.5 if arm == "G" else 7, clip_on=False, ls="none")

    step = 0.05 if lim <= 0.20 else 0.10
    n = int(lim / step + 1e-9)          # ticks strictly inside the view
    ax.set_yticks([round(step * k, 3) for k in range(-n, n + 1)])
    ax.set_xlim(*xlim)
    ax.set_ylim(-lim, lim)
    ax.set_autoscaley_on(False)
    ax.set_title(f"seed {seed}", fontsize=14, pad=7)

    # per-panel readout, in the free corner chosen above
    sign = "F" if rec["auc_pos"] else "G"
    lines = [f"AUC  F/G = {rec['auc_ratio']:.4f}   ({sign} ahead)"]
    if rec["long_arm"] is None:
        lines.append(f"B* = {rec['bstar']:,}  (arms end together)")
    else:
        lines.append(f"B* = {rec['bstar']:,} drops {rec['dropped'] * 100:.1f} %"
                     f" of {rec['long_arm']}")
    ax.text(0.035, 0.955 if top else 0.045, "\n".join(lines),
            transform=ax.transAxes, ha="left", va="top" if top else "bottom",
            fontsize=11, color=INK, zorder=8, linespacing=1.45,
            bbox=dict(fc="white", ec=ARM_COLOR[sign], lw=1.0, alpha=0.90,
                      pad=3.2, boxstyle="round,pad=0.32"))


# --------------------------------------------------------------------------
# layout self-check
# --------------------------------------------------------------------------
def text_artists(fig):
    out = list(fig.texts)
    for ax in fig.axes:
        out += [ax.title, ax.xaxis.label, ax.yaxis.label]
        out += list(ax.texts)
        out += list(ax.get_xticklabels()) + list(ax.get_yticklabels())
    return [t for t in out if t.get_visible() and t.get_text().strip()]


def check_layout(fig):
    """Measure every text/legend bbox against the canvas and each other."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    items = [(t, t.get_window_extent(r)) for t in text_artists(fig)]
    items += [(lg, lg.get_window_extent(r)) for lg in fig.legends]

    over = [(t, b) for t, b in items
            if b.x0 < -1.0 or b.y0 < -1.0 or b.x1 > W + 1.0 or b.y1 > H + 1.0]
    pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]
            w = min(a.x1, b.x1) - max(a.x0, b.x0)
            h = min(a.y1, b.y1) - max(a.y0, b.y0)
            if w > 1.0 and h > 1.0:
                pairs.append((items[i][0], items[j][0], w * h))
    print(f"  layout: canvas {W}x{H}px, {len(items)} text/legend artists")
    print(f"  overflow artists: {len(over)}, text-pair overlaps: {len(pairs)}")
    for t, b in over[:6]:
        print(f"    overflow: {_lab(t)!r} bbox=({b.x0:.0f},{b.y0:.0f},"
              f"{b.x1:.0f},{b.y1:.0f})")
    for a, b, area in sorted(pairs, key=lambda p: -p[2])[:6]:
        print(f"    overlap {area:.0f}px^2: {_lab(a)!r} vs {_lab(b)!r}")
    return len(over), len(pairs)


def _lab(t):
    s = getattr(t, "get_text", lambda: "<legend>")()
    s = " ".join(s.split())
    return s if len(s) <= 40 else s[:37] + "..."


# --------------------------------------------------------------------------
def main():
    data = {lvl: block(lvl) for lvl, _ in ROWS}

    fig, axes = common.new_fig(2, 5, figsize=(19.2, 9.2),
                               sharex="row", sharey="row")
    fig.subplots_adjust(left=0.050, right=0.988, top=0.838, bottom=0.185,
                        wspace=0.11, hspace=0.48)

    printed = {}
    for row, (level, p0) in enumerate(ROWS):
        recs = data[level]
        lim = math.ceil(max(max(abs(v) for v in r["d"]) for r in recs.values())
                        * 1.18 / 0.025) * 0.025
        xhi = max(r["end"] for r in recs.values())
        xlo = 0.0 if level == "capped" else \
            min(r["start"] for r in recs.values()) - 0.045 * xhi
        xlim = (xlo, xhi + 0.035 * (xhi - xlo))

        for col, seed in enumerate(common.SEEDS):
            ax = axes[row][col]
            panel(ax, seed, recs[seed], lim, xlim)
            ax.set_xlabel("cumulative completed evaluations", labelpad=4)
            if col == 0:
                ax.set_ylabel(r"ln( $F_{\mathrm{best}}$ / $G_{\mathrm{best}}$ )")
            ax.set_xticks(xticks_for(xlim))
            ax.xaxis.set_major_formatter(lambda v, _: f"{v / 1000:,.0f}k"
                                         if v else "0")

        npos = sum(r["auc_pos"] for r in recs.values())
        worst = max(recs.values(), key=lambda r: r["dropped"])
        wseed = [s for s, r in recs.items() if r is worst][0]
        pos = axes[row][0].get_position()
        head = (f"{level}  ·  {p0}   —   AUC( F ) > AUC( G ) on "
                f"{npos}/5 seeds   ·   panels share y at ±{lim:.3f} ln   ·   "
                f"B* discards up to {worst['dropped'] * 100:.1f} % of arm "
                f"{worst['long_arm']}'s evaluations (seed {wseed})")
        fig.text(pos.x0 - 0.044, pos.y1 + 0.044, head, ha="left", va="bottom",
                 fontsize=13, color=INK, weight="semibold")
        printed[level] = (npos, lim, recs)

    fig.suptitle(f"{SHAPE} — how far ahead arm F is, evaluation by evaluation: "
                 r"ln( $F_{\mathrm{best\,so\,far}}$ / $G_{\mathrm{best\,so\,far}}$ )",
                 y=0.983, fontsize=19)
    rise, endgap = framing("capped")
    fig.text(0.5, 0.952,
             "Each panel is the difference between the arms, not their two "
             "best-so-far curves: the vertical extent is the effect, the shaded "
             "area is the AUC difference.\n"
             f"A capped run climbs a median {rise * 100:.1f} % from Gen0 to its "
             f"end while the arms finish a median {abs(endgap - 1) * 100:.2f} % "
             "apart, so the two absolute curves drawn together are one line.",
             ha="center", va="top", fontsize=12.5, color=C_GREY,
             linespacing=1.5)

    fig.text(0.5, 0.117,
             "x is cumulative completed evaluations, not generation index: the "
             "gate's AUC is integrated against evaluations, and the two arms do "
             "not reach a given generation at the same evaluation count —\n"
             "hence the two separate gen-10 marks under each panel."
             "     0.01 in ln ≈ 1.0 %.",
             ha="center", va="top", fontsize=12, color=C_GREY, linespacing=1.5)

    handles = [
        mpatches.Patch(fc=ARM_COLOR["F"], alpha=FILL_ALPHA, ec="none",
                       label="arm F ahead"),
        mpatches.Patch(fc=ARM_COLOR["G"], alpha=FILL_ALPHA, ec="none",
                       label="arm G ahead"),
        mlines.Line2D([], [], color=INK, lw=1.4,
                      label="difference, step-held"),
        mlines.Line2D([], [], color=ZERO, lw=1.2, label="arms level"),
        mlines.Line2D([], [], color=ARM_COLOR["G"], marker="^", ms=10.0,
                      mec="white", ls="none", label="gen 10, G (wide)"),
        mlines.Line2D([], [], color=ARM_COLOR["F"], marker="^", ms=5.5,
                      mec="white", ls="none", label="gen 10, F (narrow)"),
        mlines.Line2D([], [], color=BSTAR, lw=1.5, label="B*"),
        mpatches.Patch(fc=DISCARD, alpha=0.45, ec="none",
                       label="past B*: unscored"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=8, frameon=False,
               fontsize=11.5, bbox_to_anchor=(0.5, 0.024), handlelength=1.9,
               columnspacing=1.6)

    common.provenance(fig, "trajectory.jsonl · best_gflops_so_far vs "
                           "cumulative_complete_evals · stage3_{baseline,guided} "
                           "+ stage5_native_{baseline,guided} · medium · "
                           "5 paired seeds")

    n_over, n_pairs = check_layout(fig)
    common.save(fig, FIGNAME, tight=False)

    for level, (npos, lim, recs) in printed.items():
        print(f"  {SHAPE} {level}: AUC F>G on {npos}/5 seeds; y ±{lim:.3f} ln")
        for s in common.SEEDS:
            r = recs[s]
            drop = (f"{r['dropped'] * 100:5.2f}% of {r['long_arm']}"
                    if r["long_arm"] else "  0.00% (level)")
            print(f"    seed {s}: AUC F/G = {r['auc_ratio']:.6f} "
                  f"({'F' if r['auc_pos'] else 'G'})  B* = {r['bstar']:6,d} "
                  f"drops {drop}  gen10 eval G/F = {r['g10']['G']:,}/"
                  f"{r['g10']['F']:,}  |ln| max = "
                  f"{max(abs(v) for v in r['d']):.4f}")
    print(f"  self-check -> overflow artists: {n_over}, "
          f"text-pair overlaps: {n_pairs}")


if __name__ == "__main__":
    main()
