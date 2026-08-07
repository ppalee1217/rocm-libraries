# HANDOFF — S14 Ductile BASELINE (Arm G) preflight + pilot on a remote gfx942 server

> **Doc role:** operational cross-server coordination guide (explanation/instruction only). NOT an authority/contract/lock/report. Tracked in git so it can be transferred with the repo. Authority remains: charter → experiment plan → S14 design → future S14 effective lock.

**Audience:** an autonomous agent on ANOTHER server that has gfx942 GPUs + ROCm.
**Origin study:** Formocast-factorized Gen0 guidance study (checkpoint S14).
**How to sync the code:** pull branch `users/perlee/s11-integration` at the commit that contains THIS file (its tip at handoff time — the origin session will give you the exact hash). The runnable Ductile engine + frozen config already exist at baseline commit `d939bdaa97c9cbcb39ea644cd6b9ba63d1d2798c`; the S14 design + this handoff are added on top of it.
**Status of this task:** label-blind **preflight + baseline pilot**. Read §1 before doing anything.

---

## 1. Purpose & scope (READ FIRST — this is NOT sealed evidence)

You are running the **BASELINE arm (Arm G = existing GEKO guidance)** of the Ductile genetic-algorithm (GA) kernel tuner on gfx942, plus supporting preflight. The S14 experiment's effective lock is **NOT sealed yet** (it waits on an upstream checkpoint closeout + final parameter decisions on the origin side). Therefore:

- This run is a **label-blind preflight + Arm-G pilot**. Its job is to deliver, back to the origin session:
  1. **Pipeline validation** — prove GA → build kernels → real-GPU benchmark works end-to-end on your server.
  2. **Real wall-time** — how long a real Ductile run actually takes on your hardware (per-candidate and projected full-run).
  3. **Noise pilot data** — to compute `delta_noise` and per-size references `R_s`.
  4. **Cross-server reproducibility pins** — captured toolchain/GPU/OS/library versions + hashes.
  5. **Baseline (Arm G) trajectory + champion** on the frozen problem set.
- It is **NOT** the sealed S14 baseline. The sealed baseline is re-run later under the effective lock on the origin side. Do **not** treat these numbers as final scientific evidence, and do **not** seal/commit anything into the study protocol.
- Run **Arm G only** (existing GEKO guidance). Do **NOT** add Formocast/guided weights (Arm F) or any shuffle (Arm S) in this pass — this pass is label-blind baseline + timing.

### Pins (user-authorized 2026-08-07; single-server — all runs on this box)
- **P0 (initial population)** = **cap 512** (user-authorized 2026-08-07, updated from 64; see §4; force it to exactly 512 via the isolated engine edit and fail-closed verify actual P0=512).
- **formal seeds** = **5** (`14001`–`14005`; 4-of-5 joint). **Native Ductile early-stop KEPT** (do NOT set period=0); n_gen=30 is the MAX cap. Primary metric = final champion real-GFLOPS (+ median non-inferiority); search-trajectory AUC = secondary diagnostic on the common completed budget; **NO hard U_floor gate** (FT-EVALUATION-SUPPORT only if an arm cannot finish Gen0 / produce a champion).
- **arms** = **G only** for this baseline pass (Arm S is irrelevant here).
- **5-seed parallel**: run the 5 seeds on 5 distinct idle non-0 GPUs (record each UUID). (5 clean cards available: idx 2,3,4,5,7; re-check live.)

---

## 2. Reference documents (read these from the synced repo)

- `study_docs/research/ductile-origami-warmstart/s14-stage1-full-ga-outcome-design.md` — the S14 design. Read especially **§6 / §6.1** (frozen pins + `pi_nominal` composition), **§5.2** (cross-server reproducibility pins), **§5.3** (GPU selection policy). This handoff implements those.
- `study_docs/research/ductile-origami-warmstart-experiment-plan.md` — **§7** (arms U/G/F/S, GA configuration, proposal machinery) and the **`RESCOPE-STAGE1-OUTCOME-20260807`** amendment (search for that token).
- `study_docs/research/ductile-origami-warmstart/protocol/v1/inputs/s10-generated.yaml` — the **frozen input config** you will run (GEMM, 3 problem sizes, `ForkParameters` + `Groups`/`group_0` GEKO weights).
- `study_docs/research/surrogate-dse-plan.md` — charter; **§8.6** lists forbidden claims (no convergence/speedup/persistence wording). Keep reporting factual/numeric only.
- Ductile engine: `projects/hipblaslt/tensilelite/Tensile/ductile/config/defaults.yaml` (GA knob defaults), `.../ductile/algorithm/ga.py` (GA loop, seed, pop handling), `.../ductile/core/space.py` (sampling; `os.cpu_count()` sensitivity), `.../Tensile.py` (CLI/argparse), `.../BenchmarkProblems.py` (benchmark phase).

**Important:** the exact CLI flags and GA-knob override mechanism below are our best reading of the source. **You must re-verify them against `Tensile.py` argparse and `defaults.yaml` on the synced commit before relying on them.** Do not trust a flag the source does not show.

---

## 3. Environment bring-up (Stage 0)

1. Sync the repo (see header: branch tip containing this handoff; engine baseline `d939bdaa97…`).
2. Prereqs: ROCm (with `amdclang++`), CMake, Python 3 with tensilelite deps; gfx942 GPUs.
3. Build the client (NOT prebuilt in-tree):
   ```bash
   cd projects/hipblaslt/tensilelite
   invoke rocisa
   invoke build-client --gpu-targets gfx942
   ls -lh build_tmp/tensilelite/client/tensilelite-client   # expect an executable
   ```
   (Confirm the exact `invoke` task names via `invoke --list` / `tasks.py` if they differ.)
4. Pick the GPU: run `rocm-smi` (or `rocm-smi --showuse --showmeminfo vram`), choose a GPU that is **idle (0% use, ~0 VRAM, no other processes)** and **NOT index 0**. Record its **UUID**.
   ```bash
   export HIP_VISIBLE_DEVICES=<chosen_nonzero_idle_index>
   ```
5. Capture **all** environment pins into `env/pins.json` (see §7): ROCm/HIP version, `amdclang++ --version`, hipBLASLt/tensilelite commit, rocisa build id, `tensilelite-client` sha256, CMake version, OS/kernel, Python/NumPy/joblib versions, GPU model/arch(gfx942)/driver/firmware/PCI-BDF/UUID, chosen device index.

---

## 4. Experiment spec / pins (from S14 §6.1)

- **Arm G (baseline):** run the frozen config as-is = existing GEKO guidance = full `pi_nominal`. `group_0` (MatrixInstruction/WorkGroup group, 9,918 candidates) keeps its GEKO weights; the 29 ungrouped free genes stay uniform. **Do not inject any Formocast weights.**
- **Config file:** `study_docs/research/ductile-origami-warmstart/protocol/v1/inputs/s10-generated.yaml`.
- **P0 (initial population): cap = 512** (user-authorized 2026-08-07, was 64). The constructor normally inflates the initial population to ~11,405 for this space; force it to exactly 512. Determine from `ductile/algorithm/ga.py` + `Tensile.py`/`defaults.yaml` whether this is settable via config or needs a small code change. **If P0=64 cannot be forced without a code change, STOP before Stage 3 and report** (tied to a pending origin-side decision; do not silently run at 11,405).
- **n_gen = 30** (MAX cap). **Keep Ductile's native early-stop** (native period/tol/div_thr; may terminate before 30 gens) — do NOT set period=0 (2026-08-07 user-authorized: fidelity to unmodified Ductile).
- **problem sizes = the 3 in the frozen config:** `(M,N,batch,K) = (8,8,1,128)`, `(256,256,1,1024)`, `(2304,1024,1,214336)`, gfx942 non-StreamK, single dtype/layout as in the YAML. Do not add/remove sizes.
- **correctness:** set `NumElementsToValidate = 128` (frozen YAML currently has 0 → change to 128 for every formal candidate evaluation and every champion remeasurement). Record any correctness failure verbatim.
- **benchmark measurement:** keep `NumWarmups = 321`, `EnqueuesPerSync = 321`.
- **`n_jobs = 1`** for the Ductile sampler (see `space.py` `os.cpu_count()` scaling) for cross-server reproducibility.
- **seeds:** 5 formal GA seeds (`14001, 14002, 14003, 14004, 14005`), 4-of-5 joint decision rule.
- **quality metric** (for trajectory/champion reporting): `Q(x) = max_s [ GFLOPS_s(x) / R_s ]`, `R_s` from Stage-2 noise pilot. Report raw per-size GFLOPS too.
- **GPU:** pinned idle non-0 device via `HIP_VISIBLE_DEVICES`; record UUID.

---

## 5. Staged run plan (report back after EACH stage)

- **Stage 0 — env/build/GPU/pins.** Deliver `env/pins.json`. Confirm `tensilelite-client` runs.
- **Stage 1 — pipeline smoke + throughput microbench.** Run a *tiny* GA config (very small pop, 1–2 generations) end-to-end to prove GA→build→GPU→CSV works, and measure **seconds per candidate** (compile + 3-size benchmark). Deliver `stage1_throughput.json` with per-candidate seconds and a **projected full-run wall-time** for the Stage-3 spec. ← the timing estimate the origin session needs.
- **Stage 2 — noise pilot.** Pick 3 fixed anchor configs; measure each on the 3 sizes, 7 repeats (3×3×7). Compute per-size `R_s` and `delta_noise = exp(P95(|log Q − median_r log Q|)) − 1`. Deliver `stage2_noise/`.
- **Stage 3 — baseline Arm-G pilot.** For each of the 5 formal seeds (parallel, 5 distinct idle non-0 GPUs): run the full GA (P0-cap=512, n_gen=30 max with native early-stop, 3 sizes). Record **per-generation best-so-far** trajectory (for AUC) and the final **champion**. Then **independently remeasure** the champion 7×/size. Deliver `stage3_baseline/seed_<s>/…`.

If any stage fails or a pin cannot be honored, STOP and report verbatim — do not improvise a substitute.

---

## 6. Governance / constraints (do NOT violate)

- Do **NOT** seal or commit anything into the study protocol, and do **NOT** push. Your outputs are pilot/timing artifacts handed back, not sealed evidence.
- **Label-blind:** Arm G only. No Formocast/guided weights, no shuffle. No peeking at guided results to tune anything.
- Do **NOT** reuse these baseline outcomes to change any future sealed pin (they inform timing/noise/pins capture only).
- GPU: **never device index 0**; use an idle GPU; pin via `HIP_VISIBLE_DEVICES`; record UUID.
- Keep everything **append-only**; never overwrite prior artifacts. Report failures with exact error text, exit codes, command.
- Force P0 to exactly 512 via the isolated engine edit; do not run at the constructor-inflated ~11,405 as if it were the intended baseline.

---

## 7. Handoff-back format (so the origin session can ingest directly)

Produce a single return directory `s14-baseline-return-<server>-<YYYYMMDD>/` with this exact layout:

```
s14-baseline-return-<server>-<YYYYMMDD>/
  manifest.json            # machine-readable authoritative summary (schema: s14-baseline-return-schema.json, in this handoff dir)
  env/pins.json            # toolchain/GPU/OS/Python/NumPy/joblib versions + hashes + chosen GPU UUID
  stage1_throughput.json   # per-candidate compile+bench seconds; projected full-run wall-time
  stage2_noise/
    raw_repeats.jsonl      # one line per (anchor, size, repeat): gflops
    computed.json          # per-size R_s + delta_noise + exact formula used
  stage3_baseline/
    seed_14001/
      2_BenchmarkData/…csv         # raw Tensile benchmark CSVs
      3_LibraryLogic/gfx942_*.yaml # champion per size
      trajectory.jsonl             # per generation: {gen, cumulative_complete_evals, best_Q_so_far, per_size_best_gflops}
      champion.json                # champion config + kernel_name + independent 7x/size remeasured GFLOPS (mean, stdev, raw[7])
      run.log
    seed_14002/ …
    seed_14003/ …
    seed_14004/ …
    seed_14005/ …
  hashes.sha256            # sha256 of every file in this return dir
```

- `manifest.json` is the authoritative summary; conform to `s14-baseline-return-schema.json` (in this handoff dir). **All fields numeric/factual — no prose verdicts** (interpretation happens on the origin side).
- Deliver the return dir as a tarball (`.tar.zst`/`.tar.gz`) + its sha256. State how the origin side can fetch it (scp path / shared mount / upload location).

---

## 8. Quick command sketch (verify against source before running)

```bash
REPO=/path/to/rocm-libraries          # synced to the handoff commit
cd "$REPO/projects/hipblaslt/tensilelite"
invoke rocisa && invoke build-client --gpu-targets gfx942

export HIP_VISIBLE_DEVICES=<idle_nonzero_index>
CONFIG="$REPO/study_docs/research/ductile-origami-warmstart/protocol/v1/inputs/s10-generated.yaml"
# Apply S14 pins (P0-cap=512, n_gen=30, NumElementsToValidate=128, n_jobs=1, seed) —
# confirm the exact override path from Tensile.py/defaults.yaml first.
python3 Tensile/bin/Tensile "$CONFIG" ./s14-baseline-out --device 0   # -d indexes within HIP_VISIBLE_DEVICES
```

Outputs land under `./s14-baseline-out/` (`2_BenchmarkData/*.csv`, `3_LibraryLogic/gfx942_*.yaml`). CSV columns: `GFlops`, size columns, then one GFlops column per solution (`-1`=fail, `0`=invalid). Cross-reference the winning solution column into `3_LibraryLogic` for the champion config.

---

## 9. Contact protocol
Report back after each stage with: stage id, status, key numbers (Stage 1 → wall-time; Stage 2 → delta_noise/R_s; Stage 3 → per-seed champion GFLOPS + gens run + U_floor reached?), any pin that could not be honored, and the path/URL to the (partial) return dir. Keep prose short; put detail in the JSON artifacts.
