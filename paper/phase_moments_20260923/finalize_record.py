"""Record this completed negative development screen; no scientific execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from pinn_pcm_sci.ledger import ExperimentLedger, RunManifest

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RUN=ROOT/'outputs/runs/20260923-relative-phase-moments'
ARMS=('D','P','L','R','I','RI','RIM','G')
ROUTE='NO_INCREMENT_WITHIN_SCREEN_BUDGET'
CLAIM='VERIFIED_PHASE_MOMENTS_NO_INCREMENT_WITHIN_SCREEN_BUDGET'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    scores=read(RUN/'scoring/results.json');end=read(RUN/'all-endpoints-locked.json')['arms']
    audit=read(RUN/'endpoint-audits.json');used=read(RUN/'endpoint-used-order-audit.json')
    closure=read(RUN/'compute-closure.json');deployment=read(RUN/'deployment-archive.json')
    assert scores['status']=='COMPLETE_EIGHT_ARM_DEVELOPMENT_SCORING'
    assert all(end[a]['status']=='VALID_FIXED_ENDPOINT' for a in ARMS)
    assert all(not v['A_w']['passed'] and not v['full']['A']['passed'] and not v['full']['B']['passed']
               for v in scores['comparisons'].values())
    assert all(not r['strict_device_pass'] for r in scores['records'].values())
    assert all(not any(v['outside_cost_flags'].values()) for v in scores['comparisons'].values())
    assert all(v['quadrature_pass'] for v in audit['arms'].values())
    assert all(v['all_targets_pass'] for v in used['arms'].values())
    assert closure['recovery_verified'] and closure['instance_shutdown_confirmed'] and closure['job_exit_code']==0
    summary='八臂数值有效且预算完整；所有候选均未对D和P建立原A_w增量。RIM相对D的W相态RMS改善1.918%、S改善2.202%；相对P分别改善2.264%、2.633%，低于原10%门。电热非劣与窗外代价不是此次失败原因。'
    discussion='''### 科学裁决与机制边界

**VERIFIED：**56个有序内部比较的A_W、全轨迹A及B均无通过；这些比较不是56个独立样本。八个终点均未通过原严格双周期门。所有有序比较的七项窗外代价标志均为false，原非劣标准没有被放宽。

**VERIFIED：**RIM相对RI的S／Ephi改善仅0.187%／0.295%，相对简单完整logit控制L仅0.054%／0.139%，相对固定标量G为0.703%／0.718%。R相对L的S／Ephi反而增加2.589%／2.045%。RI相对R存在约2.394%／1.851%的连续改善，但仍未建立主门增量。I相对P的变化也很小。保留全部连续差异，不把它们称为显著性或模块必要性证据。

**SUPPORTED_INTERPRETATION：**本次固定预算没有支持完整组合、一阶矩、有限截断或相态度量的独立方法贡献。L和G都能获得与完整候选接近的小幅变化。这里不选择STATE_METRIC_ONLY_SIGNAL或GENERIC_INTEGRAL_OR_SCALAR_SUFFICIENT，因为没有候选先满足对D/P的原主问题。完整候选在W的S与Ephi数值最小也不足以触发确认。

### 剩余误差在哪里

**VERIFIED：**RIM第二周期onset为1.22715，原参考1.2268，时差0.00035；recovery=1仍通过。其recall=0.641734、precision=0.824945、mass ratio=0.777911，事件覆盖不足。活跃面积峰值出现在1.5425，原参考为1.3475；峰值时差0.195不等于原onset时差。RIM的W集合误差约78.24%来自加热结束后的FP；八臂该份额为78.24%—79.76%。不能因onset接近而宣称相态重建或严格事件能力成立，也不能把通过的恢复指标改写成失败。

**VERIFIED：**RIM独立原raw审计的热项／相态项为0.00611736／0.00300684。相对D分别变化−1.690%／+0.450%；相对P为+0.505%／+0.586%。这些是原尺度下的残差平方诊断，未新增一个事后物理成功阈值。

**SUPPORTED_INTERPRETATION：**初始phase损失占比很小，且短片上Mζ与Pζ已很接近，可以解释为什么本轮模块变化有限；这不是唯一优化根因的证明，也没有证明一般PINN、积分约束或更长预算都无效。

### 唯一后续动作

按预声明停止条件收口本轮，不追加训练、调权、片宽搜索、seed、第二读出或另外两参考复评分；没有触发阶段4确认申请。原论文的独立相态PDE贡献与严格事件能力仍未补齐。本轮不自动改写为D_E主导的窄稿。若继续追求更强方法创新，下一任务须提出真正不同且可区分的科学假设，并重新固定强控制、预期效应与停止条件；不能把本次失败简单改名或续跑。
'''
    effects={b:scores['comparisons']['RIM_vs_'+b]['continuous_effects']['window'] for b in ('D','P','L','R','I','RI','G')}
    decision=dict(task_id='PCM-20260922-RELATIVE-PHASE-MOMENTS-01',route=ROUTE,claim_status=CLAIM,
        summary_zh=summary,discussion_zh=discussion,independent_initializations=1,seed=29,
        primary_candidate='RIM',selected_candidate_for_confirmation=None,
        confirmation_triggered=False,confirmation_executed=False,further_training_authorized=False,
        scoring_reference='old',scoring_reader=[160,80],scientific_thresholds_unchanged=True,
        RIM_continuous_effects=effects,all_ordered_A_w_passes=0,all_ordered_full_A_passes=0,
        all_ordered_full_B_passes=0,strict_passes=0,outside_cost_flags=0,
        numerical_validity='EIGHT_VALID_ENDPOINTS_WITH_8_16_AND_16_32_AGREEMENT',
        compute_shutdown_confirmed=True,existing_B1_0_of_12_unchanged=True,
        created_utc=datetime.now(timezone.utc).isoformat())
    if (RUN/'decision.json').exists():raise FileExistsError('Decision already recorded')
    save(RUN/'decision.json',decision)
    total_minutes=sum(v['elapsed_seconds'] for v in end.values())/60
    lines=[json.loads(v) for v in (RUN/'cloud-run.log').read_text().splitlines() if v.startswith('{')]
    started=next(v['started_utc'] for v in lines if v.get('stage')=='train')
    stopped=next(v['finished_utc'] for v in lines if v.get('gpu_sequence_exit')==0)
    gpu_minutes=(datetime.fromisoformat(stopped)-datetime.fromisoformat(started)).total_seconds()/60
    recovery_minutes=(datetime.fromisoformat(closure['shutdown_requested_utc'])-datetime.fromisoformat(stopped)).total_seconds()/60
    actual=dict(adam=sum(v['adam_updates'] for v in end.values()),
        complete_training_evaluations=sum(v['lbfgs']['evaluations'] for v in end.values()),
        training_forward_solves=sum(v['statistics']['electrical']['forward_solves'] for v in end.values()),
        training_adjoint_solves=sum(v['statistics']['electrical']['adjoint_solves'] for v in end.values()),
        training_phase_derivative_positions=sum(v['statistics']['phase_work']['phase_derivative_positions'] for v in end.values()),
        training_phase_endpoint_queries=sum(v['statistics']['phase_work']['phase_endpoint_queries'] for v in end.values()),
        raw_audit_forward_solves=128,raw_audit_adjoint_solves=0,readout_forward_solves=2224,readout_adjoint_solves=0,
        parent_profile_passes_per_arm=2,parent_profile_forward_solves=768,parent_profile_adjoint_solves=768,
        endpoint_used_order_phase_derivative_positions=used['phase_derivative_positions'],
        endpoint_used_order_queries=used['phase_endpoint_coordinate_queries'],
        new_parents=0,new_support_solves=0,new_reference_solves=0,scientific_retries=0,
        training_minutes=total_minutes,gpu_sequence_minutes=gpu_minutes,
        minutes_from_gpu_work_end_to_shutdown_request=recovery_minutes,
        cost_policy='USER_NO_COST_LIMIT',calibration_interrupted_order32_partial_work='not fully metered; zero optimizer updates')
    save(RUN/'actual-work-summary.json',actual)
    closeout=f'''# 相对相态残差与时间矩八臂开发收口

任务 `PCM-20260922-RELATIVE-PHASE-MOMENTS-01`；run_id `20260923-relative-phase-moments`；状态CLOSED。

**{CLAIM} — {ROUTE}。** {summary}

八臂D/P/L/R/I/RI/RIM/G均从合法B1 seed29观测父态开始，只重置优化器；没有使用旧E/D_E终点。原二维电—热—相态模型、表示、可见观测、缺测窗、判据与参考全部保持。本轮只有一个初始化，不是确认或formal OOD。

{discussion}

## 完成的证据与资源

- 21项聚焦／继承测试通过；真实父态及固定制造场的8/16/32求积检查通过，统一采用8点。
- 八臂均600 Adam + 100完整L-BFGS评估；共4800/800。所有试探计入，预算中断按最后接受状态回滚，未追加科学重跑。
- 训练正解／伴随51,848／51,848；独立raw审计128／0；八个160×80原生读出2224／0。CPU父态profile两次／臂，另768／768；固定模型机制诊断两次／模型，无电学求解。
- 终点16/32以及回收后补充8/16均通过。补充检查使用相同固定池、原1%／5%数值容差、零更新、零参考、零电学求解；它补齐实际训练阶数的检查，未改变原评分门。8/16最大目标差异5.504e-8、梯度范数差异6.399e-7。
- 训练累计{total_minutes:.2f}分钟；完整GPU train/audit/readout序列{gpu_minutes:.2f}分钟。结束后打包传输校验耗时{recovery_minutes:.2f}分钟即请求关机；这不是平台计费时长。
- GPU于`{closure['shutdown_requested_utc']}`关闭，退出码0，SSH拒绝连接确认；结果包SHA256 `{closure['recovery_sha256']}`。关闭后才对新八臂统一参考评分。
- 本地32点校准进程中断与部署缺少依赖均在科研优化前解决；保留记录、没有科学轨迹重试。前者部分CPU导数工作未完整计量，不编造总CPU工作量。

旧B1 0/12、B_E反例、六臂负续训、初边值及材料解释边界保留。新结果全部本地保存；未commit/push/PR、未公开上传、未读取sealed stress。

完整交付：[结果、两幅主要科学图及全部数表](../../paper/phase_moments_20260923/results.md)、[历史定位／实现／来源与复现入口](../../paper/phase_moments_20260923/README.md)、[英文方法及结果工作段落](../../paper/phase_moments_20260923/method-and-claim-boundaries.md)、[运行目录](../../outputs/runs/20260923-relative-phase-moments)、[工作量](../../outputs/runs/20260923-relative-phase-moments/actual-work-summary.json)、[关机证据](../../outputs/runs/20260923-relative-phase-moments/compute-closure.json)。
'''
    (ROOT/'docs/experiment/2026-09-23-relative-phase-moments-closeout.md').write_text(closeout,encoding='utf-8')
    environment=read(RUN/'gpu-preflight.json')
    environment.update(dtype='float64',gpu_shutdown_confirmed=True,new_endpoint_reference_scoring_after_shutdown=True)
    rel='outputs/runs/20260923-relative-phase-moments'
    manifest=RunManifest(run_id='20260923-relative-phase-moments',experiment_group_id='PHK_V23_RELATIVE_PHASE_MOMENTS',
        tier='development',scientific_role='ONE_INITIALIZATION_EIGHT_MATCHED_PHASE_OBJECTIVES',
        gate='ORIGINAL_A_W_WITH_FULL_A_B_STRICT_RAW_AND_OUTSIDE_REPORTED_SEPARATELY',
        started_at=started,ended_at=datetime.fromtimestamp((RUN/'scoring/results.json').stat().st_mtime,timezone.utc).isoformat(),
        command=['python run_cloud.py','python -m pinn_pcm_sci.phk_v23_phase_moments_endpoint_check',
                 'python -m pinn_pcm_sci.phk_v23_phase_moments_evaluate'],
        execution_status='COMPLETE',numerical_validity='EIGHT_VALID_ENDPOINTS_EIGHT_READERS_8_16_32_AGREEMENT',
        gate_outcome=ROUTE,route_disposition='STOP_FROZEN_SCREEN_NO_CONFIRMATION_TRIGGERED',
        evidence_identity='SINGLE_REUSED_LEGAL_PARENT_SEED29_OFFLINE_PHASE_GAP_RECONSTRUCTION',claim_status=CLAIM,
        code_identity=dict(base_commit='192f9551692e7b1f63add946cc8fb77295818542',published=False,
            source_bundle='outputs/staging-phase-moments-20260923.tar.gz',source_bundle_sha256=deployment['sha256'],
            training_sources_frozen=True,local_endpoint_check_sha256=sha(ROOT/'pinn_pcm_sci/phk_v23_phase_moments_endpoint_check.py'),
            local_evaluator_sha256=sha(ROOT/'pinn_pcm_sci/phk_v23_phase_moments_evaluate.py')),
        environment=environment,physical_contract_id='UNCHANGED_PHK_V21_FINITE_TWO_PULSE_GAP_1P01',
        split_id='COMPLETE_SECOND_CYCLE_PHASE_WITHHELD_V_T_AND_POST_WINDOW_PHASE_VISIBLE',
        method_id='D_P_L_R_I_RI_RIM_G_SHARED_PHASE_PANELS',case_id='lf11-history-gap-1p01',seed=29,
        planned_budget=dict(adam=4800,complete_training_evaluations=800,training_forward_cap=51848,
            training_adjoint_cap=51848,readout_forward=2224,raw_audit_forward=128,new_parents=0,new_references=0),
        actual_budget=actual,checkpoint=dict(parent=read(RUN/'input-manifest.json')['parent'],
            branches={a:rel+'/'+a+'/checkpoint.pt' for a in ARMS}),
        evaluator_id='EXISTING_PORTABLE_READOUT_KERNELS_AND_ORIGINAL_B1_WINDOW_RULE',
        artifacts=dict(closeout='docs/experiment/2026-09-23-relative-phase-moments-closeout.md',
            results='paper/phase_moments_20260923/results.md',score=rel+'/scoring/results.json',
            decision=rel+'/decision.json',readers=rel+'/readout-manifest.json',endpoints=rel+'/all-endpoints-locked.json',
            raw_and_quadrature=rel+'/endpoint-audits.json',used_order_check=rel+'/endpoint-used-order-audit.json',
            compute_closure=rel+'/compute-closure.json'),failure_class=None,replay_of=None,supersedes=None)
    ExperimentLedger(ROOT/'docs/experiment').record(manifest)
    for name in ('active_phase.md','PROJECT_STATE.md','README.md','docs/plans/NEXT_ACTIONS.md'):
        p=ROOT/name;old=p.read_text(encoding='utf-8');marker='# 历史收口：B1第二周期相态缺测与论文修订'
        assert marker in old
        prefix='../../' if name.startswith('docs/plans/') else ''
        top=f'''# 当前：相对相态残差与时间矩开发已收口

**VERIFIED：**{summary} 全部八臂严格双周期未通过；16/32与补充8/16数值检查通过。GPU结果已回收并关机。完整事实见[本轮结果]({prefix}paper/phase_moments_20260923/results.md)与[实验收口]({prefix}docs/experiment/2026-09-23-relative-phase-moments-closeout.md)。本段supersedes本轮执行中状态；下方旧B1结论与发布记录保留历史身份。

**SUPPORTED_INTERPRETATION：**本轮没有建立独立相态目标或时间矩增量。按预声明条件停止，不追加确认、调权或训练，不自动转为D_E主导窄稿。原论文的相态PDE贡献与严格事件证据仍未补齐；不同科学假设须另立任务，当前无新增科研或Git发布授权。

- `phase_id`: `PHK_V23_RELATIVE_PHASE_MOMENTS`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `{CLAIM}`
- `next_research_execution_authorized`: `false`

'''
        p.write_text(top+marker+old.split(marker,1)[1],encoding='utf-8')
    for name,marker,prefix in [('CODEX_CONTEXT.md','# Codex 项目上下文',''),('docs/README.md','# 文档库地图','../')]:
        p=ROOT/name;old=p.read_text(encoding='utf-8');assert marker in old
        top=f'''# 当前：相对相态残差与时间矩开发已收口

**VERIFIED — {ROUTE}：**八臂单初始化开发完成，RIM相对D/P没有达到原A_w；全部严格双周期未过。数值检查通过，GPU已回收关闭。见[完整结果]({prefix}paper/phase_moments_20260923/results.md)、[收口]({prefix}docs/experiment/2026-09-23-relative-phase-moments-closeout.md)及[当前阶段]({prefix}active_phase.md)。阶段4未触发，新科研与Git发布均未授权；旧B1证据按历史身份保留。

'''
        p.write_text(top+marker+old.split(marker,1)[1],encoding='utf-8')
    p=ROOT/'CONTEXT.md';old=p.read_text(encoding='utf-8');marker='## 历史：同父三臂与条件归一化已完成';assert marker in old
    top=f'''# PINN-PCM-SCI 当前研究设定与论文口径

## 当前研究问题（2026-09-23收口）

**VERIFIED：**相对相态残差／时间矩八臂开发按{ROUTE}收口。RIM有小幅连续改善，但未对D/P通过原A_w；相对简单L、RI、G的变化不足以建立组合或一阶矩必要性。八个严格双周期均未通过；数值求积检查通过，GPU已关闭。见[完整结果](paper/phase_moments_20260923/results.md)。本轮仅一个初始化、离线相态缺测重建，不是forecasting、formal OOD或材料验证。

**SUPPORTED_INTERPRETATION：**当前固定校准与短片目标未补齐论文的独立相态PDE贡献；不自动改写为D_E窄稿。初始loss尺度和时间矩接近是诊断线索，不是已证明的唯一根因。旧完整标签E/F配置收益、B1 0/12、B_E反例、六臂负续训及材料边界仍保留原身份。后续不同假设需另行规划授权，当前不追加训练或确认。下文仅为历史口径。

'''
    p.write_text(top+marker+old.split(marker,1)[1],encoding='utf-8')
    p=ROOT/'docs/experiment/README.md';old=p.read_text(encoding='utf-8')
    entry='最新：[相对相态残差与时间矩八臂开发收口](2026-09-23-relative-phase-moments-closeout.md)。八个有效终点与原生读出完成，未建立原A_w增量；全部数值检查通过，GPU已回收关闭。\n\n'
    old=old.replace('最新：[B1','历史2026-09-21：[B1',1)
    p.write_text(old.replace('# Experiment ledger protocol\n\n','# Experiment ledger protocol\n\n'+entry,1),encoding='utf-8')
    method=HERE/'method-and-claim-boundaries.md';text=method.read_text(encoding='utf-8')
    text=text.replace('Status: **HYPOTHESIS under a frozen development screen**, not a confirmed improvement.',
        'Status: **VERIFIED bounded negative development result — NO_INCREMENT_WITHIN_SCREEN_BUDGET**. Independent method improvement was not established.')
    text+='''

## Completed development result

All eight fixed endpoints and native 160×80 readers completed, with 600 Adam updates and 100 complete L-BFGS evaluations per arm. RIM reduced missing-window phase RMS error by 1.918% and set error by 2.202% relative to D; the corresponding reductions relative to the matched raw control P were 2.264% and 2.633%. Neither comparison passed the original simultaneous 10% improvement criterion. The temperature/electrical noninferiority checks passed, and no outside-window cost flag was raised. All eight strict two-cycle tests failed.

RIM improved phase RMS by only 0.139% over L, 0.295% over RI and 0.718% over G. These one-initialization differences establish neither statistical significance nor the necessity of finite clipping or the first moment. The original phase-residual audit for RIM increased by approximately 0.450% relative to D and 0.586% relative to P. Both the prescribed endpoint 16/32 quadrature audit and a supplementary, pre-scoring 8/16 check passed; numerical invalidity is not the reason for the failed improvement gate.

For RIM, second-cycle onset error was 0.00035 and the original recovery fraction was 1, but recall, precision and active-mass ratio were 0.641734, 0.824945 and 0.777911. Its active-area peak occurred at 1.5425 instead of the reference 1.3475, and after-pulse false-positive area contributed 78.24% of its window set error. Near-correct onset therefore did not establish accurate phase evolution. These observations preserve the distinction between continuous reconstruction, limited electrical function and strict event capability.

The screen terminates without a confirmation candidate. The result is conditional on this physical proxy, observation condition, shared parent, fixed weighting, panel discretization and optimization budget. It does not establish that PINNs or interval residual methods are generally ineffective. The old B1 findings and full-label counterexamples remain separate evidence. See [complete tables and figures](results.md).
'''
    method.write_text(text,encoding='utf-8')
    print(json.dumps(dict(route=ROUTE,actual=actual),ensure_ascii=False))


if __name__=='__main__':main()
