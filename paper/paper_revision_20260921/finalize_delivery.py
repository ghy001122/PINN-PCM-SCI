"""Close this bounded campaign after actual scoring and complete visual review."""
from datetime import datetime, timezone
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
REL='outputs/runs/20260921-b1-second-cycle-phase-gap'
RUN=ROOT/REL

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,text):path.write_text(text,encoding='utf-8')

def execution_times():
    entries=[]
    for line in (RUN/'cloud-run.log').read_text(encoding='utf-8').splitlines():
        try:entries.append(json.loads(line))
        except json.JSONDecodeError:pass
    started=next(x['started_utc'] for x in entries if x.get('stage')=='train')
    ended=next(x['finished_utc'] for x in reversed(entries) if x.get('gpu_sequence_exit')==0)
    return started,ended

def main():
    s=read(HERE/'evidence/b1-summary.json')
    closure=read(RUN/'compute-closure.json')
    qa=read(HERE/'evidence/visual-qa.json')
    assert s['status']=='COMPLETE_B1_SCORED_AND_RECOVERED'
    assert closure['training_and_readout_complete'] and closure['instance_shutdown_confirmed']
    assert qa['status']=='ALL_PAGES_VISUALLY_REVIEWED'
    started,ended=execution_times()
    elapsed=(datetime.fromisoformat(ended)-datetime.fromisoformat(started)).total_seconds()/60
    recovery_to_stop=(datetime.fromisoformat(closure['shutdown_requested_utc'])-datetime.fromisoformat(ended)).total_seconds()/60
    count=s['counts'];n=s['A_w_passed'];route=s['scientific_route']
    costs=sum(x['outside_cost'] for x in s['primary_comparisons'])
    phase=s['window_relative_effect_ranges']['Ephi']
    strict=s['strict_across_all_references_and_readers']
    fact=f"E/D_E的完整A_w通过{n}/12项参考／读出／seed检查；独立初始化只有两个。相态RMS相对改善范围为{100*phase['min']:.3f}%至{100*phase['max']:.3f}%；负值表示E误差更大。窗外非劣代价出现在{costs}/12项检查。"
    strict_text=('没有B1对象在三参考、双读出下稳定通过完整严格双周期门。' if not strict else
                 '三参考、双读出下稳定通过严格双周期门的对象：'+', '.join(strict)+'。')
    if not any(flag for values in s['strict_by_reference'].values() for flag in values.values()):
        strict_text='全部七个B1对象在每个参考／读出条件下均未通过完整严格双周期门。'
    if n==12:
        interpretation='支持这一离线缺测条件中的残差包增量；若伴随窗外代价，只能作为局部收益与代价的取舍。不能归因于单独相态方程、潜热项或某条梯度。'
        next_action='唯一下一步：由作者确定期刊定位、真实作者声明及完整数据访问方式，再进行对应投稿适配。该条件性结果不保证目标档次，不授权新增科研或自动发布。'
    else:
        interpretation='未建立对两个seed、三参考和双读出都稳定的额外动态残差增量；保留各项连续收益与失败，不能将不同条件的优点拼接成完整成功。'
        next_action='唯一下一步是作者作论文路线决策：以现有配置收益和条件性消融形成较窄的方法评估稿，或另立具有实质新方法贡献的研究任务。建议先据本轮完整证据评估较窄成稿的可投性；若继续以更强方法创新为目标，应单独设计并批准新任务。本轮不自动降级原研究目标，也不追加救援训练。'
    work=f"实际{count['adam']:,}次Adam、{count['complete_evaluations']:,}次完整目标／梯度评估；训练正解／伴随{count['training_forward_solves']:,}/{count['training_adjoint_solves']:,}，校准正解／伴随{count['calibration_forward_solves']:,}/{count['calibration_adjoint_solves']:,}，共同读出3,892次正解、0伴随。零新增支持／参考轨迹。"
    work+=f" 科研训练／读出序列实际耗时{elapsed:.2f}分钟；结束后完成打包、传输与校验，并在{recovery_to_stop:.2f}分钟时请求关机。前者不是平台计费时长。"
    head=f'''# 2026-09-21 B1冲刺与完整修订交付

任务 `PCM-20260921-FINAL-SPRINT-B1-01` 的阶段0—4已完成。**VERIFIED：**两个新父态、六个固定终点、七对象双读出和42条基本评分均已完成，证据已回收，本轮GPU实例已关闭。结果路由为 `{route}`。

**VERIFIED：**{fact} {strict_text}

**SUPPORTED_INTERPRETATION：**{interpretation} 原有四组E/F器件收益、全标签D_E反例、B_E连续排序反例及历史strict结论保持原身份。

正文 [PDF](manuscript.pdf)／[可编辑稿](source/manuscript.md)，补充 [PDF](supplement.pdf)／[可编辑稿](source/supplement.md)，统一[图件](figures/)与[书目](references.bib)。所有页面已实际渲染和视觉检查，页数与问题修正见[视觉记录](evidence/visual-qa.json)。

[P01—P06响应](revision-response.md)、[完整主张矩阵](claim_evidence_matrix.md)、[实际复现说明](data-and-reproduction.md)、[全部B1指标](evidence/b1-complete-results.json)、[主判据表](tables/b1-primary-decisions.md)、[完整事件](tables/b1-all-events.csv)、[有符号分脉冲能量](tables/b1-signed-pulse-energy.csv)、[端口轨迹索引](tables/b1-port-trace-index.csv)、[实际训练成本](tables/b1-training-and-calibration-work.csv)与[读出成本](tables/b1-readout-work.csv)。

{work} 用户明确取消费用上限，但冻结科学配方及次数上限保持。环境为Tesla V100-PCIE-32GB、Python 3.11.9、PyTorch 2.5.1+cu118、NumPy 2.1.1、SciPy 1.14.1；费用未虚估。回收与关机证据见[evidence/b1-compute-closure.json](evidence/b1-compute-closure.json)。

核心旧结果72记录、8,868项比较按原容差复算通过；负续训扩展18条保留历史结果，未宣称本轮重新评分。新增B1包先携带化再首次统一评分，42记录不是42次独立训练。完整数组仍本地保存，未公开、未分配DOI，未执行Git发布或投稿。

{next_action}

## 冻结实施信息与准备记录

以下准备记录保留既定数据边界和配方。`preparation-status.json`、`prepared.json`是阶段0—2历史快照；当前执行状态以本页、终点锁定、读出清单及已完成评分为准。

'''
    old=(HERE/'README.md').read_text(encoding='utf-8')
    frozen=old.split('## B1冻结信息与实现检查',1)[1].split('## 已测试解析、尚未执行的阶段3/4命令',1)[0]
    write(HERE/'README.md',head+'## B1冻结信息与实现检查'+frozen)
    response=f'''# P01—P06逐项响应：完整冲刺交付

任务 `PCM-20260921-FINAL-SPRINT-B1-01`。实际科学结果路由：`{route}`。本记录 supersedes 阶段0—2的待执行状态；旧稿和历史科学记录均保留。

| 问题 | 当前状态 | 实际修改与证据 | 未关闭边界 |
|---|---|---|---|
| P01 实际任务与监督 | 部分关闭 | 正文第1、3.7、5节明确86,625个原标签和逐协议离线重建；新增完整第二周期φ缺测，V/T和窗后φ可见；实际42记录见完整结果。 | 仍是合成已知模型，不能称最少传感器、无内部监督正向求解、零样本或材料实验验证。 |
| P02 方法增量与创新 | 条件证据已裁定；创新性仍有限 | 正文前置D_E匹配定义、全标签负结果和B1全部结果；{fact} | {interpretation} 经典电学消元不构成新算法；adapter/gate稳定独立贡献仍未建立。 |
| P03 复现与访问 | 本地评分闭合；外部待决定 | 核心72记录8,868项比较通过rtol=2e-10/atol=2e-12和精确布尔检查；B1携带化输入首次评分42记录；六臂负续训扩展保留18历史记录。 | 同代码保存数组运算不是独立实现或从零复现；外部地址、许可、权限和持久归档尚未批准。 |
| P04 B_E连续反例 | 已修正 | 正文4.2与完整精度六行CSV说明原协议43／细读出中E在原与时间参考下略差、空间参考下略好但未跨优势门。 | 原布尔裁决未变，不影响独立的四组E/F主结果；不凭显示值重判。 |
| P05 初边值相容 | 核查与解释已修正 | 正文2.2保留底部外法向导数−0.12 exp(−0.72)及十二个历史全标签固定池不含t=0边界节点的检查，区分精确IC、离散无通量和软BC罚。 | 非相容对方法排序的定量影响仍为UNKNOWN；没有改变对象或追加仿真。 |
| P06 结构与呈现 | 本轮修订完成 | 正文按问题、物理、匹配方法、主结果、缺测／反例、数值范围重排；真实二维T/φ/q图包含所有种子；指定近邻元数据、Allen–Cahn DOI和版本指代已修正；全部PDF页面视觉检查。 | 作者事实、目标期刊格式和最终作者审核仍须完成；内部检查不等于同行评审。 |

**VERIFIED：**{work} {strict_text} GPU证据回收与关机已完成，参考评分在关机后进行。详细计数、字段统计、端点和读出身份由[交付入口](README.md)及[复现说明](data-and-reproduction.md)直达。

**SUPPORTED_INTERPRETATION：**{interpretation}

**UNKNOWN：**材料有效性、连续体误差、严格事件普适能力和目标期刊接受概率。P01/P02不因写出局限性而自动全部关闭。

{next_action}

本轮未重开旧D_E、参考细化或stress；未新增seed、调权、救援分支或B2/B3；未commit、push、PR、完整数据公开或DOI分配。
'''
    write(HERE/'revision-response.md',response)
    matrix=(HERE/'claim_evidence_matrix.md').read_text(encoding='utf-8')
    matrix=matrix.replace('B1 has no trained endpoints at this stage.',f'B1 is complete with route {route}; all six endpoints and fourteen readers are locked.')
    matrix=matrix.replace('VERIFIED prior failures; strict two-cycle robustness not established.',
                          'VERIFIED historical failures; the historical endpoints do not establish strict two-cycle robustness.')
    matrix=matrix.replace('actual final counts in preparation report.',
                          '72 core records reproduced and 42 B1 records first scored; exact actual counts and commands in data-and-reproduction.md.')
    rows=matrix.splitlines()
    for i,line in enumerate(rows):
        if line.startswith('| Conditional B1 question |'):
            rows[i]='| Conditional B1 question | VERIFIED: the prescribed missing-phase observation condition has been tested. | Two fresh parents, six fixed branches, one legal interpolant; complete window/outside/full measures and unchanged event rules. V/T and post-window phase remain visible. |'
        elif line.startswith('| B1 scientific outcome |'):
            rows[i]=f'| B1 scientific outcome | VERIFIED: A_w passes {n}/12 conditions; SUPPORTED_INTERPRETATION: {route}. | Only two independent initializations. {costs}/12 comparisons have outside costs. No reference/reader-stable increment is established unless all declared conditions pass; no isolated phase-equation or gradient causation. Complete results: evidence/b1-complete-results.json. |'
    matrix='\n'.join(rows)+'\n'
    write(HERE/'claim_evidence_matrix.md',matrix)
    repro=(HERE/'data-and-reproduction.md').read_text(encoding='utf-8')
    repro=repro.replace('# Fixed-array reproduction and B1 staging',
                        '# Fixed-array reproduction and completed B1 delivery',1)
    start=repro.index('## New B1: not yet executed')
    end=repro.index('## Access and licensing boundary',start)
    b1=f'''## Completed B1: training, readout and first array score

The actual fixed run is `{REL}`. It contains both `seed-29/parent.pt` and `seed-43/parent.pt`, all six `E`, `D_E`, `F_raw` checkpoint/terminal pairs, their optimizer and work records, the visible training data, frozen configuration, calibration and pools. `all-endpoints-locked.json` and `readout-manifest.json` bind all accepted endpoints and fourteen readers. The runtime source bundle is `outputs/b1-runtime-20260921.tar.gz`; `deployment.json` records its already verified transfer identity. No old trained state or reference array was uploaded. The detached launch survived an SSH-client timeout; it was verified in progress and never relaunched. After successful scientific completion, the local recovery monitor required a parser correction for an exit-code file without a trailing newline. Four isolated format checks passed, and only packaging, transfer and shutdown resumed; no scientific computation was repeated.

Actual GPU commands used Python `/root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python` from `/tmp/pinn-b1-20260921`:

```text
python -u -m pinn_pcm_sci.phk_v23_b1 train --device cuda:0 --approval {REL}/resource-approval.json
python -u -m pinn_pcm_sci.phk_v23_b1 readout --device cuda:0 --approval {REL}/resource-approval.json
```

These commands describe completed execution, not authorization to rerun. The runner refuses an existing scientific trajectory. Exact versions are Python 3.11.9, Torch 2.5.1+cu118, NumPy 2.1.1 and SciPy 1.14.1; FP64 and the frozen finite optimizer/solve caps were retained. The user explicitly removed monetary limits for this fixed work. No monetary charge is inferred. Recovered outputs were transfer-verified once, the actual GPU instance was shut down and extraction completed before local reference scoring.

The separately portable NumPy-only package is `outputs/submission-rescore-20260921/b1`. Its 28 prediction/port files use ordinary hard links locally; transferred copies materialize normal files. References, weights, ROI, mappings, normalizers, old full-history kernels and B1 interval kernels are inside that package. Its actual first scoring command from the repository root was:

```powershell
.\\.venv\\Scripts\\python.exe -I outputs/submission-rescore-20260921/b1/portable/score_b1.py --out outputs/submission-rescore-20260921/b1/first-score
```

For a transferred package, run `python -I portable/score_b1.py --out a-new-score-directory` inside its root. Existing outputs cannot be overwritten; missing inputs fail without regeneration. `first-score/results.json` and `expected-results.json` preserve the actual first 42-record result. This first B1 score is not presented as a second independent replication. Training-output `scoring/results.json` is an explicitly recorded copy of that same result, not another execution.

The full B1 record contains seven objects × three references × two readers, with 84 cycle rows, 126 interval records and 36 E/D_E, E/F, E/B_E comparisons. Native ports remain native; only fine V for the original guard is restricted. W, its two disjoint complementary segments and the full history each retain their own normalizers. Window-plus-outside unnormalized integrals reconstruct the full history. Complete full metrics agree with the inherited scorer at rtol=2e-10 and atol=2e-12 during the same score. No neural forward, electrical solve or reference generation occurs in array scoring.

The first score also saved all 42 complete port/error traces under `first-score/traces/`. `tables/b1-port-trace-index.csv` gives package-relative paths and fields. A final report-only export integrates those saved traces over the unchanged powered intervals [0,0.35] and [1.01,1.36], producing `b1-signed-pulse-energy.csv` (84 rows) and `b1-energy-summary.csv` (42 rows). Signed pulse sums agree with saved cumulative full-history errors, and their absolute normalized totals agree with the original energy scores at the inherited tolerances. No frozen score or decision is rewritten. Supplement Table S35 displays all seven spatial-reference/fine-reader objects, including cancellation.

## Rebuild the delivered figures and PDFs

Use the project Python with NumPy, Matplotlib and ReportLab 4.4.9. The following local commands were actually executed after completed scoring:

```powershell
.\\.venv\\Scripts\\python.exe paper/paper_revision_20260921/report_b1.py
.\\.venv\\Scripts\\python.exe paper/paper_revision_20260921/plot_physics.py
.\\.venv\\Scripts\\python.exe paper/paper_revision_20260921/assemble_manuscript.py
.\\.venv\\Scripts\\python.exe paper/paper_revision_20260921/prepare_document.py
.\\.venv\\Scripts\\python.exe paper/paper_revision_20260921/build_pdf.py
```

For typesetting the delivered editable sources without replacing editorial changes, run only the last two commands. Assembly recreates the initial complete source from the completed score and historical text; it is not necessary for normal source editing. Physical plotting reads saved native arrays at fixed times 0.27/1.28, evaluates only algebraic deposition when q is absent, and adds no model inference or linear solve. All final pages were rendered with Poppler and visually checked; see `evidence/visual-qa.json` for actual counts and corrections. Historical assets copied from the 18 September snapshot retain their source identity.

'''
    write(HERE/'data-and-reproduction.md',repro[:start]+b1+repro[end:])
    closeout=f'''# B1第二周期相态缺测与最终冲刺收口

任务 `PCM-20260921-FINAL-SPRINT-B1-01`，状态CLOSED。基线218bb66069da52b2ccfe9dd68ac519edbe4584d0；现有工作与旧结果保留，未进行Git发布。

**VERIFIED：**{fact} {strict_text} 结果路由 `{route}`，全部六分支与十四读出完成，42基本记录、84周期记录、126区间记录和36组匹配比较完整保留。

**SUPPORTED_INTERPRETATION：**{interpretation} 原四组E/F器件收益仍由其历史结果支持；全标签D_E负结果、B_E连续误差反例、历史strict与六臂负续训均未改写。

{work} 两个父态从零开始，只有可见φ进入数据、界面、父态和校准；预声明窗口、seed、权重、配方、ROI和阈值不变。成本与模型工作计数见[完整交付](../../paper/paper_revision_20260921/README.md)。

本轮GPU于 `{closure['shutdown_requested_utc']}` 请求关闭，恢复包校验通过后执行关机，当前连接拒绝确认见运行目录compute-closure.json；关机后才读取参考统一评分。零科学重启、零新参考、零stress。实际单价和费用未估造。

正文与补充PDF、可编辑源、完整物理图和全部表格已完成，逐页视觉检查见[记录](../../paper/paper_revision_20260921/evidence/visual-qa.json)。核心72记录同代码复算通过；负结果扩展18历史记录保留；B1新增42记录首次从可携带输入统一评分。完整本地数组尚未公开。

**UNKNOWN：**材料有效性、连续体误差、普适strict能力、创新性与目标期刊接受概率。详见[P01—P06响应](../../paper/paper_revision_20260921/revision-response.md)，P01/P02仍未全部关闭。

{next_action}
'''
    write(ROOT/'docs/experiment/2026-09-21-b1-phase-gap-sprint-closeout.md',closeout)
    finalize_ledger(s,closure,started,ended)
    state=f'''# 当前收口：B1第二周期相态缺测与论文修订

**VERIFIED：**{fact} {strict_text} 全部冻结科学工作与PDF逐页检查已完成，实际GPU已回收关闭。**SUPPORTED_INTERPRETATION：**{interpretation}

本段 supersedes 本轮执行中／准备待批状态；历史数值、授权和未执行措辞保留其原阶段身份。结果路由 `{route}`。交付与下一步见本仓库 `paper/paper_revision_20260921/README.md` 和 `docs/experiment/2026-09-21-b1-phase-gap-sprint-closeout.md`。

{next_action}

- `phase_id`: `PHK_V23_B1_SECOND_CYCLE_PHASE_GAP`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VERIFIED_B1_{route}`
- `next_research_execution_authorized`: `false`

'''
    for name in ('README.md','active_phase.md','PROJECT_STATE.md','docs/plans/NEXT_ACTIONS.md'):
        path=ROOT/name;text=path.read_text(encoding='utf-8')
        cut=text.index('\n# ',1)
        remaining=text[cut+1:]
        remaining=remaining.replace('## 当前：共同读出、干净PDE消融与投稿修订成果发布',
                                    '## 历史：共同读出、干净PDE消融与投稿修订成果发布',1)
        write(path,state+remaining)
    for name,prefix in (('CODEX_CONTEXT.md',''),('docs/README.md','../')):
        path=ROOT/name;text=path.read_text(encoding='utf-8')
        first,rest=text.split('\n',1)
        rest=rest.replace('## 当前：共同读出、干净PDE消融与投稿修订成果发布',
                          '## 历史：共同读出、干净PDE消融与投稿修订成果发布',1)
        notice=f"\n\n## 当前：B1有界冲刺已收口\n\n**VERIFIED：**{fact} GPU已回收关闭；新科研授权结束。当前[完整稿与证据]({prefix}paper/paper_revision_20260921/README.md)、[收口]({prefix}docs/experiment/2026-09-21-b1-phase-gap-sprint-closeout.md)和[当前阶段]({prefix}active_phase.md)取代下方历史入口的当前地位。\n"
        write(path,first+notice+rest)
    path=ROOT/'docs/experiment/README.md';text=path.read_text(encoding='utf-8')
    text=text.replace('最新：[完整新脉冲历史确认终局]', '历史2026-09-15：[完整新脉冲历史确认终局]',1)
    first,rest=text.split('\n',1)
    write(path,first+'\n\n最新：[B1第二周期相态缺测收口](2026-09-21-b1-phase-gap-sprint-closeout.md)。两个新父态、六终点与共同读出已完成；全部结果和代价保留，GPU已回收关闭。\n'+rest)
    print(json.dumps(dict(status='DELIVERY_AND_SCIENTIFIC_PHASE_CLOSED',route=route)))

def finalize_ledger(s,closure,started,ended):
    sys.path.insert(0,str(ROOT))
    from pinn_pcm_sci.ledger import ExperimentLedger,RunManifest
    deployment=read(RUN/'deployment.json')
    paths={str(seed):{role:f'{REL}/seed-{seed}/{role}/checkpoint.pt' for role in ('E','D_E','F_raw')} for seed in (29,43)}
    parents={str(seed):f'{REL}/seed-{seed}/parent.pt' for seed in (29,43)}
    for path in [*parents.values(),*(p for item in paths.values() for p in item.values())]:
        assert (ROOT/path).is_file(),path
    manifest=RunManifest(run_id='20260921-b1-second-cycle-phase-gap',experiment_group_id='PHK_V23_B1',
        tier='development',scientific_role='ONE_PRESCRIBED_PHASE_GAP_TWO_FRESH_MATCHED_INITIALIZATIONS',
        gate='A_W_WITH_UNCHANGED_FULL_A_B_AND_STRICT',started_at=started,ended_at=ended,
        command=['python -m pinn_pcm_sci.phk_v23_b1 train --device cuda:0 --approval '+REL+'/resource-approval.json',
                 'python -m pinn_pcm_sci.phk_v23_b1 readout --device cuda:0 --approval '+REL+'/resource-approval.json',
                 'python -I outputs/submission-rescore-20260921/b1/portable/score_b1.py --out outputs/submission-rescore-20260921/b1/first-score'],
        execution_status='COMPLETE',numerical_validity='SIX_VALID_FIXED_ENDPOINTS_AND_FOURTEEN_READERS',
        gate_outcome=s['scientific_route'],route_disposition='BOUNDED_CAMPAIGN_CLOSED_AUTHOR_ROUTE_DECISION',
        evidence_identity='TWO_INITIALIZATIONS_ONE_PHASE_OBSERVATION_GAP_EXISTING_PROTOCOL_OFFLINE_RECONSTRUCTION',
        claim_status='VERIFIED_B1_'+s['scientific_route'],
        code_identity=dict(base_commit='218bb66069da52b2ccfe9dd68ac519edbe4584d0',source_bundle=deployment['source_bundle'],
                           source_bundle_sha256=deployment['sha256'],published=False,training_sources_frozen=True),
        environment={**{k:deployment[k] for k in ('gpu_model','python','torch','numpy','scipy')},
                     'dtype':'float64','gpu_shutdown_confirmed':True,'reference_scoring_after_shutdown':True},
        physical_contract_id='UNCHANGED_PHK_V21_FINITE_TWO_PULSE_GAP_1P01',
        split_id='COMPLETE_SECOND_CYCLE_PHASE_WITHHELD_V_T_AND_POST_WINDOW_PHASE_VISIBLE',
        method_id='MATCHED_E_D_E_F_AND_VISIBLE_B_E',case_id='lf11-history-gap-1p01',seed=29,
        planned_budget=dict(adam=13800,complete_evaluations=3000,training_forward=108000,training_adjoint=108000,
                            calibration_forward=1000,readout_forward=3892,new_reference_steps=0),
        actual_budget={**s['counts'],'readout_forward':3892,'readout_adjoint':0,'new_reference_steps':0,
                       'seed_values':[29,43],'scientific_retries':0,'cost_policy':'USER_NO_COST_LIMIT'},
        checkpoint=dict(parents=parents,branches=paths,aggregate_seed_field=29,actual_seeds=[29,43]),
        evaluator_id='FROZEN_FULL_HISTORY_KERNELS_PLUS_B1_WINDOW_AND_DISJOINT_OUTSIDE',
        artifacts=dict(closeout='docs/experiment/2026-09-21-b1-phase-gap-sprint-closeout.md',
                       compute_closure=REL+'/compute-closure.json',endpoints=REL+'/all-endpoints-locked.json',
                       readers=REL+'/readout-manifest.json',score=s['score_source'],
                       paper='paper/paper_revision_20260921/manuscript.md'),
        failure_class=None,replay_of=None,supersedes=None)
    ExperimentLedger(ROOT/'docs/experiment').record(manifest)

if __name__=='__main__':main()
