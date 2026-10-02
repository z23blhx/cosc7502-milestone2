# Evidence-based reflection

## What changed my reasoning

Parallelization alone did not account for the final CPU result. v5's one-thread restructuring/vectorization already improved its kernel. The measured T1/T8 ratio then describes thread scaling separately. This distinction prevents the 58.61× serial-relative overall gain from becoming an impossible-sounding eight-thread claim.

Persistent OpenMP looked attractive because it reused the team. The tested v2 nevertheless ran 14.03% slower than v1 on 2048²×53. The implementation also changed dispatch/code generation, so I learned to separate a theoretical saved cost from the measured net effect and avoid a startup-only causal claim.

Row-pointer access and interior/boundary specialization improved the measured CPU implementation. An SIMD directive alone still left GCC8's control-flow blocker. The safe branch-free predicate change produced a confirmed vectorized loop. Compiler diagnostics guided a specific change instead of treating a pragma as proof of SIMD execution.

Shared CUDA tiling was correct but slower. In the independent 2048²×256 comparison, shared/direct simulation ratio is 1.913×. First-generation profiling reports higher shared occupancy yet a longer duration. Additional halo arithmetic and synchronization are hypotheses to investigate, not isolated measured causes. Shared memory remains useful in other workloads and implementations.

Direct CUDA steady-context E2E substantially outperformed optimized OpenMP8 on all four tested larger workloads. The strongest main ratio was 9.74× at 2048²×256. Allocations and transfers still matter for short work. The near-one-generation OMP8 comparison changes sides of parity across batches, while CPU1 clearly wins on smaller single-generation grids.

## Methodological lessons

Retain unfavorable measurements and failed attempts. Use identical work and final states for speedup ratios. Record warmups but acknowledge separate-process warmups do not preserve a CUDA context or worker pool. Report sample dispersion alongside medians, and exclude instrumentation time from benchmark summaries. Define timers before choosing a headline.

The fixed-total-update size experiment changes spatial working set and generation count together. It is not a weak-scaling experiment. Amdahl and Gustafson offer useful interpretations, but the current evidence does not justify fitted serial fractions, cache-capacity transitions or a Gustafson validation.

## Limits and next work

Only eight allocated CPU threads, a virtualized/shared cluster, five timed repetitions/configuration, and limited fixed-density main workloads. CPU hardware counters and Nsight Systems capture were unavailable. GPU context startup, host output allocation and import/checksum remain outside steady-context E2E. There is no MPI, manual AVX or universal crossover result.

With more time, I would repeat the uncertain small-work cases, measure full-process startup separately, and isolate dispatch/team-entry or halo-loading costs while holding the rest of the code fixed. I would evaluate pinned transfers only if the measured bottleneck justified them. These are future investigations, not performance claims in this submission.
