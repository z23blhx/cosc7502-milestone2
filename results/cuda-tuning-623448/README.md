# cuda-tuning-623448

Captured allocated-GPU experiment. See environment/stdout and sacct for source, hardware, exit status and timings. 120 timed samples + 24 warmups; all three kernels, four blocks; selection based only on 2048x2048x128 synchronized simulation median.

Raw files are unchanged. CSV summaries are derived with scripts/analyse_cuda.py (five samples, sample SD n-1). SHA256SUMS checks bytes of all archive files other than itself.
