# GEKO — GEMM Kernel Optimization

> **Source URL:** https://amd.atlassian.net/wiki/spaces/MLSE/pages/1186895430/GEMM+Kernel+Optimization
> **pageId:** `1186895430`
> **Space:** MLSE (Machine Learning Software Engineering)
> **Version:** 9
> **Fetched on:** 2026-07-08 (via Atlassian Confluence MCP, `convert_to_markdown=true`)
>
> GEKO 官方使用文件的完整內容。GEKO 是 hipBLASLt 的 GEMM kernel 優化 Python framework，
> 串接 workload 分析 → TensileLite tuning（Ductile GA / dense search）→ library 整合。
> `--tune` 的 GA backend 預設即 Ductile，詳見 [ductile-tensilelite-tuning.md](./ductile-tensilelite-tuning.md)。

---

GEKO 是一套完整的 Python framework，用於優化 hipBLASLt 中的 GEMM（General Matrix Multiply）kernel。GEKO 自動化了從 workload 分析到最終 optimized library 的整個流程，為 AMD GPU 提供顯著的 GEMM 效能提升。

## Overview

GEKO 透過兩種可替換的 tuning workflow 加上一個獨立的 benchmark 模式，提供 hipBLASLt GEMM kernel 的端到端優化方案：

### Optimization Workflow（GA / 窮舉）

為個別 size 與 datatype 產生最優化的 kernel。三個主要步驟：

1. **Configuration Phase**（`scripts/configure.py`）：分析 hipblaslt logs（實際 workload）→ 產生 tensilelite tuning 用的 config YAML。可選擇「一個 size 一個 config」（最佳效能）或「相似 size 群聚在同一 config」（tuning 更有效率）。
2. **Optimization Phase**（`scripts/optimize.py`）：執行 GEMM kernel optimization → benchmark → filter → 建立 final library。可選 Genetic Algorithm（最佳效能）或依 YAML config 參數做全 kernel 窮舉搜尋（用於實驗）。
3. **Integration Phase**：把 optimized libraries merge 回 hipBLASLt → install。

> CLI 會把步驟 1、2 合併為一個指令。官方建議兩步驟做法（先 review config 再跑 optimization），但也可用 CLI 走較快路徑。

Optimization Workflow：

```text
hipBLASLt Logs → Configure → Optimize → Benchmark → Filter → Merge
   YAML logs     Tensile     Tuning     Performance  Final    hipBLASLt
                 Configs   (Ductile/full) Analysis   Library  Integration
```

### Search Workflow（Dense Benchmarking / Offline Tuning）

在既有 solutions 上做窮舉搜尋：

1. **Search Phase（AKA offline tuning）**（`scripts/search.py` 或 `./bin/geko --search`）：Parse logs → 對所有 solutions 做 dense benchmark → 取出 winners → filter → 建立 final library。

gfx950 範例指令：

```bash
./bin/geko --search --workload-log hipblaslt-log-mask64.yaml --devices=0,1,2,3,4,5,6,7
```

Workflow：

```text
hipBLASLt Logs → Search → Extract → Benchmark → Filter → Merge
   YAML logs     Dense    Winning   Performance  Final    hipBLASLt
                Benchmark  Kernels   Analysis    Library  Integration
```

2. **Integration Phase**：把 optimized libraries merge 回 hipBLASLt → install。

### Benchmark Mode

只在 workload log 上跑 hipblaslt-bench，不做任何 tuning。用於量測 baseline 或整合後驗證結果。

```bash
./bin/geko --bench --workload-log hipblaslt-log-mask64.yaml --devices=0
```

### Workload Input Options

以上三種模式都接受下列其中一種 workload 來源：

| Option | Description |
| --- | --- |
| `--workload-log PATH` | 以 `HIPBLASLT_LOG_MASK=64` 擷取的 hipBLASLt GEMM log YAML，包含真實應用執行的 workload sizes。 |
| `--list PATH` | Generator tuning YAML（範例見 `geko/config_generator/config.yaml`）。支援兩種 size 模式：顯式清單（`SIZE_OPTION=0`）或依 CU 邊界限制內部產生的 M×N grid（`SIZE_OPTION=1`）。 |
| `--inline M N batch K DataType DestDataType ComputeDataType transA transB` | 直接在命令列指定單一 GEMM（例如 `--inline 1024 1024 1 1024 B B S N T`）。 |

## GEKO Package Architecture

`geko` package 依優化流程階段分成專門模組：

```text
geko/
├── bench/                 # Benchmarking 與效能分析
│   ├── bench.py           # 核心 benchmark 執行
│   ├── log.py             # hipBLASLt log 解析
│   └── utils.py           # benchmark 解析工具
├── optim/                 # GA-based tensilelite 配置與執行
│   ├── optim.py           # 優化與結果分析
│   └── utils.py           # 進度追蹤與 device 管理
├── search.py              # Dense search workflow（offline tuning）
├── library/               # Kernel library 管理
│   ├── library.py         # Library / LibraryCollection classes
│   ├── operations.py      # library 載入、merge、建立等
│   └── _bank.py           # solution bank 工具
├── config_generator/      # Tensile 配置產生工具
│   ├── config.yaml        # 範例 config 樣板
│   ├── config_generator.py
│   ├── config_merger.py
│   ├── config_sections_generator.py
│   ├── load_input_config.py
│   ├── mi_designer.py
│   ├── sizes.py
│   ├── cluster_sizes.py
│   ├── fork_param_generator.py
│   ├── output_writer.py
│   ├── shared_utils.py
│   ├── utils.py
│   ├── constants.py
│   └── fork_params/        # 每架構 tuning 參數 profile
│       ├── optimization_param.py
│       ├── post_processor.py
│       ├── param_meta.py
│       └── hw_profiles/
│           ├── gfx942/     # gfx942 優化參數與後處理
│           └── gfx950/     # gfx950 優化參數與後處理
├── concurrency/           # 多 GPU 併發管理
│   ├── runner.py          # 併發 job 執行
│   └── utils.py           # 併發工具
├── cli.py                 # CLI 進入點
├── pipeline.py            # workflow 編排 pipeline
├── schemas.py             # 資料結構（GemmType, GemmConfig 等）
├── constants.py           # datatype 對應與欄位定義
└── utils.py               # 共用工具（如 device 管理）
```

### Workflow Output Structure

**Optimization Workflow Output：**

```text
workdir/
├── run_state.json                 # workflow 狀態追蹤
├── hipblaslt-log-mask64.yaml      # 更新後的 benchmark 檔
├── hipblaslt-log-mask64.out       # hipblaslt-bench 輸出
├── summary.csv                    # GEMM 貢獻度分析
├── gemms.csv                      # 抽取出的 unique GEMMs
├── optimizations/                 # Phase 1: configuration 輸出
│   ├── BBS_TN_0.yaml              # 某 GEMM type 的 Tensile config
│   ├── BBS_TN_0.sh                # 執行 script
│   ├── F8BS_TN_1.yaml
│   ├── ...
│   └── build_*/                   # Phase 2: 優化結果
│       ├── 3_LibraryLogic/        # optimized kernel libraries
│       │   └── *.yaml             # 個別 library 檔
│       ├── *-tensilelite.log      # 詳細 tuning log
│       └── *-optimization.log     # optimization log
├── libs/                          # merge 後的 optimized libraries
│   └── *.yaml
├── tensile/library/*.dat          # 編譯後的 Tensile libraries
├── benchmarks/                    # benchmark 配置
│   ├── *_bench.yaml               # 產生的 benchmark inputs
│   └── *_verify.yaml              # verification inputs
├── results/                       # 效能分析
│   ├── raw_results.csv            # 所有 benchmark 資料
│   └── final_results.csv          # 篩選後結果
└── final_libs/                    # 篩選後 optimized libraries（供整合）
    └── *.yaml
```

**Search Workflow Output：**

```text
workdir/
├── run_state.json
├── hipblaslt-log-mask64.yaml
├── hipblaslt-log-mask64.out
├── summary.csv
├── gemms.csv
├── winners.csv                    # 每個 GEMM 的最佳 kernel
├── search/                        # dense search 結果
│   ├── BBS_TN_M1024_N32...yaml    # 個別 GEMM configs
│   ├── BBS_TN_M1024_N32...out     # benchmark 輸出
│   └── failed_jobs.log            # 失敗 benchmark log
├── libs/                          # 抽取出的 winning kernels
│   └── *.yaml
├── tensile/library/*.dat
├── benchmarks/
│   └── *_bench.yaml
├── results/
│   ├── raw_results.csv
│   └── final_results.csv
└── final_libs/
    └── *.yaml
```

---

## Requirements

### System Dependencies

#### ROCm Installation

需要 ROCm 6.0+。依 [Quick start installation guide](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/install/quick-start.html)。

驗證 ROCm 安裝：

```bash
/opt/rocm/bin/hipconfig --full
```

預期輸出（版本字串會隨安裝而異）：

```text
HIP version: 6.5.50421-9e0f69f3c
HIP_PATH   : /opt/rocm-7.0.0
ROCM_PATH  : /opt/rocm-7.0.0
HIP_PLATFORM : amd
...
```

> **Troubleshooting ROCm**：若遇到 ROCm 問題，可嘗試 [clean removal](https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.1.0/install/install-methods/package-manager/package-manager-ubuntu.html#uninstalling) 後重裝。其他協助見 [Installation Troubleshooting Guide](https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.1.0/reference/install-faq.html)；runtime error 見 [Runtime Error Triage Checklist](https://github.com/ROCm/rocm-libraries/blob/users/davidd-amd/hipblaslt-triage-checklist.md/docs/hipblaslt-runtime-triage-checklist.md)。

#### System Packages

> **Note：** 可先修復壞掉的相依：`sudo apt update && sudo apt --fix-broken install`

```bash
sudo apt update
sudo apt install python3 python3-yaml
sudo apt install clang lldb lld
sudo apt install libomp-dev
sudo apt install libboost-all-dev libboost-program-options-dev libboost-filesystem-dev
sudo apt install libtinfo-dev libzstd-dev libmsgpack-dev libgtest-dev libgmock-dev
```

---

## Installation

### 1. Clone hipBLASLt（Sparse Checkout）

```bash
git clone --no-checkout --filter=blob:none https://github.com/ROCm/rocm-libraries.git
cd rocm-libraries
git sparse-checkout init --cone
git sparse-checkout set projects/hipblaslt shared/origami shared/stinkytofu shared/mxdatagenerator cmake
git checkout develop
```

若已有 hipblaslt，請確認是最新 commit/version。

### 2. Build hipBLASLt

```bash
cd rocm-libraries/projects/hipblaslt
pip install -r requirements.txt
invoke build --install-deps --clients --install-pkg --architecture gfx950 --skip-rocroller
# 將 gfx950 換成你的 GPU 架構；若要用 MX datatype 請移除 --skip-rocroller；
# 移除 --install-pkg 則只做本地 build（不安裝到系統）。
```

> 完整 build 前置需求、支援架構與 `install.sh` / `invoke build` 選項見 hipBLASLt README（`../../README.md`）。

### 3. Install tensilelite dependencies

```bash
cd rocm-libraries/projects/hipblaslt/tensilelite
pip install -r requirements-dev.txt
```

### 4. Install GEKO Framework

GEKO 隨 hipBLASLt checkout 一起提供，位於 `projects/hipblaslt/utilities/geko`（不需另外 clone，上面的 sparse-checkout 已含）。它用 `pyproject.toml` build、`tox.ini` 管測試環境、`tasks.py` 作為 `invoke` runner。

```bash
cd rocm-libraries/projects/hipblaslt/utilities/geko
pip install .   # 安裝 geko console script + runtime deps（來自 requirements.txt）
```

建議用 `pip install .`（非 editable）；想即時改 source 的開發者可用 `pip install -e .`。

> **hipBLASLt path** 會被 in-tree launchers（`./bin/geko`、`scripts/*.py`）自動偵測。要指向別的 build，可在任一進入點傳 `--hipblaslt PATH` 或設 `GEKO_HIPBLASLT_PATH`；安裝後的 `geko` 指令需要其中之一。

設定開發環境（測試 runner、linter、`invoke`）：

```bash
pip install -e .           # runtime deps + geko console script
pip install --group dev    # dev 工具：pytest, invoke, flake8, black, isort
```

常見開發任務透過 `invoke`（`invoke --list` 看全部）：

```bash
invoke install            # editable install（pip install -e .）
invoke test               # 跑測試套件
invoke test --skip-slow   # 快速跑
invoke lint               # flake8 over geko/
invoke format             # black + isort
invoke build              # build sdist + wheel 到 dist/
```

也可不安裝、直接從 GEKO repo root 執行 driver（與安裝版同一 code path，會把 repo root 加入 `PYTHONPATH`）：

```bash
./bin/geko --help
```

必要套件（pinned 版本見 `requirements.txt`）：`pyyaml`、`pandas`、`numpy`、`tqdm`、`joblib`、`pytest`。

### 5. Testing GEKO Framework

從 GEKO root（已裝 dev deps）：

```bash
python3 -m pytest tests/     # 直接 pytest
invoke test                  # 透過 invoke task runner
tox                          # 在隔離的 tox 環境
```

`tox` 與 `invoke test` 會把額外參數直接轉給 pytest，例如 `tox -- --skip-slow --skip-geko-bin` 或 `invoke test --skip-slow`。

整合測試需要一個 hipBLASLt repo（有時還需 tuning config 和/或 workload log）：

```bash
python3 -m pytest tests/ \
  --hipblaslt-path ~/rocm-libraries/projects/hipblaslt \
  --config tests/config_generator/fixtures/minimal_config.yaml \
  --workload tests/test_data/workload.yaml
```

`--hw gfx942`（等）可覆寫 configure / optimize 整合測試使用的架構；預設 `gfx950`。

Test markers / skip flags（在 `tests/conftest.py` 註冊）：

- `@pytest.mark.slow` — 長時間 subprocess / GPU 整合測試，用 `--skip-slow` 跳過。
- `@pytest.mark.geko_bin` — `bin/geko` 的 subprocess smoke test，用 `--skip-geko-bin` 跳過。

```bash
python3 -m pytest tests/ --skip-slow --skip-geko-bin
```

詳見 `tests/README.md`。

---

## CLI Reference

`./bin/geko` 是 tuning 與 benchmarking 的單一進入點。下列 flag 對應 `./bin/geko --help`。

### Mode（恰選一）

| Flag | Description |
| --- | --- |
| `--tune` | GA workflow：先 configure 再 optimize。 |
| `--search` | Dense-search tuning workflow。 |
| `--bench` | 只 benchmark workload 中的 GEMMs（不 tuning）。 |

### Workload source（恰選一）

| Flag | Description |
| --- | --- |
| `--workload-log PATH` | hipBLASLt GEMM log YAML（通常以 `HIPBLASLT_LOG_MASK=64` 擷取）。 |
| `--list PATH` | Generator tuning YAML。見 `geko/config_generator/config.yaml`。 |
| `--inline M N batch K DataType DestDataType ComputeDataType transA transB` | 命令列單一 GEMM，例如 `--inline 1024 1024 1 1024 B B S N T`。`transA`/`transB` 各須為 `N` 或 `T`。 |

### Common options（所有模式）

| Flag | Default | Description |
| --- | --- | --- |
| `-d, --devices LIST` | *required* | 逗號分隔的 GPU device IDs（例如 `0,1,2,3`）。 |
| `--workdir PATH` | 自動產生 `geko_<timestamp>/` | 本次 run 所有 artifact 的輸出目錄。 |
| `--keep_thr FLOAT` | `0.0`（`--search` 為 `0.1`） | 丟棄貢獻低於此比例的 GEMMs。 |
| `-v, --verbose {0,1,2}` | `1` | 0=WARNING, 1=INFO, 2=DEBUG。 |
| `--bench-freq` | off | benchmark 時設 `HIPBLASLT_BENCH_FREQ` 以擷取時脈遙測；預設關閉以省開銷。 |

### `--tune` options

| Flag | Default | Description |
| --- | --- | --- |
| `--arch ARCH` | *none* | 目標 gfx 架構，也可來自 `--list` YAML 內的 `ARCH:`。可選：`gfx950`, `gfx950_128cu`, `gfx942`, `gfx942_80cu`, `gfx942_38cu`, `gfx942_20cu`, `gfx942_228cu`。 |
| `--backend {ductile,tensile}` | `ductile` | configure 步驟使用的 tuning backend，只在 `--tune` 用。 |
| `-n, --n_slots INT` | `4` | optimize 步驟中每個 device 的最大併發 optimization jobs。 |
| `--up_thr FLOAT` | `1.03` | 效能 uplift 門檻（例如 `1.03` 保留 ≥3% uplift 的 kernel）。 |
| `--no_retry` | off | 停用失敗 optimization job 的重試。 |

### `--search` options

| Flag | Default | Description |
| --- | --- | --- |
| `--duration SEC` | `0.04` | 每個 GEMM 的目標 dense-search benchmark 時間。 |

### `--bench` options

| Flag | Default | Description |
| --- | --- | --- |
| `--benchmark-duration SEC` | `0.5` | `hipblaslt-bench` 每次 cold / timed phase 的目標秒數。 |

### Validation rules（parser 強制）

- `--workload-log` 與 `--list` 路徑必須存在。
- `--inline` 需要整數 M, N, batch, K，且 `transA`/`transB` ∈ {`N`, `T`}。
- `--tune` 必須帶 `--arch`。

---

## Usage Guide

| Feature | Best for | Speed |
| --- | --- | --- |
| GA Optimization | 最大效能、自訂 kernel 參數 | 慢（小時級） |
| Dense Search | 快速結果、找出最佳既有 kernel | 較快（分鐘級） |
| Benchmark | baseline 量測、結果驗證 | 快 |

### Capturing a hipBLASLt Workload Log

所有 tuning / benchmark workflow 都需要 workload 輸入。最常見來源是從真實應用擷取的 hipBLASLt log：

```bash
HIPBLASLT_LOG_MASK=64 HIPBLASLT_LOG_FILE=hipblaslt-log-mask64.yaml python my_application.py
```

每筆 log 長這樣：

```text
- {function: matmul, M: 16032, N: 109, K: 16384, lda: 16384, ldb: 16384, ldc: 16032, ldd: 16032, stride_a: 0, stride_b: 0, stride_c: 0, stride_d: 0, alpha: 1.0, beta: 0.0, transA: T, transB: N, batch_count: 1, scaleA: 0, scaleB: 0, scaleAlpha_vector: false, gradient: false, use_e: false, bias_vector: false, bias_source: d, a_type: bf16_r, b_type: bf16_r, c_type: bf16_r, d_type: bf16_r, scale_type: f32_r, bias_type: f32_r, compute_type: c_f32_r, activation_type: none, flush: false, rotating: 512, cold_iters: 0, iters: 0, call_count: 1}
```

以 `--workload-log` 傳給任一模式，例如 `--workload-log hipblaslt-log-mask64.yaml`。

### Specifying GEMMs via a Tuning List（`--list`）

沒有（或不需要）擷取的 log 時，可用小型 generator YAML 描述 workload，經 `--list` 傳入。最少需要 GEMM type、架構與 `[M, N, batch, K]` 清單：

```yaml
TRANSA: 'N'
TRANSB: 'T'
DataType: "B"          # bf16 inputs
DestDataType: "B"      # bf16 outputs
ComputeDataType: "S"   # fp32 accumulate
ARCH: "gfx950"
Sizes:
  - [1024, 1024, 1, 1024]
  - [2048, 2048, 1, 2048]
  - [4096, 4096, 1, 4096]
```

存成如 `my_gemm_list.yaml` 傳給任一模式：

```bash
./bin/geko --bench --list my_gemm_list.yaml --devices=0
```

完整樣板（StreamK、GA、MI filtering、`SIZE_OPTION=1` grid 模式等）在 `geko/config_generator/config.yaml`。支援每個 GEMM type 多 size、每檔多 GEMM problem。

---

### 1. GA-based Optimization

用 Genetic Algorithm（透過 Ductile）或窮舉 Tensile grid search 來 tune 新 kernel 參數。效能提升最大但需數小時。

#### Option A：單一 CLI 指令

```bash
./bin/geko --tune --workload-log hipblaslt-log-mask64.yaml --arch gfx950 --devices=0,1,2,3
```

#### Option B：兩步驟 script 控制（推薦 — 可在 tuning 前 review config）

**Step 1 — Configure**（`scripts/configure.py`）：解析 log、依 type group GEMMs、產生 tensilelite configs。

| Option | Description | Default |
| --- | --- | --- |
| `-d, --device` | baseline benchmark 的 GPU device | 0 |
| `--keep_thr` | 篩選門檻（% 總時間） | 0 |
| `-a, --architecture` | 目標 GPU 架構 | gfx950 |
| `-b, --backend` | tuning backend：`ductile`(GA) 或 `tensile`(grid) | ductile |
| `-w, --workdir` | 工作目錄 | workdir |
| `-v, --verbose` | 0=WARNING, 1=INFO, 2=DEBUG | 1 |
| `--bench-freq` | benchmark 時啟用 `HIPBLASLT_BENCH_FREQ`（僅 `--keep_thr > 0`） | False |

```bash
python scripts/configure.py hipblaslt-log-mask64.yaml \
  -a gfx950 --workdir my_optimization --keep_thr 0.05 --device 0
```

輸出：

```text
my_optimization/
├── run_state.json
├── hipblaslt-log-mask64.yaml / .out   # baseline benchmark
├── summary.csv / gemms.csv            # GEMM 貢獻度分析
└── optimizations/
    ├── BBS_TN_0.yaml                  # 每 GEMM type 一個 Tensile config
    ├── BBS_TN_0.sh
    └── ...
```

Log：

```text
GEKO:INFO [configure:main] Starting configuration phase...
GEKO:INFO [configure:main] Found 2 unique GEMMs after filtering
GEKO:INFO [optim:configure] GemmType(transA='T', transB='N', a_type='bf16_r', ...) with 2 sizes
GEKO:INFO [configure:main] Generated 1 configuration files in 'my_optimization/optimizations'
GEKO:INFO [configure:main] Configuration phase completed successfully!
```

**Step 2 — Optimize**（`scripts/optimize.py`）：跨 GPU 跑 GA tuning、merge、benchmark、filter。

| Option | Description | Default |
| --- | --- | --- |
| `-w, --workdir` | 含 configs 的工作目錄 | workdir |
| `-d, --devices` | 逗號分隔 GPU device IDs | 0,1,2,3,4,5,6,7 |
| `-n, --n_slots` | 每 device 最大併發 optimization jobs | 4 |
| `--up_thr` | 效能 uplift 門檻 | 1.03 (3%) |
| `--err_thr` | 篩選用 error 門檻 | 0.03 |
| `--client_build_dir` | tensilelite client build 目錄 | build_tmp |
| `--no_retry` | 不重試失敗 optimization | False |
| `-v, --verbose` | 0=WARNING, 1=INFO, 2=DEBUG | 1 |
| `--bench-freq` | benchmark 時啟用 `HIPBLASLT_BENCH_FREQ` | False |

```bash
python scripts/optimize.py --workdir my_optimization --devices=0,1,2,3 --up_thr 1.03
```

Log：

```text
Optimization in progress: 100%|████████| 2/2 [04:33<00:00, 136.5s/it, n_completed: 2, n_failed: 0]
GEKO:INFO [optim:analyze] Average GEMM uplift of 3.1002% for a total of 1 GEMMs
GEKO:INFO [optimize:main] Final optimized library available in: 'my_optimization/final_libs'
GEKO:INFO [optimize:main] Optimization workflow completed successfully!
```

#### Step 3 — Integrate

```bash
HIPBLASLT_PATH="/path/to/rocm-libraries/projects/hipblaslt"
LIBRARY_DIR="${HIPBLASLT_PATH}/library/src/amd_detail/rocblaslt/src/Tensile/Logic/asm_full/gfx950/Equality/"
${HIPBLASLT_PATH}/tensilelite/Tensile/bin/TensileMergeLibrary \
  --no_eff --force_merge True \
  "${LIBRARY_DIR}" my_optimization/final_libs "${LIBRARY_DIR}"
cd "${HIPBLASLT_PATH}"
invoke build --install-deps --clients --architecture gfx950 --skip-rocroller
```

`TensileMergeLibrary` 參數：`--no_eff` 略過 efficiency 計算；`--force_merge True` 於衝突時強制 merge；三個位置參數為 original dir、new libs dir、output dir（同 original 即就地更新）。

**Verify：**

```bash
"${HIPBLASLT_PATH}/build/release/clients/staging/hipblaslt-bench" \
  --yaml my_optimization/hipblaslt-log-mask64.yaml --device 0
```

**Install system-wide（optional）：**

```bash
cd "${HIPBLASLT_PATH}/build/release"
sudo make -j 64 install && sudo make package
sudo dpkg -i hipblaslt[-_]*.deb
```

---

### 2. Dense Search（Offline Tuning）

窮舉 benchmark 所有既有 hipBLASLt solutions，每個 GEMM 選出 winner — 不 tune 新 kernel 參數。比 GA optimization 快很多。下面兩個進入點跑同一 `run_search` pipeline，產生相同的 `my_search/` 佈局。

#### Option A：單一 CLI 指令

```bash
./bin/geko --search --workload-log hipblaslt-log-mask64.yaml \
  --devices=0,1,2,3,4,5,6,7 --workdir my_search --keep_thr 0.1 --up_thr 1.03
```

#### Option B：Script 進入點（`scripts/search.py`）

與 Option A 等價，但把 workload log 當位置參數，並用與 `configure.py` / `optimize.py` 共享的 script 預設值。只接受 hipBLASLt workload log（YAML 或同欄位的 CSV）；若要用 `--list` 或 `--inline`，請用 Option A。

| Option | Description | Default |
| --- | --- | --- |
| `-d, --devices` | 逗號分隔 GPU device IDs | 0,1,2,3,4,5,6,7 |
| `--keep_thr` | 篩選門檻（% 總時間） | 0.1 |
| `--up_thr` | 效能 uplift 門檻 | 1.03 (3%) |
| `-w, --workdir` | 工作目錄 | workdir |
| `--duration` | 每 GEMM 目標 benchmark 時間（秒） | 0.04 |
| `-v, --verbose` | 0=WARNING, 1=INFO, 2=DEBUG | 1 |
| `--bench-freq` | benchmark 時啟用 `HIPBLASLT_BENCH_FREQ` | False |

```bash
python scripts/search.py hipblaslt-log-mask64.yaml \
  --devices=0,1,2,3,4,5,6,7 --workdir my_search --keep_thr 0.1 --up_thr 1.03
```

Log：

```text
Search in progress: 100%|████████| 2/2 [10:25<00:00, 20.85s/it, n_completed: 2, n_failed: 0]
GEKO:INFO [optim:analyze] Average GEMM uplift of 10.4697% for a total of 2 GEMMs
GEKO:INFO [search:main] Final remapped library available in: 'my_search/final_libs'
GEKO:INFO [search:main] Search workflow completed successfully!
```

#### Integrate

與 GA Optimization 相同 — 跑 `TensileMergeLibrary` 後用 `my_search/final_libs` 內容重建 hipBLASLt。

---

### 3. Benchmark

在 workload 上跑 hipblaslt-bench，不做任何 tuning。用於量測 baseline 或整合後驗證。

```bash
# 從 workload log
./bin/geko --bench --workload-log hipblaslt-log-mask64.yaml --devices=0
# 從單一 inline GEMM
./bin/geko --bench --inline 1024 1024 1 1024 B B S N T --devices=0
# 從 generator tuning YAML
./bin/geko --bench --list my_gemm_config.yaml --devices=0
```

---

## Module Reference

（以下為各模組關鍵函式與範例，摘自原頁）

### `geko.bench` — Benchmarking Module

處理 benchmark 執行與效能分析。關鍵函式：`bench.run()`、`bench.compare()`、`bench.log.parse()`、`bench.log.update()`、`bench.log.summarize()`、`bench.utils.parse_benchmark_output()`。

### `geko.optim` — Optimization Module

編排多 GPU kernel 優化。關鍵函式：`optim.configure()`（產生 Tensile 配置）、`optim.run()`（執行多 GPU 優化）、`optim.analyze()`（benchmark 並篩選 optimized kernels）。

### `geko.search` — Dense Search Module

實作窮舉 kernel search（offline tuning），支援多 GPU。關鍵函式：`search.configure()`、`search.run()`。特色：多 GPU 負載平衡、tqdm 進度追蹤、cache（跳過已完成 benchmark）、`failed_jobs.log`。

### `geko.library` — Library Management Module

管理 Tensile library 的載入、merge 與操作。關鍵類別：`Library`、`LibraryCollection`。關鍵函式：`load_library()`、`load_collection()`、`merge_solutions()`、`extract_solutions()`（依 solution index 從 DataFrame 抽取）、`create()`（呼叫 TensileCreateLibrary）、`from_dataframe()`、`prune_library()`（在不損效能下裁到最小必要 solutions）。

### `geko.schemas` — Data Structures

型別化資料結構含驗證：`GemmType`（GEMM 操作規格）、`GemmConfig`（GEMM type + 問題 sizes）、`RunState`（workflow 狀態）。建議用 factory constructor（`GemmType.from_hipblaslt(...)` / `GemmType.from_tensile(...)`）以保持 Tensile + hipBLASLt 欄位一致。

### `geko.utils` — Utility Functions

共用工具：`run_silent_command()`、`build_tensilelite_client()`（依 hipBLASLt git hash 快取）、`parse_devices()`。

---

## Common Usage Patterns（摘要）

原頁提供四個完整 Python 範例：

- **Pattern 1**：Full GA-based Optimization Workflow（`bench.log.summarize` → 逐 GEMM type `optim.configure` → `optim.run` → `merge_solutions` → `optim.analyze` → `from_dataframe` 產出 final library）。
- **Pattern 2**：Full Dense Search Workflow（`summarize` → `search.configure` / `search.run` → `extract_solutions` → `analyze` → 建立 final library）。
- **Pattern 3**：Custom Library Manipulation（`load_library` → `add_epilogues` → `create_bench_input` → 依 size 篩選 → `trim` → `dump`）。
- **Pattern 4**：Custom Benchmarking（`parse_benchmark_output_dir` → `library.operations.create` → `bench.run` → `bench.compare`）。

---

## Troubleshooting（重點）

**1. Configuration Failures** — 常見原因：無法 benchmark log 檔、無效 GEMM types、某 GEMM type/size 找不到 solution、沒產生 tensilelite config。解法包含：確認 log 格式與必填欄位（`function` 須為 `matmul`，`M/N/K/batch_count` 為正整數，`transA/transB` 為 `T/N`，各 `*_type` 有效）、檢查 `geko/constants.py` 的 `LOG_FIELDS`、調降 `--keep_thr`（如 `0.01` 或 `0`）以納入更多 GEMM。找不到 solution 的重要 GEMM 請聯繫 GEMM Optimization team。

**2. Optimization Failures** — 查 `workdir/optimizations/failed_jobs.log`。常見原因：rocm-libraries 版本不穩導致 assembly compile error、沒有可用 AMD GPU、產不出有效 kernel。可用 `--no_retry`、指定可用 `--devices`、檢視 `build_*/BBS_TN_0-tensilelite.log`。

**3. Import Errors** — 設 `PYTHONPATH` 或 `pip install .` / `pip install -e .`。

**Debug Mode** — `-v 2` 最高 verbosity；Python 內 `logging.getLogger("GEKO").setLevel(logging.DEBUG)`。

**Performance Tips** — 適當提高 `keep_thr`（GEMM 少→更快）、device 數對齊實際 GPU、啟用 caching（`bench.compare(..., cache=True)`）、library dump 已自動平行化。

---

## Contributing / License

透過 GitHub PR 貢獻：Google-style docstrings、所有 function 加 type hints、描述性變數名、module docstring 附範例、於多 GPU 架構測試。Issue 提交於 [GitHub](https://github.com/ROCm/rocm-libraries/issues)。
