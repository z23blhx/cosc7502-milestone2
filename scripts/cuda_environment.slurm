#!/bin/bash
#SBATCH --job-name=life-cuda-env
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --time=00:02:00
#SBATCH --output=slurm-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
date -Is
hostname
git rev-parse HEAD
lscpu
nvidia-smi
nvidia-smi -q
command -v nvcc || true
nvcc --version || true
g++ --version
module list 2>&1 || true
module avail 2>&1 || true
for tool in nsys ncu nvprof compute-sanitizer cuda-memcheck; do command -v "$tool" || true; done
env | sort | grep -E '^(CUDA_|SLURM_|LOADEDMODULES|MODULEPATH)'
