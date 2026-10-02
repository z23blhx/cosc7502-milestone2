#ifndef COSC7502_LIFE_H
#define COSC7502_LIFE_H

#include <cstddef>
#include <cstdint>
#include <vector>

class Life {
public:
    // A cell needs only two states: 0 is dead and 1 is alive. The fixed-width
    // byte representation also keeps the grid format consistent across builds.
    using Cell = std::uint8_t;

    Life(std::size_t width, std::size_t height);

    std::size_t width() const noexcept;
    std::size_t height() const noexcept;

    void clear() noexcept;
    // A deterministic seed reproduces the same initial grid, allowing fair
    // correctness and performance comparisons between optimisation versions.
    void randomise(double density_percent, std::uint32_t seed);
    void set(std::size_t x, std::size_t y, bool alive);
    bool alive(std::size_t x, std::size_t y) const;

    // Advance exactly one synchronous Game of Life generation.
    void step();
    // Advance the requested number of generations by repeatedly calling step().
    void run(std::size_t generations);

    // Separate OpenMP entry points keep step()/run() as the serial reference.
    // Return the actual team size (run_omp returns 0 for zero generations).
    static bool openmp_available() noexcept;
    int step_omp(int threads);
    int run_omp(std::size_t generations, int threads);
    enum class Kernel { Lookup, Interior, Simd, Branchfree };
    int run_persistent(std::size_t generations, int threads,
                       Kernel kernel = Kernel::Lookup, int chunk = 0);

    // These independent correctness indicators help verify that optimised
    // versions finish with the same state, not merely a similar runtime.
    std::uint64_t live_count() const noexcept;
    std::uint64_t checksum() const noexcept;
    // Backend interoperability only; the serial/OpenMP update paths are unchanged.
    const std::vector<Cell>& cells() const noexcept { return current_; }
    void assign_cells(std::vector<Cell> cells);

private:
    // Cells occupy one contiguous row-major allocation; (x, y) maps to
    // y * width_ + x, avoiding the row indirection of a two-dimensional vector.
    using Grid = std::vector<Cell>;

    unsigned live_neighbours(std::size_t x, std::size_t y) const noexcept;
    void update_row(std::size_t y, Kernel kernel) noexcept;

    std::size_t width_;
    std::size_t height_;

    // Double buffering preserves lockstep updates: every cell reads current_,
    // writes next_, and the buffers are swapped only after the generation is complete.
    Grid current_;
    Grid next_;

    // Precomputed toroidal coordinates avoid repeating wrapping arithmetic in
    // the neighbour-count hot path while retaining edge-to-edge connectivity.
    std::vector<std::size_t> x_prev_;
    std::vector<std::size_t> x_next_;
    std::vector<std::size_t> y_prev_;
    std::vector<std::size_t> y_next_;
};

#endif
