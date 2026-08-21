"""P8 -- the three problem shapes are three regimes, not a sweep.

The study runs three deliberately divergent shapes rather than a smooth size
sweep, so "it scales" is never inferred from interpolation between neighbours:

    tiny    8 x 8 x 1 x 128            exploratory  (not in the gate)
    medium  256 x 256 x 1 x 1024       confirmatory
    large   2304 x 1024 x 1 x 214336   confirmatory

Three log axes, one per quantity, so each span is stated in its own units and
its own decades. The deck used to say "five orders" without naming the
quantity: K spans 3.2 decades, and it is the *measured throughput* R_s that
spans five (5.4 decades). This figure prints the multiple and the decade count
under every panel so the two can never be conflated again.

Data: problem sizes and R_s come from the shape record in the baseline
campaign; shape roles come from the shipped per-shape guidance files.

Run on the HOST (matplotlib 3.8.2). Idempotent: no timestamps, no randomness.
"""
from __future__ import annotations

import math

from matplotlib.ticker import LogLocator, NullFormatter
from matplotlib.transforms import Bbox

import common
from common import C_BLUE, C_GREY, C_ORANGE, C_RED

INK = "#2B2B2B"
SHAPES = ["tiny", "medium", "large"]

ROLE_STYLE = {
    # role -> (colour, filled, marker, gate note)
    "confirmatory": (C_BLUE, True, "o", "in the gate"),
    "exploratory": (C_ORANGE, False, "D", "not in the gate"),
}


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def shape_records():
    """{shape: {'size', 'K', 'flops', 'R_s', 'role'}} -- all read at render time.

    Only `size` and `R_s` are taken from the campaign shape record; the role is
    the shipped guidance file's own `shape_role`.
    """
    rec = common.per_shape_noise()
    out = {}
    for s in SHAPES:
        m, n, b, k = rec[s]["size"]
        out[s] = {
            "size": (m, n, b, k),
            "K": k,
            "flops": 2.0 * m * n * b * k,
            "R_s": float(rec[s]["R_s"]),
            "role": common.guidance(s)["shape_role"],
        }
    return out


REC = shape_records()

# y positions: tiny on top, large at the bottom (reading order = growing size)
YPOS = {"tiny": 2, "medium": 1, "large": 0}


def _fmt(v):
    if v >= 1e6:
        return "%.3g" % v
    if v == int(v):
        return "{:,}".format(int(v))
    return "%.6g" % v


def span(key):
    vals = [REC[s][key] for s in SHAPES]
    lo, hi = min(vals), max(vals)
    return lo, hi, hi / lo, math.log10(hi / lo)


PANELS = [
    ("K", "K  (reduction depth)", "K", False),
    ("flops", "total FLOPs  (2·M·N·B·K)", "FLOPs", False),
    ("R_s", "throughput  R$_s$  (GFLOP/s)", "GFLOP/s", True),
]

# --------------------------------------------------------------------------
# figure
# --------------------------------------------------------------------------
fig, axes = common.new_fig(1, 3, figsize=(13.0, 5.2), sharey=True)

for ax, (key, title, unit, is_five) in zip(axes, PANELS):
    lo, hi, mult, dec = span(key)
    ax.set_xscale("log")
    # generous log padding: room for the value label above each marker
    ax.set_xlim(lo / 10 ** (0.30 * dec + 0.35), hi * 10 ** (0.30 * dec + 0.35))
    ax.set_ylim(-1.35, 2.95)
    # sparse decade ticks: three log panels side by side, so neighbouring
    # panels' tick labels must not run into each other
    step = max(1, int(math.ceil((dec + 0.7) / 4.0)))
    ax.xaxis.set_major_locator(LogLocator(base=10.0, numticks=6,
                                          subs=(1.0,)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    lo_e = int(math.floor(math.log10(ax.get_xlim()[0])))
    hi_e = int(math.ceil(math.log10(ax.get_xlim()[1])))
    ax.set_xticks([10.0 ** e for e in range(lo_e, hi_e + 1, step)])

    if is_five:
        ax.set_facecolor("#FFF6EC")   # the five-order panel, tinted

    for s in SHAPES:
        colour, filled, marker, _ = ROLE_STYLE[REC[s]["role"]]
        y, v = YPOS[s], REC[s][key]
        ax.plot([v], [y], marker=marker, ms=13, zorder=4,
                mfc=(colour if filled else "white"), mec=colour, mew=2.2,
                linestyle="none")
        ax.text(v, y + 0.24, _fmt(v), ha="center", va="bottom",
                fontsize=11.5, color=INK, zorder=5)

    # the span, stated in its own units and its own decades
    ax.annotate("", xy=(lo, -0.55), xytext=(hi, -0.55),
                arrowprops=dict(arrowstyle="<->", color=C_GREY, lw=1.4,
                                shrinkA=0, shrinkB=0))
    ax.vlines([lo, hi], -0.78, -0.32, color=C_GREY, lw=1.2)
    ax.text(math.sqrt(lo * hi), -0.98,
            "span  ×%s   (%.1f decades)" % ("{:,}".format(int(round(mult))), dec),
            ha="center", va="top", fontsize=12.5,
            color=(C_RED if is_five else C_GREY),
            fontweight=("bold" if is_five else "normal"))

    ax.set_title(title, fontsize=14, pad=9)
    ax.set_xlabel(unit, fontsize=12.5)
    ax.grid(axis="x", which="major", alpha=0.25)
    ax.grid(axis="y", visible=False)

axes[2].text(0.5, 0.985, "this is the five-order quantity",
             transform=axes[2].transAxes, ha="center", va="top",
             fontsize=12.5, color=C_RED, fontweight="bold")

# y ticks carry the shape identity, its size and its role
axes[0].set_yticks([YPOS[s] for s in SHAPES])
axes[0].set_yticklabels(
    ["%s\n%s\n%s – %s" % (s, "×".join(str(x) for x in REC[s]["size"]),
                          REC[s]["role"], ROLE_STYLE[REC[s]["role"]][3])
     for s in SHAPES], fontsize=11.5)
for lab, s in zip(axes[0].get_yticklabels(), SHAPES):
    lab.set_color(ROLE_STYLE[REC[s]["role"]][0])

# gaps between neighbours: the point that this is not a smooth sweep
gapK = [REC["medium"]["K"] / REC["tiny"]["K"], REC["large"]["K"] / REC["medium"]["K"]]
axes[0].text(0.5, 0.985,
             "neighbour gaps in K:  ×%.0f  then  ×%.0f" % (gapK[0], gapK[1]),
             transform=axes[0].transAxes, ha="center", va="top",
             fontsize=12, color=INK)

fig.suptitle("Three regimes, not a sweep – and R$_s$, not K, is the quantity "
             "that spans five orders", fontsize=16.5, y=0.985)
common.provenance(fig, "260809-s14-pershape-baseline shape record (size, R_s) | "
                       "260809-s14-pershape-guidance/out-capped/guidance-*.json "
                       "(shape_role)")
fig.subplots_adjust(left=0.215, right=0.978, top=0.815, bottom=0.180, wspace=0.20)


# --------------------------------------------------------------------------
# programmatic layout check
# --------------------------------------------------------------------------
def layout_report(figure):
    figure.canvas.draw()
    rend = figure.canvas.get_renderer()
    w, h = figure.canvas.get_width_height()
    canvas = Bbox.from_bounds(0, 0, w, h)
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
            items.append(("legend", ax.get_legend().get_window_extent(rend)))
    for t in figure.texts:
        if t.get_visible() and t.get_text().strip():
            items.append(("figtext:%r" % t.get_text()[:26], t.get_window_extent(rend)))

    over = [n for n, b in items
            if b.x0 < -0.5 or b.y0 < -0.5 or b.x1 > w + 0.5 or b.y1 > h + 0.5]
    pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]
            ix = min(a.x1, b.x1) - max(a.x0, b.x0)
            iy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ix > 1.0 and iy > 1.0:
                pairs.append((items[i][0], items[j][0], ix * iy))
    print("layout: canvas %dx%d px, %d text/legend artists" % (w, h, len(items)))
    print("        smallest tick label: %.1f pt (floor 11 pt) -> %s"
          % (smallest, "OK" if smallest >= 11 else "FAIL"))
    print("overflow artists: %d, text-pair overlaps: %d" % (len(over), len(pairs)))
    for n in over:
        print("        OVERFLOW %s -> %s" % (n, canvas))
    for a, b, area in pairs:
        print("        OVERLAP  %s <-> %s  (%.0f px^2)" % (a, b, area))
    return len(over), len(pairs)


layout_report(fig)
common.save(fig, "p08_shape_regimes.png", tight=False)

# --------------------------------------------------------------------------
# stdout
# --------------------------------------------------------------------------
print()
for s in SHAPES:
    r = REC[s]
    print("%-7s %-22s K=%-7d FLOPs=%-11.4g R_s=%-12.6g role=%s (%s)"
          % (s, "×".join(str(x) for x in r["size"]), r["K"], r["flops"],
             r["R_s"], r["role"], ROLE_STYLE[r["role"]][3]))
print()
for key, title, _u, _f in PANELS:
    lo, hi, mult, dec = span(key)
    print("%-6s span  %-12.6g -> %-12.6g  ×%-10s %.2f decades"
          % (key, lo, hi, "{:,}".format(int(round(mult))), dec))
print("neighbour gaps in K: tiny->medium ×%.0f, medium->large ×%.0f "
      "(a sweep would be even; these are not)" % (gapK[0], gapK[1]))
print("gate membership: %s confirmatory, %s exploratory"
      % (", ".join(s for s in SHAPES if REC[s]["role"] == "confirmatory"),
         ", ".join(s for s in SHAPES if REC[s]["role"] == "exploratory")))
