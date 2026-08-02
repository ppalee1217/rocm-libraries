---
checkpoint_id: S10R4
binding_id: binding-05
title: Stage 1 relational-selector operational entry recovery
stage: 1
design_status: approved
authority_projection: user_approved_pending_identical_prompt_review_and_exact_commit
execution_status: not_started
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R3
scientific_gate: S10R4
execution_tranche: T-S10R4-B05
closure_unit: CU-S10R4
hypothesis_id: S10R4-H1E
dependencies:
  - checkpoint_id: S10R3
    required_terminal: CHECKPOINT_COMPLETE_negative_edge_null
entry_criteria:
  - committed_binding_05_relational_selector_authority
  - intact_sealed_S10R3_G3_raw_occurrence_frame
  - independently_authored_whole_subtree_closure_with_zero_unresolved
  - durable_binding_05_contract_and_effective_lock_before_outcomes
criterion_refs:
  - S1_ENTRY_GO_EXACT_FRAME
  - S1_ENTRY_BLOCKED
failure_ids:
  - FT-BLOCKED-MAPPING
  - FT-BLOCKED-CORRECTNESS
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S1_ENTRY_GO_EXACT_FRAME
    target_checkpoint: S11
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s10r4-s1-entry-go-relational-selector.json
formal_report_path: reports/staged/s10r4-stage1-relational-selector-entry-report.md
future_frozen_contract_path: protocol/v1/s10r4-stage1-relational-selector-entry-binding-05-contract.yaml
future_schema_manifest_path: protocol/v1/manifests/s10r4-relational-selector-schema.json
future_effective_lock_path: protocol/v1/locks/s10r4-stage1-relational-selector-entry-binding-05-lock.json
consensus_status: user_approved_pending_reviewer_a_b_precommit_and_postcommit_audits
---

# S10R4 - Relational-selector operational entry recovery

Navigation: [checkpoint index](README.md) | [B05 authority](s10r4-binding-05-relational-selector-recovery-authority.md) | [B04 design](s10r4-stage1-resolver-effective-operational-entry-design.md) | [S11](s11-stage1-model-only-factorization-design.md)

## 1. Goal and unchanged hypothesis

The B04 layered identity is scientifically retained.  B05 repairs a technical
source-closure gap before any formal row: a literal `tensorIdx` is not the same
value as the derived `ProblemType.Index{tensorIdx}` consumed by TDM's dynamic
`MacroTile{ti}` lookup.

**S10R4-H1E remains unchanged:** the fixed 114-occurrence raw frame, under the
pinned resolver and normal error-tolerant KernelWriter workflow, contains a
deterministically selected distinct stable operational-identity fixture with
`10 <= K <= 20` that covers all realized prelocked mandatory atoms and passes
mapping, native conformance, correctness and noise gates.

B05 does not redraw, change the denominator, inspect feasibility before lock or
claim that the repair improves survival.  It only makes the prelock proof
complete enough to know which `MacroTile*` keys the pinned source can request.

## 2. Clean-context lineage

B04 is frozen as
`superseded_prelock / cancelled / BLOCKED / CHANGES_REQUIRED /
not_evaluated / edge=null / lock=absent / lock_never_created=true`.
B02-B04 formal artifacts and outcomes are forbidden inputs.  The B04 contract
is an allowed preserved-science document but provides no B05 test, audit, lock
or criterion credit.

The B05 worktree, branch and ignored run root are those fixed by the authority.
All reads and commands are append-only recorded in
`access-command-provenance.jsonl`.  An allowed actual-YAML overread beyond the
ProblemType header is quarantined: no displayed candidate-group row may be used
for schema, feasibility, coverage, selection or outcome reasoning.

## 3. Source-to-consumer derivation

### 3.1 YAML, defaults and ProblemType

The source manifest binds the exact loader and handoff chain:

```text
LibraryIO.readYAML(StrictTypeLoader)
  -> Tensile config["BenchmarkProblems"]
  -> BenchmarkProblems.main entry[0]
  -> ProblemType(problemTypeConfig)
  -> assignParameterWithDefault
  -> initGEMM
  -> assignDerivedParameters
```

The fixed ProblemType input is:

| Field | Origin | Typed value |
| --- | --- | --- |
| `OperationType` | actual YAML | string `GEMM` |
| `TransposeA` | actual YAML | bool `False` |
| `TransposeB` | actual YAML overriding default `True` | bool `False` |
| `Batched` | actual YAML overriding default `False` | bool `True` |
| `Sparse` | pinned default | int `0` |
| `AllowNoFreeDims` | pinned default | bool `False` |
| `MetadataLayout` | pinned default | int `0` |
| `MXBlockA` | pinned default | int `0` |
| `MXBlockB` | pinned default | int `0` |

The only accepted result is:

```text
sumIdx=3
IndexAssignmentsA=[0,3,2]
IndexAssignmentsB=[3,1,2]
NumIndicesC=3
TotalIndices=4
IndicesFree=[0,1]
IndicesBatch=[2]
IndicesSummation=[3]
Index01A=0
Index01B=1
Index0=0
Index1=1
Tensor0=0
Tensor1=1
```

Every value and type is compared against independently reconstructed expected
canonical bytes.  A live invocation is corroboration, not the sole proof.

### 3.2 `problemtype_index_to_macrotile_v1`

This is the design's exactly one new named relational rule.  For actual A and B
tensor parameters:

```text
cM=A -> tensorIdx=0 -> idx=ProblemType.Index0=0 -> ti=0 -> MacroTile0
cM=B -> tensorIdx=1 -> idx=ProblemType.Index1=1 -> ti=1 -> MacroTile1
```

The rule must prove both consumers:

- `KernelWriterAssembly.initTDMDescriptor`;
- `KernelWriterAssembly.initTDMDescriptorWaveSeparatedImpl`, reached only
  through `initTDMDescriptorWaveSeparated(tPA,tPB)`.

It also binds the ordinary callers in `KernelWriter.setupNewTile`.  Metadata
callers are disabled by `Sparse=0`; MX callers are disabled by
`MXBlockA=MXBlockB=0`.  Their absence is a guard proof, not a guessed omission.

The following are immediate failures: missing typed premise, different
ProblemType list/order, `tensorIdx` unassigned or outside `{0,1}`, selector
outside `{0,1}`, wrong A/B association, reachable Metadata/MX role, new consumer
or unmatched source span.

## 4. Whole-subtree closure projections

The pinned-source baseline is exactly 89 dynamic `MacroTile*` subscript nodes,
canonical digest
`7a4729775bc4fa39ada1b10667799422a4bda3e1bea8b55d1a2533275cba880b`.
It comprises 68 direct `%`-formatted/f-string/named-key ASTs plus 21 indirect
`kernel[tP["mt"]]` consumers reached from the exact carrier definition at
`KernelWriter.py:9267`.  Neither the five f-string spellings nor the 68 direct
spellings are a sufficient census.

Each closure projection emits a canonical record for every node:

```text
source commit/tree/blob/path/span
normalized AST and enclosing container stack
base container and selector expression
fixed-instance reachability guard
selector domain with exact Python types
possible exact MacroTile keys
proof kind and rule identity
resolution status
```

Reviewer A and Reviewer B independently implement the traversal and author
their own projections under the B05 ignored run root.  They may consult the same
authority, pinned source and schema, but may not share code, an exported record
list or each other's output before sealing their own projection.  The production
implementation is a third corroborating traversal, not one of the two
independent projections.

Acceptance requires:

- both independent counts exactly 89, partitioned as 68 direct plus 21
  carrier-def-use consumers;
- identical canonical record bytes after schema-prescribed ordering;
- source commit/tree/blob/span and normalized AST parity;
- every node classified reachable or guard-proven unreachable;
- every reachable key domain finite and exact;
- both TDM nodes use `problemtype_index_to_macrotile_v1`;
- terminal `unresolved_dynamic_access_count=0`;
- no denied read, parse failure, skipped file or coverage gap.

## 5. Prelock schema manifest

`protocol/v1/manifests/s10r4-relational-selector-schema.json` is created and
committed before the effective lock.  It binds:

- actual YAML and pinned source identities;
- the exact source-span table in the authority;
- the AST/key-carrier census algorithm/version and canonical 89-record baseline;
- record schema and canonical JSON rules;
- the complete typed premises/conclusions of
  `problemtype_index_to_macrotile_v1`;
- allowed source-local proof kinds for all other nodes;
- ordinary/wave-separated caller and consumer inventories;
- guarded Metadata/MX reachability conclusions;
- independent projection paths/hashes and equality verdict;
- fail-closed conditions and zero-unresolved requirement.

Digest equality never substitutes for canonical-byte equality.  The manifest
may not contain formal row state, survivor predictions, realized-atom coverage,
K feasibility, mapping output or labels.

## 6. Formal workload after `LOCKED_READY`

After contract, Plan-B, Plan-A, implementation, offline tests, independent
closure equality, adversarial prelabel audit, exact no-overwrite lock and
ordinal-0 activation:

1. Census A runs registry indices 0-113 in order.
2. Every child verifies raw identity, resolves one Solution, captures layered
   identities and continues through the original KernelWriter path.
3. Only after A has 114 terminal children may Census B run 0-113 in order.
4. No early stop, reorder, deduplication, replacement, third pass or old-prefix
   credit is allowed.

Resolver projection, codegen terminal semantics and operational identity must
match across A/B.  Discordance, partial output, unknown transform, source drift,
association failure or rule mismatch is `CHANGES_REQUIRED`, not attrition.

## 7. Collision, selection and mapping

Raw multiplicity remains exactly 114.  Resolver-effective groups retain all raw
aliases; stable operational groups require compatible terminal semantics and
identical codegen semantic bytes for all aliases and both passes.  Projection
falsification cannot be hidden by splitting a collision class.

Selection remains:

```text
mandatory_atoms = prelocked_candidate_atoms intersect realized_atoms(stable groups)
C_greedy = deterministic greedy cover size
K = max(10, C_greedy)
10 <= K <= 20
```

Mapping A and B each contain exactly `3K` rows.  Every row binds operational
identity, representative raw occurrence, aliases/multiplicity, size,
SizeMapping, Formocast/runtime inputs and field provenance.  First complete
success forbids retry.  Only the same prelocked allowlisted native failure in
exactly two complete attempts is mapping-negative.  Guessing, drift, partial,
failure-to-success, unequal signatures or a third attempt is
`CHANGES_REQUIRED`.

## 8. Native, correctness and noise

Native conformance preserves the pinned Formocast/runtime consumer, guard order
and fault substitutions.  Correctness uses selected sorted anchors
`{0,floor((K-1)/2),K-1}` by three frozen sizes for exactly nine cells.  Noise
begins only after all nine pass and remains nine groups by seven repeats,
exactly 63 cells, with frozen warmups/enqueues, P95 CV threshold and
`delta_noise` rule.

GPU execution is allowed only in the existing `perlee` container and only in
the GPU phase.  The runner selects the lowest eligible free `gfx942` after
foreign-PID rejection and records the exact environment.  No reservation,
container lifecycle change or dependency install is authorized.

## 9. Outcome matrix and stopping

- Source/rule/schema/closure/lineage/implementation/partial/unknown or
  discordant evidence: `CHANGES_REQUIRED / not_evaluated / edge=null`.
- Material external safety/availability/preservation/authority boundary:
  operational `BLOCKED / not_evaluated / edge=null`.
- Complete mapping branch failure:
  `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`.
- Frozen reproducible correctness failure:
  `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-CORRECTNESS / edge=null`.
- Complete 63-cell noise criterion failure:
  `inconclusive / FT-INCONCLUSIVE / edge=null`.
- All gates, reproduction, fresh verification and closure pass:
  `positive / S1_ENTRY_GO_EXACT_FRAME / failure_id=null`.

Once a terminal branch is determined, later scientific stages are not run.
Interruptions resume only from atomic boundaries; runtime is not an
optional-stopping rule.

## 10. Verification, claim and downstream boundary

The one fresh terminal verifier receives the frozen contract, frozen Plan-B
(including its SHA-256), effective lock, baseline, current implementation and
raw current B05 evidence/reproduction inputs, but did not implement or preaudit
them.  The verifier must remain Plan-A blind: it must not read or receive Plan-A
or any Plan-A summary.  It independently recomputes the 89-node closure, named
rule premises/conclusions, 114 denominator, A/B parity, collision multiplicity,
realized atoms, greedy trace/K, mapping counts, every reached gate and unique
outcome.

Positive, negative and inconclusive outcomes require a truthful B05 report,
exact-path local terminal commit and passing postcommit audit.  Only a
post-audited positive exposes `S10R4:S1_ENTRY_GO_EXACT_FRAME -> S11` and creates
`s10r4-s1-entry-go-relational-selector.json`.

S11 must still create fresh/disjoint
`F_valid(raw) -> F_effective -> F_codegen`.  S10R4 rows, K and outcomes cannot
become S11's formal population.  B05 authorizes no S11 implementation, no push
and no claim beyond the fixed-frame bounded operational-entry fixture.
