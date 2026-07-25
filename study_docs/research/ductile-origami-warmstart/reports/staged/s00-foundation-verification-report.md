# S00 Evidence Foundation — Verification and Closeout Report

## 1. 結論與狀態邊界

S00 在 frozen CPU-only synthetic boundary 下得到：

- technical verification：`PASS`
- technical state：`VERIFIED_PENDING_CLOSEOUT`
- scientific outcome：`positive`
- criterion：`S00_EVIDENCE_READY`
- `AC-01`–`AC-10`：全部 `PASS`
- blockers／evidence requests／required unverified：皆無

這個 positive 結果支持 observer neutrality、durable checkpoint/resume parity、
artifact reconciliation、lineage與current-lock fail-closed semantics。它不支持 GPU
availability、Formocast mapping、GFLOPS／kernel performance、model quality、Stage 1
readiness或任何較廣的研究結論。

本報告是 AC-11 closeout delivery的一部分。只有本報告、三份authority projection、
原verifier對exact staged bytes的`CLOSEOUT_ACK`、exact 33-path closure commit及
post-commit audit全部成功後，S00才是`CHECKPOINT_COMPLETE`，且
`S00_EVIDENCE_READY -> S10`才從machine candidate edge成為verified edge。本報告不
嵌入包含自己的commit SHA，也不以placeholder或預填manifest identity冒充該
post-commit事實。

## 2. Frozen oracle與authority

- Baseline branch：`users/perlee/doc-study`
- Baseline commit：
  `60775f12843bee9f95cb0bef4e91de8bc4dc9dc3`
- Original Plan-B：
  `agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/plan_b.md`
- Original Plan-B raw SHA-256：
  `b8e7a458bb6cb6fa103e92c50eed5c11b2e964c354dd71d629c61cdeecc571d9`
- Recovery Plan-B：
  `agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/plan_b.md`
- Recovery Plan-B raw SHA-256：
  `3f64ec77def3960b67756b0af576bdb5d4f28683ed11a1df55956fe87c0e34c2`
- Exact implementation whitelist：29 paths
- Implementation-list canonical SHA-256：
  `9686eab5037145252bc2233e514e5a050b2662352c78d4dcd3ce7ecb716f6aa6`
- Exact delivery whitelist：33 paths
- Delivery-list canonical SHA-256：
  `0632d43fafc8bf583d0ebdad60f1c832d7be4a0022f08602bcff61ec135deb5e`

Recovery authority來自2026-07-25 standing delegation，以及兩位fresh design
reviewers `/root/s00_recovery_design_a`、`/root/s00_recovery_design_b`完整
cross-examination後的`AGREE`／`AGREE`。該共識只把六個`successor-001` paths append
到原exact authority，形成29/33 lists，並授權原implementer/verifier resume loop與
一個expanded closure commit；未授權snapshot、intermediate commit、push、
dependency install、container mutation、GPU/ROCm probe或S10 work。

## 3. Amendment與兩代lock

原verifier iteration 1找到三個technical blockers：

1. `BLOCK-S00-LOCK-SUBSTITUTION`
2. `BLOCK-S00-RECONCILIATION-FAILOPEN`
3. `BLOCK-S00-RAW-DIRECT-EVIDENCE`

在任何recovery bound source mutation前，Main append唯一一筆amendment：

- amendment ID：`s00-successor-recovery-001`
- `previous_entry_sha256`：JSON `null`
- canonical entry/head SHA-256：
  `ec0e72c60aaa2d4ea1b54545aa1c9cbd2039401447bcca6d0d374e1866ee77b2`
- appended ledger raw SHA-256：
  `92da8dde11de879c573018a1f968648cef6f328ba44cee06e83f3b379ce81619`

Predecessor generation永久保留且bytes未改：

| Artifact | Raw SHA-256 |
| --- | --- |
| genesis lock | `35d0c98cd9f6058fe21cd8723288d5bc34d68b87c3bf9e4bc9a0b7c488a0691c` |
| neutrality | `ada294f5cbf62643490564e52b8cb88092c8b6c07ad09ab7e8030f2bf436a315` |
| resume parity | `fe447f49989ad4996358cbeae60918c3209eebce314154ec022ad1e95b402281` |
| reconciliation | `bf6b83e739c6fc4c8dd437675f6b8f2cbeeceb31c3c287c71a877318cf04597a` |
| lineage fail-closed | `05a0fa9be80174a560de180ceb8bfe0399bb7ca01d625b0961910b97d1e46a82` |
| decision | `e73601ba108c31ac15d3372b8b951b8f5b50110071a5d74f8c5f982f5ac101c0` |

Genesis identity為
`s00-lock-6c9bc5c909f46d287cada9e8b8a3b74d51e6a36dabc50ab98218d7d4ac0c1946`，
parent為`null`。它與五份old evidence／decision保留作superseded provenance；
old decision不能成為current authority。

Effective successor：

- lock ID：
  `s00-lock-51744fdaf66b580118189ed0027b025eff2f67d733a0f6b06059df6dfe3b0ef3`
- lock raw SHA-256：
  `a68653a4edbf4a00228231b74ad944a2437e0aae1773c74df12db146d3265a4e`
- parent：上述genesis exact ID/raw hash
- generation/state：`successor-001`／`effective`

Verifier由raw bytes重算兩份Plan-B、29/33 literal lists與hash、baseline、contract、
六authorities、十一sources、六schemas、四fixtures、四seeds、formal-report target、
ledger、recovery authority、immutable predecessor bindings及lock body/self ID；
全部與successor lock一致。

## 4. Recovery實作與deviation紀錄

Recovery shared mutation只有amendment ledger加下列七個paths：

| Path | Pre-recovery raw SHA-256 | Recovery raw SHA-256 |
| --- | --- | --- |
| `projects/hipblaslt/tensilelite/Tensile/ductile/evidence.py` | `f6cbee12097dcc1caf3f30ab8b7be780fbb8ab47775cb85cbeaf08801ec83c59` | `d55f14d0fe184974c7397c345a4d40b87132393578115375d1f24523a1d3b4bf` |
| `projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s00_foundation.py` | `3c85d03ed8985d37d14992a73d84bc87febed03bcf31cbf5e258d86df9c6db35` | `63daeb5f8c788b763d3920e7c8dce978ff6934cd467c2f55cb2b23a994c35ad1` |
| `protocol/v1/README.md` | `9bc761eab13261ca86d055998bbbe8dafea40255543f83ef44af30d0ddad7bbf` | `fd5fc03cdd3128befb2c573490df104510011c4328dceea181ed16ffe49ed8b9` |
| `protocol/v1/study-contract.yaml` | `2974f1fa3e0ce82fd34648c66b5636bfe8512d3f54f252245d17651ebb2c2b46` | `914cda8051406dc44dda6381f094ab91852c391b78f3f2b86226192925abf549` |
| `protocol/v1/amendment-ledger.jsonl` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `92da8dde11de879c573018a1f968648cef6f328ba44cee06e83f3b379ce81619` |
| `protocol/v1/run_s00_foundation.py` | `543e1eaa00ab985f80358968dee33145f4427625b17f904e667aebe91ce92810` | `09441df0e1568ce572f017742c3cc35c258aa3f9273145586688ee48b713ee91` |
| `protocol/v1/schemas/study-contract.schema.json` | `264c9cf5a197166786c7ca1ce451d3b2c866e3fb14920f87923876e0116e75b5` | `d400c75d6321265f12db3955693359d295ca9c98434e6c1fd69943ebf033c355` |
| `protocol/v1/schemas/lock.schema.json` | `51392766846c912e1bf96f620da1315b83450554efee1edaf9b28657a9c81844` | `a4f2b345705f265c4b58c3f509b1542d0efad51a76a838964379bba068f60c7e` |

`ga.py`保持
`5633a79b8e068137000dfcc2382124d3da1bd441d7049955799cd1f8f929aa35`；
amendment/event/checkpoint/lineage schemas、四fixtures及pinned operator/core sources
均保持frozen bytes。特別是`space.py`與`mutation.py`分別維持
`7f63af21d82c0f5942f3824ecb484956c2ff27a834e8ee696afc1e28a414f69e`、
`c9a759f5d0c8be607cf4d3d4c52592d1a345ecb5edbcb38f28e3cff9bc631696`。

Plan-preserving repair iterations依序修正：

1. canonical-equal Python scalar type與swapped-kind expected error；
2. canonical JSON object key order不應成為identity；
3. schema exact-const及temp successor amendment bindings；
4. non-object observation payload明確fail closed；
5. continuous/resumed event namespaces與global identity proof；
6. lineage current-lock raw probes；
7. population raw state/hash逐欄重算。

Recorded deviations／corrections：

- Plan-B exact-byte preflight依role separation由Main執行，implementer只做opaque
  identity dry validation；沒有改acceptance或shared bytes。
- Main第一次status清單誤抄四個fixture名稱；以frozen Plan-B literal list重算後為
  exact 23，未發生worktree越權。
- Main第一次native validation把immutable legacy lock套用successor-only schema，
  得到預期rejection；修正適用instance後Draft 2020-12驗證通過，old bytes未改。
- Host沒有bare `python`命令。Verifier記錄exit 127後，以同一既有`python3`
  interpreter執行相同unit參數；未安裝或改變環境。

除此之外沒有unresolved deviation、partial output、timeout、killed/background run、
dependency install、container mutation、GPU/ROCm probe或S10 work。

## 5. Authoritative successor evidence

| Artifact | Raw SHA-256 | Canonical outcome SHA-256 |
| --- | --- | --- |
| neutrality | `c55e1cf4cd87d70839fe93f5c2eea633ed0acb40030996bf7435b67579697317` | `fe3a36be2c626ee1d59bb4d33be57fee96848384651efa11beac48d94c3505e7` |
| resume parity | `1cf232065b814efec5a32c0b06307eb6953a92ca7e0ff8694573a21ea038ec9b` | `1d9e3860e87d22e8a69f50091a7a1d1d759b081ef5dea721a14f651c66f9dca5` |
| reconciliation | `705cec7c374f7e15c5f10da195c08a9cb267d3e1034c6e3a39cc861a062bdb24` | `2911a8079e53635dc30ec92115f791ca445c3af4110c7910fc31d87be829cba4` |
| lineage fail-closed | `5209937a45521b1caa10c2a29d4cfb3e16c898028019dccfe04ce83306af0743` | `145c291e3806cf0b6eb183a0127b75a8b95c11566738cea4a6594a77a6cddae0` |
| decision | `56fa4beacadbb8990c0716c9ccc5c2f0a9bba886cb0f5db12ee2b846576d31a7` | `5945136ecb446c3cbb6c6bac761c36d0606a259c695c1a79cc9966d71af2a991` |

Neutrality的observer-off／adversarial-observer-on完整raw runs逐欄相同：4
evaluation batches、24 evaluations、4 generations，完整保存proposal、fitness、
updated/old population、survivors、offspring、champion、stats、population decay、
termination與三類RNG identity。Off events為0；on events為23；callbacks消耗Python
global RNG 391次、NumPy global RNG 391次，23份payload保持immutable。Raw-run
canonical hash兩側皆為
`f8bdd18fd7ba99b45fe57ceaa23e3b7727c6fdea4bd517a57ef513ca763592ce`，
first divergence為`no_divergence`。

Continuous／interrupted-resumed完整raw runs逐欄相同，canonical hash兩側皆為
`b25abae0489aaee6db4f6cdc32f48bb0f1ddff03ed08f66de3860eae8321ee89`。
Events為27／28，兩側sequence contiguous、IDs unique且跨trajectory disjoint；
兩側各4份checkpoint manifests及external journals皆可重算。Interrupt generation
為2，selected checkpoint為
`ga-checkpoint-1ea5e782e4c5c03789caa0d922b6ff67de205952647b3aafb1c89eddc2406614`，
saved cursor為13，first divergence為`no_divergence`。

Reconciliation從raw records重算合法success及explicit backend failure state
machines。五個recovery named probes精確拒絕：

| Probe | Error |
| --- | --- |
| generated input仍`in_progress` | `record_status_in_progress` |
| observation `timeout` | `record_status_timeout` |
| observation `killed` | `record_status_killed` |
| cross-kind conflicting `record_id` | `duplicate_record_id` |
| success status配backend-failure summary | `summary_payload_mismatch` |

另四個original negatives與13個lineage matrix cases均由production validators具名
拒絕。四類evidence各做removal與語義完整的FAIL artifact，共8個decision gates：
removal均為`decision_evidence_missing`，failure均為
`decision_evidence_failed`；全部無decision、partial output或edge。

## 6. Exact commands、環境與結果

除特別註明外，host CWD為
`/data1/perlee/rocm-libraries`，所有成功命令exit 0。

### 6.1 Unit suites

Host unit CWD：
`/data1/perlee/rocm-libraries/projects/hipblaslt/tensilelite`。

Host首次執行下列frozen literal command時，bare `python`不存在，exit 127，測試未
開始：

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s Tensile/Tests/unit -p 'test_ductile_s00_foundation.py' -v
```

既有`python3` route及shell-function重放frozen literal route均exit 0、30/30：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s Tensile/Tests/unit -p 'test_ductile_s00_foundation.py' -v
```

```bash
python() { python3 "$@"; }
export -f python
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s Tensile/Tests/unit -p 'test_ductile_s00_foundation.py' -v
```

Container route的host CWD為repo root，container CWD為
`/src/rocm-libraries/projects/hipblaslt/tensilelite`；exit 0、30/30：

```bash
docker exec perlee sh -lc 'command -v python || true; command -v python3; cd /src/rocm-libraries/projects/hipblaslt/tensilelite && PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s Tensile/Tests/unit -p "test_ductile_s00_foundation.py" -v'
```

### 6.2 Main lifecycle commands

下列五個命令的CWD都是repo root，依序exit 0：

```bash
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py preflight-successor --original-plan-b agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/plan_b.md --recovery-plan-b agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/plan_b.md
```

```bash
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py lock-successor --original-plan-b agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/plan_b.md --recovery-plan-b agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/plan_b.md
```

```bash
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py evidence-successor
```

```bash
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py decision-successor
```

```bash
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py reproduce-successor --output-dir agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/main-reproduce.leoQoA
```

依序觀察到`S00_SUCCESSOR_PREFLIGHT_OK`、
`S00_SUCCESSOR_LOCK_EFFECTIVE`、四份exclusive-write evidence、
`S00_SUCCESSOR_EVIDENCE_READY`及`S00_SUCCESSOR_REPRODUCTION_OK`。

### 6.3 Native Draft 2020-12 validation

Host CWD為repo root；既有`perlee` container repo為`/src/rocm-libraries`。完整命令：

```bash
docker exec -i perlee sh -lc 'cd /src/rocm-libraries && python3 -B -' <<'PY'
import json
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator

root = Path('/src/rocm-libraries')
p = root / 'study_docs/research/ductile-origami-warmstart/protocol/v1'
schema_names = ['study-contract', 'amendment', 'lock', 'event', 'checkpoint', 'lineage']
schemas = {}
for name in schema_names:
    path = p / 'schemas' / f'{name}.schema.json'
    schema = json.loads(path.read_text())
    Draft202012Validator.check_schema(schema)
    schemas[name] = schema
    print(f'METASCHEMA_OK {name}')

contract = yaml.safe_load((p / 'study-contract.yaml').read_text())
Draft202012Validator(schemas['study-contract']).validate(contract)
print('INSTANCE_OK study-contract.yaml')

entries = [json.loads(line) for line in (p / 'amendment-ledger.jsonl').read_text().splitlines() if line.strip()]
assert len(entries) == 1, len(entries)
Draft202012Validator(schemas['amendment']).validate(entries[0])
print('INSTANCE_OK amendment-ledger.jsonl entries=1')

lock = json.loads((p / 'locks/s00-foundation-lock-successor-001.json').read_text())
Draft202012Validator(schemas['lock']).validate(lock)
print('INSTANCE_OK successor-lock')

valid = json.loads((p / 'fixtures/valid-run.json').read_text())
Draft202012Validator(schemas['lineage']).validate(valid['lineage'])
for event in valid['events']:
    Draft202012Validator(schemas['event']).validate(event)
print(f'INSTANCE_OK valid-fixture lineage=1 events={len(valid["events"])}')

neutral = json.loads((p / 'evidence/s00-neutrality-successor-001.json').read_text())
neutral_events = neutral['observation']['observer_on']['events']
for event in neutral_events:
    Draft202012Validator(schemas['event']).validate(event)
assert neutral['observation']['observer_off']['events'] == []
print(f'INSTANCE_OK neutrality-events on={len(neutral_events)} off=0')

resume = json.loads((p / 'evidence/s00-resume-parity-successor-001.json').read_text())
for branch in ('continuous', 'resumed'):
    events = resume['observation'][branch]['events']
    for event in events:
        Draft202012Validator(schemas['event']).validate(event)
    manifests = resume['observation']['checkpoint_evidence'][branch]
    for wrapped in manifests:
        Draft202012Validator(schemas['checkpoint']).validate(wrapped['manifest'])
        Draft202012Validator(schemas['lineage']).validate(wrapped['manifest']['lineage'])
    print(f'INSTANCE_OK resume-{branch} events={len(events)} checkpoints={len(manifests)}')
print('DRAFT202012_NATIVE_VALIDATION_OK')
PY
```

Exit 0；六份metaschema、contract、one-entry ledger、successor lock、valid fixture
lineage／3 events、neutrality 23/0 events、resume 27/28 events及兩側各4
checkpoints全部valid。

### 6.4 Verifier fresh reproductions

兩個命令的CWD都是repo root，皆exit 0：

```bash
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py reproduce-successor --output-dir agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/verifier-reproduce-iteration2-a
```

```bash
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py reproduce-successor --output-dir agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/verifier-reproduce-iteration2-b
```

兩次皆為`S00_SUCCESSOR_REPRODUCTION_OK`，canonical decision皆為
`5945136ecb446c3cbb6c6bac761c36d0606a259c695c1a79cc9966d71af2a991`，
且authoritative old/current bytes unchanged。

### 6.5 Invalid-lock production-writer probes

Host CWD為repo root。完整命令：

```bash
set -euo pipefail
probe=agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/verifier-lock-writers-iteration2
test ! -e "$probe"
git check-ignore -v "$probe/probe.json"
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B - <<'PY'
import importlib.util,json
from collections import Counter
from pathlib import Path
root=Path('/data1/perlee/rocm-libraries');probe=root/'agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/verifier-lock-writers-iteration2'
test_path=root/'projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s00_foundation.py';spec=importlib.util.spec_from_file_location('s00tests_lockwriters',test_path);t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);m=t.RUNNER
probe.mkdir(parents=True);_,contract_path,_,valid,_=t._write_temp_contract_and_lock(probe);cases=m._single_substitution_cases(valid)+[('combined-substitution',m._combined_substituted_lock(valid))];codes=Counter();names=[]
for index,(name,candidate) in enumerate(cases):
 lock_path=probe/f'candidate-{index:03d}.json';m.atomic_write_json(lock_path,candidate);output=probe/f'output-{index:03d}'
 try:m._write_successor_evidence_to(output,command='verifier-iteration2-invalid-lock',lock_path=lock_path,contract_path=contract_path,verify_plan_bytes=False)
 except m.EvidenceValidationError as e:codes[e.code]+=1
 else:raise AssertionError(f'invalid lock accepted: {name}')
 assert not output.exists(),(name,'partial output');names.append(name)
required={'original-plan-b-path','original-plan-b-sha256','recovery-plan-b-path','recovery-plan-b-sha256','amendment-path','amendment-raw_sha256','amendment-head_sha256','amendment-amendment_id','parent-null','parent-wrong-id','parent-wrong-hash','parent-self','lock-id-derived','body-sha256-derived','combined-substitution'}
assert required<=set(names),required-set(names)
print('ALL_INVALID_LOCK_WRITERS_FAIL_BEFORE_OUTPUT_OK')
print('CASES',len(cases),'CODES',json.dumps(dict(sorted(codes.items())),sort_keys=True))
print('REQUIRED_CASES',json.dumps(sorted(required)))
PY
```

Exit 0；223/223 pre-output rejection：
148 `schema_validation_failed`、73 `lock_binding_mismatch`、2
`lock_hash_mismatch`。

### 6.6 Raw recomputation、reconciliation與lineage probes

Host CWD為repo root。完整命令：

```bash
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B - <<'PY'
import importlib.util, json
from collections import Counter
from pathlib import Path

root=Path('/data1/perlee/rocm-libraries')
script=root/'study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py'
spec=importlib.util.spec_from_file_location('s00runner_verify2',script); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
lock=m.strict_load_json(m.SUCCESSOR_LOCK_PATH)

failures=[]; codes=Counter()
for name,candidate in m._single_substitution_cases(lock):
    try:
        m._validate_successor_lock(candidate,verify_bound_bytes=False,verify_plan_bytes=False)
    except m.EvidenceValidationError as e:
        codes[e.code]+=1
    else:
        failures.append(name)
assert not failures, failures
single_count=sum(codes.values())
combined=m._combined_substituted_lock(lock)
try:
    m._validate_successor_lock(combined,verify_bound_bytes=False,verify_plan_bytes=False)
except m.EvidenceValidationError as e:
    combined_code=e.code
else:
    raise AssertionError('combined substitution accepted')

lock_sha=m.sha256_file(m.SUCCESSOR_LOCK_PATH)
auth={
 'neutrality':m.strict_load_json(m.SUCCESSOR_EVIDENCE_PATHS[0])['observation'],
 'resume-parity':m.strict_load_json(m.SUCCESSOR_EVIDENCE_PATHS[1])['observation'],
 'reconciliation':m.strict_load_json(m.SUCCESSOR_EVIDENCE_PATHS[2])['observation'],
 'lineage-fail-closed':m.strict_load_json(m.SUCCESSOR_EVIDENCE_PATHS[3])['observation'],
}
m._validate_neutrality_observation(auth['neutrality'])
m._validate_resume_observation(auth['resume-parity'])
m._validate_reconciliation_observation(auth['reconciliation'])
m._validate_lineage_observation(auth['lineage-fail-closed'])
fresh={
 'neutrality':m.run_neutrality(lock,effective_lock_sha256=lock_sha),
 'resume-parity':m.run_resume(lock,effective_lock_sha256=lock_sha),
 'reconciliation':m.run_reconciliation(),
 'lineage-fail-closed':m.run_lineage(lock,lock_path=m.SUCCESSOR_LOCK_PATH),
}
assert fresh==auth

for kind,path in zip(('neutrality','resume-parity','reconciliation','lineage-fail-closed'),m.SUCCESSOR_EVIDENCE_PATHS):
    m._validate_artifact(path,lock,kind,lock_path=m.SUCCESSOR_LOCK_PATH)
m._validate_decision(m.SUCCESSOR_DECISION_PATH,lock,lock_path=m.SUCCESSOR_LOCK_PATH,evidence_dir=m.EVIDENCE_DIR)

old_evidence=m.EVIDENCE_DIR/'s00-neutrality.json'
try:
    m._validate_artifact(old_evidence,lock,'neutrality',lock_path=m.SUCCESSOR_LOCK_PATH)
except m.EvidenceValidationError as e:
    old_evidence_code=e.code
else: raise AssertionError('old evidence accepted under successor lock')
try:
    m._validate_decision(m.EVIDENCE_DIR/'s00-decision.json',lock,lock_path=m.SUCCESSOR_LOCK_PATH,evidence_dir=m.EVIDENCE_DIR)
except m.EvidenceValidationError as e:
    old_decision_code=e.code
else: raise AssertionError('old decision accepted as current')

recon=auth['reconciliation']; named={x['case_id']:x for x in recon['invalid_cases'] if x['case_id'] in {
 'generated-input-in-progress','observation-timeout','observation-killed','cross-kind-conflicting-record-id','success-status-backend-failure-summary'}}
assert set(named)=={'generated-input-in-progress','observation-timeout','observation-killed','cross-kind-conflicting-record-id','success-status-backend-failure-summary'}
assert all(x['observed_error']==x['expected_error'] and x['no_ready_edge'] is True for x in named.values())
lin=auth['lineage-fail-closed']; current={x['case_id']:x for x in lin['current_lock_cases']}
assert {'missing-current-successor-lock','superseded-old-lock-is-not-current','successor-lock-substitution','illegal-null-successor-parent','mismatched-successor-parent'}<=set(current)
assert all(x['observed_error']==x['expected_error'] and x['no_ready_edge'] is True for x in current.values())
assert {x['kind'] for x in lin['evidence_class_matrix']}=={'neutrality','resume-parity','reconciliation','lineage-fail-closed'}
assert all(x['removal_error']=='decision_evidence_missing' and x['failure_error']=='decision_evidence_failed' and x['outgoing_edges']==[] for x in lin['evidence_class_matrix'])
assert all(x['observed_error']==x['expected_error'] and x['no_ready_edge'] is True for x in lin['cases'])
print('FULL_NEGATIVE_AND_RAW_RECOMPUTATION_OK')
print('LOCK_SINGLE_SUBSTITUTIONS',single_count,dict(sorted(codes.items())))
print('LOCK_COMBINED',combined_code)
print('RAW_FRESH_EQUAL',','.join(fresh))
print('NEUTRALITY_RAW',len(auth['neutrality']['observer_on']['events']),len(auth['neutrality']['observer_off']['events']),auth['neutrality']['criterion_status'],auth['neutrality']['first_divergence'])
print('RESUME_RAW',len(auth['resume-parity']['continuous']['events']),len(auth['resume-parity']['resumed']['events']),len(auth['resume-parity']['checkpoint_evidence']['continuous']),len(auth['resume-parity']['checkpoint_evidence']['resumed']),auth['resume-parity']['criterion_status'],auth['resume-parity']['first_divergence'])
print('RECON_INVALID',len(recon['invalid_cases']),'NAMED',json.dumps({k:v['observed_error'] for k,v in sorted(named.items())},sort_keys=True))
print('LINEAGE_AC07_CASES',len(lin['cases']),'CURRENT_LOCK_CASES',json.dumps({k:v['observed_error'] for k,v in sorted(current.items())},sort_keys=True))
print('EVIDENCE_CLASS_MATRIX',json.dumps(lin['evidence_class_matrix'],sort_keys=True))
print('HISTORICAL_REJECT',old_evidence_code,old_decision_code)
PY
```

Exit 0；`FULL_NEGATIVE_AND_RAW_RECOMPUTATION_OK`、222 single＋1 combined validator
rejection、fresh raw observations逐項相等、9 reconciliation cases、13 AC-07
lineage cases與historical current-selection rejection皆匹配。

### 6.7 Evidence removal／semantic-failure decision gates

Host CWD為repo root。完整命令：

```bash
set -euo pipefail
probe=agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/verifier-decision-gates-iteration2c
test ! -e "$probe"
git check-ignore -v "$probe/probe.json"
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B - <<'PY'
import copy, importlib.util, json
from pathlib import Path
root=Path('/data1/perlee/rocm-libraries')
probe=root/'agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/verifier-decision-gates-iteration2c'
test_path=root/'projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s00_foundation.py'
spec=importlib.util.spec_from_file_location('s00tests_verify2c',test_path);t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);m=t.RUNNER
probe.mkdir(parents=True)
_,contract_path,_,lock,lock_path=t._write_temp_contract_and_lock(probe)
base=probe/'base-evidence';m._write_successor_evidence_to(base,command='verifier-iteration2-decision-gate',lock_path=lock_path,contract_path=contract_path,verify_plan_bytes=False)
lock_sha=m.sha256_file(lock_path); kinds=('neutrality','resume-parity','reconciliation','lineage-fail-closed')
validators={'neutrality':m._validate_neutrality_observation,'resume-parity':m._validate_resume_observation,'reconciliation':m._validate_reconciliation_observation,'lineage-fail-closed':m._validate_lineage_observation}
baseobs={k:m.strict_load_json(base/f's00-{k}-successor-001.json')['observation'] for k in kinds}
def failed_observation(kind):
 obs=copy.deepcopy(baseobs[kind])
 if kind=='neutrality': obs['callback_counts']['python']=0
 elif kind=='resume-parity': obs['resumed']['raw_run']['python_rng_sha256']='0'*64;obs['raw_run_sha256']['resumed']=m.canonical_sha256(obs['resumed']['raw_run']);obs['first_divergence']=m._first_divergence(obs['continuous']['raw_run'],obs['resumed']['raw_run'])
 elif kind=='reconciliation': obs['invalid_cases'][0]['no_ready_edge']=False
 elif kind=='lineage-fail-closed': obs['evidence_class_matrix'][0]['outgoing_edges']=['S10']
 obs['criterion_status']='FAIL';validators[kind](obs);return obs
results=[]
for target in kinds:
 for mode in ('remove','fail'):
  candidate=probe/f'{target}-{mode}';candidate.mkdir();prior=[]
  for kind in kinds:
   obs=failed_observation(kind) if kind==target and mode=='fail' else copy.deepcopy(baseobs[kind])
   artifact=m._artifact(kind,lock,lock_sha,prior,obs,'verifier-iteration2-semantic-gate')
   path=candidate/f's00-{kind}-successor-001.json';m.atomic_write_json(path,artifact)
   prior=[{'artifact_id':artifact['artifact_id'],'path':str(path.relative_to(root)),'sha256':m.sha256_file(path)}]
  if mode=='remove': (candidate/f's00-{target}-successor-001.json').unlink()
  output=probe/f'decision-{target}-{mode}'
  try: m._write_successor_decision_to(output,candidate,command='verifier-iteration2-negative',lock_path=lock_path,contract_path=contract_path,verify_plan_bytes=False,independent_reproduction=False)
  except m.EvidenceValidationError as e: code=e.code
  else: raise AssertionError(f'accepted {target} {mode}')
  expected='decision_evidence_missing' if mode=='remove' else 'decision_evidence_failed';assert code==expected,(target,mode,code);assert not output.exists(),(target,mode,'partial output')
  results.append({'kind':target,'mode':mode,'error':code,'output_absent':True})
print('EIGHT_SEMANTIC_DECISION_GATES_OK')
print(json.dumps(results,sort_keys=True))
PY
```

Exit 0；四類removal均為`decision_evidence_missing`，四類semantic failure均為
`decision_evidence_failed`，8/8 decision/output absent。

### 6.8 Scope/status commands

Repo-root commands：

```bash
git diff --check
```

```bash
git status --porcelain=v1 -uall
```

加上從frozen Recovery Plan-B literal list解析的exact comparison，exit 0；
technical verification結束時implementation 29/29、missing/extra皆空、staged 0。

Reproduction的raw artifact hashes因invocation output path屬volatile provenance而不同，
但兩次fresh與authoritative的完整observations及五個canonical outcomes逐項相同；
reproduction前後predecessor及authoritative successor bytes都未改。

Native Draft route只使用既有`perlee` container與already-provisioned
`jsonschema` 4.25.1；沒有install或持久container mutation。全部有效命令自然完成，
無timeout、killed、still-running或background work。

## 7. Acceptance disposition

| Criterion | Status | Direct basis |
| --- | --- | --- |
| AC-01 | PASS | 六schemas原生validation、amended contract、ledger、successor lock、fixtures及無retired runtime dependency。 |
| AC-02 | PASS | 兩代lock、兩份Plan-B、29/33 lists與全部bindings重算；222 single＋1 combined substitutions全拒。 |
| AC-03 | PASS | Amendment先於mutation、old six immutable、exclusive writes、wrong/stale/current-selection cases無partial output。 |
| AC-04 | PASS | Adversarial observer off/on完整raw trajectories、events、RNG identities逐欄no divergence。 |
| AC-05 | PASS | Continuous/resumed完整raw trajectories、27/28 events、8 manifests、boundary mapping逐欄no divergence。 |
| AC-06 | PASS | Exact state machines與joins重算；原4加named5共9 negatives精確拒絕。 |
| AC-07 | PASS | 13 lineage cases、223 lock-writer probes、strict event/checkpoint cases及8 evidence gates全部fail closed。 |
| AC-08 | PASS | 四份successor chain與decision join重算；old decision排除；removal/failure均no-edge。 |
| AC-09 | PASS | Main一次＋verifier兩次fresh reproduction canonical match，volatile provenance邊界正確。 |
| AC-10 | PASS | Ordinary GA default route、operator/core hashes、exact scope與CPU-only/no-S10邊界通過。 |
| AC-11 | Closeout transaction | 本報告與三份projection需經原verifier staged-byte ACK、exact commit及post-audit。 |

`completion_correctness`與`scientific_outcome`分離：前者確認protocol、驗證與closeout
交易是否正確；後者確認S00-H1在可信evidence下是否被支持。這次兩者分別為technical
`PASS`與scientific `positive`，但technical PASS本身不跳過AC-11。

## 8. Iteration、finding closure與保留限制

- Original implementation建立genesis protocol與第一代evidence；原verifier iteration
  1為`CHANGES_REQUIRED`，AC-02–AC-09未通過，scientific outcome為
  `NOT_ESTABLISHED`，不是negative。
- Dual-review recovery consensus選擇append-only successor，不覆寫失敗世代，也不
  建snapshot/intermediate commit。
- Recovery implementer關閉三個findings；Main完成exact preflight、successor
  generation與raw audit；原verifier iteration 2作FULL重驗，沒有只驗patch points。
- Iteration 2 verifier artifact identities：
  - report raw SHA-256：
    `a8b4ebeb0a7e00b1b4d74a952af94195da61e9be210ae62b25fe5b7072fcf4dd`
  - verdict raw SHA-256：
    `d8feb2ae68e483d76a88962d9286f0b2a3387c55d35b27da12ce12f3ae2af60b`

Base recovery完整保留六份failed-generation raw artifacts，並在predecessor
lock／amendment中保留原17個shared paths的old hashes；它**沒有**保存那17份shared
old raw contents的snapshot，因此不能宣稱可只靠final tree重建完整old 23-path
workspace。這是已審查且明示的provenance限制，不影響六份immutable old artifacts或
current successor evidence的可驗證性。

## 9. Immutable execution view與closeout projection view

### 9.1 兩個合法視圖

Technical PASS之後，Recovery Plan-B §11要求exact三份authority projection改成
verified lifecycle狀態；successor lock則正確地拒絕這三份authority bytes改動。
Closeout iteration 1修正報告的exact commands後，iteration 2因此發現：

- **Execution-authority view（E）**：baseline commit
  `60775f12843bee9f95cb0bef4e91de8bc4dc9dc3`加exact 29 implementation
  blobs，以及兩份exact ignored Plan-B blobs；parent plan、active README與S00
  design保持baseline bytes。`protocol/v1/README.md`是這個immutable E view的
  runbook。E是AC-01–AC-10與fresh reproduction的執行邊界。
- **Closeout-projection view（C）**：final exact 33-path closure tree；同一29個
  implementation blobs加本formal report及exact三份post-PASS projections。C是
  AC-11完成後供使用者閱讀的active lifecycle view，不是historical outcome
  writer的執行view。

兩位fresh closeout-binding reviewers
`/root/s00_closeout_binding_a`與`/root/s00_closeout_binding_b`反覆交互詰問後皆
`AGREE`：保留successor-001、兩個immutable generations、one-entry amendment、
29/33 authority與validator semantics；不新增successor-002、不再append
amendment、不改test／lock／contract，也不把C標成green execution view。

三份authority的raw E→C mapping如下。E hashes由baseline Git object直接重算；
C hashes在三份projection達到final bytes後計算，且projection只單向連到本report，
不嵌入report hash：

| Authority projection | E raw SHA-256 | C raw SHA-256 |
| --- | --- | --- |
| `study_docs/research/ductile-origami-warmstart-experiment-plan.md` | `48e64a29c559e130c02fe60e61adc630d676df41cf5ec92a2d6156eb68ea5e73` | `ac080763ef82fe49c2944170803b5ed3531c0249c86faef2744df3f15588efe3` |
| `study_docs/research/ductile-origami-warmstart/README.md` | `b63f37b5a9ada937b8c67f337b604c74b6682ec513cb77984634dbb01bbc82e5` | `cc6cca1a681a509b6c4b17f13bc0d007132aa98b985d112b654e98d5132e83da` |
| `study_docs/research/ductile-origami-warmstart/s00-evidence-contract-lineage-observability-design.md` | `c3698947fbb58bb34b4f346848f8aa5a33c8ef3a18a46c3f864ed28b08914fc1` | `920c9b65445bdd29ea751c02e99d03fb720d17475bf3026cdb57aea29eca4150` |

### 9.2 Exact E reconstruction recipe

下列repo-root Bash route只讀baseline／index或closure commit，建立isolated temp
tree；不修改main tracked tree或index。Pre-commit closeout audit令
`s00_source_mode=index`；post-commit audit令
`s00_source_mode=commit`，並由formal-report introduction identity解析唯一closure
commit。初版配方把完整baseline archive放在`/tmp`；原verifier獨立重跑時該8.9 GiB
tree使`/tmp`耗盡，`tar` exit 2，未開始test、未改main tree/index，也未給
`CLOSEOUT_ACK`。經兩位closeout-binding reviewers再次`AGREE`，durable route固定
使用有容量gate的`/data1/perlee/s00-closeout-tmp`，禁止fallback至`/tmp`。Array是
Recovery Plan-B exact ordered 29-path list，不可改成glob：

```bash
set -euo pipefail
s00_repo=/data1/perlee/rocm-libraries
s00_baseline=60775f12843bee9f95cb0bef4e91de8bc4dc9dc3
s00_source_mode=index
s00_temp_parent=/data1/perlee/s00-closeout-tmp
mkdir -p "$s00_temp_parent"
s00_data1_available_kib=$(df -Pk /data1 | awk 'NR == 2 {print $4}')
test "$s00_data1_available_kib" -ge 20971520
s00_tmp=$(mktemp -d \
  "$s00_temp_parent/execution-view.XXXXXX")
case "$s00_tmp" in
  "$s00_temp_parent"/execution-view.*) ;;
  *) exit 2 ;;
esac
s00_e_root="$s00_tmp/e"
mkdir -p "$s00_e_root"
s00_index_before=$(git write-tree)
s00_status_before=$(git status --porcelain=v1 -uall | sha256sum | awk '{print $1}')
git archive "$s00_baseline" | tar -x -C "$s00_e_root"

s00_e_paths=(
'projects/hipblaslt/tensilelite/Tensile/ductile/algorithm/ga.py'
'projects/hipblaslt/tensilelite/Tensile/ductile/evidence.py'
'projects/hipblaslt/tensilelite/Tensile/Tests/unit/test_ductile_s00_foundation.py'
'study_docs/research/ductile-origami-warmstart/protocol/v1/README.md'
'study_docs/research/ductile-origami-warmstart/protocol/v1/study-contract.yaml'
'study_docs/research/ductile-origami-warmstart/protocol/v1/amendment-ledger.jsonl'
'study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py'
'study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/study-contract.schema.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/amendment.schema.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/lock.schema.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/event.schema.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/checkpoint.schema.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/schemas/lineage.schema.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/valid-run.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/invalid-lineage.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/duplicate-events.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/fixtures/backend-failure.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s00-foundation-lock.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-neutrality.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-resume-parity.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-reconciliation.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-lineage-fail-closed.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-decision.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s00-foundation-lock-successor-001.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-neutrality-successor-001.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-resume-parity-successor-001.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-reconciliation-successor-001.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-lineage-fail-closed-successor-001.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-decision-successor-001.json'
)
test "${#s00_e_paths[@]}" -eq 29

case "$s00_source_mode" in
  index)
    git checkout-index -f --prefix="$s00_e_root/" -- "${s00_e_paths[@]}"
    ;;
  commit)
    s00_report=study_docs/research/ductile-origami-warmstart/reports/staged/s00-foundation-verification-report.md
    s00_closure=$(git log --diff-filter=A --format=%H -n1 -- "$s00_report")
    test -n "$s00_closure"
    s00_temp_index="$s00_tmp/closure.index"
    GIT_INDEX_FILE="$s00_temp_index" git read-tree "$s00_closure"
    GIT_INDEX_FILE="$s00_temp_index" git checkout-index -f \
      --prefix="$s00_e_root/" -- "${s00_e_paths[@]}"
    ;;
  *)
    exit 2
    ;;
esac

s00_original=agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/plan_b.md
s00_recovery=agent_run/260725-ductile-factorized-guidance-s0-s2/milestones/S00/recovery/plan_b.md
mkdir -p \
  "$s00_e_root/$(dirname "$s00_original")" \
  "$s00_e_root/$(dirname "$s00_recovery")"
cp -- "$s00_repo/$s00_original" "$s00_e_root/$s00_original"
cp -- "$s00_repo/$s00_recovery" "$s00_e_root/$s00_recovery"
test "$(sha256sum "$s00_e_root/$s00_original" | awk '{print $1}')" = \
  b8e7a458bb6cb6fa103e92c50eed5c11b2e964c354dd71d629c61cdeecc571d9
test "$(sha256sum "$s00_e_root/$s00_recovery" | awk '{print $1}')" = \
  3f64ec77def3960b67756b0af576bdb5d4f28683ed11a1df55956fe87c0e34c2
```

Successor lock也把creation CWD
`/data1/perlee/rocm-libraries`納入frozen body。普通temp path雖然content相同，仍會
正確得到`lock_binding_mismatch: successor lock frozen binding substitution`；
不得忽略、monkeypatch或重算此binding。下列already-provisioned Linux
`unshare -Urnm` route只在child user/mount namespace內把E呈現於frozen absolute
path；child退出後mount消失，不改global mount、container、main tree或validator：

```bash
s00_durable=(
'study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s00-foundation-lock.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-neutrality.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-resume-parity.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-reconciliation.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-lineage-fail-closed.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-decision.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/locks/s00-foundation-lock-successor-001.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-neutrality-successor-001.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-resume-parity-successor-001.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-reconciliation-successor-001.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-lineage-fail-closed-successor-001.json'
'study_docs/research/ductile-origami-warmstart/protocol/v1/evidence/s00-decision-successor-001.json'
)
sha256sum "${s00_durable[@]}" >"$s00_tmp/durable-before.sha256"

s00_e_run() {
  unshare -Urnm sh -lc '
    set -eu
    mount --make-rprivate /
    mount --bind "$1" /data1/perlee/rocm-libraries
    cd "$2"
    shift 2
    exec "$@"
  ' sh "$s00_e_root" "$@"
}

s00_e_run \
  /data1/perlee/rocm-libraries/projects/hipblaslt/tensilelite \
  env PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s Tensile/Tests/unit \
  -p 'test_ductile_s00_foundation.py' -v

for s00_label in a b; do
  s00_out="$s00_tmp/reproduce-$s00_label"
  test ! -e "$s00_out"
  s00_e_run /data1/perlee/rocm-libraries \
    env PYTHONPATH=projects/hipblaslt/tensilelite \
    python3 -B \
    study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py \
    reproduce-successor --output-dir "$s00_out"
done

test "$(git write-tree)" = "$s00_index_before"
test "$(git status --porcelain=v1 -uall | sha256sum | awk '{print $1}')" = \
  "$s00_status_before"
sha256sum "${s00_durable[@]}" >"$s00_tmp/durable-after.sha256"
cmp "$s00_tmp/durable-before.sha256" "$s00_tmp/durable-after.sha256"
test "$(sha256sum \
  study_docs/research/ductile-origami-warmstart-experiment-plan.md |
  awk '{print $1}')" = \
  ac080763ef82fe49c2944170803b5ed3531c0249c86faef2744df3f15588efe3

# 只在全部結果／hash已保存且namespace child結束後清除本次exact temp root。
case "$s00_tmp" in
  /data1/perlee/s00-closeout-tmp/execution-view.*)
    find "$s00_tmp" -depth -delete
    ;;
  *)
    exit 2
    ;;
esac
test ! -e "$s00_tmp"
test -d "$s00_temp_parent"
```

Pre-closeout Main實際執行結果：

- namespace E unit：exit 0，`Ran 30 tests`、`OK`；
- fresh E reproduction A/B：各exit 0、各
  `S00_SUCCESSOR_REPRODUCTION_OK`；
- A/B canonical decision皆為
  `5945136ecb446c3cbb6c6bac761c36d0606a259c695c1a79cc9966d71af2a991`；
- 兩次皆明示`authoritative_old_and_successor: unchanged`；
- child退出後host仍顯示C bytes，沒有global mount、main tracked/index drift或
  container mutation；
- exact temp root只在evidence capture後清除；固定parent保留，且`/data1` free-space
  再檢查成功。

若baseline Git object、任一exact Plan-B byte或unprivileged user/mount namespace
能力不可取得，或`/data1`低於20 GiB conservative floor，E reproduction不可用，
closeout必須fail closed；不得改`ROOT`、`creation.cwd`、lock、validator、改用
symlink／path substitution或fallback至`/tmp`。這個重建保證目前workspace／
Git-history環境的可重現性，不宣稱standalone source-tarball portability。

### 9.3 Exact C rejection probes

從C的TensileLite CWD執行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s Tensile/Tests/unit \
  -p 'test_ductile_s00_foundation.py' \
  -v
```

實際exit 1，`Ran 30 tests`、`FAILED (errors=2)`；exact兩個errors為：

1. `TestEffectiveLockLifecycle.test_amendment_successor_preserves_and_invalidates_prior_bytes`
2. `TestSuccessorRecovery.test_decision_requires_each_successor_evidence_class`

兩者都在任何outcome write前得到：

```text
bound_hash_mismatch: authorities bytes changed: study_docs/research/ductile-origami-warmstart-experiment-plan.md
```

其他28 tests通過。從C repo root以fresh absent target執行：

```bash
s00_c_probe=$(mktemp -d /tmp/s00-c-view.XXXXXX)
s00_c_output="$s00_c_probe/output"
test ! -e "$s00_c_output"
set +e
PYTHONPATH=projects/hipblaslt/tensilelite python3 -B \
  study_docs/research/ductile-origami-warmstart/protocol/v1/run_s00_foundation.py \
  reproduce-successor --output-dir "$s00_c_output" \
  >"$s00_c_probe/stdout" 2>"$s00_c_probe/stderr"
s00_c_rc=$?
set -e
test "$s00_c_rc" -eq 2
test ! -e "$s00_c_output"
cat "$s00_c_probe/stderr"
```

實際exit 2、target保持absent，exact stderr為：

```text
S00_ERROR[bound_hash_mismatch]: bound_hash_mismatch: authorities bytes changed: study_docs/research/ductile-origami-warmstart-experiment-plan.md
```

因此C不能默默用E authority名義產生新evidence；這是預註冊的fail-closed safety
evidence，不是把C的兩個errors重新標成green test。

## 10. Gate與closeout projection

Machine decision在同一effective successor lineage下記錄
`S00_EVIDENCE_READY`、scientific `positive`及candidate `["S10"]`。在本closeout
transaction完成前，orchestrator edge仍是`NOT_ELIGIBLE_PENDING_CLOSEOUT`。

本delivery只同步：

- S00：`completed / CHECKPOINT_COMPLETE / positive / effective successor-001`
- S10：dependency解除，回到`not_started / DESIGN_APPROVED / not_evaluated /
  lock absent`

它不建立S10 lock、不執行S10 discovery、不預寫S10 outcome，也不改研究goal、
criteria、thresholds、strict DAG、failure taxonomy或claim authority。Push未授權。
