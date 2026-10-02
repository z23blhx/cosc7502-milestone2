# Ten-screen content plan

This is a content/layout plan, not a completed PowerPoint. Use 16:9 slides. Suggested title/body sizes: 32/22 pt or larger. Reserve a dedicated face-video gutter on the right, around 20% of width, across every screen. Place figures entirely to its left, or show the presenter separately beside the screen capture. Do not put the face over plot labels or source notes. The PNGs need no decorative stock images.

| Screen | Title | Visible content | Visual / source | Spoken purpose |
|---|---|---|---|---|
| 1 | Parallel Game of Life | Lianquan Liu; 48287045; COSC7502 Milestone 2. Objective: preserve exact generations while reducing execution time. | Minimal title, no dense result list | Establish model and CPU/GPU question |
| 2 | Synchronous cellular updates | Birth at 3 neighbors; survival at 2 or 3; toroidal edges; separate current/next grids. | Small current/read and next/write schematic, with a complete-generation swap; code note 1 | Explain semantics and why cells can run independently |
| 3 | OpenMP row ownership | Static disjoint output rows. Read-only current grid. Barrier before swap. Exact state tests. | Code notes 2–3, maximum eight visible lines at once | Show correctness and synchronization, not whole files |
| 4 | CPU optimization evidence | Persistent v2 was slower. Row pointers/direct interior accesses helped. SIMD pragma alone failed. Branch-free predicates enabled vectorization. | `cpu_optimization_progression.png`; zoom each panel separately, retaining its workload caption. Small compiler quotation: `LOOP VECTORIZED` with source/job label | Explain a measured progression without mixing the two workloads |
| 5 | OpenMP strong scaling | v5, 4096²×64, 1/2/4/8 threads. 7.77× T1/T8. 97.1% efficiency. | First `openmp_strong_scaling_runtime.png`, then `openmp_strong_scaling_speedup.png` on the same screen; preserve ideal line | Distinguish thread scaling from overall serial-relative speedup |
| 6 | CUDA generation pipeline | One thread/cell. Two resident device grids. One H2D + one D2H. Same-stream kernel boundary per generation. | Code notes 5–6, simple labelled host/device sequence | Explain safe grid-wide ordering and timing boundaries |
| 7 | CUDA kernel comparison | Naive 32×16, direct 16×16, shared 16×16; fixed before the comparison. Shared slower on this workload. | `cuda_kernel_comparison.png`, 2048²×256, synchronized simulation metric | Show measured direct addressing improvement and failed tiling hypothesis |
| 8 | Optimized CPU versus CUDA | Identical work, same job. Headline: 2048²×256, 120.86 ms OMP8 versus 12.41 ms CUDA steady-context E2E, 9.74×. | `cpu_vs_cuda.png`; visible note: E2E includes transfers/allocation/cleanup, excludes cold context | Make the practical comparison with the optimized CPU denominator |
| 9 | GPU overhead and limits | Fixed 1024², four generation counts. Setup/transfers matter. Near-parity results vary. Only eight CPU threads; VM sharing; five repeats. | `cuda_generation_amortization.png`; leave log-scale labels and min–max note visible | Explain amortization and why size-series data does not establish weak scaling |
| 10 | Conclusions | Preserve semantics. Verify generated code. Retain failed experiments. Measure overhead. | Three short conclusions; no new figures/numbers | Finish with evidence and a specific next investigation, not extra algorithms |

## Optional details to keep off the main screens

58.605× is a correctly labelled overall serial-relative CPU result, not an eight-thread scaling headline. The large serial/GPU ratio is not the main CPU/GPU result. Detailed block matrices, chunk/binding tuning, profiler raw tables and commit history belong in the package or interview notes. Mention the profile only as support, with “hypothesis” for unmeasured causal mechanisms.

Figure SVGs preserve editable text/vector geometry. If rebuilding charts as native PowerPoint objects, use `figures/provenance.json` rather than manually approximating bars. Never change the axis origins, timing definitions or source workload captions.
