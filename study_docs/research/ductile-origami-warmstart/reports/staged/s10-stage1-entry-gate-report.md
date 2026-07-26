# S10 Stage 1 Entry Gate — Verification and Closeout Report

## 1. 結論與狀態邊界

S10在frozen actual-guidance boundary下完成，結果為：

- technical verification：`PASS`
- technical goal alignment：`FULL`
- scientific outcome：`negative`
- criterion：`S1_ENTRY_BLOCKED`
- failure taxonomy：`FT-BLOCKED-MAPPING`
- outgoing edge：`null`
- verifier blockers／evidence requests／required unverified：皆為`0`

Actual YAML、三個same-space sizes、live-unreserved `gfx942`環境及30-row
mapping evidence均完整；但兩個locked anchors無法通過mapping prerequisite，而且
三個accepted rows沒有產生預註冊要求的genuine Formocast rejection。因此
`mapping_entry`是完整、可重現的`FAIL / S10-MAPPING-ENTRY-FAIL`。Smoke與noise依
negative-stop規則未啟用，並非缺漏；S11沒有eligibility。

這個結果只支持「S10正確得到mapping-negative entry decision」。它不支持Formocast
ranking、factorization、Gen0、speedup、convergence、generalization、deployment或
production claim，也不宣稱GPU reservation、exclusivity或future availability。

本報告是closeout delivery的一部分。只有本報告、三份authority projection、原
verifier對exact staged bytes的`CLOSEOUT_ACK`、exact-path commit及post-commit audit
全部成功後，S10才是`CHECKPOINT_COMPLETE`。本報告不嵌入包含自己的commit SHA，
也不預填post-commit事實。

## 2. Frozen authority與exact boundary

- Branch：`users/perlee/doc-study`
- Baseline HEAD：
  `a9de9111be7d11090bd2404ef9e2e5a1c60a2285`
- S00 incoming edge commit：
  `8d1be2af3e5033ee74a1a8e3b31536f132a014cb`
- Frozen Plan-B SHA-256：
  `3cb50d05c3481e4fb6d2a0fd9b23cb0e6876d2b9b0582af17a7220710e2a40d7`
- R10 adjudication SHA-256：
  `d0166dd259b9227df440e124afc49da1baba36e5dbfc66bd7796c0cbff0118df`
- Pinned Ductile：
  `refs/remotes/origin/ductile_integration` at
  `5d6bdc8a6438b5fc73a96e46a907f9a5b1cd4e39`
- Pinned GEKO：
  `refs/remotes/origin/users/pkamd/geko_pr` at
  `d32abacfd13579d1f523f035b7a10b0734c4ac47`
- Exact implementation whitelist：13 paths
- Exact delivery whitelist：17 paths

GEKO與Ductile是兩個獨立branch authorities；兩個exact commits分別materialize後才
形成ignored integration roots。Current checkout、GEKO branch附帶的Ductile files、
cache、installed module、build output或container內容都沒有取代任一source
authority。

本次negative-stop branch有11個present implementation paths。Whitelist中的
`s10-smoke-correctness.json`與`s10-noise-pilot.json`依決策必須保持不存在。因此
closeout是17-path whitelist內的15個present paths：11個implementation/evidence、
formal report與三份projection；prior blocker memo保持read-only historical
evidence。

## 3. Source、actual input與effective lock

兩個fresh roots各自完成：

1. 從pinned Git objects materialize Ductile與GEKO；
2. offline native `_rocisa` build與dependency/import audit；
3. pinned generator執行及complete output manifest；
4. strict raw witness、independent source model與actual Ductile runtime三層consume；
5. groups、candidate order、weights、sizes及兩root byte/semantic parity。

鎖定事實：

- actual generated YAML SHA-256：
  `faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36`
- expanded groups SHA-256：
  `0526a9b3c1d8a1bbe1db2cb03616bfda6e5a1f2dfad3826c0747d8dcb3ab9140`
- axis-order SHA-256：
  `926a6d9502546dda22ea2edc483c0f61ef74b3e378bcf32f222f17130bb668a3`
- search-space map SHA-256：
  `5785871bc0779fb67627943ef2ed5fde8e96647be7e0bb0db4f770473cd7a1a0`
- weights SHA-256：
  `56c34446385e93138944082b1801649271fd6a49df948aa41017cb05d012f34f`
- 30 indexed axes；expanded group cardinalities為`9918 / 3 / 2`
- 16個distinct generated sizes
- selected sizes：
  `[8,8,1,128]`、`[256,256,1,1024]`、
  `[2304,1024,1,214336]`

H4/R5依使用者standing rule直接在existing `perlee`做三次live samples，不預約。
Card 6有foreign KFD process且約65% VRAM allocation，因此不合格；deterministic
selection key選到visible card 0：

- architecture／partition：`gfx942 / SPX / NPS1`
- PCI：`0000:13:00.0`
- unique ID：`0x2e5e9f248283700d`
- serial：`692348002343`

有效lock：

- ID：
  `s10-lock-9fefc341a765885a03d07c00aba5fffd8bb1f2fe9333043d9d564140257c1115`
- raw SHA-256：
  `6e119788305913bcf0e69244c2c190d345cb1d360c6dc1f49323ddffcdd397f6`
- generation：`successor-003`
- ancestry：
  `successor-003 -> successor-002 -> successor-001 -> genesis`
- `evidence_reuse=false`

Lock是final pre-lock write；mapping、decision及其他outcome-bearing evidence都在
lock生效後才建立。

## 4. Iterations、repairs與deviations

### 4.1 Historical early blocker

最早read-only discovery因當時沒有可用actual YAML/provenance而產生
`reports/gen0-factorization-blocker-memo.md`。後續在不降低claim的前提下取得並
fresh生成actual artifact，故該memo只保留為historical recovery evidence，不再是
current terminal record，也未在本次修改或stage。

### 4.2 Retired generations

- Genesis／R7建立fresh dual-root pre-lock closure，但後續lifecycle recovery將它
  封存為ancestor。
- Successor-001第一次跑完30 rows時，3 rows因缺少`.duplicate`屬性而例外；R9兩位
  fresh reviewers交互詰問後一致判定這是harness defect，不是scientific
  rejection。該代被single-use claim並完整封存。
- Successor-002修正canonical duplicate prepass、typed validation boundary、
  role-aware gates、negative-stop與recursive lineage，得到3 accepted／27 typed
  rejections及同一mapping-negative outcome。Fresh verifier仍找到
  `S10-R9-SCHEMA-001`：九種非法cross-field documents會被schema誤收，因此技術
  verdict為`CHANGES_REQUIRED`，該代也被single-use claim並封存。
- Successor-003只修正該plan-preserving schema／test boundary，重新fresh
  prepare、lock、mapping及decision。九種非法mutation現在9/9拒絕，scientific
  outcome沒有被改寫。

封存完整性由原verifierrecursive重算：

| Generation | Raw tree | Entries | Regular bytes | Tree SHA-256 |
| --- | --- | ---: | ---: | --- |
| successor-001 | `r9-successor-001-lock/` | 11,788 | 12,279,134,329 | `bc99fb3a13ee74a118c3f75fff1d18387b1738e8a99cd1af34e660441c88bf65` |
| successor-002 | `r10-successor-002-lock/` | 11,792 | 12,279,373,335 | `088fd008995448bd3d99538acb0bc5e60391ff05e0da51ece6adae14a1dd1e19` |

每個successor transition只有一份claim；former canonical roots保持不存在，只有
successor-003是active canonical leaf。

### 4.3 Workspace與verifier corrections

- 兩次意外Python bytecode均立即停止並以no-clobber方式移到ignored quarantine；
  hashes為
  `f47cf0a23bae744cec628252f2d6833acc9135d90d69719b94b541b0bb3d32d2`
  與
  `f1e141102800cdedfb4c633824b6c1001e2145c39388b738819ac94441102676`。
  Active protocol path沒有`.pyc`。
- Verifier第一次semantic/lifecycle audit誤把「sealed archive raw root存在」當成
  failure。這只影響verifier-owned ignored script/result；修正為檢查former
  canonical roots後v2全部PASS，tracked implementation與canonical evidence未變。
- User-owned兩份`implement-verify-loop/SKILL.md`及兩份
  `authority-gates.md`保持原hash且排除於S10 delivery。

沒有未解deviation、partial result、network fetch、dependency install、new/other
container、container start/stop/recreate、credential write、S11+ work或push。

### 4.4 Closeout generated-YAML whitespace adjudication

Technical PASS後，exact YAML首次進入index時，
`LC_ALL=C git -c color.ui=false diff --cached --check` exit `2`，且只回報
`s10-generated.yaml` lines `49 / 24870 / 24894 / 24902`四個
`trailing whitespace` diagnostics。兩份pinned generator raw outputs、tracked
worktree與index bytes全都維持SHA-256
`faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36`
及Git blob
`1fd6fb401d5baebd4665a87e9002687fb725b2dc`；這四個bytes不是closeout手工寫入。

這造成兩個frozen requirements的衝突：full cached check原預期exit `0`，但Plan-A
同時要求generated YAML只能是exclusive raw byte copy，禁止normalize、手改或
reserialize。Main因此啟動兩位fresh `gpt-5.6-sol/xhigh` reviewers
`/root/s10_closeout_ws_a2`及`/root/s10_closeout_ws_b2`。雙方獨立立場、互相詰問及
同一candidate consensus的結論如下：

- 採用exact-bound closeout check-harness adjudication；不改任何YAML byte；
- 捨棄manual normalization，因其會破壞lock/provenance/size bindings；
- 捨棄new successor，因同一pinned generator只會重現同一bytes；修改generator或
  serializer則改變source authority；
- 捨棄attributes、filters、whitespace config與ignore options，因其擴張或隱藏
  state並可能遮蔽第五個error；
- technical verdict仍為`PASS`，pre-commit lifecycle仍為
  `VERIFIED_PENDING_CLOSEOUT`；不新增formal state；
- raw cached command必須誠實記為
  `EXPECTED_GENERATOR_DIAGNOSTIC / exit 2`，不能稱為PASS。只有完整aggregate
  whitespace predicate可PASS。

Reviewer A的主要objection是不可發明
`PASS_WITH_EXPECTED_GENERATOR_DIAGNOSTIC` vocabulary；Reviewer B的主要objection
是不能宣稱literal exit-zero已達成。Candidate consensus吸收兩點，最後兩位均
`AGREE`。

Final report restage後的aggregate predicate：

1. Run-A、Run-B、worktree、index四份YAML byte-identical，SHA/blob與
   provenance、size registry、effective lock bindings全數一致；postlock validation
   PASS。
2. Fixed-locale full cached check只出現上述四個semantic tuples，zero unexpected；
   raw transcript SHA-256
   `cb1f59f0593b306d69091fa08603536e387579894adcbf7caddc063b1c937344`
   是secondary evidence。
3. Target-only check重現相同四項；target-excluded cached、full worktree及combined
   target-excluded checks都exit `0`且無output。
4. Target的`whitespace / filter / text / eol` attributes全為`unspecified`；不使用
   suppression、filter、attribute、config override或hook bypass。
5. Final stage只能是15個present delivery paths；smoke/noise維持不存在，沒有
   blocker memo、rule/skill、S11+或whitelist-external path。
6. 任一hash/blob/diagnostic/path/mode/OID/absence/validation漂移都使裁決失效並停止。
   任一restage都必須重建manifest並重新取得ACK。

Original verifier只需fresh重驗上述closeout predicate與read-only postlock validation；
若canonical hash漂移才回完整technical loop。Post-commit固定locale range check也
必須只重現相同四項，target-excluded range必須完全clean。若更高authority或commit
hook硬性要求raw exit `0`，必須停止並human review，不得用`--no-verify`繞過。

此裁決不改scientific result、source、lock、measurement、gate、DAG、claim、
whitelist或report target；其唯一residual uncertainty是未測的remote/server policy，
而push本來就不在authority內。兩位reviewers均確認它保留frozen goal、
acceptance purpose、planned evidence、report target、checkpoint order/gates、
whitelist/authority invariants與claim boundary；因此依repository的
consensus-first治理不需要重複user review。若更高authority或commit hook要求literal
exit `0`，上述plan-preserving前提即失效，仍必須停止並交回human review。

## 5. Authoritative tracked artifacts

| Path | Raw SHA-256 / state |
| --- | --- |
| `projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10_entry.py` | `fdfe5a6a087d7ae580889766cf3a657e98a9ca9dda2b6a1095d44a1c1aae0717` |
| `protocol/v1/run_s10_entry.py` | `4c286ac6001d696bae19b688975531dfbbdc30074807e109578689d78113a051` |
| `protocol/v1/schemas/s10-entry.schema.json` | `22676831f8e889f6033cc2ed7d8a20dfd4a8ea049f840375d69e29cd22cc4c7f` |
| `protocol/v1/s10-entry-contract.yaml` | `029de2493df60318f2f3ba6ab656e6d85211eee67de7a28e1be2a3310b288a10` |
| `protocol/v1/inputs/s10-generated.yaml` | `faaa8d65014d30646b89b84a8e97395539e52684bef7b430804a63ef2d64cf36` |
| `protocol/v1/manifests/s10-yaml-provenance.json` | `2d120b41d38787c5888304f3e8fda6a033b22f554162d4a500d4d9150be24917` |
| `protocol/v1/manifests/s10-size-registry.json` | `71f253fc4d3ab7e23b078f14b254bf65d591f762b6f28aae32e24c87bab536be` |
| `protocol/v1/manifests/s10-environment.json` | `54bf91932023f9a261631d594a5cfb914ff4963c4faee60d2ae20f3b16e3f5d0` |
| `protocol/v1/locks/s10-stage1-entry-lock.json` | `6e119788305913bcf0e69244c2c190d345cb1d360c6dc1f49323ddffcdd397f6` |
| `protocol/v1/manifests/s10-mapping-corpus.json` | `9cd9429b79d6f2502741a454c8a8c0bb46de986fee79b6e2d6d762f86ca377ec` |
| `protocol/v1/evidence/s10-smoke-correctness.json` | absent by negative stop |
| `protocol/v1/evidence/s10-noise-pilot.json` | absent by negative stop |
| `protocol/v1/evidence/s10-decision.json` | `0dae417396c7565515f29e0dbd03fcade865c16fdf6bbcb6644581cbee1cc802` |

Contract semantic SHA-256為
`c2de2b08b837f1d9fd6590fb8f0c2aa2f3169db7fd134c76d89c6c24843f43d0`。
Successor-003 raw mapping及negative-stop hashes分別為
`06db88b1ef7e47e1ce7975de9192d35e1452687412b0912ed07c4ffd7c48c5bf`
與
`795ff86e20a49a78d66211216c4035cbc66a71fc9f0279bdad7259624f6c8473`。

## 6. Mapping、decision與stop semantics

Fresh mapping passes A/B均產生exact 30 rows：

- 3 accepted rows：同一config
  `83398232f63ccd4d6a7cc59520e8fb5096a62be9701c2e94aaa0a706430ff857`
  跨三個locked sizes；
- 27 rejected rows：
  `solution_resolution / pinned_validation_boundary_none /
  internal_subreason_unknown`；
- unexpected exception：`0`；
- genuine Formocast rejection：`0`；
- `mapping_evidence_integrity`：`PASS / complete`；
- `mapping_entry`：`FAIL / complete / S10-MAPPING-ENTRY-FAIL`。

兩個exact failed anchors：

- `00bf3b8b377414d01f1a92a5aa1aecf8ac4ed98fcd93ae54686df3aa1c42556a`
- `c57f853ddfb62e7150c36dced5f1c1774859aa46f459e8cb0b9d6049b7793c1a`

Ordered decision gates為：

| Gate | Role | Status | Execution |
| --- | --- | --- | --- |
| actual guidance | prerequisite | PASS | complete |
| three sizes | prerequisite | PASS | complete |
| H4 and environment | prerequisite | PASS | complete |
| mapping evidence integrity | evidence integrity | PASS | complete |
| mapping entry | entry gate | FAIL | complete |
| smoke/correctness | blocked absent | BLOCKED | not activated |
| noise stable | blocked absent | BLOCKED | not activated |

Decision是`negative / S1_ENTRY_BLOCKED / FT-BLOCKED-MAPPING / edge=null`。
`study_mode=ready_actual_yaml_guidance`只表示actual input分支成立，不表示entry GO。

Terminal audit重叫`mapping`、`smoke`、`noise`，三者皆exit `49`且回
`terminal_command_refused`；重叫`decision` exit `2`且回`already_exists`。Provenance、
size registry、environment、lock、mapping及decision六個canonical hashes前後完全
不變。

## 7. Independent verification

原fresh verifier簽出：

- verdict：`PASS`
- goal alignment：`FULL`
- blockers：`0`
- report SHA-256：
  `cbd4de132904a6be421cd29b871faec249c9e951641f707347be7b91f0d674d8`
- verdict SHA-256：
  `3a37d44b29f7650f126e52d1b2e3d9b17bc73f01081a98e34f8271b7c406be1c`

主要direct checks：

1. Exact `perlee` focused suite：`61 passed in 11.06s`。
2. R9九種invalid role/cross-field mutations：9/9以
   `schema_validation_failed`拒絕；canonical documents PASS。
3. Successor-001／002完整archive recursive rehash及active successor-003
   ancestry PASS。
4. Verifier-owned clean root fresh build helper並reproduce mapping；八個controlled
   fields與canonical evidence exact semantic equality。
5. `validate --phase postlock`回`POSTLOCK_VALID`。
6. Terminal refusal、blocked absence及六-hash invariance PASS。
7. 26個tracked S00 `protocol/v1` paths與HEAD byte-identical；staging空、
   unrelated hashes不變、無S11+ status path。

Fresh reproduction mapping SHA-256為
`152cfff642c4c0c76afed387b6cf94e0d4f4ddf9067cd18142b9e9ae01b3a9b1`。

## 8. Command ledger

所有GPU/ROCm、native build、generation、mapping及protocol checks都在exact existing
`perlee`、cwd `/src/rocm-libraries`執行；Python使用
`PYTHONDONTWRITEBYTECODE=1`與`-B`。

下列每行都是cwd `/src/rocm-libraries`中的exact runnable argv；共同env為
`PYTHONDONTWRITEBYTECODE=1`及
`PYTHONPATH=projects/hipblaslt/tensilelite`。

Implementer terminal sequence：

1. `/opt/venv/bin/python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10_entry.py prepare --scratch-root agent_run/260725-ductile-factorized-guidance-s0-s1-recovery/milestones/S10/final-prelock-r10-successor-003`
   → exit `0`，`PRELOCK_PREPARED`。
2. `/opt/venv/bin/python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10_entry.py prelock-check --scratch-root agent_run/260725-ductile-factorized-guidance-s0-s1-recovery/milestones/S10/final-prelock-r10-successor-003`
   → exit `0`，`PRELOCK_PASS`，所有postlock targets absent。
3. `/opt/venv/bin/python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10_entry.py lock --plan-b agent_run/260725-ductile-factorized-guidance-s0-s1-recovery/milestones/S10/plan_b.md`
   → exit `0`，`LOCK_EFFECTIVE`，live-unreserved card 0。
4. `/opt/venv/bin/python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10_entry.py mapping`
   → exit `0`，`MAPPING_COMPLETE`，30 rows。
5. `/opt/venv/bin/python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10_entry.py decision`
   → exit `0`，`S1_ENTRY_BLOCKED`，edge null。
6. `/opt/venv/bin/python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10_entry.py validate --phase postlock`
   → exit `0`，`POSTLOCK_VALID`。

Verifier commands：

1. `/opt/venv/bin/python3 -B -m pytest -q projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s10_entry.py`
   → exit `0`，61 passed。
2. `/opt/venv/bin/python3 -B agent_run/260725-ductile-factorized-guidance-s0-s1-recovery/milestones/S10/r10-verifier-successor-003/audit_schema_archive.py`
   → exit `0`，9/9 rejection與recursive rehash PASS。
3. `/opt/venv/bin/python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10_entry.py reproduce-mapping --output-dir agent_run/260725-ductile-factorized-guidance-s0-s1-recovery/milestones/S10/r10-verifier-successor-003/reproduce-mapping-001`
   → exit `0`，`MAPPING_REPRODUCED`、semantic parity true。
4. `/opt/venv/bin/python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s10_entry.py validate --phase postlock`
   → exit `0`，`POSTLOCK_VALID`。
5. `/opt/venv/bin/python3 -B agent_run/260725-ductile-factorized-guidance-s0-s1-recovery/milestones/S10/r10-verifier-successor-003/audit_terminal.py`
   → exit `0`，terminal refusal與six-hash invariance PASS。
6. `/opt/venv/bin/python3 -B agent_run/260725-ductile-factorized-guidance-s0-s1-recovery/milestones/S10/r10-verifier-successor-003/audit_semantics_lifecycle.py`
   → corrected v2 exit `0`，全部semantic/lifecycle criteria PASS。
7. `/opt/venv/bin/python3 -B agent_run/260725-ductile-factorized-guidance-s0-s1-recovery/milestones/S10/r10-verifier-successor-003/audit_boundary.py`
   → exit `0`，boundary/source hygiene/staging PASS。

Exact argv、cwd、environment、timestamps、exit codes、stdout/stderr hashes及complete
raw manifests由effective lock與ignored
`agent_run/260725-ductile-factorized-guidance-s0-s1-recovery/milestones/S10/`
closure保存。

## 9. Acceptance與claim boundary

| Oracle | Result | Verified conclusion |
| --- | --- | --- |
| O1 authority/scope/workspace | PASS | baseline、S00、exact scope、unrelated changes及empty stage正確 |
| O2 source/import/native lineage | PASS | pinned dual-source integration與offline native lineage可重現 |
| O3 actual input/dual generation | PASS | actual YAML與完整provenance identity成立 |
| O4 Ductile space/sizes | PASS | groups/order/weights與三個same-space sizes成立 |
| O5 live H4 | PASS | `perlee`即時選到符合條件的card 0；沒有reservation claim |
| O6 schema/contract/lock | PASS | 61 tests、9/9 negative matrix、recursive lock validation通過 |
| O7 mapping/Formocast | PASS | evidence完整且正確得到mapping-entry negative |
| O8 smoke/correctness branch | PASS | 因mapping FAIL而合法不啟用並保持不存在 |
| O9 noise branch | PASS | 因mapping FAIL而合法不啟用並保持不存在 |
| O10 decision/lifecycle | PASS | negative-stop、null edge、successor lineage與terminal immutability成立 |

沒有proxy、two-size/reduced mode、replacement candidate、synthetic rejection、
guessed metadata、threshold relaxation、partial result、source substitution或whitelist
expansion。S10完成的是negative checkpoint，不是positive study。S11維持
`not_activated`，沒有任何verified outgoing edge。
