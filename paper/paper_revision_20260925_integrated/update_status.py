"""Maintain the four existing live status surfaces for this authorized task."""
from pathlib import Path
import argparse
import re

ROOT=Path(__file__).resolve().parents[2]
FIELDS=('phase_id','lifecycle_state','blocker_id','claim_status','next_research_execution_authorized')

def update(stage,claim,authorized,description):
    for name in ('active_phase.md','README.md','PROJECT_STATE.md','docs/plans/NEXT_ACTIONS.md'):
        path=ROOT/name;old=path.read_text(encoding='utf-8')
        if '<!-- WA_CURRENT_END -->' in old:
            old=old.split('<!-- WA_CURRENT_END -->',1)[1].lstrip()
        else:
            for field in FIELDS:
                old=old.replace(f'- `{field}`:',f'- `historical_{field}`:')
            old=old.replace('# 当前：物理目标、采样与固定温度诊断已完成','# 历史：物理目标、采样与固定温度诊断已完成',1)
        prefix='../../' if name.startswith('docs/plans/') else ''
        text=f'''<!-- WA_CURRENT_BEGIN -->
# 当前：连续主稿与固定温度条件演化

{description}

任务 `PCM-20260925-INTEGRATED-MANUSCRIPT-FEASIBILITY-02` 已由用户明确批准实施 W+A，见[授权与边界]({prefix}docs/notes/2026-09-25-integrated-manuscript-conditional-ivp-authorized.md)及[本轮交付]({prefix}paper/paper_revision_20260925_integrated/README.md)。本段 supersedes 下方旧任务的当前状态；旧结果不变。仅至多两条条件轨迹，无新训练、电学求解、参考生成或自动 A+，无 Git 发布授权。

- `phase_id`: `PHK_V23_INTEGRATED_MANUSCRIPT_CONDITIONAL_IVP`
- `lifecycle_state`: `{stage}`
- `blocker_id`: `NONE`
- `claim_status`: `{claim}`
- `next_research_execution_authorized`: `{str(authorized).lower()}`

<!-- WA_CURRENT_END -->

'''
        path.write_text(text+old,encoding='utf-8')
    for name,prefix in [('CODEX_CONTEXT.md',''),('docs/README.md','../')]:
        p=ROOT/name;t=p.read_text(encoding='utf-8')
        if not t.startswith('2026-09-25 W+A'):
            p.write_text(f'2026-09-25 W+A：用户已批准连续主稿与有界条件演化。当前状态以 [active_phase]({prefix}active_phase.md) 和[本轮交付]({prefix}paper/paper_revision_20260925_integrated/README.md)为准；下方旧阶段保留历史身份。\n\n'+t,encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--close',action='store_true');p.add_argument('--claim',default='AUTHORIZED_WA_PREPARATION_NO_NEW_SCIENTIFIC_RESULT');p.add_argument('--description',default='W正文与证据映射准备中；A按冻结合同实现和资格检查。当前无新科学结果，历史 E/F 收益与阴性裁决保持。')
    a=p.parse_args();update('CLOSED' if a.close else 'EXECUTING',a.claim,not a.close,a.description)
