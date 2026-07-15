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

理解「launch 是非同步、CPU 不等 GPU」「`<<<>>>` 不是普通函式呼叫」這些事，是寫對 timing、正確同步、用 stream 做 overlap（見 HIP 書 Ch6）的前提。

也能解釋為何 launch 錯誤要用 `cudaGetLastError()` + `cudaDeviceSynchronize()` 兩段才抓得到。

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

> `dim3` **是什麼？** 
>
> - 上面 `grid`、`block` 的型別是 `dim3`——一個含 `x`/`y`/`z` 三個 `unsigned int` 的**結構體**（不是內建基本型別）。
> - 它用來描述 grid/block 的三維尺寸；未指定的維度預設為 `1`，所以`dim3 block(256)` 其實是 `x=256, y=1, z=1` 的一維配置。
> - **CUDA 與 HIP/ROCm 使用同名同語意的** `dim3`（CUDA 在 `vector_types.h`、HIP 在 `hip/hip_runtime.h`），是 HIP 原始碼相容設計的一環。

### grid / block 的三維（x/y/z）到底在指定什麼？

grid 和 block **本來就都支援到 3 維**，不是只有 2 維。常看到「只有 x、y」甚至「只有 x」，是因為多數資料是一維或二維，用不到的維度就自動當 `1` 省略了。

**第三維（z）不對應任何特殊硬體，它只是「當資料是三維時，用來定位的座標」**。維度純粹是幫你算 index 的邏輯座標系統，讓 kernel 裡能直覺地對應資料形狀：

- **1 維資料**（向量）：只用 x → `dim3 block(256)` = (256,1,1)
- **2 維資料**（影像、矩陣）：用 x、y → `dim3 block(16,16)` = (16,16,1)
- **3 維資料**（體積 volume、3D 網格）：用 x、y、z → `dim3 block(8,8,4)`

```cpp
// 例：處理 256×256×64 的 3D 體積
dim3 block(8, 8, 4);              // 每個 block 8×8×4 = 256 threads
dim3 grid(256/8, 256/8, 64/4);   // = (32, 32, 16) 個 block
int x = blockIdx.x*blockDim.x + threadIdx.x;
int y = blockIdx.y*blockDim.y + threadIdx.y;
int z = blockIdx.z*blockDim.z + threadIdx.z;  // 只有 3 維資料才用得到
```

**常見誤解：「3 維只是方便寫法，compiler 會幫我攤平成 1 維」——只對一半。**

- ✅ 3 維確實只是給人用的邏輯座標，寫起來直覺。
- ⚠️ 但「攤平」不是 compiler 在編譯期做的。`threadIdx.x/y/z` 的值是**執行期由硬體填進特殊暫存器**的（compiler 不知道會有幾個 thread）；compiler 只是把「讀 `threadIdx.x`」翻成「讀某個暫存器」，把你手寫的 `y*W+x` 編成一般算術，**不做維度攤平**。
- ⚠️ 真正的「攤平成一維」是**硬體為了把 threads 切成 warp/wavefront** 而做的，用固定公式 `linear_tid = x + y*blockDim.x + z*blockDim.x*blockDim.y`（x 變化最快），再每 64（AMD wavefront，NVIDIA 32）個連號 thread 綁成一個 warp。這也是為何常建議 `blockDim.x` 取 warp 大小的倍數（影響 coalescing / bank conflict）。

> 一句話：維度是「給人算 index 的邏輯座標」；硬體內部的線性化是「為了組 warp」，兩者目的不同，都跟 compiler 無關。block 三維乘起來（x×y×z）仍受單一 block ≤ 1024 threads 的限制。



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

1. **runtime 初始化 + context**：第一次呼叫 CUDA/HIP API 時（常是 lazy init），runtime 選 GPU、
  建立/取得 context、載入 device code module。context 像「GPU 上屬於這個 process 的工作環境」
   （可用記憶體、已載入 kernel、stream/event 狀態等）。
2. **device memory 配置**：`cudaMalloc`（HIP `hipMalloc`）在 GPU VRAM 上配置空間，回傳一個
  **device pointer**。注意 `d_a` 變數本身在 CPU 上，但它存的值是 GPU 位址。
3. **H2D 資料搬移**：`cudaMemcpy(..., cudaMemcpyHostToDevice)`（HIP `hipMemcpy`）把資料從 CPU
  RAM 複製到 GPU，經 PCIe / NVLink / SoC interconnect。`*Async` 版本則排進 stream。
4. **決定 grid / block**：`dim3 block(256); dim3 grid(ceil(n/256));`——logical threads 總數 = grid × block。
5. **kernel launch 語法**：`vecAdd<<<grid, block>>>(...)` 看似函式呼叫，實則「向 GPU 提交工作」。
6. **參數打包**：runtime 收集 kernel 入口, `gridDim`, `blockDim`, `args`, `sharedMem`, `stream`。
  kernel 參數值（含 device pointer 的「值」、純量 `n` 的值）被複製到一個 GPU launch 能看到的參數區。
7. **檢查 launch configuration**：driver 確認 kernel binary 是否可在當前架構執行、register/shared
  memory 需求、blockDim 是否合法（如單一 block > 1024 threads 通常不合法）。
8. **排進 stream**：**未指定 stream 即 default stream**。同一 stream 內依 enqueue 順序執行；而不同
  stream 若無相依且資源允許的話，可重疊。
9. **轉成 command buffer + 通知 GPU**：driver 把 launch request 轉成 GPU 可理解的 command 寫進
  command buffer/queue，再用 doorbell / submit 機制「敲」GPU。（此層細節隨 OS / driver / GPU 世代
    不同，非完全公開。）
10. **CPU 通常立刻返回**：kernel launch 是**非同步**的；CPU 不等 GPU，繼續往下跑，除非呼叫
  `cudaDeviceSynchronize` / `cudaStreamSynchronize` / event 等。



## 流程：GPU 端（device 執行）

1. GPU front-end / command processor 從 queue 讀到 kernel launch command。
2. 找到 kernel code 入口、建立 grid。
3. scheduler 把 thread block 分派到可用的 SM/CU（順序不保證、不可控）。
4. 每個 SM/CU 收到一或多個 block，把 block 內 threads 切成 warp/wavefront。
5. warp/wavefront scheduler 挑 ready 的 warp 發射指令；threads 用 `blockIdx`/`threadIdx` 算自己
  負責哪筆資料，讀 global memory → 運算 → 寫回。
6. block 分批完成；全部 block 完成後 kernel 結束，stream 中下一個 operation 才接續。

> command processor 如何節流分派、兩層 scheduler 怎麼分工、CP 怎麼「知道」dependency、以及跨
> stream 為何無順序保證，見下方[深入：GPU 端怎麼排程](#深入gpu-端怎麼排程command-processor兩層-schedulerdependency)。



## 流程：launch 之後（回收）

1. CPU 用 `cudaDeviceSynchronize` / `cudaStreamSynchronize` / event 等 GPU 完成。
2. D2H：把結果從 GPU copy 回 CPU。
3. 檢查錯誤（見下）、釋放 device memory（`cudaFree` / `hipFree`）。

**抓錯兩段式**：

- `cudaGetLastError()` 抓 launch configuration error。
- `cudaDeviceSynchronize()` 抓 kernel 執行期錯誤。因為 launch 非同步，執行期錯誤要等同步點才浮現。



## 深入：CPU↔GPU 用什麼機制溝通（MMIO / doorbell / DMA）

前面步驟 9 說 driver「寫 command buffer + 用 doorbell 敲 GPU」。這裡把 CPU 和 GPU 實際的溝通通道講清楚。

**一句話結論：MMIO 只負責「控制與通知」這種小訊號；命令主體和大量資料都靠「共享記憶體 + DMA」。** 不是「主要用 MMIO 搬東西」，而是「MMIO 負責敲門鈴，DMA 負責搬運」。

### 幾個名詞

- **MMIO（Memory-Mapped I/O）**：把 GPU 上的暫存器/控制區，透過 PCIe 的 **BAR（Base Address Register）**映射進 CPU 的實體位址空間。CPU 用一般 load/store 就能讀寫 GPU 暫存器。好處是像存取記憶體一樣簡單；缺點是**每次都要走一趟 PCIe transaction，很慢、頻寬低**，不適合搬大量資料。
- **DMA（Direct Memory Access）**：裝置自己去讀寫記憶體，不透過 CPU 一個字一個字搬。搬大量資料時效率遠高於 MMIO。
- **doorbell（門鈴）**：CPU 往一個特定 MMIO 位址寫一個值，等於「敲」GPU 一下：「佇列裡有新工作了，去看」。

### CPU → GPU 的三條路

| 用途 | 主要機制 | 是不是 MMIO |
|---|---|---|
| 設定 / 初始化 GPU 暫存器 | MMIO（BAR） | 是 |
| 通知 GPU「有新命令」 | doorbell | 是（寫一個位址） |
| 傳 kernel launch / 繪圖命令 | command buffer + DMA | 否；MMIO 只敲門鈴 |
| 搬大量資料（memcpy） | DMA engine over PCIe/NVLink | 否 |

重點是**「命令內容」和「資料」都不走 MMIO**：

1. driver 把命令寫進記憶體裡的 **ring buffer / command buffer**（CPU、GPU 都看得到）。
2. CPU 只用 MMIO **敲一下 doorbell**（更新 write pointer）。
3. GPU 的 command processor 用 **DMA 自己把命令讀進來**執行。

`cudaMemcpy` / `hipMemcpy` 搬的那些陣列，是靠 **DMA engine（copy engine）**在 RAM↔VRAM 之間搬，完全不是 MMIO（拿 MMIO 搬 GB 級資料不可行）。

### GPU → CPU 方向怎麼通知？

GPU 做完事要通知 CPU，通常**不是** MMIO，而是：

- **中斷（interrupt / MSI-X）**：GPU 完成後發中斷給 CPU。
- **寫回記憶體 + CPU 檢查**：GPU 把「完成旗標 / fence value」DMA 寫進一塊 CPU 看得到的記憶體，CPU 檢查那個值即可。這就是很多 event / fence 同步機制的底層。

### 比喻

CPU 是主廚、GPU 是外場：**doorbell** 是叫人鈴（小訊號，很快）；**command buffer** 是「大家都拿得到的架子」，主廚把整疊訂單放上去、按鈴後外場自己去拿（DMA 去讀）；**DMA 搬資料**是用推車一次運一大批，而不是主廚一根根遞。若每件事都用 MMIO（親手一個字念給外場），會慢到不行——所以 MMIO 只留給控制與通知。

### 補充：APU / 統一記憶體

在 **MI300A 這類 APU（CPU+GPU 同封裝、共享記憶體）**或 unified memory 架構下，CPU 和 GPU 共用同一塊實體記憶體、經 Infinity Fabric 一致性連接，就更少依賴「PCIe 上的顯式 DMA 搬運」——資料本來就在同一個池子裡。但 **doorbell / 命令佇列的控制模型仍在**，只是底層 interconnect 換了。



## 深入：GPU 端怎麼排程（command processor、兩層 scheduler、dependency）

前面「流程：GPU 端」列了步驟，這裡把幾個容易誤會的機制講清楚：command processor 怎麼發工作、它怎麼知道 dependency、以及跨 stream 的順序保證。

### 先分清楚「兩個不同層級」

讀 queue 和「把 block 塞進 CU」是**分離**的兩件事，受不同東西節流：

1. **讀 queue / 解析 packet**：由 **command processor（CP）**做；compute 專用的是 **ACE（Asynchronous Compute Engine）**。
2. **把 workgroup（block）塞進 CU**：由下游的 **workgroup dispatcher**（AMD 的 SPI, Shader Processor Input；NVIDIA 概念上的 GigaThread engine）做。

### CP 是「一直讀」還是「等資源」？

CP **不是**無腦一直讀，也**不是**等整個 kernel 跑完才讀下一個，而是：

- **同一條 queue 內 in-order**：照 packet 順序處理；遇到 barrier / dependency packet 就**停下來等**條件滿足才往下讀（這就是 stream FIFO 語意的硬體來源）。
- 一個 dispatch packet 被接受後，CP 把它交給下游 dispatcher，自己就能繼續看後面的 packet（除非被 barrier 擋住）。

**真正「等硬體資源夠才發」的是 workgroup dispatcher**，不是 CP：

- 每個 CU 能同時 resident 幾個 block，取決於這個 kernel 每個 block 要多少 **register / LDS / wave slot**。
- 只有當某個 CU 空出足夠資源，dispatcher 才把下一批 block 放進去；資源不夠就等。所以大 kernel 的 block 是**分批 resident、陸續執行**。

### CP 怎麼跟 scheduler 溝通？（其實是硬體狀態，不是軟體訊息）

注意有**兩個 scheduler**，別混：

- **workgroup dispatcher**：決定「哪個 block 進哪個 CU」。
- **warp/wavefront scheduler**（在每個 CU 內部）：block 進 CU 後，每個 cycle 挑一個 ready 的 wavefront 發射指令。

它們之間**不是靠軟體訊息，而是硬體訊號 / 內部狀態**：CU 回報自己的佔用（剩幾個 wave slot、register/LDS 剩多少），dispatcher 據此決定能不能再塞 block。這層握手是**晶片內部實作，未公開**，只保證對外語意。

### CP 怎麼「知道」有 dependency？——它不知道，是軟體翻譯好的

**關鍵：CP 根本不理解 dependency，也不分析 kernel、不需要 subgraph。** 相依關係是 **runtime / driver 事先翻譯成 CP 看得懂的顯式同步指令**，CP 只是機械地照做。CP 只懂兩件事：**照 queue 順序做**、**遇到「等某個值」的 packet 就卡住等**。

- **同一條 stream 內的順序**：不需要 CP 判斷——順序本身就是相依。runtime 把工作依序放進同一條 in-order queue，再靠 packet 的 **barrier bit**（AMD AQL packet 的 barrier 欄位）確保「前面所有 packet 完成後才啟動」。
- **跨 stream 的相依**：沒有共用 queue，必須顯式表達，底層被翻成一對 **signal / wait（semaphore / fence，就是記憶體裡一個數值）**。例如：

```cpp
hipEventRecord(e, streamA);        // A 的 queue 尾端插一個 signal packet：做完把 S 設為目標值
hipStreamWaitEvent(streamB, e, 0); // B 的 queue 前面插一個 wait packet：S 未達標前不准往下跑
```

CP 在 wait packet 做的事非常笨：**只是比較一個記憶體數值有沒有到目標**，完全不知道那代表「kernel1 的資料好了」。相依語意在軟體，硬體只剩「等一個數字」。

> **那 subgraph / 相依圖在哪？在軟體，不在 CP。** 用 stream+event 時，相依圖隱含在你呼叫的順序裡，runtime 邊呼叫邊把 barrier/signal/wait packet 塞進正確 queue；用 **HIP Graph / CUDA Graph** 時相依圖是顯式建的（node+edge），但 submit 時仍被**編譯成一堆 queue 提交 + signal/wait**，硬體看到的依然只是 signal/wait。Graph 的好處是圖已知、可先最佳化並降低 CPU launch overhead，但不改變 CP 只懂 signal/wait 的事實。

### 跨 stream：後 launch 的 kernel 可能搶先執行嗎？

**可以。** 順序保證**只存在於同一條 stream 內**，跨 stream **沒有任何全域的先來後到保證**：

| 情況 | 有無順序保證 |
|---|---|
| 同一條 stream 內先後兩個 kernel | ✅ FIFO：先 enqueue 的先做完，後一個才開始 |
| 不同 stream 的兩個 kernel（無相依） | ❌ 無保證：後 launch 的可能先跑 / 先完成 |
| 同一個 kernel 內不同 block 之間 | ❌ 無保證：哪個 block 先跑、在哪個 CU 跑都不可控 |

原因就是上面的機制：block 分派是「哪個 CU 空出來、哪條 ACE 佇列有空」就發，沒有「按 launch 時間排序」的全域仲裁。**所以絕不能靠「launch 順序」做跨 stream 同步**——要保證順序只能用 event / `hipStreamWaitEvent` / 放同一條 stream。



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


| CUDA 元件          | 餐廳比喻       |
| ---------------- | ---------- |
| CPU              | 客人 / 經理    |
| CUDA/HIP runtime | 櫃台         |
| driver           | 後場調度員      |
| stream           | 點餐隊列       |
| kernel           | 一道菜的做法     |
| kernel arguments | 食材與數量      |
| grid             | 整批訂單       |
| block            | 一桌 / 一組任務  |
| thread           | 廚師手上的一個小動作 |
| SM / CU          | 廚房工作站      |
| warp / wavefront | 一組同時動作的廚師  |


流程：CPU 說「做 vecAdd，4096 組、每組 256 個小工作」→ runtime 整理成訂單 → driver 放進 GPU
工作隊列 → GPU 把 block 分給各 SM/CU → SM/CU 把 threads 分成 warp 開始算 → CPU 不用等，可先做別的。

## 最容易誤會的幾件事


| 誤會                               | 正確說法                                                                     |
| -------------------------------- | ------------------------------------------------------------------------ |
| CPU launch 後會等 GPU 跑完            | 通常不會。launch 非同步，要結果須 synchronize / event / blocking copy。                |
| CPU 把每個 thread 一個個送到 GPU         | 不會。CPU 只送一個 launch command，GPU 自己拆 grid → block → warp。                  |
| GPU 一次同時跑所有 threads              | 不一定。logical threads 可能上百萬，硬體分批 resident 執行。                              |
| `kernel<<<...>>>()` 是普通 C++ 函式呼叫 | 不是。本質是「向 GPU 提交工作」。                                                      |
| GPU 可直接用 CPU 指標                  | 通常不行。需 `cudaMalloc` 取得 device pointer，或用 unified / mapped pinned memory。 |




## 公開語意 vs 實作相關

- **公開且可依賴**：launch 非同步、**同一 stream 內** FIFO 順序、**跨 stream 與 block 間無順序保證**、
相依需用 barrier bit / signal-wait 顯式表達、參數透過參數區傳遞、錯誤檢查兩段式。
- **實作相關（不要寫死依賴）**：command buffer / doorbell / MMIO 細節、CP 與 workgroup dispatcher
的握手協定、block 實際分派到哪個 SM/CU、JIT 是否觸發、lazy init 的精確時機——隨 OS / driver /
GPU 世代 / MIG / MPS / 虛擬化而異。



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