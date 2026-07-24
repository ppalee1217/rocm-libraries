---
milestone_id: S00
title: Evidence contract、lineage 與 observability foundation
stage: cross_cutting
lifecycle: active
design_status: draft
execution_status: not_started
outcome: not_evaluated
decision: pending
hypothesis_id: S00-H1
depends_on: []
entry_gate_ids: []
criterion_refs: [S00_EVIDENCE_READY]
failure_taxonomy_refs: [FT-PLUMBING, FT-INCONCLUSIVE]
planned_report_paths:
  - ../../reports/staged/s00-foundation-verification-report.md
authority:
  charter: ../../../surrogate-dse-plan.md
  protocol: ../../../ductile-origami-warmstart-experiment-plan.md
  charter_hash: pending
  protocol_hash: pending
lock:
  approved_at: null
  locked_at: null
  lock_sha256: null
supersedes: [M00-concepts-only]
---

# S00 — Evidence contract、lineage 與 observability foundation

導航：[design index](../README.md)

## 1. Authority 與 change budget

本檔只定義 evidence infrastructure 的 implementation handoff；scientific thresholds、samples、seeds與 claim一律引用 parent。

允許：

- 建立新的 stage-gated contract／lock schema；
- observer、runner、checkpoint、artifact reconciliation；
- neutrality／resume／lineage tests。

禁止：

- 改 GA 搜尋 operator、RNG順序或fitness；
- 沿用 legacy M00 criterion authority；
- 把 prototype lock改名後冒充S00完成。

## 2. 白話目標

先證明「記錄實驗」不會改變實驗，且任何比較都能從 raw artifacts、checkpoint與lineage重新對帳。

## 3. Hypothesis 與 falsification

**S00-H1：**可以在不改變相同 seed 的 proposals、fitness、population trajectory與termination語意下，完整記錄並重建 Stage 1–3 所需 evidence。

反證：

- observer開關改變 canonical proposal sets或RNG state；
- continuous與resume trajectory不一致；
- artifact無法和backend／benchmark結果對帳；
- contract可被執行參數繞過；
- parent／input hash lineage缺失或不可驗證。

## 4. 能與不能說明

能：

- evidence harness non-perturbing；
- checkpoint/resume等價；
- lineage與artifact reconciliation可用。

不能：

- GPU環境可用；
- Formocast mapping／ranking正確；
- guidance或Gen0有效。

## 5. Inputs 與 entry evidence

- pinned Ductile／runner／observer source；
- parent charter與experiment plan hashes；
- legacy M00 prototype與tests，只作migration input；
- deterministic synthetic evaluator與至少一個small valid search space。

## 6. Outputs／artifacts

- `stage-gated-contract.schema.json`
- `stage-gated-contract.yaml`
- `protocol-lock.json`
- `lineage-manifest.schema.json`
- observer event schema
- checkpoint lineage schema
- `s00-neutrality-results.json`
- `s00-resume-parity-results.json`
- `s00-reconciliation-results.json`
- `s00-decision.json`

所有 artifacts須帶schema version、source hash、parent hash與creation provenance。

## 7. Controls 與 measurement boundary

- observer off vs on：相同seed、space、evaluator；
- continuous vs checkpoint/resume；
- valid、invalid、duplicate與failure fixtures；
- randomized observer callback不可消耗GA RNG；
- population比較使用canonicalized config-set hash，不依賴set iteration order。

只驗 evidence semantics，不宣稱runtime overhead代表GPU workflow。

## 8. Implementation points

- `Tensile/ductile/algorithm/ga.py` observer／checkpoint邊界；
- `Tensile/ductile/core/space.py` sampling／validity／dedup；
- runner subprocess／benchmark reconciliation；
- protocol validator與lock writer；
- artifact checksum／exclusive finalize。

正式實作可重用legacy M00概念，但須新namespace／schema version與新lock。

## 9. Acceptance evidence binding

唯一 scientific criterion：`S00_EVIDENCE_READY`。

Milestone report須逐項綁定：

- neutrality；
- resume parity；
- reconciliation；
- lineage fail-closed；
- parent／input hash enforcement。

本檔不得自行改寫criterion語意。

## 10. Stop／degrade／failure

- Neutrality fail：negative，阻擋S10 formal exit與全部後續。
- Resume fail但continuous可用：S00仍negative；可提出continuous-only amendment，需重新review。
- 只有非必要report renderer fail：inconclusive／blocked，不能假裝foundation ready。
- Legacy prototype tests存在但未跑：not_evaluated。

## 11. Risks 與 diagnostics

- Python multiprocessing／xdist改變seed sequence；
- set ordering被誤當lineage；
- checkpoint漏存adaptive population／decay；
- untracked source無穩定revision；
- report finalize過早，後續milestone無法引用。

每個failure須保存最小reproducer與first divergent event。

## 12. Planned report、decision 與 handoff

Report：`../../reports/staged/s00-foundation-verification-report.md`

Terminal report必含：

- criterion結果；
- source／parent hashes；
- first divergence或PASS evidence；
- artifacts；
- 能／不能支持的結論；
- 是否授權S10 formal decision與S11。

## 13. Lock checklist

- [ ] Parent hashes填入
- [ ] Contract／event／lineage schema版本固定
- [ ] Test fixtures與seeds固定
- [ ] Continuous/resume comparison規則固定
- [ ] Canonical population hash規則固定
- [ ] Planned artifact paths固定
- [ ] Design approved
- [ ] Lock artifact建立
