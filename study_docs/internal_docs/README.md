# Internal AMD Documents — Categorized URL Index

This folder holds **full markdown copies** of internal AMD Confluence pages relevant to
GPU architecture, HIP programming, and the hipBLASLt / TensileLite GEMM stack. The pages
were fetched from AMD's internal Confluence (`amd.atlassian.net`) via the Atlassian MCP on
**2026-06-26** and saved here so future agents can read the full content as markdown
(the source pages require AMD SSO).

> **Confluence cloudId (AMD site):** `3ade9f4f-3a5e-4909-bc67-8816482a10f4`
> Re-fetch a page with the Atlassian MCP tool `getConfluencePage`
> (`{"cloudId": "...", "pageId": "...", "contentFormat": "markdown"}`).

---

## GPU / GCN Architecture

| Document | URL | pageId | Description | Local copy |
| --- | --- | --- | --- | --- |
| GCN (Graphics Core Next) Architecture Training Resources | https://amd.atlassian.net/wiki/spaces/MLSE/pages/744166024 | `744166024` | MLSE training-series hub: 9 recorded talks (GPU overview, scheduling, memory/CU arch, gfx9 roadmap, compiling, HIP, ML/OpenMP) plus GCN/CDNA background reading. | [gcn-architecture-training-resources.md](./gcn-architecture-training-resources.md) |

## HIP Programming & Training

| Document | URL | pageId | Description | Local copy |
| --- | --- | --- | --- | --- |
| HIP Training at AMD | https://amd.atlassian.net/wiki/spaces/LC/pages/531791935 | `531791935` | Learning Center hub for all HIP courses (100/200/300 levels) with full content of every course sub-page. | [hip-training-at-amd.md](./hip-training-at-amd.md) |
| HIP 100: Fundamentals of HIP Programming | https://amd.atlassian.net/wiki/spaces/LC/pages/531791953 | `531791953` | Intro HIP: thread/memory hierarchy, kernels, matrix transpose, debugging; Homework 1. | (in `hip-training-at-amd.md`) |
| HIP 101: HIP Programming Part A | https://amd.atlassian.net/wiki/spaces/LC/pages/531795556 | `531795556` | Kernel language, memory hierarchy, device queries; Homework 2 (transpose + matmul). | (in `hip-training-at-amd.md`) |
| HIP 102: HIP Programming Part B | https://amd.atlassian.net/wiki/spaces/LC/pages/531793232 | `531793232` | Synchronization, atomics, warp ops, streams/events; Homework 3 (histogram, with full C++ source). | (in `hip-training-at-amd.md`) |
| HIP 103: AMD GPU Architecture | https://amd.atlassian.net/wiki/spaces/LC/pages/531793350 | `531793350` | GCN architecture, kernel launch, instruction execution, memory hierarchy; Homework 4 (memory coalescing). | (in `hip-training-at-amd.md`) |
| HIP 200: HIP Tools | https://amd.atlassian.net/wiki/spaces/LC/pages/531795545 | `531795545` | rocminfo, rocm-smi, profiler/tracer, debugger; Homework 5 (profiling + debugging). | (in `hip-training-at-amd.md`) |
| HIP 201: Performance Tuning for HIP Programs | https://amd.atlassian.net/wiki/spaces/LC/pages/531793005 | `531793005` | Tuning HIP programs for performance (video/slides). | (in `hip-training-at-amd.md`) |
| HIP 202: HIPify and CUDA to HIP | https://amd.atlassian.net/wiki/spaces/LC/pages/531793000 | `531793000` | hipify-perl / hipify-clang porting workflow; CNN and K-means porting demos. | (in `hip-training-at-amd.md`) |
| HIP 203: HIP/ROCm Libraries A | https://amd.atlassian.net/wiki/spaces/LC/pages/531792300 | `531792300` | rocBLAS library overview. | (in `hip-training-at-amd.md`) |
| HIP 204: HIP/ROCm Libraries B | https://amd.atlassian.net/wiki/spaces/LC/pages/531804614 | `531804614` | rocSPARSE, rocFFT, rocRAND. | (in `hip-training-at-amd.md`) |
| HIP 300: Multi-GPU Scaling | https://amd.atlassian.net/wiki/spaces/LC/pages/531804260 | `531804260` | Multi-GPU programming, GPU-GPU communication, RCCL. | (in `hip-training-at-amd.md`) |
| HIP FEEDBACK PAGE | https://amd.atlassian.net/wiki/spaces/LC/pages/531795464 | `531795464` | Feedback survey + tracking table for the HIP training. | (in `hip-training-at-amd.md`) |
| HIP at AMD: 100/200/300 Level (containers) | https://amd.atlassian.net/wiki/spaces/LC/pages/531807554 | `531807554`, `531804264`, `531804266` | Empty grouping pages (no body); listed for completeness. | (in `hip-training-at-amd.md`) |

## hipBLASLt / TensileLite

| Document | URL | pageId | Description | Local copy |
| --- | --- | --- | --- | --- |
| Internal AMD Reference on hipBLASLt & TensileLite | https://amd.atlassian.net/wiki/spaces/~7120204c779face96d403c9783064701435635/pages/1763641016 | `1763641016` | ROVO-authored master index for hipBLASLt basics, solution selection, and TensileLite codegen; links ~50 internal pages. | [hipblaslt-tensilelite-reference.md](./hipblaslt-tensilelite-reference.md) |
| Kernel Generator: TensileLite (GEMM Kernel Tuning Guide) | https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119 | `1405870119` | Authoritative tuning-config guide: GlobalParameters/ForkParameters, `MatrixInstruction` 9-element format, solution-naming convention, tune→merge→rebuild→verify workflow. (Examples gfx1150/WMMA.) | [tensilelite-kernel-generator.md](./tensilelite-kernel-generator.md) |
| tensilelite yaml config for Kernel A-E (draft) | https://amd.atlassian.net/wiki/spaces/MLSE/pages/1732654216 | `1732654216` | Concrete reference YAML param sets for 5 MX (MXFP8/MXFP4) kernel families; copy+adapt instead of writing grids from scratch. | [tensilelite-yaml-config-kernel-a-e.md](./tensilelite-yaml-config-kernel-a-e.md) |
| Koji Nakajima Technology Transfer (Tensile param deck + tuning tips) | https://amd.atlassian.net/wiki/spaces/MLSE/pages/744192975 | `744192975` | Hosts the `MI300_tensilelite_Tensile_Kernel_Generation_Parameters_Overview_v1.1.pptx` deck (non-fetchable attachment) + codegen-bug debug tips; points to the `TensileScripts` repo's `ConfigGenerator.py` / `tuning_driver/driver.py`. | (index only — deck is `.pptx`, not fetchable) |

> The hipBLASLt reference above links to many further internal pages (GEMM hub, solution
> selection, TensileLite codegen, tuning dashboards, onboarding, etc.). Those are **not**
> mirrored locally yet — open the reference doc and follow the inline links, or fetch them
> by pageId via the MCP. Notable canonical pointers it cites:
> - GEMM (hipblasLt) hub — `1368714159`
> - Solution selection — `744176549`
> - Tensilelite - GEMM kernel generation — `1405990433`
> - Kernel Generator: TensileLite — `1405870119`
> - GEMM Kernel Optimization (GEKO) — `1186895430`
> - HIPBLASLT Onboarding — `1711090025`

## Other

| Document | URL | Description |
| --- | --- | --- |
| hipBLASLt API reference (public ROCm docs) | https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/api-reference.html | Public API reference for hipBLASLt (not Confluence). |

---

## External resources referenced (inside the GCN page)

These are linked from the GCN Architecture Training Resources page (`744166024`). They live
on SharePoint / Microsoft Stream / p4web / external sites and are **NOT fetchable via the
Confluence MCP** — they need AMD SSO, VPN, or a browser. URLs preserved verbatim.

### Recorded talk videos (Microsoft Stream)

- GPU Overview and Scheduling Kernels — https://web.microsoftstream.com/video/6b3424a4-5197-447e-9e69-96656982b36d
- Scheduling Kernels — https://web.microsoftstream.com/video/82ad7631-3fe7-4100-9f4c-b6913a91492c
- Memory, IO, and CU Architecture on gfx9 — https://web.microsoftstream.com/video/6dcd95e8-626e-4c20-bc4b-c6c19685ed69
- AMD gfx9 Product Portfolio and Roadmap — https://web.microsoftstream.com/video/e7820dcb-df3e-4a42-86b3-079ed0631c30
- Compiling for gfx9 — https://web.microsoftstream.com/video/b4c61390-687e-46ec-9024-99f71a178f5b
- HIP Programming Course — https://web.microsoftstream.com/video/80d7c859-b850-4cd7-bda7-1fde6ed9bf51
- ML Applications and Platforms — https://web.microsoftstream.com/video/6354acff-fada-429f-944b-0e5a2e118434
- OpenMP — https://web.microsoftstream.com/video/4a60dd66-5fec-4e87-b6d6-b456befb4c6d
- HIP Programming Course - Advanced — https://web.microsoftstream.com/video/16f1907b-b178-48ab-82bc-0eb234f52c06

### Offline videos & slide decks (SharePoint, amdcloud-my)

- GPU Overview — offline video / slides: see `gcn-architecture-training-resources.md` (jgreatho_amd_com `ESTApON_HYZ...`, `EU_aopm9G_FH...`)
- Scheduling Kernels — offline video / slides (`EY2xsY-M...`, `EY-0HdmM...`)
- Memory/IO/CU Architecture — offline video / slides (`ESWmvonz...`, `EUe9ooGw...`)
- gfx9 Portfolio/Roadmap — offline video / slides (`EU6CAMdM...`, `EVHlgudR...`)
- Compiling for gfx9 — offline video (avoicu_amd_com `Ef4uDp-r...`) / slides PDF (`ESkB5vb4...`)
- HIP Programming Course — offline video / slides (dancyca2_amd_com `EdUxchw8...`, `EZlGoSwd...`)
- ML Applications — offline video (`EbIlB4gU...`); ML Apps & Frameworks slides (adaml_amd_com `EQKIazqV...`); TensorFlow/XLA/MLIR slides (whchung_amd_com `EaMvj9T0...`)
- OpenMP — offline video / slides (`EYGKtivi...`, `EdI9Lz44...`)
- HIP Advanced — offline video / slides (dancyca2 `EVHxuwwg...`, `EbqTgtJM...`)
- AMD GPUVM for ROCm v1.3 (Joe Greathouse) slides — `EXi96pb0...`
- AMD GCN Architecture White Paper (PDF) — `EUYOx_wI...`
- Layla Mah's GCN Crash Course slides — `EfkN58Bw...`
- MLSE team drive (all GCN training, 5 parts) — https://amdcloud.sharepoint.com/:f:/r/sites/mlse/Shared%20Documents/Internal%20-%20MLSE%20All/Training/GCN%20Training%20(5%20parts)

### p4web internal docs (Perforce web)

- Gfx9 Overview document — `GFX9_TopLevel_Arch_Short_V2.docx` (http://p4web.amd.com:1677/...)
- Internal ISA guide for gfx9 GPUs — `Gfx9_Shader_Programming.docx` (http://p4web.amd.com:1677/...)

### Public web (fetchable without SSO)

- Intro to AMD GPU programming with HIP (YouTube) — https://www.youtube.com/watch?v=3ZXbRJVvgJs
- AMD Graphics Core Next Presentation (PDF) — http://developer.amd.com/wordpress/media/2013/06/2620_final.pdf
- Introduction to Vega 10 (Hot Chips PDF) — https://www.hotchips.org/wp-content/uploads/hc_archives/hc29/HC29.21-Monday-Pub/HC29.21.10-GPU-Gaming-Pub/HC29.21.120-Radeon-Vega10-Mantor-AMD-f1.pdf
- Advanced Shader Programming on GCN (GDC2017, gpuopen PDF) — https://gpuopen.com/wp-content/uploads/2017/03/GDC2017-Advanced-Shader-Programming-On-GCN.pdf
- HIP to be Squared tutorial (gpuopen) — https://gpuopen.com/hip-to-be-squared-an-introductory-hip-tutorial/
- Various HIP guides (ROCm-Developer-Tools/HIP on GitHub): hip_porting_guide.md, hip_programming_guide.md, hip_terms.md, hip_kernel_language.md, hip_faq.md
- Teams channel "GPUs for graphics" — https://teams.microsoft.com/l/team/19%3a62201fa0a7144f839c4f050b53095c20%40thread.skype/...

### External, referenced from HIP training pages

- AMD HIP Training Course video mirror (Notion) — https://syifan.notion.site/AMD-HIP-Training-Course-86cb772392dc45d9bc19f7018878505c
- HIP Program files.zip (Confluence attachment, pageId 531793018) — https://amd.atlassian.net/wiki/download/attachments/531793018/HIP%20Program%20files.zip

---

## How to extend this index

When you add a new internal doc:

1. Fetch it with the Atlassian MCP `getConfluencePage`
   (`{"cloudId": "3ade9f4f-3a5e-4909-bc67-8816482a10f4", "pageId": "<id>", "contentFormat": "markdown"}`),
   and for hub/landing pages also run `getConfluencePageDescendants` to pull sub-pages.
2. Save the full markdown as `internal_docs/<slug>.md` with a front-matter blockquote at the
   top: Source URL, pageId, Space, Version/last-updated, and "fetched on <date>".
3. Add a row to the most appropriate category table above (create a new category heading if
   none fits). Include: title, Confluence URL, pageId, a 1-line description, and a relative
   link to the local copy (or note where the content lives if folded into another file).
4. If the page references non-Confluence assets (SharePoint, p4web, Stream, YouTube, PDFs),
   list those URLs verbatim under "External resources referenced" so they stay discoverable.
