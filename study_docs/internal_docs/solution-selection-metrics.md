# Solution Selection Metrics

> **Source URL:** https://amd.atlassian.net/wiki/spaces/MLSE/pages/744174730/Solution+Selection+Metrics
> **pageId:** `744174730`
> **Space:** MLSE (Machine Learning Software Engineering)
> **Version:** 11
> **Fetched on:** 2026-07-08 (via Atlassian Confluence MCP, `convert_to_markdown=true`)
>
> 定義 solution selection 的效率評估指標（vs ideal / vs hand-tuned / vs 競品硬體）與量測步驟。
> 頁面主要內容為儀表板截圖（mi100/a100、F32/F64），圖檔未下載，僅保留 Confluence 連結。

---

## Objectives

1. To determine solution selection efficiency compared to ideal performance.
2. To determine solution selection efficiency compared to hand tuning kernels.
3. To determine solution selection efficiency compared to competitor's comparable hardware.

## Steps

- Measure the FLOPS performance of the current solution selection method in rocBLAS for a sweep of matrix sizes.
- Determine the set of unique kernels that were used to generate the measured performance.
- Run identical performance comparison on cuBLAS.

## Sample Dashboard Output

以下為原頁的儀表板截圖（圖檔未下載，連結指向 Confluence 附件）：

- **F32 and F64 Flops Performance (mi100 vs a100) vs M=N** — [FlopsMN_mi100vsa100.png](https://amd.atlassian.net/wiki/rest/api/content/744174730/child/attachment/att744572824/download)
- **F32 and F64 Flops Performance (mi100 vs a100) vs Total Flops** — [FlopsTotal_mi100vsa100.png](https://amd.atlassian.net/wiki/rest/api/content/744174730/child/attachment/att744572826/download)
- **mi100 F32 kernel selection** — [mi100f32_kernels.PNG](https://amd.atlassian.net/wiki/rest/api/content/744174730/child/attachment/att744665395/download)
- **mi100 F64 kernel selection** — [mi100f64_kernels.PNG](https://amd.atlassian.net/wiki/rest/api/content/744174730/child/attachment/att744728132/download)
- **a100 F32 kernel selection** — [a100f32_kernels.PNG](https://amd.atlassian.net/wiki/rest/api/content/744174730/child/attachment/att744703653/download)
- **a100 F64 kernel selection** — [a100f64_kernels.PNG](https://amd.atlassian.net/wiki/rest/api/content/744174730/child/attachment/att744677831/download)
