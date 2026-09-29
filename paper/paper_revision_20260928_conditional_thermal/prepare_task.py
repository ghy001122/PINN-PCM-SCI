"""Freeze the user-authorized local conditional response study; no propagation."""
from pathlib import Path
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib,json,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from pinn_pcm_sci.vo2_author_reproduction import P,CASES
HERE=Path(__file__).resolve().parent
TASK='PCM-20260928-CONDITIONAL-THERMAL-CLOSURE-01'
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
if (HERE/'config.json').exists():raise RuntimeError('Already frozen; reuse the existing config')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert head=='390ca72aee60a0f483697d52b72674bf07dd7297'
for source,dest in [('CODEX_Execution_Instructions_Concise.md','instructions.md'),('Review_and_Next_Plan_20260928（2）.md','review.md'),('CODEX_Next_Step_Proposal.md','proposal.md')]:
    shutil.copyfile(Path('E:/PINN-PCM')/source,HERE/dest)
subset=ROOT/'paper/paper_revision_20260928_circuit_comparison/scoring-subset'
prior=json.loads((subset/'config.json').read_text(encoding='utf-8'))
cases={x['id']:x for x in CASES};records=[]
for row in prior['records']:
    x=dict(row);case=cases[x['case']]
    x['eta']=case['eta'];x['source']=x['provenance']['original_path']
    x['predictions']={k:str((subset/v).relative_to(ROOT)).replace('\\','/') for k,v in x['predictions'].items()}
    x['input_identity']={}
    for path in [x['source'],*x['predictions'].values()]:
        p=ROOT/path
        if not p.is_file():raise FileNotFoundError(p)
        x['input_identity'][path]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    records.append(x)
config=dict(task_id=TASK,baseline=head,previous_science_commit='709b10fd28fc8fc80c9103acd68be02c35ac2816',
    frozen_at_utc=datetime.now(timezone.utc).isoformat(),records=records,parameters_SI=asdict(P),
    source_contract='paper/paper_revision_20260927_circuit_screen/evidence/core-revision/vo2/frozen-config.json',
    methods=['Q_ref','V_ref','P','CS'],dtype='float64',threads=4,device='local_CPU',
    initial_temperature_K=325.,hysteresis_initial_temperature_K=324.9,
    gauss_main=4,gauss_verification=8,temperature_quadrature_max_difference_K=1e-6,
    limits=dict(main_system_responses=40,verification_responses=40,source_history_checks=10,prediction_history_replays=20),
    windows_s=dict(full=[0.,20e-6],transient=[0.,10e-6],tail=[10e-6,20e-6]),
    metrics='Normalized trapezoid time weights; RMS/max/signed mean/end and absolute K range; no alignment',
    source_replay_tolerance='Discrete delta/reversed exact; float fields 64*eps*max(1,max(abs(saved field))); report actual errors and bitwise equality',
    source_representation='Q_ref native V*I_device linear; V_ref native V linear; P/CS exact saved PPoly in original scaled time',
    prediction_input_boundary='Temperature solve and history prediction receive only frozen voltage polynomials, parameters and legal initial state; source T/R/g/H used only controls/scoring',
    discontinuity_rule='Union of actual polynomial breakpoints and native output times; continuous state, never reset',
    clipping='No clipping of voltage, forcing, I or evolved temperature; source constitutive clip305to370 retained only inside author law',
    closure='No feedback from I_R to voltage or temperature; old I_KCL and historical energy scores remain unchanged',
    tau_task=None,no_training=True,no_GPU=True,no_experimental_csv=True,no_heldout_protocol=True,
    output=str(HERE.relative_to(ROOT)).replace('\\','/'),remote='PENDING_NEXT_AUTHORIZED_SESSION_SYNC',
    local_free_bytes_before=shutil.disk_usage(ROOT).free)
write(HERE/'config.json',config)
status='''<!-- THERMAL28_CURRENT_BEGIN -->
# 当前：条件热响应与迟滞本构闭合

用户明确授权 `PCM-20260928-CONDITIONAL-THERMAL-CLOSURE-01`。复用十套保存记录及锁定PCHIP/CS，在本地CPU完成40条条件热响应、一次4/8点求积核对和有条件的10条源历史核对/20条无反馈历史重放。见[执行合同](paper/paper_revision_20260928_conditional_thermal/instructions.md)。本轮只更新新对外稿访问段并复用既有测量请求稿；不训练、不重跑原轨迹、不读取实验CSV或留出数值，不使用GPU，不发布或发送。

科学结论暂为UNKNOWN。旧波形/能量评分及负面结果保持原身份，P02/P03与材料/二维/PINN增量不自动闭合。本段 supersedes 下方历史当前状态。

- `phase_id`: `PHK_V23_CONDITIONAL_THERMAL_CLOSURE`
- `lifecycle_state`: `EXECUTE`
- `blocker_id`: `NONE`
- `claim_status`: `UNKNOWN_PENDING_CONDITIONAL_THERMAL_CLOSURE`
- `next_research_execution_authorized`: `true`

<!-- THERMAL28_CURRENT_END -->'''
for name in ['README.md','active_phase.md','PROJECT_STATE.md']:
    p=ROOT/name;t=p.read_text(encoding='utf-8')
    old=re.search(r'<!-- CUBIC28_CURRENT_BEGIN -->.*?<!-- CUBIC28_CURRENT_END -->',t,re.S)
    if old:
        hist=old.group()
        for k in ['phase_id','lifecycle_state','blocker_id','claim_status','next_research_execution_authorized']:
            hist=hist.replace('`'+k+'`','`historical_'+k+'`')
        t=t.replace(old.group(),hist,1)
    p.write_text(status+'\n\n'+t,encoding='utf-8')
live=ROOT/'docs/plans/NEXT_ACTIONS.md'
shutil.copyfile(live,ROOT/'archive/2026-09-28-pre-conditional-thermal-next-actions.md')
live.write_text(status.replace('(paper/','(../../paper/')+'\n\n执行：必要小型测试 → 冻结源码 → 温度与求积复核 → 合格后来源历史核对及P/CS重放 → 保存数组评分、固定12.5V图与全工况索引 → 访问段和请求状态 → 关闭本包。无自动pilot。\n',encoding='utf-8')
print('Frozen authorized task; document consistency gate required before scientific execution.')
