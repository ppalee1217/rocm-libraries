#!/usr/bin/env python3
"""P15 — What the search budget actually buys.

Three panels:
  1. where the gains come from   (Gen0 -> gen 10, vs gen 10 -> end)
  2. where the budget goes       (Gen0 / gen 1-10 / gen 10-end share of evaluations)
  3. early stop                  (run length and last-improvement generation)
  4. does a Gen0 lead survive?   (each arm vs ITSELF at the two pool sizes)

Everything is computed from trajectory.jsonl at render time. The native/capped
budget-ratio scatter deliberately does NOT appear as a panel: native differs from
capped in Gen0 size AND total budget AND decay trajectory simultaneously, so it is
not a budget dial. The clean within-run manipulation (gen 10 -> end) is panel 1.

Run on the HOST.
"""
import statistics as st

import common as c

BLOCKS = [("capped", "medium"), ("capped", "large"),
          ("native", "medium"), ("native", "large")]
LABEL = {("capped", "medium"): "medium\ncapped", ("capped", "large"): "large\ncapped",
         ("native", "medium"): "medium\nnative", ("native", "large"): "large\nnative"}


def runs(level, shape):
    for s in c.SEEDS:
        for a in ("G", "F"):
            yield c.traj(level, a, s, shape)


def stats(level, shape):
    """Per-block medians of every quantity the page states."""
    early, late, g0share, by10, endgen, lastimp = [], [], [], [], [], []
    for r in runs(level, shape):
        g0, g10, fin = c.gen0(r), c.gen10(r), r[-1]["best_gflops_so_far"]
        early.append(g10 / g0 - 1.0)
        late.append(fin / g10 - 1.0)
        tot = r[-1]["cumulative_complete_evals"]
        g0share.append(r[0]["cumulative_complete_evals"] / tot)
        by10.append([x for x in r if x["gen"] <= 10][-1]["cumulative_complete_evals"] / tot)
        endgen.append(r[-1]["gen"])
        # first generation attaining the final best-so-far
        lastimp.append(next(x["gen"] for x in r if x["best_gflops_so_far"] >= fin * 0.99999))
    med = st.median
    return dict(early=med(early), late=med(late), g0=med(g0share), by10=med(by10),
                endgen=endgen, lastimp=lastimp,
                gen10frac=med(c.gen10(r) / r[-1]["best_gflops_so_far"] for r in runs(level, shape)))


def main():
    S = {b: stats(*b) for b in BLOCKS}
    fig, axes = c.new_fig(1, 4, figsize=(21.0, 5.4))
    xs = range(len(BLOCKS))
    names = [LABEL[b] for b in BLOCKS]

    # ---- panel 1: where the gains come from -------------------------------
    ax = axes[0]
    early = [S[b]["early"] * 100 for b in BLOCKS]
    late = [S[b]["late"] * 100 for b in BLOCKS]
    ax.bar(xs, early, 0.62, color=c.C_BLUE, label="Gen0 → generation 10")
    ax.bar(xs, late, 0.62, bottom=early, color=c.C_ORANGE,
           label="generation 10 → end  (the clean within-run test)")
    for i, (e, l) in enumerate(zip(early, late)):
        ax.text(i, e / 2, f"+{e:.1f} %", ha="center", va="center",
                color="white", fontsize=11, fontweight="bold")
        ax.text(i, e + l + 0.9, f"+{l:.1f} %", ha="center", va="bottom",
                color=c.C_ORANGE, fontsize=11, fontweight="bold")
    ax.set_xticks(list(xs)); ax.set_xticklabels(names)
    ax.set_ylabel("champion improvement (%)")
    ax.set_title("1 · where the gains come from", loc="left", fontweight="bold")
    ax.legend(loc="upper right", framealpha=0.95)
    ax.set_ylim(0, 38)

    # ---- panel 2: where the budget goes -----------------------------------
    ax = axes[1]
    g0 = [S[b]["g0"] * 100 for b in BLOCKS]
    mid = [(S[b]["by10"] - S[b]["g0"]) * 100 for b in BLOCKS]
    rest = [(1 - S[b]["by10"]) * 100 for b in BLOCKS]
    ax.bar(xs, g0, 0.62, color=c.C_PURPLE, label="Gen0")
    ax.bar(xs, mid, 0.62, bottom=g0, color=c.C_SKY, label="generations 1–10")
    ax.bar(xs, rest, 0.62, bottom=[a + b for a, b in zip(g0, mid)],
           color=c.C_LIGHT, label="generation 10 → end")
    for i, v in enumerate(g0):
        ax.text(i, v / 2, f"{v:.0f} %", ha="center", va="center",
                color="white", fontsize=11, fontweight="bold")
    for i, b in enumerate(BLOCKS):
        ax.text(i, S[b]["by10"] * 100 + 1.5, f"{S[b]['by10']*100:.0f} % spent\nby gen 10",
                ha="center", va="bottom", fontsize=9.5, color=c.C_GREY)
    ax.set_xticks(list(xs)); ax.set_xticklabels(names)
    ax.set_ylabel("share of all evaluations (%)")
    ax.set_ylim(0, 112)
    ax.set_title("2 · where the budget goes", loc="left", fontweight="bold")
    ax.legend(loc="upper left", framealpha=0.95, fontsize=10,
              bbox_to_anchor=(0.0, -0.09), ncol=3, frameon=False)

    # ---- panel 3: how runs terminated ------------------------------------
    # Two dot clouds per block (10 runs = 5 seeds x 2 arms) joined at their
    # medians. The vertical gap is how long a run kept going after it had
    # already found its final champion.
    ax = axes[2]
    for i, b in enumerate(BLOCKS):
        end, last = S[b]["endgen"], S[b]["lastimp"]
        ax.scatter([i - 0.13] * len(last), last, s=42, color=c.C_GREEN, zorder=3,
                   label="last improvement" if i == 0 else None)
        ax.scatter([i + 0.13] * len(end), end, s=42, marker="s", color=c.C_RED,
                   zorder=3, label="run ended" if i == 0 else None)
        ax.plot([i - 0.13, i + 0.13], [st.median(last), st.median(end)],
                color=c.C_GREY, lw=1.4, zorder=2)
    ax.axhline(30, ls="--", color=c.C_GREY, lw=1.2)
    ax.text(len(BLOCKS) - 0.5, 30.3, "30-generation horizon", ha="right",
            va="bottom", fontsize=9.5, color=c.C_GREY)
    ax.set_xticks(list(xs)); ax.set_xticklabels(names)
    ax.set_ylabel("generation")
    ax.set_title("3 · when runs stopped", loc="left", fontweight="bold")
    ax.legend(loc="lower left", framealpha=0.95, fontsize=10)
    ax.set_ylim(0, 34)

    # ---- panel 4: does a Gen0 lead survive the main loop? -----------------
    ax = axes[3]
    STY = {("medium", "G"): (c.C_BLUE, "-", "o"), ("medium", "F"): (c.C_ORANGE, "-", "o"),
           ("large", "G"): (c.C_BLUE, "--", "s"), ("large", "F"): (c.C_ORANGE, "--", "s")}
    for sh in ("medium", "large"):
        for a in ("G", "F"):
            lead = []
            for stage in ("gen0", "gen10", "final"):
                v = []
                for s_ in c.SEEDS:
                    rc, rn = c.traj("capped", a, s_, sh), c.traj("native", a, s_, sh)
                    if stage == "gen0":
                        v.append(c.gen0(rn) / c.gen0(rc) - 1)
                    elif stage == "gen10":
                        v.append(c.gen10(rn) / c.gen10(rc) - 1)
                    else:
                        v.append(rn[-1]["best_gflops_so_far"] / rc[-1]["best_gflops_so_far"] - 1)
                lead.append(st.median(v) * 100)
            col, ls, mk = STY[(sh, a)]
            ax.plot([0, 1, 2], lead, ls, color=col, marker=mk, lw=2.0, ms=7,
                    label=f"{sh} · arm {a}")
            ax.annotate(f"{lead[0]:+.0f} %", (0, lead[0]), textcoords="offset points",
                        xytext=(-6, 4), ha="right", fontsize=10, color=col)
    ax.axhline(0, color=c.C_GREY, lw=1.2)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["Gen0", "gen 10", "end"])
    ax.set_ylabel("native lead over capped, same arm (%)")
    ax.set_title("4 · the margin collapses", loc="left", fontweight="bold")
    ax.legend(loc="upper right", fontsize=9.5, framealpha=0.95)

    c.provenance(fig, "trajectory.jsonl · stage3_* + stage5_native_* · 5 seeds x 2 arms · medians")
    c.save(fig, "p15_search_budget")

    for b in BLOCKS:
        s = S[b]
        print(f"  {b[0]:7}{b[1]:7} Gen0->g10 +{s['early']*100:5.2f} %  "
              f"g10->end +{s['late']*100:4.2f} %  Gen0 share {s['g0']*100:5.2f} %  "
              f"by g10 {s['by10']*100:5.2f} %  gen10/final {s['gen10frac']:.4f}  "
              f"end gen {min(s['endgen'])}-{max(s['endgen'])}  "
              f"last-improvement median {st.median(s['lastimp']):.1f}")


if __name__ == "__main__":
    main()
