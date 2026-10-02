# Final ZIP procedure

The final ZIP cannot exist yet: the student's real video is not supplied. This script does not record, synthesize or upload a video.

Expected archive structure:

```text
Milestone2 48287045.zip
  Milestone2 48287045.mp4
  code/
    README.md
    Makefile
    src/
    tests/
    scripts/
    docs/
    results/
    presentation/
    SUBMISSION_SOURCE.json
```

Only relevant tracked files enter the code folder. Include annotated source, build/tests/Slurm scripts, supporting documentation, figures and curated raw evidence including informative unsuccessful experiments. Exclude `.git`, binaries, scratch/cache/reference directories, personal specification PDFs, video drafts, existing ZIPs and large binary profiler databases. Do not delete any repository evidence to make the package smaller.

From the repository, with Python 3:

```powershell
# Dry run: curated list, revision, expected structure, no ZIP
python scripts/prepare_submission.py

# Check the actual recording, without creating a ZIP
python scripts/prepare_submission.py --video "outputs\Milestone2 48287045.mp4"

# Only after watching the complete video and confirming identity visibility
python scripts/prepare_submission.py --video "outputs\Milestone2 48287045.mp4" --confirm-face --create
```

Pass `--ffprobe "C:\path\to\ffprobe.exe"` if it is not on PATH. Video validation checks the actual H.264 stream, MP4 container, duration and byte count. It cannot establish face visibility or assess slide readability. Keep the workspace committed/clean so metadata identifies the exact package. Existing archives are never overwritten. Use a different `--output-dir` for a subsequent version.

The script leaves at least 1 MB input headroom below 100 MB and verifies the final combined archive is under the conservative 100 MB limit. It checks ZIP CRCs and includes source hashes. A partial archive from a failure is not a valid submission.

The ZIP intentionally contains no Git database. Compilation and correctness tests work directly from `code/`. For original benchmark provenance and scripts that require `git rev-parse HEAD`, clone the public repository and check out the recorded source commit. `SUBMISSION_SOURCE.json` identifies the packaged revision, while every experiment CSV retains its own measured revision. Do not pretend a new local `git init` recreates the original history.

Before upload, reopen the ZIP and check its root video and code files. Upload using the course portal, verify the receipt and retain your copy. Deadline and interview appointment still require current Blackboard confirmation.
