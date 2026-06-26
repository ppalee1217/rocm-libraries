# Internal AMD Reference on hipBLASLt & TensileLite

> **Source URL:** https://amd.atlassian.net/wiki/spaces/~7120204c779face96d403c9783064701435635/pages/1763641016/Internal+AMD+Reference+on+hipBLASLt+TensileLite
> **pageId:** `1763641016`
> **Space:** personal space `~7120204c779face96d403c9783064701435635` (authored via ROVO AI)
> **Version:** 1 (created 2026-06-26)
> **Fetched on:** 2026-06-26 (via Atlassian Confluence MCP, `contentFormat=markdown`)
>
> Full content of the internal reference page. All Confluence/GitHub/JIRA links are
> preserved verbatim. This page is itself a curated index pointing at many other internal
> pages; the inline links below are the canonical pointers for each referenced resource.

---

## Summary

This report defines a **structured internal index** for AMD engineers working with **hipBLASLt**, its **solution-selection stack**, and the **TensileLite code generator**. It consolidates Confluence pages, repos, and training materials into three modular "reference packs," plus shared metadata and navigation guidance, so you can jump directly to the right resource for onboarding, debugging, or performance tuning.

* **Purpose & scope** – Establish a canonical, maintainable map of internal docs for hipBLASLt basics, solution selection, and TensileLite codegen, with consistent metadata, tags, and ownership.
* **Key themes** –

    * hipBLASLt as AMD's flexible GEMM workhorse (API, usage, basic tuning)
    * Solution selection as a two-stage equality + grid-based heuristic pipeline, increasingly augmented by Origami/Formocast and bench-driven swaps
    * TensileLite as the modern GEMM kernel generator (YAML → kernels → solution libraries) with emerging snippet/StinkyTofu infrastructure.

* **Major sections** –

    * Section 1 clarifies audience, usage modes, and links to HR/technical onboarding.
    * Section 2 standardizes metadata, tagging, and link hygiene for all entries.
    * Section 3 (Module A) indexes hipBLASLt concept, setup, API, and intro performance docs.
    * Section 4 (Module B) covers solution selection algorithms, tuning workflows, and debugging patterns.
    * Section 5 (Module C) covers TensileLite architecture, YAML configs, tuning, and extension guides.
    * Section 6 explains how to wire everything into a **central Confluence index page**.

* **Critical insights** –

    * The **GEMM (hipblasLt)** page should be treated as the front door for all three modules and is already used as a canonical hub for GEMM resources on new architectures like MI350/MI455 [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159).
    * **Grid-based selection and modern heuristics (Origami/Formocast)** now routinely reach **~98% of exact-tuned performance** on MI300X for many workloads, so the main practical gap is not raw kernel quality but coverage, stability, and debugability of the selection layer [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159), [Solution selection](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744176549).
    * **TensileLite** is on a clear path to absorb legacy Tensile, with characterization tests, snippet architecture, and StinkyTofu-based optimization used to de-risk refactors and new data types [Tensile Overview](https://amd.atlassian.net/wiki/spaces/~stebrown/pages/1364192827), [TensileLite Characterization Tests — Overview & Snapshot Governance](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1755647079), [TensileLite Snippet Architecture](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1643646497).
    * For day-to-day work, engineers get the best leverage by combining:

        * **hipBLASLt basics** → understand API & debugging knobs
        * **Solution-selection tooling** (hipblaslt-bench, tunableop, GEKO, bench-driven swaps) for coverage/perf
        * **TensileLite workflows** for when you must **change the kernel pool itself**, not just pick differently.

---

## 1. Document Purpose & Audience

### 1.1 Scope: Internal Index of hipBLASLt & TensileLite Materials

This document's core goal is to act as the **canonical internal index** for three tightly coupled areas: (A) hipBLASLt basics and API usage, (B) solution selection and tuning, and (C) TensileLite code generation. Rather than re-explain every concept, it organizes and annotates the best existing internal resources, explains how they relate, and adds guidance on when to use which document for which task. This avoids the common "hunt across twenty Confluence pages and GitHub READMEs" problem highlighted in multiple doc-improvement efforts [6. hipblaslt documentation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1162287265).

The scope is deliberately **engineering-focused**: build, debug, tune, and extend. HR, IT, and generic HIP training are linked only where they unblock these technical tasks. Materials span Confluence spaces (MLSE, RCPT, SHARK, DCGPUAIST, SSET), ROCm/rocm-libraries GitHub, SharePoint decks, and dashboards such as the hipBLASLt tuning dashboard [Dashboard: hipBLASLt GEMM Tuning](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1045306155).

An important design choice is that this index is **modular**: each module (A/B/C) is written so it can be copy-pasted as its own Confluence page and still make sense. That way, teams can embed only the hipBLASLt basics, or only the TensileLite tuning section, in their own project spaces while still pointing back to the full cross-module index here.

### 1.2 Target Readers

The primary audience consists of three overlapping groups:

1. **New team members** in MLSE math libs, ROCm Core Perf, or related groups (CK, MIOpen, AITER) who need to ramp on GEMM quickly. For them, this index acts as a curated "first two weeks" map pointing from corporate onboarding to HIP fundamentals and then into hipBLASLt/TensileLite specifics [Onboarding & Learning](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744183858), [HIPBLASLT Onboarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1711090025).
2. **Performance engineers and application teams** (e.g., DCGPU AIST, Data Center Performance, framework teams) who are already familiar with HIP but need to understand:

    * how hipBLASLt chooses GEMM kernels and how to override that,
    * how to run tuning workflows for specific models or GEMM shapes,
    * how to diagnose "OOB perf is fine except for these ten shapes" problems [hipBLASLt User Feedback](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1706234950).

3. **Library maintainers and codegen developers** (hipBLASLt core, TensileLite, GEKO, StinkyTofu) who need a shared reference for the ecosystem: what tools already exist, where heuristics live, and where characterization tests and refactor safety nets are documented [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433), [GEMM Kernel Optimization](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1186895430).

A subtle but important secondary audience is **non-mathlibs stakeholders** (PMs, framework leads, AAI program owners) who mostly need high-level maps to ask the right questions and file the right tickets. For them, the summary tables in Sections 3–5 plus the contact/ownership pointers in Section 6 are the most valuable parts.

### 1.3 Usage Model: Quick Lookup vs. Guided Learning Paths

Most users will first encounter this index as a **lookup tool**: "I need to know how solution selection works for batched BF16 GEMM on MI350" or "Where is the TensileLite YAML spec for MXFP8?" In that mode, the tables in each module and the cross-module dependency diagram links are meant to provide **one-click answers**.

At the same time, for new hires or engineers rotating into GEMM work, there is value in **structured learning paths**. This index therefore suggests, implicitly, a staged path:

1. HIP basics (HIP training, textbook) → [Accelerated Computing with HIP - Textbook](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744179132), [HIP Training at AMD](https://amd.atlassian.net/wiki/spaces/LC/pages/531791935).
2. BLAS and rocBLAS background → [BLAS Introduction](https://amd.atlassian.net/wiki/spaces/aialgo/pages/625983547), [rocBLAS](https://amd.atlassian.net/wiki/spaces/GPUCPT/pages/624593758).
3. hipBLASLt concept + API → [LDEF-00011: What is HIPBLASLt](https://amd.atlassian.net/wiki/spaces/SSET/pages/805805654), [Understanding hipBLASLt](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196486).
4. Bench and basic tuning → hipblaslt-bench docs and intro tuning pages [How to install and run hipblaslt-bench](https://amd.atlassian.net/wiki/spaces/~marslin2/pages/1652834745), [hipBLASLt - how to tune](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744185533).
5. Deeper solution selection & TensileLite codegen.

An original design principle is that **each module supports both styles**: its subsections start with overview/positioning paragraphs, then go into link-dense, task-oriented details. That balances readability with the need to surface a large amount of tribal knowledge.

### 1.4 Structure Overview: Three Modules + Shared Infrastructure

The rest of the document is organized as follows:

* **Section 2 – Common Metadata & Conventions**: How every resource entry is tagged and described (title, owner, ROCm version, audience level, topic tags, link hygiene). This is crucial if we want the index to stay maintainable over time.
* **Section 3 – Module A: hipBLASLt Basics**: Concept, architecture, onboarding, API usage, and intro-level performance guidance.
* **Section 4 – Module B: Solution Selection**: Algorithms and heuristics (equality, grid, StreamK, Origami, Formocast), tuning workflows (hipblaslt-bench, GEKO, bench-driven swaps), and debugging patterns.
* **Section 5 – Module C: TensileLite Code Generation**: Roles, YAML and codegen pipeline, tuning methodologies, and how to extend or debug codegen.
* **Section 6 – Cross-Module Navigation & Index Page**: How to assemble these modules into a single Confluence index page and keep it healthy.
* **Section 7 – Conclusion**: Key recommendations and the single most important habit for teams: treat GEMM (hipblasLt) as your entry point and keep tuning and selection changes visible there.

### 1.5 Onboarding: HR, Access, and Foundational Links

Before anyone can use the technical resources in this index, they must clear basic HR and access hurdles. The **HIPBLASLT Onboarding** page covers TechProtect groups, GitHub permissions, and the standard "clone → build → test" workflow on the Alola cluster, including an example Slurm+container invocation and a build line like:

```shell
cd rocm-libraries/projects/hipblaslt
./install.sh -c -a gfx942 --skip-rocroller
```

with the note to **expect ~75–85 minutes** for the initial build due to TensileLite kernel generation [HIPBLASLT Onboarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1711090025).

For broader AGS/MLSE onboarding—including HR tasks, access to HIP courses, and general ROCm learning—the **Onboarding – AGS Libraries** and **Onboarding & Learning** pages should be treated as prerequisites. They point to HIP training, architecture whitepapers, and internal learning portals that underpin everything in hipBLASLt and TensileLite [Onboarding - AGS Libraries](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744162755), [Onboarding & Learning](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744183858).

A subtle but practical insight is that **matching TechProtect groups to a colleague** (as suggested on the HIPBLASLT Onboarding page) is often far faster than ad-hoc access requests. Encoding that trick explicitly in the index helps new hires avoid days of blocked progress due to missing permissions.

---

## 2. Common Metadata & Conventions

### 2.1 Standard Metadata Fields

To keep the index maintainable and searchable, every resource entry should carry standard metadata. The table below summarizes the fields and how they are used in this report and the intended Confluence index page:

| Field | Description / Usage |
| --- | --- |
| **Title** | Exact Confluence or doc title; used as the display name and for link text. |
| **Owner / Team** | Current maintainer or primary POC; often mapped from component owner lists [List of Component owners for mathlibs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1363903581). |
| **Source System** | Confluence, GitHub, SharePoint, internal training portal, dashboard, etc. |
| **ROCm / HW Version Range** | Known good version span (e.g., "ROCm 7.1–7.3, gfx942/gfx950"), or "conceptual" if version-agnostic. |
| **Last Updated / Review Cadence** | Last modified timestamp plus an informal "review every N months" guideline. |
| **Intended Audience Level** | Intro, intermediate, advanced; used to filter views and recommend learning paths. |
| **Topic Tags** | API, performance, architecture, codegen, debugging, tuning, etc. |
| **Component Tags** | hipBLASLt, TensileLite, rocBLAS, MIOpen, CK, AITER, etc. |

Many of these fields can be inferred automatically from Confluence metadata (last update, author, space) and GitHub commit history. The constraint—and a key recommendation—is that **audience level and topic/component tags must be curated**, not auto-guessed, because they define how new engineers discover content.

An original suggestion for maintainers is to maintain these metadata **as a small table at the top of each module page** (hipBLASLt basics, solution selection, TensileLite). Confluence macros can then pull those into a global index, reducing duplication and drift.

### 2.2 Tagging / Taxonomy

Given the breadth of GEMM work, tagging is the only way to make this index scale. A minimal but effective taxonomy would include:

* **Topics**:

    * **API** – public hipBLASLt functions, descriptors, and sample code [hipBLASLt API reference](https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/api-reference.html).
    * **Performance** – tuning, benchmarking, heuristics, OOB vs tuned metrics [hipBLASLt - how to benchmark](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744185491).
    * **Architecture** – design overviews, control flows, and stack diagrams [Understanding hipBLASLt](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196486).
    * **Codegen** – TensileLite internals, YAML, snippet, StinkyTofu [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433).
    * **Debugging** – triage guides, coredump analyses, logging knobs [rocBLAS GEMM Triaging and Debugging Guide](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1496374640).
    * **Tuning** – hipblaslt-bench auto-tuning, GEKO, TensileLite tuning demos [GEMM Kernel Optimization](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1186895430), [Tensile tuning demo and documentation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744168348).

* **Components**:

    * **hipBLASLt**, **TensileLite**, **rocBLAS**, **Tensile**, **rocRoller**, **Origami**, **Formocast**, **StinkyTofu**, **GEKO**.
    * Cross-stack items like **AITER**, **CK**, **vLLM** tags are useful when GEMM tuning touches frameworks.

The non-obvious but important point is that tags should reflect **how people search**, not just how we think about the architecture. For example, adding a **"MXFP4"** or **"FP8"** tag to docs about TensileLite MX kernels or hipBLASLt epilogue extensions drastically lowers friction for inference teams, who might not know whether they need to look under "codegen" or "solution selection" [hipBLASLt User Feedback](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1706234950).

### 2.3 Link Hygiene and Maintenance

Robust link hygiene is critical because many performance and tuning docs get cloned, re-versioned, and moved between spaces. Recommended practices include:

* Prefer **Confluence page permalinks** over short URLs when embedding links in this index.
* For GitHub content, always pin to **branch + path** (e.g., `rocm-libraries/tree/develop/projects/hipblaslt/tensilelite`) not raw commit hashes, but reference PR IDs in the linked Confluence page for historical context [Kernel Generator: TensileLite](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119).
* Avoid linking directly to generated artifacts (e.g., `.dat` libraries, `.co` files). Instead, link to the docs that explain **how to regenerate them** (TensileLite, GEKO, bench-driven swap workflows).
* For links that are known to drift (e.g., SharePoint decks under team drives), add a brief "How to rediscover this" note, often via the GEMM (hipblasLt) hub or GEMM Programs Status page [GEMM Programs Status](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1662987250).

A concrete maintenance mechanism is to designate a **single contact alias** for broken links and missing docs—often the GEMM optimization team or mathlibs doc POC—so that individual engineers are not left guessing whom to ping.

### 2.4 Canonical Resource Mapping

For hipBLASLt and GEMM, there is already an implicit canonical hub: **GEMM (hipblasLt)** in the MLSE space. That page aggregates program status, offsite decks, GEMM kernel generators, and links to hipBLASLt, TensileLite, and other kernel-generation ecosystems [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159).

This index treats that page as the **root landing page** for all three modules and recommends that any new major GEMM initiative (e.g., MI455 AAI Day, MXFP4 inference enablement) be wired into it. That way:

* The hipBLASLt basics module can simply say "start from GEMM (hipblasLt) → Module A."
* Solution-selection RFCs (Formocast, Origami changes) are surfaced to everyone, not buried in isolated spaces.
* TensileLite roadmap and characterization tests have a discoverable, cross-team home.

The key idea is that **we do not need yet another canonical page**—we need a curated view on top of GEMM (hipblasLt), which this document provides.

---

## 3. Module A: hipBLASLt Basics

### A.1 Overview & Positioning

hipBLASLt is AMD's **HIP-based BLAS-like GEMM library**, designed as a flexible, high-performance counterpart to NVIDIA's cuBLASLt. It focuses purely on GEMM-style operations but adds rich **epilogue fusion** (bias, activation, scaling, softmax, layernorm, etc.) and **mixed-precision support** beyond traditional BLAS [LDEF-00011: What is HIPBLASLt](https://amd.atlassian.net/wiki/spaces/SSET/pages/805805654), [HipBLASLt Tools](https://amd.atlassian.net/wiki/spaces/aialgo/pages/626004645).

Positionally, hipBLASLt sits **beside rocBLAS**: rocBLAS implements the standard BLAS 1/2/3 APIs and still serves many HPC workloads, but increasingly **delegates GEMM to hipBLASLt** on newer architectures such as gfx942/gfx950, especially for AI datatypes and fused operations [GEMM (and hipBLASLt/rocBLAS) FAQs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744195234). hipBLASLt is the library that frameworks and routing layers (AITER, CK, Triton routers) rely on when they want best-in-class GEMM performance with fusion possibilities [hipBLASLt User Feedback](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1706234950).

A useful mental model is:

| Library | Analogue | Focus |
| --- | --- | --- |
| **rocBLAS** | cuBLAS | Standard BLAS API, HPC GEMM, legacy BLAS |
| **hipBLASLt** | cuBLASLt | AI-focused GEMM, mixed precision, fusion |
| **CK / others** | custom kernels | Specialized ops (attention, conv, MoE) |

The original insight from internal feedback is that **hipBLASLt's limiting factor is not raw GEMM performance**—for BF16 training workloads it is already considered a "gold standard" [hipBLASLt User Feedback](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1706234950). The gaps tend to be around **low-precision datatypes, fusion coverage, and usability** (tuning stability, release cadence). That is why this module emphasizes not just API docs but also performance best practices and tooling.

Key concept and architecture docs:

| Resource | Role |
| --- | --- |
| [LDEF-00011: What is HIPBLASLt](https://amd.atlassian.net/wiki/spaces/SSET/pages/805805654) | High-level purpose, features, and use cases. |
| [Understanding hipBLASLt](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196486) | Control flow and architecture from API to kernels. |
| [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159) | Canonical GEMM hub linking to design, tuning, generators. |

### A.2 Core Concepts & Architecture

At the API level, hipBLASLt exposes **handles, descriptors, and operations** similar to cuBLASLt: you create a handle, build matrix and operation descriptors (data types, layouts, epilogues), and then call `hipblasLtMatmul()` with those descriptors and data pointers [hipBLASLt API reference](https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/api-reference.html). This indirection allows it to pack a large space of GEMM variants into a small, stable public API surface.

Supported **data types** span FP64/FP32/FP16/BF16, INT8, and newer FP8/MXFPx family formats, with **mixed-precision compute** (e.g., FP8 inputs with FP32 accumulation and various output types). Internal tools and docs, such as HipBLASLt Tools and the GEMM hub, explicitly document which (A,B,C,D,compute) combinations are supported and how they map to actual kernels [HipBLASLt Tools](https://amd.atlassian.net/wiki/spaces/aialgo/pages/626004645), [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159).

Architecturally, the call stack is:

> Application → hipBLASLt front-end (API + descriptors) → solution selection logic → **TensileLite / rocRoller / custom kernels** → GPU kernels

with hipBLASLt caching kernel "solutions" to avoid re-selecting for repeated shapes [Understanding hipBLASLt](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196486). On modern parts (MI300/MI350, gfx12), **TensileLite is the primary backend** for dense and structured sparsity GEMM, while rocRoller is used mainly for certain MX datatypes, and custom kernels or CK/Triton occasionally bypass the usual path via "GEMM from anywhere" integrations [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159), [Hipblaslt-kernel-from-anywhere](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1403547193).

A non-obvious consequence of this layered design is that **performance debugging is naturally split**:

* If the wrong kernel is picked or performance is unstable across builds → look at **solution selection** (Module B).
* If no kernel exists or all candidates are slow → look at **TensileLite kernel pool** and tuning (Module C).
* If overhead dominates (e.g., batched GEMM with slow host setup) → focus on **hipBLASLt front-end and caching** [Rocblas/hipblasLt Batched GEMM Performance](https://amd.atlassian.net/wiki/spaces/DCGPUAIST/pages/1099690121).

### A.3 Getting Started & Onboarding

For someone new to hipBLASLt, there are two parallel tracks: **system setup & build**, and **conceptual learning**.

On the setup side, **HIPBLASLT Onboarding** and **Initial Setup** provide detailed steps:

* Clone via ROCm monorepo or direct hipBLASLt repo.
* Use sparse checkout to include only required projects (hipblaslt, hipblas-common, shared/origami, shared/mxdatagenerator, shared/stinkytofu) to save disk and build time [HIPBLASLT Onboarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1711090025).
* Build with `./install.sh -dc -a <arch>` (or `-idc` the first time to include dependencies) and remember to **specify the architecture** (gfx942/gfx950/etc.) to avoid multi-arch builds that can take >1 hour and consume significant disk [Initial Setup](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744197146).

On clusters like **Alola**, the HIPBLASLT Onboarding doc shows how to submit Slurm jobs with correct containers, CPU-only build nodes, and mounted home/scratch directories. It stresses avoiding builds on login nodes and explains that **TensileLite kernel generation is long and mostly silent**, which often surprises newcomers [Building and Benchmarking hipblaslt on Slurm Cluster](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1615927411).

On the learning side, **Onboarding & Learning**, the **HIP Training at AMD** hub, and the **Accelerated Computing with HIP** textbook provide the necessary HIP, ROCm, and GPU architecture background. A particularly effective pattern is to pair a HIP course (HIP 100/200/300 levels) with hands-on tasks from the GEMM optimization team's onboarding checklists—clone hipBLASLt, build it, run hipblaslt-bench, and try a small TensileLite tuning job [HIP Training at AMD](https://amd.atlassian.net/wiki/spaces/LC/pages/531791935), [GEMM Optimization Team On-Boarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196538).

From an original best-practice standpoint, teams should **treat the first end-to-end build as a training asset**, not just a gate: capture the exact commands and environment variables that worked (including ROCm version, container image, and GPU arch) and save them alongside this index, so new hires can reproduce success instead of debugging environment differences.

### A.4 API Reference & Usage Patterns

The primary reference for hipBLASLt APIs is the public **hipBLASLt API reference** hosted in ROCm docs. It documents descriptors, matmul operations, and epilogue options, together with C and C++ bindings [hipBLASLt API reference](https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/api-reference.html). Internally, **Understanding hipBLASLt** complements this by walking through a concrete C++ sample (`sample_hipblaslt_gemm.cpp`) and explaining how descriptors and operations translate into kernel selection and launch.

Core usage pattern:

1. Create a `hipblasLtHandle_t`.
2. Create matrix descriptors for A, B, C, D with layout, strides, datatypes.
3. Create a matmul descriptor capturing transposes, compute type, and epilogues (bias, activation, scaling).
4. Optionally query heuristics or run an auto-tuning pass.
5. Call `hipblasLtMatmul()`.

HipBLASLt supports a large variety of **fused epilogues**, including bias, GELU, ReLU, Swish, clamp, and backward-pass variants such as DGELU and BGRAD [HipBLASLt Tools](https://amd.atlassian.net/wiki/spaces/aialgo/pages/626004645). Comparison tables between hipBLASLt and cuBLASLt epilogues exist in internal docs and show near-parity with a few extensions (e.g., certain training backward ops).

An important original recommendation is to **view epilogues as scheduling hints** as much as mathematical ones: using a fused bias or activation not only saves memory bandwidth but also **selects a different solution family** in the backend, which may have different tuning characteristics. That is why epilogue-heavy workloads often need separate tuning or bench-driven swaps compared to "plain GEMM" of the same dimensions.

### A.5 Performance & Best Practices (Intro Level)

Intro-level performance tuning for hipBLASLt focuses on **input shaping and configuration hygiene** rather than kernel internals:

* Match leading dimensions and strides to enable coalesced access and avoid pathological padding.
* Use recommended matrix dimensions and batches when possible; extremely skinny or small matrices rely heavily on equality tuning and may not be well-covered by default grids.
* Turn on `--print_kernel_info` in hipblaslt-bench to see which solution and kernel are being used, and watch for unexpected solution index churn [HipBLASlt GEMM kernel benchmark](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196818).

The **hipBLASLt – how to benchmark** and multiple hipblaslt-bench guides show how to run stable benchmarks, control iterations and warm-ups, and collect frequency information via `HIPBLASLT_BENCH_FREQ` env vars [hipBLASLt - how to benchmark](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744185491), [How to install and run hipblaslt-bench](https://amd.atlassian.net/wiki/spaces/~marslin2/pages/1652834745). These basics are prerequisites before diving into more sophisticated tools like **hipBLT-board**, which wraps TuningDriver, benchmarks, and reporting into a single Dash application [hipBLT-board - System Overview & Usage Guide](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1673435092).

Finally, the **hipBLASlt Startup Guide into Profiling, Debugging and Optimization** ties together hipBLASLt workloads with ROCm profiling tools (rocprof, ROCm Compute Viewer) and suggests an incremental workflow: validate API correctness, confirm solution selection behavior, then use profilers and ISA inspection only after the first two are understood [hipBLASlt - a Startup Guide into Profiling, Debugging and Optimization](https://amd.atlassian.net/wiki/spaces/RCPT/pages/1179073633).

An original insight here is that **80% of "hipBLASLt is slow" tickets stem from either mis-shaped inputs or solution-selection artifacts**, not codegen. So for new engineers, the best ROI is to master hipblaslt-bench (including YAML-driven runs) and the logging knobs before attempting any TensileLite tuning.

---

## 4. Module B: hipBLASLt Solution Selection

### B.1 Conceptual Overview

A **solution** in hipBLASLt is a complete kernel configuration—macro tile sizes, wave sizes, unroll depth, instruction variant, LDS usage, and scheduling parameters. **Solution selection** is the process of mapping a runtime GEMM problem `(M,N,B,K, datatypes, layout, epilogue)` to one of these solutions in the library.

The core algorithm, as summarized in the GEMM FAQs and solution-selection design doc, is **two-level**:

1. **Equality lookup** – Search the **Equality** libraries for an exact match on M, N, K (and other parameters). If found, launch that kernel.
2. **Grid-based fallback** – If no exact match exists, search a **grid of representative sizes** and choose the closest grid point based on heuristics, then use its solution [GEMM (and hipBLASLt/rocBLAS) FAQs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744195234), [Solution selection](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744176549).

Additional solution families—**StreamK**, **Origami**, **Formocast**—behave as specialized heuristics or search spaces layered on top of this equality+grid foundation. For example, StreamK requires enabling an env var and targets concurrency-friendly scheduling; Origami and Formocast use learned or simulation-based models to refine grid selection [GEMM HEURISTICS](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744198388), [Formocast Design Document (RFC)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304232451).

Conceptually, this pipeline has a clear trade-off:

* **Equality** maximizes performance but demands tuning for every size.
* **Grid-based** drastically reduces tuning cost by selecting a small representative set whose kernels generalize over nearby sizes, with evidence that **average efficiency vs exhaustively tuned libraries is within ~1–2%, max gap ~15%** on MI100/MI200 and similar on newer GPUs [Solution selection](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744176549), [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159).

An original takeaway is that most performance engineering now revolves around **curating and improving these heuristics and grids**—including Formocast and bench-driven re-tuning—rather than hand-adding equality kernels for every size.

### B.2 Internal Design & Algorithms

The **Solution selection** page and GEMM HEURISTICS doc detail how equality and grid libraries are structured, how lookups are performed (often with binary search in sorted tables), and what metrics are recorded for each solution [Solution selection](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744176549), [GEMM HEURISTICS](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744198388). Solution selection metrics docs define **efficiency vs ideal**, stability of chosen solution, and comparison vs competitor hardware [Solution Selection Metrics](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744174730).

Heuristics such as **Origami** and **Formocast** operate on top of TensileLite's solution pool. Origami uses structured heuristics and search to select good solutions; Formocast goes further, using simulation-based performance modeling to predict performance of candidate kernels without exhaustive benchmarking [Difference between Origami and Formocast](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304199634), [Formocast Design Document (RFC)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304232451).

Crucially, **solution-selection quality is now itself a subject of benchmarking**, with dedicated dashboards and comparison tools that:

* Sweep GEMM sizes and measure FLOPS for the selected solution.
* Compare against ideal (best of all available solutions) and competitor libraries.
* Track selection efficiency and highlight outliers [Dashboard: hipBLASLt GEMM Tuning](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1045306155).

An original observation from recent work is that heuristic limits show up most clearly at **medium-sized GEMMs** where there is enough work to expose kernel differences but not enough to amortize all overheads. The ROCm-CUTLASS benchmark on MI300X, for example, shows that runtime search over multiple hipBLASLt algorithms can improve performance by up to **1.88×** at size 1024³ compared to the default heuristic pick [ROCm-CUTLASS Benchmark Results — AMD MI300X (2026-06-04)](https://amd.atlassian.net/wiki/spaces/DCGPUAIST/pages/1718303144). That underscores the value of continued work on heuristics (Origami/Formocast) and bench-driven reselection.

### B.3 Tuning Workflow & Tools

hipBLASLt solution selection is supported by a rich ecosystem of tuning tools:

* **hipblaslt-bench auto-tuning** – The "how to run hipblaslt-bench auto-tuning tool" doc explains how to explore all available solutions for a given shape (or shapes from a YAML), measure performance, and export results [hipBLASLt - how to run hipblaslt-bench auto-tuning tool](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744185063).
* **hipBLASLt – how to tune** and **hipBLASLt GEMM Tuning Steps Using Tensile** describe step-by-step workflows: pick GEMM shapes, run TensileLite tuning, merge new logic libraries, rebuild hipBLASLt, and re-benchmark [hipBLASLt - how to tune](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744185533), [hipBLASLt GEMM Tuning Steps Using Tensile](https://amd.atlassian.net/wiki/spaces/~kangwang/pages/914331845).
* **GEKO (GEMM Kernel Optimization)** – A higher-level Python package that orchestrates TensileLite tuning, benchmark analysis, and library integration via GA-based and dense search flows. It takes hipBLASLt logs, generates TensileLite configuration YAMLs, runs tuning (grid or GA search), and merges the resulting libraries back into hipBLASLt [GEMM Kernel Optimization](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1186895430).
* **hipBLT-board** – A Dash web app that unifies benchmarking, tuning entry points, and metadata for hipBLASLt. It integrates with TuningDriver, GEKO, and a MySQL catalog, letting users go from HIP logs to tuned solutions and reports via a single UI [hipBLT-board - System Overview & Usage Guide](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1673435092).
* **Bench-driven swap workflow** – When the kernel pool is adequate but grid-based picks are stale, the **hipBLASLt GridBased re-tuning: bench-driven swap workflow** allows you to systematically benchmark alternatives for each grid point and swap in winners in the YAML grid tables without regenerating kernels [hipBLASLt GridBased re-tuning: bench-driven swap workflow](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1710204999).

An original tuning strategy emerging from these tools is:

1. **Start with dense search over existing solutions** (GEKO search or hipblaslt-bench `--algo_method all`) to ensure the solution pool is well-used for your workload.
2. Use **bench-driven swap** to update grids when dense search shows systematic under-utilization (e.g., grid points consistently picking non-optimal solutions).
3. Only if performance is still insufficient, invest in **TensileLite tuning** to expand the solution pool (Module C).

This staged approach is much cheaper than jumping straight into kernel generation and avoids some common pitfalls (e.g., spending days tuning kernels that the equality libraries will never hit).

### B.4 Debugging & Analysis

When GEMM performance or correctness is off, there are several complementary debug pathways:

* **See which solution was picked** – Use `hipblaslt-bench --print_kernel_info` (and `HIPBLASLT_LOG_MASK=64` with `HIPBLASLT_LOG_FILE`) to see the solution index, kernel name, and parameters. The GEMM FAQs explain how equality/grid libraries are organized and how to interpret solution indices [GEMM (and hipBLASLt/rocBLAS) FAQs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744195234).
* **Bridge from rocBLAS to hipBLASLt** – The rocBLAS GEMM triage guide shows how to use `ROCBLAS_LAYER` and other env vars to capture which backend (Tensile vs hipBLASLt) was used and how to reproduce the same GEMM via hipblaslt-bench for deeper analysis [rocBLAS GEMM Triaging and Debugging Guide](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1496374640).
* **Persist tuned solution maps** – The **Persisting hipblaslt-bench and tunableop solution maps** doc shows how to turn per-shape winner data (from hipblaslt-bench or tunableops) into solution maps that can be merged into hipBLASLt's libraries, making tuned choices persistent across builds [Persisting hipblaslt-bench and tunableop solution maps](https://amd.atlassian.net/wiki/spaces/DCGPUAIST/pages/889321543).
* **Force a specific solution** – When you know the ideal solution index, **How to build rocblas/hipblaslt with the specific solution found by user driven** explains how to add mappings directly into YAML logic files and rebuild the library so the desired solution is hard-wired for certain shapes [How to build rocblas/hipblaslt with the specific solution found by user driven](https://amd.atlassian.net/wiki/spaces/DCGPUAIST/pages/680803767).

An original best-practice is to treat **solution index instability** as a first-class problem: hipBLASLt user-feedback documents note that changing solution indices across builds breaks stored tuning results and complicates integration with routers like AITER [hipBLASLt User Feedback](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1706234950). Therefore, when working on heuristics or library merges, engineers should verify stability using logs and characterization tests, not just performance metrics.

### B.5 Cross-Component Dependencies

Solution selection is only as good as the **kernel pool** and the **selection logic** connected to it. Cross-component dependencies include:

* **TensileLite** – The primary source of GEMM solutions. Any missing kernels, data type gaps, or mis-tuned kernel parameters show up upstream as "no solution" or poor performance for certain shapes [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433).
* **Origami & Formocast** – Integrated into the solution-selection stack for enhanced grid predictions and simulation-based performance estimates; both rely on TensileLite's solution semantics and benchmarking infrastructure [Difference between Origami and Formocast](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304199634), [Formocast Design Document (RFC)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304232451).
* **rocBLAS integration** – The rocBLAS→hipBLASLt integration plan explicitly describes how rocBLAS will call hipBLASLt for complex GEMM and how solution selection must be kept consistent for those calls [hipBLASLt rocBLAS integration Planning](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196689).

Ownership and SME references are crucial for this layer:

* The **mathlibs component owner list** identifies POCs for hipBLASLt, TensileLite, GEMM tuning, and rocRoller [List of Component owners for mathlibs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1363903581).
* The **Shift-Left – Roles/Responsibilities** page maps ROCm components to Dev, QA, and DevOps SMEs in TheRock CI, which is increasingly important now that TensileLite and solution selection logic are tested as part of unified builds [Shift-Left - Roles/Responsibilities](https://amd.atlassian.net/wiki/spaces/SHARK/pages/1382516837).

An original recommendation is to explicitly document **ownership boundaries** in the central index: for example, "hipBLASLt solution selection heuristics: contact GEMM optimization team; TensileLite kernel generation parameters: contact TensileLite developers," and link to the process-improvement and program-status pages that already encode much of this [Process improvements](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1092380686), [GEMM Active Programs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1387220065).

---

## 5. Module C: TensileLite Code Generation

### C.1 Role of TensileLite

**TensileLite** is the modern, lightweight GEMM kernel generator and runtime library embedded within hipBLASLt (and hipSPARSELt). It evolved from the original Tensile project, with a focus on:

* Tighter integration with "Lt" libraries (hipBLASLt, hipSPARSELt).
* Support for **fusion** (bias, activation, reduction, softmax, layernorm, etc.).
* Mixed-precision and newer **MXFP4/6/8** and FP8 data types [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433), [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159).

The **Tensile Overview** page clarifies the relationship between Tensile, TensileLite, and ArchGEMM, and notes that **TensileLite is now the active development focus**, with Tensile relegated to legacy hardware and certain problem types [Tensile Overview](https://amd.atlassian.net/wiki/spaces/~stebrown/pages/1364192827). For newer architectures, even rocBLAS often accesses GEMMs generated by TensileLite via hipBLASLt.

Functionally, TensileLite plays two roles:

1. **Code generator** – Given a problem spec and parameter ranges (YAML), generate candidate kernels, compile them, run benchmarks, and emit **code objects + solution logic**.
2. **Runtime library** – At hipBLASLt runtime, load solution logic and code objects, and respond to solution-selection queries with kernel launch parameters [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433).

This split is critical: most developers interact with the runtime implicitly via hipBLASLt; only kernel developers and tuners need to touch the codegen phase. This module is aimed at that latter group.

### C.2 Codegen Pipeline Overview

The high-level pipeline is:

1. **Inputs** – YAML configuration describing:

    * Problem types (GEMM, layouts, data types, epilogues).
    * Parameter grids (MacroTile, DepthU, MatrixInstruction, WorkGroupMapping, Prefetch, etc.).
    * Benchmark problem sizes (M,N,B,K ranges).

2. **TensileLite main** – Parses YAML, fills defaults from GlobalParameters and ValidParameters Python modules, generates candidate solutions, figures out which parameter combinations are valid, and optionally creates a tuning schedule [Kernel Generator: TensileLite](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119).
3. **Code generation** – Use `rocisa` (and increasingly **StinkyTofu**) to generate assembly for each candidate solution, compiling into **code objects**.
4. **Benchmarking** – Launch kernels on target GPUs (or FFM simulator) using the TensileLite client, record GFLOPS and other metrics.
5. **Solution library creation** – Emit YAML logic libraries summarizing which solution is best for each problem or grid point.
6. **Integration** – hipBLASLt build uses TensileCreateLibrary to convert logic YAMLs into binary libraries and integrate them into the build [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433), [Extending Tensilelite Code Generator Support for Complex Datatypes](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1325571391).

On modern roadmaps, this pipeline is being further refactored:

* **Snippet architecture** – A restructured codegen architecture based on typed, composable "snippets" of instructions, with per-architecture packages and functional models [TensileLite Snippet Architecture](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1643646497), [Snippet Architecture: Vision and Goals](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1643344006).
* **StinkyTofu** – A pass-based IR optimizer (logical and ASM IR) that performs DAG scheduling, waitcnt insertion, peephole optimizations, and more on TensileLite-emitted kernels [StinkyTofu Development](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1259089125), [ROCm](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1451494995).

An original insight is that these refactors are not "nice to have" but necessary to make the codebase **agent- and human-tractable**: the legacy KernelWriterAssembly was a 14k-line monolith with heavy shared state, making reasoning and refactoring extremely difficult [Snippet Architecture: Vision and Goals](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1643344006). The snippet+StinkyTofu direction enables safer, test-driven evolution of codegen.

### C.3 Configuration & Templates

TensileLite YAML files are the primary user interface for kernel tuning and generation. Several docs and decks serve as guides:

* **tensilelite yaml config for Kernel A–E (draft)** – Concrete examples for MXFP4/MXFP8 kernels, showing MatrixInstruction, DepthU, SourceSwap, Prefetch, and other parameters for specific kernel families (MAF, OpenAI GEMMs, Meta small-K) [tensilelite yaml config for Kernel A-E (draft)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1732654216).
* **MI300 Tensile Kernel Generation Parameters Overview** – A slide deck walking through key parameters (MacroTile, DepthU, VectorWidths, StaggerU, PrefetchLocalRead, LDS settings) and typical ranges, with explicit guidance like "PLR=1 is usually fine for TensileLite, but try 2+ for some configs" [MI300_tensilelite_Tensile_Kernel_Generation_Parameters_Overview_v1.1.pptx](https://amd.atlassian.net/wiki/pages/viewpageattachments.action?pageId=744192975&preview=%2F744192975%2F745281680%2FMI300_tensilelite_Tensile_Kernel_Generation_Parameters_Overview_v1.1.pptx).
* **Kernel Generator: TensileLite** – Documents GlobalParameters and ValidParameters, including typical values for performance tuning knobs like PerformanceMetric, NumWarmups, SkipSlowSolutionRatio, and EnqueuesPerSync [Kernel Generator: TensileLite](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119).

Naming conventions embed the full configuration into deterministic kernel names, e.g.:

`Cijk_Alik_Bljk_HHS_BH_HA_S_SAV_UserArgs_MT128x96x64_MI16x16x1_SN_..._WG64_2_1_...`

where fragments like `MT128x96x64`, `MI16x16x1`, `WG64_2_1`, `PGR2`, `PLR1`, and `ISA1150` encode macro tile size, MFMA instruction, workgroup, prefetch depths, and target ISA [Kernel Generator: TensileLite](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119). This makes it possible to reverse-engineer YAML parameters from a kernel name and is heavily used in workflows that tune or fix individual kernels.

A key original guideline for authoring YAMLs is:

* Start from **reference configs** (Kernel A–E docs, per-arch fork parameters in GEKO) instead of writing from scratch.
* Avoid over-expanding parameter grids; each additional axis may produce hundreds of candidate kernels, many of which exceed register or LDS limits and are ultimately discarded [Kernel Generator: TensileLite](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119).
* Document why a parameter range was chosen (e.g., "StaggerU=[0,32] for NT, [0,4] for NN/TN/TT"), ideally in comments or a companion Confluence page, to make future maintenance easier [MI300_tensilelite_Tensile_Kernel_Generation_Parameters_Overview_v1.1.pptx](https://amd.atlassian.net/wiki/pages/viewpageattachments.action?pageId=744192975&preview=%2F744192975%2F745281680%2FMI300_tensilelite_Tensile_Kernel_Generation_Parameters_Overview_v1.1.pptx).

### C.4 Tuning & Optimization

Tuning TensileLite involves exploring parameter grids and selecting the best candidates. The **Tensile tuning demo and documentation** page provides a general demonstration, while **General Usage for TensileLite Tuning** offers concrete steps and commands for running tuning jobs and rebuilding hipBLASLt with the resulting libraries [Tensile tuning demo and documentation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744168348), [General Usage for TensileLite Tuning](https://amd.atlassian.net/wiki/spaces/~geotseng/pages/389678194).

High-level tuning methodology:

1. **Define workloads** – Use hipBLASLt logs (HIPBLASLT_LOG_MASK=64) to collect real GEMM shapes from target models [GEMM Optimization Team On-Boarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196538).
2. **Generate configs** – Use config generators (in GEKO or TensileLite utilities) to produce YAMLs that cover relevant shapes and reasonable parameter grids.
3. **Run tuning** – Launch TensileLite tuning jobs across GPUs (often multi-GPU parallelized). Be prepared for expected "errors" such as kernels exceeding VGPR or LDS limits, which are legitimate filters rather than failures [Tensilelite Benchmark Execution](https://amd.atlassian.net/wiki/spaces/SHARK/pages/1405167566).
4. **Analyze and integrate** – Extract winners, generate equality and/or grid-based libraries, and merge them into hipBLASLt via TensileMergeLibrary and rebuild [GEMM Kernel Optimization](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1186895430).

The **TensileLite Characterization Tests** are a critical part of de-risking tuning and refactors: 99 `.ambr` golden files capture current behavior across ~29 modules (codegen, configuration, solution derivation). Any PR that changes behavior without updating the affected golden fails the required CI gate. This means tuning changes must pass both performance criteria and characterization tests, ensuring we do not regress hidden behavior [TensileLite Characterization Tests — Overview & Snapshot Governance](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1755647079).

An original strategic recommendation is to **separate "optimization tuning" from "coverage tuning"**:

* For hot model shapes on a given platform, you can afford aggressive GA searches and manual YAML tweaking.
* For broad coverage (new architectures like gfx1250/gfx1260), you want more conservative grids plus robust characterization, so you don't end up with fragile kernels that only work in narrow regimes.

### C.5 Debugging & Extending Codegen

When codegen misbehaves—wrong results, crashes, or missing kernels—there are several levels of tooling and docs:

* **Extending data types** – The complex-datatypes doc shows how to add support for new data types (complex float/double, MX types) across TensileLite main, TensileCreateLibrary, and client, including updates to rocisa, KernelArguments, and DataTypes helpers [Extending Tensilelite Code Generator Support for Complex Datatypes](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1325571391), [Support for complex datatype in hipBLASLt code generator](https://amd.atlassian.net/browse/SWDEV-543547).
* **Custom kernels** – The **Custom Kernel Integration Guide for hipBLASLt** and **Integrating a Custom Kernel into Tensile (for hipBLASLt)** describe end-to-end workflows for bringing hand-written or externally generated kernels into hipBLASLt via TensileLite libraries and equality YAMLs [Custom Kernel Integration Guide for hipBLASLt](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1732896926), [Integrating a Custom Kernel into Tensile (for hipBLASLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1524914169).
* **Debugging assembly** – Several pages illustrate how to run TensileLite clients, locate generated `.s` files, and debug them using ROCgdb. The "Getting Started with assembly kernel" homework tasks and the TensileLite page that shows ROCgdb commands are particularly helpful [Getting Started with assembly kernel - Homework Tasks](https://amd.atlassian.net/wiki/spaces/~menghung/pages/191332364), [TensileLite](https://amd.atlassian.net/wiki/spaces/~marhuang/pages/229539949).
* **Tuning errors and JIRA** – Tickets like **Tensile encountered issues when trying to conduct gemm tune** capture common tuning problems (slow grid-based tuning, rebuild failures) and their repro steps, providing a living knowledge base of pitfalls and fixes [Tensile encountered issues when trying to conduct gemm tune](https://amd.atlassian.net/browse/SWDEV-524855).

From an ownership perspective, the GEMM optimization team onboarding doc and mathlibs component owners list identify who to contact for TensileLite codegen questions and how responsibilities are split (CodeGen team vs GEMM tuning team vs Solution Selection team) [GEMM Optimization Team On-Boarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196538), [Process improvements](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1092380686).

A particularly important original takeaway is that **debugging and extending TensileLite is now constrained by characterization tests and snippet/StinkyTofu infrastructure**. This is a good thing: it forces changes to be accompanied by tests and behavior snapshots, reducing the risk that a single YAML or KernelWriter tweak silently degrades large swaths of the GEMM library.

---

## 6. Cross-Module Navigation & Index Page

### D.1 Linking the Three Modules

The three modules form a **stack**:

* **Module A (hipBLASLt basics)** lives mostly at the API and usage level, with minimal exposure to solution indices and kernels.
* **Module B (solution selection)** lives at the boundary between API and kernels, translating problem descriptions into solution indices and controlling equality vs grid vs StreamK vs Origami/Formocast.
* **Module C (TensileLite)** owns the generation and maintenance of the kernel pool that Module B selects from.

The **GEMM (hipblasLt)** page already contains a visual dependency diagram that shows hipBLASLt, rocBLAS, TensileLite, CK, rocRoller, and others. This index should simply **link prominently to that diagram** and use consistent terminology (Equality, GridBased, StreamK, etc.) [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159).

A concrete navigational pattern for the Confluence index:

* Top banner: "Start here" → GEMM (hipblasLt) + this index.
* Left column: links to **Module A/B/C pages**.
* Right column: **program status and contacts** (GEMM Active Programs, GEMM Programs Status, component owner list).

The original insight is that **engineers rarely start from a blank slate**; they arrive with a question ("Why is this GEMM slow?"). The index should be optimized for that: a small troubleshooting flowchart could link "symptom → module → specific doc," turning this index from a static library into a lightweight decision aid.

### D.2 Central Confluence Index

The central index page—likely in the MLSE space under GEMM or libraries—should be structured as:

1. **Executive summary** (one paragraph + bullets, similar to this report's Summary).
2. **Three module sections** (A/B/C) each with:

    * 3–5 most important links in a table (title, audience, last updated, purpose).
    * 1–2 paragraphs of when to use this module.

3. **Common infrastructure**:

    * GEMM (hipblasLt) hub.
    * Tuning dashboards (hipBLASLt GEMM Tuning, solution-selection metrics).
    * Onboarding and training links.

4. **Ownership & contacts** – pulled from mathlibs owner list and Shift-Left roles.

Maintenance responsibilities should fall to the **ROCm performance and GEMM optimization teams**, who already maintain many of the linked resources [GEMM Active Programs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1387220065), [ROCm Core performance](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1024656521). A light-weight process—quarterly review plus updates whenever large features land (e.g., new MX datatypes, new architectures)—is sufficient.

An original suggestion is to integrate **Confluence label queries and macros**: for example, the index can auto-list all pages tagged `hipblaslt-tuning` or `tensilelite-snippet` under a "Related Materials" section, keeping it fresh without manual curation of every minor doc.

### D.3 Future Extensions

The landscape around hipBLASLt and TensileLite is evolving quickly, with:

* New **datatypes** (MXFP4/6/8 variants, FP8, complex, structured sparsity).
* New **architectures** (gfx1250/gfx1260/MI455 and beyond).
* New **heuristics and ML-driven selection** (Formocast, genetic algorithms, ML models in Origami) [Create a genetic algorithms driven search for building solution libraries](https://amd.atlassian.net/browse/SWDEV-477426), [Formocast Design Document (RFC)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304232451).

To keep up, the index should be designed with **extension points**:

* Add new module subsections (e.g., "Mixed-precision & MX datatypes," "Graph-level GEMM pipelines") without changing the core structure.
* Capture new codegen backends or strategies (e.g., runtime codegen via compiled assets, integration with AITER, ML-based kernel generators) under the TensileLite section [WIP Compiled Assets for Runtime Code Generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1703150439), [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159).

A forward-looking original recommendation is to **treat GEMM as a cross-project platform**, not just a library: hipBLASLt, TensileLite, CK, AITER, Triton, and future codegen paths all need a shared index and shared terminology. This report can serve as the seed for that broader "GEMM platform index," starting from hipBLASLt/TensileLite and expanding as integration deepens.

---

## 7. Conclusion

Across AMD's ROCm stack, hipBLASLt, its solution-selection layer, and TensileLite codegen now form a cohesive GEMM platform: hipBLASLt exposes a flexible API with fusion and mixed precision; solution selection maps real-world problems into near-optimal kernels; and TensileLite continually improves the kernel pool and codegen infrastructure. The documentation and tools around these components are rich but historically scattered.

By organizing them into **three modular reference sections** with shared metadata, clear navigation, and explicit ownership, this report turns that scattered body of knowledge into a **usable internal platform**: engineers can onboard faster, debug more systematically, and tune performance with a clear sense of where to act (API usage, solution selection, or codegen). The strongest single recommendation is simple: **treat the GEMM (hipblasLt) page plus this index as the canonical entry point for all GEMM-related work**, and keep that hub updated whenever new heuristics, kernels, or architectures land. Doing so ensures that hard-won tuning insights and codegen advances are leveraged across teams, instead of rediscovered in isolation.

