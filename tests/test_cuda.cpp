#include "life_cuda.h"
#include <iostream>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>

void equal(const Life& reference, const Life& candidate) {
    if(reference.cells()!=candidate.cells() || reference.live_count()!=candidate.live_count() ||
       reference.checksum()!=candidate.checksum()) throw std::runtime_error("CUDA state mismatch");
}
int main() {
    try {
        using Position=std::pair<std::size_t,std::size_t>;
        const std::vector<std::vector<Position>> patterns{
            {{2,2},{3,2},{2,3},{3,3}}, {{1,2},{2,2},{3,2}},
            {{2,1},{3,2},{1,3},{2,3},{3,3}}, {{6,2},{0,2},{1,2}},
            {{2,4},{2,0},{2,1}}, {{6,4},{0,4},{1,0},{0,1},{1,1}}};
        std::size_t comparisons=0;
        for(const auto& block : std::vector<Position>{{8,8},{16,16},{32,8},{32,16}}) {
            for(const auto& pattern : patterns) {
                Life initial(7,5);
                for(const auto& cell : pattern) initial.set(cell.first,cell.second,true);
                Life reference=initial;
                for(std::size_t generation=1;generation<=12;++generation) {
                    reference.step();
                    Life candidate=initial;
                    run_cuda(candidate,generation,CudaKernel::Naive,
                             static_cast<unsigned>(block.first),static_cast<unsigned>(block.second),true);
                    equal(reference,candidate); ++comparisons;
                }
            }
            for(const auto& shape : std::vector<Position>{{1,1},{1,7},{7,1},{2,3},{17,33},{33,17},{65,49}})
                for(std::uint32_t seed : {0U,1U,12345U,std::numeric_limits<std::uint32_t>::max()})
                    for(double density : {0.0,35.0,100.0})
                        for(std::size_t generations : {0U,1U,2U,10U,31U}) {
                            Life initial(shape.first,shape.second); initial.randomise(density,seed);
                            Life reference=initial; reference.run(generations);
                            Life candidate=initial;
                            run_cuda(candidate,generations,CudaKernel::Naive,
                                static_cast<unsigned>(block.first),static_cast<unsigned>(block.second),true);
                            equal(reference,candidate); ++comparisons;
                        }
        }
        Life smoke(101,101); smoke.randomise(35,12345);
        run_cuda(smoke,10,CudaKernel::Naive);
        if(smoke.live_count()!=2213 || smoke.checksum()!=7897773207305806522ULL)
            throw std::runtime_error("CUDA known smoke changed");
        bool rejected=false;
        try { run_cuda(smoke,1,CudaKernel::Naive,1024,2); }
        catch(const std::invalid_argument&) { rejected=true; }
        if(!rejected) throw std::runtime_error("illegal block accepted");
        std::cout << "PASS CUDA naive: " << comparisons << " exact-state/count/checksum comparisons; known smoke; invalid block\n";
    } catch(const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n'; return 1;
    }
}
