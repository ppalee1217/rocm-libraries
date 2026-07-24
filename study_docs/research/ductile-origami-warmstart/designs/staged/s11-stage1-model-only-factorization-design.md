---
milestone_id: S11
title: Stage 1 model-only factorization 與 guidance lock
stage: 1
lifecycle: active
design_status: draft
execution_status: gated
outcome: not_evaluated
decision: pending
hypothesis_id: S11-H1
depends_on:
  - S00:S00_EVIDENCE_READY
  - S10:S1_ENTRY_GO_or_S1_ENTRY_DEGRADED_PROXY
entry_gate_ids: [S00_EVIDENCE_READY, S1_ENTRY_GO, S1_ENTRY_DEGRADED_PROXY]
criterion_refs: [S1_GUIDANCE_LOCKED]
failure_taxonomy_refs: [FT-BLOCKED-MAPPING, FT-INCONCLUSIVE]
planned_report_paths:
  - ../../reports/staged/s11-stage1-model-only-factorization-report.md
contributes_to_stage_report: ../../reports/gen0-factorization-mvp-report.md
authority:
  charter: ../../../surrogate-dse-plan.md
  protocol: ../../../ductile-origami-warmstart-experiment-plan.md
  charter_hash: pending
  protocol_hash: pending
lock:
  approved_at: null
  locked_at: null
  lock_sha256: null
supersedes: [M02-concepts-only]
---

# S11 — Stage 1 model-only factorization／guidance lock

導航：[design index](../README.md)

## 1. Authority 與 change budget

本檔只負責把 parent §3–§5 轉成可交接的 model-only pipeline與label-seal evidence。

禁止：

- 讀取 real GFLOPS選genes／weights；
- 修改existing groups／weights；
- 加入Injection A／widening；
- 自訂parent以外的sensitivity／entropy門檻。

## 2. 白話目標

在完全不看真實效能下，產生可重現、candidate-order正確、model-only穩定的Formocast residual guidance與same-entropy shuffled control，然後鎖死。

## 3. Hypothesis 與 falsification

**S11-H1：**在S10鎖定的residual space中，Formocast可對至少一個eligible residual gene產生通過parent model-sensitive criteria的穩定prior，且hook round-trip與candidate order完全一致。

反證：

- 無eligible／guidable residual genes；
- mapping／coverage／support／stability未過；
- global lambda退化；
- probability／cost round-trip失真；
- label leakage；
- existing group或weight被改動。

## 4. 能與不能說明

能：

- model-only frame與conditional marginals可建立；
- gene selection、weights與shuffle可鎖定；
- plumbing在real labels前自洽。

不能：

- Formocast ranking符合真實GFLOPS；
- factorized prior真的對準高品質區；
- actual Gen0改善。

## 5. Inputs

- S00 evidence interface與schemas；
- S10 frozen YAML、space、groups、weights、sizes、mapping與study mode；
- pinned Formocast／validity／sampler；
- sealed-label attestation；
- parent model-only constants與criterion refs。

## 6. Outputs／artifacts

- valid occurrence frame
- deduplicated resolved catalog與multiplicity
- Formocast scores／coverage／ties
- conditional top-ups
- model-sensitive gene decisions
- marginals
- Formocast residual weights
- shuffled permutation manifest
- probability round-trip results
- candidate-order parity
- guidance lock／hash
- `s11-decision.json`

## 7. Controls／measurement boundary

- `pi_nominal`、`pi_valid`與operational sampler不可混用；
- duplicate multiplicity保存；
- top-up只進對應conditional cell；
- existing groups完全保護；
- shuffle保留nominal probability multiset；
- model-only bootstrap／permutation使用prelocked randomness；
- real-score artifact不存在或保持sealed。

## 8. Implementation points

- valid occurrence collector；
- canonical config hashing／dedup；
- batch Formocast scorer；
- conditional top-up generator；
- marginal／shrinkage／lambda builder；
- hook cost converter；
- search-space／weights alignment validator；
- seal／lock writer。

## 9. Acceptance evidence

唯一go criterion：`S1_GUIDANCE_LOCKED`。

Milestone evidence須綁定：

- eligible／guided gene list；
- model-only criteria結果；
- coverage／support；
- weights／shuffle hashes；
- round-trip／order tests；
- no-leakage attestation。

## 10. Stop／degrade／failure

- 無guidable gene或lambda退化：negative，Stage 1終止並finalize reports。
- Support／stability不足：negative或inconclusive，依parent taxonomy。
- Mapping coverage問題：回S10 blocker，不得自行補值。
- Leakage：結果無效，須新protocol version與重新封存。
- Proxy模式：所有artifacts／claims保留proxy標記。

## 11. Risks／diagnostics

- multiplicity在dedup後遺失；
- benefit方向或weight符號反轉；
- candidate order silent mismatch；
- conditional top-up污染global frame；
- model score ties被誤認sensitivity；
- shuffled在validity後與treatment realized entropy差異過大。

## 12. Planned report／handoff

Milestone report：`../../reports/staged/s11-stage1-model-only-factorization-report.md`

若S11 terminal，另finalize Stage 1 rollup：

`../../reports/gen0-factorization-mvp-report.md`

通過後交付S12：

- immutable guidance lock；
- finite catalog與multiplicity；
- planned D5 frame inputs；
- sealed real-label state。

## 13. Lock checklist

- [ ] Parent hashes與criteria固定
- [ ] Inputs／seeds／caps固定
- [ ] Existing groups保護規則確認
- [ ] Real labels sealed
- [ ] Gene decision algorithm固定
- [ ] Weight／shuffle／round-trip schema固定
- [ ] Planned artifacts與reports固定
- [ ] Design approved／locked
