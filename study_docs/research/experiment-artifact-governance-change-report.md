# 實驗 artifact 治理改版：白話完整說明

狀態：repository-wide prospective governance change 的獨立說明文件  
適用範圍：這個 repository 之後新開始或重新 rebaseline 的 experiment、checkpoint、
successor、generation、execution tranche 與 closure unit  
主要實作 commit：`df02aacb0aecdafb66a778dda390270c5e18d9e0`

## 一分鐘看懂這次改了什麼

舊流程把太多不同性質的檔案都當成「一個 byte 都不能改」。這確實能保護實驗，但也
造成一個普通 timestamp、resource estimate 或 command summary 寫錯，就可能被當成整個
科學實驗身分已毀損，必須重開 binding、generation 或 successor。

新版改成 **milestone-level immutability**：

- 真正決定科學結論的東西，seal 後仍然一樣嚴格，不能原地修改。
- 還沒 seal 的草稿、程式與測試，可以正常 review、修正與重新產生。
- 只負責操作紀錄的 bookkeeping，可以保留錯誤原文，再用可重播的 correction event
  修正 effective view，不需要重開整個實驗。

最重要的界線沒有放寬：任何會改變正式 input、seed、workload、sample inclusion、
execution order、measurement、threshold、outcome、claim 或 edge 的事情，都不能假裝成
bookkeeping correction。

## 為什麼要改

舊規則把「保存歷史」近似實作成「所有歷史都必須塞在一套不可修正的 append-only
machinery 裡」。這混在一起的其實有三種完全不同的東西：

1. 科學證據，例如正式 measurement row 與 decision；它們當然必須 immutable。
2. 尚未生效的候選版本，例如 implementation、schema 或 test；它們本來就需要 review。
3. 操作紀錄，例如 heartbeat、resource forecast 或 agent routing；它們要可稽核，但偶發
   metadata 錯誤不等於科學證據被改寫。

當這三種東西使用同一個最嚴格規則時，治理程式會逐漸比實驗本身更複雜。過去流程曾
走向 single giant ledger、額外 generation、inode／`procfd`／signal／dumpability 防護與
大量 lifecycle repair。這些機制有些能處理 crash，但它們不是每一個研究 checkpoint
都需要的科學要求。

新版保留真正防止 outcome-dependent manipulation、evidence replacement 與
cherry-picking 的 hard boundary，同時拿掉普通 bookkeeping error 對整個 binding 的
連鎖破壞。

## 三層 artifact 模型

Artifact 是實驗產生、讀取或用來控制流程的檔案或 record。分類依據不是副檔名或檔案
放在哪個 directory，而是它「控制什麼」或「能證明什麼」。

### Layer A：sealed scientific milestones

Layer A 是已經 seal、會直接控制或支持科學結論的正式內容。

典型成員包括：

- approved research authority、checkpoint design 與 formal amendment；
- frozen contract、effective lock、source pins、formal inputs；
- workload、candidate registry、seed、threshold 與 stopping rule；
- formal selection、mapping、model output 與 measurement rows；
- correctness、noise、performance evidence；
- decision、independent reproduction、terminal report、parent projection 與 outgoing edge。

資料流是：

```text
design owner → 核准科學邊界 → selected candidate
seal mechanism → 綁定 exact path/tree/hash → Layer-A identity
runner/verifier → 只讀 sealed identity → formal evidence／decision
closeout → 驗證 evidence 與 claim → terminal report／edge
```

例如，一份 lock 綁定 `seed=17` 與 100 次 measurements；看到結果後不能把它改成
`seed=23` 或只保留 80 次，再稱為同一個實驗。需要改時必須建立 explicit amendment、
new version 或 successor，並交代舊證據能不能重用。

Layer A 的規則仍是最嚴格的：不能原地覆寫、刪除、重排或用 correction event 取代。

### Layer B：pre-seal candidates

Layer B 是尚未生效、也還不能用來支持科學結論的候選版本。

典型成員包括：

- design／amendment draft；
- contract、schema、fixture 與 manifest candidate；
- Plan-A、Plan-B；
- implementation candidate、pre-evidence test 與 audit draft。

資料流是：

```text
author／implementer → 建立候選 revision → reviewer／tests
reviewer → 要求普通修正 → 新 revision 與 content hash
seal gate → 選定唯一完整 revision → 轉成 Layer A
```

例如，正式 evidence 尚未開始前發現 schema 把一個 integer 寫成 string，可以修 schema、
重跑 pre-evidence tests、記錄新 hash，再 seal 正確版本。不需要只因這個候選修正建立
新的 scientific generation。

Layer B 的限制是：partial candidate、已 supersede 的 candidate 或沒有被選中的版本，
都不能冒充 effective authority 或 formal evidence。

### Layer C：operational bookkeeping

Layer C 是協助執行、監控及稽核，但不直接決定科學結論的紀錄。

典型成員包括：

- live run state、heartbeat；
- agent／role routing；
- resource telemetry 與 forecast；
- command admission／summary；
- repair history、non-outcome audit 與 workspace observation。

資料流是：

```text
runner／agent → 發布 operational event → immutable original bytes
correction writer → 指向錯誤 event → separate correction event
projection → 依固定 ordering 重播 originals＋corrections → effective state
verifier → 檢查 correction 沒碰科學欄位 → continue 或 fail closed
```

例如，已發布 event 把 estimated storage 寫成 `3 GiB`，之後確認正確值是 `5.4 GiB`。
原始 event 不刪除；新增一筆精確指向它的 correction。Projection 重播後顯示 `5.4 GiB`，
稽核者仍能看到原本寫錯什麼、誰在何時更正，以及更正沒有改變 sample 或 outcome。

這種 correction 不得用來改正式 input、sample inclusion、execution order、measurement、
outcome、claim 或 edge。只要 `scientific_impact` 不是 `none`，Layer-C correction 就必須
停止，改走正式 amendment／successor。

## Correction event 實際怎麼工作

最小 correction 包含：

```yaml
event_type: operational_correction
target:
  path: run/events/resource-0007.json
  sequence_or_id: resource-0007
  raw_sha256: original-event-sha256
reason: original estimate omitted ledger bytes
corrected_payload:
  estimated_storage_bytes: 5718346578
author_or_actor: verifier-r5
recorded_at_utc: 2026-08-04T02:36:04Z
projection_rule: operational-last-correction-wins-v1
scientific_impact: none
```

Target 的 path、ID 與 raw hash 必須唯一命中仍存在的 original bytes。多筆 corrections
依 normalized UTC instant 與 correction hash 決定性排序；同一個 latest instant 出現
duplicate 或不同 payload 時 fail closed。Writer、replay、projection 與 verifier 使用
相同 canonical JSON 規則。

這不是讓錯誤「消失」，而是同時保留：

- 原始錯誤紀錄；
- 修正原因與 actor；
- 決定性的 effective state；
- 科學內容未受影響的可驗證證據。

## 舊流程與新流程的差別

| 情境 | 舊 default 容易發生的處理 | 新規則 |
| --- | --- | --- |
| Sealed seed、workload 或 threshold 要改 | 重開 successor | 仍然必須 amendment／successor |
| Formal measurement 遺失或被替換 | 重開 successor | 仍然必須 amendment／successor |
| Pre-seal schema／test 寫錯 | 可能連整個 binding 一起 poison | 修 candidate revision、重驗、再 seal |
| Resource estimate 或 timestamp 寫錯 | 可能被當成 immutable ledger failure | 保留原文，加 correction，重播、驗證、繼續 |
| Derived index 壞掉 | 可能要求新 generation | 從 sealed raw bytes 決定性重建 |
| Unrelated workspace drift | 可能要求全 worktree byte-for-byte 相同 | 只稽核 experiment boundary，不碰 unrelated path |
| 普通 repair 次數增加 | 可能碰到 numeric stop | 保留完整 history；數字本身不是 stop gate |
| 預估超過 5 GiB／2× | 可能被當成停止理由 | 預設 record＋notify；只有真實 availability／safety／completeness 問題才暫停 |

## 什麼時候可以修正後繼續，什麼時候一定要 successor

先問一個核心問題：這個改動會不會改變正式實驗「做了什麼、量了什麼、保留了什麼、
能宣稱什麼」？

| Direct evidence 顯示的影響 | 處理 |
| --- | --- |
| 只改 display、timestamp、resource estimate、command summary、routing 或 heartbeat | Layer-C correction，replay、verify、continue |
| 修未 seal 的 schema、manifest、implementation 或 test harness | Layer-B new revision，review、重新 seal |
| 可由 sealed raw bytes 唯一重建的 index／cache | 重建 derived view，不開 successor |
| 改 effective contract、lock、source/input、seed、workload、fixture、threshold、stopping rule 或 outcome matrix | Formal amendment／successor |
| 改 sample inclusion、execution order、comparability、measurement boundary、lineage、claim 或 edge | Formal amendment／successor |
| Formal selection、mapping、measurement、correctness／noise evidence 或 decision 被污染、替換、遺失或無法驗證 | Formal amendment／successor |
| Outcome 可見後才提出會提高想要 outcome 機率的 relaxation | R3 design authority；不能用 correction |
| 不確定是不是只有 bookkeeping | Fail closed，先取得 direct evidence，不猜測 Layer C |

Successor 不會自動繼承舊 empirical evidence。新 contract 必須把 predecessor artifacts
逐項分類為：可作正式 input、只能 diagnostic，或禁止讀取。

## 既有實驗怎麼遷移

這次 policy 是前瞻性的，不會回頭改寫任何既有科學結果：

- 已 sealed 的 authority、lock、raw evidence、decision、report 與 edge 保持 immutable。
- 已有效 contract 明定的更嚴格 lifecycle 仍然優先；general rule 不能靜默放寬它。
- 尚未 seal、沒有 outcome evidence 的 checkpoint，可以先做 pre-evidence rebaseline，證明
  A／B／C 分類與 human／machine authority parity，再採新版規則。
- Retired helper、failed generation 與 superseded binding 只保留 diagnostic provenance；
  沒有新 contract 的 exact reuse declaration 就沒有 scientific credit。
- 若 migration 會改 measurement、claim、lineage、stopping rule、hard lifecycle invariant
  或 evidence boundary，必須使用 `design-discussion`，不能當普通 implementation repair。

所以「保留舊 bytes」不等於「後續每個實驗都要複製舊機制」。歷史可追溯性與未來實作
選擇是兩件不同的事。

## Proportionate threat model：到底要防到哪裡

預設 runner 必須防止：

- accidental edit、omission、substitution；
- outcome 後改 protocol／evidence／claim；
- cherry-picking；
- 普通 concurrent process、crash、partial write 與 resume error。

預設不要求每個 experiment 自己對抗同一 Unix account 的 malicious process、
syscall-window inode swap、hostile `procfs`／file-descriptor table、惡意 `SIGCHLD`／
dumpability attack，或已取得 repository-owner 權限的 hostile actor。

若特定 design、external compliance 或 direct evidence 真的要求這種防護，要在 evidence
前明列，並改用 OS identity／container isolation、read-only storage、signature 或 external
artifact service。不能把完整 OS security framework 偷塞進一般 provenance helper。

## 對目前 S11 的具體意義

S11 是 model-only factorization checkpoint：它先用固定 CPU sampling 與 pinned native
Formocast path 建立固定 frame，再判斷哪些 residual genes 能形成下一關可使用的 guidance。
它還沒有 effective lock、formal evidence 或 scientific outcome。

目前分類如下：

- 已 committed 的 S11 design、fixed frame、contract 與 prelock authority 是受保護的科學
  邊界，不能因本 policy 靜默改 workload、seed、statistics、outcome 或 edge。
- 19 個尚未提交的 runner／package／schema／test files 是 Layer-B implementation
  candidates；正式 evidence 前可接受 contract-preserving repair 與重新驗證。
- Plan-A／Plan-B 與 pre-evidence audit report 還不是 scientific outcome。
- Storage forecast 是 Layer-C resource telemetry。S11 contract 明列
  `record_and_notify_only`，不能只因預估超過 5 GiB 就產生 scientific stop 或 downgrade。

Fresh verifier R5 正確發現：目前 fault-heavy worst-case 的 chunks＋ledger 投影約為
`5,718,346,578` bytes，比 5 GiB planning target 多 `349,637,458` bytes。這是有價值的
implementation／capacity information，但現有 direct evidence 同時顯示 filesystem 尚有
足夠空間，而且 workload、measurement 與 claim 不需要改。因此：

- 可以在 seal 前做 bit-packing 之類的 Layer-B compact repair，再重驗；
- 也不能把 5 GiB planning target 自動提升成新的 scientific hard gate；
- 只有真的出現 disk／allocation 不足、完整 workload 或 artifact preservation 無法完成、
  evidence integrity 受威脅，才需要在 safe boundary 暫停；
- 這個 ordinary pre-seal issue 不需要建立 S11 successor，也不構成 scientific negative。

## Repository 實際改了哪些東西

主要治理 commit `df02aacb0a` 修改 17 個 tracked paths：

- 新增 canonical policy：
  `study_docs/research/experiment-artifact-governance.md`。
- 新增 deterministic reference implementation：
  `study_docs/research/tools/experiment_artifact_governance.py`。
- 新增 17 項 unit tests：
  `study_docs/research/tests/test_experiment_artifact_governance.py`。
- 更新 repository general rule：
  `.cursor/rules/hipblaslt-onboarding.mdc` 與 `CLAUDE.md`。
- 更新 Cursor／Claude／Codex 三個 surface 的 `implement-verify-loop`。
- 同步三個 surface 的 `authority-gates.md` 與 `planning-contract.md`。
- 更新三個 surface 的 `design-discussion`，讓 artifact migration 先使用 A／B／C 分類，
  已有唯一 Layer-B／C 答案時不濫用 design debate。

Canonical policy SHA-256 是
`58c17b6af7b578afd3a18a05d82d46d84f3d818e8bce3c97e689dc19a32dd5cc`。
Reference implementation 與 tests 的 SHA-256 分別是
`3062cfb556dc95165b0bd8b1ba9721b7639414d99aabdf5c94e26b5a748b1376` 與
`8ce4fd8436eeb2e06b0315ddbe344e33a10f7c163c80e34759a4bce9d0eeed29`。

## 驗證證據

這份改版的 deterministic tests 覆蓋：

- 原始 bad operational bytes 保留與 deterministic correction projection；
- duplicate、same-time conflict、malformed target、錯誤 hash 與 ambiguous template fail closed；
- Layer-C correction 不能碰 contract、lock、formal evidence、decision 或 scientific fields；
- pre-seal candidate revision 只能選定 exact complete version；
- sealed milestone 只能透過 linked amendment／successor 變更；
- ordinary bookkeeping metadata 不會要求 successor；
- scientific input、sample inclusion、execution order、measurement、threshold、outcome、
  claim 與 edge 仍全部是 successor boundary；
- repository rule 有 live policy trigger；
- Cursor／Claude parity 與 Codex standalone inventory。

在 current S11 lineage 的重新驗證結果是：

- Governance unit tests：`17 passed in 0.07s`。
- Cursor／Claude `implement-verify-loop`、兩份 references 與 `design-discussion`：byte parity
  通過。
- `.agents/skills/implement-verify-loop` 與 `.agents/skills/design-discussion`：Codex
  `quick_validate.py` 通過。
- `git diff --check`：通過。
- 測試沒有啟動正式 experiment、沒有讀取 outcome labels、沒有執行 GPU workload、沒有
  安裝 dependency，也沒有改變 `perlee` container。

## 這份改版沒有改什麼

Repository-wide governance commit 與本說明文件都沒有修改任何 active checkpoint 的：

- hypothesis；
- formal workload、seed、candidate selection 或 execution order；
- threshold、metric、statistics 或 stopping rule；
- formal evidence、decision 或 scientific outcome；
- allowed claim、checkpoint edge 或 downstream dependency。

它也沒有授權 push、dependency installation、container mutation、destructive cleanup 或
unrelated workspace modification。

## Evidence boundary 與剩餘限制

這套 policy 能證明 correction 不會在允許的 schema／projection boundary 內改寫 science；
它不能證明所有未來 checkpoint 的分類天然正確。每個新 tranche 仍必須：

1. 讀 current policy 並記錄 identity；
2. 逐項分類 A／B／C；
3. 綁定 B→A seal 與 Layer-C correction schema；
4. 檢查是否有更嚴格的 existing contract；
5. 在 outcome 前 freeze threat model；
6. 用該 checkpoint 自己的 tests／fresh verifier 驗證。

只要 artifact 的真正 scientific impact 無法確認，就不能因為檔名像 bookkeeping 而猜成
Layer C。新版規則的目的不是降低科學標準，而是讓嚴格性只放在真正影響結論的地方。

## 權威文件

- [Canonical artifact governance](experiment-artifact-governance.md)
- [Experiment execution workflow](../../.claude/skills/implement-verify-loop/SKILL.md)
- [Design discussion workflow](../../.claude/skills/design-discussion/SKILL.md)
- [Reference projector](tools/experiment_artifact_governance.py)
- [Deterministic tests](tests/test_experiment_artifact_governance.py)
