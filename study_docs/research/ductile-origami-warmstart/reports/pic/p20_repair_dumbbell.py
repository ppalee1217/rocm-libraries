#!/usr/bin/env python3
"""P20 -- what the repair bought, before against after.

Both panels answer the same question in two units:

  Panel 1  THE MEASUREMENT ITSELF. Per-seed cross-window sd of ln(F/G) on the
           unrepaired reference cell (nw=321, RBS=4096) against the repaired
           cell (nw=1400, RBS=401), 12 windows each. This is the quantity that
           decides whether an effect is readable at all, and it falls by between
           one and two orders of magnitude.

  Panel 2  THE QC COUNTER. Dropout rate -- the share of repeats below 0.95 x
           that arm's own maximum in its window -- for every measured cell,
           before and after.

Panel 1 is the primary one. Dropout is a counter; sd is the instrument. A slide
that shows only dropout says "we fixed a QC statistic"; this one says "the
reading got one to two orders of magnitude tighter".

Everything is computed from artifacts at render time. The single-variable
controls that establish *which knob* did the work are deliberately not here --
they belong to "how we fixed it", which is P19's text.

Run on the HOST:  python3 p20_repair_dumbbell.py
"""
from __future__ import annotations

import glob
import os

from matplotlib.lines import Line2D

import common as C

P3_LIMIT = 8.0                 # P3 acceptance: dropout <= 8 %
DROPOUT_FRAC = 0.95            # a repeat below 0.95 x that arm's window max

BEFORE_CELL = "A_"             # nw 321, rbs 4096 -- the unrepaired reference
AFTER_CELL = "C03_"            # nw 1400, rbs 401 -- the repair


# --------------------------------------------------------------------------
# dropout: "before" from the campaign artifacts, "after" from the pilot cells
# --------------------------------------------------------------------------
def _count(repeats):
    top = max(repeats)
    return sum(1 for v in repeats if v < DROPOUT_FRAC * top), len(repeats)


def campaign1(variant):
    """Dropout over 5 seeds x 2 arms x 7 repeats of the preserved campaign 1."""
    hits = n = 0
    for seed in C.SEEDS:
        hit = [p for p in sorted(glob.glob(os.path.join(
            C.BASE, "medium_recheck_control", variant, f"seed_{seed}",
            "preserved_campaign1_*", "champion_interleaved.campaign1_*.json")))
            if "status" not in os.path.basename(p)]
        if not hit:
            raise FileNotFoundError(
                f"no preserved campaign-1 champion for {variant} seed {seed}")
        rs = C.champion(hit[0])["remeasure_summary"]
        for arm in ("G", "F"):
            h, k = _count(rs[arm]["raw_gflops"])
            hits, n = hits + h, n + k
    return hits, n


def campaign2_capped():
    """Dropout of the 2026-08-12 capped recheck (campaign 2)."""
    d = C.champion(os.path.join(C.BASE, "medium_recheck_summary.json"))
    hits = n = 0
    for seed in C.SEEDS:
        spread = d["results"]["capped"][str(seed)]["spread"]
        for arm in ("G", "F"):
            h, k = _count(spread[arm]["repeats"])
            hits, n = hits + h, n + k
    return hits, n


def pilot(name):
    s = C.cell_summary(name)
    return s["dropout_hits"], s["dropout_n"]


def pct(h, n):
    return 100.0 * h / n


def main():
    # ---- panel 1: per-seed cross-window sd, before and after ---------------
    before = C.cell_per_seed(BEFORE_CELL)
    after = C.cell_per_seed(AFTER_CELL)
    sd0 = [before[s]["sample_sd"] for s in C.SEEDS]
    sd1 = [after[s]["sample_sd"] for s in C.SEEDS]
    gain = [a / b for a, b in zip(sd0, sd1)]

    # ---- panel 2 -----------------------------------------------------------
    c1c, c2c, c1n = campaign1("capped"), campaign2_capped(), campaign1("native")
    c03, c03conf, stage2 = pilot("C03_"), pilot("C03CONF_"), pilot("STAGE2_NATIVE_")

    fig, axes = C.new_fig(1, 2, figsize=(15.4, 7.0))
    ax1, ax2 = axes

    def _stage(a, n, stage, title):
        a.text(0.0, 1.150, f"{n} · {stage}", transform=a.transAxes, ha="left",
               va="bottom", fontsize=13.5, fontweight="bold", color=C.C_GREY)
        a.set_title(title, fontsize=15.0, loc="left", pad=10)

    # =============== panel 1 -- the measurement itself =====================
    _stage(ax1, "1", "THE MEASUREMENT",
           "Per-seed spread of the reading, 12 windows each")

    for i, s in enumerate(C.SEEDS):
        ax1.plot([0, 1], [sd0[i], sd1[i]], color=C.C_GREY, lw=1.6, zorder=2)
        ax1.plot([0], [sd0[i]], marker="o", ms=12, mfc="white", mec=C.C_RED,
                 mew=2.6, zorder=4, ls="none")
        ax1.plot([1], [sd1[i]], marker="o", ms=12, mfc=C.C_GREEN, mec="white",
                 mew=1.6, zorder=4, ls="none")
    # Only the two extremes are labelled. Five labels on a log axis collide,
    # and the header already carries the full range, so per-seed labels would
    # be redundant clutter rather than information.
    for idx, tag in ((gain.index(min(gain)), "smallest gain"),
                     (gain.index(max(gain)), "largest gain")):
        ax1.text(1.09, sd1[idx], f"{gain[idx]:.0f}× tighter\n({tag})",
                 va="center", ha="left", fontsize=11.5, color=C.C_GREEN,
                 fontweight="bold", linespacing=1.35)

    ax1.set_yscale("log")
    ax1.set_xlim(-0.46, 1.78)
    ax1.set_ylim(1.4e-3, 2.4)
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["before\nwarm-up 321", "after\nwarm-up 1400"],
                        fontsize=13, linespacing=1.5)
    ax1.tick_params(axis="x", length=0, pad=9)
    ax1.set_ylabel("cross-window sd of ln(F/G)   (log scale)")
    ax1.grid(axis="y", zorder=0)
    ax1.set_axisbelow(True)
    ax1.text(0.5, 0.975,
             f"{min(sd0):.2f} – {max(sd0):.2f}    →    "
             f"{min(sd1):.4f} – {max(sd1):.4f}",
             transform=ax1.transAxes, ha="center", va="top", fontsize=13.5,
             fontweight="bold", color="#222222")
    ax1.text(0.5, 0.912,
             f"every seed improves: {min(gain):.0f}× at worst, "
             f"{max(gain):.0f}× at best",
             transform=ax1.transAxes, ha="center", va="top", fontsize=11.5,
             color=C.C_GREY)

    # =============== panel 2 -- the QC counter ==============================
    _stage(ax2, "2", "THE QC COUNTER", "Dropout rate, every measured cell")

    YLIM = (-4.0, 62.0)
    ax2.axhspan(YLIM[0], P3_LIMIT, facecolor="#F0F0F0", zorder=0)
    ax2.axhline(P3_LIMIT, color="#1A1A1A", lw=1.5, ls=(0, (6, 4)), zorder=2)

    # (x, value, label, before?)
    PTS = [
        (-0.34, pct(*c1c), "campaign 1", True),
        (0.34, pct(*c2c), "campaign 2", True),
        (-0.34, pct(*c03), "C03", False),
        (0.34, pct(*c03conf), "C03CONF", False),
        (1.60, pct(*c1n), "campaign 1", True),
        (1.60, pct(*stage2), "STAGE2_NATIVE", False),
    ]
    for gx in (-0.34, 0.34, 1.60):
        b = [p for p in PTS if p[0] == gx and p[3]][0]
        a = [p for p in PTS if p[0] == gx and not p[3]][0]
        ax2.annotate("", xy=(gx, a[1] + 2.6), xytext=(gx, b[1] - 2.6),
                     arrowprops=dict(arrowstyle="-|>", color=C.C_GREY, lw=2.2,
                                     shrinkA=4, shrinkB=4), zorder=2)
    for x, v, lab, is_before in PTS:
        ax2.plot([x], [v], marker="o", ms=13, zorder=4, ls="none",
                 mfc="white" if is_before else C.C_GREEN,
                 mec=C.C_RED if is_before else "white",
                 mew=2.6 if is_before else 1.6)
        ax2.text(x, v + 2.4, f"{v:.2f} %", ha="center", va="bottom",
                 fontsize=12.5, fontweight="bold", color="#222222")
        ax2.text(x, v - 2.4, lab, ha="center", va="top", fontsize=10,
                 color=C.C_GREY)
    # High and left of the data: beside the 8 % line it lands on "6.55 %".
    ax2.text(-0.90, 55.0, "P3 acceptance:  dropout ≤ 8 %", ha="left",
             va="top", fontsize=11.5, fontweight="bold", color="#1A1A1A")

    ax2.set_xlim(-0.95, 2.36)
    ax2.set_ylim(*YLIM)
    ax2.set_yticks([0, 10, 20, 30, 40, 50])
    ax2.set_yticklabels([f"{v} %" for v in [0, 10, 20, 30, 40, 50]])
    ax2.set_xticks([0.0, 1.60])
    ax2.set_xticklabels(["capped\n(P0 = 512)", "native\n(P0 = 11,405)"],
                        fontsize=13, linespacing=1.5)
    ax2.tick_params(axis="x", length=0, pad=9)
    ax2.set_ylabel("dropout rate  (% of repeats)")
    ax2.grid(axis="y", zorder=0)
    ax2.set_axisbelow(True)

    handles = [
        Line2D([], [], marker="o", ms=12, mfc="white", mec=C.C_RED, mew=2.6,
               ls="none", label="before the repair"),
        Line2D([], [], marker="o", ms=12, mfc=C.C_GREEN, mec="white", mew=1.6,
               ls="none", label="after the repair, 12 windows"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
               fontsize=12.5, bbox_to_anchor=(0.5, 0.030), handletextpad=0.4,
               columnspacing=2.6)

    fig.text(0.012, 0.108,
             "dropout = one repeat below 0.95 × that arm's own maximum in that "
             "window.  Panel 1 compares the two 12-window pilot cells that differ "
             "only in the warm-up count.\nPanel 2's \"before\" values are the "
             "1-window campaign remeasures (70 repeats each); its \"after\" values "
             "are the 12-window repaired cells (840 repeats each).",
             ha="left", va="bottom", fontsize=10.5, color=C.C_GREY,
             linespacing=1.5)

    C.provenance(fig, "medium_pilot401/results/{A,C03,C03CONF,STAGE2_NATIVE}"
                      "/summary.json · medium_recheck_control/ · "
                      "medium_recheck_summary.json")
    fig.subplots_adjust(left=0.072, right=0.985, top=0.812, bottom=0.230,
                        wspace=0.245)
    C.save(fig, "p20_repair_dumbbell", tight=False)

    print("  per-seed cross-window sd of ln(F/G):")
    for s, a, b, g in zip(C.SEEDS, sd0, sd1, gain):
        print(f"    seed {s}: {a:.5f} -> {b:.5f}   {g:5.1f}× tighter")
    print(f"    range {min(sd0):.4f}-{max(sd0):.4f} -> "
          f"{min(sd1):.5f}-{max(sd1):.5f}   "
          f"{min(gain):.1f}× to {max(gain):.1f}×")
    print(f"  dropout capped  c1 {pct(*c1c):6.2f} %  c2 {pct(*c2c):6.2f} %  ->  "
          f"C03 {pct(*c03):5.2f} %  C03CONF {pct(*c03conf):5.2f} %")
    print(f"  dropout native  c1 {pct(*c1n):6.2f} %  ->  "
          f"STAGE2_NATIVE {pct(*stage2):5.2f} %")


if __name__ == "__main__":
    main()
