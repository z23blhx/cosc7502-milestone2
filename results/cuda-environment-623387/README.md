# cuda-environment-623387

Captured allocated-GPU experiment. See environment/stdout and sacct for source, hardware, exit status and timings. Initial discovery: default PATH lacked nvcc; follow-up 623393 verified explicit CUDA 12.2 toolkit.

Raw files are unchanged. CSV summaries are derived with scripts/analyse_cuda.py (five samples, sample SD n-1). SHA256SUMS checks bytes of all archive files other than itself.
