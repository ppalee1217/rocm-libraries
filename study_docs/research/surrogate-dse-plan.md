# Surrogate-assisted DSE 研究計畫（資料集 + 三切角 + metric）

> **狀態：待擴充（outline）。** 這是研究主線的執行骨架，隨 P2（資料 pipeline / analytics）與 P3
> （切角定案與迭代）補齊。對應 roadmap：**P2 07-11 / 07-14~22**、**P3 07-23~08-13**。

## 研究命題

GEMM tuning 現行靠 grid search 笛卡兒積窮舉 benchmark 建表；每次 codegen / config 一改就要重跑，
成本高、擴展慢。**用 prediction / surrogate 降低評估成本、加快 DSE**，量化「省下多少評估、DSE 加速多少」。
（與 NPU tile-level DSE 的 profiling-reuse 命題同構；見 roadmap Context。）

## 資料集 schema（P2 產出，三切角共用地基）

來源：`Tensile/bin/Tensile` 產出的 `2_BenchmarkData/*.csv`，經 pipeline 正規化。

| 欄位群 | 內容 | 備註 |
|---|---|---|
| gene（特徵） | `DepthU`、`MatrixInstruction`、`WorkGroup(Mapping)`、`GlobalReadVectorWidth`、`StaggerU`、`PrefetchGlobalRead/LocalRead`、`GlobalSplitU`… | 只取**自由 gene**，避免用衍生量造成共線性 |
| problem | `M,N,K,batch`、`dtype`、transpose | shape 描述 |
| label | `GFLOPS`（fitness） | 取中位數、固定 iteration 降噪 |
| （選配）counter | rocprof-compute 抓的 HBM BW%、VALU busy… | 供 feature / 分析 |
| 環境 | GPU、ROCm、driver、iteration、config 版本 | 可重現、避免跨環境不可比 |

切分原則：**按 shape / config 分組切 train/val**（避免 leakage），非隨機切列。

## 評估 metric（對應下游用途）

- **rank correlation**（Spearman / Kendall）：predictor 排序 gene 的能力。
- **top-k 命中率**：pre-screen 後保住真正 top-1 / top-k 的比例。
- **省下的評估次數**：達到同等 quality 下，比純窮舉少跑多少 benchmark。
- **efficiency vs ideal**（Solution Selection Metrics `744174730`）：相對 best-of-pool 的效率。
- **tuning-time vs quality 取捨曲線**：研究主線的核心圖。

## 三切角（P3 kickoff 依決策樹選定，見 roadmap P3）

### 切角 #1 — 搜尋空間 analytics / completeness（最低風險、純分析）
- 產出：feature importance、landscape 平滑度、completeness 指標（`SWDEV-477426` scope 2/4）。
- 假設（待填）：______
- 成功 metric（待填）：______

### 切角 #2 — surrogate-assisted tuning（最貼近命題）
- 產出：predictor（gene→GFLOPS/排序）→ pre-screen candidate → 量省下的 benchmark 次數 + 取捨曲線。
- 假設（待填）：例「predictor pre-screen 可在保住 top-1 前提下省 X% benchmark」
- 成功 metric（待填）：______

### 切角 #3 — 跨 codegen profiling 重用（最 novel，需跨版本資料）
- 產出：codegen 改版前後排序保留度 → correction / transfer model → re-profiling 減少量。
- 假設（待填）：______
- 成功 metric（待填）：______
- 前提：能否取得跨 codegen 版本的 benchmark 資料（07-08 / kickoff 確認）。

## 研究迭代日紀律（P3）

一次只改一個變因（特徵 / 模型 / 資料切分 / pre-screen 比例）→ 在 held-out validation 算 metric →
對照 baseline → 記錄 hypothesis / 改動 / 數字 / 結論。避免 leakage 與過擬合。

## 待補（自己寫）

- [ ] pipeline 的可貼指令與 `dataset.csv` 實際 schema
- [ ] baseline predictor（線性 / RF / xgboost）的初始數字
- [ ] 選定的主切角 + 備援切角、定案假設與 metric
- [ ] 結果圖表（取捨曲線、feature importance）
