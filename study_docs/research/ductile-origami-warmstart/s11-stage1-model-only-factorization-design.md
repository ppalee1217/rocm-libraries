---
checkpoint_id: S11
title: Stage 1 model-only factorization 與 guidance lock
stage: 1
design_status: approved
execution_status: gated
checkpoint_state: DESIGN_APPROVED
scientific_outcome: not_activated
lock_state: absent
risk_tier: R2
governance_baseline: b0561d2c9216a58a9d71b8e839c47efaa51f9c00
scientific_gate: S11
execution_tranche: T-S1-MECHANISM
closure_unit: CU-S1-MECHANISM
hypothesis_id: S11-H1
dependencies:
  - checkpoint_id: S10R2
    required_edge: S1_ENTRY_GO
entry_criteria:
  - S00_EVIDENCE_READY
  - post_audited_S10R2_S1_ENTRY_GO
criterion_refs:
  - S1_GUIDANCE_LOCKED
failure_ids:
  - FT-BLOCKED-MAPPING
  - FT-INCONCLUSIVE
allowed_outgoing_edges:
  - criterion_id: S1_GUIDANCE_LOCKED
    target_checkpoint: S12
formal_report_path: reports/staged/s11-stage1-model-only-factorization-report.md
compact_positive_gate_record_path: protocol/v1/evidence/gate-records/s11-s1-guidance-locked.json
tranche_final_report_path: reports/gen0-factorization-mvp-report.md
terminal_report_integration: terminal_here_on_negative_or_inconclusive_else_integrated_by_S13
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
  - README.md
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

**S11-H1：**在S10R2以相同actual YAML／source pins重新鎖定的Ductile-valid
space中，Formocast能對至少一個eligible residual gene產生符合parent model-only
criteria的穩定prior，並可無損轉成與`SearchSpace.map`完全對齊的weights與shuffled
control。

反證或inconclusive：

- 無eligible／guidable residual gene，或global lambda退化；
- mapping、coverage、support、sensitivity或stability未過；
- occurrence multiplicity在dedup後遺失；
- probability／cost round-trip、candidate order或weight sign錯誤；
- existing group／weight被修改；
- 任何real score、oracle output或outcome-derived feature參與gene／weight選擇。

## 3. Dependencies、entry 與 outgoing edge

S11需要S00 foundation、immutable S10 terminal provenance、S10R1的A32
`cancelled / not_evaluated / edge=null` record，以及S10R2的positive formal
closeout／isolated commit／post-commit audit。S10與S10R1都沒有outgoing edge；
只有post-audited `S10R2:S1_ENTRY_GO`能啟動S11。S10R2 negative／inconclusive／
`CHANGES_REQUIRED`或未完成都保持S11`not_activated`，且本dependency amendment
沒有proxy／reduced-mode edge。S10R1任何generation、test、cache或evidence都禁止
重用。

唯一outgoing edge：

```text
S1_GUIDANCE_LOCKED -> S12
```

無guidable gene、mapping failure、label leakage或model-only stability不足都不會解鎖S12。

### 3.1 Gate／tranche／closure governance

- `risk_tier=R2`、`scientific_gate=S11`、
  `execution_tranche=T-S1-MECHANISM`、`closure_unit=CU-S1-MECHANISM`。
- 執行前依`b0561d2c9216a58a9d71b8e839c47efaa51f9c00`重做cumulative resource
  preflight，先seal durable machine-readable contract與effective lock；S10R2／S11
  的wall-time、CPU/GPU、storage、throughput、repair與thread消耗不能由new
  generation／successor／root歸零。
- Positive只seal compact durable gate record
  `protocol/v1/evidence/gate-records/s11-s1-guidance-locked.json`並在verified frozen
  edge後留在同一tranche進S12；此時closure unit尚未`COMPLETE`。
- Negative／inconclusive是本tranche的terminal internal gate，立即產生本design的
  planned terminal report並停止後續；`CHANGES_REQUIRED`只在frozen repair budget內
  修復，不是scientific outcome。
- 若走到S13，最終`reports/gen0-factorization-mvp-report.md`必須整合S11 compact
  record與後續gate records；`live_run_state`與`committed_projection_state`分開，
  後者只在CU-S1 closure commit與post-commit audit後更新。

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

它綁定S10 immutable terminal provenance、S10R1 A32 cancellation、S10R2 positive
closure、frozen YAML／space／groups／weights／sizes／support-aware valid mapping、study mode、
Formocast／validity revisions、parent constants、randomness bundles、
label-seal evidence、Plan-B、exact whitelists與report target。S10R2的
ten-config corpus只作mapping／conformance fixture；S11仍須建立自己的
multiplicity-preserving occurrence frame。

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
| Mapping缺陷來自S10R2 authority | 停止並記failure；不得猜值 | 無 |
| Label leakage | evidence invalid；新lock／fresh pool後全量重跑 | 無 |
| Proxy scope需要再縮減 | `blocked-awaiting-user-decision` | 無 |

## 8. Formal report 與 closeout

S11 positive使用compact gate record
`protocol/v1/evidence/gate-records/s11-s1-guidance-locked.json`並繼續同tranche。
S11若negative／inconclusive而成為terminal，唯一formal report才是
`reports/staged/s11-stage1-model-only-factorization-report.md`；它需自含label-seal
證據、所有criteria、failure localization、artifacts、iteration history、先前gate
record與claim boundary。若S13成為tranche final，S13 report整合本record，不另製造
重複的S11 positive report。

## 9. Design-consensus record

- Reviewer A objection：只說「model-only」不足以防止D5 pool或real labels透過cache／artifact root影響gene selection。
- Reviewer B objection：把existing groups拆成independent genes或在shuffle後只比較nominal entropy，會改變protected baseline或掩蓋validity效應。
- 採納方案：explicit label-seal、root-level forbidden evidence、multiplicity-preserving occurrence frame、existing-group immutability、nominal shuffle加realized diagnostics。
- 捨棄方案：從real GFLOPS挑genes、按D5結果重調lambda、拆group或改weights；理由是它們造成leakage並改變研究問題。
- Shared resolution：S11只能交付immutable model-only guidance；任何negative仍正式closeout但不建立下游Stage 1 outcome。
- Reviewer A final：`AGREE`
- Reviewer B final：`AGREE`

### 2026-07-26 R12 dependency amendment

- S10已durable closeout為negative且沒有outgoing edge；不得由S11把它重解讀為GO。
- 兩位fresh recovery reviewers同意新增獨立S10R1，保持S10 immutable，並把
  validity、Formocast model sentinel與runtime queue semantics分離。
- 當時R12曾把S11 dependency指向S10R1；該historical authority已被下列A32
  amendment取消，沒有形成edge。S11的occurrence counts、model-only criteria、
  weights、shuffle、label seal與claim全部不變。
- Reviewer A final：`AGREE`。
- Reviewer B final：`AGREE`。
- 使用者已委派`/data1/perlee`內的此類block由design-discussion共識決定；
  amendment不授權push或任何downgrade。

### 2026-07-28 A32／S10R2 dependency amendment

- User-authorized A32在safe boundary取消S10R1：operational `cancelled / BLOCKED`、
  scientific `not_evaluated`、`edge=null`，沒有scientific report且不是
  `CHECKPOINT_COMPLETE`。
- S10R1 generations只作diagnostic provenance並禁止re-use；S11 dependency改為唯一
  post-audited `S10R2:S1_ENTRY_GO`。
- S11 hypothesis、4,096／8,192 occurrences、128／256 conditional support、
  thresholds、weights、shuffle、label seal、claim與timebox均不變。
