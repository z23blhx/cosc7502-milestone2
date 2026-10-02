#include "life.h"

#include <cstdlib>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

using Position = std::pair<std::size_t, std::size_t>;

void require(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}
void require_state(const Life& life, const std::vector<Position>& live_positions,
                   const std::string& test_name) {
    std::vector<std::vector<bool>> expected(
        life.height(), std::vector<bool>(life.width(), false));
    for (const auto& [x, y] : live_positions) {
        expected[y][x] = true;
    }
    for (std::size_t y = 0; y < life.height(); ++y) {
        for (std::size_t x = 0; x < life.width(); ++x) {
            require(life.alive(x, y) == expected[y][x],
                    test_name + " differs at (" + std::to_string(x) + "," +
                        std::to_string(y) + ")");
        }
    }
}

Life with_pattern(std::size_t width, std::size_t height,
                  const std::vector<Position>& live_positions) {
    Life life(width, height);
    for (const auto& [x, y] : live_positions) {
        life.set(x, y, true);
    }
    return life;
}

void test_block_still_life() {
    const std::vector<Position> block{{2, 2}, {3, 2}, {2, 3}, {3, 3}};
    Life life = with_pattern(6, 6, block);
    const auto before = life.checksum();
    life.step();
    require_state(life, block, "block still life");
    require(life.checksum() == before, "block checksum changed after one generation");
}

void test_blinker_oscillator() {
    const std::vector<Position> horizontal{{1, 2}, {2, 2}, {3, 2}};
    const std::vector<Position> vertical{{2, 1}, {2, 2}, {2, 3}};
    Life life = with_pattern(5, 5, horizontal);
    const auto initial_checksum = life.checksum();
    life.step();
    require_state(life, vertical, "blinker generation one");
    life.step();
    require_state(life, horizontal, "blinker generation two");
    require(life.checksum() == initial_checksum, "blinker did not return to its initial state");
}

void test_glider() {
    const std::vector<Position> initial{{2, 1}, {3, 2}, {1, 3}, {2, 3}, {3, 3}};
    const std::vector<Position> after_four{{3, 2}, {4, 3}, {2, 4}, {3, 4}, {4, 4}};
    Life life = with_pattern(8, 8, initial);
    life.run(4);
    require_state(life, after_four, "glider after four generations");
}

void test_horizontal_wrapping() {
    // These three cells form a horizontal blinker across the left/right seam.
    const std::vector<Position> across_seam{{4, 2}, {0, 2}, {1, 2}};
    const std::vector<Position> expected{{0, 1}, {0, 2}, {0, 3}};
    Life life = with_pattern(5, 5, across_seam);
    life.step();
    require_state(life, expected, "toroidal horizontal wrapping");
}

void test_vertical_wrapping() {
    // The same idea across the top/bottom seam verifies both wrapped axes.
    const std::vector<Position> across_seam{{2, 4}, {2, 0}, {2, 1}};
    const std::vector<Position> expected{{1, 0}, {2, 0}, {3, 0}};
    Life life = with_pattern(5, 5, across_seam);
    life.step();
    require_state(life, expected, "toroidal vertical wrapping");
}

void test_seed_reproducibility() {
    Life first(101, 101);
    Life second(101, 101);
    Life different_seed(101, 101);
    first.randomise(35.0, 12345);
    second.randomise(35.0, 12345);
    different_seed.randomise(35.0, 54321);
    require(first.checksum() == second.checksum(), "same seed produced different initial states");
    require(first.checksum() != different_seed.checksum(), "different seeds produced the same initial state");
}

} // namespace

int main() {
    try {
        test_block_still_life();
        test_blinker_oscillator();
        test_glider();
        test_horizontal_wrapping();
        test_vertical_wrapping();
        test_seed_reproducibility();
        std::cout << "PASS: 6 correctness tests\n";
        return EXIT_SUCCESS;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return EXIT_FAILURE;
    }
}
