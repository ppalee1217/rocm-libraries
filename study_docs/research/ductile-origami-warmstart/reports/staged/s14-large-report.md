> **⚠ 本檔是 per-shape 附冊,不是 S14 的結論。** 本檔是 **large shape 附冊**,
> 承載該 shape 的詳細實驗記錄。
> S14 的 gate 是跨 shape 的**連言**,因此只有跨 shape 的文件能陳述「S14 過了沒有」。
> **⚠ 2026-08-18 權威變更:** 原文指向 `full-ga-baseline-vs-guided-outcome-report.md`
> 為「S14 唯一 formal report」。**該檔已由 owner 解除授權。**
> gate 判定現由 [`s14-guided-results.md`](s14-guided-results.md) **§5.4** 承載。
> **本檔不得被讀成、也不得被引用為 S14 outcome 的陳述。** 本檔只逐項報告 large 的
> 觀測值與預註冊分項計數;**不下 gate 判定**。
>
> **權威順序。** 本檔為 non-authority checkpoint 附冊。若與
> [research charter](../../../surrogate-dse-plan.md)、
> [experiment plan](../../../ductile-origami-warmstart-experiment-plan.md)、
> [`../../s14-stage1-full-ga-outcome-design.md`](../../s14-stage1-full-ga-outcome-design.md)
> 衝突,一律**以後三者為準**。`report-source-index.md` / `.zh-Hant.md` 與 qa 檔同為 non-authority。
>
> **⚠ 本檔尚未完成,而且會變。** capped(P0=512)半部**已完整**;
> **native-Gen0(11,405)半部仍在執行中**——截至 **2026-08-13 02:39 UTC**,五個 native large
> **⚠ 上述執行實況是 2026-08-13 的觀測, 已過時, 保留為當時的紀錄。**
> **2026-08-17 更新: native large 兩臂五個 seed 全部完成, 7× remeasure 五個端點亦已產出。**
> **§10.7 的表 N1–N5 已由實測 artifact 填入, 表的形狀未因結果而更動;**
> **§10.3 的三項預先註冊預測已判讀於 §10.7a —— (ii) 成立, (i) 與 (iii) 被推翻。**
> **本檔仍不為任何欄位編造數字, 也不下 S14 gate 判定。**

---
checkpoint_id: S14
shape: large `(2304, 1024, 1, 214336)`
role: confirmatory
document_type: PER-SHAPE ANNEX（附屬於 formal report,不可獨立引用）
report_status: COMPLETE — capped(P0=512) 與 native(P0=11,405) 皆已完成
#   (2026-08-18 更正: 原寫 native IN PROGRESS, 為 2026-08-13 快照。native 於 2026-08-17
#   13:13-13:27 完成, 表 N1-N5 已由實測 artifact 填入。尚未經獨立 verifier 複核。)
capped_campaign_state: COMPLETE（G/F 各 5 seed + 7× interleaved remeasure 5/5）
native_campaign_state: COMPLETE（2026-08-17；5 seed 的 7× 端點見 stage5_native_baseline/seed_*/large/champion_interleaved.json。
#   guided 側無端點檔是結構性的——worker 把兩臂寫進同一個檔。原值「RUNNING…guided 0/5 未啟動」為 2026-08-13 快照,已於 2026-08-18 更正）
observation_timestamp_utc: 2026-08-13T02:39Z
scientific_outcome: NOT_STATED_HERE（屬 formal report）
design_source: ../../s14-stage1-full-ga-outcome-design.md（§10 ACTIVE、§12 pre-registered、§13 PENDING_HUMAN_DECISION）
index_source: report-source-index.zh-Hant.md（§7.2、§7.2.1、§7.2a、§9;英文版 report-source-index.md 為權威)
run_root: /data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-baseline/
lock_a_source: <run_root>/lock/lock_a_protocol.json
lock_b_sha256: 3ac9768768ac088596687c47635bd6b8b5018d67cecc3f08e69ba2857b0ce59b
amendments: [RESCOPE-STAGE1-OUTCOME-20260807, PER-SHAPE-SOO-OUTCOME-20260809, ENTROPY-CAP-20260810, CLAIM-SCOPE-S14-20260810, CONDITIONAL-ARM-S-20260810, NATIVE-P0-ROBUSTNESS-20260811, NATIVE-P0-ROBUSTNESS-20260811(b), DEVIATION-REMEASURE-STOPLINE-20260812, REDUCER-FACT-CORRECTION-20260812]
---

> **Evidence labels(全文一致)。**
> `[BASELINE GPU]`＝Arm G 真實量測;`[GUIDED GPU]`＝Arm F 真實量測;
> `[CODE AUDIT]`＝讀 code／artifact 得到的事實,附 `file:line` 或 artifact 路徑;
> `[MODEL-ONLY]`＝Formocast 模型空間量(無 GPU)。
>
> **Anti-fabrication。** 本檔每一個數值都由撰稿者**直接自 primary artifact 讀取或重算**,
> 並逐處標明來源路徑。未量測者一律標 `NOT_EVALUATED`,且
> **`NOT_EVALUATED` ≠ 無效果**。**§10 的 native 半部不含任何發明的數字。**
>
> **Two-sided。** 本檔不預設結論、不作優越性宣稱,且**絕不**把單一通過的分項升格為 shape 層級結論。
> 來源文件中的 **RETRACTION／CORRECTION 在本檔維持撤回,且效力相同**。
>
> **路徑約定。** 除另有標示外,所有 run artifact 路徑相對於
> `run_root = /data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-baseline/`。

---

## 0. 怎麼讀這份附冊

| 層 | 內容 | 狀態 |
| --- | --- | --- |
| **A｜capped(P0=512)large** | §2–§9:組態、逐 seed 全表、六個分項、根因、量測稽核、參考包絡、殘餘不確定性 | **COMPLETE** —— 全部為已量測值 |
| **B｜native(P0=11,405)large** | §10:`NATIVE-P0-ROBUSTNESS-20260811` addendum 的 large 半部 | **COMPLETE(2026-08-17)** —— 表 N1–N5 已由實測填入;預測判讀見 §10.7a(兩項被推翻);**尚未經獨立 verifier 複核** |
| **C｜屬 formal report、本檔不做的事** | S14 gate 判定、跨 shape 連言、claim ladder 最終措辭 | **不在本檔** |

**一句話定位(不是結論,是記錄):** large 是**唯一有一個預註冊子判準通過的 shape**
(5/5 non-regression),而其餘子判準皆未達 ≥4/5。**這種「一項過、其餘皆不過」的形態,正是最容易被
斷章引用的形態**,所以 §5 用整整一節處理那個 5/5——包含它所依賴的常數本身尚未被驗證這件事。

---

## 1. large 的角色、能宣稱與不能宣稱

### 1.1 角色

`[CODE AUDIT]` 依 design §10.2,large `(2304,1024,1,214336)` 與 medium `(256,256,1,1024)`
同為 **confirmatory shape**,tiny `(8,8,1,128)` 為探索性。large 在本研究中的三項特殊地位:

1. **treatment 最豐富。** 三個 shape 中 large 的 activated gene 最多——**5/27**
   (`PrefetchGlobalRead`、`TransposeLDS`、`UnrollLoopSwapGlobalReadOrder`、
   `GlobalReadVectorWidthA`、`GlobalReadVectorWidthB`),medium 2/27、tiny 0/27
   (`[MODEL-ONLY]` `derivation-manifest-capped.json` `per_shape_activation_log`;S11 報告 §13.1)。
   **這一點必須與結果一起讀:訊號供給最充足的 shape,淨效應仍 ≈ 0。**
2. **量測最乾淨。** large 的 7× remeasure **1/70 dropout = 1.43 %**(專案唯一實作的 **0.95** 判準;
   在 index §7.1a 的 **0.80** 判準下為 0/70。唯一命中是 seed 24005 arm F,`min 522,984 < 0.95 × 550,706`,
   是 0.9497 的邊界點)、視窗內經驗離散度 0.0269
   (§7)。medium 的主要指標則已被證實 instrument-invalid(design §13.3),
   **這個缺陷碰不到 large。**
3. **實務代表性最高。** design §12.2(A)(2):大 GEMM 是 tuning 成本的重心。

### 1.2 本檔能陳述的

- `[BASELINE GPU]`／`[GUIDED GPU]` capped-512 下,large 的逐 seed Gen0／gen-10／AUC／
  7×-median final champion 觀測值,以及各預註冊分項的 5-seed 計數(§4;**現行 gate 為前三項**,見 §4.4 的更正框)。
- `[CODE AUDIT]` 這些分項所依賴的 pins、hash、GPU UUID、偏差與其處置(§2、§3)。
- `[CODE AUDIT]` large 量測品質的稽核,以及它為何**不受** medium warm-up 缺陷影響(§7)。
- 5/5 non-regression 在**兩個 margin 下**的雙重判定,以及 `η_large` 本身的來源與其未驗證性(§5)。
- Gen0 分項的中心-極值根因分解(§6)。

### 1.3 本檔**不**陳述的

- **不陳述 S14 gate 判定**(屬 formal report)。本檔只給分項計數。
- **不**把 5/5 non-regression 升格為「large 通過」「guided 不會使 large 變差」或任何 shape 層級結論。
- **不**作優越性宣稱、不作一般化／部署／跨架構／end-to-end wall-clock 宣稱(charter §8.6)。
- **不**歸因於 Formocast 的 physics 方向——conditional Arm S 的觸發條件與判定屬 formal report,
  未觸發時歸因僅限「capped factorized initialization bundle vs baseline」(design §10.5)。
- ~~**不**為 native 半部給出任何數字(§10)。~~ **⚠ 2026-08-18 作廢** —— native 已於 2026-08-17
  完成,§10.7 的表 N1–N5 全部由實測 artifact 填入。本檔**確實**陳述 native 的數字。

---

## 2. 組態、臂、seed 與被釘死的東西

### 2.1 兩臂與 treatment

`[CODE AUDIT]` 逐檔核對 `config/s14-pershape-large-seed_2400{1..5}.yaml`(Arm G)與
`config/s14-pershape-guided-large-seed_2400{1..5}.yaml`(Arm F):

- 兩份 YAML 的**唯一差異**是 guided 檔在 `BenchmarkFinalParameters` 之前**多出 5 個 gene 的
  sampling-probability 權重區塊**,恰為上列 5 個 activated gene;其餘逐位元相同。
  (`diff` 兩檔的輸出只有一段 `124952a124953,124981` 的新增。)
- `group_0`(MatrixInstruction/WorkGroup,9,918 個聯合候選)在**兩臂都存在且相同**
  (兩檔 `grep -c group_0` 皆為 1;`env/guided_config_verification.json` 逐 seed 記錄
  `group_0_sha256 = 3c5a30f7…`,5 個 seed 一致)。**treatment 從不碰 group_0。**

`[CODE AUDIT]` `env/guided_config_verification.json`(fail-closed 紀錄):

| 項目 | 值 |
| --- | --- |
| `lock_b_sha256` | `3ac9768768ac088596687c47635bd6b8b5018d67cecc3f08e69ba2857b0ce59b` |
| large `ga_weights_sha256` | `9fcd25173c6773e4ec787f51fcab372e9c5a0cf8457c176c475b8949df562c70`(撰稿者對 `agent_run/260809-s14-pershape-guidance/out-capped/ga-weights-large.json` 重算 sha256,**相符**) |
| `weight_beta` | `0.25` |
| `activated` / `activated_genes` | `true` / 5 個(如上) |
| 5 個 gene 的 GA post-transform 單元測試 | 全部 `pass`;`max_abs_error` 介於 **1.07e-08 – 2.08e-08** |

`[CODE AUDIT]` `stage3_guided/seed_*/large/ga_init_evidence.json` 五個 seed 一致記錄
`weights_sha256 = 753d629c41cadb0be49b445eb935164aa7700bce6f0b94cc2fc7c435859f8e98`。
**誠實界線:** 這個 hash 是 runner 對**注入權重結構**(含 `group_0`)取的 `canonical_hash`
(`scripts/run_pershape_seed.py:324`),與 Lock B 檔案本身的 sha256 `9fcd2517…` 是**兩個不同物件**;
兩者之間的推導關係本檔**未重算**,記為 `NOT_EVALUATED`。fail-closed 對檔案 hash 的檢查則在
`scripts/make_guided_config.py:56-58` 完成且通過。

### 2.2 逐 seed pins(全部由撰稿者自 `driver_status.json` 直接讀取)

| seed | `HIP_VISIBLE_DEVICES` | `verified_gpu_uuid`(G 與 F 相同) | `DUCTILE_FORCE_P0` | Gen0 建構母體 | remeasure 卡 |
| --- | --- | --- | --- | --- | --- |
| 24001 | 2 | `GPU-8cdaa86f8629c93a` | `1` | 512 | 同卡 |
| 24002 | 3 | `GPU-eebf31642af31b3b` | `1` | 512 | 同卡 |
| 24003 | 4 | `GPU-ac9e2fc9e28ca2fb` | `1` | 512 | 同卡 |
| 24004 | 7 | `GPU-bc724e0cf5b78d17` | `1` | 512 | 同卡 |
| 24005 | 6 | `GPU-74a77207e38908fb` | `1` | 512 | 同卡 |

*Source:* `stage3_{baseline,guided}/seed_*/large/driver_status.json`、
`stage3_guided/seed_*/large/ga_init_evidence.json`(`pop_size_at_construction`、
`decay_type_at_construction: "none"`)、`stage3_baseline/seed_*/large/champion_interleaved_status.json`
(`verified_gpu_uuid`)。

**同 seed 的 G 與 F 使用同一顆實體 GPU,且 7× remeasure 也在同一顆卡上完成**——
這是 large 與 medium 的關鍵差異之一(medium 的 remeasure 被迫改到 GPU 5,見 index §8.3 的
`medium_remeasure_deviation.md`;large **無此偏差**)。

### 2.3 其餘 pins

`[CODE AUDIT]` `config/s14-pershape-large-seed_24001.yaml` 前 22 行:
`EnqueuesPerSync: 321`、`NumWarmups: 321`、`NumElementsToValidate: 128`、`SleepPercent: 50`、
`KernelTime: true`、`PreciseKernelTime: false`、`RotatingBufferSize: 0`。
`n_gen=30` 上限 + 保留 Ductile 原生早停 `period=5`;gen-10 檢查點自同一次跑擷取
(`ga_init_evidence.json`:`n_gen: 30`、`period: 5`)。

### 2.4 **large 跑在 `rotating-buffer-size = 0`,medium 跑在 4096——為何這件事影響可比性**

`[CODE AUDIT]` `diff config/s14-pershape-large-seed_24001.yaml config/s14-pershape-medium-seed_24001.yaml`
的**完整輸出只有兩處**:

```text
21c21
<   RotatingBufferSize: 0          # large
---
>   RotatingBufferSize: 4096       # medium
115016,115017c115016,115017 / 115019c115019
   ProblemSizes: [2304,1024,1,214336]  vs  [256,256,1,1024]
```

亦即 **large 與 medium 的差異只有 RBS 與四個 `ProblemSizes` 數字**;其餘 115,000 餘行完全相同。
這是 design §10.2 的 pin(「per-size rotating(large RBS=0、medium/tiny RBS=4096)」)。
`stage3_baseline/seed_*/large/driver_status.json` 的
`DUCTILE_PERSIZE_RBS = {"0":[[2304,1024,1,214336]]}` 與
`champion_interleaved.json.measurement_metadata.rotating_buffer_mb = 0` 獨立確認 large 實際跑在 RBS 0。

**為何這對可比性重要——三點,方向不同,不可混為一談:**

1. **對 G-vs-F 的內部效度:無影響。** RBS 在**同一 shape 的兩臂完全相同**,配對比值中抵銷。
   large 的 F/G 與 medium 的 F/G 各自都是乾淨的臂內對比。
2. **對跨 shape 的水準比較:不可直接比。** index §7.1b 實測:光是把 medium 從 RBS 4096 改成 0,
   量測水準就從 **12,430 移到 14,153 GFLOP/s(+14%)**——`rotating-buffer-size` 本身就是一個
   **不同的 estimand**。因此 large 與 medium 的**絕對 GFLOPS、dropout 率、經驗 η** 之間的差異,
   **不能**全部歸因於 shape;RBS 是共變因子。
3. **對 medium 缺陷修法的可移轉性:這正是它未被驗證的原因。** index §7.1b / design §13.3:
   warm-up sweep **每一個零 dropout 的點都跑在 RBS = 0**,而兩個 RBS-4096 的長暖機變體
   **25/25 全數 crash**(50 次 `hipModuleLoad rc=-6`)。所以「large 乾淨」這件事**不能**被拿來
   論證「同一個修法在 medium 的釘死 RBS 4096 下也會成立」。
   決定性的可行性探測是 **5,136 warm-ups @ RBS 4096**。
   **⚠ 更正(2026-08-18):原文寫「尚未執行」,那是假陳述 —— 它寫下時就已經是錯的。**
   該探測**已於 2026-08-13 執行**(`agent_run/260809-s14-pershape-baseline/medium_clockladder/capped/`
   `seed_{24001,24004,24005}/s4_warmup5136/probe_20260813T131304Z.log`),**三個 seed 全部 `rc = 1`**。
   **但三者的死因不同,不可寫成同一個機制:** seed **24001 與 24005** 走到了那次配置並顯示
   `Rotating buffer set to: 4294967296. Rotating num: 3272` 與
   `1312256 * 3272 = -1265664` —— **int32 環繞由引擎自己印出的負數確證**;
   seed **24004 在到達該配置之前先中止**(同檔 `:623`,
   `Client must be linked with an embedded library or a library must be specified at runtime.`),
   **其失敗與溢位無關**。
   ⇒ **該條件已 `EVALUATED / closed by infeasibility`,不是 `NOT_EVALUATED`**
   (與 index §9.5 及 ledger `CAPABILITY-ENDPOINT-PACKET-20260813` 的既有記錄一致);
   不可行的門檻是 **`nw ≥ 1638 @ RBS 4096`**,**不是「RBS 4096 不可行」** ——
   `1400 @ 4096` 與 `1637 @ 4096` 都量過,n = 50,dropout 各 4.0 %
   (`medium_warmup_rbs4096_confirm_summary.json`)。
   **本項結論(可移轉性未被驗證)不受影響,錯的只有它給的理由。**

**⚠ 因此:凡是把 large 的乾淨量測拿來替 medium 的量測背書的論述,在本研究的證據下都不成立。**

---

## 3. 執行紀錄與偏差(capped)

### 3.1 GA run 完成狀態

`[CODE AUDIT]` `stage3_{baseline,guided}/seed_*/large/driver_status.json`:10 個 run 全部
`status: PASS`、`exit_code: 0`。baseline 於 2026-08-10 06:18Z–12:09Z 之間完成;
guided 於 2026-08-11–12 完成(seed 24001 F:2026-08-11T18:14:24Z → 2026-08-12T00:05:27Z,
`wall_seconds_monotonic = 21,063`)。

**順序 confound(必須明講):** baseline 對**所有** seed 都先於 guided 跑。
控制漂移的是 **7× interleaved remeasure**(同卡、同視窗、G/F 交錯),**那才是 champion
real-GFLOPS 的比較依據**;GA log 內的分數不是端點(index §8)。

### 3.2 Deviation:`DEVIATION-REMEASURE-STOPLINE-20260812`(**直接影響 large**)

`[CODE AUDIT]` `quarantine/stopline_bug_20260812/README.md` 與其中三份 FAIL 紀錄:

`scripts/remeasure_interleaved_champion.py`(**我方 run-root 腳本,非封存碼、非 Lock A**)原本斷言
「跑到 `n_gen=30` horizon」與「log 中出現原生早停行」互斥。**兩者並不互斥**:Ductile 在
`n_gen: 30` 上限之外仍保留 `period: 5` 早停(`ductile/config/defaults.yaml`),停止條件可能恰在
最後一代觸發。因此三個**符合設計**的 run 被拒:**seed 24002(large)、seed 24002(tiny)、
seed 24005(large)**。

次生效應:第一次失敗寫下 `champion_interleaved_status.json` 的 FAIL 紀錄後,腳本的
「artifact 已存在」守門拒絕了其後每一次重試——`seed 24005 large` 在 00:37–01:45 之間的
**7 次重試全部死在這個殘留檔案**,而非原本的 bug。

被隔離的 FAIL 紀錄(撰稿者直接讀取 `quarantine/stopline_bug_20260812/seed_24005_large/champion_interleaved_status.json`):
`status: FAIL`、`exit_code: 1`、
`exception: RuntimeError("Arm G: unexpected early-stop reason at gen-30 horizon: ['Stop criterion reached: f_avg and f_max did not increase for the last 5 generations.']")`、
`wall_seconds_monotonic: 6.9`、`finished_utc: 2026-08-12T00:29:16Z`。

修正只動 pre-flight 斷言、**量測邏輯未動**;守門改為檢查真正該成立的不變量(stop 行至多一行、
run 不得超過第 30 代),artifact 新增 `stopped_at_horizon`。修正後**五個 large remeasure 全數完成**。

**⚠ 一項未解的紀錄不一致(誠實記錄,不代為裁決):** index §8.4 記載腳本 sha256 由
`f2d11974…` 改為 `040db9cd5978f1b528f1acf8cf3460366f0c4c761b2443163be46bc69dc82b95`。
撰稿者今日(2026-08-13)對 `scripts/remeasure_interleaved_champion.py` 重算得到
**`5da5a7a27581af554c1b77d9a96955f1faad1db7a17fad3460cd960fc9a279bb`**,與兩者皆不同——
顯示該檔在 08-12 的修正之後**又被編輯過**。編輯內容與其是否影響 large 的既有 artifact:
`NOT_EVALUATED`。large 的 5 份 `champion_interleaved.json` 產出時間為 2026-08-12
00:24–01:50Z,早於今日;本檔的所有 large remeasure 數字都直接讀自那些 artifact,不經腳本重跑。

### 3.3 Interleave 起始臂

`[CODE AUDIT]` 五個 seed 的 `champion_interleaved_status.json` 皆為 `start_arm: "F"`,
`champion_interleaved.json.interleave_order` 七個 repeat 皆 `first_arm: F, second_arm: G`。
這是**逐 shape 的確定性對抗平衡** `START_ARM = {medium: G, large: F, tiny: G}`,
**是設計如此,不是 deviation**(index §8.4)。

### 3.4 Checkpoint / resume

`[CODE AUDIT]` `stage3_guided/seed_24001/large/ga_init_evidence.json`:
`resume_requested: false`、`resume_from_generation: null`、`session_index: 0`;
`driver_status.json.ga_checkpoint.distinct_ledger = "exact"`。
per-generation checkpointing 在 engine 中對**兩臂本就 native 且已啟用**,故不造成 arm 不對稱
(index §8.2)。

### 3.5 主機硬重置(2026-08-11,`[CODE AUDIT]` index §8.1)

自 03:37 UTC 起機器每 57–58 分硬重置一次(其後 12 小時約 11 次),經 BMC
(`Last Power Event: ac-failed`)、兩次在 GPU 閒置時發生的重置、以及其他所有使用者容器同步重啟
證實為**外部 AC 斷電,與本工作負載無關**。**large 首代需 ~60–70 分 > ~56 分視窗**,
故有數小時 guided large 連第一個 checkpoint 都寫不出、每週期從 gen 0 重來。供電轉穩後
(出現 >70 分視窗)五個 guided large seed 全部寫出第一個 checkpoint 並完成。
**這是硬體／機房故障,不是實驗設計或軟體缺陷**;它影響的是**時程**,不影響已完成 run 的效度。

---

## 4. Capped(P0=512)large:逐 seed、逐臂完整結果

> 本節所有數字由撰稿者以 `analyze_large.py` 的定義**獨立重跑**取得,並逐項對照
> primary artifact。`[BASELINE GPU]`＝G 欄,`[GUIDED GPU]`＝F 欄。

### 4.1 Run 層級量(GA trajectory)

| seed | arm | `generations_run` | 早停 | `cumulative_complete_evals` | post-Gen0 evals | `best_fitness`(GFLOP/s) | termination_reason |
| --- | --- | ---: | :---: | ---: | ---: | ---: | --- |
| 24001 | G | 21 | 是 | 7,689 | 7,200 | 587,893 | 原生早停(f_avg/f_max 連 5 代未增) |
| 24001 | F | 21 | 是 | 7,584 | 7,101 | 545,668 | 原生早停 |
| 24002 | G | 30 | 否 | 10,021 | 9,541 | 557,577 | 到 `n_gen=30` horizon;**早停亦於最後一代觸發** |
| 24002 | F | 30 | 否 | 10,132 | 9,644 | 555,592 | 到 horizon |
| 24003 | G | 21 | 是 | 8,262 | 7,777 | 531,604 | 原生早停 |
| 24003 | F | 30 | 否 | 10,352 | 9,865 | 573,159 | 到 horizon;**早停亦於最後一代觸發** |
| 24004 | G | 30 | 否 | 10,079 | 9,594 | 560,507 | 到 horizon |
| 24004 | F | 21 | 是 | 7,993 | 7,513 | 520,523 | 原生早停 |
| 24005 | G | 30 | 否 | 10,140 | 9,654 | 545,982 | 到 horizon;**早停亦於最後一代觸發** |
| 24005 | F | 20 | 是 | 7,750 | 7,259 | 544,175 | 原生早停 |

*Source:* `stage3_{baseline,guided}/seed_*/large/optimization_result.json`
(`best_fitness`、`generations_run`)、`trajectory.jsonl`(最後一列的
`cumulative_complete_evals`)、`stage3_baseline/seed_*/large/champion_interleaved.json`
→ `arms.{G,F}.resolution_provenance.{generations_run, early_stopped, termination_reason,
cumulative_post_gen0_complete_evals}`。

**註 1 —— `best_fitness` 不是端點。** 它是約 7,700–10,400 次評估的**最大值**,帶 winner's curse
偏差(index §5(i))。端點是 §4.3 的 7×-median。
**註 2 —— 「到 horizon 且早停行同時出現」正是 §3.2 那個 bug 誤判的邊界情況**,現由
`termination_reason` 同時陳述兩者而可稽核。
**註 3 —— 早停造成兩臂評估預算不同**,故 AUC 必須對**共同累積評估預算 `B*`** 積分(§4.2)。

### 4.2 早期搜尋:Gen0、gen-10、AUC

| seed | Gen0 best G | Gen0 best F | 方向 | gen-10 best G | gen-10 best F | 方向 | `B*` | AUC F/G | 方向 |
| --- | ---: | ---: | :---: | ---: | ---: | :---: | ---: | ---: | :---: |
| 24001 | 464,638 | 385,612 | **−** | 578,403 | 541,477 | **−** | 7,584 | 0.9176 | **−** |
| 24002 | 411,852 | 439,016 | **+** | 521,516 | 538,144 | **+** | 10,021 | 1.0214 | **+** |
| 24003 | 409,646 | 398,118 | **−** | 522,940 | 552,377 | **+** | 8,262 | 1.0509 | **+** |
| 24004 | 449,519 | 379,399 | **−** | 539,633 | 508,659 | **−** | 7,993 | 0.9436 | **−** |
| 24005 | 435,831 | 425,865 | **−** | 531,197 | 530,797 | **−** | 7,750 | 1.0076 | **+** |
| **為正的 seed 數** | | | **1/5** | | | **2/5** | | | **3/5** |

*Source:* `stage3_{baseline,guided}/seed_*/large/trajectory.jsonl` —— Gen0 取 `gen==1` 列的
`best_gflops_so_far`;gen-10 取 `gen<=10` 的最後一列;AUC 對 `cumulative_complete_evals` 作
step-hold 積分至 `B* = min(evals_G, evals_F)`(design §10.2 的 AUC 定義,per shape,不跨 shape 合併)。
gen-10 亦可由 `champion_interleaved.json.arms.{G,F}.resolution_provenance.gen10_incumbent`
獨立取得(seed 24001 G:`best_gflops_so_far = 578403`、`actual_gen = 10`、
`gen10_from_earlystop: false`——與上表相符)。

`[CODE AUDIT]` **decay 法則 2 在兩臂同代啟動,不是 arm-level confounder。** index §3.2b:
每個 S14 large run 的 diversity 都在**第 6 代**跨過 `div_thr = 0.5`
(seed 24001:baseline 0.568/0.515/**0.492**、guided 0.560/0.508/**0.491**),
`ga.py:291` 的 decay 法則 2 因而安裝、族群往 256 衰減。兩臂 diversity 軌跡幾乎重疊,
所以它是**協定的共同性質**;它影響的是絕對 eval 預算,不影響配對的 G-vs-F 對比——
這也正是 AUC 必須對共同 eval 預算積分的原因。

### 4.3 Final champion:7× interleaved remeasure(逐 repeat 全表)

`[CODE AUDIT]` `stage3_baseline/seed_*/large/champion_interleaved.json` →
`remeasure.{G,F}`(七個原始 repeat,單位 GFLOP/s):

| seed | arm | 7 個 repeat | max/min | median | stdev |
| --- | :---: | --- | ---: | ---: | ---: |
| 24001 | G | 589,319 · 575,916 · 581,105 · 571,103 · 571,005 · 588,970 · 572,597 | 1.0321 | **575,916** | 8,019 |
| 24001 | F | 531,779 · 540,186 · 535,412 · 518,545 · 536,335 · 534,364 · 519,490 | 1.0417 | **534,364** | 8,483 |
| 24002 | G | 530,744 · 539,476 · 532,390 · 529,065 · 542,982 · 544,450 · 545,358 | 1.0308 | **539,476** | — |
| 24002 | F | 532,113 · 546,575 · 537,604 · 558,432 · 545,938 · 558,409 · 531,282 | 1.0511 | **545,938** | — |
| 24003 | G | 527,285 · 526,510 · 529,722 · 527,053 · 527,060 · 514,607 · 534,874 | 1.0394 | **527,060** | — |
| 24003 | F | 574,527 · 574,405 · 547,856 · 559,859 · 559,828 · 559,164 · 562,465 | 1.0487 | **559,859** | — |
| 24004 | G | 533,750 · 536,829 · 537,433 · 537,726 · 547,924 · 538,416 · 530,203 | 1.0334 | **537,433** | — |
| 24004 | F | 511,975 · 507,052 · 515,461 · 515,412 · 512,021 · 503,512 · 511,851 | 1.0237 | **511,975** | — |
| 24005 | G | 534,715 · 522,589 · 548,901 · 522,505 · 549,435 · 535,467 · 535,902 | 1.0515 | **535,467** | — |
| 24005 | F | 535,810 · 550,197 · 550,706 · 550,091 · 523,638 · 523,174 · 522,984 | 1.0530 | **535,810** | — |

**每一臂的 7 次 repeat 都落在 1.024×–1.053× 的全距內。1/70 dropout = 1.43 %(0.95 判準);0/70(0.80 判準)。見 §7.2。**
對照 medium 同一協定下的 2.36×–6.06×(index §7.1a)——**這是本研究中最可重複的量測。**

F-vs-G 對比(分析量為 `ln(F/G)`,理由見 index §5b):

| seed | G median | F median | **F/G ratio** | 變化率 | `ln(F/G)` |
| --- | ---: | ---: | ---: | ---: | ---: |
| 24001 | 575,916 | 534,364 | **0.9279** | −7.2 % | **−0.0749** |
| 24002 | 539,476 | 545,938 | **1.0120** | +1.2 % | **+0.0119** |
| 24003 | 527,060 | 559,859 | **1.0622** | +6.2 % | **+0.0604** |
| 24004 | 537,433 | 511,975 | **0.9526** | −4.7 % | **−0.0485** |
| 24005 | 535,467 | 535,810 | **1.0006** | +0.1 % | **+0.0006** |
| **中位數** | — | — | **1.0006** | **+0.1 %** | **+0.0006** |
| *(原始比值的算術平均——有誤導性,見 index §5b)* | — | — | *0.9911* | *−0.9 %* | *(幾何平均 0.9900,−1.0 %)* |

*Source:* `champion_interleaved.json` 的 `median_gflops`、`F_over_G_median_ratio`、
`F_over_G_median_log_ratio`(撰稿者對 `remeasure.{G,F}` 重算中位數,逐 seed 相符)。

**champion 解析未受汙染(紀錄事實,非推論)。** `[CODE AUDIT]` large 的
`champion_interleaved.json → arms.{G,F}.resolution_provenance.selection_candidates`
在 **10/10 個 arm-entry** 中都恰好只有一筆,且解析出的 `canonical_hash` 在 **10/10** 中
都落在該臂 `optimization_result.json` 的 `best_individual_hashes` 內(撰稿者逐檔重算)。
這是 design §13.6 那個 40/40 統計中屬於 large 的一半。

### 4.4 預註冊分項的 5-seed 計數

> **這是計數,不是判定。** gate 判定屬 `staged/s14-guided-results.md` **§5.4**(owner 於 2026-08-18 指定;
> 原本指向的 `full-ga-baseline-vs-guided-outcome-report.md` **已由 owner 解除授權**)。
>
> **⚠ gate 的成分數(2026-08-18 更正)。** 原標題寫「**六個**預註冊分項」。現行判定以
> **{Gen0、gen-10、AUC} 三項 margin-free 子判準**為準 —— 第四個子判準
> `final ratio ≥ e^{−η_s}` 已由 `ETA-MARGIN-REMOVED-20260814` **移出 gate 成分**,
> 且**未登記任何替代門檻**。
> **但預註冊設計檔 `s14-stage1-full-ga-outcome-design.md:226` 本身尚未被修訂**
> (該 token 在該檔命中 0 次;index §2 的 ledger 註明「owner to amend separately」),
> 所以那份文件讀起來仍是四項連言。
> **`final ratio` 並未被移除為必報量** —— ledger 明文「still reported(direction + effect size)」,
> 其判讀方法由 `NULL-AS-NOISE-BASELINE-20260818` 指定(對 null 尺,**不設倍數門檻**)。
> 下表保留全部分項的計數;**只有前三項是現行 gate 成分**。

| 分項 | 判準 | 為正的 seed | 需要 |
| --- | --- | :---: | :---: |
| **Gen0 best** | `Gen0_F > Gen0_G` | **1/5** | ≥4/5 |
| **gen-10 best** | `gen10_F > gen10_G` | **2/5** | ≥4/5 |
| **AUC**(best-so-far,共同 eval 預算 `B*`) | `AUC_F > AUC_G` | **3/5** | ≥4/5 |
| **final champion 為正**(7×-median) | `F/G > 1` | **3/5** | ≥4/5 |
| **final non-regression** | `F ≥ G·e^{−η_s}` | **5/5**(pinned `η`);**3/5**(經驗 `η`) | ≥4/5 —— **見 §5** |
| **final improvement** | `F > G·(1+δ_s)` | **0/5** | — |

`[CODE AUDIT]` 逐 seed 的門檻數值取自 `champion_interleaved.json`:
`eta_s = 0.12284585545668891`、`delta_s = 0.13071011471940674`、
`nonregression_floor = e^{−η} = 0.8843999774850838`、improvement 門檻 `1 + δ = 1.1307101147194067`、
`R_s = 180336.0`。`threshold_evaluations.report_only = true`。

**必須一起讀的四件事:**

1. **前四個分項(Gen0、gen-10、AUC、final positive)全部低於 ≥4/5,分別是 1/5、2/5、3/5、3/5。**
2. **這四項讀自 GA trajectory 與 large 自己的乾淨 remeasure,`medium` 的量測缺陷碰不到它們**
   (design §13.2 明列 large = 1/5、2/5、3/5)。
3. **`median → max` 估計量替換不改變任何一個方向性計數**(design §13.2:兩種算法都是
   3/5、2/5、3/5、3/5、1/5)。
4. **improvement 為 0/5**——沒有任何一個 seed 的 F 超過 `G·(1+δ_large)`。

`[BASELINE GPU]` **baseline 臂自身的離散度框住了效應的可能上限。** G 的五個 champion median
橫跨 **527,060–575,916 GFLOP/s**(相對中位數約 ±4.4 %),對比 medium 的 6,137–13,495(2.2× 幅度)。
原因:large 是 **main-loop dominated**,GA 幾乎不論 seed 都落進同一個效能 basin。
**seed 之間本來就沒有多少空間留給 Gen0 prior 去移動。**

---

## 5. 那個 5/5 non-regression —— 唯一通過的分項,必須極為小心地處理

> **⚠ 這是本研究中唯一在任何地方通過的預註冊分項,而且它尚未解決。**
> **它只是預註冊四項連言中的一個分項,且四項並未全數達標。引用它時,絕不可略去它所條件依賴的 margin。**
> **⚠ 2026-08-18 補記:** 該分項所依賴的 `η_s` margin 已於 2026-08-14 由
> `ETA-MARGIN-REMOVED-20260814` 移出 gate 成分。**因此這個 5/5 現在連「gate 分項」都不是** ——
> 它是一個已退役判準下的歷史計數。**更不可單獨引用。**
> design §13.5 對 large 的規定(該節為 `PENDING_HUMAN_DECISION`,**尚未經 owner 核准**):
> 5/5 non-regression **僅能作為一個分項報告、絕不可單獨引用**。

### 5.1 兩個 margin,兩個相反的判定

`[CODE AUDIT]` 把兩個 margin 分別套用到 `F/G ≥ e^{−η}`:

| seed | F/G | pinned `η = 0.1228459` → floor **0.8844** | empirical `η = 0.0269` → floor **0.9735** |
| --- | ---: | :---: | :---: |
| 24001 | 0.9279 | PASS | **FAIL** |
| 24002 | 1.0120 | PASS | PASS |
| 24003 | 1.0622 | PASS | PASS |
| 24004 | 0.9526 | PASS | **FAIL** |
| 24005 | 1.0006 | PASS | PASS |
| | | **5/5 PASS** | **3/5 —— 未達 ≥4/5** |

*Source:* pinned `η_s`:`noise/per_shape_noise.json`
(`shapes.large.eta_s = 0.12284585545668891`、`nonregression_floor = 0.8843999774850838`、
`n_residuals = 21`、`R_s = 180336.0`、
公式 `P95(|log y − median_r log y|) per shape, numpy percentile method='linear'`)。
empirical `η`:撰稿者依**同一條公式**,直接對 large 的
`stage3_baseline/seed_*/large/champion_interleaved.json → remeasure.{G,F}` 全部
**70 個 repeat 殘差**重算,得 **0.0269**(與 index §7.1a 表相符;`e^{−0.0269} = 0.97346`)。

### 5.2 為什麼這不是「換上比較好的那個數字」就好

**兩個估計量量的是不同的變異成分,而哪一個才對並不顯然。**

- **經驗值 0.0269** 來自**同一個 process、同一張卡**上的 7 次 repeat,整個 interleaved 視窗
  **橫跨約 106 s**(§7.3)。這些 repeats 是**相關的**:它們排除了視窗之間的 drift、
  跨數小時的熱狀態變化,以及跨日的變異。**因此它很可能是真實量測雜訊的下界**——
  用它會讓 3/5 的判定過於嚴苛。
- **釘住值 0.1228459** 來自一個 3-anchor × 7-repeat 的 pilot(design §10.2、index §3.8)。
  其設計**或許**涵蓋了視窗內 repeats 看不見的來源——但它是**在不同的量測上擬合出來的**,
  而且**從未對照這些量測驗證過**。

**要在兩者之間裁決,需要一個跨視窗的可重複性量測——而它不存在。**
design §13.7 第 1 項把它列為「合併式跨視窗 / A-A 實驗」(一個 large seed、12–15 個視窗分佈於
12–24 小時、每個視窗量 G / F / 第二個獨立 G′ 三臂,約 50 GPU-分鐘、可按視窗中斷),
**尚未獲核准、尚未執行**;design §13.9 明列「**任何 shape 都不存在跨視窗／跨日的重複性資料;
窗內 η 是一個緊度未知的下界**」。

> **⚠ 部分更正(2026-08-18)。** 上引 design §13.9 的那句概括**已不再為真**:
> `large_xwindow/results/m6/`(2026-08-17)是 **large native 的跨視窗**資料
> ——6 個 window × 5 seed,per-seed `sd(ln(F/G))` = 0.0125 / 0.0154 / 0.0125 / 0.0204 / 0.0172;
> `medium_pilot401/results/` 的九個 `m = 12` cell 是 **medium 的跨視窗**資料。
> **但這一段的主張仍然成立**,因為它要的是**特定那一個實驗**:
> design §13.7 第 1 項的 A/A 設計是 **12–15 個視窗、分佈於 12–24 小時、每窗三臂 G / F / G′**。
> m6 是 **6 個視窗、同一天連續、兩臂**,既沒有跨日、也沒有第三條 null 臂。
> **仍然不存在的是: 跨「日」的重複性(修好的儀器上一組跨 session 資料都沒有)、
> ~~以及 large capped 的跨視窗資料(該塊只有一個 window)。~~ **⚠ 已於 2026-08-18 為假** ——
> `large_xwindow/results/m6_capped/`(6 window × 5 seed,2026-08-18)就是 large capped 的跨視窗資料,
> per-seed sd **0.01195 – 0.02742**。
> **連帶後果,必須連著讀:** §5.1 的窗內經驗 `η = 0.0269` 被本檔形容為「緊度未知的下界」,
> 而 `m6_capped` 的跨窗 sd **與它同級** —— §5.2 用來拒絕經驗 margin 的理由(「它很可能只是下界」)
> 現在有直接反證。**本節不代為裁決,但該理由不能再原樣沿用。**
> **仍然沒有的只剩跨「日」的重複性。**
> 見 §10.7b。

### 5.3 `η_large` 撐在兩個 champion 重測重現不出來的 pilot anchor 上

`[CODE AUDIT]` 撰稿者直接對 pilot 原始資料
`agent_run/260807-s14-baseline-run/stage2_noise/raw_repeats.jsonl`(63 筆 = 3 shape × 3 anchor × 7 repeat)
逐 anchor 重算 large 的三個 anchor:

| large anchor | median GFLOP/s | 7 次 repeat 的 max/min | RBS |
| --- | ---: | ---: | ---: |
| anchor 1 | 213,192 | **1.2373** | 0 |
| anchor 2 | 180,336(＝ pinned `R_s`) | **1.4201** | 0 |
| anchor 3 | 62,112 | 1.0245 | 0 |

**`η_large = 0.1228` 由 anchor 1 與 anchor 2(max/min 1.24 與 1.42)撐著。**
而本次的 **champion 重測全部落在 1.024–1.053**(§4.3 表)——
**champion 重測重現不出那兩個 anchor 的離散度**(design §13.4 第三列)。

**兩點誠實補充,方向相反,都要說:**

- **有利於 pin 的一點:** large 的 pilot anchor 與 S14 的 large run **同樣跑在 RBS = 0**
  (上表末欄,撰稿者自 `raw_repeats.jsonl` 的 `rbs_used` 直接讀取),所以 large 的 pin 至少
  **沒有** medium 那種 RBS estimand 不一致的問題。
- **不利於 pin 的一點:** design §13.4 判定**三個 pin 都是 pilot 的意外,不是雜訊模型**——
  `η_medium` 由慢 3–7× 的 anchor 產生、`η_tiny` 由**單一個深度掉點**製造、`η_large` 由上述兩個
  離散的 anchor 製造。**「pin 是保守的」在 large 上為真(鬆了約 4.6×),但那不等於「pin 是對的」。**

### 5.4 與 medium 的不對稱——同一道 gate,兩個方向的誤差

| shape | pinned `η_s` | 經驗 P95 log-residual | 比值 | 誤差方向 |
| --- | ---: | ---: | --- | --- |
| medium | 0.0041953 | 1.2098(capped campaign 1) | **緊 288×** | 製造 **false positive** |
| **large** | **0.1228459** | **0.0269** | **鬆 4.6×** | 製造 **false pass** |
| tiny | 0.4466 | 0.0145 | 鬆 31× | —— |

*Source:* index §7.1a;large 一列由撰稿者獨立重算確認(§5.1)。

**同一道預註冊 gate、在兩個 confirmatory shape 上,同時出現兩個方向的誤差,原因相同:
`η_s` 從未對照它所 gate 的量測驗證過。**

### 5.5 站得住的報告方式

> **⚠ 2026-08-18 更正 —— 本節原本寫「待 owner 決策」,那已經過期八天。**
> 原文引 design §13.4 的 **D2** 提案(pinned `η_s` 維持治理地位 + 雙 margin 揭露)並稱它
> 「整體為 `PENDING_HUMAN_DECISION`,尚未核准」、index §9.3 第 5 項「仍在待裁決清單上」。
> **實際上該項已於 2026-08-14 由 owner 裁決,而且是相反的方向:**
> `ETA-MARGIN-REMOVED-20260814` **移除**了 per-shape noise margin `η_s`,
> 連同第四個 gate 子判準 `final ratio ≥ e^{−η_s}` 一併移出 gate 成分,**且未登記替代門檻**。
> index §9.3 第 5 項已標 `DECIDED 2026-08-14 … decided the other way … item closed`。
> **⇒ 「D2 是否成立」不再是待決事項;`η_s` 已無治理地位。**
> 以下保留原本的雙 margin 論證,**因為那兩個數字本身仍然是既成紀錄**
> (`measurement_design.md` §H.4 第 3 層:舊紀錄可以留著用 η,新的推理不可以),
> **但它們不得再作為新分析或新判準的尺規。**

依 index §7.2a 的建議措辭:

> 只報 5/5 pass,會把一個建立在未驗證常數之上的結果呈現得像已成定論;
> 只報 3/5,則會把一個雜訊的下界當成雜訊本身。

**另一項獨立的界線(design §13.4):`η` 是錯的尺度。** 它量的是**同一個 config** 的窗內重複性,
而 estimand 是**兩個不同 champion** 的比值。臂間離散度是窗內值的 **2.0 倍(large)**。

**⚠ 對引用者的明確警告。** 「large 的 non-regression 5/5 通過」這句話單獨出現時是**誤導的**。
它必須永遠與以下三件事同時出現:(i) 同一 shape 的 Gen0 1/5、gen-10 2/5、AUC 3/5、
final positive 3/5、improvement 0/5;(ii) 它在 large 自身的窗內經驗 margin 下是 **3/5**;
(iii) 它所依賴的 `η_large` 尚未對照它所 gate 的量測驗證過。

---

## 6. Gen0 分項(1/5)的根因 —— guidance 移動的是中心,GA 讀的是極值

> Gen0 這一項最具診斷價值,因為 **Gen0 正是處理介入的位置**——guided 臂與 baseline 的差異
> **只有** Gen0 的抽樣分布。它得到 1/5,亦即五個 seed 中有四個 guided Gen0 反而較差。

### 6.1 把 Gen0 拆成中心統計量與極值統計量

| seed | Gen0 median Q — G | Gen0 median Q — F | **中心 F/G** | Gen0 best GFLOP/s — G | Gen0 best GFLOP/s — F | **極值 F/G** | valid/512 G | valid/512 F |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 24001 | 0.8887 | 0.9052 | **1.0186** | 464,638 | 385,612 | 0.8299 | 489 | 483 |
| 24002 | 0.8797 | 0.8970 | **1.0197** | 411,852 | 439,016 | 1.0660 | 480 | 488 |
| 24003 | 0.9290 | 0.8799 | 0.9471 | 409,646 | 398,118 | 0.9719 | 485 | 487 |
| 24004 | 0.8883 | 0.9087 | **1.0229** | 449,519 | 379,399 | 0.8440 | 485 | 480 |
| 24005 | 0.8841 | 0.9187 | **1.0390** | 435,831 | 425,865 | 0.9771 | 486 | 491 |
| **中位數** | — | — | **1.0197** | — | — | **0.9719** | — | — |
| **F > G 的 seed 數** | — | — | **4/5** | — | — | **1/5** | — | — |

*Source:* `stage3_{baseline,guided}/seed_*/large/trajectory.jsonl` 的 generation-1 record
(`generation_Q_median_any_valid`、`best_gflops_so_far`、`generation_any_valid_count`);
撰稿者逐檔重算。

### 6.2 兩欄的方向穩定地相反 —— 機制

- **guidance 對它被設計要移動的量確實有效。** guided 臂在 **4/5** 個 seed 上讓*典型的* Gen0 候選
  變好(中位 **+2.0 %**)。prior 做到了 prior 該做的事:把機率質量往 S11 模型評價好的
  configuration 移。
- **但 GA 不消費這個量。** selection 讀的是*上尾*——Gen0 的 `best_gflops_so_far` 是
  **約 485 個有效抽樣的最大值**,一個**極值統計量**。極值主要由抽樣分布的**離散程度**決定,
  而非其中心位置。集中機率質量(任何非均勻 prior 都會這麼做)會抬高平均、同時壓縮上尾,
  於是即便中位數上升,期望最大值仍可能下降。guided 的 Gen0 best 在 **4/5** 個 seed 上較差
  (中位 **−2.8 %**)。
- **這不是 validity-rate 造成的假象。** 每 512 抽樣的有效候選數為 **480–489**(baseline)
  vs **480–491**(guided)——兩臂產生的可執行 config 數在統計上無法區分,所以差異**不是**
  「guidance 產生了更多無法 build 的 kernel」。
- **這正是 entropy cap 當初要框住的機制,而且它正往當初預期要防的方向作用。**
  `ENTROPY-CAP-20260810` 把 ρ 上限訂在使 `H_norm(p1) ≥ 0.80`,目的就是阻止 prior 壓垮 Gen0
  多樣性。資料顯示這個張力是**真實的**,而且 cap **並未消除它**:即使只是一個「在 29 個 gene 中對 5 個
  施加、且 entropy 損失 ≤20 %」的 prior(index §7.2.1 原文;S11 的 activation log 以 27 個
  eligible residual gene 為分母,故同一事實亦寫作 5/27——兩個分母的定義不同,見 S11 報告 §13.1
  與 design §2.3(b),本檔不代為統一),也足以在 Gen0 最大值上付出約 2.8 % 的代價、
  換到中位數約 +2.0 %。

`[MODEL-ONLY]` 參考:large 的 5 個 activated gene 與其 capped 混合強度
(`derivation-manifest-capped.json` `per_shape_activation_log`,轉引自 S11 報告 §11.2):
`PrefetchGlobalRead` **ρ=0.586133**(`S_g=0.191584`、ent@λ0 0.734498、`H_norm(p1)=0.800118`、
TV=0.335500、KL=0.277096)、`UnrollLoopSwapGlobalReadOrder` ρ=0.80(`S_g=0.164739`、`H_norm=0.839929`)、
`GlobalReadVectorWidthB` ρ=0.80(`S_g=0.058021`、`H_norm=0.844142`)、
`TransposeLDS` ρ=0.80(`S_g=0.057093`、`H_norm=0.992663`)、
`GlobalReadVectorWidthA` ρ=0.80(`S_g=0.051991`、`H_norm=0.844404`);`λ_s = 8.0`。

### 6.3 這個根因的誠實界線

- 在 n=5 之下,**4/5 與 1/5 個別都不顯著**(公正硬幣得到 ≥4/5 的機率為 3/16 ≈ 0.19)。
- 真正站得住的是**配對對比**:在同一批 run 上,中心與極值往**相反方向**移動,方向與極值論證的
  預測一致,且兩個統計量各自都在 5 個 seed 中的 4 個成立。
- **Gen0 數值是單次、未重測的數字**,因此帶有 winner's-curse 偏差(index §5(i));
  其量級**不可**與 §4.3 的 7×-remeasured final-champion 數字直接相比。
- 要正式確認此機制需要針對性的量測(逐臂的完整 Gen0 fitness 分布,或 Arm-S shuffle control),
  此處為 **`NOT_EVALUATED`**。**§10 的 native-Gen0 addendum 正是這個機制的 22× 操縱變因檢驗
  (Q3),而它尚未有結果。**

### 6.4 這對設計的意涵

若此機制成立,則 per-gene 的 Gen0 prior 正在被一個**它並不優化的指標**評分:它改善*平均*抽樣,
而 GA 只保留*最好*的那一個抽樣。**這是關於 guidance 與 GA selection rule 之間耦合關係的陳述,
不是關於 S11 模型對不對的陳述**——而且它可以獨立於「guidance 訊號是否稀疏」之外被檢驗。

---

## 7. large 的量測品質稽核 —— 單窗端點乾淨,窗間離散度另計

> **⚠ 標題於 2026-08-18 收窄。** 原標題是「**為什麼它是乾淨的**」,那個概括過寬:
> 本節量到的是**單一 window 的端點**,而 2026-08-17 的跨窗探針 `large_xwindow/results/m6/`
> 在同一批 native champion 上得到 **pooled dropout 8.10 %**(34 / 420,95 % 判準)。
> **兩者不衝突,母體與判準都不同** —— 見 §7.2 的判準說明與 §10.7b。
> **本節的結論(large 沒有 medium 那個缺陷)仍然成立**,但它成立的根據是
> **large 端點的 dropout 是 1.4–2.9 %,而 medium 修復前是 39–46 %**,
> 不是「large 與 medium 修好後同級」。

### 7.1 缺陷機制與 large 的曝險

`[CODE AUDIT]` `ClientParameters.ini` 設定 `num-warmups = 321`、`enqueues-per-sync = 321`——
**三個 shape 完全相同**(本 run 的 YAML 亦同:`NumWarmups: 321`、`EnqueuesPerSync: 321`)。
但 kernel 時長相差三個數量級,所以同一個**次數**買到的**時間**天差地遠:

| shape | kernel duration | warm-up 牆鐘時間 | 結果 |
| --- | ---: | ---: | --- |
| medium | ~10 µs | **~3.2 ms** | 28 % dropouts(campaign 2 統計;紀錄用的 campaign 1 為 46.4 %) |
| **large** | **~1,873 µs** | **~601 ms** | **1 / 70 dropouts**(0.95 判準;0.80 判準下 0/70) |
| tiny | dispatch-bound | (對 clock 不敏感) | 1 / 70 |

閒置的 MI300X 停在 132–180 MHz,需要**數十毫秒的持續工作**才會升到 2100 MHz。
warm-up sweep 給出的拐點在 **51 ms**(dropout 率 0 %)。
**large 的 ~601 ms 約為爬升所需時間的 12 倍。**

`[CODE AUDIT]` **撰稿者的獨立重算。** 由 large 十個臂的 champion 驗證值
(`stage3_{baseline,guided}/seed_*/large/1_BenchmarkProblems/*/Data/00_Final.csv` →
`WinnerTimeUS`)得到 large 的實測 kernel 時長:

| 統計量 | 值 |
| --- | ---: |
| 最小 / 最大 | **1,732.32 µs / 1,954.59 µs** |
| 平均 / 中位數 | **1,866.0 µs / 1,857.15 µs** |
| 321 × 平均 = warm-up 牆鐘時間 | **599.0 ms** |
| 相對 51 ms 拐點 | **≈ 11.7×** |

index 引用的 **1,873 µs / ~601 ms** 落在此實測區間內,兩者一致。

### 7.2 large 的 dropout 稽核:0.95 判準下 1/70,0.80 判準下 0/70

`[CODE AUDIT]` 撰稿者依 index §7.1a 的判準(低於該臂最大值 80 % 者計為 dropout),
對三個 shape 的每一次 repeat 逐筆重算:

| shape | 使用的卡 | dropouts | rate |
| --- | --- | ---: | ---: |
| medium | hip 5 only(`--gpu-uuid-override`,index §8.3) | **32 / 70**(見下方更正) | **45.7 %** |
| tiny | hip 2, 3, 4, 6, 7 | **1 / 70** | 1.4 % |
| **large** | **hip 2, 3, 4, 6, 7** | **0 / 70**(0.80 判準)／**1 / 70**(0.95 判準) | **0 %**／**1.43 %** |

*Source:* `stage3_baseline/seed_*/{large,tiny,medium}/champion_interleaved.json` → `remeasure.{G,F}`。

> **⚠ 更正(2026-08-18)—— medium 一列與它的說明都已與所引來源脫節。**
> 原文寫 **17 / 70 = 24.3 %**,並說明「live 的 medium 檔案是 **campaign 2**
> (campaign 1 已於 2026-08-12 14:01–14:04Z 被就地覆寫)」。
> **2026-08-15 的 revert 把那五個檔案換回了 campaign 1**
> (`measurement_design.md` §H.1:五個 `champion_interleaved.json` mtime `2026-08-11T08:34–08:37Z`)。
> 所以 *Source* 指的那條路徑現在給出的是 **campaign 1**,就地重算為 **32 / 70 = 45.7 %**
> (80 % 與 95 % 兩種判準下同值)。**數字與說明都已依實際檔案更正。**
> campaign 2 的 17 / 70 = 24.3 % 仍然有效,但它的來源是
> `medium_recheck_summary.json` 與 `medium_recheck_control/.../preserved_campaign2_*/`,
> **不是這一列引的路徑**。design §13.3 認定 **campaign 1 才是紀錄用量測**,與更正後的數字一致。

> **⚠ 判準必須並列標明(2026-08-18)。**
> 上表用的是 index §7.1a 的 **80 %** 判準。
> **本專案在量測程式裡唯一實作的定義是 95 %**(`medium_pilot401/run_cell.py:13`、
> `large_xwindow/run_windows.py:82` `DROPOUT_FRAC = 0.95`,兩者逐字相同)。
> 以 95 % 重算:**large `1 / 70` = 1.4 %**、**tiny 與 medium 不變**。
> `stage5_native_baseline/seed_*/large/` 以 95 % 重算為 **2 / 70 = 2.9 %**。
> **兩個判準都要標明是哪一個** —— §10.7b 引用的 m6 用的是 95 %,母體 420,
> **與本表不可直接相比**。**不得由此寫出「large 差 5 倍」這類跨判準、跨母體的比較。**
**本表的 medium 一列僅供對照,medium 的正式數字屬 medium 附冊。**

### 7.3 large 的 interleaved 視窗:**~106 s**

`[CODE AUDIT]` `stage3_baseline/seed_24001/large/champion_interleaved_raw.jsonl`,
撰稿者逐列讀取時間戳:

| 量 | 值 |
| --- | --- |
| 記錄筆數 | **14**(7 repeat × 2 arm) |
| 首筆 | `2026-08-12T00:22:45.223270Z`(arm F,repeat 1) |
| 末筆 | `2026-08-12T00:24:31.714170Z`(arm G,repeat 7) |
| **首末間距** | **106.49 s** |
| 相鄰**記錄**間距 | ≈ 8.2 s |
| 相鄰**同臂**抽樣間距 | ≈ 16.3 s |
| 每個 repeat cycle(F+G) | ≈ 15.2 s(106.49 / 7) |
| 整個 remeasure 程序牆鐘時間(含建置) | `wall_seconds_monotonic = 148.62`(`champion_interleaved_status.json`) |

> **⚠ 更正一項既有草稿敘述。** 較早的草稿把 large 的視窗寫成「相隔約 **27 s**」——
> **那是 medium 的視窗,不是 large 的**(index §7.2a 已就地更正)。
> 正確的 large 視窗是 **~106 s**,相鄰同臂抽樣約 16 s、每個 repeat cycle 約 15 s。
> design §13.6 另記為「約 107 秒」——與本檔重算的 106.49 s 為同一量、四捨五入差異。

**這個視窗長度正是 §5.2 的關鍵:** 106 s 內的 7 次 repeat 是**視窗內**量測,
它們**排除了**跨視窗 drift、跨數小時熱狀態變化與跨日變異,因此由它們算出的 0.0269
**是雜訊的下界,不是雜訊本身**。

### 7.4 large 的 champion 驗證值沒有 medium 那種臂間不對稱

`[CODE AUDIT]` `stage3_{baseline,guided}/seed_*/large/1_BenchmarkProblems/*/Data/00_Final.csv`
→ `WinnerGFlops`(每臂一次量測,同一條 client 路徑):

| seed | baseline (G) | guided (F) |
| --- | ---: | ---: |
| 24001 | 583,821 | 523,009 |
| 24002 | 548,187 | 552,298 |
| 24003 | 522,905 | 553,312 |
| 24004 | 546,289 | 517,432 |
| 24005 | 542,876 | 535,922 |
| **中位數** | **546,289** | **535,922** |

十個值全部落在 **517,432–583,821**(max/min = 1.128)。
**對照 medium 的同一欄位:G = 2,961.9 / 8,846.0 / 4,210.4 / 12,516.2 / 11,542.6、
F = 13,590.7 / … ,中位數 8,846 vs 13,360**(design §13.6)——
medium 的臂間不對稱汙染是**直接觀測到的**;**large 沒有出現對應的形態**。

> **⚠ 界線,務必保留。** 即便如此,`original_final_gflops` / `WinnerGFlops`
> **絕不可**被當成 endpoint(design §13.6 的強制警告)。endpoint 是 §4.3 的 7× interleaved
> remeasure。上表僅作為量測品質的稽核證據。
> 另外:「汙染是單向且兩臂對稱、所以在配對比值中抵銷」這個說法**已被撤回**;正確措辭是
> 「汙染是單向的;**是否 arm-symmetric 為 `NOT_EVALUATED`**,且因逐代 benchmark CSV 未保留而
> **事後無法查證**」。這條撤回**同樣適用於 large**——large 沒有出現汙染形態,
> **不等於**已證明 large 的搜尋期完全無汙染。

### 7.5 GA 搜尋未受影響 —— 已查核

`[CODE AUDIT]` design §13.6 的有效證據(**Gen0 梯度論證已撤回**,因 `best_gflops_so_far`
依構造即為單調):

- **`generation_Q_median_any_valid`** —— 每代約 510 次評估的中位數。逐代平均 |Δ|:
  medium 5.58 % / 4.61 %、**large 6.98 % / 6.11 %**、tiny 6.50 % / 4.21 %。
- **機制性曝險上界** —— 在**同一個** client invocation 內每代推進約 508–512 次評估,
  一個約 50 ms 的 ramp **每個 invocation 只付一次**,約只曝險到約 510 個 solution 中的前 8 個
  (**約 1.6 %**),對比全新 process 之 remeasure 的 28–48 %。
- **對 large 而言此論證更強**:large 的單次 kernel 就是 ~1.87 ms,GA 在單一個長壽命 invocation
  內 benchmark 數千個候選,**卡全程都是熱的**。

---

## 8. tiny 的 null 包絡作為 large 的**參考包絡**

### 8.1 觀測

`[CODE AUDIT]` 撰稿者對 `stage3_baseline/seed_*/{tiny,large}/champion_interleaved.json`
的 `F_over_G_median_log_ratio` 逐 seed 讀取:

| shape | 逐 seed `ln(F/G)` | **max |ln F/G|** | sd |
| --- | --- | ---: | ---: |
| **tiny**(零 treatment,0/27 activated gene) | −0.1247 · +0.0344 · −0.1231 · −0.0047 · −0.0315 | **0.1247** | **0.0715** |
| **large**(5/27 activated gene) | −0.0749 · +0.0119 · +0.0604 · −0.0485 · +0.0006 | **0.0749** | 0.0530 |

**large 每一個 seed 的 `|ln F/G|` 都落在 tiny 的零 treatment 包絡之內。**

tiny 之所以是零 treatment:`[MODEL-ONLY]` tiny 的 Formocast 預測 **30,490 / 30,490 = 100.00 %**
為哨兵值,27 個 gene 的 `S_g` 全為 0.0000,**activated gene = 0**,故 tiny 的兩臂 Gen0 分布
**在建構上完全相同**——它是一個**意外得到的 null control**(design §13.5、§12.2(C))。

### 8.2 **邊界:這是參考包絡,永遠不是門檻**

> **⚠ 硬性界線(design §13.4 明文):**
> 「這是參考包絡,**永遠不是門檻**,**不得**轉成 margin、floor 或 pass/fail。」

具體而言,以下每一種用法都**被禁止**:

- ❌ 把 0.1247 當成 large 的 non-regression floor 或替代 `η_large`;
- ❌ 由「large 落在 tiny 包絡內」推出「large 的兩臂等價」「guidance 對 large 無害」;
- ❌ 由它導出任何 tier、任何 pass/fail、任何效應量的信賴區間;
- ❌ 用它去覆寫或補強 §4.4 的任何一個分項計數。

**它唯一能承載的陳述是:** 在同一套量測協定下,一個**已知為零**的 treatment 產生的 F/G 離散度,
**大於** large 觀測到的 F/G 離散度。這是對「n=5 下 large 的兩臂差異能不能被解析出來」這個問題的
**描述性校準**,不是一個統計檢定。

### 8.3 為什麼這個轉移偏**保守**

`[CODE AUDIT]` design §13.4 給出的可轉移性依據是**實測的 champion 層級離散度**:
**large 1.129、tiny 1.182、medium 1.222**——**tiny 並不特別平坦,large 才是最平的 shape**,
所以把 tiny 的包絡套到 large 上偏保守。
(reviewer B 原本以「過度轉移」反對,實測後**自行證偽並撤回**——此反轉須如實記錄。)

**撰稿者的獨立重算(誠實揭露差異):** 對 live artifact
`stage3_baseline/seed_*/{shape}/champion_interleaved.json` 的 10 個 champion median
(5 seed × 2 arm)取 max/min,得到 **large 1.1249、tiny 1.1705、medium 1.2205**。
**數值與 design §13.4 的 1.129 / 1.182 / 1.222 略有差異,排序與結論完全相同**
(large 最平、medium 最散)。差異來源未經確認(medium 的 live 檔案是 campaign 2,
tiny 的 5 個 seed 於不同時點補齊),記為 `NOT_EVALUATED`;**以 design §13.4 的數字為準**。

---

## 9. improvement 0/5、殘餘不確定性

### 9.1 improvement:0/5

`[CODE AUDIT]` `champion_interleaved.json.threshold_evaluations.improvement`:
公式 `F_median / G_median > 1 + delta_s`,門檻 `1.1307101147194067`;
五個 seed 的 `passes` 皆為 `false`(最高的 seed 24003 為 1.0622)。
`F_over_G_gt_one_plus_delta_s = false` × 5。

**這一項的措辭紀律:** 0/5 意味「**沒有任何 seed 的 F 超過預註冊的 improvement 門檻**」,
**不**意味「guidance 有害」,也**不**意味「guidance 無效果」。
`NOT_EVALUATED ≠ 無效果`,而 `未達門檻 ≠ 反向效應`。

### 9.2 large 的效應上限被 shape 本身框住

`[BASELINE GPU]` per-seed 變異為 **0.93×–1.06×**,亦即**每一個 seed 都落在
`η_large = 12.28 %` 之內**。與 medium 不同,**large 的 per-seed 差異沒有任何一個能在該 shape
自身的 pinned 雜訊邊界之上被解析出來**——在 n=5 下兩臂是「**無法區分**」,
而**不是**「方向不一致」。
(§5.1 已揭露:在 large 自身的窗內經驗 margin 0.0269 之下,seed 24001 與 24004 會被解析為退步。
兩種讀法都必須並陳。)

### 9.3 稀疏性發現的實務後果

`[MODEL-ONLY]` large 是所有 shape 中 activated gene **最多**的(5/27),
而 aggregate-max reducer 在最濃的口徑下也只給出 3/26 個 gene(S11 報告 §13.2)。
**即使是訊號供給最充足的 shape,模型訊號也不足以改變結果。**
依 charter §8.5,這個負向定位是 **`marginal-loss`(per-gene 邊際訊號薄弱)**,
**「模型沒用」不是合格結論**。

### 9.4 殘餘不確定性(**報告,不求解決**)

依 design §13.9 / index §9.4,以及本檔自身的稽核:

1. **不存在任何 shape 的跨視窗／跨日重複性資料。** large 的窗內 `η = 0.0269` 是一個
   **緊度未知的下界**。裁決 §5 的兩個 margin 需要 A/A 跨視窗實驗——**未核准、未執行**。
2. **`η_large` 從未對照它所 gate 的量測驗證過**,且其兩個承重 anchor(max/min 1.24、1.42)
   在 champion 重測(1.02–1.05)中重現不出來。
3. **`η` 是錯的尺度**:窗內單一 config 的重複性 vs 兩個不同 champion 的比值;
   large 的臂間離散度是窗內值的 **2.0 倍**。
4. **搜尋期汙染是否 arm-symmetric:`NOT_EVALUATED`,且事後不可查證**
   (逐代 benchmark CSV 未保留,只有 `00_Final.csv`)。此條**同樣適用於 large**。
5. **時脈機制由 warm-up sweep、DPM 算術與 tiny 的實測時脈不敏感性推論而得;
   不存在任何直接的鎖頻證據**(design §13.7 的 owner action,約 10 分鐘、零研究 GPU 時數,
   **未執行**)。
6. **§6 的中心-極值機制尚未被正式確認**;其操縱變因檢驗(§10 的 Q3)**已於 2026-08-17 有結果**
   (2026-08-18 更正 —— 原寫「尚無結果」):見 §10.7a,預測 (i) 與 (iii) **被推翻**、(ii) **成立**。
7. **`scripts/remeasure_interleaved_champion.py` 的今日 sha256 與 index §8.4 記載的修正後 hash
   不符**(§3.2),差異內容 `NOT_EVALUATED`。
8. **Modest power**:5 對 paired seed、單一 development cluster、限受測 shape,
   **非統計顯著性證明,不一般化**。
9. **claim scope 限「P0-capped = 512 Ductile variant」**;treatment × budget 交互作用尚未量化
   ——那正是 §10 的 Q2,**尚無結果**。

---

## 10. Native-Gen0(11,405)large —— **已完成(2026-08-17)**

> **狀態變更(2026-08-17):** native large 的兩臂五個 seed 已全部完成,7× interleaved remeasure
> 亦已產出五個端點。**§10.7 的表 N1–N5 已由實測 artifact 填入**;
> §10.1–§10.6 的**執行前**內容一字未改, 使預測仍可被否證。
>
> **本節仍不含任何 S14 gate 判定。** gate 判定屬 `staged/s14-guided-results.md` **§5.4**
> (owner 於 2026-08-18 指定;原本指向的 `full-ga-baseline-vs-guided-outcome-report.md`
> 已由 owner 解除授權)。
>
> **§10.3 的三項預先註冊預測已可判讀, 結果記於 §10.7a:**
> **(ii) 成立;(i) 與 (iii) 被推翻。** 依 §10.3 的字面要求, 此處照實記錄, 不改寫預測。

### 10.1 這是什麼、屬於哪一個 gate

`[CODE AUDIT]` `NATIVE-P0-ROBUSTNESS-20260811`(2026-08-11 pre-registered)+
`NATIVE-P0-ROBUSTNESS-20260811(b)`(2026-08-12 由 large-only 擴充為 large + medium,並新增 Q3)。
權威為 **design §12**。

**它是 design §12 的 robustness addendum,屬於同一個 gate 之內,不是第二個 gate**
(reports/README.md「S14 的兩層結構」)。設定與 capped 版**完全相同,唯一自變數是 Gen0 規模**:
不設 `DUCTILE_FORCE_P0`,讓 constructor 依 `ga.py:118` 把 Gen0 膨脹到
`int(9918 × 1.15) = 11,405`,再每代 decay 回 512(`ga.py:116/293`)。

### 10.2 執行前寫定的三個問題(design §12.1)

| # | 問題 | 對 large 的具體形式 |
| --- | --- | --- |
| **Q1** | **穩健性 / 外部效度** | capped-512 在 large 上的 F-vs-G 方向與效應,在原生 Gen0 規模下是否仍成立?→ 消除「你把 P0 改小了」對 large 結論的 caveat |
| **Q2** | **treatment × budget 稀釋量化** | guidance 的邊際效應是否在原生大 Gen0 下**縮小**?(假說:prior 在小 Gen0 最有效;大 uniform Gen0 把 free-gene marginals 抽滿 → 稀釋) |
| **Q3** | **極值機制的操縱變因檢驗** | §6 顯示 guidance 改善 Gen0 **中心**卻惡化 Gen0 **極值**。Gen0 池大小正是決定極值統計量往尾部取多深的參數,**512 → 11,405 是 22× 放大** |

### 10.3 **執行前寫定、可否證的方向性預測**(design §12.4 第 4 點)

> **這三項預測寫於 2026-08-12,早於任何 native large 資料存在。
> 若結果與預測相反,必須照實記錄為機制假說被推翻,不得事後改寫預測。**

| # | 預測 | 若成立 | 若被推翻 |
| --- | --- | --- | --- |
| **(i)** | guided 相對 baseline 的 **Gen0 極值劣勢會擴大**(而非縮小) | 支持 §6 的「集中機率質量 → 壓縮上尾 → 期望最大值下降」機制 | §6 的機制假說被反證,須照實記錄 |
| **(ii)** | guided 的 **Gen0 中心優勢維持或擴大**(prior 未變、樣本更多 → 中心估計更穩) | 同上 | 同上 |
| **(iii)** | **跨 shape 梯度**:large(5 個 activated gene)的極值劣勢擴大幅度 **應大於** medium(2 個) | 支持「分布收窄幅度隨 activated gene 數增加」 | 同上 |

### 10.4 各結果的**預先聲明意涵**(避免事後解讀)

| 觀測結果 | 對 Q1 的意涵 | 對 Q2 的意涵 |
| --- | --- | --- |
| native 的 F-vs-G 方向與 capped **一致** | 結論對 Gen0 規模穩健;large 可去「capped」caveat | —— |
| native 的方向**翻轉或消失** | 512 的結論屬 **scale-specific**,誠實記錄 | —— |
| 效應量(log-ratio)在 native 下**顯著縮小** | —— | 佐證「guidance 價值集中在小 Gen0」的機制敘事 |
| 效應量在 native 下**仍維持** | —— | **更強**的證據(即使抽滿仍有效) |

**⚠ 對 Q2 在 large 上的預先揭露(必須現在說,不能等看到資料):**
design §12.2(B)2 指出「Q2 需要一個效應量本身量得出來的 shape」,而
**capped-large 的五個 seed 全落在 `η_large` 之內、兩臂無法區分**(§9.2)。
因此 **Q2 在 large 上有極高機率得到「null → null」這種無區辨力的結果**。
**這是預先寫下的預期,不是事後的辯解;若真的出現,它不構成任何方向的證據。**
(同一節把 medium 納入 addendum 的理由——「medium 是唯一兩臂差異可被量測的 shape」——
**已由 design §13.6 判定作廢**,因為那些 0.36×–2.12× 的數字正是汙染物;
§12 Q2 在 medium **final 端點**上的跨 P0 稀釋比較記為 `NOT_EVALUATED`,**Q3 不受影響**。
這條更正屬 medium 附冊,此處僅記錄它同時削弱了「Q2 在哪個 shape 上可讀」這個前提。)

### 10.5 Native large 的 pins(**已 fail-closed 驗證,可以現在寫定**)

`[CODE AUDIT]` `native_status.json.shapes.large.preflight_global`(撰稿時讀取):

| 項目 | 值 |
| --- | --- |
| `native_gen0_expected` | **11,405** |
| runner | `scripts/run_pershape_seed_native.py`,`runner_sha256 = ae2584a6e461cd460ac29f234661f67dea604ca9a84d230d3ed7d4e41b743d89` |
| `ductile_force_p0_in_driver_env` | **`false`**(native 變體不設此環境變數——這正是自變數) |
| `R_s` / `eta_s` | `180336.0` / `0.12284585545668891`(**沿用 capped 版的同一組 pin**) |
| `rbs_mb` | **0**(與 capped large 相同) |
| `lock_b_sha256` | `3ac9768768ac088596687c47635bd6b8b5018d67cecc3f08e69ba2857b0ce59b` |
| `ga_weights_file` / sha256 | `out-capped/ga-weights-large.json` / `9fcd25173c6773e4ec787f51fcab372e9c5a0cf8457c176c475b8949df562c70`(**與 capped 版逐位元相同的 treatment**) |
| activated genes | 同 capped 版 5 個 |
| seeds / GPU | 24001–24005,分別綁 hip 2 / 3 / 4 / 7 / 6,UUID 與 capped 版逐 seed 相同 |

`[CODE AUDIT]` `stage5_native_baseline/seed_*/large/ga_init_evidence.json` 五個 seed 一致:
`pop_size_at_construction = 11405`、`_pop_size_at_construction = 512`、
`decay_type_at_construction = "large_space"`(＝`ga.py:116` 的 decay 法則 1 已安裝)、
`native_p0_variant: true`、`n_gen: 30`、`period: 5`、
`weights_gene_keys = ["group_0"]`(baseline 臂,只有未受 treatment 的 group_0 GEKO 權重)、
`weights_sha256 = 56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f`。
**⇒ Gen0 確實膨脹到 11,405,fail-closed 的膨脹檢查通過。**

### 10.6 **執行實況(觀測時間:2026-08-13 02:39 UTC)—— ⚠ 已被 §10.7 取代**

> **⚠ 更正(2026-08-18)。本小節是 2026-08-13 的快照,它記錄的每一項「未啟動 / 空目錄 / `done: 0`」
> 都已於 2026-08-17 失效。§10.8 自己也要求「native 完成後必須更新 §10.6」——
> 這是那次更新。**
>
> **現況:** native large 已於 2026-08-17 執行完畢,五個 seed 的 7× 端點都在
> `stage5_native_baseline/seed_*/large/champion_interleaved.json`(mtime 2026-08-17 13:13–13:27),
> §10.7 的表 N1–N5 即由這批 artifact 填入。
> **`stage5_native_guided/seed_*/large/` 仍然沒有 `champion_interleaved.json`,但那不是缺口** ——
> worker 把**兩臂寫進同一個檔**(`arms: [F, G]`、`median_gflops {F, G}`),
> 所以端點檔只出現在 baseline 側。下表「arm F `FRESH`(未啟動)」與
> 「guided large 五個目錄完全是空的」兩句,**在 2026-08-13 為真,現在都已為假**。
>
> **以下原文保留為當時的觀測紀錄,不改寫。**

`[CODE AUDIT]` `native_status.json`(`ts_utc: 2026-08-13T02:37:02Z`)、
`native_remeasure_status_large.json`(`ts_utc: 2026-08-13T02:38:09Z`)、
`s14_native_driver.log`,以及撰稿者對 `stage5_native_{baseline,guided}/seed_*/large/` 的
**唯讀**目錄稽核:

| seed | arm G 狀態 | arm F 狀態 | 目錄實況(G) |
| --- | --- | --- | --- |
| 24001 | `PARTIAL_NO_CHECKPOINT` | **`FRESH`(未啟動)** | 有 `ga_init_evidence.json`、`resume_record.json`、optimization log(9 行);**無 `trajectory.jsonl`、無 checkpoint、`2_BenchmarkData` 為空** |
| 24002 | `PARTIAL_NO_CHECKPOINT` | **`FRESH`** | 同上 |
| 24003 | `PARTIAL_NO_CHECKPOINT` | **`FRESH`** | 同上 |
| 24004 | `PARTIAL_NO_CHECKPOINT` | **`FRESH`** | 同上 |
| 24005 | `PARTIAL_NO_CHECKPOINT` | **`FRESH`** | 同上 |

- `native_status.json.shapes.large.state = "gate_open__medium_complete"`;
  `completion = {done: 0, total: 10}`;`all_complete: false`。
  driver 每 ~15 分鐘由 cron 巡一次,最近數次一律
  `status: 10/20 complete, 0 degraded observation(s)`(那 10 個是 native **medium**)。
- **guided large 五個目錄完全是空的**(`ls stage5_native_guided/seed_*/large/` 無任何項目)。
- **native large 7× remeasure:cron 待命中,尚未執行。**
  `native_remeasure_status_large.json` 五個 seed 一律 `"wait_arms_incomplete"`;
  該檔已記錄預定 deviation:「runs on idle GPU 5, not the seed's Lock-A search card
  (large occupies 2,3,4,6,7); within-pair ratio cancels card offset」。

**時間軸(撰稿者由檔案 mtime 與 `resume_record.json` 重建):**

| 時刻(UTC) | 事件 | 證據 |
| --- | --- | --- |
| 2026-08-12 22:34:29 | 五個 native large baseline session 啟動(`session_index: 0`、`resume_requested: false`) | `resume_record.json` |
| 2026-08-12 22:34:33 | 寫出 `ga_init_evidence.json`(`pop_size_at_construction = 11405`) | 檔案 mtime |
| 2026-08-13 01:19:20 – 01:21:57 | 五個 log 最後一次寫入,末行為 `GA:INFO Starting optimization...`(前一行為 `GA:INFO Sampling initial population...`) | log mtime + 內容 |
| 2026-08-13 01:40–01:41 | 首批 kernel build 與 `Data/00_Final.csv` 出現(seed 24001) | `1_BenchmarkProblems/**` mtime |
| 2026-08-13 02:39 | **觀測時刻**:仍無 `trajectory.jsonl`、無 checkpoint | 目錄稽核 |

**撰稿者對狀態的精確判讀(與粗略描述的差異必須說明):**
截至觀測時刻,五個 baseline seed 的 `space.sample(11405)` **已完成**(耗時約 2 h 45 m –
2 h 48 m,與 design §12.6 實測的「~2.9 h/arm 單執行緒 CPU 拒絕抽樣」一致),
目前處於 **Gen0(11,405 個候選)的 GPU 評估階段**。
`trajectory.jsonl` 的第一列要到**第 1 代完成後**才寫出,故現在**尚無任何 trajectory 列**——
這與 `native_status.json` 的 `PARTIAL_NO_CHECKPOINT` 一致。
**因此:說「還在 Gen0」正確;若要精確,是「Gen0 抽樣已結束、Gen0 評估進行中」。**

**風險提示(design §12.6,非新政策):** Gen0 全程**無 checkpoint 保護**,
native large 的無保護窗口約 **25.5 h**;design §12.6 明列 native large 是**對 reboot 最敏感**的
工作負載。§3.5 的機房供電故障若重演,會使該 seed 從 gen 0 重來。

**一項相關的、已處置的基礎設施缺陷(必須記錄,因為它差點寫進科學紀錄):**
`quarantine/native_gen0_guard_false_positive_20260812/` 保存了一份
`native_gen0_degraded.json`(seed 24005 / **medium** / arm G,`recorded_utc 2026-08-12T07:38:06Z`)。
它**不是** design §12.7 預註冊的 stock-Ductile fail-open 觀測,而是
`run_pershape_seed_native.py` 的 Gen0 guard 缺陷:guard 在 `--resume` run 上比對的是
**第 2 代(post-decay)**族群。四條獨立證據:`observed_gen0 = 5958`
恰為 `ga.py:116` 的 decay 值 `int(512 + (11405−512)/2)`,而非 fail-open 值 `11405 // 2 = 5702`;
log 中零筆 `Max iterations reached`;`trajectory.jsonl` 的 generation 1 記錄
`generation_candidate_count = 11405`;marker 自身 `halved_target 5702` 與 `observed_gen0 5958` 矛盾。
**判定:FALSE POSITIVE,不得進入科學紀錄。** 該缺陷的嚴重性對 **large** 最高
(§12.6 指出 native large 最易被 reboot 打斷),已於**任何 large run 啟動前**由 kill/resume
驗證測試發現並修正(resume 路徑改為要求來自 banked trajectory 的正面證據,fail-closed)。

### 10.7 表(**形狀為執行前固定, 內容於 2026-08-17 由實測 artifact 填入**)

> **來源:** `stage5_native_{baseline,guided}/seed_*/large/` 之下的
> `trajectory.jsonl`、`optimization_result.json`、`champion_interleaved{,_raw,_status}.json`。
> **表的形狀未因結果而更動。** 尚未由獨立 verifier 重算, 因此本節數字標為
> **[measured, 未經獨立 verifier 複核]**。

#### 表 N1 —— Native large run 層級量

| seed | arm | 實際 Gen0 母體 | `generations_run` | 早停 | `cumulative_complete_evals` | `best_fitness` |
| --- | :---: | ---: | ---: | :---: | ---: | ---: |
| 24001 | G | 11,405 | 20 | **YES** | 29,380 | 587,343 |
| 24001 | F | 11,405 | 30 | no | 31,747 | 590,435 |
| 24002 | G | 11,405 | 30 | no | 31,991 | 565,845 |
| 24002 | F | 11,405 | 30 | no | 31,639 | 579,219 |
| 24003 | G | 11,405 | 30 | no | 31,821 | 584,791 |
| 24003 | F | 11,405 | 26 | **YES** | 30,953 | 573,870 |
| 24004 | G | 11,405 | 30 | no | 31,864 | 563,518 |
| 24004 | F | 11,405 | 29 | **YES** | 31,757 | 551,470 |
| 24005 | G | 11,405 | 23 | **YES** | 30,225 | 569,997 |
| 24005 | F | 11,405 | 30 | no | 32,013 | 580,795 |

**Gen0 母體十個 run 全部是 11,405, 與 fail-closed 期望值相符。**
**早停 4/10**(判準 `period = 5`, `tol = 8e-4`, `ga.py:184-197`), 其餘 6 個跑到 `n_gen = 30` 上限。
**代數 20–30, 但 `complete_evals` 落在 29,380–32,013(帶寬為平均值的 8.4 %)** ——
原因是母體幾何衰減, 前 20 代即消耗約 92 % 預算, 後期每代僅約 250–280 次。
**因此代數不可當搜尋量的代理;AUC 一律對評估數積分**(見 `report-source-index.md` 三個計數器的定義)。

*Source(將來):* `stage5_native_{baseline,guided}/seed_*/large/{trajectory.jsonl, optimization_result.json, driver_status.json}`

#### 表 N2 —— Native large 早期搜尋(Q1 / Q2)

| seed | Gen0 best G | Gen0 best F | 方向 | gen-10 G | gen-10 F | 方向 | `B*` | AUC F/G | 方向 |
| --- | ---: | ---: | :---: | ---: | ---: | :---: | ---: | ---: | :---: |
| 24001 | 510,192 | 511,367 | + | 581,308 | 575,858 | − | 29,380 | 0.9994 | − |
| 24002 | 496,728 | 516,074 | + | 547,815 | 557,692 | + | 31,639 | 1.0293 | + |
| 24003 | 458,644 | 505,837 | + | 572,912 | 564,437 | − | 30,953 | 1.0388 | + |
| 24004 | 484,090 | 483,087 | − | 542,258 | 522,916 | − | 31,757 | 0.9853 | − |
| 24005 | 511,342 | 487,432 | − | 566,572 | 561,068 | − | 30,225 | 0.9733 | − |
| **為正的 seed 數** | | | **3/5** | | | **1/5** | | | **2/5** |

#### 表 N3 —— Native large 7× interleaved remeasure

| seed | G median | F median | F/G | `ln(F/G)` | pinned floor 0.8844 | 經驗 floor(待重算) |
| --- | ---: | ---: | ---: | ---: | :---: | :---: |
| 24001 | 578,956 | 582,849 | 1.00672 | +0.00670 | 通過 | `NOT_EVALUATED` |
| 24002 | **498,236** | 579,018 | **1.16214** | **+0.15026** | 通過 | `NOT_EVALUATED` |
| 24003 | 588,193 | 564,302 | 0.95938 | −0.04147 | 通過 | `NOT_EVALUATED` |
| 24004 | 558,618 | 548,563 | 0.98200 | −0.01816 | 通過 | `NOT_EVALUATED` |
| 24005 | 573,013 | 571,291 | 0.99699 | −0.00301 | 通過 | `NOT_EVALUATED` |

**`ln(F/G)` 中位數 = −0.0030;pinned non-regression 5/5;improvement 1/5(僅 24002)。**

> **⚠ seed 24002 的 +16 % 必須連著它的來歷一起讀, 否則會被誤解。**
> 它**不是**量測不穩: 兩臂在窗內都很緊(`max/min` = 1.024 / 1.031, 零 dropout)。
> 它是 **G 臂的 champion 撐不住**: GA 記的 `best_fitness = 565,845`, 7× 重測 clean median 只有
> **498,236(−11.95 %, 十個 run 中最大的 winner's curse)**。
> 該 champion(`9908df17…`)**只在第 30 代出現一次、被量過一次, 以 0.22 % 擠掉守了三代的 incumbent
> `11dbb233…`(GA 564,595)**;重測時它在 8 次獨立 invocation 中穩定落在 2,022–2,076 µs。
> **亦即該臂實質停在其 gen-1 水準(496,728)。**
> **這正是 design §12.3 要求 native champion 必須跑同一套 7× 重測的理由 —— 它真的抓到了一次。**

*註:* design §12.3 明訂 native champion **必須**跑與 capped 版**同一套** 7× 交錯重測協定
(同卡、同視窗、G/F 交錯、取中位數),起始臂沿用 `START_ARM = {large: F}`。
理由(§12.3 原文):native 約 30,600 evals 對 capped 約 7,689(4×),
**winner's curse 的向上偏差在 native 更大**,不跑同一套重測就無法分離
「真實效應量差異」與「量測協定差異」。**⚠ 上述那條預先記錄的 deviation 最終沒有發生, 這一點要更正:**
原本排定於閒置的 GPU 5 序列執行(因為當時 native large 的 GA 佔滿五張搜尋卡)。
**實際執行時 GA 已結束、卡片釋出, 於是五個 seed 各自跑在自己那張搜尋卡上、平行執行**
(`gpu_uuid_override: null`、`run_card_differs_from_search_card: false`, 五份 status 皆然)。
**所以 native large 與 capped large 在「同卡重測」這一點上是一致的, 沒有卡片層級的差異需要折算。**

**dropout 稽核(依 §7.2 的同一判準: 一次 repeat `< 0.95 ×` 該 arm 同窗 7 次的最大值)已重做:**
**native large 為 2/70 = 2.86 %**(24004 F 第 5 次 = 0.949、24005 F 第 6 次 = 0.925);
併入 capped large 後為 **3/140 = 2.14 %**。**不是零, 但與 medium 舊儀器的 42.5 % 不同量級。**

#### 表 N4 —— Q3:極值機制的 22× 操縱

| 量 | capped(P0=512) | native(P0=11,405) | 預測方向 | 判讀 |
| --- | ---: | ---: | --- | --- |
| Gen0 **中心** F/G 中位數 | **1.0197**(4/5 為正) | **1.0208**(**5/5** 為正) | 維持或擴大(預測 ii) | **預測成立** |
| Gen0 **極值** F/G 中位數 | **0.9719**(1/5 為正) | **1.0023**(**3/5** 為正) | 劣勢**擴大**(預測 i) | **預測被推翻 —— 劣勢不但沒擴大, 反而消失** |
| Gen0 有效候選數 | G 480–489 / F 480–491(/512) | G 10,743–10,793 / F 10,760–10,811(/11,405) | —— | 兩臂對稱, 無偏 |
| large vs medium 的擴大幅度比較 | —— | large **+0.0304**(0.9719→1.0023)vs medium **−0.0080**(1.0007→0.9927) | large > medium(預測 iii) | **預測被推翻 —— 方向相反** |

#### 表 N5 —— 跨 P0 對照(Q1 / Q2 的最終讀數)

| 量 | capped 512 | native 11,405 | 判讀 |
| --- | --- | --- | --- |
| final `ln(F/G)` 中位數 | **+0.0006** | **−0.0030** | 兩者都貼近 0;**跨 P0 的方向未翻轉成一個可讀的效應** |
| Gen0 / gen-10 / AUC 的為正 seed 數 | **1/5 / 2/5 / 3/5** | **3/5 / 1/5 / 2/5** | 全部落在 1/5–3/5, **無一達到預註冊的 ≥ 4/5** |
| non-regression(pinned / 經驗) | **5/5 / 3/5** | **5/5 / `NOT_EVALUATED`** | 經驗 floor 需獨立重算 |
| improvement | **0/5** | **1/5**(僅 seed 24002) | 該筆的來歷見表 N3 的警語 |

**逐 seed 的 `ln(F/G)` 在兩個 P0 尺度之間有 3/5 換號**(24001 −0.0749→+0.0067、24003 +0.0604→−0.0415、
24005 +0.0006→−0.0030), 而**十個 champion 全部不同**, 所以這**不是**同一個東西被量兩次。
**native 的 champion 品質 9/10 優於 capped(中位數 +6.4 %)**, 與預算差約 4× 相符。

**⚠ cross-P0 比較的界線(design §12.5):** native 版**兩臂共用 P0 = 11,405**,故 F-vs-G 對比在
native 內部乾淨不偏;但 **512 vs native 的效應量比較是稀釋讀數,絕對 champion 品質跨 P0
不可直接比**(預算不同)。

### 10.7a **三項預先註冊預測的判讀** —— 兩項被推翻

> **§10.3 的字面要求:「若結果與預測相反, 必須照實記錄為機制假說被推翻, 不得事後改寫預測。」**
> **以下即照此執行。三項預測寫於 2026-08-12, 早於任何 native large 資料存在。**

| # | 預測 | 實測 | 判讀 |
| --- | --- | --- | --- |
| **(i)** | guided 的 **Gen0 極值劣勢會擴大** | large: **0.9719(1/5)→ 1.0023(3/5)** | **推翻。** 劣勢不但沒擴大, 在 22× 放大之下**反而消失** |
| **(ii)** | guided 的 **Gen0 中心優勢維持或擴大** | large: 1.0197(4/5)→ **1.0208(5/5)**;medium: 1.0251(3/5)→ **1.0331(5/5)** | **成立。** 兩個 shape 都維持, 且為正的 seed 數都升到 5/5 |
| **(iii)** | **跨 shape 梯度**: large 的極值劣勢擴大幅度 **應大於** medium | large **+0.0304**(劣勢縮小)vs medium **−0.0080**(略為擴大) | **推翻。** 兩者方向相反, 梯度與預測的正負號相反 |

**這對 §6 的機制敘事意味著什麼 —— 只講資料支持的部分:**

§6 的假說是「guidance 把機率質量集中 → 壓縮上尾 → 期望最大值下降」。
**Gen0 池從 512 放大到 11,405 是這個機制最直接的操縱變因(22×), 而它給出的結果與預測相反。**

- **中心那一半站得住**(預測 ii 在兩個 shape、兩個 P0 尺度上都成立, 5/5)。
- **上尾那一半沒有站住。** 在 large 上, 池放大之後 guided 的極值反而追上並略微超前。
- **可能的讀法有兩種, 本檔不代為裁決:**
  (a) 上尾壓縮效應存在但**隨池大小衰減** —— 池夠大時 guided 也抽得到尾部;
  (b) capped-512 那個 0.9719(1/5)本身**樣本數太小**, 五個 seed 的一個中位數不足以支撐一個機制宣稱。
  **要分辨這兩者需要中間尺度的 P0, 本研究沒有跑, 記為 `NOT_EVALUATED`。**

**⚠ 不得由此推出「guidance 對 large 有效」或「無效」。** 這裡判的是**機制預測**, 不是 gate。
gate 判定屬 `staged/s14-guided-results.md` **§5.4**(owner 2026-08-18 指定;原指向的
`full-ga-baseline-vs-guided-outcome-report.md` 已解除授權)。

### 10.7b **兩支 2026-08-17 的診斷探針 —— 都不是端點**(2026-08-18 新增)

兩者都標 `is_endpoint: false`,**都不改動表 N1–N5 的任何一格**,在此並列揭露。

#### 10.7b.1 `large_xwindow/results/m6/` —— native large 的跨視窗重現性

同一批 native champion,**6 個獨立 window × 5 seed**,`--start-arm F`。

| seed | 表 N3 的單窗端點 `ln(F/G)` | m6 六窗平均 | m6 per-seed sd |
| --- | ---: | ---: | ---: |
| 24001 | +0.00670 | +0.00962 | 0.02152 |
| 24002 | **+0.15026** | **+0.14475** | 0.01537 |
| 24003 | −0.04147 | −0.02563 | 0.01252 |
| 24004 | −0.01816 | −0.02470 | 0.02036 |
| 24005 | −0.00301 | **+0.01568** | 0.01721 |

pooled dropout **34 / 420 = 8.10 %**(95 % 判準)。

**能說什麼:** large native 的端點是**單一 window** 量的,而窗間離散度是 0.0125–0.0215。
**seed 24005 換一個窗就翻號**(−0.0030 → +0.0157),因為它的效應量本來就小於窗間離散度。
⇒ **表 N3 的逐 seed 符號,對於效應量小於約 0.02 的 seed 並不穩定。**

**不能說什麼:**
- **不得併入表 N3、不得平均、不得取代端點** —— `LARGE_XWINDOW_MANIFEST.json` 的 `claim_boundary`
  逐字:「They do not replace the endpoint of record, **are not averaged into it**,
  and do not move any shape's S14 status.」
- **不得用 m6 的 sd 去宣告表 N3 的某個 seed「是在讀雜訊」。**
  m6 自己的 pooled dropout 是 **8.10 %**,而 native large 端點的 dropout 是 **2 / 70 = 2.9 %**
  (同一個 95 % 定義)—— **m6 比它要審判的對象髒約 2.8 倍**,拿它當分母偏保守,
  會把真效應誤判成雜訊。**兩者差 2.8 倍的成因 `NOT_EVALUATED`。**
- **不得套用 medium 的 `sd ≤ 0.01` 判準** —— `m6/summary.json` 的 `note` 明文禁止
  (「medium's sd &lt;= 0.01 belongs to medium's instrument-repair acceptance and is NOT applied」)。

#### 10.7b.2 `large_champrace_24002/results/race_m3/` —— 一個未解釋的 12 % 兩群分裂

seed 24002 **baseline 臂內部**的 champion vs 被取代的 incumbent 對跑,**與 guided 無關**。
`direction_convention` 逐字:「ratio &gt; 1 means the INCUMBENT (arm F) is faster than the CHAMPION (arm G)」
—— **與本檔其他各處的 F/G 語意相反**;實測 `geometric_mean_ratio = 0.98933`,即 **champion 快 1.08 %**。

**未解釋的觀測:** 同一顆 kernel(`config_hash = 9908df17…`)在兩支 8/17 探針上分成兩群 ——

| 來源 | arm G 的 median GFLOP/s |
| --- | --- |
| canonical 端點(表 N3 的來源) | **498,236** |
| `m6` 六個獨立 window | 499,076 / 492,228 / 498,780 / 488,781 / 497,714 / 485,541 |
| `race_m3` 三個 window | **558,420 / 559,859 / 569,037** |

**兩群相差約 12 %,機制 `NOT_EVALUATED`。**

**必須連著寫的三句:**
1. **canonical 端點已被 m6 六窗重現**(498,236 落在 485,541–499,076 之內),
   ⇒ **表 N3 用的值沒有問題,離群的是 `race_m3` 這支探針,而它不餵任何端點。**
2. **不得宣稱哪一組是「正確的」**,也**不得**由此宣稱 GA 記錄值系統性上偏。
3. **不得把 GA 記錄的 565,845 併進 `race_m3` 那一群當作第三個成員** ——
   它是搜尋期的單次評估、不同 harness,數值相近不等於同一機制。

> **⚠ 撰稿者的一次撤回(2026-08-18)。** 本報告的早期草稿曾寫「對跑值貼近 GA 值,
> canonical 端點才是離群的那一個」。**那與資料相反,已撤回** —— m6 的六個 window
> 重現的是 canonical。此處記錄這次撤回,是因為同一個問題已經錯過兩次
> (先前還有一次是「GA 記錄值的上偏是搜尋期量測的系統性現象」,亦已撤回)。
> **在那 12 % 被解釋之前,任何機制敘述都沒有依據。**

### 10.8 若 native large 未能完成 —— 預註冊的降階規則(design §12.7)

| 情境 | 預註冊處置 |
| --- | --- |
| deadline 不足 | 降為 3 seed(24001/24003/24005),**必須明確標註降階** |
| Gen0 未如期膨脹到 11,405 | runner 在**第一代評估時**檢查族群數;若 `!= 11,405`,先寫 `native_gen0_degraded.json` 再**中止該 run**。降級後的 run 既不是 512 也不是 11,405,屬**第三種條件**,納入會汙染配對 |
| 真的發生 stock-Ductile fail-open 降級 | **不是「跑失敗」**,是關於 Ductile 原生行為的**實質發現**,必須單獨陳述(哪個 shape/arm/seed、降到多少、兩臂是否對稱),**不得**當成基礎設施錯誤吞掉,**不得**靜默重跑 |
| deadline 壓縮 | **medium 優先於 large**(§12.7);large 若被砍,記為降階並標註 |

**本檔在 native 完成後必須更新的部分:** §10.6 的執行實況、表 N1–N5、§9.4 的殘餘不確定性
(第 6 項),以及 frontmatter 的 `native_campaign_state`。
**§4–§9 的 capped 結果不因 native 結果而改寫**——它們是不同 P0 條件下的獨立記錄。

---

## 11. Scope 與 claim boundary(large)

### 11.1 依 charter §8.6a `CLAIM-SCOPE-S14-20260810`

本檔的所有效應陳述皆為 **two-sided、bounded**,並強制標註:
**modest power(5 對 paired seed,非統計顯著性證明)**、
**scope 限受測 shape(large)、單一 development cluster、不一般化**、
**「P0-capped = 512 Ductile variant」**(native 半部尚未完成,§10)。

### 11.2 明確禁止的措辭(charter §8.6,未放行部分不變)

- ❌ 對 MI300X workloads 一般化;❌ production / deployment ready;❌ 跨架構;
- ❌ end-to-end tuning wall-clock speedup(未量測);❌ owner/team 應採用;
- ❌ 「large 通過」或任何等價措辭;❌ 把 5/5 non-regression 升格為 shape 層級結論;
- ❌ 「無效果」「模型沒用」——依 charter §8.5,負向結果必須**定位到層次**(本檔:`marginal-loss`)。
- ❌ physics-direction 歸因。conditional Arm S 的觸發規則(design §10.2:F 需於 ≥1 confirmatory
  shape 通過 directional gate)與其判定屬 formal report;**在觸發判定之前,歸因僅限
  「capped factorized initialization bundle vs baseline」**。

### 11.3 beat-native

`[CODE AUDIT]` charter §8.6a 2026-08-10(b) owner extension 已就 S14 把「勝過 native
`PredictionThreshold`」由絕對禁令解除為 **two-sided／等資料再說**——
**唯有**實際量測 native 並揭露 budget/selection confounding 時方可宣稱。
**本檔沒有任何 native `PredictionThreshold` 的量測,故不作任何方向的宣稱。**

### 11.4 一項治理提醒

design **§13 為 `PENDING_HUMAN_DECISION`**,尚未經 owner 核准。
> **⚠ 2026-08-18 例外:** 其中 **D2(pinned `η_s`)已於 2026-08-14 裁決並關閉**
> (`ETA-MARGIN-REMOVED-20260814`,方向與 D2 提案相反 —— margin 被移除而非維持)。
> 因此「在核准之前 §10.2 / §10.4 的 gate 維持原狀」這句話**對第四個子判準已不適用**;
> 現行 gate 為三項 margin-free 子判準,詳見 §4.4 的更正框。
凡本檔引用自 §13 的內容(D1 估計量、D2 雙 margin 揭露、D3 逐 shape claim 階梯、
§13.6 的紀錄更正、§13.7 的量測排序、§13.9 的殘餘不確定性)一律標示為
**「提案／待裁決」,不得讀成「已經決定」**。在核准之前,design §10.2 / §10.4 的預註冊估計量與
gate **維持原狀**。index §9 是該節的鏡像,同樣非權威。

---

## 附錄 A — Artifact / hash 索引(全部由撰稿者重算或直接讀取)

`run_root = /data1/perlee/rocm-libraries/agent_run/260809-s14-pershape-baseline/`

### A.1 Capped large —— 主要證據

| 路徑(相對 `run_root`) | 承載內容 |
| --- | --- |
| `stage3_baseline/seed_2400{1..5}/large/optimization_result.json` | `best_fitness`、`best_individual_hashes`、`generations_run` |
| `stage3_guided/seed_2400{1..5}/large/optimization_result.json` | 同上(F 臂) |
| `stage3_{baseline,guided}/seed_*/large/trajectory.jsonl` | 逐代 `best_gflops_so_far`、`generation_Q_median_any_valid`、`generation_any_valid_count`、`cumulative_complete_evals` |
| `stage3_baseline/seed_*/large/champion_interleaved.json` | `remeasure.{G,F}`(7 repeat)、`median_gflops`、`F_over_G_median_{ratio,log_ratio}`、`threshold_evaluations`、`arms.{G,F}.resolution_provenance`、`measurement_metadata` |
| `stage3_baseline/seed_*/large/champion_interleaved_raw.jsonl` | 14 筆帶時間戳的原始量測(§7.3 的視窗) |
| `stage3_baseline/seed_*/large/champion_interleaved_status.json` | `status`、`start_arm`、`verified_gpu_uuid`、`eta_s`、`nonregression_floor`、`wall_seconds_monotonic` |
| `stage3_{baseline,guided}/seed_*/large/driver_status.json` | GPU UUID、`DUCTILE_FORCE_P0`、`DUCTILE_PERSIZE_RBS`、起訖時間 |
| `stage3_guided/seed_*/large/ga_init_evidence.json` | `pop_size_at_construction = 512`、`weights_sha256 = 753d629c…` |
| `stage3_{baseline,guided}/seed_*/large/1_BenchmarkProblems/*/Data/00_Final.csv` | `WinnerGFlops`、`WinnerTimeUS`(§7.1、§7.4)。**不得**用 `**/Data/00_Final.csv` glob(會誤中 `remeasure_work/` 的副本) |

### A.2 Pins / locks / treatment

| 路徑 | 內容 |
| --- | --- |
| `noise/per_shape_noise.json` | `η_large = 0.12284585545668891`、`nonregression_floor = 0.8843999774850838`、`δ_large = 0.13071011471940674`、`R_s = 180336.0`、`n_residuals = 21`、公式 |
| `agent_run/260807-s14-baseline-run/stage2_noise/raw_repeats.jsonl` | pilot 63 筆原始 repeat;large 三個 anchor 的 max/min = 1.2373 / 1.4201 / 1.0245,`rbs_used = 0` |
| `env/guided_config_verification.json` | `lock_b_sha256`、`ga_weights_sha256`、5 個 gene 的 post-transform 單元測試 |
| `agent_run/260809-s14-pershape-guidance/lock/lock_b_guided_guidance.json` | Lock B SEALED,sha256 `3ac9768768ac088596687c47635bd6b8b5018d67cecc3f08e69ba2857b0ce59b` |
| `agent_run/260809-s14-pershape-guidance/out-capped/ga-weights-large.json` | sha256 `9fcd25173c6773e4ec787f51fcab372e9c5a0cf8457c176c475b8949df562c70`(撰稿者重算確認) |
| `agent_run/260809-s14-pershape-guidance/derivation/derivation-manifest-capped.json` | `per_shape_activation_log`(large 5/27、ρ、`S_g`、`H_norm`、TV、KL) |
| `config/s14-pershape-{,guided-}large-seed_2400{1..5}.yaml` | `RotatingBufferSize: 0`、`NumWarmups: 321`、`EnqueuesPerSync: 321`、`NumElementsToValidate: 128` |

### A.3 Deviation / quarantine

| 路徑 | 內容 |
| --- | --- |
| `quarantine/stopline_bug_20260812/README.md` + `seed_24002_large/`、`seed_24005_large/`、`seed_24002_tiny/` | `DEVIATION-REMEASURE-STOPLINE-20260812` 的三份 FAIL 紀錄(§3.2) |
| `quarantine/native_gen0_guard_false_positive_20260812/` | native Gen0 guard 的 FALSE POSITIVE 與其 additive annotation(§10.6) |
| `scripts/remeasure_interleaved_champion.py` | 今日 sha256 `5da5a7a27581af554c1b77d9a96955f1faad1db7a17fad3460cd960fc9a279bb`(與 index §8.4 記載的 `040db9cd…` 不符,§3.2) |
| `checkpoint_deviation.md`、`medium_remeasure_deviation.md`、`medium_remeasure_root_cause.md` | 其他 deviation 記錄(medium 相關者屬 medium 附冊) |

### A.4 Native large(live,**唯讀**)

| 路徑 | 內容 |
| --- | --- |
| `native_status.json` | `shapes.large`:5 seed × 2 arm 狀態、`preflight_global`、`completion = {done: 0, total: 10}`。**⚠ `done: 0` 是 2026-08-13 的快照,已於 2026-08-17 完成(2026-08-18 註)** |
| `native_remeasure_status_large.json` | 5 seed 皆 `wait_arms_incomplete`;GPU 5 deviation 已預先記錄 |
| `s14_native_driver.log` | cron 巡檢紀錄(每 ~15 分鐘) |
| `stage5_native_baseline/seed_*/large/ga_init_evidence.json` | `pop_size_at_construction = 11405`、`decay_type_at_construction = "large_space"`、`native_p0_variant: true` |
| `stage5_native_baseline/seed_*/large/*-optimization.log` | 9 行;末行 `GA:INFO Starting optimization...`。**⚠ 2026-08-13 快照;執行已於 2026-08-17 完成(2026-08-18 註)** |
| `stage5_native_baseline/seed_*/large/champion_interleaved.json` | **5 個檔**(mtime 2026-08-17 13:13–13:27),表 N1–N5 的來源 |
| `large_xwindow/results/m6/` | 跨窗重現性探針,同一批 native champion,6 window × 5 seed。`is_endpoint: false`(§10.7b) |
| `large_champrace_24002/results/race_m3/` | seed 24002 baseline 臂內部的 champion vs incumbent 對跑。`is_endpoint: false`(§10.7b) |
| `stage5_native_guided/seed_*/large/` | **無 `champion_interleaved.json`,但這是結構性的,不是缺口**(2026-08-18 更正):worker 把兩臂寫進 baseline 側的同一個檔(`arms: [F, G]`、`median_gflops {F, G}`)。原文寫「空目錄(guided 未啟動)」已為假 |
| `scripts/run_pershape_seed_native.py` | `runner_sha256 = ae2584a6e461cd460ac29f234661f67dea604ca9a84d230d3ed7d4e41b743d89` |

### A.5 Code 引用

| 位置 | 內容 |
| --- | --- |
| `projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py:47, 110, 113, 116, 118, 293` | `pop_size=512` 預設;`max_sp_sz > pop_size` 時膨脹至 `int(max_sp_sz*1.15)`;decay 法則 1 |
| `ga.py:291` | decay 法則 2(diversity `< div_thr=0.5` 時安裝,floor 256,不可逆) |
| `ga.py:302–304` | `DUCTILE_FORCE_P0` 時 fail-closed 斷言初始母體恰為 512 |
| `ga.py:289–293` | stock Ductile 的 fail-open:`MaxIterationsReached` → `pop_size // 2` 重試(§10.8) |
| `ductile/config/defaults.yaml` | `pop_size: 512`、早停 `period: 5` |
| `scripts/run_pershape_seed.py:324` / `run_pershape_seed_native.py:342` | `weights_sha256 = canonical_hash(weights)` |
| `scripts/make_guided_config.py:56–58` | ga-weights 檔案 sha256 的 fail-closed 檢查 |

---

## 附錄 B — 本檔的 `NOT_EVALUATED` 清單(逐項,附原因)

> `NOT_EVALUATED ≠ 無效果`。以下每一項都是**尚未量測或尚未可得**,不是**量測後為零**。

| 項目 | 為何 `NOT_EVALUATED` |
| --- | --- |
| ~~Native-Gen0(11,405)large 的**全部**結果(表 N1–N5)~~ | **已於 2026-08-17 執行完畢,表 N1–N5 已由實測 artifact 填入(§10.7)。此列於 2026-08-18 作廢** |
| ~~Q1 / Q2 / Q3 對 large 的答案~~ | **已於 2026-08-17 有結果(2026-08-18 更正)** —— 見 §10.7 表 N1–N5 與 §10.7a 的三項預測判讀。**Q2 仍如 §10.4 預先揭露的,在 large 上區辨力有限** |
| ~~跨視窗／跨日的重複性資料(任一 shape)~~ | **已部分為假(2026-08-18)。** `large_xwindow/results/m6/` 提供 **large native 的跨窗**資料(6 window × 5 seed,per-seed sd 0.0125–0.0215);`medium_pilot401/results/` 的九個 m = 12 cell 提供 **medium 的跨窗**資料。**仍然沒有的是: 跨「日」的重複性。**(2026-08-18 再更正:原文還寫「以及 large capped 的跨窗」,`m6_capped` 已於 08-18 產出,6 window × 5 seed,sd 0.01195–0.02742) |
| `η_large` 的 pinned vs 經驗之裁決 | 需要上一項;design §13 為 `PENDING_HUMAN_DECISION` |
| 直接的鎖頻證據 | 需 owner 執行 `rocm-smi --setperflevel high`(約 10 分鐘、零研究 GPU 時數);容器內 `/sys` 唯讀,先前嘗試靜默變成 no-op,實為第二個 control |
| 搜尋期汙染是否 arm-symmetric(含 large) | 逐代 benchmark CSV 未保留,**事後不可查證** |
| §6 中心-極值機制的正式確認 | 需逐臂完整 Gen0 fitness 分布或 Arm-S control;Arm S 為 conditional,觸發判定屬 formal report |
| Conditional Arm S 對 large 的結果 | 未跑;Lock C 待封 |
| `weights_sha256 = 753d629c…` 與檔案 sha256 `9fcd2517…` 之間的推導關係 | 本檔未重算(§2.1) |
| `remeasure_interleaved_champion.py` 今日 hash 與 index §8.4 記載值不符的原因 | 未查(§3.2)。large 的既有 artifact 不受影響(產出時間早於今日) |
| §8.3 champion 層級離散度 1.129/1.182/1.222 與撰稿者重算值 1.1249/1.1705/1.2205 的差異來源 | 未確認;排序與結論相同,**以 design §13.4 為準** |
| large 在 native 條件下的量測品質(dropout、視窗、經驗 η) | native remeasure 未跑,且**排定於 GPU 5**,不得沿用 capped large 的乾淨結論(表 N3 註) |
