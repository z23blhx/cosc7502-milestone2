# cuda-comparison-623453

Captured allocated-GPU experiment. See environment/stdout and sacct for source, hardware, exit status and timings. 120 main + 80 generation-study timed samples; 24 + 16 warmups. Fixed tuning selection, same-job serial/CPU1/OMP8/GPU comparison. See docs/cuda-performance.md for exact timing exclusions.

Raw files are unchanged. CSV summaries are derived with scripts/analyse_cuda.py (five samples, sample SD n-1). SHA256SUMS checks bytes of all archive files other than itself.
