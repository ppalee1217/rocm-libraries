# CUDA ↔ HIP / ROCm 名詞完整對照（軟體 + 硬體）

> 路徑說明：本檔在 `study_docs/gpu_knowledge/`。連回頂層用 `../`。

## 白話總覽

可以分兩個層次看：

- **CUDA / HIP 是「軟體模型」**：你用 grid、block、thread、stream 描述工作。
- **SM / CU / warp / wavefront / ALU / LDS 是「硬體（或接近硬體）的執行模型」**：GPU 實際怎麼把
  工作跑起來。

HIP 刻意設計成與 CUDA 幾乎一對一，所以多數 CUDA 概念可直接映射到 HIP / AMD 術語。

> 本檔是 **CUDA↔HIP 的 API / 名詞對照表**。若要查 GPU 硬體/軟體架構名詞的**定義**（含 AMD-only：MALL / AGPR / XCD / WGP / wait counter…）與一張 A-Z 縮寫速查，見 [gpu-glossary.md](gpu-glossary.md)。

## 為何重要

學習者有 CUDA/Triton 背景但大半忘了；這張大表的用途是把已知的 CUDA 概念在幾分鐘內映射到
HIP / AMD，不必從零學。概念解釋（grid/block/warp 的設計用途）見
[execution-model.md](execution-model.md)；本檔專注「名詞對照」。

## 與 [../cuda-to-hip.md](../cuda-to-hip.md) 的分工

- 本檔 = **完整對照大表**，含工具鏈、library 生態系、硬體名詞。
- [../cuda-to-hip.md](../cuda-to-hip.md) = 給有 CUDA 背景者的 **API 速查 / 快速喚回記憶**（含 hipify、wave 64 易踩雷）。

兩者互為補充。

## 平台與工具鏈

| NVIDIA / CUDA | AMD / HIP / ROCm | 說明 |
|---------------|------------------|------|
| CUDA Toolkit / Platform | ROCm | 整包 GPU 軟體生態系 |
| CUDA C++ | HIP C++ | 寫 `__global__` kernel、`<<<>>>` launch 的那層 |
| CUDA Runtime API | HIP Runtime API | malloc / copy / launch / sync / stream / event |
| CUDA Driver API | ROCr / HSA runtime + AMDGPU driver / KFD | 更底層的 queue / context / 提交 |
| `nvcc` / NVRTC | `hipcc` / AMD Clang / HIPRTC | 編譯器 |
| `#include <cuda_runtime.h>` | `#include <hip/hip_runtime.h>` | runtime header |
| `-arch=sm_xx` | `--offload-arch=gfx942` | 目標架構（本 repo 為 gfx942 / MI300 / CDNA3） |
| Nsight Systems / Compute、CUPTI | ROCm Systems/Compute Profiler、ROCProfiler、ROCTracer（`rocprof`） | profiling |
| `cuda-gdb` | `ROCgdb` / ROCdbgapi | debugger |
| `nvidia-smi` | `rocm-smi` / `amd-smi` / `rocminfo` | 系統監控 / device info |

## Runtime API

| CUDA | HIP | 用途 |
|------|-----|------|
| `cudaMalloc` / `cudaFree` | `hipMalloc` / `hipFree` | device memory 配置 / 釋放 |
| `cudaMemcpy` / `cudaMemcpyAsync` | `hipMemcpy` / `hipMemcpyAsync` | H2D / D2H / D2D 搬移 |
| `cudaLaunchKernel` / `<<<>>>` | `hipLaunchKernelGGL` / `<<<>>>` | kernel launch |
| `cudaStream_t` | `hipStream_t` | command queue（同 stream 內 FIFO） |
| `cudaEvent_t` | `hipEvent_t` | 同步 / 計時 |
| `cudaDeviceSynchronize` / `cudaStreamSynchronize` | `hipDeviceSynchronize` / `hipStreamSynchronize` | CPU 等 GPU |
| `cudaError_t` / `cudaGetLastError` | `hipError_t` / `hipGetLastError` | 錯誤狀態 |
| `cudaSetDevice` / `cudaGetDeviceProperties` | `hipSetDevice` / `hipGetDeviceProperties` | 多 GPU / device 查詢 |

launch 的詳細步驟見 [kernel-launch.md](kernel-launch.md)。

## 執行模型（軟體抽象）

| CUDA | HIP | 備註 |
|------|-----|------|
| kernel | kernel | `__global__` 標記，幾乎相同 |
| grid | grid | 一次 launch 的全部 blocks |
| thread block | thread block / work-group | 一組可合作 threads；放到單一 SM/CU |
| thread | thread / work-item | 最小 logical worker |
| warp（32） | warp / wavefront（CDNA 64、RDNA 32/64） | 跨平台用 `warpSize`，勿硬寫 32 |
| `threadIdx`/`blockIdx`/`blockDim`/`gridDim` | 同名 | 內建 index |
| `__syncthreads()` | `__syncthreads()` | block 內 barrier（ISA 對應 `s_barrier`） |

## 記憶體

| CUDA | HIP / AMD | 備註 |
|------|-----------|------|
| shared memory（`__shared__`） | LDS（Local Data Share） | block scope 的 on-chip 共享記憶體 |
| registers | VGPR（per-lane）/ SGPR（全 wave 共用） | 用太多降低 occupancy；見 [../amd-isa-kernel.md](../amd-isa-kernel.md) |
| global memory | global memory / HBM / VRAM | 所有 threads 可讀寫、latency 高 |
| constant memory | constant memory | 唯讀廣播 |
| L1 / L2 cache | L1 / L2 cache | 階層因架構而異 |
| `__global__`/`__device__`/`__host__` | 同名 | 函式空間限定詞 |

## Library 生態系

| CUDA | ROCm | 領域 |
|------|------|------|
| cuBLAS | rocBLAS（本 repo 有 hipBLASLt） | BLAS / GEMM |
| cuDNN | MIOpen | deep learning primitives |
| cuFFT | rocFFT | FFT |
| cuSPARSE | rocSPARSE | 稀疏矩陣 |
| cuRAND | rocRAND | 隨機數 |
| NCCL | RCCL | 多 GPU collective（AllReduce 等） |
| Thrust / CUB | rocThrust / hipCUB | parallel algorithms（scan/sort/reduce） |

## 硬體

| NVIDIA | AMD | 備註 |
|--------|-----|------|
| SM（Streaming Multiprocessor） | CU（Compute Unit）/ WGP（RDNA） | 執行 block 的硬體工廠 |
| CUDA core / FP32 lane | Stream Processor / SIMD lane / VALU | 一般運算 lane；勿與「同時跑幾個 thread」畫等號 |
| Tensor Core | Matrix Core / MFMA（XDLOPS） | 矩陣乘加；本 repo 算力來源 `v_mfma_*` |
| warp scheduler | wavefront scheduler | 發射 ready warp/wavefront |
| copy / DMA engine | SDMA / DMA engine | 資料搬移（尤其 async copy） |
| GigaThread Engine（front-end） | Command Processor / ACE / HWS | 接收並分派 command |

AMD 沒有「CUDA core」這個名詞（CUDA 是 NVIDIA 平台）；「類 tensor core」是 Matrix Core 但
架構不同，不能一比一比較——詳見 [execution-model.md](execution-model.md) 的 core 命名小節。

## 交叉連結

- 本資料夾入口：[README.md](README.md)
- 概念與設計用途：[execution-model.md](execution-model.md)
- launch 步驟：[kernel-launch.md](kernel-launch.md)
- API 速查 / hipify：[../cuda-to-hip.md](../cuda-to-hip.md)
- 跨文件名詞彙總：[../glossary.md](../glossary.md)
- gfx942 ISA 實作：[../amd-isa-kernel.md](../amd-isa-kernel.md)

## 一句話總結

HIP 與 CUDA 幾乎一對一：

- 軟體名詞（grid/block/thread/stream、`cudaMalloc`↔`hipMalloc`）直接映射。
- 硬體名詞（SM↔CU、warp↔wavefront、Tensor Core↔Matrix Core）概念對應但不可一比一比較。
- warp size 在 AMD 上常是 64。
