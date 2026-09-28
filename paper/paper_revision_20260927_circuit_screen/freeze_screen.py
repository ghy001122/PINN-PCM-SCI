"""Prepare only the fixed analysis contract and input metadata, without predicting."""
from pathlib import Path
import csv, json, hashlib, zipfile
from datetime import datetime, timezone
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CONFIG=ROOT/'configs/voltage_circuit_screen_20260927.json'
if CONFIG.exists():
    raise FileExistsError('Analysis contract already frozen')
old=HERE.parent/'paper_revision_20260926_core'
contract_path=old/'evidence/core-revision/vo2/frozen-config.json'
contract=json.loads(contract_path.read_text(encoding='utf-8'))
assets=json.loads((old/'literature/data-assets.json').read_text(encoding='utf-8'))
records=next(v for v in assets.values() if isinstance(v,list) and v and isinstance(v[0],dict) and 'archive_member' in v[0])
records=[r for r in records if r['devices']==['1E3','1E2']]
dev=[r for r in records if r['proposed_split']!='COMPLETE_PROTOCOL_HOLDOUT_NOT_SCORED']
sealed=[r['archive_member'] for r in records if r['proposed_split']=='COMPLETE_PROTOCOL_HOLDOUT_NOT_SCORED']
assert len(dev)==5 and len(sealed)==1
qual=[]
for r in dev:
    qual.append(dict(archive_member=r['archive_member'],devices=r['devices'],nominal_source_voltages_V=r['source_voltages_V'],
      RL_ohm=r['load_resistance_ohm'],record_length_from_prior_manifest=r['record_length'],
      legal_voltage=False,interval_drive=False,load_resistance=True,equivalent_topology=False,
      capacitance_known=False,independent_load_measurement=False,independent_device_measurement=False,
      raw_numeric_read_this_task=False,execution='NOT_RUN_INPUT_QUALIFICATION_UNCLOSED',
      measurement='EXPERIMENTAL_OSCILLOSCOPE_BRANCH_UNRESOLVED',sufficiency='UNKNOWN',
      implication='Stop affected circuit comparisons; not evidence that reconstruction fails',
      missing=['50-ohm sensor connection relative to device, capacitance, and reference ground',
        'per-record mapping from CH1/CH4 to the capacitor node without hidden-current correction',
        'record-interval source waveform or explicit constant-bias timing qualification',
        'capacitance for this low-threshold device/cabling configuration (device branch only)',
        'polarity, gain and channel delay qualification at the required accuracy'],
      not_blockers=['initial T/H','pre-record thermal history','tau_task','low-threshold peak rule for waveform scoring'],
      minimal_resolution='Provide a record-specific circuit/channel wiring and bias metadata sheet; do not infer topology by fitting currents'))
units={'time':'s','voltage':'V','temperature':'K','resistance':'ohm','device_current':'A','load_current':'A','capacitor_current':'A',
       'g':'dimensionless','delta':'dimensionless','reversed':'dimensionless','Tr':'K','gr':'dimensionless','Tpr':'K','T_last':'K',
       'net_external_energy_step_J':'J','euler_capacitive_energy_defect_J':'J','discrete_energy_balance_defect_J':'J'}
inputs=[];inventory=[]
for case in contract['cases']:
    for dt,tag in [(1e-9,'1ns'),(.5e-9,'0p5ns')]:
        name=case['id']+'-'+tag
        p=ROOT/'outputs/runs/20260926-core-revision-vo2-bridge/vo2'/(name+'.npz')
        item=dict(id=name,case=case['id'],dt_s=dt,path=p.relative_to(ROOT).as_posix())
        inputs.append(item)
        fields={}
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                with z.open(n) as f:
                    version=np.lib.format.read_magic(f)
                    shape,fortran,dtype=(np.lib.format.read_array_header_1_0(f) if version==(1,0) else np.lib.format.read_array_header_2_0(f))
                key=n.removesuffix('.npy')
                fields[key]=dict(shape=list(shape),dtype=str(dtype),unit=units.get(key,'SOURCE_DEFINED'),
                  role='observation exporter/query axis' if key in ['time','voltage'] else 'scoring or historical background only')
        with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        inventory.append(dict(**item,fields=fields,bytes=p.stat().st_size,sha256=digest,
          file_mtime_utc=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),
          time_extent_s=[0,20e-6],saved_order=contract['scheme']))
stamp=datetime.now(timezone.utc).isoformat()
config=dict(task_id='PCM-20260927-MANUSCRIPT-CIRCUIT-SCREEN-01',baseline='6dd147af757bf5788e9c5d1535b49e7f965b2600',
 frozen_at_utc=stamp,source_contract=contract_path.relative_to(ROOT).as_posix(),
 output=HERE.relative_to(ROOT).as_posix()+'/circuit-screen',simulation_inputs=inputs,
 observation_interval_s=102.4e-9,time_scale_s=1e-6,engineering_safety_factor=64,
 engineering_tolerance='FP64 operation scales in analysis code, current-scale propagation for MSE cancellation; never a scientific accuracy threshold',
 peak_match_max_gap_s=.25e-6,experimental_development_allowlist=[r['archive_member'] for r in dev],
 sealed_member=sealed[0],experimental_qualification=qual,tau_task=None,
 tau_task_reason='No branch-, interval- and application-matched externally justified tolerance identified in the bounded sources before prediction',
 no_parameter_scan=True,no_new_system_integration=True,no_new_training=True,scipy='1.14.1')
CONFIG.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/'input-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
(HERE/'experimental-qualification.json').write_text(json.dumps(qual,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Verify the newly displayed text directly against the unchanged historical CSV.
rows=list(csv.DictReader((old/'tables/fcov-all-effects.csv').open(encoding='utf-8')))
expected={29:['2.14630','1.01558','52.68','0.0241544','0.0199363','17.46'],43:['2.09424','0.70046','66.55','0.0244337','0.0197631','19.12']}
checked=[]
for seed,values in expected.items():
    group={r['metric']:r for r in rows if r['reference']=='spatial' and r['reader']=='fine' and r['comparison']=='E_vs_F_cov' and int(r['seed'])==seed}
    a=group['bottom_current_NRMSE'];b=group['Ephi']
    display=[f"{100*float(a['control']):.5f}",f"{100*float(a['candidate']):.5f}",f"{100*float(a['relative_error_reduction']):.2f}",
      f"{float(b['control']):.7f}",f"{float(b['candidate']):.7f}",f"{100*float(b['relative_error_reduction']):.2f}"]
    assert display==values,(seed,display)
    checked.append(dict(seed=seed,display=display,source_rows=[a,b]))
(HERE/'display-verification.json').write_text(json.dumps(dict(status='VERIFIED',recomputed_historical_scores=False,records=checked),indent=2)+'\n',encoding='utf-8')
print('FROZEN',len(inputs),'saved systems;',len(qual),'experimental records qualified as not executable; display verified')
