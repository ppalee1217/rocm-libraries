#!/usr/bin/env python3
"""P19 -- can we trust the medium number?  No.  Two panels.

    symptom  ->  root cause

Panel 1  What one measurement actually is, and what went wrong with it. A
         "window" is 7 repeats of arm G interleaved with 7 of arm F, all on one
         fixed kernel, one card, one process, inside ~22 s. It should be the
         most repeatable number in the study. On medium it is BIMODAL. This
         panel also DEFINES the word the next two pages depend on: a repeat
         below 0.95 x its own arm's maximum in that window is a *dropout*.
Panel 2  Why. Warm-up is specified as an ENQUEUE COUNT (321), not a time, and
         it is identical for all three shapes whose kernels differ by 3 orders
         of magnitude. The warm-up sweep gives a clean knee.

The repaired instrument is deliberately NOT on this figure -- that is P20's
result, and showing it here spoiled the split. The clock-ramp hypothesis we
proposed and then disconfirmed used to be panel 3; it is now the backup slide
``apx_clock_disconfirmation``, which imports its loaders from this module.

Everything on this figure is computed from an artifact at render time. The one
fixed constant (the medium kernel duration used to convert enqueue counts to
milliseconds) is commented at its definition.

Run on the HOST:  python3 p19_defect_storyboard.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
import os
import re
from statistics import median

import common as C

# --------------------------------------------------------------------------
# panel 1 -- the symptom
# --------------------------------------------------------------------------
# The defective instrument: campaign-1 canonical 7x interleaved remeasure.
# This is the file the champion_interleaved_status.json points at as
# "raw_measurements_path". Seed 24001 / medium is the worked example.
DEFECT_SEED = 24001
DEFECT_RAW = f"{C.BASE}/stage3_baseline/seed_{DEFECT_SEED}/medium/champion_interleaved_raw.jsonl"
DEFECT_STATUS = f"{C.BASE}/stage3_baseline/seed_{DEFECT_SEED}/medium/champion_interleaved_status.json"

# Dropout definition used everywhere in this study: below 0.95 of the arm's max.
DROPOUT_FRAC = 0.95

# The arm shown. F is the worked example quoted in the report text; both arms
# are bimodal, and panel 1 prints G's spread alongside so this is not a pick.
ARM = "F"

# The repaired instrument: the same seed and arm re-run under the pilot401
# repair cell C03 (num-warmups 1400 / RBS 401). Window w01 is the FIRST window,
# chosen by position and not by value -- see REPAIR_WINDOW below.
REPAIR_CELL = "C03_"
REPAIR_WINDOW = "w01"


def _epoch(ts: str) -> float:
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()


def load_defective():
    with open(DEFECT_RAW) as fh:
        rows = [json.loads(l) for l in fh if l.strip()]
    with open(DEFECT_STATUS) as fh:
        st = json.load(fh)
    return rows, st


def load_repaired():
    rows = C.cell_repeats(REPAIR_CELL, DEFECT_SEED)
    return [r for r in rows if r["window"] == REPAIR_WINDOW]


# --------------------------------------------------------------------------
# panel 2 -- the root cause
# --------------------------------------------------------------------------
# NOTE ON SOURCE. The brief pointed at medium_ratio_warmup_probe_summary.json.
# That file does NOT hold the five sweep points: its `dropouts_pooled` block has
# exactly two conditions (w321 -> 50.0 %, w1400 -> 4.3 %), because it is the
# two-arm ratio probe, not the sweep. The sweep lives in the standalone
# mechanism probe, which is the artifact the report's knee table is built from:
#   medium_mechanism_probe_summary.json -> variants.W<nw>_norot.pct_below_0p95
# 25 fresh processes per variant, one knob varied, idle-gated.
SWEEP_JSON = f"{C.BASE}/medium_mechanism_probe_summary.json"

# Medium champion kernel duration. HARDCODED, and the only hardcoded number on
# this figure. It converts an enqueue count into a wall time; the counts
# themselves are read from the artifact. ~10 us is the value tabulated for
# medium in report-source-index.md ("medium | ~10 us | ~3.2 ms"), and it
# reproduces that document's published sweep axis exactly:
#   321 -> 3.2   642 -> 6.4   1284 -> 13   2568 -> 26   5136 -> 51 ms.
MEDIUM_KERNEL_US = 10.0

# Warm-up wall time for the OTHER two shapes at the SAME pre-registered 321
# enqueues -- this is the root cause itself, so it is drawn. Large's kernel is
# ~1.87 ms (report-source-index.md, same table), giving ~600 ms of warm-up from
# the identical count. Tiny is dispatch-bound and invariant to warm-up length,
# so it has no position on a wall-time axis and is stated in words instead.
LARGE_KERNEL_MS = 1.87
PREREG_ENQUEUES = 321


def load_sweep():
    """[(num_warmups, warmup_ms, dropout_pct, n, n_below), ...] sorted by nw."""
    with open(SWEEP_JSON) as fh:
        d = json.load(fh)
    out = []
    for name, v in d["variants"].items():
        nw = int(v["overrides"]["num-warmups"])
        assert v["overrides"]["rotating-buffer-size"] == "0", name
        out.append((nw, nw * MEDIUM_KERNEL_US / 1000.0,
                    v["pct_below_0p95"], v["n"], v["n_below_0p95"]))
    out.sort()
    return out


# --------------------------------------------------------------------------
# panel 3 -- the disconfirmation
# --------------------------------------------------------------------------
# NOTE ON SOURCE. The brief pointed at medium_ratio_probe/clock_trace.csv. That
# trace is real but is the WRONG instrument for this panel: it samples at ~96 Hz
# (48,973 samples over the 511 s probe) and is a whole-run trace with no
# per-repeat alignment. The published "1 kHz over 42 traced repeats" result comes
# from the clock-ladder step-1 traces, 3 seeds x 14 records = 42:
#   medium_clockladder/capped/seed_{24001,24004,24005}/s1_trace/
#     trace_*.csv   -- t_epoch,sclk_mhz,busy_pct at 1 kHz
#     probe_*.log   -- INTERLEAVED_CHAMPION_RESULT ... gflops= seconds=
#     probe_*/champion_interleaved_raw.jsonl  -- per-repeat end timestamps
# Alignment mirrors scripts/s14_clockladder_align.py: each record occupied
# [ts_end - seconds, ts_end]; the per-repeat clock estimator is the MAX sclk in
# that window. That estimator is the one validated in the report by reproducing
# both counterexamples bit-for-bit, and this script reproduces them too.
CLOCK_SEEDS = (24001, 24004, 24005)
CLOCK_DIR = f"{C.BASE}/medium_clockladder/capped/seed_%d/s1_trace"

REC_RE = re.compile(
    r"INTERLEAVED_CHAMPION_RESULT .*?repeat=(\d+) arm=(\w) position=(\d+) "
    r"rbs=(\d+) gflops=([\d.]+) seconds=([\d.]+)")


def _glob1(d, pat):
    hits = sorted(f for f in os.listdir(d) if re.fullmatch(pat, f))
    return os.path.join(d, hits[-1])


def load_clock_records():
    """42 per-repeat records: (seed, arm, repeat, gflops, ratio, sclk_max)."""
    rows = []
    for seed in CLOCK_SEEDS:
        d = CLOCK_DIR % seed
        with open(_glob1(d, r"trace_.*\.csv")) as fh:
            tr = [(float(r["t_epoch"]), int(r["sclk_mhz"]), int(r["busy_pct"]))
                  for r in csv.DictReader(fh)]
        with open(_glob1(d, r"probe_.*\.log")) as fh:
            logrecs = REC_RE.findall(fh.read())
        probe = _glob1(d, r"probe_[0-9A-Za-z]+Z")
        with open(os.path.join(probe, "champion_interleaved_raw.jsonl")) as fh:
            raw = [json.loads(l) for l in fh if l.strip()]
        assert len(raw) == len(logrecs) == 14, (seed, len(raw), len(logrecs))

        per = []
        for rec, lg in zip(raw, logrecs):
            assert int(lg[0]) == rec["repeat"] and lg[1] == rec["arm"]
            end = _epoch(rec["timestamp"])
            start = end - float(lg[5])
            win = [x for x in tr if start <= x[0] <= end]
            per.append({"seed": seed, "arm": rec["arm"], "repeat": rec["repeat"],
                        "gflops": rec["gflops"],
                        "sclk_max": max(x[1] for x in win)})
        # ratio to that (run, arm)'s own maximum -- the study's dropout scale
        for arm in ("G", "F"):
            vals = [p for p in per if p["arm"] == arm]
            mx = max(p["gflops"] for p in vals)
            for p in vals:
                p["ratio"] = round(p["gflops"] / mx, 4)
        rows += per
    return rows


# --- rank correlation, implemented here because scipy is not on this host -----
def _avg_ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0        # mid-rank for ties
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def _betacf(a, b, x):
    tiny, eps = 1e-300, 3e-16
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = tiny if abs(d) < tiny else d
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def _betai(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def spearman(x, y):
    """(rho, two-sided p). Mid-ranks for ties; p from the Student-t approx."""
    n = len(x)
    rx, ry = _avg_ranks(list(map(float, x))), _avg_ranks(list(map(float, y)))
    mx, my = sum(rx) / n, sum(ry) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    rho = sxy / math.sqrt(sxx * syy)
    df = n - 2
    t = rho * math.sqrt(df / max(1e-300, 1.0 - rho * rho))
    return rho, _betai(df / 2.0, 0.5, df / (df + t * t))


# --------------------------------------------------------------------------
# drawing helpers
# --------------------------------------------------------------------------
def _strip_x(centre, n, half=0.30):
    """Deterministic horizontal spread -- no jitter, so the PNG is stable."""
    if n == 1:
        return [centre]
    return [centre - half + 2 * half * i / (n - 1) for i in range(n)]


def _stage(ax, n, stage, title):
    """Two-deck panel header: the storyboard beat, then what the panel shows."""
    ax.text(0.0, 1.155, f"{n} · {stage}", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=14, fontweight="bold",
            color=C.C_GREY)
    ax.set_title(title, fontsize=15.5, loc="left", pad=10)


def main():
    # ---------------- load everything first, print what we computed ----------
    def_rows, def_status = load_defective()
    def_arm = [r for r in def_rows if r["arm"] == ARM]
    def_other = [r for r in def_rows if r["arm"] != ARM]
    def_v = [r["gflops"] for r in def_arm]
    def_span = _epoch(def_rows[-1]["timestamp"]) - _epoch(def_rows[0]["timestamp"])
    def_spread = max(def_v) / min(def_v)
    other_spread = (max(r["gflops"] for r in def_other)
                    / min(r["gflops"] for r in def_other))

    sweep = load_sweep()

    print(f"[P1] defective {DEFECT_SEED} arm {ARM}: "
          + " ".join(f"{v:,.0f}" for v in def_v))
    print(f"[P1]   spread {def_spread:.2f}x   (arm "
          f"{def_other[0]['arm']} {other_spread:.2f}x)   "
          f"span {def_span:.1f} s   wall {def_status['wall_seconds_monotonic']:.1f} s")
    print("[P2] sweep " + "  ".join(
        f"{ms:.3g}ms={pct:g}%({nb}/{n})" for _, ms, pct, n, nb in sweep))

    # ---------------- canvas ------------------------------------------------
    fig, axes = C.new_fig(1, 2, figsize=(14.4, 6.4))
    ax1, ax2 = axes

    # =============== panel 1 -- the symptom =================================
    _stage(ax1, "1", "SYMPTOM", "One window = 14 repeats of two fixed kernels")

    # Both arms of the SAME window. Each arm has its own maximum, so each gets
    # its own 0.95 line -- that is exactly how the study scores a dropout, and
    # drawing both makes "arm max" concrete instead of a phrase in a footnote.
    cols = [(0.0, [r["gflops"] for r in def_other], f"arm {def_other[0]['arm']}"),
            (1.0, def_v, f"arm {ARM}")]
    n_drop_win = 0
    for cx, vals, _lab in cols:
        thresh = DROPOUT_FRAC * max(vals)
        ax1.hlines(thresh, cx - 0.42, cx + 0.42, color=C.C_GREY,
                   linestyle=(0, (4, 3)), lw=1.5, zorder=2)
        for x, v in zip(_strip_x(cx, len(vals)), vals):
            clean = v >= thresh
            n_drop_win += 0 if clean else 1
            ax1.plot(x, v, "o", ms=11, zorder=4,
                     color=C.C_BLUE if clean else C.C_RED,
                     mec="white", mew=1.4)

    # THE DEFINITION. This is the load-bearing word for P19 and P20 and it is
    # stated here, on the line it refers to, not in a footnote.
    ax1.annotate("this line is  0.95 × that arm's own max\n"
                 "a repeat below it is called a DROPOUT",
                 xy=(1.42, DROPOUT_FRAC * max(def_v)), xytext=(1.50, 8200),
                 fontsize=12, color="#222222", ha="center", va="center",
                 linespacing=1.4, fontweight="bold", zorder=6,
                 bbox=dict(boxstyle="round,pad=0.38", fc="white",
                           ec=C.C_GREY, lw=1.3, alpha=0.97),
                 arrowprops=dict(arrowstyle="->", color=C.C_GREY, lw=1.4))

    # the two modes and the size of the gap
    lo, hi = min(def_v), max(def_v)
    ax1.annotate("", xy=(0.52, hi), xytext=(0.52, lo),
                 arrowprops=dict(arrowstyle="<->", color=C.C_RED, lw=1.8))
    ax1.text(0.47, (lo + hi) / 2,
             f"arm {ARM}: {def_spread:.2f}×\n"
             f"arm {def_other[0]['arm']}: {other_spread:.2f}×\nspread",
             ha="right", va="center", fontsize=12.5, fontweight="bold",
             color=C.C_RED, linespacing=1.35)
    ax1.annotate(f"{lo:,.0f}", xy=(1.0, lo), xytext=(1.34, lo + 950),
                 fontsize=12, color=C.C_RED, ha="left",
                 arrowprops=dict(arrowstyle="-", color=C.C_RED, lw=1.1))

    ax1.set_xlim(-0.62, 2.15)
    ax1.set_ylim(0, 16400)
    ax1.set_yticks([0, 2000, 4000, 6000, 8000, 10000, 12000, 14000])
    ax1.set_xticks([c[0] for c in cols])
    ax1.set_xticklabels([c[2] for c in cols], fontsize=13)
    ax1.set_ylabel("GFLOP/s per repeat")
    ax1.text(0.5, 0.995,
             f"seed {DEFECT_SEED} · medium · one card, one process, "
             f"{def_span:.0f} s\n"
             f"same kernel every repeat — the spread is the instrument, "
             f"not the kernel\n"
             f"{n_drop_win} of 14 repeats are dropouts in this one window",
             transform=ax1.transAxes, ha="center", va="top", fontsize=11,
             color=C.C_GREY, linespacing=1.4)
    ax1.plot([], [], "o", ms=10, color=C.C_BLUE, mec="white", label="clean")
    ax1.plot([], [], "o", ms=10, color=C.C_RED, mec="white", label="dropout")
    ax1.legend(loc="lower right", frameon=False, fontsize=12,
               handletextpad=0.3, borderpad=0.2)

    # =============== panel 2 -- the root cause ==============================
    _stage(ax2, "2", "ROOT CAUSE", "Warm-up is a count, not a time")

    xs = [s[1] for s in sweep]
    ys = [s[2] for s in sweep]
    ax2.plot(xs, ys, "-", color=C.C_ORANGE, lw=2.4, zorder=3)
    ax2.plot(xs, ys, "o", ms=10.5, color=C.C_ORANGE, mec="white", mew=1.4,
             zorder=4)
    for _nw, ms, pct, _n, _nb in sweep:
        ax2.annotate(f"{pct:g}%", xy=(ms, pct), xytext=(0, 10),
                     textcoords="offset points", ha="center", va="bottom",
                     fontsize=12.5, fontweight="bold", color=C.C_ORANGE)

    # the pre-registered count, and what that same count buys on another shape
    med_ms = PREREG_ENQUEUES * MEDIUM_KERNEL_US / 1000.0
    lrg_ms = PREREG_ENQUEUES * LARGE_KERNEL_MS
    for x, lab, col, ha, mul in (
            (med_ms, f"medium\n{med_ms:.1f} ms", C.C_RED, "left", 1.14),
            (lrg_ms, f"large\n≈ {lrg_ms:.0f} ms", C.C_GREEN, "right", 0.88)):
        ax2.axvline(x, color=col, lw=1.7, linestyle=(0, (5, 3)), zorder=2)
        ax2.text(x * mul, 68, lab, fontsize=12, color=col, ha=ha,
                 va="top", fontweight="bold", linespacing=1.25)
    ax2.text(0.595, 0.73,
             f"identical {PREREG_ENQUEUES}-enqueue warm-up —\n"
             "three orders of magnitude\napart in time",
             transform=ax2.transAxes, ha="center", va="center", fontsize=11.5,
             color=C.C_GREY, linespacing=1.4)

    knee = [s for s in sweep if s[2] == 0.0][0]
    ax2.annotate(f"knee — {knee[1]:.0f} ms\n({knee[0]:,} enqueues)",
                 xy=(knee[1], 0), xytext=(knee[1] * 0.42, 27),
                 fontsize=12, color=C.C_GREY, ha="center", linespacing=1.3,
                 arrowprops=dict(arrowstyle="->", color=C.C_GREY, lw=1.3))
    tail = sweep[-1]
    ax2.annotate("not monotone\nabove the knee",
                 xy=(tail[1], tail[2]), xytext=(tail[1] * 0.98, 18),
                 fontsize=11.5, color=C.C_GREY, ha="center", linespacing=1.3,
                 arrowprops=dict(arrowstyle="->", color=C.C_GREY, lw=1.1))

    ax2.set_xscale("log")
    ax2.set_xlim(2.2, 1000)
    ax2.set_ylim(-14, 72)
    ax2.set_yticks([0, 10, 20, 30, 40, 50])
    ax2.set_xticks([3.2, 6.4, 13, 26, 51, 103, 205, 600])
    ax2.set_xticklabels(["3.2", "6.4", "13", "26", "51", "103", "205", "600"],
                        fontsize=12)
    ax2.minorticks_off()
    ax2.set_xlabel("warm-up wall time (ms, log)")
    ax2.set_ylabel("dropout rate  (%)")
    ax2.text(0.0, 0.012,
             f"dropout = repeat < {DROPOUT_FRAC:g} × arm max\n"
             f"n = {sweep[0][3]} fresh processes per point, idle-gated\n"
             "tiny: dispatch-bound, invariant to warm-up length",
             transform=ax2.transAxes, ha="left", va="bottom", fontsize=11,
             color=C.C_GREY, linespacing=1.35)

    C.provenance(fig, "champion_interleaved_raw.jsonl (stage3_baseline) · "
                      "medium_mechanism_probe_summary.json")
    # explicit margins rather than tight_layout: the panel headers sit outside
    # the axes and tight_layout re-flows them on top of each other.
    fig.subplots_adjust(left=0.062, right=0.986, top=0.828, bottom=0.132,
                        wspace=0.225)
    C.save(fig, "p19_defect_storyboard", tight=False)


if __name__ == "__main__":
    main()
