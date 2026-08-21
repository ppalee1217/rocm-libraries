"""Shared style + data loaders for the S14 closeout figures.

Every figure script in this directory imports from here. Run on the HOST
(matplotlib 3.8.2), never inside the container: the artifact paths below are
host paths, and container-created files come out root-owned.

All loaders read the canonical artifacts directly. Nothing here hardcodes a
result value -- if a number appears in a figure it was computed from an
artifact at render time.
"""
from __future__ import annotations

import json
import os
from statistics import median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------
BASE = "/data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-baseline"
GUIDANCE = "/data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-guidance/out-capped"
PIC = os.path.dirname(os.path.abspath(__file__))

SEEDS = [24001, 24002, 24003, 24004, 24005]

# capped arms live in stage3_*, native arms in stage5_native_*
ARM_DIR = {
    ("capped", "G"): "stage3_baseline",
    ("capped", "F"): "stage3_guided",
    ("native", "G"): "stage5_native_baseline",
    ("native", "F"): "stage5_native_guided",
}

PILOT = f"{BASE}/medium_pilot401/results"
XWIN = f"{BASE}/large_xwindow/results"

# --------------------------------------------------------------------------
# style
# --------------------------------------------------------------------------
# Okabe-Ito colour-blind-safe palette
C_BLUE = "#0072B2"
C_ORANGE = "#E69F00"
C_GREEN = "#009E73"
C_RED = "#D55E00"
C_PURPLE = "#CC79A7"
C_SKY = "#56B4E9"
C_YELLOW = "#F0E442"
C_GREY = "#7F7F7F"
C_LIGHT = "#DDDDDD"

# fixed semantics for the consistency categories (P17)
CAT_COLOR = {
    "better": C_GREEN,
    "worse": C_RED,
    "tie": C_LIGHT,
    "scale-dependent": C_ORANGE,
}

# arm colours, used consistently across every figure
ARM_COLOR = {"G": C_BLUE, "F": C_ORANGE}

plt.rcParams.update({
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "font.size": 13,
    "axes.titlesize": 17,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "-",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

FIGSIZE = (8.0, 4.5)  # 8.0x4.5in @ 200dpi = 1600x900, 16:9


def new_fig(nrows=1, ncols=1, figsize=FIGSIZE, **kw):
    """A 16:9 figure at the house size."""
    return plt.subplots(nrows, ncols, figsize=figsize, **kw)


def provenance(fig, text):
    """Stamp a short data-source tag in the bottom-right.

    The compact outline strips all source citations, so each figure has to
    carry its own provenance to stay traceable away from the deck.
    """
    fig.text(0.995, 0.005, text, ha="right", va="bottom",
             fontsize=7.5, color=C_GREY, style="italic")


def save(fig, name, tight=True):
    """Write <name>.png into pic/. Idempotent: same input -> same file."""
    if not name.endswith(".png"):
        name += ".png"
    out = os.path.join(PIC, name)
    if tight:
        fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out}")
    return out


# --------------------------------------------------------------------------
# trajectory loaders  (mirrors analyze_large.py:10-34 traj/gen0/gen10/auc)
# --------------------------------------------------------------------------
def traj(level, arm, seed, shape):
    """Load one trajectory.jsonl. level in {capped, native}, arm in {G, F}."""
    p = f"{BASE}/{ARM_DIR[(level, arm)]}/seed_{seed}/{shape}/trajectory.jsonl"
    with open(p) as fh:
        return [json.loads(l) for l in fh if l.strip()]


def gen0(rows):
    return rows[0]["best_gflops_so_far"]


def gen10(rows):
    c = [x for x in rows if x["gen"] <= 10]
    return (c[-1] if c else rows[-1])["best_gflops_so_far"]


def auc(rows, budget):
    """Step-hold integral of best-so-far over cumulative completed evals."""
    xs = [x["cumulative_complete_evals"] for x in rows]
    ys = [x["best_gflops_so_far"] for x in rows]
    a = 0.0
    for i in range(1, len(xs)):
        x0, x1 = xs[i - 1], min(xs[i], budget)
        if x1 > x0:
            a += (x1 - x0) * ys[i - 1]
        if xs[i] >= budget:
            break
    return a


def gate_counts(level, shape):
    """Positive-seed counts for the three margin-free sub-criteria.

    Returns {'gen0': n, 'gen10': n, 'auc': n} out of 5.
    """
    g0 = g10 = ga = 0
    for s in SEEDS:
        rg, rf = traj(level, "G", s, shape), traj(level, "F", s, shape)
        if gen0(rf) > gen0(rg):
            g0 += 1
        if gen10(rf) > gen10(rg):
            g10 += 1
        b = min(rg[-1]["cumulative_complete_evals"],
                rf[-1]["cumulative_complete_evals"])
        if auc(rf, b) > auc(rg, b):
            ga += 1
    return {"gen0": g0, "gen10": g10, "auc": ga}


def gen0_centre_extreme(level, shape, seed):
    """(centre, extreme) for generation 1.

    centre  = generation_Q_median_any_valid   (what guidance moves)
    extreme = generation_batch_best_gflops    (what the GA selects on)
    """
    row = traj(level, "G", seed, shape)[0], traj(level, "F", seed, shape)[0]
    g, f = row
    return {
        "centre": f["generation_Q_median_any_valid"] / g["generation_Q_median_any_valid"],
        "extreme": f["generation_batch_best_gflops"] / g["generation_batch_best_gflops"],
    }


# --------------------------------------------------------------------------
# pilot401 / cross-window cell loaders
# --------------------------------------------------------------------------
def cell_dir(name, root=PILOT):
    """Resolve a cell by prefix, e.g. 'C03_' -> C03_nw1400_rbs401."""
    for d in sorted(os.listdir(root)):
        if d.startswith(name):
            return os.path.join(root, d)
    raise FileNotFoundError(f"no cell starting with {name!r} in {root}")


def cell_summary(name, root=PILOT):
    with open(os.path.join(cell_dir(name, root), "summary.json")) as fh:
        return json.load(fh)


def cell_per_seed(name, root=PILOT):
    """{seed: {'mean_ln':…, 'sample_sd':…, …}} for one cell."""
    s = cell_summary(name, root)
    ps = s["per_seed"]
    if isinstance(ps, dict):
        return {int(k): v for k, v in ps.items()}
    return {int(x.get("seed", SEEDS[i])): x for i, x in enumerate(ps)}


def cell_repeats(name, seed, root=PILOT):
    """All raw per-repeat measurements for one (cell, seed).

    Returns [{'arm','gflops','repeat','position_in_repeat','window'}, ...]
    """
    sd = os.path.join(cell_dir(name, root), f"seed_{seed}")
    out = []
    for w in sorted(os.listdir(sd)):
        p = os.path.join(sd, w, "champion_interleaved_raw.jsonl")
        if not os.path.exists(p):
            continue
        with open(p) as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    r["window"] = w
                    out.append(r)
    return out


# --------------------------------------------------------------------------
# canonical endpoint loader (campaign-1 style champion_interleaved.json)
# --------------------------------------------------------------------------
def champion(path):
    with open(path) as fh:
        return json.load(fh)


def canonical_ratio(shape, seed, arm_dir="stage3_baseline"):
    """F/G median ratio recorded on a canonical champion_interleaved.json."""
    p = f"{BASE}/{arm_dir}/seed_{seed}/{shape}/champion_interleaved.json"
    return champion(p)["F_over_G_median_ratio"]


def per_shape_noise():
    with open(f"{BASE}/noise/per_shape_noise.json") as fh:
        return json.load(fh)["shapes"]


# --------------------------------------------------------------------------
# guidance loaders (per-gene sensitivity)
# --------------------------------------------------------------------------
def guidance(shape):
    with open(f"{GUIDANCE}/guidance-{shape}.json") as fh:
        return json.load(fh)


def gene_table(shape):
    """[(gene, S_g, activated, trusted), ...] sorted by S_g descending.

    S_g is None for genes with no sensitivity estimate (1 of 27 on every
    shape). It is kept as None rather than coerced to 0.0 -- "no estimate"
    and "estimated as zero" are different things -- and sorts last.
    """
    g = guidance(shape)["genes"]
    rows = [(k, v.get("sensitivity"), bool(v.get("activated")),
             bool(v.get("trusted"))) for k, v in g.items()]
    rows.sort(key=lambda r: (r[1] is None, -(r[1] or 0.0)))
    return rows


__all__ = [n for n in dir() if not n.startswith("_")]
