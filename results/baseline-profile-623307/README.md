# Original baseline profiling, job 623307

Source: `27087d73da1a9ef7867cf343cc0fda872b565ae2`, original serial/row OpenMP.
Node: a100-b, eight CPUs, GCC 8.5.0, 2026-10-02. Accounting reports COMPLETED,
0:0, six seconds. The unedited Slurm output contains hardware, flags, commit
and short exploratory timings. These single timings are not formal averages.

`gprof.txt` is a serial O3/-pg sample with 1024x1024, 128 generations, density35,
seed12345. Sampling places approximately 0.77 s in `Life::step`; the displayed
100.16% is a profiler sampling artefact, not an exact percentage. Do not use
gprof as worker-thread accounting. `perf.txt` records software counters and
unavailable hardware counters; cycles/instructions/branch counts cannot be used.
`inline.txt` and `vector.txt` are compiler diagnostics. `disassembly.txt` comes
from the optimized benchmark binary; the neighbour helper has a symbol but no
call sites, supporting the inference that GCC8 inlines this hot calculation.

Reproduction: use a separate checkout of the baseline commit, copy
`scripts/profile_baseline.slurm` from the current repository into it, and submit
through Slurm. The report and disassembly are generated evidence, not source.
