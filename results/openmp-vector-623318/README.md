# Long-workload branch-free vector followup

Job623318, source `684b067b54b952a8f5518cb0d7ab1312b159f914`, a100-b,
eightCPUs, GCC8.5.0. Completed0:0 in6m50s on2026-10-02.
Submitted with node=a100-b and afterok dependency on623308 to keep the same
guest environment; no source was changed in either running checkout.

`vector.csv` contains200timed samples:40configurations,five repeats each.
`warmups.csv` stores40separate warmups,excluded from summaries. Each size has
1,073,741,824 updates:512²×4096,1024²×1024,2048²×256,4096²×64generations.
Density35, seed12345, static contiguous rows, close binding/cores places.
Modes:serial1,original OpenMP8,SIMD-pragma v4 at1/2/4/8,and branchfree v5 at1/2/4/8.
No original OpenMP T1 measurement in this experiment, so its pure scaling is blank.

All timed/warmup results match serial count/checksum and requested actual teams.
Expanded small-grid correctness runs before timing. Compiler diagnostics record
the v5 interior loop as vectorized, unlike v4. Hardware/compiler/affinity are in
`environment.txt`; `slurm-623318.out` and `sacct.txt` are unedited.
`summary.csv` is derived with `scripts/analyse_openmp.py` and uses all samples.
The 1024²/v5/eight-thread outlier remains in the mean and standard deviation.

Independent PowerShell recomputation of the 4096²/v5/eight-thread mean,
median, sample SD, serial-relative speedup, pure scaling and efficiency agrees
with the derived Python summary. The exact statistics are in `summary.csv`.
Downloaded raw CSV and Slurm stdout SHA256 match those reported on Rangpur.
`SHA256SUMS.txt` records raw file hashes. Git does not normalize result bytes.

`local-gcc13-vector.txt` is a separately labelled local compiler report, not
Rangpur evidence. It was generated with g++-13/C++17/O3/fopenmp from the v5
source and corroborates vectorization on that different toolchain. No local
performance timing enters the Rangpur summary.
