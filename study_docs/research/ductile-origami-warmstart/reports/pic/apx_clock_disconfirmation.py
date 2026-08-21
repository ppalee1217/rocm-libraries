#!/usr/bin/env python3
"""APPENDIX -- the clock-ramp hypothesis, tested by us and disconfirmed.

This used to be the third panel of ``p19_defect_storyboard``. It was moved to a
backup slide because it is a *side branch*: it reports a mechanism we proposed
and then refuted, which is a credibility point rather than a step in the
symptom -> root-cause story that P19 now tells in two panels.

The hypothesis
--------------
An idle GPU sits at a low clock and needs time to ramp. A 3.2 ms warm-up would
therefore open the timed window on a partly-promoted card, and the slow repeats
would be the ones that ran at low clock.

The test
--------
Direct 1 kHz clock telemetry, aligned per repeat, over 42 traced repeats. If
the hypothesis held, dropouts would sit at the low-clock end and the cloud would
climb left-to-right.

The result
----------
No relationship. Every repeat -- clean or contaminated -- reached at least the
minimum traced clock, and the two counterexamples are decisive in both
directions: a repeat at the LOWEST clock delivered 0.997 of arm max, and a
repeat near the HIGHEST clock delivered 0.470.

What survives is the correlation with warm-up *duration* (P19 panel 2). The
mechanism itself is ``NOT_EVALUATED`` -- an unidentified mechanism is not an
absent one, and at ~8 ms effective resolution this trace cannot resolve what the
clock did inside a 3.2 ms warm-up. The clock account is **disfavoured, not
excluded.**

Run on the HOST:  python3 apx_clock_disconfirmation.py
"""
from __future__ import annotations

import common as C
import p19_defect_storyboard as P19

DROPOUT_FRAC = P19.DROPOUT_FRAC


def main():
    clock = P19.load_clock_records()
    rho, pval = P19.spearman([r["sclk_max"] for r in clock],
                             [r["ratio"] for r in clock])
    clk_lo = min(r["sclk_max"] for r in clock)
    clk_hi = max(r["sclk_max"] for r in clock)

    clean = [r for r in clock if r["ratio"] >= DROPOUT_FRAC]
    drop = [r for r in clock if r["ratio"] < DROPOUT_FRAC]

    print(f"  n={len(clock)}  spearman(sclk_max, ratio) = {rho:+.4f}  "
          f"p = {pval:.4f}   sclk_max range {clk_lo:,}-{clk_hi:,} MHz   "
          f"dropouts {len(drop)}/{len(clock)}")

    fig, ax = C.new_fig(1, 1, figsize=(11.0, 7.0))

    ax.set_title("We proposed a mechanism, then disconfirmed it ourselves:\n"
                 "clock does not predict throughput",
                 fontsize=17, loc="left", pad=12, linespacing=1.35)

    # the shape the clock-ramp hypothesis predicts: low clock -> low throughput
    ax.annotate("", xy=(2135, 0.99), xytext=(1750, 0.47),
                arrowprops=dict(arrowstyle="->", color=C.C_LIGHT, lw=9),
                zorder=1)
    ax.text(1905, 0.745, "what the clock-ramp\nhypothesis predicts",
            fontsize=12.5, color=C.C_GREY, ha="center", va="center",
            rotation=25, rotation_mode="anchor", linespacing=1.3, zorder=2)

    ax.axhline(DROPOUT_FRAC, color=C.C_GREY, linestyle=(0, (4, 3)), lw=1.3,
               zorder=2)
    ax.text(2145, DROPOUT_FRAC, f" {DROPOUT_FRAC:g} × arm max", fontsize=11.5,
            color=C.C_GREY, ha="left", va="center")
    ax.axvline(clk_lo, color=C.C_GREEN, lw=1.8, linestyle=(0, (5, 3)), zorder=2)
    ax.text(clk_lo + 18, 1.34,
            f"every repeat, clean or contaminated,\nreached ≥ {clk_lo:,} MHz",
            fontsize=12.5, color=C.C_GREEN, ha="left", va="top",
            fontweight="bold", linespacing=1.35)

    for grp, col, lab in ((clean, C.C_BLUE, f"clean (n = {len(clean)})"),
                          (drop, C.C_RED, f"dropout (n = {len(drop)})")):
        ax.plot([r["sclk_max"] for r in grp], [r["ratio"] for r in grp], "o",
                ms=11, color=col, mec="white", mew=1.4, zorder=5, label=lab)

    def _find(target):
        return min(clock, key=lambda r: abs(r["ratio"] - target))

    for target, txy in ((0.997, (1640, 0.755)), (0.470, (1975, 1.145))):
        r = _find(target)
        ax.annotate(f"{r['ratio']:.3f} of max\nat {r['sclk_max']:,} MHz",
                    xy=(r["sclk_max"], r["ratio"]), xytext=txy,
                    fontsize=12.5, fontweight="bold", color="#333333",
                    ha="center", va="center", zorder=3, linespacing=1.3,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none",
                              alpha=0.85),
                    arrowprops=dict(arrowstyle="->", color="#333333", lw=1.4,
                                    shrinkB=8))

    ax.text(0.015, 0.02,
            f"Spearman ρ = {rho:+.3f},   p = {pval:.2f}\n"
            f"n = {len(clock)} traced repeats  ·  no relationship",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=14,
            linespacing=1.5, fontweight="bold", color="#222222", zorder=6,
            bbox=dict(boxstyle="round,pad=0.45", fc="white", ec=C.C_GREY,
                      lw=1.5, alpha=0.97))

    ax.set_xlim(1500, 2150)
    ax.set_ylim(0.0, 1.40)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xlabel("per-repeat peak sclk (MHz) — 1 kHz trace")
    ax.set_ylabel("throughput, fraction of arm max")
    ax.legend(loc="lower left", bbox_to_anchor=(0.015, 0.255), frameon=False,
              fontsize=12.5, handletextpad=0.3, borderpad=0.2)

    C.provenance(fig, "medium_clockladder/capped/seed_{24001,24004,24005}"
                      "/s1_trace (1 kHz) · 3 seeds × 14 records = 42 repeats")
    fig.subplots_adjust(left=0.088, right=0.972, top=0.845, bottom=0.105)
    C.save(fig, "apx_clock_disconfirmation", tight=False)


if __name__ == "__main__":
    main()
