"""Close out the approved saved-array task; no numerical rerun or publication."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,re,sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from pinn_pcm_sci.ledger import RunManifest,ExperimentLedger
OUT=HERE/'circuit-screen';TASK='PCM-20260927-MANUSCRIPT-CIRCUIT-SCREEN-01'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rel(p):return p.relative_to(ROOT).as_posix()
config=read(ROOT/'configs/voltage_circuit_screen_20260927.json')
results=read(OUT/'results.json');lock=read(OUT/'predictions-locked.json');execution=read(OUT/'execution-score.json')
qa=read(HERE/'build/visual-review.json');recovery=read(HERE/'build/cloud/recovery.json');shutdown=read(HERE/'build/cloud/shutdown.json')
assert len(results['records'])==10 and qa['status']=='PASS_REVIEW_LAYOUT'
assert recovery['array_readback']=='PASS' and shutdown['returncode']==0 and not any(x['ssh_port_reachable'] for x in shutdown['probes'])
assert all(d['KCL']['pass'] and d['decomposition']['pass'] and d['Euler_charge']['pass'] for r in results['records'] for d in r['devices'])
for n in ['manuscript','supplement']:
    assert all((HERE/(n+'.'+ext)).is_file() for ext in ['md','docx','pdf'])

# Fix only copied guide locations whose source assets deliberately stayed in the
# historical package, avoiding another copy of third-party data or old scripts.
matrix=HERE/'claim_evidence_matrix.md';t=matrix.read_text(encoding='utf-8')
t=t.replace('`next-research-plan.md`','`../paper_revision_20260926_core/next-research-plan.md`')
t=t.replace('`literature/source-manifest.json`','`../paper_revision_20260926_core/literature/source-manifest.json`')
t=t.replace('`literature/data-assets.json`','`../paper_revision_20260926_core/literature/data-assets.json`')
t+='\n\nCurrent display values were verified against the original CSV without rescoring (display-verification.json). The separate circuit-screen-report.md maps to circuit-screen/results.json, the immutable predictions and the actual input/source identities. It supplies no new PINN, experimental-material or sufficiency claim.\n'
matrix.write_text(t,encoding='utf-8')

record=dict(task_id=TASK,policy=rel(ROOT/'docs/governance/PINN_PCM_Data_Handling_Norms_2026-09-28.md'),
 blocks=[
 dict(name='ten_original_VO2_NPZ',purpose='original numerical evidence, full precision and native times',local='outputs/runs/20260926-core-revision-vo2-bridge/vo2',
 remote='/root/autodl-tmp/pinn-circuit-screen-20260927/outputs/runs/20260926-core-revision-vo2-bridge/vo2',status='TRANSFER_VERIFIED',identity='input-inventory.json and build/cloud/deployment.json'),
 dict(name='locked_PCHIP_predictions_and_core_scores',purpose='new analysis evidence, no regenerated trajectory',local=rel(OUT),remote=recovery['remote_persistent_result'],
 status='RECOVERED_AND_READBACK_VERIFIED',identity='build/cloud/recovery.json',local_only_additions='derived CSV summaries, figures and report after shutdown; scores and prediction arrays unchanged'),
 dict(name='manuscript_and_final_small_records',purpose='final deliverable',local=rel(HERE),remote=None,status='PENDING_NEXT_AUTHORIZED_SESSION_SYNC',restart_instance_for_sync=False),
 dict(name='inherited_tables_figures_evidence',purpose='unchanged history reused by hardlink',local=rel(HERE),status='REUSED_LOCAL_LINKS_NOT_INDEPENDENT_BACKUP',identity='preparation.json'),
 dict(name='historical_complete_standalone_package',purpose='independent rescoring inputs',local=r'D:\Temp\PINN-PCM-Standalone-20260926',
 status='EXISTING_MANIFEST_AND_VERIFICATION_READ_ONLY; LONG_TERM_ARCHIVE_LOCATION_PENDING',inputs=445,input_bytes_from_existing_manifest=24616803766,moved_or_deleted=False),
 dict(name='third_party_experimental_archive_and_sealed_protocol',purpose='original provenance and sealed data',local='paper/paper_revision_20260926_core/literature/data.zip',
 status='RETAINED; NO_NUMERIC_CSV_READ_OR_DEPLOYMENT',remote='NOT_DEPLOYED_INFORMATION_ISOLATION')],
 remote_temporary_cleanup=shutdown['remote_transfer_wrappers_removed'],local_cleanup=dict(status='PENDING_EXACT_WHITELIST',plan='build/cleanup-plan.json'),
 no_precision_or_sampling_reduction=True,no_historical_evidence_deleted=True,external_access='NOT_ESTABLISHED_P03_OPEN')
write(HERE/'data-handling-record.json',record)

# Exact, current-task temporary whitelist; never delete scientific NPZ/PT/DOCX.
targets=[]
for n in ['manuscript','supplement']:
    folder=HERE/'build'/('render-'+n)
    targets.extend(folder.glob('page-*.png'))
    duplicate=folder/(n+'.pdf')
    assert duplicate.read_bytes()==(HERE/(n+'.pdf')).read_bytes()
    targets.append(duplicate)
targets.extend((HERE/'build').glob('qa-*.png'))
targets.extend((HERE/'build/source-check').glob('*.png'))
targets.extend([HERE/'build/cloud/stage-inputs.tar',HERE/'build/cloud/recovered-output.tar'])
write(HERE/'build/cleanup-plan.json',dict(task_id=TASK,allowed_root=str((HERE/'build').resolve()),
 preconditions=['all document/figure visual checks completed','Word and render processes exited','recovered numeric fields/shapes verified',
 'final PDFs retained in package root','remote persistent inputs and scores retained','no scientific cache or original asset in whitelist'],
 files=[dict(path=str(p.resolve()),bytes=p.stat().st_size) for p in targets if p.is_file()]))

closeout=ROOT/'docs/experiment/2026-09-28-manuscript-circuit-screen-closeout.md'
closeout.write_text('''# 固定电路筛查与现稿局部修订收口

**VERIFIED：** `PCM-20260927-MANUSCRIPT-CIRCUIT-SCREEN-01`完成批准范围。主稿17页、完整补充58页，F_cov摘要及主表显示值已核验；历史补充源文未改动。

十条保存模拟记录完成十四套固定PCHIP重构，197点/套，预测锁定一次。保存时序、KCL、κ、电荷和分解工程检查通过；零新轨迹、推理或训练。58对原/重构峰匹配，但动态记录器件电流RMS约63–211 μA，不能由相同峰数宣称波形准确。**UNKNOWN：** 用途充分性、实验增量和材料验证。

五条低阈值开发记录因节点/50 Ω拓扑/同期驱动及器件C未闭合未评分，封存(4.1,3.9)V数值未读取。唯一下一研究建议是取得可审计的逐记录测量与用途合同，尚未授权新pilot。

产物回收读取核验后，关机命令返回0，三次SSH不可达；无平台计费状态API确认。最终本地图件/文稿待下一获准实例会话同步，不为小文件启动实例。数据规范已登记，旧证据保留。

见[全部交付](../../paper/paper_revision_20260927_circuit_screen/README.md)、[结果报告](../../paper/paper_revision_20260927_circuit_screen/circuit-screen-report.md)及[运行清单](manifests/20260928-manuscript-circuit-screen.json)。P02、严格双周期、材料/泛化及P03 OPEN；没有Git提交/推送、公开数据、DOI或投稿。
''',encoding='utf-8')
status='''<!-- CIRCUIT27_CURRENT_BEGIN -->
# 当前：现稿局部修订与固定电路筛查已收口

用户批准的 PCM-20260927-MANUSCRIPT-CIRCUIT-SCREEN-01 已完成。主稿17页、补充58页；十条保存系统记录的十四套PCHIP重构与完整合法分析完成，五条实验开发记录因测量合同未闭合未评分。封存协议未读取数值；零新轨迹、推理或训练。结果已回收核验，关机命令成功且三次SSH不可达。

VERIFIED为保存数组分析事实；绝对用途充分性和实验方法增量为UNKNOWN。唯一下一研究建议是取得低阈值记录的测量与用途合同，未授权后续研究。P02、严格双周期、材料/泛化及P03继续开放；无Git发布、数据公开或投稿。最终本地文稿/图件待下一获准实例会话同步。

- `phase_id`: `PHK_V23_MANUSCRIPT_CIRCUIT_SCREEN`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VERIFIED_SAVED_ARRAY_SCREEN_SUFFICIENCY_UNKNOWN`
- `next_research_execution_authorized`: `false`

<!-- CIRCUIT27_CURRENT_END -->'''
for name in ['README.md','active_phase.md','PROJECT_STATE.md','docs/plans/NEXT_ACTIONS.md']:
    p=ROOT/name;t=p.read_text(encoding='utf-8')
    t,count=re.subn(r'<!-- CIRCUIT27_CURRENT_BEGIN -->.*?<!-- CIRCUIT27_CURRENT_END -->',status,t,count=1,flags=re.S)
    assert count==1,name
    if name=='docs/plans/NEXT_ACTIONS.md':
        t=status+'\n\n[完整交付](../../paper/paper_revision_20260927_circuit_screen/README.md) · [收口](../experiment/2026-09-28-manuscript-circuit-screen-closeout.md) · [冻结执行合同](../../paper/paper_revision_20260927_circuit_screen/instructions.md)。\n\n本轮已完成，不继续运行。下一测量与用途合同任务为PROPOSED_NOT_AUTHORIZED，4000/800训练预算未启动。外部数据访问与正式归档位置另待批准。\n'
    p.write_text(t,encoding='utf-8')
index_readme=ROOT/'docs/experiment/README.md';t=index_readme.read_text(encoding='utf-8')
t=t.replace('最新：[W+A','历史2026-09-25：[W+A',1)
t=t.replace('# Experiment ledger protocol','# Experiment ledger protocol\n\n最新：[现稿局部修订与固定电路筛查收口](2026-09-28-manuscript-circuit-screen-closeout.md)。保存数组分析完成；实验资格与用途充分性未知，无后续训练授权。',1)
index_readme.write_text(t,encoding='utf-8')

prefix=rel(HERE)+'/'
m=RunManifest(run_id='20260928-manuscript-circuit-screen',experiment_group_id=TASK,tier='development',
 scientific_role='FIXED_VOLTAGE_ONLY_SAVED_ARRAY_SCREEN_NO_NEW_TRAJECTORY',gate='SERIALIZATION_KCL_ALGEBRA_AND_BRANCH_QUALIFICATION',
 started_at=config['frozen_at_utc'],ended_at=datetime.now(timezone.utc).isoformat(),
 command=['python','scripts/run_voltage_circuit_screen.py','--config','configs/voltage_circuit_screen_20260927.json','--mode','predict then score; figures from saved outputs'],
 execution_status='COMPLETE_WITH_EXPERIMENTAL_INPUT_UNCLOSED',numerical_validity='ALL_TEN_SAVED_SIMULATION_RECORDS_VALID',
 gate_outcome='VERIFIED_CONTINUOUS_ERRORS_ABSOLUTE_SUFFICIENCY_UNKNOWN',route_disposition='CLOSE_NEXT_MEASUREMENT_CONTRACT_ONLY_PROPOSED',
 evidence_identity='TEN_LOCKED_PCHIP_PREDICTION_ARRAYS_FROM_SAVED_AUTHOR_MODEL',claim_status='VERIFIED_SAVED_ARRAY_SCREEN_SUFFICIENCY_UNKNOWN',
 code_identity=dict(baseline=config['baseline'],successful_scoring=prefix+'circuit-screen/scoring-source.py',successful_scoring_sha256=execution['source_identity'],
   initial_engineering_interruption=prefix+'circuit-screen/attempt1-analysis-source.py',current_analysis_entry='scripts/run_voltage_circuit_screen.py'),
 environment=read(OUT/'environment.json'),physical_contract_id='UNCHANGED_PINNED_AUTHOR_MODEL_C_AND_RL_ONLY_IN_PREDICTION',
 split_id='FIVE_SIMULATION_CASES_TWO_SAVED_STEPS_EXPERIMENTAL_HOLDOUT_SEALED',method_id='SCIPY_1P14P1_FIXED_PCHIP_ANALYTIC_CIRCUIT',
 case_id='THREE_SINGLE_AND_TWO_PAIR_SAVED_CASES',seed=0,
 planned_budget=dict(saved_systems=10,voltage_reconstructions=14,observations_per_record=197,experimental_development_records_max=5,
                     new_ODE_PDE_steps=0,new_training_steps=0,seed_field_semantics='unused deterministic analysis'),
 actual_budget=dict(prediction_system_files=10,prediction_device_roles=14,prediction_generations=1,experimental_numeric_records_read=0,
                    new_system_steps=0,new_network_queries=0,new_training_steps=0,prediction_seconds=lock['elapsed_seconds'],
                    successful_score_seconds=execution['elapsed_seconds'],score_attempts=2,
                    interrupted_scoring='Engineering cancellation-scale check only; predictions retained',figures='local saved-array rendering; one plot-limit adjustment'),
 checkpoint=dict(kind='no_neural_checkpoint',predictions_locked=True,manifest=prefix+'circuit-screen/predictions-locked.json'),
 evaluator_id='NATIVE_TRAPEZOID_1MA_NORMALIZATION_WITH_SEPARATE_NONENDPOINT_DECOMPOSITION',
 artifacts=dict(delivery=prefix+'README.md',results=prefix+'circuit-screen/results.json',inputs=prefix+'input-inventory.json',
  config='configs/voltage_circuit_screen_20260927.json',experimental=prefix+'experimental-qualification.json',
  recovery=prefix+'build/cloud/recovery.json',shutdown=prefix+'build/cloud/shutdown.json',data_handling=prefix+'data-handling-record.json',
  engineering_failure=prefix+'circuit-screen/attempt1-analysis.log'),failure_class=None,replay_of=None,supersedes=None)
ExperimentLedger(ROOT/'docs/experiment').record(m)
print('CLOSEOUT_RECORDED; run document consistency gate; perform only planned temporary cleanup')
