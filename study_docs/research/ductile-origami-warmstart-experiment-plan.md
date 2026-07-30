# gfx942 Non-StreamK Factorized Guidance — Stage-Gated Experiment Plan

> **文件角色：**pre-registered experiment plan。所有公式、常數、sample counts、seeds、artifacts、Stage 1–4 schedule與stop rules以本檔為唯一數值權威。
>
> **研究 scope／claim authority：**[Formocast Factorized Gen0 Guidance Feasibility Study — Research Charter](surrogate-dse-plan.md)。
>
> **狀態：**`pre_empirical / s10r3_design_approved`。S00是durable
> positive；S10是durable `negative / S1_ENTRY_BLOCKED / edge=null`，兩者不變。
> User-authorized A32已在safe boundary取消S10R1：operational
> `cancelled / BLOCKED`、scientific `not_evaluated`、`edge=null`，沒有scientific
> report且不是`CHECKPOINT_COMPLETE`；generation 0／1只作diagnostic lineage並
> 禁止重用。A33另授權identity-only retirement；bulk artifacts不再保留。
> 新的sibling S10R2已由fresh verifier technical `PASS`，scientific outcome為
> `inconclusive / FT-INCONCLUSIVE / edge=null`；本次closure commit與post-audit後
> projection為`CHECKPOINT_COMPLETE`。A33 retirement已完成，
> A34已核准prospective calibration boundary；A35另將R2 repair round上限由3提高為6，
> 已消耗rounds完整carry over且不改scientific criteria。A36再明定不影響workload、
> stopping、evidence integrity或scientific result的resource-accounting缺口只作
> non-blocking caveat，不要求resource-only rerun；A37 further supersedes internal
> resource target與cumulative ledger作blanket hard gate的舊文字，改為
> record＋notify＋continue，只有material safety／availability／completion／evidence
> boundary才暫停。A38新增R3 sibling S10R3；S10R2保持immutable inconclusive/null。
> A44再將所有prospective R0–R3 repair cap統一為6 rounds，既有消耗完整carry over；
> experiment-design議題經兩個獨立reviewers交互詰問後仍須使用者決定，非設計阻塞的
> contract-preserving共識則已預授權直接執行。A45再以clean execution baseline及
> 雙seal lifecycle對齊current `.agents` workflow；S10R3保持
> `not_evaluated / edge=null`，threads `9/9`，scientific plan不變。A46再取消numeric
> repair stop cap：repair cycle只作append-only provenance，由reviewer支持的
> plan-preserving修復可直接進行。
> 只有post-audited `S10R3:S1_ENTRY_GO`可啟動S11。
>
> **Foundation provenance：**active `protocol/v1/`與S00 report是fresh foundation；退役M00內容仍不得作schema、hash、lock、registry、fixture、test或PASS evidence。S00只支持CPU-only evidence semantics，不是GPU／performance結果。
>
> **GEKO／Ductile source topology（默認前提）：**兩套codebase仍以不同branch作source authority，尚未假設已整合進目前checkout。Ductile為`refs/remotes/origin/ductile_integration`（目前已知pin `5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39`）；GEKO為`refs/remotes/origin/users/pkamd/geko_pr`（目前已知pin `d32abacfd13579d1f523f035b7a10b0734c4ac47`）。任何checkpoint若同時使用兩者，必須各自重新resolve並鎖定兩個exact commits，再記錄實際integration commit／patch／worktree／archive identity；不得從GEKO branch中附帶的Ductile files反推Ductile revision，也不得把current checkout、cache、build或container內容當成任一source authority。
>
> **S00雙視圖邊界：**`protocol/v1/README.md`是immutable execution-authority
> view（E）runbook；E由baseline commit
> `60775f12843bee9f95cb0bef4e91de8bc4dc9dc3`、exact 29 implementation blobs與
> exact兩份Plan-B bytes重建，且本plan、active README、S00 design在E中使用
> baseline bytes。本頁是post-PASS closeout-projection view（C）的三份投影之一；
> C中直接重跑historical outcome writer會按設計在寫入前
> `bound_hash_mismatch`，不得把它當成E runbook。Exact重建、預期拒絕與
> E→C hashes見[S00 formal report](ductile-origami-warmstart/reports/staged/s00-foundation-verification-report.md)。
> 重建依賴baseline Git object與兩份exact ignored Plan-B；不宣稱standalone
> source-tarball portability。
>
> **平台：**gfx942／MI300X、non-StreamK、單一dtype/layout。檔名中的`origami-warmstart`為歷史名稱；primary model是Formocast，Origami estimation只作reference。Stage 1是七日Gen0 gate；只有通過後才依序進Stage 2 persistence與Stage 3 bounded replication，Stage 4 surrogate是嚴格條件分支。

---

## Checkpoint authority、index 與 lifecycle

> 唯一active導航與legacy archive入口：[checkpoint index](ductile-origami-warmstart/README.md)。

### Authority order

1. Research charter：scope、claim ladder、non-goals、canonical failure taxonomy。
2. 本experiment plan：scientific criterion IDs、公式、數值、samples、seeds、go/stop與checkpoint DAG。
3. Checkpoint design：implementation handoff、maximum boundary、artifact/evidence binding。
4. Durable machine-readable frozen contract與effective lock：在evidence前把criteria、
   outcome matrix、resources、committed authorities、Plan-B、exact whitelists、
   inputs、fixtures與seeds綁成不可變執行實例。
5. Compact positive gate record或terminal formal report：記錄verified evidence、
   outcome、edge與closeout，不得反向修改criterion。

Execution governance commit
`b0561d2c9216a58a9d71b8e839c47efaa51f9c00`是所有future work的mandatory
orchestration／resource floor；它不能靜默修改上列scientific authority。

### Canonical checkpoint index

| ID | Responsibility | Design | Execution | Checkpoint | Scientific outcome | Lock | Design | Formal report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S00 | Evidence contract／lineage／observability foundation | approved | completed | CHECKPOINT_COMPLETE | positive | effective (`successor-001`) | [design](ductile-origami-warmstart/s00-evidence-contract-lineage-observability-design.md) | [report](ductile-origami-warmstart/reports/staged/s00-foundation-verification-report.md) |
| S10 | Stage 1 access／artifact／mapping／noise gate | approved | completed | CHECKPOINT_COMPLETE | negative | effective (`successor-003`) | [design](ductile-origami-warmstart/s10-stage1-entry-access-mapping-gate-design.md) | [report](ductile-origami-warmstart/reports/staged/s10-stage1-entry-gate-report.md) |
| S10R1 | Cancelled nominal-boundary recovery diagnostics | approved | cancelled | BLOCKED | not_evaluated | superseded | [design](ductile-origami-warmstart/s10r1-stage1-valid-support-entry-recovery-design.md) | none (A32 operational record only) |
| S10R2 | Stage 1 support-aware entry recovery | approved | completed | CHECKPOINT_COMPLETE | inconclusive | effective | [design](ductile-origami-warmstart/s10r2-stage1-support-aware-entry-recovery-design.md) | [report](ductile-origami-warmstart/reports/staged/s10r2-stage1-support-aware-entry-report.md) |
| S10R3 | Stage 1 bounded-cover entry recovery | approved | not_started | DESIGN_APPROVED | not_evaluated | absent | [design](ductile-origami-warmstart/s10r3-stage1-bounded-cover-entry-recovery-design.md) | `reports/staged/s10r3-stage1-bounded-cover-entry-report.md` |
| S11 | Stage 1 model-only factorization／guidance lock | approved | gated | DESIGN_APPROVED | not_activated | absent | [design](ductile-origami-warmstart/s11-stage1-model-only-factorization-design.md) | `reports/staged/s11-stage1-model-only-factorization-report.md` |
| S12 | Stage 1 D5 real-score／oracle audit | approved | gated | DESIGN_APPROVED | not_evaluated | absent | [design](ductile-origami-warmstart/s12-stage1-real-score-ranking-oracle-audit-design.md) | `reports/staged/s12-stage1-real-score-audit-report.md` |
| S13 | Stage 1 actual Gen0 mechanism | approved | gated | DESIGN_APPROVED | not_evaluated | absent | [design](ductile-origami-warmstart/s13-stage1-actual-gen0-mechanism-design.md) | `reports/gen0-factorization-mvp-report.md` |
| S20 | Stage 2 H10 persistence | approved | gated | DESIGN_APPROVED | not_evaluated | absent | [design](ductile-origami-warmstart/s20-stage2-h10-persistence-design.md) | `reports/short-horizon-persistence-report.md` |
| S30 | Stage 3 held-out registry／procedure freeze | approved | gated | DESIGN_APPROVED | not_evaluated | absent | [design](ductile-origami-warmstart/s30-stage3-heldout-registry-freeze-design.md) | `reports/staged/s30-heldout-registry-freeze-report.md` |
| S31 | Stage 3 two-cluster bounded replication | approved | gated | DESIGN_APPROVED | not_evaluated | absent | [design](ductile-origami-warmstart/s31-stage3-bounded-replication-design.md) | `reports/bounded-regime-replication-report.md` |
| S40 | Stage 4 activation／data-sufficiency gate | approved | gated | DESIGN_APPROVED | not_evaluated | absent | [design](ductile-origami-warmstart/s40-stage4-surrogate-activation-gate-design.md) | `reports/staged/s40-stage4-activation-report.md` |
| S41 | Stage 4 nested learned-residual analysis | approved | gated | DESIGN_APPROVED | not_evaluated | absent | [design](ductile-origami-warmstart/s41-stage4-learned-residual-analysis-design.md) | `reports/learned-residual-surrogate-report.md` |

`milestone`／`step`只有在指向上述ID時才是checkpoint alias。

### Strict dependency graph

```mermaid
flowchart TD
  s00["S00 Evidence foundation"]
  s10["S10 Stage 1 entry"]
  s10r1["S10R1 Cancelled diagnostics"]
  s10r2["S10R2 Support-aware entry"]
  s10r3["S10R3 Bounded-cover entry"]
  s11["S11 Guidance lock"]
  s12["S12 D5 audit"]
  s13["S13 Actual Gen0"]
  s20["S20 H10 persistence"]
  s30["S30 Registry / freeze"]
  s31["S31 Bounded replication"]
  s40["S40 Surrogate activation"]
  s41["S41 Learned residual"]

  s00 -->|"S00_EVIDENCE_READY"| s10
  s00 -. "administrative readiness" .-> s10r2
  s10 -. "terminal provenance only; no scientific edge" .-> s10r2
  s10r1 -. "A32 status only; evidence reuse forbidden" .-> s10r2
  s10r2 -. "terminal inconclusive provenance; evidence reuse forbidden" .-> s10r3
  s10r3 -->|"S1_ENTRY_GO"| s11
  s11 -->|"S1_GUIDANCE_LOCKED"| s12
  s12 -->|"D5_PASS"| s13
  s13 -->|"D6_MECHANISM_POSITIVE"| s20
  s20 -->|"S2_DIRECTIONAL_PERSISTENCE_POSITIVE"| s30
  s30 -->|"S3_REGISTRY_PROCEDURE_LOCKED"| s31
  s12 -. "predictor failure + oracle positive" .-> s40
  s31 -. "predictor heterogeneity + oracle positive" .-> s40
  s40 -->|"S4_ACTIVATE"| s41
```

S00的post-audited positive closeout已驗證`S00_EVIDENCE_READY -> S10`。S10已完成actual-guidance、live-unreserved H4與其frozen canonical mapping boundary，並以完整可重現的`FT-BLOCKED-MAPPING` negative branch形成`S1_ENTRY_BLOCKED`；沒有outgoing edge。Direct evidence、successor lineage、mapping stop與claim boundary見[S10 formal report](ductile-origami-warmstart/reports/staged/s10-stage1-entry-gate-report.md)；早期[blocker memo](ductile-origami-warmstart/reports/gen0-factorization-blocker-memo.md)只保留為historical recovery evidence。

R12曾核准S10R1；A32後續在quiescent safe boundary取消該execution。S10R1固定為
`cancelled / BLOCKED / not_evaluated / edge=null`，不建立scientific report或
completion；stochastic non-discovery不是scientific inconclusive或absence proof。
新的[S10R2 design](ductile-origami-warmstart/s10r2-stage1-support-aware-entry-recovery-design.md)
是sibling checkpoint。S00 readiness、S10 terminal provenance與A32 status只作
administrative prerequisites；虛線不是scientific edge，且S10R1 artifacts禁止重用。
S10R2已依其frozen exact-ten criterion誠實closeout為inconclusive/null。A38另建立
[S10R3](ductile-origami-warmstart/s10r3-stage1-bounded-cover-entry-recovery-design.md)；
S10R2對它只提供immutable terminal provenance，所有outcome-bearing artifacts禁止
重用。只有post-audited `S10R3:S1_ENTRY_GO -> S11`。所有downgrade仍先停在
`blocked-awaiting-user-decision`。

### Stable criterion IDs

Checkpoint designs只能引用下列parent IDs，不得自行改門檻：

- `S00_EVIDENCE_READY`
- `S1_ENTRY_GO`
- `S1_ENTRY_DEGRADED_PROXY`
- `S1_ENTRY_BLOCKED`
- `S1_GUIDANCE_LOCKED`
- `D5_PASS`
- `D5_BORDERLINE_INCONCLUSIVE`
- `D5_FAIL`
- `D6_MECHANISM_POSITIVE`
- `S2_DIRECTIONAL_PERSISTENCE_POSITIVE`
- `S3_REGISTRY_PROCEDURE_LOCKED`
- `S3_BOUNDED_REPLICATION_POSITIVE`
- `S4_TRIGGER_ELIGIBLE`
- `S4_DATA_GATE_PASS`
- `S4_ACTIVATE`
- `S4_LEARNED_RESIDUAL_POSITIVE`
- research charter中的全部`FT-*`

語意：

- `S00_EVIDENCE_READY`：observer neutrality、checkpoint/resume parity、lineage lock與artifact reconciliation全部通過。
- `S1_ENTRY_GO`：§2 entry gates通過，且actual YAML guidance可追溯。S10、已取消的
  S10R1與terminal inconclusive的S10R2都不會發出此edge；只有S10R3可產生新的
  checkpoint-scoped `S1_ENTRY_GO`。
- `S1_ENTRY_DEGRADED_PROXY`：§2 entry gates通過，但只能使用exact-space GEKO branch proxy；另需user downgrade approval。
- `S1_ENTRY_BLOCKED`：§2.8任一hard stop成立。
- `S1_GUIDANCE_LOCKED`：§4–§5 model-only frame、gene decisions、weights、shuffle與hash在real labels前完成鎖定。
- `S3_REGISTRY_PROCEDURE_LOCKED`：§16的兩primary slots、reserve、denominator、frozen procedure與完整budget均在任何Stage 3 score前鎖定。
- `S4_TRIGGER_ELIGIBLE`：§18.1 predictor-specific failure成立，且§18.2禁止patterns均不存在。
- `S4_DATA_GATE_PASS`：§18.3四-cluster data floor與prospective fourth-cluster規則通過。
- `S4_ACTIVATE`：前兩項同時通過，授權執行S41。
- `S4_LEARNED_RESIDUAL_POSITIVE`：§19.4每個primary held-out unit的ranking、prior-mass與oracle-gap gates全部strictly通過。

### Separated lifecycle fields

- `design_status`: `draft | approved | superseded`
- `execution_status`: `not_started | gated | ready | running | blocked | completed | cancelled`
- `checkpoint_state`: `DESIGN_APPROVED | LOCKED_READY | RUNNING | VERIFIED_PENDING_CLOSEOUT | CHECKPOINT_COMPLETE | BLOCKED`
- `scientific_outcome`: `not_evaluated | positive | negative | inconclusive | blocked | not_activated | skipped_by_gate`
- `lock_state`: `absent | effective | superseded`

只有`lock_state=effective`、`execution_status=ready`與`checkpoint_state=LOCKED_READY`可開始產生outcome-bearing evidence。`approved`只代表設計審查完成。

`scientific_gate`是不可合併或繞過的outcome／claim／authority edge；
`execution_tranche`可讓相容adjacent gates共享Main planning context、environment、
run root與repair ledger；每個scientific gate仍保留自己的Plan-B、Plan-A、fresh
implementer與fresh verifier。`closure_unit`可共享terminal
report/update/staged audit/commit，
但不改gate order或outcome。`live_run_state`與`committed_projection_state`必須分開；
partial working-tree evidence只能屬於前者。

### Governance tranches

| Execution tranche | Gates／risk tier | Closure unit |
| --- | --- | --- |
| `T-S10R2` | S10R2=`R2` | `CU-S10R2` standalone |
| `T-S10R3` | S10R3=`R3` | `CU-S10R3` standalone |
| `T-S1-MECHANISM` | S11=`R2` → S12=`R2` → S13=`R1` | `CU-S1-MECHANISM` |
| `T-S20` | S20=`R1` | `CU-S20` standalone |
| `T-S3-REPLICATION` | S30=`R2` → S31=`R1` | `CU-S3-REPLICATION` |
| `T-S4-LEARNED-RESIDUAL` | S40=`R2` → S41=`R1` | `CU-S4-LEARNED-RESIDUAL` |

### Future gate／tranche closeout contract

每次只執行dependency-ready gate：

1. 讀取committed repository rule、skill、charter、parent與design revisions。
2. 將design maximum boundary縮成exact implementation與delivery whitelists。
3. 在outcome evidence前建立durable machine-readable frozen contract、驗證
   human/machine parity並seal effective lock。
4. 鎖定risk tier與cumulative wall-time／CPU／GPU／storage／throughput／repair／
   thread budgets；generation、successor、replacement、new root不得reset。
5. Main依序建立goal/oracle Plan-B與decision-complete Plan-A；fresh implementer與
   fresh verifier依visibility boundary及governance floor執行。
6. `CHANGES_REQUIRED`只修active checkpoint並重驗；consequential issue先走`design-discussion`。
7. Technical`PASS`只進`VERIFIED_PENDING_CLOSEOUT`。
8. Internal positive只sealdesign指定的compact durable gate record，依verified frozen
   edge留在同tranche繼續；不刪scientific gate、不先宣告closure complete。
9. Internal negative／inconclusive產生該gate planned terminal report並停止；final
   gate report整合prior gate records。
10. Terminal staged audit、`CLOSEOUT_ACK`、isolated commit與post-commit audit成功後，
    才更新`committed_projection_state`與closure unit。

Positive、negative與inconclusive都要durable outcome closure。Operational
`BLOCKED`不是scientific completion；`skipped_by_gate`／`not_activated`不建立假report。

### 2026-07-25 pre-execution authority amendment

- **Trigger：**S00、S10、S11、S12、S13與S20的`delivery_boundary_max`未包含唯一active index；S00 delivery maximum也未承接既有implementation maximum中的observer／checkpoint-resume integration points與fresh deterministic foundation fixtures/tests。Charter另重複了會在closeout後過時的current-state敘述。
- **受影響不變量：**`delivery boundary ⊇ implementation boundary`、唯一active index與parent/design的一致性，以及checkpoint closeout的可稽核性。
- **曾考慮替代方案：**維持原狀會留下已知stale-state與boundary缺口；只修S00會讓已知缺口在S10–S20重現；只在parent加overlay則會降低各design的self-contained authority。三者均未採用。
- **審查：**Gauss（`/root/s00_closeout_a`）與Beauvoir（`/root/s00_closeout_b`）以fresh `gpt-5.6-sol/xhigh`獨立首輪、互相cross-examine，最後均明確`AGREE`。
- **決策：**只修本parent、charter、active README與S00／S10／S11／S12／S13／S20六份design，共九個exact paths。六份design delivery maximum納入`README.md`；S00另逐字承接上述兩類implementation authority；closeout同步parent、current design與README的verified lifecycle projection。投影只可更新當前checkpoint row、直接解析的outgoing edge／downstream state與事實性banner prose，不得預寫下游結果。
- **使用者核准：**2026-07-25核准「S0–S2九路徑 authority amendment 與其 exact-path ordinary baseline commit」；明確不授權push。
- **Authority effect：**不改研究問題、samples、seeds、公式、thresholds、acceptance、strict DAG、failure taxonomy或claim ladder，也不改S30+狀態。ordinary baseline commit只固定本次治理修正，不是任何checkpoint closure。
- **剩餘不確定性：**S00的exact implementation paths與scientific outcome仍須由fresh planning、effective lock、implementation、independent verification及closeout決定；S00完成後整體研究仍可能保持`pre_empirical`。

### 2026-07-26 S10R1 post-closeout measurement amendment

- **Trigger：**S10已依frozen contract合法closeout為mapping-negative；之後的唯讀replay確認九個raw Cartesian candidates被同一Ductile validator拒絕，而downstream operational domain是`valid_fn` accepted occurrences。S10 helper另只把non-finite當Formocast rejection，但pinned early-terminate回傳finite `9999999.9/0`，runtime則依whole-cohort threshold queue處理。
- **受影響不變量：**S10 terminal record／artifacts／report／design及null edge保持immutable；actual YAML、source pins、space、groups／order／weights、三sizes、exact ten、三anchors、七repeats、63 cells、correctness、noise threshold與claim均不得降級。
- **替代方案：**S10 `successor-004`、post-hoc重標、替換invalid rows、第11筆、強制啟用runtime threshold、把S11的8,192／256 accepted targets提前搬入entry gate，以及把finite-cap non-discovery當support不存在均被拒絕。
- **審查：**`/root/s10_postclose_recovery_a`與`/root/s10_postclose_recovery_b`兩位fresh `gpt-5.6-sol/xhigh` reviewers以相同evidence獨立首輪、交換完整立場、交互詰問；修正configured `pop_size=512`與constructor-resolved `11,405`的邊界後，均對同一candidate明確`AGREE`。
- **決策：**新增stable checkpoint S10R1，不重開S10。Pre-execution ordinary baseline只修改charter、本parent、active README、新S10R1 design與S11 dependency五個exact paths；不含empirical outcome。S10R1另走完整plan／implement／verify／report／ACK／isolated commit／post-audit lifecycle。
- **Sampling authority：**逐float32重現actual GA probabilities；global與每個missing-token conditional stream分開保存，使用512-draw ledger chunks及`250 * 11,405 = 2,851,250` nominal-draw ceiling，最後不足一chunk時固定434 draws；exact-ten coverage在第一個可行chunk boundary deterministic early-stop。Cap耗盡未發現support為`FT-INCONCLUSIVE`，只有complete support proof可判mapping-negative。S11的4,096／8,192與128／256 accepted targets保持在S11。
- **Measurement authority：**Ductile validity、Formocast model sentinel與runtime queue status分欄；至少一個預鎖score-blind sentinel-risk valid row須觀察exact `9999999.9/0`與source-order guard parity。Threshold `>1`誠實記`prediction_disabled`，不得為製造rejection而修改。
- **使用者授權：**使用者已委派`/data1/perlee`內的此類block由design-discussion共識決定，不需再次停下核准；本共識授權上述五路徑baseline與S10R1 checkpoint closeout commit，明確不授權push。
- **剩餘不確定性：**尚未證明exact-ten valid coverage、sentinel guard observation、anchor codegen／correctness或noise會通過；這些必須由S10R1 fresh evidence決定，不得預寫結果。

### 2026-07-28 A32 cancellation、S10R2與tiered-governance amendment

- **Trigger：**S10R1 mandatory nominal-boundary selector偏離核心Formocast
  factorization問題；repair generations、verification loops、wall-time與transient
  storage已超出合理research budget。
- **User decision／safe boundary：**append-only S10R1 governance chain的A32 event核准
  停止S10R1。Generation 0已atomic retire並byte-identical sealed；generation 1未建立
  effective L0、selection、mapping、GPU、noise、decision或formal outcome，且沒有
  scientific／GPU／pytest writer或governance flock。
- **Durable S10R1 interpretation：**
  `execution_status=cancelled / checkpoint_state=BLOCKED /
  scientific_outcome=not_evaluated / edge=null`；不是`CHECKPOINT_COMPLETE`，不建立
  scientific report。Generation 0／1只作diagnostic provenance，所有empirical／
  repair artifacts禁止重用；stochastic non-discovery不是`FT-INCONCLUSIVE`或absence
  proof。
- **S10R2 decision：**新增sibling
  [S10R2](ductile-origami-warmstart/s10r2-stage1-support-aware-entry-recovery-design.md)，
  risk tier=`R2`、standalone tranche／closure；只在observed operational valid
  support內建立exact-ten mapping，並把deterministic sentinel/helper conformance與
  random corpus分離。只有`S10R2:S1_ENTRY_GO`可啟動S11。
- **Preserved science：**S11–S41全部scientific gates、criterion edges、hypotheses、
  thresholds、samples、seeds、claims與Stage 1/2/3/4 timeboxes完整保留；沒有proxy、
  two-size、workload或acceptance downgrade。
- **Tiered governance：**execution floor固定為
  `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`；建立S10R2、
  S11+S12+S13、S20、S30+S31、S40+S41五個tranches／closure units。Internal positive
  使用compact gate record繼續；internal terminal negative／inconclusive產生planned
  report；final report整合prior records。
- **Resource authority：**所有wall-time、CPU/GPU、storage、throughput、
  pre-empirical engineering、repair與fresh-thread budgets跨generation、successor、
  sibling、replacement與new root累計；本amendment不授權reset。Stage timebox是hard
  cap，不是完成承諾。
- **Current state projection：**本次只更新documentation／authority；不建立protocol
  code、tests、contract、lock、artifact、scientific report、commit或push。Working-tree
  amendment屬`live_run_state`；在future exact-path commit與post-audit前，不把它誤稱
  已完成的`committed_projection_state`。

### 2026-07-28 A33 identity-only retirement與research rebaseline

- **Trigger：**S10R1已取消且S10R2明文禁止重用其artifacts，但約34 GB ignored
  source／selection／verification／failed-attempt tree與19個untracked S10R1-only
  implementation paths仍占用active workspace；A32的「immutable diagnostic
  provenance」若被理解成永久保留physical bytes，會同時增加storage與誤引用風險。
- **Design discussion：**fresh reviewers
  `/root/s10r1_cleanup_review_a`與`/root/s10r1_cleanup_review_b`使用相同
  `gpt-5.6-sol / xhigh` capability與相同evidence。兩方獨立提出立場，完成一輪
  cross-examination，再審查同一final candidate，均明確`AGREE`。最強反對意見是：
  authority必須先durable、permission／mount／link異常須fail closed、不能把disk
  release冒充budget reset，也不應為非authority duplicates支付34 GB逐檔hash成本。
- **Retention decision：**採identity-only retirement。Current S10R1 design只保留
  cancellation tombstone；完整superseded protocol留在Git history。新的
  [retirement manifest](ductile-origami-warmstart/retirements/s10r1-diagnostic-retirement.json)
  保存A30–A32、source／YAML／L0／selection identities、pre-cleanup inventory、
  19-path digests、resource known／`UNKNOWN`、exact allowlist與post-audit。
- **Two-phase cleanup：**第一個exact-path authority commit固定
  `authorized_pending_cleanup`；live recheck後只刪manifest列出的ignored S10R1
  run root與19個untracked paths；第二個exact-path commit固定
  `retired_post_audited`。禁止`git clean`、glob、parent-wide cleanup、unrelated
  staging、container lifecycle mutation與push。
- **Scientific effect：**沒有。S10R1仍是
  `cancelled / BLOCKED / not_evaluated / edge=null / superseded`；不建立report、
  completion或edge。Stochastic non-discovery仍不是absence proof或
  `FT-INCONCLUSIVE`。S10與S10R2 criteria／workloads／claims均不變。
- **Resource effect：**physical cleanup只降低current retained bytes，不reset歷史
  wall／CPU/GPU／storage／throughput／pre-empirical／repair／thread consumption。
  本次human instruction沒有給任何數值reset。S10R2在retirement post-audit與新的
  durable resource decision逐欄記錄prior consumption、carry-over、reset boundary及
  future caps前，保持operational
  `BLOCKED / scientific_outcome=not_evaluated / edge=null`。
- **Progression：**`retirement -> resource relock -> S10R2`；
  S10R2 positive才進`S11 -> S12 -> S13`；D6 positive才進S20；S20 positive才進
  `S30 -> S31`；S40／S41只在既定predictor-specific／oracle-positive trigger與data
  gate成立時啟動。任何terminal negative、inconclusive、resource gate或未核准
  downgrade都停止。
- **Residual uncertainty：**Stage-1 hands-on、CPU/GPU、pre-empirical餘額仍
  `UNKNOWN`；fresh threads及repair rounds只有已超過新R2 defaults的lower bounds。
  Retirement manifest保存此不確定性，不用推算補值。

### 2026-07-28 A34 prospective resource relock authority

- **Trigger：**A33已釋放S10R1 physical artifacts，但historical fresh threads至少10、
  repairs至少11，其他Stage-1 resource consumption為`UNKNOWN`，且A33沒有reset
  authority。直接進S10R2會同時違反cumulative accounting與entry preflight。
- **Design discussion：**fresh reviewers`/root/s10r2_next_plan_a`與
  `/root/s10r2_next_plan_b`以相同`gpt-5.6-sol / xhigh` capability、相同authority
  bundle獨立審查，完成一輪cross-examination與一輪evidence-backed final。最強
  objections是：calibration authority不能冒充final preflight；5/3 enforcement unit
  必須明列，不能由gate名稱自動reset；S13仍受R1 repair cap；沒有direct evidence時
  不得捏造CPU/GPU hours。修正後兩方均`AGREE`。
- **Historical ledger：**cutoff固定為
  `d66edf7ac81cb76825b988e1ea9a65264dfeb0f6`；保留3151 chunks、
  fresh threads`>=10`、repairs`>=11`與全部`UNKNOWN`。A33 cleanup只改current
  capacity，不改historical peak、writes或lifetime totals。
- **Prospective enforcement：**承載本決策的exact-path authority commit通過
  post-audit後，`T-S10R2`可使用new threads`<=5`／new repairs`<=3`；
  `T-S1-MECHANISM`先reserve同樣5/3、只有S10R2 GO後activate，且S11→S13內不得
  再reset；S13仍受R1最多2 repairs。這是A34當時的boundary，prospective repair
  caps後由A44統一supersede為6。S10R2→S13共享prospective Stage-1 hands-on
  `<=7 days`、pre-empirical`<=1.4 days`及transient storage`<=5 GiB`。
- **Two-stage relock：**第一階段只授權exact count-bounded、outcome-blind
  synthetic／foundation calibration，禁止actual validity/support、Formocast、
  GFLOPS、correctness/noise labels與S10R1 artifacts。第二階段才以calibration及
  confirmed allocation產生具單位wall／CPU／GPU caps、buffer與safe boundaries，
  寫入durable contract／lock並通過parity與adversarial audit。
- **First-1% gate：**main lock後，第6個512-draw chunk完成的3,072 draws是唯一初次
  actual resource reforecast boundary；只讀resource telemetry，labels保持sealed。
  Projection超過2倍或cap exceed即safe pause，不修改protocol或縮scope。
- **Current effect：**A34不改scientific hypothesis、workload、criteria、outcome、
  edge或claim。Numeric caps與effective lock完成前，S10R2維持
  `BLOCKED / not_evaluated / edge=null`；不授權formal evidence、push、dependency
  install、container lifecycle mutation或downgrade。

### 2026-07-28 A35 R2 repair-budget amendment

- **Trigger：**S10R2 adversarial audit v3已關閉先前noise、GPU isolation、resource
  lifecycle與registry/window findings，但typed-exact allocation cross-binding仍為
  `CHANGES_REQUIRED`；當時`T-S10R2`已消耗原3/3 repair rounds。
- **User decision：**使用者明確授權繼續修復，並將R2 repair round上限由3提高為6。
- **Carry-over：**rounds 1–3完整保留，不能因本amendment、generation、restart、
  replacement或new root歸零；下一輪是round 4，最多到round 6。Fresh role-thread
  上限仍為5。
- **Scope：**只擴張R2 repair governance，不改任何scientific hypothesis、search
  space、workload、seed、threshold、criterion、outcome／edge matrix、claim、
  resource cap、allocation value或evidence boundary。`T-S1-MECHANISM`原reserved
  5-thread／3-repair allowance與S13 R1最多2 repairs在A35當時不變；prospective
  repair caps後由A44統一supersede為6。
- **Progression：**更新後的frozen contract必須綁定本authority amendment並重新取得
  adversarial `AUDIT_PASS`；其後仍須effective lock seal commit與post-seal audit，
  才能開始formal evidence。A35不授權push或downgrade。

### 2026-07-29 A36 resource-accounting materiality amendment

- **Trigger：**S10R2已完成固定448 chunks／229,376 draws；fresh verifier重現
  `inconclusive / FT-INCONCLUSIVE / edge=null`，但發現ledger只記validator child
  wall／CPU。Ledger wall為`3561.4237106395885 s`，external selection wall為
  `8924.894379 s`，parent CPU為`UNKNOWN`。Post-hoc full-panel wall projection為
  `11010.038318274363 s`，低於frozen `11827 s` cap；沒有direct evidence顯示cap
  exceed、early stop、schedule drift或label-dependent selection。
- **User decision：**使用者明確要求不要過度放大不影響整體實驗的resource-accounting
  缺口，並要求修改治理規則、以整體實驗進行為優先。
- **Materiality rule：**resource telemetry是operational safety／planning control；
  除非resource use本身是approved scientific estimand，只有direct evidence顯示或
  實質指向cap exceed、unsafe continuation、label-dependent stopping／selection、
  required workload不完整或scientific evidence不可驗證時才blocking。Fixed workload、
  evidence chain與independent reproduction完整且沒有direct cap-exceed evidence時，
  fine-grained／parent-process accounting缺口只作non-blocking caveat。
- **S10R2 application：**既有contract、lock、terminal ledger、support classification
  與decision全部保持immutable；不建立resource-only fresh run。Fresh verifier可依
  本amendment重驗並在formal report記錄resource caveat。A36不把S10R2改成positive，
  不改exact-ten criterion、outcome matrix、claim或edge。
- **Progression boundary：**S10R2仍是
  `inconclusive / FT-INCONCLUSIVE / edge=null`，所以resource caveat即使解除technical
  blocker也不能啟動S11。後續必須依新的合法entry recovery authority取得positive
  edge，或只做明標diagnostic、不得冒充formal S11 evidence。
- **Authority limits：**本amendment不授權push、刪除evidence、重寫ledger、縮減
  scientific workload，或將nonpositive outcome改寫成GO。

### 2026-07-29 A37 prospective resource-progress priority

- **Trigger：**A36只處理S10R2 post-label accounting caveat；general rule、本plan與
  `implement-verify-loop`仍把`>2x`、internal time／storage／throughput target及
  cumulative consumption寫成blanket hard pause／successor debit。使用者明確要求
  resource ledger若不影響整體實驗，就不要過度在意並以完整研究進度為優先。
- **Design discussion：**fresh reviewers`/root/resource_rule_review_a`與
  `/root/resource_rule_review_b`使用相同`gpt-5.6-sol / xhigh`及相同repo evidence，
  各自提出立場，完成一輪cross-examination及一輪evidence-backed final。雙方均
  `AGREE`取消nonmaterial blanket gate；接受保留真正availability／safety／evidence
  hard boundary，並拒絕刪除歷史帳、縮scientific workload或讓labels決定停止。
- **Prospective rule：**resource usage預設是operational planning metadata，不是
  scientific estimand、acceptance criterion或successor-entry debit。Known usage及
  parent／child／inclusive boundary以best effort保留；`UNKNOWN`不補造、不寫成0。
  Missing telemetry、`>2x` projection、internal day／wall／CPU／GPU／storage／
  throughput／pre-empirical target crossing與historical cumulative consumption只需
  record＋notify；long-running work開始前通知，但通知不是approval gate。
- **Material pause：**只有direct或materially indicative operational evidence連到
  unsafe continuation、external／platform／allocation限制、實際資源不足、完整
  frozen workload／verification／closure／artifact preservation無法完成、
  label-dependent stopping／selection、required workload／claim change、evidence
  不可驗證，或labels前明確凍結的scientific resource／comparability boundary時，
  才safe-boundary pause。Bare `UNKNOWN`、internal target crossing或cumulative total
  不能單獨構成material evidence。
- **Unaffected hard boundaries：**scientific sample／draw／seed／arm／population／
  generation／repetition與thread caps、downgrade gate、evidence retention、claim
  boundary、destructive／push／container authority全部不變；repair history依A46只作
  append-only provenance。本amendment不授權啟動任何checkpoint。
- **Supersession／immutability：**A37 prospectively supersedes本plan中把internal
  resource target一律當hard pause或cumulative successor debit的舊文字；future
  machine contract／validator必須採相同語意。S10R2 A36、contract、lock、ledger、
  artifacts、report及`inconclusive / FT-INCONCLUSIVE / edge=null`完全immutable，
  不做resource-only rerun，也不因此產生S11 edge。

### 2026-07-29 A38 S10R3 bounded-cover entry authority

- **Trigger：**S10R2依frozen exact-ten selector完成全部fresh support discovery後，
  觀察到90個mandatory atoms，deterministic greedy full cover需要18個configs；
  因固定十筆無法cover，S10R2正確closeout為
  `CHECKPOINT_COMPLETE / inconclusive / FT-INCONCLUSIVE / edge=null`。
- **Immutable boundary：**不重開、不修改也不重標S10R2。其`C_greedy=18`只作
  post-label design diagnostic，不是S10R3 expected outcome、formal witness或coverage
  guarantee。S10R1／S10R2 outcome-bearing artifacts全部禁止重用。
- **Design discussion：**fresh reviewers`/root/s1_recovery_design_a`與
  `/root/s1_recovery_design_b`使用相同`gpt-5.6-sol / xhigh`與相同live evidence，
  完成兩輪cross-examination及一輪evidence-backed final。兩方共同支持bounded
  exact-K scientific package；final dissent只涉及planner count、resource projection
  與GPU availability authority。
- **Human decision：**使用者以「全部核准」核准完整corrected package、五路徑
  authority amendment與exact-path local commit、後續`implement-verify-loop`、
  A37 resource semantics及existing `perlee`內free-card policy；明確不授權push。
- **New checkpoint：**新增R3 sibling
  [S10R3](ductile-origami-warmstart/s10r3-stage1-bounded-cover-entry-recovery-design.md)，
  `scientific_gate=S10R3`、`execution_tranche=T-S10R3`、
  `closure_unit=CU-S10R3`。它使用fresh registry、disjoint seeds及fresh append-only
  ledger；只有post-audited `S10R3:S1_ENTRY_GO -> S11`。
- **Fixed discovery：**chunk=`512`；global exact
  `32 chunks / 16,384 draws`；global完成後依sealed registry/priority機械啟動最多15個
  conditional targets；每target exact `32 chunks / 16,384 draws`；total max
  `512 chunks / 262,144 draws`。無early stop、extension、seed retry、target
  replacement、old-row reuse或outcome-dependent scheduling。Stochastic zero仍只可
  `support_unobserved`。
- **Mandatory set與selector：**

  ```text
  mandatory_mapping_atoms
  = prelocked_candidate_atoms ∩ supported_witnessed

  selector = deterministic_greedy_set_cover_v2_bounded_k20
  C_greedy = frozen greedy full-cover cardinality
  K        = max(10, C_greedy)
  K_max    = 20
  ```

  `C_greedy`不是mathematical minimum。Fresh distinct witnesses少於10或
  `C_greedy>20`即`inconclusive / FT-INCONCLUSIVE / edge=null`；labels後不得加solver、
  draw、seed、selector或提高cap。
- **Lower-bound disclosure：**
  `L_axis=max witnessed mandatory values on one residual axis`只作non-gating audit。
  `L_axis>20`可證明所有covers over-cap；否則greedy over-cap時必須揭露沒有評估global
  minimum-cover feasibility。
- **Mapping/GPU semantics：**mapping A/B各exact `3K` rows，最多60 rows/pass；不准
  replacement、guess、unresolved或failed row。Sorted-hash anchors為
  `{0,floor((K-1)/2),K-1}`；correctness仍9 cells、noise仍63 cells，native
  helper/fault、`CV P95<=0.5%`、`delta_noise`與no-replacement criteria不變。
- **Role boundary：**已使用兩個design reviewers；Codex adapter另用two planners、
  one adversarial auditor、Main implementation與one fresh verifier，合計R3
  `6/6` threads，沒有replacement headroom。A44生效後R3 repair最多6 rounds；
  rounds 1–3完整carry over。
- **Resource/GPU：**initial
  `12669 wall-s / 65285 CPU-s / 2901 GPU-s / 2 GiB`是A37 planning estimates，
  crossing只record＋notify；只有A37 material condition暫停。所有GPU／ROCm command
  只在existing `perlee`；每phase可直接選目前free eligible gfx942，不需reservation
  或exclusivity，但必須prelockidentity、foreign-PID rejection、cell boundary、
  interruption與append-only resume。
- **Preserved downstream：**S11–S13的4,096／8,192 occurrences、128／256 support、
  samples、seeds、thresholds、workloads、criteria、claims與internal edges全部不變；
  S11只把entry dependency與mapping fixture改綁fresh S10R3 exact-K output。

### 2026-07-30 A44 universal six-round repair與goal-persistence amendment

- **User decision：**所有prospective R0–R3 checkpoint repair cap統一為6 rounds。
  已消耗rounds完整carry over；generation、successor、replacement、restart或new root
  不能歸零，第7輪仍需新的human authority。
- **S10R3 effect：**原R3 `3/3`擴為`3/6`，下一輪是round 4。這只修改execution
  governance，不改scientific hypothesis、search space、draw／seed／cell schedule、
  selector、mapping、correctness/noise threshold、outcome matrix、claim或edge。
- **Design gate：**experiment protocol、measurement／claim／lineage、stopping rule或
  scientific authority議題，必須由兩個獨立agents完成bounded cross-examination，
  再把unified recommendation或preserved dissent交使用者決定；consensus本身不授權
  design變更。
- **Non-design authority：**會使goal停止的非設計問題、多個contract-preserving修復
  方向或同一finding兩輪無material progress，可由兩個獨立agents交互詰問。其共同
  non-destructive、contract/authority-preserving結論已預授權Main agent直接執行。
  Thread cap沒有headroom時resume兩個未參與該修復實作的既有獨立角色，不以新thread
  規避cap。
- **Persistence：**普通`CHANGES_REQUIRED`、可修復test/process failure、nonmaterial
  resource-accounting variance不得提前terminalize仍可在既有authority內完成的goal。
  Missing destructive/external/platform authority、hard safety/scientific boundary與
  第6輪後仍無有效路徑仍是真實stop gate。A44不授權push、downgrade、container
  mutation或destructive cleanup。

### 2026-07-30 A45 S10R3 clean-restart／雙seal execution alignment

- **Trigger：**使用者要求刪除全部未提交S10R3 implementation、tests、manifests、
  contract draft、cache與舊run artifacts，保留committed S10R3 scientific design與
  parent authority，依current `.agents` `implement-verify-loop`從clean execution
  baseline重啟。Cleanup時不存在effective lock、formal evidence、outcome、report或
  edge；S10R3保持`not_evaluated / edge=null`。
- **Direct conflict：**current workflow禁止planner subagents與Main source
  implementation，要求Main先freeze Plan-B再寫Plan-A，之後才啟動fresh implementer；
  A38歷史role配置與S10R3單一pre-plan contract同時要求final implementation hashes，
  因而形成pre-evidence sequencing cycle。
- **Independent review：**fresh reviewers
  `/root/s10r3_restart_design_a`與`/root/s10r3_restart_design_b`收到相同repo
  evidence，完成一輪cross-examination與一輪evidence-backed final；兩方都
  `AGREE`採最小雙seal alignment。這是execution authority／lifecycle修正，不是
  scientific plan change。
- **Phase 1 scientific/oracle seal：**既有contract path完整凍結hypothesis、criteria、
  outcome／edge matrix、measurement／claim boundary、source／YAML／seed／schedule／
  selector語意、三個exact write boundaries、forbidden reuse、role visibility、
  counters、final-binding schema與prelocked invalidation matrix。Implementation
  identity是fail-closed `required_pending`，`outcome_access=false`。Current
  user-mandated workflow bytes只以path、SHA-256、mode、size、base HEAD、Git state與
  `committed=false`綁定；不得stage它們。Auditor pass後，本plan、charter、active
  README、S10R3 design與contract使用exact-path local commit seal；commit OID與
  contract SHA構成preimplementation lock identity。
- **Exact artifact／schema closure：**run root本身不作遞迴whitelist；control-plane
  逐path列出，build／run／scratch／log／raw／intermediate／reproduction只在具名
  artifact-only子目錄依explicit descendant semantics寫入，且不進delivery。Phase 1
  也完整固定Phase 2 lock的property tree、field/type/cardinality/null、
  `additionalProperties=false`、path-mode-hash record、state／audit shape與canonical
  self-hash convention。
- **Plans／implementation：**Phase 1 post-audit後，Main先freeze verifier-facing
  Plan-B，再寫implementer-facing Plan-A；Main不得實作。Fresh implementer只收到
  Plan-A與必要frozen constraints，不得讀Plan-B，只做label-blind implementation、
  tests、schema、adapter、build、registry與fixture。
- **Phase 2 effective execution lock：**既有effective-lock path綁Phase 1 identity、
  Plan-B／Plan-A hashes、全部pre-label implementation／test／schema／adapter bytes、
  native helper binary、toolchain／argv、fresh registry／fixture／input identities、
  roles／counters、whitelists與outcome-artifact absence。Outcome-dependent final-K
  binaries不預造；Phase 1只預鎖其generation／admission／lineage rules。Existing
  auditor重新驗證binding completeness、scientific projection、whitelist與no-label
  absence；lock exact-path local commit及post-seal audit全過後才是`LOCKED_READY`。
- **Plan-B／repair invariant：**Phase 2只可填predeclared binding fields；Plan-B hash、
  Phase 1 contract hash、canonical scientific projection與whitelists必須不變。任何
  bound-byte repair建立append-only successor effective lock。Labels後只可依prelocked
  component-to-phase invalidation matrix從最早受影響phase重跑；無機械證明時full
  rerun，source／seed／registry／ledger／discovery semantics改變時從first draw重跑。
- **Lineage／roles：**cleanup不重置歷史。Repair固定`4/6` used；使用者將S10R3
  fresh-thread cap提高為`9`，歷史`5`加本次兩位reviewers後為`7/9`，只保留一位fresh
  implementer與一位fresh verifier。Existing adversarial auditor以原thread對fresh
  bytes重驗，舊verdict不得沿用。
- **Phase 1 repair accounting：**首次audit findings開啟cycle 5，只補exact artifact
  boundary、effective-lock machine schema與operational blocker lifecycle。Fresh
  re-audit關閉artifact boundary，但反例仍要求補audit cross-field、fixed
  source/projection digest、formal-scope absence與resume lineage；cycle 5以
  `CHANGES_REQUIRED`完成，最後cycle 6 fresh re-audit通過時seal為`6/6`。
- **User-review boundary：**使用者澄清，只有實驗結果導致需要更動原實驗計畫並選擇
  新scientific方向時才中斷交由使用者決定。同一commit／feature內、pre-evidence且
  plan-preserving的implementation、verification與lifecycle alignment，以及所有
  non-destructive、contract／authority-preserving blocker均已預授權持續完成。
- **Operational BLOCKED：**唯一packet固定為
  `protocol/v1/evidence/s10r3-operational-blocker.json`。只有A37 material condition
  於safe atomic boundary成立才能建立；Main-only append events、conditional delivery、
  exact parent blocked/resume projection及isolated commit policy全部在Phase 1預鎖。
  它保存既有evidence但不是scientific report、completion或edge；條件解除且science
  不變時依standing authority自動resume，binding drift則先走successor lock。
- **Immutable science／authority limit：**S10R3 hypothesis、source/YAML/search space、
  draw／seed／cell schedule、mandatory atoms、selector／`K_max`、mapping、
  correctness／noise thresholds、outcome matrix、claim、report與唯一positive edge
  全部不變。Deleted S10R3 bytes／verdicts／plans及S10R1／S10R2 empirical evidence
  全部禁止。A45不授權push、downgrade、dependency install、額外container mutation或
  scientific change。

### 2026-07-30 A46 reviewer-governed uncapped-repair amendment

- **User decision：**所有R0–R3 repair cycle保留append-only finding／repair／
  verification provenance，但不再有numeric maximum；repair count不是stop、approval、
  success或completion gate，也不得由generation、successor、replacement、restart或
  new root抹除。
- **Direct repair authority：**responsible verifier／auditor提出具體finding且只有一個
  non-destructive、contract／authority-preserving修復時，可直接修復與重驗。有多個
  consequential choices、authority classification歧義，或同一finding兩輪沒有
  material progress時，由兩個獨立operational reviewers交互檢查；共同結論可直接執行。
- **User gate：**只有實驗結果迫使原實驗計畫的measurement、claim、scientific
  authority或方向改變，才中斷交使用者決定。
- **S10R3 application：**cycles 1–6完整保留。Phase 2
  `S10R3-P2-AUD-001`是cycle 7；兩位獨立reviewers確認唯一修復為threshold `0.0`
  native queue的oracle／fixture parity與受影響binding，且不改scientific plan。
  Formal evidence仍未開始，state保持`not_evaluated / edge=null`。
- **Unaffected hard gates：**scientific sample／draw／seed／cell／repetition與thread
  caps、downgrade、evidence integrity、safety、external／destructive／container及
  push gates均不變。Durable workflow baseline為
  `10b7d10ca7e197f7d93e1afd821805d4a65b1684`。

### Downgrade user gates

`DEGRADED_PROXY`、two-size／reduced-regime、S2 H5 resource-bounded pilot、single-cluster Stage 3 pilot，以及任何減少workloads、runs、seeds、metrics、validation、acceptance或scope的方案，都必須先產生完整decision packet並停在`blocked-awaiting-user-decision`。Diagnostic partial run不能滿足checkpoint或解鎖下游。

### Stage 3 reserve cutover

Primary cluster slots、最多一個technical reserve與優先序必須同時預鎖。Reserve只可因access、artifact或deterministic mapping technical failure替換，而且replacement decision必須發生在該slot第一筆Formocast score及第一筆real label之前。Scoring開始後的D5 fail、coverage不足、inconclusive、無eligible genes、oracle或GA negative都不得替換；固定denominator仍是兩個slots。

### Stage 4 data-qualified cluster

`qualified_for_stage4_data`與`D5_PASS`是不同欄位。Stage 4資料資格不要求D5 pass，但至少要求：

- independent search-space cluster ID與pre-label selection provenance；
- frozen mapping／revision；
- 至少256 unique judgment configs與兩個sizes；
- inclusion probabilities／analysis weights；
- correctness、coverage與lineage完整；
- 無leakage或outcome-driven amendment。

Mapping靠猜、coverage／correctness不完整或judgment pool不足者不具資格。

## Part I — Stage 1：七日 Gen0 mechanism protocol

> 本檔原有 D1–D7 嚴謹性完整保留。Part I 的數值、公式、locks 與 gates 不因新增後續 stages 而降低。

七日是Stage 1全部hands-on work的planning target，不是完成承諾或successor-entry
debit。S10R2、S10R3、S11、S12、S13每次entry都保留同lineage已知wall-time、CPU/GPU、
storage、throughput與pre-empirical usage及其measurement boundary作best-effort
provenance；`UNKNOWN`不補造。Repair rounds與fresh role threads仍跨generation、
successor、sibling checkpoint、replacement role或new root依governance hard caps累計。
Preflight評估dependency-ready gate、closure buffer與artifact preservation；只超過
internal planning target時record＋notify後繼續完整frozen workload，只有A37 material
condition成立才safe-boundary pause，不縮samples／seeds／sizes／criteria。

## 0. Stage 1 objective 與完成定義

### 0.1 Objective

在 frozen generated YAML 定義的 residual search space 中：

1. 量 Formocast whole-config ranking 是否有真實訊號；
2. 將訊號 factorize 成 ungrouped residual-gene probabilities；
3. 保留所有 existing YAML groups／weights；
4. 比較 existing guidance、Formocast residual guidance 與 same-entropy shuffled guidance；
5. 只有 offline gates 通過時，才用 actual Ductile `requested pop=64, n_gen=1` 測 Gen0；constructor-resolved population 必須在 real labels前鎖定。

### 0.2 Stage 1 能回答什麼

- Formocast 是否看得到 bounded residual space 的效能差異；
- Whole-config signal 是否能被獨立 per-gene hook 表達；
- 是否有超越 existing guidance／GEKO branch proxy 的 Gen0 增量；
- 失敗位於 mapping、model、factorization、sampler 或 heuristic saturation 哪一層。

### 0.3 Stage 1 不能單獨回答什麼

- 完整 GA convergence 或 tuning speedup；
- `n_gen>1` 後是否保留 Gen0 改善；此問題由 Stage 2回答；
- production deployment／adoption；
- 兩個新 fixed-tile regimes能否重現；此問題由 Stage 3回答；
- MI300X workload-level 泛化；
- StreamK、跨架構；
- learned residual surrogate是否能補 predictor failure；只有 Stage 4 data/trigger gate通過才研究。

### 0.4 完成狀態

- `completed_positive`：D5 與 D6 mechanism-positive criteria 全過。
- `completed_negative`：取得有效 empirical evidence，但某一預註冊 gate 失敗。
- `completed_inconclusive`：noise、support、coverage、importance ESS 或樣本範圍不足。
- `blocked`：D1–D2 access／artifact／mapping gate 未過。

---

## 1. Authority、locks 與不可變規則

### 1.1 Authority

- Scope、non-goals、failure taxonomy、claim boundary：research charter。
- 數值 protocol、公式、artifacts、stop rules：本檔。
- Frozen YAML 與 pinned code revisions：執行期間的實物權威。
- 實際 `soo/reduce_fn`、groups、candidate order 與 weights：只能由 frozen generated YAML／resolved config 取得，不得由 defaults 推定。

### 1.2 Lock points

在任何 real GFLOPS artifact 建立或解封前，必須 hash-lock：

- frozen YAML 與 provenance；
- source revisions；
- search-space map、groups、candidate order；
- sizes；
- model-only frame generation seeds；
- eligible／guided gene list；
- `alpha`、`epsilon`、`lambda` 與 weights；
- shuffled permutation bundle；
- D5 strata、sample IDs、fold IDs；
- measurement 與 correctness protocol。

看到 real GFLOPS 後不得修改上述項目。若必須修改：

1. 保留原 protocol 與原結果；
2. append amendment，記錄時間、理由與影響；
3. 原 D5 pool降級為 development data；
4. 另取未看過的 judgment pool，否則不得重新宣稱 gate pass。

### 1.3 Pinned code requirement

至少凍結：

- Ductile `ga.py`、`space.py`、`mutation.py` 與 validity code；
- GEKO config generator；
- TensileLite solution resolution／`getSizeMapping()`；
- Origami／Formocast；
- experiment runner／analysis code。

目前 workspace 中的工作樹狀態不能直接當正式 revision；執行前須保存 commit SHA、patch hash 或完整 source checksum。

### 1.4 S00 protocol foundation result

S00已建立fresh active runtime protocol：

```text
protocol/v1/README.md
protocol/v1/study-contract.yaml
protocol/v1/amendment-ledger.jsonl
protocol/v1/schemas/
protocol/v1/locks/s00-foundation-lock.json
```

- Genesis使用全新identity與`parent_lock: null`；iteration-1 technical findings透過
  exactly-one amendment與parent-linked `successor-001`修復，未覆寫原世代。
- 不得出現M00 version、hash、criterion、registry、path或migration provenance。
- Schema／validator／lock writer與fresh deterministic fixtures先實作、先驗證；
  兩代皆遵守lock-before-evidence。
- Effective successor lock綁定committed authority identities、兩份Plan-B、29/33 exact
  whitelists、fixtures/seeds、amendment與report target。
- Evidence開始後若schema、fixture或whitelist改變，必須append amendment、建立新lock並重跑，不得覆寫。
- Git history中的retired protocol內容不得作template、compatibility target或PASS evidence。
- Formal result見
  [S00 verification and closeout report](ductile-origami-warmstart/reports/staged/s00-foundation-verification-report.md)；
  它只支持CPU-only foundation semantics。

---

## 2. D1–D2 entry gate

### 2.1 Frozen generated YAML

保存 byte-for-byte copy、SHA-256、來源、生成命令與 generator revision，並解析：

- architecture、dtype、layout、transpose；
- non-StreamK 身分；
- problem sizes；
- fixed MacroTile 或 MTDU；
- `DepthU` 是 fixed、ungrouped free gene 或 grouped member；
- 全部 `group_i` 及其 candidate order；
- 全部 existing weights；
- `weight_beta`；
- ungrouped free genes；
- `soo` 與 resolved `reduce_fn`；
- correctness／validation 設定。

手工重建 YAML 不可冒稱 actual artifact。

### 2.2 Existing groups 的保護規則

所有 existing `group_i`：

- 不拆解；
- 不重排 candidate；
- 不修改 YAML-provided weights；
- 不將 group 內欄位另外當 residual genes；
- 即使 group 沒有 weights，也保持 YAML 原本的 grouped sampling semantics。

Formocast guidance只可作用於 manifest 明列的：

- ungrouped；
- currently-unweighted；
- frozen free genes。

### 2.3 Ten-config canonical mapping corpus

依 config hash／candidate boundary 的預註冊規則選 10 configs，至少涵蓋：

- group 候選邊界；
- residual gene 候選邊界；
- auto／sentinel 值；
- DepthU、GSU、GRVW／VectorWidth、PGR、occupancy 等適用欄位；
- 至少一個可能被 Formocast reject 的 case。

每筆保存：

- raw candidate；
- resolved solution；
- `SizeMapping`／model input；
- 每欄 provenance；
- config hash；
- mapping status／failure reason。

以下欄位不得猜值或用無證據 default：

- occupancy；
- effective GSU；
- `MathClocksUnrolledLoop`；
- unresolved `-1/-2` sentinel；
- 任何 backend-specific required metadata。

Derived mapping 可接受，但必須：

- deterministic、total、reproducible；
- 有 canonical direct／derived path；
- 相同 input 與 size 產生相同 model input；
- 逐欄 parity／round-trip 可稽核；
- dependency 寫入 mapping manifest。

多個 gene values 若映射成完全相同的 Formocast input，視為 model tie，不得捏造 sensitivity。

#### S10R2 historical support-aware／helper-conformance overlay

原S10保持durable negative；S10R1依A32取消為
`cancelled / BLOCKED / not_evaluated / edge=null`，其diagnostic artifacts禁止重用。
新的S10R2在任何Formocast／GFLOPS前執行固定CPU validity-only discovery：

- 每個candidate value分類為`supported_witnessed`、`support_unobserved`或
  `support_proven_absent`；stochastic non-discovery永遠只能是`unobserved`，只有
  complete proof可判`absent`；
- 任一value是unobserved／proven-absent時，該residual gene不具S11 guidance
  eligibility；actual YAML baseline groups／weights／uniform semantics不變，且不阻止
  unrelated genes或entry；
- L0在任何draw前建立complete candidate-atom registry：30 axes的每個exact typed
  value都有deterministic ID、value hash、YAML pointer、source symbol/blob、
  pre-draw roles與priority。`prelocked_candidate_atoms`只由全部eligible residual
  candidate rows機械形成；first／last／`-1/-2`另形成diagnostic target roles，不會
  單獨成為mandatory mapping atoms；
- 固定512-draw chunks。Global必須exact執行32 chunks／16,384 nominal draws，無
  early stop；完成第32 chunk後，才從sealed diagnostic registry中對final
  `support_unobserved` rows依prelocked priority取前15個conditional targets。每個
  activated conditional也exact執行32 chunks／16,384 draws，無result-driven early
  stop或extension；總上限262,144；
- Post-discovery mandatory set機械固定為
  `(prelocked_candidate_atoms ∩ supported_witnessed) ∪
  (always_required_structural_atoms ∩ structurally_witnessed)`；本版第二項為empty。
  Exact-ten使用prelocked greedy set-cover／first-occurrence tie-break，不能在看到
  support後重新挑「source-semantic」atoms；
- Cap內少於10 distinct witnesses、mandatory cover不可行／需超過10 configs，或
  complete proof顯示overall少於10 distinct valid configs，都為
  `inconclusive / FT-INCONCLUSIVE / edge=null`；
- mapping gate是exact ten ×三sizes的A/B parity、完整field provenance、30/30無
  mapping failure；random corpus不需要命中Formocast sentinel；
- deterministic score-blind helper與subsequent mapping/runtime interpretation必須
  使用同一S10R2 native adapter，直接呼叫pinned
  `Formocast::predictedPerformance`與`SolutionIterator::checkSolution`／
  `AllSolutionsIterator::preProblem` queue path。Contract／lock綁native blobs、
  helper symbol/binary hash與host adapter hash；separate oracle只能compare。Verifier
  必須fault-inject helper/path/source/adapter substitutions並證明fail closed；
- sorted exact-ten hashes的indices `0,4,9`仍是三anchors；correctness全過後仍執行
  3 anchors ×3 sizes ×7 repeats =63 noise cells。Locked
  generate／compile／smoke／nonzero correctness可重現失敗使用
  `FT-BLOCKED-CORRECTNESS`。

S10R2完整identity、schedule、selector、helper fixture、outcome matrix、future
contract／lock／artifact／report paths見
[S10R2 design](ductile-origami-warmstart/s10r2-stage1-support-aware-entry-recovery-design.md)。
它已closeout為`inconclusive / FT-INCONCLUSIVE / edge=null`，不再是future edge
source；claim只限該次observed operational valid support。

#### S10R3 bounded-cover／fresh-evidence overlay

A38不重開S10R2，而是新增fresh R3 sibling S10R3。它保留S10R2的三態support、
pre-draw registry、fixed discovery schedule、mandatory-set derivation、native helper、
correctness與noise semantics，但formal evidence全部fresh：

- Fresh registry、disjoint seed namespace與append-only ledger；S10R1 artifacts及
  S10R2 accepted rows、support states、conditional targets、cover、seeds、mapping、
  GPU/noise與decision禁止重用。
- Discovery仍固定global `32×512`、最多15個conditional targets各`32×512`，總上限
  `512 chunks / 262,144 draws`，不得early stop、extension或seed retry。
- Mandatory set仍是
  `prelocked_candidate_atoms ∩ supported_witnessed`。
- Selector固定：

  ```text
  C_greedy = deterministic_greedy_set_cover_v2_bounded_k20的full-cover cardinality
  K        = max(10, C_greedy)
  K_max    = 20
  ```

  Fresh witnesses少於10或`C_greedy>20`為
  `inconclusive / FT-INCONCLUSIVE / edge=null`。`C_greedy`不是minimum cover；labels後
  不得新增solver、draws、seeds或cap。
- Mapping A/B各exact `3K` rows。Anchors是sorted hashes的
  `{0,floor((K-1)/2),K-1}`；correctness仍9 cells、noise仍63 cells。

完整contract、identity、selector、lower-bound disclosure、GPU free-card policy、
outcome matrix與future paths見
[S10R3 design](ductile-origami-warmstart/s10r3-stage1-bounded-cover-entry-recovery-design.md)。
只有post-audited `S10R3:S1_ENTRY_GO`可啟動S11。

### 2.4 Size registry

優先選三個：

- 來自同一 frozen YAML；
- 共享完全相同 search-space hash、groups、candidate order 與 baseline weights；
- 不使用 Formocast score挑選；
- 依事前 workload 規則覆蓋 small-K／transition／large-K 或等價 utilization regimes。

若只有兩個合法 sizes：

- study mode標 `two_regime_pilot`；
- 所有「至少 2/3 sizes」改成「2/2 sizes」；
- claim明確降級。
- 在執行降級版前產生decision packet並停在`blocked-awaiting-user-decision`；user未批准時不得形成entry-gate outgoing edge。

不得拿不同 search space 的第三個 size湊數。

### 2.5 GPU access 與 smoke

D2結束前必須：

- 已排定 MVP期間可用的 gfx942 slot；
- generate／compile／benchmark smoke成功；
- nonzero correctness／validation；
- environment、ROCm、driver、clock／power policy可記錄；
- 能執行 D3–D6 所需的 measurement protocol。

只有「未來可能拿到 GPU」不算通過。

### 2.6 Noise pilot

由 10-config mapping corpus按 canonical config hash預選 3 anchors，不得依 model／GFLOPS選：

1. 每 anchor 在全部 sizes 做 7 次獨立重測；
2. 每次依 actual `reduce_fn` 得 aggregate quality `Q_ar`；
3. 調整 timed iterations，目標為 config-level repeat CV 的 P95 ≤ 0.5%；
4. iteration escalation cap 必須在 treatment benchmark 前鎖定；
5. cap後仍不穩定：D6 `noise_blocked`。

定義：

```text
d_ar        = abs(log(Q_ar) - median_r(log(Q_ar)))
delta_noise = exp(P95({d_ar})) - 1
```

`delta_noise` 在 D5 unblind 前鎖定，用作 D6 median-quality guardrail。

### 2.7 D1–D2 study mode

#### `ready_actual_yaml_guidance`

- Actual frozen YAML 含有可追溯 existing weights。
- 可回答完整 bounded RQ。
- 除非另有 deployment 證據，仍不得稱 production incumbent。

#### `degraded_branch_proxy_only`

- Actual YAML 沒有 weights；
- pinned GEKO commit能在**完全相同** space、groups、candidate order 下只新增 weights；
- 只能回答 GEKO branch-proxy mechanism 問題；
- 完整 RQ記為 `not_evaluated_under_actual_yaml`。

#### `blocked_no_comparable_heuristic`

- Actual weights不存在；
- branch proxy無法只改weights而保持其他條件相同；
- 不得判 existing-heuristic saturation。

### 2.8 D1–D2 hard stop

任一成立即停止 empirical work：

- frozen YAML provenance不足；
- mapping需猜 required metadata；
- actual／proxy candidate order無法對齊；
- D2前沒有已排定 gfx942 slot；
- smoke／correctness失敗；
- 剩餘可工作時間少於5日。

Historical S10 hard access／artifact blocker才輸出[blocker memo](#111-report-paths)。
S10R2已依自己的outcome matrix完成closeout。S10R3的pre-evidence material
operational failure是`BLOCKED`／decision packet；evidence-integrity完整的negative或
inconclusive寫入S10R3 formal report。不得建立假裝執行過的MVP report。

---

## 3. 三種分布與分析單位

### 3.1 `pi_nominal`

Frozen YAML／hook 定義的每個 key 的 product probabilities：

- 有 weight 的 key：依實際 `weight_beta` 轉成 probabilities；
- 無 weight 的 key：uniform；
- existing groups保持其單一 categorical key；
- 尚未經 validity 或 population 去重。

### 3.2 `pi_valid`

單一 nominal draw通過 `valid_fn` 後的 accepted-occurrence distribution：

```text
pi_valid(x) = pi_nominal(x | valid_fn(x) = true)
```

`sample_chunk()` 先保存 valid occurrences，之後 `SearchSpace.sample()` 才加入 `IndividualSet`。所以 duplicate valid occurrences 屬於 `pi_valid` 的 multiplicity，不可先去重再假裝等權。

### 3.3 `Pi_gen0,P0`

令 `P0` 為 Ductile constructor在 frozen search space上解析後的 initial population size；requested value是64，但 runtime可能依 gene cardinality調整。`SearchSpace.sample(P0)` 產生 `P0`-config joint population distribution：

- 先 per-key categorical draw；
- validity filter；
- population內由 `IndividualSet` 去重；
- 同 config 可在不同 populations重現。

`Pi_gen0,P0` 不是 `P0` 個獨立 `pi_valid` draws。本研究：

- 用 `pi_valid` 建 model marginals 與 D5 finite-frame audit；
- 用 exact `pop=P0` CPU replay描述 operational sampler；
- 用 D6 的三個新 populations測 actual endpoint。

### 3.4 Analysis units

- D5：256 個 unique configs；每 config 的所有 size observations綁在一起。
- 三 sizes時有 768 config×size observations，但不是 768 個獨立 workloads。
- D6：一個 `pop=P0` population是 joint realization；三 paired seeds只有三次方向性 evidence。

---

## 4. Model-only valid occurrence frame

### 4.1 Global frame `F_valid`

使用 pinned `sample_chunk` 等價路徑，在加入 `IndividualSet` 前收集 valid occurrences：

- default target／hard cap：8,192 accepted occurrences；
- duplicate occurrences保留；
- 每 occurrence保存 occurrence ID、seed／chunk、raw config、resolved config hash、validity provenance；
- 不因看到 GFLOPS結果追加 occurrences。

可在 4,096 occurrences後依 model-only stability提早停止，但只能在：

- 所有可能 eligible genes 已通過或明確未通過 §5 criteria；
- 兩個預鎖 disjoint halves產生相同 guided-gene set；
- 各 guided gene 的 best／worst pair均一致；
- global `lambda`選擇一致。

否則繼續到8,192 cap。Cap後仍不穩定的 gene維持uniform。

### 4.2 Deduplicated model catalog

依 canonical config hash去重只為節省 mapping／Formocast scoring：

- 每 unique config只需 resolve／score一次；
- 保存 multiplicity `m_i`；
- 保存所有 occurrence IDs；
- analysis時恢復 occurrence multiplicity。

若 complete、scoreable unique catalog少於256：

- 原 D5 design `blocked_or_underpowered`；
- 不得把 duplicate occurrences當不同 configs補足；
- 不得降低256門檻後仍聲稱照原protocol完成。

### 4.3 Model scoring

每 unique config對全部 sizes取得：

- resolved Formocast model input；
- latency／status；
- mapping與scoring time；
- rejection reason；
- score ties；
- model revision。

Whole-config Formocast coverage以 `F_valid` occurrence mass計算，也並報 unique-config coverage。

### 4.4 Conditional top-up

對 eligible residual `(gene g, value v)`：

1. 固定 `X_g=v`；
2. 其他 keys依 `pi_nominal` 抽；
3. 通過同一 `valid_fn`；
4. accepted occurrences保留 multiplicity；
5. 只用於該 `(g,v)` conditional mean；
6. 不進 global frame、whole-ranking audit或 D5 strata。

每 value：

- hard minimum：128 accepted conditional occurrences；
- precision／stability不足時可加到256 hard cap；
- cap後仍不足：該 gene維持uniform。

---

## 5. Model-sensitive residual genes 與 weights

### 5.1 Eligibility

一個 key必須同時是：

- frozen free key；
- ungrouped；
- currently unweighted；
- cardinality > 1；
- direct或deterministic derived mapping complete；
- 每 candidate value model coverage ≥95%。

Existing `group_i` 一律不 eligible。

### 5.2 Model benefit

對每 size `s`：

```text
r_s(x) = Formocast latency percentile rank in F_valid  # 0 is best
b_s(x) = 1 - r_s(x)                                   # larger is better
```

依 actual YAML objective聚合：

```text
b(x) = actual_reduce_fn({b_s(x)})
```

若 `reduce_fn` 與 benefit aggregation 語意無法無歧義對齊，D1–D2 必須在 protocol lock中寫出 resolved function與單元測試；不可由名稱猜測。

### 5.3 Shrinkage conditional mean

以 accepted-occurrence multiplicity計權：

```text
mu_gv = (sum b_i + alpha * global_mean_g) / (n_gv + alpha)
alpha = 32
```

- `alpha=32` 是 minimum support 128 的 25%；
- support增加到256時仍固定32；
- global frame與對應 conditional top-up使用同一 target conditional distribution；
- top-up只補該 cell，不當 whole-frame row。

### 5.4 Model-sensitive hard criteria

定義：

```text
S_g = max_v(mu_gv) - min_v(mu_gv)
```

只有全部成立才 guidance：

1. 每 value accepted-occurrence support ≥128；
2. 每 value model coverage ≥95%；
3. `S_g ≥ 0.05` percentile-benefit units；
4. 2,000 次 within-gene permutation，observed `S_g` > null P95；
5. 2,000 次 model-only bootstrap 中，固定 best-vs-worst contrast 的 95% interval half-width ≤0.025；
6. 同一 best／worst pair重現率 ≥90%；
7. best-vs-worst方向至少2/3 sizes一致；two-regime時2/2。

判讀：

- 90%以上：eligible for guidance；
- 80–90%：`borderline_model_sensitivity`，維持uniform；
- 80%以下：`unstable`，維持uniform。

若 support 128未過 precision／stability，可加到256；仍未過不得降低 criteria。

### 5.5 Probability construction

固定：

```text
epsilon = 0.20
alpha   = 32
```

對 guided gene：

```text
q_g(v) = exp(lambda * (mu_gv - min_v(mu_gv))) / Z_g
p_g(v) = epsilon / |V_g| + (1 - epsilon) * q_g(v)
Hnorm  = H(p_g) / log(|V_g|)
```

所有 guided genes共用單一 global `lambda`：

- 固定 grid `{0, 0.25, 0.50, ..., 8.00}`；
- 選最大 `lambda`，使所有 guided genes 的 `Hnorm ≥0.80`；
- 完全不讀 real GFLOPS；
- 若無 gene通過或 `lambda=0`，factorized guidance停止，不進 D5 treatment gate。

### 5.6 Hook cost conversion

依 frozen actual `weight_beta`：

```text
w_g(v) = -log(p_g(v)) / weight_beta
```

要求：

- `SearchSpace.map[g]` candidate order逐項等於 weight vector order；
- probability round-trip與normalization測試通過；
- NaN／Inf／missing value fail closed；
- guided gene list、`lambda`、weights、candidate order與hash在 real GFLOPS前鎖定。

### 5.7 Same-entropy shuffled control

- 所有 existing groups／weights完全不動；
- 對每個 guided residual gene，將同一 probability multiset做預鎖 deterministic non-identity label permutation；
- 保持 candidate cardinality、nominal entropy、`epsilon` floor與 guided gene數；
- permutation seeds／bundles在 real GFLOPS前鎖定；
- validity／dedup後的 realized entropy另行報告。

---

## 6. D3–D5 real-score finite-frame audit

### 6.1 Real-score pool

從 deduplicated model catalog抽固定256 unique configs。

建立 strata：

1. 對 scoreable configs依 aggregate Formocast score排序；
2. 依 occurrence multiplicity切成10個 weighted deciles；
3. sampling-only ties用 canonical config hash stable tie-break；
4. metric計算保留真實 ties／midranks；
5. unscored／rejected configs獨立為第11 stratum，不可靜默刪除。

Allocation：

- 依各 stratum occurrence mass做 largest-remainder proportional allocation至256；
- 每個非空 stratum至少1個；
- 若 quota > unique `N_h`，該層 census，剩餘 quota按同一規則重分；
- stratum內對 unique config做 simple random sampling without replacement；
- 保存 `stratum_id, N_h, n_h, rho_i=n_h/N_h`。

### 6.2 Measurement

每個 selected config在全部 sizes：

- generate／compile／benchmark；
- 使用鎖定 warmup／timed iterations；
- 保存 raw timings、GFLOPS、correctness、failure reason；
- arm／config順序依預鎖 randomized schedule；
- measurement failure不事後 replacement。

三 sizes時：

- 256 unique configs；
- 768 config×size observations；
- primary bootstrap／permutation單位仍是 config。

### 6.3 Baseline design weight

對 selected unique config `i`：

```text
W_0i = m_i / rho_i
```

其中：

- `m_i`：`F_valid` occurrence multiplicity；
- `rho_i`：stratified sampling inclusion probability。

Primary estimand只限 frozen `F_valid` empirical accepted-occurrence frame。

### 6.4 Alternative prior mass

對 alternative arm `a`：

```text
r_a(x_i) = pi_nominal,a(x_i) / pi_nominal,0(x_i)
W_ai     = W_0i * r_a(x_i)

M_a(T) = sum_i W_ai * I(x_i in real_top_decile_T)
         / sum_i W_ai
```

- Validity function相同，因此未知 valid normalization在 self-normalization中抵消；
- preserved groups在 density ratio中相消；
- `epsilon` floor確保 baseline support overlap；
- YAML baseline `r_0=1`。

每 arm必報：

```text
importance_ESS = (sum W_ai)^2 / sum(W_ai^2)
max_normalized_weight
```

若 `importance_ESS < 25`，該 arm prior-mass gate為 `inconclusive`，不得以 point estimate通過。

### 6.5 Metrics

Primary：

- design-weighted aggregate Spearman（weighted midranks後的 weighted Pearson）；
- design-weighted real top-decile cutoff；
- top-decile overlap／lift；
- arm-specific real-top-decile prior mass。

Secondary：

- raw unweighted versions；
- per-size Spearman／lift；
- Kendall；
- ties／distinct score counts；
- model／measurement coverage；
- occurrence concentration、max multiplicity、Kish effective sample size；
- compile／mapping／scoring cost。

Bootstrap：

- 在各 stratum內以 config為block重抽；
- 同一 config的全部 size outcomes一起移動；
- 不把768 rows視為獨立。

Permutation null：

- 以 config為整體 permutation unit；
- 保留同 config的全部 size outcomes；
- 規則與次數在 protocol lock中保存。

### 6.6 Coverage／rejection gate

同時要求：

- `F_valid` occurrence-mass complete Formocast coverage ≥95%；
- D5 planned real measurements coverage ≥95%；
- unscored／failed rows保留；
- 對 planned count ≥10 的 gene/value，rejection rate不得比 overall高超過10 percentage points。

低於門檻：

- 不使用 missing-weight adjustment救回；
- 記 `FT-INCONCLUSIVE` 或 mapping／model coverage failure；
- 不進 D6。

### 6.7 D5 pass／borderline／fail

全部成立才 `D5_PASS`：

1. Coverage／rejection gate通過；
2. aggregate Spearman ≥0.25；
3. aggregate top-decile lift ≥2× random；
4. 至少2/3 sizes的 Formocast ranking方向為正；two-regime時2/2；
5. existing／proxy + Formocast residual prior mass高於 existing／proxy baseline；
6. Formocast prior mass高於 same-entropy shuffled；
7. 每個相關 arm importance ESS ≥25；
8. 沒有 correctness failure。

`D5_BORDERLINE_INCONCLUSIVE`：

- Spearman在 `[0.20, 0.25)`；或
- lift在 `[1.5, 2.0)`；或
- support／ESS／coverage只差門檻但不能無偏補足。

Borderline不進 D6；不得調參後重用同 pool。

`D5_FAIL`：

- 低於 borderline；或
- factorized prior不勝 baseline／shuffled；或
- cross-fitted oracle顯示 hook expressiveness不足。

所有 threshold都是 engineering triage，不是統計保證。報告必須包含 raw overlap counts、ties、coverage、permutation null與 bootstrap interval。

### 6.8 Cross-fitted oracle diagnosis

使用5-fold config-level cross-fitting：

- fold assignment在 real scores解封前，依 config hash與D5 stratum固定；
- 同 config的所有 occurrences／sizes在同一 fold；
- occurrence multiplicity用於 fold balance與 analysis；
- 每 fold用其他80% configs建立 real-score oracle marginals；
- 只在 held-out fold判斷 factorized main effects；
- training fold缺 candidate support時標 `not_estimable`，不得用 model value補。

Oracle只用來區分：

- Formocast marginalization失敗；
- factorized hook expressiveness不足。

Oracle不進 required D6 arms。GPU有餘裕時才允許 outcome-informed、`diagnostic_only` 的 full-pool oracle arm；它不參與 success claim。

---

## 7. D6 actual Gen0 endpoint

只有 `D5_PASS` 才執行。

### 7.1 Formal arms

#### Arm U — Uniform／no guidance

- 保留 group結構；
- 停用所有 optional sampling weights；
- 只作 no-guidance ablation。

#### Arm G — Existing guidance／GEKO proxy

- `ready_actual_yaml_guidance`：使用 actual YAML weights。
- `degraded_branch_proxy_only`：使用 pinned、space-equivalent GEKO branch proxy。

#### Arm F — Existing + Formocast residual

- Arm G完全不變；
- 只新增 §5 通過的 residual-gene weights。

#### Arm S — Existing + same-entropy shuffled residual

- Arm G完全不變；
- residual probabilities使用 §5.7 permutation bundle。

### 7.2 GA configuration

固定：

```text
requested pop_size = 64
n_gen    = 1
period   = 0
seeds    = 3 paired sampler seeds
```

在 formal proposals前必須保存 `resolved_initial_pop_size=P0` 與 constructor decision：

- 若 `P0=64`，照原 protocol執行；
- 若 `P0!=64`，在任何 real labels前 append amendment，所有 arms共用同一 `P0`，replay／proposal counts／resource caps與 claim wording全部按 `P0`更新；
- 不得在看到 treatment quality後修改 `P0`；
- 各代 actual population size都須記錄，不能用 nominal 64推算 evaluation成本。

Repo code已查核：

- weights只用於 initial `space.sample(..., p=self.probs)`；
- `n_gen=1` 只執行一次 population evaluation；
- mutation新值在後續仍均勻，但本 MVP不進後續世代。

### 7.3 Proposal lock 與 benchmark union

1. 先為全部 `arm × seed`產生 `P0` proposal slots；
2. 保存 raw indices、resolved configs、config hashes與 multiplicity；
3. 每個 config canonical serialize；
4. population重現性用「config hashes排序後的 canonicalized config-set hash」比較；
5. 不依賴 set-backed population iteration order；
6. 所有 proposals hash-lock後才 benchmark；
7. 對跨 arms／seeds 的 deduplicated union量測一次；
8. 結果依 proposal multiplicity回填所有 slots。

`ordering mismatch`只指：

- `SearchSpace.map` candidate order；
- weight vector order；
- resolved candidate mapping；

不指 Python set iteration order。

### 7.4 CPU sampler replay envelope

Benchmark前，每個正式 arm執行2,000個 exact `SearchSpace.sample(P0)` replay populations：

- 使用與三個 formal seeds分離的 prelocked seeds；
- pin `n_jobs`、sampler revision、validity code hash；
- 保存 valid attempts、duplicates、fill failures；
- per-gene realized frequencies；
- normalized entropy；
- population diversity；
- pairwise Hamming diversity。

定義：

```text
T_freq = max_g 0.5 * sum_v abs(
           formal_frequency_g(v) - replay_mean_frequency_g(v)
         )
```

從 replay pseudo-panels建立三-seed panel的 P99：

- frequency discrepancy；
- entropy；
- diversity；
- invalid／duplicate／attempt counts。

判讀：

- same seed／same weights／same space的 canonicalized config-set hash不一致：`FT-PLUMBING`；
- `SearchSpace.map`／weight order不一致：`FT-PLUMBING`；
- 單一 formal seed超出 P99：`plumbing_suspect`，先audit並做含／不含該seed的敏感度；
- 同 arm至少2/3 seeds超出 P99：arm invalid，不得解讀 quality；
- realization正常但quality無增益：`FT-GEN0-MECHANISM`，不叫 plumbing。

### 7.5 Endpoint

D5 weighted audit定義 real top-decile aggregate-quality cutoff `T_D5`。

Primary：

```text
Gen0 top-decile hit rate
= proposal slots with aggregate quality >= T_D5
  / valid proposal slots
```

Secondary：

- population median aggregate quality；
- best aggregate quality；
- unique count／duplicate count；
- validity／correctness；
- realized entropy／diversity；
- 對 D5 pool的 overlap；
- mapping／compile／benchmark cost。

Best完全是 secondary，不可替代 median guardrail。

### 7.6 Median-quality noise guardrail

每 paired seed比較 Arm F 與 Arm G：

```text
median_quality_F / median_quality_G >= 1 / (1 + delta_noise)
```

至少2/3 seeds通過。

`delta_noise`只可來自 §2.6 noise pilot，不得看 arm results後修改。

### 7.7 Mechanism-positive criteria

全部成立才 `D6_MECHANISM_POSITIVE`：

1. Arm F 相對 Arm G 的 top-decile hit-rate paired delta，至少2/3 seeds >0；
2. Arm F 相對 Arm S 的 paired delta，至少2/3 seeds >0；
3. Median-quality noise guardrail至少2/3 seeds通過；
4. proposal set hash、candidate order、weights與space hashes一致；
5. replay envelope無systematic anomaly；
6. 無新增 validity／correctness failure。

三 seeds只支持 directional mechanism evidence，不執行顯著性檢定，不宣稱 speedup。

---

## 8. Operational failure mapping

實驗報告依 research charter的 canonical taxonomy：

| 觀察 | 結果 ID |
| --- | --- |
| 無 GPU／YAML／artifact | `FT-BLOCKED-ACCESS` |
| Mapping需猜值或 parity失敗 | `FT-BLOCKED-MAPPING` |
| Locked generate／compile／smoke／nonzero correctness可重現失敗 | `FT-BLOCKED-CORRECTNESS` |
| Whole ranking gate失敗 | `FT-MODEL-RANK` |
| Whole rank好、model marginal差、oracle好 | `FT-MODEL-MARGINAL` |
| Cross-fitted oracle也差 | `FT-HOOK-EXPRESSIVENESS` |
| Target／realized frequencies或candidate order不符 | `FT-PLUMBING` |
| Realization正常但Gen0無增益 | `FT-GEN0-MECHANISM` |
| Formocast不勝 existing／proxy | `FT-HEURISTIC-SATURATION` |
| Formocast不勝 shuffled | `FT-ENTROPY-ONLY` |
| Gen0好但後續未知 | `FT-WASHOUT-UNTESTED` |
| Noise／support／ESS／coverage不足 | `FT-INCONCLUSIVE` |

不得以「模型沒用」取代層級判讀。

---

## 9. D1–D7 schedule

### D1 — Artifact 與 environment

- Frozen YAML provenance／hash；
- source revision lock；
- search-space／groups／weights manifest；
- gfx942 booking；
- generate／compile／benchmark smoke。

### D2 — Mapping、sizes 與 protocol lock

- 10-config mapping corpus；
- size registry；
- noise pilot；
- study mode；
- model-only／replay seeds；
- 所有 model-sensitive constants與analysis rules lock。

**D2 hard decision：**`GO`、`DEGRADED_PROXY` 或 `BLOCKED`。`DEGRADED_PROXY`與two-regime mode都要先通過parent-level user downgrade review，不能自動解鎖下一checkpoint。

### D3 — Model-only frame

- `F_valid` accepted occurrences；
- deduplicated catalog；
- Formocast scoring；
- conditional top-ups；
- model-sensitive gene decisions；
- weights／shuffled bundle hash-lock。

任何 real GFLOPS artifact在此 lock完成前都不得建立或解封。

### D4 — Real-score pool

- D5 strata／inclusion manifest；
- 256-config generate／compile／benchmark；
- correctness與measurement coverage；
- raw result freeze。

### D5 — Audit 與 decision

- Weighted ranking／lift；
- prior-mass density-ratio analysis；
- importance ESS；
- cross-fitted oracle；
- `PASS`、`BORDERLINE`、`FAIL` 或 `INCONCLUSIVE`。

只有 `PASS` 進 D6。

### D6 — Actual Gen0

- 2,000-population CPU replay per arm；
- formal proposal lock；
- benchmark union；
- endpoint／guardrail／failure attribution。

### D7 — Report

- Positive、negative 或 inconclusive：MVP report；
- D1–D2 blocked：blocker memo；
- 不建立空白 report；
- 依各自formal report與checkpoint closeout規則完成；不得以stage rollup取代未closeout的checkpoint。

---

## 10. Artifact contract

Logical artifacts至少包括：

### Protocol／environment

- `study-manifest.json`
- `protocol-lock.json`
- `environment-and-revision-manifest.json`
- `amendments.jsonl`

### Frozen inputs

- `frozen-generated.yaml`
- `frozen-generated.sha256`
- `yaml-provenance.json`
- `search-space-manifest.json`
- `size-registry.json`

### Mapping／model-only

- `canonical-mapping-10.jsonl`
- `valid-occurrences.parquet`
- `resolved-config-catalog.parquet`
- `model-scores.parquet`
- `conditional-topups.parquet`
- `model-sensitive-gene-decisions.json`

### Weights／controls

- `marginals.parquet`
- `weights.yaml`
- `shuffled-permutation-manifest.json`
- `probability-roundtrip-results.json`

### D5

- `real-score-pool-manifest.json`
- `real-scores.parquet`
- `oracle-fold-manifest.json`
- `crossfit-oracle-results.parquet`
- `d5-gate-summary.json`

### D6

- `sampler-replay-summary.parquet`
- `gen0-proposals.jsonl`
- `gen0-proposal-lock.sha256`
- `gen0-deduplicated-union.parquet`
- `gen0-results.parquet`
- `d6-decision.json`

每個 artifact須帶：

- schema version；
- source／protocol revision；
- input hashes；
- environment ID；
- creation timestamp；
- complete／partial／rejected status；
- failure reason。

大型 raw artifacts可存在外部 artifact root；repo report保存 immutable URI、hash、schema與重現指令。

---

## 11. Report lifecycle 與允許措辭

### 11.1 Report paths

D1–D2 access／artifact／mapping blocked：

`study_docs/research/ductile-origami-warmstart/reports/gen0-factorization-blocker-memo.md`

此memo只屬historical S10 hard blocker。S10R1依A32取消，沒有scientific report。
S10R2 positive、negative或inconclusive的唯一report是：

`study_docs/research/ductile-origami-warmstart/reports/staged/s10r2-stage1-support-aware-entry-report.md`

S10R3 positive、negative或inconclusive的唯一report是：

`study_docs/research/ductile-origami-warmstart/reports/staged/s10r3-stage1-bounded-cover-entry-report.md`

D5 或 D6 已形成 empirical evidence，不論 positive、negative 或 inconclusive：

`study_docs/research/ductile-origami-warmstart/reports/gen0-factorization-mvp-report.md`

現在不建立空白檔。

### 11.2 Positive wording

只允許：

> 在指定 frozen YAML、gfx942 non-StreamK、一種 dtype/layout、指定 sizes、bounded D5 audit 與三個 paired sampler seeds 下，Formocast-factorized residual guidance 對 Gen0 candidate quality 提供方向性增量，值得擴大驗證。

### 11.3 Negative wording

必須使用 §8 result ID，說明：

- 哪個 gate失敗；
- 證據支持什麼；
- 不能支持什麼；
- 是否值得後續改 predictor、改 hook或停止。

### 11.4 Proxy wording

`degraded_branch_proxy_only` 必須包含：

- pinned GEKO commit；
- exact space／order parity evidence；
- `branch proxy` 字樣；
- `primary RQ not evaluated under actual YAML`。

禁止：

- incumbent；
- deployed；
- production baseline；
- beats original Ductile。

---

## 12. Current execution checklist

S10R2 historical terminal record：

- [x] Frozen generated YAML with provenance
- [x] Pinned Ductile／GEKO／TensileLite／Formocast revisions
- [x] Actual `group_i`／weights／candidate order confirmed
- [x] Actual `soo/reduce_fn` confirmed
- [x] S10R2 cumulative resource preflight and durable contract／lock sealed
- [x] CPU validity-only support classification complete within 262,144 nominal draws
- [ ] 10-config mapping parity：`not_activated_by_FT-INCONCLUSIVE`
- [x] Exact three same-space sizes locked
- [ ] Separate sentinel／runtime helper conformance：`not_activated_by_gate`
- [ ] gfx942 execution：`not_activated_by_gate`
- [ ] Three-anchor smoke／correctness：`not_activated_by_gate`
- [ ] 63-cell noise pilot：`not_activated_by_gate`
- [x] Study mode and evidence boundary recorded
- [x] Real GFLOPS remained sealed

S10R2已形成可重現的`inconclusive / FT-INCONCLUSIVE / edge=null`。未勾選項目是依
frozen gate合法未啟動，不是可補跑的缺漏；S11沒有eligibility。

S10R3 current state：

- [x] A38 scientific/design authority approved
- [ ] Exact-path A38 authority commit and post-commit audit
- [ ] Two execution plans and pre-label adversarial contract audit
- [ ] Durable S10R3 contract／effective lock seal
- [ ] Fresh support discovery and bounded exact-K decision
- [ ] Mapping A/B and native helper conformance
- [ ] GPU correctness and noise, if activated by prior gates
- [ ] Fresh verification, terminal report, closeout commit and post-audit

未完成項目不表示已產生partial scientific evidence。任何formal draw、Formocast或GPU
label都必須等待effective lock。

---

## Part II — Stage 2：Short-Horizon Persistence Protocol

Stage 2不是無條件延長。只有 Stage 1 `D6_MECHANISM_POSITIVE` 才可建立 Stage 2 lock artifact。

## 13. Stage 2 objective 與 entry

### 13.1 Objective

> Gen0 的增量是否能穿過後續 mutation／selection transitions，在固定10-generation horizon中改善 early-search quality-vs-complete-evaluations，而不是被 existing guidance快速追平？

這一階段測 **persistence／early evaluation efficiency**，不是完整 convergence或 system speedup。

### 13.2 Entry requirements

全部成立才 `S2_READY`：

- Stage 1 `D6_MECHANISM_POSITIVE`；
- mapping、plumbing、correctness與sampler replay無未解 anomaly；
- frozen YAML、space、sizes、groups、weights、model revision、guided genes、`alpha/epsilon/lambda`、`reduce_fn`全部不變；
- 五個 Stage 2 formal paired seeds在 Stage 1 unblind前預鎖，或由 protocol hash deterministic派生，且與 Stage 1 seeds完全 disjoint；
- 完整 G／F／S × 5 seeds × H10 GPU與時間 cap已確認；
- 保留至少一個 report工作日與10% measurement failure buffer；
- requested／resolved initial population與 adaptive population semantics已記錄。

Stage 1三個 selected seeds可延長作 continuity diagnostic，但：

- 不計入 Stage 2五個 formal pairs；
- 不與 fresh seeds混報成八個 independent seeds；
- 不參與任何 4/5、3/5 gate。

### 13.3 Formal arms

- **G：**existing YAML guidance／GEKO branch proxy。
- **F：**G + frozen Formocast residual guidance。
- **S：**G + frozen same-entropy shuffled residual guidance。

Uniform arm已在 Stage 1完成 no-guidance ablation，不再支付10-generation成本。

---

## 14. Stage 2 fixed-horizon execution

### 14.1 Configuration

```text
n_gen       = 10
period      = 0
formal arms = G / F / S
paired seeds = 5 fresh seeds
```

- 第1代是 initial population evaluation；
- 第2–10代提供9次後續 transitions；
- 不修改 size sampling、per-size iterations、fitness、mutation、selection或survival；
- 每代保存 proposal set、complete fitness matrix、best-so-far、population size、diversity、decay mode、invalid／duplicate／fill status。

### 14.2 Generation-5 checkpoint

Generation 5只可作：

- environment／resource health checkpoint；
- checkpoint integrity與resume parity；
- 最終 report中的 immediate-washout descriptive estimand。

禁止：

- 解封 G／F／S comparative quality後決定是否跑 generation 6–10；
- H5漂亮才延長；
- H5不漂亮就停、卻仍把H10 survivors當正式樣本。

正式 Stage 2從 entry即承諾 H10。若資源事前只夠H5，只能另標：

`S2_H5_RESOURCE_BOUNDED_PILOT`

提出此downgrade時必須先產生decision packet並停在`blocked-awaiting-user-decision`。

它不能通過正式 Stage 2，也不能進 Stage 3。

### 14.3 Checkpoint／resume

若分段執行：

- 先通過 continuous-vs-resume equivalence test；
- checkpoint保存 population、old population、RNG、stats、decay state、evaluation count與lineage hashes；
- resume不得 reseed或重建population；
- paired G／F／S blocks在相近 environment epoch執行。

Parity無法證明時改用 continuous H10 run。

### 14.4 Complete candidate evaluation

一個 candidate只有全部成立才計入 primary evaluation axis：

- 全部鎖定 sizes完成；
- correctness通過；
- 依 frozen `reduce_fn`可產生 aggregate quality；
- config identity與arm/seed lineage完整。

Compile failure、缺 size或invalid仍須保存，但不能當作低成本「已完成 evaluation」。

### 14.5 Prelocked support `U_floor`

Stage 2 entry、任何 Stage 2 labels產生前，依 Stage 1 telemetry、resolved population、complete-evaluation rate與 frozen GA semantics鎖定：

```text
U_floor = 每個 arm × fresh seed 在 Gen0 後
          必須提供的共同 complete-evaluation support
```

要求：

- Primary一律積分到同一 `U_floor`；
- 任一 formal run未達 `U_floor` → `FT-EVALUATION-SUPPORT`／inconclusive；
- 不得事後下修；
- observed per-pair minimum只作support報告與預註冊敏感度分析。

---

## 15. Stage 2 estimands、gate 與 failure

### 15.1 Primary AUC

對 arm `a`、fresh paired seed `r`：

```text
Q_a,r(u)
= Gen0 結束後新增 u 個 complete evaluations時，
  截至當下的 best-so-far aggregate quality

A_a,r
= (1 / U_floor) * integral[0,U_floor] log(Q_a,r(u)) du
```

- 使用 generation-end right-continuous step function；
- 不使用 candidate／set iteration order製造 batch內假 anytime曲線。

Primary paired deltas：

```text
Delta_FG,r = A_F,r - A_G,r
Delta_FS,r = A_F,r - A_S,r
```

### 15.2 Stage 2 positive gate

`S2_DIRECTIONAL_PERSISTENCE_POSITIVE` 要求全部成立：

1. 五個 fresh paired panels均有效且達 `U_floor`；
2. `Delta_FG > 0` 至少4/5，且 paired median >0；
3. `Delta_FS > 0` 至少4/5，且 paired median >0；
4. H10／`U_floor` endpoint的 F best-so-far > G 至少3/5；
5. Final independently verified aggregate quality：

   ```text
   Q_F / Q_G >= 1 / (1 + delta_noise)
   ```

   至少4/5；
6. 無 correctness、plumbing、mapping或 systematic fill failure。

Diversity是 diagnostic。只有當 decline伴隨：

- 未達 `U_floor`；
- population fill failure；或
- final non-inferiority失敗；

才構成 premature-convergence evidence。

### 15.3 Secondary／diagnostic metrics

- H5 immediate persistence／washout；
- Gen1／3／5／10 trajectory；
- D5預鎖 target的 right-censored time-to-target；
- RMST through `U_floor`；
- target achievement；
- raw generation-10 outcome；
- diversity／per-gene diversity；
- population decay、invalid、duplicates；
- 由固定H10 trace重建的 counterfactual `period=5` stop point。

Counterfactual natural stop只作 diagnostic，不是實際wall-time證據。

### 15.4 Stage 2 failure IDs

- `FT-PERSISTENCE-WASHOUT`：Gen0 positive，但 F-G／F-S AUC或late retention失敗。
- `FT-SHORT-HORIZON-REGRESSION`：AUC正向，但 final verified non-inferiority失敗。
- `FT-EVALUATION-SUPPORT`：formal run未達事前 `U_floor`。
- `FT-ENTROPY-ONLY`：F不勝S。
- `FT-PLUMBING`、`FT-INCONCLUSIVE` 與`FT-BLOCKED-CORRECTNESS`沿用 Stage 1。

Stage 1的 `FT-WASHOUT-UNTESTED` 在 Stage 2結束後必須改成具體結果。

### 15.5 Stage 2 time／resource planning

- hands-on target：4工作日；
- planning threshold：5工作日，包含分析與decision report；
- target／threshold不是完成承諾或automatic stop；跨越時record＋notify後繼續完整
  workload。只有A37 material condition成立才pause，不能以H5、縮arms或縮seeds
  保留原claim；
- entry前依 actual resolved population、adaptive decay與 `C` sizes鎖 proposal與 candidate×size request cap；
- nominal `3×5×10×64` 只能作 requested-population參考，不是正式GPU cap；
- 不得只完成部分 arms／seeds後仍判 positive。

Report：

`study_docs/research/ductile-origami-warmstart/reports/short-horizon-persistence-report.md`

---

## Part III — Stage 3：Bounded Held-Out Regime Replication

## 16. Stage 3 entry、freeze 與 clusters

### 16.1 Entry

只有正式 `S2_DIRECTIONAL_PERSISTENCE_POSITIVE` 可進 Stage 3。

`S2_H5_RESOURCE_BOUNDED_PILOT` 不具 entry權。

### 16.2 Cluster registry

在任何 Stage 3 model／real scores前鎖定：

- 兩個新 fixed-MT／fixed-MTDU clusters；
- 每 cluster恰好兩個、共享相同 search space的 sizes；
- 同 gfx942、non-StreamK、dtype/layout；
- selection provenance與非Formocast、非結果導向規則；
- 一個 optional technical reserve cluster（若資源允許）。

Stage 1／2 cluster是 development，不算 held-out。

Technical reserve只能替換：

- access不可用；
- artifact損壞；
- mapping無法建立；

不能因 D5／GA結果不好而替換。

### 16.3 Frozen procedure

從 Stage 2凍結：

- Formocast revision與mapping；
- eligibility／sensitivity algorithm；
- `alpha=32`、`epsilon=0.20`；
- lambda grid、entropy／support／coverage thresholds；
- factorization與shuffle；
- D5 sampling／analysis／oracle；
- Stage 2 AUC、`U_floor`決定規則與gates；
- arms、H10與failure taxonomy；
- source／protocol／analysis hashes。

新 cluster可由同一 label-blind deterministic algorithm輸出不同：

- eligible gene list；
- model-only marginals；
- lambda結果；
- weights。

這不算 retuning。看到該 cluster real labels後的 manual exception會使它降為 development，失去 held-out資格。

---

## 17. Stage 3 per-cluster protocol 與 gate

### 17.1 Per-cluster execution

每個預註冊 cluster：

1. mapping／access／noise gate；
2. model-only frame與 frozen guidance algorithm；
3. 256 unique configs ×2 sizes 的 D5-equivalent audit；
4. D5 fail／inconclusive仍保留在兩-cluster denominator，但不跑GA；
5. D5 pass才執行：
   - G／F／S；
   - `n_gen=10, period=0`；
   - 3個 fresh paired seeds；
   - Stage 2相同 AUC、support、late retention、non-inferiority與correctness rules。

### 17.2 Bounded replication positive

`S3_BOUNDED_REPLICATION_POSITIVE` 要求：

- 2/2 clusters無 outcome-driven amendment；
- 2/2 D5 pass；
- 每 cluster F-G與F-S AUC至少2/3 seeds正；
- 每 cluster H10 late retention至少2/3正；
- 每 cluster final verified non-inferiority至少2/3；
- 無 correctness／plumbing failure。

判讀：

- 一正一負：`FT-REGIME-HETEROGENEITY`；
- 兩者都負：bounded replication否證；
- 任一 access／mapping blocked：整體 inconclusive；
- 只完成一個 cluster：只能在user事前批准downgrade後稱`single-cluster transfer pilot`，且不能通過本checkpoint或解鎖任何原定downstream edge。

兩個 sizes是同一 cluster內 repeated conditions，不是兩個 independent generalization units。

### 17.3 Stage 3 time／resource planning

- planning threshold：7工作日；
- threshold不是完成承諾或entry debit；entry preflight保留S30／S31同lineage已知
  usage與measurement boundary作best-effort provenance；
- entry前鎖完整兩-cluster D5與GA budget；
- GPU planning estimate依Stage 2實際消耗與兩-cluster request估算，不靠cache／
  dedup的樂觀節省啟動；
- 保留 report工作日與10% failure buffer。

Report：

`study_docs/research/ductile-origami-warmstart/reports/bounded-regime-replication-report.md`

---

## Part IV — Stage 4：Conditional Learned Residual Surrogate

## 18. Stage 4 trigger 與 data gate

### 18.1 可啟動 patterns

只有 predictor-specific failure且 cross-fitted oracle支持 factorized main effects時可啟動，例如：

- `FT-MODEL-RANK`，但 oracle ranking／prior mass穩定；
- `FT-MODEL-MARGINAL`，且 oracle明顯優於 G／shuffled；
- Stage 3 predictor heterogeneity，但失敗 cluster的 oracle仍支持同一 hook。

### 18.2 不得啟動

- `FT-BLOCKED-ACCESS`／`FT-BLOCKED-MAPPING`／`FT-BLOCKED-CORRECTNESS`；
- `FT-HOOK-EXPRESSIVENESS`；
- `FT-PLUMBING`；
- `FT-GEN0-MECHANISM`；
- `FT-PERSISTENCE-WASHOUT`；
- premature convergence／short-horizon regression；
- `FT-HEURISTIC-SATURATION`；
- 單純 noise／coverage不足。

更換 predictor不能修復上述問題。

### 18.3 Formal data floor

至少：

- 4個 independent search-space clusters；
- 每 cluster ≥256 unique measured configs；
- 每 cluster ≥2 sizes；
- 總計 ≥1,024 unique configs／2,048 config×size labels；
- inclusion probabilities、correctness、mapping與coverage完整。

若已有3個合格 clusters，可在 mentor另批資源與5日cap內新增**最多一個** prospective sealed fourth cluster：

- selection rule與cluster ID在labels前鎖定；
- 不依前三clusters結果挑容易成功的regime；
- 只取得label pool，不跑GA；
- 第四cluster labels不得回流調參後再當test。

若現有少於3個，或第四cluster無法在cap內取得：

`FT-SURROGATE-DATA-INSUFFICIENT`

不得補收2–3個clusters、不得row-random split、不得把sizes當clusters。

---

## 19. Stage 4 model／split／claim contract

### 19.1 Research question

> Learned residual predictor能否在完全 unseen cluster中，恢復 Formocast未捕捉、但 oracle顯示可 factorize的效能訊號？

### 19.2 Model boundary

- 唯一model是inclusion-weighted ridge residual correction；
- target固定為`log(real latency) - log(Formocast latency)`；
- `ridge_lambda` grid固定為`{1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100}`；
- intercept不penalize；
- 不做model zoo；
- factorization與hook沿用Stage 1 frozen algorithm。

Feature manifest只能包含：

- label-blind problem/config/gene fields；
- Formocast inputs；
- model-only outputs；
- 在全部qualified clusters都有完整deterministic mapping的欄位。

禁止features：

- real scores或由real score衍生的欄位；
- oracle outputs；
- cluster ID、result ID或任何hash；
- outcome-derived selection、coverage、rank或failure features。

Preprocessing：

- continuous transform／imputation／scaling只fit當前outer-training data；
- categorical one-hot只使用training categories，另有explicit unknown bucket；
- outer-test不參與feature selection、preprocessing或calibration。

Inner model selection：

- 每個validation cluster計算inclusion-weighted residual MSE；
- objective是各validation cluster MSE的equal-cluster mean；
- loss相同時選較大的`ridge_lambda`。

### 19.3 Split invariants

- Outer：leave-one-entire-cluster-out；
- Inner：只在 outer-training clusters做 cluster-grouped selection；
- 同 cluster的sizes、repeats、duplicates、derived rows都在同 fold；
- preprocessing、feature selection、calibration只fit training data；
- D5 inclusion weights帶入training與evaluation；
- 禁止 random row split。

若恰有3個既有＋1個 prospective sealed cluster：

- Primary：前三clusters完成model／hyperparameter selection後，第四cluster作untouched prospective test，且只有第四cluster判primary gate；
- LOCO只作 secondary sensitivity。

否則：

- 所有LOCO outer clusters都是primary held-out units；
- 每個primary unit都必須獨立通過全部§19.4 gates；
- 不得跨units平均救回。

### 19.4 Stage 4 endpoint

每個parent-designated primary held-out unit都分別判以下三項。

#### Ranking gate

- 使用frozen inclusion/design weights計算aggregate weighted Spearman；
- prediction orientation是`-log(predicted latency)`；
- real orientation是`log(aggregate quality)`；
- learned必須strictly勝Formocast。

#### Prior-mass gate

- 使用§6.4相同的self-normalized real-top-decile prior mass`M_a(T)`；
- learned factorized prior必須strictly同時勝Formocast-factorized prior與same-entropy shuffled。

#### Oracle-gap gate

```text
oracle_gap_a = max(0, M_oracle(T) - M_a(T))
```

Learned oracle gap必須strictly小於Formocast oracle gap。

`S4_LEARNED_RESIDUAL_POSITIVE`要求每個primary held-out unit三項全部通過。Tie不算positive；required support或coverage缺失是inconclusive。沒有使用outer labels重選features／genes／thresholds是必要validity condition。

不得自行加入effect margin、CI/significance requirement、x-of-y relaxation、
oracle-gap ratio，或修改data floor、split、scientific resource／comparability
boundary與claim；任何此類變更都需user review。

預設不跑 actual GA。只有另有第五個 prospectively sealed cluster與 fresh mentor gate，才可設計 actual GA validation；不屬於預設 internship承諾。

### 19.5 Stage 4 timebox

- planning threshold：5工作日；
- threshold不是完成承諾或entry debit；S40／S41 preflight只在A37 material
  condition成立時停止；
- 預設不新增超過一個 label-only cluster；
- 資料 gate未過立即停止，不用較弱 split救回。

Report：

- S40 trigger／data gate（含data-insufficiency scientific negative）：`study_docs/research/ductile-origami-warmstart/reports/staged/s40-stage4-activation-report.md`
- S41完成analysis：`study_docs/research/ductile-origami-warmstart/reports/learned-residual-surrogate-report.md`

---

## 20. Cross-stage resource、claim 與 lifecycle rules

### 20.1 Resource planning 與 material boundary

每個 stage entry前：

- 以至少1工作日或預估工作時間15%作最終synthesis planning buffer，取較大者；
- 以可用GPU時間的10%作noise／failed-measurement planning buffer；
- 評估完整formal panel、verification、closure與artifact preservation；
- 不因已開始就縮 seeds／arms／clusters後沿用原 claim。
- 以governance baseline
  `b0561d2c9216a58a9d71b8e839c47efaa51f9c00`建立best-effort ledger，逐gate／
  command記measurement boundary、wall-time、CPU/GPU、peak與retained storage、
  attempted／accepted／mapped／compiled／measured throughput、pre-empirical
  engineering、repair rounds與fresh role threads；`UNKNOWN`不補造；
- Known usage跨generation、successor、sibling checkpoint、replacement role、
  restart與new run root保留，不刪除或偽稱reset；resource cumulative total不單獨
  debit successor entry；repair cycle照常累計為provenance，thread hard cap照常執行；
- 首1% throughput後重估。20% pre-empirical share、2x projection、internal
  wall／CPU／GPU／storage／throughput target或5 GiB transient target crossing時
  record＋notify後繼續完整frozen workload；
- 只有A37 material condition成立才safe-boundary pause並提交decision packet。
  Runtime／planning variance不允許optional stopping，scientific sample／execution
  caps及downgrade gate不受影響。

### 20.2 Claim ladder

- Stage 1：bounded Gen0 mechanism evidence。
- Stage 2：single-development-cluster H10 early-search persistence／evaluation efficiency。
- Stage 3：two-held-out-regime bounded replication。
- Stage 4：cluster-held-out predictor substitution。

任何階段都不得宣稱：

- system／end-to-end speedup；
- full GA convergence；
- MI300X workload generalization；
- production／deployment readiness；
- owner adoption。

### 20.3 Stage branching

- Stage 1 positive → Stage 2。
- Stage 2 positive → Stage 3。
- Stage 1／3 predictor-specific failure + oracle positive + data gate → Stage 4。
- Hook、plumbing、Gen0、washout、regression、heuristic-saturation failures → 停止該 intervention branch。
- Negative／inconclusive也必須建立對應report，不只記成功案例。

### 20.4 Gate record與closure integration

- Historical `S10R2`、current `S10R3`與future `S20`各是standalone tranche／closure。
- `S11+S12+S13`、`S30+S31`、`S40+S41`各共享一個execution tranche與closure
  unit，但每個scientific gate及edge保持獨立。
- Internal positive只建立design指定的compact durable gate record，在fresh verifier
  確認frozen edge後繼續；不提前建立重複full report，也不把closure unit標complete。
- Internal terminal negative／inconclusive建立該design既定formal report並停止；
  `CHANGES_REQUIRED`只在repair budget內重驗，不是scientific outcome。
- Final gate report整合全部prior compact records、各gate verdict、resource ledger與
  claim boundary。Closure commit／post-audit前，partial狀態只屬
  `live_run_state`，不得回填`committed_projection_state`。

### 20.5 Owner-led future handoff

只有 Stage 3成功且核心團隊有興趣後，才可把以下列為 handoff idea：

- long-horizon／natural-stop confirmation；
- 更多 workloads／24-shape validation；
- end-to-end wall-time accounting；
- productization／deployment review。

它們不是 internship stage，也不恢復舊 M00–M09權威。

### 20.6 Stage-specific artifacts

Stage 2至少保存：

- `stage2-protocol-lock.json`
- `stage2-fresh-seed-manifest.json`
- `stage2-u-floor.json`
- `stage2-checkpoint-parity.json`
- `stage2-trajectories.parquet`
- `stage2-champion-remeasurements.parquet`
- `stage2-decision.json`

Stage 3至少保存：

- `stage3-cluster-registry.json`
- `stage3-freeze-manifest.json`
- 每cluster的 mapping／D5／weights／trajectory artifacts
- `stage3-heldout-denominator.json`
- `stage3-decision.json`

Stage 4至少保存：

- `stage4-trigger-evidence.json`
- `stage4-cluster-data-registry.json`
- `stage4-prospective-cluster-lock.json`（若適用）
- `stage4-outer-inner-split-manifest.json`
- `stage4-model-contract.json`
- `stage4-predictions.parquet`
- `stage4-decision.json`

所有 stage-specific artifacts沿用 §1 的hash、lineage與append-only amendment規則。
