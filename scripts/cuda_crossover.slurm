#!/bin/bash
#SBATCH --job-name=life-cuda-small
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --time=00:03:00
#SBATCH --output=slurm-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
: "${CUDA_SELECTION:?Completed selection required}"
source /etc/profile.d/modules.sh
export PATH=/usr/local/cuda-12.2/bin:$PATH
export OMP_DYNAMIC=FALSE OMP_THREAD_LIMIT=$SLURM_CPUS_PER_TASK OMP_PROC_BIND=close OMP_PLACES=cores
out=results/cuda-crossover-$SLURM_JOB_ID
mkdir -p "$out"
{ date -Is; hostname; git rev-parse HEAD; nvcc --version; g++ --version; module list 2>&1; lscpu; taskset -pc $$; env | sort | grep -E '^(CUDA_|SLURM_|OMP_)'; } > "$out/environment.txt"
nvidia-smi -q > "$out/nvidia-smi.txt"
make cuda CUDA_ARCH=80
python3 scripts/benchmark_cuda.py --phase crossover --out "$out" --selection "$CUDA_SELECTION"
