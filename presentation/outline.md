# Video outline

Working title: **Parallel Game of Life: OpenMP and CUDA**. Presenter: Lianquan Liu, 48287045.

Target: 8–9 minutes. Ten screens, one argument: correct synchronous updates make parallel work possible, but measured kernel choices and overhead determine the benefit. This is a self-contained Milestone 2 presentation.

| Screen | Topic | Budget | Running time |
|---|---|---:|---:|
| 1 | Objective and model | 30 s | 0:30 |
| 2 | Rules, torus and serial double buffering | 50 s | 1:20 |
| 3 | OpenMP row ownership and correctness | 50 s | 2:10 |
| 4 | CPU progression and compiler evidence | 80 s | 3:30 |
| 5 | v5 strong scaling and Amdahl interpretation | 60 s | 4:30 |
| 6 | CUDA mapping, resident buffers and timing | 55 s | 5:25 |
| 7 | CUDA tuning and shared-memory negative result | 60 s | 6:25 |
| 8 | Practical optimized CPU/GPU comparison | 55 s | 7:20 |
| 9 | Generation amortization, uncertainty and limits | 60 s | 8:20 |
| 10 | Reflection and conclusion | 30 s | 8:50 |

Timing budgets include brief figure-pointing pauses. Rehearse with a real stopwatch; word count is only an estimate. If too long, omit the optional serial-relative 58.61× sentence, extra profiler numbers and the second CPU panel explanation. Preserve the 7.77× baseline definition, 9.74× timing qualification, failed experiments and limits.

## Assessment coverage

- Introduction/background: screens 1–2, independent of the Milestone 1 video.
- Optimization: screens 3–4 and 6–7, including unsuccessful attempts.
- Benchmarking: explain fixed seeds, identical workloads, repeats and uncertainty on screens 4–5 and 8–9.
- Presentation: one primary figure or small code excerpt at a time, readable typography, face never covering evidence.
- Reflection/conclusion: screen 10 and limits on screen 9. Interview is a separate hurdle.

Do not read every data label aloud. Refer to `final-results.md` as the number authority and `code-notes.md` for excerpts. Keep all hardware claims scoped to the recorded Rangpur experiments.
