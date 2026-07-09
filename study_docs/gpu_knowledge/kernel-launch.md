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

## Stream 深入：kernel≠stream、default stream 的特殊性、能開幾條

前面步驟 12 說「未指定 stream 就進 default stream」。這裡把 stream 幾個最容易誤會的點講清楚。

### 先更正一個常見誤解：kernel ≠ stream

- **kernel**：一件工作（一次 launch），是佇列裡的**一個項目**。
- **stream**：一條 **FIFO 佇列 / 時間線**，裡面可以**依序排很多件工作**（kernel、memcpy、event…）。

所以一條 stream 通常不是只有一個 kernel：

```
streamA:  [memcpyH2D] → [kernel1] → [kernel2] → [memcpyD2H]
          （同一條 stream 內：嚴格照順序，前一件做完才做下一件）
```

**關鍵**：並行不是「每個 kernel 自動各跑各的」——

- **同一條 stream 內**：FIFO，一件接一件、**不重疊**（連丟 10 個 kernel 也是依序跑）。
- **不同 stream 之間**：若無相依、資源夠，**才能重疊（並行）**。

### default stream（stream 0）會和所有其他 stream 互相同步

不指定 stream 時，工作會進 **default stream（也叫 stream 0 / NULL stream）**。它有一個特殊規則
——像一個**全裝置的柵欄**：

- **開始前**：default stream 的一個 operation 要開始，得等**其他所有 stream 先前排入的工作都做完**。
- **執行中**：只要 default stream 的工作沒做完，**其他 stream 的工作都不能開始**。

所以 **default stream 的工作不會和任何別條 stream 重疊**。這正是做 overlap 最常見的雷：你開了
多條 stream 想並行，中間卻夾了一個「忘了帶 stream」的 `hipMemcpy` 或 kernel，它進了 default
stream，就把並行打斷、逼成序列化。

```
想並行（streamA / streamB）：       不小心插了一個 default-stream 工作：
  A: [kernelA----]                    A: [kernelA----]
  B:   [copyB--]   ← 重疊，good        default:        [X]   ← 等 A 做完才開始
                                      B:                  [copyB]  ← 又要等 X，overlap 沒了
```

### 怎麼關掉這個柵欄（是 runtime 規則，不是硬體）

要讓 default stream 不再對全裝置強制同步，靠的是**程式模型 / runtime 選項**：

- **per-thread default stream**：`hipStreamPerThread`，或編譯時 `-fgpu-default-stream=per-thread`
  （等同 CUDA 的 `--default-stream per-thread`）——每個 host thread 有自己的 default stream，不再互卡。
- 用 `hipStreamCreateWithFlags(..., hipStreamNonBlocking)` 建立的 stream 也不會和 default stream 互卡。

重點：這是 **HIP/CUDA 軟體模型的規則，跟 GPU 是哪一代（gfx942 / gfx950 / gfx1250）無關**——換架構
不會讓它改變，改變它的是上面這些 runtime 選項。

### 那 hipStreamCreate 的用途是什麼？

既然 kernel≠stream、單一個 kernel 用 default stream 就會跑，你會用 `hipStreamCreate`，是為了
**建立額外的獨立時間線**，達成兩件事：

1. **讓獨立的工作重疊（overlap）**：例如 kernel 放 streamA、`hipMemcpyAsync` 放 streamB，
   算與搬同時進行；或多個彼此無關的小 kernel 各放一條 stream，同時用到不同 CU。
2. **表達順序 / 相依**：有相依的放**同一條 stream**（FIFO 保證順序），無相依的放**不同 stream**
   （宣告可並行）。

```cpp
// (a) 全部在 default stream：序列，無重疊
k1<<<...>>>();                        // 進 default stream
k2<<<...>>>();                        // 等 k1 完才開始

// (b) 用建立的 stream：可重疊
hipStream_t s1, s2;
hipStreamCreate(&s1); hipStreamCreate(&s2);
k1<<<grid, block, 0, s1>>>();         // s1 上算
hipMemcpyAsync(dst, src, n, kind, s2); // s2 上搬，和 k1 有機會同時進行
```

### 能建幾條 stream？建立 vs 真正並行是兩回事

- **能「建立」幾條**：`hipStreamCreate` 建的是**軟體佇列物件**，幾乎沒有固定上限，受**記憶體 /
  runtime 資源**限制，建幾千條通常也行；這個數字跟 GPU 世代無關。
- **能「同時真正並行」幾條**：受**硬體佇列數**限制。HIP stream 會映射到底層 HSA queue，由硬體的
  **ACE（Asynchronous Compute Engines）** 排程；ROCm 用 `GPU_MAX_HW_QUEUES`（常見預設 4、依版本而異）
  控制實際用幾條硬體佇列，超過的 stream 會**多工共用**同一條佇列，不保證真並行。

> 但要注意：**佇列多也不等於真的能同時多跑**——真正的算力天花板是 CU/WGP。為什麼「佇列」和
> 「CU/WGP」是兩種不同層級的限制、彼此怎麼配合，見
> [execution-model.md 的「併發與派工：HW queue（ACE）vs CU/WGP」](execution-model.md#併發與派工hw-queueacevs-cuwgp)。

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
- HW queue（ACE）與 CU/WGP 的併發關係（為何佇列多不等於真並行）：[execution-model.md 併發與派工節](execution-model.md#併發與派工hw-queueacevs-cuwgp)

## 一句話總結

kernel launch 的本質不是「CPU 把程式碼丟過去」，而是「CPU 把已編好、GPU 找得到的 kernel，
用一組 launch 參數排進 GPU 的工作隊列」，然後通常立刻返回；GPU 自己把 grid 拆成 block、
派到 SM/CU、用 warp 執行。
