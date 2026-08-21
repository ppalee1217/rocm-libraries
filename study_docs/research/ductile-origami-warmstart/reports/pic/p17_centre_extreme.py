#!/usr/bin/env python3
"""P16 -- Gen0 centre vs extreme, drawn twice: at P0 = 512 and at P0 = 11,405.

Guidance moves the CENTRE of the Gen0 pool. The GA selects on the EXTREME (the
batch best). Those are different quantities, and on `large` they disagree.

Enlarging the Gen0 pool 22x is the most direct available manipulation of that
hypothesis, so the same chart is drawn at both pool sizes. It confirmed one half
and refuted the other:

  * confirmed  -- guidance still lifts the centre at 22x (5/5 seeds).
  * REFUTED    -- pre-registered prediction (i), "the guided extreme
                  disadvantage will widen at 11,405", did not happen. Under 22x
                  the disadvantage did not widen; it disappeared.

Both quantities come from the generation-1 row of trajectory.jsonl via
common.gen0_centre_extreme, so the ratios are computed at render time.

Run on the HOST:  python3 p17_centre_extreme.py
"""
from __future__ import annotations

from statistics import median

import common as C

SHAPE = "large"

# (level key in common.ARM_DIR, Gen0 pool size, panel label)
PANELS = [
    ("capped", 512, "P0 = 512  (capped)"),
    ("native", 11405, "P0 = 11,405  (native)"),
]

# One fixed colour per seed, in the house Okabe-Ito order. Colour follows the
# entity, so a seed keeps its colour across both panels -- that is what makes
# the 22x manipulation readable as a manipulation.
SEED_COLOR = {
    24001: C.C_BLUE,
    24002: C.C_ORANGE,
    24003: C.C_GREEN,
    24004: C.C_PURPLE,
    24005: C.C_SKY,
}

X_CENTRE, X_EXTREME = 0.0, 1.0


def collect(level):
    """{'centre': [...5 ratios...], 'extreme': [...]} in SEEDS order."""
    out = {"centre": [], "extreme": []}
    for s in C.SEEDS:
        d = C.gen0_centre_extreme(level, SHAPE, s)
        out["centre"].append(d["centre"])
        out["extreme"].append(d["extreme"])
    return out


def _n_positive(vals):
    return sum(1 for v in vals if v > 1.0)


def main():
    data = {lvl: collect(lvl) for lvl, _p0, _lab in PANELS}

    for lvl, p0, _lab in PANELS:
        d = data[lvl]
        print(f"[{lvl} P0={p0}] {SHAPE}")
        for s, c, e in zip(C.SEEDS, d["centre"], d["extreme"]):
            print(f"   {s}:  centre {c:.4f}   extreme {e:.4f}")
        print(f"   centre  median {median(d['centre']):.4f} "
              f"({_n_positive(d['centre'])}/5 > 1.0)")
        print(f"   extreme median {median(d['extreme']):.4f} "
              f"({_n_positive(d['extreme'])}/5 > 1.0)")

    # 16:9 as the house style requires, scaled up so two slope panels plus
    # their annotations stay legible when projected. 200 dpi is unchanged.
    fig, axes = C.new_fig(1, 2, figsize=(12.0, 6.75), sharey=True)

    lo = min(min(d["centre"] + d["extreme"]) for d in data.values())
    hi = max(max(d["centre"] + d["extreme"]) for d in data.values())
    pad = 0.055 * (hi - lo)
    ylo, yhi = lo - pad, hi + 3.3 * pad

    for ax, (lvl, p0, lab) in zip(axes, PANELS):
        d = data[lvl]

        # the null: guidance neither helps nor hurts
        ax.axhline(1.0, color="#555555", lw=1.8, zorder=2)
        ax.text(-1.06, 0.9985, "F/G = 1.0", ha="left", va="top", fontsize=11.5,
                color="#555555")

        # one line per seed, centre -> extreme
        for s, c, e in zip(C.SEEDS, d["centre"], d["extreme"]):
            col = SEED_COLOR[s]
            ax.plot([X_CENTRE, X_EXTREME], [c, e], "-", color=col, lw=2.2,
                    zorder=3, alpha=0.9)
            ax.plot([X_CENTRE, X_EXTREME], [c, e], "o", ms=10, color=col,
                    mec="white", mew=1.4, zorder=4,
                    label=f"seed {s}" if ax is axes[0] else None)

        # medians, drawn as a wide tick at each end
        for x, key, side in ((X_CENTRE, "centre", "right"),
                             (X_EXTREME, "extreme", "left")):
            m = median(d[key])
            ax.hlines(m, x - 0.19, x + 0.19, color="#222222", lw=3.0, zorder=5)
            dx = -0.25 if side == "right" else 0.25
            ax.text(x + dx, m, f"median {m:.4f}\n{_n_positive(d[key])}/5 > 1.0",
                    ha=side, va="center", fontsize=11.5, fontweight="bold",
                    color="#222222", linespacing=1.35, zorder=6,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none",
                              alpha=0.88))

        ax.set_xlim(-1.10, 2.10)
        ax.set_ylim(ylo, yhi)
        ax.set_xticks([X_CENTRE, X_EXTREME])
        ax.set_xticklabels(["Gen0 centre\nmedian of pool",
                            "Gen0 extreme\nbatch best"], fontsize=13)
        ax.set_title(lab, fontsize=16, pad=10)
        ax.grid(axis="x", visible=False)

    axes[0].set_ylabel(f"F / G  ratio at generation 1  ({SHAPE})")
    axes[0].text(0.5, 0.985,
                 "guidance moves the centre  ·  the GA selects on the extreme",
                 transform=axes[0].transAxes, ha="center", va="top",
                 fontsize=11, color=C.C_GREY)
    axes[0].legend(loc="lower left", frameon=False, fontsize=11.5, ncol=2,
                   handletextpad=0.3, columnspacing=1.1, borderpad=0.2)

    # ---- the pre-registered prediction, and how it came out -----------------
    # Placed in the lower half of the native panel, which is empty: every native
    # ratio is >= 0.95 while the shared y-axis reaches down to the capped
    # extremes near 0.83.
    cap, nat = data["capped"], data["native"]
    axes[1].text(
        0.5, 0.20,
        "pre-registered prediction (i)\n"
        "“the guided extreme disadvantage will widen at 11,405”\n"
        # mathtext bold so the verdict word carries weight inside the box
        r"$\mathbf{REFUTED}$ — it did not widen, it disappeared" "\n"
        f"median {median(cap['extreme']):.4f} → {median(nat['extreme']):.4f},   "
        f"{_n_positive(cap['extreme'])}/5 → {_n_positive(nat['extreme'])}/5 "
        "above 1.0",
        transform=axes[1].transAxes, ha="center", va="bottom", fontsize=11.5,
        linespacing=1.6, color="#222222", zorder=7,
        bbox=dict(boxstyle="round,pad=0.55", fc="white", ec=C.C_RED, lw=2.0,
                  alpha=0.97))

    C.provenance(fig, "stage3_{baseline,guided} + stage5_native_{baseline,guided}"
                      " → trajectory.jsonl generation-1 rows (large)")
    C.save(fig, "p17_centre_extreme")


if __name__ == "__main__":
    main()
