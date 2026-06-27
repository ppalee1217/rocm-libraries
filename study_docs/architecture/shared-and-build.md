# 共用依賴與建置骨架（本機其餘有內容的部分）

路徑說明：本檔在 `study_docs/architecture/`。連到原始碼用 `../../shared/...`、`../../projects/...`、`../../cmake/...`。

範圍：**只記錄本機實際存在的內容**；程式碼不在此 checkout 的庫只標明是骨架，不展開其功能。

## `shared/`：跨庫共用依賴

本機 `shared/` 內**有實際內容**的三個依賴：

### [stinkytofu](../../shared/stinkytofu)

LLVM 風格、以 pass 為基礎的 **AMD GPU 組語 kernel IR 最佳化器**（針對 gfx1250），被 hipBLASLt/TensileLite 用來排程與最佳化產生的 GPU code。

| 子資料夾 | 用途 |
|----------|------|
| [include/](../../shared/stinkytofu/include)、[src/](../../shared/stinkytofu/src) | C++ IR 與 pass 實作 |
| [python_module/](../../shared/stinkytofu/python_module) | nanobind Python 綁定 |
| [hardware/](../../shared/stinkytofu/hardware) | 各架構的指令定義（TableGen 風格 `.def`） |
| [tests/](../../shared/stinkytofu/tests)、[tools/](../../shared/stinkytofu/tools)、[examples/](../../shared/stinkytofu/examples)、[docs/](../../shared/stinkytofu/docs) | 測試 / 工具（含 `stinkytofu-check`）/ 範例 / 文件 |

### [origami](../../shared/origami)

GEMM kernel 設定（如 tile 大小）的**解析式、決定性選擇方法**：用 compute/memory latency 估算掃過候選設定，挑出最佳配置以取得開箱即用的 GEMM 效能。

| 子資料夾 | 用途 |
|----------|------|
| [include/](../../shared/origami/include)、[src/](../../shared/origami/src) | C++ 實作 |
| [python/](../../shared/origami/python) | Python API |
| [tests/](../../shared/origami/tests) | 測試 |

### [mxdatagenerator](../../shared/mxdatagenerator)

AMD 的**浮點資料產生器**：支援多種浮點格式（F32、FP16、BF16、OCP MX-FP8/BF8/FP6/BF6/FP4）的資料產生與低/單精度互轉。

| 子資料夾 | 用途 |
|----------|------|
| [lib/](../../shared/mxdatagenerator/lib) | 函式庫實作 |
| [test/](../../shared/mxdatagenerator/test) | 測試 |
| [docker/](../../shared/mxdatagenerator/docker) | 建置環境 |

### 骨架的共用依賴

- [shared/tensile](../../shared/tensile)、[shared/rocroller](../../shared/rocroller) — 本機僅骨架（少量檔）。
  > 注意：hipBLASLt **自帶**一份 in-repo fork 在 [projects/hipblaslt/tensilelite/](../../projects/hipblaslt/tensilelite)（那份才是完整、會用到的，見 [hipblaslt-layout.md](hipblaslt-layout.md)）。

## `dnn-providers/`：DNN provider 整合層

| 子項 | 內容 |
|------|------|
| [cmake/](../../dnn-providers/cmake) | provider 用的 CMake 輔助（版本檢查、ClangTidy、Sanitizers、Tests 等） |
| [hip-kernel-provider/](../../dnn-providers/hip-kernel-provider) | HIP kernel provider（`src/`） |
| [miopen-provider/](../../dnn-providers/miopen-provider) | MIOpen provider（`cmake/` 等） |
| [integration-tests/](../../dnn-providers/integration-tests) | 跨 provider 整合測試（`cmake/`、`gpu_ref/`） |

## `cmake/`：superbuild 共用建置設定

| 子資料夾 | 內容 |
|----------|------|
| [modules/](../../cmake/modules) | 共用 CMake module：`fetch_rocm_cmake.cmake`、`default_amdclang.cmake`、`shared_third_party.cmake`、`add_subdirectory_with_message.cmake`、`ClangTidy.cmake`、`CheckToolVersion.cmake` |
| [toolchains/](../../cmake/toolchains) | 編譯器 toolchain：`linux-amdclang.cmake`、`rocm-clang.cmake` |

## `projects/`：其餘庫（本機僅 build 骨架）

下列庫在本機**只有 build 骨架**（多為 `cmake/`、`clients/` 等 stub，沒有核心程式碼）。此處只列存在狀態，不展開各庫功能（程式碼不在此 checkout）。

| 庫 | 約略檔數 | 骨架內容範例 |
|----|----------|--------------|
| `composablekernel` | 14 | `cmake/` |
| `hipblas` | 4 | `clients/`、`cmake/` |
| `hipblas-common` | 2 | stub |
| `hipcub` | 6 | `cmake/` |
| `hipdnn` | 25 | stub |
| `hipfft` | 6 | `clients/`、`cmake/` |
| `hiprand` | 8 | stub |
| `hipsolver` | 6 | stub |
| `hipsparse` | 6 | stub |
| `hipsparselt` | 7 | stub |
| `hiptensor` | 4 | stub |
| `miopen` | 20 | `cmake/` |
| `rocalution` | 4 | stub |
| `rocblas` | 14 | `clients/`、`cmake/`、`next-cmake/` |
| `rocfft` | 7 | `clients/`、`cmake/` |
| `rocprim` | 6 | `cmake/` |
| `rocrand` | 10 | stub |
| `rocsolver` | 6 | stub |
| `rocsparse` | 70 | `cmake/suitesparse/*.cmake`（相依版本探測） |
| `rocthrust` | 9 | stub |
| `rocwmma` | 1 | stub |
| `rpp` | 6 | stub |

> 要看真正能讀的程式碼，回到 [hipblaslt-layout.md](hipblaslt-layout.md)。

## [run.sh](../../run.sh)

repo 根目錄的便捷腳本：以 `registry-sc-harbor.amd.com/rocm-ci-images/compute-rocm-rel-7.2` 映像啟動一個掛載 `/data1/perlee` 的 docker 容器並進入 shell（開發/建置環境）。

## 交叉連結

- 全 repo 架構地圖：[README.md](README.md)
- hipBLASLt 資料夾解說：[hipblaslt-layout.md](hipblaslt-layout.md)

## 一句話總結

**`shared/` 有三個真有內容的共用依賴（[stinkytofu](../../shared/stinkytofu) / [origami](../../shared/origami) / [mxdatagenerator](../../shared/mxdatagenerator)）；[cmake/](../../cmake)、[dnn-providers/](../../dnn-providers) 是建置與整合骨架；`projects/` 其餘 22 個庫在本機只是 build 骨架。**
