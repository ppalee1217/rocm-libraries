# S14 —— guided 對 baseline 的結果彙整（跨 shape）

```
document_type: CROSS-SHAPE RESULTS（附屬於 formal report，不可獨立引用）
created: 2026-08-18
shapes: medium（capped P0 = 512 / native P0 = 11,405）、large（capped / native）
seeds: 24001-24005（5 paired）
arms: G = BASELINE（uniform p0） / F = GUIDED（Lock-B capped p1）
run_root_host: /data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-baseline
judging_rule: measurement_design.md §G.3.1（NULL-AS-NOISE-BASELINE-20260818）
gate_verdict: 本檔承載（owner 2026-08-18 指定；原承載者 full-ga-baseline-vs-guided-outcome-report.md
#   已解除授權）。三項 margin-free 子判準的計數見 §5.4。
completeness: 四塊的 G/G′ 與 F/F′ null 皆已補齊（medium capped 兩個 null 於 2026-08-17，
#   medium native 與 large 四個 null 於 2026-08-18）；仍缺的見 §5.2
```

**標點慣例：** 本檔使用全形逗號與全形括號，與 `s14-medium-report.md` 一致。

---

## 0. 這份文件是什麼

**它彙整四個區塊的 `F/G` 讀數，以及每一個讀數各自的噪音基準。**
`F/G` 是 gflops 比，**> 1 讀作 guided 較快**（worker `remeasure_interleaved_champion*.py`
的 `median_ratio = f_median / g_median`）。

**判讀規則（owner 授權，2026-08-18，`NULL-AS-NOISE-BASELINE-20260818`）：**
以 null ratio 當噪音基準，**並列報告所有可得的尺度，不合成單一裁決，不設倍數門檻**。
理由是實測上「用哪一把尺會改變答案」——這件事本身是結果的一部分（§1）。

**這份文件不做什麼：**

- ~~**不陳述任何 S14 gate 判定。**~~ **⚠ 2026-08-18 變更:** 原承載者
  `staged/full-ga-baseline-vs-guided-outcome-report.md` **已由 owner 解除授權**，
  gate 判定改由**本檔**承載。三項子判準的計數與判定見 **§5.4**。
  本檔仍**不**把 final ratio 當成 gate 成分（見 §5.4 的說明）。
- **不指定任何 measurement of record。** medium 的 final ratio 是否以 pilot401 為 record，
  是 `PENDING_HUMAN_DECISION`（`s14-medium-report.md` §17）。
- **不合併不同區塊的讀數。** 四塊用的是**四組不同的 champion**（§5.1）。

**儀器修復本身**（medium 的 denoise 前後對照）不在本檔，在 `s14-medium-report.md` §18。
**large 的兩支診斷探針**（`m6`、`race_m3`）在 `s14-large-report.md` §10.7b。

---

## 1. medium capped（P0 = 512，stage3 樹）

**來源：** `medium_pilot401/results/C03_nw1400_rbs401/` 與 `C03CONF_nw1400_rbs401/`，
各 5 seed × 12 window，`nw = 1400 / RBS = 401`（修復後的儀器）。

> **⚠ 來源身分。** `PILOT401_MANIFEST.json` 自我標記為
> `"status": "PILOT -- not an endpoint, not a campaign"`。
> **owner 於 2026-08-18 授權呈現這個讀數，但未指定它為 measurement of record**；
> `measurement_design.md` §A.5 的第五個 campaign **從未執行**。

| seed | `ln(F/G)` | `F/G` | ÷ G/G′ sd | ÷ F/F′ sd | ÷ 跨 session 0.0097 | ÷ 自身 sd |
|---:|---:|---:|---:|---:|---:|---:|
| 24001 | −0.00045 | 0.9996 | 0.1 | 0.1 | 0.0 | 0.1 |
| 24002 | **+0.06024** | **1.0621** | 25.3 | 35.0 | 6.2 | 14.8 |
| 24003 | +0.01336 | 1.0135 | 5.9 | 5.3 | **1.4** | 5.6 |
| 24004 | **+0.06142** | **1.0633** | 39.5 | **3.0** | 6.3 | 3.4 |
| 24005 | −0.00257 | 0.9974 | 0.5 | 0.9 | 0.3 | 0.7 |

**中位 `F/G` = 1.0135，`F/G > 1` 為 3/5。**

**怎麼讀：**
**24002 在所有四把尺下都明顯為正。24003 與 24004 都是正的，但幅度隨尺度而變**
——24003 在跨 session 尺度下只剩 1.4；24004 在 F/F′ 尺度下只剩 3.0。
**24001 與 24005 在所有尺度下都貼零。**
**沒有任何 seed 在任何尺度下顯示 guided 有害。**

**四把尺的性質與限制**（完整版見 `measurement_design.md` §G.3.1 與 `s14-medium-report.md` §18.3）：

| 尺 | 限制 |
|---|---|
| **G/G′ null** sd | **結構上永遠不載入 arm F 那顆 kernel。** seed 24004 的 G/G′ sd 是 `0.00155`，真實對比自己的 sd 是 `0.01807`——**差 11.6 倍**。⇒ 只用它會系統性高估顯著性 |
| **F/F′ null** sd | 註冊角色是離散度儀器。⚠ 它與 G/G′ **不是同一 session**（13:44–13:55 對 15:29–15:39），所以 F/F′ ÷ G/G′ = 13.3 倍**內含「同一儀器狀態」的假設** |
| **跨 session rms 0.0097** | ⚠ **取自舊儀器**（design §G.2.4 的 native C1↔C2，`321/4096`）。**修好的儀器上一組跨 session 資料都沒有**，這是外插 |
| **自身跨窗 sd** | 不含 session 間成分 |

⚠ **兩批不是獨立的：** `C03` 末窗收於 09:10:33、`C03CONF` 首窗起於 **09:19:48**，**相隔約 9 分 15 秒、同一 session**。
依 `NO-SEPARATION-20260817` 的代價條款，**全部只涵蓋 fast 層，slow 層仍為 `NOT_EVALUATED`**。

---

## 2. medium native（P0 = 11,405，stage5 樹）

**來源：** `medium_pilot401/results/STAGE2_NATIVE_nw1400_rbs401/`（效應）、
`N8_NATIVE_GVSG_nw1400_rbs401/`（G/G′ null）、`N8b_NATIVE_FFNULL_nw1400_rbs401/`（F/F′ null），
各 5 seed × 12 window，`nw = 1400 / RBS = 401`。
> **⚠ 來源身分。** `STAGE2_NATIVE` 與兩個 null 同屬 `PILOT401_MANIFEST.json` 的 **pilot** 範疇
> （`"status": "PILOT -- not an endpoint, not a campaign"`）；`measurement_design.md` §A.5 的
> 第五個 campaign **從未執行**。owner 於 2026-08-18 授權呈現這些讀數，未指定其為 measurement of record。

**⚠ 三個 cell 不同日:** 效應 cell `STAGE2_NATIVE` 執行於 **2026-08-17 15:42–15:52**；
兩個 null 執行於 **2026-08-18 06:51–07:15**。下表的「÷ null sd」兩欄因此是**跨日的比值**，
見 §5.2 的跨 session 揭露。

| seed | `ln(F/G)` | `F/G` | ÷ G/G′ sd | ÷ F/F′ sd | ÷ 自身 sd |
|---:|---:|---:|---:|---:|---:|
| 24001 | −0.00306 | 0.9969 | 0.50 | 0.03 | 0.74 |
| 24002 | +0.00363 | 1.0036 | 0.56 | 0.05 | 1.32 |
| 24003 | +0.02696 | 1.0273 | **18.24** | **1.57** | 17.50 |
| 24004 | **−0.12477** | **0.8827** | **8.27** | **1.84** | 86.68 |
| 24005 | +0.06414 | 1.0662 | **6.39** | **0.73** | 4.20 |

**兩把 null 尺相差一個數量級，而它們給出相反的答案。**

| seed | G/G′ 中心 | G/G′ sd | F/F′ 中心 | F/F′ sd | F/F′ ÷ G/G′ |
|---:|---:|---:|---:|---:|---:|
| 24001 | −0.00081 | 0.00609 | **+0.03736** | **0.09531** | **15.7×** |
| 24002 | −0.00107 | 0.00654 | **+0.02205** | **0.07546** | **11.5×** |
| 24003 | −0.00054 | 0.00148 | −0.00456 | 0.01717 | **11.6×** |
| 24004 | +0.00063 | 0.01510 | **+0.01889** | **0.06786** | **4.5×** |
| 24005 | +0.00091 | 0.01003 | **+0.02512** | **0.08779** | **8.8×** |

**怎麼讀 —— 這一塊不可判讀，而且不是因為缺資料。**

**G/G′ null 是乾淨的：** 五個中心都在 **±0.0011** 內，⇒ 兩臂同為 native baseline 時儀器無偏。
**F/F′ null 不是：** 真值恰為 1.0，中心卻跑到 **+1.9 % 到 +3.7 %**（五個中四個），
sd 是 **1.7 % 到 9.5 %**，比 G/G′ 大 **4.5 到 15.7 倍**。
**兩臂裝的都是同一顆 kernel，唯一的差別是量測位置** ——
所以這個偏移與離散度**屬於 native 的 guided kernel，不屬於儀器**。

**後果：以 F/F′ 為尺，五個 seed 沒有一個超過 2 倍。**
包含看起來最大的 24004（−12.5 %，只有 **1.84×**）與 24005（+6.4 %，**0.73×**）。
**以 G/G′ 為尺，同樣三個 seed 分別是 18.2×、8.3×、6.4×，看起來全都極顯著。**
**⇒ 這一塊的結論完全由「用哪一把尺」決定，因此不下判讀。**

> **⚠ 這正是只補 G/G′ 會看不見的東西。** G/G′ 兩臂都是 baseline 樹，
> **結構上永遠不載入 native 的 guided kernel**，而噪音正好在那顆 kernel 上。
> 若本檔只用 G/G′，§2 會寫出「24003 是 18 倍、24004 是 8 倍」——**那站不住**。

**dropout：** 效應 cell **6.55 %**（通過 P3），但 **G/G′ null 是 15.60 %、F/F′ null 是 18.69 %，兩個都不過**。
**一個沒有任何真實效應的建構，汙染率是效應 cell 的 2.4 到 2.9 倍** —— 成因 `NOT_EVALUATED`。

## 3. large capped（P0 = 512，stage3 樹）

**來源：** 端點為 `stage3_baseline/seed_*/large/champion_interleaved.json`（單窗，2026-08-12）；
噪音尺為 2026-08-18 新跑的三個 cell —— `large_xwindow/results/m6_capped/`（跨窗 real）、
`gvsg_capped/`（G/G′ null）、`ffnull_capped/`（F/F′ null），各 6 window × 5 seed。
**未修改的 7× 儀器**（`nw = 321`、`RBS = 0`、`--start-arm F`）。

> **⚠ 來源身分。** 三個噪音尺 cell 帶 `LARGE_XWINDOW_MANIFEST.json` 的 `claim_boundary`：
> 「do not replace the endpoint of record, **are not averaged into it**, and do not move any shape's S14 status」。
> 它們是重現性與偏差檢查，**不進 gate、不取代端點**。

| seed | 端點 `ln(F/G)` | `F/G` | ÷ G/G′ sd | ÷ F/F′ sd | ÷ 跨窗 sd | 三尺一致？ |
|---:|---:|---:|---:|---:|---:|---|
| 24001 | **−0.07488** | **0.9279** | **6.67** | **3.25** | **3.80** | **一致：劣** |
| 24002 | +0.01191 | 1.0120 | 0.44 | 0.55 | 0.52 | 一致：平 |
| 24003 | +0.06037 | 1.0622 | 2.32 | 3.08 | 4.25 | **不一致** |
| 24004 | **−0.04853** | **0.9526** | **6.04** | **3.57** | **4.06** | **一致：劣** |
| 24005 | +0.00064 | 1.0006 | 0.04 | 0.05 | 0.02 | 一致：平 |

**兩個 null 的中心與離散度：**

| seed | G/G′ 中心 | G/G′ sd | F/F′ 中心 | F/F′ sd | F/F′ ÷ G/G′ | 跨窗 sd |
|---:|---:|---:|---:|---:|---:|---:|
| 24001 | −0.00198 | 0.01123 | −0.00090 | 0.02304 | 2.05× | 0.01970 |
| 24002 | +0.00538 | 0.02717 | −0.00477 | 0.02169 | 0.80× | 0.02275 |
| 24003 | −0.01368 | 0.02602 | −0.00395 | 0.01961 | 0.75× | 0.01420 |
| 24004 | +0.00170 | 0.00803 | +0.00072 | 0.01360 | 1.69× | 0.01195 |
| 24005 | −0.01182 | 0.01534 | +0.00402 | 0.01251 | 0.82× | 0.02742 |

**怎麼讀：**
**兩個 seed（24001 與 24004）在全部三把尺下都超過 3 倍，而且是負的 —— guided 明顯較慢。**
**沒有任何一個 seed 在全部三把尺下明顯較快。**
24003（+6.0 %）在跨窗與 F/F′ 尺下過 3 倍、在 G/G′ 下只有 2.32，**隨尺度而變**。
24002 與 24005 在三把尺下都貼零。

> **⚠ 這一塊的裸符號會誤導。** 端點的 `F/G > 1` 計數是 **3/5**，
> 但那三個「正」裡有兩個（24002、24005）在噪音之內，而兩個「負」都是穩定的實質退步。
> **裸計數與噪音尺給出相反的印象。**

**這一塊的 null 表現正常：** 中心 −0.014 至 +0.005，F/F′ ÷ G/G′ 的 sd 比是 **0.75–2.05**
——**沒有 §2 那種數量級爆炸**，也就是說 large capped 的 guided kernel 沒有那個問題。

> **⚠ 並列另一把尺 —— pinned `η_large`。**
> 依預註冊的 non-regression 判準 `F ≥ G·e^{−η_large}`（`η_large = 0.12285`），
> large capped 的五個 seed **全部通過（5/5）**；改用窗內經驗 `η = 0.0269` 則為 **3/5**；
> improvement 判準為 **0/5**。
> ⚠ 該 5/5 所依賴的常數**尚未對照它所 gate 的量測驗證過**（`s14-large-report.md` §5.3），
> 且 `η_s` 已於 2026-08-14 移出 gate 成分。**它絕不可單獨引用。**
> **這把尺與上表的三把噪音尺給出相反的印象** —— 同一批端點，pinned margin 下 5/5 通過，
> 噪音尺下兩個 seed 一致較慢。**兩者都要報，本檔不代為裁決。**

**dropout：** 三個 6 窗 cell 分別是 **24.52 % / 24.05 % / 22.38 %**（real / G/G′ / F/F′），
而**單窗端點只有 1.43 %**（0.95 判準；0.80 判準下為 0/70）——差約 17 倍。
**三種建構的值幾乎相同 ⇒ 這個升高屬於「六窗背靠背」這個執行情境，不屬於任何一顆 kernel 或任何一種建構。**
成因 `NOT_EVALUATED`。⚠ **因此跨窗尺對單窗端點是偏保守的**，
用它判「不顯著」要留意；上表的兩個「一致：劣」在三把尺下都成立，不依賴這一把。

## 4. large native（P0 = 11,405，stage5 樹）

**來源：** 端點為 `stage5_native_baseline/seed_*/large/champion_interleaved.json`（單窗，2026-08-17）；
噪音尺為 `large_xwindow/results/m6/`（跨窗 real，2026-08-17）與 2026-08-18 新跑的
`gvsg_native/`（G/G′ null）、`ffnull_native/`（F/F′ null），各 6 window × 5 seed。

> **⚠ 來源身分。** 三個噪音尺 cell 帶 `LARGE_XWINDOW_MANIFEST.json` 的 `claim_boundary`：
> 「do not replace the endpoint of record, **are not averaged into it**, and do not move any shape's S14 status」。
> **⚠ 端點與尺不同日:** 端點 2026-08-17 13:13–13:27；兩個 null 2026-08-18 08:42–09:04。見 §5.2。

| seed | 端點 `ln(F/G)` | `F/G` | ÷ G/G′ sd | ÷ F/F′ sd | ÷ 跨窗 sd | 三尺一致？ |
|---:|---:|---:|---:|---:|---:|---|
| 24001 | +0.00670 | 1.0067 | 0.76 | 0.91 | 0.31 | 一致：平 |
| 24002 | **+0.15026** | **1.1621** | **8.69** | **5.24** | **9.77** | **一致：優** |
| 24003 | −0.04147 | 0.9594 | 2.26 | 1.96 | 3.31 | **不一致** |
| 24004 | −0.01816 | 0.9820 | 2.98 | 1.26 | 0.89 | **不一致** |
| 24005 | −0.00301 | 0.9970 | 0.21 | 0.14 | 0.17 | 一致：平 |

**兩個 null 的中心與離散度：**

| seed | G/G′ 中心 | F/F′ 中心 | 跨窗 sd（m6） | m6 六窗平均 |
|---:|---:|---:|---:|---:|
| 24001 | −0.01421 | +0.00338 | 0.02152 | +0.00962 |
| 24002 | +0.00520 | −0.01035 | 0.01537 | +0.14475 |
| 24003 | −0.00030 | −0.00143 | 0.01252 | −0.02563 |
| 24004 | −0.00391 | +0.00044 | 0.02036 | −0.02470 |
| 24005 | −0.00733 | +0.01532 | 0.01721 | +0.01568 |

**怎麼讀：**
**只有 24002 在全部三把尺下都明顯為正**（8.7 / 5.2 / 9.8）。
**沒有任何 seed 在全部三把尺下明顯為負。**
24003 與 24004 隨尺度而變（24003 在跨窗尺下 3.3、在 F/F′ 下 2.0;
24004 在 G/G′ 下 3.0、在跨窗尺下只有 0.9）。24001 與 24005 三尺皆貼零。

> **⚠ 24002 的 +16 % 有一部分來自 baseline 臂自己，不是 guided 變好。**
> 該 seed 的 baseline champion 重測是 **498,236 GFLOP/s**，GA 搜尋期記錄是 **565,845**
> ——**低 11.95 %**。**這不是量測失誤：498,236 落在 `m6` 六個 window 的 485,541–499,076 之內**（六窗中位數 494,971，端點落在區間上緣）。
> ⇒ 是 baseline 的 GA 在搜尋期拿到偏高讀數（winner's curse）。詳見 `s14-large-report.md` §10.7b.2。

**兩個 null 的中心都在 ±0.015 內**；sd 比 **0.84 – 2.36×**（24004 的 2.36× 高於 large capped 的上限 2.05×），
沒有 §2 那種數量級問題。

> **⚠ 「÷ 跨窗 sd」那一欄要保留看待，不可單獨用來判「不顯著」。**
> `m6` 自己的 pooled dropout 是 **8.10 %**，而 large native 端點是 **2 / 70 = 2.86 %**
> ——**m6 比它要審判的對象髒約 2.8 倍**，拿它當分母偏保守，會把真效應誤判成雜訊
> （`s14-large-report.md` §10.7b.1 的明文限制）。
> §3 對 large capped 已有對等警語；此處補上。
> **上表的判讀因此以 G/G′ 與 F/F′ 兩把尺為主，跨窗尺為佐證。**

> **⚠ 並列另一把尺 —— pinned `η_large`。**
> 依預註冊的 non-regression 判準 `F ≥ G·e^{−η_large}`（`η_large = 0.12285`），
> large 的五個 seed **全部通過（5/5）**；改用窗內經驗 `η = 0.0269` 則為 **3/5**；
> improvement 判準 `F > G·(1+δ)` 為 **0/5**（capped）。
> ⚠ 該 5/5 所依賴的常數**尚未對照它所 gate 的量測驗證過**
> （`s14-large-report.md` §5.3），且 `η_s` 已於 2026-08-14 移出 gate 成分。
> **它絕不可單獨引用**（同檔 §5.5 的 standing rule）。

**dropout：** 端點 **2.86 %**（單窗，0.95 判準）；三個 6 窗 cell 是 **8.10 % / 22.14 % / 25.00 %**
（real / G/G′ / F/F′）。⚠ **與 §3 不同，這裡三種建構的值差很多**（8 % 對 22–25 %），
所以 large native 的升高**不能**單用「六窗背靠背」解釋。成因 `NOT_EVALUATED`。

---

## 5. 四塊橫向

### 5.1 總表 —— 每一塊在「全部可得尺度下都一致」的判讀

| 區塊 | 儀器／彙整 | 中位 `F/G` | 裸計數 `F/G > 1` | **一致為優** | **一致為劣** | 一致為平 | 不一致 |
|---|---|---:|---:|---|---|---|---|
| medium capped | 修復後 `1400/401`，12 窗跨窗平均，`start_arm G` | 1.0135 | 3/5 | **24002** | 無 | 24001、24005 | 24003、24004 |
| medium native | 修復後 `1400/401`，12 窗跨窗平均，`start_arm G` | 1.0036 | 3/5 | **無** | 無 | 24001、24002 | 24003、24004、24005 |
| large capped | **未修改** `321/RBS 0`，**單窗** median-of-7，`start_arm F` | 1.0006 | 3/5 | **無** | **24001、24004** | 24002、24005 | 24003 |
| large native | **未修改** `321/RBS 0`，**單窗** median-of-7，`start_arm F` | 0.9970 | 2/5 | **24002** | 無 | 24001、24005 | 24003、24004 |

⚠ **「中位 `F/G`」在四列不是同一個量。** medium 兩列是修復後儀器的 12 窗跨窗平均（successor 讀數）；
large 兩列是未修改儀器的單窗 median-of-7（預註冊端點）。**不可跨列比較大小。**

**這張表是本檔的主要輸出。三件事：**

1. **裸計數在四塊裡都是 2/5 或 3/5，但它與噪音尺給出的圖像不一致。**
   最明顯的是 **large capped**：裸計數 3/5 為正，但那三個「正」裡有兩個在噪音內，
   而**兩個「負」在全部三把尺下都超過 3 倍**——那一塊實際上是**只有退步、沒有進步**。
2. **只有兩個 seed（都是 24002）在任何區塊裡達到「全尺一致為優」**，
   而 large native 的那一個有 winner's curse 成分（§4）。
3. **medium native 一個都判不出來**，原因不是缺資料，是**兩把 null 尺相差一個數量級**（§2）。

**四塊不可合併成一個數字**——見 §5.3。

### 5.2 完整度

| 區塊 | real 跨窗 | G/G′ null | F/F′ null | 自己的跨 session 尺度 |
|---|---|---|---|---|
| medium capped | ✓ `C03` + `C03CONF` | ✓ `N7_GVSG` | ✓ `N7b_FFNULL` | **✗ 借自舊儀器** |
| medium native | ✓ `STAGE2_NATIVE` | ✓ `N8_NATIVE_GVSG` | ✓ `N8b_NATIVE_FFNULL` | **✗** |
| large capped | ✓ `m6_capped` | ✓ `gvsg_capped` | ✓ `ffnull_capped` | **✗** |
| large native | ✓ `m6` | ✓ `gvsg_native` | ✓ `ffnull_native` | **✗** |

**owner 於 2026-08-18 裁決的七項已全部執行完畢**（六個 null + large capped 跨窗 real）。

**唯一仍然全面缺席的是跨 session（跨日）尺度 —— 但情況比「缺席」更需要說明。**

**兩層陳述，兩層都成立：**

**(i) 每一個 cell 內部只涵蓋 fast 層。** 該 cell 的 12（或 6）個 window 是同一天背靠背執行
（`NO-SEPARATION-20260817` 的代價條款），所以 cell 內的 sd 不含 session 間漂移。

**(ii) ⚠ 但四塊裡有三塊，效應與它的噪音尺根本不在同一天：**

| 區塊 | 效應／端點量於 | 噪音尺量於 | 分隔 |
|---|---|---|---|
| medium capped | 2026-08-17 08:59–09:31 | 2026-08-17 13:44–15:39 | **同日**（唯一） |
| medium native | 2026-08-17 15:42–15:52 | 2026-08-18 06:51–07:15 | 約 15 小時 |
| large capped | **2026-08-12 00:22–01:50** | 2026-08-18 07:18–08:20 | **約 6 天** |
| large native | 2026-08-17 13:11–13:27 | 2026-08-18 08:24–09:04 | 約 20 小時 |

⇒ **§2 / §3 / §4 的每一個「÷ 尺」倍數，分子與分母不在同一 session。**
那段期間的漂移**與 kernel 相依噪音無法分離**，所以那些倍數是**上界不明**的，
而不只是「缺 slow 層」。**只有 §1（medium capped）是同 session 內的判讀。**

owner 於 2026-08-18 裁決：**揭露，不重測。** 本段即為該揭露。
§1 用的 `0.0097` 另是從**舊儀器**外插來的（design §G.2.4 的 native C1↔C2），其餘三塊連外插來源都沒有。

### 5.3 為什麼不可合併

**四塊量的是四組不同的 champion。** 以 seed 24004 為例，medium capped 是
`G = c8db13d2…` / `F = fa7d6353…`，medium native 是 `G = 397d9f67…` / `F = 14d7349c…`
——四臂全不相同。capped 與 native 是**兩次不同的 GA 執行**（P0 = 512 對 11,405），
產出不同的 champion 對。
⇒ **逐 seed 排序在四塊之間對不上，是設計上的預期，不需要機制解釋，不得記為待解現象。**

**噪音本身也是 kernel 相依的，不是儀器相依的**——這是本輪最實質的發現：

| 區塊 | F/F′ sd ÷ G/G′ sd | 讀法 |
|---|---|---|
| medium capped | **0.52 – 13.33×** | **只有 seed 24004** 的 guided kernel 特別吵（13.33×）；**24002 與 24005 的 guided kernel 反而比 baseline 安靜**（0.72×、0.52×） |
| **medium native** | **4.5 – 15.7×** | **sd 是五個 seed 全部**吵；**中心是五個中四個**偏 +1.9 % 到 +3.7 %（24003 為 −0.456 %）|
| large capped | 0.75 – 2.05× | 兩臂相當，無異常 |
| large native | **0.84 – 2.36×** | 無 medium native 那個**數量級**的爆炸（≤ 2.4× 對 4.5–15.7×）。⚠ 但 **24004 的 2.36× 高於 large capped 的上限 2.05×** |

**⇒ 一把 null 尺不足以描述儀器；必須兩把都有，而且結論可能完全取決於用哪一把。**

⚠ **量測順序在兩個 shape 之間相反：** medium 全部 `('G','F')`、large 全部 `('F','G')`，
而 `first_arm` 設在 repeat 迴圈之外（design §G.3），**配對只會把順序效應凍結，不會平均掉**。
**medium 的順序觀測在數學上不可外推到 large。**

### 5.4 S14 gate 判定（owner 2026-08-18 指定本檔為承載者）

> **⚠ 權威變更。** 原承載者 `staged/full-ga-baseline-vs-guided-outcome-report.md`
> **已由 owner 解除授權**。gate 判定自 2026-08-18 起由本節承載。

**現行 gate = {Gen0 增量、gen-10 增量、AUC 差} 三項連言，各需 ≥4/5 對為正。**

> **gate 成分數的完整交代（必須連著讀）：**
> 預註冊設計檔 `s14-stage1-full-ga-outcome-design.md:226` 定義的是**四項連言**，
> 第四項為 `final ratio ≥ e^{−η_s}`。`ETA-MARGIN-REMOVED-20260814`（owner 2026-08-14）
> 把 per-shape noise margin `η_s` 與該第四項**一併移出 gate 成分**，且**未登記任何替代門檻**。
> **⚠ 但該 token 尚未落到預註冊設計檔本身**（在該檔命中 0 次；
> index §2 的 ledger 註明「owner to amend separately」），所以那份文件讀起來仍是四項。
> **⇒ 現行判定以三項為準；預註冊文本待修訂。**
>
> **`final ratio` 並未被移除為必報量** —— ledger 明文「still **reported**（direction + effect size）」。
> 它的判讀方法由 `NULL-AS-NOISE-BASELINE-20260818` 指定：**以 null ratio 為噪音基準、
> 多尺度並列、不設倍數門檻**。§1–§4 就是那個報告。
> **報出方向與效應量不是 pass，絕不可寫成 pass。**

**三項子判準的逐塊計數**（讀自 `trajectory.jsonl`，不經 7× 量測路徑，量測缺陷碰不到）：

| 子判準 | medium capped | medium native | large capped | large native | 要求 |
|---|---:|---:|---:|---:|---|
| Gen0 best | **3/5** | 2/5 | **1/5** | 3/5 | ≥4/5 |
| gen-10 best | **3/5** | 1/5 | **2/5** | 1/5 | ≥4/5 |
| AUC | **3/5** | 3/5 | **3/5** | 2/5 | ≥4/5 |

**判定：gate `NOT MET`。** 兩個 confirmatory shape（medium、large）在 capped 條件下
的三項子判準分別是 3/5, 3/5, 3/5 與 1/5, 2/5, 3/5 —— **十二格沒有一格達到 ≥4/5**。

⚠ **native 兩列是 `NATIVE-P0-ROBUSTNESS-20260811` 的 robustness addendum，不是 gate 成分**
（gate 定義於 capped 條件）。列出僅供對照。

**可用的否定措辭，逐字：**
> the amended sparse prior, as configured, **did not meet the pre-registered directional gate**

**⚠ 絕不可寫成 "no effect"。** `NOT MET ≠ 沒有效果`。

來源：`s14-medium-report.md` §5.1、`s14-large-report.md` §4.2 與表 N2、§10.7 表 N2。

---

## 6. 本檔可說與不可說

**可說：**

- **S14 gate 判定：`NOT MET`**（§5.4；三項子判準十二格無一達 ≥4/5）。
  逐字措辭：「the amended sparse prior, as configured, **did not meet the pre-registered directional gate**」。
- 上列四塊各自的 `F/G` 讀數，以及每一個讀數對每一把可得尺度的比值。
- **§5.1 的一致性判讀**：哪些 seed 在全部尺度下都是優／劣／平，哪些隨尺度而變。
- **large capped 在兩個 seed 上一致地較慢**（24001、24004，三尺皆 > 3 倍）。
  ⚠ 同一批端點在 pinned `η_large` 下卻是 **5/5 non-regression 通過** —— **兩者都要報**（§3）。
- **medium native 目前判不出任何一個 seed**，而原因是兩把 null 尺相差一個數量級。
  ⚠ 該塊的 F/F′ null 有兩種未分離的來源：native guided kernel 本身不穩，
  或該次執行受干擾（其 dropout 18.69 % 對兩者相容）。**本檔不裁決。**
- **噪音是 kernel 相依的**：F/F′ ÷ G/G′ 的 sd 比在 medium native 上是 4.5–15.7 倍，
  在 large capped 上只有 0.75–2.05 倍、large native 0.84–2.36 倍、medium capped 0.52–13.33 倍
  （後者只有 24004 一個 seed 吵，其餘反而較安靜）。
- 每一塊的 dropout，以及「跨窗 cell 比單窗端點髒」這個現象（成因 `NOT_EVALUATED`）。

**不可說：**

- **「guidance 對某個 shape 有效或無效」作為超出 §5.4 的宣稱。** §5.4 只說 gate `NOT MET`；
  **`NOT MET ≠ 沒有效果`**，也不等於「模型沒用」。
- **把 `final ratio` 的任何讀數寫成「通過」。** 它自 2026-08-14 起不是 gate 成分、無門檻；
  **報出方向與效應量不是 pass。**
- **把 native 兩列當成 gate 成分。** 它們是 robustness addendum（§5.4）。
- **「這是 medium 的 measurement of record」**——`PENDING_HUMAN_DECISION`。
- **把四塊合併成一個數字**，或用一塊的噪音尺去判另一塊，或把 medium 的順序效應外推到 large。
- **「medium native 沒有效應」**——`NOT_EVALUATED ≠ 沒有效果`。那一塊是**判不出來**，不是判出「沒有」。
- **單獨引用 large 的 5/5 non-regression。** 它所依賴的 `η_large` 尚未對照它所 gate 的量測驗證過，
  且該 margin 已於 2026-08-14 退役。
- **「量測缺陷已經解決」**——四塊的效應與噪音尺有三塊跨日，比值上界不明（§5.2）。
- **任何關於「為什麼 medium native 的 guided kernel 特別吵」「為什麼跨窗 cell 比端點髒」
  「`race_m3` 的 12 % 兩群分裂」的機制敘述**——三者都只有現象、沒有根因。
