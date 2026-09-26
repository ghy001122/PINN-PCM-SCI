"""Close the approved task only after numerical, recovery and document delivery."""
from pathlib import Path
import datetime,json,re,shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RUN=ROOT/'outputs/runs/20260926-core-revision-vo2-bridge'
PACKAGE=Path('D:/Temp/PINN-PCM-Standalone-20260926')
TASK='PCM-20260926-CORE-REVISION-VO2-BRIDGE-01'
RUN_ID='20260926-core-revision-vo2-bridge'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def complete_manifest(manifest):
    """Fit this campaign's detail into the repository's existing ledger schema."""
    from pinn_pcm_sci.ledger import RunManifest
    manifest=dict(manifest)
    manifest['command']=['python','-u','cloud/phk_v23_coverage/run_cloud.py']
    manifest['evidence_identity']='LOCKED_F_COV_ARRAYS_AND_SEPARATE_PINNED_AUTHOR_MODEL_TRAJECTORIES'
    manifest['planned_budget']=dict(seeds=manifest.pop('seeds'),inputs=manifest.pop('prescribed_inputs'),
        scientific_training_arms=2,adam_updates_per_arm=1500,lbfgs_full_evaluations_per_arm=300,
        author_cases=5,author_step_sizes_s=[1e-9,5e-10],author_system_steps_max=300000)
    manifest['code_identity']=dict(baseline_commit='90508f05a6f233a485413c7589cc74420015cbea',
        training_runtime_manifest=manifest['code_identity'],author_model=manifest.pop('author_model_identity'),
        readout_recovery='outputs/runs/'+RUN_ID+'/readout-recovery.json')
    manifest['environment']=dict(gpu=read(RUN/'environment.json'),
        standalone_runtime='Python 3.11.9; NumPy 2.1.3; SciPy 1.14.1; repository access denied')
    manifest['physical_contract_id']='UNCHANGED_SHORTER_SYNTHETIC_CONTRACT_AND_SEPARATE_AUTHOR_VO2_CONTRACT'
    manifest['checkpoint']=dict(endpoints_locked=True,reference_read_for_training=False,
        files={str(seed):'outputs/runs/'+RUN_ID+f'/fcov/seed-{seed}/F_cov/checkpoint.pt' for seed in (29,43)},
        sha256=read(RUN/'readout-recovery.json')['checkpoint_sha256'])
    manifest['evaluator_id']='ORIGINAL_THREE_REFERENCE_TWO_READER_A_B_STRICT_AND_FIXED_AUTHOR_WAVEFORM_REPORT'
    manifest['failure_class']=None
    return RunManifest(**manifest).to_dict()

def main():
    summary=read(HERE/'coverage-summary.json');counts=summary['counts']
    closure=read(RUN/'compute-closure.json');verification=read(PACKAGE/'independent-verification.json')
    qa=read(HERE/'build/visual-review.json')
    assert closure['recovery_verified'] and closure['instance_shutdown_confirmed']
    assert set(verification['scopes'])=={'core','extension','b1','s21','s22','s23','residuals','vo2','fcov'}
    assert verification['scopes']['fcov']['verification']['passed'] and qa['status']=='PASS'
    for name in ('manuscript','supplement'):
        for ext in ('md','docx','pdf'):assert (HERE/f'{name}.{ext}').is_file()
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    costs={int(c['seed']):c for c in summary['costs']}
    termination='；'.join(f"seed {seed}: {costs[seed]['termination']}" for seed in (29,43))
    fact=f"E 相对 F_cov 在原 A/B 规则下通过 {counts['E_vs_F_cov_A']}/12、{counts['E_vs_F_cov_B']}/12 条敏感性条件；F_cov 相对旧 F 分别通过 {counts['F_cov_vs_F_A']}/12、{counts['F_cov_vs_F_B']}/12。十二条记录对应两个初始化。"
    outcome=dict(task_id=TASK,status='COMPLETE_APPROVED_SCOPE',completed_utc=now,
        scientific_facts_status='VERIFIED',interpretation_status='SUPPORTED_INTERPRETATION',
        coverage_counts=counts,coverage_independent_initializations=2,
        author_model=dict(cases=5,step_sizes_s=[1e-9,5e-10],system_steps=300000,
            quantitative_experimental_reproduction='UNKNOWN',synthetic_material_validation=False),
        standalone=dict(root=str(PACKAGE),scopes=list(verification['scopes']),external_access=False,P03='OPEN',
            neural_AD_recomputation=False),compute_recovery_and_shutdown=closure,
        open_science_items=['P02 method increment','strict two-cycle usability','material validation','generalization','P03 external full-array access'],
        next_research='Finite-observation offline reconstruction input qualification and plan review only',
        next_research_execution_authorized=False,git_published=False,data_published=False,submitted=False)
    save(RUN/'result.json',outcome)
    text=f'''# 本轮交付：现稿补强、覆盖增强与 VO₂ 文献模型

任务 `{TASK}` 已完成批准范围。基线 `90508f05a6f233a485413c7589cc74420015cbea`；所有成果保存在新目录，历史终点、阈值和不利结果保持原身份。

**VERIFIED：**两条 F_cov 均完成 1500 次 Adam，seed 29／43 分别完成 {costs[29]['lbfgs_charged']}／{costs[43]['lbfgs_charged']} 次完整 L-BFGS 评价，终点有效，共同读出完成。{fact} 完整连续效应和所有比较方向见[覆盖增强报告](coverage-report.md)及补充 S24。

**SUPPORTED_INTERPRETATION：**该比较同时改变空间覆盖和时间测度，只支持对混合测度软控制的配置比较，不能单独归因 VJP。五个作者模型工况、两个步长均完成；其定性功能描述及波形差异如实保留，定量实验复现仍为 **UNKNOWN**。

## 审阅文件

| 交付 | 文件 |
|---|---|
| 连续主稿 | [PDF](manuscript.pdf) · [DOCX](manuscript.docx) · [Markdown](manuscript.md) |
| 完整补充 | [PDF](supplement.pdf) · [DOCX](supplement.docx) · [Markdown](supplement.md) |
| 修订与证据 | [修改说明](revision-notes.md) · [主张—源表—图件映射](claim_evidence_matrix.md) · [真实构建依赖](build-dependencies.json) |
| 新对照 | [F_cov 完整报告](coverage-report.md) · [全部连续效应](tables/fcov-all-effects.csv) · [全部判决](tables/fcov-all-decisions.csv) |
| 文献模型 | [五工况报告及波形](vo2-author-reproduction.md) · [原始资产身份](literature/data-assets.json) |
| 独立复算 | [入口及能力说明](standalone-README.md) · [实际复算记录](evidence/standalone/independent-verification.json) · [外部访问方案](data-access-plan.md) |
| 下一研究 | [有限观测离线重构计划](next-research-plan.md)，`PROPOSED_NOT_AUTHORIZED` |

完整本地复算包为 `D:\\Temp\\PINN-PCM-Standalone-20260926`。九类保存数组／残差复算全部通过原容差与精确布尔核验，运行时拒绝访问原仓库。保存残差的聚合不等于重新计算神经 AD。尚无实际外部访问链接或 DOI，P03 保持 OPEN。

## 计算与收口

新神经训练仅两个 F_cov；作者模型合计 300,000 个系统步。没有新二维参考、第三步长、额外训练臂或参数扫描。实际训练终止原因：{termination}。线搜索试探点与接受态分开，失败前置测量的成本另记。

GPU 结果已回收并核验；关机请求时间 `{closure['shutdown_requested_utc']}`，随后确认 SSH 拒绝连接。证据见[回收关机记录](../../outputs/runs/20260926-core-revision-vo2-bridge/compute-closure.json)。零更新部署故障、监测断线及盘满时的读出恢复分别保留。两条训练未中断重开；最后读出由已保存时刻恢复，另记至多一个被丢弃的在途电学求解，未增加科学臂。

P02 方法增量、严格双周期、材料验证、泛化与 P03 仍开放。下一步只建议先闭合有限观测重构的数据支路、合法历史和二维热合同，再审查有限 pilot；本轮未执行该研究。Git 发布、数据公开和投稿均未进行。
'''
    (HERE/'README.md').write_text(text,encoding='utf-8')
    manifest=dict(schema_version='run-manifest-v1',run_id=RUN_ID,experiment_group_id=TASK,
        case_id='ORIGINAL_SHORTER_FULL_LABEL_PARENTS_AND_SEPARATE_AUTHOR_VO2_CASES',
        tier='development',scientific_role='TWO_FIXED_F_COV_ENDPOINTS_AND_FIVE_AUTHOR_MODEL_CASES',
        method_id='MIXED_MEASURE_COVERAGE_ENHANCEMENT_AND_PINNED_AUTHOR_EULER',
        seed=29,seeds=[29,43],split_id='ORIGINAL_COMPLETE_LABEL_DEVELOPMENT_NO_NEW_FORMAL_OOD',
        gate='ORIGINAL_A_B_STRICT_AND_FIXED_TWO_STEP_AUTHOR_MODEL_REPORTING',
        gate_outcome='COMPLETE_BOUNDED_COMPARISONS_QUANTITATIVE_MATERIAL_VALIDATION_UNKNOWN',
        numerical_validity='TWO_VALID_ENDPOINTS_AND_ALL_SAVED_ARRAY_CHECKS_PASSED',
        execution_status='COMPLETE',claim_status='VERIFIED_CORE_REVISION_WITH_BOUNDED_INTERPRETATION',
        route_disposition='CLOSE_NO_NEW_PILOT_PUBLICATION_OR_SUBMISSION',replay_of=None,supersedes=None,
        started_at=read(RUN/'deployment.json')['launched_utc'],ended_at=closure['closed_utc'],
        code_identity='outputs/runs/'+RUN_ID+'/runtime-manifest.json',
        author_model_identity='outputs/runs/'+RUN_ID+'/vo2/execution-identity.json',
        actual_budget=dict(adam_updates=sum(c['adam_updates'] for c in summary['costs']),
            lbfgs_full_evaluations=sum(c['lbfgs_charged'] for c in summary['costs']),
            readout_electrical_solves=sum(c['readout_electrical_solves'] for c in summary['costs']),
            discarded_readout_solve_upper_bound=sum(c['discarded_readout_solve_upper_bound'] for c in summary['costs']),
            author_system_steps=300000,scientific_training_arms=2,reference_generation=0,
            discarded_zero_update_complete_gradient=1,new_pilot_training=0),
        prescribed_inputs=dict(parent_protocol='shorter',parent_seeds=[29,43],
            parent_path='outputs/runs/20260915-lf11-protocol-history/seed-{seed}/common-fit/parent.pt',
            coverage_configs='outputs/runs/'+RUN_ID+'/fcov/seed-{seed}/frozen-config.json',
            author_contract='outputs/runs/'+RUN_ID+'/vo2/frozen-config.json'),
        artifacts=dict(delivery='paper/paper_revision_20260926_core/README.md',
            result='outputs/runs/'+RUN_ID+'/result.json',
            closeout='docs/experiment/2026-09-26-core-revision-vo2-bridge-closeout.md',
            coverage_scores='outputs/runs/'+RUN_ID+'/fcov-scoring/results.json',
            standalone='paper/paper_revision_20260926_core/evidence/standalone/independent-verification.json'))
    manifest=complete_manifest(manifest)
    manifest_path=ROOT/'docs/experiment/manifests'/f'{RUN_ID}.json';save(manifest_path,manifest)
    closeout=f'''# {TASK} 收口

**VERIFIED：**批准范围已完成。{fact} 原始 A/B、严格双周期与参考／读出口径不变。

五工况作者模型完成两步长 300,000 系统步，保留未对齐波形、峰时、峰高、末态和历史。定量实验复现为 UNKNOWN；双器件抑制 B 的低幅调制与测量支路未知不隐藏。

独立复算九类范围通过，原仓库访问被禁止；GPU 回收核验后及时关闭。稿件及补充来自同一 Markdown 文本体系，DOCX/PDF 完成版式检查。完整本地包不代替外部可访问性，P03 保持开放。

交付见[总入口](../../paper/paper_revision_20260926_core/README.md)；实际数值和成本见[运行记录](manifests/{RUN_ID}.json)。下一研究只交付待审有限观测重构计划；无新 pilot、Git 发布、公开数据或投稿。
'''
    (ROOT/'docs/experiment/2026-09-26-core-revision-vo2-bridge-closeout.md').write_text(closeout,encoding='utf-8')
    index=ROOT/'docs/experiment/index.jsonl';items=[json.loads(line) for line in index.read_text(encoding='utf-8').splitlines() if line.strip()]
    if any(x['run_id']==RUN_ID for x in items):raise RuntimeError('Closeout already indexed; do not duplicate')
    keys=('case_id','claim_status','execution_status','gate','gate_outcome','method_id','numerical_validity','replay_of','route_disposition','run_id','scientific_role','seed','split_id','tier')
    row={k:manifest[k] for k in keys};row['manifest']='manifests/'+RUN_ID+'.json'
    with index.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n')
    index_md=ROOT/'docs/experiment/INDEX.md';body=index_md.read_text(encoding='utf-8')
    columns=('run_id','tier','scientific_role','gate','method_id','case_id','seed','execution_status','gate_outcome')
    body=body.rstrip()+'\n| '+' | '.join(str(manifest[k]) for k in columns)+f' | [manifests/{RUN_ID}.json](manifests/{RUN_ID}.json) |\n'
    index_md.write_text(body,encoding='utf-8')
    for rel in ('README.md','active_phase.md','PROJECT_STATE.md','docs/plans/NEXT_ACTIONS.md'):
        path=ROOT/rel;text=path.read_text(encoding='utf-8');prefix='../../' if rel.startswith('docs/') else ''
        block=f'''<!-- CORE26_CURRENT_BEGIN -->
# 当前：现稿补强与 VO2 作者模型任务已完成

`{TASK}` 已完成批准范围。两条 F_cov 有效终点、五工况两步长、完整复算包和修订稿已交付，GPU 已回收核验并关闭。{fact}

见[交付入口]({prefix}paper/paper_revision_20260926_core/README.md)和[收口记录]({prefix}docs/experiment/2026-09-26-core-revision-vo2-bridge-closeout.md)。下一研究仅有待审有限观测重构计划，未授权执行。P02、严格双周期、材料／泛化与 P03 外部访问保持开放；未进行 Git 发布、数据公开或投稿。本段 supersedes 下方历史任务的当前状态，旧证据保留。

- `phase_id`: `PHK_V23_CORE_REVISION_VO2_BRIDGE`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VERIFIED_CORE_REVISION_WITH_BOUNDED_INTERPRETATION`
- `next_research_execution_authorized`: `false`

<!-- CORE26_CURRENT_END -->'''
        text,n=re.subn(r'<!-- CORE26_CURRENT_BEGIN -->.*?<!-- CORE26_CURRENT_END -->',lambda m:block,text,flags=re.S)
        assert n==1
        if rel=='docs/plans/NEXT_ACTIONS.md':
            text=text[:text.index('<!-- CORE26_CURRENT_END -->')+len('<!-- CORE26_CURRENT_END -->')]+f'''

当前无继续训练或新 pilot 授权。下一次审查仅围绕[有限观测重构计划]({prefix}paper/paper_revision_20260926_core/next-research-plan.md)中尚未闭合的测量支路、参数、初态及二维热合同。待用户审查后再形成具体执行授权，不自动展开新路线。

[上一计划历史]({prefix}archive/2026-09-26-pre-core-revision-next-actions.md)。
'''
        path.write_text(text,encoding='utf-8')
    print('DELIVERABLES_RECORDED; RUN_DOCUMENT_CONSISTENCY_BEFORE_HANDOFF',flush=True)

if __name__=='__main__':main()
