---
historical_milestone_id: M01
title: Step-0 環境、整合、baseline 與噪音 gate
lifecycle: legacy
archive_status: superseded
design_authority: none
execution_status: do_not_execute
historical_design_status: draft
historical_execution_status: blocked
historical_outcome: not_available
topic_successors: [S10]
historical_depends_on: [M00]
historical_cohorts: [common]
historical_planned_report_paths:
  - ../reports/m01-step0-integration-gate-report.md
---

> ⚠️ **LEGACY／DEAD PROTOCOL／DO NOT EXECUTE：**本檔是 pre-pivot 歷史設計，不具執行權威。主題 successor：[S10](../../s10-stage1-entry-access-mapping-gate-design.md)。請先讀唯一 active 入口 [README](../../README.md)。

# M01 — Step-0 環境、整合、baseline 與噪音 gate 設計

Parent plan：[Ductile 引入 Origami/Formocast 暖啟動](../../../ductile-origami-warmstart-experiment-plan.md)

## 1. 白話目標

確認「硬體真的可用、指定版本真的能一起工作、baseline 名字沒有冒充、fitness 與 correctness 設定明確、量測噪音可控」。

M01 沒通過，後面的 GPU 數字即使看起來很漂亮，也不能當成暖啟動有效的證據。

## 2. 假設

**假設 M01-H1**：Ductile、GEKO/TensileLite 與 Origami/Formocast 的鎖定 revisions，可以在 gfx942 上完成 generate → compile → benchmark，且 production fitness、baseline provenance、metadata 與量測政策都能被明確記錄。

推翻或阻擋這個假設的觀察：

- `rocminfo` 看不到 gfx942，或 GPU node 無法建立；
- 鎖定 revisions 無法整合建置／測試；
- 單 kernel smoke 無法完成；
- 實際 generated YAML 的 `soo/reduce_fn` 不明或 arm 間不同；
- unresolved sentinel、`CUOccupancy<=0`、`MathClocksUnrolledLoop<=0` 被送入正式 Formocast；
- 噪音在預先規定的 iteration escalation 後仍超限；
- TuningDriver 狀態一直是 unknown，導致 baseline claim scope 無法判定。

## 3. 預期目標

M01 產生兩個 gate：

- **M01.SW**：revision、build、unit test、canonical single-solution mapping smoke 通過。它可解鎖 M02 CPU／functional 工作。
- **M01.ALL**：再加 gfx942、GPU smoke、baseline provenance、actual YAML、noise、correctness policy 全部通過。它才可解鎖比較性 GPU 實驗。

## 4. 結果能與不能說明什麼

能說明：

- 實驗環境與 revisions 可重現；
- baseline 應稱 original 或 GEKO-profile proxy；
- production run 實際採用的 fitness 與 correctness 設定；
- 單一 canonical solution 能取得模型需要的 resolved metadata；
- 量測 protocol 在目前機器上足以比較 paired arms。

不能說明：

- 批次 mapping、marginalization 與 weights 正確；由 M02 驗；
- cold GA 有 headroom；由 M03 驗；
- model ranking 或 warm-start 有效。

## 5. 目前已知狀態

- Ductile ref：`origin/ductile_integration@5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39`，尚未整合建置。
- GEKO ref：`origin/users/pkamd/geko_pr@d32abacfd13579d1f523f035b7a10b0734c4ac47`，尚未整合建置。
- 本機 `rocminfo` 目前只列 CPU agent，並回報 GPU node unrecognized。
- TuningDriver artifact、正式 CLI、授權及輸出等價性未知。
- [Origami `rank_configs`](../../../../../shared/origami/include/origami/origami.hpp#L83-L96) 是 whole-config API。
- [SolutionIterator mapping](../../../../../projects/hipblaslt/tensilelite/client/src/SolutionIterator.cpp#L261-L305) 從 `solution.getSizeMapping()` 取欄位，effective GSU 由 `calculateAutoGSU()` 取得。
- [Solution 初始 prediction metadata](../../../../../projects/hipblaslt/tensilelite/Tensile/SolutionStructs/Solution.py#L1509-L1513) 是 `CUOccupancy=-1`、`MathClocksUnrolledLoop=0`；不可把它們當正式值。

## 6. 輸入與輸出

輸入：

- 可存取的 MI300X/gfx942 node；
- 三個鎖定 source revisions 與 integration branch；
- 真實 workload 與生成 YAML；
- TuningDriver owner 回覆／artifact；
- 一個最小 non-StreamK 與一個 StreamK smoke case。

輸出：

- `environment.json`
- `revision-lock.json`
- `build-test-results.json`
- `baseline-registry.json`
- `generated-configs/`
- `mapping-smoke.json`
- `noise-pilot.csv`
- `correctness-policy.json`
- M00 格式的 run manifest、events、stdout/stderr 與 checksums

## 7. 實作步驟

### 7.1 硬體與環境

1. 保存完整 `rocminfo`。
2. 明確擷取 architecture、device ID、CU 數、BDF、可見 device 數。
3. 記錄 ROCm、driver、firmware、OS、compiler、Python/CMake 版本。
4. 確認獨占 GPU；若做不到，記錄同機 process、clock、temperature、power。
5. 建環境 fingerprint，後續 run 不一致時 fail closed 或另開 environment ID。

### 7.2 Revision 與整合

1. 建 integration branch/worktree，不改寫原 refs。
2. 鎖定 Ductile、GEKO、TensileLite、Origami/Formocast、analysis code SHA。
3. 建立可重現 build commands 與依賴版本。
4. 執行：
   - Ductile unit tests；
   - GEKO config-generator tests；
   - Origami/Formocast tests，包含 gfx942 prediction；
   - M00 observer differential tests。
5. 任何 patch 都記錄在 revision lock，不用 dirty working tree 跑正式比較。

可先驗證的命令入口：

```bash
cd projects/hipblaslt/tensilelite
tox -e unit -- Tensile/Tests/unit/Ductile
```

```bash
cd projects/hipblaslt/utilities/geko
python3 -m pytest tests/config_generator/ -v -rs
```

```bash
cmake -S shared/origami -B build/origami -DORIGAMI_BUILD_TESTING=ON
cmake --build build/origami
ctest --test-dir build/origami --output-on-failure
```

這些是預定入口；正式報告要保存 integration branch 上實際可執行的完整命令與 exit code。

### 7.3 TuningDriver 與 baseline provenance

向 owner 取得：

- artifact location 與 revision；
- `--convert-config` 是否仍為正式入口；
- license／internal use permission；
- 輸出和 `GFX942GAParams` 是否語意等價；
- 一份可 hash 的代表輸出或書面 attestation。

判讀：

- 有可重現證據：登錄 `original_tuningdriver`；
- owner 確認不可取得，但其他研究授權正常：登錄 `geko_gfx942_proxy`，可繼續 proxy-only；
- 狀態 unknown：M01 baseline gate blocked；
- 研究／資料授權被拒：停止相關實驗，不用 proxy 繞過。

### 7.4 Production fitness 與 correctness

1. 從**實際 generated YAML／client command**讀 `soo/reduce_fn`。
2. 確認所有 arms 使用相同 fitness aggregation。
3. 分層查核 correctness：
   - Tensile Python `GlobalParameters` 一般預設為 128；
   - standalone client CLI 沒傳 flag 時預設 0；
   - workflow YAML／backend 可能 override。
4. 正式 policy 只採實際 run 的 resolved 值；`0` 永遠不算 correctness evidence。
5. 在第一次使用 correctness gate 前，由 owner/contract 鎖定 development 與 final champion 的 count、edge cases、tolerance、failure handling。

### 7.5 Canonical mapping smoke

對一個已完成 derived/codegen 的 solution：

1. 保存 raw config、derived solution 與 generated artifact；
2. 確認 `-1/-2` sentinel 已解析；
3. 透過 `ContractionSolution::getSizeMapping()` 取得欄位；
4. effective GSU 使用 `calculateAutoGSU()`；
5. `CUOccupancy` 與 `MathClocksUnrolledLoop` 必須為有效正值；
6. 產生一筆 Origami estimation 與一筆適用時的 Formocast simulation；
7. 保存逐欄 audit，不只保存 prediction。

M01 只證明一條 canonical 路徑可行；批次 parity、ordering 與 weights 在 M02 處理。

### 7.6 Generate → compile → benchmark smoke

至少執行：

- 一個 non-StreamK gfx942 case；
- 一個 StreamK gfx942 case；
- 每個 case 有 non-zero correctness；
- 生成、編譯、載入、benchmark、輸出解析都成功；
- M00 telemetry 可和 subprocess／CSV 對帳。

### 7.7 Noise pilot

1. 固定單一已知穩定 kernel 與 shape。
2. 5 warmup + 20 timed iterations，取 median。
3. 以獨立重跑計算 CV；CV >0.5% 時依 contract 增加 timed iterations。
4. iteration escalation 的上限與停止規則在看 paired treatment 前鎖定。
5. 若仍不穩，檢查 clock、temperature、同機 load、NUMA、power、cache warmup。

## 8. Controls 與 measurement boundary

固定：

- 同 GPU、device、clock/power policy；
- 同 revisions、generated YAML fitness、correctness；
- 同 shape、kernel、warmup/timed iteration；
- 同 runner/schema。

要記錄但不混用：

- kernel runtime；
- compile time；
- end-to-end wall time；
- correctness result；
- environmental drift。

## 9. 驗收、否證與停止條件

- **M01.ACC.HW**：`rocminfo` 明確有 gfx942，environment fields 完整。
- **M01.ACC.BUILD**：所有鎖定 revisions build/test 通過，無未記錄 patch。
- **M01.ACC.SMOKE**：non-StreamK、StreamK generate→compile→benchmark→correctness 成功。
- **M01.ACC.BASELINE**：baseline provenance 不再是 unknown，claim scope 可 machine-check。
- **M01.ACC.FITNESS**：所有 arms 的實際 `soo/reduce_fn` 相同且已保存。
- **M01.ACC.MAPPING-SMOKE**：canonical solution 沒有 unresolved sentinel／invalid metadata。
- **M01.ACC.NOISE**：按鎖定 protocol 達到 CV≤0.5%，或 owner 事前批准新的研究門檻。
- **M01.FAL.ENV**：無 gfx942、GPU node unusable 或 noise 無法控制，禁止 GPU 結論。
- **M01.FAL.METADATA**：必需 metadata 只能用猜值補，禁止 Formocast 正式 arm。
- **M01.STOP.AUTH**：研究或資料授權被拒，停止；TuningDriver artifact 不可得但研究授權正常只縮小 claim。

## 10. 預期狀況、診斷與解法

### 狀況 A：`rocminfo` 只有 CPU

- 診斷：保存 warning、driver/module、device permission、container device mapping。
- 解法：移到有 MI300X 的 node，或修正 runtime/device mount。
- 狀態：M01.ALL blocked；M00 與 M02 CPU-only 部分可繼續。

### 狀況 B：三個 branches API drift

- 診斷：保存第一個 compile/test failure 與相關 SHA。
- 解法：建立最小 integration adapter，避免順手改演算法；adapter 必須有 unit/parity test。
- 無法解：M01.SW blocked。

### 狀況 C：production YAML 的 `soo` 和預期不同

- 解法：以 generated YAML 為真；所有 arms 重生相同 aggregation，舊資料不得混比。

### 狀況 D：TuningDriver 找不到

- 解法：取得 owner 的「不可得」明確答覆後轉 proxy-only；不能在 unknown 狀態自行推定等價。

### 狀況 E：correctness resolved value 是 0

- 解法：在 protocol 中設非零 policy並重跑；既有 run 只能算 performance smoke，不能算 correctness pass。

### 狀況 F：CV 持續超標

- 解法：增加 iteration、控制 clock/load、分時重跑；若超過事前上限仍不穩，標 `blocked-by-noise`，不放寬門檻後宣稱通過。

## 11. 執行完成後的報告

完成或明確失敗後才建立：

`../reports/m01-step0-integration-gate-report.md`

報告需直白列出每個 gate 的 PASS/FAIL/BLOCKED、實際 revisions/commands、TuningDriver 回覆、actual YAML、noise 數字、correctness policy、遇到的整合問題與解法。M01 若未通過，報告不得包含任何暖啟動效能結論。
