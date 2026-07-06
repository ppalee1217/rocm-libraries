# 0626｜跑通第一次 bench + 看懂 build/runtime 接點

## 今日目標

完整跑通一次 `hipblaslt-bench` 並看懂輸出欄位；說清楚磁碟上的兩階段接點。（階段：P0）

## 對應 roadmap item

- [x] 搞懂磁碟上的兩階段接點：build 產物（`.dat` 選擇表 / `.co` kernel）如何被 runtime lazy load
  - ✅ 完成判準：能畫出「build 產物 → 磁碟（`.dat`/`.co`）→ runtime lazy load」的接點圖
- [ ] 搞懂 build-time 三階段 pipeline（BenchmarkProblems → LibraryLogic → ClientWriter）各自產出什麼
  - ✅ 完成判準：能說出三階段各自的輸入與輸出、以及 `0_` ~ `4_` 目錄對應哪階段
- [x] 跑既有 bench，把抽象呼叫鏈對應到真實輸出
  - ✅ 完成判準：能對照輸出講出「這次 heuristic 選了哪個 solution、跑多快」

## 我學到什麼（自己寫）

### 搞懂磁碟上的兩階段接點：build 產物（`.dat` 選擇表 / `.co` kernel）如何被 runtime lazy load

- lazy load 的流程:
  ```mermaid
  flowchart TD
      init["TensileHost::initialize() 第一次 matmul 觸發"] --> master["載入選擇表 TensileLibrary_lazy_gfxNNN.dat"]
      master --> map["initLibraryMapping：建 index -> shard 對照"]
      map --> pick["查表選出 solution (見 runtime-flow 關卡 4)"]
      pick --> shard["用到該 solution 才載入它所在 shard"]
      shard --> co["FindCodeObject：用到該 kernel 才載入對應 .co (hipModuleLoad)"]
      co --> launch["launchKernel 執行"]
  ```


  - 初始化與載選擇表：[initialize()](../../projects/hipblaslt/library/src/amd_detail/rocblaslt/src/tensile_host.cpp#L2765)、 [LoadLibraryFilePreload](../../projects/hipblaslt/library/src/amd_detail/rocblaslt/src/tensile_host.cpp#L2915)
    - `initialize()`: 確認執行環境/lib 並透過 lazy load 載入選擇表 (if set `HIPBLASLT_ENABLE_LAZY_LOAD` in CMake)
    - `LoadLibraryFilePreload` 用來指定 problem 與 solution
  - index→shard 對照：[initLibraryMapping](../../projects/hipblaslt/library/src/amd_detail/rocblaslt/src/tensile_host.cpp#L2936)
  - 按需載 `.co`：[FindCodeObject](../../projects/hipblaslt/tensilelite/src/hip/HipSolutionAdapter.cpp#L279)、 [loadCodeObjectFile](../../projects/hipblaslt/tensilelite/src/hip/HipSolutionAdapter.cpp#L100)（內部 `hipModuleLoad`）



### 搞懂 build-time 三階段 pipeline（BenchmarkProblems → LibraryLogic → ClientWriter）各自產出什麼



### 額外發現：`class TENSILE_API SolutionAdapter` 的 `TENSILE_API` 是什麼

> 讀 `Tensile.hpp` 看到 `class TENSILE_API SolutionAdapter`，一度以為是「class 後面放兩個名字」，其實 `TENSILE_API` 是巨集，不是型別名。

- **它是巨集，不是名字**。定義在 [Macros.hpp](../../projects/hipblaslt/tensilelite/include/Tensile/Macros.hpp#L41)：
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



## 卡關與如何解（自己寫）

> 這次 gfx942 首次跑通,從「bench 一啟動就 segfault」排到「成功跑出結果」,依序踩了 5 個問題。
> 根因只有一個:**build 的目標架構是 gfx90a,但機器是 gfx942**;重編過程又連環撞到旗標寫法、build 目錄權限、rocRoller 缺原始碼。



### 問題 1｜`hipblaslt-bench` 一啟動就 Segmentation fault

- **表面**:以為是 `--print_kernel_info` 造成的。
- **排查**:`gdb` backtrace 顯示崩潰在 `fill_batch → fill_kernel<<<>>>`(client 用來初始化輸入矩陣的 device kernel)、`hipblaslt_init_device<hip_bfloat16>`,跟印 kernel info 無關;拿掉旗標一樣崩(exit 139)。
- **真因**:GPU 架構不匹配。`roc-obj-ls` 看執行檔只含 `gfx90a` device code,但機器是 **MI300X = gfx942**;要在 gfx942 上啟動 `fill_kernel` 時找不到對應 code object,HIP runtime 直接 segfault(而非回傳錯誤)。`CMakeCache.txt` 也確認 `GPU_TARGETS=gfx90a`。
- **解法**:重編並指定 `--architecture=gfx942`。



### 問題 2｜`./install.sh -dc -a gfx942` 跑去建 Debug + 權限錯誤

- **現象**:`unknown flag '-dc'`,接著 `PermissionError: build/debug`。
- **原因**:
  - `install.sh` 已是呼叫 `invoke build` 的舊 wrapper;`-dc` 連寫被原封丟給 `invoke`,而 invoke 把它拆成 `-d`(=`--debug`)`-c`(=`--clients`)→ 跑去建 **Debug**(`build/debug`)。
  - `build/` 整棵樹是最早用 **root** 建的,互動 shell 是非 root 的 `perlee`(uid 1031),沒權限在底下建目錄。
- **解法**:短旗標分開寫、且不要用 root build。正確 = `./install.sh -d -c -a gfx942`(等同 `invoke build --install-deps --clients --architecture=gfx942`,預設 Release → `build/release`)。清掉 root 擁有的 `build/` 改用 `perlee` 重建。



### 問題 3｜CMake configure 失敗:`shared/rocroller` 缺 CMakeLists.txt

- **現象**:`CMake Error at CMakeLists.txt:236 (add_subdirectory): shared/rocroller does not contain a CMakeLists.txt`。(先前的 `HIP_HAS_CLUSTER_LAUNCH ... failed` 是正常的功能偵測 try-compile,不是致命錯誤。)
- **原因**:hipBLASLt 預設 `HIPBLASLT_ENABLE_ROCROLLER=ON`,configure 要把 `shared/rocroller` 當子專案編;但該目錄只有 `cmake/` 子資料夾,**沒有原始碼、也不是 git submodule**。
- **解法**:rocRoller 是可選後端(跑 bench 不需要),加 `--skip_rocroller`(帶上 `-DHIPBLASLT_ENABLE_ROCROLLER=OFF`)跳過。



### 問題 4｜最後 `make install` Permission denied

- **現象**:編譯(library + Tensile 176550 kernel + clients)全部成功,只在複製到 `hipblaslt-install/` 時 `Permission denied`。
- **原因**:`hipblaslt-install/` 也是 root 擁有,`perlee` 沒權限寫。
- **解法**:**忽略**。跑 bench 不需要 install,執行檔已在 `build/release/clients/`。真要 install 過就 `sudo rm -rf hipblaslt-install`(或 chown 給 perlee)。



### 問題 5｜驗證

- 重跑 `EXIT=0`,solution index `90105`、`607868` Gflops、`226.1 us`,kernel 名含 `ISA942` → 確認在 gfx942 上跑,segfault 徹底解決。



### 一句話總結 & 預防

- 根因:build target(gfx90a) ≠ 機器(gfx942)。最終用 `./install.sh -d -c -a gfx942 --skip_rocroller` 以 `perlee` 身分建成。
- 預防:`root` 擁有 `build/`、`hipblaslt-install/` 的問題,源於最早那次用 root build;之後固定用 `perlee` build 就不會再遇到。



## bench 實測記錄（記下來，P2 調參會回頭對照）

- 指令：`./build/release/clients/hipblaslt-bench -m 4096 -n 4096 -k 4096 -r bf16_r --compute_type f32_r --print_kernel_info`
  - 環境：MI300X（gfx942），ROCm 7.2.4；自編 hipBLASLt（`--architecture=gfx942 --skip_rocroller`）
- solution name：`Cijk_Ailk_Bljk_BBS_BH_UserArgs_MT256x224x64_MI16x16x1_..._ISA942_...`（MT256x224x64 / MI16x16x1 / GSU1）
- solution index：`90105`
- Gflops：`607868`（≈ 608 TFLOPS，about 47% of bf16 peak）
- GB/s：`414.64`
- 時間：`226.1 us`
- 備註：`Is supported 1 / Total solutions: 1`；換算驗證 2·4096³ ≈ 137.4 GFLOP ÷ 226.1µs ≈ 608 TFLOPS，與輸出一致
- 卡關細節見上面「卡關與如何解」一節。



## code & doc 參考（可請 AI 協助補連結）

- [hipblaslt/README.md](../hipblaslt/README.md)（建置產出 / runtime 載入兩節）
- [hipblaslt/tensilelite-pipeline.md](../hipblaslt/tensilelite-pipeline.md)
- [clients/bench/README.md](../../projects/hipblaslt/clients/bench/README.md)（bench 旗標）



## Questions 整理（自己寫）

