# Codebase 架構導覽（從這裡開始）

這份文件組幫你看懂**這個 repo 在本機實際長什麼樣子**，並切分各部分的角色。

路徑說明：本檔在 repo 內的 `study_docs/architecture/`。

- 連到原始碼用 `../../projects/...`、`../../shared/...`（往上兩層回 repo root）。
- 連到既有導讀用 `../hipblaslt/...`、頂層地圖用 `../README.md`。

## 這個 repo 是什麼

`rocm-libraries` 是 AMD ROCm 一系列**數學 / DNN 函式庫**的 superbuild（mono-repo）：把 BLAS、FFT、sparse、solver、隨機數、DNN、primitive 等多個函式庫，以及它們共用的建置設定、共用依賴放在同一個 repo，用上層 CMake 串起來一起建。

## 重要：本機是 sparse checkout

這份 checkout **不是完整的 superbuild**。只有 **`projects/hipblaslt` 有完整原始碼**（約 22000+ 檔）；`projects/` 其餘的庫只是 **build 骨架**（多半只有 `cmake/`、`clients/` 等少量 stub 檔，沒有真正的核心程式碼）。

因此本文件組採「**以本機實際存在什麼為準**」的方式導覽：

- 想讀**真正能讀的程式碼** → 看 hipBLASLt（見 [hipblaslt-layout.md](hipblaslt-layout.md)）。
- 想懂**共用依賴與建置骨架** → 見 [shared-and-build.md](shared-and-build.md)。

> 提醒：若日後擴大 checkout（拉進更多庫的原始碼），下面「骨架」的描述會過時，以當前 checkout 為準。

## 頂層布局

| 路徑 | 是什麼 | 本機狀態 |
|------|--------|----------|
| `projects/` | 各個 ROCm 函式庫（BLAS/FFT/sparse/solver/RNG/DNN/...） | 只有 `hipblaslt` 完整，其餘為骨架 |
| `shared/` | 跨庫共用的依賴 / 工具 | `stinkytofu`、`origami`、`mxdatagenerator` 有內容；`tensile`、`rocroller` 為骨架 |
| [dnn-providers/](../../dnn-providers) | DNN provider 整合層與整合測試 | 有少量 cmake / stub |
| [cmake/](../../cmake) | superbuild 共用 CMake module 與 toolchain | 完整（少量檔） |
| `study_docs/` | 本學習文件組 | 完整 |
| [run.sh](../../run.sh) | 啟動 ROCm CI docker 容器的腳本 | 完整 |

## 完整 vs 骨架（一眼分辨）

- **完整（可深入讀）**：[projects/hipblaslt](../../projects/hipblaslt)。
- **有內容（共用依賴）**：[shared/stinkytofu](../../shared/stinkytofu)、[shared/origami](../../shared/origami)、[shared/mxdatagenerator](../../shared/mxdatagenerator)。
- **骨架（僅 build 用 stub）**：`projects/` 其餘 22 個庫、[shared/tensile](../../shared/tensile)、[shared/rocroller](../../shared/rocroller)。

## 命名慣例：`hip*` vs `roc*`

ROCm 函式庫常成對出現：

- **`roc*`**（如 `rocblas`、`rocfft`）= AMD 平台的**後端實作**。
- **`hip*`**（如 `hipblas`、`hipfft`）= 可攜層 / 包裝層，讓上層程式碼能跨平台呼叫，底層轉到對應的 `roc*`。

> 本機這兩類大多只是骨架；唯一完整的 `hipblaslt` 本身內部又含一個 `rocblaslt` 內部層（見 [hipblaslt-layout.md](hipblaslt-layout.md)）。

## 本文件組

1. [hipblaslt-layout.md](hipblaslt-layout.md) — hipBLASLt 的完整 folder/subfolder 解說（本機唯一完整程式碼）。
2. [shared-and-build.md](shared-and-build.md) — `shared/` 共用依賴、`dnn-providers/`、`cmake/`、以及 `projects/` 骨架清單。

## 交叉連結

- 學習旅程總綱（兩軌）：[../README.md](../README.md)
- hipBLASLt 行為導讀（執行期 / 產生 kernel / 最佳化 / profiling）：[../hipblaslt/README.md](../hipblaslt/README.md)

## 一句話總結

**這是 ROCm 函式庫的 superbuild，但本機是 sparse checkout：真正能讀的是 hipBLASLt，其餘是骨架。**

先看 [hipblaslt-layout.md](hipblaslt-layout.md)。
