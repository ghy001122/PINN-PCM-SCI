"""Render the authorized diagnostic from saved records only; no model calls."""
from pathlib import Path
import csv
import json
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RUN=ROOT/'outputs/runs/20260924-observation-preserving-phase'
DATA=RUN/'diagnostic-20260925'
LABELS=('B0','N-Adam','N-final','S-final')
POOLS=('fixed-training','independent-D','common-256','spatial-256')
COLORS=('#66717b','#d28c34','#177da6','#258e60')


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,v):Path(path).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def main():
    rows=list(csv.DictReader((DATA/'components.csv').open(encoding='utf-8')))
    for r in rows:
        for k in r:
            if k not in ('pool','state'):r[k]=float(r[k])
    lookup={(r['pool'],r['state']):r for r in rows}
    audit=read(RUN/'endpoint-audits.json')['arms'];lock=read(RUN/'all-endpoints-locked.json')['objects']
    for label,arm in [('B0','B0'),('N-final','N'),('S-final','S')]:
        actual=lookup['independent-D',label];old=audit[arm]['D']
        for k,key in [('phase_raw','phase_raw_mean_square'),('thermal_raw','thermal_raw_mean_square'),('phase_BC','phase_BC_mean_square_original_denominator')]:
            np.testing.assert_allclose(actual[k],old[key],rtol=2e-12,atol=1e-14)
    np.testing.assert_allclose(lookup['fixed-training','B0']['original_variable_objective'],read(RUN/'profile-N.json')['objective']['objective'],rtol=2e-12)
    np.testing.assert_allclose(lookup['fixed-training','N-Adam']['original_variable_objective'],next(v for v in lock if v['arm']=='N')['lbfgs']['initial_loss'],rtol=2e-12)
    for label,arm in [('N-final','N'),('S-final','S')]:
        np.testing.assert_allclose(lookup['fixed-training',label]['original_variable_objective'],next(v for v in lock if v['arm']==arm)['lbfgs']['last_accepted_loss'],rtol=2e-12)
    for r in rows:
        base=lookup[r['pool'],'B0']
        for k in ('phase_raw','thermal_raw','phase_BC','H'):r[k+'_ratio_to_B0']=r[k]/base[k]
        r['boundary_H_share']=r['boundary_weighted']/r['H']
    with (HERE/'physics-objective-components.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    time_rows=list(csv.DictReader((DATA/'time-components.csv').open()))
    detail={};traces={}
    for pool in POOLS:
        with np.load(DATA/(pool+'-traces.npz')) as z:traces[pool]={k:z[k] for k in z.files}
        for label in LABELS:
            rr=[x for x in time_rows if x['pool']==pool and x['state']==label]
            t=np.array([float(x['time']) for x in rr]);w=np.array([float(x['weight']) for x in rr]);v=np.array([float(x['phase_raw']) for x in rr])
            edge=(t<1.36+.66/16)|(t>2.02-.66/16)
            ix=int(np.argmax(v));jx=int(np.argmax([float(x['phase_BC']) for x in rr]))
            detail[pool+'/'+label]=dict(edge_phase_residual_fraction=float((w*v*edge).sum()/(w*v).sum()),
                psi_min=min(float(x['psi_min']) for x in rr),psi_max=max(float(x['psi_max']) for x in rr),
                delta_psi_min=min(float(x['delta_psi_min']) for x in rr),delta_psi_max=max(float(x['delta_psi_max']) for x in rr),
                phi_t_abs_max=max(float(x['phi_t_abs_max']) for x in rr),phase_grad_abs_max=max(float(x['phase_grad_abs_max']) for x in rr),
                phase_laplacian_abs_max=max(float(x['phase_laplacian_abs_max']) for x in rr),
                phase_time_hotspot=float(t[ix]),phase_hotspot_xy=[float(rr[ix][k]) for k in ('phase_hot_x','phase_hot_z')],
                boundary_time_hotspot=float(t[jx]),boundary_hotspot_xy=[float(rr[jx][k]) for k in ('bc_hot_x','bc_hot_z')],
                bc_by_side={s:sum(float(x['weight'])*float(x['bc_'+s]) for x in rr) for s in ('left','right','bottom','top')})
    common=traces['common-256'];t=common['time'];w=common['weight'];n=common['N-final/phi_t']
    i,j=np.unravel_index(np.argmax(abs(n)),n.shape);inds=np.flatnonzero(abs(n[:,j])>=abs(n[i,j])/2)
    groups=np.split(inds,np.flatnonzero(np.diff(inds)>1)+1);group=next(g for g in groups if i in g)
    layer=dict(peak_time=float(t[i]),peak_cell=int(common['cells'][0,j]),peak_phi_t=float(n[i,j]),
        sampled_halfmax_interval=[float(t[group[0]]),float(t[group[-1]])],halfmax_node_count=len(group),
        max_local_node_gap=float(np.diff(t[max(0,group[0]-1):min(len(t),group[-1]+2)]).max()),
        statement='Finite sampled layer is resolved by this numerical comparison; no uniform continuum certificate.')
    thermal=read(DATA/'thermal-16.json');thermal_low=read(DATA/'thermal-8.json');quad=read(DATA/'quadrature.json')
    quad_max=max(v for r in quad['128_to_256']['relative_changes'].values() for v in r.values())
    endpoint_change=float(abs(np.array(thermal['endpoint_offset'])-np.array(thermal_low['endpoint_offset'])).max())
    spatial={k:{m:lookup['spatial-256',k][m]/lookup['common-256',k][m] for m in ('phase_raw','thermal_raw','phase_BC','H')} for k in LABELS}
    closure=read(DATA/'compute-closure.json');execution=read(DATA/'execution.json')
    assert closure['recovery_verified'] and closure['instance_shutdown_confirmed']
    assert not quad['128_to_256']['requires_higher_order']
    result=dict(task_id='PCM-20260925-PHYSICS-OBJECTIVE-FEASIBILITY-01',status='BOUNDED_DIAGNOSTIC_COMPLETE',
        route='A_CONFIRMED_B_CONFIRMED_C_EXACT_CONSTRAINT_SUPPORTED',original_identity_checks='PASS',
        objective_qualification_mismatch=True,spatial_sampling_sensitive=True,
        temporal_status='TIME_CHECK_PASSED_ON_SAMPLED_SPATIAL_SUPPORT',quad_max_relative_change=quad_max,
        continuum_certificate=False,detail=detail,N_actual_sampled_layer=layer,spatial_sensitivity=spatial,
        thermal=thermal,thermal_endpoint_change_128_to_256=endpoint_change,
        tolerated_thermal_feasibility='UNKNOWN; exact-zero thermal incompatibility does not exclude the original 5-percent tolerance',
        P02_closed=False,P03_closed=False,new_training_authorized=False,
        execution=execution,compute_closure=closure)
    save(DATA/'analysis.json',result)
    save(HERE/'evidence/physics-objective-diagnostic.json',result)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(2,3,figsize=(14.4,8.5),layout='constrained')
    x=np.arange(4)
    for ax,pool,title in zip(axes[0],POOLS[:3],('Fixed training pool','Original independent D pool','Common 256-time-node measure')):
        for j,key in enumerate(('phase_raw','thermal_raw','phase_BC','H')):
            ax.bar(x+(j-1.5)*.19,[lookup[pool,s][key+'_ratio_to_B0'] for s in LABELS],width=.19,color=COLORS[j],label=('Phase','Thermal','Boundary','H')[j])
        ax.set(yscale='log',xticks=x,xticklabels=LABELS,ylabel='Ratio to B0 on the same pool',title=title,ylim=(.008,25));ax.axhline(1,c='0.4',lw=.8);ax.grid(axis='y',alpha=.15)
    axes[0,0].legend(ncol=2,fontsize=8,loc='lower left')
    ax=axes[1,0]
    for label,color in zip(LABELS,COLORS):
        v=(common[label+'/rphi']**2).mean(1);ax.plot(t,v,color=color,label=label,lw=1.4)
    ax.set_yscale('symlog',linthresh=.002)
    ax.set(xlabel='Time in D',ylabel='Conditional mean raw phase residual squared',title='Temporal concentration: same cells and weights')
    for a,b in ((1.36,1.40125),(1.97875,2.02)):ax.axvspan(a,b,color='0.7',alpha=.14)
    ax.legend(fontsize=8)
    ax=axes[1,1]
    for j,pool in enumerate(('common-256','spatial-256')):
        z=traces[pool];v=z['S-final/normal'];nb=v.shape[1]//4;ms=z['weight']@(v[:,2*nb:3*nb]**2);xy=z['boundary_xy'][0,2*nb:3*nb]
        ax.scatter(xy[:,0],ms,s=22,label='Spatial sample '+str(j+1),color=COLORS[j],alpha=.8)
    ax.set_yscale('symlog',linthresh=.01)
    ax.set(xlabel='Bottom boundary x (z=0)',ylabel='Time-mean normal phase derivative squared',title='S: bottom-boundary hotspots and coverage');ax.legend(fontsize=8)
    ax=axes[1,2]
    with np.load(DATA/'thermal-16-traces.npz') as z:
        for k in range(64):ax.plot(z['time'],z['phi_H'][:,k],color='#217e88',alpha=.15,lw=.8)
    ax.axhline(0,color='0.3',ls='--',lw=.8);ax.axhline(1,color='0.3',ls='--',lw=.8)
    ax.set(xlabel='Time in D',ylabel='Unclipped temperature-implied phase',title='Fixed T: conditional heat identity, 64 cells')
    fig.suptitle('Observation preservation does not ensure independent physical consistency',fontsize=14)
    for ext in ('png','pdf'):fig.savefig(HERE/'figures'/('physics-objective-diagnostic.'+ext),dpi=185)
    plt.close(fig)
    table='| 同池状态 | 相态平方 | 热平方 | 相态BC | H |\n|---|---:|---:|---:|---:|\n'
    for pool in POOLS:
        for label in LABELS:
            r=lookup[pool,label];table+=f"| {pool} / {label} | {r['phase_raw']:.7g} | {r['thermal_raw']:.7g} | {r['phase_BC']:.7g} | {r['H']:.7g} |\n"
    c=lookup['common-256','N-final'];c2=lookup['spatial-256','N-final'];s=lookup['common-256','S-final'];s2=lookup['spatial-256','S-final']
    text=f'''# 物理目标取舍、采样失真与固定温度可行性：定向诊断

任务 `PCM-20260925-PHYSICS-OBJECTIVE-FEASIBILITY-01` 已完成；基线 `51f561023ef7a233ba5639f5e8d22c3e314fe8f2`。**VERIFIED：A目标/资格不一致与B空间采样敏感均得到实际检查点支持；C严格热一致性受固定温度和端值阻断，但原5%热非劣容限下是否可行仍UNKNOWN。** 旧 `NO_COMPLETION_INCREMENT` 不改写，P02正向方法目标和P03完整数组访问均未闭合。

本轮只读B0、N/adam-600、N/final、S/final，G只读现有表；四对象H分解和全部20个原A_w已从实际保存字段复核，与附件转录一致，20项均不通过。没有参数更新、电学求解、参考场读取、三参考重评分或新训练。既有E/F共同修复后的正向器件结果保留原主线。

## 1. 同测度分项与阶段定位

沿用原残差和共享面AD热通量。每个池先归一为D内时间平均：`H=p/75+t/48+5 Bphi`；原BC分母13保留。固定池的实际可变目标另乘 `0.1/bE × 0.264`，不能直接与H数值混用。表中所有候选比较均使用同一行组的测度；池间绝对数值不是收敛证书。

{table}

**VERIFIED：** 固定池B0 objective={lookup['fixed-training','B0']['original_variable_objective']:.17g}；N-Adam={lookup['fixed-training','N-Adam']['original_variable_objective']:.17g}，精确对应L-BFGS initial_loss；N/S终点也复现原last_accepted_loss。原独立D的三个分项复现旧审计。零修正固定池/独立D的边界H份额分别为{100*lookup['fixed-training','B0']['boundary_H_share']:.3f}%/{100*lookup['independent-D','B0']['boundary_H_share']:.3f}%，这不是梯度份额。

共同256节点测度下，N-Adam相态平方已是B0的{lookup['common-256','N-Adam']['phase_raw_ratio_to_B0']:.3f}倍，N-final扩大到{c['phase_raw_ratio_to_B0']:.3f}倍，而H下降{100*(1-c['H_ratio_to_B0']):.3f}%。第二空间样本相应为{c2['phase_raw_ratio_to_B0']:.3f}倍与H下降{100*(1-c2['H_ratio_to_B0']):.3f}%。因此目标允许边界收益补偿相态恶化的结论不依赖单个旧审计池；把共同lambda整体调大不会改变分项偏好。保存的Adam日志来自变化中的随机池、且为更新前值，不能当成同池曲线；此处阶段判断来自固定检查点的同池复算。

## 2. 实际N的端层与S的空间热点

**VERIFIED：** 共同测度中N-final的delta_psi最低为{detail['common-256/N-final']['delta_psi_min']:.3f}，完整psi最低{detail['common-256/N-final']['psi_min']:.3f}；N-Adam的delta仅在[{detail['common-256/N-Adam']['delta_psi_min']:.3f},{detail['common-256/N-Adam']['delta_psi_max']:.3f}]。N-final的max|phi_t|={detail['common-256/N-final']['phi_t_abs_max']:.3f}，B0为{detail['common-256/B0']['phi_t_abs_max']:.3f}。两端合计12.5%的时间支撑承载{100*detail['common-256/N-final']['edge_phase_residual_fraction']:.2f}%的N相态残差平方积分；第二样本为{100*detail['spatial-256/N-final']['edge_phase_residual_fraction']:.2f}%。峰值单元(x,z)=(0.3125,0.0125)，峰时{layer['peak_time']:.6f}，采样半高区间[{layer['sampled_halfmax_interval'][0]:.6f},{layer['sampled_halfmax_interval'][1]:.6f}]包含{layer['halfmax_node_count']}个Gauss点。

两端另以64个预声明对数距离、同一128单元检查gate/delta/phi_t，delta在精确端点为零。所测位置没有显示比当前时间求积更窄且未解析的层。**SUPPORTED_INTERPRETATION：** N在Adam后至最终点之间形成了大负logit修正、内部压低相态及端部残差集中；这与构造风险相符，但没有追踪中间权重，不能证明沿常数头方向形成，也不能把构造反例当作实际轨迹的因果证明。

**VERIFIED：** 16小片×8/16点的最大分项变化{100*quad_max:.5f}%，排序不变，按合同未做512。使用同256节点、另一组空间位置后，S的BC从{s['phase_BC']:.6g}变为{s2['phase_BC']:.6g}，对各自基点分别为{s['phase_BC_ratio_to_B0']:.3f}/{s2['phase_BC_ratio_to_B0']:.3f}倍；原固定池却仅为{lookup['fixed-training','S-final']['phase_BC_ratio_to_B0']:.3f}倍。其异常几乎全在底边z=0，首组热点x≈−0.479、0.475、−0.466，三点贡献该样本底边积分约91.65%。空间支撑改变确实影响幅度，时间8→16阶变化不能解释这一差异；但未交叉替换原池的时间/空间点，不能把原训练—审计差距全数归因于空间。N相态残差也高度集中于少数近底边单元，不能据128个单元宣称空间收敛。

![同池物理分项、时间集中和温度隐含轨迹](figures/physics-objective-diagnostic.png)

## 3. 固定温度条件的具体限制

复用原64-cell坐标；原记录只保存积分C和平方量，未保存T坐标导数，故本轮以原共享面算子重新计算必要T导数，未切换算子。phi_H由热方程时间积分得到，原值未裁剪。128→256节点的端点偏差最大变化{endpoint_change:.3g}；256节点热积分恒等式`phi_H(b)-phi_base(b)=-C/L`最大误差{thermal['endpoint_identity_max_absolute']:.3g}，C对历史64阶最大差{thermal['C_vs_historical64_max_absolute']:.3g}。

**VERIFIED：** phi_H在采样节点范围为[{thermal['phi_min']:.6f},{thermal['phi_max']:.6f}]，时间×单元加权越界份额{100*thermal['outside_time_cell_fraction']:.3f}%，{100*thermal['cells_ever_outside_fraction']:.3f}%单元至少有一个越界时刻。端点绝对偏差最小/中位/最大为{thermal['endpoint_absolute_quantiles'][0]:.6f}/{thermal['endpoint_absolute_quantiles'][2]:.6f}/{thermal['endpoint_absolute_quantiles'][-1]:.6f}。热平方下界{thermal['mean_raw_square_lower_bound']:.10f}，同单元同时间基础热平方{thermal['base_mean_raw_square']:.10f}，比例{100*thermal['lower_to_base']:.3f}%。这支持固定T下的严格零热残差轨迹不能同时满足原端点及相态范围；不能推出允许5%热非劣时也不可能改善相态。phi_H不是相态PDE解、教师标签或唯一物理解，未重建其空间导数，也未给它相态资格结论。

## 4. 后续决策与一次入稿提议

**SUPPORTED_INTERPRETATION：** 先保留A/B/C并存的诊断，不启动旧N/S救援、不整体提高lambda、不解冻T或扩窗。现有证据还不能决定固定T在原误差容限下是否阻断有效补全，因此本轮不建议直接进入新训练。唯一可另行提请的下一项是温度驱动相态推进诊断：沿原二维网格/材料方程，以B0(a)为初态、T_base为输入，零参考初态替代、零训练；仅作传统诊断，不能作为PINN创新或自动训练标签。具体推进算子、初始边界不相容处理与误差预算须在执行前另行冻结批准。本轮未生成该轨迹。

本轮不提交新训练方案。后续可行性未明确前，不把分项约束、重采样或另一网络名称当作已成立方案；未来若提出训练，仍须另定一个候选、强直接控制、固定预算、原A_w及允许失败的停止条件。通用重采样和约束优化不构成原创；训练中使用的物理验证池也不再是最终独立审计。近期[When PINNs Go Wrong, §2](https://arxiv.org/html/2604.23528v1)已讨论经验残差伪解及重采样/伪时间关系；本轮只核对这一来源边界，没有移植算法或导入其适用性结论。[PhysicsCorrect](https://arxiv.org/html/2507.02227v2)也提供已有物理修正先例，不能凭该名称主张本器件有效。

建议只在现有主稿 `paper/paper_revision_20260921/source/manuscript.md` 的 **§6.3第一段之后** 加入下述一个结果段及本图，替代继续按日期扩展章节；不改写§4 E/F正向结果。精简审阅稿对应“What the experiment identifies”位置。本轮仅提交整合提议，没有重排旧主稿。

> Observation-preserving phase corrections left temperature and electrical-port predictions unchanged, but did not establish qualified phase completion. N reduced set error by 34.21% while increasing phase RMS by 7.95%. In a common 256-node dark-interval diagnostic, its scalar physical objective fell by {100*(1-c['H_ratio_to_B0']):.2f}% even though the raw phase-residual square increased {c['phase_raw_ratio_to_B0']:.2f}-fold: boundary improvement compensated for dynamical deterioration. The spline's boundary penalty was strongly sensitive to spatial coverage, while the tested temporal refinement changed all integrated components by less than {100*quad_max:.3f}%. The temperature-implied trajectory also violated phase-range and endpoint conditions under exact thermal balance; this does not establish infeasibility under the allowed thermal tolerance. Thus scalar loss reduction cannot replace independent equation-wise consistency, and unchanged ports do not imply accurate internal phase states.

## 5. 执行与复查

真实设备为已开启V100，诊断用时{execution['seconds']:.3f}秒；本轮参数更新、电学正/伴随求解、相态推进、参考场读取均为0，未出现科学计算失败。首次本地图件生成因Matplotlib轴属性用法报错，修复后仅重读保存数据，未追加模型计算。四状态坐标工作量与共享面AD计数见[紧凑诊断记录](evidence/physics-objective-diagnostic.json)。完成后校验回收，约4秒后请求关机且确认实例关闭。未提交或推送本轮诊断。

[分项CSV](physics-objective-components.csv)、[图PDF](figures/physics-objective-diagnostic.pdf)与[诊断实现](../../pinn_pcm_sci/phk_v23_physics_objective_diagnostic.py)可直接复查。每时间分项、psi/delta/phi_t/rphi/rT/边界迹线和热隐含轨迹保留于原运行目录的 `diagnostic-20260925/`；没有复制新的权威档案。P03完整模型与数组外部访问仍是实质待办。
'''
    (HERE/'physics-objective-diagnostic.md').write_text(text,encoding='utf-8')
    print(json.dumps(dict(status='DIAGNOSTIC_REPORT_BUILT',identity_checks='PASS',quad_max_relative=quad_max,thermal_endpoint_change=endpoint_change),ensure_ascii=False))


if __name__=='__main__':main()
