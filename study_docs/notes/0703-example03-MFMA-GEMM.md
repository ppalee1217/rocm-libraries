<!--
學習筆記。「我學到什麼 / 卡關 / Questions」由你親手寫；AI 只協助補 code/doc 連結與格式化。
對應 roadmap：P1・07-03（example03：結構 + tiling + 主迴圈 + ATT）。
-->

# 0703｜example03：MFMA GEMM 結構 + tiling + 主迴圈 + ATT

## 今日目標
看懂 MFMA register layout 與 LDS staging，逐行讀懂主迴圈，並用 ATT trace 看出實際 stall 在哪。（階段：P1）
**（研究線用途：建立「一支真實 GEMM kernel 長什麼樣」的介面級直覺，之後理解 gene→kernel 映射用。）**

## 對應 roadmap item
- [ ] 讀 [asm/example03_mfma/README.md](../../../asm/example03_mfma/README.md) 結構三節
  - What the kernel does（32×32 輸出塊的 tiled GEMM）／Tiling summary（256 thread / 4 wave / 4 個 16×16 子 tile → 32×32）／Constraints
  - ✅ 完成判準：能畫出 256 thread → 4 wave → 4 子 tile → 32×32 的組成圖
- [ ] 讀 `.s`（[mfma_gemm_f32_gfx942.s](../../../asm/example03_mfma/mfma_gemm_f32_gfx942.s)，259 行）L6–119 結構段
  - L6–41 檔頭（tiling 表、kernarg layout、MFMA register layout：lane↔元素）／L43–59 kernarg/座標/stride／L61–119 staging 位址、LDS 讀位址、accumulator 清零
  - ✅ 完成判準：能說出「lane l 持有 A/B/D 的哪個元素」
- [ ] （原 07-02）跑 build & run（ATT 也需先 build 出 `.hsaco`，故放在跑 ATT 前；指令見下方「操作記錄」）
  - ✅ 完成判準：執行印出 `verification : PASS`、`max_abs_err 0`，拿到可被 ATT 使用的 `.hsaco`
  - 📚 參考資源：[asm/example03_mfma](../../../asm/example03_mfma)（README + `.s` + CMake）
- [ ] 讀 `.s` L121–167 主迴圈
  - L121–140 `.Lkloop` 開頭（4 條 global load → `ds_write` → `s_barrier`）／L141–156 核心（8 條 `ds_read` + 4 條 `v_mfma_f32_16x16x4_f32`）／L165–167 `s_nop 15` pipeline drain
  - ✅ 完成判準：能解釋「為何 MFMA 後要 `s_nop 15` 才能讀 accumulator VGPR」
- [ ] 讀 + 跑 ATT thread trace
  - ✅ 完成判準：能在 trace 指出開頭 `s_waitcnt lgkmcnt(0)` 造成的 leading stall 並說明成因

## 操作記錄
```bash
cd /src/asm/example03_mfma
cmake -S . -B build && cmake --build build -j"$(nproc)"
./build/hip_launch_mfma_gemm          # 應印 verification : PASS, max_abs_err 0
# ATT（容器內收集，RCV GUI 在桌機端）
rocprofv3 --att --att-target-cu 0 --att-shader-engine-mask 0x1 \
    --kernel-include-regex "mfma_gemm_f32" -d prof/att_mfma -- \
    ./build/hip_launch_mfma_gemm ./build/mfma_gemm_f32.hsaco 512 512 512
```
- build / run 結果（PASS?、max_abs_err）：
- ATT 找到的 leading stall：

## 精讀記錄（填你自己的理解）
- MFMA register layout（lane l 持有 A/B/D 的哪個元素）：
- 主迴圈 `.Lkloop` 資料流（load → ds_write → barrier → ds_read → mfma）：
- `s_nop 15` 的作用：
- ATT 輸出目錄結構（`code.json` = 每指令 hitcount/latency）：

## 我學到什麼（自己寫）
<!-- 用自己的話寫懂了什麼；越白話越好。這是學習的核心，不要讓 AI 代寫。 -->
-

## 卡關與如何解（自己寫）
<!-- 今天哪裡卡住、怎麼查到答案、最後怎麼解 -->
-

## 快速自測（先自答再核對）
1. 一條 `v_mfma_f32_16x16x4_f32` 的 K 維只有 4，BK=16 要幾條 MFMA 串起來？
2. `s_nop 15` 解決的是什麼問題？
3. 為什麼 ATT 範例固定用 512×512×512 並 pin CU 0？
<details><summary>參考答案（roadmap）</summary>
1. 4 條（每條 K=4，串 4 次覆蓋 BK=16）。
2. MFMA 寫回 accumulator 有長延遲；`s_nop` 填空避免太早讀到未就緒的 VGPR。
3. 保證 CU 0 一定被排到、trace 資料量可控、可重現。
</details>

## code & doc 參考
- 範例：[asm/example03_mfma](../../../asm/example03_mfma)
- ISA 橋接：[amd-isa-kernel.md](../amd-isa-kernel.md)（待擴充：isa/mfma-deep-dive.md、isa/gfx942-isa-reference.md）

## Questions 整理（自己寫）
-
