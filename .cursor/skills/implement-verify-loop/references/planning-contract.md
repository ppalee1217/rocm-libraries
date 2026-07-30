# Main-authored Plan-A / Plan-B contract

## Contents

- [Ownership and order](#ownership-and-order)
- [Plan-B: frozen goal/oracle plan](#plan-b-frozen-goaloracle-plan)
- [Plan-A: implementation and experiment plan](#plan-a-implementation-and-experiment-plan)
- [Bounded spike contract](#bounded-spike-contract)
- [Revision and visibility rules](#revision-and-visibility-rules)

## Ownership and order

Main agent owns both plans for every active scientific gate. It must not delegate either
plan to a planner subagent, and it must not implement the source change itself.

Use this order:

1. Resolve the authoritative bundle, risk tier, gate/edge, whitelists, evidence boundary,
   durable frozen contract, lock identity, and scoped authority.
2. Seal the durable contract and lock through the mechanism approved by the design.
3. Main agent writes `plan_b.md` from only the authoritative bundle and sealed contract.
4. Check Plan-B parity. R0/R1 use a Main-agent check; R2/R3 also require the existing
   fresh adversarial oracle/authority auditor. The auditor reviews but never authors.
5. Record the Plan-B SHA-256 and `FROZEN` state before writing Plan-A.
6. Main agent performs the read-only code, test, configuration, environment, and artifact
   inspection needed to remove discoverable uncertainty.
7. Main agent writes `plan_a.md`, checks it against the frozen contract and Plan-B, and
   records its initial revision hash.
8. Start the fresh implementer only after both plan gates pass.

Both plans are transient execution artifacts. Neither can create authority, amend the
durable frozen contract, replace its machine-readable criteria, or weaken a hard edge.

## Plan-B: frozen goal/oracle plan

Plan-B is a concise verifier-facing view of the approved goal. It must be independently
usable with the frozen contract and must not disclose Plan-A's implementation choices.

Include:

- Gate ID, risk tier, authoritative design identity, frozen-contract path/hash, and lock
  identity.
- Overall verification objective and the required observable end state.
- Acceptance-criterion IDs and a concise statement of the direct evidence each criterion
  requires.
- The headline acceptance check that the verifier must reproduce independently.
- Required workload completeness and the evidence, measurement, and claim boundaries.
- Compatibility, regression, reproducibility, and required edge-case goals.
- Allowed positive, negative, inconclusive, and blocked outcomes, plus the corresponding
  verified next edges.
- Explicit unacceptable fallbacks.

At minimum, unacceptable fallbacks must reject:

- Presenting partial, timed-out, killed, still-running, or incomplete work as complete.
- Trusting an implementer report or implementer-produced headline artifact without fresh
  verifier reproduction.
- Changing a test, threshold, fixture, workload, metric, goal, or claim to make a result
  pass.
- Replacing the approved baseline or evidence source with a proxy.
- Applying an unapproved downgrade, including fewer runs, seeds, repetitions, workloads,
  metrics, validation, or narrower scope.
- Comparing metrics that do not measure the same quantity and boundary.
- Declaring a winner from one dataset, a narrow workload, one secondary metric, or evidence
  without a plausible and verified mechanism.
- Accepting a headline number produced through a false or unverified premise.
- Treating downstream speculative implementation or evidence outside the active gate as
  success.

Do not include:

- Per-file edits, symbols to modify, implementation sequence, reuse choices, or patch
  structure.
- Plan-A hypotheses about code mechanics or its bounded-spike branch selection.
- Instructions that would cause the verifier to judge compliance with implementation steps
  rather than the goal.

If Plan-B conflicts with the frozen contract, stop and repair parity before implementation.
The frozen contract remains authoritative; conflict is never resolved by silently treating
Plan-B as an amendment.

## Plan-A: implementation and experiment plan

Plan-A is the implementer-facing, decision-complete execution plan. Main agent must first
resolve every fact that can be established by read-only inspection. It must not leave
discoverable details for the implementer to guess.

For every field below, provide the exact value or write `N/A` with a reason.

### Identity, scope, and code changes

- Gate ID, tranche/closure mapping, risk tier, plan revision, frozen-contract/lock hashes,
  verified upstream edges, and prohibited downstream edges.
- Exact implementation whitelist, execution artifact whitelist, delivery whitelist, and
  protected user changes.
- Files to create or modify.
- For every file: symbols, anchors, current behavior, intended behavior, exact edit
  direction, interfaces, data flow, and existing utilities or patterns to reuse.
- Compatibility boundary, error handling, invariants, failure semantics, and explicitly
  out-of-scope behavior.

### Experiment design and execution

- Approved hypothesis and expected direction, without inventing a new scientific claim.
- Independent variables, dependent variables, controls, constants, known confounders, and
  how each confounder is held fixed or measured.
- Exact fixtures, datasets, manifests, source revisions, baseline identities, and input
  hashes or deterministic resolution rules.
- Complete workload matrix, including shapes/configurations/arms/populations and the reason
  each is included.
- Seeds, warmups, repetitions, execution order, randomization or balancing rule, sample
  caps, and completeness criteria.
- Required hardware, Docker container, ROCm/toolchain versions, environment variables, build
  products, and preconditions.
- Exact setup, build, run, collection, and post-processing commands with working directory.
- Metrics, units, clock/domain, measurement boundary, aggregation, ranking or fidelity
  metric, comparability checks, and acceptance linkage.
- Raw, intermediate, and final artifact paths; expected formats/schemas; file-count or run-ID
  completeness checks; hashes; raw-to-summary cross-checks; and confirmation that every
  write target is inside the execution artifact whitelist.
- Expected observable results that establish command or pipeline correctness without
  revealing or fabricating an empirical outcome.
- Failure handling, retry/rerun rules, stop conditions, safe pause points, and the boundary
  between recoverable execution failure and a design/authority decision.
- Pre-empirical engineering share, wall/CPU/GPU time, storage, throughput assumptions,
  first-1% reforecast, notification thresholds, and any explicit hard resource boundary.

### Verification and handoff

- Exact implementer self-check commands, expected exit codes, key observable output, and
  artifact paths.
- Checks that only the verifier can perform independently and evidence that the Main agent
  or user must supply.
- `impl_report.md` requirements: changed files, selected bounded-spike branch, commands,
  cwd, exits, artifacts, completeness, deviations, plan gaps, and unresolved items.
- A statement that the implementer cannot edit either plan, the frozen contract/lock,
  approved design, report target, or paths outside the implementation and execution artifact
  whitelists.

Do not invent a path, symbol, command, line number, fixture, workload, seed, repetition, or
metric. If the approved design does not contain a material experiment choice and inspection
cannot resolve it, stop at the applicable design/user authority gate instead of encoding a
guess in Plan-A.

## Bounded spike contract

A bounded spike is allowed only when Plan-A defines all of the following:

- One concrete question the spike must answer.
- The hypotheses or candidate branches that are permitted.
- Exact investigation paths and allowed read/build/test commands.
- A deterministic decision table that maps direct observations to one permitted branch.
- The changes each branch may make within the implementation whitelist.
- Evidence and reasoning that must be recorded in `impl_report.md`.
- Stop/escalation triggers, including an observation outside the candidate set, ambiguous
  evidence, an unavailable required command, or any impact on behavior, measurement,
  evidence, claim, contract, lock, whitelist, or authority not already frozen.

The implementer may choose only a branch compelled by that decision table. Otherwise it
must make no speculative change and return `BLOCKED_PLAN_GAP` with the observed evidence.

`BLOCKED_PLAN_GAP` is not a verifier verdict and never consumes a verifier repair round by
itself. A later verifier finding consumes a round only after a complete implement→verify
cycle. Two consecutive Plan-A gap/resume cycles without material progress trigger the
existing non-design operational adjudication before another resume. All completed cycles
remain append-only provenance, but their accumulated count never blocks a reviewer-supported,
contract-preserving repair and never resets any thread/resource budget.

## Revision and visibility rules

- Main agent is the only Plan-A/Plan-B author.
- Plan-B is frozen before Plan-A is written. Change it only through the existing
  contract/design amendment and R3 authority path; never overwrite historical frozen bytes.
- Main agent may revise Plan-A within the unchanged frozen contract. Record revision number,
  previous/new hash, trigger, changed instructions, direct evidence, and why the revision is
  not label-dependent selection or a contract change.
- A bounded-spike selection already authorized by Plan-A does not require a Plan-A rewrite.
- Findings that require different implementation instructions must be reflected in a new
  Main-authored Plan-A revision before resuming the implementer.
- Implementer receives Plan-A, necessary frozen constraints, baseline, and artifact paths.
  It must not read or receive Plan-B.
- Verifier receives the frozen contract/lock, frozen Plan-B, baseline, actual diff, source,
  tests, artifacts, and `impl_report.md` as an untrusted claim. It must not read or receive
  Plan-A.
- The adversarial auditor may read the contract and both plans only to check parity,
  authority, lineage, label boundaries, and unacceptable fallback coverage. It cannot author
  or select implementation.
- Formal reports may cite both plan identities for provenance, but acceptance and claims
  remain governed by the durable frozen contract and direct evidence.
