#!/usr/bin/env python3
"""Generate the technical narrative from validated statistics, without copied timing numbers."""
import csv
from pathlib import Path

root = Path(__file__).resolve().parents[1]
initial = list(csv.DictReader((root / 'results/openmp-benchmark-623308/summary.csv').open()))
final = list(csv.DictReader((root / 'results/openmp-vector-623318/summary.csv').open()))

def pick(rows, size, backend, threads, phase='vector', chunk='0', binding='close'):
    matches = [r for r in rows if r['size'] == str(size) and r['backend'] == backend and
               r['threads'] == str(threads) and r['phase'] == phase and
               r['chunk'] == chunk and r['binding'] == binding]
    assert len(matches) == 1
    return matches[0]

def number(row, key):
    return float(row[key])

def table(rows):
    lines = ['| Size | Generations | Mode | Threads | Median s | Mean s | Sample SD s | Serial-relative speedup | T1 scaling | Scaling efficiency |',
             '| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in rows:
        scaling = '{:.3f}'.format(number(row, 'omp_scaling_speedup')) if row['omp_scaling_speedup'] else 'not measured'
        efficiency = '{:.1%}'.format(number(row, 'omp_scaling_efficiency')) if row['omp_scaling_efficiency'] else 'not measured'
        lines.append('| {} | {} | {} | {} | {:.6f} | {:.6f} | {:.6f} | {:.3f} | {} | {} |'.format(
            row['size'], row['generations'], row['backend'], row['threads'], number(row, 'median_seconds'), number(row, 'mean_seconds'),
            number(row, 'stdev_seconds'), number(row, 'serial_speedup'), scaling, efficiency))
    return '\n'.join(lines)

best = max([r for r in final if r['backend'] == 'omp-vector'], key=lambda r: number(r, 'serial_speedup'))
large = [pick(final, 4096, 'omp-vector', p) for p in [1, 2, 4, 8]]
increment24 = number(large[1], 'median_seconds') / number(large[2], 'median_seconds')
increment48 = number(large[2], 'median_seconds') / number(large[3], 'median_seconds')
v1 = pick(initial, 2048, 'omp', 8, 'formal')
v2 = pick(initial, 2048, 'omp-persistent', 8, 'formal')
slowdown = number(v2, 'median_seconds') / number(v1, 'median_seconds') - 1
spread = pick(initial, 2048, 'omp-simd', 8, 'tuning', binding='spread')
close = pick(initial, 2048, 'omp-simd', 8, 'tuning')
tuning_gain = number(close, 'median_seconds') / number(spread, 'median_seconds') - 1
parts = [
'''# OpenMP optimization and controlled Rangpur evidence

## Scope and version history

Step 2 is CPU-only. Serial V3 and original row OpenMP are preserved; no CUDA,
MPI, manual AVX, slides or submission archive was added. Sources and evidence
are public in the existing Milestone2 repository.

| CLI mode | Design |
| --- | --- |
| serial | Unchanged V3 byte-grid reference |
| omp / omp_rows_v1 | Parallel region each generation; static disjoint rows |
| omp-persistent / v2 | One region across generations; original neighbour lookups via row helper |
| omp-interior / v3 | Persistent team; three read row pointers, direct interior neighbours; wrapped edge columns |
| omp-simd / v4 | v3 plus SIMD pragma, retaining short-circuit transition predicate |
| omp-vector / branchfree_v5 | v4 with safe non-short-circuit boolean comparisons, enabling compiler vectorization |

The worksharing barrier completes every output write before one `single` swap;
the `single` barrier publishes that swap before the next generation. The team
size capture alone uses `single nowait`. Byte layout, synchronous rules,
duplicate toroidal neighbour positions and serial reference remain unchanged.

## Profiling: observations versus hypotheses

Baseline job623307 ran source27087d7 on a100-b. Serial O3/-pg sampling reports
about0.77 seconds in `Life::step`, not setup. The printed100.16% is a sampling
artefact, not an exact fraction. Optimized disassembly contains the neighbour
helper symbol but no calls to it, supporting inlining by this GCC8 build;
manual neighbour inlining is therefore not credited as an independent speedup.
Local GCC13 behaves differently; compiler-specific evidence must not be pooled.

GCC8 reports control flow blocking the original interior loop. Adding a SIMD
pragma alone still reports that blocker. The v5 report at `life.cpp:205` says
`LOOP VECTORIZED`, with16-byte byte vectors, and local GCC13 also reports
16-byte vectors. This establishes generated vectorization, not its precise
contribution separate from changed predicates.

`perf` provides task-clock and software counters, but hardware cycles,
instructions and branch counters are not counted in this VM. No cache-miss,
bandwidth, branch-misprediction or false-sharing rate is inferred. There is no
worker-thread gprof claim. Team entry/exit, barriers, row dispatch and vector
code generation are plausible costs; only their combined runtime is measured.

## Method and provenance

All performance jobs used a100-b: VMware guest reporting AMD EPYC7542,
8virtual CPUs,1thread/core,1NUMA node, guest L1d32KiB/L2 512KiB/L3 16MiB.
These are guest-reported values, not proof of exclusive physical CPU/cache use.
Slurm allocated8CPUs; tested actual teams1/2/4/8, never above allocation.
Compiler GCC8.5.0; C++17, O3, DNDEBUG, fopenmp and warning flags from Makefile;
no `-march=native` or manual intrinsic path. The main settings are
OMP_DYNAMIC=FALSE, OMP_THREAD_LIMIT=8, OMP_PROC_BIND=close, OMP_PLACES=cores.
The launch affinity mask is0-7. Shared physical-host/VM interference remains possible.

Density35 and seed12345 are fixed. Each timed sample covers only generation
updates; allocation, randomization, checksum and output are excluded. Initial
team entry and all generation synchronizations are included. Each configuration
has one recorded warmup followed by five samples, with seeded shuffled order
between configurations. Warmups are separate process invocations, not reuse
of a previously initialized worker pool. All timed outliers remain. A30-second subprocess
watchdog bounds each invocation; Slurm caps jobs at15minutes.

- Job623308, source421f588b01c32281c7c3895e2a02bc8e7ba31d56: pilot36 samples,
  formal340 samples, tuning85 samples. Completed0:0,6m31s.
- Pilot-selected formal workloads:512²×1291,1024²×266,2048²×53,4096²×10 generations.
- Job623318, source684b067: followup200 samples on512²×4096,1024²×1024,
  2048²×256,4096²×64 generations; exactly1,073,741,824 cell updates per size.
  v4 and v5 use1/2/4/8threads; serial uses1; original v1 is remeasured at8.
- Tuning is separate:2048²×53, v4 at4/8threads, chunks0/1/8/32,
  close/spread; five samples each plus serial reference. No automatic affinity
  change is made to the main comparison.

Different generation counts are never pooled or directly compared as timings.
Size scaling uses equal total cell updates in the followup, changing spatial
working set and generation count; it is not constant-generation growth or
weak scaling. Two byte grids occupy about0.5/2/8/32MiB, plus lookup arrays.

Statistics: arithmetic mean, median, minimum and sample SD (n-1 denominator),
all five samples. Speedup relative to serial is Tserial/Tp. Pure OpenMP scaling
is that version's T1/Tp; efficiency is pure scaling/p, not serial-relative
algorithmic speedup/p. v1 improvement compares the same workload and p.
Tuning T1 is formal contiguous-close and is explicitly not affinity-specific.
The v1 followup has no T1 sample, so its pure scaling cells are blank.

## Initial controlled progression (2048²,53generations)
''',
table([pick(initial, 2048, b, 1 if b == 'serial' else 8, 'formal')
       for b in ['serial', 'omp', 'omp-persistent', 'omp-interior', 'omp-simd']]),
'\nPersistent v2 is {:.1%} slower than v1 here. It is retained as an unsuccessful attempt, not presented as a gain. The new row-helper dispatch also changes generated code, so this is not a clean measurement of team-startup cost alone. Row-pointer/boundary specialization improves the measured implementation; the small v3→v4 gain cannot be labelled SIMD acceleration because GCC reports no loop vectorization.\n'.format(slowdown),
'\n## Long-workload strong scaling (4096²,64generations)\n\n' + table([pick(final, 4096, 'serial', 1), pick(final, 4096, 'omp', 8), pick(final, 4096, 'omp-simd', 8)] + large),
'\nAt4096², doubling2→4threads improves runtime by {:.3f}x;4→8 by {:.3f}x. There is no pronounced plateau through eight threads on this workload; only a small sublinear loss is measured. The efficiency column is relative to v5 T1, not serial.\n'.format(increment24, increment48),
'\n## Spatial working-set comparison, constant total updates\n\n' + table([
    pick(final, size, b, p) for size in [512, 1024, 2048, 4096]
    for b, p in [('serial', 1), ('omp-vector', 1), ('omp-vector', 8)]]),
'''\nRows are grouped in size order512,1024,2048,4096; exact sizes/generations are
also present in the source summary CSV. Absolute times differ with simulation
evolution and barrier frequency as well as memory size. Timing alone does not
locate a cache-capacity transition.

The 1024²/eight-thread v5 group has a noticeable retained timing outlier:
its mean differs substantially from its median. Report both, do not discard
that sample or present all groups as equally stable. Large4096² v5 samples
have much smaller dispersion; the statistics are shown rather than hidden.

## Scheduling, unsuccessful attempts and decisions
''',
'\nIn secondary v4 tuning, contiguous-spread has {:.3f}s median versus {:.3f}s contiguous-close ({:.1%} ratio improvement). This single workload does not establish a universal binding winner. Chunk1 does not outperform contiguous rows and includes substantial variability; all its samples are retained. Main and v5 results keep contiguous-close.\n'.format(number(spread, 'median_seconds'), number(close, 'median_seconds'), tuning_gain),
'''\nThe SIMD-pragma-only attempt does not produce vectorization in this compiler.
The branch-free followup is the justified retained vector version. Collapse,
dynamic scheduling, wider cell storage, bit packing, alignment and blocking
were considered but not implemented: there are already at least512 equal-size
row tasks for8workers; those changes would confound the controlled progression.
Their performance is not claimed to be worse without measurements.

Setup failures623293/623305/623306 were diagnostic-option compatibility failures,
not simulation failures. Job623304 exceeded the course QoS walltime cap and was
cancelled before execution. Logs/accounting are retained under setup-failures.

## Correctness and validation

Both local Windows MinGW and Linux GCC13 pass the inherited serial tests,
original216pattern/1260random comparisons, plus four persistent kernels:
864pattern and15,120random/chunk comparisons, every cell/count/checksum,
threads1/2/4. Local Linux optimized O3 tests also pass. Rangpur job623318
passes the expanded debug suite before benchmarking. Width/height1, width2,
rectangles, seams, densities0/35/100, four seeds and0/1/2/10/31generations are covered.
Every formal/tuning/followup sample checks actual teams and matches serial
live counts/checksums on the large workloads. No result is accepted solely
because its Slurm exit status is0. This is not a formal race-detector proof.

The validator rejects duplicate repetition keys, missing repetitions, unequal
states, mixed source/node, nonpositive times and incomplete experiment matrices.
Mean/median/sample SD for a selected initial group were independently recomputed
in PowerShell rather than via the Python summary helper. Final key statistics
are independently checked before publishing. Reviewed scope is these particular
nodes, commits, workloads and CPU counts; broader generalization has caveats.

## Interpretation: Amdahl and Gustafson

The serial-relative gain includes single-thread kernel/vectorization improvement
and must not be compared directly to an ideal p-thread line. Use v5 T1 scaling
and provided ideal p column for strong-scaling plots. Amdahl's law qualitatively
describes fixed-workload limits, but barriers, bandwidth and VM sharing are not
a measured constant serial fraction here; no fitted percentage is reported.
Only1..8threads were allocated, so behaviour beyond8threads is unknown.
Gustafson motivates larger useful workloads, but this is not a weak-scaling
experiment and cannot validate a Gustafson curve. A future explicitly scaled
workload study is needed.

Remaining limitations: no hardware counters, no physical-host isolation,
five rather than dozens of samples, no v5 chunk/binding factorial study, and no
pure persistent-team ablation that holds all code-generation details fixed.
The current timings establish improvements, not unique hardware causes.

## Files and reproduction

Raw directories:
`results/baseline-profile-623307/`, `results/openmp-benchmark-623308/`,
`results/openmp-vector-623318/`, `results/step2-setup-failures/`.
Each successful experiment includes unedited stdout and sacct; performance
directories include metadata, raw CSV, warmups, compiler diagnostics and derived
summary. `SHA256SUMS.txt` protects downloaded raw records against accidental
changes. No evidence timestamp is altered.

Run `python3 scripts/analyse_openmp.py <result-directory>` then
`python3 scripts/report_openmp.py` to regenerate statistics/report. Compare
the recorded exact commits, not whatever happens to be latest main. Formal
jobs must be submitted through Slurm, not run on the login node.

Implementation commits: b59e8b1(persistent kernels and tooling),
a8eff3c(QoS limit),421f588(GCC8 diagnostics),684b067(branch-free followup).
Subsequent commits add evidence/docs only. Tested source commits differ between
the two experiments and are explicit in every raw CSV.

## Evidence worth using in the Milestone 2 presentation
''',
'\n- Strongest measured serial-relative v5 result: {:.2f}x at{}²,{}generations,{}threads; median {:.6f}s, mean {:.6f}s.\n'.format(
    number(best, 'serial_speedup'), best['size'], best['generations'], best['threads'],
    number(best, 'median_seconds'), number(best, 'mean_seconds')),
'- At4096²/64generations, v5 scales {:.2f}x from1→8threads with {:.1%} pure-scaling efficiency.\n'.format(
    number(large[3], 'omp_scaling_speedup'), number(large[3], 'omp_scaling_efficiency')),
'''- Original neighbour call sites are absent in the GCC8 optimized disassembly;
  the original/v4 interior loops report control-flow vectorization blockers.
- v5's compiler report confirms loop vectorization; the long followup remeasures
  v4 and v5 under identical workloads, compiler and binding.
- Persistent v2 alone is slower in the initial experiment; this negative result
  remains available, alongside all raw samples and failed setup logs.
- 625 formal/tuning/followup timed samples match serial counts/checksums; every
  configuration has five repeats and no timed outlier was removed.
'''
]
(root / 'docs/openmp-performance.md').write_text('\n'.join(parts), encoding='utf-8')
print('Generated docs/openmp-performance.md from validated statistics')
