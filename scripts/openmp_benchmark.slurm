#!/bin/bash
#SBATCH --job-name=life-m2-scaling
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:15:00
#SBATCH --output=slurm-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
out=results/openmp-benchmark-$SLURM_JOB_ID
mkdir -p "$out"
export OMP_DYNAMIC=FALSE OMP_THREAD_LIMIT=$SLURM_CPUS_PER_TASK
export OMP_PROC_BIND=close OMP_PLACES=cores
{
    date -Is
    hostname
    git rev-parse HEAD
    git status --short
    lscpu
    g++ --version
    taskset -pc $$
    env | sort | grep -E '^(OMP_|SLURM_)'
    echo 'flags=-std=c++17 -O3 -DNDEBUG -fopenmp; no -march=native'
} | tee "$out/environment.txt"
make debug benchmark
timeout 25s ./build/debug/life_tests
g++ -std=c++17 -O3 -fopenmp -Isrc -fopt-info-vec-all="$out/vector.txt" -c src/life.cpp -o "$out/vector.o"
rm "$out/vector.o"
python3 scripts/benchmark_openmp.py --out "$out" --phase pilot
python3 scripts/benchmark_openmp.py --out "$out" --phase formal
python3 scripts/benchmark_openmp.py --out "$out" --phase tuning
date -Is
