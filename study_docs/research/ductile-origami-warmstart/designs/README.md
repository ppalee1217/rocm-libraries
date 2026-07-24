# Ductile Factorized Guidance — Design Index

> **Active authority：**新 milestone designs 只在 [`staged/`](staged/)。
>
> **Legacy warning：**本目錄根層的 M00–M09 是 pre-pivot 歷史設計，全部 `do_not_execute`。它們不再定義任何 active criterion、dependency 或 report。
>
> **Parent authorities：**
> - Scope／claim／failure taxonomy：[research charter](../../surrogate-dse-plan.md)
> - 數值 protocol／criteria／milestone index：[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)

## 1. Authority order

1. Research charter
2. Experiment plan
3. Milestone design
4. Frozen lock artifact
5. Milestone／stage report

Milestone design只負責 implementation handoff、artifact checklist與 evidence binding；不得複製或改寫 parent的公式、門檻、samples、seeds或 claim。

## 2. Active／planned staged milestones

### Created now

- [S00 — Evidence contract、lineage、observability foundation](staged/s00-evidence-contract-lineage-observability-design.md)
- [S10 — Stage 1 entry access／artifact／mapping／noise](staged/s10-stage1-entry-access-mapping-gate-design.md)
- [S11 — Stage 1 model-only factorization／guidance lock](staged/s11-stage1-model-only-factorization-design.md)
- [S12 — Stage 1 real-score ranking／prior-mass／oracle audit](staged/s12-stage1-real-score-ranking-oracle-audit-design.md)
- [S13 — Stage 1 actual Gen0 mechanism](staged/s13-stage1-actual-gen0-mechanism-design.md)
- [S40 — Stage 4 surrogate activation／data-sufficiency contract](staged/s40-stage4-surrogate-activation-gate-design.md)

### Planned, not created

- `S20` — `staged/s20-stage2-h10-persistence-design.md`
  - Draft near S13 decision；only approve after `D6_MECHANISM_POSITIVE`。
- `S30` — `staged/s30-stage3-heldout-registry-freeze-design.md`
  - Create after `S2_DIRECTIONAL_PERSISTENCE_POSITIVE`。
- `S31` — `staged/s31-stage3-bounded-replication-design.md`
  - Create with S30 architecture；lock only after S30 registry／freeze。
- `S41` — `staged/s41-stage4-learned-residual-analysis-design.md`
  - Create only after `S4_ACTIVATE`。

`planned_not_created` 是 parent slot狀態，不是 design lifecycle。不存在的檔案不得被描述為 draft、approved或locked。

## 3. Dependency summary

```text
S00 + S10 → S11 → S12 → S13 → S20 → S30 → S31
                      ↘                 ↘
                       S40 ────────────→ S41
```

- S00 foundation實作與 S10 access／YAML discovery可並行。
- S10 formal exit需要 S00 evidence interface。
- S11後主線為 serial gates。
- S40只接受 parent明列的 predictor-specific／oracle-positive trigger。

## 4. Lifecycle

### `design_status`

- `draft`
- `approved`
- `locked`
- `superseded`

### `execution_status`

- `not_started`
- `gated`
- `ready`
- `running`
- `blocked`
- `completed`
- `cancelled`

### `outcome`

- `not_evaluated`
- `positive`
- `negative`
- `inconclusive`
- `blocked`
- `not_activated`
- `superseded`

只有 `design_status=locked` 且 `execution_status=ready` 可以開始產生 outcome-bearing evidence。`approved` 不等於 approved-for-execution。

## 5. Report policy

每個實際執行並terminal的 milestone都需要：

1. machine-readable decision artifact；
2. 對應 Markdown evidence report。

Evidence report只記：

- parent／milestone／lock hashes；
- hypothesis與criterion IDs；
- criterion結果；
- artifact URI／hash；
- deviation與root cause；
- outcome／decision／failure ID；
- 能與不能宣稱什麼；
- next gate或stop。

不得重抄 parent protocol。

### Planned reports

- S00：`../reports/staged/s00-foundation-verification-report.md`
- S10：`../reports/staged/s10-stage1-entry-gate-report.md`
- S11：`../reports/staged/s11-stage1-model-only-factorization-report.md`
- S12：`../reports/staged/s12-stage1-real-score-audit-report.md`
- S13／Stage 1 rollup：`../reports/gen0-factorization-mvp-report.md`
- S20／Stage 2：`../reports/short-horizon-persistence-report.md`
- S30：`../reports/staged/s30-heldout-registry-freeze-report.md`
- S31／Stage 3：`../reports/bounded-regime-replication-report.md`
- S40：`../reports/staged/s40-stage4-activation-report.md`
- S41／Stage 4：`../reports/learned-residual-surrogate-report.md`

Blocked／data-insufficient memos依 parent protocol建立；尚未執行不建空白 report。

## 6. Legacy migration map

| Legacy | Active destination | Migrated concepts | Explicitly retired |
| --- | --- | --- | --- |
| M00 | S00 | non-perturbing observer、lineage、reconciliation | 舊 M00 criteria／lock authority |
| M01 | S10 | access、YAML、mapping、noise | StreamK、舊 baseline／revision假設 |
| M02 | S11 | sample-ID、mapping、round-trip、no-leakage | Injection A、widening、舊 speed route |
| M03 | retired | — | cold-headroom／30→90 generation thesis |
| M04 | retired | — | widen-only |
| M05 | S12 | ranking、oracle failure localization | StreamK／Origami treatment、舊 sampling |
| M06 | S13；部分概念供 S20 | shuffled、initial-weight boundary、telemetry | 舊 speedup／basin／調參 claim |
| M07 | retired | — | A-safe+B factorial |
| M08 | S30／S31 | freeze、held-out hygiene | winner selection、15/100 sizes workflow |
| M09 | S30／S31 | denominator、negative reporting、holdout discipline | 24-shape／production confirmation |

Migration不代表 legacy milestone完成，也不代表舊 artifacts可直接改名成新 evidence。

## 7. Legacy files

- [M00](m00-study-contract-observability-design.md)
- [M01](m01-step0-integration-gate-design.md)
- [M02](m02-guidance-plumbing-design.md)
- [M03](m03-exp0a-cold-headroom-design.md)
- [M04](m04-exp0b-widening-gate-design.md)
- [M05](m05-expc-ranking-oracle-design.md)
- [M06](m06-exp1-injection-b-design.md)
- [M07](m07-exp2-a-safe-b-factorial-design.md)
- [M08](m08-exp3-multishape-design.md)
- [M09](m09-overall-confirmation-design.md)

這些檔案只供歷史追溯。任何執行者若從 legacy URL進入，必須回到本 README與 parent index取得 active design。
