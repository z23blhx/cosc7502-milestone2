#include "life_cuda.h"
#include <cuda_runtime.h>
#include <chrono>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>

namespace {
using Cell = Life::Cell;
using Clock = std::chrono::steady_clock;
void check(cudaError_t status, const char* operation) {
    if (status != cudaSuccess)
        throw std::runtime_error(std::string(operation) + ": " + cudaGetErrorString(status));
}
double seconds(Clock::time_point start, Clock::time_point end) {
    return std::chrono::duration<double>(end-start).count();
}
struct Resources {
    Cell* a = nullptr;
    Cell* b = nullptr;
    cudaEvent_t begin = nullptr;
    cudaEvent_t end = nullptr;
    ~Resources() { // Best-effort cleanup on an already failing operation; successful cleanup is checked.
        if (a) cudaFree(a);
        if (b) cudaFree(b);
        if (begin) cudaEventDestroy(begin);
        if (end) cudaEventDestroy(end);
    }
    void close() {
        check(cudaFree(a), "cudaFree current"); a=nullptr;
        check(cudaFree(b), "cudaFree next"); b=nullptr;
        check(cudaEventDestroy(begin), "event destroy begin"); begin=nullptr;
        check(cudaEventDestroy(end), "event destroy end"); end=nullptr;
    }
};

__global__ void naive(std::size_t w, std::size_t h, const Cell* current, Cell* next) {
    const std::size_t x = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    const std::size_t y = static_cast<std::size_t>(blockIdx.y) * blockDim.y + threadIdx.y;
    if (x >= w || y >= h) return;
    const auto xm = x == 0 ? w-1 : x-1;
    const auto xp = x+1 == w ? 0 : x+1;
    const auto ym = y == 0 ? h-1 : y-1;
    const auto yp = y+1 == h ? 0 : y+1;
    const unsigned n = current[ym*w+xm] + current[ym*w+x] + current[ym*w+xp] +
                       current[y*w+xm] + current[y*w+xp] + current[yp*w+xm] +
                       current[yp*w+x] + current[yp*w+xp];
    next[y*w+x] = static_cast<Cell>(n == 3 || (n == 2 && current[y*w+x]));
}

__global__ void direct(std::size_t w, std::size_t h, const Cell* current, Cell* next) {
    const std::size_t x=static_cast<std::size_t>(blockIdx.x)*blockDim.x+threadIdx.x;
    const std::size_t y=static_cast<std::size_t>(blockIdx.y)*blockDim.y+threadIdx.y;
    if(x>=w || y>=h) return;
    const auto i=y*w+x;
    unsigned n;
    if(x>0 && x+1<w && y>0 && y+1<h) {
        n=current[i-w-1]+current[i-w]+current[i-w+1]+current[i-1]+current[i+1]+
          current[i+w-1]+current[i+w]+current[i+w+1];
    } else {
        const auto xm=x==0?w-1:x-1, xp=x+1==w?0:x+1;
        const auto ym=y==0?h-1:y-1, yp=y+1==h?0:y+1;
        n=current[ym*w+xm]+current[ym*w+x]+current[ym*w+xp]+current[y*w+xm]+current[y*w+xp]+
          current[yp*w+xm]+current[yp*w+x]+current[yp*w+xp];
    }
    next[i]=static_cast<Cell>(n==3 || (n==2 && current[i]));
}

__global__ void shared_tile(std::size_t w, std::size_t h, const Cell* current, Cell* next) {
    extern __shared__ Cell tile[];
    const unsigned pitch=blockDim.x+2, rows=blockDim.y+2;
    const unsigned tid=threadIdx.y*blockDim.x+threadIdx.x;
    const unsigned workers=blockDim.x*blockDim.y;
    const std::size_t base_x=static_cast<std::size_t>(blockIdx.x)*blockDim.x;
    const std::size_t base_y=static_cast<std::size_t>(blockIdx.y)*blockDim.y;
    // Cooperative interior+halo loading wraps even inactive partial-block cells.
    // Every worker reaches the block-local barrier before any bounds-based return.
    for(unsigned k=tid;k<pitch*rows;k+=workers) {
        const auto gx=(base_x+k%pitch+w-1)%w;
        const auto gy=(base_y+k/pitch+h-1)%h;
        tile[k]=current[gy*w+gx];
    }
    __syncthreads();
    const auto x=base_x+threadIdx.x, y=base_y+threadIdx.y;
    if(x>=w || y>=h) return;
    const auto i=(threadIdx.y+1)*pitch+threadIdx.x+1;
    const unsigned n=tile[i-pitch-1]+tile[i-pitch]+tile[i-pitch+1]+tile[i-1]+tile[i+1]+
                     tile[i+pitch-1]+tile[i+pitch]+tile[i+pitch+1];
    next[y*w+x]=static_cast<Cell>(n==3 || (n==2 && tile[i]));
}
}

CudaStats run_cuda(Life& life, std::size_t generations, CudaKernel kernel,
                   unsigned block_x, unsigned block_y, bool debug_sync) {
    if(kernel!=CudaKernel::Naive && kernel!=CudaKernel::Direct && kernel!=CudaKernel::Shared)
        throw std::invalid_argument("unknown CUDA kernel");
    int device=0;
    check(cudaGetDevice(&device), "cudaGetDevice");
    cudaDeviceProp prop{};
    check(cudaGetDeviceProperties(&prop,device), "cudaGetDeviceProperties");
    if (!block_x || !block_y || block_x > static_cast<unsigned>(prop.maxThreadsDim[0]) ||
        block_y > static_cast<unsigned>(prop.maxThreadsDim[1]) ||
        static_cast<std::size_t>(block_x)*block_y > static_cast<unsigned>(prop.maxThreadsPerBlock))
        throw std::invalid_argument("illegal CUDA block dimensions");
    const auto w=life.width(), h=life.height();
    if (w > std::numeric_limits<std::size_t>::max()/h)
        throw std::invalid_argument("CUDA grid size overflow");
    const auto gx=(w-1)/block_x+1, gy=(h-1)/block_y+1;
    if (gx > static_cast<unsigned>(prop.maxGridSize[0]) || gy > static_cast<unsigned>(prop.maxGridSize[1]))
        throw std::invalid_argument("CUDA launch grid exceeds device limits");
    const dim3 block(block_x,block_y), grid(static_cast<unsigned>(gx),static_cast<unsigned>(gy));
    const std::size_t shared_bytes=(static_cast<std::size_t>(block_x)+2)*(block_y+2)*sizeof(Cell);
    if(kernel==CudaKernel::Shared && shared_bytes>prop.sharedMemPerBlock)
        throw std::invalid_argument("shared tile exceeds block shared-memory limit");
    const auto bytes=w*h*sizeof(Cell);
    if (bytes > std::numeric_limits<std::size_t>::max()/2)
        throw std::invalid_argument("CUDA allocation size overflow");
    std::vector<Cell> output(w*h);
    check(cudaFree(nullptr), "initialize CUDA context");
    CudaStats stats{};
    stats.device_bytes=2*bytes;
    Resources resources;
    const auto e2e_begin=Clock::now();
    check(cudaMalloc(reinterpret_cast<void**>(&resources.a),bytes), "cudaMalloc current");
    check(cudaMalloc(reinterpret_cast<void**>(&resources.b),bytes), "cudaMalloc next");
    check(cudaEventCreate(&resources.begin), "event create begin");
    check(cudaEventCreate(&resources.end), "event create end");
    auto before=Clock::now();
    check(cudaMemcpy(resources.a,life.cells().data(),bytes,cudaMemcpyHostToDevice), "copy H2D");
    check(cudaDeviceSynchronize(), "finish H2D");
    stats.h2d_seconds=seconds(before,Clock::now());
    Cell* current=resources.a;
    Cell* next=resources.b;
    const auto simulation_begin=Clock::now();
    check(cudaEventRecord(resources.begin), "record simulation begin");
    for(std::size_t generation=0;generation<generations;++generation) {
        if(kernel==CudaKernel::Naive) naive<<<grid,block>>>(w,h,current,next);
        else if(kernel==CudaKernel::Direct) direct<<<grid,block>>>(w,h,current,next);
        else shared_tile<<<grid,block,shared_bytes>>>(w,h,current,next);
        check(cudaGetLastError(), "generation kernel launch");
        if(debug_sync) check(cudaDeviceSynchronize(), "debug generation synchronization");
        // Same-stream launch ordering is the grid-wide generation boundary.
        // Host pointer swapping copies no cells and does not reorder queued kernels.
        std::swap(current,next);
    }
    check(cudaEventRecord(resources.end), "record simulation end");
    check(cudaEventSynchronize(resources.end), "complete simulation");
    stats.simulation_seconds=seconds(simulation_begin,Clock::now());
    float milliseconds=0;
    check(cudaEventElapsedTime(&milliseconds,resources.begin,resources.end), "event elapsed time");
    stats.kernel_event_seconds=static_cast<double>(milliseconds)/1000.0;
    before=Clock::now();
    check(cudaMemcpy(output.data(),current,bytes,cudaMemcpyDeviceToHost), "copy D2H");
    stats.d2h_seconds=seconds(before,Clock::now());
    resources.close();
    stats.gpu_e2e_seconds=seconds(e2e_begin,Clock::now());
    life.assign_cells(std::move(output));
    return stats;
}
