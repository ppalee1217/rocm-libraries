# Ductile / GEKO / GA tuning 生態筆記（研究線）

> **狀態：已依 Confluence 內容擴充（2026-07-08）。** 這是研究線（surrogate-assisted DSE）的背景參考。
> 五份權威來源已抓成本地副本存於 [../internal_docs/](../internal_docs/)（見該資料夾 README 的「Ductile / GEKO / GA tuning」區塊）。
> 對應 roadmap：**P1 07-08 生態定位**、**P2 07-11 工具生態**、**P3 切角選定**。

## 為何需要這份

方向轉研究線後，主線鎖定「tuning 層的評估成本」。動手前要先把**誰做什麼、我切哪一層、對接哪個
既有工作**弄清楚，避免與正職重疊（核心 Ductile / GEKO 由正職主導）。

## 一句話生態定位

- **tuning 層（決定有哪些 kernel、每個 shape 最佳參數）**：`Tensile/bin/Tensile`（grid 窮舉）、
  **Ductile**（GA backend）、**GEKO**（編排，預設 `--backend ductile`）。
- **selection 層（挑現有 solution）**：equality + grid-based、Origami、**Formocast**（模擬式效能預測）。
- **研究主線**：用既有 / 自產 `2_BenchmarkData` CSV 做 offline 建模，降低 tuning 層評估成本；**不動
  正職維護的 Ductile / GEKO 核心**。offline 建模資料**全部在 MI300（gfx942 / CDNA3）上生成**；
  **MI350（gfx950 / CDNA4）為後續需要時才 migrate 的目標**（見 [surrogate-dse-plan.md](surrogate-dse-plan.md) 平台範圍）。

## 名詞澄清（我之前容易混的）

| 名詞 | 屬哪層 | 一句話 |
|---|---|---|
| Ductile | tuning | 用 GA 取代 grid 笛卡兒積窮舉，少量評估找好解 |
| GEKO | tuning 編排 | 讀 log → 產 config → 跑 tuning（grid/GA）→ merge library |
| Grid Search | tuning | `ForkParameters` 笛卡兒積全跑 benchmark，決定性但成本爆炸 |
| Origami | selection | 結構化 heuristic / ML 模型挑 solution |
| Formocast | selection | 模擬式效能建模，不窮舉 benchmark 就預測 kernel 效能 |

## 對接的既有工作

- **JIRA `SWDEV-477426`**「Create a genetic algorithms driven search for building solution libraries」
  （負責人 William Gilmartin，SolutionSelection team）。與研究主線最相關的 scope：
  - scope 2：**completeness 指標**——證明「任意 size 都有近最佳 kernel」。
  - scope 4：**analytics 驅動搜尋**——用分析讓搜尋更有效率（＝研究切角 #1）。
  - 不在 scope：build solution selection model（那是 selection 層的事）。
- **Performance team roadmap 會議（2026/05/15）** — [../meeting_notes/GEMM-Optimization-Roadmap-Origami-Tile-Selection-摘要.md](../meeting_notes/GEMM-Optimization-Roadmap-Origami-Tile-Selection-摘要.md)。他們的 macro tile tuning 用改造過的 GA「固定 tile、對多尺寸一起 tune」（一個 tile 約 15 尺寸、2–3 hr/GPU），並用 Origami 做尺寸→tile mapping 與 greedy tile selection。**關鍵觀察：他們用 Origami 決定「tune 什麼、留什麼」，但沒有用它暖啟動 GA 的參數搜索**——後者正是本研究線的切入點（省那 2–3 hr/tile）。詳細 gap、可立即試的實驗（max-min fitness ↔ regression 保護、量化 Origami 假設）與邊界，見 [surrogate-dse-plan.md](surrogate-dse-plan.md) §3 對接團隊 pipeline（含 §3.2 循環依賴、§3.3 邊界）。

## 參考來源（本地副本 + 我的 summary）

> 已於 2026-07-08 用 cloud_atlassian 抓取，存成本地 markdown 副本（連結指向 `../internal_docs/`）。

- **Ductile 與 TensileLite Tuning 深入比較** — [ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md)（原 `1772982240`）
  - *我的 summary：* 主軸是「窮舉 grid vs 啟發式 GA」兩端。TensileLite 對 YAML `ForkParameters` 做笛卡兒積、決定性、可重現，適合 baseline / broad coverage，但空間隨維度指數爆炸。Ductile 把每組參數當染色體，fitness = 實測 GFLOPS（benchmark-driven），`--convert-config` 會把 gene 值域擴張（如 GRVW `[2,8]→[-1,-2,2,3,4,6,8]`），能探出 grid 外的解；代價是隨機性 + 多 shape 混 tune 會收斂到折衷解。**最關鍵給研究線的一句：** 建議分層 —— 先 Dense Search 確認 selector 有沒有用好既有 library，再 TensileLite 擴 kernel pool，最後才對 few hot shapes 上 Ductile。多數「效能不好」其實是 selection 問題而非缺 kernel。
- **GEMM Kernel Optimization / GEKO** — [gemm-kernel-optimization-geko.md](../internal_docs/gemm-kernel-optimization-geko.md)（原 `1186895430`）
  - *我的 summary：* GEKO 是編排層 Python framework，三種模式：`--tune`（configure→optimize，GA backend 預設 `ductile`，也可 `tensile` grid）、`--search`（dense benchmark 既有 solutions，分鐘級）、`--bench`（純量測）。輸出結構清楚：`optimizations/build_*/3_LibraryLogic/*.yaml` → merge 成 `final_libs/` → `TensileMergeLibrary` 回寫。研究線可直接複用它的 log 解析（`bench.log`）、`summary.csv`/`gemms.csv` 產物與 `--search` 當 offline 資料來源。
- **Formocast Design RFC** — [formocast-design-rfc.md](../internal_docs/formocast-design-rfc.md)（原 `1304232451`）
  - *我的 summary：* selection 層的模擬式效能預測（不窮舉 benchmark）。把 kernel 執行拆成 init/prefetch/loop/tail/LSU/GSU/store 等成本，用 HW 參數模擬 issued cycles 選最佳解。與研究主線（用建模降低評估成本）是同一思路的近親 —— 差別是它做 physics-based 模擬，我的研究線偏 data-driven surrogate。
- **Difference between Origami and Formocast** — [origami-vs-formocast.md](../internal_docs/origami-vs-formocast.md)（原 `1304199634`）
  - *我的 summary：* Origami ~90% vs Formocast ~95% exact-tuning；Origami 快、支援 Triton + StreamK、小 pool + auto WGM；Formocast 用更多 tensilelite 參數與更細的 L1/L2/L3 cache 模型、目前 tensilelite-only 且 non-StreamK。整合方向：Formocast 併入 origami subfolder，Origami 當 GEMM 前端（PR #3735）。Formocast 主賣點是用 `PredictionThreshold` 縮短 tuning 時間 —— 這正是研究線可對接的「減少評估」施力點。
- **Solution Selection Metrics** — [solution-selection-metrics.md](../internal_docs/solution-selection-metrics.md)（原 `744174730`）
  - *我的 summary：* 定義三種 efficiency（vs ideal / vs hand-tuned / vs 競品硬體）與量測步驟（sweep sizes 量 FLOPS → 找 unique kernels → 對比 cuBLAS）。內容多為 mi100/a100 舊儀表板截圖（未鏡像）。對研究線的用途：提供「completeness / efficiency 指標」的既有定義，可對應 SWDEV-477426 scope 2。
- JIRA：`SWDEV-477426`
- 內部總參考：[hipblaslt-tensilelite-reference.md](../internal_docs/hipblaslt-tensilelite-reference.md) Module B

## 待補（自己寫）

- [x] Ductile 的染色體具體包含哪些 gene、`--convert-config` 擴張了哪些值域
  - gene：`DepthU`, `GlobalReadVectorWidthA/B`, `NonTemporalA/B/C/D`, `StaggerU`, `WorkGroupMapping`, `StreamK`, `VectorWidthA/B` 等（每個參數/離散選項一個 gene）。
  - `--convert-config` 擴張例：GRVW `[2,8]→[-1,-2,2,3,4,6,8]`；`NumElementsPerBatchStore`、`NonTemporal*`、`StaggerU`、`WorkGroupMapping/XCC` 改為更廣的離散集合。細節見 [ductile-tensilelite-tuning.md](../internal_docs/ductile-tensilelite-tuning.md) §3.2。
  - **擴值實作已定位（2026-07-22 程式碼查證）**：真正決定「擴哪些/擴多少」的 in-repo 邏輯在 **GEKO config generator**（branch `origin/users/pkamd/geko_pr`）：`projects/hipblaslt/utilities/geko/geko/config_generator/fork_params/hw_profiles/gfx942/optimization_param.py`。機制＝**兩套 per-arch profile**（`GFX942Params` heuristic 窄 vs `GFX942GAParams` GA 寬，由 `config["GA"]` 切換），多數參數硬寫寬離散清單，GRVW 則由 `_compute_grvw()` 依資料型別 byte 數的 dword/dwordx4 約束算 `[-1,-2] + valid[min..max]`（fp16 → `[-1,-2,2,3,4,6,8]`）。**這是靜態 per-arch/per-dtype 規則、不看 per-shape、不跑模型**——正是研究主線要補的縫。逐行拆解見 [../geko-ductile/ga-algorithm-implementation.md](../geko-ductile/ga-algorithm-implementation.md) 3.5 節末的 `--convert-config` 實作說明。
- [x] GEKO `--tune` 的實際流程與輸出（`build_*/3_LibraryLogic`、`final_libs/`）
  - 流程：configure（解析 log→分 GEMM type→產 tensilelite config）→ optimize（GA via Ductile 跨 GPU tune→merge→benchmark→filter）→ integrate（`TensileMergeLibrary` 回寫→rebuild）。
  - 輸出：`optimizations/build_*/3_LibraryLogic/*.yaml`（per-GEMM logic）→ merge 成 `libs/`→ 篩選後 `final_libs/gfx*_*.yaml`。細節見 [gemm-kernel-optimization-geko.md](../internal_docs/gemm-kernel-optimization-geko.md)。
- [x] Ductile / GEKO / TuningDriver repo 是否可取得（07-08 與 mentor 確認；2026-07-22 程式碼查證補齊）
  - **GEKO**：位於 `projects/hipblaslt/utilities/geko`，在 branch `origin/users/pkamd/geko_pr`（隨 hipBLASLt checkout 提供，不需另外 clone）。
  - **Ductile GA 引擎**：在 branch `origin/ductile_integration` 的 `projects/hipblaslt/tensilelite/Tensile/ductile/`（GA 引擎）與 `Tensile/backends/ductile_backend.py`（與 TensileLite 串接）；不在 develop / working tree。
  - **`--convert-config` CLI flag**：把上述兩個 branch 的 hipblaslt 樹 grep 過皆**查無**此字串 → 屬**外部 Ductile `TuningDriver`**（不在本 repo）。但其「值域擴張」的等價邏輯在 GEKO config_generator（見上一則）。**待確認：** 外部 TuningDriver 本身是否需另外授權。
- [ ] 我的研究切角與正職工作的邊界（避免重疊）
