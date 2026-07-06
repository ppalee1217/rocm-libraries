# Ductile / GEKO / GA tuning 生態筆記（研究線）

> **狀態：待擴充（outline）。** 這是研究線（surrogate-assisted DSE）的背景參考骨架，隨 P1（07-08）、
> P2（07-11）學習補齊。對應 roadmap：**P1 07-08 生態定位**、**P2 07-11 工具生態**、**P3 切角選定**。

## 為何需要這份

方向轉研究線後，主線鎖定「tuning 層的評估成本」。動手前要先把**誰做什麼、我切哪一層、對接哪個
既有工作**弄清楚，避免與正職重疊（核心 Ductile / GEKO 由正職主導）。

## 一句話生態定位

- **tuning 層（決定有哪些 kernel、每個 shape 最佳參數）**：`Tensile/bin/Tensile`（grid 窮舉）、
  **Ductile**（GA backend）、**GEKO**（編排，預設 `--backend ductile`）。
- **selection 層（挑現有 solution）**：equality + grid-based、Origami、**Formocast**（模擬式效能預測）。
- **研究主線**：用既有 / 自產 `2_BenchmarkData` CSV 做 offline 建模，降低 tuning 層評估成本；**不動
  正職維護的 Ductile / GEKO 核心**。

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

## 參考來源（Confluence page id / JIRA key）

> 用 cloud_atlassian 抓取（同 `amd.atlassian.net/wiki` 站）。待各項讀完後在此補一段自己的 summary。

- Ductile 與 TensileLite Tuning 深入比較：`1772982240`（染色體、fitness、`--convert-config`、grid vs GA 取捨）
- GEMM Kernel Optimization / GEKO：`1186895430`
- Formocast Design RFC：`1304232451`
- Difference between Origami and Formocast：`1304199634`
- Solution Selection Metrics：`744174730`（efficiency vs ideal）
- JIRA：`SWDEV-477426`
- 內部總參考：[hipblaslt-tensilelite-reference.md](../internal_docs/hipblaslt-tensilelite-reference.md) Module B

## 待補（自己寫）

- [ ] Ductile 的染色體具體包含哪些 gene、`--convert-config` 擴張了哪些值域
- [ ] GEKO `--tune` 的實際流程與輸出（`build_*/3_LibraryLogic`、`final_libs/`）
- [ ] Ductile / GEKO / TuningDriver repo 是否可取得（07-08 與 mentor 確認）
- [ ] 我的研究切角與正職工作的邊界（避免重疊）
