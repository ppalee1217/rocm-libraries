---
milestone_id: M02
title: Config 到模型再到 per-gene weights 的 guidance plumbing
lifecycle: legacy
design_authority: none
design_status: superseded
execution_status: do_not_execute
outcome: superseded
historical_design_status: draft
historical_execution_status: not_started
historical_outcome: not_available
superseded_by: [S11]
depends_on: [M00, M01.SW]
cohorts: [common]
planned_report_paths:
  - ../reports/m02-guidance-plumbing-report.md
---

> ⚠️ **LEGACY／DO NOT EXECUTE：**本檔是 pre-pivot 歷史設計，不具執行權威。Active replacement：[S11](staged/s11-stage1-model-only-factorization-design.md)。請先讀 [design index](README.md) 與現行 parent protocol。

# M02 — Guidance plumbing 設計

Parent plan：[Ductile 引入 Origami/Formocast 暖啟動](../../ductile-origami-warmstart-experiment-plan.md)

## 1. 白話目標

Origami/Formocast 只會替「一整組 config」打分；Ductile 的 hook 要的是「每個 gene 的每個候選值各一個 cost」。

M02 要把中間每一步做成可 audit、可重跑、遇到缺值就 fail closed 的管線，避免模型本身沒問題，卻因欄位 mapping、candidate 順序或正負號搞錯而把 GA 往反方向推。

## 2. 假設

**假設 M02-H1**：完整解析後的 Tensile solution 可以無歧義轉成 Origami/Formocast input；whole-config latency 能按 parent 的 marginalization protocol 轉成與 `SearchSpace.map` 完全對齊的 per-gene weights。

推翻或阻擋觀察：

- 需要的 metadata 只能靠猜值或 raw sentinel 填入；
- model output 無法和 input sample ID 一一對齊；
- Python/C++ mapping 無法通過逐欄 parity；
- weights 經 Ductile hook 轉換後不是預期 probability；
- 正式 weights 混入真實 GFLOPS，造成 guidance/judgment leakage；
- 取得 Formocast metadata 的成本讓 Route 1 wall-time 目標即使在最樂觀情境也不可能達成。

## 3. 預期目標

交付五個明確介面：

```text
resolve_solution(candidate, problem, hardware) -> resolved_solution + audit
to_model_config(sample_id, resolved_solution, cohort) -> model_input + audit
score_batch(model, problem, model_inputs) -> aligned latency/status
build_factorized_marginals(scores, search_space, contract) -> probabilities
to_ductile_weights(probabilities, SearchSpace.map, weight_beta) -> weights_bundle
```

另交付 injection A 的保守 helper：

```text
build_a_safe_space(V0, legal_extras, admission_stats) -> VA + audit
```

## 4. 結果能與不能說明什麼

能說明：

- candidate mapping、model scoring、marginalization 與 weights ordering 按規格執行；
- same-entropy shuffled control 真正只改 permutation；
- insensitive/unmappable gene 正確回到 uniform；
- Formocast guidance 的 CPU 前置成本是否仍有機會達到 end-to-end 目標。

不能說明：

- 模型 whole-config ranking 好；由 M05 驗；
- factorized guidance 能改善 GA；由 M06 驗；
- A-safe extras 有實際價值；由 M04/M07 驗。

## 5. Evidence 與硬邊界

- [Origami `rank_configs`](../../../../shared/origami/include/origami/origami.hpp#L83-L96) 接 whole-config list、回傳排序結果，不是 per-gene API。
- [SolutionIterator mapping](../../../../projects/hipblaslt/tensilelite/client/src/SolutionIterator.cpp#L261-L305) 使用 `solution.getSizeMapping()` 與 `calculateAutoGSU()`，是 canonical mapping 的現有證據。
- [Solution prediction metadata 初值](../../../../projects/hipblaslt/tensilelite/Tensile/SolutionStructs/Solution.py#L1509-L1513) 不是可直接評分的正式值。
- injection B 只允許使用既有 initial-sampling weights hook；不得擴張成 mutation bias、逐世代退火或 adaptive trust。
- 正式 guidance 不得讀真實 GFLOPS；真實分數只可用在 M05 dev-only oracle diagnosis。

## 6. Functional 與 cost 子 gate

- **M02.FUNCTIONAL**：mapping、alignment、marginalization、weights round-trip 與 artifacts 全部通過 CPU/golden tests。
- **M02.COST**：在 M03 取得 cold cost 後，完成 Formocast 前置成本 feasibility bound，決定它是正式 arm 或 diagnostic arm。

M02.FUNCTIONAL 可在沒有 gfx942 時先完成大部分工作；需要真實 generated solution 的 parity case 由 M01.SW/M01 mapping smoke 提供。

## 7. Data model 與 artifacts

### 7.1 `resolved-configs.parquet`

每列至少包含：

- `sample_id`、problem/cohort/search-space hash；
- raw candidate 與完全解析後 categorical config；
- derived SizeMapping 欄位；
- sentinel resolution provenance；
- validity status、failure reason；
- converter revision/hash。

### 7.2 `model-scores.parquet`

- `sample_id`；
- model、model revision、model mode；
- predicted latency、rank、status；
- input config hash；
- mapping/scoring wall time；
- rejection／unmappable reason。

模型排序或刪除 rejected config 時，仍必須靠 `sample_id` 對齊，不可假設 positional alignment。

### 7.3 `marginals.parquet`

- shape/cluster、gene、candidate value、candidate index；
- support `n`、global/top-up source；
- conditional utility mean、shrinkage term；
- `q`、ε-mixed `p`；
- bootstrap interval（只供 admission/stability/report，不當 probability）。

### 7.4 `weights.yaml` 與 `space-manifest.json`

- gene 順序；
- 每個 candidate value 與 index；
- `p`、轉換後 `w`；
- λ、α、ε、`weight_beta`；
- V0/VA/Vwide 差異；
- contract/model/search-space hash。

## 8. Canonical mapping 設計

正式方案優先：

1. 抽取或共用基於 `ContractionSolution::getSizeMapping()` 的 C++ converter；
2. 以 stable sample ID 批次輸出 Origami/Formocast input；
3. 視需要提供 Python binding，但不重寫欄位推導。

如果 integration 成本迫使暫時使用 Python converter，最低 parity evidence：

- golden corpus 涵蓋 dtype、transpose、GSU、StreamK、grouped gene、auto sentinel；
- integer/bool fields 逐欄完全相同；
- floating fields tolerance 在第一次使用前由 contract 鎖定；
- unresolved sentinel、occupancy、math clocks 缺失時 fail closed；
- 同一 resolved config 經兩路產生相同 model input 與 ranking；
- golden artifact 與 converter SHA 鎖定。

M01 mapping smoke 只證明單一 canonical case；M02 要證明 corpus 與批次路徑。

## 9. Sampling 與 marginalization

對每個 shape／cluster：

1. 從 baseline 候選清單的均勻乘積分布抽 `_initKernel-valid` configs。
2. global-uniform：
   - pilot 1,024；
   - dev/confirm 8,192。
3. 對每個 `(gene,value)` conditional top-up：
   - pilot support ≥64；
   - dev/confirm support ≥256；
   - 每 shape/cluster model scoring cap 32,768。
4. top-up 只用於自己的 `(gene,value)`，unit weight。
5. 將 latency 轉成 percentile rank `r`，再算 `u=exp(-λr)`。
6. shrinkage mean：

```text
mu[g,v] = (sum(u) + alpha * global_mean(u)) / (n[g,v] + alpha)
q[g,v]  = mu[g,v] / sum_v(mu[g,v])
p[g,v]  = epsilon / |Vg| + (1 - epsilon) * q[g,v]
w[g,v]  = -log(p[g,v]) / weight_beta
```

7. 多 shape 先按實際 `reduce_fn` 聚合 whole-config utility，再 marginalize。
8. 完全不敏感、無法映射或沒有合法 support 的 gene 保持 uniform；不得靜默刪值。

## 10. Injection A helper

`build_a_safe_space` 必須保證：

- `V0 ⊆ VA`；
- extras 位於 generator legal domain，且有足夠 conditional completions；
- enrichment 相對 V0 mean 的 bootstrap 95% LCB > 1；
- 每 gene 最多加 2 值；
- extras 仍取得 ε-uniform mass；
- 每次輸出 exact space diff 與 admission evidence。

A-hard 不在此 helper 執行；它只在 M07 用 dev real-score pool 做 offline diagnosis。

## 11. 測試計畫

### 11.1 Mapping

- unresolved `-1/-2` 必須失敗；
- invalid occupancy/math clocks 必須失敗；
- effective GSU、PGR、DTV、GRVW、VectorWidth、DepthU、WGM 逐欄 parity；
- StreamK/non-StreamK routing 正確；
- model rejection 保留 sample ID 與原因。

### 11.2 Probability 與 ordering

- 每 gene `sum(p)=1`；
- `p[g,v] ≥ ε/|Vg|`；
- `w=-log(p)/beta` 經 Ductile transform 後重建同一 probability ratio；
- candidate 順序嚴格等於 `SearchSpace.map[g]`；
- candidate reorder test 能偵測 silent mismatch；
- NaN/Inf、zero support、missing gene fail closed；
- insensitive gene 產生 uniform；
- grouped gene 不破壞既有 group constraint。

### 11.3 Controls 與 determinism

- shuffled control 只 permutation、entropy 完全相同；
- 同 input/seed/model/contract 產物 hash 相同；
- formal model weights 的 lineage 不含 real GFLOPS；
- oracle artifact 有明確 `diagnostic_only=true`，runner 拒絕把它送入正式 arm。

## 12. Formocast 成本 feasibility

用 1,024-config pilot 分解：

- resolve/derived solution；
- validity；
- codegen（若需要）；
- mapping；
- Formocast scoring；
- rejection與 coverage。

外推 8,192 + top-up 的成本，並在 M03 有 cold GA 成本後做 optimistic bound：

```text
best_possible_total_saving
= optimistic_benchmark_saving
 - guidance_mapping_scoring_overhead
```

判讀：

- 若取得 metadata 需要 GPU benchmark 或真 compile，Formocast 不得作「便宜 guidance」正式 arm；
- 若只需 CPU derived/codegen，但即使最樂觀也不可能滿足 Route 1 的 end-to-end wall-time ≥15% saving，降為 diagnostic；
- 不在本輪發明固定秒數 cutoff；所有判斷依 contract 與 M03 實測成本。

## 13. 驗收、否證與停止條件

- **M02.ACC.CANONICAL**：正式 converter 或完整 Python parity corpus 通過。
- **M02.ACC.ALIGNMENT**：所有 accepted/rejected model result 可依 sample ID 對齊。
- **M02.ACC.PROBABILITY**：normalization、ε floor、round-trip、ordering 全通過。
- **M02.ACC.DETERMINISM**：固定 input/seed/version 產物 hash 一致。
- **M02.ACC.NO-LEAKAGE**：formal weights lineage 無真實 GFLOPS。
- **M02.ACC.COST**：每個 model/cohort 有 formal/diagnostic/blocked 明確判定。
- **M02.FAL.MAPPING**：canonical metadata 無法取得且只能猜值，該 model arm 停止。
- **M02.FAL.HOOK**：連 oracle probability round-trip 都無法忠實送入 hook，停止 injection B 實驗。
- **M02.STOP.SUPPORT**：conditional top-up 到 cap 仍不足時，保持 uniform並報告；不可刪 candidate 偷渡 pruning。

## 14. 預期狀況、診斷與解法

### 狀況 A：model output 排序後 sample 對不上

- 解法：在 binding/API 保留 sample ID 或 config hash；若現有 binding 不暴露，加入 adapter/parity test，不用 positional guess。

### 狀況 B：Python 與 C++ mapping 漂移

- 解法：C++ 為 canonical；每次 revision 跑 golden parity。不能靠放寬 tolerance 遮掉 integer 欄位差異。

### 狀況 C：低合法率造成 top-up 爆量

- 解法：記 rejection reason、達 cap 後 uniform fallback；A-safe admission 失敗，不刪 baseline 值。

### 狀況 D：Frankenstein config

- 原因：factorized marginals 丟失 epistasis。
- 解法：保留 group、ε-uniform、真實 fitness、shuffled control、M05 oracle diagnosis。
- 邊界：本輪不新增 pairwise/joint hook。

### 狀況 E：Formocast 前置成本過高

- 解法：降為 ranking diagnosis；正式 treatment 保留通過成本 gate 的 model。不能排除 overhead 後仍宣稱 end-to-end speedup。

## 15. 執行完成後的報告

完成或明確失敗後才建立：

`../reports/m02-guidance-plumbing-report.md`

報告必須包含 mapping parity、round-trip、ordering、support、cost breakdown、model/cohort eligibility、遇到的欄位／binding 問題與解法。它只能宣稱 plumbing verified／falsified，不能宣稱 warm-start uplift。
