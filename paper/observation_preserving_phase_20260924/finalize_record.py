"""Close this completed fixed campaign using only its saved evidence."""
from pathlib import Path
from datetime import datetime,timezone
import csv
import json
import os
import shutil

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
RUN=ROOT/'outputs/runs/20260924-observation-preserving-phase'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def write(p,s):Path(p).write_text(s.strip()+'\n',encoding='utf-8')
def relative(p,target):return os.path.relpath(target,Path(p).parent).replace('\\','/')

s=read(RUN/'scoring/results.json');a=read(RUN/'endpoint-audits.json');work=read(HERE/'evidence/actual-work-summary.json')
closure=read(RUN/'compute-closure.json');arms=('G','N','S');order=('B0','D_E',*arms)
assert all(s['records'][k]['valid'] for k in order)
assert all(not s['pairs'][k+'_vs_B0']['A_w']['passed'] for k in arms)
assert all(not a['arms'][k]['physical_completion']['passed'] for k in arms)
assert work['adam_updates']==1800 and work['complete_lbfgs_evaluations']==600
assert closure['recovery_verified'] and closure['instance_shutdown_confirmed']
route='NO_COMPLETION_INCREMENT'
ratio={k:{m:a['arms'][k]['D'][m]/a['arms']['B0']['D'][m] for m in
    ('phase_raw_mean_square','thermal_raw_mean_square','phase_BC_mean_square_original_denominator')} for k in arms}
dec=dict(task_id='PCM-20260924-OBSERVATION-PRESERVING-PHASE-01',route=route,
    status='VERIFIED_BOUNDED_NEGATIVE_DEVELOPMENT',independent_base_initializations=1,
    primary_reason='N reduces thresholded set error but increases raw phase RMS; N, G and S each fail original A_w against B0.',
    N_vs_base=s['pairs']['N_vs_B0'],N_vs_historical_D_E=s['pairs']['N_vs_D_E'],
    N_vs_G=s['pairs']['N_vs_G'],N_vs_S=s['pairs']['N_vs_S'],physical_ratios=ratio,
    physical_completion={k:a['arms'][k]['physical_completion'] for k in arms},
    all_ordered_A_w_passes=sum(p['A_w']['passed'] for p in s['pairs'].values()),
    all_ordered_full_A_passes=sum(p['full']['A']['passed'] for p in s['pairs'].values()),
    all_ordered_full_B_passes=sum(p['full']['B']['passed'] for p in s['pairs'].values()),
    strict_new_endpoint_passes=sum(s['records'][k]['strict_device_pass'] for k in arms),
    N_S_invariance_verified=True,original_thresholds_unchanged=True,reference='original only',native_reader=[160,80],
    numerical_status='VALID_FIXED_ENDPOINTS_WITH_RECORDED_CPU_DEVICE_DEVIATION',
    training_device='CPU; device argument omission preserved without restart',
    stage_4_triggered=False,new_scientific_execution_authorized=False,
    complete_native_arrays_local=True,complete_arrays_public=False,P02_closed=False,P03_closed=False,
    created_utc=datetime.now(timezone.utc).isoformat())
save(RUN/'decision.json',dec);save(HERE/'evidence/decision.json',dec)

historical=read(ROOT/'outputs/submission-rescore-20260921/b1/first-score/results.json')['records']['old']['coarse']
rows=[]
for key in ('shorter/29/F','shorter/B_E'):
    v=historical[key]
    rows.append(dict(id=key,scope='full',reference='original',native_reader='160x80',
        status='historical saved record; not rescored or cost-matched in this task',strict_device_pass=v['strict_device_pass'],**v['metrics']))
with (HERE/'historical-F-and-BE.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

metric_table='| 对象 | W相态RMS | 1000×集合误差 | RMS改善 | 集合改善 | 对B0的A_w |\n|---|---:|---:|---:|---:|---|\n'
for k in order:
    m=s['windows'][k]['window']['metrics']
    if k=='B0':gain=['—','—'];passed='基点'
    else:
        r=s['pairs'][k+'_vs_B0']['relative_reduction']['window'];gain=[f"{100*r[m]:.3f}%" for m in ('Ephi','S')]
        passed=str(s['pairs'][k+'_vs_B0']['A_w']['passed'])
    metric_table+=f"| {k} | {m['Ephi']:.9f} | {1000*m['S']:.6f} | {gain[0]} | {gain[1]} | {passed} |\n"
physics_table='| 臂 | D内raw相态平方/基点 | D内raw热平方/基点 | D内相态BC/基点 | 物理资格 |\n|---|---:|---:|---:|---|\n'
for k in arms:
    v=ratio[k];physics_table+=f"| {k} | {v['phase_raw_mean_square']:.6f} | {v['thermal_raw_mean_square']:.6f} | {v['phase_BC_mean_square_original_denominator']:.6f} | 未通过 |\n"
cost_table='| 臂 | 参数 | Adam/完整L-BFGS | CPU训练分钟 | 训练正解/伴随 |\n|---|---:|---:|---:|---:|\n'
for c in work['cost']:
    cost_table+=f"| {c['arm']} | {c['parameters']} | {c['adam_updates']}/{c['lbfgs_evaluations']} | {c['training_seconds']/60:.3f} | {c['forward_solves']}/{c['adjoint_solves']} |\n"

write(HERE/'results.md',f'''
# 观测保持相态补全：完整开发结果

**VERIFIED：{route}。** 阶段0—3已经完成；三个固定终点数值有效、预算完整，已按原参考和共同160×80读出统一评分。N/G/S均未相对冻结B1 E/29通过原A_w；全部20个有序比较的A_w、全程A和全程B通过数均为0。三个新终点严格双周期通过数为0。一个基础初始化和多个比较不构成独立重复。

**SUPPORTED_INTERPRETATION：**本轮证明了观测预测保持构造可以实现，但没有建立合格的相态补全增量。N对阈值集合的明显改善，伴随连续相态误差恶化和独立物理审计失败，不能作为方法成功。阶段4条件未触发，科研计算到此停止；不自动调参、加种子、扩窗、解冻T或改成传统方法主稿。

## 主比较

{metric_table}
改善为正表示误差下降，负值表示恶化。原A_w同时要求S和Ephi至少改善max(基点的10%,原绝对容差)，并满足原ET/EI/EV非劣。三个新臂对B0的电热非劣均通过；失败不是把观测保持当作新收益，而是相态双指标门未成立。N对历史D_E的集合误差下降35.163%，但相态RMS增加6.620%；对G和S也均未通过原A_w。D_E是已有长预算参照，不是本轮同新增成本终点。F29与B_E的[已有完整历史指标](historical-F-and-BE.csv)保留原身份，未重新训练或评分，也没有用N对它们的比较作为headline。

## 集合改善没有恢复正确连续状态

N的W内未归一化FP由0.0083302734降至0.0003343750，但FN由0.0006585938增至0.0055794922。D内FP由0.0080308594降至0.0000349609，FN由0.0001369141增至0.0050578125。活跃迹线在t=1.4025降至零，而原参考在D内仍活跃至t=1.8975。这是已保存场在原0.5阈值下的描述；没有把断电后无相态写入网络或损失。

**SUPPORTED_INTERPRETATION：**N删除了大量多余活跃支持，也删除了参考中仍存在的真实支持；阈值集合指标因此变小，连续相态RMS却变大。不能用单一集合指标的34.21%改善替代完整相态质量。N在全轨迹0.332004%的保存场点出现浮点sigmoid精确零；没有输出裁剪或从这些零值反求logit。该饱和现象保留为结果，不据此单独断言唯一优化根因。

![三臂完整开发比较](figures/three-arm-development.png)

图中虚线是基点误差的90%，本轮绝对容差更小；它只展示两项主增量阈值，完整电热守门在表中另报。右下为对数轴，黑横线分别为0.90/1.05/1.05的物理资格上限。所有面板都来自同一组固定终点。

## 独立物理资格与全程原审计

{physics_table}
N相态残差平方增加至基点10.287倍，热残差增加7.324%，虽相态BC下降84.959%，仍不具物理完成资格。S的raw相态平方增加47.090%，相态BC增加599.170%；较低相态RMS和较短耗时都不能补偿其物理失败。G的raw相态平方仅下降1.421%，未到10%要求。

原全程raw审计也完整保留：N的J_phi由0.00170902降至0.00142337，J_T由0.00391773降至0.00390935；S的J_phi升至0.00201370。此处J_phi和J_T分别是(r_phi/5)^2与(r_T/4)^2的原全程采样估计，不能与上表未缩放的D内均值混用。原全程池共32个时间，其中仅5个落在D；新独立D池有64个时间，空间和边界采样也不同。两个池给出不同局部结论，进一步限制了以综合训练/审计loss宣称物理改善的解释。预先指定的独立D守门仍失败；没有通过追加审计或挑选较有利的池改变裁决。这不是连续体收敛证据，也不是唯一失败原因的证明。

## 不变性质与事件

N/S的自身场电学抽查通过，完整T、I/P、V/q与基础数组保持一致，D外相态按恒等映射保持；所有检查和复用出处在[完整结果JSON](evidence/results.json)及run内composition-provenance记录中。这里保持的是已有预测，而非预测等于真值。N/S没有新增电学精度收益。

两个周期的加热支持、onset、recall、precision和相态活动质量均与B0一致。第二周期onset=1.2248、recall=0.77167037、precision=0.85482955，严格门仍失败。相态峰值位置可以改变：N第二周期峰值从t=1.5725移至1.3675，S移至1.485；这不修复加热支持不足。所有对象恢复分数仍为1，不改写为恢复门失败。G与基础预测不同不自动构成数据失败；本轮其W电流/电势误差分别增加2.003%/1.616%，仍在原非劣范围内。N相对G的窗外电势非劣代价标记为true，而相对B0为false；完整比较没有省略这一差别。

## 理论、可行性与资格

原数组必要条件通过：D含92.569%的相态平方误差和90.865%的集合误差；理想相态RMS/集合误差下界为0.02786552/0.000812964。它们是假设D内错误全消失的乐观极限，没有保证可由原PDE和表示实现。真实基点的有限反例证明观测预测和电学输出不变；固定温度/端点的64-cell热残差平方下界为0.00292226，32→64求积C相对变化2.66e−5。详见[方法及信息边界](method-and-information-boundary.md)、[理论图](figures/information-boundary.png)和两张诊断CSV。

十二项训练前聚焦/继承检查、三个零更新profile通过；N/G有限参数干预确实改变物理梯度，N观测梯度为零。G/N/S profile分别8.948/4.176/4.028秒，梯度范数0.066183/0.004942/0.109906，峰值RSS分别约506.84/465.98/486.69 MiB。这些是实现/可区分性证据，不是预测增量。后续设备传播回归另有一项通过，零科学更新。

## 实际执行与成本

{cost_table}
总计1800 Adam、600完整L-BFGS评估，CPU分支训练合计{work['training_seconds']/60:.3f}分钟。G/N在末次未接受试探处恢复最后接受态；S在预算内最后接受态结束。三者均完整消耗既定评估上限，没有数值失败或参考早停。训练正解/伴随为13031/13031；N/S均为0/0。独立raw审计64次正解，原生读出282次正解，均0伴随。完整profile已知100/100（含本地首次完成但元数据丢失的G）；局部内存失败尝试的完整工作量未知，未计为零。理论反例6次正解，其余小规模接口检查单列。

**实际偏差：**启动要求CUDA，但训练入口遗漏设备参数，所以三臂实际使用同一Xeon Gold 6130 CPU、4个Torch线程；GPU用于后续审计/原生读出。已执行源码单独归档，现入口已修复并通过针对性回归；本轮没有重启科学轨迹。N/S节省电学工作是可报告事实，但固定步数且质量未过门，不能宣称公平效率优势。两次本地profile工程失败、一次数组评分内存失败和最小恢复见[验证与偏差](validation-and-deviations.md)。后者使用只读磁盘映射及原评分函数，保留B0已完成分数，无新模型/参考计算。

云端结束于2026-09-24 16:34:14 UTC，校验回收后16:35:01 UTC发出关机，约47秒；关机命令返回0，随后SSH拒绝连接。全部新原生数组和检查点已本地保存，公开访问未新增，P03仍未关闭。

## 对论文的实际影响

新贡献可写为模型特定的观测信息边界、固定T下的热约束、真实接口实现及具有直接控制的有界阴性。不能写成新的通用投影理论、神经特有方法优势、合格物理补全、严格事件鲁棒性或材料验证。P02所需正面方法增量仍未补齐；现有全标签E/F器件配置收益与旧八臂阴性保持原身份。参见[入稿短段落](manuscript-revision-blocks.md)、[结构整合位置](integration-guide.md)、[来源](SOURCES.md)及[数据访问](data-and-reproduction.md)。本模块已可复用，但没有将旧完整主稿PDF冒充已完成此次全面排版整合。
''')

write(HERE/'manuscript-revision-blocks.md','''
# Ready-to-insert method and result paragraphs

## Method: an observation-preserving correction family

We tested physics-informed phase completion within the intersection of the existing phase-observation gap and a strictly zero-voltage interval, D=(1.36,2.02). Starting from the frozen B1 E/29 field, including its temperature adapter and complete phase latent variable, we set T_eta=T_base and phi_eta=sigmoid(psi_base+8g_D h_eta), with g_D=64s^3(1−s)^3 for s=(t−1.36)/0.66 inside D and zero elsewhere. The gate is C2 at both endpoints. Under the specified positive-conductivity, grounded electrical model, V=I=P=q=0 inside D; outside D the phase is unchanged. Consequently the available observation predictions and electrical ports equal those of the base for finite corrections. This preserves the base prediction, rather than asserting exact label fit or nonuniqueness of full coupled-PDE solutions. The construction adapts established [linear null-space](https://doi.org/10.1088/1361-6420/aaf14a) and [nonlinear data-consistency](https://www.aimsciences.org/article/doi/10.3934/ipi.2022037) ideas to this specific observation interface.

The neural correction N (1217 parameters) was compared with a full-time neural correction G with identical initialization and a cubic tensor B-spline correction S (7749 coefficients) on the same dark support. All retained the original raw phase equation, latent heat, phase boundary penalty and common saved loss calibration. Each received 600 Adam updates and 200 complete L-BFGS evaluations, with all endpoints fixed before reference scoring. Fixed temperature and phase endpoints impose an invariant integrated thermal residual C_i, yielding the conditional bound mean_t(r_T,i^2) ≥ [C_i/0.66]^2; thus observational invariance does not guarantee unrestricted physical completion.

## Results: lower set error without qualified phase completion

The prespecified joint phase-improvement criterion was not established. Against the frozen base, N reduced the missing-window set error from 0.00889987 to 0.00585531 (34.21%), but increased raw phase RMS from 0.10222268 to 0.11034555 (7.95%). The spline control reduced phase RMS and set error by 5.02% and 17.11%, while G achieved 1.37% and 1.71%; neither met the joint 10% criterion. N's lower set error accompanied a shift from false-positive to false-negative support: its window-integrated FP fell from 0.00833027 to 0.00033438, whereas FN rose from 0.00065859 to 0.00557949. The saved active fraction reached zero at t=1.4025, although the reference remained active until t=1.8975. No after-pulse zero-phase target was imposed.

The independent dark-window physical audit also failed: N's mean raw phase-residual square was 10.287 times the base and its thermal-residual square increased by 7.32%; S's phase-boundary penalty was 6.992 times the base. Lower values in the separate, more sparsely sampled full-history audit did not override the prespecified local qualification. N/S preserved all temperature and port predictions and the heated-window onset/recall/precision, including the second-cycle recall of 0.77167; strict two-cycle qualification therefore remained unmet. These results support the information-boundary construction but not a successful or neural-specific phase-completion method within this fixed budget.

## Execution and evidence limits

This experiment used one base initialization, the original reference and a common 160×80 native reader. A device-entry omission caused all three branches to train on the same CPU; their trajectories were retained, with measured training times of 20.76, 7.63 and 6.17 minutes for G, N and S. GPU execution was used for subsequent audits and native reads. Training required 13031 electrical forward/adjoint solves for G and zero for N/S; the reduction in work is not an efficiency claim at matched accuracy. Complete fields and checkpoints are retained locally, but this task did not make the complete dataset publicly accessible. Neither broader robustness nor experimental material validation is inferred. The earlier relative-residual/time-moment negative study remains separately documented in the supplement.
''')

write(HERE/'README.md',f'''
# 2026-09-24观测保持相态补全交付

**VERIFIED：{route}。** 阶段0—3完成，三臂1800 Adam/600完整L-BFGS；N/G/S对基础的原A_w和独立物理资格均未通过。N集合误差降低34.21%，但相态RMS增加7.95%。不触发阶段4。

先读[完整结果与裁决](results.md)和[可直接入稿的短段落](manuscript-revision-blocks.md)。[方法/信息边界](method-and-information-boundary.md)、[来源](SOURCES.md)、[主稿整合位置](integration-guide.md)、[验证及偏差](validation-and-deviations.md)、[数据与复现](data-and-reproduction.md)说明可复用部分与未闭合问题。

| 内容 | 入口 |
|---|---|
| 三范围全部连续指标、完整读出 | [all-metrics.csv](all-metrics.csv)、[full-readout-metrics.csv](full-readout-metrics.csv) |
| 全20对裁定及连续变化 | [all-pairwise-decisions.csv](all-pairwise-decisions.csv)、[完整JSON](evidence/results.json) |
| 两周期完整事件 | [both-cycle-events.csv](both-cycle-events.csv) |
| 独立D与全程原物理审计 | [raw-physics-audit.csv](raw-physics-audit.csv)、[full-raw-physics-audit.csv](full-raw-physics-audit.csv) |
| FN/FP、相态平方误差与浮点饱和 | [phase-error-decomposition.csv](phase-error-decomposition.csv) |
| 真实profile及训练成本 | [zero-update-profiles.csv](zero-update-profiles.csv)、[actual-training-cost.csv](actual-training-cost.csv) |
| 必要可行性及热下界 | [fixed-support-feasibility.csv](fixed-support-feasibility.csv)、[thermal-integral-bound.csv](thermal-integral-bound.csv) |
| 论文图件 | [信息边界](figures/information-boundary.png)、[三臂结果](figures/three-arm-development.png)，同名PDF可导出 |
| 结果路由与计算收口 | [decision.json](evidence/decision.json)、[关机摘录](evidence/compute-closure-public.json) |

新实现见../../pinn_pcm_sci/phk_v23_observation_preserving_phase.py及对应runner/readout/evaluate模块；实际运行目录为../../outputs/runs/20260924-observation-preserving-phase/。原始完整输入、全部复合场、端口、锁定检查点、独立池、日志与执行源码身份均保留本地。训练实际在CPU，读出/审计使用GPU；设备错误已透明记录并修复后续入口。本轮已回收并关闭实例，未发布Git或完整数组。

P02的合格方法增量与P03的外部完整数据访问仍未闭合。旧完整主稿保留，本文交付为可入稿模块和完整证据，不宣称二区竞争力或投稿完成。
''')

qa=read(HERE/'figures/visual-qa.json');qa['three-arm-development.png']=dict(visually_inspected=True,
    axes_legends_readable=True,physical_ratio_axis='log',raw_phase_and_set_metrics_separate=True)
save(HERE/'figures/visual-qa.json',qa)
for name in ('focused-tests-record.txt','additional-interface-tests.log','inherited-observation-tests.log',
             'inherited-lbfgs-tests.log','device-propagation-regression.log'):
    shutil.copyfile(RUN/name,HERE/'evidence'/name)

ledger=ROOT/'docs/experiment/2026-09-24-observation-preserving-phase-closeout.md'
write(ledger,f'''
# 观测保持相态补全：执行收口

任务PCM-20260924-OBSERVATION-PRESERVING-PHASE-01；2026-09-25完成。用户9月24日执行文件授权的阶段0—3已全部完成。**VERIFIED：{route}。** 三臂对B0的A_w及独立物理资格均未通过；阶段4未触发。没有新种子、参考求解、扩窗、解冻T或额外优化。

N的W集合误差下降34.209%，相态RMS增加7.946%；G分别改善1.706%/1.374%，S分别改善17.109%/5.025%。N独立D相态残差平方为基点10.287倍，热增加7.324%；S相态BC为6.992倍。N/S不变性质及加热事件字段验证通过，严格失败保留。一个基础初始化、原参考、共同160×80读出。

完整[论文模块](../../paper/observation_preserving_phase_20260924/README.md)、[结果](../../paper/observation_preserving_phase_20260924/results.md)、[机器裁决](../../paper/observation_preserving_phase_20260924/evidence/decision.json)构成研究证据；本治理入口不代替数值记录。运行根outputs/runs/20260924-observation-preserving-phase，基点是旧B1 E/29，所有三个新臂都冻结该基点且零修正启动。

实际1800 Adam、600完整L-BFGS，训练13031正解/13031伴随；raw审计64正解，原生读出282正解。因设备参数遗漏，三臂训练实际为同一CPU，合计34.557分钟；审计/读出为CUDA。既有轨迹未重跑，执行源码已单独保留，当前入口修复并有零更新回归。局部profile/评分内存异常均按最小范围补齐；原公式与权重不变，评分恢复使用只读磁盘映射。

云端最终退出0；完整回收校验成功，结束约47秒后请求关机，返回0并确认SSH拒绝连接。[公开关机摘录](../../paper/observation_preserving_phase_20260924/evidence/compute-closure-public.json)不包含连接凭据。完整原生数组本地可用，未新增外部访问；P03保持开放。未执行commit/push/PR。

**SUPPORTED_INTERPRETATION：**观测保持空间与理论约束成立，但本配方/预算未取得合格相态补全。没有触发确认申请，不自动把样条的局部收益作为PINN目标完成。下一步只供作者基于现有证据决定论文定位或另立不同研究问题；本轮没有新增科研执行授权。P02、严格事件、formal OOD和材料验证仍未补齐，旧阴性和旧E/F配置收益不改写。
''')

for rel in ('README.md','active_phase.md','PROJECT_STATE.md','docs/plans/NEXT_ACTIONS.md'):
    p=ROOT/rel;old=p.read_text(encoding='utf-8');marker='# 历史收口：相对相态残差与时间矩开发'
    assert marker in old
    result_link=relative(p,HERE/'results.md');ledger_link=relative(p,ledger)
    head=f'''# 当前：观测保持相态补全已收口

**VERIFIED：{route}。** 阶段0—3完成，N/G/S均未对冻结E29通过原A_w，也均未通过独立D物理资格。N集合误差降低34.209%，但相态RMS增加7.946%；其D内raw相态平方为基点10.287倍、热增加7.324%。不变性质和完整原生数组验证通过，严格双周期仍失败。全部1800 Adam/600完整L-BFGS已完成，实际为同一CPU训练，后续GPU审计/读出；产物已校验回收并关闭实例。见[完整结果]({result_link})和[实验收口]({ledger_link})。

**SUPPORTED_INTERPRETATION：**本轮未建立合格或神经特有补全增量，阶段4条件未触发，停止新增科研计算。理论边界、代码、直接控制及阴性证据可复用；P02方法增量和P03完整数据外部访问仍未补齐。没有自动Git发布。本段supersedes本任务此前准备/执行中状态，下方旧科学结论保留原身份。

- `phase_id`: `PHK_V23_OBSERVATION_PRESERVING_PHASE`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VERIFIED_OBSERVATION_PRESERVING_PHASE_NO_COMPLETION_INCREMENT`
- `next_research_execution_authorized`: `false`

'''
    p.write_text(head+marker+old.split(marker,1)[1],encoding='utf-8')
for rel in ('CODEX_CONTEXT.md','docs/README.md'):
    p=ROOT/rel;old=p.read_text(encoding='utf-8');marker='# 历史：相对相态残差与时间矩开发已收口';assert marker in old
    head=f'''# 当前：观测保持相态补全已收口

**VERIFIED：{route}。** N/G/S三臂开发完整，主增量与独立物理资格均未成立；阶段4不触发。N集合改善34.209%但相态RMS恶化7.946%。实际CPU训练/GPU读出已如实记录，产物回收、实例关闭。见[结果与论文模块]({relative(p,HERE/'README.md')})、[实验收口]({relative(p,ledger)})及[当前阶段]({relative(p,ROOT/'active_phase.md')})。新科研、完整数据公开和Git发布均未授权；旧时间矩与B1结果保持历史身份。

'''
    p.write_text(head+marker+old.split(marker,1)[1],encoding='utf-8')
p=ROOT/'CONTEXT.md';old=p.read_text(encoding='utf-8')
old=old.replace('## 当前研究问题（2026-09-23收口）','## 历史研究问题（2026-09-23收口）',1)
title,rest=old.split('\n',1)
head=f'''\n\n## 当前研究问题（2026-09-25收口）

**VERIFIED：{route}。** 冻结E29的观测保持相态补全三臂均未通过原A_w/独立物理资格。N的集合误差降低34.209%，连续相态RMS增加7.946%；D内raw相态平方为基点10.287倍。N/S保持观测预测、T/端口及加热事件，不能据此补齐原严格失败。一个基点、原参考、共同160×80读出，不是formal OOD或材料验证。见[完整结果](paper/observation_preserving_phase_20260924/results.md)。

**SUPPORTED_INTERPRETATION：**观测等价构造成立不等于合格物理/状态补全。当前配方及预算已收口，阶段4不触发；旧全标签配置收益与时间矩阴性均保留。实际CPU训练/GPU审计读出、内存恢复及关机证据已透明记录。P02/P03仍开放，没有新科研或发布授权。以下均为历史口径。
'''
p.write_text(title+head+rest,encoding='utf-8')
print(json.dumps(dict(route=route,stages_0_to_3_complete=True,stage_4_triggered=False,instance_off=True)))
