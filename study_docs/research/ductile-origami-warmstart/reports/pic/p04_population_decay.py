#!/usr/bin/env python3
"""P4 -- GA population vs generation, showing both decay laws.

Everything plotted is the *measured* per-generation population read out of
``trajectory.jsonl`` (``generation_candidate_count``), never an idealised
formula.  The two laws below are only used to locate the crossover generation
in each run; they were recovered from the trajectories themselves and
reproduce every recorded transition exactly (1,274 / 1,274, all shapes, both
levels, both arms, all seeds):

    law 1   P <- int(512 + (P - 512) / 2)      fixed point 512
    law 2   P <- int(256 + (P - 256) * 0.8)    floor       256

That fixed point is why the capped runs (P0 = 512) sit still while the native
runs (P0 = 11,405) have to halve their way down: 512 is law 1's fixed point.

Run on the HOST:  python3 p04_population_decay.py
"""
from __future__ import annotations

import statistics as st

import common
from common import ARM_COLOR, C_GREY, C_RED

# Both laws are integer recurrences read back out of the trajectories; the two
# constants (512, 256) are the laws' fixed points, verified against every
# transition on every run rather than taken from any document.
P_LAW1_FIXED = 512
P_LAW2_FLOOR = 256
HORIZON = 30  # pinned generation budget; individual runs early-stop before it


def law1(p):
    return int(P_LAW1_FIXED + (p - P_LAW1_FIXED) / 2)


def law2(p):
    return int(P_LAW2_FLOOR + (p - P_LAW2_FLOOR) * 0.8)


def pops(level, arm, seed, shape):
    """Measured population per generation, gen 1 (= Gen0) onwards."""
    return [r["generation_candidate_count"]
            for r in common.traj(level, arm, seed, shape)]


def law2_onset(cc):
    """First generation whose size came from law 2 (None if never)."""
    for i in range(1, len(cc)):
        if cc[i] == law2(cc[i - 1]) and cc[i] != law1(cc[i - 1]):
            return i + 1
    return None


def first_gen_at_or_below(cc, thresh):
    for i, v in enumerate(cc):
        if v <= thresh:
            return i + 1
    return None


def unwind_stats(shape):
    """How long native spends coming back down, measured two ways."""
    back_to_512, decayed_99 = [], []
    for arm in ("G", "F"):
        for s in common.SEEDS:
            cc = pops("native", arm, s, shape)
            # 99 % of the way from this run's own Gen0 down to the 256 floor
            thr = P_LAW2_FLOOR + 0.01 * (cc[0] - P_LAW2_FLOOR)
            back_to_512.append(first_gen_at_or_below(cc, P_LAW1_FIXED))
            decayed_99.append(first_gen_at_or_below(cc, thr))
    return back_to_512, decayed_99


def panel(ax, shape, show_ylabel):
    onsets, native_p0 = [], set()
    cross = []
    # G drawn thick underneath, F thin on top: the two arms follow the same
    # law and would otherwise hide one another completely.
    for level, ls in (("capped", "--"), ("native", "-")):
        for arm, lw, al in (("G", 2.6, 0.40), ("F", 1.1, 0.85)):
            for seed in common.SEEDS:
                cc = pops(level, arm, seed, shape)
                gens = range(1, len(cc) + 1)
                ax.plot(gens, cc, ls, color=ARM_COLOR[arm], lw=lw, alpha=al,
                        zorder=2 if arm == "G" else 3)
                on = law2_onset(cc)
                if on is not None:
                    onsets.append(on)
                    cross.append((on, cc[on - 1]))
                    ax.plot([on], [cc[on - 1]], "o", ms=4.5,
                            mfc="white", mec=ARM_COLOR[arm], mew=1.1, zorder=5)
                if level == "native":
                    native_p0.add(cc[0])

    ax.axhline(P_LAW1_FIXED, color=C_GREY, ls=(0, (6, 3)), lw=1.3, zorder=1)
    ax.axhline(P_LAW2_FLOOR, color=C_GREY, ls=(0, (1, 2)), lw=1.6, zorder=1)

    ax.set_yscale("log", base=2)
    ticks = [256, 512, 1024, 2048, 4096, 8192, max(native_p0)]
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:,}" for t in ticks])
    ax.set_ylim(228, max(native_p0) * 1.45)
    ax.set_xlim(0.4, HORIZON + 0.6)
    ax.set_xticks([1, 5, 10, 15, 20, 25, 30])
    ax.set_xlabel("generation  (gen 1 = Gen0)")
    if show_ylabel:
        ax.set_ylabel("population (candidates submitted)")

    back, d99 = unwind_stats(shape)
    ax.set_title(f"{shape}   ({common.guidance(shape)['problem_size'][0]}"
                 f"×{common.guidance(shape)['problem_size'][1]}"
                 f"×1×{common.guidance(shape)['problem_size'][3]:,})",
                 pad=8)

    # law-2 crossover span, measured (arrow points at the marker cluster)
    lo, hi = min(onsets), max(onsets)
    cx = st.median([c[0] for c in cross])
    cy = st.median([c[1] for c in cross])
    ax.annotate(f"law 1 → law 2\ncrossover: gen {lo}–{hi}",
                xy=(cx, cy), xytext=(1.0, 268),
                fontsize=11, color=C_GREY, ha="left", va="bottom",
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5),
                arrowprops=dict(arrowstyle="->", color=C_GREY, lw=1.0,
                                connectionstyle="arc3,rad=-0.2"))

    # where native comes back to the capped Gen0 size
    gback = int(st.median(back))
    ax.annotate(f"native back to 512\nat gen {gback}",
                xy=(gback, P_LAW1_FIXED), xytext=(gback + 3.0, 1500),
                fontsize=11, color=C_RED, ha="left",
                arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.1))

    lo99, hi99 = min(d99), max(d99)
    span = f"gen {lo99}" if lo99 == hi99 else f"gen {lo99}–{hi99}"
    ax.text(0.985, 0.965,
            f"99 % of the {max(native_p0):,}→256 decay\ncomplete by {span}"
            f"  (median {int(st.median(d99))})",
            transform=ax.transAxes, ha="right", va="top", fontsize=10.5,
            color="black",
            bbox=dict(fc="white", ec=C_GREY, lw=0.7, alpha=0.9, pad=3.5))

    return onsets, back, d99


def main():
    fig, axes = common.new_fig(1, 2, figsize=(12.0, 6.75))
    out = {}
    for ax, shape, lab in ((axes[0], "medium", True), (axes[1], "large", False)):
        out[shape] = panel(ax, shape, lab)

    # legend: 4 run families + the 2 fixed points, drawn as proxies
    import matplotlib.lines as mlines
    handles = [
        mlines.Line2D([], [], color=ARM_COLOR["G"], ls="-", lw=1.6,
                      label="arm G, native  $P_0$ = 11,405"),
        mlines.Line2D([], [], color=ARM_COLOR["F"], ls="-", lw=1.6,
                      label="arm F, native  $P_0$ = 11,405"),
        mlines.Line2D([], [], color=ARM_COLOR["G"], ls="--", lw=1.6,
                      label="arm G, capped  $P_0$ = 512"),
        mlines.Line2D([], [], color=ARM_COLOR["F"], ls="--", lw=1.6,
                      label="arm F, capped  $P_0$ = 512"),
        mlines.Line2D([], [], color=C_GREY, ls=(0, (6, 3)), lw=1.3,
                      label="law 1 fixed point, 512"),
        mlines.Line2D([], [], color=C_GREY, ls=(0, (1, 2)), lw=1.6,
                      label="law 2 floor, 256"),
        mlines.Line2D([], [], color=C_GREY, ls="none", marker="o", ms=5,
                      mfc="white", mec=C_GREY, label="law 1 → law 2 crossover"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
               fontsize=11, bbox_to_anchor=(0.5, 0.028))

    fig.suptitle("Measured GA population decay: two laws, one shared floor",
                 y=0.985)
    fig.text(0.5, 0.885,
             "law 1: $P\\leftarrow512+(P-512)/2$   ·   "
             "law 2: $P\\leftarrow256+0.8\\,(P-256)$   ·   "
             "curves end where the run early-stopped (20–30 gens of the "
             "30-generation horizon)",
             ha="center", va="top", fontsize=10.5, color=C_GREY)

    common.provenance(fig, "trajectory.jsonl · generation_candidate_count "
                           "· stage3_* + stage5_native_* · 5 seeds × 2 arms")
    fig.tight_layout(rect=(0, 0.115, 1, 0.875))
    common.save(fig, "p04_population_decay", tight=False)

    for shape, (onsets, back, d99) in out.items():
        print(f"  {shape}: law-2 onset gen {min(onsets)}-{max(onsets)}; "
              f"native back to <=512 at gen {sorted(set(back))}; "
              f"99% decayed by gen {sorted(set(d99))} "
              f"(median {st.median(d99):g})")


if __name__ == "__main__":
    main()
