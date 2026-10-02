# Rangpur OpenMP correctness smoke - job 623235

- Tested source commit: `27087d73da1a9ef7867cf343cc0fda872b565ae2`.
- Script: `scripts/omp_smoke.slurm` at that commit.
- Partition/account: `cosc3500`; one node `a100-a`, four allocated CPUs.
- Compiler: GCC 8.5.0; warnings enabled; OpenMP option `-fopenmp`.
- Start/end: 2026-10-02 16:28:57 / 16:29:02 AEST.
- Status: `COMPLETED`, exit code `0:0`, elapsed 5 seconds.

The log records successful inherited serial tests, invalid-thread API checks,
216 per-generation pattern comparisons, 1,260 random-grid comparisons and
three in-suite deterministic smoke comparisons. All state comparisons included
every cell, live-cell count and checksum at thread counts 1/2/4.

The optimized executable then ran serial and OpenMP 1/2/4 with
`--size 101 --generations 10 --density 35 --seed 12345 --csv`. All four results
have 2,213 live cells and checksum `7897773207305806522`. The reported OpenMP
team sizes are exactly 1, 2 and 4. These tiny runs establish correctness;
their timings are not formal performance or scaling evidence.

`slurm-623235.out` is the unedited job output downloaded from Rangpur.
`accounting.txt` records the returned `sacct --parsable2` output. Its timestamps
use the cluster's AEST time zone. The downloaded log was checked against the
remote SHA-256:

```text
9dd1c21286b5a6b0312014be6d3dbd791dd40a2c20705c339164399c4b5a4e57  slurm-623235.out
```
