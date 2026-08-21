#!/usr/bin/env python3
"""P9 -- per-gene sensitivity S_g for all 27 free genes on all three shapes.

Source: 260809-s14-pershape-guidance/out-capped/guidance-{shape}.json, read
through common.gene_table().

Three states are drawn distinctly, because they are three different things:

  * S_g >= threshold  -> gene activated, the prior is applied to it
  * S_g <  threshold  -> gene estimated, left uniform (fallback)
  * S_g is None       -> **no estimate at all** (fewer than two trusted
                         values).  It is never plotted as zero.

On tiny every estimable gene comes back at exactly 0.000, which is a measured
zero and again not the same thing as "no estimate"; those get their own mark.

Run on the HOST:  python3 p09_gene_sensitivity.py
"""
from __future__ import annotations

import re

import common
from common import C_GREEN, C_GREY, C_LIGHT, C_PURPLE, C_RED

SHAPES = ["tiny", "medium", "large"]
NO_EST_STUB = 0.0105  # bar length used to draw the "no estimate" hatched mark


def activation_threshold(shape):
    """Recover the selection cut from the artifact's own fallback_reason.

    Non-selected genes carry fallback_reason 'sensitivity_below_0_05', so the
    0.05 cut is read out of the shipped file rather than transcribed.
    """
    thr = set()
    for v in common.guidance(shape)["genes"].values():
        m = re.fullmatch(r"sensitivity_below_(\d+)_(\d+)", v.get("fallback_reason") or "")
        if m:
            thr.add(float(f"{m.group(1)}.{m.group(2)}"))
    if len(thr) != 1:
        raise RuntimeError(f"{shape}: ambiguous activation threshold {thr}")
    return thr.pop()


def main():
    tables = {s: common.gene_table(s) for s in SHAPES}
    meta = {s: common.guidance(s) for s in SHAPES}
    thresholds = {s: activation_threshold(s) for s in SHAPES}
    thr = next(iter(set(thresholds.values())))
    assert len(set(thresholds.values())) == 1, thresholds

    genes = sorted(tables["large"], key=lambda r: r[0])
    gene_names = [g for g, *_ in genes]
    assert all(sorted(n for n, *_ in tables[s]) == sorted(gene_names)
               for s in SHAPES)

    # one shared row order for all three panels: strongest anywhere at the top,
    # the no-estimate gene pinned to the bottom.
    def keyf(g):
        vals = [dict((n, s) for n, s, *_ in tables[sh]).get(g) for sh in SHAPES]
        est = [v for v in vals if v is not None]
        return (0 if est else 1, -(max(est) if est else 0.0), g)

    order = sorted(gene_names, key=keyf)
    ypos = {g: len(order) - 1 - i for i, g in enumerate(order)}

    fig, axes = common.new_fig(1, 3, figsize=(15.0, 8.6), sharex=True,
                               sharey=True)

    xmax = max(s for sh in SHAPES for _, s, *_ in tables[sh] if s is not None)
    counts = {}

    for ax, shape in zip(axes, SHAPES):
        rows = {g: (s, a) for g, s, a, _ in tables[shape]}
        n_act = meta[shape]["n_genes_activated"]
        counts[shape] = n_act

        # alternating row bands so a gene can be tracked across the panels
        for i, g in enumerate(order):
            if i % 2 == 0:
                ax.axhspan(ypos[g] - 0.5, ypos[g] + 0.5, facecolor="#F4F4F4",
                           edgecolor="none", zorder=0)

        ax.axvline(thr, color=C_RED, ls="--", lw=1.5, zorder=1)

        for g in order:
            s, act = rows[g]
            y = ypos[g]
            if s is None:
                ax.barh(y, NO_EST_STUB, height=0.62, facecolor="white",
                        edgecolor=C_PURPLE, lw=1.4, hatch="///", zorder=3)
                continue
            if s == 0.0:
                # measured zero: a mark on the axis so the gene is not simply
                # missing from the panel
                ax.plot([0.0], [y], marker="|", ms=11, mew=2.0, color=C_GREY,
                        zorder=3)
                continue
            ax.barh(y, s, height=0.62, zorder=3,
                    facecolor=(C_GREEN if act else C_LIGHT),
                    edgecolor=(C_GREEN if act else C_GREY), lw=0.9)
            if act:
                ax.text(s + xmax * 0.018, y, f"{s:.3f}", va="center",
                        ha="left", fontsize=11, color="black")

        role = meta[shape]["shape_role"]
        ax.set_title(f"{shape}  ·  {n_act} / {len(order)} activated\n"
                     f"({role})", fontsize=15, pad=9)
        ax.set_xlabel("sensitivity  $S_g$")
        ax.set_xlim(-0.004, xmax * 1.30)
        ax.set_ylim(-0.75, len(order) - 0.25)
        ax.grid(axis="y", alpha=0.0)
        ax.tick_params(axis="x", labelsize=11.5)

    axes[0].set_yticks([ypos[g] for g in order])
    axes[0].set_yticklabels(order, fontsize=11.5)
    axes[0].set_ylabel("gene  (27 free genes)")

    # threshold callout, placed low where every panel is empty
    axes[1].text(thr + xmax * 0.03, 3.2, f"activation cut\n$S_g \\geq$ {thr}",
                 color=C_RED, fontsize=12.5, va="center", ha="left")

    # tiny returns an exact zero for every gene it could estimate at all
    n_zero = sum(1 for _, s, *_ in tables["tiny"] if s == 0.0)
    axes[0].text(xmax * 0.62, len(order) / 2,
                 f"all {n_zero} estimable genes\ncome back at exactly\n"
                 f"$S_g$ = 0.000",
                 fontsize=12.5, ha="center", va="center", color=C_GREY,
                 linespacing=1.6)

    import matplotlib.lines as mlines
    import matplotlib.patches as mpatches
    handles = [
        mpatches.Patch(facecolor=C_GREEN, edgecolor=C_GREEN,
                       label="activated — prior applied to this gene"),
        mpatches.Patch(facecolor=C_LIGHT, edgecolor=C_GREY,
                       label=f"estimated, below the cut — left uniform"),
        mlines.Line2D([], [], color=C_GREY, marker="|", ms=11, mew=2.0,
                      ls="none", label="$S_g$ = 0.000 exactly (measured zero)"),
        mpatches.Patch(facecolor="white", edgecolor=C_PURPLE, hatch="///",
                       label="$S_g$ = None — no estimate "
                             "(fewer than two trusted values)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
               fontsize=12, bbox_to_anchor=(0.5, 0.005))

    fig.suptitle("Per-gene sensitivity across the three shapes: "
                 f"{counts['tiny']} / {counts['medium']} / {counts['large']} "
                 "genes activated of 27", y=0.985)

    common.provenance(fig, "260809-s14-pershape-guidance/out-capped/"
                           "guidance-{tiny,medium,large}.json")
    fig.tight_layout(rect=(0, 0.075, 1, 0.955))
    common.save(fig, "p09_gene_sensitivity", tight=False)

    for shape in SHAPES:
        t = tables[shape]
        act = [(g, s) for g, s, a, _ in t if a]
        none = [g for g, s, *_ in t if s is None]
        zeros = [g for g, s, *_ in t if s == 0.0]
        print(f"  {shape:6s} n_genes={len(t)} activated={len(act)} "
              f"(json says {meta[shape]['n_genes_activated']}) "
              f"no-estimate={none} exact-zeros={len(zeros)} "
              f"cut={thresholds[shape]}")
        for g, s in act:
            print(f"           + {g:32s} S_g={s:.6f}")


if __name__ == "__main__":
    main()
