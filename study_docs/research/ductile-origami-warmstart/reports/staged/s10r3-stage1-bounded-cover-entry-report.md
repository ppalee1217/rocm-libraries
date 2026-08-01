# S10R3 Stage 1 Bounded-Cover Entry Recovery — Verification and Closeout Report

## 1. 白話結論

S10R3 的固定 workload、證據鏈與獨立驗證都通過，但科學結果是
`negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`，不是 positive。

原因很直接：fresh support discovery 找到 114 個 distinct valid configs，deterministic
greedy cover 以 `K=C_greedy=19` 在 frozen cap 20 內成功建立 corpus；但 Mapping Pass A
處理第六個 required config 時，pinned KernelWriter 兩次都產生完全相同的 allowlisted
resource-overflow failure。A46.5 預先規定這個兩次可重現的完整 failure signature 必須
terminalize 為 mapping negative，不得第三次 retry、替換 config、執行 Pass B 或進入
native／GPU／correctness／noise。

| 欄位 | 結果 |
| --- | --- |
| Technical verification | `PASS` |
| Scientific outcome | `negative` |
| Criterion | `S1_ENTRY_BLOCKED` |
| Failure ID | `FT-BLOCKED-MAPPING` |
| Checkpoint state before terminal commit | `VERIFIED_PENDING_CLOSEOUT` |
| Outgoing edge | `null` |
| S11 authorization | `false` |

本報告支持「S10R3 在 observed operational valid support 中能建立合法 bounded-K corpus，
但 required mapping code generation 可重現失敗」。它不支持 Formocast ranking、
factorization、prior-mass、Gen0、GFLOPS、speedup、generalization 或 production claim。

本報告是 closure delivery 的一部分。只有 exact staged bytes 取得 `CLOSEOUT_ACK`、
exact-path local commit 與 post-commit audit 後，committed projection 才是
`CHECKPOINT_COMPLETE`。本報告不預填包含自己的 closure commit SHA。

## 2. 問題與 frozen 判定邊界

S10R3 要回答：在保留 S10 source pins、actual YAML、groups、candidate order、weights、
三個 sizes、correctness 與 noise 要求時，能否用 fresh、deterministic、最多 20 筆的
bounded-cover corpus 建立可信且可重現的 Stage-1 entry boundary？

正式順序固定為：

```text
G3 effective lock
  -> 32 global chunks
  -> 15 mechanically activated conditional streams × 32 chunks
  -> tri-state support classification
  -> deterministic bounded cover (K <= 20)
  -> Mapping Pass A
  -> frozen terminal negative on two identical complete failures
```

S10R3 不測 Formocast ranking 是否準確、factorization 是否有效、prior mass 是否改善、
Gen0 是否改善、未觀察 candidate 是否不存在，或 production readiness。

## 3. Frozen authority 與 identity

- A46.5 scientific authority commit：
  `8ae987bb89558c798b01eff2c27f0a212f534288`
- G2 durable lineage-seal commit：
  `b8e9b0a78a77d5fbd1948da8871e04c0ac165c58`
- G3 effective-lock commit：
  `6ac2f8541d1eb819caae634d087b664d15bf098d`
- Contract raw SHA-256：
  `f89f37b5b7585fdaaab30db4b2d29c50d951d468b5f39ff8c207cbed119177c0`
- Contract canonical SHA-256：
  `7af6cfe8db1c3d28c62e0454e98f4660666c2fad447c6b074669c3bd4df2d71d`
- Scientific/oracle projection SHA-256：
  `185c6ae6c7b255c1330b4723b8a241ba111c0d23715bdb28149b024f78729e1e`
- G3 effective-lock raw SHA-256：
  `2333589fada1df201d233807a8b7cdee10b7554e64cc61b3cc00d352f1b8e352`
- G3 effective-lock canonical self SHA-256：
  `fdebc1ea9128cf56e8b50dc911ccc77c713f00b7a73f7ba0645ca5870bc227b9`
- Ductile commit：
  `5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39`
- GEKO commit：
  `d32abacfd13579d1f523f035b7a10b0734c4ac47`
- Actual YAML SHA-256：
  `faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36`

GEKO 與 Ductile 保持各自 branch authority；current checkout、cache、container 或舊
S10R1／S10R2／S10R3-G2 evidence 都不替代上述 exact identities。G2 已封存為
immutable diagnostic provenance，沒有一筆 empirical row 被用作 G3 gate evidence。

## 4. Fixed support discovery

Formal discovery 沒有 early stop、extension、target replacement、seed retry 或
outcome-driven priority：

| Stream | Chunks | Draws |
| --- | ---: | ---: |
| Global | 32 | 16,384 |
| 15 conditional streams | 480 | 245,760 |
| Total | 512 | 262,144 |

- Ledger terminal digest：
  `91fae325397b5ea660f19f8147369b5c4e803d894a532f38d31c3726310f9584`
- Accepted occurrences／distinct hashes：`114 / 114`
- Rejected draws：`262,030`
- Rejection taxonomy：全部為 pinned `_validate_solution=false`
- Resolver、KernelWriter exception 與 harness exception：`0`

Raw chunks 的 first-to-last durable mtime boundary 約 9 小時 49 分；validator-child
measurement 合計 wall `3312.528274172917 s`、CPU `12031.912122000014 s`，最大 child
RSS `308560 KiB`。這些 measurement boundary 明列於 raw chunks，不把未知的完整
lineage accounting 補成 0，也不改 scientific outcome。

## 5. Support 三態與 guidance eligibility

| State | Atom count |
| --- | ---: |
| `supported_witnessed` | 205 |
| `support_unobserved` | 9,819 |
| `support_proven_absent` | 0 |

27 個 residual candidate genes 中，23 個的所有 candidate values 都被 witnessed；
以下 4 個 genes 至少有一個 unobserved value，因此不具 S11 guidance eligibility：

- `GlobalReadVectorWidthA`
- `GlobalReadVectorWidthB`
- `PrefetchGlobalRead`
- `DepthU`

`DepthU` 的 observed states 是：32／64／128 為 `supported_witnessed`，256／512／1024
為 `support_unobserved`。尤其 `DepthU=1024` 仍只是 stochastic non-discovery，不是
absence proof；actual YAML candidate list 與 baseline sampling semantics 都未修改。

Support classification：

- File SHA-256：
  `d3477cb6fc616b4ca10f28a4ce8ac798b3432b7116355aec73ca173c4a99a115`
- Semantic digest：
  `cb9e16051a03891b196ffdaa838def0fbaa8ce8fb8760c32a625191f7cb6e4e6`

## 6. Deterministic bounded cover

Fresh selector 從 raw accepted occurrences 重建：

- distinct witnesses：114；
- witnessed mandatory atoms：90；
- `C_greedy=19`；
- `K=max(10,C_greedy)=19`；
- frozen cap：20；
- non-gating `L_axis=18`；
- selector status：`selected`；
- selection digest：
  `54cd7fc21ba011426e9ff8e37ae1bf204f171c7f1800ea495184d6d73718fd1d`。

沒有使用 exact-solver 結果冒充 greedy，沒有第 20／21 筆 replacement，也沒有讀取
Formocast score 或 GFLOPS 選 corpus。

## 7. Mapping Pass A 的可重現 failure

Pass A request 固定為 19 configs × 3 sizes，order 與 hashes 都由 bounded-cover artifact
決定。兩個 append-only attempts 都在 slot 5、同一 config
`4ffcecf6c21213303a3a040cbae66c228beeab9e6aec9a0096579444fc9a89e1`失敗：

- category：`code_generation_nonzero`；
- error class：`KernelWriterAssembly_overflowedResources`；
- error code：`5`；
- worker return code：`23`；
- `processKernelSource` result：`-2`；
- failure signature：
  `faf718ce76eda0e8b1ab4525b67d1a0e2c35729b865e6f910c27134d45c9a7d7`；
- attempt-01／02 stdout SHA-256：
  `7dd033033b6cfbbf313fca86f77be358933b81421dddde68ed8722bbd380b79f`；
- attempt-01／02 stderr SHA-256：空檔
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；
- worker artifact SHA-256：
  `ade2bf1583b5e75a276cae8d63c9a128ffae678d788f66fc53287bbf28d7a58c`。

兩次 complete signature 一致，故 frozen A46.5 outcome matrix 唯一允許：

`negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`

Mapping corpus：

- File SHA-256：
  `e5847ab21d05cf23149ea9da43e8f159060bfbf43415e8de9ef25e7ea865db03`
- Semantic digest：
  `7e00c880b15fea9e1dcce92b75c2be37d12141a164e5b55ac805337b686a511b`

## 8. 合法未啟動的 downstream work

Mapping A 已 terminalize，因此以下 work／artifacts 必須不存在：

- Mapping Pass B 與 A/B parity corpus；
- native sentinel/runtime conformance；
- GPU environment evidence；
- three-anchor smoke／correctness；
- 63-cell noise evidence；
- positive compact gate record；
- S11 implementation或evidence。

這些是 `NOT_REACHED_BY_FROZEN_GATE`，不是缺漏。沒有為了取得較好結果而縮減或跳過
workload；protocol 的 negative branch 本來就禁止繼續。

## 9. Decision、reproduction 與 fresh verification

Decision：

- File SHA-256：
  `c324205db9bb9c1ebc94c806c3e9b95158dd74b466f774f30cf93fab2f6c6aa5`
- Semantic digest：
  `f25627f669ba58d33c228403c50918b1889da4b1ca7a36d753eca4e7f1e49abb`

Independent reproduction 從 raw evidence 重建同一 outcome：

- status：`PASS`；
- scientific outcome：`negative`；
- criterion／failure：`S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING`；
- edge：`null`；
- File SHA-256：
  `116efe1ac6653a306b810438d3a38263d8add4f1a3f52697ebf870d9fd57e5da`；
- Semantic digest：
  `788682b5111d4771877bb2c3bc52023e352e0fc78c856766a03fcb898f037793`。

Plan-A-blind fresh verifier 的 precloseout verdict：

- B01–B21：全部 `PASS`；
- S10R3-C01–C09：全部 `PASS`；
- C06–C08：依 frozen negative branch 為 `NOT_REACHED_BY_FROZEN_GATE` 並滿足 criterion；
- C10：`PASS_PENDING_CLOSEOUT`；
- technical verdict：`PASS`；
- blocking findings／evidence requests：`0 / 0`；
- phase-appropriate full suite：334 passed，3 個只屬 prelabel-absence lifecycle 的
  tests 明確 deselect；
- Verifier report SHA-256：
  `b91d6cde2f5d35a76b58783b389eb3136b99620a06e0c67a706300f706f51ee6`；
- Verifier verdict SHA-256：
  `82290523d625e0ba09d68f8d59670f1486ffc9b4529721e52b1843848eebb384`。

## 10. Resource 與 storage disclosure

- Formal CPU tree：`767 MiB` filesystem usage；
- Formal mapping tree：`76 KiB`；
- Reproduction tree：`944 KiB`；
- Formal GPU time：`0`，因 branch 未到達 GPU；
- Historical cumulative wall／CPU／transient peak 的未完整 telemetry 保持 `UNKNOWN`。

Resource estimates與未知 accounting 只作 record／notification；本次 fixed schedule、
evidence integrity與terminal reproduction 均完整，沒有 material safety、availability、
completion 或 storage condition。沒有因資源帳 optional stop，也沒有用 successor reset
歷史 consumption。

## 11. Claim boundary 與研究進度

已確認：

- fresh G3 support schedule 完整；
- tri-state support semantics 正確；
- bounded cover 以 `K=19 <= 20` 成功；
- required Mapping Pass A code generation 兩次可重現失敗；
- canonical terminal result為
  `negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`。

未確認且不能宣稱：

- unobserved candidates 不在 valid support；
- complete Mapping A/B parity；
- native helper conformance；
- GPU correctness、noise 或 performance；
- factorized guidance 有效；
- S11／S12／S13 任何結果。

因 outgoing edge 是 `null`，S11 維持 `not_activated`。任何新的 Stage-1 recovery 都需要
新的 scientific design authority；不能把本次 negative、G2 diagnostics 或未到達的
downstream work 改寫成 `S1_ENTRY_GO`。

## 12. Closeout boundary

本次 terminal delivery 只納入 frozen implementation／tests、G3 registry與 reached
manifests、decision、這份 report，以及四份 parent/design/index projection。以下內容
不會被 stage 或 commit：

- protected `.agents`／`.claude`／`.cursor` 與 general-rule edits；
- S00／S10 post-closeout editorial changes；
- experiment guide、cache、`a.out` 或其他 unrelated untracked files；
- G2 retired bulk evidence；
- absent sentinel／GPU／correctness／noise／positive gate artifacts；
- S11 implementation或report。

Push 未授權且不會執行。`CLOSEOUT_ACK`、closure commit與 post-commit audit 由同一
fresh verifier lineage在 exact staged bytes 上完成。
