# CUDA → HIP 快速對照（給有 CUDA 背景的人）

> **狀態：outline，待擴充。** 本文目前只有大綱；內容會隨 roadmap 推進補上。
> 對應 roadmap：**P0 / 06-27**（寫第一支 HIP kernel）。在文件補齊前，先用下方「替代資源」。

## 為何重要

學習者有 CUDA/Triton 背景但大半忘了。HIP 與 CUDA 幾乎一對一，這份對照表的目的是**幾分鐘喚回
記憶**，把已知的 CUDA 概念直接映射到 HIP / AMD 術語，不必從零學。

## 本文件將涵蓋（大綱）

- 執行模型對照：`threadIdx/blockIdx/blockDim/gridDim` ↔ HIP 同名；warp(32) ↔ wave(64) 的差異
- 記憶體對照：`__shared__` ↔ LDS、`__global__/__device__/__host__`、constant memory
- API 對照：`cudaMalloc/cudaMemcpy/cudaLaunchKernel` ↔ `hipMalloc/hipMemcpy/hipLaunchKernelGGL`
- 編譯對照：`nvcc` ↔ `hipcc`；`--offload-arch=gfx942` 對應 `-arch=sm_xx`
- 易踩雷：wave size 64（非 32）對 reduction / ballot / shuffle 的影響
- hipify 工具（`hipify-perl` / `hipify-clang`）一頁式用法

## 目前可先看的替代資源

- `study_docs/gpu_knowledge/cuda-hip-terminology.md`：CUDA↔HIP/ROCm **完整對照大表**（含硬體與 library 生態系），本文未補齊前先看它
- `study_docs/amd-isa-kernel.md`「階段 A-1」：第一支 HIP kernel 與反組譯
- AMD 官方 HIP 課程（延伸閱讀）：[HIP 101 Part A](internal_docs/hip-training-at-amd.md#hip-101-hip-programming-part-a)、
  [HIP 202 HIPify - CUDA to HIP](internal_docs/hip-training-at-amd.md#hip-202-hipify-and-cuda-to-hip)；
  library 類比另見 [internal_docs/hipblaslt-tensilelite-reference.md](internal_docs/hipblaslt-tensilelite-reference.md)
  Module A.1（cuBLASLt ↔ hipBLASLt 對照）
