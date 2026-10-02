# Initial CPU scaling and schedule tuning

Job 623308, source `421f588b01c32281c7c3895e2a02bc8e7ba31d56`, node a100-b,
eight allocated CPUs, GCC8.5.0, completed0:0 in6m31s on2026-10-02.

- `pilot.csv`:36 exploratory samples; not pooled with formal results.
- `workloads.csv`:pilot-selected generations per size.
- `formal.csv`:340 samples,68 configurations,five repeats each.
- `tuning.csv`:85 samples,17 configurations,five repeats each.
- `warmups.csv`:warmup records,excluded from summaries.
- `summary.csv`:derived reproducibly with `scripts/analyse_openmp.py`.
- `environment.txt`, `vector.txt`, `slurm-623308.out`, `sacct.txt`:unedited source records.

All samples/warmups match the workload's serial live count and checksum;
actual threads match requests. No timed outlier was removed. The environment
shows only untracked generated results, not source modifications.
Summary uses median-based speedup and sample standard deviation. Tuning's T1
reference is the formal contiguous/close configuration; spread/chunk tuning is
not binding-specific pure scaling. Compare only identical workloads within an
experiment, not these shorter timings against the later longer vector run.
