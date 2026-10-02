#!/usr/bin/env python3
"""Generate archive notes and byte hashes without rewriting captured raw evidence."""
import argparse
import hashlib
import pathlib

parser=argparse.ArgumentParser(); parser.add_argument('directories',nargs='+',type=pathlib.Path)
args=parser.parse_args()
for directory in args.directories:
    name=directory.name
    note='Captured allocated-GPU experiment. See environment/stdout and sacct for source, hardware, exit status and timings.'
    if '623387' in name: note+=' Initial discovery: default PATH lacked nvcc; follow-up 623393 verified explicit CUDA 12.2 toolkit.'
    if '623431' in name: note='FAILED before GPU execution: invalid-block test referenced an out-of-scope variable. Fixed in 0c65775; passed in 623448. No benchmark samples claimed.'
    if '623412' in name: note='Cancelled after allocation on a100-b: environment probe and CPU compilation began, but cancellation occurred before CUDA tests or benchmarks. No performance samples or completed CUDA correctness claims.'
    if 'baseline' in name: note+=' Naive exact tests passed; nsys permission failure retained; ncu results are instrumented profiling only.'
    if 'tuning' in name: note+=' 120 timed samples + 24 warmups; all three kernels, four blocks; selection based only on 2048x2048x128 synchronized simulation median.'
    if 'comparison' in name: note+=' 120 main + 80 generation-study timed samples; 24 + 16 warmups. Fixed tuning selection, same-job serial/CPU1/OMP8/GPU comparison. See docs/cuda-performance.md for exact timing exclusions.'
    if 'profile' in name: note+=' Single first-generation kernel counters only. Profiled CLI wall times are not performance samples; preserve nsys capture failure if present.'
    (directory/'README.md').write_text('# '+name+'\n\n'+note+'\n\nRaw files are unchanged. CSV summaries are derived with scripts/analyse_cuda.py (five samples, sample SD n-1). SHA256SUMS checks bytes of all archive files other than itself.\n',encoding='utf-8')
    manifest=[]
    for path in sorted(directory.rglob('*')):
        if path.is_file() and path.name!='SHA256SUMS':
            manifest.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.relative_to(directory).as_posix())
    (directory/'SHA256SUMS').write_text('\n'.join(manifest)+'\n')
