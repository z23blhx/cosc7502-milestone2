#!/bin/bash
#SBATCH --job-name=life-cuda-tune
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --time=00:05:00
#SBATCH --output=slurm-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source /etc/profile.d/modules.sh
export PATH=/usr/local/cuda-12.2/bin:$PATH
out=results/cuda-tuning-$SLURM_JOB_ID
mkdir -p "$out"
{ date -Is; hostname; git rev-parse HEAD; nvcc --version; g++ --version; module list 2>&1; lscpu; env | sort | grep -E '^(CUDA_|SLURM_|LOADEDMODULES)'; } > "$out/environment.txt"
nvidia-smi -q > "$out/nvidia-smi.txt"
make cuda CUDA_ARCH=80
timeout 90s build/cuda/life_cuda_tests
python3 scripts/benchmark_cuda.py --phase tuning --out "$out"
for kernel in naive direct shared; do
    timeout 30s compute-sanitizer --tool memcheck build/cuda/life --backend cuda --cuda-kernel "$kernel" --width 33 --height 17 --generations 10 --block-x 32 --block-y 8 --csv > "$out/memcheck-$kernel.txt" 2>&1
done
timeout 30s compute-sanitizer --tool synccheck build/cuda/life --backend cuda --cuda-kernel shared --width 1 --height 7 --generations 10 --csv > "$out/synccheck-shared.txt" 2>&1
date -Is
