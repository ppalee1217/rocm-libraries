# GEMM Heuristics（Solution / Heuristics Selection 效率評估）

> **Source URL:** https://amd.atlassian.net/wiki/spaces/MLSE/pages/744198388/GEMM+HEURISTICS
> **pageId:** `744198388`
> **Space:** MLSE (Machine Learning Software Engineering)
> **Version:** 58
> **Fetched on:** 2026-07-09 (via Atlassian Confluence MCP, `convert_to_markdown=true`)
>
> 本檔已由舊版更新。原本對應的頁面是 2022 年的「Solution Selection Metrics」(pageId `744174730`)，
> 內容以 **MI100 vs A100**、rocBLAS F32/F64 為主，MI100 屬 CDNA1 舊架構，現已參考價值偏低。
> 現改為對應同主題、但涵蓋 **現代架構 (MI300X / MI350 / MI355)** 與 **現代函式庫堆疊 (hipBLASLt / TensileLite)** 的
> 「GEMM HEURISTICS」initiative 頁面。
>
> 一句話總結：這頁在講「怎麼衡量並提升 AMD GPU 上 GEMM 函式庫『開箱即用 (OOB) 的自動選核 (heuristics) 效率』，
> 並和 NVIDIA cuBLASLt 做對比」，是舊頁「solution selection 效率評估」的現代版延續。

---

## 名詞先講白話（why / what）

在往下讀之前，先把幾個關鍵字用白話講清楚：

- **GEMM**：General Matrix Multiply，一般矩陣乘法。它是深度學習 / HPC 裡最吃效能的核心運算，函式庫效能好不好，很大程度就看 GEMM。
- **Solution / Kernel selection（解法/核心選擇）**：對同一個矩陣尺寸 (M, N, K)，函式庫內部通常有很多個預先產生的 GPU kernel 可以用。「selection」就是**在執行當下自動挑一個最快的 kernel**這件事。
- **Heuristics（啟發式選核）**：就是上面那個「自動挑 kernel」的決策邏輯。舊頁叫它 *solution selection*，現代 hipBLASLt 生態習慣叫它 *heuristics*，指的是同一件事。
- **Heuristics efficiency / Selection efficiency（選核效率）**：白話就是「自動挑到的 kernel，效能有多接近『這台機器上最好的那顆 kernel』」。
  例如 90%，代表自動選出來的 kernel 大約跑到理想最佳 kernel 的九成速度。這是本主題最核心的指標。
- **OOB / OOTB（Out-of-the-Box，開箱即用）**：使用者不做任何手動調校，直接呼叫函式庫時的效能。目標是「Day-1 就有高效能」。
- **hipBLASLt / TensileLite**：AMD 現代的 BLAS-like GEMM 函式庫堆疊，對標 NVIDIA 的 cuBLASLt；TensileLite 負責產生底層高效能 GEMM kernel。取代舊時代的 rocBLAS / Tensile。
- **Origami**：一種「硬體感知的解析式 (analytical) 解法選擇」方法，用數學/架構知識直接推算好的 GEMM 分塊 (tiling)，而不是純靠查表。是這頁裡選核策略的重點技術之一。

---

## 這個 initiative 在做什麼（GOALS）

來源頁把整件事定位成一個 initiative（跨團隊的推進項目），核心目標：

> **Delivering high performance OOB GEMM Libraries.**
> **Generate high performance OOB GEMM libraries on day one!**
> **Match or exceed the NVIDIA Heuristics Performance.**

白話：讓 AMD GPU 上的 GEMM 函式庫**一裝好、不用手動 tuning 就有高效能**，而且它的**自動選核效率要追平、甚至超越 NVIDIA**。

> 對照舊頁 (744174730) 的三個 objective，可以看到主題是一脈相承、只是升級到現代硬體與現代量測方法：
> 1. solution selection efficiency **vs ideal**（對比理想/最佳效能）→ 現以 MAF/MAB「硬體上限」當作理想基準。
> 2. solution selection efficiency **vs hand tuning**（對比手動調校）→ 現以 Origami / Auto-Tuning 的對比呈現。
> 3. solution selection efficiency **vs competitor hardware**（對比競品）→ 現以 hipBLASLt vs NVIDIA cuBLASLt 直接對打。

## 主要工作流（Workstreams 摘要）

來源頁用「Workstream」拆分工作，以下是重點整理（狀態大多為 Done/On track）：

- **WS1 — StreamK**：一種把工作沿 K 維度切分、讓 GPU 上所有 CU 都吃滿的 GEMM 排程法。
  已在 **MI350X** 設為預設、**MI300X** 支援（opt-in），並在推動 MI200 / NAVI3 / NAVI4 採用。
- **WS2 — Origami（Hardware-Informed Analytical Solution Selection）**：把「選核」從查表改成用架構知識解析式推算的技術移轉。
  已驗證在 **MI350** 上 f8/f16 平均比 Auto-Tuning 好 10%~54%，並整合進 hipBLASLt、TritonBLAS、RocRoller(MX 資料型別)。
  （相關開源：`ROCm/tritonBLAS`、`ROCm/origami_paper`。）
- **WS3 — Heuristics Improvement: ML for Kernel Selection**：用機器學習改善選核。
  已在 hipBLASLt/MI300X 實驗性導入 **MLPNet**；另有「Two Towers」嵌入+回歸模型在訓練中。
- **WS4 — Dashboard 量測與對比競品（重點！這對應舊頁的「metrics + 對比 cuBLAS」）**：
  - 設計一組 **KPI/metrics** 衡量 heuristics 好壞，並和 NVIDIA 對比（簡報：`OOBMetrics.pptx`）。
  - 把 GEMM 依特性分成約 **20 類**（延伸自 latency / memory-bound / compute-bound 的簡單分法），用來找出 heuristics 在哪類尺寸上比較弱。
  - **Benchmark 自動化**，同時量 hipBLASLt 與 cuBLASLt：
    - hipBLASLt 工具：`ROCm/hipblaslt-benchmarking-tool`
    - cuBLASLt 工具：`ROCm/cublaslt-solution-selection-benchmark`
  - **對比 NVIDIA**：實測 cuBLASLt 的 heuristics 效率約 **97–99%**，作為 AMD 追趕的基準。
  - 標準化 Dashboard 呈現硬體上限：MI300X / MI350 / MI355 的 **MAF (Max Achievable FLOPs)** 與 **MAB (Max Achievable Bandwidth)**。
- **WS5 — Tuning Automation**：TuningDriver 支援 StreamK 與 MI350X、產生 OOB 函式庫，並研究用基因演算法自動挑參數。

## 現代選核效率的量化數字（補充來源）

以下數字來自同空間、持續更新中的狀態頁 **「GEMM Programs Status」**（pageId `1662987250`, MLSE, Version 155，內含至 2026-07-08 的資料），
其中 **Kernel Selection**（owner: Nelson, Bryant）一列給出了現代架構上的實測「選核效率」，可視為舊頁「solution selection efficiency」的直接現代對應值：

- **Selection Efficiency（選核效率）**（2026-07 附近數據）：
  - MI350：Mean ≈ **90.36%**
  - MI355：Mean ≈ **93.49%**、Median ≈ 97.22%
  - MI4xx：N/A（尚在導入）
  - 年底目標：MI350/MI355 ≥ 95%、MI4xx ≥ 90%
- **Solution Selection Time（首次呼叫的選核耗時，MI350 BF16 全 transpose）**：
  - Mean ≈ **136.1 µs**、每個 kernel 約 **27 ns**（目標 Mean < 100 µs、每 kernel ≤ 27 ns）
- **Origami 已整合的函式庫**：hipBLASLt、Triton、CK、Torch、TraceLens
- **支援的演算法**：GEMM、Attention

> 註：這些數字會隨時間更新，引用時請以來源頁當下版本為準（連結：
> https://amd.atlassian.net/wiki/spaces/MLSE/pages/1662987250/GEMM+Programs+Status）。

## 圖檔 / 附件

來源頁「GEMM HEURISTICS」帶有幾張截圖（圖檔未下載，僅保留 Confluence 附件連結）：

- image-2024-11-10_17-40-0.png — [下載](https://amd.atlassian.net/wiki/rest/api/content/744198388/child/attachment/att745425061/download)
- image-2024-11-10_16-43-6.png — [下載](https://amd.atlassian.net/wiki/rest/api/content/744198388/child/attachment/att745161744/download)
- image-2024-11-10_15-27-45.png — [下載](https://amd.atlassian.net/wiki/rest/api/content/744198388/child/attachment/att745162073/download)

## 相關的其他新頁面（延伸閱讀）

搜尋過程中找到的其他現代相關頁面（皆為實際搜尋/抓取結果，非杜撰）：

- **GEMM Performance Dashboard** — pageId `744192559`, MLSE：定義衡量 GEMM 相對效能的 metrics、GEMM 取樣、AMD Instinct 與 NVIDIA 的 benchmark 工具、roofline。
  https://amd.atlassian.net/wiki/spaces/MLSE/pages/744192559
- **GEMM Programs Status** — pageId `1662987250`, MLSE：跨程式的狀態儀表板，含 Kernel Selection 選核效率 / 選核耗時實測（見上一節）。
  https://amd.atlassian.net/wiki/spaces/MLSE/pages/1662987250
- **Solution selection** — pageId `744176549`, MLSE：提出以 grid-based 取代 distance-based 選核，把搜尋複雜度從 O(M×N×K) 降到 O(log M + log N + log K)。
  https://amd.atlassian.net/wiki/spaces/MLSE/pages/744176549
- **Hipblaslt Creation and Kernel Selection** — pageId `1403711078`, MLSE：hipBLASLt 建立與選核流程。
  https://amd.atlassian.net/wiki/spaces/MLSE/pages/1403711078
- **Tensilelite - GEMM kernel generation** — pageId `1405990433`, MLSE：TensileLite 如何產生 GEMM kernel。
  https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433
- **Dashboard: hipBLASLt GEMM Tuning** — pageId `1045306155`, MLSE：hipBLASLt 效能調校的 executive dashboard。
  https://amd.atlassian.net/wiki/spaces/MLSE/pages/1045306155

---

## 前身頁面（已過時，僅供追溯）

- **Solution Selection Metrics（2022, MI100 vs A100）** — pageId `744174730`, MLSE, Version 11。
  舊頁以 rocBLAS 在 MI100(CDNA1) 對 A100 的 F32/F64 FLOPS 及 kernel selection 儀表板截圖為主。
  該頁本身沒有子頁面 (children = 0)；主題已由本檔對應的現代頁面延續，舊頁保留供歷史追溯。
  https://amd.atlassian.net/wiki/spaces/MLSE/pages/744174730/Solution+Selection+Metrics
