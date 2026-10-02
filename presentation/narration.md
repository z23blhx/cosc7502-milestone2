# Narration draft

Read only the spoken paragraphs below. Headings and notes are not narration. Use plain technical English, with brief pauses to point at a graph. Exact source values and rounding live in `final-results.md`. This draft needs a timed rehearsal before recording.

## 1. Objective

Hello, I am Lianquan Liu. This project implements Conway's Game of Life and investigates parallel execution with OpenMP and CUDA. My objective was to reduce simulation time while preserving exactly the same generations as the serial reference. I will explain the design, the optimizations that helped, and the experiments that did not.

## 2. Model and serial reference

Game of Life uses a grid of live and dead cells. A dead cell becomes alive with exactly three live neighbors. A live cell survives with two or three. I count the eight positions in its Moore neighborhood and wrap both grid edges to form a torus.

All cells update synchronously. I therefore keep two byte grids. Each update reads the current grid and writes the next grid. Only after every output is complete do I swap the buffers. An in-place update would let some cells observe the new generation too early, changing the model. This separation also makes the work parallel: each output depends only on read-only input data.

## 3. OpenMP design and correctness

The initial OpenMP implementation distributes rows with static scheduling. Each row has one writer, and workers share only the read-only current grid. The implicit worksharing barrier and team completion happen before the buffer swap.

In the persistent implementation, one team processes several generations. A single worker swaps the grids after the row-loop barrier. The single-section barrier then publishes the swap before the next generation starts.

I verified full cell states against serial for patterns, boundary seams, narrow and rectangular grids, several seeds and generation counts. Large timed runs also check the live count and checksum. A successful job exit alone does not establish correctness.

## 4. CPU optimization

The two panels here represent separate controlled experiments, with different generation counts. Comparisons are valid within each panel.

First, I expected a persistent team to reduce repeated team-entry overhead. In this implementation it was about fourteen percent slower than the original row-parallel version on the selected workload. The restructuring also changed generated code, so I cannot attribute that difference solely to team startup.

Next, I used row pointers and direct offsets for interior neighbors, leaving explicit wrapping at the boundaries. This reduced measured execution time. Adding an SIMD pragma alone did not make the compiler vectorize the loop: GCC still reported a control-flow blocker.

The later branch-free version evaluates safe Boolean predicates without short-circuit branches. GCC's diagnostic then confirmed vectorization with sixteen-byte vectors. The follow-up benchmark remeasured the pragma-only and branch-free versions on identical workloads. This supports the implementation change, although it does not isolate the contribution of each machine instruction.

## 5. Strong scaling

For strong scaling, I keep the branch-free kernel and the four-thousand-and-ninety-six square grid fixed at sixty-four generations. I increase the actual team from one to eight threads. Median runtime drops from about zero point nine three six seconds to zero point one two zero seconds.

The correct thread-scaling ratio is this kernel's one-thread time divided by its eight-thread time. That gives seven point seven seven times speedup and ninety-seven point one percent efficiency. The overall improvement relative to the original serial kernel is fifty-eight point six times, but that also includes kernel restructuring and vectorization.

Amdahl's Law explains why fixed-workload scaling eventually has limits. Here I see only a small sublinear loss through eight threads. I have not measured behavior beyond that allocation or fitted a serial fraction.

## 6. CUDA design and timing

The CUDA baseline maps one thread to one cell in a two-dimensional launch. I copy the initial grid to the GPU once, keep two device buffers for all generations, and copy the final state back once. Swapping device pointers moves no grid data.

Each generation launches a separate kernel in the same ordered stream. That kernel boundary supplies the global generation ordering. A block barrier cannot synchronize the whole grid.

I distinguish synchronized simulation time from GPU end-to-end time. The latter includes allocation, transfers and cleanup after context initialization. It excludes cold context startup, host output allocation and checksum work. The CUDA event interval includes gaps between launches, rather than a sum of kernel durations.

## 7. CUDA optimization

I tested four block dimensions and fixed the selected settings before the independent comparison. The direct version uses linear neighbor offsets for interior cells and exact wrapped accesses at the boundaries.

On the two-thousand-and-forty-eight square grid with two hundred and fifty-six generations, its median simulation time is ten point nine three milliseconds, compared with thirteen point seven four for naive and twenty point nine zero for shared tiling.

The shared version loads a tile and halo, and every thread reaches the barrier before an edge thread can return. It passes the correctness and sanitizer checks, but it is slower here. Halo loading and extra synchronization are plausible costs. The evidence does not establish that shared memory is generally a bad choice.

## 8. CPU versus GPU

This comparison uses the same allocated node, initial conditions and workloads for optimized OpenMP8 and CUDA. I recorded a warmup and five timed repetitions for each configuration, retained every sample, and show median times with observed minimum-to-maximum ranges.

The main result is the two-thousand-and-forty-eight square grid with two hundred and fifty-six generations. OpenMP8 takes one hundred and twenty point eight six milliseconds. CUDA direct takes twelve point four one milliseconds including transfers, allocation and cleanup. That is a nine point seven four times improvement over the optimized eight-thread CPU, under the stated timing boundary. It combines architecture and implementation differences, so I do not call it CPU thread scaling.

## 9. Overhead and limitations

At a fixed one-thousand-and-twenty-four square grid, I also measured one, ten, one hundred and one thousand generations. For one generation, setup and transfers occupy much of GPU time. With more computation, their relative cost becomes smaller.

Near one-generation CPU/GPU parity, independent batches land on opposite sides of the comparison. Small-grid tests also favor the optimized single-thread CPU. I therefore do not claim one exact universal crossover.

The cluster exposes a virtualized environment, and I tested only eight CPU threads with five repeats per configuration. Cold GPU process startup is outside the timer. Some profiling tools or counters were unavailable.

Gustafson's Law concerns increasing useful work with processor count. My size series instead holds total cell updates fixed while changing grid size and generations. It is not a weak-scaling test or a validation of that law.

## 10. Conclusion

The main lesson is that parallelization and kernel design work together. Compiler evidence helped turn the CPU SIMD attempt into a useful optimization. Persistent OpenMP and shared CUDA show why an appealing hypothesis still needs measurement. The direct CUDA implementation outperformed optimized OpenMP8 on the larger tested workloads. With more time, I would isolate specific overheads and repeat uncertain cases before adding further complexity.
