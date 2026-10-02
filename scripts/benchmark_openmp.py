#!/usr/bin/env python3
"""Controlled subprocess timings; each invocation has a 30-second watchdog."""
import argparse
import csv
import io
import os
import random
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--binary', default='./build/benchmark/life')
parser.add_argument('--out', required=True)
parser.add_argument('--phase', choices=['pilot', 'formal', 'tuning'], required=True)
args = parser.parse_args()
os.makedirs(args.out, exist_ok=True)
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], universal_newlines=True).strip()
fields = ['job_id', 'node', 'commit', 'phase', 'rep', 'order', 'requested_threads',
          'binding', 'backend', 'version', 'width', 'height', 'generations', 'density',
          'seed', 'threads', 'chunk', 'elapsed_seconds', 'live_cells', 'checksum']

def run(size, generations, backend, threads, chunk, binding):
    env = dict(os.environ, OMP_PROC_BIND=binding)
    command = [args.binary, '--size', str(size), '--generations', str(generations),
               '--backend', backend, '--threads', str(threads), '--chunk', str(chunk),
               '--density', '35', '--seed', '12345', '--csv']
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True, timeout=30, env=env)
    if result.returncode:
        raise RuntimeError('command failed: {} {}'.format(command, result.stderr))
    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    if len(rows) != 1 or int(rows[0]['threads']) != threads:
        raise RuntimeError('malformed result or team-size mismatch: ' + result.stdout)
    if float(rows[0]['elapsed_seconds']) <= 0:
        raise RuntimeError('nonpositive timing')
    return rows[0]

sizes = [(512, 512), (1024, 128), (2048, 32), (4096, 8)]
# Fixed 134,217,728 cell updates initially; pilot calibrates without changing versions' work.
if args.phase != 'pilot':
    with open(os.path.join(args.out, 'workloads.csv')) as source:
        sizes = [(int(r['size']), int(r['generations'])) for r in csv.DictReader(source)]
if args.phase == 'tuning':
    sizes = [pair for pair in sizes if pair[0] == 2048]
configs = [('serial', 1, 0, 'close')]
if args.phase == 'pilot':
    configs += [(b, p, 0, 'close') for b in ['omp', 'omp-persistent', 'omp-interior', 'omp-simd'] for p in [1, 8]]
elif args.phase == 'formal':
    configs += [(b, p, 0, 'close') for b in ['omp', 'omp-persistent', 'omp-interior', 'omp-simd'] for p in [1, 2, 4, 8]]
else:
    configs += [('omp-simd', p, chunk, binding) for p in [4, 8]
                for chunk in [0, 1, 8, 32] for binding in ['close', 'spread']]
if int(os.environ.get('SLURM_CPUS_PER_TASK', '8')) < max(c[1] for c in configs):
    raise RuntimeError('insufficient allocated CPUs')
repetitions = 1 if args.phase == 'pilot' else 5
calibrated = []
with open(os.path.join(args.out, args.phase + '.csv'), 'w', newline='') as target:
    writer = csv.DictWriter(target, fieldnames=fields)
    writer.writeheader()
    for size, generations in sizes:
        reference = run(size, generations, 'serial', 1, 0, 'close')
        expected = (reference['live_cells'], reference['checksum'])
        # Warm up once for every configuration, checking correctness but not mixing into samples.
        for backend, threads, chunk, binding in configs:
            warm = run(size, generations, backend, threads, chunk, binding)
            if (warm['live_cells'], warm['checksum']) != expected:
                raise RuntimeError('warmup correctness mismatch')
            warm.update(job_id=os.environ.get('SLURM_JOB_ID', 'local'), node=os.uname().nodename,
                        commit=commit, phase=args.phase + '-warmup', rep=0, order=0,
                        requested_threads=threads, binding=binding)
            warm_path = os.path.join(args.out, 'warmups.csv')
            exists = os.path.exists(warm_path)
            with open(warm_path, 'a', newline='') as warm_target:
                warm_writer = csv.DictWriter(warm_target, fieldnames=fields)
                if not exists:
                    warm_writer.writeheader()
                warm_writer.writerow(warm)
        fastest = float('inf')
        slowest = 0.0
        for rep in range(1, repetitions + 1):
            order = list(configs)
            random.Random(12345 + size + rep).shuffle(order)
            for index, (backend, threads, chunk, binding) in enumerate(order):
                row = run(size, generations, backend, threads, chunk, binding)
                if (row['live_cells'], row['checksum']) != expected:
                    raise RuntimeError('timed correctness mismatch')
                elapsed = float(row['elapsed_seconds'])
                fastest, slowest = min(fastest, elapsed), max(slowest, elapsed)
                row.update(job_id=os.environ.get('SLURM_JOB_ID', 'local'),
                           node=os.uname().nodename, commit=commit, phase=args.phase,
                           rep=rep, order=index, requested_threads=threads, binding=binding)
                writer.writerow(row)
                target.flush()
            print('completed size={} generations={} repetition={}'.format(size, generations, rep), flush=True)
        if args.phase == 'pilot':
            # Aim for fastest >=0.15s while bounding slowest to roughly 8s.
            factor = max(1, min(0.15 / fastest, 8.0 / slowest))
            calibrated.append((size, max(generations, int(generations * factor))))
if args.phase == 'pilot':
    with open(os.path.join(args.out, 'workloads.csv'), 'w', newline='') as target:
        writer = csv.writer(target)
        writer.writerow(['size', 'generations'])
        writer.writerows(calibrated)
