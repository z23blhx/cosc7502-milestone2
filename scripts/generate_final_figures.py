#!/usr/bin/env python3
"""Read immutable raw CSVs, validate them, and build the six presentation figures.

No benchmark is executed and no file under results/ is written. Matplotlib is
the sole extra dependency. Figure values and source hashes accompany the PNGs.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics as st
import textwrap
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[1]
CPU_INITIAL='results/openmp-benchmark-623308/formal.csv'
CPU_LONG='results/openmp-vector-623318/vector.csv'
GPU_MAIN='results/cuda-comparison-623453/main.csv'
GPU_GENS='results/cuda-comparison-623453/generations.csv'
SOURCES=[CPU_INITIAL,CPU_LONG,GPU_MAIN,GPU_GENS]
COLORS={'cpu':'#315E91','gpu':'#C27624','negative':'#777777','reference':'#333333'}

def need(condition,message):
    if not condition: raise ValueError(message)

def load(relative):
    path=ROOT/relative
    with path.open(newline='',encoding='utf-8') as source: rows=list(csv.DictReader(source))
    need(bool(rows),'empty source '+relative)
    groups=defaultdict(list); states=defaultdict(set)
    need(len({(r['job_id'],r['node'],r['commit']) for r in rows})==1,'mixed provenance '+relative)
    for r in rows:
        need(r['density']=='35' and r['seed']=='12345','inconsistent initial conditions')
        need(r['width']==r['height'],'unexpected non-square benchmark')
        need(r['phase']=={'formal.csv':'formal','vector.csv':'vector','main.csv':'main','generations.csv':'generations'}[path.name],'mixed phase')
        key=tuple(r.get(k,'') for k in ('width','height','generations','backend','version','threads','chunk','binding','block_x','block_y'))
        groups[key].append(r)
        states[(r['width'],r['height'],r['generations'])].add((r['live_cells'],r['checksum']))
        metrics=['elapsed_seconds'] if 'elapsed_seconds' in r else (['cpu_seconds'] if r['backend']!='cuda' else ['simulation_seconds','kernel_event_seconds','gpu_e2e_seconds','h2d_seconds','d2h_seconds'])
        for metric in metrics:
            value=float(r[metric]); need(math.isfinite(value) and value>0,'invalid time '+metric)
        if r['backend']=='cuda':
            need(float(r['gpu_e2e_seconds'])>=float(r['simulation_seconds']),'invalid timing boundaries')
            need(int(r['device_bytes'])==2*int(r['width'])*int(r['height']),'wrong buffer footprint')
            need(r['threads']=='0','GPU reported CPU team')
        elif 'requested_threads' in r:
            need(r['threads']==r['requested_threads'],'wrong CPU team')
    need(all(len(v)==1 for v in states.values()),'state mismatch')
    expected={CPU_INITIAL:(340,68),CPU_LONG:(200,40),GPU_MAIN:(120,24),GPU_GENS:(80,16)}[relative]
    need((len(rows),len(groups))==expected,'incomplete matrix '+relative)
    need(all(sorted(int(r['rep']) for r in samples)==[1,2,3,4,5] for samples in groups.values()),'duplicate/missing repetitions')
    return rows

def select(data,source,n,g,backend,threads,metric=None):
    rows=[r for r in data[source] if (r['width'],r['generations'],r['backend'],r['threads'])==(str(n),str(g),backend,str(threads))]
    rows=[r for r in rows if r.get('chunk','0') in ('','0') and r.get('binding','close') in ('','close')]
    need(len(rows)==5,'selection not a unique five-sample group')
    metric=metric or ('elapsed_seconds' if 'elapsed_seconds' in rows[0] else 'cpu_seconds')
    vals=[float(r[metric]) for r in rows]
    return {'source':source,'commit':rows[0]['commit'],'job_id':rows[0]['job_id'],
            'node':rows[0]['node'],'width':n,'height':n,'generations':g,
            'backend':backend,'version':rows[0]['version'],'threads':threads,
            'block_x':rows[0].get('block_x',''),'block_y':rows[0].get('block_y',''),
            'metric':metric,'samples_seconds':vals,'median_seconds':st.median(vals),
            'mean_seconds':st.mean(vals),'min_seconds':min(vals),'max_seconds':max(vals),
            'sample_sd_seconds':st.stdev(vals)}

def produce(output,table_path,render=True):
    data={source:load(source) for source in SOURCES}
    initial=[select(data,CPU_INITIAL,2048,53,b,t) for b,t in [('serial',1),('omp',8),('omp-persistent',8),('omp-interior',8),('omp-simd',8)]]
    later=[select(data,CPU_LONG,4096,64,b,t) for b,t in [('serial',1),('omp',8),('omp-simd',8),('omp-vector',8)]]
    scaling=[select(data,CPU_LONG,4096,64,'omp-vector',t) for t in [1,2,4,8]]
    # GPU groups have the same backend/team but differ in version; select explicitly.
    def gpu(n,g,version,metric,source=GPU_MAIN):
        filtered={**data,source:[r for r in data[source] if r['version']==version]}
        return select(filtered,source,n,g,'cuda',0,metric)
    cuda=[gpu(2048,256,v,'simulation_seconds') for v in ['cuda_naive_v1','cuda_direct_v2','cuda_shared_v3']]
    sizes=[(512,4096),(1024,1024),(2048,256),(4096,64)]
    cpu=[select(data,GPU_MAIN,n,g,'omp-vector',8) for n,g in sizes]
    e2e=[gpu(n,g,'cuda_direct_v2','gpu_e2e_seconds') for n,g in sizes]
    gen_cpu=[select(data,GPU_GENS,1024,g,'omp-vector',8) for g in [1,10,100,1000]]
    gen_sim=[gpu(1024,g,'cuda_direct_v2','simulation_seconds',GPU_GENS) for g in [1,10,100,1000]]
    gen_e2e=[gpu(1024,g,'cuda_direct_v2','gpu_e2e_seconds',GPU_GENS) for g in [1,10,100,1000]]
    manifests={
        'cpu_optimization_progression':initial+later,
        'openmp_strong_scaling_runtime':scaling,
        'openmp_strong_scaling_speedup':scaling,
        'cuda_kernel_comparison':cuda,
        'cpu_vs_cuda':cpu+e2e,
        'cuda_generation_amortization':gen_cpu+gen_sim+gen_e2e}
    t1=scaling[0]['median_seconds']; t8=scaling[-1]['median_seconds']
    ratios={'v5_thread_scaling':t1/t8,'v5_efficiency_percent':100*t1/t8/8,
            'v5_serial_relative_overall':later[0]['median_seconds']/t8,
            'persistent_slowdown_percent':100*(initial[2]['median_seconds']/initial[1]['median_seconds']-1),
            'omp8_over_gpu_e2e_2048':cpu[2]['median_seconds']/e2e[2]['median_seconds'],
            'naive_over_direct_simulation_2048':cuda[0]['median_seconds']/cuda[1]['median_seconds'],
            'shared_over_direct_simulation_2048':cuda[2]['median_seconds']/cuda[1]['median_seconds']}
    output.mkdir(parents=True,exist_ok=True)
    provenance={'sources':{s:{'sha256':hashlib.sha256((ROOT/s).read_bytes()).hexdigest()} for s in SOURCES},'figures':manifests,'ratios':ratios}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    lines=['# Presentation source of truth','',
           'Generated directly from immutable raw CSVs by `scripts/generate_final_figures.py`. All groups contain five timed repetitions. Values below are medians in seconds, with unrounded values preserved in `figures/provenance.json`. No benchmark is rerun.','',
           'CPU timers include generation work, team entry and barriers, excluding setup/checksum. CUDA simulation includes ordered launches and final synchronization. CUDA steady-context E2E includes allocation/events/transfers/cleanup, excluding context initialization, host output allocation and result import/checksum. Event interval includes launch gaps and is not summed kernel duration.','',
           '## Figure datasets','',
           '| Figure | Raw source |','|---|---|']
    for name,rows in manifests.items():
        sources=list(dict.fromkeys(r['source'] for r in rows))
        lines.append('| [{}](figures/{}.png) | {} |'.format(name,name,'; '.join('`'+s+'`' for s in sources)))
    for title,rows in [('Initial CPU progression, only 2048²×53',initial),('Later CPU progression, only 4096²×64',later),('v5 strong scaling, 4096²×64',scaling),('CUDA comparison, 2048²×256',cuda),('CPU/GPU practical comparison',cpu+e2e),('Generation amortization, 1024²',gen_cpu+gen_sim+gen_e2e)]:
        lines+=['','## '+title,'','| Workload | Version | Threads / block | Median seconds | Timing column | Source |','|---|---|---|---:|---|---|']
        for r in rows:
            team='{}×{}'.format(r['block_x'],r['block_y']) if r['backend']=='cuda' else str(r['threads'])
            lines.append('| {width}²×{generations} | `{version}` | {team} | {median_seconds:.9f} | `{metric}` | `{source}` |'.format(team=team,**r))
    lines+=['','## Ratios and allowed wording','',
            '| Claim | Unrounded ratio | Allowed rounded wording |','|---|---:|---|',
            '| v5 T1/T8 | {:.12f} | {:.2f}× pure thread scaling |'.format(ratios['v5_thread_scaling'],ratios['v5_thread_scaling']),
            '| (v5 T1/T8)/8 | {:.12f}% | {:.1f}% efficiency |'.format(ratios['v5_efficiency_percent'],ratios['v5_efficiency_percent']),
            '| serial / v5 T8 | {:.12f} | {:.2f}× serial-relative overall CPU speedup |'.format(ratios['v5_serial_relative_overall'],ratios['v5_serial_relative_overall']),
            '| OMP8 / direct E2E, 2048²×256 | {:.12f} | {:.2f}×, same job/workload |'.format(ratios['omp8_over_gpu_e2e_2048'],ratios['omp8_over_gpu_e2e_2048']),
            '| persistent / original rows minus 1 | {:.12f}% | {:.1f}% slower, tested implementation |'.format(ratios['persistent_slowdown_percent'],ratios['persistent_slowdown_percent']),
            '',
            'Min–max whiskers show observed sample spread, not confidence intervals. Thread-scaling plot uses v5 T1, never the serial reference. CPU progression panels have independently labelled seconds axes and incompatible generation counts: compare within a panel only. CPU/GPU size series holds total cell updates constant, not generations. Near-parity small GPU claims and unmatched cross-job ratios are excluded.','',
            '## Compiler / profiler evidence','',
            '- `results/openmp-vector-623318/vector.txt`: GCC8 control-flow blocker for v4 and vectorized 16-byte interior loop for v5. This supports generated vectorization, not its isolated causal speedup.',
            '- `results/cuda-profile-623467/ncu-direct.txt`, `ncu-shared.txt`: single first-generation profiles at 2048², 16×16. Direct 54.272 µs, occupancy 82.62%; shared 114.176 µs, occupancy 92.66%. These are separate from the median simulation bars.',
            '- `results/cuda-comparison-623453` and `results/cuda-crossover-623470`: one-generation 1024² OMP8/E2E ratios fall on opposite sides of parity. No universal crossover claim.',
            '',
            'Narration and slide labels use this file for rounding. Each source SHA and measured commit is recorded in provenance.json. Retain all raw samples and original timestamps.']
    table_path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if not render: return provenance
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':17,'axes.titlesize':22,
                         'axes.labelsize':18,'xtick.labelsize':16,'ytick.labelsize':16,
                         'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none',
                         'figure.facecolor':'white','axes.edgecolor':'#555555','text.color':'#252525',
                         'svg.hashsalt':'cosc7502-milestone2-final-figures'})
    def style(ax):
        ax.grid(axis='y',color='#DDDDDD',linewidth=.7); ax.set_axisbelow(True)
    def save(fig,name,subtitle):
        fig.text(.06,.035,'\n'.join(textwrap.wrap(subtitle,118)),fontsize=13,color='#555555')
        fig.subplots_adjust(left=.12,right=.95,bottom=.20,top=.83)
        fig.savefig(output/(name+'.png'),dpi=160)
        svg_path=output/(name+'.svg')
        fig.savefig(svg_path,metadata={'Date':None})
        # Normalize generated SVG formatting only. Archive files are never written.
        # Fixed IDs and no generated date make repeated exports reproducible.
        content='\n'.join(line.rstrip() for line in svg_path.read_text(encoding='utf-8').splitlines())+'\n'
        with svg_path.open('w',encoding='utf-8',newline='\n') as destination:
            destination.write(content)
        plt.close(fig)
    def values(rows,factor=1): return [r['median_seconds']*factor for r in rows]
    def spread(rows,factor=1): return [[(r['median_seconds']-r['min_seconds'])*factor for r in rows],[(r['max_seconds']-r['median_seconds'])*factor for r in rows]]
    fig,axes=plt.subplots(1,2,figsize=(16,9))
    for ax,rows,title,labels in [(axes[0],initial,'Initial experiment\n2048² × 53 generations',['Serial (T1)','Rows v1 (T8)','Persistent v2 (T8)','Interior v3 (T8)','SIMD v4 (T8)']),
                               (axes[1],later,'Independent follow-up\n4096² × 64 generations',['Serial (T1)','Rows v1 (T8)','SIMD v4 (T8)','Branch-free v5 (T8)'])]:
        yy=list(range(len(rows))); vv=values(rows)
        ax.barh(yy,vv,xerr=spread(rows),color=[COLORS['reference']]+[COLORS['cpu']]*(len(rows)-1),capsize=4,height=.55)
        ax.set_yticks(yy,labels,fontsize=14); ax.invert_yaxis(); ax.set_xlim(0,max(vv)*1.28)
        for y,v in zip(yy,vv): ax.text(v+max(vv)*.035,y,'{:.3f}'.format(v),va='center',fontsize=14)
        ax.set_xlabel('Median simulation time (s)'); ax.set_title(title,pad=20)
        ax.grid(axis='x',color='#DDDDDD',linewidth=.7); ax.set_axisbelow(True)
    fig.suptitle('CPU optimization evidence in two controlled experiments',fontsize=25,y=.97)
    fig.subplots_adjust(wspace=.8)
    save(fig,'cpu_optimization_progression','Compare within each panel only. Different workloads and axis ranges. Whiskers: min–max, n=5.')
    fig,ax=plt.subplots(figsize=(14,8)); ts=[1,2,4,8]
    ax.errorbar(ts,values(scaling),yerr=spread(scaling),marker='o',color=COLORS['cpu'],capsize=6,linewidth=2.5)
    for t,v in zip(ts,values(scaling)): ax.annotate('{:.3f} s'.format(v),(t,v),xytext=(6,12),textcoords='offset points')
    ax.set(xticks=ts,xlim=(.5,8.8),ylim=(0,t1*1.18),xlabel='Allocated / actual threads',ylabel='Median simulation time (s)',title='OpenMP v5 runtime, 4096² × 64 generations'); style(ax)
    save(fig,'openmp_strong_scaling_runtime','Rangpur job 623318. Same kernel/workload/binding. Whiskers: observed min–max, n=5.')
    fig,ax=plt.subplots(figsize=(14,8)); speed=[t1/v for v in values(scaling)]
    ax.plot(ts,ts,'--',color=COLORS['reference'],linewidth=2,label='Ideal p-thread scaling')
    ax.plot(ts,speed,'o-',color=COLORS['cpu'],linewidth=2.5,label='v5 T1 / Tp')
    for t,v in zip(ts,speed): ax.annotate('{:.3f}×'.format(v),(t,v),xytext=(8,-24),textcoords='offset points')
    ax.set(xticks=ts,xlim=(.5,8.8),ylim=(0,9),xlabel='Allocated / actual threads',ylabel='Speedup relative to v5 T1',title='OpenMP strong scaling, 4096² × 64 generations'); ax.legend(loc='upper left'); style(ax)
    save(fig,'openmp_strong_scaling_speedup','Ratios of five-sample medians. T1→T8: {:.3f}×; efficiency {:.2f}%. Serial is not the baseline.'.format(ratios['v5_thread_scaling'],ratios['v5_efficiency_percent']))
    fig,ax=plt.subplots(figsize=(14,8)); labels=['Naive v1\n32×16','Direct v2\n16×16','Shared v3\n16×16']
    vv=values(cuda,1000); ax.bar(labels,vv,yerr=spread(cuda,1000),capsize=6,color=[COLORS['cpu'],COLORS['gpu'],COLORS['negative']],width=.55)
    for i,v in enumerate(vv): ax.text(i,cuda[i]['max_seconds']*1000+max(vv)*.07,'{:.2f} ms'.format(v),ha='center')
    ax.set(ylim=(0,max(r['max_seconds'] for r in cuda)*1300),ylabel='Median synchronized simulation time (ms)',title='CUDA versions, 2048² × 256 generations'); style(ax)
    save(fig,'cuda_kernel_comparison','A100, job 623453. Blocks fixed by earlier tuning. Whiskers: min–max, n=5. Shared is slower here.')
    fig,ax=plt.subplots(figsize=(14,8)); xx=list(range(4))
    for rows,offset,label,color in [(cpu,-.18,'Optimized OpenMP8',COLORS['cpu']),(e2e,.18,'CUDA direct, steady-context E2E',COLORS['gpu'])]:
        pos=[x+offset for x in xx]; vv=values(rows,1000)
        ax.bar(pos,vv,.34,label=label,color=color,yerr=spread(rows,1000),capsize=4,hatch='//' if offset>0 else None)
        for x,v,row in zip(pos,vv,rows): ax.text(x,row['max_seconds']*1000+3,'{:.1f}'.format(v),ha='center',fontsize=14)
    ax.set_xticks(xx,['{}²\n{:,} gen.'.format(n,g) for n,g in sizes])
    ax.set(ylim=(0,max(r['max_seconds'] for r in cpu)*1250),ylabel='Median time (ms)',title='Optimized CPU versus CUDA, identical workloads'); style(ax)
    ax.legend(loc='upper right',fontsize=15)
    save(fig,'cpu_vs_cuda','Job 623453. Fixed 2³⁰ cell updates per size. E2E includes transfers/cleanup, excludes cold context. Min–max, n=5.')
    fig,ax=plt.subplots(figsize=(14,8)); gs=[1,10,100,1000]
    for rows,label,color,marker,dash in [(gen_cpu,'OpenMP8 simulation',COLORS['cpu'],'o','-'),(gen_e2e,'CUDA direct steady-context E2E',COLORS['gpu'],'s','-'),(gen_sim,'CUDA synchronized simulation',COLORS['reference'],'^','--')]:
        ax.errorbar(gs,values(rows,1000),yerr=spread(rows,1000),label=label,color=color,marker=marker,linestyle=dash,capsize=4,linewidth=2)
    ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xticks(gs,[str(g) for g in gs])
    ax.set(xlim=(.7,1400),xlabel='Generations (log scale)',ylabel='Median time (ms, log scale)',title='Generation-count amortization, fixed 1024² grid'); ax.legend(loc='upper left',fontsize=15); style(ax)
    save(fig,'cuda_generation_amortization','Job 623453. Only four measured counts. Min–max, n=5. Near one-generation parity is not a robust crossover.')
    return provenance

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--validate-only',action='store_true')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'presentation/figures')
    parser.add_argument('--table',type=Path,default=ROOT/'presentation/final-results.md')
    args=parser.parse_args()
    result=produce(args.output_dir,args.table,not args.validate_only)
    print(json.dumps(result['ratios'],indent=2))
