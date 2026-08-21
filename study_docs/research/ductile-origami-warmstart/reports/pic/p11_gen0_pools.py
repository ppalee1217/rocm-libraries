#!/usr/bin/env python3
"""P11 -- Gen0 at 512 vs 11,405, with the decay curves overlaid.

Both panels are read from ``trajectory.jsonl``:

  * Gen0 pool size          = generation_candidate_count of the first record
  * total evaluation spend  = cumulative_complete_evals of the last record
  * decay curve             = generation_candidate_count, all generations

Nothing is transcribed: the 22x enlargement and the evaluation-spend ratio are
both divisions of numbers computed here.  Shape shown is `medium`; `large` is
printed to stdout alongside it.

Run on the HOST:  python3 p11_gen0_pools.py
"""
from __future__ import annotations

import statistics as st

import common
from common import ARM_COLOR, C_GREY, C_LIGHT, C_RED

SHAPE = "medium"
LEVELS = ["capped", "native"]
LEVEL_FACE = {"capped": C_LIGHT, "native": C_GREY}   # level is not arm-coded
LEVEL_LS = {"capped": "--", "native": "-"}


def runs(level, shape):
    """[(arm, seed, [population per generation], total complete evals)]"""
    out = []
    for arm in ("G", "F"):
        for seed in common.SEEDS:
            rows = common.traj(level, arm, seed, shape)
            out.append((arm, seed,
                        [r["generation_candidate_count"] for r in rows],
                        rows[-1]["cumulative_complete_evals"]))
    return out


def median_curve(rs, ngen):
    """Median population per generation over the runs still active."""
    xs, ys, alive = [], [], []
    for g in range(ngen):
        v = [r[2][g] for r in rs if len(r[2]) > g]
        if not v:
            break
        xs.append(g + 1)
        ys.append(st.median(v))
        alive.append(len(v))
    return xs, ys, alive


def panel_pools(ax, data):
    gen0 = {lv: {r[2][0] for r in data[lv]} for lv in LEVELS}
    for lv in LEVELS:
        assert len(gen0[lv]) == 1, f"{lv}: Gen0 not constant {gen0[lv]}"
    gen0 = {lv: next(iter(v)) for lv, v in gen0.items()}
    evals = {lv: [r[3] for r in data[lv]] for lv in LEVELS}
    mean_ev = {lv: st.mean(evals[lv]) for lv in LEVELS}

    xs = {("Gen0", "capped"): 0.0, ("Gen0", "native"): 0.62,
          ("evals", "capped"): 2.15, ("evals", "native"): 2.77}
    w = 0.52
    arrow_x = {"Gen0": 1.05, "evals": 3.20}

    for lv in LEVELS:
        ax.bar(xs[("Gen0", lv)], gen0[lv], width=w, zorder=2,
               facecolor=LEVEL_FACE[lv], edgecolor="black", lw=1.0)
        ax.bar(xs[("evals", lv)], mean_ev[lv], width=w, zorder=2,
               facecolor=LEVEL_FACE[lv], edgecolor="black", lw=1.0)
        ax.text(xs[("Gen0", lv)], gen0[lv] + 700, f"{gen0[lv]:,}",
                ha="center", va="bottom", fontsize=12.5)
        ax.text(xs[("evals", lv)], mean_ev[lv] + 700, f"{mean_ev[lv]:,.0f}",
                ha="center", va="bottom", fontsize=12.5)

        # every individual run, arm-coloured, over the evaluation bars
        for arm, seed, _, ev in data[lv]:
            ax.plot([xs[("evals", lv)]], [ev], marker="o", ms=6, zorder=4,
                    mfc=ARM_COLOR[arm], mec="white", mew=0.8, alpha=0.95)

    ymax = 40000
    for key, lo, hi, lab in (
            ("Gen0", gen0["capped"], gen0["native"],
             f"×{gen0['native'] / gen0['capped']:.1f}"),
            ("evals", mean_ev["capped"], mean_ev["native"],
             f"×{mean_ev['native'] / mean_ev['capped']:.2f}")):
        x = arrow_x[key]
        # dotted leaders from each bar top out to the ratio arrow
        for lv, y in (("capped", lo), ("native", hi)):
            ax.plot([xs[(key, lv)], x], [y, y], ls=":", lw=1.0, color=C_RED,
                    zorder=1)
        ax.annotate("", xy=(x, hi), xytext=(x, lo),
                    arrowprops=dict(arrowstyle="<->", color=C_RED, lw=1.7))
        ax.text(x + 0.12, (lo + hi) / 2, lab, color=C_RED, fontsize=15,
                fontweight="bold", va="center", ha="left")

    ax.set_xticks([0.31, 2.46])
    ax.set_xticklabels(["Gen0 pool\n(generation 1)",
                        "total evaluations\n(whole run)"])
    ax.set_ylim(0, ymax)
    ax.set_yticks([0, 5000, 10000, 15000, 20000, 25000, 30000, 35000])
    ax.set_yticklabels([f"{v:,}" for v in
                        [0, 5000, 10000, 15000, 20000, 25000, 30000, 35000]])
    ax.set_ylabel("candidate evaluations  (linear scale)")
    ax.set_xlim(-0.50, 3.90)
    ax.set_title(f"{SHAPE}: pool size and total spend", pad=8)
    return gen0, mean_ev, evals


def panel_decay(ax, data):
    ngen = 30
    # G thick underneath, F thin on top: identical laws, otherwise F hides G
    for lv in LEVELS:
        for arm, lw, al in (("G", 2.6, 0.40), ("F", 1.1, 0.85)):
            for a, seed, cc, _ in data[lv]:
                if a != arm:
                    continue
                ax.plot(range(1, len(cc) + 1), cc, LEVEL_LS[lv],
                        color=ARM_COLOR[arm], lw=lw, alpha=al,
                        zorder=3 if arm == "G" else 4)

    mc = {lv: median_curve(data[lv], ngen) for lv in LEVELS}
    n = min(len(mc["capped"][0]), len(mc["native"][0]))
    ax.fill_between(mc["capped"][0][:n], mc["capped"][1][:n],
                    mc["native"][1][:n], facecolor=C_GREY, alpha=0.18,
                    zorder=1, label="excess pool carried by native")

    ax.axhline(512, color=C_GREY, ls=(0, (6, 3)), lw=1.3, zorder=2)
    ax.axhline(256, color=C_GREY, ls=(0, (1, 2)), lw=1.6, zorder=2)

    back = [next(i + 1 for i, v in enumerate(cc) if v <= 512)
            for _, _, cc, _ in data["native"]]
    gb = int(st.median(back))
    ax.annotate(f"native back to 512\nat gen {gb}",
                xy=(gb, 512), xytext=(gb + 3.2, 1700),
                fontsize=11.5, color=C_RED, ha="left",
                arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.1))

    ax.set_yscale("log", base=2)
    ticks = [256, 512, 1024, 2048, 4096, 8192, 11405]
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:,}" for t in ticks])
    ax.set_ylim(228, 11405 * 1.35)
    ax.set_xlim(0.4, ngen + 0.6)
    ax.set_xticks([1, 5, 10, 15, 20, 25, 30])
    ax.set_xlabel("generation  (gen 1 = Gen0)")
    ax.set_ylabel("population (log scale)")
    ax.set_title(f"{SHAPE}: the two pools decaying to the same floor", pad=8)
    return back


def main():
    data = {lv: runs(lv, SHAPE) for lv in LEVELS}

    fig, axes = common.new_fig(1, 2, figsize=(13.0, 6.6),
                               gridspec_kw={"width_ratios": [1.0, 1.45]})
    gen0, mean_ev, evals = panel_pools(axes[0], data)
    back = panel_decay(axes[1], data)

    import matplotlib.lines as mlines
    import matplotlib.patches as mpatches
    axes[0].legend(handles=[
        mpatches.Patch(facecolor=LEVEL_FACE["capped"], edgecolor="black",
                       label="capped ($P_0$ = 512)"),
        mpatches.Patch(facecolor=LEVEL_FACE["native"], edgecolor="black",
                       label="native ($P_0$ = 11,405)"),
        mlines.Line2D([], [], ls="none", marker="o", ms=7,
                      mfc=ARM_COLOR["G"], mec="white",
                      label="one run, arm G"),
        mlines.Line2D([], [], ls="none", marker="o", ms=7,
                      mfc=ARM_COLOR["F"], mec="white",
                      label="one run, arm F"),
    ], loc="upper left", fontsize=11, frameon=True, framealpha=0.95)

    axes[1].legend(handles=[
        mlines.Line2D([], [], color=ARM_COLOR["G"], ls="-", lw=1.6,
                      label="arm G"),
        mlines.Line2D([], [], color=ARM_COLOR["F"], ls="-", lw=1.6,
                      label="arm F"),
        mlines.Line2D([], [], color="black", ls="-", lw=1.6, label="native"),
        mlines.Line2D([], [], color="black", ls="--", lw=1.6, label="capped"),
        mpatches.Patch(facecolor=C_GREY, alpha=0.25,
                       label="excess pool carried by native"),
        mlines.Line2D([], [], color=C_GREY, ls=(0, (1, 2)), lw=1.6,
                      label="shared decay floor, 256"),
    ], loc="upper right", fontsize=11, ncol=2, frameon=True, framealpha=0.95)

    fig.suptitle(
        f"Gen0 pool: {gen0['capped']:,} (capped) vs {gen0['native']:,} "
        f"(native) — a ×{gen0['native'] / gen0['capped']:.1f} enlargement",
        y=0.975)
    fig.text(0.5, 0.918,
             f"{SHAPE}; bars are means over 5 seeds × 2 arms, dots are the "
             f"individual runs; decay curves are every run",
             ha="center", va="top", fontsize=11, color=C_GREY)

    common.provenance(fig, "trajectory.jsonl · generation_candidate_count + "
                           "cumulative_complete_evals · stage3_* + "
                           "stage5_native_* · medium")
    fig.tight_layout(rect=(0, 0.01, 1, 0.90))
    common.save(fig, "p11_gen0_pools", tight=False)

    print(f"  Gen0 pool: capped {gen0['capped']:,}  native {gen0['native']:,}"
          f"  ratio x{gen0['native'] / gen0['capped']:.4f}")
    for shape in ("medium", "large"):
        d = {lv: runs(lv, shape) for lv in LEVELS}
        m = {lv: st.mean([r[3] for r in d[lv]]) for lv in LEVELS}
        per_arm = {(lv, a): st.mean([r[3] for r in d[lv] if r[0] == a])
                   for lv in LEVELS for a in ("G", "F")}
        print(f"  {shape}: total complete evals -- capped mean {m['capped']:,.1f} "
              f"(G {per_arm[('capped', 'G')]:,.1f} / "
              f"F {per_arm[('capped', 'F')]:,.1f}), "
              f"native mean {m['native']:,.1f} "
              f"(G {per_arm[('native', 'G')]:,.1f} / "
              f"F {per_arm[('native', 'F')]:,.1f}), "
              f"ratio x{m['native'] / m['capped']:.3f}")
    print(f"  native back to <=512 at gen {sorted(set(back))} (medium)")
    print(f"  medium per-run totals: capped {sorted(evals['capped'])}")
    print(f"                         native {sorted(evals['native'])}")


if __name__ == "__main__":
    main()
