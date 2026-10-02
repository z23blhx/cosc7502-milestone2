# COSC7502 Milestone 2 - Parallel Game of Life

This repository starts the parallel phase of the existing Conway's Game of
Life project. The current implementation is the **serial V3 reference**;
parallel implementations and Milestone 2 cluster measurements are not yet added.

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
with subsequent explanatory comments. The program still reports
`v3_explicit_neighbours` in CSV output, accurately identifying this serial reference.

## Build and run

Windows PowerShell with MinGW on PATH:

```powershell
mingw32-make test
mingw32-make benchmark
.\build\benchmark\life.exe --size 101 --generations 10 --density 35 --seed 12345 --csv
```

Linux / Rangpur:

```bash
make test
make benchmark
./build/benchmark/life --size 101 --generations 10 --density 35 --seed 12345 --csv
```

This small workload should finish quickly. With these parameters, the serial
reference finishes with 2,213 live cells and checksum `7897773207305806522`.
Only generation updates are timed; setup, validation and output are excluded.

On Rangpur, submit the small serial smoke check through Slurm:

```bash
sbatch scripts/serial_smoke.slurm
```

The script uses the course account and partition `cosc3500`, one CPU and a
20-second execution timeout. Resource settings should be reviewed against the
current cluster configuration before larger experiments.

## Project layout

- `src/`: current serial reference; future parallel backends.
- `tests/`: six inherited correctness tests.
- `scripts/`: cluster execution scripts.
- `docs/`: checked assessment requirements and development plan.
- `results/`: future reproducible Milestone 2 evidence.
- `presentation/`: future presentation material.
- `reference/`: local-only personal specification PDF, ignored by Git.
- `work/`: local scratch work, ignored by Git.
- `outputs/`: local deliverables, ignored by Git.

Read [the requirements checklist](docs/requirements.md) before implementation.
The proposed development sequence is documented in [the plan](docs/plan.md).
