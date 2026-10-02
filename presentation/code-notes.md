# Short code excerpts for the video

Current file locations are verified against the unchanged final source. `...` means omitted code and is not a compilable replacement. Show one excerpt at a time, using at least 22 pt monospace. Do not show complete files.

## 1. Synchronous double buffering

Source: `src/life.cpp`, `Life::step`, line 107 onward.

```cpp
const unsigned neighbours = live_neighbours(x, y);
next_[row_offset + x] = static_cast<Cell>(
    neighbours == 3 || (neighbours == 2 && current_[row_offset + x] != 0));
...
current_.swap(next_);
```

Explanation: Every output reads the old generation, even if another output has already completed. The swap happens after the complete serial traversal, preserving synchronous updates.

## 2. OpenMP row work sharing

Source: `src/life.cpp`, `Life::step_omp`, line 137 onward.

```cpp
#pragma omp parallel default(none) num_threads(threads) shared(actual_threads)
{
    ...
    #pragma omp for schedule(static)
    for (std::size_t y = 0; y < height_; ++y) {
        ... // compute only this output row
    }
}
current_.swap(next_);
```

Explanation: Static row ownership gives each output cell one writer. The worksharing barrier and region join finish the writes before this serial swap.

## 3. Persistent-team generation barrier and single swap

Source: `src/life.cpp`, `Life::run_persistent`, line 235 onward. These statements execute inside the team and generation loop.

```cpp
#pragma omp for schedule(static)
for (std::size_t y = 0; y < height_; ++y) update_row(y, kernel);
...
#pragma omp single
current_.swap(next_);
```

Explanation: The row loop's implicit barrier precedes the single swap. The single section's implicit barrier makes the new buffer identity visible before the next generation. The separate `single nowait` in the function only records actual team size and never swaps grids.

## 4. Branch-free transition

Source: `src/life.cpp`, `Life::update_row`, branch-free path line 206 onward.

```cpp
#pragma omp simd
for (std::size_t x = 1; x < width_ - 1; ++x) {
    ... // eight direct neighbour loads into n
    out[x] = static_cast<Cell>((n == 3) | ((n == 2) & (row[x] != 0)));
}
```

Explanation: Both Boolean predicates are safe to evaluate, so removing short-circuit control flow preserves the transition. GCC8's archived report confirms a vectorized interior loop after this change. The pragma-only v4 keeps `||`/`&&` and still has a compiler control-flow blocker.

## 5. CUDA thread-to-cell mapping

Source: `src/life_cuda.cu`, naive kernel line 38 onward.

```cpp
const std::size_t x = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
const std::size_t y = static_cast<std::size_t>(blockIdx.y) * blockDim.y + threadIdx.y;
if (x >= w || y >= h) return;
```

Explanation: A conventional two-dimensional launch assigns one cell to each active thread. The guard handles partial blocks. This early return belongs to the naive/direct kernels, not before the shared kernel's barrier.

## 6. Device pointer swap and generation ordering

Source: `src/life_cuda.cu`, host generation loop line 137 onward.

```cpp
for(std::size_t generation=0;generation<generations;++generation) {
    if(kernel==CudaKernel::Naive) naive<<<grid,block>>>(w,h,current,next);
    else if(kernel==CudaKernel::Direct) direct<<<grid,block>>>(w,h,current,next);
    else shared_tile<<<grid,block,shared_bytes>>>(w,h,current,next);
    check(cudaGetLastError(), "generation kernel launch");
    ... // optional debug-only device synchronization
    std::swap(current,next);
}
```

Explanation: Ordered launches in the same stream give the global generation dependency. Host pointer swapping passes reversed buffers to the next launch without copying cells. Final event synchronization completes the timed run before transfer/checksum.

## 7. Shared halo loading and the partial-block barrier

Source: `src/life_cuda.cu`, shared kernel line 70 onward.

```cpp
for(unsigned k=tid;k<pitch*rows;k+=workers) {
    const auto gx=(base_x+k%pitch+w-1)%w;
    const auto gy=(base_y+k/pitch+h-1)%h;
    tile[k]=current[gy*w+gx];
}
__syncthreads();
const auto x=base_x+threadIdx.x, y=base_y+threadIdx.y;
if(x>=w || y>=h) return;
```

Explanation: Even inactive edge threads help load the toroidal tile and reach the block barrier before returning. This synchronizes only that block's shared-memory loading, never the whole grid. Correctness is established for tested cases, but the measured implementation is slower.
