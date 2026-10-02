#include "life.h"

#include <cstdlib>
#include <exception>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

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

void require_equal(const Life& serial, const Life& parallel, const std::string& name) {
    require(serial.width() == parallel.width() && serial.height() == parallel.height(),
            name + " dimensions differ");
    for (std::size_t y = 0; y < serial.height(); ++y) {
        for (std::size_t x = 0; x < serial.width(); ++x) {
            require(serial.alive(x, y) == parallel.alive(x, y),
                    name + " differs at (" + std::to_string(x) + "," + std::to_string(y) + ")");
        }
    }
    require(serial.live_count() == parallel.live_count(), name + " live counts differ");
    require(serial.checksum() == parallel.checksum(), name + " checksums differ");
}

void test_openmp_patterns() {
    struct Pattern {
        const char* name;
        std::size_t width;
        std::size_t height;
        std::vector<Position> cells;
    };
    const std::vector<Pattern> patterns{
        {"block", 6, 6, {{2, 2}, {3, 2}, {2, 3}, {3, 3}}},
        {"blinker", 5, 5, {{1, 2}, {2, 2}, {3, 2}}},
        {"glider", 8, 8, {{2, 1}, {3, 2}, {1, 3}, {2, 3}, {3, 3}}},
        {"horizontal seam", 5, 5, {{4, 2}, {0, 2}, {1, 2}}},
        {"vertical seam", 5, 5, {{2, 4}, {2, 0}, {2, 1}}},
        {"rectangular corner", 9, 5, {{8, 4}, {0, 4}, {1, 0}, {0, 1}, {1, 1}}}
    };
    for (int threads : {1, 2, 4}) {
        for (const auto& pattern : patterns) {
            Life serial = with_pattern(pattern.width, pattern.height, pattern.cells);
            Life parallel = serial;
            for (int generation = 0; generation < 12; ++generation) {
                serial.step();
                require(parallel.step_omp(threads) == threads, "OpenMP team size differs from request");
                require_equal(serial, parallel, std::string(pattern.name) + " generation " +
                              std::to_string(generation + 1) + " threads " + std::to_string(threads));
            }
        }
    }
}

void test_openmp_random_grids() {
    // Include narrow grids: toroidal neighbour positions can coincide there,
    // and must retain the serial reference's eight-position counting rule.
    const std::vector<Position> dimensions{{1, 1}, {1, 7}, {7, 1}, {2, 3},
                                           {17, 33}, {33, 17}, {65, 49}};
    const std::vector<std::uint32_t> seeds{0, 1, 12345, std::numeric_limits<std::uint32_t>::max()};
    for (const auto& [width, height] : dimensions) {
        for (std::uint32_t seed : seeds) {
            for (double density : {0.0, 35.0, 100.0}) {
                Life initial(width, height);
                initial.randomise(density, seed);
                for (std::size_t generations : {0U, 1U, 2U, 10U, 31U}) {
                    Life serial = initial;
                    serial.run(generations);
                    for (int threads : {1, 2, 4}) {
                        Life parallel = initial;
                        const int actual = parallel.run_omp(generations, threads);
                        require(actual == (generations == 0 ? 0 : threads), "Incorrect actual thread count");
                        require_equal(serial, parallel,
                            "random " + std::to_string(width) + "x" + std::to_string(height) +
                            " seed " + std::to_string(seed) + " density " + std::to_string(density) +
                            " generations " + std::to_string(generations) + " threads " + std::to_string(threads));
                    }
                }
            }
        }
    }
}

void test_openmp_smoke() {
    Life serial(101, 101);
    serial.randomise(35.0, 12345);
    serial.run(10);
    require(serial.live_count() == 2213, "Serial smoke live count changed");
    require(serial.checksum() == 7897773207305806522ULL, "Serial smoke checksum changed");
    for (int threads : {1, 2, 4}) {
        Life parallel(101, 101);
        parallel.randomise(35.0, 12345);
        require(parallel.run_omp(10, threads) == threads, "Smoke team size differs from request");
        require_equal(serial, parallel, "101x101 smoke threads " + std::to_string(threads));
    }
}

void test_thread_validation() {
    Life life(3, 3);
    for (int threads : {0, -1}) {
        bool step_rejected = false;
        bool run_rejected = false;
        try { life.step_omp(threads); }
        catch (const std::invalid_argument&) { step_rejected = true; }
        try { life.run_omp(0, threads); }
        catch (const std::invalid_argument&) { run_rejected = true; }
        require(step_rejected && run_rejected, "Invalid thread count accepted");
    }
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
        test_thread_validation();
        std::cout << "PASS: 6 inherited serial tests and invalid-thread API checks\n";
        if (Life::openmp_available()) {
#ifdef _OPENMP
            omp_set_dynamic(0);
#endif
            test_openmp_patterns();
            test_openmp_random_grids();
            test_openmp_smoke();
            std::cout << "PASS: OpenMP threads 1/2/4; 216 per-generation pattern comparisons, "
                         "1260 random-grid comparisons, 3 smoke comparisons (every cell/count/checksum)\n";
        } else {
            bool rejected = false;
            try { Life(3, 3).run_omp(1, 1); }
            catch (const std::runtime_error&) { rejected = true; }
            require(rejected, "Serial-only build silently accepted OpenMP");
            std::cout << "PASS: serial-only build rejects unavailable OpenMP backend\n";
        }
        return EXIT_SUCCESS;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return EXIT_FAILURE;
    }
}
