"""Close only the completed, explicitly authorized conditional response package."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,shutil,sys
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from pinn_pcm_sci.ledger import RunManifest,ExperimentLedger
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
e=read(HERE/'execution.json');cfg=read(HERE/'config.json');s=read(HERE/'results/summary.json');d=read(HERE/'decision.json')
assert e['status']=='COMPLETE' and e['counts']==cfg['limits']
assert s['source_history_pass']==10 and s['history_records']==20 and s['max_quadrature_K']<=1e-6
assert all(x['all_bitwise_equal'] for x in read(HERE/'results/source-history-checks.json'))
assert read(HERE/'manuscript/build/visual-review.json')['status']=='PASS'
for name in ['README.md','results-report.md','figures-index.md','reproduction.md','author-contact-status.md','access-change.md']:
    assert (HERE/name).is_file()
for path,digest in e['source_identity'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    target=HERE/'code'/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
for path in ['scripts/circuit_screen_metrics.py','scripts/plot_conditional_thermal_closure.py','tests/test_conditional_thermal_tools.py','tests/test_conditional_history_tools.py']:
    target=HERE/'code'/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
write(HERE/'engineering-verification.json',dict(task_id=e['task_id'],status='PASS',
    tests=[dict(command='.venv/Scripts/python.exe -m unittest tests.test_conditional_thermal_tools -v',tests=5,status='PASS',
                scope='constant power; common/differential modes; transformed/direct heat equivalence including negative forcing; continuity; units/initial state'),
           dict(command='.venv/Scripts/python.exe -m unittest tests.test_conditional_history_tools -q',tests=4,status='PASS',
                scope='same-time law; legal initial state; joint trigger and repeated reversal; source field checks; no-feedback diagnostics')],
    test_execution='Delegated agents ran these before scientific execution; their tool outputs were reviewed; no scientific data in synthetic checks',
    execution_gate='DOCUMENT_CONSISTENCY_VALID before compute',numerical_max_4_minus_8_K=s['max_quadrature_K'],
    source_history_checks=10,source_history_bitwise_identical=True,pointwise_decomposition_max_K=s['max_decomposition_closure_K'],
    no_rerun_of_old_interpolation_or_energy=True,actual_source_snapshot='code/'))
cleanup=read(HERE/'manuscript/build/cleanup.json')
arrayfiles=list((HERE/'arrays').rglob('*.npz'))
write(HERE/'data-handling-record.json',dict(task_id=e['task_id'],
    policy='docs/governance/PINN_PCM_Data_Handling_Norms_2026-09-28.md',
    local='paper/paper_revision_20260928_conditional_thermal',remote='PENDING_NEXT_AUTHORIZED_SESSION_SYNC',
    GPU_used=False,GPU_shutdown='NOT_APPLICABLE_NO_INSTANCE_USED_OR_STARTED',
    historical_inputs='REUSED_READ_ONLY_NO_DUPLICATE_ARRAY_COPY',
    arrays=dict(files=len(arrayfiles),bytes=sum(p.stat().st_size for p in arrayfiles),dtype='FP64',all_native_times_saved=True,
                content='40 main temperatures, 40 verification differences, pointwise decomposition, 20 full history replays'),
    code='Exact runtime source snapshot retained; root scoring mode does not propagate',
    temporary_cleanup=dict(status=cleanup['status'],files=len(cleanup['removed']),bytes=cleanup['total_bytes'],details='manuscript/build/cleanup.json'),
    prior_manuscript_assets='Hard-linked build inputs, not an independent backup',
    no_originals_or_scientific_caches_deleted=True,no_precision_reduction=True,
    new_results_external_access='NOT_PUBLISHED',old_circuit_subset_access='PUBLIC_AT_709b10f',old_2D_full_field_access='P03_OPEN'))
prefix=HERE.relative_to(ROOT).as_posix()+'/'
closeout=ROOT/'docs/experiment/2026-09-29-conditional-thermal-closure-closeout.md'
closeout.write_text('''# 条件热响应与迟滞本构闭合收口

任务 `PCM-20260928-CONDITIONAL-THERMAL-CLOSURE-01` 已完成：40条系统主响应、40条固定求积复核、10条源历史核对和20条无反馈预测历史。VERIFIED：最大求积温差1.136868e-13 K；源R/g/H全部逐位一致；保存三层温差完整闭合。实际本地计算84.279秒，无新闭环源轨迹、神经训练、GPU、实验CSV或封存协议读取。

12.5 V细来源P/CS温度RMS为0.654351/0.761025 K，最大差6.472258/9.257625 K；V_ref RMS为0.018898 K。CS历史反转25次，源与P为13次；I_R−I_KCL RMS为223.271/243.731 μA。全工况、两来源步长与原不利证据保留，不把源步长差当连续误差界。

SUPPORTED_INTERPRETATION：唯一下一动作是聚焦热输入时序／合法状态估计，并面对同信息传统强基线；未授权后续方案执行。UNKNOWN：用途充分性、PINN增量、二维/实验/材料验证及连续真解精度。P02/P03等不自动关闭。

17页新对外稿仅更新访问两段；旧科学结论不变。旧电路子集已公開与旧二维全场未公开分开说明。本轮热数组本地交付、未发布、待下一获准实例会话同步；没有开启GPU来同步。复用既有测量请求，收件人待确认，未发送。没有Git发布、数据上传或投稿。

见[交付入口](../../paper/paper_revision_20260928_conditional_thermal/README.md)、[完整结果](../../paper/paper_revision_20260928_conditional_thermal/results-report.md)和[运行清单](manifests/20260929-conditional-thermal-closure.json)。
''',encoding='utf-8')
status='''<!-- THERMAL28_CURRENT_BEGIN -->
# 当前：条件热响应与迟滞本构闭合已完成

PCM-20260928-CONDITIONAL-THERMAL-CLOSURE-01完成批准范围：40条主热响应、40条求积复核、10条源历史核对及20条无反馈重放。最大求积差1.14e-13 K，来源R/g/H逐位复现；全工况两步长完整交付。见[研究结果](paper/paper_revision_20260928_conditional_thermal/README.md)。

VERIFIED：动态有限电压重构的偏差已进入温度、历史和本构闭合。SUPPORTED_INTERPRETATION：唯一下一建议聚焦热输入时序与合法状态估计，面对同信息传统强基线；没有自动后续计算。UNKNOWN：用途合格、连续真解误差界、PINN/二维/材料增量。旧科学主张及P02/P03保持原身份。

新17页主稿仅更新访问段，旧公开电路子集与未公开二维全场分开说明；本轮新热产物未发布、待下一获准实例会话同步。测量请求复用未发送；无GPU、训练、实验CSV/封存协议读取、Git发布或投稿。

- `phase_id`: `PHK_V23_CONDITIONAL_THERMAL_CLOSURE`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VERIFIED_CONDITIONAL_THERMAL_HISTORY_ERRORS_TASK_SUFFICIENCY_UNKNOWN`
- `next_research_execution_authorized`: `false`

<!-- THERMAL28_CURRENT_END -->'''
for name in ['README.md','active_phase.md','PROJECT_STATE.md','docs/plans/NEXT_ACTIONS.md']:
    p=ROOT/name;t=p.read_text(encoding='utf-8')
    block=status.replace('(paper/','(../../paper/') if name.startswith('docs/') else status
    t,n=re.subn(r'<!-- THERMAL28_CURRENT_BEGIN -->.*?<!-- THERMAL28_CURRENT_END -->',block,t,count=1,flags=re.S)
    assert n==1
    if name=='docs/plans/NEXT_ACTIONS.md':t=block+'\n\n[收口记录](../experiment/2026-09-29-conditional-thermal-closure-closeout.md)。研究建议不等于下一轮授权；不启动4000/800训练、插值扫描或新二维PDE。\n'
    p.write_text(t,encoding='utf-8')
idx=ROOT/'docs/experiment/README.md';t=idx.read_text(encoding='utf-8')
t=t.replace('最新：[固定CS','历史：[固定CS',1)
t=t.replace('# Experiment ledger protocol','# Experiment ledger protocol\n\n最新：[条件热响应与迟滞本构闭合](2026-09-29-conditional-thermal-closure-closeout.md)。完整有界包已完成；唯一建议为热输入时序/合法状态估计，无下一轮执行授权。',1)
idx.write_text(t,encoding='utf-8')
manifest=RunManifest(run_id='20260929-conditional-thermal-closure',experiment_group_id=e['task_id'],tier='development',
    scientific_role='FIXED_VOLTAGE_CONDITIONAL_THERMAL_AND_NO_FEEDBACK_HISTORY_DIAGNOSTIC',
    gate='GAUSS4_VS8_AND_EXACT_SOURCE_HISTORY',started_at=e['start_utc'],ended_at=e['end_utc'],
    command=['python','scripts/run_conditional_thermal_closure.py','compute'],execution_status='COMPLETE',
    numerical_validity='40_RESPONSES_QUALIFIED_10_SOURCE_HISTORIES_BITWISE_EQUAL',
    gate_outcome='RESOLVED_TEMPERATURE_AND_CONSTITUTIVE_ERRORS_WITH_SOURCE_LIMITS',
    route_disposition='CLOSED_HEAT_INPUT_TIMING_LEGAL_STATE_ESTIMATION_ONLY_PROPOSED',
    evidence_identity='FIVE_CASES_TWO_SAVED_STEPS_FOUR_FIXED_FORCINGS_NO_NEW_CLOSED_LOOP_SOURCE',
    claim_status='VERIFIED_CONDITIONAL_THERMAL_HISTORY_ERRORS_TASK_SUFFICIENCY_UNKNOWN',
    code_identity=dict(baseline=cfg['baseline'],actual_source=e['source_identity'],snapshot=prefix+'code'),
    environment=e['environment'],physical_contract_id='PINNED_AUTHOR_SI_TWO_NODE_WITH_FIXED_324P9K_HISTORY',
    split_id='TEN_SAVED_DEVELOPMENT_SYSTEMS_EXPERIMENT_AND_HOLDOUT_UNREAD',
    method_id='EXPONENTIAL_GAUSS4_TRANSFORMED_THERMAL_PLUS_PINNED_NO_FEEDBACK_HISTORY',case_id='THREE_SINGLE_TWO_PAIR_TWO_SOURCE_STEPS',seed=0,
    planned_budget=cfg['limits'],actual_budget=dict(**e['counts'],seconds=e['seconds'],training_updates=0,GPU_jobs=0,
        source_trajectory_steps=0,experimental_numeric_reads=0,score_passes=1,seed_semantics='unused deterministic analysis'),
    checkpoint=dict(kind='full_native_FP64_conditional_arrays',path=prefix+'arrays'),
    evaluator_id='NATIVE_TRAPEZOID_ABSOLUTE_K_AND_THREE_LAYER_DIFFERENCE_WITH_NO_FEEDBACK_CLOSURE',
    artifacts=dict(delivery=prefix+'README.md',report=prefix+'results-report.md',config=prefix+'config.json',
        execution=prefix+'execution.json',decision=prefix+'decision.json',figures=prefix+'figures-index.md',
        data_handling=prefix+'data-handling-record.json',reproduction=prefix+'reproduction.md'),
    failure_class=None,replay_of=None,supersedes=None)
ExperimentLedger(ROOT/'docs/experiment').record(manifest)
print('Closed bounded task, preserved arrays and source, appended immutable manifest. Run document gate.')
