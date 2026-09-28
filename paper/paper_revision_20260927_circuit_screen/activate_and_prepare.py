"""Prepare the approved local manuscript revision; never run a scientific solver."""
from pathlib import Path
import csv
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OLD = ROOT / 'paper/paper_revision_20260926_core'
TASK = 'PCM-20260927-MANUSCRIPT-CIRCUIT-SCREEN-01'

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

def main():
    if (HERE / 'preparation.json').exists():
        raise RuntimeError('Preparation already recorded; do not overwrite the revision.')
    for source, target in [
        ('E:/PINN-PCM/CODEX_Execution_Instructions (1).md', HERE / 'instructions.md'),
        ('E:/PINN-PCM/PLAN_Review_Amendments.md', HERE / 'plan-amendments.md'),
        ('E:/PINN-PCM/PINN_PCM_Data_Handling_Norms_2026-09-28.md', ROOT / 'docs/governance/PINN_PCM_Data_Handling_Norms_2026-09-28.md'),
    ]:
        shutil.copyfile(source, target)
    # Small text is copied for editing. Immutable images/tables use same-volume
    # hard links and are never edited through the new path; this is not a backup.
    linked = []
    for directory in ['tables', 'figures', 'evidence']:
        for src in (OLD / directory).rglob('*'):
            if src.is_file():
                dst = HERE / src.relative_to(OLD)
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.hardlink_to(src)
                linked.append(str(dst.relative_to(HERE)).replace('\\', '/'))
    for name in ['source/manuscript.md', 'source/supplement.md', 'references.md',
                 'claim_evidence_matrix.md', 'table-source-map.json', 'coverage-report.md',
                 'conditional-evolution-report.md', 'vo2-author-reproduction.md',
                 'standalone-README.md', 'data-access-plan.md', 'prepare_document.py',
                 'build_docx.py', 'record_build.py']:
        dst = HERE / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(OLD / name, dst)
    rows = list(csv.DictReader((OLD/'tables/fcov-all-effects.csv').open(encoding='utf-8-sig')))
    selected = [r for r in rows if r.get('reference') == 'spatial' and r.get('reader') == 'fine' and r.get('comparison') == 'E_vs_F_cov']
    write(HERE/'display-source-rows.json', json.dumps(selected, ensure_ascii=False, indent=2)+'\n')
    m = (HERE/'source/manuscript.md').read_text(encoding='utf-8')
    old = 'Against an additional soft control with mixed-measure coverage enhancement, E meets the complete device criterion in 12/12 shorter-protocol sensitivity conditions on the same two parents.'
    new = 'Against a soft control with mixed-measure space–time coverage enhancement, the eliminated configuration reduces current error by 52.68% and 66.55% for the two shorter-protocol initializations under the spatially refined reference and finer electrical reader.'
    assert old in m
    m = m.replace(old, new, 1)
    old = 'Against the mixed-measure coverage control F_cov, E satisfies the original whole-history A/B criteria in 12/12 and 12/12 reference/reader/initialization conditions. The device-criterion advantage is retained in all twelve sensitivity conditions.'
    new = 'Against F_cov, E satisfies the original whole-history phase criterion A and device criterion B in 12/12 conditions each: two initializations, each evaluated with three references and two readers. The twelve rows are sensitivity conditions of two endpoints, not independent repetitions.'
    assert old in m
    m = m.replace(old, new, 1)
    anchor = 'F_cov nevertheless reduces current and power error relative to F'
    table = ('Table 2a. Continuous effects against F_cov under the spatially refined reference and finer electrical reader. Current NRMSE is reported in percent from the native 240 by 120 electrical reader; phase RMS uses the original 160 by 80 ROI. Values are display summaries of the existing spatial/fine/E_vs_F_cov rows, not new threshold decisions.\n\n'
             '{{TABLE:fcov-continuous-primary}}\n\n')
    m = m.replace(anchor, table+anchor, 1)
    anchor = '### 3.5 Common parents, fixed endpoints and readouts'
    explanation = ('The controls answer distinct questions. F_cov tests the declared mixed-measure strengthening of the soft electrical configuration; D_E tests the additional thermal/phase interior-residual package; B_E tests competitiveness under its stated use of visible fields; B1 tests a complete second-cycle phase-observation gap. E/F and E/F_cov remain configuration comparisons and do not isolate the VJP.\n\n')
    m = m.replace(anchor, explanation+anchor, 1)
    old = 'The curated repository through [commit 90508f05](https://github.com/ghy001122/PINN-PCM-SCI/tree/90508f05a6f233a485413c7589cc74420015cbea) includes the integrated manuscript and selected B1, bounded-correction, diagnostic and conditional-evolution evidence. The present revision and mixed-measure coverage comparison are subsequent local deliverables.'
    new = 'The curated results published in [commit 539130a](https://github.com/ghy001122/PINN-PCM-SCI/tree/539130a2837594c4d8ae3d67fadddda3e862548a), with the recorded release verification at [6dd147a](https://github.com/ghy001122/PINN-PCM-SCI/tree/6dd147af757bf5788e9c5d1535b49e7f965b2600), include the integrated manuscript and selected B1, bounded-correction, diagnostic, conditional-evolution and mixed-measure coverage evidence. This subsequent local text revision has not been published.'
    assert old in m
    write(HERE/'source/manuscript.md', m.replace(old, new, 1))
    write(HERE/'tables/fcov-continuous-primary.md', '| Seed | Current F_cov (%) | Current E (%) | Reduction (%) | Phase F_cov | Phase E | Reduction (%) |\n|---|---:|---:|---:|---:|---:|---:|\n| 29 | 2.14630 | 1.01558 | 52.68 | 0.0241544 | 0.0199363 | 17.46 |\n| 43 | 2.09424 | 0.70046 | 66.55 | 0.0244337 | 0.0197631 | 19.12 |\n')
    mapping = (HERE/'claim_evidence_matrix.md').read_text(encoding='utf-8')
    write(HERE/'claim_evidence_matrix.md', mapping+'\n## Local revision on 28 September 2026\n\nAbstract and Section 4.3 / Table 2a use only spatial/fine/E_vs_F_cov, seeds 29 and 43, from [the unchanged complete effects](tables/fcov-all-effects.csv). The displayed values and full-precision rows are in [display-source-rows.json](display-source-rows.json). Original F and F_cov effects remain separate. The new circuit screen is a separate author-model diagnostic and supports no new PINN or material claim.\n')
    b = HERE/'build_docx.py'
    write(b, b.read_text(encoding='utf-8').replace('Core revision 26 September 2026', 'Circuit screen revision 28 September 2026'))
    write(HERE/'README.md', '# 现稿修订与固定电路筛查\n\n任务 '+TASK+' 已授权执行中。权威正文及补充在 source；历史输入不覆盖。新模拟筛查最多十条保存系统轨迹，实验最多五条合格开发记录，4.1/3.9 V 不读取数值。无新推进、训练、参数反演、Git 发布或公开上传。\n\n[执行指令](instructions.md) · [审查修订](plan-amendments.md) · [数据规范](../../docs/governance/PINN_PCM_Data_Handling_Norms_2026-09-28.md)\n')
    write(HERE/'preparation.json', json.dumps({'task_id':TASK,'baseline':'6dd147af757bf5788e9c5d1535b49e7f965b2600','immutable_hardlinked_assets':linked,'hardlinks_are_independent_backup':False,'original_numeric_arrays_copied':False,'new_remote_sync':'PENDING'},indent=2)+'\n')
    norms = ROOT/'AGENTS.md'
    text = norms.read_text(encoding='utf-8')
    line = '- 科研文件、缓存、回收与临时文件处理遵守 [2026-09-28 数据处理规范](docs/governance/PINN_PCM_Data_Handling_Norms_2026-09-28.md)。该规范不自动授权历史清理、公开上传或突破数据隔离；离线待同步如实记录。\n'
    text = text.replace('## 仓库与交付\n', '## 仓库与交付\n\n'+line, 1)
    write(norms, text)
    status = ('<!-- CIRCUIT27_CURRENT_BEGIN -->\n# 当前：现稿局部修订与固定电路筛查执行中\n\n'
              '用户于2026-09-28明确批准 '+TASK+'。仅执行保存数组的固定PCHIP、必要测量资格核对及局部修稿；按本轮指令使用既有GPU实例上的兼容SciPy环境，完成回收后及时关机。新训练、新ODE/PDE轨迹、参数反演、保留协议评分、Git和数据公开不在范围。\n\n'
              '- `phase_id`: `PHK_V23_MANUSCRIPT_CIRCUIT_SCREEN`\n- `lifecycle_state`: `EXECUTING`\n- `blocker_id`: `NONE`\n- `claim_status`: `UNKNOWN_SCREEN_NOT_EXECUTED`\n- `next_research_execution_authorized`: `true`\n\n<!-- CIRCUIT27_CURRENT_END -->\n\n')
    for rel in ['README.md','active_phase.md','PROJECT_STATE.md']:
        path=ROOT/rel
        text=path.read_text(encoding='utf-8')
        for key in ['phase_id','lifecycle_state','blocker_id','claim_status','next_research_execution_authorized']:
            text=text.replace('- `'+key+'`:', '- `historical_'+key+'`:')
        write(path,status+text)
    plan=ROOT/'docs/plans/NEXT_ACTIONS.md'
    shutil.copyfile(plan,ROOT/'archive/2026-09-28-pre-circuit-screen-next-actions.md')
    write(plan,status+'授权合同：[本轮指令](../../paper/paper_revision_20260927_circuit_screen/instructions.md)。\n\n顺序：局部稿件与固定配置 → 聚焦检查 → 十条保存模拟分析 → 合格开发记录条件分析 → 回收核验关机 → 成稿与数据处理收口。历史结果保持，P02/P03及材料泛化不自动关闭。\n')
    print('PREPARED',HERE)

if __name__ == '__main__':
    main()
