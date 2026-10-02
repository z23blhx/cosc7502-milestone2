# CUDA performance evidence — Milestone 2 Step 3

## Environment and build

Actual allocated device: NVIDIA A100-PCIE-40GB, compute capability 8.0, 42,405,855,232 bytes reported by CUDA. Driver 590.48.01; driver API 13.1 is not the installed toolkit. CUDA toolkit/runtime 12.2 (nvcc V12.2.128). Rangpur CPU: AMD EPYC 7542, VMware guest. GPU environment probes: jobs 623387 and 623393; performance metadata records the actual node per job.

Slurm: `--partition=cosc3500 --account=cosc3500 --gres=gpu:1`; comparison uses one node and eight allocated CPUs. Initialize `/etc/profile.d/modules.sh`, add `/usr/local/cuda-12.2/bin` to PATH. No CUDA module required; module lists retained. Nodes report nominal 1 MB Slurm memory, so no explicit memory request. CUDA compilation: `-std=c++17 -O3 -lineinfo -arch=sm_80`. CPU comparison: GCC 8.5, `-O3 -DNDEBUG -fopenmp` with warning flags. Architecture 80 was selected only after device verification.

## Versions, synchronization and memory

- `cuda_naive_v1`: one thread per cell, eight global byte reads and conditional wrapping for all cells.
- `cuda_direct_v2`: same launch; direct linear offsets for interior cells, exact wrapped boundary path.
- `cuda_shared_v3`: cooperative shared-memory tile plus one-cell halo, followed by one block-local barrier. Even inactive edge threads reach the barrier before returning.

One ordered default-stream kernel per generation supplies the global generation boundary. `__syncthreads()` only protects tile loading, never synchronizes the grid. Two resident device grids are swapped by host pointers; one H2D and one D2H transfer per simulation, no per-generation grid copies. All CUDA allocations, copies, launch errors, events and successful cleanup are checked. Correctness mode synchronizes each generation; benchmark mode only waits at the final event.

The two global allocations require exactly `2*width*height` bytes: 512²=524,288; 1024²=2,097,152; 2048²=8,388,608; 4096²=33,554,432. A 16×16 shared tile adds 324 bytes/block. These are application buffer sizes, not total context/driver/device memory usage.

CPU-only builds remain available (`make test benchmark`, `OPENMP=0`); CUDA builds use `make cuda`, and `make cuda-test` must execute on an allocated GPU. Historical serial/OpenMP implementations and raw evidence remain intact.

## Timing definitions

`simulation_seconds`: synchronized host wall time from before begin-event recording through all generation launches and end-event synchronization. `kernel_event_seconds`: elapsed stream-event interval; includes gaps between launches, NOT a sum of pure kernel durations. Neither includes initialization, checksum, printing or transfers.

`gpu_e2e_seconds`: allocations/event creation + H2D + simulation + D2H + checked cleanup. Context initialization, device query and host output allocation precede this timer; host result import/validation follows it. This is a steady-context GPU operation metric, not whole-process cold-start latency. H2D and D2H are separately recorded synchronized host wall intervals. Each sample starts a new CLI process: host warmups are recorded but do not preserve a process context across samples.

## Correctness and validation

Naive baseline job 623417 passed 1,968 exact comparisons. Tuning job 623448 passed 5,904 exact cell/count/checksum comparisons across all three kernels and four blocks. Patterns include block, blinker, glider, horizontal/vertical/corner seams; dimensions include 1×1, 1×7, 7×1, 2×3, 17×33, 33×17 and 65×49. Seeds 0, 1, 12345 and UINT32_MAX; densities 0/35/100; generations 0/1/2/10/31. Pattern comparisons check every generation up to 12.

Known 101²×10 smoke remains 2213 live cells and checksum 7897773207305806522. Illegal blocks are rejected. Compute Sanitizer memcheck for each kernel on partial rectangular blocks and synccheck on narrow shared tiles reported zero errors. These checks are not a proof against every possible race. Every timed sample independently matches the serial live count and checksum. CPU regression suites pass locally and in the comparison job.

## Methodology and block tuning

One recorded warmup and five retained timed repetitions/configuration; deterministic shuffled ordering; density 35, seed 12345. No outlier removal. Summaries include median, mean, minimum and sample SD (n−1). Each subprocess has a 30-second watchdog. Profiling samples are never mixed into timing summaries.

Tuning: 512²×512 and 2048²×128; blocks 8×8, 16×16, 32×8, 32×16; 120 timed samples plus 24 warmups. Selection is predeclared: minimum median synchronized simulation time on 2048²×128, separately per kernel, then fastest kernel. Selection is fixed before the independent comparison. CLI/API historical default remains naive 16×16 for reproducibility; the recommended measured configuration is explicit in `selection.json`, not a universal optimum.

| Kernel | Selected block | Simulation median (ms) | E2E median (ms) | Simulation sample SD (ms) |
|---|---:|---:|---:|---:|
| naive | 32×16 | 4.959683 | 6.476450 | 0.159529 |
| direct | 16×16 | 4.264202 | 5.725115 | 0.195294 |
| shared | 16×16 | 8.375668 | 9.873750 | 0.307497 |

Shared memory did not win this tuning workload; additional halo/modulo/barrier instructions are plausible costs, not measured causal attribution. Direct offsets were retained as the recommended kernel. A small block-tuning difference may reflect noise; all four configurations remain available.

## Independent controlled CPU/GPU comparison

Same allocated node/job, same size/generations/density/seed/final state for every denominator. Serial V3, branch-free optimized CPU at 1 and 8 threads, and all three CUDA variants with fixed tuned blocks. OMP_DYNAMIC=FALSE, OMP_PROC_BIND=close, OMP_PLACES=cores. GPU uses the full allocated GPU; CPU team sizes never exceed allocation. Cross-backend ratios are not CPU parallel efficiency or a causal GPU-core-count claim.

| N / generations | Serial (s) | CPU1 (s) | OMP8 (s) | Best GPU simulation (s) | Event (s) | GPU E2E (s) | Serial / E2E | OMP8 / simulation | OMP8 / E2E |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 512 / 4096 | 4.49598 | 0.979333 | 0.135367 | 0.0266435 | 0.0266271 | 0.0270193 | 166.399 | 5.08067 | 5.00999 |
| 1024 / 1024 | 4.90257 | 0.952909 | 0.123594 | 0.0146524 | 0.0146352 | 0.0153407 | 319.58 | 8.43509 | 8.05664 |
| 2048 / 256 | 5.70322 | 0.941967 | 0.120862 | 0.0109265 | 0.0109084 | 0.0124107 | 459.541 | 11.0614 | 9.73856 |
| 4096 / 64 | 6.83413 | 0.938062 | 0.120322 | 0.0111832 | 0.0111695 | 0.0152915 | 446.922 | 10.7592 | 7.86852 |

Full naive/direct/shared medians, mean/min/sample SD, single-thread speedups and both serial simulation/E2E ratios are in `main-summary.csv`; raw samples are retained. The selected kernel may not win every size.

## CUDA optimization gain on independently measured workloads

| N | Naive / direct simulation | Shared / direct simulation |
|---|---:|---:|
| 512 | 1.285511 | 1.525227 |
| 1024 | 1.122913 | 1.826555 |
| 2048 | 1.257658 | 1.913033 |
| 4096 | 1.253169 | 2.214073 |

The fixed direct16×16 configuration wins every tested main workload, but this is not an optimality proof. The largest observed OMP8/E2E gain in this main experiment is 9.739×. Shared tiling is consistently slower despite its measured higher first-generation occupancy; occupancy alone does not determine runtime.

## Generation-count amortization and crossover

Fixed 1024² with 1/10/100/1000 generations; same four CPU/best-GPU configurations, 80 timed samples and 16 warmups.

| Generations | GPU simulation (ms) | GPU E2E (ms) | H2D+D2H median intervals (ms) | OMP8 / E2E |
|---|---:|---:|---:|---:|
| 1 | 0.176132 | 0.863587 | 0.425772 | 1.048296 |
| 10 | 0.270720 | 0.953246 | 0.428578 | 2.329854 |
| 100 | 1.297996 | 1.943771 | 0.423218 | 6.895684 |
| 1000 | 17.854795 | 18.536910 | 0.436101 | 6.592796 |

These measured points bracket any crossover only where the ratio changes sides of 1; no interpolated exact crossover or universal GPU advantage is claimed. Transfer/allocation overhead matters at small generation counts. Larger N runs use different generation counts to keep total updates practical; this is a workload-size study, not fixed-generation scaling.

## Measured small-grid crossover

Independent single-generation experiment, 64²/128²/256²/512²/1024², 100 timed samples and 20 warmups, same selection and eight-CPU/GPU allocation. CPU team creation is included in CPU simulation timing. Cold CUDA context startup remains excluded, as defined above.

| N | GPU E2E (ms) | CPU1 / E2E | OMP8 / E2E |
|---|---:|---:|---:|
| 64 | 0.440640 | 0.023466 | 1.917509 |
| 128 | 0.445068 | 0.065395 | 1.507417 |
| 256 | 0.482359 | 0.149277 | 1.433461 |
| 512 | 0.526692 | 0.467700 | 1.847062 |
| 1024 | 0.853468 | 1.110040 | 0.950156 |

Ratios below 1 favor CPU. CPU1 wins clearly on the smaller tested grids. OMP8 ratios are non-monotonic because its startup/scheduling cost is substantial for one generation; do not infer a unique hardware crossover from this series. The separate 1024² generation-count experiment and crossover repeat land on opposite sides of parity against OMP8 at one generation (about 1.05× versus 0.95×), demonstrating that this near-parity result is not a robust win. Ratios near 1 require more repeats and variability analysis. No exact universal crossover is claimed.

## Profiling and limitations

Baseline Nsight Compute (job 623417, first generation 2048², naive16×16) measured 65.472 µs kernel duration, 30 registers/thread, 86.12% achieved occupancy, 100% theoretical occupancy, 67.93% SM throughput and 4.14% DRAM throughput. These percentages are hardware peak-normalized throughput metrics, NOT cache hit rates. The profiler suggests compute instruction work is more active than DRAM, motivating direct offsets; it does not establish a universal bottleneck. Profiled CLI wall time includes replay/instrumentation and is not a valid benchmark runtime.

Nsight Systems baseline failed with filesystem permission denied at `/usr/local/cuda/lib`; the error is preserved. Follow-up profiler raw files document whether explicit toolkit paths help. Do not claim a measured launch timeline where capture failed. CPU/GPU virtualized environment, clock variation, driver/launch costs, pageable transfers, fresh-process setup, five-sample uncertainty and fixed-density workloads limit generalization. No unsupported cache-hit-rate/bandwidth claim, persistent kernel, MPI or manual AVX was added.

Follow-up Nsight Compute counters (first generation 2048², fixed 16×16):

| Kernel | Duration (µs) | Registers/thread | Achieved occupancy (%) |
|---|---:|---:|---:|
| direct | 54.272 | 25 | 82.62 |
| shared | 114.176 | 32 | 92.66 |

These are profile-specific first-generation measurements, not median long-simulation times or proof that occupancy determines speed. Explicit CUDA_HOME/CUDA_PATH/CUDA_INSTALL_PATH retry of nsys also failed at the same protected path; no Nsight Systems timeline was captured.

## Reproduction, evidence and history

`python3 scripts/analyse_cuda.py <directory>/<phase>.csv` validates and writes summaries. `python3 scripts/report_cuda.py --comparison results/cuda-comparison-623453 --tuning results/cuda-tuning-623448` regenerates this report. GPU Slurm scripts record environment, git revision, module/compiler/device information. Selection is a completed independent experiment, passed to `cuda_benchmark.slurm` via CUDA_SELECTION.

Raw directories: `results/cuda-environment-623387`, `results/cuda-environment-623393`, `results/cuda-baseline-623417`, `results/cuda-tuning-623448`, `results/cuda-comparison-623453`; follow-up profiles and failed smoke 623431 are retained separately. Each archive contains accounting, stdout/metadata, README and SHA256SUMS where applicable. No output timestamps were fabricated.

Source history: ff2e537 environment; 6a4afba device query; 4daf357 naive implementation/tests; d69b3d3 baseline profiling; 1f8965c direct/shared; 0c65775 corrected test scope and controlled tuning; 38af1f9 sample validation. Job CSV commit hashes identify exactly measured source; later evidence/report commits do not retroactively change those identities. Failed smoke 623431 was a test-variable scope compilation error, corrected before tuning; no invalid performance claim was made.

## Evidence worth using in the Milestone 2 presentation

- Allocated A100 capability 8.0 verified through the CUDA runtime, not inferred from node name.
- All three kernels pass 5,904 exact comparisons including narrow toroidal grids and partial shared tiles.
- Direct offsets beat shared tiling on the predeclared tuning workload; the slower shared result is preserved.
- 512²×4096: cuda_direct_v2 synchronized simulation 0.0266435 s; steady-context E2E 0.0270193 s; OMP8/E2E 5.010×; serial/E2E 166.399× (five-sample medians).
- 1024²×1024: cuda_direct_v2 synchronized simulation 0.0146524 s; steady-context E2E 0.0153407 s; OMP8/E2E 8.057×; serial/E2E 319.580× (five-sample medians).
- 2048²×256: cuda_direct_v2 synchronized simulation 0.0109265 s; steady-context E2E 0.0124107 s; OMP8/E2E 9.739×; serial/E2E 459.541× (five-sample medians).
- 4096²×64: cuda_direct_v2 synchronized simulation 0.0111832 s; steady-context E2E 0.0152915 s; OMP8/E2E 7.869×; serial/E2E 446.922× (five-sample medians).

Additional raw evidence: `results/cuda-profile-623467`, `results/cuda-crossover-623470`. Regenerate including `--profile` and `--crossover` with those directories. Evidence/report commits follow source commits; inspect `git log --oneline` for archive history.
