---
checkpoint_id: S11
title: Stage 1 model-only factorization 與 guidance lock
stage: 1
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_evaluated
lock_state: absent
hypothesis_id: S11-H1
dependencies:
  - checkpoint_id: S10
    required_edge: S1_ENTRY_GO_or_user_approved_S1_ENTRY_DEGRADED_PROXY
entry_criteria:
  - S00_EVIDENCE_READY
  - S1_ENTRY_GO_or_user_approved_S1_ENTRY_DEGRADED_PROXY
criterion_refs:
  - S1_GUIDANCE_LOCKED
failure_ids:
  - FT-BLOCKED-MAPPING
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S1_GUIDANCE_LOCKED
    target_checkpoint: S12
formal_report_path: reports/staged/s11-stage1-model-only-factorization-report.md
blocker_path: null
future_effective_lock_path: protocol/v1/locks/s11-stage1-model-only-factorization-lock.json
implementation_boundary_max:
  - model-only occurrence, catalog, scoring, factorization, weight, shuffle and guidance-lock pipeline
  - protocol/v1 schemas and lock entries required only by S11
delivery_boundary_max:
  - S11 implementation and tests selected by future exact-path planning
  - protocol/v1/**
  - reports/staged/s11-stage1-model-only-factorization-report.md
  - ../ductile-origami-warmstart-experiment-plan.md
  - s11-stage1-model-only-factorization-design.md
forbidden_downstream_roots:
  - reports/staged/s12-stage1-real-score-audit-report.md
  - reports/gen0-factorization-mvp-report.md
  - reports/short-horizon-persistence-report.md
  - reports/bounded-regime-replication-report.md
  - reports/staged/s40-stage4-activation-report.md
  - reports/learned-residual-surrogate-report.md
consensus_status: approved_two_reviewer_agree
---

# S11 — Stage 1 model-only factorization／guidance lock

導航：[active checkpoint index](README.md)｜[experiment plan §§3–5](../ductile-origami-warmstart-experiment-plan.md#3-三種分布與分析單位)

## 1. 白話目標

在完全label-blind的條件下，建立accepted-occurrence frame、deduplicated catalog、Formocast scores、residual-gene factorization、weights與same-entropy shuffle，通過candidate-order／probability round-trip後鎖死。這一步只建立guidance，不能偷看real GFLOPS。

## 2. Hypothesis 與 falsification

**S11-H1：**在S10鎖定的space中，Formocast能對至少一個eligible residual gene產生符合parent model-only criteria的穩定prior，並可無損轉成與`SearchSpace.map`完全對齊的weights與shuffled control。

反證或inconclusive：

- 無eligible／guidable residual gene，或global lambda退化；
- mapping、coverage、support、sensitivity或stability未過；
- occurrence multiplicity在dedup後遺失；
- probability／cost round-trip、candidate order或weight sign錯誤；
- existing group／weight被修改；
- 任何real score、oracle output或outcome-derived feature參與gene／weight選擇。

## 3. Dependencies、entry 與 outgoing edge

S11需要S00 foundation與S10 formal closeout。若S10是`S1_ENTRY_DEGRADED_PROXY`，還必須綁定user批准的decision packet。

唯一outgoing edge：

```text
S1_GUIDANCE_LOCKED -> S12
```

無guidable gene、mapping failure、label leakage或model-only stability不足都不會解鎖S12。

## 4. Maximum implementation 與 delivery boundary

允許：

- `pi_nominal`／`pi_valid` occurrence collection與multiplicity-preserving catalog；
- canonical config resolution、Formocast scoring與coverage/tie audit；
- conditional top-up、shrinkage marginals、gene decisions與global lambda；
- probability→hook-cost conversion、candidate-order parity與round-trip tests；
- same-entropy non-identity shuffle；
- guidance lock與sealed-label attestation。

禁止：

- 讀取或產生real GFLOPS、D5 judgments或oracle outputs；
- 修改existing groups／weights、candidate space或size registry；
- 加入Injection A、widening或parent未指定threshold；
- 建立S12+ evidence/report；
- 使用M02 pipeline、fixture或hash作相容性/PASS target。

Future plans必須將boundary縮成exact paths/symbols；S11 closeout不得包含下游implementation。

## 5. Future effective lock、inputs 與 outputs

Future lock：

`protocol/v1/locks/s11-stage1-model-only-factorization-lock.json`

它綁定S10 closure、frozen YAML/space/groups/weights/sizes/mapping、study mode、Formocast/validity revisions、parent constants、randomness bundles、label-seal evidence、Plan-B、exact whitelists與report target。

Outputs至少包括：

- valid occurrence frame與deduplicated catalog/multiplicity；
- model scores、coverage、ties與conditional top-ups；
- eligible/guided gene decision與marginals；
- Formocast residual weights；
- shuffle manifest；
- probability round-trip與candidate-order results；
- immutable guidance bundle與machine decision。

## 6. Controls 與 measurement boundary

- `pi_nominal`、`pi_valid`與operational Gen0 sampler明確分離；
- duplicate occurrences保留；
- conditional top-up只進對應cell；
- existing groups／weightsbyte-level或canonical parity；
- shuffle保留每gene probability multiset與nominal entropy；
- bootstrap／permutation使用prelocked model-only randomness；
- real-label root不存在或由S00 seal證明不可讀。

S11能說明model-only factorization是否可建立，不能說明real ranking、prior mass或actual Gen0效果。

## 7. Acceptance binding 與 stop matrix

唯一positive criterion是parent的`S1_GUIDANCE_LOCKED`。Formal evidence須綁定guided genes、model-only criteria、coverage/support、weights/shuffle hashes、round-trip/order tests與no-leakage attestation。

| 狀況 | checkpoint處理 | downstream |
| --- | --- | --- |
| Guidance完整且label-blind鎖定 | positive closeout | S12 |
| 無guidable gene／lambda退化 | negative formal closeout | 無 |
| Support／stability不足 | negative或inconclusive formal closeout | 無 |
| Mapping缺陷來自S10 authority | 停止並記failure；不得猜值 | 無 |
| Label leakage | evidence invalid；新lock／fresh pool後全量重跑 | 無 |
| Proxy scope需要再縮減 | `blocked-awaiting-user-decision` | 無 |

## 8. Formal report 與 closeout

唯一formal report：

`reports/staged/s11-stage1-model-only-factorization-report.md`

S11若terminal，不製造S13的Stage 1 rollup。Report需自含label-seal證據、所有criteria、failure localization、artifacts、iteration history與claim boundary；closeout流程依README。

## 9. Design-consensus record

- Reviewer A objection：只說「model-only」不足以防止D5 pool或real labels透過cache／artifact root影響gene selection。
- Reviewer B objection：把existing groups拆成independent genes或在shuffle後只比較nominal entropy，會改變protected baseline或掩蓋validity效應。
- 採納方案：explicit label-seal、root-level forbidden evidence、multiplicity-preserving occurrence frame、existing-group immutability、nominal shuffle加realized diagnostics。
- 捨棄方案：從real GFLOPS挑genes、按D5結果重調lambda、拆group或改weights；理由是它們造成leakage並改變研究問題。
- Shared resolution：S11只能交付immutable model-only guidance；任何negative仍正式closeout但不建立下游Stage 1 outcome。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`
