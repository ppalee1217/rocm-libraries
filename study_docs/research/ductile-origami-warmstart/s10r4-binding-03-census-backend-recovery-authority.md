# S10R4 Binding-03 Census Backend Recovery Authority (A50)

Status: approved operational execution-recovery authority, subject to exact
precommit review and postcommit audit.  This authority changes no scientific
hypothesis, workload, threshold, outcome matrix, claim, or outgoing edge.

## 1. Trigger and direct evidence

Binding-02 reached an effective lock and an independently audited
`LOCKED_READY` state at Phase-2 commit
`bd0d1b2859c67933a8136e27a8ce8e549a36113d`.  Its first Census-A child,
registry index 0 / config hash
`72dec49998a8db0bb51fcc723e5585925a7ec87906e61c149a7754d4c9b9ae0b`,
then stopped with a partial child: request, singleton YAML, stdout, stderr and
an early capability-probe `a.out` exist, while `result.json` and
`process-completion.json` are absent.  The parent failed closed.  No later
child or outcome-bearing document was created.

The partial inventory and root-cause evidence are recorded append-only in
binding-02 adjudication A8.  The stderr is exactly
`S10R4_FAIL_CLOSED: unexpected ValueError`; stdout stops after the benchmark
step's `# Fork Parameters:` line.

Two independent reviewers traced the exact exception:

1. committed `s10r4/census.py` writes singleton
   `Backend.Name: Exhaustive`;
2. pinned `BenchmarkProblems.py` lower-cases it to `exhaustive`;
3. the pinned backend factory registers only `tensile` and `ductile`;
4. factory dispatch raises `ValueError: Unknown backend: exhaustive` before
   `backend.run`.

The failure occurs before solution generation, `writeBenchmarkFiles`,
`writeSolutionsAndKernels`, `processKernelSource`, or KernelWriter.  It is not
a Ductile-validator/KernelWriter disagreement, normal native attrition, or a
scientific observation.

## 2. Binding-02 retirement at this authority commit

This authority commit is the effective retirement boundary for binding-02.
Its binding lifecycle becomes:

- retirement state: `retired_diagnostic_in_place`;
- execution status: `cancelled`;
- binding checkpoint state: `BLOCKED`;
- scientific outcome: `not_evaluated`;
- edge: `null`;
- lock state: `superseded`;
- completed terminal Census-A prefix: `0`;
- formal report, decision and gate record: forbidden.

S10R4 as a scientific checkpoint remains active through binding-03; this is
not a scientific `BLOCKED` terminal result and does not close S10R4.

The complete binding-02 run root remains immutable in place, including its
prelabel build, plans, ledgers, effective lock, activation event, writer-lock
inode and partial child.  No file may be deleted, moved, overwritten,
completed, aliased, mirrored, scanned as binding-03 input, or reused as
binding-03 evidence.  In particular, nobody may create binding-02
`result.json` or `process-completion.json` after this authority.

## 3. Binding-03 identity and unchanged science

The authorized successor is a new sibling execution binding:

- binding ID: `binding-03`;
- execution tranche: `T-S10R4-B03`;
- run root:
  `agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-03`;
- supplement:
  `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4-stage1-exact-frame-entry-binding-03-contract.yaml`;
- effective lock:
  `study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s10r4-stage1-exact-frame-entry-binding-03-lock.json`;
- prebinding ledger:
  `agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-03/gates/s10r4/audit-verdict.json`;
- postcommit ledger:
  `agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-03/closure/post-commit-audit.json`.

The base S10R4 scientific contract, actual YAML, S10R3 exact 114-row frame,
three sizes, two complete census passes, selection, mapping, native
conformance, correctness, noise, decision, reproduction, outcome matrix,
thresholds, claim boundary and only allowed S11 edge remain byte-for-byte or
canonically identical.  Binding-03 Census A starts at registry index 0 and
runs all 114 children; Census B then runs all 114.  There is no resume,
replacement or prefix credit from binding-02.

## 4. Exact semantic repair

The only scientific-path code-semantic delta authorized by A50 is:

```text
singleton Backend.Name: Exhaustive -> Tensile
```

Pinned `TensileBackend` is the repository's exhaustive fork-parameter
enumerator.  For the singleton document, all frame values become constants;
the empty fork/group Cartesian product contains exactly one permutation, and
the existing census wrapper must still fail closed unless exactly one
solution reaches the normal write boundary.

`Backend.Name: Ductile` is forbidden: it would start a GA/search, may read
performance data, and would change the fixed-frame census.  Any other backend,
exception-to-attrition conversion, retry, fallback, proxy, or bypass is also
forbidden.

All other changes are mechanical binding-03 path/lifecycle/source-identity
changes required to isolate the successor and seal it independently.

## 5. Strengthened source identity

The original Ductile and GEKO commits and original S10R4 source pins remain
unchanged.  Binding-03 additionally binds the pinned-commit tree object for:

```text
projects/hipblaslt/tensilelite/Tensile
tree OID a60ed94f10563aa133782bb0ccc801aba279b843
```

Fresh source verification must compare the complete `git ls-tree -r` path,
entry-type, mode and blob-OID set for that subtree at Ductile commit
`5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39`, then remeasure every
materialized ordinary file's Git blob OID.  Recording the tree OID without
performing this comparison is insufficient.

The following six files are separately named as the semantic decision chain;
they are not claimed to be a complete transitive closure:

| Repository path under `projects/hipblaslt/tensilelite` | Git blob OID |
| --- | --- |
| `Tensile/Tensile.py` | `b89d54d2941521c2d0dbaadf82ac0c404c21c27e` |
| `Tensile/backends/__init__.py` | `58b077a85bc87549e2c8562ca8d225555123591d` |
| `Tensile/backends/base.py` | `7b77c253e043e13e417130288fb4eb74b45617fb` |
| `Tensile/backends/tensile_backend.py` | `34e1444e2c5373857481f2e4198bce649a8e460a` |
| `Tensile/BenchmarkStructs.py` | `4968b29b5eacddc56b20c42cb4b2c1e3d8d6f406` |
| `Tensile/SolutionStructs/Solution.py` | `769d2f69c87ec0cad4569a9c2873ec5ec9da3d4f` |

## 6. Reuse and freshness boundary

Binding-03 may reuse only committed authority/scientific inputs, always with
fresh current-byte/ancestry remeasurement:

- committed S10R4 design and base scientific contract;
- actual YAML and source-commit identities;
- immutable S10R3 raw input identity;
- the three committed S10R4 exact-frame, size-registry and native-fixture
  records, after a fresh unchanged double replay and validation;
- unchanged implementation modules as committed source ancestry.

Binding-03 must freshly create:

- run root, Plan-B freeze, Plan-A revision and revision ledger;
- pinned-source materialization, complete subtree verification, native build,
  prelabel summary and self-check records under the binding-03 root;
- nonformal backend-dispatch diagnostic;
- prebinding audit ledger, effective lock, exact-path repair seal commit and
  ordinal-0 activation;
- every census/mapping/native/GPU/correctness/noise/decision/reproduction and
  fresh-verifier artifact.

No ignored binding-02 source/native/prelabel output, plan, audit, lock,
activation, raw child, formal document or conclusion is reusable.

## 7. Required prelock nonformal diagnostic

Before binding-03 lock creation, create an append-only diagnostic only under:

```text
agent_run/260802-ductile-factorized-guidance-s10r4-exact-frame-binding-03/
artifacts/prelabel-tests/repair-backend-dispatch-01/
```

It must be labelled `NONFORMAL_DIAGNOSTIC`, excluded from formal scanners and
never used as outcome evidence.  It contains two probes:

1. Direct factory dispatch captures the full traceback for
   `create('exhaustive')`, proves the exact unknown-backend/registered-set
   failure, and proves `create('tensile')` selects `TensileBackend`.
2. Under the proposed fixed bytes and archive-local cwd/request/artifact
   paths, recreate frame row 0's singleton and replace the outer
   `BenchmarkProblems.writeBenchmarkFiles` entry with a deliberate boundary
   sentinel.  Prove backend `Tensile`, one fork permutation, exactly one
   solution and mechanical correspondence between flattened raw fields and
   resolved solution state.  Stop before the original write and all
   KernelWriter/native execution.

The probes use the frozen CPU environment with
`PYTHONDONTWRITEBYTECODE=1`, read no GFLOPS, use no GPU, create no formal
`result.json` or `process-completion.json`, and do not touch the binding-02
partial.  Preserve exact argv/cwd/environment, source identities, stdout,
stderr, traceback, manifest and diagnostic completion.

## 8. Implementation, audit and seal boundary

Pre-evidence implementation may modify only these seven committed paths:

1. `study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10r4_entry.py`
2. `study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/s10r4-entry.schema.json`
3. `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/contract.py`
4. `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/census.py`
5. `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/correctness.py`
6. `study_docs/research/ductile-origami-warmstart/protocol/v1/s10r4/native_adapter.py`
7. `projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10r4_entry.py`

The binding-03 Phase-2 repair commit contains exactly those seven changed
paths plus the new binding-03 effective lock: eight paths total.  All other
tracked paths, including the three committed manifests and eight unchanged
implementation modules, must remain byte-identical.  No broad staging is
allowed.

The order is mandatory:

1. independent precommit reviews and exact authority commit;
2. machine-readable binding-03 supplement, independent reviews, exact commit
   and postcommit audit;
3. fresh Plan-B/Plan-A and implementation;
4. fresh prelabel source/tree/native build plus the nonformal diagnostic;
5. full offline/unit verification and final adversarial prebinding audit;
6. no-overwrite binding-03 lock and exact-eight local seal commit;
7. fresh ordinal-0 activation proving all binding-03 formal/outcome paths
   absent, then `LOCKED_READY`;
8. complete formal sequence from Census-A registry index 0;
9. still-fresh independent verification, truthful closeout and terminal audit.

No push is authorized.  The failed binding-02 attempt's wall/CPU/storage,
role usage and repair history carry forward; the successor does not reset any
resource or governance account.  Ordinary planning variance remains
notify-and-continue unless actual capacity, preservation or complete-workload
safety is materially threatened.
