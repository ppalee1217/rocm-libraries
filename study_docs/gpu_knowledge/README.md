# GPU 背景知識（從這裡開始）

> 路徑說明：本資料夾在 `study_docs/gpu_knowledge/`。連回頂層用 `../`（如 `../README.md`）。

## 白話總覽

這個資料夾是 **GPU 通用背景知識層**，回答兩個入門問題：

1. GPU 怎麼組織與執行工作？（grid / block / thread → SM/CU / warp/wavefront 的軟硬體對照）
2. CPU 怎麼把 kernel 丟給 GPU，CUDA 名詞又怎麼對到 AMD / HIP？

它的定位在兩個現有 stub（[../cuda-to-hip.md](../cuda-to-hip.md)、[../glossary.md](../glossary.md)）與
[../amd-isa-kernel.md](../amd-isa-kernel.md)（gfx942 ISA 實作層）**之前**——先建立通用概念，再進
AMD-specific 的組語細節。適合 1.5 年前寫過 CUDA、現在補硬體架構與名詞的讀者。

## 閱讀順序（建議）

| 順序 | 文件 | 涵蓋 |
|------|------|------|
| 1 | [execution-model.md](execution-model.md) | grid / block / warp / thread / SM / CU 的差異與設計用途；AMD 有沒有 tensor/cuda core |
| 2 | [kernel-launch.md](kernel-launch.md) | CPU 把 kernel launch 到 GPU 的詳細步驟（CUDA 主軸 + HIP 對應） |
| 3 | [memory-hierarchy-and-chiplet.md](memory-hierarchy-and-chiplet.md) | 記憶體階層（register / LDS / L1 / L2 / MALL / HBM）、cache vs scratchpad、Infinity Cache 命名與 256MB 大小、XCD / chiplet 與 CDNA 世代 |
| 4 | [cuda-hip-terminology.md](cuda-hip-terminology.md) | CUDA ↔ HIP / ROCm 名詞完整對照（軟體 + 硬體 + 生態系） |
| 5 | [hip-book-guide.md](hip-book-guide.md) | 《Accelerated Computing with HIP》章節導讀 |
| 進階 | [cdna5-gfx1250.md](cdna5-gfx1250.md) | CDNA5 / gfx1250（MI450）深入：AGPR、WGP、MFMA→WMMA、dual-issue、同步原語、UDNA（**未來 migration 參考**） |

> **平台定位：** 本 repo 實驗平台是 **MI300（gfx942 / CDNA3）**；CDNA4（MI350）為近期 migration 目標、
> CDNA5（MI450）為更遠期參考。官方規格 PDF 索引見 [../isa/spec-sources.md](../isa/spec-sources.md)。

## 交叉連結

- 頂層學習地圖（兩軌總綱）：[../README.md](../README.md)
- 記憶體階層 + 晶粒組織（MALL / Infinity Cache / XCD）：[memory-hierarchy-and-chiplet.md](memory-hierarchy-and-chiplet.md)
- API 速查 / hipify：[../cuda-to-hip.md](../cuda-to-hip.md)
- 跨文件名詞彙總：[../glossary.md](../glossary.md)
- 接續的 gfx942 ISA 實作：[../amd-isa-kernel.md](../amd-isa-kernel.md)
- 最新架構（CDNA5 / gfx1250 / MI450）深入：[cdna5-gfx1250.md](cdna5-gfx1250.md)
- 官方規格 PDF（CDNA3 / CDNA4 白皮書 + ISA）本地索引：[../isa/spec-sources.md](../isa/spec-sources.md)
- 八週進度表：[../learning-roadmap.md](../learning-roadmap.md)

## 一句話總結

先在這裡建立「GPU 怎麼執行、CUDA 名詞怎麼對到 AMD/HIP」的通用心智模型，再進
[../amd-isa-kernel.md](../amd-isa-kernel.md) 學 gfx942 組語實作。
