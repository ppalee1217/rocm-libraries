---
historical_milestone_id: M00
title: Study contract 與 observability harness
lifecycle: legacy
archive_status: superseded
design_authority: none
execution_status: do_not_execute
historical_design_status: draft
historical_execution_status: not_started
historical_outcome: not_available
topic_successors: [S00]
historical_depends_on: []
historical_cohorts: [common]
historical_planned_report_paths:
  - ../reports/m00-study-contract-observability-report.md
---

> ⚠️ **LEGACY／DEAD PROTOCOL／DO NOT EXECUTE：**本檔是 pre-pivot 歷史設計，不具執行權威。主題 successor：[S00](../s00-evidence-contract-lineage-observability-design.md)。請先讀唯一 active 入口 [README](../README.md)。

# M00 — Study contract 與 observability harness 設計

Parent plan：[Ductile 引入 Origami/Formocast 暖啟動](../../ductile-origami-warmstart-experiment-plan.md)

## 1. 白話目標

先把「實驗規則」和「每一次搜尋到底發生了什麼」記清楚，再開始比較 cold 與 warm-start。

如果沒有這一步，後面即使看到暖啟動少跑了幾代，也無法分辨它是真的省下 benchmark，還是因為 invalid config、duplicate、提前停止或漏記成本而看起來比較快。

## 2. 實驗／工程假設

**假設 M00-H1**：可以在不改變 GA 搜尋語意與 RNG（random number generator，亂數產生器）順序的前提下，加上結構化 observer 與 experiment runner，完整記錄候選產生、合法性、實測與停止原因。

會推翻這個假設的觀察：

- observer 開啟後，同 seed 的 initial population、候選序列、fitness、champion 或 termination 發生變化；
- structured log 無法和原始 benchmark CSV、checkpoint、subprocess 次數對帳；
- runner 無法阻止 holdout shape 被 development/guidance 讀取；
- 實際執行值可繞過已鎖定的 contract，導致文件、runner 與分析使用不同門檻。

## 3. 預期目標

本 milestone 完成時，要交付：

1. 一份唯一可執行的 `protocol/experiment-contract.yaml` schema；
2. shape、baseline、revision 與 protocol lock 的 registry/schema；
3. 不改 GA 行為的 optional observer/event sink；
4. 能產生一致 run manifest、逐代 events、benchmark observations 與 summary 的 research runner；
5. observer off/on、artifact reconciliation、holdout fail-closed 與 contract immutability tests。

## 4. 結果能與不能說明什麼

能說明：

- 後續實驗的規則、資料角色、baseline 身分與 artifact 可追溯；
- `candidate_evals`、實際 GPU measurement 數與 wall time 沒有混為同一件事；
- instrumentation 本身沒有改變固定 seed 的 GA trajectory。

不能說明：

- Origami/Formocast 排名是否準確；
- warm-start 是否省評估或提高 GFLOPS；
- gfx942 環境、TuningDriver、production YAML 已通過；
- config→model mapping 正確；那是 M01 smoke 與 M02 的責任。

## 5. Scope 與不可越界項目

允許：

- 在 Ductile 邊界加入預設為 `None` 的 observer/event callback；
- 在 backend／runner 記錄 proposal、invalid、duplicate、compile、benchmark 與 timing；
- 新增 research-only orchestration、schema、analysis 與 tests。

不允許：

- 改 selection、crossover、mutation、survival、fitness、population decay 或 termination 邏輯；
- 為了 logging 多抽一次亂數，或改變候選迭代順序；
- 在 contract 內預填尚未確認的 TuningDriver 等價性、correctness policy 或統計 estimator；
- 讓 Markdown 成為第二份可執行常數來源。

實際程式 ownership 不在本設計先寫死。整合後依 dependency 與 maintainer ownership 決定：

- Ductile：observer/event interface；
- GEKO 或獨立 research package：arm orchestration、registry、artifact renderer；
- TensileLite／Origami：canonical mapping helper；
- study docs：protocol 與設計／報告。

## 6. Canonical contract

預定路徑：`study_docs/research/ductile-origami-warmstart/protocol/experiment-contract.yaml`

至少包含下列 group：

- `study`: protocol version、parent plan、design IDs、amendments；
- `platform`: gfx942、ROCm/driver/firmware、device policy；
- `revisions`: Ductile、GEKO、TensileLite、Origami/Formocast、analysis code；
- `data_roles`: pilot、development、development_guidance、development_judgment、final_holdout；
- `baseline`: provenance、fork params、weights、allowed claim scope；
- `measurement`: warmup、timed iterations、noise escalation、champion remeasurement；
- `search`: population、generation、period、seed、fitness aggregation；
- `guidance`: model、cohort route、λ、α、ε、`weight_beta`、sampling cap；
- `statistics`: target definition、censor representation、estimand、bootstrap unit、CI；
- `criteria`: 所有 acceptance、falsification、stop criterion 的 stable ID；
- `correctness`: validation count、edge cases、tolerance、failure policy；
- `locks`: split、winner、hyperparameters、analysis 與 holdout seal。

規則：

- runner 只能從 contract 讀執行常數；
- design 文件可以顯示 criterion key 與目前值，但只是非權威快照；
- 每個 run 保存 contract 完整副本與 SHA-256；
- 修改已用於 treatment 比較的 hypothesis、metric、threshold 或 analysis，只能 append amendment 並建立新 protocol version；
- 所有規則要在**第一次用它判斷 treatment 前**鎖定，不能看過結果後追溯修改。

## 7. Registry 與 fail-closed 規則

### 7.1 `shape-registry.csv`

至少包含：

- `shape_id`、`cluster_id`、`tile_id`、dtype、transpose、M/N/K/batch；
- `cohort`：`nonstreamk` 或 `streamk`；
- `role`：`pilot`、`development`、`development_guidance`、`development_judgment`、`final_holdout`；
- selection provenance、source hash、sealed timestamp。

Runner 必須拒絕：

- guidance role 讀取 `final_holdout`；
- M08 judgment 與 M09 final holdout 有相同 shape/cluster ID；
- 沒有 registry entry 的 shape 進入比較性實驗。

### 7.2 `baseline-registry.json`

至少包含：

- `baseline_id`；
- `source_kind`: `original_tuningdriver` 或 `geko_gfx942_proxy`；
- generator revision、fork params hash、weights hash；
- TuningDriver artifact／owner attestation；
- `allowed_claim_scope`。

沒有 original 的可驗證證據時，renderer 必須拒絕輸出「original Ductile cold baseline」。

### 7.3 `protocol-lock.json`

記錄：

- contract、split、baseline、revision、model、weights、analysis code 的 hash；
- lock owner、lock time、amendment chain；
- holdout sealed/unsealed 狀態；
- M08 鎖定的唯一 winner。

## 8. Telemetry 與 artifact schema

每個 run 的最小 artifact：

- `run-manifest.json`
- `environment.json`
- `search-space.json`
- `ga-events.jsonl`
- `benchmark-observations.parquet` 或等價 typed format
- `summary.json`
- generated YAML、stdout/stderr、checkpoint、artifact checksums

### 8.1 `run-manifest.json`

記錄：

- run/design/contract ID 與 SHA；
- arm、cohort、shape/cluster/tile、seed；
- baseline provenance；
- model、weights、search-space hash；
- revisions、commands、working directory；
- planned budget 與實際開始／結束時間。

### 8.2 `ga-events.jsonl`

逐 generation 至少記錄：

- `proposed`、`invalid`、`duplicate`、`compile_attempts`；
- `complete_candidate_evals`；
- `candidate_shape_benchmark_samples`；
- population size、decay mode、global/per-gene diversity；
- `f_avg`、`f_max`、best config hash；
- termination reason；
- model、mapping、validity、codegen、compile、benchmark 與 cumulative wall time。

`complete_candidate_eval` 的定義：同一 candidate 已取得該 run 所有 guidance shapes 的完整 fitness vector。Partial result 不可算入。

## 9. 實作步驟

1. 定義 contract、registry、manifest、event 與 summary schema。
2. 建立 stable criterion ID，例如 `M06.ACC.SPEED_DEV`、`R1.WALLTIME`。
3. 在 deterministic CPU evaluator 上加入 optional observer。
4. 建 observer off/on differential test：
   - 固定 seed；
   - 比 initial population、逐步 proposal、fitness、RNG state、checkpoint、champion、termination；
   - 必須完全相同。
5. 在 backend 邊界拆開 invalid、duplicate、compile failure、benchmark failure。
6. 建 artifact reconciliation：
   - events 的 total 對上 checkpoint／benchmark CSV；
   - subprocess／GPU sample 數可重建；
   - summary 只能從 raw artifacts 產生。
7. 建 shape-role 與 baseline claim fail-closed tests。
8. 建 protocol mutation test：鎖定後改 threshold/split/model 必須失敗或要求新 amendment。
9. M01 整合環境可用後，再做一次真實 smoke reconciliation；這不取代 CPU differential test。

## 10. 驗收、否證與停止條件

- **M00.ACC.OBS-SEMANTICS**：observer off/on 同 seed trajectory 完全一致。
- **M00.ACC.RECONCILE**：summary 的所有計數可由 raw artifacts 重建，沒有 unexplained delta。
- **M00.ACC.SPLIT-GUARD**：holdout/guidance overlap 測試 fail closed。
- **M00.ACC.BASELINE-GUARD**：缺 original evidence 時 renderer 無法產生 original claim。
- **M00.ACC.CONTRACT-LOCK**：鎖定後的 rule 只能以 append-only amendment 改版。
- **M00.FAL.INSTRUMENTATION**：instrumentation 改變候選、fitness 或停止行為，M00 失敗，後續比較性實驗禁止開始。
- **M00.STOP.MISSING-EVIDENCE**：若必要 event 在現有 backend 無法觀測，先停下補觀測介面，不用推測值填滿。

## 11. 預期狀況、診斷與解法

### 狀況 A：observer 改變 RNG

- 證據：off/on proposal 或 RNG state 首次分岔。
- 解法：observer 只接收 immutable snapshot；禁止在 callback 內採樣、排序原容器或延遲 materialization。
- 無法排除：M00 falsified，不能拿 instrumented run 和舊 baseline 比。

### 狀況 B：invalid 與 duplicate 都被記成零 fitness

- 證據：backend summary 無法將零分對應到原因。
- 解法：在原因仍可見的最早邊界發 structured event；保留原 fitness 行為不變。
- 無法排除：只允許 smoke，不允許成本 claim。

### 狀況 C：Markdown 與 runner 門檻不同

- 證據：design snapshot 與 contract key 不一致。
- 解法：加入 doc lint；報告一律引用 contract SHA，不讀 Markdown 數字執行。

### 狀況 D：cohort 不同時間完成

- 解法：共用 design／contract；各 cohort 獨立 report 與 outcome，避免為等另一 cohort 而延遲記錄。

## 12. 執行完成後的報告

完成並驗證 M00 後才建立：

`../reports/m00-study-contract-observability-report.md`

報告必須逐項回答 M00 criteria，包含 observer differential、artifact reconciliation、遇到的 instrumentation 問題、root cause、修正與仍未觀測到的欄位。未通過也要建立 negative／inconclusive report，不得只留下「工具還在開發」。
