# tensilelite yaml config for Kernel A-E (draft)

> **Source URL:** https://amd.atlassian.net/wiki/spaces/MLSE/pages/1732654216/tensilelite+yaml+config+for+Kernel+A-E+draft
> **pageId:** `1732654216`
> **Space:** MLSE
> **Version:** 5 (last updated 2026-06-19)
> **Fetched on:** 2026-06-27 (via Atlassian Confluence MCP, `contentFormat=markdown`)
>
> Draft of concrete TensileLite YAML parameter sets for five MX (MXFP8/MXFP4) kernel families.
> Useful as **reference configs** (copy + adapt) rather than writing parameter grids from scratch.
> NOTE: these target newer MX datatypes / gfx1250-class kernels; many entries are marked TBD/plan.

---

## Common settings

- **GlobalParameters:** `DataInitTypeAlpha: 1`, `DataInitTypeBeta: 0`
- **ProblemType:** `HighPrecisionAccumulate: True`, `TransposeA: True`, `TransposeB: False`,
  `UseBeta: True`, `Batched: True`, `SupportUserArgs: True`, `UseBias: 0`, `Activation: False`,
  `MXBlockA/MXBlockB`: 32 for fp8 / 16 for fp4, `DataTypeMXSA/DataTypeMXSB: e8`,
  `EnableMREG: [-1]` (default, auto-enabled).
- **Tuning parameters:** `WavefrontSize: [32]`, `PrefetchGlobalRead: [2]`, `PrefetchLocalRead: [1]`,
  `ScheduleIterAlg: [0]`, `TDMInst: [3]`, `1LDSBuffer: [0]`, `StaggerU: [0]`,
  `ForceDisableShadowInit: [True]` (reduce sgpr usage with TDMInst), `ExpandPointerSwap: [False]`.
- **Subtile:** `UseSubtileImpl: [True]`.
- **Plan to use (TBD):** `ScheduleIterAlg: [4]` (once supported on gfx1260); `WorkGroupMapping` /
  `WorkGroupMappingXCC` (needs experiments with `ClusterDim`; gfx1250 kernels use WGM=1, WGMXCC=1
  with ClusterDim `[2,2]/[4,2]/[2,4]/[4,4]`); `PrefetchGL2: 1 or 2`.
- **More optimizations (TBD):** wave specialization, `ds_block_load_mcast` (A/B, MXSA/MXSB),
  `ds_load_mcast` (MX), LDS segment optimization, `DtlPlusLdsBuf` (3 LDS buffer with MT256x512).

## Kernel-specific settings

- **Kernel A: MXFP8 MAF** — `MatrixInstruction [32,64,128,1,1,4,4,2,2]` (MT256x512, needs MREG;
  with SourceSwap ⇒ MT512x256), `DepthU: [256]`, `AssertSummationElementMultiple: [256]`.
- **Kernel B: MXFP4 MAF** — `MatrixInstruction [32,64,256,1,1,4,4,2,2]` (MT256x512), `DepthU: [512]`,
  `AssertSummationElementMultiple: [512]`.
- **Kernel C: MXFP4 MAB** — `MatrixInstruction [32,64,256,1,1,1,1,1,4]` (MT32x256x1024) or
  `[16,16,128,1,1,1,4,1,4]` (MT16x256x1024), `DepthU: [1024]`. (MT16x256x1024 currently rejected
  by a `pad_interval` constraint — needs latest develop.)
- **Kernel D: OpenAI batched (MXFP8)** — `MatrixInstruction [32,64,128,1,1,1,2,2,2]` (MT64x256) or
  `[32,64,128,1,1,1,4,2,2]` (MT64x512), `DepthU: [256]`.
- **Kernel E: Meta Small K (MXFP8)** — `MatrixInstruction [32,64,128,1,1,4,4,2,2]` (MT256x512) or
  `[32,64,128,1,1,4,3,2,2]` (MT256x384), `DepthU: [256]`.

Recurring "plan to use" knobs across kernels: `SourceSwap: True` + `VectorWidthA: 4` (store
optimization), `HalfPLR` 1–3, `StoreRemapVectorWidth: [4]`, `TemporalHintB: [1]`, and `ClusterDim`
experiments. See the source page for the full per-kernel TBD notes.
