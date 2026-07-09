<!--
學習筆記。「我學到什麼 / 卡關 / Questions」由你親手寫；AI 只協助補 code/doc 連結與格式化。
對應 roadmap：P0・06-29（精讀 example01）。
-->

# 0629｜精讀 example01：逐行讀懂手寫 AMDGCN reduce

## 今日目標
能逐行讀懂一支完整手寫 kernel（`reduce_sum`）並 build & run 到 `verification : PASS`。（階段：P0）

## 對應 roadmap item
- [ ] 讀 [asm/example01_reduce_sum/README.md](../../../asm/example01_reduce_sum/README.md) 全 4 節
  - Prerequisites / Build：用 CMake 把 `.s` 組成 `.hsaco`
  - Run / Expected output：成功會印 `verification : PASS`
  - ✅ 完成判準：能說出 host 端 `hipModuleLoad` → `hipExtModuleLaunchKernel` 的流程
- [ ] 讀 `.s`（[reduce_sum_f32_gfx942.s](../../../asm/example01_reduce_sum/reduce_sum_f32_gfx942.s)，219 行）逐段
  - L13–36：kernarg load → exec-mask 邊界保護的 `global_load_dword` → `s_waitcnt vmcnt(0)`
  - L38–56：第一個 LDS reduction 階段（`ds_write` → `s_barrier` → +128 offset）
  - L57–172：其餘 7 個 reduction 階段（offset 遞減）+ 最終 `global_store`
  - L174–219：AMDHSA kernel descriptor / metadata（每欄對應一個實體資源）
  - ✅ 完成判準：能不看檔說出「為何每個 reduction 階段之間都要 `s_barrier`」
- [ ] 跑 build & run
  - ✅ 完成判準：跑出 PASS，且能對應「組語裡哪段對應這次輸出的部分和」
  - 📚 參考資源：[asm/example01_reduce_sum](../../../asm/example01_reduce_sum)（README + `.s`；待擴充 isa/gfx942-isa-reference.md）

## 操作記錄
```bash
cd /src/asm/example01_reduce_sum
cmake -S . -B build && cmake --build build -j"$(nproc)"
./build/hip_launch_reduce_sum            # 應印 verification : PASS
```
- build 結果：
- 執行輸出（是否 PASS）：

## 精讀記錄（.s 分段對照，填你自己的理解）
- L13–36 載入階段（`s_load_*` / `global_load_dword` / `s_waitcnt vmcnt`）：
- L38–56 第一個 LDS reduction（`ds_write` → `s_barrier`）：
- L57–172 其餘 reduction 階段 + `global_store`：
- L174–219 kernel descriptor / metadata：

## 我學到什麼（自己寫）
<!-- 用自己的話寫懂了什麼；越白話越好。這是學習的核心，不要讓 AI 代寫。 -->
-

## 卡關與如何解（自己寫）
<!-- 今天哪裡卡住、怎麼查到答案、最後怎麼解 -->
-

## 快速自測（先自答再核對）
1. 為什麼每個 reduction 階段之間都要 `s_barrier`？
2. 這支 baseline 為什麼慢？（從每個 wave 一次載入多少 bytes 想）
<details><summary>參考答案（roadmap）</summary>
1. 下一階段要讀上一階段寫進 LDS 的部分和，必須等整個 workgroup 寫完才能讀。
2. 每 wave 只發一條 `global_load_dword`＝256 B/wave，之後 stall 等 HBM（~上千 cycle），頻寬利用率低。
</details>

## code & doc 參考
- 範例（README + `.s`）：[asm/example01_reduce_sum](../../../asm/example01_reduce_sum)
- ISA 前導：[amd-isa-kernel.md](../amd-isa-kernel.md)「前置：定位工具 / 階段 A-1」
- （opcode 速查 isa/gfx942-isa-reference.md 為待擴充 stub）

## Questions 整理（自己寫）
-
