"""P2 -- the twelve gate cells: positive seed-pairs out of 5.

4 blocks x 3 margin-free sub-criteria (Gen0 best, gen-10 best, AUC).  Every count
is recomputed here from `trajectory.jsonl` through `common.gate_counts`, which
mirrors `analyze_large.py:10-34`.

Two things this figure has to get across besides the numbers:

  * the pre-registered requirement is >= 4 / 5 in *every* cell, and no cell here
    reaches it -- so the shade encodes *distance below the line*, on a single-hue
    sequential ramp.  Deliberately not red/green: nothing passes, and a pass/fail
    palette would invite the reader to hunt for the green cell that does not exist.
  * the two capped rows are the gate; the two native rows are the
    NATIVE-P0-ROBUSTNESS-20260811 addendum and are *not* gate components.  They
    are banded apart, because conflating them is the likeliest misreading.

The verdict wording lives on the slide, not in the image.

Run on the HOST:  python3 p02_gate_matrix.py
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle

import common as C

# --------------------------------------------------------------------------
# what to draw
# --------------------------------------------------------------------------
# (label, level, shape, band)  -- capped rows first: they are the gate.
ROWS = [
    ("medium capped", "capped", "medium", "gate"),
    ("large capped", "capped", "large", "gate"),
    ("medium native", "native", "medium", "addendum"),
    ("large native", "native", "large", "addendum"),
]
COLS = [("gen0", "Gen0 best"), ("gen10", "gen-10 best"), ("auc", "AUC")]

N_SEEDS = len(C.SEEDS)          # 5 paired seeds
REQUIRED = 4                    # pre-registered: >= 4 / 5 positive in every cell

# single-hue sequential ramp: pale -> house blue, darker = further below the line
RAMP = LinearSegmentedColormap.from_list("gate_deficit", ["#EEF4F9", C.C_BLUE])
NORM = Normalize(vmin=0, vmax=REQUIRED)


def deficit(n):
    """How far a cell sits below the >= 4 / 5 requirement (0 once it is met)."""
    return max(0, REQUIRED - n)


# --------------------------------------------------------------------------
# geometry (explicit, so the two bands can be separated by a real gap)
# --------------------------------------------------------------------------
ROW_Y = [3.70, 2.70, 1.30, 0.30]     # gap between index 1 and 2 = the band break
SEP_Y = 2.02                         # separating rule
GRP_Y = {"gate": 4.28, "addendum": 1.80}
HALF_H, HALF_W = 0.42, 0.44
HDR_Y, REQ_Y = 5.02, 4.66

counts = {lbl: C.gate_counts(level, shape) for lbl, level, shape, _ in ROWS}

fig, ax = C.new_fig()
fig.subplots_adjust(left=0.235, right=0.985, top=0.880, bottom=0.115)
ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlim(-0.55, len(COLS) - 0.45)
ax.set_ylim(-0.30, 5.35)

# ---- column headers + the requirement, stated once per column ------------
for j, (_, name) in enumerate(COLS):
    ax.text(j, HDR_Y, name, ha="center", va="center", fontsize=13.5, weight="bold")
    ax.text(j, REQ_Y, "requires ≥ 4 / 5", ha="center", va="center",
            fontsize=11, color=C.C_GREY)

# ---- band labels ---------------------------------------------------------
ax.text(-0.53, GRP_Y["gate"], "PRE-REGISTERED GATE", ha="left", va="center",
        fontsize=11.5, weight="bold", color="#1A1A1A")
ax.text(-0.53, GRP_Y["addendum"],
        "ROBUSTNESS ADDENDUM  —  reported, not a gate component",
        ha="left", va="center", fontsize=11.5, weight="bold", color=C.C_GREY)

# the rule that separates the two bands: solid, full width, unmissable
ax.plot([-0.55, len(COLS) - 0.45], [SEP_Y, SEP_Y],
        color="#1A1A1A", lw=1.6, solid_capstyle="butt", zorder=4)

# ---- cells ---------------------------------------------------------------
for i, (lbl, _, _, band) in enumerate(ROWS):
    y = ROW_Y[i]
    ax.text(-0.62, y, lbl, ha="right", va="center", fontsize=13,
            weight="bold" if band == "gate" else "normal",
            color="#1A1A1A" if band == "gate" else "#4D4D4D", clip_on=False)
    for j, (key, _) in enumerate(COLS):
        n = counts[lbl][key]
        shade = NORM(deficit(n))
        ax.add_patch(Rectangle((j - HALF_W, y - HALF_H), 2 * HALF_W, 2 * HALF_H,
                               facecolor=RAMP(shade), edgecolor="white",
                               linewidth=1.2, zorder=2))
        ax.text(j, y, f"{n}/{N_SEEDS}", ha="center", va="center", fontsize=21,
                weight="bold", color="white" if shade > 0.55 else "#1A1A1A",
                zorder=3)

fig.suptitle("Directional-consistency gate — positive seed-pairs out of 5",
             x=0.5, y=0.972, va="top", fontsize=16)

fig.text(0.235, 0.030,
         "shade = distance below the required 4 / 5 (darker = further below)",
         ha="left", va="bottom", fontsize=9.5, color=C.C_GREY)

C.provenance(fig, "trajectory.jsonl · stage3_{baseline,guided} + "
                  "stage5_native_{baseline,guided} · seeds 24001-24005")
C.save(fig, "p02_gate_matrix", tight=False)

for lbl, _, _, band in ROWS:
    c = counts[lbl]
    print(f"  {lbl:<14s} [{band:9s}]  Gen0 {c['gen0']}/5   "
          f"gen-10 {c['gen10']}/5   AUC {c['auc']}/5")
plt.close("all")
