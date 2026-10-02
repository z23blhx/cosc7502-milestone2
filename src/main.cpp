#include "life.h"

#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {

struct Options {
    // Keeping every workload parameter on the CLI makes benchmark runs explicit
    // and reproducible across machines and optimisation versions.
    std::size_t width = 101;
    std::size_t height = 101;
    std::size_t generations = 1000;
    double density = 35.0;
    std::uint32_t seed = 12345;
    bool csv = false;
    std::string backend = "serial";
    int threads = 1;
};

std::uint64_t parse_unsigned(const std::string& text, const char* option) {
    if (text.empty() || text.find_first_not_of("0123456789") != std::string::npos) {
        throw std::invalid_argument(std::string("invalid non-negative integer for ") + option);
    }
    std::size_t consumed = 0;
    const auto value = std::stoull(text, &consumed);
    if (consumed != text.size()) {
        throw std::invalid_argument(std::string("invalid value for ") + option + ": " + text);
    }
    return value;
}
double parse_density(const std::string& text) {
    std::size_t consumed = 0;
    const double value = std::stod(text, &consumed);
    if (consumed != text.size() || !std::isfinite(value) || value < 0.0 || value > 100.0) {
        throw std::invalid_argument("density must be a number from 0 to 100");
    }
    return value;
}

std::string require_value(int& index, int argc, char* argv[], const char* option) {
    if (++index >= argc) {
        throw std::invalid_argument(std::string("missing value after ") + option);
    }
    return argv[index];
}

void print_help(const char* program) {
    std::cout
        << "Usage: " << program << " [options]\n"
        << "  --backend NAME    serial or omp (default: serial)\n"
        << "  --threads N       Requested OpenMP threads (default: 1; serial uses 1)\n"
        << "  --size N          Set both width and height (default: 101)\n"
        << "  --width N         Set grid width\n"
        << "  --height N        Set grid height\n"
        << "  --generations N   Number of synchronous updates (default: 1000)\n"
        << "  --density P       Initial live-cell percentage (default: 35)\n"
        << "  --seed N          Deterministic 32-bit random seed (default: 12345)\n"
        << "  --csv             Print a CSV header and result row\n"
        << "  --help            Show this help\n";
}

Options parse_options(int argc, char* argv[]) {
    Options options;
    for (int i = 1; i < argc; ++i) {
        const std::string argument = argv[i];
        if (argument == "--help") {
            print_help(argv[0]);
            std::exit(EXIT_SUCCESS);
        } else if (argument == "--csv") {
            options.csv = true;
        } else if (argument == "--backend") {
            options.backend = require_value(i, argc, argv, "--backend");
            if (options.backend != "serial" && options.backend != "omp") {
                throw std::invalid_argument("backend must be serial or omp");
            }
        } else if (argument == "--threads") {
            const auto value = parse_unsigned(require_value(i, argc, argv, "--threads"), "--threads");
            if (value == 0 || value > static_cast<std::uint64_t>(std::numeric_limits<int>::max())) {
                throw std::invalid_argument("threads must be a positive integer within the int range");
            }
            options.threads = static_cast<int>(value);
        } else if (argument == "--size") {
            const auto value = parse_unsigned(require_value(i, argc, argv, "--size"), "--size");
            options.width = options.height = static_cast<std::size_t>(value);
        } else if (argument == "--width") {
            options.width = static_cast<std::size_t>(
                parse_unsigned(require_value(i, argc, argv, "--width"), "--width"));
        } else if (argument == "--height") {
            options.height = static_cast<std::size_t>(
                parse_unsigned(require_value(i, argc, argv, "--height"), "--height"));
        } else if (argument == "--generations") {
            options.generations = static_cast<std::size_t>(
                parse_unsigned(require_value(i, argc, argv, "--generations"), "--generations"));
        } else if (argument == "--density") {
            options.density = parse_density(require_value(i, argc, argv, "--density"));
        } else if (argument == "--seed") {
            const auto value = parse_unsigned(require_value(i, argc, argv, "--seed"), "--seed");
            if (value > std::numeric_limits<std::uint32_t>::max()) {
                throw std::invalid_argument("seed must fit in an unsigned 32-bit integer");
            }
            options.seed = static_cast<std::uint32_t>(value);
        } else {
            throw std::invalid_argument("unknown option: " + argument);
        }
    }
    if (options.width == 0 || options.height == 0) {
        throw std::invalid_argument("grid dimensions must be positive");
    }
    return options;
}

} // namespace

int main(int argc, char* argv[]) {
    try {
        const Options options = parse_options(argc, argv);
        if (options.backend == "omp" && !Life::openmp_available()) {
            throw std::runtime_error("OpenMP backend unavailable: rebuild with OPENMP=1");
        }
#ifdef _OPENMP
        // Configure the runtime before timing; num_threads controls each team.
        if (options.backend == "omp") omp_set_dynamic(0);
#endif
        Life simulation(options.width, options.height);
        simulation.randomise(options.density, options.seed);
        int actual_threads = 1;
        const char* version = options.backend == "serial" ? "v3_explicit_neighbours" : "omp_rows_v1";

        // Construct and randomise before starting the timer so the measurement
        // covers generation updates only, not workload setup.
        const auto start = std::chrono::steady_clock::now();
        if (options.backend == "serial") {
            simulation.run(options.generations);
        } else {
            actual_threads = simulation.run_omp(options.generations, options.threads);
        }
        const auto finish = std::chrono::steady_clock::now();
        const std::chrono::duration<double> elapsed = finish - start;

        if (options.csv) {
            // CSV provides a stable machine-readable record for benchmark scripts;
            // correctness checks and output formatting remain outside the timer.
            std::cout << "backend,version,width,height,generations,density,seed,threads,elapsed_seconds,live_cells,checksum\n";
            std::cout << options.backend << ',' << version << ',' << options.width << ',' << options.height << ','
                      << options.generations << ',' << options.density << ',' << options.seed << ','
                      << actual_threads << ','
                      << std::setprecision(9) << elapsed.count() << ',' << simulation.live_count()
                      << ',' << simulation.checksum() << '\n';
        } else {
            std::cout << "backend: " << options.backend << '\n'
                      << "version: " << version << '\n'
                      << "threads: " << actual_threads << '\n'
                      << "grid: " << options.width << 'x' << options.height << '\n'
                      << "generations: " << options.generations << '\n'
                      << "density_percent: " << options.density << '\n'
                      << "seed: " << options.seed << '\n'
                      << "elapsed_seconds: " << std::fixed << std::setprecision(6)
                      << elapsed.count() << '\n'
                      << "live_cells: " << simulation.live_count() << '\n'
                      << "checksum: " << simulation.checksum() << '\n';
        }
        return EXIT_SUCCESS;
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << "\nUse --help for usage.\n";
        return EXIT_FAILURE;
    }
}
