"""Record the completed bounded comparison; no scientific recomputation."""
from pathlib import Path
from datetime import datetime,timezone
import json,re,shutil,sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from pinn_pcm_sci.ledger import RunManifest,ExperimentLedger
TASK='PCM-20260928-CUBIC-ENERGY-DISCRIMINATION-01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rel(p):return p.relative_to(ROOT).as_posix()
config=read(ROOT/'configs/cubic_energy_comparison_20260928.json')
lock=read(HERE/'comparison/predictions-locked.json')
r=read(HERE/'scoring-subset/results/results.json')
ind=read(HERE/'build/independent-reproduction.json')
doc=read(HERE/'build/visual-review-manuscript.json')
fig=read(HERE/'build/figure-review-complete.json')
score=read(HERE/'scoring-subset/results/execution-score.json')
pack=read(HERE/'comparison/execution-package.json')
assert len(lock['records'])==10 and len(r['records'])==10 and len(r['pchip_reproduction'])==14
assert ind['status']=='PASS' and ind['complete_results_exact_match'] and fig['status']=='PASS'
assert all(x['waveforms_FP64_reproduced'] and x['peaks_exact'] for x in r['pchip_reproduction'])
assert all(d['KCL']['pass'] and d['Euler_charge']['pass'] and all(m['decomposition']['pass'] for m in d['methods'].values()) for rec in r['records'] for d in rec['devices'])
for name in ['results-report.md','README.md','measurement-request-draft.md','measurement-source-status.json','manuscript.docx','manuscript.pdf']:
    assert (HERE/name).is_file()

inddir=Path(ind['independent_directory'])
shutil.copyfile(inddir/'run_isolated.py',HERE/'build/independent-runner.py')
shutil.copyfile(inddir/'isolation-check.json',HERE/'build/independent-isolation.json')
shutil.copyfile(inddir/'results/execution-score.json',HERE/'build/independent-score-execution.json')

write(HERE/'build/engineering-verification.json',dict(task_id=TASK,
 tests=[dict(command=r'.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_cubic_energy_comparison.py -v',tests=3,outcome='PASS',scope='constant/linear/cubic; units/short ending; endpoints/no extrapolation; no hidden scoring interface'),
        dict(command=r'.\.venv\Scripts\python.exe -m unittest tests.test_circuit_energy_tools -v',tests=5,outcome='PASS',scope='analytic energy versus independent Gauss4; piecewise-linear reference; 196 interval partition; Euler signs/closure')],
 source_review='Relevant eight metric functions and detector equal to frozen successful code; no solver entry in portable helper',
 scientific_pipeline='All fourteen KCL/decomposition/charge checks and all window Euler energy checks passed',
 pchip_reproduction='14 role records within fixed FP64 scale; exact peak lists',
 independent_reproduction='Exact complete result JSON equality and required-input failure, see independent-reproduction.json',
 initial_engineering_event='One hand-computed synthetic expected reference area corrected before real scoring; integration formula unchanged',
 numerical_faults_during_real_prediction_or_scoring=0))

targets=list((HERE/'build/render-manuscript').glob('page-*.png'))
dup=HERE/'build/render-manuscript/manuscript.pdf'
assert dup.read_bytes()==(HERE/'manuscript.pdf').read_bytes()
targets.append(dup)
targets.extend([HERE/'build/figure-review-waveforms.png',HERE/'build/figure-review-energy.png'])
targets.extend(p for p in inddir.rglob('*') if p.is_file())
write(HERE/'build/cleanup-plan.json',dict(task_id=TASK,
 allowed_roots=[str((HERE/'build/render-manuscript').resolve()),str((HERE/'build').resolve()),str(inddir.resolve())],
 reason='Completed document/figure QA and exact isolated re-score; canonical arrays and outputs preserved',
 preserved='Source originals, locked CS predictions, complete portable subset, equations, final PDF/DOCX, fifteen figures, logs and isolated runner/check',
 files=[dict(path=str(p.resolve()),bytes=p.stat().st_size) for p in targets]))
write(HERE/'data-handling-record.json',dict(task_id=TASK,
 policy='docs/governance/PINN_PCM_Data_Handling_Norms_2026-09-28.md',
 blocks=[dict(name='old_source_arrays_and_PCHIP',purpose='unchanged historical evidence',status='REUSED_READ_ONLY',
   local=['outputs/runs/20260926-core-revision-vo2-bridge/vo2','paper/paper_revision_20260927_circuit_screen/circuit-screen/predictions'],
   remote='Prior task transfer record retained; not contacted in this CPU-only task'),
  dict(name='new_CS_predictions_scores_energy_figures_manuscript',purpose='scientific evidence and deliverable',local=rel(HERE),remote=None,
   status='PENDING_NEXT_AUTHORIZED_SESSION_SYNC',GPU_started=False,restart_for_sync=False),
  dict(name='portable_subset',purpose='required handoff and saved-array rescoring',local=rel(HERE/'scoring-subset'),status='INDEPENDENT_RESCORING_VERIFIED_LOCAL',
   bytes_from_input_transfer=ind['copied_bytes'],shared_arrays='one source/time/observation block per system; FP64/native times retained'),
  dict(name='temporary_independent_copy',local=str(inddir),purpose='completed isolated verification only',
   status='ELIGIBLE_FOR_CLEANUP_AFTER_EXACT_RESULT_CHECK',canonical=rel(HERE/'scoring-subset'),evidence='build/independent-reproduction.json'),
  dict(name='inherited_manuscript_assets',purpose='unchanged layout input',status='HARDLINKS_NOT_INDEPENDENT_BACKUP',evidence='build-dependencies.json'),
  dict(name='experimental_CSV_and_historical_full_pack',status='UNCHANGED_NOT_OPENED_NUMERICALLY_NOT_MOVED_NOT_DELETED')],
 external_access='NOT_ESTABLISHED_P03_OPEN',remote_sync='PENDING_NEXT_AUTHORIZED_SESSION',
 local_cleanup=dict(status='PENDING',plan='build/cleanup-plan.json'),no_raw_precision_reduction=True,
 no_original_or_expensive_cache_deleted=True))

closeout=ROOT/'docs/experiment/2026-09-28-cubic-energy-comparison-closeout.md'
closeout.write_text('''# 固定CS对照与焦耳能量辨别收口

**VERIFIED：**PCM-20260928-CUBIC-ENERGY-DISCRIMINATION-01完成批准范围。十套CS只预测一次，十四条角色/步长与旧PCHIP保存预测配对；电流、峰、分解、电荷、三窗口/196区间能量全部保留。CS对静息极小误差及抑制两角色有RMS改善，对12.5V、15.8V及激发两角色恶化；各角色方向在两来源步长一致。CS有保存时刻负器件电流与负耗散。总能量与区间能量、电流指标不同向，不升级为温度或PINN证据。

独立工作区外评分与首次完整结果精确一致，研究仓库数据访问被拒绝，缺输入立即失败；没有历史24.6GB全包重跑。主稿仅更新可用性文字、单次构建17页，未改58页补充；测量请求草稿未发送。

**SUPPORTED_INTERPRETATION：**固定CS未形成统一替代优势，不自动延伸插值扫描或新神经训练。唯一下一研究建议是取得五条实验开发记录的测量接线/通道/驱动和C/RL说明。**UNKNOWN：**用途充分性、连续误差界、实验方法增量及内部热状态；P02、严格双周期、材料/泛化及P03保持开放。

本地CPU、FP64；零新系统步、零神经更新、零实验CSV数值读取、零GPU作业。新产物本地保留、待下一获准实例会话同步。无Git发布、DOI、外部数据上传或投稿。

见[完整交付](../../paper/paper_revision_20260928_circuit_comparison/README.md)、[研究报告](../../paper/paper_revision_20260928_circuit_comparison/results-report.md)及[运行清单](manifests/20260928-cubic-energy-comparison.json)。
''',encoding='utf-8')
status='''<!-- CUBIC28_CURRENT_BEGIN -->
# 当前：固定样条对照与焦耳能量辨别已完成

PCM-20260928-CUBIC-ENERGY-DISCRIMINATION-01完成批准范围。十套锁定CS、十四条配对、三窗口/196区间焦耳能量、独立评分子集、测量草稿与17页局部修订主稿已交付；58页补充沿用不变。见[结果入口](paper/paper_revision_20260928_circuit_comparison/README.md)。

VERIFIED：CS对不同角色有相反RMS效应，伴随保存时刻负电流/负耗散；能量总量、时间分配与电流波形不能互相认证。独立目录结果与首次评分精确一致。UNKNOWN：用途充分性、实验和PINN增量、内部热状态。唯一后续建议为取得五条开发记录测量说明，未授权校准或新pilot。

零新增系统轨迹、训练、实验CSV读取或GPU作业。新交付待下一获准实例会话同步；P02、严格双周期、材料/泛化及P03开放，无Git发布、数据公开或投稿。

- `phase_id`: `PHK_V23_CUBIC_ENERGY_DISCRIMINATION`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VERIFIED_CS_MIXED_EFFECTS_ENERGY_TIME_DISTRIBUTION`
- `next_research_execution_authorized`: `false`

<!-- CUBIC28_CURRENT_END -->'''
for name in ['README.md','active_phase.md','PROJECT_STATE.md','docs/plans/NEXT_ACTIONS.md']:
    p=ROOT/name;t=p.read_text(encoding='utf-8')
    block=status.replace('(paper/','(../../paper/') if name=='docs/plans/NEXT_ACTIONS.md' else status
    t,count=re.subn(r'<!-- CUBIC28_CURRENT_BEGIN -->.*?<!-- CUBIC28_CURRENT_END -->',block,t,count=1,flags=re.S)
    assert count==1,name
    if name=='docs/plans/NEXT_ACTIONS.md':
        t=block+'\n\n[收口](../experiment/2026-09-28-cubic-energy-comparison-closeout.md) · [执行合同](../../paper/paper_revision_20260928_circuit_comparison/instructions.md)。本包关闭；测量说明、C校准或PINN研究不自动启动。\n'
    p.write_text(t,encoding='utf-8')
index=ROOT/'docs/experiment/README.md';t=index.read_text(encoding='utf-8')
t=t.replace('最新：[现稿局部修订','历史：[现稿局部修订',1)
t=t.replace('# Experiment ledger protocol','# Experiment ledger protocol\n\n最新：[固定CS与焦耳能量比较收口](2026-09-28-cubic-energy-comparison-closeout.md)。本地有界对照及独立子集完成，无后续科研授权。',1)
index.write_text(t,encoding='utf-8')

prefix=rel(HERE)+'/'
m=RunManifest(run_id='20260928-cubic-energy-comparison',experiment_group_id=TASK,tier='development',
 scientific_role='FIXED_INTERPOLATION_CONTROL_AND_ENERGY_DIAGNOSTIC_NO_NEW_DEVICE_TRAJECTORY',
 gate='FROZEN_SOURCE_CHECKS_AND_ANALYTIC_ENERGY_ENGINEERING',started_at=lock['started'],ended_at=datetime.now(timezone.utc).isoformat(),
 command=['python',prefix+'scoring-subset/scripts/run_cubic_energy_comparison.py','--root',prefix+'scoring-subset','--config','config.json','--mode','score'],
 execution_status='COMPLETE',numerical_validity='TEN_SAVED_SYSTEMS_AND_ALL_ENERGY_CHECKS_VALID',
 gate_outcome='CS_MIXED_ROLE_EFFECTS_NEGATIVE_EXCURSIONS_NO_UNIFORM_DOMINANCE',route_disposition='CLOSED_NEXT_MEASUREMENT_CLARIFICATION_PROPOSED',
 evidence_identity='TEN_LOCKED_CS_PREDICTIONS_AND_REUSED_PCHIP_WITH_NATIVE_SOURCE_SUBSET',
 claim_status='VERIFIED_CS_MIXED_EFFECTS_ENERGY_TIME_DISTRIBUTION',
 code_identity=dict(baseline=config['baseline'],sources_at_lock=lock['source_identity'],source_snapshot=prefix+'scoring-subset/scripts'),
 environment=lock['environment'],physical_contract_id='UNCHANGED_PINNED_AUTHOR_C_AND_RL_WITH_FIXED_VOLTAGE_OBSERVATIONS',
 split_id='FIVE_DEVELOPMENT_SIMULATION_CASES_TWO_SOURCE_STEPS_EXPERIMENTAL_NUMERIC_UNREAD',
 method_id='SCIPY_1P14P1_NOT_A_KNOT_CS_WITH_ANALYTIC_CIRCUIT_AND_ENERGY',case_id='THREE_SINGLE_AND_TWO_PAIR_SAVED_CASES',seed=0,
 planned_budget=dict(CS_system_fits=10,role_step_pairs=14,new_system_steps=0,new_training_steps=0,experimental_numeric_reads=0),
 actual_budget=dict(CS_system_fits=10,PCHIP_refits=0,role_step_pairs=14,score_passes=2,score_pass_roles=['primary','independent_reproduction'],
   energy_intervals_per_role_method=196,new_system_steps=0,new_training_steps=0,new_network_queries=0,experimental_numeric_reads=0,GPU_jobs=0,
   CS_prediction_seconds=lock['elapsed_seconds'],first_score_seconds=score['elapsed_seconds'],packaging_seconds=pack['elapsed_seconds'],
   independent_copy_score_check_seconds=ind['elapsed_seconds'],seed_semantics='unused deterministic analysis'),
 checkpoint=dict(kind='locked_saved_arrays',manifest=prefix+'comparison/predictions-locked.json'),
 evaluator_id='UNCHANGED_NATIVE_TRAPEZOID_1MA_PLUS_POLYNOMIAL_VERSUS_LINEAR_POWER_ENERGY',
 artifacts=dict(delivery=prefix+'README.md',report=prefix+'results-report.md',results=prefix+'scoring-subset/results/results.json',
   config='configs/cubic_energy_comparison_20260928.json',subset=prefix+'scoring-subset/README.md',independent=prefix+'build/independent-reproduction.json',
   data_handling=prefix+'data-handling-record.json',measurement_draft=prefix+'measurement-request-draft.md'),
 failure_class=None,replay_of=None,supersedes=None)
ExperimentLedger(ROOT/'docs/experiment').record(m)
print('Recorded completed task; run document gate and bounded cleanup')
