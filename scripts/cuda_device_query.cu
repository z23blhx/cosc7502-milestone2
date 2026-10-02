#include <cuda_runtime.h>
#include <cstdio>
int main() {
    int count=0, driver=0, runtime=0;
    if (cudaGetDeviceCount(&count)!=cudaSuccess || cudaDriverGetVersion(&driver)!=cudaSuccess ||
        cudaRuntimeGetVersion(&runtime)!=cudaSuccess) return 1;
    std::printf("device_count=%d driver_api=%d runtime_api=%d\n", count, driver, runtime);
    for(int i=0;i<count;++i) {
        cudaDeviceProp p{};
        if(cudaGetDeviceProperties(&p,i)!=cudaSuccess) return 1;
        std::printf("device=%d name=%s capability=%d.%d memory_bytes=%zu max_threads=%d max_block=%d,%d,%d shared_per_block=%zu\n",
                    i,p.name,p.major,p.minor,p.totalGlobalMem,p.maxThreadsPerBlock,
                    p.maxThreadsDim[0],p.maxThreadsDim[1],p.maxThreadsDim[2],p.sharedMemPerBlock);
    }
}
