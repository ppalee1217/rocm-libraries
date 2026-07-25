---
checkpoint_id: S00
title: Evidence contract、lineage 與 observability foundation
stage: foundation
design_status: approved
execution_status: completed
checkpoint_state: CHECKPOINT_COMPLETE
scientific_outcome: positive
lock_state: effective
hypothesis_id: S00-H1
dependencies: []
entry_criteria: []
criterion_refs:
  - S00_EVIDENCE_READY
failure_ids:
  - FT-PLUMBING
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S00_EVIDENCE_READY
    target_checkpoint: S10
formal_report_path: reports/staged/s00-foundation-verification-report.md
blocker_path: null
effective_lock_path: protocol/v1/locks/s00-foundation-lock-successor-001.json
implementation_boundary_max:
  - protocol/v1/**
  - checkpoint/resume and observer integration points selected by future exact-path planning
  - fresh deterministic foundation fixtures and their tests
delivery_boundary_max:
  - protocol/v1/**
  - checkpoint/resume and observer integration points selected by future exact-path planning
  - fresh deterministic foundation fixtures and their tests
  - reports/staged/s00-foundation-verification-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - README.md
  - s00-evidence-contract-lineage-observability-design.md
forbidden_downstream_roots:
  - reports/staged/s10-stage1-entry-gate-report.md
  - reports/staged/s11-stage1-model-only-factorization-report.md
  - reports/staged/s12-stage1-real-score-audit-report.md
  - reports/gen0-factorization-mvp-report.md
  - reports/short-horizon-persistence-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
---

# S00 — Evidence contract、lineage 與 observability foundation

導航：[active checkpoint index](README.md)｜[research charter](../surrogate-dse-plan.md)｜[experiment plan](../ductile-origami-warmstart-experiment-plan.md)

> **Verified E/C lifecycle boundary：**S00的immutable execution-authority view（E）
> 由baseline commit
> `60775f12843bee9f95cb0bef4e91de8bc4dc9dc3`、exact 29 implementation blobs與
> exact兩份Plan-B重建；本design、parent plan與active README在E使用baseline
> bytes，`protocol/v1/README.md`是E runbook。本檔目前是post-PASS
> closeout-projection view（C）的三份投影之一；在C直接執行historical outcome
> writer必須於寫入前`bound_hash_mismatch`。Green E重建、C拒絕probe與exact
> E→C hashes見[formal report](reports/staged/s00-foundation-verification-report.md)。
> 重建依賴baseline Git object與兩份exact ignored Plan-B；不宣稱standalone
> source-tarball portability。

## 1. 白話目標

從真正的zero state建立可信的證據底座：先證明observer不改變搜尋、checkpoint/resume與continuous execution等價、runtime artifacts可對帳，而且每個outcome都能追溯到唯一effective lock。S00不繼承、搬移或重新命名任何M00 protocol artifact。

## 2. Hypothesis 與 falsification

**S00-H1：**使用全新schema、validator、lock writer與fresh deterministic fixtures，可以在不改變相同seed的proposals、fitness、population trajectory與termination語意下，完整重建Stage 1–3需要的evidence、resume與lineage。

以下任一項反證或使結果無法判讀：

- observer開關改變canonical proposal set、RNG state或fitness；
- continuous與checkpoint/resume的first divergent event無法消除；
- generated input、backend result、benchmark observation與summary無法reconcile；
- contract／lock可被runtime參數繞過；
- lineage缺少parent、source、fixture、seed或input identity；
- PASS依賴retired M00 schema、fixture、registry、hash、lock或test。

## 3. Dependencies、entry 與 outgoing edge

S00沒有上游checkpoint，但開始執行前必須有一個ordinary committed baseline，包含本design bundle與intentional legacy protocol deletions。該baseline commit不是S00完成證據。

唯一outgoing edge是：

```text
S00_EVIDENCE_READY -> S10
```

Negative或inconclusive在evidence integrity完整時仍要formal report／closeout／commit，但不解鎖S10。缺少必要authority或durable evidence時可以`BLOCKED`；implementation defect先在S00範圍內修復並重驗，不能用blocker取代修復。

## 4. Maximum implementation 與 delivery boundary

本design只給maximum boundary。Future Plan-A／Plan-B必須把它縮成exact path與symbol whitelist。

允許：

- 首次建立`protocol/v1/`的schema、validator、study contract、append-only amendment ledger與lock writer；
- observer、checkpoint/resume、artifact reconciliation與lineage的最小integration points；
- fresh deterministic valid／invalid／duplicate／failure fixtures及neutrality／resume tests；
- S00 report、checkpoint-specific parent hunk與S00 design status closeout。

禁止：

- 從Git history或legacy檔案複製M00 identity、schema、criterion、registry、hash、lock、path、fixture或test；
- 修改GA operator、fitness、mutation、selection、survival或RNG consumption；
- 探索S10 YAML/GPU/mapping，或建立任何S10+ evidence/report；
- 建立compatibility stub、migration adapter、fake hash、placeholder lock或空白report。

## 5. Future effective lock 與 bootstrap order

Future S00第一次建立：

```text
protocol/v1/README.md
protocol/v1/study-contract.yaml
protocol/v1/amendment-ledger.jsonl
protocol/v1/schemas/
protocol/v1/locks/s00-foundation-lock.json
```

Genesis identity必須全新，且`parent_lock: null`。執行順序固定：

1. 先實作並驗證schema、validator、lock writer與fresh fixtures；
2. 將committed rule／skill／charter／parent／S00 design revisions、Plan-B、exact whitelists、fixtures、seeds與report target寫入lock；
3. effective lock成功驗證後，才產生neutrality、resume parity、reconciliation與lineage outcome evidence；
4. evidence開始後若schema、fixture或whitelist改變，append amendment並建立新lock，重跑全部affected evidence，不得覆寫原lock。

## 6. Inputs、outputs 與 controls

Inputs：

- committed authority revisions；
- fresh synthetic evaluator與small deterministic search spaces；
- future Plan-A／frozen Plan-B；
- exact implementation／delivery whitelists；
- observer/checkpoint integration points的pinned source revision。

Logical outputs：

- study-contract、amendment、lock、event、checkpoint與lineage schemas；
- neutrality、resume parity、reconciliation與fail-closed evidence；
- machine-readableS00 decision；
- 唯一formal report。

Controls：

- observer off vs on：相同seed、space、evaluator；
- continuous vs checkpoint/resume；
- valid、invalid、duplicate、partial與failure fixtures；
- callback不得消耗GA RNG；
- population用canonicalized config-set hash比較，不使用set iteration order；
- malformed／missing lineage必須fail closed。

Measurement boundary只涵蓋evidence semantics；synthetic fixture runtime不能冒充GPU workflow成本。

## 7. Acceptance binding 與 stop matrix

唯一positive criterion是parent定義的`S00_EVIDENCE_READY`，必須同時綁定：

- observer neutrality；
- checkpoint/resume parity；
- artifact reconciliation；
- lineage／lock fail-closed；
- parent/input/source/fixture hash enforcement。

| 狀況 | checkpoint處理 | outgoing edge |
| --- | --- | --- |
| 全部S00 criterion通過 | positive closeout | S10 |
| observer／resume／reconciliation implementation defect | `CHANGES_REQUIRED`，限S00修復並全量重驗 | 無 |
| evidence完整但foundation假設被反證 | negative或inconclusive formal closeout | 無 |
| authority或durable evidence確實不可取得 | `BLOCKED`，不得標complete | 無 |
| 需要縮減neutrality、resume、lineage或reconciliation | `blocked-awaiting-user-decision` | 無 |

## 8. Report 與 checkpoint closeout

唯一formal report：

`reports/staged/s00-foundation-verification-report.md`

Report必須self-contained地記錄frozen oracle、commands、working directories、exit codes、raw artifact hashes、每輪finding／repair、criterion結果、first divergence、outcome、failure ID、能與不能支持的結論。Technical `PASS`只進`VERIFIED_PENDING_CLOSEOUT`；parent hunk、原verifier的`CLOSEOUT_ACK`、isolated commit與post-commit audit全過後才是`CHECKPOINT_COMPLETE`。

### Verified closeout projection

- Formal report：
  [S00 Evidence Foundation — Verification and Closeout Report](reports/staged/s00-foundation-verification-report.md)
- Effective lock：`protocol/v1/locks/s00-foundation-lock-successor-001.json`
- Technical verification：原verifier FULL `PASS`，`AC-01`–`AC-10`全PASS
- Scientific outcome：`positive`
- Completion：formal report、exact staged-byte `CLOSEOUT_ACK`、single exact-path
  closure commit與post-commit audit完成後，投影為`CHECKPOINT_COMPLETE`
- Verified edge：`S00_EVIDENCE_READY -> S10`只解除S10 dependency；S10仍
  `not_started`、lock absent，沒有S10 implementation或outcome
- Claim boundary：只支持CPU-only synthetic observer/resume/lineage/reconciliation
  semantics，不支持GPU availability、mapping、performance或Stage 1 readiness

## 9. Design-consensus record

本checkpoint是同一個十checkpoint bundle-level雙reviewer交叉詰問的一部分。

- Reviewer A objection：若把M00 prototype當foundation reuse source，新的foundation仍會暗中繼承retired identity與PASS語意。
- Reviewer B objection：若S10可與S00並行，S10可能先產生無法由effective evidence interface承載的artifact。
- 採納方案：true genesis、fresh fixtures、`parent_lock: null`、lock-before-evidence，以及唯一`S00_EVIDENCE_READY -> S10` edge。
- 捨棄方案：M00 schema migration、compatibility target、prototype PASS reuse與S00/S10 parallel discovery；理由是它們破壞zero-state與lineage authority。
- Shared resolution：S00可以terminal negative／inconclusive，但只有positive criterion能解鎖S10；任何downgrade需user decision。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`
