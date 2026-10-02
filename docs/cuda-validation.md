# CUDA evidence validation

Validation completed on 2026-10-02, without changing prior CPU evidence.

- GPU correctness: naive 1,968 comparisons in job 623417; all three kernels 5,904 comparisons in job 623448 and again before the comparison in 623453. Every comparison checks full cells, count and checksum.
- Sanitizers: three rectangular partial-block memchecks and a narrow-grid shared synccheck report zero errors in 623448.
- Accounting: successful environment/baseline/tuning/comparison/profile/crossover jobs have `COMPLETED`, exit `0:0`. Failed test compilation 623431 and cancelled job 623412 are preserved. The latter acquired a GPU allocation and started environment probing/CPU compilation before cancellation; neither supplies completed CUDA tests or benchmarks.
- Local Linux GCC13 OpenMP test suite and serial-only `OPENMP=0` tests passed; Windows MinGW OpenMP suite and benchmark build passed. CUDA is not claimed to run on the Windows laptop.
- Dataset checks: 40 baseline + 120 tuning + 120 main + 80 generation + 100 crossover timed rows, plus 92 recorded warmups. Five distinct repetitions per configuration; complete expected group counts; one source/job/node identity per dataset; fixed seed/density; matching count/checksum per workload; positive finite times; E2E >= simulation; actual CPU team checked at capture; exact device-buffer footprint checked. No samples removed.
- Independent PowerShell recomputation for direct16×16, 2048²×128 tuning samples: median `0.004264202`, mean `0.0043021042`, sample SD `0.00019529373327682582` seconds. These agree with the Python summary, independently of its statistics implementation.
- All ratios use same-job, same-workload CPU medians as denominators. Profiling wall times are excluded. Event elapsed time is not mislabeled as a sum of kernel durations. Full-process cold-start time is not claimed.
- Small single-generation CPU/GPU near-parity results vary between independent batches. The report explicitly avoids a precise universal crossover claim.
- Archive SHA256SUMS covers exact captured bytes; metadata/source hashes identify measured commits rather than later report commits.

The validation script is `scripts/analyse_cuda.py`. Report generation is `scripts/report_cuda.py`. This is a bounded validation of measured configurations, not an exhaustive concurrency proof or guarantee for other GPUs/toolkits.
