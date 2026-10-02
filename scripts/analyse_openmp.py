#!/usr/bin/env python3
"""Validate complete experiments before producing reproducible plot-ready statistics."""
import csv
import math
from pathlib import Path
import statistics
import sys
from collections import defaultdict

root = Path(sys.argv[1])
groups = defaultdict(list)
states = {}
commits = set()
nodes = set()
seen = set()
for phase in ['formal', 'tuning']:
    with (root / (phase + '.csv')).open() as source:
        for row in csv.DictReader(source):
            assert row['phase'] == phase
            assert row['threads'] == row['requested_threads']
            assert row['density'] == '35' and row['seed'] == '12345'
            key = (phase, int(row['width']), int(row['generations']), row['backend'],
                   int(row['threads']), int(row['chunk']), row['binding'])
            identity = key + (int(row['rep']),)
            assert identity not in seen, 'duplicate timed repetition'
            seen.add(identity)
            workload = (key[1], key[2])
            state = row['live_cells'], row['checksum']
            assert states.setdefault(workload, state) == state, 'state mismatch'
            value = float(row['elapsed_seconds'])
            assert math.isfinite(value) and value > 0
            groups[key].append(value)
            commits.add(row['commit'])
            nodes.add(row['node'])
assert len(commits) == len(nodes) == 1, 'mixed build or node'
assert len([k for k in groups if k[0] == 'formal']) == 4 * 17, 'incomplete formal matrix'
assert len([k for k in groups if k[0] == 'tuning']) == 17, 'incomplete tuning matrix'
assert all(len(v) == 5 for v in groups.values()), 'not five repetitions'
assert all({identity[-1] for identity in seen if identity[:-1] == k} == set(range(1, 6)) for k in groups)
header = ['phase', 'size', 'generations', 'backend', 'threads', 'chunk', 'binding',
          'n', 'mean_seconds', 'median_seconds', 'min_seconds', 'stdev_seconds',
          'serial_speedup', 'omp_scaling_speedup', 'omp_scaling_efficiency',
          'v1_improvement', 'ideal_scaling_speedup']
with (root / 'summary.csv').open('w', newline='') as target:
    writer = csv.DictWriter(target, fieldnames=header)
    writer.writeheader()
    for key, values in sorted(groups.items()):
        phase, size, gens, backend, threads, chunk, binding = key
        median = statistics.median(values)
        serial = statistics.median(groups[(phase, size, gens, 'serial', 1, 0, 'close')])
        t1_key = ('formal', size, gens, backend, 1, 0, 'close')
        t1 = statistics.median(groups[t1_key])
        v1 = statistics.median(groups[('formal', size, gens, 'omp', threads, 0, 'close')])
        writer.writerow(dict(zip(header, [phase, size, gens, backend, threads, chunk, binding,
            len(values), statistics.mean(values), median, min(values), statistics.stdev(values),
            serial / median, t1 / median, t1 / median / threads, v1 / median, threads])))
print('VALIDATED: {} timed rows, {} groups, five repetitions each; identical states; commit={}, node={}'.format(
    len(seen), len(groups), next(iter(commits)), next(iter(nodes))))
