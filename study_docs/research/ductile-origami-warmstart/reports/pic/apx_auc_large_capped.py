#!/usr/bin/env python3
"""APPENDIX -- AUC, large capped: both arms' best-so-far curves, per seed.

AUC is one of the three sub-criteria of the directional-consistency gate. It is
the step-hold integral of ``best_gflops_so_far`` against
``cumulative_complete_evals``, truncated at

    B* = min(final cumulative_complete_evals of arm G, of arm F)

and it is computed here by ``common.auc``, the same helper the analysis uses.

The main-deck evolution figures plot arm differences. These appendix panels do
the opposite on purpose: they show both absolute curves, because the question a
backup slide has to answer is what the search actually *did* -- how fast it
climbed, when it stalled, and how much of the run B* throws away.

Three things each panel carries that the deck does not currently state:

  * the signed area between the two curves. Orange where F is ahead, blue where
    G is ahead. That area is the AUC difference over the evaluation range both
    arms cover.
  * how much of one arm's run B* discards. On several seeds the truncation is
    not a rounding detail.
  * the start offset. ``common.auc`` starts each arm's integral at that arm's
    own first ``cumulative_complete_evals``, and the two arms do not finish
    Gen0 at the same evaluation count. The leftover one-sided sliver is
    therefore part of the metric but is *not* part of the shaded area, and on
    some seeds it is a large share of the total. Panels flag it when it is.

The y-axis starts at the lower of the two Gen0 values rather than at zero: the
run climbs tens of percent while the arms separate by a few percent, so a
zero-based axis would collapse both curves onto one line.

Run on the HOST:  python3 apx_auc_large_capped.py
"""
from __future__ import annotations

import bisect

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter, MaxNLocator

import common as C

# --------------------------------------------------------------------------
# which block this figure is
# --------------------------------------------------------------------------
SHAPE = "large"
LEVEL = "capped"
BLOCK = f"{SHAPE} {LEVEL}"
OUT = "apx_auc_large_capped"
SRC_TAG = f"{C.ARM_DIR[(LEVEL, 'G')]} + {C.ARM_DIR[(LEVEL, 'F')]}"

FADE = 0.30            # alpha for everything past B*
FILL_ALPHA = 0.32      # signed area between the curves
DISCARD_MIN = 3.0      # annotate a discarded fraction at or above this %
OFFSET_MIN = 5.0       # annotate a start offset worth this % of the AUC gap

COMMA = FuncFormatter(lambda v, _pos: f"{v:,.0f}")


# --------------------------------------------------------------------------
# step-hold machinery -- deliberately the same semantics as common.auc
# --------------------------------------------------------------------------
def series(rows):
    """(xs, ys) for one arm: evaluation counts and best-so-far."""
    return ([r["cumulative_complete_evals"] for r in rows],
            [r["best_gflops_so_far"] for r in rows])


def hold(xs, ys, t):
    """Value in force at t under the step-hold rule common.auc integrates."""
    return ys[max(bisect.bisect_right(xs, t) - 1, 0)]


def common_grid(xg, xf, budget):
    """Every breakpoint of either arm inside the range both arms cover."""
    lo = max(xg[0], xf[0])
    pts = {lo, budget}
    pts.update(x for x in xg if lo <= x <= budget)
    pts.update(x for x in xf if lo <= x <= budget)
    return sorted(pts)


def seed_facts(seed):
    """Everything one panel needs, all computed from the artifacts."""
    rg = C.traj(LEVEL, "G", seed, SHAPE)
    rf = C.traj(LEVEL, "F", seed, SHAPE)
    xg, yg = series(rg)
    xf, yf = series(rf)

    budget = min(xg[-1], xf[-1])
    auc_g, auc_f = C.auc(rg, budget), C.auc(rf, budget)
    ratio = auc_f / auc_g
    delta = auc_f - auc_g

    grid = common_grid(xg, xf, budget)
    vg = [hold(xg, yg, t) for t in grid]
    vf = [hold(xf, yf, t) for t in grid]
    shaded = sum((grid[k + 1] - grid[k]) * (vf[k] - vg[k])
                 for k in range(len(grid) - 1))

    # the one-sided piece common.auc counts and the shaded area cannot show
    if xf[0] < xg[0]:
        offset_area = (xg[0] - xf[0]) * yf[0]
    elif xg[0] < xf[0]:
        offset_area = -(xf[0] - xg[0]) * yg[0]
    else:
        offset_area = 0.0

    # who gets truncated, and by how much
    discard = {"G": 1.0 - budget / xg[-1], "F": 1.0 - budget / xf[-1]}
    long_arm = "G" if xg[-1] > xf[-1] else ("F" if xf[-1] > xg[-1] else None)

    return {
        "seed": seed,
        "xg": xg, "yg": yg, "xf": xf, "yf": yf,
        "budget": budget, "auc_g": auc_g, "auc_f": auc_f,
        "ratio": ratio, "delta": delta, "positive": auc_f > auc_g,
        "grid": grid, "vg": vg, "vf": vf,
        "shaded": shaded, "offset_area": offset_area,
        "offset_evals": xf[0] - xg[0],
        "offset_share": 100.0 * offset_area / delta if delta else 0.0,
        "sign_flip": (shaded > 0) != (delta > 0) and shaded != 0 and delta != 0,
        "discard": discard, "long_arm": long_arm,
        "end_ev": max(xg[-1], xf[-1]),
    }


# --------------------------------------------------------------------------
# one panel
# --------------------------------------------------------------------------
def signed_runs(grid, vg, vf):
    """Maximal runs of intervals with a constant lead, as (sign, k0, k1)."""
    out = []
    for k in range(len(grid) - 1):
        s = (vf[k] > vg[k]) - (vf[k] < vg[k])
        if out and out[-1][0] == s:
            out[-1][2] = k
        else:
            out.append([s, k, k])
    return out


def draw_panel(ax, d):
    grid, vg, vf = d["grid"], d["vg"], d["vf"]
    budget, end_ev = d["budget"], d["end_ev"]

    # ---- signed area between the curves ----------------------------------
    for sign, k0, k1 in signed_runs(grid, vg, vf):
        if sign == 0:
            continue
        px, lo, hi = [], [], []
        for k in range(k0, k1 + 1):
            px += [grid[k], grid[k + 1]]
            lo += [vg[k], vg[k]]
            hi += [vf[k], vf[k]]
        ax.fill_between(px, lo, hi, lw=0, zorder=2,
                        facecolor=C.ARM_COLOR["F" if sign > 0 else "G"],
                        alpha=FILL_ALPHA)

    # ---- the discarded tail ----------------------------------------------
    if end_ev > budget:
        ax.axvspan(budget, end_ev, facecolor=C.C_GREY, alpha=0.10, lw=0,
                   zorder=1)

    # ---- curves: full run faded, the part AUC actually scores solid -------
    for arm, xs, ys in (("G", d["xg"], d["yg"]), ("F", d["xf"], d["yf"])):
        ax.plot(xs, ys, drawstyle="steps-post", color=C.ARM_COLOR[arm],
                lw=1.6, alpha=FADE, zorder=3)
        kept = [x for x in xs if x <= budget]
        if kept and kept[-1] < budget:
            kept.append(budget)
        ax.plot(kept, [hold(xs, ys, t) for t in kept], drawstyle="steps-post",
                color=C.ARM_COLOR[arm], lw=2.4, zorder=4,
                solid_joinstyle="miter")

    # ---- B* -------------------------------------------------------------
    ax.axvline(budget, color="#1A1A1A", ls=(0, (5, 3)), lw=1.7, zorder=5)

    # ---- axes -------------------------------------------------------------
    y_lo = min(d["yg"][0], d["yf"][0])
    y_hi = max(max(d["yg"]), max(d["yf"]))
    span = y_hi - y_lo
    ax.set_ylim(y_lo - 0.10 * span, y_hi + 0.13 * span)
    x_lo = min(d["xg"][0], d["xf"][0])
    x_span = end_ev - x_lo
    ax.set_xlim(x_lo - 0.05 * x_span, end_ev + 0.05 * x_span)
    ax.xaxis.set_major_locator(MaxNLocator(4, integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(6))
    ax.xaxis.set_major_formatter(COMMA)
    ax.yaxis.set_major_formatter(COMMA)
    ax.tick_params(labelsize=11.5)
    ax.set_xlabel("cumulative completed evaluations", fontsize=12.5)
    ax.set_title(f"seed {d['seed']}", pad=9)

    # ---- the verdict for this seed ---------------------------------------
    ax.text(0.035, 0.965, f"AUC F/G = {d['ratio']:.4f}", transform=ax.transAxes,
            ha="left", va="top", fontsize=14, fontweight="bold", zorder=7)
    ax.text(0.035, 0.885,
            "AUC-positive" if d["positive"] else "AUC-negative",
            transform=ax.transAxes, ha="left", va="top", fontsize=12.5,
            fontweight="bold", zorder=7,
            color=C.CAT_COLOR["better" if d["positive"] else "worse"])

    # ---- B* label, in the empty low-right corner --------------------------
    ax.text(budget, 0.025, f"B* = {budget:,}",
            transform=ax.get_xaxis_transform(), rotation=90, ha="right",
            va="bottom", fontsize=11.5, zorder=7, color="#1A1A1A",
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.6))

    # ---- the two caveats, stacked in the empty lower-right corner ---------
    notes = []
    arm = d["long_arm"]
    if arm is not None and 100.0 * d["discard"][arm] >= DISCARD_MIN:
        notes.append((f"B* discards {100 * d['discard'][arm]:.1f} %\n"
                      f"of arm {arm}'s evaluations", C.C_RED))
    if abs(d["offset_share"]) >= OFFSET_MIN:
        msg = (f"start offset, unshaded:\n"
               f"{abs(d['offset_evals'])} evals = "
               f"{d['offset_share']:+.0f} % of the gap")
        if d["sign_flip"]:
            msg += "\nand it sets the sign"
        notes.append((msg, C.C_PURPLE))

    note_y = 0.245
    for msg, colour in notes:
        ax.text(0.975, note_y, msg, transform=ax.transAxes, ha="right",
                va="bottom", fontsize=11.5, color=colour, zorder=7,
                linespacing=1.35,
                bbox=dict(fc="white", ec=colour, lw=0.8, alpha=0.92,
                          boxstyle="round,pad=0.3"))
        note_y += 0.048 * (msg.count("\n") + 1) + 0.048


# --------------------------------------------------------------------------
# layout audit -- measured, not eyeballed
# --------------------------------------------------------------------------
def _drawn_ticklabels(ax):
    """Only tick labels that actually render.

    ``get_xticklabels`` also hands back ticks the locator produced just outside
    the view interval; those are never drawn, and counting them would invent
    overflows and overlaps that are not in the PNG.
    """
    out = []
    for axis, lim in ((ax.xaxis, ax.get_xlim()), (ax.yaxis, ax.get_ylim())):
        lo, hi = min(lim), max(lim)
        for tick in axis.get_major_ticks():
            loc = tick.get_loc()
            if loc is None or not (lo <= loc <= hi):
                continue
            for lab in (tick.label1, tick.label2):
                if lab.get_visible() and lab.get_text().strip():
                    out.append(lab)
    return out


def _measured_artists(fig):
    """[(tag, artist)] for every visible text and legend, legends atomic."""
    items, inside_legend = [], set()
    legends = list(fig.legends) + [ax.get_legend() for ax in fig.axes]
    for i, lg in enumerate(l for l in legends if l is not None):
        inside_legend.update(id(t) for t in lg.get_texts())
        items.append((f"legend{i}", lg))

    seen = set()

    def add(tag, t):
        if t is None or id(t) in inside_legend or id(t) in seen:
            return
        if not t.get_visible() or not t.get_text().strip():
            return
        seen.add(id(t))
        items.append((tag, t))

    add("suptitle", getattr(fig, "_suptitle", None))
    for t in fig.texts:
        add("fig.text", t)
    for i, ax in enumerate(fig.axes):
        add(f"ax{i}.title", ax.title)
        add(f"ax{i}.xlabel", ax.xaxis.label)
        add(f"ax{i}.ylabel", ax.yaxis.label)
        for t in ax.texts:
            add(f"ax{i}.text", t)
        for t in _drawn_ticklabels(ax):
            add(f"ax{i}.tick[{t.get_text()}]", t)
    return items


def audit_layout(fig, tol=0.5):
    """Print `overflow artists: N, text-pair overlaps: N` and the offenders."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    w, h = fig.canvas.get_width_height()

    boxes = []
    for tag, art in _measured_artists(fig):
        try:
            bb = art.get_window_extent(rend)
        except TypeError:
            bb = art.get_window_extent()
        boxes.append((tag, art, bb))

    overflow = [(tag, bb) for tag, _a, bb in boxes
                if bb.x0 < -tol or bb.y0 < -tol
                or bb.x1 > w + tol or bb.y1 > h + tol]

    overlaps = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][2], boxes[j][2]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox > tol and oy > tol:
                overlaps.append((boxes[i][0], boxes[j][0], ox * oy))

    smallest_tick = min((t.get_fontsize() for ax in fig.axes
                         for t in _drawn_ticklabels(ax)),
                        default=float("nan"))

    print(f"  layout: canvas {w}x{h} px | overflow artists: {len(overflow)}, "
          f"text-pair overlaps: {len(overlaps)} | "
          f"artists measured: {len(boxes)} | "
          f"smallest tick label: {smallest_tick:.1f} pt")
    for tag, bb in overflow:
        print(f"    OVERFLOW {tag}: [{bb.x0:.1f},{bb.y0:.1f},"
              f"{bb.x1:.1f},{bb.y1:.1f}] vs canvas {w}x{h}")
    for a, b, area in overlaps:
        print(f"    OVERLAP  {a} <-> {b}  ({area:.0f} px^2)")
    return len(overflow), len(overlaps)


# --------------------------------------------------------------------------
def main():
    facts = [seed_facts(s) for s in C.SEEDS]
    n_pos = sum(1 for d in facts if d["positive"])

    fig, axes = C.new_fig(1, 5, figsize=(24.0, 7.2))
    fig.subplots_adjust(left=0.052, right=0.988, top=0.780, bottom=0.108,
                        wspace=0.260)
    for ax, d in zip(axes, facts):
        draw_panel(ax, d)
    axes[0].set_ylabel("best GFLOP/s so far", fontsize=13.5)

    fig.legend(handles=[
        mlines.Line2D([], [], color=C.ARM_COLOR["G"], lw=2.6,
                      label="arm G (baseline) best-so-far"),
        mlines.Line2D([], [], color=C.ARM_COLOR["F"], lw=2.6,
                      label="arm F (guided) best-so-far"),
        mpatches.Patch(facecolor=C.ARM_COLOR["F"], alpha=FILL_ALPHA,
                       label="F ahead of G"),
        mpatches.Patch(facecolor=C.ARM_COLOR["G"], alpha=FILL_ALPHA,
                       label="G ahead of F"),
        mlines.Line2D([], [], color="#1A1A1A", ls=(0, (5, 3)), lw=1.7,
                      label="B* truncation point"),
        mpatches.Patch(facecolor=C.C_GREY, alpha=0.25,
                       label="evaluations discarded by B*"),
    ], loc="upper center", bbox_to_anchor=(0.5, 0.884), ncol=6, fontsize=12.5,
        frameon=True, framealpha=0.95, borderaxespad=0.0, handlelength=2.4)

    fig.suptitle(
        f"AUC by seed — {BLOCK}:  {n_pos}/{len(C.SEEDS)} seeds AUC-positive",
        x=0.5, y=0.990, va="top", fontsize=20)
    fig.text(0.5, 0.944,
             "step-hold integral of best_gflops_so_far against cumulative "
             "completed evaluations, truncated at "
             "B* = the smaller of the two arms' final evaluation counts\n"
             "shaded area between the curves = the AUC difference over the "
             "evaluation range both arms cover   ·   "
             "y-axis starts at the lower Gen0 value, not at zero",
             ha="center", va="top", fontsize=12.5, color=C.C_GREY,
             linespacing=1.45)

    C.provenance(fig, f"trajectory.jsonl · {SRC_TAG} · {SHAPE} · "
                      f"seeds 24001-24005 · AUC via common.auc()")

    for d in facts:
        print(f"  seed {d['seed']}:  B* = {d['budget']:>6,}  "
              f"AUC G = {d['auc_g']:>14,.1f}  F = {d['auc_f']:>14,.1f}  "
              f"F/G = {d['ratio']:.6f}  "
              f"{'POSITIVE' if d['positive'] else 'negative'}  |  "
              f"discard G {100 * d['discard']['G']:5.2f} % / "
              f"F {100 * d['discard']['F']:5.2f} %  |  "
              f"shaded {d['shaded']:+,.1f}  "
              f"start offset {d['offset_evals']:+d} evals "
              f"({d['offset_area']:+,.1f}, {d['offset_share']:+.2f} % of gap)"
              f"{'  <-- offset flips the sign' if d['sign_flip'] else ''}")
    print(f"  {BLOCK}: AUC-positive {n_pos}/{len(C.SEEDS)}")
    audit_layout(fig)
    C.save(fig, OUT, tight=False)


if __name__ == "__main__":
    main()
