#!/bin/bash
#SBATCH --job-name=life-cuda-profile
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --time=00:03:00
#SBATCH --output=slurm-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source /etc/profile.d/modules.sh
export PATH=/usr/local/cuda-12.2/bin:$PATH
export CUDA_HOME=/usr/local/cuda-12.2 CUDA_PATH=/usr/local/cuda-12.2 CUDA_INSTALL_PATH=/usr/local/cuda-12.2
out=results/cuda-profile-$SLURM_JOB_ID
mkdir -p "$out"
{ date -Is; hostname; git rev-parse HEAD; nvcc --version; module list 2>&1; } > "$out/environment.txt"
nvidia-smi -q > "$out/nvidia-smi.txt"
make cuda CUDA_ARCH=80
for kernel in direct shared; do
    timeout 30s ncu --set basic --launch-count 1 --csv build/cuda/life --backend cuda --cuda-kernel "$kernel" --size 2048 --generations 1 --block-x 16 --block-y 16 --csv > "$out/ncu-$kernel.txt" 2>&1
done
# One safe retry with explicit toolkit location; a tool failure is preserved, not a benchmark.
timeout 30s nsys profile --trace=cuda --sample=none --cpuctxsw=none -o "$out/timeline" build/cuda/life --backend cuda --cuda-kernel direct --size 2048 --generations 10 --csv > "$out/nsys.txt" 2>&1 || echo "nsys unavailable; inspect recorded error"
