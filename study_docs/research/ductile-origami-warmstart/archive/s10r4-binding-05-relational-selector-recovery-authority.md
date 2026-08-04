# S10R4 Binding-05 Relational-Selector Recovery Authority

Authority ID: `S10R4-B05-CLEAN-RELATIONAL-SELECTOR-AUTHORITY-V1`

Status: user-approved clean successor authority, pending identical-prompt
Reviewer-A/Reviewer-B precommit review, exact-path authority commit and
postcommit audit.  This document creates no effective lock, formal observation,
scientific outcome, report or outgoing edge.

## 1. Trigger and amendment boundary

Binding-04 correctly separated raw declarations from resolver-effective and
codegen identities, but its prelock source-closure proof stopped one relation too
early.  `KernelWriter.getTensorParameters` first assigns a literal
`tensorIdx in {0,1}`, then separately computes
`tP["idx"] = ProblemType["Index%d" % tensorIdx]`.  Both ordinary and
wave-separated TDM consumers use that derived `idx` as `ti` in
`kernel[f"MacroTile{ti}"]`.

Therefore, proving only the literal `tensorIdx` domain does not prove the key
domain consumed by `initTDMDescriptor` or
`initTDMDescriptorWaveSeparatedImpl`.  The missing edge is the fixed-instance
relation from actual YAML and `ProblemType` defaults/overrides, through
`initGEMM` and `assignDerivedParameters`, to `Index0`/`Index1`, and only then to
the TDM key.  This is an evidence-lineage/source-closure defect discovered
before any B04 effective lock or formal row.  It is not KernelWriter attrition,
mapping failure, correctness failure or scientific evidence.

Binding-05 is a prospective clean-context repair of exactly that closure.  It
does not change the S10R4 hypothesis, raw population, 114x2 formal workload,
selection rule, mapping workload, correctness/noise thresholds, decision table,
claim or only possible outgoing edge.

## 2. Immutable binding-04 non-scientific history

At the B05 authority commit, binding-04 is immutable as:

- binding status: `superseded_prelock`;
- execution status: `cancelled`;
- checkpoint state: `BLOCKED`;
- criterion status: `CHANGES_REQUIRED`;
- scientific outcome: `not_evaluated`;
- edge: `null`;
- lock state: `absent`;
- lock never created: `true`;
- formal report, decision and gate record: absent and forbidden.

B02, B03 and B04 locks, reports, evidence rows, audit verdicts, plans, run-root
products and closure projections provide zero B05 criterion credit and must not
be read or copied into the clean B05 lineage.  The committed B04 contract may be
read only as the user-allowed preserved-science input; its bytes and any B04
implementation bytes still require fresh B05 review, tests and evidence.

The clean successor was born from exact repository identity
`8dab023613d3b2a6484327bc18d82e74caeccb1f` on
`refs/heads/users/perlee/doc-study`, using the new local branch
`refs/heads/users/perlee/s10r4-binding-05-clean` and worktree
`/data1/perlee/rocm-libraries-s10r4-b05-clean`.  Its sole ignored run root is
`agent_run/260802-ductile-factorized-guidance-s10r4-relational-selector-binding-05`.
No previous binding run root is a B05 input.

## 3. Binding-05 identity and role authority

- binding ID: `binding-05`;
- risk tier: `R3`;
- scientific gate: `S10R4`;
- execution tranche: `T-S10R4-B05`;
- closure unit: `CU-S10R4`;
- design:
  `study_docs/research/ductile-origami-warmstart/s10r4-stage1-relational-selector-operational-entry-design.md`;
- contract:
  `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4-stage1-relational-selector-entry-binding-05-contract.yaml`;
- prelock schema manifest:
  `study_docs/research/ductile-origami-warmstart/protocol/v1/manifests/s10r4-relational-selector-schema.json`;
- effective lock:
  `study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s10r4-stage1-relational-selector-entry-binding-05-lock.json`;
- terminal report:
  `study_docs/research/ductile-origami-warmstart/reports/staged/s10r4-stage1-relational-selector-entry-report.md`;
- positive-only compact record:
  `study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/gate-records/s10r4-s1-entry-go-relational-selector.json`.

The cumulative S10R4 lineage cap is exactly nine roles.  Seven historical roles
already exist.  This clean successor Main is role eight.  Role nine is reserved
for exactly one fresh terminal verifier who must remain Plan-A blind and must
not participate in implementation, prebinding audit or repair.  All preterminal
work must resume only these existing roles:

- `/root/s10r4_design_reviewer_a`;
- `/root/s10r4_design_reviewer_b`;
- `/root/s10r4_adversarial_auditor`;
- `/root/s10r4_fresh_implementer`.

No replacement implementer, auditor, reviewer, helper or second verifier may be
spawned without new explicit user authority.  A new root, binding or repair does
not reset role, resource or repair provenance.

## 4. Pinned source and fixed problem instance

The source authority is Ductile commit
`5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39`; its Tensile subtree tree is
`a60ed94f10563aa133782bb0ccc801aba279b843`.  Actual YAML is
`protocol/v1/inputs/s10-generated.yaml`, raw SHA-256
`faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36`.

Before any remaining-frame row or label, B05 must bind these source-only facts:

1. `LibraryIO.StrictTypeLoader` preserves explicit bool/int types, and
   `LibraryIO.readYAML` loads the actual YAML.
2. `Tensile` passes `config["BenchmarkProblems"]` to
   `BenchmarkProblems.main`; the first member of each entry is passed unchanged
   to `ProblemType`.
3. `assignParameterWithDefault` deep-copies the YAML value when present and the
   `_defaultProblemType` value otherwise.
4. The fixed instance is `OperationType=GEMM`, `TransposeA=False`,
   `TransposeB=False`, `Batched=True`, plus default `Sparse=0`,
   `AllowNoFreeDims=False`, `MetadataLayout=0`, `MXBlockA=0` and `MXBlockB=0`.
5. `ProblemType.__init__` applies defaults/overrides, calls `initGEMM`, then
   `assignDerivedParameters`.

The contract and schema manifest must bind blob OIDs and exact span hashes.  At
minimum they include:

| Source span | Blob OID | Span SHA-256 |
| --- | --- | --- |
| `LibraryIO.py:79-105` | `794e1e528e9113a25e46a8e628f7e441132e1a14` | `53a106366608d76a22d223c5b6c81dd12a0b31cfce4d9cf72ece467dc0cdb361` |
| `LibraryIO.py:345-359` | same | `81ae5ffcb435f19f8f39e0f850e08964f4ec0851b39fec6d6454bec97260a98a` |
| `Tensile.py:102-121` | `b89d54d2941521c2d0dbaadf82ac0c404c21c27e` | `1d5c7535aff4b089489b875537607e6c2d724a90a1db2655a2368afdf59b289f` |
| `Tensile.py:571-598` | same | `9923a0c97e0ec6b57020df38a37fc4ad7074e09498b8d3e50f47318dc96775ad` |
| `BenchmarkProblems.py:717-751` | `c9e4144ca0b2d7396c57249eaf3770b12ebd87f8` | `e697ce393063472c2d320d261025c3cbb7e93649027cd774bc342030aa089d9a` |
| `Common/Utilities.py:322-326` | `685ce17c5e581de3a388594667e1d075efcd9229` | `8d31082079c58d09ee67ac511b901209e60913b8953af6cb8962fa0753c1eb91` |
| `SolutionStructs/Problem.py:408-503` | `49aa4c66f53c42b7760617fdb1370155d02c862d` | `fd252fc9637c91e2f5225a0888a38af5b395af78f3f6a80d1e1c79f3049aac31` |
| `SolutionStructs/Problem.py:809-924` | same | `212d6d3c73adc4431a6e1c3d2894305640bd7e594ea0a877885b963babfb8122` |
| `SolutionStructs/Problem.py:1043-1078` | same | `696d59efd5544c35c718e95cbfdf938af5873d1d859e0a52c1c0dfd5882e7f0f` |
| `SolutionStructs/Problem.py:1086-1227` | same | `878cbb942c3647a655bf7ec227e4d7b865cfa2bf6b9089200493614c767e0ee8` |
| `KernelWriter.py:9230-9305` | `163fd4ceba214b89633af22eee83feee17fef294` | `083843736930c107dfc3104bae4b132764b411280bf73fe08948736885640012` |
| `KernelWriter.py:2579-2705` | same | `08a468d7509be2e66ffd13e71f5d3832fe635336b4bd06fa39e184a1c22d9252` |
| `KernelWriterAssembly.py:18160-18520` | `99ff3ec21c68facde233ba60073588bdfbefb281` | `1c35202621044d2769136dd2cdf74991ccccb154599dec07a7fbd3112184dbb1` |

Any commit, blob, line-span, AST or actual-YAML drift before lock is
`CHANGES_REQUIRED / not_evaluated / edge=null`.

## 5. Exactly one named relational proof rule

The only newly authorized relational rule is
`problemtype_index_to_macrotile_v1`.  It is a fixed-instance proof rule, not a
general symbolic executor.  Its canonical derivation is:

```text
actual YAML + defaults
  -> Batched=True, TransposeA=False, TransposeB=False,
     Sparse=0, AllowNoFreeDims=False, MetadataLayout=0,
     MXBlockA=0, MXBlockB=0
  -> sumIdx=3
  -> IndexAssignmentsA=[0,3,2]
  -> IndexAssignmentsB=[3,1,2]
  -> NumIndicesC=3
  -> IndicesFree=[0,1], IndicesBatch=[2], IndicesSummation=[3]
  -> Index01A=0, Index01B=1
  -> Index0=0, Index1=1, Tensor0=0, Tensor1=1
  -> getTensorParameters(A): tensorIdx=0, idx=ProblemType.Index0=0
  -> getTensorParameters(B): tensorIdx=1, idx=ProblemType.Index1=1
  -> ordinary and wave-separated TDM ti in {0,1}
  -> reachable keys are exactly MacroTile0 and MacroTile1
```

The proof must separately record every premise, exact Python type, assignment
site, guard, source blob/span and consumer.  It must cover both ordinary callers
and `initTDMDescriptorWaveSeparated(tPA,tPB)`.  Because `Sparse=0` and
`MXBlockA=MXBlockB=0`, Metadata and MX origins are unreachable for this fixed
workload; that unreachability must itself be proved from exact callers/guards,
not assumed.  Any unassigned `tensorIdx`, bool/int confusion, `tensorIdx=2`,
selector outside `{0,1}`, incomplete branch or additional reachable role fails
closed.

All other dynamic-key closure uses only source-local literal/caller-domain,
constant-propagation or guard proofs recorded per access.  Those proofs cannot
silently invoke another named relational rule.

## 6. Whole-subtree dynamic-access closure

The prelock schema is based on a whole-subtree AST and key-carrier def-use
census, not a grep spelling.  For the pinned Tensile subtree, the canonical
source-only baseline is exactly 89 dynamic `MacroTile*` subscript nodes: 68
direct key ASTs containing a `MacroTile` literal/identifier and 21 indirect
`kernel[tP["mt"]]` consumers whose carrier is assigned at
`KernelWriter.py:9267`.  The canonical 89-record census digest is
`7a4729775bc4fa39ada1b10667799422a4bda3e1bea8b55d1a2533275cba880b`.
The five f-string spellings and the 68 direct spellings are both incomplete
subsets and must not be used as the denominator.

Every canonical access record must contain at least source path, blob OID,
line/span, enclosing class/function stack, normalized subscript AST, base
container, selector expression, reachable guard, proved selector domain,
possible exact keys and proof-rule identity.  The terminal unresolved access
count must be exactly zero.

Reviewer A and Reviewer B must independently author and independently traverse
the closure.  Running the production implementation twice, sharing an exported
record list, or one reviewer checking the other's projection is not independent
authorship.  Their canonical records must match exactly on record membership,
blob/span, normalized AST, container, domain, exact keys and rule identity.
Any missing/extra record, denied read, traversal error, parser drift, unequal
canonical bytes or unresolved node is `CHANGES_REQUIRED` before lock.

## 7. Preserved scientific contract

B05 preserves without modification:

- 114 raw occurrences, multiplicity and raw denominator;
- complete ordered Census A 0-113 followed by complete ordered Census B 0-113;
- no early stop, deduplication, replacement, reordering, third pass or old
  prefix credit;
- resolver-effective partition, operational identity and collision rules;
- deterministic greedy `K=max(10,C_greedy)` with `10 <= K <= 20`;
- Mapping A and B each exact `3K` rows;
- the existing native conformance state machine and retry semantics;
- correctness at three anchors by three sizes, exactly nine cells;
- noise at nine groups by seven repeats, exactly 63 cells, with
  `NumWarmups=321`, `EnqueuesPerSync=321`, `CV P95 <= 0.5%` and the existing
  `delta_noise` calculation;
- GPU use only in the existing `perlee` container, selecting the lowest
  eligible free `gfx942` at the GPU phase;
- canonical outcome priority and the only possible positive criterion
  `S1_ENTRY_GO_EXACT_FRAME`.

The source schema, dual closure projections and rule tests are prelock technical
evidence.  They cannot supply raw-row, survivor, collision, atom, K, mapping or
outcome evidence.

## 8. Information firewall and required order

Before the effective lock, allowed reads are governance, the B04 preserved
contract, current B05 authority/design/contract/plan, pinned source, the actual
YAML ProblemType header/candidate-universe schema, synthetic fixtures and
prelocked registries.  Remaining formal frame rows, previous binding formal
artifacts and any outcome-bearing report are forbidden.

Required order:

1. authority/design plus parent/S11 projection review and exact-path commit;
2. standalone B05 machine contract, two precommit audits, commit and two
   postcommit audits;
3. Main-authored transient Plan-B;
4. adversarial Plan-B/contract/authority audit;
5. Main-authored transient Plan-A;
6. resume the existing implementer with Plan-A only;
7. offline implementation/tests and two independently authored closure
   projections;
8. adversarial prelabel audit;
9. no-overwrite effective lock, exact seal, ordinal-0 activation and
   `LOCKED_READY`;
10. formal Census A/B, selection, mapping A/B, native, GPU, correctness, noise,
    decision and independent reproduction in frozen order;
11. spawn exactly one fresh terminal verifier;
12. truthful closeout, exact terminal commit and postcommit audit.

No source or test implementation may begin before the contract audits and
plans.  Main authors plans and authority only; Main never implements source.

## 9. Exact write and delivery authority

### 9.1 Tracked implementation paths

Only these implementation/test paths may be modified after Plan-A:

- `study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/s10r4-entry.schema.json`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/__init__.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/contract.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/conformance.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/frame.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/ledger.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/census.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/relational_selector.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/selector.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/mapping.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/state_machine.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/correctness.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/native_adapter.py`;
- `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/native_formocast_runtime_adapter.cpp`;
- `projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10r4_entry.py`.

Pinned Ductile, hipBLASLt client and shared Origami sources are read/build inputs,
not modification targets.

### 9.2 Tracked protocol/evidence delivery paths

Only these additional S10R4 tracked outputs are authorized:

- the B05 contract, schema manifest, lock, report and positive record named in
  section 3;
- `protocol/v1/manifests/s10r4-codegen-classification.json`;
- `protocol/v1/manifests/s10r4-operational-selection.json`;
- `protocol/v1/manifests/s10r4-mapping-corpus.json`;
- `protocol/v1/manifests/s10r4-sentinel-conformance.json`;
- `protocol/v1/manifests/s10r4-environment.json`;
- `protocol/v1/evidence/s10r4-smoke-correctness.json`;
- `protocol/v1/evidence/s10r4-noise-pilot.json`;
- `protocol/v1/evidence/s10r4-decision.json`;
- `protocol/v1/evidence/s10r4-operational-blocker.json`.

The positive record and blocker are mutually exclusive.  The contract must
convert these repository-relative paths to full exact paths and freeze exact
run-root files/pattern domains before Plan-B.  Plan-A may narrow but never
expand them.

### 9.3 Authority/parent delivery paths

Authority and closeout may modify only:

- this authority;
- the B05 design;
- `study_docs/research/surrogate-dse-plan.md`;
- `study_docs/research/ductile-origami-warmstart-experiment-plan.md`;
- `study_docs/research/ductile-origami-warmstart/README.md`;
- `study_docs/research/ductile-origami-warmstart/s11-stage1-model-only-factorization-design.md`.

No S11 implementation, evidence, report or lock is authorized.  No push,
dependency install, container mutation, destructive cleanup, downgrade or
scientific substitution is authorized.

## 10. Outcomes, claim and S11 edge

Outcome priority remains:

1. `CHANGES_REQUIRED / not_evaluated / edge=null` for source/rule/schema,
   closure, implementation, lineage, partial, discordant or unknown evidence;
2. operational `BLOCKED / not_evaluated / edge=null` only for material external
   safety, availability, preservation or authority boundaries;
3. `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`;
4. `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-CORRECTNESS / edge=null`;
5. `inconclusive / FT-INCONCLUSIVE / edge=null` after complete noise evidence;
6. `positive / S1_ENTRY_GO_EXACT_FRAME / failure_id=null`.

Only a terminal commit followed by a passing independent postcommit audit can
expose `S10R4:S1_ENTRY_GO_EXACT_FRAME -> S11`.  Even then the claim is limited
to this fixed 114-occurrence raw frame producing a reproducible bounded
distinct-effective-state fixture under the pinned resolver, relational selector
proof and normal KernelWriter workflow.  It does not establish raw injectivity,
general support, value-level causal effect, survival probability, ranking,
factorization or production readiness.
