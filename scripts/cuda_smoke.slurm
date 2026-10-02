#!/bin/bash
#SBATCH --job-name=life-cuda-correct
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
export OMP_DYNAMIC=FALSE OMP_THREAD_LIMIT=$SLURM_CPUS_PER_TASK
date -Is
hostname
git rev-parse HEAD
nvidia-smi
nvcc --version
module list 2>&1
make benchmark cuda CUDA_ARCH=80
timeout 90s build/cuda/life_cuda_tests
timeout 20s build/cuda/life --backend cuda --size 101 --generations 10 --csv
date -Is
