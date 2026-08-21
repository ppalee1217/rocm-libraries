"""P10 -- the prior-to-weight inversion, verified end to end on the shipped file.

Ductile does not accept probabilities. Its config field is `weights`, and at
sampling time it applies

        p_realised(v)  =  exp(-beta * (w_v - min_u w_u)) / sum_u exp(...)     beta = 0.25

so a *lower* weight yields a *higher* sampling probability -- the field is
cost-like, not preference-like. Feeding the intended prior in directly would
therefore make the model's best value the least likely draw. The derivation
emits the inverse instead:

        w_v  =  -4 * ln p1(v)          ( = -(1/beta) * ln p1(v) )

This is the pipeline step most likely to be got wrong, and it would fail
silently: a reversed emission still produces a valid config, a valid run and a
plausible number. So the figure walks the whole chain on the shipped artifact
and closes the loop -- it recomputes the realised probability by applying
Ductile's own transform to the weights that were actually emitted, and checks
that it lands back on the intended prior.

Top row  : the chain for medium's DepthU (6 values) -- intended -> emitted -> realised.
Bottom   : the non-inverted counterfactual (order reverses), medium's
           1LDSBuffer (2 values), and a NON-activated gene, which must come out
           exactly uniform -- that is what confines the treatment to activated genes.

Nothing here is hardcoded: beta is read from the guidance file's `weight_beta`,
and every probability is recomputed from `weights_float32`.

Run on the HOST (matplotlib 3.8.2). Idempotent: no timestamps, no randomness.
"""
from __future__ import annotations

import math

import numpy as np
from matplotlib.transforms import Bbox

import common
from common import C_BLUE, C_GREEN, C_GREY, C_ORANGE, C_RED

INK = "#2B2B2B"
SHAPE = "medium"

G = common.guidance(SHAPE)
BETA = float(G["weight_beta"])          # Ductile's own exponent, from the file
GENES = G["genes"]

CHAIN_GENE = "DepthU"                   # 6 values, activated
SMALL_GENE = "1LDSBuffer"               # 2 values, activated
OFF_GENE = "WaveSeparateGlobalReadA"    # 2 values, NOT activated


# --------------------------------------------------------------------------
# Ductile's transform, reimplemented exactly as the tool applies it
# --------------------------------------------------------------------------
def ductile_probability(weights, beta=BETA):
    """weights -> sampling probability.  exp(-beta*(w - w.min())), renormalised."""
    w = np.asarray(weights, dtype=float)
    e = np.exp(-beta * (w - w.min()))
    return e / e.sum()


def emitted_weight(p, beta=BETA):
    """The derivation's emission rule:  w = -(1/beta) * ln p   ( = -4 ln p )."""
    return -np.log(np.asarray(p, dtype=float)) / beta


def gene(name):
    g = GENES[name]
    p1 = np.asarray(g["p1"], dtype=float)
    w = np.asarray(g["weights_float32"], dtype=float)
    return {
        "name": name,
        "n": len(p1),
        "p0": np.asarray(g["p0"], dtype=float),
        "p1": p1,
        "w": w,
        "realised": ductile_probability(w),
        # the counterfactual: emit the prior itself into the `weights` field
        "naive": ductile_probability(p1),
        "activated": bool(g["activated"]),
        "best": g["candidate_order"].index(g["best"]),
        "worst": g["candidate_order"].index(g["worst"]),
        "order": g["candidate_order"],
    }


CH = gene(CHAIN_GENE)
SM = gene(SMALL_GENE)
OF = gene(OFF_GENE)

# closure error over every gene on the shape, not just the three plotted
ALL_DEV = {k: float(np.max(np.abs(ductile_probability(v["weights_float32"])
                                  - np.asarray(v["p1"], dtype=float))))
           for k, v in GENES.items()}
MAXDEV = max(ALL_DEV.values())
MAXDEV_GENE = max(ALL_DEV, key=ALL_DEV.get)
ACT_DEV = max(ALL_DEV[k] for k, v in GENES.items() if v["activated"])
OFF_DEV = max(float(np.max(np.abs(ductile_probability(v["weights_float32"])
                                  - 1.0 / len(v["p1"]))))
              for k, v in GENES.items() if not v["activated"])
# the emission rule itself, checked against the float32 values in the file
RULE_DEV = max(float(np.max(np.abs(emitted_weight(v["p1"])
                                   - np.asarray(v["weights_float32"], dtype=float))))
               for v in GENES.values())


def vlabels(g):
    out = []
    for i in range(g["n"]):
        tag = ""
        if g["activated"] and i == g["best"]:
            tag = "  (best)"
        elif g["activated"] and i == g["worst"]:
            tag = "  (worst)"
        out.append("v%d%s" % (i + 1, tag))
    return out


# --------------------------------------------------------------------------
# figure
# --------------------------------------------------------------------------
fig, axg = common.new_fig(2, 3, figsize=(14.4, 8.6),
                          gridspec_kw={"height_ratios": [1.0, 0.92]})
(axA, axB, axC), (axD, axE, axF) = axg

Y = np.arange(CH["n"])[::-1]   # v1 at the top

# ---- (1) intended prior ---------------------------------------------------
axA.barh(Y, CH["p1"], height=0.62, color=C_BLUE, zorder=3)
for y, v in zip(Y, CH["p1"]):
    axA.text(v + 0.012, y, "%.4f" % v, va="center", ha="left", fontsize=11.5,
             color=INK)
axA.set_xlim(0, max(CH["p1"]) * 1.42)
axA.set_xlabel("probability", fontsize=12.5)
axA.set_title("1.  intended prior  p1\n(what the derivation means)",
              fontsize=13.5, color=C_BLUE, pad=8)

# ---- (2) emitted weight ---------------------------------------------------
axB.barh(Y, CH["w"], height=0.62, color=C_ORANGE, zorder=3)
for y, v in zip(Y, CH["w"]):
    axB.text(v + 0.28, y, "%.3f" % v, va="center", ha="left", fontsize=11.5,
             color=INK)
axB.set_xlim(0, max(CH["w"]) * 1.34)
axB.set_xlabel("weight (Ductile `weights` field)", fontsize=12.5)
axB.set_title("2.  emitted weight  w = -4·ln p1\n(inverted: bigger = less likely)",
              fontsize=13.5, color=C_ORANGE, pad=8)
_ybest = CH["n"] - 1 - CH["best"]
axB.text(CH["w"][CH["best"]] + 2.85, _ybest,
         "← smallest weight = the best value", va="center", ha="left",
         fontsize=11.5, color=C_RED)

# ---- (3) realised probability --------------------------------------------
axC.barh(Y, CH["realised"], height=0.62, color=C_GREEN, zorder=3,
         label="realised (Ductile transform of w)")
axC.plot(CH["p1"], Y, "o", ms=9, mfc="none", mec=C_BLUE, mew=2.2,
         linestyle="none", zorder=5, label="intended p1")
axC.set_xlim(0, max(CH["p1"]) * 2.05)
axC.set_xlabel("probability", fontsize=12.5)
axC.set_title("3.  realised sampling probability\n(lands back on the prior)",
              fontsize=13.5, color=C_GREEN, pad=8)
axC.legend(fontsize=11, loc="lower right", framealpha=0.95)
axC.text(0.975, 0.56,
         "max |realised − intended|\nover all %d genes:  %.2e" % (len(GENES), MAXDEV),
         transform=axC.transAxes, ha="right", va="bottom", fontsize=11.5,
         color=INK, bbox=dict(fc="white", ec=C_GREEN, lw=1.0, alpha=0.95))

for ax in (axA, axB, axC):
    ax.set_yticks(Y)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", alpha=0.25)
axA.set_yticklabels(vlabels(CH), fontsize=11.5)
for ax in (axB, axC):
    ax.tick_params(labelleft=False)

# ---- (4) the counterfactual ----------------------------------------------
axD.barh(Y, CH["naive"], height=0.62, color=C_RED, zorder=3,
         label="realised if w = p1 were emitted")
axD.plot(CH["p1"], Y, "o", ms=9, mfc="none", mec=C_BLUE, mew=2.2,
         linestyle="none", zorder=5, label="intended p1")
axD.set_xlim(0, max(CH["p1"]) * 1.55)
axD.set_yticks(Y)
axD.set_yticklabels(vlabels(CH), fontsize=11.5)
axD.set_xlabel("probability", fontsize=12.5)
axD.grid(axis="y", visible=False)
naive_rank = int(np.argsort(np.argsort(-CH["naive"]))[CH["best"]]) + 1
axD.set_title("the silent failure: NO inversion\n"
              "best value falls to rank %d of %d" % (naive_rank, CH["n"]),
              fontsize=13.5, color=C_RED, pad=8)
axD.legend(fontsize=10.5, loc="lower right", framealpha=0.95)

# ---- (5) the 2-value activated gene --------------------------------------
Y2 = np.arange(SM["n"])[::-1]
axE.barh(Y2 + 0.17, SM["p1"], height=0.30, color=C_BLUE, zorder=3,
         label="intended p1")
axE.barh(Y2 - 0.17, SM["realised"], height=0.30, color=C_GREEN, zorder=3,
         label="realised")
for y, v in zip(Y2, SM["p1"]):
    axE.text(v + 0.012, y + 0.17, "%.6f" % v, va="center", ha="left",
             fontsize=11.5, color=INK)
for y, v in zip(Y2, SM["realised"]):
    axE.text(v + 0.012, y - 0.17, "%.6f" % v, va="center", ha="left",
             fontsize=11.5, color=INK)
axE.set_xlim(0, max(SM["p1"]) * 1.62)
axE.set_ylim(-0.65, SM["n"] - 0.35)
axE.set_yticks(Y2)
axE.set_yticklabels(vlabels(SM), fontsize=11.5)
axE.set_xlabel("probability", fontsize=12.5)
axE.grid(axis="y", visible=False)
axE.set_title("%s – activated, 2 values\nw = %s"
              % (SMALL_GENE, ", ".join("%.4f" % x for x in SM["w"])),
              fontsize=13.5, color=C_GREEN, pad=8)
axE.legend(fontsize=11, loc="lower right", framealpha=0.95)

# ---- (6) a NON-activated gene: exactly uniform ---------------------------
Y3 = np.arange(OF["n"])[::-1]
axF.barh(Y3, OF["realised"], height=0.44, color=C_GREY, zorder=3)
for y, v in zip(Y3, OF["realised"]):
    axF.text(v + 0.035, y, "%.6f" % v, va="center", ha="left", fontsize=11.5,
             color=INK)
axF.vlines(1.0 / OF["n"], -0.42, OF["n"] - 0.58, color=INK, lw=1.6, ls="--",
           zorder=4, label="uniform 1/%d" % OF["n"])
axF.set_xlim(0, 1.0 / OF["n"] * 1.95)
axF.set_ylim(-1.15, OF["n"] - 0.35)
axF.set_yticks(Y3)
axF.set_yticklabels(["v%d" % (i + 1) for i in range(OF["n"])], fontsize=11.5)
axF.set_xlabel("probability", fontsize=12.5)
axF.grid(axis="y", visible=False)
axF.set_title("%s\nNOT activated → exactly uniform" % OFF_GENE,
              fontsize=13.5, color=C_GREY, pad=8)
axF.legend(fontsize=11, loc="upper right", framealpha=0.95)
axF.text(0.03, 0.02, "max deviation from uniform over all\n%d non-activated "
                     "genes:  %.1e"
         % (sum(1 for v in GENES.values() if not v["activated"]), OFF_DEV),
         transform=axF.transAxes, ha="left", va="bottom", fontsize=11,
         color=INK)

fig.suptitle("Prior → weight inversion, verified on the shipped file  "
             "(%s, β = %.2f):  w = −4·ln p1, and the loop closes"
             % (SHAPE, BETA), fontsize=16.5, y=0.975)
fig.text(0.5, 0.923,
         "Ductile applies  p ∝ exp(−β·(w − w.min()))  to its `weights` field, "
         "so a LOWER weight is a HIGHER sampling probability.",
         ha="center", va="center", fontsize=12.5, color=INK)

common.provenance(fig, "260809-s14-pershape-guidance/out-capped/guidance-%s.json "
                       "(p1, weights_float32, weight_beta); realised probability "
                       "recomputed here" % SHAPE)
fig.subplots_adjust(left=0.085, right=0.980, top=0.822, bottom=0.085,
                    hspace=0.62, wspace=0.30)


# --------------------------------------------------------------------------
# programmatic layout check
# --------------------------------------------------------------------------
def layout_report(figure):
    figure.canvas.draw()
    rend = figure.canvas.get_renderer()
    w, h = figure.canvas.get_width_height()
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
            items.append(("legend@" + (ax.get_title()[:14] or "?"),
                          ax.get_legend().get_window_extent(rend)))
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
        print("        OVERFLOW %s" % n)
    for a, b, area in pairs:
        print("        OVERLAP  %s <-> %s  (%.0f px^2)" % (a, b, area))
    return len(over), len(pairs)


layout_report(fig)
common.save(fig, "p10_weight_inversion.png", tight=False)

# --------------------------------------------------------------------------
# stdout
# --------------------------------------------------------------------------
print()
print("Ductile transform: p ∝ exp(-β·(w - w.min())), β = %.2f (weight_beta, "
      "read from guidance-%s.json)" % (BETA, SHAPE))
print("emission rule:     w = -(1/β)·ln p1 = -%.0f·ln p1" % (1.0 / BETA))
print("max |w_file - (-4·ln p1)| over all %d genes = %.3e  (float32 emission)"
      % (len(GENES), RULE_DEV))
print()
hdr = "%-8s %-10s %-11s %-11s %-11s %-11s" % ("gene/val", "p0", "intended p1",
                                              "emitted w", "realised p",
                                              "|dev|")
for g in (CH, SM, OF):
    print("-- %s  (%s, %d values)"
          % (g["name"], "activated" if g["activated"] else "NOT activated", g["n"]))
    print("   " + hdr)
    for i in range(g["n"]):
        dev = abs(g["realised"][i] - g["p1"][i])
        print("   %-8s %-10.6f %-11.6f %-11.6f %-11.6f %-11.3e"
              % ("v%d" % (i + 1), g["p0"][i], g["p1"][i], g["w"][i],
                 g["realised"][i], dev))
    if not g["activated"]:
        print("   -> uniform check: max |realised - 1/%d| = %.3e"
              % (g["n"], float(np.max(np.abs(g["realised"] - 1.0 / g["n"])))))
print()
print("counterfactual (no inversion: emit w = p1) on %s:" % CH["name"])
print("   realised: " + "  ".join("%.6f" % x for x in CH["naive"]))
print("   best value v%d has intended p1 = %.6f (rank 1 of %d) but would be "
      "sampled at %.6f -> rank %d of %d"
      % (CH["best"] + 1, CH["p1"][CH["best"]], CH["n"], CH["naive"][CH["best"]],
         naive_rank, CH["n"]))
sp_correct = np.corrcoef(np.argsort(np.argsort(CH["p1"])),
                         np.argsort(np.argsort(CH["realised"])))[0, 1]
sp_naive = np.corrcoef(np.argsort(np.argsort(CH["p1"])),
                       np.argsort(np.argsort(CH["naive"])))[0, 1]
print("   rank correlation vs intended:  inverted emission %+0.4f,  "
      "non-inverted emission %+0.4f  (order reverses)" % (sp_correct, sp_naive))
print()
print("MAX ABSOLUTE DEVIATION intended p1 vs realised probability")
print("   over all %d genes of %s : %.6e   (worst gene: %s)"
      % (len(GENES), SHAPE, MAXDEV, MAXDEV_GENE))
print("   activated genes only     : %.6e" % ACT_DEV)
print("   non-activated vs uniform : %.6e" % OFF_DEV)
print("   float32 round-off is the whole error budget: %s"
      % ("yes, < 1e-7" if MAXDEV < 1e-7 else "NO -- investigate"))
