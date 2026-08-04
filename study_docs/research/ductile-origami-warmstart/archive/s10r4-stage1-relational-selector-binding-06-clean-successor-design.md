---
checkpoint_id: S10R4
binding_id: binding-06
title: Stage 1 relational-selector clean provenance successor
stage: 1
design_status: approved
authority_projection: user_approved_pending_identical_candidate_precommit_and_postcommit_audits
execution_status: not_started
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
risk_tier: R3
scientific_gate: S10R4
execution_tranche: T-S10R4-B06
closure_unit: CU-S10R4
hypothesis_id: S10R4-H1E
dependencies:
  - checkpoint_id: S10R3
    required_terminal: CHECKPOINT_COMPLETE_negative_edge_null
entry_criteria:
  - committed_binding_06_provenance_recovery_authority
  - intact_binding_05_preserved_science_bytes_with_zero_gate_credit
  - fresh_binding_06_standalone_contract_and_audits
  - fresh_binding_06_plan_b_then_plan_a
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
future_frozen_contract_path: protocol/v1/s10r4-stage1-relational-selector-entry-binding-06-contract.yaml
future_schema_manifest_path: protocol/v1/manifests/s10r4-relational-selector-schema.json
future_effective_lock_path: protocol/v1/locks/s10r4-stage1-relational-selector-entry-binding-06-lock.json
consensus_status: user_approved_pending_reviewer_b_adversarial_precommit_and_postcommit_audits
---

# S10R4 — Binding-06 clean provenance successor

Navigation: [checkpoint index](../README.md) | [B06 authority](s10r4-binding-06-provenance-recovery-authority.md) | [immutable B05 design](s10r4-stage1-relational-selector-operational-entry-design.md) | [S11](../s11-stage1-model-only-factorization-design.md)

## 1. Purpose and preserved science

Binding-06 repairs only the Binding-05 ignored-ledger provenance failure. The
immutable B05 design remains the approved scientific specification and a
preserved-science drafting input, but contributes zero B06 gate credit. Its
hypothesis, fixed 114-occurrence population, complete ordered 114x2 census,
source-to-selector proof, exact-89 closure, resolver and collision semantics,
deterministic `K=max(10,C_greedy)`, exact-two mapping resolution, native
conformance, 9-cell correctness, 63-cell noise protocol, thresholds, outcome
priority, claim boundary, and sole possible positive edge are unchanged.

The standalone B06 machine contract must fully restate and type those rules. A
pointer to B05 is not sufficient machine authority. The B05 design and contract
remain byte-immutable throughout this successor.

## 2. Clean execution identity

- birth commit: `3e020bcc6e307e7e6ffc4df1baa7e116da90c163`;
- branch: `refs/heads/users/perlee/s10r4-binding-06-clean`;
- worktree: `/data1/perlee/rocm-libraries-s10r4-b06-clean`;
- ignored run root: `agent_run/260803-ductile-factorized-guidance-s10r4-relational-selector-binding-06`;
- contract: `protocol/v1/s10r4-stage1-relational-selector-entry-binding-06-contract.yaml`;
- future lock: `protocol/v1/locks/s10r4-stage1-relational-selector-entry-binding-06-lock.json`.

The lock path is declared now and must remain absent until fresh implementation,
tests, independent closure projections, schema materialization, and prebinding
audit all pass. B05 run-root bytes, plans, audits, ledger events, evidence, and
closure state are forbidden inputs.

## 3. Required fresh order

1. Commit and post-audit this authority, design, and active parent projections.
2. Materialize the standalone B06 contract, obtain identical-candidate Reviewer
   B and adversarial precommit audits, commit it, then obtain both postcommit
   audits.
3. Main authors B06 Plan-B only from the sealed bundle, freezes it after parity
   and adversarial audit, then performs read-only inspection and authors Plan-A.
4. Resume the original implementer with Plan-A only for offline implementation
   and tests; Reviewer A and Reviewer B independently author closure projections.
5. After parity and adversarial prebinding audit, create the B06 lock by
   no-overwrite, commit exact implementation/schema/lock bytes, post-audit, and
   reach `LOCKED_READY` before formal observations.
6. Execute the complete frozen formal order, decision, and reproduction. Only
   then spawn the one reserved fresh role-9 terminal verifier, Plan-A blind.
7. Close out truthfully with exact-path local commit and postcommit audit. Do
   not push.

## 4. Roles, resources, and repair continuity

Seven historical roles, this same Main as ordinal 8, and the one reserved fresh
terminal verifier as ordinal 9 exhaust the lineage role cap. All preterminal
work resumes the existing Reviewer A, Reviewer B, adversarial auditor, and
implementer. Binding-06 does not reset repair counts or cumulative resource
provenance. Unknown historical telemetry stays `UNKNOWN`, not zero.

Ordinary unique contract-preserving repairs continue under reviewer governance.
Only a material change to protocol, claim, measurement lineage, stopping rule,
or scientific authority pauses for user decision. No dependency installation,
container mutation, destructive cleanup, external write, downgrade, S11
implementation, or push is authorized.

## 5. Outcome and edge invariant

The Binding-05 outcome matrix is unchanged. Provenance, source, closure,
implementation, lineage, partial, discordant, or unknown evidence fails closed
as `CHANGES_REQUIRED / not_evaluated / edge=null`. Material external operational
unavailability is `BLOCKED / not_evaluated / edge=null`. Complete frozen mapping
or correctness failure is negative; complete noise failure is inconclusive; only
all-gate success is positive `S1_ENTRY_GO_EXACT_FRAME`.

Only a post-audited terminal B06 positive commit exposes
`S10R4:S1_ENTRY_GO_EXACT_FRAME -> S11`. `LOCKED_READY`, technical PASS, or any
B05 artifact cannot activate S11.
