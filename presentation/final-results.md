# Presentation source of truth

Generated directly from immutable raw CSVs by `scripts/generate_final_figures.py`. All groups contain five timed repetitions. Values below are medians in seconds, with unrounded values preserved in `figures/provenance.json`. No benchmark is rerun.

CPU timers include generation work, team entry and barriers, excluding setup/checksum. CUDA simulation includes ordered launches and final synchronization. CUDA steady-context E2E includes allocation/events/transfers/cleanup, excluding context initialization, host output allocation and result import/checksum. Event interval includes launch gaps and is not summed kernel duration.

## Figure datasets

| Figure | Raw source |
|---|---|
| [cpu_optimization_progression](figures/cpu_optimization_progression.png) | `results/openmp-benchmark-623308/formal.csv`; `results/openmp-vector-623318/vector.csv` |
| [openmp_strong_scaling_runtime](figures/openmp_strong_scaling_runtime.png) | `results/openmp-vector-623318/vector.csv` |
| [openmp_strong_scaling_speedup](figures/openmp_strong_scaling_speedup.png) | `results/openmp-vector-623318/vector.csv` |
| [cuda_kernel_comparison](figures/cuda_kernel_comparison.png) | `results/cuda-comparison-623453/main.csv` |
| [cpu_vs_cuda](figures/cpu_vs_cuda.png) | `results/cuda-comparison-623453/main.csv` |
| [cuda_generation_amortization](figures/cuda_generation_amortization.png) | `results/cuda-comparison-623453/generations.csv` |

## Initial CPU progression, only 2048²×53

| Workload | Version | Threads / block | Median seconds | Timing column | Source |
|---|---|---|---:|---|---|
| 2048²×53 | `v3_explicit_neighbours` | 1 | 1.516718890 | `elapsed_seconds` | `results/openmp-benchmark-623308/formal.csv` |
| 2048²×53 | `omp_rows_v1` | 8 | 0.187584499 | `elapsed_seconds` | `results/openmp-benchmark-623308/formal.csv` |
| 2048²×53 | `omp_persistent_v2` | 8 | 0.213908376 | `elapsed_seconds` | `results/openmp-benchmark-623308/formal.csv` |
| 2048²×53 | `omp_interior_v3` | 8 | 0.143603861 | `elapsed_seconds` | `results/openmp-benchmark-623308/formal.csv` |
| 2048²×53 | `omp_simd_v4` | 8 | 0.136317305 | `elapsed_seconds` | `results/openmp-benchmark-623308/formal.csv` |

## Later CPU progression, only 4096²×64

| Workload | Version | Threads / block | Median seconds | Timing column | Source |
|---|---|---|---:|---|---|
| 4096²×64 | `v3_explicit_neighbours` | 1 | 7.059887220 | `elapsed_seconds` | `results/openmp-vector-623318/vector.csv` |
| 4096²×64 | `omp_rows_v1` | 8 | 0.867340041 | `elapsed_seconds` | `results/openmp-vector-623318/vector.csv` |
| 4096²×64 | `omp_simd_v4` | 8 | 0.635570039 | `elapsed_seconds` | `results/openmp-vector-623318/vector.csv` |
| 4096²×64 | `omp_branchfree_v5` | 8 | 0.120465009 | `elapsed_seconds` | `results/openmp-vector-623318/vector.csv` |

## v5 strong scaling, 4096²×64

| Workload | Version | Threads / block | Median seconds | Timing column | Source |
|---|---|---|---:|---|---|
| 4096²×64 | `omp_branchfree_v5` | 1 | 0.935899131 | `elapsed_seconds` | `results/openmp-vector-623318/vector.csv` |
| 4096²×64 | `omp_branchfree_v5` | 2 | 0.468973670 | `elapsed_seconds` | `results/openmp-vector-623318/vector.csv` |
| 4096²×64 | `omp_branchfree_v5` | 4 | 0.236367272 | `elapsed_seconds` | `results/openmp-vector-623318/vector.csv` |
| 4096²×64 | `omp_branchfree_v5` | 8 | 0.120465009 | `elapsed_seconds` | `results/openmp-vector-623318/vector.csv` |

## CUDA comparison, 2048²×256

| Workload | Version | Threads / block | Median seconds | Timing column | Source |
|---|---|---|---:|---|---|
| 2048²×256 | `cuda_naive_v1` | 32×16 | 0.013741817 | `simulation_seconds` | `results/cuda-comparison-623453/main.csv` |
| 2048²×256 | `cuda_direct_v2` | 16×16 | 0.010926513 | `simulation_seconds` | `results/cuda-comparison-623453/main.csv` |
| 2048²×256 | `cuda_shared_v3` | 16×16 | 0.020902777 | `simulation_seconds` | `results/cuda-comparison-623453/main.csv` |

## CPU/GPU practical comparison

| Workload | Version | Threads / block | Median seconds | Timing column | Source |
|---|---|---|---:|---|---|
| 512²×4096 | `omp_branchfree_v5` | 8 | 0.135366603 | `cpu_seconds` | `results/cuda-comparison-623453/main.csv` |
| 1024²×1024 | `omp_branchfree_v5` | 8 | 0.123594096 | `cpu_seconds` | `results/cuda-comparison-623453/main.csv` |
| 2048²×256 | `omp_branchfree_v5` | 8 | 0.120862109 | `cpu_seconds` | `results/cuda-comparison-623453/main.csv` |
| 4096²×64 | `omp_branchfree_v5` | 8 | 0.120321821 | `cpu_seconds` | `results/cuda-comparison-623453/main.csv` |
| 512²×4096 | `cuda_direct_v2` | 16×16 | 0.027019318 | `gpu_e2e_seconds` | `results/cuda-comparison-623453/main.csv` |
| 1024²×1024 | `cuda_direct_v2` | 16×16 | 0.015340659 | `gpu_e2e_seconds` | `results/cuda-comparison-623453/main.csv` |
| 2048²×256 | `cuda_direct_v2` | 16×16 | 0.012410679 | `gpu_e2e_seconds` | `results/cuda-comparison-623453/main.csv` |
| 4096²×64 | `cuda_direct_v2` | 16×16 | 0.015291536 | `gpu_e2e_seconds` | `results/cuda-comparison-623453/main.csv` |

## Generation amortization, 1024²

| Workload | Version | Threads / block | Median seconds | Timing column | Source |
|---|---|---|---:|---|---|
| 1024²×1 | `omp_branchfree_v5` | 8 | 0.000905295 | `cpu_seconds` | `results/cuda-comparison-623453/generations.csv` |
| 1024²×10 | `omp_branchfree_v5` | 8 | 0.002220924 | `cpu_seconds` | `results/cuda-comparison-623453/generations.csv` |
| 1024²×100 | `omp_branchfree_v5` | 8 | 0.013403630 | `cpu_seconds` | `results/cuda-comparison-623453/generations.csv` |
| 1024²×1000 | `omp_branchfree_v5` | 8 | 0.122210057 | `cpu_seconds` | `results/cuda-comparison-623453/generations.csv` |
| 1024²×1 | `cuda_direct_v2` | 16×16 | 0.000176132 | `simulation_seconds` | `results/cuda-comparison-623453/generations.csv` |
| 1024²×10 | `cuda_direct_v2` | 16×16 | 0.000270720 | `simulation_seconds` | `results/cuda-comparison-623453/generations.csv` |
| 1024²×100 | `cuda_direct_v2` | 16×16 | 0.001297996 | `simulation_seconds` | `results/cuda-comparison-623453/generations.csv` |
| 1024²×1000 | `cuda_direct_v2` | 16×16 | 0.017854795 | `simulation_seconds` | `results/cuda-comparison-623453/generations.csv` |
| 1024²×1 | `cuda_direct_v2` | 16×16 | 0.000863587 | `gpu_e2e_seconds` | `results/cuda-comparison-623453/generations.csv` |
| 1024²×10 | `cuda_direct_v2` | 16×16 | 0.000953246 | `gpu_e2e_seconds` | `results/cuda-comparison-623453/generations.csv` |
| 1024²×100 | `cuda_direct_v2` | 16×16 | 0.001943771 | `gpu_e2e_seconds` | `results/cuda-comparison-623453/generations.csv` |
| 1024²×1000 | `cuda_direct_v2` | 16×16 | 0.018536910 | `gpu_e2e_seconds` | `results/cuda-comparison-623453/generations.csv` |

## Ratios and allowed wording

| Claim | Unrounded ratio | Allowed rounded wording |
|---|---:|---|
| v5 T1/T8 | 7.769053759005 | 7.77× pure thread scaling |
| (v5 T1/T8)/8 | 97.113171987560% | 97.1% efficiency |
| serial / v5 T8 | 58.605293591934 | 58.61× serial-relative overall CPU speedup |
| OMP8 / direct E2E, 2048²×256 | 9.738557334373 | 9.74×, same job/workload |
| persistent / original rows minus 1 | 14.033076901519% | 14.0% slower, tested implementation |

Min–max whiskers show observed sample spread, not confidence intervals. Thread-scaling plot uses v5 T1, never the serial reference. CPU progression panels have independently labelled seconds axes and incompatible generation counts: compare within a panel only. CPU/GPU size series holds total cell updates constant, not generations. Near-parity small GPU claims and unmatched cross-job ratios are excluded.

## Compiler / profiler evidence

- `results/openmp-vector-623318/vector.txt`: GCC8 control-flow blocker for v4 and vectorized 16-byte interior loop for v5. This supports generated vectorization, not its isolated causal speedup.
- `results/cuda-profile-623467/ncu-direct.txt`, `ncu-shared.txt`: single first-generation profiles at 2048², 16×16. Direct 54.272 µs, occupancy 82.62%; shared 114.176 µs, occupancy 92.66%. These are separate from the median simulation bars.
- `results/cuda-comparison-623453` and `results/cuda-crossover-623470`: one-generation 1024² OMP8/E2E ratios fall on opposite sides of parity. No universal crossover claim.

Narration and slide labels use this file for rounding. Each source SHA and measured commit is recorded in provenance.json. Retain all raw samples and original timestamps.
