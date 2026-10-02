# Milestone 2 submission checklist

Authority: personal `COSC3500_Milestone.pdf`, pages 1–2, re-read 2026-10-02. Blackboard screenshot confirms the same specification applies to Milestone 2. Personal PDF stays local and must not enter the public repository or ZIP.

Status labels: READY means the repository item exists. PENDING means a human/recording/upload action remains. UNCONFIRMED means the supplied course material does not establish it.

| Item | Status | Evidence / action |
|---|---|---|
| Well-commented source | READY | `src/life.cpp`, `life.h`, `main.cpp`, `life_cuda.cu`, `life_cuda.h`; source comment audit in `audit.md` |
| Makefile and build instructions | READY | Makefile, root README; CPU-only builds remain supported |
| Tests and Slurm scripts | READY | `tests/`, `scripts/`; launch workloads on allocated nodes |
| At least one UQ cluster benchmark | READY | Rangpur OpenMP jobs 623308/623318, GPU 623453, raw CSV/stdout/accounting |
| Figures traceable to raw data | READY | Six PNGs + SVGs; `figures/provenance.json`; `final-results.md` |
| Outline, narration, code and viva notes | READY | Ten-screen plan, approximately 1,090-word spoken draft, around 8.4 min at 130 words/min before pauses |
| Actual slides / screen recording | PENDING | Content plan exists; assemble the screens and rehearse |
| Video duration at most 10 minutes | PENDING | Course strictly caps at 10 min. Aim 8–9 min; packaging conservatively requires <600 s |
| Face visible throughout | PENDING | Required. Inspect the entire recording, including transitions and edits. Automated codec checks cannot establish this |
| Face does not obscure important content | PENDING | Reserve a presenter gutter or separate camera panel; inspect all graph labels |
| H.264 video codec | PENDING | `ffprobe` must report video `codec_name=h264`; MP4 extension alone is insufficient |
| Video strictly smaller than 100 MB | PENDING | Use conservative decimal limit 100,000,000 bytes, including audio/container. Keep sufficient ZIP headroom |
| Video filename | CONFIRMED | `Milestone2 48287045.mp4` |
| Combined code + video ZIP filename | CONFIRMED | `Milestone2 48287045.zip` |
| Combined final ZIP | PENDING | `scripts/prepare_submission.py` dry run / video validation / explicit creation. No final ZIP without the actual checked recording |
| Interview / viva hurdle | PENDING | Approximately 7 min, in-person identity verification. Specification describes second exam week; verify appointment and preparation in current course notices |
| Exact submission deadline | UNCONFIRMED | Supplied PDF/screenshot do not confirm a date. Check Blackboard and course profile; no date guessed |
| Detailed interview schedule / FAQ | UNCONFIRMED | Check current Blackboard, FAQ and course profile |
| Milestone 1 feedback applied | UNCONFIRMED | Feedback was not supplied in this task. Review it before recording |

## Recording/export procedure

1. Build the ten planned screens, rehearse aloud, and shorten before recording if necessary. Keep rule explanation and benchmark qualifications.
2. Record with your face continuously visible. Multiple edited takes are permitted by the specification. Check audio clarity, graph readability, cuts and lip sync yourself.
3. Export MP4 with H.264. For roughly nine minutes, a video rate around 1 Mbit/s plus modest audio may fit, but actual bytes control compliance. Test readability rather than blindly choosing a bitrate. A useful starting budget is total bits/sec < `(desired_bytes*8)/duration_seconds`.
4. Name the video exactly and run the packaging dry run. `ffprobe` is required for actual video checks. If unavailable, install it or pass its full path through `--ffprobe`.
5. Inspect the full final video, then use `--confirm-face` only after personally checking face visibility and unobscured content. This flag is an attestation, not an automated identity check.
6. Create the ZIP, reopen it to verify contents, upload to Blackboard, and confirm the submission receipt. Neither the script nor these notes submit anything automatically.

The PDF explicitly limits video size, not a separately stated ZIP size. The script conservatively caps the combined ZIP below 100 MB because of the referenced Blackboard upload limit. The final measured ZIP and current upload UI remain the authority for upload acceptance.
