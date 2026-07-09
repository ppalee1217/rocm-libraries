<!--
學習筆記。「我學到什麼 / 卡關 / Questions」由你親手寫；AI 只協助補 code/doc 連結與格式化。
對應 roadmap：P0・06-30（⭐優化重點日：profiling 驅動優化完整迴圈）。
-->

# 0630｜example02：profiling 驅動優化完整迴圈

## 今日目標
第一次跑通「profile → 讀 counter → 改 code → 驗證加速」的完整迴圈，並能講出瓶頸如何從 counter 讀出來。
這是最薄弱、也是研究線 profiling 判讀的關鍵基礎。（階段：P0）
**（解鎖研究線：判讀 compute/memory-bound、判斷 benchmark 是否可信、定義 predictor 的目標 / feature。）**

## 對應 roadmap item
- [ ] 讀 [asm/example02_reduce_sum/README.md](../../../asm/example02_reduce_sum/README.md) 全 4 節（profiling 最佳單篇教材）
  - Build and run / Generating profiling data（`profile` → `analyze` 兩階段）
  - How the report led us to dwordx4（從報告讀出瓶頸 → 決定改哪行）
  - Performance comparison vs example01（before/after 數字表）
  - ✅ 完成判準：能複述「報告哪個面板 → 指向哪個瓶頸 → 改哪條指令」的因果鏈
- [ ] 跑 profile 與 analyze，讀三個面板
  - 2.1 System SoL（HBM BW% 與 VALU FLOPs%）／7.2 Wavefront Runtime（Dependency Wait）／10.1 Instruction Mix（VMEM/wave）
  - ✅ 完成判準：能從三個面板各讀出一個關鍵數字並說它代表什麼
- [ ] 讀 `.s` L25–56（向量化載入 + ILP register tree），對照 ex01
  - 兩條 `global_load_dwordx4`（每 thread 8 floats）＋ 8→1 ILP pairwise 加法樹
  - ✅ 完成判準：能解釋「`dword`→`dwordx4` + K=8/thread 為何帶來 1.90× 加速」
- [ ] 讀 [profiling-rocprof.md](../hipblaslt/profiling-rocprof.md)「怎麼讀這些指標」
  - coalescing / 向量化、latency hiding 與 Little's Law、compute vs memory-bound 判讀
  - ✅ 完成判準：能用 counter 數值說出一個 kernel 是 compute- 還是 memory-bound
- [ ] （AMD 資源，選做）HIP 200「HIP Tools」HW5（profiler trace/counter + debugger 讀 kernel 組語）＋ HIP 201「Performance Tuning for HIP Programs」（~1.5h），與本日 profiling 迴圈同主題
  - 📚 參考資源：[internal_docs/hip-training-at-amd.md](../internal_docs/hip-training-at-amd.md#hip-200-hip-tools)（HIP 200）、[HIP 201 段](../internal_docs/hip-training-at-amd.md#hip-201-performance-tuning-for-hip-programs)

## 操作記錄
```bash
cd /src/asm/example02_reduce_sum
cmake -S . -B build && cmake --build build -j"$(nproc)"
rocprof-compute profile --name reduce_n128m --path prof/n128m -- \
    ./build/hip_launch_reduce_sum ./build/reduce_sum_f32.hsaco 134217728
rocprof-compute analyze --path prof/n128m --tui
```
- 面板 2.1 System SoL（HBM BW% / VALU FLOPs%）：
- 面板 7.2 Wavefront Runtime（Dependency Wait Cycles）：
- 面板 10.1 Instruction Mix（VMEM 指令數/wave）：

## 對照數字（抄 ex01→ex02，供研究線當「可信量測」範例）
- HBM 峰值佔比：44.7% → 83.7%
- 加速：1.90×
- Dependency Wait：84.8% → 95.4%
- L2-Fabric 延遲：1270 → 2477 cycle（延遲上升但吞吐更高，見自測 2）

## 我學到什麼（自己寫）
<!-- 用自己的話寫懂了什麼；越白話越好。這是學習的核心，不要讓 AI 代寫。 -->
-

## 卡關與如何解（自己寫）
<!-- 今天哪裡卡住、怎麼查到答案、最後怎麼解 -->
-

## 快速自測（先自答再核對）
1. HBM 峰值佔比從 44.7% 升到 83.7% 代表 kernel 變成什麼 bound？
2. 為何 ex02 的 L2-Fabric 延遲上升，throughput 反而更高？
3. 怎麼從 counter 一眼判斷 compute-bound vs memory-bound？
<details><summary>參考答案（roadmap）</summary>
1. 更接近純 memory-bound（已逼近 HBM 頻寬上限）。
2. Little's Law：in-flight 請求數變多（每 wave 8 floats、2 條 dwordx4），用更多並行度掩蓋延遲，單筆延遲上升但總吞吐提高。
3. VALU/MFMA busy 高→compute-bound；MemUnit busy/stalled 高、HBM BW% 逼近峰值→memory-bound。
</details>

## 研究線連結（自己補）
<!-- 這套 profiling 判讀之後如何用在：定義 predictor 的 label（GFLOPS）與 feature、判斷 benchmark 是否可信 -->
-

## code & doc 參考
- 範例（profiling 最佳單篇教材）：[asm/example02_reduce_sum/README.md](../../../asm/example02_reduce_sum/README.md)
- counter 解讀：[hipblaslt/profiling-rocprof.md](../hipblaslt/profiling-rocprof.md)「第三步：怎麼讀這些指標」
- AMD 課程（選做）：[HIP 200 HIP Tools](../internal_docs/hip-training-at-amd.md#hip-200-hip-tools)（HW5）、[HIP 201 Performance Tuning](../internal_docs/hip-training-at-amd.md#hip-201-performance-tuning-for-hip-programs)
- 研究線 metric 對照：Solution Selection Metrics（Confluence `744174730`，efficiency vs ideal）

## Questions 整理（自己寫）
-
