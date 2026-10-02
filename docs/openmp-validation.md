# OpenMP correctness validation - 2026-10-02

This records local correctness verification and the subsequent Rangpur
correctness smoke job. No formal performance experiment, CUDA implementation
or MPI implementation was run during this step.

## Design

The original serial `Life::step()` and `Life::run()` are unchanged. Separate
`step_omp(int)` and `run_omp(size_t, int)` methods use the same grids, toroidal
lookups, neighbour counter and rules. Each generation opens an OpenMP team:

```cpp
#pragma omp parallel default(none) num_threads(threads) shared(actual_threads)
#pragma omp single
#pragma omp for schedule(static)
```

The single section records the actual team size. The row loop writes each
`next_` cell exactly once, while `current_` and the lookups are read-only.
The implicit for barrier and parallel-region join precede the serial buffer
swap. Loop indices and block-local temporaries are private. The CLI disables
dynamic team selection outside the timed interval. Library callers should
configure the runtime likewise when they require a fixed team size.

Team creation and synchronization are included in generation timing. No
persistent-team optimization is attempted in this initial baseline.

## Builds actually executed

Windows: MinGW GCC 16.1.0, with static linking as in the inherited Makefile.

```powershell
mingw32-make debug benchmark profile
.\build\debug\life_tests.exe
mingw32-make OPENMP=0 debug benchmark
.\build\serial-only\debug\life_tests.exe
```

Linux: WSL Ubuntu 24.04.3, GCC 13.3.0 (`g++-13`). The generic `g++` name is
absent on this installation; the explicit compiler name was used.

```bash
make CXX=g++-13 BUILD_DIR=build/linux test benchmark profile
make CXX=g++-13 OPENMP=0 BUILD_DIR=build/linux-serial-only test benchmark
```

Both platforms built without compiler warnings. The warning flags were
`-Wall -Wextra -Wpedantic -Wconversion -Wshadow`; OpenMP builds used `-fopenmp`.
Debug, optimized and profiling targets compiled. The test suite ran in debug
builds; optimized executables ran the CLI smoke checks below. Profiling
executables were compiled but no profiling experiment was performed.

## Tests actually executed

- Six inherited serial tests passed on both platforms.
- Invalid thread-count API checks passed (0 and -1).
- 216 pattern comparisons checked every cell after each generation: block,
  blinker, glider, both boundary seams and a rectangular corner pattern,
  each at 1/2/4 threads for 12 generations.
- 1,260 random-grid comparisons checked every cell, count and checksum:
  dimensions 1x1, 1x7, 7x1, 2x3, 17x33, 33x17, 65x49; seeds 0, 1, 12345,
  4294967295; densities 0/35/100%; generations 0/1/2/10/31; threads 1/2/4.
- Three 101x101 deterministic serial/OpenMP comparisons passed in the suite.
- Both platforms' serial-only builds passed serial tests and rejected the
  unavailable OpenMP backend.
- Windows CLI checks passed: default serial backend, serial ignoring a valid
  thread request, zero generations, missing backend/thread values, unknown
  backend, threads 0/-1/1.5/abc/2147483648/18446744073709551616, negative size
  and non-finite density. Invalid inputs returned an error and nonzero status.
- Windows with `OMP_THREAD_LIMIT=2` and `--threads 4` correctly reported 2
  actual threads and retained the expected checksum. The environment was
  restored after the check.
- Both Slurm scripts passed `bash -n` during local verification. The OpenMP
  script was subsequently submitted to Rangpur, as recorded below.

## Optimized executable smoke results

Parameters: `--size 101 --generations 10 --density 35 --seed 12345 --csv`.
These results were observed on both Windows and Linux:

| Backend | Requested threads | Reported threads | Live cells | Checksum |
| --- | ---: | ---: | ---: | ---: |
| serial | default | 1 | 2213 | 7897773207305806522 |
| omp | 1 | 1 | 2213 | 7897773207305806522 |
| omp | 2 | 2 | 2213 | 7897773207305806522 |
| omp | 4 | 4 | 2213 | 7897773207305806522 |

All states, counts and checksums matched. Source inspection found no competing
writes in the generation update. No dedicated race detector was run. Single
tiny-run timings are not used to claim parallel speedup.

## Subsequent Rangpur verification

Job `623235` tested source commit `27087d73da1a9ef7867cf343cc0fda872b565ae2`
on `a100-a` with four CPUs and GCC 8.5.0. It completed with exit code `0:0`
in 5 seconds on 2026-10-02 (16:28:57 to 16:29:02 AEST). Compilation emitted
no warnings. All in-suite tests passed, followed by the optimized executable's
serial and OpenMP 1/2/4 smoke runs, each with 2,213 live cells and checksum
`7897773207305806522`.

The unedited log and accounting output are preserved in
[`results/openmp-smoke-623235`](../results/openmp-smoke-623235/README.md).
The downloaded log's SHA-256 matched the remote original. This verifies
correctness on a UQ cluster, not performance scaling.
