#ifndef COSC7502_LIFE_CUDA_H
#define COSC7502_LIFE_CUDA_H
#include "life.h"
enum class CudaKernel { Naive, Direct, Shared };
struct CudaStats {
    double simulation_seconds = 0; // host wall: ordered launches and final event synchronization
    double kernel_event_seconds = 0; // stream events: includes gaps between generation launches
    double gpu_e2e_seconds = 0; // allocations/events + H2D + simulation + D2H + cleanup
    double h2d_seconds = 0;
    double d2h_seconds = 0;
    std::size_t device_bytes = 0;
};
// Context initialization and host output allocation occur before measured e2e.
// State validation/import, checksum and printing occur after measured e2e.
CudaStats run_cuda(Life& life, std::size_t generations, CudaKernel kernel,
                   unsigned block_x = 16, unsigned block_y = 16, bool debug_sync = false);
#endif
