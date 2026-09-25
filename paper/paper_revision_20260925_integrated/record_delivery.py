"""Close this approved task after final review artifacts have been checked."""
from pathlib import Path
import json,hashlib,re,sys
from datetime import datetime,timezone
from pinn_pcm_sci.ledger import ExperimentLedger,RunManifest
from paper.paper_revision_20260925_integrated.update_status import update
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
RUN=ROOT/'outputs/runs/20260925-fixed-temperature-phase-probe'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
cfg=read(RUN/'frozen-config.json');result=read(RUN/'result.json');lock=read(RUN/'trajectories-locked.json');cache=read(RUN/'cache-complete.json');closure=read(RUN/'compute-closure.json')
assert closure['instance_shutdown_confirmed'] and read(RUN/'saved-array-verification.json')['passed']
qa=read(HERE/'build/visual-qa.json');assert qa['passed']
manifest=read(HERE/'build/render-manifest.json');inputs=set([HERE/'source/manuscript.md',HERE/'source/supplement.md',HERE/'references.md'])
for p in (HERE/'source').glob('*.md'):
    inputs.update(HERE/'tables'/f'{name}.md' for name in re.findall(r'\{\{TABLE:([^}]+)\}\}',p.read_text(encoding='utf-8')))
for blocks in manifest['documents'].values():inputs.update(Path(b['path']) for b in blocks if b['type']=='image')
assets=[]
for p in sorted(inputs):
    assert p.is_file(),p
    old=HERE.parent/'paper_revision_20260921'/p.relative_to(HERE)
    source=str(old.relative_to(ROOT)).replace('\\','/') if old.is_file() and sha(old)==sha(p) else 'current authoritative source or derived saved-data asset'
    assets.append(dict(path=rel(p),sha256=sha(p),immediate_source=source))
dependencies=dict(authoritative_text=['source/manuscript.md','source/supplement.md'],review_build_inputs=assets,
    equations='Regenerated from formulas in the same Markdown source by prepare_document.py',
    builders=['prepare_document.py','build_docx.py','../advisor_review_20260924/render_with_word.ps1'],
    pdf_derivation='Microsoft Word exports the final DOCX; the PDF and DOCX therefore share one typeset content source.',
    runtime=dict(numeric_and_markdown_preparation='.venv Python 3.11, NumPy, SciPy, Matplotlib',docx='Bundled Python 3.12 with python-docx 1.2.0 and Pillow',pdf='Installed Microsoft Word COM; bundled Poppler 130 dpi for QA',QA='Project PyMuPDF and Pillow'),
    renderer_fallback='Packaged render_docx.py was attempted and failed because Windows LibreOffice was absent. Its traceback is preserved in build/packaged-render.log. The existing project Word renderer was used.',
    historical_figures='Consumed as unchanged saved PNGs; this manuscript build does not rerun their scientific generators.',
    scientific_regeneration=dict(B1_and_physical_figures='paper/paper_revision_20260921/plot_physics.py; outputs/submission-rescore-20260921/manifest.json, outputs/runs/20260921-b1-second-cycle-phase-gap and saved physical-panels.npz',
        common_reader='paper/paper_revision_20260918/report_results.py; outputs/submission-archive-20260918/isolated-rescore',
        objective_diagnostic='paper/observation_preserving_phase_20260924/build_diagnostic_report.py; outputs/runs/20260924-observation-preserving-phase/diagnostic-20260925',
        conditional='finalize_conditional_report.py consumes outputs/runs/20260925-fixed-temperature-phase-probe only; no model queries or propagation'),
    archived_unused_renderer='build_pdf.py is inherited for provenance; it was not used for the delivered PDF.',
    outputs={f'{n}.{ext}':dict(sha256=sha(HERE/f'{n}.{ext}'),bytes=(HERE/f'{n}.{ext}').stat().st_size) for n in ('manuscript','supplement') for ext in ('md','docx','pdf')})
(HERE/'build-dependencies.json').write_text(json.dumps(dependencies,indent=2),encoding='utf-8')
(HERE/'build-and-reproduction.md').write_text('''# Build and reproduction

The authoritative body text is source/manuscript.md and source/supplement.md. Tables, references and saved figures are includes. The top-level Markdown, DOCX and PDF are derived deliverables, not separately maintained bodies.

Run prepare_document.py with the project Python to expand includes and render equations, then build_docx.py with the bundled documents-runtime Python. Export each resulting DOCX through the existing ../advisor_review_20260924/render_with_word.ps1. Copy its checked PDF to the delivery root. Full page images and render logs are retained under build/. The exact consumed inputs, identities, runtime dependencies and output checksums are in build-dependencies.json.

The bundled LibreOffice renderer was attempted once; Windows has no installed LibreOffice. The existing Microsoft Word renderer produced the actual PDF, so DOCX and PDF share typography and pagination. No dependency was installed globally.

Historical figure PNGs are unchanged inputs. Regenerating those figures from raw fields is a separate operation requiring the historical local arrays and original scripts named in build-dependencies.json. Full-array external access is still open. Current conditional figures and the report use the recovered numeric cache; the saved-array verification reproduces all accepted defects and comparison measures without model queries, propagation or training.

The initial preparation and editorial scripts document this revision. Once prepared, edit only the source/ Markdown and referenced tables; do not rerun preparation to overwrite the authoritative prose. Scientific execution is closed and is not part of the document build.
''',encoding='utf-8')
report='''# W+A execution closeout

Task PCM-20260925-INTEGRATED-MANUSCRIPT-FEASIBILITY-02 is complete within the approved W+A scope. W contains a continuous manuscript and full supplement, an evidence map, revision response, build dependencies and checked Markdown/DOCX/PDF review outputs. A contains exactly two complete locked trajectories, all internal states, 265-node exports, unchanged B0 numeric queries and the three separate residual layers, paired heat budgets, endpoint seam vectors, boundary records and gated development-reference analysis.

VERIFIED: 3168 accepted steps, 6361 Newton iterations/linear solves, no clipping; all three numerical gates pass. The phase-step difference RMS is 3.9213970e-5 and right endpoint maximum is 2.9046819e-4. Both thermal conventions are resolved within budget. Full-domain Ephi_D_80 is 0.0669435757 / 0.0207595909 / 0.0207429571 for B0/coarse/fine; the ROI direction agrees. The common phase residual was evaluated by independent second-order time differences. Arrays have no neural AD strong residual.

The active-support diagnostics remain mixed: fine-step recall against the restricted native indicator decreases from 0.974612 to 0.763383, while precision increases from 0.410817 to 0.890215 and symmetric difference decreases. The other restriction/threshold order has the same tradeoff. These are descriptive D-window quantities, not a new strict-event qualification.

SUPPORTED_INTERPRETATION: CONDITIONAL_IVP_SUPPORTS_FURTHER_WITNESS_SEARCH. The sole proposed follow-on is to consider a bounded original-family witness search addressing the saved seams, subject to a separately approved plan. UNKNOWN: original C2-family feasibility and neural-specific phase benefit. Left first-derivative mismatch RMS is 0.49770263; fine right value mismatch RMS is 0.020562588. These are not erased by favorable reference errors. No A+, new training or confirmation has begun.

All results were recovered and verified before shutdown; shutdown returned zero and the subsequent connection was refused. The execution used no new electrical solves or reference generation. A deployment preflight initially omitted an original contract-identity fixture; it ended before any query or scientific step, and the unchanged fixture repair passed the targeted preflight. Full failure and recovery records are retained. GPU peak allocation was not persisted and remains unreported; resource guards did not trigger.

P02 method value, strict two-cycle use, material validation and P03 complete external array access remain open. No Git/data publication or submission was performed. Frozen historical findings and unrelated workspace changes remain outside this delivery.

Links: [delivery](../../paper/paper_revision_20260925_integrated/README.md), [A report](../../paper/paper_revision_20260925_integrated/conditional-evolution-report.md), [result](../../outputs/runs/20260925-fixed-temperature-phase-probe/result.json), [compute closure](../../outputs/runs/20260925-fixed-temperature-phase-probe/compute-closure.json).
'''
closeout=ROOT/'docs/experiment/2026-09-25-integrated-manuscript-conditional-ivp-closeout.md';closeout.write_text(report,encoding='utf-8')
run_id='20260925-fixed-temperature-phase-probe'
record=RunManifest(run_id=run_id,experiment_group_id='PCM-20260925-INTEGRATED-MANUSCRIPT-FEASIBILITY-02',tier='development',scientific_role='TWO_FIXED_TEMPERATURE_CONDITIONAL_TRAJECTORIES',gate='PROSPECTIVE_TWO_STEP_NUMERICAL_QUALIFICATION_THEN_PAIRED_HEAT_REFERENCE_SEAMS',started_at=read(RUN/'run-started.json')['utc'],ended_at=result['utc'],command=['python -m pinn_pcm_sci.phk_v23_conditional_phase_run','python -m pinn_pcm_sci.phk_v23_conditional_phase_evaluate numerical','python -m pinn_pcm_sci.phk_v23_conditional_phase_evaluate reference'],execution_status='COMPLETE',numerical_validity='ALL_THREE_PROSPECTIVE_GATES_PASSED_SAVED_ARRAY_RECONSTRUCTION_PASSED',gate_outcome=result['status'],route_disposition='CLOSE_NO_AUTOMATIC_A_PLUS_OR_NEW_TRAINING',evidence_identity='FROZEN_B1_E29_TEMPERATURE_INITIAL_VALUE_PROBLEM_AT_FIXED_80X40',claim_status='SUPPORTED_INTERPRETATION_FURTHER_WITNESS_SEARCH_ORIGINAL_FAMILY_UNKNOWN',code_identity=read(RUN/'runtime-manifest.json'),environment={**read(RUN/'environment-observation.json'),'instance_shutdown_confirmed':True},physical_contract_id='UNCHANGED_B0_PHK_V21_SHORTER_PROTOCOL',split_id='D_1P36_2P02_POST_LOCK_DEVELOPMENT_REFERENCE_ONLY',method_id='LOGIT_NEWTON_ANALYTIC_JACOBIAN_BACKWARD_EULER',case_id='B1_E29_FROZEN_T',seed=29,planned_budget=cfg,actual_budget=dict(main_steps=3168,newton_iterations=6361,linear_solves=6361,query_work=cache['work'],query_seconds=cache['seconds'],trajectory_seconds={k:v['seconds'] for k,v in lock['trajectories'].items()},electrical_forwards=0,electrical_adjoints=0,reference_generation=0,optimizer_updates=0,preflight_engineering_recoveries=1,scientific_retries=0),checkpoint=dict(parent=cfg['parent'],changed=False),evaluator_id='COMMON_FD_PAIRED_THERMAL_B0_AD_SEAMS_POST_LOCK_VOLUME_RESTRICTION',artifacts=dict(result=rel(RUN/'result.json'),trajectories=rel(RUN/'trajectories-locked.json'),report=rel(HERE/'conditional-evolution-report.md'),manuscript=rel(HERE/'manuscript.md'),compute_closure=rel(RUN/'compute-closure.json'),closeout=rel(closeout)),failure_class=None,replay_of=None,supersedes=None)
ledger=ExperimentLedger(ROOT/'docs/experiment');ledger.record(record)
index=ROOT/'docs/experiment/README.md';text=index.read_text(encoding='utf-8');text=text.replace('最新：[相对相态残差','历史2026-09-23：[相对相态残差',1);text=text.replace('# Experiment ledger protocol\n','# Experiment ledger protocol\n\n最新：[W+A 连续成稿与条件演化收口](2026-09-25-integrated-manuscript-conditional-ivp-closeout.md)。两条轨迹数值资格通过；支持考虑原修正族证人搜索，原族可行性仍未知；实例已回收关闭。\n',1);index.write_text(text,encoding='utf-8')
update('CLOSED','WA_COMPLETE_CONDITIONAL_IVP_SUPPORTS_FURTHER_WITNESS_SEARCH_ORIGINAL_FAMILY_UNKNOWN',False,'W连续主稿与完整补充材料已完成；A两条轨迹完成并通过数值资格，两热口径及开发参考方向支持后续证人搜索，但原C²修正族可行性仍为UNKNOWN。结果已回收核验、实例已关闭。无自动A+、新训练或发布。')
(HERE/'README.md').write_text(f'''# W+A integrated manuscript delivery

Task PCM-20260925-INTEGRATED-MANUSCRIPT-FEASIBILITY-02 is CLOSED. All outputs are local review deliverables.

- Main manuscript: [PDF](manuscript.pdf), [DOCX](manuscript.docx), [Markdown](manuscript.md).
- Complete supplement: [PDF](supplement.pdf), [DOCX](supplement.docx), [Markdown](supplement.md).
- [Revision response](revision-response.md), [claim and evidence map](claim_evidence_matrix.md), [build and reproduction](build-and-reproduction.md), [exact dependencies](build-dependencies.json).
- [Conditional evolution report](conditional-evolution-report.md), [locked result](../../outputs/runs/20260925-fixed-temperature-phase-probe/result.json), [saved-array verification](../../outputs/runs/20260925-fixed-temperature-phase-probe/saved-array-verification.json), [recovery and shutdown](../../outputs/runs/20260925-fixed-temperature-phase-probe/compute-closure.json).

VERIFIED: both trajectories completed; numerical gates and two thermal conventions passed. Full-domain phase RMS on the new D/80 measure is 0.0669436 (B0), 0.0207596 (coarse) and 0.0207430 (fine); ROI agrees. SUPPORTED_INTERPRETATION: consider a bounded original-family witness search. UNKNOWN: original C2-family feasibility; nonzero endpoint seams remain. No new neural training or original-family certificate is claimed.

The final documents have {qa['page_counts']['manuscript']} and {qa['page_counts']['supplement']} pages. One Markdown source per document supplies every format; prior evidence stays frozen. The GPU instance was shut down after verified recovery. P02, strict two-cycle use, material validation and P03 full-array external access remain open. This delivery includes no Git publication, data release or submission.
''',encoding='utf-8')
print('WA_DELIVERY_RECORDED_AND_CLOSED')
