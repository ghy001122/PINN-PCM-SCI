"""Render the locked, saved comparison results; never fit or rescore a model.

All seven roles and both saved source step sizes are retained. The prespecified
12.5 V/A zoom is centered on the 1 ns source's first recorded detector peak;
both columns use that same absolute time window (no event alignment).
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
COLORS = {'source': '#242424', 'PCHIP': '#197a8c', 'CS': '#ce642e'}
CASE_LABEL = {'single_9V': 'Single device, 9 V', 'single_12p5V': 'Single device, 12.5 V',
              'single_15p8V': 'Single device, 15.8 V',
              'pair_excitation': 'Coupled excitation, inputs 11 / 9.4 V',
              'pair_inhibition': 'Coupled inhibition, inputs 11 / 14 V'}
ROLE_ORDER = [('single_9V','A'),('single_12p5V','A'),('single_15p8V','A'),
              ('pair_excitation','A'),('pair_excitation','B'),
              ('pair_inhibition','A'),('pair_inhibition','B')]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def read_csv(path):
    with path.open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))


def finish_figure(fig, path, title, subtitle, footnote):
    fig.suptitle(title, fontsize=15, fontweight='bold', y=.98)
    fig.text(.5,.948,subtitle,ha='center',va='top',fontsize=10,color='#333333')
    fig.text(.065,.022,footnote,ha='left',va='bottom',fontsize=9,color='#444444')
    fig.subplots_adjust(left=.08,right=.985,bottom=.095,top=.865,hspace=.32,wspace=.22)
    fig.savefig(path,dpi=180,facecolor='white')
    plt.close(fig)


def style_axes(axes):
    for ax in np.asarray(axes).flat:
        ax.grid(True,alpha=.17,linewidth=.7)
        ax.spines[['top','right']].set_visible(False)
        ax.yaxis.set_major_locator(MaxNLocator(5))
        ax.tick_params(labelsize=9)
        ax.margins(x=0, y=.09)


def waveform(records, loaded, case, role, output, zoom=None):
    j=ord(role)-65
    fig,axes=plt.subplots(3,2,figsize=(13.4,9.5),sharex='col')
    style_axes(axes)
    panels=[('voltage',1.,'Voltage (V)'),('device_current',1e3,'Device current (mA)'),
            ('load_current',1e3,'Load current (mA)')]
    for column,item in enumerate(records):
        original,predictions=loaded[column];t=original['time']
        selected=np.ones(len(t),dtype=bool) if zoom is None else (t>=zoom[0])&(t<=zoom[1])
        for row,(field,scale,ylabel) in enumerate(panels):
            ax=axes[row,column]
            ax.plot(t[selected]*1e6,original[field][selected,j]*scale,color=COLORS['source'],
                    lw=1.3,label='Saved source',zorder=2)
            for method in ('PCHIP','CS'):
                ax.plot(t[selected]*1e6,predictions[method][field][selected,j]*scale,
                        color=COLORS[method],lw=1.05,alpha=.9,label=method,zorder=3)
            if row==0:
                s=original['observation_time'];v=original['observation_voltage'][:,j]
                obs=np.ones(len(s),dtype=bool) if zoom is None else (s>=zoom[0])&(s<=zoom[1])
                ax.scatter(s[obs]*1e6,v[obs],s=13 if zoom is None else 26,marker='o',
                           facecolors='white',edgecolors='#303030',linewidths=.6,
                           label='Voltage observations',zorder=4)
                ax.set_title(f"Saved source step: {item['dt_s']*1e9:g} ns",fontsize=11,pad=10)
            if column==0:ax.set_ylabel(ylabel,fontsize=10)
            if row==2:ax.set_xlabel('Absolute time (µs)',fontsize=10)
            if zoom is not None:ax.set_xlim(zoom[0]*1e6,zoom[1]*1e6)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.927),
               fontsize=9,ncol=4,frameon=False)
    title=f"{CASE_LABEL[case]} — role {role}"
    if zoom is None:
        subtitle='Full saved native trajectories; identical finite voltage observations for both reconstructions'
        note='Device and load currents are different branches. Markers are voltage observations only. No current observations are supplied.'
    else:
        subtitle=f"Prespecified first-peak view: {zoom[0]*1e6:.4f}–{zoom[1]*1e6:.4f} µs; same absolute window in both columns"
        note='Center: first 1 ns source peak from the frozen detector; ±0.25 µs. Display only: all scores use the complete declared windows.'
    finish_figure(fig,output,title,subtitle,note)


def energy_plot(records, case, role, cumulative, intervals, output):
    fig,axes=plt.subplots(2,2,figsize=(13.4,7.5),sharex='col')
    style_axes(axes)
    for column,item in enumerate(records):
        for method in ('PCHIP','CS'):
            top=[r for r in cumulative if r['id']==item['id'] and r['device']==role and r['method']==method]
            bottom=[r for r in intervals if r['id']==item['id'] and r['device']==role and r['method']==method]
            if len(top)!=197 or len(bottom)!=196:
                raise ValueError('Energy display requires all frozen boundaries and intervals')
            axes[0,column].plot([float(r['time_s'])*1e6 for r in top],
                               [float(r['signed_error_J'])*1e9 for r in top],
                               lw=1.25,color=COLORS[method],label=method)
            edges=np.array([float(r['left_s']) for r in bottom]+[float(bottom[-1]['right_s'])])*1e6
            values=np.array([float(r['signed_error_J'])*1e9 for r in bottom])
            # One level per actual interval, preserving its real width (last32 ns).
            axes[1,column].stairs(values,edges,lw=1.0,color=COLORS[method],label=method)
        for row in (0,1):
            axes[row,column].axhline(0.,color='#777777',lw=.75,zorder=0)
            axes[row,column].ticklabel_format(axis='y',style='sci',scilimits=(-3,3),useOffset=False)
        axes[0,column].set_title(f"Saved source step: {item['dt_s']*1e9:g} ns",fontsize=11,pad=10)
        axes[0,column].legend(loc='best',fontsize=9,framealpha=.9)
        axes[1,column].set_xlabel('Absolute time (µs)',fontsize=10)
    axes[0,0].set_ylabel('Cumulative signed energy error (nJ)',fontsize=10)
    axes[1,0].set_ylabel('Signed interval energy error (nJ)',fontsize=10)
    finish_figure(fig,output,f"Energy timing: {CASE_LABEL[case]} — role {role}",
        'ΔW = polynomial prediction − piecewise-linear saved power reference; both signs retained',
        'Prediction: analytic integral of p·I_device. Reference: linear interpolation of saved V·I_device. All 196 intervals; final interval 32 ns.')


def contact_sheet(paths,target,label):
    thumb_width,thumb_height=620,460
    columns,rows=2,(len(paths)+1)//2
    sheet=Image.new('RGB',(columns*thumb_width,rows*(thumb_height+34)+50),'white')
    draw=ImageDraw.Draw(sheet);draw.text((12,12),label,fill='black')
    for k,path in enumerate(paths):
        with Image.open(path) as opened:
            thumb=opened.convert('RGB');thumb.thumbnail((thumb_width-10,thumb_height))
        x=(k%columns)*thumb_width;y=50+(k//columns)*(thumb_height+34)
        draw.text((x+5,y),path.name,fill='black');sheet.paste(thumb,(x+5,y+28))
    sheet.save(target)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(HERE/'scoring-subset'))
    parser.add_argument('--results-dir');args=parser.parse_args()
    root=Path(args.root).resolve();results_dir=Path(args.results_dir).resolve() if args.results_dir else root/'results'
    config=read_json(root/'config.json');results=read_json(results_dir/'results.json')
    if results['scientific_status']!='VERIFIED_SAVED_ARRAY_COMPARISON_ABSOLUTE_SUFFICIENCY_UNKNOWN':
        raise ValueError('Valid completed scoring is required before rendering')
    sys.path.insert(0,str(root/'scripts'))
    spec=importlib.util.spec_from_file_location('saved_cubic_comparison',root/'scripts'/'run_cubic_energy_comparison.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    cumulative=read_csv(results_dir/'energy-cumulative.csv');intervals=read_csv(results_dir/'energy-intervals.csv')
    plt.rcParams.update({'font.family':'DejaVu Sans','path.simplify':False,'axes.unicode_minus':True})
    figures=HERE/'figures';build=HERE/'build';figures.mkdir(exist_ok=True);build.mkdir(exist_ok=True)
    wave_paths=[];energy_paths=[];zoom_record=None
    for case,role in ROLE_ORDER:
        records=sorted([r for r in config['records'] if r['case']==case],key=lambda r:r['dt_s'],reverse=True)
        if len(records)!=2:raise ValueError('Both frozen source steps required')
        loaded=[module.loaded_record(root,item) for item in records]
        wave=figures/f'circuit-waveform-{case}-{role}.png'
        waveform(records,loaded,case,role,wave);wave_paths.append(wave)
        energy=figures/f'circuit-energy-{case}-{role}.png'
        energy_plot(records,case,role,cumulative,intervals,energy);energy_paths.append(energy)
        if (case,role)==('single_12p5V','A'):
            record=next(r for r in results['records'] if r['id']==records[0]['id'])
            peak=record['devices'][0]['methods']['PCHIP']['peaks']['full']['reference_first_peak_s']
            if peak is None:raise ValueError('Prespecified source has no detected first peak')
            bounds=(max(0.,peak-.25e-6),min(20e-6,peak+.25e-6))
            zoom=figures/'circuit-waveform-single_12p5V-A-first-peak.png'
            waveform(records,loaded,case,role,zoom,bounds);wave_paths.append(zoom)
            zoom_record={'source_id':records[0]['id'],'first_reference_peak_s':peak,'bounds_s':bounds,
                         'both_columns_share_same_absolute_time_window':True,'used_for_score':False}
        del loaded
    contact_sheet(wave_paths,build/'figure-review-waveforms.png','All saved waveform views; both source steps and all 7 roles')
    contact_sheet(energy_paths,build/'figure-review-energy.png','All 7 role energy views; signed cumulative and 196 interval errors')
    files=[]
    for path in wave_paths+energy_paths:
        with Image.open(path) as im:width,height=im.size
        files.append({'path':path.relative_to(HERE).as_posix(),'bytes':path.stat().st_size,
                      'width':width,'height':height,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest={'generated_at':datetime.now(timezone.utc).isoformat(),'source_root':str(root),'results_directory':str(results_dir),
              'figures':files,'prespecified_zoom':zoom_record,'new_interpolation_fits':0,'new_scoring_runs':0,
              'read_only_saved_arrays':True,'no_waveform_alignment':True,'current_observations_drawn':False,
              'visual_review_status':'PENDING_ACTUAL_IMAGE_INSPECTION'}
    (build/'figure-review-generation.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'figures':len(files),'output':str(figures),'zoom':zoom_record}))


if __name__=='__main__':main()
