# 《Accelerated Computing with HIP》章節導讀

路徑說明：本檔在 `study_docs/gpu_knowledge/`。連回頂層用 `../`。

- 對應書檔：`Accelerated_Computing_with_HIP_Internal.pdf`（AMD 內部教材）。

## 白話總覽

這本書整體是 **11 個主章 + 2 個附錄**，主線從 HIP/ROCm 基礎、GPU 架構、效能分析、常見 kernel
pattern，一路到 stream、library、CUDA porting、多 GPU、datacenter 與第三方工具。本檔提供一張
「哪章在講什麼 / 何時查」的速查表，並把章節連回 repo 內既有學習文件。

## 為何重要

教材厚、不必從頭讀。依你當下目標（新手入門 / 效能優化 / CUDA 移植 / cluster 多 GPU）挑章節，
搭配 repo 內對應文件交叉閱讀，效率最高。

## 章節速查表

| 章節 | 主題 | 大概在講什麼 / 何時查 |
|------|------|----------------------|
| **Ch1 Introduction** | HIP / GPU / ROCm 入門背景 | 為何 GPU 適合平行運算、CPU vs GPU、ROCm 軟體堆疊、HIP 定位。第一次接觸先看。 |
| **Ch2 HIP Language** | HIP 語法與基本程式結構 | Hello World、`hipcc` 編譯、kernel launch、Runtime API、memory alloc/copy、thread/block/grid、vector add。寫第一支 HIP 程式的核心。 |
| **Ch3 AMD GPU Internals** | AMD GPU 硬體架構與效能基礎 | command processor、DMA engine、workgroup dispatch、CU、SIMD、wavefront、divergence、coalescing、memory hierarchy。理解「為何慢/怎麼寫快」必看。 |
| **Ch4 Tools for Performance Analysis & Debug** | ROCm profiling / debug 工具 | `rocprof`、`rocgdb`、ROCm SMI。量 kernel 時間、讀 counter、debug。開始調校/除錯時查。 |
| **Ch5 HIP Programming Patterns** | 常見 GPU kernel 設計模式 | gamma correction、stencil/convolution、reduction、matmul tiling、transpose coalescing、BFS。實戰優化重點章。 |
| **Ch6 HIP Streams** | Stream、非同步與 overlap | stream 建立/同步、async copy、concurrent kernels、computation/communication overlap。想做 pipeline overlap 看這章。 |
| **Ch7 ROCm Libraries** | ROCm 高效能函式庫 | rocBLAS、rocSPARSE、rocFFT、rocRAND。很多運算不必自寫 kernel，直接用 library。 |
| **Ch8 Porting CUDA to HIP** | CUDA → HIP 移植 | Hipify（`hipify-clang` / `hipify-perl`）、移植 guideline、transpose 範例、常見 pitfall。手上有 CUDA code 要轉 HIP 看這章。 |
| **Ch9 Multi-GPU Programming** | 多 GPU 程式設計 | HIP device API、stream/thread/MPI-based 寫法、GPU-GPU 通訊、RCCL collective。單 GPU 熟後擴展多 GPU。 |
| **Ch10 ROCm in Datacenters** | 資料中心 / HPC 部署 | containerized ROCm、Docker、Kubernetes、SLURM、interactive/batch job。在 cluster/HPC 跑時看。 |
| **Ch11 Third-Party Tools** | 第三方 profiling / 除錯 | PAPI、Score-P/Vampir、Trace Compass、TAU、TotalView、HPCToolkit、E4S。進階 tracing / performance engineering。 |
| **Appendix A CDNA Assembly** | AMD GPU assembly / 低階分析 | 取出 kernel binary、反組譯 CDNA、register、instruction type、memory access、shifted copy/branching 範例。看 ISA / compiler output 時查。 |
| **Appendix B ML with ROCm** | ROCm 上的機器學習框架 | PyTorch / TensorFlow on ROCm。目標是 DL workload 而非手寫 kernel 時看。 |

## 快速閱讀建議（依目標選路徑）

- **HIP 新手**：Ch1 → Ch2 → Ch4 → Ch5。先懂 HIP/ROCm 與基本程式，再學 profiling/debug，最後進 kernel pattern。
- **效能優化**：Ch3 → Ch5 → Ch6 → Ch11 → Appendix A。Ch3 建立 wavefront/coalescing/memory hierarchy 概念；Ch5/6 實作；Ch11 與 Appendix A 偏進階分析。
- **CUDA 移植**：Ch2 → Ch8 → Ch4 → Ch5。先熟 HIP API，用 Hipify 移植，再用工具驗證效能與正確性。
- **cluster / 多 GPU / datacenter**：Ch6 → Ch9 → Ch10 → Ch11。先懂 stream，再擴展多 GPU，最後處理 SLURM/K8s/container 與大型 profiling。

## 連回 repo 內既有文件

- **Ch3（AMD GPU Internals）** → [execution-model.md](execution-model.md)（CU/wavefront/coalescing 概念）、[../amd-isa-kernel.md](../amd-isa-kernel.md)（gfx942 實作）。
- **Ch2 / Ch8（語言 / porting）** → [cuda-hip-terminology.md](cuda-hip-terminology.md)、[../cuda-to-hip.md](../cuda-to-hip.md)。
- **Ch4 / Ch11（profiling）** → [../hipblaslt/profiling-rocprof.md](../hipblaslt/profiling-rocprof.md)。
- **Ch5（patterns：reduction / matmul tiling）** → [../amd-isa-kernel.md](../amd-isa-kernel.md) 階段 A 範例、`../../asm/`。
- **Appendix A（CDNA assembly）** → [../amd-isa-kernel.md](../amd-isa-kernel.md)、[../isa/gfx942-isa-reference.md](../isa/gfx942-isa-reference.md)。
- **Ch7（ROCm libraries）** → [../hipblaslt/README.md](../hipblaslt/README.md)（hipBLASLt 即一個 BLAS library 的深入案例）。

## 交叉連結

- 本資料夾入口：[README.md](README.md)
- 頂層學習地圖：[../README.md](../README.md)
- 八週進度表：[../learning-roadmap.md](../learning-roadmap.md)

## 一句話總結

不必從頭讀整本，依目標選路徑：

- 新手走 Ch1-2-4-5。
- 優化走 Ch3-5-6-11+附錄A。
- 移植走 Ch2-8-4-5。
- 多 GPU 走 Ch6-9-10-11，並搭配 repo 內對應文件交叉閱讀。
