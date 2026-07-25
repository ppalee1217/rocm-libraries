# S00 evidence foundation protocol v1

This directory contains the `ductile-origami-s00-v1` protocol. The original
`s00-foundation-lock.json` remains the true genesis lock with
`parent_lock: null`. Its five original evidence/decision artifacts form a
failed verification generation and are immutable raw bytes. The append-only
ledger now has exactly one amendment, `s00-successor-recovery-001`, whose head
selects `successor-001` as the only current generation. An old decision is
therefore historical even though its preserved bytes contain `["S10"]`.

Authority remains ordered from the research charter through the parent plan,
active index, S00 design, study contract, amendment, and effective successor
lock. The successor lock binds both opaque Plan-B identities, exact 29-path
implementation and 33-path delivery lists plus their canonical hashes, the
baseline, six authorities, eleven source files, six schemas, four fixtures,
four seeds, formal-report identity, ledger head/raw bytes, immutable old
generation, recovery consensus, and the exact old-lock parent.

## Successor lifecycle

Every production command is fail-closed and successor-specific. There is no
fallback that selects the old lock, old evidence, or old decision as current.
Writers validate all frozen identities before creating an outcome and use
exclusive creation. The six old artifacts are guarded before and after every
phase.

From the repository root, run the phases in this order:

```bash
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py preflight-successor --original-plan-b agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/plan_b.md --recovery-plan-b agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/plan_b.md
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py lock-successor --original-plan-b agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/plan_b.md --recovery-plan-b agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/plan_b.md
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py evidence-successor
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py decision-successor
```

Fresh verifier reproduction uses an empty, ignored transient directory:

```bash
S00_SUCCESSOR_REPRO_DIR="$(mktemp -d agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/reproduce.XXXXXX)"
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py reproduce-successor --output-dir "$S00_SUCCESSOR_REPRO_DIR"
```

The effective output names are
`s00-foundation-lock-successor-001.json`, followed by the four
`*-successor-001.json` evidence artifacts and
`s00-decision-successor-001.json`. A positive decision requires all four
current evidence classes, their exact ordered parent chain, independent raw
validation, a fresh in-process reproduction comparison, and `AC-01` through
`AC-10` all marked `PASS`. Missing, failed, partial, negative, inconclusive,
blocked, or `CHANGES_REQUIRED` input yields no ready edge.

## Direct evidence semantics

Observer neutrality stores the frozen measurement boundary and complete raw
observer-off/on GA runs: every evaluation, fitness matrix, updated/old
population, survivors, offspring, champion, population decay, statistics,
evaluation counts, final result, termination, and Python/NumPy/search-space
RNG identities. Observer-off events are explicitly an empty array;
observer-on stores the complete immutable callback event chain and callback
counts. A recursive canonical first-divergence record proves equality or
identifies the first JSON-pointer difference.

Resume parity stores complete continuous and interrupted/resumed raw runs,
both event arrays, every checkpoint manifest and external journal, exact
checkpoint parent/hash/component/lineage identities, and the resume boundary.
The boundary binds the interruption generation, selected checkpoint, saved
event head/cursor, first resumed control and outcome events, typed control
mapping, and continuous-to-resumed outcome mapping. Validators recompute
manifest and event chains, global event uniqueness/continuity, raw run hashes,
and first divergence.

Reconciliation accepts only these exact state machines:

- generated input success → backend success with exit code zero → successful
  finite observation → `{"outcome":"success"}` summary;
- generated input success → backend failure with a nonzero exit code →
  `{"outcome":"backend_failure"}` summary, with no observation.

Record IDs are globally unique across kinds. Canonical payload/record hashes,
predecessors, common lineage, exact kind order, status, and payload semantics
are all checked. `in_progress`, `timeout`, and `killed` have stable named
rejections; no malformed or contradictory row is inferred, dropped,
deduplicated, or converted into a numeric success.

## Preservation and claim boundary

Base recovery preserves the six old lock/evidence/decision raw artifacts and
the recorded old hashes of the other seventeen shared implementation paths.
It does not claim that those seventeen old raw contents are reconstructable
from the final tree.

All S00 measurements are deterministic CPU-only synthetic evidence-semantics
checks. They provide no GPU or kernel-performance result, no model-quality
claim, and no S10 discovery or implementation result.
