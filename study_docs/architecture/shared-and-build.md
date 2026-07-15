# 共用依賴與建置骨架（本機其餘有內容的部分）

路徑說明：本檔在 `study_docs/architecture/`。連到原始碼用 `../../shared/...`、`../../projects/...`、`../../cmake/...`。

範圍：**只記錄本機實際存在的內容**；程式碼不在此 checkout 的庫只標明是骨架，不展開其功能。

## `shared/`：跨庫共用依賴

本機 `shared/` 內**有實際內容**的三個依賴：

### [stinkytofu](../../shared/stinkytofu)

LLVM 風格、以 pass 為基礎的 **AMD GPU 組語 kernel IR 最佳化器**（針對 gfx1250），被 hipBLASLt/TensileLite 用來排程與最佳化產生的 GPU code。

> 白話導讀（無 compiler 背景可讀）：[../stinkytofu/README.md](../stinkytofu/README.md)（是什麼/為什麼、IR 與 pass pipeline、重點 passes、在 TensileLite 怎麼被呼叫）。

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

### 驗證容器工具鏈（進容器後先確認）

用 [run.sh](../../run.sh) 起容器（實際 image：`registry-sc-harbor.amd.com/rocm-ci-images/compute-rocm-rel-7.2:93-ubuntu-24.04`）後，先確認建置 / profiling 要用的工具鏈齊全、GPU 架構正確，再開始 build：

| 元件 | 狀態 | 路徑 / 版本 |
| --- | --- | --- |
| `hipcc` | ✅ FOUND | `/usr/local/bin/hipcc` |
| `amdclang++` | ✅ FOUND | `/usr/local/bin/amdclang++` |
| `rocprofv3` | ✅ FOUND | `/opt/rocm-7.2.4/bin/rocprofv3` |
| `rocprof-compute` | ✅ FOUND | `/opt/rocm-7.2.4/bin/rocprof-compute` |
| `gfx942` | ✅ 偵測到 | 8 張 GPU 皆為 `gfx942`（`sramecc+:xnack-`），即 MI300X |

> `.co` 是 per-arch 的：**build 的目標架構必須和機器一致**（這裡是 `gfx942`），否則執行檔在別的架構上啟動 kernel 會直接 segfault，見下方〈常見建置踩坑〉。

## 符號可見性：`TENSILE_API` 巨集與跨 `.so` interposition

讀 `Tensile.hpp` 會看到 `class TENSILE_API SolutionAdapter`，一度以為是「class 後面放兩個名字」，其實 `TENSILE_API` 是**巨集，不是型別名**。

- 定義在 [Macros.hpp](../../projects/hipblaslt/tensilelite/include/Tensile/Macros.hpp#L41)：
  - GCC / Clang → 展開成 `__attribute__((visibility("hidden")))`
  - MSVC / 其他 → 展開成空字串（變回普通 `class SolutionAdapter`）
- 所以在 GCC/Clang 下這行等於：

  ```cpp
  class __attribute__((visibility("hidden"))) SolutionAdapter
  ```

  attribute 寫在 `class` 與類名之間，是修飾「這個型別」的語法位置，不是新名字。
- **作用：把 class 相關符號設為 hidden**（不導出到 `.so` 的動態符號表），包含 vtable、typeinfo、inline 方法本體、隱式 template 實例化。
- **為什麼要這樣做**（見 `Macros.hpp` 上方註解）：
  - `libhipblaslt.so` 與 `libhipsparselt.so` 都內嵌 TensileLite 程式碼。
  - 若兩邊對同一 class（如 `ContractionProblemGemm`）有不同 layout，卻導出相同 mangled name，Linux ELF flat-namespace 的符號插補（interposition）會讓 A 庫呼叫被綁到 B 庫定義 → layout 不相容 → crash（2026/03 實際發生過）。
  - 標成 hidden 後符號不進動態符號表，各 `.so` 只用自己內部定義，避免跨庫誤綁。
- **為什麼標在 class 而非每個函式**：class-level visibility attribute 會透過 header 傳播到每個使用端 TU，並覆蓋使用端自己的 `-fvisibility=` 設定，連 vtable/typeinfo/inline 一起蓋，比逐一標函式更保險。
- 同檔另有 `TENSILE_HIDDEN_BEGIN / TENSILE_HIDDEN_END`（[Macros.hpp](../../projects/hipblaslt/tensilelite/include/Tensile/Macros.hpp#L64)）用 `#pragma GCC visibility push/pop` 包整段宣告，當作沒加 attribute 之新型別的保底。

## 常見建置踩坑（gfx942 troubleshooting）

首次在 gfx942 跑通 `hipblaslt-bench` 時，從「bench 一啟動就 segfault」排到「成功跑出結果」，依序踩了 5 個問題。**根因只有一個：build 的目標架構是 gfx90a，但機器是 gfx942**；重編過程又連環撞到旗標寫法、build 目錄權限、rocRoller 缺原始碼。

### 問題 1｜`hipblaslt-bench` 一啟動就 Segmentation fault

- **表面**：以為是 `--print_kernel_info` 造成的。
- **排查**：`gdb` backtrace 顯示崩潰在 `fill_batch → fill_kernel<<<>>>`（client 用來初始化輸入矩陣的 device kernel）、`hipblaslt_init_device<hip_bfloat16>`，跟印 kernel info 無關；拿掉旗標一樣崩（exit 139）。
- **真因**：GPU 架構不匹配。`roc-obj-ls` 看執行檔只含 `gfx90a` device code，但機器是 **MI300X = gfx942**；要在 gfx942 上啟動 `fill_kernel` 時找不到對應 code object，HIP runtime 直接 segfault（而非回傳錯誤）。`CMakeCache.txt` 也確認 `GPU_TARGETS=gfx90a`。
- **解法**：重編並指定 `--architecture=gfx942`。

### 問題 2｜`./install.sh -dc -a gfx942` 跑去建 Debug + 權限錯誤

- **現象**：`unknown flag '-dc'`，接著 `PermissionError: build/debug`。
- **原因**：
  - `install.sh` 已是呼叫 `invoke build` 的舊 wrapper；`-dc` 連寫被原封丟給 `invoke`，而 invoke 把它拆成 `-d`(=`--debug`) `-c`(=`--clients`) → 跑去建 **Debug**（`build/debug`）。
  - `build/` 整棵樹是最早用 **root** 建的，互動 shell 是非 root 的 `perlee`（uid 1031），沒權限在底下建目錄。
- **解法**：短旗標分開寫、且不要用 root build。正確 = `./install.sh -d -c -a gfx942`（等同 `invoke build --install-deps --clients --architecture=gfx942`，預設 Release → `build/release`）。清掉 root 擁有的 `build/` 改用 `perlee` 重建。

### 問題 3｜CMake configure 失敗：`shared/rocroller` 缺 CMakeLists.txt

- **現象**：`CMake Error at CMakeLists.txt:236 (add_subdirectory): shared/rocroller does not contain a CMakeLists.txt`。（先前的 `HIP_HAS_CLUSTER_LAUNCH ... failed` 是正常的功能偵測 try-compile，不是致命錯誤。）
- **原因**：hipBLASLt 預設 `HIPBLASLT_ENABLE_ROCROLLER=ON`，configure 要把 `shared/rocroller` 當子專案編；但該目錄只有 `cmake/` 子資料夾，**沒有原始碼、也不是 git submodule**（本機僅骨架，見上方〈骨架的共用依賴〉）。
- **解法**：rocRoller 是可選後端（跑 bench 不需要），加 `--skip_rocroller`（帶上 `-DHIPBLASLT_ENABLE_ROCROLLER=OFF`）跳過。

### 問題 4｜最後 `make install` Permission denied

- **現象**：編譯（library + Tensile 176550 kernel + clients）全部成功，只在複製到 `hipblaslt-install/` 時 `Permission denied`。
- **原因**：`hipblaslt-install/` 也是 root 擁有，`perlee` 沒權限寫。
- **解法**：**忽略**。跑 bench 不需要 install，執行檔已在 `build/release/clients/`。真要 install 過就 `sudo rm -rf hipblaslt-install`（或 chown 給 perlee）。

### 問題 5｜驗證

- 重跑 `EXIT=0`，solution index `90105`、`607868` Gflops、`226.1 us`，kernel 名含 `ISA942` → 確認在 gfx942 上跑，segfault 徹底解決（實測數字見 [../hipblaslt/profiling-rocprof.md](../hipblaslt/profiling-rocprof.md) 的〈實測 baseline〉）。

### 一句話總結 & 預防

- **根因**：build target（gfx90a）≠ 機器（gfx942）。最終用 `./install.sh -d -c -a gfx942 --skip_rocroller` 以 `perlee` 身分建成。
- **預防**：`root` 擁有 `build/`、`hipblaslt-install/` 的問題，源於最早那次用 root build；之後固定用 `perlee` build 就不會再遇到。

## 交叉連結

- 全 repo 架構地圖：[README.md](README.md)
- hipBLASLt 資料夾解說：[hipblaslt-layout.md](hipblaslt-layout.md)

## 一句話總結

**`shared/` 有三個真有內容的共用依賴（[stinkytofu](../../shared/stinkytofu) / [origami](../../shared/origami) / [mxdatagenerator](../../shared/mxdatagenerator)）；[cmake/](../../cmake)、[dnn-providers/](../../dnn-providers) 是建置與整合骨架；`projects/` 其餘 22 個庫在本機只是 build 骨架。**
