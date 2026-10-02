#!/usr/bin/env bash
#SBATCH --job-name=life-m2-omp-smoke
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:02:00
#SBATCH --output=slurm-%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the project root}"

date -Is
hostname
git rev-parse HEAD
g++ --version
export OMP_DYNAMIC=FALSE
export OMP_THREAD_LIMIT="${SLURM_CPUS_PER_TASK}"
make debug benchmark
timeout 20s ./build/debug/life_tests
timeout 20s ./build/benchmark/life --backend serial \
    --size 101 --generations 10 --density 35 --seed 12345 --csv
for threads in 1 2 4; do
    timeout 20s ./build/benchmark/life --backend omp --threads "${threads}" \
        --size 101 --generations 10 --density 35 --seed 12345 --csv
done
