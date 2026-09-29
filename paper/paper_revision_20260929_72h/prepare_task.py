"""Freeze the user-approved 72h manuscript and single joint prototype."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
from dataclasses import asdict
import ast,hashlib,json,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from pinn_pcm_sci.vo2_author_reproduction import P
TASK='PCM-20260929-72H-MANUSCRIPT-JOINT-01'
if (HERE/'config.json').exists():raise RuntimeError('Use already frozen contract')
for source,dest in [('02_CODEX_72h_Execution_Instructions.md','instructions.md'),('01_Condensed_Assessment_and_72h_Plan.md','assessment.md')]:
    shutil.copyfile(Path('E:/PINN-PCM')/source,HERE/dest)
started=datetime(2026,9,29,7,30,tzinfo=timezone.utc)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert head=='adf34b5e22c2d8a6654dd2908c230c7a186239f7'
cfg=dict(task_id=TASK,baseline=head,started_utc=started.isoformat(),
    admission_deadline_utc=(started+timedelta(hours=8)).isoformat(),science_deadline_utc=(started+timedelta(hours=36)).isoformat(),
    delivery_deadline_utc=(started+timedelta(hours=72)).isoformat(),
    case='pair_excitation',dt_s=.5e-9,end_s=20e-6,Vin_V=[11.,9.4],eta=.12,parameters_SI=asdict(P),
    initial_temperature_K=325.,initial_voltage_V=[0.,0.],hysteresis_initial_K=324.9,
    shared_temperature='paper/paper_revision_20260928_conditional_thermal/arrays/pair_excitation-0p5ns/thermal.npz:T_P',
    finite_observations='paper/paper_revision_20260928_circuit_comparison/scoring-subset/inputs/pair_excitation-0p5ns.npz:observation_time,observation_voltage',
    original_source_for_scoring_only='outputs/runs/20260926-core-revision-vo2-bridge/vo2/pair_excitation-0p5ns.npz',
    methods=['N_dyn','F_dyn','S_dyn'],seeds=[29,43],seed43_requires_seed29_joint_increment=True,
    representation=dict(neural='existing make_mlp, 1 input, 2 output, 64 width, 4 Tanh hidden layers',
        time_input='2*t/end-1',initial_gate='a=t/end',temperature_correction_units='K',voltage_correction_units='V',
        final_layer='all weights and biases zero; N/F temperature parameters identical at each seed',
        spline='cubic clamped B-splines on sorted union of 197 observations and196 midpoints; zero coefficients',
        T0='same unchanged native FP64 array in all methods; no T0 supervision; native discrete representation'),
    loss=dict(V_scale_V=11.,I_scale_A=.001,P_scale_W=.001,device_weights=[.5,.5],
        observation_weights='normalized trapezoid weights on original197 times',
        observation_sampling='linear interpolation of native voltages, no nearest-node substitution',
        physics_weights='equal h per40000intervals; two devices equal',
        N_and_S='obs + mean((rT/Pscale)^2)',F='obs + mean((rT/Pscale)^2)+mean((rRC/Iscale)^2)'),
    optimizer=dict(adam_updates=600,adam_lr=.001,adam_betas=[.9,.999],adam_eps=1e-8,adam_grad_clip=10.,
        neural_lbfgs_evals=100,spline_lbfgs_evals=700,lbfgs='reuse accepted_lbfgs strong_wolfe max_iter1 history50 true full gradients; trial rollback'),
    increment=dict(current_relative=.10,current_absolute_A=1e-5,noninferiority_factor=1.05,
        absolute_floors=dict(temperature_RMS_K=1e-6,observation_RMS_V=1e-8,thermal_RMS_W=1e-10),
        noninferiority_rule='candidate <= max(1.05*control,control+absolute_floor) independently for T/obs/replayed heat',
        scope='prospective development, not formal OOD; joint two-device native trapz RMS'),
    gradient_admission=dict(relative_tolerance=2e-4,absolute_tolerance=1e-7,
        finite_steps_K=[1e-3,1e-4,1e-5,1e-6],fixed_events_only=True,
        rule='report all directions/steps; qualify two smallest steps preserving full event signature, no smoothing of events; cross-event variation separate'),
    resource=dict(threads=4,host_stop_GiB=12,GPU_allocated_stop_GiB=16,minimum_free_GiB=4),
    gpu_endpoint='region-46.seetacloud.com:28355',gpu_probe='CONNECTION_REFUSED_USER_ASKED_FOR_CURRENT_ENDPOINT',
    no_source_T_R_H_or_full_current_in_training=True,no_experimental_or_holdout_numeric=True,no_publication=True,
    output='outputs/runs/20260929-joint-reconstruction',remote_sync='PENDING')
(HERE/'config.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
# Reuse the accepted-state L-BFGS implementation verbatim without importing its
# unrelated old scientific campaign and reference/calibration modules.
src=(ROOT/'pinn_pcm_sci/phk_v23_lf11_coverage.py').read_text(encoding='utf-8')
node=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='accepted_lbfgs')
target=ROOT/'pinn_pcm_sci/vo2_joint_lbfgs.py'
target.write_text('"""Verbatim accepted_lbfgs from phk_v23_lf11_coverage; project MIT; Torch BSD-3-Clause."""\nimport copy\nimport torch\n\n'+ast.get_source_segment(src,node)+'\n',encoding='utf-8')
status='''<!-- JOINT72_CURRENT_BEGIN -->
# 当前：72小时成稿与唯一联合重构原型

用户明确授权 PCM-20260929-72H-MANUSCRIPT-JOINT-01。写作与原型独立并行：保留二维E/F、F_cov正向核心，压缩VO2辅助证据；固定pair_excitation的N/F/S共同起点和离散物理，先seed29，只有联合增量满足才补N/F seed43。见[执行合同](paper/paper_revision_20260929_72h/instructions.md)。

8小时内可信梯度/资源准入；36小时冻结科学结果，72小时完成正文/补充/复算材料。GPU已获授权，使用后回收并及时关闭。实验数值、留出、参数拟合、额外训练臂和Git发布均不在范围。科学增量暂为UNKNOWN；旧冻结证据不改。

- `phase_id`: `PHK_V23_72H_MANUSCRIPT_JOINT_RECONSTRUCTION`
- `lifecycle_state`: `EXECUTE`
- `blocker_id`: `NONE`
- `claim_status`: `UNKNOWN_PENDING_FIXED_JOINT_RECONSTRUCTION`
- `next_research_execution_authorized`: `true`

<!-- JOINT72_CURRENT_END -->'''
for name in ['README.md','active_phase.md','PROJECT_STATE.md']:
    p=ROOT/name;t=p.read_text(encoding='utf-8');old=re.search(r'<!-- THERMAL28_CURRENT_BEGIN -->.*?<!-- THERMAL28_CURRENT_END -->',t,re.S)
    hist=old.group()
    for k in ['phase_id','lifecycle_state','blocker_id','claim_status','next_research_execution_authorized']:hist=hist.replace('`'+k+'`','`historical_'+k+'`')
    t=t.replace(old.group(),hist,1);p.write_text(status+'\n\n'+t,encoding='utf-8')
live=ROOT/'docs/plans/NEXT_ACTIONS.md';shutil.copyfile(live,ROOT/'archive/2026-09-29-pre-72h-next-actions.md')
live.write_text(status.replace('(paper/','(../../paper/')+'\n\n先零修正/真梯度/资源准入，同步可构建稿v1；再固定三端点、共同RC读出和一次评分；条件满足才seed43。失败正常交付，不延迟成稿。\n',encoding='utf-8')
print(TASK,'frozen; consistency gate required')
