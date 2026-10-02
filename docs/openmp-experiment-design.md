# Step 2 controlled CPU experiments

Serial `step`/`run` and `omp_rows_v1` are retained unchanged. New persistent modes:

| CLI | Version | Difference |
| --- | --- | --- |
| `omp-persistent` | `omp_persistent_v2` | One team across generations, same neighbour lookup expression |
| `omp-interior` | `omp_interior_v3` | Persistent team, three read row pointers and one output pointer; only two columns use x-wrapping lookups |
| `omp-simd` | `omp_simd_v4` | Same v3 arithmetic, interior loop has `omp simd` (experimental until measured) |
| `omp-vector` | `omp_branchfree_v5` | v4 plus non-short-circuit boolean predicates; compiler confirms local interior-loop vectorization |

`--chunk 0` means contiguous `schedule(static)`; positive chunk means round-robin static row blocks. This is a schedule setting, not a new algorithm. No dynamic schedule is presumed useful.

## Synchronization proof

Every row is assigned to one worker. All workers read only `current_` and write disjoint `next_` cells. The worksharing loop's implicit barrier precedes `single` buffer swap. Its implicit barrier completes and publishes the swap before the next generation. `single nowait` is used only for capturing team size, which is read after the parallel-region join. Width/height remain fixed. Width-one/two retain eight-position neighbour counting, including duplicates. SIMD writes independent x positions in a different allocation from the input pointers.

## Method

The benchmark script allocates eight CPUs on one Rangpur node, uses GCC `-O3 -DNDEBUG -fopenmp` without host-specific ISA flags, and checks actual thread counts. Main experiment: density 35, seed 12345, sizes 512/1024/2048/4096, serial plus four OpenMP modes at 1/2/4/8 threads, contiguous static schedule, `OMP_PROC_BIND=close`, `OMP_PLACES=cores`, dynamic teams disabled. All configurations share the same generations for a grid size. Pilot starts with 134,217,728 cell updates and selects longer workloads aiming at a fastest sample of 0.15 seconds, bounded by approximately eight seconds for the slowest pilot estimate. Actual samples, not that estimate, establish timing stability.

One warmup per configuration precedes five recorded repetitions. A seeded shuffle changes configuration order each repetition. Warmups have their own raw file and do not enter summary statistics. No outlier is removed. A serial state is the reference for every warmup/timed result. Each process has a 30-second watchdog. Only synchronous generation updates enter the application's timer; setup, randomisation, checksum and CSV are outside it. Single team startup and generation barriers are included.

Secondary tuning uses the 2048 workload, SIMD mode, 4/8 threads, static chunks 0/1/8/32, close/spread binding, five repetitions. It is a separate experiment, not mixed into main strong scaling. Tuning T1 reference is the formal contiguous-close one-thread mode; it is not a binding-specific pure-scaling result.

Mean, median, minimum and sample standard deviation use all five samples. Serial-relative speedup uses the same workload's serial median. Pure OpenMP scaling uses that algorithm's one-thread median; efficiency divides this scaling speedup by p. v1 improvement compares the same p's original OpenMP median. Ideal scaling p is provided for later plots. Algorithmic speedup must not be labelled parallel efficiency.

## Investigations deliberately bounded

Contiguous equal-length rows already offer hundreds/thousands of tasks for at most eight threads; collapse is not initially implemented because there is no task-count shortage and it would obstruct the separate interior/boundary structure. This is design reasoning, not a measured claim that collapse is slower. Byte representation and row-major traversal remain unchanged. Packing bits, wider cells, alignment and cache blocking would confound this controlled progression and are deferred. Power-of-two widths are multiples of cache-line sizes, but allocation alignment is not guaranteed; false sharing is possible at ownership boundaries, not demonstrated without counters. No bandwidth/cache bottleneck is claimed solely from timing.

The final four persistent kernels pass 864 pattern comparisons and 15,120 random/chunk comparisons in addition to the original suite, with every cell, live count and checksum checked at threads 1/2/4. Local Linux GCC13 and Windows MinGW builds are correctness checks, not substitutes for Rangpur performance.

## Evidence-driven vector followup

The first GCC8 report identifies control flow as a blocker; the pragma alone is not evidence of vectorization. A separate v5 keeps the safe boolean predicate arithmetic but uses bitwise OR/AND on comparisons to remove short-circuit branches. It retains v4 as the failed/limited SIMD-pragma-only experiment. `openmp_vector.slurm` repeats serial, v1 at eight threads, and v4/v5 at 1/2/4/8 threads on four longer workloads, each 1,073,741,824 cell updates: 512/4096 generations, 1024/1024, 2048/256, 4096/64. Each size has five repetitions and its own warmups, all raw. These timings must not be directly pooled with the shorter initial experiment. One-thread v1 is not measured in the vector followup, so its pure-scaling metrics are intentionally blank there.
