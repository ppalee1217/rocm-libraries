# Authority gates and `/data1/perlee` workspace recovery

## Contents

- [General human-review boundary](#general-human-review-boundary)
- [`/data1/perlee` current-run artifact recovery](#data1perlee-current-run-artifact-recovery-standing-authority)

## General human-review boundary

Use risk-tiered, contract-first governance:

- Freeze R0-R3 risk before labels; after labels permit escalation only.
- Use bounded dual-agent `design-discussion` only for material experiment
  protocol, claim, measurement-lineage, stopping-rule, or scientific-authority
  ambiguity. It has at most two
  cross-examination rounds, one evidence-backed final round, and 60 total agent
  wall-minutes.
- Always submit the resulting unified recommendation or preserved dissent to
  the user before changing or resuming the affected experiment-design path;
  reviewer agreement is not design authority.
- For a consequential non-design blocker, multiple contract-preserving repair
  choices, or two repair rounds without material progress, use two independent
  operational reviewers with the same bounded cross-examination procedure.
  Prefer fresh threads when headroom exists; otherwise resume two independent
  non-implementer roles and disclose their lineage. Their agreed
  non-destructive, contract/authority-preserving action
  is pre-authorized and may proceed without another user round-trip. At
  operational dissent, the Main agent may proceed only with the minimum action
  uniquely compelled by the frozen contract and direct evidence; otherwise
  route the issue to its experiment-design, missing-authority, or safety gate.
- Do not use a planner, auditor, verifier, or consensus to invent authority.
- Every R0-R3 gate has a six-round repair cap. Two rounds without material
  progress trigger operational adjudication instead of immediate termination;
  a seventh repair still requires new human authority. Do not terminalize an
  achievable goal merely for ordinary `CHANGES_REQUIRED`, a recoverable test or
  process failure, or nonmaterial resource accounting variance.

Keep these gates unchanged:

- An isolated terminal commit is allowed only when existing scoped authority
  covers the exact closure unit and delivery whitelist. Compatible adjacent
  scientific gates may share one terminal closeout. Push, PR, credentials,
  external-system writes, dependency installation, and container mutation
  remain separately gated.
- Require human review for destructive non-run-artifact operations, overlap
  with unrelated user changes, forbidden host/container use, ambiguous
  source/spec/target/scope/user preference.
- Notify the user before starting long-running work and when first-1%,
  pre-empirical-share, 2x, wall/CPU/GPU/storage/throughput, or default 5 GiB
  planning targets are crossed. Notification is not an approval gate; record
  the variance and continue the complete frozen workload.
- Preserve known cumulative resource usage and its parent/child/inclusive
  measurement boundary across generations, successors, replacement roles,
  restarts, and new run roots as best-effort provenance. Never erase, invent,
  or silently treat `UNKNOWN` as zero. Historical consumption, missing
  telemetry, a 2x projection, or an internal planning-cap crossing does not by
  itself pause work or debit successor-entry authority.
- Pause at a safe boundary only when direct or materially indicative
  operational evidence ties continuation to unsafe operation; an
  external/platform/allocation limit; unavailable compute, memory, or storage;
  inability to complete the full frozen workload, verification, closure, or
  artifact preservation; label-dependent stopping/selection; a required
  workload or claim change; compromised evidence; or an exact resource
  quantity/boundary frozen pre-label as a scientific/comparability criterion.
  Bare `UNKNOWN`, planning variance, internal cap crossing, or cumulative total
  is not such evidence. Do not rerun outcome-bearing work only to perfect
  accounting. Scientific sample/execution caps, repair/thread caps, downgrade
  gates, and evidence requirements remain hard and this rule cannot create or
  alter a scientific edge.
- Apply the experiment's separate user gate for every downgrade.
- Any destructive or post-label contract/lock/protocol/fixture/threshold/
  selection/lineage/claim change is R3 and requires its authority gate.

## `/data1/perlee` current-run artifact recovery standing authority

Treat the repository owner's 2026-07-25 instruction as standing authority:
automatically recover a qualifying whitelist-outside disposable artifact by
exact quarantine plus post-audit. This deterministic path does not require
dual reviewers or repeated human approval. Classification must be proved from
the incident manifest; uncertainty is not qualification.

### Qualify every exact target

Require all of the following:

- The target is a new untracked and unstaged regular file created by the
  current active workflow in its active repo/worktree or a predeclared,
  snapshotted run/scratch root.
- Both lexical and resolved absolute paths are strictly below
  `/data1/perlee/`; the target belongs to the active workflow area, not merely
  the same owner prefix.
- Baseline or targeted pre-command evidence proves that the target was absent.
- Direct convergent evidence attributes creation to the current role. Accept
  an exact creator command, or an equally direct bundle such as role
  admission/interval plus an artifact fingerprint bound to current-run source
  bytes and matching path/type/hash/time evidence. Never rely on extension,
  owner, or timestamp alone.
- `lstat`, link count, Git/index/ignore state, size, hash, and timestamps prove
  one exact ordinary file with no symlink, special-file, or hard-link
  ambiguity.
- The artifact is byte-regenerable, non-sensitive, and has no user,
  authority, source, test, config, design, input, raw/derived evidence, lock,
  report, delivery, or other independent value.
- Recovery only restores baseline absence. It does not change the goal,
  Plan-B, acceptance, evidence/measurement boundary, report, DAG/gate, claim,
  implementation/delivery whitelist, commit authority, or another authority
  gate.

Exclude tracked, staged/index, committed, pre-existing untracked/ignored,
attribution-ambiguous, concurrently/user-modified, other-workspace/repository/
mount, sensitive, evidence-bearing, plan-listed, or independently valuable
targets. Send every excluded or insufficiently proved case to human review or
bounded dual review when classification—not destructive authority—is the only
material ambiguity.

### Preserve one incident manifest

Stop the active role and checkpoint progression before recovery. Record:

- exact absolute, repo-relative, and resolved paths plus active-area identity;
- `lstat` type/mode/link count, size, SHA-256, and birth/mtime/ctime;
- Git tracked/index/ignore/status evidence and baseline absence evidence;
- creator role/command or equivalent convergent attribution;
- artifact semantics, sensitivity, and evidence/delivery value;
- the exact proposed operation, its nonrecursive property, and expected
  postconditions.

The orchestrator must deterministically prove qualification, attribution,
absence of user/concurrent overlap, absence of sensitive/evidence/delivery
value, invariant preservation, exact operation, and postconditions. Missing
proof or identity drift returns to the human/dual-review gate; it never falls
through to automatic recovery.

### Execute only the agreed exact recovery

- Immediately recheck path resolution, type, link count, hash, Git/index
  state, and directory children. Stop on drift.
- Move the exact file to a new incident-specific path in the current ignored
  `agent_run/...` quarantine and verify source absence plus identical
  destination hash. Automatic recovery never unlinks bytes or removes a
  directory; those operations require separate authority.
- Forbid globs, recursive deletion, broad or unresolved variables, parent
  cleanup, `git clean`, `git reset`, `git checkout`, `git stash`, broad
  restore, and every unlisted side effect.
- Re-run full status/diff/index, whitelist, target-absence or quarantine-hash,
  and unrelated-change audits. Resume the original role only after all
  postconditions pass.
- Record the trigger, qualification evidence, exact commands/exits/results,
  quarantine identity, post-audit, and standing-authority basis in
  `adjudication.md`; add it to `impl_report.md` when relevant and materialize
  it in the formal report at closeout.

This standing authority restores the workspace only. Never stage, commit,
deliver, or use quarantined bytes as scientific evidence.
