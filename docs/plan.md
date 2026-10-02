# Milestone 2 development plan

This is a proposed implementation sequence, not an additional assessment rule.

Current status: the serial import, local OpenMP correctness verification and
Rangpur correctness job `623235` are complete. Formal performance experiments
remain pending. See `openmp-validation.md` for the exact completed checks.

1. Preserve the imported serial V3 reference and confirm the inherited tests and
   deterministic small workload. Record baseline provenance in the initial commit.
2. Add a CPU OpenMP implementation with explicit generation synchronization.
   Compare every cell against the serial reference for small square and rectangular
   grids, boundary patterns, several seeds, and several thread counts.
3. Add a CUDA implementation after correctness is established. Preserve toroidal
   boundaries and synchronous updates; keep state on the device across generations
   where appropriate. Measure transfers and kernel work with clearly defined timers.
4. Evaluate whether MPI would add useful distributed scaling evidence before
   implementing it. It is optional, not an assumed requirement.
5. Run small Slurm smoke checks first, then repeated controlled UQ cluster
   experiments. Record hardware, compiler flags, Git commit, workload, thread/rank
   counts, timing boundaries, checksums and raw logs. Explain serial-to-parallel
   speedup, scaling efficiency and any bottlenecks using measured evidence.
6. Prepare the self-contained video, figures, interview notes and final combined
   submission archive according to `docs/requirements.md`.

Announce any command expected to run longer than 30 seconds before starting it.
Do not start large benchmark jobs during repository setup.
