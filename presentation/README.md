# Milestone 2 presentation preparation

The evidence, figures and English speaking materials are prepared. An actual
slide deck, student recording and final code+video ZIP are **not yet produced**.

## Reading order

1. [Final results](final-results.md): numerical source of truth and timing scope.
2. [Outline](outline.md) and [slide plan](slide-plan.md): ten screens, 8:50 budget.
3. [Narration](narration.md): about 1,090 spoken words, approximately 8.4 minutes at
   130 words/minute before pauses; aim for 8.7–9 minutes after rehearsal.
4. [Code notes](code-notes.md): short source excerpts, not standalone programs.
5. [Reflection](reflection.md) and [24 interview questions](interview-notes.md).
6. [Submission checklist](submission-checklist.md) and [packaging](packaging.md).
7. [Audit](audit.md): scope, exclusions and retained negative evidence.

## Figure inventory

All figures have PNG and editable SVG versions in `figures/`. Each value is a
five-repetition median; min–max whiskers are observed spread, not confidence
intervals. [provenance.json](figures/provenance.json) preserves individual samples,
source hashes, recorded commits and unrounded ratios.

| Figure stem | Raw CSV source under `results/` |
|---|---|
| `cpu_optimization_progression` | `openmp-benchmark-623308/formal.csv`; `openmp-vector-623318/vector.csv` |
| `openmp_strong_scaling_runtime` | `openmp-vector-623318/vector.csv` |
| `openmp_strong_scaling_speedup` | `openmp-vector-623318/vector.csv` |
| `cuda_kernel_comparison` | `cuda-comparison-623453/main.csv` |
| `cpu_vs_cuda` | `cuda-comparison-623453/main.csv` |
| `cuda_generation_amortization` | `cuda-comparison-623453/generations.csv` |

CPU progression has two independent workload panels: do not compare runtimes
across them. Strong scaling uses **v5 T1**, not serial V3, as denominator.
CPU/GPU comparisons use GPU steady-context end-to-end time. The generation
figure separately shows simulation timing and transfer/allocation-inclusive
timing. Constant total updates across grid sizes are not weak scaling.

Colors are restrained (blue CPU, orange GPU, gray negative, charcoal reference).
Labels, markers and CPU/GPU bar hatching also distinguish series. Keep figure
labels readable and reserve a camera gutter so the student's face never covers
evidence. Rehearse the actual deck/video: word count is not a duration guarantee.

Regenerate with `python scripts/generate_final_figures.py`; run tool checks with
`python -m unittest discover -s tests -p test_submission_tools.py`.
Neither command starts a benchmark. The packaging command is dry-run by default
and requires a clean committed checkout, actual H.264 MP4 and human face
confirmation before it can create the final ZIP.
