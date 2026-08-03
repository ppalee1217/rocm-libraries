# Experiment artifact governance

Status: repository-wide prospective governance policy

This policy applies to every new experiment, checkpoint, successor,
generation, execution tranche, and closure unit in this repository.  Read it
at the start of each execution tranche together with the repository general
rule and `implement-verify-loop`.

The purpose is milestone-level immutability: protect artifacts that determine
or support a scientific conclusion, while allowing traceable correction of
ordinary operational records.  A bookkeeping defect is not, by itself, a
scientific-identity defect.

## 1. Precedence and migration boundary

This policy is prospective and does not rewrite history.

- Existing sealed authority, contracts, locks, raw evidence, decisions,
  reports, parent projections, and outgoing edges remain immutable.
- An effective contract or approved design that explicitly freezes a stricter
  lifecycle remains controlling until a formal amendment or successor changes
  it.  This policy is not an implicit amendment.
- An unsealed checkpoint with no outcome evidence may adopt this policy only
  after a pre-evidence rebaseline proves artifact-layer classification,
  outcome absence, and human/machine authority parity.
- Retired helpers, failed generations, and superseded bindings remain
  diagnostic provenance.  They receive no scientific credit without an exact
  reuse declaration in a new effective contract.
- If migration would change an approved measurement, claim, lineage, stopping
  rule, hard lifecycle invariant, or evidence boundary, use
  `design-discussion` and obtain the user's decision before resuming that
  experiment-design path.

The more specific sealed scientific contract wins over this general default.
An implementation choice that has not been sealed does not become a permanent
scientific requirement merely because code or a draft mentions it.

## 2. Three artifact layers

Every artifact must be classified before an outcome-revealing command can
consume it.  Classification is based on what the artifact controls or proves,
not its extension, directory, or whether it contains a hash.

### A. Sealed scientific milestones

Layer A contains artifacts that determine or support a scientific conclusion:

- approved research authority, checkpoint design, and formal amendments;
- durable frozen contracts, effective locks, and seal manifests;
- source pins, formal inputs, workloads, candidate registries, seeds,
  thresholds, and stopping rules;
- formal selection, mapping, model output, and measurement rows;
- GPU environment, correctness, noise, and performance evidence;
- decisions, independent reproductions, verifier verdicts, terminal reports,
  parent projections, and outgoing edges.

Layer A becomes effective only through the declared seal mechanism, normally
an exact-path Git commit/tree identity plus content hashes and a small
deterministic seal manifest.  After sealing:

- never overwrite, delete, reorder, or replace the artifact in place;
- never use an operational correction to change its effective meaning;
- change it only through an explicit amendment, new version, or successor;
- preserve predecessor identity, reason, authority, affected scope, and the
  evidence-reuse boundary;
- give every amendment/successor its own sealed artifact inventory so lineage
  remains chainable beyond one transition;
- treat any post-label protocol, threshold, selection, measurement, lineage,
  claim, or edge change as R3 experiment-design authority;
- fail closed when the verifier cannot reproduce the formal state from the
  sealed identity.

Layer-A immutability prevents outcome-dependent manipulation, evidence
replacement, cherry-picking, and silent claim changes.  It is the hard
boundary this policy preserves.

### B. Pre-seal candidates

Layer B contains artifacts that are not yet effective:

- design and amendment drafts;
- contract, schema, fixture, and seal-manifest candidates;
- Plan-A and Plan-B;
- implementation candidates;
- audit drafts and pre-evidence tests.

Before outcome-revealing work starts, Layer B may be reviewed, revised,
replaced, or deterministically rebuilt.  Apply these rules:

- assign every review candidate a revision and content hash;
- identify the exact candidate selected for sealing;
- do not treat a partial or incomplete candidate as sealable;
- do not let a superseded candidate masquerade as authority or formal
  evidence;
- do not create a scientific successor for an ordinary candidate edit,
  serialization correction, or test-harness repair;
- move only the selected exact version into Layer A through the declared seal.

### C. Operational bookkeeping

Layer C contains records that help operate and audit a run but do not directly
determine a scientific conclusion:

- live run state and heartbeats;
- agent and role routing;
- resource telemetry and forecasts;
- command admission and summaries;
- repair history;
- non-outcome audits, planning records, and workspace observations.

Preserve enough information to reconstruct decisions and responsibility
boundaries, but do not require every field to share one giant append-only
ledger.  Layer C follows these rules:

- a published or referenced bad event keeps its original bytes and receives a
  separate correction event;
- an unpublished temporary record with no consumer may be atomically rebuilt;
- a deterministic, versioned projection rule produces effective state;
- projection consumes the sealed Layer-C target/schema boundary; a record's
  self-declared layer never grants correction eligibility;
- writer, replay, projection, and verifier use the same canonicalization;
- a correction must not alter Layer-A identity, sample inclusion, execution
  order, measurement, outcome, claim, or edge;
- a bookkeeping defect does not automatically reopen a binding.

Prefer one-event-per-file `O_EXCL` JSON/YAML, a small correction-aware database,
or another simple crash-safe representation.  Derived views are caches rebuilt
from events, never the only source of truth.  Resume formal workloads at their
declared atomic artifact, cell, or chunk boundary.

The sealed Layer-C boundary may use a compact deterministic target/template
rule for future heartbeats or command IDs; it need not pre-enumerate every
runtime event.  Replay expands that rule to exact targets and payload schemas,
then rejects any event outside the expansion.  This is a classification guard,
not a giant event inventory.

### Default representation choices

- Layer A: exact-path Git commit/tree identity, content hashes, and a small
  deterministic seal manifest.
- Layer B: normal versioned files; use atomic temporary-file-plus-rename for an
  unpublished candidate when crash safety is needed, then record the selected
  revision and content hash.
- Layer C: one-event-per-file `O_EXCL` canonical JSON/YAML or a simple database
  with the same correction and projection semantics.
- Derived views: deterministic rebuilds from source events, never the only
  source of truth.

Do not expand a single giant ledger or inode/procfd/signal/dumpability
transaction framework unless a frozen design requires it.  Governance
complexity must remain proportionate to the experiment it protects.

## 3. Operational correction events

The minimum machine-readable correction is:

```yaml
event_type: operational_correction
target:
  path: exact/original/path
  sequence_or_id: original-event-id
  raw_sha256: original-raw-hash
reason: why-the-original-record-is-wrong
corrected_payload: {}
author_or_actor: stable-role-or-process-id
recorded_at_utc: RFC3339-timestamp
projection_rule: operational-last-correction-wins-v1
scientific_impact: none
```

The target path, ID, and raw hash must uniquely identify original bytes that
still exist.  The pre-evidence seal must also bind the registry identity,
target-template classification, complete recursive JSON-pointer leaf schema,
and correctable leaf subset.  Every observed target must match exactly one
sealed template, and a correction may change only that subset.  Protected
scientific semantics such as sample inclusion, execution order, measurement,
outcome, claim, and edge must stay outside that subset.  Classification is
fixed by pre-evidence contract/registry parity and what the leaf controls or
proves, never guessed from its field name; for example, an operational display
field named `input` is not automatically a formal scientific input.
Corrections use canonical UTF-8
JSON with sorted keys, compact separators, no duplicate keys, and no non-finite
numbers.

`operational-last-correction-wins-v1` normalizes RFC3339 UTC timestamps to the
represented instant, then applies corrections for one structured `(path,
sequence_or_id)` target in ascending `(instant, correction_raw_sha256)` order.
The final complete `corrected_payload` is the effective payload.  Two different
or duplicate corrections at the same latest instant fail closed.  By this
projection rule, any later unique complete correction automatically supersedes
the whole earlier conflicting group; no free-form reason or implicit actor
intent controls that result.  This gives ordinary bookkeeping a deterministic
recovery path without changing history.
Replay fails closed on:

- a missing, ambiguous, or raw-hash-mismatched target;
- unresolved duplicate correction bytes at the latest instant;
- two different unresolved corrections for one target at the same instant;
- malformed timestamps or unknown projection rules;
- a target outside Layer C;
- `scientific_impact` other than `none`.

When scientific impact is not `none`, stop Layer-C correction and use a formal
amendment or successor.  The reference projector and tests are in
`study_docs/research/tools/experiment_artifact_governance.py` and
`study_docs/research/tests/test_experiment_artifact_governance.py`.

## 4. Successor decision

A successor or formal amendment is mandatory when any of the following
changes, is polluted, is replaced, is lost, or cannot be verified:

- effective contract, lock, source/input, seed, workload, fixture, threshold,
  stopping rule, or outcome matrix;
- formal selection, mapping, measurement, correctness/noise evidence, or
  decision;
- sample inclusion, execution order, comparability, measurement boundary,
  lineage, claim, or edge;
- a post-label relaxation that could increase the probability of the desired
  outcome;
- an identity explicitly frozen by the effective design as a scientific or
  safety boundary.

A successor never automatically inherits empirical evidence.  Its contract
must classify every predecessor artifact as reusable formal input, diagnostic
only, or forbidden to read.

Do not automatically reopen a binding when direct evidence proves science,
replay, and claim are unchanged.  Correct, replay, verify, and continue for:

- JSON/YAML key order, pretty-printing, or non-semantic whitespace;
- timestamp, display label, live status, resource estimate, or command summary;
- pre-seal schema, manifest, implementation, or test-harness repair;
- debug, heartbeat, or agent-routing omission;
- a derived index/cache rebuilt deterministically from sealed raw bytes;
- isolated unrelated workspace drift.

A real later workspace drift is a new observation, not a correction of a
historically accurate earlier observation.  Use a correction only when direct
evidence proves the earlier published observation was wrong when recorded.

## 5. Proportionate threat model

By default, experiment machinery must handle accidental edits, omissions,
substitutions, post-outcome manipulation, cherry-picking, ordinary concurrent
processes, crashes, partial writes, and resume errors.

It does not, by default, need to defend itself from a malicious process under
the same Unix account, syscall-window inode swaps, hostile file-descriptor
tables or `procfs`, adversarial `SIGCHLD`/dumpability behavior, or an actor with
repository-owner privileges.  Do not silently turn an experiment provenance
helper into an operating-system security framework.

When an approved design, external compliance rule, or direct evidence requires
that stronger threat model, declare it before evidence and use proportionate
isolation: a separate OS identity/container, read-only storage, signatures, or
an external artifact service.  Record the cost and verification method.

## 6. Migration matrix from the former default

| Existing pattern | Layer | Prospective treatment | Reason |
| --- | --- | --- | --- |
| Contract, lock, source/input pins, formal rows, decision, report, edge | A | Strictly immutable after seal; amendment/successor only | Controls evidence or claim |
| Contract/schema/fixture/Plan/implementation before seal | B | Revision plus exact hash; normal review/rebuild allowed | Not yet effective authority |
| Repair history, resource accounting, routing, command summaries, live state | C | Traceable events and deterministic corrections | Reconstructs operation, not outcome |
| General-rule wording that repair history is “append-only provenance” | C | Preserve history, but no single-ledger or immutable-byte mandate | The required property is traceability |
| External workspace observations | C | New observation/correction event; no global equality gate | Does not affect scoped evidence |
| Existing checkpoint-specific append-only formal workload or sealed ledger | A when frozen | Keep the effective contract unchanged | General policy cannot weaken a sealed design |
| Unsealed custom inode/procfd/signal/dumpability helper | B unless a design explicitly freezes it | Replaceable implementation candidate under the default threat model | Mechanism is not itself scientific evidence |

The old general wording protected useful scientific boundaries but also let
serialization, timestamp, resource, routing, and command-summary mistakes
poison an entire binding.  This matrix narrows strict immutability to the
milestones that actually prevent outcome manipulation.

## 7. Required workflow checks

At each new tranche:

1. Read this policy and record its commit/hash.
2. Classify every authority, implementation, execution, evidence, and delivery
   artifact as A, B, or C.
3. Record the exact seal transition from B to A and the Layer-C projection
   rule.
4. Confirm whether a more specific effective contract requires stricter
   behavior.
5. Freeze the scientific threat model and any explicit external compliance
   requirement before outcome evidence.
6. Test correction replay, candidate selection, seal protection, and
   successor triggers without reading outcome labels.
7. Keep experiment conclusions unchanged unless the proper design authority
   approves and seals a scientific amendment.
