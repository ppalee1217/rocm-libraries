# GPU 執行模型：grid / block / warp / thread / SM / CU

路徑說明：本檔在 `study_docs/gpu_knowledge/`。連回頂層用 `../`（如 `../amd-isa-kernel.md`）。

- 建議先讀本資料夾入口 [README.md](README.md)。

## 白話總覽

寫程式時你看到的是 **grid → block → thread**；GPU 真正執行時會把 block 放到 **SM/CU**
上，再把 block 裡的 threads 切成 **warp/wavefront** 來發射指令。一句話抓住：

> Grid 是整份工作，block 是合作小隊，thread 是小隊成員；SM/CU 是工廠，warp/wavefront
> 是工廠一次發令的一排工人。

最常見的混淆是把「軟體抽象」和「硬體實體」混為一談。本文先給總圖，再逐一拆解。

## 為何重要

讀懂任何 GPU kernel、做任何效能優化（occupancy、coalescing、divergence）之前，都得先有
這套心智模型。本檔是 [amd-isa-kernel.md](../amd-isa-kernel.md)（gfx942 ISA 實作層，講 wave /
SGPR / VGPR / exec mask）的前置概念層；那邊的 `wave = 64 lane` 就是這裡的 wavefront。

## 總圖：軟體抽象 vs 硬體實體

軟體 / 程式視角（你寫 kernel 時看到的）：

```
kernel launch
└── grid                         ← 一次 kernel 的全部工作
    ├── block / thread block      ← 可合作的一群 threads
    │   ├── thread                ← 你寫的「每個元素做什麼」
    │   └── ...
    └── block ...
```

硬體 / 執行視角（GPU 實際怎麼跑）：

```
GPU device
├── SM (NVIDIA) / CU (AMD)        ← 真正執行 block 的「工廠」
│   ├── resident block(s)
│   │   ├── warp / wavefront       ← 一次發令的一排 lanes
│   │   └── ...
│   ├── registers (VGPR/SGPR)
│   ├── shared memory / LDS
│   ├── warp/wavefront scheduler
│   └── ALUs / SIMD lanes / matrix cores ...
└── SM/CU ...
```

對照關鍵：**一個 block 會被放到單一 SM/CU 上執行**（所以 block 內 threads 能共享 shared
memory/LDS、能 barrier 同步）；硬體再把 block 內 threads 切成固定大小的 warp/wavefront。

## Kernel：一次丟給 GPU 的函式

你用 `__global__` 標記、由 host 端 launch 的 GPU function 就是 kernel。

```cpp
__global__ void add(float* A, float* B, float* C, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < N) C[i] = A[i] + B[i];
}

add<<<numBlocks, threadsPerBlock>>>(A, B, C, N);  // 一次 launch = 一個 grid
```

每個 thread 都跑同一段 kernel code，但因 `threadIdx`、`blockIdx` 不同而處理不同資料。
launch 的完整步驟見 [kernel-launch.md](kernel-launch.md)。

## Grid：一次 launch 的全部 blocks

Grid 是這次 kernel launch 的所有 blocks——它是「工作清單」，不是硬體、也不等於整張 GPU。

```cpp
int threadsPerBlock = 256;
int numBlocks = (N + threadsPerBlock - 1) / threadsPerBlock;
add<<<numBlocks, threadsPerBlock>>>(A, B, C, N);
```

- 全域 thread 編號公式（CUDA/HIP 通用、極核心）：`blockIdx.x * blockDim.x + threadIdx.x`。
- 資料量不是 block size 整數倍時，多出的 thread 用 `if (i < N)` 擋掉。
- 1D/2D/3D 皆可：1D 配 array、2D 配 image/matrix、3D 配 volume。

**設計用途**：把大問題拆成很多 block，讓同一份 kernel 在小 GPU（少 SM）與大 GPU（多 SM）
都能跑——scheduler 自動把 block 分派到可用 SM/CU。因此：

- block 之間沒有執行順序保證，**不能假設 block 0 比 block 1 早完成**。
- 不同 block 之間不能用 `__syncthreads()` 同步；要溝通得透過 global memory / atomics / 第二個 kernel。

## Thread Block / Work-group：一群可合作的 threads

Block（HIP/OpenCL 常稱 work-group）是一群可以合作的 threads。`blockDim.x = 256` 表示每個
block 有 256 threads。

**設計用途**——讓這群 threads 能：

- 放在同一個 SM/CU 上；
- 共用 shared memory / LDS（block scope 的 on-chip 快速記憶體）；
- 用 `__syncthreads()`（HIP 同名 / AMD ISA 的 `s_barrier`）做 block 內 barrier 同步；
- 合作完成一小塊工作，例如 matmul 的一個 tile、reduction、stencil。

```cpp
__shared__ float tile[256];
tile[threadIdx.x] = some_value;
__syncthreads();          // 全 block 寫完才繼續，之後可安全互讀
```

**Block 不是 SM/CU**（最常見誤解）：

- block 是軟體工作單位，SM/CU 是硬體。
- 一個 SM/CU 可同時 resident 多個 block（取決於 register、shared memory/LDS、warp slot 上限）。
- 一個 block 通常**不跨** SM/CU（否則無法共享 shared memory/LDS）。

**Block size 取捨**：太小則 scheduler overhead 相對高、難發揮 shared memory 合作；太大則每個
block 吃太多 register / shared memory，使 SM/CU 能同時 resident 的 block 變少、occupancy 下降。
常見起點 128 / 256 / 512（多為 warp/wavefront size 的倍數），最佳值需用 profiler 決定。

## Thread / Work-item：最小的 logical worker

Thread（AMD 低階文件稱 work-item）是程式模型裡最小的邏輯工作者，有自己的 index、register
state、program counter。注意它是**邏輯單位，不是一顆硬體 core**——你可能 launch 上百萬個
thread，但 GPU 不會有上百萬個 core，而是分批排到 SM/CU 執行。

GPU thread 與 CPU thread 也不同：CPU thread 重、數量少、追求單一 latency；GPU thread 輕、
數量極多、靠大量並行 + warp 排程來掩蓋 latency、追求 throughput。

## Warp / Wavefront：硬體實際發射指令的一排 lanes

Warp（NVIDIA）/ Wavefront（AMD ISA 術語；HIP 也常用 warp）是 GPU 實際發射指令時的一組
threads，以 SIMT / lockstep 方式執行同一條指令、各自處理不同資料。

| 平台 | 名詞 | 常見大小 |
|------|------|----------|
| NVIDIA CUDA | warp | 32 threads |
| AMD CDNA（MI 系列，如 gfx942） | wavefront | 64 threads |
| AMD RDNA（消費級 Radeon） | wavefront | 32 或 64 |

**跨平台原則**：不要硬寫「warp = 32」。在 CUDA 上合理，但 HIP / AMD 上應查 `warpSize` 或
device 屬性。本 repo 目標 gfx942（CDNA3）的 wave = 64，見 [amd-isa-kernel.md](../amd-isa-kernel.md)。

**Warp 與 block 的關係**：硬體把 block 切成 warp/wavefront。

- `blockDim.x = 256` 在 NVIDIA → 256 / 32 = **8 warps**；在 CDNA wave64 → 256 / 64 = **4 wavefronts**。
- block size 不是 warp size 倍數時（如 100 threads），最後一個 warp 會有未使用 lanes，浪費算力——
  所以 block size 最好取 warp/wavefront size 的倍數。

### Warp divergence（為何 branch 影響效能）

同一個 warp 內 threads 走不同 branch 時，硬體會分別執行兩條路、對不參與的 lane 做 mask——
等於兩條路都跑一遍，效能下降。優化原則：**盡量讓同一 warp/wavefront 內的 threads 走同一條
branch**。（exec mask 的 ISA 細節見 [amd-isa-kernel.md](../amd-isa-kernel.md)。）

### Memory coalescing（為何 index 排列重要）

最佳情況：相鄰 thread 讀相鄰記憶體（thread 0 讀 `a[0]`、thread 1 讀 `a[1]`…），硬體可把多個
request 合併成少量 transaction。糟糕情況：相鄰 thread 讀相距很遠的位址，造成大量分散
transaction、浪費頻寬。這也是 `blockIdx.x * blockDim.x + threadIdx.x` 這種 indexing 的另一個
用意——讓相鄰 thread 通常碰相鄰資料。

## SM / CU / WGP：真正執行 block 的硬體工廠

- **NVIDIA**：SM（Streaming Multiprocessor）。
- **AMD**：CU（Compute Unit）；RDNA 還有 WGP（Work Group Processor，含兩個 CU）。

SM/CU 不是「一顆 core」，而是內含 warp/wavefront scheduler、register file、shared memory/LDS、
多條 ALU/SIMD lane、matrix core 等的執行單元。kernel 能否跑滿，常取決於每個 block 用掉多少
register / shared memory，進而決定每個 SM/CU 能同時 resident 幾個 block / 幾個 warp——這就是
**occupancy**。

## AMD 有沒有 tensor core / cuda core？

「CUDA Core」「Tensor Core」基本上是 **NVIDIA 的名詞**；AMD 有功能相近的單元，但叫法與架構
不同，**不能一比一對應、也不能只比數量**。

| NVIDIA | AMD 大致對應 | 用途 |
|--------|--------------|------|
| CUDA Core（FP32/INT lane） | Stream Processor / SIMD lane（CU 內的向量 ALU） | 一般 shader、浮點/整數、平行運算 |
| Tensor Core | Matrix Core / MFMA（AI Accelerator） | 矩陣乘加、FP16/BF16/FP8/INT8 等加速 |
| CUDA（平台 + 程式模型） | ROCm / HIP / OpenCL | GPU 運算開發 |

重點：

- AMD **沒有** 「CUDA Core」，因為 CUDA 是 NVIDIA 的平台；AMD 對應的軟體堆疊是 ROCm（支援 HIP、OpenCL、OpenMP）。
- AMD 消費級 Radeon（RDNA）以 Compute Units、Stream Processors、Ray Accelerators、AI Accelerators 描述。
- AMD Instinct / CDNA（如 MI300、gfx942）用 **Matrix Core Technology** 加速矩陣/AI/HPC，角色近似 Tensor Core；本 repo 的算力來源 `v_mfma_*` 指令就屬此類，見 [amd-isa-kernel.md](../amd-isa-kernel.md)。

## 互相 refer 濃縮表

| 名詞 | 它是什麼 | 和誰有關 |
|------|----------|----------|
| Kernel | 你 launch 的 GPU 函式 | 產生一個 grid；launch 過程見 [kernel-launch.md](kernel-launch.md) |
| Grid | 一次 launch 的全部 blocks | scheduler 把 blocks 分派到 SM/CU |
| Block / Work-group | 一組可合作 threads | 放到單一 SM/CU；內部切成 warp/wavefront；用 shared memory/LDS + barrier 合作 |
| Thread / Work-item | 最小 logical worker | 成為 warp/wavefront 裡的一個 lane |
| Warp / Wavefront | 硬體發令的一排 lanes | NV 32 / CDNA 64 / RDNA 32or64；divergence、coalescing 都跟它相關 |
| SM / CU / WGP | 硬體執行工廠 | 容納 block、保存 warp 狀態、含 register / shared memory / ALU / matrix core |

## 交叉連結

- 本資料夾入口：[README.md](README.md)
- launch 的詳細步驟：[kernel-launch.md](kernel-launch.md)
- CUDA↔HIP 名詞完整對照：[cuda-hip-terminology.md](cuda-hip-terminology.md)
- gfx942 ISA 實作（wave / SGPR / VGPR / exec mask / MFMA）：[../amd-isa-kernel.md](../amd-isa-kernel.md)
- 跨文件名詞彙總：[../glossary.md](../glossary.md)

## 一句話總結

Grid 是整份工作，block 是放到單一 SM/CU 的合作小隊，thread 是小隊成員、實際成為
warp/wavefront 裡的一個 lane；AMD 的「類 CUDA core」是 SIMD lane、「類 Tensor core」是
Matrix Core，但都不叫那個名字、也不能一比一比較。
