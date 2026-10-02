#!/bin/bash
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:03:00
#SBATCH --output=slurm-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
out=results/baseline-profile-$SLURM_JOB_ID
mkdir -p "$out"
git rev-parse HEAD
lscpu
g++ --version
export OMP_DYNAMIC=FALSE OMP_THREAD_LIMIT=8 OMP_PROC_BIND=close OMP_PLACES=cores
make benchmark
g++ -std=c++17 -O3 -fopenmp -Isrc -fopt-info-optimized -c src/life.cpp -o "$out/inline.o" 2> "$out/inline.txt"
g++ -std=c++17 -O3 -fopenmp -Isrc -fopt-info-vec-all -c src/life.cpp -o "$out/vector.o" 2> "$out/vector.txt"
if command -v perf; then
  perf stat ./build/benchmark/life --size 512 --generations 32 --csv > "$out/perf.txt" 2>&1 || true
fi
g++ -std=c++17 -O3 -g -pg -fopenmp -Isrc src/main.cpp src/life.cpp -o "$out/profile"
timeout 20s "$out/profile" --size 1024 --generations 128 --csv
gprof "$out/profile" gmon.out > "$out/gprof.txt"
for backend in serial omp; do
  for threads in 1 8; do
    timeout 20s ./build/benchmark/life --backend "$backend" --threads "$threads" --size 1024 --generations 128 --csv
  done
done
rm "$out/inline.o" "$out/vector.o" "$out/profile"
