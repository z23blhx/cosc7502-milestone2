# Interview / viva notes

Use these to explain your own implementation, not to recite claims you cannot defend. The personal specification describes an approximately seven-minute in-person identity-verification hurdle. Confirm the actual appointment in Blackboard.

1. **Why is Game of Life parallelizable?** Each next-generation cell depends only on current-generation neighbors. Separate input and output grids remove dependencies between output calculations within a generation.
2. **Why double buffering?** It preserves synchronous updates and gives every worker a stable read-only input snapshot.
3. **What goes wrong with in-place updates?** Later calculations can read already-updated neighbors. Parallel execution adds competing reads/writes and order-dependent results.
4. **Why a generation barrier?** Every next-grid write must finish before any worker reads that grid as current input. Buffer identity also needs consistent publication.
5. **What does `omp for` do?** It distributes iterations among an existing team. Each row iteration has one worker. Its implicit barrier remains enabled here.
6. **Why static scheduling?** Rows have similar work and there are many more rows than workers. Contiguous static ownership is simple and avoids dynamic scheduling overhead. This reasoning does not prove every alternative slower.
7. **Why did persistent OpenMP not necessarily help?** Saving team-entry cost does not remove barriers or other overhead. My row-helper restructuring also changed generated code. The measured v2 was 14.03% slower on 2048²×53, so the startup-only hypothesis was insufficient.
8. **Why did branch-free predicates help?** GCC8 reported control flow blocking the pragma-only loop. Safe non-short-circuit Boolean evaluation removed that blocker and the compiler confirmed 16-byte vectorization. The timing measures the combined change, not an isolated SIMD-only effect.
9. **SIMD versus multithreading?** SIMD processes several cell values through vector instructions on a core. OpenMP runs work across CPU threads. The optimized CPU uses both.
10. **Why is 58.6× not eight-thread scaling?** Its numerator is the original serial kernel, while its denominator uses a restructured/vectorized kernel plus eight threads. Pure v5 scaling uses its own T1, giving 7.77×.
11. **Parallel efficiency?** `E(p)=(T1/Tp)/p`. For v5 4096²×64, eight-thread efficiency is 97.113%, based on medians. Never use serial-relative algorithmic gain as this numerator.
12. **Why one CUDA launch per generation?** Kernel ordering in the same stream supplies the grid-wide dependency without an unsafe device-wide software barrier.
13. **Why not `__syncthreads()` for generations?** It synchronizes a block only. Other blocks might still be writing or might not yet execute.
14. **Why was shared memory slower?** The tiled implementation adds halo loading, wrapping and a block barrier. Those are plausible costs. Counters show higher shared-kernel occupancy but slower duration, so occupancy alone is insufficient. I did not isolate each cost experimentally.
15. **Why separate simulation and E2E?** Simulation hides transfers/allocation/cleanup. Main practical ratios use steady-context E2E, with explicit cold-context and host-work exclusions. The event interval includes launch gaps.
16. **Why can GPU lose on small work?** Transfers, device allocation, launch and synchronization costs can exceed a short CPU calculation. My optimized CPU1 wins on the smaller one-generation grids. OMP8 startup complicates a separate crossover comparison.
17. **Amdahl's Law?** For fixed work and an idealized serial fraction `f`, `S(p)=1/(f+(1-f)/p)`. Serial work limits speedup as p grows, even before additional synchronization/communication costs.
18. **How does it relate here?** Strong scaling shows a small loss from ideal through eight threads. Barriers, runtime overhead and shared hardware matter. I have not fitted a constant serial fraction or measured saturation beyond eight.
19. **Gustafson's Law?** With a scaled workload, increasing processors can allow more useful parallel work in similar elapsed time. Its idealized speedup is `p-f*(p-1)`, where f has the scaled-execution interpretation.
20. **Why is this not weak scaling?** My grid-size series keeps total cell updates at 2³⁰ by changing generation counts, rather than keeping work per processor fixed while increasing p. It cannot validate a Gustafson curve.
21. **How did you verify correctness?** Known patterns, per-generation comparisons, seams, narrow/rectangular grids, several seeds/densities/generation counts, exact cells/count/checksum. GPU checks cover four blocks and three kernels, plus memcheck/synccheck. Every accepted timed run matches the serial count/checksum.
22. **Why checksum plus full states?** Live count alone ignores positions. A position-sensitive checksum is cheap for large timed runs, but collisions remain theoretically possible. Exact state comparison catches differences directly on the bounded test suite.
23. **What next?** Repeat uncertain small cases, isolate team/launch overhead under a controlled ablation, and measure cold-process latency. Consider pinned transfers only after evidence supports the extra complexity. These are proposals, not completed results.
24. **Main limitations?** Eight CPU threads maximum, VM/shared-host interference, five repeats, fixed density/seed for main runs, no hardware CPU counters, failed nsys capture, no cold-process GPU timing. No MPI, manual AVX or universal crossover claim.

## Numbers to know without mixing jobs

- CPU scaling job 623318, 4096²×64: v5 T1 0.935899131 s, T8 0.120465009 s. T1/T8 7.769053759×. Original serial 7.05988722 s.
- CPU/GPU job 623453, 2048²×256: optimized OMP8 0.120862109 s, direct simulation 0.010926513 s, direct E2E 0.012410679 s. Ratio OMP8/E2E 9.738557334×.
- CUDA first-generation profiling job 623467, 2048²16×16: direct 54.272 µs / occupancy 82.62%; shared 114.176 µs / 92.66%. Never substitute these durations for the median multi-generation benchmark.
- Known smoke 101²×10: 2,213 live cells, checksum 7897773207305806522.
