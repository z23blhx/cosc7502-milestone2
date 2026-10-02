# COSC7502 Milestone 2 - Parallel Game of Life

This repository starts the parallel phase of the existing Conway's Game of
Life project. It preserves the **serial V3 reference** and adds a correctness-
verified OpenMP row-parallel backend. Formal Milestone 2 cluster measurements
have not been performed yet.

The model uses synchronous double-buffered updates, an eight-position Moore
neighbourhood, and toroidal boundaries. Dimensions, generations, initial density,
and random seed are configurable. Final live-cell counts and checksums make
correctness comparisons reproducible. NetLogo was used to confirm model settings;
the C++ implementation was developed separately.

## Baseline provenance

The initial `src/`, `tests/`, and `Makefile` are copied unchanged from
[Milestone 1](https://github.com/z23blhx/cosc7502-milestone1), commit
`b3f025026c8558ee69f3ac09cfe0721941f10441`. Its implementation is V3
(`v3_explicit_neighbours`, commit `60ebf199d20f8ffacee92b49b50ae85c76f1e6ef`)
with subsequent explanatory comments. The serial update remains unchanged and
reports `v3_explicit_neighbours`; the OpenMP backend reports `omp_rows_v1`.

## Build and run

Windows PowerShell with MinGW on PATH:

```powershell
mingw32-make test
mingw32-make benchmark
.\build\benchmark\life.exe --backend serial --size 101 --generations 10 --density 35 --seed 12345 --csv
.\build\benchmark\life.exe --backend omp --threads 4 --size 101 --generations 10 --density 35 --seed 12345 --csv
```

Linux / Rangpur:

```bash
make test
make benchmark
./build/benchmark/life --backend serial --size 101 --generations 10 --density 35 --seed 12345 --csv
for threads in 1 2 4; do
    ./build/benchmark/life --backend omp --threads "$threads" --size 101 --generations 10 --density 35 --seed 12345 --csv
done
```

OpenMP is enabled by default using `-fopenmp` at compilation and linking. If the
compiler is named `g++-13`, pass `CXX=g++-13` to make. A build without any OpenMP
dependency remains available with `make OPENMP=0 test benchmark` (Windows:
`mingw32-make OPENMP=0 test benchmark`), under `build/serial-only/`. Selecting
`--backend omp` in that build produces an explicit error.

The default backend is `serial`. `--threads` accepts a positive integer and
defaults to 1; the serial backend always reports 1. The OpenMP CLI disables
dynamic team sizing before timing. `threads` in the output records the actual
team size, which may be capped by an external `OMP_THREAD_LIMIT`; it is 0 for
an OpenMP run with zero generations, because no team was created.

This small workload finishes with 2,213 live cells and checksum
`7897773207305806522` for serial and OpenMP with 1, 2 or 4 threads. Only generation
execution is timed, including OpenMP team creation and barriers. Construction,
randomisation, runtime configuration, checksums and output are excluded.

CSV columns are:

```text
backend,version,width,height,generations,density,seed,threads,elapsed_seconds,live_cells,checksum
```

The schema adds backend and actual thread count to the inherited CSV format;
consumers should read columns by name. No performance claim is based on these
correctness smoke checks.

## Correctness and synchronization

`step()` / `run()` remain the serial reference. `step_omp(threads)` assigns rows
with static scheduling; `run_omp(generations, threads)` calls it once per generation.
Each thread reads `current_` and writes disjoint cells in `next_`. An implicit
worksharing barrier and the parallel-region join complete every write before
the calling thread swaps buffers. There is no `nowait` or concurrent swap.

The six inherited tests still run. OpenMP tests additionally compare every cell,
live-cell count and checksum for patterns, seams, rectangular and narrow grids,
four seeds, three densities, five generation counts and thread counts 1/2/4.
Tests require the environment to permit four threads. See the exact local
verification record in [docs/openmp-validation.md](docs/openmp-validation.md).

On Rangpur, submit the small serial smoke check through Slurm:

```bash
sbatch scripts/serial_smoke.slurm
```

The script uses the course account and partition `cosc3500`, one CPU and a
20-second execution timeout. Resource settings should be reviewed against the
current cluster configuration before larger experiments.

For a four-CPU correctness job covering both backends, use
`sbatch scripts/omp_smoke.slurm`. This script has only been syntax-checked locally;
it has not yet been submitted to Rangpur.

## Project layout

- `src/`: serial reference and OpenMP row-parallel implementation.
- `tests/`: inherited tests and direct serial/OpenMP comparisons.
- `scripts/`: cluster execution scripts.
- `docs/`: checked assessment requirements and development plan.
- `results/`: future reproducible Milestone 2 evidence.
- `presentation/`: future presentation material.
- `reference/`: local-only personal specification PDF, ignored by Git.
- `work/`: local scratch work, ignored by Git.
- `outputs/`: local deliverables, ignored by Git.

Read [the requirements checklist](docs/requirements.md) before implementation.
The proposed development sequence is documented in [the plan](docs/plan.md).
