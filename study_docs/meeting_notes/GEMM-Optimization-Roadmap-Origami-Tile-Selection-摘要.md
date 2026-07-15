# GEMM Optimization Roadmap & Origami Tile Selection Policy — 會議摘要

> 來源：`meeting_notes/GEMM Optimization Roadmap & Origami Tile Selection Policy.docx`（Teams 會議錄影逐字稿）
> 會議時間：2026/05/15，約 31 分 30 秒
> 逐字稿由 Khoddamy, Arash 開啟／結束轉錄
>
> ⚠️ 說明：逐字稿的講者是以「會議室裝置」而非「人名」標記，加上自動轉錄有口語與辨識誤差，因此本摘要在**講者歸屬**與**少數聽寫不清的名詞**上會標明「（推斷）」。技術名詞、API、產品／程式庫名一律保留原文英文，並在第一次出現時用一句話白話解釋。

---

## 0. 先看這一句（會議主題）

這是一場**技術分享 / roadmap 對齊會議**：performance team 向大家報告過去這一年在 **GEMM out-of-the-box（開箱即用）效能**上做的工作，重點放在兩件事——
1. **Origami macro tile tuning**：怎麼把每個 tile 對應的「代表 kernel」調到夠快；
2. **tile selection policy**：在「只能放有限數量 tile」的預算下，用 greedy 演算法**挑出最值得放進 library 的那幾個 tile**。

背後的驅動力是：團隊正準備投入 **450**（下一個 release 版本 / 里程碑，推斷）與**新架構**（會中提到代號 **Grimlock**），想先把這一年的方法論、工具與流程整理清楚，讓它們能延續到新架構與 MI350 library 的改善上。

> 名詞速記：
> - **GEMM** = General Matrix Multiply，一般化矩陣乘法（`D = α·A×B + β·C`），是深度學習與 HPC 最核心的運算，也是這裡所有優化的對象。
> - **kernel** = 真正在 GPU 上跑的那段運算程式。同一個 GEMM 可以用很多支不同 kernel 算，各自只在某些矩陣形狀上最快。
> - **tile / macro tile（MT）** = 一個 workgroup 一次負責算的輸出區塊大小 `(MT_M × MT_N)`，是最關鍵的可調參數。「選 tile」大致等同「選 kernel」。
> - **Origami** = 一個「**不用真的把 kernel 跑一遍，只靠硬體參數＋數學模型估算延遲，就從一堆候選裡挑最快那支**」的分析式（analytical）solution selector。詳見同 repo 的 `origami/README.md`。

---

## 1. 背景脈絡：為什麼現在談這些？

- 團隊去年（約 2025 年 11–12 月）在 **Meta** 客戶的第一波壓力後，開始集中火力做 **Origami 的 out-of-the-box tuning**（讓使用者不做客製 tuning、直接裝好就有好效能的情境）。
- 現在壓力較低、有餘裕，正好把方法整理出來，**為 450 與新架構（Grimlock）做準備**，並可回頭改善 **MI350** 的 library。
- 這場是**總覽 + 第一場深入**；講者提到後面還有「接下來三場」會分別深入各子題，另外隔天還有 **two tower solution selection** 的專場。

---

## 2. Roadmap 總覽（開場 intro，由 Babak 主講，推斷）

開場先把這一年 / 接下來的工作分成幾大塊，之後由不同人分場深入：

1. **Origami / out-of-the-box tuning** — 本場主軸之一，講「macro tile tuning 到底怎麼做」（見 §3）。
2. **Tile selection policy（新架構怎麼選 tile）** — 本場主軸之二，由 Rithwik 講（見 §5）；並可延伸去改善 MI350 library。
3. **Library logic 結構重構** — 目前 library logic 檔案**非常難維護**：每個 solution 佔的行數很多，改一個 PR 很痛苦。
   - 目標：**移除 library logic 裡所有冗餘參數**，只保留**一組 default 參數**；每個 solution 只需記錄**與 default 不同的參數**。
   - 狀態：測試已完成、技術上對所有 library 都可行，但一次全改**風險太高**；計畫**先在 450 導入這個新格式**。
   - 本場沒有專門的 presentation，只在 intro 帶過。
4. **Gem Tuner 工具改版** — 已重構完成、**for 450 可用**；設計成**很容易為新架構加功能 / 加新 class**（要支援另一個架構，大致只要「加一個 parameter class」即可）。
5. **Dashboard（整合平台）** — 本場 intro 的最後一項。把散落的工具整合到**同一個地方**：benchmarking 工具、Gem Tuner、post-processing、以及 **gem analyzer**（由 Hamdy 與 Siavash 開發）。
   - 目的：其他團隊 / 外部使用者要對 GEMM 做事，**直接看這個 dashboard 就好**，上面有所有 model 資料與資訊。
6. **Two tower solution selection** — Julio 主導，隔天專場。等 Gem Tuner 收尾後會投入更多，**目標是在 450 讓它成為 default 的 solution selection**。

---

## 3. 主題一：Origami Macro Tile Tuning（Rithwik 主講）

> 講者自我介紹：Rithwik，加入 AMD 約 8 個月，performance team；此工作由 Parth、Babak、Joel 等人共同貢獻。

### 3.1 先建立直覺：Origami 與 macro tile 的關係

- **Origami 裡有一組 kernel，每支 kernel 對應一個唯一的 "MTDU"**。
  - `MTDU`（逐字稿聽寫為 "macro tile depth view"，**推斷實際是 MacroTile + DepthU**）＝「tile 形狀 `MT_M×MT_N` ＋ K 方向一次處理的深度 `DepthU`」的組合。這正是 kernel 命名裡 `MT128x96x64` 那種編碼（MacroTile 128×96 + DepthU 64）。
  - `DepthU` = K 方向的 unroll 深度；它和 macro tile 一起決定資料重用量與 LDS 用量。
- **一個 MTDU ↔ 一支 kernel，是一對一對應。**
- runtime 時，Origami 會**預測**「對這個問題尺寸，最好的 MTDU 是哪個」，然後用對應那支 kernel。

### 3.2 Macro tile tuning 在解什麼問題？

因為所有被 Origami 對應到某個 tile 的問題，最後都會用那個 tile 的**「代表 kernel」（representative kernel）**去算，所以：

> **目標：讓每個 tile 的代表 kernel，對「所有會被 Origami 對應到它」的尺寸都跑得夠好。**

做法上是**改造 GA 與 Gem Tuner**：
- **GA（genetic algorithm，基因演算法）** = 團隊用來在龐大 kernel 參數空間裡「養一群候選、好的多生、壞的淘汰」搜尋高效解的搜尋引擎（對應 repo 內的 Ductile / GEKO tuning 生態）。
- 原本的 **equality tuning** 是「**針對單一個尺寸**」調到最好（library 裡有 exact / Equality 精確 tune 結果的那種）。
- 這裡改成：**固定一個 macro tile，同時對很多個尺寸一起優化**——把「對應到這個 tile 的多個尺寸」一起餵給 GA，找出對它們整體都好的代表 kernel。

**品質 vs 成本的取捨**：對應到一個 tile 的尺寸選越多，tuning 品質越好，但要跑的 benchmark 越多、越貴。實務上**一個 macro tile 大約用 15 個尺寸**，在**單一 GPU 上約需 2–3 小時**。

### 3.3 完整 workflow（七步）

1. **產生大量問題尺寸**：用簡單的 random size generator，取 16 / 32 / 64 的倍數，組出一批 `(M, N, K)` 尺寸。
2. **呼叫 Origami（有 Python API）做 mapping**：算出每個尺寸「最適合的 tile」是哪個。
3. **挑 N 個尺寸**（通常 15 個）作為某個 tile 的 tuning 集合。
4. **用 GA tune 代表 kernel**，對這 N 個尺寸一起優化。
5. **獨立 benchmark**：拿 tune 好的 kernel，在**另外產生的 100 個尺寸**上量測。**tuning 用的尺寸與 benchmark 用的尺寸完全獨立**（類似 train / test 分離）。
6. **判斷是否值得 merge**：若 **geometric mean（幾何平均）uplift > 3%**，就認為值得併回 Origami。
7. **驗證正確性**：確認 norm error 在可接受範圍，再把這些 kernel 替換進 Origami library。

**成效**：在上一次交付給 **Meta**（"Meta drop"，推斷）中，Origami tuning 雖然昂貴，但**在 100+ 個 tile 上、對 BF16 平均帶來約 8% uplift**。

### 3.4 這一段的關鍵 Q&A（穿插討論）

**Q1：問題尺寸怎麼選？（Ryan / Bryan，推斷）**
提問點：很多 tuning 參數其實和問題尺寸強相關（例如 K 很小時，傾向用較小的 PDR/GSU 類參數）；**你怎麼產生 / 挑輸入資料集，會直接影響 tune 出來的最佳參數**。

答：目前用**「距離」挑點**——從一大堆對應到同一 tile 的尺寸裡，挑出**在 MNK 空間中彼此距離最遠、分布最分散**的一組（本質是 farthest-point / 貪婪最遠取樣），讓 tuning 與 benchmark 的尺寸池夠**多樣**。還會刻意分兩類：**granularity-1 的尺寸**與**非 granularity-1 的尺寸**，兩類組合使用；**K 也用不同值涵蓋**。

**Q2：這根本是「哪些能容忍 regression」的難題（Bryan，推斷）**
- 大家同意這是**很難的問題**：曾發生「tune 完某些尺寸反而變差（regression），因為它們沒被代表到」。
- Bryan 提出**多層（tiered）驗證**的想法，類似 train/test split + 分級：
  - 有一組尺寸是**絕對不能 regress**的（限定的小集合）；
  - 再往下有幾個 tier，例如「這一類不能 regress」「那一類只要不 regress 超過 X% 就可接受，且平均 uplift 要達到某個百分比」。
- 現況被形容為 **"uncharted territory"（未知領域）**：以前**零 regression**，接受與否是簡單的 yes/no；**現在允許 regression 後，要不要收一個 change 變成困難得多的判斷**，必須**排優先級**——哪些可以退、可以退多少，要更 granular。
- Bryan 表示會在 **450** 的場次更完整談這套（原本針對 solution selection，但也可當成一般 library change 的通用品質指標）。

**Q3：如果一開始 macro tile 選錯了呢？（Ryan，推斷）**
提問點：這裡是「**tile 形狀已定，找對應的最佳 kernel**」；但**萬一根本沒有正確的 tile 形狀**呢？會不會存在更好的 tile？尤其在**全新架構（Grimlock）從零開始、沒有任何 library / 先驗知識**時，要怎麼「根據架構特性（指令集、實作方式）決定該用哪些 macro tile size」？
答：**「這正是下一個主題」**（tile selection policy，見 §5）。並補充：這套 out-of-the-box 的初衷是「**不依賴任何特定 model 的知識**」，但業界越來越傾向「**保護 Origami**、確保某些關鍵尺寸不 regress」；團隊的 workflow 很有彈性、可以很快實作，只是還要決定**怎麼實作**。

**Q4：對 Meta / OpenAI 這種大客戶，有沒有固定必跑、保證不 regress 的尺寸集合？**
答：**有，但目前是 ad hoc（臨時性）地跑**那些近期聚焦的高優先 model 尺寸。希望能**把這件事正式化**：集中收到一個中央位置，配上前述 tiered 機制（不能退的 / 能退多少的 / 平均 uplift 要達標的），之後會專門講計畫。

**Q5：用什麼 metric 判斷哪支 kernel 最好？**
提問點：跨 100 個尺寸比較 50–100 支 kernel 時，怎麼排名——是看**平均效能**？**最高的最小值（max-min）**？**最大值**？**最低變異數**？
答：目前是 **GA 的 selection**，用的是**尺寸池的平均（average）效能**當 fitness。討論指出：其他 metric（例如 **max-min**＝最大化最差表現的 kernel、或**最低 variance**）各有利弊；團隊坦言**沒試過別的**、直覺上覺得 average 最合理，但**只要改 GA 的 fitness function 就能很容易換**，歡迎建議。

---

## 4. 主題二：Tile Selection Policy（Rithwik 主講）

### 4.1 為什麼需要「選 tile」？

不可能把「所有可能的 tile」都 tune 出來塞進 library，原因有四：
1. **可能的 tile 數量非常多**。
2. **macro tile tuning 很貴**（一個 tile 就要 2–3 小時，見 §3.2）。
3. **solution selection 時間隨 tile 數量線性增加**——因為 Origami 是對所有 tile 做**線性掃描**來選；tile 越多，runtime 選型越慢。
4. **不是每個 tile 都好**。

> 核心問題：**tile 數量有「預算」上限，如何用有限的 tile 數量榨出最好的整體效能？** → 這就是 tile selection policy。

### 4.2 Greedy 選 tile 的做法

直接窮舉「從一大堆 tile 裡挑 N 個最好組合」會**組合爆炸（combinatorial explosion）**，所以用**貪婪（greedy）**策略：

1. **列舉所有合法 tile**：用 script 產生候選 tile，並用 **TensileLite**（"tensile light"）檢查哪些 tile 合法（能真的產生 kernel）。
2. **建效能矩陣（performance matrix）**：準備一大批問題尺寸（約 **100,000** 個），用 **Origami 預測**每個 tile 對每個問題的效能，得到一個**稠密矩陣**，規模約 **100,000 問題 × ~1,000 kernel**。
3. **選第 1 個 tile**：對每個 tile 把「所有問題的效能」加總 / 平均，挑**平均效能最好**的那個。
4. **選第 2 個 tile（greedy 的核心）**：假設已選 tile I，對每個候選 tile J，逐一問題取 `max(tile_I, tile_J)`（假設 Origami 會替每個問題挑兩者中較好的），再平均，看**相對目前的提升**有多少；掃過所有剩下的 tile，選**提升最大**的那個。
5. **一般化**：已選一組 tile 後，對每個問題先算「目前這組能達到的最大效能」，再看**加入哪個新 tile 能讓整體提升最多**，就選它；反覆進行。

### 4.3 一個關鍵假設（也是限制）

整個 greedy 選 tile（以及前面的 macro tile tuning）都建立在一個假設上：

> **假設：runtime 時 Origami 真的會替每個問題挑到那個「最好的 tile」。**

- 為什麼一定要假設？因為**無法用 hipBLASLt bench（"Plus LT bench"）真的把整個 100,000×1,000 的稠密矩陣跑出來**（太貴），只能靠 Origami 預測。
- 若這個假設對 Origami 不成立，就會「**tile 選對了，但實際跑起來沒那麼好**」。這是**公認的限制**；目前經驗上 Origami 夠準、假設大致成立。
- 討論共識：**沒有這個假設就根本做不下去**，只能盡量把它做到最好；並延伸出一個方向——**回頭改 Origami 的 heuristics，讓它的實際選擇更貼近這個假設**。

### 4.4 模擬結果（BF16，DN layout）

- 以「**擁有全部合法 tile 時能達到的效能**」當作 100% 基準；greedy 曲線顯示：
  - **只加第 1 個 tile ≈ 接近 60%**；
  - **加到 25 個 tile ≈ 88%**；
  - **要到 95% 大約需要 100–150 個 tile**（**高度取決於所用的問題尺寸池**）。
- 現況數字：
  - 目前第一輪只有 **52 個 macro tile 的預算**；預計總量可到約 **78 個**（把某些考量算進去，推斷）。
  - 對 BF16，其實**可以產生多達 370 個 tile**——不需要全用，目的是確保所有 tile 的 tile efficiency 相近，所以先全產生、再看效能；最終由 Origami / live view 決定選哪些。
  - 對 **TF32**，「連 150 都還不夠」（推斷指達到目標效能所需 tile 更多）。

### 4.5 這一段的關鍵 Q&A

**Q：只加不減，會不會累積一堆過時的 tile？（Ryan，推斷）**
提問點：當你加了第 7、第 8 個 tile 後，原本的第 2 個 tile 可能**對任何尺寸都不再是最好**了；你會不會**回頭把它移除**？
答：**目前只加不刪（additive only），不做移除。** 提問者建議：如果有一套 **pruning（剪枝）**機制，就能在選完後**維持較小的 tile 集合**——這樣 runtime 的 selection 時間能保持很短，同時仍有好效能。團隊認同這是個好方向，列為**未來可考慮的 pruning approach**（尤其若之後決定要縮減 tile 數量，就得走這條路）。

---

## 5. 關鍵技術決策 / 結論

- **採用 macro tile tuning 流程**：固定 tile、對多尺寸用 GA 一起優化；以 **geomean uplift > 3%** 為 merge 門檻，並做 norm-error 驗證。實測（上一次 Meta drop）**BF16 平均 +8% / 100+ tiles**。
- **採用 greedy tile selection policy**：用 Origami 預測建 100k×1k 效能矩陣，貪婪地一次加一個「邊際提升最大」的 tile；目前**只加不刪**。
- **library logic 換新格式**：改成「default 參數 + 只記 delta」，**先在 450 導入**（不一次改所有 library，因風險太高）。
- **Gem Tuner 改版完成、for 450 可用**，且設計成容易擴充到新架構（加一個 parameter class）。
- **Dashboard 整合**：benchmarking / Gem Tuner / post-processing / gem analyzer 整併到單一平台，供其他團隊直接使用。
- **Two tower solution selection（Julio）**：**目標在 450 成為 default solution selection**。
- **共同前提**：上述 tuning 與 tile selection 的正確性，**都依賴「Origami 會選到最佳 tile」這個假設**。

---

## 6. 待辦事項 / Action items

> 逐字稿多為口頭承諾，時程多綁在「**450**」，負責人以推斷標註。

- **正式化 regression 保護機制**：把 Meta / OpenAI 等高優先客戶的「必跑尺寸」收進**中央位置**，並設計 **tiered 品質指標**（絕對不能 regress / 可 regress X% / 平均 uplift 需 ≥ Y%）。Bryan（推斷）將在 **450** 場次提出完整計畫。
- **導入新 library logic 格式**：在 **450** roll out「default + delta」格式。
- **收尾 Gem Tuner，再投入 two tower + dashboard**：目標讓 two tower 在 450 成為 default solution selection。
- **試驗其他 GA fitness metric**：除 average 外，評估 **max-min**、**lowest variance** 等（只需改 fitness function）。
- **研究 tile pruning**：加入「移除過時 tile」的剪枝機制，維持小 tile 集合與短 selection 時間。
- **改善 Origami heuristics**：讓 runtime 實際選擇更貼近「選到最佳 tile」的假設。
- **回答新架構 bring-up 問題**：整理「全新架構（Grimlock）從零、無先驗知識時，如何依架構特性決定 macro tile size」的方法論（tile selection policy 已部分回答，架構專屬部分待補）。

---

## 7. 未解決的問題 / Open questions

- **可接受的 regression 界線怎麼定？** 哪些尺寸絕對不能退、其他可退多少——「uncharted territory」，尚無定論。
- **選 kernel 的最佳 metric 是哪個？** average vs max-min vs 最低 variance，尚未實測比較。
- **「Origami 會選到最佳 tile」假設的可靠度？** 已知是限制；若假設不成立，tuning 與 tile selection 的成果都會打折。
- **全新架構從零選 macro tile 的架構專屬方法？** greedy tile selection 提供了框架，但「如何從架構的指令特性推導出候選 tile」仍未完整展開。
- **是否要、以及何時導入 tile pruning？** 目前只加不刪，pruning 僅停留在「好方向」。
- **TF32 的 tile 預算需求？** 提到「連 150 都不夠」，尚未定案要放多少。

---

## 8. 一句話總結

> 這場會議把 performance team 這一年在 **GEMM out-of-the-box 效能**上的兩大方法論講清楚——**用改造過的 GA 對「固定 tile、多尺寸」做 macro tile tuning**，以及**用 greedy 演算法在有限 tile 預算下挑出最有價值的 tile**；兩者都倚賴「**Origami 會選到最佳 tile**」的假設，並把**如何在允許 regression 的新世界裡分級管理品質**、以及 **library logic 重構 / Gem Tuner / dashboard / two tower selection** 一起收斂到 **450 與新架構（Grimlock）** 的準備工作上。
