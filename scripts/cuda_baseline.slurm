#!/bin/bash
#SBATCH --job-name=life-cuda-baseline
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
out=results/cuda-baseline-$SLURM_JOB_ID
mkdir -p "$out"
{ date -Is; hostname; git rev-parse HEAD; nvcc --version; g++ --version; module list 2>&1; env | sort | grep -E '^(CUDA_|SLURM_|OMP_|LOADEDMODULES)'; } > "$out/environment.txt"
nvidia-smi -q > "$out/nvidia-smi.txt"
make cuda CUDA_ARCH=80
timeout 90s build/cuda/life_cuda_tests
python3 scripts/benchmark_cuda.py --phase baseline --out "$out"
timeout 30s compute-sanitizer --tool memcheck build/cuda/life --backend cuda --width 33 --height 17 --generations 10 --csv > "$out/memcheck.txt" 2>&1 || echo 'memcheck unavailable/failed: inspect raw log'
timeout 30s nsys profile --sample=none --trace=cuda -o "$out/naive-nsys" build/cuda/life --backend cuda --size 2048 --generations 10 --csv > "$out/nsys.txt" 2>&1 || echo 'nsys unavailable/failed: inspect raw log'
if test -f "$out/naive-nsys.nsys-rep"; then
    timeout 20s nsys stats --report cuda_gpu_kern_sum,cuda_api_sum --format csv "$out/naive-nsys.nsys-rep" > "$out/nsys-stats.txt" 2>&1 || true
fi
timeout 30s ncu --set basic --launch-count 1 --csv build/cuda/life --backend cuda --size 2048 --generations 1 --csv > "$out/ncu.txt" 2>&1 || echo 'ncu unavailable/failed: inspect raw log'
date -Is
