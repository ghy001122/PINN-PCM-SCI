"""Close only this task's live marker after final paper and numerical delivery."""
from pathlib import Path
import json,re,sys
from datetime import datetime,timezone

PAPER=Path(__file__).resolve().parent
ROOT=PAPER.parents[1]
RUN=ROOT/'outputs/runs/20260929-joint-reconstruction'
sys.path.insert(0,str(ROOT))
from pinn_pcm_sci.ledger import RunManifest,ExperimentLedger
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')

def main():
    for stem in ['manuscript','supplement']:
        for ext in ['md','docx','pdf']:assert (PAPER/(stem+'.'+ext)).stat().st_size>1000
    assert read(RUN/'shutdown.json')['confirmed']
    assert read(PAPER/'scoring-subset/independent-verification.json')['status']=='PASS'
    assert not read(RUN/'seed-29-gate.json')['trigger_seed43']
    assert 'in progress' not in (PAPER/'source/joint-result-section.md').read_text(encoding='utf-8')
    now=datetime.now(timezone.utc).isoformat()
    block='''<!-- JOINT72_CURRENT_BEGIN -->
# 当前：72小时成稿与联合重构已收口

PCM-20260929-72H-MANUSCRIPT-JOINT-01完成授权范围：连续二维主稿与完整S1—S25补充由单一源构建；固定N/F/S联合原型的接受终点、共同读出、分项门和独立复算全部交付。见[交付入口]({prefix}paper/paper_revision_20260929_72h/README.md)。

VERIFIED：N/F/S完整电流联合RMS为116.823/102.533/171.691 μA。N比F差13.94%，比S低31.96%但热非劣失败；首轮联合门未过，seed43未触发。N/F各600 Adam+100 L-BFGS评价，S187评价后Wolfe失败回滚至第75接受步；不称收敛。GPU结果已回收核验、实例已成功关闭。独立包指标算术容差通过，科学布尔门及计数一致。

SUPPORTED_INTERPRETATION：本次固定辅助神经消元原型未建立所需联合增量，原二维E/F和E/F_cov配置证据不变。UNKNOWN：普遍算法、formal OOD、实验/材料验证。P02/P03及严格双周期等旧未闭合项保持开放。唯一下一动作是作者终审及数据访问安排，无自动新训练或路线；本轮无Git发布、数据公开、邮件或投稿。关机后稿件/评分包待下次已授权实例会话同步，不为小文件重启GPU。

- `phase_id`: `PHK_V23_72H_MANUSCRIPT_JOINT_RECONSTRUCTION`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VERIFIED_BOUNDED_JOINT_INCREMENT_NOT_ESTABLISHED`
- `next_research_execution_authorized`: `false`

<!-- JOINT72_CURRENT_END -->'''
    for name in ['README.md','active_phase.md','PROJECT_STATE.md','docs/plans/NEXT_ACTIONS.md']:
        p=ROOT/name;content=p.read_text(encoding='utf-8');prefix='../../' if name.startswith('docs/') else ''
        updated,n=re.subn(r'<!-- JOINT72_CURRENT_BEGIN -->.*?<!-- JOINT72_CURRENT_END -->',lambda m:block.format(prefix=prefix),content,count=1,flags=re.S)
        assert n==1,name
        if name=='docs/plans/NEXT_ACTIONS.md':
            updated=updated[:updated.index('<!-- JOINT72_CURRENT_END -->')+len('<!-- JOINT72_CURRENT_END -->')]+'\n\n本轮执行已结束。请作者按终审清单核对；新研究、发布或投稿需新的明确指令。\n'
        write(p,updated)
    closeout='''# 72小时成稿与固定联合重构收口

任务 `PCM-20260929-72H-MANUSCRIPT-JOINT-01` 已完成。二维主体保持，P/CS/条件热证据压入补充S25；主文6.3保留紧凑说明并加入真实联合原型结果。完整权威Markdown、PDF、DOCX、逐页视觉核验、作者清单和主张—源表映射一并交付。

VERIFIED：N/F/S的共同RC电流RMS为116.822960/102.532716/171.690634 μA；T RMS为0.576409/0.577604/1.327032 K；热缺陷RMS为0.433365/0.482072/0.231736 mW。N/F电流与观测门失败，N/S热门失败；没有触发seed43。N/F各600 Adam+100 L-BFGS完整评价；S在187评价/75接受步后Wolfe线搜索失败回滚，所有终点和停止记录保留。

完整历史和RC梯度准入通过，三者零修正场一致；首步前平台舍入和cgroup工程修复有原始记录。完整源只在三端点锁定后评分读取。独立NumPy子集在仓库外、拒绝访问原科研文件的条件下实际复算通过，缺输入明确失败；这不代表神经AD重算或独立重训。

GPU产物已回收、传输和读取核验通过；08:05 UTC关机命令成功，SSH拒绝连接确认。本地评分和最终文稿待下一获准实例会话同步。只清理本轮核验后的两个冗余传输包，不删除科研NPZ/PT或历史不利证据。

SUPPORTED_INTERPRETATION：固定辅助神经消元原型没有建立预期联合增量，论文完整收口不依赖阳性结果。UNKNOWN：普遍方法增量、材料验证、formal OOD。旧二维P02/P03和严格双周期等问题不自动关闭。唯一下一动作是作者终审及审稿/数据获取安排；无新增科研、Git发布、公开数据、邮件或投稿授权。

见[稿件入口](../../paper/paper_revision_20260929_72h/README.md)、[结果报告](../../paper/paper_revision_20260929_72h/results-report.md)、[独立评分](../../paper/paper_revision_20260929_72h/scoring-subset/README.md)、[运行清单](manifests/20260929-joint-reconstruction.json)。
'''
    write(ROOT/'docs/experiment/2026-09-29-joint-reconstruction-closeout.md',closeout)
    p=ROOT/'docs/experiment/README.md';text=p.read_text(encoding='utf-8')
    prior='最新：[条件热响应与迟滞本构闭合]'
    text=text.replace(prior,'历史：[条件热响应与迟滞本构闭合]',1)
    marker='最新：[72小时成稿与联合重构](2026-09-29-joint-reconstruction-closeout.md)。固定三端点未过联合门，完整稿件与独立复算完成；GPU已回收关闭，无新科研授权。\n\n'
    if marker not in text:text=text.replace('# Experiment ledger protocol\n\n','# Experiment ledger protocol\n\n'+marker,1)
    write(p,text)
    manifest=dict(task_id='PCM-20260929-72H-MANUSCRIPT-JOINT-01',baseline=read(RUN/'config.json')['baseline'],closed_utc=now,
        status='CLOSED',scientific_claim='VERIFIED_BOUNDED_JOINT_INCREMENT_NOT_ESTABLISHED',
        manuscript_root=str(PAPER.relative_to(ROOT)).replace('\\','/'),run_root=str(RUN.relative_to(ROOT)).replace('\\','/'),
        configuration='config.json',admission='admission.json',accepted_endpoints='seed-29/*/checkpoint.pt',
        full_native_fields='seed-29/*/endpoint.npz',scores='seed-29-results.json',increment='seed-29-gate.json',
        exact_runtime='actual-runtime-manifest.json and runtime-source/',costs='seed-29-locked.json',
        independent_score='paper/paper_revision_20260929_72h/scoring-subset/independent-verification.json',
        recovery='recovery.json',shutdown='shutdown.json',second_seed_started=False,
        remote_post_shutdown_delivery_sync='PENDING_NEXT_AUTHORIZED_SESSION',publication=False,next_research_authorized=False)
    write(RUN/'closeout.json',json.dumps(manifest,indent=2)+'\n')
    ledger_path=ROOT/'docs/experiment/manifests/20260929-joint-reconstruction.json'
    ledger_manifest=RunManifest(
        run_id='20260929-joint-reconstruction',experiment_group_id=manifest['task_id'],tier='development',
        scientific_role='ONE_COMMON_START_NEURAL_SOFT_SPLINE_JOINT_RECONSTRUCTION',
        gate='CURRENT_10_PERCENT_AND_10UA_WITH_SEPARATE_T_OBSERVATION_HEAT_5_PERCENT_NI',
        started_at=read(RUN/'config.json')['started_utc'],ended_at=read(RUN/'seed-29-locked.json')['locked_utc'],
        command=['python','scripts/run_vo2_joint_sprint.py','train','--device','cuda:0','--seed','29'],
        execution_status='COMPLETE_BOUNDED_ACCEPTED_ENDPOINTS',
        numerical_validity='GRADIENT_ADMISSION_PASS_THREE_ACCEPTED_STATES_S_WOLFE_STOP_ROLLED_BACK',
        gate_outcome='JOINT_INCREMENT_NOT_ESTABLISHED_SEED43_NOT_TRIGGERED',
        route_disposition='CLOSED_AUTHOR_REVIEW_ONLY_NO_NEW_RESEARCH',
        evidence_identity='ONE_INSPECTED_DEVELOPMENT_CASE_ONE_NEURAL_SEED_ONE_DETERMINISTIC_SPLINE',
        claim_status=manifest['scientific_claim'],
        code_identity=dict(baseline=manifest['baseline'],runtime_manifest=manifest['run_root']+'/actual-runtime-manifest.json',source_archive=manifest['run_root']+'/runtime-source'),
        environment=read(RUN/'environment.json'),
        physical_contract_id='PINNED_AUTHOR_SI_PAIR_EULER_0P5NS_FULL_HISTORY',
        split_id='PAIR_EXCITATION_197_VOLTAGES_SOURCE_STATE_SCORING_ONLY_AFTER_LOCK',
        method_id='N_DYN_F_DYN_S_DYN_SAME_INITIAL_FIELD_DISCRETE_RC_COMMON_READOUT',
        case_id='PAIR_EXCITATION_11V_9P4V_ETA0P12_20US',seed=29,
        planned_budget=dict(first_neural_adam=1200,first_neural_lbfgs_evaluations=200,spline_lbfgs_cap=700,conditional_seed43_neural_adam=1200,conditional_seed43_neural_lbfgs=200),
        actual_budget=read(RUN/'cost-summary.json'),
        checkpoint=dict(path=manifest['run_root']+'/seed-29',kind='accepted_FP64_models_optimizer_histories_full_native_endpoint_arrays'),
        evaluator_id='NATIVE_TRAPEZOID_TWO_DEVICE_CURRENT_RMS_AND_ORIGINAL_DISCRETE_THERMAL_RC',
        artifacts=dict(delivery=manifest['manuscript_root']+'/README.md',report=manifest['manuscript_root']+'/results-report.md',
            config=manifest['run_root']+'/config.json',scores=manifest['run_root']+'/seed-29-results.json',
            independent_score=manifest['independent_score'],recovery=manifest['run_root']+'/recovery.json',shutdown=manifest['run_root']+'/shutdown.json'),
        failure_class='S_WOLFE_LINE_SEARCH_STOP_ACCEPTED_STATE_RETAINED_AND_JOINT_SCIENTIFIC_GATE_FAIL',replay_of=None,supersedes=None)
    # A prior, unindexed closeout draft is local bookkeeping, not a finalized
    # scientific manifest. Register the completed task with the existing API.
    if ledger_path.exists() and read(ledger_path).get('schema_version')=='run-manifest-v1':
        ledger_manifest=RunManifest(**read(ledger_path))
    else:write(ledger_path,json.dumps(ledger_manifest.to_dict(),indent=2,sort_keys=True)+'\n')
    ExperimentLedger(ROOT/'docs/experiment').record(ledger_manifest)
    print('Task closeout written; run document consistency gate next')

if __name__=='__main__':main()
