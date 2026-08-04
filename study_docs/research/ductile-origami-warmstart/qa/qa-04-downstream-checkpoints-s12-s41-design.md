# QA-04 — 下游 checkpoints S12–S41

> **文件角色：**這是從 [實驗白話導讀 hub](../../ductile-origami-warmstart-experiment-guide.md) 拆分出來的白話導讀主題檔，方便在單一主題上持續討論。它不是 experiment authority，也不是 contract、lock 或 report，不會取代正式的 charter、experiment plan、checkpoint design、lock 或 report。
>
> **衝突處理：**若本檔與正式文件衝突，以 [research charter](../../surrogate-dse-plan.md)、[experiment plan](../../ductile-origami-warmstart-experiment-plan.md)、[active checkpoint index](../README.md) 及各 checkpoint design 為準。
>
> **2026-08-04 current status override：**S10R3 已 terminal negative；S10R4 已 retired／not evaluated；S11 已 sealed `LOCKED_READY`。沒有 S11/S12 result、effective checkpoint lock、report 或 edge；最新狀態仍須對照 active checkpoint index、formal artifacts 與 Git history。

---

## 10. S12：Real-score D5 audit

S12 是第一個正式用 real GPU labels 判斷 Formocast/factorization 的核心 checkpoint。

### 10.1 測量

- 256 unique configs；
- 3 sizes；
- 768 config×size observations；
- 分析單位仍是 config，不把 768 rows 當獨立樣本。

### 10.2 Metrics

- design-weighted Spearman；
- real top-decile cutoff；
- top-decile overlap/lift；
- arm-specific real-top-decile prior mass；
- importance ESS；
- coverage/rejection；
- cross-fitted oracle。

Real-high-quality set與directional raw-mass index在labels前綁定：

```text
r_a(o)   = pi_nominal,a(o) / pi_nominal,0(o)
A_aj     = sum_{o aliases j} r_a(o)
N_HT,a   = sum_{j in D5} [A_aj / rho_j] * I[j in T_D5]
D_exact,a = sum_{o in Fraw_global} r_a(o)
M_HT,a   = N_HT,a / D_exact,a
ESS_a    = [sum_{j in D5} A_aj/rho_j]^2 / sum_{j in D5}[A_aj/rho_j]^2

w_0j = A_0j / rho_j
Q_D5(t) = [sum_{j in D5} w_0j * I[quality_j <= t]] / sum_{j in D5} w_0j
t_D5 = min{quality_j : Q_D5(quality_j) >= 0.90}
T_D5 = {j in D5 : quality_j >= t_D5}
```

Stable estimator identity是
`S12-DIRECTIONAL-FINITE-FRAME-HT-EXACT-DENOMINATOR-v1`。`rho_j`是fixed-256
stratified design的identity inclusion probability；`quality_j`是all-size aggregate real
quality、越大越好，cutoff ties全部進`T_D5`。`M_HT`是design-based
directional index，可大於1，不是bounded probability。禁止clip、winsorize、post-hoc
normalize或sampled denominator。Stratum／identity bootstrap每次重建cutoff、set、
estimators、contrasts、ESS與oracle gap。

### 10.3 `D5_PASS`

全部要求：

- coverage/rejection gate 通過；
- aggregate Spearman ≥0.25；
- top-decile lift ≥2×；
- 至少 2/3 sizes 方向為正；
- Formocast residual `M_HT` strictly勝 existing baseline；
- 同時勝 shuffled；
- 每個相關 arm ESS ≥25；
- 沒有 correctness failure。

### 10.4 Oracle 的角色

Oracle 使用 held-out real-score marginals診斷：

- Formocast ranking/marginalization 失敗；
- factorized hook 本身表達力不足。

Oracle 不是 treatment arm，也不能把 D5 fail 改成 pass。

---

## 11. S13：Actual Gen0 mechanism

### Arms

- U：uniform／no optional guidance；
- G：existing YAML/GEKO guidance；
- F：G + Formocast residual guidance；
- S：G + same-entropy shuffled residual guidance。

### 設定

```text
requested pop_size = 64
n_gen = 1
period = 0
paired seeds = 3
```

Resolved `P0` 必須在 labels 前鎖定。若 `P0 != 64`，需 amendment及重新估算成本。

### Primary endpoint

```text
Gen0 top-decile hit rate
```

### `D6_MECHANISM_POSITIVE`

- F-G paired delta 至少 2/3 seeds >0；
- F-S paired delta 至少 2/3 seeds >0；
- median-quality guardrail 至少 2/3；
- proposal hashes/order/weights/space 一致；
- sampler replay 無 systematic anomaly；
- 無新增 correctness failure。

三個 seeds 只支持方向性 mechanism evidence，不做顯著性宣稱，也不等於 speedup。

---

## 12. S20：固定 10 代 persistence

### 設定

- G/F/S；
- `n_gen=10`；
- `period=0`；
- 5 個 fresh paired seeds；
- 與 Stage 1 seeds 完全分離。

### Primary metric

在共同 complete-evaluation support `U_floor` 上，積分 best-so-far log-quality：

```text
AUC_F - AUC_G
AUC_F - AUC_S
```

### Positive gate

- F-G AUC 至少 4/5 為正；
- F-S AUC 至少 4/5 為正；
- H10 endpoint F>G 至少 3/5；
- final non-inferiority 至少 4/5；
- 無 correctness/plumbing/mapping/systematic fill failure。

H5 只能是 blinded operational checkpoint，不能看到結果後決定要不要跑 H10。

---

## 13. S30／S31：Held-out bounded replication

### S30

在任何 Stage-3 score/label 前鎖定：

- 兩個新 primary clusters；
- 每 cluster 兩個 same-space sizes；
- 最多一個 technical reserve；
- fixed two-slot denominator；
- frozen procedure；
- 完整 budget。

S30 不跑 D5 或 GA。

### S31

每個 cluster：

1. mapping/access/noise；
2. model-only factorization；
3. 256 configs ×2 sizes D5；
4. D5 pass 才跑 G/F/S × H10 ×3 fresh seeds。

Positive 要求兩個 clusters 都通過。

一正一負是 regime heterogeneity，不能只報成功者，也不能跨 cluster 平均救回。

---

## 14. S40／S41：條件式 learned residual

### S40 trigger

只有：

- Formocast predictor-specific failure；
- oracle 仍支持 factorized main effects；
- forbidden causes 不存在；
- data floor 足夠；

才可啟動。

### Data floor

- 至少 4 independent clusters；
- 每 cluster ≥256 unique configs；
- 每 cluster ≥2 sizes；
- 總計 ≥1,024 configs／2,048 labels。

### S41 model

唯一 model：

```text
inclusion-weighted ridge residual correction
```

Target：

```text
log(real latency) - log(Formocast latency)
```

使用 whole-cluster holdout，禁止 random row split。

每個 primary held-out unit 都要：

- ranking strictly 勝 Formocast；
- exact inherited、unclipped `M_HT` strictly勝Formocast-factorized與shuffled；
- directional-index `oracle_gap_a=max(0,M_HT,oracle-M_HT,a)` strictly變小；它不是
  probability gap。

預設不跑 actual GA，且 S41 沒有自動 outgoing edge。

---

