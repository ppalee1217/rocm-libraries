# Authority gates and `/data1/perlee` workspace recovery

## Contents

- [General human-review boundary](#general-human-review-boundary)
- [`/data1/perlee` current-run artifact recovery](#data1perlee-current-run-artifact-recovery-standing-authority)

## General human-review boundary

Use risk-tiered, contract-first governance:

- Freeze R0-R3 risk before labels; after labels permit escalation only.
- Use bounded dual-agent `design-discussion` only for material protocol, claim,
  measurement-lineage, or authority ambiguity. It has at most two
  cross-examination rounds, one evidence-backed final round, and 60 total agent
  wall-minutes.
- Continue without repeated human approval when agreement preserves the frozen
  contract and uses existing authority. At a cap or material dissent, preserve
  both positions and escalate; never force `AGREE`.
- Do not use a planner, auditor, verifier, or consensus to invent authority.

Keep these gates unchanged:

- An isolated terminal commit is allowed only when existing scoped authority
  covers the exact closure unit and delivery whitelist. Compatible adjacent
  scientific gates may share one terminal closeout. Push, PR, credentials,
  external-system writes, dependency installation, and container mutation
  remain separately gated.
- Require human review for destructive non-run-artifact operations, overlap
  with unrelated user changes, forbidden host/container use, ambiguous
  source/spec/target/scope/user preference.
- Notify the user before starting a long-running command or experiment, then
  proceed within the frozen resource contract. Runtime duration alone must not
  permit optional stopping. However, a projection over 2x the original,
  wall-time/storage/throughput budget exceed, or the default 5 GiB transient
  storage cap is a hard pause gate: stop at a safe boundary and send a decision
  packet. Reforecast after the first 1% of planned throughput; pre-empirical
  engineering may consume at most 20% of the stage cap.
- For the same scientific gate/lineage, consumed wall-time, CPU/GPU time,
  storage, throughput samples, and pre-empirical engineering budget accumulate
  across generations, successors, replacement roles, process restarts, and new
  run roots. None may reset without explicit human-approved new
  authority/contract, which must record prior consumption, carry-over, and the
  approved reset boundary.
- Treat resource telemetry as operational safety/planning evidence, not as a
  scientific outcome criterion unless the approved design explicitly measures
  resource use. A resource-accounting gap is a hard blocker only when direct
  evidence shows or materially indicates a cap exceed, unsafe continuation,
  label-dependent stopping/selection, incomplete required work, or compromised
  scientific evidence. If the fixed workload and evidence chain are complete,
  the result independently reproduces, stopping was label-blind, and no direct
  cap exceed is evidenced, record missing fine-grained or parent-process
  telemetry as a non-blocking caveat and repair it prospectively. Do not rerun
  outcome-bearing work only to perfect accounting. This classification cannot
  create or alter a scientific edge.
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
