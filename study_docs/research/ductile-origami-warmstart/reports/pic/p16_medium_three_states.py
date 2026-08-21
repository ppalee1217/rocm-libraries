"""P15 -- medium: the tight sub-criteria, and one quantity in three instrument states.

Left  : per-seed ln(F/G) for the three trajectory sub-criteria (Gen0, gen-10, AUC),
        medium capped. Read from trajectory.jsonl; these never touch the 7x
        champion remeasure, so they are unaffected by the instrument defect.
Right : the final-champion ratio -- the *same* underlying quantity -- as measured by
        (1) the defective instrument (campaign 1), (2) the repaired instrument at
        nw=1400/RBS=401 capped, (3) the repaired instrument native, with both null
        envelopes drawn behind it.

Run on the HOST (matplotlib 3.8.2). Idempotent: no timestamps, no randomness.
"""
from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np

import common
from common import ARM_COLOR, C_GREY

# deterministic per-seed marker + x-offset (no jitter, so re-runs are identical)
MARKERS = ["o", "s", "^", "D", "v"]
OFFS = [-0.20, -0.10, 0.00, 0.10, 0.20]
INK = "#2B2B2B"


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def traj_ln(seed):
    """(gen0, gen10, auc) ln(F/G) for one seed on medium capped."""
    rg = common.traj("capped", "G", seed, "medium")
    rf = common.traj("capped", "F", seed, "medium")
    budget = min(rg[-1]["cumulative_complete_evals"],
                 rf[-1]["cumulative_complete_evals"])
    return (
        math.log(common.gen0(rf) / common.gen0(rg)),
        math.log(common.gen10(rf) / common.gen10(rg)),
        math.log(common.auc(rf, budget) / common.auc(rg, budget)),
    )


TRAJ = {s: traj_ln(s) for s in common.SEEDS}
CRIT = ["Gen0", "gen-10", "AUC"]

# state 1: the defective instrument. These are the campaign-1 canonical endpoints
# (F/G = 0.9971 / 0.7053 / 1.0746 / 2.1175 / 0.3551). They are NOT hardcoded here --
# stage3_baseline/seed_*/medium/champion_interleaved.json still holds campaign 1,
# so the loader returns them directly; the assert below pins that.
DEFECT = {s: common.canonical_ratio("medium", s) for s in common.SEEDS}
_CAMPAIGN1 = [0.9971, 0.7053, 1.0746, 2.1175, 0.3551]
assert all(abs(DEFECT[s] - v) < 5e-5 for s, v in zip(common.SEEDS, _CAMPAIGN1)), \
    "stage3_baseline medium no longer holds the campaign-1 endpoints"

# state 2: repaired instrument, capped -- the two nw=1400/RBS=401 cells averaged
c03, conf = common.cell_per_seed("C03_"), common.cell_per_seed("C03CONF_")
REPAIRED = {s: 0.5 * (c03[s]["mean_ln"] + conf[s]["mean_ln"]) for s in common.SEEDS}

# state 3: repaired instrument, native
nat = common.cell_per_seed("STAGE2_NATIVE_")
NATIVE = {s: nat[s]["mean_ln"] for s in common.SEEDS}


def pooled_sd(cell):
    """RMS of the per-seed sample_sd (equal n_windows on every seed)."""
    ps = common.cell_per_seed(cell)
    sds = [ps[s]["sample_sd"] for s in common.SEEDS]
    return float(np.sqrt(np.mean(np.square(sds)))), sds


SD_GG, _gg = pooled_sd("N8_NATIVE_GVSG_")      # G/G' null: both arms baseline
SD_FF, _ff = pooled_sd("N8b_NATIVE_FFNULL_")   # F/F' null: both arms guided

STATES = [
    ("defective\ncampaign 1", [math.log(DEFECT[s]) for s in common.SEEDS]),
    ("repaired capped\nnw1400 / RBS401", [REPAIRED[s] for s in common.SEEDS]),
    ("repaired native\nnw1400 / RBS401", [NATIVE[s] for s in common.SEEDS]),
]

# --------------------------------------------------------------------------
# figure
# --------------------------------------------------------------------------
fig = plt.figure(figsize=(12.2, 6.2))
gs = fig.add_gridspec(3, 2, width_ratios=[1.0, 1.32], hspace=0.62, wspace=0.20)
axL = fig.add_subplot(gs[:, 0])
axS = [fig.add_subplot(gs[k, 1]) for k in range(3)]

# ---- left: the three trajectory sub-criteria ----
for j, crit in enumerate(CRIT):
    vals = [TRAJ[s][j] for s in common.SEEDS]
    for i, s in enumerate(common.SEEDS):
        axL.scatter(j + OFFS[i], vals[i], marker=MARKERS[i], s=54, c=INK,
                    edgecolors="white", linewidths=0.7, zorder=5,
                    label=str(s) if j == 0 else None)
    axL.hlines(np.median(vals), j - 0.30, j + 0.30, color=C_GREY, lw=2.2, zorder=4)

axL.axhline(0.0, color=INK, lw=1.1, alpha=0.7, zorder=3)
axL.set_xticks(range(3))
axL.set_xticklabels(
    [f"{c}\n{sum(1 for s in common.SEEDS if TRAJ[s][j] > 0)}/5 seeds > 0"
     for j, c in enumerate(CRIT)])
axL.set_xlim(-0.55, 2.55)
axL.set_ylim(-0.158, 0.105)
axL.set_ylabel("ln(F/G)")
axL.set_title("trajectory sub-criteria, medium capped", pad=10)
axL.legend(title="seed", fontsize=11, title_fontsize=11, loc="lower right",
           ncol=2, framealpha=0.95, handletextpad=0.2, columnspacing=0.8)
_span_note = axL.text(0.015, 0.975, "", transform=axL.transAxes, ha="left",
                      va="top", fontsize=11, color=C_GREY)

# ---- right: the same quantity, three instrument states, three x-scales ----
# One shared scale would squash states 2 and 3 (and both null envelopes) into a
# flat line, so each state gets the scale it needs. The zoom band drawn on the
# defective strip is exactly the x-range of the two strips below it, so the
# change of scale is on the figure rather than left to the reader.
WIDE = 1.16          # x half-range of the defective strip
ZOOM = 0.145         # x half-range of the two repaired strips
BBOX = dict(fc="white", ec="none", alpha=0.85, pad=1.5)


def _stagger(vals, step=0.20):
    """Deterministic vertical spread inside a strip; no jitter."""
    order = np.argsort(vals, kind="stable")
    off = np.zeros(len(vals))
    for rank, idx in enumerate(order):
        off[idx] = ((rank % 3) - 1) * step
    return off


for k, (name, vals) in enumerate(STATES):
    ax = axS[k]
    half = WIDE if k == 0 else ZOOM

    if k == 0:
        ax.axvspan(-ZOOM, ZOOM, color=C_GREY, alpha=0.16, lw=0, zorder=1)
        ax.text(ZOOM, -0.72, "  x-range of the two strips below", ha="left",
                va="bottom", fontsize=10, color=C_GREY)
    if k == 2:
        # both null envelopes, directly labelled rather than put in a legend box
        ax.axvspan(-SD_FF, SD_FF, color=ARM_COLOR["F"], alpha=0.22, lw=0, zorder=1)
        ax.axvspan(-SD_GG, SD_GG, color=ARM_COLOR["G"], alpha=0.45, lw=0, zorder=2)
        ax.text(-SD_FF + 0.003, -0.90, "F/F' null  ±1 sd = %.3f" % SD_FF,
                ha="left", va="bottom", fontsize=10.5, color=ARM_COLOR["F"],
                zorder=8, bbox=BBOX)
        ax.text(half - 0.02 * half, -0.90, "G/G' null  ±1 sd = %.3f" % SD_GG,
                ha="right", va="bottom", fontsize=10.5, color=ARM_COLOR["G"],
                zorder=8, bbox=BBOX)

    ax.axvline(0.0, color=INK, lw=1.1, alpha=0.7, zorder=3)
    off = _stagger(vals)
    for i in range(len(common.SEEDS)):
        ax.scatter(vals[i], off[i], marker=MARKERS[i], s=54, c=INK,
                   edgecolors="white", linewidths=0.7, zorder=6)
    ax.vlines(np.median(vals), -0.62, 0.62, color=C_GREY, lw=2.2, zorder=5)

    ax.set_xlim(-half, half)
    ax.set_ylim(-0.95, 0.95)
    ax.set_yticks([])
    ax.tick_params(axis="x", labelsize=11)
    ax.text(-half + 0.02 * half, 0.90, name.replace("\n", "  "), ha="left",
            va="top", fontsize=11.5, color=INK, zorder=8, bbox=BBOX)
    ax.text(half - 0.02 * half, 0.90, "median F/G %.4f" % math.exp(np.median(vals)),
            ha="right", va="top", fontsize=11, color=INK, zorder=8, bbox=BBOX)

axS[0].set_title("final-champion ratio, three instrument states", pad=10)
axS[2].set_xlabel("ln(F/G)  (final champion)")

_span_note.set_text("y-axis span %.2f" % (axL.get_ylim()[1] - axL.get_ylim()[0]))

common.provenance(fig, "trajectory.jsonl (stage3 capped) | stage3_baseline/*/medium/"
                       "champion_interleaved.json | medium_pilot401: C03, C03CONF, "
                       "STAGE2_NATIVE, N8_NATIVE_GVSG, N8b_NATIVE_FFNULL")
fig.subplots_adjust(left=0.090, right=0.988, top=0.885, bottom=0.150)
common.save(fig, "p16_medium_three_states.png", tight=False)

# --------------------------------------------------------------------------
# stdout: every number that reached the figure
# --------------------------------------------------------------------------
print("left panel -- ln(F/G), medium capped trajectory sub-criteria")
for j, c in enumerate(CRIT):
    v = [TRAJ[s][j] for s in common.SEEDS]
    print("  %-7s " % c + " ".join("%+.5f" % x for x in v)
          + "  median %+.5f  %d/5 > 0" % (np.median(v), sum(1 for x in v if x > 0)))
print("right panel -- ln(F/G), final champion")
for name, vals in STATES:
    print("  %-22s " % name.replace("\n", " ") + " ".join("%+.5f" % x for x in vals)
          + "  median ln %+.5f  median F/G %.4f  %d/5 > 0"
          % (np.median(vals), math.exp(np.median(vals)),
             sum(1 for x in vals if x > 0)))
print("  defective F/G per seed: " + " ".join("%.4f" % DEFECT[s] for s in common.SEEDS))
print("native null envelopes (sample_sd per seed -> RMS pooled)")
print("  G/G'  " + " ".join("%.5f" % x for x in _gg) + "  -> pooled %.5f" % SD_GG)
print("  F/F'  " + " ".join("%.5f" % x for x in _ff) + "  -> pooled %.5f" % SD_FF)
print("  |median native effect| = %.5f ; F/F' envelope / effect = %.1fx"
      % (abs(np.median(STATES[2][1])), SD_FF / abs(np.median(STATES[2][1]))))
