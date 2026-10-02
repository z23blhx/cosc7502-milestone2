# Milestone 2 results

Rangpur correctness job [623235](openmp-smoke-623235/README.md) verified the
serial reference and OpenMP backend on the cluster. The unedited job log and
accounting record are stored with that experiment. Local checks are documented
in `docs/openmp-validation.md`.

Completed Step2 evidence:

- [Baseline profiling623307](baseline-profile-623307/README.md).
- [Scaling and schedule tuning623308](openmp-benchmark-623308/README.md):425timed samples.
- [Branch-free vector followup623318](openmp-vector-623318/README.md):200timed samples.
- [Setup failures](step2-setup-failures/README.md):retained,excluded from timings.

See `docs/openmp-performance.md` for methodology, findings, limitations and
presentation-worthy evidence. `summary.csv` is derived; raw CSV/stdout are
immutable evidence. Git preserves original result bytes through .gitattributes.

For each future experiment, retain the exact source commit, Slurm job ID,
hardware and compiler information, complete workload parameters, raw timings,
and correctness evidence. Keep claims traceable to measured results.
