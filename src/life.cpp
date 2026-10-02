#include "life.h"

#include <algorithm>
#include <limits>
#include <random>
#include <stdexcept>

Life::Life(std::size_t width, std::size_t height)
    : width_(width),
      height_(height),
      current_(width * height, 0),
      next_(width * height, 0),
      x_prev_(width),
      x_next_(width),
      y_prev_(height),
      y_next_(height) {
    if (width == 0 || height == 0) {
        throw std::invalid_argument("grid dimensions must be positive");
    }

    // Toroidal neighbours depend only on the grid dimensions. Precomputing
    // these four lookups avoids recalculating wrapped coordinates for every
    // neighbour of every cell in every generation.
    for (std::size_t x = 0; x < width_; ++x) {
        x_prev_[x] = (x == 0) ? width_ - 1 : x - 1;
        x_next_[x] = (x + 1 == width_) ? 0 : x + 1;
    }
    for (std::size_t y = 0; y < height_; ++y) {
        y_prev_[y] = (y == 0) ? height_ - 1 : y - 1;
        y_next_[y] = (y + 1 == height_) ? 0 : y + 1;
    }
}
std::size_t Life::width() const noexcept {
    return width_;
}

std::size_t Life::height() const noexcept {
    return height_;
}

void Life::clear() noexcept {
    std::fill(current_.begin(), current_.end(), Cell{0});
    std::fill(next_.begin(), next_.end(), Cell{0});
}

void Life::randomise(double density_percent, std::uint32_t seed) {
    if (density_percent < 0.0 || density_percent > 100.0) {
        throw std::invalid_argument("density must be between 0 and 100 percent");
    }

    // mt19937 has a standardised output sequence. Comparing its integer output
    // with an explicit threshold makes a seed reproduce the same starting grid
    // locally and on Rangpur, which keeps version comparisons fair.
    std::mt19937 random(seed);
    constexpr std::uint64_t outcomes =
        static_cast<std::uint64_t>(std::numeric_limits<std::uint32_t>::max()) + 1ULL;
    const auto threshold = static_cast<std::uint64_t>(
        (density_percent / 100.0) * static_cast<double>(outcomes));

    for (auto& cell : current_) {
        cell = static_cast<Cell>(static_cast<std::uint64_t>(random()) < threshold);
    }
}

void Life::set(std::size_t x, std::size_t y, bool alive_state) {
    if (x >= width_ || y >= height_) {
        throw std::out_of_range("cell coordinate is outside the grid");
    }
    current_[y * width_ + x] = static_cast<Cell>(alive_state);
}

bool Life::alive(std::size_t x, std::size_t y) const {
    if (x >= width_ || y >= height_) {
        throw std::out_of_range("cell coordinate is outside the grid");
    }
    return current_[y * width_ + x] != 0;
}

unsigned Life::live_neighbours(std::size_t x, std::size_t y) const noexcept {
    const std::size_t xm = x_prev_[x];
    const std::size_t xp = x_next_[x];
    const std::size_t row_above = y_prev_[y] * width_;
    const std::size_t row_here = y * width_;
    const std::size_t row_below = y_next_[y] * width_;

    // A Moore neighbourhood contains exactly these eight cells. Listing them
    // explicitly avoids a generic 3x3 loop and its centre-skip branch while
    // leaving the toroidal neighbour semantics unchanged.
    return current_[row_above + xm] + current_[row_above + x] +
           current_[row_above + xp] + current_[row_here + xm] +
           current_[row_here + xp] + current_[row_below + xm] +
           current_[row_below + x] + current_[row_below + xp];
}

void Life::step() {
    // Read only from current_ and write only to next_. Swapping only after every
    // cell is calculated preserves Game of Life's synchronous generation rule.
    // The flat grid maps (x, y) to y * width_ + x. Row-major order keeps cells
    // with neighbouring x coordinates adjacent in one contiguous allocation.
    for (std::size_t y = 0; y < height_; ++y) {
        const std::size_t row_offset = y * width_;
        for (std::size_t x = 0; x < width_; ++x) {
            const unsigned neighbours = live_neighbours(x, y);
            next_[row_offset + x] = static_cast<Cell>(
                neighbours == 3 || (neighbours == 2 && current_[row_offset + x] != 0));
        }
    }
    current_.swap(next_);
}

void Life::run(std::size_t generations) {
    for (std::size_t generation = 0; generation < generations; ++generation) {
        step();
    }
}

std::uint64_t Life::live_count() const noexcept {
    std::uint64_t count = 0;
    for (Cell cell : current_) {
        count += cell;
    }
    return count;
}

std::uint64_t Life::checksum() const noexcept {
    // FNV-1a over dimensions and cells is deterministic and sensitive to cell
    // positions, so it can detect mismatches that live_count() alone cannot.
    std::uint64_t hash = 14695981039346656037ULL;
    constexpr std::uint64_t prime = 1099511628211ULL;
    const auto mix = [&hash](std::uint8_t byte) {
        hash ^= byte;
        hash *= prime;
    };

    for (unsigned shift = 0; shift < 64; shift += 8) {
        mix(static_cast<std::uint8_t>(width_ >> shift));
        mix(static_cast<std::uint8_t>(height_ >> shift));
    }
    for (Cell cell : current_) {
        mix(cell);
    }
    return hash;
}
