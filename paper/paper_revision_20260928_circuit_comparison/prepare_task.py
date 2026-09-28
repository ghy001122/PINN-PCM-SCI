"""Activate the explicitly authorized bounded CPU comparison, without scoring."""
from pathlib import Path
import ast, hashlib, json, re, shutil, subprocess
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / 'paper/paper_revision_20260927_circuit_screen'
TASK = 'PCM-20260928-CUBIC-ENERGY-DISCRIMINATION-01'
def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

if (HERE/'preparation.json').exists():
    raise RuntimeError('Already prepared; reuse existing task')
for source, dest in [('02_CODEX_Execution_Instructions.md','instructions.md'),
                     ('01_Research_Improvement_Plan.md','research-improvement-plan.md'),
                     ('Review_and_Next_Plan_20260928.md','review-and-next-plan.md')]:
    shutil.copyfile(Path('E:/PINN-PCM')/source, HERE/dest)
old_config=json.loads((ROOT/'configs/voltage_circuit_screen_20260927.json').read_text(encoding='utf-8'))
contract=json.loads((OLD/'evidence/core-revision/vo2/frozen-config.json').read_text(encoding='utf-8'))
items=[]
for x in old_config['simulation_inputs']:
    m=json.loads((OLD/'circuit-screen/predictions'/f"{x['id']}.json").read_text(encoding='utf-8'))
    assert m['C_F']==contract['parameters_SI']['C'] and m['RL_ohm']==contract['parameters_SI']['RL']
    items.append(dict(x, pchip=f"paper/paper_revision_20260927_circuit_screen/circuit-screen/predictions/{x['id']}.npz",
        source_voltage_V=m['source_voltage_V'], C_F=m['C_F'], RL_ohm=m['RL_ohm']))
config=dict(task_id=TASK, baseline='9414c1da37cb9a101bf3ed812d248f63d4454470',
    previous_science_commit='fa475c257651c17fcfe83007ab0fe238c6c5995c',
    frozen_at_utc=datetime.now(timezone.utc).isoformat(),
    output='paper/paper_revision_20260928_circuit_comparison/comparison',
    subset='paper/paper_revision_20260928_circuit_comparison/scoring-subset',
    simulation_inputs=items, method='CubicSpline', bc_type='not-a-knot', extrapolate=False,
    scipy_version='1.14.1', time_scale_s=1e-6, engineering_safety_factor=64,
    peak_match_max_gap_s=0.25e-6, observation_rule='Reuse old locked 197 times and voltages exactly',
    windows_s=dict(full=[0.,20e-6],transient=[0.,10e-6],tail=[10e-6,20e-6]),
    energy_reference='Exact integral of native piecewise-linear saved power V*I_D',
    energy_prediction='Analytic piecewise-polynomial integral; square before integration',
    energy_intervals='All 196 intervals between the unchanged observation times',
    tau_task=None, experimental_numeric_read_authorized=False, GPU_authorized=False,
    new_system_steps=0, new_training_steps=0, CS_system_prediction_limit=10,
    original_results='paper/paper_revision_20260927_circuit_screen/circuit-screen/results.json')
write(ROOT/'configs/cubic_energy_comparison_20260928.json',config)

# Reuse exact successful metric functions; the portable helper contains no solver.
source=(OLD/'circuit-screen/scoring-source.py').read_text(encoding='utf-8')
current=(ROOT/'scripts/run_voltage_circuit_screen.py').read_text(encoding='utf-8')
functions=['now','save_json','sha','resolve','trap_weights','prediction_charge','peak_matches',
           'metrics','circuit_checks','decomposition','charge_accounting','summarize_peaks','write_csv']
def functions_in(text):
    return {n.name:ast.get_source_segment(text,n) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
a,b=functions_in(source),functions_in(current)
assert all(a[n]==b[n] for n in functions),'Relevant current and successful scoring functions differ'
detector_source=(ROOT/'pinn_pcm_sci/vo2_author_reproduction.py').read_text(encoding='utf-8')
detector=functions_in(detector_source)['detect_peaks']
helper='''"""Exact reused frozen scoring functions, without any model integration entry.
Sources: paper/paper_revision_20260927_circuit_screen/circuit-screen/scoring-source.py
and pinn_pcm_sci/vo2_author_reproduction.py:detect_peaks (project MIT license).
"""
from pathlib import Path
from datetime import datetime, timezone
from functools import lru_cache
import csv, hashlib, json
import numpy as np
from scipy.interpolate import PPoly
EPS=np.finfo(np.float64).eps
WINDOWS={'full':(0.,20e-6),'transient':(0.,10e-6),'tail':(10e-6,20e-6)}
'''+detector+'\n\n'+'\n\n'.join(a[n] for n in functions)+'\n'
(ROOT/'scripts/circuit_screen_metrics.py').write_text(helper,encoding='utf-8')
write(HERE/'preparation.json',dict(task_id=TASK, baseline=config['baseline'],
    actual_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    frozen_at_utc=config['frozen_at_utc'], reused_functions=functions+['detect_peaks'],
    reused_function_identity='verbatim source equality checked against successful old scoring snapshot',
    old_scoring_sha256=hashlib.sha256(source.encode()).hexdigest(),
    unrelated_preexisting_tracked_change='docs/governance/EXTERNAL_SKILLS.md',
    scientific_source_arrays_read=False, external_csv_numeric_read=False,
    filename_resolution='PLAN_Review_Amendments is prior PCHIP review; new Review_and_Next_Plan plus explicit new instruction authorize this one CS comparator',
    remote='OFFLINE_PENDING_NEXT_AUTHORIZED_SESSION_SYNC; no instance startup for CPU work'))
status='''<!-- CUBIC28_CURRENT_BEGIN -->
# 当前：固定样条对照、热输入辨别与现稿收口

用户已明确授权 `PCM-20260928-CUBIC-ENERGY-DISCRIMINATION-01`：本地CPU对十条保存记录新增固定CS预测，复用PCHIP，锁定后比较原电流指标与焦耳能量；准备测量澄清草稿、独立评分子集及必要稿件更新。见[执行合同](paper/paper_revision_20260928_circuit_comparison/instructions.md)。本轮不读取实验CSV数值，不新增系统轨迹、训练、GPU作业、参数校准或外部发布。4000/800 pilot未授权。

实现/准备不代表方法增量；科学结论暂为UNKNOWN。旧正反证据、P02/P03及封存协议保持原身份。

- `phase_id`: `PHK_V23_CUBIC_ENERGY_DISCRIMINATION`
- `lifecycle_state`: `EXECUTE`
- `blocker_id`: `NONE`
- `claim_status`: `UNKNOWN_PENDING_BOUNDED_SAVED_ARRAY_COMPARISON`
- `next_research_execution_authorized`: `true`

<!-- CUBIC28_CURRENT_END -->'''
for name in ['README.md','active_phase.md','PROJECT_STATE.md']:
    p=ROOT/name;t=p.read_text(encoding='utf-8')
    oldblock=re.search(r'<!-- CIRCUIT27_CURRENT_BEGIN -->.*?<!-- CIRCUIT27_CURRENT_END -->',t,re.S)
    if oldblock:
        historical=oldblock.group().replace('`phase_id`','`historical_phase_id`').replace('`lifecycle_state`','`historical_lifecycle_state`').replace('`blocker_id`','`historical_blocker_id`').replace('`claim_status`','`historical_claim_status`').replace('`next_research_execution_authorized`','`historical_next_research_execution_authorized`')
        t=t.replace(oldblock.group(),historical,1)
    p.write_text(status+'\n\n'+t,encoding='utf-8')
live=ROOT/'docs/plans/NEXT_ACTIONS.md'
shutil.copyfile(live,ROOT/'archive/2026-09-28-pre-cubic-energy-next-actions.md')
live.write_text(status.replace('(paper/','(../../paper/')+'\n\n执行顺序：接口与工程检查 → 全部CS锁定 → 子集导出 → 一次评分 → 独立目录复评分 → 结果/图件/稿件收口。没有自动后续训练。\n',encoding='utf-8')
print('Prepared bounded contract and activation; document gate required before computation')
