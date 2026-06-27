# CPU 把 kernel launch 到 GPU 的詳細步驟

路徑說明：本檔在 `study_docs/gpu_knowledge/`。連回頂層用 `../`。以 CUDA / NVIDIA 為主軸，並標註 HIP / ROCm 對應。

- AMD、OpenCL、Vulkan Compute 概念相近，只是 API 名稱與 driver 實作不同。

## 白話總覽

CPU 並不是把一個 C 函式「真的丟過去執行」。CPU 做的是：**準備資料、準備 kernel 入口與參數、
把一張「工作單」放進 GPU 的 command queue / stream**；GPU 看到工作單後，自己把大量 thread
分派到 SM/CU 上執行。

> 最簡短心智模型：CPU 負責安排工作（準備資料/kernel/參數、提交 command），GPU 負責執行工作
> （讀 command、建 grid、分派 block 到 SM、用 warp 執行、寫回結果）。

grid / block / warp / SM 等名詞若不熟，先看 [execution-model.md](execution-model.md)。

## 為何重要

理解「launch 是非同步、CPU 不等 GPU」「`<<<>>>` 不是普通函式呼叫」這些事，是寫對 timing、
正確同步、用 stream 做 overlap（見 HIP 書 Ch6）的前提。也能解釋為何 launch 錯誤要用
`cudaGetLastError()` + `cudaDeviceSynchronize()` 兩段才抓得到。

## 一個最小例子

```cpp
__global__ void vecAdd(float* c, const float* a, const float* b, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}

cudaMalloc(&d_a, bytes); cudaMalloc(&d_b, bytes); cudaMalloc(&d_c, bytes);
cudaMemcpy(d_a, h_a, bytes, cudaMemcpyHostToDevice);
cudaMemcpy(d_b, h_b, bytes, cudaMemcpyHostToDevice);

dim3 block(256);
dim3 grid((n + block.x - 1) / block.x);
vecAdd<<<grid, block>>>(d_c, d_a, d_b, n);     // ← 真正的 kernel launch

cudaMemcpy(h_c, d_c, bytes, cudaMemcpyDeviceToHost);
cudaDeviceSynchronize();
```

`<<<grid, block, sharedMem, stream>>>` 指定 grid 維度、block 維度、動態 shared memory 大小、
stream；底層等價於 `cudaLaunchKernel(func, gridDim, blockDim, args, sharedMem, stream)`。

## 流程：編譯期

launch 發生前，code 要先被編成 GPU 看得懂的東西。

1. **原始碼含 host + device code**：`__global__` 函式是 device code（kernel），`main()` 是 host code。
2. **編譯器分流**：`nvcc`（HIP 用 `hipcc`）把 host code 交給一般 C++ compiler；device code 編成中間/機器碼。
3. **PTX / cubin / fatbin**：
   - PTX = GPU 的中間語言（類似「半成品組語」）。
   - cubin = 特定 NVIDIA 架構可直接執行的 binary（AMD 對應 `.co` / `.hsaco` code object）。
   - fatbinary = 一個包包，可同時放多個架構版本的 PTX / cubin，執行時挑適合當前 GPU 的版本。
4. **JIT（可能發生）**：若可執行檔沒有對應當前 GPU 的 cubin、但有 PTX，driver 可在 runtime 即時編譯。

## 流程：CPU 端（host runtime）

5. **runtime 初始化 + context**：第一次呼叫 CUDA/HIP API 時（常是 lazy init），runtime 選 GPU、
   建立/取得 context、載入 device code module。context 像「GPU 上屬於這個 process 的工作環境」
   （可用記憶體、已載入 kernel、stream/event 狀態等）。
6. **device memory 配置**：`cudaMalloc`（HIP `hipMalloc`）在 GPU VRAM 上配置空間，回傳一個
   **device pointer**。注意 `d_a` 變數本身在 CPU 上，但它存的值是 GPU 位址。
7. **H2D 資料搬移**：`cudaMemcpy(..., cudaMemcpyHostToDevice)`（HIP `hipMemcpy`）把資料從 CPU
   RAM 複製到 GPU，經 PCIe / NVLink / SoC interconnect。`*Async` 版本則排進 stream。
8. **決定 grid / block**：`dim3 block(256); dim3 grid(ceil(n/256));`——logical threads 總數 = grid × block。
9. **kernel launch 語法**：`vecAdd<<<grid, block>>>(...)` 看似函式呼叫，實則「向 GPU 提交工作」。
10. **參數打包**：runtime 收集 kernel 入口、gridDim、blockDim、args、sharedMem、stream。kernel
    參數值（含 device pointer 的「值」、純量 `n` 的值）被複製到一個 GPU launch 能看到的參數區。
11. **檢查 launch configuration**：driver 確認 kernel binary 是否可在當前架構執行、register/shared
    memory 需求、blockDim 是否合法（如單一 block > 1024 threads 通常不合法）。
12. **排進 stream**：未指定 stream 即 default stream。同一 stream 內依 enqueue 順序執行；不同
    stream 若無相依且資源允許，可重疊。
13. **轉成 command buffer + 通知 GPU**：driver 把 launch request 轉成 GPU 可理解的 command 寫進
    command buffer/queue，再用 doorbell / submit 機制「敲」GPU。（此層細節隨 OS / driver / GPU 世代
    不同，非完全公開。）
14. **CPU 通常立刻返回**：kernel launch 是**非同步**的；CPU 不等 GPU，繼續往下跑，除非呼叫
    `cudaDeviceSynchronize` / `cudaStreamSynchronize` / event 等。

## 流程：GPU 端（device 執行）

15. GPU front-end / command processor 從 queue 讀到 kernel launch command。
16. 找到 kernel code 入口、建立 grid。
17. scheduler 把 thread block 分派到可用的 SM/CU（順序不保證、不可控）。
18. 每個 SM/CU 收到一或多個 block，把 block 內 threads 切成 warp/wavefront。
19. warp/wavefront scheduler 挑 ready 的 warp 發射指令；threads 用 `blockIdx`/`threadIdx` 算自己
    負責哪筆資料，讀 global memory → 運算 → 寫回。
20. block 分批完成；全部 block 完成後 kernel 結束，stream 中下一個 operation 才接續。

## 流程：launch 之後（回收）

21. CPU 用 `cudaDeviceSynchronize` / `cudaStreamSynchronize` / event 等 GPU 完成。
22. D2H：把結果從 GPU copy 回 CPU。
23. 檢查錯誤（見下）、釋放 device memory（`cudaFree` / `hipFree`）。

**抓錯兩段式**：

- `cudaGetLastError()` 抓 launch configuration error。
- `cudaDeviceSynchronize()` 抓 kernel 執行期錯誤。因為 launch 非同步，執行期錯誤要等同步點才浮現。

## 餐廳比喻

| CUDA 元件 | 餐廳比喻 |
|-----------|----------|
| CPU | 客人 / 經理 |
| CUDA/HIP runtime | 櫃台 |
| driver | 後場調度員 |
| stream | 點餐隊列 |
| kernel | 一道菜的做法 |
| kernel arguments | 食材與數量 |
| grid | 整批訂單 |
| block | 一桌 / 一組任務 |
| thread | 廚師手上的一個小動作 |
| SM / CU | 廚房工作站 |
| warp / wavefront | 一組同時動作的廚師 |

流程：CPU 說「做 vecAdd，4096 組、每組 256 個小工作」→ runtime 整理成訂單 → driver 放進 GPU
工作隊列 → GPU 把 block 分給各 SM/CU → SM/CU 把 threads 分成 warp 開始算 → CPU 不用等，可先做別的。

## 最容易誤會的幾件事

| 誤會 | 正確說法 |
|------|----------|
| CPU launch 後會等 GPU 跑完 | 通常不會。launch 非同步，要結果須 synchronize / event / blocking copy。 |
| CPU 把每個 thread 一個個送到 GPU | 不會。CPU 只送一個 launch command，GPU 自己拆 grid → block → warp。 |
| GPU 一次同時跑所有 threads | 不一定。logical threads 可能上百萬，硬體分批 resident 執行。 |
| `kernel<<<...>>>()` 是普通 C++ 函式呼叫 | 不是。本質是「向 GPU 提交工作」。 |
| GPU 可直接用 CPU 指標 | 通常不行。需 `cudaMalloc` 取得 device pointer，或用 unified / mapped pinned memory。 |

## 公開語意 vs 實作相關

- **公開且可依賴**：launch 非同步、stream FIFO 順序、block 間無順序保證、參數透過參數區傳遞、
  錯誤檢查兩段式。
- **實作相關（不要寫死依賴）**：command buffer / doorbell 細節、block 實際分派到哪個 SM、JIT
  是否觸發、lazy init 的精確時機——隨 OS / driver / GPU 世代 / MIG / MPS / 虛擬化而異。

## 交叉連結

- 本資料夾入口：[README.md](README.md)
- grid/block/warp/SM 的概念：[execution-model.md](execution-model.md)
- API 名稱速查（`cudaMalloc`↔`hipMalloc` 等）：[cuda-hip-terminology.md](cuda-hip-terminology.md)、[../cuda-to-hip.md](../cuda-to-hip.md)
- stream / overlap 的進階主題：見 HIP 書 Ch6，導讀在 [hip-book-guide.md](hip-book-guide.md)

## 一句話總結

kernel launch 的本質不是「CPU 把程式碼丟過去」，而是「CPU 把已編好、GPU 找得到的 kernel，
用一組 launch 參數排進 GPU 的工作隊列」，然後通常立刻返回；GPU 自己把 grid 拆成 block、
派到 SM/CU、用 warp 執行。
