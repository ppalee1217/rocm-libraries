# QA-00 — 總覽、閱讀順序與來源

> **文件角色：**這是從 [實驗白話導讀 hub](../../ductile-origami-warmstart-experiment-guide.md) 拆分出來的白話導讀主題檔，方便在單一主題上持續討論。它不是 experiment authority，也不是 contract、lock 或 report，不會取代正式的 charter、experiment plan、checkpoint design、lock 或 report。
>
> **衝突處理：**若本檔與正式文件衝突，以 [research charter](../../surrogate-dse-plan.md)、[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)、[active checkpoint index](../README.md) 及各 checkpoint design 為準。
>
> **2026-08-04 current status override：**S10R3 已 terminal negative；S10R4 已 retired／not evaluated；S11 已 sealed `LOCKED_READY`。沒有 S11/S12 result、effective checkpoint lock、report 或 edge；最新狀態仍須對照 active checkpoint index、formal artifacts 與 Git history。

---

## 1. 先用一分鐘理解整個研究

Formocast 可以看一整組 kernel 參數，預測這組 config 可能有多快。

Ductile 的 Gen0 初始化介面卻不是直接接收：

> 「請多抽這個完整 config。」

它主要接收的是：

> 「這個 gene 的每個候選值，各自應該多常被抽到。」

因此研究要做的事是：

```text
Formocast 對 whole config 的評分
    ↓
factorization
    ↓
每個 residual gene value 的抽樣偏好
    ↓
Ductile Gen0 initial population
    ↓
真實 GPU 品質判斷
```

核心問題是：

> 把 whole-config 訊號拆成 per-gene probabilities 後，還剩多少真正有用的資訊？

如果有用，再繼續問：

1. 離線 ranking 是否真的對準高品質 configs？
2. 這個 prior 經過 validity filter、去重及有限 population 後，是否仍能改善 Gen0？
3. Gen0 優勢是否能保留到固定 10 generations？
4. 同一方法能否在兩個新 held-out regimes 重現？
5. 若 Formocast predictor 失敗但 factorization oracle 仍有效，learned residual 能否補救？

這是一個 **stage-gated mechanism study**，不是完整 tuning speedup 或 production deployment 專案。

---

## 2. 目前最重要的結論

### 已經有正式科學結果

- **S00：positive**
  - 證明 evidence、lock、lineage、observer、checkpoint/resume 等 CPU-only 實驗基礎可信。
  - 不證明任何 GPU、Formocast 或 kernel performance 結果。
- **S10：negative**
  - 正確且可重現地得到 `S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`。
  - 只證明原始 S10 mapping boundary 不能通過，不證明 Formocast 沒有效。

### 已取消的嘗試

- **S10R1**
  - 因 nominal boundary selector、超長 valid-support 搜尋、ledger scaling 與治理成本偏離核心研究問題，在 A32 被取消。
  - 狀態是 `cancelled / BLOCKED / not_evaluated / edge=null`。
  - 不是 negative，也不是 inconclusive。
  - A33 已把約 34 GB bulk diagnostics 和 19 個舊 implementation paths 退休，只保留 identity tombstone。

### 已完成但沒有下游 edge 的 recovery

- **S10R2：inconclusive**
  - 依 frozen exact-ten criterion 完成 closeout。
  - 正式狀態是 `CHECKPOINT_COMPLETE / inconclusive / FT-INCONCLUSIVE / edge=null`。
  - 沒有啟動 S11。
  - S10R2 outcome artifacts 不得改作 S10R3 或 S11 formal evidence。

### 目前 active 的入口設計

- **S10R3**
  - 延續 support-aware entry，但改用 bounded deterministic exact-K corpus。
  - `K = max(10, C_greedy)`，且 `K <= 20`。
  - 先確認 Ductile 實際接受哪些 candidate values，再用最多 20 個 fresh configs 覆蓋 mandatory witnessed atoms。
  - 只有 post-audited `S10R3:S1_ENTRY_GO` 可以啟動 S11。

### 目前還沒有的科學結果

截至 2026-08-01 本次補充所查到的 committed projection：

- S10R3 尚未有 committed terminal scientific outcome。
- S11 仍需等待 post-audited `S10R3:S1_ENTRY_GO`。
- 本文件中的 live observations 不得冒充 committed result。
- S11–S41 尚未因 S10R3 取得新的正式下游 edge。

---

## 3. 完整 checkpoint 主線

```text
S00  Evidence foundation                     已完成 positive
  ↓
S10  原始 Stage-1 entry                      已完成 negative，edge=null

S10R1 舊 recovery                            已取消，不提供科學 edge
  ⋮ administrative / historical only

S10R2 support-aware entry                    已完成 inconclusive，edge=null
  ⋮ historical only

S10R3 bounded-cover support-aware entry      active entry checkpoint
  │ S1_ENTRY_GO
  ↓
S11  model-only factorization / guidance lock
  │ S1_GUIDANCE_LOCKED
  ↓
S12  real-score ranking / prior-mass / oracle audit
  │ D5_PASS
  ↓
S13  actual Gen0 mechanism
  │ D6_MECHANISM_POSITIVE
  ↓
S20  fixed-H10 persistence
  │ S2_DIRECTIONAL_PERSISTENCE_POSITIVE
  ↓
S30  held-out registry / procedure freeze
  │ S3_REGISTRY_PROCEDURE_LOCKED
  ↓
S31  two-cluster bounded replication

條件分支：
S12 predictor-specific failure + oracle positive ─┐
                                                   ├→ S40 → S41
S31 predictor heterogeneity + oracle positive ─────┘
```

只有 post-audited `S10R3:S1_ENTRY_GO` 可以啟動 S11。

---

## 24. 閱讀與討論順序建議

如果要針對設計提出問題，建議依序閱讀：

1. 本導讀；
2. [research charter](../../surrogate-dse-plan.md)；
3. [experiment plan](../../ductile-origami-warmstart-experiment-plan.md)；
4. [active checkpoint index](../README.md)；
5. [S10R2 historical design](../s10r2-stage1-support-aware-entry-recovery-design.md)；
6. [S10R3 active design](../s10r3-stage1-bounded-cover-entry-recovery-design.md)；
7. [Value-level guidance proposal](../archive/s10r3-s11-value-level-guidance-amendment-proposal.md)；
8. [S11 design](../s11-stage1-model-only-factorization-design.md)；
9. [S12 design](../s12-stage1-real-score-ranking-oracle-audit-design.md)；
10. [S13 design](../s13-stage1-actual-gen0-mechanism-design.md)；
11. 後續 Stage 2–4 designs；
12. 最後再看 protocol/schema/tests 與 formal reports。

後續可直接在本文件對應段落留下問題，例如：

- 「§7.4 的 15 conditional targets是否足夠？」
- 「§8.5 的 gene criteria是否過嚴？」
- 「§9 的 shuffled control是否仍有 validity confounder？」
- 「§10 的 D5 thresholds是否有足夠power？」
- 「§11 的 resolved P0 對成本影響有多大？」
- 「§21 的 post-seal audit現在完成了嗎？」

---

## 25. 重要來源

### Authority

- [Research charter](../../surrogate-dse-plan.md)
- [Experiment plan](../../ductile-origami-warmstart-experiment-plan.md)
- [Active checkpoint index](../README.md)

### Stage 1

- [S10 formal report](../reports/staged/s10-stage1-entry-gate-report.md)
- [S10R2 historical design](../s10r2-stage1-support-aware-entry-recovery-design.md)
- [S10R3 active design](../s10r3-stage1-bounded-cover-entry-recovery-design.md)
- [Value-level bounded guidance proposal](../archive/s10r3-s11-value-level-guidance-amendment-proposal.md)
- [S11 design](../s11-stage1-model-only-factorization-design.md)
- [S12 design](../s12-stage1-real-score-ranking-oracle-audit-design.md)
- [S13 design](../s13-stage1-actual-gen0-mechanism-design.md)

### Later stages

- [S20 design](../s20-stage2-h10-persistence-design.md)
- [S30 design](../s30-stage3-heldout-registry-freeze-design.md)
- [S31 design](../s31-stage3-bounded-replication-design.md)
- [S40 design](../s40-stage4-surrogate-activation-gate-design.md)
- [S41 design](../s41-stage4-learned-residual-analysis-design.md)

### Relevant code

- [Ductile GA](../../../../projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py)
- [Ductile SearchSpace](../../../../projects/hipblaslt/tensilelite/Tensile/ductile/core/space.py)
- [Origami public types and prediction modes](../../../../shared/origami/include/origami/types.hpp)
- [Origami public selection API](../../../../shared/origami/include/origami/origami.hpp)
- [Origami estimation/Formocast mode dispatch](../../../../shared/origami/src/origami/gemm.cpp)
- [Formocast simulator](../../../../shared/origami/src/simulator/tensilelite/formocast_simulator.cpp)
- [SolutionIterator runtime queue](../../../../projects/hipblaslt/tensilelite/client/src/SolutionIterator.cpp)
- [S10R2 frozen contract](../protocol/v1/s10r2-stage1-support-aware-entry-contract.yaml)
- [S10R3 support classification](../protocol/v1/s10r3/support.py)
- [S10R3 mapping adapter](../protocol/v1/s10r3/mapping.py)
- [S10R3 native Formocast/runtime adapter](../protocol/v1/s10r3/native_formocast_runtime_adapter.cpp)

### Origami／Formocast explanatory docs

- [Origami API and usage](../../../origami/api-and-usage.md)
- [Origami latency model](../../../origami/latency-model.md)
- [Origami ecosystem and Formocast](../../../origami/ecosystem-and-formocast.md)
- [Origami vs Formocast internal comparison](../../../internal_docs/origami-vs-formocast.md)
