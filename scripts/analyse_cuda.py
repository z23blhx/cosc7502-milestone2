#!/usr/bin/env python3
"""Validate complete experiments; summarize without dropping samples or mixing workloads."""
import argparse
import csv
import json
import math
import pathlib
import statistics as stats
from collections import defaultdict

KEY = ('phase','width','height','generations','backend','version','threads','block_x','block_y')
METRICS = ('cpu_seconds','simulation_seconds','kernel_event_seconds','gpu_e2e_seconds','h2d_seconds','d2h_seconds')

def analyse(path):
    with path.open(newline='') as source:
        rows=list(csv.DictReader(source))
    groups=defaultdict(list); states=defaultdict(set)
    assert rows, 'empty experiment'
    assert len({(r['job_id'],r['node'],r['commit']) for r in rows})==1, 'mixed identity'
    for r in rows:
        assert r['density']=='35' and r['seed']=='12345'
        states[(r['width'],r['height'],r['generations'])].add((r['live_cells'],r['checksum']))
        if r['backend']=='cuda':
            assert int(r['device_bytes'])==2*int(r['width'])*int(r['height'])
            assert r['threads']=='0'
            assert float(r['gpu_e2e_seconds'])>=float(r['simulation_seconds'])
        for m in METRICS:
            if r.get(m):
                v=float(r[m]); assert math.isfinite(v) and v>0, (m,v)
        groups[tuple(r[k] for k in KEY)].append(r)
    assert all(len(s)==1 for s in states.values()), 'final states disagree'
    summaries=[]
    for key,samples in groups.items():
        assert sorted(int(r['rep']) for r in samples)==[1,2,3,4,5], 'missing/duplicate repetitions'
        summary=dict(zip(KEY,key)); summary['samples']=5
        for metric in METRICS:
            values=[float(r[metric]) for r in samples if r.get(metric)]
            if values:
                assert len(values)==5
                for name,value in [('mean',stats.mean(values)),('median',stats.median(values)),('min',min(values)),('sample_sd',stats.stdev(values))]:
                    summary[metric+'_'+name]=value
        summaries.append(summary)
    with path.with_name(path.stem+'-warmups.csv').open(newline='') as source:
        warm=list(csv.DictReader(source))
    assert len(warm)==len(groups) and all(r['rep']=='0' for r in warm)
    assert {tuple(r[k] for k in KEY) for r in warm}==set(groups)
    for r in warm:
        assert (r['live_cells'],r['checksum']) in states[(r['width'],r['height'],r['generations'])]
    for s in summaries:
        if s['backend']!='cuda': continue
        peers=[p for p in summaries if all(p[k]==s[k] for k in ('phase','width','height','generations'))]
        for backend,threads,label in [('serial','1','serial'),('omp-vector','1','cpu1'),('omp-vector','8','omp8')]:
            cpu=next((p for p in peers if p['backend']==backend and p['threads']==threads),None)
            if cpu:
                for metric,label_suffix in [('simulation_seconds','simulation'),('gpu_e2e_seconds','e2e')]:
                    s[label+'_speedup_'+label_suffix]=cpu['cpu_seconds_median']/s[metric+'_median']
    fields=list(KEY)+['samples']+sorted({k for s in summaries for k in s if k not in KEY and k!='samples'})
    with path.with_name(path.stem+'-summary.csv').open('w',newline='') as target:
        writer=csv.DictWriter(target,fieldnames=fields); writer.writeheader(); writer.writerows(summaries)
    if rows[0]['phase']=='tuning':
        candidates=[s for s in summaries if s['width']=='2048' and s['generations']=='128']
        winners={kernel:min((s for s in candidates if s['version']=='cuda_'+kernel+'_v'+str(i)),key=lambda s:s['simulation_seconds_median']) for i,kernel in enumerate(['naive','direct','shared'],1)}
        best=min(winners,key=lambda k:winners[k]['simulation_seconds_median'])
        selection={'criterion':'2048x2048,128 generations; minimum median synchronized host simulation seconds',
                   'job_id':rows[0]['job_id'],'commit':rows[0]['commit'],
                   'blocks':{k:[int(s['block_x']),int(s['block_y'])] for k,s in winners.items()},'best_kernel':best}
        path.with_name('selection.json').write_text(json.dumps(selection,indent=2)+'\n')
        print(json.dumps(selection))
    print('VALIDATED {}: {} timed samples, {} groups, {} warmups'.format(path,len(rows),len(groups),len(warm)))
    return summaries

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('csv',nargs='+',type=pathlib.Path)
    args=parser.parse_args()
    for path in args.csv: analyse(path)
