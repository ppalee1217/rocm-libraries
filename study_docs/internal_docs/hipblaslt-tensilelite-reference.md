# Internal AMD Reference on hipBLASLt & TensileLite

> **Source URL:** https://amd.atlassian.net/wiki/spaces/~7120204c779face96d403c9783064701435635/pages/1763641016/Internal+AMD+Reference+on+hipBLASLt+TensileLite
> **pageId:** `1763641016`
> **Space:** personal space `~7120204c779face96d403c9783064701435635` (authored via ROVO AI)
> **Version:** 1 (created 2026-06-26)
> **Fetched on:** 2026-06-26 (via Atlassian Confluence MCP, `contentFormat=markdown`)
>
> 內部參考頁面的完整內容。所有 Confluence/GitHub/JIRA 連結都原樣保留。
> 本頁本身就是一份經過整理的索引,指向許多其他內部頁面;下方的內嵌連結即為各個被引用
> 資源的標準指標。

---

## 摘要

本報告為使用 **hipBLASLt**、其 **solution-selection 堆疊** 以及 **TensileLite code generator** 的 AMD 工程師定義了一份 **結構化的內部索引**。它把 Confluence 頁面、儲存庫與訓練教材整併成三個模組化的「reference pack」,再加上共用的 metadata 與導覽指引,讓你能直接跳到適合 onboarding、除錯或效能調校的正確資源。

* **目的與範圍** – 為 hipBLASLt 基礎、solution selection 與 TensileLite codegen 建立一份標準、可維護的內部文件地圖,並具備一致的 metadata、標籤與負責人歸屬。
* **重點主題** –

    * hipBLASLt 作為 AMD 靈活的 GEMM 主力(API、使用方式、基本 tuning)
    * solution selection 是一條兩階段的 equality + grid-based 啟發式管線,並逐漸由 Origami/Formocast 與 bench-driven swap 強化
    * TensileLite 作為現代 GEMM kernel generator(YAML → kernels → solution libraries),並有逐漸成形的 snippet/StinkyTofu 基礎設施。

* **主要章節** –

    * 第 1 節釐清適用對象、使用模式,並連結到 HR/技術 onboarding。
    * 第 2 節為所有條目統一 metadata、標籤與連結維護規範。
    * 第 3 節(Module A)索引 hipBLASLt 的概念、安裝設定、API 與入門效能文件。
    * 第 4 節(Module B)涵蓋 solution selection 演算法、tuning 工作流程與除錯模式。
    * 第 5 節(Module C)涵蓋 TensileLite 架構、YAML 設定、tuning 與擴充指南。
    * 第 6 節說明如何把所有內容串接成一個 **集中式的 Confluence 索引頁面**。

* **關鍵洞見** –

    * 應把 **GEMM (hipblasLt)** 頁面當作這三個模組的入口,它已經被當成 MI350/MI455 等新架構上 GEMM 資源的標準中樞 [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159)。
    * **Grid-based 選擇與現代啟發式(Origami/Formocast)** 在 MI300X 上對許多 workload 現在已經能穩定達到 **約 98% 的 exact-tuned 效能**,因此主要的實務落差不在 kernel 本身的品質,而在於選擇層的涵蓋率、穩定性與可除錯性 [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159)、[Solution selection](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744176549)。
    * **TensileLite** 正朝著吸收 legacy Tensile 的明確方向前進,並透過 characterization tests、snippet 架構與基於 StinkyTofu 的最佳化,來降低重構與新資料型別的風險 [Tensile Overview](https://amd.atlassian.net/wiki/spaces/~stebrown/pages/1364192827)、[TensileLite Characterization Tests — Overview & Snapshot Governance](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1755647079)、[TensileLite Snippet Architecture](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1643646497)。
    * 在日常工作中,工程師結合以下幾項能獲得最大效益:

        * **hipBLASLt 基礎** → 理解 API 與除錯旋鈕
        * **Solution-selection 工具**(hipblaslt-bench、tunableop、GEKO、bench-driven swap)以提升涵蓋率/效能
        * **TensileLite 工作流程**,適用於你必須 **改變 kernel pool 本身**、而不只是換個選擇方式時。

---

## 1. 文件目的與適用對象

### 1.1 範圍:hipBLASLt 與 TensileLite 教材的內部索引

本文件的核心目標,是作為三個緊密耦合領域的 **標準內部索引**:(A) hipBLASLt 基礎與 API 使用、(B) solution selection 與 tuning,以及 (C) TensileLite code generation。它並非重新解釋每個概念,而是整理並註解現有最佳的內部資源、說明它們之間的關係,並補充在什麼任務該用哪份文件的指引。這能避免在多次文件改善行動中被點出的常見問題:「在二十個 Confluence 頁面與 GitHub README 之間到處翻找」 [6. hipblaslt documentation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1162287265)。

範圍刻意 **聚焦於工程**:build、除錯、tuning 與擴充。HR、IT 與一般性的 HIP 訓練,只有在能解除這些技術任務阻塞時才會被連結。教材橫跨多個 Confluence space(MLSE、RCPT、SHARK、DCGPUAIST、SSET)、ROCm/rocm-libraries GitHub、SharePoint 簡報,以及 hipBLASLt tuning dashboard 之類的儀表板 [Dashboard: hipBLASLt GEMM Tuning](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1045306155)。

一個重要的設計選擇是這份索引採 **模組化**:每個模組(A/B/C)都寫成可以單獨複製貼上成一個 Confluence 頁面而仍然成立。如此一來,團隊可以只在自己的專案 space 中嵌入 hipBLASLt 基礎、或只嵌入 TensileLite tuning 章節,同時仍能連回此處完整的跨模組索引。

### 1.2 目標讀者

主要對象由三個彼此重疊的群體組成:

1. **新進團隊成員**,位於 MLSE math libs、ROCm Core Perf 或相關群組(CK、MIOpen、AITER),需要快速上手 GEMM。對他們而言,這份索引就像一張經過整理的「前兩週」地圖,從公司 onboarding 指向 HIP 基礎,再進入 hipBLASLt/TensileLite 的細節 [Onboarding & Learning](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744183858)、[HIPBLASLT Onboarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1711090025)。
2. **效能工程師與應用團隊**(例如 DCGPU AIST、Data Center Performance、framework 團隊),已經熟悉 HIP,但需要理解:

    * hipBLASLt 如何選擇 GEMM kernels、以及如何覆寫該選擇,
    * 如何針對特定模型或 GEMM shape 執行 tuning 工作流程,
    * 如何診斷「OOB 效能都沒問題,只有這十個 shape 例外」這類問題 [hipBLASLt User Feedback](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1706234950)。

3. **函式庫維護者與 codegen 開發者**(hipBLASLt core、TensileLite、GEKO、StinkyTofu),需要一份生態系的共用參考:有哪些既有工具、heuristics 放在哪裡,以及 characterization tests 與重構安全網的文件在哪 [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433)、[GEMM Kernel Optimization](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1186895430)。

一個微妙但重要的次要對象是 **非 mathlibs 的相關人士**(PM、framework leads、AAI program owners),他們主要需要高層次地圖,以便提出正確的問題並開立正確的 ticket。對他們來說,第 3–5 節的摘要表格,加上第 6 節的聯絡人/負責人指標,是最有價值的部分。

### 1.3 使用模式:快速查詢 vs. 引導式學習路徑

多數使用者第一次接觸這份索引時會把它當成 **查詢工具**:「我需要知道 MI350 上 batched BF16 GEMM 的 solution selection 怎麼運作」或「MXFP8 的 TensileLite YAML spec 在哪裡?」在這種模式下,每個模組的表格與跨模組相依關係圖的連結,目的就是提供 **一鍵答案**。

同時,對於新進人員或輪調進 GEMM 工作的工程師,**結構化學習路徑** 也有價值。因此這份索引隱含地建議一條分階段的路徑:

1. HIP 基礎(HIP 訓練、教科書) → [Accelerated Computing with HIP - Textbook](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744179132)、[HIP Training at AMD](https://amd.atlassian.net/wiki/spaces/LC/pages/531791935)。
2. BLAS 與 rocBLAS 背景 → [BLAS Introduction](https://amd.atlassian.net/wiki/spaces/aialgo/pages/625983547)、[rocBLAS](https://amd.atlassian.net/wiki/spaces/GPUCPT/pages/624593758)。
3. hipBLASLt 概念 + API → [LDEF-00011: What is HIPBLASLt](https://amd.atlassian.net/wiki/spaces/SSET/pages/805805654)、[Understanding hipBLASLt](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196486)。
4. Bench 與基本 tuning → hipblaslt-bench 文件與入門 tuning 頁面 [How to install and run hipblaslt-bench](https://amd.atlassian.net/wiki/spaces/~marslin2/pages/1652834745)、[hipBLASLt - how to tune](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744185533)。
5. 更深入的 solution selection 與 TensileLite codegen。

一項原創的設計原則是 **每個模組都同時支援這兩種風格**:其子章節先以概覽/定位段落開頭,再進入連結密集、任務導向的細節。這在可讀性與「需要把大量 tribal knowledge 浮現出來」之間取得平衡。

### 1.4 結構概覽:三個模組 + 共用基礎設施

文件其餘部分的組織方式如下:

* **第 2 節 – Common Metadata & Conventions**:每個資源條目如何被標籤與描述(title、owner、ROCm 版本、audience level、topic tags、link hygiene)。若希望索引長期維持可維護性,這點至關重要。
* **第 3 節 – Module A: hipBLASLt Basics**:概念、架構、onboarding、API 使用,以及入門層級的效能指引。
* **第 4 節 – Module B: Solution Selection**:演算法與 heuristics(equality、grid、StreamK、Origami、Formocast)、tuning 工作流程(hipblaslt-bench、GEKO、bench-driven swap)與除錯模式。
* **第 5 節 – Module C: TensileLite Code Generation**:角色定位、YAML 與 codegen pipeline、tuning 方法論,以及如何擴充或除錯 codegen。
* **第 6 節 – Cross-Module Navigation & Index Page**:如何把這些模組組裝成單一 Confluence 索引頁面並維持其健康。
* **第 7 節 – Conclusion**:關鍵建議,以及團隊最重要的單一習慣:把 GEMM (hipblasLt) 當成你的入口,並讓 tuning 與 selection 的變動在那裡保持可見。

### 1.5 Onboarding:HR、權限與基礎連結

在任何人能使用這份索引中的技術資源之前,必須先跨越基本的 HR 與權限門檻。**HIPBLASLT Onboarding** 頁面涵蓋 TechProtect 群組、GitHub 權限,以及 Alola cluster 上標準的「clone → build → test」工作流程,包含一個 Slurm+container 的呼叫範例,以及類似這樣的 build 指令:

```shell
cd rocm-libraries/projects/hipblaslt
./install.sh -c -a gfx942 --skip-rocroller
```

並提醒:由於 TensileLite kernel generation,初次 build **預期約需 75–85 分鐘** [HIPBLASLT Onboarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1711090025)。

至於更廣泛的 AGS/MLSE onboarding——包括 HR 任務、HIP 課程權限與一般 ROCm 學習——應把 **Onboarding – AGS Libraries** 與 **Onboarding & Learning** 頁面視為先決條件。它們指向 HIP 訓練、架構白皮書與內部學習入口網站,這些是 hipBLASLt 與 TensileLite 一切內容的基礎 [Onboarding - AGS Libraries](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744162755)、[Onboarding & Learning](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744183858)。

一個微妙但實用的洞見是:**把 TechProtect 群組對照到某位同事**(如 HIPBLASLT Onboarding 頁面所建議)往往遠比臨時提出權限申請來得快。把這個訣竅明確寫進索引,能幫助新進人員避免因缺少權限而卡關好幾天。

---

## 2. Common Metadata & Conventions(共用 Metadata 與慣例)

### 2.1 標準 Metadata 欄位

為了讓索引可維護且可搜尋,每個資源條目都應帶有標準 metadata。下表彙整這些欄位,以及它們在本報告與預期的 Confluence 索引頁面中如何使用:

| 欄位 | 說明 / 用途 |
| --- | --- |
| **Title** | 確切的 Confluence 或文件標題;用作顯示名稱與連結文字。 |
| **Owner / Team** | 目前的維護者或主要 POC;通常對照自 component owner 清單 [List of Component owners for mathlibs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1363903581)。 |
| **Source System** | Confluence、GitHub、SharePoint、內部訓練入口網站、dashboard 等。 |
| **ROCm / HW Version Range** | 已知可正常運作的版本範圍(例如「ROCm 7.1–7.3, gfx942/gfx950」),若與版本無關則標為「conceptual」。 |
| **Last Updated / Review Cadence** | 最後修改時間,加上一個非正式的「每 N 個月複查一次」準則。 |
| **Intended Audience Level** | Intro、intermediate、advanced;用於篩選檢視與推薦學習路徑。 |
| **Topic Tags** | API、performance、architecture、codegen、debugging、tuning 等。 |
| **Component Tags** | hipBLASLt、TensileLite、rocBLAS、MIOpen、CK、AITER 等。 |

這些欄位中有許多可從 Confluence metadata(最後更新、作者、space)與 GitHub commit 歷史自動推得。限制——同時也是一項關鍵建議——是 **audience level 與 topic/component 標籤必須經過人工整理**,而非自動猜測,因為它們決定了新進工程師如何發現內容。

給維護者的一項原創建議是:把這些 metadata **以小表格放在每個模組頁面的最上方**(hipBLASLt 基礎、solution selection、TensileLite)。如此 Confluence macro 便能把它們抓進一個全域索引,減少重複與漂移。

### 2.2 標籤 / 分類法(Tagging / Taxonomy)

考量 GEMM 工作的廣度,標籤是讓這份索引能擴展的唯一方法。一套精簡但有效的分類法會包含:

* **Topics**:

    * **API** – 公開的 hipBLASLt 函式、descriptors 與範例程式 [hipBLASLt API reference](https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/api-reference.html)。
    * **Performance** – tuning、benchmarking、heuristics、OOB vs tuned 指標 [hipBLASLt - how to benchmark](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744185491)。
    * **Architecture** – 設計概覽、control flow 與堆疊圖 [Understanding hipBLASLt](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196486)。
    * **Codegen** – TensileLite 內部、YAML、snippet、StinkyTofu [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433)。
    * **Debugging** – triage 指南、coredump 分析、logging 旋鈕 [rocBLAS GEMM Triaging and Debugging Guide](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1496374640)。
    * **Tuning** – hipblaslt-bench auto-tuning、GEKO、TensileLite tuning demo [GEMM Kernel Optimization](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1186895430)、[Tensile tuning demo and documentation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744168348)。

* **Components**:

    * **hipBLASLt**、**TensileLite**、**rocBLAS**、**Tensile**、**rocRoller**、**Origami**、**Formocast**、**StinkyTofu**、**GEKO**。
    * 當 GEMM tuning 觸及 framework 時,**AITER**、**CK**、**vLLM** 之類的跨堆疊標籤很有用。

一個不那麼顯而易見但重要的重點是:標籤應反映 **人們如何搜尋**,而不只是我們如何思考架構。例如,為關於 TensileLite MX kernels 或 hipBLASLt epilogue 擴充的文件加上 **「MXFP4」** 或 **「FP8」** 標籤,能大幅降低 inference 團隊的摩擦,因為他們可能不知道該去「codegen」還是「solution selection」底下找 [hipBLASLt User Feedback](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1706234950)。

### 2.3 連結維護(Link Hygiene)與維運

健全的 link hygiene 至關重要,因為許多效能與 tuning 文件會被複製、重新版本化,並在不同 space 之間搬移。建議的作法包括:

* 在這份索引中嵌入連結時,優先使用 **Confluence 頁面 permalink** 而非短網址。
* 對於 GitHub 內容,務必固定到 **branch + path**(例如 `rocm-libraries/tree/develop/projects/hipblaslt/tensilelite`),而非原始 commit hash,但在被連結的 Confluence 頁面中引用 PR ID 以保留歷史脈絡 [Kernel Generator: TensileLite](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119)。
* 避免直接連到產生出的 artifact(例如 `.dat` libraries、`.co` 檔)。改為連到說明 **如何重新產生它們** 的文件(TensileLite、GEKO、bench-driven swap 工作流程)。
* 對於已知會漂移的連結(例如 team drive 下的 SharePoint 簡報),加上一段簡短的「How to rediscover this」備註,通常透過 GEMM (hipblasLt) 中樞或 GEMM Programs Status 頁面 [GEMM Programs Status](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1662987250)。

一個具體的維運機制是:為失效連結與缺漏文件指定一個 **單一聯絡 alias**——通常是 GEMM optimization team 或 mathlibs 文件 POC——讓個別工程師不必猜要 ping 誰。

### 2.4 標準資源對應(Canonical Resource Mapping)

對 hipBLASLt 與 GEMM 而言,已存在一個隱含的標準中樞:MLSE space 中的 **GEMM (hipblasLt)**。該頁面彙整了 program status、offsite 簡報、GEMM kernel generators,並連結到 hipBLASLt、TensileLite 及其他 kernel-generation 生態系 [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159)。

這份索引把該頁面當作三個模組的 **根登陸頁**,並建議任何新的重大 GEMM 計畫(例如 MI455 AAI Day、MXFP4 inference 啟用)都串接進去。如此一來:

* hipBLASLt 基礎模組只要說「從 GEMM (hipblasLt) → Module A 開始」即可。
* Solution-selection 的 RFC(Formocast、Origami 變更)會浮現給所有人,而不是埋在孤立的 space 裡。
* TensileLite 的 roadmap 與 characterization tests 有一個可被發現、跨團隊的歸屬地。

關鍵想法是:**我們不需要再多一個標準頁面**——我們需要的是在 GEMM (hipblasLt) 之上經過整理的檢視,而這正是本文件所提供的。

---

## 3. Module A: hipBLASLt Basics(hipBLASLt 基礎)

### A.1 概覽與定位

hipBLASLt 是 AMD **以 HIP 為基礎、類 BLAS 的 GEMM 函式庫**,定位為 NVIDIA cuBLASLt 的靈活、高效能對應品。它純粹聚焦於 GEMM 風格的運算,但在傳統 BLAS 之外加入了豐富的 **epilogue fusion**(bias、activation、scaling、softmax、layernorm 等)與 **mixed-precision 支援** [LDEF-00011: What is HIPBLASLt](https://amd.atlassian.net/wiki/spaces/SSET/pages/805805654)、[HipBLASLt Tools](https://amd.atlassian.net/wiki/spaces/aialgo/pages/626004645)。

就定位而言,hipBLASLt **與 rocBLAS 並列**:rocBLAS 實作標準的 BLAS 1/2/3 API,仍服務許多 HPC workload,但在 gfx942/gfx950 等較新架構上,越來越常 **把 GEMM 委派給 hipBLASLt**,尤其是針對 AI 資料型別與 fused operations [GEMM (and hipBLASLt/rocBLAS) FAQs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744195234)。當 framework 與 routing 層(AITER、CK、Triton routers)想要兼具 fusion 可能性的頂尖 GEMM 效能時,所仰賴的就是 hipBLASLt [hipBLASLt User Feedback](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1706234950)。

一個有用的心智模型是:

| Library | 對應品 | 重點 |
| --- | --- | --- |
| **rocBLAS** | cuBLAS | 標準 BLAS API、HPC GEMM、legacy BLAS |
| **hipBLASLt** | cuBLASLt | 以 AI 為主的 GEMM、mixed precision、fusion |
| **CK / others** | custom kernels | 特化運算(attention、conv、MoE) |

來自內部回饋的一項原創洞見是:**hipBLASLt 的限制因素並非 GEMM 的原始效能**——對 BF16 訓練 workload 而言,它已被視為「gold standard」 [hipBLASLt User Feedback](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1706234950)。落差往往集中在 **低精度資料型別、fusion 涵蓋率與易用性**(tuning 穩定性、發版節奏)。這也是為什麼本模組不只強調 API 文件,也強調效能最佳實務與工具。

關鍵概念與架構文件:

| 資源 | 角色 |
| --- | --- |
| [LDEF-00011: What is HIPBLASLt](https://amd.atlassian.net/wiki/spaces/SSET/pages/805805654) | 高層次的目的、功能與使用情境。 |
| [Understanding hipBLASLt](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196486) | 從 API 到 kernels 的 control flow 與架構。 |
| [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159) | 標準 GEMM 中樞,連結到設計、tuning、generators。 |

### A.2 核心概念與架構

在 API 層級,hipBLASLt 公開的 **handles、descriptors 與 operations** 類似 cuBLASLt:你建立一個 handle、構建 matrix 與 operation descriptors(資料型別、layouts、epilogues),然後用這些 descriptors 與資料指標呼叫 `hipblasLtMatmul()` [hipBLASLt API reference](https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/api-reference.html)。這種間接層讓它能把龐大的 GEMM 變體空間,封裝進一個精簡、穩定的公開 API 介面。

支援的 **資料型別** 橫跨 FP64/FP32/FP16/BF16、INT8,以及較新的 FP8/MXFPx 系列格式,並具備 **mixed-precision compute**(例如 FP8 輸入搭配 FP32 accumulation 與各種輸出型別)。HipBLASLt Tools 與 GEMM 中樞之類的內部工具與文件,明確記載了哪些 (A,B,C,D,compute) 組合受支援,以及它們如何對應到實際 kernels [HipBLASLt Tools](https://amd.atlassian.net/wiki/spaces/aialgo/pages/626004645)、[GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159)。

在架構上,call stack 為:

> Application → hipBLASLt front-end (API + descriptors) → solution selection logic → **TensileLite / rocRoller / custom kernels** → GPU kernels

其中 hipBLASLt 會快取 kernel「solutions」,以避免對重複出現的 shape 重新選擇 [Understanding hipBLASLt](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196486)。在現代產品(MI300/MI350、gfx12)上,**TensileLite 是主要 backend**,負責 dense 與 structured sparsity GEMM,而 rocRoller 主要用於某些 MX 資料型別,custom kernels 或 CK/Triton 偶爾會透過「GEMM from anywhere」整合繞過一般路徑 [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159)、[Hipblaslt-kernel-from-anywhere](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1403547193)。

這種分層設計有個不那麼顯而易見的後果:**效能除錯會自然地被切分**:

* 若選到錯的 kernel,或效能在不同 build 之間不穩定 → 看 **solution selection**(Module B)。
* 若沒有 kernel,或所有候選都很慢 → 看 **TensileLite kernel pool** 與 tuning(Module C)。
* 若 overhead 主導(例如 batched GEMM 搭配緩慢的 host 設定) → 聚焦於 **hipBLASLt front-end 與 caching** [Rocblas/hipblasLt Batched GEMM Performance](https://amd.atlassian.net/wiki/spaces/DCGPUAIST/pages/1099690121)。

### A.3 入門與 Onboarding

對 hipBLASLt 的新手而言,有兩條並行的軌道:**系統設定與 build**,以及 **概念學習**。

在設定方面,**HIPBLASLT Onboarding** 與 **Initial Setup** 提供詳細步驟:

* 透過 ROCm monorepo 或直接從 hipBLASLt repo clone。
* 使用 sparse checkout 只納入必要的專案(hipblaslt、hipblas-common、shared/origami、shared/mxdatagenerator、shared/stinkytofu),以節省磁碟與 build 時間 [HIPBLASLT Onboarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1711090025)。
* 以 `./install.sh -dc -a <arch>`(首次可用 `-idc` 以包含相依套件)進行 build,並記得 **指定架構**(gfx942/gfx950 等),以避免可能耗時超過 1 小時且占用大量磁碟的 multi-arch build [Initial Setup](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744197146)。

在 **Alola** 這類 cluster 上,HIPBLASLT Onboarding 文件示範如何提交 Slurm job,使用正確的 container、僅 CPU 的 build 節點,以及掛載的 home/scratch 目錄。它強調要避免在 login 節點上 build,並說明 **TensileLite kernel generation 既長又幾乎無輸出**,這常讓新手感到意外 [Building and Benchmarking hipblaslt on Slurm Cluster](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1615927411)。

在學習方面,**Onboarding & Learning**、**HIP Training at AMD** 中樞,以及 **Accelerated Computing with HIP** 教科書,提供必要的 HIP、ROCm 與 GPU 架構背景。一個特別有效的做法,是把 HIP 課程(HIP 100/200/300 等級)與 GEMM optimization team onboarding checklist 中的動手任務搭配——clone hipBLASLt、build 它、跑 hipblaslt-bench,並嘗試一個小型 TensileLite tuning job [HIP Training at AMD](https://amd.atlassian.net/wiki/spaces/LC/pages/531791935)、[GEMM Optimization Team On-Boarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196538)。

從原創最佳實務的角度看,團隊應 **把第一次端到端 build 當作訓練資產**,而不只是一道關卡:記下實際可行的確切指令與環境變數(包括 ROCm 版本、container image 與 GPU arch),並與這份索引一起保存,讓新進人員能重現成功,而不是去除錯環境差異。

### A.4 API 參考與使用模式

hipBLASLt API 的主要參考是託管於 ROCm docs 的公開 **hipBLASLt API reference**。它記載了 descriptors、matmul operations 與 epilogue 選項,連同 C 與 C++ 繫結 [hipBLASLt API reference](https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/api-reference.html)。在內部,**Understanding hipBLASLt** 透過逐步講解一個具體的 C++ 範例(`sample_hipblaslt_gemm.cpp`),說明 descriptors 與 operations 如何轉譯為 kernel 的選擇與啟動,以此作為補充。

核心使用模式:

1. 建立一個 `hipblasLtHandle_t`。
2. 為 A、B、C、D 建立 matrix descriptors,含 layout、strides、資料型別。
3. 建立一個 matmul descriptor,捕捉 transposes、compute type 與 epilogues(bias、activation、scaling)。
4. 選擇性地查詢 heuristics 或執行一次 auto-tuning。
5. 呼叫 `hipblasLtMatmul()`。

HipBLASLt 支援種類繁多的 **fused epilogues**,包含 bias、GELU、ReLU、Swish、clamp,以及 DGELU、BGRAD 等反向傳遞(backward-pass)變體 [HipBLASLt Tools](https://amd.atlassian.net/wiki/spaces/aialgo/pages/626004645)。內部文件中有 hipBLASLt 與 cuBLASLt epilogues 的對照表,顯示兩者幾乎對等,並有少數擴充(例如某些訓練 backward ops)。

一項重要的原創建議是 **把 epilogues 同時當作 scheduling hints 與數學運算來看待**:使用 fused bias 或 activation 不僅節省 memory bandwidth,還會在 backend **選到不同的 solution family**,而後者可能有不同的 tuning 特性。這正是為什麼相較於相同維度的「plain GEMM」,epilogue 較重的 workload 往往需要單獨 tuning 或 bench-driven swap。

### A.5 效能與最佳實務(入門層級)

hipBLASLt 入門層級的效能 tuning,聚焦於 **輸入塑形與設定衛生**,而非 kernel 內部細節:

* 對齊 leading dimensions 與 strides,以啟用 coalesced access 並避免病態的 padding。
* 盡可能使用建議的 matrix 維度與 batch;極度細長或極小的 matrix 高度依賴 equality tuning,可能無法被預設 grid 良好涵蓋。
* 在 hipblaslt-bench 中開啟 `--print_kernel_info`,以查看正在使用哪個 solution 與 kernel,並留意非預期的 solution index 變動 [HipBLASlt GEMM kernel benchmark](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196818)。

**hipBLASLt – how to benchmark** 與多份 hipblaslt-bench 指南,示範如何執行穩定的 benchmark、控制 iterations 與 warm-up,並透過 `HIPBLASLT_BENCH_FREQ` 環境變數收集頻率資訊 [hipBLASLt - how to benchmark](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744185491)、[How to install and run hipblaslt-bench](https://amd.atlassian.net/wiki/spaces/~marslin2/pages/1652834745)。在深入 **hipBLT-board** 這類更精細的工具之前,這些基礎是先決條件;hipBLT-board 把 TuningDriver、benchmark 與報表包裝進單一 Dash 應用程式 [hipBLT-board - System Overview & Usage Guide](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1673435092)。

最後,**hipBLASlt Startup Guide into Profiling, Debugging and Optimization** 把 hipBLASLt workload 與 ROCm profiling 工具(rocprof、ROCm Compute Viewer)串連起來,並建議一個漸進式工作流程:先驗證 API 正確性、確認 solution selection 行為,再在前兩者都理解之後,才使用 profiler 與 ISA 檢視 [hipBLASlt - a Startup Guide into Profiling, Debugging and Optimization](https://amd.atlassian.net/wiki/spaces/RCPT/pages/1179073633)。

這裡的一項原創洞見是:**80% 的「hipBLASLt 很慢」ticket 源自塑形不當的輸入或 solution-selection 假象**,而非 codegen。因此對新進工程師而言,最佳投報率是在嘗試任何 TensileLite tuning 之前,先精通 hipblaslt-bench(包括 YAML 驅動的執行)與 logging 旋鈕。

---

## 4. Module B: hipBLASLt Solution Selection(hipBLASLt 解法選擇)

### B.1 概念總覽

hipBLASLt 中的 **solution** 是一份完整的 kernel 設定——macro tile sizes、wave sizes、unroll depth、instruction variant、LDS 用量,以及 scheduling 參數。**Solution selection** 則是把一個執行期的 GEMM 問題 `(M,N,B,K, datatypes, layout, epilogue)` 對應到函式庫中其中一個 solution 的過程。

如 GEMM FAQs 與 solution-selection 設計文件所彙整,其核心演算法是 **兩階層** 的:

1. **Equality lookup** – 在 **Equality** libraries 中搜尋對 M、N、K(及其他參數)的精確匹配。若找到,就啟動該 kernel。
2. **Grid-based fallback** – 若不存在精確匹配,則在 **一組具代表性的 size grid** 中搜尋,依 heuristics 選出最接近的 grid point,再使用其 solution [GEMM (and hipBLASLt/rocBLAS) FAQs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744195234)、[Solution selection](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744176549)。

其他 solution family——**StreamK**、**Origami**、**Formocast**——的行為,是疊加在這個 equality+grid 基礎之上的特化 heuristics 或搜尋空間。例如,StreamK 需要啟用一個環境變數,並針對有利於 concurrency 的 scheduling;Origami 與 Formocast 則使用學習式或模擬式模型來精修 grid 選擇 [GEMM HEURISTICS](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744198388)、[Formocast Design Document (RFC)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304232451)。

在概念上,這條 pipeline 有個清楚的權衡:

* **Equality** 使效能最大化,但要求對每個 size 都進行 tuning。
* **Grid-based** 藉由挑選一小組具代表性的集合(其 kernels 能對鄰近 size 泛化)來大幅降低 tuning 成本;有證據顯示,在 MI100/MI200 上,相對於窮舉 tuning 的函式庫,**平均效率落在約 1–2% 內,最大落差約 15%**,在較新的 GPU 上也類似 [Solution selection](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744176549)、[GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159)。

一項原創結論是:如今大多數效能工程都圍繞著 **整理與改進這些 heuristics 與 grid**——包括 Formocast 與 bench-driven 的重新 tuning——而非對每個 size 手動新增 equality kernels。

### B.2 內部設計與演算法

**Solution selection** 頁面與 GEMM HEURISTICS 文件詳述了 equality 與 grid libraries 的結構、查詢如何進行(常以排序表中的 binary search),以及為每個 solution 記錄哪些指標 [Solution selection](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744176549)、[GEMM HEURISTICS](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744198388)。Solution selection metrics 文件定義了 **efficiency vs ideal**、所選 solution 的穩定性,以及與競爭對手硬體的比較 [Solution Selection Metrics](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744174730)。

**Origami** 與 **Formocast** 等 heuristics 運作於 TensileLite 的 solution pool 之上。Origami 使用結構化 heuristics 與搜尋來選出好的 solution;Formocast 更進一步,使用模擬式效能建模,在不窮舉 benchmark 的情況下預測候選 kernels 的效能 [Difference between Origami and Formocast](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304199634)、[Formocast Design Document (RFC)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304232451)。

至關重要的是,**solution-selection 的品質如今本身也成為 benchmark 的對象**,並有專屬的 dashboard 與比較工具,能:

* 掃描各種 GEMM size,並量測所選 solution 的 FLOPS。
* 與 ideal(所有可用 solution 中的最佳者)及競爭對手函式庫比較。
* 追蹤 selection efficiency 並標出離群值 [Dashboard: hipBLASLt GEMM Tuning](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1045306155)。

近期工作的一項原創觀察是:heuristic 的極限在 **中等大小的 GEMM** 上最明顯——這裡的工作量足以暴露 kernel 之間的差異,卻不足以攤平所有 overhead。例如,MI300X 上的 ROCm-CUTLASS benchmark 顯示,相較於預設 heuristic 的選擇,在 size 1024³ 時對多個 hipBLASLt 演算法進行執行期搜尋,可將效能提升最多達 **1.88×** [ROCm-CUTLASS Benchmark Results — AMD MI300X (2026-06-04)](https://amd.atlassian.net/wiki/spaces/DCGPUAIST/pages/1718303144)。這凸顯了持續投入 heuristics(Origami/Formocast)與 bench-driven 重新選擇的價值。

### B.3 Tuning 工作流程與工具

hipBLASLt solution selection 有一個豐富的 tuning 工具生態系支援:

* **hipblaslt-bench auto-tuning** – 「how to run hipblaslt-bench auto-tuning tool」文件說明如何為某個 shape(或 YAML 中的多個 shape)探索所有可用 solution、量測效能並匯出結果 [hipBLASLt - how to run hipblaslt-bench auto-tuning tool](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744185063)。
* **hipBLASLt – how to tune** 與 **hipBLASLt GEMM Tuning Steps Using Tensile** 描述逐步的工作流程:挑選 GEMM shape、執行 TensileLite tuning、合併新的 logic libraries、重新 build hipBLASLt 並重新 benchmark [hipBLASLt - how to tune](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744185533)、[hipBLASLt GEMM Tuning Steps Using Tensile](https://amd.atlassian.net/wiki/spaces/~kangwang/pages/914331845)。
* **GEKO (GEMM Kernel Optimization)** – 一個更高層級的 Python 套件,透過 GA-based 與 dense search 流程,協調 TensileLite tuning、benchmark 分析與函式庫整合。它讀取 hipBLASLt logs、產生 TensileLite 設定 YAML、執行 tuning(grid 或 GA search),再把產生的函式庫合併回 hipBLASLt [GEMM Kernel Optimization](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1186895430)。
* **hipBLT-board** – 一個 Dash 網頁應用,為 hipBLASLt 整合 benchmarking、tuning 進入點與 metadata。它與 TuningDriver、GEKO 及一個 MySQL catalog 整合,讓使用者透過單一 UI 從 HIP logs 一路走到 tuned solutions 與報表 [hipBLT-board - System Overview & Usage Guide](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1673435092)。
* **Bench-driven swap workflow** – 當 kernel pool 足夠、但 grid-based 的選擇已過時時,**hipBLASLt GridBased re-tuning: bench-driven swap workflow** 讓你能對每個 grid point 系統性地 benchmark 各種替代方案,並在 YAML grid 表中換入勝出者,而無需重新產生 kernels [hipBLASLt GridBased re-tuning: bench-driven swap workflow](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1710204999)。

從這些工具浮現出的一項原創 tuning 策略是:

1. **先對既有 solution 做 dense search**(GEKO search 或 hipblaslt-bench `--algo_method all`),以確保 solution pool 對你的 workload 被充分利用。
2. 當 dense search 顯示出系統性的利用不足時(例如某些 grid point 一直選到非最佳 solution),使用 **bench-driven swap** 來更新 grid。
3. 只有在效能仍不足時,才投入 **TensileLite tuning** 以擴充 solution pool(Module C)。

這種分階段做法比直接跳進 kernel generation 便宜得多,也避開一些常見陷阱(例如花好幾天 tuning 那些 equality libraries 永遠不會命中的 kernels)。

### B.4 除錯與分析

當 GEMM 的效能或正確性出問題時,有數條互補的除錯途徑:

* **查看選到哪個 solution** – 使用 `hipblaslt-bench --print_kernel_info`(以及搭配 `HIPBLASLT_LOG_FILE` 的 `HIPBLASLT_LOG_MASK=64`)來查看 solution index、kernel 名稱與參數。GEMM FAQs 說明 equality/grid libraries 如何組織,以及如何解讀 solution index [GEMM (and hipBLASLt/rocBLAS) FAQs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744195234)。
* **從 rocBLAS 橋接到 hipBLASLt** – rocBLAS GEMM triage 指南示範如何使用 `ROCBLAS_LAYER` 與其他環境變數,捕捉使用了哪個 backend(Tensile vs hipBLASLt),以及如何透過 hipblaslt-bench 重現相同的 GEMM 以做更深入分析 [rocBLAS GEMM Triaging and Debugging Guide](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1496374640)。
* **持久化 tuned solution maps** – **Persisting hipblaslt-bench and tunableop solution maps** 文件示範如何把每個 shape 的勝出資料(來自 hipblaslt-bench 或 tunableops)轉成 solution maps,並合併進 hipBLASLt 的函式庫,使 tuned 的選擇能在不同 build 之間持久存在 [Persisting hipblaslt-bench and tunableop solution maps](https://amd.atlassian.net/wiki/spaces/DCGPUAIST/pages/889321543)。
* **強制使用特定 solution** – 當你已知 ideal 的 solution index 時,**How to build rocblas/hipblaslt with the specific solution found by user driven** 說明如何把對應關係直接加入 YAML logic 檔並重新 build 函式庫,讓所需 solution 對特定 shape 被硬接寫死 [How to build rocblas/hipblaslt with the specific solution found by user driven](https://amd.atlassian.net/wiki/spaces/DCGPUAIST/pages/680803767)。

一項原創最佳實務是把 **solution index 不穩定** 當成一等問題來處理:hipBLASLt 使用者回饋文件指出,solution index 在不同 build 之間變動會破壞已儲存的 tuning 結果,並讓與 AITER 等 router 的整合變複雜 [hipBLASLt User Feedback](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1706234950)。因此,在處理 heuristics 或函式庫合併時,工程師應使用 logs 與 characterization tests 來驗證穩定性,而不只是看效能指標。

### B.5 跨元件相依

Solution selection 的好壞,取決於與其連接的 **kernel pool** 與 **selection logic**。跨元件相依包括:

* **TensileLite** – GEMM solutions 的主要來源。任何缺少的 kernels、資料型別缺口或 mis-tuned 的 kernel 參數,都會在上游表現為某些 shape 的「no solution」或效能不佳 [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433)。
* **Origami & Formocast** – 整合進 solution-selection 堆疊,提供增強的 grid 預測與模擬式效能估計;兩者都仰賴 TensileLite 的 solution 語意與 benchmarking 基礎設施 [Difference between Origami and Formocast](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304199634)、[Formocast Design Document (RFC)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304232451)。
* **rocBLAS integration** – rocBLAS→hipBLASLt 整合計畫明確描述 rocBLAS 將如何為複雜 GEMM 呼叫 hipBLASLt,以及這些呼叫的 solution selection 必須如何保持一致 [hipBLASLt rocBLAS integration Planning](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196689)。

負責人與 SME 的參考對這一層至關重要:

* **mathlibs component owner list** 指出 hipBLASLt、TensileLite、GEMM tuning 與 rocRoller 的 POC [List of Component owners for mathlibs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1363903581)。
* **Shift-Left – Roles/Responsibilities** 頁面把 ROCm 元件對應到 TheRock CI 中的 Dev、QA 與 DevOps SME;隨著 TensileLite 與 solution selection 邏輯被當成統一 build 的一部分來測試,這點越來越重要 [Shift-Left - Roles/Responsibilities](https://amd.atlassian.net/wiki/spaces/SHARK/pages/1382516837)。

一項原創建議是在中央索引中明確記載 **負責邊界**:例如「hipBLASLt solution selection heuristics:聯絡 GEMM optimization team;TensileLite kernel generation 參數:聯絡 TensileLite 開發者」,並連結到已涵蓋大部分這類資訊的 process-improvement 與 program-status 頁面 [Process improvements](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1092380686)、[GEMM Active Programs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1387220065)。

---

## 5. Module C: TensileLite Code Generation(TensileLite 程式碼產生)

### C.1 TensileLite 的角色

**TensileLite** 是嵌入在 hipBLASLt(與 hipSPARSELt)之中、現代且輕量的 GEMM kernel generator 與 runtime library。它由原本的 Tensile 專案演進而來,重點包括:

* 與「Lt」函式庫(hipBLASLt、hipSPARSELt)更緊密整合。
* 支援 **fusion**(bias、activation、reduction、softmax、layernorm 等)。
* mixed-precision,以及較新的 **MXFP4/6/8** 與 FP8 資料型別 [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433)、[GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159)。

**Tensile Overview** 頁面釐清了 Tensile、TensileLite 與 ArchGEMM 之間的關係,並指出 **TensileLite 現在是積極開發的重心**,而 Tensile 則退居於 legacy 硬體與某些問題類型 [Tensile Overview](https://amd.atlassian.net/wiki/spaces/~stebrown/pages/1364192827)。對較新的架構而言,連 rocBLAS 也常透過 hipBLASLt 取用由 TensileLite 產生的 GEMM。

在功能上,TensileLite 扮演兩種角色:

1. **Code generator** – 給定一份問題 spec 與參數範圍(YAML),產生候選 kernels、編譯它們、執行 benchmark,並產出 **code objects + solution logic**。
2. **Runtime library** – 在 hipBLASLt runtime,載入 solution logic 與 code objects,並以 kernel launch 參數回應 solution-selection 查詢 [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433)。

這種切分至關重要:多數開發者透過 hipBLASLt 隱含地與 runtime 互動;只有 kernel 開發者與 tuner 需要碰 codegen 階段。本模組正是針對後者這群人。

### C.2 Codegen Pipeline 概覽

高層次的 pipeline 為:

1. **Inputs** – YAML 設定,描述:

    * 問題類型(GEMM、layouts、資料型別、epilogues)。
    * 參數 grid(MacroTile、DepthU、MatrixInstruction、WorkGroupMapping、Prefetch 等)。
    * benchmark 問題 size(M,N,B,K 範圍)。

2. **TensileLite main** – 解析 YAML、從 GlobalParameters 與 ValidParameters 這些 Python 模組填入預設值、產生候選 solutions、判斷哪些參數組合有效,並選擇性地建立一份 tuning schedule [Kernel Generator: TensileLite](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119)。
3. **Code generation** – 使用 `rocisa`(以及越來越多的 **StinkyTofu**)為每個候選 solution 產生 assembly,並編譯成 **code objects**。
4. **Benchmarking** – 使用 TensileLite client 在目標 GPU(或 FFM simulator)上啟動 kernels,記錄 GFLOPS 與其他指標。
5. **Solution library 建立** – 產出 YAML logic libraries,總結每個問題或 grid point 最佳的 solution 是哪個。
6. **Integration** – hipBLASLt build 使用 TensileCreateLibrary 把 logic YAML 轉成 binary libraries,並整合進 build [Tensilelite - GEMM kernel generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405990433)、[Extending Tensilelite Code Generator Support for Complex Datatypes](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1325571391)。

在現代 roadmap 上,這條 pipeline 正被進一步重構:

* **Snippet architecture** – 一套重新結構化的 codegen 架構,以具型別、可組合的指令「snippets」為基礎,並有 per-architecture 套件與功能模型 [TensileLite Snippet Architecture](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1643646497)、[Snippet Architecture: Vision and Goals](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1643344006)。
* **StinkyTofu** – 一個以 pass 為基礎的 IR optimizer(logical 與 ASM IR),對 TensileLite 產出的 kernels 執行 DAG scheduling、waitcnt 插入、peephole 最佳化等 [StinkyTofu Development](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1259089125)、[ROCm](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1451494995)。

一項原創洞見是:這些重構並非「有也不錯」,而是讓 codebase 變得 **對 agent 與人類都可處理** 的必要條件:legacy 的 KernelWriterAssembly 是一個 1.4 萬行、帶有大量共享狀態的 monolith,使得推理與重構都極為困難 [Snippet Architecture: Vision and Goals](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1643344006)。snippet+StinkyTofu 這個方向讓 codegen 能以更安全、test-driven 的方式演進。

### C.3 設定與範本

TensileLite YAML 檔是 kernel tuning 與 generation 的主要使用者介面。多份文件與簡報可作為指南:

* **tensilelite yaml config for Kernel A–E (draft)** – MXFP4/MXFP8 kernels 的具體範例,展示特定 kernel family(MAF、OpenAI GEMMs、Meta small-K)的 MatrixInstruction、DepthU、SourceSwap、Prefetch 等參數 [tensilelite yaml config for Kernel A-E (draft)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1732654216)。
* **MI300 Tensile Kernel Generation Parameters Overview** – 一份簡報,逐一講解關鍵參數(MacroTile、DepthU、VectorWidths、StaggerU、PrefetchLocalRead、LDS 設定)及其典型範圍,並有明確指引,如「PLR=1 對 TensileLite 通常沒問題,但某些設定可試 2 以上」 [MI300_tensilelite_Tensile_Kernel_Generation_Parameters_Overview_v1.1.pptx](https://amd.atlassian.net/wiki/pages/viewpageattachments.action?pageId=744192975&preview=%2F744192975%2F745281680%2FMI300_tensilelite_Tensile_Kernel_Generation_Parameters_Overview_v1.1.pptx)。
* **Kernel Generator: TensileLite** – 記載 GlobalParameters 與 ValidParameters,包括 PerformanceMetric、NumWarmups、SkipSlowSolutionRatio、EnqueuesPerSync 等效能 tuning 旋鈕的典型值 [Kernel Generator: TensileLite](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119)。

命名慣例把完整設定嵌入確定性的 kernel 名稱中,例如:

`Cijk_Alik_Bljk_HHS_BH_HA_S_SAV_UserArgs_MT128x96x64_MI16x16x1_SN_..._WG64_2_1_...`

其中像 `MT128x96x64`、`MI16x16x1`、`WG64_2_1`、`PGR2`、`PLR1` 與 `ISA1150` 等片段,分別編碼 macro tile size、MFMA instruction、workgroup、prefetch 深度與目標 ISA [Kernel Generator: TensileLite](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119)。這讓人能從 kernel 名稱反推出 YAML 參數,並在 tuning 或修補個別 kernel 的工作流程中被大量使用。

撰寫 YAML 的一項關鍵原創準則是:

* 從 **reference configs**(Kernel A–E 文件、GEKO 中 per-arch fork 的參數)起步,而非從頭寫起。
* 避免過度擴張參數 grid;每多一個軸,都可能產生數百個候選 kernels,其中許多會超出 register 或 LDS 上限而最終被丟棄 [Kernel Generator: TensileLite](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1405870119)。
* 記錄為何選擇某個參數範圍(例如「StaggerU=[0,32] 用於 NT,[0,4] 用於 NN/TN/TT」),最好寫在註解或一個搭配的 Confluence 頁面,以利日後維護 [MI300_tensilelite_Tensile_Kernel_Generation_Parameters_Overview_v1.1.pptx](https://amd.atlassian.net/wiki/pages/viewpageattachments.action?pageId=744192975&preview=%2F744192975%2F745281680%2FMI300_tensilelite_Tensile_Kernel_Generation_Parameters_Overview_v1.1.pptx)。

### C.4 Tuning 與最佳化

Tuning TensileLite 牽涉探索參數 grid 並選出最佳候選。**Tensile tuning demo and documentation** 頁面提供一個通用示範,而 **General Usage for TensileLite Tuning** 則提供執行 tuning job、並用產生的函式庫重新 build hipBLASLt 的具體步驟與指令 [Tensile tuning demo and documentation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744168348)、[General Usage for TensileLite Tuning](https://amd.atlassian.net/wiki/spaces/~geotseng/pages/389678194)。

高層次 tuning 方法論:

1. **定義 workload** – 使用 hipBLASLt logs(HIPBLASLT_LOG_MASK=64)從目標模型收集真實的 GEMM shape [GEMM Optimization Team On-Boarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196538)。
2. **產生 configs** – 使用 config generators(在 GEKO 或 TensileLite 工具中)產出涵蓋相關 shape 與合理參數 grid 的 YAML。
3. **執行 tuning** – 在多顆 GPU 上(通常多 GPU 並行)啟動 TensileLite tuning job。要預期會出現「錯誤」,例如 kernels 超出 VGPR 或 LDS 上限,這些是正當的過濾,而非失敗 [Tensilelite Benchmark Execution](https://amd.atlassian.net/wiki/spaces/SHARK/pages/1405167566)。
4. **分析並整合** – 取出勝出者,產生 equality 與/或 grid-based libraries,透過 TensileMergeLibrary 合併進 hipBLASLt 並重新 build [GEMM Kernel Optimization](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1186895430)。

**TensileLite Characterization Tests** 是降低 tuning 與重構風險的關鍵環節:99 個 `.ambr` golden 檔捕捉了約 29 個模組(codegen、configuration、solution derivation)的現有行為。任何在不更新受影響 golden 的情況下改變行為的 PR,都會無法通過必要的 CI 關卡。這意味著 tuning 變更必須同時通過效能標準與 characterization tests,確保我們不會讓隱藏的行為退步 [TensileLite Characterization Tests — Overview & Snapshot Governance](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1755647079)。

一項原創的策略建議是 **把「optimization tuning」與「coverage tuning」分開**:

* 對某平台上的熱門模型 shape,你可以負擔得起激進的 GA search 與手動調整 YAML。
* 對於廣泛涵蓋(gfx1250/gfx1260 之類的新架構),你會希望採用較保守的 grid 加上穩健的 characterization,才不會落得一堆只在狹窄範圍內可用的脆弱 kernels。

### C.5 除錯與擴充 Codegen

當 codegen 出現異常——結果錯誤、crash 或缺少 kernels——時,有數個層級的工具與文件:

* **擴充資料型別** – complex-datatypes 文件示範如何跨 TensileLite main、TensileCreateLibrary 與 client 新增對新資料型別(complex float/double、MX 型別)的支援,包括對 rocisa、KernelArguments 與 DataTypes helpers 的更新 [Extending Tensilelite Code Generator Support for Complex Datatypes](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1325571391)、[Support for complex datatype in hipBLASLt code generator](https://amd.atlassian.net/browse/SWDEV-543547)。
* **Custom kernels** – **Custom Kernel Integration Guide for hipBLASLt** 與 **Integrating a Custom Kernel into Tensile (for hipBLASLt)** 描述把手寫或外部產生的 kernels,透過 TensileLite libraries 與 equality YAML 引入 hipBLASLt 的端到端工作流程 [Custom Kernel Integration Guide for hipBLASLt](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1732896926)、[Integrating a Custom Kernel into Tensile (for hipBLASLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1524914169)。
* **除錯 assembly** – 數個頁面說明如何執行 TensileLite client、定位產生的 `.s` 檔,並用 ROCgdb 除錯。「Getting Started with assembly kernel」的作業任務,以及展示 ROCgdb 指令的 TensileLite 頁面,特別有幫助 [Getting Started with assembly kernel - Homework Tasks](https://amd.atlassian.net/wiki/spaces/~menghung/pages/191332364)、[TensileLite](https://amd.atlassian.net/wiki/spaces/~marhuang/pages/229539949)。
* **Tuning 錯誤與 JIRA** – 像 **Tensile encountered issues when trying to conduct gemm tune** 這類 ticket,捕捉了常見的 tuning 問題(grid-based tuning 緩慢、rebuild 失敗)及其重現步驟,提供一個關於陷阱與修法的活知識庫 [Tensile encountered issues when trying to conduct gemm tune](https://amd.atlassian.net/browse/SWDEV-524855)。

從負責歸屬的角度看,GEMM optimization team onboarding 文件與 mathlibs component owners 清單,指出 TensileLite codegen 問題該聯絡誰,以及責任如何切分(CodeGen team vs GEMM tuning team vs Solution Selection team) [GEMM Optimization Team On-Boarding](https://amd.atlassian.net/wiki/spaces/MLSE/pages/744196538)、[Process improvements](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1092380686)。

一項特別重要的原創結論是:**除錯與擴充 TensileLite 如今受到 characterization tests 與 snippet/StinkyTofu 基礎設施的約束**。這是件好事:它迫使變更必須伴隨測試與行為快照,降低單一 YAML 或 KernelWriter 微調靜默地讓 GEMM 函式庫大範圍退步的風險。

---

## 6. Cross-Module Navigation & Index Page(跨模組導覽與索引頁面)

### D.1 串接三個模組

這三個模組構成一個 **堆疊**:

* **Module A(hipBLASLt 基礎)** 主要存在於 API 與使用層級,幾乎不涉及 solution index 與 kernels。
* **Module B(solution selection)** 位於 API 與 kernels 的邊界,把問題描述轉譯成 solution index,並控制 equality vs grid vs StreamK vs Origami/Formocast。
* **Module C(TensileLite)** 擁有 Module B 所挑選的那個 kernel pool 的產生與維護。

**GEMM (hipblasLt)** 頁面已經包含一張視覺化的相依關係圖,顯示 hipBLASLt、rocBLAS、TensileLite、CK、rocRoller 等。這份索引只需 **顯著地連結到該圖**,並使用一致的術語(Equality、GridBased、StreamK 等) [GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159)。

Confluence 索引的一個具體導覽模式:

* 頂部橫幅:「Start here」→ GEMM (hipblasLt) + 這份索引。
* 左欄:連結到 **Module A/B/C 頁面**。
* 右欄:**program status 與聯絡人**(GEMM Active Programs、GEMM Programs Status、component owner 清單)。

原創洞見是:**工程師很少從一張白紙開始**;他們帶著一個問題前來(「這個 GEMM 為什麼慢?」)。索引應為此最佳化:一張小型故障排除流程圖可以串連「症狀 → 模組 → 特定文件」,把這份索引從靜態函式庫轉變成一個輕量的決策輔助。

### D.2 集中式 Confluence 索引

中央索引頁面——很可能位於 MLSE space 中 GEMM 或 libraries 之下——應如下結構化:

1. **Executive summary**(一段加上條列,類似本報告的摘要)。
2. **三個模組章節**(A/B/C),各自包含:

    * 在表格中列出 3–5 個最重要的連結(title、audience、last updated、purpose)。
    * 1–2 段說明何時使用此模組。

3. **共用基礎設施**:

    * GEMM (hipblasLt) 中樞。
    * Tuning dashboards(hipBLASLt GEMM Tuning、solution-selection metrics)。
    * Onboarding 與訓練連結。

4. **負責歸屬與聯絡人** – 取自 mathlibs owner 清單與 Shift-Left roles。

維護責任應落在 **ROCm performance 與 GEMM optimization 團隊**,他們已經維護許多被連結的資源 [GEMM Active Programs](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1387220065)、[ROCm Core performance](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1024656521)。一個輕量流程——每季複查,加上每當有大型功能落地(例如新的 MX 資料型別、新架構)時更新——就已足夠。

一項原創建議是整合 **Confluence label queries 與 macros**:例如,索引可以在「Related Materials」章節下自動列出所有被標記為 `hipblaslt-tuning` 或 `tensilelite-snippet` 的頁面,讓它在不必逐一手動整理每份次要文件的情況下保持新鮮。

### D.3 未來擴充

圍繞 hipBLASLt 與 TensileLite 的版圖正快速演進,包含:

* 新的 **資料型別**(MXFP4/6/8 變體、FP8、complex、structured sparsity)。
* 新的 **架構**(gfx1250/gfx1260/MI455 及之後)。
* 新的 **heuristics 與 ML 驅動的選擇**(Formocast、genetic algorithms、Origami 中的 ML 模型) [Create a genetic algorithms driven search for building solution libraries](https://amd.atlassian.net/browse/SWDEV-477426)、[Formocast Design Document (RFC)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1304232451)。

為了跟上,索引應設計成具備 **擴充點**:

* 在不改變核心結構的情況下,新增模組子章節(例如「Mixed-precision & MX datatypes」、「Graph-level GEMM pipelines」)。
* 在 TensileLite 章節下,收納新的 codegen backend 或策略(例如透過 compiled assets 的執行期 codegen、與 AITER 的整合、ML-based kernel generators) [WIP Compiled Assets for Runtime Code Generation](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1703150439)、[GEMM (hipblasLt)](https://amd.atlassian.net/wiki/spaces/MLSE/pages/1368714159)。

一項具前瞻性的原創建議是 **把 GEMM 當成一個跨專案平台** 來看待,而不只是一個函式庫:hipBLASLt、TensileLite、CK、AITER、Triton 以及未來的 codegen 路徑,全都需要共用的索引與共用的術語。本報告可作為那個更廣義「GEMM platform index」的種子,從 hipBLASLt/TensileLite 起步,並隨整合加深而擴展。

---

## 7. 結論

橫跨 AMD 的 ROCm 堆疊,hipBLASLt、其 solution-selection 層,以及 TensileLite codegen,如今構成一個內聚的 GEMM 平台:hipBLASLt 公開一個帶有 fusion 與 mixed precision 的靈活 API;solution selection 把真實世界的問題對應到接近最佳的 kernels;而 TensileLite 則持續改進 kernel pool 與 codegen 基礎設施。圍繞這些元件的文件與工具雖然豐富,卻一向分散。

藉由把它們組織成 **三個模組化的參考章節**,並具備共用 metadata、清晰導覽與明確的負責歸屬,本報告把那些分散的知識體轉化為一個 **可用的內部平台**:工程師能更快 onboard、更有系統地除錯,並在清楚知道該從何處著手(API 使用、solution selection 或 codegen)的情況下調校效能。最強的單一建議很簡單:**把 GEMM (hipblasLt) 頁面加上這份索引,當成一切 GEMM 相關工作的標準入口**,並在每當有新的 heuristics、kernels 或架構落地時保持該中樞更新。如此可確保得來不易的 tuning 洞見與 codegen 進展能跨團隊被善用,而非各自孤立地重新發現。

