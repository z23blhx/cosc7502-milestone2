#!/usr/bin/env bash
#SBATCH --job-name=life-m2-serial-smoke
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:02:00
#SBATCH --output=slurm-%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the project root}"

date -Is
hostname
git rev-parse HEAD
g++ --version
make benchmark

# The imported executable is still the serial V3 reference.
timeout 20s ./build/benchmark/life \
    --size 101 --generations 10 --density 35 --seed 12345 --csv
