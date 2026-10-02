#!/usr/bin/env python3
"""GPU watchdogs, serial state checks, recorded warmups and shuffled repetitions."""
import argparse
import csv
import io
import os
import random
import subprocess
import json

parser=argparse.ArgumentParser()
parser.add_argument('--out',required=True)
parser.add_argument('--phase',choices=['baseline','tuning','main','generations'],required=True)
parser.add_argument('--selection',help='JSON from an independently completed tuning experiment')
args=parser.parse_args()
os.makedirs(args.out,exist_ok=True)
commit=subprocess.check_output(['git','rev-parse','HEAD'],universal_newlines=True).strip()
fields=['job_id','node','commit','phase','rep','order','backend','version','width','height',
        'generations','density','seed','threads','block_x','block_y','cpu_seconds',
        'simulation_seconds','kernel_event_seconds','gpu_e2e_seconds','h2d_seconds','d2h_seconds',
        'device_bytes','live_cells','checksum']

def run(size,generations,backend,threads,bx,by,kernel='naive'):
    command=['./build/cuda/life','--backend',backend,'--size',str(size),'--generations',str(generations),
             '--density','35','--seed','12345','--csv']
    if backend=='cuda': command+=['--block-x',str(bx),'--block-y',str(by),'--cuda-kernel',kernel]
    else: command+=['--threads',str(threads)]
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          universal_newlines=True,timeout=30)
    if result.returncode: raise RuntimeError(str(command)+' '+result.stderr)
    rows=list(csv.DictReader(io.StringIO(result.stdout)))
    if len(rows)!=1: raise RuntimeError('malformed output')
    row=rows[0]
    if backend!='cuda':
        if int(row['threads'])!=threads: raise RuntimeError('incorrect actual CPU team')
        row['cpu_seconds']=row.pop('elapsed_seconds')
        row.pop('chunk')
    else:
        row['threads']='0'
        if float(row['gpu_e2e_seconds'])<float(row['simulation_seconds']):
            raise RuntimeError('invalid timing boundaries')
    return row

workloads=[(512,512),(2048,128)]
if args.phase in ['baseline','tuning']:
    kernels=['naive'] if args.phase=='baseline' else ['naive','direct','shared']
    configs=[('cuda',0,bx,by,kernel) for kernel in kernels for bx,by in [(8,8),(16,16),(32,8),(32,16)]]
else:
    if not args.selection: raise RuntimeError('selection from completed tuning required')
    with open(args.selection) as source: selection=json.load(source)
    with open(os.path.join(args.out,'selection.json'),'w') as target: json.dump(selection,target,indent=2)
    configs=[('serial',1,0,0,''),('omp-vector',1,0,0,''),('omp-vector',8,0,0,'')]
    for kernel in ['naive','direct','shared']:
        bx,by=selection['blocks'][kernel]
        configs.append(('cuda',0,bx,by,kernel))
    workloads=[(512,4096),(1024,1024),(2048,256),(4096,64)]
    if args.phase=='generations':
        workloads=[(1024,g) for g in [1,10,100,1000]]
        kernel=selection['best_kernel']; bx,by=selection['blocks'][kernel]
        configs=[('serial',1,0,0,''),('omp-vector',1,0,0,''),('omp-vector',8,0,0,''),('cuda',0,bx,by,kernel)]
if max(c[1] for c in configs)>int(os.environ['SLURM_CPUS_PER_TASK']):
    raise RuntimeError('CPU team would exceed allocation')
with open(os.path.join(args.out,args.phase+'.csv'),'w',newline='') as target, \
     open(os.path.join(args.out,args.phase+'-warmups.csv'),'w',newline='') as warm_target:
    timed=csv.DictWriter(target,fieldnames=fields); timed.writeheader()
    warms=csv.DictWriter(warm_target,fieldnames=fields); warms.writeheader()
    for size,generations in workloads:
        reference=run(size,generations,'serial',1,0,0)
        expected=reference['live_cells'],reference['checksum']
        for rep in range(6):
            order=list(configs)
            random.Random(12345+size+rep).shuffle(order)
            for index,(backend,threads,bx,by,kernel) in enumerate(order):
                row=run(size,generations,backend,threads,bx,by,kernel)
                if (row['live_cells'],row['checksum'])!=expected:
                    raise RuntimeError('invalid CUDA result: checksum/count differs')
                row.update(job_id=os.environ['SLURM_JOB_ID'],node=os.uname().nodename,commit=commit,
                           phase=args.phase,rep=rep,order=index)
                (warms if rep==0 else timed).writerow(row)
                (warm_target if rep==0 else target).flush()
            print('completed phase={} size={} generations={} rep={}'.format(args.phase,size,generations,rep),flush=True)
