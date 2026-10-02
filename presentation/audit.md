# Step 4 repository and claim audit

Audited 2026-10-02 from clean main at `066e833`. This step changes presentation/tooling, not algorithms or benchmark evidence.

## Requirements and missing items

Read README, requirements, OpenMP validation/design/performance, CUDA validation/performance, recent history, source, tests, build/benchmark/analysis scripts and results inventory. Re-read both pages of the personal Milestone PDF locally. Do not redistribute that PDF. The Blackboard screenshot states Milestone 2 uses the same specification.

The technical artifacts exist. `presentation/` initially held only `.gitkeep`. Missing user deliverables: actual slides/screens, the student's recording with face visible, validated video and final combined ZIP. Step 4 supplies figures, outline, screen plan, English narration, code notes, viva notes, reflection and a packaging procedure. It does not fabricate a video or certify identity visibility.

## Selected story

Focus on serial V3, OpenMP rows v1 and branch-free v5. Use persistent v2 as a failed hypothesis. Briefly explain interior row pointers and the compiler's SIMD control-flow blocker. Show naive/direct/shared CUDA, with direct16×16 as the measured recommendation and shared as the negative result.

Strongest selected claims: v5 7.769053759× T1/T8 and 97.113171988% efficiency on 4096²×64; separately 58.605293592× serial-relative overall CPU gain. Main practical GPU headline: OMP8/direct E2E 9.738557334× on identical 2048²×256 in job 623453.

## Issues resolved or carefully scoped

- README still described the start of the parallel phase and future presentation material. Update it to the completed CPU/CUDA scope and concise marker navigation.
- `results/README.md` omitted CUDA evidence. Add links without modifying experiment files.
- No single archived CPU workload contains all six versions including v5. Use two separately labelled progression panels: 2048²×53 in 623308, then 4096²×64 in 623318. Never directly compare their runtimes.
- CPU long-run job 623318 and CPU/GPU job 623453 both contain 4096²×64 but differ in source/job. Use 623318 for scaling and 623453 for GPU ratios. Never substitute the old CPU denominator into the new GPU ratio.
- GPU E2E excludes context startup, host output allocation and import/checksum. Show this qualification whenever the headline comparison appears.
- CUDA event interval includes launch gaps. Use synchronized simulation wall time for the kernel-version plot and E2E for the practical comparison.
- The single-generation OMP8/GPU repeats straddle parity. Exclude an exact universal crossover claim. Fixed-total-update size experiments are not weak scaling or a Gustafson validation.
- Shared first-generation occupancy exceeds direct occupancy yet its kernel is slower. Do not infer speed from occupancy or treat peak throughput percentages as cache hit rates.
- Persistent-team restructuring is not a clean isolation of team startup overhead. Its measured slowdown is 14.033%, with generated-code differences also present.
- CPU hardware counters and Nsight Systems capture were unavailable. No cache/misprediction rate or launch timeline claim.
- Test compilation failure 623431 and cancellation 623412 remain distinct from successful correctness jobs. No raw timestamp or sample is changed.

## Material to omit from the ten-minute video

Chronological commits, every block/chunk/binding configuration, all 1,000+ raw rows, full source files, installation logs and profiler exceptions. Keep them inspectable in the code/evidence package. Do not headline the 459× serial/GPU number, call 58.6× eight-thread scaling, claim universal shared-memory failure, or claim complete cold-process latency.

## Source comment audit

`life.cpp` already explains the serial reference, deterministic initialization, row ownership, safe branch-free predicates, worksharing barrier and single-swap barrier. `life.h` explains row-major storage and double buffering. `life_cuda.cu` explains partial-block halo/barrier participation and same-stream generation ordering, plus checked cleanup. `life_cuda.h` states timing exclusions. The comments are sufficient for assessment readability; no source rewrite or comment-only line renumbering is necessary. Preserve tested source bytes.

## Verification scope

The figure generator checks complete selected raw matrices, five distinct repeats/group, actual CPU teams, state equality, provenance, finite positive timings and GPU buffer sizes before rendering. Figure manifests store exact raw-source SHA256, sample arrays and measured commits. Charts show medians and observed min–max ranges, not invented confidence intervals. Source datasets remain immutable. Generated artifacts are reproducible and locally rendered for review. Video duration, encoding and size remain unverified until the student's recording exists. Face visibility and interview participation require human confirmation.

## Local verification, 2026-10-02

- Regenerated and visually inspected all six PNGs, including labels, axes,
  workload captions and timing qualifiers; SVG companions were also generated.
- Thirteen small Python tool tests passed. These exercise incomplete/malformed
  CSVs, duplicate repetitions, mixed provenance, state mismatches, and video
  filename/codec/container/duration/size gates. Video metadata objects are mocks;
  these tests do not validate a real recording.
- Independently recomputed principal medians with PowerShell `Import-Csv` and
  sorting, without importing the plot generator: v5 T1 0.935899131 s; T8
  0.120465009 s; T1/T8 7.76905375900482; efficiency 97.1131719875603%; overall
  serial-relative ratio 58.6052935919342. In the controlled CUDA job: OMP8
  0.120862109 s, direct E2E 0.012410679 s, ratio 9.73855733437308.
- Original CPU/CUDA archive SHA256 manifests were checked (92 files). Experiment-file diffs
  remain empty; only the top-level results index changes. No `src/` changes,
  new remote run, benchmark campaign or raw timestamp rewrite occurred.
- Final package preparation is deliberately a dry run until an actual student
  video is supplied. Face visibility is not machine-certified.
