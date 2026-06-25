# hipBLASLt / TensileLite 實習學習 Roadmap（8 週）

> **這份是 canonical（唯一可編輯來源）。** 另有兩份只讀 mirror：Claude Code plan 檔
> （`~/.claude/plans/rocm-libraries-repo-familiar-starry-aurora.md`）與 `../.cursor/learning-roadmap.md`。
> 要改 roadmap **一律改本檔**；在 Claude Code 內改本檔會自動同步兩份 mirror，在 Cursor 內或直接改
> mirror 則需手動同步（見 `../CLAUDE.md`）。

## Context（為什麼做這份計畫）

你是短期實習生（剩近 2 個月，從 2026-06-25 起算 ~8 週），目標是「熟悉 hipBLASLt 與
TensileLite、寫 GPU kernel 熟悉 AMD ISA」，最終要在 main repo 有**多顆 commit**，並完成
一個 **GEMM kernel 優化且被 tensilelite 實際採用**。短期硬截止：**下週三 2026-07-01** 前要把
codebase / workflow 摸熟、HIP 練熟。

本計畫評估了兩份既有資產並把它們融合成一條可執行的學習軌：

- **`study_docs/`（rocm-libraries 內）** — 偏「看懂現有系統」（Track 1）：runtime-flow →
  tensilelite-pipeline → gemm-optimization → profiling-rocprof，外加 architecture 導覽。
  深度足夠當系統地圖，但 Track 2（動手 ISA）只有方法論，可跑範例靠 `asm/` 補上。
- **`asm/`（主管未完成的教材）** — 補上 study_docs 缺的實作半邊。四個**完整可編譯、
  重注解**的 gfx942 範例，自成漸進：
  - `example01_reduce_sum` — 手寫 AMDGCN reduce baseline + HIP launcher + CMake。
  - `example02_reduce_sum` — 用 rocprof-compute 找瓶頸 → 改 `global_load_dwordx4` 優化（1.9×），
    附完整 roofline / counter 解讀。**這是「profiling 驅動優化」的最佳範本**。
  - `example03_mfma` — **MFMA GEMM + LDS tiling**（`v_mfma_f32_16x16x4_f32`），最接近最終工作，
    附 ATT thread-trace（rocprof-compute-viewer）流程。
  - `example04_global_mem_oob` — buffer descriptor (V#) / `num_records` 邊界檢查的 ISA 深潛。

**結論：`asm/` 作為 Track 2 的實作骨幹**，與 study_docs 的 Track 1 交織。`asm/ex03` 是通往
真實 GEMM 優化的天然橋樑。（`asm/` 在 repo 外的同層 `/data1/perlee/asm`，容器內 `/src/asm`。）

### 環境現況（已驗證，省下數天）

- GPU：**gfx942 (MI300X)**；ROCm 6.4.0 在 host，另有 **ROCm 7.2.0 docker 容器 `perlee`**
  （`run.sh` 啟動，掛載 `/data1/perlee`→`/src`）。
- hipBLASLt **已建置完成**：`projects/hipblaslt/build/release` 存在，`hipblaslt-bench` 已可用。
  → 不必花時間從頭 build，可直接 bench / profile。
- `asm/` 各範例附 CMake，容器內 `cmake -S . -B build && cmake --build build` 即可跑。

### 學習者起點（據此校準節奏）

- 約 1.5 年前寫過簡單 CUDA/Triton（已大半忘），近期在補 GPU 硬體架構 + launch workflow + 軟硬體名詞。
  → **HIP 語法可快速帶過**（CUDA→HIP 幾乎一對一），P0 的 A-1/A-2 視為「喚回記憶 + 對照組語」。
- **讀得懂組合語言** → `asm/` 可加速看，gfx942 指令當增量學。
- **優化所知不深**（僅 occupancy、shared memory 資源控管）→ 把時間移到「優化 + profiling」，
  這是最薄弱、也是 P3 成敗關鍵。需補：memory coalescing / 向量化載入、latency hiding 與
  Little's Law、compute-bound vs memory-bound 判讀、roofline、occupancy↔暫存器/LDS 取捨、
  bank conflict。`asm/example02` README 是這些概念最好的單篇教材。
- **全職且願意加碼** → 進度表以工作日為主軸，里程碑排得積極，週末為彈性追進度/緩衝。

### 如何使用本 roadmap

- **每天一個小節**：標題格式 `### MM-DD（週幾）｜一句話主題`，底下是可勾選的
  checklist（`- [ ]`）。每天開工前掃一遍當天 checklist，收工前逐項打勾確認進度。
- **目的導向（重要）**：P0~P1 的主 item 以「**搞懂什麼 / 能做到什麼**」為主，而非「讀哪份文件」。
  每個主 item 底下有：可勾子項（拆成具體理解點）、一行 `✅ 完成判準`（自我驗證真的懂了）、
  一行 `📚 參考資源`（現有 doc / asm 行段 / codebase 路徑 / AMD 選做）。動手項（**跑** / **寫**）
  仍附可貼指令與預期輸出。
- **📚 參考資源是手段不是目的**：現有教學文件還不夠完整。資源若標記 **（待擴充：<doc>）**，表示
  該主題對應一份規劃中、目前只是 outline 的文件（清單見 `README.md`「規劃中文件」），會隨學習補齊；
  在它長好前，以同列其他資源 + codebase 為準。
- **（AMD 資源，選做）** 標記的 item 來自公司內部 HIP 課程與 GCN 架構 talk，是補充非必修；
  趕進度時可略過，完整對照見檔末「AMD 訓練資源對照表」。
- **兩層測驗**：每天有**內嵌快速自測**（題數視內容調整，答案收在 `<details>` 摺疊區，先自答再核對）；
  完成當天 item 後若想要更深入的檢核，向我要求啟動 `learning-quiz` skill——我會依當天目標生成
  互動測驗檔（放 `study_docs/quizzes/`）、批改你的作答、指出要回去補強的具體主題。
- **筆記自己寫**：每天的「筆記提示」列出該記什麼；筆記由**你親手寫**在 `study_docs/notes/`
  （檔名 `MMDD-{當天主題}.md`），用 `learning-notes` skill 開新筆記（含 template），我只協助補
  code / doc 連結，不代寫內容。
- **P0–P2 逐日詳列；P3–P4 框架化**（給里程碑、決策樹與可重複套用的迭代 checklist 模板，
  因為優化主線是開放式探索，無法預先寫死每天步驟）。

---

## 全程節奏總覽

| 階段 | 日期 | 主題 | 產出 |
|---|---|---|---|
| P0 | 06-25 ~ 07-01 | Codebase + workflow 摸熟、HIP 練熟（**硬截止**） | 能跑 bench/profile、自寫 HIP kernel 反組譯、讀懂 ex01/02 |
| P1 | 07-02 ~ 07-08 | AMD ISA 深化（ex03 MFMA / ex04 buffer）、tensilelite pipeline 實跑 | 讀懂 MFMA GEMM 組語、跑過一次 Tensile tuning |
| P2 | 07-09 ~ 07-22 | tensilelite 內部 + 第一批低風險 commit | 2~3 顆 main repo commit（小修/docs/config/test） |
| P3 | 07-23 ~ 08-13 | GEMM 優化主線：選題 → 調參/codegen → 驗證 → PR | 被 tensilelite 採用的優化 PR |
| P4 | 08-14 ~ 08-20 | 收尾、benchmark 報告、PR review 回應、buffer | 合併產出、實習總結 |

> 提醒：每個工作日都有單一可 follow 的目標（見下）。落後時用週末補；領先時把 P3 選題提前。

---

## P0：Codebase + Workflow 摸熟、HIP 練熟（06-25 → 07-01，硬截止）

階段目標：07-01 結束時，你能:
- (a) 講清楚 build-time / runtime 兩階段如何交接
- (b) 跑 `hipblaslt-bench` + rocprof 並看懂輸出
- (c) 自己寫 HIP kernel 並反組譯對照 gfx942 組語
- (d) 逐行讀懂 ex01/ex02 的組語與優化邏輯

關鍵檔案：`study_docs/{README,architecture/README,hipblaslt/*}.md`、
`asm/example01_reduce_sum/*`、`asm/example02_reduce_sum/*`、`amd-isa-kernel.md`。

### 06-25（四）｜建立全局地圖 + 進容器驗證工具

**今日目標**：對整個 repo 與 runtime 呼叫鏈有「一張地圖」，且容器內工具鏈全部可用。

- [ ] **搞懂** build-time vs runtime 兩階段分工，以及 repo 為何長這樣
  - [ ] 能說出「build 時 TensileLite 做食譜、runtime 時 hipBLASLt 查食譜出菜」這條主軸
  - [ ] 知道為何只有 `projects/hipblaslt` 是完整 source（sparse checkout），其餘是骨架
  - [ ] 分清 `library/`（runtime 本體）vs `tensilelite/`（build-time kernel 產生器）的職責
  - ✅ 完成判準：能用兩句話講出兩階段如何交接、各由哪個資料夾負責
  - 📚 參考資源：`study_docs/README.md`、`architecture/README.md`、`architecture/hipblaslt-layout.md`
- [ ] **搞懂** runtime GEMM 呼叫鏈：`hipblasLtMatmul` 如何一路走到 kernel launch
  - [ ] 入口無邏輯：`hipblasLtMatmul`（`library/src/amd_detail/hipblaslt.cpp`）只做型別轉換、轉呼叫
  - [ ] 收斂成問題：`rocblaslt_matmul_impl`（`rocblaslt/src/rocblaslt_mat.cpp`）把 descriptor
    收成一個 `RocblasltContractionProblem`
  - [ ] dispatch hub：`runContractionProblem`（`rocblaslt/src/tensile_host.cpp`）＝
    選 solution → `solve()` 產 launch 描述 → `launchKernels`
  - [ ] 出菜：`SolutionAdapter::launchKernel`（`tensilelite/src/hip/HipSolutionAdapter.cpp`）
    lazy `hipModuleLoad` 再 launch
  - ✅ 完成判準：能不看檔默述「API→problem→選 solution→solve→lazy load→launch」並指出每關卡的角色
  - 📚 參考資源：`study_docs/hipblaslt/runtime-flow.md`（關卡 1→5）；上列 4 個函式路徑
- [ ] **跑**：進容器並確認工具鏈可用
  ```bash
  bash run.sh            # 或 docker exec -it perlee bash
  which hipcc amdclang++ rocprofv3 rocprof-compute
  rocminfo | grep -m1 gfx     # 應顯示 gfx942
  ```
  - [ ] 成功進入容器
  - [ ] 四個工具 `which` 都印出路徑
  - [ ] `rocminfo` 確認是 gfx942
  - ✅ 完成判準：四個工具路徑齊全且確認 GPU 為 gfx942（MI300X）
- [ ] **（AMD 資源，選做）** GCN talk #1「GPU Overview and Scheduling Kernels」建立硬體心智模型
- **筆記提示**：把 runtime 呼叫鏈用自己的話各寫一句（每個函式做什麼）；記下容器內各工具的實際路徑。
  筆記寫在 `study_docs/notes/0625-建立全局地圖.md`（用 `learning-notes` skill 開）。
- **快速自測**（完成後想要深度測驗可用 `learning-quiz` skill）：
  1. 為什麼本機只有 `projects/hipblaslt` 有完整程式碼，其他庫只是骨架？
  2. runtime 選 kernel 是在「公開 API 層」還是「`tensile_host` 層」決定的？
  3. `RocblasltContractionProblem` 在這條鏈裡扮演什麼角色？
  <details><summary>答案</summary>
  1. 本機是 sparse checkout，只 check out hipBLASLt 全量；其餘為 build 骨架。
  2. 在 `tensile_host` 層（`runContractionProblem` → 依矩陣大小選 solution）。
  3. 把使用者 descriptor 收斂成「這次要解的問題」的單一真相來源，往下傳給 dispatch hub。
  </details>

### 06-26（五）｜跑通第一次 bench + 看懂 build/runtime 接點

**今日目標**：完整跑通一次 `hipblaslt-bench` 並看懂輸出欄位；說清楚磁碟上的兩階段接點。

- [ ] **搞懂** 磁碟上的兩階段接點：build 產物如何被 runtime 載入
  - [ ] 認識兩種產物：選擇表 `.dat`（MessagePack 二進位）與 kernel `.co`（code object）
  - [ ] 知道 runtime 尋找 library 的順序（env var `HIPBLASLT_TENSILE_LIBPATH` → 相對 `.so`）
  - [ ] 理解 lazy load：用到某 size 才載對應 shard / `.co`，不是一次全載
  - ✅ 完成判準：能畫出「build 產物 → 磁碟（`.dat`/`.co`）→ runtime lazy load」的接點圖
  - 📚 參考資源：`study_docs/hipblaslt/README.md`（建置產出 / runtime 載入兩節）
- [ ] **搞懂** build-time 三階段 pipeline 各自產出什麼
  - [ ] 階段 1 BenchmarkProblems：產生 + 編譯 + benchmark 候選 kernel
  - [ ] 階段 2 LibraryLogic：每個 size 從計時結果挑「贏家」solution
  - [ ] 階段 3 ClientWriter：打包成 library / client
  - ✅ 完成判準：能說出三階段各自的輸入與輸出、以及 `0_`~`4_` 目錄對應哪階段
  - 📚 參考資源：`study_docs/hipblaslt/tensilelite-pipeline.md`（待擴充：tuning-config-reference.md）
- [ ] **跑** 既有 bench（已建置完成，免重 build），把抽象呼叫鏈對應到真實輸出：
  ```bash
  ./build/release/clients/hipblaslt-bench -m 4096 -n 4096 -k 4096 -r f16_r --print_kernel_info
  ```
  - [ ] 指令成功跑完、印出結果列
  - [ ] 找到 solution name 欄位
  - [ ] 找到 solution index 欄位（記下來）
  - [ ] 找到 Gflops 欄位
  - ✅ 完成判準：能對照輸出講出「這次 heuristic 選了哪個 solution、跑多快」
  - 📚 參考資源：`projects/hipblaslt/clients/bench/README.md`（旗標）
- [ ] **（AMD 資源，選做）** HIP 200「HIP Tools」（~1.5h）的 ROCm Profiler/Tracer 段
- **筆記提示**：記下這次 bench 選到的 solution index 與 Gflops，P2 調參時會回頭對照。
  筆記寫在 `study_docs/notes/0626-跑通第一次bench.md`。
- **快速自測**：
  1. runtime 載入的選擇表是 YAML 還是 MessagePack？`3_LibraryLogic/` 的 YAML 是同一份嗎？
  2. 一次 build 產生很多候選 `.co`，最後「出貨」的是哪些？
  <details><summary>答案</summary>
  1. runtime 載入的是 MessagePack 二進位 `.dat`；`3_LibraryLogic/` YAML 只是可讀中間產物。
  2. 只留每個 size 的「贏家」solution（由 LibraryLogic 從 benchmark 結果挑出）。
  </details>

### 06-27（六，彈性）｜HIP A-1：第一支自寫 kernel + 反組譯

**今日目標**：寫出 vector add，反組譯對照基本 gfx942 指令家族。

- [ ] **搞懂** gfx942 執行模型的基本字彙（讀任何組語的前提）
  - [ ] wave = 64 lane；一個 wave 共用一個 exec mask
  - [ ] SGPR（全 wave 共用，放純量：指標/迴圈數）vs VGPR（每 lane 私有，放 per-thread 資料）
  - [ ] `s_waitcnt vmcnt`（等 HBM global load/store）vs `lgkmcnt`（等 LDS/scalar/kernarg）
  - ✅ 完成判準：能解釋為何同一段程式同時需要 `vmcnt` 與 `lgkmcnt` 兩種等待
  - 📚 參考資源：`study_docs/amd-isa-kernel.md`「前置：定位工具 / 階段 A-1」（待擴充：cuda-to-hip.md、isa/gfx942-isa-reference.md）
- [ ] **動手** 寫 vector add、反組譯、把組語對回原始碼
  ```bash
  hipcc --offload-arch=gfx942 --save-temps -c vadd.hip
  # 找 .s 檔，對照 A-1 的指令家族表
  ```
  - [ ] 寫出 vector add kernel
  - [ ] 編譯成功並找到 `.s` 檔
  - [ ] 在 `.s` 對照出 `s_load_*`（載 kernarg）
  - [ ] 對照出 `global_load_*`（讀 HBM）與 `v_add_f32`（運算）
  - [ ] 對照出 `s_waitcnt` 與 `s_endpgm`
  - ✅ 完成判準：能逐條指出 `.s` 裡每個指令家族對應原始 C++ 的哪一行
  - 📚 參考資源：`asm/example01_reduce_sum/`（同類手寫組語可比對）
- [ ] **（AMD 資源，選做）** HIP 101「Part A」（~2h，kernel language/thread hierarchy）；
  GCN talk #5「Compiling for gfx9」
- **筆記提示**：記下 `s_waitcnt` 的 `vmcnt` vs `lgkmcnt` 差別（你 06-29 會大量用到）。
  筆記寫在 `study_docs/notes/0627-第一支HIP-kernel反組譯.md`。
- **快速自測**：
  1. `s_waitcnt vmcnt(0)` 與 `lgkmcnt(0)` 分別等的是哪類記憶體操作？
  2. 一個 wavefront 有幾個 lane？exec mask 的作用是什麼？
  3. 同一個值該放 SGPR 還是 VGPR，依據是什麼？
  <details><summary>答案</summary>
  1. `vmcnt`＝向量記憶體（HBM global load/store）；`lgkmcnt`＝LDS/GDS/kernarg 等 scalar 類。
  2. 64 lane；exec mask 決定哪些 lane 實際執行（條件分支/邊界保護靠它開關 lane）。
  3. 全 wave 一致的純量放 SGPR；per-lane 不同的（如 index、載入值）放 VGPR。
  </details>

### 06-28（日，彈性）｜HIP A-2：tiled matmul + LDS

**今日目標**：寫 tiled matmul，反組譯確認 LDS 指令出現。

- [ ] **搞懂** LDS（shared memory）的角色與 `ds`+`s_barrier` 協作模式
  - [ ] LDS 指令家族：`ds_write_b32/64/128`、`ds_read_*`，由 `lgkmcnt` 追蹤
  - [ ] 為何 tiling 要先把 HBM 資料 staging 進 LDS 再重複使用（省 HBM 流量）
  - [ ] `s_barrier` 的必要性：跨 wave 共享 LDS，寫完要全體同步才能讀
  - ✅ 完成判準：能說出 LDS 在 matmul tiling 裡扮演的角色與 barrier 為何不可省
  - 📚 參考資源：`study_docs/amd-isa-kernel.md`「階段 A-2」；`asm/example03_mfma/` 的 LDS staging
- [ ] **認識** LDS bank conflict（這是現有教材最大缺口，先建立概念）
  - [ ] 概念：LDS 32 banks、每 bank 4 bytes、`bank = (byte_addr/4) % 32`
  - [ ] 同 wave 多 lane 落同 bank 不同址 → N-way conflict 被序列化
  - ✅ 完成判準：能說出何時會 bank conflict、`LDSBankConflict` counter 看哪裡
  - 📚 參考資源：（待擴充：isa/lds-bank-conflicts.md）；`profiling-rocprof.md` 的 `LDSBankConflict`
- [ ] **動手** 寫 tiled matmul（用 shared memory），反組譯確認 LDS 指令出現
  - [ ] 寫出有 shared memory tiling 的 matmul kernel
  - [ ] 反組譯找到 `ds_write_b*`（寫 LDS）與 `ds_read_b*`（讀 LDS）
  - [ ] 反組譯找到 `s_barrier`
  - ✅ 完成判準：能解釋「為什麼 tile 載入後、計算前需要 `s_barrier`」
- [ ] **（AMD 資源，選做）** HIP 100「Fundamentals」的 Matrix Transpose naive→LDS 優化段
  （與 A-2 同主題，是最貼近的官方教材）
- **筆記提示**：記下 LDS 一個 bank 的寬度與 bank conflict 的觸發條件（P3 會用）。
  筆記寫在 `study_docs/notes/0628-tiled-matmul與LDS.md`。
- **快速自測**：
  1. LDS（shared memory）相對 HBM 的延遲與頻寬差在哪個量級？
  2. `ds_read` / `ds_write` 由哪個 counter（vmcnt / lgkmcnt）追蹤？
  3. 什麼存取 pattern 會造成 32-way bank conflict？
  <details><summary>答案</summary>
  1. LDS 延遲約數十 cycle、頻寬遠高於 HBM；HBM 延遲達上千 cycle。
  2. lgkmcnt。
  3. 同 wave 的 lane 以 128-byte（32×4）為間距存取，全部落同一 bank → 被序列化成 32 拍。
  </details>

### 06-29（一）｜精讀 example01：逐行讀懂手寫 AMDGCN reduce

**今日目標**：能逐行讀懂一支完整手寫 kernel 並 build & run 到 PASS。

- [ ] **讀** `asm/example01_reduce_sum/README.md` 全 4 節
  - [ ] Prerequisites / Build：知道怎麼用 CMake 把 `.s` 組成 `.hsaco`
  - [ ] Run / Expected output：知道成功會印 `verification : PASS`
  - ✅ 完成判準：能說出 HIP host 端 `hipModuleLoad` → `hipExtModuleLaunchKernel` 的流程
- [ ] **讀** `.s`（`reduce_sum_f32_gfx942.s`，219 行）逐段
  - [ ] L13–36：kernarg load → exec-mask 邊界保護的 `global_load_dword` → `s_waitcnt vmcnt(0)`
  - [ ] L38–56：第一個 LDS reduction 階段（`ds_write` → `s_barrier` → +128 offset）
  - [ ] L57–172：其餘 7 個 reduction 階段（offset 遞減）+ 最終 `global_store`
  - [ ] L174–219：AMDHSA kernel descriptor / metadata（每欄對應一個實體資源）
  - ✅ 完成判準：能不看檔說出「為何每個 reduction 階段之間都要 `s_barrier`」
- [ ] **跑**：
  ```bash
  cd /src/asm/example01_reduce_sum
  cmake -S . -B build && cmake --build build -j"$(nproc)"
  ./build/hip_launch_reduce_sum            # 應印 verification : PASS
  ```
  - [ ] build 成功
  - [ ] 執行印出 `verification : PASS`
  - ✅ 完成判準：跑出 PASS，且能對應「組語裡哪段對應這次輸出的部分和」
  - 📚 參考資源：`asm/example01_reduce_sum/`（README + `.s`）（待擴充：isa/gfx942-isa-reference.md）
- **筆記提示**：畫一張 LDS tree reduction 圖（256→128→…→1），標每階段的 `s_barrier`。
  筆記寫在 `study_docs/notes/0629-精讀example01.md`。
- **快速自測**：
  1. 為什麼每個 reduction 階段之間都要 `s_barrier`？
  2. 這支 baseline 為什麼慢？（從每個 wave 一次載入多少 bytes 想）
  <details><summary>答案</summary>
  1. 下一階段要讀上一階段寫進 LDS 的部分和，必須等整個 workgroup 寫完才能讀。
  2. 每 wave 只發一條 `global_load_dword`＝256 B/wave，之後 stall 等 HBM（~上千 cycle），頻寬利用率低。
  </details>

### 06-30（二）⭐優化重點日｜example02：profiling 驅動優化完整迴圈

**今日目標**：第一次跑通「profile → 讀 counter → 改 code → 驗證加速」的完整迴圈，並能講出
瓶頸如何從 counter 讀出來。這是你最薄弱、也是 P3 成敗關鍵的主題。

- [ ] **讀** `asm/example02_reduce_sum/README.md` 全 4 節（四個範例裡 **profiling 最佳單篇教材**）
  - [ ] Build and run：跑得起來
  - [ ] Generating profiling data：學會 `profile` → `analyze` 兩階段
  - [ ] How the report led us to dwordx4：學會「從報告讀出瓶頸 → 決定改哪行」的推理鏈
  - [ ] Performance comparison vs example01：看懂 before/after 數字表
  - ✅ 完成判準：能複述「報告哪個面板 → 指向哪個瓶頸 → 改哪條指令」的因果鏈
  - 📚 參考資源：`asm/example02_reduce_sum/README.md`（profiling 最佳單篇教材）
- [ ] **跑** profile 與 analyze：
  ```bash
  cd /src/asm/example02_reduce_sum
  cmake -S . -B build && cmake --build build -j"$(nproc)"
  rocprof-compute profile --name reduce_n128m --path prof/n128m -- \
      ./build/hip_launch_reduce_sum ./build/reduce_sum_f32.hsaco 134217728
  rocprof-compute analyze --path prof/n128m --tui
  ```
  - [ ] build 並跑完 `profile`（首次收集較久）
  - [ ] `analyze --tui` 打得開報告
  - [ ] 面板 2.1「System SoL」：讀 HBM BW% 與 VALU FLOPs%
  - [ ] 面板 7.2「Wavefront Runtime」：讀 Dependency Wait Cycles
  - [ ] 面板 10.1「Instruction Mix」：讀 VMEM 指令數/wave
  - ✅ 完成判準：能從三個面板各讀出一個關鍵數字並說它代表什麼
- [ ] **讀** `.s` L25–56（向量化載入 + ILP register tree），對照 ex01 `.s` L13–36
  - [ ] 找出兩條 `global_load_dwordx4`（每 thread 8 floats）
  - [ ] 看懂 8→1 的 ILP pairwise 加法樹
  - ✅ 完成判準：能解釋「`dword`→`dwordx4` + K=8/thread 為何帶來 1.90× 加速」
- [ ] **讀** `study_docs/hipblaslt/profiling-rocprof.md`「第三步：怎麼讀這些指標」counter 解讀表
  - [ ] memory coalescing / 向量化載入
  - [ ] latency hiding 與 Little's Law
  - [ ] compute-bound vs memory-bound 判讀
  - ✅ 完成判準：能用 counter 數值說出一個 kernel 是 compute- 還是 memory-bound
  - 📚 參考資源：`study_docs/hipblaslt/profiling-rocprof.md`（待擴充：該檔末「bench+rocprof cookbook / roofline 數字」、isa/lds-bank-conflicts.md）
- [ ] **（AMD 資源，選做）** HIP 201「Performance Tuning for HIP Programs」（~1.5h）
- **筆記提示**：抄下 ex01→ex02 的對照數字（HBM 峰值佔比 44.7%→83.7%、1.90×、Dependency Wait
  84.8%→95.4%），並寫一句「為何 L2 延遲反而上升卻更快」（Little's Law）。
  筆記寫在 `study_docs/notes/0630-profiling驅動優化.md`。
- **快速自測**：
  1. HBM 峰值佔比從 44.7% 升到 83.7% 代表 kernel 變成什麼 bound？
  2. 為何 ex02 的 L2-Fabric 延遲（1270→2477 cycle）上升，throughput 反而更高？
  3. 怎麼從 counter 一眼判斷 compute-bound vs memory-bound？
  <details><summary>答案</summary>
  1. 更接近純 memory-bound（已逼近 HBM 頻寬上限）。
  2. Little's Law：in-flight 請求數變多（每 wave 8 floats、2 條 dwordx4），用更多並行度掩蓋延遲，
     單筆延遲上升但總吞吐提高。
  3. VALU/MFMA busy 高→compute-bound；MemUnit busy/stalled 高、HBM BW% 逼近峰值→memory-bound。
  </details>

### 07-01（三）✅ 硬截止驗收｜HIP A-3：MFMA builtin + 自我總驗收

**今日目標**：召喚並反組譯出 MFMA 指令；通過 P0 總驗收。

- [ ] **搞懂** MFMA 是什麼、為何用 builtin 召喚
  - [ ] 知道 MFMA＝矩陣乘累加硬體指令，一條算一整塊 tile（非逐元素）
  - [ ] 知道用 builtin（如 `__builtin_amdgcn_mfma_f32_16x16x16f16`）讓編譯器發 `v_mfma_*`
  - ✅ 完成判準：能說出 MFMA 為何比手寫 FMA 迴圈快（吞吐與 register 重用）
  - 📚 參考資源：`study_docs/amd-isa-kernel.md`「階段 A-3」（待擴充：isa/mfma-deep-dive.md）
- [ ] **動手** 寫 builtin kernel 並反組譯
  - [ ] 寫出呼叫該 builtin 的 kernel 並編譯
  - [ ] 反組譯找到 `v_mfma_*` 指令
  - ✅ 完成判準：在 `.s` 指出那條 MFMA，並說出它一次算的矩陣形狀
- [ ] **總驗收（自我檢核，全部要能做到）**：
  - [ ] 對人講清楚 build-time / runtime 兩階段如何交接
  - [ ] 跑過 `hipblaslt-bench` + rocprof-compute 並能解讀輸出
  - [ ] 自寫 HIP kernel 並反組譯對照預期指令
  - [ ] 逐行讀懂 ex01（手寫 reduce）與 ex02（向量化 + profiling）
  - ✅ 完成判準：四項全部打勾＝通過 P0 硬截止
- **筆記提示**：把上面四點各寫 2–3 句「我能做到」的證據（截圖/指令/數字），當實習週報素材。
  筆記寫在 `study_docs/notes/0701-MFMA-builtin與P0驗收.md`。建議用 `learning-quiz` 做一次 P0 總複習測驗。
- **快速自測**：
  1. MFMA 指令 `v_mfma_f32_16x16x4_f32` 一次算的是什麼形狀的矩陣乘累加？
  2. 若 06-30 還沒跑通 profiling，今天該優先補哪一項、捨哪一項？
  <details><summary>答案</summary>
  1. 一個 wave（64 lane）算 `D[16x16] += A[16x4] * B[4x16]`，累加在每 lane 的 4 個 VGPR。
  2. 優先補 ex02 的 profiling 迴圈（P3 關鍵）；A-3 可壓縮到「找到 `v_mfma_*` 即可」。
  </details>

## P1：AMD ISA 深化 + tensilelite 實跑（07-02 → 07-08）

階段目標：讀懂真實 MFMA GEMM 組語（ex03）、掌握 buffer 邊界除錯（ex04）、實跑一次完整
TensileLite tuning 並在產出的真實 GEMM `.s` 裡認出優化手法。

關鍵檔案：`asm/example03_mfma/*`、`asm/example04_global_mem_oob/*`、
`projects/hipblaslt/tensilelite/Tensile/{KernelWriter.py,SolutionStructs/,Components/,Tests/}`。

### 07-02（四）｜⚙️ Charge day（不上班・team 活動）

公司活動，當天不排 roadmap 任務。原本的 example03「結構 + tiling」內容已平均攤提到
07-03、07-04、07-05（見下）。P1 階段結束日仍為 07-08，不延期。

### 07-03（五）｜example03：結構 + tiling + 主迴圈 + ATT

**今日目標**：看懂 MFMA register layout 與 LDS staging，逐行讀懂主迴圈，並用 ATT trace 看出
實際 stall 在哪。（內容較滿——這是把 07-02 charge day 的 example03 結構併入的一天；`.s` 深讀
若當天消化不完，可順延到 07-04／07-05。）

- [ ] **（原 07-02）讀** `asm/example03_mfma/README.md` 結構三節
  - [ ] 「What the kernel does」：kernel 做的是 32×32 輸出塊的 tiled GEMM
  - [ ] 「Tiling summary」表：256 thread / 4 wave / 4 個 16×16 子 tile 如何組成 32×32
  - [ ] 「Constraints」：這支教學 kernel 的尺寸/型別限制
  - ✅ 完成判準：能畫出 256 thread → 4 wave → 4 子 tile → 32×32 的組成圖
- [ ] **（原 07-02）讀** `.s`（`mfma_gemm_f32_gfx942.s`，259 行）L6–119 結構段
  - [ ] L6–41 檔頭註解：tiling 表、kernarg layout、**MFMA register layout**（lane↔元素）
  - [ ] L43–59：kernarg load、tile 基底座標、stride 常數
  - [ ] L61–119：各 lane 的 global staging 位址、LDS 讀位址、accumulator 清零
  - ✅ 完成判準：能說出「lane l 持有 A/B/D 的哪個元素」
- [ ] **（原 07-02）跑** build & run（ATT 也需要先 build 出 `.hsaco`，故放在跑 ATT 前）：
  ```bash
  cd /src/asm/example03_mfma
  cmake -S . -B build && cmake --build build -j"$(nproc)"
  ./build/hip_launch_mfma_gemm          # 應印 verification : PASS, max_abs_err 0
  ```
  - [ ] build 成功
  - [ ] 執行印出 `verification : PASS`、`max_abs_err 0`
  - ✅ 完成判準：拿到可被 ATT 使用的 `.hsaco`
- [ ] **讀** `.s` L121–167 主迴圈
  - [ ] L121–140：`.Lkloop` 開頭——4 條 global load → `ds_write` → `s_barrier`
  - [ ] L141–156：核心——8 條 `ds_read` + 4 條 `v_mfma_f32_16x16x4_f32`
  - [ ] L165–167：`s_nop 15` pipeline drain
  - ✅ 完成判準：能解釋「為何 MFMA 後要 `s_nop 15` 才能讀 accumulator VGPR」
- [ ] **讀 + 跑** ATT thread trace（RCV GUI 在桌機端，容器內僅收集）
  - [ ] 讀 `asm/example03_mfma/README.md`「Thread trace with RCV」Stage 1–2
  - [ ] 跑 trace：
    ```bash
    rocprofv3 --att --att-target-cu 0 --att-shader-engine-mask 0x1 \
        --kernel-include-regex "mfma_gemm_f32" -d prof/att_mfma -- \
        ./build/hip_launch_mfma_gemm ./build/mfma_gemm_f32.hsaco 512 512 512
    ```
  - [ ] 在輸出辨認開頭 `s_waitcnt lgkmcnt(0)`（等 kernarg load）造成的數千 cycle stall
  - ✅ 完成判準：能在 trace 指出那個 leading stall 並說明成因
  - 📚 參考資源：`asm/example03_mfma/`（待擴充：isa/mfma-deep-dive.md、isa/gfx942-isa-reference.md）
- **筆記提示**：抄下 MFMA register layout（lane l 持有 A/B/D 的哪個元素），P3 改 store 位址會用到；
  記下 ATT 輸出目錄結構（`code.json` = 每指令 hitcount/latency）。筆記寫在 `study_docs/notes/0703-example03-MFMA-GEMM.md`。
- **快速自測**：
  1. 一條 `v_mfma_f32_16x16x4_f32` 的 K 維只有 4，BK=16 要幾條 MFMA 串起來？
  2. `s_nop 15` 解決的是什麼問題？
  3. 為什麼 ATT 範例固定用 512×512×512 並 pin CU 0？
  <details><summary>答案</summary>
  1. 4 條（每條 K=4，串 4 次覆蓋 BK=16）。
  2. MFMA 寫回 accumulator 有長延遲；`s_nop` 填空避免太早讀到未就緒的 VGPR。
  3. 保證 CU 0 一定被排到、trace 資料量可控、可重現。
  </details>

### 07-04（六，彈性）｜example04：buffer 邊界（V# / num_records）

**今日目標**：理解 buffer SRD / `num_records` 範圍檢查與 safe/fault 差異——日後改 kernel
記憶體存取除錯的根基。（彈性日：若 07-03 內容太滿、example03 的 `.s` 結構沒讀完，優先用今天補完
再進 example04。）

- [ ] **（彈性，補 07-03）選做** 補讀 ex03 `.s` L6–119 未消化的部分，直到看懂 tiling 與
  MFMA register layout
- [ ] **讀** `asm/example04_global_mem_oob/README.md` 四節
  - [ ] 「The store loop」：這支 kernel 只用單 lane 反覆 store 的設計
  - [ ] 「The kinds of global-memory OOB」表：5 類越界的差別（丟棄/fault/corruption）
  - [ ] 「Kernel argument layout」：kernarg 怎麼擺
  - [ ] safe / fault 兩節：兩種 `num_records` 設定造成的不同結果
  - ✅ 完成判準：能講出 5 類 OOB 中哪些會 fault、哪些靜默
- [ ] **讀** `.s`（`oob_store_gfx942.s`，161 行）L62–113
  - [ ] SRD（V#）在 `s[4:7]` 的構造（`s_and_b32` 遮罩 + `s_mov_b32` 設 word3）
  - [ ] `.Lloop` 的 `buffer_store_dwordx4 ... offen offset:N nt`
  - [ ] 64-bit base 進位（`s_add_u32` + `s_addc_u32`）與 `num_records` 夾擠遞減（`s_cselect_b32`）
  - ✅ 完成判準：能說出範圍檢查為何比 offset 而非 base，故 base 前進時 `num_records` 要同步遞減
- [ ] **跑** safe 與 fault 兩模式：
  ```bash
  cd /src/asm/example04_global_mem_oob
  cmake -S . -B build && cmake --build build -j"$(nproc)"
  ./build/hip_launch_oob_store ./build/oob_store.hsaco safe    # 無 fault，OOB 被丟棄
  ./build/hip_launch_oob_store ./build/oob_store.hsaco fault   # GPU memory access fault
  ```
  - [ ] safe 模式：無 fault、越界寫入被丟棄
  - [ ] fault 模式：出現 GPU memory access fault（SIGABRT）
  - ✅ 完成判準：能對應「兩次 `num_records` 設定差異 → 為何一個安全一個 fault」
  - 📚 參考資源：`asm/example04_global_mem_oob/`（待擴充：isa/gfx942-isa-reference.md）
- [ ] **（AMD 資源，選做）** GCN talk #3「Memory, IO, and CU Architecture on gfx9」
- **筆記提示**：記下 Raw Buffer 範圍檢查公式：越界 iff `inst_offset + voff >= num_records`
  （比的是 offset 不是 base，所以 base 前進時 `num_records` 要同步遞減）。筆記寫在 `study_docs/notes/0704-example04-buffer邊界.md`。
- **快速自測**：
  1. 為什麼 `flat` / `global_*` 指令沒有 `num_records` 邊界保護，`buffer_*` 有？
  2. safe 模式為何不會 fault？
  <details><summary>答案</summary>
  1. 邊界檢查是 buffer（MUBUF）指令透過 SRD 的 `num_records` 硬體做的；flat/global 走平坦定址，無此欄位。
  2. 越界的 store 其 offset ≥ `num_records`，硬體直接丟棄該 lane 的寫入，不觸發 fault。
  </details>

### 07-05（日，彈性/緩衝）｜補進度 + 鞏固 example03

**今日目標**：把前面落後項補齊；務必鞏固 example03（因 07-02 charge day 把 ex03 壓到 07-03，
這裡是它的緩衝）。

- [ ] 補齊 06-25~07-04 任何未打勾的 item
  - [ ] 掃過前面每天的 checklist，補完未勾的子項
  - ✅ 完成判準：06-25~07-04 所有主 item 都已打勾
- [ ] 鞏固 ex03：能不看檔默畫 example03 完整流程
  - [ ] 默畫：tiling（32×32 組成）→ 主迴圈 `.Lkloop`（load/ds_write/barrier/ds_read/mfma）→ store
  - ✅ 完成判準：不看檔能完整講一遍 example03 的資料流
- [ ] **（AMD 資源，選做）** HIP 102「Part B」的「Example: Reduction」段（回扣 ex01/ex02）
- **筆記提示**：補完原 07-02 要記的 MFMA register layout（lane l 持有 A/B/D 的哪個元素，P3 改
  store 位址會用到）；列出目前還不夠有把握的 1–2 個主題，P2 安排時間補。
  可用 `learning-quiz` 對 P0~P1 最薄弱主題做一次綜合測驗，找出要回補的點。

### 07-06（一）｜實跑一次 TensileLite tuning

**今日目標**：親手跑完一次 tuning，看到 `0_`~`4_` 輸出目錄生成。

- [ ] **讀** `study_docs/hipblaslt/tensilelite-pipeline.md`「如何建置 / 執行以觀察此流程」
  - [ ] 看懂 `invoke rocisa` / `invoke build-client` / `Tensile/bin/Tensile` 各做什麼
  - ✅ 完成判準：能說出跑一次 tuning 需要哪幾個前置步驟
- [ ] **跑** 一次完整 tuning（小 config 練手最合適）：
  ```bash
  cd projects/hipblaslt/tensilelite
  invoke rocisa            # 首次或改過 rocisa 後才需要
  invoke build-client
  Tensile/bin/Tensile Tensile/Tests/common/gsu/f32_gsu.yaml out/
  ls out/                  # 應見 0_Build 1_BenchmarkProblems 2_BenchmarkData 3_LibraryLogic 4_LibraryClient
  ```
  - [ ] `invoke rocisa` 成功
  - [ ] `invoke build-client` 成功
  - [ ] `Tensile/bin/Tensile` 跑完不報錯
  - [ ] `ls out/` 看到 `0_`~`4_` 五個目錄
  - ✅ 完成判準：五個輸出目錄都生成，且能說出每個放什麼
  - 📚 參考資源：`study_docs/hipblaslt/tensilelite-pipeline.md`；`Tensile/Tests/common/gsu/f32_gsu.yaml`（待擴充：hipblaslt/tuning-config-reference.md）
- **筆記提示**：記下五個輸出目錄各放什麼（對照 pipeline 文件的輸出目錄表）。筆記寫在 `study_docs/notes/0706-跑TensileLite-tuning.md`。
- **快速自測**：
  1. `3_LibraryLogic/` 與 `2_BenchmarkData/` 內容差在哪？
  2. 改了 config 一定要重跑整條 pipeline 嗎？
  <details><summary>答案</summary>
  1. `2_BenchmarkData` 是每個 size 所有候選的計時 CSV；`3_LibraryLogic` 是挑完贏家後的選擇邏輯 YAML（出貨用）。
  2. 不一定，視改動而定（可用 `--build-only` / cache 等避免全跑）；詳見 pipeline 文件「何時要重跑」。
  </details>

### 07-07（二）｜在真實 GEMM 組語裡認出優化手法

**今日目標**：用 ex01–04 學的指令當索引，在 TensileLite 產出的真實 kernel 組語裡認出
prefetch / double buffer / MFMA 排程。

- [ ] **讀** `study_docs/amd-isa-kernel.md`「階段 B」三小節
  - [ ] B-1：為何 TensileLite 用 rocisa 產組語、不是 hipcc
  - [ ] B-2：怎麼從 build 產出拿到一支真實 GEMM kernel 的組語
  - [ ] B-3：把階段 A 學的指令對應回 GEMM kernel 的對照表
  - ✅ 完成判準：能說出手寫 kernel 與 codegen 產物在「誰決定排程」上的差別
- [ ] **讀** 昨天產出的 `out/1_BenchmarkProblems/.../*.s`（挑一支），對照 B-3 表辨認
  - [ ] 找出 prefetch global read（下一輪 load 提前出現）
  - [ ] 找出 double buffer（LDS 雙緩衝交替）
  - [ ] 找出 MFMA 主迴圈排程與 `s_waitcnt` 調度
  - ✅ 完成判準：能在真實 `.s` 至少指出 prefetch 與 double buffer 各一處
  - 📚 參考資源：`study_docs/amd-isa-kernel.md`「階段 B」（待擴充：isa/mfma-deep-dive.md、isa/gfx942-isa-reference.md、isa/lds-bank-conflicts.md）
- **筆記提示**：把「手寫 ex03 的 `.Lkloop`」與「真實 GEMM kernel 主迴圈」並排，記下多了哪些
  優化（prefetch / 更深 unroll / 排程交錯）。筆記寫在 `study_docs/notes/0707-真實GEMM組語認優化.md`。
- **快速自測**：
  1. 為什麼 TensileLite 用 rocisa 直接產組語，而不是寫 HIP C++ 給 hipcc 編？
  2. double-buffer prefetch 在組語上長什麼樣（提示：下一輪的 global load 出現在哪）？
  <details><summary>答案</summary>
  1. 為精準控制指令排程 / 暫存器配置 / 延遲掩蓋，這是 hipcc 自動編譯難以保證的。
  2. 本輪 MFMA 還在算時，就先發出下一輪的 `global_load`（載入與計算重疊），用雙緩衝交替 LDS。
  </details>

### 07-08（三）｜定位 codegen 入口 + 三層優化地圖

**今日目標**：在程式碼裡定位 GEMM 優化的三個介入層，為 P2/P3 做準備。

- [ ] **讀** `study_docs/hipblaslt/gemm-optimization.md` 兩節
  - [ ] 「你會調的參數從哪來：Solution 與 Problem」：參數的來源與衍生
  - [ ] 「三個調整層級（由淺到深）」：參數 fork → codegen → rocisa
  - ✅ 完成判準：能說出三層各改什麼、風險高低排序
- [ ] **定位** 三個關鍵入口（開檔掃過，先建立座標感，不必讀懂全部）
  - [ ] `tensilelite/Tensile/KernelWriter.py` 的 `kernelBody()`（約 L5279）
  - [ ] `tensilelite/Tensile/SolutionStructs/Solution.py` 的 `assignDerivedParameters`（約 L1478）
  - [ ] `tensilelite/Tensile/Components/`（`MAC` / `LocalRead` / `SIA` / `GlobalWriteComponents`）
  - ✅ 完成判準：能在每個檔指出「若要改 prefetch / 改 tile / 改 MFMA 發射，該動哪裡」
  - 📚 參考資源：`study_docs/hipblaslt/gemm-optimization.md`；上列三入口路徑（待擴充：hipblaslt/components-codegen-map.md、hipblaslt/tuning-config-reference.md）
- **筆記提示**：用一句話記住三層：第 1 層改 config fork（最低風險）→ 第 2 層改 `kernelBody()`/
  Components codegen → 第 3 層改 rocisa 指令（最深）。筆記寫在 `study_docs/notes/0708-定位codegen三層入口.md`。
- **快速自測**：
  1. 實習 scope 下，優化應該從哪一層開始？為什麼？
  2. tile 大小、`DepthU` 這類參數屬於三層中的哪一層？
  <details><summary>答案</summary>
  1. 第 1 層（config 參數 fork）——風險最低，只要新 solution 進選擇表就達標「被 tensilelite 採用」。
  2. 第 1 層（參數空間）。
  </details>

## P2：tensilelite 內部 + 第一批低風險 commit（07-09 → 07-22）

階段策略：先用「小而真」的 commit 熟悉 PR / CI / review 流程（**降低最終大 PR 的風險**），同時
加深對 solution 參數空間的理解，並建立一套可信的 before/after 量測 harness。

里程碑：累積 2~3 顆 main repo commit + 一套穩定量測流程。

關鍵檔案：`projects/hipblaslt/{AGENTS.md,clients/bench/README.md}`、
`tensilelite/{AGENTS.md,Tensile/SolutionStructs/Solution.py,Tensile/KernelWriter.py,Tensile/Components/}`。

> 先決條件（07-09 開工前完成）：精讀 `projects/hipblaslt/AGENTS.md` 與
> `projects/hipblaslt/tensilelite/AGENTS.md` 的 build / 測試 / PR 規範（分支 `users/<user>/<branch>`、
> base `develop`、SPDX header、PR 六段模板、`invoke build` / `invoke build-client` / `tox -e unit`）。

### 07-09（三）｜讀 Solution / Problem：參數從哪來

**今日目標**：看懂使用者參數如何衍生成 tile 幾何，建立調參的因果感。

- [ ] **讀** `tensilelite/Tensile/SolutionStructs/Solution.py` 的 `assignDerivedParameters`
  （約 L1478）與 `assignProblemIndependentDerivedParameters`（約 L618）
  - 完成後能說出：`MacroTile0 = SubGroup0 * ThreadTile0`、`NumThreads` 怎麼來
- [ ] **讀** `tensilelite/Tensile/SolutionStructs/Problem.py` 的 `ProblemType`（約 L818）
- **筆記提示**：畫一張「使用者參數 → 衍生參數」依賴圖（`MatrixInstruction`/`WorkGroup` → tile）。
- **小測驗**：
  1. `MatrixInstruction` 9 元素格式各代表什麼？macro tile 怎麼從它推出？
  2. `ProblemType` 與 `Problem` 差在哪？
  <details><summary>答案</summary>
  1. `[M,N,K,B, WaveM,WaveN, WaveTileM,WaveTileN, WaveTileK]`；`MacroTile0 = WaveM*WaveTileM*M`。
  2. `ProblemType` 是問題「規格」（op/型別/transpose/bias…）；`Problem` 是一組具體 M,N,K,batch。
  </details>

### 07-10（四）｜讀懂 tuning config 的 fork 區段

**今日目標**：看懂 config YAML 結構，知道每個 fork 參數控制什麼。

- [ ] **讀** `tensilelite/Tensile/Tests/common/gsu/f32_gsu.yaml`（61 行）整份結構：
  `GlobalParameters` / `BenchmarkProblems`（ProblemType + ForkParameters）/ `BenchmarkFinalParameters`
- [ ] **讀** `tensilelite/Tensile/Common/ValidParameters.py` 裡 `DepthU`、`GlobalReadVectorWidth`、
  `WorkGroup` 的定義與註解
  - 完成後能說出每個 fork 參數控制的硬體行為（unroll / coalescing / tile / split-K / tile 排序）
- **筆記提示**：列一張小抄：`DepthU` / `GlobalReadVectorWidthA/B` / `MatrixInstruction` /
  `GlobalSplitU` / `WorkGroupMapping` / `PrefetchGlobalRead` 各管什麼。
- **小測驗**：
  1. `GlobalSplitU` > 1 在輸出端會多出什麼動作？什麼情況（K 大小）受益？
  2. `ForkParameters` 裡每個參數給多個值，產生的是什麼？
  <details><summary>答案</summary>
  1. 把 K 切給多個 workgroup，輸出端要做 atomic-add 或多緩衝 reduction；K 很大時受益。
  2. 各參數值的笛卡兒積——每個組合是一個候選 solution。
  </details>

### 07-11（五）｜動手調參並比較 Gflops

**今日目標**：親手改 fork 重跑，從 `2_BenchmarkData` 看出參數對效能的影響。

- [ ] **寫**：複製 `f32_gsu.yaml`，改 `DepthU` / `GlobalReadVectorWidth` / tile 其一，重跑
  `Tensile/bin/Tensile <你的config> out_tune/`
- [ ] **比較** `out_tune/2_BenchmarkData/*.csv` 的 Gflops 與原始 baseline
- **筆記提示**：表格記下「改了什麼 → Gflops 變化 → 你的解釋」，這是 P3 調參的預演。
- **小測驗**：
  1. `DepthU` 調大通常的取捨是什麼？
  2. 若某參數讓 Gflops 變差，下一步該往哪個方向試？
  <details><summary>答案</summary>
  1. 更多 ILP / 更少迴圈開銷，但暫存器壓力上升、可能降 occupancy。
  2. 回看是 compute- 還是 memory-bound（rocprof），朝放鬆瓶頸資源的方向調。
  </details>

### 07-12 ~ 07-13（六/日，彈性）｜送出第 1 顆 PR

**里程碑：第 1 顆 PR 送出。**

- [ ] 找低風險題材：文件錯字、註解補強、明顯小 bug、缺測試、config 清理
- [ ] 依 `AGENTS.md`：開分支 `users/<user>/<branch>`、加 SPDX header、填 PR 六段模板
- [ ] 跑本地檢查（如 `tox -e unit`），推上去跑 CI
- **筆記提示**：記下 PR / CI 流程踩到的坑（build 時間、lint、模板要求），最終大 PR 會再用。
- **小測驗**：
  1. PR 的 base 分支是什麼？分支命名規則？
  2. 新檔案一定要加什麼？
  <details><summary>答案</summary>
  1. base `develop`；分支 `users/<github-username>/<branch-name>`。
  2. SPDX header（Copyright + `SPDX-License-Identifier: MIT`）。
  </details>

### 07-14 ~ 07-18（一~五）｜深入 codegen + 再找 1~2 顆 commit

**今日目標**：理解 codegen 如何程式化產生你手讀過的那類 MFMA 組語。

- [ ] **讀** `KernelWriter.py` 的 `kernelBody()`（約 L5279）主結構：signature → 資源配置 →
  prologue（`setupNewTile`）→ 主 unroll 迴圈（global read / local write / local read / MAC）→ epilogue/store
- [ ] **讀** `Components/` 至少三個：`MAC`（發 MFMA）、`LocalRead`（LDS→VGPR）、
  `SIA` 或 `GlobalWriteComponents`（排程 / 輸出）
  - 對照 ex03 手寫 `.Lkloop`，理解 Components 怎麼組出同類組語
- [ ] 再找 1~2 顆小 commit 送出
- **筆記提示**：把 ex03 手寫主迴圈的每個區塊，對應到 `kernelBody()` 裡呼叫的 Component。
- **小測驗**：
  1. `kernelBody()` 主迴圈裡，global read / local write / local read / MAC 的先後與重疊關係？
  2. Component 系統怎麼替當前 GPU/kernel 選對的實作？
  <details><summary>答案</summary>
  1. 透過排程交錯：本輪 MAC 進行時 prefetch 下一輪 global read，local write/read 雙緩衝銜接。
  2. `Component.find()` 依 `asmCaps`/`archCaps`/`kernel` 參數做 partial-match 選註冊的實作。
  </details>

### 07-19 ~ 07-22（六~二）｜建立穩定 before/after 量測 harness

**里程碑：累積 2~3 顆 commit + 一套可信的量測 harness。**

- [ ] **建立** 可重複量測流程：
  ```bash
  HIPBLASLT_BENCH_PERF=1 ./build/release/clients/hipblaslt-bench \
      -m <M> -n <N> -k <K> -r bf16_r --algo_method heuristic -i 50 -j 5 --print_kernel_info -v
  ```
  - 固定 GPU / iteration / problem，取中位數；加 `-v` 確認正確性；必要時 rocprof-compute 抓 counter
- [ ] **選定** 一個 target problem shape（對齊真實負載，如常見 LLM GEMM shape），記錄 baseline 數字
- **筆記提示**：把量測協定寫成可貼指令 + 一張 baseline 表（shape / dtype / Gflops 中位數 / 主要 counter），P3 直接沿用。
- **小測驗**：
  1. `HIPBLASLT_BENCH_PERF=1` 會多印哪類欄位？為何對判斷瓶頸有用？
  2. 為什麼要取中位數、固定 cold/iter 次數？
  <details><summary>答案</summary>
  1. efficiency monitor 欄位（num_cu、tiles_per_cu、granularity、efficiency、mem read/write bytes）——
     可看 tile/CU 利用率與記憶體流量，輔助 compute/memory-bound 判讀。
  2. 降低雜訊與暖機/時脈波動影響，讓 before/after 比較可信。
  </details>

## P3：GEMM 優化主線（07-23 → 08-13）

> 本階段是**開放式探索**，故採框架化：給里程碑、決策樹與可重複套用的「迭代日 checklist 模板」，
> 而非寫死每天步驟。每天從模板複製一份 checklist 來用。

階段目標：完成一個**被 tensilelite 採用**的 GEMM 優化並送 PR。由淺到深，能在淺層成功就不強求深層。

關鍵檔案：tuning config（fork 區段）、`KernelWriter.py::kernelBody()`、`Components/`、
`hipblaslt-bench`、rocprof-compute。

### 決策樹（決定今天該待在哪一層）

```
選定 target shape + baseline（已在 P2 建好量測 harness）
        │
        ▼
第 1 層：擴 config fork → 重跑 Tensile → 新 solution 進 3_LibraryLogic 並被選用？
        │
        ├── 是 → ✅ 已達「被 tensilelite 採用」最低標 → 直接進「PR 化」（其餘為加分）
        │
        └── 否 / 加速幅度不滿意
                │
                ▼
        第 2 層：改 kernelBody() / Components（prefetch / 排程 / read-write）
                │
                ├── 成功且 -v 正確 → PR 化
                │
                └── 仍不足且時間允許 → 第 3 層 rocisa 指令（高風險，非必需，謹慎評估）
```

### 里程碑與時間框

- **07-23 ~ 07-25 選題 + baseline**：選定 target shape + dtype（bf16 常見），用 rocprof-compute
  判斷 compute-bound / memory-bound（用 ex02 的判讀法 + P2 的量測 harness）。確立優化假設與 baseline。
- **07-26 ~ 08-01 第 1 層（參數空間，風險最低，先做）**：擴 tuning config 的 fork，讓 LibraryLogic
  自動挑出更快 solution。新 solution 勝出且被選擇表採用即達最低標。
- **08-02 ~ 08-09 第 2 層（codegen，視決策樹結果）**：進 `kernelBody()` / `Components/` 調
  prefetch / 排程 / read-write。每步 before/after 驗證。
- **08-10 ~ 08-13 PR 化**：整理 commit、benchmark 證據（中位數、roofline、counter），依 AGENTS.md
  送 PR。**里程碑：GEMM 優化 PR 送出。**

### 優化迭代日 checklist 模板（每天複製一份）

- [ ] **定 hypothesis**：今天要驗證的一句話假設（例：「`DepthU` 16→32 能提高此 memory-bound shape 的 ILP」）
- [ ] **改** config fork 或 `kernelBody()`/Components（一次只改一個變因）
- [ ] **重 build**：第 1 層 `Tensile/bin/Tensile <config> out/`；第 2 層 `invoke build-client`
- [ ] **量測**：`hipblaslt-bench` 取中位數 + `-v` 正確性（沿用 P2 量測協定）
- [ ] **比 counter**：rocprof-compute 對照 before/after，確認瓶頸是否如預期改變
- [ ] **記錄**：hypothesis / 改動 / 數字 / 結論（成立或否）寫進優化日誌
- **每日進度自我檢核**：
  1. 我的新 solution 有出現在 `3_LibraryLogic` 嗎？怎麼確認它「被選用」而非只是候選？
  2. 這次加速是真的嗎（中位數、固定條件、`-v` 通過）還是雜訊？
  <details><summary>答案</summary>
  1. 看 `3_LibraryLogic` 的選擇邏輯 YAML / 選擇表是否把該 size 映射到新 solution；
     或用 `hipblaslt-bench --algo_method index --solution_index <idx>` 對照它確被 heuristic 選中。
  2. 需同 GPU / 同 iteration / 取中位數且 `-v` 正確，單次跑贏不算數。
  </details>

## P4：收尾 + buffer（08-14 → 08-20）

階段目標：把 P3 產出收斂成已合併/可交付的成果，並寫實習總結。

- [ ] 回應 PR review、修 CI、依 reviewer 意見迭代數字
- [ ] **寫實習總結**：before/after 效能（中位數 + roofline + counter）、學到的 ISA / tooling、
  送出的 commit / PR 清單
- [ ] buffer 吸收任何前期落後
- [ ] （行有餘力，加碼）挑第 2 個 shape 或更深的 codegen 優化，增加 commit 數
- **筆記提示**：實習總結應包含——目標達成度（多顆 commit + 被採用的優化）、量化效能證據、
  遇到的坑與解法、若再多兩週會做什麼。

---

## 風險與 scope 控制（客觀評估）

- **最大風險：P3 codegen 太深做不完。** 緩解：P3 先做第 1 層參數優化——只要新 solution 進到選擇表，
  就**已滿足「被 tensilelite 採用」**，第 2 層 codegen 為加分而非必需。避免一開始就鑽 rocisa 指令層
  （study_docs 第 3 層），那是 scope 過大的陷阱。
- **不要過度投入 HIP C++。** 你的目標是 ISA + tensilelite；HIP 只是反組譯練單字的手段，A-1~A-3 夠用。
- **避免進度盲點：** P0 是硬截止，若 06-30 仍未跑通 profiling，週末（06-27/28 已預留彈性）優先補，
  不要把 ISA 深潛（P1）往前擠壓掉 profiling 基礎。
- **commit 早做。** P2 的低風險 commit 不只是練手，是降低最終大 PR 在 CI/review 卡關的風險。

## 驗證方式（如何確認每階段達標）

- P0：容器內自寫 HIP kernel 反組譯出預期指令；`hipblaslt-bench` + rocprof-compute 跑通 ex02 並能解讀。
- P1：`Tensile/bin/Tensile` 跑出 `1_`~`4_`；能在真實 GEMM `.s` 指出 prefetch/MFMA 排程。
- P2：PR 出現在 main repo 且 CI 綠；`2_BenchmarkData` 能比出 config 改動的效能差。
- P3：`hipblaslt-bench -v` 正確 + 中位數證明加速；`3_LibraryLogic` / 選擇表顯示新 solution 被選用。

## AMD 訓練資源對照表

公司內部資源，**選做補充**（非必修）。每日 checklist 已用「**（AMD 資源，選做）**」標記嵌入相關日期；
此表為總覽。連結指向 repo 根目錄兩份 PDF：
[HIP Training](<../HIP Training at AMD - Learning Center - Confluence.pdf>)、
[GCN Architecture](<../GCN (Graphics Core Next) Architecture Training Resources - Machine Learning Software Engineering - Confluence.pdf>)。

### HIP 課程（Learning Center）

| 課程 | 時長 | 對應階段 | 為何在這裡學 |
|---|---|---|---|
| HIP 100 Fundamentals（含 Matrix Transpose naive→LDS、GCN compute units、LDS） | ~3h | P0（06-28） | LDS / shared memory 與 A-2 tiled matmul 同主題的官方教材 |
| HIP 101 Programming Part A（kernel language、thread/memory hierarchy） | ~2h | P0（06-27） | 喚回 HIP 語法，配合 A-1 反組譯 |
| HIP 102 Programming Part B（Example: Reduction、atomics/warp-ops/sync、streams） | ~2h | P1（07-05） | reduction 主題回扣 ex01/ex02 |
| HIP 200 HIP Tools（ROCm Info / Profiler / Tracer / Debugger） | ~1.5h | P0（06-26） | bench/profile 前先認識工具鏈 |
| HIP 201 Performance Tuning for HIP Programs | ~1.5h | P0（06-30）、P3 | 優化主題，對齊 ex02 profiling 與 P3 主線 |
| HIP 203 HIP/ROCm Libraries A（rocBLAS） | ~1.5h | P2（07-19~22） | hipBLASLt 的近親，理解 BLAS library 設計 |

### GCN（gfx9）架構 talk 系列

| Talk | 主題 | 對應階段 | 為何在這裡學 |
|---|---|---|---|
| #1 | GPU Overview and Scheduling Kernels | P0（06-25） | 建立 GPU 排程的整體心智模型 |
| #2 | Scheduling Kernels | P0~P1 | 補充 wave / workgroup 排程細節 |
| #3 | Memory, IO, and CU Architecture on gfx9 | P1（07-04） | 配合 ex04 buffer / 記憶體階層 |
| #5 | Compiling for gfx9 | P0（06-27） | 配合反組譯，理解 compile→ISA 流程 |
| #6 / #9 | HIP Programming Course（基礎 / 進階） | P0~P1 | HIP 語法與進階用法影片版 |
| #4, #7, #8 | gfx9 Product Portfolio / ML Apps / OpenMP | 選讀 | 背景知識，與本實習主線關聯較低 |

## 每日提醒

每日 **09:15（UTC+8）= 01:15 UTC**（cron `15 1 * * *`）durable 提醒，讀本檔推送「今日目標」+
目前階段（P0~P4）。注意：recurring 排程**七天後自動過期**，過期後需重新設定。
