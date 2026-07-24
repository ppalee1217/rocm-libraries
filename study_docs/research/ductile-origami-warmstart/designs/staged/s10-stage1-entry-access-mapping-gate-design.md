---
milestone_id: S10
title: Stage 1 access、artifact、mapping 與 noise entry gate
stage: 1
lifecycle: active
design_status: draft
execution_status: not_started
outcome: not_evaluated
decision: pending
hypothesis_id: S10-H1
depends_on:
  - S00:S00_EVIDENCE_READY
entry_gate_ids: []
criterion_refs: [S1_ENTRY_GO, S1_ENTRY_DEGRADED_PROXY, S1_ENTRY_BLOCKED]
failure_taxonomy_refs: [FT-BLOCKED-ACCESS, FT-BLOCKED-MAPPING, FT-INCONCLUSIVE]
planned_report_paths:
  - ../../reports/staged/s10-stage1-entry-gate-report.md
blocked_memo_paths:
  - ../../reports/gen0-factorization-blocker-memo.md
authority:
  charter: ../../../surrogate-dse-plan.md
  protocol: ../../../ductile-origami-warmstart-experiment-plan.md
  charter_hash: pending
  protocol_hash: pending
lock:
  approved_at: null
  locked_at: null
  lock_sha256: null
supersedes: [M01-concepts-only]
---

# S10 — Stage 1 entry access／artifact／mapping／noise gate

導航：[design index](../README.md)

## 1. Authority 與 change budget

本檔實作 parent Stage 1 D1–D2 entry gate。Exact checks、study modes與stop rules由experiment plan §2定義。

允許：

- environment／YAML discovery；
- canonical mapping adapter與parity harness；
- size registry、noise pilot與study-mode decision。

禁止：

- 猜 required metadata；
- 修改search space或weights；
- 在entry lock前產生treatment judgment labels；
- 宣稱proxy為production baseline。

## 2. 白話目標

確認研究對象真的存在：有可信 YAML、可用gfx942、可解析Formocast metadata、可控制noise，並能誠實判定 actual-guidance、proxy或blocked模式。

## 3. Hypothesis 與 falsification

**S10-H1：**可在不猜值的前提下鎖定一份有provenance的generated YAML、可執行gfx942環境、canonical mapping、same-space sizes與noise protocol。

反證／阻擋：

- YAML來源或candidate order不可驗；
- mapping只能用default／猜值補occupancy、effective GSU、math clocks或sentinel；
- gfx942 slot未確認或smoke失敗；
- noise在parent cap內不可控；
- actual／proxy space parity不可證。

## 4. 能與不能說明

能：

- Stage 1是否可合法開始；
- study mode與claim降級；
- mapping／noise是否足以支撐後續。

不能：

- Formocast有ranking訊號；
- factorization或Gen0有效；
- owner已部署GEKO weights。

## 5. Inputs／dependencies

Discovery可與S00實作並行；formal decision需要：

- `S00_EVIDENCE_READY`；
- parent／source hashes；
- candidate YAML／generator provenance；
- GPU reservation evidence；
- mapping code與10-config selection rule。

## 6. Outputs／artifacts

- frozen YAML／SHA／provenance
- environment／revision manifest
- search-space／group／weights manifest
- size registry
- canonical mapping-10 corpus
- mapping parity／round-trip results
- smoke／correctness results
- noise pilot與`delta_noise`
- study-mode decision
- `s10-decision.json`

## 7. Controls 與 boundary

- actual YAML vs branch proxy差異逐欄比較；
- same config／size mapping determinism；
- sentinel／boundary／rejection cases；
- three-anchor repeated noise measurement；
- treatment labels在S11 lock前保持sealed。

GPU access discovery不等於正式實驗執行。

## 8. Implementation points

- YAML parser／manifest generator；
- `ContractionSolution::getSizeMapping()` canonical path；
- effective GSU與Formocast input adapter；
- gfx942 runner／environment capture；
- correctness與noise harness；
- study-mode state machine。

## 9. Acceptance IDs

- `S1_ENTRY_GO`
- `S1_ENTRY_DEGRADED_PROXY`
- `S1_ENTRY_BLOCKED`

Report只綁定parent IDs與artifact hashes，不複製門檻。

## 10. Stop／degrade

- Actual guidance可追溯：GO。
- Actual無weights但exact-space branch proxy成立：DEGRADED_PROXY。
- 無GPU／YAML／mapping：BLOCKED。
- Noise或coverage不足但非明確反證：INCONCLUSIVE／blocked，依parent判讀。

Blocked時不得建立假裝執行過的Stage 1 MVP report。

## 11. Risks／diagnostics

- YAML手工修改未留下provenance；
- fixed MT與MTDU混淆；
- candidate order漂移；
- Formocast mapping對部分values silent fallback；
- GPU shared load／clock drift；
- proxy同時改space與weights。

所有差異保存field-level audit與first failure。

## 12. Planned report／handoff

Milestone report：`../../reports/staged/s10-stage1-entry-gate-report.md`

Access／artifact／mapping blocked memo：`../../reports/gen0-factorization-blocker-memo.md`

GO／DEGRADED後交付S11：

- frozen inputs；
- study mode；
- mapping／coverage boundaries；
- sealed-label attestation；
- parent／lock hashes。

## 13. Lock checklist

- [ ] S00 criterion已綁定
- [ ] YAML／revision／environment paths固定
- [ ] 10-config selection rule固定
- [ ] Size selection rule固定
- [ ] Noise／correctness protocol引用固定
- [ ] Study-mode transition固定
- [ ] Treatment labels sealed
- [ ] Design approved／locked
