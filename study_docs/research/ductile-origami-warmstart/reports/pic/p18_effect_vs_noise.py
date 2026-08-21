"""P18 -- per-seed effect against that seed's own measured noise, all four blocks.

One panel per block. x = seed, y = ln(F/G). The null is drawn as shaded noise, so
only what protrudes beyond the shading counts as a call.

Three things the naive version of this figure gets wrong, and how it is done here:

1.  The two nulls are NOT nested. G/G' is the *wider* null on 6 of the 20
    seed-cells, so drawing one inside the other and relying on z-order would hide
    a band on those six. They are drawn side by side as half-width bars at each
    seed position, each with its own fill, edge colour and hatch, so which one is
    wider is read off the figure rather than assumed.
2.  The band is +/-2 sd with a +/-3 sd whisker, not +/-1 sd. At +/-1 sd, 11 of the
    20 seed-cells protrude, which would make "protruding = real" meaningless.
    2x / 3x is the convention already registered in this deck.
3.  It is two-sided. Two of the seven protrusions are arm F *losing* (large capped
    24001 and 24004). Solid up = F ahead, solid down = F behind, hollow = inside
    the noise and no call is made either way.

Every band uses that seed's *own* null sd. Null width varies ~12x across seeds
inside a single block, so a block median would misdraw both ends of that range.

Run on the HOST (matplotlib 3.8.2). Idempotent: no timestamps, no randomness.
"""
from __future__ import annotations

import math
from statistics import median

from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

import common
from common import ARM_COLOR, CAT_COLOR, C_GREY, SEEDS

INK = "#2B2B2B"
C_WIN = CAT_COLOR["better"]
C_LOSS = CAT_COLOR["worse"]

BAND_K = 2.0      # shaded half-width, in sd
WHISK_K = 3.0     # whisker tick, in sd

MEDIUM_BADGE = ("repaired  nw=1400 / RBS=401\n"
                "cross-window mean, 12 windows")
LARGE_BADGE = ("unmodified  nw=321 / RBS=0\n"
               "single-window endpoint")


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def medium_capped_effect():
    """Mean of the two nw=1400/RBS=401 capped cells."""
    a, b = common.cell_per_seed("C03_"), common.cell_per_seed("C03CONF_")
    return {s: 0.5 * (a[s]["mean_ln"] + b[s]["mean_ln"]) for s in SEEDS}


def medium_native_effect():
    c = common.cell_per_seed("STAGE2_NATIVE_")
    return {s: c[s]["mean_ln"] for s in SEEDS}


def large_effect(cell):
    """large cells use a different schema -- never index ['mean_ln'] on these."""
    c = common.cell_per_seed(cell, root=common.XWIN)
    return {s: c[s]["canonical_endpoint_ln_F_over_G"] for s in SEEDS}


def medium_null(cell):
    c = common.cell_per_seed(cell)
    return {s: c[s]["sample_sd"] for s in SEEDS}


def large_null(cell):
    c = common.cell_per_seed(cell, root=common.XWIN)
    return {s: c[s]["sample_sd_ln_F_over_G"] for s in SEEDS}


BLOCKS = [
    dict(key="medium capped", title="medium  ·  capped",
         badge=MEDIUM_BADGE, truth=1.0135,
         eff=medium_capped_effect(),
         gg=medium_null("N7_GVSG_"), ff=medium_null("N7b_FFNULL_")),
    dict(key="large capped", title="large  ·  capped",
         badge=LARGE_BADGE, truth=1.0006,
         eff=large_effect("m6_capped"),
         gg=large_null("gvsg_capped"), ff=large_null("ffnull_capped")),
    dict(key="medium native", title="medium  ·  native",
         badge=MEDIUM_BADGE, truth=1.0036,
         eff=medium_native_effect(),
         gg=medium_null("N8_NATIVE_GVSG_"), ff=medium_null("N8b_NATIVE_FFNULL_"),
         caption="near-solid band on purpose, not a rendering fault:\n"
                 "F/F′ null sd is 0.017–0.095 against effects ≤ 0.125.\n"
                 "a null that noisy cannot calibrate anything — 0/5 seeds separable."),
    dict(key="large native", title="large  ·  native",
         badge=LARGE_BADGE, truth=0.9970,
         eff=large_effect("m6"),
         gg=large_null("gvsg_native"), ff=large_null("ffnull_native")),
]

for b in BLOCKS:
    b["wider"] = {s: ("G/G′" if b["gg"][s] > b["ff"][s] else "F/F′")
                  for s in SEEDS}
    b["gate"] = {s: BAND_K * max(b["gg"][s], b["ff"][s]) for s in SEEDS}
    b["call"] = {s: ("up" if b["eff"][s] > b["gate"][s] else
                     "down" if b["eff"][s] < -b["gate"][s] else "in")
                 for s in SEEDS}
    b["median_ln"] = median(b["eff"][s] for s in SEEDS)
    b["npos"] = sum(1 for s in SEEDS if b["eff"][s] > 0)

N_INVERSION = sum(1 for b in BLOCKS for s in SEEDS if b["wider"][s] == "G/G′")


# --------------------------------------------------------------------------
# figure
# --------------------------------------------------------------------------
fig, axes = common.new_fig(2, 2, figsize=(13.6, 9.8))
AX = [axes[0][0], axes[0][1], axes[1][0], axes[1][1]]

HALF = 0.44          # half slot width
GAP = 0.022          # gap between the two side-by-side bands
BBOX = dict(fc="white", ec="none", alpha=0.90, pad=2.0)

for ax, blk in zip(AX, BLOCKS):
    span = max(max(WHISK_K * max(blk["gg"][s], blk["ff"][s]) for s in SEEDS),
               max(abs(blk["eff"][s]) for s in SEEDS))
    lim = 1.66 * span

    ax.axhline(0.0, color=INK, lw=1.1, alpha=0.65, zorder=3)

    for i, s in enumerate(SEEDS):
        for sd, colour, hatch, side in (
                (blk["gg"][s], ARM_COLOR["G"], "///", -1),
                (blk["ff"][s], ARM_COLOR["F"], "\\\\\\", +1)):
            x0 = i + GAP if side > 0 else i - HALF
            ax.add_patch(Rectangle((x0, -BAND_K * sd), HALF - GAP, 2 * BAND_K * sd,
                                   facecolor=colour, alpha=0.20, edgecolor=colour,
                                   linewidth=1.0, hatch=hatch, zorder=2))
            xc = x0 + 0.5 * (HALF - GAP)
            for sign in (-1, +1):
                ax.plot([xc, xc], [sign * BAND_K * sd, sign * WHISK_K * sd],
                        color=colour, lw=1.1, zorder=2, solid_capstyle="butt")
                ax.plot([xc - 0.09, xc + 0.09], [sign * WHISK_K * sd] * 2,
                        color=colour, lw=1.4, zorder=2)

        e, call = blk["eff"][s], blk["call"][s]
        line_c = C_WIN if call == "up" else C_LOSS if call == "down" else INK
        ax.hlines(e, i - HALF, i + HALF, color=line_c, lw=2.4,
                  alpha=1.0 if call != "in" else 0.75, zorder=6)
        if call == "in":
            ax.plot([i], [e], marker="o", ms=9.0, mfc="white", mec=INK,
                    mew=1.6, ls="none", zorder=7)
        else:
            ax.plot([i], [e], marker="^" if call == "up" else "v", ms=11.5,
                    mfc=line_c, mec="white", mew=1.1, ls="none", zorder=7)

    ax.set_xticks(range(len(SEEDS)))
    ax.set_xticklabels([str(s) for s in SEEDS])
    ax.set_xlim(-0.62, len(SEEDS) - 0.38)
    ax.set_ylim(-lim, lim)
    ax.tick_params(axis="both", labelsize=12)
    ax.set_ylabel("ln(F/G)")
    ax.set_title(blk["title"], pad=9)

    ax.text(0.014, 0.975, blk["badge"], transform=ax.transAxes, ha="left",
            va="top", fontsize=10.5, color=C_GREY, linespacing=1.35,
            zorder=9, bbox=BBOX)
    ax.text(0.986, 0.975,
            "median F/G  %.4f\n%d/5 seeds F ahead" % (math.exp(blk["median_ln"]),
                                                      blk["npos"]),
            transform=ax.transAxes, ha="right", va="top", fontsize=11.5,
            color=INK, linespacing=1.35, zorder=9, bbox=BBOX)
    if blk.get("caption"):
        ax.text(0.5, 0.022, blk["caption"], transform=ax.transAxes, ha="center",
                va="bottom", fontsize=10.5, color=C_LOSS, linespacing=1.35,
                zorder=9, bbox=dict(fc="white", ec=C_LOSS, lw=0.8, alpha=0.94,
                                    pad=3.0))

AX[2].set_xlabel("seed")
AX[3].set_xlabel("seed")

handles = [
    Rectangle((0, 0), 1, 1, facecolor=ARM_COLOR["G"], alpha=0.20,
              edgecolor=ARM_COLOR["G"], hatch="///"),
    Rectangle((0, 0), 1, 1, facecolor=ARM_COLOR["F"], alpha=0.20,
              edgecolor=ARM_COLOR["F"], hatch="\\\\\\"),
    Line2D([], [], marker="^", ms=11, mfc=C_WIN, mec="white", ls="none"),
    Line2D([], [], marker="v", ms=11, mfc=C_LOSS, mec="white", ls="none"),
    Line2D([], [], marker="o", ms=9, mfc="white", mec=INK, mew=1.6, ls="none"),
]
labels = [
    "G/G′ null ±2 sd (±3 sd whisker)",
    "F/F′ null ±2 sd (±3 sd whisker)",
    "clears both nulls: F ahead",
    "clears both nulls: F behind",
    "inside noise: no call",
]
fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.905),
           ncol=5, frameon=True, framealpha=0.95, fontsize=11,
           handletextpad=0.5, columnspacing=1.1, borderpad=0.55)

fig.suptitle("Per-seed effect against that seed’s own measured noise", y=0.988,
             fontsize=19)
fig.text(0.5, 0.958,
         "bands are per-seed, never a block median — null width varies ≈ 12× "
         "across seeds.  the two nulls are side by side because they do not\n"
         "nest: G/G′ is the wider one on %d of 20 seed-cells.  both nulls are "
         "cross-window everywhere, but medium and large are different\n"
         "instruments (see badges), so the panels are not directly comparable.  "
         "y-scale is per panel." % N_INVERSION,
         ha="center", va="top", fontsize=10.5, color=C_GREY, linespacing=1.4)

common.provenance(fig, "medium_pilot401 C03 / C03CONF / STAGE2_NATIVE + N7, N7b, "
                       "N8, N8b nulls  |  large_xwindow m6 / m6_capped + gvsg, "
                       "ffnull nulls")
fig.subplots_adjust(left=0.070, right=0.988, top=0.818, bottom=0.088,
                    hspace=0.40, wspace=0.19)


# --------------------------------------------------------------------------
# layout check: every text / legend bbox against the canvas and against itself
# --------------------------------------------------------------------------
def _on_view_ticklabels(a):
    """Only the tick labels matplotlib actually draws (locator can emit ticks
    outside the view limits; those Text objects still carry stale positions and
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
common.save(fig, "p18_effect_vs_noise.png", tight=False)

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
print("per-seed effect ln(F/G), null sds, and the +/-2 sd call")
for b in BLOCKS:
    print("  %-14s" % b["key"])
    for s in SEEDS:
        print("    %d  eff %+.6f | G/G' sd %.6f  F/F' sd %.6f | wider %s | "
              "2sd gate %.6f | %s"
              % (s, b["eff"][s], b["gg"][s], b["ff"][s], b["wider"][s],
                 b["gate"][s], {"up": "F AHEAD", "down": "F BEHIND",
                                "in": "inside"}[b["call"][s]]))
    print("    median ln %+.6f -> F/G %.4f (truth %.4f)  %d/5 positive  "
          "null-width spread %.1fx"
          % (b["median_ln"], math.exp(b["median_ln"]), b["truth"], b["npos"],
             max(max(b["gg"][s], b["ff"][s]) for s in SEEDS)
             / min(min(b["gg"][s], b["ff"][s]) for s in SEEDS)))

print()
print("nesting inversions (G/G' wider than F/F'): %d of 20 seed-cells" % N_INVERSION)
for b in BLOCKS:
    inv = [s for s in SEEDS if b["wider"][s] == "G/G′"]
    print("  %-14s %s" % (b["key"], inv if inv else "none"))

print()
_calls = [(b["key"], s, b["call"][s]) for b in BLOCKS for s in SEEDS
          if b["call"][s] != "in"]
print("protruding at +/-2 sd: %d of 20  (up %d, down %d)"
      % (len(_calls), sum(1 for c in _calls if c[2] == "up"),
         sum(1 for c in _calls if c[2] == "down")))
for k, s, c in _calls:
    print("  %-14s %d  %s" % (k, s, c))
_one = sum(1 for b in BLOCKS for s in SEEDS
           if abs(b["eff"][s]) > max(b["gg"][s], b["ff"][s]))
print("for comparison, at +/-1 sd: %d of 20 protrude" % _one)
