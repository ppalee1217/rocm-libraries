

# 0627｜HIP A-1：第一支自寫 kernel + 反組譯

## 今日目標

寫出 vector add，反組譯對照基本 gfx942 指令家族。（階段：P0，彈性日）

## 對應 roadmap item

- [ ] 搞懂 GPU 執行階層（通用，gfx942 字彙的前導）
  - 軟體抽象 grid → block → thread；硬體實體 GPU → SM/CU → warp/wavefront → lane
  - ✅ 完成判準：能畫出「軟體抽象 vs 硬體實體」兩張階層圖並對應，且能答「AMD 有沒有 tensor/cuda core」
- [ ] 喚回 CUDA→HIP 名詞對照（你有 CUDA 背景，這步是喚回記憶）
  - ✅ 完成判準：能不查表寫出對應，並說出 shared↔LDS、warp(32)↔wavefront(64) 的差別
- [ ] 搞懂 gfx942 執行模型的基本字彙（讀組語的前提）
  - wave = 64 lane / SGPR vs VGPR / `s_waitcnt vmcnt` vs `lgkmcnt`
  - ✅ 完成判準：能解釋為何同一段程式同時需要 `vmcnt` 與 `lgkmcnt` 兩種等待
- [ ] 動手寫 vector add、反組譯、把組語對回原始碼
  - ✅ 完成判準：能逐條指出 `.s` 裡每個指令家族對應原始 C++ 的哪一行
  - 📚 參考資源：[asm/example01_reduce_sum](../../../asm/example01_reduce_sum)（同類手寫組語可比對）
- [ ] （AMD 資源，選做）HIP 101「Part A」（~2h，kernel language/thread hierarchy）；GCN talk #5「Compiling for gfx9」
  - 📚 參考資源：[internal_docs/hip-training-at-amd.md](../internal_docs/hip-training-at-amd.md#hip-101-hip-programming-part-a)、[gcn-architecture-training-resources.md](../internal_docs/gcn-architecture-training-resources.md)（talk #5）



## 我學到什麼（自己寫）

#### 搞懂 GPU 執行階層（通用，gfx942 字彙的前導）


#### 喚回 CUDA→HIP 名詞對照


#### 搞懂 gfx942 執行模型的基本字彙（讀組語的前提）


#### 動手寫 vector add、反組譯、把組語對回原始碼

## 卡關與如何解（自己寫）





## 反組譯記錄（填你在 .s 找到的指令）

- 編譯：`hipcc --offload-arch=gfx942 --save-temps -c vadd.hip`
- `s_load_*`（載 kernarg）：
- `global_load_*`（讀 HBM）：
- `v_add_f32`（運算）：
- `s_waitcnt`（哪種 cnt）/ `s_endpgm`：
- 對回原始 C++ 哪幾行：



## code & doc 參考（可請 AI 協助補連結）

- 執行階層（通用）：[gpu_knowledge/execution-model.md](../gpu_knowledge/execution-model.md)
- CUDA→HIP 名詞對照：[gpu_knowledge/cuda-hip-terminology.md](../gpu_knowledge/cuda-hip-terminology.md)、[cuda-to-hip.md](../cuda-to-hip.md)
- gfx942 字彙（A-1）：[amd-isa-kernel.md](../amd-isa-kernel.md)「前置：定位工具 / 階段 A-1」
- 可比對的手寫組語：[asm/example01_reduce_sum](../../../asm/example01_reduce_sum)
- AMD 課程（選做）：[HIP 101 Part A](../internal_docs/hip-training-at-amd.md#hip-101-hip-programming-part-a)、[GCN talk #5](../internal_docs/gcn-architecture-training-resources.md)



## Questions 整理（自己寫）

