# Formocast 的設計目的、使用限制，與研究盲區清單

路徑說明：本檔在 `study_docs/origami/formocast/`。連研究文件用 `../../research/...`，連原始碼用 `../../../shared/...`。

> **一句話：**Formocast 是為了「不上機就用細粒度模擬幫 TensileLite 選/剪 kernel」而生;它準度不錯但**只是模型預測、不是實測**,而且拿去 `ductile-origami-warmstart` 研究用時有一串**必須先知道的盲區**,否則會誤讀實驗結果。

這份是整組文件裡**最需要看的一篇**,尤其若你要在研究實驗中使用 Formocast。建議先讀 [model.md](model.md)、[integration.md](integration.md)。

## 一、設計目的（它為什麼存在）

（來源:內部 Confluence「Formocast Design Document RFC」/「Formocast」overview,見 [../../internal_docs/formocast-design-rfc.md](../../internal_docs/formocast-design-rfc.md)）

- **要解決的問題**:GEMM kernel selection 傳統靠「靜態 solution pool + 人工 tuning」,難以隨新硬體/新 workload 擴展,導致效能次佳、重工、跟不上硬體迭代。
- **做法**:用**硬體模擬**預測 tensilelite GEMM kernel 的效能,選出(一個或數個)預測最快的解——不必窮舉 benchmark。
- **為什麼要比 Origami estimation 細**:它讀得到 `tensile_params_t`(DepthU、PrefetchGlobalRead、DirectToLds、GSU 等 backend 參數),能分辨 estimation 看不出的細節差異;官方對「best-of-pool」的效率,Origami 約 ~90%、Formocast 約 ~95%。
- **量化 uplift**(來源:內部 Confluence,MI350 BF16、約 13K sizes,相對 Origami baseline library):
  - TN 幾何平均 ≈ **105.7%**(約 +5%)。
  - NN ≈ **102.2%**、NT ≈ **103.7%**。
- **目標硬體/範圍**:AMD MI300/MI350、tensilelite 框架、hipblaslt-bench 驗證。

## 二、一般使用限制（不分研究,誰用都要知道）

- **模型 ≠ 真實 GPU**:Formocast 的輸出是**模擬預測**,不是實測 GFLOPS。它的價值是「相對排名」,不是「保證的絕對時間」。
- **early-terminate sentinel 是有限值**:命中 guard 時回 `microSeconds=9,999,999.9`(`hitRate=0`)。它**不是 NaN/Inf**,`isfinite` 為 true。任何「只用非有限判斷有無分數」的程式會**把它誤當成一個(極大的)正常延遲**。細節與 guard 清單見 [model.md](model.md)。
- **guard 非窮舉**:只有那幾類明確不該模擬的組合會回 sentinel;其他不理想組合會回一個「正常但偏差」的預測,不會被擋。
- **per-arch 常數硬編、要校正**:準度依賴 `HardwareConstants`(cache/頻寬/頻率/NumCUs…),每個架構一份、部分要 micro-benchmark 量。上新架構沒填好就會偏(Formocast 最早在 gfx942 開發,gfx9 與 gfx12/13 差異大)。SOP 見 [debugging-and-calibration.md](debugging-and-calibration.md)。
- **estimation 模式不讀 backend metadata**:若你用的是 origami 預設 `estimation`(不是 `simulation`),`tensile_params_t` 不會被讀,兩個只差 DepthU 的 config 會「打平」。要 Formocast 的辨識力,必須確認走 simulation 路徑(見 [integration.md](integration.md))。
- **覆蓋範圍**:目前**只支援 TensileLite**、**主要 non-StreamK**;StreamK/CMS/DTL 支援仍在進行,CMS 預測是已知較弱處。
- **selection time 未最佳化**:比 Origami 慢,不適合對延遲極敏感的 runtime 純選型;實務建議「Origami 上 production、Formocast 做特定 ASIC/workload tuning」。
- **內含 magic number**:模型與常數表裡有硬編數字(內部文件自承),維護時要留意。

## 三、研究盲區清單（給 ductile-origami-warmstart)

`ductile-origami-warmstart` 研究把 Formocast 當成 **label-blind 的 whole-config scorer**:用它替完整 config 打分,再 factorize 成 per-gene 的 Gen0 抽樣偏好。下面這些是**讀實驗結果前必須先懂的盲區**,否則會下錯結論。每點都標了研究文件裡的詳細出處。

> 這些盲區的**機制細節寫在研究 qa 文件**(避免重抄);本節只給「一句話盲區 + 為何危險 + 去哪看」。

1. **「3 個 size」不是統計樣本數**
   - 研究只在 3 個 locked size 上量 Formocast。它們是**條件觀測**,不是 n=3 的統計基礎;真正樣本數是 config 筆數。跨其他 shape 未知(留給 Stage 3)。
   - 詳見 [qa-03 §0.1](../../research/ductile-origami-warmstart/qa/qa-03-s11-factorization-and-metric-design.md)。
2. **label-blind:Formocast 分數不是真值**
   - S11 全程只用 Formocast 預測,**完全不看真實 GFLOPS**;「這個引導對真實 GPU 有沒有用」要到 S12 用 real label 才算數。把 Formocast「準」與「真的變快」劃等號是錯的。
   - 詳見 [qa-03 §0.11](../../research/ductile-origami-warmstart/qa/qa-03-s11-factorization-and-metric-design.md)、[qa-06](../../research/ductile-origami-warmstart/qa/qa-06-origami-formocast-ecosystem-design.md)。
3. **finite sentinel 會污染統計**
   - `9,999,999.9` 是 finite,若當成真實延遲混進排名/平均會嚴重扭曲。研究把它獨立成一種狀態、不當真實值。
   - 詳見 [qa-05 §15.2](../../research/ductile-origami-warmstart/qa/qa-05-controls-and-formocast-rejection-layers-design.md)。
4. **三層 rejection 必須分開記**
   - 「這個 config 沒進 benchmark」可能是 (a) Ductile validity 不合法、(b) Formocast sentinel、(c) runtime PredictionThreshold 落選——三者意義完全不同,混為一談會誤判「Formocast 有沒有用」。
   - 詳見 [qa-05 §15](../../research/ductile-origami-warmstart/qa/qa-05-controls-and-formocast-rejection-layers-design.md)。
5. **marginal factorization 丟掉交互作用 + confounding**
   - 把 whole-config 分數拆成 per-gene 平均(`mu_gv`),**刻意丟掉「哪些參數搭配才好」**的資訊;且某值若常與好隊友共現,功勞會被算到它頭上(confounding)。所以 per-gene 分數只是 first-order main effect,不是因果、不含搭配。
   - 詳見 [qa-03 §0.4 / §0.4b](../../research/ductile-origami-warmstart/qa/qa-03-s11-factorization-and-metric-design.md)。
6. **baseline 驅動抽樣,Formocast 只評分**
   - 研究用 baseline 機率抽 config、Formocast 只負責打分——**不是**用 Formocast 引導抽樣。這是為了讓「其他參數隨機」的邊際前提成立、避免用模型證明模型自己。若誤以為是 Formocast 選要看哪些 config,會誤解結果。
   - 詳見 [qa-03 §0.11](../../research/ductile-origami-warmstart/qa/qa-03-s11-factorization-and-metric-design.md)。
7. **execution attrition ≠ model missingness**
   - config 編不出 kernel(resolver/codegen/compile 失敗)是**工程流失**,不是「Formocast 沒訊號」。研究把兩者嚴格分層(Fraw→Fexec→Fscore)。
   - 詳見 [qa-03 §0.2](../../research/ductile-origami-warmstart/qa/qa-03-s11-factorization-and-metric-design.md)。
8. **「這方法有沒有本質問題」的定位**
   - 因為 Formocast 只給 label-blind、marginal、丟交互作用的訊號,研究線很可能得到「訊號主要在交互作用、per-gene 幫助有限」的**負結果**——但那是合格的 finding、不是方法壞掉,前提是不繞過 diagnostics/shuffle/S12。
   - 詳見 [qa-07 §18.4](../../research/ductile-origami-warmstart/qa/qa-07-value-risks-governance-timeboxes-design.md)。

## 四、什麼該放這裡、什麼留在研究文件

- **屬於本 Formocast 文件(通用設計/限制)**:模型是什麼、estimation vs simulation 差異、sentinel 是 finite、只量特定 shape 是模型使用範圍、三層 rejection 的定義。
- **留在研究 qa(研究專屬,只交叉連結)**:marginal confounding 的公式、七 gate、shrinkage `alpha=32`、shuffle control 構造、baseline 抽樣的理由、Ductile Gen0 hook 的接法。這些是**研究設計**,不是 Formocast 本身的性質。

## 交叉連結

- 模型與 sentinel 機制 → [model.md](model.md)
- dispatch / PredictionThreshold → [integration.md](integration.md)
- Formocast 設計 RFC 原文 → [../../internal_docs/formocast-design-rfc.md](../../internal_docs/formocast-design-rfc.md)
- 研究如何使用 Formocast(生態、辨識力論證)→ [qa-06](../../research/ductile-origami-warmstart/qa/qa-06-origami-formocast-ecosystem-design.md)
- 研究的 factorization/metric 機制 → [qa-03](../../research/ductile-origami-warmstart/qa/qa-03-s11-factorization-and-metric-design.md)
- 研究的 controls 與三層 rejection → [qa-05](../../research/ductile-origami-warmstart/qa/qa-05-controls-and-formocast-rejection-layers-design.md)
- 研究價值/風險與「限制 vs 致命缺陷」 → [qa-07](../../research/ductile-origami-warmstart/qa/qa-07-value-risks-governance-timeboxes-design.md)

## 一句話總結

> **Formocast 是為 TensileLite tuning 設計的細粒度模擬預測器(比 Origami 準但慢);它只是模型預測、sentinel 是 finite、常數要 per-arch 校正;拿去 warmstart 研究時,務必記住 label-blind、只量 3 size、marginal 丟交互作用、三層 rejection 要分開——細節在 qa-03/05/06/07。** 下一篇看 [debugging-and-calibration.md](debugging-and-calibration.md)。
