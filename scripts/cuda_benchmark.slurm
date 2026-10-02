#!/bin/bash
#SBATCH --job-name=life-cuda-compare
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --time=00:15:00
#SBATCH --output=slurm-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
: "${CUDA_SELECTION:?Pass path to completed tuning selection via sbatch --export}"
source /etc/profile.d/modules.sh
export PATH=/usr/local/cuda-12.2/bin:$PATH
export OMP_DYNAMIC=FALSE OMP_THREAD_LIMIT=$SLURM_CPUS_PER_TASK OMP_PROC_BIND=close OMP_PLACES=cores
out=results/cuda-comparison-$SLURM_JOB_ID
mkdir -p "$out"
{ date -Is; hostname; git rev-parse HEAD; git status --short; nvcc --version; g++ --version; module list 2>&1; lscpu; taskset -pc $$; env | sort | grep -E '^(CUDA_|SLURM_|OMP_|LOADEDMODULES)'; } > "$out/environment.txt"
nvidia-smi -q > "$out/nvidia-smi.txt"
make debug cuda CUDA_ARCH=80
timeout 25s build/debug/life_tests
timeout 90s build/cuda/life_cuda_tests
python3 scripts/benchmark_cuda.py --phase main --out "$out" --selection "$CUDA_SELECTION"
python3 scripts/benchmark_cuda.py --phase generations --out "$out" --selection "$CUDA_SELECTION"
date -Is
