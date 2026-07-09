# Formocast Design Document (RFC)

> **Source URL:** https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304232451/Formocast+Design+Document+RFC
> **pageId:** `1304232451`
> **Space:** MLSE (Machine Learning Software Engineering)
> **Version:** 2
> **Fetched on:** 2026-07-08 (via Atlassian Confluence MCP, `convert_to_markdown=true`)
>
> Formocast RFC 完整內容。Formocast 是 tensilelite 框架內以硬體模擬為基礎的 GEMM 效能預測模型，
> 屬 **selection 層**（不窮舉 benchmark 就預測 kernel 效能），與 Origami 的比較見
> [origami-vs-formocast.md](./origami-vs-formocast.md)。

---

## Executive Summary

Formocast is a hardware simulation-based prediction model designed to optimize the selection and performance of GEMM (General Matrix-Matrix Multiplication) algorithms within the tensilelite framework. Its primary goal is to automate and improve kernel selection for diverse hardware platforms, notably AMD's MI300/MI350 series, by simulating and predicting performance outcomes for a large pool of candidate solutions. The intended outcome is a measurable uplift in GEMM performance, streamlined integration with existing benchmarking and deployment workflows.

## Problem Statement

Current GEMM kernel selection processes are limited by static solution pools and manual tuning, which do not scale efficiently across new hardware platforms or evolving workloads. This results in suboptimal performance, duplicated engineering effort, and slow adaptation to hardware changes. The lack of a robust, simulation-driven prediction model hinders the ability to quickly identify the best-performing kernel configurations for a given problem and hardware context.

## Vision

The desired future state is an automated, extensible prediction system that:

- Rapidly evaluates and selects optimal GEMM kernels for any hardware platform.
- Seamlessly integrates with benchmarking tools (e.g., hipblaslt-bench) and deployment pipelines.
- Supports ongoing hardware evolution (e.g., MI350 features) and algorithmic innovation.
- Enables collaborative development and reduces duplicated effort between Formocast and Origami teams.

## Design / Architecture

**Key Components:**

- **Problem Dimension Calculation:** Extracts matrix dimensions and data type from user input.
- **Hardware Parameter Extraction:** Gathers platform-specific parameters (e.g., NumCUs, cache sizes, bandwidths) from APIs and static definitions. Supports extensibility for new platforms.
- **Solution Pool Management:** Maintains a diverse set of tensilelite GEMM kernels, including combinations not present in legacy pools (e.g., CMS/DTL).
- **Performance Simulation:** Models kernel execution, breaking down costs (initialization, prefetch, loop, tail loop, LSU, GSU, store, etc.) and simulates issued cycles using hardware and algorithm parameters.
- **Selection Logic:** Chooses one or several solutions with the best predicted performance for each problem instance.
- **Integration Layer:** Interfaces with benchmarking tools and deployment scripts (e.g., YAML generation for hipblaslt-bench).

**Interactions:**

- User or automated workflow submits a GEMM problem.
- Formocast extracts problem and hardware parameters.
- Simulates performance for all candidate kernels.
- Selects and outputs the optimal solution(s) for deployment or benchmarking.

## Execution Plan

**Steps:**

1. **Finalize Model Specification:** Document all required hardware and algorithm parameters.
2. **Develop Simulation Engine:** Implement and validate the performance breakdown and prediction logic.
3. **Expand Solution Pool:** Integrate additional kernel combinations and scheduling strategies.
4. **Integrate with Benchmarking Tools:** Enable Formocast to be called from hipblaslt-bench and other relevant workflows.
5. **Collaborative Review:** Coordinate with Origami and evaluation committee to align features and avoid duplication.
6. **Documentation and Training:** Prepare design docs, user guides, and onboarding materials.
7. **Deployment and Verification:** Roll out to production environments and validate with real workloads.

**Timeline:** Initial benchmarking and integration targeted for EOD 11/21/25, with ongoing feature expansion and collaborative review.

**Resources Required:**

- Engineering time for model development and integration.
- Access to hardware platforms (MI300/MI350).
- Collaboration with Origami team and evaluation committee.

## Risks / Unknowns

- **Hardware Evolution:** New platforms may require updates to parameter extraction and simulation logic.
- **Model Accuracy:** Prediction accuracy depends on completeness of hardware and kernel modeling; ongoing validation required.
- **Integration Complexity:** Merging Formocast and Origami may encounter architectural or workflow conflicts.
- **Resource Constraints:** Limited engineering bandwidth and expertise for MI350 features.
- **Unknown Unknowns:** Unforeseen technical or organizational challenges in new tensilelite features, new HW features and deployment.

## Background

Formocast builds on prior work in simulation-based performance modeling for GEMM algorithms, leveraging lessons from both internal and external research. It addresses limitations in static kernel selection and manual tuning by introducing a dynamic, simulation-driven approach. The project has evolved through collaborative discussions, benchmarking efforts, and integration planning with related technologies like Origami.

## Supporting Technology or Enablers

- **Tensilelite Framework:** Provides the kernel pool and benchmarking infrastructure.
- **hipblaslt-bench:** Enables automated benchmarking and validation.
- **Hardware APIs:** Facilitate extraction of platform-specific parameters.
- **Collaborative Tools:** Teams, Loop, and internal documentation platforms for coordination.
- **Simulation and Modeling Techniques:** Informed by both internal expertise and external research on hardware simulation and performance prediction.
